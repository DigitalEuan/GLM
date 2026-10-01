"""The one generic path: a question, matched against the described shapes.

Nothing in this module knows what a coordinate, a measure word or a task is.
It walks the tokens of a question left to right against a
:class:`~glm_universal.language.question.QuestionSpec`, fills the slots with
the runs of tokens between the literal words, and either returns a
:class:`Match` -- a query kind and its options, ready for the same solver the
hand-written parser feeds -- or a :class:`Decline` that names the boundary it
hit.

The rules, in full
------------------
1. A question must **open** with one of the shape's opening phrasings, at the
   head of the string -- or after the shape's described **preamble**, which
   is the closed set of courtesy and generic-interrogative words that may
   introduce a question without changing it.  A keyword found in the middle
   of arbitrary text is still not an opening: the shipped parser accepts one
   and reads the stray words into a slot, this declines, and the difference
   is measured rather than assumed (see :func:`agreement` and
   :func:`narrowing`).
2. Each slot is filled with the tokens up to the **earliest** occurrence of
   the phrasing that follows it, and the search resumes after that phrasing.
3. A slot with no phrasing after it takes the rest of the question.
4. If the phrasing after a slot is absent and every slot from there on is
   optional, the slot takes the rest and the optional ones are left empty.
   Otherwise the question is declined at ``no_separator``.
5. A required slot that comes out empty is declined at ``empty_<slot>``.
   An optional slot that comes out empty is empty, which is not a refusal.
6. A slot's filling loses a leading article unless the slot keeps them; see
   :attr:`~glm_universal.language.question.Slot.keep_articles`.

Every one of those is integer token arithmetic.  There is no scoring, no
back-tracking and no regular expression, so the match is a function of the
token list, and ``RequestProject/GLM/Question.lean`` proves the parts of it
that are not a measurement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Tuple,
                    Union)

from .question import (ListSlot, Phrasing, QuestionSpec, Slot,
                       describe_specs, tokenise, tokenise_cased)
from .descriptions import DESCRIBED_KINDS, QUESTIONS

__all__ = [
    "Match", "Decline", "Outcome", "ARTICLES", "walk",
    "match", "parse", "options_of", "render", "openings_disjoint",
    "corpus", "agreement", "refusal_audit", "describe",
    "decorations", "narrowing", "STRAY_OPENINGS",
    "infix_corpus", "infix_agreement", "undescribed_parts",
    "UNDESCRIBED_PARTS", "nested_corpus", "nested_agreement",
    "widening", "WIDENINGS", "coverage",
]

#: Leading words a slot drops unless it is declared to keep them.  The set is
#: the shipped parser's, so that a description reproduces it exactly.
ARTICLES: Tuple[str, ...] = ("the", "of", "for", "to", "a", "an")


# ===========================================================================
# 1.  WHAT A MATCH IS
# ===========================================================================

@dataclass(frozen=True)
class Match:
    """A question recognised by a described shape."""

    kind: str
    fills: Mapping[str, str]
    surfaces: Tuple[str, ...]
    trace: Tuple[str, ...]

    matched: bool = True

    def option(self, name: str) -> str:
        return self.fills.get(name, "")


@dataclass(frozen=True)
class Decline:
    """A question the descriptions will not decide, with the boundary named.

    ``boundary`` is the name a description gives the limit; ``reason`` is the
    sentence it writes.  A decline is a *stated* limit and is why the
    surface can be driven off descriptions at all: the alternative to
    declining is guessing which slot the missing words belonged to.
    """

    boundary: str
    reason: str
    kind: Optional[str] = None
    trace: Tuple[str, ...] = ()

    matched: bool = False


Outcome = Union[Match, Decline]


# ===========================================================================
# 2.  MATCHING ONE SHAPE
# ===========================================================================

def _strip_articles(words: Sequence[str]) -> Tuple[str, ...]:
    out = list(words)
    while out and out[0].lower() in ARTICLES:
        out.pop(0)
    return tuple(out)


def _fill_text(words: Sequence[str], piece: Slot) -> str:
    kept = tuple(words) if piece.keep_articles else _strip_articles(words)
    return " ".join(kept)


def _reason(spec: QuestionSpec, boundary: str, question: str,
            fills: Mapping[str, str]) -> str:
    """The sentence the description writes for this boundary."""
    try:
        described = spec.refusal(boundary)
    except KeyError:
        return (f"{question!r} does not fit the shape "
                f"{spec.render()!r} ({boundary})")
    fields: Dict[str, object] = {"question": question}
    fields.update(fills)
    try:
        return described.reason.format(**fields)
    except (KeyError, IndexError):  # pragma: no cover - a malformed sentence
        return described.reason


def walk(shape: Sequence[Any], tokens: Sequence[str],
         cased: Sequence[str], position: int, spec: Any, question: str,
         fills: Dict[str, str], surfaces: List[str],
         trace: List[str]) -> Optional[Decline]:
    """Fill the holes of ``shape`` from ``tokens``, starting at ``position``.

    This is the walk described in the module docstring, and it is a function
    of the token list and nothing else.  It is separated from :func:`match`
    because a *nested* shape -- an operand that is itself a shape -- needs
    exactly this walk over a run of tokens that is not a whole question, and
    a second copy of it would be a second description language.

    ``spec`` is used only for the sentences a refusal prints and the kind it
    names, so anything that answers ``kind`` and ``refusal`` will serve.
    Returns ``None`` when every hole is filled, and a :class:`Decline`
    otherwise; ``fills``, ``surfaces`` and ``trace`` are filled in place.
    """
    index = 0
    while index < len(shape):
        piece = shape[index]
        if isinstance(piece, Phrasing):
            hit = piece.match_at(tokens, position)
            if hit is None:
                return Decline(
                    boundary="no_separator",
                    reason=_reason(spec, "no_separator", question, fills),
                    kind=spec.kind, trace=tuple(trace))
            position, surface = hit
            surfaces.append(surface)
            index += 1
            continue

        begin_at = position
        following = (shape[index + 1] if index + 1 < len(shape) else None)
        if following is None:
            end_at, position = len(tokens), len(tokens)
            consumed_to = len(shape)
        else:
            assert isinstance(following, Phrasing)
            hit = following.first_match(tokens, position)
            if hit is None:
                later = [p for p in shape[index + 1:]
                         if isinstance(p, Slot)]
                if not all(p.optional for p in later):
                    trace.append(f"no {following.render()!r} after "
                                 f"{piece.name!r}")
                    return Decline(
                        boundary="no_separator",
                        reason=_reason(spec, "no_separator", question, fills),
                        kind=spec.kind, trace=tuple(trace))
                end_at, position = len(tokens), len(tokens)
                consumed_to = len(shape)
                trace.append(
                    f"{following.render()!r} is absent and every slot after "
                    f"{piece.name!r} is optional, so they stay empty")
            else:
                begin, after, surface = hit
                end_at = begin
                position = after
                surfaces.append(surface)
                consumed_to = index + 2

        source = cased if piece.preserve_case else tokens
        words = source[begin_at:end_at]

        if isinstance(piece, ListSlot):
            if not piece.keep_articles:
                words = _strip_articles(words)
            items = piece.cut(words)
            if len(items) < piece.minimum:
                trace.append(f"the list {piece.name!r} holds "
                             f"{len(items)} item(s)")
                return Decline(
                    boundary=f"short_{piece.name}",
                    reason=_reason(spec, f"short_{piece.name}", question,
                                   dict(fills, items=str(len(items)))),
                    kind=spec.kind, trace=tuple(trace))
            for name, item in zip(piece.names, items):
                fills[name] = item
            trace.append(f"list {piece.name!r} ({piece.role}) cut at "
                         f"{piece.separators.render()!r} into "
                         f"{items[:len(piece.names)]!r}")
            index = consumed_to
            continue

        filled = _fill_text(words, piece)
        if not filled and not piece.optional:
            trace.append(f"slot {piece.name!r} is empty")
            return Decline(
                boundary=f"empty_{piece.name}",
                reason=_reason(spec, f"empty_{piece.name}", question, fills),
                kind=spec.kind, trace=tuple(trace))
        if filled and not piece.admits(filled):
            trace.append(f"slot {piece.name!r} is filled with {filled!r}, "
                         f"which is not a {piece.form}")
            return Decline(
                boundary=f"unshaped_{piece.name}",
                reason=_reason(spec, f"unshaped_{piece.name}", question,
                               dict(fills, **{piece.name: filled})),
                kind=spec.kind, trace=tuple(trace))
        fills[piece.name] = filled
        trace.append(f"slot {piece.name!r} ({piece.role}) = {filled!r}")
        index = consumed_to
    return None


def match(spec: QuestionSpec, question: str) -> Outcome:
    """Match one question against one described shape."""
    tokens = tokenise(question, marks=spec.marks)
    cased = tokenise_cased(question, marks=spec.marks)
    trace: List[str] = [f"tokens {tokens!r}"]
    head, skipped = ((0, ()) if spec.preamble is None
                     else spec.preamble.skip(tokens))
    if skipped:
        trace.append(f"preamble {list(skipped)!r} skipped; the opening is "
                     f"looked for after it")
    opened = spec.opening.match_at(tokens, head)
    if opened is None:
        return Decline(
            boundary="unrecognised_opening",
            reason=(f"{question!r} does not open with any of "
                    f"{spec.opening.render()!r}, so it is not a "
                    f"{spec.kind} question"),
            kind=None, trace=tuple(trace))
    position, surface = opened
    surfaces: List[str] = [surface]
    trace.append(f"opening {surface!r} matched; {spec.kind} shape entered")

    fills: Dict[str, str] = {name: "" for name in spec.options}
    if spec.meaning_option:
        fills[spec.meaning_option] = spec.meaning_of(surface)
        trace.append(f"the opening written is part of the answer: "
                     f"{spec.meaning_option} = "
                     f"{fills[spec.meaning_option]!r}")
    declined = walk(spec.shape[1:], tokens, cased, position, spec, question,
                    fills, surfaces, trace)
    if declined is not None:
        return declined
    return Match(kind=spec.kind, fills=dict(fills),
                 surfaces=tuple(surfaces), trace=tuple(trace))


def parse(question: str,
          specs: Sequence[QuestionSpec] = QUESTIONS) -> Outcome:
    """Match a question against every described shape.

    The openings are disjoint (:func:`openings_disjoint`), so at most one
    shape can be entered and the order the shapes are tried in cannot change
    the answer.  A question that opens no shape is declined at
    ``unrecognised_opening`` with the openings listed, which is the honest
    statement of what the descriptions cover.
    """
    entered: List[Outcome] = []
    for spec in specs:
        outcome = match(spec, question)
        if outcome.matched or outcome.boundary != "unrecognised_opening":
            entered.append(outcome)
    if len(entered) == 1:
        return entered[0]
    if not entered:
        openings = "; ".join(spec.opening.render() for spec in specs)
        return Decline(
            boundary="unrecognised_opening",
            reason=(f"{question!r} opens none of the described shapes; the "
                    f"described openings are {openings}"),
            kind=None, trace=(f"tokens {tokenise(question)!r}",))
    kinds = ", ".join(str(outcome.kind) for outcome in entered)
    return Decline(  # pragma: no cover - openings_disjoint forbids this
        boundary="ambiguous_opening",
        reason=(f"{question!r} opens more than one described shape "
                f"({kinds}); the descriptions do not decide between them"),
        kind=None, trace=())


def options_of(outcome: Outcome) -> Dict[str, str]:
    """The options a match carries, keyed as the runtime keys them.

    A slot is *named* for the option it fills, so this is a copy and not a
    translation table: the mapping from a described shape to a runtime query
    is the identity, which is what keeps the description from acquiring a
    hidden second half in code.
    """
    if not isinstance(outcome, Match):
        return {}
    return dict(outcome.fills)


def render(spec: QuestionSpec, fills: Mapping[str, str],
           choices: Optional[Mapping[int, int]] = None) -> str:
    """Write a question of this shape -- the inverse of :func:`match`."""
    return spec.render_question(fills, choices)


def openings_disjoint(specs: Sequence[QuestionSpec] = QUESTIONS
                      ) -> Dict[str, Any]:
    """Check that no surface form opens two *different* described shapes.

    A prefix counts as a clash, not just an equal form: if one shape opened
    with ``task`` and another with ``task force``, a question beginning
    ``task force ...`` would enter both, and which one answered would be the
    order they were tried in.  Within a single shape a prefix is harmless --
    ``measure`` and ``measure word`` are alternatives of one opening and the
    longer is matched first -- so the test is across shapes only.
    """
    seen: Dict[Tuple[str, ...], str] = {}
    clashes: List[Tuple[str, str, str]] = []
    for spec in specs:
        for words in spec.opening.alternatives:
            for known, kind in list(seen.items()):
                if kind == spec.kind:
                    continue
                shorter, longer = sorted((known, words), key=len)
                if longer[:len(shorter)] == shorter:
                    clashes.append((" ".join(known), " ".join(words),
                                    f"{kind}/{spec.kind}"))
            seen[words] = spec.kind
    return {"openings": len(seen), "clashes": tuple(clashes),
            "disjoint": not clashes}


def describe(specs: Sequence[QuestionSpec] = QUESTIONS) -> Dict[str, Any]:
    """What the descriptions say, before any question is matched."""
    return describe_specs(specs)


# ===========================================================================
# 3.  THE CORPUS, GENERATED FROM THE REGISTERS
# ===========================================================================
#
#  The corpus is not a list of questions somebody wrote.  Its values come out
#  of the registers the questions are about -- the coordinates and objects of
#  the domain descriptions, the measure words, the worked tasks -- and its
#  phrasings are every combination the descriptions declare.  Adding a
#  coordinate or a measure word therefore widens the corpus without anyone
#  having to remember to widen it.

def _derive_values() -> Tuple[Tuple[str, str, str], ...]:
    """``(coordinate, object, domain)`` triples out of the descriptions."""
    from ..recipe import DESCRIPTIONS
    out: List[Tuple[str, str, str]] = []
    for spec in DESCRIPTIONS:
        names = [str(facts["name"]) for facts in spec.facts()]
        for coordinate in spec.coordinates[:2]:
            for object_name in names[:2]:
                out.append((coordinate.name.lower(), object_name.lower(),
                            spec.name.lower()))
    return tuple(out)


def _measure_values() -> Tuple[Tuple[str, str], ...]:
    """``(subject, class)`` pairs out of the measure register."""
    from ..reasoning import measure_view as mv
    from ..recipe import COMPARISON_DESCRIPTION
    classes = [str(facts["name"]).lower()
               for facts in COMPARISON_DESCRIPTION.facts()][:3]
    words = [word.word.lower() for word in mv.measure_words()][:4]
    return tuple((word, klass) for word in words for klass in classes)


def _task_values() -> Tuple[str, ...]:
    from ..runtime.session import TASKS
    return tuple(name.lower() for name in TASKS)


def corpus(specs: Sequence[QuestionSpec] = QUESTIONS
           ) -> Tuple[Tuple[str, str, Dict[str, str]], ...]:
    """``(kind, question, expected fills)`` over every declared phrasing.

    Every opening of every shape is crossed with every separator of that
    shape and with the values above, and the optional slots are written both
    ways.  The questions are lower case throughout: the shipped parser
    preserves the case of an operand and this matcher folds it, so a
    comparison between them is only well defined where there is no case to
    lose.  That restriction is stated in the report rather than hidden.
    """
    out: List[Tuple[str, str, Dict[str, str]]] = []
    by_kind = {spec.kind: spec for spec in specs}

    derive = by_kind.get("derive")
    if derive is not None:
        separators = derive.shape[2]
        assert isinstance(separators, Phrasing)
        for opening in range(len(derive.opening.alternatives)):
            for split in range(len(separators.alternatives)):
                for coordinate, object_name, domain in _derive_values():
                    for named in ("", domain):
                        fills = {"coordinate": coordinate,
                                 "object": object_name, "domain": named}
                        question = derive.render_question(
                            fills, {0: opening, 2: split})
                        out.append(("derive", question, dict(fills)))

    measure = by_kind.get("measure")
    if measure is not None:
        separators = measure.shape[2]
        assert isinstance(separators, Phrasing)
        for opening in range(len(measure.opening.alternatives)):
            for split in range(len(separators.alternatives)):
                for subject, klass in _measure_values():
                    for named in (klass, ""):
                        fills = {"subject": subject, "class": named}
                        question = measure.render_question(
                            fills, {0: opening, 2: split})
                        out.append(("measure", question, dict(fills)))

    task = by_kind.get("task")
    if task is not None:
        for opening in range(len(task.opening.alternatives)):
            for name in _task_values():
                fills = {"task": name}
                question = task.render_question(fills, {0: opening})
                out.append(("task", question, dict(fills)))

    compare = by_kind.get("compare")
    if compare is not None:
        values = compare.shape[1]
        assert isinstance(values, ListSlot)
        for opening in range(len(compare.opening.alternatives)):
            for split in range(len(values.separator_forms())):
                for left, right in _compare_values():
                    fills = {"left": left, "right": right}
                    question = compare.render_question(
                        fills, {0: opening, 1: split})
                    expected = dict(fills)
                    expected[compare.meaning_option] = compare.meaning_of(
                        " ".join(compare.opening.alternatives[opening]))
                    out.append(("compare", question, expected))

    out.extend(_decorated(out, specs))

    seen: Dict[str, None] = {}
    unique: List[Tuple[str, str, Dict[str, str]]] = []
    for kind, question, fills in out:
        if question in seen:
            continue
        seen[question] = None
        unique.append((kind, question, fills))
    return tuple(unique)


#: How many questions of each kind are written again with a preamble.  The
#: preamble is independent of the shape it introduces -- one matcher skips
#: it before any shape is entered -- so crossing every decoration with every
#: question would multiply the corpus without measuring anything new.
DECORATED_PER_KIND: int = 4


def decorations(specs: Sequence[QuestionSpec] = QUESTIONS) -> Tuple[str, ...]:
    """Every leading remainder the descriptions admit, written out.

    Each single surface form of each preamble piece, plus two forms that
    exercise the *structure* of the preamble rather than its vocabulary: a
    repeated courtesy opening, which only the repeatable piece allows, and a
    courtesy followed by an interrogative, which only the declared order
    allows.
    """
    seen: Dict[str, None] = {}
    for spec in specs:
        if spec.preamble is None:
            continue
        for form in spec.preamble.forms():
            seen.setdefault(form, None)
        pieces = spec.preamble.pieces
        repeatable = [p for p in pieces if p.repeatable]
        once = [p for p in pieces if not p.repeatable]
        if repeatable:
            first = repeatable[0].phrasing.alternatives
            if len(first) >= 2:
                seen.setdefault(" ".join(first[-1] + first[-2]), None)
        if repeatable and once:
            seen.setdefault(" ".join(repeatable[0].phrasing.alternatives[-1]
                                     + once[0].phrasing.alternatives[-1]),
                            None)
    return tuple(seen)


def _decorated(rows: Sequence[Tuple[str, str, Dict[str, str]]],
               specs: Sequence[QuestionSpec]
               ) -> List[Tuple[str, str, Dict[str, str]]]:
    """The same questions, introduced by each admitted leading remainder."""
    prefixes = decorations(specs)
    if not prefixes:
        return []
    taken: Dict[str, int] = {}
    out: List[Tuple[str, str, Dict[str, str]]] = []
    for kind, question, fills in rows:
        if taken.get(kind, 0) >= DECORATED_PER_KIND:
            continue
        taken[kind] = taken.get(kind, 0) + 1
        for prefix in prefixes:
            out.append((kind, f"{prefix} {question}", dict(fills)))
    return out


def other_kind_questions() -> Tuple[Tuple[str, str], ...]:
    """``(kind, question)`` for kinds the descriptions do **not** cover.

    Taken from the evaluation set, which is the corpus the whole runtime is
    already held to, so this half of the measurement is not a list of
    questions chosen to be declined.
    """
    from ..evaluation.cases import CASES
    from ..runtime.parser import QueryError, parse_query
    out: List[Tuple[str, str]] = []
    for case in CASES:
        question = getattr(case, "question", None)
        if not isinstance(question, str) or not question.strip():
            continue
        try:
            parsed = parse_query(question)
        except QueryError:
            continue
        if parsed.kind in DESCRIBED_KINDS:
            continue
        out.append((parsed.kind, question))
    return tuple(out)


# ===========================================================================
# 4.  THE MEASUREMENT
# ===========================================================================

def _shipped(question: str) -> Optional[Tuple[str, Dict[str, object]]]:
    """What the hand-written branch made of a question, or ``None``.

    The branches are no longer in the parser -- the runtime reads these three
    kinds off these descriptions -- so the comparison is against
    :mod:`glm_universal.language.legacy`, which is what they said when they
    were removed.  Measuring against the live parser would now be measuring
    the descriptions against themselves.
    """
    from .legacy import legacy_parse, legacy_parse_shaped
    read = legacy_parse(question)
    if read is None:
        # `compare` is described by a slot shape as well -- 'compare a and
        # b' is an opening with a list after it -- and its branch is frozen
        # beside the other three shaped ones.
        read = legacy_parse_shaped(question)
    if read is None:
        return None
    kind, options = read
    out = {name: value for name, value in options.items()
           if name != "__operands__"}
    return kind, out


def agreement(specs: Sequence[QuestionSpec] = QUESTIONS) -> Dict[str, Any]:
    """Run both parsers over the corpus and compare them question by question.

    Three outcomes are counted and they are not the same thing:

    ``agreed``
        the described shape produced the kind the shipped parser produced,
        and every option it fills has the value the shipped parser gave it;
    ``declined``
        the described shape refused, naming a boundary.  A refusal is a
        stated limit, not a wrong answer, and it is reported separately;
    ``disagreed``
        the described shape answered, and answered differently.  This is the
        number that has to be zero, and the disagreements are returned in
        full rather than summarised so that a regression names itself.
    """
    agreed = 0
    declined: List[Tuple[str, str]] = []
    disagreed: List[Dict[str, Any]] = []
    rows = corpus(specs)
    for kind, question, expected in rows:
        shipped = _shipped(question)
        outcome = parse(question, specs)
        if not isinstance(outcome, Match):
            declined.append((question, outcome.boundary))
            continue
        if shipped is None:
            disagreed.append({"question": question, "described": outcome.kind,
                              "shipped": "QueryError"})
            continue
        shipped_kind, shipped_options = shipped
        mine = options_of(outcome)
        differing = {key: (value, shipped_options.get(key))
                     for key, value in mine.items()
                     if shipped_options.get(key) != value}
        if outcome.kind == shipped_kind == kind and not differing:
            if dict(expected) != mine:  # pragma: no cover - a broken corpus
                disagreed.append({"question": question, "described": mine,
                                  "shipped": "corpus round trip"})
                continue
            agreed += 1
        else:
            disagreed.append({"question": question, "described": outcome.kind,
                              "shipped": shipped_kind,
                              "options": differing})

    outside = other_kind_questions()
    false_positives: List[Dict[str, str]] = []
    for shipped_kind, question in outside:
        outcome = parse(question, specs)
        if isinstance(outcome, Match):
            false_positives.append({"question": question,
                                    "described": outcome.kind,
                                    "shipped": shipped_kind})
    return {
        "corpus": len(rows),
        "agreed": agreed,
        "declined": tuple(declined),
        "disagreed": tuple(disagreed),
        "outside": len(outside),
        "false_positives": tuple(false_positives),
        "exact": not disagreed and not false_positives,
    }


#: Leading text that is **not** described, paired with why it is not.  Each
#: one puts an opening in the middle of a question, which is exactly what
#: the shipped parser will find and the descriptions will not.
STRAY_OPENINGS: Tuple[Tuple[str, str], ...] = (
    ("the tea",
     "a bare noun phrase: it names something, so skipping it would throw "
     "away part of the question"),
    ("give me",
     "a courtesy form the shipped parser does not strip either, which is "
     "why its words end up inside the answer's subject"),
    ("run",
     "an imperative of its own; two imperatives in one question do not "
     "make one question"),
    ("in tea",
     "a separator phrase before the opening: reading it would mean "
     "deciding that a slot may precede the word that introduces it"),
    ("what is please",
     "the described words in an order the description does not declare -- "
     "the shipped parser strips its courtesy openings only at the head, so "
     "here it does not strip this one either"),
)


def narrowing(specs: Sequence[QuestionSpec] = QUESTIONS) -> Dict[str, Any]:
    """The commitment: an undescribed leading remainder is declined.

    The shipped parser finds its verb anywhere in the token stream, so a
    question with arbitrary text in front of an opening is *answered* rather
    than refused.  What it answers, though, is not the question: the stray
    words are still in the remainder when the slots are filled, so they come
    back inside an option -- ``the tea measure hot`` is answered with the
    subject ``'tea  hot'``.

    The descriptions decline instead, and this is the measurement that makes
    the narrowing a decision rather than a loss.  For every witness it
    records what the shipped parser made of it, whether the stray words
    survived into one of the options (``polluted``), and that the described
    matcher declined at ``unrecognised_opening``.  ``exact`` is true when
    every witness is declined by the descriptions *and* was mis-read by the
    parser -- if a witness were read correctly by the parser, the narrowing
    would be throwing something away and this would say so.
    """
    rows: List[Dict[str, Any]] = []
    for spec in specs:
        base = _plain_question(spec)
        if base is None:
            continue
        for prefix, why in STRAY_OPENINGS:
            question = f"{prefix} {base}"
            read = _shipped(question)
            if read is None:
                shipped_kind: Optional[str] = None
                shipped_options: Dict[str, object] = {}
            else:
                shipped_kind, shipped_options = read[0], dict(read[1])
            stray = tokenise(prefix)
            polluted = tuple(
                name for name, value in shipped_options.items()
                if isinstance(value, str)
                and any(word in tokenise(value) for word in stray))
            outcome = parse(question, specs)
            rows.append({
                "kind": spec.kind, "question": question, "why": why,
                "shipped_kind": shipped_kind,
                "shipped_options": shipped_options,
                "polluted": polluted,
                "described": ("matched" if isinstance(outcome, Match)
                              else outcome.boundary),
            })
    declined = tuple(row for row in rows
                     if row["described"] == "unrecognised_opening")
    misread = tuple(row for row in rows
                    if row["polluted"] or row["shipped_kind"] is None)
    return {
        "witnesses": tuple(rows),
        "declined": len(declined),
        "misread_by_the_parser": len(misread),
        "exact": len(declined) == len(rows) == len(misread) and bool(rows),
        "commitment": (
            "a question whose opening is preceded by anything the preamble "
            "does not describe is declined at 'unrecognised_opening'; the "
            "shipped parser answers it, and in every witness the words it "
            "skipped over came back inside an option"),
    }


def _plain_question(spec: QuestionSpec) -> Optional[str]:
    """One question of this shape, written from the shape itself."""
    for kind, question, _fills in corpus((spec,)):
        if kind == spec.kind and " ".join(
                spec.opening.alternatives[0]) == " ".join(
                    tokenise(question)[:len(spec.opening.alternatives[0])]):
            return question
    return None


# ===========================================================================
# 4b.  THE SECOND SHAPE, MEASURED THE SAME WAY
# ===========================================================================
#
#  The infix shapes are measured the way the slot shapes are: against the
#  hand-written branches, frozen in `glm_universal.language.legacy` at the
#  moment they were deleted from the parser.  Measuring against the live
#  parser would now measure the descriptions against themselves, because the
#  runtime reads these kinds off these descriptions.

def _verify_values() -> Tuple[Tuple[str, str], ...]:
    """``(lhs, rhs)`` pairs out of the physics register's own relations."""
    return (
        ("force", "mass * acceleration"),
        ("power", "energy / time"),
        ("pressure", "force / area"),
        ("energy", "mass * velocity"),
    )


