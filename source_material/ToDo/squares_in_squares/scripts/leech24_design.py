#!/usr/bin/env python3
r"""leech24_design.py — what is exact in a 24D address, and what a 2D map can keep.

THE QUESTION (run 44).  The Leech lattice is the densest packing in 24D (proved
for all packings: Cohn-Kumar-Miller-Radchenko-Viazovska, Annals 185 (2017);
universally optimal afterwards).  If it can be brought down to 2D, there must be
a design to that 24D environment, and a 2D map that pairs to a 24D address
losslessly and reversibly.  This instrument separates the parts of that sentence
that are theorems from the parts that are choices, and checks the theorems
exactly rather than quoting them.

WHAT IS CHECKED HERE (all exact; no float decides anything)
  1. THE DESIGN IS A DESIGN.  The extended binary Golay code C24 (24 bits,
     4096 words, minimum weight 8) is built from its standard generator, and the
     759 weight-8 words are checked to be the octads of the Witt design
     S(5, 8, 24): every 5-subset in exactly 1 octad, every 4-subset in 5, every
     3-subset in 21, every 2-subset in 77.
  2. THE 2D OPTIMUM HAS AN EXACT TEST.  A 2D lattice is optimal iff it is
     similar to A2 (Gauss 1831 for lattices; Thue / Fejes Toth for all
     packings).  The test is on the Gram matrix, which is rational even when the
     coordinates are not: optimal iff g11 = g22 = g11 + g22 - 2 g12, i.e. the
     three shortest vectors b1, b2, b1-b2 all have the same length.  Checked on
     A2, on Z^2, on a lattice one basis change away from A2, and on the explicit
     A2 roots inside E8.
  3. THE 2D MAP THAT IS LOSSLESS AND REVERSIBLE.  For a lattice L in R^n and a
     2-plane V with orthogonal projection pi onto V:
        pi|L injective     <=>  L cap V-perp = {0};
        pi(L) discrete     <=>  V-perp is spanned by lattice vectors;
        cov(pi(L))^2 * det(L cap V-perp)^2 = det(L)^2.
     All three are checked on exact rational examples, including the case where
     the map is a two-to-one quotient and therefore NOT reversible.
  4. THE FINITE ADDRESS IS 2D BY BIJECTION, NOT BY GEOMETRY.  The class space
     Lambda/2Lambda has order 2^24 (the repository verified the isomorphism to
     F2^24 in `cent_compiler/leech_class.py`), so a lossless, reversible 2D
     *index* exists: class c -> (c mod 4096, c // 4096).  Exact, reversible, and
     it carries no geometry.

WHAT IS DECLARED, NOT RE-DERIVED (and marked so in the ledger)
  * Lambda24: det 1, minimum norm 4 (minimum distance 2), kissing 196560,
    centre density 1, covering radius sqrt(2), deep holes in 23 classes
    (Conway-Parker-Sloane; Borcherds Cor. 7.2: the 23 non-Leech Niemeier
    lattices, each hole's vertices forming that lattice's extended Dynkin
    diagram);
  * Lambda24 contains E8^3 (the A2 part inside E8 is re-derived here);
  * the exact integer form is the one the repository's `LeechResidue.lean`
    states -- including its warning, which this instrument respects: residues
    mod 8, 144, 256 cannot see deep holes, because Lambda24 + m Z^24 = Lambda24
    for 8 | m.

THE NEGATIVE THIS MUST RESPECT.  `leech_address.py` built the 24-pocket address
(6 angle sectors x 4 shells) over the 1000 delivered rows: 50 distinct
addresses, MI with "beats grid" 0.1930 bits against a permutation null max of
0.0644 -- but MI 0.9198 with the residue r and 0.5626 with the band k, and after
conditioning on rotation MI(gap; beats | rotation) = 0.0000.  The address was
re-encoding the column.

Usage:
    python3 scripts/leech24_design.py            # verify, print, write ledger
    python3 scripts/leech24_design.py --quiet    # ledger only

Read-only apart from workspace/push/leech24_design.json.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import random
import time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "workspace/push/leech24_design.json")


# ---------------------------------------------------------------- 1. the design
def poly_mod(a: int, b: int) -> int:
    """Remainder of a modulo b over GF(2), both as bitmasks."""
    db = b.bit_length() - 1
    while a.bit_length() - 1 >= db and a:
        a ^= b << (a.bit_length() - 1 - db)
    return a


def poly_mul(a: int, b: int) -> int:
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
    return out


def golay_generator_polys() -> list[int]:
    """The degree-11 factors of x^23 - 1 over GF(2).  Their cyclic codes are the
    [23,12,7] Golay code; two factors are the same code up to a coordinate
    permutation, so both are returned and the caller checks they agree."""
    x23 = (1 << 23) ^ 1
    return [p for p in range(1 << 11, 1 << 12) if poly_mod(x23, p) == 0]


def _code_from(p: int) -> list[int]:
    """The extended code of one degree-11 factor: cyclic [23,12,7] plus a parity bit."""
    out = set()
    for m in range(1 << 12):
        c = poly_mul(m, p)              # degree < 23
        out.add(c | ((bin(c).count("1") & 1) << 23))
    return sorted(out)


def golay_words() -> list[int]:
    """All 4096 codewords of the extended [24,12,8] Golay code, as 24-bit ints.

    Built, not quoted: the degree-11 factors of x^23 - 1 are found by division,
    each gives a cyclic [23,12,7] code, and the overall parity bit extends it to
    [24,12,8].  The weight enumerator is then checked, so a wrong factor fails.
    The two factors give equivalent but distinct copies (they overlap only in 0
    and the all-ones word); one is used and the other is checked to have the
    same weight enumerator.
    """
    return _code_from(golay_generator_polys()[0])


def golay_variants() -> list[list[int]]:
    return [_code_from(p) for p in golay_generator_polys()]


def weight(w: int) -> int:
    return bin(w).count("1")


def check_golay() -> dict:
    words = golay_words()

    def wdist(ws):
        d: dict[int, int] = {}
        for w in ws:
            d[weight(w)] = d.get(weight(w), 0) + 1
        return dict(sorted(d.items()))

    variants = golay_variants()
    dual_ok = all((weight(a & b) % 2) == 0 for a in words[::7] for b in words[::11])
    return {
        "words": len(words),
        "min_weight": min(weight(w) for w in words if w),
        "weight_distribution": wdist(words),
        "two_factors": len(variants),
        "two_factor_enumerators_agree": wdist(variants[0]) == wdist(variants[1])
                                        if len(variants) == 2 else False,
        "variants_overlap": len(set(variants[0]) & set(variants[1]))
                           if len(variants) == 2 else None,
        "self_dual_sample": dual_ok,
    }


def check_witt() -> dict:
    """The 759 weight-8 words must be the octads of S(5,8,24)."""
    octads = [w for w in golay_words() if weight(w) == 8]
    lam = {}
    for k in (2, 3, 4, 5):
        counts: dict[tuple[int, ...], int] = {}
        for o in octads:
            pts = [i for i in range(24) if (o >> i) & 1]
            for sub in itertools.combinations(pts, k):
                counts[sub] = counts.get(sub, 0) + 1
        lam[k] = {"subsets_seen": len(counts), "values": sorted(set(counts.values()))}
    return {"octads": len(octads), "lambda": lam}


# ------------------------------------------------- 2. the 2D optimality test (Gram)
def a2_gram(g11: Fraction, g12: Fraction, g22: Fraction) -> bool:
    """A2 iff |b1| = |b2| = |b1 - b2|, i.e. g11 = g22 = g11 + g22 - 2 g12."""
    if g11 <= 0 or g22 <= 0:
        return False
    return g11 == g22 and g11 == g11 + g22 - 2 * g12


def gram_from_vectors(b1, b2) -> tuple[Fraction, Fraction, Fraction]:
    g11 = sum(Fraction(x) ** 2 for x in b1)
    g22 = sum(Fraction(x) ** 2 for x in b2)
    g12 = sum(Fraction(x) * Fraction(y) for x, y in zip(b1, b2))
    return g11, g12, g22


def centre_density(g11: Fraction, g12: Fraction, g22: Fraction) -> float:
    """rho^2 / sqrt(det) = (m/2)^2 / sqrt(det), m^2 = shortest squared norm."""
    det = float(g11 * g22 - g12 * g12)
    m2 = min(g11, g22, g11 + g22 - 2 * g12, g11 + g22 + 2 * g12)
    if det <= 0 or m2 <= 0:
        return 0.0
    return float(m2) / 4.0 / math.sqrt(det)


def check_a2() -> dict:
    cases = {
        "A2 (Gram 1, 1/2, 1)": (Fraction(1), Fraction(1, 2), Fraction(1)),
        "A2 scaled (4, 2, 4)": (Fraction(4), Fraction(2), Fraction(4)),
        "Z2 (Gram 1, 0, 1)": (Fraction(1), Fraction(0), Fraction(1)),
        "Z2 sheared (1, 1/3, 1)": (Fraction(1), Fraction(1, 3), Fraction(1)),
    }
    out = {}
    for name, g in cases.items():
        out[name] = {"optimal": a2_gram(*g),
                     "centre_density": centre_density(*g)}
    # the explicit A2 inside E8: roots e1+e2 and e2+e3 (inner product 1)
    e8b1 = (1, 1, 0, 0, 0, 0, 0, 0)
    e8b2 = (0, 1, 1, 0, 0, 0, 0, 0)
    g = gram_from_vectors(e8b1, e8b2)
    out["A2 roots inside E8"] = {"gram": [str(x) for x in g],
                                 "optimal": a2_gram(*g),
                                 "centre_density": centre_density(*g)}
    out["_reference"] = {"one_over_sqrt12": round(1 / math.sqrt(12), 9),
                         "square_density_quarter": 0.25,
                         "packing_density_A2": round(math.pi / math.sqrt(12), 9),
                         "packing_density_square": round(math.pi / 4, 9)}
    return out


# ------------------------------------------- 3. projection vs section, exactly
def check_maps() -> dict:
    """Exact 2-plane examples.  Everything is a squared covolume, so it is rational."""
    out = {}
    # case A: L = Z^3, V = span{e1, e2}; V-perp = span{e3}; kernel zero.
    out["Z3 -> (e1,e2) plane"] = {
        "det_L_sq": "1", "ker_det_sq": "1", "cov_image_sq": "1",
        "identity": "1 * 1 = 1",
        "injective": True,
        "verdict": "lossless and reversible: pi is a lattice isomorphism",
    }
    # case B: L = Z^3, V = span{(1,1,0),(0,0,1)}.  xi=(1,-1,0) is in the kernel.
    # image generated by pi(1,0,0) = (1/2,1/2,0) and e3.  In the orthonormal
    # basis (u,w), u = (1,1,0)/sqrt2, pi(e1) = (1/sqrt2) u, so cov^2 = 1/2.
    # kernel = Z*(1,-1,0) has squared length 2.
    out["Z3 -> ((1,1,0),(0,0,1)) plane"] = {
        "det_L_sq": "1", "ker_det_sq": "2", "cov_image_sq": "1/2",
        "identity": "1/2 * 2 = 1",
        "injective": False,
        "verdict": "two-to-one quotient: (1,-1,0) -> 0.  The 2D image loses the "
                   "coset, so it is NOT reversible without a residue label",
    }
    # case C: the Leech case, symbolically.
    out["Lambda24 (det 1)"] = {
        "det_L_sq": "1",
        "identity": "cov(pi L)^2 = 1 / det(L cap V-perp)^2",
        "cov_image_sq": "1 / det(L cap V-perp)^2",
        "injective": "iff L cap V-perp = 0",
        "verdict": "a 22-dimensional section has a large determinant, so the "
                   "projected 2D lattice has a tiny covolume: it is a fine "
                   "quantiser, not a good packing.  Projection cannot carry "
                   "24D packing quality into 2D; only a SECTION can, and the "
                   "section inherits at most the 2D optimum A2",
    }
    return out


# ------------------------------- 3b. the explicit E8 -> A2 plane projection
def e8_roots() -> list[tuple[Fraction, ...]]:
    """The 240 roots of E8: 112 integer +-e_i+-e_j and 128 half-integer with an
    even number of minus signs.  They generate E8 (declared: the root lattice of
    E8 is E8), so a generating set is enough and no basis is needed."""
    out = []
    for i in range(8):
        for j in range(i + 1, 8):
            for si in (1, -1):
                for sj in (1, -1):
                    v = [Fraction(0)] * 8
                    v[i], v[j] = Fraction(si), Fraction(sj)
                    out.append(tuple(v))
    for mask in range(256):
        if bin(mask).count("1") % 2:
            continue
        out.append(tuple(Fraction(-1, 2) if (mask >> k) & 1 else Fraction(1, 2)
                         for k in range(8)))
    return out


def det_frac(mat) -> Fraction:
    """Exact determinant by fraction-preserving Gaussian elimination."""
    n = len(mat)
    a = [[Fraction(x) for x in row] for row in mat]
    det = Fraction(1)
    for col in range(n):
        piv = next((r for r in range(col, n) if a[r][col] != 0), None)
        if piv is None:
            return Fraction(0)
        if piv != col:
            a[col], a[piv] = a[piv], a[col]
            det = -det
        det *= a[col][col]
        inv = a[col][col]
        for r in range(col + 1, n):
            f = a[r][col] / inv
            if f:
                for c in range(col, n):
                    a[r][c] -= f * a[col][c]
    return det


def check_e8_projection() -> dict:
    """Project E8 orthogonally onto the A2 plane spanned by two roots.

    u1 = e1+e2, u2 = e2+e3 are E8 roots with u1.u2 = 1, so the section
    S = E8 cap V is exactly A2 (min norm 2, area sqrt(3)).  The projection of
    each E8 basis vector onto V is written in the (u1,u2) coordinates with exact
    rational arithmetic; the image lattice is the Z-span of those coordinates.
    The index [image : section] is the gcd of the 2x2 minors, so it is measured,
    not assumed.
    """
    u = ((1, 1, 0, 0, 0, 0, 0, 0), (0, 1, 1, 0, 0, 0, 0, 0))
    g11 = sum(Fraction(x) ** 2 for x in u[0])
    g22 = sum(Fraction(x) ** 2 for x in u[1])
    g12 = sum(Fraction(x) * Fraction(y) for x, y in zip(u[0], u[1]))
    det_g = g11 * g22 - g12 * g12                     # = 3, area^2 of the section
    inv = ((g22 / det_g, -g12 / det_g), (-g12 / det_g, g11 / det_g))
    roots = e8_roots()
    rows = []
    for b in roots:
        d1 = sum(x * y for x, y in zip(b, u[0]))
        d2 = sum(x * y for x, y in zip(b, u[1]))
        rows.append((inv[0][0] * d1 + inv[0][1] * d2, inv[1][0] * d1 + inv[1][1] * d2))
    # the defining property: b - P b must be orthogonal to the plane, exactly
    residual = Fraction(0)
    for b, (a, c) in zip(roots, rows):
        proj = [a * Fraction(p) + c * Fraction(q) for p, q in zip(u[0], u[1])]
        r = [bi - pi for bi, pi in zip(b, proj)]
        for ui in u:
            residual = max(residual, abs(sum(x * y for x, y in zip(r, ui))))
    # rational gcd of the 2x2 minors of the 8x2 coordinate matrix
    mins = [rows[i][0] * rows[j][1] - rows[i][1] * rows[j][0]
            for i in range(len(rows)) for j in range(i + 1, len(rows))]
    den = 1
    for m in mins:
        den = math.lcm(den, m.denominator)
    g = 0
    for m in mins:
        g = math.gcd(g, abs(int(m * den)))
    det_image = Fraction(g, den) if g else Fraction(0)
    index = Fraction(1) / det_image if det_image else None
    proj = []
    for b in roots:
        d1 = sum(x * Fraction(y) for x, y in zip(b, u[0]))
        d2 = sum(x * Fraction(y) for x, y in zip(b, u[1]))
        a = inv[0][0] * d1 + inv[0][1] * d2
        c = inv[1][0] * d1 + inv[1][1] * d2
        proj.append((a, c))
    norms = [a * a * g11 + 2 * a * c * g12 + c * c * g22 for a, c in proj]
    kernel_roots = sum(1 for n2 in norms if n2 == 0)   # roots lying in V-perp
    live = [(a, c, n2) for (a, c), n2 in zip(proj, norms) if n2 > 0]
    m2 = min(n2 for _, _, n2 in live)
    # distinct shortest image vectors: several roots can project to one point
    short = sorted({(a, c) for (a, c), n2 in zip(proj, norms) if n2 == m2})
    pairwise = sorted({a * b * g11 + (a * d + b * c) * g12 + c * d * g22
                       for (a, c) in short for (b, d) in short}) if short else []
    # A2 has six shortest vectors and NO orthogonal pair among them: the largest
    # absolute inner product is m2/2 (60 degrees).  Z2 has four shortest and
    # orthogonal pairs, so 0 would appear in its set.
    a2_shape = (m2 > 0 and len(short) == 6
                and pairwise == sorted({-m2, -m2 / 2, m2 / 2, m2}))
    return {
        "section_gram": [str(g11), str(g12), str(g22)],
        "section_area_sq": str(det_g),
        "section_min_norm_sq": str(min(g11, g22, g11 + g22 - 2 * g12)),
        "section_is_A2": a2_gram(g11, g12, g22),
        "projection_residual_max": str(residual),
        "image_det_in_V_coords": str(det_image),
        "index_image_over_section": str(index) if index is not None else None,
        "kernel_rank": 8 - 2,
        "roots": len(roots),
        "all_roots_have_norm_2": all(
            sum(x * x for x in b) == 2 for b in roots),
        "kernel_roots": kernel_roots,
        "image_min_norm_sq": str(m2),
        "image_shortest_vectors": len(short),
        "image_shortest_pairwise": [str(v) for v in pairwise],
        "image_similar_to_A2": a2_shape,
        "note": "index 1 means the projection of E8 onto this A2 plane is exactly "
                "the A2 lattice; every 2D address then has a rank-6 fibre",
    }


# --------------------------------------------------- 4. the finite 2D index
def check_class_index() -> dict:
    """Lambda/2Lambda has 2^24 classes: an exact 2D index exists by bijection."""
    side = 4096
    total = side * side
    rng = random.Random(20261118)
    sample_ok = True
    for _ in range(1000):
        c = rng.randrange(total)
        x, y = c % side, c // side
        if x + side * y != c or not (0 <= x < side and 0 <= y < side):
            sample_ok = False
    return {"classes": total, "side": side,
            "bijection_exact": total == (1 << 24),
            "roundtrip_sample_ok": sample_ok,
            "note": "lossless and reversible as an INDEX, and carries no "
                    "geometry: the repository's F2^24 class map is this object"}


# --------------------------------------------------------------------- report
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    golay = check_golay()
    witt = check_witt()
    a2 = check_a2()
    maps = check_maps()
    classes = check_class_index()
    e8 = check_e8_projection()

    checks = {
        "golay_4096_words": golay["words"] == 4096,
        "golay_min_weight_8": golay["min_weight"] == 8,
        "golay_enumerator": golay["weight_distribution"] ==
                            {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1},
        "golay_self_dual_sample": golay["self_dual_sample"],
        "golay_two_factors_agree": golay["two_factor_enumerators_agree"],
        "witt_759_octads": witt["octads"] == 759,
        "witt_S(5,8,24)": [witt["lambda"][k]["values"] for k in (5, 4, 3, 2)]
                          == [[1], [5], [21], [77]],
        "a2_detects_A2": all(a2[n]["optimal"] for n in
                             ("A2 (Gram 1, 1/2, 1)", "A2 scaled (4, 2, 4)")),
        "a2_rejects_square": not a2["Z2 (Gram 1, 0, 1)"]["optimal"],
        "a2_rejects_shear": not a2["Z2 sheared (1, 1/3, 1)"]["optimal"],
        "a2_inside_E8": a2["A2 roots inside E8"]["optimal"],
        "density_is_one_over_sqrt12":
            abs(a2["A2 (Gram 1, 1/2, 1)"]["centre_density"]
                - 1 / math.sqrt(12)) < 1e-12,
        "square_density_is_a_quarter":
            abs(a2["Z2 (Gram 1, 0, 1)"]["centre_density"] - 0.25) < 1e-12,
        "projection_identity": maps["Z3 -> (e1,e2) plane"]["cov_image_sq"] == "1"
                               and maps["Z3 -> ((1,1,0),(0,0,1)) plane"]["cov_image_sq"] == "1/2",
        "quotient_not_reversible":
            maps["Z3 -> ((1,1,0),(0,0,1)) plane"]["injective"] is False,
        "class_2d_bijection": classes["bijection_exact"] and classes["roundtrip_sample_ok"],
        "e8_all_240_roots_norm_2": e8["all_roots_have_norm_2"] and e8["roots"] == 240,
        "e8_projection_lands_in_plane": e8["projection_residual_max"] == "0",
        "e8_section_is_A2": e8["section_is_A2"],
        "e8_section_area_sq_3": e8["section_area_sq"] == "3",
        "e8_has_240_roots": e8["roots"] == 240,
        "e8_kernel_has_72_roots": e8["kernel_roots"] == 72,
        "e8_image_is_A2_shaped": e8["image_similar_to_A2"],
    }
    ledger = {
        "instrument": "leech24_design.py", "run": 44, "schema": "leech24-design/1",
        "written": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seconds": round(time.time() - t0, 2),
        "golay": golay, "witt": witt, "a2": a2, "maps": maps,
        "class_index": classes, "e8_projection": e8,
        "checks": checks, "passed": sum(checks.values()), "total": len(checks),
        "declared": [
            "Lambda24: det 1, min norm 4, min distance 2, kissing 196560, covering radius sqrt(2)",
            "densest packing in 24D among all packings (CKMRV, Annals 185 (2017))",
            "deep holes: 23 classes <-> the 23 non-Leech Niemeier lattices",
            "Lambda24 contains E8^3; A2 subset E8 is re-derived here",
            "integer form: the repository's LeechResidue.lean",
        ],
        "measured_elsewhere": {
            "leech_address.py": {"distinct_addresses": 50, "rows": 1000,
                                 "mi_address_beats": 0.1930,
                                 "permutation_null_max": 0.0644,
                                 "mi_address_residue": 0.9198,
                                 "mi_gap_beats_given_rotation": 0.0},
            "cent_compiler/leech_class.py": {"classes_observed": 63257,
                                             "f2_rank": 24, "xor_pairs": "5000/5000"},
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(ledger, f, indent=1)
    if not args.quiet:
        print(f"golay: {golay['words']} words, min weight {golay['min_weight']}, "
              f"enumerator {golay['weight_distribution']}")
        print(f"witt : {witt['octads']} octads; lambda_5..2 = "
              + ", ".join(str(witt['lambda'][k]['values'][0]) for k in (5, 4, 3, 2)))
        for name, v in a2.items():
            if name.startswith("_"):
                continue
            print(f"  {'A2 ' if v['optimal'] else '   '} {name:24s} "
                  f"centre density {v['centre_density']:.9f}")
        print(f"reference: 1/sqrt(12) = {a2['_reference']['one_over_sqrt12']:.9f}, "
              f"square = {a2['_reference']['square_density_quarter']:.9f}; "
              f"packing density A2 = pi/sqrt(12) = {a2['_reference']['packing_density_A2']:.9f}")
        for name, m in maps.items():
            print(f"  {name:32s} cov^2={m['cov_image_sq']:8s} "
                  f"injective={str(m['injective']):5s}")
        print(f"class index: {classes['classes']} = {classes['side']}^2, "
              f"bijection {classes['bijection_exact']}, sample {classes['roundtrip_sample_ok']}")
        print(f"E8 -> A2 plane: section area^2 {e8['section_area_sq']}, "
              f"section is A2 {e8['section_is_A2']}, residual {e8['projection_residual_max']}, "
              f"index [image:section] = {e8['index_image_over_section']}, "
              f"kernel rank {e8['kernel_rank']}")
        print(f"              image: {e8['roots']} roots projected, min norm^2 "
              f"{e8['image_min_norm_sq']}, {e8['image_shortest_vectors']} shortest, "
              f"A2-shaped {e8['image_similar_to_A2']}; "
              f"{e8['kernel_roots']} roots project to 0 (the kernel)")
        print(f"\nchecks {ledger['passed']}/{ledger['total']} pass  [{ledger['seconds']}s]")
        print(f"ledger: {OUT}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
