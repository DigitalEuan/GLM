"""The intake pipeline (directive D22), pinned.

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 31 October 2026: the build-record gate, staged code,
``absorb-staged`` and the staged reports; the study gate's synchronised
manifest, the finished measurement and its acceptance decision, test
fingerprints (a stale pass refused, absorption re-running every test) and
records absorbed before acceptance decisions were recorded; the fallback
runner used where pytest is not installed; the exit status of the owner's
two scripts; provisional parts (installed ahead of the build record by the
owner's decision), the register of provisional families, and absorption
that confirms them; the fallback runner's setup and teardown hooks (a failing
``teardown_class`` fails the file and refuses the promotion).*
*Last altered 1 November 2026 (Phase 186): ``absorb-ahead`` and
``confirm-build`` (whole and partial absorption ahead of the build record, by
the owner's decision, on the measurements and a standalone Lean check); the
real ledger's wheel items read in either register state.*

``glm_universal.intake`` files supplied material under
``source_material/ToDo/`` and ``source_material/done/`` and moves an item along
received -> triaged -> study drafted -> tested -> Lean written -> Lean
verified -> measured -> absorbed (or closed with a reason) only when each
gate's evidence exists.  Lean verified (and every later promotion) needs the
owner's build record, matched against the named Lean files and everything
they import; staged code is tested in a scratch overlay and installed only on
absorption.
Most tests build a scratch repository with :meth:`Layout.under`, so nothing
in the real tree is touched; the last class checks the real ledger.
"""

from __future__ import annotations

import datetime
import io
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from glm_universal import constants as C
from glm_universal import lean_check
from glm_universal.intake import actions, gates, ledger
from glm_universal.intake.__main__ import main as intake_main
from glm_universal.intake.ledger import Layout, LedgerError

STUDY = """# Demo study

## Tier 0 — the coarse read

**Question.** Does the demo help?

**Verdict.** Yes: 3 of 3.

**Deciding figure.** 3 of 3 marks.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows.*

## 1. Body

The demo is accepted when it answers 3 of 3.

Yes: 3 of 3 marks.
"""

#: The acceptance decision of an item measured by DEMO_STUDY.
ACCEPT_DEMO = {"study": "DEMO_STUDY", "criterion": "The demo is accepted when it answers 3 of 3",
               "result": "3 of 3 marks", "decision": "accept"}

MARKED_STUDY = """# Marked study

## Tier 0 — the coarse read

**Question.** Does the marked demo help?

**Verdict.** Yes, with one mark not met: M1 is met and M2 is not.

**Deciding figure.** 3 of 3 answers right, 1 wrong answer.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows.*

## 1. The marks

The demo is accepted when M1 is met.

| Mark | Met when | Measured | Met |
|---|---|---|---|
| M1 | 3 of 3 answers right | 3 of 3 | yes |
| M2 | no wrong answer | 1 wrong | no |
"""


def _passing(ref, command, cwd, env, timeout):
    return "pass", "exit 0"


