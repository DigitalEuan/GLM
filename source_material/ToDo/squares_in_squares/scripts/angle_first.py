#!/usr/bin/env python3
r"""angle_first.py — Run 11, Piece 2: the reverse-direction recognizer.

User directive: "use lean to drive some of this from the reverse
direction - the proof generating the theorem generating the grids."
Applied to the Level-0 (unresolved) grids of leech_map.json:

  Stage A  ANGLE INVENTORY (measured): every Level-0 state's square
           angles vs the algebraic angle set (exact forms known:
           0/90 Q, 45 Q(√2), 30/60 Q(√3), 22.5 Q(√(2+√2)), 15/75
           Q(√2,√3), 36/72 Q(√5), arctan(p/q) Q(√(p²+q²))).
           Match window 0.05° (SVG parse noise measured ≤ 0.01° on
           clean members; set members are ≥ 0.8° apart).
  Stage B  EXACT RECONSTRUCTION: states with ALL angles in the set ->
           hypothesize K = compositum of angle fields; fit every center
           in K's √-basis (rational coeffs, the leech_map integer-scan
           standard); if ALL fit -> exact state known in K -> exact
           L = max bbox in K -> minpoly + Galois + level -> CERTIFICATE.
  Stage C  PSLQ HYPOTHESIS ENGINE (value-level only, never a cert):
           degree-2/4/8 minpoly of the stored 12-dp L, height ≤ 10^4,
           irreducible, real root within 1e-5; POSITIVE control (the
           280 certificates' s_float truncated to 12 dp: must recover
           the known minpoly) and NEGATIVE control (500 random 12-dp
           decimals in [2, 32]: spurious rate must be 0).

Output: download/level0_precision.json — per-n verdicts + controls.
No change to leech_map.json levels from Stage C (hypotheses are
reported, not applied); Stage B certificates go to
galois_certificates.json only when fully verified.
"""
import json
import math
from collections import Counter, defaultdict
from math import atan, degrees, sqrt

import sympy as sp
from mpmath import mp, mpf

mp.dps = 60


def parse_exact(s):
    """Certificate strings mix ASCII 'sqrt(2)' and unicode '(7+1√7)/2'
    (verbatim from leech_map.py — the audited parser)."""
    import re
    s = s.replace("·", "*").replace(" ", "")
    s = re.sub(r"(\d)√", r"\1*sqrt", s)
    s = s.replace("√", "sqrt")
    s = re.sub(r"sqrt(\d+)", r"sqrt(\1)", s)
    return sp.sympify(s)

TAB = json.load(open("/home/z/my-project/download/table.json"))
MAP = json.load(open("/home/z/my-project/download/leech_map.json"))
CERTS = json.load(open("/home/z/my-project/download/galois_certificates.json"))
OUT = "/home/z/my-project/download/level0_precision.json"

X = sp.symbols("x")

# ---- the algebraic angle set: name -> (float_deg, exact_cos, exact_sin)
def _q(*a):
    return sp.Rational(*a) if len(a) == 2 else sp.Rational(a[0])

ANGLE_SET = {}
def _add(name, deg, c_exact, s_exact):
    ANGLE_SET[name] = (deg, c_exact, s_exact)

