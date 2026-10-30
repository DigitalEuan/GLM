"""Round 10 self-test (plain asserts; no pytest needed).

Each check recomputes, independently of the register, a fact that a Lean theorem states, and
names that theorem.  Run from a GLM checkout with the Round 9 and Round 10 overlays copied in:

    PYTHONPATH=. python3 rule30_round10/test_round10.py
"""
import sys

sys.path.insert(0, ".")

from glm_universal.data_objects import automata as ca          # noqa: E402
from glm_universal.reasoning import wheel_induction as wi      # noqa: E402


def cell(r, x, t, c, bg=0):
    """Independent reference: the cell (t, c) of wheel r from a finitely supported row x
    (a dict of non-background cells), by direct recursion over the light cone."""
    memo = {}

    def go(t, c):
        if t == 0:
            return x.get(c, bg)
        key = (t, c)
        if key not in memo:
            memo[key] = ca.local_rule(r, go(t - 1, c - 1), go(t - 1, c), go(t - 1, c + 1))
        return memo[key]
    return go(t, c)


IMPULSE = {0: 1}

# -- WheelInduction.lean ----------------------------------------------------------------
# rows_agree_iff / next_row_determined_iff, on every prefix of the Rule 30 diagram and on
# random-free exhaustive small tasks: survivors = tables agreeing on the seen entries, and
# "all survivors agree" = "query needs nothing unseen" (asserted inside induce_rows).
for T in range(1, 8):
    pairs, q, true = wi.rule30_demonstrations(T)
    res = wi.induce_rows(pairs, q)
    if res["status"] == "answered":
        assert res["answer"] == "".join(map(str, true))
for r in range(0, 256, 2):          # every wheel keeping white white, three rows each
    rows = ca.impulse_rows(r, 3, 5)
    res = wi.induce_rows(list(zip(rows[:2], rows[1:3])), rows[2])
    assert r in res["survivors"]
    if res["status"] == "answered":
        assert res["answer"] == "".join(map(str, rows[3]))

# -- Observer.lean ------------------------------------------------------------------------
# rows_identify_thirty: rows 0..4 in the light cone determine 30 among all 256.
# (odd wheels flip the background, so the cone cells are read from the exact evolution)
def cone_exact(r, T):
    col = []
    for t in range(T + 1):
        col.append([ca.evolve_impulse_column(r, t + 1, c)[t] for c in range(-t, t + 1)])
    return col
c30 = cone_exact(30, 4)
assert [r for r in range(256) if cone_exact(r, 4) == c30] == [30]                # rows_identify_thirty
c30_3 = cone_exact(30, 3)
assert [r for r in range(256) if cone_exact(r, 3) == c30_3] == [30, 62]          # rows_three_do_not_identify
assert all(cell(62, IMPULSE, t, c) == cell(30, IMPULSE, t, c)
           for t in range(4) for c in range(-6, 7))                              # ... at every cell
assert any(cell(62, IMPULSE, 4, c) != cell(30, IMPULSE, 4, c) for c in range(-4, 5))  # row_four_not_determined

# centre_column_class / centre_prefix_class / centre_six_not_enough
centre = lambda r, K: ca.evolve_impulse_column(r, K, 0)
assert [r for r in range(256) if centre(r, 7) == centre(30, 7)] == [30, 86]
assert [r for r in range(256) if centre(r, 6) == centre(30, 6)] == [30, 86, 175, 245]
assert centre(86, 3000) == centre(30, 3000)                                       # ecaColumn_eightySix_centre
# column_one_identifies / column_one_seven_not_enough / offCentre_column_identifies
col = lambda r, K, c: ca.evolve_impulse_column(r, K, c)
assert [r for r in range(256) if col(r, 8, 1) == col(30, 8, 1)] == [30]
assert 17 in [r for r in range(256) if col(r, 7, 1) == col(30, 7, 1)]
for c in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5):
    assert [r for r in range(256) if col(r, 13, c) == col(30, 13, c)] == [30], c

# observerArrow_eightySix / observerArrow_oneThirtyFive (the wobble under the two frames)
a30 = ca.evolve_impulse_column(30, 2000)
a86 = ca.evolve_impulse_column(86, 2000)
assert all(ca.wobble(a86, n) == ca.wobble(a30, n) for n in range(2001))
# the complemented impulse: black everywhere except cell 0
a135 = [cell(135, {0: 0}, t, 0, bg=1) for t in range(60)]
assert all(ca.wobble(a135, n) == -ca.wobble(a30, n) for n in range(61))

# -- the register carriers agree with all of this ----------------------------------------
objs = {o.name: o for o in ca.automata_objects()}
assert objs["wheel_30_induction_rows_3"].attributes["survivors"] == [30, 62]
assert objs["wheel_30_induction_rows_4"].attributes["value"] == 1
assert objs["wheel_30_observer_column_0"].attributes["survivors"] == [30, 86]
assert objs["wheel_30_observer_column_0"].attributes["value"] == 7
assert objs["wheel_30_observer_column_1"].attributes["value"] == 8
assert all(objs[f"wheel_30_observer_column_{ca.column_token(c)}"].attributes["value"] <= 13
           for c in ca.OBSERVER_COLUMNS)
bits = ca.evolve_impulse_column(30, 65)
for t in range(ca.STEP_COUNT):
    o = objs[f"wheel_30_step_{t}"]
    assert o.attributes["value"] == bits[t + 1] == cell(30, IMPULSE, t + 1, 0)
assert objs["wheel_30_arrow_mirror"].attributes["value"] == 1
assert objs["wheel_30_arrow_colour"].attributes["value"] == -1

print("round 10: all checks pass")
