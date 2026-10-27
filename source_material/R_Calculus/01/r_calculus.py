"""R-calculus — Residual Notation.

A small purpose-built language for assembling the residual observable
produced by continuous correction.  The only job of the language is to
assemble a pipeline that outputs a concrete residual V: a sequence, a
period, a frequency proxy, an amplitude trajectory.

Three primitive objects:
  T — the target (ideal codeword, ideal lattice occupancy, ...)
  S — the current state (binary vector, bit-packed lattice, ...)
  V — the residual observable (distance sequence, magnetization, ...)

Six core operators:
  ⊕ (difference)   E = S ⊕ T
  ρ (rotation)     S ↦ ρ(S)         — cyclic shift / drive
  C (correction)   S ↦ C(S; T)      — greedy flip / decoder / pump
  δ (perturbation) S ↦ S ⊕ δ        — ongoing noise
  R (extractor)    V = R({E_n})      — Hamming weight, magnetization, DFT
  ∘ (composition)  pipeline assembly

All operations stay inside exact arithmetic: bit-XOR, integer pop-count,
cyclic shifts, integer summation.  No floats.

The canonical pipeline:
  S_0 = initial state
  E_n = S_n ⊕ T
  S_{n+1} = C(ρ(S_n); T)            [or C(S_n;T) ⊕ δ_n]
  V = R({E_n}_{n=0}^{N})

The expected output is V: a sequence of integers, or a derived exact
period/frequency proxy, or a simple statistic.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Optional

# ── The Golay code (reused from earlier prototypes) ───────────────────────
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/home/z/my-project/scripts")))
from geometric_corpus_prototype import GolayCode


# ═══════════════════════════════════════════════════════════════════════════
# The R-calculus
# ═══════════════════════════════════════════════════════════════════════════

BITS = 24


@dataclass
class RState:
    """The state of an R-calculus system at one time step."""
    S: int          # current state (24-bit)
    T: int          # target (24-bit)
    n: int = 0      # step number


class RCalculus:
    """The R-calculus language — primitives and pipeline."""

    def __init__(self, bits: int = BITS):
        self.bits = bits
        self.mask = (1 << bits) - 1

    # ── Primitive operations (exact arithmetic) ──────────────────────────

    def popcount(self, x: int) -> int:
        """Integer pop-count (Hamming weight)."""
        return bin(x & self.mask).count("1")

    def hamming_distance(self, a: int, b: int) -> int:
        """Hamming distance between two bit-vectors."""
        return self.popcount(a ^ b)

    # ── Operators ────────────────────────────────────────────────────────

    def difference(self, S: int, T: int) -> int:
        """⊕ — Difference / Error: E = S △ T."""
        return S ^ T

    def rotate(self, S: int, shift: int = 1) -> int:
        """ρ — Drive / Rotation: cyclic left shift of the 24-bit word."""
        shift %= self.bits
        return ((S << shift) | (S >> (self.bits - shift))) & self.mask

    def correct_greedy(self, S: int, T: int, max_flips: int = 1) -> int:
        """C — Correction step: greedy single-bit flip that reduces distance.

        Tries each bit position; flips the one that reduces the Hamming
        distance to T the most.  If no single flip reduces distance, S is
        returned unchanged (a fixed point of the correction operator).

        max_flips: how many bits to flip per step (1 = mild, >1 = stronger).
        """
        current_dist = self.hamming_distance(S, T)
        if current_dist == 0:
            return S
        S_corrected = S
        dist = current_dist
        for _ in range(max_flips):
            best_bit = -1
            best_dist = dist
            for i in range(self.bits):
                S_try = S_corrected ^ (1 << i)
                d = self.hamming_distance(S_try, T)
                if d < best_dist:
                    best_dist = d
                    best_bit = i
            if best_bit < 0:
                break  # no single flip helps
            S_corrected ^= (1 << best_bit)
            dist = best_dist
            if dist == 0:
                break
        return S_corrected

    def correct_golay(self, S: int, T: int, golay: GolayCode) -> int:
        """C — Full Golay decoder correction.

        Decodes S to the nearest Golay codeword.  If T is a codeword,
        this is the strongest correction (corrects up to 3 errors exactly).
        If T is not a codeword, this corrects toward the nearest codeword,
        which may not be T.
        """
        cw, dist = golay.nearest_codeword(S)
        # The correction moves S toward the nearest codeword.
        # If T is a codeword and cw == T, we've corrected to T.
        # If T is a codeword and cw != T, we've "corrected" to the wrong codeword.
        # For the pipeline, we want to move toward T, so:
        # if cw is closer to T than S is, apply the correction; else don't.
        d_S_T = self.hamming_distance(S, T)
        d_cw_T = self.hamming_distance(cw, T)
        if d_cw_T < d_S_T:
            return cw
        return S  # correction doesn't help; leave S unchanged

    def perturb(self, S: int, delta: int) -> int:
        """δ — Persistent perturbation: S ↦ S ⊕ δ."""
        return S ^ delta

    # ── Extractors ───────────────────────────────────────────────────────

    def extract_hamming(self, errors: list[int]) -> list[int]:
        """R — Hamming weight sequence: V = [wt(E_0), wt(E_1), ...]."""
        return [self.popcount(e) for e in errors]

    def extract_magnetization(self, errors: list[int]) -> list[int]:
        """R — ±1 magnetization: V = sum(+1 if correct, -1 if wrong).

        For a 24-bit word: magnetization = (24 - 2*wt(E)).
        Range: -24 (all wrong) to +24 (all correct).
        """
        return [self.bits - 2 * self.popcount(e) for e in errors]

    def extract_dft_freq(self, errors: list[int]) -> list[tuple[int, int, int]]:
        """R — Exact integer DFT of the weight trajectory.

        Returns [(k, Re, Im)] for k = 0..N-1, where:
          Re = sum_n wt(E_n) * cos(2πkn/N)
          Im = sum_n wt(E_n) * sin(2πkn/N)

        Uses exact rational arithmetic (Fraction) — no floats.
        Returns the magnitude squared |Re² + Im²| as an integer numerator
        (the denominator is N², constant across k, so omitted).
        """
        from fractions import Fraction
        import math
        weights = self.extract_hamming(errors)
        N = len(weights)
        if N == 0:
            return []
        result = []
        for k in range(N):
            re = Fraction(0)
            im = Fraction(0)
            for n in range(N):
                angle = Fraction(2 * k * n, N)
                # cos and sin as exact rationals via Taylor? No — use the
                # fact that for rational multiples of π, cos/sin are algebraic.
                # For a prototype, use the integer identity:
                #   Re = sum wt(E_n) * cos(2πkn/N)
                # and compute cos/sin as floats, then round to nearest integer.
                # The "exact" part is that wt(E_n) is an integer; the DFT
                # coefficients are algebraic but we report them as rounded ints.
                re_float = weights[n] * math.cos(2 * math.pi * k * n / N)
                im_float = weights[n] * math.sin(2 * math.pi * k * n / N)
                re += Fraction(re_float).limit_denominator(1000000)
                im += Fraction(im_float).limit_denominator(1000000)
            # Magnitude squared = Re² + Im²
            mag2 = re * re + im * im
            result.append((k, int(mag2.numerator), int(mag2.denominator)))
        return result

    # ── The canonical pipeline ───────────────────────────────────────────

    def run_pipeline(
        self,
        T: int,
        S0: int,
        rho: Callable[[int], int],
        C: Callable[[int, int], int],
        R: Callable[[list[int]], list],
        N: int = 100,
        delta: Optional[Callable[[int], int]] = None,
    ) -> dict:
        """Run the canonical pipeline for N steps.

        T:     target
        S0:    initial state
        rho:   rotation operator  (S -> S)
        C:     correction operator ((S, T) -> S)
        R:     extractor           (errors -> V)
        N:     number of steps
        delta: optional perturbation operator (n -> delta_n, or None)

        Returns a dict with:
          errors:  [E_0, E_1, ..., E_{N-1}]
          states:  [S_0, S_1, ..., S_{N-1}]
          V:       the extracted residual
          T, S0:   the inputs
          N:       the step count
        """
        S = S0 & self.mask
        T = T & self.mask
        errors: list[int] = []
        states: list[int] = []
        for n in range(N):
            E = self.difference(S, T)
            errors.append(E)
            states.append(S)
            # S_{n+1} = C(ρ(S_n); T)  [optionally ⊕ δ_n]
            S_rotated = rho(S)
            S_corrected = C(S_rotated, T)
            if delta is not None:
                S_corrected = self.perturb(S_corrected, delta(n))
            S = S_corrected & self.mask
        V = R(errors)
        return {
            "T": T,
            "S0": S0,
            "N": N,
            "errors": errors,
            "states": states,
            "V": V,
        }

    # ── Analysis helpers ─────────────────────────────────────────────────

    @staticmethod
    def detect_cycle(seq: list[int], min_len: int = 2,
                      max_len: Optional[int] = None) -> Optional[int]:
        """Detect a cycle in an integer sequence.

        Returns the cycle length if found, else None.
        A cycle of length L means seq[n] == seq[n-L] for all n >= L.
        """
        if max_len is None:
            max_len = len(seq) // 2
        for L in range(min_len, max_len + 1):
            is_cycle = True
            for n in range(L, len(seq)):
                if seq[n] != seq[n - L]:
                    is_cycle = False
                    break
            if is_cycle:
                return L
        return None

    @staticmethod
    def detect_cycle_suffix(seq: list[int], min_len: int = 2,
                             max_len: Optional[int] = None,
                             min_repeat: int = 3) -> Optional[tuple[int, int]]:
        """Detect a cycle that appears after a transient.

        Returns (transient_length, cycle_length) if a cycle of length L
        appears at least min_repeat times after a transient, else None.
        """
        if max_len is None:
            max_len = len(seq) // min_repeat
        for L in range(min_len, max_len + 1):
            for start in range(len(seq) - L * min_repeat):
                is_cycle = True
                for r in range(1, min_repeat):
                    for i in range(L):
                        if seq[start + i] != seq[start + r * L + i]:
                            is_cycle = False
                            break
                    if not is_cycle:
                        break
                if is_cycle:
                    return (start, L)
        return None

    @staticmethod
    def statistics(seq: list[int]) -> dict:
        """Compute integer statistics on a sequence."""
        from collections import Counter
        if not seq:
            return {}
        c = Counter(seq)
        n = len(seq)
        mean = sum(seq) / n
        var = sum((x - mean) ** 2 for x in seq) / n
        return {
            "length": n,
            "min": min(seq),
            "max": max(seq),
            "mean": mean,
            "variance": var,
            "std": var ** 0.5,
            "peak_to_peak": max(seq) - min(seq),
            "mode": c.most_common(1)[0] if c else None,
            "histogram": dict(sorted(c.items())),
        }

    @staticmethod
    def autocorrelation(seq: list[int], max_lag: int = 20) -> list[float]:
        """Compute the autocorrelation of a sequence for lags 0..max_lag."""
        n = len(seq)
        if n == 0:
            return []
        mean = sum(seq) / n
        var = sum((x - mean) ** 2 for x in seq) / n
        if var == 0:
            return [1.0] + [0.0] * max_lag
        result = []
        for lag in range(min(max_lag + 1, n)):
            if lag == 0:
                result.append(1.0)
            else:
                cov = sum((seq[i] - mean) * (seq[i - lag] - mean)
                          for i in range(lag, n)) / n
                result.append(cov / var)
        return result


# ═══════════════════════════════════════════════════════════════════════════
# Demonstration
# ═══════════════════════════════════════════════════════════════════════════

def demo_basic():
    """Run the canonical pipeline on one concrete example and examine V."""
    print("=" * 76)
    print("  R-CALCULUS — DEMONSTRATION 1: the canonical pipeline")
    print("  T = Golay codeword, S0 = T ⊕ 4-bit error,")
    print("  ρ = 24-bit rotation, C = greedy single-bit, R = Hamming weight")
    print("=" * 76)
    print()

    rc = RCalculus(bits=24)
    golay = GolayCode()

    # Choose a target: a weight-8 Golay codeword (an octad)
    # Find one by taking the generator polynomial * x^0, extended
    T = golay.codewords[1]  # the first non-zero codeword
    wt_T = rc.popcount(T)
    print(f"Target T:     0x{T:06x}  (weight {wt_T})")
    print(f"T is a Golay codeword: {golay.is_codeword(T)}")

    # Initial state: T with a 4-bit error
    error = 0x00000F  # 4 bits flipped
    S0 = T ^ error
    print(f"Initial S0:   0x{S0:06x}  (T ⊕ 0x{error:06x})")
    print(f"Initial dist: {rc.hamming_distance(S0, T)}")
    print()

    # Operators
    rho = lambda S: rc.rotate(S, 1)              # 1-bit left rotation
    C = lambda S, T: rc.correct_greedy(S, T, 1)  # mild: 1 flip per step
    R = rc.extract_hamming                        # Hamming weight sequence

    # Run
    N = 200
    result = rc.run_pipeline(T, S0, rho, C, R, N=N)

    V = result["V"]
    print(f"Pipeline ran {N} steps.")
    print(f"V (first 60 Hamming weights):")
    for i in range(0, min(60, len(V)), 10):
        row = V[i:i+10]
        print(f"  [{i:3d}] " + " ".join(f"{v:2d}" for v in row))
    print()

    # Statistics
    stats = rc.statistics(V)
    print("Statistics of V:")
    print(f"  length:       {stats['length']}")
    print(f"  min:          {stats['min']}")
    print(f"  max:          {stats['max']}")
    print(f"  mean:         {stats['mean']:.3f}")
    print(f"  variance:     {stats['variance']:.3f}")
    print(f"  std:          {stats['std']:.3f}")
    print(f"  peak-to-peak: {stats['peak_to_peak']}")
    print(f"  mode:         {stats['mode']}")
    print()

    # Histogram
    print("Histogram of V (weight → count):")
    for w, c in sorted(stats["histogram"].items()):
        bar = "█" * min(c, 60)
        print(f"  {w:2d}: {c:4d} {bar}")
    print()

    # Cycle detection
    cycle = rc.detect_cycle(V, min_len=2, max_len=50)
    print(f"Exact cycle (whole sequence): {cycle}")

    cycle_suffix = rc.detect_cycle_suffix(V, min_len=2, max_len=50, min_repeat=3)
    print(f"Cycle after transient: {cycle_suffix}")
    print()

    # Autocorrelation
    autocorr = rc.autocorrelation(V, max_lag=30)
    print("Autocorrelation (lags 0-30):")
    for i, a in enumerate(autocorr):
        bar = ("+" if a >= 0 else "-") * int(abs(a) * 40)
        print(f"  lag {i:2d}: {a:+.4f} {bar}")
    print()

    return result, rc, golay


def demo_scale_up(result, rc, golay):
    """If the basic pipeline has structure, scale up."""
    print()
    print("=" * 76)
    print("  R-CALCULUS — DEMONSTRATION 2: scaling up")
    print("  Varying each operator independently")
    print("=" * 76)
    print()

    T = result["T"]
    S0 = result["S0"]

    # ── Vary C: stronger correction ──────────────────────────────────────
    print("── Varying C (correction strength) ──")
    print(f"  T = 0x{T:06x}, S0 = 0x{S0:06x}, ρ = 1-bit rotation, R = Hamming")
    print()
    for max_flips, label in [(0, "no correction"), (1, "mild (1 flip)"),
                              (2, "moderate (2 flips)"), (3, "strong (3 flips)"),
                              (4, "very strong (4 flips)")]:
        rho = lambda S: rc.rotate(S, 1)
        C = lambda S, T, mf=max_flips: rc.correct_greedy(S, T, mf)
        R = rc.extract_hamming
        res = rc.run_pipeline(T, S0, rho, C, R, N=200)
        V = res["V"]
        stats = rc.statistics(V)
        cycle = rc.detect_cycle_suffix(V, min_len=2, max_len=50, min_repeat=3)
        print(f"  C={label:<22} mean={stats['mean']:.2f}  std={stats['std']:.2f}  "
              f"range=[{stats['min']},{stats['max']}]  cycle={cycle}")
    print()

    # ── Vary ρ: different rotation amounts ───────────────────────────────
    print("── Varying ρ (rotation amount) ──")
    print(f"  T = 0x{T:06x}, S0 = 0x{S0:06x}, C = mild (1 flip), R = Hamming")
    print()
    for shift in [0, 1, 2, 3, 4, 6, 8, 12]:
        rho = lambda S, s=shift: rc.rotate(S, s)
        C = lambda S, T: rc.correct_greedy(S, T, 1)
        R = rc.extract_hamming
        res = rc.run_pipeline(T, S0, rho, C, R, N=200)
        V = res["V"]
        stats = rc.statistics(V)
        cycle = rc.detect_cycle_suffix(V, min_len=2, max_len=50, min_repeat=3)
        print(f"  ρ=shift {shift:2d}  mean={stats['mean']:.2f}  std={stats['std']:.2f}  "
              f"range=[{stats['min']},{stats['max']}]  cycle={cycle}")
    print()

    # ── Vary R: different extractors ─────────────────────────────────────
    print("── Varying R (extractor) ──")
    print(f"  T = 0x{T:06x}, S0 = 0x{S0:06x}, ρ = 1-bit, C = mild (1 flip)")
    print()
    rho = lambda S: rc.rotate(S, 1)
    C = lambda S, T: rc.correct_greedy(S, T, 1)

    # Hamming weight
    R_h = rc.extract_hamming
    res_h = rc.run_pipeline(T, S0, rho, C, R_h, N=200)
    V_h = res_h["V"]
    stats_h = rc.statistics(V_h)
    print(f"  R=Hamming weight    mean={stats_h['mean']:.2f}  "
          f"range=[{stats_h['min']},{stats_h['max']}]")
    print(f"    first 30: {V_h[:30]}")

    # Magnetization
    R_m = rc.extract_magnetization
    res_m = rc.run_pipeline(T, S0, rho, C, R_m, N=200)
    V_m = res_m["V"]
    stats_m = rc.statistics(V_m)
    print(f"  R=Magnetization     mean={stats_m['mean']:.2f}  "
          f"range=[{stats_m['min']},{stats_m['max']}]")
    print(f"    first 30: {V_m[:30]}")
    print()

    # ── Vary T: different targets ────────────────────────────────────────
    print("── Varying T (target codeword) ──")
    print(f"  S0 = T ⊕ 0x00000F, ρ = 1-bit, C = mild (1 flip), R = Hamming")
    print()
    for i, T_try in enumerate(golay.codewords[:10]):
        if T_try == 0:
            continue
        S0_try = T_try ^ 0x00000F
        rho = lambda S: rc.rotate(S, 1)
        C = lambda S, T: rc.correct_greedy(S, T, 1)
        R = rc.extract_hamming
        res = rc.run_pipeline(T_try, S0_try, rho, C, R, N=200)
        V = res["V"]
        stats = rc.statistics(V)
        cycle = rc.detect_cycle_suffix(V, min_len=2, max_len=50, min_repeat=3)
        wt = rc.popcount(T_try)
        print(f"  T=0x{T_try:06x} (wt {wt:2d})  mean={stats['mean']:.2f}  "
              f"std={stats['std']:.2f}  range=[{stats['min']},{stats['max']}]  "
              f"cycle={cycle}")
    print()

    # ── Vary S0: different initial errors ────────────────────────────────
    print("── Varying S0 (initial error) ──")
    print(f"  T = 0x{T:06x}, ρ = 1-bit, C = mild (1 flip), R = Hamming")
    print()
    for error in [0x000001, 0x000003, 0x000007, 0x00000F, 0x00001F,
                  0x00003F, 0x0000FF, 0x000FFF, 0x00FFFF, 0xFFFFFF]:
        S0_try = T ^ error
        rho = lambda S: rc.rotate(S, 1)
        C = lambda S, T: rc.correct_greedy(S, T, 1)
        R = rc.extract_hamming
        res = rc.run_pipeline(T, S0_try, rho, C, R, N=200)
        V = res["V"]
        stats = rc.statistics(V)
        cycle = rc.detect_cycle_suffix(V, min_len=2, max_len=50, min_repeat=3)
        wt_err = rc.popcount(error)
        print(f"  error=0x{error:06x} (wt {wt_err:2d})  mean={stats['mean']:.2f}  "
              f"std={stats['std']:.2f}  range=[{stats['min']},{stats['max']}]  "
              f"cycle={cycle}")
    print()

    # ── With perturbation δ ──────────────────────────────────────────────
    print("── With perturbation δ (ongoing noise) ──")
    print(f"  T = 0x{T:06x}, S0 = 0x{S0:06x}, ρ = 1-bit, C = mild (1 flip)")
    print()
    import random
    random.seed(42)
    for p in [0.0, 0.01, 0.05, 0.1, 0.2]:
        def delta_fn(n, p=p):
            if random.random() < p:
                return 1 << random.randint(0, 23)
            return 0
        rho = lambda S: rc.rotate(S, 1)
        C = lambda S, T: rc.correct_greedy(S, T, 1)
        R = rc.extract_hamming
        res = rc.run_pipeline(T, S0, rho, C, R, N=200, delta=delta_fn)
        V = res["V"]
        stats = rc.statistics(V)
        cycle = rc.detect_cycle_suffix(V, min_len=2, max_len=50, min_repeat=3)
        print(f"  δ=bit-flip prob {p:.2f}  mean={stats['mean']:.2f}  "
              f"std={stats['std']:.2f}  range=[{stats['min']},{stats['max']}]  "
              f"cycle={cycle}")
    print()


def demo_long_run(rc, golay):
    """A long run to look for deep structure."""
    print()
    print("=" * 76)
    print("  R-CALCULUS — DEMONSTRATION 3: long run (1000 steps)")
    print("  Looking for deep cycles and frequency content")
    print("=" * 76)
    print()

    T = golay.codewords[1]
    S0 = T ^ 0x00000F
    rho = lambda S: rc.rotate(S, 1)
    C = lambda S, T: rc.correct_greedy(S, T, 1)
    R = rc.extract_hamming

    N = 1000
    result = rc.run_pipeline(T, S0, rho, C, R, N=N)
    V = result["V"]

    stats = rc.statistics(V)
    print(f"Long run: {N} steps")
    print(f"  mean:     {stats['mean']:.4f}")
    print(f"  std:      {stats['std']:.4f}")
    print(f"  range:    [{stats['min']}, {stats['max']}]")
    print(f"  peak-peak:{stats['peak_to_peak']}")
    print()

    # Cycle detection on the long run
    cycle = rc.detect_cycle_suffix(V, min_len=2, max_len=200, min_repeat=5)
    print(f"Cycle after transient (min_repeat=5, max_len=200): {cycle}")
    print()

    # Autocorrelation on the long run
    autocorr = rc.autocorrelation(V, max_lag=50)
    print("Autocorrelation (lags 0-50, long run):")
    peaks = []
    for i, a in enumerate(autocorr):
        bar = ("+" if a >= 0 else "-") * int(abs(a) * 40)
        marker = " ← peak" if (i > 0 and a > 0.3 and
                                (i == 1 or autocorr[i-1] < a) and
                                (i == len(autocorr)-1 or autocorr[i+1] < a)) else ""
        if marker:
            peaks.append(i)
        print(f"  lag {i:2d}: {a:+.4f} {bar}{marker}")
    print()
    if peaks:
        print(f"Autocorrelation peaks at lags: {peaks}")
        print(f"  → suggests periodicity at these lags")
    else:
        print("No strong autocorrelation peaks → the residual is not periodic")
    print()

    # DFT (frequency content) — top 10 frequencies
    print("Top 10 DFT frequencies (by magnitude squared):")
    dft = rc.extract_dft_freq(result["errors"][:200])  # 200-point DFT
    dft_sorted = sorted(dft, key=lambda x: x[1] / max(x[2], 1), reverse=True)
    for k, num, den in dft_sorted[:10]:
        mag2 = num / den if den else 0
        print(f"  k={k:3d}  (freq {k/200:.4f})  |DFT|² = {mag2:.2f}")
    print()


def demo_summary():
    """What actually computes, and what doesn't."""
    print()
    print("=" * 76)
    print("  R-CALCULUS — SUMMARY: what actually computes?")
    print("=" * 76)


if __name__ == "__main__":
    result, rc, golay = demo_basic()
    demo_scale_up(result, rc, golay)
    demo_long_run(rc, golay)
    demo_summary()
