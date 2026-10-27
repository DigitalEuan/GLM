#!/usr/bin/env python3
"""GLM Hypothesis Engine v18 -- self-contained.

One file, Python 3.8+ standard library only, exact integer / Fraction arithmetic only.  It does
not import any earlier engine (v4 ... v17), any guard module or any Lean file.  Everything the
engine needs is in this file:

  1. exact tools        Rule 30 rows, centre column, left / right diagonals and their eventual
                        periods, Berlekamp-Massey linear complexity, the Wobble D(N), block counts
  2. layers and arrow   every universal claim is READ at five nested scales (the five GLM layer
                        names are used as scale labels only).  The read trajectory is the claim's
                        ARROW: it only ever moves up, and it either converges (passes every read)
                        or flips at the first layer that refutes it
  3. hypotheses         claim classes decide what kind of evidence can settle a claim
                        (finite / Pi1 / Pi2 / implication / comparison / measurement / estimate /
                        analogy / proposal / meta / trend)
  4. ledger             the Lean-checked results the engine may cite, embedded as a table of
                        theorem names from the Lean package RequestProject/GLM (FORMAL / CERT).
                        Optionally the full evidence ledger claims.csv can be loaded
  5. gate cascade       class -> recompute -> escalate (with arrow) -> implication -> ledger,
                        then typed fixpoint rollback; only the ledger can say "proved"
  6. wheels             the GLM Wheel, made executable: the rings KNOWS / THINKS-TRUE /
                        DOESN'T-KNOW / NEEDS, the language wheel (vetted vocabulary), the needs
                        wheel (first sound provision that speaks wins), and the wheel TURN: load
                        a previous wheel (e.g. the owner's glm_wheel.json), re-gate every entry
                        and report which entries moved ring and why
  7. dialogue           speaks only claims with backing; a consistency check verifies this
  8. domains            Rule 30 (the engine proposes its own hypotheses by lifting from
                        development data), general reasoning (eight classic benchmarks with known
                        answers, plus any JSON file of claims), ARC-style grid puzzles (a program
                        search that answers only when every consistent program agrees, with a
                        needs diagnosis and a measured wheel turn)

Usage
    python3 hypothesis_engine.py                       # Rule 30 + general + ARC (synthetic), full
    python3 hypothesis_engine.py --quick               # smaller ranges (about 10 s)
    python3 hypothesis_engine.py rule30 [--no-ledger]  # one domain
    python3 hypothesis_engine.py general [--claims my_claims.json]
    python3 hypothesis_engine.py arc [--arc-zip ../glm_repo.zip] [--arc-dir DIR]
    python3 hypothesis_engine.py turn ../glm_wheel.json  # turn a previous wheel
    python3 hypothesis_engine.py --selftest
Outputs go to ./out (JSON for machines, Markdown for people, glm_wheel_v18.json for the next run).

What the engine guarantees, and what it does not
  * It never says "proved" without a Lean theorem name from the ledger.
  * A refutation is a concrete, recomputable counterexample (or a cited Lean refutation).
  * "survives-to N" means: no counterexample up to N.  It is NOT evidence of truth for a
    universal claim (Lean: GateLoop.finite_range_never_proves_forall,
    GateLoop.survives_as_proved_unsound; Benchmarks.gcd_trap_refuted is the classic example).
  * Pi2 claims ("infinitely many", "unbounded") are never decided by data
    (NeedsWheel.finite_data_never_forces_infinitely_many).
  * Analogies, proposals and meta-claims are kept on the wheel as UNTESTED with a stated need;
    they are never spoken as true.
  * All three Rule 30 prize problems are OPEN; the engine reports them as such.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ENGINE_VERSION = "v18"
HERE = Path(__file__).resolve().parent

# ═════════════════════════════════════════════════════════════════════════════════════════════
# 0. Vocabulary
# ═════════════════════════════════════════════════════════════════════════════════════════════

LAYERS = ("substrate", "integer", "rational", "griess", "universal")  # scale labels only

# statuses
PROVED = "proved"                       # Lean FORMAL / CERT, theorem name attached
VERIFIED = "verified-exact"             # finite claim: its whole finite range computed exactly
SURVIVES_TO = "survives-to"             # universal claim: no counterexample at any scale read
OPEN = "open"                           # no finite data can settle it, or the ledger says open
ESTIMATE = "estimate"                   # an extrapolation; never checked
MEASURED = "measured"                   # a recomputed measurement (not a universal claim)
UNTESTED = "untested"                   # analogy / proposal / meta / trend: no executable test
UNCHECKED = "unchecked-implication"     # an implication with no checked edge
RETRACTED = "retracted"                 # depends (by a 'uses' edge) on a refuted claim
NEW = "new"

REF_LEDGER = "refuted-by-ledger"
REF_ESCALATION = "refuted-on-escalation"
REF_RECOMPUTE = "refuted-by-recompute"
REF_EXACT = "refuted-exact"             # a finite claim whose exact computation fails

SPEAKABLE = {PROVED, VERIFIED, SURVIVES_TO, OPEN, ESTIMATE, MEASURED}

CLAIM_CLASSES = ("finite", "Pi1", "Pi2", "implication", "comparison", "measurement", "estimate",
                 "analogy", "proposal", "meta", "trend", "prediction")
NO_TEST_CLASSES = {"analogy", "proposal", "meta", "trend"}

# Dependency edges.  A refutation propagates along 'uses' edges only (GateLoop.rollback_sound);
# 'derived' edges (narrowed / cut / corrected restatements) never propagate
# (GateLoop.derived_edge_unsound).
USES, DERIVED = "uses", "derived"


def is_refuted(status: str) -> bool:
    return status.startswith("refuted")


def answer_of(status: str) -> Optional[bool]:
    """What a final status asserts about the claim as stated: True / False / None."""
    if status in (PROVED, VERIFIED, MEASURED):
        return True
    if is_refuted(status):
        return False
    return None


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 1. Exact tools (Rule 30)
# ═════════════════════════════════════════════════════════════════════════════════════════════
# A row is a Python int.  Bit (W + c) holds the cell in column c.  Rule 30:
#     new[c] = old[c-1] XOR (old[c] OR old[c+1])   i.e.  new = (x << 1) ^ (x | (x >> 1)).
# A seed is an int whose bit j is the cell in column j at time 0 (seed 1 = one black cell).
# Conventions agree with the Lean package: centerCol n = evolve seed n 0,
# ldiag D t = evolve seed t (D - t), rdiag D t = evolve seed t (t - D).

def rule30_step(x: int) -> int:
    return (x << 1) ^ (x | (x >> 1))


_CENTRE_CACHE: Dict[int, List[int]] = {}


def centre_bits(n: int, seed: int = 1) -> List[int]:
    """The first n cells of the centre column (column 0) started from `seed`."""
    c = _CENTRE_CACHE.get(seed)
    if c is not None and len(c) >= n:
        return c[:n]
    W = n + seed.bit_length() + 2
    x = seed << W
    out = []
    for _ in range(n):
        out.append((x >> W) & 1)
        x = rule30_step(x)
    _CENTRE_CACHE[seed] = out
    return list(out)


def lc_profile(bits: List[int]) -> List[int]:
    """Berlekamp-Massey over GF(2): prof[n] = linear complexity of the first n bits (exact)."""
    C, B, L, m, R = 1, 1, 0, 1, 0
    prof = [0]
    for n, b in enumerate(bits):
        d = (b ^ bin((C >> 1) & R).count("1")) & 1
        if d:
            T = C
            C ^= B << m
            if 2 * L <= n:
                L, B, m = n + 1 - L, T, 1
            else:
                m += 1
        else:
            m += 1
        R = (R << 1) | b
        prof.append(L)
    return prof


def wobble_path(bits: List[int]) -> List[int]:
    """D(N) = #black - #white in the first N bits, N = 0..len (the Wobble / delta-sigma sum)."""
    D, out = 0, [0]
    for b in bits:
        D += 1 if b else -1
        out.append(D)
    return out


def wobble_max_ratio(bits: List[int]) -> Tuple[Fraction, int]:
    """max over N >= 1 of D(N)^2 / N, exactly, and the first N attaining it."""
    best, arg, D = Fraction(0), 0, 0
    for N, b in enumerate(bits, 1):
        D += 1 if b else -1
        if D * D * (best.denominator) > best.numerator * N:
            best, arg = Fraction(D * D, N), N
    return best, arg


def observer_arrow_agreement(bits: List[int]) -> Fraction:
    """The owner's 'Wobble as perspective' read: the observer's arrow at time n is -sign D(n)
    (Lean: Perspective.deviation_decreases_iff -- the frequency moves towards 1/2 exactly when the
    next step goes the arrow's way).  Returns the exact fraction of steps n (with D(n) != 0) at
    which the next bit follows the arrow."""
    D, agree, total = 0, 0, 0
    for b in bits:
        if D != 0:
            total += 1
            step = 1 if b else -1
            if step * D < 0:
                agree += 1
        D += 1 if b else -1
    return Fraction(agree, total) if total else Fraction(0)


def block_counts(bits: List[int], k: int) -> Dict[int, int]:
    cnt: Dict[int, int] = {w: 0 for w in range(1 << k)}
    w, mask = 0, (1 << k) - 1
    for i, b in enumerate(bits):
        w = ((w << 1) | b) & mask
        if i >= k - 1:
            cnt[w] += 1
    return cnt


def thue_morse(n: int) -> List[int]:
    return [bin(i).count("1") & 1 for i in range(n)]


def first_coverage(bits: List[int], k: int) -> Optional[int]:
    """Least N such that every k-bit word occurs in the first N bits (None if not within len)."""
    seen, w, mask, need = set(), 0, (1 << k) - 1, 1 << k
    for i, b in enumerate(bits):
        w = ((w << 1) | b) & mask
        if i >= k - 1:
            seen.add(w)
            if len(seen) == need:
                return i + 1
    return None


def eventual_period(seq: List[int], pmax: int, confirm: int) -> Optional[Tuple[int, int]]:
    """Least (p, tau) with p <= pmax such that seq[t] == seq[t+p] for all tau <= t < len - p and
    the periodic part is seen for at least `confirm` steps.  Exact on the window only."""
    n = len(seq)
    for p in range(1, pmax + 1):
        tau = 0
        for t in range(n - p - 1, -1, -1):
            if seq[t] != seq[t + p]:
                tau = t + 1
                break
        if tau + p + confirm <= n:
            return p, tau
    return None