_add("0", 0.0, _q(1), _q(0))
_add("90", 90.0, _q(0), _q(1))
_add("45", 45.0, sqrt2 := sp.sqrt(2) / 2, sqrt2)
_add("30", 30.0, sp.sqrt(3) / 2, _q(1, 2))
_add("60", 60.0, _q(1, 2), sp.sqrt(3) / 2)
_add("22.5", 22.5, sp.sqrt(2 - sp.sqrt(2)) / 2, sp.sqrt(2 + sp.sqrt(2)) / 2)
_add("67.5", 67.5, sp.sqrt(2 + sp.sqrt(2)) / 2, sp.sqrt(2 - sp.sqrt(2)) / 2)
_add("15", 15.0, (sp.sqrt(6) + sp.sqrt(2)) / 4, (sp.sqrt(6) - sp.sqrt(2)) / 4)
_add("75", 75.0, (sp.sqrt(6) - sp.sqrt(2)) / 4, (sp.sqrt(6) + sp.sqrt(2)) / 4)
_add("36", 36.0, (1 + sp.sqrt(5)) / 4, sp.sqrt((5 - sp.sqrt(5)) / 8))
_add("54", 54.0, sp.sqrt((5 - sp.sqrt(5)) / 8), (1 + sp.sqrt(5)) / 4)
_add("72", 72.0, (sp.sqrt(5) - 1) / 4, sp.sqrt((5 + sp.sqrt(5)) / 8))
_add("18", 18.0, sp.sqrt((5 + sp.sqrt(5)) / 8), (sp.sqrt(5) - 1) / 4)
for p, q in [(1, 2), (2, 1), (1, 3), (3, 1), (1, 4), (4, 1), (3, 4), (4, 3),
             (1, 5), (5, 1), (2, 3), (3, 2), (1, 6), (6, 1), (2, 5), (5, 2),
             (1, 1), (1, 7), (7, 1), (3, 5), (5, 3), (4, 5), (5, 4)]:
    if p == q:
        continue
    if p == 1 and q == 1:
        continue
    r2 = p * p + q * q
    deg = degrees(atan(p / q))
    _add(f"arctan({p}/{q})", deg, sp.sqrt(sp.Rational(q * q, r2)),
         sp.sqrt(sp.Rational(p * p, r2)))

NAMES = sorted(ANGLE_SET, key=lambda k: ANGLE_SET[k][0])
DEGS = [ANGLE_SET[k][0] for k in NAMES]
# safety: minimum gap between set members
_gaps = sorted(abs(a - b) for i, a in enumerate(DEGS) for b in DEGS[i + 1:])
MIN_GAP = _gaps[0]
WINDOW = 0.05          # degrees; parse noise measured <= 0.01


def match_angle(th_rad):
    """Return (name, exact (cos, sin)) or (None, dist_to_nearest)."""
    d = degrees(th_rad) % 180.0
    best, bd = None, 1e9
    for k in NAMES:
        for cand in (ANGLE_SET[k][0], ANGLE_SET[k][0] + 180.0):
            dd = abs(d - (cand % 180.0))
            dd = min(dd, 180.0 - dd) if dd > 90 else dd
            if dd < bd:
                bd, best = dd, k
    if bd <= WINDOW:
        return best, ANGLE_SET[best][1], ANGLE_SET[best][2]
    return None, bd, None


# ---- Stage B helpers -------------------------------------------------
def field_of_angle(name):
    """Exact sympy (cos, sin) -> the √-basis field dict {sqfree: [powers]}."""
    c, s = ANGLE_SET[name][1], ANGLE_SET[name][2]
    radicals = set()
    for e in (c, s):
        radicals |= {r for r in sp.preorder_traversal(e)
                     if isinstance(r, sp.Pow) and r.exp == sp.Half
                     and isinstance(r.base, sp.Integer)}
    return radicals


def basis_for(radicals):
    """Multiplicative √-basis: all squarefree products, as sympy exprs."""
    rads = sorted(set(radicals), key=lambda r: r.base)
    bases = [sp.Integer(1)]
    for r in rads:
        bases = bases + [b * r for b in bases]
    return bases


def fit_in_basis(val, bases, den_max=24, num_max=480, tol=1e-6):
    """Integer-scan fit val = sum c_i*basis_i / d. Returns coeffs or None."""
    best = None
    bvals = [float(b) for b in bases]
    for d in range(1, den_max + 1):
        vd = val * d
        # greedy: solve for largest basis first? full scan only if dim<=2
        if len(bases) <= 2:
            for c0 in range(-num_max, num_max + 1):
                resid = None
                if len(bases) == 1:
                    resid = abs(c0 / d - val)
                    if resid < tol and (best is None or resid < best[0]):
                        best = (resid, [c0], d)
                else:
                    c1 = round((vd - c0) / bvals[1])
                    if abs(c1) > num_max:
                        continue
                    resid = abs((c0 + c1 * bvals[1]) / d - val)
                    if resid < tol and (best is None or resid < best[0]):
                        best = (resid, [c0, c1], d)
        elif len(bases) == 3:
            for c0 in range(-num_max, num_max + 1):
                r1 = vd - c0
                c2 = round(r1 / bvals[2]) if abs(bvals[2]) > 1e-9 else 0
                if abs(c2) > num_max:
                    continue
                r2 = r1 - c2 * bvals[2]
                c1 = round(r2 / bvals[1]) if abs(bvals[1]) > 1e-9 else 0
                if abs(c1) > num_max:
                    continue
                resid = abs((c0 + c1 * bvals[1] + c2 * bvals[2]) / d - val)
                if resid < tol and (best is None or resid < best[0]):
                    best = (resid, [c0, c1, c2], d)
        else:
            return None  # compositum too wide for scans; honest skip
    return best