def _failing(ref, command, cwd, env, timeout):
    return "fail", "exit 1"


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class Scratch(unittest.TestCase):
    """A scratch repository with the shape :meth:`Layout.under` expects."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="glm-intake-test-"))
        self.lay = Layout.under(self.tmp)
        lay = self.lay
        for d in (lay.todo, lay.done, lay.studies):
            d.mkdir(parents=True, exist_ok=True)
        _write(lay.package / "reasoning" / "demo_mod.py", "X = 1\n")
        _write(lay.package / "tests" / "test_demo_mod.py", "def test_x():\n    assert True\n")
        for sid, text in (("DEMO_STUDY", STUDY), ("MARKED_STUDY", MARKED_STUDY)):
            md = _write(lay.studies / f"{sid}.md", text)
            _write(lay.studies / f"{sid}.yaml", actions.manifest_text(md))
        _write(lay.lean_glm / "Demo.lean", "theorem demo : True := trivial\n")
        _write(lay.lean_glm / "Loose.lean", "theorem loose : True := trivial\n")
        _write(lay.lean_audit, "import RequestProject.GLM.Demo\n")
        _write(lay.lean_holding / lay.lean_library / "GLM" / "Held.lean", "-- waits\n")
        _write(lay.lean_needed, "| `Missing.lean` | lost |\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    # helpers -------------------------------------------------------------
    def new_item(self, name: str = "note.md", text: str = "an idea\n") -> dict:
        _write(self.lay.material / name, text)
        return actions.register(str(self.lay.material / name), self.lay)

    def edit(self, item_id: str, **fields) -> None:
        data = ledger.load(self.lay)
        ledger.record_by_id(data, item_id).update(fields)
        ledger.save(data, self.lay)

    def record(self, item_id: str) -> dict:
        return ledger.record_by_id(ledger.load(self.lay), item_id)

    def errors(self) -> list:
        return gates.check(ledger.load(self.lay), self.lay)["errors"]

    def record_current_pass(self, item_id: str) -> None:
        """A pass of every named test, taken against the code as it now stands."""
        rec = self.record(item_id)
        fp = gates.test_fingerprint(rec, self.lay)
        self.edit(item_id, test_results=[
            {"test": t, "result": "pass", "detail": "exit 0", "date": "31 October 2026",
             "fingerprint": fp} for t in rec.get("tests", [])])

    def write_evidence(self) -> None:
        """A passing build record of the scratch Lean tree as it now stands."""
        ok, _ = lean_check.write_build_evidence(
            static_exit=0, build_exit=0, sorry_exit=0, log="scratch.log",
            root=self.lay.lean_source, library=self.lay.lean_library, audit=self.lay.lean_audit,
            repo_root=self.lay.root, out=self.lay.lean_evidence)
        self.assertTrue(ok)


class TestNames(unittest.TestCase):

    def test_stage_names(self):
        self.assertEqual(ledger.stage_key("Lean verified"), "lean_verified")
        self.assertEqual(ledger.stage_key("study-drafted"), "study_drafted")
        self.assertEqual(ledger.stage_key("CLOSED"), "closed")
        with self.assertRaises(LedgerError):
            ledger.stage_key("finished")
        self.assertEqual(ledger.STAGES[0], "received")
        self.assertEqual(ledger.STAGES[-1], "absorbed")

    def test_ids(self):
        self.assertEqual(actions.item_id_for("Golay codes and Hadamard matrices.txt"),
                         "Golay_codes_and_Hadamard_matrices")
        self.assertEqual(actions.item_id_for("cent_compiler_v12"), "cent_compiler_v12")
        self.assertEqual(actions.study_id_for("cent_compiler_v12"), "CENT_COMPILER_V12_STUDY")
        self.assertEqual(actions.study_id_for("HISTORY_V4_STUDY"), "HISTORY_V4_STUDY")

    def test_layout_comes_from_constants(self):
        lay = Layout.default()
        self.assertEqual(lay.todo, C.SOURCE_TODO_DIR)
        self.assertEqual(lay.done, C.SOURCE_DONE_DIR)
        self.assertEqual(lay.ledger, C.INTAKE_LEDGER)
        self.assertEqual(lay.lean_audit, C.LEAN_AUDIT_FILE)


class TestRegisterAndCheck(Scratch):

    def test_register_moves_a_loose_item(self):
        rec = self.new_item()
        self.assertEqual(rec["path"], "ToDo/note.md")
        self.assertEqual(rec["stage"], "received")
        self.assertTrue((self.lay.todo / "note.md").is_file())
        self.assertFalse((self.lay.material / "note.md").exists())
        self.assertEqual(ledger.today(datetime.date(2026, 10, 31)), "31 October 2026")
        self.assertEqual(self.errors(), [])

    def test_register_copies_from_outside_and_refuses_twice(self):
        outside = _write(self.tmp / "elsewhere" / "folder_item" / "a.py", "print(1)\n").parent
        rec = actions.register(str(outside), self.lay)
        self.assertEqual(rec["path"], "ToDo/folder_item")
        self.assertTrue(outside.exists())               # copied, not moved
        self.assertTrue((self.lay.todo / "folder_item" / "a.py").is_file())
        with self.assertRaises(LedgerError):
            actions.register(str(outside), self.lay)
        with self.assertRaises(LedgerError):
            actions.register(str(self.lay.todo / "folder_item"), self.lay)

    def test_check_finds_unrecorded_loose_and_misfiled(self):
        _write(self.lay.todo / "stray.txt", "x\n")
        _write(self.lay.material / "loose.txt", "x\n")
        errors = self.errors()
        self.assertTrue(any("ToDo/stray.txt is filed but has no intake record" in e for e in errors))
        self.assertTrue(any("loose.txt is loose" in e for e in errors))
        self.new_item("other.md")
        self.edit("other", path="done/other.md")
        (self.lay.todo / "other.md").rename(self.lay.done / "other.md")
        self.assertTrue(any("filed in done/ at stage received" in e for e in self.errors()))

    def test_record_claiming_a_stage_without_evidence_fails(self):
        self.new_item()
        self.edit("note", stage="tested", kind="concept note", offers="an idea", next_step="go")
        errors = self.errors()
        self.assertTrue(any("[study_drafted] no study named" in e for e in errors))
        self.assertTrue(any("[tested] no test named" in e for e in errors))


class TestGates(Scratch):

    def test_lean_states(self):
        self.assertEqual(gates.lean_state("Demo", self.lay)[0], "audited")
        self.assertEqual(gates.lean_state("RequestProject.GLM.Demo", self.lay)[0], "audited")
        self.assertEqual(gates.lean_state("Loose", self.lay)[0], "unaudited")
        self.assertEqual(gates.lean_state("Held", self.lay)[0], "held")
        self.assertEqual(gates.lean_state("Missing", self.lay)[0], "missing")
        self.assertEqual(gates.lean_state("Nowhere", self.lay)[0], "absent")

    def test_advance_needs_triage_first(self):
        self.new_item()
        report = actions.advance("note", "triaged", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertEqual(self.record("note")["stage"], "received")
        self.edit("note", kind="concept note", offers="an idea", next_step="study it")
        self.assertTrue(actions.advance("note", "triaged", self.lay, run=False)["ok"])
        with self.assertRaises(LedgerError):
            actions.advance("note", "received", self.lay)
        with self.assertRaises(LedgerError):
            actions.advance("note", "closed", self.lay)

    def test_scaffold_drafts_a_study_and_never_overwrites(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea worth testing", next_step="study it",
                  stage="triaged")
        md, yml = actions.scaffold("note", self.lay)
        self.assertEqual(md.name, "NOTE_STUDY.md")
        text = md.read_text(encoding="utf-8")
        for needle in ("## Tier 0", "**Question.**", "**Verdict.**", "**Deciding figure.**",
                       "**Recomputed by.**", "Created ", "## 3. The marks, declared before the code",
                       "| I1 |", "## 5. Lean obligations", "an idea worth testing"):
            self.assertIn(needle, text)
        import yaml
        manifest = yaml.safe_load(yml.read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], "NOTE_STUDY")
        self.assertEqual(manifest["schema"], "glm-study-manifest/v1")
        rec = self.record("note")
        self.assertEqual(rec["studies"], ["NOTE_STUDY"])
        self.assertEqual(rec["stage"], "study_drafted")
        with self.assertRaises(LedgerError):
            actions.scaffold("note", self.lay)
        self.assertEqual(self.errors(), [])

    def test_the_whole_line_to_absorbed(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="study it",
                  stage="study_drafted", studies=["DEMO_STUDY"], tests=["tests/test_demo_mod.py"])

        def failing(ref, command, cwd, env, timeout):
            return "fail", "exit 1"

        def passing(ref, command, cwd, env, timeout):
            return "pass", "exit 0"

        report = actions.advance("note", "tested", self.lay, runner=failing)
        self.assertFalse(report["ok"])
        rec = self.record("note")
        self.assertEqual(rec["stage"], "study_drafted")
        self.assertEqual(rec["test_results"][-1]["result"], "fail")   # a failed run is recorded
        self.assertTrue(actions.advance("note", "tested", self.lay, runner=passing)["ok"])

        self.edit("note", lean=["Held"])
        report = actions.advance("note", "lean_written", self.lay,
                                 lean_checker=lambda lay, t: (True, "OK"))
        self.assertFalse(report["ok"])
        self.assertTrue(any("held" in p for p in report["problems"]))
        self.edit("note", lean=["Demo"])
        report = actions.advance("note", "lean_written", self.lay,
                                 lean_checker=lambda lay, t: (False, "exit 1"))
        self.assertFalse(report["ok"])
        self.assertTrue(actions.advance("note", "lean_written", self.lay,
                                        lean_checker=lambda lay, t: (True, "OK"))["ok"])
        # Lean verified needs the owner's build record: none yet, so refused.
        report = actions.advance("note", "lean_verified", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("no build record" in p or "not verified" in p or "record" in p
                            for p in report["problems"]), report["problems"])
        self.write_evidence()
        self.assertTrue(actions.advance("note", "lean_verified", self.lay, run=False)["ok"])
        self.assertIn("lake build passed", self.record("note")["lean_build"])

        self.assertFalse(actions.advance("note", "measured", self.lay, run=False)["ok"])
        self.edit("note", measured="DEMO_STUDY: 3 of 3 marks")
        report = actions.advance("note", "measured", self.lay, run=False)
        self.assertFalse(report["ok"])                      # no acceptance decision yet
        self.assertTrue(any("no acceptance decision" in p for p in report["problems"]))
        actions.accept("note", ACCEPT_DEMO["criterion"], ACCEPT_DEMO["result"], self.lay)
        self.assertEqual(self.record("note")["acceptance"]["decision"], "accept")
        self.assertTrue(actions.advance("note", "measured", self.lay, run=False)["ok"])

        self.edit("note", absorbed_into=["reasoning/nowhere"])
        self.assertFalse(actions.advance("note", "absorbed", self.lay, run=False)["ok"])
        self.edit("note", absorbed_into=["reasoning/demo_mod"])
        self.assertTrue(actions.advance("note", "absorbed", self.lay, run=False)["ok"])
        rec = self.record("note")
        self.assertEqual(rec["path"], "done/note.md")
        self.assertTrue((self.lay.done / "note.md").is_file())
        self.assertFalse((self.lay.todo / "note.md").exists())
        self.assertEqual(self.errors(), [])
        with self.assertRaises(LedgerError):
            actions.advance("note", "absorbed", self.lay)

    def test_close_needs_a_reason_evidence_and_no_open_part(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="decide",
                  stage="triaged", parts=[{"part": "the rest", "status": "open"}])
        with self.assertRaises(LedgerError):
            actions.close("note", "", ["DEMO_STUDY"], self.lay)
        with self.assertRaises(LedgerError):
            actions.close("note", "superseded", [], self.lay)
        with self.assertRaises(LedgerError):
            actions.close("note", "superseded", ["NO_SUCH_STUDY"], self.lay)
        with self.assertRaises(LedgerError):
            actions.close("note", "superseded", ["DEMO_STUDY"], self.lay)   # an open part
        rec = actions.close("note", "superseded by the demo", ["DEMO_STUDY"], self.lay,
                            close_open_parts=True)
        self.assertEqual(rec["stage"], "closed")
        self.assertEqual(rec["path"], "done/note.md")
        self.assertEqual(rec["parts"][0]["status"], "closed")
        self.assertTrue((self.lay.done / "note.md").is_file())
        self.assertEqual(self.errors(), [])

    def test_item_tests_run_on_a_scratch_copy(self):
        folder = self.lay.material / "kit"
        _write(folder / "check.py",
               "from pathlib import Path\nPath('written_by_test.txt').write_text('x')\n")
        _write(folder / "bad.py", "raise SystemExit(3)\n")
        actions.register(str(folder), self.lay)
        rec = self.record("kit")
        self.assertEqual(actions.run_test("item:check.py", rec, self.lay, timeout=120)[0], "pass")
        result, detail = actions.run_test("item:bad.py", rec, self.lay, timeout=120)
        self.assertEqual(result, "fail")
        self.assertIn("exit 3", detail)
        self.assertEqual(actions.run_test("item:absent.py", rec, self.lay)[0], "error")
        self.assertEqual(sorted(p.name for p in (self.lay.todo / "kit").iterdir()),
                         ["bad.py", "check.py"])        # the item is unchanged

    def test_a_detail_never_copies_what_the_test_printed(self):
        """The ledger records an outcome in the intake's own words (exit
        code, meaning, counts), not lines of the test's output."""
        folder = self.lay.material / "loud"
        _write(folder / "ok.py", "print('PRINTED-BY-OK /tmp/somewhere')\n")
        _write(folder / "no.py", "import sys\nprint('PRINTED-BY-NO')\n"
                                 "sys.stderr.write('Traceback: PRINTED-ON-STDERR\\n')\nsys.exit(1)\n")
        actions.register(str(folder), self.lay)
        rec = self.record("loud")
        ok = actions.run_test("item:ok.py", rec, self.lay, timeout=120)
        no = actions.run_test("item:no.py", rec, self.lay, timeout=120)
        self.assertEqual(ok, ("pass", "passed (exit 0): the script ran to completion"))
        self.assertEqual(no[0], "fail")
        self.assertTrue(no[1].startswith("failed (exit 1): "), no)
        for detail in (ok[1], no[1]):
            self.assertNotIn("PRINTED", detail)
            self.assertNotIn("/tmp", detail)

    def test_package_test_counts_are_rewritten_not_copied(self):
        out = "....\n3 passed, 1 failed (including 1 failing setup/teardown hook(s)), " \
              "2 skipped of 5 collected in test_x.py (without pytest)\n"
        self.assertEqual(
            actions.describe_exit("fallback", 1, out),
            ("fail", "failed (exit 1): a test or a setup/teardown hook failed (without pytest); "
                     "3 passed, 1 failed (1 of them setup/teardown hooks), 2 skipped of 5 collected"))
        self.assertEqual(actions.describe_exit("pytest", 0, "..\n2 passed, 1 skipped in 0.1s\n"),
                         ("pass", "passed (exit 0): every collected test passed (pytest); "
                                  "2 passed, 1 skipped"))
        self.assertEqual(actions.describe_exit("script", 7, "anything at all"),
                         ("fail", "failed (exit 7): the command ended without success"))
        self.assertEqual(actions.command_kind(["python3", "/x/run.py", "-c"]), "script")
        self.assertEqual(actions.command_kind(["python3", "-c", "pass"]), "call")

    def test_local_only_files_warn_rather_than_fail(self):
        data = ledger.load(self.lay)
        data["items"].append({"id": "archive", "path": "done/archive.zip", "local_only": True,
                              "kind": "data", "offers": "a snapshot", "stage": "closed",
                              "closed_reason": "kept on the owner's machine",
                              "evidence": ["DEMO_STUDY"]})
        ledger.save(data, self.lay)
        _write(self.lay.material / "archive.zip", "zip\n")
        result = gates.check(ledger.load(self.lay), self.lay)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("still at the flat location" in w for w in result["warnings"]))


