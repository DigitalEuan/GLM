"""``glm_universal.reasoning.cell_guard`` -- the cell guard (Phase 128;
STATUS item "the ladder on held-out perturbations").

``studies/CELL_GUARD_STUDY.md`` pre-registered two answers to the eight wrong
answers Phase 127's held-out set found in the ladder Phase 123 left, a third,
unseen query set, and nine marks.  This module takes them.

The guard
---------
A rung of minimum norm ``m`` names the single carrier ``i`` of the cell its
quantiser puts the query ``q`` in.  The **cell guard** lets it answer only
when

    ``|q - c_i| + |q - Q(q)| < sqrt(m) / 2``

-- the query's displacement from the named carrier, plus its distance from
the cell's centre, inside the packing radius.  ``RequestProject/GLM/
CellGuard.lean`` proves that a guarded answer is then the *strictly nearest*
carrier to the query among all carriers (``guarded_strict_nearest``), so two
guarded rungs never disagree (``guarded_agree``, ``firstNamed_agree``), and
that the test is decided exactly by ``A + B < R`` and ``4AB < (R - A - B)^2``
with ``A``, ``B`` the squared distances and ``R = m / 4``
(``sqrt_add_lt_sqrt_iff``).  No square root is taken here.

The comparison
--------------
``U``: the retirement rule of :func:`norm_escalation.retirement` read over the
standard and held-out queries together, retired rungs dropped, the rest read
unguarded.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout; the test vectors are a
deterministic integer sweep.  No float, no randomness.
"""

from __future__ import annotations

import json
from fractions import Fraction
from math import isqrt
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import construction_ladder as CL
from . import ladder_escalation as LE
from . import norm256_hex as NH
from . import norm_escalation as NE
from .fwht_decode import _Sweep

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "LADDER", "THIRD", "THIRD_OFFSET",
    "third_queries", "query_sets", "guard_holds", "guarded_named",
    "nearest_carrier", "quantiser_hypothesis", "read_set", "union_ladder",
    "placement",
    "cell_guard_report", "DATA_PATH", "module_digest", "measure",
    "write_measurements", "measurements", "state", "current",
]

LEAN_FILE = "RequestProject/GLM/CellGuard.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "quantise_eq_of_dist_lt", "guarded_strict_nearest",
    "guarded_isStrictNearest", "strictNearest_unique", "guarded_agree",
    "firstNamed_agree", "guarded_correct_of_close", "sqrt_add_lt_sqrt_iff")

#: The ladder Phase 123 left (and Phase 127 measured on the held-out set).
LADDER: Tuple[str, ...] = NH.BASE_LADDER

#: The third query set of section 4: ``(label, support, magnitude)``, applied
#: with the codeword index ``i + THIRD_OFFSET``.
THIRD: Tuple[Tuple[str, int, Fraction], ...] = (
    ("16 coordinates by 1/2", 16, Fraction(1, 2)),
    ("8 coordinates by 1", 8, Fraction(1)),
    ("4 coordinates by 3/2", 4, Fraction(3, 2)),
    ("20 coordinates by 1/4", 20, Fraction(1, 4)),
)
THIRD_OFFSET = 3072

Query = Tuple[int, Tuple[Fraction, ...]]
Point = Tuple[int, ...]


def third_queries(carriers) -> List[Query]:
    """The 568 queries of the third set, declared in section 4."""
    out: List[Query] = []
    for _label, support, magnitude in THIRD:
        for i, (_r, _n, carrier) in enumerate(carriers):
            out.append((i, LE.perturb(carrier, i + THIRD_OFFSET, support,
                                      magnitude)))
    return out


def query_sets(carriers) -> Dict[str, List[Query]]:
    """The three query sets, in the order they were declared."""
    return {"standard": NH.standard_queries(carriers),
            "held_out": NH.held_out_queries(carriers),
            "third": third_queries(carriers)}


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE GUARD
# ═════════════════════════════════════════════════════════════════════════

def _nsq(a: Sequence, b: Sequence) -> Fraction:
    return sum(((Fraction(x) - Fraction(y)) ** 2 for x, y in zip(a, b)),
               Fraction(0))


def guard_holds(a2: Fraction, b2: Fraction, norm: int) -> bool:
    """``sqrt(a2) + sqrt(b2) < sqrt(norm / 4)``, decided exactly
    (``GLM.CellGuard.sqrt_add_lt_sqrt_iff``)."""
    r2 = Fraction(norm, 4)
    slack = r2 - a2 - b2
    return slack > 0 and 4 * a2 * b2 < slack * slack


def _index(rung: str, carriers) -> Dict[Point, Tuple[int, ...]]:
    table: Dict[Point, List[int]] = {}
    for i, (_r, _n, carrier) in enumerate(carriers):
        table.setdefault(NH.quantise(carrier, rung), []).append(i)
    return {p: tuple(m) for p, m in table.items()}


