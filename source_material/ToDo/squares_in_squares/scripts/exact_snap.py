#!/usr/bin/env python3
r"""exact_snap.py — Run 12: integer-exact geometric verification.

The Leech/Golay discipline (leech_core.py: integer-exact, no floats)
applied to the packing states. For every table row:

  1. CERT MATCH: value-level cert (1e-6) -> the claimed exact field
     and s_exact. Scope: Q, Q(sqrt2), Q(sqrt7).
  2. ANGLE SCOPE: all square angles within 0.01 deg of {0, 45} (mod 90)
     — the class where exact predicates are closed in the field:
       0-0   : |dx| >= 1 or |dy| >= 1
       45-45 : |dx+dy| >= sqrt(2) or |dx-dy| >= sqrt(2)
       mixed : max(|dx|-1/2,0) + max(|dy|-1/2,0) >= sqrt(2)/2
     (45-degree predicates need sqrt(2) in the field: rows in Q(sqrt7)
     with a 45-deg square are classified compositum-out-of-scope.)
  3. SNAP: every coordinate fit as (c0 + c1*sqrt(m))/d, d | 24,
     |c0| <= 480, |c1| <= 240, residual < 4e-9*d (the run-11
     calibration: table clearance 1.3-1.9e-9 + margin).
  4. VERIFY (exact arithmetic, Fractions only):
     container: exact bbox <= s_exact (cert value);
     pairwise: the three predicates above, touch allowed.

Classification per row -> counts by src family and cert provenance.
Expected (run-11 analysis): constructed rows (formula provenance)
verify exactly; value-scan certs on parsed states (chain3 / SVG)
fail the snap — their certificate is value-level only. That measured
split is the honest meaning of "certificate" per row.

Output: download/exact_snap.json
"""
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction as F
from math import degrees, sqrt

import sympy as sp

TAB = json.load(open("/home/z/my-project/download/table.json"))
CERTS = json.load(open("/home/z/my-project/download/galois_certificates.json"))
OUT = "/home/z/my-project/download/exact_snap.json"

DIVS = [1, 2, 3, 4, 6, 8, 12, 24]
SNAP_TOL = 4e-9      # per unit d: residual < SNAP_TOL * d
ANGLE_WIN = 0.01     # degrees


# ---------- exact arithmetic in Q(sqrt(m)) ---------------------------
class QE:
    """a + b*sqrt(m), Fractions."""
    __slots__ = ("a", "b", "m")

    def __init__(self, a, b, m):
        self.a, self.b, self.m = F(a), F(b), m

    def __add__(self, o):
        assert self.m == o.m
        return QE(self.a + o.a, self.b + o.b, self.m)

    def __sub__(self, o):
        assert self.m == o.m
        return QE(self.a - o.a, self.b - o.b, self.m)

    def __neg__(self):
        return QE(-self.a, -self.b, self.m)

    def abs(self):
        return self if self.cmp0() >= 0 else -self

    def cmp0(self):
        """sign of a + b*sqrt(m): -1/0/+1. Exact via square comparison."""
        if self.b == 0:
            return (self.a > 0) - (self.a < 0)
        if self.a == 0:
            return 1 if self.b > 0 else -1
        sa = self.a > 0
        sb = self.b > 0
        if sa == sb:
            # same sign: |a| + |b|sqrt(m) with both same sign -> the sum
            # has that sign (both terms add constructively)
            return 1 if sa else -1
        # opposite signs: sign of a + b*sqrt(m) = sign of a^2 - m*b^2
        # (multiply by a - b*sqrt(m), which shares the sign of the larger
        # term; (a+bs)(a-bs) = a^2 - m*b^2, and a-bs has the sign of a)
        d = self.a * self.a - self.m * self.b * self.b
        if d == 0:
            # impossible over Q unless both zero (sqrt(m) irrational, m>1):
            # a^2 = m b^2 with b != 0 would make sqrt(m) = |a/b| rational
            return (self.a > 0) - (self.a < 0)
        sd = d > 0
        # if a > 0, b < 0: a - b*sqrt(m) > 0 always (a>0, -b*sqrt(m)>0)
        # sign(a + b*sqrt(m)) = sign(a^2 - m*b^2) * sign(a) ... careful:
        # (a+b√m)(a−b√m) = a²−m·b². a−b√m > 0 when a>0 (both terms >0).
        # so sign(a+b√m) = sign(a²−m·b²) when a>0; = -sign(a²−m·b²)·(−1)^{a<0}
        if sa:
            return 1 if d > 0 else -1
        else:
            return -1 if d > 0 else 1

    def cmp(self, o):
        """-1/0/+1 comparing self vs o (same m)."""
        return (self - o).cmp0()

    def ge(self, o):
        return self.cmp(o) >= 0

    def half_width(self, cls):
        """Half-extent of a unit square of class 0/45 along x (or y)."""
        if cls == 0:
            return QE(F(1, 2), 0, self.m)
        return QE(0, F(1, 2), self.m)   # sqrt(m)/2 with m=2 -> sqrt2/2


