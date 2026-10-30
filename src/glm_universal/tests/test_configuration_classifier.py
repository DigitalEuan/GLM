"""Tests for ``reasoning/configuration_classifier`` -- the configuration
reading ``L5`` in the deep-hole answering path (Phase 123, part B).

``studies/LATTICE_COMPLETION_STUDY.md`` §2.B makes ``L5`` the classifier's
reading under a declared answer rule.  These tests pin what has to be *right*:

* the **answer rule is sound** -- where it answers, the answer is the strict
  nearest reference, which is `GLM.LatticeCompletion.config_answer_sound`;
* an **absence is never issued for the answer**, and a query inside its own
  type's certified radius never draws a false absence, which is the
  contrapositive half of `GLM.LatticeCompletion.config_absent`;
* the **certified radius is positive** for distinct references
  (`config_radius_pos`);
* the **uniform floor**: with every vertex's share equal, the 23 Niemeier
  profiles are pairwise at least ``4/9`` apart, the figure
  `GLM.LatticeCompletion.uniform_floor` proves, and the floor is attained;
* the **stopping rule** and the stored figures, read from the cache, which
  must describe the sources it was taken from (D4).
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

from glm_universal.reasoning import configuration_classifier as cc
from glm_universal.reasoning import configuration_queries as cq
from glm_universal.reasoning import configuration_reading as cr
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import lattice_completion as ltc


def _profile(**shares):
    return tuple(sorted(((int(k[1:].split("_")[0]), int(k.split("_")[1])),
                         Fraction(v)) for k, v in shares.items()))


_TABLE = (
    ("A", _profile(k1_2=1)),
    ("B", _profile(k2_2=1)),
    ("C", _profile(k1_2="1/2", k2_2="1/2")),
)


# ---------------------------------------------------------------------------
#  1.  The rule and the absences, on small exact tables
# ---------------------------------------------------------------------------

def test_the_certified_radius_is_half_the_nearest_other_reference():
    radii = cc.certified_radii(_TABLE)
    assert radii == {"A": Fraction(1, 2), "B": Fraction(1, 2),
                     "C": Fraction(1, 2)}
    assert all(r > 0 for r in radii.values())     # config_radius_pos


def _grid():
    steps = [Fraction(i, 8) for i in range(9)]
    for a, b in product(steps, steps):
        if a + b <= 1:
            yield ((((1, 2), a), ((2, 2), b), ((3, 1), 1 - a - b)))


def test_where_the_rule_answers_the_answer_is_the_strict_nearest():
    """`config_answer_sound` on every point of an exact grid."""
    answered = 0
    for profile in _grid():
        reading = cc.name(profile, _TABLE)
        if reading["answer"] is None:
            continue
        answered += 1
        own = dict(reading["distances"])[reading["answer"]]
        for label, distance in reading["distances"]:
            if label != reading["answer"]:
                assert own < distance
    assert answered > 0


def test_an_absence_is_never_issued_for_the_answer():
    for profile in _grid():
        reading = cc.name(profile, _TABLE)
        assert reading["answer"] not in reading["absences"]


def test_inside_its_own_radius_a_type_is_never_declared_absent():
    radii = cc.certified_radii(_TABLE)
    for profile in _grid():
        reading = cc.name(profile, _TABLE, radii)
        for label, distance in reading["distances"]:
            if distance <= radii[label]:
                assert label not in reading["absences"]


def test_a_tie_for_nearest_is_refused():
    middle = _profile(k1_2="1/2", k2_2="1/2")
    table = (("A", _profile(k1_2=1)), ("B", _profile(k2_2=1)))
    reading = cc.name(middle, table)
    assert reading["nearest"] is None and reading["answer"] is None


# ---------------------------------------------------------------------------
#  2.  The uniform floor over all 23 types
# ---------------------------------------------------------------------------

def _uniform(label):
    keys = cr.expected_keys(label)
    total = sum(keys.values())
    return tuple(sorted((k, Fraction(v, total)) for k, v in keys.items()))


def test_the_uniform_profiles_of_the_23_types_are_four_ninths_apart():
    labels = cr.NIEMEIER_TYPES
    assert len(labels) == 23
    profiles = [_uniform(label) for label in labels]
    distances = [cr.configuration_distance(profiles[i], profiles[j])
                 for i in range(23) for j in range(i + 1, 23)]
    assert len(distances) == 253
    assert min(distances) == Fraction(4, 9)


# ---------------------------------------------------------------------------
#  3.  The stored figures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def report():
    rep = ltc.lattice_completion_report()["classifier"]
    assert rep["available"], (
        "the query profiles are absent or stale; re-take them with "
        "python3 -m glm_universal.tools configuration-classifier --write")
    return rep


def test_the_queries_are_read_at_the_escalation_rounds_cell():
    assert cq.STARTS == 1920
    assert cc.EXPECTED_JOINT == (40, 44)


def test_the_stopping_rule_reproduces_the_joint_reading(report):
    ten = report["ten"]
    assert (ten["joint_correct"], ten["queries"]) == cc.EXPECTED_JOINT
    assert report["marks"]["B1"] is True


def test_the_verdicts_partition_the_queries(report):
    for table in (report["ten"], report["twenty_three"]):
        if table is None:
            continue
        assert (table["correct"] + table["wrong"] + table["refused"]
                == table["queries"])
        assert table["answered"] == table["correct"] + table["wrong"]


def test_every_stored_answer_is_inside_its_certified_radius(report):
    for row in report["ten"]["rows"]:
        if row["answer"] is not None:
            assert row["nearest"] == row["answer"]


def test_a_query_inside_its_own_radius_draws_no_false_absence(report):
    for row in report["ten"]["rows"]:
        if row["within_own_radius"]:
            assert row["false_absence"] is False


def test_more_references_answer_nothing_wrongly(report):
    wide = report["twenty_three"]
    assert wide is not None and wide["references"] == 23
    assert wide["wrong"] == 0
    assert report["marks"]["B6"] is True


def test_the_classifier_is_exact():
    assert ex.module_float_sites(Path(cc.__file__)) == {}
    assert ex.module_float_sites(Path(ltc.__file__)) == {}


def test_against_the_ten_every_query_is_answered_and_none_wrongly(report):
    ten = report["ten"]
    assert (ten["correct"], ten["wrong"], ten["refused"]) == (44, 0, 0)
    assert ten["nearest_correct"] == 44
    assert report["marks"]["B2"] is True and report["marks"]["B3"] is True


def test_every_query_reads_inside_its_own_types_certified_radius(report):
    ten = report["ten"]
    assert ten["within_radius"] == ten["queries"] == 44
    assert ten["false_absences"] == 0
    assert ten["absences"] == ten["absence_slots"] == 44 * 9
    assert report["marks"]["B4"] is True