class TestTheBuildRecordGate(Scratch):
    """Lean verified rests on the owner's build record, file by file."""

    def item_at_lean_written(self, lean=("Demo",)) -> None:
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="build it",
                  stage="lean_written", studies=["DEMO_STUDY"], tests=["tests/test_demo_mod.py"],
                  lean=list(lean))
        self.record_current_pass("note")
        self.assertEqual(self.errors(), [])

    def test_a_missing_record_refuses(self):
        self.item_at_lean_written()
        report = actions.advance("note", "lean_verified", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertEqual(self.record("note")["stage"], "lean_written")

    def test_a_failed_build_writes_no_record(self):
        ok, why = lean_check.write_build_evidence(
            static_exit=0, build_exit=1, sorry_exit=0, root=self.lay.lean_source,
            library=self.lay.lean_library, audit=self.lay.lean_audit, repo_root=self.lay.root,
            out=self.lay.lean_evidence)
        self.assertFalse(ok)
        self.assertIn("build exit 1", why)
        self.assertFalse(self.lay.lean_evidence.exists())

    def test_a_matching_record_verifies_and_a_stale_one_does_not(self):
        self.item_at_lean_written()
        self.write_evidence()
        demo = self.lay.lean_glm / "Demo.lean"
        demo.write_text("theorem demo : True := by trivial\n", encoding="utf-8")   # changed since
        report = actions.advance("note", "lean_verified", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("Demo" in p for p in report["problems"]), report["problems"])
        self.write_evidence()                       # the owner rebuilds
        self.assertTrue(actions.advance("note", "lean_verified", self.lay, run=False)["ok"])
        self.assertEqual(self.errors(), [])
        demo.write_text("theorem demo : True := trivial\n", encoding="utf-8")
        result = gates.check(ledger.load(self.lay), self.lay)
        self.assertEqual(result["errors"], [])      # recorded; later edits warn
        self.assertTrue(any("since its verified build" in w for w in result["warnings"]))

    def test_a_change_in_an_imported_file_invalidates_the_record(self):
        _write(self.lay.lean_glm / "Base.lean", "theorem base : True := trivial\n")
        _write(self.lay.lean_glm / "Top.lean",
               "import RequestProject.GLM.Base\ntheorem top : True := base\n")
        _write(self.lay.lean_audit, "import RequestProject.GLM.Demo\nimport RequestProject.GLM.Top\n")
        self.item_at_lean_written(lean=("Top",))
        self.write_evidence()
        (self.lay.lean_glm / "Base.lean").write_text("theorem base : 1 = 1 := rfl\n", encoding="utf-8")
        report = actions.advance("note", "lean_verified", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("Base" in p for p in report["problems"]), report["problems"])


class TestStagedCode(Scratch):
    """Code waits in <item>/staged/ until absorption installs it."""

    def staged_item(self, open_part: bool = False) -> Path:
        folder = self.lay.material / "kit"
        _write(folder / "README.md", "a kit\n")
        actions.register(str(folder), self.lay)
        item = self.lay.todo / "kit"
        pkg = self.lay.package.relative_to(self.lay.root)
        _write(item / "staged" / pkg / "wheels" / "kit_wheel.py", "VALUE = 7\n")
        _write(item / "staged" / pkg / "tests" / "test_kit_wheel.py",
               "from glm_universal.wheels.kit_wheel import VALUE\n\n"
               "def test_value():\n    assert VALUE == 7\n")
        parts = [{"part": "the wheel", "status": "staged", "absorbed_into": ["wheels/kit_wheel"]}]
        if open_part:
            parts.append({"part": "the notes", "status": "open"})
        ref = f"staged:{pkg}/tests/test_kit_wheel.py"
        self.edit("kit", kind="code", offers="a wheel", next_step="build it", stage="measured",
                  studies=["DEMO_STUDY"], tests=[ref],
                  lean=["Demo"], lean_build="scratch", measured="DEMO_STUDY: 3 of 3 marks",
                  acceptance=dict(ACCEPT_DEMO), absorbed_into=["wheels/kit_wheel"], parts=parts)
        self.record_current_pass("kit")
        return item

    def test_staged_parts_check_and_never_reach_done(self):
        self.staged_item()
        self.assertEqual(self.errors(), [])
        self.edit("kit", parts=[{"part": "the wheel", "status": "staged",
                                 "absorbed_into": ["wheels/elsewhere"]}])
        self.assertTrue(any("does not stage" in e for e in self.errors()))

    def test_a_staged_file_that_would_overwrite_is_an_error(self):
        self.staged_item()
        _write(self.lay.package / "wheels" / "kit_wheel.py", "VALUE = 8\n")
        self.assertTrue(any("would overwrite" in e or "differs from the file" in e
                            for e in self.errors()))
        self.write_evidence()
        report = actions.advance("kit", "absorbed", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertEqual((self.lay.package / "wheels" / "kit_wheel.py").read_text(), "VALUE = 8\n")
        self.assertTrue((self.lay.todo / "kit" / "staged").is_dir())

    def test_absorption_needs_the_build_record_then_installs(self):
        item = self.staged_item()
        report = actions.advance("kit", "absorbed", self.lay, run=False)
        self.assertFalse(report["ok"])                       # no build record yet
        self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())
        self.assertTrue((item / "staged").is_dir())
        self.write_evidence()
        report = actions.advance("kit", "absorbed", self.lay, run=False)
        self.assertTrue(report["ok"], report["problems"])
        self.assertEqual((self.lay.package / "wheels" / "kit_wheel.py").read_text(), "VALUE = 7\n")
        self.assertTrue((self.lay.package / "tests" / "test_kit_wheel.py").is_file())
        rec = self.record("kit")
        self.assertEqual(rec["path"], "done/kit")
        self.assertEqual(rec["parts"][0]["status"], "absorbed")
        self.assertEqual(len(rec["installed"]), 2)
        self.assertFalse((self.lay.done / "kit" / "staged").exists())
        self.assertEqual(self.errors(), [])

    def test_a_failing_absorbed_gate_rolls_the_install_back(self):
        item = self.staged_item()
        self.edit("kit", absorbed_into=["wheels/kit_wheel", "wheels/never_written"])
        self.write_evidence()
        report = actions.advance("kit", "absorbed", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("never_written" in p for p in report["problems"]))
        self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())
        self.assertTrue((item / "staged" / self.lay.package.relative_to(self.lay.root)
                         / "wheels" / "kit_wheel.py").is_file())
        self.assertEqual(self.record("kit")["stage"], "measured")

    def test_absorb_staged_takes_the_staged_parts_and_leaves_the_open_ones(self):
        self.staged_item(open_part=True)
        self.assertFalse(actions.advance("kit", "absorbed", self.lay, run=False)["ok"])
        self.assertFalse(actions.absorb_staged("kit", self.lay, run=False)["ok"])  # no build record
        self.write_evidence()
        report = actions.absorb_staged("kit", self.lay, runner=_passing)
        self.assertTrue(report["ok"], report["problems"])
        rec = self.record("kit")
        self.assertEqual(rec["path"], "ToDo/kit")
        self.assertEqual([p["status"] for p in rec["parts"]], ["absorbed", "open"])
        self.assertTrue((self.lay.package / "wheels" / "kit_wheel.py").is_file())
        self.assertEqual(self.errors(), [])
        with self.assertRaises(LedgerError):
            actions.absorb_staged("kit", self.lay, runner=_passing)       # nothing left staged

    def test_staged_tests_run_against_the_staged_code(self):
        self.staged_item()
        rec = self.record("kit")
        ref = rec["tests"][0]
        top = Path(tempfile.mkdtemp(prefix="glm-intake-overlay-"))
        try:
            actions.staged_overlay(rec, self.lay, top)
            pkg = self.lay.package.relative_to(self.lay.root)
            self.assertEqual((top / pkg / "wheels" / "kit_wheel.py").read_text(), "VALUE = 7\n")
            self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())
            self.assertFalse((top / pkg / "reasoning" / "demo_mod.py").is_symlink())   # a copy
        finally:
            shutil.rmtree(top, ignore_errors=True)
        seen = {}

        def runner(r, command, cwd, env, timeout):
            seen["cwd"] = cwd
            seen["target"] = command[-1]
            return "pass", "exit 0"

        self.assertEqual(actions.run_test(ref, rec, self.lay, runner=runner)[0], "pass")
        self.assertTrue(seen["target"].endswith("test_kit_wheel.py"))
        self.assertNotEqual(Path(seen["cwd"]), self.lay.root)