def qe_sqrt2_half(m):
    return QE(0, F(1, 2), m) if m == 2 else None


def cmp_le(a2, b2, m):
    """exact: (a2) <= (b2) as QEs."""
    return a2.cmp(b2) <= 0


# ---------- cert matching --------------------------------------------
def parse_exact(s):
    import re
    s = s.replace("·", "*").replace(" ", "")
    s = re.sub(r"(\d)√", r"\1*sqrt", s)
    s = s.replace("√", "sqrt")
    s = re.sub(r"sqrt(\d+)", r"sqrt(\1)", s)
    return sp.sympify(s)


certs_by_n = defaultdict(list)
for c in CERTS:
    certs_by_n[c.get("n")].append(c)


def cert_value(c):
    if c.get("s_float") is not None:
        return float(c["s_float"])
    return float(sp.N(parse_exact(c["s_exact"]), 30))


def field_m(field):
    if field == "Q":
        return 1
    if field in ("Q(√2)",):
        return 2
    if field in ("Q(√7)",):
        return 7
    return None


def s_exact_qe(c, m):
    """Exact s value of the cert as QE in Q(sqrt(m)) (m from its field)."""
    ex = parse_exact(c["s_exact"])
    r = sp.sqrt(m if m > 1 else 2)
    if m == 1:
        val = sp.simplify(ex)
        assert val.is_Rational
        return QE(F(int(val.p), int(val.q)), 0, 1)
    conj = ex.subs(r, -r)
    A = sp.simplify((ex + conj) / 2)
    B = sp.simplify((ex - conj) / (2 * r))
    assert A.is_Rational and B.is_Rational, f"not in Q(sqrt({m})): {c['s_exact']}"
    return QE(F(int(A.p), int(A.q)), F(int(B.p), int(B.q)), m)


# ---------- snapping --------------------------------------------------
def snap_coord(x, m):
    """Fit x = (c0 + c1*sqrt(m))/d. Returns QE or None.

    Full c1 scan (-240..240) per d, c0 derived by rounding — the
    leech_map audited standard. (Run-12 fix: the first version
    anchored c1 near vd/sqrt(m)+-2, which misses forms with a large
    rational part — e.g. (30-9*sqrt2)/4 needs c1=-9 at anchor 12.)"""
    if m == 1:
        for q in range(1, 25):
            p = round(x * q)
            if abs(p) <= 480 and abs(p / q - x) < SNAP_TOL:
                return QE(F(p, q), 0, 1)
        return None
    r = sqrt(m)
    for d in DIVS:
        vd = x * d
        for c1 in range(-240, 241):
            c0 = round(vd - c1 * r)
            if abs(c0) > 480:
                continue
            if abs(c0 + c1 * r - vd) < SNAP_TOL * d:
                return QE(F(c0, d), F(c1, d), m)
    return None


def angle_class(th):
    d = (degrees(th) % 90.0 + 90.0) % 90.0
    if min(d, 90 - d) < ANGLE_WIN:
        return 0
    if abs(d - 45) < ANGLE_WIN:
        return 45
    return None


