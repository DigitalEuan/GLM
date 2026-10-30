"""``glm_universal.reasoning.norm256_hex`` -- norm 256 and the hex colour
(Phase 127; lattice item 3).

``studies/NORM_256_HEX_STUDY.md`` pre-registered three candidates for the
empty norm-256 rung of the power-of-two family, the order they are tried in, a
held-out query set and nine marks.  This module takes them.

The candidates
--------------
==========  ======================================================  =========
key         construction                                            kissing
==========  ======================================================  =========
``R256``    ``(1 + hexRot)(2 Lambda_24)``: rung ``2C`` rotated by    196,560
            ``sqrt 2``
``16Z``     ``16 Z^24``: each coordinate rounded to a multiple of    48
            16 (the nearest hex digit)
``H16``     the coset ``16 Z^24 + 8``: each coordinate read by its   48
            first hex digit ``floor(v / 16)``
==========  ======================================================  =========

``hexRot`` is the signed permutation ``x -> (j -> e(P j) x(P j))`` with
:data:`HEX_P` a fixed-point-free involution that is a Golay automorphism and
:data:`HEX_S` a dodecad meeting every pair of it once.
``RequestProject/GLM/HexRung.lean`` proves that it squares to ``-1``, maps the
Leech lattice to itself (``hexRot_isLeech``), doubles every norm under
``1 + hexRot`` (``normSq_add_rot``), that ``R256`` has minimum norm at least
256 (``rotLeech_min_norm``), and that the nearest point of ``R256`` is
``1 + hexRot`` applied to the nearest point of ``2C`` to ``(y - hexRot y)/2``
(``nearest_transfer``) -- which is the quantiser below.

The hex shortcut
----------------
The package names every class of ``Lambda_24 / 2 Lambda_24`` by a 24-bit word
(:func:`glm_universal.substrate.leech2.class_of`), i.e. by a six-digit hex
colour.  The image ``W`` of ``1 + hexRot`` on those classes is a
12-dimensional subspace -- 4096 = 16**3 colours -- and a point ``p`` of ``2C``
lies on ``R256`` exactly when the colour of ``p / 2`` is in ``W``: twelve
parity checks on six hex digits (X1, X2).

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout; the test vectors and
the points are the package's deterministic sweep.  No float, no randomness.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import construction_ladder as CL
from ..substrate import leech2 as L2
from ..substrate.linalg import f2_independent, f2_rank
from . import empty_rungs as ER
from . import ladder_escalation as LE
from . import norm_escalation as NE
from .fwht_decode import _Sweep

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "HEX_P", "HEX_S", "HEX_SIGN", "hex_rot",
    "CANDIDATES", "CANDIDATE_ORDER", "BASE_LADDER", "quantise", "in_rung",
    "rung_norm", "quantiser_check", "candidate_facts", "HELD_OUT",
    "held_out_queries", "standard_queries", "audit", "run_ladder", "fill",
    "hex_colour", "w_basis", "in_w", "shortcut_check", "held_out_marks",
    "norm256_hex_report", "DATA_PATH", "module_digest", "measure",
    "write_measurements", "measurements", "state", "current",
]

LEAN_FILE = "RequestProject/GLM/HexRung.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "rot_rot", "inner_rot_self", "normSq_add_rot", "sub_rot_add_rot",
    "min_norm_doubles", "nearest_transfer", "golay_perm_closed",
    "hexRot_isLeech", "rotLeech_min_norm", "floor_bucket_nearest",
    "hex_counts")

Point = Tuple[int, ...]

# ═════════════════════════════════════════════════════════════════════════
# 1.  THE ROTATION
# ═════════════════════════════════════════════════════════════════════════

#: ``hexP`` of the Lean file: a fixed-point-free involution of the 24
#: coordinates that is an automorphism of the Golay code.
HEX_P: Tuple[int, ...] = (1, 0, 3, 2, 5, 4, 9, 20, 23, 6, 14, 13, 21, 11, 10,
                          16, 15, 19, 22, 17, 7, 12, 18, 8)
#: ``hexS``: a dodecad meeting every pair of :data:`HEX_P` once.
HEX_S: int = 466837
#: The sign vector, ``-1`` on :data:`HEX_S`.
HEX_SIGN: Tuple[int, ...] = tuple(-1 if (HEX_S >> i) & 1 else 1
                                  for i in range(24))


def hex_rot(x: Sequence) -> Tuple:
    """``hexRot``: ``(j -> e(P j) * x(P j))``; works on ints and Fractions."""
    return tuple(HEX_SIGN[HEX_P[j]] * x[HEX_P[j]] for j in range(24))


def _plus_rot(x: Sequence) -> Tuple:
    r = hex_rot(x)
    return tuple(a + b for a, b in zip(x, r))


def _half_minus_rot(y: Sequence) -> Tuple[Fraction, ...]:
    r = hex_rot(y)
    return tuple((Fraction(a) - Fraction(b)) / 2 for a, b in zip(y, r))


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE CANDIDATES
# ═════════════════════════════════════════════════════════════════════════

CANDIDATES: Dict[str, Dict[str, object]] = {
    "R256": {"title": "(1 + hexRot)(2 Lambda_24), rung 2C rotated by sqrt 2",
             "norm": 256, "kissing": 196_560, "covolume_log2": 72,
             "lattice": True},
    "16Z": {"title": "16 Z^24, the nearest hex digit", "norm": 256,
            "kissing": 48, "covolume_log2": 96, "lattice": True},
    "H16": {"title": "16 Z^24 + 8, the first hex digit floor(v/16)",
            "norm": 256, "kissing": 48, "covolume_log2": 96,
            "lattice": False},
}

#: The declared order: densest first, a lattice before a translate.
CANDIDATE_ORDER: Tuple[str, ...] = ("R256", "16Z", "H16")

#: The ladder Phase 123 left: the repaired ladder with ``D12^2`` at norm 2.
BASE_LADDER: Tuple[str, ...] = ER._insert(ER.REPAIRED, "D12^2")


def _quantise_candidate(values: Tuple[Fraction, ...], key: str) -> Point:
    if key == "R256":
        z = _half_minus_rot(values)
        q = tuple(LE.quantise(z, "2C").point)
        return tuple(int(v) for v in _plus_rot(q))
    if key == "16Z":
        return tuple(16 * LE._round_nearest(v / 16)[0] for v in values)
    if key == "H16":
        return tuple(16 * int(v // 16) + 8 for v in values)
    raise KeyError(key)


_CACHE: Dict[Tuple[Tuple[Fraction, ...], str], Point] = {}


def quantise(vector: Sequence, rung: str) -> Point:
    """The nearest point of ``rung``: a candidate here, else Phase 123's."""
    values = tuple(Fraction(x) for x in vector)
    key = (values, rung)
    hit = _CACHE.get(key)
    if hit is not None:
        return hit
    if rung in CANDIDATES:
        point = _quantise_candidate(values, rung)
    else:
        point = ER.quantise(values, rung)
    _CACHE[key] = point
    return point


