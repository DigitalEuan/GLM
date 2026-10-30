"""The W09/W13 oscillator junction -- four variants, B shipped.

Phase 158's measurement of the W09 (wave kinematics) / W13 (mass-spring
oscillator) junction.  Four variants were tried under one declared rule:

  * A ``turn_and_rate`` -- join ``angle`` and ``frequency``.
  * B ``rate_only`` -- join ``frequency`` only, split ``angle``.  **Shipped.**
  * C ``apart`` -- join nothing (full split).
  * D ``reference_circle`` -- join via the reference-circle identity.

Variant B was chosen: it keeps all 21 declared answers + 9 refusals +
249/249 preservation answers, and refuses the rotor chain
(``angular_frequency * torque = power``).

The Lean file ``src/lean/RequestProject/GLM/OscillatorJunction.lean``
proves the four variants' theorems with no ``sorry``:
  * ``rotor_chain_turn_and_rate``
  * ``rotor_chain_refused_rate_only``
  * ``wave_period_rate_only``
  * ``rotor_chain_refused_reference_circle``
  * ``reference_circle_identity``

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from typing import Dict, Tuple

__all__ = [
    "VARIANTS", "VARIANT_READINGS", "SHIPPED", "LEAN_FILE", "LEAN_THEOREMS",
]


#: The four variant names, in the order the study tried them.
VARIANTS: Tuple[str, ...] = ("A", "B", "C", "D")

#: A human-readable description of each variant.
VARIANT_READINGS: Dict[str, str] = {
    "A": "turn_and_rate: join angle and frequency",
    "B": "rate_only: join frequency only, split angle (shipped)",
    "C": "apart: join nothing (full split)",
    "D": "reference_circle: join via the reference-circle identity",
}

#: The shipped variant.
SHIPPED: str = "B"

#: The Lean file that formalises the four variants.
LEAN_FILE: str = "RequestProject/GLM/OscillatorJunction.lean"

#: The theorems the Lean file proves (one per variant, plus the
#: reference-circle identity).
LEAN_THEOREMS: Tuple[str, ...] = (
    "rotor_chain_turn_and_rate",
    "rotor_chain_refused_rate_only",
    "wave_period_rate_only",
    "rotor_chain_refused_reference_circle",
    "reference_circle_identity",
)


def junction_for_variant(variant: str) -> Tuple[str, ...]:
    """The shared carrier names for the W09/W13 junction under ``variant``.

    * A: ``("frequency", "angle")``
    * B: ``("frequency",)``  (angle split)
    * C: ``()``              (full split)
    * D: ``("frequency", "angle")``  (via the reference-circle identity)
    """
    if variant == "A":
        return ("frequency", "angle")
    if variant == "B":
        return ("frequency",)
    if variant == "C":
        return ()
    if variant == "D":
        return ("frequency", "angle")
    raise KeyError(f"unknown variant {variant!r}")
