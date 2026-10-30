"""Tests for the guarded read in the ``nearest`` kind (Phase 148).

``studies/NEAREST_ADDRESS_STUDY.md`` pre-registered eight marks.  These tests
pin:

* the **Lean file** (L1);
* the **address path** of the parser: only a move or a coordinate list goes
  there, and every earlier ``nearest`` question keeps its register path;
* the **ranking** and its agreement with the guarded read on declared points;
* the session's answers, certified and uncertified, and column 3;
* the **ladder audit** list and the frozen path's declarations;
* the stored **measurement** and its marks, read from the cache (D4).
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

from glm_universal.reasoning import address_read as ar
from glm_universal.reasoning import address_table as at
from glm_universal.reasoning import budget_guard_frozen as bgf
from glm_universal.reasoning import nearest_address as na
from glm_universal.reasoning import nearest_address_study as nas
from glm_universal.runtime.parser import parse_query

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / na.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in na.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text
    assert "import RequestProject.GLM.AddressRead" in text


@pytest.mark.parametrize("text, request_text, limit", [
    ("nearest to C moved 8 by 1/2", "C moved 8 by 1/2", None),
    ("nearest 3 to C moved 8 by 1/2", "C moved 8 by 1/2", 3),
    ("nearest to C moved 8 by 1/2 top 2", "C moved 8 by 1/2", 2),
    ("nearest to 1, 2", "1, 2", None),
])
def test_the_address_path_is_taken_for_a_point(text, request_text, limit):
    assert na.split_request(text) == (request_text, limit)
    q = parse_query(text)
    assert q.kind == "nearest"
    assert q.options["address_request"] == request_text


@pytest.mark.parametrize("text", [
    "nearest to water", "nearest 3 to pressure", "nearest to C",
    "what is the nearest 3 to pressure", "nearest to Cl2Pb",
])
def test_a_name_keeps_the_register_path(text):
    assert na.split_request(text) is None
    assert "address_request" not in parse_query(text).options


def test_the_ranking_is_sorted_and_complete():
    rows = at.carriers()
    ranked = na.ranking(rows[29][2], rows)
    assert len(ranked) == len(rows) == 142
    assert sorted(i for i, _ in ranked) == list(range(142))
    assert all(a[1] <= b[1] for a, b in zip(ranked, ranked[1:]))
    assert ranked[0] == (29, 0)


def test_the_head_agrees_with_the_read():
    out = na.nearest_read("C moved 8 by 1/2")
    assert out["certified"] and out["gap_certified"]
    assert out["head_tied"] == [out["read_carrier"]]
    junction = na.nearest_read("albedo moved 4 by 1/4")
    assert junction["certified"] and len(junction["members"]) == 2
    assert sorted(junction["head_tied"]) == sorted(junction["members"])
    refused = na.nearest_read("harmonics:perfect_fifth moved 2 by 2", 3)
    assert not refused["certified"] and len(refused["ranked"]) == 3


@pytest.mark.parametrize("request_text, reason", [
    ("water moved 8 by 1/2", "ambiguous-name"),
    ("Fe moved 8 by 1/2", "unknown-name"),
    ("1, 2, 3", "dimension"),
    ("C moved 30 by 1/2", "malformed"),
])
def test_a_refused_request_keeps_its_reason(request_text, reason):
    with pytest.raises(ar.AddressError) as caught:
        na.nearest_read(request_text)
    assert caught.value.reason == reason


def test_the_session_answers_and_column_three_verifies():
    from glm_universal.runtime.session import GeometricSession
    from glm_universal.runtime import tct_engine as tct
    session = GeometricSession(domains=())
    sol = session.ask("nearest to C moved 8 by 1/2")
    assert sol.ok and sol.kind == "nearest"
    assert "certifies the head" in sol.answer
    assert tct.verify_trace(tct.build_trace(sol)).verdict.matches_column2
    for bad in (dict(sol.expected, head="chemistry:H"),
                dict(sol.expected, margin="1000000/1")):
        mutated = dataclasses.replace(sol, expected=bad)
        assert not tct.verify_trace(tct.build_trace(mutated)).verdict \
            .matches_column2
    unc = session.ask("nearest 3 to harmonics:perfect_fifth moved 2 by 2")
    assert unc.ok and "no margin is certified" in unc.answer
    assert tct.verify_trace(tct.build_trace(unc)).verdict.matches_column2


def test_the_audit_watches_the_unguarded_readings():
    import importlib
    for module, names in bgf.UNGUARDED:
        mod = importlib.import_module(f"glm_universal.reasoning.{module}")
        for name in names:
            assert callable(getattr(mod, name)), (module, name)


def test_the_wiring_census_reaches_the_path():
    w = nas.wiring()
    assert w["nearest_address_reached"]
    assert not w["diverted"]


def test_the_stored_measurement_is_current_and_meets_its_marks():
    report = nas.nearest_address_report()
    assert report.get("available"), report.get("reason")
    assert report["met"] == report["taken"], report["marks"]