def _analogy_values() -> Tuple[Tuple[str, str, str, str], ...]:
    """``(a, b, c, d)`` four-term analogies over register names."""
    return (
        ("hot", "temperature", "fast", "?"),
        ("force", "mass", "energy", "?"),
        ("proton", "charge", "electron", "?"),
    )


def _compare_values() -> Tuple[Tuple[str, str], ...]:
    """``(left, right)`` exact-real notations."""
    return (
        ("sqrt(2)", "7/5"),
        ("3/2", "6/4"),
        ("pi", "22/7"),
    )


def infix_corpus(specs: Sequence[Any] = ()
                 ) -> Tuple[Tuple[str, str, Dict[str, str]], ...]:
    """``(kind, question, expected operands)`` for the infix shapes.

    Every operator alternative is crossed with every operand tuple and with
    the opening written and left out, and the first question of each kind is
    written again behind every admitted preamble.  As with the slot corpus,
    the values come out of the registers the questions are about rather than
    from a list somebody typed.
    """
    from .descriptions import INFIX_QUESTIONS
    from .infix import InfixSpec

    chosen: Sequence[InfixSpec] = specs or INFIX_QUESTIONS
    values = {
        "verify": tuple({"lhs": a, "rhs": b} for a, b in _verify_values()),
        "analogy": tuple({"a": a, "b": b, "c": c, "d": d}
                         for a, b, c, d in _analogy_values()),
        "compare": tuple({"left": a, "right": b}
                         for a, b in _compare_values()),
    }
    out: List[Tuple[str, str, Dict[str, str]]] = []
    for spec in chosen:
        rows = values.get(spec.kind, ())
        openings: List[Optional[int]] = [None]
        if spec.opening is not None:
            openings += list(range(len(spec.opening.alternatives)))
        for index, fills in enumerate(rows):
            for operator in range(len(spec.operator.alternatives)):
                for opening in openings:
                    question = spec.render_question(
                        fills, operator=operator, opening=opening)
                    out.append((spec.kind, question, dict(fills)))
                    if opening is None and spec.closing is not None:
                        for words in spec.closing.alternatives:
                            out.append((spec.kind,
                                        f"{question} {' '.join(words)}",
                                        dict(fills)))
                    if index == 0 and operator == 0:
                        for extra in _infix_option_questions(
                                spec, question, head=opening is None):
                            out.append((spec.kind, extra, dict(fills)))

    decorated: List[Tuple[str, str, Dict[str, str]]] = []
    taken: Dict[str, int] = {}
    for kind, question, fills in out:
        if taken.get(kind, 0) >= 2:
            continue
        taken[kind] = taken.get(kind, 0) + 1
        for prefix in _infix_decorations(chosen):
            decorated.append((kind, f"{prefix} {question}", dict(fills)))
    out.extend(decorated)

    seen: Dict[str, None] = {}
    unique: List[Tuple[str, str, Dict[str, str]]] = []
    for kind, question, fills in out:
        if question in seen:
            continue
        seen[question] = None
        unique.append((kind, question, fills))
    return tuple(unique)


