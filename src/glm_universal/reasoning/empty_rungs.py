"""``glm_universal.reasoning.empty_rungs`` -- Construction A rungs for the two
empty norms of the power-of-two family (Phase 123, part C; lattice item 3).

The question
------------
:mod:`glm_universal.reasoning.norm_escalation` repaired the power-of-two
ladder by a declared retirement rule, and the repair left norms 2 and 256
empty: every rung the scaling ``L -> 2L`` generates at those norms was
retired.  ``studies/LATTICE_COMPLETION_STUDY.md`` §2.C names the candidates
that the scaling does not generate -- Construction A over direct sums of
short binary codes -- and a declared rule for trying them.

The candidates
--------------
==========  ==========================================  =====  =======  =========
key         lattice (Construction A over ...)           norm   kissing  covolume
==========  ==========================================  =====  =======  =========
``D12^2``   even-weight ``[12,11,2]^2``                 2      528      ``2^2``
``D8^3``    even-weight ``[8,7,2]^3``                   2      336      ``2^3``
``D4^6``    even-weight ``[4,3,2]^6``                   2      144      ``2^6``
``8E8^3``   ``8 x`` extended Hamming ``[8,4,4]^3``      256    720      ``2^84``
``8D4^6``   ``8 x`` repetition ``[4,1,4]^6``            256    144      ``2^90``
==========  ==========================================  =====  =======  =========

``GLM.LatticeCompletion.constructionA_normSq_ge`` proves Construction A over
a code of minimum distance ``d`` has minimum norm ``min 4 d``; the scaling by
eight multiplies it by 64 (``GLM.NormFamily.scaled_min_norm``).

The rule
--------
Norm 2 first, then norm 256, each densest first.  A candidate is inserted
into the repaired ladder at its norm and the 568 queries are re-read; it is
**kept** when the retirement rule of :func:`norm_escalation.retirement`
retires no rung of the resulting ladder.

Everything else -- the carriers, the perturbations, the stopping rule, the
three visiting orders, the audit -- is the norm family's, re-used.  The new
rungs have their own exact nearest-point quantisers here; every existing rung
is quantised by :func:`ladder_escalation.quantise`, unchanged.

Exactness
---------
Integers and :class:`~fractions.Fraction`; the test vectors come from the
package's deterministic sweep.
"""

from __future__ import annotations

import json
from fractions import Fraction
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import construction_ladder as CL
from . import ladder_escalation as LE
from . import norm_escalation as NE
from .fwht_decode import _Sweep

__all__ = [
    "CANDIDATES", "CANDIDATE_ORDER", "REPAIRED", "quantise", "in_rung",
    "short_vectors", "candidate_facts", "quantiser_check", "audit",
    "run_ladder", "fill", "empty_rungs_report", "module_digest", "measure",
    "write_measurements", "measurements", "state", "current", "DATA_PATH",
]

Point = Tuple[int, ...]

# ═════════════════════════════════════════════════════════════════════════
# 1.  THE CANDIDATES
# ═════════════════════════════════════════════════════════════════════════

#: The extended Hamming code ``[8,4,4]`` (first-order Reed--Muller), from its
#: generator rows.
_HAMMING_ROWS: Tuple[Tuple[int, ...], ...] = (
    (1, 1, 1, 1, 0, 0, 0, 0), (1, 1, 0, 0, 1, 1, 0, 0),
    (1, 0, 1, 0, 1, 0, 1, 0), (1, 1, 1, 1, 1, 1, 1, 1))


def _span(rows: Sequence[Sequence[int]]) -> Tuple[Tuple[int, ...], ...]:
    words = {tuple(0 for _ in rows[0])}
    for row in rows:
        words |= {tuple((a + b) % 2 for a, b in zip(word, row))
                  for word in words}
    return tuple(sorted(words))


HAMMING8: Tuple[Tuple[int, ...], ...] = _span(_HAMMING_ROWS)
REPETITION4: Tuple[Tuple[int, ...], ...] = ((0, 0, 0, 0), (1, 1, 1, 1))

#: ``key -> (block kind, block length, scale exponent, minimum norm,
#: kissing number, covolume log2)``.  ``even`` blocks are ``D_n``; ``code``
#: blocks are Construction A over the named small code.
CANDIDATES: Dict[str, Dict[str, object]] = {
    "D12^2": {"block": "even", "length": 12, "exponent": 0, "norm": 2,
              "kissing": 528, "covolume_log2": 2},
    "D8^3": {"block": "even", "length": 8, "exponent": 0, "norm": 2,
             "kissing": 336, "covolume_log2": 3},
    "D4^6": {"block": "even", "length": 4, "exponent": 0, "norm": 2,
             "kissing": 144, "covolume_log2": 6},
    "8E8^3": {"block": "hamming", "length": 8, "exponent": 3, "norm": 256,
              "kissing": 720, "covolume_log2": 84},
    "8D4^6": {"block": "repetition", "length": 4, "exponent": 3,
              "norm": 256, "kissing": 144, "covolume_log2": 90},
}

