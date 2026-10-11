"""Tests for ``reasoning/frozen_path`` -- the lattice round's frozen-path
comparison (Phase 123, mark B5), and the marks of the round read together.

``studies/LATTICE_COMPLETION_STUDY.md`` §2.B declared that every evaluation
case present before the round returns the same answer and refusal after it.
These tests pin:

* the **baseline** -- every case it holds is still an evaluation case, and
  the round added exactly one case;
* the **declared causes** name only cases of the baseline;
* the stored **comparison** (which must describe its sources, D4): no case
  moved between answered and refused and no moved text is undeclared;
* the round's **marks**, as §7.2 scores them.
"""

from __future__ import annotations

import pytest

from glm_universal.evaluation import cases as ev
from glm_universal.reasoning import frozen_path as fp
from glm_universal.reasoning import lattice_completion as lc


def test_every_baseline_case_is_still_an_evaluation_case():
    ids = {case.id for case in ev.CASES}
    before = [str(row["id"]) for row in fp.baseline()["before"]]
    assert len(before) == len(set(before)) == 178
    assert set(before) <= ids
    assert ids - set(before) == {"report-hole-configuration"}


def test_the_declared_causes_name_only_baseline_cases():
    before = {str(row["id"]) for row in fp.baseline()["before"]}
    assert set(fp.DECLARED_CAUSES) <= before


def test_the_stored_comparison_holds():
    report = fp.frozen_path_report()
    if not report["available"]:
        pytest.skip(report["reason"])
    assert report["cases"] == report["present"] == 178
    assert report["same_status"] == 178
    assert report["undeclared"] == ()
    assert report["new_cases"] == ("report-hole-configuration",)
    assert report["holds"] is True


def test_the_marks_of_the_round_as_scored():
    report = lc.lattice_completion_report()
    marks = report["marks"]
    if marks["B5"] is None:
        pytest.skip("the frozen-path comparison is not current")
    assert marks == {
        "L1": True, "A1": False, "A2": True, "A3": False, "A4": False,
        "B1": True, "B2": True, "B3": True, "B4": True, "B5": True,
        "B6": True, "C1": True, "C2": False, "C3": True,
    }
    assert report["marks_met"] == 10 and report["marks_scored"] == 14
    post_hoc = report["census"]["post_hoc"]
    assert post_hoc["available"]
    assert post_hoc["marks"] == {"A1": True, "A2": True, "A3": True,
                                 "A4": True}
