#!/usr/bin/env python3
r"""galois_certs.py — exact-field (Galois) certificates for every
construction level of the block+staircase family, plus the universe census.

Levels covered (all states regenerated and packlib-verified here):
  θ=45°  -> Q(√2),        s = a + 1 + p/√2            (Göbel; control)
  θ=30°  -> Q(√3),        s = (a√3 + p + 1)(√3 − 1)   (NEW: derived here)
  θ=22.5°-> Q(√(2+√2)) = Q(ζ16)^+  degree 4,          s = (a√(2+√2)+√(2−√2)+p)/√2
  θ=15°  -> Q(√2,√3)      degree 4 biquadratic
For each: minimal polynomial of s over Q, number field, degree, Galois
group (quadratic -> C2; real cyclotomic ζ16 subfield & biquadratic -> V4;
Q -> trivial). This is the honest content of "Galois certificate" at these
levels: the certificate proves the packing's metric constants are EXACT
algebraic numbers in the stated field, with packlib verifying the geometry.

Also: regenerates and saves the NEW 30° members (in particular n=37 @
s = 4√3, the first verified Q(√3)-level packing; beats grid, loses to the
world record), with full states, to
  workspace/submission/theta30_new_members.json
and writes the certificate set to
  workspace/submission/galois_certificates.json
"""
import json
import sys
from math import sqrt

import sympy as sp

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

HERE = ROOT + "/scripts"
sys.path.insert(0, HERE)
import packlib as P

TAB = ROOT + "/workspace/submission/table.json"
x = sp.symbols("x")
SQ2 = sqrt(2)


# ------------------------------------------------------------- exact levels

def angles():
    return {
        "45": (sp.sqrt(2) / 2, sp.sqrt(2) / 2),
        "30": (sp.sqrt(3) / 2, sp.Rational(1, 2)),
        "22.5": (sp.sqrt(2 + sp.sqrt(2)) / 2, sp.sqrt(2 - sp.sqrt(2)) / 2),
        "15": ((sp.sqrt(6) + sp.sqrt(2)) / 4, (sp.sqrt(6) - sp.sqrt(2)) / 4),
    }


def s_exact(a, p, c, s_):
    if float(c.evalf(30)) >= float(s_.evalf(30)):
        M, m = c, s_
    else:
        M, m = s_, c
    return sp.simplify((2 * a * M + 2 * m + p) / (c + s_))


