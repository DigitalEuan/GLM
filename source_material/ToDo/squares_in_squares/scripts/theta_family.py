#!/usr/bin/env python3
r"""theta_family.py — level-escalation test: the rotated-block + corner-
staircase family at ARBITRARY block angle θ (generalized Göbel).

Exact derivation (this file implements and verifies it):
  state: p×p block of unit squares rotated by θ ∈ (0°,45°], centered at
  (s/2, s/2); four corner staircases, depth a (squares at (i+0.5, j+0.5)
  etc., i+j ≤ a−1); tightness (deepest staircase corner touches the
  binding block face at the face center) gives EXACTLY
      s(θ) = (2a·M + 2·m + p) / (cosθ + sinθ),
      M = max(cosθ, sinθ), m = min(cosθ, sinθ),
  feasibility:
      p·sinθ > a−1            (block corner clears the side staircases;
                               at 45° this is Göbel's a−1 < b√2/2)
      p·sin(2θ) ≤ 2(aM + m)   (block bbox fits the container; at 45°:
                               Göbel's b√2/2 < a+1)
  n = p² + 2a(a+1) (independent of θ).
  At θ=45° this reproduces Göbel exactly: s = a+1+p/√2.
  s(θ) has a kink-minimum at 45° (M switches), so s(θ) ≥ s(45°) with
  equality only at 45° — to be confirmed by a fine sweep below.

Special angle levels tested exactly (sympy):
  45°  -> Q(√2)      (Göbel; control — must reproduce the known family)
  30°  -> Q(√3)      (the user's hypothesis)
  22.5°-> Q(√(2+√2)) (quartic — a genuinely "higher system")
  15°  -> Q(√2,√3)   (biquadratic)
  18.435°=atan(1/3), 26.565°=atan(1/2), 36.870°=atan(3/4) (rational slopes)
  40.18° (Trump's angle; numeric only)
Procedure per (a, p, θ):
  1. prefilter by the two feasibility inequalities + K-clearance
     (block corner outside the staircase region);
  2. build the exact state (sympy placement, then float);
  3. packlib.verify: worst_pen ≤ 0 required (touching allowed, overlap
     never); P.finalize for clearance.
Search targets:
  (i)  any (a,p,θ) with verified s < current table L  -> world record;
  (ii) members infeasible at 45° but feasible at θ≠45° (new n values) —
       reported with their s vs grid(n);
  (iii) the s(θ) fine sweep (0.25° steps) proving the 45° minimum.
"""
import json
import math
import os
import sys
from math import sqrt

import sympy as sp

HERE = "/home/z/my-project/scripts"
sys.path.insert(0, HERE)
import packlib as P

TAB = "/home/z/my-project/workspace/submission/table.json"
SQ2 = sqrt(2)


def special_angles():
    """θ -> (exact cos, sin as sympy expressions)."""
    out = {}
    out["45"] = (sp.sqrt(2) / 2, sp.sqrt(2) / 2)
    out["30"] = (sp.sqrt(3) / 2, sp.Rational(1, 2))
    out["22.5"] = (sp.sqrt(2 + sp.sqrt(2)) / 2, sp.sqrt(2 - sp.sqrt(2)) / 2)
    out["15"] = ((sp.sqrt(6) + sp.sqrt(2)) / 4, (sp.sqrt(6) - sp.sqrt(2)) / 4)
    for name, slope in (("18.435", sp.Rational(1, 3)), ("26.565", sp.Rational(1, 2)), ("36.870", sp.Rational(3, 4))):
        # θ = atan(slope): cos = 1/√(1+s²), sin = s/√(1+s²)
        d = sp.sqrt(1 + slope**2)
        out[name] = (1 / d, slope / d)
    return out


def s_formula(a, p, c, s_):
    M, m = sp.Max(c, s_), sp.Min(c, s_)
    # numeric compare to pick M/m (Max/Min of sympy exprs don't simplify)
    if float(c.evalf(30)) >= float(s_.evalf(30)):
        M, m = c, s_
    else:
        M, m = s_, c
    return (2 * a * M + 2 * m + p) / (c + s_), M, m


def feasible(a, p, c, s_, K):
    """Feasibility prefilter (exact algebra, 40-digit comparisons)."""
    sn = float(s_.evalf(40))
    cs = float(c.evalf(40))
    # lower: p sinθ > a−1  (block corner clears side staircases)
    if not (p * sn > a - 1):
        return False, "lower(p·sinθ≤a−1)"
    # upper: p sin2θ ≤ 2(aM+m)  (bbox in container)
    M = max(cs, sn)
    m = min(cs, sn)
    if not (p * 2 * cs * sn <= 2 * (a * M + m) + 1e-30):
        return False, "upper(bbox)"
    return True, ""


def k_clears(a, p, c, s_, s_val):
    """Block corner K outside the LL staircase region
    {x,y ≤ a, x+y ≤ a+1}: require NOT(K strictly inside)."""
    Kx = s_val / 2 - (p / 2) * c
    Ky = s_val / 2 - (p / 2) * s_
    S = Kx + Ky
    vals = [float(v.evalf(40)) for v in (Kx, Ky, S)]
    Kx, Ky, S = vals
    strict_inside = (Kx < a - 1e-30) and (Ky < a - 1e-30) and (S < a + 1 - 1e-30)
    return not strict_inside


