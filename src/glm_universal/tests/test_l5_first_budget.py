"""Tests for ``L5`` at the first round's budget (Phase 152,
``studies/L5_FIRST_BUDGET_STUDY.md``).

These pin:

* the **prefix property** (P0): an ensemble of 240 starts is the first 240 of
  the 1,920-start ensemble of the same seed, so the 240-start reading reads
  the same walks the first round read;
* the **1,920-start figures** the comparison is made against, from the stored
  query profiles: 44 of 44 correct, 0 wrong, 0 refused, 396 absences and none
  of them false;
* the **stored measurement**: current, meeting its three marks, with the
  figures of the study (43 correct, 0 wrong, 1 refused -- ``walk 6 · sibling
  centre`` -- 10 of 10 seed queries, and the 20 reference ensembles agreeing
  with the stored share ensembles cut at 240).

Created 31 October 2026 (repository check: the file was named in
``tests/README.md`` and lost in the October 2026 reorganisation; written from
the README row and the study).
"""

from __future__ import annotations

from glm_universal.reasoning import deep_hole_escalation as de
from glm_universal.reasoning import l5_first_budget as lfb


def test_a_240_start_ensemble_is_a_prefix_of_the_1920_start_one():
    seeds = [de.REFERENCE_SEED, de.SANITY_SEED]
    p = lfb.p0_prefix(seeds)
    assert p["seeds"] == len(set(seeds))
    assert p["prefix"] == p["seeds"], p["rows"]
    assert lfb.STARTS == 240 and lfb.FULL_STARTS == 1920


def test_the_1920_start_figures_the_comparison_is_made_against():
    full = lfb.at_full()
    assert full is not None, "the stored query profiles are not current"
    assert full["starts"] == lfb.FULL_STARTS
    assert full["queries"] == 44
    assert (full["correct"], full["wrong"], full["refused"]) == (44, 0, 0)
    assert full["seed_correct"] == full["seed_queries"] == 10
    assert full["within_answered"] == full["within_radius"] == 44
    assert (full["absences"], full["false_absences"]) == (396, 0)


def test_the_stored_measurement_is_current_and_meets_its_marks():
    report = lfb.current()
    assert report is not None, lfb.state()
    assert report["met"] == report["taken"] == 3, report["marks"]
    r = report["reading"]
    assert r["starts"] == lfb.STARTS
    assert (r["correct"], r["wrong"], r["refused"]) == (43, 0, 1)
    assert [q["query"] for q in r["refused_queries"]] == \
        ["walk 6 · sibling centre"]
    assert r["seed_correct"] == r["seed_queries"] == 10
    assert r["within_answered"] == r["within_radius"] == 43
    assert report["prefix"]["prefix"] == report["prefix"]["seeds"] > 0
    check = report["ensemble_check"]
    assert check["available"] and check["agree"] == check["checked"] == 20
