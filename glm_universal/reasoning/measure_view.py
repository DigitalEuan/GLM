"""``glm_universal.reasoning.measure_view`` -- a measure word as a measurement.

What this module is
-------------------
``hot`` is, in :mod:`~glm_universal.data_objects.semantic_lexicon`, a concept:
ten primitives, a part of speech, and four relations, one of which is
``property_of temperature``.  That reading is *static*.  It says which quantity
the word is about and, through ``positive_negative``, which pole of it the word
names; it cannot say **how hot**, and no amount of resolution in the carrier
would let it, because *hot* is not a temperature.  What is missing is the
**comparison class**: hot for a cup of tea is 363 K, hot for a star is 44 000 K,
and the same word is being measured against two different brackets.

:mod:`~glm_universal.data_objects.comparison_classes` supplies the classes and
the scales.  This module is what reads them, and it does so in the shape the
layer work settled on:

>   the relative reading is a **widening** of the static one, never a
>   replacement for it.

So a *use* -- a word together with a comparison class -- is seen by two layers.
The **static** layer sees exactly what the lexicon concept carries today.  The
**measure** layer sees that *and* the quantity, the class and the exact
magnitude the pair names.  Being cumulative, the measure layer cannot lose
anything the static layer had; the audit below measures what it gains, and
``RequestProject/GLM/MeasureView.lean`` proves the parts that are not
measurements -- that the widening refines the static reading, that it is the
coarsest layer that does, that its gain is exactly what the new reading sees,
and that where the new reading is undefined the widening gains nothing at all,
which is why the runtime must *refuse* rather than answer there.

The three things it computes
----------------------------
``measure_words``
    Which lexicon adjectives have a measure reading at all, and why the rest
    do not.  All twelve now have one: ``large`` and ``small`` are
    ``property_of size`` and ``dark`` is ``property_of light``, and the
    comparison-class register reaches both through the physics register's
    ``volume`` and ``illuminance`` -- two of the seven entries of
    ``comparison_classes.QUANTITY_ALIASES``, which resolve a name and supply
    no coordinate.  The query still refuses where a *class* is of another
    quantity than the word (``measure large in room``: *room* brackets a
    length), and :func:`replacement_witness` keeps the cost of the rejected
    reading measurable now that the shipped data no longer exhibits it.
``widening_audit``
    The static and measure layers, over every use the registers admit:
    resolution, what each boundary gains, and whether the step is a
    refinement.  Same definitions as
    :mod:`~glm_universal.reasoning.information_loss`, and
    :func:`static_agrees_with_rational_layer` checks that the static reading
    used here really is the machine's own rational layer on the concept
    carrier rather than a convenient idealisation of it.
``relation_repair``
    ``related_to`` is the lexicon's residue: 66 of its 380 triples record that
    a link exists without saying which, and the analogy layer refuses to
    transport them.  This converts the ones the physics register can *decide*
    -- same dimension, or differing by the dimension of exactly one quantity
    of a fixed factor basis -- and reports the rest as residue with the reason
    each was declined.  Nothing is converted on a guess.

Exactness
---------
Every magnitude is an ``int`` or a :class:`fractions.Fraction`.  No float is
constructed anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import (Callable, Dict, Hashable, List, Optional, Sequence, Tuple)

from ..derived import memo
from ..data_objects import comparison_classes as cc
from ..data_objects import physics as ph
from ..data_objects import semantic_lexicon as sl
from . import dimension_layers as DL
from . import information_loss as IL

__all__ = [
    "FACTOR_BASIS", "MEASURE_RELATIONS",
    "MeasureBoundary", "MeasureWord", "Use", "Reading",
    "measure_words", "word_by_name", "scaled_words", "unscaled_words",
    "lexicon_quantity",
    "read", "classify", "above_on", "compare_words", "measure_relations",
    "Comparison", "compare_uses", "degree_words", "comparative_stem",
    "comparative_direction", "answer_comparative", "comparative_audit",
    "uses", "static_view", "measure_view",
    "static_agrees_with_rational_layer",
    "widening_audit", "replacement_witness", "relation_repair",
    "basis_dimension_audit", "basis_sweep", "repaired_triples",
    "transport_audit",
    "measure_report",
]


#: The quantities a dimensional difference may be attributed to.  Deliberately
#: small: the seven SI base quantities the register names, plus the derived
#: ones a first course would use.  An ambiguous attribution -- two members of
#: the basis both carrying one dimension to the other -- is declined rather
#: than guessed, so the basis may hold at most one name per dimension, and
#: :func:`basis_dimension_audit` checks that it does.
#:
#: The last three entries were added on the strength of :func:`basis_sweep`,
#: which offers **every** quantity the physics register holds as a candidate
#: and measures what each one would do.  Until that sweep was run this comment
#: claimed that a wider basis converts nothing and only adds ambiguity; the
#: measurement says otherwise, and precisely.  Of the 713 candidates, 571
#: change nothing and 125 would make some attribution ambiguous and are
#: refused; the 17 that strictly convert more occupy only **four dimensions**
#: -- the ohm, its reciprocal the siemens, the joule per kelvin and the radian
#: per metre -- and the first two decide the same triple, since the search
#: already tries a factor in both directions.  So the data decides three
#: factors.  A dimension is what it decides; the *name* is not, since eight
#: register entries carry the ohm and five the joule per kelvin.  The names
#: below are the ones a first course would use, and ``basis_sweep`` reports
#: the whole class beside each so the choice of spelling stays visible as a
#: choice.
FACTOR_BASIS: Tuple[str, ...] = (
    "length", "mass", "time", "current", "temperature", "luminous_intensity",
    "area", "volume", "velocity", "acceleration", "frequency", "charge",
    "energy",
    "resistance", "entropy", "angular_wavenumber",
)

#: The three the sweep added, kept separately so :func:`basis_sweep` can put
#: the basis back the way it was and measure the growth rather than assert it.
_GROWN_BASIS: Tuple[str, ...] = ("resistance", "entropy",
                                 "angular_wavenumber")

#: The relation family a measure reading generates.  These are *derived*
#: triples: they are not stored in the lexicon, and they could not be -- the
#: concepts already use all four of their relation slots, which is the
#: constraint that forced the widening in the first place.
MEASURE_RELATIONS: Tuple[str, ...] = (
    "measures",               # word -> the quantity it measures
    "measures_relative_to",   # word -> a comparison class
    "above_on",               # word -> a word lower on the same scale
    "opposite_pole",          # word -> the word at 1 - its position
)


class MeasureBoundary(Exception):
    """Raised where the machine has a word but no measurement for it.

    Carries the reason, so a caller can refuse with the reason rather than
    with a shrug.  Every raise site here is a *boundary*: a place where the
    registers hold no coordinate, not a place where the code fell short.
    """

    def __init__(self, message: str, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


# ===========================================================================
# 1.  WHICH WORDS HAVE A MEASURE READING
# ===========================================================================

@dataclass(frozen=True)
class MeasureWord:
    """A lexicon adjective, with the measure reading it does or does not have.

    ``quantity`` is what the concept's own ``property_of`` relation names, and
    is never invented here.  ``position`` is the word's place on its
    quantity's scale, and ``status`` says which of the three cases the word is
    in: ``\"scaled\"`` (a quantity in the physics register, a scale, and at
    least one class), ``\"unregistered_quantity\"`` (the lexicon names a
    quantity the physics register does not hold) or ``\"unscaled\"`` (a
    registered quantity with no scale or no class).
    """

    word: str
    quantity: Optional[str]
    position: Optional[Fraction]
    status: str
    reason: str = ""

    @property
    def scaled(self) -> bool:
        return self.status == "scaled"


def _concepts() -> Dict[str, sl.SemanticConcept]:
    return {c.subject: c for c in sl.SEMANTIC_SAMPLE_CONCEPTS}


def _named_quantity(concept: sl.SemanticConcept) -> Optional[str]:
    """What the concept's ``property_of`` relation names, if anything.

    Returned under the physics register's own name for the quantity: the
    lexicon says *size* and *light*, the register says ``volume`` and
    ``illuminance``, and ``comparison_classes.QUANTITY_ALIASES`` is the
    resolution between the two names.  Nothing is invented by that step --
    an alias whose target the register does not hold fails
    ``comparison_classes.alias_audit``.
    """
    for predicate, other in concept.relations:
        if predicate == "property_of":
            return cc.resolve_quantity(other)
    return None


def lexicon_quantity(word: str) -> Optional[str]:
    """The quantity name the *lexicon itself* uses, before any alias.

    ``lexicon_quantity('large')`` is ``'size'`` where
    :func:`_named_quantity` reports the register's ``'volume'``.  The runtime
    quotes both, so that an answer never claims the lexicon says something it
    does not.
    """
    for concept in sl.SEMANTIC_SAMPLE_CONCEPTS:
        if concept.subject != word:
            continue
        for predicate, other in concept.relations:
            if predicate == "property_of":
                return other
    return None


def _in_physics(name: str) -> bool:
    try:
        ph.quantity_by_name(name)
    except KeyError:
        return False
    return True


def measure_words() -> Tuple[MeasureWord, ...]:
    """Every lexicon adjective, classified by whether it can be measured.

    Derived from the two registers on every call: nothing here is a list of
    words typed out beside the lexicon.
    """
    out: List[MeasureWord] = []
    for concept in sl.SEMANTIC_SAMPLE_CONCEPTS:
        if concept.pos != "adjective":
            continue
        quantity = _named_quantity(concept)
        if quantity is None:
            out.append(MeasureWord(concept.subject, None, None, "unscaled",
                                   "the concept names no quantity"))
            continue
        if not _in_physics(quantity):
            out.append(MeasureWord(
                concept.subject, quantity, None, "unregistered_quantity",
                f"the physics register holds no quantity called "
                f"{quantity!r}"))
            continue
        scale = cc.scale_for_quantity(quantity)
        classes = cc.classes_for_quantity(quantity)
        if scale is None or not classes:
            out.append(MeasureWord(
                concept.subject, quantity, None, "unscaled",
                f"{quantity} has no measure scale or no comparison class"))
            continue
        try:
            position = scale.position_of(concept.subject)
        except KeyError:
            out.append(MeasureWord(
                concept.subject, quantity, None, "unscaled",
                f"{concept.subject} is not a degree word on the {quantity} "
                f"scale"))
            continue
        out.append(MeasureWord(concept.subject, quantity, position, "scaled"))
    return tuple(out)


def word_by_name(word: str) -> MeasureWord:
    """One measure word, by name.

    A word that is on a scale without being a lexicon concept -- ``warm``,
    ``scalding`` -- is returned too: the scale is the vocabulary of the
    measure view, and the lexicon is only where some of its words also have a
    static reading.
    """
    for entry in measure_words():
        if entry.word == word:
            return entry
    found = cc.degree_word(word)
    if found is not None:
        quantity, position = found
        if cc.classes_for_quantity(quantity):
            return MeasureWord(word, quantity, position, "scaled")
        return MeasureWord(word, quantity, position, "unscaled",
                           f"{quantity} has no comparison class")
    raise MeasureBoundary(
        f"{word!r} is neither a lexicon adjective nor a word on any measure "
        f"scale, so there is nothing to measure it with",
        reason="no such measure word")


def scaled_words() -> Tuple[MeasureWord, ...]:
    """The lexicon adjectives that do have a measure reading."""
    return tuple(w for w in measure_words() if w.scaled)


def unscaled_words() -> Tuple[MeasureWord, ...]:
    """The lexicon adjectives that do not, each with its reason."""
    return tuple(w for w in measure_words() if not w.scaled)


# ===========================================================================
# 2.  READING A WORD AGAINST A CLASS
# ===========================================================================

@dataclass(frozen=True)
class Reading:
    """What a word and a comparison class together name: a magnitude."""

    word: str
    quantity: str
    comparison_class: str
    position: Fraction
    magnitude: Fraction
    unit: str
    dimension: str
    low: Fraction
    high: Fraction

    def as_dict(self) -> Dict[str, object]:
        return {
            "word": self.word,
            "quantity": self.quantity,
            "comparison_class": self.comparison_class,
            "position": self.position,
            "magnitude": self.magnitude,
            "unit": self.unit,
            "dimension": self.dimension,
            "low": self.low,
            "high": self.high,
        }


def read(word: str, comparison_class: str) -> Reading:
    """*How hot is hot, for a cup of tea?*  -- as an exact magnitude.

    Raises :class:`MeasureBoundary`, with the reason, when the word has no
    measure reading, when the class is not in the register, or when the two
    are about different quantities.  None of those is a failure of the
    computation: each is a place the registers do not reach.
    """
    entry = word_by_name(word)
    if not entry.scaled:
        raise MeasureBoundary(
            f"{word!r} has no measure reading: {entry.reason}",
            reason=entry.status)
    try:
        klass = cc.class_by_name(comparison_class)
    except KeyError:
        raise MeasureBoundary(
            f"{comparison_class!r} is not a comparison class the register "
            f"holds; the classes for {entry.quantity} are "
            f"{[c.name for c in cc.classes_for_quantity(str(entry.quantity))]}",
            reason="no such comparison class") from None
    if klass.quantity != entry.quantity:
        raise MeasureBoundary(
            f"{word!r} measures {entry.quantity} and {comparison_class!r} is "
            f"a class of {klass.quantity}; a word cannot be measured against "
            f"a class of another quantity",
            reason="quantity mismatch")
    position = Fraction(entry.position)   # scaled implies a position
    return Reading(
        word=word, quantity=klass.quantity, comparison_class=klass.name,
        position=position, magnitude=klass.magnitude_at(position),
        unit=klass.unit,
        dimension=ph.dimension_string(klass.exps_ext10),
        low=klass.low, high=klass.high)


def classify(magnitude: Fraction, comparison_class: str) -> Dict[str, object]:
    """*Is 300 K hot, for a cup of tea?*  -- the other direction.

    Returns the exact position the magnitude occupies in the class, the scale
    word nearest that position, and whether the magnitude is inside the
    class's bracket at all.  A magnitude outside the bracket is reported as
    outside rather than clamped: the class is a claim about ordinary cases,
    and a value beyond it is a case the class does not cover.
    """
    klass = cc.class_by_name(comparison_class)
    scale = cc.scale_for_quantity(klass.quantity)
    if scale is None:
        raise MeasureBoundary(
            f"{klass.quantity} has no measure scale, so a magnitude in "
            f"{comparison_class!r} cannot be given a word",
            reason="unscaled")
    magnitude = Fraction(magnitude)
    position = klass.position_of(magnitude)
    inside = klass.contains(magnitude)
    clamped = min(max(position, Fraction(0)), Fraction(1))
    word = scale.nearest_word(clamped)
    return {
        "magnitude": magnitude,
        "comparison_class": klass.name,
        "quantity": klass.quantity,
        "unit": klass.unit,
        "position": position,
        "inside_bracket": inside,
        "word": word,
        "word_position": scale.position_of(word),
        "above": scale.above(word),
        "bracket": (klass.low, klass.high),
    }


def above_on(word: str) -> Tuple[str, ...]:
    """The words strictly above ``word`` on its own scale, lowest first."""
    entry = word_by_name(word)
    if entry.quantity is None:
        return ()
    scale = cc.scale_for_quantity(entry.quantity)
    return () if scale is None else scale.above(word)


def compare_words(left: str, right: str) -> Dict[str, object]:
    """Order two words -- and refuse when they are not on the same scale.

    Two words of *different* quantities are not comparable at all, and saying
    so is the answer.  Two words of the same quantity are ordered by position,
    which is a comparison of exact rationals.
    """
    a, b = word_by_name(left), word_by_name(right)
    if a.quantity != b.quantity or a.quantity is None:
        raise MeasureBoundary(
            f"{left!r} measures {a.quantity} and {right!r} measures "
            f"{b.quantity}; words on different scales are not ordered",
            reason="different quantities")
    if a.position is None or b.position is None:
        raise MeasureBoundary(
            f"one of {left!r}, {right!r} has no position on the "
            f"{a.quantity} scale",
            reason="unscaled")
    order = (a.position > b.position) - (a.position < b.position)
    return {"left": left, "right": right, "quantity": a.quantity,
            "left_position": a.position, "right_position": b.position,
            "order": order,
            "verdict": f"{left} = {right}" if order == 0 else
                       (f"{left} above {right}" if order > 0
                        else f"{left} below {right}")}


def measure_relations(word: str) -> Tuple[Tuple[str, str], ...]:
    """The derived relation family for one word: the widening, as triples.

    ``measures`` and ``opposite_pole`` are single; ``measures_relative_to``
    and ``above_on`` are one triple per class and per lower word.  None of
    these is stored: the lexicon's four relation slots are already full, which
    is exactly why the measure reading has to be a view of its own.
    """
    entry = word_by_name(word)
    if not entry.scaled or entry.quantity is None:
        return ()
    quantity = entry.quantity
    scale = cc.scale_for_quantity(quantity)
    assert scale is not None
    out: List[Tuple[str, str]] = [("measures", quantity)]
    for klass in cc.classes_for_quantity(quantity):
        out.append(("measures_relative_to", klass.name))
    position = Fraction(entry.position)
    for other in scale.words:
        if other.position < position:
            out.append(("above_on", other.word))
    for other in scale.words:
        if other.position == 1 - position and other.word != word:
            out.append(("opposite_pole", other.word))
    return tuple(out)


# ===========================================================================
# 3.  THE WIDENING, AUDITED
# ===========================================================================

@dataclass(frozen=True)
class Use:
    """One *use* of a measure word: the word, measured against a class.

    ``comparison_class`` is empty for a word the registers cannot measure at
    all.  The shipped registers now measure every lexicon adjective, so no
    such use arises from :func:`uses` any more; :func:`replacement_witness`
    constructs them deliberately, because they are where the new
    reading is undefined, and they are what distinguishes widening the view
    from replacing it.
    """

    word: str
    comparison_class: str

    @property
    def measured(self) -> bool:
        return bool(self.comparison_class)

    @property
    def name(self) -> str:
        return f"{self.word}@{self.comparison_class or '-'}"


def uses(words: Optional[Sequence[str]] = None,
         include_unmeasured: bool = True) -> Tuple[Use, ...]:
    """Every use the registers admit: each scaled word against each class.

    Drawn by default from the lexicon adjectives, because the audit compares
    the widening *against* the static reading and a word with no concept has
    nothing to compare.  The adjectives with no measure reading are included
    once each, with no class, unless ``include_unmeasured`` says otherwise.
    """
    if words is None:
        words = [w.word for w in measure_words()]
    out: List[Use] = []
    for word in words:
        entry = word_by_name(word)
        if not entry.scaled or entry.quantity is None:
            if include_unmeasured:
                out.append(Use(word, ""))
            continue
        for klass in cc.classes_for_quantity(entry.quantity):
            out.append(Use(word, klass.name))
    return tuple(out)


def _concept_carrier(word: str) -> Tuple[Fraction, ...]:
    """The 24-coordinate carrier the semantic lexicon gives the word."""
    objects, _codec = sl.semantic_lexicon_objects()
    for obj in objects:
        if obj.name == word:
            return tuple(Fraction(x) for x in obj.carrier)
    raise KeyError(f"{word} is not a semantic lexicon concept")


def static_view(use: Use) -> Hashable:
    """What the machine sees of a use **today**: the concept, and no more.

    Two uses of the same word are the same thing to this view, whatever they
    are measured against -- which is the whole of the complaint that ``hot``
    is a standalone concept.
    """
    return _concept_carrier(use.word)


def _measurement(use: Use) -> Optional[Tuple[str, str, Fraction]]:
    """The new reading of a use, or ``None`` where there is not one."""
    if not use.measured:
        return None
    reading = read(use.word, use.comparison_class)
    return (reading.quantity, reading.comparison_class, reading.magnitude)


def measure_view(use: Use) -> Hashable:
    """The widened view: the static reading, and the measurement beside it.

    A pair, exactly as ``GLM.Info.Layer.cumulative`` is a pair: the second
    component is the new reading and the first is everything that was there
    before, so nothing the static view could say is given up.
    """
    return (_concept_carrier(use.word), _measurement(use))


def measure_only_view(use: Use) -> Hashable:
    """The new reading alone -- the *non-cumulative* alternative.

    Kept, and measured, for the same reason ``LAYER_INTEGER_RAW`` is kept in
    the layer stack: it is the reading the design rejected, and the cost of
    rejecting it should be a number rather than an assertion.  Here the cost
    is the words it cannot measure: they all read ``None``, so a view that
    keeps only the measurement conflates words the lexicon told apart.
    """
    return _measurement(use)


_VIEWS: Dict[str, Callable[[Use], Hashable]] = {
    "static": static_view,
    "measure": measure_view,
    "measure_only": measure_only_view,
}


def _classes(view: str, entries: Sequence[Use]) -> Tuple[Tuple[int, ...], ...]:
    """Partition uses into what one view can tell apart.  Same shape as
    :func:`information_loss.classes`, keyed rather than pairwise."""
    seen: Dict[Hashable, List[int]] = {}
    order: List[Hashable] = []
    fn = _VIEWS[view]
    for i, entry in enumerate(entries):
        key = fn(entry)
        if key not in seen:
            seen[key] = []
            order.append(key)
        seen[key].append(i)
    return tuple(tuple(seen[k]) for k in order)


def _resolution(view: str, entries: Sequence[Use]) -> int:
    return len(_classes(view, entries))


def _pairs(view: str, entries: Sequence[Use]) -> set:
    """The index pairs this view conflates."""
    out = set()
    for group in _classes(view, entries):
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                out.add((group[i], group[j]))
    return out


def _boundary(lower: str, higher: str,
              entries: Sequence[Use]) -> Dict[str, object]:
    """What the step from ``lower`` to ``higher`` gains, and whether it loses.

    ``gained`` counts the pairs the lower view conflates and the higher view
    splits; ``violations`` counts the pairs the *higher* view conflates that
    the lower one already split, which is exactly the failure the layer chain
    was repaired for, and must be zero for a widening.
    """
    low = _pairs(lower, entries)
    high = _pairs(higher, entries)
    gained = sorted(low - high)
    violations = sorted(high - low)
    return {
        "lower": lower, "higher": higher,
        "gained": len(gained),
        "violations": len(violations),
        "refines": not violations,
        "example_gain": [entries[i].name for i in gained[0]] if gained
        else None,
        "example_violation": [entries[i].name for i in violations[0]]
        if violations else None,
    }


def static_agrees_with_rational_layer(
        entries: Optional[Sequence[Use]] = None) -> Dict[str, object]:
    """The static view here *is* the machine's rational layer -- checked.

    The audit's claim to be about the real static reading rests on the static
    view being the concept carrier and nothing else.  This re-derives every
    verdict from ``dimension_layers.LAYER_RATIONAL`` -- the layer whose view
    is the exact carrier -- through ``information_loss.indistinguishable``,
    and reports a disagreement rather than assuming there is none.
    """
    if entries is None:
        entries = uses()
    checked = 0
    disagreements: List[Dict[str, object]] = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            by_view = static_view(entries[i]) == static_view(entries[j])
            by_layer = IL.indistinguishable(
                DL.LAYER_RATIONAL,
                _concept_carrier(entries[i].word),
                _concept_carrier(entries[j].word))
            checked += 1
            if by_view != by_layer:
                disagreements.append({"a": entries[i].name,
                                      "b": entries[j].name,
                                      "by_view": by_view,
                                      "by_layer": by_layer})
    return {"pairs_checked": checked, "agrees": not disagreements,
            "disagreements": disagreements}


def widening_audit(entries: Optional[Sequence[Use]] = None
                   ) -> Dict[str, object]:
    """The static and measure views, measured over every use.

    Every number here is computed from the registers.  The three findings the
    write-up quotes are ``resolution`` (how many of the uses each view tells
    apart), ``boundary`` (what the widening gains, and that it loses nothing)
    and ``non_cumulative`` (what the rejected replacement reading would cost).
    """
    if entries is None:
        entries = uses()
    static_classes = _classes("static", entries)
    largest = max((len(c) for c in static_classes), default=0)
    boundary = _boundary("static", "measure", entries)
    replacement = _boundary("static", "measure_only", entries)
    magnitudes: Dict[object, List[str]] = {}
    for entry in entries:
        measurement = _measurement(entry)
        if measurement is None:
            continue
        magnitudes.setdefault(
            (measurement[0], measurement[2]), []).append(entry.name)
    collisions = {k: v for k, v in magnitudes.items() if len(v) > 1}
    return {
        "uses": len(entries),
        "measured_uses": len([e for e in entries if e.measured]),
        "unmeasured_words": [e.word for e in entries if not e.measured],
        "words": len({e.word for e in entries}),
        "classes": len({e.comparison_class for e in entries if e.measured}),
        "views": [
            {"name": "static",
             "resolution": _resolution("static", entries),
             "loss": len(entries) - _resolution("static", entries),
             "largest_class": largest,
             "sees": "the concept carrier: ten primitives, the part of "
                     "speech, four relation slots"},
            {"name": "measure",
             "resolution": _resolution("measure", entries),
             "loss": len(entries) - _resolution("measure", entries),
             "largest_class": max(
                 (len(c) for c in _classes("measure", entries)), default=0),
             "sees": "the concept carrier, and beside it the quantity, the "
                     "comparison class and the exact magnitude"},
            {"name": "measure_only",
             "resolution": _resolution("measure_only", entries),
             "loss": len(entries) - _resolution("measure_only", entries),
             "largest_class": max(
                 (len(c) for c in _classes("measure_only", entries)),
                 default=0),
             "sees": "the measurement alone -- the reading the design "
                     "rejected, kept so its cost is a number"},
        ],
        "boundary": boundary,
        "non_cumulative": replacement,
        "magnitude_collisions": {
            "count": len(collisions),
            "examples": [v for v in list(collisions.values())[:3]],
        },
        "static_agreement": static_agrees_with_rational_layer(entries),
    }


def replacement_witness() -> Dict[str, object]:
    """What the rejected replacement reading costs, kept as a number.

    The reading that keeps only the measurement and drops the concept used to
    be refuted by the shipped data itself: ``large``, ``small`` and ``dark``
    had no measurement, all three read ``None``, and the replacement
    conflated three pairs the lexicon told apart.  Supplying the *size* and
    *light* comparison classes removed those three uses, so
    :func:`widening_audit` now reports **zero** violations -- not because the
    replacement became sound, but because the register no longer holds a word
    it fails on.

    The failure is a property of the reading rather than of the data, and
    ``GLM.Info.measureReading_not_refines_staticLayer`` proves it in general.
    This function keeps it measurable here too: the audit is re-run over the
    uses the registers admit **plus one unmeasured use of each word**, which
    is exactly the case that arises the moment a word's quantity is not yet
    in a register -- where all three of ``large``, ``small`` and ``dark``
    stood before this round.
    """
    words = [w.word for w in measure_words()]
    entries = tuple(uses(include_unmeasured=False)) + tuple(
        Use(word, "") for word in words)
    audit = widening_audit(entries)
    return {
        "uses": audit["uses"],
        "unmeasured_uses": len(words),
        "widening": audit["boundary"],
        "replacement": audit["non_cumulative"],
        "shipped_violations": widening_audit()["non_cumulative"][
            "violations"],
    }


# ===========================================================================
# 4.  THE ``related_to`` RESIDUE, CONVERTED WHERE IT CAN BE DECIDED
# ===========================================================================

def _dimension_of(name: str) -> Optional[Tuple[Fraction, ...]]:
    """The EXT10 exponents a lexicon name reaches, directly or by ``property_of``."""
    try:
        return ph.quantity_by_name(cc.resolve_quantity(name)).exps_ext10
    except KeyError:
        pass
    for concept in sl.SEMANTIC_SAMPLE_CONCEPTS:
        if concept.subject != name:
            continue
        named = _named_quantity(concept)
        if named is None:
            return None
        try:
            return ph.quantity_by_name(named).exps_ext10
        except KeyError:
            return None
    return None


def _factor_between(source: Tuple[Fraction, ...],
                    target: Tuple[Fraction, ...],
                    basis: Sequence[str] = FACTOR_BASIS
                    ) -> Tuple[Tuple[str, str], ...]:
    """Which single basis quantities carry ``source`` to ``target``."""
    hits: List[Tuple[str, str]] = []
    for name in basis:
        try:
            factor = ph.quantity_by_name(name).exps_ext10
        except KeyError:      # pragma: no cover -- basis is checked by a test
            continue
        if tuple(a + b for a, b in zip(source, factor)) == target:
            hits.append((name, "times"))
        if tuple(a - b for a, b in zip(source, factor)) == target:
            hits.append((name, "over"))
    return tuple(hits)


def _quantity_dimension(name: str) -> Optional[Tuple[Fraction, ...]]:
    try:
        return ph.quantity_by_name(name).exps_ext10
    except KeyError:                # pragma: no cover -- basis is audited
        return None


def basis_dimension_audit() -> Dict[str, object]:
    """The basis holds at most one name per dimension, and every name exists.

    Two basis members of the same dimension would make *every* attribution
    they decide ambiguous, so the rule is structural rather than a
    convenience.  Reported as a measurement because the basis grew, and a rule
    that is only stated is a rule that quietly stops holding.
    """
    unregistered: List[str] = []
    by_dimension: Dict[Tuple[Fraction, ...], List[str]] = {}
    for name in FACTOR_BASIS:
        exps = _quantity_dimension(name)
        if exps is None:
            unregistered.append(name)
            continue
        by_dimension.setdefault(exps, []).append(name)
    collisions = {ph.dimension_string(k): v
                  for k, v in by_dimension.items() if len(v) > 1}
    return {
        "size": len(FACTOR_BASIS),
        "dimensions": len(by_dimension),
        "unregistered": unregistered,
        "collisions": collisions,
        "sound": not (unregistered or collisions),
    }


def _repair_pairs() -> Tuple[Tuple[str, str], ...]:
    """The ``related_to`` endpoints, in register order."""
    out: List[Tuple[str, str]] = []
    for concept in sl.SEMANTIC_SAMPLE_CONCEPTS:
        for predicate, other in concept.relations:
            if predicate == "related_to":
                out.append((concept.subject, other))
    return tuple(out)


@memo
def _repair_dims() -> Tuple[Tuple[Optional[Tuple[Fraction, ...]],
                                  Optional[Tuple[Fraction, ...]]], ...]:
    """The endpoints' dimensions, once, so the sweep is not quadratic in them."""
    return tuple((_dimension_of(s), _dimension_of(o))
                 for s, o in _repair_pairs())


