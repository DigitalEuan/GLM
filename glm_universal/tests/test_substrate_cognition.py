"""Tests for the substrate-native cognition round: the certificate-carrying
derivations of :mod:`glm_universal.reasoning.certificates`, the planner frame
that reaches them, and the experiments of
:mod:`glm_universal.reasoning.substrate_cognition`, each held to the pass mark
``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`` declared before it ran."""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.evaluation.certificates_heldout import CERTIFICATES
from glm_universal.reasoning import certificates as cert
from glm_universal.reasoning import substrate_cognition as sc


class TestCertificates(unittest.TestCase):

    def test_bezout_checks_on_a_grid(self):
        for a in range(-12, 13):
            for b in range(-12, 13):
                got = cert.bezout(a, b)
                self.assertTrue(cert.check_bezout(got))
                self.assertEqual(a * got.x + b * got.y, got.g)

    def test_linear_family_is_every_solution_in_a_box(self):
        for a, b, c in ((12, 18, 30), (7, 5, 1), (3, -9, 6), (0, 5, 10),
                        (17, 0, 34)):
            sol = cert.solve_linear(a, b, c)
            self.assertEqual(sol.kind, "family")
            family = {(sol.x0 + sol.sx * k, sol.y0 + sol.sy * k)
                      for k in range(-60, 61)}
            for x in range(-15, 16):
                for y in range(-15, 16):
                    if a * x + b * y == c:
                        self.assertIn((x, y), family)

    def test_impossibility_certificate(self):
        for a, b, c in ((6, 9, 5), (4, 6, 7), (0, 0, 5)):
            sol = cert.solve_linear(a, b, c)
            self.assertEqual(sol.kind, "none")
            self.assertTrue(cert.check_linear(sol))
            self.assertFalse(any(a * x + b * y == c for x in range(-20, 21)
                                 for y in range(-20, 21)))

    def test_factorisation_and_refusal_past_bound(self):
        f = cert.factorise(600851475143)
        self.assertEqual(f.factors, ((71, 1), (839, 1), (1471, 1), (6857, 1)))
        with self.assertRaises(cert.CertificateRefusal):
            cert.factorise(998244359987710471)

    def test_rendering_matches_the_declared_form(self):
        self.assertIn("x = 1 + 3k",
                      cert.render_linear(cert.solve_linear(12, 18, 30)))
        self.assertIn("2^3 * 3^2 * 5",
                      cert.render_factorisation(cert.factorise(360)))


