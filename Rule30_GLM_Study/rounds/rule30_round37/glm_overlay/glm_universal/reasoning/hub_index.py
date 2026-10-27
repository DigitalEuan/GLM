"""``glm_universal.reasoning.hub_index`` -- Round 37 of the Rule 30 study (To Do 41): the GLM
indexes the half-line family by **hubs**.

Why
---
Round 36 proved in Lean (``DriveWheel.lean``) that the periodic drives of the half-line machine form
a wheel: reading the same column from a later phase is a *turn*; a word that repeats after
``g | p`` steps *is* a word of period ``g``; every non-white word of period ``p`` is a turn of a
**hub** (``WheelRep q j``: primitive least turn, a Lyndon word) of a period ``q | p``
(``exists_wheelRep``), and ``HalfLineDies p`` holds iff the hubs of the divisors of ``p`` kill every
half-line (``halfLineDies_iff_wheel``).  Round 37 proved the exact price of a turn
(``TurnCost.lean``): starting the clock ``m`` steps later costs ``m + (tests skipped)``
(``testSlack_of_shift_count``), between phases ``a`` and ``b`` (``a + m = b mod p``)

    slack(a) <= slack(b) + m + testsBefore(phase a, m)        (testSlack_phase_transfer)

and a slack at *one* phase of every wheel gives the per-period law (``testCountLinear_of_phases``).

So the unit of work is a **spoke ``(q, hub)``**: one proof or certificate per hub fills in every
phase of its wheel and every multiple period.  This module

* maps any word ``(p, k)`` to its hub ``(q, j)`` and phase ``s`` exactly as ``exists_wheelRep``
  does (``to_hub``; ``driveN q j t = driveN p k (t + s)`` for all ``t``);
* lists the hubs of a period (``hubs``) and computes the exact turn cost (``turn_cost``);
* reads the hub table ``_data/r37_hubs.json`` (Lean-certified slack on ``d <= 24`` from
  ``DriveWheelData.wheelTable``; measured per-phase slacks from ``rule30_round37/wheel_phases37.py``,
  EMP) and answers ``tool hub P K`` and ``tool hubs P`` in three columns.

Exact integer arithmetic only.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
HUBS37 = os.path.join(_HERE, "_data", "r37_hubs.json")


def drive(p: int, k: int, t: int) -> int:
    """``driveN p k t = k.testBit (t % p)``."""
    return (k >> (t % p)) & 1


def turn(p: int, k: int, s: int) -> int:
    """``wheelTurn p k s``: bit ``i`` of the turned word is bit ``(i + s) mod p`` of ``k``."""
    return sum(((k >> ((i + s) % p)) & 1) << i for i in range(p))


def is_hub(p: int, k: int) -> bool:
    """``WheelRep p k``: non-white, least of its turns, and no proper turn returns it."""
    if p < 1 or not (0 < k < 2 ** p):
        return False
    ts = [turn(p, k, s) for s in range(p)]
    return all(k <= t for t in ts) and all(ts[s] != k for s in range(1, p))


def hubs(p: int) -> List[int]:
    return [k for k in range(1, 2 ** p) if is_hub(p, k)]


def primitive_period(p: int, k: int) -> int:
    """The least ``q | p`` with ``drive(t + q) = drive(t)`` for all ``t``."""
    for q in range(1, p + 1):
        if p % q == 0 and all(drive(p, k, t + q) == drive(p, k, t) for t in range(p)):
            return q
    return p


def to_hub(p: int, k: int) -> Tuple[int, int, int]:
    """``(q, j, s)`` with ``q | p``, ``WheelRep q j`` and ``driveN q j t = driveN p k (t + s)``
    (the statement of ``exists_wheelRep``).  Requires ``0 < k < 2^p``."""
    if not (0 < k < 2 ** p):
        raise ValueError("the word must be non-white and have p bits")
    q = primitive_period(p, k)
    w = k & (2 ** q - 1)
    best = min(range(q), key=lambda s: (turn(q, w, s), s))
    return q, turn(q, w, best), best


def tests_before(p: int, k: int, m: int) -> int:
    return sum(drive(p, k, t) for t in range(m))


def turn_cost(p: int, k: int, a: int, b: int) -> int:
    """Exact cost of reading phase ``a`` of the wheel of ``k`` from phase ``b``
    (``testSlack_phase_transfer``): ``m + testsBefore(phase a, m)``, ``m = (b - a) mod p``."""
    m = (b - a) % p
    return m + tests_before(p, turn(p, k, a), m)


def divisors(p: int) -> List[int]:
    return [q for q in range(1, p + 1) if p % q == 0]


def word_str(p: int, k: int) -> str:
    """Time 0 first."""
    return "".join(str((k >> i) & 1) for i in range(p))


def load_table() -> Dict[str, dict]:
    try:
        return json.load(open(HUBS37))["hubs"]
    except (OSError, ValueError, KeyError):
        return {}


def hub_record(q: int, j: int) -> Optional[dict]:
    return load_table().get(f"{q},{j}")


def _status_lines(q: int, j: int) -> List[str]:
    rec = hub_record(q, j)
    out = []
    if q == 1:
        out.append("    status: PROVED for every d (period 1: halfLineDies_one; slack 2, "
                   "testCountLinear_one)")
    else:
        out.append(f"    status: OPEN for all d (WordDies (driveN {q} {j}) is the spoke to prove)")
    if rec:
        if rec.get("cert_slack") is not None:
            out.append(f"    CERT: every code of length d <= {rec['cert_range']} fails within d + "
                       f"{rec['cert_slack']} tests of the hub [{rec['cert_lean']}]")
        ps = rec.get("phase_slacks")
        if ps:
            b = rec["best_phase"]
            out.append(f"    EMP (exact search, d <= {rec['emp_range']}): slack per phase "
                       f"{ps}; best phase {b} (word {word_str(q, turn(q, j, b))}) needs "
                       f"{ps[b]}, worst {max(ps)}")
            pred = [ps[b] + (turn_cost(q, j, a, b) if a != b else 0) for a in range(q)]
            out.append(f"    proved turn cost from the best phase gives at most {pred} "
                       f"(testSlack_phase_transfer); attained at "
                       f"{sum(1 for a in range(q) if pred[a] == ps[a])} of {q} phases")
        for extra in rec.get("lean_extra", []):
            out.append(f"    Lean: {extra}")
    return out


def hub_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool hub P K``: the hub of the word ``K`` of period ``P`` and what one proof there fills."""
    parts = (arg or "").split()
    if len(parts) != 2 or not all(x.isdigit() for x in parts):
        return False, "refused: tool hub P K  (period P >= 1, word 0 < K < 2^P, time 0 = bit 0)", {
            "status": "unread"}
    p, k = int(parts[0]), int(parts[1])
    if p < 1 or p > 24 or not (0 < k < 2 ** p):
        return False, (f"refused: the word must be non-white with {p} bits (0 < K < 2^{p}); "
                       f"the white word has no hub and dies by halfLineDies_iff"), {
            "status": "white"}
    q, j, s = to_hub(p, k)
    orbit = sorted({turn(q, j, a) for a in range(q)})
    mults = [m for m in range(q, 13) if m % q == 0]
    lines = [f"HUB  word {word_str(p, k)} (period {p}, K = {k}) is phase {(-s) % q} of period {q} hub {j} "
             f"(word {word_str(q, j)})",
             "  COLUMN 1 — LANGUAGE",
             f"    The drive of K started {s} steps later is the hub's drive (the same column, "
             f"read from another phase)" + (f", and it already repeats after {q} "
                                                       f"steps" if q < p else "") + ".",
             f"    One proof for this hub fills its whole wheel ({q} phases: words "
             f"{', '.join(word_str(q, w) for w in orbit)}) and the same words written out for "
             f"every multiple period ({', '.join(map(str, mults))}, ...).",
             "  COLUMN 2 — MATHEMATICS",
             f"    driveN {q} {j} t = driveN {p} {k} (t + {s}) for all t  [exists_wheelRep, "
             f"driveN_wheelTurn, driveN_eq_of_period]",
             f"    WordDies (driveN {p} {k}) <-> WordDies (driveN {q} {j})  "
             f"[wordDies_wheelTurn_iff, wordDies_shift_iff_of_periodic]",
             f"    HalfLineDies {p} <-> every hub of every divisor of {p} kills  "
             f"[halfLineDies_iff_wheel]; hubs needed: "
             f"{sum(len(hubs(d)) for d in divisors(p))} (not {2 ** p - 1} words)"]
    lines += _status_lines(q, j)
    lines += ["  COLUMN 3 — SCRIPT",
              f"    gcc -O2 -o test_slack34 rule30_round34/test_slack34.c && "
              f"./test_slack34 {q} {j} 1 28     # the hub's exact excess",
              f"    python3 rule30_round37/wheel_phases37.py {q} 28   # every phase of every wheel "
              f"up to period {q}"]
    return True, "\n".join(lines), {"status": "hub", "q": q, "hub": j, "phase": s}


