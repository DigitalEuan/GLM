#!/usr/bin/env python3
r"""seam_census.py — run 26 P1(c): census + decode of the tilted-seam
records (axis-aligned dominant + tilted seams).

Question (NEXT_STEPS P1(c)): do the sub-grid records form a clean
parametric family (the run-25 method: decode -> closed form -> sweep),
or something else?  This script measures:

  1. CENSUS over all sub-grid rows: split the state into axis-aligned
     majority / tilted minority; cluster the tilted angles (1.5 deg);
     classify each row's dominant cluster:
       - 'strip-45'    all tilted at 45.000 deg (the Gobel strip = P1(a),
                       closed run 25);
       - 'pyth-exact'  the dominant angle is a Pythagorean angle
                       atan2(b,a), a^2+b^2=c^2, within 0.15 deg;
       - 'drift'       otherwise (report angle + spread).
  2. DECODE of the cleanest case n=50 (L=53/7, 7^2+1): exact angle,
     rational lattices (tilted centers on 1/25; axis grid at 2/7 mod 1),
     contact count, the grid-capacity+1 signature, the blob structure
     in the (u,v) frame.
  3. CONCLUSION for NEXT_STEPS: (c) is a search regime, not a family;
     the follow-up is a blob-regime insertion campaign (named there).

Output: workspace/push/seam_census26.json + stdout summary.
"""
import itertools
import json
import math
import os

W = "/home/z/my-project"
TAB = W + "/workspace/submission/table.json"
OUT = W + "/workspace/push/seam_census26.json"

# Pythagorean angles: (a,b,c) with a<b, c<=200, folded to [0,90)
PYTH = []
for c in range(5, 201):
    for a in range(1, c):
        b2 = c * c - a * a
        b = int(math.isqrt(b2))
        if b >= 1 and a < b and b * b == b2:
            ang = math.degrees(math.atan2(b, a))
            PYTH.append((round(ang, 4), (a, b, c)))
PYTH.sort()


def fold(theta):
    """fold to [0, 90) in degrees"""
    d = math.degrees(theta) % 90.0
    if d >= 89.999 or d < 0.0005:
        d = 0.0
    return d


def clusters(anons):
    """anons: list of (folded_deg, index). Greedy 1.5-deg clustering."""
    anons = sorted(anons)
    out = []
    cur = [anons[0]]
    for a in anons[1:]:
        if a[0] - cur[-1][0] <= 1.5:
            cur.append(a)
        else:
            out.append(cur)
            cur = [a]
    out.append(cur)
    return out