def _repair_counts(basis: Sequence[str]) -> Tuple[int, int, int, int]:
    """``(converted, ambiguous, no_factor, no_dimension)`` under one basis."""
    converted = ambiguous = no_factor = no_dimension = 0
    for source, target in _repair_dims():
        if source is None or target is None:
            no_dimension += 1
            continue
        if source == target:
            converted += 1
            continue
        hits = _factor_between(source, target, basis)
        if len(hits) == 1:
            converted += 1
        elif not hits:
            no_factor += 1
        else:
            ambiguous += 1
    return converted, ambiguous, no_factor, no_dimension


@memo
def basis_sweep() -> Dict[str, object]:
    """Every registered quantity offered as a factor, and what it would do.

    The basis is a *choice*, and this measures it rather than defending it.
    Each quantity the physics register holds and the basis does not is added
    to the shipped basis on its own, the repair is re-run, and the candidate
    is filed as

    ``converts``
        it decides at least one triple more and makes none ambiguous;
    ``ambiguates``
        it makes at least one attribution ambiguous, so it is refused;
    ``inert``
        the counts do not move.

    The converting candidates are grouped by *dimension*, because that is what
    the data decides.  Which of the eight register names for the ohm is
    written into :data:`FACTOR_BASIS` is not decided by anything here, and the
    grouping is what makes that visible.
    """
    shipped = tuple(FACTOR_BASIS)
    base = _repair_counts(shipped)
    converts: List[Dict[str, object]] = []
    ambiguates: List[str] = []
    inert = 0
    groups: Dict[Tuple[Fraction, ...], List[str]] = {}
    gains: Dict[Tuple[Fraction, ...], int] = {}
    without = tuple(n for n in shipped if n not in _GROWN_BASIS)
    trimmed = _repair_counts(without)
    for quantity in ph.load_physics_register():
        if quantity.name in without:
            continue
        row = _repair_counts(without + (quantity.name,))
        if row[1] > trimmed[1]:
            ambiguates.append(quantity.name)
        elif row[0] > trimmed[0]:
            groups.setdefault(quantity.exps_ext10, []).append(quantity.name)
            gains[quantity.exps_ext10] = row[0] - trimmed[0]
            converts.append({"name": quantity.name,
                             "dimension": ph.dimension_string(
                                 quantity.exps_ext10),
                             "converts": row[0] - trimmed[0]})
        else:
            inert += 1
    classes = [{"dimension": ph.dimension_string(exps),
                "gain": gains[exps],
                "names": sorted(names),
                "shipped": sorted(set(names) & set(_GROWN_BASIS))}
               for exps, names in groups.items()]
    classes.sort(key=lambda row: str(row["dimension"]))
    return {
        "basis": list(shipped),
        "basis_size": len(shipped),
        "basis_dimensions": basis_dimension_audit()["dimensions"],
        "basis_sound": basis_dimension_audit()["sound"],
        "grown_by": list(_GROWN_BASIS),
        "candidates": len(ph.load_physics_register()) - len(without),
        "converts": len(converts),
        "ambiguates": len(ambiguates),
        "inert": inert,
        "converting_classes": classes,
        "shipped_counts": {"converted": base[0], "ambiguous": base[1],
                           "no_factor": base[2],
                           "no_dimension": base[3]},
        "trimmed_counts": {"converted": trimmed[0], "ambiguous": trimmed[1],
                           "no_factor": trimmed[2],
                           "no_dimension": trimmed[3]},
        "ambiguating_examples": sorted(ambiguates)[:5],
    }


