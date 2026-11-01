"""Tests for ``glm_universal.corpus.study_manifest`` -- the study manifests
derived from their .md and the tree.

*Created 31 October 2026 (repository check of the YAML study system).*
*Last altered 31 October 2026 (the same check, later): every study document
the repository cites exists (the seven lost in the October 2026 reorganisation
were reconstructed), and every reconstructed study says so.  Also: a
``hand_fields`` name covers its sub-fields (``marks``); a name a package's
``__init__.py`` defines is not a missing module.*
"""
from __future__ import annotations

import unittest
from collections import Counter

try:
    import yaml as _yaml
except ImportError:  # pragma: no cover
    _yaml = None

from glm_universal import constants as C
from glm_universal.corpus import study_manifest as sm


def _tree(**overrides) -> sm.Tree:
    """A small hand-made tree for the file-reference tests."""
    base = dict(
        modules={"reasoning/leech_shells.py", "reasoning/tool_machine.py",
                 "runtime/toolbox.py", "tools.py", "corpus/checks.py"},
        module_stems={"leech_shells": ["reasoning/leech_shells.py"],
                      "tool_machine": ["reasoning/tool_machine.py"],
                      "toolbox": ["runtime/toolbox.py"],
                      "tools": ["tools.py"], "checks": ["corpus/checks.py"]},
        subpackages={"reasoning", "runtime", "corpus", "knowledge"},
        tests={"test_tool_values.py"},
        lean={"GolayWeightEnum": "build", "LeechShellCount": "held",
              "Rule30/Basic": "build"},
        lean_stems={"GolayWeightEnum": ["GolayWeightEnum"],
                    "LeechShellCount": ["LeechShellCount"],
                    "Basic": ["Rule30/Basic"]},
        lean_registry=("LeechShells.lean", "FoldMachine.lean"),
        study_ids=set(), phase_records={}, phase_votes={},
    )
    base.update(overrides)
    return sm.Tree(**base)


class TestFileRefs(unittest.TestCase):

    def test_code_test_and_lean_are_separated_and_resolved(self):
        text = """
        The machine is `reasoning/tool_machine.py`; the count is
        `glm_universal.reasoning.leech_shells.shell_report`, run by
        `python3 -m glm_universal.tools tool-machine`; `runtime/toolbox` answers.
        Tests: `tests/test_tool_values.py` and `tests/test_fold_machine.py`.
        The lost module `reasoning/fold_machine.py`.
        Lean: `GolayWeightEnum.lean`, `GLM.LeechShellCount.shellArr_correct`,
        `RequestProject/GLM/Rule30/Basic.lean`, `LeechShells.lean` and
        `GLM.FoldMachine.kth_eq_iff`; `Mathlib/Order/Basic.lean` is external.
        """
        refs = sm._file_refs(text, _tree())
        self.assertEqual(refs["code"], ["reasoning/leech_shells.py",
                                        "reasoning/tool_machine.py",
                                        "runtime/toolbox.py", "tools.py"])
        self.assertEqual(refs["test"], ["test_tool_values.py"])
        self.assertEqual(refs["lean"], ["GolayWeightEnum", "LeechShellCount",
                                        "Rule30/Basic"])
        self.assertEqual(refs["lean_held"], ["LeechShellCount"])
        self.assertEqual(refs["lean_missing"], ["FoldMachine", "LeechShells"])
        self.assertEqual(refs["missing"], ["reasoning/fold_machine.py",
                                           "tests/test_fold_machine.py"])
        for ref in refs["code"]:
            self.assertTrue(ref.endswith(".py"))
            self.assertFalse(ref.startswith("tests/"))


    def test_a_name_a_package_exports_is_not_a_missing_module(self):
        """``glm_universal.wheels.provisional_status`` is a function of
        ``wheels/__init__.py``: it resolves to the package (not listed as
        code, like every ``__init__.py``) and is never reported as a missing
        module ``wheels/provisional_status.py``; a name the package does not
        hold still is."""
        tree = _tree(modules={"wheels/__init__.py", "wheels/cent_wheels.py"},
                     module_stems={"__init__": ["wheels/__init__.py"],
                                   "cent_wheels": ["wheels/cent_wheels.py"]},
                     subpackages={"wheels"},
                     exports={"wheels/__init__.py": {"provisional_status",
                                                     "answer_derivability"}})
        text = ("The note comes from `glm_universal.wheels.provisional_status` and "
                "`glm_universal.wheels.answer_derivability`; the data from "
                "`glm_universal.wheels.cent_wheels.CENT_WHEELS`; "
                "`glm_universal.wheels.no_such_module` was never written.")
        refs = sm._file_refs(text, tree)
        self.assertEqual(refs["code"], ["wheels/cent_wheels.py"])
        self.assertEqual(refs["missing"], ["wheels/no_such_module.py"])

    def test_the_real_tree_resolves_package_exports(self):
        tree = sm.tree()
        self.assertIn("provisional_status", tree.exports["wheels/__init__.py"])
        refs = sm._file_refs("`glm_universal.wheels.provisional_status`", tree)
        self.assertNotIn("wheels/provisional_status.py", refs["missing"])

    def test_no_manifest_lists_a_package_export_as_missing(self):
        if _yaml is None:
            self.skipTest("PyYAML is not installed")
        tree = sm.tree()
        for path in sorted(C.STUDIES_DIR.glob("*.yaml")):
            data = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for ref in (data.get("file_refs") or {}).get("missing", []):
                pkg, _, name = ref.rpartition("/")
                init = f"{pkg}/__init__.py"
                with self.subTest(manifest=path.name, ref=ref):
                    self.assertNotIn(name[:-3] if name.endswith(".py") else name,
                                     tree.exports.get(init, set()),
                                     f"{ref} is a name {init} defines")


