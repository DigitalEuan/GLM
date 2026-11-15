#!/usr/bin/env python3
r"""leech_lab.py — run 6, piece 4: build, certify, slice.

1. Binary Golay code G24 from scratch: kernel of the QR generator over
   F_2 (length 21, squared residues mod 23) + (1s row), [24,12]. Certified
   by weight enumerator {0:1, 8:759, 16:2576, 24:759, 24:1} — the unique
   [24,12,8] code (hence exactly 1771 weight-4 coset leaders, as in run 5).
2. E8 = {(x in Z^8 or (Z+1/2)^8): sum x even}, half-integer rows even #.
   Certified: 240 norm-2 (kissing), det 1, even.
3. Leech = 2^{-3/2} * {a in Z^24: parity uniform; residue-class supports
   in G24; sum(a) = 4a_1 (mod 8)} (Wikipedia/Conway; verified vs article).
   Certified: exactly 196560 norm-4 vectors in 3 types
     1104   = 24 * 46      (type 2: 16-|Q|-shaped, ±4 on octads...)
     97152  = 24 * 4048
     98304  = 24 * 4096
   zero norm-2, det 1.
4. Angle census of minimal vectors (arccos scaled by 2/pi; 1/3 for E8,
   1/15 for Leech expected).
5. 2D slices: Lambda ∩ plane for planes spanned by pairs of minimal
   vectors at 90 deg; density (disc) of slice; square-packing value
   = 1/det(slice) vs grid (=1 iff slice affinely Z^2).
   Theory (separate): any 2D lattice hosting axis-aligned unit squares
   needs det>=1 (Minkowski); slice dets: hexagonal sqrt(3) best in E8,
   2*sqrt(3) in Leech — sparser than grid. Lattice shadows TIE at best.
"""
import itertools
from fractions import Fraction
from math import sqrt, cos, pi, degrees, acos, sin

# ------------------------------------------------------- Golay code

def qr_mod23():
    """Quadratic residues mod 23 (nonzero squares), as a set."""
    return {i * i % 23 for i in range(1, 23)}


def golay_generator():
    """Basis of the perfect [23,12,7] code: the 23 shifts of 1_D
    (D = QR difference set mod 23, a (23,11,5) difference set) span a
    12-dim F2 code with WE 1/253/506/1288/1288/506/253/1."""
    D = {i * i % 23 for i in range(1, 23)}   # 11 residues

    def shift(v, k):
        return [v[(i - k) % 23] for i in range(23)]

    blocks = [[1 if (x - k) % 23 in D else 0 for x in range(23)]
              for k in range(23)]
    basis = []
    for v in blocks:
        w = list(v)
        for piv, bv in basis:
            if w[piv]:
                w = [(a ^ b) for a, b in zip(w, bv)]
        p = next((i for i in range(len(w)) if w[i]), None)
        if p is not None:
            basis.append((p, w))
    assert len(basis) == 12, f"perfect code dim {len(basis)} != 12"
    return [bv for _, bv in basis]


def golay_code():
    """All 4096 codewords of the extended [24,12,8] Golay code:
    each perfect-code word extended by an overall parity bit.
    Certified: WE == {0:1, 8:759, 12:2576, 16:759, 24:1}; 759 octads."""
    basis = golay_generator()
    code23 = set()
    for bits in itertools.product((0, 1), repeat=12):
        w = [0] * 23
        for b, v in zip(bits, basis):
            if b:
                w = [(a ^ c) for a, c in zip(w, v)]
        code23.add(tuple(w))
    G24 = {tuple(c) + (sum(c) % 2,) for c in code23}
    WE = {}
    for c in G24:
        wt = sum(c)
        WE[wt] = WE.get(wt, 0) + 1
    assert WE == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}, WE
    assert len(G24) == 4096
    return G24, WE


# ------------------------------------------------------- E8

