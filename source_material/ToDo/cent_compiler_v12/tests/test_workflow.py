#!/usr/bin/env python3
"""End-to-end workflow handoff checks.

Run without pytest: ``python3 tests/test_workflow.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import pipeline, workflow  # noqa: E402

PASS = 0
FAIL = 0


def expect(condition: bool, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def _cli(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "cent"), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def main() -> int:
    print("=" * 78)
    print("WORKFLOW HANDOFF")
    print("=" * 78)

    payload = workflow.build_workflow("compute a square root")
    selection = payload.get("selection") or {}
    stages = payload.get("stages") or {}
    expect(
        payload.get("schema") == workflow.SCHEMA
        and payload.get("ok") is True
        and selection.get("operation") == "sqrt"
        and selection.get("method_id"),
        "a problem statement selects a discovered method and operation",
    )
    expect(
        (payload.get("discovery") or {}).get("matched") is True
        and len((payload.get("discovery") or {}).get("methods") or ()) >= 5,
        "discovery runs before proposal selection",
    )
    expect(
        stages.get("discover", {}).get("status") == "pass"
        and stages.get("hypotheses", {}).get("status") == "pass"
        and stages.get("propose", {}).get("status") == "pass",
        "discovery, hypotheses and proposal stages are all recorded",
    )

    carry = workflow.build_workflow(operation="quantized_carry")
    expect(
        (carry.get("hypotheses") or {}).get("summary", {}).get("leads") == 1
        and (carry.get("stages") or {}).get("hypotheses", {}).get("status") == "gap"
        and "no automatic promotion" in (
            (carry.get("stages") or {}).get("hypotheses", {}).get("detail", "")
        ),
        "a keepable hypothesis lead stays pre-admission and is reported as a gap",
    )
    proposal = payload.get("proposal") or {}
    expect(
        (proposal.get("summary") or {}).get("proposals") == 3
        and (proposal.get("trial_summary") or {}).get("passed") == 1,
        "the proposal bundle runs its declared trial side-loop",
    )
    expect(
        stages.get("pipeline", {}).get("status") == "pass"
        and len((payload.get("pipeline") or {}).get("stages") or ()) == 3,
        "the exact sqrt pipeline is carried into the workflow",
    )
    expect(
        (payload.get("machine") or {}).get("id") == "sqrt-log"
        and (payload.get("machine") or {}).get("ok") is True,
        "the compatible route wrapper is carried into the workflow",
    )

    feedback_pipeline = pipeline.build_pipeline("sqrt", "sqrt-feedback")
    expect(
        feedback_pipeline.get("ok") is False
        and feedback_pipeline.get("mechanism") == "sqrt-feedback"
        and feedback_pipeline.get("checks", [{}])[0].get("status") == "gap",
        "a declared route without a cent-program returns an explicit pipeline gap",
    )

    method_id = selection["method_id"]
    explicit = workflow.build_workflow(
        "compute a square root", method_id=method_id
    )
    expect(
        (explicit.get("selection") or {}).get("method_id") == method_id,
        "an explicit discovery method id is preserved",
    )

    methods = (payload.get("discovery") or {}).get("methods") or ()
    feedback_id = next(
        method["id"] for method in methods if "analog-feedback" in method["id"]
    )
    fluidic_id = next(
        method["id"] for method in methods if "fluidic" in method["id"]
    )
    feedback = workflow.build_workflow(
        "compute a square root", method_id=feedback_id
    )
    expect(
        (feedback.get("machine") or {}).get("id") == "sqrt-feedback"
        and (feedback.get("stages") or {}).get("pipeline", {}).get("status") == "gap",
        "an analog-feedback method selects its machine and exposes the pipeline gap",
    )
    fluidic = workflow.build_workflow(
        "compute a square root", method_id=fluidic_id
    )
    expect(
        (fluidic.get("machine") or {}).get("id") is None
        and (fluidic.get("stages") or {}).get("machine", {}).get("status") == "gap",
        "a method without a matching wrapper leaves a machine gap",
    )

    compiled = workflow.build_workflow(formula="y = 1/x")
    expect(
        (compiled.get("selection") or {}).get("operation") == "reciprocal"
        and (compiled.get("stages") or {}).get("compile", {}).get("status") == "pass",
        "a compiled formula feeds the proposal operation",
    )
    expect(
        (compiled.get("status") == "partial")
        and (compiled.get("stages") or {}).get("pipeline", {}).get("status") == "gap"
        and (compiled.get("stages") or {}).get("machine", {}).get("status") == "gap",
        "unsupported pipeline and machine stages remain explicit gaps",
    )

    try:
        workflow.build_workflow("compute a square root", method_id="not-a-method")
    except ValueError as exc:
        expect("not-a-method" in str(exc), str(exc))
    else:
        expect(False, "an unknown method id must fail explicitly")

    cli = _cli("workflow", "compute a square root", "--json")
    try:
        cli_payload = json.loads(cli.stdout)
    except json.JSONDecodeError:
        cli_payload = {}
    expect(
        cli.returncode == 0 and cli_payload.get("schema") == workflow.SCHEMA,
        "the workflow CLI emits its manifest",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        written = workflow.write_workflow(payload, tmpdir)
        root = pathlib.Path(tmpdir)
        names = {path.name for path in written}
        manifest = json.loads((root / "workflow.json").read_text())
        expect(
            {"workflow.json", "workflow.md", "discovery.json", "hypotheses.json", "pipeline.json"}
            <= names
            and {"machine.json", "machine.md", "machine.cir"}
            <= {path.name for path in (root / "machine").iterdir()}
            and (root / "proposals" / "index.json").exists(),
            "the output directory contains the manifest and stage artifacts",
        )
        expect(
            manifest.get("artifacts", {}).get("workflow.md") == "workflow.md"
            and manifest.get("artifacts", {}).get("proposals") == "proposals/",
            "the manifest records workflow and nested artifacts",
        )

    print("\n" + "=" * 78)
    if FAIL:
        print(f"WORKFLOW: {PASS}/{PASS + FAIL} checks passed, {FAIL} failed")
        return 1
    print(f"WORKFLOW: {PASS}/{PASS + FAIL} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
