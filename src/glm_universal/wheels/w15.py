"""W15 -- Charge and energy over time.

Declared in ``studies/DOMAIN_WHEELS_STUDY.md`` §2.2.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from ..engineering.wheels import Wheel

__all__ = ["WHEEL"]

#: The W15 wheel.
WHEEL: Wheel = Wheel(
    id="W15",
    title="Charge and energy over time",
    axioms=(
        "charge = current * time",
        "energy = power * time",
    ),
    cases=(),
)
