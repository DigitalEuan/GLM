"""Tests for the address read and the `locate` kind (Phase 143).

``studies/ADDRESS_READ_STUDY.md`` pre-registered ten marks.  These tests pin:

* the **Lean file** (L1): it states the theorems the read relies on and has
  no ``sorry``;
* the **stored table** and its three digests, and the twelve tamperings of
  T1, each refused ``stale-table``;
* the **margin bound** (``margin_lower``): never above the true margin;
* the **read** on a small declared example, and the **request grammar** with
  every named refusal;
* the **query kind**: start-only, and the seventeen declared questions
  through the session (Q1's own half; the scripts and mutants are measured);
* the **fifth set** as declared;
* the **wiring census** (W1's own half);
* the stored **measurement** -- the six sets and the marks, read from the
  cache, which must describe the sources (D4).
"""

from __future__ import annotations

import re
from fractions import Fraction
from math import isqrt
from pathlib import Path

import pytest

from glm_universal.reasoning import address_read as ar
from glm_universal.reasoning import address_read_study as ars
from glm_universal.reasoning import address_table as at
from glm_universal.reasoning import cell_guard as cg
from glm_universal.reasoning import norm256_hex as nh
from glm_universal.reasoning import placement_guard as pg
from glm_universal.runtime.parser import KINDS, parse_query

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / ar.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in ar.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text
    assert "import RequestProject.GLM.PlacementGuard" in text


def test_the_table_is_fresh_and_covers_the_ladder():
    assert at.state()["verdict"] == "fresh"
    stored = at.current()
    assert stored is not None
    assert stored["ladder"] == list(pg.LADDER)
    assert len(stored["carriers"]) == len(at.carriers()) == 142
    table = ar.load_table()
    assert set(table) == set(pg.LADDER)


def test_every_tampering_is_refused():
    out = ars.tamperings()
    assert out["intact_loads"]
    assert out["rows"] == {how: "stale-table" for how in ars.TAMPERINGS}
    assert (out["refused"], out["of"]) == (12, 12)


@pytest.mark.parametrize("rho2,b2", [
    (Fraction(9), Fraction(1)), (Fraction(20, 3), Fraction(0)),
    (Fraction(2), Fraction(1, 7)), (Fraction(10 ** 9 + 7, 3), Fraction(5, 11)),
    (Fraction(1), Fraction(4))])
