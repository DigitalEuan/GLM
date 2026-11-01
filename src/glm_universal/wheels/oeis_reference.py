"""``glm_universal.wheels.oeis_reference`` -- an independent reference for
the Integer Wheel's data, and the audit that admits an entry.

*Created 31 October 2026 (intake of glm_wheels_bundle; directive D22;
``studies/INTEGER_WHEEL_STUDY.md``, mark A).*

**Why.**  A wheel that speaks only ids whose *stored* terms start with the
claim is sound against its stored terms (``Wheels/IntegerWheel.lean``,
``speak_sound``), but the supplied data files some terms under identifiers
that are not theirs.  Soundness cannot see that; a second, independent
source can.

**What.**  :data:`REFERENCE` maps an OEIS identifier to a description and a
generator of that sequence's first terms *from its OEIS offset*.  The
generators were written in this round without reading the supplied
generators: closed forms, recurrences, sieves, exact integer arithmetic for the
digits of constants (Machin's formula, ``isqrt``, Brent-McMillan, Ramanujan's
series for Catalan's constant), Rule 30 run from a single cell, the
Lucas-Lehmer test for the Mersenne exponents; two famous sequences that cannot
be recomputed here (``A000001``, ``A000088``) and the first orders of the
noncyclic simple groups (``A001034``) are short literal lists.  The pairing
of an identifier with its definition is the reviewer's knowledge of the OEIS,
not a fetch from oeis.org; an entry is admitted only when that knowledge and
the item's author agree term for term.

**The audit.**  :func:`audit_entry` gives a supplied entry one verdict:

* ``verified`` -- its identifier has a reference and its stored terms equal a
  run of consecutive reference terms (the run's start is recorded: ``0`` is
  the b-file's first term);
* ``disagrees`` -- it has a reference and its stored terms are no such run;
* ``short reference`` -- the reference has fewer terms than are stored and
  agrees as far as it goes (not admitted: the rest is unchecked);
* ``not recomputed`` -- no reference exists for its identifier.

Only ``verified`` entries enter the absorbed wheels.  :data:`ADMITTED_IDS` is
the frozen list :func:`glm_universal.wheels.integer_wheel.default_wheel` uses
(the audit takes some seconds, chiefly the Lucas-Lehmer runs);
``tests/test_integer_wheel.py`` checks it against the live audit.  Integers
only; nothing here constructs a float (directive D7).
"""
from __future__ import annotations

from functools import lru_cache
from math import comb, factorial, gcd, isqrt, lcm
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "REFERENCE", "MAX_SHIFT", "VERIFIED", "DISAGREES", "SHORT", "NOT_RECOMPUTED",
    "reference_terms", "audit_entry", "audit_entries", "audit_supplied",
    "admitted_ids", "ADMITTED_IDS", "ADMITTED_GROUP_THEORY_IDS",
]

VERIFIED = "verified"
DISAGREES = "disagrees"
SHORT = "short reference"
NOT_RECOMPUTED = "not recomputed"

#: How far into the reference a stored run may start (a stored list that
#: drops the b-file's first few terms is still the sequence).
MAX_SHIFT = 8


# ---------------------------------------------------------------------------
# Small exact helpers (independent of the supplied code)
# ---------------------------------------------------------------------------

def _sieve(limit: int) -> List[int]:
    if limit < 2:
        return []
    flags = bytearray([1]) * (limit + 1)
    flags[0] = flags[1] = 0
    i = 2
    while i * i <= limit:
        if flags[i]:
            flags[i * i::i] = bytearray(len(flags[i * i::i]))
        i += 1
    return [i for i in range(limit + 1) if flags[i]]


def _primes(n: int) -> List[int]:
    limit = 32
    while True:
        ps = _sieve(limit)
        if len(ps) >= n:
            return ps[:n]
        limit *= 2