class TestStagedReports(Scratch):
    """A study's recompute function that lives in staged code runs against it."""

    def test_staged_call_returns_plain_data(self):
        folder = self.lay.material / "kit"
        _write(folder / "README.md", "a kit\n")
        actions.register(str(folder), self.lay)
        pkg = self.lay.package.relative_to(self.lay.root)
        _write(self.lay.package / "__init__.py", "")
        _write(self.lay.package / "wheels" / "__init__.py", "")
        _write(self.lay.todo / "kit" / "staged" / pkg / "wheels" / "kit_study.py",
               "from fractions import Fraction\n\n"
               "def report():\n"
               "    return {'holds': True, 'share': Fraction(1, 3), (1, 2): [3, 4]}\n")
        from glm_universal.intake import staged_reports
        got = staged_reports.staged_call("kit", "glm_universal.wheels.kit_study.report", self.lay,
                                         timeout=300)
        self.assertEqual(got, {"holds": True, "share": "1/3", "(1, 2)": [3, 4]})
        self.assertFalse((self.lay.package / "wheels" / "kit_study.py").exists())
        with self.assertRaises(RuntimeError):
            staged_reports.staged_call("kit", "glm_universal.wheels.kit_study.absent", self.lay,
                                       timeout=300)

    def test_the_wheel_studies_recompute_from_the_installed_modules(self):
        from glm_universal.intake import staged_reports
        self.assertEqual(staged_reports.__all__, ["staged_call"])
        for sid, fn in (("INTEGER_WHEEL_STUDY",
                         "glm_universal.wheels.integer_wheel_study.integer_wheel_report"),
                        ("CENT_WHEELS_STUDY",
                         "glm_universal.wheels.cent_wheels_study.cent_wheels_report")):
            text = (C.STUDIES_DIR / f"{sid}.md").read_text(encoding="utf-8")
            self.assertIn(f"**Recomputed by.** `{fn}`", text, sid)


class TestProvisionalCode(Scratch):
    """By the owner's decision, staged code may be installed ahead of the build
    record: its parts are ``provisional``, the item is in the register of
    provisional families, and absorption on a verifying build record confirms
    it."""

    def provisional_item(self, open_part: bool = False, **edits) -> dict:
        TestStagedCode.staged_item(self, open_part=open_part)
        self.edit("kit", stage="lean_written", measured=None, acceptance=None, lean_build=None,
                  **edits)
        self.record_current_pass("kit")
        return actions.provisional("kit", "keep it in the wheels folder, marked provisional",
                                   self.lay, wheels=["KW"], runner=_passing)

    def promote_to_measured(self) -> None:
        self.edit("kit", stage="measured", lean_build="scratch",
                  measured="DEMO_STUDY: 3 of 3 marks", acceptance=dict(ACCEPT_DEMO))
        self.write_evidence()

    def test_the_install_marks_the_parts_and_registers_the_item(self):
        report = self.provisional_item()
        self.assertTrue(report["ok"], report["problems"])
        self.assertEqual((self.lay.package / "wheels" / "kit_wheel.py").read_text(), "VALUE = 7\n")
        self.assertFalse((self.lay.todo / "kit" / "staged").exists())
        rec = self.record("kit")
        self.assertEqual((rec["path"], rec["stage"]), ("ToDo/kit", "lean_written"))
        self.assertEqual([p["status"] for p in rec["parts"]], ["provisional"])
        reg = ledger.load_provisional(self.lay)
        self.assertEqual(reg["kit"]["modules"], ["wheels/kit_wheel"])
        self.assertEqual((reg["kit"]["wheels"], reg["kit"]["lean"]), (["KW"], ["Demo"]))
        self.assertIn("marked provisional", reg["kit"]["decision"])
        self.assertEqual(self.errors(), [])
        from glm_universal import wheels as W
        note = W.provisional_status("KW", path=self.lay.provisional)
        #  The note names the Lean modules as the ledger does, without the
        #  suffix (ITERATION_COST_STUDY.md §5l: a literal suffix in the
        #  wheels package reads as a walk over the whole development).
        self.assertTrue(note.startswith("provisional:") and "its Lean (Demo)" in note, note)
        self.assertEqual(W.provisional_status("wheels/kit_wheel", path=self.lay.provisional), note)
        self.assertIsNone(W.provisional_status("W5", path=self.lay.provisional))
        report = actions.intake_report(self.lay)
        self.assertEqual((report["parts_provisional"], report["provisional_items"]), (1, 1))

    def test_the_install_is_refused_without_its_conditions(self):
        TestStagedCode.staged_item(self)
        self.edit("kit", stage="tested", measured=None, acceptance=None, lean_build=None)
        self.record_current_pass("kit")
        with self.assertRaises(LedgerError):                       # before Lean written
            actions.provisional("kit", "keep it", self.lay, runner=_passing)
        self.edit("kit", stage="lean_written")
        with self.assertRaises(LedgerError):                       # no decision
            actions.provisional("kit", "  ", self.lay, runner=_passing)
        report = actions.provisional("kit", "keep it", self.lay, runner=_failing)
        self.assertFalse(report["ok"])                              # a failing test
        self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())
        self.assertEqual(self.record("kit")["parts"][0]["status"], "staged")
        self.assertEqual(ledger.load_provisional(self.lay), {})

    def test_check_holds_the_register_and_the_ledger_together(self):
        self.assertTrue(self.provisional_item()["ok"])
        reg = ledger.load_provisional(self.lay)
        ledger.save_provisional({}, self.lay)
        self.assertTrue(any("no entry in the register" in e for e in self.errors()))
        ledger.save_provisional(dict(reg, ghost=dict(reg["kit"])), self.lay)
        self.assertTrue(any("lists ghost" in e for e in self.errors()))
        ledger.save_provisional({"kit": dict(reg["kit"], modules=["wheels/other"])}, self.lay)
        self.assertTrue(any("the register lists modules" in e for e in self.errors()))
        ledger.save_provisional({"kit": dict(reg["kit"], decision="")}, self.lay)
        self.assertTrue(any("no decision" in e for e in self.errors()))
        ledger.save_provisional(reg, self.lay)
        self.assertEqual(self.errors(), [])
        self.edit("kit", stage="tested")
        self.assertTrue(any("only at Lean written or beyond" in e for e in self.errors()))
        self.edit("kit", stage="lean_written")
        (self.lay.package / "wheels" / "kit_wheel.py").unlink()
        self.assertTrue(any("not in the package" in e for e in self.errors()))

    def test_absorption_confirms_the_parts_and_clears_the_register(self):
        self.assertTrue(self.provisional_item()["ok"])
        self.edit("kit", stage="measured", lean_build="scratch",
                  measured="DEMO_STUDY: 3 of 3 marks", acceptance=dict(ACCEPT_DEMO))
        self.assertFalse(actions.advance("kit", "absorbed", self.lay, runner=_passing)["ok"])
        self.assertIn("kit", ledger.load_provisional(self.lay))     # no build record yet
        self.write_evidence()
        report = actions.advance("kit", "absorbed", self.lay, runner=_passing)
        self.assertTrue(report["ok"], report["problems"])
        rec = self.record("kit")
        self.assertEqual(rec["path"], "done/kit")
        self.assertEqual(rec["parts"][0]["status"], "absorbed")
        self.assertIn("provisional until", rec["parts"][0]["note"])
        self.assertEqual(ledger.load_provisional(self.lay), {})
        self.assertEqual(self.errors(), [])

    def test_absorb_staged_confirms_the_parts_and_leaves_the_open_ones(self):
        self.assertTrue(self.provisional_item(open_part=True)["ok"])
        self.promote_to_measured()
        report = actions.absorb_staged("kit", self.lay, runner=_passing)
        self.assertTrue(report["ok"], report["problems"])
        rec = self.record("kit")
        self.assertEqual(rec["path"], "ToDo/kit")
        self.assertEqual([p["status"] for p in rec["parts"]], ["absorbed", "open"])
        self.assertEqual(ledger.load_provisional(self.lay), {})
        self.assertEqual(self.errors(), [])
        with self.assertRaises(LedgerError):
            actions.absorb_staged("kit", self.lay, runner=_passing)       # nothing left

    def test_a_provisional_part_never_stands_in_done(self):
        self.assertTrue(self.provisional_item()["ok"])
        shutil.move(str(self.lay.todo / "kit"), str(self.lay.done / "kit"))
        self.edit("kit", path="done/kit", stage="absorbed")
        errors = self.errors()
        self.assertTrue(any("provisional part(s)" in e for e in errors), errors)


