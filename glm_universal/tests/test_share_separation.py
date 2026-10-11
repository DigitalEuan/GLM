"""Tests for ``reasoning/share_ensemble`` and ``reasoning/share_separation``
-- lattice item 6 for the share-carrying rungs (Phase 121).

``RequestProject/GLM/ShareSeparation.lean`` proves that sorting never
increases an L1 distance, so the share part's seed shift is at most the
vertex-matched shift, and that a hole is named correctly whenever its own
shift is under half its distance to the nearest other reference.  These tests
pin

* the **pure pieces** on hand-built records: the stored multiset round trip,
  the prefix property of the summaries, the bound on sorted against matched
  shifts, and the per-hole ratio;
* the **stored ensembles**, extended to 30720 starts: the ladder's sixteen
  cells reproduced exactly, the bound at every instance, and the marks as
  measured (``studies/SHARE_SEPARATION_STUDY.md`` §7);
* the **Lean file** exists, carries the named theorems, and has no ``sorry``.

The ensembles are 614,400 exact decodes, so they are read from their cache,
and the fixture fails if the cache no longer describes its sources (D4).
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import deep_hole_escalation as de
from glm_universal.reasoning import share_ensemble as se
from glm_universal.reasoning import share_separation as ss

R = Fraction(16)


@pytest.fixture(scope="module")
def report():
    data = se.current()
    assert data is not None, (
        "the share ensembles are absent or stale; re-take them with "
        "python3 -m glm_universal.tools share-ensemble --write")
    out = ss.share_separation_report()
    assert out["available"] is True
    return out


def _record(*pairs):
    return tuple(((point,), Fraction(distance)) for point, distance in pairs)


def test_summary_round_trip_keeps_the_multiset():
    record = _record((1, 16), (2, 16), (1, 16), (3, 18), (2, 16))
    summary = se.summarise(record, (2, 5))
    assert summary["counts"]["2"] == (1, 1)
    assert summary["counts"]["5"] == (2, 2, 1)
    back = ss.expand(summary, 5)
    assert sorted(back) == sorted(record)
    assert sorted(ss.expand(summary, 2)) == sorted(record[:2])


def test_sizes_are_nested_and_extend_the_ladder():
    assert se.SIZES[:len(de.STARTS_LADDER)] == tuple(de.STARTS_LADDER)
    assert se.SIZES[-1] == se.TOP == 30720
    assert all(se.SIZES[i] < se.SIZES[i + 1] for i in range(len(se.SIZES) - 1))


def test_sorted_shift_never_exceeds_the_matched_shift():
    # Same shares on different vertices: sorted distance 0, matched 2.
    left = _record((1, 16), (1, 16), (2, 16))
    right = _record((2, 16), (2, 16), (1, 16))
    sorted_shift = de.l1(de.share_profile(left), de.share_profile(right))
    assert sorted_shift == 0
    assert ss.matched_share_shift(left, right) == Fraction(2, 3)
    # The stray spectrum, matched by distance value.
    a = _record((1, 16), (5, 18), (6, 20))
    b = _record((1, 16), (5, 20), (7, 20))
    assert de.l1(de.stray_profile(a), de.stray_profile(b)) <= \
        ss.matched_stray_shift(a, b)


def test_per_hole_ratio_certifies_on_its_own_evidence():
    holes = []
    for label, ref, san in (("p", ((1, 16),) * 4, ((1, 16),) * 4),
                            ("q", ((2, 16), (3, 16)) * 2,
                             ((2, 16), (3, 16), (2, 16), (2, 16)))):
        holes.append({"label": label,
                      "reference": se.summarise(_record(*ref), (4,)),
                      "sanity": se.summarise(_record(*san), (4,))})
    data = {"sizes": (4,), "extension": (), "holes": tuple(holes)}
    cell = ss.cell(data, "shares", 4)
    rows = {row["label"]: row for row in cell["rows"]}
    assert rows["p"]["own_distance"] == 0
    assert rows["p"]["local_ratio"] == 0 and rows["p"]["locally_certified"]
    assert rows["q"]["own_distance"] == Fraction(1, 2)
    assert rows["q"]["nearest_other_reference"] == 1
    assert rows["q"]["local_ratio"] == 1
    assert not rows["q"]["locally_certified"]
    assert cell["ratio"] == 1 and not cell["ratio_below_one"]


def test_the_ladder_is_reproduced_exactly(report):
    assert report["marks"]["H2"] is True
    assert report["reproduced_cells"] == report["ladder_cells"] == 16


def test_the_bound_holds_at_every_instance(report):
    assert report["marks"]["H3"] is True
    assert report["bound_holds"] == report["bound_instances"] == 80


def test_every_cell_is_reported_at_every_size(report):
    assert len(report["cells"]) == len(ss.LAYERS) * len(se.SIZES)
    assert report["statistics_tried"] == 36


def test_the_marks_as_measured(report):
    # H4, H5 and H6 were missed; a measurement that misses is a result, and
    # these pin what it is (SHARE_SEPARATION_STUDY.md section 7).
    assert report["marks"] == {"H1": True, "H2": True, "H3": True,
                               "H4": False, "H5": False, "H6": False}
    assert report["first_below_one"] is None
    best = report["best_share_cell"]
    assert (best["layer"], best["starts"], best["q0"]) == ("joint", 7680, 9)
    assert de.rounded(best["ratio"], 4) == "2.3508"
    joint = {c["starts"]: c for c in report["cells"] if c["layer"] == "joint"}
    assert [joint[n]["q0"] for n in (1920, 3840, 7680, 15360, 30720)] == \
        [10, 9, 9, 9, 10]
    assert de.rounded(joint[30720]["ratio"], 4) == "2.4231"


def test_the_per_hole_certificate_leaves_one_equal_count_pair(report):
    best = report["per_hole_best"]
    assert (best["layer"], best["starts"], best["certified"]) == \
        ("joint", 15360, 8)
    assert best["uncertified"] == ("E_6^4", "D_6^4")
    counts = report["vertex_counts"]
    assert counts["E_6^4"] == counts["D_6^4"] == 28
    assert report["closest_pair_equal_count"] == \
        report["extension_share_cells"] == 8


def test_lean_file_carries_the_theorems():
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    text = (root / ss.LEAN_MODULE).read_text(encoding="utf-8")
    for name in ("four_point", "l1_le_perm", "l1_le_perm_of_monotone",
                 "l1_rearranged_le", "l1_sort_le", "share_shift_le_matched",
                 "l1_rearranged_self", "nearest_correct_local",
                 "resolves_local", "local_can_certify_when_global_fails"):
        assert f"theorem {name}" in text
    assert "sorry" not in text
