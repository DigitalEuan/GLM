#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 TEST SUITE
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Role   :  independent verification of every module, at a finer grain than
            the numbered claims of glm3_paper.py.

  The paper checks that the SYSTEM does what the paper says.  This suite
  checks that each PART does what its docstring says, including the edge
  cases the paper has no reason to mention: the zero class, negative
  coordinates in the 2-adic stack, both signs of an axis, concepts with no
  axis at all, the degenerate plane 0, unknown concept names, and the
  algebraic identities (commutativity, Frobenius, non-associativity) on
  randomly chosen elements rather than on the ones the paper picked.

      python3 test_glm3.py                # the whole suite (145 tests, ~37 s)
      python3 test_glm3.py -v             # with the name of every test
      python3 test_glm3.py TestGriess     # one class

  Standard library only.  Run it from inside the glm3 directory.
  The first test that needs the type-2 table pays about nine seconds for it;
  everything after that is a dictionary lookup.
================================================================================
"""

from __future__ import annotations

import random
import unittest
from fractions import Fraction as F

import glm3_common  # noqa: F401  (path shim)

import glm3_extraspecial as XS
import glm3_griess as GR
import glm3_leech2 as L2
import glm3_bench as BM
import glm3_metric as MET
import glm3_mog as MG
import glm3_odd as OD
import glm3_sign as SGN
from glm3_reasoner import REASONER, RELATION_BY_PRODUCT_TYPE, MonsterReasoner

import glm2_lattice as LAT
from glm2_codec import encode

RNG = random.Random(20260816)


def _random_class() -> int:
    return RNG.randrange(1, L2.N_CLASSES)


# ══════════════════════════════════════════════════════════════════════════════
#  LAMBDA / 2LAMBDA
# ══════════════════════════════════════════════════════════════════════════════

class TestLeech2(unittest.TestCase):

    def test_class_of_is_reduction_of_the_basis_coordinates(self):
        for _ in range(50):
            u = [RNG.randrange(-6, 7) for _ in range(24)]
            expect = 0
            for i, c in enumerate(u):
                if c % 2:
                    expect |= 1 << i
            self.assertEqual(L2.class_of(LAT.from_coords(u)), expect)

    def test_representative_inverts_class_of(self):
        for _ in range(50):
            c = _random_class()
            self.assertEqual(L2.class_of(L2.representative(c)), c)
            self.assertEqual(L2.class_vector(c),
                             [(c >> i) & 1 for i in range(24)])

    def test_class_of_refuses_a_point_outside_the_lattice(self):
        x = list(REASONER.carrier("energy"))
        x[0] += 1
        with self.assertRaises(ValueError):
            L2.class_of(x)

    def test_zero_class_is_type_zero(self):
        self.assertEqual(L2.q_form(0), 0)
        self.assertEqual(L2.class_type(0), 0)
        self.assertEqual(REASONER.class_type(0), 0)

    def test_q_is_quadratic_with_polar_b(self):
        for _ in range(200):
            u, v = _random_class(), _random_class()
            self.assertEqual(
                L2.q_form(u ^ v),
                (L2.q_form(u) + L2.q_form(v) + L2.b_form(u, v)) % 2)

    def test_b_is_symmetric_bilinear_and_alternating_on_q(self):
        for _ in range(200):
            u, v, w = _random_class(), _random_class(), _random_class()
            self.assertEqual(L2.b_form(u, v), L2.b_form(v, u))
            self.assertEqual(L2.b_form(u ^ v, w),
                             (L2.b_form(u, w) + L2.b_form(v, w)) % 2)
            self.assertEqual(L2.b_form(u, u), 0)

    def test_q_agrees_with_the_lattice_norm(self):
        for name in REASONER.list_concepts()[:20]:
            x = REASONER.carrier(name)
            self.assertEqual(L2.q_form(L2.class_of(x)),
                             (LAT.norm2(x) // 16) % 2)

    def test_witt_is_twelve_hyperbolic_planes(self):
        w = L2.witt_decomposition()
        self.assertEqual(w["planes"], 12)
        self.assertEqual(w["anisotropic_planes"], 0)
        self.assertTrue(w["plus_type"])

    def test_singular_count_is_the_plus_type_count(self):
        self.assertEqual(L2.singular_class_count(), (1 << 23) + (1 << 11))
        self.assertTrue(L2.form_is_plus_type())

    def test_class_census_closes(self):
        cen = L2.type_census()
        self.assertTrue(cen["closes"])
        self.assertEqual(cen["type2_classes"], 98280)
        self.assertEqual(cen["type3_classes"], (1 << 23) - (1 << 11))
        self.assertEqual(cen["total"], 1 << 24)

    def test_fast_type_matches_the_decoder(self):
        table = GR.type2_table()
        sample = [0] + list(table)[:5] + [_random_class() for _ in range(15)]
        sample += [L2.class_of(REASONER.carrier(n))
                   for n in REASONER.list_concepts()[:10]]
        for c in sample:
            self.assertEqual(REASONER.class_type(c), L2.class_type(c),
                             f"class {c:#08x}")

    def test_type_two_class_has_exactly_two_minimal_vectors(self):
        cls = next(iter(GR.type2_table()))
        vs = L2.minimal_vectors_of_class(cls)
        self.assertEqual(len(vs), 2)
        self.assertEqual(vs[0], tuple(-t for t in vs[1]))
        self.assertEqual(LAT.norm2(vs[0]), 32)

    def test_type_four_class_is_a_frame(self):
        cls = next(c for c in (L2.class_of(REASONER.carrier(n))
                               for n in REASONER.list_concepts()[:60])
                   if REASONER.class_type(c) == 4)
        fr = L2.frame_of_class(cls)
        self.assertEqual(len(fr), 48)
        for v in fr:
            self.assertEqual(LAT.norm2(v), 64)
            self.assertEqual(L2.class_of(v), cls)

    def test_pair_census_totals_the_kissing_number(self):
        cen = L2.pair_census()
        self.assertEqual(sum(cen.values()), 196560)
        self.assertEqual({k: v // 2 for k, v in cen.items()},
                         {0: 46575, 1: 47104, 2: 4600, 4: 1})


class TestStack(unittest.TestCase):
    """The 2-adic stack — the multi-MOG-cube in the Leech basis."""

    def test_stack_is_faithful_on_the_whole_register(self):
        for name in REASONER.list_concepts():
            x = REASONER.carrier(name)
            self.assertEqual(L2.class_stack_rebuild(L2.class_stack(x)), x,
                             name)

    def test_stack_handles_negative_coordinates(self):
        x = LAT.from_coords([-3, 5, -1] + [0] * 21)
        self.assertEqual(L2.class_stack_rebuild(L2.class_stack(x)), tuple(x))

    def test_stack_of_the_origin_is_the_offset(self):
        zero = tuple([0] * 24)
        planes = L2.class_stack(zero)
        self.assertEqual(len(planes), L2.STACK_DEPTH)
        self.assertEqual(L2.class_stack_rebuild(planes), zero)

    def test_stack_depth_and_offset_are_consistent(self):
        self.assertEqual(L2.STACK_OFFSET, 1 << (L2.STACK_DEPTH - 1))

    def test_every_plane_is_a_valid_class(self):
        for name in REASONER.list_concepts()[:40]:
            for p in REASONER.stack(name):
                self.assertTrue(0 <= p < L2.N_CLASSES)

    def test_stack_distinguishes_what_one_reduction_cannot(self):
        names = REASONER.list_concepts()
        raw = {L2.class_of(REASONER.carrier(n)) for n in names}
        stacks = {tuple(REASONER.stack(n)) for n in names}
        carriers = {tuple(REASONER.carrier(n)) for n in names}
        self.assertLess(len(raw), 20)          # the mod-2 ceiling
        self.assertEqual(len(stacks), len(carriers))

    def test_primitive_point_leaves_2_lambda(self):
        for name in ("energy", "force", "entropy", "mass"):
            x = REASONER.carrier(name)
            p = L2.primitive_point(x)
            u = LAT.to_coords(list(p))
            self.assertIsNotNone(u)
            self.assertFalse(all(int(v) % 2 == 0 for v in u), name)
            self.assertEqual(L2.class_of(p),
                             next(c for c in L2.class_stack(x) if c))


# ══════════════════════════════════════════════════════════════════════════════
#  THE EXTRASPECIAL GROUP
# ══════════════════════════════════════════════════════════════════════════════

class TestExtraspecial(unittest.TestCase):

    def test_symplectic_basis_pairs_correctly(self):
        alpha, beta = XS.symplectic_basis()
        self.assertEqual(len(alpha), XS.RANK)
        self.assertEqual(len(beta), XS.RANK)
        for i in range(XS.RANK):
            self.assertEqual(L2.q_form(alpha[i]), 0)
            self.assertEqual(L2.q_form(beta[i]), 0)
            for j in range(XS.RANK):
                self.assertEqual(L2.b_form(alpha[i], beta[j]),
                                 1 if i == j else 0)
                if i != j:
                    self.assertEqual(L2.b_form(alpha[i], alpha[j]), 0)
                    self.assertEqual(L2.b_form(beta[i], beta[j]), 0)

    def test_cocycle_has_the_defining_properties(self):
        for _ in range(200):
            u, v = _random_class(), _random_class()
            self.assertEqual(XS.cocycle(u, u), L2.q_form(u))
            self.assertEqual((XS.cocycle(u, v) + XS.cocycle(v, u)) % 2,
                             L2.b_form(u, v))

    def test_group_is_associative_with_identity_and_inverses(self):
        for _ in range(60):
            g = XS.x_of_class(_random_class())
            h = XS.x_of_class(_random_class())
            k = XS.x_of_class(_random_class())
            self.assertEqual((g * h) * k, g * (h * k))
            self.assertEqual(g * XS.identity(), g)
            self.assertEqual(g * XS.inverse(g), XS.identity())

    def test_square_is_z_to_the_q(self):
        z = XS.central()
        for _ in range(80):
            u = _random_class()
            g = XS.x_of_class(u)
            self.assertEqual(XS.square(g),
                             z if L2.q_form(u) else XS.identity())

    def test_commutator_is_z_to_the_b(self):
        z = XS.central()
        for _ in range(80):
            u, v = _random_class(), _random_class()
            self.assertEqual(XS.commutator(XS.x_of_class(u),
                                           XS.x_of_class(v)),
                             z if L2.b_form(u, v) else XS.identity())

    def test_centre_is_central(self):
        z = XS.central()
        for _ in range(40):
            g = XS.x_of_class(_random_class())
            self.assertEqual(z * g, g * z)
        self.assertEqual(z * z, XS.identity())

    def test_involution_count(self):
        rep = XS.involution_count()
        self.assertEqual(rep["elements_of_order_at_most_2"],
                         (1 << 24) + (1 << 12))

    def test_representation_is_a_faithful_homomorphism(self):
        z = XS.central()
        v = [0] * XS.REP_DIM
        v[3] = 1
        self.assertEqual(XS.rep_apply(z, v), [-t for t in v])
        for _ in range(20):
            g = XS.x_of_class(_random_class())
            h = XS.x_of_class(_random_class())
            self.assertTrue(XS.operators_equal(g * h, g * h))
            self.assertEqual(XS.rep_apply(g * h, v),
                             XS.rep_apply(g, XS.rep_apply(h, v)))

    def test_rep_dimension_is_the_ledger_odd_factor(self):
        self.assertEqual(XS.REP_DIM, 4096)
        self.assertEqual(24 * XS.REP_DIM, 98304)
        self.assertEqual(300 + 98280 + 24 * XS.REP_DIM, 196884)


# ══════════════════════════════════════════════════════════════════════════════
#  THE EVEN GRIESS ALGEBRA
# ══════════════════════════════════════════════════════════════════════════════

class TestGriess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.table = GR.type2_table()
        it = iter(cls.table)
        cls.c1 = next(it)
        cls.c2 = next(it)
        cls.c3 = next(it)

    def test_table_has_the_right_size(self):
        self.assertEqual(len(self.table), 98280)
        for cls_, rep in list(self.table.items())[:20]:
            self.assertEqual(L2.class_of(rep), cls_)
            self.assertEqual(LAT.norm2(rep), 32)

    def test_dimensions(self):
        self.assertEqual(GR.DIM_A, 300)
        self.assertEqual(GR.DIM_B, 98280)
        self.assertEqual(GR.DIM_EVEN, 98580)

    def test_product_is_commutative(self):
        xs = [GR.axis(self.c1), GR.b_vector(self.c2), GR.identity(),
              GR.a_matrix(GR.outer(GR.class_representative(self.c3)))]
        for x in xs:
            for y in xs:
                self.assertEqual(x.mul(y), y.mul(x))

    def test_product_is_not_associative(self):
        lam = GR.class_representative(self.c1)
        partner = next(c for c, v in self.table.items()
                       if c != self.c1 and abs(GR.std_inner(lam, v)) == 2)
        a, b = GR.axis(self.c1), GR.axis(partner)
        witness = a.mul(a.mul(b)) - a.mul(a).mul(b)
        self.assertFalse(witness.is_zero())
        self.assertGreater(witness.form(witness), 0)

    def test_identity_is_a_two_sided_identity(self):
        one = GR.identity()
        for x in (GR.axis(self.c1), GR.b_vector(self.c2),
                  GR.a_matrix(GR.outer(GR.class_representative(self.c3)))):
            self.assertEqual(one.mul(x), x)

    def test_form_is_symmetric_and_frobenius(self):
        xs = [GR.axis(self.c1), GR.b_vector(self.c2), GR.identity(),
              GR.a_matrix(GR.outer(GR.class_representative(self.c3)))]
        for x in xs:
            for y in xs:
                self.assertEqual(x.form(y), y.form(x))
                for z in xs:
                    self.assertEqual(x.mul(y).form(z), x.form(y.mul(z)))

    def test_axis_is_idempotent_of_norm_one_for_both_signs(self):
        for sign in (1, -1):
            a = GR.axis(self.c1, sign)
            self.assertEqual(a.mul(a), a)
            self.assertEqual(a.form(a), F(1))
        self.assertNotEqual(GR.axis(self.c1, 1), GR.axis(self.c1, -1))

    def test_axis_of_a_non_type_two_class_is_refused(self):
        bad = next(c for c in (_random_class() for _ in range(500))
                   if REASONER.class_type(c) != 2)
        with self.assertRaises(Exception):
            GR.axis(bad)

    def test_spectrum_dimensions_sum_to_the_dimension(self):
        d = GR.spectrum_dimensions()
        self.assertEqual(d["1"] + d["0"] + d["1/4"] + d["1/32"], GR.DIM_EVEN)
        self.assertEqual((d["1"], d["0"], d["1/4"], d["1/32"]),
                         (1, 49152, 2323, 47104))

    def test_spectrum_dimensions_match_the_pair_census(self):
        n = {k: v // 2 for k, v in L2.pair_census().items()}
        d = GR.spectrum_dimensions()
        self.assertEqual(d["1/32"], n[1])
        self.assertEqual(d["1/4"], n[2] // 2 + 23)
        self.assertEqual(d["0"], n[0] + n[2] // 2 + 277)

    def test_fusion_law_holds(self):
        rep = GR.fusion_report(self.c1, count=2)
        self.assertTrue(rep["idempotent"])
        self.assertTrue(rep["norm_one"])
        self.assertTrue(rep["all_rules_hold"], rep["rules"])

    def test_eigenvectors_really_are_eigenvectors(self):
        a = GR.axis(self.c1)
        samples = GR._eigen_samples(self.c1, count=2)
        for label, vectors in samples.items():
            lam = {"1": F(1), "0": F(0),
                   "1/4": F(1, 4), "1/32": F(1, 32)}[label]
            for v in vectors:
                self.assertEqual(a.mul(v), v.scale(lam), label)

    def test_miyamoto_is_the_extraspecial_sign(self):
        rep = GR.miyamoto_signs(self.c1)
        self.assertTrue(rep["miyamoto_is_extraspecial_sign"])

    def test_sign_automorphism_preserves_product_and_form(self):
        x, y = GR.axis(self.c2), GR.axis(self.c3)
        for mu in (self.c1, self.c2, _random_class()):
            gx = GR.apply_sign_automorphism(mu, x)
            gy = GR.apply_sign_automorphism(mu, y)
            self.assertEqual(GR.apply_sign_automorphism(mu, x.mul(y)),
                             gx.mul(gy))
            self.assertEqual(x.form(y), gx.form(gy))

    def test_sign_automorphism_is_an_involution(self):
        x = GR.axis(self.c2)
        for mu in (self.c1, _random_class()):
            self.assertEqual(
                GR.apply_sign_automorphism(mu,
                                           GR.apply_sign_automorphism(mu, x)),
                x)

    def test_norton_sakuma_types(self):
        rep = GR.norton_sakuma_report()
        self.assertTrue(rep["all_identified"])
        self.assertEqual(rep["types"], {0: "2B", 1: "4A", 2: "2A"})
        self.assertEqual(rep["orbits"][2]["dimension"], 3)
        self.assertTrue(rep["orbits"][2]["sakuma_2A_identity"])
        self.assertEqual(rep["orbits"][0]["dimension"], 2)
        self.assertEqual(rep["orbits"][1]["dimension"], 5)

    def test_orthogonal_axes_have_zero_product(self):
        lam = GR.class_representative(self.c1)
        other = next(c for c in self.table
                     if GR.std_inner(lam, GR.class_representative(c)) == 0)
        a, b = GR.axis(self.c1), GR.axis(other)
        self.assertEqual(a.form(b), F(0))
        self.assertEqual(len(GR.subalgebra_closure([a, b])), 2)

    def test_structure_constants_are_the_derived_ones(self):
        self.assertEqual((GR.ALPHA, GR.BETA, GR.GAMMA, GR.DELTA),
                         (F(1, 2), F(1, 4), F(1, 4), F(1, 4)))
        self.assertEqual((GR.FORM_A, GR.FORM_B), (F(2), F(2)))

    def test_arithmetic_is_exact(self):
        a = GR.axis(self.c1)
        s = a.scale(F(1, 3)).form(a.scale(F(1, 7)))
        self.assertIsInstance(s, F)
        self.assertEqual(s, F(1, 21))


# ══════════════════════════════════════════════════════════════════════════════
#  THE MULTI-MOG-CUBE
# ══════════════════════════════════════════════════════════════════════════════

class TestMog(unittest.TestCase):

    def test_cell_addressing_is_a_bijection(self):
        cells = {MG.cell_of(r, c) for r in range(4) for c in range(6)}
        self.assertEqual(cells, set(range(24)))
        coords = {MG.cube_coordinates(i) for i in range(24)}
        self.assertEqual(len(coords), 24)

    def test_bricks_are_a_trio_of_octads(self):
        rep = MG.trio_report()
        self.assertTrue(rep["is_a_trio"])
        self.assertEqual(rep["brick_weights"], [8, 8, 8])
        for b in MG.BRICKS:
            self.assertIn(b, MG.GOLAY_SET)
            self.assertEqual(bin(b).count("1"), 8)
        self.assertEqual(MG.BRICKS[0] | MG.BRICKS[1] | MG.BRICKS[2],
                         (1 << 24) - 1)

    def test_columns_are_a_sextet(self):
        rep = MG.sextet_report()
        self.assertTrue(rep["is_a_sextet"])
        self.assertEqual(rep["sextet_count"], 1771)
        for c in MG.COLUMNS:
            self.assertEqual(bin(c).count("1"), 4)

    def test_golay_trace_on_a_cube_is_the_even_weight_code(self):
        rep = MG.cube_code_report(0)
        self.assertEqual(rep["trace_size"], 128)
        self.assertTrue(rep["trace_is_even_weight_code"])
        self.assertNotEqual(rep["trace_size"], 16)      # RM(1,3) would be 16
        self.assertTrue(rep["rm13_claim_refuted"])

    def test_shortened_code_on_a_cube_is_trivial(self):
        rep = MG.cube_code_report(0)
        self.assertEqual(rep["shortened_size"], 2)
        self.assertTrue(rep["shortened_is_cube_and_zero"])

    def test_affine_geometry_on_the_complement_of_a_cube(self):
        for brick in range(3):
            rep = MG.affine_structure(brick)
            self.assertEqual(rep["disjoint_octads"], 30)
            self.assertEqual(rep["complementary_pairs"], 15)
            self.assertTrue(rep["closed_under_addition"])
            self.assertTrue(rep["labels_are_a_bijection"])
            self.assertEqual(rep["affine_group_order"], 322560)

    def test_affine_coordinates_label_sixteen_cells(self):
        coords = MG.affine_coordinates(0)
        self.assertEqual(len(coords), 16)
        self.assertEqual(sorted(coords.values()), list(range(16)))

    def test_octad_intersection_census(self):
        self.assertEqual(MG.octad_intersection_census(0),
                         {0: 30, 2: 448, 4: 280, 8: 1})

    def test_design_counts(self):
        self.assertEqual(MG.trio_census(),
                         {"trios": 3795, "octads": 759, "sextets": 1771})
        self.assertEqual(len(MG.OCTADS), 759)

    def test_sextet_and_trio_of_a_block(self):
        self.assertEqual(len(MG.sextet_of_tetrad(MG.COLUMNS[0])), 6)
        self.assertEqual(len(MG.trio_of_octad(MG.BRICKS[0])), 3)

    def test_hexacode_shadow_of_every_codeword(self):
        rep = MG.mog_audit(full=False)["alignment"]
        self.assertTrue(rep["aligned"])
        self.assertEqual(rep["failures"], 0)
        self.assertEqual(rep["codewords_tested"], 4096)

    def test_ambient_stack_of_a_leech_point(self):
        pts = [REASONER.carrier(n) for n in REASONER.list_concepts()[:24]]
        rep = MG.stack_report(pts)
        self.assertTrue(rep["plane0_constant"])
        self.assertTrue(rep["plane1_is_golay"])
        self.assertTrue(rep["plane1_casts_hexacode_shadow"])
        self.assertTrue(rep["mod8_sum_condition"])

    def test_golay_plane_is_always_a_codeword(self):
        for n in REASONER.list_concepts()[:40]:
            self.assertIn(MG.golay_plane(REASONER.carrier(n)), MG.GOLAY_SET)

    def test_frame_renders_a_mask_as_four_by_six(self):
        f = MG.frame(MG.BRICKS[0])
        self.assertEqual(len(f), 4)
        self.assertEqual([len(r) for r in f], [6] * 4)
        self.assertEqual(sum(sum(r) for r in f), 8)


# ══════════════════════════════════════════════════════════════════════════════
#  THE COMPANION REASONER
# ══════════════════════════════════════════════════════════════════════════════

class TestReasonerGlmLayer(unittest.TestCase):
    """The retained UBP/GLM layer must be untouched."""

    def test_register_size(self):
        self.assertGreaterEqual(len(REASONER.list_concepts()), 660)

    def test_audit_accepts_and_rejects(self):
        self.assertTrue(REASONER.audit("energy", "mass*speed^2").admissible)
        self.assertFalse(REASONER.audit("energy", "mass*speed^4").admissible)
        self.assertTrue(REASONER.audit("force", "mass*acceleration")
                        .admissible)

    def test_solve_finds_the_missing_formula(self):
        self.assertEqual(str(REASONER.solve("energy", ["mass", "speed"])),
                         "energy = mass * speed^2")

    def test_convert_uses_the_decimal_scale(self):
        self.assertIn("10^5", REASONER.convert("kilometre", "centimetre"))

    def test_identify_lists_synonyms(self):
        out = REASONER.identify("energy")
        self.assertIn("energy", out["is"])
        self.assertIn("work_function", out["is"])

    def test_repair_recovers_the_meaning(self):
        y = list(REASONER.carrier("energy"))
        y[2] += 1
        y[11] -= 1
        res = REASONER.repair(y)
        self.assertTrue(res.within_radius)
        self.assertEqual(res.meaning, REASONER.meaning("energy"))

    def test_carrier_is_derived_from_the_meaning(self):
        for n in REASONER.list_concepts()[:80]:
            self.assertEqual(tuple(REASONER.carrier(n)),
                             tuple(encode(REASONER.meaning(n))))

    def test_unknown_concept_raises(self):
        with self.assertRaises(Exception):
            REASONER.meaning("no_such_quantity_at_all")


class TestReasonerMonsterLayer(unittest.TestCase):

    def test_address_reports_a_faithful_stack(self):
        a = REASONER.address("energy")
        self.assertTrue(a["stack_rebuilds_carrier"])
        self.assertEqual(len(a["planes"]), L2.STACK_DEPTH)
        self.assertEqual(len(a["type_word"]), L2.STACK_DEPTH)
        self.assertTrue(set(a["type_word"]) <= set("0234"))

    def test_group_word_is_a_single_group_element(self):
        w = REASONER.group_word("energy")
        self.assertIsInstance(w.u, int)
        self.assertIn(w.eps, (0, 1))

    def test_composition_is_the_group_law(self):
        for a, b in (("mass", "speed"), ("force", "length"),
                     ("energy", "time")):
            r = REASONER.composition_is_group_law(a, b)
            self.assertTrue(r["classes_add"])
            self.assertTrue(r["group_matches"])
            self.assertTrue(r["phase_is_the_cocycle"])

    def test_griess_vector_is_exact_and_deterministic(self):
        g1 = REASONER.griess_vector("energy")
        g2 = REASONER.griess_vector("energy")
        self.assertEqual(g1, g2)
        self.assertIsInstance(g1.form(g2), F)

    def test_similarity_is_symmetric(self):
        for a, b in (("energy", "speed"), ("energy", "force"),
                     ("power", "entropy")):
            self.assertEqual(REASONER.similarity(a, b),
                             REASONER.similarity(b, a))

    def test_similarity_is_invariant_under_the_group(self):
        mu = REASONER.stack("energy")[2]
        ga = REASONER.griess_vector("energy")
        gb = REASONER.griess_vector("force")
        self.assertEqual(
            ga.form(gb),
            GR.apply_sign_automorphism(mu, ga)
              .form(GR.apply_sign_automorphism(mu, gb)))

    def test_relation_word_is_symmetric_and_well_formed(self):
        r1 = REASONER.relation("energy", "torque")
        r2 = REASONER.relation("torque", "energy")
        self.assertEqual(r1["relation_word"], r2["relation_word"])
        self.assertEqual(len(r1["relation_word"]), L2.STACK_DEPTH)
        self.assertTrue(set(r1["relation_word"]) <= {"1A", "2A", "4A", "2B"})
        self.assertTrue(r1["all_predictions_hold"])

    def test_relation_of_a_concept_with_itself_is_all_1A(self):
        r = REASONER.relation("energy", "energy")
        self.assertEqual(set(r["relation_word"]), {"1A"})

    def test_relation_table_is_the_documented_one(self):
        self.assertEqual({t: v[0] for t, v in RELATION_BY_PRODUCT_TYPE.items()},
                         {0: "1A", 2: "2A", 3: "4A", 4: "2B"})
        self.assertEqual(RELATION_BY_PRODUCT_TYPE[2][2], F(1, 8))
        self.assertEqual(RELATION_BY_PRODUCT_TYPE[3][2], F(1, 32))
        self.assertEqual(RELATION_BY_PRODUCT_TYPE[4][2], F(0))

    def test_triangle_realises_glm_composition(self):
        found = REASONER.find_triangle(limit=90)
        self.assertIsNotNone(found)
        tri = REASONER.triangle(*found)
        self.assertTrue(tri["applicable"])
        self.assertTrue(tri["third_class_is_the_product_concept"])
        self.assertTrue(tri["sakuma_identity"])
        self.assertEqual(tri["subalgebra_dimension"], 3)
        self.assertEqual(tri["inner_product"], "1/8")

    def test_fusion_report_for_a_concept(self):
        f = REASONER.fusion("energy")
        self.assertTrue(f["is_axis"])
        self.assertTrue(f["all_rules_hold"])

    def test_involution_two_colours_the_register(self):
        total = len(REASONER.list_concepts())
        o = REASONER.involution_orbit("energy", plane=2, limit=total)
        self.assertEqual(o["fixed_count"] + o["moved_count"], total)
        self.assertGreater(o["moved_count"], 0)
        self.assertGreater(o["fixed_count"], 0)

    def test_plane_zero_is_degenerate_over_the_register(self):
        total = len(REASONER.list_concepts())
        o = REASONER.involution_orbit("energy", plane=0, limit=total)
        self.assertEqual(o["moved_count"], 0)

    def test_frame_of_a_type_four_plane(self):
        f = next(REASONER.frame(n) for n in REASONER.list_concepts()[:60]
                 if REASONER.frame(n).get("has_frame"))
        self.assertEqual(f["vectors"], 48)
        self.assertEqual(f["orthogonal_pairs"], 24)

    def test_mog_view_of_a_concept(self):
        m = REASONER.mog("energy")
        self.assertTrue(m["golay_plane_is_a_codeword"])
        self.assertEqual(len(m["hexacode_shadow"]), 6)
        self.assertEqual(len(m["basis_planes"]), L2.STACK_DEPTH)
        self.assertEqual(len(m["golay_frame"]), 4)

    def test_census_covers_the_register(self):
        cen = REASONER.census()
        self.assertEqual(cen["unencodable"], 0)
        self.assertEqual(sum(cen["plane_types"].values()),
                         cen["concepts"] * cen["planes_per_concept"])
        self.assertGreater(cen["concepts_with_an_axis"], 500)

    def test_relation_census_counts_every_pair(self):
        cen = REASONER.relation_census(limit=30)
        self.assertEqual(sum(cen.values()), 30 * 29 // 2)
        self.assertTrue(set(cen) <= {"1A", "2A", "4A", "2B"})

    def test_neighbours_are_sorted_and_exclude_the_query(self):
        near = REASONER.neighbours("energy", count=5, limit=120)
        self.assertEqual(len(near), 5)
        self.assertNotIn("energy", [n for n, _ in near])
        values = [F(s) for _, s in near]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_summary_reports_the_built_structures(self):
        s = REASONER.summary()
        self.assertEqual(s["even_griess_dimension"], 98580)
        self.assertEqual(s["axes_available"], 98280)
        self.assertEqual(s["rep_dimension"], 4096)

    def test_a_fresh_reasoner_agrees_with_the_shared_one(self):
        fresh = MonsterReasoner()
        self.assertEqual(fresh.stack("energy"), REASONER.stack("energy"))
        self.assertEqual(fresh.similarity("energy", "force"),
                         REASONER.similarity("energy", "force"))

    def test_a_concept_without_an_axis_is_handled(self):
        names = REASONER.list_concepts()
        without = next((n for n in names
                        if all(REASONER.class_type(p) != 2
                               for p in REASONER.stack(n))), None)
        if without is None:
            self.skipTest("every concept in the register carries an axis")
        self.assertIsNone(REASONER.axis(without))
        self.assertEqual(REASONER.griess_vector(without), GR.zero())
        self.assertFalse(REASONER.fusion(without)["is_axis"])


# ══════════════════════════════════════════════════════════════════════════════
#  THE DERIVED STACK DEPTH
# ══════════════════════════════════════════════════════════════════════════════

class TestDepth(unittest.TestCase):
    """glm3_leech2: depth and offset are derived parameters, not constants."""

    def test_coordinate_range_of_the_register(self):
        points = [REASONER.carrier(n) for n in REASONER.list_concepts()]
        self.assertEqual(L2.coordinate_range(points), 180)

    def test_least_admissible_pair(self):
        self.assertEqual(L2.derive_stack_parameters(180), (256, 9))
        self.assertEqual(L2.derive_stack_parameters(180, 512), (512, 10))
        self.assertEqual(L2.derive_stack_parameters(0), (1, 1))

    def test_the_module_depth_is_the_derived_one(self):
        self.assertEqual(
            L2.derive_stack_parameters(180, L2.STACK_OFFSET)[1],
            L2.STACK_DEPTH)

    def test_an_offset_below_the_range_is_refused(self):
        with self.assertRaises(ValueError):
            L2.derive_stack_parameters(180, 64)

    def test_rebuild_at_several_admissible_pairs(self):
        x = REASONER.carrier("energy")
        for offset, depth in ((256, 9), (256, 12), (512, 10), (1024, 11)):
            self.assertTrue(L2.stack_is_faithful(x, depth, offset),
                            f"({offset}, {depth})")

    def test_a_depth_too_small_is_refused(self):
        x = REASONER.carrier("energy")
        with self.assertRaises(ValueError):
            L2.class_stack(x, depth=4, offset=512)

    def test_extra_planes_are_zero_and_lower_planes_do_not_move(self):
        x = REASONER.carrier("energy")
        base = L2.class_stack(x, 10, 512)
        deeper = L2.class_stack(x, 13, 512)
        self.assertEqual(deeper[:10], base)
        self.assertFalse(any(deeper[10:]))

    def test_a_reasoner_at_another_depth_agrees(self):
        deep = MonsterReasoner(depth=12, offset=512)
        shallow = MonsterReasoner(depth=9, offset=256)
        for lhs, rhs in (("energy", "mass*speed^2"),
                         ("energy", "mass*speed^4"),
                         ("force", "mass*acceleration")):
            a = REASONER.monster_check(lhs, rhs)["verdict"]
            self.assertEqual(a, deep.monster_check(lhs, rhs)["verdict"])
            self.assertEqual(a, shallow.monster_check(lhs, rhs)["verdict"])

    def test_the_zero_word_follows_the_parameters(self):
        deep = MonsterReasoner(depth=12, offset=512)
        self.assertEqual(len(deep.zero_word), 12)
        self.assertEqual(deep.zero_word[:10], REASONER.zero_word)


# ══════════════════════════════════════════════════════════════════════════════
#  THE CANONICAL SIGN
# ══════════════════════════════════════════════════════════════════════════════

class TestSign(unittest.TestCase):
    """glm3_sign: the Golay theta function and the coherent convention."""

    def test_theta_is_quadratic_and_not_linear(self):
        rep = SGN.theta_report(full=False, sample=64)
        self.assertTrue(rep["quadratic_identity"])
        self.assertFalse(rep["is_linear"])

    def test_theta_of_the_zero_word_and_of_an_octad(self):
        self.assertEqual(SGN.theta(0), 0)
        octad = next(c for c in MG.GOLAY_SET if bin(c).count("1") == 8)
        self.assertEqual(SGN.theta(octad), 0)      # 8/4 = 2 = 0 mod 2
        dodecad = next(c for c in MG.GOLAY_SET if bin(c).count("1") == 12)
        self.assertEqual(SGN.theta(dodecad), 1)    # 12/4 = 3 = 1 mod 2

    def test_theta_is_the_leech_form(self):
        self.assertTrue(SGN.theta_is_the_leech_form()["q_equals_theta"])

    def test_the_canonical_axis_is_the_minus_axis(self):
        cls = sorted(GR.type2_table())[0]
        self.assertEqual(SGN.CANONICAL_SIGN, -1)
        self.assertEqual(SGN.canonical_axis(cls), GR.axis(cls, -1))

    def test_the_all_plus_convention_is_incoherent(self):
        rep = SGN.coherence_report(count=3)
        self.assertTrue(rep["rule_holds_everywhere"])
        self.assertFalse(rep["all_plus_convention_is_coherent"])
        self.assertTrue(rep["canonical_convention_is_coherent"])

    def test_sakuma_holds_with_no_ad_hoc_sign(self):
        self.assertTrue(SGN.sakuma_report(count=2)["all_hold"])

    def test_the_cocycle_has_the_right_polarisation(self):
        rep = SGN.cocycle_report(trials=12)
        self.assertTrue(rep["bimultiplicative"])
        self.assertTrue(rep["eps(x,y) eps(y,x) = (-1)^(x.y)"])
        self.assertTrue(rep["eps(x,x) = (-1)^((x.x)/2)"])

    def test_the_coherent_conventions_number_two_to_the_24(self):
        rep = SGN.conventions_report(dimension=16)
        self.assertEqual(rep["nullity"], 24)
        self.assertTrue(rep["every_B_convention_solves_the_system"])


# ══════════════════════════════════════════════════════════════════════════════
#  THE ODD PART
# ══════════════════════════════════════════════════════════════════════════════

class TestOdd(unittest.TestCase):
    """glm3_odd: V- = 24 (x) 4096, both products, and the whole 196,884."""

    def test_the_dimensions_close(self):
        self.assertEqual(OD.DIM_ODD, 24 * 4096)
        self.assertEqual(OD.DIM_FULL, GR.DIM_EVEN + OD.DIM_ODD)
        self.assertEqual(OD.DIM_FULL, 196884)

    def test_the_constants_are_derived(self):
        c = OD.derive_constants()
        self.assertTrue(c["identity_condition"])
        self.assertTrue(c["over_determined_system_closes"])
        self.assertTrue(c["counting_puts_one_quarter_on_the_along_block"])
        self.assertEqual((c["c1"], c["c2"], c["c3"], c["c4"]),
                         (F(1, 4), F(1, 32), F(1, 16), F(-1, 32)))

    def test_the_identity_of_the_even_part_acts_as_the_identity(self):
        u = OD.basis(3, 17) + OD.basis(0, 4, -2)
        self.assertEqual(OD.act(GR.identity(), u), u)

    def test_the_form_is_positive_definite_on_the_odd_part(self):
        u = OD.basis(3, 17) + OD.basis(0, 4, -2)
        self.assertEqual(OD.form(u, u), 5)
        self.assertEqual(OD.form(OD.OddVector(), OD.OddVector()), 0)

    def test_the_ledger_is_the_classical_one(self):
        led = OD.ledger()
        self.assertTrue(led["agrees"])
        self.assertEqual(led["whole"], {"1": 1, "0": 96256, "1/4": 4371,
                                        "1/32": 96256, "total": 196884})

    def test_the_block_spectrum_is_the_monster_set(self):
        block = OD.spectrum_block()
        self.assertTrue(block["eigenvalues_are_the_monster_set"])
        self.assertEqual(block["total"], OD.DIM_ODD)

    def test_the_products_are_commutative_and_frobenius(self):
        self.assertTrue(OD.commutativity_report(trials=2)["commutative"])
        self.assertTrue(OD.frobenius_report(trials=2)["frobenius_holds"])

    def test_the_products_are_q_equivariant(self):
        self.assertTrue(OD.equivariance_report(trials=2)["equivariant"])

    def test_the_fusion_rules_hold(self):
        self.assertTrue(OD.fusion_report(count=1)["all_rules_hold"])

    def test_the_two_signs_have_different_miyamoto_involutions(self):
        rep = OD.miyamoto_report(count=1)
        self.assertTrue(rep["the_two_signs_have_different_miyamoto_involutions"])

    def test_the_odd_part_separates_the_signs_of_a_register_axis(self):
        view = REASONER.odd_view("energy")
        self.assertTrue(view["the_odd_part_separates_them"])
        self.assertNotEqual(view["eigenvalue_of_the_canonical_axis"],
                            view["eigenvalue_of_the_other_axis"])

    def test_a_concept_with_no_axis_on_a_plane_is_refused(self):
        planes = REASONER.stack("energy")
        bad = next(k for k, p in enumerate(planes)
                   if REASONER.class_type(p) != 2)
        with self.assertRaises(ValueError):
            REASONER.odd_view("energy", plane=bad)


# ══════════════════════════════════════════════════════════════════════════════
#  THE METRIC
# ══════════════════════════════════════════════════════════════════════════════

class TestMetric(unittest.TestCase):
    """glm3_metric: from an invariant form to an honest distance."""

    def test_the_form_is_a_positive_sum_of_squares(self):
        rep = MET.positive_definite_report()
        self.assertTrue(rep["all_ok"])
        self.assertTrue(rep["both_coefficients_positive"])

    def test_the_norm_vanishes_only_at_zero(self):
        cls = sorted(GR.type2_table())[0]
        self.assertEqual(MET.norm2_of(GR.zero()), 0)
        self.assertGreater(MET.norm2_of(GR.axis(cls)), 0)

    def test_distance_is_symmetric_and_zero_on_the_diagonal(self):
        self.assertEqual(REASONER.distance2("energy", "energy"), 0)
        self.assertEqual(REASONER.distance2("energy", "mass"),
                         REASONER.distance2("mass", "energy"))

    def test_concepts_with_the_same_carrier_are_at_distance_zero(self):
        self.assertEqual(tuple(REASONER.carrier("energy")),
                         tuple(REASONER.carrier("work")))
        self.assertEqual(REASONER.distance2("energy", "work"), 0)

    def test_concepts_with_different_carriers_are_at_positive_distance(self):
        for other in ("mass", "speed", "entropy", "pressure"):
            self.assertGreater(REASONER.distance2("energy", other), 0)

    def test_the_triangle_inequality_on_the_register(self):
        names = REASONER.list_concepts()[:30]
        rng = random.Random(7)
        for _ in range(60):
            a, b, c = (rng.choice(names), rng.choice(names),
                       rng.choice(names))
            self.assertTrue(MET.triangle_holds(
                REASONER.distance2(a, b), REASONER.distance2(b, c),
                REASONER.distance2(a, c)))

    def test_the_plane_vector_is_injective_and_zero_only_at_zero(self):
        tab = GR.type2_table()
        classes = sorted(tab)[:8] + [0] + [c for c in range(1, 500)
                                           if c not in tab][:8]
        keys = {}
        for c in classes:
            key = MET.griess_key(MET.plane_vector(c))
            self.assertNotIn(key, keys)
            keys[key] = c
            self.assertEqual(MET.plane_vector(c).is_zero(), c == 0)

    def test_the_fast_plane_distance_agrees_with_the_algebra(self):
        tab = GR.type2_table()
        classes = sorted(tab)[:4] + [0, 1, 5]
        for c1 in classes:
            for c2 in classes:
                self.assertEqual(
                    MET.plane_distance2(c1, c2),
                    MET.pseudo_distance2(MET.plane_vector(c1),
                                         MET.plane_vector(c2)))

    def test_nearest_neighbours_are_ordered_and_exclude_the_query(self):
        out = REASONER.nearest("energy", count=5, limit=120)
        self.assertEqual(len(out), 5)
        self.assertNotIn("energy", [n for n, _ in out])
        values = [float(d) for _, d in out]
        self.assertEqual(values, sorted(values))

    def test_clustering_is_a_partition(self):
        names = REASONER.list_concepts()[:80]
        groups = REASONER.cluster(F(1, 10), limit=80)
        flat = sorted(n for g in groups for n in g)
        self.assertEqual(flat, sorted(names))

    def test_a_bigger_threshold_gives_coarser_clusters(self):
        small = REASONER.cluster(F(1, 100), limit=60)
        big = REASONER.cluster(F(1, 2), limit=60)
        self.assertLessEqual(len(big), len(small))


# ══════════════════════════════════════════════════════════════════════════════
#  THE BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════

class TestBench(unittest.TestCase):
    """glm3_bench: the four benchmark sections, on reduced sizes."""

    def test_every_law_of_the_corpus_is_admissible(self):
        rep = BM.law_report(BM.LAWS[:16])
        self.assertEqual(rep["pass_rate"], 1, rep["failures"])
        self.assertEqual(rep["monster_agrees_with_glm"], rep["laws"])

    def test_the_corpus_is_wide(self):
        self.assertGreaterEqual(len(BM.LAWS), 60)
        self.assertGreaterEqual(len(BM.DIMENSIONLESS), 36)
        names = {n for n, _l, _r in BM.LAWS}
        for expected in ("newton_second", "coulomb", "ohm", "ideal_gas",
                         "stefan_boltzmann", "de_broglie", "bragg",
                         "arrhenius", "fourier_conduction"):
            self.assertIn(expected, names)

    def test_a_mutant_of_a_law_is_rejected(self):
        rep = BM.mutant_report(BM.LAWS[:8])
        self.assertEqual(rep["pass_rate"], 1, rep["false_negatives"])
        self.assertFalse(rep["false_negatives"])

    def test_the_facet_attribution_is_the_predicted_one(self):
        rep = BM.mutant_report(BM.LAWS[:12])
        att = rep["facet_attribution"]
        self.assertEqual(set(att["rank"]), {"tensor"})
        self.assertEqual(set(att["scale"]), {"scale"})
        for key in att["exponent"]:
            self.assertTrue(key.startswith("dimension"), key)

    def test_the_mutators_change_the_expression(self):
        text = "mass*speed^2"
        for name, fn in BM.MUTATORS.items():
            out = fn(text, 0)
            if out is not None:
                self.assertNotEqual(out, text, name)

    def test_the_dimensionless_groups_are_dimensionless(self):
        rep = BM.dimensionless_report()
        self.assertEqual(rep["pass_rate"], 1, rep["failures"])
        self.assertGreaterEqual(rep["dimensionless"], rep["groups"] - 2)

    def test_a_partial_sweep_agrees_everywhere(self):
        rep = BM.pairwise_sweep(limit=60, cross_check=50)
        self.assertEqual(rep["disagreements"], 0)
        self.assertTrue(rep["unrolled_form_agrees"])
        self.assertEqual(rep["pairs"], 60 * 59 // 2)


class TestIntegration(unittest.TestCase):
    """Cross-module consistency: the same number computed two ways."""

    def test_ledger_from_three_independent_modules(self):
        self.assertEqual(GR.DIM_A + GR.DIM_B + 24 * XS.REP_DIM, 196884)
        self.assertEqual(L2.type_census()["type2_classes"], GR.DIM_B)
        self.assertEqual(LAT.j_invariant_series(2)[2], 196884)

    def test_plus_type_from_witt_and_from_involutions(self):
        witt = L2.witt_decomposition()["singular_count"]
        inv = XS.involution_count()["singular_classes"]
        self.assertEqual(witt, inv)
        self.assertEqual(witt, (1 << 23) + (1 << 11))

    def test_octad_stabiliser_from_mog_and_from_m24(self):
        rep = MG.mog_audit(full=True)
        self.assertEqual(rep["affine"]["affine_group_order"],
                         rep["m24"]["octad_stabiliser_order"])
        self.assertTrue(rep["m24"]["octad_stabiliser_is_AGL_4_2"])

    def test_type_two_classes_from_theta_and_from_the_table(self):
        self.assertEqual(L2.type_census()["type2_vectors"] // 2,
                         len(GR.type2_table()))

    def test_every_module_self_audit_is_green(self):
        for rep in (L2.leech2_audit(full=False),
                    XS.extraspecial_audit(full=False),
                    GR.griess_audit(full=False),
                    MG.mog_audit(full=False)):
            for key, value in rep.items():
                if isinstance(value, bool):
                    self.assertTrue(value, key)
                elif isinstance(value, dict):
                    for k2, v2 in value.items():
                        if isinstance(v2, bool):
                            self.assertTrue(v2, f"{key}.{k2}")

    def test_the_new_modules_audit_green(self):
        # these two audits contain deliberate negatives (theta is NOT linear,
        # the all-plus sign convention is NOT coherent), so they are checked
        # by their own summary flag rather than by walking every boolean
        self.assertTrue(SGN.sign_audit(full=False)["all_ok"])
        self.assertTrue(OD.odd_audit(full=False)["all_ok"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
