"""Phase 89: the declared question frames, their column-3 gate, the router's
``frames`` surface, the question-set scorer, and K1 (``-q`` through the
router).  ``studies/QUESTION_SET_B_STUDY.md``."""

from __future__ import annotations

import ast
import glob
import io
import os
import sys
import unittest
from fractions import Fraction

from glm_universal.evaluation import question_set_b_cases as qc
from glm_universal.reasoning import exact_forms as ef
from glm_universal.runtime import question_frames as qf
from glm_universal.runtime import router

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.normpath(os.path.join(HERE, "..", ".."))


class TestExactForms(unittest.TestCase):

    def test_surds(self):
        self.assertEqual(ef.sqrt_of(Fraction(8)).text(), "2*sqrt(2)")
        self.assertEqual(ef.sqrt_of(Fraction(1, 5)).text(), "1/5*sqrt(5)")
        self.assertEqual(ef.sqrt_of(Fraction(9, 4)).text(), "3/2")

    def test_entropy_is_exact(self):
        h = ef.entropy([Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)])
        self.assertTrue(h.is_rational())
        self.assertEqual(h.rational, Fraction(3, 2))
        hx = ef.entropy([Fraction(3, 4), Fraction(1, 4)])
        self.assertEqual(hx.text(), "2 - 3/4*log2(3)")
        terms = [(-Fraction(3, 4), Fraction(3, 4)),
                 (-Fraction(1, 4), Fraction(1, 4))]
        self.assertTrue(ef.log_identity_holds(terms, hx))
        self.assertFalse(ef.log_identity_holds(terms, h))

    def test_sturm_isolates_the_one_root(self):
        roots = ef.sturm_roots((Fraction(-2), Fraction(0), Fraction(1)),
                               Fraction(0), Fraction(2), Fraction(1, 10**9))
        self.assertEqual(len(roots), 1)
        lo, hi = roots[0]
        self.assertTrue(lo * lo <= 2 <= hi * hi)


def _read(text):
    rd = qf.read(text)
    assert rd is not None, text
    return rd


class TestSetB(unittest.TestCase):
    """Every Set B item is read by a frame and gets the audited verdict."""

    EXPECTED = {
        "O1-001": ("agree_operating", "ANSWER", None),
        "O1-002": ("octad_pair", "REFUSED", "AMBIGUOUS"),
        "O1-003": ("error_weight", "REFUSED", "UNCORRECTABLE"),
        "O1-004": ("declared_rate_floor", "REFUSED", "BELOW_FLOOR"),
        "O1-005": ("floor_range", "REFUSED", "FLOOR_OUT_OF_RANGE"),
        "O1-006": ("rate_grid", "REFUSED", "RATE_GRID_EXCEEDED"),
        "O1-007": ("across_wheels_values", "ANSWER", None),
        "O1-008": ("energy_light", "REFUSED", "NO_LICENSED_JUNCTION"),
        "O1-009": ("heat_level", "REFUSED", "LEVEL_AS_DIFFERENCE"),
        "O1-010": ("stepwise_givens", "REFUSED", "INCONSISTENT_GIVENS"),
        "O1-011": ("integer_entails", "ANSWER", None),
        "O1-012": ("loop_least", "ANSWER", None),
        "O1-013": ("integer_system", "ANSWER", None),
        "O1-014": ("rate_grid", "REFUSED", "RATE_GRID_EXCEEDED"),
    }

    def test_every_item(self):
        for it in qc.set_b():
            with self.subTest(item=it.id):
                rd = _read(it.query)
                frame, verdict, code = self.EXPECTED[it.id]
                self.assertEqual((rd.frame, rd.verdict, rd.code),
                                 (frame, verdict, code), rd.body())
                self.assertTrue(rd.gate and rd.gate[0], rd.gate)

    def test_the_audit_agrees_with_the_machine(self):
        for it in qc.set_b():
            status, code, _ = qc.SET_B_AUDIT.get(
                it.id, (it.expected_status, it.refusal_code, ""))
            frame, verdict, got = self.EXPECTED[it.id]
            self.assertEqual(status == "REFUSAL", verdict == "REFUSED")
            if status == "REFUSAL":
                self.assertEqual(code, got)

    def test_exact_values(self):
        rd = _read(qc.set_b()[0].query)
        self.assertIn("0.979633", rd.value)
        self.assertIn("4.6120e-5", rd.value)
        rd = _read(qc.set_b()[3].query)
        self.assertIn("150094635296999121/193036414974201856", rd.value)


class TestOutside(unittest.TestCase):
    """Every pre-registered outside question is read by its frame, gated,
    and carries the audited value."""

    def test_pre_registered_frames(self):
        from glm_universal.evaluation.question_set_b import OUTSIDE_AUDITED
        items = qc.outside()
        self.assertEqual(len(items), 112)
        for i, frame in qc.EXPECTED_FRAME.items():
            with self.subTest(index=i, frame=frame):
                rd = _read(items[i].text)
                self.assertEqual(rd.frame, frame)
                self.assertTrue(rd.gate and rd.gate[0], rd.gate)
                self.assertIn(OUTSIDE_AUDITED[i], rd.body())

    def test_unframed_questions_are_classed(self):
        items = qc.outside()
        for it in items:
            framed = qf.reads(it.text)
            self.assertEqual(framed, it.index in qc.EXPECTED_FRAME,
                             it.text[:80])
            if not framed:
                self.assertIn(qc.BOUNDARY[it.index], qc.BOUNDARY_CLASSES)