def _infix_option_questions(spec: Any, question: str,
                            head: bool) -> List[str]:
    """The same question written again carrying each described option.

    A modifier is written in both of the positions its description admits
    -- at the head, and in the trailing frame -- and a trailing option in
    each of its declared forms.  ``head`` is false where the question is
    already introduced by an opening, because a qualifier before the verb
    is a position neither the branch nor the description reads.
    """
    out: List[str] = []
    for modifier in getattr(spec, "modifiers", ()):
        seen: Dict[str, None] = {}
        for word, meaning in modifier.values:
            if meaning in seen:
                continue
            seen[meaning] = None
            if head:
                out.append(f"{word} {question}")
            if modifier.prepositions is not None:
                frame = " ".join(modifier.prepositions.alternatives[0])
                out.append(f"{question} {frame} {word} {modifier.noun}")
    for option in getattr(spec, "trailing", ()):
        if option.form == "qualified_name":
            for head_name in option.heads:
                out.append(f"{question} in {head_name}.dimension")
        elif option.introducers is not None:
            for alternative in option.introducers.alternatives:
                out.append(f"{question} {' '.join(alternative)} 5")
    return out


def _infix_decorations(specs: Sequence[Any]) -> Tuple[str, ...]:
    seen: Dict[str, None] = {}
    for spec in specs:
        if spec.preamble is None:
            continue
        for form in spec.preamble.forms():
            seen.setdefault(form, None)
    return tuple(seen)


