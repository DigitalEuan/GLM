#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM TEST SUITE
================================================================================

  Run:   python3 test_glm.py            (all tests, ~30 s)
         python3 test_glm.py -v         (verbose)
         python3 -m unittest test_glm.TestCodec   (one class)

  The suite covers all six modules and enforces the invariants I1-I6 listed in
  the paper (glm_paper.py, section 10).  Where a property is small enough to
  check exhaustively, it is checked exhaustively (the 16 column states, the
  4096 codewords, the 4096 cosets, sub-boxes of the exponent lattice); where
  it is not, the sweep is deterministic pseudo-random so failures reproduce.

  Test classes
  ------------
    TestGolay          code parameters, syndromes, decoding, ties
    TestHexacodeMOG    GF(4), the hexacode, the MOG alignment
    TestLeech          minimal-vector classes, the cost layer
    TestColumnCodec    the 16-state bijection
    TestCodec          the 24-bit codec and the dimension carrier
    TestDimension      the group (Z^7,+) and its laws
    TestLibrary        the quantity library's internal consistency
    TestParser         the expression parser, including its error paths
    TestEquationAudit  exact verdicts and the mod-2 shadow
    TestLinalg         Smith normal form, kernels, integer/rational solving
    TestReasoner       concepts, audit, synthesis, Pi groups, scene export
    TestUpperTiers     code automorphisms, 2^(1+24), the snap algebra
    TestNormaliser     the semidirect product 2^(1+24) : S_12
    TestGeometry       versors, quaternionic fibres, winding, holonomy,
                       the conformal grading, vacua, colour
    TestMoonshine      the Leech line census, the 196,884 ledger, the head of
                       J, the Jordan layer
    TestPaper          every numbered claim of the paper
================================================================================
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from fractions import Fraction
from typing import List

from glm_codec import (CARRIER_CAPACITY, DIM_MAX, DIM_MIN, ColumnCodec,
                       DimCarrier, MOGCodec, ontological_profile)
from glm_linalg import (kernel_basis, matmul, matvec, smith_normal_form,
                        solve_integer_system, solve_rational_system)
from glm_metrology import (ALIASES, DIM_NAMES, QUANTITIES, Dimension,
                           ParseError, audit_equation, dimensional_collisions,
                           mod2_box_census, mod2_collapse_report,
                           mod2_perturbation_sweep, mod2_shadow,
                           mod2_would_accept, parse_expression, resolve)
from glm_geometry import (Q_I, Q_J, Q_K, Q_ONE, QUATERNION_OF_FIBRE,
                          Quaternion, chromatic_ground_states, colour_of_word,
                          colour_report, conformal_grading_report,
                          fibre_keys, fibre_noncommutativity_report,
                          fibre_product, h6_norm_sq, holonomy,
                          quaternion_group_report, vacuum_census,
                          versor_index, walk_of_names, winding_report,
                          word_of_colour)
from glm_m24 import (BASE_POINTS, M24_GENERATORS, StabChain, code_automorphisms,
                     compose, cycles, identity_perm, inverse, m24_report,
                     octad_orbit, permute_word, preserves_code, schreier_sims,
                     sextet_of, subgroup_census)
from glm_monster import (IDENTITY_PERM, ExtraspecialElement,
                         NormaliserElement, SchrodingerRep, SnapAlgebra,
                         act_on_element, column_symmetry_report,
                         extraspecial_relation_report,
                         golay_permutation_check, normaliser_report,
                         perm_compose, perm_inverse, permute_bits,
                         snap_algebra_report, visual_24d_commutator_check)
from glm_moonshine import (JordanElement, class_c_indexing_report,
                           dimension_ledger, eta_power_series,
                           hamming_inner_product_report,
                           jordan_algebra_report, leech_voa_head, line_census)
from glm_paper import CLAIMS, run_paper
from glm_reasoner import (REASONER, Concept, GeometricReasoner,
                          derive_substrate)
from glm_substrate import GF4, GOLAY, HEXACODE, LEECH, MOG, PI, Y, BitOps


def prng(seed: int, count: int, bits: int = 24) -> List[List[int]]:
    """A deterministic stream of bit vectors, so any failure reproduces."""
    out = []
    state = seed
    for _ in range(count):
        state = (1103515245 * state + 12345) & ((1 << bits) - 1)
        out.append(BitOps.from_int(state, bits))
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  SUBSTRATE
# ══════════════════════════════════════════════════════════════════════════════

class TestGolay(unittest.TestCase):

    def test_dimensions_and_count(self):
        self.assertEqual(len(GOLAY.all_codewords()), 4096)
        self.assertEqual(len({tuple(c) for c in GOLAY.all_codewords()}), 4096)
        self.assertTrue(all(len(c) == 24 for c in GOLAY.all_codewords()))

    def test_min_distance_and_enumerator(self):
        self.assertEqual(GOLAY.min_distance(), 8)
        self.assertEqual(GOLAY.weight_enumerator(),
                         {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1})
        self.assertEqual(len(GOLAY.octads()), 759)

    def test_self_dual_and_doubly_even(self):
        self.assertTrue(GOLAY.is_self_dual())
        self.assertTrue(GOLAY.is_doubly_even())

    def test_linearity(self):
        words = GOLAY.codeword_ints()
        for a, b in zip(prng(1, 40, 12), prng(2, 40, 12)):
            ca, cb = GOLAY.encode(a), GOLAY.encode(b)
            self.assertIn(BitOps.to_int(BitOps.xor(ca, cb)), words)

    def test_syndrome_is_linear_and_zero_on_codewords(self):
        for cw in GOLAY.all_codewords()[:200]:
            self.assertEqual(GOLAY.syndrome_int(cw), 0)
            self.assertTrue(GOLAY.is_codeword(cw))
        for u, v in zip(prng(3, 50), prng(4, 50)):
            self.assertEqual(GOLAY.syndrome_int(BitOps.xor(u, v)),
                             GOLAY.syndrome_int(u) ^ GOLAY.syndrome_int(v))

    def test_syndrome_bits_match_int(self):
        for v in prng(5, 25):
            bits = GOLAY.syndrome(v)
            self.assertEqual(BitOps.to_int(bits), GOLAY.syndrome_int(v))
            self.assertEqual(sum(bits), GOLAY.syndrome_weight(v))

    def test_coset_table_is_complete(self):
        census = GOLAY.census()
        self.assertEqual(census["cosets"], 4096)
        self.assertEqual(census["leader_weight_profile"],
                         {0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771})
        self.assertEqual(census["covering_radius"], 4)

    def test_snap_lands_on_a_codeword_within_four(self):
        words = GOLAY.codeword_ints()
        for v in prng(6, 500):
            out, meta = GOLAY.snap(v)
            self.assertIn(BitOps.to_int(out), words)
            self.assertLessEqual(meta.distance, 4)
            self.assertEqual(meta.distance, BitOps.distance(v, out))

    def test_snap_corrects_up_to_three_errors_exactly(self):
        base = GOLAY.encode([1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0])
        for positions in ((), (0,), (3, 17), (1, 8, 23)):
            noisy = list(base)
            for p in positions:
                noisy[p] ^= 1
            out, meta = GOLAY.snap(noisy)
            self.assertEqual(out, base)
            self.assertEqual(meta.distance, len(positions))
            self.assertEqual(meta.tie_count, 1)
            self.assertEqual(set(meta.corrected_bits), set(positions))

    def test_distance_four_is_a_six_way_tie(self):
        leaders = GOLAY.leader_table()
        ambiguous = [s for s, mask in leaders.items() if bin(mask).count("1") == 4]
        self.assertEqual(len(ambiguous), 1771)
        for syn in ambiguous[:5]:
            word = BitOps.from_int(leaders[syn], 24)
            _out, meta = GOLAY.snap(word)
            self.assertEqual(meta.distance, 4)
            self.assertEqual(meta.tie_count, 6)
            self.assertEqual(len(GOLAY.nearest_codewords(word)), 6)
            self.assertEqual(meta.status, "ambiguous")

    def test_snap_is_idempotent(self):
        for v in prng(7, 100):
            once, _ = GOLAY.snap(v)
            twice, meta = GOLAY.snap(once)
            self.assertEqual(once, twice)
            self.assertEqual(meta.distance, 0)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            GOLAY.snap([0] * 23)
        with self.assertRaises(ValueError):
            GOLAY.encode([0] * 11)
        with self.assertRaises(ValueError):
            GOLAY.syndrome_int([0] * 25)


