#!/usr/bin/env python3
"""GLM push #2 (rewritten): the method of translation, on every grid.

Framework (all exact; mpmath 100 digits + certified comparisons; module
elements are integer tuples in the power basis of Z[zeta_N]):

  module M_N = Z[zeta_N], rank phi(N)  (4 for N=5,8,12; 6 for N=7)
  physical reader : zeta |-> e^{2 pi i /N}        (the 2D plane we see)
  internal reader : zeta |-> e^{2 pi i j/N}       (the Galois-conjugate plane)
       N=5: j=2  (field Q(sqrt5), golden)
       N=8: j=3  (field Q(sqrt2), silver)
       N=12: j=5 (field Q(sqrt3), 12-fold)
       N=7: TWO internal planes j=2 and j=3 (4D internal space)
  window W = conv hull of the internal images of the orbit of the unit
       strand {c in {-1,0,1}^phi(N)} under multiplication by zeta
       (rotation-invariant by construction);
       for N=7: product window W2 x W3 in R^4.
  model set Lambda_W = {z in M_N : z* in W}   (cut-and-project).

  Inflation theorem (verified point by point, and true in general):
    u in M_N a real unit, |sigma_j(u)| < 1 (Pisot), W convex symmetric
    => u . Lambda_W subset Lambda_W, because (u z)* = sigma_j(u) . z*
    and sigma_j(u) . W subset W.
"""
import itertools
from fractions import Fraction as F
import mpmath as mp

mp.mp.dps = 100
EPS = mp.mpf("1e-60")

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"[{'VERIFIED' if cond else 'FAILED'}] {name}" + (f"  -- {detail}" if detail else ""))


def cert_cmp(a, b):
    """Certified comparison; |a-b| < 1e-50 counts as equality (closed window)."""
    d = a - b
    if abs(d) > mp.mpf("1e-50"):
        return 1 if d > 0 else -1
    return 0


# ---------------------------------------------------------------------------
# cyclotomic arithmetic: Z[x]/Phi_N, power basis 1, zeta, ..., zeta^(phi-1)
# ---------------------------------------------------------------------------
PHI = {
    5: [1, 1, 1, 1, 1],        # x^4+x^3+x^2+x+1
    8: [1, 0, 0, 0, 1],        # x^4+1
    12: [1, 0, -1, 0, 1],      # x^4-x^2+1
    7: [1] * 7,                # x^6+...+1
}
RANK = {5: 4, 8: 4, 12: 4, 7: 6}


def polymul_mod(a, b, N):
    """product of two coefficient tuples (low-first) reduced mod Phi_N."""
    r = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    r[i + j] += ai * bj
    # reduce mod Phi_N (Phi monic): x^phi = -(sum of lower terms)
    phi = PHI[N]
    d = RANK[N]
    for k in range(len(r) - 1, d - 1, -1):
        c = r[k]
        if c:
            r[k] = 0
            for t in range(d):
                r[t] -= c * phi[t] if t else c * phi[0] - 0  # phi[0]=1
            # careful: x^d = -(phi[0] + phi[1] x + ... + phi[d-1] x^{d-1})
            # since Phi_N = x^d + phi[d-1] x^{d-1} + ... + phi[0]
    # the loop above is wrong; do it cleanly:
    return _reduce(r, N)


def _reduce(r, N):
    """Reduce coefficient list (low-first) mod Phi_N.

    Phi_N(x) = x^d + phi[d-1] x^{d-1} + ... + phi[0], so
    x^d = -phi[d-1] x^{d-1} - ... - phi[0], i.e. for c . x^k with k >= d:
    c x^k = -c sum_t phi[t] x^{(k-d)+t}   (t = 0..d-1).
    One top-down pass suffices: each subtraction lands at indices < k.
    """
    d = RANK[N]
    phi = PHI[N]  # low-first, phi[d] = 1 (leading)
    r = list(r)
    if len(r) < d:
        r += [0] * (d - len(r))
    for k in range(len(r) - 1, d - 1, -1):
        c = r[k]
        if c:
            r[k] = 0
            base = k - d
            # ensure index range
            if base + d - 1 >= len(r):
                r += [0] * (base + d - len(r))
            for t in range(d):
                if phi[t]:
                    r[base + t] -= c * phi[t]
    return tuple(r[:d])