def hubs_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool hubs P``: the hubs of period ``P`` (and the count against words)."""
    a = (arg or "").strip()
    if not a.isdigit() or not (1 <= int(a) <= 16):
        return False, "refused: tool hubs P  (1 <= P <= 16)", {"status": "unread"}
    p = int(a)
    hs = hubs(p)
    need = sum(len(hubs(d)) for d in divisors(p))
    lines = [f"HUBS  period {p}: {len(hs)} hubs (primitive least turns, Lyndon words; "
             f"DriveWheelData.wheelReps_count for p <= 12)",
             f"  HalfLineDies {p} needs the {need} hubs of the divisors {divisors(p)}, "
             f"not the {2 ** p - 1} non-white words  [halfLineDies_iff_wheel]"]
    for j in hs[:40]:
        rec = hub_record(p, j) or {}
        cs = rec.get("cert_slack")
        ps = rec.get("phase_slacks")
        bits = [f"  hub {j} [{word_str(p, j)}]"]
        if cs is not None:
            bits.append(f"CERT slack {cs} on d <= {rec['cert_range']}")
        if ps:
            bits.append(f"EMP best phase {rec['best_phase']} slack {min(ps)}, worst {max(ps)} "
                        f"(d <= {rec['emp_range']})")
        lines.append("; ".join(bits))
    if len(hs) > 40:
        lines.append(f"  ... {len(hs) - 40} more")
    return True, "\n".join(lines), {"status": "hubs", "count": len(hs), "needed": need}