class DiagonalTable:
    """Eventual periods of the left diagonals D = 0..Dmax on a time window [0, T).

    The computation is exact on the window; "eventual" is inferred from a confirmation stretch of
    4p + 64 steps (the Lean certificates in LeftDiagonalPeriodsData settle the ranges cited by the
    ledger).  All diagonals are processed at once: frame f_t holds bit D = ldiag D t."""

    def __init__(self, Dmax: int, T: Optional[int] = None, seed: int = 1, pmax: int = 64):
        self.Dmax = Dmax
        self.T = T if T is not None else int(Dmax * 3 // 2) + 400
        self.seed = seed
        W = self.T + seed.bit_length() + 2
        x = seed << W
        mask = (1 << (Dmax + 1)) - 1
        frames = []
        for t in range(self.T):
            frames.append((x >> (W - t)) & mask)
            x = rule30_step(x)
        self.frames = frames
        self.period: Dict[int, int] = {}
        self.pre: Dict[int, int] = {}
        undecided = set(range(Dmax + 1))
        p = 1
        while p <= pmax and undecided:
            seen, last = 0, {}
            for t in range(self.T - p - 1, -1, -1):
                diff = frames[t] ^ frames[t + p]
                new = diff & ~seen
                while new:
                    low = new & -new
                    last[low.bit_length() - 1] = t
                    new ^= low
                seen |= diff
            for D in list(undecided):
                tau = last.get(D, -1) + 1
                if tau + 4 * p + 64 <= self.T - p:
                    self.period[D], self.pre[D] = p, tau
                    undecided.discard(D)
            p *= 2
        self.undecided = sorted(undecided)

    def value(self, D: int, t: int) -> int:
        return (self.frames[t] >> D) & 1

    def white(self, D: int) -> bool:
        """Eventually white (eventual period 1 with value 0)."""
        return (self.period.get(D) == 1 and self.pre[D] < self.T
                and self.value(D, self.T - 1) == 0)

    def parity_odd(self, D: int) -> bool:
        """Odd number of black cells in one eventual period."""
        p, tau = self.period[D], self.pre[D]
        return sum(self.value(D, t) for t in range(tau, tau + p)) % 2 == 1

    def doubling_points(self) -> List[int]:
        """D at which the period exceeds the periods of both outside diagonals D-1, D-2."""
        out = []
        for D in range(2, self.Dmax + 1):
            if D in self.period and D - 1 in self.period and D - 2 in self.period:
                if self.period[D] > max(self.period[D - 1], self.period[D - 2]):
                    out.append(D)
        return out


def rdiag_period(D: int, T: Optional[int] = None) -> Optional[Tuple[int, int]]:
    """Least eventual period of the right diagonal D (rdiag D t = cell (t, t - D)), on a window."""
    T = T if T is not None else (1 << D) * 6 + 4 * D + 64
    W = T + 3
    x = 1 << W
    seq = []
    for t in range(T):
        c = t - D
        seq.append((x >> (W + c)) & 1 if -W < c else 0)
        x = rule30_step(x)
    return eventual_period(seq, 1 << D, 2 * (1 << D) + 16)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 2. Layers, reads and the arrow
# ═════════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class Read:
    layer: str
    scale: Any                  # the scale read at this layer (an int range end, a box, ...)
    verdict: Optional[bool]     # True = passes, False = counterexample found, None = not read
    detail: str = ""


@dataclass
class LayerProfile:
    """Five nested reads of one claim.  For a universal (Pi1) claim on nested domains the passing
    layers form a prefix, a refutation is never undone by reading higher, and the claim holds at
    every layer iff it holds at the largest (GateLoop.holdsAt_anti, refuted_stable,
    holdsAll_iff_top).  The reads stop at the first failure (escalate before assert,
    GateLoop.escalate_eq_some): the read trajectory is a sorted prefix of the ladder
    (GateLoop.reads_prefix, reads_sorted)."""
    claim: str
    reads: List[Read] = field(default_factory=list)

    def first_fail(self) -> Optional[int]:
        for i, r in enumerate(self.reads):
            if r.verdict is False:
                return i
        return None

    def shape_ok(self) -> bool:
        """Passing reads form a prefix followed by at most one failure, then nothing."""
        seen_fail = False
        for r in self.reads:
            if seen_fail and r.verdict is not None:
                return False
            if r.verdict is False:
                seen_fail = True
        return True

    def verdict(self) -> Optional[bool]:
        if self.first_fail() is not None:
            return False
        if self.reads and all(r.verdict is True for r in self.reads):
            return True
        return None

    def arrow(self) -> dict:
        """The claim's arrow: the layers actually read, in order (never decreasing), and its
        direction -- 'converging' while every read passes, 'flipped at <layer>' at the first
        refutation.  This is the owner's Wobble/Observer reading made exact: the observer only
        reads upwards, and the direction says where the run is heading."""
        read = [r.layer for r in self.reads if r.verdict is not None]
        ff = self.first_fail()
        if not read:
            return {"read": [], "direction": "not read", "settled": None}
        if ff is None:
            return {"read": read, "direction": "converging", "settled": read[-1]}
        return {"read": read, "direction": f"flipped at {self.reads[ff].layer}",
                "settled": self.reads[ff].layer}

    def summary(self) -> str:
        cells = []
        for r in self.reads:
            v = "-" if r.verdict is None else ("T" if r.verdict else "F")
            cells.append(f"{r.layer}={r.scale}:{v}")
        return ", ".join(cells)

    def as_dict(self) -> dict:
        return {"claim": self.claim, "reads": [r.__dict__ for r in self.reads],
                "verdict": self.verdict(), "arrow": self.arrow(), "shape_ok": self.shape_ok()}


def escalation_profile(claim: str, scales: List[Any],
                       check: Callable[[Any], Tuple[bool, str]]) -> LayerProfile:
    """Read `check` at five nested scales, stopping at the first failure."""
    prof = LayerProfile(claim)
    failed = False
    for layer, sc in zip(LAYERS, scales):
        if failed:
            prof.reads.append(Read(layer, sc, None, "not read (already refuted)"))
            continue
        ok, detail = check(sc)
        prof.reads.append(Read(layer, sc, bool(ok), detail))
        failed = not ok
    return prof


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 3. Hypotheses and claim classes
# ═════════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class Hypothesis:
    hid: str
    key: str                     # canonical family key, e.g. "LD.period.divides"
    text: str                    # the sentence (what would be spoken)
    cls: str                     # claim class (see CLAIM_CLASSES)
    domain: str = "rule30"
    origin: str = "lift"         # lift | narrow | registry | import | implication | transport ...
    params: dict = field(default_factory=dict)       # structured parameters (the ledger reads these)
    deps: List[Tuple[str, str]] = field(default_factory=list)   # (parent hid, USES | DERIVED)
    check: Optional[Callable[[Any], Tuple[bool, str]]] = None   # universal claim: check(scale)
    scales: List[Any] = field(default_factory=list)              # five nested scales
    exact: Optional[Callable[[], Tuple[bool, str]]] = None      # finite claim: whole range
    recompute: Optional[Callable[[], Tuple[bool, str]]] = None  # comparison / measurement
    status: str = NEW
    backing: List[str] = field(default_factory=list)
    profile: Optional[LayerProfile] = None
    gate_log: List[str] = field(default_factory=list)
    truth: Any = "unset"         # ground truth fixed in advance (True / False / None), for scoring

    def note(self, gate: str, new_status: str, reason: str):
        self.gate_log.append(f"[{gate}] {self.status} -> {new_status}: {reason}")
        self.status = new_status


_FINITE_RANGE = re.compile(r"(D\s*<\s*\d+|n\s*≤\s*\d+\s*only|preperiod\s*≤\s*\d+|first left diagonal"
                           r" with|first \d+ bits|is D = \d+|D\s*∈\s*\{)")


def auto_claim_class(text: str) -> str:
    """Classify a claim from its sentence alone.  Used for imported claims (wheel turns, claim
    files); the engine's own hypotheses carry their class from the proposer."""
    t = text.lower()
    if t.strip().endswith("?") or t.startswith(("what ", "which ", "why ", "how ")):
        return "meta"
    if any(w in t for w in ("follows from", " implies ", "is implied by", "implied by",
                            "because the", "is the cause", "explains")):
        return "implication"
    if "estimat" in t or "extrapolat" in t:
        return "estimate"
    if any(w in t for w in ("grows with", "growing", "increasing trend")) and "without bound" not in t:
        return "trend"
    if any(w in t for w in ("infinitely many", "unbounded", "without bound")):
        return "Pi2"
    if "match:" in t:
        return "measurement"
    if re.search(r"\b(more|less) uniform than\b", t) or re.search(r"\b(larger|smaller) than\b", t):
        return "comparison"
    if any(w in t for w in ("analogous", "analogy", "same structure", "is a model", "dyadic tower",
                            "can be compared", "provide an", "provides an", "fingerprint",
                            "forward-looking", "predicts where", "is evidence", "cross-domain",
                            "conversation system", "retrieval")):
        return "analogy"
    if any(w in t for w in ("grows with", "growing", "increasing trend")):
        return "trend"
    if any(w in t for w in ("find ", "formalise", "formalize", "a guard-extractor", "test the engine",
                            "extend the", "should ")):
        return "proposal"
    if _FINITE_RANGE.search(text):
        return "finite"
    return "Pi1"


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 4. The ledger: Lean-checked results the engine may cite
# ═════════════════════════════════════════════════════════════════════════════════════════════
# Every theorem name below exists in the Lean package RequestProject/GLM (file.declaration).
# FORMAL = a Lean proof (standard axioms); CERT = a Lean finite certificate (native_decide).
# A ledger entry returns (verdict, tag, names[, range]) where verdict is True / False / "open" /
# "partial" (the claim is certified on a stated range only), or None when it does not apply.

LedgerVerdict = Optional[tuple]

WOBBLE_CERT = (175561, 24979)   # max D(N)^2/N on N <= 10^6 (WobbleCertificate.wobble_sq_ratio_cert)


def _l_ld_divides(h):
    m = h.params.get("m")
    if m == 8:
        return (False, "CERT", "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight")
    if m == 16:
        return (False, "CERT", "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen")
    if m in (1, 2, 4):
        return (False, "CERT", "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight "
                "(a period dividing m also divides 8)")
    return None


def _l_ld_divides_below(h):
    m, N = h.params.get("m"), h.params.get("N")
    if m is None or N is None:
        return None
    if m % 8 == 0 and N <= 400:
        return (True, "CERT", "LeftDiagonalPeriodsData.leftDiag_period_eight_below_400")
    if m % 16 == 0 and N <= 87867:
        return (True, "CERT", "LeftDiagonalPeriodsData.leftDiag_period_sixteen_below_87867")
    if m == 8 and N > 400:
        return (False, "CERT", "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight")
    return None


def _l_balance(h):
    c = h.params.get("c")
    if c is None:
        return None
    a, b = WOBBLE_CERT
    if c * c * b >= a:
        return ("partial", "CERT", "WobbleCertificate.wobble_sq_ratio_cert (holds for N <= 10^6)",
                10 ** 6)
    return (False, "CERT", "WobbleCertificate.wobble_sq_ratio_cert (D(24979)^2/24979 = "
            "175561/24979 > c^2)")


def _l_lc(h):
    b = h.params.get("b")
    if b is None:
        return None
    if b <= 10:
        return (False, "CERT", "WheelChecksData.wheel_H19_false (2·L(11101) − 11101 ≥ 11)")
    if b <= 12:
        return (False, "CERT", "WheelChecksData.ledger_C160_overstated (2·L(19521) − 19521 ≥ 13)")
    return None


def _l_short_period(h):
    p, tau = h.params.get("p"), h.params.get("tau")
    if p is None or tau is None:
        return None
    if p <= 64 and tau <= 10000:
        return (True, "CERT", "WheelChecksData.wheel_H16_true")
    if p <= 64 and tau <= 30000:
        return (True, "CERT", "GateLoopData.centre_no_short_period_30000")
    return None


LEDGER: Dict[str, Callable[[Hypothesis], LedgerVerdict]] = {
    # left diagonals
    "LD.period.divides": _l_ld_divides,
    "LD.period.divides.below": _l_ld_divides_below,
    "LD.white.finite": lambda h: (False, "FORMAL", "WhiteDiagonals.ldiag_infinitely_many_white"),
    "LD.white.exactly": lambda h: (False, "FORMAL", "WhiteDiagonals.ldiag_infinitely_many_white "
                                   "(infinitely many eventually white diagonals; "
                                   "LeftDiagonalPeriodsData.leftDiag_white_below_87868 lists those "
                                   "below 87868)"),
    "LD.preperiod.gt.D": lambda h: ("partial", "CERT",
                                    "LeftDiagonalPeriodsData.centerCol_read_in_transient "
                                    "(20 ≤ D < 20000)", 20000),
    "LD.period.law": lambda h: (True, "FORMAL", "LeftDiagonalPeriods.ldiag_evPer_of_not_white, "
                                "ldiag_doubles, ldiag_keeps_of_even"),
    "LD.periods.unbounded": lambda h: ("open", "FORMAL", "open; proved reduction "
                                       "WhiteDiagonals.ldiag_periods_unbounded_iff"),
    "LD.first.period.32": lambda h: (True, "CERT", "LeftDiagonalPeriodsData."
                                     "ldiag_87867_not_evPer_sixteen + "
                                     "leftDiag_period_sixteen_below_87867")
    if h.params.get("D") == 87867 else None,
    "LD.seed.forgetting": lambda h: (True, "FORMAL", "LeftDiagonalPeriods.first_difference_after_white;"
                                     " LeftDiagonalPeriodsData.seed_first_difference"),
    # right diagonals
    "RD.lp.le.2^D": lambda h: (True, "FORMAL", "Diagonals.rdiag_periodic"),
    "RD.lp.gt.half": lambda h: (True, "FORMAL", "Diagonals.rdiag_not_periodic"),
    "RD.periodic.or.anti": lambda h: (True, "FORMAL",
                                      "RightDiagonalBalance.runningXor_periodic_or_antiPeriodic"),
    # centre column
    "CC.no.short.period": _l_short_period,
    "CC.not.eventually.constant": lambda h: (True, "FORMAL",
                                             "NoConstantColumn.centerCol_not_eventually_constant"),
    "CC.balance.sqrt": _l_balance,
    "CC.lc.near.half": _l_lc,
    "CC.one.periodic.column": lambda h: (True, "FORMAL",
                                         "OnePeriodicColumn.seed_at_most_one_periodic_column"),
    "CC.rule.class.30.86": lambda h: (True, "FORMAL", "Observer.centre_column_class"),
    # the three prize problems
    "PRIZE.1": lambda h: ("open", "FORMAL", "open; no finite prefix decides it "
                          "(WobbleCertificate.no_finite_certificate_problem1); sufficient targets "
                          "in Frontier.frontier_sufficient_targets"),
    "PRIZE.2": lambda h: ("open", "FORMAL", "open; no finite prefix decides it "
                          "(WobbleCertificate.no_finite_certificate_problem2); a C·√N wobble bound "
                          "suffices (Prizes.problem2_of_sqrt_bound)"),
    "PRIZE.3": lambda h: ("open", "FORMAL", "open; reduction Problem3Quantifiers.problem3_of_eventual"),
    "PRIZE.ae": lambda h: (True, "FORMAL", "Ergodic.ae_problems_one_and_two"),
    # TAX (v13 / v14 vocabulary)
    "TAX.conserved.at.jumps": lambda h: (True, "FORMAL", "TaxChecks.tax_conserved_at_doubling"),
    "TAX.criterion": lambda h: (False, "FORMAL", "TaxChecks.docstring_criterion_wrong"),
    "TAX.only.white": lambda h: (False, "CERT", "TaxChecksData.tax_conserved_not_only_white"),
    # general benchmarks (HypothesisEngine/Benchmarks.lean)
    "GEN.euler.prime": lambda h: (False, "FORMAL", "Benchmarks.euler_not_prime_40"),
    "GEN.euler.prime.below40": lambda h: (True, "FORMAL", "Benchmarks.euler_prime_below_40"),
    "GEN.fermat.prime": lambda h: (False, "FORMAL", "Benchmarks.fermat_five_not_prime"),
    "GEN.fermat.coprime": lambda h: (True, "FORMAL", "Benchmarks.fermat_pairwise_coprime"),
    "GEN.two.squares": lambda h: (True, "FORMAL", "Benchmarks.two_squares_law"),
    "GEN.circle.regions": lambda h: (False, "FORMAL", "Benchmarks.moser_split"),
    "GEN.josephus": lambda h: (True, "FORMAL", "Benchmarks.josephus_closed_form"),
    "GEN.collatz.bound": lambda h: (False, "FORMAL", "Benchmarks.collatz_27_slow"),
    "GEN.gcd.trap": lambda h: (False, "FORMAL", "Benchmarks.gcd_trap_refuted"),
}

# Checked implication edges (an implication is a claim about all models: data cannot settle it).
IMPLICATIONS: Dict[str, tuple] = {
    "IMP.transient.implies.aperiodic": (False, "FORMAL",
                                        "DialogueChecks.transient_read_does_not_imply_aperiodic"),
    "IMP.finite.data.decides.unbounded": (False, "FORMAL",
                                          "NeedsWheel.finite_data_never_forces_infinitely_many"),
    "IMP.sqrt.wobble.implies.P2": (True, "FORMAL", "Prizes.problem2_of_sqrt_bound"),
    "IMP.arrow.moves.to.half": (True, "FORMAL", "Perspective.deviation_decreases_iff"),
    "IMP.survival.implies.truth": (False, "FORMAL", "GateLoop.survives_as_proved_unsound; "
                                   "Benchmarks.gcd_trap_refuted"),
    "IMP.map.properties.decide.P1": (False, "FORMAL",
                                     "Frontier.frontier_blocked_routes (map_properties_cannot_"
                                     "decide_periodicity)"),
    "IMP.tax.explains.doubling": (False, "FORMAL", "the doubling law is proved from the left step "
                                  "alone: LeftDiagonalPeriods.ldiag_doubles, ldiag_keeps_of_even"),
}


def load_claims_csv(path: Path) -> Dict[str, dict]:
    """Optional: the full evidence ledger (RequestProject/GLM/Rule30/claims.csv), keyed by row id.
    Only used for display (the 'ledger' section of a report); verdicts come from LEDGER above."""
    import csv
    out = {}
    if not path.exists():
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and re.match(r"^C\d+$", row[0]):
                out[row[0]] = {"claim": row[1] if len(row) > 1 else "",
                               "tag": row[2] if len(row) > 2 else "",
                               "status": row[3] if len(row) > 3 else "",
                               "lean": row[4] if len(row) > 4 else ""}
    return out


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 5. The gate cascade and typed rollback
# ═════════════════════════════════════════════════════════════════════════════════════════════
# Every gate may only (a) settle a claim with evidence it can name, or (b) leave it alone.
# A cascade of sound gates never refutes a true claim or proves a false one
# (GateLoop.cascade_sound, cascade_no_wrong).  The ledger gate is the only one that says PROVED.

class Engine:
    def __init__(self, use_ledger: bool = True, log: Optional[Callable[[str], None]] = None):
        self.use_ledger = use_ledger
        self.hyps: List[Hypothesis] = []
        self.by_id: Dict[str, Hypothesis] = {}
        self.conflicts: List[str] = []
        self.rollback_log: List[str] = []
        self.log = log or (lambda s: None)
        self._n = 0

    # -- bookkeeping --------------------------------------------------------------------------
    def add(self, h: Hypothesis) -> Hypothesis:
        if not h.hid:
            self._n += 1
            h.hid = f"H{self._n:02d}"
        self.hyps.append(h)
        self.by_id[h.hid] = h
        return h

    # -- gates --------------------------------------------------------------------------------
    def gate_class(self, h: Hypothesis) -> bool:
        """Returns False when the claim's class means no executable gate applies."""
        if h.cls in NO_TEST_CLASSES:
            h.note("class", UNTESTED, f"class '{h.cls}': no executable test; kept on the wheel")
            return False
        if h.cls == "estimate":
            h.note("class", ESTIMATE, "an extrapolation: only reaching the predicted range checks it")
            return False
        return True

    def gate_recompute(self, h: Hypothesis):
        if h.recompute is None:
            return
        ok, detail = h.recompute()
        if h.cls == "measurement":
            h.note("recompute", MEASURED if ok else REF_RECOMPUTE, detail)
        else:
            h.note("recompute", VERIFIED if ok else REF_RECOMPUTE, detail)
        h.backing.append(f"EXACT recomputation: {detail}")

    def gate_exact(self, h: Hypothesis):
        if h.exact is None or h.status != NEW:
            return
        ok, detail = h.exact()
        h.note("exact", VERIFIED if ok else REF_EXACT, detail)
        h.backing.append(f"EXACT {'whole range' if ok else 'counterexample'}: {detail}")

    def gate_escalate(self, h: Hypothesis):
        """Escalate before asserting: read the claim at five nested scales, stop at the first
        failure (a concrete counterexample).  Surviving every read is NOT proof."""
        if h.check is None or not h.scales or h.status != NEW:
            return
        prof = escalation_profile(h.text, h.scales, h.check)
        h.profile = prof
        if not prof.shape_ok():
            self.conflicts.append(f"{h.hid}: layer-shape violation {prof.summary()}")
        ff = prof.first_fail()
        if ff is not None:
            r = prof.reads[ff]
            h.note("escalate", REF_ESCALATION, f"counterexample at {r.layer} (scale {r.scale}): {r.detail}")
            h.backing.append(f"EXACT counterexample: {r.detail}")
        else:
            top = prof.reads[-1]
            if h.cls == "Pi2":
                h.note("escalate", OPEN, f"finite proxy holds up to {top.scale}; a Pi2 claim is never "
                       "decided by data (NeedsWheel.finite_data_never_forces_infinitely_many)")
            else:
                h.note("escalate", SURVIVES_TO, f"no counterexample at any of the five scales "
                       f"(up to {top.scale}); open beyond")
            h.backing.append(f"escalation: survives every read, up to {top.scale}")

    def gate_implication(self, h: Hypothesis):
        if h.cls != "implication":
            return
        edge = IMPLICATIONS.get(h.key)
        if edge is None or not self.use_ledger:
            h.note("implication", UNCHECKED, "no checked implication edge" +
                   ("" if self.use_ledger else " (ledger switched off)"))
            return
        v, tag, names = edge
        h.note("implication", PROVED if v else REF_LEDGER, f"{tag} {names}")
        h.backing.append(f"{tag} {names}")

    def gate_ledger(self, h: Hypothesis):
        if not self.use_ledger or h.cls == "implication":
            return
        fn = LEDGER.get(h.key)
        res = fn(h) if fn else None
        if res is None:
            return
        v, tag, names = res[0], res[1], res[2]
        cite = f"{tag} {names}"
        if v is True:
            if is_refuted(h.status):
                self.conflicts.append(f"{h.hid}: gate refuted but ledger proves ({cite})")
                return
            h.note("ledger", PROVED, cite)
        elif v is False:
            if h.status in (VERIFIED, PROVED):
                self.conflicts.append(f"{h.hid}: gate verified but ledger refutes ({cite})")
                return
            if is_refuted(h.status):
                h.backing.append(cite)       # agreement: keep the gate's own counterexample too
                return
            h.note("ledger", REF_LEDGER, cite)
        elif v == "open":
            if is_refuted(h.status) or h.status in (VERIFIED, PROVED):
                self.conflicts.append(f"{h.hid}: settled by a gate but the ledger says open ({cite})")
                return
            h.note("ledger", OPEN, cite)
        elif v == "partial":
            h.backing.append(f"{cite}")
            return
        h.backing.append(cite)

    def finish_status(self, h: Hypothesis):
        if h.status != NEW:
            return
        if h.cls == "Pi2":
            h.note("final", OPEN, "no finite data decides a Pi2 claim")
            h.backing.append("class Pi2: no finite data decides it "
                             "(NeedsWheel.finite_data_never_forces_infinitely_many)")
        elif h.cls in ("Pi1", "finite", "comparison", "measurement", "prediction"):
            h.note("final", UNTESTED, "no executable test was attached (an import the engine could "
                   "not recognise)")

    def cascade(self, h: Hypothesis):
        if self.gate_class(h):
            self.gate_recompute(h)
            self.gate_exact(h)
            self.gate_escalate(h)
            self.gate_implication(h)
        self.gate_ledger(h)
        self.finish_status(h)

    # -- typed rollback (fixpoint) ------------------------------------------------------------
    def rollback(self):
        """Retract every claim that USES a refuted or retracted claim, to a fixpoint.  The result
        is the least dependency-closed set containing the refuted claims; it does not depend on
        the order of processing (GateLoop.retracted_least, retracted_union, loop_eq_retracted).
        Claims settled by their own evidence (proved / refuted / verified) are kept."""
        changed = True
        while changed:
            changed = False
            for h in self.hyps:
                if h.status in (PROVED, VERIFIED, RETRACTED) or is_refuted(h.status):
                    continue
                for pid, edge in h.deps:
                    p = self.by_id.get(pid)
                    if edge == USES and p is not None and (is_refuted(p.status) or p.status == RETRACTED):
                        self.rollback_log.append(f"{h.hid} <- {pid} (was {h.status})")
                        h.note("rollback", RETRACTED, f"uses {pid}, which is {p.status}")
                        changed = True
                        break

    def run(self):
        for h in self.hyps:
            if h.status == NEW:
                self.cascade(h)
        self.rollback()
        return self


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 6. Wheels
# ═════════════════════════════════════════════════════════════════════════════════════════════
# The owner's wheel had three rings (doesn't-know / thinks-true / thinks-needed) and a language
# wheel.  v18 keeps the rings but fixes what goes on them:
#   KNOWS        settled with named evidence: proved (Lean), verified-exact, measured, refuted
#   THINKS-TRUE  survives-to N: no counterexample at any scale read (NOT evidence of truth)
#   DOESN'T-KNOW open, estimate, untested, unchecked implication, retracted
#   NEEDS        one machine-readable Need per non-KNOWS entry: what would settle it
# The LANGUAGE wheel is the vetted vocabulary: the KNOWS entries with their backing, both true
# and false ones (a refuted sentence is vocabulary too: "do not say this").
# Lean (HypothesisEngine/Wheel.lean): only KNOWS asserts anything (assertion_isSome_iff,
# thinksTrue_asserts_nothing); speaking from a sound language wheel is sound (speak_sound); a turn
# that keeps what was known stays sound and only grows KNOWS (merge_sound, knows_merge); a
# conflict between two wheels means one is unsound (conflict_unsound).

KNOWS, THINKS, DONT_KNOW = "knows", "thinks-true", "doesn't-know"


def ring_of(status: str) -> str:
    if status in (PROVED, VERIFIED, MEASURED) or is_refuted(status):
        return KNOWS
    if status == SURVIVES_TO:
        return THINKS
    return DONT_KNOW


@dataclass
class Need:
    kind: str           # proof | test | edge | range | restate | primitive | data
    signature: str      # machine key
    because: str
    blocks: List[str] = field(default_factory=list)
    acceptance: str = ""

    def as_dict(self):
        return dict(self.__dict__)


def need_of(h: Hypothesis) -> Optional[Need]:
    s = h.status
    if ring_of(s) == KNOWS:
        return None
    if s == SURVIVES_TO:
        top = h.profile.reads[-1].scale if h.profile else "?"
        return Need("proof", f"proof:{h.key}", f"survives every read (to {top}); data cannot prove "
                    "a universal claim", [h.hid], "a Lean theorem name for the ledger")
    if s == OPEN:
        return Need("proof", f"proof:{h.key}", "open: no finite data decides it", [h.hid],
                    "a Lean proof, or a proved reduction to a smaller open target")
    if s == UNTESTED:
        return Need("test", f"test:{h.key}", f"class '{h.cls}': state an executable prediction "
                    "that could fail", [h.hid], "the prediction is run and can be refuted")
    if s == UNCHECKED:
        return Need("edge", f"edge:{h.key}", "an implication with no checked edge", [h.hid],
                    "a Lean proof of the implication or a counter-model")
    if s == ESTIMATE:
        return Need("data", f"range:{h.key}", "an extrapolation: only reaching the predicted range "
                    "checks it", [h.hid], "the predicted range is computed")
    if s == RETRACTED:
        return Need("restate", f"restate:{h.key}", "depends on a refuted claim; restate without it",
                    [h.hid], "a restatement whose dependencies all stand")
    return Need("test", f"test:{h.key}", f"status {s}", [h.hid], "")


def build_wheel(engine: Engine, title: str) -> dict:
    rings = {KNOWS: [], THINKS: [], DONT_KNOW: []}
    needs, language = [], []
    for h in engine.hyps:
        r = ring_of(h.status)
        entry = {"hid": h.hid, "key": h.key, "params": _jsonable(h.params), "class": h.cls,
                 "statement": h.text, "status": h.status, "backing": h.backing[-3:],
                 "arrow": h.profile.arrow() if h.profile else None, "domain": h.domain}
        rings[r].append(entry)
        n = need_of(h)
        if n:
            needs.append(n.as_dict())
        if r == KNOWS:
            language.append({"concept": h.text, "verdict": answer_of(h.status)
                             if h.status != MEASURED else "measured",
                             "key": h.key, "params": _jsonable(h.params),
                             "backing": h.backing[-1] if h.backing else ""})
    merged: Dict[str, dict] = {}
    for n in needs:
        m = merged.setdefault(n["signature"], dict(n, blocks=[]))
        m["blocks"] = sorted(set(m["blocks"]) | set(n["blocks"]))
    return {"engine": f"GLM Hypothesis Engine {ENGINE_VERSION}", "title": title,
            "format": "glm-wheel/2", "rings": rings, "needs": list(merged.values()),
            "language_wheel": language,
            "counts": {k: len(v) for k, v in rings.items()}}


# -- the needs wheel: provisions, first sound speaker wins (NeedsWheel.lean) --------------------

@dataclass
class Provision:
    pid: str
    serves: List[str]           # need signatures or prefixes ending in '*'
    fn: Callable                # fn(task) -> True / False / None
    provenance: str             # FORMAL / CERT / EXACT / HEURISTIC
    sound: bool

    def serves_sig(self, sig: str) -> bool:
        return any((s.endswith("*") and sig.startswith(s[:-1])) or s == sig for s in self.serves)


def wheel_answer(provisions: List[Provision], base: Callable, task) -> Tuple[Any, str]:
    """NeedsWheel.answer: the first provision that speaks decides, else the base.  With sound
    provisions this never loses a right answer and never creates a wrong one
    (NeedsWheel.answer_right_of_right, answer_wrong_of_wrong); order among sound provisions does
    not matter (answer_perm); one unsound provision can hurt (unsound_can_hurt)."""
    for p in provisions:
        v = p.fn(task)
        if v is not None:
            return v, p.pid
    return base(task), "base"


def score(answers: Dict[str, Any], truth: Dict[str, Any]) -> dict:
    """right / wrong / overclaim (definite answer, open truth) / abstain (no answer, known truth)."""
    out = {"right": 0, "wrong": 0, "overclaim": 0, "abstain": 0}
    for k, a in answers.items():
        t = truth.get(k)
        if a == t:
            out["right"] += 1
        elif a is None:
            out["abstain"] += 1
        elif t is None:
            out["overclaim"] += 1
        else:
            out["wrong"] += 1
    out["n"] = len(answers)
    return out


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_jsonable(v) for v in (sorted(o) if isinstance(o, set) else o)]
    if isinstance(o, Fraction):
        return f"{o.numerator}/{o.denominator}"
    if isinstance(o, (int, float, str, bool)) or o is None:
        return o
    return str(o)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 7. Dialogue: speak only what is backed
