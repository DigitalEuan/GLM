"""The archive's reasoning loop, pinned.

``glm_universal.reasoning.search_loop`` is the computational half of
``studies/SEARCH_LOOP_STUDY.md``, and every census it reports is also a theorem
in ``RequestProject/GLM/SearchLoop.lean``.  This file fixes those numbers, and
checks the loop's *properties* -- soundness, monotonicity, termination,
blindness of the gate to its own residue -- directly on the same candidate set,
so that the Lean statements have a running counterpart rather than only a
proof.

The Lean file is the specification (D8) and everything here is exact (D7).
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import search_loop as sl


class TestTheGroup(unittest.TestCase):
    """The candidate set really is the eight symmetries of the square."""

    def test_the_eight_tables_are_closed_under_composition(self):
        # GLM.SearchLoop.d4_closed
        self.assertTrue(sl.group_is_closed())

    def test_they_are_eight_different_permutations(self):
        # GLM.SearchLoop.d4_faithful
        self.assertTrue(sl.group_is_faithful())

    def test_the_action_stays_inside_the_grids(self):
        # GLM.SearchLoop.act_lt
        self.assertTrue(all(sl.act(k, g) < sl.GRIDS
                            for k in range(sl.GROUP_ORDER)
                            for g in range(sl.GRIDS)))

    def test_the_identity_is_the_identity(self):
        self.assertTrue(all(sl.act(0, g) == g for g in range(sl.GRIDS)))


class TestWhatOneExampleLeaves(unittest.TestCase):
    """The hard gate on a single example."""

    def test_the_truth_always_survives(self):
        # GLM.SearchLoop.gate_sound
        for g in range(sl.GRIDS):
            for k in range(sl.GROUP_ORDER):
                self.assertIn(k, sl.survivors(g, sl.act(k, g)))

    def test_the_survivors_are_the_stabiliser_coset(self):
        # GLM.SearchLoop.card_symSurvivors
        for g in range(sl.GRIDS):
            for k in range(sl.GROUP_ORDER):
                self.assertEqual(len(sl.survivors(g, sl.act(k, g))),
                                 sl.stabiliser_card(g))

    def test_the_stabiliser_census_is_the_lean_one(self):
        # GLM.SearchLoop.stab_census
        self.assertEqual(sl.stabiliser_census(),
                         {1: 288, 2: 200, 4: 16, 8: 8})

    def test_the_census_accounts_for_every_grid(self):
        self.assertEqual(sum(sl.stabiliser_census().values()), 512)

    def test_the_total_is_eight_times_the_orbit_count(self):
        # GLM.SearchLoop.stab_total, GLM.SearchLoop.burnside_orbits
        total = sum(k * v for k, v in sl.stabiliser_census().items())
        self.assertEqual(total, 816)
        self.assertEqual(sl.orbit_count(), 102)
        self.assertEqual(total, sl.GROUP_ORDER * sl.orbit_count())

    def test_the_mean_number_of_survivors(self):
        self.assertEqual(sl.mean_survivors(), Fraction(51, 32))

    def test_every_survivor_count_divides_the_group_order(self):
        # Lagrange, GLM.SearchLoop.card_stabF_dvd
        self.assertTrue(all(sl.GROUP_ORDER % k == 0
                            for k in sl.stabiliser_census()))

    def test_the_gate_is_blind_to_its_own_residue(self):
        # GLM.SearchLoop.gate_blind: survivors agree on the observed input
        for g in range(sl.GRIDS):
            out = sl.act(6, g)
            kept = sl.survivors(g, out)
            self.assertTrue(all(sl.act(k, g) == out for k in kept))


class TestHowAmbiguousTheAnswerIs(unittest.TestCase):
    """What the survivors disagree about, on a fresh question."""

    def test_the_ambiguity_census_is_the_lean_one(self):
        # GLM.SearchLoop.ambiguity_census
        self.assertEqual(sl.ambiguity_census(),
                         {1: 160320, 2: 91776, 4: 7744, 8: 2304})

    def test_the_census_accounts_for_every_pair(self):
        self.assertEqual(sum(sl.ambiguity_census().values()), 262144)

    def test_the_total_and_the_mean(self):
        # GLM.SearchLoop.ambiguity_total
        census = sl.ambiguity_census()
        self.assertEqual(sum(k * v for k, v in census.items()), 393280)
        self.assertEqual(sl.mean_ambiguity(), Fraction(6145, 4096))

    def test_one_example_determines_the_answer_five_times_in_eight(self):
        self.assertEqual(sl.determined_fraction(), Fraction(2505, 4096))
        self.assertLess(Fraction(3, 5), sl.determined_fraction())
        self.assertLess(sl.determined_fraction(), Fraction(5, 8))

    def test_every_ambiguity_divides_the_number_of_survivors(self):
        # GLM.SearchLoop.ambiguity_dvd_stab
        for g in range(0, sl.GRIDS, 7):
            for t in range(0, sl.GRIDS, 5):
                self.assertEqual(sl.stabiliser_card(g) % sl.ambiguity(g, t), 0)

    def test_the_answer_is_unique_exactly_when_the_question_is_fixed(self):
        # GLM.SearchLoop.ambiguity_eq_one_iff
        for g in range(0, sl.GRIDS, 7):
            for t in range(0, sl.GRIDS, 5):
                unique = sl.ambiguity(g, t) == 1
                fixed = all(sl.act(k, t) == t for k in sl.stabiliser(g))
                self.assertEqual(unique, fixed)

    def test_the_prediction_set_does_not_depend_on_the_observed_output(self):
        # card_predictions_eq_orbit: the count is the orbit, whatever s0 was
        for g in range(0, sl.GRIDS, 11):
            for t in range(0, sl.GRIDS, 13):
                counts = {len(sl.predictions(g, sl.act(k, g), t))
                          for k in range(sl.GROUP_ORDER)}
                self.assertEqual(counts, {sl.ambiguity(g, t)})


class TestTheLoop(unittest.TestCase):
    """Two rounds, and the properties the Lean file proves in general."""

    def test_a_second_example_only_removes_candidates(self):
        # GLM.SearchLoop.survivors_antitone
        for g1 in range(0, sl.GRIDS, 13):
            for g2 in range(0, sl.GRIDS, 17):
                first = set(sl.survivors(g1, sl.act(6, g1)))
                both = first & set(sl.survivors(g2, sl.act(6, g2)))
                self.assertTrue(both <= first)
                self.assertIn(6, both)

    def test_the_second_example_census(self):
        second = sl.second_example_census()
        self.assertEqual(second["pairs"], 262144)
        self.assertEqual(second["census"],
                         {1: 245760, 2: 15936, 4: 384, 8: 64})
        self.assertEqual(second["pinned_by_two"], 245760)
        self.assertEqual(second["pinned_by_one"], 147456)
        self.assertEqual(second["mean"], Fraction(2185, 2048))

    def test_two_examples_beat_one(self):
        second = sl.second_example_census()
        self.assertGreater(second["pinned_by_two"], second["pinned_by_one"])

    def test_the_loop_reaches_a_fixed_point(self):
        # GLM.SearchLoop.loop_stabilises, on this candidate set
        truth = 6
        state = set(range(sl.GROUP_ORDER))
        history = [frozenset(state)]
        for g in range(sl.GRIDS):
            state &= set(sl.survivors(g, sl.act(truth, g)))
            history.append(frozenset(state))
            if history[-1] == history[-2]:
                break
        self.assertLessEqual(len(history) - 1, sl.GROUP_ORDER)
        self.assertIn(truth, state)

    def test_full_information_isolates_the_truth(self):
        # GLM.SearchLoop.full_information: with every grid observed, the
        # survivors are exactly the candidates computing the same function
        truth = 6
        state = set(range(sl.GROUP_ORDER))
        for g in range(sl.GRIDS):
            state &= set(sl.survivors(g, sl.act(truth, g)))
        self.assertEqual(state, {truth})


class TestTheSoftGate(unittest.TestCase):
    """The rule the archive's ledger records as catastrophic."""

    def test_the_score_prefers_a_refuted_candidate(self):
        # GLM.SearchLoop.score_gate_unsound
        witness = sl.gate_beats_score_witness()
        self.assertTrue(witness["truth_survives"])
        self.assertTrue(witness["score_choice_is_refuted"])
        self.assertNotEqual(witness["score_choice"], witness["truth"])

    def test_the_gate_keeps_the_truth_on_that_example(self):
        witness = sl.gate_beats_score_witness()
        self.assertIn(witness["truth"], witness["survivors"])


