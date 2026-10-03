"""The rate from the machine's own reads, pinned.

``glm_universal.reasoning.rate_posterior`` is the runtime half of
``studies/RATE_POSTERIOR_STUDY.md`` (Phase 82): an exact posterior over a
declared grid of rates, the soft reading's marginal confidence and the refusal
``RATE_GRID_EXCEEDED``; ``rate_posterior_marks`` is its measuring half, exact
over every count vector of coset weights.  The facts it rests on are theorems
of ``RequestProject/GLM/RatePosterior.lean`` (J9).  Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import rate_posterior as rp
from glm_universal.reasoning import rate_posterior_marks as rpm
from glm_universal.reasoning.decoder_confidence import ConfidenceRefusal
from glm_universal.substrate.mog import GOLAY_MASKS

P10 = Fraction(1, 10)
P20 = Fraction(1, 20)


def _w(i: int, e: int) -> int:
    return GOLAY_MASKS[i] ^ e


class TestTheLikelihood(unittest.TestCase):

    def test_grid_and_guard(self):
        self.assertEqual(rp.GRID[-1], rp.GUARD)
        self.assertEqual(rp.GUARD, Fraction(1, 5))
        self.assertEqual(len(rp.GRID), 6)

    def test_j1_classes_and_stride(self):
        j1 = rpm.j1_likelihood()
        self.assertTrue(j1["classes_sum_to_one"])
        self.assertEqual(j1["disagreements"], 0)

    def test_read_likelihood_is_the_coset_mass(self):
        y = _w(3, 0b101)
        for p in rp.GRID:
            self.assertEqual(rp.read_likelihood(y, p),
                             rp.coset_class_mass(2, p) / len(GOLAY_MASKS))

    def test_posterior_is_a_distribution(self):
        post = rp.rate_posterior([_w(1, 0), _w(2, 1)])
        self.assertEqual(sum(post), 1)
        self.assertTrue(all(x > 0 for x in post))


class TestTheRuntime(unittest.TestCase):

    def test_a_lone_weight_three_read_leans_above_the_grid(self):
        with self.assertRaises(ConfidenceRefusal) as cm:
            rp.decode_soft(_w(5, 0b111))
        self.assertEqual(cm.exception.name, "RATE_GRID_EXCEEDED")

    def test_clean_corpus_lets_it_answer(self):
        r = rp.decode_soft(_w(5, 0b111), [_w(6, 0), _w(7, 0), _w(8, 1)])
        self.assertEqual(r["value"], GOLAY_MASKS[5])
        self.assertEqual(r["confidence"], Fraction(r["confidence"]))
        self.assertTrue(0 < r["confidence"] < 1)

    def test_tie_is_refused_at_any_rate(self):
        with self.assertRaises(ConfidenceRefusal) as cm:
            rp.decode_soft(_w(5, 0b1111))
        self.assertEqual(cm.exception.name, "TIE")

    def test_floor(self):
        # Phase 82's marginal rule: below the floor
        with self.assertRaises(ConfidenceRefusal) as cm:
            rp.decode_soft_floor(Fraction(999, 1000), _w(5, 0b111),
                                 [_w(6, 0b1), _w(7, 0b11)], rule="marginal")
        self.assertEqual(cm.exception.name, "BELOW_FLOOR")
        # the production rule (Phase 89): the credible set reaches the guard
        with self.assertRaises(ConfidenceRefusal) as cm:
            rp.decode_soft_floor(Fraction(999, 1000), _w(5, 0b111),
                                 [_w(6, 0b1), _w(7, 0b11)])
        self.assertEqual(cm.exception.name, "RATE_GRID_EXCEEDED")

    def test_agree_soft_answers_the_carrier(self):
        # Phase 82's contract (the marginal rule, now set aside, still callable)
        r = rp.agree_soft(_w(12, 0b111), _w(12, 0b111000), rule="marginal")
        self.assertEqual(r["value"], GOLAY_MASKS[12])
        self.assertGreater(r["confidence"], Fraction(999, 1000))

    def test_agree_soft_production_rule_needs_evidence(self):
        # Phase 89's production rule (upper credible): one lone pair leaves
        # the guard rate inside the credible set, so it refuses at the edge;
        # a clean session history lets it answer
        with self.assertRaises(ConfidenceRefusal) as cm:
            rp.agree_soft(_w(12, 0b111), _w(12, 0b111000))
        self.assertEqual(cm.exception.name, "RATE_GRID_EXCEEDED")
        r = rp.agree_soft(_w(12, 0b111), _w(12, 0b111000),
                          history=[_w(i, 0) for i in range(1, 9)])
        self.assertEqual(r["value"], GOLAY_MASKS[12])
        self.assertEqual(r["rule"], "upper")
        self.assertEqual(r["session_reads"], 8)

    def test_session_history_is_evidence(self):
        # the same subject, with and without a clean session behind it
        alone = rp.decode_soft(_w(5, 0b111), [_w(6, 0), _w(7, 0), _w(8, 1)])
        backed = rp.decode_soft(_w(5, 0b111), [_w(6, 0), _w(7, 0), _w(8, 1)],
                                history=[_w(i, 0) for i in range(9, 20)])
        self.assertGreaterEqual(backed["confidence"], alone["confidence"])
        self.assertLessEqual(backed["rate"], alone["rate"])

    def test_marginal_rule_still_callable(self):
        r = rp.decode_soft(_w(5, 0b111), [_w(6, 0), _w(7, 0), _w(8, 1)],
                           rule="marginal")
        self.assertIsNone(r["rate"])
        self.assertEqual(r["rule"], "marginal")


class TestTheOperatingCharacteristics(unittest.TestCase):

    def test_j2_promise_under_the_prior_small_n(self):
        for n in (1, 2):
            for t in (Fraction(9, 10), Fraction(999, 1000)):
                c = rpm._prior_cell(n, t)
                self.assertLessEqual(c["residual"], 1 - t)

    def test_j3_the_on_grid_break_at_one_tenth(self):
        t = Fraction(9999, 10000)
        c = rpm.soft_cell(2, P10, t)
        self.assertGreater(c["residual"], 1 - t)
        self.assertLess(c["residual"], Fraction(15, 100000))

    def test_soft_is_more_conservative_than_the_oracle_at_n_one(self):
        t = Fraction(999, 1000)
        soft, oracle = rpm.soft_cell(1, P20, t), rpm.oracle_cell(P20, t)
        self.assertLess(soft["retention"], oracle["retention"])
        self.assertLess(soft["residual"], oracle["residual"])

    def test_j6_naive_underestimates(self):
        self.assertTrue(rpm.j6_naive()["passed"])

    def test_j7_refusals_are_evidence(self):
        j7 = rpm.j7_refusals_are_evidence()
        self.assertTrue(j7["passed"])
        self.assertGreater(j7["after_tie"], j7["prior_mean"])
        self.assertLess(j7["after_clean_pair"], j7["prior_mean"])

    def test_j9_lean_file_names_its_theorems(self):
        self.assertTrue(rpm._lean_has(["soft_floor_error_le",
                                       "rate_posterior_prod",
                                       "naive_rate_underestimates",
                                       "read_marginal_eq_coset_mass"]))


class TestTheRepairs(unittest.TestCase):
    """Phase 86: the repairs Phase 82 named, over the same engine."""

    T = Fraction(9999, 10000)

    def test_a_finer_grid_does_not_repair_the_on_grid_break(self):
        for n in (2, 5):
            c = rpm.repair_cell("R1 finer grid", n, P10, self.T)
            self.assertGreater(c["residual"], 1 - self.T)

    def test_the_upper_credible_rule_repairs_it(self):
        for n in (2, 5):
            c = rpm.repair_cell("R4 upper credible", n, P10, self.T)
            self.assertLessEqual(c["residual"], 1 - self.T)
            self.assertGreater(c["retention"], Fraction(5, 100))

    def test_shipped_rule_reproduces_j3(self):
        a = rpm.repair_cell("R0 as shipped", 2, P10, self.T)
        b = rpm.soft_cell(2, P10, self.T)
        self.assertEqual(a["residual"], b["residual"])
        self.assertEqual(a["retention"], b["retention"])

    def test_fixed_rate_identity(self):
        for name in ("R0 as shipped", "R4 upper credible"):
            self.assertTrue(rpm.fixed_rate_identity(
                rpm.repair_cell(name, 5, P10, self.T)))

    def test_one_fifth_breaks_because_every_answered_class_falls_short(self):
        r = Fraction(1, 5)
        c = rpm.repair_cell("R5 upper and raised", 5, r, self.T)
        answered = [d for d, w in enumerate(c["by_class"]) if w]
        self.assertTrue(answered)
        for d in answered:
            self.assertLess(rpm._confidence(d, r), self.T)
        self.assertGreater(c["residual"], 1 - self.T)

    def test_lean_file_names_the_repair_theorems(self):
        from pathlib import Path
        path = (Path(rpm.__file__).resolve().parents[2] / "glm_lean"
                / "RequestProject/GLM/RateRepair.lean")
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("fixed_rate_keep", "fixed_rate_break"):
            self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":
    unittest.main()
