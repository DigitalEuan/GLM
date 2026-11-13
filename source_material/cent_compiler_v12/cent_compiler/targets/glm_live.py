"""Live external target for the Geometric Language Machine (GLM).

This adapter executes the real ``GLM.py`` CLI from the adjacent GLM repository
(or a path supplied through ``GLM_CLI``) and reads the exact value from its
``--result`` JSON.  It currently supports only the exact KCL ``sum`` and
``difference`` operations; it does not call a model, measure latency, claim a
bit budget or turn the reference target into a GLM integration.

The live target is deliberately separate from ``glm-reference``: reference
certificates remain ``target-simulated``, while a passing live certificate is
``target-integrated`` because an external process actually ran.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from ..exact import Q, q_to_json
from ..transfer import TargetProfile
from .glm import KCL_DIFFERENCE_VECTORS, KCL_VECTORS, KclVector

TARGET_ID = "glm-live"
ADAPTER_SCHEMA = "cent-glm-live-adapter/1"
ENV_VAR = "GLM_CLI"
_VALUE_RE = re.compile(r"(?:value=|number\s+)(-?\d+(?:/\d+)?)")


class GLMLiveError(ValueError):
    """The external GLM interface is unavailable or returned no exact answer."""


def glm_cli_path(path: str | Path | None = None) -> Path:
    """Resolve the GLM CLI path, preferring ``GLM_CLI`` over the sibling tree."""
    configured = path or os.environ.get(ENV_VAR)
    if configured:
        candidate = Path(configured).expanduser()
    else:
        candidate = (
            Path(__file__).resolve().parents[3]
            / "glm-study"
            / "src"
            / "GLM.py"
        )
    if not candidate.is_file():
        raise GLMLiveError(
            f"GLM CLI not found at {candidate}; set {ENV_VAR} to a runnable GLM.py"
        )
    return candidate


def _fraction(value: Any, name: str) -> Q:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise GLMLiveError(f"{name} must be an exact rational, not boolean")
    try:
        return Fraction(str(value).strip())
    except (ValueError, ZeroDivisionError) as exc:
        raise GLMLiveError(f"{name} is not an exact rational: {value!r}") from exc


def _query(operation: str, a: Q, b: Q) -> str:
    token = "+" if operation == "sum" else "-"
    return f"what is ({a}) {token} ({b})"


def _value_from_result(row: dict[str, Any]) -> Q:
    for item in row.get("witness") or ():
        if isinstance(item, str):
            match = _VALUE_RE.search(item)
            if match:
                return Fraction(match.group(1))
    answer = str(row.get("answer") or "")
    match = _VALUE_RE.search(answer)
    if match:
        return Fraction(match.group(1))
    raise GLMLiveError("GLM answered without an exact rational value in its witness")


@dataclass(frozen=True)
class LiveRun:
    """One real GLM CLI execution for an exact KCL operation."""

    adapter: str
    operation: str
    a: Q
    b: Q
    expected: Q
    value: Q
    answer: str
    query: str
    cli: str
    returncode: int
    witness: tuple[str, ...]
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "operation": self.operation,
            "a": q_to_json(self.a),
            "b": q_to_json(self.b),
            "expected": q_to_json(self.expected),
            "value": q_to_json(self.value),
            "answer": self.answer,
            "query": self.query,
            "cli": self.cli,
            "returncode": self.returncode,
            "witness": list(self.witness),
            "passed": self.passed,
        }


def run_live_kcl(
    operation: str,
    a: Any,
    b: Any,
    *,
    cli: str | Path | None = None,
    timeout: int = 60,
) -> LiveRun:
    """Execute one exact GLM query through the real CLI and parse its value."""
    if operation not in {"sum", "difference"}:
        raise GLMLiveError(f"live GLM adapter does not support {operation!r}")
    a_q = _fraction(a, "a")
    b_q = _fraction(b, "b")
    expected = a_q + b_q if operation == "sum" else a_q - b_q
    path = glm_cli_path(cli)
    query = _query(operation, a_q, b_q)
    try:
        completed = subprocess.run(
            [sys.executable, str(path), "-q", query, "--result"],
            cwd=str(path.parent.parent),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GLMLiveError(f"GLM CLI could not be executed: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        raise GLMLiveError(
            "GLM CLI failed with exit "
            f"{completed.returncode}: {detail[-1] if detail else 'no stderr'}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GLMLiveError("GLM CLI did not return JSON") from exc
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise GLMLiveError("GLM CLI returned no result row")
    row = payload[0]
    if row.get("status") != "answered":
        raise GLMLiveError(
            f"GLM refused the query: {row.get('refusal') or row.get('status')}"
        )
    value = _value_from_result(row)
    witness = tuple(str(item) for item in row.get("witness") or ())
    return LiveRun(
        adapter=f"glm-live-kcl-{operation}",
        operation=operation,
        a=a_q,
        b=b_q,
        expected=expected,
        value=value,
        answer=str(row.get("answer") or ""),
        query=query,
        cli=str(path),
        returncode=completed.returncode,
        witness=witness,
        passed=value == expected,
    )


def run_live_sum(a: Any, b: Any) -> LiveRun:
    return run_live_kcl("sum", a, b)


def run_live_difference(a: Any, b: Any) -> LiveRun:
    return run_live_kcl("difference", a, b)


@dataclass(frozen=True)
class LiveAdapterSpec:
    """A declared executable adapter backed by the real GLM subprocess."""

    id: str
    operation: str
    mechanism: str
    entrypoint: str
    function: Callable[..., LiveRun]
    description: str
    vectors: tuple[KclVector, ...]
    kind: str

    @property
    def path(self) -> str:
        return "cent_compiler/targets/glm_live.py"

    @property
    def invocation(self) -> str:
        return f"{self.entrypoint}(a, b)"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": ADAPTER_SCHEMA,
            "id": self.id,
            "operation": self.operation,
            "mechanism": self.mechanism,
            "target": TARGET_ID,
            "kind": "external-subprocess",
            "operation_kind": self.kind,
            "path": self.path,
            "entrypoint": self.entrypoint,
            "invocation": self.invocation,
            "precision": "exact rational parsed from the GLM result witness",
            "description": self.description,
            "test_vectors": [vector.id for vector in self.vectors],
        }


LIVE_SUM_ADAPTER = LiveAdapterSpec(
    id="glm-live-kcl-exact-sum",
    operation="sum",
    mechanism="kcl-conservation",
    entrypoint="run_live_sum",
    function=run_live_sum,
    description=(
        "Run an exact parenthesized sum query through the real GLM CLI and read "
        "the exact rational value from its result witness."
    ),
    vectors=KCL_VECTORS,
    kind="exact_sum",
)

LIVE_DIFFERENCE_ADAPTER = LiveAdapterSpec(
    id="glm-live-kcl-exact-difference",
    operation="difference",
    mechanism="kcl-conservation",
    entrypoint="run_live_difference",
    function=run_live_difference,
    description=(
        "Run an exact parenthesized difference query through the real GLM CLI "
        "and read the exact rational value from its result witness."
    ),
    vectors=KCL_DIFFERENCE_VECTORS,
    kind="exact_difference",
)

ADAPTERS: dict[tuple[str, str], LiveAdapterSpec] = {
    (LIVE_SUM_ADAPTER.operation, LIVE_SUM_ADAPTER.mechanism): LIVE_SUM_ADAPTER,
    (LIVE_DIFFERENCE_ADAPTER.operation, LIVE_DIFFERENCE_ADAPTER.mechanism): LIVE_DIFFERENCE_ADAPTER,
}


def get_adapter(operation: str, mechanism: str | None = None) -> LiveAdapterSpec:
    """Return the declared live adapter, or fail explicitly."""
    matches = [
        spec
        for (candidate_operation, candidate_mechanism), spec in ADAPTERS.items()
        if candidate_operation == operation
        and (mechanism is None or candidate_mechanism == mechanism)
    ]
    if not matches:
        detail = f"{operation!r}"
        if mechanism is not None:
            detail += f" via {mechanism!r}"
        known = ", ".join(f"{op}/{mech}" for op, mech in sorted(ADAPTERS))
        raise KeyError(f"no live GLM adapter for {detail}; declared: {known}")
    if len(matches) > 1:
        raise ValueError(
            f"ambiguous live GLM adapter for {operation!r}; declare a mechanism"
        )
    return matches[0]


GLM_LIVE_TARGET = TargetProfile(
    id=TARGET_ID,
    kind="software",
    description=(
        "Live subprocess target for exact KCL sum and difference through the "
        "external Geometric Language Machine CLI. It is a real interface, not "
        "a model score or a measured-performance target."
    ),
    interface={
        "contract": "subprocess: GLM.py -q <exact expression> --result",
        "operations": ["sum", "difference"],
        "interfaces": {
            "sum": {
                "inputs": {"a": "exact rational", "b": "exact rational"},
                "outputs": {"total": "exact rational from GLM witness"},
                "state": "none",
                "feedback": "none",
            },
            "difference": {
                "inputs": {"a": "exact rational", "b": "exact rational"},
                "outputs": {"total": "exact rational from GLM witness"},
                "state": "none",
                "feedback": "none",
            },
        },
        "precision": "exact rational parsed from the GLM result witness",
        "latency": {
            "kind": "not measured; subprocess execution only",
            "status": "not declared",
        },
        "bit_budget": {
            "kind": "not measured; exact rational result",
            "status": "not declared",
        },
        "cli": f"${ENV_VAR} or sibling glm-study/src/GLM.py",
    },
    constraints={
        "real_glm_interface": True,
        "subprocess_transport": True,
        "exact_rational": True,
        "no_glm_performance_claim": True,
        "no_latency_or_bit_budget_claim": True,
    },
    evidence_required=(
        "real GLM subprocess execution",
        "fixed target vectors",
        "pass/fail certificate",
    ),
    provenance=(
        "https://github.com/DigitalEuan/GLM",
        "glm-study/src/GLM.py",
        "cent_compiler/targets/glm_live.py",
    ),
    gaps=(
        "no performance, latency or bit-budget measurement is claimed",
        "only exact KCL sum and difference are wired",
        "requires a runnable external GLM package and CLI",
    ),
)
GLM_LIVE_TARGET.validate()


__all__ = [
    "ADAPTERS",
    "ADAPTER_SCHEMA",
    "ENV_VAR",
    "GLMLiveError",
    "GLM_LIVE_TARGET",
    "LIVE_DIFFERENCE_ADAPTER",
    "LIVE_SUM_ADAPTER",
    "LiveAdapterSpec",
    "LiveRun",
    "TARGET_ID",
    "get_adapter",
    "glm_cli_path",
    "run_live_difference",
    "run_live_kcl",
    "run_live_sum",
]
