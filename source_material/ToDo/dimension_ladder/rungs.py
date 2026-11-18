#!/usr/bin/env python3
"""Exact data for the densest known sphere packings in dimensions 1 to 24.

What is stored
--------------
One row per dimension.  For each: the record packing, how many centres it puts
in a unit cell, the minimal squared norm ``mu``, the cell determinant ``det``
(where the record is a lattice with an integral Gram determinant), the exact
centre density ``delta``, and the packing density as the decimal printed in
Cohn's table.

The centre density is the invariant that compares packings across dimensions:

    delta = N * (sqrt(mu) / 2)**n / sqrt(det)          (N centres per cell)
    delta**2 = N**2 * (mu/4)**n / det                  (a rational number)

and the packing density is ``Delta = V_n * delta`` with ``V_n`` the volume of
the unit ball.

The gain over the grid
----------------------
``g = delta / 2**-n = delta * 2**n`` is how much denser the record is than the
cubic grid ``Z**n`` at the same dimension, which is the figure that carries
across dimensions: a packing in 8 dimensions is not comparable to one in 2 by
its density, but it is by its gain.  ``g**2 = delta**2 * 4**n``, again exact.

What is checked (``--selftest``)
--------------------------------
* exact: ``delta**2 == N**2 (mu/4)**n / det`` for every row that has a
  determinant.  For n = 1..8 and n = 24 the determinant and minimal norm are
  the lattice's own published invariants, so this is a real check; from n = 10
  the determinant is the value implied by the published density, so there it is
  a consistency check on the stored triple, not independent evidence.
* gain: ``g = delta 2**n`` and ``g**2 = delta**2 4**n``.
* published: the density recomputed from the stored ``delta`` matches the
  decimal string to 1e-9 relative.  This one uses floats and is only a
  transcription check, not a proof.

Nothing here is a new mathematical claim.  Each row is either proved optimal
(marked) or the best known packing when the source table was read.
"""

from fractions import Fraction
import math
import sys

F = Fraction

# --------------------------------------------------------------------------
# The table.  Fields:
#   n        dimension
#   name     the packing
#   centres  spheres per unit cell of the underlying lattice (1 = lattice)
#   mu       minimal squared norm
#   det      Gram determinant of the cell, or None where it is not integral
#   delta2   exact centre density, squared
#   density  packing density, as printed in the source table
#   status   proved / lattice only / best known
#   note     what the object is
#   kissing  kissing number, where it is classical and unambiguous
# --------------------------------------------------------------------------