def _shipped_infix(question: str) -> Optional[Tuple[str, Dict[str, object]]]:
    """What the hand-written infix branch made of a question, or ``None``.

    As with :func:`_shipped`: the branches are gone from the parser, so the
    comparison is against :mod:`glm_universal.language.legacy`, which is
    what they said when they were removed.
    """
    from .legacy import legacy_parse_shaped
    read = legacy_parse_shaped(question)
    if read is None:
        return None
    kind, options = read
    out: Dict[str, object] = dict(options)
    out.setdefault("__operands__", ())
    return kind, out


def infix_agreement(specs: Sequence[Any] = ()) -> Dict[str, Any]:
    """The infix descriptions against the parser, question by question.

    What is compared is everything the description *carries*: the operands,
    in the order the runtime takes them; where the operator's identity is
    part of the answer, the relation it names; and every option beside them
    -- a ``verify`` question's semantics qualifier, an ``analogy``
    question's subspace and limit -- which earlier rounds left undescribed
    and this one describes.
    """
    from .descriptions import INFIX_QUESTIONS
    from .infix import InfixMatch, parse_infix

    chosen = specs or INFIX_QUESTIONS
    by_kind = {spec.kind: spec for spec in chosen}
    agreed = 0
    declined: List[Tuple[str, str]] = []
    disagreed: List[Dict[str, Any]] = []
    rows = infix_corpus(chosen)
    for kind, question, _expected in rows:
        spec = by_kind[kind]
        outcome = parse_infix(question, chosen)
        if not isinstance(outcome, InfixMatch):
            declined.append((question, outcome.boundary))
            continue
        shipped = _shipped_infix(question)
        if shipped is None:
            disagreed.append({"question": question, "described": outcome.kind,
                              "shipped": "QueryError"})
            continue
        shipped_kind, read = shipped
        mine = outcome.carried(spec)
        if spec.into == "operands":
            theirs = {name: value for name, value in
                      zip(spec.carried, read.get("__operands__", ()))}
        else:
            theirs = {name: read.get(name) for name in spec.carried}
        mine = dict(mine)
        theirs = dict(theirs)
        if spec.meaning_option:
            mine[spec.meaning_option] = outcome.meaning
            theirs[spec.meaning_option] = read.get(spec.meaning_option)
        for name in spec.carried_options:
            if name == spec.meaning_option:
                continue
            if name in outcome.options or name in read:
                mine[name] = outcome.options.get(name)
                theirs[name] = read.get(name)
        if outcome.kind == shipped_kind == kind and mine == theirs:
            agreed += 1
        else:
            disagreed.append({"question": question, "described": outcome.kind,
                              "shipped": shipped_kind,
                              "mine": mine, "theirs": theirs})
    outside, false_positives = _infix_outside(chosen)
    return {
        "corpus": len(rows),
        "agreed": agreed,
        "declined": tuple(declined),
        "disagreed": tuple(disagreed),
        "outside": outside,
        "false_positives": tuple(false_positives),
        "exact": (not disagreed and not declined and not false_positives),
    }


