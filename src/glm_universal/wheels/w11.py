"""W11 -- Uniform motion.

Constant-velocity kinematics.  Declared in
``studies/DOMAIN_WHEELS_STUDY.md`` §2.2.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from ..engineering.wheels import Wheel

__all__ = ["WHEEL"]

#: The W11 wheel: ``velocity = length / time``.
WHEEL: Wheel = Wheel(
    id="W11",
    title="Uniform motion",
    axioms=(
        "velocity = length / time",
    ),
    cases=(),
)
