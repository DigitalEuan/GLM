"""``glm_universal.reasoning.share_separation`` -- the separation criterion
for the share-carrying rungs of the deep-hole ladder (Phase 121, lattice
item 6).

The question
------------
``studies/STRAY_BLIND_STUDY.md`` closed lattice item 6 for the distance-only
rung ``L3`` and left it open for the two rungs whose profile carries the
**arrival shares**: ``L2`` (the shares widened by the stray spectrum) and
``L4`` (``L2`` and ``L3`` together).  At the ladder's best cell,
``(L4, 1920)``, the ratio was ``rho = 2W/B = 2.5943``; the criterion
``GLM.DeepHoleLadder.nearest_correct`` needs ``rho < 1``.
``studies/SHARE_SEPARATION_STUDY.md`` pre-registered six marks and extended
the ensemble to 30720 starts.

What this module does
---------------------
It reads the stored sufficient statistics of
:mod:`glm_universal.reasoning.share_ensemble` -- every emitted point with its
exact squared distance and count, at every prefix size -- and applies the
ladder's own readings and metrics to them (:func:`deep_hole_escalation.layer_profile`
and :func:`deep_hole_escalation.layer_distance`, unchanged).  Per cell it
reports the sanity count ``Q0``, the worst seed shift ``W``, the separation
``B`` and ``rho``, as the ladder does; per hole it adds the **per-hole
ratio** ``rho_T = 2 W_T / B_T`` (``W_T`` the hole's own shift, ``B_T`` the
distance from its reference to the nearest other), which certifies the hole
when below one (``GLM.ShareSeparation.nearest_correct_local``).

Beside the readings it checks the bound proved in
``RequestProject/GLM/ShareSeparation.lean``: for the same centre under the
two seeds, the sorted share shift is at most the **vertex-matched** shift
(``share_shift_le_matched``), and likewise for the stray spectrum matched by
distance value.

Exactness
---------
Integers and :class:`~fractions.Fraction` only.  Nothing here decodes a
lattice point; the expensive half is the stored ensemble.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from . import deep_hole_escalation as de
from . import share_ensemble as se

__all__ = [
    "LAYERS", "SHARE_LAYERS", "LEAN_MODULE", "STATISTICS_TRIED",
    "PREDICTED_RATIO", "expand", "matched_share_shift", "matched_stray_shift",
    "cell", "bound_rows", "share_separation_report",
]

#: The Lean file that proves the bound and the per-hole criterion.
LEAN_MODULE: str = "RequestProject/GLM/ShareSeparation.lean"

#: Every reading of the ladder, in its declared order.
LAYERS: Tuple[str, ...] = tuple(de.LAYER_KEYS)

#: The two rungs whose profile carries the arrival shares.
SHARE_LAYERS: Tuple[str, ...] = ("widened", "joint")

#: The ladder's 20 statistics plus the 16 cells of this round's extension.
STATISTICS_TRIED: int = de.STATISTICS_TRIED + len(se.EXTENSION_SIZES) * len(LAYERS)

#: The pre-registered prediction at ``L4``: ``rho`` falling by ``1/sqrt 2``
#: per doubling from 2.5943 at 1920 starts (``SHARE_SEPARATION_STUDY.md`` §3),
#: stated to two places as it was declared.
PREDICTED_RATIO: Dict[int, str] = {15360: "0.92", 30720: "0.65"}


# ═════════════════════════════════════════════════════════════════════════
# 1.  FROM THE STORED STATISTICS BACK TO A RECORD
# ═════════════════════════════════════════════════════════════════════════

def expand(summary: Dict[str, object], starts: int
           ) -> Tuple[Tuple[Tuple[int, ...], Fraction], ...]:
    """An emission record with the stored multiset of the first ``starts``
    starts.  Every reading of the ladder is a function of the multiset, so
    the order the pairs come back in does not matter."""
    out: List[Tuple[Tuple[int, ...], Fraction]] = []
    for point, distance, count in se.multiset(summary, starts):
        out.extend([(point, distance)] * count)
    return tuple(out)


def _arrival_shares(record: Sequence[Tuple[Tuple[int, ...], Fraction]]
                    ) -> Dict[Tuple[int, ...], Fraction]:
    if not record:
        return {}
    best = min(distance for _point, distance in record)
    counts: Dict[Tuple[int, ...], int] = {}
    for point, distance in record:
        if distance == best:
            counts[point] = counts.get(point, 0) + 1
    total = sum(counts.values())
    return {point: Fraction(count, total) for point, count in counts.items()}


def _stray_shares(record: Sequence[Tuple[Tuple[int, ...], Fraction]]
                  ) -> Dict[Fraction, Fraction]:
    if not record:
        return {}
    best = min(distance for _point, distance in record)
    counts: Dict[Fraction, int] = {}
    for _point, distance in record:
        if distance != best:
            counts[distance] = counts.get(distance, 0) + 1
    return {value: Fraction(count, len(record))
            for value, count in counts.items()}


def _matched(left: Dict[object, Fraction], right: Dict[object, Fraction]
             ) -> Fraction:
    keys = set(left) | set(right)
    return sum((abs(left.get(key, Fraction(0)) - right.get(key, Fraction(0)))
                for key in keys), Fraction(0))


def matched_share_shift(left: Sequence[Tuple[Tuple[int, ...], Fraction]],
                        right: Sequence[Tuple[Tuple[int, ...], Fraction]]
                        ) -> Fraction:
    """The vertex-matched shift: the L1 distance between two records' arrival
    shares compared vertex by vertex.  Meaningful for one centre under two
    seeds, where the vertices are the same lattice points."""
    return _matched(_arrival_shares(left), _arrival_shares(right))


def matched_stray_shift(left: Sequence[Tuple[Tuple[int, ...], Fraction]],
                        right: Sequence[Tuple[Tuple[int, ...], Fraction]]
                        ) -> Fraction:
    """The stray spectra compared distance value by distance value."""
    return _matched(_stray_shares(left), _stray_shares(right))


# ═════════════════════════════════════════════════════════════════════════
# 2.  ONE CELL, AT ANY SIZE THE ENSEMBLE WAS STORED AT
# ═════════════════════════════════════════════════════════════════════════

def _records(data: Dict[str, object], starts: int
             ) -> Tuple[Tuple[str, Tuple, Tuple], ...]:
    rows = []
    for hole in data["holes"]:
        rows.append((str(hole["label"]), expand(hole["reference"], starts),
                     expand(hole["sanity"], starts)))
    return tuple(rows)


def cell(data: Dict[str, object], layer: str, starts: int) -> Dict[str, object]:
    """The ladder's cell statistics at ``(layer, starts)``, from the stored
    ensembles, with the per-hole ratio beside each row."""
    table = _records(data, starts)
    references = [(label, de.layer_profile(ref, layer))
                  for label, ref, _san in table]
    sanity = [(label, de.layer_profile(san, layer))
              for label, _ref, san in table]
    passes = 0
    worst: Optional[Fraction] = None
    rows: List[Dict[str, object]] = []
    for index, (label, profile) in enumerate(sanity):
        distances = [(name, de.layer_distance(profile, reference, layer))
                     for name, reference in references]
        own = distances[index][1]
        best = min(distance for _name, distance in distances)
        winners = [name for name, distance in distances if distance == best]
        correct = len(winners) == 1 and winners[0] == label
        passes += int(correct)
        worst = own if worst is None else max(worst, own)
        nearest_other = min(
            de.layer_distance(references[index][1], other, layer)
            for name, other in references if name != label)
        local = (None if nearest_other == 0
                 else Fraction(2) * own / nearest_other)
        rows.append({"label": label, "own_distance": own,
                     "nearest_other_reference": nearest_other,
                     "local_ratio": local,
                     "locally_certified": local is not None and local < 1,
                     "correct": correct})
    separation: Optional[Fraction] = None
    closest: Optional[Tuple[str, str]] = None
    for i in range(len(references)):
        for j in range(i + 1, len(references)):
            distance = de.layer_distance(references[i][1], references[j][1],
                                         layer)
            if separation is None or distance < separation:
                separation = distance
                closest = (references[i][0], references[j][0])
    ratio = (None if separation is None or separation == 0 or worst is None
             else Fraction(2) * worst / separation)
    return {
        "layer": layer, "layer_name": de.LAYER_NAMES[layer], "starts": starts,
        "rung": ("declared" if starts in de.DECLARED_STARTS else
                 "extension" if starts in de.EXTENSION_STARTS else
                 "phase 121 extension"),
        "q0": passes, "gate": len(table), "spread": worst,
        "separation": separation, "closest_pair": closest, "ratio": ratio,
        "ratio_below_one": ratio is not None and ratio < 1,
        "locally_certified": sum(1 for row in rows if row["locally_certified"]),
        "rows": tuple(rows),
    }


def bound_rows(data: Dict[str, object]) -> Tuple[Dict[str, object], ...]:
    """The bound of ``share_shift_le_matched`` at every hole and size: the
    sorted shift (what the ladder measures) against the matched one."""
    out = []
    for starts in data["sizes"]:
        for label, ref, san in _records(data, int(starts)):
            sorted_share = de.l1(de.share_profile(ref), de.share_profile(san))
            sorted_stray = de.l1(de.stray_profile(ref), de.stray_profile(san))
            share = matched_share_shift(ref, san)
            stray = matched_stray_shift(ref, san)
            out.append({"starts": int(starts), "label": label,
                        "sorted_share": sorted_share, "matched_share": share,
                        "sorted_stray": sorted_stray, "matched_stray": stray,
                        "holds": sorted_share <= share
                        and sorted_stray <= stray})
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE REPORT AND ITS MARKS
# ═════════════════════════════════════════════════════════════════════════

def _stored_ladder() -> Dict[Tuple[str, int], Dict[str, object]]:
    stored = de.current()
    if stored is None:
        return {}
    return {(str(c["layer"]), int(c["starts"])): c for c in stored["cells"]}


@lru_cache(maxsize=1)
def share_separation_report() -> Dict[str, object]:
    """Every cell at every stored size, the bound, and the six marks."""
    data = se.current()
    if data is None:
        return {"available": False, "lean": LEAN_MODULE,
                "reason": "the share ensembles are absent or stale; re-take "
                          "them with python3 -m glm_universal.tools "
                          "share-ensemble --write"}
    sizes = tuple(int(n) for n in data["sizes"])
    cells = tuple(cell(data, layer, n) for layer in LAYERS for n in sizes)
    by_key = {(c["layer"], c["starts"]): c for c in cells}

    ladder = _stored_ladder()
    reproduced = []
    for (layer, n), stored in sorted(ladder.items()):
        mine = by_key.get((layer, n))
        reproduced.append(mine is not None and all(
            mine[key] == stored[key]
            for key in ("q0", "spread", "separation", "ratio")))
    h2 = bool(ladder) and len(reproduced) == len(de.CELLS) and all(reproduced)

    bounds = bound_rows(data)
    h3 = bool(bounds) and all(row["holds"] for row in bounds)

    share_cells = [c for c in cells if c["layer"] in SHARE_LAYERS]
    below = [c for c in share_cells if c["ratio_below_one"]]
    h4 = bool(below)
    best = min((c for c in share_cells if c["ratio"] is not None),
               key=lambda c: (c["ratio"], c["starts"]))
    first = (min(below, key=lambda c: (SHARE_LAYERS.index(c["layer"]),
                                       c["starts"])) if below else None)

    climb = [n for n in sizes if n >= 1920]
    joint = [by_key[("joint", n)] for n in climb]
    h5 = all(joint[i + 1]["spread"] < joint[i]["spread"]
             for i in range(len(joint) - 1))
    h6 = all(c["q0"] == c["gate"] for c in joint)

    # Post hoc, reported and never a mark: the per-hole certificate at its
    # best share-carrying cell, and whether the closest pair of references
    # shares a vertex count wherever the extension was read.
    counts = {str(entry["type"]): int(entry["vertex_count"])
              for entry in de.reference_entries()[0]}
    local_best = max(share_cells, key=lambda c: (c["locally_certified"],
                                                 -SHARE_LAYERS.index(c["layer"]),
                                                 -c["starts"]))
    extension_share = [c for c in share_cells
                       if c["starts"] in se.EXTENSION_SIZES]
    equal_count = [c for c in extension_share if c["closest_pair"]
                   and counts[c["closest_pair"][0]]
                   == counts[c["closest_pair"][1]]]

    marks = {
        "H1": True,   # the Lean file; checked by the build, pinned by the tests
        "H2": h2, "H3": h3, "H4": h4, "H5": h5, "H6": h6,
    }
    return {
        "available": True, "lean": LEAN_MODULE, "sizes": sizes,
        "extension": tuple(int(n) for n in data["extension"]),
        "cells": cells, "bounds": bounds,
        "bound_instances": len(bounds),
        "bound_holds": sum(1 for row in bounds if row["holds"]),
        "reproduced_cells": sum(1 for ok in reproduced if ok),
        "ladder_cells": len(de.CELLS),
        "best_share_cell": {"layer": best["layer"], "starts": best["starts"],
                            "ratio": best["ratio"], "q0": best["q0"]},
        "first_below_one": (None if first is None else
                            {"layer": first["layer"],
                             "starts": first["starts"],
                             "ratio": first["ratio"]}),
        "per_hole_best": {
            "layer": local_best["layer"], "starts": local_best["starts"],
            "certified": local_best["locally_certified"],
            "uncertified": tuple(row["label"] for row in local_best["rows"]
                                 if not row["locally_certified"])},
        "vertex_counts": counts,
        "extension_share_cells": len(extension_share),
        "closest_pair_equal_count": len(equal_count),
        "predicted_ratio": PREDICTED_RATIO,
        "statistics_tried": STATISTICS_TRIED,
        "marks": marks,
        "marks_met": sum(1 for value in marks.values() if value),
    }
