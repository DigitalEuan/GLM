"""Tests for :mod:`glm_universal.reasoning.pipeline`.

The pipeline board says how far each piece of work has got, from *studied* to
*verified*.  Its whole value is that it cannot flatter: only the registry --
which document, modules, subject and Lean files belong together -- is declared,
and every stage is read off the tree at call time.  These tests hold that line:

* each stage is decided by evidence the test can also see for itself;
* a stage cannot be reached by declaring it (a missing document, a stub
  document, an unwired subject and a missing template each block their stage);
* the coverage index is computed with :mod:`ast`, so asking the board what is
  tested never runs, or even imports, a test;
* the board's own row is in the registry, which is what stops the instrument
  from escaping the discipline it measures.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import pipeline as ppl


class TestRegistry(unittest.TestCase):

    def test_the_registry_is_a_set_of_named_rows(self):
        keys = [row.key for row in ppl.REGISTRY]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertGreaterEqual(len(keys), 14)

    def test_every_row_names_a_document_and_at_least_one_module(self):
        for row in ppl.REGISTRY:
            self.assertTrue(row.document.endswith(".md"), row.key)
            self.assertTrue(row.modules, row.key)

    def test_the_instruments_of_this_round_are_rows_themselves(self):
        keys = {row.key for row in ppl.REGISTRY}
        for key in ("higher-lattices", "shell-sigma", "lean-address",
                    "directives", "pipeline"):
            self.assertIn(key, keys)

    def test_a_row_that_expects_no_lean_file_names_none(self):
        for row in ppl.REGISTRY:
            if not row.lean_expected:
                self.assertEqual(row.lean, (), row.key)

    def test_every_declared_module_exists(self):
        # The registry is the one declared thing, so a typo in it must show up
        # as a missing module rather than as a quietly incomplete row.
        for row in ppl.REGISTRY:
            for module in row.modules:
                self.assertIsNotNone(ppl.module_path(module),
                                     f"{row.key}: {module}")


class TestStages(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = ppl.pipeline_report()
        cls.rows = {r["key"]: r for r in cls.report["rows"]}

    def test_the_six_stages_are_in_order(self):
        self.assertEqual(ppl.STAGES,
                         ("studied", "implemented", "wired", "tested",
                          "formalised", "verified"))

    def test_studied_means_a_document_that_is_not_a_stub(self):
        for row in self.report["rows"]:
            document = ppl.document_path(row["document"])
            expected = bool(document) and row["document_bytes"] >= ppl.STUB_BYTES
            self.assertEqual(row["stages"]["studied"], expected, row["key"])

    def test_a_stub_document_does_not_count_as_a_study(self):
        self.assertGreater(ppl.STUB_BYTES, 0)
        for row in self.report["rows"]:
            if row["stages"]["studied"]:
                self.assertGreaterEqual(row["document_bytes"], ppl.STUB_BYTES)

    def test_implemented_means_every_module_is_on_disk(self):
        for row in self.report["rows"]:
            self.assertEqual(row["stages"]["implemented"],
                             all(row["modules"].values()), row["key"])

    def test_wired_means_the_subject_dispatches(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        for row in self.report["rows"]:
            self.assertEqual(row["stages"]["wired"],
                             row["subject"] in REPORT_SUBJECTS, row["key"])

    def test_tested_means_a_test_file_imports_one_of_the_modules(self):
        for row in self.report["rows"]:
            self.assertEqual(row["stages"]["tested"], bool(row["tests"]),
                             row["key"])
            for name in row["tests"]:
                self.assertTrue((ppl.TESTS_DIR / name).is_file())

    def test_formalised_means_every_named_lean_file_is_there(self):
        for row in self.report["rows"]:
            if row["lean_expected"]:
                self.assertEqual(row["stages"]["formalised"],
                                 bool(row["lean"]) and all(row["lean"].values()),
                                 row["key"])

    def test_verified_means_a_column_three_template_exists(self):
        from glm_universal.runtime.tct_engine import TEMPLATES
        for row in self.report["rows"]:
            self.assertEqual(row["stages"]["verified"],
                             row["template"] in TEMPLATES, row["key"])

    def test_first_missing_is_the_earliest_unreached_stage(self):
        for row in self.report["rows"]:
            missing = [s for s in ppl.STAGES if not row["stages"][s]]
            self.assertEqual(row["first_missing"],
                             missing[0] if missing else None, row["key"])
            self.assertEqual(row["complete"], not missing, row["key"])


class TestCoverageIndex(unittest.TestCase):

    def test_the_index_is_read_and_not_run(self):
        index = ppl.test_index()
        self.assertIn("glm_universal.reasoning", index)
        for key in index:
            self.assertTrue(key.startswith("glm_universal"))

    def test_this_file_covers_the_pipeline_module(self):
        self.assertIn("test_pipeline.py",
                      ppl.tests_covering("reasoning/pipeline.py"))

    def test_a_module_nothing_imports_is_reported_as_uncovered(self):
        self.assertEqual(ppl.tests_covering("reasoning/no_such_module.py"), ())

    def test_test_methods_are_counted_from_the_source(self):
        counted = ppl.count_tests("test_pipeline.py")
        source = (ppl.TESTS_DIR / "test_pipeline.py").read_text(encoding="utf-8")
        written = sum(1 for line in source.splitlines()
                      if line.strip().startswith("def test_"))
        self.assertEqual(counted, written)

    def test_counting_a_file_that_is_not_there_is_zero(self):
        self.assertEqual(ppl.count_tests("test_not_a_file.py"), 0)


class TestBoard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = ppl.pipeline_report()

    def test_the_board_covers_the_whole_registry(self):
        self.assertEqual(self.report["count"], len(ppl.REGISTRY))
        self.assertEqual(len(self.report["rows"]), len(ppl.REGISTRY))

    def test_the_completion_rate_is_an_exact_rational(self):
        rate = self.report["complete_rate"]
        self.assertIsInstance(rate, Fraction)
        self.assertEqual(rate, Fraction(self.report["complete"],
                                        self.report["count"]))

    def test_incomplete_rows_are_named_not_merely_counted(self):
        self.assertEqual(len(self.report["incomplete"]),
                         self.report["count"] - self.report["complete"])
        for key in self.report["incomplete"]:
            self.assertIn(key, {r.key for r in ppl.REGISTRY})

    def test_every_incomplete_row_appears_under_the_stage_it_is_blocked_at(self):
        blocked = {key for keys in self.report["blocked_at"].values()
                   for key in keys}
        self.assertEqual(blocked, set(self.report["incomplete"]))

    def test_the_stage_tallies_match_the_rows(self):
        for stage in ppl.STAGES:
            expected = sum(1 for r in self.report["rows"] if r["stages"][stage])
            self.assertEqual(self.report["by_stage"][stage], expected)

    def test_the_verification_commands_are_offered_for_wired_subjects(self):
        commands = self.report["verify_commands"]
        wired = [r for r in self.report["rows"] if r["stages"]["wired"]]
        self.assertEqual(len(commands), len(wired))
        for row in wired:
            self.assertTrue(any(f'report {row["subject"]}' in c
                                for c in commands), row["key"])
        for command in commands:
            self.assertIn("--verify-tct", command)

    def test_the_test_total_is_the_sum_of_the_rows(self):
        self.assertEqual(
            self.report["total_tests"],
            sum(r["test_count"] for r in self.report["rows"]))
        self.assertGreater(self.report["total_tests"], 100)


class TestTheBoardMeasuresItself(unittest.TestCase):
    """The instrument is inside the discipline it reports on."""

    @classmethod
    def setUpClass(cls):
        cls.rows = {r["key"]: r for r in ppl.pipeline_report()["rows"]}

    def test_the_pipeline_row_is_implemented_wired_and_tested(self):
        row = self.rows["pipeline"]
        self.assertTrue(row["stages"]["implemented"])
        self.assertTrue(row["stages"]["wired"])
        self.assertIn("test_pipeline.py", row["tests"])

    def test_the_directives_row_is_tested_too(self):
        self.assertTrue(self.rows["directives"]["stages"]["tested"])

    def test_a_row_cannot_claim_a_document_it_does_not_have(self):
        missing = ppl.Row("invented", "a row for something not written",
                          "NO_SUCH_STUDY.md", ("reasoning/pipeline.py",),
                          None, ())
        report = ppl.stage_report(missing)
        self.assertFalse(report["stages"]["studied"])
        self.assertFalse(report["stages"]["wired"])
        self.assertFalse(report["stages"]["verified"])
        self.assertEqual(report["first_missing"], "studied")

    def test_a_row_with_a_missing_module_is_not_implemented(self):
        broken = ppl.Row("broken", "a row naming a module that is not there",
                         "PROJECT_DIRECTIVES.md",
                         ("reasoning/not_written_yet.py",), "pipeline", ())
        report = ppl.stage_report(broken)
        self.assertFalse(report["stages"]["implemented"])
        self.assertFalse(report["stages"]["tested"])

    def test_a_row_with_a_missing_lean_file_is_not_formalised(self):
        broken = ppl.Row("unformalised", "a row naming a Lean file not written",
                         "PROJECT_DIRECTIVES.md", ("reasoning/pipeline.py",),
                         "pipeline", ("NotWritten.lean",))
        self.assertFalse(ppl.stage_report(broken)["stages"]["formalised"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
