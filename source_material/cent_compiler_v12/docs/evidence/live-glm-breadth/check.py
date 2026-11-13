#!/usr/bin/env python3
"""Reproducible probe for the current GLM live-breadth refusal.

The probe checks the exact external CLI, not a model score or a latency result.
It records why T3 refuses to add another live operation for this interface:

* GLM refuses the tested ``sqrt`` and ``exp`` queries;
* GLM answers exact ``mult`` and ``div`` queries, but neither operation has a
  production mechanism card;
* the only declared live adapters remain KCL ``sum`` and ``difference``.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from cent_compiler.targets import glm_live  # noqa: E402

NUMBER_RE = re.compile(r"number\s+(-?\d+/\d+)")
EXPECTED_ARITHMETIC = {
    "what is (1/2) * (1/3)": "1/6",
    "what is (1/2) / (1/3)": "3/2",
}
REFUSED_OPERATIONS = (
    "what is sqrt(2)",
    "what is sqrt(9)",
    "what is exp(0)",
)


def run_query(cli: Path, query: str) -> dict:
    """Run one query and return its result row; refusal rows are valid data."""
    completed = subprocess.run(
        [sys.executable, str(cli), "-q", query, "--result"],
        cwd=str(cli.parent.parent),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        detail = (completed.stderr or "").strip().splitlines()
        raise RuntimeError(
            f"GLM returned no JSON for {query!r}: {detail[-1] if detail else 'no stderr'}"
        ) from exc
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise RuntimeError(f"GLM returned no result row for {query!r}")
    return payload[0]


def exact_value(row: dict) -> Fraction:
    """Read the exact rational rendered in the answer or witness."""
    for text in (row.get("answer") or "", *(row.get("witness") or ())):
        match = NUMBER_RE.search(str(text))
        if match:
            return Fraction(match.group(1))
    raise RuntimeError("GLM answered without an exact rational number")


def main() -> int:
    try:
        cli = glm_live.glm_cli_path()
    except (glm_live.GLMLiveError, OSError) as exc:
        print(
            json.dumps(
                {
                    "schema": "cent-live-breadth-evidence/1",
                    "kind": "live-glm-breadth",
                    "passed": False,
                    "status": "unavailable",
                    "error": str(exc),
                    "conclusion": (
                        "The live breadth refusal cannot be reproduced without the "
                        "declared GLM CLI."
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    checks = []
    for query in REFUSED_OPERATIONS:
        row = run_query(cli, query)
        refusal = str(row.get("refusal") or "")
        passed = row.get("status") == "refused" and "names no carrier" in refusal
        checks.append(
            {
                "name": "unsupported operation refused",
                "query": query,
                "status": row.get("status"),
                "detail": refusal,
                "passed": passed,
            }
        )

    for query, expected in EXPECTED_ARITHMETIC.items():
        row = run_query(cli, query)
        value = exact_value(row) if row.get("status") == "answered" else None
        checks.append(
            {
                "name": "exact arithmetic without a mechanism card",
                "query": query,
                "status": row.get("status"),
                "value": str(value) if value is not None else None,
                "expected": expected,
                "passed": row.get("status") == "answered"
                and value == Fraction(expected),
            }
        )

    live_keys = sorted(glm_live.ADAPTERS)
    declared_operations = list(glm_live.GLM_LIVE_TARGET.interface.get("operations") or ())
    adapter_scope_ok = live_keys == [
        ("difference", "kcl-conservation"),
        ("sum", "kcl-conservation"),
    ] and declared_operations == ["sum", "difference"]
    checks.append(
        {
            "name": "live adapter scope remains KCL sum/difference",
            "adapters": [f"{operation}/{mechanism}" for operation, mechanism in live_keys],
            "operations": declared_operations,
            "passed": adapter_scope_ok,
        }
    )

    passed = all(check["passed"] for check in checks)
    result = {
        "schema": "cent-live-breadth-evidence/1",
        "kind": "live-glm-breadth",
        "passed": passed,
        "cli": str(cli),
        "checks": checks,
        "conclusion": (
            "T3 refuses to add another live operation for the current GLM "
            "interface: sqrt/exp are refused, and mult/div are exact but have "
            "no production mechanism cards. The live adapters remain exact KCL "
            "sum/difference only. This is a scope refusal, not a claim that "
            "additional live operations are impossible."
        ),
        "reopen_when": [
            "a declared mechanism card with a real source law, fixed vectors and an adapter exists for mult/div",
            "the live interface exposes an exact, reproducible sqrt or exp result with fixed vectors",
            "the broader live target declares its external interface and any measured latency/bit budgets",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
