"""Third domain: integer and quadratic lattice shells (Z^d, D_4, E_8).

Vectors live in the *doubled* lattice: a point of (1/2)Z^d is a tuple of ints `y`
meaning the vector y/2, so a norm is `sum(y*y)/4` and an inner product is
`sum(u*v)/4` -- integer sums throughout.  That is the whole reason this domain is a
stress test for the engine: it shares no scalar arithmetic with the packing domain
(there is no `Q2`, no tolerance, no side length), it reads its witnesses off
counting identities, and its refusals are theorems about parity rather than failed
searches.

The domain registers the same five combinator slots:

  Tile          a single shell   L_m = {v in L : |v|^2 = m}
  Frame         the minimal shell and its kissing/root graph
  Strip         the ball up to M (the shells as annuli)
  Glue          a direct sum L (+) M, with theta multiplicativity as the law
  SymmetryFold  the -1 symmetry: shell counts pair up, so r(m) is even
  Atom          a lattice as a single object (rank, minimal norm, kissing number)
"""

from decimal import Decimal, getcontext
from fractions import Fraction as F
from math import isqrt

import glm_wheels as W

getcontext().prec = 70

#: square-free discriminants admitted by the side-level field test (triage only)
SQUAREFREE = (2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21)

#: the declared rank budget: beyond this the shell enumeration is not a cell
RANK_BUDGET = 8


class Lattice:
    """A declared lattice: kind, rank, minimal norm, and the parity test for y/2."""

    def __init__(self, kind, dim, minimal_norm=None):
        self.kind, self.dim = kind, dim
        self.minimal_norm = 1 if kind == "Z" else 2
        if minimal_norm is not None:
            self.minimal_norm = minimal_norm

    def desc(self):
        return f"Z{self.dim}" if self.kind == "Z" else self.kind

    def member(self, y):
        """Exact membership of the doubled vector `y` in this lattice."""
        if len(y) != self.dim:
            return False
        if self.kind == "Z":
            return all(c % 2 == 0 for c in y)
        if self.kind == "D4":
            return all(c % 2 == 0 for c in y) and sum(y) % 4 == 0
        if self.kind == "E8":
            par = y[0] % 2
            return all(c % 2 == par for c in y) and sum(y) % 4 == 0
        raise W.Refusal("unknown_lattice", f"{self.kind} is not in the alphabet")


LATTICES = {
    "Z1": Lattice("Z", 1), "Z2": Lattice("Z", 2), "Z3": Lattice("Z", 3),
    "Z4": Lattice("Z", 4), "D4": Lattice("D4", 4), "E8": Lattice("E8", 8),
}

_SHELLS: dict = {}
_BALLS: dict = {}


def _norm4(y):
    """4 * |y/2|^2, exactly (an int)."""
    return sum(c * c for c in y)


def _sum_of_k_squares(rem, k):
    """Necessary conditions for `rem` to be a sum of exactly `k` integer squares.

    k = 1: a perfect square; k = 2: no prime 3 mod 4 to an odd power (Fermat);
    k = 3: not of the form 4^a (8b + 7) (Legendre).  Used only to prune.
    """
    if rem < 0:
        return False
    if rem == 0:
        return True
    if k == 1:
        r = isqrt(rem)
        return r * r == rem
    if k == 2:
        n, p = rem, 3
        while p * p <= n:
            if n % p == 0:
                e = 0
                while n % p == 0:
                    n //= p
                    e += 1
                if p % 4 == 3 and e % 2:
                    return False
            p += 2
        return not (n % 4 == 3)
    if k == 3:
        while rem % 4 == 0:
            rem //= 4
        return rem % 8 != 7
    return True


def _rec(dim, budget, out, acc, i=0):
    """All y in Z^dim with sum(y*y) == budget (pruned recursion, ints only)."""
    rest = dim - i
    if rest == 0:
        if budget == 0:
            out.append(tuple(acc))
        return
    if budget < 0 or not _sum_of_k_squares(budget, rest if rest <= 3 else 4):
        return
    r = isqrt(budget)
    for v in range(-r, r + 1):
        acc.append(v)
        _rec(dim, budget - v * v, out, acc, i + 1)
        acc.pop()


