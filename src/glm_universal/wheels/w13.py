"""W13 -- Period and the mass-spring oscillator.

Declared in ``studies/DOMAIN_WHEELS_STUDY.md`` §2.2.  The oscillator
junction (W09/W13) joins ``frequency`` only (rule B, Phase 158); see
:mod:`glm_universal.wheels.junctions.oscillator`.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from ..engineering.wheels import Wheel

__all__ = ["WHEEL"]

#: The W13 wheel.
WHEEL: Wheel = Wheel(
    id="W13",
    title="Period and the mass-spring oscillator",
    axioms=(
        "frequency = 1 / period",
        "angular_frequency = angle * frequency",
        "spring_constant = mass * angular_frequency * angular_frequency",
    ),
    cases=(),
)