def in_rung(vector: Sequence[int], key: str) -> bool:
    """Membership in a candidate, from its definition."""
    if key == "R256":
        z = _half_minus_rot(vector)
        if any(v.denominator != 1 for v in z):
            return False
        return CL.in_rung(tuple(int(v) for v in z), "2C")
    if key == "16Z":
        return all(int(x) % 16 == 0 for x in vector)
    if key == "H16":
        return all((int(x) - 8) % 16 == 0 for x in vector)
    raise KeyError(key)


def rung_norm(rung: str) -> int:
    if rung in CANDIDATES:
        return int(CANDIDATES[rung]["norm"])
    return ER.rung_norm(rung)


def _insert(ladder: Sequence[str], rung: str) -> Tuple[str, ...]:
    norm = rung_norm(rung)
    return (tuple(r for r in ladder if rung_norm(r) > norm) + (rung,)
            + tuple(r for r in ladder if rung_norm(r) < norm))


# ═════════════════════════════════════════════════════════════════════════
# 3.  C1 -- THE QUANTISERS, CHECKED
# ═════════════════════════════════════════════════════════════════════════

def _nsq(v: Sequence) -> Fraction:
    return sum((Fraction(x) * Fraction(x) for x in v), Fraction(0))


def quantiser_check(key: str, vectors: int = 200, seed: int = 20260902
                    ) -> Dict[str, object]:
    """C1: on the Phase 123 test vectors the answer is on the rung; for
    ``R256`` the distance is ``sqrt 2`` times the ``2C`` one (the identity
    ``nearest_transfer`` rests on); for the per-coordinate readings no single
    coordinate step of 16 is nearer."""
    sweep = _Sweep(seed)
    failures = 0
    for _ in range(vectors):
        y = [Fraction(sweep.below(8001) - 4000, 1000) * 8 for _ in range(24)]
        p = quantise(y, key)
        ok = in_rung(p, key)
        if key == "R256":
            z = _half_minus_rot(y)
            q = tuple(LE.quantise(z, "2C").point)
            ok = ok and (_nsq([a - b for a, b in zip(y, p)])
                         == 2 * _nsq([a - b for a, b in zip(z, q)]))
        else:
            for i in range(24):
                here = (y[i] - p[i]) ** 2
                if (y[i] - p[i] - 16) ** 2 < here or \
                        (y[i] - p[i] + 16) ** 2 < here:
                    ok = False
        failures += 0 if ok else 1
    return {"key": key, "vectors": vectors, "failures": failures,
            "holds": failures == 0}


