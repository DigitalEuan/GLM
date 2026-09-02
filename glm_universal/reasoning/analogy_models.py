"""``glm_universal.reasoning.analogy_models`` -- analogy by named relation.

Why this module exists
----------------------
:mod:`glm_universal.reasoning.analogy` reads ``A : B :: C : ?`` as a
*translation*: it computes ``D* = C + (B - A)`` in ``Q^24`` and returns the
nearest carrier.  That is exactly right when the relation between ``A`` and
``B`` really is a displacement of the coordinates, and exactly wrong when it
is not.  The end-to-end evaluation measured the difference: every failing
case it found was an analogy whose relation is *not* a displacement.

* ``He : Ne :: Ar : ?`` -- a **step along the periodic table**.  The chemistry
  carrier holds ``z``, ``period`` and a group-block *category*, so a step of
  one period inside a group is not a displacement of the carrier at all, and
  the nearest point to the translated target was ``Fe``.
* ``length : wavenumber :: time : ?`` -- a **reciprocal**, ``L -> L^-1``.
  Reflection is not translation: transporting the difference asks for
  ``T . L^-2`` and lands on ``chromatic_dispersion``.
* ``solid : liquid :: liquid : ?`` -- a relation the lexicon **states in so
  many words** (``solid opposite_of liquid``), which the primitive-space
  metric turns into "nearest word", and ``fluid`` is nearer to ``liquid``
  than ``gas`` is because it is its hypernym.

So this module adds the layer the translation model was missing: a small,
ordered set of **named relation models**.  Each one looks at ``A`` and ``B``
and either says *what the relation is* -- in the register's own terms, not in
coordinates -- or declines.  The first model that recognises the pair
transports it to ``C``.  A model that recognises the pair but finds nothing at
the transported position **refuses**, and says where it looked: that is a
better answer than the nearest point to a target that means nothing.

The models
----------

``periodic_step`` (chemistry)
    ``A`` and ``B`` are elements, and the step from one to the other is a
    displacement ``(dperiod, dgroup)`` in the *derived* table coordinates of
    :mod:`glm_universal.reasoning.periodic_table` -- period and group computed
    from the period boundaries, never tabulated.  Transport adds the same
    displacement to ``C``'s position and reads off the element there, refusing
    when the position is empty or holds the fifteen-element f-block.

``reciprocal_dimension`` (physics)
    The EXT10 exponent vector of ``B`` is the negative of ``A``'s, so the
    relation is "the reciprocal quantity".  The answer must be the reciprocal
    of ``C``, which fixes its dimension exactly and its *name* only up to the
    quantities that share that dimension; the shortlist is narrowed by the
    filters below and any residual tie is reported, not broken silently.

``scale_shift`` (physics)
    ``A`` and ``B`` have the same dimension and differ by a decimal scale
    ``dscale`` -- ``gram`` to ``mass`` is ``10^3``.  Transport shifts ``C`` by
    the same power of ten.

``lexicon_relation`` (lexicon)
    The lexicon register carries 380 explicit triples: ``hot opposite_of
    cold``, ``liquid form_of fluid``, ``force causes acceleration``.  If a
    triple relates ``A`` and ``B``, the same relation is looked up from ``C``
    -- in either direction, since ``gas opposite_of liquid`` is stored on
    ``gas`` and not on ``liquid`` -- and the operands themselves are excluded,
    which is what makes ``solid : liquid :: liquid : gas`` come out.

    One relation is deliberately **not** transportable: ``related_to``.  It
    records that a link exists without saying which, so it determines no
    answer; ``heat related_to temperature`` is the whole reason
    ``heat : temperature :: force : ?`` has no honest answer here.

Narrowing a dimension class
---------------------------
``reciprocal_dimension`` and ``scale_shift`` both fix the answer's dimension
exactly, and a dimension does not fix a name: 24 register quantities have
dimension ``T^-1``.  The shortlist is narrowed by three structural filters,
each of which transports a property of ``B`` rather than guessing, and each
of which is skipped when it would empty the shortlist:

1. **sub-domain** -- if ``A`` and ``C`` share a ``domain_name`` then the
   answer should sit in ``B``'s, as ``wavenumber`` sits in ``kinematics``;
2. **primitivity** -- ``B`` either is or is not the left-hand side of a
   defining relation in the register's own relation table, and the answer
   should match: ``wavenumber`` is defined by nothing, so ``strain_rate``
   (``strain / time``) is not its counterpart;
3. **symbol shape** -- ``B``'s symbol is atomic (``k``) or compound
   (``grad v``), and the answer's should be too.

Filter 3 is applied only as a *tie-break*, and when it fires the excluded
candidates are named in the answer, so the reader can see the choice being
made.  If a tie survives all three, every survivor is reported.

Everything here is exact: integer table positions, integer exponent vectors,
integer scales.  No coordinate metric is consulted at all -- that is the point
of the layer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..data_objects import elements as do_elements
from ..data_objects import physics as do_physics
from ..data_objects.base import DataObject
from . import periodic_table as pt

__all__ = [
    "MODEL_NAMES", "MODELS_BY_DOMAIN", "VAGUE_RELATIONS", "REPORT_CASES",
    "ModelResult", "explain_analogy", "analogy_models_report",
    "periodic_step", "reciprocal_dimension", "scale_shift",
    "lexicon_relation", "repaired_triples",
]


# ===========================================================================
# 0.  THE RESULT OF A MODEL
# ===========================================================================

@dataclass(frozen=True)
class ModelResult:
    """What a relation model made of ``A : B :: C : ?``.

    ``answer`` is ``None`` exactly when ``refusal`` is set: the model
    recognised the relation and then found nothing at the transported
    position.  ``candidates`` holds every name that survived the model's own
    filters, so a tie is visible rather than broken by ordering.
    """

    model: str
    domain: str
    relation: str
    answer: Optional[str] = None
    candidates: Tuple[str, ...] = ()
    refusal: Optional[str] = None
    steps: Tuple[Tuple[str, str], ...] = ()
    witness: Dict[str, str] = field(default_factory=dict)

    @property
    def unique(self) -> bool:
        """Whether exactly one candidate survived."""
        return len(self.candidates) == 1

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "model": self.model,
            "domain": self.domain,
            "relation": self.relation,
            "answer": self.answer,
            "candidates": list(self.candidates),
            "unique": self.unique,
            "refusal": self.refusal,
            "witness": dict(self.witness),
        }


# ===========================================================================
# 1.  CHEMISTRY -- A STEP ALONG THE TABLE
# ===========================================================================

def periodic_step(a: str, b: str, c: str,
                  pool: Sequence[DataObject]) -> Optional[ModelResult]:
    """``A : B :: C : ?`` as a displacement in derived table coordinates.

    Returns ``None`` when any of the three is not an element of the register,
    which is the model declining rather than failing.
    """
    try:
        pa, pb, pc = (pt.position_of_symbol(x) for x in (a, b, c))
    except pt.PositionError:
        return None
    d_period = pb.period - pa.period
    d_group = pb.group - pa.group
    if d_period == 0 and d_group == 0:
        return None                       # A and B are the same square
    target_period, target_group = pc.period + d_period, pc.group + d_group
    relation = (f"{a} -> {b} is a step of ({d_period:+d} period, "
                f"{d_group:+d} group) in the derived table coordinates")
    steps: List[Tuple[str, str]] = [
        ("position",
         f"Derive the table position of each term from the period "
         f"boundaries: {a} is period {pa.period}, group {pa.group}, block "
         f"{pa.block}; {b} is period {pb.period}, group {pb.group}, block "
         f"{pb.block}; {c} is period {pc.period}, group {pc.group}, block "
         f"{pc.block}.",
         ),
        ("step",
         f"The step from {a} to {b} is ({d_period:+d}, {d_group:+d}); "
         f"applied to {c} it asks for period {target_period}, group "
         f"{target_group}."),
    ]
    witness = {
        "model": "periodic_step",
        "d_period": str(d_period),
        "d_group": str(d_group),
        "target_period": str(target_period),
        "target_group": str(target_group),
    }
    names = {o.name for o in pool}
    try:
        symbol = pt.symbol_at(target_period, target_group)
    except pt.PositionError as exc:
        return ModelResult(
            model="periodic_step", domain="chemistry", relation=relation,
            refusal=(f"the step is well defined -- ({d_period:+d} period, "
                     f"{d_group:+d} group) -- but {str(exc).split(': ', 1)[-1]}"),
            steps=tuple(steps), witness=witness)
    if symbol not in names:
        return ModelResult(
            model="periodic_step", domain="chemistry", relation=relation,
            refusal=(f"period {target_period}, group {target_group} holds "
                     f"{symbol}, which is not in this session's register"),
            steps=tuple(steps), witness=witness)
    steps.append(("answer",
                  f"Period {target_period}, group {target_group} holds "
                  f"exactly one element: {symbol}."))
    witness["answer"] = symbol
    return ModelResult(
        model="periodic_step", domain="chemistry", relation=relation,
        answer=symbol, candidates=(symbol,), steps=tuple(steps),
        witness=witness)


# ===========================================================================
# 2.  PHYSICS -- DIMENSION SPACE
# ===========================================================================

_EXT10 = tuple(f"ext10.{axis}" for axis in do_physics.AXES_EXT10)
_SI7 = tuple(f"si7.{axis}" for axis in do_physics.AXES_SI7)


def _coordinate(obj: DataObject, name: str):
    return obj.carrier[tuple(obj.layout).index(name)]


def _exponents(obj: DataObject) -> Tuple:
    return tuple(_coordinate(obj, n) for n in _EXT10 + _SI7)


def _scale(obj: DataObject):
    return _coordinate(obj, "scale")


def _attribute(obj: DataObject, key: str) -> str:
    return str(obj.attributes.get(key, ""))


@lru_cache(maxsize=1)
def _defined_quantities() -> frozenset:
    """Names that stand on the left of a defining relation in the register.

    A quantity that is defined by an expression over other quantities --
    ``strain_rate = strain / time`` -- is *derived*; one that appears on no
    left-hand side -- ``length``, ``wavenumber``, ``frequency`` -- is a
    primitive of the register's own relation table.
    """
    path = (Path(__file__).resolve().parent / "_data"
            / "physics_relations.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {str(row[0]) for row in data.get("scalar_relations", ())}
    names |= {str(row[0]) for row in data.get("tensor_relations", ())}
    return frozenset(names)


def _atomic_symbol(symbol: str) -> bool:
    """Whether a register symbol is a single letter, possibly subscripted."""
    head = symbol.split("_")[0]
    return len(head) <= 1


def _narrow(candidates: Sequence[DataObject], b: DataObject, a: DataObject,
            c: DataObject, steps: List[Tuple[str, str]]
            ) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Apply the three structural filters; return survivors and tie-break losers.

    Each filter is skipped when it would empty the shortlist, and every filter
    that fires is recorded in ``steps``.
    """
    names = tuple(sorted(o.name for o in candidates))
    pool = list(candidates)

    if _attribute(a, "domain_name") == _attribute(c, "domain_name"):
        want = _attribute(b, "domain_name")
        kept = [o for o in pool if _attribute(o, "domain_name") == want]
        if kept and len(kept) < len(pool):
            steps.append((
                "filter: sub-domain",
                f"{a.name} and {c.name} are both in the {_attribute(a, 'domain_name')!r} "
                f"part of the register, so the answer should sit where "
                f"{b.name} sits, in {want!r}: {len(pool)} candidates -> "
                f"{len(kept)}."))
            pool = kept

    defined = _defined_quantities()
    want_defined = b.name in defined
    kept = [o for o in pool if (o.name in defined) == want_defined]
    if kept and len(kept) < len(pool):
        steps.append((
            "filter: primitivity",
            f"{b.name} is "
            f"{'defined by a relation in the register' if want_defined else 'defined by no relation in the register'}"
            f", so the answer should be too: {len(pool)} candidates -> "
            f"{len(kept)}."))
        pool = kept

    survivors = tuple(sorted(o.name for o in pool))
    excluded: Tuple[str, ...] = ()
    if len(pool) > 1:
        want_atomic = _atomic_symbol(_attribute(b, "symbol"))
        kept = [o for o in pool
                if _atomic_symbol(_attribute(o, "symbol")) == want_atomic]
        if kept and len(kept) < len(pool):
            excluded = tuple(sorted(o.name for o in pool if o not in kept))
            steps.append((
                "tie-break: symbol shape",
                f"{len(pool)} candidates survive the structural filters. "
                f"{b.name} carries the {'atomic' if want_atomic else 'compound'} "
                f"symbol {_attribute(b, 'symbol')!r}; keeping the candidates "
                f"whose symbol has the same shape leaves {len(kept)} and "
                f"excludes {list(excluded)}."))
            pool = kept
            survivors = tuple(sorted(o.name for o in pool))
    del names
    return survivors, excluded


