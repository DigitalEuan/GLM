"""``glm_universal.data_objects.automata_round12`` -- Round 12 carriers of the automata register.

Round 12 of the Rule 30 study: reading the wobble through different lenses.  New carriers for
the wheel-30 impulse run, each with its exact value, evidence class and Lean theorem (Lean
package ``RequestProject/GLM/Rule30``, namespace ``GLM.Rule30``):

* **The strobe (clock) lens.**  ``r30_strobe_D_p_r``: the phase wobble
  ``D_{p,r}(M) = sum_{t < M} w(p t + r)`` of the centre column at ``M = 10^6 // p`` (CERT,
  ``strobe_wobble_table``), and at ``M = 10^7 // p`` for ``p = 3`` (EMP).
  ``r30_question_apbalanced``: the strobe target ``SeedAPBalanced`` (every arithmetic progression
  has frequency 1/2) -- OPEN; it implies questions 1 and 2 and is implied by ``SeedFSTypical``,
  and the converse implication fails for general sequences (FORMAL).
* **The arrow lens.**  ``r30_arrow_last_zero_1e6``: the wobble is 0 at N = 195112 and positive on
  (195112, 10^6] (CERT, ``arrow_last_flip_1e6``); ``r30_wobble_D_10000000`` = 4440 (EMP).
* **The read angle.**  ``r30_ldiag_D``: left diagonal ``ldiag D t = a(t)(D - t)``, computed here
  for ``D <= 63`` from the bit-parallel rows (``ldiag D t`` is bit ``D`` of row ``t``): its
  least eventual period and its preperiod.  Every left diagonal is eventually periodic with a
  power-of-two period (FORMAL, ``ldiag_eventually_periodic``); the values are EMP.

Exact integers only.
"""
from __future__ import annotations

from functools import lru_cache
from math import isqrt
from typing import Dict, List, Tuple

__all__ = ["left_diagonal_records", "round12_objects", "STROBE_TABLE_1E6", "STROBE_3_1E7",
           "ARROW_LAST_ZERO", "WOBBLE_1E7", "LDIAG_RANGE"]

#: ``(p, r) -> D_{p,r}(10^6 // p)`` (CERT: GLM.Rule30.strobe_wobble_table).
STROBE_TABLE_1E6: Dict[Tuple[int, int], int] = {
    (2, 0): 704, (2, 1): 832, (3, 0): 179, (3, 1): 1583, (3, 2): -227,
    (4, 0): 18, (4, 1): 388, (4, 2): 686, (4, 3): 444,
    (5, 0): 1044, (5, 1): -72, (5, 2): 1144, (5, 3): -376, (5, 4): -204,
    (6, 0): 298, (6, 1): 568, (6, 2): -610, (6, 3): -120, (6, 4): 1014, (6, 5): 382,
}

#: ``D_{3,r}(3333333)`` (EMP: rule30_round12/r12_centre_column.c, 10^7 bits).
STROBE_3_1E7: Dict[int, int] = {0: 37, 1: 3229, 2: 1175}

#: Last zero of the wobble in [1, 10^6] (CERT: GLM.Rule30.arrow_last_flip_1e6).
ARROW_LAST_ZERO = 195112

#: ``D(10^7)`` (EMP: r12_centre_column.c).
WOBBLE_1E7 = 4440

#: Left diagonals held as carriers.
LDIAG_RANGE = 63
_LDIAG_T = 1024


