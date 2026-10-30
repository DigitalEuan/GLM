"""Tests for register junctions: the `locate` read over carriers that share
coordinates (Phase 144).

``studies/COORDINATE_JUNCTION_STUDY.md`` pre-registered nine marks.  These
tests pin:

* the **Lean file** (L1): it states the theorems the junction read relies on
  and has no ``sorry``;
* the **declarations**: each names exactly one junction of the live
  carriers, and an undeclared junction is described as distinct;
* the **junction table** and its digests, fresh, and refused when a
  declaration or the address table moves;
* the **read**: every Phase 143 answer on the clean set unchanged, the
  duplicates read as their junctions, the crowded zero junction refused;
* the **questions** through the session, and their column-3 scripts;
* the stored **measurement**, read from the cache, which must describe the
  sources (D4).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from glm_universal.reasoning import address_read as ar
from glm_universal.reasoning import address_table as at
from glm_universal.reasoning import coordinate_junction as cj
from glm_universal.reasoning import coordinate_junction_study as cjs

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / cj.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in cj.LEAN_THEOREMS:
        assert re.search(rf"^theorem {re.escape(name)}\b", text,
                         re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text
    assert "import RequestProject.GLM.AddressRead" in text


def test_the_declarations_name_the_live_junctions():
    rows = at.carriers()
    assert cj.check_declarations(rows) == []
    live = {frozenset(cj._labels(rows, g)) for g in cj.junctions(rows)}
    assert len(live) == len(cj.DECLARATIONS) == 4
    assert sum(len(g) for g in cj.junctions(rows)) == 15
    for dec in cj.DECLARATIONS:
        assert dec.kind in ("identity", "distinct")


def test_an_undeclared_junction_is_read_as_distinct():
    labels = cj.DECLARATIONS[0].members
    assert "undeclared" in cj.describe(labels, ())
    assert "identity" not in cj.describe(labels, ())
    assert "declared distinct" in cj.describe(labels)


def test_the_junction_table_is_fresh_and_refuses_drift():
    rows = at.carriers()
    assert cj.state()["verdict"] == "fresh"
    table, st = cj.load()
    assert table is not None and st["fresh"]
    stale = cj.DECLARATIONS + (cj.Declaration(
        ("physics:absorptance", "chemistry:C"), "identity", "x", "x"),)
    assert "declarations" in cj.state(None, rows, None, stale)["failed"]
    moved = cj.DECLARATIONS[1:]
    assert cj.load(None, rows, None, moved)[0] is None


def test_the_read_keeps_every_phase_143_answer_on_the_clean_set():
    rows = at.carriers()
    table = ar.load_table()
    jtable, _st = cj.load()
    duplicates = set(cjs.DUPLICATES(rows))
    junction_answers = 0
    for i in range(len(rows)):
        plain = ar.read_point(rows[i][2], table, rows)
        read = cj.read_point(rows[i][2], table, jtable, rows)
        if plain.status == "answered":
            assert (read.carrier, read.rung, read.members) == (
                plain.carrier, plain.rung, (plain.carrier,))
        elif read.status == "answered":
            assert i in duplicates and i in read.members
            assert len(read.members) > 1
            junction_answers += 1
    assert junction_answers == 13


def test_the_zero_junction_is_crowded_and_refused():
    rows = at.carriers()
    read = cj.read_point([0] * 24, ar.load_table(), cj.load()[0], rows)
    assert read.status == "refused"


@pytest.mark.parametrize("qid,text,declared", cjs.BATTERY)
def test_q1_the_declared_questions(qid, text, declared):
    from glm_universal.runtime.parser import parse_query
    from glm_universal.runtime.session import GeometricSession
    sol = GeometricSession(domains=()).solve(parse_query(text))
    if qid in ("J-B4", "J-B6"):
        # declared junctions, measured refused: the zero junction is crowded
        assert not sol.ok and "no-certified-rung" in (sol.error or "")
    elif declared[0] == "junction":
        assert sol.ok
        assert set(sol.payload["junction"]) == set(declared[1])
        assert "no_read_separates" in sol.answer
    elif declared[0] == "carrier":
        assert sol.ok and sol.payload["carrier"] == declared[1]
    elif declared[0] == "refused":
        assert not sol.ok and declared[1] in (sol.error or "")
    else:
        assert sol.ok and len(sol.payload["junction"]) > 1


def test_a_junction_answer_passes_its_script():
    from glm_universal.runtime import tct_engine as tct
    from glm_universal.runtime.parser import parse_query
    from glm_universal.runtime.session import GeometricSession
    sol = GeometricSession(domains=()).solve(parse_query("locate albedo"))
    assert tct.verify_trace(tct.build_trace(sol)).verdict.matches_column2


def test_the_stored_measurement_describes_the_sources():
    assert cjs.state()["verdict"] == "fresh"


def test_the_marks():
    report = cjs.current()
    assert report is not None
    marks = report["marks"]
    for mark in ("J1", "J2", "J3", "T1"):
        assert marks[mark], mark
    # J4, J5 and Q1 were missed as declared (the study's section 7)
    assert report["duplicates"]["duplicates_read"] == 13
    assert report["census"]["cross_register"] == 0
    for row in report["sets"].values():
        assert row["changed"] == 0 and row["wrong"] == 0