class TestMarks(unittest.TestCase):

    TEXT = """
## 4. The marks

| mark | statement |
|---|---|
| **L1** | the Lean file builds |
| **A1** | the first |
| **A2** | the second |
| **F1** | the frozen path |

## 7. What came out

The first is right. **A1 met.** The second fails at the first take:
**A2
missed**, and the amended F1′ is declared.

| mark | result | met |
|---|---|---|
| L1 | builds | yes |
| F1 | 699 of 702 | no |
| F1′ | 702 of 702 | yes |
"""

    def test_declared_met_missed_amended(self):
        marks = sm._marks(self.TEXT, "2 of 4 marks and 1 of 1 amended")
        self.assertEqual(marks["declared"], ["L1", "A1", "A2", "F1"])
        self.assertEqual(marks["amended"], ["F1′"])
        self.assertEqual(marks["met"], ["L1", "A1", "F1′"])
        self.assertEqual(marks["missed"], ["A2", "F1"])

    def test_the_tally_settles_unnamed_marks(self):
        text = ("| mark | claim |\n|---|---|\n| **L1** | a |\n| **T1** | b |\n"
                "\nBoth hold.\n")
        marks = sm._marks(text, "2 of 2 marks")
        self.assertEqual(marks["met"], ["L1", "T1"])
        self.assertEqual(sm._marks(text, "1 of 2 marks")["met"], [])

    def test_ranges_and_lists(self):
        self.assertEqual(sm._mark_ids("**C1–C3**"), ["C1", "C2", "C3"])
        self.assertEqual(sm._mark_ids("R1, R2"), ["R1", "R2"])
        self.assertEqual(sm._mark_ids("F1'"), ["F1′"])
        self.assertEqual(sm._mark_ids("the first"), [])


class TestDirectivesAndDates(unittest.TestCase):

    def test_directive_contexts(self):
        text = ("exact `Fraction` only (D7); directive D3 forbids it; "
                "directives D2–D4 and D15; the lattice `D12^2` and D16+ are "
                "not directives; mark (D5) is a mark here; D99 is not one.")
        self.assertEqual(sm._directives(text, ["D5"]),
                         ["D2", "D3", "D4", "D7", "D15"])

    def test_last_altered(self):
        text = ("*Created 19 October 2026.* Last altered 22 October 2026 "
                "(x). Last altered 20 October 2026 (y).")
        self.assertEqual(sm._last_altered(text), "22 October 2026")
        self.assertEqual(sm._last_altered("*Created 3 May 2026.*"),
                         "3 May 2026")
        self.assertEqual(sm._last_altered("no stamp"), "")

    def test_status(self):
        t = _tree()
        self.assertEqual(sm._status("No. None passes.", 0, t), "negative")
        self.assertEqual(sm._status("No member is lost.", 0, t), "closed")
        self.assertEqual(sm._status("The verdict: `not reproduced`.", 0, t),
                         "negative")
        self.assertEqual(sm._status("Not yet measured.", 0, t), "open")