def guarded_named(query: Sequence[Fraction], rung: str, indices,
                  carriers) -> Tuple[Optional[int], Optional[int], bool]:
    """``(unguarded answer, guarded answer, guard computed)`` at one rung."""
    point = NH.quantise(query, rung)
    members = indices[rung].get(point, ())
    if len(members) != 1:
        return None, None, False
    i = members[0]
    a2 = _nsq(query, carriers[i][2])
    b2 = _nsq(query, point)
    return i, (i if guard_holds(a2, b2, NH.rung_norm(rung)) else None), True


def nearest_carrier(query: Sequence[Fraction], carriers) -> Optional[int]:
    """The strictly nearest carrier, or ``None`` at a tie."""
    dists = [_nsq(query, carrier) for (_r, _n, carrier) in carriers]
    best = min(dists)
    winners = [i for i, d in enumerate(dists) if d == best]
    return winners[0] if len(winners) == 1 else None


# ═════════════════════════════════════════════════════════════════════════
# 2.  Q1 -- THE HYPOTHESIS THE THEOREMS NEED
# ═════════════════════════════════════════════════════════════════════════

def quantiser_hypothesis(rung: str, vectors: int = 200,
                         seed: int = 20261011) -> Dict[str, object]:
    """Q1: a rung point plus an offset of squared length below ``m/4`` is
    quantised back to that point (``quantise_eq_of_dist_lt``)."""
    norm = NH.rung_norm(rung)
    scale = max(1, isqrt(norm))
    sweep = _Sweep(seed + norm)
    failures = 0
    for _ in range(vectors):
        x = [Fraction(sweep.below(8001) - 4000, 1000) * scale
             for _ in range(24)]
        p = NH.quantise(x, rung)
        d = [Fraction(sweep.below(2001) - 1000, 1000) for _ in range(24)]
        length = sum((v * v for v in d), Fraction(0))
        if length == 0:
            d[0], length = Fraction(1, 1000), Fraction(1, 1000000)
        # t = k/1000 with t^2 * length < norm/4, as large as k allows
        k = isqrt(int(Fraction(norm, 4) * 1000000 / length))
        while k > 0 and Fraction(k, 1000) ** 2 * length >= Fraction(norm, 4):
            k -= 1
        t = Fraction(k, 1000)
        y = [Fraction(a) + t * b for a, b in zip(p, d)]
        if NH.quantise(y, rung) != p:
            failures += 1
    return {"rung": rung, "norm": norm, "vectors": vectors,
            "failures": failures, "holds": failures == 0}


# ═════════════════════════════════════════════════════════════════════════
# 3.  ONE QUERY SET, READ
# ═════════════════════════════════════════════════════════════════════════

def _verdict(answer: Optional[int], truth: int) -> str:
    return ("refused" if answer is None
            else "correct" if answer == truth else "wrong")


def read_set(carriers, queries: Sequence[Query],
             ladder: Sequence[str] = LADDER) -> Dict[str, object]:
    """The unguarded and the guarded ladder on one query set, with N1, N2,
    the nearest-carrier floor and the per-rung counts."""
    ladder = tuple(ladder)
    indices = {rung: _index(rung, carriers) for rung in ladder}
    orders = {"middle_out": CL.middle_out_order(ladder),
              "coarse_to_fine": ladder,
              "fine_to_coarse": tuple(reversed(ladder))}
    plain = {name: {"correct": 0, "wrong": 0, "refused": 0}
             for name in orders}
    guarded = {name: {"correct": 0, "wrong": 0, "refused": 0}
               for name in orders}
    per_rung = {rung: {"answered": 0, "guarded": 0, "guarded_correct": 0,
                       "guarded_wrong": 0} for rung in ladder}
    nearest = {"correct": 0, "wrong": 0, "tie": 0}
    n1_violations = 0
    n2_violations = 0
    guard_evaluations = 0
    removed_wrong: List[Dict[str, object]] = []
    for truth, query in queries:
        near = nearest_carrier(query, carriers)
        nearest["tie" if near is None
                else "correct" if near == truth else "wrong"] += 1
        named: Dict[str, Optional[int]] = {}
        safe: Dict[str, Optional[int]] = {}
        for rung in ladder:
            a, g, computed = guarded_named(query, rung, indices, carriers)
            named[rung], safe[rung] = a, g
            guard_evaluations += int(computed)
            if a is not None:
                per_rung[rung]["answered"] += 1
            if g is not None:
                per_rung[rung]["guarded"] += 1
                per_rung[rung]["guarded_" + ("correct" if g == truth
                                             else "wrong")] += 1
                if g != near:
                    n1_violations += 1
        for name, order in orders.items():
            first = next((named[r] for r in order if named[r] is not None),
                         None)
            plain[name][_verdict(first, truth)] += 1
            gfirst = next((safe[r] for r in order if safe[r] is not None),
                          None)
            guarded[name][_verdict(gfirst, truth)] += 1
            if name == "middle_out":
                if gfirst is not None and gfirst != truth and near == truth:
                    n2_violations += 1
                if first is not None and first != truth:
                    removed_wrong.append({
                        "truth": carriers[truth][1],
                        "named": carriers[first][1],
                        "rung": next(r for r in order
                                     if named[r] is not None),
                        "guarded_answer": (None if gfirst is None
                                           else carriers[gfirst][1])})

    def _summary(totals):
        correct = {t["correct"] for t in totals.values()}
        wrong = {t["wrong"] for t in totals.values()}
        return {"totals": totals, "correct": max(correct),
                "wrong": max(wrong),
                "refused": max(t["refused"] for t in totals.values()),
                "order_independent": len(correct) == 1 and len(wrong) == 1}

    plain_s = _summary(plain)
    guard_s = _summary(guarded)
    kept = (Fraction(guard_s["totals"]["middle_out"]["correct"],
                     plain_s["totals"]["middle_out"]["correct"])
            if plain_s["totals"]["middle_out"]["correct"] else Fraction(1))
    return {"queries": len(queries), "plain": plain_s, "guarded": guard_s,
            "per_rung": per_rung, "nearest": nearest,
            "n1_violations": n1_violations, "n2_violations": n2_violations,
            "guard_evaluations": guard_evaluations,
            "kept_share": kept, "unguarded_wrong": removed_wrong}