class TestTheAnswersFollowTheGivens(unittest.TestCase):
    """Nothing is looked up by question: change a given, the answer
    changes."""

    CASES = (
        ("Using the Routh-Hurwitz criterion with $G(s) = \\frac{K}{s(s + 1)"
         "(s + 3)}$, find the range of K.", "0 < K < 12"),
        ("A transformer has a leakage reactance of 0.10 p.u. on its own base "
         "of 50 MVA and 13.8 kV. Rescale to a system base of 200 MVA and "
         "13.8 kV.", "2/5 p.u."),
        ("Find the reflection coefficient for Z₀ = 50 Ω terminated with "
         "$Z_L = 100 + j0 \\Omega$ and the VSWR.", "VSWR = 2"),
        ("Two wavelengths λ₁ = 500 nm and λ₂ = 400 nm: the lowest order of "
         "the bright fringe that coincides.", "m1 = 4"),
        ("Compute the linear convolution of $x[n] = \\{1, 1\\}$ and "
         "$h[n] = \\{1, 1\\}$.", "[1, 2, 1]"),
        ("A Huffman code for p(A) = 0.5, p(B) = 0.5.", "L = 1 bits"),
        ("Joint entropy: $P(X=0, Y=0) = \\frac{1}{4}$, $P(X=0, Y=1) = "
         "\\frac{1}{4}$, $P(X=1, Y=0) = \\frac{1}{4}$, and P(X=1, Y=1) = "
         "1/4.", "H(X,Y) = 2"),
        ("Evaluate the second reading agree(y1, y2) at bit-flip rate p = "
         "1/100 under floor t = 999/1000; retention and residual.",
         "retention 1.000000"),
        ("Initialize a resolve_floor query with threshold parameter t = 0.",
         "FLOOR_OUT_OF_RANGE"),
        ("Evaluate integer decision procedure over system 6*x + 9*y == 5 "
         "with x, y in Z.", "no integer solution"),
    )

    def test_cases(self):
        for text, fragment in self.CASES:
            with self.subTest(text=text[:50]):
                rd = _read(text)
                self.assertTrue(rd.gate and rd.gate[0], rd.gate)
                self.assertIn(fragment, rd.body())


class TestTheGate(unittest.TestCase):

    def test_a_failing_script_is_caught(self):
        self.assertEqual(qf.run_gate("print('VERIFIED True')")[0], True)
        self.assertEqual(qf.run_gate("assert False")[0], False)
        self.assertEqual(qf.run_gate("print('VERIFIED False')")[0], False)

    def test_a_reading_the_gate_rejects_is_refused(self):
        bad = qf.Frame("broken", "a frame whose script disagrees",
                       lambda t: {} if t == "the broken frame probe" else None,
                       lambda g: qf.Reading("broken", True, "42", "", "",
                                            "assert 41 == 42"))
        qf.frames()
        qf.FRAMES.insert(0, bad)
        try:
            rd = qf.read("the broken frame probe")
        finally:
            qf.FRAMES.remove(bad)
        self.assertFalse(rd.answered)
        self.assertEqual(rd.code, "SCRIPT_GATE_FAILED")


class TestNonInterference(unittest.TestCase):
    """The frames surface reads no declared question of any earlier set."""

    def test_reads_census(self):
        for name, counts in router.reads_census().items():
            self.assertEqual(counts["frames"], 0, name)

    def test_no_declared_string_is_read(self):
        hits = []
        for f in glob.glob(os.path.join(OVERLAY, "glm_universal",
                                        "evaluation", "*.py")):
            if "question_set_b" in f or "typed_operator_cases" in f:
                continue     # the frames' own corpora (Phases 89 and 90)
            for node in ast.walk(ast.parse(open(f, encoding="utf-8").read())):
                if isinstance(node, ast.Constant) and \
                        isinstance(node.value, str) and " " in node.value \
                        and len(node.value) > 15 and qf.reads(node.value):
                    hits.append((os.path.basename(f), node.value[:60]))
        self.assertEqual(hits, [])


class TestK1(unittest.TestCase):
    """``-q`` goes through the router; ``--plan`` keeps the old path."""

    def _run(self, argv):
        sys.path.insert(0, OVERLAY)
        import GLM as glm_cli
        out = io.StringIO()
        code = glm_cli.main(argv, out=out)
        return code, out.getvalue()

    def test_frames_reached_by_q(self):
        code, text = self._run(["-q", "Initialize a resolve_floor query with "
                                      "threshold parameter t = 3/2."])
        self.assertEqual(code, 1)
        self.assertIn("SURFACE frames", text)
        self.assertIn("FLOOR_OUT_OF_RANGE", text)
        self.assertIn("VERIFIED True", text)

    def test_planner_questions_unchanged(self):
        from glm_universal.evaluation.cases import CASES
        for c in CASES[:8]:
            with self.subTest(q=c.question):
                self.assertEqual(self._run(["-q", c.question]),
                                 self._run(["--plan", "-q", c.question]))


if __name__ == "__main__":
    unittest.main()
