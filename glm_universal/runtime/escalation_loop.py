"""``glm_universal.runtime.escalation_loop`` -- escalation as a step of the
query loop, with the layer, the ladder and the cost all on the record.

What this is
------------
Every solver in the runtime refuses at whatever layer it was asked at.  The
deep-hole rounds are the one place in this repository where a refusal was
answered by *raising the resolution of the reading* along a declared ladder
instead of stopping, and they are also where the discipline that makes such a
thing honest was worked out: the ladder is declared before it is climbed, the
cells that are tried are counted, and the original refusal stays on the record
beside whatever the escalated reading returns.

This module is that discipline as runtime plumbing.

The four commitments
--------------------
1. **A refusal carries the layer it was refused at.**  ``absent`` becomes
   *absent at L1*, and a claim that a question is unanswerable becomes
   *refused at the top of the declared tower*, which is a much stronger and
   much more falsifiable statement.
2. **The ladder is finite and fixed per query kind.**  :data:`LADDERS` is the
   whole of it.  A kind not in the table gets :data:`DEFAULT_LADDER`, and no
   ladder is built at run time from what the query happens to look like, so
   the loop terminates after at most ``len(ladder)`` rungs -- the property
   ``GLM.EscalationLoop.climb_total`` states: the climb costs at most the
   whole declared ladder, so it cannot run for ever.
3. **An escalated answer is more expensive than a direct one, and says so.**
   Each rung carries a declared cost; the reported cost is the sum over the
   rungs actually run, so the runtime cannot quietly buy accuracy with
   unbounded work.  Cost is non-decreasing along the ladder
   (``GLM.EscalationLoop.climbFrom_cost_ge``, with
   ``GLM.EscalationLoop.climb_direct_cost`` for the direct answer).
4. **Escalation may not convert a principled refusal into an answer.**  Some
   refusals are correct at every layer: a question that is underdetermined,
   one whose relation is grounded in no register, one that is ill formed.
   Those are classified **non-escalatable up front** by :func:`classify`, and
   the loop stops on them at the layer they were refused at.  Without that
   rule the loop would grind up the ladder on every such question and the
   verdict *refused at the top of the tower* would stop meaning anything.

The tower
---------
Three readings, declared here and nowhere else:

``L1`` the register reading
    the query answered from the register the surface terms name.  This is what
    :meth:`~glm_universal.runtime.session.GeometricSession.ask` does today, and
    an escalated run that answers here costs exactly what a direct run costs.
``L2`` the semantics reading
    the operands resolved through the reference layer first -- a notation, an
    SI constant symbol or a formula that denotes a register entry without
    being spelled like one -- and the query re-asked with what they denote.
``L3`` the neighbourhood reading
    the lookup, **named as one**.  The declared radius is one edit; a unique
    alias inside it answers the question and the answer says that it came from
    a lookup at L3, and an *empty* shortlist inside that radius is reported as
    a certified absence, because the index is enumerated rather than sampled.

L3 is where this module meets the honest-dictionary point: nearest-neighbour
retrieval was never objectionable for being a lookup; it was objectionable for
carrying an unstated claim that the representation it indexes is adequate to
the question.  Naming the layer makes that claim stated and checkable.

Exactness
---------
No float, no random source and no digest.  The one numeric quantity is the
integer edit distance the index already computes, and the costs are integers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Sequence, Tuple

from .parser import Query, QueryError, parse_query
from .solution import Solution, SolverError, Step

__all__ = [
    "LayerSpec", "LAYERS", "LAYER_BY_KEY", "LADDERS", "DEFAULT_LADDER",
    "NEIGHBOURHOOD_RADIUS", "PRINCIPLED_MARKERS", "ESCALATABLE",
    "Attempt", "Escalated", "classify", "ladder_for", "resolve",
    "escalated_solution", "ladder_table",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE TOWER
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LayerSpec:
    """One rung: what it reads, and what it costs to read it."""

    key: str
    title: str
    cost: int
    description: str


LAYERS: Tuple[LayerSpec, ...] = (
    LayerSpec("L1", "the register reading", 1,
              "The query answered from the register its surface terms name."),
    LayerSpec("L2", "the semantics reading", 2,
              "The operands resolved through the reference layer, and the "
              "query re-asked with what they denote."),
    LayerSpec("L3", "the neighbourhood reading", 4,
              "A lookup, named as one: the unique alias within the declared "
              "radius answers, and an empty shortlist within it is a "
              "certified absence."),
)

LAYER_BY_KEY: Dict[str, LayerSpec] = {layer.key: layer for layer in LAYERS}

#: The declared radius of the neighbourhood reading, in exact edit distance.
#: Two edits, and no more: a lookup that will travel any distance to find
#: something to say is not a reading of the question, and the radius has to be
#: stated for an empty shortlist inside it to be a certified absence rather
#: than a failure to look far enough.
NEIGHBOURHOOD_RADIUS: int = 2

#: The ladder for each query kind, declared here and fixed.  A kind whose
#: answer is already a reading of the semantics layer -- ``meaning`` -- has a
#: one-rung ladder on purpose: escalating it would be circular.  A kind whose
#: refusals are decisions of a scale, a description or a process -- ``measure``,
#: ``comparative``, ``derive``, ``real``, ``compare``, ``ordering``,
#: ``extremum`` -- likewise, because no rung of this tower reads those.
#: ``ordering`` is the clearest case: it refuses when two readings are on
#: different scales, and raising the resolution of the reading cannot put them
#: on one.  ``extremum`` refuses for the same reason one level up, and for a
#: hole in the column, which no resolution fills either.
LADDERS: Dict[str, Tuple[str, ...]] = {
    "describe": ("L1", "L2", "L3"),
    "nearest": ("L1", "L2", "L3"),
    "spatial": ("L1", "L2", "L3"),
    "cluster": ("L1", "L2"),
    "analogy": ("L1", "L2"),
    "verify": ("L1", "L2"),
    "angle": ("L1", "L2"),
    "product": ("L1",),
    "project": ("L1", "L2"),
    "trilinear": ("L1",),
    "coherence": ("L1", "L2"),
    "report": ("L1",),
    "task": ("L1",),
    "pi_groups": ("L1", "L2"),
    "meaning": ("L1",),
    "real": ("L1",),
    "compare": ("L1",),
    "measure": ("L1",),
    "comparative": ("L1",),
    "derive": ("L1",),
    "ordering": ("L1",),
    "extremum": ("L1",),
    "unknown": ("L1",),
}

#: What a kind with no entry gets.  One rung: an undeclared kind does not get
#: an undeclared ladder.
DEFAULT_LADDER: Tuple[str, ...] = ("L1",)


def ladder_for(kind: str) -> Tuple[str, ...]:
    """The declared ladder of a query kind."""
    return LADDERS.get(kind, DEFAULT_LADDER)


def ladder_table() -> Tuple[Dict[str, object], ...]:
    """Every declared ladder, with its cost if it is climbed to the top."""
    rows = []
    for kind in sorted(LADDERS):
        rungs = LADDERS[kind]
        rows.append({
            "kind": kind, "rungs": rungs, "height": len(rungs),
            "top_cost": sum(LAYER_BY_KEY[key].cost for key in rungs),
        })
    return tuple(rows)


# ═════════════════════════════════════════════════════════════════════════
# 2.  WHICH REFUSALS MAY BE ESCALATED AT ALL
# ═════════════════════════════════════════════════════════════════════════

#: Declared markers of a refusal that is correct at *every* layer, each with
#: the reason it is one.  Matched against the refusal text, lower-cased.  A
#: refusal that matches none of these is treated as an absence, which is the
#: only thing a finer reading can repair.
PRINCIPLED_MARKERS: Tuple[Tuple[str, str, str], ...] = (
    ("unrecognised query", "ill-formed",
     "no classification rule matched, so there is no question to re-read"),
    ("type-2 classes", "ill-formed",
     "the index names no axis, and no reading of it will"),
    ("by an exact zero", "ill-formed",
     "a quotient by an exact zero names no value"),
    ("must be between", "ill-formed",
     "the option is outside its declared range"),
    ("names no single element", "underdetermined",
     "the step is well defined and lands on a cell holding many elements, so "
     "the question has no unique answer at any resolution"),
    ("not decidable", "underdetermined",
     "equality of two processes is undecidable, whatever the precision"),
    ("no side for it to enter on", "ungrounded",
     "the relation is not grounded in the register the question is asked of"),
    ("occupies no column", "ungrounded",
     "the operand has no place in the relation's register"),
    ("cannot be measured against", "ungrounded",
     "the word and the class measure different quantities"),
    ("magnitudes of different quantities", "ungrounded",
     "the two uses are not comparable at any layer"),
    ("cannot order", "ungrounded",
     "the scale word does not order the quantity the uses measure"),
    ("names no direction", "ungrounded",
     "the word sits at the middle of its scale, so the comparative is empty"),
    ("is neither a lexicon adjective", "ungrounded",
     "the word is on no scale, so there is nothing to measure"),
    ("no description derives", "ungrounded",
     "no register describes the coordinate asked for"),
)

#: The tag a refusal gets when no marker matches: an absence, which is the one
#: kind of refusal a finer reading can repair.
ESCALATABLE: str = "absent"


def classify(text: str) -> Dict[str, object]:
    """Is this refusal escalatable, and if not, why not?

    Declared up front, and applied before any rung above the first is run.
    """
    lowered = (text or "").lower()
    for marker, tag, reason in PRINCIPLED_MARKERS:
        if marker in lowered:
            return {"escalatable": False, "tag": tag, "marker": marker,
                    "reason": reason}
    return {"escalatable": True, "tag": ESCALATABLE, "marker": None,
            "reason": ("nothing in the refusal says the question is ill "
                       "formed, underdetermined or ungrounded, so it is read "
                       "as an absence at this layer and the ladder is "
                       "climbed")}


# ═════════════════════════════════════════════════════════════════════════
# 3.  WHAT ONE CLIMB PRODUCES
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Attempt:
    """One rung, run or declined, with what it cost and what it said."""

    layer: str
    cost: int
    outcome: str          # "answered" | "refused" | "skipped" | "not run"
    detail: str
    solution: Optional[Solution] = None


@dataclass(frozen=True)
class Escalated:
    """The result of climbing one ladder: an answer with its layer, or a
    refusal with the layer it was refused at."""

    query: Query
    ladder: Tuple[str, ...]
    attempts: Tuple[Attempt, ...]
    answered: bool
    layer: Optional[str]
    cost: int
    verdict: str
    refusal_tag: Optional[str]
    solution: Solution
    certified_absence: bool = False
    shortlist: Tuple[str, ...] = ()

    @property
    def escalated(self) -> bool:
        """Was anything above the first rung needed?"""
        return self.layer is not None and self.layer != self.ladder[0]

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view of the climb, without the solutions."""
        return {
            "kind": self.query.kind,
            "ladder": list(self.ladder),
            "answered": self.answered,
            "layer": self.layer,
            "cost": self.cost,
            "verdict": self.verdict,
            "refusal_tag": self.refusal_tag,
            "escalated": self.escalated,
            "certified_absence": self.certified_absence,
            "shortlist": list(self.shortlist),
            "attempts": [{"layer": a.layer, "cost": a.cost,
                          "outcome": a.outcome, "detail": a.detail}
                         for a in self.attempts],
        }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE RUNGS
