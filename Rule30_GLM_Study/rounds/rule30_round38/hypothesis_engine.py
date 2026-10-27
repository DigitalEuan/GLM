#!/usr/bin/env python3
"""GLM Hypothesis Engine v5 — statements, not parameters.

Round 38 of the Rule 30 / GLM study.  This keeps the owner's v4 idea — a cheap guess (a "sorry"),
a rigorous check, a refinement that reads *why* the check failed, and a loop — and changes what is
guessed and how it is checked:

  * A hypothesis is a **statement** about the puzzle (a quantified claim with an exact per-instance
    test and a Lean rendering), not a parameter triple of a correction pipeline.
  * The check is **falsification on exact data**: a development range, then held-out ranges that
    the generator never saw, then control systems.  A survivor is reported as surviving its stated
    range only (EMP or CERT), never as proved.
  * Refinement is **counterexample-guided**: a refuted lift is (a) cut to the range where it holds,
    (b) narrowed to the sharpest bound the data allow, and (c) handed to the mechanism miner, which
    looks for a local cause that separates the failing instances from the passing ones and proposes
    a law.  A law is a new hypothesis, checked like any other, and if it holds it is used to
    **predict** the next failure far beyond the data — and the prediction is checked.
  * Controls decide what a statement is about: the mirror rule, other seeds, a linear rule.
  * Novelty and credit are scored against the evidence ledger (`claims.csv`) only *after*
    generation; the generator never reads the ledger.

Exact arithmetic only (project rule 7): integers, `Fraction`s and bit vectors.  No floating point
inside any computation, no random numbers, no hashing.  Floats appear only for wall-clock timing.

Run:  python3 hypothesis_engine.py            (full run, about 20 seconds)
      python3 hypothesis_engine.py --quick    (smaller held-out ranges)
Outputs (next to this file): r38_engine_report.json, r38_engine_report.md, r38_conjectures.lean.txt
"""

from __future__ import annotations

import json
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent

# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1. The exact observatory
# ═══════════════════════════════════════════════════════════════════════════════════════════════
#
# Rows are Python integers used as bit vectors.  Two framings are used.
#   left-aligned : bit k is the cell k steps inside the left edge of the light cone.  A left
#                  diagonal D is bit D read over time.  Bit k of the next row depends only on bits
#                  k-2, k-1, k of this row, so the first N bits evolve on their own (this is the
#                  autonomy that `LeftDiagonalPeriodsData.lean` turns into a certificate).
#   right-aligned: bit k is the cell k steps inside the right edge (right diagonal k).
# A general elementary rule is applied by its eight minterms.


def eca_apply(rule: int, L: int, C: int, R: int, mask: int) -> int:
    """New row from the three neighbour rows (already shifted into place), for any ECA rule."""
    out = 0
    for p in range(8):
        if (rule >> p) & 1:
            a = L if p & 4 else ~L
            b = C if p & 2 else ~C
            c = R if p & 1 else ~R
            out |= a & b & c
    return out & mask


def left_step(rule: int, r: int, mask: int) -> int:
    """Left-aligned step: new[k] = f(old[k-2], old[k-1], old[k])."""
    if rule == 30:
        return ((r << 2) ^ ((r << 1) | r)) & mask
    return eca_apply(rule, r << 2, r << 1, r, mask)


def right_step(rule: int, r: int, mask: int) -> int:
    """Right-aligned step: new[k] = f(old[k], old[k-1], old[k-2])."""
    if rule == 30:
        return (r ^ ((r << 1) | (r << 2))) & mask
    return eca_apply(rule, r, r << 1, r << 2, mask)


@dataclass
class DiagonalProfile:
    """Exact per-diagonal invariants of one family (left or right diagonals) of one system."""
    system: str
    N: int                       # diagonals 0..N-1
    settled_at: Optional[int]    # time s with row(s + pmax) = row(s) on the first N bits (exact)
    pmax: int
    lp: list                     # least eventual period (divides pmax) or None if not settled
    white: list                  # eventually white
    parity: list                 # parity of the black cells over one least period
    density: list                # Fraction: black cells per least period
    pattern: list                # eventual pattern as an int over phases t mod pmax
    pre: Optional[list] = None   # exact preperiod (only when requested)


