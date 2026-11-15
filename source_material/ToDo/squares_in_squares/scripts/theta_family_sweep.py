#!/usr/bin/env python3
r"""theta_family_sweep.py — run 6, piece (b)+(c): the exact theta-family.

Exact generalized-Göbel family (derived; at 45 deg reproduces the catalog
formula s = a+1+b*sqrt(2)/2 EXACTLY, checked vs n=5 (2.7071) and n=40
(6.8284)):
  count n = b^2 + 2a(a+1)   (b^2 squares at tilt theta + 4 staircases)
  L(theta,a,b) = max( L_A if a>=1, b(C+S) if b>=1, 2a if a>=1 )
  L_A = [2(C*a + S) + b] / (C+S)   (staircase-block separating plane)
Sweep: open n, integer (a,b) with n=b^2+2a(a+1), theta over the algebraic
set (degree-2 exact; 15/22.5/75 degree-4 float). Hits (L < grid) are
constructed and packlib-verified. Also the theta-uniqueness curve.
"""
import json
from fractions import Fraction as Fr
from math import atan, sqrt, cos, sin, ceil, radians

import packlib as P

TAB = "/home/z/my-project/workspace/submission/table.json"

# name -> ((C_p, C_q, d), (S_p, S_q, d)) with C = C_p + C_q*sqrt(d)
FIELDS = {
    "45":        ((Fr(0), Fr(1, 2), 2), (Fr(0), Fr(1, 2), 2)),
    "30":        ((Fr(0), Fr(1, 2), 3), (Fr(1, 2), Fr(0), 3)),
    "60":        ((Fr(1, 2), Fr(0), 3), (Fr(0), Fr(1, 2), 3)),
    "arctan(1/2)": ((Fr(0), Fr(2, 5), 5), (Fr(0), Fr(1, 5), 5)),
    "arctan(2)":   ((Fr(0), Fr(1, 5), 5), (Fr(0), Fr(2, 5), 5)),
    "arctan(1/3)": ((Fr(0), Fr(3, 10), 10), (Fr(0), Fr(1, 10), 10)),
    "arctan(3)":   ((Fr(0), Fr(1, 10), 10), (Fr(0), Fr(3, 10), 10)),
    "arctan(1/4)": ((Fr(0), Fr(4, 17), 17), (Fr(0), Fr(1, 17), 17)),
    "arctan(4)":   ((Fr(0), Fr(1, 17), 17), (Fr(0), Fr(4, 17), 17)),
    "arctan(3/4)": ((Fr(4, 5), Fr(0), 1), (Fr(3, 5), Fr(0), 1)),
    "arctan(4/3)": ((Fr(3, 5), Fr(0), 1), (Fr(4, 5), Fr(0), 1)),
    "0":           ((Fr(1), Fr(0), 1), (Fr(0), Fr(0), 1)),
}
DEG4 = ("15", "22.5", "75")


def get_CS(name):
    """Return (C, S, d, exact?) — d is the field discriminant (1=rational).
    degree-4 angles return floats with d=None."""
    if name in DEG4:
        th = radians(float(name))
        return cos(th), sin(th), None, False
    (cp, cq, cd), (sp, sq, sd) = FIELDS[name]
    return (cp, cq, cd), (sp, sq, sd), cd, True


def val(t):
    p, q, d = t
    return float(p) + float(q) * sqrt(d)


def L_A_exact(name, a, b):
    """L_A as (p, q, d) exact if degree-2; float otherwise.
    Binding staircase far-corner: (a,1) [value Ca+S] for theta<=45 (C>=S,
    wall-low square binds); (1,a) [value C+Sa] for theta>=45 (wall-high).
    At 45 both coincide -> the catalog formula."""
    C, S, d, exact = get_CS(name)
    if not exact:
        Cv, Sv = C, S
        binding = Cv * a + Sv if Cv >= Sv else Cv + Sv * a
        return (2 * binding + b) / (Cv + Sv)
    cp, cq, cd = C
    sp, sq, sd = S
    # branch on VALUES (C>=S <=> theta<=45), not rational parts
    if val(C) >= val(S):
        b_p = cp * a + sp
        b_q = cq * a + sq
    else:
        b_p = cp + sp * a
        b_q = cq + sq * a
    num_p = 2 * b_p + b
    num_q = 2 * b_q
    den_p = cp + sp
    den_q = cq + sq
    den_norm = float(den_p) ** 2 - d * float(den_q) ** 2
    Lp = (float(num_p) * float(den_p) - d * float(num_q) * float(den_q)) / den_norm
    Lq = (float(num_q) * float(den_p) - float(num_p) * float(den_q)) / den_norm
    return (Fr(Lp).limit_denominator(10**6), Fr(Lq).limit_denominator(10**6), d)