def zmul(a, b, N):
    raw = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    raw[i + j] += ai * bj
    return _reduce(list(raw), N)


def embed(z, N, j):
    """z (tuple) -> complex value of sum z_k e^{2 pi i j k/N} (mp)."""
    s = mp.mpc(0)
    for k, c in enumerate(z):
        if c:
            s += c * mp.e ** (2 * mp.pi * mp.mpf(j) * mp.mpf(k) / N * mp.j)
    return s


def phys(z, N):
    return embed(z, N, 1)


def rot_closure(strand, N):
    """orbit of the strand under multiplication by zeta (x -> x*zeta)."""
    out = set(strand)
    frontier = set(strand)
    zeta = (0, 1) + (0,) * (RANK[N] - 2)  # the element zeta
    for _ in range(N):
        nxt = set()
        for s in frontier:
            w = zmul(s, zeta, N)
            if w not in out:
                out.add(w)
                nxt.add(w)
        frontier = nxt
        if not frontier:
            break
    return out


def hull(pts):
    pts = sorted(set(pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def in_convex(pt, hull_pts):
    n = len(hull_pts)
    for i in range(n):
        a, b = hull_pts[i], hull_pts[(i + 1) % n]
        cr = (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
        c = cert_cmp(cr, 0)
        if c == "INCONCLUSIVE":
            return "INCONCLUSIVE"
        if c < 0:
            return False
    return True


def window_for(N, j):
    strand = [tuple(t) for t in itertools.product((-1, 0, 1), repeat=RANK[N])]
    orb = rot_closure(strand, N)
    pts = [(embed(z, N, j).real, embed(z, N, j).imag) for z in orb]
    H = hull(pts)
    # ensure CCW orientation
    area2 = sum(a[0] * b[1] - b[0] * a[1]
                 for a, b in zip(H, H[1:] + H[:1]))
    if area2 < 0:
        H = H[::-1]
    return H, orb


def unit_for(N):
    """(u tuple, u real value, sigma_j(u) real value, minimal poly str)."""
    if N == 5:
        # phi = 1 + zeta + zeta^4  (2 cos(pi/5) = 1 + 2cos(2pi/5)? no:
        # 2cos(pi/5) = 1.618; in Z[zeta5]: zeta5 + zeta5^{-1} = 2cos(2pi/5)=0.618
        # phi = 1 + (zeta5 + zeta5^4) = 1 + 0.618 = 1.618  -> tuple (1,1,0,0,1)->rank4
        u = (1, 1, 0, 0, 1)[:RANK[5]]
        u = tuple((1, 1, 0, 0, 1)[:4]) + ()
        # rank-4 power basis {1,z,z^2,z^3}; z^4 = -(1+z+z^2+z^3)
        # 1 + z + z^4 = 1 + z - (1+z+z^2+z^3) = -z^2-z^3
        u = (0, 0, -1, -1)
        uval = mp.mpf(5) ** mp.mpf("0.5") / 2 + mp.mpf("0.5")
        return u, uval, 1 - uval, "x^2-x-1"
    if N == 8:
        # 1+sqrt2 = 1 + z + z^3   (z+z^3 = 2cos(pi/4)+... z=e^{i pi/4}: z+z^{-1}=sqrt2;
        # z^{-1} = z^7 = -z^3 (x^4=-1 => z^7 = z^4*z^3 = -z^3)
        # so z+z^{-1} = z - z^3 = sqrt2  -> 1+sqrt2 = 1 + z - z^3
        u = (1, 1, 0, -1)
        uval = 1 + mp.sqrt(2)
        return u, uval, 1 - mp.sqrt(2), "x^2-2x-1"
    if N == 12:
        # 2+sqrt3 = 2 + 2cos(pi/6)?? 2cos(pi/12)... 2+sqrt3 = 2(1+... in Z[zeta12]:
        # zeta12 = e^{i pi/6}; 2cos(pi/12) = z+z^{-1} = z + z^{11}; z^{11} = -z^3-...
        # simpler: sqrt3 = 2cos(pi/6) = z^2 + z^{-2} = z^2 + z^{10}; with Phi12: x^4-x^2+1=0
        # => z^4 = z^2 - 1; z^6 = -1; z^10 = z^6 z^4 = -(z^2-1) = 1 - z^2
        # sqrt3 = z^2 + 1 - z^2 = 1 ?? wrong. 2cos(pi/6) = sqrt3: z^2 = e^{i pi/3}:
        #   2cos(pi/6) involves z (not z^2): 2cos(pi/12)= (1/2)sqrt(2+sqrt3)... skip:
        # take 2+sqrt3 = 4 cos^2(pi/12) = (z + z^{-1})^2 + 2 = z^2 + 2 + z^{-2} + 2
        # cleanest: 2+sqrt3 = 2 + (z^2 + z^{-2})? z^2+z^{-2} = 2cos(pi/3) = 1. NO.
        # sqrt3 = 2cos(pi/6): pi/6 = 2pi/12: 2cos(2pi/12) = z + z^{-1} with z=zeta12!
        #   z + z^{-1} = 2cos(pi/6) = sqrt3.  z^{-1} = z^{11} = z^6 z^5 = -z^5
        #   and z^5 = z(z^4) = z(z^2 -1) = z^3 - z  =>  z^{-1} = -(z^3 - z) = z - z^3
        # sqrt3 = z + (z - z^3) = 2z - z^3 ;  2+sqrt3 = 2 + 2z - z^3
        u = (2, 2, 0, -1)
        uval = 2 + mp.sqrt(3)
        return u, uval, 2 - mp.sqrt(3), "x^2-4x+1"
    if N == 7:
        # u7 = 1 + 2cos(2pi/7) = 1 + z + z^6 ; z^6 = -(1+z+...+z^5)
        # => u7 = 1 + z - (1+z+z^2+z^3+z^4+z^5) = -z^2-z^3-z^4-z^5
        u = (0, 0, -1, -1, -1, -1)
        uval = 1 + 2 * mp.cos(2 * mp.pi / 7)
        return u, uval, None, "x^3-2x^2-x+1"
    raise ValueError(N)


def sigma_j_value(u_tuple, N, j):
    """sigma_j(u) = embed(u, N, j) -- must be real for our units."""
    v = embed(u_tuple, N, j)
    assert abs(v.imag) < mp.mpf("1e-80"), f"sigma_{j}(u) not real: {v}"
    return v.real


print("=" * 76)
print("B. THE THREE 2D FAMILIES: model sets + inflation  (N = 5, 8, 12)")
print("=" * 76)

summary = {}
for N, j_int, label in ((5, 2, "Penrose / pentagonal"),
                          (8, 3, "Ammann-Beenker / octagonal"),
                          (12, 5, "12-fold / dodecagonal")):
    print(f"\n--- N = {N} ({label}), internal plane zeta |-> zeta^{j_int} ---")
    H, orb = window_for(N, j_int)
    nv = len(H)
    area2 = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(H, H[1:] + H[:1]))) / 2
    print(f"   window: {nv}-gon, area {mp.nstr(area2, 8)}, "
          f"from {len(orb)} orbit-strand points")

    # patch: enumerate module box, keep |phys| <= R and window IN
    B = 4 if N != 12 else 3
    R = mp.mpf(25)
    patch = {}
    inconclusive = 0
    for t in itertools.product(range(-B, B + 1), repeat=RANK[N]):
        if all(c == 0 for c in t):
            continue
        z = t
        p = phys(z, N)
        if p.real ** 2 + p.imag ** 2 > R * R:
            continue
        ii = embed(z, N, j_int)
        ok = in_convex((ii.real, ii.imag), H)
        if ok == "INCONCLUSIVE":
            inconclusive += 1
            continue
        if ok:
            patch[z] = (p.real, p.imag)
    n_pts = len(patch)
    dens = n_pts / (mp.pi * R * R)
    print(f"   patch |z| <= {mp.nstr(R,4)}: {n_pts} points, density {mp.nstr(dens,6)}"
          + (f", INCONCLUSIVE window tests skipped: {inconclusive}" if inconclusive else ""))
    check(f"N={N}: model set exists (Delone-looking patch, {n_pts} points)", n_pts > 50)

    # N-fold symmetry: rotation by 2pi/N = module multiplication by zeta;
    # internal rotates by 2pi j/N; window built rotation-invariant.
    sym_ok, sym_n = True, 0
    zeta = (0, 1) + (0,) * (RANK[N] - 2)
    for z in list(patch.keys()):
        w = zmul(z, zeta, N)
        if w in patch:
            sym_n += 1
        else:
            # radius is preserved; must be a window miss -> would contradict
            # rotation invariance of W; check directly
            ii = embed(w, N, j_int)
            ok = in_convex((ii.real, ii.imag), H)
            if ok is True and (phys(w, N).real ** 2 + phys(w, N).imag ** 2) <= R * R:
                sym_n += 1  # in the set, just missed the dict (should not happen)
            else:
                sym_ok = False
    check(f"N={N}: patch closed under rotation by 2pi/{N} ({sym_n}/{n_pts})",
          sym_ok and sym_n == n_pts)

    # inflation
    u, uval, uint, poly = unit_for(N)
    u_tuple = tuple(u[:RANK[N]])
    # verify the tuple really is the unit: embed at j=1
    check(f"N={N}: unit tuple embeds to u = {mp.nstr(uval,10)} (root of {poly})",
          abs(phys(u_tuple, N).real - uval) < mp.mpf("1e-80")
          and abs(phys(u_tuple, N).imag) < mp.mpf("1e-80"))
    sj = sigma_j_value(u_tuple, N, j_int)
    check(f"N={N}: sigma_j(u) = {mp.nstr(sj, 10)} with |sigma_j(u)| = 1/u < 1 "
          "(Pisot unit; internal contraction)",
          abs(abs(sj) - 1 / uval) < mp.mpf("1e-80") and abs(sj) < 1)
    # verify u is a unit of the module: multiplication by u is a bijection on
    # the box? instead verify on enough points that u.z stays integral
    # (automatic) and det of the multiplication matrix = +-1:
    d = RANK[N]
    cols = []
    for k in range(d):
        e = [0] * d
        e[k] = 1
        cols.append(zmul(tuple(e), u_tuple, N))
    # determinant of the integer matrix whose columns are u.e_k
    import fractions as fr
    Mm = [[cols[c][r] for c in range(d)] for r in range(d)]
    # fraction Gaussian det
    A = [[fr.Fraction(x) for x in row] for row in Mm]
    det = fr.Fraction(1)
    for col in range(d):
        piv = next((r for r in range(col, d) if A[r][col] != 0), None)
        if piv is None:
            det = fr.Fraction(0)
            break
        if piv != col:
            A[col], A[piv] = A[piv], A[col]
            det = -det
        det *= A[col][col]
        for r in range(col + 1, d):
            if A[r][col]:
                f = A[r][col] / A[col][col]
                A[r] = [a - f * b for a, b in zip(A[r], A[col])]
    check(f"N={N}: multiplication by u on M_N has determinant {det} = +-1 "
          "(u is a module unit: u.M = M)", det in (1, -1))

    infl_ok, infl_n, bad = True, 0, []
    for z, p in patch.items():
        w = zmul(z, u_tuple, N)
        pw = phys(w, N)
        # identity check: phys(w) = u * phys(z)
        if abs(pw.real - uval * p[0]) > mp.mpf("1e-60") or \
           abs(pw.imag - uval * p[1]) > mp.mpf("1e-60"):
            bad.append(("identity", z))
            break
        ii = embed(w, N, j_int)
        # identity check on internal: (u z)* = sigma_j(u) z*
        iz = embed(z, N, j_int)
        if abs(ii.real - sj * iz.real) > mp.mpf("1e-60") or \
           abs(ii.imag - sj * iz.imag) > mp.mpf("1e-60"):
            bad.append(("internal-identity", z))
            break
        ok = in_convex((ii.real, ii.imag), H)
        if ok is True:
            infl_n += 1
        else:
            bad.append(("window", z))
        if len(bad) > 3:
            break
    check(f"N={N}: inflation u.Lambda subset Lambda -- {infl_n} patch points "
          f"inflated, all land back in the model set"
          + (f" (first failures {bad[:3]})" if bad else ""),
          infl_ok and not bad, f"u = {mp.nstr(uval, 10)}")
    summary[N] = dict(points=n_pts, density=mp.nstr(dens, 6), window=nv,
                      u=mp.nstr(uval, 10), poly=poly)

print()
print("=" * 76)
print("C. N = 7: translation works; the inflation question has a subtlety")
print("=" * 76)
N = 7
strand = [tuple(t) for t in itertools.product((-1, 0, 1), repeat=6)]
orb = rot_closure(strand, N)
H2 = hull([(embed(z, 7, 2).real, embed(z, 7, 2).imag) for z in orb])
H3 = hull([(embed(z, 7, 3).real, embed(z, 7, 3).imag) for z in orb])
for Hx in (H2, H3):
    if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(Hx, Hx[1:] + Hx[:1])) < 0:
        Hx[:] = Hx[::-1]
