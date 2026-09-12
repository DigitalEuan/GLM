"""Tests for ``reasoning/deep_hole_escalation`` -- the ladder round.

``studies/DEEP_HOLE_ESCALATION_STUDY.md`` fixes four readings, three ensemble
sizes, the primary statistic, the gate, the multiplicity correction and a
decision tree, and was committed before this module existed.  These tests pin
the parts of that machinery that have to be *right* rather than merely
reported:

* the **nesting** of the ensemble, which is what makes one 960-start run
  supply all twelve cells: the 240-start ensemble must be a prefix of it;
* the **bottom rung reproduces the first round**, which is the study's first
  stopping rule -- if the two rounds disagree about the same measurement,
  nothing above the bottom rung may be read;
* the **readings**, which must be exact probability vectors and measures, and
  must agree with the first round's statistic where they claim to be it;
* **cumulativity**: the widened reading's distance is never below the narrow
  one's, which is `GLM.DeepHoleLadder.Reading.cumulative_ge_left` in Python;
* the **criterion**, which is sufficient and not necessary: every measured
  cell with ``rho < 1`` must reach the gate, and the converse is not asserted;
* **the controls never rise to the method's rate**, wherever the tree ran
  them;
* the **exactness** of the module, by the static instrument of directive D7.

The measurement is a quarter of an hour of exact decoding, so the tests read
it from the cache, and one of them fails if the cache no longer describes the
sources it was taken from (D4).
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import deep_hole_classifier as dhc
from glm_universal.reasoning import deep_hole_escalation as esc
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import pipeline as ppl
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession, REPORT_SUBJECTS


@pytest.fixture(scope="module")
def stored():
    data = esc.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools escalation --write")
    return data


@pytest.fixture(scope="module")
def record():
    """A small ensemble at a real hole centre, cheap enough for a test."""
    entries, _siblings = esc.reference_entries()
    centre = tuple(Fraction(x) for x in entries[0]["center"])
    return esc.emissions(centre, esc.REFERENCE_SEED, 24)


# ---------------------------------------------------------------------------
#  1.  The ensemble, and why one run supplies every cell
# ---------------------------------------------------------------------------

def test_the_smaller_ensemble_is_a_prefix_of_the_larger():
    short = dhc.offsets(esc.REFERENCE_SEED, esc.STARTS_LADDER[0])
    long = dhc.offsets(esc.REFERENCE_SEED, esc.STARTS_LADDER[-1])
    assert long[:len(short)] == short


def test_the_ladder_is_declared_cells_then_the_extension_rung():
    assert esc.DECLARED_STARTS == (240, 480, 960)
    assert esc.EXTENSION_STARTS == (1920,)
    assert len(esc.CELLS) == len(esc.LAYER_KEYS) * len(esc.STARTS_LADDER) == 16
    assert esc.CELLS[0] == ("shares", 240)
    assert esc.CELLS[4] == ("widened", 240)
    assert esc.CELLS[-1] == ("joint", 1920)
    declared = [cell for cell in esc.CELLS if cell[1] in esc.DECLARED_STARTS]
    assert len(declared) == 12


def test_the_ensemble_is_deterministic_and_exact(record):
    entries, _siblings = esc.reference_entries()
    centre = tuple(Fraction(x) for x in entries[0]["center"])
    again = esc.emissions(centre, esc.REFERENCE_SEED, 24)
    assert record == again
    for point, distance in record:
        assert all(isinstance(x, int) for x in point)
        assert isinstance(distance, (int, Fraction))
        assert not isinstance(distance, float)


def test_no_emission_is_discarded_by_the_ensemble(record):
    assert len(record) == 24


# ---------------------------------------------------------------------------
#  2.  The readings
# ---------------------------------------------------------------------------

def test_the_shares_reading_is_the_first_rounds_statistic(record):
    counts = {}
    best = min(distance for _point, distance in record)
    for point, distance in record:
        if distance == best:
            counts[point] = counts.get(point, 0) + 1
    assert esc.share_profile(record) == dhc.share_profile(counts)


def test_the_shares_reading_is_a_probability_vector(record):
    profile = esc.share_profile(record)
    assert len(profile) == esc.PROFILE_LENGTH
    assert sum(profile) == 1
    assert list(profile) == sorted(profile, reverse=True)


def test_the_stray_reading_is_taken_over_every_emission(record):
    strays = esc.stray_profile(record)
    best = min(distance for _point, distance in record)
    stray_count = sum(1 for _point, distance in record if distance != best)
    assert sum(strays) == Fraction(stray_count, len(record))


def test_the_rational_reading_is_a_measure_sorted_by_value(record):
    measure = esc.rational_profile(record)
    assert sum(share for _value, share in measure) == 1
    assert [value for value, _share in measure] == sorted(
        value for value, _share in measure)


# ---------------------------------------------------------------------------
#  3.  The metrics
# ---------------------------------------------------------------------------

def test_wasserstein_is_zero_on_the_diagonal_and_symmetric():
    left = ((Fraction(2), Fraction(1, 2)), (Fraction(3), Fraction(1, 2)))
    right = ((Fraction(2), Fraction(1, 4)), (Fraction(4), Fraction(3, 4)))
    assert esc.wasserstein1(left, left) == 0
    assert esc.wasserstein1(left, right) == esc.wasserstein1(right, left)


def test_wasserstein_has_the_value_the_integral_gives():
    left = ((Fraction(0), Fraction(1)),)
    right = ((Fraction(1), Fraction(1)),)
    assert esc.wasserstein1(left, right) == 1
    half = ((Fraction(0), Fraction(1, 2)), (Fraction(1), Fraction(1, 2)))
    assert esc.wasserstein1(left, half) == Fraction(1, 2)


def test_wasserstein_obeys_the_triangle_inequality():
    a = ((Fraction(0), Fraction(1)),)
    b = ((Fraction(1), Fraction(1)),)
    c = ((Fraction(1, 2), Fraction(1, 3)), (Fraction(3), Fraction(2, 3)))
    assert (esc.wasserstein1(a, b)
            <= esc.wasserstein1(a, c) + esc.wasserstein1(c, b))


def test_widening_never_shrinks_a_distance(record):
    entries, _siblings = esc.reference_entries()
    other = tuple(Fraction(x) for x in entries[1]["center"])
    second = esc.emissions(other, esc.REFERENCE_SEED, 24)
    narrow = esc.layer_distance(esc.layer_profile(record, "shares"),
                                esc.layer_profile(second, "shares"), "shares")
    wide = esc.layer_distance(esc.layer_profile(record, "widened"),
                              esc.layer_profile(second, "widened"), "widened")
    joint = esc.layer_distance(esc.layer_profile(record, "joint"),
                               esc.layer_profile(second, "joint"), "joint")
    assert narrow <= wide <= joint


def test_every_reading_vanishes_on_the_same_record(record):
    for layer in esc.LAYER_KEYS:
        profile = esc.layer_profile(record, layer)
        assert esc.layer_distance(profile, profile, layer) == 0


def test_an_unknown_layer_is_refused_rather_than_guessed(record):
    with pytest.raises(ValueError):
        esc.layer_profile(record, "not a rung")
    with pytest.raises(ValueError):
        esc.layer_distance((), (), "not a rung")


# ---------------------------------------------------------------------------
#  4.  The measurement, read from the cache
# ---------------------------------------------------------------------------

def test_the_cache_describes_the_sources_it_was_taken_from():
    assert esc.state()["verdict"] == "fresh"


def test_the_bottom_rung_reproduces_the_first_round(stored):
    tree = stored["decision"]
    bottom = tree["bottom"]
    assert bottom["layer"] == "shares"
    assert bottom["starts"] == 240
    assert bottom["q0"] == esc.REPRODUCTION_EXPECTED
    assert tree["reproduces"] is True


def test_every_cell_reports_a_count_within_its_gate(stored):
    for cell in stored["cells"]:
        assert 0 <= cell["q0"] <= cell["gate"]
        assert cell["gate"] == len(stored["labels"])
        assert cell["separation"] >= 0
        assert cell["spread"] >= 0


def test_a_rung_that_conflates_two_references_reports_no_ratio(stored):
    for cell in stored["cells"]:
        if cell["separation"] == 0:
            assert cell["ratio"] is None, (
                "a rung whose references are not separated has no ratio to "
                "report, and must say so rather than divide")
            assert cell["ratio_below_one"] is False


def test_the_criterion_is_sufficient_wherever_it_holds(stored):
    for cell in stored["cells"]:
        if cell["ratio_below_one"]:
            assert cell["passes"], (
                f"{cell['layer']} at {cell['starts']} starts has rho < 1 and "
                "does not reach the gate, which contradicts "
                "GLM.DeepHoleLadder.nearest_correct")


def test_the_ratio_is_twice_the_spread_over_the_separation(stored):
    for cell in stored["cells"]:
        if cell["ratio"] is None:
            continue
        assert cell["ratio"] == 2 * cell["spread"] / cell["separation"]


def test_the_decision_takes_the_cheapest_passing_cell(stored):
    tree = stored["decision"]
    passing = [cell for cell in stored["cells"] if cell["passes"]]
    if passing:
        assert tree["winner"] is not None
        assert (tree["winner"]["layer"], tree["winner"]["starts"]) == \
            (passing[0]["layer"], passing[0]["starts"])
    else:
        assert tree["winner"] is None
        assert tree["run_full_query_set"] is False
        assert "boundary" in tree["verdict"]


def test_the_best_cell_is_the_best_cell(stored):
    best = stored["decision"]["best"]
    assert best["q0"] == max(cell["q0"] for cell in stored["cells"])


def test_no_control_ever_rises_to_the_methods_rate(stored):
    run = stored.get("run")
    if not run:
        pytest.skip("the tree runs the query set only at a passing cell")
    assert run["beats_baseline"]
    assert run["beats_every_control"]
    method = run["method"]
    for control in run["controls"]:
        assert control["accuracy"] < method["accuracy"], (
            f"the control {control['name']} reached the method's rate, which "
            "the study says must never happen")


def test_nothing_in_the_cache_is_a_float(stored):
    def walk(value):
        if isinstance(value, float):
            raise AssertionError("a float reached the measurement cache")
        if isinstance(value, dict):
            for key, item in value.items():
                walk(key)
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)
    walk(stored)


def test_the_cost_is_reported_in_decoder_calls(stored):
    cost = stored["cost"]
    assert cost["decoder_calls"] == cost["ensembles"] * cost["starts_each"]
    assert cost["cells"] == len(esc.CELLS)


# ---------------------------------------------------------------------------
#  5.  Exactness, and the wiring D5 requires
# ---------------------------------------------------------------------------

def test_no_float_is_constructed_in_the_module():
    path = Path(esc.__file__)
    assert ex.module_float_sites(path) == {}


def test_the_subject_is_wired_and_answers():
    assert "hole ladder" in REPORT_SUBJECTS
    session = GeometricSession()
    solution = session.ask("report hole ladder")
    assert solution.kind == "report"
    assert "cells" in solution.answer
    assert solution.expected["cache"] == "fresh"
    assert solution.expected["reproduces"] == "True"
    assert solution.expected["verdict"] == "the law descends"


def test_a_passing_cell_of_the_extension_rung_is_reported_as_one(stored):
    tree = stored["decision"]
    if tree["winner"] is None:
        pytest.skip("no cell reaches the gate")
    if not tree["winner"]["declared"]:
        assert tree["winner_is_extension"] is True
        assert "extension" in tree["reading"]
        session = GeometricSession()
        assert "extension" in session.ask("report hole ladder").answer


def test_the_extension_rung_is_counted_in_the_multiplicity_correction(stored):
    run = stored.get("run")
    if not run:
        pytest.skip("the tree runs the query set only at a passing cell")
    assert run["method"]["score"]["statistics"] == esc.STATISTICS_TRIED
    assert esc.STATISTICS_TRIED == 4 + len(esc.CELLS)


def test_column_three_renders_for_the_subject():
    session = GeometricSession()
    solution = session.ask("report hole ladder")
    script = tct.render_script(solution)
    assert "deep_hole_escalation" in script


def test_the_pipeline_row_names_the_study_the_subject_and_the_lean_file():
    row = next(r for r in ppl.REGISTRY if r.key == "deep-hole-escalation")
    assert row.document == "DEEP_HOLE_ESCALATION_STUDY.md"
    assert row.subject == "hole ladder"
    assert "DeepHoleEscalation.lean" in row.lean


def test_the_two_copies_of_the_lean_file_agree():
    here = Path(esc.__file__).resolve().parents[2]
    mirror = here / "glm_lean" / "RequestProject" / "GLM" / \
        "DeepHoleEscalation.lean"
    original = here.parent / "RequestProject" / "GLM" / \
        "DeepHoleEscalation.lean"
    assert mirror.is_file()
    text = mirror.read_text(encoding="utf-8")
    for name in ("nearest_correct", "cumulative_can_break_criterion",
                 "firstResolving_least", "firstResolving_eq_none_iff"):
        assert name in text
    assert "sorry" not in text
    if original.is_file():
        assert original.read_text(encoding="utf-8") == text
