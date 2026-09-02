"""``glm_universal.reasoning.mantissa`` -- the PTB/AOO mantissa metrology.

Part IV, section 5.1 of the unification blueprint asks for a bit-spectrum
tracker: something that "unzips" an IEEE-754 double and measures its
bit-allocation against the exact rational binary expansion, so that the
origin of floating-point drift can be *located* rather than described.

This module is that tracker, built so that it obeys the Universal Binary
Principle while its subject matter violates it: **no float is ever
constructed here**.  IEEE-754 binary64 is modelled exactly, in integers and
:class:`~fractions.Fraction`, by :func:`to_double` -- round-to-nearest,
ties-to-even, 53 significant bits.  Everything the module says about doubles
is therefore a theorem about that model, reproducible on any machine, and not
a measurement of the interpreter it happens to run on.

The three questions, and the answers
------------------------------------
**1. How much precision does the first operation cost?**  The blueprint says
ten full bits of mantissa are lost on step 0 or 1 for every odd prime.  Under
the natural readings -- relative error of the stored value, and Hamming
distance between the stored significand and the exact expansion's leading 53
bits -- that is not what happens: rounding ``1/p`` to a double retains at
least 53 bits of relative precision for every odd prime tested, and the
stored significand differs from the exact expansion in at most a handful of
trailing bits.  :func:`rounding_report` gives the measured figures, and
:func:`blueprint_claims` records the claim as *not reproduced*: the number
may well come from a longer computation in the original study, but no
definition stated in the blueprint yields it.

**2. Where does the drift actually come from, then?**  From the fact that a
double is a *dyadic* rational and ``1/p`` is not.  Run the doubling map
``x -> 2x mod 1`` -- the map that reads off one bit of the expansion per
step, and the cleanest expansive iteration there is.  Every arithmetic step
of that map is exact in binary floating point, so the double's orbit is not
corrupted by any later rounding; and yet it *dies*.  A dyadic with ``k``
bits after the point reaches ``0`` in at most ``k`` steps and stays there,
while the exact orbit of ``1/p`` is periodic with period
``ord_2(p)`` -- the multiplicative order of 2 mod ``p`` -- and never
terminates.  So the entire loss is spent in the *first* rounding, and it is
total: the float eventually reports a constant where the exact value keeps
oscillating.  That, exactly stated, is the hallucination origin.
:func:`doubling_orbit` measures both orbits, and
``RequestProject/GLM/Mantissa.lean`` proves the two statements.

**3. What does the drift look like on the substrate?**  :func:`projection`
folds the leading 48 significand bits into 24 coordinates by pairwise parity,
which is the coarsest projection that lands on the substrate's own width.
:func:`projection_drift` follows the Hamming distance between the exact
orbit's projection and the double's, step by step.  The blueprint's two
figures -- "substrate-faithful" 0 and "substrate-inverted" 24 -- both turn
up, but not where it puts them.  Before the collapse the two projections
agree closely; after it the distance is simply the *exact* orbit's own
projection weight, which is a property of the phase: ``p = 3`` is inverted at
every phase and ``p = 5`` alternates between faithful and inverted.  So the
labels are real and the assignment to primes is not.

Reachable from the runtime as ``report mantissa``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

__all__ = [
    "PRECISION",
    "PROJECTION_BITS",
    "ODD_PRIMES",
    "normalise",
    "to_double",
    "significand_bits",
    "expansion_bits",
    "retained_bits",
    "binary_period",
    "repeating_block",
    "dyadic_bits",
    "rounding_report",
    "doubling_orbit",
    "projection",
    "projection_weights",
    "projection_drift",
    "blueprint_claims",
    "mantissa_report",
]


#: IEEE-754 binary64: 53 significant bits, one of them implicit.
PRECISION = 53

#: The leading significand bits folded onto the 24-coordinate substrate.
#: 48 = 2 * 24, so each coordinate is the parity of one bit pair.
PROJECTION_BITS = 48

#: The odd primes the report walks.  Fixed, so the figures are the same on
#: every run; no sampling and no seed.
ODD_PRIMES: Tuple[int, ...] = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31)


# ═════════════════════════════════════════════════════════════════════════
# 1.  IEEE-754 BINARY64, MODELLED IN EXACT INTEGERS
# ═════════════════════════════════════════════════════════════════════════

def normalise(x: Fraction) -> Tuple[Fraction, int]:
    """Write ``x > 0`` as ``s * 2**e`` with ``1/2 <= s < 1``, exactly."""
    value = Fraction(x)
    if value <= 0:
        raise ValueError(f"normalise: expected a positive value, got {x}")
    e = value.numerator.bit_length() - value.denominator.bit_length()
    scaled = value / Fraction(2) ** e
    while scaled >= 1:
        scaled /= 2
        e += 1
    while scaled < Fraction(1, 2):
        scaled *= 2
        e -= 1
    return scaled, e


def to_double(x: Fraction, precision: int = PRECISION) -> Fraction:
    """``x`` rounded to ``precision`` significant bits, ties to even.

    This is IEEE-754 binary64 arithmetic's rounding rule, carried out in
    exact rational arithmetic, so the result is the *value* the hardware
    would hold rather than a float object.  Subnormals and overflow are out
    of scope: every value this module rounds is a small positive rational.
    """
    value = Fraction(x)
    if value == 0:
        return Fraction(0)
    if value < 0:
        return -to_double(-value, precision)
    significand, e = normalise(value)
    scaled = significand * (1 << precision)
    n = scaled.numerator // scaled.denominator
    remainder = scaled - n
    if remainder > Fraction(1, 2) or (remainder == Fraction(1, 2)
                                      and n % 2 == 1):
        n += 1
    return Fraction(n, 1 << precision) * Fraction(2) ** e


def significand_bits(x: Fraction, count: int = PRECISION) -> Tuple[int, ...]:
    """The leading ``count`` bits of ``x``'s significand, exactly.

    ``x = 0`` has no significand; it is reported as all zeros, which is what
    the projection needs when a float orbit has collapsed.
    """
    if x == 0:
        return tuple(0 for _ in range(count))
    significand, _ = normalise(Fraction(x))
    out: List[int] = []
    for _ in range(count):
        significand *= 2
        bit = 1 if significand >= 1 else 0
        out.append(bit)
        significand -= bit
    return tuple(out)


def expansion_bits(x: Fraction, count: int) -> Tuple[int, ...]:
    """The first ``count`` bits after the point of ``0 <= x < 1``."""
    value = Fraction(x)
    if not (0 <= value < 1):
        raise ValueError(f"expansion_bits: {x} is not in [0, 1)")
    out: List[int] = []
    for _ in range(count):
        value *= 2
        bit = 1 if value >= 1 else 0
        out.append(bit)
        value -= bit
    return tuple(out)


def retained_bits(exact: Fraction, stored: Fraction) -> int:
    """How many bits of relative precision ``stored`` keeps of ``exact``.

    The largest ``k`` with ``|stored - exact| < 2**-k * |exact|``, or ``-1``
    to mean "exactly equal, no bit lost at any depth".
    """
    if exact == 0:
        raise ValueError("retained_bits: the exact value must be non-zero")
    error = abs(Fraction(stored) - Fraction(exact)) / abs(Fraction(exact))
    if error == 0:
        return -1
    k = 0
    while error < Fraction(1, 1 << (k + 1)):
        k += 1
    return k


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE EXACT PERIOD OF 1/p
# ═════════════════════════════════════════════════════════════════════════

def binary_period(p: int) -> int:
    """The multiplicative order of 2 mod ``p``: the period of ``1/p``.

    The blueprint's "oscillation frequency of the float drift" is this
    number, and it is exactly computable -- which is the point.  Defined for
    odd ``p > 1``; even denominators terminate rather than repeat.
    """
    if p <= 1 or p % 2 == 0:
        raise ValueError(f"binary_period: expected an odd p > 1, got {p}")
    k = 1
    value = 2 % p
    while value != 1:
        value = (value * 2) % p
        k += 1
        if k > p:  # pragma: no cover -- unreachable for odd p
            raise ValueError(f"binary_period: no order found for {p}")
    return k


def repeating_block(p: int) -> Tuple[int, ...]:
    """One period of the binary expansion of ``1/p``."""
    return expansion_bits(Fraction(1, p), binary_period(p))


def dyadic_bits(x: Fraction) -> int:
    """How many bits after the point a dyadic rational needs; ``0`` if none.

    Raises for a value that is not dyadic -- a value no float can hold.
    """
    value = Fraction(x)
    denominator = value.denominator
    if denominator & (denominator - 1):
        raise ValueError(f"dyadic_bits: {x} is not a dyadic rational")
    return denominator.bit_length() - 1


# ═════════════════════════════════════════════════════════════════════════
# 3.  WHAT THE FIRST ROUNDING COSTS
# ═════════════════════════════════════════════════════════════════════════

def rounding_report(primes: Sequence[int] = ODD_PRIMES) -> Dict[str, object]:
    """Round ``1/p`` to a double and measure exactly what was lost."""
    rows: List[Dict[str, object]] = []
    for p in primes:
        exact = Fraction(1, p)
        stored = to_double(exact)
        kept = retained_bits(exact, stored)
        exact_leading = significand_bits(exact, PRECISION)
        stored_leading = significand_bits(stored, PRECISION)
        rows.append({
            "prime": p,
            "period": binary_period(p),
            "retained_bits": kept,
            "exact_is_dyadic": False,
            "stored_is_dyadic": True,
            "stored_bits_after_point": dyadic_bits(stored),
            "significand_hamming": sum(
                1 for a, b in zip(exact_leading, stored_leading) if a != b),
            "error": abs(stored - exact),
            "rounded_up": stored > exact,
        })
    return {
        "precision": PRECISION,
        "rows": tuple(rows),
        "min_retained_bits": min(int(r["retained_bits"]) for r in rows),
        "max_significand_hamming": max(int(r["significand_hamming"])
                                       for r in rows),
        "bits_lost_at_step_zero": max(
            0, PRECISION - min(int(r["retained_bits"]) for r in rows)),
        "every_prime_repeats": all(int(r["period"]) >= 1 for r in rows),
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE DOUBLING MAP: WHERE THE DRIFT ACTUALLY LIVES
# ═════════════════════════════════════════════════════════════════════════

def _double_step(x: Fraction) -> Fraction:
    """One step of the doubling map ``x -> 2x mod 1`` on ``[0, 1)``."""
    y = Fraction(x) * 2
    return y - 1 if y >= 1 else y


def doubling_orbit(p: int, steps: int = 64) -> Dict[str, object]:
    """The exact orbit of ``1/p`` against the double's, step by step.

    Both orbits run the same map.  Every step of it is exact in binary
    floating point -- doubling only moves the exponent, and subtracting 1
    from a value in ``[1, 2)`` is exact -- so no rounding after the first
    can be blamed for what happens.  What happens is that the double's orbit
    reaches ``0`` and stops, at the step given by ``collapse_step``, while
    the exact orbit repeats with period ``period`` for ever.
    """
    if steps < 1:
        raise ValueError(f"doubling_orbit: steps must be positive, got {steps}")
    exact = Fraction(1, p)
    stored = to_double(exact)
    initial_bits = dyadic_bits(stored)
    collapse: int | None = None
    first_divergence: int | None = None
    first_projection_divergence: int | None = None
    distances: List[int] = []
    for n in range(steps + 1):
        distance = sum(1 for a, b in zip(projection(exact), projection(stored))
                       if a != b)
        distances.append(distance)
        if first_divergence is None and exact != stored:
            first_divergence = n
        if first_projection_divergence is None and distance != 0:
            first_projection_divergence = n
        if collapse is None and stored == 0:
            collapse = n
        exact = _double_step(exact)
        stored = _double_step(stored)
    return {
        "prime": p,
        "steps": steps,
        "period": binary_period(p),
        "initial_bits_after_point": initial_bits,
        "collapse_step": collapse,
        "collapse_bound": initial_bits,
        "collapse_within_bound": collapse is not None
                                 and collapse <= initial_bits,
        "first_divergence_step": first_divergence,
        "first_projection_divergence_step": first_projection_divergence,
        "exact_orbit_terminates": False,
        "projection_distances": tuple(distances),
        "max_projection_distance": max(distances),
        "final_projection_distance": distances[-1],
        "pre_collapse_max_distance": max(distances[:collapse])
                                     if collapse else max(distances),
        "post_collapse_weights": projection_weights(p),
    }


def projection_weights(p: int) -> Tuple[int, ...]:
    """The projection weight of the exact orbit of ``1/p``, phase by phase.

    Once the double's orbit has collapsed to ``0`` its projection is the
    origin, so the Hamming distance between the two projections *is* the
    weight of the exact orbit's own projection.  These are the numbers the
    blueprint's "substrate-faithful" and "substrate-inverted" labels are
    really about, and they are a property of the phase, not only of ``p``.
    """
    weights: List[int] = []
    value = Fraction(1, p)
    for _ in range(binary_period(p)):
        weights.append(sum(projection(value)))
        value = _double_step(value)
    return tuple(weights)


def projection(x: Fraction) -> Tuple[int, ...]:
    """The 24-coordinate substrate parity projection of a significand.

    The leading ``PROJECTION_BITS`` significand bits are folded in pairs, so
    coordinate ``i`` is the parity of bits ``2i`` and ``2i+1``.  A value of
    ``0`` -- a collapsed orbit -- projects to the origin.
    """
    bits = significand_bits(Fraction(x), PROJECTION_BITS)
    return tuple((bits[2 * i] + bits[2 * i + 1]) % 2 for i in range(24))


def projection_drift(primes: Sequence[int] = ODD_PRIMES,
                     steps: int = 64) -> Dict[str, object]:
    """Follow the substrate projection of both orbits, for each prime."""
    rows = tuple(doubling_orbit(p, steps) for p in primes)
    return {
        "steps": steps,
        "rows": rows,
        "any_antipodal": any(int(r["max_projection_distance"]) == 24
                             for r in rows),
        "any_antipodal_before_collapse": any(
            int(r["pre_collapse_max_distance"]) == 24 for r in rows),
        "max_distance_before_collapse": max(
            int(r["pre_collapse_max_distance"]) for r in rows),
        "earliest_projection_divergence": min(
            int(r["first_projection_divergence_step"]) for r in rows),
        "max_distance_overall": max(int(r["max_projection_distance"])
                                    for r in rows),
        "all_collapse": all(r["collapse_step"] is not None for r in rows),
        "all_collapse_within_bound": all(bool(r["collapse_within_bound"])
                                         for r in rows),
    }


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE BLUEPRINT'S SECTION 5.1 CLAIMS, EACH WITH A VERDICT
# ═════════════════════════════════════════════════════════════════════════

def blueprint_claims(steps: int = 64) -> Tuple[Dict[str, object], ...]:
    """Each section-5.1 claim, the figure that settles it, and the verdict."""
    rounding = rounding_report()
    drift = projection_drift(steps=steps)
    p3 = next(r for r in drift["rows"] if r["prime"] == 3)   # type: ignore
    p5 = next(r for r in drift["rows"] if r["prime"] == 5)   # type: ignore

    return (
        {
            "claim": "10 full bits of mantissa are lost on the first "
                     "operation, for every odd prime",
            "verdict": "not reproduced -- no reading in the blueprint gives "
                       "it",
            "holds": rounding["bits_lost_at_step_zero"] == 0,
            "figure": f"the stored double keeps at least "
                      f"{rounding['min_retained_bits']} bits of relative "
                      f"precision on every prime tested, and its significand "
                      f"differs from the exact expansion in at most "
                      f"{rounding['max_significand_hamming']} of "
                      f"{PRECISION} bits",
        },
        {
            "claim": "the exact binary period of 1/p is the multiplicative "
                     "order of 2 mod p, and is exactly computable",
            "verdict": "confirmed",
            "holds": all(binary_period(p) == len(repeating_block(p))
                         for p in ODD_PRIMES),
            "figure": "; ".join(f"1/{p} has period {binary_period(p)}"
                                for p in ODD_PRIMES[:5]) + "; ...",
        },
        {
            "claim": "the loss is structural: a double is dyadic, so its "
                     "orbit under the doubling map dies while the exact "
                     "orbit repeats for ever",
            "verdict": "confirmed -- and this is where the drift really is",
            "holds": bool(drift["all_collapse"]
                          and drift["all_collapse_within_bound"]),
            "figure": f"every double collapses to 0 within its "
                      f"bit count (p = 3 at step {p3['collapse_step']} of a "
                      f"bound of {p3['collapse_bound']}), while the exact "
                      f"orbit has period {p3['period']} and never "
                      f"terminates",
        },
        {
            "claim": "the drift is substrate-faithful for p = 3 (Hamming 0) "
                     "and substrate-inverted for p = 5 (Hamming 24)",
            "verdict": "refuted as stated -- both values occur, but they "
                       "belong to the phase rather than to the prime, and "
                       "the two primes are the other way round",
            "holds": (tuple(p3["post_collapse_weights"]) == (24, 24)
                      and 0 in tuple(p5["post_collapse_weights"])
                      and 24 in tuple(p5["post_collapse_weights"])),
            "figure": f"while the double still holds information the "
                      f"projections agree to within Hamming "
                      f"{drift['max_distance_before_collapse']}; after the "
                      f"collapse the distance is the exact orbit's own "
                      f"projection weight, which for p = 3 is "
                      f"{tuple(p3['post_collapse_weights'])} -- inverted at "
                      f"every phase -- and for p = 5 is "
                      f"{tuple(p5['post_collapse_weights'])}, faithful at "
                      f"three of its four phases and inverted at the "
                      f"fourth",
        },
    )


def mantissa_report(steps: int = 64) -> Dict[str, object]:
    """Everything section 5.1 asks for, recomputed in one call."""
    claims = blueprint_claims(steps)
    return {
        "precision": PRECISION,
        "primes": ODD_PRIMES,
        "rounding": rounding_report(),
        "drift": projection_drift(steps=steps),
        "claims": claims,
        "claim_count": len(claims),
        "claims_holding": sum(1 for c in claims if c["holds"]),
        "confirmed": sum(1 for c in claims
                         if str(c["verdict"]).startswith("confirmed")),
        "not_reproduced": sum(1 for c in claims
                              if str(c["verdict"]).startswith(
                                  "not reproduced")),
        "refuted": sum(1 for c in claims
                       if str(c["verdict"]).startswith("refuted")),
    }
