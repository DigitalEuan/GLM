"""Tests for ``reasoning/probe_budget`` -- the certifying reading's stopping
rule (Phase 124).

``studies/PROBE_BUDGET_STUDY.md`` pre-registered the rule -- no barren stop,
a budget of 1056 starts -- and six marks.  These tests pin:

* the **constants**: the budget, the share constant and the census
  convention, and the held-out walk indices as declared;
* the **Lean file**: it exists, names its theorems and has no ``sorry``;
* the **model's hypothesis** on the stored ensembles (P2);
* the stored **readings** (which must describe their sources, D4): the 23
  references as recorded, every held-out deep hole certified, agreement with
  the census convention, and no reading run to the budget -- the marks as
  §7 of the study scores them.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import probe_budget as pb

_ROOT = Path(__file__).resolve().parents[3]


def test_the_declared_constants():
    assert pb.BUDGET == 1056
    assert pb.SHARE_CONSTANT == Fraction(1, 2)
    assert (pb.CENSUS_PROBES, pb.CENSUS_PATIENCE) == (400, 60)
    assert pb.HELDOUT_INDICES == tuple(range(3000, 3256))


def test_the_lean_file_states_the_rule_and_has_no_sorry():
    text = (_ROOT / "src" / "lean" / pb.LEAN_MODULE).read_text(
        encoding="utf-8")
    for name in ("miss_bound", "budget_mono", "niemeier_vertexCount_le",
                 "budget_1056_suffices", "budget_serves_every_type"):
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "(1 - p) ^ 1056 ≤ 1 / 1000" in text


def test_the_model_hypothesis_holds_on_the_stored_ensembles():
    shares = pb.share_check()
    if not shares["rows"]:
        pytest.skip("the stored ensembles are absent or stale")
    assert shares["holes"] == 23
    assert len(shares["rows"]) == 46
    assert shares["holds"] is True
    assert shares["least"] == Fraction(101, 160)       # A_1^24


@pytest.fixture(scope="module")
def report():
    rep = pb.probe_budget_report()
    if not rep["available"]:
        pytest.skip(rep["reason"])
    return rep


def test_the_references_read_as_recorded(report):
    assert len(report["references"]) == 23
    assert report["references_certified"] == 23


def test_every_held_out_deep_hole_is_certified_by_the_rule(report):
    assert report["walks"] == report["reached"] == 256
    assert report["rule_certified"] == 256
    assert report["census_certified"] == 252
    assert sum(report["census_missed_by_type"].values()) == 4


def test_the_budget_never_stops_a_reading(report):
    assert report["max_starts"] < pb.BUDGET
    assert report["max_starts"] == 254
    assert report["median_starts"] == 96


def test_the_marks_as_scored(report):
    assert report["marks"] == {"P1": True, "P2": True, "P3": True,
                               "P4": True, "P5": True, "P6": True}


def test_the_module_is_exact():
    assert ex.module_float_sites(Path(pb.__file__)) == {}