class TestMerge(unittest.TestCase):

    def test_judgement_fields_and_hand_fields_are_kept(self):
        derived = {"schema": sm.SCHEMA_NAME, "id": "X_STUDY", "faculty":
                   "unknown", "phase": 7, "question": "q", "verdict": "v",
                   "file_refs": {"prose": "X_STUDY.md", "code": ["a.py"]}}
        existing = {"faculty": "refusal", "phase": 3,
                    "hand_fields": ["faculty"],
                    "junctions": [{"wheels": ["W1", "W2"], "rule": "current"}],
                    "file_refs": {"prose": "X_STUDY.md", "wheel": ["W1"],
                                  "code": ["junk"]},
                    "note": "a person's own key"}
        merged = sm.merged_manifest(derived, existing)
        self.assertEqual(merged["faculty"], "refusal")      # hand field kept
        self.assertEqual(merged["phase"], 7)                # derived wins
        self.assertEqual(merged["junctions"], existing["junctions"])
        self.assertEqual(merged["file_refs"]["wheel"], ["W1"])
        self.assertEqual(merged["file_refs"]["code"], ["a.py"])
        self.assertEqual(merged["note"], "a person's own key")
        self.assertEqual(merged["follow_ups"], [])          # default

    def test_a_hand_field_covers_its_sub_fields(self):
        derived = {"schema": sm.SCHEMA_NAME, "id": "X_STUDY", "question": "q",
                   "verdict": "v", "file_refs": {"prose": "X_STUDY.md"},
                   "marks": {"declared": ["A1", "A2"], "met": ["A2"],
                             "missed": ["A1"], "amended": []}}
        record = {"declared": ["A1", "A2"], "met": ["A1", "A2"],
                  "missed": [], "amended": []}
        kept = sm.merged_manifest(derived, {"hand_fields": ["marks"],
                                            "marks": record})
        self.assertEqual(kept["marks"], record)
        one = sm.merged_manifest(derived, {"hand_fields": ["marks.met"],
                                           "marks": record})
        self.assertEqual(one["marks"]["met"], ["A1", "A2"])
        self.assertEqual(one["marks"]["missed"], ["A1"])   # not kept
        # a name is not a prefix of another field's name
        loose = sm.merged_manifest(derived, {"hand_fields": ["mark"],
                                             "marks": record})
        self.assertEqual(loose["marks"], derived["marks"])


@unittest.skipUnless(_yaml is not None, "PyYAML not installed")
class TestTheRepository(unittest.TestCase):
    """The real studies folder, as it stands."""

    @classmethod
    def setUpClass(cls):
        cls.derived = sm.derive_all(sm.tree(refresh=True))
        cls.manifests = sm.load_manifests()

    def test_every_study_has_a_manifest_and_none_drifted(self):
        report = sm.drift()
        self.assertEqual(report.missing, [])
        self.assertEqual(report.orphans, [])
        self.assertEqual(report.unreadable, [])
        self.assertEqual(report.invalid, {})
        self.assertEqual(sorted(report.drifted), [],
                         "run python3 -m glm_universal.corpus.study_manifest "
                         "--sync")

    def test_derivation_is_deterministic(self):
        again = sm.derive_all(sm.tree(refresh=True))
        self.assertEqual(again, self.derived)

    def test_file_refs_name_existing_files(self):
        for sid, data in self.manifests.items():
            refs = data["file_refs"]
            self.assertEqual(refs["prose"], sid + ".md")
            for ref in refs.get("code", []):
                self.assertTrue(ref.endswith(".py"), (sid, ref))
                self.assertTrue((C.PACKAGE_ROOT / ref).is_file(), (sid, ref))
            for ref in refs.get("test", []):
                self.assertTrue((C.PACKAGE_ROOT / "tests" / ref).is_file(),
                                (sid, ref))
            for ref in refs.get("lean", []):
                self.assertTrue(C.lean_file(ref).is_file(), (sid, ref))
            for ref in refs.get("lean_held", []):
                self.assertIn(ref, refs.get("lean", []))
                self.assertIn(C.LEAN_HOLDING_DIR, C.lean_file(ref).parents)

    def test_lean_missing_is_registered(self):
        registry = {name[:-len(".lean")] for name in
                    sm._parse_missing_registry(
                        C.LEAN_FILES_NEEDED.read_text(encoding="utf-8"))}
        for sid, data in self.manifests.items():
            for ref in data["file_refs"].get("lean_missing", []):
                self.assertIn(ref, registry, sid)
                self.assertFalse(C.lean_file(ref).is_file(), (sid, ref))

    def test_predecessors_are_strictly_earlier_and_successors_invert(self):
        phases = {sid: d.get("phase", 0) for sid, d in self.manifests.items()}
        succ = Counter()
        for sid, data in self.manifests.items():
            for pred in data.get("predecessors", []):
                self.assertLess(0, phases[pred])
                self.assertLess(phases[pred], phases[sid], (sid, pred))
                self.assertIn(sid, self.manifests[pred]["successors"])
                succ[pred] += 1
        for sid, data in self.manifests.items():
            self.assertEqual(len(data.get("successors", [])), succ[sid])

    def test_directives_are_in_range(self):
        for sid, data in self.manifests.items():
            for name in data.get("directives", []):
                self.assertRegex(name, r"^D([1-9]|1[0-9]|2[0-2])$", sid)

    def test_check_command(self):
        self.assertEqual(sm.main(["--check"]), 0)


