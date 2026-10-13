"""Tests for ``reasoning/placement_guard`` -- the placement guard (Phase 129).

``studies/PLACEMENT_GUARD_STUDY.md`` pre-registered the rule, a fourth query
set and nine marks.  These tests pin:

* the **Lean file** -- its theorems, no ``sorry``, no axiom;
* the **exact test** and the **radii** on a small declared example;
* the **fourth set** -- as declared: four perturbations, offset 1024, used by
  no earlier set;
* the stored **measurement** -- the four sets, the union retirement and the
  marks, read from the cache, which must describe the sources (D4).
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import cell_guard as cg
from glm_universal.reasoning import ladder_escalation as LE
from glm_universal.reasoning import norm256_hex as nh
from glm_universal.reasoning import placement_guard as pg

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "overlay" / "glm_lean" / pg.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in pg.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text
    assert "import RequestProject.GLM.CellGuard" in text


def test_the_exact_test_and_the_radii_on_a_small_example():
    assert pg.exact_lt(Fraction(1), Fraction(1), Fraction(9))      # 1 + 1 < 3
    assert not pg.exact_lt(Fraction(1), Fraction(4), Fraction(9))  # 1 + 2 = 3
    zero = (Fraction(0),) * 24
    carriers = (("r", "a", zero),
                ("r", "b", (Fraction(3),) + (Fraction(0),) * 23),
                ("r", "c", (Fraction(0), Fraction(5)) + (Fraction(0),) * 22))
    index = {(0,) * 24: (0,), (3,) + (0,) * 23: (1,),
             (0, 5) + (0,) * 22: (2,)}
    rads = pg.radii("Z", carriers, index)
    assert rads[(0,) * 24] == 9
    assert rads[(3,) + (0,) * 23] == 9
    assert rads[(0, 5) + (0,) * 22] == 25


def test_the_fourth_set_is_as_declared_and_new():
    assert pg.FOURTH_OFFSET == 1024
    assert [(s, m) for _l, s, m in pg.FOURTH] == [
        (24, Fraction(1, 4)), (12, Fraction(1, 2)), (10, Fraction(3, 4)),
        (2, Fraction(2))]
    carriers = LE.sample_carriers()
    n = len(carriers)
    offsets = {0, nh.HELD_OUT_OFFSET, cg.THIRD_OFFSET, pg.FOURTH_OFFSET}
    assert len(offsets) == 4
    assert all(abs(a - b) >= n for a in offsets for b in offsets if a != b)
    assert len(pg.fourth_queries(carriers)) == 4 * n == 568


def test_the_stored_measurement_describes_the_sources():
    assert pg.state()["verdict"] == "fresh"
    assert pg.current() is not None


def test_the_radii_are_at_least_the_packing_radius():
    report = pg.current()
    assert report is not None
    assert all(row["below_packing"] == 0 for row in report["radii"])
    assert [row["rung"] for row in report["radii"]] == list(pg.LADDER)


def test_the_placement_guard_on_four_sets():
    report = pg.current()
    assert report is not None
    read = report["read"]
    assert {name: (r["placed"]["correct"], r["placed"]["wrong"])
            for name, r in read.items()} == {
        "standard": (445, 0), "held_out": (402, 0), "third": (393, 0),
        "fourth": (402, 0)}
    assert {name: (r["plain"]["totals"]["middle_out"]["correct"],
                   r["plain"]["totals"]["middle_out"]["wrong"])
            for name, r in read.items()} == {
        "standard": (467, 0), "held_out": (435, 8), "third": (426, 1),
        "fourth": (441, 2)}
    for r in read.values():
        assert r["p1_violations"] == 0 and r["n1_violations"] == 0
        assert r["placed"]["order_independent"]
        assert r["cell"]["wrong"] == 0


def test_the_union_retirement_and_the_marks():
    report = pg.current()
    assert report is not None
    assert tuple(report["union"]["ladder"]) == ("8C", "8A", "4C", "2C", "2A")
    fourth = report["union_fourth"]
    assert (fourth["correct"], fourth["wrong"]) == (386, 0)
    assert report["marks"] == {"P1": True, "N1": True, "S1": True,
                               "S2": True, "S3": True, "S4": True,
                               "K1": True, "U2": True}
