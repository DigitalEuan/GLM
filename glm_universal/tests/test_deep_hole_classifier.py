"""Tests for ``reasoning/deep_hole_classifier`` -- the pre-registered round.

``studies/DEEP_HOLE_STUDY.md`` fixes the ensemble, the statistic, the label
rule, four controls, the multiplicity correction and a decision tree, and was
committed before this module existed.  These tests pin the parts of that
machinery which have to be *right* rather than merely reported:

* the **classifier's semantics**, which are the Python side of
  ``GLM.DeepHole``: a name only when one reference is uniquely nearest inside
  the radius, ``ambiguous`` on a tie, ``absent`` when nothing is near enough,
  and -- the theorem with teeth -- uniqueness whenever the table is separated
  by more than twice the radius;
* the **statistic**, which must be a probability vector of exact rationals,
  sorted, padded to 48, and blind to how the vertices were named;
* the **ensemble**, which must be deterministic and must agree with the frozen
  path: every vertex it arrives at is a vertex the certified reader found;
* **the controls never rise to the method's rate** -- the test the study asked
  for by name, and the one that would catch a leak of the label into the
  statistic;
* the **exactness** of the module, by the static instrument of directive D7.

The measurement itself is a quarter of an hour of exact decoding, so the tests
read it from the cache, and one of them fails if the cache no longer describes
the sources it was taken from (D4).
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import deep_hole_classifier as dhc
from glm_universal.reasoning import deep_holes as dh
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import niemeier
from glm_universal.reasoning import pipeline as ppl
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession, REPORT_SUBJECTS


@pytest.fixture(scope="module")
def stored():
    data = dhc.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools deepholes --write")
    return data


def _profile(*shares: Fraction) -> tuple:
    values = list(shares)
    return tuple(values + [Fraction(0)] * (dhc.PROFILE_LENGTH - len(values)))


# ---------------------------------------------------------------------------
#  1.  The classifier: a name, or a refusal that says which
# ---------------------------------------------------------------------------

def test_named_when_one_reference_is_uniquely_nearest():
    table = [("A", _profile(Fraction(1))),
             ("B", _profile(Fraction(1, 2), Fraction(1, 2)))]
    outcome = dhc.classify(_profile(Fraction(1)), table, Fraction(1, 2))
    assert outcome["verdict"] == "named"
    assert outcome["label"] == "A"
    assert outcome["distance"] == 0


def test_absent_when_nothing_is_within_the_radius():
    table = [("A", _profile(Fraction(1)))]
    query = _profile(Fraction(0), Fraction(1))
    outcome = dhc.classify(query, table, Fraction(1, 2))
    assert outcome["verdict"] == "absent"
    assert outcome["label"] is None
    assert outcome["distance"] > Fraction(1, 2)


def test_ambiguous_on_an_exact_tie():
    table = [("A", _profile(Fraction(1), Fraction(0))),
             ("B", _profile(Fraction(0), Fraction(1)))]
    query = _profile(Fraction(1, 2), Fraction(1, 2))
    outcome = dhc.classify(query, table, Fraction(2))
    assert outcome["verdict"] == "ambiguous"
    assert outcome["label"] is None


def test_a_separated_table_cannot_be_ambiguous():
    """The Python side of ``GLM.DeepHole.classify_named_of_separated``."""
    table = [("A", _profile(Fraction(1))),
             ("B", _profile(Fraction(0), Fraction(1))),
             ("C", _profile(Fraction(0), Fraction(0), Fraction(1)))]
    radius = dhc.certified_radius(table)
    assert radius == Fraction(1)
    for label, reference in table:
        outcome = dhc.classify(reference, table, radius)
        assert outcome["verdict"] == "named"
        assert outcome["label"] == label


def test_the_certified_radius_is_half_the_smallest_separation():
    table = [("A", _profile(Fraction(1))),
             ("B", _profile(Fraction(1, 2), Fraction(1, 2)))]
    separation = dhc.separation(table)
    assert separation["minimum"] == dhc.l1(table[0][1], table[1][1])
    assert dhc.certified_radius(table) == separation["minimum"] / 2


# ---------------------------------------------------------------------------
#  2.  The statistic
# ---------------------------------------------------------------------------

def test_the_profile_is_an_exact_sorted_probability_vector():
    counts = {(1,): 3, (2,): 1, (3,): 4}
    profile = dhc.share_profile(counts)
    assert len(profile) == dhc.PROFILE_LENGTH
    assert all(isinstance(share, Fraction) for share in profile)
    assert sum(profile) == 1
    assert list(profile) == sorted(profile, reverse=True)
    assert profile[:3] == (Fraction(1, 2), Fraction(3, 8), Fraction(1, 8))


def test_the_profile_cannot_see_how_the_vertices_were_named():
    """``GLM.DeepHole.sortedProfile_reindex``, on the Python side."""
    counts = {(1,): 3, (2,): 1, (3,): 4}
    renamed = {(7,): 4, (8,): 3, (9,): 1}
    assert dhc.share_profile(counts) == dhc.share_profile(renamed)


def test_the_uniform_ablation_is_the_vertex_count_in_the_metric():
    for support in (25, 27, 36, 48):
        profile = dhc.uniform_profile(support)
        assert sum(profile) == 1
        assert sum(1 for share in profile if share) == support
    assert dhc.l1(dhc.uniform_profile(27), dhc.uniform_profile(27)) == 0
    assert dhc.l1(dhc.uniform_profile(27), dhc.uniform_profile(28)) > 0


def test_the_digest_profile_is_a_probability_vector_and_carries_no_geometry():
    one = dhc.digest_profile("A_1^24")
    again = dhc.digest_profile("A_1^24")
    other = dhc.digest_profile("A_2^12")
    assert sum(one) == 1 and len(one) == dhc.PROFILE_LENGTH
    assert one == again
    assert one != other


def test_l1_is_a_metric_on_the_profiles_it_is_given():
    a = _profile(Fraction(1))
    b = _profile(Fraction(1, 2), Fraction(1, 2))
    c = dhc.digest_profile("C")
    assert dhc.l1(a, a) == 0
    assert dhc.l1(a, b) == dhc.l1(b, a)
    assert dhc.l1(a, c) <= dhc.l1(a, b) + dhc.l1(b, c)
    assert dhc.linf(a, b) <= dhc.l1(a, b)


# ---------------------------------------------------------------------------
#  3.  The ensemble, and its agreement with the frozen path
# ---------------------------------------------------------------------------

def test_the_offsets_are_exact_deterministic_and_start_at_zero():
    first = dhc.offsets(20260825, 8)
    second = dhc.offsets(20260825, 8)
    assert first == second
    assert first[0] == tuple([Fraction(0)] * 24)
    assert all(isinstance(value, Fraction)
               for offset in first for value in offset)
    assert all(abs(value) <= Fraction(1000, dhc.DITHER)
               for offset in first for value in offset)


def test_every_arrival_is_a_vertex_the_frozen_path_certifies():
    hole = dh.octad_pair_hole()
    center = tuple(Fraction(x) for x in hole["center"])
    ensemble = dhc.arrival_counts(center, 20260825, 12)
    assert ensemble["arrivals"] + ensemble["strays"] == 12
    assert ensemble["arrivals"] > 0
    certified = set(dh.hole_vertices(center, probes=60, patience=20)["vertices"])
    assert set(ensemble["support"]) <= certified
    # and the ensemble is a function of its declared inputs alone
    assert dhc.arrival_counts(center, 20260825, 12) == ensemble


# ---------------------------------------------------------------------------
#  4.  The score
# ---------------------------------------------------------------------------

def test_the_tail_is_exact_and_a_whole_probability_at_zero():
    assert dhc.tail_probability(0, 10, 4) == 1
    assert isinstance(dhc.tail_probability(3, 10, 4), Fraction)
    assert dhc.tail_probability(10, 10, 4) == Fraction(1, 4 ** 10)


def test_the_tail_only_falls_as_the_method_does_better():
    previous = Fraction(1)
    for correct in range(0, 11):
        tail = dhc.tail_probability(correct, 10, 5)
        assert tail <= previous
        previous = tail


# ---------------------------------------------------------------------------
#  5.  The measurement, read from the cache
# ---------------------------------------------------------------------------

def test_the_cache_is_present_and_fresh():
    condition = dhc.state()
    assert condition["present"]
    assert condition["fresh"], (
        "the measurement cache is stale; re-take it with "
        "python3 -m glm_universal.tools deepholes --write")


def test_no_control_ever_rises_to_the_method(stored):
    """The test the study asked for by name.

    If a control ever matched the method, the method would be measuring the
    control's information and not the hole's -- and the digest control rising
    at all would mean the label had leaked into the statistic (D3).
    """
    run = stored["run"]
    method = run["method"]
    for control in run["controls"]:
        assert control["accuracy"] < method["accuracy"], (
            f"the control {control['name']!r} reached the method's rate: "
            f"{control['accuracy']} vs {method['accuracy']}")
    assert run["beats_every_control"]
    assert run["beats_baseline"]
    assert run["digest"]["accuracy"] <= 2 * method["chance"]
    assert run["reshuffle"]["accuracy"] <= 2 * method["chance"]


def test_the_verdict_is_the_one_the_decision_tree_gives(stored):
    gate = stored["gate"]
    assert gate["verdict"] == "stopped at the sanity query"
    assert not gate["sanity_holds"]
    assert not gate["claims_faculty"]


def test_the_reference_labels_are_all_in_the_derived_catalogue(stored):
    catalogue = {name for name, _rank, _h in niemeier.NIEMEIER_ROOT_SYSTEMS}
    labels = [str(label) for label in stored["table"]["labels"]]
    assert labels
    assert len(labels) == len(set(labels))
    assert set(labels) <= catalogue
    assert len(labels) + len(stored["table"]["missing_types"]) == len(catalogue)


def test_every_reference_ensemble_stayed_inside_its_certified_hole(stored):
    for entry in stored["table"]["entries"]:
        assert entry["support_within_certified"]
        assert entry["support"] <= entry["certified_vertex_count"]
        assert entry["arrivals"] > 0


def test_the_certified_radius_and_faithfulness_are_reported_together(stored):
    run = stored["run"]
    assert run["certified_radius"] > 0
    assert run["faithfulness_radius"] >= 0
    assert run["faithfulness_compatible"] == (
        run["faithfulness_radius"] <= run["certified_radius"])


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


# ---------------------------------------------------------------------------
#  6.  Exactness, and the wiring D5 requires
# ---------------------------------------------------------------------------

def test_no_float_is_constructed_in_the_module():
    path = Path(dhc.__file__)
    assert ex.module_float_sites(path) == {}


def test_the_subject_is_wired_and_answers():
    assert "hole classifier" in REPORT_SUBJECTS
    session = GeometricSession()
    solution = session.ask("report hole classifier")
    assert solution.kind == "report"
    assert "arrival-share profile" in solution.answer
    assert "vertex count" in solution.answer
    assert solution.expected["cache"] == "fresh"
    assert solution.expected["verdict"] == "stopped at the sanity query"


def test_column_three_renders_for_the_subject():
    session = GeometricSession()
    solution = session.ask("report hole classifier")
    script = tct.render_script(solution)
    assert "deep_hole_classifier" in script


def test_the_pipeline_row_names_the_study_the_subject_and_the_lean_file():
    row = next(r for r in ppl.REGISTRY if r.key == "deep-hole-classifier")
    assert row.document == "DEEP_HOLE_STUDY.md"
    assert row.subject == "hole classifier"
    assert "DeepHoleClassifier.lean" in row.lean
