"""Test suite for ``glm_universal.data_objects``.

The suite is organised around the two-legged losslessness contract: for every
one of the 660 physics quantities, all 118 elements, the mathematical
collection and the sample lexicon, both

    ``class_stack_rebuild(class_stack(v)) == v``      (substrate leg)
    ``decode(encode(x)) == x``                        (semantic leg)

are asserted.  Tests that would pass vacuously are avoided: the negative
controls below deliberately corrupt carriers and assert that the codecs
*notice*, because a decoder that never rejects anything is not validating.
"""

from __future__ import annotations

import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from glm_universal import data_objects as do              # noqa: E402
from glm_universal.substrate import digit_stack, leech2, mog   # noqa: E402
from glm_universal.data_objects import base                # noqa: E402


# ===========================================================================
# 1.  EXACTNESS
# ===========================================================================

class TestExactness(unittest.TestCase):
    """No float may enter a carrier, by any route."""

    def test_float_is_refused(self):
        for bad in (1.0, 0.5, -3.25, float("inf")):
            with self.assertRaises(TypeError):
                base.as_exact(bad)

    def test_bool_is_refused(self):
        with self.assertRaises(TypeError):
            base.as_exact(True)

    def test_decimal_string_is_exact(self):
        self.assertEqual(base.as_exact("1.0080"), Fraction(126, 125))
        self.assertEqual(base.as_exact("0.1"), Fraction(1, 10))
        self.assertNotEqual(base.as_exact("0.1"), Fraction(0.1))

    def test_data_object_rejects_float_carrier(self):
        with self.assertRaises(TypeError):
            do.DataObject(name="bad", domain="test",
                          carrier=[1.5] + [0] * 23)

    def test_registers_contain_no_floats(self):
        """Every numeric field of both frozen snapshots parses as a rational."""
        data_dir = _ROOT / "glm_universal" / "data_objects" / "_data"
        for fname in ("physics_660.json", "elements_118.json",
                      "diatomics.json"):
            raw = json.loads((data_dir / fname).read_text(encoding="utf-8"))
            self._assert_no_floats(raw, fname)

    def _assert_no_floats(self, node, where):
        if isinstance(node, float):
            self.fail(f"{where}: a float appears in the frozen snapshot")
        if isinstance(node, dict):
            for v in node.values():
                self._assert_no_floats(v, where)
        elif isinstance(node, list):
            for v in node:
                self._assert_no_floats(v, where)


# ===========================================================================
# 2.  DYNAMIC STACK PARAMETERS
# ===========================================================================