class TestAbsorbAhead(Scratch):
    """By the owner's decision of 1 November 2026 an item that has passed every
    gate but the build record may be absorbed on its measurements and a
    standalone Lean check: it is filed in ``done/`` with ``ahead_of_build``
    (or, with parts still open, only its ready parts are absorbed and it stays
    in ``ToDo/``), its register entry says the owner's build has still to
    confirm it, and ``confirm-build`` ends that state when the build record
    verifies it."""

    DECISION = "absorb the ones that measurably help now"

    def ahead_item(self, provisional_first: bool = True, open_part: bool = False) -> None:
        if provisional_first:
            self.assertTrue(TestProvisionalCode.provisional_item(self, open_part=open_part)["ok"])
        else:
            TestStagedCode.staged_item(self, open_part=open_part)
        self.edit("kit", stage="lean_written", lean_build=None,
                  measured="DEMO_STUDY: 3 of 3 marks", acceptance=dict(ACCEPT_DEMO))
        self.record_current_pass("kit")

    def absorb(self, **kw) -> dict:
        args = dict(standalone=["Demo"], check="built on its own with a newer Lean")
        args.update(kw)
        return actions.absorb_ahead("kit", self.DECISION, args.pop("standalone"),
                                    args.pop("check"), self.lay, runner=_passing, **args)

    def test_absorption_ahead_files_the_item_and_keeps_the_note(self):
        self.ahead_item()
        report = self.absorb()
        self.assertTrue(report["ok"], report["problems"])
        rec = self.record("kit")
        self.assertEqual((rec["path"], rec["stage"]), ("done/kit", "absorbed"))
        self.assertNotIn("lean_build", rec)
        self.assertEqual(rec[ledger.AHEAD_FIELD]["standalone"], ["Demo"])
        self.assertIn("confirm-build kit", rec["next_step"])
        self.assertEqual(rec["parts"][0]["status"], "absorbed")
        self.assertIn("absorbed ahead of the build", rec["parts"][0]["note"])
        reg = ledger.load_provisional(self.lay)
        self.assertEqual(reg["kit"]["state"], ledger.AHEAD_STATE)
        self.assertEqual((reg["kit"]["modules"], reg["kit"]["wheels"]),
                         (["wheels/kit_wheel"], ["KW"]))       # the wheels carried over
        self.assertEqual(reg["kit"]["decision"], self.DECISION)
        self.assertEqual(self.errors(), [])
        warnings = gates.check(ledger.load(self.lay), self.lay)["warnings"]
        self.assertTrue(any("absorbed ahead of the build" in w for w in warnings), warnings)
        self.assertFalse(any("installed provisionally" in w for w in warnings), warnings)
        from glm_universal import wheels as W
        note = W.provisional_status("KW", path=self.lay.provisional)
        self.assertTrue(note.startswith(W.AHEAD_STATE + ":"), note)
        self.assertIn("has still to confirm its Lean (Demo)", note)
        self.assertEqual(W.AHEAD_STATE, ledger.AHEAD_STATE)

    def test_staged_code_is_installed_by_the_absorption(self):
        self.ahead_item(provisional_first=False)
        report = self.absorb(wheels=["KW"])
        self.assertTrue(report["ok"], report["problems"])
        self.assertEqual((self.lay.package / "wheels" / "kit_wheel.py").read_text(), "VALUE = 7\n")
        self.assertFalse((self.lay.done / "kit" / "staged").exists())
        self.assertEqual(self.errors(), [])

    def test_the_absorption_is_refused_without_its_conditions(self):
        self.ahead_item()
        with self.assertRaises(LedgerError):                    # no decision
            actions.absorb_ahead("kit", "  ", ["Demo"], "how", self.lay, runner=_passing)
        with self.assertRaises(LedgerError):                    # no standalone check
            actions.absorb_ahead("kit", self.DECISION, [], "how", self.lay, runner=_passing)
        with self.assertRaises(LedgerError):
            actions.absorb_ahead("kit", self.DECISION, ["Demo"], " ", self.lay, runner=_passing)
        report = self.absorb(standalone=["Other"])              # not the item's own Lean
        self.assertFalse(report["ok"])
        self.assertTrue(any("not one of the record's Lean files" in p
                            for p in report["problems"]), report["problems"])
        self.edit("kit", acceptance=None)                       # no acceptance decision
        self.assertFalse(self.absorb()["ok"])
        self.edit("kit", acceptance=dict(ACCEPT_DEMO))
        report = actions.absorb_ahead("kit", self.DECISION, ["Demo"], "how", self.lay,
                                      runner=_failing)          # a failing test
        self.assertFalse(report["ok"])
        rec = self.record("kit")
        self.assertEqual((rec["path"], rec["stage"]), ("ToDo/kit", "lean_written"))
        self.assertNotIn(ledger.AHEAD_FIELD, rec)
        self.assertNotIn("state", ledger.load_provisional(self.lay)["kit"])
        self.edit("kit", stage="tested")
        with self.assertRaises(LedgerError):                    # before Lean written
            self.absorb()

    def test_with_an_open_part_only_the_ready_parts_are_absorbed(self):
        # The pattern of absorb-staged: the provisional part is absorbed ahead
        # of the build, the open part stays open, and the item stays in ToDo/.
        self.ahead_item(open_part=True)
        report = self.absorb()
        self.assertTrue(report["ok"], report["problems"])
        self.assertTrue(report["partial"])
        rec = self.record("kit")
        self.assertEqual((rec["path"], rec["stage"]), ("ToDo/kit", "lean_written"))
        self.assertEqual([p["status"] for p in rec["parts"]], ["absorbed", "open"])
        self.assertIn("the notes", rec["next_step"])
        self.assertIn("confirm-build kit", rec["next_step"])
        reg = ledger.load_provisional(self.lay)
        self.assertEqual(reg["kit"]["state"], ledger.AHEAD_STATE)
        self.assertEqual(reg["kit"]["modules"], ["wheels/kit_wheel"])
        self.assertEqual(self.errors(), [])
        self.write_evidence()
        report = actions.confirm_build("kit", self.lay)
        self.assertTrue(report["ok"], report["problems"])
        rec = self.record("kit")
        self.assertEqual((rec["path"], rec["stage"]), ("ToDo/kit", "lean_written"))
        self.assertEqual(ledger.load_provisional(self.lay), {})
        self.assertEqual(self.errors(), [])

    def test_only_open_parts_refuse(self):
        self.ahead_item(open_part=True)
        rec_parts = [dict(p, status="open") for p in self.record("kit")["parts"]]
        self.edit("kit", parts=rec_parts)
        ledger.save_provisional({}, self.lay)
        with self.assertRaises(LedgerError):
            self.absorb()

    def test_check_holds_the_ahead_record_and_the_register_together(self):
        self.ahead_item()
        self.assertTrue(self.absorb()["ok"])
        reg = ledger.load_provisional(self.lay)
        ledger.save_provisional({}, self.lay)
        self.assertTrue(any("no entry in the register" in e for e in self.errors()))
        ledger.save_provisional({"kit": dict(reg["kit"], state="provisional")}, self.lay)
        self.assertTrue(any("not 'absorbed ahead of the build'" in e for e in self.errors()))
        ledger.save_provisional({"kit": dict(reg["kit"], modules=["wheels/other"])}, self.lay)
        self.assertTrue(any("not among the record's absorbed" in e for e in self.errors()))
        ledger.save_provisional(reg, self.lay)
        self.assertEqual(self.errors(), [])
        ahead = dict(self.record("kit")[ledger.AHEAD_FIELD])
        self.edit("kit", ahead_of_build=dict(ahead, check=""))
        self.assertTrue(any("has no check" in e for e in self.errors()))
        self.edit("kit", ahead_of_build=None)
        errors = self.errors()
        self.assertTrue(any("no lean_build entry" in e for e in errors), errors)
        self.assertTrue(any("confirm-build removes the entry" in e for e in errors), errors)

    def test_the_build_record_confirms_the_absorption(self):
        self.ahead_item()
        self.assertTrue(self.absorb()["ok"])
        report = actions.confirm_build("kit", self.lay)
        self.assertFalse(report["ok"])                          # no build record yet
        self.assertIn("kit", ledger.load_provisional(self.lay))
        self.write_evidence()
        warnings = gates.check(ledger.load(self.lay), self.lay)["warnings"]
        self.assertTrue(any("run `python3 -m glm_universal.intake confirm-build kit`" in w
                            for w in warnings), warnings)
        report = actions.confirm_build("kit", self.lay)
        self.assertTrue(report["ok"], report["problems"])
        rec = self.record("kit")
        self.assertNotIn(ledger.AHEAD_FIELD, rec)
        self.assertIn("confirms the absorption ahead of the build", rec["lean_build"])
        self.assertIn("confirmed by the build record", rec["parts"][0]["note"])
        self.assertEqual(ledger.load_provisional(self.lay), {})
        self.assertEqual(self.errors(), [])
        with self.assertRaises(LedgerError):
            actions.confirm_build("kit", self.lay)


class TestTheStudyGate(Scratch):
    """study_drafted needs the .md and a valid .yaml manifest in step with it."""

    def test_a_missing_manifest_refuses(self):
        (self.lay.studies / "DEMO_STUDY.yaml").unlink()
        problems = gates.study_problems("DEMO_STUDY", self.lay)
        self.assertTrue(any("does not exist" in p for p in problems), problems)
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="study it",
                  stage="triaged", studies=["DEMO_STUDY"])
        report = actions.advance("note", "study_drafted", self.lay, run=False)
        self.assertFalse(report["ok"])

    def test_an_out_of_step_or_invalid_manifest_refuses(self):
        import yaml
        y = self.lay.studies / "DEMO_STUDY.yaml"
        good = yaml.safe_load(y.read_text(encoding="utf-8"))
        self.assertEqual(gates.study_problems("DEMO_STUDY", self.lay), [])
        changed = dict(good, verdict="No: 0 of 3.")
        y.write_text(yaml.safe_dump(changed), encoding="utf-8")
        self.assertTrue(any("verdict is not the .md's" in p
                            for p in gates.study_problems("DEMO_STUDY", self.lay)))
        y.write_text(yaml.safe_dump(dict(good, id="OTHER_STUDY")), encoding="utf-8")
        self.assertTrue(any("names id" in p for p in gates.study_problems("DEMO_STUDY", self.lay)))
        y.write_text(yaml.safe_dump(dict(good, schema="something/v0")), encoding="utf-8")
        self.assertTrue(any("does not validate" in p
                            for p in gates.study_problems("DEMO_STUDY", self.lay)))
        y.write_text("id: [unclosed\n", encoding="utf-8")
        self.assertTrue(any("does not parse" in p
                            for p in gates.study_problems("DEMO_STUDY", self.lay)))

    def test_a_study_without_tier0_refuses(self):
        md = _write(self.lay.studies / "BARE_STUDY.md", "# Bare\n\nNo tier 0 here.\n")
        _write(self.lay.studies / "BARE_STUDY.yaml", actions.manifest_text(md))
        self.assertTrue(any("no tier-0 block" in p
                            for p in gates.study_problems("BARE_STUDY", self.lay)))


