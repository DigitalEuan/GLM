"""Tests for ``reasoning/hole_census`` and part A of
``reasoning/lattice_completion`` -- a reference centre for every one of the
23 Niemeier types, and the configuration reading over all of them
(Phase 123, part A).

``studies/LATTICE_COMPLETION_STUDY.md`` §2.A declares three stages, each used
only for what the stages before it left unreached.  These tests pin:

* the **declared stages** -- the walk seeds continue the first round's, the
  budget and chunk are constants, the cycle construction applies exactly to
  the labels with an ``A_n`` component, the pilot's seeds are the disclosed
  range;
* the **cycle construction's geometry** -- a constructed configuration has the
  ``A~_n`` Gram matrix it is meant to have;
* the **sizes** are nested prefixes of one run, the same ladder the share
  ensemble uses up to 7680;
* the stored **census and its control**, read from the cache, which must
  describe the sources it was taken from (D4): every entry is certified by
  the frozen path as its own type, and every stored reading is exact.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import configuration_reading as cr
from glm_universal.reasoning import deep_hole_classifier as dhc
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import hole_census as hc
from glm_universal.reasoning import lattice_completion as ltc
from glm_universal.reasoning.fwht_decode import _Sweep


# ---------------------------------------------------------------------------
#  1.  The declared stages
# ---------------------------------------------------------------------------

def test_the_walk_continues_the_first_rounds_seeds():
    assert hc.FIRST_NEW_INDEX == len(dhc.WALK_SEEDS) == 12
    for i, seed in enumerate(dhc.WALK_SEEDS):
        assert hc.walk_seed(i) == seed
    assert hc.WALK_BUDGET == 2048 and hc.CHUNK == 256
    assert hc.WALK_BUDGET % hc.CHUNK == 0


def test_the_cycle_construction_applies_to_the_labels_with_an_a_component():
    with_a = [l for l in cr.NIEMEIER_TYPES if hc.a_component(l) is not None]
    assert hc.a_component("A_8^3") == 8
    assert hc.a_component("A_11 D_7 E_6") == 11
    assert hc.a_component("D_4^6") is None
    assert hc.a_component("E_8^3") is None
    # the A_n rank determines the type: no two labels share it
    ranks = [hc.a_component(l) for l in with_a]
    assert len(ranks) == len(set(ranks))


def test_the_pilot_seeds_are_the_disclosed_range():
    assert hc.PILOT_SEEDS[0] == 1000 and hc.PILOT_SEEDS[-1] == 2995
    assert len(hc.PILOT_SEEDS) == 1996


def test_the_sizes_are_a_doubling_ladder_to_7680():
    assert hc.SIZES == (240, 480, 960, 1920, 3840, 7680)
    assert hc.TOP == 7680
    assert all(b == 2 * a for a, b in zip(hc.SIZES, hc.SIZES[1:]))


def test_a_constructed_cycle_has_the_affine_a_gram_matrix():
    n = 8
    sweep = _Sweep(hc.CYCLE_SEED + n)
    points = None
    for _ in range(hc.CYCLE_ATTEMPTS):
        points = hc.cycle_attempt(n, sweep)
        if points is not None:
            break
    assert points is not None and len(points) == n + 1
    for i in range(n + 1):
        for j in range(i + 1, n + 1):
            d = sum((a - b) ** 2 for a, b in zip(points[i], points[j]))
            adjacent = (j - i) in (1, n)
            assert d == (48 if adjacent else 32), (i, j, d)


# ---------------------------------------------------------------------------
#  2.  The stored census
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def report():
    rep = ltc.hole_census_report()
    assert rep["available"], (
        "the hole census is absent or stale; re-take it with python3 -m "
        "glm_universal.tools hole-census --write")
    return rep


def test_every_census_entry_is_certified_as_its_own_type(report):
    # A centre the second certifying reading could not finish is kept in
    # the census with no type (Phase 123: three of them, §7.2 of the study).
    for entry in report["entries"]:
        assert entry["stage"] in ("walk", "cycle", "pilot")
        if entry["certified"]:
            assert entry["type"] in cr.NIEMEIER_TYPES
        else:
            assert entry["type"] is None
    certified = [e for e in report["entries"] if e["certified"]]
    labels = [e["type"] for e in certified]
    assert len(labels) == len(set(labels))


def test_the_census_counts_add_up(report):
    assert report["catalogue"] == 23
    uncertified = sum(1 for e in report["entries"] if not e["certified"])
    assert (report["types_reached"] + len(report["unreached"]) + uncertified
            == report["catalogue"])
    assert sum(report["by_stage"].values()) + 10 == report["types_reached"]


def test_the_walk_stage_ran_within_its_budget(report):
    assert report["walks_run"] <= hc.WALK_BUDGET
    assert report["pilot_walks_run"] <= len(hc.PILOT_SEEDS)


def test_the_cells_are_read_at_every_declared_size(report):
    assert [c["starts"] for c in report["cells"]] == list(hc.SIZES)
    for c in report["cells"]:
        assert c["gate"] == report["types_reached"]
        assert 0 <= c["q0"] <= c["gate"]
        if c["ratio"] is not None:
            assert isinstance(c["ratio"], Fraction)


def test_the_closest_pair_realises_the_separation(report):
    for c in report["cells"]:
        if c["separation"] is not None:
            assert c["separation"] > 0
            assert len(c["closest_pair"]) == 2


def test_the_census_modules_are_exact():
    assert ex.module_float_sites(Path(hc.__file__)) == {}
    assert ex.module_float_sites(Path(ltc.__file__)) == {}


def test_the_post_hoc_follow_up_certifies_the_three_and_reads_all_23(report):
    post_hoc = report["post_hoc"]
    if not post_hoc["available"]:
        pytest.skip(post_hoc["reason"])
    assert post_hoc["types_reached"] == 23
    assert sorted(e["type"] for e in post_hoc["entries"]) == [
        "A_17 E_7", "A_5^4 D_4", "D_4^6"]
    assert post_hoc["control_holds"] == len(post_hoc["control"]) == 26
    top = post_hoc["cells"][-1]
    assert top["q0"] == top["gate"] == top["locally_certified"] == 23
    assert top["ratio"] < 1
