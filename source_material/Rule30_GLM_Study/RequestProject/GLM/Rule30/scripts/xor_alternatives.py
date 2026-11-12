#!/usr/bin/env python3
"""Round 24 (EMP): centre columns of the 32 one-gate variants of Rule 30.

Outer family: g(L, C or R) for the 16 gates g.  Inner family: L xor h(C, R) for the 16 gates h.
For each variant, simulate N steps from a single black cell (uniform background tracked
separately) and report the smallest (transient, period) that fits the computed centre column,
or "none" if no period <= 100 with transient <= N/2 fits.

The Lean package proves the periodic cases (`outer_alternative_periodic`,
`inner_alternative_periodic`) and certifies `no eventual period p <= 500 from time <= 500` for the
four OR-type wheels 30, 45, 75, 135 (`orType_no_small_period`).  This script is only a guide.

Usage: python3 xor_alternatives.py [N]
"""
import sys


def centre_column(f, n_steps):
    row = {0: 1}
    bg = 0
    col = [1]
    for n in range(n_steps):
        new = {c: f(row.get(c - 1, bg), row.get(c, bg), row.get(c + 1, bg))
               for c in range(-n - 1, n + 2)}
        bg = f(bg, bg, bg)
        row = new
        col.append(row[0])
    return col


def eventual_period(col, max_p=100):
    n = len(col)
    for p in range(1, max_p + 1):
        for t in range(n // 2):
            if all(col[i] == col[i + p] for i in range(t, n - p)):
                return t, p
    return None


def gate(i):
    return lambda a, b: (i >> (2 * a + b)) & 1


def wheel(f):
    return sum(f((k >> 2) & 1, (k >> 1) & 1, k & 1) << k for k in range(8))


def gate_name(i):
    names = {0: "0", 1: "nor", 2: "!a&b", 3: "!a", 4: "a&!b", 5: "!b", 6: "xor", 7: "nand",
             8: "and", 9: "xnor", 10: "b", 11: "!a|b", 12: "a", 13: "a|!b", 14: "or", 15: "1"}
    return names[i]


def main():
    n_steps = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    print(f"N = {n_steps}")
    print("outer family g(L, C or R):  gate  wheel  (transient, period)")
    for i in range(16):
        g = gate(i)
        f = lambda L, C, R, g=g: g(L, C | R)
        print(f"  {gate_name(i):>5}  {wheel(f):>3}  {eventual_period(centre_column(f, n_steps))}")
    print("inner family L xor h(C, R):  gate  wheel  (transient, period)")
    for i in range(16):
        h = gate(i)
        f = lambda L, C, R, h=h: L ^ h(C, R)
        print(f"  {gate_name(i):>5}  {wheel(f):>3}  {eventual_period(centre_column(f, n_steps))}")


if __name__ == "__main__":
    main()
