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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
