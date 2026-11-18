#!/usr/bin/env python3
r"""r1_atoms.py — G-1: the r = 1 column read in the exact t-basis.

Every row with n = k^2 + 1 (k = 1..31) is one number and one word: delta = L - k
and the exact angle alphabet of its squares. G-1 asks whether the *word* changes
at k = 25, where delta steps from 0.535534 to 0.520815.

Angles are reduced mod pi/2 (a square is symmetric) and classified:

    axis     theta = 0              t = 0
    pi/4     theta = pi/4           t = sqrt2 - 1      (quadratic, the sqrt2 word)
    t=a/b    theta = 2 arctan(a/b)  rational t         (import certificate)
    other    neither                printed, never assumed

`pi/4` is detected by |theta - pi/4| < 1e-11, which separates the exact 45 degree
world (stored as 0.785398163397, error 4.5e-13) from the nearest rational
near-45 signature (225058681/543339720, 1e-10 away). Rational t is recovered by
continued fractions with denominator <= 1e7 and re-checked against the stored
angle, so `t=1/3` means the square is at 2*arctan(1/3), not "about 36.87".

Nothing here is a float guess about the geometry: delta is read off exactly
(Decimal(repr(L)) - k) and the only claim made is about the alphabet.

Output: table, delta-family grouping, an exact-candidate fit for each family's
delta, the tilted diamond each row carries, and a verdict line. Writes
`workspace/push/r1_atoms.json`.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from decimal import Decimal
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import leech_comb as C          # noqa: E402
import packlib                  # noqa: E402
import sqscore                  # noqa: E402

SUB = os.path.join(ROOT, "workspace/submission/submission.csv")
OUT = os.path.join(ROOT, "workspace/push/r1_atoms.json")

PI = math.pi
#: a *declared* rational t has a small denominator. With den <= 1e7 every float
#: angle fits some fraction, so the bound is what makes `t=1/3` a word and
#: `t=4258896/9585127` noise; the latter is reported as a plain angle instead.
MAX_DEN = 10 ** 4
TOL_45 = 1e-11


def rational_t(t: float):
    """tan(theta/2) as an exact Fraction, or None if it is not rational."""
    f = Fraction(t).limit_denominator(MAX_DEN)
    return f if abs(float(f) - t) <= 1e-12 else None


def classify(theta: float):
    """(class, exact t or None, theta mod pi/2) for one square's angle."""
    th = float(theta) % (PI / 2.0)
    if abs(math.sin(2.0 * th)) < 1e-12:
        return "axis", None, th
    if abs(th - PI / 4.0) < TOL_45:
        return "pi/4", None, th
    f = rational_t(math.tan(th / 2.0))
    if f is not None:
        return "t", f, th
    return "other", None, th


def t_denominator(theta: float, max_den=10 ** 7):
    """Smallest denominator that reproduces tan(theta/2) to 1e-12 (diagnostic)."""
    f = Fraction(math.tan(theta / 2.0)).limit_denominator(max_den)
    return f.denominator if abs(float(f) - math.tan(theta / 2.0)) <= 1e-12 else None


def word_of(state):
    """Counter of exact words, and the per-square classes."""
    counts = Counter()
    detail = []
    for s in state:
        cls, t, th = classify(float(s[2]))
        key = cls if t is None else f"t={t.numerator}/{t.denominator}"
        if cls == "other":
            key = f"other:{math.degrees(th):.6f}"
        counts[key] += 1
        detail.append((key, t, th))
    return counts, detail


def uniq_vals(vals, tol=1e-6):
    out = []
    for v in sorted(vals):
        if not out or v - out[-1] > tol:
            out.append(v)
    return out


def diamond(state, bits, L):
    """The 45-degree block: lattice spacing, p, occupancy, wall gap."""
    tilt = [s for s, b in zip(state, bits) if b]
    if not tilt:
        return None
    xs = uniq_vals([float(s[0]) for s in tilt])
    ys = uniq_vals([float(s[1]) for s in tilt])
    gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    spacing = min(gaps) if gaps else 0.0
    w = C.bbox(tilt)[2]
    p = (len(xs) + 1) // 2
    return {"count": len(tilt), "nx": len(xs), "ny": len(ys),
            "spacing": round(spacing, 9), "width": round(w, 9), "p": p,
            "occupancy": round(len(tilt) / (p * p), 6),
            "wall_gap": round(L - p * math.sqrt(2.0), 9)}


SURDS = (2, 3, 5, 6, 7, 10, 11, 13, 17)


def surd_fits(d, tol=1e-8, maxh=240):
    """Small-height (a + b*sqrt(D))/c matches for a delta, cheapest first."""
    out = []
    for D in SURDS:
        r = math.sqrt(D)
        for c in range(1, maxh + 1):
            for a in range(-maxh, maxh + 1):
                b = round((d * c - a) / r)
                if abs(b) > maxh:
                    continue
                v = (a + b * r) / c
                if abs(v - d) <= tol:
                    out.append({"D": D, "a": a, "b": b, "c": c,
                                "height": abs(a) + abs(b) + c,
                                "value": v, "err": v - d})
    out.sort(key=lambda z: (z["height"], z["D"], z["c"]))
    return out