def _dimension_answer(model: str, relation: str, a: DataObject,
                      b: DataObject, c: DataObject,
                      pool: Sequence[DataObject],
                      target_exponents: Tuple, target_scale,
                      target_text: str,
                      steps: List[Tuple[str, str]],
                      witness: Dict[str, str]) -> ModelResult:
    """Finish a physics model: find the quantities at a target dimension."""
    matches = [o for o in pool
               if _exponents(o) == target_exponents and _scale(o) == target_scale
               and o.name not in (a.name, b.name, c.name)]
    witness["target"] = target_text
    witness["class_size"] = str(len(matches))
    if not matches:
        return ModelResult(
            model=model, domain="physics", relation=relation,
            refusal=(f"the relation is well defined and asks for "
                     f"{target_text}, and the register holds no quantity of "
                     f"that dimension"),
            steps=tuple(steps), witness=witness)
    steps.append((
        "class",
        f"The register holds {len(matches)} quantit"
        f"{'y' if len(matches) == 1 else 'ies'} of dimension {target_text}"
        + ("." if len(matches) == 1
           else f", so the relation fixes what the answer *is* and not yet "
                f"what it is called.")))
    survivors, excluded = _narrow(matches, b, a, c, steps)
    witness["candidates"] = ",".join(survivors)
    if excluded:
        witness["tie_broken_against"] = ",".join(excluded)
    answer = survivors[0] if len(survivors) == 1 else " or ".join(survivors)
    steps.append((
        "answer",
        f"{answer}." if len(survivors) == 1 else
        f"{len(survivors)} candidates are indistinguishable to every "
        f"property this model can transport, so all of them are reported: "
        f"{list(survivors)}."))
    witness["answer"] = answer
    return ModelResult(
        model=model, domain="physics", relation=relation, answer=answer,
        candidates=survivors, steps=tuple(steps), witness=witness)