@lru_cache(maxsize=2)
def left_diagonal_records(Dmax: int = LDIAG_RANGE, T: int = _LDIAG_T) -> Tuple[Tuple[int, int],
                                                                               ...]:
    """``(least eventual period, preperiod)`` of ``ldiag D`` for ``D <= Dmax`` from ``T`` rows of
    the bit-parallel step ``r -> (r << 2) xor ((r << 1) or r)`` (Lean ``rowStep``)."""
    rows = []
    r = 1
    mask = (1 << (Dmax + 1)) - 1
    for _ in range(T):
        rows.append(r & mask)
        r = (r << 2) ^ ((r << 1) | r)
    out = []
    for D in range(Dmax + 1):
        s = [(row >> D) & 1 for row in rows]
        per = next(p for p in range(1, T // 4)
                   if all(s[i] == s[i + p] for i in range(T // 2, T - p)))
        pre = T // 2
        while pre > 0 and s[pre - 1] == s[pre - 1 + per]:
            pre -= 1
        out.append((per, pre))
    return tuple(out)


def round12_objects(run_object) -> List[object]:
    out: List[object] = []
    # -- the strobe lens ------------------------------------------------------------------
    for (p, r), v in sorted(STROBE_TABLE_1E6.items()):
        M = 1000000 // p
        out.append(run_object(
            f"wheel_30_strobe_D_{p}_{r}", (f"r30_strobe_D_{p}_{r}",
                                           f"wheel_00011110_strobe_D_{p}_{r}"),
            M, v, "CERT",
            (f"the strobe read of stride {p}, phase {r}: D_{{{p},{r}}}({M}) = sum over t < {M} of "
             f"w({p} t + {r}) = {v}; a fair coin gives about +-{isqrt(M)}"),
            "GLM.Rule30.strobe_wobble_table (WobbleLensesData.lean)", aux=[p, r],
            extra={"kind_r12": "strobe", "stride": p, "phase": r}))
    for r, v in sorted(STROBE_3_1E7.items()):
        out.append(run_object(
            f"wheel_30_strobe_D_3_{r}_1e7", (f"r30_strobe_D_3_{r}_1e7",
                                             f"wheel_00011110_strobe_D_3_{r}_1e7"),
            3333333, v, "EMP",
            (f"the stride-3 phase-{r} wobble at 10^7 bits: D_{{3,{r}}}(3333333) = {v} (the "
             f"largest phase at 10^6, D_{{3,1}} = 1583, has fallen back towards the fair-coin "
             f"scale +-1826)"),
            "value from rule30_round12/r12_centre_column.c (exact, not machine-checked)",
            aux=[3, r], extra={"kind_r12": "strobe"}))
    out.append(run_object(
        "wheel_30_question_apbalanced", ("r30_question_apbalanced", "wheel_00011110_qap"),
        0, None, "OPEN",
        ("SeedAPBalanced: every arithmetic progression a(p t + r) of the centre column has "
         "frequency 1/2.  PROVED: it implies questions 1 and 2; SeedFSTypical implies it; the "
         "converse fails for general sequences (a doubled typical sequence); question 1 is "
         "equivalent to: for every stride some phase keeps changing colour"),
        ("GLM.Rule30.problems_one_and_two_of_seed_apBalanced, apBalanced_of_fsTypical, "
         "exists_apBalanced_not_fsTypical, problem1_iff_strobes (WobbleLenses.lean)"),
        about="question", extra={"kind_r12": "target"}))
    # -- the arrow lens --------------------------------------------------------------------
    out.append(run_object(
        "wheel_30_arrow_last_zero_1e6", ("r30_arrow_last_zero_1e6",
                                         "wheel_00011110_arrow_last_zero_1e6"),
        1000000, ARROW_LAST_ZERO, "CERT",
        ("the observer's arrow -sign D(N) does not flip after N = 195112: D(195112) = 0 and "
         "D(N) > 0 for 195112 < N <= 10^6 (to 10^7: still no zero, EMP).  A fair coin does this "
         "with probability about 9% (arcsine law), and a balanced sequence can have an arrow "
         "that never flips (exists_balanced_persistent_arrow): persistence is not bias"),
        "GLM.Rule30.arrow_last_flip_1e6, exists_balanced_persistent_arrow",
        extra={"kind_r12": "arrow"}))
    out.append(run_object(
        "wheel_30_wobble_D_10000000", ("r30_wobble_D_10000000", "wheel_00011110_wobble_D_1e7"),
        10000000, WOBBLE_1E7, "EMP",
        "the wobble at 10^7: D(10^7) = 4440 (a fair coin: about +-3162)",
        "value from rule30_round12/r12_centre_column.c (exact, not machine-checked)",
        extra={"kind_r12": "arrow"}))
    # -- the read angle --------------------------------------------------------------------
    for D, (per, pre) in enumerate(left_diagonal_records()):
        inside = "inside" if pre > D else "after"
        out.append(run_object(
            f"wheel_30_ldiag_{D}", (f"r30_ldiag_{D}", f"wheel_00011110_ldiag_{D}"),
            D, per, "EMP",
            (f"left diagonal {D} (cells a(t)({D} - t)): least eventual period {per}, periodic "
             f"from t = {pre}; the centre column reads it at t = {D}, {inside} its transient.  "
             f"Every left diagonal is eventually periodic with a power-of-two period (FORMAL)"),
            "GLM.Rule30.ldiag_eventually_periodic (the values are computed here)",
            aux=[per, pre], extra={"kind_r12": "ldiag", "period": per, "preperiod": pre}))
    return out