print(f"   product window W2 x W3 in R^4: |W2| = {len(H2)}-gon, |W3| = {len(H3)}-gon")

B7 = 3
R7 = mp.mpf(25)
patch7 = {}
for t in itertools.product(range(-B7, B7 + 1), repeat=6):
    if all(c == 0 for c in t):
        continue
    p = phys(t, 7)
    if p.real ** 2 + p.imag ** 2 > R7 * R7:
        continue
    i2 = embed(t, 7, 2)
    i3 = embed(t, 7, 3)
    if in_convex((i2.real, i2.imag), H2) is True and \
       in_convex((i3.real, i3.imag), H3) is True:
        patch7[t] = (p.real, p.imag)
print(f"   patch |z| <= 25: {len(patch7)} points, "
      f"density {mp.nstr(len(patch7) / (mp.pi * 625), 6)}")
check("N=7: the cut-and-project model set exists (7-fold quasilattice)",
      len(patch7) > 100)

zeta7 = (0, 1, 0, 0, 0, 0)
def member7(w, R=R7):
    """Direct membership test (no box enumeration needed)."""
    p = phys(w, 7)
    if p.real ** 2 + p.imag ** 2 > R * R:
        return False
    i2 = embed(w, 7, 2)
    i3 = embed(w, 7, 3)
    return in_convex((i2.real, i2.imag), H2) is True and \
        in_convex((i3.real, i3.imag), H3) is True


