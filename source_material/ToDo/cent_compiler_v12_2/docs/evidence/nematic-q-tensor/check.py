#!/usr/bin/env python3
"""Exact evidence for the nematic Q-tensor invariant obstruction."""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from cent_compiler.envelope import orientation_envelope  # noqa: E402

Q = Fraction


def q_tensor(n: tuple[Q, Q], order: Q = Q(1)) -> tuple[tuple[Q, Q], tuple[Q, Q]]:
    x, y = n
    return (
        (order * (2 * x * x - 1), order * 2 * x * y),
        (order * 2 * x * y, order * (2 * y * y - 1)),
    )


def invariants(matrix: tuple[tuple[Q, Q], tuple[Q, Q]]) -> tuple[Q, Q]:
    a, b = matrix[0]
    c, d = matrix[1]
    return a * a + 2 * b * c + d * d, a * d - b * c


def directions(n: tuple[Q, Q]) -> tuple[tuple[Q, Q], tuple[Q, Q]]:
    return n, (-n[1], n[0])


def main() -> int:
    n1 = (Q(1), Q(0))
    n2 = (Q(3, 5), Q(4, 5))
    q1 = q_tensor(n1)
    q2 = q_tensor(n2)
    inv1 = invariants(q1)
    inv2 = invariants(q2)
    assert inv1 == inv2 == (Q(2), Q(-1))
    assert q1 != q2

    points = ((Q(0), Q(0)), (Q(2), Q(0)), (Q(0), Q(1)))
    env1 = orientation_envelope(points, directions(n1))
    env2 = orientation_envelope(points, directions(n2))
    area1 = env1["summary"]["best_area"]
    area2 = env2["summary"]["best_area"]
    assert area1 == {"num": "2", "den": "1"}
    assert area2 == {"num": "66", "den": "25"}
    assert area1 != area2
    assert env1["best"]["direction"] != env2["best"]["direction"]

    result = {
        "schema": "cent-hypothesis-evidence/1",
        "kind": "q-tensor-invariant-obstruction",
        "passed": True,
        "definition": {
            "tensor": "Q = S * (2 n n^T - I2)",
            "normalization": "||n|| = 1, n ~ -n, S in [0, 1]",
            "field": "uniform; no spatial boundary-value problem",
        },
        "checks": [
            {
                "name": "same scalar invariants",
                "q1": {"tr_q2": "2", "det": "-1"},
                "q2": {"tr_q2": "2", "det": "-1"},
                "status": "pass",
            },
            {
                "name": "different director eigenframes",
                "q1": [[str(value) for value in row] for row in q1],
                "q2": [[str(value) for value in row] for row in q2],
                "status": "pass",
            },
            {
                "name": "invariant-only map cannot select an envelope",
                "reason": "same invariants, different exact envelopes",
                "status": "pass",
            },
        ],
        "exact_envelopes": {
            "n1": {"directions": [["1", "0"], ["0", "1"]], "area": area1},
            "n2": {
                "directions": [["3/5", "4/5"], ["-4/5", "3/5"]],
                "area": area2,
            },
        },
        "conclusion": (
            "no map from scalar Q-tensor invariants alone to finite-direction "
            "projections exists; orientation is an additional input"
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