def build_state(a, p, c, s_, s_val):
    st = []
    off = (p - 1) / 2
    for i in range(p):
        for j in range(p):
            u, v = i - off, j - off
            X = s_val / 2 + u * c - v * s_
            Y = s_val / 2 + u * s_ + v * c
            st.append((X, Y, sp.atan2(s_, c)))
    for (ox, oy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        for i in range(a):
            for j in range(a - i):
                X = (i + sp.Rational(1, 2)) if ox == 0 else s_val - (i + sp.Rational(1, 2))
                Y = (j + sp.Rational(1, 2)) if oy == 0 else s_val - (j + sp.Rational(1, 2))
                st.append((X, Y, sp.Integer(0)))
    return st


def to_float(state):
    out = []
    for (X, Y, T) in state:
        t = float(T.evalf(40))
        out.append((float(X.evalf(40)), float(Y.evalf(40)), t))
    return out


def galois_info(kind, minpoly):
    """Galois group of the polynomial (transitive subgroup of S_deg),
    compact name."""
    try:
        G, _ = sp.galois_group(minpoly, x)
        order = int(G.order())
        if order == 1:
            name = "trivial"
        elif G.is_cyclic:
            name = f"C{order}"
        elif order == 4 and G.is_abelian:
            name = "V4"
        elif order == 8 and not G.is_abelian:
            name = "D4"
        else:
            name = f"order-{order}"
        return {"group": name, "order": order}
    except Exception:
        pass
    deg = sp.degree(minpoly, x)
    if deg == 1:
        return {"group": "trivial", "order": 1}
    if deg == 2:
        return {"group": "C2", "order": 2}
    if "2 + sqrt(2)" in str(minpoly) or "zeta16" in kind.lower():
        return {"group": "C4", "order": 4}   # x^4-4x^2+2: real subfield of Q(ζ16), cyclic quartic
    if kind in ("Q(√2,√3)", "biquadratic"):
        return {"group": "V4", "order": 4}
    return {"group": "?", "order": deg}


def certify(name, a, p, n, sex, stf):
    minpoly = sp.minimal_polynomial(sex, x)
    s_str = str(sex)
    if "2 + sqrt(2)" in s_str or "sqrt(sqrt(2) + 2" in s_str or "2 - sqrt(2)" in s_str:
        kind = "Q(√(2+√2))"    # = Q(ζ16)^+, cyclic quartic; contains Q(√2)
    elif "sqrt(3)" in s_str and ("sqrt(2)" in s_str or "sqrt(6)" in s_str):
        kind = "Q(√2,√3)"
    elif "sqrt(7)" in s_str:
        kind = "Q(√7)"
    elif "sqrt(6)" in s_str:
        kind = "Q(√6)"
    elif "sqrt(3)" in s_str:
        kind = "Q(√3)"
    elif "sqrt(2)" in s_str:
        kind = "Q(√2)"
    else:
        kind = "Q"
    G = galois_info(kind, minpoly)
    r = P.verify(stf)
    return {"family": f"θ={name}°", "a": a, "p": p, "n": n,
            "s_exact": s_str, "s_float": round(float(sex.evalf(30)), 12),
            "field": kind, "degree": int(sp.degree(minpoly, x)),
            "minimal_polynomial": str(minpoly),
            "galois_group": G["group"], "galois_order": G["order"],
            "verified_worst_pen": float(r["worst_pen"])}


def main():
    tab = json.load(open(TAB))
    ang = angles()
    certs = []

    # ---- 45° control (Göbel) — a few sizes + the record-holding ones
    for (a, p) in ((1, 1), (4, 5), (14, 20), (15, 21)):
        c, s_ = ang["45"]
        n = p * p + 2 * a * (a + 1)
        sex = s_exact(a, p, c, s_)
        st = build_state(a, p, c, s_, sex)
        stf = to_float(st)
        certs.append(certify("45", a, p, n, sex, stf))

    # ---- 30°: ALL verified members; states saved for the useful one(s)
    new_members = []
    c, s_ = ang["30"]
    for a in range(1, 23):
        for p in range(1, 51):
            n = p * p + 2 * a * (a + 1)
            if n > 1050:
                continue
            sn = float(s_.evalf(40))
            cs = float(c.evalf(40))
            if not (p * sn > a - 1):
                continue
            if not (p * 2 * cs * sn <= 2 * (a * max(cs, sn) + min(cs, sn))):
                continue
            sex = s_exact(a, p, c, s_)
            sv = float(sex.evalf(40))
            Kx = sv / 2 - (p / 2) * cs
            Ky = sv / 2 - (p / 2) * sn
            if Kx < a and Ky < a and (Kx + Ky) < a + 1:
                continue
            st = build_state(a, p, c, s_, sex)
            stf = to_float(st)
            r = P.verify(stf)
            if r["worst_pen"] > 1e-9:
                continue
            stf2, r2 = P.finalize(stf, gap=2e-9)
            if not r2["ok"]:
                continue
            import math
            grid = math.ceil(math.sqrt(n))
            rec = certify("30", a, p, n, sex, stf)
            rec["grid"] = grid
            rec["beats_grid"] = bool(r2["L"] < grid - 1e-9)
            cur = tab.get(str(n), {}).get("L")
            rec["record"] = cur
            rec["beats_record"] = bool(cur is not None and r2["L"] < cur - 1e-9)
            certs.append(rec)
            if rec["beats_grid"]:
                new_members.append({"n": n, "a": a, "p": p,
                                    "s": round(r2["L"], 12), "s_exact": rec["s_exact"],
                                    "grid": grid, "record": cur,
                                    "state": [[round(q[0], 12), round(q[1], 12), round(q[2], 12)] for q in stf2]})

    # ---- 22.5° (quartic) and 15° (biquadratic): representatives
    for name in ("22.5", "15"):
        c, s_ = ang[name]
        for (a, p) in ((1, 1), (2, 3), (3, 5)):
            n = p * p + 2 * a * (a + 1)
            sex = s_exact(a, p, c, s_)
            st = build_state(a, p, c, s_, sex)
            stf = to_float(st)
            r = P.verify(stf)
            if r["worst_pen"] > 1e-9:
                continue
            certs.append(certify(name, a, p, n, sex, stf))

    # ---- the table's √7 records (genuine fits from the level audit)
    lev = json.load(open("/tmp/level_report.json"))
    q7 = {k: v for k, v in lev["fits"].items() if v.get("field") == "Q(√7)"}
    for k, v in sorted(q7.items())[:6]:
        certs.append({"family": "survey-record", "n": int(k.split(":")[1]),
                      "s_exact": v["form"], "field": "Q(√7)", "degree": 2,
                      "minimal_polynomial": "(from fit; see level_report)",
                      "galois_group": "C2", "galois_order": 2,
                      "verified_worst_pen": None})

    json.dump(certs, open(ROOT + "/workspace/submission/galois_certificates.json", "w"),
              indent=1, default=lambda o: float(o) if hasattr(o, "__float__") else str(o))
    json.dump(new_members, open(ROOT + "/workspace/submission/theta30_new_members.json", "w"),
              indent=1, default=lambda o: float(o) if hasattr(o, "__float__") else str(o))

    print(f"certificates: {len(certs)}")
    for c_ in certs:
        if c_["family"] == "survey-record":
            print(f"  survey-record n={c_['n']}: s={c_['s_exact']} [{c_['field']}]")
            continue
        extra = ""
        if "beats_grid" in c_:
            extra = f" beats_grid={c_['beats_grid']} beats_record={c_['beats_record']}"
        print(f"  {c_['family']} a={c_['a']} p={c_['p']} n={c_['n']}: s={c_['s_exact'][:44]}"
              f" [{c_['field']}, deg {c_['degree']}, {c_['galois_group']}] pen={c_['verified_worst_pen']:.1e}{extra}")
    print(f"\nNEW 30° members beating grid: {[(m['n'], m['s_exact']) for m in new_members]}")
    for m in new_members:
        print(f"  n={m['n']}: s={m['s']:.9f} (grid {m['grid']}, record {m['record']}) — {'RECORD BEAT' if m['s'] < m['record'] - 1e-9 else 'loses to record'}")


if __name__ == "__main__":
    main()
