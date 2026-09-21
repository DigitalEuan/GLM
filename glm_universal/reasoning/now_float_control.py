"""``glm_universal.reasoning.now_float_control`` -- the one float in the audit.

Why this module exists
----------------------
The supplied study ``source_material/HISTORY_RECORDED_NOW_V2_STUDY.md`` rests
its case for the substrate on one comparative claim:

    "Float-based systems cannot do this -- the accumulator state is corrupted
    by rounding at every step."

That is a claim about floating point, and it cannot be settled without running
floating point.  Directive **D11** says a forbidden operation never cancels an
experiment: run it, declare the site, and carry the cost.  This module is that
declared site -- it is listed in
:data:`glm_universal.reasoning.exactness.FLOAT_SITES` -- and it is the only
module in the package that builds a float.  Nothing the system computes with
imports it; the audit in :mod:`glm_universal.reasoning.now_receipt` imports it
to report its reading, and nothing else does.

What it measures
----------------
The same first-order loop, twice: once in ``Fraction`` and once in ``float``,
on a target that is exactly representable as a double (so that the *only*
difference is the rounding of the additions).  Three readings:

``first_bit_divergence``
    the first tick at which the two loops emit different bits, or ``None``;
``first_count_divergence``
    the first tick at which their running counts differ, or ``None``;
``recovery``
    whether the supplied recovery, ``round(target*n - state)``, still returns
    the true count when the state it is handed is the float one.

The honest reading is in the study: within the horizon measured the float loop
does not diverge at all, so the comparative claim is not supported at the
scales the supplied studies ran.  What exactness buys is the *bound* -- the
exact loop's accumulator is provably in ``[0, 1)`` for every tick
(``GLM.ZeroStorageV5.dsAcc_mem_Ico``), while the float loop's error is bounded
only by an accumulation argument that fails at around ``2/eps`` ticks.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from typing import Dict, Optional, Sequence, Tuple

__all__ = ["float_control", "DEFAULT_HORIZON"]

#: The default horizon.  A hundred thousand ticks is two orders of magnitude
#: beyond the longest run the supplied studies report recovering from, and the
#: exhaustive case in ``tests/test_now_receipt.py`` takes it to ten million.
DEFAULT_HORIZON: int = 100_000


def float_control(horizon: int = DEFAULT_HORIZON,
                  checkpoints: Sequence[int] = (100, 10_000, 100_000)
                  ) -> Dict[str, object]:
    """Run the loop in exact arithmetic and in ``float``, and compare.

    The target is ``sqrt(2)/2`` as a double -- the value the supplied studies
    used, since theirs came from ``math.sqrt`` -- read here as the exact
    rational that double denotes, so the two loops chase the same number.
    """
    float_target = 2.0 ** -0.5
    exact_target = Fraction(float_target)

    float_state = 0.0
    float_count = 0
    exact_state = Fraction(0)
    exact_count = 0
    first_bit: Optional[int] = None
    first_count: Optional[int] = None
    largest_gap = Fraction(0)
    rows = []
    checkpoint_set = {int(value) for value in checkpoints if value <= horizon}

    for tick in range(1, horizon + 1):
        float_state += float_target
        float_bit = 1 if float_state >= 1.0 else 0
        if float_bit:
            float_state -= 1.0
            float_count += 1

        driven = exact_state + exact_target
        exact_bit = 1 if driven >= 1 else 0
        if exact_bit:
            exact_state = driven - 1
            exact_count += 1
        else:
            exact_state = driven

        if float_bit != exact_bit and first_bit is None:
            first_bit = tick
        if float_count != exact_count and first_count is None:
            first_count = tick
        gap = abs(Fraction(float_state) - exact_state)
        if gap > largest_gap:
            largest_gap = gap
        if tick in checkpoint_set:
            recovered = round(exact_target * tick - Fraction(float_state))
            rows.append({
                "ticks": tick,
                "exact_count": exact_count,
                "float_count": float_count,
                "recovered_from_the_float_state": recovered,
                "recovery_holds": recovered == exact_count,
            })

    return {
        "horizon": horizon,
        "target": str(exact_target),
        "rows": tuple(rows),
        "first_bit_divergence": first_bit,
        "first_count_divergence": first_count,
        "largest_state_gap_numerator": abs(Fraction(largest_gap)).numerator,
        "largest_state_gap_denominator_bits":
            Fraction(largest_gap).denominator.bit_length() - 1,
        "float_recovery_always_holds": all(row["recovery_holds"] for row in rows),
        "epsilon_denominator_bits": abs(sys.float_info.epsilon.as_integer_ratio()[1]).bit_length() - 1,
    }