def _factor(n: int) -> Dict[int, int]:
    """Trial division (the reference only factors small integers)."""
    out: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def _is_prime_small(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _probable_prime(n: int) -> bool:
    """Strong probable-prime test to the first twelve prime bases (a proof
    below 3.18 * 10**23)."""
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in small:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _divisors(n: int) -> List[int]:
    small, large = [], []
    d = 1
    while d * d <= n:
        if n % d == 0:
            small.append(d)
            if d * d != n:
                large.append(n // d)
        d += 1
    return small + large[::-1]


def _phi(n: int) -> int:
    out = n
    for p in _factor(n):
        out = out // p * (p - 1)
    return out


def _digits(value: int, n: int) -> List[int]:
    return [int(c) for c in str(value)[:n]]


def _linear(first: Sequence[int], step: Callable[[List[int]], int], n: int) -> List[int]:
    out = list(first[:n])
    while len(out) < n:
        out.append(step(out))
    return out


def _seq(f: Callable[[int], int], start: int) -> Callable[[int], List[int]]:
    """The generator ``n -> [f(start), ..., f(start + n - 1)]``."""
    return lambda n: [f(k) for k in range(start, start + n)]


def _filtered(pred: Callable[[int], bool], start: int) -> Callable[[int], List[int]]:
    def gen(n: int) -> List[int]:
        out, k = [], start
        while len(out) < n:
            if pred(k):
                out.append(k)
            k += 1
        return out
    return gen


# ---------------------------------------------------------------------------
# Constants, to n decimal digits, in exact integer arithmetic
# ---------------------------------------------------------------------------

def _atan_inv(x: int, scale: int) -> int:
    """``atan(1/x) * scale``."""
    total, power, k, sign = 0, scale // x, 1, 1
    x2 = x * x
    while power:
        total += sign * (power // k)
        power //= x2
        k += 2
        sign = -sign
    return total


def _atanh_inv(x: int, scale: int) -> int:
    """``atanh(1/x) * scale``."""
    total, power, k = 0, scale // x, 1
    x2 = x * x
    while power:
        total += power // k
        power //= x2
        k += 2
    return total


def _pi_scaled(scale: int) -> int:
    return 16 * _atan_inv(5, scale) - 4 * _atan_inv(239, scale)


def _e_digits(n: int) -> List[int]:
    scale = 10 ** (n + 12)
    total, term, k = 0, scale, 0
    while term:
        total += term
        k += 1
        term //= k
    return _digits(total, n)


def _pi_digits(n: int) -> List[int]:
    return _digits(_pi_scaled(10 ** (n + 12)), n)


def _sqrt_digits(m: int, n: int) -> List[int]:
    return _digits(isqrt(m * 10 ** (2 * (n + 12))), n)


def _phi_digits(n: int) -> List[int]:
    scale = 10 ** (n + 12)
    return _digits((scale + isqrt(5 * scale * scale)) // 2, n)


def _ln2_scaled(scale: int) -> int:
    return 2 * _atanh_inv(3, scale)


def _ln2_digits(n: int) -> List[int]:
    return _digits(_ln2_scaled(10 ** (n + 12)), n)


def _gamma_digits(n: int) -> List[int]:
    """Euler-Mascheroni by Brent-McMillan (B1) with N = 2**5: error below
    e**(-128), so 50 digits at most are asked of it."""
    if n > 50:
        raise ValueError("at most 50 digits")
    scale = 10 ** 80
    big = 32
    ln_n = 5 * _ln2_scaled(scale)
    a = -ln_n
    b = scale
    u, v = a, b
    k = 1
    while True:
        b = b * big * big // (k * k)
        a = (a * big * big // k + b) // k
        if b == 0 and a == 0:
            break
        u += a
        v += b
        k += 1
    return _digits(u * scale // v, n)


def _catalan_digits(n: int) -> List[int]:
    """Catalan's constant by Ramanujan's series
    G = (pi/8) ln(2 + sqrt 3) + (3/8) sum_k 1 / ((2k+1)^2 C(2k, k)),
    with ln(2 + sqrt 3) = 2 atanh(1/sqrt 3)."""
    scale = 10 ** (n + 15)
    # atanh(1/sqrt3) = (1/sqrt3) * sum_k 3**-k / (2k+1)
    s, power, k = 0, scale, 0
    while power:
        s += power // (2 * k + 1)
        power //= 3
        k += 1
    sqrt3 = isqrt(3 * scale * scale)
    atanh = s * scale // sqrt3
    log_term = 2 * atanh
    first = _pi_scaled(scale) * log_term // (8 * scale)
    series, k = 0, 0
    while True:
        term = scale // ((2 * k + 1) ** 2 * comb(2 * k, k))
        if term == 0:
            break
        series += term
        k += 1
    return _digits(first + 3 * series // 8, n)


def _continued_fraction(num: int, den: int, n: int) -> List[int]:
    out = []
    while den and len(out) < n:
        q = num // den
        out.append(q)
        num, den = den, num - q * den
    return out


def _pi_cf(n: int) -> List[int]:
    """Partial quotients of pi, kept only where the bracketing rationals
    agree."""
    scale = 10 ** 80
    p = _pi_scaled(scale)
    lo = _continued_fraction(p - 10, scale, n + 5)
    hi = _continued_fraction(p + 10, scale, n + 5)
    out = []
    for x, y in zip(lo, hi):
        if x != y:
            break
        out.append(x)
    return out[:n]


def _e_cf(n: int) -> List[int]:
    out = [2]
    k = 1
    while len(out) < n:
        out += [1, 2 * k, 1]
        k += 1
    return out[:n]


# ---------------------------------------------------------------------------
# Sequences that need a little machinery
# ---------------------------------------------------------------------------

def _rule30_centre(n: int) -> List[int]:
    """Rule 30 from a single black cell: new = left XOR (centre OR right).
    The row is an integer whose bit ``j`` is a cell; every step shifts the
    picture one cell, so the centre cell at step ``t`` is bit ``t``."""
    row, out = 1, []
    for t in range(n):
        out.append((row >> t) & 1)
        row = (row << 2) ^ ((row << 1) | row)
    return out


def _thue_morse(k: int) -> int:
    return bin(k).count("1") % 2


def _kolakoski(n: int) -> List[int]:
    out = [1, 2, 2]
    i = 2
    while len(out) < n:
        value = 1 if out[-1] == 2 else 2
        out += [value] * out[i]
        i += 1
    return out[:n]


def _recaman(n: int) -> List[int]:
    out, seen = [0], {0}
    for k in range(1, n):
        x = out[-1] - k
        if x < 0 or x in seen:
            x = out[-1] + k
        out.append(x)
        seen.add(x)
    return out[:n]


def _ulam(n: int) -> List[int]:
    out = [1, 2]
    while len(out) < n:
        last = out[-1]
        ways: Dict[int, int] = {}
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                s = out[i] + out[j]
                if s > last:
                    ways[s] = ways.get(s, 0) + 1
        out.append(min(s for s, c in ways.items() if c == 1))
    return out[:n]


def _look_and_say(n: int) -> List[int]:
    s, out = "1", []
    for _ in range(n):
        out.append(int(s))
        nxt, i = [], 0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]:
                j += 1
            nxt.append(f"{j - i}{s[i]}")
            i = j
        s = "".join(nxt)
    return out


def _stern(n: int) -> List[int]:
    out = [0, 1]
    while len(out) < n:
        k = len(out)
        out.append(out[k // 2] if k % 2 == 0 else out[k // 2] + out[k // 2 + 1])
    return out[:n]


def _happy(k: int) -> bool:
    seen = set()
    while k != 1 and k not in seen:
        seen.add(k)
        k = sum(int(c) ** 2 for c in str(k))
    return k == 1


def _fortunate(n: int) -> List[int]:
    out, primorial = [], 1
    for p in _primes(n):
        primorial *= p
        m = 2
        while not _probable_prime(primorial + m):
            m += 1
        out.append(m)
    return out


def _lucas_lehmer(p: int) -> bool:
    if p == 2:
        return True
    m = (1 << p) - 1
    s = 4
    for _ in range(p - 2):
        x = s * s - 2
        x = (x & m) + (x >> p)
        if x >= m:
            x -= m
        s = x
    return s == 0 or s == m


@lru_cache(maxsize=None)
def _mersenne_exponents(n: int) -> Tuple[int, ...]:
    out: List[int] = []
    limit = 64
    checked = 1
    while len(out) < n:
        for p in _sieve(limit):
            if p <= checked:
                continue
            if _lucas_lehmer(p):
                out.append(p)
                if len(out) == n:
                    break
        checked = limit
        limit *= 2
    return tuple(out[:n])


def _euclid_mullin(n: int) -> List[int]:
    out: List[int] = []
    product = 1
    while len(out) < n:
        m = product + 1
        d = 2
        found = None
        while d * d <= m and d < 10 ** 6:
            if m % d == 0:
                found = d
                break
            d += 1
        if found is None:
            if _probable_prime(m):
                found = m
            else:
                raise ValueError("Euclid-Mullin term beyond the reference's reach")
        out.append(found)
        product *= found
    return out


def _sylvester(n: int) -> List[int]:
    out = [2]
    while len(out) < n:
        out.append(out[-1] * out[-1] - out[-1] + 1)
    return out[:n]


def _hcn(n: int) -> List[int]:
    """Highly composite numbers: the records of d(m), taken over the m whose
    exponents do not increase along 2, 3, 5, ... (every record is such an
    m, and every m has one of them, no larger, with the same d)."""
    ps = _primes(12)
    limit = 2
    while True:
        cands: List[Tuple[int, int]] = []

        def walk(i: int, value: int, cap: int, d: int) -> None:
            cands.append((value, d))
            if i == len(ps):
                return
            v, e = value, 0
            while e < cap:
                v *= ps[i]
                e += 1
                if v > limit:
                    break
                walk(i + 1, v, e, d * (e + 1))

        walk(0, 1, 64, 1)
        cands.sort()
        out, best = [], 0
        for value, d in cands:
            if d > best:
                best = d
                out.append(value)
        if len(out) >= n + 1:
            return out[:n]
        limit *= 4


def _landau(n: int) -> List[int]:
    top = n - 1
    best = [1] * (top + 1)
    for p in _sieve(max(top, 2)):
        new = best[:]
        q = p
        while q <= top:
            for s in range(q, top + 1):
                cand = best[s - q] * q
                if cand > new[s]:
                    new[s] = cand
            q *= p
        best = new
    return best[:n]


def _factorisations(m: int, least: int = 2) -> int:
    count = 1
    d = least
    while d * d <= m:
        if m % d == 0:
            count += _factorisations(m // d, d)
        d += 1
    return count


def _partitions(n: int, distinct: bool = False) -> List[int]:
    table = [1] + [0] * (n - 1)
    for part in range(1, n):
        if distinct:
            for s in range(n - 1, part - 1, -1):
                table[s] += table[s - part]
        else:
            for s in range(part, n):
                table[s] += table[s - part]
    return table[:n]


def _bell(n: int) -> List[int]:
    out = [1]
    while len(out) < n:
        m = len(out)
        out.append(sum(comb(m - 1, k) * out[k] for k in range(m)))
    return out[:n]


def _fubini(n: int) -> List[int]:
    out = [1]
    while len(out) < n:
        m = len(out)
        out.append(sum(comb(m, k) * out[m - k] for k in range(1, m + 1)))
    return out[:n]


def _motzkin(n: int) -> List[int]:
    out = [1, 1]
    while len(out) < n:
        m = len(out)
        out.append(out[m - 1] + sum(out[k] * out[m - 2 - k] for k in range(m - 1)))
    return out[:n]


def _schroeder(n: int) -> List[int]:
    out = [1]
    while len(out) < n:
        m = len(out)
        out.append(out[m - 1] + sum(out[k] * out[m - 1 - k] for k in range(m)))
    return out[:n]


def _little_schroeder(n: int) -> List[int]:
    big = _schroeder(n)
    return [1] + [x // 2 for x in big[1:]]


def _zigzag(n: int) -> List[int]:
    """Euler up/down numbers by the Seidel-Entringer triangle."""
    out = [1]
    row = [1]
    while len(out) < n:
        new = [0]
        for x in reversed(row):
            new.append(new[-1] + x)
        row = new
        out.append(row[-1])
    return out[:n]


def _rooted_trees(n: int) -> List[int]:
    a = [0, 1]
    while len(a) < n:
        m = len(a) - 1     # compute a(m + 1)
        total = 0
        for k in range(1, m + 1):
            s = sum(d * a[d] for d in _divisors(k))
            total += s * a[m - k + 1]
        a.append(total // m)
    return a[:n]


def _necklaces(m: int) -> int:
    if m == 0:
        return 1
    return sum(_phi(d) * 2 ** (m // d) for d in _divisors(m)) // m


def _runs(k: int) -> int:
    if k == 0:
        return 0
    b = bin(k)[2:]
    return 1 + sum(1 for i in range(1, len(b)) if b[i] != b[i - 1])


def _perfect_power(k: int) -> bool:
    if k == 1:
        return True
    e = 2
    while (1 << e) <= k:
        r = _root_floor(k, e)
        if r ** e == k:
            return True
        e += 1
    return False


def _root_floor(k: int, e: int) -> int:
    """The integer ``r`` with ``r**e <= k < (r+1)**e``."""
    lo, hi = 1, 1
    while hi ** e <= k:
        hi *= 2
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if mid ** e <= k:
            lo = mid
        else:
            hi = mid
    return lo


def _pascal(n: int) -> List[int]:
    out, r = [], 0
    while len(out) < n:
        out += [comb(r, k) for k in range(r + 1)]
        r += 1
    return out[:n]


def _abelian_groups(m: int) -> int:
    parts = _partitions(64)
    out = 1
    for e in _factor(m).values():
        out *= parts[e]
    return out


def _fermat_primes(n: int) -> List[int]:
    """The Fermat primes known: F0..F4 (F5..F32 are known composite)."""
    out = [2 ** (2 ** k) + 1 for k in range(5)]
    if not all(_probable_prime(x) for x in out):
        raise ValueError("a Fermat prime failed its primality test")
    return out[:n]


def _wieferich(n: int) -> List[int]:
    """Wieferich primes below 10**5 (two: 1093 and 3511)."""
    return [p for p in _sieve(10 ** 5) if pow(2, p - 1, p * p) == 1][:n]


# ---------------------------------------------------------------------------
# The reference table
# ---------------------------------------------------------------------------

Generator = Callable[[int], List[int]]

#: identifier -> (what the OEIS entry is, generator of its first terms from
#: its OEIS offset).
REFERENCE: Dict[str, Tuple[str, Generator]] = {
    # constant and simple sequences
    "A000004": ("the zero sequence", lambda n: [0] * n),
    "A000007": ("the characteristic function of 0", lambda n: [1] + [0] * (n - 1)),
    "A000012": ("the all-ones sequence", lambda n: [1] * n),
    "A000027": ("the positive integers", _seq(lambda k: k, 1)),
    "A001477": ("the nonnegative integers", _seq(lambda k: k, 0)),
    "A005408": ("the odd numbers", _seq(lambda k: 2 * k + 1, 0)),
    "A005843": ("the even numbers", _seq(lambda k: 2 * k, 0)),
    "A004526": ("floor(n/2)", _seq(lambda k: k // 2, 0)),
    # powers and factorials
    "A000079": ("powers of 2", _seq(lambda k: 2 ** k, 0)),
    "A000244": ("powers of 3", _seq(lambda k: 3 ** k, 0)),
    "A000302": ("powers of 4", _seq(lambda k: 4 ** k, 0)),
    "A000351": ("powers of 5", _seq(lambda k: 5 ** k, 0)),
    "A000400": ("powers of 6", _seq(lambda k: 6 ** k, 0)),
    "A000420": ("powers of 7", _seq(lambda k: 7 ** k, 0)),
    "A001020": ("powers of 8", _seq(lambda k: 8 ** k, 0)),
    "A001021": ("powers of 9", _seq(lambda k: 9 ** k, 0)),
    "A011557": ("powers of 10", _seq(lambda k: 10 ** k, 0)),
    "A000225": ("2^n - 1", _seq(lambda k: 2 ** k - 1, 0)),
    "A000051": ("2^n + 1", _seq(lambda k: 2 ** k + 1, 0)),
    "A000142": ("n!", _seq(factorial, 0)),
    "A000312": ("n^n", _seq(lambda k: k ** k, 0)),
    "A000178": ("superfactorials", _seq(lambda k: _prod(factorial(i) for i in range(k + 1)), 0)),
    "A000169": ("n^(n-1)", _seq(lambda k: k ** (k - 1), 1)),
    "A001147": ("double factorials of odd numbers", _seq(lambda k: _prod(range(1, 2 * k, 2)), 0)),
    "A003261": ("Woodall numbers n*2^n - 1", _seq(lambda k: k * 2 ** k - 1, 1)),
    # polynomial sequences
    "A000290": ("the squares", _seq(lambda k: k * k, 0)),
    "A000578": ("the cubes", _seq(lambda k: k ** 3, 0)),
    "A000583": ("fourth powers", _seq(lambda k: k ** 4, 0)),
    "A001014": ("sixth powers", _seq(lambda k: k ** 6, 0)),
    "A000217": ("triangular numbers", _seq(lambda k: k * (k + 1) // 2, 0)),
    "A000292": ("tetrahedral numbers", _seq(lambda k: comb(k + 2, 3), 0)),
    "A000330": ("square pyramidal numbers", _seq(lambda k: k * (k + 1) * (2 * k + 1) // 6, 0)),
    "A000332": ("binomial(n,4)", _seq(lambda k: comb(k, 4), 0)),
    "A000389": ("binomial(n,5)", _seq(lambda k: comb(k, 5), 0)),
    "A000384": ("hexagonal numbers n(2n-1)", _seq(lambda k: k * (2 * k - 1), 0)),
    "A000326": ("pentagonal numbers n(3n-1)/2", _seq(lambda k: k * (3 * k - 1) // 2, 0)),
    "A000566": ("heptagonal numbers n(5n-3)/2", _seq(lambda k: k * (5 * k - 3) // 2, 0)),
    "A000567": ("octagonal numbers n(3n-2)", _seq(lambda k: k * (3 * k - 2), 0)),
    "A001318": ("generalized pentagonal numbers",
                _seq(lambda k: (lambda m: m * (3 * m - 1) // 2)(
                    (k + 1) // 2 if k % 2 else -(k // 2)), 0)),
    "A000096": ("n(n+3)/2", _seq(lambda k: k * (k + 3) // 2, 0)),
    "A002378": ("oblong numbers n(n+1)", _seq(lambda k: k * (k + 1), 0)),
    "A000447": ("sums of the first n odd squares", _seq(lambda k: k * (2 * k - 1) * (2 * k + 1) // 3, 0)),
    "A005898": ("centred cube numbers n^3 + (n+1)^3", _seq(lambda k: k ** 3 + (k + 1) ** 3, 0)),
    "A005891": ("centred pentagonal numbers", _seq(lambda k: (5 * k * k + 5 * k + 2) // 2, 0)),
    "A005563": ("n(n+2)", _seq(lambda k: k * (k + 2), 0)),
    "A006003": ("n(n^2+1)/2", _seq(lambda k: k * (k * k + 1) // 2, 0)),
    "A000093": ("floor(n^(3/2))", _seq(lambda k: isqrt(k ** 3), 0)),
    # primes and divisors
    "A000040": ("the primes", _primes),
    "A002808": ("the composite numbers", _filtered(lambda k: not _is_prime_small(k), 4)),
    "A000720": ("pi(n)", _seq(lambda k: sum(1 for p in _sieve(k)), 1)),
    "A001223": ("prime gaps", lambda n: [b - a for a, b in zip(_primes(n + 1), _primes(n + 1)[1:])]),
    "A001359": ("lesser of twin primes", _filtered(lambda k: _is_prime_small(k) and _is_prime_small(k + 2), 2)),
    "A006512": ("greater of twin primes", _filtered(lambda k: _is_prime_small(k) and _is_prime_small(k - 2), 3)),
    "A005384": ("Sophie Germain primes", _filtered(lambda k: _is_prime_small(k) and _is_prime_small(2 * k + 1), 2)),
    "A007504": ("sum of the first n primes", lambda n: [sum(_primes(k)) for k in range(n)]),
    "A002110": ("primorials", lambda n: [_prod(_primes(k)) for k in range(n)]),
    "A000043": ("Mersenne exponents", lambda n: list(_mersenne_exponents(n))),
    "A000668": ("Mersenne primes", lambda n: [2 ** p - 1 for p in _mersenne_exponents(n)]),
    "A000396": ("perfect numbers", lambda n: [2 ** (p - 1) * (2 ** p - 1) for p in _mersenne_exponents(n)]),
    "A000215": ("Fermat numbers", _seq(lambda k: 2 ** (2 ** k) + 1, 0)),
    "A019434": ("Fermat primes", _fermat_primes),
    "A001220": ("Wieferich primes", _wieferich),
    "A000945": ("Euclid-Mullin sequence", _euclid_mullin),
    "A000058": ("Sylvester's sequence", _sylvester),
    "A005235": ("Fortunate numbers", _fortunate),
    "A003418": ("lcm(1..n)", lambda n: [_lcm_upto(k) for k in range(n)]),
    "A002182": ("highly composite numbers", _hcn),
    "A000793": ("Landau's function", _landau),
    "A002473": ("7-smooth numbers", _filtered(lambda k: set(_factor(k)) <= {2, 3, 5, 7}, 1)),
    "A005117": ("squarefree numbers", _filtered(lambda k: all(e == 1 for e in _factor(k).values()), 1)),
    "A001694": ("powerful numbers", _filtered(lambda k: all(e >= 2 for e in _factor(k).values()), 1)),
    "A001597": ("perfect powers", _filtered(_perfect_power, 1)),
    "A000037": ("the nonsquares", _filtered(lambda k: isqrt(k) ** 2 != k, 1)),
    "A000005": ("d(n)", _seq(lambda k: len(_divisors(k)), 1)),
    "A000203": ("sigma(n)", _seq(lambda k: sum(_divisors(k)), 1)),
    "A000010": ("Euler's phi(n)", _seq(_phi, 1)),
    "A001221": ("omega(n)", _seq(lambda k: len(_factor(k)), 1)),
    "A001222": ("bigomega(n)", _seq(lambda k: sum(_factor(k).values()), 1)),
    "A001414": ("sopfr(n)", _seq(lambda k: sum(p * e for p, e in _factor(k).items()), 1)),
    "A001055": ("unordered factorisations of n", _seq(_factorisations, 1)),
    # recurrences
    "A000045": ("Fibonacci numbers", lambda n: _linear([0, 1], lambda a: a[-1] + a[-2], n)),
    "A000032": ("Lucas numbers from L(0)", lambda n: _linear([2, 1], lambda a: a[-1] + a[-2], n)),
    "A000204": ("Lucas numbers from L(1)", lambda n: _linear([1, 3], lambda a: a[-1] + a[-2], n)),
    "A001045": ("Jacobsthal numbers", lambda n: _linear([0, 1], lambda a: a[-1] + 2 * a[-2], n)),
    "A001608": ("Perrin sequence", lambda n: _linear([3, 0, 2], lambda a: a[-2] + a[-3], n)),
    "A000930": ("Narayana's cows", lambda n: _linear([1, 1, 1], lambda a: a[-1] + a[-3], n)),
    "A000931": ("Padovan sequence", lambda n: _linear([1, 0, 0], lambda a: a[-2] + a[-3], n)),
    "A000073": ("tribonacci numbers", lambda n: _linear([0, 0, 1], lambda a: a[-1] + a[-2] + a[-3], n)),
    "A000129": ("Pell numbers", lambda n: _linear([0, 1], lambda a: 2 * a[-1] + a[-2], n)),
    "A001353": ("a(n) = 4a(n-1) - a(n-2)", lambda n: _linear([0, 1], lambda a: 4 * a[-1] - a[-2], n)),
    "A001109": ("square triangular roots", lambda n: _linear([0, 1], lambda a: 6 * a[-1] - a[-2], n)),
    # combinatorics
    "A000041": ("partitions of n", lambda n: _partitions(n)),
    "A000009": ("partitions of n into distinct parts", lambda n: _partitions(n, True)),
    "A000108": ("Catalan numbers", _seq(lambda k: comb(2 * k, k) // (k + 1), 0)),
    "A000110": ("Bell numbers", _bell),
    "A000670": ("Fubini numbers", _fubini),
    "A000085": ("involutions", lambda n: _linear([1, 1], lambda a: a[-1] + (len(a) - 1) * a[-2], n)),
    "A000166": ("derangements", lambda n: _linear([1, 0], lambda a: (len(a) - 1) * (a[-1] + a[-2]), n)),
    "A001006": ("Motzkin numbers", _motzkin),
    "A006318": ("large Schroeder numbers", _schroeder),
    "A001003": ("little Schroeder numbers", _little_schroeder),
    "A000111": ("Euler up/down numbers", _zigzag),
    "A001850": ("central Delannoy numbers", _seq(lambda k: sum(comb(k, i) * comb(k + i, i) for i in range(k + 1)), 0)),
    "A001405": ("binomial(n, floor(n/2))", _seq(lambda k: comb(k, k // 2), 0)),
    "A007318": ("Pascal's triangle by rows", _pascal),
    "A000081": ("unlabelled rooted trees", _rooted_trees),
    "A000031": ("binary necklaces", _seq(_necklaces, 0)),
    "A000688": ("abelian groups of order n", _seq(_abelian_groups, 1)),
    # recreational and digital
    "A005132": ("Recaman's sequence", _recaman),
    "A000002": ("Kolakoski sequence", lambda n: _kolakoski(n)),
    "A005150": ("look-and-say", _look_and_say),
    "A002858": ("Ulam numbers", _ulam),
    "A007770": ("happy numbers", _filtered(_happy, 1)),
    "A002487": ("Stern's diatomic sequence", _stern),
    "A010060": ("Thue-Morse sequence", _seq(_thue_morse, 0)),
    "A010059": ("1 - Thue-Morse", _seq(lambda k: 1 - _thue_morse(k), 0)),
    "A001969": ("evil numbers", _filtered(lambda k: _thue_morse(k) == 0, 0)),
    "A000069": ("odious numbers", _filtered(lambda k: _thue_morse(k) == 1, 0)),
    "A000120": ("binary weight of n", _seq(lambda k: bin(k).count("1"), 0)),
    "A005811": ("runs in the binary expansion of n", _seq(_runs, 0)),
    "A001511": ("the ruler function", _seq(lambda k: ((2 * k) & -(2 * k)).bit_length() - 1, 1)),
    "A006519": ("highest power of 2 dividing n", _seq(lambda k: k & -k, 1)),
    "A002113": ("palindromes in base 10", _filtered(lambda k: str(k) == str(k)[::-1], 0)),
    "A007953": ("digit sum of n", _seq(lambda k: sum(int(c) for c in str(k)), 0)),
    "A000201": ("lower Wythoff sequence", _seq(lambda k: (k + isqrt(5 * k * k)) // 2, 1)),
    "A001950": ("upper Wythoff sequence", _seq(lambda k: (k + isqrt(5 * k * k)) // 2 + k, 1)),
    "A001951": ("floor(n*sqrt 2)", _seq(lambda k: isqrt(2 * k * k), 1)),
    "A001952": ("floor(n*(2 + sqrt 2))", _seq(lambda k: 2 * k + isqrt(2 * k * k), 1)),
    "A051023": ("Rule 30 centre column", _rule30_centre),
    # constants
    "A001113": ("digits of e", _e_digits),
    "A000796": ("digits of pi", _pi_digits),
    "A002193": ("digits of sqrt 2", lambda n: _sqrt_digits(2, n)),
    "A002194": ("digits of sqrt 3", lambda n: _sqrt_digits(3, n)),
    "A001622": ("digits of the golden ratio", _phi_digits),
    "A002162": ("digits of ln 2", _ln2_digits),
    "A001620": ("digits of Euler's gamma", _gamma_digits),
    "A006752": ("digits of Catalan's constant", _catalan_digits),
    "A003417": ("continued fraction of e", _e_cf),
    "A001203": ("continued fraction of pi", _pi_cf),
    "A040000": ("continued fraction of sqrt 2", lambda n: [1] + [2] * (n - 1)),
    # literal lists (not recomputable here)
    "A000001": ("groups of order n (literal, n = 1..24)", lambda n: [
        1, 1, 1, 2, 1, 2, 1, 5, 2, 2, 1, 5, 1, 2, 1, 14, 1, 5, 1, 5, 2, 2, 1, 15][:n]),
    "A000088": ("graphs on n nodes (literal, n = 0..11)", lambda n: [
        1, 1, 2, 4, 11, 34, 156, 1044, 12346, 274668, 12005168, 1018997864][:n]),
    "A001034": ("orders of noncyclic simple groups (literal, first 8)", lambda n: [
        60, 168, 360, 504, 660, 1092, 2448, 2520][:n]),
}


def _prod(values: Iterable[int]) -> int:
    out = 1
    for v in values:
        out *= v
    return out


def _lcm_upto(k: int) -> int:
    out = 1
    for i in range(1, k + 1):
        out = lcm(out, i)
    return out


# ---------------------------------------------------------------------------
# The audit
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def reference_terms(oeis_id: str, n: int) -> Tuple[int, ...]:
    """The reference's first ``n`` terms of ``oeis_id`` (fewer for a literal
    or bounded list, or where the generator cannot reach); ``()`` without a
    reference."""
    ref = REFERENCE.get(oeis_id)
    if ref is None:
        return ()
    try:
        return tuple(ref[1](n))
    except ValueError:
        return ()


def audit_entry(oeis_id: str, terms: Sequence[int]) -> Dict[str, object]:
    """``{"id", "verdict", "start", "reason"}`` for one supplied entry.

    The stored terms are compared with the reference's first terms; when they
    are not those, with the reference's runs starting at ``1 .. MAX_SHIFT``
    (asking the reference for ``MAX_SHIFT`` more terms only then, since some
    references are costly or bounded)."""
    stored = tuple(terms)
    if oeis_id not in REFERENCE:
        return {"id": oeis_id, "verdict": NOT_RECOMPUTED, "start": None,
                "reason": "no independent reference for this identifier"}
    ref = reference_terms(oeis_id, len(stored))
    if ref == stored:
        return {"id": oeis_id, "verdict": VERIFIED, "start": 0,
                "reason": f"the stored terms are the reference's first {len(stored)}"}
    longer = reference_terms(oeis_id, len(stored) + MAX_SHIFT)
    if len(longer) > len(ref):
        ref = longer
    for j in range(1, min(MAX_SHIFT, len(ref) - len(stored)) + 1):
        if ref[j:j + len(stored)] == stored:
            return {"id": oeis_id, "verdict": VERIFIED, "start": j,
                    "reason": f"the stored terms are the reference's terms "
                              f"{j}..{j + len(stored) - 1}"}
    if len(ref) < len(stored) and stored[:len(ref)] == ref:
        return {"id": oeis_id, "verdict": SHORT, "start": None,
                "reason": f"the reference has {len(ref)} terms and agrees with the "
                          f"first {len(ref)} of the {len(stored)} stored"}
    first = next((i for i, (a, b) in enumerate(zip(stored, ref)) if a != b),
                 min(len(stored), len(ref)))
    got = stored[first] if first < len(stored) else None
    want = ref[first] if first < len(ref) else None
    return {"id": oeis_id, "verdict": DISAGREES, "start": None,
            "reason": f"{REFERENCE[oeis_id][0]}: stored term {first} is {got}, "
                      f"the reference's is {want}"}


def audit_entries(entries: Iterable[Tuple[str, Sequence[int]]]) -> List[Dict[str, object]]:
    return [audit_entry(oid, terms) for oid, terms in entries]


def audit_supplied() -> Dict[str, object]:
    """The audit of every supplied sequence entry: the 183 of the Integer
    Wheel's seed and the 5 group-theory entries of the Monster Wheel's."""
    from .oeis_seed import CURATED_OEIS
    from .cfsg_seed import GROUP_THEORY_OEIS
    integer = audit_entries((e[0], e[2]) for e in CURATED_OEIS)
    group = audit_entries((e[0], e[2]) for e in GROUP_THEORY_OEIS)
    counts: Dict[str, int] = {}
    for row in integer + group:
        counts[str(row["verdict"])] = counts.get(str(row["verdict"]), 0) + 1
    return {
        "integer": integer,
        "group_theory": group,
        "counts": counts,
        "admitted_integer": tuple(r["id"] for r in integer if r["verdict"] == VERIFIED),
        "admitted_group_theory": tuple(r["id"] for r in group if r["verdict"] == VERIFIED),
    }


def admitted_ids() -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """``(integer, group_theory)``: the ids the live audit admits, in the
    supplied order."""
    a = audit_supplied()
    return a["admitted_integer"], a["admitted_group_theory"]  # type: ignore[return-value]


#: The Integer Wheel entries the audit admits, in the supplied order (frozen
#: from :func:`admitted_ids` on 31 October 2026; ``tests/test_integer_wheel.py``
#: fails if the live audit disagrees).
ADMITTED_IDS: Tuple[str, ...] = (
    "A000012", "A000027", "A001477", "A000079", "A000244", "A000302", "A000351",
    "A000400", "A000420", "A001020", "A001021", "A011557", "A000142", "A000312",
    "A000290", "A000578", "A000217", "A000292", "A000330", "A000332", "A000384",
    "A000326", "A001318", "A000583", "A001014", "A001414", "A005408", "A005843",
    "A000040", "A002808", "A001223", "A001359", "A006512", "A000043", "A000668",
    "A000225", "A000215", "A019434", "A002110", "A000945", "A002182", "A002858",
    "A003418", "A002473", "A005384", "A005117", "A000045", "A000032", "A000204",
    "A001045", "A001608", "A000930", "A000931", "A000073", "A000041", "A000203",
    "A000005", "A000010", "A001221", "A000108", "A000110", "A000085", "A000166",
    "A001006", "A001147", "A000088", "A001405", "A007318", "A005132", "A000002",
    "A005150", "A010060", "A001969", "A000069", "A000120", "A002113", "A001511",
    "A006519", "A001113", "A000796", "A001622", "A002162", "A001620", "A010059",
    "A002378", "A001055", "A000037", "A000396", "A000004", "A004526", "A003417",
    "A001203", "A000129", "A001353", "A001109", "A007770", "A003261", "A000058",
    "A000007", "A000031", "A000093", "A000096", "A002487", "A000001", "A007953",
    "A000201", "A001950",
)

#: The Monster Wheel's group-theory entries the audit admits.
ADMITTED_GROUP_THEORY_IDS: Tuple[str, ...] = (
    "A000001", "A000688",
)