def relation_repair() -> Dict[str, object]:
    """Convert the ``related_to`` triples the physics register can decide.

    Two rules, both decisions rather than judgements:

    ``same_dimension_as``
        the two endpoints reach the same EXT10 exponent vector;
    ``differs_by``
        exactly one quantity of :data:`FACTOR_BASIS` carries one exponent
        vector to the other, and the triple records which and in which
        direction -- ``energy = force times length``, ``density = mass over
        volume``.

    Everything else stays ``related_to`` and is reported with the reason it
    was declined.  A triple whose subject or object reaches no dimension is
    not a candidate at all, and an ambiguous attribution is refused: the point
    of the exercise is to remove guesses from the register, not to add better
    ones.
    """
    converted: List[Dict[str, object]] = []
    residue: List[Dict[str, str]] = []
    total_triples = 0
    for concept in sl.SEMANTIC_SAMPLE_CONCEPTS:
        for predicate, other in concept.relations:
            total_triples += 1
            if predicate != "related_to":
                continue
            source = _dimension_of(concept.subject)
            target = _dimension_of(other)
            if source is None or target is None:
                missing = (concept.subject if source is None else other)
                residue.append({
                    "subject": concept.subject, "object": other,
                    "kind": "not_a_quantity",
                    "endpoint": missing,
                    "pos": _part_of_speech(missing),
                    "reason": f"{missing} reaches no dimension the physics "
                              f"register holds"})
                continue
            if source == target:
                converted.append({
                    "subject": concept.subject, "object": other,
                    "predicate": "same_dimension_as",
                    "dimension": ph.dimension_string(source),
                    "triple": (concept.subject, "same_dimension_as", other),
                    "witness": None})
                continue
            hits = _factor_between(source, target)
            if len(hits) == 1:
                factor, direction = hits[0]
                converted.append({
                    "subject": concept.subject, "object": other,
                    "predicate": "differs_by",
                    "dimension": ph.dimension_string(source),
                    "triple": (concept.subject,
                               f"{direction}_{factor}", other),
                    "witness": f"{other} = {concept.subject} {direction} "
                               f"{factor}"})
            elif not hits:
                residue.append({
                    "subject": concept.subject, "object": other,
                    "kind": "no_single_factor",
                    "endpoint": "", "pos": "",
                    "reason": "no single quantity of the factor basis "
                              "carries one dimension to the other"})
            else:
                residue.append({
                    "subject": concept.subject, "object": other,
                    "kind": "ambiguous",
                    "endpoint": "", "pos": "",
                    "reason": f"the difference is attributable in "
                              f"{len(hits)} ways "
                              f"({', '.join(f for f, _ in hits)}), so it is "
                              f"not decided"})
    related = len(converted) + len(residue)
    by_predicate: Dict[str, int] = {}
    for row in converted:
        key = str(row["predicate"])
        by_predicate[key] = by_predicate.get(key, 0) + 1
    reasons: Dict[str, int] = {}
    for row in residue:
        reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
    by_kind: Dict[str, int] = {}
    for row in residue:
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
    by_pos: Dict[str, int] = {}
    for row in residue:
        if row["kind"] != "not_a_quantity":
            continue
        by_pos[row["pos"]] = by_pos.get(row["pos"], 0) + 1
    return {
        "triples": total_triples,
        "related_to": related,
        "converted": len(converted),
        "residue": len(residue),
        "by_predicate": by_predicate,
        "conversions": converted,
        "residue_reasons": reasons,
        "residue_by_kind": by_kind,
        "residue_by_pos": by_pos,
        "residue_rows": residue,
        "residue_examples": residue[:5],
        "factor_basis": list(FACTOR_BASIS),
        "basis_sound": basis_dimension_audit()["sound"],
    }


