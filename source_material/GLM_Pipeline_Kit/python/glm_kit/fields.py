"""Finite-field puncture/spin table (Lean: GLMKit/Fields.lean).

Elements of F_{p^k} are tuples of k coefficients over F_p, reduced by a monic irreducible.
"""
from __future__ import annotations
from itertools import product
from typing import Dict, List, Tuple

# monic irreducible polynomials, coefficients c_0..c_{k-1} of x^k + ... (x^k = -sum c_i x^i)
IRREDUCIBLE = {
    (2, 2): (1, 1),      # x^2 + x + 1
    (2, 3): (1, 1, 0),   # x^3 + x + 1
    (3, 2): (1, 0),      # x^2 + 1   (alpha^2 = -1, alpha has order 4)
}


def _mul(a, b, p, k, red):
    prod = [0] * (2 * k - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            prod[i + j] = (prod[i + j] + x * y) % p
    for d in range(2 * k - 2, k - 1, -1):
        c = prod[d]
        if c:
            prod[d] = 0
            for i in range(k):
                prod[d - k + i] = (prod[d - k + i] - c * red[i]) % p
    return tuple(prod[:k])


def field(p: int, k: int = 1):
    red = IRREDUCIBLE.get((p, k), ())
    elems = list(product(range(p), repeat=k))
    one = tuple([1] + [0] * (k - 1))
    mul = (lambda a, b: _mul(a, b, p, k, red)) if k > 1 else (lambda a, b: ((a[0] * b[0]) % p,))
    return elems, one, mul


def order(x, one, mul) -> int:
    cur, n = x, 1
    while cur != one:
        cur = mul(cur, x)
        n += 1
        if n > 1000:
            return 0
    return n


def table() -> List[Dict]:
    rows = []
    for (p, k) in [(2, 1), (3, 1), (2, 2), (5, 1), (7, 1), (2, 3), (3, 2)]:
        elems, one, mul = field(p, k)
        zero = tuple([0] * k)
        units = [e for e in elems if e != zero]
        assert all(any(mul(u, v) == one for v in units) for u in units), "not a field"
        orders = sorted({order(u, one, mul) for u in units})
        alpha = tuple([0, 1] + [0] * (k - 2)) if k > 1 else ((2 % p),)
        rows.append({
            "field": f"F_{p**k}", "q": p ** k, "char": p, "units": len(units),
            "spin_element": "alpha" if k > 1 else "2",
            "spin_order": 0 if alpha == zero else order(alpha, one, mul),
            "max_unit_order": max(orders),            # = q - 1 (cyclic group)
        })
    return rows


def zmod6_zero_divisors() -> List[Tuple[int, int]]:
    return [(a, b) for a in range(1, 6) for b in range(1, 6) if (a * b) % 6 == 0]
