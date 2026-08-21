"""Tests for :mod:`glm_universal.data_objects.semantic_lexicon`.

Mirrors the structure of :class:`TestLexicon` in
:mod:`tests.test_data_objects` so the semantic codec is held to the same
standard as the legacy one.  Every test here exercises a property the
codec must hold, not an implementation detail.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.data_objects import semantic_lexicon as sl
from glm_universal.data_objects import base as do_base
from glm_universal.data_objects.semantic_lexicon import (
    CHECKSUM_MODULUS, DEFAULT_PRIMITIVE, MAX_SEMANTIC_RELATIONS,
    SEMANTIC_LAYOUT, SEMANTIC_PRIMITIVE_NAMES, SEMANTIC_PRIMITIVES,
    SEMANTIC_SAMPLE_CONCEPTS, SemanticConcept, SemanticLexiconCodec,
    default_semantic_vocabulary, semantic_lexicon_objects)

F = Fraction
_ROOT = Path(__file__).resolve().parents[2]


def _b_pairs(names):
    """All distinct pairs from ``names``, as a flat list of (a, b)."""
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            out.append((a, b))
    return out


# ===========================================================================
# 1.  LAYOUT AND PRIMITIVES
# ===========================================================================

class TestLayout(unittest.TestCase):

    def test_layout_has_24_coordinates(self):
        self.assertEqual(len(SEMANTIC_LAYOUT), 24)

    def test_primitive_names_are_in_layout_order(self):
        self.assertEqual(SEMANTIC_LAYOUT[:10], SEMANTIC_PRIMITIVE_NAMES)

    def test_primitive_count_is_ten(self):
        self.assertEqual(len(SEMANTIC_PRIMITIVES), 10)

    def test_layout_has_no_duplicates(self):
        self.assertEqual(len(set(SEMANTIC_LAYOUT)), 24)

    def test_max_relations_is_four(self):
        # Predicates occupy coords 12..15, objects 16..19, hence the cap.
        self.assertEqual(MAX_SEMANTIC_RELATIONS, 4)

    def test_default_primitive_is_neither(self):
        self.assertEqual(DEFAULT_PRIMITIVE, F(1, 2))

    def test_all_primitives_are_fractions(self):
        for name, value in SEMANTIC_PRIMITIVES.items():
            self.assertIsInstance(value, Fraction, name)


# ===========================================================================
# 2.  CONCEPT VALIDATION
# ===========================================================================

class TestConceptValidation(unittest.TestCase):

    def test_unknown_pos_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticConcept("x", pos="gerundive")

    def test_unknown_primitive_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticConcept("x", primitives={"nonexistent": F(1)})

    def test_overfull_relations_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticConcept("toomany", relations=tuple(
                (f"p{i}", f"o{i}") for i in range(MAX_SEMANTIC_RELATIONS + 1)))

    def test_wrong_length_physical_dims_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticConcept("bad", physical_dims=(F(1), F(2), F(3)))

    def test_empty_concept_is_valid(self):
        c = SemanticConcept("solo")
        self.assertEqual(c.subject, "solo")
        self.assertEqual(c.pos, "unspecified")
        self.assertEqual(c.arity, 0)
        self.assertEqual(c.n_primitives_set, 0)

    def test_saturated_concept_is_valid(self):
        c = SemanticConcept(
            "full", pos="noun",
            primitives={n: F(3, 4) for n in SEMANTIC_PRIMITIVE_NAMES},
            relations=tuple((f"p{i}", f"o{i}")
                            for i in range(MAX_SEMANTIC_RELATIONS)))
        self.assertEqual(c.arity, MAX_SEMANTIC_RELATIONS)
        self.assertEqual(c.n_primitives_set, 10)

    def test_triples_round_out_relations(self):
        c = SemanticConcept("water", pos="noun",
                            relations=(("is_a", "liquid"),))
        self.assertEqual(c.triples(), (("water", "is_a", "liquid"),))


# ===========================================================================
# 3.  EQUALITY SEMANTICS
# ===========================================================================

class TestEquality(unittest.TestCase):

    def test_concepts_equal_when_primitives_defaulted_vs_unset(self):
        """A primitive set to its default equals one left unset."""
        a = SemanticConcept("x", primitives={"abstract_concrete": F(1, 2)})
        b = SemanticConcept("x")
        self.assertEqual(a, b)
        # Both are unhashable (SemanticConcept.__hash__ is None), so we
        # cannot assert hash equality.  The equality contract still holds
        # via __eq__.

    def test_concepts_equal_when_only_physical_dims_differ(self):
        """physical_dims is metadata; the carrier cannot preserve it."""
        a = SemanticConcept("energy", pos="noun",
                           physical_dims=(F(2), F(1), F(-2), F(0), F(0),
                                          F(0), F(0), F(0), F(0), F(0)))
        b = SemanticConcept("energy", pos="noun")
        self.assertEqual(a, b)

    def test_concepts_unequal_when_primitives_differ(self):
        a = SemanticConcept("x", primitives={"abstract_concrete": F(1, 4)})
        b = SemanticConcept("x", primitives={"abstract_concrete": F(3, 4)})
        self.assertNotEqual(a, b)

    def test_concepts_unequal_when_subjects_differ(self):
        a = SemanticConcept("alpha")
        b = SemanticConcept("beta")
        self.assertNotEqual(a, b)

    def test_concepts_unequal_when_pos_differs(self):
        a = SemanticConcept("x", pos="noun")
        b = SemanticConcept("x", pos="verb")
        self.assertNotEqual(a, b)

    def test_concepts_unequal_when_relations_differ(self):
        a = SemanticConcept("x", relations=(("is_a", "y"),))
        b = SemanticConcept("x", relations=(("is_a", "z"),))
        self.assertNotEqual(a, b)


# ===========================================================================
# 4.  CODEC ROUND TRIPS
# ===========================================================================

class TestCodecRoundTrip(unittest.TestCase):

    def test_sample_lexicon_round_trips(self):
        """Every concept in the curated sample passes both round trips."""
        objs, codec = semantic_lexicon_objects()
        self.assertEqual(len(objs), len(SEMANTIC_SAMPLE_CONCEPTS))
        for obj, concept in zip(objs, SEMANTIC_SAMPLE_CONCEPTS):
            with self.subTest(name=obj.name):
                self.assertTrue(obj.round_trip_ok(),
                                 f"substrate leg failed for {obj.name}")
                self.assertEqual(codec.decode(obj), concept,
                                 f"semantic leg failed for {obj.name}")

    def test_check_passes_every_sample_concept(self):
        """The strict Codec.check() runs both legs and asserts."""
        codec = SemanticLexiconCodec(default_semantic_vocabulary())
        for concept in SEMANTIC_SAMPLE_CONCEPTS:
            with self.subTest(name=concept.subject):
                obj = codec.check(concept)
                self.assertEqual(obj.name, concept.subject)

    def test_empty_concept_round_trips(self):
        codec = SemanticLexiconCodec()
        obj = codec.check(SemanticConcept("solo"))
        self.assertTrue(obj.round_trip_ok())
        self.assertEqual(codec.decode(obj), SemanticConcept("solo"))

    def test_saturated_concept_round_trips(self):
        codec = SemanticLexiconCodec()
        c = SemanticConcept(
            "full", pos="noun",
            primitives={n: F(3, 4) for n in SEMANTIC_PRIMITIVE_NAMES},
            relations=tuple((f"p{i}", f"o{i}")
                            for i in range(MAX_SEMANTIC_RELATIONS)),
            physical_dims=tuple(F(0) for _ in range(10)))
        codec.check(c)

    def test_overfull_concept_rejected(self):
        codec = SemanticLexiconCodec()
        with self.assertRaises(ValueError):
            SemanticConcept("toomany",
                            relations=tuple((f"p{i}", f"o{i}")
                                            for i in range(
                                                MAX_SEMANTIC_RELATIONS + 1)))

    def test_checksum_catches_corruption(self):
        """Tampering with a coordinate covered by the checksum fails decode."""
        codec = SemanticLexiconCodec(default_semantic_vocabulary())
        obj = codec.encode(SEMANTIC_SAMPLE_CONCEPTS[0])
        # Coord 12 is the first predicate index, which is part of the
        # checksum input.
        broken = list(obj.carrier)
        broken[12] = int(broken[12]) + 1
        tampered = do_base.DataObject(name=obj.name, domain=obj.domain,
                                       carrier=broken, attributes=obj.attributes,
                                       layout=obj.layout)
        with self.assertRaises(ValueError):
            codec.decode(tampered)

    def test_vocabulary_is_stable_and_invertible(self):
        v = default_semantic_vocabulary()
        # The vocabulary includes the subjects and all relation tokens.
        for concept in SEMANTIC_SAMPLE_CONCEPTS:
            self.assertIn(concept.subject, v)
            for p, o in concept.relations:
                self.assertIn(p, v)
                self.assertIn(o, v)

    def test_two_independent_vocabularies_agree(self):
        a = default_semantic_vocabulary().tokens()
        b = default_semantic_vocabulary().tokens()
        self.assertEqual(a, b)


# ===========================================================================
# 5.  CARRIER INVARIANTS
# ===========================================================================

class TestCarrierInvariants(unittest.TestCase):

    def test_parameters_are_admissible_everywhere(self):
        objs, _ = semantic_lexicon_objects()
        for obj in objs:
            params = obj.parameters()
            self.assertTrue(params.contains(),
                             f"{obj.name}: stack parameters not admissible")

    def test_every_object_round_trips_through_stack(self):
        objs, _ = semantic_lexicon_objects()
        for obj in objs:
            self.assertTrue(obj.round_trip_ok(), obj.name)

    def test_layout_matches_carrier_length(self):
        objs, _ = semantic_lexicon_objects()
        for obj in objs:
            self.assertEqual(len(obj.layout), len(obj.carrier))

    def test_every_carrier_has_24_coordinates(self):
        objs, _ = semantic_lexicon_objects()
        for obj in objs:
            self.assertEqual(len(obj.carrier), 24)

    def test_no_carrier_holds_a_float(self):
        objs, _ = semantic_lexicon_objects()
        for obj in objs:
            for c in obj.carrier:
                self.assertNotIsInstance(c, float)


# ===========================================================================
# 6.  NO HASHING ANYWHERE
# ===========================================================================

class TestNoHashing(unittest.TestCase):
    """The module must not rely on ``hash``, which is salted per process."""

    def test_no_hash_call_in_source(self):
        src = (_ROOT / "glm_universal" / "data_objects" /
               "semantic_lexicon.py").read_text(encoding="utf-8")
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue
            self.assertNotIn("hash(", stripped)


# ===========================================================================
# 7.  SEMANTIC DISTANCES ARE MEANINGFUL
# ===========================================================================

class TestSemanticDistances(unittest.TestCase):
    """The whole point of semantic primitives is that semantic distances
    track meaning, not spelling."""

    def setUp(self):
        from glm_universal.reasoning import metric
        self.metric = metric
        objs, codec = semantic_lexicon_objects()
        self.objs = {o.name: o for o in objs}

    def d2(self, a: str, b: str) -> Fraction:
        from glm_universal.reasoning.metric import distance2
        return distance2(self.objs[a].carrier, self.objs[b].carrier)

    def test_antonyms_differ_on_the_relevant_primitive_axis(self):
        """The 'hot'/'cold' antonym pair should differ in their
        ``positive_negative`` primitive (hot=positive, cold=negative),
        and the difference should be maximal (1 vs 0)."""
        hot_obj = self.objs["hot"]
        cold_obj = self.objs["cold"]
        # ``positive_negative`` is index 6 in SEMANTIC_PRIMITIVE_NAMES.
        prim_index = SEMANTIC_PRIMITIVE_NAMES.index("positive_negative")
        hot_pn = hot_obj.carrier[prim_index]
        cold_pn = cold_obj.carrier[prim_index]
        self.assertEqual(hot_pn, F(1, 1))
        self.assertEqual(cold_pn, F(0, 1))
        # And their distance in the primitives subspace should be > 0.
        self.assertGreater(self._prim_d2("hot", "cold"), 0)

    def test_antonym_pair_distance_is_at_least_the_axis_difference(self):
        """hot↔cold primitives-subspace distance is at least the
        positive_negative axis difference (1²/8 = 1/8).  In v0.5.1
        the antonyms also differ on active_stative, so the actual
        distance is larger."""
        self.assertGreaterEqual(self._prim_d2("hot", "cold"), F(1, 8))

    def test_fast_and_slow_differ_on_primitive_axes(self):
        # v0.5.1 fixed fast/slow to differ on positive_negative and
        # active_stative as well as their opposite_of relation target.
        # In the primitives subspace, they now differ on two axes.
        prim_d = self._prim_d2("fast", "slow")
        self.assertGreater(prim_d, 0)
        # And the full carrier distance is also nonzero.
        full_d = self.d2("fast", "slow")
        self.assertGreater(full_d, 0)

    def test_energy_is_closer_to_force_than_to_water(self):
        # Both energy and force are abstract physics quantities with
        # physical dimensions.  Water is a concrete noun with no physical
        # dims.  In the primitives subspace, energy is closer to force.
        d_energy_force = self._prim_d2("energy", "force")
        d_energy_water = self._prim_d2("energy", "water")
        self.assertLess(d_energy_force, d_energy_water)

    def test_math_concepts_cluster_away_from_matter(self):
        # lattice, reflection, monster, golay are all abstract math.
        # water is concrete.  Distance (in the primitives subspace) to
        # water should exceed distance among themselves (in aggregate).
        math_names = ["lattice", "reflection", "monster", "golay"]
        within_math = max(self._prim_d2(a, b) for a, b in _b_pairs(math_names))
        to_water = max(self._prim_d2(m, "water") for m in math_names)
        self.assertGreater(to_water, within_math,
                           f"within-math max={within_math}, to-water max="
                           f"{to_water}")

    def _prim_d2(self, a: str, b: str) -> Fraction:
        """Distance² in the ten-primitive subspace (coords 0..9 only).

        The full carrier's predicate/object indices dominate the Griess
        metric because they are integers while primitives are Fractions
        in [0, 1].  Restricting to the primitives subspace gives a real
        semantic distance, which is what these tests are about.

        The metric module requires 24-coordinate inputs, so we zero-pad
        the 10 primitive values to 24.
        """
        from glm_universal.reasoning.metric import distance2
        a_obj = self.objs[a]
        b_obj = self.objs[b]
        a_prim = list(a_obj.carrier[:10]) + [F(0)] * 14
        b_prim = list(b_obj.carrier[:10]) + [F(0)] * 14
        return distance2(a_prim, b_prim)


def b_pair(names):
    """Deprecated; use _b_pairs instead."""
    return _b_pairs(names)


if __name__ == "__main__":
    unittest.main()