class TestTheReport(unittest.TestCase):
    """The report subject, and the figures it publishes."""

    def test_the_report_carries_every_census(self):
        report = sl.search_loop_report()
        self.assertEqual(report["stabiliser_census"],
                         {1: 288, 2: 200, 4: 16, 8: 8})
        self.assertEqual(report["ambiguity_census"],
                         {1: 160320, 2: 91776, 4: 7744, 8: 2304})
        self.assertEqual(report["orbits"], 102)
        self.assertEqual(report["mean_ambiguity"], Fraction(6145, 4096))
        self.assertTrue(report["every_ambiguity_divides_eight"])

    def test_the_report_names_its_lean_file(self):
        self.assertEqual(sl.search_loop_report()["lean_file"],
                         "RequestProject/GLM/SearchLoop.lean")

    def test_the_runtime_answers_the_subject(self):
        from glm_universal.runtime.session import GeometricSession
        answer = GeometricSession().ask("report searchloop").answer
        self.assertIn("51/32", answer)
        self.assertIn("stabiliser of the example", answer)

    def test_no_floats_anywhere_in_the_report(self):
        def walk(value):
            if isinstance(value, float):
                return False
            if isinstance(value, dict):
                return all(walk(v) for v in value.values())
            if isinstance(value, (list, tuple)):
                return all(walk(v) for v in value)
            return True
        self.assertTrue(walk(sl.search_loop_report()))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
