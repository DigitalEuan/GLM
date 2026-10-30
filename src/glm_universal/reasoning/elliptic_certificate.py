"""``glm_universal.reasoning.elliptic_certificate`` -- the elliptic-curve
search (Phase 141, ``studies/ELLIPTIC_CERTIFICATE_STUDY.md``).

Why this module exists
----------------------
Phase 140 left this line in ``STATUS.md`` §2.2: *a prime that neither side
reaches within the budget is still refused (elliptic-curve certificates would
be the next kind)*.  Pratt and Pocklington entries need ``p - 1`` factored,
N+1 entries need ``p + 1``; a prime where neither splits was refused.

An **elliptic entry** ``[p, a, b, x, y, k, q]`` uses the group of the curve
``y^2 = x^3 + a x + b`` modulo ``p`` instead: ``Q = k (x, y)`` is computed as
an affine point, ``q Q`` as the point at infinity, ``q`` is certified by an
earlier entry and ``4p < (q - 1)^2``.  Its check is
:func:`primality_certificate._check_eentry`, which mirrors
``GLM.PrimalityCertificate.checkEEntry`` line for line, and
``elliptic_prime`` (``RequestProject/GLM/EllipticCertificate.lean``) proves
that an accepted entry is about a prime, using only the trivial bound of
``2r + 1`` points on a curve over ``ZMod r``.

What this module does is **find** entries.  A curve whose number of points
modulo ``p`` is ``k q`` with ``q`` prime and large is found by complex
multiplication (Atkin--Morain): for a discriminant ``D`` with
``4p = t^2 + |D| s^2`` (Cornacchia), the curves with CM by the order of
discriminant ``D`` have ``p + 1 - t`` or ``p + 1 + t`` points (and four or
six orders when ``D = -4`` or ``-3``), and their ``j``-invariants are the
roots modulo ``p`` of the class polynomial ``H_D``.  ``H_D`` is computed from
the ``q``-expansion of ``j`` at the reduced forms of discriminant ``D`` in
**fixed-point integer arithmetic** (no float is constructed), and rounded; a
wrong coefficient could only make a curve fail the check, never make a wrong
entry pass, so nothing about this computation is trusted.  The entry's own
``q`` is certified recursively (the descent); small ones by the Phase 140
mixed search.

The work is bounded twice: a budget of descent nodes (:data:`NODE_BUDGET`)
and a budget of rho iterations spent stripping small factors off the
candidate orders (:data:`RHO_BUDGET`).  When either runs out the search gives
up and the step stays refused.

Exact and deterministic: ``int`` only, no randomness.
"""

from __future__ import annotations

from math import gcd, isqrt
from typing import Dict, Iterator, List, Optional, Tuple

from . import primality_certificate as pc

__all__ = ["elliptic", "class_polynomial", "reduced_forms", "cornacchia",
           "sqrt_mod", "NODE_BUDGET", "RHO_BUDGET", "DISCRIMINANT_LIMIT",
           "CLASS_LIMIT", "SMALL"]

#: Descent nodes (numbers for which an elliptic entry is sought) one
#: certification may visit.
NODE_BUDGET = 400
#: Rho iterations one certification may spend on candidate orders.
RHO_BUDGET = 20_000_000
#: Rho iterations per candidate order and attempt.
RHO_SLICE = 20_000
#: Discriminants ``-3 >= D >= -DISCRIMINANT_LIMIT`` are tried ...
DISCRIMINANT_LIMIT = 3000
#: ... whose class number is at most this.
CLASS_LIMIT = 10
#: Below this a number is certified by the Phase 140 mixed search.
SMALL = 10 ** 30
#: Candidate orders are cleared of primes below this by trial division.
TRIAL_BOUND = 100_000


def _sieve(n: int) -> Tuple[int, ...]:
    flags = bytearray([1]) * (n + 1)
    flags[0] = flags[1] = 0
    for i in range(2, isqrt(n) + 1):
        if flags[i]:
            flags[i * i::i] = bytearray(len(flags[i * i::i]))
    return tuple(i for i in range(n + 1) if flags[i])