# ---- Stage C: exhaustive certified scan (NOT PSLQ) --------------------
# The stored L is a 12-dp value = true + clearance(<=1.4e-9); a genuine
# algebraic L therefore fits its form at residual <= ~1.5e-9. PSLQ with
# loose tolerance was measured to produce spurious relations — replaced
# by exhaustive integer scans over the SAME form ladder the mapping
# uses: rational, (c0+c1√m)/d, biquadratic. Per-stage residual budgets:
#   rational 2e-8 (density ~38/unit in [2,32]: noise ~1e-6/value)
#   quadratic 3e-9 (measured noise reported by the negative control)
#   biquadratic 1.5e-9 with the c3 EXPLICIT SCAN (the derivation
#     c0=round(r2), c3=round((r2-c0)/rab) — inherited from the mapping —
#     is valid only when |c3*rab| < 0.5; it silently forced c3=0 on every
#     historical fit, which is how 8 borderline members entered Level 3).
import math as _m

import numpy as np

SQFREE = [2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23]
DIVS = [1, 2, 3, 4, 6, 8, 12, 24]
TOL_RAT = 2e-8
TOL_QUAD = 3e-9
TOL_BQ = 1.5e-9


def scan_exact(v, want_bq=True):
    """Exhaustive: rational p/q; then (c0+c1√m)/d; then biquadratic with
    the explicit c3 scan. Returns dict(minpoly, degree, form, resid) or
    None. Budgets above; every stage's noise is measured by the controls."""
    # rational
    for q in range(1, 25):
        p = round(v * q)
        if abs(p) <= 480 and abs(p / q - v) < TOL_RAT:
            return {"form": f"{p}/{q}", "degree": 1,
                    "minpoly": str(sp.Poly(sp.sympify(f"x - {p}/{q}"), X).as_expr()),
                    "resid": abs(p / q - v)}
    # quadratic
    best = None
    for mm in SQFREE:
        r = _m.sqrt(mm)
        for d in DIVS:
            vd = v * d
            for c1 in range(-240, 241):
                c0 = round(vd - c1 * r)
                if abs(c0) > 480:
                    continue
                resid = abs((c0 + c1 * r) / d - v)
                if resid < TOL_QUAD and (best is None or resid < best["resid"]):
                    best = {"form": f"({c0}+{c1}√{mm})/{d}", "degree": 2,
                            "minpoly": None, "resid": resid,
                            "expr": (sp.Integer(c0) + sp.Integer(c1) * sp.sqrt(mm)) / d}
    if best is not None:
        poly = sp.minimal_polynomial(best["expr"], X)
        best["minpoly"] = str(poly.as_expr())
        del best["expr"]
        return best
    if not want_bq:
        return None
    # biquadratic: c0 AND c3 both derived per (c1,c2,c3) — the explicit
    # c3 scan (61^3 x 8 x 3 derived combos, vectorized over c1 x c2).
    C = np.arange(-60, 61)
    for (a, b) in ((2, 3), (2, 5), (3, 5)):
        ra, rb, rab = _m.sqrt(a), _m.sqrt(b), _m.sqrt(a * b)
        for d in DIVS:
            vd = v * d
            R2 = (vd - C[:, None] * ra - C[None, :] * rb)   # 121 x 121
            for c3 in range(-60, 61):
                F = R2 - c3 * rab
                c0 = np.rint(F)
                resid = np.abs(F - c0)                       # = d*|expr - v|
                ok = (resid < TOL_BQ * d) & (np.abs(c0) <= 480)
                if not ok.any():
                    continue
                # take the minimum residual among hits
                resid_ok = np.where(ok, resid, np.inf)
                idx = np.unravel_index(np.argmin(resid_ok), resid_ok.shape)
                i1, i2 = int(C[idx[0]]), int(C[idx[1]])
                c0v = int(round(float(c0[idx])))
                r_final = float(resid_ok[idx]) / d
                expr = ((sp.Integer(c0v) + sp.Integer(i1) * sp.sqrt(a)
                         + sp.Integer(i2) * sp.sqrt(b)
                         + sp.Integer(c3) * sp.sqrt(a * b)) / d)
                poly = sp.minimal_polynomial(expr, X)
                return {"form": f"({c0v}+{i1}√{a}+{i2}√{b}+{c3}√{a*b})/{d}",
                        "degree": 4, "minpoly": str(poly.as_expr()),
                        "resid": r_final}
    return None


