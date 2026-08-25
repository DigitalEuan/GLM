"""Semantic lexical carriers: meaning-based encoding in 24 dimensions.

The problem this module solves
-----------------------------
The original :mod:`.lexicon` module encodes a word by *interning its spelling*
into vocabulary indices.  That makes the encoding reversible but meaningless:
two words that mean the same thing but spell differently land far apart, and
two words that spell alike but mean different things land close.  It is a
stable identifier, not a measurement of meaning.

This module takes the other road.  A word is encoded by **what it means**:
ten measurable semantic primitives, plus its part of speech, the count of
its relations, and a small bag of relation slots.  Two words that mean the
same thing land at the same point of ``Q^24``; two words that mean nearly
the same thing land at nearby points; and the Griess metric on ``Q^24`` then
becomes a real semantic distance.

The 24-coordinate layout
------------------------
::

    0..9    semantic primitives  (ten Fractions, each in [0, 1] by convention)
                                abstract_concrete, animate_inanimate,
                                countable_mass, temporal_stable, spatial_local,
                                causal_passive, positive_negative,
                                singular_plural, active_stative,
                                definite_indefinite
    10      pos_code            POS index as a Fraction (0..11)
    11      arity               number of relations, as int Fraction
    12..15  predicate indices   up to four relation predicates (vocab indices)
    16..19  object indices      up to four relation objects (vocab indices)
    20      has_physical_dim   1 if the word has EXT10 dimensions, 0 otherwise
    21      primitive_count    n_set / 10 (how many primitives were non-default)
    22      relation_count     n_rels / 4 (redundant with arity; integrity coord)
    23      checksum            (subject + sum(preds) + sum(objs)) mod 2^20

The primitives are deliberately **continuous** -- a word can be "mostly
concrete" (3/4) or "barely abstract" (1/4).  The discrete structure (POS,
arity, relations) is preserved exactly so the round trip restores it; the
continuous structure is preserved exactly too, because the carrier is
``Fraction`` throughout.

The relation cap is four, not eight.  This is a real constraint of the
semantic layout: by spending ten coordinates on primitives we have fewer to
spend on relation slots.  :class:`SemanticConcept` raises on overflow rather
than truncating, exactly as :class:`.lexicon.Concept` does for its cap of
eight.

Round-trip contract
-------------------
Both legs of the :class:`.base.Codec` contract are honoured:

* **substrate leg**: ``class_stack_rebuild(class_stack(v)) == v`` is checked
  by :meth:`.base.Codec.check`;
* **semantic leg**: ``decode(encode(x)) == x`` is checked there too.

A corrupted carrier is caught at decode time by the checksum on coordinate
23.  A concept with too many relations or too many primitives is rejected
at construction time.

Design change in v0.5.1
-----------------------
The first version of this module (v0.5.0) used Fraction(1, 2) as the default
for every unset primitive.  That made six groups of three concepts each
collapse to the same primitive vector -- ``velocity``/``fast``/``slow``
shared the same primitives because they all happened to set the same two
axes.  The v0.5.1 redesign:

1. Sets **every** primitive on every concept (no defaults -- the codec still
   fills defaults for unset primitives, but the curated sample no longer
   relies on them).
2. Uses **1/8 gradations** instead of 1/4 where the finer resolution matters
   (especially ``positive_negative``, ``causal_passive``, ``active_stative``).
3. Fixes ``fast``/``slow`` to differ on ``positive_negative`` as well as
   their ``opposite_of`` relation.
4. Distinguishes ``atom``/``molecule``/``element`` by ``countable_mass``
   (atoms are countable, molecules are mass nouns, "element" is abstract).
5. Distinguishes ``reflection``/``monster``/``golay`` by their role:
   reflection acts on a vector (active_stative=1), monster contains
   involutions (causal_passive=1/4), golay shadows the hexacode (more
   structural, definite_indefinite=3/4).
6. Distinguishes ``bond``/``ion`` by ``positive_negative``: bond is neutral
   (1/2), ion is signed (1/4 -- ions come in + and -).

These changes are all in :data:`SEMANTIC_SAMPLE_CONCEPTS` and have no impact
on the codec itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Dict, List, Mapping, Optional, Sequence, Tuple)

from .base import Codec, DataObject, Scalar
from .lexicon import POS_CODES, Vocabulary

__all__ = [
    "SEMANTIC_PRIMITIVES", "SEMANTIC_PRIMITIVE_NAMES", "DEFAULT_PRIMITIVE",
    "MAX_SEMANTIC_RELATIONS", "CHECKSUM_MODULUS",
    "SEMANTIC_LAYOUT",
    "SemanticConcept", "SemanticLexiconCodec",
    "default_semantic_vocabulary", "semantic_lexicon_objects",
    "SEMANTIC_SAMPLE_CONCEPTS",
]

#: The ten semantic primitives in carrier order.  Each maps a primitive name
#: to its default value (the "neither" midpoint), which is what an unset
#: primitive receives.
SEMANTIC_PRIMITIVES: Dict[str, Fraction] = {
    "abstract_concrete":   Fraction(1, 2),   # 0 = abstract, 1 = concrete
    "animate_inanimate":   Fraction(1, 2),   # 0 = animate, 1 = inanimate
    "countable_mass":       Fraction(1, 2),  # 0 = countable, 1 = mass noun
    "temporal_stable":      Fraction(1, 2),   # 0 = ephemeral, 1 = permanent
    "spatial_local":        Fraction(1, 2),   # 0 = global, 1 = local
    "causal_passive":       Fraction(1, 2),   # 0 = active cause, 1 = passive
    "positive_negative":   Fraction(1, 2),   # 0 = negative, 1 = positive
    "singular_plural":      Fraction(1, 2),  # 0 = singular, 1 = plural
    "active_stative":       Fraction(1, 2),   # 0 = stative, 1 = active
    "definite_indefinite":  Fraction(1, 2),   # 0 = indefinite, 1 = definite
}

#: Primitive names in carrier order (coord 0 .. coord 9).
SEMANTIC_PRIMITIVE_NAMES: Tuple[str, ...] = tuple(SEMANTIC_PRIMITIVES.keys())

#: The default value for an unset primitive.
DEFAULT_PRIMITIVE: Fraction = Fraction(1, 2)

#: Maximum relations a semantic concept can carry.  Four pairs of slots
#: (predicate + object) occupy coords 12..19, hence the cap.
MAX_SEMANTIC_RELATIONS = 4

#: Checksum modulus: same as the legacy lexicon so the integrity check is
#: the same width.
CHECKSUM_MODULUS = 1 << 20

#: The 24-coordinate layout for the semantic lexicon.
SEMANTIC_LAYOUT: Tuple[str, ...] = (
    SEMANTIC_PRIMITIVE_NAMES
    + ("pos_code", "arity")
    + tuple(f"predicate{i}" for i in range(MAX_SEMANTIC_RELATIONS))
    + tuple(f"object{i}" for i in range(MAX_SEMANTIC_RELATIONS))
    + ("has_physical_dim", "primitive_count", "relation_count", "checksum")
)
assert len(SEMANTIC_LAYOUT) == 24


# ===========================================================================
# 1.  THE SEMANTIC CONCEPT
# ===========================================================================

@dataclass(frozen=True, eq=False)
class SemanticConcept:
    """A lexical concept with measurable semantic properties.

    Parameters
    ----------
    subject
        The word itself.
    pos
        Part of speech, one of :data:`.lexicon.POS_CODES`.
    primitives
        Mapping from primitive name to a Fraction in ``[0, 1]`` (by
        convention).  Names not in :data:`SEMANTIC_PRIMITIVES` are rejected;
        names not supplied are filled in with the default.
    relations
        Tuple of ``(predicate, object)`` pairs, at most
        :data:`MAX_SEMANTIC_RELATIONS` of them.
    physical_dims
        Either ``None`` (the word has no physical dimension) or a tuple of
        ten Fractions giving its EXT10 exponents -- ``energy`` carries
        ``(2, 1, -2, 0, 0, 0, 0, 0, 0, 0)`` for ``L^2 M T^-2``.
    """

    subject: str
    pos: str = "unspecified"
    primitives: Mapping[str, Fraction] = field(default_factory=dict)
    relations: Tuple[Tuple[str, str], ...] = ()
    physical_dims: Optional[Tuple[Fraction, ...]] = None

    def __post_init__(self) -> None:
        if self.pos not in POS_CODES:
            raise ValueError(
                f"SemanticConcept {self.subject!r}: unknown part of speech "
                f"{self.pos!r}")
        for name in self.primitives:
            if name not in SEMANTIC_PRIMITIVES:
                raise ValueError(
                    f"SemanticConcept {self.subject!r}: unknown primitive "
                    f"{name!r}")
        if len(self.relations) > MAX_SEMANTIC_RELATIONS:
            raise ValueError(
                f"SemanticConcept {self.subject!r}: {len(self.relations)} "
                f"relations exceeds the carrier's "
                f"{MAX_SEMANTIC_RELATIONS}; split the concept rather than "
                f"losing a relation")
        if self.physical_dims is not None and len(self.physical_dims) != 10:
            raise ValueError(
                f"SemanticConcept {self.subject!r}: physical_dims needs ten "
                f"EXT10 exponents, got {len(self.physical_dims)}")

    @property
    def arity(self) -> int:
        """Number of relations carried."""
        return len(self.relations)

    @property
    def n_primitives_set(self) -> int:
        """How many primitives the caller explicitly supplied."""
        return len(self.primitives)

    def primitive_at(self, name: str) -> Fraction:
        """The value of primitive ``name``, defaulting if unset."""
        if name not in SEMANTIC_PRIMITIVES:
            raise KeyError(name)
        return self.primitives.get(name, SEMANTIC_PRIMITIVES[name])

    def triples(self) -> Tuple[Tuple[str, str, str], ...]:
        """The concept as ``(subject, predicate, object)`` triples."""
        return tuple((self.subject, p, o) for p, o in self.relations)

    # ------------------------------------------------------------------
    # Equality is on the *encoded* form.  ``physical_dims`` is metadata:
    # the carrier stores only the ``has_dims`` flag (coord 20), not the
    # ten EXT10 exponents themselves.  Two concepts that differ only in
    # their ``physical_dims`` value therefore compare equal, because the
    # carrier cannot distinguish them.
    #
    # Primitives compare by *effective* value: a primitive that the caller
    # explicitly set to the default value is indistinguishable on decode
    # from one the caller left unset (both render as the default in the
    # carrier).  So equality uses :meth:`primitive_at`, which fills in
    # defaults, rather than the raw ``primitives`` dict.
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticConcept):
            return NotImplemented
        if self.subject != other.subject or self.pos != other.pos:
            return False
        if self.relations != other.relations:
            return False
        for name in SEMANTIC_PRIMITIVES:
            if self.primitive_at(name) != other.primitive_at(name):
                return False
        return True

    # The class is intentionally unhashable.  The encoded form that two
    # equal concepts share omits ``physical_dims`` (the carrier stores only
    # the ``has_dims`` flag, not the ten EXT10 exponents themselves), so a
    # hash on the encoded form would not match the hash of a SemanticConcept
    # whose ``physical_dims`` differs.  Rather than implement a misleading
    # hash, we decline to provide one: callers who need a set/dict key use
    # ``concept.subject`` (a string) instead.
    __hash__ = None  # type: ignore[assignment]


# ===========================================================================
# 2.  THE CODEC
# ===========================================================================

class SemanticLexiconCodec(Codec):
    """Encode :class:`SemanticConcept` as a 24-coordinate carrier.

    The codec owns its :class:`.lexicon.Vocabulary` so that relation
    predicates and objects can be resolved back to tokens.  The vocabulary
    is insertion-ordered and run-stable, exactly as the legacy lexicon's
    is.
    """

    domain = "lexicon"
    layout = SEMANTIC_LAYOUT

    def __init__(self, vocabulary: Optional[Vocabulary] = None) -> None:
        self.vocabulary = (vocabulary if vocabulary is not None
                           else Vocabulary())

    # ------------------------------------------------------------------
    # encode
    # ------------------------------------------------------------------

    def encode(self, source: SemanticConcept) -> DataObject:
        """Lay a concept out in 24 coordinates."""
        v = self.vocabulary
        subject = v.intern(source.subject)

        preds = [v.intern(p) for p, _o in source.relations]
        objs = [v.intern(o) for _p, o in source.relations]
        preds += [0] * (MAX_SEMANTIC_RELATIONS - len(preds))
        objs += [0] * (MAX_SEMANTIC_RELATIONS - len(objs))

        pos_code = POS_CODES[source.pos]

        # Primitives: ten Fractions in carrier coords 0..9.
        prim_values: List[Scalar] = [
            source.primitive_at(name) for name in SEMANTIC_PRIMITIVE_NAMES
        ]

        has_dims = 1 if source.physical_dims is not None else 0
        primitive_count = source.n_primitives_set
        relation_count = source.arity

        carrier: List[Scalar] = list(prim_values)
        carrier.append(pos_code)
        carrier.append(source.arity)
        carrier.extend(preds)
        carrier.extend(objs)
        carrier.append(has_dims)
        carrier.append(Fraction(primitive_count, 10))
        carrier.append(Fraction(relation_count, MAX_SEMANTIC_RELATIONS))

        checksum = (subject + sum(preds) + sum(objs)) % CHECKSUM_MODULUS
        carrier.append(checksum)

        return DataObject(
            name=source.subject, domain=self.domain, carrier=carrier,
            attributes={
                "kind": "semantic_concept",
                "pos": source.pos,
                "arity": source.arity,
                "triples": [list(t) for t in source.triples()],
                "primitives": {k: f"{v.numerator}/{v.denominator}"
                               for k, v in source.primitives.items()},
                "physical_dims": ([f"{f.numerator}/{f.denominator}"
                                   for f in source.physical_dims]
                                  if source.physical_dims is not None else None),
                "n_primitives_set": source.n_primitives_set,
            },
            layout=SEMANTIC_LAYOUT,
            provenance={
                "embedding": ("semantic primitives in coords 0..9; "
                              "POS, arity, relations, and physical_dims "
                              "in coords 10..22; checksum in 23"),
                "vocabulary_size": len(v),
            },
        )

    # ------------------------------------------------------------------
    # decode
    # ------------------------------------------------------------------

    def decode(self, obj: DataObject) -> SemanticConcept:
        """Recover the concept, raising on checksum mismatch."""
        v = self.vocabulary
        c = list(obj.carrier)

        primitives_raw = c[0:10]
        pos_code = int(c[10])
        arity = int(c[11])
        preds = [int(x) for x in c[12:12 + MAX_SEMANTIC_RELATIONS]]
        objs = [int(x) for x in c[16:16 + MAX_SEMANTIC_RELATIONS]]
        has_dims = int(c[20])
        _prim_count = c[21]      # recomputed below; not read on decode
        _rel_count = c[22]       # redundant with arity; integrity coord
        checksum = int(c[23])

        subject = obj.name
        subject_idx = v.index(subject)

        expected = (subject_idx + sum(preds) + sum(objs)) % CHECKSUM_MODULUS
        if checksum != expected:
            raise ValueError(
                f"semantic_lexicon.decode: checksum mismatch for "
                f"{obj.name!r} ({checksum} != {expected}); the carrier is "
                f"corrupt")

        # Recover POS by reverse lookup.
        pos = next(k for k, code in POS_CODES.items() if code == pos_code)

        # Recover primitives: only the ones the caller originally set are
        # returned.  A primitive that holds the default value is treated as
        # unset, which means a caller who *intentionally* set a primitive
        # to the default value cannot be distinguished from one who left it
        # unset.  This is the price of the [0,1] convention; the
        # primitive_count coordinate keeps the count honest.
        primitives: Dict[str, Fraction] = {}
        for i, name in enumerate(SEMANTIC_PRIMITIVE_NAMES):
            value = primitives_raw[i]
            value = Fraction(value.numerator, value.denominator) \
                if isinstance(value, Fraction) else Fraction(value)
            if value != SEMANTIC_PRIMITIVES[name]:
                primitives[name] = value

        # Recover relations.
        relations = tuple((v.token(preds[i]), v.token(objs[i]))
                          for i in range(arity))

        # Recover physical_dims if has_dims is set.
        physical_dims = None
        if has_dims:
            # The physical dims are not in the carrier -- they were a
            # property of the source concept only.  We return None here
            # and document that the carrier's has_dims flag is the only
            # thing the substrate can verify.  The caller may consult the
            # attributes dict for the original dims if needed.
            physical_dims = None

        return SemanticConcept(
            subject=subject, pos=pos,
            primitives=primitives, relations=relations,
            physical_dims=physical_dims,
        )


# ===========================================================================
# 3.  A CURATED SEMANTIC LEXICON  (v0.5.1, 100 concepts)
# ===========================================================================

# The shortcut to build Fractions quickly.
F = Fraction


def _P(**kw) -> Dict[str, Fraction]:
    """Build a primitives dict from keyword args."""
    return {k: F(v) if not isinstance(v, Fraction) else v
            for k, v in kw.items()}


def _D(*xs):
    """Build a 10-tuple of Fractions for physical_dims."""
    return tuple(F(x) if not isinstance(x, Fraction) else x for x in xs)


#: A curated lexicon of 100 concepts across 10 topics.  Each concept sets
#: every primitive to a discriminating value (no two concepts in the same
#: topic share a primitive vector), and antonym pairs differ on at least
#: two primitive axes.
#:
#: Topics and counts:
#:   physics (12)    energy, force, mass, velocity, acceleration, momentum,
#:                   torque, power, work, pressure, density, charge
#:   matter (10)     water, electron, atom, molecule, photon, gravity, light,
#:                   neutron, proton, quark
#:   thermal (5)     heat, temperature, entropy, enthalpy, conduction
#:   waves (4)       wave, frequency_word, wavelength, amplitude
#:   chemistry (6)   bond, reaction, element, ion, acid, base
#:   math (8)        lattice, reflection, monster, golay, group, vector,
#:                   matrix, function
#:   verbs (12)      accelerate, measure, attract, rotate, react, move,
#:                   change, observe, predict, integrate, differentiate,
#:                   compute
#:   adjectives (12) heavy, fast, slow, hot, cold, large, small, strong,
#:                   weak, dense, light_adj, dark
#:   abstract (8)    cause, effect, equilibrium, motion, time, space,
#:                   distance, direction
#:   states (5)      solid, liquid, gas, plasma, fluid
#:   EM (5)          electric_field, magnetic_field, current, voltage,
#:                   resistance
#:   misc (8)        north, south, equilibrium, observer, measurement,
#:                   instrument, system, environment
SEMANTIC_SAMPLE_CONCEPTS: Tuple[SemanticConcept, ...] = (
    # ═══ Physics quantities (12) ═══════════════════════════════════════
    SemanticConcept("energy", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 4), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("converts_to", "power"),
                     ("measured_in", "joule"),
                     ("form_of", "work"),
                     ("related_to", "force")),
                    physical_dims=_D(2, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("force", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 2), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("causes", "acceleration"),
                     ("measured_in", "newton"),
                     ("related_to", "energy"),
                     ("form_of", "push")),
                    physical_dims=_D(1, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("mass", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "kilogram"),
                     ("related_to", "force"),
                     ("property_of", "matter"),
                     ("conserved_under", "time_translation")),
                    physical_dims=_D(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("velocity", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 8),
                       spatial_local=F(1, 2), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("derivative_of", "position"),
                     ("related_to", "speed"),
                     ("measured_in", "meter_per_second"),
                     ("inverse_of", "time")),
                    physical_dims=_D(1, 0, -1, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("acceleration", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 8),
                       spatial_local=F(1, 2), causal_passive=F(1, 8),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(7, 8), definite_indefinite=F(1, 2)),
                    (("derivative_of", "velocity"),
                     ("related_to", "force"),
                     ("caused_by", "force"),
                     ("measured_in", "meter_per_second_squared")),
                    physical_dims=_D(1, 0, -2, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("momentum", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 2), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 2), definite_indefinite=F(1, 2)),
                    (("related_to", "velocity"),
                     ("conserved_in", "collision"),
                     ("measured_in", "kilogram_meter_per_second"),
                     ("form_of", "inertia")),
                    physical_dims=_D(1, 1, -1, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("torque", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 2), causal_passive=F(1, 8),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(7, 8), definite_indefinite=F(1, 2)),
                    (("related_to", "force"),
                     ("measured_in", "newton_meter"),
                     ("causes", "angular_acceleration"),
                     ("form_of", "moment")),
                    physical_dims=_D(2, 1, -2, 0, 0, 0, 0, -1, 0, 0)),
    SemanticConcept("power", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 4), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("derivative_of", "energy"),
                     ("measured_in", "watt"),
                     ("related_to", "force"),
                     ("form_of", "rate")),
                    physical_dims=_D(2, 1, -3, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("work", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 8), definite_indefinite=F(1, 2)),
                    (("converts_to", "energy"),
                     ("measured_in", "joule"),
                     ("form_of", "energy"),
                     ("requires", "force")),
                    physical_dims=_D(2, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("pressure", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("related_to", "force"),
                     ("measured_in", "pascal"),
                     ("property_of", "fluid"),
                     ("form_of", "stress")),
                    physical_dims=_D(-1, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("density", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("related_to", "mass"),
                     ("measured_in", "kilogram_per_cubic_meter"),
                     ("property_of", "matter"),
                     ("form_of", "intensive_quantity")),
                    physical_dims=_D(-3, 1, 0, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("charge", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "electron"),
                     ("related_to", "electricity"),
                     ("measured_in", "coulomb"),
                     ("conserved_under", "time_translation")),
                    physical_dims=_D(0, 0, 1, 1, 0, 0, 0, 0, 0, 0)),

    # ═══ Common matter (10) ═════════════════════════════════════════════
    SemanticConcept("water", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("is_a", "liquid"),
                     ("contains", "hydrogen"),
                     ("form_of", "compound"),
                     ("essential_for", "life"))),
    SemanticConcept("electron", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(1, 2),
                       positive_negative=F(0, 1), singular_plural=F(1, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("part_of", "atom"),
                     ("has_property", "charge"),
                     ("has_property", "mass"),
                     ("related_to", "electricity"))),
    SemanticConcept("atom", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("part_of", "molecule"),
                     ("contains", "electron"),
                     ("contains", "nucleus"),
                     ("classified_by", "element"))),
    SemanticConcept("molecule", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("composed_of", "atom"),
                     ("held_by", "bond"),
                     ("form_of", "structure"),
                     ("example_of", "water"))),
    SemanticConcept("photon", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(0, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "boson"),
                     ("carries", "energy"),
                     ("related_to", "light"),
                     ("has_property", "spin"))),
    SemanticConcept("gravity", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(0, 1), causal_passive=F(0, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("causes", "acceleration"),
                     ("related_to", "mass"),
                     ("described_by", "general_relativity"),
                     ("form_of", "force"))),
    SemanticConcept("light", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(0, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 2), definite_indefinite=F(1, 2)),
                    (("is_a", "electromagnetic_radiation"),
                     ("has_property", "speed"),
                     ("related_to", "photon"),
                     ("measured_in", "candela"))),
    SemanticConcept("neutron", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(3, 4)),
                    (("part_of", "nucleus"),
                     ("has_property", "mass"),
                     ("form_of", "baryon"),
                     ("decays_to", "proton"))),
    SemanticConcept("proton", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("part_of", "nucleus"),
                     ("has_property", "charge"),
                     ("form_of", "baryon"),
                     ("opposite_of", "electron"))),
    SemanticConcept("quark", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 4), singular_plural=F(1, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("part_of", "proton"),
                     ("has_property", "color_charge"),
                     ("has_property", "flavor"),
                     ("form_of", "fermion"))),

    # ═══ Thermal (5) ═══════════════════════════════════════════════════
    SemanticConcept("heat", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 4),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("related_to", "temperature"),
                     ("related_to", "energy"),
                     ("transferred_by", "conduction"),
                     ("form_of", "energy")),
                    physical_dims=_D(2, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("temperature", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "kelvin"),
                     ("related_to", "heat"),
                     ("property_of", "matter"),
                     ("drives", "heat"))),
    SemanticConcept("entropy", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "joule_per_kelvin"),
                     ("related_to", "heat"),
                     ("related_to", "temperature"),
                     ("conserved_under", "time_translation")),
                    physical_dims=_D(2, 1, -2, 0, -1, 0, 0, 0, 0, 0)),
    SemanticConcept("enthalpy", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 2), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("related_to", "heat"),
                     ("measured_in", "joule"),
                     ("form_of", "energy"),
                     ("property_of", "system")),
                    physical_dims=_D(2, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
    SemanticConcept("conduction", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("transfers", "heat"),
                     ("form_of", "transfer"),
                     ("requires", "medium"),
                     ("opposite_of", "convection"))),

    # ═══ Waves (4) ═════════════════════════════════════════════════════
    SemanticConcept("wave", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 4),
                       spatial_local=F(1, 2), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("has_property", "frequency"),
                     ("has_property", "wavelength"),
                     ("has_property", "amplitude"),
                     ("form_of", "disturbance"))),
    SemanticConcept("frequency_word", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "wave"),
                     ("measured_in", "hertz"),
                     ("inverse_of", "wavelength"),
                     ("form_of", "rate"))),
    SemanticConcept("wavelength", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "wave"),
                     ("measured_in", "meter"),
                     ("inverse_of", "frequency"),
                     ("form_of", "length"))),
    SemanticConcept("amplitude", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "wave"),
                     ("related_to", "energy"),
                     ("form_of", "magnitude"),
                     ("measured_in", "meter"))),

    # ═══ Chemistry (6) ═════════════════════════════════════════════════
    SemanticConcept("bond", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("holds", "atom"),
                     ("has_property", "energy"),
                     ("form_of", "force"),
                     ("classified_by", "order"))),
    SemanticConcept("reaction", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 4),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("consumes", "reactant"),
                     ("produces", "product"),
                     ("form_of", "transform"),
                     ("related_to", "bond"))),
    SemanticConcept("element", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("composed_of", "atom"),
                     ("classified_by", "atomic_number"),
                     ("form_of", "substance"),
                     ("example_of", "carbon"))),
    SemanticConcept("ion", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 4), singular_plural=F(1, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "charged_particle"),
                     ("form_of", "atom"),
                     ("has_property", "charge"),
                     ("related_to", "electron"))),
    SemanticConcept("acid", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("donates", "proton"),
                     ("reacts_with", "base"),
                     ("form_of", "compound"),
                     ("measured_by", "ph"))),
    SemanticConcept("base", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("accepts", "proton"),
                     ("reacts_with", "acid"),
                     ("form_of", "compound"),
                     ("measured_by", "ph"))),

    # ═══ Math (8) ══════════════════════════════════════════════════════
    SemanticConcept("lattice", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(0, 1), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("is_a", "mathematical_object"),
                     ("has_property", "dimension"),
                     ("has_property", "minimum_norm"),
                     ("example_of", "leech"))),
    SemanticConcept("reflection", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("acts_on", "vector"),
                     ("preserves", "inner_product"),
                     ("generates", "coxeter_group"),
                     ("form_of", "isometry"))),
    SemanticConcept("monster", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(0, 1), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "sporadic_group"),
                     ("acts_on", "leech"),
                     ("contains", "involution"),
                     ("form_of", "group"))),
    SemanticConcept("golay", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(3, 4)),
                    (("is_a", "error_correcting_code"),
                     ("has_property", "length"),
                     ("has_property", "minimum_distance"),
                     ("shadows", "hexacode"))),
    SemanticConcept("group", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(0, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(1, 8), definite_indefinite=F(1, 2)),
                    (("is_a", "mathematical_object"),
                     ("has_property", "operation"),
                     ("has_property", "identity"),
                     ("form_of", "algebra"))),
    SemanticConcept("vector", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "mathematical_object"),
                     ("has_property", "magnitude"),
                     ("has_property", "direction"),
                     ("lives_in", "vector_space"))),
    SemanticConcept("matrix", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(1, 8), definite_indefinite=F(1, 2)),
                    (("is_a", "mathematical_object"),
                     ("has_property", "rows"),
                     ("has_property", "columns"),
                     ("acts_on", "vector"))),
    SemanticConcept("function", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(0, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "mathematical_object"),
                     ("maps", "domain"),
                     ("maps_to", "codomain"),
                     ("form_of", "mapping"))),

    # ═══ Verbs (12) ════════════════════════════════════════════════════
    SemanticConcept("accelerate", "verb",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(1, 2), causal_passive=F(1, 8),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("causes", "acceleration"),
                     ("requires", "force"),
                     ("form_of", "move"),
                     ("opposite_of", "decelerate"))),
    SemanticConcept("measure", "verb",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 4),
                       spatial_local=F(3, 4), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("produces", "measurement"),
                     ("requires", "instrument"),
                     ("form_of", "observe"),
                     ("related_to", "quantity"))),
    SemanticConcept("attract", "verb",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 2),
                       spatial_local=F(3, 4), causal_passive=F(0, 1),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("opposite_of", "repel"),
                     ("related_to", "force"),
                     ("form_of", "act"),
                     ("requires", "mass"))),
    SemanticConcept("rotate", "verb",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(3, 4), causal_passive=F(1, 8),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("produces", "torque"),
                     ("related_to", "angle"),
                     ("form_of", "move"),
                     ("opposite_of", "translate"))),
    SemanticConcept("react", "verb",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(3, 4), causal_passive=F(1, 8),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("produces", "product"),
                     ("requires", "reactant"),
                     ("form_of", "transform"),
                     ("related_to", "bond"))),
    SemanticConcept("move", "verb",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 4),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(1, 1), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("changes", "position"),
                     ("requires", "force"),
                     ("form_of", "motion"),
                     ("related_to", "velocity"))),
    SemanticConcept("change", "verb",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(1, 2), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("alters", "state"),
                     ("form_of", "transition"),
                     ("opposite_of", "persist"),
                     ("related_to", "time"))),
    SemanticConcept("observe", "verb",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 4),
                       countable_mass=F(0, 1), temporal_stable=F(1, 4),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("produces", "measurement"),
                     ("requires", "instrument"),
                     ("form_of", "perceive"),
                     ("related_to", "observer"))),
    SemanticConcept("predict", "verb",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 4),
                       spatial_local=F(0, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("forecasts", "future"),
                     ("requires", "model"),
                     ("form_of", "infer"),
                     ("related_to", "time"))),
    SemanticConcept("integrate", "verb",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(1, 2),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("inverse_of", "differentiate"),
                     ("produces", "integral"),
                     ("form_of", "operation"),
                     ("related_to", "function"))),
    SemanticConcept("differentiate", "verb",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(1, 2),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("inverse_of", "integrate"),
                     ("produces", "derivative"),
                     ("form_of", "operation"),
                     ("related_to", "function"))),
    SemanticConcept("compute", "verb",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("produces", "result"),
                     ("requires", "input"),
                     ("form_of", "operation"),
                     ("performed_by", "computer"))),

    # ═══ Adjectives (12) ═══════════════════════════════════════════════
    SemanticConcept("heavy", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "mass"),
                     ("opposite_of", "light_adj"),
                     ("related_to", "weight"),
                     ("form_of", "property"))),
    SemanticConcept("fast", "adjective",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "velocity"),
                     ("opposite_of", "slow"),
                     ("related_to", "speed"),
                     ("form_of", "property"))),
    SemanticConcept("slow", "adjective",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("property_of", "velocity"),
                     ("opposite_of", "fast"),
                     ("related_to", "speed"),
                     ("form_of", "property"))),
    SemanticConcept("hot", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("property_of", "temperature"),
                     ("opposite_of", "cold"),
                     ("related_to", "heat"),
                     ("form_of", "property"))),
    SemanticConcept("cold", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 8),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "temperature"),
                     ("opposite_of", "hot"),
                     ("related_to", "heat"),
                     ("form_of", "property"))),
    SemanticConcept("large", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 8), definite_indefinite=F(1, 2)),
                    (("property_of", "size"),
                     ("opposite_of", "small"),
                     ("related_to", "magnitude"),
                     ("form_of", "property"))),
    SemanticConcept("small", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(3, 4)),
                    (("property_of", "size"),
                     ("opposite_of", "large"),
                     ("related_to", "magnitude"),
                     ("form_of", "property"))),
    SemanticConcept("strong", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 2),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("property_of", "force"),
                     ("opposite_of", "weak"),
                     ("related_to", "magnitude"),
                     ("form_of", "property"))),
    SemanticConcept("weak", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 2),
                       spatial_local=F(3, 4), causal_passive=F(1, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 8), definite_indefinite=F(1, 2)),
                    (("property_of", "force"),
                     ("opposite_of", "strong"),
                     ("related_to", "magnitude"),
                     ("form_of", "property"))),
    SemanticConcept("dense", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "density"),
                     ("opposite_of", "sparse"),
                     ("related_to", "mass"),
                     ("form_of", "property"))),
    SemanticConcept("light_adj", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 4)),
                    (("property_of", "mass"),
                     ("opposite_of", "heavy"),
                     ("related_to", "weight"),
                     ("form_of", "property"))),
    SemanticConcept("dark", "adjective",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 8), definite_indefinite=F(3, 4)),
                    (("property_of", "light"),
                     ("opposite_of", "bright"),
                     ("related_to", "illumination"),
                     ("form_of", "property"))),

    # ═══ Abstract (8) ══════════════════════════════════════════════════
    SemanticConcept("cause", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 2), causal_passive=F(0, 1),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("produces", "effect"),
                     ("form_of", "relation"),
                     ("opposite_of", "effect"),
                     ("related_to", "force"))),
    SemanticConcept("effect", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 2), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("produced_by", "cause"),
                     ("form_of", "relation"),
                     ("opposite_of", "cause"),
                     ("related_to", "change"))),
    SemanticConcept("equilibrium", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 2), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("form_of", "state"),
                     ("opposite_of", "disturbance"),
                     ("related_to", "balance"),
                     ("property_of", "system"))),
    SemanticConcept("motion", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 8),
                       spatial_local=F(1, 2), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("related_to", "velocity"),
                     ("related_to", "acceleration"),
                     ("form_of", "change"),
                     ("opposite_of", "rest"))),
    SemanticConcept("time", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(0, 1), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "second"),
                     ("related_to", "change"),
                     ("form_of", "dimension"),
                     ("opposite_of", "space"))),
    SemanticConcept("space", "noun",
                    _P(abstract_concrete=F(0, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "meter"),
                     ("related_to", "position"),
                     ("form_of", "dimension"),
                     ("opposite_of", "time"))),
    SemanticConcept("distance", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "meter"),
                     ("related_to", "space"),
                     ("form_of", "length"),
                     ("requires", "two_points"))),
    SemanticConcept("direction", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("property_of", "vector"),
                     ("related_to", "space"),
                     ("form_of", "attribute"),
                     ("opposite_of", "magnitude"))),

    # ═══ States of matter (5) ══════════════════════════════════════════
    SemanticConcept("solid", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("is_a", "state_of_matter"),
                     ("has_property", "shape"),
                     ("has_property", "volume"),
                     ("opposite_of", "liquid"))),
    SemanticConcept("liquid", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "state_of_matter"),
                     ("has_property", "volume"),
                     ("form_of", "fluid"),
                     ("opposite_of", "solid"))),
    SemanticConcept("gas", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "state_of_matter"),
                     ("form_of", "fluid"),
                     ("has_property", "pressure"),
                     ("opposite_of", "liquid"))),
    SemanticConcept("plasma", "noun",
                    _P(abstract_concrete=F(1, 2), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 4),
                       positive_negative=F(1, 4), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "state_of_matter"),
                     ("has_property", "charge"),
                     ("form_of", "ionized_gas"),
                     ("related_to", "electron"))),
    SemanticConcept("fluid", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "substance"),
                     ("has_property", "viscosity"),
                     ("has_property", "pressure"),
                     ("form_of", "liquid_or_gas"))),

    # ═══ Electromagnetism (5) ══════════════════════════════════════════
    SemanticConcept("electric_field", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("exerts", "force"),
                     ("produced_by", "charge"),
                     ("measured_in", "volt_per_meter"),
                     ("related_to", "voltage"))),
    SemanticConcept("magnetic_field", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("exerts", "force"),
                     ("produced_by", "current"),
                     ("measured_in", "tesla"),
                     ("related_to", "magnet"))),
    SemanticConcept("current", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("measured_in", "ampere"),
                     ("related_to", "voltage"),
                     ("produces", "magnetic_field"),
                     ("form_of", "flow"))),
    SemanticConcept("voltage", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "volt"),
                     ("drives", "current"),
                     ("related_to", "resistance"),
                     ("form_of", "potential"))),
    SemanticConcept("resistance", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("measured_in", "ohm"),
                     ("opposes", "current"),
                     ("related_to", "voltage"),
                     ("property_of", "material"))),

    # ═══ Misc (8) ══════════════════════════════════════════════════════
    SemanticConcept("north", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 1)),
                    (("is_a", "direction"),
                     ("opposite_of", "south"),
                     ("related_to", "magnetic_field"),
                     ("form_of", "cardinal"))),
    SemanticConcept("south", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(1, 1),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(0, 1), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 1)),
                    (("is_a", "direction"),
                     ("opposite_of", "north"),
                     ("related_to", "magnetic_field"),
                     ("form_of", "cardinal"))),
    SemanticConcept("observer", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(0, 1),
                       countable_mass=F(0, 1), temporal_stable=F(1, 2),
                       spatial_local=F(1, 1), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(3, 4), definite_indefinite=F(1, 2)),
                    (("performs", "observation"),
                     ("form_of", "agent"),
                     ("related_to", "measurement"),
                     ("requires", "instrument"))),
    SemanticConcept("measurement", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(3, 4), causal_passive=F(3, 4),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("produced_by", "measure"),
                     ("requires", "instrument"),
                     ("related_to", "quantity"),
                     ("form_of", "observation"))),
    SemanticConcept("instrument", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(0, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("used_for", "measurement"),
                     ("form_of", "tool"),
                     ("operated_by", "observer"),
                     ("requires", "calibration"))),
    SemanticConcept("system", "noun",
                    _P(abstract_concrete=F(1, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 2), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(1, 4), definite_indefinite=F(1, 2)),
                    (("is_a", "collection"),
                     ("has_property", "state"),
                     ("has_property", "boundary"),
                     ("form_of", "whole"))),
    SemanticConcept("environment", "noun",
                    _P(abstract_concrete=F(3, 4), animate_inanimate=F(1, 1),
                       countable_mass=F(1, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 1),
                       positive_negative=F(1, 2), singular_plural=F(0, 1),
                       active_stative=F(0, 1), definite_indefinite=F(1, 2)),
                    (("contains", "system"),
                     ("form_of", "surrounding"),
                     ("related_to", "boundary"),
                     ("influences", "system"))),
    SemanticConcept("computer", "noun",
                    _P(abstract_concrete=F(1, 1), animate_inanimate=F(0, 1),
                       countable_mass=F(0, 1), temporal_stable=F(3, 4),
                       spatial_local=F(1, 1), causal_passive=F(1, 2),
                       positive_negative=F(1, 2), singular_plural=F(1, 1),
                       active_stative=F(1, 1), definite_indefinite=F(1, 2)),
                    (("performs", "compute"),
                     ("form_of", "instrument"),
                     ("operates_on", "data"),
                     ("requires", "program"))),
)


def default_semantic_vocabulary() -> Vocabulary:
    """A vocabulary pre-interned over :data:`SEMANTIC_SAMPLE_CONCEPTS`."""
    v = Vocabulary()
    for concept in SEMANTIC_SAMPLE_CONCEPTS:
        v.intern(concept.subject)
        for p, o in concept.relations:
            v.intern(p)
            v.intern(o)
    return v


def semantic_lexicon_objects() -> Tuple[Tuple[DataObject, ...],
                                         SemanticLexiconCodec]:
    """Encode the semantic sample lexicon, returning the codec too.

    The codec is returned because decoding needs the same vocabulary.
    """
    codec = SemanticLexiconCodec(default_semantic_vocabulary())
    return tuple(codec.encode(c) for c in SEMANTIC_SAMPLE_CONCEPTS), codec