def _kissing_axis(step: int = 16) -> Tuple[int, int]:
    """Minimum norm and kissing number of ``16 Z^24`` (and of its translate's
    difference lattice), by enumerating every vector with at most two nonzero
    entries in ``{+-16, +-32}`` -- every shorter-than-512 vector is one."""
    counts: Dict[int, int] = {}
    values = (-2 * step, -step, step, 2 * step)
    for i in range(24):
        for a in values:
            counts[a * a] = counts.get(a * a, 0) + 1
            for j in range(i + 1, 24):
                for b in values:
                    n = a * a + b * b
                    counts[n] = counts.get(n, 0) + 1
    minimum = min(counts)
    return minimum, counts[minimum]


def candidate_facts() -> Tuple[Dict[str, object], ...]:
    rows = []
    axis = _kissing_axis()
    for key in CANDIDATE_ORDER:
        check = quantiser_check(key)
        row: Dict[str, object] = {"key": key, "norm": rung_norm(key),
                                  "quantiser_failures": check["failures"]}
        if key == "R256":
            row["kissing_by"] = "rotLeech_min_norm and normSq_add_rot"
            row["holds"] = bool(check["holds"])
        else:
            row["enumerated_norm"], row["enumerated_kissing"] = axis
            row["holds"] = bool(check["holds"]) and axis == (256, 48)
        rows.append(row)
    return tuple(rows)


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE QUERY SETS AND THE AUDIT
# ═════════════════════════════════════════════════════════════════════════

#: The held-out perturbations of section 4: ``(label, support, magnitude)``,
#: applied with the codeword index ``i + HELD_OUT_OFFSET``.
HELD_OUT: Tuple[Tuple[str, int, Fraction], ...] = (
    ("12 coordinates by 1/3", 12, Fraction(1, 3)),
    ("12 coordinates by 2/3", 12, Fraction(2, 3)),
    ("6 coordinates by 1", 6, Fraction(1)),
    ("24 coordinates by 1/2", 24, Fraction(1, 2)),
)
HELD_OUT_OFFSET = 2048

Query = Tuple[int, Tuple[Fraction, ...]]


def standard_queries(carriers) -> List[Query]:
    """The 568 queries of the norm family."""
    return ER._queries(carriers)


def held_out_queries(carriers) -> List[Query]:
    """The 568 held-out queries, declared in section 4."""
    out: List[Query] = []
    for _label, support, magnitude in HELD_OUT:
        for i, (_r, _n, carrier) in enumerate(carriers):
            out.append((i, LE.perturb(carrier, i + HELD_OUT_OFFSET, support,
                                      magnitude)))
    return out


def _index(rung: str, carriers) -> Dict[Point, Tuple[int, ...]]:
    table: Dict[Point, List[int]] = {}
    for i, (_r, _n, carrier) in enumerate(carriers):
        table.setdefault(quantise(carrier, rung), []).append(i)
    return {p: tuple(m) for p, m in table.items()}


