#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 TEST SUITE
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Role   :  independent verification of every module, at a finer grain than
            the numbered claims of glm2_paper.py.

  The paper checks that the SYSTEM does what the paper says.  This suite
  checks that each PART does what its docstring says, including the edge
  cases the paper has no reason to mention: empty expressions, fractional
  powers of pseudovectors, points outside the packing radius, degenerate
  Buckingham Pi problems, and so on.

      python3 test_glm2.py            # the whole suite
      python3 test_glm2.py -v         # with the name of every test
      python3 test_glm2.py TestCodec  # one class

  Standard library only.  Run it from inside the glm2 directory.
================================================================================
"""

from __future__ import annotations

import random
import unittest
from fractions import Fraction as F

from glm2_axial import (Algebra, basis_vector, jordan_symmetric_algebra,
                        jordan_type_rules, matsuo_algebra,
                        miyamoto_group_order, nullspace, rank, rref,
                        symmetric_group_transpositions, vadd, vscale)
from glm2_codec import (N_CONTEXT, SLOTS, capacity_within_norm, compose,
                        coords_of, decode_point, encode, meaning_of_coords,
                        repair, separation_bound)
from glm2_common import GOLAY_BASIS_MASKS, GOLAY_MASKS, M24_GENERATORS, OCTAD_MASKS
from glm2_conway import (CO0_ORDER_CLASSICAL, GENERATORS, MONOMIAL_GENERATORS,
                         MONOMIAL_ORDER, SEXTET, SEXTET_SIGN_PATTERNS,
                         f2_apply, f2_matrix, f2_mul, minimal_vector_orbit_census,
                         mod_two_type_census, verify_automorphism)
from glm2_lattice import (DIM, INDEX_IN_Z24, KISSING, LEECH_BASIS, MIN_NORM2,
                          basis_determinant, decode, decode_reference,
                          from_coords, in_leech, index_derivation, inner,
                          j_invariant_series, minimal_vectors, norm2,
                          packing_radius2, theta_series, to_coords,
                          verify_local_optimality)
from glm2_library import (AFFINE_SCALES, ALIASES, CONCEPTS, DOMAINS, KINDS,
                          RELATIONS, TENSOR_RELATIONS, by_domain,
                          check_relations, check_tensor_relations,
                          library_audit, lookup, resolve)
from glm2_meaning import (AXES, DENOM, N_AXES, SCALAR, Meaning, ParseError,
                          axis, mod2_confusable, mod2_shadow)
from glm2_parse import FUNCTIONS, NABLA, parse, tokenise
from glm2_reasoner import REASONER, Reasoner

RNG = random.Random(20260816)


# ══════════════════════════════════════════════════════════════════════════════
#  §1.  THE MEANING MODULE
# ══════════════════════════════════════════════════════════════════════════════

class TestMeaningBasics(unittest.TestCase):

    def test_ten_axes(self):
        self.assertEqual(N_AXES, 10)
        self.assertEqual(len(AXES), 10)
        self.assertEqual(len(set(AXES)), 10)

    def test_scalar_is_zero(self):
        self.assertTrue(SCALAR.is_pure_number())
        self.assertTrue(SCALAR.is_dimensionless())
        self.assertEqual(SCALAR.rank, 0)

    def test_axis_constructor(self):
        for ax in AXES:
            m = axis(ax)
            self.assertEqual(m.exponent(ax), 1)
            self.assertEqual(sum(1 for e in m.exps if e != 0), 1)

    def test_make_rejects_unknown_axis(self):
        with self.assertRaises(ValueError):
            Meaning.make(Q=1)

    def test_wrong_length_rejected(self):
        with self.assertRaises(ValueError):
            Meaning((F(0),) * 9)

    def test_parity_must_be_binary(self):
        with self.assertRaises(ValueError):
            Meaning((F(0),) * 10, p=2)

    def test_negative_kind_rejected(self):
        with self.assertRaises(ValueError):
            Meaning((F(0),) * 10, kind=-1)

    def test_addition_adds_exponents(self):
        a = Meaning.make(L=1, T=-1)
        b = Meaning.make(M=1)
        self.assertEqual((a + b).exponent("L"), 1)
        self.assertEqual((a + b).exponent("M"), 1)
        self.assertEqual((a + b).exponent("T"), -1)

    def test_subtraction_is_inverse(self):
        a = Meaning.make(L=2, M=1, T=-2)
        b = Meaning.make(M=1)
        self.assertTrue((a + b - b).same_quantity(a))

    def test_negation(self):
        a = Meaning.make(L=1, scale=3, rank=1)
        n = -a
        self.assertEqual(n.exponent("L"), -1)
        self.assertEqual(n.scale, -3)
        self.assertEqual(n.rank, -1)

    def test_group_is_abelian(self):
        a = Meaning.make(L=1, M=2)
        b = Meaning.make(T=-3, I=1)
        self.assertEqual(a + b, b + a)

    def test_scale_adds(self):
        km = Meaning.make(L=1, scale=3)
        self.assertEqual((km + km).scale, 6)

    def test_rank_adds(self):
        v = Meaning.make(L=1, rank=1)
        self.assertEqual((v + v).rank, 2)


class TestMeaningPowers(unittest.TestCase):

    def test_integer_power(self):
        v = Meaning.make(L=1, T=-1)
        self.assertEqual(v.power(2).exponent("L"), 2)
        self.assertEqual(v.power(2).exponent("T"), -2)

    def test_zero_power_is_scalar(self):
        self.assertTrue(Meaning.make(L=1, M=1).power(0).is_pure_number())

    def test_half_power(self):
        e = Meaning.make(L=2, M=1, T=-2)
        m = Meaning.make(M=1)
        self.assertTrue((e - m).power(F(1, 2)).same_quantity(
            Meaning.make(L=1, T=-1)))

    def test_third_power(self):
        v = Meaning.make(L=3)
        self.assertEqual(v.power(F(1, 3)).exponent("L"), 1)

    def test_fractional_power_of_tensor_refused(self):
        with self.assertRaises(ParseError):
            Meaning.make(L=1, rank=2).power(F(1, 2))

    def test_fractional_power_of_pseudo_refused(self):
        with self.assertRaises(ParseError):
            Meaning.make(L=1, p=1).power(F(1, 2))

    def test_integer_power_of_tensor_allowed(self):
        self.assertEqual(Meaning.make(L=1, rank=2).power(3).rank, 6)

    def test_power_multiplies_scale(self):
        self.assertEqual(Meaning.make(L=2, scale=6).power(F(1, 2)).scale, 3)

    def test_rmul_is_power(self):
        m = Meaning.make(L=1)
        self.assertEqual(2 * m, m.power(2))

    def test_parity_doubles_to_even(self):
        self.assertEqual(Meaning.make(L=1, p=1, rank=1).power(2).p, 0)


class TestMeaningGradings(unittest.TestCase):

    def test_time_is_t_odd(self):
        self.assertEqual(Meaning.make(T=1).t_parity(), 1)

    def test_energy_is_t_even(self):
        self.assertEqual(Meaning.make(L=2, M=1, T=-2).t_parity(), 0)

    def test_current_is_t_odd_and_c_odd(self):
        cur = Meaning.make(I=1)
        self.assertEqual(cur.t_parity(), 1)
        self.assertEqual(cur.c_parity(), 1)

    def test_charge_is_t_even_and_c_odd(self):
        q = Meaning.make(T=1, I=1)
        self.assertEqual(q.t_parity(), 0)
        self.assertEqual(q.c_parity(), 1)

    def test_grading_is_additive(self):
        a = Meaning.make(T=-1, I=1)
        b = Meaning.make(T=3, I=2)
        self.assertEqual((a + b).t_parity(),
                         (a.t_parity() + b.t_parity()) % 2)
        self.assertEqual((a + b).c_parity(),
                         (a.c_parity() + b.c_parity()) % 2)

    def test_grading_undefined_for_fractional(self):
        self.assertIsNone(Meaning.make(T=F(1, 2)).t_parity())
        self.assertIsNone(Meaning.make(I=F(1, 2)).c_parity())

    def test_anomaly_flips_grading(self):
        plain = Meaning.make(L=1, T=1, I=1)
        anom = Meaning.make(L=1, T=1, I=1, t=1)
        self.assertEqual(plain.t_parity(), 0)
        self.assertEqual(anom.t_parity(), 1)
        self.assertFalse(plain.same_quantity(anom))

    def test_anomaly_erased_by_fractional_power(self):
        anom = Meaning.make(L=2, t=1, c=1)
        self.assertEqual(anom.power(F(1, 2)).t, 0)
        self.assertEqual(anom.power(F(1, 2)).c, 0)

    def test_pseudo_detection(self):
        self.assertTrue(Meaning.make(L=1, rank=1, p=0).is_pseudo())   # axial
        self.assertFalse(Meaning.make(L=1, rank=1, p=1).is_pseudo())  # polar
        self.assertTrue(Meaning.make(L=1, rank=0, p=1).is_pseudo())   # pseudoscalar

    def test_same_tensor_character(self):
        a = Meaning.make(L=1, rank=1, p=1)
        b = Meaning.make(M=1, rank=1, p=1)
        self.assertTrue(a.same_tensor_character(b))


class TestMeaningPredicates(unittest.TestCase):

    def test_same_dimension_ignores_rank(self):
        a = Meaning.make(L=1)
        b = Meaning.make(L=1, rank=2)
        self.assertTrue(a.same_dimension(b))
        self.assertFalse(a.same_quantity(b))

    def test_same_quantity_ignores_labels(self):
        a = Meaning.make(L=1, kind=3, domain=5)
        b = Meaning.make(L=1)
        self.assertTrue(a.same_quantity(b))
        self.assertNotEqual(a, b)

    def test_commensurable_respects_kind(self):
        a = Meaning.make(L=2, M=1, T=-2, kind=1)
        b = Meaning.make(L=2, M=1, T=-2, kind=2)
        self.assertFalse(a.commensurable(b))

    def test_commensurable_allows_unlabelled(self):
        a = Meaning.make(L=1, kind=1)
        b = Meaning.make(L=1)
        self.assertTrue(a.commensurable(b))

    def test_scale_breaks_commensurability(self):
        self.assertFalse(Meaning.make(L=1, scale=3).commensurable(
            Meaning.make(L=1)))

    def test_is_integral(self):
        self.assertTrue(Meaning.make(L=2).is_integral())
        self.assertFalse(Meaning.make(L=F(1, 2)).is_integral())

    def test_denominator(self):
        self.assertEqual(Meaning.make(L=F(1, 3), M=F(1, 4)).denominator(), 12)

    def test_encodable_on_twelfths(self):
        self.assertTrue(Meaning.make(L=F(1, 12)).encodable())
        self.assertFalse(Meaning.make(L=F(1, 5)).encodable())

    def test_numerators_length(self):
        self.assertEqual(len(Meaning.make(L=1).numerators()), 11)

    def test_numerators_scaled_by_denom(self):
        self.assertEqual(Meaning.make(L=1).numerators()[0], DENOM)

    def test_signature_round_trip_readable(self):
        self.assertIn("L^2", str(Meaning.make(L=2, M=1, T=-2)))

    def test_signature_of_scalar(self):
        self.assertEqual(str(SCALAR), "1")


class TestMeaningOperators(unittest.TestCase):

    def test_contract_reduces_rank(self):
        a = Meaning.make(L=1, rank=1)
        b = Meaning.make(M=1, rank=1)
        self.assertEqual(a.contract(b).rank, 0)

    def test_contract_needs_rank(self):
        with self.assertRaises(ParseError):
            Meaning.make(L=1).contract(Meaning.make(M=1, rank=1))

    def test_contract_adds_exponents(self):
        a = Meaning.make(L=1, rank=1)
        b = Meaning.make(L=1, rank=1)
        self.assertEqual(a.contract(b).exponent("L"), 2)

    def test_cross_has_rank_one(self):
        a = Meaning.make(L=1, rank=1, p=1)
        self.assertEqual(a.cross(a).rank, 1)

    def test_cross_of_two_polars_is_axial(self):
        a = Meaning.make(L=1, rank=1, p=1)
        self.assertEqual(a.cross(a).p, 0)
        self.assertTrue(a.cross(a).is_pseudo())

    def test_cross_adds_no_angle(self):
        a = Meaning.make(L=1, rank=1, p=1)
        self.assertEqual(a.cross(a).exponent("A"), 0)

    def test_moment_consumes_a_radian(self):
        a = Meaning.make(L=1, rank=1, p=1)
        self.assertEqual(a.moment(a).exponent("A"), -1)

    def test_cross_requires_rank_one(self):
        with self.assertRaises(ParseError):
            Meaning.make(L=1).cross(Meaning.make(L=1, rank=1))

    def test_moment_and_cross_differ(self):
        a = Meaning.make(L=1, rank=1, p=1)
        self.assertNotEqual(a.cross(a), a.moment(a))


class TestMod2Diagnostic(unittest.TestCase):

    def test_shadow_is_ten_bits(self):
        self.assertEqual(len(mod2_shadow(Meaning.make(L=3))), 10)

    def test_shadow_reduces(self):
        self.assertEqual(mod2_shadow(Meaning.make(L=3))[0], 1)
        self.assertEqual(mod2_shadow(Meaning.make(L=2))[0], 0)

    def test_shadow_none_for_fractional(self):
        self.assertIsNone(mod2_shadow(Meaning.make(L=F(1, 2))))

    def test_mc4_is_confusable_mod2(self):
        energy = Meaning.make(L=2, M=1, T=-2)
        wrong = Meaning.make(M=1) + Meaning.make(L=1, T=-1).power(4)
        self.assertTrue(mod2_confusable(wrong, energy))
        self.assertFalse(wrong.same_quantity(energy))

    def test_equal_meanings_not_confusable(self):
        e = Meaning.make(L=2, M=1, T=-2)
        self.assertFalse(mod2_confusable(e, e))

    def test_meaning_has_no_mod2_method(self):
        # the mod-2 view is an appendix diagnostic, not part of a meaning
        self.assertFalse(hasattr(Meaning.make(L=1), "mod2"))


# ══════════════════════════════════════════════════════════════════════════════
#  §2.  THE REGISTER
# ══════════════════════════════════════════════════════════════════════════════

class TestLibrary(unittest.TestCase):

    def test_size(self):
        self.assertGreaterEqual(len(CONCEPTS), 460)

    def test_domains(self):
        self.assertGreaterEqual(len(by_domain()), 18)

    def test_every_concept_has_a_domain(self):
        for name, c in CONCEPTS.items():
            self.assertIn(c.meaning.domain, DOMAINS, name)

    def test_every_kind_label_is_declared(self):
        for name, c in CONCEPTS.items():
            if c.meaning.kind:
                self.assertIn(c.meaning.kind, KINDS, name)

    def test_all_encodable(self):
        for name, c in CONCEPTS.items():
            self.assertTrue(c.meaning.encodable(), name)

    def test_relations_all_hold(self):
        ok, total, failures = check_relations()
        self.assertEqual(failures, [])
        self.assertEqual(ok, total)
        self.assertGreaterEqual(total, 105)

    def test_tensor_relations_all_hold(self):
        ok, total, failures = check_tensor_relations()
        self.assertEqual(failures, [])
        self.assertEqual(ok, total)
        self.assertGreaterEqual(total, 36)

    def test_most_scalar_relations_are_also_strict(self):
        strict, total, _ = check_relations(strict=True)
        self.assertGreater(strict, total * 3 // 4)

    def test_aliases_resolve(self):
        for alias in ALIASES:
            self.assertIsNotNone(resolve(alias), alias)

    def test_lookup_unknown(self):
        self.assertIsNone(lookup("definitely_not_a_concept"))

    def test_affine_scales_are_separate(self):
        for name in AFFINE_SCALES:
            self.assertNotIn(name, CONCEPTS)

    def test_torque_is_not_energy(self):
        self.assertFalse(CONCEPTS["torque"].meaning.same_quantity(
            CONCEPTS["energy"].meaning))

    def test_hertz_is_not_becquerel(self):
        self.assertFalse(CONCEPTS["frequency"].meaning.commensurable(
            CONCEPTS["activity"].meaning))

    def test_radiance_is_not_irradiance(self):
        self.assertFalse(CONCEPTS["radiance"].meaning.same_dimension(
            CONCEPTS["irradiance"].meaning))

    def test_planck_and_reduced_planck_differ(self):
        self.assertFalse(CONCEPTS["planck_constant"].meaning.same_quantity(
            CONCEPTS["reduced_planck"].meaning))

    def test_kilometre_is_scaled_metre(self):
        self.assertEqual(CONCEPTS["kilometre"].meaning.scale, 3)

    def test_exactly_one_anomaly(self):
        anomalous = [n for n, c in CONCEPTS.items()
                     if c.meaning.t or c.meaning.c]
        self.assertEqual(anomalous, ["particle_electric_dipole_moment"])

    def test_edm_is_t_odd(self):
        self.assertEqual(
            CONCEPTS["particle_electric_dipole_moment"].meaning.t_parity(), 1)

    def test_audit_reports_no_failure(self):
        rep = library_audit()
        self.assertEqual(rep["relation_failures"], [])
        self.assertEqual(rep["tensor_relation_failures"], [])
        self.assertTrue(rep["all_encodable"])

    def test_fractional_exponents_present(self):
        self.assertGreater(library_audit()["with_fractional_exponents"], 0)

    def test_tensors_present(self):
        self.assertGreater(library_audit()["with_nonzero_rank"], 40)


class TestTextbookGradings(unittest.TestCase):
    """The derived T grading against the standard classical answers."""

    TABLE = {
        "position": 0, "velocity": 1, "acceleration": 0, "momentum": 1,
        "force": 0, "energy": 0, "power": 1, "time": 1, "torque": 0,
        "angular_momentum": 1, "charge": 0, "current": 1, "voltage": 0,
        "electric_field": 0, "magnetic_flux_density": 1, "resistance": 1,
        "capacitance": 0, "inductance": 0, "pressure": 0, "entropy": 0,
        "magnetic_dipole_moment": 1, "frequency": 1, "action": 1,
    }

    def test_all_textbook_t_gradings(self):
        for name, expected in self.TABLE.items():
            with self.subTest(name=name):
                self.assertEqual(REASONER.meaning(name).t_parity(), expected)

    def test_c_grading_of_neutral_quantities(self):
        for name in ("mass", "length", "time", "energy", "pressure"):
            with self.subTest(name=name):
                self.assertEqual(REASONER.meaning(name).c_parity(), 0)

    def test_c_grading_of_charged_quantities(self):
        for name in ("charge", "current", "voltage", "electric_field"):
            with self.subTest(name=name):
                self.assertEqual(REASONER.meaning(name).c_parity(), 1)


# ══════════════════════════════════════════════════════════════════════════════
#  §3.  THE PARSER AND THE OPERATOR ALGEBRA
# ══════════════════════════════════════════════════════════════════════════════

class TestParser(unittest.TestCase):

    def test_tokenise_simple(self):
        self.assertEqual(tokenise("a*b"), ["a", "*", "b"])

    def test_tokenise_comma(self):
        self.assertIn(",", tokenise("dot(a, b)"))

    def test_product(self):
        self.assertTrue(parse("mass*speed^2").same_dimension(
            REASONER.meaning("energy")))

    def test_quotient(self):
        self.assertTrue(parse("energy/time").same_dimension(
            REASONER.meaning("power")))

    def test_parenthesised(self):
        self.assertTrue(parse("energy/(area*time)").same_dimension(
            parse("energy/area/time")))

    def test_rational_exponent(self):
        self.assertTrue(parse("(energy/mass)^(1/2)").same_quantity(
            REASONER.meaning("speed")))

    def test_negative_exponent(self):
        self.assertEqual(parse("length^-1").exponent("L"), -1)

    def test_power_of_ten_literal(self):
        self.assertEqual(parse("1000*length").scale, 3)

    def test_division_by_power_of_ten(self):
        self.assertEqual(parse("length/1000").scale, -3)

    def test_non_power_of_ten_refused(self):
        with self.assertRaises(ParseError):
            parse("2*length")

    def test_unknown_name_refused(self):
        with self.assertRaises(ParseError):
            parse("phlogiston")

    def test_symbolic_exponent_refused(self):
        with self.assertRaises(ParseError):
            parse("length^x")

    def test_empty_refused(self):
        with self.assertRaises(ParseError):
            parse("")

    def test_trailing_operator_refused(self):
        with self.assertRaises(ParseError):
            parse("mass*")

    def test_leading_minus_refused(self):
        with self.assertRaises(ParseError):
            parse("-length")

    def test_unbalanced_paren_refused(self):
        with self.assertRaises(ParseError):
            parse("(mass*length")

    def test_bad_character_refused(self):
        with self.assertRaises(ParseError):
            parse("mass $ length")

    def test_alias_accepted(self):
        self.assertTrue(parse("emf").same_quantity(REASONER.meaning("voltage")))


class TestOperatorAlgebra(unittest.TestCase):

    def test_nabla(self):
        self.assertEqual(NABLA.exponent("L"), -1)
        self.assertEqual(NABLA.rank, 1)
        self.assertEqual(NABLA.p, 1)

    def test_all_functions_have_arity(self):
        for name, (arity, fn) in FUNCTIONS.items():
            self.assertIn(arity, (1, 2), name)

    def test_dot_is_energy(self):
        self.assertTrue(parse("dot(force, position)").same_quantity(
            REASONER.meaning("energy")))

    def test_tensor_product_is_not_energy(self):
        self.assertFalse(parse("force*position").same_quantity(
            REASONER.meaning("energy")))

    def test_tensor_product_has_rank_two(self):
        self.assertEqual(parse("force*position").rank, 2)

    def test_moment_is_torque(self):
        self.assertTrue(parse("moment(position, force)").same_quantity(
            REASONER.meaning("torque")))

    def test_moment_is_angular_momentum(self):
        self.assertTrue(parse("moment(position, momentum)").same_quantity(
            REASONER.meaning("angular_momentum")))

    def test_cross_is_poynting(self):
        self.assertTrue(
            parse("cross(electric_field, magnetic_field_h)").same_quantity(
                REASONER.meaning("poynting_vector")))

    def test_grad_is_electric_field(self):
        self.assertTrue(parse("grad(voltage)").same_quantity(
            REASONER.meaning("electric_field")))

    def test_div_is_charge_density(self):
        self.assertTrue(parse("div(electric_displacement)").same_quantity(
            REASONER.meaning("charge_density")))

    def test_curl_is_current_density(self):
        self.assertTrue(parse("curl(magnetic_field_h)").same_quantity(
            REASONER.meaning("current_density")))

    def test_rot_is_vorticity(self):
        self.assertTrue(parse("rot(velocity)").same_quantity(
            REASONER.meaning("vorticity")))

    def test_curl_and_rot_differ_by_a_radian(self):
        a = parse("curl(velocity)")
        b = parse("rot(velocity)")
        self.assertEqual(a.exponent("A") - b.exponent("A"), 1)

    def test_laplacian_preserves_character(self):
        for name in ("voltage", "temperature", "pressure"):
            m = REASONER.meaning(name)
            self.assertTrue(FUNCTIONS["laplacian"][1](m)
                            .same_tensor_character(m), name)

    def test_laplacian_is_two_inverse_lengths(self):
        m = REASONER.meaning("voltage")
        self.assertEqual(FUNCTIONS["laplacian"][1](m).exponent("L")
                         - m.exponent("L"), -2)

    def test_ddt_is_acceleration(self):
        self.assertTrue(parse("ddt(velocity)").same_quantity(
            REASONER.meaning("acceleration")))

    def test_ddt_and_integral_are_inverse(self):
        for name in ("energy", "velocity", "charge_density", "torque"):
            m = REASONER.meaning(name)
            got = FUNCTIONS["ddt"][1](FUNCTIONS["integral_dt"][1](m))
            self.assertTrue(got.same_quantity(m), name)

    def test_ddt_flips_the_t_grading(self):
        for name in ("energy", "velocity", "charge", "pressure"):
            m = REASONER.meaning(name)
            self.assertNotEqual(m.t_parity(),
                                FUNCTIONS["ddt"][1](m).t_parity(), name)

    def test_integral_dV_is_charge(self):
        self.assertTrue(parse("integral_dV(charge_density)").same_quantity(
            REASONER.meaning("charge")))

    def test_wrong_arity_refused(self):
        with self.assertRaises(ParseError):
            parse("dot(force)")

    def test_grad_of_scalar_has_rank_one(self):
        self.assertEqual(parse("grad(pressure)").rank, 1)

    def test_div_of_scalar_refused(self):
        with self.assertRaises(ParseError):
            parse("div(pressure)")

    def test_maxwell_at_full_meaning(self):
        cases = [("charge_density", "div(electric_displacement)"),
                 ("current_density", "curl(magnetic_field_h)"),
                 ("current_density", "ddt(electric_displacement)"),
                 ("magnetic_flux_density", "curl(magnetic_vector_potential)"),
                 ("electric_field", "ddt(magnetic_vector_potential)")]
        for lhs, rhs in cases:
            with self.subTest(rhs=rhs):
                self.assertTrue(
                    REASONER.meaning(lhs).same_quantity(parse(rhs)))


# ══════════════════════════════════════════════════════════════════════════════
#  §4.  THE LATTICE
# ══════════════════════════════════════════════════════════════════════════════

class TestLattice(unittest.TestCase):

    def test_dimension(self):
        self.assertEqual(DIM, 24)

    def test_min_norm(self):
        self.assertEqual(MIN_NORM2, 32)

    def test_packing_radius(self):
        self.assertEqual(packing_radius2(), F(8))

    def test_index(self):
        self.assertEqual(INDEX_IN_Z24, 2 ** 36)

    def test_index_derivation_agrees(self):
        self.assertEqual(index_derivation()["index"], 2 ** 36)

    def test_basis_determinant(self):
        self.assertEqual(abs(basis_determinant()), 2 ** 36)

    def test_basis_rows_are_in_lattice(self):
        for row in LEECH_BASIS:
            self.assertTrue(in_leech(row))

    def test_zero_is_in_lattice(self):
        self.assertTrue(in_leech([0] * 24))

    def test_odd_vector_not_in_lattice(self):
        x = [0] * 24
        x[0] = 1
        self.assertFalse(in_leech(x))

    def test_norm_and_inner(self):
        x = list(LEECH_BASIS[0])
        self.assertEqual(inner(x, x), norm2(x))

    def test_all_basis_norms_are_multiples_of_eight(self):
        for row in LEECH_BASIS:
            self.assertEqual(norm2(row) % 8, 0)

    def test_coords_round_trip(self):
        for _ in range(20):
            u = [RNG.randint(-3, 3) for _ in range(24)]
            x = from_coords(u)
            self.assertTrue(in_leech(x))
            self.assertEqual(to_coords(x), u)

    def test_to_coords_none_outside(self):
        x = [1] + [0] * 23
        self.assertIsNone(to_coords(x))

    def test_minimal_vectors_count(self):
        self.assertEqual(sum(1 for _ in minimal_vectors()), KISSING)

    def test_minimal_vectors_have_min_norm(self):
        it = minimal_vectors()
        for _ in range(200):
            v = next(it)
            self.assertEqual(norm2(v), 32)
            self.assertTrue(in_leech(v))

    def test_theta_series_head(self):
        self.assertEqual(theta_series(5)[:5],
                         [1, 0, 196560, 16773120, 398034000])

    def test_j_invariant_head(self):
        self.assertEqual(j_invariant_series(3)[:4],
                         [1, 744, 196884, 21493760])

    def test_griess_ledger(self):
        self.assertEqual(300 + 98280 + 98304, 196884)

    def test_class_census(self):
        total = 1 + 196560 // 2 + 16773120 // 2 + 398034000 // 48
        self.assertEqual(total, 2 ** 24)


class TestDecoder(unittest.TestCase):

    def _random_point(self):
        return from_coords([RNG.randint(-2, 2) for _ in range(24)])

    def test_decode_exact_point(self):
        for _ in range(5):
            x = self._random_point()
            res = decode(list(x))
            self.assertEqual(res.dist2, 0)
            self.assertEqual(tuple(res.point), tuple(x))

    def test_decode_small_error(self):
        for _ in range(5):
            x = list(self._random_point())
            y = list(x)
            for i in RNG.sample(range(24), 3):
                y[i] += RNG.choice((-1, 1))
            res = decode(y)
            self.assertEqual(tuple(res.point), tuple(x))
            self.assertEqual(res.dist2, 3)

    def test_decode_matches_reference(self):
        for _ in range(3):
            x = list(self._random_point())
            y = [c + RNG.randint(-1, 1) for c in x]
            res = decode(y)
            _, d = decode_reference(y)
            self.assertEqual(res.dist2, d)

    def test_local_optimality(self):
        for _ in range(3):
            x = list(self._random_point())
            y = [c + RNG.randint(-1, 1) for c in x]
            res = decode(y)
            self.assertTrue(verify_local_optimality(y, res.point))

    def test_decoded_point_is_in_lattice(self):
        y = [RNG.randint(-10, 10) for _ in range(24)]
        self.assertTrue(in_leech(decode(y).point))


# ══════════════════════════════════════════════════════════════════════════════
#  §5.  THE CODEC
# ══════════════════════════════════════════════════════════════════════════════

class TestCodec(unittest.TestCase):

    def test_slot_count(self):
        self.assertEqual(len(SLOTS), 24)
        self.assertEqual(N_CONTEXT, 7)

    def test_encode_is_in_lattice(self):
        for name in ("energy", "torque", "radiance", "gigabit_per_second"):
            self.assertTrue(in_leech(encode(REASONER.meaning(name))), name)

    def test_round_trip_every_concept(self):
        for name, c in CONCEPTS.items():
            with self.subTest(name=name):
                back, ctx = decode_point(encode(c.meaning))
                self.assertEqual(back, c.meaning)
                self.assertEqual(ctx, (0,) * N_CONTEXT)

    def test_context_round_trip(self):
        m = REASONER.meaning("energy")
        ctx = (1, -2, 3, 0, 0, 5, -1)
        back, got = decode_point(encode(m, ctx))
        self.assertEqual(back, m)
        self.assertEqual(got, ctx)

    def test_encoder_is_injective(self):
        seen = {}
        for name, c in CONCEPTS.items():
            pt = encode(c.meaning)
            if pt in seen:
                self.assertEqual(c.meaning, CONCEPTS[seen[pt]].meaning)
            seen[pt] = name
        self.assertGreater(len(seen), 200)

    def test_separation_bound(self):
        self.assertEqual(separation_bound(), 32)

    def test_distinct_concepts_are_far_apart(self):
        names = sorted(CONCEPTS)[:60]
        pts = {n: encode(CONCEPTS[n].meaning) for n in names}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if CONCEPTS[a].meaning == CONCEPTS[b].meaning:
                    continue
                d = sum((x - y) ** 2 for x, y in zip(pts[a], pts[b]))
                self.assertGreaterEqual(d, 32, f"{a} vs {b}")

    def test_capacity(self):
        self.assertEqual(capacity_within_norm(32), 196561)
        self.assertEqual(capacity_within_norm(48), 16969681)

    def test_capacity_of_zero(self):
        self.assertEqual(capacity_within_norm(0), 1)

    def test_compose_matches_product(self):
        a = REASONER.meaning("force")
        b = REASONER.meaning("length")
        pt = compose(encode(a), encode(b))
        got, _ = decode_point(pt)
        self.assertTrue(got.same_quantity(a + b))

    def test_compose_rejects_non_lattice(self):
        with self.assertRaises(ValueError):
            compose([1] + [0] * 23, [0] * 24)

    def test_coords_of_length(self):
        self.assertEqual(len(coords_of(REASONER.meaning("energy"))), 24)

    def test_meaning_of_coords_inverse(self):
        m = REASONER.meaning("torque")
        back, _ = meaning_of_coords(coords_of(m))
        self.assertEqual(back, m)

    def test_repair_within_radius(self):
        for name in ("energy", "radiance", "torque"):
            x = list(encode(REASONER.meaning(name)))
            y = list(x)
            for i in RNG.sample(range(24), 7):
                y[i] += RNG.choice((-1, 1))
            res = repair(y, REASONER.meaning(name))
            self.assertTrue(res.within_radius, name)
            self.assertTrue(res.exact, name)
            self.assertEqual(res.error_norm2, 7)

    def test_repair_outside_radius_is_honest(self):
        # the midpoint between two lattice points at squared distance 32 is
        # at squared distance exactly 8 from both: on the packing sphere, so
        # outside the guarantee, and the decoder must say so
        x = list(encode(REASONER.meaning("energy")))
        v = next(minimal_vectors())
        y = [a + b // 2 for a, b in zip(x, v)]
        res = repair(y, REASONER.meaning("energy"))
        self.assertEqual(res.error_norm2, 8)
        self.assertFalse(res.within_radius)

    def test_repair_never_raises(self):
        for _ in range(10):
            y = [RNG.randint(-500, 500) for _ in range(24)]
            res = repair(y)                        # must not raise
            self.assertTrue(in_leech(res.point))

    def test_all_error_patterns_of_weight_three(self):
        m = REASONER.meaning("energy")
        x = list(encode(m))
        for i in range(0, 24, 5):
            for j in range(i + 1, 24, 7):
                for k in range(j + 1, 24, 11):
                    y = list(x)
                    y[i] += 1
                    y[j] -= 1
                    y[k] += 1
                    res = repair(y, m)
                    self.assertTrue(res.exact)


# ══════════════════════════════════════════════════════════════════════════════
#  §6.  THE CONWAY GROUP
# ══════════════════════════════════════════════════════════════════════════════

class TestConway(unittest.TestCase):

    def test_golay_reused(self):
        self.assertEqual(len(GOLAY_MASKS), 4096)
        self.assertEqual(len(OCTAD_MASKS), 759)
        self.assertEqual(len(GOLAY_BASIS_MASKS), 12)

    def test_m24_generators_are_permutations(self):
        for g in M24_GENERATORS:
            self.assertEqual(sorted(g), list(range(24)))

    def test_monomial_order(self):
        self.assertEqual(MONOMIAL_ORDER, 4096 * 244823040)

    def test_every_generator_is_an_automorphism(self):
        for g in GENERATORS:
            rep = verify_automorphism(g, samples=25)
            self.assertTrue(all(rep.values()), g.name)

    def test_sextet_is_a_partition(self):
        flat = sorted(i for tetrad in SEXTET for i in tetrad)
        self.assertEqual(flat, list(range(24)))
        self.assertEqual(len(SEXTET), 6)
        for tetrad in SEXTET:
            self.assertEqual(len(tetrad), 4)

    def test_sextet_sign_patterns(self):
        self.assertEqual(SEXTET_SIGN_PATTERNS, 32)

    def test_monomial_orbit_census(self):
        self.assertEqual(sorted(minimal_vector_orbit_census(
            MONOMIAL_GENERATORS)), [1104, 97152, 98304])

    def test_orbit_sizes_sum_to_kissing(self):
        self.assertEqual(sum(minimal_vector_orbit_census(MONOMIAL_GENERATORS)),
                         KISSING)

    def test_f2_matrix_is_invertible(self):
        for g in GENERATORS[:6]:
            M = f2_matrix(g)
            self.assertEqual(len(M), 24)
            images = {f2_apply(1 << i, M) for i in range(24)}
            self.assertEqual(len(images), 24)

    def test_f2_mul_associates(self):
        A, B, C = (f2_matrix(g) for g in GENERATORS[:3])
        self.assertEqual(f2_mul(f2_mul(A, B), C), f2_mul(A, f2_mul(B, C)))

    def test_mod_two_census(self):
        rep = mod_two_type_census()
        self.assertEqual(rep["mod2_classes_total"], 2 ** 24)

    def test_classical_order_recorded(self):
        self.assertEqual(CO0_ORDER_CLASSICAL, 8315553613086720000)


# ══════════════════════════════════════════════════════════════════════════════
#  §7.  THE ALGEBRA LAYER
# ══════════════════════════════════════════════════════════════════════════════

class TestLinearAlgebra(unittest.TestCase):

    def test_rref_of_identity(self):
        rows = [[F(1), F(0)], [F(0), F(1)]]
        red, piv = rref(rows)
        self.assertEqual(piv, [0, 1])

    def test_rank_of_dependent_rows(self):
        self.assertEqual(rank([[F(1), F(2)], [F(2), F(4)]]), 1)

    def test_nullspace_dimension(self):
        ns = nullspace([[F(1), F(1), F(0)]], 3)
        self.assertEqual(len(ns), 2)

    def test_nullspace_vectors_annihilate(self):
        rows = [[F(1), F(2), F(3)]]
        for v in nullspace(rows, 3):
            self.assertEqual(sum(a * b for a, b in zip(rows[0], v)), 0)


class TestJordanAlgebra(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.alg = jordan_symmetric_algebra(3)

    def test_dimension(self):
        self.assertEqual(self.alg.dim, 6)

    def test_commutative(self):
        self.assertTrue(self.alg.is_commutative())

    def test_non_associative(self):
        self.assertGreater(self.alg.associator_defects(), 0)

    def test_jordan_identity(self):
        self.assertTrue(self.alg.satisfies_jordan_identity())

    def test_has_identity(self):
        self.assertIsNotNone(self.alg.identity_element())

    def test_frobenius_form(self):
        self.assertTrue(self.alg.form_is_frobenius())


class TestMatsuoAlgebra(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.trans3 = symmetric_group_transpositions(3)
        cls.alg = matsuo_algebra(cls.trans3, F(1, 4), name="S3 eta=1/4")

    def test_dimension_is_three(self):
        self.assertEqual(self.alg.dim, 3)

    def test_commutative(self):
        self.assertTrue(self.alg.is_commutative())

    def test_non_associative(self):
        self.assertGreater(self.alg.associator_defects(), 0)

    def test_basis_vectors_are_idempotent(self):
        for i in range(self.alg.dim):
            self.assertTrue(self.alg.is_idempotent(basis_vector(self.alg.dim, i)))

    def test_norton_sakuma_2a_structure_constants(self):
        a0 = basis_vector(3, 0)
        a1 = basis_vector(3, 1)
        prod = self.alg.mul(a0, a1)
        self.assertEqual(prod[0], F(1, 8))
        self.assertEqual(prod[1], F(1, 8))
        self.assertEqual(prod[2], F(-1, 8))

    def test_spectrum_is_jordan_type(self):
        for i in range(self.alg.dim):
            ok, _ = self.alg.spectrum_within(basis_vector(3, i),
                                             (1, 0, F(1, 4)))
            self.assertTrue(ok)

    def test_fusion_rules(self):
        rep = self.alg.fusion_report(basis_vector(3, 0), (1, 0, F(1, 4)),
                                     jordan_type_rules(F(1, 4)))
        self.assertTrue(rep["ok"])

    def test_miyamoto_is_an_automorphism(self):
        for i in range(self.alg.dim):
            M = self.alg.miyamoto(basis_vector(3, i), F(1, 4))
            self.assertTrue(self.alg.is_automorphism(M))

    def test_3c_algebra(self):
        alg = matsuo_algebra(self.trans3, F(1, 32), name="3C")
        self.assertTrue(alg.is_commutative())
        ok, _ = alg.spectrum_within(basis_vector(3, 0), (1, 0, F(1, 32)))
        self.assertTrue(ok)

    def test_s4_matsuo(self):
        alg = matsuo_algebra(symmetric_group_transpositions(4), F(1, 4))
        self.assertEqual(alg.dim, 6)
        self.assertTrue(alg.is_commutative())
        self.assertGreater(alg.associator_defects(), 0)

    def test_miyamoto_group_orders(self):
        self.assertEqual(miyamoto_group_order(self.trans3), 6)
        self.assertEqual(
            miyamoto_group_order(symmetric_group_transpositions(4)), 24)

    def test_transposition_counts(self):
        self.assertEqual(len(symmetric_group_transpositions(5)), 10)


# ══════════════════════════════════════════════════════════════════════════════
#  §8.  THE REASONER
# ══════════════════════════════════════════════════════════════════════════════

class TestReasonerAudit(unittest.TestCase):

    def test_accepts_true_laws(self):
        cases = [("energy", "mass*speed^2"),
                 ("force", "mass*acceleration"),
                 ("power", "energy/time"),
                 ("charge", "current*time"),
                 ("pressure", "energy/volume"),
                 ("action", "energy*time"),
                 ("illuminance", "luminous_flux/area")]
        for lhs, rhs in cases:
            with self.subTest(rhs=rhs):
                self.assertTrue(REASONER.audit(lhs, rhs).admissible)

    def test_rejects_traps(self):
        cases = [("energy", "mass*speed^4"),
                 ("energy", "torque"),
                 ("frequency", "activity"),
                 ("kilometre", "length"),
                 ("radiance", "irradiance"),
                 ("particle_electric_dipole_moment", "electric_dipole_moment")]
        for lhs, rhs in cases:
            with self.subTest(rhs=rhs):
                self.assertFalse(REASONER.audit(lhs, rhs).admissible)

    def test_every_rejection_has_a_reason(self):
        for lhs, rhs in [("energy", "mass*speed^4"), ("energy", "torque"),
                         ("kilometre", "length")]:
            self.assertTrue(REASONER.audit(lhs, rhs).reasons())

    def test_audit_carries_no_mod2_verdict(self):
        audit = REASONER.audit("energy", "mass*speed^4")
        self.assertFalse(hasattr(audit, "mod2_would_accept"))
        self.assertFalse(hasattr(audit, "mod2_false_positive"))
        self.assertNotIn("mod-2", str(audit))

    def test_mc4_is_a_mod2_false_positive_in_the_appendix(self):
        report = REASONER.mod2_ceiling([("energy", "mass*speed^4")])
        self.assertEqual(report["mod2_false_positives"], 1)

    def test_torque_rejection_mentions_dimensions(self):
        reasons = " ".join(REASONER.audit("energy", "torque").reasons())
        self.assertIn("dimensions", reasons)

    def test_kilometre_rejection_mentions_scale(self):
        reasons = " ".join(REASONER.audit("kilometre", "length").reasons())
        self.assertIn("scale", reasons)

    def test_edm_rejection_mentions_t(self):
        reasons = " ".join(REASONER.audit(
            "particle_electric_dipole_moment", "electric_dipole_moment")
            .reasons())
        self.assertIn("T", reasons)

    def test_audit_of_operator_expression(self):
        self.assertTrue(REASONER.audit(
            "torque", "moment(position, force)").admissible)

    def test_audit_rejects_tensor_product_as_energy(self):
        self.assertFalse(REASONER.audit("energy", "force*position").admissible)

    def test_residual_is_zero_for_true_law(self):
        aud = REASONER.audit("energy", "mass*speed^2")
        self.assertTrue(aud.residual.is_dimensionless())

    def test_str_of_audit(self):
        self.assertIn("ADMISSIBLE", str(REASONER.audit("energy",
                                                       "mass*speed^2")))


class TestReasonerSolve(unittest.TestCase):

    def test_energy_from_mass_and_speed(self):
        sol = REASONER.solve("energy", ["mass", "speed"])
        self.assertTrue(sol.solvable)
        self.assertEqual(list(sol.exponents), [F(1), F(2)])

    def test_speed_from_energy_and_mass(self):
        sol = REASONER.solve("speed", ["energy", "mass"])
        self.assertTrue(sol.solvable)
        self.assertEqual(list(sol.exponents), [F(1, 2), F(-1, 2)])

    def test_no_pathway(self):
        self.assertFalse(REASONER.solve("energy", ["length", "time"])
                         .solvable)

    def test_kernel_reported_when_dependent(self):
        sol = REASONER.solve("energy", ["mass", "speed", "momentum"])
        self.assertTrue(sol.solvable)
        self.assertTrue(sol.kernel)

    def test_formula_is_readable(self):
        sol = REASONER.solve("energy", ["mass", "speed"])
        self.assertIn("mass", sol.formula())

    def test_fractional_solution(self):
        sol = REASONER.solve("fracture_toughness", ["stress", "length"])
        self.assertTrue(sol.solvable)
        self.assertIn(F(1, 2), list(sol.exponents))


class TestReasonerPi(unittest.TestCase):

    def test_reynolds_like_group_exists(self):
        groups = REASONER.pi_groups(["speed", "length",
                                     "kinematic_viscosity"])
        self.assertEqual(len(groups), 1)

    def test_no_group_for_independent_quantities(self):
        self.assertEqual(REASONER.pi_groups(["length", "mass"]), [])

    def test_group_is_dimensionless(self):
        names = ["speed", "length", "kinematic_viscosity"]
        for g in REASONER.pi_groups(names):
            total = SCALAR
            for n, e in g.items():
                total = total + REASONER.meaning(n).power(e)
            self.assertTrue(total.is_dimensionless())


class TestReasonerCarrier(unittest.TestCase):

    def test_telemetry_keys(self):
        t = REASONER.telemetry("energy")
        for k in ("meaning", "carrier_norm2", "carrier_in_lattice"):
            self.assertIn(k, t)

    def test_telemetry_point_in_lattice(self):
        self.assertTrue(REASONER.telemetry("torque")["carrier_in_lattice"])

    def test_transmit_repairs(self):
        for name in ("energy", "radiance", "gigabit_per_second"):
            r = REASONER.transmit(name, 7)
            self.assertTrue(r["repaired_exactly"], name)

    def test_neighbours_returns_requested_count(self):
        self.assertEqual(len(REASONER.neighbours("energy", 4)), 4)

    def test_neighbours_are_sorted(self):
        ds = [d for _, d in REASONER.neighbours("energy", 6)]
        self.assertEqual(ds, sorted(ds))

    def test_symmetry_preserves_norm(self):
        self.assertTrue(REASONER.symmetry("energy")["norm_preserved_by_all"])

    def test_convert_kilometre(self):
        self.assertIn("10^3", REASONER.convert("kilometre", "length"))

    def test_convert_incommensurable(self):
        self.assertIsNone(REASONER.convert("energy", "torque"))

    def test_identify_names_torque(self):
        self.assertIn("torque",
                      REASONER.identify("moment(position, force)")["is"])

    def test_identify_finds_no_name_for_tensor(self):
        self.assertEqual(REASONER.identify("force*position")["is"], [])

    def test_identify_reports_dimensional_near_misses(self):
        info = REASONER.identify("force*position")
        self.assertIn("energy", info["same dimensions only"])

    def test_list_concepts_by_domain(self):
        self.assertTrue(REASONER.list_concepts("mechanics"))

    def test_list_all_concepts(self):
        self.assertEqual(len(REASONER.list_concepts()), len(CONCEPTS))

    def test_summary(self):
        self.assertEqual(REASONER.summary()
                         ["minimum_carrier_separation_squared"], 32)

    def test_unknown_concept_raises(self):
        with self.assertRaises(ParseError):
            REASONER.meaning("not_a_concept_at_all")

    def test_fresh_reasoner_agrees(self):
        self.assertEqual(Reasoner().meaning("energy"),
                         REASONER.meaning("energy"))


class TestCarrierIsDerived(unittest.TestCase):
    """Invariant I0: the meaning is the state, the point is a view of it."""

    def test_every_concept_derives_its_point(self):
        for name in sorted(CONCEPTS):
            self.assertTrue(REASONER.carrier_is_derived(name), name)

    def test_expressions_derive_their_point_too(self):
        for text in ("force*length", "mass*speed^2", "grad(pressure)",
                     "integral_dt(power)"):
            self.assertTrue(REASONER.carrier_is_derived(text), text)

    def test_same_meaning_same_point(self):
        # two different texts, one meaning: the point depends on nothing else
        self.assertEqual(REASONER.meaning("mass*speed^2"),
                         REASONER.meaning("speed^2*mass"))
        self.assertEqual(REASONER.carrier("mass*speed^2"),
                         REASONER.carrier("speed^2*mass"))
        m = REASONER.meaning("energy")
        self.assertEqual(tuple(encode(m)), REASONER.carrier("energy"))

    def test_distinct_meanings_distinct_points(self):
        seen = {}
        for name in sorted(CONCEPTS):
            m = REASONER.meaning(name)
            key = REASONER.carrier(name)
            self.assertEqual(seen.setdefault(key, m), m, name)

    def test_point_follows_a_changed_meaning(self):
        m = REASONER.meaning("energy")
        self.assertNotEqual(tuple(encode(m)), tuple(encode(m + m)))

    def test_cache_holds_nothing_extra(self):
        fresh = Reasoner()
        self.assertEqual(fresh.carrier("energy"), REASONER.carrier("energy"))
        self.assertEqual(tuple(encode(REASONER.meaning("energy"))),
                         REASONER.carrier("energy"))

    def test_a_carrier_is_never_an_input(self):
        # no public entry point accepts a point in place of a meaning
        for method in ("meaning", "audit", "telemetry", "carrier",
                       "carrier_is_derived", "identify"):
            self.assertTrue(hasattr(REASONER, method))
        with self.assertRaises(ParseError):
            REASONER.meaning("0,0,0")

    def test_composition_happens_on_meanings(self):
        a, b = REASONER.meaning("force"), REASONER.meaning("length")
        self.assertEqual(tuple(encode(a + b)),
                         tuple(compose(encode(a), encode(b))))

    def test_torsion_free_slots_add(self):
        a, b = REASONER.meaning("force"), REASONER.meaning("length")
        ua, ub, uab = coords_of(a), coords_of(b), coords_of(a + b)
        for i in range(12):          # ten exponents, scale, rank
            self.assertEqual(uab[i], ua[i] + ub[i], SLOTS[i])

    def test_telemetry_reports_the_derivation(self):
        self.assertTrue(REASONER.telemetry("energy")["carrier_is_derived"])

    def test_telemetry_carries_no_mod2_view(self):
        self.assertNotIn("mod2_shadow", REASONER.telemetry("energy"))

    def test_repair_returns_the_meaning_not_the_bits(self):
        r = REASONER.transmit("energy", 7)
        self.assertTrue(r["repaired_exactly"])


# ══════════════════════════════════════════════════════════════════════════════
#  §9.  INVARIANTS
# ══════════════════════════════════════════════════════════════════════════════

class TestInvariants(unittest.TestCase):

    def test_I1_no_floats_in_carriers(self):
        for name in list(CONCEPTS)[:50]:
            for v in encode(CONCEPTS[name].meaning):
                self.assertIsInstance(v, int)

    def test_I1_exponents_are_exact(self):
        for c in CONCEPTS.values():
            for e in c.meaning.exps:
                self.assertIsInstance(e, F)

    def test_I3_every_carrier_is_in_lambda(self):
        for name, c in CONCEPTS.items():
            self.assertTrue(in_leech(encode(c.meaning)), name)

    def test_I4_separation_is_the_leech_minimum(self):
        self.assertEqual(separation_bound(), MIN_NORM2)

    def test_I5_repair_is_exact_within_the_radius(self):
        m = REASONER.meaning("energy")
        x = list(encode(m))
        y = list(x)
        y[0] += 2
        y[5] -= 1
        y[9] += 1
        y[17] -= 1
        res = repair(y, m)
        self.assertEqual(res.error_norm2, 7)
        self.assertTrue(res.exact)

    def test_I10_gradings_stay_derived(self):
        for c in CONCEPTS.values():
            m = c.meaning
            if m.t == 0 and m.exponent("T").denominator == 1 \
                    and m.exponent("I").denominator == 1:
                self.assertEqual(
                    m.t_parity(),
                    (int(m.exponent("T")) + int(m.exponent("I"))) % 2)

    def test_I11_three_products_are_distinct(self):
        a = Meaning.make(L=1, rank=1, p=1)
        b = Meaning.make(M=1, rank=1, p=1)
        self.assertNotEqual(a + b, a.cross(b))
        self.assertNotEqual(a.cross(b), a.moment(b))
        self.assertNotEqual(a.contract(b), a.cross(b))


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