# ---------- main ------------------------------------------------------
def main():
    rows = []
    stats = Counter()
    by_family = defaultdict(Counter)

    for n in range(1, 1001):
        rec = TAB[str(n)]
        st = rec["state"]
        src = rec["src"]
        fam = src.split(":")[0]
        L = float(rec["L"])
        row = {"n": n, "src": src, "family": fam, "L": L}

        # 1. cert
        match = [c for c in certs_by_n.get(n, [])
                 if abs(cert_value(c) - L) < 1e-6]
        if not match:
            row["class"] = "no_cert"
            stats["no_cert"] += 1
            by_family[fam]["no_cert"] += 1
            rows.append(row)
            continue
        c = match[0]
        row["provenance"] = c.get("provenance", "original")
        m = field_m(c.get("field", ""))
        if m is None:
            row["class"] = "field_out_of_scope"
            stats["field_out_of_scope"] += 1
            by_family[fam]["field_out_of_scope"] += 1
            rows.append(row)
            continue
        row["field"] = c["field"]

        # 2. angle scope
        classes = []
        for sq in st:
            cl = angle_class(sq[2])
            if cl is None:
                row["class"] = "angle_out_of_scope"
                break
            classes.append(cl)
        if row.get("class") == "angle_out_of_scope":
            stats["angle_out_of_scope"] += 1
            by_family[fam]["angle_out_of_scope"] += 1
            rows.append(row)
            continue
        if m != 2 and 45 in classes:
            row["class"] = "compositum_needed (45deg outside field)"
            stats["compositum_needed"] += 1
            by_family[fam]["compositum_needed"] += 1
            rows.append(row)
            continue

        # 3. snap all coordinates
        xs, ys = [], []
        ok = True
        for sq in st:
            fx = snap_coord(sq[0], m)
            fy = snap_coord(sq[1], m)
            if fx is None or fy is None:
                ok = False
                break
            xs.append(fx)
            ys.append(fy)
        if not ok:
            row["class"] = "snap_failed"
            stats["snap_failed"] += 1
            by_family[fam]["snap_failed"] += 1
            rows.append(row)
            continue

        # 4. exact verification
        s_val = s_exact_qe(c, m)
        one = QE(1, 0, m)
        half = QE(F(1, 2), 0, m)
        s2h = QE(0, F(1, 2), 2) if m == 2 else None   # sqrt2/2
        sqs = list(zip(xs, ys, classes))

        # container: bbox <= s_exact
        minx = miny = None
        maxx = maxy = None
        for (x, y, cl) in sqs:
            hw = half if cl == 0 else s2h
            lo_x, hi_x = x - hw, x + hw
            lo_y, hi_y = y - hw, y + hw
            if minx is None or lo_x.cmp(minx) < 0:
                minx = lo_x
            if maxx is None or hi_x.cmp(maxx) > 0:
                maxx = hi_x
            if miny is None or lo_y.cmp(miny) < 0:
                miny = lo_y
            if maxy is None or hi_y.cmp(maxy) > 0:
                maxy = hi_y
        width = (maxx - minx) if minx is not None else None
        height = (maxy - miny) if miny is not None else None
        cont_ok = True
        if width is not None and width.cmp(s_val) > 0:
            cont_ok = False
        if height is not None and height.cmp(s_val) > 0:
            cont_ok = False
        # exact margin
        margin = None
        if width is not None:
            margin = s_val.cmp(width)

        # pairwise (sweep by x)
        order = sorted(range(len(sqs)), key=lambda i: sqs[i][0].a + sqs[i][0].b * 0)
        # exact sort: sort by numeric value for the sweep window only
        order = sorted(range(len(sqs)),
                       key=lambda i: float(sqs[i][0].a) + float(sqs[i][0].b) * sqrt(m))
        pairs_bad = 0
        n_pairs = 0
        for ii in range(len(order)):
            i = order[ii]
            xi, yi, ci = sqs[i]
            hwi = half if ci == 0 else s2h
            for jj in range(ii + 1, len(order)):
                j = order[jj]
                xj, yj, cj = sqs[j]
                hwj = half if cj == 0 else s2h
                dx = xi - xj
                if dx.abs().cmp(hwi + hwj) >= 0:
                    # x-projections disjoint -> interiors disjoint
                    continue
                # within possible contact: check the exact predicate
                n_pairs += 1
                dy = yi - yj
                if ci == 0 and cj == 0:
                    okp = (dx.abs().ge(one)) or (dy.abs().ge(one))
                elif ci == 45 and cj == 45:
                    okp = ((dx + dy).abs().ge(QE(0, 1, 2))
                           if m == 2 else True)
                    if m == 2:
                        okp = ((dx + dy).abs().ge(QE(0, 1, 2))
                               or (dx - dy).abs().ge(QE(0, 1, 2)))
                else:
                    # mixed: max(|dx|-1/2,0) + max(|dy|-1/2,0) >= sqrt2/2
                    if m == 2:
                        adx = dx.abs() - half
                        ady = dy.abs() - half
                        t1 = adx if adx.cmp0() > 0 else QE(0, 0, m)
                        t2 = ady if ady.cmp0() > 0 else QE(0, 0, m)
                        okp = (t1 + t2).ge(s2h)
                    else:
                        okp = None
                if okp is True:
                    continue
                if okp is None:
                    continue
                pairs_bad += 1
        if not cont_ok or pairs_bad:
            row["class"] = "verify_failed"
            row["container_ok"] = cont_ok
            row["pairs_bad"] = pairs_bad
            stats["verify_failed"] += 1
            by_family[fam]["verify_failed"] += 1
        else:
            row["class"] = "exact_verified"
            row["pairs_checked"] = n_pairs
            stats["exact_verified"] += 1
            by_family[fam]["exact_verified"] += 1
        rows.append(row)

    # provenance cross
    prov_cross = defaultdict(Counter)
    for r in rows:
        prov_cross[r.get("provenance", "original")][r["class"]] += 1

    out = {
        "rows": rows,
        "stats": dict(stats),
        "by_family": {k: dict(v) for k, v in by_family.items()},
        "provenance_x_class": {k: dict(v) for k, v in prov_cross.items()},
        "convention": {
            "snap_tol_per_d": SNAP_TOL,
            "angle_window_deg": ANGLE_WIN,
            "predicates": ["0-0: |dx|>=1 or |dy|>=1",
                           "45-45: |dx+dy|>=sqrt2 or |dx-dy|>=sqrt2",
                           "mixed: max(|dx|-1/2,0)+max(|dy|-1/2,0)>=sqrt2/2"],
        },
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print("stats:", dict(stats))
    print("by family:")
    for fam, cc in sorted(by_family.items()):
        print("  ", fam, dict(cc))
    print("provenance x class:")
    for p, cc in prov_cross.items():
        print("  ", p, dict(cc))
    print("->", OUT)


if __name__ == "__main__":
    main()
