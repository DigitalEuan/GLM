#!/usr/bin/env python3
"""GLM-to-cent application audit.

The GLM evidence in this repository is a set of source/audit documents, not a
running model.  This suite therefore does three separate things:

1. records concrete GLM gaps that the source material already declares;
2. compiles scalar, free-license application probes for GLM-style operations
   and evaluates their exact-core programs;
3. records operations that remain gaps or currently overmatch a generic cent
   contract.  A generic multiplier is not accepted as a Griess product or a
   matrix-vector product.

The exact-core results are arithmetic checks, not physical-device tests.  The
only assembled physical route here is the KCL residual-add check.

Run without pytest: ``python3 tests/test_glm_application_audit.py``.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]

PASS = 0
FAIL = 0

ISSUES = [
    {
        "id": "arc-fill",
        "issue": "ARC's most frequent unmet need is primitive:fill (19 tasks).",
        "source": "expansion/hypothesis_engine_README.md",
    },
    {
        "id": "arc-recolour",
        "issue": "ARC's next unmet need is primitive:recolour (13 tasks).",
        "source": "expansion/hypothesis_engine_README.md",
    },
    {
        "id": "arc-unknown",
        "issue": "ARC reports primitive:unknown as an unmet need (10 tasks).",
        "source": "expansion/hypothesis_engine_README.md",
    },
    {
        "id": "rule30-prizes",
        "issue": "All three Rule 30 prize problems remain open; no finite certificate is claimed.",
        "source": "expansion/hypothesis_engine_README.md",
    },
    {
        "id": "griess-product",
        "issue": "No Griess multiplication tensor is implemented; move-class XOR is not a Griess product.",
        "source": "docs/LEECH_STUDY_AUDIT.md",
    },
    {
        "id": "monster-action",
        "issue": "No Monster representation, generators or action table is declared.",
        "source": "docs/LEECH_STUDY_AUDIT.md",
    },
    {
        "id": "lean-build",
        "issue": "The GLM Lean tree was not built, and its claimed wheel cross-check test is absent.",
        "source": "docs/GLM_LEAN_REVIEW.md",
    },
    {
        "id": "r-calculus-range",
        "issue": "The wheel turn leaves R-calculus and the range past D=87867 as unmet needs.",
        "source": "expansion/hypothesis_engine_README.md",
    },
]

# Scalar application probes.  They are deliberately labelled probes: the GLM
# source does not declare a transformer attention or softmax implementation.
APPLICATIONS = [
    {
        "id": "attention-score",
        "formula": "score = query * key / sqrt(d)",
        "ops": {"mult", "sqrt", "div"},
        "spice": "gap",
        "inputs": {"query": "3", "key": "2", "d": "4"},
        "expected": "3",
    },
    {
        "id": "softmax-cell",
        "formula": "weight = exp(score) / total",
        "ops": {"exp", "div"},
        "spice": "gap",
        "inputs": {"score": "0", "total": "2"},
        "expected": "1/2",
    },
    {
        "id": "layer-norm",
        "formula": "normalized = (x - mean) / sqrt(variance)",
        "ops": {"neg", "sum", "sqrt", "div"},
        "spice": "gap",
        "inputs": {"x": "5", "mean": "3", "variance": "4"},
        "expected": "1",
    },
    {
        "id": "affine-cell",
        "formula": "y = weight * x + bias",
        "ops": {"mult", "sum"},
        "spice": "gap",
        "inputs": {"weight": "2", "x": "3", "bias": "4"},
        "expected": "10",
    },
    {
        "id": "residual-add",
        "formula": "next = x + update",
        "ops": {"sum"},
        "spice": "match",
        "inputs": {"x": "5/7", "update": "2/7"},
        "expected": "1",
    },
    {
        "id": "exp-denominator",
        "formula": "denominator = exp(score1) + exp(score2)",
        "ops": {"exp", "sum"},
        "spice": "gap",
        "inputs": {"score1": "0", "score2": "0"},
        "expected": "2",
    },
]

GAP_QUERIES = [
    ("arc-fill-query", "fill a region"),
    ("arc-recolour-query", "recolour an object"),
    ("arc-unknown-query", "select an unknown ARC primitive"),
    ("rule30-xor-query", "compute XOR"),
    ("monster-action-query", "apply a Monster action"),
]


def expect(condition: bool, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def run_cent(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "cent"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def read_json(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout)


def parse_eval_value(stdout: str) -> Fraction:
    value = stdout.strip().rsplit("=", 1)[-1].strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1].strip()
    if not value:
        raise ValueError(f"no eval value in {stdout!r}")
    return Fraction(value)


def check_application(case: dict) -> list[str]:
    failures: list[str] = []
    compiled = run_cent("compile", case["formula"], "--json")
    if compiled.returncode != 0:
        return [f"compile exit {compiled.returncode}: {compiled.stderr.strip()}"]
    payload = read_json(compiled)
    dag_ops = {op.get("op") for op in payload.get("dag", [])}
    if payload.get("schema") != "cent-compile/1" or not payload.get("ok"):
        failures.append("compile schema/ok mismatch")
    if dag_ops != case["ops"]:
        failures.append(f"dag ops {sorted(dag_ops)}, expected {sorted(case['ops'])}")
    proposals = payload.get("proposals") or []
    if not proposals:
        failures.append("no delta proposals")
    if any(
        item.get("boundary", {}).get("status") != "not-fabricated"
        for item in proposals
    ):
        failures.append("a proposal lost its not-fabricated boundary")
    spice = payload.get("spice") or {}
    if spice.get("status") != case["spice"]:
        failures.append(f"spice status {spice.get('status')!r}, expected {case['spice']!r}")

    with tempfile.TemporaryDirectory() as out_dir:
        report = run_cent("report", case["formula"], "--save", out_dir)
        if report.returncode != 0:
            failures.append(f"report exit {report.returncode}: {report.stderr.strip()}")
            return failures
        materials = list(pathlib.Path(out_dir).glob("*.material.json"))
        if len(materials) != 1:
            failures.append(f"expected one material file, found {len(materials)}")
            return failures
        material = json.loads(materials[0].read_text(encoding="utf-8"))
        if not material.get("program"):
            failures.append("exact program is unavailable")
            return failures
        command = ["eval", str(materials[0])]
        for name, value in case["inputs"].items():
            command.extend(["--set", f"{name}={value}"])
        evaluated = run_cent(*command)
        if evaluated.returncode != 0:
            failures.append(f"eval exit {evaluated.returncode}: {evaluated.stderr.strip()}")
            return failures
        try:
            actual = parse_eval_value(evaluated.stdout)
        except ValueError as exc:
            failures.append(str(exc))
        else:
            expected = Fraction(case["expected"])
            if actual != expected:
                failures.append(f"eval {actual}, expected {expected}")
    return failures


def main() -> int:
    print("=" * 78)
    print("GLM APPLICATION AUDIT")
    print("=" * 78)

    issue_ids = [item["id"] for item in ISSUES]
    expect(
        len(ISSUES) == 8
        and len(set(issue_ids)) == 8
        and all((ROOT / item["source"]).is_file() for item in ISSUES),
        "eight sourced GLM issues are recorded with existing evidence paths",
    )

    app_ids = [item["id"] for item in APPLICATIONS]
    expect(
        len(APPLICATIONS) == 6
        and len(set(app_ids)) == 6
        and all(item["ops"] and item["inputs"] for item in APPLICATIONS),
        "six scalar application probes declare DAG operations and exact inputs",
    )

    for case in APPLICATIONS:
        failures = check_application(case)
        detail = "" if not failures else " — " + "; ".join(failures)
        expect(not failures, f"{case['id']}: {case['formula']}{detail}")

    route = run_cent(
        "assemble", "sum-kcl", "--input", "5/7", "--input-b", "2/7", "--json"
    )
    route_payload = read_json(route) if route.returncode == 0 else {}
    simulation = route_payload.get("simulation") or {}
    expect(
        route.returncode == 0
        and route_payload.get("schema") == "cent-route/1"
        and route_payload.get("route", {}).get("status") == "exact route model"
        and simulation.get("operation") == "sum"
        and simulation.get("result") == {"num": "1", "den": "1"}
        and simulation.get("expected") == {"num": "1", "den": "1"}
        and simulation.get("passed") is True,
        "the residual-add probe has an exact KCL route result",
    )

    tanh = run_cent("compile", "output = tanh(x)", "--json")
    tanh_payload = read_json(tanh) if tanh.returncode == 0 else {}
    with tempfile.TemporaryDirectory() as out_dir:
        tanh_report = run_cent("report", "output = tanh(x)", "--save", out_dir)
        tanh_materials = list(pathlib.Path(out_dir).glob("*.material.json"))
        tanh_material = (
            json.loads(tanh_materials[0].read_text(encoding="utf-8"))
            if tanh_materials
            else {}
        )
    expect(
        tanh.returncode == 0
        and tanh_payload.get("spice", {}).get("template") == "clipper"
        and len(tanh_payload.get("proposals") or []) == 1
        and tanh_report.returncode == 0
        and not tanh_material.get("program")
        and any("missing required parameter" in str(note) for note in tanh_material.get("notes", [])),
        "tanh yields a clipper proposal but no exact program without lo/hi",
    )

    for gap_id, query in GAP_QUERIES:
        result = run_cent("discover", query, "--json")
        payload = read_json(result) if result.returncode == 0 else {}
        expect(
            result.returncode == 0
            and payload.get("matched") is False
            and payload.get("methods") == []
            and payload.get("output_certificate", {}).get("status") == "gap",
            f"{gap_id}: {query} remains an explicit gap",
        )

    vector_softmax = run_cent(
        "compile", "weights = exp(score) / sum(exp(score))", "--json"
    )
    expect(
        vector_softmax.returncode == 2
        and vector_softmax.stdout.strip() == ""
        and "unsupported function call: sum()" in vector_softmax.stderr,
        "vector softmax aggregation is refused because sum() is not a cent function",
    )

    griess = run_cent("discover", "compute a Griess product", "--json")
    griess_payload = read_json(griess) if griess.returncode == 0 else {}
    griess_methods = griess_payload.get("methods") or []
    expect(
        griess.returncode == 0
        and griess_payload.get("matched") is True
        and len(griess_methods) == 4
        and all("multiply" in str(method.get("name", "")).lower() for method in griess_methods),
        "finding: Griess product currently overmatches four generic multiplier methods",
    )

    matvec = run_cent("discover", "compute a matrix-vector product", "--json")
    matvec_payload = read_json(matvec) if matvec.returncode == 0 else {}
    matvec_methods = matvec_payload.get("methods") or []
    expect(
        matvec.returncode == 0
        and matvec_payload.get("matched") is True
        and len(matvec_methods) == 4
        and all("multiply" in str(method.get("name", "")).lower() for method in matvec_methods),
        "finding: matrix-vector product currently overmatches four generic multiplier methods",
    )

    lab = run_cent(
        "explore",
        "addition",
        "--declarations",
        "examples/addition_declarations.json",
        "--glm",
        "--json",
    )
    lab_payload = read_json(lab) if lab.returncode == 0 else {}
    lab_summary = lab_payload.get("summary") or {}
    expect(
        lab.returncode == 0
        and lab_payload.get("schema") == "cent-computational-evidence/1"
        and lab_payload.get("target") == "glm"
        and lab_payload.get("evidence_tier") == "computational"
        and lab_payload.get("physical_transfer") is False
        and lab_payload.get("glm_call") is False
        and lab_summary.get("methods_passed") == 6
        and lab_summary.get("port_contracts") == 8
        and lab_summary.get("coverage_complete") is True,
        "the addition lab exposes six declared computational methods to GLM, not a physical transfer",
    )

    print()
    print("=" * 78)
    print(f"GLM APPLICATION AUDIT: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