class TestDynamicParameters(unittest.TestCase):
    """Depth and offset are measured from the data, never assumed."""

    def test_containment_holds_for_derived_parameters(self):
        cases = [
            [0] * 24,
            [1] * 24,
            [-1] * 24,
            [Fraction(3, 4)] * 24,
            [Fraction(1, 3)] * 24,
            [Fraction(10 ** 30), Fraction(-10 ** 30)] + [0] * 22,
            [Fraction(1, 10 ** 25)] + [0] * 23,
            list(range(-12, 12)),
        ]
        for v in cases:
            with self.subTest(v=str(v[:3])):
                p = do.derive_dynamic_parameters(v)
                self.assertTrue(p.contains())
                ints, den = digit_stack._clear_denominators(tuple(v))
                for c in ints:
                    self.assertGreaterEqual(c + p.offset, 0)
                    self.assertLessEqual(c + p.offset,
                                         p.shifted_upper_bound())

    def test_no_hardcoded_depth_ceiling(self):
        """A carrier at 10^40 stacks at the depth its range demands."""
        v = [Fraction(10 ** 40)] + [0] * 23
        p = do.derive_dynamic_parameters(v)
        self.assertGreater(p.depth, 130)
        obj = do.DataObject(name="huge", domain="test", carrier=v)
        self.assertTrue(obj.round_trip_ok())
        self.assertEqual(obj.rebuild()[0], Fraction(10 ** 40))

    def test_depth_is_least_admissible(self):
        """One plane fewer must not suffice."""
        v = [Fraction(1000)] + [0] * 23
        p = do.derive_dynamic_parameters(v)
        self.assertTrue(digit_stack.stack_is_faithful(v, p.depth, p.offset))
        with self.assertRaises(ValueError):
            digit_stack.class_stack(v, depth=p.depth - 1, offset=p.offset)

    def test_deeper_planes_are_zero(self):
        """Raising the depth above the minimum only appends empty planes."""
        v = [Fraction(37), Fraction(-8)] + [0] * 22
        p = do.derive_dynamic_parameters(v)
        for extra in (1, 5, 20):
            deep = digit_stack.class_stack(v, depth=p.depth + extra,
                                           offset=p.offset)
            self.assertEqual(deep.planes[:p.depth],
                             digit_stack.class_stack(
                                 v, depth=p.depth, offset=p.offset).planes)
            self.assertTrue(all(x == 0 for x in deep.planes[p.depth:]))
            self.assertEqual(digit_stack.class_stack_rebuild(deep),
                             tuple(v))

    def test_dyadic_exponent(self):
        self.assertEqual(do.dyadic_exponent([0] * 24), 0)
        self.assertEqual(do.dyadic_exponent([Fraction(3, 8)] + [0] * 23), 3)
        self.assertEqual(do.dyadic_exponent([Fraction(1, 2), Fraction(1, 16)]
                                            + [0] * 22), 4)
        self.assertIsNone(do.dyadic_exponent([Fraction(1, 3)] + [0] * 23))
        self.assertIsNone(do.dyadic_exponent([Fraction(1, 12)] + [0] * 23))

    def test_dyadic_exponent_absent_for_the_physics_register(self):
        """The plan's ``2^O v in Z^24`` route does not cover this data.

        Denominator 12 is not a power of two, so a purely dyadic rescaling
        cannot clear these carriers.  The general LCD route does, which is why
        the codecs use it.
        """
        lossy = [q for q in do.load_physics_register()
                 if any(e.denominator == 12 or e.denominator == 3
                        for e in q.exps_ext10)]
        for q in lossy[:5]:
            obj = do.PhysicsCodec().encode(q)
            self.assertIsNone(do.dyadic_exponent(obj.carrier))
            self.assertTrue(obj.round_trip_ok())

    def test_wrong_length_rejected(self):
        with self.assertRaises(ValueError):
            do.derive_dynamic_parameters([1, 2, 3])


# ===========================================================================
# 3.  PHYSICS -- all 660
# ===========================================================================