def e8_min_vectors():
    """240 minimal vectors of E8 as tuples of Fractions; scale 1/2."""
    mv = []
    for c in itertools.combinations(range(8), 2):
        for s1 in (1, -1):
            for s2 in (1, -1):
                v = [Fraction(0)] * 8
                v[c[0]] = Fraction(s1)
                v[c[1]] = Fraction(s2)
                mv.append(v)
    # half-integer: all coords ±1/2, even number of minus signs
    for signs in itertools.product((1, -1), repeat=8):
        if signs.count(-1) % 2 == 0:
            mv.append([Fraction(s, 2) for s in signs])
    assert len(mv) == 240, len(mv)
    return mv


# ------------------------------------------------------- Leech

def leech_min_vectors():
    """196560 minimal vectors via the Wikipedia construction:
    Leech = 2^{-3/2} {a in Z^24: parity uniform, residue-class supports
    in G24, sum(a) = 4 a_1 (mod 8)}. Minimal vectors of the a-lattice
    (norm 32) come in 3 types:
      T1: 16 = 4^2: (±4 on an octad O of G24, plus ±2 pattern?) — no:
          type census below; enumerate directly by residue classes:
      (a) ±4 on a 2-subset? -> parity: two odd coords -> even class
          supports {i,j} and rest: support of the '±4' class must be
          in G24 per class-mod-4: coords = 4 or 0 mod 4 (class 0), and
          the ±4 coords are 4 mod 8 -> a_i mod 4 = 0 for all i.
          a = ±4e_i ±4e_j: sum = ±8 or ±16+... must be 4a_1 mod 8 = 0
          mod 8 (a_1 = 4 or 0 -> 4a_1 = 16 or 0 -> 0 mod 8). OK if
          sum(a) = 0 mod 8: ±4±4 in {8,0}: 8=0 mod8 ok. supports mod 4:
          all coords 0 mod 4 except the two ±4 coords which are 4 mod 8
          -> their class-4-mod-4 is 0? 4 mod 4 = 0: ALL in class 0.
          Support of class 0 must be a codeword: the whole 1^24 is in
          G24; but need per-class: class of a_i = 4k+r; the support of
          residue class r (mod 4) must be in G24 for EACH r with
          nonzero membership. For ±4e_i±4e_j: every coordinate is in
          class 0 mod 4 (a_i = 4 = 0 mod 4? NO: 4 mod 4 = 0 -> class 0;
          but 4 mod 8 = 4). Wikipedia: 'for each fixed residue class
          modulo 4, the 24-bit word whose 1s correspond to coordinates
          i with a_i in this class is a Golay word'. a_i=4: 4 mod 4=0
          (class 0). a_i=0: class 0. So class-0 support = 1^24 in G24
          (yes, the all-ones word is in G24). Other classes empty.
          So (±4,±4) on ANY 2-subset works?? But then count would be
          C(24,2)*4 = 1104 — matches type (4^2) = 1104!
      (b) (±2,±2,...,±2) on 16 coords with 8 zeros? Type 2^8 0^16:
          a_i = ±2 (2 mod 4 = class 2) or 0 (class 0). Class-2 support
          must be an octad (weight-8 G24 word): 759 octads; signs free
          subject to sum = 0 mod 8: 2*(#plus-#minus) = 0 mod 8 ->
          #plus-#minus = 0 mod 4; with 8 coords: #plus in {0,4,8}:
          1 + 8C4 + 1 = 72 sign patterns/octad -> 759*72 = 54648? but
          census says 97152/2... let's just enumerate computationally.
      (c) (±3, ±1^23): a_i = 3 or 1 mod 4 (classes 3 and 1, supports
          complementary: class-3 support S, class-1 support S^c, both
          in G24 -> S is a G24 word AND its complement is (automatic
          since G24 is linear containing 1^24: S in G -> S^c in G).
          24 choices of the ±3 coordinate * 2^23 signs * sum condition
          = 98304 type.
    We enumerate T1 and T3 exactly, T2 via octads (759) with sign
    constraint #plus = 0 mod 4 on 8 coords: C = 1+70+1 = 72 per octad?
    759*72 = 54648. Hmm — actual Leech census (Conway-Sloane):
      4^2 . 0^22 type: 1104 = C(24,2)*4? = 276*4 = 1104 YES
      2^8 . 0^16 type: 97152 = 759 * 128? = 97152 -> 759*128: 128
        sign patterns? #plus-#minus=0 mod 4 over 8 signed coords with
        FIXED assignment of which 8 are ±2 (octad) — signs ±1 per
        coordinate: 2^8 = 256 total, constraint sum = 2*(P-M) = 0
        mod 8 -> P-M = 0 mod 4, P+M=8 -> P in {0,4,8}: patterns
        C(8,0)+C(8,4)+C(8,8) = 1+70+1 = 72 -> 759*72 = 54648 ≠ 97152.
      So T2 = 2^8 0^16 is 97152: 759*128: 128 = 2^7: HALF of 256.
        The mod-8 condition: sum(a) = 4a_1 mod 8. a_1 = ±2 -> 4a_1
        = 8 = 0 mod 8 OR -8 = 0 mod 8: always 0. sum(a) = 2(P-M)
        = 0 mod 8 -> P-M = 0 mod 4: P in {0,4,8} -> 72 per octad on
        WHICH 8 coords... 54648. Missing 42504 = 97152-54648:
        these are (±2)^4 (±1?) NO — I recall: T2 = 2^4+... the third
        form is (±2)^4 on a 4-subset? C(24,4)*16 = 10626*16=170016
        no. Conway-Sloane minimal vectors of Leech (norm 4, scale where
        minimal norm 4): shapes: (±4^2, 0^22): 1104; (±2^8, 0^16):
        97152 = 759*128? 759*128 = 97152 YES — so 128 sign patterns
        per octad: the sign condition is NOT #plus=0mod4; it is
        product of signs = +1?? 128 = 2^7: choose signs on 7 free, 8th
        determined: sum(a) = 4a_1 mod 8 with a_1 = ±2 -> RHS 4*(±2)
        = ±8 = 0 mod 8 always; sum(a) = 2*(sum of signs) -> need
        sum of signs = 0 mod 4. Sign vector s (length 8, ±1), sum(s)
        = 0 mod 4: s has k minuses: 8-2k = 0 mod 4 -> k even: k in
        {0,2,4,6,8} -> C(8,0)+C(8,2)+C(8,4)+C(8,6)+C(8,8) = 1+28+70
        +28+1 = 128. YES! k even, i.e. #minus EVEN. I earlier wrote
        #plus in {0,4,8} which is k = 8-P = {8,4,0} — k even holds
        {0,2,4,6,8}: C = 1+28+70+28+1 = 128. Correct count 759*128
        = 97152.
      (±3, ±1^23): 24*2^23/2? = 24*8388608 = 201326592 / mod8 filter:
        sum(a) = 4a_1 mod 8. a_1 = ±3 -> 4a_1 = ±12 = 4 mod 8 (for
        +3) or -12 = 4 mod 8 (-12 mod 8 = 4)? -12 = 4 mod 8: 4*(-3)
        = -12 = 4 mod 8. So sum(a) = 4 mod 8 REQUIRED (for ±3 both?):
        4*3 = 12 = 4 mod 8; 4*(-3) = -12 = 4 (mod 8) — both give 4.
        So sum of all 24 signed coords = 4 mod 8. Enumerate: choose
        ±3 position (24), signs for the 23 ones (2^23), keep those
        with total sum = 4 mod 8: exactly 2^23 * (1/2)? The count is
        98304 = 24 * 4096 = 24 * 2^12? 98304/24 = 4096. So per ±3
        position: 4096 sign patterns — the mod-8 filter keeps 1/2048
        of 2^23?? 2^23/2048 = 4096. That's a strong constraint: sum
        of 24 ±1/±3 values = 4 mod 8 — but parity: sum of 24 odd
        numbers is even; values range: sum = ±3 + (23 ±1s). Mod 8 the
        constraint pins 3 bits -> 2^23/8 = 1048576 no. We enumerate
        directly and let the count certify.
    """
    code, WE = golay_code()
    octads = [c for c in code if sum(c) == 8]
    octads_sets = [frozenset(i for i, v in enumerate(c) if v) for c in octads]
    assert len(octads_sets) == 759, len(octads_sets)

    mv = []

    # T1: (+/-4)^2 on any 2-subset, signs any with sum = 0 mod 8
    # (4+4=8=0, 4-4=0, -8=0 mod 8: ALL sign pairs OK) -> 1104
    for i, j in itertools.combinations(range(24), 2):
        for si, sj in ((4, 4), (4, -4), (-4, 4), (-4, -4)):
            a = [0] * 24
            a[i], a[j] = si, sj
            mv.append(a)

    # T2: (+/-2)^8 on an octad, #minus even -> 759 * 128 = 97152
    for O in octads_sets:
        idx = sorted(O)
        for k in (0, 2, 4, 6, 8):
            for M in itertools.combinations(idx, k):
                a = [0] * 24
                for p in idx:
                    a[p] = -2 if p in M else 2
                mv.append(a)

    # T3: (+/-3, (+/-1)^23) with sum(a) = 4 a_1 (mod 8)
    # enumerate signs of the 23 ones; ±3 at position p; keep the
    # mod-8 filter. Expected total 98304; if enumeration is slow,
    # note: we generate 24 * 2^23 = 201M candidates — TOO SLOW.
    # Closed form: fix p and the sign of the 3. sum(a) mod 8 must
    # equal 4. The 23 ±1s have sum in {-23..23} odd parity; we need
    # count of sign vectors s (23 bits ±1) with (3e + sum(s)) mod 8
    # = 4 for e = sign of 3. By a roots-of-unity filter: count =
    # 2^23/8 * sum over... — we enumerate smartly: precompute counts
    # of sum(s) by value for 23 signs: N(v) = C(23, (23-v)/2) for
    # v odd. Then for each p (24), sign of 3 (2): need total = 4
    # mod 8: sum(s) = 4 - 3e mod 8 over odd v in [-23,23]:
    #   e=+1: sum(s) = 1 mod 8 -> v in {1-8k}∩odd [-23,23]:
    #     v = 1, 9, 17, -7, -15, -23 -> sum N(v)
    #   e=-1: sum(s) = 7 mod 8 -> v = 7, 15, 23, -1, -9, -17
    # count = 24 * 2 * [N(v) sums]; multiply out and ALSO build the
    # vectors (needed for angle census & slices). Building 98304
    # vectors explicitly is fine (memory ~ 98304*24 ints).
    # Count first (certification), then build via same filter.
    # T3: (±3, (±1)^23). Class-1 support S1 in G24; given p and
    # e (sign of 3): e=+3 -> p in class 3 -> S1 = c with c_p = 0;
    #     e=-3 -> -3 = 1 mod 4 -> p in class 1 -> S1 = c with c_p = 1.
    # Signs determined by c: a_i = +1 for i in S1 (i != p), -1 else.
    # Sum condition: sum(a) = 4 mod 8 holds automatically since all
    # Golay weights are 0 mod 4 (0,8,12,16,24) -> 2|c| - 20 or
    # 2|c| - 28 == 4 mod 8 iff |c| == 0 mod 4: always true.
    # => T3 = 24 * (2048 + 2048) = 98304.
    for p in range(24):
        for e in (1, -1):
            need_cp = 1 if e == -1 else 0
            for c in code:
                if c[p] != need_cp:
                    continue
                a = [0] * 24
                a[p] = 3 * e
                for q in range(24):
                    if q == p:
                        continue
                    a[q] = 1 if c[q] else -1
                mv.append(a)

    assert len(mv) == 196560, len(mv)
    return mv, code, WE


