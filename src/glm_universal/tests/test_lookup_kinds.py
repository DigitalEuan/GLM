"""Tests for the four lookup kinds -- ``tool``, ``corpus``, ``study`` and
``sequence`` (:mod:`glm_universal.runtime.lookup_kinds`, parser rule 0,
:mod:`glm_universal.runtime.reports.lookup`,
:mod:`glm_universal.runtime.lookup_scripts`).

*Created 31 October 2026 (repository check).*

What is pinned:

* **The claim is narrow.**  No question of the evaluation set is claimed
  except the cases of the four kinds themselves, and no declared text of the
  router's census (engineering, cognition, Python) is claimed at all -- so
  adding the kinds moves no existing answer.  *What is the order of
  operations* is not a sequence question and falls through to the grammar.
* **The study kind answers from the manifests**, through the planner even
  where a frame would otherwise read the words (*what does
  FOLD_MACHINE_STUDY depend on*), refuses an unknown id with the reason, and
  its column 3 verifies.
* **The sequence kind answers from the wheels** -- a prefix (*identify the
  sequence 2 3 5 7 11*), a run (*what sequence is 1, 1, 2, 3, 5, 8*), a
  sporadic order written as an integer or as a product of prime powers, the
  reverse question -- refuses what no entry holds, and its column 3 verifies.
* **The tool kind** runs the toolbox through the session exactly as the
  router does.
* **No report subject is claimed** (*Last altered 31 October 2026
  (repository check): added after the full test run found*
  ``report external studies`` *and* ``report companion studies`` *claimed as*
  ``study``*; every alias the session's report dispatch names is read off
  its source and asked).*
"""
from __future__ import annotations

import unittest

from glm_universal.evaluation.cases import CASES
from glm_universal.runtime import lookup_kinds as lk
from glm_universal.runtime import router
from glm_universal.runtime import tct_engine as T
from glm_universal.runtime.parser import KINDS, parse_query
from glm_universal.runtime.session import GeometricSession

_SESSION = None


def _session() -> GeometricSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = GeometricSession()
    return _SESSION


def _verified(solution) -> bool:
    trace = T.verify_trace(T.build_trace(solution))
    verdict = trace.verdict
    return (verdict is not None and verdict.returncode == 0
            and verdict.matches_column2 and not verdict.missing_keys)


class TestTheKindsAreDeclared(unittest.TestCase):

    def test_the_four_kinds_are_parser_kinds(self):
        for kind in lk.LOOKUP_KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(KINDS.count(kind), 1)
        self.assertEqual(KINDS[-1], "unknown")

    def test_each_kind_has_a_solver_and_a_template(self):
        for kind in lk.LOOKUP_KINDS:
            with self.subTest(kind=kind):
                self.assertTrue(hasattr(GeometricSession, f"_solve_{kind}"))
                self.assertIn(kind, T.TEMPLATES)

    def test_rule_zero_carries_the_request_whole(self):
        q = parse_query("corpus address of seven")
        self.assertEqual((q.kind, q.rule), ("corpus", "lookup_claim"))
        self.assertEqual(q.options["request"], "address of seven")
        q = parse_query("tool majority 1 : 0, 2 : 1 :: 3")
        self.assertEqual(q.kind, "tool")
        self.assertEqual(q.options["request"], "tool majority 1 : 0, 2 : 1 :: 3")
        q = parse_query("what does FOLD_MACHINE_STUDY depend on")
        self.assertEqual(q.kind, "study")
        q = parse_query("which sporadic group has order 7920")
        self.assertEqual(q.kind, "sequence")


class TestTheClaimIsNarrow(unittest.TestCase):
    """Adding the kinds moves no existing answer."""

    def test_no_evaluation_question_of_another_kind_is_claimed(self):
        for case in CASES:
            claimed = lk.claimed_kind(case.question)
            with self.subTest(case=case.id):
                if case.kind in lk.LOOKUP_KINDS and case.kind != "tool":
                    self.assertEqual(claimed, case.kind)
                elif case.kind == "tool":
                    # tool-leech-norm-12 is English, read by the tool values
                    # after the planner refuses; it is not a `tool ...` text.
                    self.assertIsNone(claimed)
                else:
                    self.assertIsNone(claimed, case.question)

    def test_no_declared_text_of_the_census_is_claimed(self):
        for name, texts in router._declared_sets().items():
            if name == "contract":
                continue        # the evaluation set, checked above
            for text in texts:
                with self.subTest(set=name, text=text[:60]):
                    self.assertIsNone(lk.claimed_kind(text))

    def test_the_census_reads_every_evaluation_case_through_the_planner(self):
        census = router.reads_census()["contract"]
        self.assertEqual(census["planner"], len(CASES))

    def test_no_report_subject_is_claimed(self):
        import ast
        import inspect
        from glm_universal.runtime import session as S
        tree = ast.parse(inspect.getsource(S))
        subjects = set(getattr(S, "REPORT_SUBJECTS", ()))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Compare)
                    and isinstance(node.left, ast.Name)
                    and node.left.id == "subject"
                    and len(node.ops) == 1
                    and isinstance(node.ops[0], ast.In)
                    and isinstance(node.comparators[0], ast.Tuple)):
                for elt in node.comparators[0].elts:
                    if isinstance(elt, ast.Constant) and isinstance(
                            elt.value, str):
                        subjects.add(elt.value)
        self.assertIn("external studies", subjects)
        claimed = sorted(s for s in subjects
                         if lk.claimed_kind(f"report {s}") is not None)
        self.assertEqual(claimed, [])
        for text in ("report external studies", "report companion studies"):
            self.assertEqual(parse_query(text).kind, "report")

    def test_order_of_operations_falls_through(self):
        self.assertIsNone(lk.claimed_kind("what is the order of operations"))
        self.assertNotEqual(parse_query("what is the order of operations").kind,
                            "sequence")
        self.assertIsNone(lk.claimed_kind("order 5 to pressure"))
        self.assertIsNone(lk.claimed_kind("the order of magnitude of 1, 2, 3"))

    def test_the_study_forms(self):
        for text in ("study colour induction", "studies on the Golay code",
                     "which studies bear on the Golay code",
                     "study LEECH_SHELLS_STUDY",
                     "what does FOLD_MACHINE_STUDY depend on",
                     "which studies have a missing Lean file", "open studies"):
            with self.subTest(text=text):
                self.assertEqual(lk.claimed_kind(text), "study")
        for text in ("describe carbon", "the student studied hard",
                     "report pipeline", "FOLD_MACHINE_STUDYING"):
            with self.subTest(text=text):
                self.assertIsNone(lk.claimed_kind(text))