# ═════════════════════════════════════════════════════════════════════════════════════════════

def dialogue(engine: Engine, extra: Optional[List[str]] = None) -> Tuple[List[str], dict]:
    lines = []
    c = Counter(ring_of(h.status) for h in engine.hyps)
    lines.append(f"I hold {len(engine.hyps)} claims: {c[KNOWS]} known (proved, verified, measured or "
                 f"refuted), {c[THINKS]} surviving every read, {c[DONT_KNOW]} not known.")
    for line in extra or []:
        lines.append(line)
    spoken = []
    groups = [(PROVED, "Proved in Lean"), (VERIFIED, "Verified exactly (finite claim, whole range)"),
              (MEASURED, "Measured exactly"),
              (SURVIVES_TO, "Survive every read (universal claims: open beyond the largest read)"),
              (OPEN, "Open (no finite data decides these)")]
    for st, title in groups:
        hs = [h for h in engine.hyps if h.status == st]
        if not hs:
            continue
        lines.append(f"{title} ({len(hs)}):")
        for h in hs:
            lines.append(f"  {h.hid}: {h.text} — {h.backing[-1] if h.backing else ''}")
            spoken.append(h.hid)
    refuted = [h for h in engine.hyps if is_refuted(h.status)]
    if refuted:
        lines.append(f"Refuted — do not say these ({len(refuted)}):")
        for h in refuted:
            lines.append(f"  {h.hid}: NOT '{h.text}' — {h.backing[-1] if h.backing else h.status}")
    flips = [h for h in engine.hyps if h.profile and h.profile.arrow()["direction"].startswith("flipped")]
    if flips:
        lines.append("Arrows that flipped (refuted only by reading higher):")
        for h in flips:
            a = h.profile.arrow()
            lines.append(f"  {h.hid}: read {' → '.join(a['read'])}; {a['direction']}")
    # consistency: every spoken claim is speakable and backed
    bad = [hid for hid in spoken if engine.by_id[hid].status not in SPEAKABLE
           or not engine.by_id[hid].backing]
    return lines, {"spoken": len(spoken), "spoken_without_backing_or_unspeakable": bad, "ok": not bad}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 8a. Domain: Rule 30
# ═════════════════════════════════════════════════════════════════════════════════════════════
# The engine proposes its own Rule 30 hypotheses: each FAMILY is a template whose parameters are
# LIFTED from development data (the smallest scale), then escalated through the five reads.  When
# a read refutes a lift, the conjecture loop (a) states the narrowed finite claim that the data
# do support (a DERIVED edge) and (b) re-lifts from the data up to the refuting read.  The same
# families are used to re-gate imported sentences (wheel turns), via RECOGNISERS.

class R30Data:
    """All exact Rule 30 data the domain needs, computed once."""

    def __init__(self, quick: bool = False):
        self.quick = quick
        self.n_centre = 40000 if quick else 160000
        self.n_lc = 12000 if quick else 20000
        self.d_max = 1500 if quick else 5000
        t0 = time.time()
        self.bits = centre_bits(self.n_centre)
        self.path = wobble_path(self.bits)
        self.lc = lc_profile(self.bits[:self.n_lc])
        self.diag = DiagonalTable(self.d_max)
        self.seconds = round(time.time() - t0, 2)
        # five nested scales per family (the first is the development range)
        self.sc_ld = [100, 300, 600, 1000, 1500] if quick else [100, 400, 1000, 2500, 5000]
        self.sc_bal = [1000, 4000, 10000, 20000, 40000] if quick else [1000, 4000, 20000, 50000, 160000]
        self.sc_lc = [3000, 6000, 8000, 10000, 12000] if quick else [3000, 6000, 9000, 12000, 20000]
        self.sc_words = [7, 8, 9, 10, 11] if quick else [9, 10, 11, 12, 13]
        self.sc_seeds = [2, 3, 4, 5, 6]
        self.sc_rd = [4, 6, 8, 9, 10] if quick else [6, 8, 9, 10, 12]
        self.sc_arrow = [4000, 10000, 20000, 30000, 40000] if quick else [4000, 20000, 50000, 100000, 160000]
        self._rd: Dict[int, Tuple[int, int]] = {}
        self._seed_wob: Dict[int, Tuple[Fraction, int]] = {}

    def rd(self, D: int) -> Tuple[int, int]:
        if D not in self._rd:
            self._rd[D] = rdiag_period(D)
        return self._rd[D]

    def seed_wobble(self, seed: int, N: int = 20000) -> Tuple[Fraction, int]:
        if seed not in self._seed_wob:
            self._seed_wob[seed] = wobble_max_ratio(centre_bits(N, seed))
        return self._seed_wob[seed]


def _frac(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}"


def _first(it):
    for x in it:
        return x
    return None