class TestCitedStudiesExist(unittest.TestCase):
    """Every ``X_STUDY.md`` the repository's documents and code cite is a
    study document in ``studies/`` (or a supplied item of that name, found
    through ``constants.source_material_item``)."""

    #: Citations known to be stale, outside this area, with their fix; the
    #: second test fails as soon as one is fixed, so the list only shrinks.
    KNOWN_STALE: set = set()

    #: Seven studies lost in the October 2026 reorganisation, reconstructed.
    RECONSTRUCTED = ("FOLD_MACHINE_STUDY", "STUDY_LEDGER_STUDY",
                     "SOURCE_TIERS_STUDY", "TOOL_MACHINE_STUDY",
                     "LEECH_SHELLS_STUDY", "LEECH_KISSING_STUDY",
                     "COLOUR_INDUCTION_STUDY")

    @staticmethod
    def _citations():
        import os
        import re
        from pathlib import Path
        pattern = re.compile(
            r"(?<![A-Za-z0-9_])([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_STUDY)\.md")
        root = C.REPOSITORY_ROOT
        skip = {".git", ".lake", "__pycache__", "source_material", "tests",
                "node_modules"}
        found = set()
        for folder, dirs, files in os.walk(root):
            dirs[:] = sorted(d for d in dirs
                             if d not in skip and not d.startswith("."))
            for name in files:
                if not name.endswith((".md", ".py", ".lean")):
                    continue
                path = Path(folder) / name
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                rel = path.relative_to(root).as_posix()
                for line in text.splitlines():
                    if "was cited as" in line:      # a recorded former name
                        continue
                    for match in pattern.finditer(line):
                        found.add((rel, match.group(1)))
        return found

    def _missing(self):
        return {(rel, sid) for rel, sid in self._citations()
                if not (C.STUDIES_DIR / f"{sid}.md").exists()
                and not C.source_material_item(f"{sid}.md").exists()}

    def test_every_cited_study_exists(self):
        self.assertEqual(sorted(self._missing() - self.KNOWN_STALE), [])

    def test_the_known_stale_list_only_records_real_sites(self):
        self.assertEqual(sorted(self.KNOWN_STALE - self._missing()), [],
                         "remove these from KNOWN_STALE")

    def test_reconstructed_studies_say_so(self):
        for sid in self.RECONSTRUCTED:
            path = C.STUDIES_DIR / f"{sid}.md"
            self.assertTrue(path.exists(), sid)
            text = path.read_text(encoding="utf-8")
            self.assertIn("Reconstructed 31 October 2026 from the round "
                          "records; the original was lost in the October "
                          "2026 reorganisation", text, sid)
            self.assertTrue((C.STUDIES_DIR / f"{sid}.yaml").exists(), sid)


if __name__ == "__main__":
    unittest.main()
