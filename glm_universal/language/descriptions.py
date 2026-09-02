"""Three question shapes, written down.

These are the shapes the hand-written parser recognises for three of its
query kinds, restated as descriptions.  Nothing here is new language: each
opening is exactly the set of surface forms
:data:`glm_universal.runtime.parser.VERBS` maps to that kind, and each
separator is exactly the set the corresponding branch of
:func:`~glm_universal.runtime.parser.parse_query` splits on.  Writing them
down is the point -- once the shape is an object, the matcher is generic, the
count of decisions about English is a figure rather than a habit, and a new
domain can arrive with its questions instead of waiting for a hand-written
branch.

Which three, and why not all of them
------------------------------------
A shape is *an opening, then slots separated by literal words*.  Three of the
runtime's kinds are exactly that and are described here:

``derive``
    ``derive <coordinate> of <object>``, optionally ``in <domain>``.
``measure``
    ``measure <subject>``, optionally ``in <class>``.
``task``
    ``task <task>``.

The rest are not, and are deliberately left alone rather than forced:
``analogy`` is recognised by an infix operator (``a : b :: c : ?``),
``verify`` by a top-level ``=``, ``comparative`` by a suffix (``-er than``)
whose two sides must each be a measured use, ``compare`` by a keyword that
splits the *original* string rather than a remainder, and ``describe`` by a
bare concept name resolving in the register index.  A description language
that could express those would be a parser generator; this one is a
description of one shape, and it says so.

What the matcher is held to
---------------------------
:mod:`glm_universal.language.build` matches against these and nothing else,
and :mod:`glm_universal.language.report` measures the result against the
shipped parser over a generated corpus: same kind, same options, or a refusal
with the boundary named.  A question of a kind that is *not* described must
be declined, not misread -- that is the false-positive half of the same
measurement.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .infix import InfixSpec, Modifier, TrailingOption
from .nested import DegreeOperator, NestedSide, NestedSpec
from .question import (Preamble, QuestionSpec, Refusal, list_slot, phrasing,
                       preamble_piece, slot)

__all__ = [
    "DERIVE_QUESTION", "MEASURE_QUESTION", "TASK_QUESTION",
    "COMPARE_LIST_QUESTION",
    "QUESTIONS", "DESCRIBED_KINDS", "STANDARD_PREAMBLE",
    "COURTESY", "COURTESY_PREAMBLE", "INTERROGATIVE",
    "ANALOGY_QUESTION", "COMPARE_QUESTION", "VERIFY_QUESTION",
    "INFIX_QUESTIONS", "INFIX_KINDS", "infix_by_kind",
    "COMPARATIVE_QUESTION", "NESTED_QUESTIONS", "NESTED_KINDS",
    "nested_by_kind", "question_by_kind", "described_kinds",
]


# ===========================================================================
# 0.  THE LEADING REMAINDER, DESCRIBED
# ===========================================================================
#
#  The round that wrote the first three shapes stopped at a measured
#  difference: the described matcher wanted its opening at the head of the
#  string, and the shipped parser finds its verb anywhere, so `please measure
#  hot in tea` was answered by one and declined by the other.  The two ways
#  out were named at the time -- describe the leading remainder, or narrow
#  the surface and record the narrowing -- and both are taken here, because
#  the shipped parser's freedom is not one thing but two.
#
#  What it accepts *usefully* is a closed set: the courtesy openings it
#  strips before it looks at anything (`please`, `could you`, ...) and the
#  generic interrogative it strips after (`what is`, `tell me about`, ...).
#  Those are described below, and the described matcher now reads every
#  question of that form exactly as the parser does.
#
#  What it accepts *by accident* is everything else: `the tea measure hot`
#  finds `measure` in the middle and answers with the subject `'tea  hot'`,
#  the stray words still in the slot.  A description will not reproduce that,
#  and the project does not want it reproduced -- so the surface narrows
#  there, deliberately, and `glm_universal.language.build.narrowing` holds
#  the witnesses: for each one, what the shipped parser used to answer and
#  which slot the leftovers landed in.

COURTESY = phrasing(
    "please", "could you", "can you", "would you", "i want to know",
    "i would like to know", "kindly",
    why="the seven courtesy openings the shipped parser strips before it "
        "reads anything. They are one set because none of them changes "
        "which question is being asked -- dropping every one of them leaves "
        "the same question -- and they are described here rather than "
        "stripped silently so that the count of words the surface admits is "
        "a figure and not a habit")

INTERROGATIVE = phrasing(
    "what is", "tell me about", "explain", "profile", "address",
    why="the five generic interrogative openings the shipped parser treats "
        "as weak: each one asks for *something* about what follows without "
        "saying which reading is wanted, so a more specific opening later "
        "in the question governs. Admitting them in front of an opening is "
        "the same judgement the parser makes, and it is made once rather "
        "than per kind")

#: What may stand in front of an opening, and nothing else may.
#:
#: The order is the order the shipped parser applies them in -- courtesy
#: first and repeatedly, because it strips them in a loop; the interrogative
#: once, because it strips one.  Reproducing that order is what makes
#: ``please what is measure hot in tea`` read the same way in both.
STANDARD_PREAMBLE = Preamble(
    pieces=(
        preamble_piece(COURTESY, repeatable=True),
        preamble_piece(INTERROGATIVE),
    ),
    why="a question may be introduced politely or generically without "
        "becoming a different question; anything else before an opening is "
        "declined rather than skipped, because a description that skipped "
        "arbitrary words would be guessing where the question starts")

#: What may stand in front of an *infix* question, which is less.
#:
#: A slot shape is recognised by a word, so a generic interrogative in front
#: of it is unambiguous: the shipped parser's own rule is that a weak opener
#: yields to a more specific keyword later in the question.  An infix shape
#: has no keyword to yield to -- everything to the left of the operator *is*
#: the left operand -- so ``what is force = mass * acceleration`` is read by
#: the shipped parser as a request to describe something, and admitting the
#: interrogative here would be inventing a rule the surface does not have.
#: The courtesy openings still apply, because those are stripped before the
#: parser reads anything at all.
COURTESY_PREAMBLE = Preamble(
    pieces=(preamble_piece(COURTESY, repeatable=True),),
    why="an infix question may be asked politely; it may not be introduced "
        "by a generic interrogative, because it has no keyword for one to "
        "be weaker than and the words would be read as its left operand")


# ===========================================================================
# 1.  DERIVE -- one coordinate of one object
# ===========================================================================

DERIVE_QUESTION = QuestionSpec(
    kind="derive",
    gloss="one coordinate of one object, answered off the domain "
          "descriptions",
    shape=(
        phrasing(
            "derive", "derivation of", "coordinate", "which coordinate",
            "what derives",
            why="the five openings the shipped parser maps to `derive`. "
                "`derivation of` and `which coordinate` are kept as whole "
                "openings rather than being read as `derivation` plus a "
                "separator, because `derivation of tea` asks nothing: the "
                "`of` there is part of the opening, and which of the two it "
                "is cannot be decided by counting words"),
        slot("coordinate", "coordinate"),
        phrasing(
            "of", "for", "on",
            why="three prepositions that all attach a coordinate to the "
                "object it is a coordinate of. English lets a coordinate be "
                "`of` a thing, `for` a thing or `on` a thing with no change "
                "of meaning here; that they are one set is a judgement, and "
                "it is the same one the shipped parser makes"),
        slot("object", "object", keep_articles=True),
        phrasing(
            "in",
            why="the one word that names the domain a coordinate is to be "
                "read in. `within` and `under` would be defensible and are "
                "deliberately not admitted: the domain tail is optional, so "
                "every word admitted here is a word that can no longer "
                "appear inside an object's name"),
        slot("domain", "domain", optional=True, keep_articles=True),
    ),
    refusals=(
        Refusal(
            "no_separator",
            "a derivation needs a coordinate and an object, written "
            "'<coordinate> of <object>'; {question!r} names only one thing",
            raises=True),
        Refusal(
            "empty_coordinate",
            "{question!r} opens a derivation but names no coordinate before "
            "the separator",
            raises=True),
        Refusal(
            "empty_object",
            "{question!r} asks for the coordinate {coordinate!r} of nothing; "
            "an object has to be named after the separator",
            raises=True),
    ),
    preamble=STANDARD_PREAMBLE,
)


# ===========================================================================
# 2.  MEASURE -- a measure word read against a comparison class
# ===========================================================================

MEASURE_QUESTION = QuestionSpec(
    kind="measure",
    gloss="a measure word, or a magnitude, read against a comparison class",
    shape=(
        phrasing(
            "measure", "how much", "relative measure", "measure word",
            "how far up",
            why="the five openings the shipped parser maps to `measure`. "
                "`how much` and `how far up` are questions where the others "
                "are imperatives; they are one set because the answer asked "
                "for is the same reading, which is a fact about the register "
                "and not about the grammar"),
        slot("subject", "subject"),
        phrasing(
            "in", "for", "against", "within", "relative to",
            why="five ways of naming what a measure word is measured "
                "against. `hot in tea`, `hot for tea` and `hot relative to "
                "tea` are the same question; `hot against tea` is a stretch "
                "in isolation and is admitted because the register's own "
                "wording uses it"),
        slot("class", "class", optional=True),
    ),
    refusals=(
        Refusal(
            "empty_subject",
            "{question!r} opens a measurement but names nothing to measure",
            raises=False),
    ),
    preamble=STANDARD_PREAMBLE,
    # There is deliberately no `empty_class` boundary: the class is
    # optional, `measure hot` is a question, and a boundary that can never
    # be reached is a claim rather than a limit.  The audit in
    # `glm_universal.language.build.refusal_audit` gives every described
    # boundary a witness, so an unreachable one would be caught here.
)


# ===========================================================================
# 3.  TASK -- a worked end-to-end run
# ===========================================================================

TASK_QUESTION = QuestionSpec(
    kind="task",
    gloss="one of the worked end-to-end tasks, run through the whole "
          "pipeline",
    shape=(
        phrasing(
            "task", "solve task", "puzzle", "worked example",
            why="the four openings the shipped parser maps to `task`. "
                "`puzzle` is the odd one: it names the grid task by what it "
                "is rather than by what running it is, and it is in the set "
                "because the shipped surface has always accepted it"),
        slot("task", "task"),
    ),
    refusals=(
        Refusal(
            "empty_task",
            "{question!r} asks for a task and names none",
            raises=False),
    ),
    preamble=STANDARD_PREAMBLE,
)


# ===========================================================================
# 3b.  COMPARE, THE LIST FORM -- A SLOT WHOSE FILLING IS A SEQUENCE
# ===========================================================================
#
#  `compare sqrt(2) and 1.5` is not an infix question: `compare` is an
#  opening, and what follows it is one hole holding *two* values.  The round
#  that described the infix comparison named this as one of the four parts it
#  could not describe, and the piece of description language it needed: a
#  slot whose filling is a **list**.  `question.ListSlot` is that piece, and
#  this is the shape that uses it.
#
#  Two things the list slot has to say, and both are read off the branch it
#  restates rather than invented:
#
#  * the separators come in **two ranks**.  The branch cuts at a comma or an
#    `and` first, and only reaches for `or` / `versus` / `vs` when that left
#    one value; merging the ranks would read `a or b and c` as three items
#    where the branch reads two.
#  * the items **keep their case**.  Both sides go to the exact-real grammar
#    unresolved, and `Pb` is an element where `pb` is nothing.

COMPARE_LIST_QUESTION = QuestionSpec(
    kind="compare",
    gloss="two exact values, named as a list after the opening, and ordered",
    shape=(
        phrasing(
            "compare", "which is bigger", "which is larger",
            why="the three openings the shipped parser maps to `compare` "
                "without naming a relation. They are one set because each "
                "asks for the order of the values that follow and none of "
                "them asserts one, which is exactly what makes the relation "
                "they carry `compare` rather than `greater` or `less`"),
        list_slot(
            "values", "notation",
            separators=phrasing(
                "and",
                why="the one word that joins the items of a comparison "
                    "list, beside the comma. It is the first rank of two: "
                    "the branch this restates cuts here first and only "
                    "reaches for the second rank when this leaves one "
                    "value"),
            fallback=phrasing(
                "versus", "vs", "or",
                why="the second rank of separators, tried only when the "
                    "first leaves too few items. They are one set because "
                    "each of them opposes two values rather than joining "
                    "them, and they are a *rank* rather than more "
                    "alternatives because reading them first would cut "
                    "`a or b and c` into three items where the branch cuts "
                    "two"),
            names=("left", "right"),
            preserve_case=True),
    ),
    meanings=(("compare", "compare"), ("which is bigger", "compare"),
              ("which is larger", "compare")),
    meaning_option="relation",
    refusals=(
        Refusal(
            "short_values",
            "{question!r} names {items} value(s); a comparison needs two, "
            "e.g. 'compare sqrt(2) and 1.5'",
            raises=True),
    ),
    preamble=STANDARD_PREAMBLE,
)


# ===========================================================================
# 4.  THE SECOND SHAPE -- AN OPERATOR WITH AN OPERAND ON EACH SIDE
# ===========================================================================
#
#  The three shapes above are *an opening, then slots separated by literal
#  words*.  The round that wrote them asked the honest next question: is
#  there a second shape, and does it cover more than one kind?  These three
#  descriptions are the answer.  `glm_universal.language.infix` holds the
#  matcher; it cuts a *string* at an operator rather than walking tokens,
#  because an operand of an equation is a notation (`mass * acceleration`,
#  `sqrt(2)`) and a notation is not a run of words.

VERIFY_QUESTION = InfixSpec(
    kind="verify",
    gloss="an identity, checked for dimensional and scale consistency",
    operator=phrasing(
        "=",
        why="one operator, and no worded alternative. `equals` and `is` "
            "would each be defensible and are deliberately not admitted: "
            "the operands here are notations, so a word admitted as the "
            "operator is a word that can no longer appear inside one"),
    operands=(
        slot("lhs", "notation", keep_articles=True),
        slot("rhs", "notation", keep_articles=True),
    ),
    carried=("lhs", "rhs"),
    opening=phrasing(
        "verify", "check", "audit", "is it true that",
        "does it hold that",
        why="the five openings the shipped parser maps to `verify`. They "
            "are optional here, and that is the judgement: an equation is "
            "already a question, and the verb only says again what the `=` "
            "says"),
    closing=phrasing(
        "dimensionally consistent", "holds",
        why="the two verify verbs that are written *after* the equation "
            "rather than before it -- `force = mass * acceleration holds`. "
            "They are described as a closing rather than admitted into the "
            "opening because position is the whole of the difference: read "
            "as an opening they would never match, and left undescribed "
            "they would end up inside the right-hand operand, which would "
            "then name nothing"),
    into="operands",
    not_adjacent_to="=!<>",
    preamble=COURTESY_PREAMBLE,
    modifiers=(
        Modifier(
            option="semantics",
            values=(
                ("dimensionally", "scalar"), ("dimensional", "scalar"),
                ("units", "scalar"), ("unit", "scalar"),
                ("scalar", "scalar"), ("magnitude", "scalar"),
                ("tensor", "full"), ("full", "full"), ("rank", "full"),
                ("parity", "full"), ("vector", "full"),
            ),
            default="scalar",
            prepositions=phrasing(
                "under", "in", "with",
                why="the three prepositions that introduce a trailing "
                    "statement of which reading is wanted. They are one "
                    "set because `under tensor semantics`, `in tensor "
                    "semantics` and `with tensor semantics` ask for the "
                    "same comparison"),
            noun="semantics",
            why="eleven words that select how strictly the two sides are "
                "compared, and the reading each of them selects. They are "
                "a modifier rather than an operand because an equation "
                "with one of them removed is the same equation: `tensor` "
                "in `check tensor force = mass * acceleration` names "
                "nothing in the equation, it says how to compare its "
                "sides. The default is stated -- an unqualified equation "
                "is read for dimension and decimal scale -- because a "
                "default that is not written down is a silent decision. "
                "Where it may be *removed* is narrower than where it may "
                "be written: at the head, or in the trailing frame, and "
                "nowhere else, because a word in the middle of an "
                "expression is plausibly part of it"),
    ),
    refusals=(
        Refusal(
            "operator_repeated",
            "{question!r} holds {count} top-level '=' signs; a chained "
            "equality is not a single relation",
            raises=True),
        Refusal(
            "empty_lhs",
            "{question!r} has nothing on the left of its '='",
            raises=True),
        Refusal(
            "empty_rhs",
            "{question!r} has nothing on the right of its '='",
            raises=True),
    ),
)


ANALOGY_QUESTION = InfixSpec(
    kind="analogy",
    gloss="a proportional analogy, a : b :: c : ?, solved for the fourth "
          "term",
    operator=phrasing(
        "::",
        why="the one operator the shipped parser recognises for an analogy. "
            "`is to` is in the parser's verb table and is not admitted "
            "here: it would make the *inner* operator a word as well, and "
            "`a is to b as c is to what` is a different shape rather than "
            "another spelling of this one"),
    inner=phrasing(
        ":",
        why="the inner operator, which pairs each side. It is one \"same "
            "question\" decision and not two: a side written with `:` and a "
            "side written with anything else would not be the same "
            "analogy"),
    operands=(
        slot("a", "term", keep_articles=True),
        slot("b", "term", keep_articles=True),
        slot("c", "term", keep_articles=True),
        slot("d", "term", optional=True, keep_articles=True),
    ),
    carried=("a", "b", "c"),
    into="operands",
    preamble=COURTESY_PREAMBLE,
    trailing=(
        TrailingOption(
            option="subspace",
            form="qualified_name",
            heads=("physics", "chemistry", "lexicon"),
            why="a subspace is named as a register and a projection of it, "
                "written with a dot. The three heads are the registers "
                "that define subspaces at all, so the set is read off the "
                "registers rather than chosen; that a dotted name in an "
                "analogy is a subspace and not a term is the judgement"),
        TrailingOption(
            option="limit",
            form="count",
            introducers=phrasing(
                "top", "limit",
                why="the two words that introduce how many answers are "
                    "wanted. They are one set because `top 5` and `limit "
                    "5` ask for the same five; the description looks for "
                    "the longer word first, where the branch looked for "
                    "`top` first, which can differ only in a question "
                    "that writes both and means neither"),
            why="a count written after the operands, narrowing how many "
                "answers come back. It is not an operand: an analogy with "
                "it removed is the same analogy, answered as widely as "
                "the register allows"),
    ),
    refusals=(
        Refusal(
            "operator_repeated",
            "{question!r} holds {count} '::' operators; an analogy relates "
            "one pair to one pair",
            raises=True),
        Refusal(
            "malformed_side",
            "the side {side!r} is not a pair: an analogy is written "
            "'a : b :: c : ?', so each side holds exactly one {inner}",
            raises=True),
        Refusal(
            "empty_a",
            "{question!r} opens an analogy with nothing before its first "
            "':'", raises=True),
        Refusal(
            "empty_b",
            "{question!r} names no second term of the first pair",
            raises=True),
        Refusal(
            "empty_c",
            "{question!r} names no third term; the pair being extended has "
            "to start somewhere", raises=True),
    ),
)


COMPARE_QUESTION = InfixSpec(
    kind="compare",
    gloss="two exact values, ordered by a relation the operator names",
    operator=phrasing(
        "greater than", "bigger than", "larger than", "less than",
        "smaller than", "equal to", "the same as",
        why="seven relational operators, and -- unlike every other phrasing "
            "in this package -- they are *not* alternatives meaning the "
            "same thing. They are one phrasing because they occupy the same "
            "position in the same shape; which one was written is part of "
            "the answer and is carried as the relation, which is what "
            "`meanings` below records"),
    operands=(
        slot("left", "notation", keep_articles=True),
        slot("right", "notation", keep_articles=True),
    ),
    carried=("left", "right"),
    opening=phrasing(
        "is", "are", "does", "do",
        why="the copula the shipped parser strips from the left side. It is "
            "optional: `sqrt(2) greater than 7/5` asks the same question as "
            "`is sqrt(2) greater than 7/5`"),
    meanings=(
        ("greater than", "greater"), ("bigger than", "greater"),
        ("larger than", "greater"), ("less than", "less"),
        ("smaller than", "less"), ("equal to", "equal"),
        ("the same as", "equal"),
    ),
    meaning_option="relation",
    preamble=COURTESY_PREAMBLE,
    refusals=(
        Refusal(
            "empty_left",
            "{question!r} compares nothing against something; a comparison "
            "needs two values", raises=True),
        Refusal(
            "empty_right",
            "{question!r} compares something against nothing; a comparison "
            "needs two values", raises=True),
        Refusal(
            "operator_repeated",
            "{question!r} holds {count} relational operators; which two "
            "values are being compared is then a guess",
            raises=True),
    ),
)


# ===========================================================================
# 5.  THE THIRD SHAPE -- AN OPERATOR BETWEEN TWO *SHAPES*
# ===========================================================================
#
#  `is cold in stellar_surface hotter than hot in tea` is infix, and its
#  operands are not notations: each side has to be a *measured use*, which is
#  the shape section 2 already describes.  So the description here nests that
#  one rather than restating it -- the measure shape, entered without its
#  opening, with both slots required and each of them tightened to a single
#  name.  Reusing the shape is the point: a second copy of it would be a
#  second surface, and the two would drift.

COMPARATIVE_QUESTION = NestedSpec(
    kind="comparative",
    gloss="two measured uses, ordered by a degree word",
    operator=DegreeOperator(
        suffix="er",
        tail=phrasing(
            "than",
            why="the one word that follows a comparative degree word. "
                "`hotter to` and `hotter compared with` are not admitted: "
                "the shipped surface has never accepted them, and every "
                "word admitted here is a word that can no longer end a "
                "comparison class's name"),
        frame=phrasing(
            "as",
            why="the word that opens and closes the equative frame. It is "
                "one phrasing used twice rather than two, because `as hot "
                "as` is one construction: a frame whose halves differed "
                "would not be it"),
        why="an operator formed from a degree word rather than listed: any "
            "word ending in `-er` followed by `than`, or any word inside "
            "`as ... as`. The set is open because the register decides "
            "which degree words mean anything, and enumerating them here "
            "would put that decision in two places. Which word was written "
            "is carried, because the direction the comparison asserts is "
            "read off the measure register from it and not decided here"),
    side=NestedSide(
        shape=MEASURE_QUESTION,
        without_opening=True,
        required=("class",),
        forms=(("subject", "word"), ("class", "word")),
        why="a side of a comparative is a measured use, which is the "
            "measure shape -- and three things nesting changes about it, "
            "each a restriction and none an addition. Its opening is "
            "dropped, because inside a comparative a use is recognised by "
            "its position rather than by the word `measure`. Its class "
            "becomes required, because `hot hotter than cold in tea` "
            "compares a reading against nothing. And both slots are "
            "tightened to a single name, which is what keeps `is sqrt(2) "
            "greater than 7/5` -- an exact-real comparison, whose sides "
            "name no class -- out of this shape rather than out of a "
            "special case somewhere else"),
    names=(("subject", "word"), ("class", "class")),
    opening=phrasing(
        "is", "are", "was", "were",
        why="the copula a comparative may open with. It is optional, and "
            "that is the judgement: `cold in stellar_surface hotter than "
            "hot in tea` asks the same question"),
    preamble=COURTESY_PREAMBLE,
    refusals=(
        Refusal(
            "left_not_a_use",
            "the left side {side!r} is not a measured use; a comparative "
            "compares two readings, each written {shape!r}",
            raises=False),
        Refusal(
            "right_not_a_use",
            "the right side {side!r} is not a measured use; a comparative "
            "compares two readings, each written {shape!r}",
            raises=False),
    ),
)


#: Every described nested shape.  There is one, and the count is the
#: measurement: a third shape family that covered one kind and no more would
#: be a parser generator being written one kind at a time, which is exactly
#: the question the second family was made to answer.
NESTED_QUESTIONS: Tuple[NestedSpec, ...] = (COMPARATIVE_QUESTION,)

#: The query kinds the nested descriptions cover.
NESTED_KINDS: Tuple[str, ...] = tuple(spec.kind for spec in NESTED_QUESTIONS)

_BY_NESTED_KIND: Dict[str, NestedSpec] = {spec.kind: spec
                                          for spec in NESTED_QUESTIONS}


def nested_by_kind(kind: str) -> NestedSpec:
    """The nested description of one kind, or a :class:`KeyError`."""
    try:
        return _BY_NESTED_KIND[kind]
    except KeyError:
        raise KeyError(
            f"no described nested shape for {kind!r}; the described nested "
            f"kinds are {', '.join(NESTED_KINDS)}") from None


#: Every described infix shape, in the order a question is tried against
#: them.  The order is not a priority: a question holding two of these
#: operators is declined rather than decided by it.
INFIX_QUESTIONS: Tuple[InfixSpec, ...] = (
    VERIFY_QUESTION, ANALOGY_QUESTION, COMPARE_QUESTION,
)

#: The query kinds the infix descriptions cover.
INFIX_KINDS: Tuple[str, ...] = tuple(spec.kind for spec in INFIX_QUESTIONS)

_BY_INFIX_KIND: Dict[str, InfixSpec] = {spec.kind: spec
                                        for spec in INFIX_QUESTIONS}


def infix_by_kind(kind: str) -> InfixSpec:
    """The infix description of one kind, or a :class:`KeyError`."""
    try:
        return _BY_INFIX_KIND[kind]
    except KeyError:
        raise KeyError(
            f"no described infix shape for {kind!r}; the described infix "
            f"kinds are {', '.join(INFIX_KINDS)}") from None


#: Every described shape, in the order a question is tried against them.
#: The order is fixed and is not a priority: the openings are disjoint, which
#: :mod:`glm_universal.language.report` checks, so at most one can match.
QUESTIONS: Tuple[QuestionSpec, ...] = (
    DERIVE_QUESTION, MEASURE_QUESTION, TASK_QUESTION,
    COMPARE_LIST_QUESTION,
)

#: The query kinds the descriptions cover.
DESCRIBED_KINDS: Tuple[str, ...] = tuple(spec.kind for spec in QUESTIONS)

_BY_KIND: Dict[str, QuestionSpec] = {spec.kind: spec for spec in QUESTIONS}


def question_by_kind(kind: str) -> QuestionSpec:
    """The description of one kind, or a :class:`KeyError` naming the rest."""
    try:
        return _BY_KIND[kind]
    except KeyError:
        raise KeyError(
            f"no described question shape for {kind!r}; the described kinds "
            f"are {', '.join(DESCRIBED_KINDS)}") from None


def described_kinds() -> Tuple[str, ...]:
    """The kinds a described question can produce."""
    return DESCRIBED_KINDS
