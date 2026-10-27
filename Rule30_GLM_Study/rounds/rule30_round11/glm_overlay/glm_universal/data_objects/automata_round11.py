"""``glm_universal.data_objects.automata_round11`` -- Round 11 carriers of the automata register.

Round 11 of the Rule 30 study.  Three new families of carriers for the wheel-30 impulse run,
each with its exact value, evidence class and Lean theorem (Lean package
``RequestProject/GLM/Rule30``, namespace ``GLM.Rule30``):

* **The seed's right edge** (track A).  ``r30_seed_right_edge_zero``: the boundary condition that
  singles out the seed on the right (every right diagonal is white at time 0 except diagonal 0,
  and the diagonals outside the light cone are white for ever).  ``r30_rdiag_D``: the right
  diagonal ``rdiag D t = a(t)(t - D)``, its least period, its black cells per period, whether it is
  anti-periodic, and its frequency.  ``r30_rdiag_balanced``: the theorem that infinitely many right
  diagonals are exactly balanced (bounded wobble), and ``r30_rdiag_5`` the proved counterexample
  showing that not all are.
* **The off-centre observer** (track B).  ``r30_wobble_D_N_column_c``: the wobble ``D_c(N)`` of
  column ``c``; ``r30_chiral_gap_c_N = D_c(N) - D_{-c}(N)``, the part of the wobble that only an
  off-centre observer can see; ``r30_chiral_gap_first_c``: the first ``N`` at which it is non-zero.
* **The parity count** (track C).  ``r30_white_diagonal_parity``: ``whiteDiagonalCount n`` is odd
  for **every** ``n >= 2`` (proved in Round 8, not only checked to ``n = 14`` / ``36``).

Exact integers only.  Values computed here are ``EMP`` unless a Lean theorem covers the value
itself; values beyond the in-module range are quoted from ``rule30_round11/r11_diagonals.c`` and
``rule30_round11/r11_offcentre_wobble.c`` (exact C programs, outputs in the same folder).
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Sequence, Tuple

__all__ = ["right_diagonals", "least_period", "diagonal_record", "column_wobbles",
           "round11_objects", "DIAGONAL_RANGE", "WOBBLE_COLUMNS", "WOBBLE_N",
           "QUOTED_DIAGONALS", "QUOTED_COLUMN_WOBBLE", "CHIRAL_FIRST", "CHIRAL_MAX_1E6"]

#: Diagonals computed when the register loads (``T = 2^DIAGONAL_RANGE`` steps).
DIAGONAL_RANGE = 12

#: Least period and black cells per period for diagonals 13..39 (EMP, r11_diagonals.c, exact).
QUOTED_DIAGONALS: Dict[int, Tuple[int, int]] = {
    13: (64, 29), 14: (64, 29), 15: (128, 64), 16: (256, 128), 17: (256, 128),
    18: (256, 128), 19: (256, 126), 20: (256, 127), 21: (256, 118), 22: (256, 122),
    23: (256, 125), 24: (512, 256), 25: (1024, 512), 26: (1024, 516), 27: (2048, 1024),
    28: (2048, 1022), 29: (4096, 2048), 30: (4096, 2026), 31: (4096, 2021),
    32: (4096, 2062), 33: (4096, 2034), 34: (8192, 4096), 35: (8192, 4047),
    36: (16384, 8192), 37: (32768, 16384), 38: (32768, 16376), 39: (65536, 32768),
}

#: Diagonals 13..39 that r11_diagonals.c found anti-periodic (checked directly, not inferred).
QUOTED_ANTI = {15, 16, 24, 25, 27, 29, 34, 36, 37, 39}

#: Columns and lengths of the off-centre wobble carriers.
WOBBLE_COLUMNS = tuple(range(-5, 6))
WOBBLE_N = (100, 1000, 10000)

#: ``D_c(N)`` for ``N = 10^5, 10^6`` (EMP, r11_offcentre_wobble.c, exact).
QUOTED_COLUMN_WOBBLE: Dict[int, Dict[int, int]] = {
    100000: {-5: 6, -4: -356, -3: 338, -2: -216, -1: -256, 0: 196, 1: 118, 2: -186,
             3: 316, 4: 150, 5: 374},
    1000000: {-5: 286, -4: 430, -3: 292, -2: -904, -1: 1072, 0: 1536, 1: 220, 2: -58,
              3: -1440, 4: 720, 5: 1806},
}

#: First ``N`` with ``D_c(N) != D_{-c}(N)`` (FORMAL for c = 1..5: chiralGap_first).
CHIRAL_FIRST = {1: 3, 2: 6, 3: 5, 4: 9, 5: 7}

#: ``max_{N <= 10^6} |D_c(N) - D_{-c}(N)|`` (EMP, r11_offcentre_wobble.c).
CHIRAL_MAX_1E6 = {1: 886, 2: 1170, 3: 1754, 4: 1924, 5: 2918}


@lru_cache(maxsize=4)
def right_diagonals(Dmax: int, T: int) -> Tuple[Tuple[int, ...], ...]:
    """``rdiag D t = a(t)(t - D)`` for ``D <= Dmax``, ``t < T``, from the bit-parallel step
    ``r -> (r << 2) xor ((r << 1) or r)`` (Lean ``rowStep``; bit ``2t - D`` of row ``t``,
    ``rdiag_eq_fast``)."""
    rows = [[0] * T for _ in range(Dmax + 1)]
    r = 1
    for t in range(T):
        low = r >> max(0, 2 * t - Dmax)
        for D in range(Dmax + 1):
            k = 2 * t - D
            if k >= 0:
                rows[D][t] = (low >> (k - max(0, 2 * t - Dmax))) & 1
        r = (r << 2) ^ ((r << 1) | r)
    return tuple(tuple(x) for x in rows)


def least_period(seq: Sequence[int], bound: int) -> int:
    """The least ``p | bound`` (``bound`` a power of two) with ``seq[t+p] = seq[t]`` on the
    whole sequence; ``seq`` must have length at least ``bound``."""
    p = 1
    while p < bound:
        if all(seq[t] == seq[t + p] for t in range(len(seq) - p)):
            return p
        p *= 2
    return bound


@lru_cache(maxsize=64)
def diagonal_record(D: int) -> Dict[str, object]:
    """Least period, black cells per period, anti-periodicity and frequency of diagonal ``D``."""
    if D <= DIAGONAL_RANGE:
        T = 2 ** DIAGONAL_RANGE
        seq = right_diagonals(DIAGONAL_RANGE, T)[D]
        P = least_period(seq, 2 ** D)
        k = sum(seq[:P])
        anti = P >= 2 and all(seq[t + P // 2] == 1 - seq[t] for t in range(T - P // 2))
        source = "computed in this register (exact, T = 4096 steps)"
    else:
        P, k = QUOTED_DIAGONALS[D]
        anti = D in QUOTED_ANTI
        source = "quoted from rule30_round11/r11_diagonals.c (exact, T = 2^17 steps)"
    return {"D": D, "period": P, "ones": k, "frequency": Fraction(k, P), "anti": anti,
            "source": source}


@lru_cache(maxsize=1)
def column_wobbles() -> Dict[Tuple[int, int], int]:
    from . import automata as ca
    out: Dict[Tuple[int, int], int] = {}
    Nmax = max(WOBBLE_N)
    for c in WOBBLE_COLUMNS:
        bits = ca.evolve_impulse_column(30, Nmax, c)
        for N in WOBBLE_N:
            out[(c, N)] = ca.wobble(bits, N)
    for N, row in QUOTED_COLUMN_WOBBLE.items():
        for c, v in row.items():
            out[(c, N)] = v
    return out


def _tok(c: int) -> str:
    return f"m{-c}" if c < 0 else str(c)


def round11_objects(run_object) -> List[object]:
    """The Round 11 carriers, built with the register's own ``_run_object``."""
    out: List[object] = []

    # -- track A: the seed's right edge ---------------------------------------------------
    out.append(run_object(
        "wheel_30_seed_right_edge_zero",
        ("r30_seed_right_edge_zero", "wheel_00011110_seed_right_edge_zero"),
        0, 0, "FORMAL",
        ("the seed's right-edge boundary: at time 0 every right diagonal is white except "
         "diagonal 0 (rdiag D 0 = [D = 0]); diagonals D < 0 are white at every time; and each "
         "diagonal is the running XOR of the two outside it: rdiag D (t+1) = rdiag D t + "
         "(rdiag (D-1) t OR rdiag (D-2) t) over GF(2).  Consequences: every diagonal is "
         "periodic with period 2^D, the least periods are unbounded, and each diagonal is either "
         "periodic or ANTI-periodic with the common period of the two outside it"),
        ("GLM.Rule30.rdiag_zero, rdiag_neg, rdiag_succ, rdiag_periodic, rdiag_period_unbounded, "
         "rdiag_periodic_or_antiPeriodic (RightDiagonalBalance.lean)"),
        extra={"kind_r11": "edge"}))
    for D in range(0, 40):
        rec = diagonal_record(D)
        P, k, anti = rec["period"], rec["ones"], rec["anti"]
        freq = rec["frequency"]
        if D == 5:
            ev = "FORMAL"
            lean = ("GLM.Rule30.wobble_rdiag_five_32 (12 black in 32), wobble_rdiag_five "
                    "(D(32k) = -8k), rdiag_five_not_half")
        elif D == 7:
            ev = "FORMAL"
            lean = ("GLM.Rule30.rdiag_seven_antiPeriodic (half-period 16), rdiag_seven_bounded "
                    "(|D(N)| <= 16 for every N, frequency 1/2)")
        else:
            ev = "EMP"
            lean = ("value computed here; the consequence of anti-periodicity is "
                    "GLM.Rule30.wobble_antiPeriodic_bound / antiPeriodic_hasFrequencyHalf")
        if anti:
            verdict = (f"ANTI-periodic with half-period {P // 2}: exactly balanced, frequency "
                       f"1/2, and |wobble(N)| <= {P // 2} for every N (bounded regime)")
        elif P == 1:
            verdict = "constant (the right edge itself is always black): frequency 1"
        else:
            verdict = (f"not anti-periodic: frequency {freq}"
                       + (" over each period; the wobble is periodic" if freq == Fraction(1, 2)
                          else f", so the wobble grows linearly: D(N)/N -> {2 * freq - 1}"))
        out.append(run_object(
            f"wheel_30_rdiag_{D}", (f"r30_rdiag_{D}", f"wheel_00011110_rdiag_{D}"),
            D, freq, ev,
            (f"right diagonal {D} of the seed pattern (cells a(t)(t - {D})): least period {P}, "
             f"{k} black cells per period; {verdict}  [{rec['source']}]"),
            lean, aux=[P, k, int(anti)],
            extra={"kind_r11": "rdiag", "period": P, "ones": k, "anti": anti}))
    out.append(run_object(
        "wheel_30_rdiag_balanced", ("r30_rdiag_balanced", "wheel_00011110_rdiag_balanced"),
        0, Fraction(1, 2), "FORMAL",
        ("infinitely many right diagonals of the seed pattern are exactly balanced: for every "
         "D0 there is a diagonal D >= D0 and m with |wobble(N)| <= 2^m for all N, exactly 2^m "
         "black cells in the first 2^(m+1), and frequency exactly 1/2.  Not all diagonals are "
         "(diagonal 5 has frequency 3/8).  The centre column a(t) = rdiag t t crosses every "
         "diagonal once, so this does not decide question 2"),
        ("GLM.Rule30.infinitely_many_balanced_rdiag, exists_antiPeriodic_rdiag, "
         "rdiag_five_not_half"), extra={"kind_r11": "edge"}))

    # -- track B: the off-centre observer -------------------------------------------------
    W = column_wobbles()
    for (c, N), v in sorted(W.items()):
        quoted = N in QUOTED_COLUMN_WOBBLE
        ev = "CERT" if (c == 0 and N == 1000000) else "EMP"
        lean = ("GLM.Rule30.wobble_1e6" if ev == "CERT" else
                ("value quoted from rule30_round11/r11_offcentre_wobble.c" if quoted else
                 "value computed here (wobble = 2 * ones - N, Lean definition GLM.Rule30.wobble)"))
        out.append(run_object(
            f"wheel_30_wobble_D_{N}_column_{_tok(c)}",
            (f"r30_wobble_D_{N}_column_{_tok(c)}",
             f"wheel_00011110_wobble_D_{N}_column_{_tok(c)}"),
            N, v, ev,
            f"the wobble of column {c} of the impulse run: D_{c}({N}) = 2 * #black - {N} = {v}",
            lean, extra={"kind_r11": "column_wobble", "observer_column": c}))
    for c in range(1, 6):
        for N in (100, 1000, 10000, 100000, 1000000):
            g = W[(c, N)] - W[(-c, N)]
            out.append(run_object(
                f"wheel_30_chiral_gap_{c}_{N}",
                (f"r30_chiral_gap_{c}_{N}", f"wheel_00011110_chiral_gap_{c}_{N}"),
                N, g, "EMP",
                (f"the chirality signal in the wobble at column {c}: D_{c}({N}) - D_-{c}({N}) = "
                 f"{g}; by the mirror symmetry this is also wheel 30 minus wheel 86, both read at "
                 f"column {c}.  At the centre it is 0 for every N"),
                ("GLM.Rule30.chiralGap_eq_thirty_sub_eightySix, chiralGap_centre, "
                 "chiralGap_neg (the identities, every N); the value is computed/quoted"),
                extra={"kind_r11": "chiral"}))
        out.append(run_object(
            f"wheel_30_chiral_gap_first_{c}",
            (f"r30_chiral_gap_first_{c}", f"wheel_00011110_chiral_gap_first_{c}"),
            c, CHIRAL_FIRST[c], "FORMAL",
            (f"chirality enters the wobble at column {c} at N = {CHIRAL_FIRST[c]}: D_{c}(N) = "
             f"D_-{c}(N) for N < {CHIRAL_FIRST[c]} and not at N = {CHIRAL_FIRST[c]}; to N = 10^6 "
             f"the gap stays within +-{CHIRAL_MAX_1E6[c]} (EMP), the size of a random walk, not "
             f"a drift"),
            "GLM.Rule30.chiralGap_first", extra={"kind_r11": "chiral"}))

    # -- track C: the parity count ---------------------------------------------------------
    out.append(run_object(
        "wheel_30_white_diagonal_parity",
        ("r30_white_diagonal_parity", "wheel_00011110_white_diagonal_parity"),
        2, 1, "FORMAL",
        ("whiteDiagonalCount n is odd for EVERY n >= 2 (so the top ANF monomial is unique and the "
         "ANF degree of a(n)(c) is exactly 2n - 1 for every cell c).  The GF(2) recurrence that "
         "generates the parity is the triangle parity law triQ_succ; the parity sequence is the "
         "constant 1"),
        ("GLM.Rule30.whiteDiagonalCount_odd, topMonomialConjecture_holds, center_anfDegree_eq, "
         "anfDegree_eq_at, triQ_succ (TopMonomial.lean, Round 8)"),
        extra={"kind_r11": "parity"}))
    return out