def _named(query, rung: str, indices) -> Optional[int]:
    members = indices[rung].get(quantise(query, rung), ())
    return members[0] if len(members) == 1 else None


def audit(ladder: Sequence[str], carriers, queries: Sequence[Query]
          ) -> Tuple[Dict[str, object], ...]:
    """Per rung: correct, wrong, refused, unique_correct, disagrees -- the
    columns :func:`norm_escalation.retirement` reads."""
    ladder = tuple(ladder)
    indices = {rung: _index(rung, carriers) for rung in ladder}
    rows = {rung: {"correct": 0, "wrong": 0, "refused": 0,
                   "unique_correct": 0, "disagrees": 0} for rung in ladder}
    for truth, query in queries:
        named = {rung: _named(query, rung, indices) for rung in ladder}
        for rung, answer in named.items():
            key = ("refused" if answer is None
                   else "correct" if answer == truth else "wrong")
            rows[rung][key] += 1
        right = [rung for rung in ladder if named[rung] == truth]
        if len(right) == 1:
            rows[right[0]]["unique_correct"] += 1
        spoken = {r: a for r, a in named.items() if a is not None}
        if len(set(spoken.values())) > 1:
            for rung in spoken:
                rows[rung]["disagrees"] += 1
    return tuple(dict(rung=rung, minimum_norm=rung_norm(rung), **rows[rung])
                 for rung in ladder)


def run_ladder(ladder: Sequence[str], carriers, queries: Sequence[Query]
               ) -> Dict[str, object]:
    """Correct, wrong and refused in the three visiting orders, the oracle and
    the disagreements."""
    ladder = tuple(ladder)
    indices = {rung: _index(rung, carriers) for rung in ladder}
    orders = {"middle_out": CL.middle_out_order(ladder),
              "coarse_to_fine": ladder,
              "fine_to_coarse": tuple(reversed(ladder))}
    totals = {name: {"correct": 0, "wrong": 0, "refused": 0}
              for name in orders}
    oracle = 0
    for truth, query in queries:
        named = {rung: _named(query, rung, indices) for rung in ladder}
        oracle += int(any(a == truth for a in named.values()))
        for name, order in orders.items():
            answer = next((named[r] for r in order if named[r] is not None),
                          None)
            key = ("refused" if answer is None
                   else "correct" if answer == truth else "wrong")
            totals[name][key] += 1
    correct = {t["correct"] for t in totals.values()}
    wrong = {t["wrong"] for t in totals.values()}
    return {"ladder": ladder, "totals": totals, "oracle": oracle,
            "order_independent": len(correct) == 1 and len(wrong) == 1,
            "correct": max(correct), "wrong": max(wrong),
            "refused": max(t["refused"] for t in totals.values()),
            "safe": max(wrong) == 0,
            "matches_oracle": totals["middle_out"]["correct"] == oracle}


def fill(carriers, queries: Sequence[Query]) -> Dict[str, object]:
    """The declared filling rule at norm 256, in the declared order."""
    trials: List[Dict[str, object]] = []
    kept: Optional[str] = None
    ladder = BASE_LADDER
    for key in CANDIDATE_ORDER:
        trial = _insert(BASE_LADDER, key)
        rows = audit(trial, carriers, queries)
        verdict = NE.retirement(rows)
        ok = not verdict["any_retired"]
        mine = next(r for r in rows if r["rung"] == key)
        trials.append({"candidate": key, "ladder": trial, "row": mine,
                       "retired": verdict["retired"], "kept": ok})
        if ok:
            kept, ladder = key, trial
            break
    return {"trials": tuple(trials), "kept": kept, "ladder": ladder}


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE HEX SHORTCUT
# ═════════════════════════════════════════════════════════════════════════

def hex_colour(cls: int) -> str:
    """The six-hex-digit colour of a 24-bit class."""
    return "#" + format(cls, "06x")


def w_basis() -> Tuple[int, ...]:
    """A basis of ``W``: the classes of ``y + hexRot y`` over the Leech basis,
    reduced by the package's own F2 row reduction."""
    images = [L2.class_of(list(_plus_rot(row))) for row in L2.LEECH_BASIS]
    return tuple(f2_independent(images))