#: The declared order: norm 2 first, then norm 256, densest first at each.
CANDIDATE_ORDER: Tuple[Tuple[int, Tuple[str, ...]], ...] = (
    (2, ("D12^2", "D8^3", "D4^6")),
    (256, ("8E8^3", "8D4^6")),
)

#: The repaired ladder of :mod:`norm_escalation`, coarsest first.
REPAIRED: Tuple[str, ...] = ("8C", "8A", "4C", "2C", "2A", "C", "A", "2D",
                             "A/2", "Z")


def _code(spec: Dict[str, object]) -> Tuple[Tuple[int, ...], ...]:
    return HAMMING8 if spec["block"] == "hamming" else REPETITION4


def _round(value: Fraction, parity: int) -> int:
    """The nearest integer of the given parity; ties to the smaller."""
    shifted = (value - parity) / 2
    base, _cost, _alt = LE._round_nearest(shifted)
    return 2 * base + parity


def _decode_even_block(values: Sequence[Fraction]) -> Tuple[List[int], Fraction]:
    """Nearest point of ``D_n`` (Conway--Sloane): round, and if the sum is
    odd move the worst-rounded coordinate the other way."""
    rounded = [LE._round_nearest(v) for v in values]
    point = [r[0] for r in rounded]
    cost = sum((r[1] for r in rounded), Fraction(0))
    if sum(point) % 2:
        penalty, index = min((r[2], i) for i, r in enumerate(rounded))
        base = point[index]
        up = (values[index] - (base + 1)) ** 2
        down = (values[index] - (base - 1)) ** 2
        point[index] = base + 1 if up <= down else base - 1
        cost += penalty
    return point, cost


def _decode_code_block(values: Sequence[Fraction],
                       code: Sequence[Sequence[int]]) -> Tuple[List[int], Fraction]:
    """Nearest point of Construction A over a small code: try every codeword."""
    best: Optional[Tuple[Fraction, List[int]]] = None
    for word in code:
        point = [_round(v, p) for v, p in zip(values, word)]
        cost = sum(((v - x) ** 2 for v, x in zip(values, point)), Fraction(0))
        if best is None or cost < best[0]:
            best = (cost, point)
    assert best is not None
    return best[1], best[0]


def _quantise_new(values: Sequence[Fraction], key: str) -> Tuple[Point, Fraction]:
    spec = CANDIDATES[key]
    factor = Fraction(2) ** int(spec["exponent"])
    shrunk = [v / factor for v in values]
    length = int(spec["length"])
    point: List[int] = []
    cost = Fraction(0)
    for start in range(0, 24, length):
        block = shrunk[start:start + length]
        if spec["block"] == "even":
            p, c = _decode_even_block(block)
        else:
            p, c = _decode_code_block(block, _code(spec))
        point.extend(p)
        cost += c
    scaled = tuple(int(x * factor) for x in point)
    return scaled, cost * factor * factor


_CACHE: Dict[Tuple[Tuple[Fraction, ...], str], Point] = {}


def quantise(vector: Sequence, rung: str) -> Point:
    """The nearest point of ``rung``: a candidate here, else the family's."""
    values = tuple(Fraction(x) for x in vector)
    key = (values, rung)
    hit = _CACHE.get(key)
    if hit is not None:
        return hit
    if rung in CANDIDATES:
        point = _quantise_new(values, rung)[0]
    else:
        point = tuple(LE.quantise(values, rung).point)
    _CACHE[key] = point
    return point


