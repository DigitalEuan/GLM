"""Tests for :mod:`glm_universal.signoff`.

The sign-off ledger exists to answer one question cheaply: *has anything this
test file depends on changed since the last time it passed?*  A wrong answer in
one direction wastes a quarter of an hour; a wrong answer in the other direction
is worse, because it reports a suite as green that was never run.  These tests
pin the second kind shut:

* the closure of a unit contains the test file, everything it imports through
  the package, the data files those modules read, and the shared scaffolding;
* the digest changes when any of that changes -- content *or* name -- and does
  not change otherwise;
* a signature is valid only for the digest and interpreter it was taken at, so
  an edit anywhere in the closure makes the unit stale again;
* only ``passed`` signs; a failure is recorded and leaves the unit stale.

Nothing here runs the test suite.  Every test either inspects the plan or works
on a ledger written to a temporary path.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal import integrity
from glm_universal.signoff import checks as C
from glm_universal.signoff import ledger as L


class TestUnits(unittest.TestCase):

    def test_every_test_file_is_a_unit(self):
        names = {p.name for p in L.test_units()}
        self.assertIn("test_signoff.py", names)
        self.assertIn("test_lean_address.py", names)
        self.assertGreater(len(names), 40)

    def test_units_are_in_a_stable_order(self):
        self.assertEqual(L.test_units(), L.test_units())
        self.assertEqual(list(L.test_units()), sorted(L.test_units()))


class TestClosure(unittest.TestCase):

    def closure_names(self, unit: str):
        path = L.TESTS_DIR / unit
        return {p.name for p in L.unit_closure(path)}

    def test_the_closure_contains_the_test_file_itself(self):
        self.assertIn("test_signoff.py", self.closure_names("test_signoff.py"))

    def test_the_closure_follows_imports_through_the_package(self):
        names = self.closure_names("test_lean_address.py")
        self.assertIn("lean_address.py", names)
        # ``lean_address`` imports ``analogy`` and ``integrity``; a change in
        # either can change what the test observes.
        self.assertIn("analogy.py", names)
        self.assertIn("integrity.py", names)

    def test_the_closure_contains_the_data_a_module_reads(self):
        names = self.closure_names("test_lean_address.py")
        self.assertIn("lean_addresses.json", names)

    def test_the_closure_contains_the_shared_scaffolding(self):
        names = self.closure_names("test_signoff.py")
        self.assertIn("__init__.py", names)
        for path in L.scaffolding_paths():
            self.assertIn(path.name, names)

    def test_the_closure_is_a_sorted_set_of_existing_files(self):
        closure = L.unit_closure(L.TESTS_DIR / "test_signoff.py")
        self.assertEqual(len(closure), len(set(closure)))
        self.assertTrue(all(p.is_file() for p in closure))

    def test_computing_a_closure_imports_nothing(self):
        # ``unit_closure`` reads the sources with ``ast``.  A module that was
        # not already imported must not appear in ``sys.modules`` because the
        # closure was computed.
        import sys

        victim = "glm_universal.reasoning.noise_lab"
        was_present = victim in sys.modules
        L.unit_closure(L.TESTS_DIR / "test_noise_lab.py")
        if not was_present:
            self.assertNotIn(victim, sys.modules)


class TestDigests(unittest.TestCase):

    def test_a_unit_digest_is_a_sha256_and_is_reproducible(self):
        path = L.TESTS_DIR / "test_signoff.py"
        first = L.unit_digest(path)
        self.assertEqual(len(first), 64)
        self.assertEqual(first, L.unit_digest(path))
        int(first, 16)  # it is hexadecimal

    def test_different_units_have_different_digests(self):
        a = L.unit_digest(L.TESTS_DIR / "test_signoff.py")
        b = L.unit_digest(L.TESTS_DIR / "test_lean_address.py")
        self.assertNotEqual(a, b)

    def test_content_changes_change_the_tree_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            one = root / "one.py"
            one.write_text("x = 1\n", encoding="utf-8")
            before = L.tree_digest([one], root)
            one.write_text("x = 2\n", encoding="utf-8")
            self.assertNotEqual(before, L.tree_digest([one], root))

    def test_renames_change_the_tree_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            one = root / "one.py"
            one.write_text("x = 1\n", encoding="utf-8")
            before = L.tree_digest([one], root)
            two = root / "two.py"
            one.rename(two)
            self.assertNotEqual(before, L.tree_digest([two], root))

    def test_the_digest_does_not_depend_on_the_order_supplied(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = []
            for i in range(3):
                p = root / f"f{i}.py"
                p.write_text(f"x = {i}\n", encoding="utf-8")
                paths.append(p)
            self.assertEqual(L.tree_digest(paths, root),
                             L.tree_digest(list(reversed(paths)), root))

    def test_the_project_uses_one_hashing_implementation(self):
        data = b"the digest addresses integrity, never meaning"
        self.assertEqual(integrity.sha256_hex(data), integrity.sha256_hex(data))
        self.assertEqual(len(integrity.sha256_hex(data)), 64)

    def test_the_interpreter_is_part_of_a_signature(self):
        tag = L.interpreter_tag()
        self.assertTrue(tag)
        self.assertIn(".", tag)


class TestPlanAndSignature(unittest.TestCase):
    """The state machine: new, signed, changed, failed."""

    @classmethod
    def setUpClass(cls):
        # ``plan`` walks every closure in the suite; compute it once.
        cls.plan_rows = L.plan()

    @property
    def unit(self):
        return next(u for u in self.plan_rows if u.name == "test_signoff.py")

    def signed_book(self, status="passed", digest=None, milliseconds=1000):
        book = {"schema": L.SCHEMA, "python": L.interpreter_tag(), "units": {}}
        return L.sign(self.unit,
                      {"status": status, "tests": 3, "subtests": 0,
                       "failures": 0, "milliseconds": milliseconds},
                      dict(book, units=dict(book["units"])))

    def state_of(self, book):
        return next(u.state for u in L.plan(book) if u.name == self.unit.name)

    def test_an_unknown_unit_is_new(self):
        empty = {"schema": L.SCHEMA, "python": L.interpreter_tag(), "units": {}}
        self.assertEqual(self.state_of(empty), "new")

    def test_a_passing_run_signs_the_unit(self):
        self.assertEqual(self.state_of(self.signed_book()), "signed")

    def test_a_failing_run_is_recorded_but_does_not_sign(self):
        book = self.signed_book(status="failed")
        self.assertEqual(self.state_of(book), "failed")
        self.assertEqual(book["units"][self.unit.name]["status"], "failed")

    def test_an_edit_in_the_closure_makes_a_signed_unit_stale(self):
        book = self.signed_book()
        book["units"][self.unit.name]["digest"] = "0" * 64
        self.assertEqual(self.state_of(book), "changed")

    def test_a_signature_records_what_it_is_valid_for(self):
        entry = self.signed_book()["units"][self.unit.name]
        self.assertEqual(entry["digest"], self.unit.digest)
        self.assertEqual(entry["python"], L.interpreter_tag())
        self.assertIn("signed_at", entry)

    def test_stale_is_the_complement_of_signed(self):
        for unit in L.plan(self.signed_book()):
            self.assertEqual(unit.stale, unit.state != "signed")

    def test_a_ledger_written_at_another_schema_is_discarded(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ledger.json"
            path.write_text(json.dumps({"schema": L.SCHEMA + 99, "units":
                                        {"test_signoff.py": {}}}),
                            encoding="utf-8")
            book = L.load_ledger(path)
            self.assertEqual(book["units"], {})
            self.assertEqual(book["superseded_schema"], L.SCHEMA + 99)

    def test_the_ledger_round_trips_through_a_file(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ledger.json"
            book = self.signed_book()
            L.save_ledger(book, path)
            self.assertEqual(L.load_ledger(path)["units"], book["units"])


class TestSaving(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = L.plan()
        cls.saving = L.predicted_saving(cls.rows)

    def test_the_prediction_is_exact_rational_seconds(self):
        for key in ("seconds_saved", "seconds_to_run", "seconds_full_run",
                    "fraction_saved"):
            self.assertIsInstance(self.saving[key], Fraction)
            self.assertGreaterEqual(self.saving[key], 0)

    def test_the_saving_and_the_work_add_up_to_the_full_run(self):
        self.assertEqual(
            self.saving["seconds_saved"] + self.saving["seconds_to_run"],
            self.saving["seconds_full_run"])

    def test_units_never_timed_are_counted_separately(self):
        self.assertEqual(self.saving["units"], len(self.rows))
        self.assertEqual(self.saving["signed"] + self.saving["stale"],
                         self.saving["units"])
        self.assertIsInstance(self.saving["units_without_timing"], tuple)

    @pytest.mark.exhaustive
    def test_a_dry_run_runs_nothing_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ledger.json"
            result = L.run_plan(all_units=True, dry_run=True, ledger_path=path)
            self.assertFalse(path.is_file())
            self.assertEqual(result["ran"], len(L.plan()))
            self.assertTrue(all(r["status"] == "not run"
                                for r in result["results"]))


class TestVerify(unittest.TestCase):

    def test_verify_runs_nothing_and_partitions_the_units(self):
        report = L.verify()
        total = (report["signed"] + len(report["new"]) + len(report["changed"])
                 + len(report["failed"]))
        self.assertEqual(total, report["units"])
        self.assertEqual(report["units"], len(L.test_units()))

    def test_all_signed_is_not_claimed_unless_every_unit_is_signed(self):
        report = L.verify()
        self.assertEqual(report["all_signed"],
                         report["signed"] == report["units"])

    def test_an_empty_ledger_signs_nothing(self):
        with tempfile.TemporaryDirectory() as raw:
            report = L.verify(Path(raw) / "absent.json")
            self.assertEqual(report["signed"], 0)
            self.assertFalse(report["all_signed"])


class TestDocumentClosure(unittest.TestCase):
    """A unit that reads a document depends on it, and one that does not, does not.

    This is the hole the first version of the ledger had: a closure built from
    imports alone signs off ``test_figures.py`` -- whose whole job is to catch
    a stale count in ``STATUS.md`` -- while ``STATUS.md`` is being edited.
    """

    @classmethod
    def setUpClass(cls):
        cls.figures = L.unit_closure(L.TESTS_DIR / "test_figures.py")
        cls.substrate = L.unit_closure(L.TESTS_DIR / "test_substrate.py")

    def names(self, closure):
        return {p.name for p in closure}

    def test_the_documents_a_unit_checks_are_in_its_closure(self):
        names = self.names(self.figures)
        for document in ("STATUS.md", "MASTER_PLAN.md", "FIGURES.md",
                         "CAPABILITY_ASSESSMENT.md"):
            self.assertIn(document, names)

    def test_a_unit_that_reads_no_document_carries_no_figures(self):
        """``test_substrate.py`` states no figure, so no figure-bearing document.

        It is not literally document-free: the type-2 table is now stored
        against a SHA-256 digest, that digest comes from ``integrity.py``, and
        ``integrity.py`` cites the directive that licenses it.  The closure is
        a deliberate over-approximation -- a module that *names* a document
        depends on it -- and that citation is the whole of what it found.  The
        property that matters is unchanged: editing a document that quotes a
        count does not make this unit stale.
        """
        documents = sorted(p.name for p in self.substrate
                           if p.suffix in (".md", ".txt"))
        self.assertEqual(documents, ["PROJECT_DIRECTIVES.md"])
        for quoted in ("STATUS.md", "README.md", "FIGURES.md",
                       "MASTER_PLAN.md", "CAPABILITY_ASSESSMENT.md"):
            self.assertNotIn(quoted, documents)

    def test_naming_a_lean_file_pulls_in_the_whole_development(self):
        names = self.names(L.unit_closure(L.TESTS_DIR / "test_lean_address.py"))
        self.assertIn("Address.lean", names)
        self.assertIn("Tower.lean", names)
        self.assertIn("lean-toolchain", names)

    def test_the_document_index_is_by_name_and_holds_every_copy(self):
        index = L.document_index()
        self.assertIn("STATUS.md", index)
        self.assertEqual(len(index["STATUS.md"]), 1)
        # several READMEs share a name; all of them are indexed
        self.assertGreater(len(index["README.md"]), 3)

    def test_the_lean_development_is_found_in_both_copies(self):
        sources = L.lean_sources()
        repository = [p for p in sources if "glm_lean" not in p.parts]
        overlay = [p for p in sources if "glm_lean" in p.parts]
        self.assertGreater(len(repository), 30)
        self.assertGreater(len(overlay), 30)

    @pytest.mark.exhaustive
    def test_editing_a_document_makes_exactly_the_units_that_read_it_stale(self):
        """The point of the whole exercise, checked on the real closures."""
        document = (L.REPOSITORY_ROOT / "STATUS.md").resolve()
        reads_it = [u for u in L.plan()
                    if document in L.unit_closure(u.path)]
        self.assertIn("test_figures.py", {u.name for u in reads_it})
        self.assertNotIn("test_substrate.py", {u.name for u in reads_it})


class TestInstruments(unittest.TestCase):
    """The non-pytest instruments are signed off by the same rule."""

    @classmethod
    def setUpClass(cls):
        cls.rows = C.check_plan()

    def test_every_instrument_has_a_command_and_a_closure(self):
        for check in C.CHECKS:
            self.assertTrue(check.command)
            self.assertIn(check.where, ("overlay", "repository"))
            self.assertTrue(check.cwd.is_dir())
            self.assertTrue(check_closure_nonempty(check))

    def test_the_slow_instruments_are_all_covered(self):
        names = {check.name for check in C.CHECKS}
        for expected in ("lean-build", "evaluation", "benchmarks",
                         "capabilities", "figures"):
            self.assertIn(expected, names)

    def test_a_lean_instrument_depends_on_the_lean_sources(self):
        closure = set(C.check_closure(C.checks_by_name()["lean-build"]))
        self.assertTrue(set(L.lean_sources()) <= closure)

    def test_the_evaluation_depends_on_the_command_line_it_drives(self):
        closure = {p.name for p in
                   C.check_closure(C.checks_by_name()["evaluation"])}
        self.assertIn("GLM.py", closure)
        self.assertIn("harness.py", closure)

    def test_the_figures_instrument_depends_on_the_file_it_compares(self):
        closure = {p.name for p in
                   C.check_closure(C.checks_by_name()["figures"])}
        self.assertIn("FIGURES.md", closure)

    def test_the_command_is_part_of_the_signature(self):
        check = C.checks_by_name()["benchmarks"]
        other = C.Check(name=check.name, description=check.description,
                        command=check.command + ("--extra",),
                        entry_points=check.entry_points)
        self.assertNotEqual(C.check_digest(check), C.check_digest(other))

    def test_an_instrument_digest_is_a_sha256_and_is_reproducible(self):
        for check in C.CHECKS:
            digest = C.check_digest(check)
            self.assertEqual(len(digest), 64)
            self.assertEqual(digest, C.check_digest(check))

    def test_a_failing_instrument_is_recorded_but_does_not_sign(self):
        unit = self.rows[0]
        book = {"schema": L.SCHEMA, "python": L.interpreter_tag(),
                "checks": {}}
        book = C._sign_check(unit, {"status": "failed", "returncode": 1,
                                    "milliseconds": 10}, book)
        state = next(u.state for u in C.check_plan(book) if u.name == unit.name)
        self.assertEqual(state, "failed")
        book = C._sign_check(unit, {"status": "passed", "returncode": 0,
                                    "milliseconds": 10}, book)
        state = next(u.state for u in C.check_plan(book) if u.name == unit.name)
        self.assertEqual(state, "signed")

    def test_a_dry_run_runs_nothing_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ledger.json"
            result = C.run_checks(all_units=True, dry_run=True,
                                  ledger_path=path)
            self.assertFalse(path.is_file())
            self.assertEqual(result["ran"], len(C.CHECKS))

    def test_verify_partitions_the_instruments(self):
        report = C.verify_checks()
        total = (report["signed"] + len(report["new"]) + len(report["changed"])
                 + len(report["failed"]))
        self.assertEqual(total, report["units"])
        self.assertEqual(report["units"], len(C.CHECKS))

    def test_the_saving_is_exact_rational_seconds(self):
        saving = C.predicted_check_saving(self.rows)
        for key in ("seconds_saved", "seconds_to_run", "seconds_full_run",
                    "fraction_saved"):
            self.assertIsInstance(saving[key], Fraction)
        self.assertEqual(saving["seconds_saved"] + saving["seconds_to_run"],
                         saving["seconds_full_run"])


class TestScaffoldingIsTheRuleAndNothingElse(unittest.TestCase):
    """What belongs in *every* closure, and what deliberately does not."""

    def test_the_harness_and_the_rule_are_in_every_closure(self):
        names = {p.name for p in L.scaffolding_paths()}
        self.assertIn("__init__.py", names)
        self.assertIn("ledger.py", names)

    def test_the_instrument_table_is_not_in_a_test_units_closure(self):
        """Adding an instrument must not invalidate all fifty test units.

        ``checks.py`` cannot change what a test file observes, so it is not
        scaffolding -- but it *is* in every instrument's closure, and a test
        file that imports it picks it up as an ordinary import.
        """
        closure = {p.name for p in
                   L.unit_closure(L.TESTS_DIR / "test_substrate.py")}
        self.assertNotIn("checks.py", closure)
        self.assertNotIn("__main__.py", closure)
        for check in C.CHECKS:
            self.assertIn("checks.py",
                          {p.name for p in C.check_closure(check)})
        # test_signoff.py imports it, so it is in this file's own closure
        self.assertIn("checks.py",
                      {p.name for p in
                       L.unit_closure(L.TESTS_DIR / "test_signoff.py")})


class TestSummaryParsing(unittest.TestCase):
    """The recorded counts are what pytest reported."""

    def test_tests_and_subtests_are_read_separately(self):
        summary = L._parse_pytest_summary(
            "24 passed, 33 subtests passed in 1.52s")
        self.assertEqual(summary["passed"], 24)
        self.assertEqual(summary["subtests"], 33)
        self.assertEqual(summary["failed"], 0)

    def test_a_file_without_subtests_reports_none(self):
        summary = L._parse_pytest_summary("47 passed in 77.04s")
        self.assertEqual(summary["passed"], 47)
        self.assertEqual(summary["subtests"], 0)

    def test_failures_and_errors_are_read(self):
        summary = L._parse_pytest_summary(
            "2 failed, 45 passed, 1 error in 9.10s")
        self.assertEqual(summary["failed"], 2)
        self.assertEqual(summary["passed"], 45)
        self.assertEqual(summary["errors"], 1)


class TestRunModes(unittest.TestCase):
    """Fast and full: a routine signature does not satisfy a release check.

    The exhaustive cases are deselected on a routine run, so a unit signed by
    one has covered less than a unit signed by a release run.  The ledger
    records which, and ``plan(full=True)`` -- the question ``--verify-release``
    asks -- reports the difference as ``partial`` rather than treating it as
    signed off.  That is what keeps "nothing only runs on demand" a fact.
    """

    @classmethod
    def setUpClass(cls):
        cls.plan_rows = L.plan()

    @property
    def unit(self):
        return next(u for u in self.plan_rows if u.name == "test_signoff.py")

    def book_signed_in(self, mode):
        book = {"schema": L.SCHEMA, "python": L.interpreter_tag(), "units": {}}
        return L.sign(self.unit,
                      {"status": "passed", "tests": 3, "subtests": 0,
                       "failures": 0, "milliseconds": 1000, "mode": mode},
                      book)

    def state_of(self, book, full):
        return next(u.state for u in L.plan(book, full=full)
                    if u.name == self.unit.name)

    def test_the_mode_is_recorded_with_the_signature(self):
        entry = self.book_signed_in("full")["units"][self.unit.name]
        self.assertEqual(entry["mode"], "full")

    def test_a_fast_signature_satisfies_a_routine_run(self):
        self.assertEqual(self.state_of(self.book_signed_in("fast"), False),
                         "signed")

    def test_a_fast_signature_does_not_satisfy_a_release_run(self):
        self.assertEqual(self.state_of(self.book_signed_in("fast"), True),
                         "partial")

    def test_a_full_signature_satisfies_both(self):
        book = self.book_signed_in("full")
        self.assertEqual(self.state_of(book, False), "signed")
        self.assertEqual(self.state_of(book, True), "signed")

    def test_a_ledger_from_before_the_mode_existed_reads_as_fast(self):
        book = self.book_signed_in("fast")
        del book["units"][self.unit.name]["mode"]
        self.assertEqual(self.state_of(book, False), "signed")
        self.assertEqual(self.state_of(book, True), "partial")

    def test_verify_names_the_partial_units(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ledger.json"
            L.save_ledger(self.book_signed_in("fast"), path)
            report = L.verify(path, full=True)
            self.assertIn(self.unit.name, report["partial"])
            self.assertFalse(report["all_signed"])
            self.assertTrue(report["full"])


class TestParallelRuns(unittest.TestCase):
    """``--jobs`` changes how fast the plan runs, never what it decides."""

    @pytest.mark.exhaustive
    def test_a_dry_run_reports_the_jobs_and_the_mode(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ledger.json"
            result = L.run_plan(all_units=True, dry_run=True, jobs=4,
                                ledger_path=path)
            self.assertEqual(result["jobs"], 4)
            self.assertEqual(result["mode"], "full")
            self.assertEqual(result["ran"], len(L.test_units()))
            self.assertFalse(path.exists())

    def test_the_default_job_count_is_at_least_one(self):
        self.assertGreaterEqual(L.DEFAULT_JOBS, 1)
        self.assertLessEqual(L.DEFAULT_JOBS, 8)

    def test_the_instruments_take_a_job_count_too(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ledger.json"
            result = C.run_checks(all_units=True, dry_run=True, jobs=3,
                                  ledger_path=path)
            self.assertEqual(result["jobs"], 3)
            self.assertEqual(result["ran"], len(C.CHECKS))


class TestTheRecordedTotals(unittest.TestCase):
    """What may and may not stop a complete run from recording its totals.

    The totals are measured over ``counted_units()`` -- the suite minus
    ``tests/test_figures.py`` -- so the condition for recording them is over
    the same set.  Requiring the document check to pass as well would restore
    the loop that excluding it exists to remove: a round that adds a test file
    makes the recorded ``N of M test files`` sentence one file short, which is
    exactly what the document check refuses, so the run that measured the new
    totals could never record them.
    """

    def _book(self, *, doc_status: str) -> dict:
        units = {}
        for path in L.counted_units():
            units[path.name] = {"status": "passed", "mode": "full",
                                "tests": 2, "subtests": 3}
        for name in L.DOCUMENT_CHECKS:
            units[name] = {"status": doc_status, "mode": "full",
                           "tests": 99, "subtests": 99}
        return {"units": units}

    def _record(self, book: dict) -> dict:
        written = {}
        original = L._write_totals_sidecar
        L._write_totals_sidecar = lambda counts, path=None: written.update(
            counts)
        try:
            out = L._record_totals(dict(book), "full")
        finally:
            L._write_totals_sidecar = original
        return out

    def test_a_failing_document_check_does_not_block_the_totals(self):
        out = self._record(self._book(doc_status="failed"))
        totals = out["totals"]
        counted = len(L.counted_units())
        self.assertEqual(totals["test_files"], counted)
        self.assertEqual(totals["tests"], 2 * counted)
        self.assertEqual(totals["subtests"], 3 * counted)
        self.assertEqual(totals["excludes"], list(L.DOCUMENT_CHECKS))

    def test_the_document_check_is_never_counted(self):
        passed = self._record(self._book(doc_status="passed"))["totals"]
        failed = self._record(self._book(doc_status="failed"))["totals"]
        for key in ("test_files", "tests", "subtests"):
            self.assertEqual(passed[key], failed[key])
        self.assertNotIn(99, passed.values())

    def test_a_failing_counted_unit_does_block_them(self):
        book = self._book(doc_status="passed")
        name = L.counted_units()[0].name
        book["units"][name] = {"status": "failed", "mode": "full",
                               "tests": 2, "subtests": 3}
        self.assertNotIn("totals", self._record(book))

    def test_a_fast_run_does_not_record_them(self):
        book = self._book(doc_status="passed")
        name = L.counted_units()[0].name
        book["units"][name] = {**book["units"][name], "mode": "fast"}
        self.assertNotIn("totals", self._record(book))


def check_closure_nonempty(check) -> bool:
    """Whether an instrument's closure names at least its own scaffolding."""
    return len(C.check_closure(check)) > 0


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