def reciprocal_dimension(a: str, b: str, c: str,
                         pool: Sequence[DataObject]
                         ) -> Optional[ModelResult]:
    """``A : B :: C : ?`` where ``B`` is the reciprocal quantity of ``A``."""
    index = {o.name: o for o in pool}
    try:
        oa, ob, oc = (index[x] for x in (a, b, c))
    except KeyError:
        return None
    ea, eb, ec = (_exponents(o) for o in (oa, ob, oc))
    if all(x == 0 for x in ea) or any(x + y != 0 for x, y in zip(ea, eb)):
        return None
    if _scale(oa) + _scale(ob) != 0:
        return None
    target = tuple(-x for x in ec)
    target_scale = -_scale(oc)
    relation = (f"{a} -> {b} is a reciprocal: the exponent vectors sum to "
                f"zero ({_attribute(oa, 'dimension_ext10')} and "
                f"{_attribute(ob, 'dimension_ext10')})")
    steps: List[Tuple[str, str]] = [
        ("relation",
         f"Every exponent of {b} is the negative of the matching exponent of "
         f"{a}, so the step is a reflection of the dimension vector and not "
         f"a translation of it."),
        ("transport",
         f"Reflecting {c} ({_attribute(oc, 'dimension_ext10')}) asks for its "
         f"reciprocal."),
    ]
    witness = {"model": "reciprocal_dimension",
               "a_dimension": _attribute(oa, "dimension_ext10"),
               "b_dimension": _attribute(ob, "dimension_ext10"),
               "c_dimension": _attribute(oc, "dimension_ext10")}
    target_text = _reciprocal_text(oc)
    return _dimension_answer("reciprocal_dimension", relation, oa, ob, oc,
                             pool, target, target_scale, target_text, steps,
                             witness)


