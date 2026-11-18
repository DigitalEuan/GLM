#!/usr/bin/env python3
"""bridge.py — the 2D optimal lattice as a layer of the 3D one, exactly.

THE QUESTION
------------
Is there a bridge from the 2D densest packing to the first lattice up, which is
reversible and loses nothing?  If so, what does it say?

THE ANSWER, IN ONE LINE
-----------------------
Yes, and it is exact: the densest plane lattice A2 is *literally a slice* of the
face-centred cubic lattice D3, the slice -> point map is a bijection with one
integer (the layer index), and that bijection is reversible and information-
preserving.  What it does **not** do is preserve density: the extra 3D gain comes
from the stacking offset, which is not a symmetry of the 2D lattice.

THE CONSTRUCTION
----------------
Everything below is integer arithmetic; no square root is ever formed.

* the **layer**  L = { v in Z^3 : v1 + v2 + v3 = 0 }.  Its shortest nonzero
  vectors are the six (1, -1, 0) permutations, so its minimal squared norm is 2,
  and a basis is (1,-1,0), (0,1,-1) with Gram determinant 3.  That is A2 scaled
  by sqrt(2): the densest plane lattice, with centre density
  delta^2 = (2/4)^2 / 3 = 1/12.
* the **lattice**  D3 = { v in Z^3 : v1 + v2 + v3 even }, the face-centred cubic
  lattice: minimal squared norm 2, Gram determinant 4, centre density
  delta^2 = (2/4)^3 / 4 = 1/32.
* the **bridge**  for v in D3 let s = v1+v2+v3 (even) and m = s/2.  Then
      phi(v)   = ( v - m*(1,1,0),  m )        in L x Z
      phi^-1(p, m) = p + m*(1,1,0)
  is a bijection: phi(v) has zero coordinate sum, and p + m*(1,1,0) has sum 2m,
  hence is in D3.  So  D3  ~=  L x Z  exactly, and the layer at height 2m is
  L + m*(1,1,0).  (The shift m*(1,1,0) is the stacking offset; reduced mod L it
  takes three values, which is the ABC stacking of close-packed layers.)
* the **same step repeats** along a coordinate axis:
      D_{n+1} -> D_n x Z,  v |-> (v' - (v_{n+1} mod 2) e_1,  v_{n+1}),
      (p, k) |-> p + (k mod 2) e_1 + k e_{n+1},
  so by composition  D_n ~= L x Z^{n-2}.

WHAT IT SAYS, AND WHAT IT REFUSES TO SAY
----------------------------------------
1. The 2D optimum is a layer of FCC -- but **which layer matters**.  Slicing D3
   by z = 0 gives D2, the *square* lattice (delta^2 = 1/16), not A2.  Slicing by
   v1+v2+v3 = const gives A2 (delta^2 = 1/12).  The two layers' densities differ
   by exactly 4/3 in the square, i.e. by 2/sqrt(3) in delta -- which *is* the 2D
   gain of the hexagonal packing over the square one.  So the choice of slice is
   the whole content: the same 3D lattice carries both the optimal 2D packing and
   the one it beats.
2. The bridge is lossless and reversible: every D3 point is a layer point plus
   one integer, and back, with no residue.  Informational loss: none.
3. The bridge is not an isometry and not a density map.  The layer thickness is
   2/sqrt(3) (the spacing between planes of constant sum), and
       (area of L)^2 * (thickness)^2 = 3 * 4/3 = 4 = det Gram(D3),
   so the 3D cell is exactly "one layer's worth of area times the stacking
   spacing" -- additive accounting, not a density multiplication.  The gain rises
   from 2/sqrt(3) to sqrt(2) because the offset m*(1,1,0) is added, and that
   offset is not in L (its sum is 2, not 0).
4. To 24 dimensions the same decomposition holds rung by rung for the laminated
   lattices (Lambda_{n+1} is two layers of Lambda_n, SPLAG ch. 6), so
   Lambda_24 ~= A2 x Z^22 as a set: 22 integers and two continuous coordinates
   address every Leech point.  That statement is *quoted* here, not verified --
   this script verifies the D-chain and the A2-in-D3 slice only, because those
   are the ones it can enumerate exactly.

Run:  python3 bridge.py            # the verdicts, one line each
      python3 bridge.py --selftest # the same, asserting instead of printing
"""

