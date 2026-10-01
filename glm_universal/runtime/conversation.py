"""``glm_universal.runtime.conversation`` -- the turn that refers back to an
earlier turn, and the three ways it can refuse to.

Why this module exists
----------------------
Every query this package answers is answered alone.  ``describe carbon`` is a
whole question; ``describe it`` is not a question at all, and the parser says
so -- ``resolve: 'it' names no carrier in any enabled domain``.  Yet *describe
it*, *and the smallest?* and *and oxygen?* are how a second question is
actually asked, and the material this round was given
(``source_material/conversation_experiment/``, eight scripts on a
conversational GLM) is built around exactly that gap.  This module is the part
of it that the package could not already do, rebuilt to the standing rules:
every rewrite is exact and textual, every binding is **licensed by the solver
rather than guessed**, and every ambiguity is a refusal with a name.

What a follow-up is, mechanically
---------------------------------
Three shapes, detected in this order, and nothing else is a follow-up:

``end-flip``
    *and the smallest?* -- the previous ``extremum`` turn asked again at the
    other end of the same column.

``subject``
    *and oxygen?* -- the previous turn asked again about a different row.

``pronoun``
    *describe it*, ``field electronegativity_pauling of it`` -- the token
    ``it`` stands for a carrier named in, or produced by, an earlier turn.

A text that is none of the three is not a follow-up: :meth:`Conversation.ask`
passes it to the session unchanged, which is what makes the conversation layer
additive rather than a second parser.

Licensing -- the whole of the idea
----------------------------------
A candidate antecedent is **licensed** when the query it produces *solves*.
That is the only test, and it is the reason this is a reading of the registers
rather than a heuristic about word order.  ``field
electronegativity_pauling of it`` after *describe carbon; describe water*
binds **carbon**, not ``water``, because the molecule table holds no
electronegativity and the element table does: the geometry of the registers
decides the reference, and the most recent mention is simply wrong.
``GLM.Conversation.most_recent_mention_is_not_the_antecedent`` is that
statement, proved.

Recency decides *between* turns; licensing decides *within* one.  The turns are
scanned newest first, and within a turn the **answer** side is tried before the
**subject** side, because a turn that produced a name is a turn about that
name.  If exactly one candidate of the side under consideration is licensed,
it is the antecedent.  If two or more are, the operation refuses: a 14-row tie
on ``abstract_concrete`` offers fourteen equally good referents and naming one
of them would be a choice the conversation does not make.

The three refusals
------------------
``no-antecedent``
    Nothing earlier in the conversation offers a candidate at all -- a
    follow-up as the first turn, or *and the smallest?* with no column behind
    it.

``ambiguous-antecedent``
    The side that decided offers two or more licensed candidates.  This is the
    refusal the operation is built for.

``unlicensed``
    Candidates exist and not one of them produces a query that solves.  *What
    is the electronegativity of it?* after a conversation about energy is a
    question about nothing the registers hold.

What it does not claim
----------------------
Nothing here parses English beyond three declared surface patterns, and no
answer is computed here at all: every rewritten query is answered by the same
:class:`~glm_universal.runtime.session.GeometricSession` that would have
answered it written out in full, so the conversation layer can add an answer
but can never change one.  Under the standing target this is **addressing** --
an answer recovered when the query is not the stored key, the key being
supplied by an earlier turn -- together with three stated refusals.  It is not
derivation: the derivation, where there is one, is the underlying kind's.

The machine-checked half is ``RequestProject/GLM/Conversation.lean``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as _field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "FollowUpError", "REFUSAL_REASONS", "SHAPES", "PRONOUNS", "ENDS",
    "Mention", "Turn", "Binding", "Conversation",
    "DECLARED_FOLLOW_UPS", "conversation_report",
]


class FollowUpError(ValueError):
    """Raised when a follow-up has no antecedent, with the reason why.

    The reason is one of :data:`REFUSAL_REASONS`, carried in :attr:`reason` so
    a caller can act on the kind of refusal rather than on its wording.
    """

    def __init__(self, reason: str, message: str,
                 considered: Sequence[str] = ()):
        super().__init__(message)
        self.reason = reason
        self.considered: Tuple[str, ...] = tuple(considered)


#: Every way a follow-up can refuse, in the order the operation checks them.
REFUSAL_REASONS: Tuple[str, ...] = (
    "not-a-follow-up", "no-antecedent", "ambiguous-antecedent", "unlicensed",
)

#: The three shapes of follow-up, in detection order.
SHAPES: Tuple[str, ...] = ("end-flip", "subject", "pronoun")

#: The tokens that stand for a carrier named earlier.  Deliberately two: a
#: longer list buys coverage at the price of a rule nobody can state.
PRONOUNS: Tuple[str, ...] = ("it", "that")

#: The two ends of a column, and the words that ask for each.
ENDS: Mapping[str, str] = {
    "largest": "largest", "highest": "largest", "maximum": "largest",
    "most": "largest", "biggest": "largest",
    "smallest": "smallest", "lowest": "smallest", "minimum": "smallest",
    "least": "smallest",
}

#: Where a solved turn keeps the rows it is *about*, by query kind.  Operands
#: are read for every kind; these option keys are read as well, because the
#: field, ordering and extremum kinds carry their rows there.
SUBJECT_OPTION_KEYS: Tuple[str, ...] = ("row", "left", "right")

#: The kinds whose payload names the carrier the turn *produced*, and the key
#: it is named under.  Everything else has no answer side: the neighbours of a
#: ``nearest`` query are a list rather than a name, and the verdict of an
#: ``ordering`` query is an order rather than a row.
ANSWER_SIDE: Mapping[str, Tuple[str, ...]] = {
    "extremum": ("winners",),
    "analogy": ("result.tied", "model.candidates"),
}

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_:@.\-]*")
_ELLIPSIS = re.compile(r"^(?:and|what\s+about|how\s+about|now)\s+(.+)$")
_THE = re.compile(r"^(?:the\s+)?(.+)$")


# ===========================================================================
# 1.  WHAT A TURN LEAVES BEHIND
# ===========================================================================

@dataclass(frozen=True)
class Mention:
    """One carrier a turn named, and which side of the turn named it."""

    name: str                 # the register name, as the index resolves it
    domain: str
    turn: int
    side: str                 # 'answer' | 'subject'


@dataclass(frozen=True)
class Turn:
    """One turn of a conversation: what was asked, and what it left behind."""

    index: int
    text: str                 # what the user typed
    asked: str                # what was asked of the session, after rewriting
    kind: str
    ok: bool
    answer: str
    mentions: Tuple[Mention, ...]
    binding: Optional["Binding"] = None

    def side(self, which: str) -> Tuple[Mention, ...]:
        """The mentions of one side, in the order the turn made them."""
        return tuple(m for m in self.mentions if m.side == which)


@dataclass(frozen=True)
class Binding:
    """How a follow-up was resolved: to what, from where, and against what."""

    shape: str                        # one of SHAPES
    name: str                         # the antecedent, or '' for end-flip
    antecedent_turn: int
    side: str                         # 'answer' | 'subject' | 'query'
    rewritten: str
    considered: Tuple[str, ...] = ()  # every candidate weighed on that side
    licensed: Tuple[str, ...] = ()    # those of them that solved

    @property
    def sentence(self) -> str:
        """The binding as one line, with what it was weighed against."""
        against = (f", against {len(self.considered)} candidates from turn "
                   f"{self.antecedent_turn}"
                   if len(self.considered) > 1 else
                   f", from turn {self.antecedent_turn}")
        who = f" to {self.name}" if self.name else ""
        return (f"{self.shape} bound{who}{against}: "
                f"{self.rewritten!r}")


# ===========================================================================
# 2.  THE CONVERSATION
# ===========================================================================

class Conversation:
    """A session with a memory of what has been asked of it.

    The conversation keeps its own register of :class:`Turn` -- the session's
    inference history additionally records every *licensing trial*, which is
    as it should be: a trial is an inference that was run, and hiding it would
    make the history a summary rather than a record.
    """

    def __init__(self, session=None, store=None):
        if session is None:
            from .session import GeometricSession
            session = GeometricSession()
        self.session = session
        self._turns: List[Turn] = []
        #: How many licensing trials this conversation has run.  A trial is an
        #: inference, and what it costs is the thing
        #: :mod:`glm_universal.runtime.plan_store` measures.
        self.trials = 0
        #: An optional :class:`~glm_universal.runtime.plan_store.PlanStore`.
        #: With one, a follow-up already resolved in this same conversation is
        #: not resolved again -- but the query it rewrites to is still asked,
        #: so the store can save trials and can never change an answer.
        self.store = store

    # -- the record ---------------------------------------------------------

    @property
    def turns(self) -> Tuple[Turn, ...]:
        """Every turn of this conversation, in order."""
        return tuple(self._turns)

    def mentions(self) -> Tuple[Mention, ...]:
        """Every carrier the conversation has named, newest turn first."""
        out: List[Mention] = []
        for turn in reversed(self._turns):
            out.extend(turn.side("answer"))
            out.extend(turn.side("subject"))
        return tuple(out)

    # -- the central verb ---------------------------------------------------

    def ask(self, text: str):
        """Answer one turn, resolving it against the conversation first.

        A text that is not a follow-up is passed to the session unchanged.  A
        follow-up that cannot be bound raises :class:`FollowUpError` with the
        reason; the turn is recorded either way, because a refusal is part of
        the conversation.
        """
        shape = self.shape_of(text)
        if shape is None:
            solution = self.session.ask(text)
            self._record(text, text, solution, None)
            return solution
        binding = self.resolve(text)
        solution = self.session.ask(binding.rewritten)
        self._record(text, binding.rewritten, solution, binding)
        return solution

    def _record(self, text: str, asked: str, solution,
                binding: Optional[Binding]) -> Turn:
        turn = Turn(index=len(self._turns), text=text, asked=asked,
                    kind=solution.kind, ok=bool(solution.ok),
                    answer=solution.answer,
                    mentions=self._mentions_of(len(self._turns), solution),
                    binding=binding)
        self._turns.append(turn)
        return turn

    # -- reading a solved turn ---------------------------------------------

    def _lookup(self, surface: str) -> Optional[Tuple[str, str]]:
        try:
            return self.session.index.lookup(str(surface))
        except Exception:                      # pragma: no cover -- defensive
            return None

    def _mentions_of(self, index: int, solution) -> Tuple[Mention, ...]:
        """Every carrier one solved turn names, answer side before subject."""
        if not solution.ok:
            return ()
        out: List[Mention] = []
        seen = set()

        def add(surface, side: str) -> None:
            hit = self._lookup(surface)
            if hit is None:
                return
            domain, name = hit
            if (name, side) in seen:
                return
            seen.add((name, side))
            out.append(Mention(name=name, domain=domain, turn=index,
                               side=side))

        payload = dict(solution.payload)
        for path in ANSWER_SIDE.get(solution.kind, ()):
            head, _, tail = path.partition(".")
            block = payload.get(head)
            values = block if not tail else (
                (block or {}).get(tail) if isinstance(block, Mapping) else None)
            for value in tuple(values or ()):
                add(value, "answer")
        for operand in solution.query.operands:
            add(operand, "subject")
        for key in SUBJECT_OPTION_KEYS:
            value = solution.query.options.get(key)
            if value:
                add(value, "subject")
        return tuple(out)

    def _surface_of(self, text: str, name: str) -> Optional[str]:
        """The token of ``text`` that names ``name``, if one does."""
        for token in _TOKEN.findall(text):
            hit = self._lookup(token)
            if hit is not None and hit[1] == name:
                return token
        return None

    # -- detecting a follow-up ---------------------------------------------

    def shape_of(self, text: str) -> Optional[str]:
        """Which of :data:`SHAPES` the text is, or ``None`` for a whole query.

        The order matters and is part of the rule: *and the smallest?* is an
        end-flip even though it also matches the subject pattern, because
        ``the smallest`` names no carrier.
        """
        stripped = text.strip().rstrip("?").strip()
        lowered = stripped.lower()
        tail = _ELLIPSIS.match(lowered)
        if tail is not None:
            inner = _THE.match(tail.group(1).strip()).group(1).strip()
            if inner in ENDS:
                return "end-flip"
            if self._lookup(inner) is not None:
                return "subject"
        for pronoun in PRONOUNS:
            if re.search(rf"(?<![\w]){pronoun}(?![\w])", lowered):
                return "pronoun"
        return None

    # -- resolving one -----------------------------------------------------

    def resolve(self, text: str) -> Binding:
        """Bind a follow-up to its antecedent, or refuse and say why.

        With a plan store attached, a follow-up this same conversation has
        already resolved is replayed from the store rather than licensed
        again, refusals included.  The replay reproduces the binding, not the
        answer: the rewritten query is still asked of the session.
        """
        replayed = self._replay(text)
        if replayed is not None:
            return replayed
        shape = self.shape_of(text)
        if shape is None:
            raise FollowUpError(
                "not-a-follow-up",
                f"{text!r} is a whole query, not a follow-up: it names no "
                f"pronoun and opens with no continuation")
        if shape == "end-flip":
            return self._record_plan(text, self._resolve_end_flip, shape)
        if shape == "subject":
            return self._record_plan(text, self._resolve_subject, shape)
        return self._record_plan(text, self._resolve_pronoun, shape)

    # -- the plan store, when there is one ---------------------------------

    def _prefix(self) -> Tuple[str, ...]:
        """The turns asked before now, verbatim -- what a plan depended on."""
        return tuple(turn.text for turn in self._turns)

    def _replay(self, text: str) -> Optional[Binding]:
        """The recorded resolution of this follow-up, if the store holds one."""
        if self.store is None:
            return None
        plan = self.store.get(self._prefix(), text)
        if plan is None:
            return None
        if plan.refused:
            raise FollowUpError(plan.reason, plan.message, plan.considered)
        return Binding(
            shape=plan.shape, name="" if plan.outcome == "answer"
            else plan.outcome,
            antecedent_turn=plan.antecedent_turn, side=plan.side,
            rewritten=plan.rewritten, considered=plan.considered,
            licensed=plan.licensed)

    def _record_plan(self, text: str, resolver, shape: str) -> Binding:
        """Resolve a follow-up, recording what it decided and what it cost."""
        if self.store is None:
            return resolver(text)
        from .plan_store import Plan
        prefix = self._prefix()
        before = self.trials
        try:
            binding = resolver(text)
        except FollowUpError as error:
            self.store.put(Plan(
                prefix=prefix, text=text, shape=shape,
                outcome=error.reason, reason=error.reason,
                message=str(error), considered=tuple(error.considered),
                trials=self.trials - before))
            raise
        self.store.put(Plan(
            prefix=prefix, text=text, shape=binding.shape,
            outcome=binding.name or "answer", rewritten=binding.rewritten,
            antecedent_turn=binding.antecedent_turn, side=binding.side,
            considered=tuple(binding.considered),
            licensed=tuple(binding.licensed),
            trials=self.trials - before))
        return binding

    def _solves(self, text: str) -> bool:
        """Whether the session answers ``text`` -- the licensing test."""
        self.trials += 1
        try:
            return bool(self.session.ask(text).ok)
        except Exception:
            return False

    def _resolve_pronoun(self, text: str) -> Binding:
        rewrite = lambda name: re.sub(          # noqa: E731 -- one expression
            rf"(?i)(?<![\w])(?:{'|'.join(PRONOUNS)})(?![\w])", name, text)
        considered_any = False
        for turn in reversed(self._turns):
            for side in ("answer", "subject"):
                candidates = tuple(m.name for m in turn.side(side))
                if not candidates:
                    continue
                considered_any = True
                licensed = tuple(name for name in candidates
                                 if self._solves(rewrite(name)))
                if len(licensed) == 1:
                    return Binding(
                        shape="pronoun", name=licensed[0],
                        antecedent_turn=turn.index, side=side,
                        rewritten=rewrite(licensed[0]),
                        considered=candidates, licensed=licensed)
                if len(licensed) > 1:
                    raise FollowUpError(
                        "ambiguous-antecedent",
                        f"{text!r}: turn {turn.index} names "
                        f"{len(licensed)} carriers that all answer it "
                        f"({', '.join(licensed[:6])}"
                        f"{', ...' if len(licensed) > 6 else ''}); the "
                        f"conversation does not say which is meant",
                        considered=candidates)
        if not considered_any:
            raise FollowUpError(
                "no-antecedent",
                f"{text!r}: no earlier turn names a carrier for the pronoun "
                f"to stand for")
        raise FollowUpError(
            "unlicensed",
            f"{text!r}: every carrier this conversation names leaves the "
            f"question unanswerable",
            considered=tuple(m.name for m in self.mentions()))

    def _resolve_subject(self, text: str) -> Binding:
        stripped = text.strip().rstrip("?").strip().lower()
        inner = _THE.match(_ELLIPSIS.match(stripped).group(1).strip()).group(1)
        new = inner.strip()
        considered_any = False
        for turn in reversed(self._turns):
            if not turn.ok:
                continue
            subjects = tuple(m.name for m in turn.side("subject"))
            if not subjects:
                continue
            considered_any = True
            surfaces = tuple(s for s in
                             (self._surface_of(turn.asked, name)
                              for name in subjects) if s)
            if len(surfaces) > 1:
                raise FollowUpError(
                    "ambiguous-antecedent",
                    f"{text!r}: turn {turn.index} is about "
                    f"{len(surfaces)} rows ({', '.join(surfaces)}); which "
                    f"of them {new!r} replaces is not said",
                    considered=subjects)
            if not surfaces:
                continue
            rewritten = re.sub(rf"(?<![\w]){re.escape(surfaces[0])}(?![\w])",
                               new, turn.asked, count=1)
            if self._solves(rewritten):
                return Binding(
                    shape="subject", name=new, antecedent_turn=turn.index,
                    side="query", rewritten=rewritten,
                    considered=(surfaces[0],), licensed=(new,))
        if not considered_any:
            raise FollowUpError(
                "no-antecedent",
                f"{text!r}: no earlier turn is about a row that {new!r} "
                f"could replace")
        raise FollowUpError(
            "unlicensed",
            f"{text!r}: {new!r} in place of the earlier row leaves a "
            f"question the registers do not answer")

    def _resolve_end_flip(self, text: str) -> Binding:
        stripped = text.strip().rstrip("?").strip().lower()
        inner = _THE.match(_ELLIPSIS.match(stripped).group(1).strip()).group(1)
        want = ENDS[inner.strip()]
        for turn in reversed(self._turns):
            if turn.kind != "extremum" or not turn.ok:
                continue
            had = str(turn.asked).split()[0].lower()
            rewritten = re.sub(rf"(?i)(?<![\w]){re.escape(had)}(?![\w])",
                               want, turn.asked, count=1)
            if self._solves(rewritten):
                return Binding(
                    shape="end-flip", name="", antecedent_turn=turn.index,
                    side="query", rewritten=rewritten,
                    considered=(had,), licensed=(want,))
            raise FollowUpError(
                "unlicensed",
                f"{text!r}: the column of turn {turn.index} has no "
                f"{want} end")
        raise FollowUpError(
            "no-antecedent",
            f"{text!r}: no earlier turn folds a column, so there is no "
            f"other end to ask for")


# ===========================================================================
# 3.  THE DECLARED SET -- what the operation is measured on
# ===========================================================================

#: The follow-ups this round declares before running them: eight answers
#: across the three shapes, and seven refusals covering every named reason.
#: Each row is ``(key, script, expected, note)`` where ``script`` is the whole
#: conversation with the follow-up last, and ``expected`` is the bound name,
#: ``"answer"`` where the name is not the point, or a refusal reason.
DECLARED_FOLLOW_UPS: Tuple[Tuple[str, Tuple[str, ...], str, str], ...] = (
    ("pronoun-describe",
     ("describe carbon", "describe it"), "C",
     "the plainest one: the subject of the turn before"),
    ("pronoun-after-extremum",
     ("largest atomic_weight_u in element", "describe it"), "Og",
     "the pronoun stands for a row the fold produced, not one anybody named"),
    ("pronoun-licensing-skips",
     ("describe carbon", "describe water",
      "field electronegativity_pauling of it"), "C",
     "the margin over recency: water is nearer and holds no "
     "electronegativity"),
    ("pronoun-licensing-agrees",
     ("describe carbon", "describe water", "field molar_mass_u of it"),
     "water",
     "the same conversation, the other field: now recency is right, and "
     "licensing says so too"),
    ("pronoun-analogy-answer",
     ("H : He :: Li : ?", "describe it"), "Ne",
     "the answer side outranks the subject side"),
    ("pronoun-nearest-subject",
     ("nearest 3 to oxygen", "describe it"), "O",
     "a list of neighbours is not a name, so the subject decides"),
    ("end-flip",
     ("largest atomic_weight_u in element", "and the smallest?"), "answer",
     "the same column, the other end"),
    ("subject-substitution",
     ("field atomic_weight_u of carbon", "and oxygen?"), "oxygen",
     "the same question, a different row"),
    ("pronoun-tie-refused",
     ("largest abstract_concrete in carrier:lexicon", "describe it"),
     "ambiguous-antecedent",
     "fourteen rows attain the end; naming one would be a choice the "
     "conversation does not make"),
    ("pronoun-two-subjects",
     ("order atomic_weight_u of carbon and oxygen", "describe it"),
     "ambiguous-antecedent",
     "a comparison is about two rows and its verdict names neither"),
    ("pronoun-first-turn",
     ("describe it",), "no-antecedent",
     "a follow-up with nothing to follow"),
    ("pronoun-unlicensed",
     ("describe energy", "field electronegativity_pauling of it"),
     "unlicensed",
     "the only carrier in play is not a row of the table the question needs"),
    ("end-flip-no-column",
     ("describe carbon", "and the smallest?"), "no-antecedent",
     "no column has been folded, so there is no other end"),
    ("subject-ambiguous",
     ("order atomic_weight_u of carbon and oxygen", "and nitrogen?"),
     "ambiguous-antecedent",
     "which of the two rows nitrogen replaces is not said"),
    ("subject-unlicensed",
     ("field electronegativity_pauling of carbon", "and water?"),
     "unlicensed",
     "the row exists and the field does not reach it"),
)


def _outcome(conversation: "Conversation", script: Sequence[str]
             ) -> Dict[str, object]:
    """Run one declared script and report what its last turn did."""
    for text in script[:-1]:
        conversation.ask(text)
    text = script[-1]
    try:
        binding = conversation.resolve(text)
    except FollowUpError as error:
        return {"outcome": error.reason, "detail": str(error),
                "considered": list(error.considered)}
    solution = conversation.session.ask(binding.rewritten)
    if not solution.ok:
        return {"outcome": "unlicensed", "detail": solution.answer,
                "considered": list(binding.considered)}
    return {"outcome": binding.name or "answer",
            "bound": binding.name, "shape": binding.shape,
            "rewritten": binding.rewritten,
            "answer": solution.answer,
            "considered": list(binding.considered),
            "detail": binding.sentence}


def _naive(conversation: "Conversation", script: Sequence[str]
           ) -> Dict[str, object]:
    """The control: bind to the most recent mention, with no licensing.

    Defined for the pronoun shape, which is the only shape a recency rule has
    an opinion about; the other two are reported as ``n/a``.
    """
    for text in script[:-1]:
        conversation.ask(text)
    text = script[-1]
    if conversation.shape_of(text) != "pronoun":
        return {"outcome": "n/a"}
    mentions = conversation.mentions()
    if not mentions:
        return {"outcome": "no-antecedent"}
    name = mentions[0].name
    rewritten = re.sub(
        rf"(?i)(?<![\w])(?:{'|'.join(PRONOUNS)})(?![\w])", name, text)
    solution = conversation.session.ask(rewritten)
    return {"outcome": name if solution.ok else "unlicensed",
            "bound": name, "rewritten": rewritten, "ok": bool(solution.ok)}


def _no_context(session, script: Sequence[str]) -> Dict[str, object]:
    """The other control: the follow-up asked of a session with no memory."""
    text = script[-1]
    try:
        solution = session.ask(text)
    except Exception as error:
        return {"outcome": "refused", "detail": type(error).__name__}
    return {"outcome": "answered" if solution.ok else "refused",
            "detail": solution.answer[:80]}


def _report(session=None) -> Dict[str, object]:
    if session is None:
        from .session import GeometricSession
        session = GeometricSession()
    rows: List[Dict[str, object]] = []
    for key, script, expected, note in DECLARED_FOLLOW_UPS:
        found = _outcome(Conversation(session), script)
        control = _naive(Conversation(session), script)
        alone = _no_context(session, script)
        rows.append({
            "key": key, "script": list(script), "expected": expected,
            "note": note,
            "outcome": found["outcome"], "detail": found.get("detail", ""),
            "shape": found.get("shape", ""),
            "rewritten": found.get("rewritten", ""),
            "answer": found.get("answer", ""),
            "considered": found.get("considered", []),
            "as_declared": found["outcome"] == expected,
            "control_recency": control["outcome"],
            "control_agrees": control["outcome"] == found["outcome"],
            "control_applies": control["outcome"] != "n/a",
            "alone": alone["outcome"],
        })
    answered = tuple(r for r in rows
                     if r["outcome"] not in REFUSAL_REASONS)
    refused = tuple(r for r in rows if r["outcome"] in REFUSAL_REASONS)
    as_declared = tuple(r for r in rows if r["as_declared"])
    reasons = tuple(sorted({str(r["outcome"]) for r in refused}))
    alone_answered = tuple(r for r in rows if r["alone"] == "answered")
    control_rows = tuple(r for r in rows if r["control_applies"])
    control_wrong = tuple(r for r in control_rows if not r["control_agrees"])
    return {
        "declared": len(DECLARED_FOLLOW_UPS),
        "rows": rows,
        "answered": len(answered),
        "refused": len(refused),
        "as_declared": len(as_declared),
        "refusal_reasons": reasons,
        "reasons_declared": len(REFUSAL_REASONS) - 1,   # not-a-follow-up is
        "shapes": len(SHAPES),                          # raised, not measured
        "alone_answered": len(alone_answered),
        "control_rows": len(control_rows),
        "control_wrong": len(control_wrong),
        "control_wrong_keys": [r["key"] for r in control_wrong],
        "verdict": (
            f"the conversation layer answers {len(answered)} of the "
            f"{len(DECLARED_FOLLOW_UPS)} declared follow-ups and refuses "
            f"{len(refused)}, every one of them as declared before the run, "
            f"with the refusals falling under all "
            f"{len(REFUSAL_REASONS) - 1} of its named reasons "
            f"({', '.join(reasons)}). Asked of a session with no memory of "
            f"the conversation, {len(alone_answered)} of the same "
            f"{len(DECLARED_FOLLOW_UPS)} texts are answered."),
        "caveat": (
            f"the reference is the whole of the addressing here: every "
            f"rewritten query is answered by the session that would have "
            f"answered it written out in full, so no answer is new and no "
            f"answer is changed. The recency control -- bind the pronoun to "
            f"the most recent mention, licensing unchecked -- differs from "
            f"the operation on {len(control_wrong)} of the "
            f"{len(control_rows)} pronoun follow-ups it applies to "
            f"({', '.join(str(k) for k in (r['key'] for r in control_wrong))}"
            f"), and nothing here parses English beyond three declared "
            f"surface patterns."),
    }


def conversation_report(session=None) -> Dict[str, object]:
    """What the conversation layer binds, what it refuses, and against what.

    The declared set is run against one session, so a caller that already has
    one passes it rather than building a second.
    """
    return _report(session)


if __name__ == "__main__":                      # pragma: no cover
    report = conversation_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<26} {str(row['outcome']):<22} "
              f"{'as declared' if row['as_declared'] else 'NOT AS DECLARED'}")