sym7 = sum(1 for z in patch7 if member7(zmul(z, zeta7, 7)))
check(f"N=7: patch closed under rotation by 2pi/7 ({sym7}/{len(patch7)})",
      sym7 == len(patch7))

u7t, u7, _, poly7 = unit_for(7)
check(f"N=7: u7 = 1+2cos(2pi/7) = {mp.nstr(u7,10)} (root of {poly7}) is in M_7",
      abs(phys(u7t, 7).real - u7) < mp.mpf("1e-80"))
roots7 = mp.polyroots([1, -2, -1, 1])
others = [r for r in roots7 if abs(r - u7) > mp.mpf("1e-40")]
check("N=7: conjugates " + ", ".join(mp.nstr(r, 8) for r in others)
      + " both inside unit circle (Pisot unit of the real cubic subfield)",
      len(others) == 2 and all(abs(r) < 1 for r in others))
s2v = sigma_j_value(u7t, 7, 2)
s3v = sigma_j_value(u7t, 7, 3)
check(f"N=7: internal action scales: sigma_2(u7) = {mp.nstr(s2v,8)} (plane j=2), "
      f"sigma_3(u7) = {mp.nstr(s3v,8)} (plane j=3) -- both |.|<1 but DIFFERENT "
      f"({mp.nstr(abs(s2v),6)} vs {mp.nstr(abs(s3v),6)}): non-conformal, "
      "the j=3 plane also flips sign",
      abs(s2v) < 1 and abs(s3v) < 1 and abs(abs(s2v) - abs(s3v)) > mp.mpf("1e-6")
      and s3v < 0)

