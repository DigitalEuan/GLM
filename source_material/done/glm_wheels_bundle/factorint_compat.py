"""``factorint`` with or without sympy.

Added by the repository's intake check (see ``source_material/INTAKE.yaml``,
record ``glm_wheels_bundle``): the bundle imported ``sympy.factorint`` in six
places, and sympy is not part of the GLM's standard-library environment, so
``default_wheel()`` failed before any test ran.  When sympy is installed its
``factorint`` is used unchanged; otherwise this exact, integer-only fallback
(trial division by every integer below 1000, then deterministic Miller-Rabin
and Pollard rho on what is left) returns the same ``{prime: exponent}`` dict.
"""
from __future__ import annotations

from math import gcd
from typing import Dict

try:  # pragma: no cover - depends on the environment
    from sympy import factorint as _sympy_factorint
except ImportError:  # pragma: no cover
    _sympy_factorint = None

_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)


def _is_prime(n: int) -> bool:
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


def _fallback_factorint(n: int) -> Dict[int, int]:
    n = int(n)
    out: Dict[int, int] = {}
    if n < 2:
        return out
    for p in range(2, 1000):
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        if n == 1:
            return out
    stack = [n]
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if _is_prime(m):
            out[m] = out.get(m, 0) + 1
            continue
        d = _rho(m)
        stack.extend((d, m // d))
    return dict(sorted(out.items()))


def factorint(n: int) -> Dict[int, int]:
    """The prime factorisation of ``n`` as ``{prime: exponent}``."""
    if _sympy_factorint is not None:
        return dict(_sympy_factorint(n))
    return _fallback_factorint(n)