def build_state(a, p, c, s_, s_val):
    """Exact state: rotated block + 4 staircases."""
    st = []
    # block: p×p in block frame, rotated θ, centered (s/2, s/2)
    off = (p - 1) / 2
    for i in range(p):
        for j in range(p):
            u = i - off
            v = j - off
            x = s_val / 2 + u * c - v * s_
            y = s_val / 2 + u * s_ + v * c
            st.append((x, y, sp.atan2(s_, c)))
    # staircases (axis-aligned), 4 corners
    for (ox, oy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        for i in range(a):
            for j in range(a - i):
                if ox == 0:
                    x = i + sp.Rational(1, 2)
                else:
                    x = s_val - (i + sp.Rational(1, 2))
                if oy == 0:
                    y = j + sp.Rational(1, 2)
                else:
                    y = s_val - (j + sp.Rational(1, 2))
                st.append((x, y, sp.Integer(0)))
    return st


def main():
    tab = json.load(open(TAB))
    angles = special_angles()
    results = {}
    wins = []
    new_members = []
    # (i) exact enumeration at special angles
    for name, (c, s_) in sorted(angles.items(), key=lambda kv: -float(kv[1][1].evalf(30))):
        rows = []
        for a in range(1, 23):
            for p in range(1, 51):
                n = p * p + 2 * a * (a + 1)
                if n > 1050:
                    continue
                s_val, M, m = s_formula(a, p, c, s_)
                ok, why = feasible(a, p, c, s_, s_val)
                if not ok:
                    continue
                if not k_clears(a, p, c, s_, s_val):
                    continue
                # exact state + packlib verify
                st = build_state(a, p, c, s_, s_val)
                stf = [(float(x.evalf(40)), float(y.evalf(40)), float(t.evalf(40)) % (sp.pi.evalf(40) / 2)) for (x, y, t) in st]
                assert len(stf) == n, (a, p, len(stf), n)
                r = P.verify(stf)
                if r["worst_pen"] > 1e-9:  # genuine overlap
                    rows.append((a, p, n, "OVERLAP", r["worst_pen"]))
                    continue
                stf2, r2 = P.finalize(stf, gap=2e-9)
                if not r2["ok"]:
                    continue
                Lv = float(r2["L"])
                cur = tab[str(n)]["L"] if str(n) in tab else None
                rec = {"a": a, "p": p, "n": n, "s": round(Lv, 9),
                       "cur": cur, "grid": None}
                import math
                rec["grid"] = math.ceil(math.sqrt(n))
                rows.append(rec)
                if cur is not None and Lv < cur - 1e-9:
                    wins.append((name, a, p, n, cur, Lv))
                # new member = infeasible at 45°? test later
        results[name] = rows
    # report
    for name, rows in sorted(results.items()):
        feas = [r for r in rows if isinstance(r, dict)]
        print(f"θ={name}°: feasible verified members: {len(feas)}")
        for r in feas[:6]:
            tag = " WIN!" if r["s"] < (r["cur"] or 1e18) - 1e-9 else ""
            better_grid = " < GRID" if r["s"] < r["grid"] - 1e-9 else ""
            print(f"   a={r['a']} p={r['p']} n={r['n']} s={r['s']:.6f} grid={r['grid']} cur={r['cur']}{better_grid}{tag}")
    # (ii) members at θ≠45° that are NOT Göbel members (infeasible at 45°)
    print("\n=== new members (infeasible at 45°, feasible at θ≠45°) ===")
    c45, s45 = angles["45"]
    for name, rows in results.items():
        if name == "45":
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            a, p, n = r["a"], r["p"], r["n"]
            ok45, _ = feasible(a, p, c45, s45, 0)
            ok45 = ok45 and k_clears(a, p, c45, s45, s_formula(a, p, c45, s45)[0])
            if not ok45:
                new_members.append((name, a, p, n, r["s"], r["grid"]))
    for nm in new_members[:20]:
        name, a, p, n, s, g = nm
        print(f"  θ={name}° a={a} p={p}: n={n} s={s:.4f} grid={g} {'USEFUL' if s < g else 'worse-than-grid'}")
    print(f"total new members: {len(new_members)}, useful: {sum(1 for nm in new_members if nm[4] < nm[5])}")
    # (iii) fine sweep: s(θ) ≥ s(45°)?
    print("\n=== fine sweep 0.25°..45° in 0.05° steps ===")
    for (a, p) in ((3, 5), (10, 14), (5, 7)):
        best = None
        for deg10 in range(25, 4501, 5):   # 0.25° .. 45.00°
            th = math.radians(deg10 / 100)
            c, s_ = math.cos(th), math.sin(th)
            M, m = max(c, s_), min(c, s_)
            sL = (2 * a * M + 2 * m + p) / (c + s_)
            if best is None or sL < best[0]:
                best = (sL, deg10 / 100)
        s45v = a + 1 + p / SQ2
        print(f"  a={a} p={p}: s(45°)={s45v:.6f}; sweep min={best[0]:.6f} at {best[1]}° (>= 45° value: {best[0] >= s45v - 1e-12})")
    print(f"\nWINS: {wins}")
    json.dump({"results": {k: [r if isinstance(r, dict) else list(r) for r in v] for k, v in results.items()},
               "new_members": [list(nm) for nm in new_members], "wins": [list(w) for w in wins]},
              open("/tmp/theta_family.json", "w"))


if __name__ == "__main__":
    main()
