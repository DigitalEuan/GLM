"""Tests for ``PROJECT_DIRECTIVES.md`` and :mod:`glm_universal.reasoning.directives`.

A directive nobody can check is a wish.  The document therefore names, for each
rule, an instrument that would fail if the rule were broken, and the module
reads the document rather than paraphrasing it.  These tests check both halves:

* the reader really reads -- a table row with no section, a section with no
  row, or an instrument that does not resolve is reported as a defect;
* the document as it stands has no defects, every instrument resolves, and
  every rule is explained rather than merely asserted;
* the rules that can be checked directly are checked here: the core computes
  no digests (D3), the reasoning package constructs no floats (D7), and every
  study document named by the pipeline registry exists (D5).

This file is named ``test_project_directives`` because ``test_directive.py``
already exists and is about a different document.
"""

from __future__ import annotations

import ast
import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import directives as drc
from glm_universal.reasoning import pipeline as ppl


DOCUMENT = drc.document_path()


class TestDocument(unittest.TestCase):

    def test_the_document_is_where_the_reader_looks(self):
        self.assertIsNotNone(DOCUMENT)
        self.assertEqual(DOCUMENT.name, "PROJECT_DIRECTIVES.md")

    def test_every_row_has_a_section_and_every_section_a_row(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        rows = {m.group(1) for m in
                (drc._ROW.match(line) for line in text.splitlines()) if m}
        headings = {m.group(1) for m in
                    (drc._HEADING.match(line) for line in text.splitlines())
                    if m}
        self.assertEqual(rows, headings)

    def test_the_directives_are_numbered_from_one_without_gaps(self):
        keys = [d.key for d in drc.parse_document()]
        self.assertEqual(keys, [f"D{i}" for i in range(1, len(keys) + 1)])

    def test_each_directive_is_explained_and_not_merely_stated(self):
        for directive in drc.parse_document():
            self.assertTrue(directive.heading, directive.key)
            self.assertGreaterEqual(directive.body_words, 40, directive.key)

    def test_each_directive_names_at_least_one_instrument(self):
        for directive in drc.parse_document():
            self.assertTrue(directive.instruments, directive.key)


class TestReader(unittest.TestCase):
    """The parser is a reader of the document, not a copy of it."""

    SAMPLE = """
# Rules

| id | rule | instrument |
|----|------|------------|
| D1 | Always do the thing. | `glm_universal.reasoning.pipeline` |
| D2 | Never do the other thing. | `no_such_module.py` |

## D1 — always do the thing

""" + ("word " * 50) + """

## D2 — never do the other thing

Too short.
"""

    def setUp(self):
        self.parsed = drc.parse_document(self.SAMPLE)

    def test_rows_and_sections_are_paired_by_key(self):
        self.assertEqual([d.key for d in self.parsed], ["D1", "D2"])
        self.assertEqual(self.parsed[0].heading, "always do the thing")

    def test_the_instrument_cell_is_read_as_code_spans(self):
        self.assertEqual(self.parsed[0].instruments,
                         ("glm_universal.reasoning.pipeline",))

    def test_an_instrument_that_exists_resolves(self):
        state = drc.instrument_state(self.parsed[0])
        self.assertTrue(state["all_resolved"])
        self.assertEqual(state["unresolved"], ())

    def test_an_instrument_that_does_not_exist_is_unresolved(self):
        state = drc.instrument_state(self.parsed[1])
        self.assertFalse(state["all_resolved"])
        self.assertEqual(state["unresolved"], ("no_such_module.py",))

    def test_a_report_subject_resolves_only_if_it_dispatches(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        self.assertTrue(drc._resolves("report pipeline"))
        self.assertFalse(drc._resolves("report nothing_like_this"))
        self.assertIn("pipeline", REPORT_SUBJECTS)

    def test_a_document_resolves_by_name(self):
        self.assertTrue(drc._resolves("PROJECT_DIRECTIVES.md"))
        self.assertFalse(drc._resolves("NEVER_WRITTEN.md"))

    def test_body_words_measure_the_section_not_the_table(self):
        self.assertGreaterEqual(self.parsed[0].body_words, 50)
        self.assertLess(self.parsed[1].body_words, 40)


class TestReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = drc.directives_report()

    def test_every_directive_is_reported(self):
        self.assertEqual(self.report["count"], len(drc.parse_document()))
        self.assertGreaterEqual(self.report["count"], 8)

    def test_the_document_has_no_defects(self):
        self.assertEqual(self.report["defects"], ())
        self.assertTrue(self.report["sound"])

    def test_every_instrument_of_every_directive_resolves(self):
        self.assertEqual(self.report["instrumented"], self.report["count"])
        self.assertEqual(self.report["instrumented_rate"], Fraction(1))

    def test_the_rate_is_an_exact_rational(self):
        self.assertIsInstance(self.report["instrumented_rate"], Fraction)


class TestTheRulesThemselves(unittest.TestCase):
    """Where a directive can be checked directly, check it."""

    def test_d3_the_core_computes_no_digests(self):
        # A digest addresses integrity, never meaning, so hashing lives in
        # ``glm_universal.integrity`` and the core does not import it.
        core = ("substrate", "data_objects", "reasoning", "semantics",
                "runtime", "migration")
        root = Path(drc.PACKAGE_ROOT)
        offenders = []
        for package in core:
            for path in sorted((root / package).rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [a.name.split(".")[0] for a in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0:
                        names = [(node.module or "").split(".")[0]]
                    else:
                        continue
                    if "hashlib" in names:
                        offenders.append(f"{package}/{path.name}")
        self.assertEqual(offenders, [])

    def test_d7_the_reasoning_package_constructs_no_floats(self):
        root = Path(drc.PACKAGE_ROOT) / "reasoning"
        offenders = []
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value,
                                                                 float):
                    offenders.append(f"{path.name}:{node.lineno}")
        self.assertEqual(offenders, [])

    def test_d5_every_document_the_registry_names_exists(self):
        for row in ppl.REGISTRY:
            self.assertIsNotNone(ppl.document_path(row.document), row.key)

    def test_d1_the_directives_document_is_itself_a_study(self):
        self.assertGreaterEqual(DOCUMENT.stat().st_size, ppl.STUB_BYTES)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
