"""Tests for the budget rule in the answering path (Phase 147).

``studies/BUDGET_READING_STUDY.md`` pre-registered nine marks.  These tests
pin:

* the **Lean file** (L1): it states the theorems and has no ``sorry``;
* the **rule's constants**: the budget is Phase 124's, the walk seeds are the
  census's;
* the **request grammar** of the ``hole`` kind, with every named refusal;
* the **query kind**: start-only, so the report subjects are unmoved;
* **readings** under the rule through the session, and column 3;
* ``report deep holes`` reads under the rule;
* the **wiring census** (W1's own half);
* the stored **measurement** and its marks, read from the cache, which must
  describe the sources (D4).
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

from glm_universal.reasoning import budget_reading_study as brs
from glm_universal.reasoning import hole_reading as hr
from glm_universal.reasoning import probe_budget as pb
from glm_universal.runtime.parser import KINDS, START_ONLY, parse_query

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "overlay" / "glm_lean" / hr.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in hr.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def test_the_budget_is_phase_124s():
    assert hr.BUDGET == pb.BUDGET == 1056
    assert hr.walk_seed(0) == 20260825
    assert hr.walk_seed(3) == 20260825 + 3 * 977


@pytest.mark.parametrize("text, reason", [
    ("walk x", "malformed"), ("1, 2, 3", "dimension"), ("", "malformed"),
    ("the moon", "malformed"), ("walk 100000", "malformed"),
    ("1/0, " * 23 + "0", "malformed"),
])
def test_a_malformed_request_is_refused_with_its_reason(text, reason):
    with pytest.raises(hr.HoleError) as caught:
        hr.parse_request(text)
    assert caught.value.reason == reason


def test_the_request_grammar():
    assert hr.parse_request("walk 7")["walk"] == 7
    assert hr.parse_request("of walk 7")["walk"] == 7
    assert hr.parse_request("octad pair")["label"] == "the octad-pair midpoint"
    assert hr.parse_request("dodecad triangle")["centre"] is not None
    assert len(hr.parse_request(", ".join(["0"] * 24))["centre"]) == 24


def test_hole_is_a_start_only_kind():
    assert "hole" in KINDS
    for word in ("hole", "deep hole", "read hole", "classify hole"):
        assert word in START_ONLY
    assert parse_query("hole walk 3").kind == "hole"
    assert parse_query("deep hole of walk 3").options["request"] == \
        "of walk 3"
    for text in ("report deep holes", "report hole ladder",
                 "report hole classifier"):
        assert parse_query(text).kind == "report"


def test_start_zero_decides_the_depth():
    assert hr.depth([0] * 24)["lattice_point"]
    shallow = hr.depth(["1/8"] * 23 + ["3/8"])
    assert not shallow["deep"] and not shallow["lattice_point"]


def test_a_construction_is_certified_under_the_rule():
    out = hr.answer("dodecad triangle")
    assert out["status"] == "certified"
    assert out["type"] == "A_2^12"
    assert out["rule"] == "budget"
    assert 0 < out["starts"] < hr.BUDGET


def test_the_session_answers_and_column_three_verifies():
    from glm_universal.runtime.session import GeometricSession
    from glm_universal.runtime import tct_engine as tct
    session = GeometricSession(domains=())
    sol = session.ask("hole walk 1")
    assert sol.ok and sol.kind == "hole"
    assert "D_24" in sol.answer and "budget rule" in sol.answer
    assert tct.verify_trace(tct.build_trace(sol)).verdict.matches_column2
    wrong = dataclasses.replace(sol, expected=dict(sol.expected,
                                                   type="E_8^3"))
    assert not tct.verify_trace(tct.build_trace(wrong)).verdict \
        .matches_column2
    for text, reason in (("hole " + ", ".join(["0"] * 24), "lattice-point"),
                         ("hole walk x", "malformed")):
        refused = session.ask(text)
        assert not refused.ok and f"({reason})" in refused.error


def test_report_deep_holes_reads_under_the_rule():
    from glm_universal.runtime.session import GeometricSession
    sol = GeometricSession(domains=()).ask("report deep holes")
    assert sol.ok
    assert any("not on patience" in s.label for s in sol.steps)
    assert "exhibited 5 of the 23" in sol.answer


def test_the_wiring_census_reaches_the_reader():
    w = brs.wiring()
    assert w["hole_reading_reached"]
    assert not w["census"]["undeclared"]
    assert not w["census"]["stale_declarations"]
    assert not w["diverted"]


def test_the_stored_measurement_is_current_and_meets_its_marks():
    report = brs.budget_reading_report()
    assert report.get("available"), report.get("reason")
    assert report["met"] == report["taken"], report["marks"]
    held = report["heldout"]
    assert held["rule_certified"] == held["reached"] == 256