class TestTheMeasuredGate(Scratch):
    """measured needs a finished, closed study and an acceptance decision."""

    def rec(self, **fields) -> dict:
        base = {"id": "note", "path": "ToDo/note.md", "stage": "lean_verified",
                "measured": "DEMO_STUDY: 3 of 3 marks", "acceptance": dict(ACCEPT_DEMO)}
        base.update(fields)
        return base

    def test_a_finished_accepted_measurement_passes(self):
        self.assertEqual(gates.measurement_problems(self.rec(), self.lay, promotion=True), [])

    def test_the_draft_scaffold_is_refused(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="study it",
                  stage="triaged")
        md, _ = actions.scaffold("note", self.lay)
        rec = self.rec(measured=f"{md.stem}: 3 of 3 marks",
                       acceptance=dict(ACCEPT_DEMO, study=md.stem))
        problems = gates.measurement_problems(rec, self.lay, promotion=True)
        self.assertTrue(any("still a draft" in p for p in problems), problems)
        self.assertTrue(any("no measured deciding figure" in p for p in problems), problems)
        self.assertTrue(any("not closed" in p or "is open" in p for p in problems), problems)
        with self.assertRaises(LedgerError):
            actions.accept("note", "anything", "3 of 3 marks", self.lay, study=md.stem)
        self.assertNotIn("acceptance", self.record("note"))

    def test_a_marker_quoted_as_code_is_not_draft_text(self):
        md = self.lay.studies / "DEMO_STUDY.md"
        md.write_text(STUDY + "\nThe scaffold marks unwritten text `TO WRITE`.\n", encoding="utf-8")
        self.assertEqual(gates.measurement_problems(self.rec(), self.lay, promotion=True), [])
        md.write_text(STUDY + "\nTO WRITE: the controls.\n", encoding="utf-8")
        self.assertTrue(any("still a draft" in p for p in
                            gates.measurement_problems(self.rec(), self.lay, promotion=True)))

    def test_a_missing_or_failed_acceptance_is_refused(self):
        def problems(**fields):
            return gates.measurement_problems(self.rec(**fields), self.lay, promotion=True)
        self.assertTrue(any("no acceptance decision" in p for p in problems(acceptance=None)))
        self.assertTrue(any("decision is 'reject'" in p
                            for p in problems(acceptance=dict(ACCEPT_DEMO, decision="reject"))))
        self.assertTrue(any("criterion is not stated" in p for p in problems(
            acceptance=dict(ACCEPT_DEMO, criterion="every answer is perfect"))))
        self.assertTrue(any("has no result" in p
                            for p in problems(acceptance=dict(ACCEPT_DEMO, result="none yet"))))
        self.assertTrue(any("not the measured" in p for p in problems(
            acceptance=dict(ACCEPT_DEMO, study="MARKED_STUDY"))))

    def test_marks_must_be_declared_and_met(self):
        marked = {"study": "MARKED_STUDY", "criterion": "The demo is accepted when M1 is met",
                  "result": "3 of 3 answers right, 1 wrong answer", "decision": "accept"}

        def problems(**acc):
            return gates.measurement_problems(
                self.rec(measured="MARKED_STUDY: 3 of 3 answers right",
                         acceptance=dict(marked, **acc)), self.lay, promotion=True)
        self.assertTrue(any("declares marks" in p for p in problems()))
        self.assertTrue(any("M2 is not met" in p for p in problems(marks=["M1", "M2"])))
        self.assertTrue(any("M9 is not declared" in p for p in problems(marks=["M9"])))
        self.assertEqual(problems(marks=["M1"]), [])

    def test_a_negative_or_open_study_is_refused(self):
        import yaml
        y = self.lay.studies / "DEMO_STUDY.yaml"
        data = yaml.safe_load(y.read_text(encoding="utf-8"))
        for status, needle in (("negative", "is negative"), ("open", "is open")):
            y.write_text(yaml.safe_dump(dict(data, status=status)), encoding="utf-8")
            self.assertTrue(any(needle in p for p in gates.measurement_problems(
                self.rec(), self.lay, promotion=True)), status)

    def test_legacy_absorption_only_for_finished_records_and_never_on_promotion(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="",
                  stage="absorbed", path="done/note.md", studies=["DEMO_STUDY"],
                  tests=["tests/test_demo_mod.py"], lean=["Demo"], lean_build="scratch",
                  measured="DEMO_STUDY: 3 of 3 marks", absorbed_into=["reasoning/demo_mod"])
        self.record_current_pass("note")
        (self.lay.todo / "note.md").rename(self.lay.done / "note.md")
        self.assertTrue(any("no acceptance decision" in e for e in self.errors()))
        self.edit("note", legacy_absorption="absorbed by an earlier round")
        result = gates.check(ledger.load(self.lay), self.lay)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("before acceptance decisions were recorded" in w
                            for w in result["warnings"]))
        rec = self.record("note")
        self.assertTrue(any("no acceptance decision" in p for p in
                            gates.measurement_problems(rec, self.lay, promotion=True)))
        # The same field on an open record is an error, and does not stand in
        # for the decision.
        self.edit("note", stage="measured", path="ToDo/note.md")
        (self.lay.done / "note.md").rename(self.lay.todo / "note.md")
        errors = self.errors()
        self.assertTrue(any("legacy_absorption is only for" in e for e in errors), errors)
        self.assertTrue(any("no acceptance decision" in e for e in errors), errors)


class TestCurrentTestResults(Scratch):
    """A promotion accepts only a pass taken against the code as it now stands."""

    def staged_item(self) -> None:
        folder = self.lay.material / "kit"
        _write(folder / "README.md", "a kit\n")
        actions.register(str(folder), self.lay)
        pkg = self.lay.package.relative_to(self.lay.root)
        item = self.lay.todo / "kit"
        _write(item / "staged" / pkg / "wheels" / "kit_wheel.py", "VALUE = 7\n")
        _write(item / "staged" / pkg / "tests" / "test_kit_wheel.py",
               "from glm_universal.wheels.kit_wheel import VALUE\n\n"
               "def test_value():\n    assert VALUE == 7\n")
        ref = f"staged:{pkg}/tests/test_kit_wheel.py"
        self.edit("kit", kind="code", offers="a wheel", next_step="build it", stage="measured",
                  studies=["DEMO_STUDY"], tests=[ref], lean=["Demo"], lean_build="scratch",
                  measured="DEMO_STUDY: 3 of 3 marks", acceptance=dict(ACCEPT_DEMO),
                  absorbed_into=["wheels/kit_wheel"],
                  parts=[{"part": "the wheel", "status": "staged",
                          "absorbed_into": ["wheels/kit_wheel"]}])
        self.record_current_pass("kit")
        self.write_evidence()

    def test_a_change_to_the_package_makes_a_pass_stale(self):
        self.staged_item()
        rec = self.record("kit")
        self.assertEqual(gates.stale_results(rec, self.lay), [])
        _write(self.lay.package / "reasoning" / "demo_mod.py", "X = 2\n")
        self.assertEqual(gates.stale_results(self.record("kit"), self.lay), rec["tests"])
        warnings = gates.check(ledger.load(self.lay), self.lay)["warnings"]
        self.assertTrue(any("not taken against the code as it now stands" in w for w in warnings))

    def test_a_change_to_the_staged_code_makes_a_pass_stale(self):
        self.staged_item()
        pkg = self.lay.package.relative_to(self.lay.root)
        _write(self.lay.todo / "kit" / "staged" / pkg / "wheels" / "kit_wheel.py", "VALUE = 8\n")
        self.assertTrue(gates.stale_results(self.record("kit"), self.lay))

    def test_a_stale_pass_is_refused_without_a_run(self):
        self.staged_item()
        _write(self.lay.package / "reasoning" / "demo_mod.py", "X = 2\n")
        report = actions.advance("kit", "absorbed", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("run it again" in p for p in report["problems"]), report["problems"])
        self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())
        report = actions.absorb_staged("kit", self.lay, run=False)
        self.assertFalse(report["ok"])
        self.assertTrue(any("run it again" in p for p in report["problems"]), report["problems"])
        self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())

    def test_absorption_runs_every_test_again_before_installing(self):
        self.staged_item()
        report = actions.advance("kit", "absorbed", self.lay, runner=_failing)
        self.assertFalse(report["ok"])                      # the recorded pass is not enough
        self.assertEqual([r["result"] for r in report["ran"]], ["fail"])
        self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())
        self.assertEqual(self.record("kit")["test_results"][-1]["result"], "fail")
        report = actions.advance("kit", "absorbed", self.lay, runner=_passing)
        self.assertTrue(report["ok"], report["problems"])
        self.assertEqual([r["result"] for r in report["ran"]], ["pass"])
        self.assertTrue((self.lay.package / "wheels" / "kit_wheel.py").is_file())
        last = self.record("kit")["test_results"][-1]
        self.assertTrue(last["fingerprint"])

    def test_absorb_staged_runs_every_test_again(self):
        self.staged_item()
        report = actions.absorb_staged("kit", self.lay, runner=_failing)
        self.assertFalse(report["ok"])
        self.assertFalse((self.lay.package / "wheels" / "kit_wheel.py").exists())
        report = actions.absorb_staged("kit", self.lay, runner=_passing)
        self.assertTrue(report["ok"], report["problems"])
        self.assertTrue((self.lay.package / "wheels" / "kit_wheel.py").is_file())

    def test_a_later_promotion_reruns_only_stale_tests(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="build it",
                  stage="tested", studies=["DEMO_STUDY"], tests=["tests/test_demo_mod.py"],
                  lean=["Demo"])
        self.record_current_pass("note")
        ok = lambda lay, t: (True, "OK")
        report = actions.advance("note", "lean_written", self.lay, runner=_failing,
                                 lean_checker=ok)
        self.assertTrue(report["ok"], report["problems"])     # current: nothing re-run
        self.assertEqual([r["test"] for r in report["ran"]], ["lean_check"])
        _write(self.lay.package / "reasoning" / "demo_mod.py", "X = 3\n")
        self.write_evidence()
        report = actions.advance("note", "lean_verified", self.lay, runner=_failing)
        self.assertFalse(report["ok"])                        # stale, re-run, failed
        self.assertEqual([r["result"] for r in report["ran"]], ["fail"])
        report = actions.advance("note", "lean_verified", self.lay, runner=_passing)
        self.assertTrue(report["ok"], report["problems"])

    def test_retest_records_current_results_without_moving(self):
        self.staged_item()
        self.assertEqual(actions.retest("kit", self.lay, only_stale=True, runner=_failing)["ran"],
                         [])                                # all current: nothing to run
        _write(self.lay.package / "reasoning" / "demo_mod.py", "X = 4\n")
        ran = actions.retest("kit", self.lay, only_stale=True, runner=_passing)["ran"]
        self.assertEqual([r["result"] for r in ran], ["pass"])
        rec = self.record("kit")
        self.assertEqual(rec["stage"], "measured")
        self.assertEqual(gates.stale_results(rec, self.lay), [])