from fractions import Fraction
import itertools
import sys

F = Fraction


# --------------------------------------------------------------- exact models
def vecs(n, r):
    return itertools.product(range(-r, r + 1), repeat=n)


def in_L(v):
    """The (111) layer: integer points whose coordinates sum to zero."""
    return sum(v) == 0


def in_D(v):
    """D_n: integer points whose coordinates sum to an even number."""
    return sum(v) % 2 == 0


def min_shell(pred, n, r):
    """(least squared norm, number of vectors attaining it) in a box."""
    best, count = None, 0
    for v in vecs(n, r):
        if not any(v) or not pred(v):
            continue
        q = sum(c * c for c in v)
        if best is None or q < best:
            best, count = q, 1
        elif q == best:
            count += 1
    return best, count


def gram_det(basis):
    """Determinant of the Gram matrix, exactly (integer arithmetic)."""
    k = len(basis)
    g = [[sum(a * b for a, b in zip(basis[i], basis[j])) for j in range(k)]
         for i in range(k)]
    # integer determinant by fraction-free Gauss
    num = 1
    mat = [[F(x) for x in row] for row in g]
    for i in range(k):
        piv = next((r for r in range(i, k) if mat[r][i] != 0), None)
        if piv is None:
            return 0
        if piv != i:
            mat[i], mat[piv] = mat[piv], mat[i]
            num = -num
        num *= mat[i][i]
        inv = mat[i][i]
        for r in range(i + 1, k):
            f = mat[r][i] / inv
            for c in range(i, k):
                mat[r][c] -= f * mat[i][c]
    return int(num)


def delta2(mu, n, det):
    """Centre density squared from minimal norm, dimension and Gram determinant."""
    return F(mu, 4) ** n / F(det)


# ----------------------------------------------------------------- the bridges
def phi3(v):
    """D3 -> L x Z:  v = p + m*(1,1,0) with p in the layer."""
    s = sum(v)
    if s % 2:
        raise ValueError("not in D3")
    m = s // 2
    return (v[0] - m, v[1] - m, v[2]), m


def phi3_inv(p, m):
    if sum(p) != 0:
        raise ValueError("not in the layer")
    return (p[0] + m, p[1] + m, p[2])


def psi(v):
    """D_{n+1} -> D_n x Z along the last coordinate."""
    k = v[-1]
    b = k % 2
    head = list(v[:-1])
    head[0] -= b
    return tuple(head), k


def psi_inv(p, k):
    b = k % 2
    head = list(p)
    head[0] += b
    return tuple(head) + (k,)


# ---------------------------------------------------------------------- checks
def check_shells():
    out = {}
    out["L  (A2 layer)"] = min_shell(in_L, 3, 3)
    out["D2 (square)"] = min_shell(in_D, 2, 3)
    out["D3 (FCC)"] = min_shell(in_D, 3, 3)
    out["D4"] = min_shell(in_D, 4, 3)
    out["D5"] = min_shell(in_D, 5, 3)
    return out