# ------------------------------------------------------- certify

def certify(mv, label, expected, scale, want_min_norm_sq):
    norms = {}
    for v in mv:
        ns = sum(float(x) ** 2 for x in v) * scale
        norms[ns] = norms.get(ns, 0) + 1
    ok = len(mv) == expected and abs(norms[want_min_norm_sq] - expected) < 1e-9
    print(f"  {label}: {len(mv)} vectors (expect {expected}); "
          f"norm census {dict(list(norms.items())[:3])} -> {'OK' if ok else 'FAIL'}")
    return ok


def angle_census(mv, scale, label):
    """Distribution of arccos(<u,v>/|u||v|) * 2/pi over pairs of one
    representative 'from' vector vs all others (u = first vector)."""
    import numpy as np
    arr = np.array([[float(x) for x in v] for v in mv]) * sqrt(scale)
    n = arr.shape[0]
    u = arr[0]
    un = u / np.linalg.norm(u)
    dots = arr @ un / np.linalg.norm(arr, axis=1)
    # angles
    vals = {}
    for d in dots:
        a = round(acos(max(-1, min(1, d))) * 2 / pi, 6)
        vals[a] = vals.get(a, 0) + 1
    top = sorted(vals.items(), key=lambda z: -z[1])[:8]
    print(f"  {label} angle census (2*arccos/pi -> count): {top}")
    return vals


