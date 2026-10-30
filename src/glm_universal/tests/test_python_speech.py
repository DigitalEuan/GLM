"""Tests for the GLM speaking Python: the substrate operations of
:mod:`glm_universal.reasoning.python_substrate`, the evaluator and payloads of
:mod:`glm_universal.reasoning.python_speech`, each held to the pass mark
``studies/PYTHON_SPEECH_STUDY.md`` declared before the module existed."""

from __future__ import annotations

import unittest
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from glm_universal.evaluation import python_speech_cases as C
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import python_substrate as ps


def _cpython(source):
    ns = {}
    exec(ps.PRELUDE, ns)
    return ns, ns["run_source"](source)


class TestRegisters(unittest.TestCase):

    def test_every_program_computes_and_is_undone(self):
        for name, row in ps.lane_table().items():
            with self.subTest(program=name):
                self.assertTrue(row["computes"])
                self.assertTrue(row["bijective"])
                self.assertTrue(row["restores"])

    def test_register_tower_agrees_with_cpython(self):
        for a, b in C.BITWISE_OPERANDS:
            self.assertEqual(ps.register_bitwise("and", a, b).value, a & b)
            self.assertEqual(ps.register_bitwise("or", a, b).value, a | b)
            self.assertEqual(ps.register_bitwise("xor", a, b).value, a ^ b)
            self.assertEqual(ps.register_bitwise("andnot", a, b).value, a & ~b)
            self.assertEqual(ps.register_invert(a).value, ~a)

    def test_a_wide_word_uses_several_carriers(self):
        run = ps.register_bitwise("xor", 2 ** 50, 1)
        self.assertEqual(run.carriers, 3)
        self.assertEqual(run.erased_bits, 0)

    def test_code_points_round_trip(self):
        for ch in "aΛ€😀":
            self.assertEqual(ps.register_load(ord(ch)).value, ord(ch))