ROWS = [
    dict(n=1, name="Z", centres=1, mu=1, det=F(1), delta2=F(1, 4),
         density="1",
         status="proved (trivial)",
         note="the integer grid; laminated Lambda_1",
         kissing=2),
    dict(n=2, name="A2 (hexagonal)", centres=1, mu=2, det=F(3), delta2=F(1, 12),
         density="0.9068996821171089",
         status="proved (Thue 1910; Fejes Toth 1940)",
         note="circles in the hexagonal lattice; laminated Lambda_2",
         kissing=6),
    dict(n=3, name="A3 = D3 (FCC)", centres=1, mu=2, det=F(4), delta2=F(1, 32),
         density="0.7404804896930610",
         status="proved (Hales 2005; Kepler)",
         note="face-centred cubic, oranges on a stall; laminated Lambda_3; HCP ties",
         kissing=12),
    dict(n=4, name="D4", centres=1, mu=2, det=F(4), delta2=F(1, 64),
         density="0.6168502750680849",
         status="lattice proved (Korkine-Zolotareff 1872); packing open",
         note="even-sum lattice; Voronoi cell is the regular 24-cell; Lambda_4",
         kissing=24),
    dict(n=5, name="D5", centres=1, mu=2, det=F(4), delta2=F(1, 128),
         density="0.4652576133092586",
         status="lattice proved (Korkine-Zolotareff 1873); packing open",
         note="even-sum lattice; Lambda_5",
         kissing=40),
    dict(n=6, name="E6", centres=1, mu=2, det=F(3), delta2=F(1, 192),
         density="0.3729475455820649",
         status="lattice proved (Blichfeldt 1935); packing open",
         note="Lambda_6",
         kissing=72),
    dict(n=7, name="E7", centres=1, mu=2, det=F(2), delta2=F(1, 256),
         density="0.2952978731457125",
         status="lattice proved (Blichfeldt 1935); packing open",
         note="Lambda_7",
         kissing=126),
    dict(n=8, name="E8", centres=1, mu=2, det=F(1), delta2=F(1, 256),
         density="0.2536695079010480",
         status="proved (Viazovska 2017)",
         note="Lambda_8; Voronoi cell is the Gosset polytope 4_21",
         kissing=240),
    dict(n=9, name="Lambda_9", centres=1, mu=4, det=F(512), delta2=F(1, 512),
         density="0.1457748758081711",
         status="best known; lattice optimality open",
         note="first laminated rung past E8",
         kissing=None),
    dict(n=10, name="Best's 40-centre packing", centres=40, mu=4,
         det=F(2) ** 20, delta2=F(25, 16384),
         density="0.0996157828077088",
         status="best known; not a lattice",
         note="40 spheres per cell, from a nonlinear binary code (Best 1980)",
         kissing=None),
    dict(n=11, name="Leech-Sloane 72-centre packing", centres=72, mu=4,
         det=F(2) ** 22, delta2=F(81, 65536),
         density="0.0662380270098011",
         status="best known; not a lattice",
         note="72 spheres per cell (Leech-Sloane 1971); beats Lambda_11 and K11",
         kissing=None),
    dict(n=12, name="K12 (Coxeter-Todd)", centres=1, mu=4, det=F(729),
         delta2=F(1, 729),
         density="0.0494541766242440",
         status="best known; densest known lattice",
         note="the Kappa lattice; denser than Lambda_12",
         kissing=None),
    dict(n=13, name="Leech-Sloane 72-centre packing", centres=72, mu=4,
         det=F(2) ** 22, delta2=F(81, 65536),
         density="0.0320142921603497",
         status="best known; not a lattice",
         note="72 spheres per cell; beats Lambda_13 and K13",
         kissing=None),
    dict(n=14, name="Lambda_14", centres=1, mu=4, det=F(768),
         delta2=F(1, 768),
         density="0.0216240960824471",
         status="best known; laminated",
         note="laminated rung",
         kissing=None),
    dict(n=15, name="Lambda_15", centres=1, mu=4, det=F(512),
         delta2=F(1, 512),
         density="0.0168575706567626",
         status="best known; laminated",
         note="laminated rung",
         kissing=None),
    dict(n=16, name="Lambda_16 = BW16 (Barnes-Wall)", centres=1, mu=4,
         det=F(256), delta2=F(1, 256),
         density="0.0147081643974308",
         status="best known; the LP bound cannot settle it",
         note="Construction B on the [16,5,8] Reed-Muller code; a fixed "
              "16-space of the Leech lattice",
         kissing=4320),
    dict(n=17, name="Lambda_17", centres=1, mu=4, det=F(256),
         delta2=F(1, 256),
         density="0.0088113191823211",
         status="best known; laminated",
         note="laminated rung; same centre density as E8 and BW16",
         kissing=None),
    dict(n=18, name="512-centre packing", centres=512, mu=4, det=None,
         delta2=F(3 ** 18, 2 ** 36),
         density="0.0061678981253312",
         status="best known; not a lattice",
         note="512 spheres per cell (Bierbrauer-Edel 2000)",
         kissing=None),
    dict(n=19, name="record packing (6 centres)", centres=6, mu=4, det=None,
         delta2=F(13 ** 19, 3 ** 18 * 5 ** 21),
         density="0.0041473691458627",
         status="best known; not a lattice",
         note="record from the antipode construction",
         kissing=None),
    dict(n=20, name="record packing (5 centres)", centres=5, mu=4, det=None,
         delta2=F(3 ** 40, 2 ** 20 * 5 ** 21),
         density="0.0040241650630681",
         status="best known; not a lattice",
         note="record from the antipode construction",
         kissing=None),
    dict(n=21, name="record packing (4 centres)", centres=4, mu=4, det=None,
         delta2=F(43 ** 21, 2 ** 82 * 3 ** 23),
         density="0.0029298291067157",
         status="best known; not a lattice",
         note="record from the antipode construction",
         kissing=None),
    dict(n=22, name="record packing (3 centres)", centres=3, mu=4, det=None,
         delta2=F(11 ** 22, 2 ** 46 * 3 ** 21),
         density="0.0024510340441211",
         status="best known; not a lattice",
         note="record packing; see the source table for the reference",
         kissing=None),
    dict(n=23, name="record packing (2 centres)", centres=2, mu=4, det=None,
         delta2=F(23 ** 23, 2 ** 68 * 3 ** 24),
         density="0.0019071945388448",
         status="best known; not a lattice",
         note="record from the antipode construction",
         kissing=None),
    dict(n=24, name="Lambda_24 (Leech)", centres=1, mu=4, det=F(1),
         delta2=F(1), density="0.0019295743094039",
         status="proved (Cohn-Kumar-Miller-Radchenko-Viazovska 2017)",
         note="Construction B/C on the Golay code; the last laminated lattice; "
              "Voronoi cell has 196,560 facets",
         kissing=196560),
]

