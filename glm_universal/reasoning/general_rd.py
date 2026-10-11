"""``glm_universal.reasoning.general_rd`` -- the rate-distortion function for
any finite distortion matrix (Phase 119, ``studies/DERIVATION_FOUR_STUDY.md``).

Why it exists
-------------
Phase 107 derived ``R(D)`` for Hamming distortion where the Shannon lower
bound is tight, and Phase 118 (:mod:`.hamming_rd`) on the rest of the range.
Any other distortion was refused ``UNSUPPORTED``.  For a general matrix
``d(x, y)`` the function has no closed form, but every value of it can be
*enclosed* by two certificates the reader can check:

* **an upper bound** -- any channel ``Q(y | x)`` whose expected distortion is
  at most ``D`` has ``I(X; Xh) >= R(D)``; the channel here is the
  Blahut-Arimoto channel ``Q(y|x) = q(y) t^d(x,y) / Z(x)`` at a rational
  ``t`` in ``(0, 1)``, with its distortion checked to be ``<= D`` exactly;
* **a lower bound** -- for ``s >= 0`` and weights ``mu > 0`` with
  ``sum_x p(x) mu(x) e^(-s d(x,y)) <= 1`` for every ``y``, every channel of
  distortion ``<= D`` has ``I >= sum_x p(x) log mu(x) - s D``
  (``GLM.NonShannon.rd_dual_lower_bound``).  With ``e^(-s) = t^(1/L)``
  (``L`` the common denominator of the distortions, ``dI = L d`` integers)
  every exponential is a power of the rational ``t``, so the dual condition
  is checked exactly in rationals, and ``mu(x) = 1 / (c_max Z(x))``.

Both bounds are sums of rational multiples of ``log2`` of rationals; each
logarithm is bracketed in integer fixed point (bit by bit by squaring,
:func:`.non_shannon.log2_fixed`, widened by its error bound), so the enclosure
``R(D) in [lower, upper]`` is rigorous and no float is used (D7).  The
interval is narrowed by running the iteration longer until it is shorter than
``WIDTH``, and the value is printed to six decimals when the two ends round
alike.

Also exact: ``D_min = sum_x p(x) min_y d(x, y)``, ``D_max = min_y sum_x p(x)
d(x, y)``, and ``R(D) = 0`` for ``D >= D_max`` (a constant reproduction).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd
from typing import List, Optional, Sequence, Tuple

from . import non_shannon as NS

__all__ = ["RDError", "GeneralRD", "Enclosure", "parse_matrix", "parse_rd",
           "general_rd", "enclose", "log2_bounds", "WIDTH"]

#: The target width of an enclosure, in bits.
WIDTH = Fraction(1, 10 ** 7)

#: Fixed-point precision of the logarithms (fractional bits).
LOG_BITS = 72

#: Fixed-point precision of the iteration (fractional bits).
FX = 96


class RDError(Exception):
    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
# 1.  READING
# ===========================================================================

def parse_matrix(text: str) -> List[List[Fraction]]:
    t = text.strip()
    if not (t.startswith("[[") and t.endswith("]]")):
        raise RDError("UNREADABLE", "write the distortion as [[d00, d01, ...], "
                                    "[d10, ...], ...]")
    rows = re.findall(r"\[([^\[\]]*)\]", t[1:-1])
    try:
        out = [[Fraction(x.strip()) for x in r.split(",")] for r in rows]
    except ValueError:
        raise RDError("UNREADABLE", f"cannot read the matrix {text!r}")
    if not out or any(len(r) != len(out[0]) for r in out) or len(out[0]) < 2:
        raise RDError("UNREADABLE", "the rows must have one common length >= 2")
    if any(x < 0 for r in out for x in r):
        raise RDError("UNREADABLE", "a distortion is never negative")
    return out


def _parse_source(spec: str) -> List[Fraction]:
    from .coding_theory import CodingError, _parse_source
    try:
        m, ps, letter = _parse_source(spec)
    except CodingError as e:
        raise RDError(e.code, e.why)
    if ps is None:
        raise RDError("UNSUPPORTED", f"a symbolic source ({letter}) with a "
                                     f"general distortion: give it a value")
    return ps


_RD = re.compile(r"^(.*?)\s+source\s+with\s+distortion\s+(\[\[.*\]\])"
                 r"(?:\s+at\s+D\s*=\s*(\d+(?:/\d+)?))?\s*$")


def parse_rd(text: str) -> Tuple[List[Fraction], List[List[Fraction]],
                                 Optional[Fraction]]:
    """``SOURCE source with distortion [[...]] [at D = q]``."""
    m = _RD.match(text.strip())
    if not m:
        raise RDError("UNREADABLE", "write SOURCE source with distortion "
                                    "[[...], ...] (optionally: at D = q)")
    p = _parse_source(m.group(1))
    d = parse_matrix(m.group(2))
    if len(d) != len(p):
        raise RDError("UNREADABLE", f"{len(p)} source letters but {len(d)} "
                                    f"rows of distortion")
    return p, d, (Fraction(m.group(3)) if m.group(3) else None)


# ===========================================================================
# 2.  RIGOROUS LOGARITHMS
# ===========================================================================

def _log2_int(n: int) -> Tuple[Fraction, Fraction]:
    """``log2(n)`` bracketed: the fixed-point value widened by eight units
    of the last place (its error is below two)."""
    v = NS.log2_fixed(n, LOG_BITS)
    u = Fraction(1, 1 << LOG_BITS)
    return v * u - 8 * u, v * u + 8 * u


def log2_bounds(q: Fraction) -> Tuple[Fraction, Fraction]:
    """``log2(q)`` for a positive rational, bracketed."""
    q = Fraction(q)
    if q <= 0:
        raise ValueError("log2 of a non-positive number")
    a_lo, a_hi = _log2_int(q.numerator)
    b_lo, b_hi = _log2_int(q.denominator)
    return a_lo - b_hi, a_hi - b_lo


# ===========================================================================
# 3.  THE PROBLEM
# ===========================================================================

@dataclass
class Enclosure:
    D: Fraction
    lower: Fraction
    upper: Fraction
    t: Fraction                     # e^(-s) per unit of the scaled distortion
    q: List[Fraction]               # the reproduction law of the iteration
    distortion: Fraction            # of the upper-bound channel, <= D
    iterations: int
    channel: List[List[Fraction]] = field(default_factory=list)

    def decimal(self) -> Optional[str]:
        def rnd(x: Fraction) -> str:
            n = x * 10 ** 6
            v = (n.numerator * 2 + n.denominator) // (2 * n.denominator)
            return f"{v // 10 ** 6}.{v % 10 ** 6:06d}"
        a, b = rnd(self.lower), rnd(self.upper)
        return a if a == b else None


@dataclass
class GeneralRD:
    probs: List[Fraction]
    d: List[List[Fraction]]
    scale: int                      # L: dI = L * d are integers
    d_min: Fraction
    d_max: Fraction
    y_star: int                     # a constant reproduction at D_max
    hamming: bool
    points: List[Enclosure] = field(default_factory=list)


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def general_rd(p: Sequence[Fraction], d: Sequence[Sequence[Fraction]],
               at: Optional[Fraction] = None) -> GeneralRD:
    p = [Fraction(x) for x in p]
    d = [[Fraction(x) for x in r] for r in d]
    L = 1
    for r in d:
        for x in r:
            L = _lcm(L, x.denominator)
    d_min = sum(px * min(r) for px, r in zip(p, d))
    cols = [sum(p[x] * d[x][y] for x in range(len(p)))
            for y in range(len(d[0]))]
    d_max = min(cols)
    y_star = cols.index(d_max)
    ham = (len(d) == len(d[0]) and
           all(d[x][y] == (0 if x == y else 1) for x in range(len(d))
               for y in range(len(d))))
    g = GeneralRD(p, d, L, d_min, d_max, y_star, ham)
    if d_min >= d_max:
        return g
    pts = [d_min + (d_max - d_min) * j / 4 for j in (1, 2, 3)]
    if at is not None:
        if at < d_min:
            raise RDError("INFEASIBLE", f"no channel reaches D = {at} < "
                                        f"D_min = {d_min}")
        if at < d_max and at not in pts:
            pts.append(at)
    for D in sorted(pts):
        e = enclose(p, d, L, D)
        if e.decimal() is None:
            # the two ends round apart at six decimals: narrow the enclosure
            e2 = enclose(p, d, L, D, WIDTH / 1000, max_rounds=6)
            if e2.upper - e2.lower < e.upper - e.lower:
                e = e2
        g.points.append(e)
    return g


# ===========================================================================
# 4.  THE ENCLOSURE
# ===========================================================================

def _powers(t: Fraction, dI: List[List[int]]) -> List[List[Fraction]]:
    return [[t ** k for k in row] for row in dI]


def _ba_fixed(p_fx: List[int], w_fx: List[List[int]], q_fx: List[int],
              iters: int) -> List[int]:
    """Blahut-Arimoto in integer fixed point (scale ``2**FX``): the
    iteration only chooses ``q``; every bound is then computed exactly."""
    one = 1 << FX
    nx, ny = len(p_fx), len(q_fx)
    for _ in range(iters):
        Z = [sum(q_fx[y] * w_fx[x][y] for y in range(ny)) >> FX
             for x in range(nx)]
        new = [0] * ny
        for x in range(nx):
            if Z[x] <= 0:
                continue
            c = (p_fx[x] << FX) // Z[x]
            for y in range(ny):
                new[y] += (c * ((q_fx[y] * w_fx[x][y]) >> FX)) >> FX
        s = sum(new)
        q_fx = [max(1, (v * one) // s) for v in new] if s else q_fx
    return q_fx


def _channel(p, dI, t, q):
    w = _powers(t, dI)
    Z = [sum(q[y] * w[x][y] for y in range(len(q))) for x in range(len(p))]
    Q = [[q[y] * w[x][y] / Z[x] for y in range(len(q))] for x in range(len(p))]
    return w, Z, Q


def _distortion(p, d, Q) -> Fraction:
    return sum(p[x] * Q[x][y] * d[x][y] for x in range(len(p))
               for y in range(len(Q[0])))


def _upper(p, Q) -> Fraction:
    """``I(X; Xh)`` of the channel, bracketed from above."""
    ny = len(Q[0])
    out = [sum(p[x] * Q[x][y] for x in range(len(p))) for y in range(ny)]
    total = Fraction(0)
    for x in range(len(p)):
        for y in range(ny):
            P = p[x] * Q[x][y]
            if P:
                _, hi = log2_bounds(Q[x][y] / out[y])
                total += P * hi
    return total


def _lower(p, dI, t, q, DI) -> Fraction:
    """The dual bound at ``t``, bracketed from below."""
    w = _powers(t, dI)
    Z = [sum(q[y] * w[x][y] for y in range(len(q))) for x in range(len(p))]
    c = [sum(p[x] * w[x][y] / Z[x] for x in range(len(p)))
         for y in range(len(q))]
    cmax = max(c)
    total = Fraction(0)
    for x in range(len(p)):
        lo, _ = log2_bounds(1 / (cmax * Z[x]))
        total += p[x] * lo
    lo_t, _ = log2_bounds(t)                # log2 t < 0 and DI >= 0
    return total + DI * lo_t


def _round_q(q_fx: List[int]) -> List[Fraction]:
    s = sum(q_fx)
    return [Fraction(v, s) for v in q_fx]


def _wfx(t: Fraction, dI: List[List[int]]) -> List[List[int]]:
    one = 1 << FX
    return [[(t ** k * one).numerator // (t ** k * one).denominator
             for k in row] for row in dI]


def enclose(p: Sequence[Fraction], d: Sequence[Sequence[Fraction]], L: int,
            D: Fraction, width: Fraction = WIDTH,
            max_rounds: int = 4) -> Enclosure:
    """A rigorous enclosure of ``R(D)`` for ``D_min < D < D_max``.

    A bisection on ``t`` (the iteration warm-started from the last law)
    brackets the slope whose curve point has distortion ``D`` between two
    dyadic rationals ``2**-40`` apart.  The upper bound is the mutual
    information of a channel of distortion exactly ``D``: the time-sharing
    mixture of the iteration's channels at the two ends (so a straight piece
    of ``R`` is bounded by its chord).  The lower bound is the better of the
    two dual points.  A round that misses ``WIDTH`` is re-run with three
    times the iterations."""
    p = list(p)
    dI = [[int(x * L) for x in r] for r in d]
    DI = D * L
    ny = len(d[0])
    one = 1 << FX
    p_fx = [(x.numerator << FX) // x.denominator for x in p]
    iters = 300
    enc = None
    for _ in range(max_rounds):
        lo_t, hi_t = Fraction(0), Fraction(1)
        q_fx = [one // ny] * ny
        lo_q = hi_q = None
        for _ in range(40):
            t = (lo_t + hi_t) / 2
            # a letter the last slope left unused must be able to come back
            q_fx = [max(v, one >> 16) for v in q_fx]
            q_fx = _ba_fixed(p_fx, _wfx(t, dI), q_fx, iters)
            _, _, Q = _channel(p, dI, t, _round_q(q_fx))
            if _distortion(p, d, Q) <= D:
                lo_t, lo_q = t, list(q_fx)
            else:
                hi_t, hi_q = t, list(q_fx)
        ends = []
        for t, qf in ((lo_t, lo_q), (hi_t, hi_q)):
            if qf is None or t == 0 or t == 1:
                continue
            q0 = _round_q(qf)
            qf = _ba_fixed(p_fx, _wfx(t, dI), qf, 4 * iters)
            q = _round_q(qf)
            _, _, Q = _channel(p, dI, t, q)
            ends.append((t, q, Q, _distortion(p, d, Q)))
            if t == lo_t and ends[-1][3] > D:
                # on a straight piece the longer run can cross D: keep the
                # bisection's own channel, whose distortion was <= D
                _, _, Q0 = _channel(p, dI, t, q0)
                ends.append((t, q0, Q0, _distortion(p, d, Q0)))
        ends.sort(key=lambda e: e[3])
        below = [e for e in ends if e[3] <= D]
        above = [e for e in ends if e[3] > D]
        if below and above:
            (_, _, Q1, D1), (_, _, Q2, D2) = below[-1], above[0]
            th = (D2 - D) / (D2 - D1)
            Qm = [[th * a + (1 - th) * b for a, b in zip(r1, r2)]
                  for r1, r2 in zip(Q1, Q2)]
        elif below:
            Qm = below[0][2]
        else:
            iters *= 3
            continue
        Dm = _distortion(p, d, Qm)
        up = _upper(p, Qm)
        low, tb, qb = max(((_lower(p, dI, e[0], e[1], DI), e[0], e[1])
                           for e in ends), key=lambda z: z[0])
        got = Enclosure(D, max(low, Fraction(0)), up, tb, qb, Dm, iters,
                        channel=Qm)
        if enc is None or got.upper - got.lower < enc.upper - enc.lower:
            enc = got
        if enc.upper - enc.lower <= width:
            return enc
        iters *= 3
    if enc is None:                                       # pragma: no cover
        raise RDError("NO_ENCLOSURE", "no channel within the distortion")
    return enc
