"""Tests for ``reasoning/deep_hole_failures`` -- the four failures, opened.

``studies/DEEP_HOLE_FAILURE_STUDY.md`` asks what the four queries the escalated
reading does not name have in common, and whether that is the same mechanism
that keeps the separation ratio above its criterion.  It is read at a single
pre-registered cell, and these tests pin the parts of the round that have to be
*right* rather than merely reported:

* the **cell is one cell** -- the layer and the budget are the escalation
  round's passing cell, fixed as constants, so no result here can be the best
  of a search along the layer axis (D13);
* the **stopping rule** -- the round reproduces the escalation round's own
  figure at that cell, or nothing below it is read;
* the **diagnoses are scored by rules fixed in advance**, are not forced to be
  exclusive, and report the outcome that would refute all four at once;
* **a failure is a statement about the references**: every failure sits on a
  closest reference pair, which `GLM.DeepHoleFailure.failure_pair_close` says
  it must;
* the **deletion sweep can only make the criterion easier**, which is
  `resolves_of_subset` and is why the sweep locates the spread rather than
  certifying anything;
* the **per-type criterion certifies what it claims** -- every query of a
  certified type is in fact named correctly, which is `per_type_correct` on
  this data;
* the **original negative is kept**, and the **control** on the bimodality
  rule is reported as a control;
* the **exactness** of the module, by the static instrument of directive D7.

The measurement is a long exact decode, so the tests read it from the cache,
and one of them fails if the cache no longer describes the sources it was taken
from (D4).
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import deep_hole_escalation as esc
from glm_universal.reasoning import deep_hole_failures as dhf
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import pipeline as ppl
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def stored():
    data = dhf.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools failures --write")
    return data


# ---------------------------------------------------------------------------
#  1.  One cell, declared before the round
# ---------------------------------------------------------------------------

def test_the_cell_is_the_escalation_rounds_passing_cell():
    assert dhf.CELL_LAYER == "joint"
    assert dhf.CELL_STARTS == 1920
    assert (dhf.CELL_LAYER, dhf.CELL_STARTS) in esc.CELLS
    assert dhf.CELL_LAYER in esc.LAYER_KEYS


def test_the_half_split_is_a_rung_boundary_and_not_a_new_object():
    assert dhf.HALF == dhf.CELL_STARTS // 2
    assert dhf.HALF in esc.STARTS_LADDER


def test_the_round_reads_that_cell_and_reports_no_other(stored):
    cell = stored["cell"]
    assert cell["layer"] == dhf.CELL_LAYER
    assert cell["starts"] == dhf.CELL_STARTS
    assert "no cell other than" in str(stored["limits"])


def test_the_diagnosis_rules_are_constants_fixed_before_the_ranks(stored):
    assert dhf.SHORTLIST_DEPTH == 3
    assert dhf.CLOSE_PAIR_RANK == 5
    assert dhf.SUBSETS_TRIED == 10 + 45
    assert stored["subsets_tried"] == dhf.SUBSETS_TRIED


# ---------------------------------------------------------------------------
#  2.  The stopping rule
# ---------------------------------------------------------------------------

def test_the_round_reproduces_the_escalation_round_at_the_same_cell(stored):
    rep = stored["reproduction"]
    assert rep["queries"] == dhf.EXPECTED_QUERIES == 44
    assert rep["correct"] == dhf.EXPECTED_CORRECT == 40
    assert rep["reproduces"] is True
    assert rep["failures"] == len(stored["failures"]) == 4


def test_every_query_is_ranked_against_every_reference(stored):
    for row in stored["queries"]:
        assert len(row["ranked"]) == 10
        labels = [label for label, _distance in row["ranked"]]
        assert len(set(labels)) == 10
        distances = [distance for _label, distance in row["ranked"]]
        assert distances == sorted(distances)


def test_the_distances_are_exact_rationals(stored):
    for row in stored["queries"][:5]:
        for _label, distance in row["ranked"]:
            assert isinstance(distance, (int, Fraction))
            assert not isinstance(distance, float)


# ---------------------------------------------------------------------------
#  3.  The four failures
# ---------------------------------------------------------------------------

def test_every_failure_is_a_rank_two_near_miss_and_not_a_crossing(stored):
    for row in stored["failures"]:
        assert row["own_rank"] == 2
        assert row["d_absent_from_shortlist"] is False
        assert row["margin"] > 0


def test_every_failure_sits_on_a_closest_reference_pair(stored):
    for row in stored["failures"]:
        assert row["a_closest_pair"] is True
        assert row["pair_rank"] <= dhf.CLOSE_PAIR_RANK


def test_the_failing_pair_is_never_further_apart_than_twice_the_spread(stored):
    """`GLM.DeepHoleFailure.failure_pair_close`, on this data.

    A query named as another type lies at least as close to the winner as to
    its own reference, so the two references are within twice the query's own
    distance -- the failure is a statement about the references.
    """
    rows = {row["query"]: row for row in stored["queries"]}
    for failure in stored["failures"]:
        query = rows[failure["query"]]
        assert failure["pair_distance"] <= 2 * Fraction(query["own_distance"])


def test_the_diagnoses_are_not_forced_to_be_exclusive(stored):
    counts = stored["counts"]
    fired = (counts["a_closest_pair"] + counts["b_bimodal"]
             + counts["c_tie"] + counts["d_absent_from_shortlist"])
    assert fired >= len(stored["failures"])
    # and the outcome that would refute all four at once is reported
    assert counts["none_of_the_four"] == 0


def test_a_failure_that_matched_none_of_the_four_would_be_named(stored):
    for row in stored["failures"]:
        expected = not (row["a_closest_pair"] or row["b_bimodal"]
                        or row["c_tie"] or row["d_absent_from_shortlist"])
        assert row["none_of_the_four"] is expected


# ---------------------------------------------------------------------------
#  4.  The spread, and why it is one mechanism
# ---------------------------------------------------------------------------

def test_the_type_that_stalls_the_ratio_is_a_type_the_failures_belong_to(stored):
    assert stored["worst_spread_type"] in stored["failing_types"]
    assert stored["same_mechanism"] is True


def test_the_ratio_is_two_spreads_over_the_closest_separation(stored):
    spread = stored["spread"]
    assert (Fraction(spread["rho_seed"])
            == 2 * Fraction(spread["worst_seed_spread"])
            / Fraction(spread["separation"]))
    assert (Fraction(spread["rho_all"])
            == 2 * Fraction(spread["worst_spread"])
            / Fraction(spread["separation"]))


def test_the_closest_separation_is_the_first_reference_pair(stored):
    pairs = stored["pairs"]
    assert len(pairs) == 45
    assert pairs[0]["rank"] == 1
    assert Fraction(stored["spread"]["separation"]) == Fraction(
        pairs[0]["distance"])
    assert set(stored["spread"]["closest_pair"]) == {pairs[0]["left"],
                                                     pairs[0]["right"]}


def test_the_original_negative_is_kept_beside_the_new_reading(stored):
    negative = stored["original_negative"]
    assert negative["stands"] is True
    assert negative["criterion"] == "rho < 1"
    assert Fraction(negative["rho_at_the_passing_cell"]) > 1


# ---------------------------------------------------------------------------
#  5.  The deletion sweep
# ---------------------------------------------------------------------------

def test_the_sweep_enumerates_every_one_and_two_type_deletion(stored):
    sweep = stored["leave_out"]
    assert len(sweep["one"]) == 10
    assert len(sweep["two"]) == 45
    assert sweep["subsets_tried"] == 55


def test_a_deletion_can_only_make_the_criterion_easier(stored):
    """`GLM.DeepHoleFailure.resolves_of_subset`, on this data.

    Deleting references removes spreads and can only widen the closest
    separation, so no sub-table's ratio exceeds the full table's.  That is why
    the sweep locates the spread and certifies nothing.
    """
    sweep = stored["leave_out"]
    full = Fraction(sweep["full"]["ratio"])
    for row in tuple(sweep["one"]) + tuple(sweep["two"]):
        assert Fraction(row["ratio"]) <= full


def test_the_sweep_reaches_the_criterion_nowhere(stored):
    sweep = stored["leave_out"]
    assert sweep["any_below_one"] is False
    for row in tuple(sweep["one"]) + tuple(sweep["two"]):
        assert row["below_one"] is False
        assert Fraction(row["ratio"]) >= 1


# ---------------------------------------------------------------------------
#  6.  The per-type criterion, and the control
# ---------------------------------------------------------------------------

def test_a_certified_type_is_a_type_whose_own_ratio_is_below_one(stored):
    per_type = stored["per_type"]
    by_type = {row["type"]: row for row in stored["spread"]["rows"]}
    assert per_type["total"] == len(by_type) == 10
    for label in per_type["certified"]:
        assert Fraction(by_type[label]["ratio"]) < 1
    for label, row in by_type.items():
        if label not in per_type["certified"]:
            assert Fraction(row["ratio"]) >= 1


def test_every_query_of_a_certified_type_is_in_fact_named_correctly(stored):
    """`GLM.DeepHoleFailure.per_type_correct` is a theorem; this is the data."""
    certified = set(stored["per_type"]["certified"])
    assert certified
    for row in stored["queries"]:
        if row["truth"] in certified:
            assert row["correct"] is True, row["query"]


def test_no_failure_belongs_to_a_certified_type(stored):
    certified = set(stored["per_type"]["certified"])
    for row in stored["failures"]:
        assert row["truth"] not in certified


def test_the_faithfulness_radius_is_still_incompatible(stored):
    faith = stored["faithfulness"]
    assert faith["compatible"] is False
    assert Fraction(faith["faithfulness"]) >= Fraction(
        faith["certified_radius"])
    assert Fraction(faith["shortfall"]) > 0


def test_the_bimodality_control_is_reported_beside_the_rule(stored):
    control = stored["half_control"]
    assert control["correct"] == 40
    assert control["failures"] == 4
    # the control exists to say whether "the halves disagree" discriminates,
    # so it must be reported for the correct queries too
    assert control["correct_halves_disagree"] >= 0
    assert control["failures_halves_disagree"] <= control["failures"]


# ---------------------------------------------------------------------------
#  7.  The runtime, and the record
# ---------------------------------------------------------------------------

def test_the_subject_answers_from_the_cache(stored):
    session = GeometricSession()
    solution = session.ask("report hole failures")
    assert solution.kind == "report"
    assert solution.expected["cache"] == "fresh"
    assert solution.expected["layer"] == dhf.CELL_LAYER
    assert solution.expected["starts"] == str(dhf.CELL_STARTS)
    assert solution.expected["correct"] == "40"
    assert solution.expected["same_mechanism"] == "True"
    assert solution.expected["negative_stands"] == "True"


def test_column_three_renders_for_the_subject():
    session = GeometricSession()
    script = tct.render_script(session.ask("report hole failures"))
    assert "deep_hole_failures" in script


def test_the_pipeline_row_names_the_study_the_subject_and_the_lean_file():
    row = next(r for r in ppl.REGISTRY if r.key == "deep-hole-failure")
    assert row.document == "DEEP_HOLE_FAILURE_STUDY.md"
    assert row.subject == "hole failures"
    assert "DeepHoleFailure.lean" in row.lean


def test_the_module_holds_no_float():
    assert ex.module_float_sites(Path(dhf.__file__)) == {}


def test_the_two_copies_of_the_lean_file_agree():
    here = Path(dhf.__file__).resolve().parents[2]
    mirror = here / "glm_lean" / "RequestProject" / "GLM" / \
        "DeepHoleFailure.lean"
    original = here.parent / "RequestProject" / "GLM" / "DeepHoleFailure.lean"
    assert mirror.is_file()
    text = mirror.read_text(encoding="utf-8")
    for name in ("failure_pair_close", "no_failure_of_separated",
                 "resolves_of_subset", "per_type_correct", "per_type_absent",
                 "rank_one_correct"):
        assert name in text
    assert "sorry" not in text
    if original.is_file():
        assert original.read_text(encoding="utf-8") == text