# ═════════════════════════════════════════════════════════════════════════

def _dispatch(session, query: Query) -> Solution:
    """One reading at the register layer, refusals returned rather than raised."""
    try:
        return session._dispatch(query)
    except (SolverError, QueryError, ValueError, KeyError) as exc:
        return Solution(query=query, kind=query.kind,
                        answer=f"unsolved: {exc}", ok=False, error=str(exc),
                        steps=(Step("failure",
                                    f"The query parsed as {query.kind!r} but "
                                    f"could not be solved.",
                                    f"error: {exc}"),))


def _rung_register(session, query: Query) -> Tuple[Optional[Solution], str]:
    return _dispatch(session, query), "the register the surface terms name"


def _denoted_name(session, term: str) -> Optional[str]:
    """What a term denotes, when the register does not spell it that way.

    The reference layer is consulted only for a term the index cannot resolve,
    and only a denotation that the index *can* resolve is used: the rung
    rewrites the question into the machine's own vocabulary and does not
    invent one.
    """
    from ..semantics import reference as rf
    if session.index.candidates(term):
        return None
    try:
        resolution = rf.resolve(term)
    except Exception:                           # pragma: no cover - defensive
        return None
    if resolution.meaning is None:
        return None
    # The resolver's own witness names what it used -- "boltzmann_constant:
    # J/K, exact by SI definition" -- so the bridge reads the register name
    # off the witness rather than guessing one from the dimension.
    witness = str(getattr(resolution, "witness", "") or "")
    head = witness.split(":", 1)[0].strip()
    if head and session.index.candidates(head):
        return head
    for attribute in ("name", "canonical", "symbol"):
        value = getattr(resolution.meaning, attribute, None)
        if isinstance(value, str) and value and session.index.candidates(value):
            return value
    # A quantity meaning with no witness the register spells: fall back to the
    # dimension, and only where the register holds exactly one entry of it, so
    # that an ambiguous dimension refuses rather than picks.
    if getattr(resolution.meaning, "kind", "") == "quantity":
        from fractions import Fraction
        from ..data_objects import physics as dop
        try:
            target = tuple(Fraction(x)
                           for x in resolution.meaning.exponents)
            matches = [entry.name for entry in dop.load_physics_register()
                       if tuple(Fraction(v) for v in entry.exps_ext10) == target]
        except Exception:                       # pragma: no cover - defensive
            return None
        if len(matches) == 1 and session.index.candidates(matches[0]):
            return matches[0]
    return None


