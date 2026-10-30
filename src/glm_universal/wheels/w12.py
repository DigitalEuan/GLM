"""W12 -- Density, volume and amount of substance.

Declared in ``studies/DOMAIN_WHEELS_STUDY.md`` §2.2.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from ..engineering.wheels import Wheel

__all__ = ["WHEEL"]

#: The W12 wheel.
WHEEL: Wheel = Wheel(
    id="W12",
    title="Density, volume and amount of substance",
    axioms=(
        "density = mass / volume",
        "volume = area * length",
        "amount = mass / molar_mass",
    ),
    cases=(),
)
