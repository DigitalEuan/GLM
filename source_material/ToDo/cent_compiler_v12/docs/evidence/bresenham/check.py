#!/usr/bin/env python3
"""Exact evidence for the Bresenham / one-tick delta-sigma correspondence."""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from cent_compiler.targets.glm import (  # noqa: E402
    delta_sigma_quantized_carry,
    uniform_quantizer_carry,
)

Q = Fraction


def line_walk(dx: int, dy: int) -> tuple[int, ...]:
    """Integer DDA/Bresenham walk: floor(n dy/dx) increments."""
    return tuple(
        ((n + 1) * dy) // dx - (n * dy) // dx for n in range(dx)
    )


def one_tick(dx: int, dy: int) -> tuple[int, ...]:
    """One-tick floor delta-sigma with input dy/dx."""
    state = Q(0)
    code: list[int] = []
    for _ in range(dx):
        state += Q(dy, dx)
        level = state.numerator // state.denominator
        code.append(level)
        state -= level
    return tuple(code)


def main() -> int:
    pairs = [(dx, dy) for dx in range(1, 33) for dy in range(dx + 1)]
    for dx, dy in pairs:
        assert line_walk(dx, dy) == one_tick(dx, dy), (dx, dy)

    half_walk = line_walk(6, 3)
    half_target = delta_sigma_quantized_carry(Q(1, 2), samples=6)
    assert half_walk == (0, 1, 0, 1, 0, 1)
    assert half_target.code == (1, 1, 1, 0, 0, 0)
    assert half_walk != half_target.code

    third_walk = line_walk(9, 3)
    third_target = delta_sigma_quantized_carry(Q(1, 3), samples=9)
    assert third_walk != third_target.code

    two_fifths_walk = line_walk(10, 4)
    two_fifths_target = delta_sigma_quantized_carry(Q(2, 5), samples=10)
    assert two_fifths_walk != two_fifths_target.code

    control = uniform_quantizer_carry(Q(3, 8), samples=8)
    assert control.code == (0,) * 8
    assert control.code != line_walk(8, 3)

    result = {
        "schema": "cent-hypothesis-evidence/1",
        "kind": "bresenham-one-tick-delta-sigma",
        "passed": True,
        "definition": {
            "line_walk": "y_n = floor(n*dy/dx), q_n = y_{n+1}-y_n",
            "delta_sigma": "one-tick floor feedback: r += dy/dx; q=floor(r); r-=q",
            "scope": "1 <= dx <= 32, 0 <= dy <= dx",
        },
        "checks": [
            {
                "name": "exact one-tick equivalence",
                "pairs": len(pairs),
                "status": "pass",
            },
            {
                "name": "existing two-tick target mismatch",
                "half_walk": list(half_walk),
                "half_target": list(half_target.code),
                "third_mismatch": list(third_walk) != list(third_target.code),
                "two_fifths_mismatch": (
                    list(two_fifths_walk) != list(two_fifths_target.code)
                ),
                "status": "pass",
            },
            {
                "name": "stateless uniform-quantizer control differs",
                "control_code": list(control.code),
                "walk_code": list(line_walk(8, 3)),
                "status": "pass",
            },
        ],
        "conclusion": (
            "one-tick Bresenham/delta-sigma equivalence is exact; the existing "
            "two-tick target is a different timing and is not equivalent"
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
