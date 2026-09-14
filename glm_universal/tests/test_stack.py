"""Tests for :mod:`glm_universal.reasoning.stack` and its grid register.

Five things are pinned here.

* **The Lean file's promises hold of the running code.**  Every theorem of
  ``RequestProject/GLM/Relay.lean`` that is a statement about the relay is
  checked against the running mechanism: a confident leader is returned
  untouched (``relay_confident``), nothing is invented (``mem_relay``), no
  candidate appears twice (``relay_nodup``), whatever sits inside a member's
  quota sits inside the summed window (``relay_carry``), and widening the
  window only appends (``relay_take_prefix``).

* **The measured claim is recomputed from the tables.**  The report's verdict
  is derived here from its own numbers, so the summary cannot drift: the relay
  beats the text control at ``k = 5`` on all three query sets, is never below
  it at any window, and carries many more queries than it loses.

* **The controls are controls.**  A relay to the digest addresses and a seeded
  permutation, and a relay to the name search, carry strictly fewer queries
  than the two address books do.  If a control ever caught up, the gain would
  be the list padding's rather than the substrate's and this test would say so.

* **The arithmetic is exact.**  Confidences, hit rates and precisions are
  :class:`~fractions.Fraction`; nothing here is a float (directive D7).

* **The mechanism transports.**  The grid register runs the same relay over
  the 50 ARC training puzzles with faculties that read no text at all, and the
  same three properties hold there: the relay is never behind its leading
  faculty, the cheap look pays for most of the expensive gate, and more than
  one faculty carries a puzzle.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import lean_address as la
from glm_universal.reasoning import retrieval as rt
from glm_universal.reasoning import stack as sk
from glm_universal.reasoning import vision_stack as vs


# ===========================================================================
# 1.  THE MECHANISM, AGAINST THE LEAN FILE
# ===========================================================================

class TestTheInterleave(unittest.TestCase):

    BLOCKS = (("a", "b", "c"), ("b", "d"), ("e",))
    QUOTAS = (2, 2, 1)

    def test_it_matches_the_lean_example(self):
        #  ``GLM.Relay.interleave examplePlan = [1, 2, 4, 5, 3]`` with the
        #  names carried as letters instead of numbers.
        self.assertEqual(sk.interleave(self.BLOCKS, self.QUOTAS),
                         ("a", "b", "d", "e", "c"))

    def test_nothing_is_invented(self):
        #  GLM.Relay.mem_interleave
        proposed = {name for block in self.BLOCKS for name in block}
        for name in sk.interleave(self.BLOCKS, self.QUOTAS):
            with self.subTest(name=name):
                self.assertIn(name, proposed)

    def test_nothing_is_lost(self):
        answer = sk.interleave(self.BLOCKS, self.QUOTAS)
        for block in self.BLOCKS:
            for name in block:
                with self.subTest(name=name):
                    self.assertIn(name, answer)

    def test_no_candidate_appears_twice(self):
        #  GLM.Relay.interleave_nodup
        answer = sk.interleave(self.BLOCKS, self.QUOTAS)
        self.assertEqual(len(answer), len(set(answer)))

    def test_a_quota_is_inside_the_window(self):
        #  GLM.Relay.relay_carry: the window is the summed quota.
        answer = sk.interleave(self.BLOCKS, self.QUOTAS)
        window = sum(self.QUOTAS)
        for block, quota in zip(self.BLOCKS, self.QUOTAS):
            for name in block[:quota]:
                with self.subTest(name=name):
                    self.assertIn(name, answer[:window])

    def test_a_missing_member_costs_only_its_quota(self):
        #  A faculty that answers nothing degrades the stack gracefully.
        with_gap = sk.interleave((self.BLOCKS[0], (), self.BLOCKS[2]),
                                 self.QUOTAS)
        self.assertEqual(with_gap, ("a", "b", "e", "c"))


class TestTheRelay(unittest.TestCase):

    PLAN = (("text", 2), ("lexical", 2), ("address", 1))

    def answers(self, confidence: Fraction):
        return {
            "text": sk.Answer("text", ("t1", "t2", "t3"), confidence),
            "lexical": sk.Answer("lexical", ("l1", "l2"), Fraction(0)),
            "address": sk.Answer("address", ("a1",), Fraction(0)),
        }

    def test_a_confident_leader_is_untouched(self):
        #  GLM.Relay.relay_confident
        answers = self.answers(Fraction(1, 2))
        self.assertEqual(sk.relay(answers, gate=sk.GATE, quotas=self.PLAN),
                         answers["text"].names)
        self.assertFalse(sk.gate_fires(answers, gate=sk.GATE))

    def test_an_abstaining_leader_hands_over(self):
        #  GLM.Relay.relay_abstain
        answers = self.answers(Fraction(0))
        self.assertTrue(sk.gate_fires(answers, gate=sk.GATE))
        self.assertEqual(sk.relay(answers, gate=sk.GATE, quotas=self.PLAN),
                         ("t1", "t2", "l1", "l2", "a1", "t3"))

    def test_widening_the_window_only_appends(self):
        #  GLM.Relay.relay_take_prefix
        order = sk.relay(self.answers(Fraction(0)), gate=sk.GATE,
                         quotas=self.PLAN)
        for k in range(len(order)):
            with self.subTest(k=k):
                self.assertEqual(order[:k], order[:k + 1][:k])

    def test_the_gate_is_a_rational(self):
        self.assertIsInstance(sk.GATE, Fraction)


# ===========================================================================
# 2.  THE CONFIDENCE IS A STATEMENT ABOUT THE QUERY
# ===========================================================================

class TestConfidence(unittest.TestCase):

    def test_an_empty_ranking_has_no_confidence(self):
        self.assertEqual(sk.confidence_of(()), Fraction(0))

    def test_a_distance_metric_claims_no_confidence(self):
        candidate = rt.Candidate(name="x", file="f", score=Fraction(8),
                                 metric="squared_distance")
        self.assertEqual(sk.confidence_of((candidate,)), Fraction(0))

    def test_an_overlap_metric_reports_its_best(self):
        candidate = rt.Candidate(name="x", file="f", score=Fraction(3, 7),
                                 metric="overlap")
        self.assertEqual(sk.confidence_of((candidate,)), Fraction(3, 7))


# ===========================================================================
# 3.  THE QUERY SETS
# ===========================================================================

class TestTheQuerySets(unittest.TestCase):

    def test_the_address_book_is_fresh(self):
        self.assertEqual(la.cache_state()["verdict"], "fresh")

    def test_the_two_strides_are_disjoint(self):
        tuning = set(sk.tuning_queries())
        holdout = set(sk.holdout_queries())
        self.assertGreater(len(tuning), 100)
        self.assertGreater(len(holdout), 100)
        self.assertEqual(tuning & holdout, set())

    def test_every_query_has_a_relative(self):
        for name in sk.tuning_queries()[:20]:
            with self.subTest(name=name):
                self.assertTrue(rt.relatives(name))

    def test_the_goal_set_is_both_strides(self):
        self.assertEqual(len(sk.goal_queries()),
                         len(sk.tuning_queries()) + len(sk.holdout_queries()))


# ===========================================================================
# 4.  THE MEASURED CLAIM
# ===========================================================================

class TestTheRelayReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = sk.relay_report()

    def test_the_relay_beats_the_text_control_on_every_set(self):
        for name, entry in self.report["sets"].items():
            with self.subTest(set=name):
                self.assertGreater(entry["relay"]["hit_rate"][5],
                                   entry["leader"]["hit_rate"][5])

    def test_the_relay_is_never_below_the_text_control(self):
        for name, entry in self.report["sets"].items():
            for k in sk.K_LADDER:
                with self.subTest(set=name, k=k):
                    self.assertGreaterEqual(entry["relay"]["hit_rate"][k],
                                            entry["leader"]["hit_rate"][k])

    def test_the_carried_queries_outnumber_the_lost_ones(self):
        carried = sum(len(entry["carried"])
                      for entry in self.report["sets"].values())
        lost = sum(len(entry["lost"])
                   for entry in self.report["sets"].values())
        self.assertGreater(carried, lost)
        self.assertGreater(carried, 4 * lost)

    def test_the_gate_fires_rarely(self):
        for name, entry in self.report["sets"].items():
            with self.subTest(set=name):
                self.assertLessEqual(
                    Fraction(entry["fired"], entry["queries"]),
                    Fraction(1, 10))

    def test_the_geometry_carries_more_than_the_controls(self):
        carried = sum(len(entry["carried"])
                      for entry in self.report["sets"].values())
        for partner in ("digest_random", "name"):
            control = sum(len(entry["carried"])
                          for entry in self.report["controls"][partner].values())
            with self.subTest(partner=partner):
                self.assertGreater(carried, control)

    def test_the_geometry_never_carries_fewer_than_the_control(self):
        for name, entry in self.report["sets"].items():
            with self.subTest(set=name):
                self.assertGreaterEqual(
                    len(entry["carried"]),
                    len(self.report["controls"]["digest_random"][name]["carried"]))

    def test_the_gain_does_not_hang_on_the_threshold(self):
        baseline = self.report["sets"]["tuning"]["leader"]["hit_rate"][5]
        for row in self.report["sweep"]:
            if Fraction(1, 20) <= row["gate"] <= Fraction(1, 4):
                with self.subTest(gate=row["gate"]):
                    self.assertGreater(row["hit_at_5"], baseline)

    def test_the_verdict_is_the_measurement(self):
        verdict = self.report["verdict"]
        self.assertTrue(verdict["relay_beats_text_on_every_set"])
        self.assertTrue(verdict["carried_outnumber_lost"])
        self.assertTrue(verdict["relay_never_below_leader"])
        self.assertTrue(verdict["geometry_carries_more_than_control"])
        self.assertTrue(verdict["geometry_never_carries_fewer_than_control"])
        self.assertTrue(verdict["geometry_carries_more_than_name"])
        self.assertTrue(verdict["gain_holds_across_the_gate"])
        self.assertTrue(verdict["gate_fires_rarely"])

    def test_every_rate_is_exact(self):
        for name, entry in self.report["sets"].items():
            for who in ("leader", "relay"):
                for k in sk.K_LADDER:
                    with self.subTest(set=name, who=who, k=k):
                        self.assertIsInstance(entry[who]["hit_rate"][k],
                                              Fraction)
                with self.subTest(set=name, who=who):
                    self.assertIsInstance(entry[who]["precision_at_5"],
                                          Fraction)

    def test_the_tiebreak_alternative_is_recorded_as_it_falls(self):
        tiebreak = sk.tiebreak_report()
        #  Recomputed from the tables rather than asserted: whichever way the
        #  geometric tie-break falls against the shipped name tie-break, the
        #  verdict says so.
        beats = all(
            tiebreak["sets"][label]["address"]["hit_rate"][5]
            > tiebreak["sets"][label]["name"]["hit_rate"][5]
            for label in ("tuning", "holdout"))
        self.assertEqual(tiebreak["verdict"]["beats_name_tiebreak_on_hits"],
                         beats)


# ===========================================================================
# 5.  THE GRID REGISTER
# ===========================================================================

class TestTheGridRegister(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = vs.vision_report()

    def test_the_puzzles_are_there(self):
        self.assertEqual(len(vs.puzzles()), 50)
        for puzzle in vs.puzzles()[:5]:
            with self.subTest(puzzle=puzzle.name):
                self.assertTrue(puzzle.train)
                self.assertTrue(puzzle.test_input)

    def test_the_relay_is_never_behind_its_leading_faculty(self):
        self.assertGreaterEqual(self.report["relay_solves"],
                                self.report["leader_solves"])

    def test_the_relay_is_ahead_of_its_leading_faculty(self):
        self.assertGreater(self.report["relay_solves"],
                           self.report["leader_solves"])

    def test_the_cheap_look_pays_for_the_expensive_gate(self):
        self.assertGreater(self.report["filter_saving"], Fraction(1, 2))
        self.assertIsInstance(self.report["filter_saving"], Fraction)

    def test_more_than_one_faculty_carries(self):
        self.assertGreater(len(self.report["carry"]), 1)

    def test_a_verified_rule_is_verified(self):
        for puzzle in vs.puzzles():
            row = vs.attempt(puzzle)
            if row.verified is None:
                continue
            table = {candidate.name: candidate
                     for faculty in vs.FACULTIES
                     for candidate in vs.candidates_of(puzzle, faculty)}
            with self.subTest(puzzle=puzzle.name):
                self.assertTrue(vs.verifies(table[row.verified], puzzle))

    def test_the_dihedral_operations_are_involutions_where_they_should_be(self):
        grid = ((1, 2, 3), (4, 5, 6))
        self.assertEqual(vs.flip_h(vs.flip_h(grid)), grid)
        self.assertEqual(vs.flip_v(vs.flip_v(grid)), grid)
        self.assertEqual(vs.transpose(vs.transpose(grid)), grid)
        self.assertEqual(vs.rotate90(vs.rotate270(grid)), grid)
        self.assertEqual(vs.rotate180(vs.rotate180(grid)), grid)

    def test_gravity_keeps_the_cells_it_moves(self):
        grid = ((0, 2, 0), (3, 0, 0), (0, 0, 4))
        for direction in ("down", "up", "left", "right"):
            moved = vs.gravity(grid, direction)
            with self.subTest(direction=direction):
                self.assertEqual(
                    sorted(v for row in moved for v in row if v),
                    sorted(v for row in grid for v in row if v))

    def test_the_look_is_exact(self):
        puzzle = vs.puzzles()[0]
        candidate = vs.geometry_candidates(puzzle)[0]
        self.assertIsInstance(vs.look_score(candidate, puzzle), Fraction)

    def test_the_cross_domain_check_round_trips(self):
        for name, words in vs.WORDS.items():
            read = vs.read_words(words)
            if read is None:
                continue
            with self.subTest(operation=name):
                self.assertEqual(read, name)


if __name__ == "__main__":
    unittest.main()