def in_rung(vector: Sequence[int], key: str) -> bool:
    """Membership in a candidate rung, from its definition."""
    spec = CANDIDATES[key]
    factor = 1 << int(spec["exponent"])
    if any(int(x) % factor for x in vector):
        return False
    shrunk = [int(x) // factor for x in vector]
    length = int(spec["length"])
    for start in range(0, 24, length):
        block = shrunk[start:start + length]
        parity = tuple(x % 2 for x in block)
        if spec["block"] == "even":
            if sum(parity) % 2:
                return False
        elif parity not in set(_code(spec)):
            return False
    return True


def _norm(spec: Dict[str, object]) -> int:
    return int(spec["norm"])


def rung_norm(rung: str) -> int:
    """The minimum norm of any rung, candidate or family."""
    if rung in CANDIDATES:
        return _norm(CANDIDATES[rung])
    return CL.rung_spec(rung).minimum_norm


# ═════════════════════════════════════════════════════════════════════════
# 2.  C1 -- THE FACTS, ENUMERATED, AND THE QUANTISER, CHECKED
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=None)
def short_vectors(key: str) -> Dict[str, object]:
    """Minimum norm and kissing number of one block, by enumeration, and the
    whole rung's by the direct sum (blocks are orthogonal)."""
    spec = CANDIDATES[key]
    length = int(spec["length"])
    reach = 1 if spec["block"] == "even" else 2
    counts: Dict[int, int] = {}
    vectors: List[Tuple[int, ...]] = []
    for entries in product(range(-reach, reach + 1), repeat=length):
        if not any(entries):
            continue
        parity = tuple(x % 2 for x in entries)
        if spec["block"] == "even":
            ok = sum(parity) % 2 == 0
        else:
            ok = parity in set(_code(spec))
        if not ok:
            continue
        n = sum(x * x for x in entries)
        counts[n] = counts.get(n, 0) + 1
        vectors.append(entries)
    minimum = min(counts)
    blocks = 24 // length
    scale = 4 ** int(spec["exponent"])
    shortest = [v for v in vectors if sum(x * x for x in v) == minimum]
    return {"key": key, "block_minimum": minimum,
            "block_kissing": counts[minimum],
            "minimum_norm": minimum * scale,
            "kissing": counts[minimum] * blocks,
            "blocks": blocks, "block_shortest": tuple(shortest),
            "agrees": (minimum * scale == _norm(spec)
                       and counts[minimum] * blocks == int(spec["kissing"]))}


def _minimal_steps(key: str) -> Tuple[Point, ...]:
    """Every minimal vector of the whole rung (block shortest, placed)."""
    facts = short_vectors(key)
    spec = CANDIDATES[key]
    length = int(spec["length"])
    factor = 1 << int(spec["exponent"])
    out: List[Point] = []
    for block in range(int(facts["blocks"])):
        for v in facts["block_shortest"]:
            full = [0] * 24
            for i, x in enumerate(v):
                full[block * length + i] = x * factor
            out.append(tuple(full))
    return tuple(out)


def quantiser_check(key: str, vectors: int = 200, seed: int = 20260902
                    ) -> Dict[str, object]:
    """C1: on declared test vectors the answer is in the rung, and no
    minimal-vector step from it is nearer."""
    spec = CANDIDATES[key]
    factor = 1 << int(spec["exponent"])
    sweep = _Sweep(seed)
    steps = _minimal_steps(key)
    failures = 0
    for _ in range(vectors):
        x = [Fraction(sweep.below(8001) - 4000, 1000) * factor
             for _ in range(24)]
        p = quantise(x, key)
        here = sum(((a - b) ** 2 for a, b in zip(x, p)), Fraction(0))
        member = in_rung(p, key)
        nearer = any(sum(((a - b - s) ** 2 for a, b, s in zip(x, p, step)),
                         Fraction(0)) < here for step in steps)
        if not member or nearer:
            failures += 1
    return {"key": key, "vectors": vectors, "failures": failures,
            "holds": failures == 0}


def candidate_facts() -> Tuple[Dict[str, object], ...]:
    """C1 for every candidate."""
    rows = []
    for key in CANDIDATES:
        facts = short_vectors(key)
        check = quantiser_check(key)
        rows.append({"key": key, "norm": facts["minimum_norm"],
                     "kissing": facts["kissing"],
                     "declared_norm": _norm(CANDIDATES[key]),
                     "declared_kissing": int(CANDIDATES[key]["kissing"]),
                     "agrees": bool(facts["agrees"]),
                     "quantiser_failures": check["failures"],
                     "holds": bool(facts["agrees"]) and bool(check["holds"])})
    return tuple(rows)


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE ESCALATION OVER A LADDER WITH CANDIDATES IN IT
# ═════════════════════════════════════════════════════════════════════════

def _index(rung: str, carriers) -> Dict[Point, Tuple[int, ...]]:
    table: Dict[Point, List[int]] = {}
    for i, (_r, _n, carrier) in enumerate(carriers):
        table.setdefault(quantise(carrier, rung), []).append(i)
    return {p: tuple(m) for p, m in table.items()}


def _named(query, rung: str, indices) -> Optional[int]:
    members = indices[rung].get(quantise(query, rung), ())
    return members[0] if len(members) == 1 else None


def _queries(carriers) -> List[Tuple[int, Tuple[Fraction, ...]]]:
    out = []
    for _label, support, magnitude in LE.PERTURBATIONS:
        for i, (_r, _n, carrier) in enumerate(carriers):
            out.append((i, LE.perturb(carrier, i, support, magnitude)))
    return out


