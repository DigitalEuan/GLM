"""``glm_universal.reasoning.confidence_floor_marks`` -- the floor, hunted and measured.

``studies/CONFIDENCE_FLOOR_STUDY.md`` (Phase 80) declared the marks F1-F7
before :mod:`glm_universal.reasoning.confidence_floor` existed;
:func:`confidence_floor_report` measures every one of them.  Kept apart from
the runtime module so that a unit that answers a query does not depend on the
study's documents.

The channel census
------------------
Every probability here is exact: a sum over every received word, not a sample.
The truth is drawn uniformly from the reading's allowed candidates and each of
its 24 bits flips independently at the true rate ``p = a/b``.  A received word
at distance ``d`` from a candidate has likelihood ``a^d (b-a)^(24-d) / b^24``,
so every probability is an integer over ``k * b^24`` (``k`` candidates).

* **The decoder** (all 4096 codewords).  By linearity the truth can be taken
  to be the zero word.  A read at coset weight ``d <= 3`` is answered and is
  right exactly when the error was the coset leader, so
  ``P(right, weight d) = C(24, d) p^d q^(24-d)`` and
  ``P(answered, weight d) = C(24, d) * sum_w A_w(d) p^w q^(24-w)`` over the
  coset weight enumerator ``A(d)``; every such read has the same confidence
  (the absorbed law).  A read at coset weight 4 is the refused tie; its
  probability is taken by a separate route -- 1,771 cosets, each weighed by an
  enumerator counted directly from one deep hole -- and the three must sum to
  one (mark F1).
* **The context stage** over a case set ``S`` of ``k`` codewords.  A read
  ``r`` is resolved to case ``v`` exactly when ``v`` is the only case at the
  read's coset weight; every such read is ``v + e`` with ``wt(e) <= 4`` (the
  covering radius), and arises from ``v`` alone.  So enumerating
  ``v + e`` over the cases and the 12,951 errors of weight at most four visits
  every resolved read once.  The census keeps, per resolved read, its distance
  to the survivor and the sorted distances to every other case -- which is all
  that its probability and its confidence depend on.

Exactness: ``int`` masks, ``int`` weights and :class:`fractions.Fraction`
only.  No float, no RNG.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from math import comb
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.mog import GOLAY_MASKS
from . import carried_fork as cf
from . import law_absorption as la
from .confidence_floor import ConfidenceRefusal, graded_resolve
from .decoder_confidence import (N, brute_posterior, decode_confidence,
                                 int_weights)

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "HUNT_RATES", "THRESHOLDS", "CASE_SIZES",
    "LEAST_RETENTION", "DECLARED_PROGRAMS", "context_census",
    "decoder_census", "cell", "hunt", "f1_census", "f2_promise", "f3_hunt",
    "f4_declared_rate", "f5_runtime", "f6_unchanged", "per_reading_working",
    "confidence_floor_report",
]

LEAN_FILE = "RequestProject/GLM/ConfidenceFloor.lean"

#: The theorems of ``RequestProject/GLM/ConfidenceFloor.lean`` (mark F7).
LEAN_THEOREMS: Tuple[str, ...] = (
    "floor_error_le", "floor_retention_antitone", "posterior_antitone_rate",
    "floor_safe_overdeclared",
)

#: The declared grid of the hunt.
HUNT_RATES: Tuple[Fraction, ...] = (
    Fraction(1, 1000), Fraction(1, 100), Fraction(1, 50), Fraction(1, 20),
    Fraction(1, 10))
THRESHOLDS: Tuple[Fraction, ...] = (
    Fraction(9, 10), Fraction(19, 20), Fraction(49, 50), Fraction(99, 100),
    Fraction(199, 200), Fraction(999, 1000), Fraction(9999, 10000))
#: K1's case sets.
CASE_SIZES: Tuple[int, ...] = (2, 4, 8, 16, 32)
#: What *working* asks a floor to keep of the unfloored right answers.
LEAST_RETENTION = Fraction(9, 10)
#: The owner's two candidates.
OWNER_CANDIDATES: Tuple[Fraction, ...] = (Fraction(99, 100),
                                          Fraction(999, 1000))


# ===========================================================================
# 1.  THE CENSUS
# ===========================================================================

@lru_cache(maxsize=None)
def _errors_up_to_four() -> Tuple[Tuple[int, int], ...]:
    out: List[Tuple[int, int]] = []
    for w in range(5):
        for s in combinations(range(N), w):
            out.append((sum(1 << i for i in s), w))
    return tuple(out)


@lru_cache(maxsize=None)
def context_census(k: int) -> Tuple[Tuple[Tuple[int, Tuple[int, ...]], int],
                                    ...]:
    """The resolved reads of the context stage over ``S_k``: each distinct
    ``(distance to the survivor, sorted distances to the other cases)`` with
    how many reads have it.  Every resolved read is counted once."""
    cases = cf.case_set(k)
    census: Dict[Tuple[int, Tuple[int, ...]], int] = {}
    for v in cases:
        others = [s for s in cases if s != v]
        for e, w in _errors_up_to_four():
            r = v ^ e
            ds = sorted((r ^ s).bit_count() for s in others)
            if ds and ds[0] <= w:
                continue            # another case is as near: not resolved
            key = (w, tuple(ds))
            census[key] = census.get(key, 0) + 1
    return tuple(sorted(census.items()))


def _deep_hole_enumerator() -> Tuple[int, ...]:
    """The weight enumerator of one deep-hole coset, counted directly over
    the 4096 codewords (the separate route of F1)."""
    hole = 0b1111
    enum = [0] * (N + 1)
    for c in GOLAY_MASKS:
        enum[(hole ^ c).bit_count()] += 1
    return tuple(enum)


def decoder_census() -> Tuple[Tuple[int, int, Tuple[int, ...]], ...]:
    """``(coset weight d, cosets of weight d, coset enumerator)`` for the
    answered weights ``d <= 3``."""
    return tuple((d, comb(N, d), la.coset_enumerator(d)) for d in range(4))


def _mass(enum: Sequence[int], weights: Sequence[int]) -> int:
    return sum(a * weights[w] for w, a in enumerate(enum) if a)


@lru_cache(maxsize=None)
def _groups(reading: str, declared: Fraction, true: Fraction
            ) -> Tuple[Tuple[Fraction, int, int], ...]:
    """Per census group: ``(confidence at the declared rate, right mass,
    wrong mass)`` at the true rate, masses as integers over the reading's
    denominator (see :func:`_denominator`)."""
    wd, wt = int_weights(declared), int_weights(true)
    out: List[Tuple[Fraction, int, int]] = []
    if reading == "decoder":
        for d, cosets, enum in decoder_census():
            conf = la.confidence(d, declared)
            right = cosets * wt[d]
            answered = cosets * _mass(enum, wt)
            out.append((conf, right, answered - right))
        return tuple(out)
    k = int(reading.split("_")[1])
    for (m, others), n in context_census(k):
        conf = Fraction(wd[m], wd[m] + sum(wd[d] for d in others))
        out.append((conf, n * wt[m], n * sum(wt[d] for d in others)))
    return tuple(out)


def _denominator(reading: str, true: Fraction) -> int:
    b = true.denominator
    if reading == "decoder":
        return b ** N
    return int(reading.split("_")[1]) * b ** N


READINGS: Tuple[str, ...] = ("decoder",) + tuple(f"S_{k}" for k in CASE_SIZES)


def cell(reading: str, declared: Fraction, t: Optional[Fraction],
         true: Optional[Fraction] = None) -> Dict[str, object]:
    """The exact channel measure of one reading at one floor.

    ``t=None`` is the unfloored reading.  ``true`` is the rate the reads are
    drawn at (the declared rate unless given)."""
    true = declared if true is None else true
    den = _denominator(reading, true)
    groups = _groups(reading, declared, true)
    right0 = sum(g[1] for g in groups)
    wrong0 = sum(g[2] for g in groups)
    kept = [g for g in groups if t is None or g[0] >= t]
    right = sum(g[1] for g in kept)
    wrong = sum(g[2] for g in kept)
    answered = right + wrong
    return {
        "reading": reading, "declared": declared, "true": true, "floor": t,
        "p_right": Fraction(right, den), "p_wrong": Fraction(wrong, den),
        "p_answered": Fraction(answered, den),
        "p_right_unfloored": Fraction(right0, den),
        "p_wrong_unfloored": Fraction(wrong0, den),
        "residual": Fraction(wrong, answered) if answered else Fraction(0),
        "retention": Fraction(right, right0) if right0 else Fraction(1),
        "wrong_removed": (Fraction(wrong0 - wrong, wrong0) if wrong0
                          else Fraction(1)),
        "least_confidence": min((g[0] for g in groups), default=None),
    }


def hunt(true_factor: Fraction = Fraction(1)) -> Dict[str, object]:
    """Every (rate, threshold) cell over the six readings: whether the
    threshold *works* there (the promise and the cost), with the least
    retention and the greatest residual error.  ``true_factor`` scales the
    true rate against the declared one (2 for the robustness read)."""
    rows = []
    for p in HUNT_RATES:
        for t in THRESHOLDS:
            cells = [cell(r, p, t, p * true_factor) for r in READINGS]
            promise = all(c["residual"] <= 1 - t for c in cells)
            cost = all(c["retention"] >= LEAST_RETENTION for c in cells)
            worst = min(cells, key=lambda c: c["retention"])
            rows.append({
                "rate": p, "floor": t, "promise": promise, "cost": cost,
                "works": promise and cost,
                "least_retention": worst["retention"],
                "least_retention_reading": worst["reading"],
                "greatest_residual": max(c["residual"] for c in cells),
                "cells": cells})
    working: Dict[Fraction, Optional[Fraction]] = {}
    for p in HUNT_RATES:
        ok = [r["floor"] for r in rows if r["rate"] == p and r["works"]]
        working[p] = max(ok) if ok else None
    return {"rows": rows, "working": working, "true_factor": true_factor}


# ===========================================================================
# 2.  THE MARKS
# ===========================================================================

def f1_census(brute_stride: int = 211) -> Dict[str, object]:
    """F1: the census is right."""
    #  (i) the decoder: right + wrong + refused = 1, refused by its own route
    hole = _deep_hole_enumerator()
    decoder_rows = []
    decoder_ok = True
    for p in HUNT_RATES:
        c = cell("decoder", p, None)
        refused = Fraction(1771 * _mass(hole, int_weights(p)),
                           p.denominator ** N)
        total = c["p_right"] + c["p_wrong"] + refused
        decoder_rows.append({"rate": p, "p_right": c["p_right"],
                             "p_wrong": c["p_wrong"], "p_refused": refused,
                             "sum": total})
        decoder_ok = decoder_ok and total == 1
    #  (ii) the context stage: K1's resolved weight-4 reads, per case set
    k1 = cf.k1_context(CASE_SIZES)
    k1_by_k = {r["k"]: r["answered"] for r in k1["rows"]}
    census_by_k = {k: sum(n for (m, _), n in context_census(k) if m == 4)
                   for k in CASE_SIZES}
    #  ... and on a stride of resolved reads, the census's confidence against
    #  the runtime and a brute-force Fraction sum
    checked = disagreements = 0
    p = Fraction(1, 20)
    wd = int_weights(p)
    for k in CASE_SIZES:
        cases = cf.case_set(k)
        n = 0
        for v in cases:
            others = [s for s in cases if s != v]
            for e, w in _errors_up_to_four():
                r = v ^ e
                ds = sorted((r ^ s).bit_count() for s in others)
                if ds and ds[0] <= w:
                    continue
                n += 1
                if n % brute_stride:
                    continue
                checked += 1
                conf = Fraction(wd[w], wd[w] + sum(wd[d] for d in ds))
                runtime = decode_confidence(r, p, cases)
                brute = brute_posterior((r,), v, cases, p)
                disagreements += not (runtime["value"] == v
                                      and runtime["confidence"] == conf
                                      == brute)
    context_ok = (census_by_k == k1_by_k and disagreements == 0
                  and checked > 0)
    return {"decoder": decoder_rows, "k1_resolved": k1_by_k,
            "census_resolved": census_by_k,
            "k1_total": sum(k1_by_k.values()),
            "census_total": sum(census_by_k.values()),
            "checked": checked, "disagreements": disagreements,
            "passed": decoder_ok and context_ok}


def f2_promise(h: Dict[str, object]) -> Dict[str, object]:
    """F2: ``P(wrong | answered) <= 1 - t`` in every cell of the grid."""
    cells = [c for row in h["rows"] for c in row["cells"]]
    broken = [c for c in cells if c["residual"] > 1 - c["floor"]]
    return {"cells": len(cells), "broken": len(broken),
            "passed": not broken and len(cells) == (
                len(READINGS) * len(HUNT_RATES) * len(THRESHOLDS))}


def f3_hunt(h: Dict[str, object]) -> Dict[str, object]:
    """F3: every cell classified, the working threshold named per rate, and
    the classification monotone in the floor and in the rate."""
    works = {(r["rate"], r["floor"]): r["works"] for r in h["rows"]}
    mono_floor = all(
        works[(p, t2)] for (p, t), ok in works.items() if ok
        for t2 in THRESHOLDS if t2 < t)
    mono_rate = all(
        works[(p2, t)] for (p, t), ok in works.items() if ok
        for p2 in HUNT_RATES if p2 < p)
    owner = {str(t): [str(p) for p in HUNT_RATES if works[(p, t)]]
             for t in OWNER_CANDIDATES}
    recommended = {}
    for p in HUNT_RATES:
        w = h["working"][p]
        recommended[str(p)] = (f"floor {w}" if w is not None
                               and w >= Fraction(99, 100) else "graded")
    table = [{"rate": r["rate"], "floor": r["floor"], "works": r["works"],
              "promise": r["promise"], "cost": r["cost"],
              "least_retention": r["least_retention"],
              "least_retention_reading": r["least_retention_reading"],
              "greatest_residual": r["greatest_residual"]}
             for r in h["rows"]]
    falls = [h["working"][p] for p in HUNT_RATES]
    expectation = all(
        (b is None) or (a is not None and a >= b)
        for a, b in zip(falls, falls[1:]))
    return {"table": table, "classified": len(table),
            "working": {str(p): (str(w) if w is not None else None)
                        for p, w in h["working"].items()},
            "owner_candidates_work_at": owner,
            "recommended": recommended,
            "monotone_in_floor": mono_floor, "monotone_in_rate": mono_rate,
            "expectation_falls_with_rate": expectation,
            "passed": (len(table) == len(HUNT_RATES) * len(THRESHOLDS)
                       and mono_floor and mono_rate)}


def f4_declared_rate() -> Dict[str, object]:
    """F4: the promise with the rate overdeclared (reads at ``p/2``: the
    mark) and underdeclared (reads at ``2p``: reported)."""
    over = hunt(Fraction(1, 2))
    under = hunt(Fraction(2))
    over_broken = [(c["reading"], c["declared"], c["floor"], c["residual"])
                   for row in over["rows"] for c in row["cells"]
                   if c["residual"] > 1 - c["floor"]]
    under_broken = [{"reading": c["reading"], "declared": c["declared"],
                     "floor": c["floor"], "residual": c["residual"],
                     "promised": 1 - c["floor"]}
                    for row in under["rows"] for c in row["cells"]
                    if c["residual"] > 1 - c["floor"]]
    robust = {str(p): [str(r["floor"]) for r in under["rows"]
                       if r["rate"] == p and r["promise"]]
              for p in HUNT_RATES}
    cells = len(READINGS) * len(HUNT_RATES) * len(THRESHOLDS)
    return {"cells": cells, "overdeclared_broken": len(over_broken),
            "underdeclared_broken": len(under_broken),
            "underdeclared_worst": max(
                under_broken, key=lambda b: b["residual"] / b["promised"],
                default=None),
            "underdeclared_rows": under_broken,
            "promise_holds_at_double_rate": robust,
            "passed": not over_broken}


#: The declared programs of F5: ``(source, "answer")`` or ``(source, NAME)``.
#: ``e1``/``e2``/``octad`` are an octad split in two tetrads (the K2 witness).
DECLARED_PROGRAMS: Tuple[Tuple[str, str], ...] = (
    ("resolve_at(Fraction(1, 100), golay_encode(1) ^ 0b1111, "
     "golay_encode(1), golay_encode(2))", "answer"),
    ("resolve_at(Fraction(1, 10), golay_encode(1) ^ 0b1111, "
     "golay_encode(1), golay_encode(2), golay_encode(3), golay_encode(4))",
     "answer"),
    ("resolve_at(Fraction(1, 10), golay_encode(1) ^ 0b111, "
     "golay_encode(1), golay_encode(2))", "answer"),
    ("resolve_at(Fraction(1, 100), golay_encode(1) ^ 0b1111, "
     "golay_encode(2), golay_encode(3))", "UNCORRECTABLE"),
    ("resolve_at(Fraction(1, 100), {e1}, 0, {octad})", "AMBIGUOUS"),
    ("resolve_at(Fraction(1, 2), golay_encode(1), golay_encode(1))",
     "RATE_OUT_OF_RANGE"),
    ("c = golay_encode(5)\n"
     "agree_at(Fraction(1, 100), c ^ 0b1111, c ^ 0b111000000000000000000001)",
     "answer"),
    ("agree_at(Fraction(1, 100), {e1}, {e2})", "AMBIGUOUS"),
    ("resolve_floor(Fraction(1, 100), Fraction(99, 100), "
     "golay_encode(1) ^ 0b1111, golay_encode(1), golay_encode(2))", "answer"),
    #  Declared BELOW_FLOOR, measured an answer: its one rival lies four
    #  further away, so a weight-3 read at 1/10 is 1/(1 + (1/9)^4) =
    #  6561/6562 sure, above 999/1000.  The
    #  declaration was wrong (it took the decoder's 78 % at weight 3 for the
    #  context stage's); recorded as missed, not re-read (study §2.5).
    ("resolve_floor(Fraction(1, 10), Fraction(999, 1000), "
     "golay_encode(1) ^ 0b111, golay_encode(1), golay_encode(2))",
     "BELOW_FLOOR"),
    ("resolve_floor(Fraction(1, 10), Fraction(9, 10), "
     "golay_encode(1) ^ 0b111, golay_encode(1), golay_encode(2))", "answer"),
    ("resolve_floor(Fraction(1, 100), 0, golay_encode(1), golay_encode(1))",
     "FLOOR_OUT_OF_RANGE"),
    ("resolve_floor(Fraction(1, 100), Fraction(3, 2), golay_encode(1), "
     "golay_encode(1))", "FLOOR_OUT_OF_RANGE"),
    ("c = golay_encode(9)\n"
     "agree_floor(Fraction(1, 20), Fraction(99, 100), c ^ 0b11, c ^ 0b1)",
     "answer"),
    ("c = golay_encode(9)\n"
     "agree_floor(Fraction(1, 10), Fraction(9999, 10000), c ^ 0b111)",
     "BELOW_FLOOR"),
    ("i, c = resolve_at(Fraction(1, 10), golay_encode(1) ^ 0b1111, "
     "golay_encode(1), golay_encode(2), golay_encode(3), golay_encode(4))\n"
     "c > Fraction(99, 100)", "answer"),
)


def _witness_masks() -> Dict[str, int]:
    octad = next(w for w in GOLAY_MASKS if w.bit_count() == 8)
    sup = [i for i in range(N) if (octad >> i) & 1]
    return {"octad": octad, "e1": sum(1 << i for i in sup[:4]),
            "e2": sum(1 << i for i in sup[4:])}


def f5_runtime() -> Dict[str, object]:
    """F5: the four builtins on the declared programs, each answer checked
    by its fresh-interpreter script."""
    from . import python_speech as sp
    masks = _witness_masks()
    rows = []
    for source, expected in DECLARED_PROGRAMS:
        src = source.format(**masks)
        payload = sp.speak(src)
        got = payload.refusal or "answer"
        verified = None
        if got == "answer":
            verified = bool(sp.verify_payload(payload)["verified"])
        rows.append({"source": src, "expected": expected, "got": got,
                     "value": payload.value, "verified": verified,
                     "as_declared": got == expected
                     and verified in (None, True)})
    wrong = sum(1 for r in rows if not r["as_declared"])
    return {"rows": rows, "programs": len(rows),
            "as_declared": len(rows) - wrong, "wrong": wrong,
            "passed": wrong == 0}


def f6_unchanged() -> Dict[str, object]:
    """F6: the graded and floored readings return what ``resolve``/``agree``
    return, and the carried fork's K1 and K2 figures stand."""
    from . import python_substrate as ps
    from .decoder_confidence_marks import CARRIED_FORK_FIGURES
    k1 = cf.k1_context(CASE_SIZES)
    k2 = cf.k2_second_reading()
    now = {"K1": (k1["reads"], k1["answered"], k1["wrong"]),
           "K2": (k2["double_reads"], k2["answered"], k2["wrong"])}
    same = checked = 0
    p = Fraction(1, 20)
    for k in (2, 32):
        cases = cf.case_set(k)
        for v in cases[:4]:
            for e in cf._weight4_errors()[::331]:
                checked += 1
                plain = ps.resolve(v ^ e, cases)
                try:
                    g = graded_resolve(v ^ e, p, cases)
                    same += (plain.verdict == "resolved"
                             and g["value"] == plain.value)
                except ConfidenceRefusal as r:
                    same += r.name == plain.verdict
    return {"figures": now, "stated": CARRIED_FORK_FIGURES,
            "checked": checked, "same": same,
            "passed": now == CARRIED_FORK_FIGURES and same == checked}


