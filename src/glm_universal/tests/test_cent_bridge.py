"""Tests for ``glm_universal.cent_bridge`` -- the GLM asking the cent compiler.

*Created 14 November 2026 (platform round, cent compiler round 1).*

The compiler is a supplied system with its own gate, so these tests ask it for
real answers rather than mocking it: the bridge's whole job is that a question
reaches the compiler and its JSON comes back intact.  The one mocked case is
the compiler's absence, which cannot be produced in a checkout that holds it.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from glm_universal import cent_bridge as cb


class TestAvailability(unittest.TestCase):
    def test_the_compiler_is_in_this_checkout(self):
        self.assertTrue(cb.available(), f"looked in {cb.cent_directory()}")

    def test_a_missing_folder_says_so_rather_than_answering(self):
        with mock.patch.object(cb, "cent_directory", return_value=Path("/nonexistent/cent")):
            self.assertFalse(cb.available())
            with self.assertRaises(cb.CentUnavailable):
                cb.discover("compute a square root")


class TestDiscover(unittest.TestCase):
    def test_a_parseable_problem_comes_back_with_its_schema(self):
        payload = cb.discover("compute an irrational value with an analog method")
        self.assertEqual(payload["schema"], "cent-discovery/1")
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["matched"])
        self.assertIn("compute:irrational", payload["problem"]["goals"])

    def test_an_unmatched_problem_is_an_answer_not_an_error(self):
        payload = cb.discover("zzz qqq xyzzy")
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["matched"])

    def test_the_question_is_passed_as_an_argument_not_through_a_shell(self):
        payload = cb.discover("sum; echo not executed")
        self.assertEqual(payload["query"], "sum; echo not executed")


class TestOriginate(unittest.TestCase):
    def test_the_analogy_search_reviews_every_declared_analogy(self):
        payload = cb.originate()
        self.assertEqual(payload["schema"], "cent-origination-ledger/1")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["search_space"]["size"], len(payload["reviews"]))
        self.assertTrue(any(r.get("accepted") for r in payload["reviews"]))

    def test_a_refusal_carries_its_reason_rather_than_silence(self):
        payload = cb.originate()
        refused = [r for r in payload["reviews"] if not r.get("accepted")]
        for review in refused:
            self.assertTrue(review.get("reason"), review)

    def test_the_scale_search_originates_beyond_the_analogy_search(self):
        # The two searches carry their own ledger shapes: D8 reviews each
        # declared analogy, D9 reports families, originated interpretations
        # and its own scoreboard.
        analogies = cb.originate()
        scale = cb.originate(search="scale")
        self.assertEqual(scale["schema"], "cent-origination-ledger/2")
        self.assertTrue(scale["parity_ok"])
        accepted = sum(1 for r in analogies["reviews"] if r.get("accepted"))
        self.assertGreater(len(scale["originated"]), accepted)
        self.assertIn("scoreboard", scale)

    def test_the_ledger_states_what_it_did_not_establish(self):
        scale = cb.originate(search="scale")
        self.assertTrue(scale["gaps"], "a ledger with no gaps claims too much")

    def test_an_unknown_search_is_refused_before_it_is_run(self):
        with self.assertRaises(ValueError):
            cb.originate(search="everything")


class TestPropose(unittest.TestCase):
    def test_a_proposal_bundle_carries_a_handoff_per_proposal(self):
        payload = cb.propose("sqrt", target="glm-reference", top=1)
        self.assertEqual(payload["schema"], "cent-proposal-bundle/1")
        proposals = payload.get("proposals") or []
        self.assertTrue(proposals, "the compiler offered no proposal for sqrt")
        self.assertIn("handoff", proposals[0])

    def test_the_live_target_is_the_repository_glm(self):
        # The adapter resolves the enclosing repository's src/GLM.py, so the
        # live target is available wherever the delivery is unpacked.
        payload = cb.propose("sum", target="glm-live", top=5)
        live = [p for p in payload.get("proposals") or ()
                if (p.get("mechanism") or {}).get("id") == "kcl-conservation"]
        self.assertTrue(live, "no KCL conservation proposal for the live target")
        environment = live[0]["handoff"]["environment"]
        self.assertTrue(environment["available"], environment.get("detail"))



class TestTheToolsCommand(unittest.TestCase):
    """``python3 -m glm_universal.tools cent`` -- the developer-facing surface."""

    def test_the_command_parses_each_of_its_three_actions(self):
        from glm_universal import tools as tools_module
        parser = tools_module._parser()
        discover = parser.parse_args(["cent", "--discover", "a square root"])
        self.assertEqual(discover.handler, tools_module._cent)
        self.assertEqual(discover.discover, "a square root")
        propose = parser.parse_args(["cent", "--propose", "sqrt", "--top", "2"])
        self.assertEqual(propose.top, 2)
        self.assertEqual(propose.propose, "sqrt")
        originate = parser.parse_args(["cent", "--originate", "scale"])
        self.assertEqual(originate.originate, "scale")

    def test_one_action_is_required(self):
        from glm_universal import tools as tools_module
        with self.assertRaises(SystemExit):
            tools_module._parser().parse_args(["cent"])

    def test_the_handler_prints_the_methods_and_its_gaps(self):
        import contextlib
        import io
        from glm_universal import tools as tools_module
        args = tools_module._parser().parse_args(["cent", "--discover", "a square root"])
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            status = tools_module._cent(args)
        printed = buffer.getvalue()
        self.assertEqual(status, 0)
        self.assertIn("cent discover", printed)
        self.assertIn("declared method", printed)
        self.assertIn("gap", printed)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