def audit(ladder: Sequence[str], carriers=None) -> Tuple[Dict[str, object], ...]:
    """:func:`norm_escalation.rung_audit`, for a ladder that may hold
    candidates: per rung, correct, wrong, refused, unique and disputed."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    ladder = tuple(ladder)
    indices = {rung: _index(rung, carriers) for rung in ladder}
    rows = {rung: {"correct": 0, "wrong": 0, "refused": 0,
                   "unique_correct": 0, "disagrees": 0} for rung in ladder}
    for truth, query in _queries(carriers):
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


def run_ladder(ladder: Sequence[str], carriers=None) -> Dict[str, object]:
    """Correct, wrong and refused in each of the three visiting orders, the
    oracle, and the disagreements -- what C3 asks of the filled ladder."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    ladder = tuple(ladder)
    indices = {rung: _index(rung, carriers) for rung in ladder}
    orders = {"middle_out": CL.middle_out_order(ladder),
              "coarse_to_fine": ladder,
              "fine_to_coarse": tuple(reversed(ladder))}
    totals = {name: {"correct": 0, "wrong": 0, "refused": 0}
              for name in orders}
    oracle = 0
    disagree = 0
    for truth, query in _queries(carriers):
        named = {rung: _named(query, rung, indices) for rung in ladder}
        oracle += int(any(a == truth for a in named.values()))
        disagree += int(len({a for a in named.values() if a is not None}) > 1)
        for name, order in orders.items():
            answer = next((named[r] for r in order if named[r] is not None),
                          None)
            key = ("refused" if answer is None
                   else "correct" if answer == truth else "wrong")
            totals[name][key] += 1
    correct = {t["correct"] for t in totals.values()}
    wrong = {t["wrong"] for t in totals.values()}
    return {"ladder": ladder, "norms": tuple(rung_norm(r) for r in ladder),
            "totals": totals, "oracle": oracle, "rungs_disagree": disagree,
            "order_independent": len(correct) == 1 and len(wrong) == 1,
            "correct": max(correct), "wrong": max(wrong),
            "refused": max(t["refused"] for t in totals.values()),
            "safe": max(wrong) == 0,
            "matches_oracle": totals["middle_out"]["correct"] == oracle}


def _insert(ladder: Sequence[str], rung: str) -> Tuple[str, ...]:
    """``rung`` placed in a coarsest-first ladder by its minimum norm."""
    norm = rung_norm(rung)
    out = [r for r in ladder if rung_norm(r) > norm] + [rung] + \
        [r for r in ladder if rung_norm(r) < norm]
    return tuple(out)


def fill(carriers=None) -> Dict[str, object]:
    """The declared filling rule, norm 2 then norm 256, densest first."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    ladder = REPAIRED
    trials: List[Dict[str, object]] = []
    filled: Dict[int, Optional[str]] = {}
    for norm, keys in CANDIDATE_ORDER:
        filled[norm] = None
        for key in keys:
            trial = _insert(ladder, key)
            rows = audit(trial, carriers)
            verdict = NE.retirement(rows)
            kept = not verdict["any_retired"]
            trials.append({"norm": norm, "candidate": key, "ladder": trial,
                           "audit": rows, "retired": verdict["retired"],
                           "kept": kept})
            if kept:
                filled[norm] = key
                ladder = trial
                break
    return {"trials": tuple(trials), "filled": filled, "ladder": ladder,
            "both_filled": all(v is not None for v in filled.values())}


def empty_rungs_report(carriers=None) -> Dict[str, object]:
    """C1, the reproduction of the repaired ladder, the filling and C3."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    facts = candidate_facts()
    repaired = run_ladder(REPAIRED, carriers)
    filling = fill(carriers)
    final = run_ladder(filling["ladder"], carriers)
    reproduces = (repaired["correct"] == 467 and repaired["wrong"] == 0
                  and repaired["refused"] == 101)
    return {
        "facts": facts, "repaired": repaired, "reproduces": reproduces,
        "filling": filling, "final": final,
        "marks": {
            "C1": all(row["holds"] for row in facts),
            "C2": bool(filling["both_filled"]),
            "C3": (final["safe"] and final["order_independent"]
                   and final["matches_oracle"]
                   and final["correct"] >= repaired["correct"]),
        },
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "empty_rungs.json")

_SOURCES: Tuple[str, ...] = ("reasoning/empty_rungs.py",) + tuple(
    NE._SOURCES)


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
    """The whole of part C, recomputed."""
    report = empty_rungs_report()
    for row in report["facts"]:
        row.pop("block_shortest", None)
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
