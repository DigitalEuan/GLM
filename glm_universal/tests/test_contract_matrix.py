"""Candidate P's two contract changes, tested four ways, pinned.

``glm_universal.reasoning.contract_matrix`` (Phase 89,
``studies/CONTRACT_MATRIX_STUDY.md``) measures the control (A), the
upper-credible rate rule alone (B), the session-marginal confidence alone (C)
and both (D) over the fixed-rate cells of the rate-posterior study, in two
frames: a call passing its own corpus (frame I) and a session of plain calls
(frame II).  The fast cases check the engine's identities on short sessions;
the whole matrix, which decides the production baseline, is an exhaustive
case.  Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

import pytest

from glm_universal.reasoning import contract_matrix as cm
from glm_universal.reasoning import rate_posterior_marks as rpm

P20 = Fraction(1, 20)
P10 = Fraction(1, 10)
T3 = Fraction(999, 1000)


class TestTheEngine(unittest.TestCase):

    def test_four_variants_declared(self):
        self.assertEqual(sorted(cm.VARIANTS), ["A", "B", "C", "D"])
        self.assertEqual(cm.VARIANTS["A"][1:], ("call", "marginal"))
        self.assertEqual(cm.VARIANTS["D"][1:], ("session", "upper"))

    def test_one_call_session_is_the_call(self):
        # a session of one call has no history: C reads as A, D as B
        for r in (P20, P10, Fraction(1, 5)):
            a = cm.session_cell("A", 1, r, T3)
            c = cm.session_cell("C", 1, r, T3)
            self.assertEqual(a["residual"], c["residual"])
            self.assertEqual(a["retention"], c["retention"])
            b = cm.session_cell("B", 1, r, T3)
            d = cm.session_cell("D", 1, r, T3)
            self.assertEqual(b["retention"], d["retention"])

    def test_marginal_call_is_the_soft_cell(self):
        # call k of a session variant is the count-vector engine's k-read cell
        for n in (1, 2, 5):
            right, wrong, _edge = cm._call("marginal", n, P20, T3)
            cell = rpm.soft_cell(n, P20, T3)
            self.assertEqual(right, cell["p_right"])
            self.assertEqual(wrong, cell["p_wrong"])

    def test_upper_call_is_the_repair_cell(self):
        for n in (1, 2, 5):
            right, wrong, _edge = cm._call("upper", n, P10, T3)
            rep = rpm.repair_cell("R4 upper credible", n, P10, T3)
            res = wrong / (right + wrong)
            self.assertEqual(res, rep["residual"])

    def test_session_improves_retention(self):
        # the session's reads sharpen the posterior: more right answers kept
        a = cm.session_cell("A", 5, P20, T3)
        c = cm.session_cell("C", 5, P20, T3)
        self.assertGreater(c["retention"], a["retention"])
        b = cm.session_cell("B", 5, P20, T3)
        d = cm.session_cell("D", 5, P20, T3)
        self.assertGreater(d["retention"], b["retention"])

    def test_prior_promise_kept_short_sessions(self):
        for v in cm.VARIANTS:
            for s in (1, 2):
                for t in (Fraction(9, 10), T3):
                    self.assertTrue(cm.prior_cell(v, s, t)["promise"])

    def test_calibration_is_an_interval(self):
        c = cm.calibration_cell("D", 2, P10)
        self.assertLessEqual(c["excess_lo"], c["excess_hi"])
        self.assertLess(c["excess_hi"] - c["excess_lo"],
                        Fraction(1, 10 ** 10))


@pytest.mark.exhaustive
class TestTheMatrix(unittest.TestCase):
    """The whole matrix (about two minutes): the figures the study quotes."""

    @classmethod
    def setUpClass(cls):
        cls.m = cm.matrix()
        cls.rows = {r["variant"]: r for r in cls.m["rows"]}

    def test_cells(self):
        self.assertEqual(self.m["cells_each"], 525)

    def test_frame_one_is_phase_86(self):
        # frame I reproduces the repairs table: R0 37 (2 on grid), R4 32 (0)
        self.assertEqual(self.rows["A"]["frame_one"]["broken"], 37)
        self.assertEqual(self.rows["A"]["frame_one"]["on_grid"], 2)
        self.assertEqual(self.rows["B"]["frame_one"]["broken"], 32)
        self.assertEqual(self.rows["B"]["frame_one"]["on_grid"], 0)
        self.assertEqual(self.rows["C"]["frame_one"]["broken"], 37)
        self.assertEqual(self.rows["D"]["frame_one"]["broken"], 32)

    def test_frame_two_breaks(self):
        got = {v: (r["broken"], r["on_grid"], r["at_one_fifth"])
               for v, r in self.rows.items()}
        self.assertEqual(got, {"A": (35, 0, 35), "B": (20, 0, 20),
                               "C": (37, 2, 35), "D": (28, 0, 28)})

    def test_prior_promise_everywhere(self):
        for r in self.rows.values():
            self.assertEqual(r["prior_broken"], 0)

    def test_reference_retention(self):
        key = f"{P20}@{T3}"
        self.assertEqual(round(float(self.rows["A"]["retention"][key]), 4),
                         0.3010)
        self.assertEqual(round(float(self.rows["D"]["retention"][key]), 4),
                         0.7265)
        self.assertEqual(round(float(self.rows["C"]["retention"][key]), 4),
                         0.7624)

    def test_decision(self):
        self.assertEqual(self.m["qualified"], ["B", "D"])
        self.assertEqual(self.m["production"], cm.PRODUCTION)
        self.assertEqual(cm.PRODUCTION, "D")


if __name__ == "__main__":
    unittest.main()