_TRIAL: Tuple[int, ...] = ()


def _trial_primes() -> Tuple[int, ...]:
    global _TRIAL
    if not _TRIAL:
        _TRIAL = _sieve(TRIAL_BOUND)
    return _TRIAL


# ---------------------------------------------------------------------------
# Square roots and Cornacchia modulo a (probable) prime
# ---------------------------------------------------------------------------

def sqrt_mod(n: int, p: int) -> Optional[int]:
    """A square root of ``n`` modulo the odd probable prime ``p`` (Cipolla,
    deterministic), or ``None``; every root returned is checked."""
    n %= p
    if n == 0:
        return 0
    if pow(n, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        r = pow(n, (p + 1) // 4, p)
        return r if r * r % p == n else None
    t = 0
    while True:
        w = (t * t - n) % p
        if w == 0:
            return t
        e = pow(w, (p - 1) // 2, p)
        if e == p - 1:
            break
        if e != 1:
            return None
        t += 1

    def mul(x, y):
        return ((x[0] * y[0] + x[1] * y[1] * w) % p,
                (x[0] * y[1] + x[1] * y[0]) % p)
    acc, base, e = (1, 0), (t, 1), (p + 1) // 2
    while e:
        if e & 1:
            acc = mul(acc, base)
        base = mul(base, base)
        e >>= 1
    r = acc[0]
    return r if r * r % p == n else None


def cornacchia(p: int, d: int) -> Optional[Tuple[int, int]]:
    """``(t, s)`` with ``4p = t^2 + |d| s^2`` for the discriminant ``d < 0``,
    or ``None`` (Cornacchia--Smith)."""
    x0 = sqrt_mod(d % p, p)
    if x0 is None:
        return None
    if (x0 - d) % 2:
        x0 = p - x0
    a, b, lim = 2 * p, x0, isqrt(4 * p)
    while b > lim:
        a, b = b, a % b
    c = 4 * p - b * b
    if c % (-d):
        return None
    s = isqrt(c // (-d))
    if s * s != c // (-d):
        return None
    return b, s


# ---------------------------------------------------------------------------
# Class polynomials, in fixed-point integer arithmetic
# ---------------------------------------------------------------------------

def reduced_forms(d: int) -> Tuple[Tuple[int, int, int], ...]:
    """The reduced primitive positive forms ``(a, b, c)`` of discriminant
    ``d``: ``|b| <= a <= c``, ``b >= 0`` when ``|b| = a`` or ``a = c``."""
    out = []
    a = 1
    while 3 * a * a <= -d:
        for b in range(-a + 1, a + 1):
            if (b * b - d) % (4 * a):
                continue
            c = (b * b - d) // (4 * a)
            if c < a or (b < 0 and a == c):
                continue
            if gcd(gcd(a, abs(b)), c) != 1:
                continue
            out.append((a, b, c))
        a += 1
    return tuple(out)


def _atan_inv(x: int, scale: int) -> int:
    power = scale // x
    total, n, sign, x2 = power, 1, -1, x * x
    while power:
        power //= x2
        total += sign * (power // (2 * n + 1))
        sign, n = -sign, n + 1
    return total


def _pi(scale: int) -> int:
    return 4 * (4 * _atan_inv(5, scale) - _atan_inv(239, scale))


def _exp_neg(y: int, prec: int) -> int:
    """``exp(-y / 2^prec)`` scaled by ``2^prec``, for ``y >= 0``."""
    k = max(0, y.bit_length() - prec + 4)
    z = y >> k                                   # z / 2^prec < 1/8
    term, total, n = 1 << prec, 1 << prec, 1
    while term:
        term = (term * -z) >> prec
        term = term // n if term >= 0 else -((-term) // n)
        total += term
        n += 1
    for _ in range(k):
        total = total * total >> prec
    return total


def _cos_sin(theta: int, prec: int) -> Tuple[int, int]:
    """``(cos, sin)`` of ``theta / 2^prec`` (``|theta| <= pi``), scaled."""
    one = 1 << prec
    c, s = one, 0
    term, n = one, 0
    while term:
        n += 1
        term = term * theta >> prec
        term = term // n if term >= 0 else -((-term) // n)
        r = n % 4
        if r == 1:
            s += term
        elif r == 2:
            c -= term
        elif r == 3:
            s -= term
        else:
            c += term
    return c, s


def _cmul(x, y, prec: int):
    return ((x[0] * y[0] - x[1] * y[1]) >> prec,
            (x[0] * y[1] + x[1] * y[0]) >> prec)


def _cdiv(x, y, prec: int):
    den = y[0] * y[0] + y[1] * y[1]
    return (((x[0] * y[0] + x[1] * y[1]) << prec) // den,
            ((x[1] * y[0] - x[0] * y[1]) << prec) // den)


def _j_value(form: Tuple[int, int, int], d: int, prec: int):
    """``j((-b + sqrt(d)) / 2a)`` scaled by ``2^prec``, as a complex pair."""
    a, b, _ = form
    one = 1 << prec
    pi = _pi(one << 16) >> 16
    root = isqrt((-d) << (2 * prec))             # sqrt|d| scaled
    modulus = _exp_neg(pi * root // (a << prec), prec)
    cs = _cos_sin(-pi * b // a, prec)
    q = (modulus * cs[0] >> prec, modulus * cs[1] >> prec)
    # E4 = 1 + 240 sum sigma3(n) q^n ; Delta = q prod (1 - q^n)^24
    e4 = (one, 0)
    prod = (one, 0)
    qn = (one, 0)
    n = 0
    while True:
        n += 1
        qn = _cmul(qn, q, prec)
        if abs(qn[0]) + abs(qn[1]) <= 2:
            break
        s3 = sum(t ** 3 for t in range(1, n + 1) if n % t == 0)
        e4 = (e4[0] + 240 * s3 * qn[0], e4[1] + 240 * s3 * qn[1])
        f = (one - qn[0], -qn[1])
        f2 = _cmul(f, f, prec)
        f4 = _cmul(f2, f2, prec)
        f8 = _cmul(f4, f4, prec)
        f24 = _cmul(_cmul(f8, f8, prec), f8, prec)
        prod = _cmul(prod, f24, prec)
    delta = _cmul(q, prod, prec)
    e4c = _cmul(_cmul(e4, e4, prec), e4, prec)
    return _cdiv(e4c, delta, prec)


_CLASS_POLY: Dict[int, Optional[Tuple[int, ...]]] = {}


def class_polynomial(d: int) -> Optional[Tuple[int, ...]]:
    """The ring class polynomial ``H_d`` (coefficients, constant first,
    monic), or ``None`` when the rounding is not clean.  Steering only: a
    wrong coefficient makes the curves it gives fail the check."""
    if d in _CLASS_POLY:
        return _CLASS_POLY[d]
    forms = reduced_forms(d)
    # bits of the largest coefficient: sum over forms of pi sqrt|d| / a / ln 2
    est = sum(isqrt(-d * 21) // a for a, _, _ in forms) + 16   # 4.54 ~ sqrt 21
    prec = 2 * est + 96
    poly = [(1 << prec, 0)]                       # constant first
    for form in forms:
        j = _j_value(form, d, prec)
        nxt = [(0, 0)] * (len(poly) + 1)
        for i, c in enumerate(poly):
            nxt[i + 1] = (nxt[i + 1][0] + c[0], nxt[i + 1][1] + c[1])
            m = _cmul(c, j, prec)
            nxt[i] = (nxt[i][0] - m[0], nxt[i][1] - m[1])
        poly = nxt
    out = []
    tol = 1 << (prec - 24)
    half = 1 << (prec - 1)
    for re, im in poly:
        r = (re + half) >> prec
        if abs(re - (r << prec)) > tol or abs(im) > tol:
            _CLASS_POLY[d] = None
            return None
        out.append(r)
    _CLASS_POLY[d] = tuple(out)
    return _CLASS_POLY[d]


_DISCRIMINANTS: Tuple[Tuple[int, int], ...] = ()


def discriminants() -> Tuple[Tuple[int, int], ...]:
    """``(h, d)`` for ``-3 >= d >= -DISCRIMINANT_LIMIT`` with class number
    ``h <= CLASS_LIMIT``, by class number then size."""
    global _DISCRIMINANTS
    if not _DISCRIMINANTS:
        out = []
        for m in range(3, DISCRIMINANT_LIMIT + 1):
            d = -m
            if d % 4 not in (0, 1):
                continue
            h = len(reduced_forms(d))
            if 1 <= h <= CLASS_LIMIT:
                out.append((h, d))
        _DISCRIMINANTS = tuple(sorted(out, key=lambda t: (t[0], -t[1])))
    return _DISCRIMINANTS


# ---------------------------------------------------------------------------
# Polynomials modulo p: one root of H_d
# ---------------------------------------------------------------------------

def _trim(f: List[int]) -> List[int]:
    while f and f[-1] == 0:
        f.pop()
    return f


def _pmod(f: List[int], g: List[int], p: int) -> List[int]:
    f = [c % p for c in f]
    inv = pow(g[-1], -1, p)
    while len(f) >= len(g) and _trim(f):
        if len(f) < len(g):
            break
        c = f[-1] * inv % p
        shift = len(f) - len(g)
        for i, gc in enumerate(g):
            f[shift + i] = (f[shift + i] - c * gc) % p
        _trim(f)
    return f


def _pmulmod(f: List[int], g: List[int], m: List[int], p: int) -> List[int]:
    out = [0] * (len(f) + len(g) - 1) if f and g else []
    for i, a in enumerate(f):
        for j, b in enumerate(g):
            out[i + j] = (out[i + j] + a * b) % p
    return _pmod(out, m, p)


def _ppowmod(base: List[int], e: int, m: List[int], p: int) -> List[int]:
    out: List[int] = [1]
    base = _pmod(base, m, p)
    while e:
        if e & 1:
            out = _pmulmod(out, base, m, p)
        base = _pmulmod(base, base, m, p)
        e >>= 1
    return out


def _pgcd(f: List[int], g: List[int], p: int) -> List[int]:
    f, g = _trim([c % p for c in f]), _trim([c % p for c in g])
    while g:
        f, g = g, _pmod(f, g, p)
    if f:
        inv = pow(f[-1], -1, p)
        f = [c * inv % p for c in f]
    return f


def _root(f: List[int], p: int) -> Optional[int]:
    """One root modulo ``p`` of the squarefree split polynomial ``f``."""
    while len(f) > 2:
        for delta in range(1, 200):
            h = _ppowmod([delta, 1], (p - 1) // 2, f, p)
            h = h + [0] * (1 - len(h)) if h else [0]
            h[0] = (h[0] - 1) % p
            g = _pgcd(f, h, p)
            if 1 < len(g) < len(f):
                f = g
                break
        else:
            return None
    if len(f) != 2:
        return None
    return (-f[0]) * pow(f[1], -1, p) % p


def _class_root(d: int, p: int) -> Optional[int]:
    poly = class_polynomial(d)
    if poly is None:
        return None
    f = _trim([c % p for c in poly])
    if len(f) < 2:
        return None
    if len(f) == 2:
        return (-f[0]) * pow(f[1], -1, p) % p
    xp = _ppowmod([0, 1], p, f, p)
    xp = xp + [0] * (2 - len(xp))
    xp[1] = (xp[1] - 1) % p
    g = _pgcd(f, xp, p)
    if len(g) < 2:
        return None
    return _root(g, p)


# ---------------------------------------------------------------------------
# Curves and orders
# ---------------------------------------------------------------------------

def _nonresidue(p: int) -> int:
    g = 2
    while pow(g, (p - 1) // 2, p) != p - 1:
        g += 1
    return g


def _curves(p: int, d: int) -> Iterator[Tuple[int, int]]:
    """``(a, b)`` covering the twists of the curves with CM by ``d``."""
    if d == -3:
        for b in range(1, 60):
            yield 0, b % p
        return
    if d == -4:
        for a in range(1, 60):
            yield a % p, 0
        return
    j = _class_root(d, p)
    if j is None or j in (0, 1728 % p):
        return
    c = j * pow((1728 - j) % p, -1, p) % p
    a, b = 3 * c % p, 2 * c % p
    yield a, b
    g = _nonresidue(p)
    yield a * g * g % p, b * g * g * g % p


def _orders(p: int, d: int, t: int, s: int) -> Tuple[int, ...]:
    traces = {t, -t}
    if d == -4:
        traces = {t, -t, 2 * s, -2 * s}
    if d == -3:
        traces |= {(t + 3 * s) // 2, -(t + 3 * s) // 2,
                   (t - 3 * s) // 2, -(t - 3 * s) // 2}
    return tuple(sorted(p + 1 - u for u in traces))


class _Work:
    def __init__(self) -> None:
        self.nodes = NODE_BUDGET
        self.rho = RHO_BUDGET


def _split_order(m: int, p: int, work: _Work) -> Optional[Tuple[int, int]]:
    """``(k, q)`` with ``m = k q``, ``q`` a probable prime below ``p`` with
    ``4p < (q - 1)^2``; small primes off by trial division, then a few rho
    slices."""
    k, q = 1, m
    for r in _trial_primes():
        while q % r == 0:
            q //= r
            k *= r
        if (q - 1) ** 2 <= 4 * p:
            return None
    for _ in range(4):
        if q < p and (q - 1) ** 2 > 4 * p and pc._probable_prime(q):
            return k, q
        if work.rho <= 0:
            return None
        bud = pc._Budget(q)
        bud.left = min(RHO_SLICE, work.rho)
        start = bud.left
        f = pc._rho(q, bud)
        work.rho -= start - max(bud.left, 0)
        if f is None:
            return None
        f = min(f, q // f)
        q //= f
        k *= f
        if (q - 1) ** 2 <= 4 * p:
            return None
    return None


def _point(p: int, a: int, b: int) -> Optional[Tuple[int, int]]:
    for x in range(0, 2000):
        y = sqrt_mod((x * x * x + a * x + b) % p, p)
        if y:
            return x, y
    return None


def _ec_candidates(p: int, work: _Work) -> Iterator[Tuple[int, list]]:
    """Accepted elliptic entries for ``p`` (with ``q`` not yet certified),
    lazily: ``(q, [p, a, b, x, y, k, q])``."""
    for _h, d in discriminants():
        if pow(d % p, (p - 1) // 2, p) != 1:
            continue
        ts = cornacchia(p, d)
        if ts is None:
            continue
        splits = []
        for m in _orders(p, d, *ts):
            kq = _split_order(m, p, work)
            if kq is not None:
                splits.append(kq)
        if not splits:
            continue
        curves = list(_curves(p, d))
        for k, q in splits:
            for a, b in curves:
                if gcd((4 * a * a * a + 27 * b * b) % p, p) != 1:
                    continue
                pt = _point(p, a, b)
                if pt is None:
                    continue
                entry = [p, a, b, pt[0], pt[1], k, q]
                if pc._check_eentry({q}, *entry):
                    yield q, entry
                    break


def _descend(n: int, work: _Work, done: Dict[int, list], chain: list) -> bool:
    if n in done:
        return True
    if n < SMALL:
        return pc._mixed(n, pc._Budget(n), done, chain)
    if work.nodes <= 0:
        return False
    work.nodes -= 1
    for q, entry in _ec_candidates(n, work):
        mark = len(chain)
        if _descend(q, work, done, chain):
            if pc._check_eentry(set(done), *entry):
                chain.append(entry)
                done[n] = entry
                return True
        for e in chain[mark:]:
            done.pop(e[0], None)
        del chain[mark:]
        if work.nodes <= 0:
            return False
    return False


def elliptic(n: int) -> Dict[str, object]:
    """An ``elliptic`` certificate for the probable prime ``n``; raises
    :class:`primality_certificate.NoCertificate` when the work runs out."""
    chain: list = []
    if not _descend(n, _Work(), {}, chain):
        raise pc.NoCertificate(n, n)
    return {"kind": "elliptic", "chain": chain}