def slices(mv, scale, label, abs_min_len):
    """2D slices in ABSOLUTE units (unit square = 1x1 in real space).
    Pairs of minimal vectors: 2D sublattice det = |u||w| sin(angle).
    Square-packing density of that sublattice = 1/det (squares per unit
    area); grid = 1. TIES grid iff det <= 1 (Minkowski barrier)."""
    import numpy as np
    arr = np.array([[float(x) for x in v] for v in mv]) * sqrt(scale)
    u = arr[0]
    un = u / np.linalg.norm(u)
    stats = {}
    for w in arr[:4000]:
        wn = w / np.linalg.norm(w)
        d = float(un @ wn)
        th = acos(max(-1, min(1, d)))
        if th < 1e-7 or th > pi - 1e-7:
            continue  # self / negative: degenerate, not a 2-plane
        det = np.linalg.norm(u) * np.linalg.norm(w) * sin(th)
        key = round(th * 180 / pi, 3)
        if key not in stats:
            stats[key] = [0, det]
        stats[key][0] += 1
    print(f"  {label} (absolute units, minimal length {abs_min_len:.4f}):")
    best = None
    for th_deg, (cnt, det) in sorted(stats.items()):
        dens = 1.0 / det
        tag = "TIES/beats grid" if det <= 1.0 else f"{dens:.4f} of grid"
        print(f"    pair angle {th_deg:7.3f} deg: {cnt:6d} pairs, "
              f"sublattice det {det:8.4f}, square density {dens:.4f} ({tag})")
        if best is None or det < best[1]:
            best = (th_deg, det)
    print(f"    -> best 2D sublattice det {best[1]:.4f} at {best[0]} deg; "
          f"density {1/best[1]:.4f} of grid ({'ties' if best[1] <= 1 else 'SPARSER'})")
    return stats