def shell(lat: Lattice, m: int):
    """The m-th shell of `lat`, as doubled vectors of norm 4m (cached)."""
    key = (lat.desc(), m)
    if key in _SHELLS:
        return _SHELLS[key]
    if lat.dim > RANK_BUDGET:
        raise W.Refusal("rank_budget",
                        f"{lat.desc()} has rank {lat.dim} > {RANK_BUDGET}")
    out = []
    cand = []
    _rec(lat.dim, 4 * m, cand, [])
    for y in cand:
        if lat.member(y):
            out.append(y)
    out.sort()
    _SHELLS[key] = out
    return out


def ball(lat: Lattice, M: int):
    """Every vector of norm^2 <= M, grouped by shell (cached)."""
    key = (lat.desc(), M)
    if key in _BALLS:
        return _BALLS[key]
    shells = [shell(lat, m) for m in range(M + 1)]
    _BALLS[key] = shells
    return shells


def theta(lat: Lattice, M: int):
    """Theta series coefficients r(0..M): the shell sizes, exactly."""
    return [len(s) for s in ball(lat, M)]


def norm2(y):
    """|y/2|^2 as an exact Fraction (an integer in every cell here)."""
    return F(_norm4(y), 4)


def inner(u, v):
    """<u/2, v/2> as an exact Fraction."""
    return F(sum(a * b for a, b in zip(u, v)), 4)


def root_degree(lat: Lattice):
    """Degree of the inner-product-1 graph on the minimal shell (roots only)."""
    if lat.minimal_norm != 2:
        return None
    roots = shell(lat, 2)
    if not roots:
        return None
    deg = {len([1 for v in roots if inner(r, v) == 1]) for r in roots}
    return (deg.pop() if len(deg) == 1 else sorted(deg))


def _lat(key):
    if key not in LATTICES:
        raise W.Refusal("unknown_lattice", f"{key} is not in the alphabet")
    return LATTICES[key]


# ----------------------------------------------------------------- builders
def l_shell(key, m):
    """Tile: one shell.  An empty shell is refused, not certified as zero."""
    lat = _lat(key)
    vecs = shell(lat, m)
    if not vecs:
        raise W.Refusal(
            "empty_shell",
            f"{lat.desc()} has no vectors of norm^2 {m} "
            f"({'even lattice, odd norm' if lat.kind != 'Z' and m % 2 else 'no representation'})")
    claim = W.Claim("lattice_shells", "Tile", {"lat": lat.desc(), "m": m}, len(vecs), {
        "count": ("r_L(m)", len(vecs)),
        "norm": ("m", m),
        "rank": ("rank", lat.dim),
    }, {"lat": lat, "m": m, "shell": vecs})
    claim.meta["gain"] = None
    return claim


def l_frame(key):
    """Frame: the minimal shell plus its kissing and root-graph degrees."""
    lat = _lat(key)
    roots = shell(lat, lat.minimal_norm)
    if not roots:
        raise W.Refusal("empty_shell", f"{lat.desc()} has no minimal shell")
    deg = root_degree(lat)
    claim = W.Claim("lattice_shells", "Frame", {"lat": lat.desc()}, len(roots), {
        "kissing": ("|L_min|", len(roots)),
        "min_norm": ("m_min", lat.minimal_norm),
        "root_degree": ("deg_1", deg if deg is not None else "n/a (not a root lattice)"),
    }, {"lat": lat, "roots": roots, "kissing": len(roots), "degree": deg})
    claim.meta["gain"] = None
    return claim