def _infix_outside(specs: Sequence[Any]
                   ) -> Tuple[int, List[Dict[str, str]]]:
    """The false-positive half: questions of other kinds must be declined.

    The set is the evaluation set again, minus the kinds these shapes
    describe.  A comparative -- ``is cold in stellar_surface hotter than hot
    in tea`` -- is the one to watch: it is infix in the ordinary sense and
    holds no described operator, so a shape that matched it would be reading
    a question it cannot answer.
    """
    from ..evaluation.cases import CASES
    from ..runtime.parser import QueryError, parse_query
    from .infix import InfixMatch, parse_infix

    kinds = {spec.kind for spec in specs}
    seen = 0
    caught: List[Dict[str, str]] = []
    for case in CASES:
        question = getattr(case, "question", None)
        if not isinstance(question, str) or not question.strip():
            continue
        try:
            parsed = parse_query(question)
        except QueryError:
            continue
        if parsed.kind in kinds:
            continue
        seen += 1
        outcome = parse_infix(question, specs)
        if isinstance(outcome, InfixMatch):
            caught.append({"question": question, "described": outcome.kind,
                           "shipped": parsed.kind})
    return seen, caught


# ===========================================================================
# 4c.  THE THIRD SHAPE, MEASURED THE SAME WAY
# ===========================================================================
#
#  A nested shape is an operator whose operands are not text but *matches*:
#  each side of `is cold in stellar_surface hotter than hot in tea` is
#  itself the measure shape.  It is measured exactly as the other two are,
#  against the frozen branch, and its own false-positive half matters more
#  than theirs: an exact-real comparison is infix in the same way and must
#  be declined rather than read as a comparison of two readings.