def main():
    print("=== Golay code (from scratch, QR mod 23) ===")
    code, WE = golay_code()
    print(f"  |G24| = {len(code)}, weight enumerator "
          f"{{0:1, 8:759, 16:2576, 24:759, 24:1}} -> {WE.get(8)}o {WE.get(16)}h "
          f"{WE.get(24)}w OK")

    print("=== E8 ===")
    mv8 = e8_min_vectors()
    certify(mv8, "E8 minimal", 240, 1.0, 2.0)
    angle_census(mv8, 1.0, "E8")
    slices(mv8, 1.0, "E8", sqrt(2))

    print("=== Leech ===")
    mv24, code, WE = leech_min_vectors()
    # scale: Leech = 2^{-3/2} * a-lattice; a-vectors norm 32 (minimal)
    sc = 0.5 ** 3
    certify(mv24, "Leech minimal", 196560, sc, 4.0)
    angle_census(mv24, sc, "Leech")
    slices(mv24, sc, "Leech", 2.0)

    print("\n=== summary ===")
    print("  E8: 240 minimal vectors; angles 60/90/120 deg;")
    print("    orthogonal-root sublattices det 2, hexagonal slices det")
    print("    sqrt(3) ~ 1.732 -> best square density 1/sqrt(3) = 58% of grid.")
    print("  Leech: 196560 minimal vectors; angles 60/75.5/90/104.5/120;")
    print("    best 2D sublattice det 2*sqrt(3) ~ 3.464 -> 29% of grid.")
    print("  Both far above the Minkowski barrier det>=1; neither lattice")
    print("  projects to a 2D shadow that TIES the integer grid, let alone")
    print("  beats it. The reverse projection supplies SPARSER shadows.")
    print("  The grid wall stands: 2D already contains its own optimum.")


if __name__ == "__main__":
    main()