@memo
def repaired_triples() -> Tuple[Tuple[str, str, str], ...]:
    """The converted relations, as triples the analogy layer can transport.

    A ``differs_by`` conversion becomes ``times_<factor>`` or ``over_<factor>``
    rather than a bare ``differs_by``: two pairs differing by *different*
    factors do not stand in the same relation, and a transport that ignored
    the factor would be exactly the guess the repair exists to remove.
    """
    return tuple(tuple(row["triple"])            # type: ignore[misc]
                 for row in relation_repair()["conversions"])


def _part_of_speech(name: str) -> str:
    """The lexicon's own part of speech for a concept, or ``absent``.

    Read off the register entry, never supplied here: an endpoint the lexicon
    does not hold at all is a different kind of refusal from a verb it does.
    """
    for concept in sl.SEMANTIC_SAMPLE_CONCEPTS:
        if concept.subject == name:
            return concept.pos
    return "absent"


@memo
def transport_audit() -> Dict[str, object]:
    """What the analogy layer does with the repaired relations, before and after.

    A conversion is only worth having if the machine can *use* it, and the
    analogy layer is where that shows: ``A : B :: C : ?`` is answered when the
    register states a relation linking ``A`` and ``B`` and that relation
    reaches something from ``C``.  ``related_to`` is in
    ``analogy_models.VAGUE_RELATIONS`` and is never transported, so before the
    repair every one of these analogies was declined -- not wrongly, since
    "is related to" transports nothing.

    The audit builds every analogy the repaired triples themselves license:
    for each pair of distinct converted triples sharing a predicate, the four
    terms are put to :func:`analogy_models.explain_analogy` twice, once with
    the repair in scope and once with it suppressed.  The second run is the
    control, and it has to refuse everything.
    """
    from . import analogy_models as am
    from ..data_objects import semantic_lexicon as lex

    pool, _codec = lex.semantic_lexicon_objects()
    names = {obj.name for obj in pool}
    triples = repaired_triples()
    by_predicate: Dict[str, List[Tuple[str, str, str]]] = {}
    for subject, predicate, other in triples:
        by_predicate.setdefault(predicate, []).append(
            (subject, predicate, other))

    cases: List[Dict[str, object]] = []
    for predicate, group in sorted(by_predicate.items()):
        for i, (a, _, b) in enumerate(group):
            for j, (c, _, _d) in enumerate(group):
                if i == j or not {a, b, c} <= names:
                    continue
                result = am.explain_analogy("lexicon", a, b, c, pool)
                control = am.explain_analogy("lexicon", a, b, c, pool,
                                             repaired=False)
                cases.append({
                    "predicate": predicate,
                    "a": a, "b": b, "c": c,
                    "answer": None if result is None else result.answer,
                    "refusal": None if result is None else result.refusal,
                    "control_answer":
                        None if control is None else control.answer,
                })
    answered = [row for row in cases if row["answer"]]
    control_answered = [row for row in cases if row["control_answer"]]
    return {
        "triples": len(triples),
        "predicates": len(by_predicate),
        "transportable_predicates": sorted(
            p for p, g in by_predicate.items() if len(g) > 1),
        "cases": len(cases),
        "answered": len(answered),
        "refused": len(cases) - len(answered),
        "control_answered": len(control_answered),
        "examples": [{"query": f"{row['a']} : {row['b']} :: {row['c']} : ?",
                      "answer": row["answer"],
                      "predicate": row["predicate"]}
                     for row in answered[:6]],
    }


