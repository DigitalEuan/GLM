"""Round 11 self-test (plain asserts; pytest not needed).  Each check names the Lean theorem it
mirrors.  From a GLM checkout after the Round 11 setup:
    PYTHONPATH=. python3 rule30_round11/test_round11.py
"""
from fractions import Fraction

from glm_universal.data_objects import automata as ca
from glm_universal.data_objects import automata_round11 as r11
from glm_universal.reasoning import wheel_claims as wc
from glm_universal.reasoning import wheel_induction as wi
from glm_universal.runtime import toolbox as tb

# --- track A: the right diagonals ---------------------------------------------------------
T = 4096
d = r11.right_diagonals(12, T)
ref = ca.impulse_rows(30, 80)                       # independent evolution (window rows)
h = 81
for D in range(8):                                  # rdiag D t = a(t)(t - D)
    for t in range(80):
        assert d[D][t] == ref[t][h + t - D], (D, t)
assert all(d[D][0] == (1 if D == 0 else 0) for D in range(13))          # rdiag_zero
for D in range(2, 13):                                                   # rdiag_succ
    for t in range(T - 1):
        assert d[D][t + 1] == d[D][t] ^ (d[D - 1][t] | d[D - 2][t])
for D in range(13):                                                      # rdiag_periodic
    assert all(d[D][t] == d[D][t + 2 ** D] for t in range(T - 2 ** D))
rec5, rec7 = r11.diagonal_record(5), r11.diagonal_record(7)
assert sum(d[5][:32]) == 12 and rec5["frequency"] == Fraction(3, 8)       # wobble_rdiag_five_32
assert rec7["anti"] and rec7["period"] == 32                             # rdiag_seven_antiPeriodic
assert all(abs(2 * sum(d[7][:n]) - n) <= 16 for n in range(T))           # rdiag_seven_bounded
for D in range(1, 13):                                  # periodic or anti-periodic (dichotomy)
    Q = r11.least_period([d[D - 1][t] | (d[D - 2][t] if D >= 2 else 0) for t in range(T)],
                         2 ** max(D - 1, 0))
    per = all(d[D][t + Q] == d[D][t] for t in range(T - Q))
    anti = all(d[D][t + Q] != d[D][t] for t in range(T - Q))
    assert per or anti, D                             # rdiag_periodic_or_antiPeriodic
    assert anti == (r11.diagonal_record(D)["anti"] and r11.diagonal_record(D)["period"] == 2 * Q)

# --- track B: chirality in the wobble -----------------------------------------------------
for c in range(1, 6):                                  # chiralGap_first
    a = ca.evolve_impulse_column(30, 64, c)
    b = ca.evolve_impulse_column(30, 64, -c)
    first = next(n for n in range(65) if ca.wobble(a, n) != ca.wobble(b, n))
    assert first == r11.CHIRAL_FIRST[c]
    m86 = ca.evolve_impulse_column(86, 64, c)           # wobble_mirror_column
    assert all(ca.wobble(m86, n) == ca.wobble(b, n) for n in range(65))
a0 = ca.evolve_impulse_column(30, 2000, 0)
assert ca.wobble(a0, 1000) == r11.column_wobbles()[(0, 1000)]

# --- the moving frame: the right-edge observer sees wheel 86, velocity -1 ------------------
rows = [tuple(d[D][t] for D in range(12)) for t in range(12)]
pairs = list(zip(rows[3:7], rows[4:8]))
res = wi.induce_rows_moving(pairs, rows[7])
assert res["status"] == "answered" and res["answer"] == "".join(map(str, rows[8]))
assert res["fits"] == {-1: [86]}                       # rdiag_moving_frame
assert wi.induce_rows(pairs, rows[7])["status"] == "unsolved"

# --- track D: the claim checker -----------------------------------------------------------
assert wc.check_claim("The center column observer can distinguish wheel 30 from wheel 86.")[
    "verdict"] == "REJECT"                             # centre_column_class
assert wc.check_claim("column 1 distinguishes wheel 30 from wheel 86")["verdict"] == "ACCEPT"
assert wc.check_claim("right diagonal 5 is balanced")["verdict"] == "REJECT"
assert wc.check_claim("right diagonal 7 is balanced")["verdict"] == "ACCEPT"
assert wc.check_claim("rows 0..3 determine wheel 30")["verdict"] == "REJECT"
assert wc.check_claim("rows 0..4 determine wheel 30")["verdict"] == "ACCEPT"
assert wc.check_claim("rule 110 is Turing complete") is None
r = tb.run_tool("tool claim the wobble at column 3 equals the wobble at column -3")
assert r.ok and "REJECT" in r.text

# --- the register -------------------------------------------------------------------------
assert ca.value_of("r30_rdiag_5")[1] == Fraction(3, 8)
assert ca.value_of("r30_white_diagonal_parity")[0].attributes["evidence"] == "FORMAL"
print("round 11: all checks pass")
