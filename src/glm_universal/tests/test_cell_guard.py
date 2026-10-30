"""Tests for ``reasoning/cell_guard`` -- the cell guard (Phase 128).

``studies/CELL_GUARD_STUDY.md`` pre-registered the guard, the union
retirement, a third query set and nine marks.  These tests pin:

* the **Lean file** -- its theorems, no ``sorry``, no axiom;
* the **exact test** -- ``guard_holds`` agrees with the square-root inequality
  it replaces (``GLM.CellGuard.sqrt_add_lt_sqrt_iff``) on a declared grid;
* the **third set** -- as declared: four perturbations, offset 3072;
* the **quantiser hypothesis** (Q1) on two rungs, recomputed live;
* the stored **measurement** -- the three sets, the union retirement and the
  marks, read from the cache, which must describe the sources (D4).
"""

from __future__ import annotations

import re
from fractions import Fraction
from math import isqrt
from pathlib import Path

from glm_universal.reasoning import cell_guard as cg
from glm_universal.reasoning import ladder_escalation as LE

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / cg.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in cg.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def _exact_sqrt_sum_lt(a2: int, b2: int, r2: int) -> bool:
    """``sqrt a2 + sqrt b2 < sqrt r2`` for perfect squares, by integers."""
    a, b, r = isqrt(a2), isqrt(b2), isqrt(r2)
    assert a * a == a2 and b * b == b2 and r * r == r2
    return a + b < r


def test_the_exact_test_is_the_square_root_inequality():
    for a in range(0, 9):
        for b in range(0, 9):
            for r in range(0, 13):
                expected = _exact_sqrt_sum_lt(a * a, b * b, r * r)
                got = cg.guard_holds(Fraction(a * a), Fraction(b * b),
                                     4 * r * r)
                assert got == expected, (a, b, r)


def test_the_third_set_is_as_declared():
    assert cg.THIRD_OFFSET == 3072
    assert [(s, m) for _l, s, m in cg.THIRD] == [
        (16, Fraction(1, 2)), (8, Fraction(1)), (4, Fraction(3, 2)),
        (20, Fraction(1, 4))]
    assert [s * m * m for _l, s, m in cg.THIRD] == [4, 8, 9, Fraction(5, 4)]
    carriers = LE.sample_carriers()
    assert len(cg.third_queries(carriers)) == 4 * len(carriers) == 568


def test_the_quantiser_hypothesis_on_two_rungs():
    for rung in ("Z", "C"):
        assert cg.quantiser_hypothesis(rung, vectors=40)["holds"]


def test_the_stored_measurement_describes_the_sources():
    assert cg.state()["verdict"] == "fresh"
    assert cg.current() is not None


def test_the_guard_is_safe_and_certified_on_three_sets():
    report = cg.current()
    assert report is not None
    read = report["read"]
    assert {name: r["queries"] for name, r in read.items()} == {
        "standard": 568, "held_out": 568, "third": 568}
    assert {name: (r["plain"]["correct"], r["plain"]["wrong"])
            for name, r in read.items()} == {
        "standard": (467, 0), "held_out": (439, 8), "third": (426, 1)}
    assert {name: (r["guarded"]["correct"], r["guarded"]["wrong"])
            for name, r in read.items()} == {
        "standard": (30, 0), "held_out": (12, 0), "third": (12, 0)}
    for r in read.values():
        assert r["n1_violations"] == 0 and r["n2_violations"] == 0
        assert r["guarded"]["order_independent"]


def test_the_union_retirement_and_the_marks():
    report = cg.current()
    assert report is not None
    assert tuple(report["union"]["ladder"]) == ("8C", "8A", "4C", "2C", "2A")
    third = report["union_third"]
    assert (third["correct"], third["wrong"]) == (388, 0)
    assert report["marks"] == {"Q1": True, "N1": True, "N2": True,
                               "S1": True, "S2": True, "S3": True,
                               "K1": False, "U1": True}