# ===========================================================================
# 5.  THE COMPARATIVE: *hotter than*, *as hot as*
# ===========================================================================
#
# A comparative is a relation between two **uses**, not between two words.
# ``above_on`` already orders the words of one scale and
# ``GLM.Info.above_on_magnitude_lt`` proves that order survives into
# magnitudes -- but only *within one class*.  Across classes the word order
# decides nothing: ``cold`` in ``stellar_surface`` is 8000 K and ``hot`` in
# ``tea`` is 363 K, so the lower word names the greater magnitude.
# ``GLM.Info.comparative_not_determined_by_word_order`` is that as a theorem,
# and :func:`comparative_audit` measures how often it happens over every pair
# of uses the registers admit.
#
# The direction a comparative asserts is read off the register rather than
# listed here: *hotter* is built from ``hot``, which sits above the midpoint
# of the temperature scale, so it asserts the greater magnitude, and *cooler*
# is built from ``cool``, which sits below it.  A word exactly at the midpoint
# names no direction and the query refuses rather than guessing one.


@dataclass(frozen=True)
class Comparison:
    """Two uses, compared as exact magnitudes.

    ``order`` is ``1`` when the left use names the greater magnitude, ``-1``
    when the right one does and ``0`` when they are equal -- the comparison of
    two :class:`fractions.Fraction`, and no float anywhere.
    """

    left: Reading
    right: Reading
    order: int
    difference: Fraction
    ratio: Optional[Fraction]

    @property
    def quantity(self) -> str:
        return self.left.quantity

    def as_dict(self) -> Dict[str, object]:
        return {
            "left": self.left.as_dict(),
            "right": self.right.as_dict(),
            "quantity": self.quantity,
            "order": self.order,
            "difference": self.difference,
            "ratio": self.ratio,
        }