def check_bijections(r=3):
    """phi and psi are bijections on a box, both ways, with no residue."""
    # phi: D3 <-> layer x Z
    seen = {}
    for v in vecs(3, r):
        if not in_D(v):
            continue
        p, m = phi3(v)
        assert (m, p) not in seen
        seen[(m, p)] = v
        assert phi3_inv(p, m) == v
        assert in_L(p) and in_D(phi3_inv(p, m))
    # every (layer point, height) in the box decodes into D3 and encodes back
    for p in vecs(3, r):
        if not in_L(p):
            continue
        for m in range(-r, r + 1):
            v = phi3_inv(p, m)
            assert in_D(v)
            assert phi3(v) == (p, m)
    n_phi = len(seen)

    # psi: D_{n+1} <-> D_n x Z, for n = 3, 4
    n_psi = {}
    for n in (3, 4):
        seen = {}
        for v in vecs(n + 1, r):
            if not in_D(v):
                continue
            p, k = psi(v)
            assert (k, p) not in seen
            seen[(k, p)] = v
            assert psi_inv(p, k) == v and in_D(p)
        for p in vecs(n, r):
            if not in_D(p):
                continue
            for k in range(-r, r + 1):
                v = psi_inv(p, k)
                assert in_D(v) and psi(v) == (p, k)
        n_psi[n] = len(seen)
    return n_phi, n_psi


def check_densities():
    gL = gram_det([(1, -1, 0), (0, 1, -1)])
    gD2 = gram_det([(1, 1), (1, -1)])
    gD3 = gram_det([(1, 1, 0), (1, 0, 1), (1, -1, 0)])
    gD4 = gram_det([(1, 1, 0, 0), (1, 0, 1, 0), (1, 0, 0, 1), (1, -1, 0, 0)])
    gD5 = gram_det([(1, 1, 0, 0, 0), (1, 0, 1, 0, 0), (1, 0, 0, 1, 0),
                    (1, 0, 0, 0, 1), (1, -1, 0, 0, 0)])
    return {
        "L": (gL, delta2(2, 2, gL)),
        "D2": (gD2, delta2(2, 2, gD2)),
        "D3": (gD3, delta2(2, 3, gD3)),
        "D4": (gD4, delta2(2, 4, gD4)),
        "D5": (gD5, delta2(2, 5, gD5)),
    }


def main() -> int:
    shells = check_shells()
    print("minimal shells (squared norm, count) -- exact enumeration")
    for k, (q, c) in shells.items():
        print(f"  {k:<16} {q}  x {c:4d}")
    print("  L's six shortest vectors are the hexagonal directions; D3/D4/D5 give")
    print("  kissing 12/24/40, the classical numbers.")

    n_phi, n_psi = check_bijections()
    print(f"\nbijections on a box: D3 <-> L x Z  ({n_phi} points, both ways);")
    for n, c in n_psi.items():
        print(f"  D{n+1} <-> D{n} x Z  ({c} points, both ways)")

    d = check_densities()
    print("\ncentre densities, squared (exact)")
    for k, (det, q) in d.items():
        print(f"  {k:<3} det Gram {det:2d}   delta^2 = {q}")
    ratio = d["L"][1] / d["D2"][1]
    print(f"\n  the (111) layer over the (001) layer: delta^2 ratio {ratio}"
          f" = 4/3, so delta ratio 2/sqrt(3) = the 2D gain")
    print(f"  the 2D (111) layer over the 3D lattice: delta^2 {d['L'][1]} vs "
          f"{d['D3'][1]}; the gain rises 2/sqrt(3) -> sqrt(2)")
    print("\n  cell accounting: area^2(L) * thickness^2 = "
          f"{d['L'][0]} * 4/3 = {d['L'][0] * F(4, 3)} = det Gram(D3) "
          f"{d['D3'][0]}")

    # the assertions, so the printed table cannot drift from the claims
    assert shells["L  (A2 layer)"] == (2, 6)
    assert shells["D2 (square)"] == (2, 4)
    assert shells["D3 (FCC)"] == (2, 12)
    assert shells["D4"] == (2, 24)
    assert shells["D5"] == (2, 40)
    assert d["L"][1] == F(1, 12) and d["D2"][1] == F(1, 16)
    assert d["D3"][1] == F(1, 32) and d["D4"][1] == F(1, 64)
    assert ratio == F(4, 3)
    assert d["L"][0] * F(4, 3) == d["D3"][0]
    assert d["D3"][0] == 4 and d["L"][0] == 3
    print("\nselftest OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
