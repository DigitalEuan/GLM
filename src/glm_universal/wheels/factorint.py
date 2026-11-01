"""``glm_universal.wheels.factorint`` -- exact prime factorisation for the
Integer and Monster Wheels.

*Taken 31 October 2026 (intake of glm_wheels_bundle; directive D22) and installed
provisionally, by the owner's decision, until the owner's Lean build confirms the
wheels (``wheels/_data/provisional.json``).*
Ported from ``source_material/ToDo/glm_wheels_bundle/factorint_compat.py``,
the exact fallback the repository's intake check added to the bundle when
``sympy`` was found missing.  The package takes only the exact branch: trial
division by every integer below 1000, then a deterministic Miller-Rabin test
(the first thirteen primes as bases, which is a proof of primality below
3.3 * 10**24 and a strong probable-prime test above) and Pollard's rho on what
is left.  Integers only; nothing here constructs a float (directive D7).
"""
from __future__ import annotations

from math import gcd
from typing import Dict, List

__all__ = ["is_probable_prime", "factorint", "smallest_prime_factor"]

_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)


def is_probable_prime(n: int) -> bool:
    """Miller-Rabin with the first thirteen primes as bases (exact below
    3317044064679887385961981, a strong probable-prime test above)."""
    if n < 2:
        return False
    for p in _MR_BASES:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _MR_BASES:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _rho(n: int) -> int:
    if n % 2 == 0:
        return 2
    c = 1
    while True:
        x = y = 2
        d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = gcd(abs(x - y), n)
        if d != n:
            return d
        c += 1


def factorint(n: int) -> Dict[int, int]:
    """The prime factorisation of ``n`` as ``{prime: exponent}``, primes in
    increasing order (``{}`` for ``n < 2``)."""
    n = int(n)
    out: Dict[int, int] = {}
    if n < 2:
        return out
    for p in range(2, 1000):
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        if n == 1:
            return dict(sorted(out.items()))
    stack: List[int] = [n]
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if is_probable_prime(m):
            out[m] = out.get(m, 0) + 1
            continue
        d = _rho(m)
        stack.extend((d, m // d))
    return dict(sorted(out.items()))


def smallest_prime_factor(n: int) -> int:
    """The least prime dividing ``n`` (``n >= 2``)."""
    if n < 2:
        raise ValueError("n must be at least 2")
    return min(factorint(n))