class TestHexacodeMOG(unittest.TestCase):

    def test_gf4_field_axioms(self):
        for a in range(4):
            self.assertEqual(GF4.add(a, 0), a)
            self.assertEqual(GF4.add(a, a), 0)
            self.assertEqual(GF4.mul(a, 1), a)
            self.assertEqual(GF4.mul(a, 0), 0)
            for b in range(4):
                self.assertEqual(GF4.add(a, b), GF4.add(b, a))
                self.assertEqual(GF4.mul(a, b), GF4.mul(b, a))
                for c in range(4):
                    self.assertEqual(GF4.mul(a, GF4.add(b, c)),
                                     GF4.add(GF4.mul(a, b), GF4.mul(a, c)))

    def test_hexacode_parameters(self):
        self.assertEqual(len(HEXACODE.words), 64)
        self.assertEqual(HEXACODE.min_distance(), 4)

    def test_hexacode_is_linear(self):
        words = HEXACODE.words
        for i in range(0, 64, 7):
            for j in range(0, 64, 11):
                total = tuple(GF4.add(a, b) for a, b in zip(words[i], words[j]))
                self.assertIn(total, HEXACODE)

    def test_mog_alignment_is_a_permutation(self):
        self.assertEqual(sorted(MOG.ALIGNED_BITS), list(range(24)))

    def test_every_codeword_casts_a_hexacode_shadow(self):
        report = MOG.verify_hexacode_shadow()
        self.assertEqual(report["failures"], 0)
        self.assertTrue(report["aligned"])

    def test_column_labels_have_equal_fibres(self):
        self.assertEqual(MOG.label_fibre_sizes(), {0: 4, 1: 4, 2: 4, 3: 4})

    def test_label_map_is_linear(self):
        for u in range(16):
            for v in range(16):
                self.assertEqual(MOG.COLUMN_LABEL[u ^ v],
                                 GF4.add(MOG.COLUMN_LABEL[u], MOG.COLUMN_LABEL[v]))

    def test_tier_gridding_shadow_is_not_claimed_to_be_hexacode(self):
        """The plain gridding may fail hexacode membership; that is expected."""
        failures = sum(1 for cw in GOLAY.all_codewords()[:500]
                       if MOG.shadow(cw, aligned=False) not in HEXACODE)
        self.assertGreater(failures, 0)


class TestLeech(unittest.TestCase):

    def test_class_sizes_and_norms(self):
        counts = {"A": 1104, "B": 97152, "C": 98304}
        for cls, expected in counts.items():
            seen = 0
            for v in LEECH.minimal_vectors(cls):
                seen += 1
                if seen % 997 == 1:                      # spot-check norms
                    self.assertEqual(sum(x * x for x in v), 32)
            self.assertEqual(seen, expected)

    def test_glue_conditions(self):
        first = {cls: next(iter(LEECH.minimal_vectors(cls))) for cls in "ABC"}
        self.assertEqual(sum(first["A"]) % 8, 0)
        self.assertEqual(sum(first["B"]) % 8, 0)
        self.assertEqual(sum(first["C"]) % 8, 4)

    def test_cost_layer_is_exact_and_monotone(self):
        zero = [0] * 24
        self.assertEqual(LEECH.tax(zero), 0)
        self.assertEqual(LEECH.nrci(zero), 1)
        light = [1] + [0] * 23
        heavy = [1] * 24
        self.assertIsInstance(LEECH.tax(light), Fraction)
        self.assertLess(LEECH.tax(light), LEECH.tax(heavy))
        self.assertGreater(LEECH.nrci(light), LEECH.nrci(heavy))
        self.assertTrue(0 < LEECH.nrci(heavy) <= 1)

    def test_constants_are_rational_and_accurate(self):
        import math
        self.assertIsInstance(PI, Fraction)
        self.assertLess(abs(float(PI) - math.pi), 1e-15)
        self.assertLess(abs(float(Y) - 1 / (math.pi + 2 / math.pi)), 1e-15)

    def test_tax_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            LEECH.tax([0] * 12)


# ══════════════════════════════════════════════════════════════════════════════
#  CODEC
# ══════════════════════════════════════════════════════════════════════════════

class TestColumnCodec(unittest.TestCase):

    def test_exhaustive_bijection(self):
        seen = set()
        for value in range(16):
            label, fibre = ColumnCodec.encode(value)
            self.assertIn(label, range(4))
            self.assertIn(fibre, range(4))
            self.assertEqual(ColumnCodec.decode(label, fibre), value)
            seen.add((label, fibre))
        self.assertEqual(len(seen), 16)

    def test_label_agrees_with_mog(self):
        for value in range(16):
            self.assertEqual(ColumnCodec.encode(value)[0], MOG.COLUMN_LABEL[value])

    def test_report(self):
        self.assertTrue(ColumnCodec.verify_bijection()["bijective"])


class TestCodec(unittest.TestCase):

    def test_round_trip_on_every_codeword(self):
        for cw in GOLAY.all_codewords():
            self.assertEqual(MOGCodec.round_trip_error(cw, aligned=True), 0)

    def test_round_trip_random_both_griddings(self):
        for v in prng(11, 3000):
            self.assertEqual(MOGCodec.round_trip_error(v, aligned=True), 0)
            self.assertEqual(MOGCodec.round_trip_error(v, aligned=False), 0)

    def test_shadow_shape(self):
        shadow = MOGCodec.project(GOLAY.octads()[0])
        self.assertEqual(len(shadow.labels), 6)
        self.assertEqual(len(shadow.fibres), 6)
        self.assertTrue(shadow.is_hexacode_word())
        self.assertIn("MOGShadow", repr(shadow))

    def test_carrier_is_injective_on_a_full_sub_box(self):
        seen = set()
        count = 0
        for a in range(DIM_MIN, DIM_MAX + 1):
            for b in range(DIM_MIN, DIM_MAX + 1):
                for c in range(DIM_MIN, DIM_MAX + 1):
                    for d in (-1, 0, 2):
                        dims = [a, b, c, d, 0, -3, 4]
                        n = DimCarrier.to_int(dims)
                        seen.add(n)
                        count += 1
                        self.assertEqual(DimCarrier.from_int(n), dims)
        self.assertEqual(len(seen), count)

    def test_carrier_round_trip_through_bits_and_shadow(self):
        for dims in ([0] * 7, [2, 1, -2, 0, 0, 0, 0], [-2, -1, 4, 2, 0, 0, 0],
                     [0, 1, -3, 0, -4, 0, 0], [4, -4, 4, -4, 4, -4, 4]):
            bits = DimCarrier.encode(dims)
            shadow = MOGCodec.project(bits)
            self.assertEqual(MOGCodec.reconstruct(shadow), bits)
            self.assertEqual(DimCarrier.decode(bits), dims)

    def test_dimensionless_is_the_zero_codeword(self):
        bits = DimCarrier.encode([0] * 7)
        self.assertEqual(sum(bits), 0)
        self.assertTrue(GOLAY.is_codeword(bits))

    def test_carrier_range_enforcement(self):
        with self.assertRaises(ValueError):
            DimCarrier.encode([5, 0, 0, 0, 0, 0, 0])
        with self.assertRaises(ValueError):
            DimCarrier.encode([0, 0, 0, 0, 0, 0])
        self.assertFalse(DimCarrier.in_range([0, 0, 0, 0, 0, 0, -5]))
        self.assertIsNone(DimCarrier.from_int(CARRIER_CAPACITY))
        self.assertIsNone(DimCarrier.from_int(-1))

    def test_carrier_capacity(self):
        self.assertEqual(CARRIER_CAPACITY, 9 ** 7)
        self.assertLess(CARRIER_CAPACITY, 1 << 24)

    def test_ontological_profile_is_a_view_not_an_encoding(self):
        a = ontological_profile([2, 1, -2, 0, 0, 0, 0])
        b = ontological_profile([4, 1, -4, 0, 0, 0, 0])
        self.assertEqual(a, b)                     # many-to-one, by design
        self.assertEqual(a["Reality"], [1, 1, 1, 0, 0, 0, 0])
        self.assertEqual(a["Potential"], [0, 0, 1, 0, 0, 0, 0])
        self.assertEqual(a["Activation"], [1, 0, 1, 0, 0, 0, 0])
        with self.assertRaises(ValueError):
            ontological_profile([0, 0, 0])