def rational_fit(d, max_den=5000, tol=1e-8):
    f = Fraction(d).limit_denominator(max_den)
    return f if abs(float(f) - d) <= tol else None


def alphabet(words):
    """The set of angle classes in a word counter."""
    return {k if k in ("axis", "pi/4") else k.split(":")[0].split("=")[0]
            for k in words}


def main():
    store = packlib.read_csv(SUB)
    rows = []
    print(f"{'k':>2} {'n':>4} {'L':>14} {'delta':>12} {'tilt':>4} {'|E|':>5}  word")
    for k in range(1, 32):
        n = k * k + 1
        st = store.get(n)
        if st is None:
            print(f"{k:2d} {n:4d}  MISSING")
            continue
        L = sqscore.extent(st)
        delta = Decimal(repr(L)) - k
        bits = C.tilt_bits(st)
        counts, _ = word_of(st)
        m = sum(len(a) for a in C.contacts(st)) // 2
        d = diamond(st, bits, L)
        word = " ".join(f"{key}:{c}" for key, c in counts.most_common())
        print(f"{k:2d} {n:4d} {L:14.9f} {delta:12.9f} {sum(bits):4d} {m:5d}  {word}")
        rows.append({"k": k, "n": n, "L": L, "delta": float(delta),
                     "delta_str": f"{delta:.9f}", "tilt": sum(bits), "E": m,
                     "words": dict(counts), "diamond": d})

    fam: dict = {}
    for r in rows:
        fam.setdefault(round(r["delta"], 6), []).append(r)
    print("\ndelta families (delta to 1e-6):")
    for d, group in sorted(fam.items()):
        ks = [g["k"] for g in group]
        words: Counter = Counter()
        for g in group:
            words.update(g["words"])
        ps = sorted({g["diamond"]["p"] for g in group if g["diamond"]})
        print(f"  delta {d:+.9f}  k {min(ks)}..{max(ks)} ({len(group)} rows)  "
              f"p {ps}  word {dict(words)}")

    print("\nexact candidates for each family delta, (a + b*sqrt(D))/c, |.| <= 240:")
    fits_by_delta = {}
    for dkey, group in sorted(fam.items()):
        d = sum(g["delta"] for g in group) / len(group)   # 9 dp, not the 6 dp key
        rf = rational_fit(d)
        fits = surd_fits(d)[:3]
        fits_by_delta[f"{dkey:+.6f}"] = {
            "delta": d, "rational": str(rf) if rf else None, "surd": fits}
        print(f"  {d:+.9f}: " + (f"RATIONAL {rf}" if rf
                                  else "not rational (den <= 5000)"))
        for f in fits:
            print(f"      ({f['a']} + {f['b']}*sqrt{f['D']})/{f['c']} = "
                  f"{f['value']:.12f}  err {f['err']:+.2e}  h {f['height']}")

    print("\ntilted diamond per row (p from distinct x, occupancy = count/p^2):")
    for r in rows:
        d = r["diamond"]
        if d:
            print(f"  k={r['k']:2d} n={r['n']:4d} p={d['p']:2d} "
                  f"occ={d['occupancy']:.3f} nx={d['nx']:2d} "
                  f"spacing={d['spacing']:.6f} wall_gap={d['wall_gap']:+.4f}")

    def fam_of(k):
        for d, g in fam.items():
            if any(x["k"] == k for x in g):
                return d, g
        return None, []

    d_lo, g_lo = fam_of(8)
    d_hi, g_hi = fam_of(25)
    a_lo = set()
    a_hi = set()
    for g in g_lo:
        a_lo |= alphabet(g["words"])
    for g in g_hi:
        a_hi |= alphabet(g["words"])
    same = a_lo == a_hi
    print(f"\nalphabet of the delta {d_lo:+.9f} family (k = {g_lo[0]['k']}.."
          f"{g_lo[-1]['k']}): {sorted(a_lo)}")
    print(f"alphabet of the delta {d_hi:+.9f} family (k = {g_hi[0]['k']}.."
          f"{g_hi[-1]['k']}): {sorted(a_hi)}")
    verdict = ("SAME alphabet: the step is an ARRANGEMENT of the same words, "
               "not a new word" if same else
               "DIFFERENT alphabet: a new word appears above k = 25")
    print(f"VERDICT: {verdict}")

    fam_out = {f"{d:+.9f}": [g["k"] for g in grp]
               for d, grp in sorted(fam.items())}
    with open(OUT, "w") as f:
        json.dump({"run": 52, "schema": "r1-atoms/1", "rows": rows,
                   "families": fam_out, "fits": fits_by_delta,
                   "verdict": verdict}, f, indent=1)
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