def L_family(name, a, b):
    """(L_total, L_A_value, b*(C+S)) with degeneracy guards."""
    la_t = L_A_exact(name, a, b)
    la_v = val(la_t) if isinstance(la_t, tuple) else la_t
    C, S, d, exact = get_CS(name)
    cs_v = val((C[0] + S[0], C[1] + S[1], d)) if exact else C + S
    parts = []
    if a >= 1:
        parts.append(la_v)
    if b >= 1:
        parts.append(b * cs_v)
    if a >= 1:
        parts.append(2 * a)
    return (max(parts) if parts else 0.0), la_v, b * cs_v


def construct(name, a, b, L):
    from math import atan
    C, S, d, exact = get_CS(name)
    Cv = val(C) if exact else C
    Sv = val(S) if exact else S
    th = atan(Sv / Cv) if Cv > 1e-12 else atan(1e18)
    st = []
    off = (b - 1) / 2.0
    for i in range(b):
        for j in range(b):
            u, v = i - off, j - off
            st.append((L / 2 + u * Cv - v * Sv, L / 2 + u * Sv + v * Cv, th))
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (L, 0, -1, 1),
                             (0, L, 1, -1), (L, L, -1, -1)):
        for i in range(a):
            for j in range(a - i):
                st.append((cx + sx * (i + 0.5), cy + sy * (j + 0.5), 0.0))
    return st


def main():
    tab = json.load(open(TAB))
    open_n = [n for n in range(1, 1001) if tab[str(n)]["src"].startswith("grid")]
    names = ["45", "30", "60", "arctan(1/2)", "arctan(2)", "arctan(1/3)",
             "arctan(3)", "arctan(1/4)", "arctan(4)", "arctan(3/4)",
             "arctan(4/3)", "15", "22.5", "75"]

    sols = {}
    for n in open_n:
        for b in range(0, 40):
            rem = n - b * b
            if rem < 0:
                break
            if rem % 2:
                continue
            half = rem // 2
            a = int(round((sqrt(4 * half + 1) - 1) / 2))
            if a < 0 or a * (a + 1) != half:
                continue
            sols.setdefault(n, []).append((a, b))
    n_with = [n for n in open_n if n in sols and any(a >= 1 and b >= 1 for a, b in sols[n])]
    print(f"open n with integer (a,b), both>=1: {len(n_with)}/{len(open_n)}")

    print("\n=== theta-uniqueness: L_A(theta) at (a,b)=(3,4),(10,10),(8,28) ===")
    for (a, b) in ((3, 4), (10, 10), (8, 28)):
        row = []
        for nm in names:
            L, la, _ = L_family(nm, a, b)
            row.append((nm, round(L, 4)))
        m = min(x[1] for x in row)
        at = [nm for nm, v in row if v == m]
        print(f"  (a={a},b={b}): " + "  ".join(f"{nm}={v}" for nm, v in row))
        print(f"    -> family-value min at {at} (value {m}); "
              f"45-deg value {[v for nm,v in row if nm=='45'][0]}")

    print("\n=== sweep: any open n with family L < grid? ===")
    hits = []
    best_per_n = {}
    for n in n_with:
        g = ceil(sqrt(n))
        best = None
        for (a, b) in sols[n]:
            if a < 1 or b < 1:
                continue
            for nm in names:
                L, la, bcs = L_family(nm, a, b)
                if best is None or L < best[0]:
                    best = (L, nm, a, b)
                if L < g - 1e-9:
                    st = construct(nm, a, b, L)
                    if len(st) != n:
                        continue
                    r = P.verify(st, tol=1e-9)
                    hits.append((n, g, nm, a, b, round(L, 6),
                                 "VERIFIED" if r["ok"] else f"REJECT {r}"))
        if best:
            best_per_n[n] = best
    print(f"hits below grid: {len(hits)}")
    for h in hits[:20]:
        print("   ", h)
    print("\n=== best family L per open n (top-12 roomiest) ===")
    roomy = sorted(n_with, key=lambda n: -(ceil(sqrt(n)) - sqrt(n)))[:12]
    for n in roomy:
        g = ceil(sqrt(n))
        L, nm, a, b = best_per_n[n]
        tag = "BEATS GRID" if L < g - 1e-9 else "no"
        print(f"  n={n}: grid={g} best={L:.4f} ({nm},a={a},b={b}) {tag}")
    json.dump({"hits": hits, "best_per_n": {str(k): v for k, v in best_per_n.items()}},
              open("/home/z/my-project/workspace/push/theta_sweep.json", "w"), indent=1)


if __name__ == "__main__":
    main()