def _reciprocal_text(obj: DataObject) -> str:
    """A readable name for the reciprocal dimension of a quantity."""
    parts = []
    for axis, name in zip(do_physics.AXES_EXT10, _EXT10):
        exponent = -_coordinate(obj, name)
        if exponent == 0:
            continue
        parts.append(axis if exponent == 1 else f"{axis}^{exponent}")
    return " ".join(parts) if parts else "1"


def scale_shift(a: str, b: str, c: str,
                pool: Sequence[DataObject]) -> Optional[ModelResult]:
    """``A : B :: C : ?`` where ``B`` is ``A`` at a different decimal scale."""
    index = {o.name: o for o in pool}
    try:
        oa, ob, oc = (index[x] for x in (a, b, c))
    except KeyError:
        return None
    if _exponents(oa) != _exponents(ob):
        return None
    delta = _scale(ob) - _scale(oa)
    if delta == 0:
        return None
    target_scale = _scale(oc) + delta
    relation = (f"{a} -> {b} is a change of decimal scale by 10^{delta}, "
                f"the dimension {_attribute(oa, 'dimension_ext10')} being "
                f"unchanged")
    steps: List[Tuple[str, str]] = [
        ("relation",
         f"{a} and {b} have the same dimension and differ only in scale: "
         f"10^{_scale(oa)} against 10^{_scale(ob)}."),
        ("transport",
         f"Applying the same factor to {c} (10^{_scale(oc)}) asks for "
         f"10^{target_scale} at dimension "
         f"{_attribute(oc, 'dimension_ext10')}."),
    ]
    witness = {"model": "scale_shift", "d_scale": str(delta),
               "target_scale": str(target_scale)}
    target_text = (f"{_attribute(oc, 'dimension_ext10')} at scale "
                   f"10^{target_scale}")
    return _dimension_answer("scale_shift", relation, oa, ob, oc, pool,
                             _exponents(oc), target_scale, target_text, steps,
                             witness)