def test_the_margin_bound_never_overstates(rho2, b2):
    # margin_bound returns a - b with a^2 <= rho2 and b^2 >= b2, b >= 0, so
    # a - b <= sqrt(rho2) - sqrt(b2) (GLM.AddressRead.margin_lower).
    m = ar.margin_bound(rho2, b2)
    scale = ar.MARGIN_SCALE
    n = -((-b2 * scale * scale) // 1)
    b = isqrt(int(n))
    if b * b < n:
        b += 1
    b = Fraction(b, scale)
    a = m + b
    assert b >= 0 and b * b >= b2
    assert a >= 0 and a * a <= rho2
    assert (a + Fraction(1, scale)) ** 2 > rho2      # and it is tight
    assert (m * scale).denominator == 1


def test_the_margin_text_is_exact():
    assert ar.margin_text(Fraction(2581, 1000)) == "2.581"
    assert ar.margin_text(Fraction(-1, 1000)) == "-0.001"
    assert ar.margin_text(Fraction(7)) == "7.000"


def _toy():
    zero = (Fraction(0),) * 24
    rows = (("r", "a", zero),
            ("r", "b", (Fraction(8),) + (Fraction(0),) * 23),
            ("r", "c", (Fraction(0), Fraction(8)) + (Fraction(0),) * 22))
    index = {nh.quantise(c, "Z"): (i,) for i, (_r, _n, c) in enumerate(rows)}
    rads = pg.radii("Z", rows, index)
    table = {"Z": {p: ("single", (m[0], rads[p])) for p, m in index.items()}}
    return rows, table


def test_the_read_on_a_small_example():
    rows, table = _toy()
    near_a = (Fraction(1, 3),) + (Fraction(0),) * 23
    read = ar.read_point(near_a, table, rows, order=("Z",),
                         delta2=Fraction(1, 9))
    assert (read.status, read.carrier, read.rung) == ("answered", 0, "Z")
    assert read.origin_certified is True
    assert read.margin > 0
    # Halfway between a and b the cell is a's or b's, and the guard fails.
    middle = (Fraction(4),) + (Fraction(0),) * 23
    read = ar.read_point(middle, table, rows, order=("Z",))
    assert read.status == "refused"
    assert read.rows[0]["cell"] in ("single", "empty")


def test_the_request_grammar():
    rows = at.carriers()
    parts = ar.parse_request("C moved 8 by 1/2", rows)
    assert parts["delta2"] == 2 and rows[parts["origin"]][1] == "C"
    parts = ar.parse_request("physics:acceleration moved 8 by 1/4 word 7",
                             rows)
    assert rows[parts["origin"]][:2] == ("physics", "acceleration")
    parts = ar.parse_request(", ".join(["0"] * 24) + " within 1/2", rows)
    assert parts["delta2"] == Fraction(1, 4) and parts["origin"] is None
    assert ar.parse_request("carbon dioxide", rows)["origin"] is not None
    for bad, reason in (("water", "ambiguous-name"),
                        ("Fe", "unknown-name"), ("xyz:C", "unknown-name"),
                        ("1, 2, 3", "dimension"),
                        ("C moved 30 by 1/2", "malformed"),
                        ("C moved 8 by x", "malformed"),
                        ("C moved 8 by -1", "malformed"),
                        ("C please", "malformed"),
                        ("", "malformed")):
        with pytest.raises(ar.AddressError) as info:
            ar.parse_request(bad, rows)
        assert info.value.reason == reason, bad


def test_the_kind_is_start_only():
    assert "locate" in KINDS
    assert parse_query("locate C").kind == "locate"
    assert parse_query("locate point 1, 2").options["request"] == "1, 2"
    assert parse_query("where do I locate the carrier of energy").kind \
        != "locate"


@pytest.mark.parametrize("qid,text,declared", ars.BATTERY)
def test_q1_the_declared_questions(qid, text, declared):
    from glm_universal.runtime.session import GeometricSession
    session = GeometricSession(domains=())
    solution = session.solve(parse_query(text))
    if declared[0] == "refused":
        assert not solution.ok, solution.answer
        assert f"({declared[1]})" in solution.error
    elif declared[0] == "answered":
        assert solution.ok, solution.error
        assert solution.payload["carrier"] == declared[1]
        if declared[2] is not None:
            assert bool(solution.payload["origin_certified"]) is declared[2]
    else:
        assert solution.ok or "(no-certified-rung)" in solution.error


def test_the_fifth_set_is_as_declared_and_new():
    assert ars.FIFTH_OFFSET == 512
    assert [(s, m) for _l, s, m in ars.FIFTH] == [
        (16, Fraction(1, 4)), (6, Fraction(1)), (24, Fraction(1, 2)),
        (3, Fraction(3, 2))]
    rows = at.carriers()
    n = len(rows)
    offsets = {0, nh.HELD_OUT_OFFSET, cg.THIRD_OFFSET, pg.FOURTH_OFFSET,
               ars.FIFTH_OFFSET}
    assert len(offsets) == 5
    assert all(abs(a - b) >= n for a in offsets for b in offsets if a != b)
    assert len(ars.fifth_queries(rows)) == 4 * n == 568


def test_the_wiring_census_passes_with_the_guards_reached():
    out = ars.wiring()
    assert not out["census"]["undeclared"]
    assert not out["census"]["stale_declarations"]
    assert out["guards_reached"] == ["cell_guard", "norm256_hex",
                                     "placement_guard"]
    assert out["diverted"] == []


def test_the_stored_measurement_describes_the_sources():
    assert ars.state()["verdict"] == "fresh"
    assert ars.current() is not None


def test_the_six_sets_and_the_marks():
    report = ars.current()
    assert report is not None
    sets = report["sets"]
    assert {name: (sets[name]["correct"], sets[name]["wrong"])
            for name in ("standard", "held_out", "third", "fourth")} == {
        "standard": (445, 0), "held_out": (402, 0), "third": (393, 0),
        "fourth": (402, 0)}
    for name, row in sets.items():
        assert row["not_strict_nearest"] == 0, name
        assert row["margin_violations"] == 0, name
        assert row["orders_disagree"] == 0, name
        assert row["origin_violations"] == 0, name
        assert row.get("reference_disagreements", 0) == 0, name
    assert (sets["clean"]["correct"], sets["clean"]["wrong"]) == (125, 0)
    assert (sets["fifth"]["correct"], sets["fifth"]["wrong"]) == (402, 0)
    assert report["marks"] == {k: True for k in (
        "A1", "A2", "A3", "A4", "O1", "C1", "T1", "Q1", "W1")}
    q = report["questions"]
    assert (q["scripts"], q["answered"]) == (7, 7)
    assert (q["mutants_rejected"], q["mutants"]) == (14, 14)