class TestSubstrateMaps(unittest.TestCase):

    def test_slices_match_cpython(self):
        data = list(range(17))
        for start in (None, -30, -5, -1, 0, 2, 16, 40):
            for stop in (None, -30, -5, -1, 0, 3, 16, 40):
                for step in (None, -4, -1, 1, 3):
                    got = [data[i] for i in ps.slice_indices(17, start, stop,
                                                             step)]
                    self.assertEqual(got, data[start:stop:step])

    def test_zero_step_is_python_error(self):
        with self.assertRaises(ps.PythonRefusal) as cm:
            ps.slice_indices(3, None, None, 0)
        self.assertEqual(cm.exception.name, "PYTHON_ERROR")

    def test_shifts_are_dyadic(self):
        for n in (-1000, -1, 0, 5, 2 ** 40):
            for k in range(0, 30, 7):
                self.assertEqual(ps.dyadic_shift(n, k, True), n << k)
                self.assertEqual(ps.dyadic_shift(n, k, False), n >> k)

    def test_plane_is_a_floor(self):
        self.assertEqual(ps.plane(Fraction(5, 3), 4), 26)
        self.assertEqual(ps.plane(Fraction(-5, 3), 4), -27)

    def test_masks(self):
        self.assertEqual(ps.mask_of_frozenset({0, 23}), 1 | 1 << 23)
        with self.assertRaises(ps.PythonRefusal):
            ps.mask_of_frozenset({24})

    def test_ds_bits_count_is_floor(self):
        for p, q in ((2, 7), (3, 8), (0, 1), (5, 6)):
            for n in (1, 7, 21, 40):
                self.assertEqual(sum(ps.ds_bits(Fraction(p, q), n)),
                                 n * p // q)


class TestClassification(unittest.TestCase):

    def test_radius_four_ball(self):
        c1, c2 = ps.golay_encode(1), ps.golay_encode(2)
        for w in range(5):
            for pos in combinations(range(24), w):
                e = sum(1 << i for i in pos)
                c = ps.classify(c1 ^ e, [c1, c2])
                if w <= 3:
                    self.assertEqual((c.verdict, c.branch), ("branch", 0))
                else:
                    self.assertEqual(c.verdict, "AMBIGUOUS")
                    self.assertEqual(len(c.candidates), 6)

    def test_undeclared_codeword_is_uncorrectable(self):
        c1, c2 = ps.golay_encode(1), ps.golay_encode(2)
        c = ps.classify(ps.golay_encode(7), [c1, c2])
        self.assertEqual(c.verdict, "UNCORRECTABLE")
        self.assertGreaterEqual(min(c.distances), 5)

    def test_a_case_must_be_a_codeword(self):
        with self.assertRaises(ps.PythonRefusal):
            ps.classify(0, [1])


class TestAddresses(unittest.TestCase):

    def test_equivalent_pairs_share_an_address(self):
        for a, b in C.EQUIVALENT_PAIRS:
            with self.subTest(pair=(a, b)):
                self.assertEqual(ps.ast_address(a)["carrier"],
                                 ps.ast_address(b)["carrier"])

    def test_distinct_expressions_do_not_collide(self):
        seen = {}
        for s in C.DISTINCT_EXPRESSIONS:
            key = ps.ast_address(s)["carrier"]
            self.assertNotIn(key, seen, (s, seen.get(key)))
            seen[key] = s

    def test_subtraction_is_not_sorted(self):
        self.assertNotEqual(ps.canonical_form("a - (b - c)"),
                            ps.canonical_form("(a - b) - c"))

    def test_address_is_exact(self):
        for c in ps.ast_address("(a + b) * c")["carrier"]:
            self.assertIsInstance(c, Fraction)


class TestDeclaredCorpus(unittest.TestCase):
    """P1 and P2: every value equals CPython's, every refusal is named."""

    def test_values_equal_cpython(self):
        for cid, src in C.VALUE_CASES:
            with self.subTest(case=cid):
                p = sp.speak(src)
                self.assertTrue(p.answered, p.reason)
                ns, ref = _cpython(src)
                self.assertTrue(ns["same"](eval(p.value_literal, ns), ref))

    def test_refusals_are_named(self):
        for cid, src, want in C.REFUSAL_CASES:
            with self.subTest(case=cid):
                p = sp.speak(src)
                self.assertFalse(p.answered)
                self.assertEqual(p.refusal, want, p.reason)

    def test_the_payload_has_three_columns(self):
        p = sp.speak("'geometric language machine'[2:20:3]")
        self.assertTrue(p.column1 and p.column2 and p.column3)
        self.assertIn("MOG cells", "\n".join(p.column2))


class TestColumnThree(unittest.TestCase):
    """P3, on a sample in this unit; the report runs every case."""

    SAMPLE = ("frac-mixed", "bit-neg-or", "str-neg-slice", "fs-xor",
              "match-literal", "classify-match", "def-harmonic")

    def test_scripts_verify_and_mutants_fail(self):
        cases = dict(C.VALUE_CASES)
        for cid in self.SAMPLE:
            with self.subTest(case=cid):
                p = sp.speak(cases[cid])
                self.assertTrue(sp.verify_payload(p)["verified"])
                self.assertFalse(sp.verify_payload(
                    p, sp.mutated_script(p))["verified"])

    def test_refusal_certificates_verify(self):
        cases = {c: s for c, s, _ in C.REFUSAL_CASES}
        for cid in ("deep-hole", "uncorrectable", "zero-division",
                    "scale-mismatch", "float-truediv"):
            with self.subTest(case=cid):
                self.assertTrue(sp.verify_payload(sp.speak(cases[cid]))
                                ["verified"])

    def test_scripts_are_exact(self):
        from glm_universal.runtime.tct_engine import script_is_exact
        for cid, src in C.VALUE_CASES:
            ok, offenders = script_is_exact(sp.speak(src).column3)
            self.assertTrue(ok, (cid, offenders))


class TestBattery(unittest.TestCase):

    def test_no_answer_differs_from_cpython(self):
        report = sp.differential_battery()
        self.assertEqual(report["wrong"], 0)
        self.assertGreater(report["answered"], 2000)


class TestExactness(unittest.TestCase):

    def test_no_float_is_constructed(self):
        for module in (ps, sp):
            self.assertEqual(ex.module_float_sites(Path(module.__file__)), {})


if __name__ == "__main__":
    unittest.main()