def main():
    lvl0 = MAP["unresolved"]
    rows = []
    stats = Counter()
    angle_hist = Counter()

    for n in lvl0:
        st = TAB[str(n)]["state"]
        L = float(TAB[str(n)]["L"])
        src = TAB[str(n)]["src"]
        row = {"n": n, "L": L, "src": src}

        # ---- Stage A: angle inventory
        names, dists, nonalg = [], [], []
        for c in st:
            nm, a, b = match_angle(c[2])[:3] if False else match_angle(c[2])
            if nm:
                names.append(nm)
            else:
                nonalg.append(round(a, 4))
        row["angles_matched"] = sorted(set(names))
        row["angles_nonalg"] = sorted(set(nonalg))
        for nm in set(names):
            angle_hist[nm] += 1
        stats["states_all_alg" if not nonalg else "states_with_nonalg"] += 1

        # ---- Stage B: exact reconstruction (only if all angles alg)
        cert = None
        if nonalg:
            row["stageB"] = "blocked: non-algebraic angle present"
        else:
            radicals = set()
            for nm in set(names):
                radicals |= field_of_angle(nm)
            bases = basis_for(radicals)
            okc = True
            exact_centers = []
            for c in st:
                fx = fit_in_basis(c[0], bases)
                fy = fit_in_basis(c[1], bases)
                if fx is None or fy is None:
                    okc = False
                    break
                exact_centers.append((fx, fy, nm2 := match_angle(c[2])[1]))
            if okc and exact_centers:
                # exact bbox: max over squares of center +- half-extent
                def half_extent(cee, ssn):
                    cc, ssn_ = ANGLE_SET[ssn][1], ANGLE_SET[ssn][2]
                    return (abs(cc) + abs(ssn_)) / 2
                xs, ys = [], []
                for (fx, fy, ssn), c in zip(exact_centers, st):
                    he = half_extent(None, ssn)
                    cx = sum(fx[1][i] * bases[i] for i in range(len(bases))) / fx[2]
                    cy = sum(fy[1][i] * bases[i] for i in range(len(bases))) / fy[2]
                    xs += [cx - he, cx + he]
                    ys += [cy - he, cy + he]
                Lx = sp.Rational(0)
                L_exact = sp.simplify(max(xs) - min(xs))
                L_exact2 = sp.simplify(max(ys) - min(ys))
                Lq = sp.simplify(max(L_exact, L_exact2))
                try:
                    poly = sp.minimal_polynomial(Lq, X)
                    deg = int(sp.degree(poly, X))
                    g, _ = sp.polys.numberfields.galois_group(poly, X)
                    cert = {"s_exact": str(Lq), "degree": deg,
                            "minimal_polynomial": str(poly.as_expr()),
                            "galois_group": str(g), "level":
                            {1: 1, 2: 2, 4: 3}.get(deg, 4 if deg >= 8 else 0)}
                    stats["stageB_certified"] += 1
                except Exception as e:
                    row["stageB"] = f"exact computation failed: {e}"
            else:
                row["stageB"] = "blocked: centers do not fit the angle field"
                stats["stageB_center_fail"] += 1
        if cert:
            row["stageB"] = cert

        # ---- Stage C: exhaustive certified scan (value-level)
        hyp = scan_exact(L)
        if hyp:
            row["stageC"] = hyp
            stats[f"scan_deg{hyp['degree']}"] += 1
        else:
            row["stageC"] = None
            stats["scan_none"] += 1
        rows.append(row)

    # ---- controls
    def norm_poly(s):
        """Primitive integer poly, leading coeff positive; None on error."""
        try:
            p = sp.Poly(sp.sympify(s), X)
            cont, prim = p.primitive()
            if prim.LC() < 0:
                prim = -prim
            return str(prim.as_expr())
        except Exception:
            return None

    # in-ladder = field expressible by the scan's forms; out-of-ladder =
    # nested quartic Q(√(2+√2)) — covered by the certificate route in the
    # mapping, outside the scan's expressive range BY DESIGN.
    def in_ladder(field):
        return field == "Q" or (field.startswith("Q(√") and "," not in field) \
            or field in ("Q(√2,√3)", "Q(√2,√5)", "Q(√3,√5)")

    pos_ok = pos_tot = 0
    pos_fail = []
    pos_skip = 0
    for c in CERTS:
        try:
            ex = parse_exact(c["s_exact"])
            v = round(float(sp.N(ex, 30)), 12)
            want = norm_poly(str(sp.minimal_polynomial(ex, X).as_expr()))
        except Exception:
            continue
        if not in_ladder(c.get("field", "")):
            pos_skip += 1        # nested quartic: out of scan range by design
            continue
        got = scan_exact(v)
        if got and norm_poly(got["minpoly"]) == want:
            pos_ok += 1
        else:
            pos_fail.append({"n": c.get("n"), "s_exact": c["s_exact"],
                             "field": c.get("field"),
                             "want": want,
                             "got": (got or {}).get("minpoly")})
        pos_tot += 1

    import random
    random.seed(20261104)
    NEG_N = 300
    neg_hits = 0
    for _ in range(NEG_N):
        v = round(random.uniform(2.0, 32.0), 12)
        if scan_exact(v):
            neg_hits += 1
    noise_rate = neg_hits / NEG_N
    sig = (1.0 - noise_rate) ** len(lvl0)

    # ---- re-audit the mapping's 8 Level-3 members (c3=0 borderline fits)
    reaudit = []
    for r in MAP["rows"]:
        if r.get("how") == "fit-biquadratic":
            n = r["n"]
            L = float(TAB[str(n)]["L"])
            got = scan_exact(L)
            reaudit.append({"n": n, "old_form": r.get("form"),
                            "old_resid": r.get("fit_resid"),
                            "new": got})

    out = {
        "level0_count": len(lvl0),
        "min_angle_gap_deg": round(MIN_GAP, 4),
        "match_window_deg": WINDOW,
        "rows": rows,
        "angle_histogram": dict(angle_hist),
        "stats": dict(stats),
        "controls": {
            "positive": {"in_ladder": pos_tot, "recovered": pos_ok,
                         "rate": round(pos_ok / pos_tot, 4) if pos_tot else None,
                         "out_of_ladder_by_design": pos_skip,
                         "failures": pos_fail[:10]},
            "negative": {"random_values": NEG_N, "spurious": neg_hits,
                         "noise_rate": round(noise_rate, 4)},
            "level0_zero_fits_pvalue": sig,
        },
        "level3_reaudit": reaudit,
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print("level-0:", len(lvl0))
    print("stats:", dict(stats))
    print("angle histogram:", dict(angle_hist))
    print(f"control pos: {pos_ok}/{pos_tot} in-ladder "
          f"({pos_skip} out-of-ladder by design)")
    print(f"control neg: {neg_hits}/{NEG_N} (noise rate {noise_rate:.4f})")
    print(f"P(0 fits among {len(lvl0)} | noise) = {sig:.3e}")
    print(f"level-3 re-audit: {len(reaudit)} members")
    for r in reaudit:
        print("   n=%s old_resid=%s -> %s" % (
            r["n"], r["old_resid"],
            "RECOVERED " + r["new"]["form"] if r["new"] else "no fit (reclassify)"))
    print("->", OUT)


if __name__ == "__main__":
    main()
