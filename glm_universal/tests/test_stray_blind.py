"""Tests for ``reasoning/stray_blind`` -- lattice item 10 (Phase 110).

``RequestProject/GLM/StrayBlind.lean`` proves which pairs of deep-hole records
a reading of distances alone must conflate: exactly the pairs of equal size
with equal stray spectra.  These tests pin

* the **pure readings** on hand-built records, where the theorem's three
  cases (equal strays, different strays, no strays) are each exhibited;
* the **stored census**, taken over the escalation ladder's own ensembles:
  one covering radius for every hole, and the predicted conflation set equal
  to the measured one at every ensemble size;
* the **Lean file** exists, carries the named theorems, and has no ``sorry``.

The ensembles are a quarter of an hour of exact decoding, so the census is
read from its cache, and the fixture fails if the cache no longer describes
its sources (D4).
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import stray_blind as sb

R = Fraction(16)


def _record(*distances):
    return tuple(((index,), Fraction(value))
                 for index, value in enumerate(distances))


@pytest.fixture(scope="module")
def stored():
    data = sb.current()
    assert data is not None, (
        "the stray-blind census is absent or stale; re-take it with "
        "python3 -m glm_universal.tools stray-blind --write")
    return data


def test_minimum_is_the_radius_once_one_start_arrives():
    assert sb.covering_minimum(_record(18, 16, 20)) == R
    assert sb.covering_minimum(()) is None


def test_distance_profile_is_arrivals_plus_strays():
    record = _record(16, 16, 18, 20, 18)
    profile = dict(sb.distance_profile(record))
    strays = dict(sb.stray_spectrum(record, R))
    assert profile.pop(R) == 2
    assert profile == strays


def test_equal_strays_are_conflated_whatever_the_vertices():
    # Different points, same stray spectrum: the theorem says conflated.
    left = (((1,), R), ((2,), R), ((3,), Fraction(18)))
    right = (((7,), R), ((7,), R), ((9,), Fraction(18)))
    records = {"a": left, "b": right}
    assert sb.predicted_pairs(records, R) == (("a", "b"),)
    assert sb.measured_pairs(records) == (("a", "b"),)


def test_different_strays_are_separated():
    records = {"a": _record(16, 16, 18), "b": _record(16, 16, 20),
               "c": _record(16, 18, 18)}
    assert sb.predicted_pairs(records, R) == ()
    assert sb.measured_pairs(records) == ()


def test_stray_free_records_are_all_conflated():
    records = {"x": _record(16, 16, 16), "y": _record(16, 16, 16),
               "z": _record(16, 16, 16)}
    row = sb.census(records)
    assert row["stray_free"] == ("x", "y", "z")
    assert row["predicted"] == row["measured"] == (
        ("x", "y"), ("x", "z"), ("y", "z"))
    assert row["rho_defined"] is False


def test_census_on_every_rung_agrees_with_the_theorem(stored):
    assert stored["agree_everywhere"] is True
    assert stored["common_radius_everywhere"] is True
    for row in stored["rows"]:
        assert row["predicted"] == row["measured"]
        assert row["radius"] == R


def test_the_measured_pair_is_the_one_the_ladder_reported(stored):
    for row in stored["rows"]:
        assert tuple(tuple(pair) for pair in row["measured"]) == (
            ("A_1^24", "A_2^12"),)
        assert tuple(row["stray_free"]) == ("A_1^24", "A_2^12")
        assert row["rho_defined"] is False


def test_lean_file_carries_the_theorems():
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    text = (root / sb.LEAN_MODULE).read_text(encoding="utf-8")
    for name in ("distances_decomp", "distances_eq_iff", "strayFree_conflate",
                 "arrivalMeasure_const", "distanceReading_indist",
                 "not_resolves_of_indist", "minimum_eq_radius"):
        assert f"theorem {name}" in text
    assert "sorry" not in text