# ===========================================================================
# 3.  LEXICON -- A RELATION THE REGISTER STATES
# ===========================================================================

#: Relations that record *that* two concepts are linked without saying how.
#: They are not transportable: knowing ``heat related_to temperature`` fixes
#: no step to take from ``force``.
VAGUE_RELATIONS: Tuple[str, ...] = ("related_to",)

#: Relation names the register uses for one and the same relation.  The
#: lexicon says ``cause produces effect`` and ``force causes acceleration``;
#: those are the same step under two spellings, and transporting one to the
#: other is reading the register rather than guessing.  Inverses are grouped
#: with their forward form, since the transport already looks in both
#: directions.
RELATION_SYNONYMS: Tuple[Tuple[str, ...], ...] = (
    ("produces", "causes", "generates"),
    ("produced_by", "caused_by"),
)


def _synonyms(relation: str) -> Tuple[str, ...]:
    """Every spelling of a relation, including the one given."""
    for group in RELATION_SYNONYMS:
        if relation in group:
            return group
    return (relation,)


def _triples(pool: Sequence[DataObject]
             ) -> Tuple[Tuple[str, str, str], ...]:
    out: List[Tuple[str, str, str]] = []
    for obj in pool:
        for triple in obj.attributes.get("triples", ()) or ():
            if len(triple) == 3:
                out.append((str(triple[0]), str(triple[1]), str(triple[2])))
    return tuple(out)


