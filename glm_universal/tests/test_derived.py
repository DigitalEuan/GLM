"""Tests for the derived-artefact layer and the exhaustive opt-in.

Three things are pinned here.

* **A memo is an optimisation, never a claim.**  Every memoised derivation is
  registered, and for each one the cached object and the object the uncached
  function builds must be equal.  If a memo ever changed an answer, that is
  where it would show.
* **A stored artefact is answered only against its digest.**
  :class:`glm_universal.derived.DerivedStore` is the address book's rule made
  reusable: fresh, stale or absent, with both digests visible, and a stale
  artefact is never handed back.
* **Nothing only runs on demand.**  The ``exhaustive`` marker is deselected by
  default and selected by ``--exhaustive`` or ``GLM_EXHAUSTIVE=1``, and the
  sign-off runner turns it on for every ``-all`` form -- checked here by
  running pytest twice over a temporary test file.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

from glm_universal import derived as D
from glm_universal.signoff import ledger as L

REPOSITORY_ROOT = L.REPOSITORY_ROOT
OVERLAY = L.PROJECT_ROOT


# ===========================================================================
# 1.  THE MEMO REGISTRY
# ===========================================================================

class TestMemoRegistry:

    def test_the_registry_is_not_empty(self):
        assert len(D.memo_registry()) >= 10

    def test_every_registered_name_resolves_to_a_memoised_function(self):
        for dotted in D.memo_registry():
            module_name, attribute = dotted.rsplit(".", 1)
            module = importlib.import_module(module_name)
            function = getattr(module, attribute)
            assert hasattr(function, "__wrapped__"), dotted
            assert hasattr(function, "memo"), dotted

    def test_the_registry_names_are_sorted_and_unique(self):
        names = D.memo_registry()
        assert list(names) == sorted(names)
        assert len(set(names)) == len(names)


class TestMemoBehaviour:

    def test_the_second_call_returns_the_first_call_s_object(self):
        calls = []

        @D.memo
        def derivation():
            calls.append(1)
            return {"a": 1}

        first = derivation()
        second = derivation()
        assert first is second
        assert calls == [1]

    def test_the_uncached_function_is_still_reachable_and_agrees(self):
        @D.memo
        def derivation():
            return {"a": 1, "b": (2, 3)}

        cached = derivation()
        fresh = derivation.__wrapped__()
        assert fresh == cached
        assert fresh is not cached

    def test_clearing_forces_a_recomputation(self):
        calls = []

        @D.memo
        def derivation():
            calls.append(1)
            return len(calls)

        assert derivation() == 1
        assert derivation() == 1
        D.clear_memos([derivation.memo.name])
        assert derivation() == 2

    def test_the_state_counts_hits_and_misses(self):
        @D.memo
        def derivation():
            return 7

        name = derivation.memo.name
        derivation()
        derivation()
        derivation()
        state = D.memo_state()[name]
        assert state["filled"] is True
        assert state["misses"] == 1
        assert state["hits"] == 2


class TestTheStudiesAgreeWithTheirUncachedForm:
    """The memo does not change what the project reports.

    One cheap derivation from each corner is recomputed from scratch and
    compared with the cached answer.  The expensive ledgers are compared the
    same way in their own test files, where the object is already built.
    """

    @pytest.mark.parametrize("dotted", [
        "glm_universal.reasoning.blueprint.ubp_source_audit",
        "glm_universal.reasoning.containers.critical_scales",
        "glm_universal.reasoning.containers.hull_table",
        "glm_universal.substrate.isomorphism.migration_report",
    ])
    def test_the_cached_answer_is_the_computed_one(self, dotted):
        module_name, attribute = dotted.rsplit(".", 1)
        function = getattr(importlib.import_module(module_name), attribute)
        assert function() == function.__wrapped__()


# ===========================================================================
# 2.  THE DIGEST-KEYED STORE
# ===========================================================================

class TestDerivedStore:

    def _store(self, root, inputs):
        return D.DerivedStore("unit-test", lambda: inputs, schema=1,
                              root=root)

    def test_an_absent_artefact_is_absent_not_fresh(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "input.txt"
            source.write_text("one", encoding="utf-8")
            store = self._store(root / "cache", [source])
            state = store.state()
            assert state["present"] is False
            assert state["fresh"] is False
            assert state["verdict"] == "absent"
            assert store.read_fresh() is None

    def test_a_written_artefact_is_fresh_against_its_inputs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "input.txt"
            source.write_text("one", encoding="utf-8")
            store = self._store(root / "cache", [source])
            store.write({"value": 1})
            state = store.state()
            assert state["verdict"] == "fresh"
            assert state["stored_digest"] == state["live_digest"]
            assert store.read_fresh() == {"value": 1}

    def test_editing_an_input_makes_the_artefact_stale_and_unreadable(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "input.txt"
            source.write_text("one", encoding="utf-8")
            store = self._store(root / "cache", [source])
            store.write({"value": 1})
            source.write_text("two", encoding="utf-8")
            state = store.state()
            assert state["verdict"] == "stale"
            assert state["stored_digest"] != state["live_digest"]
            # the honest part: a stale artefact is reported, never answered
            assert store.read_fresh() is None

    def test_a_stale_artefact_is_recomputed_and_rewritten(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "input.txt"
            source.write_text("one", encoding="utf-8")
            store = self._store(root / "cache", [source])
            calls = []

            def compute():
                calls.append(1)
                return {"n": len(calls)}

            assert store.cached(compute) == {"n": 1}
            assert store.cached(compute) == {"n": 1}    # fresh: not recomputed
            source.write_text("two", encoding="utf-8")
            assert store.cached(compute) == {"n": 2}    # stale: recomputed
            assert store.state()["verdict"] == "fresh"

    def test_a_schema_bump_retires_the_artefact(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "input.txt"
            source.write_text("one", encoding="utf-8")
            cache = root / "cache"
            D.DerivedStore("unit-test", lambda: [source], schema=1,
                           root=cache).write({"value": 1})
            later = D.DerivedStore("unit-test", lambda: [source], schema=2,
                                   root=cache)
            assert later.state()["verdict"] == "stale"
            assert later.read_fresh() is None


# ===========================================================================
# 3.  THE EXHAUSTIVE OPT-IN
# ===========================================================================

MARKED_TEST = textwrap.dedent(
    """
    import pytest

    def test_cheap():
        assert True

    @pytest.mark.exhaustive
    def test_expensive():
        assert True
    """
)


def _run_pytest(path, extra=(), env=None):
    command = [sys.executable, "-m", "pytest", str(path), "-q", "--no-header",
               *extra]
    return subprocess.run(command, cwd=str(OVERLAY), capture_output=True,
                          text=True, env=env)


class TestTheMarkerIsHonoured:
    """Deselected by default; selected by either spelling of the switch."""

    def _file(self, directory):
        target = Path(directory) / "test_marker_probe.py"
        target.write_text(MARKED_TEST, encoding="utf-8")
        return target

    def test_by_default_the_exhaustive_case_is_skipped_not_dropped(self):
        with tempfile.TemporaryDirectory(dir=str(OVERLAY)) as raw:
            result = _run_pytest(self._file(raw),
                                 env=L.run_environment(False))
            assert result.returncode == 0, result.stdout
            assert "1 passed, 1 skipped" in result.stdout

    def test_the_command_line_flag_selects_it(self):
        with tempfile.TemporaryDirectory(dir=str(OVERLAY)) as raw:
            result = _run_pytest(self._file(raw), extra=("--exhaustive",),
                                 env=L.run_environment(False))
            assert result.returncode == 0, result.stdout
            assert "2 passed" in result.stdout

    def test_the_environment_variable_selects_it(self):
        with tempfile.TemporaryDirectory(dir=str(OVERLAY)) as raw:
            result = _run_pytest(self._file(raw), env=L.run_environment(True))
            assert result.returncode == 0, result.stdout
            assert "2 passed" in result.stdout

    def test_the_skip_reason_says_how_to_run_it(self):
        with tempfile.TemporaryDirectory(dir=str(OVERLAY)) as raw:
            result = _run_pytest(self._file(raw), extra=("-rs",),
                                 env=L.run_environment(False))
            assert "--exhaustive" in result.stdout
            assert L.EXHAUSTIVE_ENV in result.stdout


class TestTheRunEnvironment:

    def test_the_switch_is_set_only_when_asked_for(self):
        assert L.run_environment(True)[L.EXHAUSTIVE_ENV] == "1"
        assert L.EXHAUSTIVE_ENV not in L.run_environment(False)

    def test_the_rest_of_the_environment_survives(self):
        env = L.run_environment(True)
        for key in ("PATH",):
            if key in os.environ:
                assert env[key] == os.environ[key]


class TestEveryMarkedCaseIsDeclared:
    """The marker is registered, so a typo is an error rather than a silent
    pass.  ``--strict-markers`` would not catch a mark that is never declared
    unless the declaration exists, so the declaration is checked directly."""

    def test_the_marker_is_declared_in_the_conftest(self):
        text = (OVERLAY / "conftest.py").read_text(encoding="utf-8")
        assert "exhaustive:" in text
        assert L.EXHAUSTIVE_ENV in text

    def test_at_least_one_case_in_the_suite_carries_the_marker(self):
        marked = [p.name for p in sorted(L.TESTS_DIR.glob("test_*.py"))
                  if "@pytest.mark.exhaustive" in p.read_text(encoding="utf-8")]
        assert len(marked) >= 8


# ===========================================================================
# 5.  THE TYPE-2 TABLE ON DISK
# ===========================================================================

class TestTheTypeTwoTableIsCachedAgainstItsDigest:
    """The 98,280-class table is the biggest single derivation in the package.

    It is now stored the way the Lean address book is: beside the SHA-256
    digest of the three modules it is a function of, read back only while that
    digest holds.  What has to stay true is that the stored answer is the
    enumerated answer -- so the packing is checked to be exactly invertible,
    and the cached table is compared against a fresh enumeration.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def table(cls):
        from glm_universal.substrate import leech2

        return leech2.type2_class_table()

    def test_the_packing_round_trips_exactly(self, table):
        from glm_universal.substrate import leech2

        packed = leech2._encode_type2(table)
        assert leech2._decode_type2(packed) == table

    def test_a_damaged_block_is_absent_rather_than_wrong(self, table):
        from glm_universal.substrate import leech2

        packed = dict(leech2._encode_type2(table))
        packed["count"] = 17
        assert leech2._decode_type2(packed) is None
        assert leech2._decode_type2("not a payload") is None
        assert leech2._decode_type2({"count": 98280}) is None

    def test_the_cache_reports_a_verdict_rather_than_a_boolean(self, table):
        from glm_universal.substrate import leech2

        state = leech2.type2_table_cache_state()
        assert state["verdict"] in {"fresh", "stale", "absent"}
        assert set(state) >= {"present", "fresh", "stored_digest",
                              "live_digest"}

    def test_the_table_equals_a_fresh_enumeration(self, table):
        from glm_universal.substrate import leech2

        fresh = {}
        for v in leech2.minimal_vectors():
            fresh.setdefault(leech2.class_of(v), v)
        assert fresh == table

    def test_a_moved_input_makes_the_artefact_stale(self, tmp_path):
        from glm_universal.derived import DerivedStore

        source = tmp_path / "input.txt"
        source.write_text("one", encoding="utf-8")
        store = DerivedStore("probe", lambda: [source], root=tmp_path)
        store.write({"value": 1})
        assert store.state()["verdict"] == "fresh"
        source.write_text("two", encoding="utf-8")
        assert store.state()["verdict"] == "stale"
        assert store.read_fresh() is None


# ===========================================================================
# 6.  THE MEMOISED DEFAULT DERIVATIONS
# ===========================================================================

class TestTheDefaultDerivationsReuseNothingTheyShouldNot:
    """A memo over a default argument must not change what a caller gets.

    Both of these take an optional argument: passing one recomputes, passing
    none returns the memoised object.  The two must agree, which is the whole
    content of the optimisation being sound.
    """

    def test_the_grounded_graph_is_the_uncached_graph(self):
        from glm_universal.semantics import graph

        assert graph.build_graph() == graph.default_graph.__wrapped__()

    def test_the_escalation_report_is_the_uncached_report(self):
        from glm_universal.reasoning import escalation

        fresh = escalation.default_escalation_report.__wrapped__()
        assert escalation.escalation_report() == fresh

    def test_passing_the_carriers_explicitly_recomputes(self):
        from glm_universal.reasoning import escalation

        entries = escalation.register_carriers()
        assert escalation.escalation_report(entries) == \
            escalation.escalation_report()