def _rung_semantics(session, query: Query) -> Tuple[Optional[Solution], str]:
    rewritten = []
    changed = []
    for operand in query.operands:
        denoted = _denoted_name(session, operand)
        if denoted is None:
            rewritten.append(operand)
        else:
            rewritten.append(denoted)
            changed.append(f"{operand} -> {denoted}")
    if not changed:
        return None, ("no operand denotes a register entry it is not spelled "
                      "like, so this rung has nothing to read")
    moved = Query(raw=query.raw, normalised=query.normalised, kind=query.kind,
                  domain=query.domain, operands=tuple(rewritten),
                  options=dict(query.options), rule=query.rule + "+semantics",
                  trace=query.trace + tuple(changed),
                  suggestions=query.suggestions)
    return _dispatch(session, moved), "resolved through the reference layer: " \
                                      + ", ".join(changed)


def _rung_neighbourhood(session, query: Query
                        ) -> Tuple[Optional[Solution], str]:
    """The lookup, named: a unique alias within the declared radius, or an
    absence certified within it."""
    if not query.operands:
        return None, "the query names no operand to look up"
    surface = query.operands[0]
    shortlist = session.index.suggest(surface, limit=8,
                                      max_distance=NEIGHBOURHOOD_RADIUS)
    if len(shortlist) != 1:
        detail = (f"the shortlist within {NEIGHBOURHOOD_RADIUS} edits of "
                  f"{surface!r} is {list(shortlist)}")
        return None, detail
    alias = shortlist[0]
    moved = Query(raw=query.raw, normalised=query.normalised, kind=query.kind,
                  domain=query.domain,
                  operands=(alias,) + tuple(query.operands[1:]),
                  options=dict(query.options),
                  rule=query.rule + "+neighbourhood",
                  trace=query.trace + (f"{surface} -> {alias} "
                                       f"(a lookup at L3, within "
                                       f"{NEIGHBOURHOOD_RADIUS} edits)",),
                  suggestions=query.suggestions)
    solution = _dispatch(session, moved)
    if solution.ok:
        solution = Solution(
            query=solution.query, kind=solution.kind,
            answer=(f"{solution.answer}  [answered by a lookup at L3: "
                    f"{surface!r} -> {alias!r}, the unique alias within "
                    f"{NEIGHBOURHOOD_RADIUS} edits]"),
            steps=solution.steps + (
                Step("the layer the answer came from",
                     f"The register did not hold {surface!r} and the "
                     f"reference layer did not denote it, so the question was "
                     f"answered by a lookup -- and the lookup names its "
                     f"layer rather than passing itself off as a reading.",
                     f"L3, radius {NEIGHBOURHOOD_RADIUS}, "
                     f"shortlist = [{alias}]"),),
            expected=solution.expected, script_spec=solution.script_spec,
            payload=dict(solution.payload), ok=True, error=None)
    return solution, f"the unique alias within {NEIGHBOURHOOD_RADIUS} edits is {alias!r}"