def _comparative_values() -> Tuple[Tuple[str, str, str, str], ...]:
    """``(left word, left class, right word, right class)`` for the sides.

    Out of the measure register, as the measure corpus is: the words are
    measure words and the classes are comparison classes, so a comparative
    written from them is a question the runtime could be asked.
    """
    pairs = _measure_values()
    out: List[Tuple[str, str, str, str]] = []
    for (left_word, left_class), (right_word, right_class) in zip(
            pairs, pairs[1:] + pairs[:1]):
        out.append((left_word, left_class, right_word, right_class))
    return tuple(out)


def nested_corpus(specs: Sequence[Any] = ()
                  ) -> Tuple[Tuple[str, str, Dict[str, Any]], ...]:
    """``(kind, question, expected options)`` for the nested shapes.

    Both forms of the operator -- the ``-er than`` comparative and the ``as
    ... as`` equative -- are crossed with every separator the nested shape
    admits, with the opening written and left out, and the first questions
    are written again behind every admitted preamble.
    """
    from .descriptions import NESTED_QUESTIONS

    chosen = specs or NESTED_QUESTIONS
    out: List[Tuple[str, str, Dict[str, Any]]] = []
    for spec in chosen:
        openings: List[Optional[int]] = [None]
        if spec.opening is not None:
            openings += list(range(len(spec.opening.alternatives)))
        for values in _comparative_values():
            left_word, left_class, right_word, right_class = values
            fills = {"left_word": left_word, "left_class": left_class,
                     "right_word": right_word, "right_class": right_class}
            for equative in (False, True):
                word = (left_word if equative
                        else f"{left_word}{spec.operator.suffix}")
                for separator in range(spec.separators):
                    for opening in openings:
                        question = spec.render_question(
                            fills, word=word, equative=equative,
                            opening=opening, separator=separator)
                        expected = dict(fills)
                        expected[spec.operator.form_option] = word
                        expected[spec.operator.equative_option] = equative
                        out.append((spec.kind, question, expected))

    decorated: List[Tuple[str, str, Dict[str, Any]]] = []
    taken: Dict[str, int] = {}
    for kind, question, expected in out:
        if taken.get(kind, 0) >= DECORATED_PER_KIND:
            continue
        taken[kind] = taken.get(kind, 0) + 1
        for prefix in _infix_decorations(chosen):
            decorated.append((kind, f"{prefix} {question}", dict(expected)))
    out.extend(decorated)

    seen: Dict[str, None] = {}
    unique: List[Tuple[str, str, Dict[str, Any]]] = []
    for kind, question, expected in out:
        if question in seen:
            continue
        seen[question] = None
        unique.append((kind, question, expected))
    return tuple(unique)


