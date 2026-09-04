"""Tests for :mod:`glm_universal.reasoning.controller`.

Six things are pinned here.

* **The state space is the register's, not a restatement of it.**  Each of the
  ten generators is checked against ``data_objects.physics`` to be the unit
  quantity of its axis, with zero scale, rank and grading.

* **The Lean file's promises hold of the running loop.**  The shortest plan has
  exactly ``‖t‖₁`` moves (``minimal_length_eq_l1``); a descent move always
  exists (``exists_descent``); a plan replays to its target (``replay``); and
  an invariant that no move changes makes a target unreachable at any depth
  (``unreachable_of_invariant``).

* **No answer is trusted because the loop produced it.**  Every plan the report
  counts as solved was re-checked by
  :func:`glm_universal.reasoning.verifier.verify_expression_pair`, which is a
  different instrument, and the test recomputes that check rather than reading
  the flag.

* **A refusal is a refusal.**  An unreachable target is refused with an
  invariant named and *no* search; an exhausted beam is refused rather than
  answered with its closest state.

* **The controls are controls.**  No guidance and the random scorer are scored
  on the same tasks, and the substrate's heuristic is required to beat both --
  and required *not* to beat the exact one, which is the honest reading of the
  measurement.

* **The arithmetic is exact.**  Every rate is a :class:`~fractions.Fraction`,
  every distance an ``int``, no float is constructed.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects import physics as do_physics
from glm_universal.reasoning import controller as ct
from glm_universal.reasoning import verifier as vf


# ===========================================================================
# 1.  THE GENERATORS ARE THE REGISTER'S UNIT QUANTITIES
# ===========================================================================

class TestTheGenerators(unittest.TestCase):

    def test_each_generator_is_the_unit_of_its_axis(self):
        check = ct.generator_check()
        self.assertTrue(check["all_unit_vectors"])
        self.assertEqual(len(check["generators"]), len(ct.AXES))
        for row in check["generators"]:
            with self.subTest(axis=row["axis"]):
                self.assertTrue(row["unit"])

    def test_there_are_twenty_moves_in_a_stated_order(self):
        self.assertEqual(len(ct.MOVES), 2 * len(ct.GENERATORS))
        self.assertEqual(len(set(ct.MOVES)), len(ct.MOVES))
        self.assertEqual([m.key for m in ct.MOVES],
                         sorted(m.key for m in ct.MOVES))

    def test_a_move_changes_one_exponent_by_one(self):
        for move in ct.MOVES:
            with self.subTest(move=str(move)):
                after = ct.apply_move(ct.ORIGIN, move)
                self.assertEqual(ct.l1(after), 1)
                self.assertEqual(after[move.axis], 1 if move.up else -1)


# ===========================================================================
# 2.  THE LEAN PROMISES, ON THE RUNNING LOOP
# ===========================================================================

class TestTheLeanPromisesHold(unittest.TestCase):

    def test_minimal_length_eq_l1(self):
        # `GLM.Controller.minimal_length_eq_l1`: the optimum the report scores
        # against is the L1 norm, and the exact heuristic attains it.
        for name in ct.task_targets():
            state, refusal = ct.classify_target(name)
            if state is None:
                continue
            outcome = ct.solve(name, "exponent")
            with self.subTest(target=name):
                self.assertEqual(outcome["optimum"], ct.l1(state))
                if outcome["answered"]:
                    self.assertGreaterEqual(outcome["length"], ct.l1(state))

    def test_exists_descent(self):
        # `GLM.Controller.exists_descent`: from any state but the target some
        # move strictly reduces the distance.
        target = tuple(ct.classify_target("energy")[0])
        state = ct.ORIGIN
        for _ in range(ct.l1(state, target)):
            best = min((ct.l1(ct.apply_move(state, m), target), m.key, m)
                       for m in ct.MOVES)
            self.assertEqual(best[0] + 1, ct.l1(state, target))
            state = ct.apply_move(state, best[2])
        self.assertEqual(state, target)

    def test_a_plan_replays_to_its_target(self):
        for name in ct.task_targets():
            state, refusal = ct.classify_target(name)
            if state is None:
                continue
            outcome = ct.solve(name, "exponent")
            if not outcome["answered"]:
                continue
            with self.subTest(target=name):
                self.assertTrue(outcome["reaches_target"])

    def test_an_invariant_makes_a_target_unreachable(self):
        # `GLM.Controller.unreachable_of_invariant`, in the three forms the
        # register actually presents.
        kinds = set()
        for name in ct.refused_targets():
            state, refusal = ct.classify_target(name)
            self.assertIsNone(state)
            self.assertEqual(refusal.kind, "invariant")
            kinds.add(refusal.reason.split(" is ")[0])
        self.assertGreaterEqual(len(kinds), 2)

    def test_no_move_changes_the_scale_or_the_rank(self):
        for name in ct.GENERATORS:
            quantity = do_physics.quantity_by_name(name)
            with self.subTest(generator=name):
                self.assertEqual(quantity.scale, 0)
                self.assertEqual(quantity.rank, 0)
                self.assertEqual((quantity.p, quantity.t, quantity.c),
                                 (0, 0, 0))


# ===========================================================================
# 3.  NOTHING IS TRUSTED BECAUSE THE LOOP SAID SO
# ===========================================================================

class TestEveryAnswerIsCheckedIndependently(unittest.TestCase):

    def test_the_verifier_confirms_every_plan(self):
        for heuristic in ct.HEURISTIC_ORDER:
            for name in ct.task_targets():
                outcome = ct.solve(name, heuristic)
                if not outcome.get("answered"):
                    continue
                with self.subTest(heuristic=heuristic, target=name):
                    verdict = vf.verify_expression_pair(
                        name, outcome["expression"], "scalar")
                    self.assertTrue(verdict.holds)

    def test_a_wrong_expression_is_rejected_by_the_same_instrument(self):
        # The check is a check: it fails on an expression that is one move out.
        verdict = vf.verify_expression_pair(
            "energy", "length * length * mass / time", "scalar")
        self.assertFalse(verdict.holds)

    def test_the_expression_is_the_plan(self):
        outcome = ct.solve("energy", "exponent")
        self.assertTrue(outcome["answered"])
        self.assertEqual(outcome["expression"],
                         ct.expression([ct.Move(axis=0, up=True),
                                        ct.Move(axis=0, up=True),
                                        ct.Move(axis=1, up=True),
                                        ct.Move(axis=2, up=False),
                                        ct.Move(axis=2, up=False)]))


# ===========================================================================
# 4.  REFUSALS
# ===========================================================================

class TestRefusals(unittest.TestCase):

    def test_an_unreachable_target_is_refused_without_searching(self):
        refused = ct.refused_targets()
        self.assertGreater(len(refused), 50)
        outcome = ct.solve(refused[0])
        self.assertFalse(outcome["answered"])
        self.assertEqual(outcome["refusal"]["kind"], "invariant")
        self.assertNotIn("proposals", outcome)

    def test_an_exhausted_beam_refuses_rather_than_guesses(self):
        outcome = ct.solve("energy", "none")
        self.assertFalse(outcome["answered"])
        self.assertEqual(outcome["refusal"]["kind"], "exhausted")
        self.assertNotIn("plan", outcome)

    def test_the_two_refusals_are_different_claims(self):
        invariant = ct.solve(ct.refused_targets()[0])["refusal"]
        exhausted = ct.solve("energy", "none")["refusal"]
        self.assertIn("invariant", invariant["certificate"])
        self.assertIn("incomplete", exhausted["certificate"])

    def test_every_register_quantity_is_classified(self):
        register = do_physics.load_physics_register()
        self.assertEqual(len(ct.reachable_targets())
                         + len(ct.refused_targets()), len(register))


# ===========================================================================
# 5.  THE EXPERIMENT AND ITS CONTROLS
# ===========================================================================

class TestTheMeasuredComparison(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = ct.controller_report()

    def test_the_address_table_is_the_one_this_task_set_needs(self):
        self.assertEqual(self.report["table"]["verdict"], "fresh")

    def test_the_exact_heuristic_solves_everything_minimally(self):
        row = self.report["heuristics"]["exponent"]
        self.assertEqual(row["solved"], self.report["reachable"])
        self.assertEqual(row["minimal"], row["solved"])

    def test_the_substrate_heuristic_beats_its_controls(self):
        rows = self.report["heuristics"]
        self.assertGreater(rows["address"]["solved"], rows["none"]["solved"])
        self.assertGreater(rows["address"]["solved"], rows["random"]["solved"])

    def test_the_substrate_heuristic_does_not_reach_the_exact_one(self):
        # The honest half: the lattice guides, and it does not guide as well as
        # counting the exponents does.
        rows = self.report["heuristics"]
        self.assertLess(rows["address"]["solved"], rows["exponent"]["solved"])

    def test_the_native_resolution_collapses_to_no_guidance(self):
        # `Address.lean`'s read-back bound predicts this: at scale 1 the
        # covering radius swamps the spacing between adjacent states.
        rows = self.report["heuristics"]
        self.assertEqual(rows["address_native"]["solved"],
                         rows["none"]["solved"])
        self.assertEqual(rows["address_native"]["mean_proposals"],
                         rows["none"]["mean_proposals"])

    def test_every_solved_task_was_verified(self):
        for heuristic, row in self.report["heuristics"].items():
            with self.subTest(heuristic=heuristic):
                self.assertEqual(row["verified"], row["solved"])
                self.assertTrue(row["all_answers_verified"])

    def test_the_rates_are_exact(self):
        for row in self.report["heuristics"].values():
            self.assertIsInstance(row["solve_rate"], Fraction)
            self.assertIsInstance(row["mean_proposals"], Fraction)

    def test_the_verdict_is_recomputed_from_the_table(self):
        rows = self.report["heuristics"]
        verdict = self.report["verdict"]
        self.assertEqual(verdict["address_beats_no_guidance"],
                         rows["address"]["solved"] > rows["none"]["solved"])
        self.assertEqual(verdict["address_matches_exact"],
                         rows["address"]["solved"] == rows["exponent"]["solved"])
        self.assertTrue(verdict["every_answer_is_verified"])

    def test_the_task_set_is_the_stated_stride(self):
        reachable = ct.reachable_targets()
        stride = max(1, len(reachable) // ct.TASK_COUNT)
        self.assertEqual(ct.task_targets()[:ct.TASK_COUNT],
                         tuple(reachable[::stride])[:ct.TASK_COUNT])

    def test_the_report_answers_from_the_stored_table(self):
        # The lattice heuristic costs about twenty milliseconds a node; the
        # table is why the report is seconds rather than minutes.  A miss would
        # be counted, and there should be none.
        self.assertEqual(self.report["decodes_this_process"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