BY_N = {r["n"]: r for r in ROWS}

# The dimensions where the densest packing of any kind is known.
PROVED_PACKING = (1, 2, 3, 8, 24)
# The dimensions where the densest lattice is known.
PROVED_LATTICE = (1, 2, 3, 4, 5, 6, 7, 8, 24)


# --------------------------------------------------------------------------
# Derived quantities
# --------------------------------------------------------------------------

def centre_density(n):
    """The exact centre density delta, as a positive number whose square is a
    Fraction (returned as that Fraction, since delta itself may be a surd)."""
    return BY_N[n]["delta2"]


def gain_squared(n):
    """``(delta * 2**n)**2``: the gain over the cubic grid, squared, exact."""
    return BY_N[n]["delta2"] * F(4) ** n


def ball_volume(n):
    """Volume of the unit ball in n dimensions (float; display only)."""
    return math.pi ** (n / 2.0) / math.gamma(n / 2.0 + 1.0)


def density(n):
    """Packing density, float (display and transcription check only)."""
    return ball_volume(n) * math.sqrt(float(BY_N[n]["delta2"]))


# --------------------------------------------------------------------------
# Formatting: exact surds, with a limit so huge prime powers fall back
# --------------------------------------------------------------------------

def _squarefree(x, div_limit=10 ** 7):
    """(k, m) with x == k*k*m and m squarefree, or None if undecidable.

    Every entry in the table is a product of small prime powers, so trial
    division stops immediately; the divisor cap only guards against a number
    this code has no business factoring.
    """
    x = int(x)
    k, m = 1, 1
    d = 2
    while d * d <= x and d <= div_limit:
        e = 0
        while x % d == 0:
            x //= d
            e += 1
        k *= d ** (e // 2)
        if e % 2:
            m *= d
        d += 1 if d == 2 else 2
    if x > 1:
        if d <= div_limit:
            m *= x          # what is left is prime
        else:
            return None
    return (k, m)


def surd(q):
    """``sqrt(q)`` as a string like ``'2.sqrt.3/3'``, or None if too big."""
    a = _squarefree(q.numerator)
    b = _squarefree(q.denominator)
    if a is None or b is None:
        return None
    kp, mp = a
    kb, mb = b
    k = F(kp, kb * mb)
    m = mp * mb
    if m == 1:
        return str(k.numerator) if k.denominator == 1 else f"{k.numerator}/{k.denominator}"
    if k == 1:
        return f"sqrt({m})"
    if k.denominator == 1:
        return f"{k.numerator}*sqrt({m})"
    return f"{k.numerator}*sqrt({m})/{k.denominator}"


def _short(s, value):
    """The exact surd if it is short enough to read, else the decimal."""
    if s is not None and len(s) <= 24:
        return s
    return f"~{value:.6g}"


def delta_str(n):
    q = BY_N[n]["delta2"]
    return _short(surd(q), math.sqrt(float(q)))


def gain_str(n):
    q = gain_squared(n)
    return _short(surd(q), math.sqrt(float(q)))


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def check_exact():
    """delta**2 == N**2 (mu/4)**n / det, where a determinant is stored."""
    checks = 0
    for r in ROWS:
        if r["det"] is None:
            continue
        want = F(r["centres"]) ** 2 * F(r["mu"], 4) ** r["n"] / r["det"]
        if want != r["delta2"]:
            raise AssertionError(
                f"n={r['n']}: N^2 (mu/4)^n / det = {want}, stored delta^2 = "
                f"{r['delta2']}")
        checks += 1
    return checks


def check_gain():
    """The gain over the grid squares to delta**2 * 4**n."""
    for r in ROWS:
        n = r["n"]
        g2 = gain_squared(n)
        if g2 != r["delta2"] * F(4) ** n:
            raise AssertionError(f"n={n}: gain identity failed")
        if g2 <= 0:
            raise AssertionError(f"n={n}: gain must be positive")
    return len(ROWS)


def check_published(tol=1e-9):
    """The recomputed density matches the published decimal (float check)."""
    worst = 0.0
    for r in ROWS:
        n = r["n"]
        got = density(n)
        want = float(r["density"])
        rel = abs(got - want) / want
        worst = max(worst, rel)
        if rel > tol:
            raise AssertionError(
                f"n={n}: computed density {got!r} vs published {want!r} "
                f"(relative {rel:.3e})")
    return worst


def check_counts():
    """The proved sets are what the table says they are."""
    proved = tuple(r["n"] for r in ROWS if r["status"].startswith("proved"))
    if proved != PROVED_PACKING:
        raise AssertionError(f"proved packings: {proved}")
    lattice = tuple(r["n"] for r in ROWS
                    if "lattice proved" in r["status"]
                    or r["status"].startswith("proved"))
    if lattice != PROVED_LATTICE:
        raise AssertionError(f"proved lattices: {lattice}")
    if sorted(BY_N) != list(range(1, 25)):
        raise AssertionError("the table must hold every dimension 1..24")
    return len(proved), len(lattice)


def check_headline():
    """The equalities this note is built on."""
    # E8, BW16 and Lambda_17 have the same centre density.
    if not (BY_N[8]["delta2"] == BY_N[16]["delta2"] == BY_N[17]["delta2"]):
        raise AssertionError("E8, BW16 and Lambda_17 must tie in centre density")
    # The Leech lattice has 16 times the centre density of E8 (256 in the square).
    if BY_N[24]["delta2"] != 256 * BY_N[8]["delta2"]:
        raise AssertionError("Leech must be 16x E8 in centre density")
    # The gains of the classic rungs: g = delta * 2**n, stored as g**2.
    want = {2: F(4, 3), 3: F(2), 4: F(4), 5: F(8), 6: F(64, 3),
            7: F(64), 8: F(256), 16: F(4096) ** 2, 17: F(8192) ** 2,
            24: F(2) ** 48}
    for n, g2 in want.items():
        if gain_squared(n) != g2:
            raise AssertionError(f"n={n}: gain^2 {gain_squared(n)} != {g2}")
    # Non-monotonicity: the record centre density falls from 12 to 13, and
    # 11 and 13 tie.
    if not (BY_N[11]["delta2"] == BY_N[13]["delta2"]):
        raise AssertionError("Lambda/Sloane rungs 11 and 13 must tie")
    if not (BY_N[12]["delta2"] > BY_N[13]["delta2"]):
        raise AssertionError("n=12 must be denser than n=13 in centre density")
    return True


def selftest():
    n_exact = check_exact()
    n_gain = check_gain()
    worst = check_published()
    n_proved, n_lattice = check_counts()
    check_headline()
    print(f"exact determinant identity : {n_exact} rows")
    print(f"gain identity              : {n_gain} rows")
    print(f"published densities        : all 24 agree (worst relative {worst:.2e})")
    print(f"proved: {n_proved} packings {PROVED_PACKING}, "
          f"{n_lattice} lattices {PROVED_LATTICE}")
    print("headline ties              : E8 = BW16 = Lambda_17, Leech = 16 x E8")
    print("OK")


def table():
    print(f"{'n':>3}  {'packing':<34} {'centres':>7} {'delta':>18} "
          f"{'gain':>16}  status")
    for r in ROWS:
        print(f"{r['n']:>3}  {r['name']:<34} {r['centres']:>7} "
              f"{delta_str(r['n']):>18} {gain_str(r['n']):>16}  {r['status']}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        table()