def compare_uses(left_word: str, left_class: str,
                 right_word: str, right_class: str) -> Comparison:
    """*Is hot, for a cup of tea, hotter than cold, for a star?*

    Both sides are read exactly and then compared as rationals.  Raises
    :class:`MeasureBoundary` where either side has no reading, and where the
    two readings are of **different quantities**: a temperature and a velocity
    are both perfectly well measured and still not comparable, which is what
    ``GLM.Info.hotTea_not_comparable_fastWalking`` says.
    """
    left = read(left_word, left_class)
    right = read(right_word, right_class)
    if left.quantity != right.quantity:
        raise MeasureBoundary(
            f"{left_word!r} in {left_class!r} measures {left.quantity} and "
            f"{right_word!r} in {right_class!r} measures {right.quantity}; "
            f"magnitudes of different quantities are not comparable",
            reason="different quantities")
    order = ((left.magnitude > right.magnitude)
             - (left.magnitude < right.magnitude))
    ratio = (left.magnitude / right.magnitude) if right.magnitude else None
    return Comparison(left=left, right=right, order=order,
                      difference=left.magnitude - right.magnitude,
                      ratio=ratio)


def degree_words() -> Tuple[str, ...]:
    """Every degree word the register holds, over all its scales."""
    return tuple(sorted({w.word for scale in cc.MEASURE_SCALES.values()
                         for w in scale.words}))