class TestPhysics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.register = do.load_physics_register()
        cls.codec = do.PhysicsCodec()

    def test_register_holds_660_concepts(self):
        self.assertEqual(len(self.register), 660)
        self.assertEqual(len({q.name for q in self.register}), 660)

    def test_axes(self):
        self.assertEqual(do.AXES_EXT10,
                         ("L", "M", "T", "I", "H", "N", "J", "A", "S", "B"))
        self.assertEqual(do.AXES_SI7, ("L", "M", "T", "I", "H", "N", "J"))
        self.assertEqual(len(do.PHYSICS_LAYOUT), 24)

    def test_all_660_round_trip(self):
        """Both legs, for every quantity in the register."""
        for q in self.register:
            with self.subTest(quantity=q.name):
                obj = self.codec.encode(q)
                self.assertTrue(obj.round_trip_ok(),
                                f"substrate leg failed for {q.name}")
                self.assertEqual(self.codec.decode(obj), q,
                                 f"semantic leg failed for {q.name}")

    def test_all_660_pass_the_codec_contract(self):
        for q in self.register:
            with self.subTest(quantity=q.name):
                self.codec.check(q)

    def test_si7_slice_matches_ext10_prefix(self):
        for q in self.register:
            with self.subTest(quantity=q.name):
                obj = self.codec.encode(q)
                self.assertEqual(tuple(base.as_exact(x)
                                       for x in obj.carrier[10:17]),
                                 q.exps_ext10[:7])

    def test_fractional_exponents_survive(self):
        frac = [q for q in self.register
                if any(e.denominator != 1 for e in q.exps_ext10)]
        self.assertEqual(len(frac), 6)
        for q in frac:
            with self.subTest(quantity=q.name):
                decoded = self.codec.decode(self.codec.encode(q))
                self.assertEqual(decoded.exps_ext10, q.exps_ext10)
                self.assertTrue(any(e.denominator != 1
                                    for e in decoded.exps_ext10))

    def test_known_dimensions(self):
        cases = {
            "energy": "L^2 M T^-2",
            "force": "L M T^-2",
            "length": "L",
            "speed": "L T^-1",
            "torque": "L^2 M T^-2 A^-1",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(
                    do.quantity_by_name(name).dimension_string("EXT10"),
                    expected)

    def test_torque_and_energy_separate_only_in_ext10(self):
        energy = do.quantity_by_name("energy")
        torque = do.quantity_by_name("torque")
        self.assertEqual(energy.exps_si7, torque.exps_si7)
        self.assertNotEqual(energy.exps_ext10, torque.exps_ext10)
        self.assertFalse(do.si7_projection_lossy(energy))
        self.assertTrue(do.si7_projection_lossy(torque))

    def test_ext10_resolves_more_than_si7(self):
        report = do.basis_collision_report()
        self.assertEqual(report["concepts"], 660)
        self.assertLess(report["EXT10"]["colliding_pairs"],
                        report["SI7"]["colliding_pairs"])
        self.assertGreater(report["ext10_resolves_extra_pairs"], 0)

    def test_internally_inconsistent_carrier_is_rejected(self):
        """A tampered SI7 slice must be caught, not silently accepted."""
        obj = self.codec.encode(do.quantity_by_name("energy"))
        broken = list(obj.carrier)
        broken[10] = broken[10] + 1
        tampered = do.DataObject(name=obj.name, domain=obj.domain,
                                 carrier=broken, attributes=obj.attributes,
                                 layout=obj.layout)
        with self.assertRaises(ValueError):
            self.codec.decode(tampered)

    def test_unknown_name(self):
        with self.assertRaises(KeyError):
            do.quantity_by_name("no_such_quantity")

    def test_coordinate_lookup_by_label(self):
        obj = self.codec.encode(do.quantity_by_name("energy"))
        self.assertEqual(obj.coordinate("ext10.L"), 2)
        self.assertEqual(obj.coordinate("ext10.T"), -2)
        self.assertEqual(len(obj.labelled()), 24)


# ===========================================================================
# 4.  CHEMISTRY -- all 118
# ===========================================================================

class TestElements(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.register = do.load_element_register()
        cls.codec = do.ElementCodec()

    def test_register_holds_118_elements(self):
        self.assertEqual(len(self.register), 118)
        self.assertEqual(sorted(e.z for e in self.register),
                         list(range(1, 119)))
        self.assertEqual(len({e.symbol for e in self.register}), 118)

    def test_all_118_round_trip(self):
        for e in self.register:
            with self.subTest(element=e.symbol):
                obj = self.codec.encode(e)
                self.assertTrue(obj.round_trip_ok(),
                                f"substrate leg failed for {e.symbol}")
                self.assertEqual(self.codec.decode(obj), e,
                                 f"semantic leg failed for {e.symbol}")

    def test_all_118_pass_the_codec_contract(self):
        for e in self.register:
            with self.subTest(element=e.symbol):
                self.codec.check(e)

    def test_missing_values_survive_as_none(self):
        """A missing field must decode to ``None``, never to a measured 0."""
        og = do.element_by_symbol("Og")
        self.assertIsNone(og.electronegativity_pauling)
        decoded = self.codec.decode(self.codec.encode(og))
        self.assertIsNone(decoded.electronegativity_pauling)
        self.assertIsNone(decoded.covalent_radius_pm)
        self.assertEqual(decoded, og)

    def test_missing_mask_is_consistent(self):
        for e in self.register:
            with self.subTest(element=e.symbol):
                obj = self.codec.encode(e)
                mask = int(obj.coordinate("missing_mask"))
                for i, fname in enumerate(do.MEASURED_FIELDS):
                    absent = bool((mask >> i) & 1)
                    self.assertEqual(absent, e.field(fname) is None,
                                     f"{e.symbol}.{fname} mask disagrees")
                    if absent:
                        self.assertEqual(obj.carrier[1 + i], 0)

    def test_measured_zero_is_distinguishable_from_missing(self):
        """A genuine 0 and an absent value must not collide."""
        real_zero = do.Element(z=1, symbol="Zz", name="Test",
                               electron_configuration="1s1",
                               electronegativity_pauling=Fraction(0))
        absent = do.Element(z=1, symbol="Zz", name="Test",
                            electron_configuration="1s1",
                            electronegativity_pauling=None)
        a = self.codec.encode(real_zero)
        b = self.codec.encode(absent)
        self.assertNotEqual(a.carrier, b.carrier)
        self.assertEqual(self.codec.decode(a).electronegativity_pauling,
                         Fraction(0))
        self.assertIsNone(self.codec.decode(b).electronegativity_pauling)

    def test_exact_atomic_weights(self):
        h = do.element_by_symbol("H")
        self.assertEqual(h.atomic_weight_u, Fraction(126, 125))
        self.assertIsInstance(h.atomic_weight_u, Fraction)
        c = do.element_by_symbol("C")
        self.assertEqual(c.atomic_weight_u.denominator > 1, True)

    def test_period_derivation(self):
        self.assertEqual(do.period_of(1), 1)
        self.assertEqual(do.period_of(2), 1)
        self.assertEqual(do.period_of(3), 2)
        self.assertEqual(do.period_of(18), 3)
        self.assertEqual(do.period_of(57), 6)
        self.assertEqual(do.period_of(118), 7)
        for bad in (0, 119, -1):
            with self.assertRaises(ValueError):
                do.period_of(bad)

    def test_valence_electron_derivation(self):
        """Derived from the configuration; checked against main-group truth."""
        expected = {"H": 1, "He": 2, "Li": 1, "C": 4, "N": 5, "O": 6,
                    "F": 7, "Ne": 8, "Na": 1, "Cl": 7, "Ar": 8}
        for sym, ve in expected.items():
            with self.subTest(symbol=sym):
                self.assertEqual(do.element_by_symbol(sym).valence_electrons,
                                 ve)

    def test_predicted_configurations_decline_valence(self):
        for sym in ("Ts", "Og"):
            with self.subTest(symbol=sym):
                e = do.element_by_symbol(sym)
                self.assertIn("predicted", e.electron_configuration)
                self.assertIsNone(e.valence_electrons)

    def test_golay_addresses_are_distinct_and_separated(self):
        report = do.periodic_separation_report()
        self.assertEqual(report["elements"], 118)
        self.assertEqual(report["distinct_codewords"], 118)
        self.assertEqual(report["pairs_compared"], 118 * 117 // 2)
        self.assertGreaterEqual(report["minimum_separation"], 8)
        self.assertTrue(report["meets_golay_bound"])

    def test_golay_addresses_are_codewords(self):
        for z in range(1, 119):
            with self.subTest(z=z):
                addr = do.golay_address(z)
                self.assertIn(addr["codeword"], mog.GOLAY_SET)
                self.assertIn(addr["weight"], (0, 8, 12, 16, 24))
                self.assertEqual(addr["brick0_weight"] + addr["brick1_weight"]
                                 + addr["brick2_weight"], addr["weight"])

    def test_corrupted_golay_address_is_rejected(self):
        obj = self.codec.encode(do.element_by_symbol("C"))
        broken = list(obj.carrier)
        broken[18] = broken[18] + 1
        tampered = do.DataObject(name=obj.name, domain=obj.domain,
                                 carrier=broken, attributes=obj.attributes,
                                 layout=obj.layout)
        with self.assertRaises(ValueError):
            self.codec.decode(tampered)

    def test_lookup_helpers(self):
        self.assertEqual(do.element_by_z(6).symbol, "C")
        self.assertEqual(do.element_by_symbol("Fe").z, 26)
        with self.assertRaises(KeyError):
            do.element_by_symbol("Xx")

    def test_diatomic_register(self):
        dia = do.load_diatomic_register()
        self.assertEqual(len(dia), 52)
        homo = [d for d in dia if d.homonuclear]
        self.assertGreater(len(homo), 0)
        for d in dia:
            with self.subTest(species=d.species):
                if d.d0_kJ_per_mol is not None:
                    self.assertIsInstance(d.d0_kJ_per_mol, Fraction)
                    self.assertGreater(d.d0_kJ_per_mol, 0)

    def test_high_denominator_element_forces_deep_stack(self):
        """Densities with 10^-8 precision drive the depth well past ten."""
        obj = self.codec.encode(do.element_by_symbol("H"))
        p = obj.parameters()
        self.assertGreater(p.denominator, 1)
        self.assertGreater(p.depth, digit_stack.STACK_DEPTH)
        self.assertTrue(obj.round_trip_ok())


# ===========================================================================
# 5.  MATHEMATICS
# ===========================================================================

class TestMathematics(unittest.TestCase):

    def test_matrix_round_trip_all_shapes(self):
        codec = do.MatrixCodec()
        for r in range(1, 25):
            for c in range(1, 25):
                if r * c > 24:
                    continue
                with self.subTest(shape=(r, c)):
                    entries = tuple(Fraction(i + 1, (i % 5) + 1)
                                    for i in range(r * c))
                    m = do.RationalMatrix(name=f"m{r}x{c}", rows=r, cols=c,
                                          entries=entries)
                    obj = codec.check(m)
                    self.assertTrue(obj.round_trip_ok())

    def test_shape_is_preserved(self):
        """A 2x5 and a 5x2 with the same entries must not decode alike."""
        codec = do.MatrixCodec()
        entries = tuple(Fraction(i) for i in range(10))
        a = do.RationalMatrix(name="a", rows=2, cols=5, entries=entries)
        b = do.RationalMatrix(name="a", rows=5, cols=2, entries=entries)
        self.assertEqual(codec.encode(a).carrier, codec.encode(b).carrier)
        self.assertNotEqual(codec.decode(codec.encode(a)),
                            codec.decode(codec.encode(b)))

    def test_oversized_matrix_rejected(self):
        with self.assertRaises(ValueError):
            do.RationalMatrix(name="too_big", rows=5, cols=5,
                              entries=tuple(Fraction(i) for i in range(25)))

    def test_exact_shapes_fill_the_carrier(self):
        for r, c in do.EXACT_SHAPES:
            with self.subTest(shape=(r, c)):
                self.assertEqual(r * c, 24)
                m = do.RationalMatrix(name="f", rows=r, cols=c,
                                      entries=tuple(Fraction(1)
                                                    for _ in range(24)))
                self.assertTrue(m.fills_carrier)

    def test_mog_frame_shape(self):
        m = do.RationalMatrix(name="frame", rows=4, cols=6,
                              entries=tuple(Fraction(i) for i in range(24)))
        self.assertTrue(m.is_mog_frame)
        obj = do.MatrixCodec().encode(m)
        grid = obj.mog_grid()
        self.assertEqual(len(grid), 4)
        self.assertEqual(len(grid[0]), 6)

    def test_transpose_is_an_involution(self):
        m = do.RationalMatrix.from_rows(
            "t", [[Fraction(1), Fraction(2), Fraction(3)],
                  [Fraction(4), Fraction(5), Fraction(6)]])
        self.assertEqual(m.transpose().transpose().entries, m.entries)

    def test_matrix_product_is_exact(self):
        a = do.RationalMatrix.from_rows(
            "a", [[Fraction(1, 3), Fraction(2, 7)],
                  [Fraction(3, 11), Fraction(5, 13)]])
        identity = do.RationalMatrix.from_rows(
            "I", [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])
        self.assertEqual(do.compose_matrices(a, identity).entries, a.entries)

    def test_reflection_is_an_exact_involution(self):
        """Twice-reflected is identically equal, not merely close."""
        roots = [
            [Fraction(1)] + [Fraction(0)] * 23,
            [Fraction(1, 3)] * 24,
            [Fraction(i + 1) for i in range(24)],
        ]
        vectors = [
            [Fraction(i - 12) for i in range(24)],
            [Fraction(1, 7)] * 24,
        ]
        for root in roots:
            ref = do.Reflection(name="r", root=tuple(root))
            for v in vectors:
                with self.subTest(root=str(root[:2]), v=str(v[:2])):
                    once = ref.apply(v)
                    twice = ref.apply(once)
                    self.assertEqual(twice, tuple(v))
                    self.assertTrue(ref.is_involution_on(v))

    def test_reflection_preserves_the_inner_product(self):
        ref = do.Reflection(name="r",
                            root=tuple([Fraction(1), Fraction(-1)]
                                       + [Fraction(0)] * 22))
        x = [Fraction(i) for i in range(24)]
        y = [Fraction(24 - i) for i in range(24)]
        before = sum((a * b for a, b in zip(x, y)), Fraction(0))
        rx, ry = ref.apply(x), ref.apply(y)
        after = sum((a * b for a, b in zip(rx, ry)), Fraction(0))
        self.assertEqual(before, after)

    def test_reflection_round_trip(self):
        codec = do.ReflectionCodec()
        for root in ([Fraction(1)] + [Fraction(0)] * 23,
                     [Fraction(1, 5)] * 24):
            with self.subTest(root=str(root[:2])):
                codec.check(do.Reflection(name="r", root=tuple(root)))

    def test_zero_root_rejected(self):
        with self.assertRaises(ValueError):
            do.Reflection(name="zero", root=tuple([Fraction(0)] * 24))

    def test_leech_minimal_vector_is_a_2a_axis(self):
        minimal = next(iter(leech2.minimal_vectors()))
        ref = do.Reflection(name="min", root=tuple(Fraction(x)
                                                   for x in minimal))
        self.assertEqual(leech2.norm2(list(minimal)), 32)
        self.assertTrue(ref.is_2a_axis())

    def test_non_lattice_root_is_not_an_axis(self):
        """Must return False, not raise -- the substrate raises here."""
        ref = do.Reflection(name="e0",
                            root=tuple([Fraction(1)] + [Fraction(0)] * 23))
        self.assertFalse(ref.is_2a_axis())
        ref2 = do.Reflection(name="thirds", root=tuple([Fraction(1, 3)] * 24))
        self.assertFalse(ref2.is_2a_axis())

    def test_field_elements_round_trip(self):
        codec = do.FieldElementCodec()
        for idx in (0, 1, 17, 4095):
            word = mog.GOLAY_MASKS[idx]
            symbols = tuple((word >> i) & 1 for i in range(24))
            with self.subTest(gf2=idx):
                obj = codec.check(do.FieldElement(name=f"g{idx}",
                                                  field_order=2,
                                                  symbols=symbols))
                self.assertTrue(obj.attributes["is_golay_codeword"])
        for i, word in enumerate(mog.HEXACODE.words[:8]):
            with self.subTest(gf4=i):
                obj = codec.check(do.FieldElement(
                    name=f"h{i}", field_order=4,
                    symbols=tuple(int(s) for s in word)))
                self.assertTrue(obj.attributes["is_hexacode_word"])

    def test_field_element_validation(self):
        with self.assertRaises(ValueError):
            do.FieldElement(name="bad", field_order=3, symbols=(0,))
        with self.assertRaises(ValueError):
            do.FieldElement(name="short", field_order=2, symbols=(0, 1))
        with self.assertRaises(ValueError):
            do.FieldElement(name="range", field_order=4,
                            symbols=(0, 1, 2, 3, 4, 0))

    def test_non_codeword_is_not_claimed_to_be_one(self):
        symbols = tuple(1 if i == 0 else 0 for i in range(24))
        fe = do.FieldElement(name="weight1", field_order=2, symbols=symbols)
        self.assertFalse(fe.is_golay_codeword())

    def test_collection_round_trips(self):
        objs = do.mathematics_objects()
        self.assertGreaterEqual(len(objs), 20)
        for obj in objs:
            with self.subTest(name=obj.name):
                self.assertTrue(obj.round_trip_ok())


# ===========================================================================
# 6.  LEXICON
# ===========================================================================

class TestLexicon(unittest.TestCase):

    def test_vocabulary_is_stable_and_invertible(self):
        v = do.Vocabulary()
        a = v.intern("alpha")
        b = v.intern("beta")
        self.assertEqual(v.intern("alpha"), a)
        self.assertNotEqual(a, b)
        self.assertEqual(v.token(a), "alpha")
        self.assertEqual(v.token(0), "")
        self.assertGreater(a, 0)

    def test_vocabulary_order_is_deterministic(self):
        """Two independently built vocabularies must agree exactly."""
        self.assertEqual(do.default_vocabulary().tokens(),
                         do.default_vocabulary().tokens())

    def test_unknown_token_and_index(self):
        v = do.Vocabulary(["known"])
        with self.assertRaises(KeyError):
            v.index("unknown")
        with self.assertRaises(KeyError):
            v.token(9999)

    def test_sample_lexicon_round_trips(self):
        objs, codec = do.lexicon_objects()
        self.assertEqual(len(objs), 10)
        for obj, concept in zip(objs, do.lexicon.SAMPLE_CONCEPTS):
            with self.subTest(name=obj.name):
                self.assertTrue(obj.round_trip_ok())
                self.assertEqual(codec.decode(obj), concept)

    def test_empty_concept_round_trips(self):
        codec = do.LexiconCodec()
        codec.check(do.Concept("solo"))

    def test_saturated_concept_round_trips(self):
        codec = do.LexiconCodec()
        c = do.Concept("full", "noun",
                       tuple((f"p{i}", f"o{i}") for i in range(8)),
                       ("singular", "abstract", "countable"))
        codec.check(c)

    def test_overfull_concept_is_rejected_not_truncated(self):
        with self.assertRaises(ValueError):
            do.Concept("toomany", "noun",
                       tuple((f"p{i}", f"o{i}") for i in range(9)))
        with self.assertRaises(ValueError):
            do.Concept("toofeaturey", "noun", (),
                       ("singular", "plural", "animate", "abstract"))

    def test_unknown_pos_and_feature_rejected(self):
        with self.assertRaises(ValueError):
            do.Concept("x", "gerundive")
        with self.assertRaises(ValueError):
            do.Concept("x", "noun", (), ("nonexistent_feature",))

    def test_checksum_catches_corruption(self):
        codec = do.LexiconCodec(do.default_vocabulary())
        obj = codec.encode(do.lexicon.SAMPLE_CONCEPTS[0])
        broken = list(obj.carrier)
        broken[7] = broken[7] + 1
        tampered = do.DataObject(name=obj.name, domain=obj.domain,
                                 carrier=broken, attributes=obj.attributes,
                                 layout=obj.layout)
        with self.assertRaises(ValueError):
            codec.decode(tampered)

    def test_triples(self):
        c = do.Concept("water", "noun", (("is_a", "compound"),))
        self.assertEqual(c.triples(), (("water", "is_a", "compound"),))
        self.assertEqual(c.arity, 1)

    def test_no_hashing_is_used(self):
        """The module must not rely on ``hash``, which is salted per process."""
        src = (_ROOT / "glm_universal" / "data_objects" /
               "lexicon.py").read_text(encoding="utf-8")
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue
            self.assertNotIn("hash(", stripped)


# ===========================================================================
# 7.  GEOMETRY AND CROSS-DOMAIN INVARIANTS
# ===========================================================================

class TestGeometry(unittest.TestCase):

    def test_mog_presentations_are_bijective(self):
        obj = do.PhysicsCodec().encode(do.quantity_by_name("energy"))
        self.assertEqual(mog.from_grid_4x6(obj.mog_grid()),
                         list(obj.carrier))
        self.assertEqual(mog.from_trio_3x8(obj.mog_trio()),
                         list(obj.carrier))

    def test_plane_grids_match_the_stack(self):
        obj = do.ElementCodec().encode(do.element_by_symbol("C"))
        grids = obj.plane_grids()
        self.assertEqual(len(grids), obj.stack().depth)
        for grid, plane in zip(grids, obj.stack().planes):
            bits = mog.from_grid_4x6(grid)
            self.assertEqual(sum(b << i for i, b in enumerate(bits)), plane)

    def test_facet_signature_covers_31_facets(self):
        obj = do.PhysicsCodec().encode(do.quantity_by_name("force"))
        sig = obj.facet_signature()
        self.assertEqual(len(sig), 31)
        self.assertEqual(set(sig), set(digit_stack.FACETS))
        self.assertTrue(all(v >= 0 for v in sig.values()))

    def test_facet_signature_sums_consistently(self):
        """Brick weights partition each plane, so they must total its weight."""
        obj = do.ElementCodec().encode(do.element_by_symbol("O"))
        sig = obj.facet_signature()
        total = sum(bin(p).count("1") for p in obj.stack().planes)
        self.assertEqual(sig["brick0"] + sig["brick1"] + sig["brick2"], total)
        self.assertEqual(sum(sig[f"col{c}"] for c in range(6)), total)
        self.assertEqual(sum(sig[f"row{r}"] for r in range(4)), total)

    def test_monster_address_is_honest_about_lattice_membership(self):
        obj = do.PhysicsCodec().encode(do.quantity_by_name("energy"))
        addr = obj.monster_address()
        self.assertIn("carrier_in_leech_lattice", addr)
        if not addr["carrier_in_leech_lattice"]:
            self.assertIsNone(addr["leech_class"])
            self.assertIn("note", addr)

    def test_leech_point_carrier_reports_its_class(self):
        minimal = list(next(iter(leech2.minimal_vectors())))
        obj = do.DataObject(name="min", domain="mathematics", carrier=minimal)
        addr = obj.monster_address()
        self.assertTrue(addr["carrier_is_integral"])
        self.assertTrue(addr["carrier_in_leech_lattice"])
        self.assertEqual(addr["leech_norm2"], 32)
        self.assertTrue(addr["is_2a_axis"])

    def test_golay_alignment_reports_distance(self):
        obj = do.ElementCodec().encode(do.element_by_symbol("H"))
        align = obj.golay_alignment()
        self.assertGreaterEqual(align["distance_to_code"], 0)
        self.assertLessEqual(align["distance_to_code"], 24)
        if align["distance_to_code"] > 3:
            self.assertFalse(align["uniquely_decodable"])

    def test_serialisation_round_trip(self):
        obj = do.ElementCodec().encode(do.element_by_symbol("Fe"))
        text = do.carrier_to_json(obj.carrier)
        self.assertTrue(all(isinstance(s, str) for s in text))
        self.assertEqual(do.carrier_from_json(text), obj.carrier)
        json.dumps(obj.as_dict())   # must be JSON-serialisable


class TestCrossDomain(unittest.TestCase):

    def test_every_object_round_trips(self):
        """The whole catalogue, in one sweep."""
        catalogue = do.all_objects()
        total = 0
        for domain in ("physics", "chemistry", "mathematics", "lexicon"):
            for obj in catalogue[domain]:
                with self.subTest(domain=domain, name=obj.name):
                    self.assertTrue(obj.round_trip_ok())
                total += 1
        self.assertGreaterEqual(total, 660 + 118 + 20 + 10)

    def test_every_carrier_has_24_coordinates(self):
        catalogue = do.all_objects()
        for domain in ("physics", "chemistry", "mathematics", "lexicon"):
            for obj in catalogue[domain]:
                with self.subTest(domain=domain, name=obj.name):
                    self.assertEqual(len(obj.carrier), 24)
                    self.assertEqual(len(obj.layout), 24)

    def test_no_carrier_holds_a_float(self):
        catalogue = do.all_objects()
        for domain in ("physics", "chemistry", "mathematics", "lexicon"):
            for obj in catalogue[domain]:
                for c in obj.carrier:
                    self.assertNotIsInstance(c, float)
                    self.assertIn(type(c), (int, Fraction))

    def test_parameters_are_admissible_everywhere(self):
        catalogue = do.all_objects()
        for domain in ("physics", "chemistry", "mathematics", "lexicon"):
            for obj in catalogue[domain]:
                with self.subTest(domain=domain, name=obj.name):
                    self.assertTrue(obj.parameters().contains())

    def test_module_default_depth_is_insufficient_for_chemistry(self):
        """A fixed depth of ten would fail; the dynamic derivation is required.

        This is the test that would break if anyone reintroduced a hardcoded
        depth constant into the codec path.
        """
        obj = do.ElementCodec().encode(do.element_by_symbol("H"))
        with self.assertRaises(ValueError):
            digit_stack.class_stack(obj.carrier,
                                    depth=digit_stack.STACK_DEPTH,
                                    offset=digit_stack.STACK_OFFSET)
        self.assertTrue(obj.round_trip_ok())


if __name__ == "__main__":
    unittest.main(verbosity=2)