# ═════════════════════════════════════════════════════════════════════════
# 4.  U -- THE RETIREMENT RULE READ ON TWO SETS
# ═════════════════════════════════════════════════════════════════════════

def union_ladder(carriers, sets: Dict[str, List[Query]]
                 ) -> Dict[str, object]:
    """The retirement rule over the standard and held-out sets together."""
    queries = list(sets["standard"]) + list(sets["held_out"])
    rows = NH.audit(LADDER, carriers, queries)
    verdict = NE.retirement(rows)
    kept = tuple(r for r in LADDER if r in set(verdict["kept"]))
    return {"queries": len(queries), "rows": rows,
            "retired": verdict["retired"], "ladder": kept}


def placement(carriers) -> Tuple[Dict[str, object], ...]:
    """Post hoc: per rung, how many carriers sit inside the inscribed ball of
    their own cell, and how many are alone in it.  A carrier outside the ball
    can never pass the guard, whatever the perturbation: the query ``c_i``
    itself fails it."""
    out: List[Dict[str, object]] = []
    for rung in LADDER:
        norm = NH.rung_norm(rung)
        index = _index(rung, carriers)
        inside = alone = both = 0
        for (_r, _n, carrier) in carriers:
            point = NH.quantise(carrier, rung)
            ins = _nsq(carrier, point) < Fraction(norm, 4)
            alo = len(index[point]) == 1
            inside += int(ins)
            alone += int(alo)
            both += int(ins and alo)
        out.append({"rung": rung, "norm": norm, "inside": inside,
                    "alone": alone, "inside_and_alone": both,
                    "carriers": len(carriers)})
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def cell_guard_report(carriers=None) -> Dict[str, object]:
    """Every mark of the study except L1 (pinned by the build and the test)."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    hypothesis = tuple(quantiser_hypothesis(rung) for rung in LADDER)
    sets = query_sets(carriers)
    read = {name: read_set(carriers, queries)
            for name, queries in sets.items()}
    union = union_ladder(carriers, sets)
    union_third = NH.run_ladder(union["ladder"], carriers, sets["third"])
    marks = {
        "Q1": all(bool(h["holds"]) for h in hypothesis),
        "N1": all(r["n1_violations"] == 0 for r in read.values()),
        "N2": all(r["n2_violations"] == 0 for r in read.values()),
        "S1": (read["standard"]["guarded"]["wrong"] == 0
               and read["standard"]["guarded"]["order_independent"]),
        "S2": read["held_out"]["guarded"]["wrong"] == 0,
        "S3": read["third"]["guarded"]["wrong"] == 0,
        "K1": all(r["kept_share"] >= Fraction(1, 2) for r in read.values()),
        "U1": union_third["wrong"] == 0,
    }
    return {"ladder": LADDER, "hypothesis": hypothesis, "read": read,
            "placement": placement(carriers), "union": union,
            "union_third": union_third, "marks": marks}


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "cell_guard.json")

_SOURCES: Tuple[str, ...] = ("reasoning/cell_guard.py",) + tuple(NH._SOURCES)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    return integrity.tree_digest([root / name for name in names], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The whole study, recomputed."""
    report = cell_guard_report()
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurement and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
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