def per_reading_working() -> Dict[str, Dict[str, Optional[str]]]:
    """Not declared, so not a mark: the highest threshold of ``T`` that keeps
    the cost clause for each reading on its own, per rate (the promise holds
    in every cell, F2)."""
    out: Dict[str, Dict[str, Optional[str]]] = {}
    for r in READINGS:
        row: Dict[str, Optional[str]] = {}
        for p in HUNT_RATES:
            ok = [t for t in THRESHOLDS
                  if cell(r, p, t)["retention"] >= LEAST_RETENTION]
            row[str(p)] = str(max(ok)) if ok else None
        out[r] = row
    return out


def _lean_has(names: Sequence[str]) -> bool:
    """Whether the Lean file states every named theorem and holds no
    ``sorry`` (the build itself is the release's Lean instrument)."""
    import re
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "sorry" not in text and all(
        re.search(rf"\btheorem {n}\b", text) for n in names)


def confidence_floor_report() -> Dict[str, object]:
    """Every mark of the study, measured."""
    h = hunt()
    f1 = f1_census()
    f2 = f2_promise(h)
    f3 = f3_hunt(h)
    f4 = f4_declared_rate()
    f5 = f5_runtime()
    f6 = f6_unchanged()
    f7 = {"file": LEAN_FILE, "theorems": list(LEAN_THEOREMS),
          "passed": _lean_has(LEAN_THEOREMS)}
    unfloored = [{"reading": r, "rate": p,
                  **{k: v for k, v in cell(r, p, None).items()
                     if k in ("p_right", "p_wrong", "p_answered",
                              "residual", "least_confidence")}}
                 for r in READINGS for p in HUNT_RATES]
    marks = {"F1": f1["passed"], "F2": f2["passed"], "F3": f3["passed"],
             "F4": f4["passed"], "F5": f5["passed"], "F6": f6["passed"],
             "F7": f7["passed"]}
    return {"F1": f1, "F2": f2, "F3": f3, "F4": f4, "F5": f5, "F6": f6,
            "F7": f7, "unfloored": unfloored,
            "per_reading_working": per_reading_working(), "marks": marks,
            "met": sum(marks.values()), "of": len(marks)}