def repaired_triples() -> Tuple[Tuple[str, str, str], ...]:
    """The relations the measure layer recovered from the ``related_to`` residue.

    ``related_to`` is in :data:`VAGUE_RELATIONS` and is never transported: it
    records that a link exists without saying which, and transporting it would
    be a guess.  :func:`glm_universal.reasoning.measure_view.relation_repair`
    decides some of those links against the physics register -- two endpoints
    of the same dimension, or differing by exactly one quantity of a fixed
    factor basis -- and the results are relations of a definite name.  They
    are *derived*, so they cannot live in the lexicon's four relation slots;
    they are read here instead, and they are the only triples in this module
    that no register file contains.
    """
    from . import measure_view as mv
    return mv.repaired_triples()


def lexicon_relation(a: str, b: str, c: str,
                     pool: Sequence[DataObject],
                     repaired: bool = True) -> Optional[ModelResult]:
    """``A : B :: C : ?`` transported along a relation the register states.

    ``repaired=False`` suppresses the derived relations of
    :func:`repaired_triples` and leaves only what the lexicon itself stores.
    It is the control the repair has to beat, and nothing in the runtime uses
    it.
    """
    names = {o.name for o in pool}
    if not {a, b, c} <= names:
        return None
    triples = _triples(pool)
    if repaired:
        triples = triples + repaired_triples()
    linking = sorted({r for s, r, o in triples
                      if r not in VAGUE_RELATIONS
                      and ((s, o) == (a, b) or (s, o) == (b, a))})
    if not linking:
        return None
    relation = "; ".join(f"{a} {r} {b}" if any(
        (s, rr, o) == (a, r, b) for s, rr, o in triples) else f"{b} {r} {a}"
        for r in linking)
    steps: List[Tuple[str, str]] = [
        ("relation",
         f"The lexicon register states the relation outright: "
         f"{relation}.  No coordinate metric is consulted."),
    ]
    # The answer may legitimately be ``B`` itself -- two things can stand in
    # the same relation to one third thing -- so only ``A`` and ``C`` are
    # excluded, ``C`` because a relation of a term to itself is no step.
    wanted = {name for r in linking for name in _synonyms(r)}
    reached: Dict[str, List[str]] = {}
    for s, rr, o in triples:
        if rr not in wanted:
            continue
        if s == c and o in names and o not in (a, c):
            reached.setdefault(o, []).append(f"{c} {rr} {o}")
        elif o == c and s in names and s not in (a, c):
            reached.setdefault(s, []).append(f"{s} {rr} {c}")
    witness = {"model": "lexicon_relation", "relations": ",".join(linking)}
    if not reached:
        return ModelResult(
            model="lexicon_relation", domain="lexicon", relation=relation,
            refusal=(f"looking {' and '.join(linking)} up from {c}, in either "
                     f"direction and excluding the operands, reaches nothing "
                     f"else in the register"),
            steps=tuple(steps), witness=witness)
    steps.append((
        "transport",
        f"Looking the same relation up from {c}, in either direction and "
        f"excluding the operands themselves, reaches "
        f"{sorted(reached)}."))
    survivors = tuple(sorted(reached))
    witness["candidates"] = ",".join(survivors)
    witness["witness_triples"] = "; ".join(
        sorted(t for triples_of in reached.values() for t in triples_of))
    answer = survivors[0] if len(survivors) == 1 else " or ".join(survivors)
    witness["answer"] = answer
    steps.append((
        "answer",
        f"{answer}, on the strength of {witness['witness_triples']}."))
    return ModelResult(
        model="lexicon_relation", domain="lexicon", relation=relation,
        answer=answer, candidates=survivors, steps=tuple(steps),
        witness=witness)


# ===========================================================================
# 4.  THE LAYER
# ===========================================================================

#: The models a domain offers, in the order they are tried.
MODELS_BY_DOMAIN: Dict[str, Tuple] = {
    "chemistry": (periodic_step,),
    "physics": (reciprocal_dimension, scale_shift),
    "lexicon": (lexicon_relation,),
}

#: Every model name, in domain order.
MODEL_NAMES: Tuple[str, ...] = (
    "periodic_step", "reciprocal_dimension", "scale_shift",
    "lexicon_relation",
)