def main():
    tab = json.load(open(TAB))
    rows = []
    for k in sorted(tab, key=int):
        n = int(k)
        g = math.ceil(math.sqrt(n))
        r = tab[k]
        if r["L"] >= g - 1e-9:
            continue
        st = r["state"]
        ax = [s for s in st if fold(s[2]) < 0.05 or fold(s[2]) > 89.95]
        til = [s for s in st if not (fold(s[2]) < 0.05 or fold(s[2]) > 89.95)]
        if not til:
            cls = "no-tilt??"
        else:
            anons = [(fold(s[2]), i) for i, s in enumerate(til)]
            cls_list = clusters(anons)
            big = max(cls_list, key=len)
            th = sum(a for a, _ in big) / len(big)
            spread = max(a for a, _ in big) - min(a for a, _ in big)
            n45 = sum(1 for s in til if abs(fold(s[2]) - 45.0) < 0.05)
            if n45 == len(til):
                cls = "strip-45"
            else:
                hit = None
                # exact Pythagorean requires a TIGHT cluster: a drifted
                # cluster (spread > 0.3 deg) is a hand-polished blob
                # even when its mean lands near a Pythagorean angle
                # (e.g. n=84: 28.017..29.129 vs atan2(8,15)=28.07).
                if spread <= 0.3:
                    for pa, (aa, bb, cc) in PYTH:
                        for cand in (pa, 90 - pa):
                            if abs(th - cand) < 0.15:
                                hit = (round(cand, 3), (aa, bb, cc))
                                break
                        if hit:
                            break
                cls = "pyth-exact" if hit else "drift"
            rows.append({"n": n, "L": r["L"], "grid": g, "src": r.get("src", ""),
                         "n_axis": len(ax), "n_tilt": len(til),
                         "class": cls, "theta": round(th, 3),
                         "spread": round(spread, 3),
                         "pyth": hit[1] if (cls == "pyth-exact" and hit) else None})
    # aggregate
    agg = {}
    for row in rows:
        agg.setdefault(row["class"], []).append(row)
    print(f"sub-grid rows: {len(rows)}")
    for c in ("strip-45", "pyth-exact", "drift"):
        rs = agg.get(c, [])
        print(f"  {c:10s}: {len(rs):3d} rows"
              + (f"  angles: {sorted({round(r['theta'],1) for r in rs})[:12]}"
                 if c != "strip-45" and rs else ""))

    # ---- decode n=50
    r50 = tab["50"]
    st = r50["state"]
    L = r50["L"]
    til = [s for s in st if fold(s[2]) > 0.05 and fold(s[2]) < 89.95]
    ax = [s for s in st if fold(s[2]) <= 0.05 or fold(s[2]) >= 89.95]
    th_mean = sum(fold(s[2]) for s in til) / len(til)
    th_exact = math.degrees(math.atan2(3, 4))
    # lattice auto-detect: smallest d with all tilted centers on (1/d)Z^2
    lat_d, lat_dev = None, None
    for d in range(1, 201):
        dev = max(max(abs(x * d - round(x * d)), abs(y * d - round(y * d)))
                  for x, y, _ in til)
        if dev < 1e-6:
            lat_d, lat_dev = d, dev
            break
    # axis grid: centers at (2+7i)/7, i in Z, i.e. (7x) mod 7 in {2, 5}
    grid_ok = all((round(x * 7) % 7) in (2, 5) and (round(y * 7) % 7) in (2, 5)
                  for x, y, _ in ax)
    off = max(max(abs(x * 7 - round(x * 7)), abs(y * 7 - round(y * 7)))
              for x, y, _ in ax)
    # contacts (full SAT pair margin: extent = projection of BOTH edges)
    def pair_margin(a, b):
        m = 1e9
        for th_i in (a[2], b[2]):
            uu = (math.cos(th_i), math.sin(th_i))
            w = (-math.sin(th_i), math.cos(th_i))
            for axv in (uu, w):
                d = (b[0] - a[0]) * axv[0] + (b[1] - a[1]) * axv[1]
                ea = 0.5 * (abs(math.cos(a[2]) * axv[0] + math.sin(a[2]) * axv[1])
                            + abs(-math.sin(a[2]) * axv[0] + math.cos(a[2]) * axv[1]))
                eb = 0.5 * (abs(math.cos(b[2]) * axv[0] + math.sin(b[2]) * axv[1])
                            + abs(-math.sin(b[2]) * axv[0] + math.cos(b[2]) * axv[1]))
                m = min(m, ea + eb - abs(d))
        return m
    ncont = sum(1 for a, b in itertools.combinations(st, 2)
                if pair_margin(a, b) > -1e-5)
    K = 7
    decode50 = {
        "n": 50, "K2plus1": f"{K}^2+1",
        "stored_L": L,
        "L_exact_53_over_7": 53 / 7,
        "L_dev": L - 53 / 7,
        "angle_mean_deg": th_mean, "angle_exact_arctan3_4": th_exact,
        "angle_dev_deg": th_mean - th_exact,
        "tilted_lattice_denominator": lat_d,
        "tilted_lattice_maxdev": lat_dev,
        "axis_grid_mod7_offset2_ok": grid_ok,
        "axis_offset_maxdev": off,
        "n_axis": len(ax), "n_tilt": len(til),
        "contacts_at_zero": ncont,
        "grid_capacity_at_L": math.floor(53 / 7 + 1e-9) ** 2,
        "signature": ("packs grid-capacity+1 into L=53/7: the K^2+1 "
                      "architecture; the blob is an isostatic "
                      "hand-polished arrangement, not a parametric "
                      "family member")}
    print("\nn=50 decode:")
    for k2, v in decode50.items():
        print(f"  {k2}: {v}")

    # ---- n=50 blob structure in the (u,v) frame (for the record)
    u = (4 / 5, 3 / 5)
    vv = (-3 / 5, 4 / 5)
    blob = sorted({(round(s[0] * u[0] + s[1] * u[1], 3),
                    round(s[0] * vv[0] + s[1] * vv[1], 3)) for s in til})
    print(f"  blob (u,v) centers: {blob}")

    json.dump({
        "run": 26, "part": "P1(c) census + decode",
        "census": {"sub_grid_rows": len(rows),
                   "by_class": {c: len(agg.get(c, []))
                                for c in ("strip-45", "pyth-exact", "drift")},
                   "rows": rows},
        "decode_n50": decode50,
        "blob_uv": blob,
        "conclusion": (
            "P1(c) records are isostatic, hand-polished blobs at "
            "(mostly) Pythagorean angles on rational lattices — e.g. "
            "n=50: exact arctan(3/4), tilted centers on the 1/25 "
            "lattice, axis grid at 2/7 mod 1, L=53/7 exact, 105 "
            "contacts, K^2+1 signature.  They are NOT members of a "
            "low-dimensional parametric family: the run-25 method "
            "(decode->closed form->sweep) does not transfer.  The "
            "follow-up is a blob-regime INSERTION campaign (seed from "
            "the records themselves, insert one square at fixed L, "
            "pressure-settle) — named in NEXT_STEPS.md as the next "
            "P2 variant."),
    }, open(OUT, "w"), indent=1)
    print("\nledger ->", OUT)


if __name__ == "__main__":
    main()
