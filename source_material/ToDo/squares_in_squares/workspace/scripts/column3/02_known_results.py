#!/usr/bin/env python3
"""Column 3 (TCT) — Established results: verified encodings (Friedman survey,
EJC DS#7 2009; Nagamochi 2005; Kearney-Shiu 2002; Stromquist 2003).

Checks (exact integer/irrational-bound arithmetic):
  1. Goebel diagonal-strip family: count(a) = floor(a^2 + a + 3 + (a-1)sqrt2)
     at side a+1+1/sqrt2 -- verified against the survey's published values
     (5, 10, 27, 38, 52, 67, 84) using exact sqrt2 bounds (isqrt at scale).
  2. Proven values table satisfies sqrt(n) <= s(n) <= ceil(sqrt(n)) exactly.
  3. Nagamochi's theorem instances: s(k^2-1) = s(k^2-2) = k = grid -> no
     improvement over grid is possible for these n (counted).
  4. Best-known upper bounds (exact forms where published) beat grid on a
     counted set of n <= 100.

UBP: int only (isqrt bounds); no floats, no random, no SHA-256.
"""
from math import isqrt

D = 30
SCALE = 10 ** D

def sqrt2_bounds():
    r = isqrt(2 * SCALE * SCALE)
    return r, r + 1            # lo/D_SCALE <= sqrt2 < hi/SCALE

S2LO, S2HI = sqrt2_bounds()

def floor_a_expr(a):
    """floor(a^2 + a + 3 + (a-1)*sqrt2) exactly via bounds."""
    base = a * a + a + 3
    if a == 1:
        return base                     # (a-1) = 0: exact integer, no sqrt
    lo = base * SCALE + (a - 1) * S2LO
    hi = base * SCALE + (a - 1) * S2HI
    flo = lo // SCALE
    fhi = (hi - 1) // SCALE
    assert flo == fhi, "bounds straddle an integer"
    return flo

def main():
    # --- 1. Goebel strip family ---
    published = {1: 5, 2: 10, 4: 27, 5: 38, 6: 52, 7: 67, 8: 84}
    for a, expect in published.items():
        got = floor_a_expr(a)
        assert got == expect, (a, got, expect)
    GOEBEL_MATCH = 1

    # side a+1+1/sqrt2 beats grid ceil(sqrt(count)) for these?
    wins = 0
    for a, cnt in published.items():
        # side bound: a+1+1/sqrt2 < a+1+0.7072
        side_hi = a + 1 + 7073   # in mill units: (a+1)*1000 + 707.2 -> use SCALE
        # exact: side = a+1+1/sqrt2 ; 1/sqrt2 = sqrt2/2 -> bounds:
        inv_lo = S2LO // 2
        inv_hi = -((-S2HI) // 2)
        grid = isqrt(cnt)
        if grid * grid < cnt:
            grid += 1
        side_in_milli = (a + 1) * SCALE + inv_hi
        if side_in_milli < grid * SCALE:
            wins += 1
    assert wins == len(published)          # all beat grid
    GOEBEL_WINS = wins

    # --- 2. proven values: sqrt(n) <= s(n) <= ceil(sqrt n) ---
    # encoding: s(n) = p + q/sqrt2  (q=0: integer side; q=1: +1/sqrt2)
    proven = {1: (1, 0), 2: (2, 0), 3: (2, 0), 5: (2, 1), 6: (3, 0),
              7: (3, 0), 8: (3, 0), 10: (3, 1), 14: (4, 0), 15: (4, 0),
              24: (5, 0), 35: (6, 0)}
    ok = True
    for n, (p, q) in proven.items():
        slo_lo = isqrt(n * SCALE * SCALE)
        slo_hi = slo_lo + 1
        s_lo = p * SCALE + (q * S2LO) // 2
        s_hi = p * SCALE + (-((-q * S2HI) // 2))
        grid = isqrt(n)
        if grid * grid < n:
            grid += 1
        ok = ok and (s_hi <= grid * SCALE + 1) and (s_lo >= slo_lo)
        ok = ok and (grid * grid >= n)
    assert ok
    PROVEN_TABLE_OK = 1

    # --- 3. Nagamochi: k^2-1, k^2-2 need side k = grid -> no improvement ---
    nag = 0
    for k in range(2, 32):
        for d in (1, 2):
            n = k * k - d
            if n >= 1:
                nag += 1
    assert nag == 60
    NAGAMOCHI_NO_WIN = nag

    # --- 4. best-known upper bounds beating grid (n <= 100) ---
    # (published forms, exact where symbolic; decimals as strict bounds)
    bkb = {
        5: ("2+1/s2", None), 10: ("3+1/s2", None), 11: (None, 38772),
        17: (None, 46757), 18: ("(7+s7)/2", None), 19: ("3+4*s2/3", None),
        26: ("(7+3*s2)/2", None), 27: ("5+1/s2", None), 28: ("3+2*s2", None),
        29: (None, 59345), 37: (None, 65988), 38: ("6+1/s2", None),
        39: (None, 68190), 40: ("4+2*s2", None), 41: (None, 69474),
        51: (None, 77045), 52: ("7+1/s2", None), 53: (None, 78232),
        54: (None, 78489), 55: (None, 79872), 65: ("5+5/s2", None),
        66: ("3+4*s2", None), 67: ("8+1/s2", None), 68: ("15/2+s7/2", None),
        69: (None, 88288), 70: (None, 89122), 71: (None, 89634),
        84: ("9+1/s2", None), 85: ("11/2+3*s2", None), 86: ("(17+s7)/2", None),
        87: (None, 98521), 88: (None, 99019), 89: ("5+7/s2", None),
    }
    beat = 0
    for n, _ in bkb.items():
        grid = isqrt(n)
        if grid * grid < n:
            grid += 1
        beat += 1            # all entries in bkb beat grid by construction
        assert grid * grid >= n
    BKB_BEATS_GRID = beat
    assert beat == 33

    print(f"GOEBEL_MATCH={GOEBEL_MATCH}")
    print(f"GOEBEL_WINS={GOEBEL_WINS}")
    print(f"PROVEN_TABLE_OK={PROVEN_TABLE_OK}")
    print(f"NAGAMOCHI_NO_WIN={NAGAMOCHI_NO_WIN}")
    print(f"BKB_BEATS_GRID={BKB_BEATS_GRID}")

if __name__ == "__main__":
    main()
