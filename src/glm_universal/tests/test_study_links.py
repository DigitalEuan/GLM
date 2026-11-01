"""Tests for ``glm_universal.corpus.study_links`` -- the study documents'
links checked against the tree and repointed after a move.

*Created 31 October 2026 (repository check of the YAML study system).  Last
altered 31 October 2026 (repository check): tests for ``--scope all``, for
documents under ``src/`` that climb one level short, for package documents
placed inside their package and for never-supplied package files.*
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from glm_universal import constants as C
from glm_universal.corpus import study_links as sl

DOC = C.STUDIES_DIR / "SOME_STUDY.md"       # repair_target reads only its place


def _first(paths):
    for path in sorted(paths):
        return path
    return None


class TestRepairRules(unittest.TestCase):

    def test_an_existing_target_is_kept(self):
        self.assertEqual(sl.repair_target(DOC, "../ENTRY.md"), "../ENTRY.md")

    def test_the_package_moved_under_src(self):
        self.assertEqual(
            sl.repair_target(DOC, "../glm_universal/constants.py"),
            "../src/glm_universal/constants.py")
        # the fragment survives the move
        self.assertEqual(
            sl.repair_target(DOC, "../glm_universal/constants.py#L1"),
            "../src/glm_universal/constants.py#L1")

    def test_the_lean_tree_moved_under_src(self):
        lean = _first(C.LEAN_GLM_DIR.glob("*.lean"))
        if lean is None:
            self.skipTest("no Lean file in the build tree")
        rel = lean.relative_to(C.LEAN_ROOT).as_posix()
        self.assertEqual(sl.repair_target(DOC, "../glm_lean/" + rel),
                         "../src/lean/" + rel)

    def test_a_supplied_item_is_followed_into_done_or_todo(self):
        for base in (C.SOURCE_DONE_DIR, C.SOURCE_TODO_DIR):
            item = _first(p for p in base.iterdir()
                          if p.is_file() and " " not in p.name) \
                if base.is_dir() else None
            if item is None:
                continue
            want = "../" + item.relative_to(C.REPOSITORY_ROOT).as_posix()
            self.assertEqual(
                sl.repair_target(DOC, "../source_material/" + item.name), want)
            other = "ToDo" if base == C.SOURCE_DONE_DIR else "done"
            self.assertEqual(
                sl.repair_target(DOC, f"../source_material/{other}/"
                                      + item.name), want)

    def test_a_spaced_name_keeps_its_percent_spelling(self):
        item = _first(p for base in (C.SOURCE_DONE_DIR, C.SOURCE_TODO_DIR)
                      if base.is_dir() for p in base.iterdir()
                      if p.is_file() and " " in p.name)
        if item is None:
            self.skipTest("no supplied file with a space in its name")
        got = sl.repair_target(
            DOC, "../source_material/" + item.name.replace(" ", "%20"))
        self.assertIsNotNone(got)
        self.assertNotIn(" ", got)
        self.assertIn("%20", got)

    def test_a_package_readme_links_into_the_lean_tree(self):
        audit = C.LEAN_GLM_DIR / "Rule30" / "AUDIT.md"
        if not audit.is_file():
            self.skipTest("Rule30/AUDIT.md not in the tree")
        doc = C.STUDIES_DIR / "RULE30_STUDY.md"
        self.assertEqual(
            sl.repair_target(doc, "RequestProject/GLM/Rule30/AUDIT.md"),
            "../src/lean/RequestProject/GLM/Rule30/AUDIT.md")
        # the same link from an ordinary study is not guessed at
        self.assertIsNone(
            sl.repair_target(DOC, "RequestProject/GLM/Rule30/AUDIT.md"))

    def test_nothing_is_invented(self):
        self.assertIsNone(sl.repair_target(DOC, "../nowhere/NO_SUCH_FILE.md"))
        self.assertIsNone(sl.repair_target(DOC, "../glm_universal/no_such.py"))

    def test_a_recorded_missing_lean_file_is_not_broken(self):
        registry = sl._lean_registry()
        if not registry:
            self.skipTest("no Lean file recorded missing")
        name = registry[0]
        lean_rel = C.LEAN_GLM_DIR.relative_to(C.REPOSITORY_ROOT).as_posix()
        if (C.LEAN_GLM_DIR / name).exists():
            self.skipTest("the recorded file has come back")
        self.assertEqual(sl._recorded(f"{lean_rel}/{name}"), "lean-missing")
        self.assertEqual(
            sl.repair_target(DOC, "../glm_lean/RequestProject/GLM/" + name),
            f"../{lean_rel}/{name}")
        self.assertEqual(sl._recorded(f"{lean_rel}/NoSuchFile.lean"), "")


class TestDocumentsUnderSrc(unittest.TestCase):
    """The package and the Lean tree moved one level down, so a link written
    one level higher than it now needs is read from the repository root."""

    def setUp(self):
        if (C.REPOSITORY_ROOT / "src" / "README.md").exists():
            self.skipTest("src/README.md exists, so nothing climbs short")

    def test_a_package_readme_reaches_the_root_readme(self):
        if not (C.REPOSITORY_ROOT / "README.md").is_file():
            self.skipTest("no root README.md")
        doc = C.PACKAGE_ROOT / "reasoning" / "README.md"
        self.assertEqual(sl.repair_target(doc, "../../README.md"),
                         "../../../README.md")
        top = C.PACKAGE_ROOT / "README.md"
        self.assertEqual(sl.repair_target(top, "../README.md#tier-0"),
                         "../../README.md#tier-0")
        # a link that is right already is kept
        self.assertEqual(sl.repair_target(doc, "../README.md"),
                         "../README.md")

    def test_only_documents_under_src_are_read_so(self):
        doc = C.STUDIES_DIR / "SOME_STUDY.md"
        self.assertIsNone(sl.repair_target(doc, "../src/README.md"))

    def test_a_short_link_into_the_old_lean_tree(self):
        lean = _first(C.LEAN_GLM_DIR.glob("*.lean"))
        if lean is None:
            self.skipTest("no Lean file in the build tree")
        rel = lean.relative_to(C.LEAN_ROOT).as_posix()
        doc = C.PACKAGE_ROOT / "corpus" / "README.md"
        self.assertEqual(sl.repair_target(doc, "../../glm_lean/" + rel),
                         "../../lean/" + rel)


class TestPackageDocuments(unittest.TestCase):
    """A copied package README links relative to its place in the package;
    a file the package never held is dropped as a link, not invented."""

    RULE30_README = (C.LEAN_GLM_DIR / "Rule30" / "README.md")

    def test_the_registry_is_well_formed(self):
        for doc, (package, place) in sl.PACKAGE_DOCUMENTS.items():
            self.assertTrue((C.REPOSITORY_ROOT / doc).is_file(), doc)
            self.assertIn(package, sl.NOT_SUPPLIED)
            self.assertFalse(place.startswith(("/", "..")))
        for package, names in sl.NOT_SUPPLIED.items():
            root = C.source_material_item(package)
            for name in names:
                self.assertFalse((root / name).exists(), name)
                if name.startswith(C.LEAN_LIBRARY + "/"):
                    self.assertFalse((C.LEAN_ROOT / name).exists(), name)

    def test_a_never_supplied_file_is_recognised_from_either_place(self):
        study = C.STUDIES_DIR / "RULE30_STUDY.md"
        self.assertTrue(sl._not_supplied(study, "MERGE_INTO_GLM.md"))
        self.assertTrue(sl._not_supplied(self.RULE30_README,
                                         "../../../MERGE_INTO_GLM.md"))
        self.assertTrue(sl._not_supplied(self.RULE30_README, "DEVELOPMENT.md"))
        self.assertIsNone(sl.repair_target(self.RULE30_README,
                                           "../../../MERGE_INTO_GLM.md"))
        # not a package document: no such reading
        self.assertFalse(sl._not_supplied(C.STUDIES_DIR / "SOME_STUDY.md",
                                          "MERGE_INTO_GLM.md"))

    def test_the_lean_readme_links_inside_the_lean_tree(self):
        audit = C.LEAN_GLM_DIR / "Rule30" / "AUDIT.md"
        if not audit.is_file():
            self.skipTest("Rule30/AUDIT.md not in the tree")
        self.assertEqual(sl.repair_target(self.RULE30_README, "AUDIT.md"),
                         "AUDIT.md")

    def test_rewrite_drops_the_link_and_keeps_the_text(self):
        text = ("the gates are in [`MERGE_INTO_GLM.md`](../../../MERGE_INTO_GLM.md)"
                ". See [`AUDIT.md`](AUDIT.md) and [`old`](../glm_universal/x.py).\n")
        links = [
            sl.Link("R.md", 1, "../../../MERGE_INTO_GLM.md", None,
                    sl.NOT_SUPPLIED_RECORD),
            sl.Link("R.md", 1, "../glm_universal/x.py",
                    "../src/glm_universal/x.py"),
            sl.Link("R.md", 1, "gone.md", None),            # unresolved: kept
        ]
        new, pairs = sl.rewrite_text(text, links)
        self.assertEqual(new, "the gates are in `MERGE_INTO_GLM.md`. See "
                              "[`AUDIT.md`](AUDIT.md) and "
                              "[`old`](../src/glm_universal/x.py).\n")
        self.assertEqual(pairs, [("../../../MERGE_INTO_GLM.md", ""),
                                 ("../glm_universal/x.py",
                                  "../src/glm_universal/x.py")])


class TestScopes(unittest.TestCase):

    def test_the_all_scope_is_the_inventory_less_the_generated(self):
        from glm_universal.corpus import inventory as inv
        docs = {sl._repo_path(p) for p in sl.scope_documents("all")}
        self.assertIn("ENTRY.md", docs)
        self.assertIn("studies/RULE30_STUDY.md", docs)
        self.assertIn("src/glm_universal/README.md", docs)
        self.assertTrue(any(d.startswith("archive/") for d in docs))
        self.assertTrue(any(d.startswith("src/lean/") for d in docs))
        for generated in inv.generated_paths():
            self.assertNotIn(generated, docs)
        self.assertFalse(any(d.startswith("source_material/") for d in docs))
        studies = {p.name for p in sl.scope_documents("studies")}
        self.assertEqual(studies, {p.name for p in C.STUDIES_DIR.glob("*.md")})
        with self.assertRaises(ValueError):
            sl.scope_documents("everything")

    def test_the_all_report_names_documents_by_repository_path(self):
        report = sl.links_report(scope="all")
        self.assertEqual(report["scope"], "all")
        for doc, _line, _target in report["unresolved"] + report["not_supplied"]:
            self.assertTrue((C.REPOSITORY_ROOT / doc).is_file(), doc)

    def test_cli_scope(self):
        self.assertEqual(sl.main(["--scope", "nowhere"]), 2)


class TestOnAScratchFolder(unittest.TestCase):
    """Outside the repository no rule applies, so the fix touches nothing."""

    def test_report_and_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PRESENT.md").write_text("# here\n", encoding="utf-8")
            text = ("# A\n\nSee [`present`](PRESENT.md), [`gone`](GONE.md) "
                    "and [the web](https://example.org/x.md), "
                    "[a section](#tier-0).\n")
            (root / "A_STUDY.md").write_text(text, encoding="utf-8")
            report = sl.links_report(root)
            self.assertEqual(report["documents"], 2)
            self.assertEqual(report["links"], 2)      # web and anchor skipped
            self.assertEqual(report["broken"], 1)
            self.assertEqual(report["unresolved"], [("A_STUDY.md", 3, "GONE.md")])
            self.assertEqual(report["to_documents"],
                             [("A_STUDY.md", 3, "GONE.md")])
            self.assertFalse(report["holds"])
            self.assertEqual(sl.fix_links(root), {})
            self.assertEqual((root / "A_STUDY.md").read_text(encoding="utf-8"),
                             text)


class TestTheRepository(unittest.TestCase):

    def test_no_study_links_to_a_missing_file(self):
        report = sl.links_report()
        self.assertEqual([], report["unresolved"])
        self.assertEqual([], report["to_documents"])
        self.assertTrue(report["holds"], report)

    def test_cli(self):
        self.assertEqual(sl.main([]), 0)


if __name__ == "__main__":
    unittest.main()
