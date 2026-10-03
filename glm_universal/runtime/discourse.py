"""``glm_universal.runtime.discourse`` -- discourse state: a set carried as a
column, the fourth shape of follow-up, and follow-ups bound on every surface.

Round 5 of the order of work (``studies/DISCOURSE_STATE_STUDY.md``, Phase
92).  :mod:`glm_universal.runtime.conversation` binds three surface shapes of
follow-up and refuses everything else.  This module is that layer with the
three things its own study named as the next round, in the order the roadmap
gave them:

0b -- a tie carried as a column
    A fold whose end is attained by several rows **produced a set**.  A later
    *it* or *them* names the set, so the question is asked of every row and
    the answer is the column of their answers, in the fold's order, rather
    than the refusal ``ambiguous-antecedent``.  The column is answered only
    when every row answers; a row that does not is a hole and the column is
    refused ``column-incomplete`` -- unless no row answers at all, when the
    set does not decide and older turns are read, as for any unlicensed side.
    A column turn produces the same set again, so the set is *carried*.  A
    comparison's two rows are not a set the turn produced: *it* after one is
    still ambiguous.

D = 0a -- the fourth shape
    Three phrasings that are not a substitution into one earlier query:
    *the one before that* (the referent of the deciding turn **before** the
    one *that* names), the plural pronouns *them*, *both of them*, *each of
    them*, *all of them* (a set-valued referent: the set a turn produced, the
    rows a turn was about, or -- for *both* only, whose number is stated --
    the single rows of the two newest deciding turns), and *why?* (the turn
    before it, explained from the record: its binding, its refusal or its own
    derivation).  A plural with one referent, or *both* with other than two,
    is refused ``number-mismatch``.

K3 -- follow-ups bound on every surface
    The licensing test is a parameter.  With ``surfaces=True`` a candidate is
    licensed when the **multi-surface router** answers the rewritten text, so
    a follow-up whose rewritten question only the typed or the stepwise
    planner reads is bound; and a turn some other surface answered names the
    register rows written in its question.

What it does not claim
----------------------
No answer is computed here.  Every row of a column, and every single
binding, is answered by the same asker that would answer the rewritten text
written out in full (mark D6), so the layer can add answers and can never
change one.  *why?* re-reads the record and computes nothing.  Nothing here
parses English beyond the declared phrasings.

The machine-checked half is ``RequestProject/GLM/DiscourseState.lean``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .conversation import (Binding, Conversation, FollowUpError, Mention,
                           PRONOUNS, REFUSAL_REASONS as _BASE_REASONS,
                           SHAPES as _BASE_SHAPES, Turn)

__all__ = [
    "REFUSAL_REASONS", "SHAPES", "PLURALS", "PRIOR", "COLUMN_KINDS",
    "ROW_DOMAINS", "ColumnBinding", "Discourse",
]

#: Every refusal, the base layer's and the two this round adds.
REFUSAL_REASONS: Tuple[str, ...] = _BASE_REASONS + (
    "column-incomplete", "number-mismatch")

#: The six shapes, in detection order: the three new ones first, because
#: *the one before that* holds the pronoun *that* and *why?* holds none.
SHAPES: Tuple[str, ...] = ("why", "prior", "plural") + _BASE_SHAPES

#: The plural phrasings, longest first, with the number each states (``None``
#: for an unstated number).
PLURALS: Tuple[Tuple[str, Optional[int]], ...] = (
    ("both of them", 2), ("each of them", None), ("all of them", None),
    ("them", None),
)

#: The prior phrasing.
PRIOR = "the one before that"

_WHY = re.compile(r"^(?:why|why is that|explain|explain that)$")

#: Verb phrases of the grammar that hold the word *it* without referring:
#: ``is it true that ...`` is a whole query, not a follow-up.
_IDIOMS = ("is it true that", "does it hold that")

#: The kinds whose answer side, when it holds two or more rows, is a set the
#: turn **produced**: a fold's tied winners, and a column turn's rows.
COLUMN_KINDS: Tuple[str, ...] = ("extremum", "column")

#: The domains whose carriers are register rows -- what a routed turn's
#: question is read for when its surface reports no operands (K3).
ROW_DOMAINS: Tuple[str, ...] = ("chemistry", "molecules")


@dataclass(frozen=True)
class ColumnBinding:
    """A follow-up bound to a set: every row, and the text asked of each."""

    shape: str
    members: Tuple[str, ...]
    antecedent_turn: int
    side: str
    rewritten: Tuple[str, ...]
    considered: Tuple[str, ...] = ()

    @property
    def sentence(self) -> str:
        return (f"{self.shape} bound to the {len(self.members)} rows "
                f"{', '.join(self.members)} of turn {self.antecedent_turn}")


# What one side of one turn decides, for a given rewrite.
_Decision = Tuple[str, Tuple[str, ...], Tuple[str, ...]]
#   ("one", (name,), candidates) | ("set", members, candidates)
#   ("multi", licensed, candidates) | ("incomplete", missing, members)


class Discourse(Conversation):
    """A conversation with discourse state: sets, the fourth shape, and any
    surface as the licence.

    ``surfaces=False`` licenses through the session alone, as Phase 55 did;
    ``surfaces=True`` through :func:`glm_universal.runtime.router.
    ask_routed`.  ``carry=False`` turns 0b off -- a tie is refused as
    before -- and is the round's own control.
    """

    def __init__(self, session=None, surfaces: bool = False,
                 carry: bool = True,
                 asker: Optional[Callable[[str], object]] = None):
        super().__init__(session)
        self.surfaces = surfaces
        self.carry = carry
        if asker is None:
            if surfaces:
                from .router import ask_routed
                asker = lambda text: ask_routed(self.session, text)  # noqa
            else:
                asker = self.session.ask
        self._asker = asker
        self._groups: Dict[int, Tuple[str, ...]] = {}
        self._solutions: Dict[int, object] = {}
        self._refusals: Dict[int, FollowUpError] = {}
        self._columns: Dict[int, ColumnBinding] = {}

    # -- asking -------------------------------------------------------------

    def _ask_one(self, text: str):
        return self._asker(text)

    def _solves(self, text: str) -> bool:
        self.trials += 1
        try:
            return bool(self._ask_one(text).ok)
        except Exception:
            return False

    def ask(self, text: str):
        """Answer one turn.  A refusal is recorded as a turn and re-raised."""
        shape = self.shape_of(text)
        if shape is None:
            solution = self._ask_one(text)
            self._record(text, text, solution, None)
            return solution
        if shape != "why":
            # whole first: a text the asker already answers as written is a
            # whole query, whatever words it holds -- so the layer can never
            # change an answer the machine gives alone
            alone = self._ask_one(text)
            if alone.ok:
                self._record(text, text, alone, None)
                return alone
        try:
            if shape == "why":
                solution = self._why(text)
                self._record(text, text, solution, None)
                return solution
            binding = self.resolve(text)
        except FollowUpError as error:
            self._record_refusal(text, error)
            raise
        if isinstance(binding, ColumnBinding):
            solution = self._column(text, binding)
            self._record(text, text, solution, None)
            self._columns[len(self._turns) - 1] = binding
            return solution
        solution = self._ask_one(binding.rewritten)
        self._record(text, binding.rewritten, solution, binding)
        return solution

    def _record(self, text, asked, solution, binding):
        turn = super()._record(text, asked, solution, binding)
        self._solutions[turn.index] = solution
        if self.carry and solution.ok and solution.kind in COLUMN_KINDS:
            answers = tuple(m.name for m in turn.side("answer"))
            if len(answers) >= 2:
                self._groups[turn.index] = answers
        return turn

    def _record_refusal(self, text: str, error: FollowUpError) -> None:
        turn = Turn(index=len(self._turns), text=text, asked=text,
                    kind="refused", ok=False, answer=str(error),
                    mentions=())
        self._turns.append(turn)
        self._refusals[turn.index] = error

    # -- what a turn names --------------------------------------------------

    def _mentions_of(self, index: int, solution) -> Tuple[Mention, ...]:
        if not solution.ok:
            return ()
        if solution.kind == "column":
            out = []
            for name in solution.payload.get("members", ()):
                hit = self._lookup(name)
                if hit is not None:
                    out.append(Mention(name=hit[1], domain=hit[0],
                                       turn=index, side="answer"))
            return tuple(out)
        if solution.kind == "why":
            return ()
        found = super()._mentions_of(index, solution)
        if self.surfaces and not found:
            found = self._rows_written_in(index, solution.query.raw)
        return found

    def _rows_written_in(self, index: int, text: str) -> Tuple[Mention, ...]:
        """The register rows a question names, longest phrase first (K3).

        Read only when the surface that answered reports no operand the index
        resolves -- a turn the typed or the stepwise planner answered."""
        words = re.findall(r"[A-Za-z][A-Za-z0-9()\-]*", text)
        out: List[Mention] = []
        seen = set()
        i = 0
        while i < len(words):
            hit = None
            for n in (3, 2, 1):
                if i + n > len(words):
                    continue
                phrase = " ".join(words[i:i + n])
                cand = self._lookup(phrase)
                if cand is not None and cand[0] in ROW_DOMAINS:
                    hit = (cand, n)
                    break
            if hit is None:
                i += 1
                continue
            (domain, name), n = hit
            if name not in seen:
                seen.add(name)
                out.append(Mention(name=name, domain=domain, turn=index,
                                   side="subject"))
            i += n
        return tuple(out)

    def _surface_of(self, text: str, name: str) -> Optional[str]:
        found = super()._surface_of(text, name)
        if found is not None or not self.surfaces:
            return found
        words = re.findall(r"[A-Za-z][A-Za-z0-9()\-]*", text)
        for n in (3, 2):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i + n])
                hit = self._lookup(phrase)
                if hit is not None and hit[1] == name:
                    return phrase
        return None

    # -- detecting a follow-up ---------------------------------------------

    def shape_of(self, text: str) -> Optional[str]:
        stripped = text.strip().rstrip("?").strip()
        lowered = stripped.lower()
        if _WHY.match(lowered):
            return "why"
        if PRIOR in lowered:
            return "prior"
        for phrase, _ in PLURALS:
            if re.search(rf"(?<![\w]){phrase}(?![\w])", lowered):
                return "plural"
        for idiom in _IDIOMS:
            if lowered.startswith(idiom):
                rest = lowered[len(idiom):]
                if not any(re.search(rf"(?<![\w]){p}(?![\w])", rest)
                           for p in PRONOUNS):
                    return None
        return super().shape_of(text)

    @staticmethod
    def _plural_of(text: str) -> Tuple[str, Optional[int]]:
        lowered = text.lower()
        for phrase, number in PLURALS:
            if re.search(rf"(?<![\w]){phrase}(?![\w])", lowered):
                return phrase, number
        raise ValueError(text)                 # pragma: no cover

    # -- resolving ----------------------------------------------------------

    def resolve(self, text: str):
        shape = self.shape_of(text)
        if shape == "prior":
            return self._resolve_prior(text)
        if shape == "plural":
            return self._resolve_plural(text)
        if shape == "pronoun":
            return self._resolve_singular(text)
        if shape == "why":
            raise FollowUpError("not-a-follow-up",
                                "why? is answered from the record, not bound")
        return super().resolve(text)

    @staticmethod
    def _rewriter(text: str, phrase_pattern: str) -> Callable[[str], str]:
        pattern = re.compile(rf"(?i)(?<![\w])(?:{phrase_pattern})(?![\w])")
        return lambda name: pattern.sub(lambda _m: name, text, count=1)

    def _decide(self, turn: Turn, side: str, rewrite, plural: bool
                ) -> Optional[_Decision]:
        """What one side of one turn decides for this rewrite, or ``None``."""
        candidates = tuple(m.name for m in turn.side(side))
        if not candidates:
            return None
        is_set = (side == "answer" and turn.index in self._groups)
        if is_set or (plural and len(candidates) >= 2):
            members = self._groups.get(turn.index, candidates) \
                if is_set else candidates
            licensed = tuple(n for n in members if self._solves(rewrite(n)))
            if not licensed:
                return None
            if len(licensed) == len(members):
                return ("set", members, candidates)
            missing = tuple(n for n in members if n not in licensed)
            return ("incomplete", missing, members)
        licensed = tuple(n for n in candidates if self._solves(rewrite(n)))
        if not licensed:
            return None
        if len(licensed) == 1:
            return ("one", licensed, candidates)
        return ("multi", licensed, candidates)

    def _decisions(self, rewrite, plural: bool, start: int = None):
        """Every deciding side, newest turn first: ``(turn, side, decision)``.
        One per turn: the first side of a turn that decides is that turn's."""
        turns = self._turns if start is None else self._turns[:start]
        for turn in reversed(turns):
            for side in ("answer", "subject"):
                d = self._decide(turn, side, rewrite, plural)
                if d is not None:
                    yield turn, side, d
                    break

    def _no_decision(self, text: str, what: str):
        if not self.mentions():
            return FollowUpError(
                "no-antecedent",
                f"{text!r}: no earlier turn names a carrier for {what} to "
                f"stand for")
        return FollowUpError(
            "unlicensed",
            f"{text!r}: every carrier this conversation names leaves the "
            f"question unanswerable",
            considered=tuple(m.name for m in self.mentions()))

    def _bind(self, text: str, shape: str, turn: Turn, side: str,
              d: _Decision, rewrite):
        """Turn a singular decision into a binding or a refusal."""
        kind, names, candidates = d
        if kind == "one":
            return Binding(shape=shape, name=names[0],
                           antecedent_turn=turn.index, side=side,
                           rewritten=rewrite(names[0]),
                           considered=candidates, licensed=names)
        if kind == "set":
            return ColumnBinding(shape=shape, members=names,
                                 antecedent_turn=turn.index, side=side,
                                 rewritten=tuple(rewrite(n) for n in names),
                                 considered=candidates)
        if kind == "incomplete":
            raise FollowUpError(
                "column-incomplete",
                f"{text!r}: turn {turn.index} produced a set of "
                f"{len(candidates)} rows and {len(names)} of them do not "
                f"answer the question ({', '.join(names[:6])}"
                f"{', ...' if len(names) > 6 else ''}); a hole refuses the "
                f"column", considered=candidates)
        raise FollowUpError(
            "ambiguous-antecedent",
            f"{text!r}: turn {turn.index} names {len(names)} carriers that "
            f"all answer it ({', '.join(names[:6])}"
            f"{', ...' if len(names) > 6 else ''}); the conversation does "
            f"not say which is meant", considered=candidates)

    def _resolve_singular(self, text: str):
        if not self.carry:
            return super()._resolve_pronoun(text)
        rewrite = self._rewriter(text, "|".join(PRONOUNS))
        for turn, side, d in self._decisions(rewrite, plural=False):
            return self._bind(text, "pronoun", turn, side, d, rewrite)
        raise self._no_decision(text, "the pronoun")

    def _resolve_prior(self, text: str):
        rewrite = self._rewriter(text, re.escape(PRIOR))
        found = None
        for turn, side, d in self._decisions(rewrite, plural=False):
            found = turn
            break
        if found is None:
            raise self._no_decision(text, "the one before that")
        for turn, side, d in self._decisions(rewrite, plural=False,
                                             start=found.index):
            return self._bind(text, "prior", turn, side, d, rewrite)
        raise FollowUpError(
            "no-antecedent",
            f"{text!r}: 'that' is turn {found.index}, and nothing was named "
            f"before it")

    def _resolve_plural(self, text: str):
        phrase, number = self._plural_of(text)
        rewrite = self._rewriter(text, re.escape(phrase))
        decisions = self._decisions(rewrite, plural=True)
        first = next(decisions, None)
        if first is None:
            raise self._no_decision(text, f"{phrase!r}")
        turn, side, d = first
        kind, names, candidates = d
        if kind == "incomplete":
            return self._bind(text, "plural", turn, side, d, rewrite)
        if kind == "set":
            if number is not None and len(names) != number:
                raise FollowUpError(
                    "number-mismatch",
                    f"{text!r}: {phrase!r} names {number} rows and turn "
                    f"{turn.index} offers {len(names)}",
                    considered=candidates)
            return self._bind(text, "plural", turn, side, d, rewrite)
        # a single row: only *both*, whose number is stated, reads on
        if number != 2 or kind != "one":
            raise FollowUpError(
                "number-mismatch",
                f"{text!r}: {phrase!r} is plural and the deciding turn "
                f"{turn.index} offers one row ({names[0]})",
                considered=candidates)
        second = next(decisions, None)
        if second is None or second[2][0] != "one":
            raise FollowUpError(
                "number-mismatch",
                f"{text!r}: {phrase!r} names two rows and the conversation "
                f"offers one single row ({names[0]}) before any other",
                considered=candidates)
        older_turn, _, (_, older, _) = second
        members = (older[0], names[0])
        return ColumnBinding(
            shape="plural", members=members,
            antecedent_turn=older_turn.index, side="turns",
            rewritten=tuple(rewrite(n) for n in members),
            considered=members)

    # -- the column ---------------------------------------------------------

    def _column(self, text: str, binding: ColumnBinding):
        """Ask every row, each alone, and report the column of answers."""
        from .parser import Query
        from .solution import Solution, Step
        cells = []
        for name, asked in zip(binding.members, binding.rewritten):
            solution = self._ask_one(asked)
            cells.append({"row": name, "asked": asked, "ok": bool(solution.ok),
                          "kind": solution.kind, "answer": solution.answer})
        lines = "; ".join(f"{c['row']}: {c['answer']}" for c in cells)
        answer = (f"a column of {len(cells)} rows, one answer per row of the "
                  f"set turn {binding.antecedent_turn} named -- {lines}")
        query = Query(raw=text, normalised=text.strip(), kind="unknown",
                      rule="discourse:column",
                      trace=(f"discourse: {binding.sentence}",))
        steps = tuple(Step(c["row"], c["asked"], c["answer"]) for c in cells)
        return Solution(query=query, kind="column", answer=answer,
                        steps=steps, ok=all(c["ok"] for c in cells),
                        payload={"members": list(binding.members),
                                 "cells": cells,
                                 "binding": binding.sentence,
                                 "antecedent_turn": binding.antecedent_turn})

    # -- why? ---------------------------------------------------------------

    def _why(self, text: str):
        """Explain the turn before this one from the record alone."""
        from .parser import Query
        from .solution import Solution, Step
        if not self._turns:
            raise FollowUpError("no-antecedent",
                                f"{text!r}: nothing has been asked to explain")
        turn = self._turns[-1]
        steps: List[Step] = []
        if turn.index in self._refusals:
            error = self._refusals[turn.index]
            subject = error.reason
            answer = (f"turn {turn.index} ({turn.text!r}) was refused "
                      f"{error.reason}: {error}")
        elif turn.index in self._columns:
            binding = self._columns[turn.index]
            subject = ", ".join(binding.members)
            answer = (f"turn {turn.index} ({turn.text!r}) was a follow-up: "
                      f"{binding.sentence}; each row was asked alone")
            steps.extend(self._solutions[turn.index].steps)
        elif turn.binding is not None:
            b = turn.binding
            subject = b.name or b.rewritten
            answer = (f"turn {turn.index} ({turn.text!r}) was a follow-up: "
                      f"{b.sentence}; of the candidates "
                      f"{', '.join(b.considered)}, "
                      f"{', '.join(b.licensed)} answered; the answer was "
                      f"{turn.answer}")
            steps.extend(self._solutions[turn.index].steps)
        else:
            subject = turn.text
            answer = (f"turn {turn.index} asked {turn.text!r} as a whole "
                      f"query; the answer was {turn.answer}")
            solution = self._solutions.get(turn.index)
            if solution is not None:
                steps.extend(solution.steps)
        query = Query(raw=text, normalised=text.strip(), kind="unknown",
                      rule="discourse:why",
                      trace=(f"discourse: why? explains turn {turn.index}",))
        return Solution(query=query, kind="why", answer=answer,
                        steps=tuple(steps), ok=True,
                        payload={"turn": turn.index, "subject": subject})