def nested_agreement(specs: Sequence[Any] = ()) -> Dict[str, Any]:
    """The nested descriptions against the frozen branch, question by
    question.

    Every option is compared, both sides of both readings included, and the
    false-positive half is the evaluation set minus this kind.

    A third count sits beside ``agreed`` and ``disagreed``: ``widened``,
    the questions this shape answers and the frozen branch declined.  They
    are not disagreements -- there is no answer to differ from -- and they
    are not agreements either, so they are counted on their own and their
    cause is stated in :data:`WIDENINGS`.
    """
    from .descriptions import NESTED_QUESTIONS
    from .nested import NestedMatch, match_nested

    chosen = specs or NESTED_QUESTIONS
    by_kind = {spec.kind: spec for spec in chosen}
    agreed = 0
    declined: List[Tuple[str, str]] = []
    disagreed: List[Dict[str, Any]] = []
    widened: List[str] = []
    rows = nested_corpus(chosen)
    for kind, question, expected in rows:
        spec = by_kind[kind]
        outcome = match_nested(spec, question)
        if not isinstance(outcome, NestedMatch):
            declined.append((question, outcome.boundary))
            continue
        shipped = _shipped_infix(question)
        if shipped is None:
            widened.append(question)
            continue
        shipped_kind, read = shipped
        mine = {name: outcome.options.get(name) for name in spec.options}
        theirs = {name: read.get(name) for name in spec.options}
        if (outcome.kind == shipped_kind == kind and mine == theirs
                and mine == {name: expected[name] for name in spec.options}):
            agreed += 1
        else:
            disagreed.append({"question": question, "described": outcome.kind,
                              "shipped": shipped_kind,
                              "mine": mine, "theirs": theirs})
    outside, false_positives = _nested_outside(chosen)
    return {
        "corpus": len(rows),
        "agreed": agreed,
        "declined": tuple(declined),
        "disagreed": tuple(disagreed),
        "widened": tuple(widened),
        "outside": outside,
        "false_positives": tuple(false_positives),
        "exact": (not disagreed and not declined and not false_positives),
    }


def _nested_outside(specs: Sequence[Any]
                    ) -> Tuple[int, List[Dict[str, str]]]:
    """Questions of other kinds, which the nested shape must decline."""
    from ..evaluation.cases import CASES
    from ..runtime.parser import QueryError, parse_query
    from .nested import NestedMatch, match_nested

    kinds = {spec.kind for spec in specs}
    seen = 0
    caught: List[Dict[str, str]] = []
    for case in CASES:
        question = getattr(case, "question", None)
        if not isinstance(question, str) or not question.strip():
            continue
        try:
            parsed = parse_query(question)
        except QueryError:
            continue
        if parsed.kind in kinds:
            continue
        seen += 1
        for spec in specs:
            outcome = match_nested(spec, question)
            if isinstance(outcome, NestedMatch):
                caught.append({"question": question,
                               "described": outcome.kind,
                               "shipped": parsed.kind})
    return seen, caught


# ===========================================================================
# 4d.  WHERE THE DESCRIPTION IS WIDER THAN THE BRANCH
# ===========================================================================

#: Questions the descriptions answer and the hand-written branches did not,
#: with why the widening is admitted.  Every one of them is a *found*
#: difference rather than a designed one: they came out of the measurement
#: and are written down here so that the agreement figures can be read
#: honestly.  A widening is not a disagreement -- the branch declined, so
#: there is no answer to differ from -- but it is a change, and a change
#: that is not counted is a change that is hidden.
WIDENINGS: Tuple[Tuple[str, str], ...] = (
    ("is hot relative to tea hotter than hot in tea",
     "a side of a comparative is the measure shape, and the measure shape "
     "admits five separators. The branch this replaces spelled its sides "
     "out with a regular expression of its own, which listed four of them "
     "-- 'in', 'for', 'against', 'within' -- and not 'relative to', so a "
     "comparative written with 'relative to' on a side was unknown to it "
     "and is read here. The two-word separator being the one it missed is "
     "the tell: a side spelled out a second time is a side that drifts "
     "from the shape it copies, which is exactly what nesting the measure "
     "shape instead of restating it prevents"),
)


def _branch_separators(spec: Any) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """``(admitted, refused)``: which spellings of a side the branch read.

    Measured rather than asserted: one comparative is written with each
    separator the nested shape admits and handed to the frozen branch.  The
    ones it declines are the cause of every widened row, and deriving them
    this way means the audit cannot go stale against the branch.
    """
    fills = {"left_word": "hot", "left_class": "tea",
             "right_word": "cold", "right_class": "tea"}
    admitted: List[str] = []
    refused: List[str] = []
    for index in range(spec.separators):
        question = spec.render_question(fills, word="hotter",
                                        separator=index)
        surface = _separator_surface(spec, index)
        (admitted if _shipped_infix(question) is not None
         else refused).append(surface)
    return tuple(admitted), tuple(refused)


def _separator_surface(spec: Any, index: int) -> str:
    """The words the ``index``-th spelling of a side's separator writes."""
    for piece in spec.side.pieces:
        if isinstance(piece, Phrasing):
            return " ".join(
                piece.alternatives[index % len(piece.alternatives)])
    return ""


def widening(specs: Sequence[Any] = ()) -> Dict[str, Any]:
    """Check every declared widening is still exactly that, and account for
    every widened row of the corpus.

    A declared row holds if the descriptions answer the question and the
    frozen branch declined it.  A row that no longer holds is reported:
    either the branch reads it after all -- in which case the row was never
    a widening -- or the descriptions have stopped reading it, in which
    case the row is stale.

    Beside the declared rows the whole nested corpus is accounted for: every
    question the descriptions answered and the branch declined must write a
    separator the branch refuses, and every question written only with
    separators it admits must have been read by it.  That is what makes the
    widening *one* difference with many witnesses rather than an unexamined
    set.
    """
    from .descriptions import INFIX_QUESTIONS, NESTED_QUESTIONS
    from .infix import InfixMatch, parse_infix
    from .nested import NestedMatch, match_nested

    chosen = specs or NESTED_QUESTIONS
    rows: List[Dict[str, Any]] = []
    for question, why in WIDENINGS:
        described: Optional[str] = None
        outcome = parse(question)
        if isinstance(outcome, Match):
            described = outcome.kind
        if described is None:
            infix = parse_infix(question, INFIX_QUESTIONS)
            if isinstance(infix, InfixMatch):
                described = infix.kind
        if described is None:
            for spec in chosen:
                nested = match_nested(spec, question)
                if isinstance(nested, NestedMatch):
                    described = nested.kind
                    break
        shipped = _shipped(question) or _shipped_infix(question)
        rows.append({
            "question": question,
            "described": described or "declined",
            "shipped": shipped[0] if shipped else "declined",
            "why": why,
            "holds": described is not None and shipped is None,
        })
    admitted, refused = _branch_separators(chosen[0])
    measured = nested_agreement(chosen)
    unexplained = [question for question in measured["widened"]
                   if not any(f" {surface} " in f" {question} "
                              for surface in refused)]
    return {
        "witnesses": len(rows),
        "rows": tuple(rows),
        "admitted": admitted,
        "refused": refused,
        "measured": len(measured["widened"]),
        "agreed": measured["agreed"],
        "unexplained": tuple(unexplained),
        "holds": (all(row["holds"] for row in rows) and bool(rows)
                  and not unexplained and bool(refused)),
    }