def in_w(cls: int, basis: Optional[Sequence[int]] = None) -> bool:
    """Is the class in ``W``?  Adding it to a basis leaves the rank unchanged."""
    basis = w_basis() if basis is None else basis
    return f2_rank(list(basis) + [cls]) == len(basis)


def shortcut_check(points: int = 1000, seed: int = 20261010
                   ) -> Dict[str, object]:
    """X1 and X2."""
    basis = w_basis()
    singular = all(L2.q_form(b) == 0 for b in basis)
    # q vanishes on the whole span iff on a basis and b vanishes pairwise
    pairwise = all(L2.b_form(a, b) == 0 for a in basis for b in basis)
    sweep = _Sweep(seed)
    on_rung_yes = 0
    for _ in range(points):
        u = [sweep.below(5) - 2 for _ in range(24)]
        y = L2.from_coords(u)
        p = _plus_rot([2 * v for v in y])
        if in_rung(p, "R256") and in_w(L2.class_of([v // 2 for v in p]),
                                       basis):
            on_rung_yes += 1
    agree = 0
    members = 0
    for _ in range(points):
        u = [sweep.below(5) - 2 for _ in range(24)]
        p = [2 * v for v in L2.from_coords(u)]
        direct = in_rung(p, "R256")
        short = in_w(L2.class_of([v // 2 for v in p]), basis)
        agree += int(direct == short)
        members += int(direct)
    return {"dimension": len(basis), "colours": 1 << len(basis),
            "basis_colours": tuple(hex_colour(b) for b in basis),
            "totally_singular": singular and pairwise,
            "points": points, "rung_points_said_yes": on_rung_yes,
            "agree": agree, "members_among_sample": members,
            "X1": len(basis) == 12 and singular and pairwise,
            "X2": on_rung_yes == points and agree == points}


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def held_out_marks(carriers, kept: Optional[str],
                   filled: Sequence[str]) -> Dict[str, object]:
    """H1 and H2, plus every candidate and the base ladder on the held-out
    set as description."""
    queries = held_out_queries(carriers)
    alone = {key: audit((key,), carriers, queries)[0]
             for key in CANDIDATE_ORDER}
    base = run_ladder(BASE_LADDER, carriers, queries)
    final = run_ladder(filled, carriers, queries)
    rows = audit(filled, carriers, queries)
    return {"queries": len(queries), "alone": alone, "base": base,
            "final": final, "final_rows": rows,
            "H1": kept is not None and alone[kept]["wrong"] == 0,
            "H2": kept is not None and final["wrong"] == 0}


def norm256_hex_report(carriers=None) -> Dict[str, object]:
    """Every mark of the study except L1 (pinned by the build)."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    queries = standard_queries(carriers)
    facts = candidate_facts()
    filling = fill(carriers, queries)
    base = run_ladder(BASE_LADDER, carriers, queries)
    final = run_ladder(filling["ladder"], carriers, queries)
    held = held_out_marks(carriers, filling["kept"], filling["ladder"])
    shortcut = shortcut_check()
    retired = {t["candidate"]: [r["clause"] for r in t["retired"]
                                if r["rung"] == t["candidate"]]
               for t in filling["trials"]}
    marks = {
        "C1": all(bool(r["holds"]) for r in facts),
        "F1": (filling["kept"] == "H16"
               and retired.get("R256") == [1] and retired.get("16Z") == [1]),
        "F2": (final["safe"] and final["order_independent"]
               and final["matches_oracle"] and final["correct"] >= 467),
        "H1": bool(held["H1"]),
        "H2": bool(held["H2"]),
        "X1": bool(shortcut["X1"]),
        "X2": bool(shortcut["X2"]),
    }
    return {"facts": facts, "filling": filling, "base": base, "final": final,
            "held_out": held, "shortcut": shortcut, "marks": marks}


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "norm256_hex.json")

_SOURCES: Tuple[str, ...] = ("reasoning/norm256_hex.py",
                             "substrate/leech2.py", "substrate/linalg.py") + tuple(ER._SOURCES)


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
    report = norm256_hex_report()
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
