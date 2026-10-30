"""Phase 96 -- second readings: the framed register.

``studies/SECOND_VIEW_STUDY.md`` declares marks V1-V9 before any code
(:mod:`glm_universal.evaluation.second_view_cases`).  These tests hold the
facts the round rests on at the sampled scale (one probe codeword); the full
census is ``python3 -m glm_universal.tools second-view``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from itertools import combinations

from glm_universal.evaluation import second_view_cases as C
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import second_view as sv
from glm_universal.substrate.mog import GOLAY_MASKS, GOLAY_SET


class TestFrames(unittest.TestCase):

    def test_rotation_round_trips(self):
        for w in (1, 0b1111, 0xABCDEF, 1 << 23):
            for k in range(24):
                self.assertEqual(sv.rot(sv.rot(w, -k), k), w)

    def test_views_are_codewords_and_align(self):
        c = GOLAY_MASKS[100]
        stored = sv.store_views(c)
        self.assertEqual(len(stored), len(C.FRAMES))
        for w, k in zip(stored, C.FRAMES):
            self.assertEqual(sv.align(w, k), c)

    def test_store_refuses_a_non_codeword(self):
        with self.assertRaises(ValueError):
            sv.store_views(1)

    def test_common_mode_burst_reads_as_rotations(self):
        c, e = GOLAY_MASKS[7], 0b1111
        reg = sv.FramedRegister(c).inject(e)
        for w, k in zip(reg.stored, C.FRAMES):
            self.assertEqual(sv.align(w, k) ^ c, sv.rot(e, k))


class TestMarks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = sv.second_view_report(full=False)

    def test_v1_live_count_is_predicted(self):
        v1 = self.report["V1"]
        self.assertTrue(v1["met"])
        self.assertEqual(v1["open_bursts"], 174)      # pair_frame_open_count
        self.assertEqual(v1["open_live_counts"], [2])
        self.assertEqual(v1["resolved"], 10626 - 174)

    def test_v2_three_views_resolve_every_burst(self):
        v2 = self.report["V2"]
        self.assertEqual((v2["reads"], v2["resolved"], v2["wrong"]),
                         (10626, 10626, 0))

    def test_v3_no_single_second_frame_suffices(self):
        v3 = self.report["V3"]
        self.assertTrue(v3["met"])
        self.assertEqual(len(v3["open_by_frame"]), 23)

    def test_v4_independent_faults(self):
        v4 = self.report["V4"]
        self.assertEqual(v4["reads"], 4224)
        self.assertEqual(v4["wrong"], 0)
        # Declared 4,224 of 4,224; the register's second view reads e_j
        # rotated by one, and 64 of those pairs share an octad: not met.
        self.assertEqual(v4["resolved"], 4160)
        self.assertFalse(v4["met"])

    def test_v5_inside_the_packing_radius(self):
        self.assertTrue(self.report["V5"]["met"])

    def test_weight5_views_refuse_where_one_view_is_wrong(self):
        w5 = self.report["weight5"]
        self.assertEqual(w5["single"]["wrong"], w5["single"]["reads"])
        self.assertEqual(w5["three"]["wrong"], 0)
        self.assertLessEqual(w5["two"]["wrong"], 6)

    def test_v6_composition_sampled(self):
        v6 = self.report["V6"]
        self.assertTrue(v6["met"])
        for row in v6["rows"]:
            self.assertEqual(row["open"], row["predicted_open"])
            self.assertEqual(row["wrong"], 0)

    def test_v7_escalation_is_the_intersection(self):
        v7 = self.report["V7"]
        self.assertTrue(v7["met"])
        self.assertEqual(v7["rows"]["x1"]["gained"], 0)


class TestSoftIdentity(unittest.TestCase):
    """The identity `soft_mean_dist` of SecondView.lean, numerically."""

    def test_mean_distance_identity(self):
        words = (0, 0b1111, 0xF0F0F0, GOLAY_MASKS[9], 0x123456)
        for a, b, x in combinations(words, 3):
            lhs = sum((Fraction(((a >> j) & 1) + ((b >> j) & 1), 2)
                       - ((x >> j) & 1)) ** 2 for j in range(24))
            d = lambda u, v: bin(u ^ v).count("1")
            rhs = Fraction(d(a, x) + d(b, x), 2) - Fraction(d(a, b), 4)
            self.assertEqual(lhs, rhs)


class TestDialect(unittest.TestCase):

    def test_declared_programs(self):
        for cid, src in C.DIALECT_CASES:
            p = sp.speak(src)
            # ``views-clean`` was refused in Phase 96 (no argument
            # unpacking, so mark V8 was not met as declared).  Phase 97
            # added unpacking and re-scored it as a fresh declared case
            # (mark U1 of studies/UNPACKING_RESCORE_STUDY.md): a recorded
            # later change, so it is answered here too.
            self.assertIsNone(p.refusal, cid)
            self.assertEqual(p.value, sp._cpython_reference(src)[1], cid)

    def test_declared_refusals(self):
        for cid, src, name in C.DIALECT_REFUSALS:
            self.assertEqual(sp.speak(src).refusal, name, cid)

    def test_two_views_refuse_an_open_burst_by_name(self):
        c = GOLAY_MASKS[64]
        tets = [sum(1 << i for i in s) for s in combinations(range(24), 4)]
        e = next(t for t in tets
                 if sv.octads_through(t | sv.rot(t, 1)) == 1)
        w = sv.store_views(c)
        p = sp.speak(f"read_views({w[0] ^ e}, {w[1] ^ e})")
        self.assertEqual(p.refusal, "AMBIGUOUS")
        q = sp.speak(f"read_views({w[0] ^ e}, {w[1] ^ e}, {w[2] ^ e})")
        self.assertEqual(q.value, c)
        self.assertIn(q.value, GOLAY_SET)

    def test_the_payload_verifies(self):
        src = dict(C.DIALECT_CASES)["views-burst"]
        p = sp.speak(src)
        self.assertTrue(sp.verify_payload(p)["verified"])
        self.assertFalse(sp.verify_payload(p, sp.mutated_script(p))["verified"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