class TestTheStudyKind(unittest.TestCase):

    def test_a_card_is_answered_and_verifies(self):
        sol = _session().ask("study LEECH_SHELLS_STUDY")
        self.assertTrue(sol.ok, sol.answer)
        self.assertEqual(sol.kind, "study")
        self.assertIn("LEECH_SHELLS_STUDY (Phase 164)", sol.answer)
        self.assertEqual(sol.expected["named"].split(",")[0],
                         "LEECH_SHELLS_STUDY")
        self.assertTrue(_verified(sol))

    def test_a_dependency_question_reaches_the_study_kind(self):
        text = "what does FOLD_MACHINE_STUDY depend on"
        self.assertEqual(router.reader_of(text), "planner")
        routed = router.route(_session(), text)
        self.assertTrue(routed.answered, routed.text)
        self.assertIn("FOLD_MACHINE_STUDY builds on", routed.text)
        self.assertTrue(_verified(routed.solution))

    def test_an_unknown_study_is_refused_with_the_reason(self):
        sol = _session().ask("study zzqx")
        self.assertFalse(sol.ok)
        self.assertIn("NOTHING_IN_THE_MANIFESTS", sol.answer)
        self.assertIn("zzqx", sol.answer)


class TestTheSequenceKind(unittest.TestCase):

    def test_a_prefix_is_spoken(self):
        sol = _session().ask("identify the sequence 2 3 5 7 11")
        self.assertTrue(sol.ok, sol.answer)
        self.assertEqual(sol.expected["id"], "A000040")
        self.assertEqual(sol.expected["position"], "0")
        self.assertTrue(_verified(sol))

    def test_a_run_is_located(self):
        sol = _session().ask("what sequence is 1, 1, 2, 3, 5, 8")
        self.assertTrue(sol.ok, sol.answer)
        self.assertEqual((sol.expected["id"], sol.expected["position"]),
                         ("A000045", "1"))
        self.assertTrue(_verified(sol))

    def test_a_sporadic_order_both_ways(self):
        for text in ("which sporadic group has order 7920",
                     "which sporadic group has order 2^4 * 3^2 * 5 * 11"):
            with self.subTest(text=text):
                sol = _session().ask(text)
                self.assertTrue(sol.ok, sol.answer)
                self.assertEqual(sol.expected, {"group": "M11",
                                                "order": "7920"})
                self.assertTrue(_verified(sol))
        sol = _session().ask("what is the order of the Monster group")
        self.assertTrue(sol.ok, sol.answer)
        self.assertEqual(sol.expected["group"], "M")
        self.assertEqual(sol.expected["order"],
                         "808017424794512875886459904961710757005754368000000000")
        self.assertTrue(_verified(sol))

    def test_what_no_entry_holds_is_refused(self):
        sol = _session().ask("what sequence is 9, 17, 4, 1000, 3")
        self.assertFalse(sol.ok)
        self.assertIn("NOT_ON_THE_WHEEL", sol.answer)
        self.assertIn("nothing is guessed", sol.answer)
        sol = _session().ask("which sporadic group has order 7921")
        self.assertFalse(sol.ok)
        self.assertIn("No sporadic simple group has order 7921", sol.answer)


class TestTheToolKind(unittest.TestCase):

    def test_the_session_runs_the_toolbox_as_the_router_does(self):
        sol = _session().ask("tools")
        self.assertTrue(sol.ok)
        self.assertEqual(sol.kind, "tool")
        self.assertEqual(sol.answer, router.route(_session(), "tools").text)
        self.assertTrue(_verified(sol))

    def test_an_unknown_tool_is_refused(self):
        sol = _session().ask("tool nosuch")
        self.assertFalse(sol.ok)
        self.assertIn("no tool named 'nosuch'", sol.answer)


if __name__ == "__main__":
    unittest.main()