class TestCertificateFrame(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.x7 = sc.certificate_experiment()

    def test_declared_set_scores(self):
        self.assertEqual(self.x7["questions"], len(CERTIFICATES))
        self.assertEqual(self.x7["planner"], {"correct": 13,
                                              "correct-refusal": 3})
        self.assertEqual(self.x7["grammar"], {"correct-refusal": 3,
                                              "refused": 13})
        self.assertTrue(self.x7["passed"])


class TestExperiments(unittest.TestCase):

    def test_x1_fork(self):
        r = sc.fork_experiment()
        self.assertTrue(r["sextet_all_sextets"])
        self.assertEqual(r["single_read_refused"], r["reads"])
        self.assertEqual(r["truth_in_fork"], r["reads"])
        self.assertEqual(r["fork_wrong"], 0)
        self.assertEqual(r["fork_answered"], 4224)
        self.assertEqual(r["refusal_witness_shared"], 2)
        self.assertTrue(r["refusal_witness_is_truth_and_octad"])

    def test_x2_one_tower_misses_two_towers_do_not(self):
        r = sc.dyadic_experiment()
        self.assertGreater(r["one_tower_misses"], 0)
        self.assertEqual(r["two_tower_misses"], 0)
        self.assertFalse(r["passed"])
        self.assertEqual(sc.conflation_level(Fraction(-1, 8), Fraction(0)), -1)

    def test_x3_tax_is_not_generative(self):
        r = sc.tax_experiment()
        self.assertEqual(r["engine_tax_invariant"],
                         r["engine_tax_translates_checked"])
        self.assertEqual(r["coherence_descents_to_zero"], r["coherence_starts"])
        self.assertFalse(r["passed"])

    def test_x4_certificate_agrees_with_search(self):
        r = sc.reversible_experiment()
        self.assertEqual(r["certificate_disagrees"], 0)
        self.assertEqual(r["undo_not_exact"], 0)
        self.assertEqual(r["certified_impossible"], 16)

    def test_x4_orbit_is_the_three_cycle(self):
        dist = sc.gate_orbit_distances()
        orbit = {t for (s, t) in dist if s == 0b011}
        # bits in coordinate order: 0b011 is (a, b, c) = (1, 1, 0)
        self.assertEqual(orbit, {0b011, 0b111, 0b101})
        self.assertEqual({t for (s, t) in dist if s == 0b010}, {0b010})

    def test_x5_decoys(self):
        r = sc.wobble_experiment()
        self.assertEqual(r["decoys_matching"], 8)
        separated = [row["name"] for row in r["rows"]
                     if not row["decoy_matches"]]
        self.assertEqual(separated, ["1/3"])

    def test_x6_intervals(self):
        r = sc.interval_experiment()
        self.assertEqual(r["inconsistent"], 0)
        self.assertEqual(r["consistent_at_stated_precision"], 7)
        self.assertEqual(r["ordering_disagreements"], 0)
        iron = [row for row in r["rows"] if row["symbol"] == "Fe"][0]
        self.assertEqual(iron["verdict"],
                         "consistent at the register's stated precision")

    def test_x6_interval_contract(self):
        a = sc.Interval(Fraction(1), Fraction(2))
        b = sc.Interval(Fraction(3), Fraction(4))
        c = sc.Interval(Fraction(3, 2), Fraction(5, 2))
        self.assertEqual(sc.compare_intervals(a, b), "lt")
        self.assertEqual(sc.compare_intervals(b, a), "gt")
        self.assertEqual(sc.compare_intervals(a, c), "overlap")
        held = sc.Interval.as_held(Fraction(1396, 25))
        self.assertEqual((held.lo, held.hi),
                         (Fraction(55835, 1000), Fraction(55845, 1000)))
        with self.assertRaises(TypeError):
            sc.Interval(0.5, Fraction(1))            # the float is the probe

    def test_x8_mobius(self):
        r = sc.mobius_experiment()
        self.assertTrue(r["passed"])
        for row in r["rows"]:
            self.assertGreater(row["cf_bits_after_steps"],
                               row["delta_sigma_bits_after_steps"])

    def test_x8_known_transform(self):
        # 1/x at x = [2; 3, 4]: the last term waits for a tail that never comes.
        out = list(sc.mobius_stream(0, 1, 1, 0, [2, 3, 4]))
        self.assertEqual(out, [0, 2, 3])    # 1/x of [2; 3, 4], as far as certain

    def test_x9_weyl_vector(self):
        self.assertTrue(sc.lorentzian_experiment()["null"])

    def test_the_wired_experiments(self):
        self.assertEqual(sc.WIRED, ("X6", "X7", "Y1", "Y2", "Y3"))


class TestRoundTwoCertificates(unittest.TestCase):
    """The round-two derivations (Phase 63), each with its certificate."""

    def test_simplest_in_against_a_brute_scan(self):
        def brute(lo, hi):
            q = 1
            while True:
                p = -((-lo.numerator * q) // lo.denominator)
                if Fraction(p, q) <= hi:
                    return min((Fraction(k, q) for k in range(
                        p, (hi.numerator * q) // hi.denominator + 1)),
                        key=abs)
                q += 1
        for a in range(-30, 30):
            for w in (1, 4, 11):
                lo = Fraction(a, 29)
                hi = lo + Fraction(w, 311)
                self.assertEqual(cert.simplest_in(lo, hi), brute(lo, hi))

    def test_recognition_and_its_rule(self):
        got = cert.recognise_decimal("0.142857")
        self.assertEqual(got.fraction, Fraction(1, 7))
        self.assertTrue(got.significant)
        self.assertTrue(cert.check_recognition(got))
        coarse = cert.recognise_decimal("0.1")
        self.assertEqual(coarse.fraction, Fraction(1, 7))
        self.assertFalse(coarse.significant)
        self.assertIn("below 8", cert.refusal_recognition(coarse))
        with self.assertRaises(cert.CertificateRefusal):
            cert.recognise_decimal("pi")

    def test_stream_recognition(self):
        from glm_universal.reasoning import exact_real as xr
        for x in (Fraction(3, 7), Fraction(5, 16), Fraction(1, 2)):
            kind, got = cert.recognise_stream(xr.delta_sigma_bits(x, 512), 16)
            self.assertEqual((kind, got), ("rational", x))
        kind, _got = cert.recognise_stream(
            xr.delta_sigma_bits(Fraction(141421356, 10 ** 9), 512), 16)
        self.assertEqual(kind, "excluded")

    def test_monomial_three_outcomes(self):
        axes = ("L", "M", "T")
        length, accel = (1, 0, 0), (1, 0, -2)
        period, mass = (0, 0, 1), (0, 1, 0)
        got = cert.derive_monomial("period", period,
                                   [("length", length), ("acceleration", accel)],
                                   axes)
        self.assertEqual(got.kind, "unique")
        self.assertEqual(got.exponents, (Fraction(1, 2), Fraction(-1, 2)))
        self.assertTrue(cert.check_monomial(got))
        no = cert.derive_monomial("mass", mass, [("length", length),
                                                 ("period", period)], axes)
        self.assertEqual(no.kind, "impossible")
        self.assertTrue(cert.check_monomial(no))
        self.assertIn("no product of powers", cert.render_monomial(no))
        free = cert.derive_monomial("period", period,
                                    [("length", length), ("acceleration", accel),
                                     ("wavelength", length)], axes)
        self.assertEqual(free.kind, "undetermined")
        self.assertTrue(cert.check_monomial(free))


class TestRoundTwoExperiments(unittest.TestCase):
    """Each round-two experiment against the mark section 6 declared."""

    @classmethod
    def setUpClass(cls):
        from glm_universal.runtime.session import GeometricSession
        cls.session = GeometricSession()

    def test_y1_interval_questions(self):
        r = sc.interval_wired_experiment(self.session)
        self.assertEqual(r["planner"], {"correct": 7, "correct-refusal": 1})
        self.assertEqual(r["grammar"], {"correct-refusal": 1, "refused": 7})
        self.assertEqual(r["guard_element_overlaps"], 0)
        self.assertEqual(r["guard_molecule_overlaps"], 0)
        self.assertTrue(r["passed"])

    def test_y2_recognition(self):
        r = sc.recognition_experiment(self.session)
        self.assertEqual(r["recognised_exactly"], r["farey_targets"])
        self.assertEqual(r["farey_targets"], 79)
        self.assertEqual(r["recognised_wrongly"], 0)
        self.assertEqual(r["certified_excluded"], r["irrational_targets"])
        self.assertEqual(r["decimal"]["planner"],
                         {"correct": 7, "correct-refusal": 3})
        self.assertTrue(r["passed"])

    def test_y3_dimensional(self):
        r = sc.dimensional_experiment(self.session)
        self.assertEqual(r["planner"], {"correct": 12, "correct-refusal": 3})
        self.assertEqual(r["grammar"], {"correct-refusal": 3, "refused": 12})
        self.assertTrue(r["passed"])

    def test_y4_coset_descent_is_the_decoder(self):
        r = sc.coset_descent_experiment()
        self.assertTrue(r["tax_monotone_in_weight"])
        self.assertEqual(r["agree_with_decoder"], r["reads"])
        self.assertEqual(r["reads"], 3136)
        self.assertEqual(r["ties"], 768)
        self.assertLess(r["greedy_reached_minimum"], r["reads"])

    def test_y5_nested_holdouts(self):
        r = sc.nested_holdout_experiment()
        self.assertEqual(r["fields"], 9)
        failing = sorted(row["field"] for row in r["rows"]
                         if not row["survives"])
        self.assertEqual(failing, ["covalent_radius_pm", "electron_affinity_eV"])

    def test_ordering_guard_refuses_overlap(self):
        from glm_universal.runtime import semantic_plan as sp

        class _Value:
            def __init__(self, row, value):
                self.row, self.value, self.rendered = row, value, str(value)

        class _Surface:
            def field(self, name, row):
                return {"a": _Value("A", Fraction(1234, 100)),
                        "b": _Value("B", Fraction(12345, 1000)),
                        "c": _Value("C", Fraction(13))}[row]

        class _Session:
            field_surface = _Surface()

        why = sp._held_overlap(_Session(), "a", "w", "b", "w")
        self.assertIn("overlap at their stated precision", why)
        self.assertEqual(sp._held_overlap(_Session(), "a", "w", "c", "w"), "")


if __name__ == "__main__":
    unittest.main()
