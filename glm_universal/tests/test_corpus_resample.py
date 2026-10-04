"""The declared resampling (Phase 100): every sub-corpus that drops one Lean
file and every stride offset of the query sample, against the rule declared
in ``studies/CORPUS_RESAMPLE_STUDY.md`` before the module existed.

The census-sized figures are read from the stored measurements when they are
current (``tools corpus-resample --write``), and re-taken otherwise.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import corpus_resample as crs
from glm_universal.reasoning import retrieval as rt

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "overlay" / "glm_lean" / crs.LEAN_FILE

_REPORT = None


def report():
    global _REPORT
    if _REPORT is None:
        _REPORT = crs.current() or crs.corpus_resample_report()
    return _REPORT


class TestTheSignTest(unittest.TestCase):

    def test_exact_values(self):
        self.assertEqual(Fraction(1, 4), crs.sign_test(3, 0))
        self.assertEqual(Fraction(1), crs.sign_test(2, 2))
        self.assertEqual(Fraction(1), crs.sign_test(0, 0))
        # 2 * (1 + 10) / 2^10
        self.assertEqual(Fraction(22, 1024), crs.sign_test(9, 1))

    def test_symmetric_and_a_probability_bound(self):
        for b, c in ((161, 94), (44, 59), (7, 0), (12, 12)):
            with self.subTest(b=b, c=c):
                self.assertEqual(crs.sign_test(b, c), crs.sign_test(c, b))
                self.assertLessEqual(crs.sign_test(b, c), 1)


class TestTheSampling(unittest.TestCase):

    def test_offset_zero_is_the_systems_own_sample(self):
        names = rt.corpus()
        relatives = rt.relative_table()
        for mode in crs.MODES:
            with self.subTest(mode=mode):
                self.assertEqual(
                    rt.query_sample(crs.SAMPLE_SIZE[mode]),
                    crs._sample(names, crs.SAMPLE_SIZE[mode], 0, relatives))

    def test_the_offsets_partition_the_corpus(self):
        names = rt.corpus()
        for size in crs.SAMPLE_SIZE.values():
            stride = max(1, len(names) // size)
            seen = []
            for offset in range(stride):
                seen.extend(names[offset::stride])
            self.assertEqual(sorted(seen), sorted(names))
            self.assertEqual(len(seen), len(set(seen)))

    def test_the_census_depth_covers_any_one_file(self):
        largest = max(len(v) for v in crs.file_members().values())
        self.assertEqual(largest + max(rt.K_LADDER), crs.depth())


class TestTheFilter(unittest.TestCase):
    """A small live instance of mark M2: two queries, one dropped file."""

    def test_a_direct_reranking_equals_the_filtered_full_ranking(self):
        names = crs._names()
        members = crs.file_members()
        dropped_file = sorted(members)[0]
        dropped = frozenset(members[dropped_file])
        sub = tuple(n for n in names if n not in dropped)
        top = max(rt.K_LADDER)
        for query in (sub[3], sub[len(sub) // 2]):
            full = crs._query_row((query, "declarations", None))
            direct = crs._query_row((query, "declarations", sub))
            for scheme in crs.SCHEMES:
                with self.subTest(query=query, scheme=scheme):
                    filtered = [n for n in full[scheme] if n not in dropped][:top]
                    self.assertEqual(filtered, list(direct[scheme][:top]))


class TestTheMarks(unittest.TestCase):

    def test_m1_the_engine_reproduces_both_studies(self):
        self.assertTrue(report()["marks"]["M1"])
        self.assertEqual([], report()["faithfulness"]["mismatches"])

    def test_m2_the_filter_is_exact(self):
        self.assertTrue(report()["marks"]["M2"])
        self.assertEqual(5, len(report()["filter_check"]["files"]))

    def test_m3_every_resample_scored(self):
        r = report()
        self.assertTrue(r["marks"]["M3"])
        self.assertEqual(r["files"], len(r["drop_queries"]["declarations"]))
        self.assertEqual(r["census"], r["pool"])

    def test_m4_the_control_failed_as_recorded(self):
        # The declared control j (native2 = features2 in hits) does not hold
        # in every resample: the two rankings share their first two keys and
        # differ in the third (lexical Leech distance against name), which
        # can move a hit inside a tie.  The study records M4 as not met.
        r = report()
        self.assertFalse(r["marks"]["M4"])
        for mode, v in r["verdicts"]["j"].items():
            with self.subTest(mode=mode):
                self.assertEqual("fails", v["verdict"])

    def test_m5_the_held_fixed_addresses_are_priced(self):
        held = report()["held_fixed"]
        self.assertTrue(report()["marks"]["M5"])
        self.assertEqual(0, held["baseline_changed"])
        self.assertGreater(held["largest"], 0)

    def test_the_effects_found(self):
        verdicts = report()["verdicts"]
        self.assertEqual("effect", verdicts["i"]["declarations"]["verdict"])

    def test_the_post_hoc_readings_are_draws(self):
        verdicts = report()["verdicts"]
        for rid in ("a", "b", "d"):
            for mode, v in verdicts[rid].items():
                with self.subTest(reading=rid, mode=mode):
                    self.assertNotEqual("effect", v["verdict"])


class TestTheLeanFile(unittest.TestCase):

    def test_no_sorry_and_the_named_theorems(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("sorted_perm_filter_eq", "take_filter_take",
                     "stride_slice_iff", "stride_offsets_card",
                     "signTest_symm"):
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":
    unittest.main()
