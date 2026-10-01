"""A question description, and the pieces a question shape is written in.

Why a question description
--------------------------
:mod:`glm_universal.recipe` made a *domain* declarative: a description yields
the carriers, the readings, the widening audit, the query surface and the
refusal boundary with no code of its own.  What it did not make declarative is
the **way a question is asked**.  ``derive <coordinate> of <object>`` is
generic in the coordinate and in the object, but it is still one hand-written
phrase in :mod:`glm_universal.runtime.parser`, and so is every other query
kind: a new domain arrives without its questions.

This module makes the question's *shape* an object.  A :class:`QuestionSpec`
says what a question of that shape asks for, which of its parts name an
object, a coordinate, a class or a task, which words separate those parts, and
what it must refuse.  :mod:`glm_universal.language.build` matches a question
against the described shapes and fills the slots, knowing nothing about any
particular kind; ``RequestProject/GLM/Question.lean`` proves the part of that
matching which is not a measurement.

Shapes and phrasings
--------------------
A shape is a sequence of :class:`Piece`\\ s, alternating literal words and
named holes:

``Phrasing``
    A set of alternative surface words that mean the same thing here -- the
    openings ``derive`` / ``derivation of`` / ``what derives``, or the
    separators ``of`` / ``for`` / ``on``.  **Which phrasings count as the same
    question is a decision about English**, not something a description can
    derive, so every :class:`Phrasing` carries the justification for the set
    it declares and the audit counts them.  This is the same discipline
    :func:`glm_universal.recipe.spec.judgement` applies to a domain: what does
    not generalise is *counted*, not hidden.
``Preamble``
    A described *leading remainder*: the courtesy words and the generic
    interrogative opener a question may carry before its opening.  Anything
    else in front of an opening is declined rather than skipped.
``Slot``
    A named hole, filled by the run of tokens between the literals around it.
    A slot carries a ``role`` -- what the filled text names -- so the same
    matcher serves a coordinate, an object, a measure word, a comparison class
    or a task name.

Nothing in a shape is a regular expression and nothing is scored: matching is
a left-to-right walk over the tokens, the first described shape whose opening
is present -- after its described preamble, if it has one -- wins, and a shape
whose slots cannot all be filled **refuses** and says which slot was empty.

Exactness and determinism
-------------------------
No randomness, no statistics, no float: the only arithmetic here is integer
token counting.  The same string always matches the same shape and fills the
same slots.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

__all__ = [
    "Phrasing", "Slot", "ListSlot", "Piece", "QuestionSpec", "Refusal",
    "ROLES", "FORMS", "Preamble", "PreamblePiece",
    "tokenise", "tokenise_cased", "phrasing", "slot", "list_slot",
    "preamble_piece", "is_word",
]


#: What a filled slot names.  A role is what lets one matcher serve every
#: described kind: the *object* of a derivation and the *class* of a measure
#: word are filled the same way and told apart by their role.
ROLES: Tuple[str, ...] = (
    "coordinate",   # a description's name for a coordinate
    "object",       # an object some register holds
    "domain",       # one of the described domains
    "subject",      # a measure word, or a magnitude to be read as one
    "class",        # a comparison class to read a measure word against
    "task",         # the name of a worked end-to-end task
    "term",         # one term of an analogy, resolved in a register
    "notation",     # an expression, read by a grammar rather than looked up
)


#: What a slot's filling may look like, token by token.  ``free`` is any run
#: of tokens -- an object's name may be several words and an expression may
#: be anything a grammar reads.  ``word`` is one alphabetic name and nothing
#: else, which is what a *nested* shape needs: the sides of a comparative are
#: a degree word and a comparison class, and ``sqrt(2)`` is neither.
FORMS: Tuple[str, ...] = ("free", "word")


def is_word(text: str) -> bool:
    """Is ``text`` one alphabetic name -- a letter, then letters or ``_``?"""
    if not text or " " in text:
        return False
    head, rest = text[0], text[1:]
    return head.isalpha() and all(ch.isalpha() or ch == "_" for ch in rest)


def tokenise(text: str, marks: bool = False) -> Tuple[str, ...]:
    """Split a question into lower-case word tokens.

    Punctuation that never carries meaning in a question -- the trailing
    question mark, commas, colons -- is dropped; everything else is kept
    verbatim, because a coordinate name such as ``span_ratio`` and an
    expression such as ``sqrt(2)`` are tokens a description may need whole.

    ``marks`` keeps the comma as a token of its own.  It is off by default
    and on for exactly one thing: a shape holding a :class:`ListSlot`, where
    the comma is not decoration but the mark that separates one item of the
    list from the next.  Making it an argument rather than a rule is what
    keeps every other shape reading its questions exactly as before.
    """
    cleaned = text.replace(":", " ").replace("?", " ")
    cleaned = cleaned.replace(",", " , " if marks else " ")
    return tuple(token for token in cleaned.lower().split() if token)


def tokenise_cased(text: str, marks: bool = False) -> Tuple[str, ...]:
    """:func:`tokenise`, with the case of each token left alone.

    The two are the same split, so the two token lists have the same length
    and the same boundaries; a matcher walks the folded one and fills a slot
    that asks to keep its case from this one.  A slot filled with a notation
    needs it -- ``compare Pb and Fe`` names two elements, and ``pb`` names
    nothing.
    """
    cleaned = text.replace(":", " ").replace("?", " ")
    cleaned = cleaned.replace(",", " , " if marks else " ")
    return tuple(token for token in cleaned.split() if token)


@dataclass(frozen=True)
class Phrasing:
    """A set of surface words that count as the same thing here.

    ``why`` is the justification for the set: which phrasings mean the same
    question is a decision about English, and this is where it is written
    down.  ``alternatives`` are stored longest-first, so ``derivation of``
    cannot be shadowed by ``derive``.
    """

    alternatives: Tuple[Tuple[str, ...], ...]
    why: str

    @property
    def is_judgement(self) -> bool:
        """Every phrasing is a judgement; nothing derives one."""
        return True

    def render(self) -> str:
        written = [" ".join(words) for words in self.alternatives]
        if len(written) == 1:
            return written[0]
        return "(" + " | ".join(written) + ")"

    def match_at(self, tokens: Sequence[str], start: int
                 ) -> Optional[Tuple[int, str]]:
        """Match one alternative at ``start``; return the end index and it."""
        for words in self.alternatives:
            end = start + len(words)
            if tuple(tokens[start:end]) == words:
                return end, " ".join(words)
        return None

    def first_match(self, tokens: Sequence[str], start: int
                    ) -> Optional[Tuple[int, int, str]]:
        """Find the earliest alternative at or after ``start``.

        Returns ``(begin, end, surface)`` -- the index the separator starts
        at, the index the text after it starts at, and the words matched.
        """
        for position in range(start, len(tokens)):
            hit = self.match_at(tokens, position)
            if hit is not None:
                return position, hit[0], hit[1]
        return None


def phrasing(*surfaces: str, why: str) -> Phrasing:
    """A :class:`Phrasing` from written surface forms, longest first."""
    if not surfaces:
        raise ValueError("phrasing: at least one surface form is needed")
    if not why:
        raise ValueError("phrasing: a phrasing set must say why it is one set")
    forms = tuple(tuple(surface.lower().split()) for surface in surfaces)
    if len(set(forms)) != len(forms):
        raise ValueError(f"phrasing: duplicate surface form in {surfaces!r}")
    ordered = tuple(sorted(forms, key=lambda words: (-len(words), words)))
    return Phrasing(alternatives=ordered, why=why)


@dataclass(frozen=True)
class Slot:
    """A named hole in a shape, and what its filling names.

    ``optional`` marks a slot a question may leave out -- the class in
    ``measure hot``, the domain in ``derive span_ratio of tea``.  An optional
    slot that is absent is filled with the empty string rather than guessed
    at, and a *required* slot that cannot be filled is a refusal with the
    slot's name in the reason.

    ``keep_articles`` says whether a leading ``the`` / ``a`` / ``an`` belongs
    to the filling or is dropped from it.  It is a per-slot fact and not a
    global rule because the hand-written parser has one: it strips articles
    from the *body* it is about to split, so the head of a question loses
    them and what follows a separator keeps them -- ``derive span_ratio of
    the tea`` asks about an object written ``the tea``.  Recording that here
    is what lets the description reproduce the shipped behaviour exactly
    rather than approximately.
    """

    name: str
    role: str
    optional: bool = False
    keep_articles: bool = False
    preserve_case: bool = False
    form: str = "free"

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"Slot: unknown role {self.role!r}")
        if self.form not in FORMS:
            raise ValueError(f"Slot: unknown form {self.form!r}")

    def admits(self, filled: str) -> bool:
        """Is this filling of the shape the slot says it must have?"""
        if self.form == "word":
            return is_word(filled)
        return True

    def render(self) -> str:
        return f"<{self.name}>" + ("?" if self.optional else "")


def slot(name: str, role: str, optional: bool = False,
         keep_articles: bool = False, preserve_case: bool = False,
         form: str = "free") -> Slot:
    """A named hole of the given role."""
    return Slot(name=name, role=role, optional=optional,
                keep_articles=keep_articles, preserve_case=preserve_case,
                form=form)


@dataclass(frozen=True)
class ListSlot(Slot):
    """A slot whose filling is a *sequence*, cut at described separators.

    The three shapes described first each have holes filled by one run of
    words.  ``compare sqrt(2) and 1.5`` does not: one hole holds two values,
    and which words separate them is a decision about English exactly as a
    shape's separators are.  So a list slot carries its own
    :class:`Phrasing` of separators, the names its items fill -- the first
    item is the ``left`` of a comparison and the second the ``right`` -- and
    the smallest number of items that makes the question well formed.

    ``mark`` is the one piece of punctuation admitted beside the words: a
    comma.  It is declared rather than assumed, because admitting it means
    tokenising the question differently, and a shape with no list slot is
    still read exactly as it was.
    """

    separators: Optional[Phrasing] = None
    names: Tuple[str, ...] = ()
    minimum: int = 2
    mark: str = ","
    fallback: Optional[Phrasing] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.separators is None:
            raise ValueError(
                f"ListSlot {self.name!r}: a list is cut at described "
                f"separators and none are given")
        if len(self.names) < self.minimum:
            raise ValueError(
                f"ListSlot {self.name!r}: {self.minimum} items are required "
                f"and only {len(self.names)} are named")

    def render(self) -> str:
        joint = self.separators.render() if self.separators else ""
        return "<" + f" {joint} ".join(self.names) + ">"

    def _cut_with(self, tokens: Sequence[str],
                  phrasings: Sequence[Phrasing]) -> Tuple[str, ...]:
        items: List[str] = []
        current: List[str] = []
        position = 0
        while position < len(tokens):
            if tokens[position] == self.mark:
                items.append(" ".join(current))
                current = []
                position += 1
                continue
            hit = None
            for piece in phrasings:
                hit = piece.match_at([t.lower() for t in tokens], position)
                if hit is not None:
                    break
            if hit is not None:
                items.append(" ".join(current))
                current = []
                position = hit[0]
                continue
            current.append(tokens[position])
            position += 1
        items.append(" ".join(current))
        return tuple(item.strip() for item in items if item.strip())

    def separator_forms(self) -> Tuple[str, ...]:
        """Every surface that may separate two items, in rank order.

        The first rank's words, then the mark, then the second rank's.  It
        is what a corpus writes questions with: a list form that is only
        ever written with its first separator is a list form measured on one
        of its spellings.
        """
        out: List[str] = []
        if self.separators is not None:
            out += [" ".join(alternative)
                    for alternative in self.separators.alternatives]
        out.append(self.mark)
        if self.fallback is not None:
            out += [" ".join(alternative)
                    for alternative in self.fallback.alternatives]
        return tuple(out)

    def cut(self, tokens: Sequence[str]) -> Tuple[str, ...]:
        """Cut a filled run of tokens into its items, in order.

        Deterministic and greedy from the left: at each position the longest
        separator alternative that matches ends the current item.  Nothing
        back-tracks and nothing is scored, so the items are a function of the
        token list.

        A ``fallback`` phrasing is a *second rank* of separators, tried only
        when the first rank leaves too few items.  It is described rather
        than merged into one set because the hand-written branch it restates
        has two ranks: it cuts a comparison at a comma or an ``and`` first,
        and only reaches for ``or`` / ``versus`` / ``vs`` when that produced
        one value.  Merging the ranks would read ``a or b and c`` as three
        items where the branch reads two.
        """
        assert self.separators is not None
        items = self._cut_with(tokens, (self.separators,))
        if len(items) < self.minimum and self.fallback is not None:
            items = self._cut_with(tokens,
                                   (self.separators, self.fallback))
        return items


def list_slot(name: str, role: str, separators: Phrasing,
              names: Sequence[str], minimum: int = 2,
              preserve_case: bool = False, keep_articles: bool = False,
              fallback: Optional[Phrasing] = None) -> ListSlot:
    """A named hole whose filling is a sequence of items."""
    return ListSlot(name=name, role=role, keep_articles=keep_articles,
                    preserve_case=preserve_case, separators=separators,
                    names=tuple(names), minimum=minimum, fallback=fallback)


#: A shape is a sequence of these: literal phrasings and named holes.
Piece = Union[Phrasing, Slot]


@dataclass(frozen=True)
class PreamblePiece:
    """One family of words a question may carry *before* its opening.

    ``repeatable`` says whether the family may be matched more than once in
    a row.  It is not a stylistic choice: the shipped parser strips its
    courtesy fillers in a loop and its interrogative opener once, so a
    description that reproduces the shipped surface has to say which is
    which.
    """

    phrasing: "Phrasing"
    repeatable: bool = False

    def render(self) -> str:
        return self.phrasing.render() + ("*" if self.repeatable else "?")


def preamble_piece(phrasing_: "Phrasing", repeatable: bool = False
                   ) -> PreamblePiece:
    """One family of leading words, repeatable or not."""
    return PreamblePiece(phrasing=phrasing_, repeatable=repeatable)


@dataclass(frozen=True)
class Preamble:
    """A described *leading remainder*: what may precede a shape's opening.

    A shape is recognised by its opening, and the first version of this
    description language required that opening at the head of the string.
    That was too narrow for the surface the project already ships: ``please
    measure hot in tea`` and ``what is measure hot in tea`` are answered
    today, because the hand-written parser looks for its verb anywhere in
    the token stream.

    Rather than let the opening float free -- which would make *any* leading
    text acceptable, and the hand-written parser demonstrably mis-reads such
    questions, keeping the stray words inside a slot -- the description says
    exactly which leading words it admits.  A preamble is an ordered list of
    :class:`PreamblePiece`\\ s, each a phrasing that may be skipped before
    the opening; the order is the order they may appear in, and everything
    else before an opening is still declined.

    Each piece is a :class:`Phrasing` and so carries its own justification:
    admitting a word here is a decision about English exactly as admitting a
    separator is, and the audit counts it the same way.
    """

    pieces: Tuple[PreamblePiece, ...]
    why: str

    @property
    def judgements(self) -> int:
        """How many decisions about English the preamble states."""
        return len(self.pieces)

    def render(self) -> str:
        return " ".join(piece.render() for piece in self.pieces)

    def forms(self) -> Tuple[str, ...]:
        """Every single surface form the preamble admits, in order."""
        return tuple(" ".join(words)
                     for piece in self.pieces
                     for words in piece.phrasing.alternatives)

    def skip(self, tokens: Sequence[str], start: int = 0
             ) -> Tuple[int, Tuple[str, ...]]:
        """Consume the preamble at ``start``; return where it ends and it.

        Deterministic and greedy in one pass: each piece is tried in turn at
        the current position, a repeatable piece as many times as it matches
        and a non-repeatable one at most once.  Nothing back-tracks, so the
        end position is a function of the tokens.
        """
        position = start
        taken: List[str] = []
        for piece in self.pieces:
            while True:
                hit = piece.phrasing.match_at(tokens, position)
                if hit is None:
                    break
                position, surface = hit
                taken.append(surface)
                if not piece.repeatable:
                    break
        return position, tuple(taken)


@dataclass(frozen=True)
class Refusal:
    """A boundary a described question can hit, named in the description.

    ``name`` is the boundary; ``reason`` is the sentence the refusal prints,
    with ``{...}`` fields filled from the slots that were matched.  A question
    the descriptions cannot decide is declined *with the boundary named*,
    which is the difference between a stated limit and a gap.

    ``raises`` says what the *runtime* does when this boundary fires: a
    boundary marked ``raises`` is a malformed question and is reported as an
    error, and one that is not is passed to the solver with the slot left
    empty.  The distinction used to live in the hand-written branches -- a
    derivation with no separator raised, a measurement with no subject did
    not -- and it is described here so that those branches could be deleted
    without changing what a reader of the CLI sees.
    """

    name: str
    reason: str
    raises: bool = False


@dataclass(frozen=True)
class QuestionSpec:
    """One described question shape.

    ``kind`` is the query kind a match produces -- the same string
    :data:`glm_universal.runtime.parser.KINDS` uses, so a description can
    stand in for the hand-written rule that produced it.  ``shape`` is the
    sequence of literal phrasings and named holes, and it must open with a
    :class:`Phrasing`: a question is recognised by its opening, and never by
    a keyword found somewhere in the middle.  ``preamble`` says which leading
    words -- and only which -- may stand in front of that opening.
    """

    kind: str
    gloss: str
    shape: Tuple[Piece, ...]
    refusals: Tuple[Refusal, ...] = ()
    preamble: Optional[Preamble] = None
    meanings: Tuple[Tuple[str, str], ...] = ()
    meaning_option: str = ""

    def __post_init__(self) -> None:
        if not self.shape:
            raise ValueError("QuestionSpec: an empty shape matches nothing")
        if not isinstance(self.shape[0], Phrasing):
            raise ValueError(
                f"QuestionSpec {self.kind!r}: a shape must open with a "
                f"phrasing, so a question is recognised by its opening")
        names = [piece.name for piece in self.shape if isinstance(piece, Slot)]
        if not names:
            raise ValueError(
                f"QuestionSpec {self.kind!r}: a shape with no slot asks "
                f"nothing")
        if len(set(names)) != len(names):
            raise ValueError(
                f"QuestionSpec {self.kind!r}: duplicate slot name in {names}")
        for first, second in zip(self.shape, self.shape[1:]):
            if isinstance(first, Slot) and isinstance(second, Slot):
                raise ValueError(
                    f"QuestionSpec {self.kind!r}: slots {first.name!r} and "
                    f"{second.name!r} are adjacent, so no word separates "
                    f"them and the split would be a guess")
        if self.meanings and not self.meaning_option:
            raise ValueError(
                f"QuestionSpec {self.kind!r}: the openings' meanings are "
                f"declared and no option is named to carry them")

    # -- what the description says, read back --------------------------------

    @property
    def opening(self) -> Phrasing:
        """The phrasing a question of this shape must open with."""
        first = self.shape[0]
        assert isinstance(first, Phrasing)
        return first

    @property
    def slots(self) -> Tuple[Slot, ...]:
        return tuple(piece for piece in self.shape if isinstance(piece, Slot))

    @property
    def lists(self) -> Tuple["ListSlot", ...]:
        return tuple(piece for piece in self.shape
                     if isinstance(piece, ListSlot))

    @property
    def marks(self) -> bool:
        """Does this shape need the comma kept as a token of its own?"""
        return bool(self.lists)

    @property
    def options(self) -> Tuple[str, ...]:
        """The option names a match of this shape fills, in order.

        A plain slot fills the option it is named for; a list slot fills one
        option per item it names; and where the opening's identity is part of
        the answer, the option that carries it is filled too.
        """
        out: List[str] = []
        for piece in self.shape:
            if isinstance(piece, ListSlot):
                out.extend(piece.names)
            elif isinstance(piece, Slot):
                out.append(piece.name)
        if self.meaning_option:
            out.append(self.meaning_option)
        return tuple(out)

    def meaning_of(self, surface: str) -> str:
        """What the opening that was written means, if that is part of it."""
        for written, meaning in self.meanings:
            if written == surface:
                return meaning
        return ""

    @property
    def phrasings(self) -> Tuple[Phrasing, ...]:
        return tuple(piece for piece in self.shape
                     if isinstance(piece, Phrasing))

    @property
    def judgements(self) -> int:
        """How many decisions about English this description states."""
        return len(self.phrasings) + (self.preamble.judgements
                                      if self.preamble is not None else 0)

    def roles(self) -> Tuple[str, ...]:
        return tuple(slot_.role for slot_ in self.slots)

    def refusal(self, name: str) -> Refusal:
        for refusal in self.refusals:
            if refusal.name == name:
                return refusal
        raise KeyError(
            f"QuestionSpec {self.kind!r}: no described refusal {name!r}")

    def render(self) -> str:
        """The shape, written the way the documentation writes it."""
        return " ".join(piece.render() for piece in self.shape)

    def phrasing_count(self) -> int:
        """How many distinct surface forms this one description recognises."""
        total = 1
        for piece in self.phrasings:
            total *= len(piece.alternatives)
        return total

    def render_question(self, fills: Mapping[str, str],
                        choices: Optional[Mapping[int, int]] = None) -> str:
        """Write a question of this shape from the values of its slots.

        ``choices`` picks which alternative each phrasing is written with, by
        the phrasing's position in the shape; the default is the first
        alternative.  This is the inverse of matching, and the round trip
        between them is what ``GLM.Question`` proves.
        """
        chosen = dict(choices or {})
        words: list[str] = []
        for position, piece in enumerate(self.shape):
            if isinstance(piece, Phrasing):
                index = chosen.get(position, 0) % len(piece.alternatives)
                surface = piece.alternatives[index]
                following = self.shape[position + 1:]
                next_slot = next((p for p in following if isinstance(p, Slot)),
                                 None)
                if (next_slot is not None and next_slot.optional
                        and not fills.get(next_slot.name, "")):
                    continue
                words.extend(surface)
            elif isinstance(piece, ListSlot):
                assert piece.separators is not None
                forms = piece.separator_forms()
                joint = forms[chosen.get(position, 0) % len(forms)]
                items = [fills.get(name, "") for name in piece.names]
                written = [item for item in items if item]
                if len(written) < piece.minimum:
                    raise ValueError(
                        f"render_question: the list {piece.name!r} needs "
                        f"{piece.minimum} items and {len(written)} were "
                        f"given")
                text = (f"{piece.mark} ".join(written)
                        if joint == piece.mark
                        else f" {joint} ".join(written))
                words.extend(text.lower().split())
            else:
                value = fills.get(piece.name, "")
                if not value:
                    if not piece.optional:
                        raise ValueError(
                            f"render_question: slot {piece.name!r} is "
                            f"required and no value was given")
                    continue
                words.extend(value.lower().split())
        return " ".join(words)


def describe_specs(specs: Sequence[QuestionSpec]) -> Dict[str, object]:
    """What the descriptions say, before any question is matched."""
    return {
        "kinds": tuple(spec.kind for spec in specs),
        "shapes": {spec.kind: spec.render() for spec in specs},
        "slots": {spec.kind: tuple(s.name for s in spec.slots)
                  for spec in specs},
        "roles": {spec.kind: spec.roles() for spec in specs},
        "judgements": {spec.kind: spec.judgements for spec in specs},
        "phrasings": {spec.kind: spec.phrasing_count() for spec in specs},
        "preamble": {spec.kind: (spec.preamble.render()
                                 if spec.preamble is not None else "")
                     for spec in specs},
        "refusals": {spec.kind: tuple(r.name for r in spec.refusals)
                     for spec in specs},
    }
