"""The second described shape: an operator with an operand on each side.

Why a second shape at all
-------------------------
The first description language -- :mod:`glm_universal.language.question` --
says *an opening, then named slots separated by literal words*.  Three of the
runtime's query kinds are exactly that, and are now read off their
descriptions with no branch in the parser.  The round that closed them named
the honest next question rather than answering it:

    Seventeen kinds are undescribed and five of them are undescribable *by
    construction* ... the honest next step is to ask whether a **second**
    described shape -- an infix shape, say, with two operand slots and a
    described operator -- covers ``analogy`` and ``verify`` together, and to
    count the judgements it costs.  If two shapes cover seven kinds, the
    description language is worth extending; if a second shape covers one
    kind, it is a parser generator being written one kind at a time.

This module is the answer, measured.  It describes one more shape and finds
that it covers **three** kinds -- ``verify``, ``analogy`` and the relational
half of ``compare`` -- and it says what it does not cover and why.

What an infix shape is, and how it differs from a slot shape
------------------------------------------------------------
A slot shape walks *tokens*.  An infix shape cuts a *string*: its operands
are notations -- ``sqrt(2)``, ``mass * acceleration`` -- and a notation is
not a run of words.  That difference is the finding, not an inconvenience: an
infix shape is a genuinely second primitive and not the first one rearranged,
so the description language is now two shapes rather than one general one,
and the count of what each covers is the measurement of whether the second
was worth adding.

A description says:

``operator``
    the phrasing that cuts the string.  It may be symbolic (``::``, ``=``) or
    worded (``greater than``), and which surface form matched can itself be
    part of the answer -- ``greater than`` and ``less than`` are the same
    shape asking opposite questions, so an operator alternative may carry a
    *meaning*.
``operands``
    the named pieces the cut produces, in order, each with a role.
``inner``
    an operator that cuts each side again -- the analogy's ``:`` inside its
    ``::`` -- which is what lets one description hold a four-term question.
``opening``
    an optional leading word: ``verify`` before an equation, the copula
    ``is`` before a comparison.  It is optional because the equation is the
    question and the verb only says so again.
``carried``
    which operands the runtime is given, and under which name.  The analogy's
    fourth term is described -- a question without it is malformed -- and not
    carried, because it is the hole the answer fills.

Exactness
---------
No float, no scoring, no back-tracking: the operator is found by scanning for
its surface forms, the cut is made at character positions, and the operands
are the substrings between the cuts with the outer whitespace removed.  Case
is *preserved*, because an operand of an equation is a notation and the
shipped parser preserves it too.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Tuple,
                    Union)

from .question import Phrasing, Preamble, Refusal, Slot

__all__ = [
    "InfixSpec", "InfixMatch", "InfixDecline", "InfixOutcome",
    "Modifier", "TrailingOption", "VALUE_FORMS",
    "match_infix", "parse_infix", "describe_infix",
]


# ===========================================================================
# 0.  THE TWO THINGS A SHAPE MAY HOLD BESIDE ITS OPERANDS
# ===========================================================================
#
#  The round that wrote the infix shape named four parts of the six described
#  kinds that were still hand-written, and for each the piece of description
#  language it needed.  Two of them are here.
#
#  A **modifier** is a word that directs the reading rather than naming an
#  operand: `check tensor force = ...` asks the same question of the same
#  equation under a stricter comparison.  It is a third thing a shape can
#  hold, and it is not an operand precisely because removing it leaves the
#  question well formed.
#
#  A **trailing option** is a value written after the operands that narrows
#  where the answer is looked for: `... in the physics.dimension subspace top
#  5`.  Neither is a slot -- neither has a place in the shape -- so both are
#  described as things the shape *carries*, with the position they may be
#  written in stated rather than assumed.

#: The value forms a trailing option may take.  The list is short and closed
#: on purpose: a description language whose values were arbitrary patterns
#: would be a parser generator with a regular expression in it, and the
#: judgement it is meant to expose -- what counts as a written value here --
#: would be hidden inside that pattern again.
VALUE_FORMS: Tuple[str, ...] = (
    "qualified_name",   # `physics.dimension`: a declared head, a dot, a name
    "count",            # `top 5`: a declared introducer, then digits
)


@dataclass(frozen=True)
class Modifier:
    """A described word that directs the reading rather than naming a thing.

    ``values`` maps each admitted surface word to the reading it selects, and
    ``default`` is the reading of a question that carries none of them --
    stated, because a default that is not written down is a silent decision.

    Where the word may be *written* and where it may be *stripped* are two
    different questions and are answered separately, which is what the branch
    this restates does:

    * a modifier is **selected** by appearing anywhere in the question, on a
      word boundary, longest surface first;
    * it is **removed** from the operands only in the two positions where it
      is unambiguously a directive -- at the head (``tensor force = ...``)
      and in the trailing frame (``... under tensor semantics``).  A
      qualifier in the middle of an expression is left where it is, because
      deleting it there would change the equation being audited.
    """

    option: str
    values: Tuple[Tuple[str, str], ...]
    default: str
    why: str
    prepositions: Optional[Phrasing] = None
    noun: str = ""

    @property
    def surfaces(self) -> Tuple[str, ...]:
        """Every admitted word, longest first -- the order it is looked for."""
        return tuple(sorted((word for word, _ in self.values),
                            key=lambda word: (-len(word), word)))

    def select(self, lowered: str) -> Tuple[str, str]:
        """``(value, why)`` for a question, without changing it."""
        table = dict(self.values)
        for word in self.surfaces:
            if re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])",
                         lowered):
                return table[word], (f"the word {word!r} selects "
                                     f"{table[word]!r} for {self.option}")
        return self.default, (f"no {self.option} word is written; the "
                              f"description's default {self.default!r} "
                              f"stands")

    def strip(self, body: str, lowered: str) -> str:
        """Remove the modifier from the operands where it is a directive."""
        table = dict(self.values)
        word = next((surface for surface in self.surfaces
                     if re.search(
                         rf"(?<![a-z0-9_]){re.escape(surface)}(?![a-z0-9_])",
                         lowered)), "")
        if not word or word not in table:
            return body
        out = body.strip()
        if self.prepositions is not None and self.noun:
            forms = "|".join(re.escape(" ".join(alternative))
                             for alternative in
                             self.prepositions.alternatives)
            out = re.sub(rf"\b(?:{forms})\s+{re.escape(word)}\s+"
                         rf"{re.escape(self.noun)}\b\s*$",
                         "", out, flags=re.IGNORECASE)
        tail = rf"(\s+{re.escape(self.noun)})?" if self.noun else ""
        out = re.sub(rf"^\s*{re.escape(word)}{tail}(?![a-z0-9_])", "", out,
                     flags=re.IGNORECASE)
        return out.strip(" ,:")


@dataclass(frozen=True)
class TrailingOption:
    """A described value written after the operands, narrowing the answer.

    ``form`` is one of :data:`VALUE_FORMS`.  A ``qualified_name`` is one of
    the declared ``heads``, a dot and a name; a ``count`` is one of the
    declared ``introducers`` followed by digits.  Both are read off the
    question and neither is cut out of an operand: they are written where the
    shape's last operand is the hole the answer fills, so nothing carried is
    disturbed by leaving them in place -- which is exactly what the branch
    this restates does.
    """

    option: str
    form: str
    why: str
    heads: Tuple[str, ...] = ()
    introducers: Optional[Phrasing] = None

    def __post_init__(self) -> None:
        if self.form not in VALUE_FORMS:
            raise ValueError(
                f"TrailingOption {self.option!r}: unknown value form "
                f"{self.form!r}; the described forms are "
                f"{', '.join(VALUE_FORMS)}")
        if self.form == "qualified_name" and not self.heads:
            raise ValueError(
                f"TrailingOption {self.option!r}: a qualified name is "
                f"qualified by one of a declared set of heads, and none are "
                f"declared")
        if self.form == "count" and self.introducers is None:
            raise ValueError(
                f"TrailingOption {self.option!r}: a count is introduced by a "
                f"declared word, and none is declared")

    def render(self) -> str:
        if self.form == "qualified_name":
            return f"({' | '.join(self.heads)}).<name>"
        assert self.introducers is not None
        return f"{self.introducers.render()} <digits>"

    def read(self, lowered: str) -> Optional[Union[str, int]]:
        """The value this option carries in a question, or ``None``."""
        if self.form == "qualified_name":
            heads = "|".join(re.escape(head) for head in self.heads)
            hit = re.search(rf"(?<![a-z0-9_.])({heads})\.[a-z_]+", lowered)
            return hit.group(0) if hit else None
        assert self.introducers is not None
        for alternative in self.introducers.alternatives:
            name = " ".join(alternative)
            hit = re.search(
                rf"(?<![a-z0-9_]){re.escape(name)}\s*=?\s*(\d+)", lowered)
            if hit:
                return int(hit.group(1))
        return None


# ===========================================================================
# 1.  WHAT AN INFIX MATCH IS
# ===========================================================================

@dataclass(frozen=True)
class InfixMatch:
    """A question cut by a described operator."""

    kind: str
    fills: Mapping[str, str]
    operator: str
    meaning: str
    trace: Tuple[str, ...]
    options: Mapping[str, Any] = field(default_factory=dict)

    matched: bool = True

    def carried(self, spec: "InfixSpec") -> Dict[str, str]:
        """The operands the runtime is given, in the order it takes them."""
        return {name: self.fills[name] for name in spec.carried}


@dataclass(frozen=True)
class InfixDecline:
    """A question the infix description will not decide."""

    boundary: str
    reason: str
    kind: Optional[str] = None
    trace: Tuple[str, ...] = ()

    matched: bool = False


InfixOutcome = Union[InfixMatch, InfixDecline]


# ===========================================================================
# 2.  THE DESCRIPTION
# ===========================================================================

@dataclass(frozen=True)
class InfixSpec:
    """One described infix shape."""

    kind: str
    gloss: str
    operator: Phrasing
    operands: Tuple[Slot, ...]
    carried: Tuple[str, ...]
    inner: Optional[Phrasing] = None
    opening: Optional[Phrasing] = None
    closing: Optional[Phrasing] = None
    meanings: Tuple[Tuple[str, str], ...] = ()
    meaning_option: str = ""
    into: str = "options"
    not_adjacent_to: str = ""
    preamble: Optional[Preamble] = None
    refusals: Tuple[Refusal, ...] = ()
    modifiers: Tuple[Modifier, ...] = ()
    trailing: Tuple[TrailingOption, ...] = ()

    def __post_init__(self) -> None:
        if self.into not in ("options", "operands"):
            raise ValueError(
                f"InfixSpec {self.kind!r}: an operand is carried either as "
                f"an option or as an operand, not as {self.into!r}")
        names = [operand.name for operand in self.operands]
        if len(set(names)) != len(names):
            raise ValueError(
                f"InfixSpec {self.kind!r}: duplicate operand name in {names}")
        if len(self.operands) != (4 if self.inner is not None else 2):
            raise ValueError(
                f"InfixSpec {self.kind!r}: an operator with no inner "
                f"operator cuts two operands, and one with an inner operator "
                f"cuts four; {len(self.operands)} are described")
        for name in self.carried:
            if name not in names:
                raise ValueError(
                    f"InfixSpec {self.kind!r}: {name!r} is carried and not "
                    f"described")
        if self.meanings and not self.meaning_option:
            raise ValueError(
                f"InfixSpec {self.kind!r}: the operator's meanings are "
                f"declared and no option is named to carry them")

    # -- what the description says -------------------------------------------

    @property
    def phrasings(self) -> Tuple[Phrasing, ...]:
        out = [self.operator]
        if self.inner is not None:
            out.append(self.inner)
        if self.opening is not None:
            out.append(self.opening)
        if self.closing is not None:
            out.append(self.closing)
        return tuple(out)

    @property
    def judgements(self) -> int:
        """How many decisions about English this description states.

        A modifier and a trailing option each carry their own justification
        -- which words direct a reading, and what counts as a written value
        -- so each of them is counted here exactly as a phrasing is.
        """
        return (len(self.phrasings) + len(self.modifiers)
                + len(self.trailing)
                + (self.preamble.judgements
                   if self.preamble is not None else 0))

    @property
    def carried_options(self) -> Tuple[str, ...]:
        """The option names a match may carry beside its operands."""
        out = [modifier.option for modifier in self.modifiers]
        out += [option.option for option in self.trailing]
        if self.meaning_option:
            out.append(self.meaning_option)
        return tuple(out)

    def phrasing_count(self) -> int:
        """How many distinct surface forms this one description recognises."""
        total = 1
        for piece in self.phrasings:
            total *= len(piece.alternatives)
        return total

    def roles(self) -> Tuple[str, ...]:
        return tuple(operand.role for operand in self.operands)

    def render(self) -> str:
        left, right = self.operands[:2], self.operands[2:]
        if self.inner is None:
            body = (f"{left[0].render()} {self.operator.render()} "
                    f"{left[1].render()}")
        else:
            inner = self.inner.render()
            body = (f"{left[0].render()} {inner} {left[1].render()} "
                    f"{self.operator.render()} "
                    f"{right[0].render()} {inner} {right[1].render()}")
        if self.opening is not None:
            body = f"{self.opening.render()}? {body}"
        if self.closing is not None:
            body = f"{body} {self.closing.render()}?"
        return body

    def refusal(self, name: str) -> Refusal:
        for refusal in self.refusals:
            if refusal.name == name:
                return refusal
        raise KeyError(f"InfixSpec {self.kind!r}: no described refusal "
                       f"{name!r}")

    def meaning_of(self, surface: str) -> str:
        for written, meaning in self.meanings:
            if written == surface:
                return meaning
        return ""

    def render_question(self, fills: Mapping[str, str],
                        operator: int = 0, inner: int = 0,
                        opening: Optional[int] = None) -> str:
        """Write a question of this shape -- the inverse of matching."""
        operator_surface = " ".join(
            self.operator.alternatives[operator % len(
                self.operator.alternatives)])
        pieces: List[str] = []
        if opening is not None and self.opening is not None:
            pieces.append(" ".join(self.opening.alternatives[
                opening % len(self.opening.alternatives)]))
        if self.inner is None:
            pieces.append(fills[self.operands[0].name])
            pieces.append(operator_surface)
            pieces.append(fills[self.operands[1].name])
        else:
            inner_surface = " ".join(
                self.inner.alternatives[inner % len(self.inner.alternatives)])
            pieces.append(fills[self.operands[0].name])
            pieces.append(inner_surface)
            pieces.append(fills[self.operands[1].name])
            pieces.append(operator_surface)
            pieces.append(fills[self.operands[2].name])
            pieces.append(inner_surface)
            pieces.append(fills[self.operands[3].name])
        return " ".join(piece for piece in pieces if piece)


# ===========================================================================
# 3.  THE GENERIC MATCHER
# ===========================================================================

def _occurrences(text: str, form: str, forbid: str = ""
                 ) -> List[Tuple[int, int]]:
    """Every place ``form`` appears, as ``(start, end)`` character offsets.

    A worded operator matches on word boundaries, so ``on`` inside
    ``iron`` is not an operator.  A symbolic one matches literally, and a
    ``:`` that is part of a ``::`` is not a ``:`` -- the longer operator is
    the one written, which is why the alternatives are tried longest first
    everywhere in this package.
    """
    out: List[Tuple[int, int]] = []
    if form.strip("abcdefghijklmnopqrstuvwxyz "):
        start = 0
        while True:
            found = text.find(form, start)
            if found < 0:
                break
            end = found + len(form)
            before = text[found - 1] if found else ""
            after = text[end] if end < len(text) else ""
            if forbid and ((before and before in forbid)
                           or (after and after in forbid)):
                # `>=` and `==` hold a `=` that is not *the* operator: the
                # description says which characters may not touch it, which
                # is the same rule the shipped parser's top-level scan makes.
                start = end
                continue
            out.append((found, end))
            start = end
        return out
    for hit in re.finditer(rf"(?<![a-z0-9_]){re.escape(form)}(?![a-z0-9_])",
                           text, flags=re.IGNORECASE):
        out.append((hit.start(), hit.end()))
    return out


def _find_operator(operator: Phrasing, text: str, forbid: str = ""
                   ) -> Tuple[str, List[Tuple[int, int]]]:
    """The operator alternative present, and every place it appears.

    The alternatives are stored longest first, so ``::`` is looked for
    before ``:`` and the first alternative that appears at all is the
    operator.  Nothing is scored and nothing back-tracks.
    """
    for words in operator.alternatives:
        form = " ".join(words)
        hits = _occurrences(text, form, forbid)
        if hits:
            return form, hits
    return "", []


def _strip_opening(spec: InfixSpec, text: str) -> Tuple[str, str]:
    """Remove a described opening from the head, and say which it was."""
    if spec.opening is None:
        return text, ""
    lowered = text.lower().lstrip()
    offset = len(text) - len(text.lstrip())
    for words in spec.opening.alternatives:
        form = " ".join(words)
        if lowered.startswith(form) and (
                len(lowered) == len(form)
                or not lowered[len(form)].isalnum()):
            # Only the *leading* punctuation goes: a trailing `:` is an
            # operator this shape may still be about to read.
            return text[offset + len(form):].lstrip(" ,:"), form
    return text, ""


def _strip_closing(spec: InfixSpec, text: str) -> Tuple[str, str]:
    """Remove a described closing from the tail, and say which it was.

    A closing is an opening written after the question instead of before
    it: ``force = mass * acceleration holds`` asks what ``verify force =
    mass * acceleration`` asks.  It has to be described, because a verb
    left in place is a verb inside the last operand, and an operand with a
    verb in it names nothing.
    """
    if spec.closing is None:
        return text, ""
    stripped = text.rstrip(" ,:?")
    lowered = stripped.lower()
    for words in spec.closing.alternatives:
        form = " ".join(words)
        if lowered.endswith(form) and (
                len(lowered) == len(form)
                or not lowered[len(lowered) - len(form) - 1].isalnum()):
            return stripped[:len(stripped) - len(form)].rstrip(" ,:"), form
    return text, ""


def match_infix(spec: InfixSpec, question: str) -> InfixOutcome:
    """Match one question against one described infix shape."""
    from .build import ARTICLES  # the same set the slot matcher uses

    text = question.strip().rstrip("?").strip()
    whole = text.lower()
    trace: List[str] = [f"question {text!r}"]
    if spec.preamble is not None:
        while True:
            before = text
            for form in spec.preamble.forms():
                if text.lower().startswith(form) and (
                        len(text) == len(form)
                        or not text[len(form)].isalnum()):
                    text = text[len(form):].lstrip(" ,:")
                    trace.append(f"preamble {form!r} skipped")
                    break
            if text == before:
                break
    text, opened = _strip_opening(spec, text)
    if opened:
        trace.append(f"opening {opened!r} removed; the operator is the "
                     f"question and the verb only says so again")
    text, closed = _strip_closing(spec, text)
    if closed:
        trace.append(f"closing {closed!r} removed; it is the opening "
                     f"written after the question rather than before it")

    options: Dict[str, Any] = {}
    for modifier in spec.modifiers:
        value, why = modifier.select(whole)
        options[modifier.option] = value
        trace.append(why)
        shortened = modifier.strip(text, whole)
        if shortened != text.strip(" ,:"):
            trace.append(f"the {modifier.option} word directs the reading "
                         f"rather than naming an operand, and is written "
                         f"in a position the description admits, so it is "
                         f"removed from the operands")
            text = shortened
    for option in spec.trailing:
        read = option.read(whole)
        if read is not None:
            options[option.option] = read
            trace.append(f"trailing option {option.option} = {read!r}, "
                         f"written as {option.render()}")

    form, hits = _find_operator(spec.operator, text, spec.not_adjacent_to)
    if not hits:
        return InfixDecline(
            boundary="no_operator",
            reason=(f"{question!r} holds none of the operators "
                    f"{spec.operator.render()}, so it is not a {spec.kind} "
                    f"question"),
            kind=None, trace=tuple(trace))
    if len(hits) != 1:
        return InfixDecline(
            boundary="operator_repeated",
            reason=_reason(spec, "operator_repeated", question,
                           {"operator": form, "count": str(len(hits))}),
            kind=spec.kind, trace=tuple(trace))
    trace.append(f"operator {form!r} at {hits[0][0]}")

    start, end = hits[0]
    sides = [text[:start], text[end:]]
    if spec.inner is None:
        pieces = sides
    else:
        pieces = []
        for side in sides:
            inner_form, inner_hits = _find_operator(spec.inner, side)
            if len(inner_hits) != 1:
                return InfixDecline(
                    boundary="malformed_side",
                    reason=_reason(spec, "malformed_side", question,
                                   {"side": side.strip(),
                                    "inner": spec.inner.render()}),
                    kind=spec.kind, trace=tuple(trace))
            cut = inner_hits[0]
            pieces.append(side[:cut[0]])
            pieces.append(side[cut[1]:])
        trace.append(f"each side cut again at {spec.inner.render()}")

    fills: Dict[str, str] = {}
    for operand, piece in zip(spec.operands, pieces):
        value = piece.strip(" ,:?")
        if not operand.keep_articles:
            words = value.split()
            while words and words[0].lower() in ARTICLES:
                words.pop(0)
            value = " ".join(words)
        if not value and not operand.optional:
            return InfixDecline(
                boundary=f"empty_{operand.name}",
                reason=_reason(spec, f"empty_{operand.name}", question,
                               dict(fills)),
                kind=spec.kind, trace=tuple(trace))
        fills[operand.name] = value
        trace.append(f"operand {operand.name!r} ({operand.role}) = "
                     f"{value!r}")

    meaning = spec.meaning_of(form)
    if spec.meanings and not meaning:  # pragma: no cover - a broken table
        meaning = spec.meaning_of(form.lower())
    if spec.meaning_option:
        options[spec.meaning_option] = meaning
    return InfixMatch(kind=spec.kind, fills=fills, operator=form,
                      meaning=meaning, trace=tuple(trace),
                      options=options)


def _reason(spec: InfixSpec, boundary: str, question: str,
            fields: Mapping[str, str]) -> str:
    try:
        described = spec.refusal(boundary)
    except KeyError:
        return (f"{question!r} does not fit the shape {spec.render()!r} "
                f"({boundary})")
    values: Dict[str, object] = {"question": question}
    values.update(fields)
    try:
        return described.reason.format(**values)
    except (KeyError, IndexError):  # pragma: no cover - a malformed sentence
        return described.reason


def parse_infix(question: str, specs: Sequence[InfixSpec]) -> InfixOutcome:
    """Match a question against every described infix shape.

    The operators are looked for in the order the shapes are declared, and a
    shape is *entered* as soon as its operator is present.  Unlike the slot
    shapes, whose openings are disjoint by test, two infix operators can both
    be present -- ``verify a = b`` holds no ``::``, but a question could hold
    both -- so a question that enters two shapes is declined at
    ``ambiguous_operator`` rather than decided by declaration order.
    """
    entered: List[Tuple[InfixSpec, InfixOutcome]] = []
    for spec in specs:
        outcome = match_infix(spec, question)
        if outcome.matched or outcome.boundary != "no_operator":
            entered.append((spec, outcome))
    if len(entered) == 1:
        return entered[0][1]
    if not entered:
        operators = "; ".join(spec.operator.render() for spec in specs)
        return InfixDecline(
            boundary="no_operator",
            reason=(f"{question!r} holds none of the described operators "
                    f"({operators})"),
            kind=None, trace=())
    kinds = ", ".join(spec.kind for spec, _ in entered)
    return InfixDecline(
        boundary="ambiguous_operator",
        reason=(f"{question!r} holds the operators of more than one "
                f"described shape ({kinds}); the descriptions do not decide "
                f"between them"),
        kind=None, trace=())


def describe_infix(specs: Sequence[InfixSpec]) -> Dict[str, Any]:
    """What the infix descriptions say, before any question is matched."""
    return {
        "kinds": tuple(spec.kind for spec in specs),
        "shapes": {spec.kind: spec.render() for spec in specs},
        "operands": {spec.kind: tuple(o.name for o in spec.operands)
                     for spec in specs},
        "carried": {spec.kind: spec.carried for spec in specs},
        "roles": {spec.kind: spec.roles() for spec in specs},
        "judgements": {spec.kind: spec.judgements for spec in specs},
        "phrasings": {spec.kind: spec.phrasing_count() for spec in specs},
        "meanings": {spec.kind: dict(spec.meanings) for spec in specs},
        "refusals": {spec.kind: tuple(r.name for r in spec.refusals)
                     for spec in specs},
    }
