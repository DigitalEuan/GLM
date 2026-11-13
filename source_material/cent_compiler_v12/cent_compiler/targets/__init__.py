"""Declared target adapters for the Cent transfer compiler.

Targets are deliberately explicit.  A profile describes the invocation and
evidence contract; an adapter is executable source for one selected operation
and mechanism.  A reference adapter is not a claim that a real external system
has been integrated.
"""
from .glm import (
    ADAPTERS,
    FIXED_VECTORS,
    FLUID_ADAPTER,
    FLUID_VECTORS,
    FluidVector,
    GLM_REFERENCE_TARGET,
    KCL_ADAPTER,
    KCL_DIFFERENCE_ADAPTER,
    KCL_DIFFERENCE_VECTORS,
    KCL_VECTORS,
    SQRT_ADAPTER,
    SQRT_VECTORS,
    TARGET_ID,
    get_adapter,
)

__all__ = [
    "ADAPTERS",
    "FIXED_VECTORS",
    "FLUID_ADAPTER",
    "FLUID_VECTORS",
    "FluidVector",
    "GLM_REFERENCE_TARGET",
    "KCL_ADAPTER",
    "KCL_DIFFERENCE_ADAPTER",
    "KCL_DIFFERENCE_VECTORS",
    "KCL_VECTORS",
    "SQRT_ADAPTER",
    "SQRT_VECTORS",
    "TARGET_ID",
    "get_adapter",
]