def coverage() -> Dict[str, Any]:
    """How much of the surface is described, counted rather than claimed.

    ``kinds`` is every query kind the parser can produce, ``unknown``
    excluded because it is what the parser produces when it recognises
    nothing.  ``described`` is the kinds some shape family covers, and
    every one of them is also *read off* its description by the runtime:
    there is no branch left for any of them.
    """
    from ..runtime.parser import KINDS
    from .descriptions import DESCRIBED_KINDS, INFIX_KINDS, NESTED_KINDS

    kinds = tuple(kind for kind in KINDS if kind != "unknown")
    described = tuple(sorted(set(DESCRIBED_KINDS) | set(INFIX_KINDS)
                             | set(NESTED_KINDS)))
    return {
        "kinds": len(kinds),
        "described": len(described),
        "described_kinds": described,
        "undescribed_kinds": tuple(sorted(set(kinds) - set(described))),
        "slot": tuple(DESCRIBED_KINDS),
        "infix": tuple(INFIX_KINDS),
        "nested": tuple(NESTED_KINDS),
        "families": 3,
    }


#: What the described shapes do **not** cover, and why.  A limit that is
#: counted is a limit; a limit that is only true is a gap waiting to be
#: found.
UNDESCRIBED_PARTS: Tuple[Tuple[str, str], ...] = (
    ("thirteen kinds have no description at all",
     "`describe`, `nearest`, `product`, `cluster`, `spatial`, `project`, "
     "`trilinear`, `coherence`, `report`, `angle`, `pi_groups`, "
     "`meaning` and `real` are still read by a branch apiece in "
     "`glm_universal.runtime.parser`. Seven of the twenty kinds are "
     "described and the count is in :func:`coverage`; what is *not* "
     "claimed is that the three shape families cover the surface, and the "
     "thirteen are the measurement of that"),
    ("the described kinds fold the case of their operands",
     "a slot keeps the case it was written in only where its description "
     "says so -- the comparison list does, because `Pb` is an element and "
     "`pb` is nothing -- and everywhere else the fill is lower case. The "
     "corpora are therefore written in lower case, and the agreement is "
     "a statement about questions with no case to lose"),
    ("a verb *inside* an operand is not removed",
     "the branch scanned the whole question for its verb and cut it out "
     "wherever it was, so `is 5 holds = 5` lost its `holds` from the "
     "middle of the left-hand side. A described opening is read at the "
     "head and a described closing at the tail, and nowhere else. That is "
     "a narrowing rather than a gap -- a word deleted from the middle of "
     "an expression changes the expression -- and it is recorded here "
     "because it is a difference and differences are counted"),
)


def undescribed_parts() -> Tuple[Dict[str, str], ...]:
    """The named limits of the described shapes, as rows."""
    return tuple({"part": part, "why": why}
                 for part, why in UNDESCRIBED_PARTS)


def round_trip(specs: Sequence[QuestionSpec] = QUESTIONS) -> Dict[str, Any]:
    """Write each corpus question back from its fills and match it again.

    Rendering is the inverse of matching on the described shapes; this is the
    measured half of what ``GLM.Question.matchPieces_rendered`` proves.
    """
    checked = 0
    broken: List[Dict[str, Any]] = []
    by_kind = {spec.kind: spec for spec in specs}
    for kind, question, _expected in corpus(specs):
        spec = by_kind[kind]
        outcome = match(spec, question)
        if not isinstance(outcome, Match):
            broken.append({"question": question, "why": outcome.boundary})
            continue
        written = spec.render_question(outcome.fills)
        again = match(spec, written)
        if not isinstance(again, Match) or dict(again.fills) != dict(
                outcome.fills):
            broken.append({"question": question, "written": written})
            continue
        checked += 1
    return {"checked": checked, "broken": tuple(broken),
            "exact": not broken}


def _empty_slot_witness(spec: QuestionSpec, target: Slot) -> str:
    """A question of this shape with exactly one required slot left empty.

    Written from the shape rather than by hand, so a description that grows a
    slot grows a witness for it and cannot describe a boundary it never
    reaches.  Everything from the first optional slot on is dropped: an
    optional slot left out is not a refusal.
    """
    words: List[str] = []
    for position, piece in enumerate(spec.shape):
        if isinstance(piece, Phrasing):
            following = next((p for p in spec.shape[position + 1:]
                              if isinstance(p, Slot)), None)
            if following is not None and following.optional:
                break
            words.extend(piece.alternatives[0])
        else:
            if piece.optional:
                break
            if piece.name != target.name:
                words.append("x")
    return " ".join(words)


def refusal_audit(specs: Sequence[QuestionSpec] = QUESTIONS
                  ) -> Dict[str, Any]:
    """Exercise every boundary a description names, with a witness each.

    A refusal that is only written down is a claim; a refusal with a witness
    that hits it is a measurement.  Each described boundary is given a
    question that reaches it, and the audit fails if the boundary is not the
    one that fires or if a boundary the matcher can reach was never
    described.
    """
    rows: List[Dict[str, Any]] = []
    reached: Dict[str, int] = {}
    for spec in specs:
        opening = " ".join(spec.opening.alternatives[0])
        separator = next((piece for piece in spec.shape[1:]
                          if isinstance(piece, Phrasing)), None)
        witnesses: List[Tuple[str, str]] = []
        for target in spec.slots:
            if isinstance(target, ListSlot):
                # A list slot's boundary is not emptiness but *shortness*:
                # the question that reaches it names fewer items than the
                # shape requires, and naming none is one such question.
                witnesses.append((f"short_{target.name}",
                                  f"{opening} x"))
            elif not target.optional:
                witnesses.append((f"empty_{target.name}",
                                  _empty_slot_witness(spec, target)))
        if separator is not None and any(
                not piece.optional for piece in spec.slots[1:]):
            witnesses.append(("no_separator", f"{opening} x"))
        for boundary, question in witnesses:
            outcome = parse(question, specs)
            hit = (outcome.boundary if isinstance(outcome, Decline)
                   else "matched")
            reached[hit] = reached.get(hit, 0) + 1
            rows.append({
                "kind": spec.kind, "boundary": boundary,
                "question": question, "hit": hit,
                "described": any(r.name == hit for r in spec.refusals),
                "as_described": hit == boundary,
            })
    undescribed = tuple(row for row in rows if not row["described"])
    wrong = tuple(row for row in rows if not row["as_described"])
    return {"witnesses": tuple(rows), "boundaries": len(reached),
            "undescribed": undescribed, "wrong": wrong,
            "exact": not undescribed and not wrong}