def explain_analogy(domain: str, a: str, b: str, c: str,
                    pool: Sequence[DataObject],
                    repaired: bool = True) -> Optional[ModelResult]:
    """The first relation model that recognises ``A : B``, or ``None``.

    ``None`` means no model claims to know what the relation is, which is the
    signal for the caller to fall back on the translation solver -- or to
    refuse, if the terms do not even share a register.

    ``repaired`` reaches :func:`lexicon_relation` and nothing else; it is the
    control switch for the repaired relations and defaults to on.
    """
    for model in MODELS_BY_DOMAIN.get(domain, ()):
        if model is lexicon_relation:
            result = model(a, b, c, pool, repaired=repaired)
        else:
            result = model(a, b, c, pool)
        if result is not None:
            return result
    return None


# ===========================================================================
# 5.  THE REPORT
# ===========================================================================

#: The analogies the report re-solves, with the model each one should meet.
#: Every entry is a question a user could type; the expectations are the
#: mathematics of the case and not a transcript of what the code printed.
REPORT_CASES: Tuple[Tuple[str, str, str, str, str, str], ...] = (
    # domain, a, b, c, expected model, expected answer ("" = a refusal)
    ("chemistry", "He", "Ne", "Ar", "periodic_step", "Kr"),
    ("chemistry", "B", "Al", "C", "periodic_step", "Si"),
    ("chemistry", "Li", "Na", "Be", "periodic_step", "Mg"),
    ("chemistry", "F", "Cl", "O", "periodic_step", "S"),
    ("chemistry", "Li", "Be", "Na", "periodic_step", "Mg"),
    ("chemistry", "H", "He", "Li", "periodic_step", "Ne"),
    ("chemistry", "Ca", "Sc", "Ba", "periodic_step", ""),
    ("physics", "length", "wavenumber", "time", "reciprocal_dimension",
     "frequency"),
    ("physics", "time", "frequency", "length", "reciprocal_dimension",
     "wavenumber"),
    ("physics", "gram", "mass", "millisecond", "scale_shift", "time"),
    ("lexicon", "hot", "cold", "fast", "lexicon_relation", "slow"),
    ("lexicon", "solid", "liquid", "liquid", "lexicon_relation", "gas"),
)


def analogy_models_report() -> Dict[str, object]:
    """Re-solve every case in :data:`REPORT_CASES` through the model layer.

    Nothing is quoted: each case is solved here and now, and the report says
    which model fired, what it answered, and whether that is what the
    mathematics of the case requires.
    """
    from ..data_objects import semantic_lexicon as do_semantic_lexicon
    lexicon = do_semantic_lexicon.semantic_lexicon_objects()
    if isinstance(lexicon, tuple) and lexicon and not isinstance(
            lexicon[0], DataObject):
        lexicon = lexicon[0]
    pools = {
        "chemistry": do_elements.element_objects(),
        "physics": do_physics.physics_objects(),
        "lexicon": tuple(lexicon),
    }
    rows: List[Dict[str, object]] = []
    agree = 0
    for domain, a, b, c, model, expected in REPORT_CASES:
        pool = pools[domain]
        result = explain_analogy(domain, a, b, c, pool)
        got_model = "" if result is None else result.model
        got_answer = "" if result is None or result.answer is None \
            else result.answer
        ok = (got_model == model
              and (expected in got_answer.split(" or ") if expected
                   else got_answer == ""))
        agree += int(ok)
        rows.append({
            "question": f"{a} : {b} :: {c} : ?",
            "domain": domain,
            "model": got_model,
            "answer": got_answer,
            "refusal": "" if result is None or result.refusal is None
                       else result.refusal,
            "expected_model": model,
            "expected_answer": expected,
            "as_expected": ok,
        })
    return {
        "models": list(MODEL_NAMES),
        "vague_relations": list(VAGUE_RELATIONS),
        "cases": rows,
        "cases_total": len(rows),
        "cases_as_expected": agree,
        "periodic_table": pt.periodic_report(),
    }
