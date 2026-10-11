"""Tests for ``reasoning/configuration_reading`` -- the configuration reading
``L5`` for the 28-vertex pair of lattice item 6 (Phase 122).

``RequestProject/GLM/ConfigurationReading.lean`` proves that pushing shares
forward along a key map never increases an L1 distance (so the reading's seed
shift is at most the vertex-matched shift), that the uniform-limit profiles of
``E_6^4`` and ``D_6^4`` are ``4/7`` apart (``E_8^3`` / ``D_8^3``: ``4/9``),
and a separation floor.  These tests pin

* the **pure pieces** on hand-built points: the multiplicity graph, the keys,
  the affine diagrams of each label, and the uniform-limit distances the Lean
  file states;
* the **stored ensembles**: the control (every arrival set is the declared
  vertex set and forms the label's affine diagram), the bound at every
  instance, and the marks as measured
  (``studies/CONFIGURATION_READING_STUDY.md`` §7);
* the **Lean file** exists, carries the named theorems, and has no ``sorry``.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import configuration_reading as cr
from glm_universal.reasoning import deep_hole_escalation as de
from glm_universal.reasoning import share_ensemble as se
from glm_universal.reasoning import share_separation as ss


@pytest.fixture(scope="module")
def report():
    data = se.current()
    assert data is not None, (
        "the share ensembles are absent or stale; re-take them with "
        "python3 -m glm_universal.tools share-ensemble --write")
    out = cr.configuration_report()
    assert out["available"] is True
    return out


def test_multiplicity_graph_reads_single_and_double_edges():
    # r^2 = 1: squared distance 3 is one edge, 4 is two, 2 is none.
    points = [(0, 0, 0, 0), (1, 1, 1, 0), (0, 0, 0, 2), (1, 1, 0, 0)]
    edges = cr.multiplicity_graph(points, Fraction(1))
    assert edges == {(0, 1): 1, (0, 2): 2}


def test_keys_are_component_size_and_degree():
    # A path of three points at squared spacing 3, plus an isolated point.
    points = [(0, 0, 0, 0, 0, 0, 0, 0, 0), (1, 1, 1, 0, 0, 0, 0, 0, 0),
              (1, 1, 1, 1, 1, 1, 0, 0, 0), (9, 9, 9, 9, 9, 9, 9, 9, 9)]
    assert cr.vertex_keys(points, Fraction(1)) == ((3, 1), (3, 2), (3, 1),
                                                   (1, 0))


def test_affine_diagrams_of_the_labels():
    assert cr.expected_keys("E_6^4") == Counter({(7, 1): 12, (7, 2): 12,
                                                 (7, 3): 4})
    assert cr.expected_keys("D_6^4") == Counter({(7, 1): 16, (7, 2): 4,
                                                 (7, 3): 8})
    assert cr.expected_keys("A_1^24") == Counter({(2, 2): 48})
    for entry in de.reference_entries()[0]:
        assert sum(cr.expected_keys(str(entry["type"])).values()) == \
            int(entry["vertex_count"])


def test_uniform_limit_distances_match_the_lean_file():
    assert cr.uniform_distance("E_6^4", "D_6^4") == Fraction(4, 7)
    assert cr.uniform_distance("E_8^3", "D_8^3") == Fraction(4, 9)
    assert cr.uniform_distance("A_2^12", "A_12^2") == 2


def test_every_niemeier_pair_is_apart_in_the_uniform_limit():
    out = cr.niemeier_uniform_floor()
    assert out["pairs"] == 253
    assert out["floor"] == Fraction(4, 9)
    assert [(a, b) for _d, a, b in out["closest"]] == \
        [("E_8^3", "D_8^3"), ("D_24", "A_24"), ("E_6^4", "D_6^4")]
    assert out["closest"][1][0] == Fraction(12, 25)
    for label in cr.NIEMEIER_TYPES:
        powers = sum(int(part.split("^")[1]) if "^" in part else 1
                     for part in label.split())
        # rank 24 plus one extra node per component
        assert sum(cr.expected_keys(label).values()) == 24 + powers


def test_profile_from_a_record_and_from_a_multiset_agree():
    record = (((0, 0, 0, 0), Fraction(1)), ((1, 1, 1, 0), Fraction(1)),
              ((0, 0, 0, 0), Fraction(1)), ((5, 5, 5, 5), Fraction(4)))
    triples = (((0, 0, 0, 0), Fraction(1), 2), ((1, 1, 1, 0), Fraction(1), 1),
               ((5, 5, 5, 5), Fraction(4), 1))
    assert cr.configuration_profile(record) == cr.configuration_profile(triples)
    assert cr.configuration_profile(record) == (((2, 1), Fraction(1)),)


def test_matched_shift_agrees_with_phase_121():
    data = se.current()
    assert data is not None
    hole = data["holes"][-1]
    for starts in (240, 1920):
        assert cr.matched_share_shift(
            se.multiset(hole["reference"], starts),
            se.multiset(hole["sanity"], starts)) == ss.matched_share_shift(
                ss.expand(hole["reference"], starts),
                ss.expand(hole["sanity"], starts))


def test_the_control_reads_every_declared_diagram(report):
    assert report["marks"]["K2"] is True
    assert report["control_holds"] == len(report["control"]) == 20


def test_the_bound_holds_at_every_instance(report):
    assert report["marks"]["K3"] is True
    assert report["bound_holds"] == report["bound_instances"] == 80


def test_the_marks_as_measured(report):
    assert report["marks"] == {"K1": True, "K2": True, "K3": True,
                               "K4": True, "K5": True, "K6": True}
    assert report["statistics_tried"] == 44
    cells = {c["starts"]: c for c in report["cells"]}
    top = cells[30720]
    assert top["q0"] == 10 and top["locally_certified"] == 10
    assert top["closest_pair"] == ("E_8^3", "D_8^3")
    assert de.rounded(top["ratio"], 4) == "0.1261"
    assert de.rounded(top["separation"], 4) == "0.4351"
    assert top["pair_certified"] is True
    assert de.rounded(top["pair_distance"], 4) == "0.5768"
    # Below 1920 starts: one cell above the criterion, as measured.
    assert [cells[n]["ratio_below_one"] for n in (240, 480, 960)] == \
        [True, False, True]
    assert report["uniform_closest"] == {"pair": ("E_8^3", "D_8^3"),
                                         "distance": Fraction(4, 9)}


def test_lean_file_carries_the_theorems():
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    text = (root / cr.LEAN_MODULE).read_text(encoding="utf-8")
    for name in ("push_shift_le", "config_shift_le_matched",
                 "e6_degree_counts", "d6_degree_counts",
                 "e6_d6_uniform_distance", "e8_d8_uniform_distance",
                 "separation_floor", "e6_d6_separation_floor",
                 "e6_d6_separated", "diagrams_are_trees"):
        assert f"theorem {name}" in text
    assert "sorry" not in text
