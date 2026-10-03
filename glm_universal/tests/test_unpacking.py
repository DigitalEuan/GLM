"""Phase 97 -- argument unpacking and the third view on demand.

``studies/UNPACKING_RESCORE_STUDY.md`` declares marks U1-U5 and R1-R7 before
any code (:mod:`glm_universal.evaluation.unpacking_cases`).  These tests hold
the facts the round rests on at the sampled scale (one probe codeword, two
census first errors); the full census is
``python3 -m glm_universal.tools unpacking``.
"""

from __future__ import annotations

import unittest
from itertools import combinations

from glm_universal.evaluation import unpacking_cases as C
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import second_view as sv
from glm_universal.runtime import unpacking_report as ur
from glm_universal.substrate.mog import GOLAY_MASKS


def _cpython(src):
    return sp._cpython_reference(src)[1]


class TestUnpackingInTheDialect(unittest.TestCase):

    def test_u1_the_refused_program_is_answered(self):
        cid, src = C.RESCORED
        p = sp.speak(src)
        self.assertIsNone(p.refusal, cid)
        self.assertEqual(p.value, _cpython(src))
        self.assertTrue(sp.verify_payload(p)["verified"])
        self.assertFalse(sp.verify_payload(p, sp.mutated_script(p))["verified"])

    def test_u2_call_cases_equal_cpython(self):
        for cid, src in C.CALL_CASES:
            p = sp.speak(src)
            self.assertIsNone(p.refusal, cid)
            ref = _cpython(src)
            self.assertIs(type(p.value), type(ref), cid)
            self.assertEqual(p.value, ref, cid)

    def test_u3_vararg_cases_equal_cpython(self):
        for cid, src in C.VARARG_CASES:
            p = sp.speak(src)
            self.assertIsNone(p.refusal, cid)
            ref = _cpython(src)
            self.assertIs(type(p.value), type(ref), cid)
            self.assertEqual(p.value, ref, cid)

    def test_u4_refusals_by_name(self):
        for cid, src, name in C.UNPACK_REFUSALS:
            self.assertEqual(sp.speak(src).refusal, name, cid)

    def test_unpacking_is_a_named_step(self):
        p = sp.speak("max(*range(3, 40, 7))")
        self.assertTrue(any("Unpack" in s.language for s in p.steps))
        q = sp.speak("def f(a, *rest):\n    return rest\nf(1, 2, 3)")
        self.assertTrue(any("into the tuple rest" in s.language
                            for s in q.steps))

    def test_star_round_trip(self):
        # OnDemandView.lean, star_round_trip: def f(*r) called f(*xs).
        for xs in ("()", "(1,)", "(1, 2, 3)", "('a', 'b')"):
            src = f"def f(*r):\n    return r\nf(*{xs})"
            self.assertEqual(sp.speak(src).value, _cpython(src))

    def test_u5_earlier_programs_do_not_move(self):
        r = ur.no_regression()
        self.assertEqual(r["moved"], [])
        self.assertEqual(r["moved_as_declared"], list(ur.DECLARED_MOVES))
        self.assertTrue(r["met"])

    def test_before_the_round_every_program_was_refused(self):
        b = ur.before()
        self.assertEqual(b["answered_before"], 0)
        self.assertEqual(b["refusals_before"], ["UNSUPPORTED"])


class TestOnDemand(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = sv.on_demand_report(full=False)

    def test_r1_same_answers_fewer_reads(self):
        r1 = self.report["R1"]
        self.assertTrue(r1["met"])
        self.assertEqual(r1["third_reads"], 174)     # pair_frame_open_count
        self.assertEqual(r1["views_read"], 2 * 10626 + 174)

    def test_r2_inside_the_radius(self):
        r2 = self.report["R2"]
        self.assertTrue(r2["met"])
        self.assertEqual(r2["third_reads"], 0)

    def test_r3_weight5_matches_two_views(self):
        r3 = self.report["R3"]
        self.assertEqual(r3["same_as_two"], r3["reads"])
        self.assertEqual(r3["third_reads"], 0)

    def test_r4_r6_independent(self):
        for key in ("R4", "R5", "R6"):
            self.assertTrue(self.report[key]["met"], key)
        self.assertEqual(self.report["R5"]["resolved"],
                         self.report["R5"]["reads"])

    def test_r7_census(self):
        self.assertTrue(self.report["R7"]["met"])

    def test_read_on_demand_names_the_frame(self):
        c = GOLAY_MASKS[64]
        tets = [sum(1 << i for i in s) for s in combinations(range(24), 4)]
        e = next(t for t in tets if sv.octads_through(t | sv.rot(t, 1)) == 1)
        fork, taken = sv.FramedRegister(c).inject(e).read_on_demand()
        self.assertEqual(taken, 3)
        self.assertEqual(fork.value, c)
        f = next(t for t in tets if sv.octads_through(t | sv.rot(t, 1)) == 0)
        fork2, taken2 = sv.FramedRegister(c).inject(f).read_on_demand()
        self.assertEqual((fork2.value, taken2), (c, 2))
        # 0b1111 is one of the 174: its union with its rotation is five
        # consecutive points, and five points lie in an octad.
        self.assertEqual(sv.FramedRegister(c).inject(0b1111)
                         .read_on_demand()[1], 3)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
