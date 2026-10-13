"""``glm_universal.reasoning.placement_guard`` -- the placement guard
(Phase 129; the follow-up the cell guard left).

``studies/PLACEMENT_GUARD_STUDY.md`` pre-registered the rule, a fourth query
set and nine marks.  This module takes them.

The rule
--------
The cell guard (:mod:`cell_guard`, Phase 128) answers the single carrier
``i`` of a cell ``p`` only when ``|q - c_i| + |q - p|`` is below the packing
radius.  The proof needed the packing radius only as a lower bound on how far
every *other* carrier is from ``p``.  The placement guard stores that distance
itself, once per cell,

    ``rho_p^2 = min over k != i of |c_k - p|^2``,

and answers when ``|q - c_i| + |q - p| < rho_p``.
``RequestProject/GLM/PlacementGuard.lean`` proves that the answer is then the
strictly nearest carrier with no hypothesis on the quantiser
(``placed_strict_nearest``), that ``rho_p`` is at least the packing radius for
a nearest-point quantiser (``placement_radius_ge``), so every cell-guard
answer is a placement-guard answer (``cellGuard_imp_placed``), and that the
guarded ladder is order-independent (``placed_firstNamed_agree``).  The test
is decided exactly by ``GLM.CellGuard.sqrt_add_lt_sqrt_iff``.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout.  No float, no
randomness.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import construction_ladder as CL
from . import cell_guard as CG
from . import ladder_escalation as LE
from . import norm256_hex as NH

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "LADDER", "FOURTH", "FOURTH_OFFSET",
    "fourth_queries", "query_sets", "exact_lt", "radii", "read_set",
    "placement_guard_report", "DATA_PATH", "module_digest", "measure",
    "write_measurements", "measurements", "state", "current",
]

LEAN_FILE = "RequestProject/GLM/PlacementGuard.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "placed_strict_nearest", "placement_radius_ge", "cellGuard_imp_placed",
    "placed_firstNamed_agree")

LADDER: Tuple[str, ...] = CG.LADDER

#: The fourth query set of section 4, codeword index ``i + FOURTH_OFFSET``.
FOURTH: Tuple[Tuple[str, int, Fraction], ...] = (
    ("24 coordinates by 1/4", 24, Fraction(1, 4)),
    ("12 coordinates by 1/2", 12, Fraction(1, 2)),
    ("10 coordinates by 3/4", 10, Fraction(3, 4)),
    ("2 coordinates by 2", 2, Fraction(2)),
)
FOURTH_OFFSET = 1024

Query = Tuple[int, Tuple[Fraction, ...]]
Point = Tuple[int, ...]


def fourth_queries(carriers) -> List[Query]:
    """The 568 queries of the fourth set, declared in section 4."""
    out: List[Query] = []
    for _label, support, magnitude in FOURTH:
        for i, (_r, _n, carrier) in enumerate(carriers):
            out.append((i, LE.perturb(carrier, i + FOURTH_OFFSET, support,
                                      magnitude)))
    return out


def query_sets(carriers) -> Dict[str, List[Query]]:
    """The four query sets, in the order they were declared."""
    sets = CG.query_sets(carriers)
    sets["fourth"] = fourth_queries(carriers)
    return sets


def exact_lt(a2: Fraction, b2: Fraction, r2: Fraction) -> bool:
    """``sqrt(a2) + sqrt(b2) < sqrt(r2)``, decided exactly."""
    slack = r2 - a2 - b2
    return slack > 0 and 4 * a2 * b2 < slack * slack


def radii(rung: str, carriers, index) -> Dict[Point, Fraction]:
    """``rho_p^2`` for every cell of the rung that holds exactly one
    carrier: the squared distance from the cell's centre to the nearest
    other carrier."""
    out: Dict[Point, Fraction] = {}
    for point, members in index.items():
        if len(members) != 1:
            continue
        i = members[0]
        out[point] = min(CG._nsq(carrier, point)
                         for k, (_r, _n, carrier) in enumerate(carriers)
                         if k != i)
    return out


def read_set(carriers, queries: Sequence[Query], indices, rads
             ) -> Dict[str, object]:
    """The unguarded, cell-guarded and placement-guarded ladder on one set."""
    ladder = LADDER
    orders = {"middle_out": CL.middle_out_order(ladder),
              "coarse_to_fine": ladder,
              "fine_to_coarse": tuple(reversed(ladder))}
    kinds = ("plain", "cell", "placed")
    totals = {kind: {name: {"correct": 0, "wrong": 0, "refused": 0}
                     for name in orders} for kind in kinds}
    per_rung = {rung: {"answered": 0, "cell": 0, "placed": 0,
                       "placed_wrong": 0} for rung in ladder}
    nearest = {"correct": 0, "wrong": 0, "tie": 0}
    p1_violations = n1_violations = 0
    wrong_placed: List[Dict[str, object]] = []
    for truth, query in queries:
        near = CG.nearest_carrier(query, carriers)
        nearest["tie" if near is None
                else "correct" if near == truth else "wrong"] += 1
        named = {kind: {} for kind in kinds}
        for rung in ladder:
            point = NH.quantise(query, rung)
            members = indices[rung].get(point, ())
            if len(members) != 1:
                for kind in kinds:
                    named[kind][rung] = None
                continue
            i = members[0]
            a2 = CG._nsq(query, carriers[i][2])
            b2 = CG._nsq(query, point)
            cell_ok = CG.guard_holds(a2, b2, NH.rung_norm(rung))
            placed_ok = exact_lt(a2, b2, rads[rung][point])
            named["plain"][rung] = i
            named["cell"][rung] = i if cell_ok else None
            named["placed"][rung] = i if placed_ok else None
            per_rung[rung]["answered"] += 1
            per_rung[rung]["cell"] += int(cell_ok)
            per_rung[rung]["placed"] += int(placed_ok)
            if cell_ok and not placed_ok:
                p1_violations += 1
            if placed_ok:
                if i != near:
                    n1_violations += 1
                if i != truth:
                    per_rung[rung]["placed_wrong"] += 1
        for kind in kinds:
            for name, order in orders.items():
                first = next((named[kind][r] for r in order
                              if named[kind][r] is not None), None)
                totals[kind][name][CG._verdict(first, truth)] += 1
                if kind == "placed" and name == "middle_out" and \
                        first is not None and first != truth:
                    wrong_placed.append({
                        "truth": carriers[truth][1],
                        "named": carriers[first][1],
                        "rung": next(r for r in order
                                     if named[kind][r] is not None),
                        "nearest_is_named": near == first})

    def _summary(by_order):
        correct = {t["correct"] for t in by_order.values()}
        wrong = {t["wrong"] for t in by_order.values()}
        return {"totals": by_order, "correct": max(correct),
                "wrong": max(wrong),
                "refused": max(t["refused"] for t in by_order.values()),
                "order_independent": len(correct) == 1 and len(wrong) == 1}

    out = {kind: _summary(totals[kind]) for kind in kinds}
    plain_correct = out["plain"]["totals"]["middle_out"]["correct"]
    kept = (Fraction(out["placed"]["totals"]["middle_out"]["correct"],
                     plain_correct) if plain_correct else Fraction(1))
    out.update({"queries": len(queries), "per_rung": per_rung,
                "nearest": nearest, "p1_violations": p1_violations,
                "n1_violations": n1_violations, "kept_share": kept,
                "placed_wrong_answers": wrong_placed})
    return out


def placement_guard_report(carriers=None) -> Dict[str, object]:
    """Every mark of the study except L1 (pinned by the build and the test)."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    indices = {rung: CG._index(rung, carriers) for rung in LADDER}
    rads = {rung: radii(rung, carriers, indices[rung]) for rung in LADDER}
    radius_rows = tuple({
        "rung": rung, "norm": NH.rung_norm(rung), "cells": len(rads[rung]),
        "below_packing": sum(1 for v in rads[rung].values()
                             if v < Fraction(NH.rung_norm(rung), 4)),
        "smallest": min(rads[rung].values()),
    } for rung in LADDER)
    sets = query_sets(carriers)
    read = {name: read_set(carriers, queries, indices, rads)
            for name, queries in sets.items()}
    union = CG.union_ladder(carriers, sets)
    union_fourth = NH.run_ladder(union["ladder"], carriers, sets["fourth"])
    marks = {
        "P1": (all(row["below_packing"] == 0 for row in radius_rows)
               and all(r["p1_violations"] == 0 for r in read.values())),
        "N1": all(r["n1_violations"] == 0 for r in read.values()),
        "S1": read["standard"]["placed"]["wrong"] == 0,
        "S2": read["held_out"]["placed"]["wrong"] == 0,
        "S3": read["third"]["placed"]["wrong"] == 0,
        "S4": read["fourth"]["placed"]["wrong"] == 0,
        "K1": all(r["kept_share"] >= Fraction(1, 2) for r in read.values()),
        "U2": union_fourth["wrong"] == 0,
    }
    return {"ladder": LADDER, "radii": radius_rows, "read": read,
            "union": {"ladder": union["ladder"],
                      "retired": union["retired"]},
            "union_fourth": union_fourth, "marks": marks}


# ═════════════════════════════════════════════════════════════════════════
# THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "placement_guard.json")

_SOURCES: Tuple[str, ...] = ("reasoning/placement_guard.py",) + tuple(
    CG._SOURCES)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    return integrity.tree_digest([root / name for name in names], root)


def measure() -> Dict[str, object]:
    """The whole study, recomputed."""
    report = placement_guard_report()
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurement and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(CG._freeze(measure()), indent=1,
                                 sort_keys=True, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurement if it still describes the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