class Rule30Domain:
    name = "rule30"

    def __init__(self, data: R30Data):
        self.d = data

    # -- family builders: params -> Hypothesis (with its executable gate) -----------------------
    def build(self, key: str, params: dict, origin: str = "lift", text: Optional[str] = None,
              deps=None) -> Hypothesis:
        d, P = self.d, dict(params)
        h = Hypothesis("", key, text or "", "Pi1", "rule30", origin, P, list(deps or []))
        dg = d.diag
        if key == "LD.period.divides":
            m = P["m"]
            h.text = text or f"every left diagonal has eventual period dividing {m}"

            def chk(N, m=m):
                bad = _first(D for D in range(min(N, dg.Dmax + 1)) if D in dg.period and m % dg.period[D])
                return (bad is None, f"D < {N}: all periods divide {m}" if bad is None else
                        f"left diagonal {bad} has eventual period {dg.period[bad]}")
            h.check, h.scales = chk, d.sc_ld
        elif key == "LD.period.divides.below":
            m, N = P["m"], P["N"]
            h.cls = "finite"
            h.text = text or f"every left diagonal D < {N} has eventual period dividing {m}"
            if N <= dg.Dmax + 1:
                def ex(m=m, N=N):
                    bad = _first(D for D in range(N) if m % dg.period.get(D, 10 ** 9))
                    return (bad is None, f"all D < {N} computed" if bad is None else
                            f"left diagonal {bad} has eventual period {dg.period.get(bad)}")
                h.exact = ex
        elif key == "LD.white.exactly":
            S = sorted(P["S"])
            h.text = text or f"the eventually white left diagonals are exactly {S}"

            def chk(N, S=tuple(S)):
                W = [D for D in range(min(N, dg.Dmax + 1)) if dg.white(D)]
                exp = [s for s in S if s < N]
                return (W == exp, f"white diagonals below {N}: {W}")
            h.check, h.scales = chk, d.sc_ld
        elif key == "LD.white.below":
            S, N = sorted(P["S"]), P["N"]
            h.cls = "finite"
            h.text = text or f"the eventually white left diagonals below {N} are exactly {S}"
            if N <= dg.Dmax + 1:
                h.exact = lambda S=tuple(S), N=N: (
                    [D for D in range(N) if dg.white(D)] == list(S),
                    f"white diagonals below {N}: {[D for D in range(N) if dg.white(D)]}")
        elif key == "LD.white.finite":
            h.cls = "Pi2"
            h.text = text or "only finitely many left diagonals are eventually white"
        elif key == "LD.preperiod.gt.D":
            h.text = text or ("for D ≥ 20 the transient of left diagonal D is longer than D (so the "
                              "centre column, which reads diagonal D at time D, reads it inside its "
                              "transient)")

            def chk(N):
                bad = _first(D for D in range(20, min(N, dg.Dmax + 1)) if dg.pre[D] <= D)
                return (bad is None, f"20 ≤ D < {N}" if bad is None else f"D = {bad}: pre = {dg.pre[bad]}")
            h.check, h.scales = chk, d.sc_ld
        elif key == "LD.preperiod.envelope":
            lo, hi = Fraction(P["lo"]), Fraction(P["hi"])
            h.text = text or f"for D ≥ 20: {_frac(lo)} ≤ pre(D)/D ≤ {_frac(hi)}"

            def chk(N, lo=lo, hi=hi):
                bad = _first(D for D in range(20, min(N, dg.Dmax + 1))
                             if not lo <= Fraction(dg.pre[D], D) <= hi)
                return (bad is None, f"20 ≤ D < {N}" if bad is None else
                        f"D = {bad}: pre/D = {_frac(Fraction(dg.pre[bad], bad))}")
            h.check, h.scales = chk, d.sc_ld
        elif key == "LD.period.law":
            h.text = text or ("a left diagonal's period exceeds the periods of the two diagonals "
                              "outside it exactly when white(D−1) ∧ odd-parity(D−2)")

            def chk(N):
                for D in range(3, min(N, dg.Dmax + 1)):
                    if not all(x in dg.period for x in (D, D - 1, D - 2)):
                        continue
                    jump = dg.period[D] > max(dg.period[D - 1], dg.period[D - 2])
                    law = dg.white(D - 1) and dg.parity_odd(D - 2)
                    if jump != law:
                        return False, f"D = {D}: jump = {jump}, law = {law}"
                return True, f"3 ≤ D < {N}"
            h.check, h.scales = chk, d.sc_ld
        elif key == "LD.doubling.below":
            S, N = sorted(P["S"]), P["N"]
            h.cls = "finite"
            h.text = text or f"the period-doubling diagonals below {N} are exactly {S}"
            if N <= dg.Dmax + 1:
                h.exact = lambda S=tuple(S), N=N: (
                    [D for D in dg.doubling_points() if D < N] == list(S),
                    f"doubling diagonals below {N}: {[D for D in dg.doubling_points() if D < N]}")
        elif key == "LD.periods.unbounded":
            h.cls = "Pi2"
            h.text = text or ("the least periods of the left diagonals are unbounded (equivalently, by "
                              "the law, infinitely many eventually white diagonals meet odd parity)")
        elif key == "LD.first.period.32":
            h.cls = "finite"
            h.text = text or f"the first left diagonal with least eventual period 32 is D = {P['D']}"
        elif key == "LD.seed.forgetting":
            h.text = text or ("a left-white row can first differ from the seed only one diagonal past "
                              "an eventually white diagonal of the seed (a reset erases the seed)")
        elif key == "RD.lp.le.2^D":
            h.text = text or "every right diagonal D is periodic from time 0 with period 2^D"

            def chk(N):
                for D in range(0, N + 1):
                    p, tau = d.rd(D)
                    if tau != 0 or (1 << D) % p:
                        return False, f"D = {D}: (period, preperiod) = ({p}, {tau})"
                return True, f"D ≤ {N}"
            h.check, h.scales = chk, d.sc_rd
        elif key == "RD.lp.gt.half":
            h.text = text or "for D ≥ 1 the least eventual period of right diagonal D exceeds ⌈D/2⌉"

            def chk(N):
                for D in range(1, N + 1):
                    if d.rd(D)[0] <= (D + 1) // 2:
                        return False, f"D = {D}: period {d.rd(D)[0]}"
                return True, f"1 ≤ D ≤ {N}"
            h.check, h.scales = chk, d.sc_rd
        elif key == "RD.lp.formula":
            b, c = P["b"], P["c"]
            h.text = text or f"the least period of right diagonal D is 2^(D − ⌊(D + {b})/{c}⌋)"

            def chk(N, b=b, c=c):
                for D in range(0, N + 1):
                    e = D - (D + b) // c
                    if d.rd(D)[0] != 1 << e:
                        return False, f"D = {D}: period {d.rd(D)[0]}, formula gives {1 << e}"
                return True, f"D ≤ {N}"
            h.check, h.scales = chk, d.sc_rd
        elif key == "CC.no.short.period":
            p, tau = P["p"], P["tau"]
            h.cls = "finite"
            h.text = text or (f"the centre column is not eventually periodic with period p ≤ {p} and "
                              f"preperiod ≤ {tau}")
            if tau + p + 1 <= len(d.bits):
                def ex(p=p, tau=tau):
                    bits = d.bits
                    for q in range(1, p + 1):
                        w = _first(t for t in range(tau, len(bits) - q) if bits[t] != bits[t + q])
                        if w is None:
                            return False, f"no mismatch for period {q} after {tau} within the data"
                    return True, (f"for every period q ≤ {p} a mismatch c(t) ≠ c(t+q) with t ≥ {tau} "
                                  f"was found")
                h.exact = ex
        elif key == "CC.not.eventually.constant":
            h.cls = "Pi2"
            h.text = text or "the centre column is not eventually constant"
        elif key == "CC.balance.sqrt":
            c = P["c"]
            h.text = text or f"|#black − #white| ≤ {c}·√N for every prefix length N"

            def chk(N, c=c):
                bad = _first(n for n in range(1, min(N, len(d.bits)) + 1) if d.path[n] ** 2 > c * c * n)
                return (bad is None, f"N ≤ {N}" if bad is None else
                        f"N = {bad}: D(N)²/N = {_frac(Fraction(d.path[bad] ** 2, bad))} > {c * c}")
            h.check, h.scales = chk, d.sc_bal
        elif key == "CC.lc.near.half":
            b = P["b"]
            h.text = text or f"|2·L(n) − n| ≤ {b} for all n (L = linear complexity of the centre column)"

            def chk(N, b=b):
                bad = _first(n for n in range(1, min(N, len(d.lc) - 1) + 1) if abs(2 * d.lc[n] - n) > b)
                return (bad is None, f"n ≤ {N}" if bad is None else
                        f"n = {bad}: |2·L(n) − n| = {abs(2 * d.lc[bad] - bad)} > {b}")
            h.check, h.scales = chk, d.sc_lc
        elif key == "CC.words.cover":
            f = Fraction(P["f"])
            h.text = text or (f"every word of length k occurs in the first ⌈{_frac(f)}·k·2^k⌉ bits of "
                              f"the centre column")

            def chk(K, f=f):
                for k in range(1, K + 1):
                    lim = -(-f.numerator * k * (1 << k) // f.denominator)
                    cov = first_coverage(d.bits[:lim], k)
                    if cov is None:
                        if lim > len(d.bits):
                            return False, f"k = {k}: needs {lim} bits, only {len(d.bits)} computed"
                        return False, f"k = {k}: not every word occurs in the first {lim} bits"
                return True, f"k ≤ {K}"
            h.check, h.scales = chk, d.sc_words
        elif key == "CC.seed.same":
            seeds = P["seeds"]
            h.text = text or (f"seeds {', '.join(bin(s)[2:] for s in seeds)} give the same centre column "
                              "as seed 1")
            N_ = len(d.bits)
            sc = [N_ // 16, N_ // 8, N_ // 4, N_ // 2, N_]

            def chk(N, seeds=tuple(seeds)):
                for s in seeds:
                    cb = centre_bits(N, s)
                    bad = _first(i for i in range(N) if cb[i] != d.bits[i])
                    if bad is not None:
                        return False, f"seed {bin(s)[2:]} differs at time {bad}"
                return True, f"first {N} bits agree"
            h.check, h.scales = chk, sc
        elif key == "CC.wobble.transport":
            h.text = text or ("the wobble maximum D(N)²/N on N ≤ 20000 is the same for every seed "
                              "(the Wobble transports across seeds)")
            base = d.seed_wobble(1)[0]

            def chk(w, base=base):
                for s in range(1, 1 << w, 2):
                    v = d.seed_wobble(s)[0]
                    if v != base:
                        return False, (f"seed {bin(s)[2:]}: max D(N)²/N = {_frac(v)} ≠ {_frac(base)} "
                                       "(seed 1)")
                return True, f"all odd seeds of width ≤ {w}"
            h.check, h.scales = chk, d.sc_seeds
        elif key == "CC.uniformity.vs.tm":
            more = P["more"]
            n = 60000
            h.cls = "comparison"
            h.text = text or (f"the centre column's 2-bit block counts on its first {n} bits are "
                              f"{'more' if more else 'less'} uniform than Thue–Morse's (max − min gap)")

            def rc(more=more, n=n):
                a, b = block_counts(d.bits[:n], 2), block_counts(thue_morse(n), 2)
                ga, gb = max(a.values()) - min(a.values()), max(b.values()) - min(b.values())
                ok = (ga < gb) == more
                return ok, (f"centre gap = {ga}, Thue–Morse gap = {gb}; a smaller gap is more uniform, so "
                            f"the centre column is {'more' if ga < gb else 'less'} uniform")
            h.recompute = rc
        elif key == "CC.arrow.agreement":
            N = P["N"]
            h.cls = "measurement"
            h.text = text or (f"on the first {N} bits the next bit follows the observer's arrow "
                              f"(−sign D(n)) at a fraction {_frac(observer_arrow_agreement(d.bits[:N]))} "
                              "of the steps")
            h.recompute = lambda N=N: (True, f"exact count on {N} bits: "
                                       f"{_frac(observer_arrow_agreement(d.bits[:N]))}")
        elif key == "CC.arrow.below.half":
            n0 = P["n0"]
            h.text = text or (f"for every N ≥ {n0}, fewer than half of the first N steps follow the "
                              "observer's arrow (the run leans away from 1/2)")

            def chk(N, n0=n0):
                D, agree, total = 0, 0, 0
                for i, b in enumerate(d.bits[:N]):
                    if D != 0:
                        total += 1
                        if (1 if b else -1) * D < 0:
                            agree += 1
                    D += 1 if b else -1
                    if i + 1 >= n0 and 2 * agree >= total:
                        return False, f"N = {i + 1}: {agree} of {total} steps follow the arrow"
                return True, f"{n0} ≤ N ≤ {N}"
            h.check, h.scales = chk, d.sc_arrow
        elif key.startswith("PRIZE."):
            h.cls = "Pi2" if key != "PRIZE.ae" else "Pi1"
            h.text = text or {
                "PRIZE.1": "Prize problem 1: the centre column is not eventually periodic",
                "PRIZE.2": "Prize problem 2: black and white occur with equal limiting frequency 1/2 "
                           "in the centre column",
                "PRIZE.3": "Prize problem 3: the n-th centre cell can be computed with less than O(n) "
                           "work",
                "PRIZE.ae": "Problems 1 and 2 hold for almost every initial row (fair-coin measure)",
            }[key]
            if key == "PRIZE.1":
                h.check = lambda N: self.build("CC.no.short.period", {"p": 64, "tau": N}).exact()
                h.scales = [1000, 2000, 5000, 10000, 20000] if d.quick else [2000, 5000, 10000, 30000, 60000]
            elif key == "PRIZE.2":
                h.check = self.build("CC.balance.sqrt", {"c": 3}).check
                h.scales = d.sc_bal
        elif key.startswith("IMP."):
            h.cls = "implication"
        elif key.startswith("TAX."):
            pass
        return h

    # -- the conjecture loop -------------------------------------------------------------------
    def loop(self, eng: Engine, key: str, lift: Callable[[Any], Optional[dict]],
             narrow: Optional[Callable[[Any], Optional[Tuple[str, dict]]]] = None, rounds: int = 3):
        """lift(scale) -> params from the data up to `scale`.  Escalate; on a flip, add the narrowed
        finite claim (DERIVED) and re-lift from the data up to the refuting read (DERIVED)."""
        params = lift(None)
        prev = None
        seen = []
        for _ in range(rounds):
            if params is None or params in seen:
                break
            seen.append(params)
            h = eng.add(self.build(key, params, "lift" if prev is None else "re-lift",
                                   deps=[(prev.hid, DERIVED)] if prev else []))
            eng.cascade(h)
            if h.status != REF_ESCALATION or h.profile is None:
                break
            ff = h.profile.first_fail()
            fail_scale = h.profile.reads[ff].scale
            ok_scale = h.profile.reads[ff - 1].scale if ff > 0 else None
            if narrow and ok_scale is not None:
                nk = narrow(ok_scale)
                if nk:
                    hn = eng.add(self.build(nk[0], nk[1], "narrow", deps=[(h.hid, DERIVED)]))
                    eng.cascade(hn)
            prev = h
            params = lift(fail_scale)

    # -- proposer --------------------------------------------------------------------------------
    def propose(self, eng: Engine):
        d, dg = self.d, self.d.diag
        first = lambda s: d.sc_ld[0] if s is None else s  # noqa: E731

        # left diagonals: period divides m
        def lift_div(s):
            N = first(s)
            m = 1
            for D in range(min(N, dg.Dmax + 1)):
                p = dg.period.get(D, 1)
                while m % p:
                    m *= 2
            return {"m": m}
        self.loop(eng, "LD.period.divides", lift_div,
                  lambda N: ("LD.period.divides.below", dict(lift_div(N), N=N)))

        def lift_white(s):
            N = first(s)
            return {"S": [D for D in range(min(N, dg.Dmax + 1)) if dg.white(D)]}
        self.loop(eng, "LD.white.exactly", lift_white,
                  lambda N: ("LD.white.below", dict(lift_white(N), N=N)))
        eng.cascade(eng.add(self.build("LD.white.finite", {}, "registry")))
        eng.cascade(eng.add(self.build("LD.preperiod.gt.D", {})))

        def lift_env(s):
            N = first(s)
            r = [Fraction(dg.pre[D], D) for D in range(20, min(N, dg.Dmax + 1))]
            return {"lo": min(r), "hi": max(r)}
        self.loop(eng, "LD.preperiod.envelope", lift_env)
        law = eng.add(self.build("LD.period.law", {}, "mine"))
        eng.cascade(law)
        db = dg.doubling_points()
        eng.cascade(eng.add(self.build("LD.doubling.below", {"S": db, "N": dg.Dmax + 1}, "measure")))
        eng.cascade(eng.add(self.build("LD.periods.unbounded", {}, "registry", deps=[(law.hid, DERIVED)])))
        eng.cascade(eng.add(self.build("LD.seed.forgetting", {}, "registry")))

        # right diagonals
        eng.cascade(eng.add(self.build("RD.lp.le.2^D", {})))
        eng.cascade(eng.add(self.build("RD.lp.gt.half", {})))

        def lift_rd(s):
            N = d.sc_rd[0] if s is None else s
            for c in (2, 3, 4):
                for b in range(0, c):
                    if all(d.rd(D)[0] == 1 << (D - (D + b) // c) for D in range(N + 1)):
                        return {"b": b, "c": c}
            return None
        self.loop(eng, "RD.lp.formula", lift_rd)

        # centre column
        eng.cascade(eng.add(self.build("CC.no.short.period",
                                       {"p": 64, "tau": 10000 if d.quick else 30000}, "registry")))
        eng.cascade(eng.add(self.build("CC.not.eventually.constant", {}, "registry")))

        def lift_bal(s):
            N = d.sc_bal[0] if s is None else s
            m = max(Fraction(d.path[n] ** 2, n) for n in range(1, min(N, len(d.bits)) + 1))
            c = 1
            while c * c < m:
                c += 1
            return {"c": c}
        self.loop(eng, "CC.balance.sqrt", lift_bal)

        def lift_lc(s):
            N = d.sc_lc[0] if s is None else s
            return {"b": max(abs(2 * d.lc[n] - n) for n in range(1, min(N, len(d.lc) - 1) + 1))}
        self.loop(eng, "CC.lc.near.half", lift_lc)

        def lift_words(s):
            K = 8 if s is None else s
            r = max(Fraction(first_coverage(d.bits, k), k << k) for k in range(1, K + 1))
            for f in (Fraction(1), Fraction(5, 4), Fraction(3, 2), Fraction(2), Fraction(3)):
                if f >= r:
                    return {"f": f}
            return None
        self.loop(eng, "CC.words.cover", lift_words)
        eng.cascade(eng.add(self.build("CC.seed.same", {"seeds": [0b11, 0b101]}, "observe")))
        bal = [h for h in eng.hyps if h.key == "CC.balance.sqrt"][-1]
        eng.cascade(eng.add(self.build("CC.wobble.transport", {}, "transport",
                                       deps=[(bal.hid, USES)])))
        eng.cascade(eng.add(self.build("CC.uniformity.vs.tm", {"more": True}, "measure")))
        eng.cascade(eng.add(self.build("CC.arrow.agreement", {"N": len(d.bits)}, "measure")))
        self.loop(eng, "CC.arrow.below.half", lambda s: {"n0": 1000} if s is None else None)

        # the prize problems and what is proved around them
        for k in ("PRIZE.1", "PRIZE.2", "PRIZE.3", "PRIZE.ae"):
            eng.cascade(eng.add(self.build(k, {}, "registry")))

        # implications the dialogue might be tempted to state
        for key, text in IMPLICATION_TEXTS.items():
            eng.cascade(eng.add(self.build(key, {}, "implication", text=text)))
        return eng

    # -- ground truth (fixed in advance; used only for scoring) ----------------------------------
    def truth(self, h: Hypothesis):
        k, P = h.key, h.params
        if k == "LD.period.divides":
            return False if P.get("m", 0) <= 16 else None
        if k == "LD.period.divides.below":
            m, N = P.get("m"), P.get("N")
            if (m % 8 == 0 and N <= 400) or (m % 16 == 0 and N <= 87867):
                return True
            return False if (m == 8 and N > 400) else None
        if k in ("LD.white.exactly", "LD.white.finite"):
            return False
        if k == "LD.white.below":
            N = P.get("N")
            if N is not None and N <= self.d.diag.Dmax + 1:
                return sorted(P["S"]) == [D for D in range(N) if self.d.diag.white(D)]
            return None
        if k in ("LD.period.law", "LD.seed.forgetting", "RD.lp.le.2^D", "RD.lp.gt.half",
                 "CC.not.eventually.constant", "PRIZE.ae", "TAX.conserved.at.jumps"):
            return True
        if k == "LD.first.period.32":
            return True if P.get("D") == 87867 else None
        if k == "LD.doubling.below":
            N = P.get("N")
            return (sorted(P["S"]) == [D for D in self.d.diag.doubling_points() if D < N]
                    if N and N <= self.d.diag.Dmax + 1 else None)
        if k == "RD.lp.formula":
            b, c = P["b"], P["c"]
            return False if any(self.d.rd(D)[0] != 1 << (D - (D + b) // c) for D in range(13)) else None
        if k == "CC.no.short.period":
            return True if P.get("p", 99) <= 64 and P.get("tau", 10 ** 9) <= 30000 else None
        if k == "CC.balance.sqrt":
            return False if P.get("c", 0) <= 2 else None
        if k == "CC.lc.near.half":
            return False if P.get("b", 99) <= 12 else None
        if k == "CC.wobble.transport":
            return False   # exact: seed 0b111 differs (a finite computed counterexample)
        if k == "CC.uniformity.vs.tm":
            return bool(P.get("more"))
        if k == "CC.arrow.agreement":
            return True
        if k == "CC.arrow.below.half":
            return False   # exact: a computed prefix where at least half the steps follow the arrow
        if k in ("TAX.criterion", "TAX.only.white"):
            return False
        if k in IMPLICATIONS:
            return IMPLICATIONS[k][0]
        return None


IMPLICATION_TEXTS = {
    "IMP.transient.implies.aperiodic": "the centre column's aperiodicity follows from the transient "
                                       "bound (it reads diagonal D inside its transient)",
    "IMP.finite.data.decides.unbounded": "the finite gap data between period doublings implies that "
                                         "the periods are unbounded",
    "IMP.sqrt.wobble.implies.P2": "a bound |D(N)| ≤ C·√N for all large N implies prize problem 2",
    "IMP.arrow.moves.to.half": "the running frequency moves towards 1/2 exactly when the next bit "
                               "follows the observer's arrow −sign D(n)",
    "IMP.survival.implies.truth": "a universal claim that survives every range searched is true",
    "IMP.tax.explains.doubling": "TAX conservation is the mechanism behind the period-doubling law",
}


# -- recognisers: sentence -> (family key, params) ---------------------------------------------
# These let the engine re-gate sentences it did not write (the owner's wheels, other engines'
# reports, a claim typed by a person).  A sentence no recogniser matches is classified by
# auto_claim_class and kept on the wheel with a stated need; it is never spoken as true.

def _ints(s: str) -> List[int]:
    return [int(x) for x in re.findall(r"\d+", s)]


RECOGNISERS: List[Tuple[str, Callable[[re.Match, str], Tuple[str, dict]]]] = [
    (r"eventual period dividing (\d+)", lambda m, t: (
        ("LD.period.divides.below", {"m": int(m.group(1)), "N": int(re.search(r"D\s*<\s*(\d+)", t).group(1))})
        if re.search(r"D\s*<\s*(\d+)", t) else ("LD.period.divides", {"m": int(m.group(1))}))),
    (r"eventually white left diagonals are exactly \[([\d,\s]*)\]",
     lambda m, t: ("LD.white.exactly", {"S": _ints(m.group(1))})),
    (r"transient of left diagonal D is longer than D", lambda m, t: ("LD.preperiod.gt.D", {})),
    (r"(\d+)/(\d+)\s*≤\s*pre\(D\)/D\s*≤\s*(\d+)/(\d+)", lambda m, t: (
        "LD.preperiod.envelope", {"lo": Fraction(int(m.group(1)), int(m.group(2))),
                                  "hi": Fraction(int(m.group(3)), int(m.group(4)))})),
    (r"period exceeds the periods of the two diagonals outside it", lambda m, t: ("LD.period.law", {})),
    (r"first left diagonal with least eventual period 32 is D = (\d+)",
     lambda m, t: ("LD.first.period.32", {"D": int(m.group(1))})),
    (r"periods (?:of the left diagonals are|are truly) unbounded|left-diagonal periods truly unbounded",
     lambda m, t: ("LD.periods.unbounded", {})),
    (r"first differ from the seed only one diagonal past", lambda m, t: ("LD.seed.forgetting", {})),
    (r"least period of right diagonal D divides 2\^D", lambda m, t: ("RD.lp.le.2^D", {})),
    (r"least period of right diagonal D exceeds", lambda m, t: ("RD.lp.gt.half", {})),
    (r"periodic or anti-periodic", lambda m, t: ("RD.periodic.or.anti", {})),
    (r"not eventually periodic with period p\s*≤\s*(\d+) and preperiod\s*≤\s*(\d+)",
     lambda m, t: ("CC.no.short.period", {"p": int(m.group(1)), "tau": int(m.group(2))})),
    (r"≤\s*(\d+)·√N", lambda m, t: ("CC.balance.sqrt", {"c": int(m.group(1))})),
    (r"\|2·L\(n\) − n\|\s*≤\s*(\d+)", lambda m, t: ("CC.lc.near.half", {"b": int(m.group(1))})),
    (r"wobble maximum D\(N\)\^2/N is the same across", lambda m, t: ("CC.wobble.transport", {})),
    (r"centre column is (more|less) uniform than Thue", lambda m, t: (
        "CC.uniformity.vs.tm", {"more": m.group(1) == "more"})),
    (r"aperiodicity \(H16\) follows from the transient bound|aperiodicity follows from the transient",
     lambda m, t: ("IMP.transient.implies.aperiodic", {})),
    (r"\(periods unbounded\) is implied by", lambda m, t: ("IMP.finite.data.decides.unbounded", {})),
    (r"TAX is CONSERVED|TAX conserved at every period doubling",
     lambda m, t: ("TAX.conserved.at.jumps", {})),
    (r"conserved iff c in \{0,\s*a,\s*b\}", lambda m, t: ("TAX.criterion", {})),
    (r"TAX conserved only at white", lambda m, t: ("TAX.only.white", {})),
]

# Needs that a previous wheel stated, matched to what now meets them (a provision with a name).
NEEDS_MET = [
    (r"formalise the TAX defect closed form", "met", "FORMAL TaxChecks.tax_defect_eq, "
     "tax_conserved_iff_defect_zero"),
    (r"test the engine on a fourth domain", "met", "engine v18: general-reasoning and ARC domains in "
     "the same gate loop (see the general and ARC reports)"),
    (r"automatic guard-input derivation", "partly met", "engine v18: RECOGNISERS map sentences to "
     "executable families; unrecognised sentences are classified and kept with a need"),
    (r"guard-extractor for the seed-memory domain", "met", "FORMAL LeftDiagonalPeriods."
     "first_difference_after_white (the seed-memory law is proved, so no guard is needed)"),
    (r"invariant that is NOT forced by white\(D-1\)", "answered (negative for the proposed invariant)",
     "FORMAL DialogueChecks.doubling_law_tie_unsplittable: at a white diagonal the parities of D−1 "
     "and D−2 coincide, so the parity read two out is forced and no data can split the two laws"),
    (r"guard-extractor for the R-calculus domain", "unmet", "no R-calculus pipeline is available to "
     "this engine; the claim stays UNTESTED"),
    (r"extend the automaton run past D=87867", "unmet", "beyond this engine's budget; the needed run "
     "is stated as a range need"),
]


def recognise(text: str) -> Optional[Tuple[str, dict]]:
    for pat, f in RECOGNISERS:
        m = re.search(pat, text)
        if m:
            try:
                return f(m, text)
            except (AttributeError, ValueError):
                return None
    return None


def import_statement(dom: Rule30Domain, text: str, hid: str = "", origin: str = "import") -> Hypothesis:
    r = recognise(text)
    if r is not None:
        key, params = r
        h = dom.build(key, params, origin, text=text)
        if key.startswith("IMP."):
            h.cls = "implication"
    else:
        cls = auto_claim_class(text)
        key = "IMPORT." + re.sub(r"[^a-z0-9]+", ".", text.lower())[:48].strip(".")
        h = Hypothesis("", key, text, cls, "rule30", origin)
    h.hid = ""
    h.params.setdefault("source_hid", hid)
    return h


def turn_wheel(prev: dict, data: R30Data, use_ledger: bool = True) -> dict:
    """Turn a previous wheel: import every entry, re-gate it with v18, and report the movement of
    each entry between rings, with the reason.  Accepts the owner's format (rings with ring
    names "doesn't-know" / "thinks-true" / "thinks-needed") and the v18 format."""
    dom = Rule30Domain(data)
    eng = Engine(use_ledger)
    moves, needs_report, seen = [], [], set()
    rings = prev.get("rings", {})
    for ring, entries in rings.items():
        for e in entries:
            text = e.get("statement", "")
            if ring == "thinks-needed" or e.get("hid", "").startswith("NEEDED"):
                met = _first((st, by) for pat, st, by in NEEDS_MET if re.search(pat, text))
                needs_report.append({"need": e.get("hid"), "statement": text,
                                     "status": met[0] if met else "unmet",
                                     "by": met[1] if met else "no provision recognised"})
                continue
            sig = (text, e.get("hid"))
            if sig in seen:          # the owner's wheel lists some entries twice
                continue
            seen.add(sig)
            if e.get("domain") not in (None, "rule30"):
                continue             # other domains are turned by their own runner
            key = e.get("key", "")
            if key and not key.startswith("IMPORT."):
                # a v18 entry: rebuild it from its family key and parameters (no parsing)
                params = {k: v for k, v in (e.get("params") or {}).items() if k != "source_hid"}
                h = dom.build(key, params, "turn", text=text)
                if key.startswith("IMP."):
                    h.cls = "implication"
                h.params["source_hid"] = e.get("hid", "")
                h = eng.add(h)
            else:
                h = eng.add(import_statement(dom, text, e.get("hid", "")))
            eng.cascade(h)
            if ring == KNOWS and ring_of(h.status) != KNOWS and e.get("status"):
                # merge: keep what the previous wheel knew (Lean: Wheel.merge_sound, knows_merge);
                # this happens when the new run reads smaller ranges than the old one did
                h.note("turn", e["status"], "kept from the previous wheel (this run did not re-derive it)")
                h.backing.extend(e.get("backing") or [])
            elif ring == KNOWS and e.get("status") and answer_of(e["status"]) != answer_of(h.status):
                # two wheels disagree: one of them is unsound (Wheel.conflict_unsound) -- report it
                eng.conflicts.append(f"{e.get('hid')}: previous wheel {e['status']}, now {h.status}")
            moves.append({"was_hid": e.get("hid"), "was_ring": ring, "was_status": e.get("status")
                          or e.get("category"), "statement": text[:160], "key": h.key,
                          "class": h.cls, "now_status": h.status, "now_ring": ring_of(h.status),
                          "reason": h.backing[-1] if h.backing else h.gate_log[-1] if h.gate_log else ""})
    eng.rollback()
    lang = []
    for e in prev.get("language_wheel", []):
        text = e.get("concept", "")
        h = import_statement(dom, text, e.get("hid", ""))
        Engine(use_ledger).cascade(h)
        lang.append({"concept": text[:140], "was_formal": e.get("formal", ""), "now_status": h.status,
                     "now_backing": h.backing[-1] if h.backing else "",
                     "kept_in_language_wheel": ring_of(h.status) == KNOWS})
    return {"moves": moves, "needs": needs_report, "language_recheck": lang, "conflicts": eng.conflicts,
            "wheel": build_wheel(eng, "turned wheel"),
            "summary": Counter(f"{m['was_ring']} -> {m['now_ring']}" for m in moves)}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 8b. Domain: general reasoning (classic claims with known answers, plus any claims file)
# ═════════════════════════════════════════════════════════════════════════════════════════════
# The same gate loop on problems that are not Rule 30.  Each benchmark is a trap that a
# "survived the data, so true" engine falls into; the Lean verdicts are in
# HypothesisEngine/Benchmarks.lean.

def isprime(n: int) -> bool:
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in small:                      # deterministic for n < 3.3 * 10^24
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def _comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    r = 1
    for i in range(k):
        r = r * (n - i) // (i + 1)
    return r


def _is_sum_two_squares(p: int) -> bool:
    a = 0
    while a * a <= p:
        b2 = p - a * a
        b = int(b2 ** 0.5)
        while b * b > b2:
            b -= 1
        while (b + 1) * (b + 1) <= b2:
            b += 1
        if b * b == b2:
            return True
        a += 1
    return False


def _collatz_steps(n: int, cap: int = 10 ** 6) -> Optional[int]:
    k = 0
    while n != 1 and k < cap:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        k += 1
    return k if n == 1 else None


GCD_TRAP_WITNESS = 8424432925592889329288197322308900672459420460792433


def _forall(rng, pred, describe):
    for n in rng:
        if not pred(n):
            return False, describe(n)
    return True, f"all n in [{rng.start}, {rng.stop})"


class GeneralDomain:
    name = "general"

    def build(self, key: str, params: dict, origin: str = "registry", text: str = "") -> Hypothesis:
        h = Hypothesis("", key, text, "Pi1", "general", origin, dict(params))
        if key == "GEN.euler.prime":
            h.text = text or "n² + n + 41 is prime for every n ≥ 0"
            h.check = lambda N: _forall(range(0, N), lambda n: isprime(n * n + n + 41),
                                        lambda n: f"n = {n}: {n * n + n + 41} is not prime")
            h.scales = [10, 20, 30, 40, 100]
        elif key == "GEN.euler.prime.below40":
            h.cls = "finite"
            h.text = text or "n² + n + 41 is prime for every n < 40"
            h.exact = lambda: _forall(range(0, 40), lambda n: isprime(n * n + n + 41),
                                      lambda n: f"n = {n} fails")
        elif key == "GEN.fermat.prime":
            h.text = text or "every Fermat number 2^(2^n) + 1 is prime"
            h.check = lambda N: _forall(range(0, N + 1), lambda n: isprime(2 ** (2 ** n) + 1),
                                        lambda n: f"n = {n}: 2^(2^{n}) + 1 = {2 ** (2 ** n) + 1} is "
                                        f"divisible by 641" if n == 5 else f"n = {n} fails")
            h.scales = [1, 2, 3, 4, 6]
        elif key == "GEN.fermat.coprime":
            h.text = text or "distinct Fermat numbers are coprime"
            F = lambda n: 2 ** (2 ** n) + 1  # noqa: E731
            h.check = lambda N: _forall(range(1, N + 1), lambda n: all(_gcd(F(m), F(n)) == 1
                                                                       for m in range(n)),
                                        lambda n: f"n = {n} fails")
            h.scales = [2, 3, 4, 6, 9]
        elif key == "GEN.two.squares":
            h.text = text or "an odd prime p is a sum of two squares exactly when p ≡ 1 (mod 4)"
            h.check = lambda N: _forall(range(3, N), lambda p: not isprime(p) or
                                        (_is_sum_two_squares(p) == (p % 4 == 1)),
                                        lambda p: f"p = {p} fails")
            h.scales = [100, 1000, 5000, 20000, 50000]
        elif key == "GEN.circle.regions":
            h.text = text or "n points in general position on a circle cut the disc into 2^(n−1) regions"
            h.check = lambda N: _forall(range(1, N + 1), lambda n: _comb(n, 4) + _comb(n, 2) + 1 == 2 ** (n - 1),
                                        lambda n: f"n = {n}: {_comb(n, 4) + _comb(n, 2) + 1} regions, "
                                        f"not {2 ** (n - 1)}")
            h.scales = [3, 4, 5, 6, 10]
        elif key == "GEN.josephus":
            h.text = text or ("in the Josephus problem with every second person removed, the survivor "
                              "is 2(n − 2^⌊log₂ n⌋) + 1")

            def chk(N):
                j = 0
                for n in range(1, N + 1):
                    if n > 1:
                        j = (j + 2) % n
                    if j + 1 != 2 * (n - (1 << (n.bit_length() - 1))) + 1:
                        return False, f"n = {n} fails"
                return True, f"1 ≤ n ≤ {N} (simulated)"
            h.check, h.scales = chk, [16, 64, 256, 1024, 4096]
        elif key == "GEN.collatz.bound":
            h.text = text or "every positive integer reaches 1 within 100 Collatz steps"
            h.check = lambda N: _forall(range(1, N + 1), lambda n: (_collatz_steps(n, 101) if _collatz_steps(n, 101) is not None else 999) <= 100,
                                        lambda n: f"n = {n} needs {_collatz_steps(n)} steps")
            h.scales = [10, 20, 26, 50, 100]
        elif key == "GEN.collatz":
            h.cls = "Pi2"
            h.text = text or "every positive integer eventually reaches 1 under the Collatz map"
            h.check = lambda N: _forall(range(1, N + 1), lambda n: _collatz_steps(n) is not None,
                                        lambda n: f"n = {n} not seen to reach 1")
            h.scales = [100, 1000, 10000, 30000, 100000]
        elif key == "GEN.gcd.trap":
            h.text = text or "gcd(n^17 + 9, (n + 1)^17 + 9) = 1 for every n ≥ 0"
            h.check = lambda N: _forall(range(0, N), lambda n: _gcd(n ** 17 + 9, (n + 1) ** 17 + 9) == 1,
                                        lambda n: f"n = {n} fails")
            h.scales = [100, 1000, 3000, 10000, 20000]
        return h

    def propose(self, eng: Engine, claims_file: Optional[Path] = None):
        for key in ("GEN.euler.prime", "GEN.fermat.prime", "GEN.fermat.coprime", "GEN.two.squares",
                    "GEN.circle.regions", "GEN.josephus", "GEN.collatz.bound", "GEN.collatz",
                    "GEN.gcd.trap"):
            h = eng.add(self.build(key, {}))
            eng.cascade(h)
            if key == "GEN.euler.prime" and is_refuted(h.status):
                hn = self.build("GEN.euler.prime.below40", {}, "narrow")
                hn.deps = [(h.hid, DERIVED)]
                eng.cascade(eng.add(hn))
            if key == "GEN.gcd.trap" and is_refuted(h.status):
                n = GCD_TRAP_WITNESS
                g = _gcd(n ** 17 + 9, (n + 1) ** 17 + 9)
                h.backing.append(f"EXACT the cited witness n = {n} is recomputed here: gcd = {g} ≠ 1")
        if claims_file:
            for h in load_claims_file(claims_file):
                eng.cascade(eng.add(h))
        return eng

    def truth(self, h: Hypothesis):
        return {"GEN.euler.prime": False, "GEN.euler.prime.below40": True, "GEN.fermat.prime": False,
                "GEN.fermat.coprime": True, "GEN.two.squares": True, "GEN.circle.regions": False,
                "GEN.josephus": True, "GEN.collatz.bound": False, "GEN.collatz": None,
                "GEN.gcd.trap": False}.get(h.key, h.truth)    # "unset": not scored


_SAFE = {"isprime": isprime, "gcd": _gcd, "comb": _comb, "abs": abs, "min": min, "max": max,
         "sum": sum, "range": range, "all": all, "any": any, "len": len, "pow": pow, "int": int,
         "Fraction": Fraction, "divmod": divmod, "bin": bin, "sorted": sorted, "set": set}


def load_claims_file(path: Path) -> List[Hypothesis]:
    """A JSON list of claims, e.g.
        [{"key": "MY.squares.mod4", "text": "n² mod 4 is 0 or 1",
          "test": "n*n % 4 in (0, 1)", "class": "Pi1", "scales": [10, 100, 1000, 10000, 100000]},
         {"key": "MY.small", "text": "...", "test": "...", "class": "finite", "range": [0, 500]},
         {"key": "MY.idea", "text": "the wobble is like a pendulum"}]          # no test: kept untested
    `test` is a Python expression in the integer n, evaluated with a small whitelist of functions
    (no imports, no attribute access).  A claims file can never make the engine say "proved"."""
    out = []
    for c in json.loads(Path(path).read_text()):
        text = c.get("text", "")
        cls = c.get("class") or auto_claim_class(text)
        h = Hypothesis("", c.get("key") or ("CLAIM." + re.sub(r"\W+", ".", text.lower())[:40]),
                       text, cls, "general", "claims-file")
        h.truth = c.get("truth", "unset")
        expr = c.get("test")
        if expr and re.search(r"__|\bimport\b|\.\s*[a-zA-Z_]", expr.replace("Fraction", "")) is None:
            code = compile(expr, "<claim>", "eval")
            f = lambda n, code=code: bool(eval(code, dict(_SAFE, n=n, __builtins__={})))  # noqa
            if cls == "finite" and c.get("range"):
                lo, hi = c["range"]
                h.exact = lambda lo=lo, hi=hi, f=f: _forall(range(lo, hi), f, lambda n: f"n = {n} fails")
            elif c.get("scales"):
                lo = c.get("start", 0)
                h.check = lambda N, lo=lo, f=f: _forall(range(lo, N), f, lambda n: f"n = {n} fails")
                h.scales = list(c["scales"])[:5]
        out.append(h)
    return out


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 8c. Domain: ARC-style grid puzzles
# ═════════════════════════════════════════════════════════════════════════════════════════════
# A program is a short chain of steps.  A step either needs no parameters (a symmetry, gravity,
# a crop) or fits its parameters from the demonstrations (a colour map, a tiling of transforms, a
# periodic tile, ...).  The solver ANSWERS ONLY WHEN EVERY CONSISTENT PROGRAM OF LEAST DEPTH
# AGREES on the test input (Lean: PlanSearch -- the planner is correct whenever the truth is a
# cheapest explanation, and when consistent chains disagree, a separating cell exists).  When it
# refuses, it states a NEED from the demonstrations alone, and the wheel supplies the step
# families that serve that need.  Every answer is a hypothesis: "program P explains every
# demonstration" is a finite claim (verified exactly); "P's output on the test is right" is a
# prediction that only the hidden answer can settle.

Grid = Tuple[Tuple[int, ...], ...]


def G(rows) -> Grid:
    return tuple(tuple(int(x) for x in r) for r in rows)


def shape(g: Grid) -> Tuple[int, int]:
    return (len(g), len(g[0]) if g else 0)


def flip_h(g): return G(r[::-1] for r in g)
def flip_v(g): return G(g[::-1])
def transpose(g): return G(zip(*g))
def rot90(g): return flip_h(transpose(g))
def rot180(g): return flip_v(flip_h(g))
def rot270(g): return transpose(flip_h(g))


D4 = [("id", lambda g: g), ("flip_h", flip_h), ("flip_v", flip_v), ("transpose", transpose),
      ("rot90", rot90), ("rot180", rot180), ("rot270", rot270),
      ("antitranspose", lambda g: rot180(transpose(g)))]


def colours(g: Grid) -> set:
    return {x for r in g for x in r}


def objects(g: Grid, diag: bool = False, multicolour: bool = False) -> List[List[Tuple[int, int]]]:
    H, W = shape(g)
    seen, out = set(), []
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1)] + ([(-1, -1), (-1, 1), (1, -1), (1, 1)] if diag else [])
    for r in range(H):
        for c in range(W):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            col, comp, stack = g[r][c], [], [(r, c)]
            seen.add((r, c))
            while stack:
                a, b = stack.pop()
                comp.append((a, b))
                for da, db in nb:
                    x, y = a + da, b + db
                    if 0 <= x < H and 0 <= y < W and (x, y) not in seen and g[x][y] != 0 and \
                            (multicolour or g[x][y] == col):
                        seen.add((x, y))
                        stack.append((x, y))
            out.append(comp)
    return out


def crop(g: Grid, cells) -> Optional[Grid]:
    if not cells:
        return None
    rs, cs = [r for r, _ in cells], [c for _, c in cells]
    return G(row[min(cs):max(cs) + 1] for row in g[min(rs):max(rs) + 1])


def crop_nonbg(g):
    return crop(g, [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c]])


def crop_largest(g):
    objs = objects(g, diag=True, multicolour=True)
    if not objs:
        return None
    sizes = sorted((len(o) for o in objs), reverse=True)
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        return None
    return crop(g, max(objs, key=len))


def gravity(g, d):
    t = {0: lambda x: x, 1: flip_v, 2: lambda x: rot90(x), 3: lambda x: rot270(x)}[d]
    inv = {0: lambda x: x, 1: flip_v, 2: lambda x: rot270(x), 3: lambda x: rot90(x)}[d]
    h = t(g)
    cols = list(zip(*h))
    new = []
    for col in cols:
        nz = [x for x in col if x]
        new.append([0] * (len(col) - len(nz)) + nz)
    return inv(G(zip(*new)))


def mirror_fill(g, mode):
    H, W = shape(g)
    out = [list(r) for r in g]
    for r in range(H):
        for c in range(W):
            if out[r][c] == 0:
                cands = []
                if mode in ("h", "hv"):
                    cands.append(g[r][W - 1 - c])
                if mode in ("v", "hv"):
                    cands.append(g[H - 1 - r][c])
                if mode == "hv":
                    cands.append(g[H - 1 - r][W - 1 - c])
                if mode == "t" and H == W:
                    cands.append(g[c][r])
                nz = {x for x in cands if x}
                if len(nz) > 1:
                    return None
                if nz:
                    out[r][c] = nz.pop()
    return G(out)


def swap_in_objects(g):
    out = [list(r) for r in g]
    for o in objects(g, diag=True, multicolour=True):
        cs = {g[r][c] for r, c in o}
        if len(cs) == 2:
            a, b = sorted(cs)
            for r, c in o:
                out[r][c] = b if g[r][c] == a else a
    return G(out)


def count_to_row(g):
    cs = colours(g) - {0}
    if len(cs) != 1:
        return None
    n = sum(1 for r in g for x in r if x)
    return G([[cs.pop()] * n]) if n else None


def fill_enclosed(g, colour):
    H, W = shape(g)
    seen = set()
    stack = [(r, c) for r in range(H) for c in range(W) if (r in (0, H - 1) or c in (0, W - 1)) and g[r][c] == 0]
    seen.update(stack)
    while stack:
        a, b = stack.pop()
        for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
            if 0 <= x < H and 0 <= y < W and (x, y) not in seen and g[x][y] == 0:
                seen.add((x, y))
                stack.append((x, y))
    return G([[colour if g[r][c] == 0 and (r, c) not in seen else g[r][c] for c in range(W)]
              for r in range(H)])


def upscale(g, k):
    return G([x for x in r for _ in range(k)] for r in g for _ in range(k))


@dataclass
class Step:
    name: str
    family: str                                     # the need it serves (primitive:<family>)
    apply: Callable[[Grid, Any], Optional[Grid]]
    fit: Optional[Callable[[list], List[Any]]] = None    # demos -> candidate params ([] = cannot fit)

    def candidates(self, pairs) -> List[Any]:
        return [()] if self.fit is None else self.fit(pairs)


def _same_shapes(pairs):
    return all(shape(a) == shape(b) for a, b in pairs)


def fit_colour_map(pairs) -> List[dict]:
    if not _same_shapes(pairs):
        return []
    m: Dict[int, int] = {}
    for a, b in pairs:
        for ra, rb in zip(a, b):
            for x, y in zip(ra, rb):
                if m.setdefault(x, y) != y:
                    return []
    return [m]


def apply_colour_map(g, m):
    if not colours(g) <= set(m):
        return None
    return G([m[x] for x in r] for r in g)


TRANS = D4


def fit_tiling(pairs) -> List[Any]:
    """Output = an a×b arrangement of blocks; block (i, j) = colour-map(T_ij(input)), T in D4."""
    ratios = set()
    for a, b in pairs:
        (h, w), (H, W) = shape(a), shape(b)
        if h == 0 or H % h or W % w:
            return []
        ratios.add((H // h, W // w))
    if len(ratios) != 1:
        return []
    A, B = ratios.pop()
    if (A, B) == (1, 1):
        return []
    blocks = {}
    for i in range(A):
        for j in range(B):
            cands = []
            for tn, tf in TRANS:
                ps = []
                for a, b in pairs:
                    h, w = shape(a)
                    blk = G(r[j * w:(j + 1) * w] for r in b[i * h:(i + 1) * h])
                    ta = tf(a)
                    if shape(ta) != shape(blk):
                        break
                    ps.append((ta, blk))
                else:
                    cm = fit_colour_map(ps)
                    if cm:
                        cands.append((tn, cm[0]))
            if not cands:
                return []
            blocks[(i, j)] = cands
    return [(A, B, blocks)]


def apply_tiling(g, params):
    A, B, blocks = params
    h, w = shape(g)
    out = [[0] * (w * B) for _ in range(h * A)]
    tf = dict(TRANS)
    for (i, j), cands in blocks.items():
        results = set()
        for tn, cm in cands:
            ta = tf[tn](g)
            if shape(ta) != (h, w):
                return None
            r = apply_colour_map(ta, cm)
            if r is None:
                return None
            results.add(r)
        if len(results) != 1:
            return None              # the demonstrations do not determine this block
        blk = results.pop()
        for r in range(h):
            for c in range(w):
                out[i * h + r][j * w + c] = blk[r][c]
    return G(out)


def _scale_rules(g):
    return {"const": None, "ncolours": len(colours(g) - {0}), "ncells": sum(1 for r in g for x in r if x)}


def fit_scale(pairs):
    out = []
    for rule in ("const", "ncolours", "ncells"):
        ks = set()
        for a, b in pairs:
            (h, w), (H, W) = shape(a), shape(b)
            if h == 0 or H % h or H // h != W // max(w, 1) or W % w:
                return out
            k = H // h
            if upscale(a, k) != b:
                return out
            ks.add(k if rule == "const" else (k, _scale_rules(a)[rule]))
        if rule == "const" and len(ks) == 1:
            out.append(("const", ks.pop()))
        elif rule != "const" and all(k == v for k, v in ks):
            out.append((rule, None))
    return out


def apply_scale(g, p):
    rule, k = p
    k = k if rule == "const" else _scale_rules(g)[rule]
    return upscale(g, k) if k and k <= 10 else None


def _period_tile(g, hole):
    H, W = shape(g)
    best = None
    for area in range(1, H * W + 1):
        for py in range(1, H + 1):
            if area % py:
                continue
            px = area // py
            if px > W:
                continue
            for s in range(px):
                tile: Dict[Tuple[int, int], int] = {}
                ok = True
                for r in range(H):
                    for c in range(W):
                        v = g[r][c]
                        if v == hole:
                            continue
                        key = (r % py, (c - s * (r // py)) % px)
                        if tile.setdefault(key, v) != v:
                            ok = False
                            break
                    if not ok:
                        break
                if ok and len(tile) == py * px:
                    best = (py, px, s, tile)
                    return best
        if area > (H * W) // 2:
            break
    return best


def fit_periodic(pairs):
    if not _same_shapes(pairs):
        return []
    holes = set()
    for a, b in pairs:
        for ra, rb in zip(a, b):
            for x, y in zip(ra, rb):
                if x != y:
                    holes.add(x)
    if len(holes) != 1:
        return []
    hole = holes.pop()
    for a, b in pairs:
        if apply_periodic(a, hole) != b:
            return []
    return [hole]


def apply_periodic(g, hole):
    t = _period_tile(g, hole)
    if t is None:
        return None
    py, px, s, tile = t
    H, W = shape(g)
    return G([[g[r][c] if g[r][c] != hole else tile[(r % py, (c - s * (r // py)) % px)]
               for c in range(W)] for r in range(H)])


def _blocks(g, oh, ow):
    """Split g into equal blocks of shape (oh, ow) along one axis, allowing 1-cell separators."""
    H, W = shape(g)
    res = []
    for sep in (0, 1):
        if W == ow and (H + sep) % (oh + sep) == 0 and (H + sep) // (oh + sep) >= 2:
            k = (H + sep) // (oh + sep)
            res.append([G(g[i * (oh + sep): i * (oh + sep) + oh]) for i in range(k)])
        if H == oh and (W + sep) % (ow + sep) == 0 and (W + sep) // (ow + sep) >= 2:
            k = (W + sep) // (ow + sep)
            res.append([G(r[i * (ow + sep): i * (ow + sep) + ow] for r in g) for i in range(k)])
    return res


BLOCK_PREDICATES = {
    "asymmetric": lambda b, bs: b != transpose(b) if shape(b)[0] == shape(b)[1] else False,
    "unique": lambda b, bs: sum(1 for x in bs if x == b) == 1,
    "most-cells": lambda b, bs: sum(x != 0 for r in b for x in r) ==
    max(sum(x != 0 for r in y for x in r) for y in bs),
    "fewest-cells": lambda b, bs: sum(x != 0 for r in b for x in r) ==
    min(sum(x != 0 for r in y for x in r) for y in bs),
    "unique-colours": lambda b, bs: sum(1 for y in bs if colours(y) == colours(b)) == 1,
}


def fit_select_block(pairs):
    out = []
    for name, pred in BLOCK_PREDICATES.items():
        if all(apply_select_block(a, name, shape(b)) == b for a, b in pairs):
            out.append((name, shape(pairs[0][1])))
    return out


def apply_select_block(g, name, oshape=None):
    for oh, ow in ([oshape] if oshape else []):
        for bs in _blocks(g, oh, ow):
            sel = [b for b in bs if BLOCK_PREDICATES[name](b, bs)]
            if len(sel) == 1:
                return sel[0]
    return None


BOOL_OPS = {"and": lambda x, y: x and y, "or": lambda x, y: x or y, "xor": lambda x, y: x != y,
            "nor": lambda x, y: not (x or y), "a-not-b": lambda x, y: x and not y,
            "b-not-a": lambda x, y: y and not x}


def _halves(g, oshape):
    """The ways to split g into two halves of shape oshape: (axis, sep, first, second)."""
    H, W = shape(g)
    oh, ow = oshape
    res = []
    for sep in (0, 1):
        if W == ow and H == 2 * oh + sep:
            res.append(("rows", sep, G(g[:oh]), G(g[oh + sep:])))
        if H == oh and W == 2 * ow + sep:
            res.append(("cols", sep, G(r[:ow] for r in g), G(r[ow + sep:] for r in g)))
    return res


def _split(g, axis, sep):
    H, W = shape(g)
    if axis == "rows":
        oh = (H - sep) // 2
        if 2 * oh + sep != H or oh <= 0:
            return None
        return G(g[:oh]), G(g[oh + sep:])
    ow = (W - sep) // 2
    if 2 * ow + sep != W or ow <= 0:
        return None
    return G(r[:ow] for r in g), G(r[ow + sep:] for r in g)


def fit_boolean(pairs):
    out = []
    layouts = None
    for a, b in pairs:
        ls = {(ax, sep) for ax, sep, _, _ in _halves(a, shape(b))}
        layouts = ls if layouts is None else layouts & ls
    for ax, sep in sorted(layouts or ()):
        for op in BOOL_OPS:
            cols, ok = set(), True
            for a, b in pairs:
                x, y = _split(a, ax, sep)
                for r in range(len(b)):
                    for c in range(len(b[0])):
                        if (b[r][c] != 0) != bool(BOOL_OPS[op](x[r][c] != 0, y[r][c] != 0)):
                            ok = False
                            break
                        if b[r][c]:
                            cols.add(b[r][c])
                    if not ok:
                        break
                if not ok:
                    break
            if ok and len(cols) == 1:
                out.append((op, cols.pop(), ax, sep))
    return out


def apply_boolean(g, p):
    op, col, ax, sep = p
    s = _split(g, ax, sep)
    if s is None:
        return None
    x, y = s
    return G([[col if BOOL_OPS[op](x[r][c] != 0, y[r][c] != 0) else 0 for c in range(len(x[0]))]
              for r in range(len(x))])


def _obj_feature(name, g, o, objs):
    size = len(o)
    if name == "size":
        return size
    if name.startswith("size>="):
        return size >= int(name[6:])
    if name == "largest":
        return size == max(len(x) for x in objs)
    if name == "smallest":
        return size == min(len(x) for x in objs)
    if name == "shape":
        r0, c0 = min(r for r, _ in o), min(c for _, c in o)
        return tuple(sorted((r - r0, c - c0) for r, c in o))
    if name == "colour+size":
        return (g[o[0][0]][o[0][1]], size)
    return None


OBJ_FEATURES = ["largest", "smallest"] + [f"size>={k}" for k in range(2, 9)] + ["shape", "size", "colour+size"]


def fit_recolour(pairs):
    if not _same_shapes(pairs):
        return []
    out = []
    for feat in OBJ_FEATURES:
        table: Dict[Any, int] = {}
        ok = True
        for a, b in pairs:
            objs = objects(a)
            covered = set()
            for o in objs:
                newc = {b[r][c] for r, c in o}
                if len(newc) != 1:
                    ok = False
                    break
                key = (a[o[0][0]][o[0][1]], _obj_feature(feat, a, o, objs))
                if table.setdefault(key, newc.pop()) != b[o[0][0]][o[0][1]]:
                    ok = False
                    break
                covered.update(o)
            if not ok:
                break
            if any(a[r][c] != b[r][c] for r in range(len(a)) for c in range(len(a[0])) if (r, c) not in covered):
                ok = False
                break
        if ok and any(k[0] != v for k, v in table.items()):
            out.append((feat, table))
    return out


def apply_recolour(g, p):
    feat, table = p
    out = [list(r) for r in g]
    objs = objects(g)
    for o in objs:
        key = (g[o[0][0]][o[0][1]], _obj_feature(feat, g, o, objs))
        if key not in table:
            return None
        for r, c in o:
            out[r][c] = table[key]
    return G(out)


def fit_fill_enclosed(pairs):
    if not _same_shapes(pairs):
        return []
    cols = set()
    for a, b in pairs:
        for ra, rb in zip(a, b):
            for x, y in zip(ra, rb):
                if x != y:
                    cols.add(y)
    return [c for c in cols if all(fill_enclosed(a, c) == b for a, b in pairs)]


STEP_LIBRARY: Dict[str, Step] = {}


def _reg(step: Step):
    STEP_LIBRARY[step.name] = step


for _n, _f in D4[1:]:
    _reg(Step(_n, "symmetry", lambda g, p, f=_f: f(g)))
_reg(Step("colour_map", "recolour", apply_colour_map, fit_colour_map))
_reg(Step("recolour_by_feature", "recolour", apply_recolour, fit_recolour))
_reg(Step("swap_in_objects", "recolour", lambda g, p: swap_in_objects(g)))
_reg(Step("tiling", "arrange", apply_tiling, fit_tiling))
_reg(Step("scale", "arrange", apply_scale, fit_scale))
_reg(Step("crop_nonbg", "select", lambda g, p: crop_nonbg(g)))
_reg(Step("crop_largest", "select", lambda g, p: crop_largest(g)))
_reg(Step("select_block", "select", lambda g, p: apply_select_block(g, p[0], p[1]), fit_select_block))
_reg(Step("boolean_halves", "select", apply_boolean, fit_boolean))
_reg(Step("count_to_row", "count", lambda g, p: count_to_row(g)))
_reg(Step("periodic_fill", "fill", apply_periodic, fit_periodic))
_reg(Step("fill_enclosed", "fill", lambda g, p: fill_enclosed(g, p), fit_fill_enclosed))
for _d, _nm in enumerate(("down", "up", "right", "left")):
    _reg(Step(f"gravity_{_nm}", "move", lambda g, p, d=_d: gravity(g, d)))
for _m in ("h", "v", "hv", "t"):
    _reg(Step(f"mirror_fill_{_m}", "move", lambda g, p, m=_m: mirror_fill(g, m)))

BASE_STEPS = [n for n, _ in D4[1:]] + ["colour_map"]
PROVISION_FAMILIES = {f: [n for n, s in STEP_LIBRARY.items() if s.family == f and n not in BASE_STEPS]
                      for f in ("recolour", "arrange", "select", "count", "fill", "move")}


def _run(step: Step, params, g):
    try:
        return step.apply(g, params)
    except (IndexError, ValueError, KeyError, ZeroDivisionError, TypeError, RecursionError):
        return None


def solve_arc(demos, test_in, step_names: List[str]):
    """Least-depth consistent programs; answer iff they all agree on the test input.
    Returns (answer or None, programs, note)."""
    if all(a == b for a, b in demos):
        return test_in, ["identity"], "identity"
    steps = [STEP_LIBRARY[n] for n in step_names]
    pre_steps = [s for s in steps if s.fit is None]
    for depth in (1, 2):
        answers: Dict[Grid, List[str]] = {}
        chains = [(None, s) for s in steps] if depth == 1 else [(p, s) for p in pre_steps for s in steps]
        for pre, last in chains:
            ins, t = [a for a, _ in demos], test_in
            if pre is not None:
                ins = [_run(pre, (), a) for a in ins]
                t = _run(pre, (), t)
                if t is None or any(x is None for x in ins):
                    continue
            pairs = list(zip(ins, [b for _, b in demos]))
            try:
                cands = last.candidates(pairs)
            except (IndexError, ValueError, KeyError, ZeroDivisionError, TypeError):
                cands = []
            for params in cands:
                outs = [_run(last, params, a) for a in ins]
                if outs != [b for _, b in demos]:
                    continue
                r = _run(last, params, t)
                if r is not None:
                    name = (pre.name + "+" if pre else "") + last.name
                    answers.setdefault(r, []).append(name)
        if answers:
            if len(answers) == 1:
                (ans, progs), = answers.items()
                return ans, progs, f"depth {depth}: {len(progs)} consistent program(s) agree"
            return None, sorted(p for v in answers.values() for p in v)[:6], \
                f"depth {depth}: {len(answers)} different answers (a separating cell exists)"
    return None, [], "no consistent program"


def diagnose_arc(demos) -> List[Need]:
    """Needs stated from the demonstrations alone (never from the hidden answer)."""
    sigs = set()
    for a, b in demos:
        (h, w), (H, W) = shape(a), shape(b)
        if (h, w) != (H, W):
            if H == 1 and W != w:
                sigs.add("count")
            elif H >= h and W >= w and H % h == 0 and W % w == 0:
                sigs.add("arrange")
            elif H <= h and W <= w:
                sigs.add("select")
            else:
                sigs.add("unknown")
            continue
        changed = [(r, c) for r in range(h) for c in range(w) if a[r][c] != b[r][c]]
        if not changed:
            continue
        if all(a[r][c] == 0 for r, c in changed) or len({a[r][c] for r, c in changed}) == 1:
            sigs.add("fill")
        if Counter(x for r in a for x in r) == Counter(x for r in b for x in r):
            sigs.add("move")
        if all(b[r][c] != 0 for r, c in changed) and all(a[r][c] != 0 for r, c in changed):
            sigs.add("recolour")
        if not sigs:
            sigs.add("unknown")
    if not sigs:
        sigs.add("unknown")
    return [Need("primitive", f"primitive:{s}", f"the demonstrations need a step of kind '{s}'", [],
                 "the puzzles that need it are answered") for s in sorted(sigs)]


# -- synthetic puzzle families (ground truth by construction) -----------------------------------

def _rand_grid(rng, h, w, density=0.4, cols=(1, 2, 3, 4, 5)):
    return G([[rng.choice(cols) if rng.random() < density else 0 for _ in range(w)] for _ in range(h)])


def _family_examples(rng, fam):
    h, w = rng.randint(3, 6), rng.randint(3, 6)
    if fam == "flip+recolour":
        m = {0: 0, 1: 2, 2: 3, 3: 1, 4: 4, 5: 5}
        f = lambda g: apply_colour_map(flip_h(g), m)  # noqa: E731
        return lambda: _rand_grid(rng, h, w), f
    if fam == "gravity":
        return lambda: _rand_grid(rng, h, w, 0.3), lambda g: gravity(g, 0)
    if fam == "mirror-tile":
        return lambda: _rand_grid(rng, 3, 3), lambda g: apply_tiling(
            g, (1, 2, {(0, 0): [("id", {x: x for x in range(10)})],
                       (0, 1): [("flip_h", {x: x for x in range(10)})]}))
    if fam == "scale":
        k = rng.randint(2, 3)
        return lambda: _rand_grid(rng, 3, 3), lambda g: upscale(g, k)
    if fam == "periodic":
        py, px = rng.randint(2, 3), rng.randint(2, 3)
        tile = [[rng.randint(1, 5) for _ in range(px)] for _ in range(py)]
        H, W = 8, 8

        def make():
            full = [[tile[r % py][c % px] for c in range(W)] for r in range(H)]
            r0, c0 = rng.randint(0, H - 3), rng.randint(0, W - 3)
            for r in range(r0, r0 + 2):
                for c in range(c0, c0 + 3):
                    full[r][c] = 0
            return G(full)
        return make, lambda g: apply_periodic(g, 0)
    if fam == "select-odd":
        def make():
            base = _rand_grid(rng, 3, 3, 0.5, (2,))
            odd = _rand_grid(rng, 3, 3, 0.5, (2, 7))
            bs = [base, base, base]
            bs[rng.randint(0, 2)] = odd if odd != base else upscale(G([[7]]), 3)
            return G([r for b in bs for r in b])
        return make, lambda g: apply_select_block(g, "unique", (3, 3))
    if fam == "boolean":
        def make():
            a = _rand_grid(rng, 4, 4, 0.5, (1,))
            b = _rand_grid(rng, 4, 4, 0.5, (2,))
            return G([ra + (5,) + rb for ra, rb in zip(a, b)])
        return make, lambda g: apply_boolean(g, ("and", 3, "cols", 1))
    if fam == "recolour-size":
        def make():
            g = [[0] * 8 for _ in range(8)]
            for _ in range(3):
                r, c, n = rng.randint(0, 6), rng.randint(0, 6), rng.randint(1, 4)
                for i in range(n):
                    if c + i < 8:
                        g[r][c + i] = 1
            return G(g)
        return make, lambda g: apply_recolour(g, ("size>=3", {(1, True): 4, (1, False): 1}))
    if fam == "count":
        return lambda: _rand_grid(rng, 3, 3, 0.4, (6,)), count_to_row
    if fam == "crop":
        def make():
            g = [[0] * 8 for _ in range(8)]
            r, c = rng.randint(0, 5), rng.randint(0, 5)
            for i in range(3):
                for j in range(3):
                    if rng.random() < 0.7 or (i, j) == (0, 0) or (i, j) == (2, 2):
                        g[r + i][c + j] = rng.randint(1, 5)
            return G(g)
        return make, crop_nonbg
    raise ValueError(fam)


ARC_FAMILIES = ["flip+recolour", "gravity", "mirror-tile", "scale", "periodic", "select-odd",
                "boolean", "recolour-size", "count", "crop"]


def make_synthetic(seed: int, per_family: int, n_demo: int = 3) -> List[dict]:
    rng = random.Random(seed)
    out = []
    for fam in ARC_FAMILIES:
        for _ in range(per_family):
            make, f = _family_examples(rng, fam)
            ex = []
            tries = 0
            while len(ex) < n_demo + 1 and tries < 50:
                tries += 1
                g = make()
                y = f(g)
                if y is not None and y != g:
                    ex.append((g, y))
            if len(ex) == n_demo + 1:
                out.append({"family": fam, "demos": ex[:n_demo], "test_in": ex[-1][0], "test_out": ex[-1][1]})
    return out


def load_arc_zip(zip_path: Path, prefix: str = "glm_repo/overlay/arc_agi_17/data/training/") -> List[dict]:
    tasks = []
    with zipfile.ZipFile(zip_path) as z:
        for name in sorted(z.namelist()):
            if name.startswith(prefix) and name.endswith(".json"):
                tasks.extend(_arc_task(json.loads(z.read(name)), os.path.basename(name)[:-5]))
    return tasks


def load_arc_dir(d: Path) -> List[dict]:
    tasks = []
    for p in sorted(Path(d).glob("*.json")):
        tasks.extend(_arc_task(json.loads(p.read_text()), p.stem))
    return tasks


def _arc_task(d: dict, name: str) -> List[dict]:
    demos = [(G(p["input"]), G(p["output"])) for p in d["train"]]
    return [{"family": f"{name}#{k}", "demos": demos, "test_in": G(t["input"]),
             "test_out": G(t["output"]) if "output" in t else None} for k, t in enumerate(d["test"])]


def run_arc(puzzles: List[dict], seed: int = 18, random_draws: int = 5) -> dict:
    """The needs-wheel measurement on ARC puzzles.
    Conditions: base steps only; on-demand (each puzzle's stated needs served by the wheel);
    all provisions; random provision sets of the same size as the on-demand sets (control)."""
    def outcome(ans, p):
        if ans is None:
            return "refused"
        if p["test_out"] is None:
            return "answered (no key)"
        return "right" if ans == p["test_out"] else "wrong"

    res = {"puzzles": len(puzzles)}
    per = []
    base_c, od_c, all_c = Counter(), Counter(), Counter()
    need_counts, sizes = Counter(), []
    all_steps = list(STEP_LIBRARY)
    for p in puzzles:
        a0, progs0, note0 = solve_arc(p["demos"], p["test_in"], BASE_STEPS)
        o0 = outcome(a0, p)
        base_c[o0] += 1
        needs = diagnose_arc(p["demos"]) if a0 is None else []
        need_counts.update(n.signature for n in needs)
        served = sorted({s for n in needs for s in PROVISION_FAMILIES.get(n.signature.split(":")[1], [])})
        sizes.append(len(served))
        if a0 is None and served:
            a1, progs1, note1 = solve_arc(p["demos"], p["test_in"], BASE_STEPS + served)
        else:
            a1, progs1, note1 = a0, progs0, note0
        o1 = outcome(a1, p)
        od_c[o1] += 1
        a2, progs2, note2 = solve_arc(p["demos"], p["test_in"], all_steps)
        all_c[outcome(a2, p)] += 1
        per.append({"puzzle": p["family"], "base": o0, "needs": [n.signature for n in needs],
                    "served": served, "on_demand": o1, "programs": progs1[:4], "note": note1,
                    "all_provisions": outcome(a2, p)})
    rng = random.Random(seed)
    extra = [n for n in all_steps if n not in BASE_STEPS]
    draws = []
    for _ in range(random_draws):
        c = Counter()
        for p, k in zip(puzzles, sizes):
            a, _, _ = solve_arc(p["demos"], p["test_in"], BASE_STEPS)
            if a is None and k:
                a, _, _ = solve_arc(p["demos"], p["test_in"], BASE_STEPS + rng.sample(extra, min(k, len(extra))))
            c[outcome(a, p)] += 1
        draws.append(dict(c))
    res.update({"base": dict(base_c), "on_demand": dict(od_c), "all_provisions": dict(all_c),
                "random_same_size": draws, "stated_needs": dict(need_counts.most_common()),
                "per_puzzle": per})
    return res


def arc_hypotheses(eng: Engine, puzzles: List[dict], tag: str) -> None:
    """Put each ARC answer on the wheel as a hypothesis (finite part verified, prediction part
    pending), and each refusal as a DOESN'T-KNOW entry with its need."""
    for p in puzzles:
        ans, progs, note = solve_arc(p["demos"], p["test_in"], list(STEP_LIBRARY))
        if ans is not None:
            h = eng.add(Hypothesis("", f"ARC.{tag}.{p['family']}.explains",
                                   f"[{p['family']}] program {progs[0]} reproduces every demonstration",
                                   "finite", "arc", "search"))
            h.exact = lambda p=p, prog=progs[0]: (True, f"{len(p['demos'])} demonstrations reproduced exactly")
            eng.cascade(h)
            hp = eng.add(Hypothesis("", f"ARC.{tag}.{p['family']}.predicts",
                                    f"[{p['family']}] the test output is the one all consistent programs "
                                    f"agree on ({note})", "prediction", "arc", "search",
                                    deps=[(h.hid, USES)]))
            if p["test_out"] is not None:
                right = ans == p["test_out"]
                hp.recompute = lambda right=right: (right, "checked against the held-out answer: " +
                                                    ("right" if right else "WRONG"))
                hp.cls = "comparison"
            eng.cascade(hp)
        else:
            needs = diagnose_arc(p["demos"])
            h = eng.add(Hypothesis("", f"ARC.{tag}.{p['family']}.unsolved",
                                   f"[{p['family']}] no answer: {note}; needs "
                                   f"{', '.join(n.signature for n in needs)}", "meta", "arc", "search"))
            eng.cascade(h)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 9. Reports
# ═════════════════════════════════════════════════════════════════════════════════════════════

def engine_report(eng: Engine, domain, title: str, extra_lines: Optional[List[str]] = None) -> dict:
    lines, consistency = dialogue(eng, extra_lines)
    truth = {h.hid: domain.truth(h) for h in eng.hyps} if hasattr(domain, "truth") else {}
    truth = {k: v for k, v in truth.items() if v != "unset"}      # claims with no stated truth
    answers = {h.hid: answer_of(h.status) for h in eng.hyps if h.hid in truth}
    rows = []
    for h in eng.hyps:
        rows.append({"hid": h.hid, "key": h.key, "params": _jsonable(h.params), "class": h.cls,
                     "origin": h.origin, "deps": h.deps, "text": h.text, "status": h.status,
                     "ring": ring_of(h.status), "backing": h.backing,
                     "profile": h.profile.as_dict() if h.profile else None,
                     "gate_log": h.gate_log, "truth": truth.get(h.hid)})
    return {"engine": ENGINE_VERSION, "title": title, "use_ledger": eng.use_ledger,
            "hypotheses": rows, "conflicts": eng.conflicts, "rollback": eng.rollback_log,
            "dialogue": lines, "dialogue_consistency": consistency,
            "score": score(answers, truth) if truth else None,
            "wheel": build_wheel(eng, title)}


def _md_table(rows: List[dict]) -> List[str]:
    out = ["| id | claim | class | status | arrow | backing |", "|---|---|---|---|---|---|"]
    for r in rows:
        arrow = ""
        if r["profile"]:
            a = r["profile"]["arrow"]
            arrow = f"{a['direction']} ({' → '.join(a['read'])})" if a["read"] else ""
        back = (r["backing"][-1] if r["backing"] else "").replace("|", "/")
        out.append(f"| {r['hid']} | {r['text'][:110].replace('|', '/')} | {r['class']} | **{r['status']}** | "
                   f"{arrow} | {back[:160]} |")
    return out


def report_md(rep: dict) -> str:
    L = [f"# {rep['title']} — GLM Hypothesis Engine {rep['engine']}", "",
         f"Lean ledger gate: {'on' if rep['use_ledger'] else 'OFF (ablation)'}", ""]
    if rep.get("score"):
        s = rep["score"]
        L += ["Score against the ground truth fixed in advance (right / wrong / overclaim / abstain): "
              f"**{s['right']} / {s['wrong']} / {s['overclaim']} / {s['abstain']}** of {s['n']}.", ""]
    L += _md_table(rep["hypotheses"]) + [""]
    prof = [r for r in rep["hypotheses"] if r["profile"]]
    if prof:
        L += ["## Layer reads (five nested scales) and arrows", ""]
        for r in prof:
            p = r["profile"]
            cells = ", ".join(f"{x['layer']}={x['scale']}:{'-' if x['verdict'] is None else 'T' if x['verdict'] else 'F'}"
                              for x in p["reads"])
            L.append(f"* {r['hid']}: {cells} — {p['arrow']['direction']}")
        L.append("")
    L += ["## Rollback", ""] + ([f"* {x}" for x in rep["rollback"]] or ["* none"]) + [""]
    L += [f"Conflicts (gate vs ledger, layer shape): {rep['conflicts'] or 'none'}",
          f"Dialogue consistency: {rep['dialogue_consistency']}", "", "## Dialogue", ""]
    L += ["> " + x for x in rep["dialogue"]]
    w = rep["wheel"]
    L += ["", "## Wheel", "", f"Rings: {w['counts']}", "", "Needs:"]
    L += [f"* `{n['signature']}` ({n['kind']}): {n['because']} — blocks {', '.join(n['blocks'])}" for n in w["needs"]]
    return "\n".join(L) + "\n"


def write(out: Path, stem: str, obj: dict, md: Optional[str] = None):
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}.json").write_text(json.dumps(_jsonable(obj), indent=1, ensure_ascii=False))
    if md is not None:
        (out / f"{stem}.md").write_text(md)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 10. Runners
# ═════════════════════════════════════════════════════════════════════════════════════════════

def run_rule30(data: R30Data, use_ledger: bool = True) -> Tuple[Engine, dict]:
    dom = Rule30Domain(data)
    eng = Engine(use_ledger)
    dom.propose(eng)
    eng.rollback()
    b = data.bits
    wm, wn = wobble_max_ratio(b)
    extra = [f"Data: {len(b)} centre bits, linear complexity to {len(data.lc) - 1}, left diagonals "
             f"D ≤ {data.d_max} (computed in {data.seconds} s).",
             f"Wobble: max D(N)²/N = {_frac(wm)} at N = {wn}; D({len(b)}) = {data.path[-1]}.",
             f"Observer arrow (−sign D(n), the 'Wobble as perspective' read): followed at "
             f"{_frac(observer_arrow_agreement(b))} ≈ {float(observer_arrow_agreement(b)):.5f} of the steps; "
             f"the frequency moves towards 1/2 exactly on those steps (Perspective.deviation_decreases_iff)."]
    rep = engine_report(eng, dom, "Rule 30", extra)
    rep["data"] = {"centre_bits": len(b), "lc_to": len(data.lc) - 1, "diagonals_to": data.d_max,
                   "seconds": data.seconds}
    return eng, rep


def run_general(use_ledger: bool = True, claims: Optional[Path] = None) -> Tuple[Engine, dict]:
    dom = GeneralDomain()
    eng = Engine(use_ledger)
    dom.propose(eng, claims)
    eng.rollback()
    return eng, engine_report(eng, dom, "General reasoning benchmarks")


def arc_md(res: dict, title: str) -> List[str]:
    L = [f"## {title}", "", f"{res['puzzles']} test grids", "",
         "| condition | outcome |", "|---|---|",
         f"| base steps only (symmetries + colour map) | {res['base']} |",
         f"| on demand: the wheel serves each puzzle's stated needs | {res['on_demand']} |",
         f"| all provisions | {res['all_provisions']} |"]
    for i, d in enumerate(res["random_same_size"], 1):
        L.append(f"| random provisions, same number as on demand #{i} | {d} |")
    L += ["", f"Needs stated by the base solver (from demonstrations only): {res['stated_needs']}", ""]
    solved = [p for p in res["per_puzzle"] if p["on_demand"] == "right"]
    if solved:
        L += ["Solved on demand: " + ", ".join(f"{p['puzzle']} ({'+'.join(sorted(set(p['programs'])))})"
                                              for p in solved), ""]
    wrong = [p for p in res["per_puzzle"] if p["on_demand"] == "wrong" or p["all_provisions"] == "wrong"]
    L += [f"Wrong answers: {[p['puzzle'] for p in wrong] or 'none'}", ""]
    return L


def run_arc_all(quick: bool, arc_zip: Optional[Path], arc_dir: Optional[Path]) -> Tuple[dict, str]:
    out = {}
    syn = make_synthetic(4402, 3 if quick else 6)
    out["synthetic"] = run_arc(syn, random_draws=3 if quick else 5)
    md = ["# ARC-style puzzles — GLM Hypothesis Engine " + ENGINE_VERSION, "",
          "The solver answers only when every consistent program of least depth agrees. Synthetic "
          "families are generated from steps that the library contains, so they measure need "
          "routing, not discovery; the real ARC tasks are the honest test.", ""]
    md += arc_md(out["synthetic"], "Synthetic held-out families")
    real = []
    if arc_dir and Path(arc_dir).exists():
        real = load_arc_dir(arc_dir)
    elif arc_zip and Path(arc_zip).exists():
        real = load_arc_zip(arc_zip)
    if real:
        out["real"] = run_arc(real, random_draws=2 if quick else 3)
        md += arc_md(out["real"], "Real ARC tasks")
    return out, "\n".join(md) + "\n"


def combined_wheel(reps: List[dict], turn: Optional[dict]) -> dict:
    rings = {KNOWS: [], THINKS: [], DONT_KNOW: []}
    needs, lang = [], []
    for r in reps:
        w = r["wheel"]
        for k in rings:
            rings[k] += w["rings"][k]
        needs += w["needs"]
        lang += w["language_wheel"]
    out = {"engine": f"GLM Hypothesis Engine {ENGINE_VERSION}", "format": "glm-wheel/2",
           "how_to_use": "Pass this file back with `python3 hypothesis_engine.py turn <file>`: every "
                         "entry is rebuilt from its family key and parameters and re-gated, and the "
                         "report lists which entries moved ring and why.",
           "rings": rings, "needs": needs, "language_wheel": lang,
           "counts": {k: len(v) for k, v in rings.items()}}
    if turn:
        out["turn_of_previous_wheel"] = {"summary": dict(turn["summary"]), "needs": turn["needs"]}
    return out


def turn_md(t: dict, src: str) -> str:
    L = [f"# Wheel turn: `{src}` re-gated by engine {ENGINE_VERSION}", "",
         "Every entry of the previous wheel is imported as a sentence, recognised as an executable "
         "family where possible, and sent through the same gate cascade.", "",
         f"Movement between rings: {dict(t['summary'])}", "",
         "| was | ring then | class | status now | ring now | reason |", "|---|---|---|---|---|---|"]
    for m in t["moves"]:
        L.append(f"| {m['was_hid']} | {m['was_ring']} | {m['class']} | **{m['now_status']}** | {m['now_ring']} | "
                 f"{str(m['reason'])[:150].replace('|', '/')} |")
    L += ["", "## Needs the previous wheel stated", "", "| need | status | met by |", "|---|---|---|"]
    for n in t["needs"]:
        L.append(f"| {n['need']}: {n['statement'][:90]} | {n['status']} | {n['by'][:160]} |")
    if t["language_recheck"]:
        L += ["", "## Language wheel re-checked", "", "| concept | status now | keep? |", "|---|---|---|"]
        for x in t["language_recheck"]:
            L.append(f"| {x['concept'][:100]} | {x['now_status']} | {'yes' if x['kept_in_language_wheel'] else 'no'} |")
    return "\n".join(L) + "\n"


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 11. Self-test (no Lean, no network; about a few seconds)
# ═════════════════════════════════════════════════════════════════════════════════════════════

def selftest() -> int:
    fails = []

    def ok(cond, msg):
        if not cond:
            fails.append(msg)

    b = centre_bits(64)
    ok(b[:10] == [1, 1, 0, 1, 1, 1, 0, 0, 1, 1], "centre column prefix (OEIS A051023)")
    ok(centre_bits(3000, 0b11) == centre_bits(3000), "seed 11 gives the seed-1 centre column (prefix)")
    p = lc_profile(centre_bits(12000))
    ok(2 * p[11101] - 11101 == 11, "L(11101) = 5556 (WheelChecksData.wheel_H19_false)")
    ok(wobble_max_ratio(centre_bits(4000)) == (Fraction(3200, 731), 1462), "wobble maximum on N ≤ 4000")
    dt = DiagonalTable(450)
    ok([D for D in range(451) if dt.white(D)] == [2, 7, 28, 399], "white left diagonals below 451")
    ok(dt.period[400] == 16 and all(8 % dt.period[D] == 0 for D in range(400)), "first period 16 at D = 400")
    ok(dt.doubling_points()[:4] == [3, 8, 29, 400], "period-doubling diagonals")
    ok(rdiag_period(4) == (8, 0), "right diagonal 4 has period 8 from time 0")
    # layer laws on a toy claim
    prof = escalation_profile("n < 7", [2, 4, 8, 16, 32], lambda N: (N < 7, str(N)))
    ok(prof.first_fail() == 2 and prof.shape_ok() and prof.arrow()["direction"] == "flipped at rational",
       "arrow flips at the first failing read and reads stop there")
    # gates
    e = Engine()
    h = e.add(Hypothesis("", "GEN.gcd.trap", "gcd trap", "Pi1", check=lambda N: (True, ""), scales=[1, 2, 3, 4, 5]))
    e.cascade(h)
    ok(h.status == REF_LEDGER, "survives every read, yet the ledger refutes it (gcd trap)")
    e2 = Engine(use_ledger=False)
    h2 = e2.add(Hypothesis("", "GEN.gcd.trap", "gcd trap", "Pi1", check=lambda N: (True, ""), scales=[1, 2, 3, 4, 5]))
    e2.cascade(h2)
    ok(h2.status == SURVIVES_TO and answer_of(h2.status) is None, "without the ledger it only survives")
    e3 = Engine()
    a = e3.add(Hypothesis("", "X", "a", "Pi1", check=lambda N: (N < 3, "x"), scales=[1, 2, 3, 4, 5]))
    c1 = e3.add(Hypothesis("", "Y", "uses a", "analogy", deps=[(a.hid, USES)]))
    c2 = e3.add(Hypothesis("", "Z", "narrowed from a", "analogy", deps=[(a.hid, DERIVED)]))
    c3 = e3.add(Hypothesis("", "W", "uses c1", "analogy", deps=[(c1.hid, USES)]))
    e3.run()
    ok(a.status == REF_ESCALATION and c1.status == RETRACTED and c3.status == RETRACTED and c2.status == UNTESTED,
       "typed transitive rollback: uses-edges retract, derived edges do not")
    ok(auto_claim_class("there are infinitely many white diagonals") == "Pi2", "classifier: Pi2")
    ok(auto_claim_class("X is analogous to the GLM's ladder") == "analogy", "classifier: analogy")
    ok(recognise("|2·L(n) − n| ≤ 10 for all n") == ("CC.lc.near.half", {"b": 10}), "recogniser")
    # ARC solver basics
    demos = [(G([[1, 0], [0, 0]]), G([[0, 1], [0, 0]])), (G([[2, 2], [0, 3]]), G([[2, 2], [3, 0]]))]
    ans, progs, _ = solve_arc(demos, G([[5, 0], [6, 0]]), BASE_STEPS)
    ok(ans == G([[0, 5], [0, 6]]), "ARC: horizontal flip")
    amb = [(G([[1, 1], [1, 1]]), G([[2, 2], [2, 2]]))]
    ans2, _, note2 = solve_arc(amb, G([[1, 3], [3, 1]]), BASE_STEPS)
    ok(ans2 is None, "ARC: refuses when consistent programs disagree or cannot apply")
    if fails:
        print("SELFTEST FAILED:", *fails, sep="\n  ")
        return 1
    print("selftest: all checks passed")
    return 0


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 12. Command line
# ═════════════════════════════════════════════════════════════════════════════════════════════

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="GLM Hypothesis Engine v18 (self-contained)")
    ap.add_argument("what", nargs="?", default="all", choices=["all", "rule30", "general", "arc", "turn"])
    ap.add_argument("wheel_file", nargs="?", help="for `turn`: a previous wheel JSON")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-ledger", action="store_true", help="ablation: no Lean provisions")
    ap.add_argument("--claims", type=Path, help="a JSON claims file for the general domain")
    ap.add_argument("--arc-zip", type=Path, default=HERE.parent / "glm_repo.zip")
    ap.add_argument("--arc-dir", type=Path, help="a directory of ARC task JSON files")
    ap.add_argument("--out", type=Path, default=HERE / "out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    t0 = time.time()
    sfx = ("_quick" if a.quick else "") + ("_noledger" if a.no_ledger else "")
    reps, turn = [], None
    data = None
    if a.what in ("all", "rule30", "turn"):
        data = R30Data(a.quick)
    if a.what in ("all", "rule30"):
        _, rep = run_rule30(data, not a.no_ledger)
        write(a.out, "rule30" + sfx, rep, report_md(rep))
        reps.append(rep)
        print(f"Rule 30: score {rep['score']}, rings {rep['wheel']['counts']}, "
              f"dialogue ok = {rep['dialogue_consistency']['ok']}, conflicts = {rep['conflicts']}")
    if a.what in ("all", "general"):
        _, rep = run_general(not a.no_ledger, a.claims)
        write(a.out, "general" + sfx, rep, report_md(rep))
        reps.append(rep)
        print(f"General: score {rep['score']}, rings {rep['wheel']['counts']}")
    if a.what in ("all", "arc"):
        res, md = run_arc_all(a.quick, a.arc_zip, a.arc_dir)
        write(a.out, "arc" + ("_quick" if a.quick else ""), res, md)
        print(f"ARC synthetic on demand: {res['synthetic']['on_demand']}"
              + (f"; real: base {res['real']['base']}, on demand {res['real']['on_demand']}" if "real" in res else ""))
    if a.what in ("all", "turn"):
        src = Path(a.wheel_file) if a.wheel_file else HERE.parent / "glm_wheel.json"
        if src.exists():
            turn = turn_wheel(json.loads(src.read_text()), data, not a.no_ledger)
            write(a.out, "wheel_turn" + sfx, turn, turn_md(turn, src.name))
            print(f"Wheel turn of {src.name}: {dict(turn['summary'])}")
    if reps:
        write(a.out, "glm_wheel_v18" + sfx, combined_wheel(reps, turn))
    print(f"done in {time.time() - t0:.1f} s; outputs in {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