def comparative_stem(form: str) -> Optional[str]:
    """The degree word a comparative form is built from -- ``hotter`` -> ``hot``.

    Four spellings are tried against the register: the word itself (which is
    the *equative* form, ``as hot as``), ``-er`` dropped (``faster``), ``-r``
    dropped (``larger``) and a doubled final consonant undone (``hotter``),
    with ``-ier`` -> ``-y`` beside them (``heavier``).  Nothing is invented:
    a candidate counts only if the register holds it as a degree word, and
    ``None`` comes back when none does.
    """
    form = form.strip().lower()
    known = set(degree_words())
    if form in known:
        return form
    candidates: List[str] = []
    if form.endswith("ier"):
        candidates.append(form[:-3] + "y")
    if form.endswith("er"):
        candidates.append(form[:-2])
        candidates.append(form[:-1])
        stem = form[:-2]
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            candidates.append(stem[:-1])
    found = [c for c in candidates if c in known]
    if not found:
        return None
    if len(set(found)) > 1:                # pragma: no cover -- register-guarded
        raise MeasureBoundary(
            f"{form!r} could be the comparative of {sorted(set(found))}; "
            f"the register does not decide which",
            reason="ambiguous comparative")
    return found[0]


def comparative_direction(word: str) -> str:
    """Which end of its scale a degree word points at: ``greater`` or ``less``.

    Read off the position, not from a list: a word above the midpoint of its
    scale asserts the greater magnitude and a word below it the smaller.  A
    word *at* the midpoint -- ``tepid``, ``middling`` -- names no direction,
    and this refuses rather than choosing one.
    """
    entry = word_by_name(word)
    if entry.position is None or entry.quantity is None:
        raise MeasureBoundary(
            f"{word!r} is on no measure scale, so it has no comparative",
            reason="unscaled")
    if entry.position > Fraction(1, 2):
        return "greater"
    if entry.position < Fraction(1, 2):
        return "less"
    raise MeasureBoundary(
        f"{word!r} sits exactly at the middle of the {entry.quantity} scale, "
        f"so {word!r}-er names no direction on it",
        reason="no direction")