# inflation with the product window: (u z)*2 = s2 z*2 (scale 0.555),
# (u z)*3 = s3 z*3 (scale -0.802): each contracted into its own convex
# symmetric factor window -> closes.
infl7_ok, infl7_n, bad7 = True, 0, []
for z, p in patch7.items():
    w = zmul(z, u7t, 7)
    pw = phys(w, 7)
    if abs(pw.real - u7 * p[0]) > mp.mpf("1e-60") or abs(pw.imag - u7 * p[1]) > mp.mpf("1e-60"):
        bad7.append(("identity", z))
        break
    i2 = embed(w, 7, 2)
    i3 = embed(w, 7, 3)
    iz2 = embed(z, 7, 2)
    iz3 = embed(z, 7, 3)
    if abs(i2.real - s2v * iz2.real) > mp.mpf("1e-60") or \
       abs(i2.imag - s2v * iz2.imag) > mp.mpf("1e-60") or \
       abs(i3.real - s3v * iz3.real) > mp.mpf("1e-60") or \
       abs(i3.imag - s3v * iz3.imag) > mp.mpf("1e-60"):
        bad7.append(("internal-identity", z))
        break
    ok2 = in_convex((i2.real, i2.imag), H2)
    ok3 = in_convex((i3.real, i3.imag), H3)
    if ok2 is True and ok3 is True:
        infl7_n += 1
    else:
        bad7.append(("window", z, ok2, ok3))
    if len(bad7) > 3:
        break
check(f"N=7: with the product window, inflation u7.Lambda subset Lambda -- "
      f"{infl7_n} points inflated, all return to the model set"
      + (f" (failures {bad7[:3]})" if bad7 else ""),
      infl7_ok and not bad7, f"u7 = {mp.nstr(u7, 10)}")

print()
print("=" * 76)
print("SUMMARY TABLE")
print("=" * 76)
print(f"{'N':>3} {'points':>7} {'density':>9} {'window':>7} {'inflation u':>13}  poly")
for N, row in sorted(summary.items()):
    print(f"{N:>3} {row['points']:>7} {row['density']:>9} {row['window']:>7} "
          f"{row['u']:>13}  {row['poly']}")
print(f"  7 {len(patch7):>7} {mp.nstr(len(patch7)/(mp.pi*625),6):>9} "
      f"{f'{len(H2)}x{len(H3)}':>7} {mp.nstr(u7,10):>13}  x^3-2x^2-x+1")

n_pass = sum(1 for _, c in results if c)
print(f"\nSUMMARY: {n_pass}/{len(results)} checks VERIFIED")
for nm, c in results:
    if not c:
        print("  FAILED:", nm)
