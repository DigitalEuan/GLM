"""``glm_universal.wheels.lean_wheel_data`` -- what the two Lean files of the
Integer and Monster Wheels state, read from their source text.

*Created 31 October 2026 (intake of glm_wheels_bundle; directive D22;
``studies/INTEGER_WHEEL_STUDY.md``, marks L and S1).*

The Lean half of the intake states, with proofs, the finite facts the Python
wheels rest on:

* ``Wheels/IntegerWheel.lean`` (namespace ``GLM.IntegerWheel``) -- eight
  ``def termsAxxxxxx : List ℕ := [...]`` lists, each proved equal to its
  closed form (``termsA000045_eq`` ...);
* ``Wheels/SporadicOrders.lean`` (namespace ``GLM.SporadicOrders``) -- the
  26 sporadic groups and their orders (``sporadicOrders``), and for each a
  theorem ``order_<name> : (N : ℕ) = 2 ^ a * 3 ^ b * ...``.

This module reads those statements back out of the source text (no Lean is
run here; the build is the owner's, ``scripts/rebuild_lean.sh``) so that the
tests and the study can compare them with the Python data, and so that S1 has
a reference for the group-side identifiers that does not come from the
supplied ``cfsg_seed.py``: the order of a group is recomputed as the product
of the prime powers of its ``order_<name>`` theorem.  Paths come from
:func:`glm_universal.constants.lean_file`.  A file that is missing or does not
parse gives empty results, so a reader reports the absence (never a guess).
Integers only (directive D7).
"""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from ..constants import lean_file

__all__ = [
    "INTEGER_WHEEL_LEAN", "SPORADIC_ORDERS_LEAN", "lean_text",
    "integer_wheel_terms", "sporadic_orders", "sporadic_factorisations",
    "parse_product",
]

#: The two Lean files, as names :func:`glm_universal.constants.lean_file`
#: resolves.
INTEGER_WHEEL_LEAN = "Wheels/IntegerWheel.lean"
SPORADIC_ORDERS_LEAN = "Wheels/SporadicOrders.lean"

_TERMS = re.compile(r"\bdef\s+terms(A\d{6})\s*:\s*List\s+ℕ\s*:=\s*\[([^\]]*)\]")
_ORDERS = re.compile(
    r"\bdef\s+sporadicOrders\s*:\s*List\s*\(\s*String\s*×\s*ℕ\s*\)\s*:=\s*\[(.*?)\]\s*\n\s*\n",
    re.DOTALL)
_PAIR = re.compile(r"\(\s*\"([^\"]+)\"\s*,\s*(\d+)\s*\)")
_ORDER_THEOREM = re.compile(
    r"^theorem\s+order_([\w']+)\s*:\s*\(\s*(\d+)\s*:\s*ℕ\s*\)\s*=\s*(.*?):=\s*by",
    re.DOTALL | re.MULTILINE)


def lean_text(name: str) -> str:
    """The source text of a Lean file of the development, ``""`` if absent."""
    path = lean_file(name)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def integer_wheel_terms() -> Dict[str, Tuple[int, ...]]:
    """``{oeis_id: terms}`` for every ``def termsAxxxxxx : List ℕ := [...]``
    of ``Wheels/IntegerWheel.lean``."""
    out: Dict[str, Tuple[int, ...]] = {}
    for m in _TERMS.finditer(lean_text(INTEGER_WHEEL_LEAN)):
        body = m.group(2).strip()
        out[m.group(1)] = tuple(int(t) for t in body.split(",")) if body else ()
    return out


def sporadic_orders() -> Tuple[Tuple[str, int], ...]:
    """The list ``sporadicOrders`` of ``Wheels/SporadicOrders.lean``, in its
    order: ``(name, order)`` pairs."""
    m = _ORDERS.search(lean_text(SPORADIC_ORDERS_LEAN))
    if not m:
        return ()
    return tuple((name, int(order)) for name, order in _PAIR.findall(m.group(1)))


def parse_product(expr: str) -> Optional[Tuple[Tuple[int, int], ...]]:
    """``((p, e), ...)`` for a Lean product of prime powers such as
    ``2 ^ 4 * 3 ^ 2 * 5 * 11``, in the order written; ``None`` when the text
    is not such a product."""
    factors = []
    for part in expr.split("*"):
        m = re.fullmatch(r"\s*(\d+)\s*(?:\^\s*(\d+))?\s*", part)
        if not m:
            return None
        factors.append((int(m.group(1)), int(m.group(2)) if m.group(2) else 1))
    return tuple(factors)


def sporadic_factorisations() -> Dict[str, Tuple[int, Tuple[Tuple[int, int], ...]]]:
    """``{name: (stated_order, ((p, e), ...))}`` for every theorem
    ``order_<name> : (N : ℕ) = p ^ e * ...`` of ``Wheels/SporadicOrders.lean``
    (the left-hand side as written, and the right-hand side's prime powers)."""
    out: Dict[str, Tuple[int, Tuple[Tuple[int, int], ...]]] = {}
    for m in _ORDER_THEOREM.finditer(lean_text(SPORADIC_ORDERS_LEAN)):
        factors = parse_product(" ".join(m.group(3).split()))
        if factors is None:
            continue
        out[m.group(1)] = (int(m.group(2)), factors)
    return out