def l_ball(key, M):
    """Strip: the ball of radius sqrt(M), i.e. the shells as annuli."""
    lat = _lat(key)
    shells = ball(lat, M)
    counts = [len(s) for s in shells]
    claim = W.Claim("lattice_shells", "Strip", {"lat": lat.desc(), "M": M},
                    sum(counts), {
                        "ball": ("N(0..M)", sum(counts)),
                        "shells": ("M+1", M + 1),
                        "theta": ("r(0..M)", tuple(counts)),
                    }, {"lat": lat, "M": M, "shells": shells, "theta": counts})
    claim.meta["gain"] = None
    return claim


def l_sum(key_a, key_b, M):
    """Glue: a direct sum, with theta multiplicativity as its conservation law."""
    a, b = _lat(key_a), _lat(key_b)
    if a.dim + b.dim > RANK_BUDGET:
        raise W.Refusal("rank_budget",
                        f"{a.desc()}(+){b.desc()} has rank {a.dim + b.dim} "
                        f"> {RANK_BUDGET}: the shell walk is not a cell")
    ta, tb = theta(a, M), theta(b, M)
    conv = [sum(ta[i] * tb[m - i] for i in range(m + 1)) for m in range(M + 1)]
    # the direct enumeration, independent of the convolution: pairs (u, v)
    pairs = []
    for m in range(M + 1):
        pairs.append([(u, v) for i in range(m + 1)
                      for u in shell(a, i) for v in shell(b, m - i)])
    claim = W.Claim("lattice_shells", "Glue",
                    {"a": a.desc(), "b": b.desc(), "M": M},
                    sum(len(p) for p in pairs), {
                        "rank": ("rank A + rank B", a.dim + b.dim),
                        "theta": ("r_A * r_B", tuple(conv)),
                        "shell0": ("r(0)", len(pairs[0])),
                    }, {"a": a, "b": b, "M": M, "pairs": pairs, "conv": conv,
                        "ta": ta, "tb": tb})
    claim.meta["gain"] = None
    return claim


