"""Tests for the configuration reading ``L5`` in the other deep-hole reports
(Phase 149, ``studies/HOLE_REPORTS_L5_STUDY.md``).

These pin:

* the **Lean file** (L1): its four theorems, no ``sorry``;
* the three **readings** from the existing stores -- the classifier's sanity
  query and the 44 queries (C1), the escalation gate at every stored size
  (D1), the joint reading's four failures and ``L5``'s per-type criterion at
  1920 starts (E1) -- and the rule firing inside every radius (R1);
* each **report** keeping its round's record, ending with the ``L5`` clause,
  its column-3 script verifying (the ``report hole ladder`` script had never
  verified before Phase 149, §7.3) and a mutant rejected (Q1);
* the stored **measurement**, current and meeting its marks.

The report tests need the answering-path half of the round
(``runtime/reports/lattice_geometry.py`` and ``runtime/tct_engine.py``); they
fail, by design, while that half is missing.

Created 31 October 2026 (repository check: the file was named in
``tests/README.md`` and lost in the October 2026 reorganisation; written from
the README row and the study).  Last altered 31 October 2026 (the same check:
while ``_data/hole_l5_baseline.json`` is lost, F1 is pinned as not met with
its reason).
"""

from __future__ import annotations

import dataclasses
import re

import pytest

from glm_universal.constants import lean_file
from glm_universal.reasoning import configuration_classifier as cc
from glm_universal.reasoning import configuration_queries as cq
from glm_universal.reasoning import hole_reports_l5 as hl5
from glm_universal.reasoning import hole_reports_l5_study as hls


@pytest.fixture(scope="module")
def readings():
    return hl5.readings()


@pytest.fixture(scope="module")
def session():
    from glm_universal.runtime.session import GeometricSession
    return GeometricSession()


def test_the_lean_file_states_the_theorems_without_sorry():
    text = lean_file(hl5.LEAN_FILE).read_text(encoding="utf-8")
    for name in hl5.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "namespace GLM.HoleReportsL5" in text


def test_the_classifier_question_at_l5(readings):
    c = readings["classifier"]
    assert c["available"], c
    assert (c["seed_correct"], c["seed_queries"]) == (10, 10)
    assert c["sanity_holds"]
    assert (c["correct"], c["wrong"], c["refused"], c["queries"]) \
        == (44, 0, 0, 44)


def test_the_ladder_gate_at_l5(readings):
    d = readings["ladder"]
    assert d["available"], d
    assert d["passing"] == d["sizes"] == 8
    assert d["smallest_passing"] == 240
    assert d["passes_without_criterion"] == [480]
    assert d["joint_first_passing"] == 1920


def test_the_failures_at_l5(readings):
    e = readings["failures"]
    assert e["available"], e
    assert e["names_as_recorded"], e["names"]
    assert (e["l5_correct"], e["joint_failures"]) == (4, 4)
    assert e["locally_certified"] == e["types"] == 10
    assert e["rho_below_one"]
    assert hl5._rho(e["rho"]) == "0.3048"


def test_the_rule_fires_inside_every_radius():
    data = cq.current()
    assert data is not None, "configuration_queries is not current"
    table = cc.reference_table(data)
    run = cc.classify_queries(table, data)
    radii = cc.certified_radii(table)
    inside = [r for r in run["rows"] if r["within_own_radius"]]
    assert len(inside) == 44
    for r in inside:
        assert r["answer"] == r["truth"], r["query"]
        # rule_sound: the answer is the strict nearest reference
        assert r["nearest"] == r["answer"]
        assert r["own_distance"] <= radii[r["truth"]]


def test_the_clause_texts(readings):
    texts = hl5.clauses()
    assert texts[0] == (
        "read at L5 (the configuration reading, 1920 starts) under its "
        "answer rule the sanity query holds -- 10 of 10 seed queries named "
        "as themselves -- and the 44 queries are answered 44 correctly, 0 "
        "wrongly and 0 refused")
    assert texts[1] == (
        "read at L5 the gate passes at 8 of 8 ensemble sizes, first at 240 "
        "starts where the joint reading needed 1920, and at 480 starts it "
        "passes with rho at or above one, so the global criterion is "
        "sufficient, not necessary")
    assert texts[2] == (
        "read at L5 under its answer rule the 4 failures are answered 4 "
        "correctly, 0 wrongly and 0 refused, and at 1920 starts L5 meets "
        "the criterion for 10 of 10 types (rho = 0.3048)")


@pytest.mark.parametrize("question, reading", [
    ("report hole classifier", "classifier"),
    ("report hole ladder", "ladder"),
    ("report hole failures", "failures"),
])
def test_each_report_keeps_its_record_and_adds_the_clause(session, readings,
                                                          question, reading):
    clause = {"classifier": hl5.classifier_clause,
              "ladder": hl5.ladder_clause,
              "failures": hl5.failures_clause}[reading](readings[reading])
    sol = session.ask(question)
    assert sol.ok, sol.error
    assert clause in sol.answer, "the report does not carry the L5 clause"
    record, _sep, _rest = sol.answer.partition("; " + clause)
    assert record.startswith(question + ":")


def test_each_script_verifies_and_rejects_a_mutant(session):
    from glm_universal.runtime.tct_engine import build_trace, verify_trace
    for question, _reading, keys in hls.BATTERY:
        sol = session.ask(question)
        assert sol.ok, question
        assert verify_trace(build_trace(sol)).verified, question
        for key in keys:
            assert key in sol.expected, (question, key)
            altered = dict(sol.expected)
            altered[key] = str(altered[key]) + "-altered"
            bad = dataclasses.replace(sol, expected=altered)
            assert not verify_trace(build_trace(bad)).verified, (question,
                                                                 key)


def test_the_stored_measurement_is_current_and_meets_its_marks():
    report = hls.hole_reports_l5_report()
    assert report["available"], report.get("reason")
    assert report["taken"] == 6
    assert report["lean"]["met"]
    if hls.BASELINE_PATH.is_file():
        assert report["met"] == 6, report["marks"]
    else:
        # The baseline frozen before the answering-path edit was lost in the
        # October 2026 reorganisation: F1 is reported not met, with the reason
        # (31 October 2026, repository check); the other five marks hold.
        assert report["marks"]["F1"] is False
        assert "baseline lost in the October 2026 reorganisation" in \
            report["frozen"]["reason"]
        assert report["met"] == 5, report["marks"]