def answer_comparative(form: str, left_word: str, left_class: str,
                       right_word: str, right_class: str,
                       equative: bool = False) -> Dict[str, object]:
    """Decide one comparative claim, exactly -- or refuse with the reason.

    ``form`` is the comparative as it was asked (``hotter``, ``cooler``) or,
    when ``equative`` is set, the bare degree word of an ``as hot as``
    question.  Three refusals are possible and all three are boundaries
    rather than failures: an unmeasurable use, two uses of different
    quantities, and a comparative whose own quantity is not the quantity being
    compared -- *hotter* asked of two velocities.
    """
    stem = comparative_stem(form)
    if stem is None:
        raise MeasureBoundary(
            f"{form!r} is not the comparative of any degree word the "
            f"register holds",
            reason="unknown comparative")
    entry = word_by_name(stem)
    if not entry.scaled or entry.quantity is None:
        raise MeasureBoundary(
            f"{stem!r} has no measure reading: {entry.reason}",
            reason=entry.status)
    comparison = compare_uses(left_word, left_class, right_word, right_class)
    if entry.quantity != comparison.quantity:
        raise MeasureBoundary(
            f"{form!r} is a {entry.quantity} comparative and the two uses "
            f"measure {comparison.quantity}; a scale word cannot order "
            f"magnitudes of another quantity",
            reason="comparative quantity mismatch")
    direction = "equal" if equative else comparative_direction(stem)
    if direction == "equal":
        holds = comparison.order == 0
        claim = f"{left_word} in {left_class} is as {stem} as " \
                f"{right_word} in {right_class}"
    elif direction == "greater":
        holds = comparison.order > 0
        claim = f"{left_word} in {left_class} is {form} than " \
                f"{right_word} in {right_class}"
    else:
        holds = comparison.order < 0
        claim = f"{left_word} in {left_class} is {form} than " \
                f"{right_word} in {right_class}"
    return {
        "form": form,
        "stem": stem,
        "equative": equative,
        "direction": direction,
        "claim": claim,
        "holds": holds,
        "quantity": comparison.quantity,
        "unit": comparison.left.unit,
        "order": comparison.order,
        "left_magnitude": comparison.left.magnitude,
        "right_magnitude": comparison.right.magnitude,
        "difference": comparison.difference,
        "ratio": comparison.ratio,
        "left_position": comparison.left.position,
        "right_position": comparison.right.position,
        "same_class": left_class == right_class,
        "word_order": ((comparison.left.position > comparison.right.position)
                       - (comparison.left.position
                          < comparison.right.position)),
        "comparison": comparison,
    }


@memo
def comparative_audit() -> Dict[str, object]:
    """How far the word order decides the comparative -- measured, not asserted.

    Over every ordered pair of measured uses of one quantity: the pair is
    *decided by the words* when the order of the two positions is the order of
    the two magnitudes.  Within a class that is always so, and the Lean file
    proves it (``GLM.Info.hotterThan_iff_position_lt``); across classes it
    fails often, and every failure is a question no reading of the two
    concepts alone could answer.
    """
    measured = [u for u in uses() if u.measured]
    readings = {u.name: read(u.word, u.comparison_class) for u in measured}
    same_class = {"pairs": 0, "agree": 0, "disagree": 0}
    cross_class = {"pairs": 0, "agree": 0, "disagree": 0}
    examples: List[Dict[str, object]] = []
    for a in measured:
        for b in measured:
            if a.name >= b.name:
                continue
            ra, rb = readings[a.name], readings[b.name]
            if ra.quantity != rb.quantity:
                continue
            word_order = (ra.position > rb.position) - (ra.position
                                                        < rb.position)
            magnitude_order = (ra.magnitude > rb.magnitude) - (
                ra.magnitude < rb.magnitude)
            bucket = (same_class if a.comparison_class == b.comparison_class
                      else cross_class)
            bucket["pairs"] += 1
            if word_order == magnitude_order:
                bucket["agree"] += 1
            else:
                bucket["disagree"] += 1
                if (len(examples) < 6 and word_order != 0
                        and a.comparison_class != b.comparison_class):
                    lower, higher = ((a, b) if word_order < 0 else (b, a))
                    examples.append({
                        "lower_word": lower.name,
                        "higher_word": higher.name,
                        "lower_magnitude": readings[lower.name].magnitude,
                        "higher_magnitude": readings[higher.name].magnitude,
                        "unit": readings[lower.name].unit,
                    })
    total_pairs = same_class["pairs"] + cross_class["pairs"]
    total_disagree = same_class["disagree"] + cross_class["disagree"]
    return {
        "uses": len(measured),
        "comparable_pairs": total_pairs,
        "disagreements": total_disagree,
        "same_class": same_class,
        "cross_class": cross_class,
        "word_order_decides_within_class": same_class["disagree"] == 0,
        "cross_class_disagreement": (
            Fraction(cross_class["disagree"], cross_class["pairs"])
            if cross_class["pairs"] else Fraction(0)),
        "examples": examples,
    }


# ===========================================================================
# 6.  THE REPORT
# ===========================================================================

@memo
def measure_report() -> Dict[str, object]:
    """The whole study, recomputed.  Nothing here is quoted from a document."""
    words = measure_words()
    summary = cc.register_summary()
    audit = widening_audit()
    repair = relation_repair()
    examples = []
    for word, klass in (("hot", "tea"), ("hot", "stellar_surface"),
                        ("cold", "stellar_surface"), ("fast", "walking"),
                        ("fast", "airliner"), ("heavy", "fruit"),
                        ("heavy", "star"), ("large", "room_volume"),
                        ("small", "room_volume"),
                        ("dark", "indoor_lighting"),
                        ("dark", "direct_sunlight")):
        examples.append(read(word, klass).as_dict())
    refusals = []
    for word, klass in (("large", "room"), ("dark", "room"),
                        ("hot", "walking"), ("expensive", "market")):
        try:
            read(word, klass)
        except MeasureBoundary as boundary:
            refusals.append({"word": word, "class": klass,
                             "reason": boundary.reason,
                             "message": str(boundary)})
        else:                       # pragma: no cover -- guarded by a test
            refusals.append({"word": word, "class": klass,
                             "reason": "answered", "message": ""})
    return {
        "register": dict(summary),
        "words": [
            {"word": w.word, "quantity": w.quantity, "position": w.position,
             "status": w.status, "reason": w.reason} for w in words],
        "scaled": len([w for w in words if w.scaled]),
        "unscaled": len([w for w in words if not w.scaled]),
        "lexicon_agreement": cc.lexicon_agreement(),
        "widening": audit,
        "replacement_witness": replacement_witness(),
        "relation_repair": repair,
        "basis_sweep": basis_sweep(),
        "transport": transport_audit(),
        "examples": examples,
        "refusals": refusals,
        "relation_family": list(MEASURE_RELATIONS),
        "derived_relations_hot": [list(t) for t in measure_relations("hot")],
    }
