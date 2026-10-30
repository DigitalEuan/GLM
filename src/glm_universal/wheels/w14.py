"""W14 -- Inductors and the LC circuit.

Declared in ``studies/DOMAIN_WHEELS_STUDY.md`` §2.2.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from ..engineering.wheels import Wheel

__all__ = ["WHEEL"]

#: The W14 wheel.
WHEEL: Wheel = Wheel(
    id="W14",
    title="Inductors and the LC circuit",
    axioms=(
        "reactance = inductance * angular_frequency",
        "inductance * capacitance * angular_frequency * angular_frequency = 1",
        "energy = 1/2 * inductance * current * current",
    ),
    cases=(),
)
