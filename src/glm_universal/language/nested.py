"""The third described shape: an operator whose operands are *shapes*.

Why a third shape
-----------------
:mod:`glm_universal.language.question` describes a question as an opening and
named slots; :mod:`glm_universal.language.infix` describes one as an operator
cutting a string in two.  Between them they cover six of the runtime's
answerable kinds, and the round that measured them named the one kind neither
family reaches and the piece of description language it needs:

    ``comparative``: an operator between two *measured uses*.  ``is cold in
    stellar_surface hotter than hot in tea`` is infix, and its operands are
    not text but readings -- each side must itself match the measure shape.
    A nested shape is a real extension and is not attempted here.

This module is that extension.  A :class:`NestedSpec` is an operator with an
operand on each side, exactly as an infix shape is, except that an operand is
not a run of characters handed on to a grammar: it is **another described
shape**, and a side that does not match it is not an operand at all.

What the description has to say that no earlier one did
-------------------------------------------------------
``operator``
    a :class:`DegreeOperator`, which is the second new thing here.  The
    operators described so far are sets of surface forms -- ``::``, ``=``,
    ``greater than``.  A comparative's operator is built out of a *word*:
    any degree word with an ``-er`` suffix, then ``than``, or the frame
    ``as <word> as``.  The set is therefore open, and the description says
    how the operator is formed rather than listing it.  Which word was
    written is part of the answer, because the direction the marker asserts
    is read off the measure register from it.
``side``
    the shape each operand must match, given as *the shape itself* and the
    restrictions the nesting places on it, rather than as a second copy of
    it.  Nesting the measure shape means dropping its opening -- inside a
    comparative a use is recognised by its position, not by the word
    ``measure`` -- requiring the slots that a bare use may leave out, and
    tightening what may fill them: each side names a degree word and a
    comparison class, and ``sqrt(2)`` is neither.  That last restriction is
    what keeps ``is sqrt(2) greater than 7/5`` -- an exact-real comparison
    -- out of this shape, and it is stated in the description rather than
    kept in a regular expression.

Exactness
---------
No scoring, no back-tracking and no float: the operator is found by scanning
the tokens left to right for the earliest position at which it is formed, the
sides are the token runs either side of it, and each side is filled by
:func:`glm_universal.language.build.walk` -- the same walk the slot shapes
use, not a second copy of it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Tuple,
                    Union)

from .question import (Phrasing, Preamble, QuestionSpec, Refusal, Slot,
                       tokenise, tokenise_cased)

__all__ = [
    "DegreeOperator", "NestedSide", "NestedSpec",
    "NestedMatch", "NestedDecline", "NestedOutcome",
    "match_nested",
]


# ===========================================================================
# 1.  AN OPERATOR MADE OUT OF A WORD
# ===========================================================================

@dataclass(frozen=True)
class DegreeOperator:
    """An operator formed from a degree word rather than listed.

    Two forms, and they are one operator because they occupy the same place
    in the same shape and are answered by the same reading of the register:

    * ``<word><suffix> than`` -- ``hotter than``, ``colder than``;
    * ``as <word> as`` -- ``as hot as``.

    The second is the *equative*: it asserts that the two readings are the
    same where the first asserts an order, so which form was written is
    carried beside the word.  Neither form is enumerated: a degree word is
    any name, and the register decides whether it means anything, which is
    the same division of labour the measure shape already makes.
    """

    suffix: str
    tail: Phrasing
    frame: Phrasing
    why: str
    form_option: str = "form"
    equative_option: str = "equative"

    def render(self) -> str:
        return (f"(<word>{self.suffix} {self.tail.render()} | "
                f"{self.frame.render()} <word> {self.frame.render()})")

    def _is_degree_word(self, token: str) -> bool:
        if not token.endswith(self.suffix) or len(token) <= len(self.suffix):
            return False
        head, rest = token[0], token[1:]
        return head.isalpha() and all(ch.isalpha() or ch == "_"
                                      for ch in rest)

    def find(self, tokens: Sequence[str]
             ) -> Optional[Tuple[int, int, str, bool]]:
        """The earliest operator in ``tokens``.

        Returns ``(begin, end, word, equative)`` -- where the operator
        starts, where the right operand starts, the degree word it is built
        from, and whether the equative frame was the form written.  The
        earliest position wins, which is what makes the left operand the
        shortest run that can be one; the shipped rule is a non-greedy left
        side and this is the same rule stated on tokens.
        """
        for position in range(len(tokens)):
            token = tokens[position]
            if (self._is_degree_word(token)
                    and self.tail.match_at(tokens, position + 1) is not None):
                after = self.tail.match_at(tokens, position + 1)
                assert after is not None
                return position, after[0], token, False
            opened = self.frame.match_at(tokens, position)
            if opened is not None:
                middle = opened[0]
                if middle >= len(tokens):
                    continue
                closed = self.frame.match_at(tokens, middle + 1)
                if closed is not None:
                    return position, closed[0], tokens[middle], True
        return None


# ===========================================================================
# 2.  AN OPERAND THAT IS ITSELF A SHAPE
# ===========================================================================

@dataclass(frozen=True)
class NestedSide:
    """One side of a nested shape: a described shape, tightened.

    ``shape`` is the description this side must match, and the three fields
    beside it are what nesting changes about it.  They are restrictions and
    never additions: a nested side can only be *harder* to match than the
    shape it nests, which is what keeps the nesting from becoming a second
    surface with a life of its own.
    """

    shape: QuestionSpec
    without_opening: bool
    required: Tuple[str, ...]
    forms: Tuple[Tuple[str, str], ...]
    why: str

    @property
    def pieces(self) -> Tuple[Any, ...]:
        """The pieces a side is walked over, with the tightening applied."""
        forms = dict(self.forms)
        required = set(self.required)
        out: List[Any] = []
        for index, piece in enumerate(self.shape.shape):
            if index == 0 and self.without_opening:
                continue
            if isinstance(piece, Slot):
                out.append(Slot(
                    name=piece.name, role=piece.role,
                    optional=(piece.optional
                              and piece.name not in required),
                    keep_articles=piece.keep_articles,
                    preserve_case=piece.preserve_case,
                    form=forms.get(piece.name, piece.form)))
            else:
                out.append(piece)
        return tuple(out)

    def render(self) -> str:
        return " ".join(piece.render() for piece in self.pieces)


# ===========================================================================
# 3.  WHAT A NESTED MATCH IS
# ===========================================================================

@dataclass(frozen=True)
class NestedMatch:
    """A question cut at a described operator into two matched sides."""

    kind: str
    options: Mapping[str, Any]
    word: str
    equative: bool
    trace: Tuple[str, ...]

    matched: bool = True


@dataclass(frozen=True)
class NestedDecline:
    """A question the nested description will not decide."""

    boundary: str
    reason: str
    kind: Optional[str] = None
    trace: Tuple[str, ...] = ()

    matched: bool = False


NestedOutcome = Union[NestedMatch, NestedDecline]


# ===========================================================================
# 4.  THE DESCRIPTION, AND THE MATCHER
# ===========================================================================

@dataclass(frozen=True)
class NestedSpec:
    """One described nested shape."""

    kind: str
    gloss: str
    operator: DegreeOperator
    side: NestedSide
    names: Tuple[Tuple[str, str], ...]
    opening: Optional[Phrasing] = None
    preamble: Optional[Preamble] = None
    refusals: Tuple[Refusal, ...] = ()

    def __post_init__(self) -> None:
        named = {slot_.name for slot_ in self.side.shape.slots}
        for slot_name, _option in self.names:
            if slot_name not in named:
                raise ValueError(
                    f"NestedSpec {self.kind!r}: {slot_name!r} is carried and "
                    f"is not a slot of the nested shape "
                    f"{self.side.shape.kind!r}")

    @property
    def judgements(self) -> int:
        """How many decisions about English this description states.

        The operator is one -- that an ``-er than`` and an ``as ... as`` are
        one shape asking two questions -- the nesting is a second, and the
        preamble and the optional opening are counted as they are elsewhere.
        The nested shape's own judgements are *not* counted again here: they
        were counted once where that shape is described, and counting them
        twice would make reuse look expensive.
        """
        return (2 + (1 if self.opening is not None else 0)
                + (self.preamble.judgements
                   if self.preamble is not None else 0))

    @property
    def options(self) -> Tuple[str, ...]:
        """Every option a match of this shape carries, in order."""
        out = [self.operator.form_option, self.operator.equative_option]
        for side in ("left", "right"):
            for _slot, option in self.names:
                out.append(f"{side}_{option}")
        return tuple(out)

    def render(self) -> str:
        side = self.side.render()
        opening = f"{self.opening.render()}? " if self.opening else ""
        return f"{opening}{side} {self.operator.render()} {side}"

    def refusal(self, name: str) -> Refusal:
        for refusal in self.refusals:
            if refusal.name == name:
                return refusal
        raise KeyError(f"NestedSpec {self.kind!r}: no described refusal "
                       f"{name!r}")

    @property
    def separators(self) -> int:
        """How many ways one side of this shape may be written.

        The nested shape has no separators of its own: these are the nested
        shape's, and crossing them is how a corpus stops measuring one
        spelling of a side.
        """
        counts = [len(piece.alternatives) for piece in self.side.pieces
                  if isinstance(piece, Phrasing)]
        return max(counts) if counts else 1

    def render_question(self, fills: Mapping[str, str], word: str,
                        equative: bool = False,
                        opening: Optional[int] = None,
                        separator: int = 0) -> str:
        """Write a question of this shape -- the inverse of matching."""
        pieces: List[str] = []
        if opening is not None and self.opening is not None:
            pieces.append(" ".join(self.opening.alternatives[
                opening % len(self.opening.alternatives)]))
        def side(prefix: str) -> str:
            written: List[str] = []
            for piece in self.side.pieces:
                if isinstance(piece, Slot):
                    option = dict(self.names).get(piece.name, piece.name)
                    written.append(fills[f"{prefix}_{option}"])
                else:
                    written.append(" ".join(piece.alternatives[
                        separator % len(piece.alternatives)]))
            return " ".join(part for part in written if part)
        pieces.append(side("left"))
        if equative:
            frame = " ".join(self.operator.frame.alternatives[0])
            pieces.append(f"{frame} {word} {frame}")
        else:
            tail = " ".join(self.operator.tail.alternatives[0])
            pieces.append(f"{word} {tail}")
        pieces.append(side("right"))
        return " ".join(piece for piece in pieces if piece)


def _reason(spec: NestedSpec, boundary: str, question: str,
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


def _match_side(spec: NestedSpec, prefix: str, tokens: Sequence[str],
                cased: Sequence[str], question: str,
                trace: List[str]) -> Union[Dict[str, str], NestedDecline]:
    """Fill one side against the nested shape, or decline naming the side."""
    from .build import walk

    fills: Dict[str, str] = {slot_.name: ""
                             for slot_ in spec.side.shape.slots}
    surfaces: List[str] = []
    inner: List[str] = []
    declined = walk(spec.side.pieces, tokens, cased, 0, spec.side.shape,
                    question, fills, surfaces, inner)
    trace.extend(f"{prefix}: {line}" for line in inner)
    if declined is not None:
        return NestedDecline(
            boundary=f"{prefix}_not_a_use",
            reason=_reason(spec, f"{prefix}_not_a_use", question,
                           {"side": " ".join(tokens),
                            "shape": spec.side.render()}),
            kind=spec.kind, trace=tuple(trace))
    return fills


def match_nested(spec: NestedSpec, question: str) -> NestedOutcome:
    """Match one question against one described nested shape."""
    tokens = list(tokenise(question))
    cased = list(tokenise_cased(question))
    trace: List[str] = [f"tokens {tuple(tokens)!r}"]

    if spec.preamble is not None:
        head, skipped = spec.preamble.skip(tokens)
        if skipped:
            trace.append(f"preamble {list(skipped)!r} skipped")
        tokens, cased = tokens[head:], cased[head:]
    if spec.opening is not None:
        opened = spec.opening.match_at(tokens, 0)
        if opened is not None:
            trace.append(f"opening {opened[1]!r} removed; the operator is "
                         f"the question and the copula only says so again")
            tokens, cased = tokens[opened[0]:], cased[opened[0]:]

    found = spec.operator.find(tokens)
    if found is None:
        return NestedDecline(
            boundary="no_operator",
            reason=(f"{question!r} holds no operator of the form "
                    f"{spec.operator.render()}, so it is not a {spec.kind} "
                    f"question"),
            kind=None, trace=tuple(trace))
    begin, after, word, equative = found
    trace.append(f"operator {word!r} at token {begin}, "
                 f"{'equative' if equative else 'comparative'}")

    sides = {"left": (tokens[:begin], cased[:begin]),
             "right": (tokens[after:], cased[after:])}
    options: Dict[str, Any] = {
        spec.operator.form_option: word,
        spec.operator.equative_option: equative,
    }
    for prefix in ("left", "right"):
        side_tokens, side_cased = sides[prefix]
        filled = _match_side(spec, prefix, side_tokens, side_cased,
                             question, trace)
        if isinstance(filled, NestedDecline):
            return filled
        for slot_name, option in spec.names:
            options[f"{prefix}_{option}"] = filled[slot_name]
    return NestedMatch(kind=spec.kind, options=options, word=word,
                       equative=equative, trace=tuple(trace))