# ══════════════════════════════════════════════════════════════════════════════
#  METROLOGY
# ══════════════════════════════════════════════════════════════════════════════

class TestDimension(unittest.TestCase):

    def test_group_laws(self):
        a = Dimension((1, -2, 3, 0, 0, 1, 0))
        b = Dimension((0, 1, -1, 2, 0, 0, 3))
        c = Dimension((2, 0, 0, -1, 1, 0, 0))
        self.assertEqual(a + b, b + a)
        self.assertEqual((a + b) + c, a + (b + c))
        self.assertEqual(a + Dimension.zero(), a)
        self.assertEqual(a + (-a), Dimension.zero())
        self.assertEqual(a - b, a + (-b))

    def test_power_is_repeated_addition(self):
        a = Dimension((1, 0, -1, 0, 0, 0, 0))
        self.assertEqual(a * 3, a + a + a)
        self.assertEqual(a * 0, Dimension.zero())
        self.assertEqual(a * -1, -a)
        with self.assertRaises(TypeError):
            a * 1.5

    def test_meaning_has_no_mod2_view(self):
        """The shadow is an appendix diagnostic, not a method on a meaning."""
        a = Dimension((2, 1, -2, 0, 0, 0, 0))
        b = Dimension((4, 1, -4, 0, 0, 0, 0))
        self.assertNotEqual(a, b)
        self.assertFalse(hasattr(a, "mod2"))
        self.assertEqual(mod2_shadow(a), mod2_shadow(b))

    def test_string_form(self):
        self.assertEqual(str(Dimension.zero()), "1 (dimensionless)")
        self.assertEqual(str(Dimension((2, 1, -2, 0, 0, 0, 0))), "L^2*M*T^-2")
        self.assertEqual(str(Dimension.base(0)), "L")

    def test_validation(self):
        with self.assertRaises(ValueError):
            Dimension((1, 2, 3))
        with self.assertRaises(TypeError):
            Dimension((1.0, 0, 0, 0, 0, 0, 0))