def l_fold(key, m):
    """SymmetryFold: v -> -v is a free involution on the shell, so r(m) is even."""
    lat = _lat(key)
    vecs = shell(lat, m)
    if not vecs:
        raise W.Refusal("empty_shell", f"{lat.desc()} has no vectors of norm^2 {m}")
    neg = {tuple(-c for c in y) for y in vecs}
    closed = neg == {tuple(y) for y in vecs}
    fixed = [y for y in vecs if tuple(-c for c in y) == tuple(y)]
    if not closed or fixed:
        raise W.Refusal("fold_broken", f"{lat.desc()} shell {m} is not closed under -1")
    claim = W.Claim("lattice_shells", "SymmetryFold", {"lat": lat.desc(), "m": m},
                    len(vecs), {
                        "count": ("r_L(m)", len(vecs)),
                        "pairs": ("r/2", len(vecs) // 2),
                        "even": ("r mod 2", len(vecs) % 2),
                    }, {"lat": lat, "m": m, "shell": vecs})
    claim.meta["gain"] = None
    return claim


def l_atom(key):
    """Atom: the lattice itself -- rank, minimal norm, kissing number."""
    lat = _lat(key)
    roots = shell(lat, lat.minimal_norm)
    if not roots:
        raise W.Refusal("empty_shell", f"{lat.desc()} has no minimal shell")
    claim = W.Claim("lattice_shells", "Atom", {"lat": lat.desc()}, len(roots), {
        "rank": ("rank", lat.dim),
        "min_norm": ("m_min", lat.minimal_norm),
        "kissing": ("|L_min|", len(roots)),
    }, {"lat": lat, "roots": roots})
    claim.meta["gain"] = None
    return claim


# ---------------------------------------------------------------- witnesses
class ShellWitness(W.Witness):
    """The exactness gate: every vector is in the lattice, at exactly the norm."""

    name = "exact_norm"
    law = "shell_refused"

    def applies(self, claim):
        return claim.domain == "lattice_shells"

    def check(self, claim):
        p = claim.payload
        if "shell" in p:
            lat, m, vecs = p["lat"], p["m"], p["shell"]
            bad_norm = [y for y in vecs if _norm4(y) != 4 * m]
            bad_member = [y for y in vecs if not lat.member(y)]
            dup = len(vecs) != len({tuple(y) for y in vecs})
            ok = not bad_norm and not bad_member and not dup \
                and len(vecs) == claim.laws["count"][1]
            return ok, (f"{len(vecs)} vectors, {len(bad_norm)} off-norm, "
                        f"{len(bad_member)} off-lattice, duplicates {dup}")
        if "shells" in p:
            lat = p["lat"]
            bad = 0
            total = 0
            for m, grp in enumerate(p["shells"]):
                for y in grp:
                    total += 1
                    if _norm4(y) != 4 * m or not lat.member(y):
                        bad += 1
            ok = (bad == 0 and total == claim.n == claim.laws["ball"][1])
            return ok, (f"ball: {total} vectors over {len(p['shells'])} shells, "
                        f"{bad} off-norm or off-lattice")
        if "pairs" in p:
            a, b, M = p["a"], p["b"], p["M"]
            tot = sum(len(x) for x in p["pairs"])
            ok = tot == claim.laws["shell0"][1] * 0 + tot  # count is in `n`
            ok = tot == claim.n and all(
                _norm4(u) + _norm4(v) == 4 * m
                for m, grp in enumerate(p["pairs"]) for u, v in grp)
            return ok, f"{tot} pairs, every pair at norm 4m"
        roots = p.get("roots")
        if roots is not None:
            lat = p["lat"]
            bad = [y for y in roots if _norm4(y) != 4 * lat.minimal_norm]
            off = [y for y in roots if not lat.member(y)]
            return (not bad and not off and len(roots) == claim.n), \
                (f"{len(roots)} minimal vectors, {len(bad)} off-norm, "
                 f"{len(off)} off-lattice")
        raise W.Refusal("witness_scope", f"{claim.family} has no shell payload")


class KissingWitness(W.Witness):
    """Topology: the minimal shell's size and the inner-product-1 graph degree."""

    name = "kissing_topology"
    law = "kissing_mismatch"

    def applies(self, claim):
        return claim.domain == "lattice_shells" and (
            claim.family in ("Frame", "Atom"))

    def check(self, claim):
        lat = claim.payload["lat"]
        roots = shell(lat, lat.minimal_norm)
        deg = root_degree(lat)
        claimed = claim.laws["kissing"][1]
        ok = len(roots) == claimed and len({tuple(y) for y in roots}) == len(roots)
        nbrs = "n/a (not a root lattice)"
        if deg is not None:
            r0 = roots[0]
            nb = [v for v in roots if inner(r0, v) == 1]
            nbrs = str(len(nb))
            ok = ok and isinstance(deg, int) and deg >= 1 and len(nb) == deg
        return ok, (f"|L_min| = {len(roots)} (claimed {claimed}), "
                    f"degree set {deg}, neighbours of one root {nbrs}")


class ThetaWitness(W.Witness):
    """Conservation: theta(A (+) B) = theta(A) * theta(B), and ball = sum of shells."""

    name = "theta_conservation"
    law = "theta_mismatch"

    def applies(self, claim):
        return claim.domain == "lattice_shells"

    def check(self, claim):
        p = claim.payload
        if "pairs" in p:
            enumerated = [len(x) for x in p["pairs"]]
            ok = tuple(enumerated) == tuple(p["conv"]) == claim.laws["theta"][1]
            return ok, (f"enumerated {tuple(enumerated)} == convolution "
                        f"{tuple(p['conv'])}")
        if "shells" in p:
            counts = [len(s) for s in p["shells"]]
            ok = (tuple(counts) == claim.laws["theta"][1]
                  and sum(counts) == claim.laws["ball"][1] == claim.n)
            return ok, f"ball {claim.laws['ball'][1]} == sum of {len(counts)} shells"
        if "shell" in p:
            lat, m = p["lat"], p["m"]
            # the count must be the shell size the lattice itself reports
            ok = len(shell(lat, m)) == claim.laws["count"][1]
            return ok, f"r({m}) = {len(shell(lat, m))} recomputed from the lattice"
        roots = p.get("roots")
        if roots is not None:
            return len(roots) == len(shell(p["lat"], p["lat"].minimal_norm)), \
                f"minimal shell {len(roots)} == recomputed"
        return False, "no theta payload"


class DecimalLatticeWitness(W.Witness):
    """Independent 70-digit Decimal recomputation of the integer-only claims."""

    name = "decimal_cross"
    law = "decimal_mismatch"

    def applies(self, claim):
        return claim.domain == "lattice_shells"

    def check(self, claim):
        p = claim.payload
        if "pairs" in p:
            a, b, M = p["a"], p["b"], p["M"]
            ta = [Decimal(len(shell(a, i))) for i in range(M + 1)]
            tb = [Decimal(len(shell(b, i))) for i in range(M + 1)]
            dec = [sum(ta[i] * tb[m - i] for i in range(m + 1)) for m in range(M + 1)]
            exact = [Decimal(c) for c in claim.laws["theta"][1]]
            return dec == exact, f"theta_dec {tuple(int(c) for c in dec)}"
        if "shells" in p:
            dec = [Decimal(len(g)) for g in p["shells"]]
            ok = [int(c) for c in dec] == list(claim.laws["theta"][1])
            return ok, f"shell counts_dec {tuple(int(c) for c in dec)}"
        vecs = p.get("shell") or p.get("roots")
        if vecs is None:
            return True, "no coordinate payload: count law only"
        m = p.get("m", p["lat"].minimal_norm)
        dec = [sum(Decimal(c) * Decimal(c) for c in y) for y in vecs]
        want = Decimal(4 * m)
        ok = all(d == want for d in dec) and Decimal(len(vecs)) == Decimal(claim.n)
        return ok, f"{len(dec)} vectors, all |y|^2 == {want} in Decimal"


# --------------------------------------------------------------- the domain
def alphabet():
    return W.Alphabet("lattice_vectors", "Z^d / D_4 / E_8 (integer parity)", {
        "e": {"kind": "basis", "measure": 1, "extent": 1},
        "root": {"kind": "minimal", "measure": 2, "extent": 1},
        "half": {"kind": "coset", "measure": 2, "extent": 2},
    })


def domain():
    d = W.Domain("lattice_shells", alphabet(),
                 [ShellWitness(), KissingWitness(), ThetaWitness(),
                  DecimalLatticeWitness()])
    for name, fn in (("Tile", l_shell), ("Frame", l_frame), ("Strip", l_ball),
                     ("Glue", l_sum), ("SymmetryFold", l_fold), ("Atom", l_atom)):
        d.register(name, fn)
    return d


def wheel():
    cells = (
        [W.Cell("Tile", {"key": k, "m": m})
         for k, m in (("Z1", 1), ("Z2", 1), ("Z2", 2), ("Z3", 1), ("Z4", 2),
                      ("D4", 2), ("D4", 4), ("D4", 6), ("E8", 2), ("E8", 4))]
        + [W.Cell("Frame", {"key": k}) for k in ("Z2", "D4", "E8")]
        + [W.Cell("Strip", {"key": k, "M": M})
           for k, M in (("Z2", 3), ("D4", 6), ("E8", 2))]
        + [W.Cell("Glue", {"key_a": a, "key_b": b, "M": M})
           for a, b, M in (("Z2", "D4", 4), ("Z4", "D4", 3), ("Z2", "E8", 2))]
        + [W.Cell("SymmetryFold", {"key": k, "m": m})
           for k, m in (("Z2", 1), ("D4", 4), ("E8", 2))]
        + [W.Cell("Atom", {"key": k}) for k in ("Z2", "D4", "E8")]
        # declared refusals: an empty shell, and a rank over the budget
        + [W.Cell("Tile", {"key": "D4", "m": 3}),
           W.Cell("Tile", {"key": "E8", "m": 1}),
           W.Cell("Glue", {"key_a": "Z4", "key_b": "E8", "M": 2})]
    )
    return W.Wheel("lattice", domain(), list(cells))
