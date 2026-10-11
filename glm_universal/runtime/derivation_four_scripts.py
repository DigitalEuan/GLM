"""``glm_universal.runtime.derivation_four_scripts`` -- the column-3 scripts of
Phase 119 (``studies/DERIVATION_FOUR_STUDY.md``).

Each function returns a stand-alone Python program, run in a fresh ``python3
-I`` interpreter by the gate, that re-checks one reading from its data with
code of its own: it imports nothing from the package (only ``fractions``,
``itertools``, ``math`` and ``re``), re-reads the claim from its text, and
prints a line ending ``VERIFIED True`` only when every check passes.

* :func:`chain_script` -- a certificate over the originals and chained copies:
  the copy conditions rebuilt from the steps' descriptions, the identity
  re-summed exactly;
* :func:`five_zy_script` -- a five-variable certificate over the elemental
  inequalities and Zhang-Yeung instances on four of the five, each instance
  re-derived from one copy;
* :func:`rd_script` -- a rate-distortion enclosure: ``D_min`` and ``D_max``
  recomputed, the channel's rows and distortion checked exactly, the dual
  point's feasibility checked exactly, both bounds recomputed with the
  script's own bracketed logarithms, and the printed decimal re-derived;
* :func:`robin_both_script`, :func:`robin_cases_script`,
  :func:`robin_bounds_script` -- certified sign changes from the script's own
  Taylor bounds and enclosure of ``pi``.

No float anywhere (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import derivation_two_scripts as DS
from . import derivation_three_scripts as S3

__all__ = ["chain_script", "five_zy_script", "rd_script",
           "robin_both_script", "robin_cases_script", "robin_bounds_script"]

_q = S3._q


def _el(e):
    return list(e[:3]) + [list(e[3])] if e[0] == "I" else list(e)


# ===========================================================================
# 1.  CHAINS OF COPIES AND FIVE VARIABLES
# ===========================================================================

def chain_script(names: Sequence[str], givens: Sequence[str], claim: str,
                 chains, label: str = "COPY-CHAIN") -> str:
    """``chains``: per claim ``(steps, lam, mu, nu)`` with ``steps`` the
    ``(name, of, base)`` triples, ``lam`` elementals over ``names + copies``,
    ``mu`` given coefficients, ``nu`` copy-condition coefficients (in the
    order the script rebuilds them)."""
    body = []
    for steps, lam, mu, nu in chains:
        body.append(
            "([" + ", ".join(f"({s[0]!r}, {s[1]!r}, {list(s[2])!r})"
                             for s in steps) + "], [" +
            ", ".join(f"({_el(e)!r}, {_q(c)})" for e, c in lam) + "], [" +
            ", ".join(f"({j}, {_q(c)})" for j, c in mu) + "], [" +
            ", ".join(f"({j}, {_q(c)})" for j, c in nu) + "])")
    lines = [DS._ENTROPY_READER,
             f"NAMES = {list(names)!r}",
             f"GIVENS = givens_of({list(givens)!r})",
             f"CLAIMS = claims_of({claim!r})",
             f"CHAINS = [{', '.join(body)}]",
             r'''
def conditions(names, steps):
    """the copy lemma's conditions: R has the joint law of (x, T) for every
    T in the base, and I(R; everything so far outside the base | base) = 0"""
    out, so_far = [], list(names)
    for r, x, base in steps:
        assert r not in so_far and x in so_far and x not in base
        assert all(b in so_far for b in base)
        for k in range(len(base) + 1):
            for T in combinations(base, k):
                out.append(vec_add(H([r] + list(T)), H([x] + list(T)), -1))
        rest = [v for v in so_far if v not in base]
        out.append(I([r], rest, list(base)))
        so_far.append(r)
    return out, so_far

assert len(CHAINS) == len(CLAIMS)
for claim, (steps, lam, mu, nu) in zip(CLAIMS, CHAINS):
    conds, allnames = conditions(NAMES, steps)
    total = {}
    for e, c in lam:
        assert c > 0
        total = vec_add(total, elemental_vec(tuple(e), allnames), c)
    for j, c in mu:
        total = vec_add(total, GIVENS[j], c)
    for j, c in nu:
        total = vec_add(total, conds[j], c)
    assert claim.get(frozenset(), F(0)) >= 0
    body = {s: c for s, c in claim.items() if s}
    assert total == body, ('certificate does not sum to the claim', total, body)
''',
             f"print({label!r}, len(CHAINS), 'certificate(s) over the copies "
             f"re-summed exactly, copy conditions rebuilt from the steps "
             f"VERIFIED True')"]
    return "\n".join(lines) + "\n"


def five_zy_script(names: Sequence[str], givens: Sequence[str], claim: str,
                   certificates, zy_certificates,
                   label: str = "FIVE-VARIABLES") -> str:
    """As Phase 118's script, with each Zhang-Yeung instance on four of the
    names (any four)."""
    body = []
    for lam, mu, nu in certificates:
        body.append(
            "([" + ", ".join(f"({_el(e)!r}, {_q(c)})" for e, c in lam) +
            "], [" + ", ".join(f"({j}, {_q(c)})" for j, c in mu) +
            "], [" + ", ".join(f"({list(i)!r}, {_q(c)})" for i, c in nu) +
            "])")
    zys = []
    for inst, lam5, conds in zy_certificates:
        zys.append(f"({list(inst)!r}, [" +
                   ", ".join(f"({_el(e)!r}, {_q(c)})" for e, c in lam5) +
                   "], [" + ", ".join(f"({j}, {_q(c)})" for j, c in conds) +
                   "])")
    lines = [DS._ENTROPY_READER, S3._ZY,
             f"NAMES = {list(names)!r}",
             f"GIVENS = givens_of({list(givens)!r})",
             f"CLAIMS = claims_of({claim!r})",
             f"CERTS = [{', '.join(body)}]",
             f"ZY_CERTS = [{', '.join(zys)}]",
             r'''
assert len(CERTS) == len(CLAIMS)
used = set()
for claim, (lam, mu, nu) in zip(CLAIMS, CERTS):
    total = {}
    for e, c in lam:
        assert c > 0
        total = vec_add(total, elemental_vec(tuple(e), NAMES), c)
    for j, c in mu:
        total = vec_add(total, GIVENS[j], c)
    for inst, c in nu:
        assert c > 0 and len(set(inst)) == 4 and set(inst) <= set(NAMES)
        total = vec_add(total, ZY(*inst), c)
        used.add(tuple(inst))
    assert claim.get(frozenset(), F(0)) >= 0
    body = {s: c for s, c in claim.items() if s}
    assert total == body, ('certificate does not sum to the claim', total, body)
done = set()
for inst, lam5, conds in ZY_CERTS:
    names5 = list(inst) + ['R']
    total = {}
    for e, c in lam5:
        assert c > 0
        total = vec_add(total, elemental_vec(tuple(e), names5), c)
    cc = copy_conditions(*inst)
    for j, c in conds:
        total = vec_add(total, cc[j], c)
    assert total == ZY(*inst), ('copy certificate does not sum', inst)
    done.add(tuple(inst))
assert used <= done, 'an instance without its copy certificate'
''',
             f"print({label!r}, 'certificate over the elemental inequalities "
             f"and Zhang-Yeung on four of the five re-summed, every "
             f"instance re-derived from one copy VERIFIED True')"]
    return "\n".join(lines) + "\n"


# ===========================================================================
# 2.  RATE DISTORTION FOR ANY DISTORTION MATRIX
# ===========================================================================

_LOG = r'''
from fractions import Fraction as F

def log2_iv(q, bits=64, P=256):
    """log2(q) between two rationals: the integer part from bit lengths,
    the fraction bit by bit by squaring, every square rounded outward"""
    q = F(q); assert q > 0
    e = q.numerator.bit_length() - q.denominator.bit_length()
    while F(2) ** e > q: e -= 1
    while F(2) ** (e + 1) <= q: e += 1
    m = q / F(2) ** e
    assert 1 <= m < 2
    one, two = 1 << P, 1 << (P + 1)
    lo = (m.numerator << P) // m.denominator
    hi = -((-(m.numerator << P)) // m.denominator)
    s, w = F(e), F(1)
    for _ in range(bits):
        lo = (lo * lo) >> P
        hi = -((-(hi * hi)) >> P)
        w /= 2
        if lo >= two:
            s += w; lo >>= 1; hi = -((-hi) >> 1)
        elif hi < two:
            pass
        else:
            return s, s + 2 * w
    return s, s + w

def rnd6(x):
    n = x * 10 ** 6
    v = (n.numerator * 2 + n.denominator) // (2 * n.denominator)
    return f"{v // 10 ** 6}.{v % 10 ** 6:06d}"
'''


def rd_script(p: Sequence[Fraction], d: Sequence[Sequence[Fraction]],
              d_min: Fraction, d_max: Fraction,
              points: Sequence[Tuple[Fraction, List[List[Fraction]],
                                     Fraction, List[Fraction], str]],
              label: str = "RATE-DISTORTION") -> str:
    """``points``: ``(D, channel, t, q, claimed decimal)``."""
    pts = []
    for D, Q, t, q, text in points:
        pts.append(f"({_q(D)}, [" + ", ".join(
            "[" + ", ".join(_q(v) for v in row) + "]" for row in Q) +
            f"], {_q(t)}, [" + ", ".join(_q(v) for v in q) + f"], {text!r})")
    lines = [_LOG,
             "P = [" + ", ".join(_q(v) for v in p) + "]",
             "D = [" + ", ".join("[" + ", ".join(_q(v) for v in r) + "]"
                                 for r in d) + "]",
             f"DMIN, DMAX = {_q(d_min)}, {_q(d_max)}",
             f"POINTS = [{', '.join(pts)}]",
             r'''
from math import gcd
nx, ny = len(P), len(D[0])
assert sum(P) == 1 and all(v > 0 for v in P)
assert all(v >= 0 for r in D for v in r)
assert DMIN == sum(P[x] * min(D[x]) for x in range(nx)), 'D_min'
assert DMAX == min(sum(P[x] * D[x][y] for x in range(nx)) for y in range(ny)), 'D_max'
L = 1
for r in D:
    for v in r:
        L = L * v.denominator // gcd(L, v.denominator)
for Dv, Q, t, q, text in POINTS:
    assert DMIN < Dv < DMAX
    # the upper bound: a channel within the distortion
    assert all(v >= 0 for r in Q for v in r) and all(sum(r) == 1 for r in Q)
    dist = sum(P[x] * Q[x][y] * D[x][y] for x in range(nx) for y in range(ny))
    assert dist <= Dv, 'the channel exceeds the distortion'
    out = [sum(P[x] * Q[x][y] for x in range(nx)) for y in range(ny)]
    upper = F(0)
    for x in range(nx):
        for y in range(ny):
            if Q[x][y]:
                upper += P[x] * Q[x][y] * log2_iv(Q[x][y] / out[y])[1]
    # the lower bound: a dual point, every exponential a power of t
    assert 0 < t < 1 and all(v > 0 for v in q)
    W = [[t ** int(D[x][y] * L) for y in range(ny)] for x in range(nx)]
    Z = [sum(q[y] * W[x][y] for y in range(ny)) for x in range(nx)]
    c = [sum(P[x] * W[x][y] / Z[x] for x in range(nx)) for y in range(ny)]
    cmax = max(c)
    mu = [1 / (cmax * Z[x]) for x in range(nx)]
    for y in range(ny):
        assert sum(P[x] * mu[x] * W[x][y] for x in range(nx)) <= 1, 'dual infeasible'
    lower = sum(P[x] * log2_iv(mu[x])[0] for x in range(nx)) + Dv * L * log2_iv(t)[0]
    lower = max(lower, F(0))
    assert lower <= upper and upper - lower < F(1, 10 ** 6), ('width', upper - lower)
    assert rnd6(lower) == rnd6(upper) == text, ('R(D)', Dv, rnd6(lower), rnd6(upper), text)
''',
             f"print({label!r}, len(POINTS), 'values of R(D) enclosed by a "
             f"channel within the distortion and a feasible dual point "
             f"VERIFIED True')"]
    return "\n".join(lines) + "\n"


# ===========================================================================
# 3.  ROBIN
# ===========================================================================

_BOTH = r'''
def sign_both(a, b, L, k):
    sn, cs = sincos(k * L)
    p, r = scale(sn, a * b - k * k), scale(cs, k * (a + b))
    lo, hi = p[0] + r[0], p[1] + r[1]
    return 1 if lo > 0 else (-1 if hi < 0 else 0)
'''


def robin_both_script(a: Fraction, b: Fraction, L: Optional[Fraction],
                      roots: Sequence[Tuple[Fraction, Fraction]],
                      claimed: Sequence[str], equation: str,
                      shift: Fraction = Fraction(0),
                      label: str = "ROBIN-BOTH") -> str:
    """Root ``n`` in ``((n - 1 + shift) pi/L, (n + shift) pi/L)``; on a
    symbolic interval the sign change on each interval is checked at
    ``L = 1/2, 1, 3``.  The printed equation is re-read: its coefficients
    must be ``ab`` and ``a + b``."""
    lines = [S3._TRIG, _BOTH, "import re",
             f"A, B, SHIFT = {_q(a)}, {_q(b)}, {_q(shift)}",
             f"EQ = {equation!r}",
             r'''
assert A > 0 and B > 0       # then lambda = 0 and lambda < 0 give y = 0
m = re.fullmatch(r"\((\d+(?:/\d+)?) - k\^2\)\*sin\((.*?)\) \+ (?:(\d+(?:/\d+)?)\*)?k\*cos\((.*?)\) = 0", EQ)
assert m and F(m.group(1)) == A * B and F(m.group(3) or 1) == A + B, 'equation'
''']
    if L is None:
        lines += [r'''
for L in (F(1, 2), F(1), F(3)):
    for n in (1, 2, 3):
        lo = (n - 1 + SHIFT) * PI_HI / L + F(1, 10 ** 20) if n + SHIFT > 1 else F(1, 10 ** 4)
        hi = (n + SHIFT) * PI_LO / L - F(1, 10 ** 20)
        sa, sb = sign_both(A, B, L, lo), sign_both(A, B, L, hi)
        assert sa != 0 and sb != 0 and sa != sb, ('no sign change', L, n)
''', f"print({label!r}, 'one root in each declared interval at L = 1/2, 1, 3 "
     f"(sign changes certified) VERIFIED True')"]
        return "\n".join(lines) + "\n"
    lines += [f"L = {_q(L)}",
              "ROOTS = [" + ", ".join(f"({_q(x)}, {_q(y)})" for x, y in roots)
              + "]",
              f"CLAIMED = {list(claimed)!r}",
              r'''
assert len(ROOTS) == len(CLAIMED) == 3
for n, ((lo, hi), text) in enumerate(zip(ROOTS, CLAIMED), 1):
    assert 0 < lo < hi
    assert lo > (n - 1 + SHIFT) * PI_HI / L, 'below its interval'
    assert hi < (n + SHIFT) * PI_LO / L, 'above its interval'
    sa, sb = sign_both(A, B, L, lo), sign_both(A, B, L, hi)
    assert sa != 0 and sb != 0 and sa != sb, 'no certified sign change'
    assert rnd(lo * lo) == rnd(hi * hi) == text, ('eigenvalue', text)
''', f"print({label!r}, len(ROOTS), 'eigenvalues enclosed with certified "
     f"sign changes in their intervals VERIFIED True')"]
    return "\n".join(lines) + "\n"


def robin_cases_script(family: str, cases, label: str = "ROBIN-CASES") -> str:
    """``cases``: ``(samples, mults, nonpositive)`` with ``samples`` the
    ``(h, L)`` points of the class, ``mults`` the first three intervals of
    ``k`` as multiples ``(a, b)`` of ``pi/L`` (or ``(m, m)`` for a closed
    form ``k = m pi/L``), ``nonpositive`` the claim ``none | zero |
    negative``.  At every sample the script certifies a sign change in each
    interval (around ``m pi/L`` for a closed form), and decides what is
    ``<= 0``: zero exactly when ``1 + hL = 0`` (Dirichlet end) or ``h = 0``
    (Neumann end); a negative eigenvalue exactly when the hyperbolic
    determinant changes sign, which it does at most once and is positive
    for large ``mu``."""
    rows = []
    for samples, mults, nonpos in cases:
        rows.append("([" + ", ".join(f"({_q(h)}, {_q(L)})" for h, L in samples)
                    + "], [" + ", ".join(f"({_q(x)}, {_q(y)})"
                                         for x, y in mults)
                    + f"], {nonpos!r})")
    lines = [S3._TRIG, f"FAM = {family!r}", f"CASES = [{', '.join(rows)}]",
             r'''
for samples, mults, nonpos in CASES:
    assert samples
    for h, L in samples:
        for a, b in mults:
            if a == b:          # a closed form: a sign change around it
                lo = a * PI_HI / L - F(1, 10 ** 12)
                hi = a * PI_LO / L + F(1, 10 ** 12)
            else:
                lo = a * PI_HI / L + F(1, 10 ** 20) if a > 0 else F(1, 10 ** 6)
                hi = b * PI_LO / L - F(1, 10 ** 20)
            sa, sb = sign_f(FAM, h, L, lo), sign_f(FAM, h, L, hi)
            assert sa != 0 and sb != 0 and sa != sb, ('no sign change', h, L, a, b)
        zero = (1 + h * L == 0) if FAM == 'D' else (h == 0)
        fam = 'Dneg' if FAM == 'D' else 'Nneg'
        neg = False
        if not zero:
            small = sign_f(fam, h, L, F(1, 10 ** 6))
            big = F(1)
            while sign_f(fam, h, L, big) <= 0:
                big *= 2
            assert small != 0
            neg = small < 0
        got = 'zero' if zero else ('negative' if neg else 'none')
        assert got == nonpos, ('what is <= 0', h, L, got, nonpos)
''', f"print({label!r}, sum(len(c[0]) for c in CASES), 'sample points: a "
     f"certified sign change in each of the first three intervals of "
     f"every case, the zero or negative eigenvalue exactly where "
     f"declared VERIFIED True')"]
    return "\n".join(lines) + "\n"


def robin_bounds_script(h: Fraction, lower: str, upper: str,
                        label: str = "ROBIN-BOUNDS") -> str:
    """For ``y(0) = 0``, ``y'(L) + h y(L) = 0``: the printed bounds of
    ``k_n L`` re-read, and at ``L = 1/2, 1, 3`` the root of each of the
    first three intervals enclosed and shown to lie between them (``tan``
    increasing on ``(0, pi/2)``)."""
    lines = [S3._TRIG, "import re",
             f"H = {_q(h)}", f"LOWER, UPPER = {lower!r}, {upper!r}",
             r'''
def offset(text):
    """(n - 1/2)*pi + arctan(C/(M*pi)) -> M - n as a Fraction"""
    m = re.fullmatch(r"\(n - 1/2\)\*pi \+ arctan\((.+)/\((n|\(n - (\d+(?:/\d+)?)\))\*pi\)\)", text)
    assert m, ('cannot read', text)
    return F(0) if m.group(2) == 'n' else -F(m.group(3))
lo_off, hi_off = offset(LOWER), offset(UPPER)
for L in (F(1, 2), F(1), F(3)):
    c = H * L
    for n in (1, 2, 3):
        a = (2 * n - 1) * PI_HI / (2 * L) + F(1, 10 ** 20)
        b = n * PI_LO / L - F(1, 10 ** 20)
        a = F(-((-a.numerator << 64) // a.denominator), 1 << 64)   # dyadic, up
        b = F((b.numerator << 64) // b.denominator, 1 << 64)       # dyadic, down
        sa = sign_f('D', H, L, a)
        assert sa != 0 and sa != sign_f('D', H, L, b)
        for _ in range(56):
            m = (a + b) / 2
            if sign_f('D', H, L, m) == sa: a = m
            else: b = m
        th_min = a * L - (2 * n - 1) * PI_HI / 2      # theta = z - (n - 1/2) pi
        th_max = b * L - (2 * n - 1) * PI_LO / 2
        assert 0 < th_min < th_max < PI_LO / 2
        (s1, _), (_, c1) = sincos(th_min)
        (_, s2), (c2, _) = sincos(th_max)
        # theta > arctan(c/((n + lo_off) pi)) and theta < arctan(c/((n + hi_off) pi))
        assert s1 / c1 > c / ((n + lo_off) * PI_LO), ('lower bound', L, n)
        assert s2 / c2 < c / ((n + hi_off) * PI_HI), ('upper bound', L, n)
''', f"print({label!r}, 'the first three roots at L = 1/2, 1, 3 lie between "
     f"the printed bounds VERIFIED True')"]
    return "\n".join(lines) + "\n"
