"""Tests for the cent route -- a computational-method question answered by the
compiler (14 November 2026).

Three properties matter and each is tested directly:

* a question that asks for a method comes back with the compiler's declared
  methods and its ranked proposals;
* a question that does not ask for one routes exactly as it did before the
  route existed -- the non-interference rule every routing pass in this package
  is held to;
* when the compiler is not in the checkout, the question refuses as it did
  before rather than raising.
"""
from __future__ import annotations

import unittest
from unittest import mock

from glm_universal import cent_bridge as cb
from glm_universal.runtime import router as rt
from glm_universal.runtime.session import GeometricSession


def _session() -> GeometricSession:
    return GeometricSession()


class TestTheRoute(unittest.TestCase):
    def test_a_method_question_comes_back_with_the_compilers_proposals(self):
        routed = rt._cent_methods(
            "which physical method could compute the square root of five")
        self.assertIsNotNone(routed)
        self.assertEqual(routed.surface, "cent")
        self.assertTrue(routed.answered)
        self.assertEqual(routed.faculty, "propose")
        self.assertIn("declares", routed.text)
        self.assertIn("ranked proposals for sqrt", routed.text)
        self.assertIn("gap:", routed.text)

    def test_a_question_without_the_asking_words_is_not_the_compilers(self):
        for text in ("how do I add two numbers",
                     "what is 12/8",
                     "compute the square root of five"):
            self.assertIsNone(rt._cent_methods(text), text)

    def test_the_answer_says_which_system_spoke(self):
        solution = _session().ask(
            "which physical method could compute the square root of five")
        self.assertTrue(solution.ok)
        self.assertEqual(solution.payload.get("surface"), "cent")
        self.assertEqual(solution.kind, "routed-cent")
        self.assertIn("cent compiler", solution.answer)

    def test_an_ordinary_question_is_answered_by_the_ordinary_path(self):
        solution = _session().ask("what is the gcd of 12 and 18")
        self.assertNotEqual(solution.payload.get("surface"), "cent")


class TestNonInterference(unittest.TestCase):
    """The route may only turn a refusal into an answer, never the reverse."""

    def test_a_refusal_stays_a_refusal_when_the_compiler_is_absent(self):
        with mock.patch.object(cb, "available", return_value=False):
            solution = _session().ask(
                "which physical method could compute the square root of five")
        self.assertFalse(solution.ok)
        self.assertFalse(solution.payload.get("surface") == "cent")

    def test_a_refusal_that_is_not_a_method_question_is_untouched(self):
        before = _session().ask("which fred is the tallest")
        with mock.patch.object(cb, "discover", side_effect=AssertionError("asked")):
            after = _session().ask("which fred is the tallest")
        self.assertEqual(before.ok, after.ok)
        self.assertEqual(before.answer, after.answer)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