class TestLibrary(unittest.TestCase):

    def test_every_quantity_is_well_formed(self):
        for name, (dim, symbol, unit) in QUANTITIES.items():
            self.assertEqual(name, name.lower())
            self.assertEqual(len(dim.exps), 7)
            self.assertTrue(symbol and unit)
            self.assertTrue(DimCarrier.in_range(dim.exps),
                            f"{name} has an exponent outside the carrier box")

    def test_aliases_resolve(self):
        for alias, target in ALIASES.items():
            self.assertIn(target, QUANTITIES)
            self.assertEqual(resolve(alias), QUANTITIES[target][0])

    def test_known_dimensions(self):
        cases = {
            "energy": (2, 1, -2, 0, 0, 0, 0),
            "force": (1, 1, -2, 0, 0, 0, 0),
            "voltage": (2, 1, -3, -1, 0, 0, 0),
            "capacitance": (-2, -1, 4, 2, 0, 0, 0),
            "illuminance": (-2, 0, 0, 0, 0, 0, 1),
            "stefan_boltzmann": (0, 1, -3, 0, -4, 0, 0),
            "gas_constant": (2, 1, -2, 0, -1, -1, 0),
        }
        for name, exps in cases.items():
            self.assertEqual(QUANTITIES[name][0].exps, exps, name)

    def test_base_quantities_are_the_seven_unit_vectors(self):
        base = ["length", "mass", "time", "current", "temperature", "amount",
                "luminous_intensity"]
        for i, name in enumerate(base):
            self.assertEqual(QUANTITIES[name][0], Dimension.base(i))
            self.assertEqual(len(DIM_NAMES), 7)

    def test_collisions_are_reported(self):
        collisions = dimensional_collisions()
        joined = {frozenset(v) for v in collisions.values()}
        self.assertIn(frozenset({"energy", "torque", "work"}), joined)
        self.assertIn(frozenset({"illuminance", "luminance"}), joined)

    def test_mod2_report_is_consistent(self):
        report = mod2_collapse_report()
        n = report["distinct_dimensions"]
        self.assertEqual(report["unordered_pairs"], n * (n - 1) // 2)
        self.assertGreater(report["pairs_indistinguishable_mod2"], 0)
        self.assertEqual(report["exact_false_positive_rate"], 0.0)
        self.assertLess(report["distinct_mod2_shadows"], n)

    def test_unknown_names(self):
        self.assertIsNone(resolve("phlogiston"))


class TestParser(unittest.TestCase):

    def test_products_quotients_powers(self):
        cases = {
            "mass": (0, 1, 0, 0, 0, 0, 0),
            "mass*speed^2": (2, 1, -2, 0, 0, 0, 0),
            "energy/time": (2, 1, -3, 0, 0, 0, 0),
            "1/time": (0, 0, -1, 0, 0, 0, 0),
            "energy/(area*time)": (0, 1, -3, 0, 0, 0, 0),
            "force*length^2/mass^2": (3, -1, -2, 0, 0, 0, 0),
            "speed^-1": (-1, 0, 1, 0, 0, 0, 0),
            "(luminous_flux/area)*time": (-2, 0, 1, 0, 0, 0, 1),
            "3*mass": (0, 1, 0, 0, 0, 0, 0),
        }
        for text, exps in cases.items():
            self.assertEqual(parse_expression(text).exps, exps, text)

    def test_typographic_operators(self):
        self.assertEqual(parse_expression("mass\u00b7speed"),
                         parse_expression("mass*speed"))
        self.assertEqual(parse_expression("energy\u00f7time"),
                         parse_expression("energy/time"))

    def test_aliases_and_symbols(self):
        self.assertEqual(parse_expression("m*v^2"), parse_expression("mass*speed^2"))

    def test_whitespace_insensitive(self):
        self.assertEqual(parse_expression("  mass  *  speed ^ 2 "),
                         parse_expression("mass*speed^2"))

    def test_errors(self):
        for bad in ("", "   ", "mass*", "mass*)", "(mass", "unknown_thing",
                    "mass^speed", "mass$speed"):
            with self.assertRaises(ParseError, msg=bad):
                parse_expression(bad)


class TestEquationAudit(unittest.TestCase):

    def test_true_equations_accepted(self):
        for lhs, rhs in (("energy", "mass*speed^2"),
                         ("force", "mass*acceleration"),
                         ("power", "voltage*current"),
                         ("entropy", "energy/temperature"),
                         ("capacitance", "charge/voltage"),
                         ("illuminance", "luminous_flux/area")):
            self.assertTrue(audit_equation(lhs, rhs).accepted, f"{lhs}={rhs}")

    def test_mod2_traps_rejected(self):
        for lhs, rhs in (("energy", "mass*speed^4"),
                         ("force", "mass*acceleration^3"),
                         ("illuminance", "luminous_flux*area"),
                         ("stefan_boltzmann", "irradiance/temperature^2")):
            rec = audit_equation(lhs, rhs)
            self.assertFalse(rec.accepted)
            # the appendix measurement, not part of the verdict
            self.assertTrue(mod2_would_accept(rec.lhs_dim, rec.rhs_dim))

    def test_audit_carries_no_second_verdict(self):
        """An audit reports the exact verdict and nothing weaker."""
        rec = audit_equation("energy", "mass*speed^4")
        self.assertFalse(hasattr(rec, "mod2_accepted"))
        self.assertFalse(hasattr(rec, "mod2_false_positive"))
        self.assertNotIn("mod-2", rec.summary())

    def test_plain_mismatch_rejected_by_both(self):
        rec = audit_equation("energy", "mass*speed")
        self.assertFalse(rec.accepted)
        self.assertFalse(mod2_would_accept(rec.lhs_dim, rec.rhs_dim))

    def test_residual(self):
        rec = audit_equation("energy", "mass*speed^4")
        self.assertEqual(rec.residual.exps, (-2, 0, 2, 0, 0, 0, 0))

    def test_summary_mentions_verdict(self):
        self.assertIn("ACCEPT", audit_equation("energy", "force*length").summary())
        self.assertIn("REJECT", audit_equation("energy", "force").summary())


# ══════════════════════════════════════════════════════════════════════════════
#  THE MOD-2 CEILING, MEASURED
# ══════════════════════════════════════════════════════════════════════════════

class TestMod2Ceiling(unittest.TestCase):
    """Proposition 1 of the paper, and the two measurements of it."""

    def test_perturbation_family_size(self):
        sweep = mod2_perturbation_sweep()
        self.assertEqual(sweep["false_equations"], 2 * 7 * len(QUANTITIES))

    def test_every_even_perturbation_fools_mod_two(self):
        sweep = mod2_perturbation_sweep()
        self.assertEqual(sweep["mod2_accepted"], sweep["false_equations"])
        self.assertEqual(sweep["mod2_false_positive_rate"], 1.0)

    def test_no_even_perturbation_fools_the_integer_checker(self):
        sweep = mod2_perturbation_sweep()
        self.assertEqual(sweep["exact_accepted"], 0)
        self.assertEqual(sweep["exact_false_positive_rate"], 0.0)

    def test_larger_even_shifts_behave_the_same(self):
        for shift in (2, 4, 6):
            sweep = mod2_perturbation_sweep(shift)
            self.assertEqual(sweep["mod2_false_positive_rate"], 1.0)
            self.assertEqual(sweep["exact_accepted"], 0)

    def test_odd_shift_is_rejected_as_input(self):
        with self.assertRaises(ValueError):
            mod2_perturbation_sweep(3)

    def test_named_traps_are_real_equations(self):
        sweep = mod2_perturbation_sweep()
        self.assertGreater(sweep["named_traps"], 0)
        for example in sweep["named_trap_examples"]:
            lhs, rhs = example.split(" = ")
            rec = audit_equation(lhs, rhs)
            self.assertTrue(mod2_would_accept(rec.lhs_dim, rec.rhs_dim))
            self.assertFalse(rec.accepted)

    def test_box_census_matches_brute_force(self):
        for bound in (1, 2):
            census = mod2_box_census(bound)
            vectors = [()]
            for _ in range(7):
                vectors = [v + (e,) for v in vectors
                           for e in range(-bound, bound + 1)]
            self.assertEqual(census["box_size"], len(vectors))
            if bound == 1:
                brute = sum(
                    1
                    for i in range(len(vectors))
                    for j in range(i + 1, len(vectors))
                    if tuple(x % 2 for x in vectors[i])
                    == tuple(x % 2 for x in vectors[j]))
                self.assertEqual(census["pairs_confused_mod2"], brute)

    def test_box_census_default_numbers(self):
        census = mod2_box_census(2)
        self.assertEqual(census["box_size"], 5 ** 7)
        self.assertEqual(census["pairs_confused_mod2"], 31335196)
        self.assertEqual(census["pairs_confused_exactly"], 0)
        self.assertLess(census["mod2_false_positive_rate"], 0.02)

    def test_ceiling_is_exactly_the_even_sublattice(self):
        """d and e are mod-2 confusable iff they differ by an even vector."""
        a = Dimension((2, 1, -2, 0, 0, 0, 0))
        for delta in ((2, 0, -2, 0, 0, 0, 0), (0, 4, 0, 0, 0, 0, 0),
                      (-2, 2, 2, 0, 0, 0, 0)):
            b = Dimension(tuple(x + y for x, y in zip(a.exps, delta)))
            self.assertEqual(mod2_shadow(a), mod2_shadow(b))
            self.assertNotEqual(a.exps, b.exps)
        for delta in ((1, 0, 0, 0, 0, 0, 0), (0, 0, 3, 0, 0, 0, 0)):
            b = Dimension(tuple(x + y for x, y in zip(a.exps, delta)))
            self.assertNotEqual(mod2_shadow(a), mod2_shadow(b))


# ══════════════════════════════════════════════════════════════════════════════
#  LINEAR ALGEBRA
# ══════════════════════════════════════════════════════════════════════════════

class TestLinalg(unittest.TestCase):

    def test_snf_identity_and_diagonality(self):
        A = [[2, 4, 4], [-6, 6, 12], [10, 4, 16]]
        D, U, V, rank = smith_normal_form(A)
        self.assertEqual(matmul(matmul(U, A), V), D)
        for i, row in enumerate(D):
            for j, x in enumerate(row):
                if i != j:
                    self.assertEqual(x, 0)
        self.assertEqual(rank, 3)

    def test_kernel_basis(self):
        A = [[1, 1, 1], [0, 1, 2]]
        ker = kernel_basis(A)
        self.assertEqual(len(ker), 1)
        for k in ker:
            self.assertEqual(matvec(A, k), [0, 0])

    def test_integer_solving(self):
        A = [[1, 0, 2], [0, 1, 1]]
        sol = solve_integer_system(A, [4, 3])
        self.assertIsNotNone(sol)
        x, ker = sol
        self.assertEqual(matvec(A, x), [4, 3])
        self.assertEqual(len(ker), 1)

    def test_non_integer_but_rational(self):
        A = [[2]]
        self.assertIsNone(solve_integer_system(A, [1]))
        self.assertEqual(solve_rational_system(A, [1]), [Fraction(1, 2)])

    def test_inconsistent_system(self):
        A = [[1], [0]]
        self.assertIsNone(solve_integer_system(A, [1, 1]))
        self.assertIsNone(solve_rational_system(A, [1, 1]))

    def test_randomised(self):
        from glm_linalg import _self_check
        passed, total = _self_check(150)
        self.assertEqual(passed, total)


# ══════════════════════════════════════════════════════════════════════════════
#  REASONER
# ══════════════════════════════════════════════════════════════════════════════

class TestReasoner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.r = REASONER

    def test_every_library_concept_is_carried_losslessly(self):
        integrity = self.r.codec_integrity()
        self.assertTrue(integrity["lossless"])
        self.assertEqual(integrity["concepts_tested"], len(QUANTITIES))
        self.assertEqual(integrity["failures"], [])

    def test_concept_telemetry_is_complete(self):
        c = self.r.concept("energy")
        self.assertIsNotNone(c)
        t = c.telemetry()
        for key in ("dims", "carrier_int", "hexacode_shadow", "fibre_keys",
                    "syndrome", "snap_distance", "snap_ties", "snap_status",
                    "lawful", "codec_round_trip_ok", "tax", "nrci", "profile"):
            self.assertIn(key, t)
        self.assertTrue(t["codec_round_trip_ok"])
        self.assertLessEqual(t["snap_distance"], 4)

    def test_dimensionless_concept_is_lawful(self):
        c = self.r.concept("dimensionless")
        self.assertTrue(c.lawful)
        self.assertEqual(c.snap.distance, 0)
        self.assertEqual(c.tax, 0)
        self.assertEqual(c.nrci, 1)

    def test_lawful_concepts_are_exactly_the_dimensionless_ones(self):
        for name in self.r.lawful_concepts():
            self.assertTrue(self.r.concept(name).dim.is_dimensionless)

    def test_unknown_concept(self):
        self.assertIsNone(self.r.concept("phlogiston"))

    def test_expression_concepts(self):
        c = self.r.concept_of_expression("mass*speed^2")
        self.assertEqual(c.dim, self.r.concept("energy").dim)
        self.assertTrue(c.round_trip_ok())

    def test_identify_reports_collisions(self):
        names = self.r.identify(Dimension((2, 1, -2, 0, 0, 0, 0)))
        self.assertIn("energy", names)
        self.assertIn("torque", names)

    def test_audit_structure(self):
        rec = self.r.audit("energy", "mass*speed^4", "trap")
        self.assertFalse(rec["accepted"])
        self.assertIn("lhs_telemetry", rec)
        self.assertIn("rhs_telemetry", rec)

    def test_audit_record_carries_one_verdict_only(self):
        rec = self.r.audit("energy", "mass*speed^4", "trap")
        self.assertNotIn("mod2_accepted", rec)
        self.assertNotIn("mod2_false_positive", rec)

    def test_audit_many_counts(self):
        batch = self.r.audit_many([
            ("energy", "mass*speed^2", "true"),
            ("energy", "mass*speed^4", "trap"),
            ("energy", "mass*speed", "plain mismatch"),
        ])
        self.assertEqual(batch["total"], 3)
        self.assertEqual(batch["accepted"], 1)
        self.assertEqual(batch["rejected"], 2)
        self.assertNotIn("mod2_false_positives_prevented", batch)

    def test_mod2_ceiling_batch_is_the_appendix(self):
        ceiling = self.r.mod2_ceiling_batch([
            ("energy", "mass*speed^2", "true"),
            ("energy", "mass*speed^4", "trap"),
            ("energy", "mass*speed", "plain mismatch"),
        ])
        self.assertEqual(ceiling["total"], 3)
        self.assertEqual(ceiling["mod2_false_positives_prevented"], 1)

    def test_solve_integer_cases(self):
        cases = {
            ("energy", ("mass", "speed")): "energy = mass * speed^2",
            ("power", ("energy", "time")): "power = energy / time",
            ("power", ("current", "resistance")): "power = current^2 * resistance",
            ("resistance", ("voltage", "current")): "resistance = voltage / current",
            ("illuminance", ("luminous_flux", "area")):
                "illuminance = luminous_flux / area",
            ("gravitational_constant", ("force", "length", "mass")):
                "gravitational_constant = force * length^2 / mass^2",
        }
        for (target, inputs), formula in cases.items():
            sol = self.r.solve(target, list(inputs))
            self.assertEqual(sol.status, "integer", (target, inputs))
            self.assertEqual(sol.formula(), formula)
            self.assertTrue(sol.found)
            self.assertTrue(sol.proof_steps())

    def test_solve_fractional_case(self):
        sol = self.r.solve("speed", ["energy", "mass"])
        self.assertEqual(sol.status, "fractional")
        self.assertEqual(sol.exponents, [Fraction(1, 2), Fraction(-1, 2)])
        self.assertIn("^1/2", sol.formula())

    def test_solve_impossible_case(self):
        sol = self.r.solve("temperature", ["energy", "mass"])
        self.assertEqual(sol.status, "impossible")
        self.assertFalse(sol.found)
        self.assertIn("not in the span", sol.detail)

    def test_solve_unknown_names(self):
        self.assertEqual(self.r.solve("phlogiston", ["mass"]).status, "impossible")
        self.assertEqual(self.r.solve("mass", ["phlogiston"]).status, "impossible")

    def test_solution_exponents_actually_solve(self):
        for target, inputs in (("energy", ("mass", "speed")),
                               ("pressure", ("density", "speed")),
                               ("magnetic_flux", ("voltage", "time"))):
            sol = self.r.solve(target, list(inputs))
            total = Dimension.zero()
            for name, e in zip(inputs, sol.exponents):
                self.assertEqual(e.denominator, 1)
                total = total + resolve(name) * int(e)
            self.assertEqual(total, resolve(target))

    def test_pi_groups(self):
        res = self.r.pi_groups(["force", "density", "speed", "length"])
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["pi_group_count"], 1)
        self.assertTrue(res["pi_theorem_holds"])
        self.assertTrue(all(g["verified_dimensionless"] for g in res["groups"]))

    def test_pi_groups_of_independent_inputs(self):
        res = self.r.pi_groups(["length", "mass", "time"])
        self.assertEqual(res["pi_group_count"], 0)
        self.assertEqual(res["rank"], 3)

    def test_pi_groups_unknown_input(self):
        self.assertEqual(self.r.pi_groups(["phlogiston"])["status"], "error")

    def test_scene_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "scene.json")
            self.r.export_scene(["energy", "mass", "speed"],
                                [("energy", "mass")], path)
            with open(path, encoding="utf-8") as fh:
                scene = json.load(fh)
            self.assertEqual(len(scene["spheres"]), 3)
            self.assertEqual(len(scene["lines"]), 1)
            self.assertIn("axes", scene)

    def test_substrate_table(self):
        rows = self.r.substrate_table(["energy", "mass"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "energy")

    def test_fresh_reasoner_matches_singleton(self):
        fresh = GeometricReasoner()
        self.assertEqual(sorted(fresh.concepts), sorted(REASONER.concepts))

    def test_concept_outside_carrier_box(self):
        c = Concept("huge", Dimension((9, 0, 0, 0, 0, 0, 0)))
        self.assertFalse(c.representable)
        self.assertIsNone(c.carrier)
        self.assertFalse(c.round_trip_ok())
        # no bits at all is the honest answer, and it is still "derived"
        self.assertTrue(c.carrier_is_derived())


# ══════════════════════════════════════════════════════════════════════════════
#  MEANING IS PRIMARY, THE BIT PATTERN IS DERIVED  (paper §5.2, claims C42-C43)
# ══════════════════════════════════════════════════════════════════════════════

class TestCarrierIsDerived(unittest.TestCase):
    """The architecture invariant: one source of truth, one derived view."""

    def setUp(self):
        self.r = REASONER

    def test_every_library_concept_derives_its_bits(self):
        for name, c in self.r.concepts.items():
            self.assertTrue(c.carrier_is_derived(), name)

    def test_same_meaning_same_bits(self):
        d = Dimension((2, 1, -2, 0, 0, 0, 0))
        self.assertEqual(Concept("one", d).carrier, Concept("other", d).carrier)

    def test_distinct_meanings_distinct_bits(self):
        seen = {}
        for name, c in self.r.concepts.items():
            if c.carrier is None:
                continue
            key = tuple(c.carrier)
            self.assertEqual(seen.setdefault(key, c.dim), c.dim, name)

    def test_bits_follow_a_changed_meaning(self):
        base = self.r.concept("energy")
        moved = base.with_meaning(Dimension((4, 1, -4, 0, 0, 0, 0)))
        self.assertNotEqual(base.carrier, moved.carrier)
        self.assertTrue(moved.carrier_is_derived())
        self.assertEqual(moved.name, base.name)

    def test_bits_cannot_be_set(self):
        c = self.r.concept("energy")
        with self.assertRaises(AttributeError):
            c.carrier = [0] * 24
        with self.assertRaises(AttributeError):
            c.dim = Dimension.zero()
        with self.assertRaises(AttributeError):
            c.lawful = True

    def test_derivation_is_a_pure_function(self):
        d = Dimension((1, 0, -1, 0, 0, 0, 0))
        self.assertEqual(derive_substrate(d).word, derive_substrate(d).word)
        self.assertEqual(list(derive_substrate(d).word),
                         DimCarrier.encode(d.exps))

    def test_derived_view_round_trips_across_the_box(self):
        for n in range(0, CARRIER_CAPACITY, 7919):
            dims = DimCarrier.from_int(n)
            c = Concept("sample", Dimension(tuple(dims)))
            self.assertTrue(c.carrier_is_derived())
            self.assertTrue(c.round_trip_ok())

    def test_carrier_does_not_compose(self):
        """XOR of two words is almost never the word of the product."""
        a = Dimension((2, 1, -2, 0, 0, 0, 0))
        b = Dimension((1, 0, -1, 0, 0, 0, 0))
        wa = DimCarrier.encode(a.exps)
        wb = DimCarrier.encode(b.exps)
        wsum = DimCarrier.encode((a + b).exps)
        self.assertNotEqual([x ^ y for x, y in zip(wa, wb)], wsum)

    def test_no_f2_encoder_separates_meanings(self):
        """Corollary 1: an F_2-linear encoder identifies d with d + 2u."""
        for name, c in list(self.r.concepts.items())[:20]:
            shifted = Dimension(tuple(e + 2 if i == 0 else e
                                      for i, e in enumerate(c.dim.exps)))
            self.assertNotEqual(c.dim, shifted)
            self.assertTrue(mod2_would_accept(c.dim, shifted), name)


# ══════════════════════════════════════════════════════════════════════════════
#  UPPER TIERS
# ══════════════════════════════════════════════════════════════════════════════

class TestUpperTiers(unittest.TestCase):

    def test_identity_is_an_automorphism(self):
        self.assertTrue(golay_permutation_check(list(range(24))))

    def test_non_permutation_rejected(self):
        with self.assertRaises(ValueError):
            golay_permutation_check([0] * 24)

    def test_symmetry_report(self):
        report = column_symmetry_report()
        self.assertTrue(report["identity"])
        self.assertTrue(report["swap_halves"])
        self.assertFalse(report["transpose_1_2"])

    def test_extraspecial_group_law(self):
        x0, y0, z = (ExtraspecialElement.x(0), ExtraspecialElement.y(0),
                     ExtraspecialElement.z())
        ident = ExtraspecialElement.identity()
        self.assertEqual(x0 * x0, ident)
        self.assertEqual(y0 * y0, ident)
        self.assertEqual(z * z, ident)
        self.assertEqual(x0 * y0 * x0.inverse() * y0.inverse(), z)
        self.assertTrue(ident.is_identity())

    def test_extraspecial_associativity(self):
        elements = [ExtraspecialElement((i * 37) % 4096, (i * 91) % 4096, i % 2)
                    for i in range(12)]
        for a in elements:
            for b in elements[:6]:
                for c in elements[:3]:
                    self.assertEqual((a * b) * c, a * (b * c))

    def test_representation_is_a_faithful_homomorphism(self):
        report = extraspecial_relation_report()
        self.assertTrue(report["representation_is_a_homomorphism"])
        self.assertTrue(report["faithful_on_sample"])
        self.assertTrue(report["all_relations_hold"])
        self.assertEqual(report["representation_dimension"], 4096)

    def test_action_on_a_basis_vector(self):
        """rho(a,b,eps)|k> = (-1)^(<a,k>+eps) |k xor b>, checked by hand."""
        state = [0] * SchrodingerRep.DIM
        state[0b101] = 1
        # <a,k> = popcount(0b101 & 0b101) = 2 -> even -> sign +1
        out = SchrodingerRep.apply(ExtraspecialElement(0b101, 0b011, 0), state)
        self.assertEqual(sum(1 for x in out if x), 1)
        self.assertEqual(out[0b101 ^ 0b011], 1)
        # <a,k> = popcount(0b100 & 0b101) = 1 -> odd -> sign -1
        out = SchrodingerRep.apply(ExtraspecialElement(0b100, 0b011, 0), state)
        self.assertEqual(out[0b101 ^ 0b011], -1)
        # the central element is minus the identity
        out = SchrodingerRep.apply(ExtraspecialElement.z(), state)
        self.assertEqual(out[0b101], -1)

    def test_24d_action_cannot_realise_the_commutator(self):
        self.assertFalse(visual_24d_commutator_check())

    def test_snap_algebra_structure(self):
        report = snap_algebra_report(120)
        self.assertTrue(report["commutative"])
        self.assertTrue(report["associative"])
        self.assertTrue(report["defect_is_always_a_codeword"])
        self.assertTrue(report["defect_depends_only_on_syndromes"])
        self.assertTrue(report["product_equals_snap_xor_snap"])
        self.assertTrue(report["squares_are_zero"])
        self.assertEqual(report["triple_defect_nonzero_count"], 0)
        self.assertFalse(report["earlier_non_associativity_claim_holds"])

    def test_snap_product_identity_by_hand(self):
        for v, w in zip(prng(21, 40), prng(22, 40)):
            self.assertEqual(SnapAlgebra.product(v, w),
                             BitOps.xor(SnapAlgebra.snap_word(v),
                                        SnapAlgebra.snap_word(w)))
            self.assertTrue(GOLAY.is_codeword(SnapAlgebra.bilinear_defect(v, w)))


# ══════════════════════════════════════════════════════════════════════════════
#  THE SEMIDIRECT PRODUCT
# ══════════════════════════════════════════════════════════════════════════════

class TestNormaliser(unittest.TestCase):

    def test_bit_permutation_is_involutive_on_swaps(self):
        swap = (1, 0) + tuple(range(2, 12))
        for mask in (0, 1, 0b1010, 0xFFF, 0x555):
            self.assertEqual(permute_bits(permute_bits(mask, swap), swap), mask)

    def test_perm_inverse_and_compose(self):
        shift = tuple((i + 5) % 12 for i in range(12))
        inv = perm_inverse(shift)
        self.assertEqual(perm_compose(shift, inv), IDENTITY_PERM)
        self.assertEqual(perm_compose(inv, shift), IDENTITY_PERM)

    def test_pair_permutations_preserve_the_cocycle(self):
        shift = tuple((i + 5) % 12 for i in range(12))
        g = ExtraspecialElement(0b1011, 0b0110, 0)
        h = ExtraspecialElement(0b0101, 0b1100, 1)
        self.assertEqual(act_on_element(shift, g * h),
                         act_on_element(shift, g) * act_on_element(shift, h))

    def test_conjugation_moves_generators(self):
        swap = (1, 0) + tuple(range(2, 12))
        s = NormaliserElement(ExtraspecialElement.identity(), swap)
        conj = s * NormaliserElement(ExtraspecialElement.x(0)) * s.inverse()
        self.assertEqual(conj, NormaliserElement(ExtraspecialElement.x(1)))

    def test_group_axioms_and_faithful_action(self):
        report = normaliser_report()
        for key in ("pair_perms_are_automorphisms", "centre_fixed",
                    "associative", "unital", "inverses",
                    "conjugation_moves_generators",
                    "action_is_homomorphism_on_4096"):
            self.assertTrue(report[key], key)
        self.assertGreater(report["non_commuting_pairs"], 0)

    def test_action_is_a_signed_permutation_of_the_whole_space(self):
        shift = tuple((i + 5) % 12 for i in range(12))
        u = NormaliserElement(ExtraspecialElement(0b1101, 0b0011, 1), shift)
        cols = u.columns()
        self.assertEqual(len(cols), 4096)
        self.assertEqual(len({t for t, _ in cols}), 4096)
        self.assertTrue(all(sign in (1, -1) for _, sign in cols))


# ══════════════════════════════════════════════════════════════════════════════
#  THE FIBRE GEOMETRY  (paper section 9)
# ══════════════════════════════════════════════════════════════════════════════

class TestGeometry(unittest.TestCase):

    def test_quaternion_relations_exhaustively(self):
        report = quaternion_group_report()
        self.assertEqual(report["order"], 8)
        self.assertTrue(report["closed"])
        self.assertTrue(report["associative"])
        self.assertTrue(report["relations_all_hold"])

    def test_quaternion_arithmetic_is_exact_integer(self):
        self.assertEqual(Q_I * Q_J, Q_K)
        self.assertEqual(Q_J * Q_I, Quaternion(0, 0, 0, -1))
        self.assertEqual(Q_I * Q_I * Q_I * Q_I, Q_ONE)
        self.assertEqual((Q_I * Q_J * Q_K), Quaternion(-1, 0, 0, 0))
        self.assertEqual(Q_K.inverse() * Q_K, Q_ONE)

    def test_fibre_map_is_a_bijection_but_not_a_homomorphism(self):
        self.assertEqual(len({QUATERNION_OF_FIBRE[f] for f in range(4)}), 4)
        self.assertNotEqual(QUATERNION_OF_FIBRE[1] * QUATERNION_OF_FIBRE[1],
                            QUATERNION_OF_FIBRE[2])

    def test_versor_index_matches_the_fibre_keys(self):
        for word in prng(31, 60):
            self.assertEqual(versor_index(word), sum(fibre_keys(word)) % 4)

    def test_h6_norm_is_always_six(self):
        for word in prng(32, 60):
            self.assertEqual(h6_norm_sq(word), 6)

    def test_fibre_product_order_sensitivity_is_counted(self):
        report = fibre_noncommutativity_report()
        self.assertEqual(report["tested"],
                         report["order_sensitive"] + report["order_insensitive"])
        self.assertGreater(report["order_sensitive"], 0)

    def test_closed_walks_have_integer_winding(self):
        report = winding_report()
        self.assertTrue(report["all_windings_integral"])
        self.assertGreater(report["closed_walks"], 0)

    def test_walk_steps_lift_the_z4_differences(self):
        walk = walk_of_names(["energy", "mass", "speed", "speed", "energy"])
        self.assertTrue(walk.closed)
        self.assertEqual(walk.quarter_turns % 4, 0)
        self.assertEqual(walk.winding, walk.quarter_turns // 4)
        for i, step in enumerate(walk.steps):
            self.assertIn(step, (-1, 0, 1, 2))
            self.assertEqual(step % 4,
                             (walk.indices[i + 1] - walk.indices[i]) % 4)

    def test_open_walks_have_no_winding(self):
        walk = walk_of_names(["energy", "mass", "speed"])
        self.assertFalse(walk.closed)
        self.assertIsNone(walk.winding)

    def test_holonomy_is_path_dependent_and_telescopes(self):
        loop = ["pressure", "force", "area", "pressure"]
        self.assertNotEqual(holonomy(loop), holonomy(loop, reverse=True))
        undo = Q_ONE
        for name in reversed(loop):
            concept = REASONER.concept(name)
            assert concept is not None and concept.carrier is not None
            undo = undo * fibre_product(concept.carrier).inverse()
        self.assertEqual(holonomy(loop) * undo, Q_ONE)

    def test_archive_conformal_weight_is_half_the_syndrome(self):
        report = conformal_grading_report()
        self.assertTrue(report["h6_norm_sq_always_six"])
        self.assertTrue(report["archive_L0_equals_half_syndrome"])

    def test_vacuum_census_is_exact_and_lawful(self):
        census = vacuum_census(bound=1)
        self.assertEqual(census["searched"], 3 ** 7)
        for dims in census["examples"]:
            word = DimCarrier.encode(dims)
            self.assertTrue(GOLAY.is_codeword(word))
            self.assertEqual(DimCarrier.decode(word), dims)

    def test_colour_round_trip(self):
        for word in prng(33, 60):
            self.assertEqual(word_of_colour(colour_of_word(word)), word)
        self.assertEqual(colour_of_word([0] * 24), "#000000")
        self.assertEqual(colour_of_word([1] * 24), "#FFFFFF")

    def test_chromatic_ground_states_are_exactly_the_code(self):
        grounds = chromatic_ground_states()
        self.assertEqual(len(grounds), 4096)
        self.assertEqual(len(set(grounds)), 4096)
        for colour in grounds[:128]:
            self.assertTrue(GOLAY.is_codeword(word_of_colour(colour)))
        report = colour_report()
        self.assertEqual(report["ground_state_fraction_one_in"], 4096)
        self.assertTrue(report["round_trip_lossless"])

    def test_reasoner_exposes_geometry_without_deciding_with_it(self):
        concept = REASONER.concept("energy")
        assert concept is not None
        geo = concept.geometry()
        self.assertIsNotNone(geo)
        self.assertEqual(geo["colour"], colour_of_word(concept.carrier))
        self.assertEqual(geo["h6_norm_sq"], 6)
        # the verdict is unaffected by anything in `geo`
        self.assertTrue(REASONER.audit("energy", "mass*speed^2")["accepted"])
        self.assertFalse(REASONER.audit("energy", "mass*speed^4")["accepted"])


# ══════════════════════════════════════════════════════════════════════════════
#  THE LEECH LEDGER  (paper section 10)
# ══════════════════════════════════════════════════════════════════════════════

class TestMoonshine(unittest.TestCase):

    def test_line_census(self):
        census = line_census()
        self.assertEqual(census["vectors"], 196560)
        self.assertTrue(census["all_distinct"])
        self.assertTrue(census["negation_closed"])
        self.assertTrue(census["class_preserved_under_negation"])
        self.assertEqual(census["self_negative_vectors"], 0)
        self.assertEqual(census["lines"], 98280)
        self.assertEqual(census["lines_by_class"],
                         {"A": 552, "B": 48576, "C": 49152})

    def test_class_c_indexing_is_a_bijection(self):
        report = class_c_indexing_report()
        self.assertTrue(report["injective"])
        self.assertEqual(report["index_pairs"], 98304)
        self.assertEqual(report["norm_failures"], 0)
        self.assertEqual(report["glue_failures"], 0)

    def test_dimension_ledger_balances(self):
        ledger = dimension_ledger()
        self.assertEqual(ledger["traceless_sym_dim"], 299)
        self.assertEqual(ledger["total"], 196884)
        self.assertEqual(ledger["standard_rep"], 196883)

    def test_eta_power_series_head(self):
        self.assertEqual(eta_power_series(4)[:5], [1, 24, 324, 3200, 25650])

    def test_head_of_j(self):
        head = leech_voa_head()
        self.assertEqual(head["J_head"]["q^-1"], 1)
        self.assertEqual(head["J_head"]["q^0"], 24)
        self.assertEqual(head["J_head"]["q^1"], 196884)
        self.assertEqual(head["weight_two_split"],
                         {"oscillator": 324, "lattice": 196560})
        with self.assertRaises(ValueError):
            leech_voa_head(2)

    def test_jordan_layer_is_commutative_unital_non_associative(self):
        report = jordan_algebra_report()
        self.assertEqual(report["dimension"], 300)
        self.assertTrue(report["commutative"])
        self.assertTrue(report["unital"])
        self.assertTrue(report["closed_in_layer"])
        self.assertFalse(report["associative"])
        self.assertTrue(report["jordan_identity"])

    def test_jordan_elements_stay_symmetric_and_traceless(self):
        x = JordanElement.from_seed(5)
        y = JordanElement.from_seed(9)
        for element in (x, y, x * y, (x * y) * x):
            self.assertTrue(element.is_symmetric())
            self.assertTrue(element.is_traceless())
        self.assertEqual(JordanElement.identity() * x, x)
        self.assertEqual(x * y, y * x)

    def test_archive_inner_product_is_hamming_distance(self):
        report = hamming_inner_product_report(256)
        self.assertTrue(report["holds"])
        for u, v in zip(prng(41, 40), prng(42, 40)):
            archive = (sum(1 for a, b in zip(u, v) if a == b)
                       - sum(1 for a, b in zip(u, v) if a != b))
            self.assertEqual(archive, 24 - 2 * BitOps.distance(u, v))


# ══════════════════════════════════════════════════════════════════════════════
#  THE PAPER
# ══════════════════════════════════════════════════════════════════════════════

class TestM24(unittest.TestCase):
    """glm_m24.py: the automorphism group of the Golay code, constructed."""

    @classmethod
    def setUpClass(cls):
        cls.chain = schreier_sims(list(M24_GENERATORS), 24,
                                  base_hint=BASE_POINTS)

    def test_generators_are_automorphisms(self):
        for g in M24_GENERATORS:
            self.assertEqual(sorted(g), list(range(24)))
            self.assertTrue(preserves_code(g))

    def test_permutation_algebra(self):
        ident = identity_perm(24)
        for g in M24_GENERATORS:
            self.assertEqual(compose(g, inverse(g)), ident)
            self.assertEqual(compose(ident, g), g)
            self.assertEqual(compose(g, ident), g)
            self.assertNotEqual(cycles(g), [])

    def test_composites_are_automorphisms(self):
        g = M24_GENERATORS[0]
        for h in M24_GENERATORS:
            g = compose(g, h)
            self.assertTrue(preserves_code(g))
            self.assertTrue(preserves_code(inverse(g)))

    def test_group_order_and_transitivity(self):
        self.assertEqual(self.chain.order(), 244823040)
        self.assertEqual(self.chain.orbit_lengths()[:5], [24, 23, 22, 21, 20])
        self.assertEqual(self.chain.stabiliser_order(5), 48)

    def test_membership_agrees_with_exhaustive_test(self):
        ident = identity_perm(24)
        self.assertTrue(self.chain.contains(ident))
        transposition = list(range(24))
        transposition[0], transposition[1] = 1, 0
        self.assertFalse(self.chain.contains(tuple(transposition)))
        self.assertFalse(preserves_code(tuple(transposition)))
        for g in M24_GENERATORS:
            self.assertTrue(self.chain.contains(g))

    def test_pointwise_stabiliser_is_exactly_48(self):
        stab = code_automorphisms({b: b for b in BASE_POINTS})
        self.assertEqual(len(stab), 48)
        for p in stab:
            self.assertTrue(preserves_code(p))
            self.assertTrue(self.chain.contains(p))
            for b in BASE_POINTS:
                self.assertEqual(p[b], b)

    def test_five_transitivity_by_construction(self):
        # any prescribed image of five points extends to an automorphism
        for spec in ({0: 7, 1: 3, 2: 19, 3: 5, 4: 12},
                     {0: 23, 1: 0, 2: 1, 3: 2, 4: 3}):
            found = code_automorphisms(spec, first_only=True)
            self.assertEqual(len(found), 1)
            p = found[0]
            self.assertTrue(preserves_code(p))
            for d, v in spec.items():
                self.assertEqual(p[d], v)

    def test_orbit_stabiliser_gives_the_full_group(self):
        report = m24_report(quick=False)
        self.assertEqual(report["exhaustive_stabiliser"], 48)
        self.assertEqual(report["aut_order_from_orbit_stabiliser"], 244823040)
        self.assertTrue(report["is_full_automorphism_group"])

    def test_octad_transitivity(self):
        orbit, total = octad_orbit(list(M24_GENERATORS))
        self.assertEqual(orbit, 759)
        self.assertEqual(total, 759)
        self.assertEqual(244823040 // orbit, 322560)

    def test_permute_word_moves_bits_not_weights(self):
        word = [0] * 24
        word[0] = word[5] = word[11] = 1
        for g in M24_GENERATORS:
            image = permute_word(word, g)
            self.assertEqual(sum(image), 3)

    def test_subgroup_census(self):
        census = subgroup_census()
        self.assertEqual(census["group_order"], 244823040)
        self.assertEqual(census["octad_orbit"], 759)
        self.assertEqual(census["octad_stabiliser_order"], 322560)
        self.assertEqual(census["dodecad_orbit"], 2576)
        self.assertEqual(census["dodecad_stabiliser_order"], 95040)
        self.assertEqual(census["sextet_orbit"], 1771)
        self.assertEqual(census["sextet_stabiliser_order"], 138240)
        self.assertTrue(census["matches_expected"])

    def test_sextet_partitions_the_24_points(self):
        for tetrad in (0b1111, 0b111100000000, 0xF00000):
            sextet = sextet_of(tetrad)
            self.assertEqual(len(sextet), 6)
            union = 0
            for part in sextet:
                self.assertEqual(bin(part).count("1"), 4)
                self.assertEqual(union & part, 0)
                union |= part
            self.assertEqual(union, (1 << 24) - 1)

    def test_stab_chain_type(self):
        self.assertIsInstance(self.chain, StabChain)
        self.assertEqual(len(self.chain.base), len(self.chain.transversals))


class TestSymmetryOrbit(unittest.TestCase):
    """The reasoner's view of M24 (paper section 8.1, claim C40)."""

    def test_orbit_of_a_weight_three_concept(self):
        report = REASONER.symmetry_orbit("energy")
        self.assertIsNotNone(report)
        self.assertTrue(report["decisions_preserved"])
        self.assertEqual(report["orbit_size"], report["words_of_this_weight"])
        self.assertTrue(report["orbit_is_every_word_of_this_weight"])
        self.assertFalse(report["orbit_truncated"])

    def test_unknown_quantity(self):
        self.assertIsNone(REASONER.symmetry_orbit("no_such_quantity"))

    def test_decisions_preserved_across_the_library(self):
        for name in ("force", "pressure", "speed", "entropy", "power"):
            report = REASONER.symmetry_orbit(name)
            if report is None:
                continue
            self.assertTrue(report["decisions_preserved"], name)


class TestPaper(unittest.TestCase):

    def test_every_claim_verifies(self):
        for cid, statement, verifier in CLAIMS:
            ok, evidence = verifier()
            self.assertTrue(ok, f"{cid} failed: {statement}\nevidence: {evidence}")

    def test_claim_ids_are_unique(self):
        ids = [c[0] for c in CLAIMS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_run_paper_quick(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = run_paper(quick=True, out_dir=tmp)
            self.assertEqual(payload["claims_passed"], payload["claims_checked"])
            self.assertTrue(os.path.exists(os.path.join(tmp, "glm_results.json")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