class TestTheFallbackRunner(Scratch):
    """Without pytest, a package test passes only when its tests ran and
    passed: plain test functions are run, a fixture refuses, an empty file
    fails (``python3 -m unittest`` would collect none of them and pass)."""

    FILES = {
        "test_plain_fail.py": "def test_wrong():\n    assert 1 == 2\n",
        "test_plain_pass.py": "def test_right():\n    assert 1 == 1\n",
        "test_nothing.py": "X = 1\n",
        "test_fixture.py": "def test_needs(tmp_path):\n    assert tmp_path\n",
        "test_class_fail.py": "class TestThing:\n    def test_a(self):\n        assert False\n",
        "test_mixed.py": ("import unittest\n\nclass T(unittest.TestCase):\n"
                          "    def test_a(self):\n        self.assertTrue(True)\n\n"
                          "def test_b():\n    assert True\n"),
        "test_all_skipped.py": ("import unittest\n\n@unittest.skip('no')\n"
                                "class T(unittest.TestCase):\n    def test_a(self):\n        pass\n"),
        #  A passing test whose class teardown check fails: the file fails.
        "test_teardown_fail.py": ("class TestThing:\n    def test_a(self):\n        assert True\n\n"
                                  "    @classmethod\n    def teardown_class(cls):\n"
                                  "        assert False, 'the teardown check'\n"),
        #  The hooks in pytest's order, an inherited test collected, and the
        #  module teardown checking that the class teardown ran.
        "test_hooks_order.py": ("order = []\n\ndef setup_module(module):\n    order.append('sm')\n\n"
                                "def teardown_module(module):\n    assert order[-1] == 'tc', order\n\n"
                                "class Base:\n    def test_inherited(self):\n        order.append('inh')\n\n"
                                "class TestThing(Base):\n    @classmethod\n    def setup_class(cls):\n"
                                "        order.append('sc')\n\n    def test_a(self):\n"
                                "        assert order[:2] == ['sm', 'sc'], order\n\n"
                                "    @classmethod\n    def teardown_class(cls):\n        order.append('tc')\n\n"
                                "def test_fn():\n    assert order[0] == 'sm'\n"),
    }

    def setUp(self) -> None:
        super().setUp()
        for name, text in self.FILES.items():
            _write(self.lay.package / "tests" / name, text)
        from unittest import mock
        patcher = mock.patch.object(actions, "_pytest_available", lambda: False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def result(self, name: str):
        return actions.run_test(f"tests/{name}", {"id": "x", "path": "ToDo/x"}, self.lay,
                                timeout=300)

    def test_the_command_is_the_fallback_without_pytest(self):
        cmd = actions._package_test_command(self.lay.package / "tests" / "test_plain_pass.py",
                                            self.lay)
        self.assertIn("glm_universal.intake.fallback_tests", cmd)
        self.assertNotIn("unittest", cmd)

    def test_each_file_is_judged_by_what_ran(self):
        expected = {"test_plain_fail.py": "fail", "test_plain_pass.py": "pass",
                    "test_nothing.py": "fail", "test_fixture.py": "fail",
                    "test_class_fail.py": "fail", "test_mixed.py": "pass",
                    "test_all_skipped.py": "fail", "test_teardown_fail.py": "fail",
                    "test_hooks_order.py": "pass"}
        got = {name: self.result(name) for name in expected}
        self.assertEqual({k: v[0] for k, v in got.items()}, expected, got)
        self.assertIn("exit 5", got["test_nothing.py"][1])
        self.assertIn("needs pytest", got["test_fixture.py"][1])
        self.assertIn("2 passed", got["test_mixed.py"][1])
        self.assertIn("setup/teardown", got["test_teardown_fail.py"][1])
        self.assertIn("3 passed", got["test_hooks_order.py"][1])

    def test_a_failing_class_teardown_refuses_the_promotion(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="test it",
                  stage="study_drafted", studies=["DEMO_STUDY"],
                  tests=["tests/test_teardown_fail.py"])
        report = actions.advance("note", "tested", self.lay, timeout=300)
        self.assertFalse(report["ok"])
        self.assertEqual(report["ran"][0]["result"], "fail")
        self.assertEqual(self.record("note")["stage"], "study_drafted")

    def test_a_failing_plain_test_refuses_the_promotion(self):
        self.new_item()
        self.edit("note", kind="concept note", offers="an idea", next_step="test it",
                  stage="study_drafted", studies=["DEMO_STUDY"],
                  tests=["tests/test_plain_fail.py"])
        report = actions.advance("note", "tested", self.lay, timeout=300)
        self.assertFalse(report["ok"])
        self.assertEqual(report["ran"][0]["result"], "fail")
        self.assertEqual(self.record("note")["stage"], "study_drafted")
        self.edit("note", tests=["tests/test_nothing.py"])
        self.assertFalse(actions.advance("note", "tested", self.lay, timeout=300)["ok"])
        self.edit("note", tests=["tests/test_plain_pass.py"])
        self.assertTrue(actions.advance("note", "tested", self.lay, timeout=300)["ok"])


# ---------------------------------------------------------------------------
# The owner's two scripts carry their result in their exit status
# ---------------------------------------------------------------------------
#
# ``scripts/rebuild_lean.sh`` (the Lean rebuild; its step 7 writes the build
# record the Lean verified gate reads) and ``scripts/check_repository.sh``
# (every Python gate) log each step and end with a summary line; a caller also
# needs the exit status to say whether they passed.  Each test copies a script
# into a scratch tree holding a stand-in package (``glm_universal`` modules
# that exit 0, or 1 when named in ``FAKE_FAIL``) and stand-in ``lake``,
# ``elan`` and ``lean`` commands, runs it with ``bash``, and checks the exit
# status, the log's result line and that the log is still written.  Nothing
# in the repository is run or written.

REPO = C.PACKAGE_ROOT.parent.parent
BASH = shutil.which("bash")

#: A stand-in module: exits 1 when its name is listed in FAKE_FAIL.
_FAKE_MAIN = textwrap.dedent('''\
    import os, sys
    NAME = {name!r}
    sys.exit(1 if NAME in os.environ.get("FAKE_FAIL", "").split(",") else 0)
''')

_FAKE_LEAN_CHECK = textwrap.dedent('''\
    import os, sys

    def _strip_comments(text):
        return text

    if __name__ == "__main__":
        args = sys.argv[1:]
        fail = os.environ.get("FAKE_FAIL", "").split(",")
        if "--write-build-evidence" in args:
            exits = [args[args.index(k) + 1] for k in ("--static-exit", "--build-exit", "--sorry-exit")]
            sys.exit(0 if all(e == "0" for e in exits) and "record" not in fail else 1)
        sys.exit(1 if "lean_check" in fail else 0)
''')

_FAKE_CONSTANTS = textwrap.dedent('''\
    from pathlib import Path
    LEAN_SOURCE_DIR = Path(__file__).resolve().parents[1] / "lean"
    LEAN_LIBRARY = "RequestProject"
''')

_FAKE_COMMAND = textwrap.dedent('''\
    #!/usr/bin/env bash
    # a stand-in for {name}: `lake build` fails when FAKE_FAIL names build,
    # `lake exe cache get` when it names cache
    case ",${{FAKE_FAIL:-}}," in
      *,build,*) [ "${{1:-}}" = build ] && exit 1 ;;
    esac
    case ",${{FAKE_FAIL:-}}," in
      *,cache,*) [ "${{1:-}}" = exe ] && exit 1 ;;
    esac
    echo "{name} (stand-in)"
    exit 0
''')


def _write_mode(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


@unittest.skipIf(BASH is None, "bash is not installed")
class ScriptCase(unittest.TestCase):
    """A scratch tree for one of the owner's scripts."""

    script = ""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="glm-owner-script-"))
        (self.tmp / "scripts").mkdir()
        shutil.copy2(REPO / "scripts" / self.script, self.tmp / "scripts" / self.script)
        pkg = self.tmp / "src" / "glm_universal"
        _write_mode(pkg / "__init__.py", "")
        _write_mode(pkg / "lean_check.py", _FAKE_LEAN_CHECK)
        _write_mode(pkg / "constants.py", _FAKE_CONSTANTS)
        _write_mode(pkg / "tools.py", _FAKE_MAIN.format(name="tools"))
        for sub in ("intake", "corpus", "evaluation"):
            _write_mode(pkg / sub / "__init__.py", "")
            _write_mode(pkg / sub / "__main__.py", _FAKE_MAIN.format(name=sub))
        _write_mode(self.tmp / "src" / "GLM.py", _FAKE_MAIN.format(name="glm"))
        _write_mode(self.tmp / "src" / "lean" / "RequestProject" / "A.lean",
                    "theorem a : True := trivial\n")
        _write_mode(self.tmp / "lean-toolchain", "leanprover/lean4:v0.0.0-stand-in\n")
        for cmd in ("lake", "elan", "lean"):
            _write_mode(self.tmp / "bin" / cmd, _FAKE_COMMAND.format(name=cmd), 0o755)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_script(self, *args: str, fail: str = "") -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PATH"] = f"{self.tmp / 'bin'}{os.pathsep}{env.get('PATH', '')}"
        env["FAKE_FAIL"] = fail
        env.pop("PYTHONPATH", None)
        return subprocess.run([BASH, str(self.tmp / "scripts" / self.script), *args],
                              cwd=str(self.tmp), env=env, capture_output=True, text=True,
                              timeout=300)

    def latest_log(self, name: str) -> str:
        return (self.tmp / "scripts" / "logs" / name).read_text(encoding="utf-8")