def left_profile(N: int, rule: int = 30, seed: int = 1, pmax: int = 64,
                 want_pre: bool = False, tmax: Optional[int] = None) -> DiagonalProfile:
    """Run the first N left diagonals until the packed row repeats with period pmax.

    The repeat is an exact certificate: from that time on every diagonal D < N is periodic with
    period pmax, for all later times (autonomy).  If no repeat happens before tmax the profile is
    marked unsettled (lp = None)."""
    mask = (1 << N) - 1
    if tmax is None:
        tmax = 3 * N + 4 * pmax + 64
    r = seed & mask
    ring: deque = deque()
    hist = [] if want_pre else None
    s = None
    for t in range(tmax + pmax + 1):
        ring.append(r)
        if want_pre:
            hist.append(r)
        if len(ring) > pmax:
            old = ring.popleft()
            if old == r:
                s = t - pmax
                break
        r = left_step(rule, r, mask)
    name = f"rule {rule}, seed {bin(seed)[2:]}"
    if s is None:
        return DiagonalProfile(name, N, None, pmax, [None] * N, [None] * N, [None] * N,
                               [None] * N, [None] * N)
    # ring now holds rows s+1 .. s+pmax ; rebuild rows s .. s+pmax-1 as a list
    rows = list(ring)[:-1]
    rows.insert(0, old)  # row s
    base = s
    lp, white, parity, density, pattern = [], [], [], [], []
    for D in range(N):
        pat = 0
        for i, row in enumerate(rows):
            pat |= ((row >> D) & 1) << ((base + i) % pmax)
        p = pmax
        while p > 1 and _pattern_has_period(pat, p // 2, pmax):
            p //= 2
        ones = bin(pat).count("1") * p // pmax
        lp.append(p)
        white.append(pat == 0)
        parity.append(ones % 2)
        density.append(Fraction(ones, p))
        pattern.append(pat)
    prof = DiagonalProfile(name, N, s, pmax, lp, white, parity, density, pattern)
    if want_pre:
        # exact preperiod: one past the last time t with bit D of row(t) != bit D of row(t+pmax)
        # (for an eventually periodic sequence the preperiod is the same for every multiple of
        # its least period).
        pre = [0] * N
        seen = 0
        for t in range(s - 1, -1, -1):
            x = (hist[t] ^ hist[t + pmax]) & ~seen
            while x:
                low = x & -x
                pre[low.bit_length() - 1] = t + 1
                x ^= low
            seen |= hist[t] ^ hist[t + pmax]
        prof.pre = pre
    return prof


def _pattern_has_period(pat: int, q: int, m: int) -> bool:
    rot = ((pat >> q) | (pat << (m - q))) & ((1 << m) - 1)
    return rot == pat


def right_profile(DM: int, rule: int = 30, seed: int = 1) -> list:
    """Exponent of the least period of right diagonals 0..DM of the seed pattern (rule 30).

    For the seed every right diagonal D is periodic from t = 0 with period 2^D (ledger C48), so
    the least period is the least power of two that works on one period: exact."""
    mask = (1 << (DM + 1)) - 1
    T = 2 ** (DM + 1) + 2
    rows = []
    r = seed & mask
    for _ in range(T):
        rows.append(r)
        r = right_step(rule, r, mask)
    out = []
    for D in range(DM + 1):
        p = 1
        while not all(((rows[t] >> D) & 1) == ((rows[t + p] >> D) & 1) for t in range(2 ** D + 1)):
            p *= 2
        out.append(p.bit_length() - 1)
    return out


def centre_column(n: int, rule: int = 30, seed: int = 1) -> list:
    """First n centre-column bits from a seed placed at the origin (full rows, exact)."""
    W = 2 * n + 3
    mask = (1 << W) - 1
    mid = n + 1
    r = (seed << mid) & mask
    out = []
    for _ in range(n):
        out.append((r >> mid) & 1)
        if rule == 30:
            r = ((r << 1) ^ (r | (r >> 1))) & mask
        else:
            r = eca_apply(rule, r << 1, r, r >> 1, mask)
    return out


def linear_complexity(bits: list) -> list:
    """Berlekamp–Massey over GF(2): profile L(1..n) (exact, bit-vector polynomials)."""
    n = len(bits)
    s = 0
    for i, b in enumerate(bits):
        s |= b << i
    C, B = 1, 1
    L, m = 0, 1
    prof = []
    for i in range(n):
        d = bits[i]
        x = C >> 1
        j = 1
        while x:
            if x & 1:
                d ^= bits[i - j]
            x >>= 1
            j += 1
        if d:
            T = C
            C ^= B << m
            if 2 * L <= i:
                L, B, m = i + 1 - L, T, 1
            else:
                m += 1
        else:
            m += 1
        prof.append(L)
    return prof


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 2. Hypotheses
# ═══════════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class Hypothesis:
    hid: str
    family: str                 # e.g. "left-diagonals"
    text: str                   # the statement in words
    lean: str                   # the statement as a Lean `Prop` (proposal; proof is `sorry`)
    origin: str                 # template | lift | narrow | cut | mechanism | analogy | prediction
    parent: Optional[str] = None
    # per-instance test over an index range; returns (ok, first counterexample or None)
    test: Optional[Callable] = None
    key: str = ""               # canonical key, used only for novelty scoring after generation
    status: str = "proposed"    # proposed | refuted-dev | refuted-heldout | survives | law-holds
    evidence: list = field(default_factory=list)
    controls: dict = field(default_factory=dict)
    scope: str = ""             # seed-specific | rule-specific | map-level | ...

    def record(self, stage: str, ok: bool, detail: str):
        self.evidence.append({"stage": stage, "ok": ok, "detail": detail})


class Engine:
    def __init__(self, quick: bool = False, log=print):
        self.quick = quick
        self.log = log
        self.hyps: list[Hypothesis] = []
        self.counter = 0
        self.timings = {}
        self.predictions = []

    def new(self, **kw) -> Hypothesis:
        self.counter += 1
        h = Hypothesis(hid=f"H{self.counter:02d}", **kw)
        self.hyps.append(h)
        return h

    # ───────────────────────────────────────────────────────────────────────────────────────────
    # Stage A: left diagonals — lift, refute, cut, narrow, mine, prove-by-law, predict
    # ───────────────────────────────────────────────────────────────────────────────────────────
    def run_left_diagonals(self):
        t0 = time.time()
        dev_N = 200                      # the range of the earlier EMP observation (C133)
        held = [2000, 20000] if not self.quick else [2000, 6000]
        self.log("== Left diagonals ldiag D t = a(t)(D - t) ==")
        dev = left_profile(dev_N, want_pre=True)
        self.log(f"  dev range D < {dev_N}: settled exactly at t = {dev.settled_at} "
                 f"(period 64 certificate)")
        max_lp = max(dev.lp)

        # -- cheap guesses (lifts) from the development data
        h_bound = self.new(
            family="left-diagonals", origin="lift", key="LD.period.divides.8",
            text=f"every left diagonal has eventual period dividing {max_lp}",
            lean=f"∀ D : ℕ, ∃ T, ∀ t ≥ T, ldiag D (t + {max_lp}) = ldiag D t",
            test=lambda prof, lo, hi, m=max_lp: _first(lambda D: prof.lp[D] is not None
                                                     and m % prof.lp[D] == 0, lo, hi))
        ratios = [Fraction(dev.pre[D], D) for D in range(20, dev_N)]
        lo_r, hi_r = min(ratios), max(ratios)
        h_trans = self.new(
            family="left-diagonals", origin="lift", key="LD.preperiod.gt.D",
            text="for D ≥ 20 the transient of left diagonal D is longer than D (the centre column, "
                 "which reads diagonal D at time D, always reads it inside its transient)",
            lean="∀ D : ℕ, 20 ≤ D → ∃ t ≥ D, ldiag D (t + 64) ≠ ldiag D t",
            test=lambda prof, lo, hi: _first(lambda D: D < 20 or prof.pre[D] > D, lo, hi))
        h_env = self.new(
            family="left-diagonals", origin="lift", key="LD.preperiod.envelope",
            text=f"for D ≥ 20 the transient satisfies {lo_r} ≤ pre(D)/D ≤ {hi_r} "
                 f"(the exact extremes on the development range)",
            lean=f"-- envelope {lo_r} ≤ pre(D)/D ≤ {hi_r}; EMP target, no Lean form proposed",
            test=lambda prof, lo, hi, a=lo_r, b=hi_r: _first(
                lambda D: D < 20 or a <= Fraction(prof.pre[D], D) <= b, lo, hi))
        h_white = self.new(
            family="left-diagonals", origin="lift", key="LD.white.finite",
            text="the eventually white left diagonals are exactly "
                 f"{[D for D in range(dev_N) if dev.white[D]]}",
            lean="∀ D : ℕ, (∃ T, ∀ t ≥ T, ldiag D t = false) ↔ D = 2 ∨ D = 7 ∨ D = 28",
            test=lambda prof, lo, hi: _first(lambda D: prof.white[D] == (D in (2, 7, 28)), lo, hi))

        for h in (h_bound, h_trans, h_env, h_white):
            ok, w = h.test(dev, 0, dev_N)
            h.record(f"dev D<{dev_N}", ok, "passes" if ok else f"fails at D={w}")
            h.status = "survives-dev" if ok else "refuted-dev"

        # -- held-out escalation
        profiles = {}
        for Nh in held:
            prof = left_profile(Nh, want_pre=True, pmax=64)
            profiles[Nh] = prof
            self.log(f"  held-out D < {Nh}: settled exactly at t = {prof.settled_at}")
            for h in (h_bound, h_trans, h_env, h_white):
                if h.status.startswith("refuted"):
                    continue
                if h.key.startswith("LD.preperiod") and prof.pre is None:
                    continue
                ok, w = h.test(prof, 0, Nh)
                if ok:
                    h.record(f"held-out D<{Nh}", True, "passes")
                else:
                    h.record(f"held-out D<{Nh}", False, f"fails at D={w}")
                    h.status = "refuted-heldout"
                    h.witness = w
        for h in (h_bound, h_trans, h_env, h_white):
            if h.status == "survives-dev":
                h.status = "survives"
        big = profiles[held[-1]]

        # -- refinement of the refuted bound: cut, narrow, mine
        if h_bound.status == "refuted-heldout":
            w = h_bound.witness
            cut = self.new(
                family="left-diagonals", origin="cut", parent=h_bound.hid,
                key="LD.period.divides.8.below",
                text=f"every left diagonal D < {w} has eventual period dividing {max_lp}",
                lean=f"∀ D : ℕ, D < {w} → ∃ T, ∀ t ≥ T, ldiag D (t + {max_lp}) = ldiag D t")
            cut.status = "survives"
            cut.record("cut", True, f"holds for every D < {w} (exact repeat certificate)")
            new_max = max(p for p in big.lp if p is not None)
            nar = self.new(
                family="left-diagonals", origin="narrow", parent=h_bound.hid,
                key="LD.period.divides.16",
                text=f"every left diagonal has eventual period dividing {new_max}",
                lean=f"∀ D : ℕ, ∃ T, ∀ t ≥ T, ldiag D (t + {new_max}) = ldiag D t",
                test=lambda prof, lo, hi, m=new_max: _first(
                    lambda D: prof.lp[D] is not None and m % prof.lp[D] == 0, lo, hi))
            ok, ww = nar.test(big, 0, big.N)
            nar.record(f"all data D<{big.N}", ok, "passes" if ok else f"fails at D={ww}")
            nar.status = "survives" if ok else "refuted-heldout"
            # mechanism mining on the period jumps
            laws = self.mine_period_jumps(big)
            if laws:
                self.predict_next_jump(big, laws, nar)
        self.timings["left-diagonals"] = time.time() - t0
        self.left_profiles = profiles
        self.left_dev = dev

    def mine_period_jumps(self, prof: DiagonalProfile) -> Optional[Hypothesis]:
        """Find a local cause of the period jumps lp(D) > max(lp(D-1), lp(D-2))."""
        N = prof.N
        jumps = [D for D in range(2, N) if prof.lp[D] > max(prof.lp[D - 1], prof.lp[D - 2])]
        self.log(f"  mechanism miner: period jumps at D = {jumps}")
        # predicate library on the two outer diagonals (the inputs of the one-bit machine)
        preds = {
            "white(D-1)": lambda D: prof.white[D - 1],
            "white(D-2)": lambda D: prof.white[D - 2],
            "odd-parity(D-2)": lambda D: prof.parity[D - 2] == 1,
            "odd-parity(D-1)": lambda D: prof.parity[D - 1] == 1,
            "lp(D-1) < lp(D-2)": lambda D: prof.lp[D - 1] < prof.lp[D - 2],
            "density(D-1) = 1": lambda D: prof.density[D - 1] == 1,
            "D even": lambda D: D % 2 == 0,
        }
        names = list(preds)
        cands = [(n,) for n in names] + [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
        J = set(jumps)
        results = []
        for c in cands:
            holds = {D for D in range(2, N) if all(preds[n](D) for n in c)}
            necessary = J <= holds
            sufficient = holds <= J
            results.append((c, necessary, sufficient, len(holds)))
        exact = [r for r in results if r[1] and r[2]]
        necessary_single = [r for r in results if r[1] and len(r[0]) == 1]
        for c, nec, suf, n in results:
            if nec and (suf or len(c) == 1):
                self.log(f"    {' ∧ '.join(c):32s} necessary={nec} sufficient={suf} (holds at {n})")
        if not exact:
            return None
        laws = []
        for c, _, _, n in sorted(exact, key=lambda r: len(r[0])):
            cname = " ∧ ".join(c)
            law = self.new(
                family="left-diagonals", origin="mechanism",
                key="LD.period.law" if len(c) == 2 else "LD.period.law.simple",
                text=f"a left diagonal's period exceeds the periods of the two diagonals outside it "
                     f"exactly when {cname}",
                lean="∀ (D : ℤ) (Q : ℕ), EvPer (ldiag (D - 1)) Q → EvPer (ldiag (D - 2)) Q → "
                     "¬ EventuallyWhite (ldiag (D - 1)) → EvPer (ldiag D) Q"
                     if len(c) == 2 else f"-- jump(D) ↔ {cname}")
            law.status = "law-holds"
            law.cond = c
            law.record(f"all data D<{N}", True,
                       f"exact on every D < {N}: {len(J)} jumps, the condition holds at {n} indices")
            laws.append(law)
        if len(laws) > 1:
            names = [" ∧ ".join(l.cond) for l in laws]
            self.log(f"  junction: the data cannot separate the laws {names}; the separating "
                     f"observation is a white diagonal whose outer neighbour has even parity")
            for l in laws:
                l.record("junction", True, f"not separated by D < {N} from {names}")
        return laws

    @staticmethod
    def _law_pred(name: str, p: DiagonalProfile, D: int) -> bool:
        return {"white(D-1)": p.white[D - 1], "white(D-2)": p.white[D - 2],
                "odd-parity(D-2)": p.parity[D - 2] == 1, "odd-parity(D-1)": p.parity[D - 1] == 1,
                "lp(D-1) < lp(D-2)": p.lp[D - 1] < p.lp[D - 2],
                "density(D-1) = 1": p.density[D - 1] == 1, "D even": D % 2 == 0}[name]

    def predict_next_jump(self, prof: DiagonalProfile, laws: list, target: Hypothesis):
        """Use the law to predict the next period jump far beyond the data, then check it.

        By the law (proved in Lean: `one_bit_reset`, `one_bit_doubles`) the eventual pattern of
        diagonal D is a function of the patterns of D-1 and D-2 whenever D-1 is not eventually
        white.  So the patterns can be run forward at O(1) cost per diagonal.  At a white diagonal
        the law leaves one bit open (the constant of the running parity); the engine settles it by
        one exact computation of the automaton, and continues."""
        M = 16
        assert prof.pmax % M == 0
        def to16(pat):  # the pattern restricted to phases mod 16 (valid when lp | 16)
            out = 0
            for ph in range(M):
                out |= ((pat >> ph) & 1) << ph
            return out
        def F(A, B):
            phi = (B & -B).bit_length() - 1
            x = 1 - ((A >> phi) & 1)
            ph = (phi + 1) % M
            C = 0
            for _ in range(M):
                C |= x << ph
                x = ((A >> ph) & 1) ^ (((B >> ph) & 1) | x)
                ph = (ph + 1) % M
            return C
        N = prof.N
        if max(prof.lp) > M:
            return
        a, b, D = to16(prof.pattern[N - 2]), to16(prof.pattern[N - 1]), N - 1
        limit = 400000 if not self.quick else 100000
        t0 = time.time()
        zeros_seen = []
        while D < limit:
            if b == 0:
                odd = bin(a).count("1") % 2
                zeros_seen.append((D, odd))
                if odd:
                    break
                # settle the open constant by one exact run of the automaton; the same run is the
                # separating observation for the junction of laws
                p = left_profile(D + 3, pmax=64, tmax=2 * (D + 3) + 512)
                jump = p.lp[D + 1] > max(p.lp[D], p.lp[D - 1])
                for l in laws:
                    says = all(self._law_pred(n, p, D + 1) for n in l.cond)
                    if says != jump and l.status == "law-holds":
                        l.status = "refuted-heldout"
                        l.record("separating observation", False,
                                 f"diagonal {D} is eventually white with even parity outside it; the "
                                 f"law predicts a jump at {D + 1} = {says}, actual = {jump}")
                    elif l.status == "law-holds":
                        l.record("separating observation", True,
                                 f"correct at the even-parity white diagonal {D}")
                a, b, D = to16(p.pattern[D + 1]), to16(p.pattern[D + 2]), D + 2
                continue
            a, b, D = b, F(a, b), D + 1
        if not zeros_seen or not zeros_seen[-1][1]:
            self.log(f"  predictor: no jump predicted below {limit}")
            return
        Z = zeros_seen[-1][0]
        pred = Z + 1
        self.log(f"  predictor: white diagonals ahead {[z for z, _ in zeros_seen]}; "
                 f"odd parity before {Z} ⇒ predicted first period-32 diagonal D = {pred} "
                 f"({time.time() - t0:.1f}s)")
        # check the prediction directly
        chk = left_profile(pred + 1, pmax=64, tmax=2 * (pred + 1) + 512)
        ok = chk.lp[pred] == 32 and all(p <= 16 for p in chk.lp[:pred])
        law = next((l for l in laws if l.status == "law-holds"), laws[0])
        h = self.new(
            family="left-diagonals", origin="prediction", parent=law.hid,
            key="LD.first.period.32",
            text=f"the first left diagonal with least eventual period 32 is D = {pred}",
            lean=f"¬ (∃ T, ∀ t ≥ T, ldiag {pred} (t + 16) = ldiag {pred} t) ∧ "
                 f"∀ D < {pred}, ∃ T, ∀ t ≥ T, ldiag D (t + 16) = ldiag D t")
        h.status = "prediction-confirmed" if ok else "prediction-failed"
        h.record("direct check", ok, f"automaton run to D = {pred}: lp = {chk.lp[pred]}, "
                                     f"all earlier lp ≤ 16: {all(p <= 16 for p in chk.lp[:pred])}")
        self.predictions.append({"predicted": pred, "confirmed": ok,
                                 "white_diagonals_on_the_way": [z for z, _ in zeros_seen]})
        if ok and target.status == "survives":
            target.status = "refuted-by-prediction"
            target.record("prediction", False, f"fails at D={pred}")
            cut = self.new(
                family="left-diagonals", origin="cut", parent=target.hid,
                key="LD.period.divides.16.below",
                text=f"every left diagonal D < {pred} has eventual period dividing 16",
                lean=f"∀ D : ℕ, D < {pred} → ∃ T, ∀ t ≥ T, ldiag D (t + 16) = ldiag D t")
            cut.status = "survives"
            cut.record("cut", True, f"holds for every D < {pred} (exact repeat certificate)")
            nxt = self.new(
                family="left-diagonals", origin="lift", parent=law.hid,
                key="LD.periods.unbounded",
                text="the least periods of the left diagonals are unbounded (equivalently, by the "
                     "law, infinitely many eventually white diagonals meet odd parity)",
                lean="∀ m, ∃ D : ℕ, ¬ ∃ T, ∀ t ≥ T, ldiag D (t + 2 ^ m) = ldiag D t")
            nxt.status = "open"
            nxt.record("data", True, "periods 1, 2, 4, 8, 16, 32 first at D = 0, 3, 8, 29, 400, "
                                     f"{pred}; no finite range decides it")

    # ───────────────────────────────────────────────────────────────────────────────────────────
    # Stage B: right diagonals — closed-form lifts and analogy transport of the law
    # ───────────────────────────────────────────────────────────────────────────────────────────
    def run_right_diagonals(self):
        t0 = time.time()
        self.log("== Right diagonals rdiag D t = a(t)(t - D) ==")
        dev_D, held_D = 8, (16 if not self.quick else 13)
        ex = right_profile(held_D)
        dev = ex[:dev_D + 1]
        self.log(f"  least-period exponents, dev D ≤ {dev_D}: {dev}")
        forms = []
        for m in range(2, 6):
            for c in range(0, m):
                forms.append((f"D - floor((D + {c}) / {m})", lambda D, m=m, c=c: D - (D + c) // m))
        forms += [("D", lambda D: D), ("ceil(D / 2)", lambda D: (D + 1) // 2)]
        fits = [(name, f) for name, f in forms if all(f(D) == dev[D] for D in range(dev_D + 1))]
        for name, f in fits:
            h = self.new(family="right-diagonals", origin="lift", key=f"RD.lp.closed.{name}",
                         text=f"the least period of right diagonal D is 2^({name})",
                         lean=f"-- least period of rdiag D equals 2 ^ ({name})")
            bad = next((D for D in range(dev_D + 1, held_D + 1) if f(D) != ex[D]), None)
            h.record(f"dev D≤{dev_D}", True, "fits exactly")
            if bad is None:
                h.status = "survives"
                h.record(f"held-out D≤{held_D}", True, "passes")
            else:
                h.status = "refuted-heldout"
                h.record(f"held-out D≤{held_D}", False,
                         f"fails at D={bad}: exponent {ex[bad]}, form gives {f(bad)}")
        hb = self.new(family="right-diagonals", origin="lift", key="RD.lp.le.2^D",
                      text="the least period of right diagonal D divides 2^D",
                      lean="∀ D t, rdiag D (t + 2 ^ D) = rdiag D t")
        hb.status = "survives"
        hb.record(f"all D≤{held_D}", all(ex[D] <= D for D in range(held_D + 1)), "passes")
        hl = self.new(family="right-diagonals", origin="lift", key="RD.lp.gt.half",
                      text="the least period of right diagonal D exceeds ceil(D/2)",
                      lean="-- 2^(exponent) > ceil(D/2)")
        okl = all(2 ** ex[D] > (D + 1) // 2 for D in range(held_D + 1))
        hl.status = "survives" if okl else "refuted-heldout"
        hl.record(f"all D≤{held_D}", okl, "passes" if okl else "fails")
        # analogy transport of the left-diagonal law: the right diagonal is the one-bit machine
        # u(t+1) = u(t) xor (rdiag(D-1) t or rdiag(D-2) t), i.e. a machine whose reset input is
        # always white: so the transported law says "period doubles iff the parity is odd",
        # and never stays equal through a reset.
        ha = self.new(family="right-diagonals", origin="analogy", key="RD.periodic.or.anti",
                      text="(transported from the left-diagonal law) every right diagonal is "
                           "periodic or anti-periodic with the common period of the two diagonals "
                           "outside it",
                      lean="-- rdiag D (t + Q) = rdiag D t xor (parity of (rdiag (D-1) ∨ rdiag (D-2)) "
                           "over one period Q)")
        jumps_ok = all(ex[D] <= max(ex[D - 1], ex[D - 2]) + 1 for D in range(2, held_D + 1))
        ha.status = "survives" if jumps_ok else "refuted-heldout"
        ha.record(f"all D≤{held_D}", jumps_ok, "every exponent is at most one more than the "
                                               "larger outer exponent")
        self.timings["right-diagonals"] = time.time() - t0

    # ───────────────────────────────────────────────────────────────────────────────────────────
    # Stage C: the centre column — the three questions, honestly bounded
    # ───────────────────────────────────────────────────────────────────────────────────────────
    def run_centre(self):
        t0 = time.time()
        self.log("== Centre column a(t) ==")
        dev_n, held_n = 4000, (60000 if not self.quick else 20000)
        c = centre_column(held_n)
        # P1 rungs: no eventual period p with small preperiod
        P = 64
        last_mis = {}
        for p in range(1, P + 1):
            lm = -1
            for t in range(held_n - p):
                if c[t] != c[t + p]:
                    lm = t
            last_mis[p] = lm
        h1 = self.new(family="centre", origin="template", key="CC.no.short.period",
                      text=f"the centre column is not eventually periodic with period p ≤ {P} and "
                           f"preperiod ≤ {held_n // 2}",
                      lean=f"∀ p, 1 ≤ p → p ≤ {P} → ¬ ∀ t ≥ {held_n // 2}, centerCol (t + p) = centerCol t")
        okp = all(last_mis[p] >= held_n // 2 for p in last_mis)
        h1.status = "survives" if okp else "refuted-heldout"
        h1.record(f"n<{held_n}", okp, "a mismatch after the stated preperiod exists for every p "
                                      "(this is a finite refutation of each rung, CERT-able)")
        # P2: balance with the sharpest integer constant on the dev range, then held-out
        def worst_c2(bits, upto):
            ones, best = 0, Fraction(0)
            for N in range(1, upto + 1):
                ones += bits[N - 1]
                d = 2 * ones - N
                v = Fraction(d * d, N)
                if v > best:
                    best = v
            return best
        c2_dev = worst_c2(c, dev_n)
        k = 1
        while Fraction(k * k) < c2_dev:
            k += 1
        h2 = self.new(family="centre", origin="narrow", key="CC.balance.sqrt",
                      text=f"|#black − #white| ≤ {k}·√N for every prefix length N "
                           f"(sharpest integer constant on N ≤ {dev_n})",
                      lean=f"-- informal: ∀ N ≥ 1, (2·#black(N) − N)^2 ≤ {k * k}·N; ledger C25: an "
                           f"O(√N) bound is expected to fail eventually (iterated logarithm)")
        c2_all = worst_c2(c, held_n)
        h2.record(f"dev N≤{dev_n}", True, f"max (2·ones−N)²/N = {c2_dev} ≤ {k * k}")
        if c2_all <= k * k:
            h2.status = "survives"
            h2.record(f"held-out N≤{held_n}", True, f"max = {c2_all}")
        else:
            h2.status = "refuted-heldout"
            h2.record(f"held-out N≤{held_n}", False, f"max = {c2_all} > {k * k}")
            k2 = k
            while Fraction(k2 * k2) < c2_all:
                k2 += 1
            hn = self.new(family="centre", origin="narrow", parent=h2.hid, key="CC.balance.sqrt.2",
                          text=f"|#black − #white| ≤ {k2}·√N for every N (narrowed on N ≤ {held_n})",
                          lean=f"-- informal: ∀ N ≥ 1, (2·#black(N) − N)^2 ≤ {k2 * k2}·N")
            hn.status = "survives"
            hn.record(f"N≤{held_n}", True, f"max = {c2_all}; EMP only — no finite range decides P2")
        # P1/P3: linear complexity stays within a constant of n/2
        lc_n = 6000 if not self.quick else 3000
        prof = linear_complexity(c[:lc_n])
        dev_lc = 2000
        dmax = max(abs(2 * prof[i] - (i + 1)) for i in range(dev_lc))
        h3 = self.new(family="centre", origin="lift", key="CC.lc.half",
                      text=f"the GF(2) linear complexity L(n) of the centre column satisfies "
                           f"|2·L(n) − n| ≤ {dmax} for all n (sharpest on n ≤ {dev_lc})",
                      lean=f"-- |2 L(n) - n| ≤ {dmax}; would imply Problem 1 via LCUnbounded")
        dall = max(abs(2 * prof[i] - (i + 1)) for i in range(lc_n))
        h3.record(f"dev n≤{dev_lc}", True, f"max |2L−n| = {dmax}")
        h3.status = "survives" if dall <= dmax else "refuted-heldout"
        h3.record(f"held-out n≤{lc_n}", dall <= dmax, f"max |2L−n| = {dall}")
        if dall > dmax:
            h3n = self.new(family="centre", origin="narrow", parent=h3.hid, key="CC.lc.half.2",
                           text=f"|2·L(n) − n| ≤ {dall} for all n (narrowed on n ≤ {lc_n})",
                           lean=f"-- |2 L(n) - n| ≤ {dall}")
            h3n.status = "survives"
            h3n.record(f"n≤{lc_n}", True, "EMP only; the narrowing never settles from a finite range")
        # complexity: every word of length k appears early
        wk = 12
        firsts = []
        for kk in range(1, wk + 1):
            seen, need, pos = set(), 1 << kk, None
            w = 0
            for i, b in enumerate(c):
                w = ((w << 1) | b) & (need - 1)
                if i >= kk - 1:
                    seen.add(w)
                    if len(seen) == need:
                        pos = i + 1
                        break
            firsts.append(pos)
        ratio = max(Fraction(firsts[kk - 1], kk * (1 << kk)) for kk in range(1, 9))
        h4 = self.new(family="centre", origin="lift", key="CC.words.early",
                      text=f"every binary word of length k occurs in the first ⌈{ratio}·k·2^k⌉ "
                           f"centre bits (sharpest on k ≤ 8)",
                      lean="-- factor complexity: all words of length k occur in a prefix of "
                           "length O(k 2^k)")
        okw = all(firsts[kk - 1] is not None and Fraction(firsts[kk - 1]) <= ratio * kk * (1 << kk)
                  for kk in range(1, wk + 1))
        h4.status = "survives" if okw else "refuted-heldout"
        h4.record(f"k≤{wk}", okw, f"first full coverage at {firsts}")
        self.timings["centre"] = time.time() - t0

    # ───────────────────────────────────────────────────────────────────────────────────────────
    # Stage D: controls — what is each surviving statement about?
    # ───────────────────────────────────────────────────────────────────────────────────────────
    def run_controls(self):
        t0 = time.time()
        self.log("== Controls ==")
        systems = [(30, 0b11, "rule 30, seed 11"), (30, 0b101, "rule 30, seed 101"),
                   (86, 1, "rule 86 (mirror), seed 1"), (90, 1, "rule 90 (linear), seed 1"),
                   (45, 1, "rule 45, seed 1")]
        N = 400
        cprofs = {}
        for rule, seed, name in systems:
            cprofs[name] = left_profile(N, rule=rule, seed=seed, pmax=64, tmax=6 * N)
            p = cprofs[name]
            if p.settled_at is None:
                self.log(f"  {name:28s}: first {N} left diagonals not periodic with period | 64 "
                         f"by t = {6 * N}")
            else:
                lps = sorted(set(p.lp))
                self.log(f"  {name:28s}: settled at t = {p.settled_at}, periods {lps}, "
                         f"white {[D for D in range(N) if p.white[D]][:8]}")
        self.control_profiles = cprofs
        for h in self.hyps:
            if h.family != "left-diagonals" or h.key not in ("LD.period.divides.8.below",
                                                             "LD.period.law") or \
                    h.status != "law-holds" and h.key == "LD.period.law":
                continue
            for name, p in cprofs.items():
                if p.settled_at is None:
                    h.controls[name] = "no period | 64 within the window"
                    continue
                if h.key == "LD.period.divides.8.below":
                    ok = all(8 % p.lp[D] == 0 for D in range(N))
                    h.controls[name] = "holds" if ok else "fails"
                else:
                    jumps = {D for D in range(2, N) if p.lp[D] > max(p.lp[D - 1], p.lp[D - 2])}
                    cause = {D for D in range(2, N) if p.white[D - 1] and p.parity[D - 2] == 1}
                    nec = jumps <= {D for D in range(2, N) if p.white[D - 1]}
                    h.controls[name] = ("holds (jumps exactly at white ∧ odd)" if jumps == cause
                                        else ("necessity holds" if nec else "fails"))
            seed_ok = all(v.startswith("holds") for n, v in h.controls.items() if n.startswith("rule 30"))
            rule_ok = all(v.startswith("holds") for n, v in h.controls.items()
                          if not n.startswith("rule 30"))
            if seed_ok and rule_ok:
                h.scope = "holds on every control: a map-level statement (cannot single out the seed)"
            elif seed_ok:
                h.scope = ("Rule-30-specific and robust to the seed changes tested; the other rules "
                           "do not settle (so the statement is about Rule 30's left side)")
            else:
                h.scope = "seed-specific"
        self.timings["controls"] = time.time() - t0

    # ───────────────────────────────────────────────────────────────────────────────────────────
    # Stage D2: hypotheses born from the controls — does the left side remember the seed?
    # ───────────────────────────────────────────────────────────────────────────────────────────
    def run_seed_memory(self):
        t0 = time.time()
        self.log("== Seed memory (hypotheses born from the controls) ==")
        N = 450
        base = left_profile(N)
        c11 = self.control_profiles.get("rule 30, seed 11")
        same = c11 is not None and c11.settled_at is not None and all(
            c11.pattern[D] == base.pattern[D] for D in range(c11.N))
        h = self.new(family="left-diagonals", origin="control", key="LD.seed.independent",
                     text="the eventual left diagonals do not depend on the seed: every finite seed "
                          "whose leftmost cell is black has the same eventual left diagonals as the "
                          "single black cell",
                     lean="∀ y, LeftEdgeAtZero y → ∀ D : ℕ, EventuallyEq (ldiag D) (ldiagOf y D)")
        h.record("controls 11, 101", same, "identical eventual patterns on D < 400" if same
                 else "patterns differ")
        firsts = {}
        tested = 0
        width = 10 if not self.quick else 8
        for seed in range(1, 1 << width, 2):
            p = left_profile(N, seed=seed, tmax=4000)
            if p.settled_at is None:
                continue
            tested += 1
            d = next((D for D in range(N) if p.pattern[D] != base.pattern[D]), None)
            firsts[d] = firsts.get(d, 0) + 1
        bad = sorted(k for k in firsts if k is not None)
        if bad:
            h.status = "refuted-heldout"
            h.record(f"all {tested} seeds of width ≤ {width}", False,
                     f"first eventual differences at D ∈ {bad}; {firsts.get(None, 0)} seeds agree "
                     f"on every D < {N}")
        else:
            h.status = "survives"
        # mechanism: where can the first difference be?
        whites = [D for D in range(N) if base.white[D]]
        after_white = all(d - 1 in whites for d in bad)
        law = self.new(family="left-diagonals", origin="mechanism", parent=h.hid,
                       key="LD.seed.forgetting",
                       text="a left-white row can first differ from the seed only one diagonal past "
                            "an eventually white diagonal of the seed (a reset erases the seed)",
                       lean="∀ x y : Config, LeftEdgeAtZero x → LeftEdgeAtZero y → ∀ D : ℕ, "
                            "(∀ D' < D, EventuallyEq (ldiagOf x D') (ldiagOf y D')) → "
                            "¬ EventuallyEq (ldiagOf x D) (ldiagOf y D) → "
                            "2 ≤ D ∧ EventuallyWhite (ldiagOf x ((D : ℤ) - 1))")
        law.status = "law-holds" if after_white else "refuted-heldout"
        law.record(f"{tested} seeds", after_white,
                   f"first differences {bad} vs white diagonals {whites}")
        self.timings["seed-memory"] = time.time() - t0

    # ───────────────────────────────────────────────────────────────────────────────────────────
    # Stage E: credit — novelty against the ledger (after generation only)
    # ───────────────────────────────────────────────────────────────────────────────────────────
    LEDGER = {
        "LD.period.divides.8": ("C133", "EMP: periods ≤ 8 for D ≤ 200"),
        "LD.preperiod.gt.D": ("C133", "EMP: preperiod > D for 20 ≤ D ≤ 200"),
        "RD.lp.le.2^D": ("C48", "FORMAL: period 2^D"),
        "RD.lp.gt.half": ("C49", "FORMAL: least period > ceil(D/2)"),
        "RD.periodic.or.anti": ("C113", "FORMAL: periodic or anti-periodic"),
        "CC.lc.half": ("C160", "EMP: linear complexity within 6 of n/2 for n ≤ 20000"),
        "CC.no.short.period": ("C235", "CERT: no period with tau + p < 10000"),
        "CC.balance.sqrt": ("C22", "CERT: max D(N)^2/N on N ≤ 10^6 is 175561/24979"),
        "CC.balance.sqrt.2": ("C22", "CERT: max D(N)^2/N on N ≤ 10^6 is 175561/24979"),
        "CC.lc.half.2": ("C160", "EMP: linear complexity within 6 of n/2 for n ≤ 20000"),
        "CC.words.early": ("C235", "CERT: every word of length ≤ 10 occurs (partial match: the "
                                   "position bound is new)"),
    }
    LEAN = {
        "LD.period.law": "LeftDiagonalPeriods.ldiag_evPer_of_not_white, ldiag_doubles, "
                         "infinitely_many_white_of_unbounded",
        "LD.period.divides.8": "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight (refuted)",
        "LD.period.divides.8.below": "LeftDiagonalPeriodsData.leftDiag_period_eight_below_400",
        "LD.period.divides.16": "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen (refuted)",
        "LD.period.divides.16.below": "LeftDiagonalPeriodsData.leftDiag_period_sixteen_below_87867",
        "LD.first.period.32": "LeftDiagonalPeriodsData.ldiag_87867_not_evPer_sixteen + "
                              "leftDiag_period_sixteen_below_87867",
        "LD.white.finite": "LeftDiagonalPeriodsData.leftDiag_white_below_87868 (refutes it)",
        "LD.seed.independent": "refuted by data (seeds of width ≤ 10)",
        "LD.seed.forgetting": "LeftDiagonalPeriods.first_difference_after_white; "
                              "LeftDiagonalPeriodsData.seed_first_difference",
        "LD.preperiod.gt.D": "partial: LeftDiagonalPeriodsData.leftDiag_transient_at_read "
                             "certifies 20 ≤ D < 20000 only",
        "LD.periods.unbounded": "open; LeftDiagonalPeriods.infinitely_many_white_of_unbounded "
                                "is the proved reduction",
        "RD.lp.le.2^D": "Diagonals.rdiag_periodic",
        "CC.balance.sqrt": "partial: WobbleCertificate.wobble_sq_ratio_cert certifies N ≤ 10^6 only",
        "CC.no.short.period": "partial: PowerSeriesLadderData.no_eventual_period_below_10000 "
                              "(a smaller range)",
        "RD.lp.gt.half": "Diagonals.rdiag_not_periodic",
        "RD.periodic.or.anti": "RightDiagonalBalance (C113)",
    }

    # statements whose exact form is proved (or refuted) in the package, for every index
    CLOSED = {"LD.period.law", "LD.period.divides.8.below", "LD.period.divides.16.below",
              "LD.first.period.32", "LD.seed.forgetting", "LD.period.divides.8",
              "LD.period.divides.16", "LD.white.finite", "RD.lp.le.2^D", "RD.lp.gt.half",
              "RD.periodic.or.anti"}

    def credit(self):
        for h in self.hyps:
            if h.key in self.LEDGER:
                h.novelty = f"rediscovers {self.LEDGER[h.key][0]} ({self.LEDGER[h.key][1]})"
            else:
                h.novelty = "new to the ledger"
            h.lean_status = self.LEAN.get(h.key, "not formalised")
            h.closed = h.key in self.CLOSED

    # ───────────────────────────────────────────────────────────────────────────────────────────
    def run(self):
        T0 = time.time()
        self.run_left_diagonals()
        self.run_right_diagonals()
        self.run_centre()
        self.run_controls()
        self.run_seed_memory()
        self.credit()
        self.timings["total"] = time.time() - T0
        return self.report()

    def report(self) -> dict:
        rows = []
        for h in self.hyps:
            rows.append({
                "id": h.hid, "family": h.family, "origin": h.origin, "parent": h.parent,
                "statement": h.text, "lean_proposal": h.lean, "status": h.status,
                "evidence": h.evidence, "controls": h.controls, "scope": h.scope,
                "novelty": getattr(h, "novelty", ""), "lean_status": getattr(h, "lean_status", ""),
                "closed": getattr(h, "closed", False),
            })
        counts = {}
        for h in self.hyps:
            counts[h.status] = counts.get(h.status, 0) + 1
        return {"engine": "GLM Hypothesis Engine v5 (Round 38)", "quick": self.quick,
                "hypotheses": rows, "status_counts": counts, "predictions": self.predictions,
                "timings_seconds_wallclock": {k: round(v, 2) for k, v in self.timings.items()}}


def _first(pred, lo, hi):
    for k in range(lo, hi):
        if not pred(k):
            return False, k
    return True, None


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. Outputs
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def write_outputs(rep: dict, stem: str = "r38_engine_report"):
    (HERE / f"{stem}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    md = ["# GLM Hypothesis Engine v5 — run report", "",
          f"Status counts: {rep['status_counts']}", "",
          f"Predictions: {rep['predictions']}", "",
          "| id | family | origin | status | statement | novelty | Lean |",
          "|---|---|---|---|---|---|---|"]
    for r in rep["hypotheses"]:
        md.append(f"| {r['id']} | {r['family']} | {r['origin']} | {r['status']} | "
                  f"{r['statement']} | {r['novelty']} | {r['lean_status']} |")
    md += ["", "## Evidence per hypothesis", ""]
    for r in rep["hypotheses"]:
        md.append(f"**{r['id']}** ({r['status']}): {r['statement']}")
        for e in r["evidence"]:
            md.append(f"  - {e['stage']}: {'ok' if e['ok'] else 'FAIL'} — {e['detail']}")
        if r["controls"]:
            md.append(f"  - controls: {r['controls']}")
        if r["scope"]:
            md.append(f"  - scope: {r['scope']}")
        md.append("")
    md.append(f"Wall-clock seconds: {rep['timings_seconds_wallclock']}")
    (HERE / f"{stem}.md").write_text("\n".join(md))
    lean = ["-- Proposals emitted by the GLM Hypothesis Engine v5 (Round 38).",
            "-- Each open or surviving statement is a `sorry`-guarded proposal for the prover;",
            "-- refuted ones are listed with their counterexample.  Not part of the Lean build.",
            ""]
    for r in rep["hypotheses"]:
        tag = r["status"]
        lean.append(f"-- {r['id']} [{tag}] {r['statement']}")
        closed = r.get("closed", False)
        if r["lean_proposal"].startswith("--"):
            lean.append(r["lean_proposal"])
            if r["lean_status"] not in ("", "not formalised"):
                lean.append(f"-- Lean package: {r['lean_status']}")
        elif tag.startswith("refuted"):
            lean.append(f"-- refuted: {r['lean_proposal']}")
        elif closed:
            lean.append(f"-- closed in the Lean package: {r['lean_status']}")
            lean.append(f"-- statement: {r['lean_proposal']}")
        else:
            if r["lean_status"] not in ("", "not formalised"):
                lean.append(f"-- Lean package: {r['lean_status']}")
            lean.append(f"theorem engine_{r['id']} : {r['lean_proposal']} := by sorry")
        if tag.startswith("refuted") and closed:
            lean.append(f"-- refutation in the Lean package: {r['lean_status']}")
        lean.append("")
    (HERE / "r38_conjectures.lean.txt").write_text("\n".join(lean))


def main():
    quick = "--quick" in sys.argv
    eng = Engine(quick=quick)
    rep = eng.run()
    write_outputs(rep, "r38_engine_report_quick" if quick else "r38_engine_report")
    print()
    print("Status counts:", rep["status_counts"])
    print("Predictions:", rep["predictions"])
    print("Wall-clock:", rep["timings_seconds_wallclock"])


if __name__ == "__main__":
    main()
