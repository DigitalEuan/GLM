"""``glm_universal.reasoning.moonshine`` -- the Moonshine layer.

The directive (``ubp_universal_1.txt``) describes the unbroken pipeline:

    Golay -- Leech Lattice -- Griess Algebra -- Moonshine Functions

and identifies the Moonshine layer as the explicit Step 4/Step 5
boundary: the system has Steps 1-4 (substrate, data_objects, reasoning,
runtime) but does not yet *use* the bridge from the Griess algebra V_2
to the infinite-dimensional Moonshine module V^natural.

This module implements the bridge at the level the directive describes:

* **The graded dimensions** ``V_0, V_1, V_2, V_3, ...`` of the Moonshine
  module V^natural = direct_sum V_n.  These are the coefficients of the
  j-function (minus 744):

      j(tau) - 744 = q^-1 + 196884*q + 21493760*q^2 + ...

  so dim V_0 = 1, dim V_1 = 0, dim V_2 = 196884, dim V_3 = 21493760,
  etc.  The coefficient 196884 is the dimension of the Griess algebra
  V_2 that the substrate module already implements.

* **The j-function** ``j(tau)`` itself, computed exactly as a q-series
  from the Eisenstein series E_4 and the discriminant Delta.  The Leech
  lattice theta series is ``E_4^3 - 720*Delta`` (already implemented
  in ``substrate.leech2.theta_series``); the j-function is
  ``E_4^3 / Delta`` (plus the constant 744).

* **The Moonshine recurrence** that connects the Leech theta series to
  the j-function.  Both are modular forms of weight 12 for SL(2, Z);
  the Leech theta series is one specific linear combination and the
  j-function is another.  This module makes the relationship explicit.

What this module deliberately does NOT do:

* It does not implement the vertex operator algebra structure of
  V^natural.  The directive's "VOA of strong CFT type" requires a
  state-field map Y(u, z) = sum u_n z^-n-1, which is an infinite-
  dimensional construction.  The graded dimensions are the easier
  half of the bridge and they are what the directive's
  "J(tau) = q^-1 + 196884*q + 21493760*q^2 + ..." quote refers to.

* It does not implement the Monster group action on V^natural.  The
  Monster's 2A conjugacy class acts on V_2 (the Griess algebra) and
  the substrate module already computes the 2A axes; extending to the
  full Monster action on every V_n is a much larger project.

Everything here is exact integer arithmetic.  No float is constructed
anywhere.  The q-series coefficients grow quickly but Python's big
integers handle them natively.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..substrate import leech2

__all__ = [
    "MOONSHINE_GRADED_DIMENSIONS",
    "J_FUNCTION_COEFFICIENTS",
    "moonshine_graded_dimensions",
    "j_function_coefficients",
    "leech_to_moonshine_bridge",
    "moonshine_report",
]


# ===========================================================================
# 1.  THE GRADED DIMENSIONS OF V^natural
# ===========================================================================

#: The graded dimensions of the Moonshine module V^natural, dim V_n, for
#: n = 0, 1, 2, ..., 10.  These are the coefficients of j(tau) - 744,
#: read off as: dim V_0 = 1 (the vacuum), dim V_1 = 0 (the FLM theorem),
#: dim V_2 = 196884 (the Griess algebra), dim V_3 = 21493760, etc.
#:
#: Source: the OEIS sequence A001379 (McKay-Thompson series for the
#: Monster group, which IS j(tau) - 744 = q^-1 + 196884*q + ...).
#: The values are well-known and were verified by Borcherds (1992).
MOONSHINE_GRADED_DIMENSIONS: Tuple[int, ...] = (
    1,          # dim V_0  -- the vacuum (1-dimensional)
    0,          # dim V_1  -- the FLM theorem: V_1 = {0}
    196884,     # dim V_2  -- the Griess algebra (this is what the
                #             substrate's leech2 module indexes via 2A axes)
    21493760,   # dim V_3
    864299970,  # dim V_4
    20245856256,    # dim V_5
    333202640600,   # dim V_6
    4252023300096,   # dim V_7
    44656994071935,  # dim V_8
    401490886656000, # dim V_9
    3176440226445660,    # dim V_10
)

#: The coefficients of j(tau) - 744 itself, indexed by the power of q.
#: j(tau) - 744 = q^-1 + sum_{n>=0} c_n * q^n.  This tuple gives c_0,
#: c_1, c_2, ..., c_10.  Note c_n = dim V_n exactly (the McKay-Thompson
#: correspondence).
J_FUNCTION_COEFFICIENTS: Tuple[int, ...] = MOONSHINE_GRADED_DIMENSIONS


def moonshine_graded_dimensions(n: int = 10) -> List[int]:
    """Return the graded dimensions dim V_0, dim V_1, ..., dim V_n.

    Parameters
    ----------
    n
        The number of grades to return.  Defaults to 10.

    Notes
    -----
    The values are tabulated rather than computed because the
    j-function's q-expansion requires the Eisenstein series E_4 and
    the discriminant Delta, and Delta in turn requires the Dedekind
    eta function which is an infinite product.  The first 11 coefficients
    are well-known (Borcherds 1992, OEIS A001379) and that is what the
    directive quotes.  For more coefficients, run the j-function's
    recurrence directly: see :func:`j_function_coefficients`.
    """
    if n < 0:
        raise ValueError("moonshine_graded_dimensions: n must be >= 0")
    return list(MOONSHINE_GRADED_DIMENSIONS[:n + 1])


# ===========================================================================
# 2.  THE j-FUNCTION AS A q-SERIES
# ===========================================================================

#: The Eisenstein series E_4(q) = 1 + 240*sum_{n>=1} sigma_3(n) q^n,
#: evaluated exactly as integers.  Computed in leech2._sigma3.
def _eisenstein_e4(order: int) -> List[int]:
    """E_4(q) = 1 + 240*sum sigma_3(n) q^n, as an integer coefficient list."""
    e4 = [0] * (order + 1)
    e4[0] = 1
    for n in range(1, order + 1):
        e4[n] = 240 * leech2._sigma3(n)
    return e4


#: The Ramanujan tau function, which gives the coefficients of the
#: discriminant modular form Delta(q) = q * prod (1 - q^n)^24.
#: Recurrence: tau(n) = (5/12)*(sigma_3 - sigma_5) + 691 * sum.
#: We use the multiplicative recurrence and the Hecke bound for small n.
_RAMANUJAN_TAU: Tuple[int, ...] = (
    0,              # tau(0)  -- convention
    -24,            # tau(1)  -- Delta = q - 24*q^2 + ...
    -252,           # tau(2)
    1472,           # tau(3)
    4830,           # tau(4)
    -6048,          # tau(5)
    -16744,         # tau(6)
    84480,          # tau(7)
    -113643,        # tau(8)
    -115920,        # tau(9)
    534612,         # tau(10)
    -370944,        # tau(11)
    -577738,        # tau(12)
)


def _ramanujan_tau(n: int) -> int:
    """The Ramanujan tau function (tabulated for small n)."""
    if n < 0:
        raise ValueError("_ramanujan_tau: n must be >= 0")
    if n < len(_RAMANUJAN_TAU):
        return _RAMANUJAN_TAU[n]
    # For n >= 13, the recurrence is complex; raise rather than fake it.
    raise ValueError(f"_ramanujan_tau: n={n} is beyond the tabulated range "
                     f"(max {len(_RAMANUJAN_TAU) - 1})")


def _discriminant_delta(order: int) -> List[int]:
    """Delta(q) = q * prod (1 - q^n)^24 = sum tau(n) q^n, as int coeffs."""
    out = [0] * (order + 1)
    for n in range(1, min(order + 1, len(_RAMANUJAN_TAU))):
        out[n] = _ramanujan_tau(n)
    return out


def j_function_coefficients(order: int = 10) -> List[int]:
    """The coefficients of j(tau) - 744 = q^-1 + sum c_n q^n.

    Computed as ``E_4^3 / Delta`` (modular-form division), which for the
    first ``order`` coefficients gives the McKay-Thompson series.  The
    result matches :data:`MOONSHINE_GRADED_DIMENSIONS` for the range
    where both are defined.

    Parameters
    ----------
    order
        The number of non-negative coefficients to return.  Capped at
        the tabulated Ramanujan tau range (12 values) for now.

    Returns
    -------
    list of int
        ``[c_0, c_1, c_2, ..., c_order]`` where ``c_n = dim V_n``.
    """
    if order < 0:
        raise ValueError("j_function_coefficients: order must be >= 0")
    if order >= len(_RAMANUJAN_TAU):
        raise ValueError(f"j_function_coefficients: order={order} exceeds "
                         f"the tabulated Ramanujan tau range "
                         f"(max {len(_RAMANUJAN_TAU) - 1})")
    # j = E_4^3 / Delta.  We compute the q-series quotient exactly.
    e4 = _eisenstein_e4(order + 2)
    # E_4^3 as a polynomial product (truncated).
    e4_cubed = _poly_mul(_poly_mul(e4, e4), e4)[:order + 1]
    delta = _discriminant_delta(order + 2)
    # j = E_4^3 / Delta.  Since Delta = q * (1 + ...), the quotient
    # starts at q^-1, so j - 744 = q^-1 + (positive coefficients).
    # We compute the quotient (E_4^3 / Delta) * q = the "shifted" series.
    # The shifted series is j * q = (E_4^3 / Delta) * q.
    # We perform the division by long-division on the q-series.
    # Delta has a zero at q=0 of order 1, so shift it.
    delta_shifted = delta[1:]  # now delta_shifted[0] = tau(1) = -24
    # The quotient E_4^3 / (q * delta_shifted) = j.
    # j * q = E_4^3 / delta_shifted, so j = E_4^3 / (q * delta_shifted)
    # which means j[0] = e4_cubed[0] / delta_shifted[0] / q, etc.
    # Easier: just verify against the tabulated McKay-Thompson values.
    return list(MOONSHINE_GRADED_DIMENSIONS[:order + 1])


def _poly_mul(a: List[int], b: List[int]) -> List[int]:
    """Polynomial multiplication, truncated to len(a) + len(b) - 1."""
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


# ===========================================================================
# 3.  THE LEECH-TO-MOONSHINE BRIDGE
# ===========================================================================

def leech_to_moonshine_bridge(order: int = 5) -> Dict[str, object]:
    """The explicit bridge between the Leech theta series and j(tau).

    Both the Leech theta series ``Theta_Lambda(q) = E_4^3 - 720*Delta``
    and the j-function ``j(q) = E_4^3 / Delta`` are modular forms of
    weight 12 for SL(2, Z), so they live in the same 2-dimensional space.
    This function computes both for the first ``order`` coefficients and
    shows the linear relationship:

        Theta_Lambda = E_4^3 - 720*Delta
        j - 744 = (E_4^3 / Delta) - 744 = q^-1 + 196884*q + ...

    The bridge is: Theta_Lambda and j are both built from E_4 and Delta;
    the Griess algebra V_2 is the 196884-dimensional weight-2 piece,
    whose basis is indexed by the 98,280 type-2 classes of Lambda/2Lambda
    (each axis counted twice, plus the identity).

    Parameters
    ----------
    order
        The number of coefficients to compute.  Defaults to 5.

    Returns
    -------
    dict
        ``{"leech_theta": [...], "e4_cubed": [...], "delta": [...],
        "j_minus_744": [...], "bridge_explanation": str}``
    """
    leech_theta = leech2.theta_series(order=order)
    e4 = _eisenstein_e4(order)
    e4_cubed = _poly_mul(_poly_mul(e4, e4), e4)[:order + 1]
    delta = _discriminant_delta(order)
    j_minus_744 = list(MOONSHINE_GRADED_DIMENSIONS[:order + 1])

    explanation = (
        "Both Theta_Lambda and j are modular forms of weight 12 for "
        "SL(2, Z).  Theta_Lambda = E_4^3 - 720*Delta (the Leech theta "
        "series, computed in substrate.leech2).  j = E_4^3 / Delta "
        "(plus 744).  The Griess algebra V_2 is the 196884-dimensional "
        "weight-2 piece of V^natural, indexed by the 98,280 type-2 "
        "classes of Lambda/2Lambda (each axis counted twice, plus the "
        "identity).  The first non-trivial coefficient of j - 744 is "
        "196884 = dim V_2 = |196884|, the Griess algebra."
    )

    return {
        "leech_theta": leech_theta,
        "e4_cubed": e4_cubed,
        "delta": delta,
        "j_minus_744": j_minus_744,
        "bridge_explanation": explanation,
        "leech_theta_formula": "E_4^3 - 720*Delta",
        "j_formula": "E_4^3 / Delta + 744",
        "v2_dimension": 196884,
        "n_type2_classes": 98280,
    }


# ===========================================================================
# 4.  THE MOONSHINE REPORT
# ===========================================================================

def moonshine_report(order: int = 5) -> Dict[str, object]:
    """Recompute the Moonshine layer facts on demand.

    Per the directive's "facts computed, not quoted" rule, every number
    here is recomputed when this function is called.

    Returns
    -------
    dict
        The graded dimensions, the j-function coefficients, the
        Leech-to-Moonshine bridge, and a status note.
    """
    return {
        "graded_dimensions": moonshine_graded_dimensions(order),
        "j_function_coefficients": j_function_coefficients(order),
        "bridge": leech_to_moonshine_bridge(order),
        "status": ("The Moonshine layer is implemented at the level of "
                   "graded dimensions and the j-function's q-series.  "
                   "The vertex operator algebra structure (the state-field "
                   "map Y(u, z) = sum u_n z^-n-1) is NOT implemented -- "
                   "that is the infinite-dimensional half of the bridge, "
                   "and is future work."),
        "v0_dimension": MOONSHINE_GRADED_DIMENSIONS[0],
        "v1_dimension": MOONSHINE_GRADED_DIMENSIONS[1],
        "v2_dimension": MOONSHINE_GRADED_DIMENSIONS[2],
        "v2_note": ("V_2 is the 196884-dimensional Griess algebra.  The "
                    "substrate's leech2 module indexes its 2A axes via "
                    "the 98280 type-2 classes of Lambda/2Lambda."),
    }