class TestRebuildLean(ScriptCase):
    """``scripts/rebuild_lean.sh`` exits 1 when a required step fails."""

    script = "rebuild_lean.sh"

    def test_all_steps_passing_exits_zero(self):
        p = self.run_script()
        self.assertEqual(p.returncode, 0, p.stdout[-2000:])
        log = self.latest_log("lean_build_latest.log")
        self.assertIn("== result: PASSED", log)
        self.assertIn("build=0", log)

    def test_a_failed_build_exits_non_zero_and_still_logs(self):
        p = self.run_script(fail="build")
        self.assertEqual(p.returncode, 1, p.stdout[-2000:])
        log = self.latest_log("lean_build_latest.log")
        self.assertIn("build=1", log)
        self.assertIn("== result: FAILED:", log)
        self.assertIn("build", log.rsplit("== result: FAILED:", 1)[1])
        self.assertIn("citation=skipped", log)

    def test_a_sorry_exits_non_zero(self):
        _write_mode(self.tmp / "src" / "lean" / "RequestProject" / "B.lean",
                    "theorem b : 1 = 2 := by sorry\n")
        p = self.run_script()
        self.assertEqual(p.returncode, 1, p.stdout[-2000:])
        self.assertIn("sorry=1", self.latest_log("lean_build_latest.log"))

    def test_a_failed_static_check_citation_or_record_exits_non_zero(self):
        for fail in ("lean_check", "record", "tools"):
            p = self.run_script(fail=fail)
            self.assertEqual(p.returncode, 1, (fail, p.stdout[-2000:]))

    def test_a_failed_cache_download_alone_is_not_a_failure(self):
        p = self.run_script(fail="cache")
        self.assertEqual(p.returncode, 0, p.stdout[-2000:])
        self.assertIn("cache=1", self.latest_log("lean_build_latest.log"))


class TestCheckRepository(ScriptCase):
    """``scripts/check_repository.sh`` exits 1 when any gate fails."""

    script = "check_repository.sh"

    def test_all_gates_passing_exits_zero(self):
        p = self.run_script("--quick")
        self.assertEqual(p.returncode, 0, p.stdout[-2000:])
        log = self.latest_log("repository_check_latest.log")
        self.assertIn("== result: PASSED", log)
        self.assertIn("intake=0", log)

    def test_any_failing_gate_exits_non_zero_and_still_logs(self):
        for fail, gate in (("intake", "intake"), ("corpus", "corpus"), ("lean_check", "lean_check"),
                           ("tools", "dates"), ("glm", "smoke")):
            p = self.run_script("--quick", fail=fail)
            self.assertEqual(p.returncode, 1, (fail, p.stdout[-2000:]))
            log = self.latest_log("repository_check_latest.log")
            self.assertIn(f"{gate}=1", log)
            self.assertIn(gate, log.rsplit("== result: FAILED:", 1)[1])

    def test_the_full_run_includes_the_evaluation(self):
        p = self.run_script(fail="evaluation")
        self.assertEqual(p.returncode, 1, p.stdout[-2000:])
        self.assertIn("evaluation=1", self.latest_log("repository_check_latest.log"))


class TestTheRealLedger(unittest.TestCase):
    """The repository's own ledger and folders (read only)."""

    @classmethod
    def setUpClass(cls):
        cls.lay = Layout.default()
        cls.data = ledger.load(cls.lay)

    def test_ledger_and_folders_agree_and_every_stage_has_its_evidence(self):
        result = gates.check(self.data, self.lay)
        self.assertEqual(result["errors"], [])

    def test_every_filed_item_has_one_record(self):
        paths = [r["path"] for r in self.data["items"]]
        self.assertEqual(len(paths), len(set(paths)))
        for path in ledger.folder_items(self.lay):
            self.assertIn(path, paths)
        self.assertEqual(ledger.loose_items(self.lay), [])

    def test_done_is_finished_and_todo_is_open(self):
        for r in self.data["items"]:
            if r["path"].startswith("done/"):
                self.assertIn(r["stage"], ledger.TERMINAL, r["id"])
            else:
                self.assertNotIn(r["stage"], ledger.TERMINAL, r["id"])

    def test_wheels_carry_lean_obligations(self):
        wheels = [w for r in self.data["items"] for w in r.get("wheels", [])]
        self.assertTrue(wheels)
        for w in wheels:
            self.assertTrue(w.get("lean_obligations"), w.get("name"))
            self.assertTrue(w.get("test_result"), w.get("name"))

    def test_the_new_wheels_are_provisional_until_their_build(self):
        from glm_universal import wheels as W
        self.assertEqual(self.lay.provisional, W.PROVISIONAL_REGISTER)
        self.assertEqual(gates.provisional_problems(self.data, self.lay), [])
        reg = ledger.load_provisional(self.lay)
        for item, ids in (("glm_wheels_bundle", ("IW", "MW")),
                          ("cent_compiler_v12", W.CENT_WHEEL_IDS)):
            rec = ledger.record_by_id(self.data, item)
            statuses = {p["status"] for p in rec.get("parts", []) if p.get("absorbed_into")}
            if item in reg and reg[item].get("state") == ledger.AHEAD_STATE:
                # Absorbed ahead of the build by the owner's decision of
                # 1 November 2026 (Phase 186): the parts absorbed, the record
                # carrying its ahead_of_build entry, every answer still marked
                # until confirm-build.
                self.assertIn("absorbed", statuses, item)
                self.assertNotIn("provisional", statuses, item)
                self.assertNotIn("staged", statuses, item)
                self.assertTrue(rec.get(ledger.AHEAD_FIELD), item)
                self.assertEqual(tuple(reg[item]["wheels"]), tuple(ids))
                for wid in ids:
                    note = W.provisional_status(wid)
                    self.assertTrue(note and note.startswith(ledger.AHEAD_STATE), wid)
            elif item in reg:
                # Lean written, the owner's build pending: in the wheels folder,
                # every answer resting on them marked.
                self.assertIn("provisional", statuses, item)
                self.assertNotIn("staged", statuses, item)
                self.assertEqual(tuple(reg[item]["wheels"]), tuple(ids))
                self.assertEqual(rec["path"], f"ToDo/{item}")
                for wid in ids:
                    self.assertTrue(W.provisional_status(wid), wid)
            else:
                self.assertNotIn("provisional", statuses, item)
                for wid in ids:
                    self.assertIsNone(W.provisional_status(wid), wid)
        for wid in ("W1", "W5", "W15"):
            self.assertIsNone(W.provisional_status(wid))
        self.assertEqual(W.provision_wheel("IW").status,
                         W.provisional_status("IW") or "absorbed")

    def test_report_and_cli(self):
        report = actions.intake_report(self.lay)
        self.assertEqual(report["items"], report["todo"] + report["done"])
        self.assertTrue(report["check_ok"])
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(intake_main(["status"]), 0)
            self.assertEqual(intake_main(["check", "--quiet"]), 0)
        self.assertIn(f"{report['items']} items", out.getvalue())


if __name__ == "__main__":
    unittest.main()