_RUNGS: Dict[str, Callable[[object, Query], Tuple[Optional[Solution], str]]] = {
    "L1": _rung_register,
    "L2": _rung_semantics,
    "L3": _rung_neighbourhood,
}


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE LOOP
# ═════════════════════════════════════════════════════════════════════════

def _certified_absence(session, query: Query) -> Tuple[bool, Tuple[str, ...]]:
    """Is the shortlist within the declared radius empty, and enumerated?"""
    if not query.operands:
        return False, ()
    shortlist = session.index.suggest(query.operands[0], limit=8,
                                      max_distance=NEIGHBOURHOOD_RADIUS)
    return (not shortlist), tuple(shortlist)


def resolve(session, query: Query) -> Escalated:
    """Climb the query's declared ladder: the least rung that resolves.

    Returns the first rung's answer where there is one -- an escalated run is
    never slower than a direct one on a question the register answers -- and
    otherwise the least rung that resolves, or a refusal carrying the layer it
    was refused at and the cost of having asked.
    """
    ladder = ladder_for(query.kind)
    attempts: list[Attempt] = []
    cost = 0
    first_refusal: Optional[Solution] = None
    tag: Optional[str] = None

    for index, key in enumerate(ladder):
        layer = LAYER_BY_KEY[key]
        rung = _RUNGS.get(key)
        if rung is None:                        # pragma: no cover - defensive
            continue
        solution, detail = rung(session, query)
        if solution is None:
            attempts.append(Attempt(key, 0, "skipped", detail))
            continue
        cost += layer.cost
        if solution.ok:
            attempts.append(Attempt(key, layer.cost, "answered", detail,
                                    solution))
            return Escalated(
                query=query, ladder=ladder, attempts=tuple(attempts),
                answered=True, layer=key, cost=cost,
                verdict=(f"answered at {key} -- {layer.title}"
                         + ("" if index == 0 else
                            f", reached by escalating from "
                            f"{ladder[0]} at a cost of {cost} against "
                            f"{LAYER_BY_KEY[ladder[0]].cost} for a direct "
                            f"answer")),
                refusal_tag=None, solution=solution)
        attempts.append(Attempt(key, layer.cost, "refused", detail, solution))
        if first_refusal is None:
            first_refusal = solution
            verdict = classify(solution.error or solution.answer)
            tag = str(verdict["tag"])
            if not verdict["escalatable"]:
                return Escalated(
                    query=query, ladder=ladder, attempts=tuple(attempts),
                    answered=False, layer=key, cost=cost,
                    verdict=(f"refused at {key} and not escalated: the "
                             f"refusal is {tag} -- {verdict['reason']}"),
                    refusal_tag=tag, solution=solution)

    certified, shortlist = _certified_absence(session, query)
    top = ladder[-1]
    refusal = first_refusal if first_refusal is not None else _dispatch(
        session, query)
    verdict = (
        (f"refused at {top}, which is the whole of the declared ladder for "
         f"a {query.kind} query")
        if len(ladder) == 1 else
        (f"refused at every rung of the declared ladder {list(ladder)}, so "
         f"the answer is refused at the top of the tower ({top}) and not "
         f"merely absent at {ladder[0]}"))
    if certified:
        verdict += (f"; the absence is certified within "
                    f"{NEIGHBOURHOOD_RADIUS} edits, the shortlist there being "
                    f"empty over an enumerated index")
    return Escalated(
        query=query, ladder=ladder, attempts=tuple(attempts), answered=False,
        layer=top, cost=cost, verdict=verdict, refusal_tag=tag or ESCALATABLE,
        solution=refusal, certified_absence=certified, shortlist=shortlist)


def escalated_solution(session, climb: Escalated) -> Solution:
    """The climb as a :class:`Solution`, with the ladder in the payload.

    The answer text of a direct answer is untouched: a question the register
    answers is answered exactly as it was before, and the ladder is recorded
    beside it rather than written into it.
    """
    base = climb.solution
    trace = Step(
        "the ladder",
        climb.verdict,
        "; ".join(f"{a.layer}:{a.outcome}(cost {a.cost})"
                  for a in climb.attempts) or "no rung ran")
    payload = dict(base.payload)
    payload["escalation"] = climb.as_dict()
    answer = base.answer
    if not climb.answered:
        answer = f"{base.answer}  [{climb.verdict}]"
    return Solution(query=base.query, kind=base.kind, answer=answer,
                    steps=base.steps + (trace,), expected=base.expected,
                    script_spec=base.script_spec, payload=payload,
                    ok=base.ok, error=base.error)


def ask(session, text: str, domain: Optional[str] = None) -> Solution:
    """Parse and answer one query through the escalation loop."""
    query = parse_query(text, session.index, domain)
    return escalated_solution(session, resolve(session, query))
