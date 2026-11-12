#!/usr/bin/env python3
"""Focused tests for constrained design selection and verification plans.

Run without pytest: ``python3 tests/test_design.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler.design import (  # noqa: E402
    COMPARISON_SCHEMA,
    PI_BOUNDS,
    _bandwidth_result,
    _pareto_layers,
    compare_routes,
    fabrication_audit,
    solve_route,
)
from cent_compiler.device import bind_feedback_sqrt  # noqa: E402
from cent_compiler.exact import CentError, ErrorCode  # noqa: E402
from cent_compiler.fabrication import DRCRules  # noqa: E402

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


def raises_code(callable_, code: ErrorCode) -> bool:
    try:
        callable_()
    except CentError as exc:
        return exc.code == code
    return False


def main() -> int:
    print("=" * 78)
    print("CONSTRAINED DESIGN")
    print("=" * 78)

    delta = solve_route("delta-sigma")
    expect(delta.status == "solved", "the default delta-sigma design is solved")
    expect(
        delta.selected is not None
        and delta.selected.option.name == "offset-1/200"
        and delta.selected.option.cost == 1,
        "the cheapest passing comparator grade is selected",
    )
    expect(
        delta.selected is not None
        and delta.selected.binding is not None
        and delta.selected.binding.passed,
        "the selected delta-sigma binding passes its exact checks",
    )
    expect(
        delta.ranking is not None
        and delta.ranking.profile == "exact-static"
        and delta.ranking.front
        == tuple(item.option.name for item in delta.candidates)
        and all(item.pareto_rank == 1 for item in delta.candidates)
        and delta.ranking.selected == "offset-1/200",
        "the exact-static front exposes every non-dominated candidate",
    )
    expect(
        delta.ranking is not None
        and [item.name for item in delta.ranking.objectives]
        == ["cost", "max_relative_error"]
        and delta.ranking.rule.startswith("lowest declared cost"),
        "the static profile declares only cost and worst-probe error",
    )
    expect(
        len(delta.candidates) == 4
        and len({item.option.name for item in delta.candidates}) == 4,
        "all four declared delta-sigma candidates are exposed",
    )
    delta_audit = delta.as_dict()["fabrication_audit"]
    expect(
        delta_audit["status"] == "drc-pass"
        and delta_audit["passed"] is True
        and delta_audit["advisory"] is True
        and delta_audit["checks_passed"] == delta_audit["check_count"] == 10
        and len(delta_audit["parasitics"]) == delta_audit["parasitic_count"]
        and not delta_audit["failed_checks"],
        "a solved design carries a passing advisory fabrication audit",
    )
    expect(
        delta.verification_plan[0].name == "Declared exact binding"
        and delta.verification_plan[0].status == "pass"
        and delta.verification_plan[0].command is not None,
        "the verification plan starts with an executable exact-binding check",
    )
    expect(
        any(
            step.name == "Reference netlist / floorplan"
            and step.status == "pass"
            and step.command is not None
            and "physical" in step.command
            for step in delta.verification_plan
        ),
        "the plan points at the reference netlist/floorplan emitter",
    )
    expect(
        any(
            step.name == "Dynamic behavior"
            and step.status == "partial"
            and step.command is not None
            and "dynamics" in step.command
            for step in delta.verification_plan
        ),
        "the plan exposes the partial sampled-data check",
    )

    tight_delta = solve_route("delta-sigma", accuracy=Fraction(1, 500))
    expect(
        tight_delta.status == "solved"
        and tight_delta.selected is not None
        and tight_delta.selected.option.name == "offset-1/1000",
        "a tighter accuracy constraint selects the tighter comparator grade",
    )
    no_budget = solve_route(
        "delta-sigma", accuracy=Fraction(1, 500), max_cost=Fraction(2)
    )
    expect(
        no_budget.status == "gap" and no_budget.selected is None,
        "a cost ceiling can reject every otherwise-passing candidate",
    )
    expect(
        any(
            "cost 3 exceeds declared maximum 2" in failure
            for item in no_budget.candidates
            for failure in item.failures
        ),
        "the rejected candidate reports the exact cost violation",
    )
    no_budget_audit = no_budget.as_dict()["fabrication_audit"]
    expect(
        no_budget_audit["status"] == "not-run"
        and no_budget_audit["passed"] is None
        and no_budget_audit["check_count"] == 0
        and no_budget_audit["gaps"],
        "an unsolved design reports fabrication as not-run instead of inventing geometry",
    )

    log = solve_route("sqrt-log")
    expect(
        log.status == "solved"
        and log.selected is not None
        and log.selected.option.name == "precision-8",
        "the cheapest declared log-domain precision is selected by default",
    )
    failed_audit = fabrication_audit(
        log, DRCRules(bus_pitch=Fraction(1, 4))
    )
    expect(
        failed_audit["status"] == "drc-gap"
        and failed_audit["passed"] is False
        and "Copper clearance" in failed_audit["failed_checks"]
        and any(check["status"] == "gap" for check in failed_audit["checks"]),
        "a forced DRC rule failure is reported by the advisory audit, not hidden",
    )
    expect(
        len(log.candidates) == 4,
        "all four declared log-domain precisions are exposed",
    )
    expect(
        any(
            step.name == "Dynamic behavior"
            and step.status == "partial"
            and step.command is not None
            and "dynamics" in step.command
            for step in log.verification_plan
        ),
        "the log-domain plan exposes its partial nonlinear model",
    )
    log_range = solve_route(
        "sqrt-log", input_min=Fraction(1, 2), input_max=Fraction(1)
    )
    expect(
        log_range.status == "solved"
        and log_range.selected is not None
        and log_range.selected.option.name == "precision-20",
        "range probing selects a precision that passes at both endpoints",
    )
    expect(
        len(log_range.selected.probes) == 2
        and log_range.selected.range_certificate is not None
        and log_range.selected.range_certificate.status == "pass"
        and log_range.selected.range_certificate.error_direction == "decreasing"
        and log_range.selected.range_certificate.max_error_at == Fraction(1, 2),
        "the declared range checks both endpoints and carries a continuous certificate",
    )
    delta_range = solve_route(
        "delta-sigma", input_min=Fraction(1, 4), input_max=Fraction(3, 4)
    )
    expect(
        delta_range.selected is not None
        and delta_range.selected.range_certificate is not None
        and delta_range.selected.range_certificate.status == "pass"
        and any(
            step.name == "Continuous range certificate" and step.status == "pass"
            for step in delta_range.verification_plan
        ),
        "a constant-error route exposes its continuous range certificate in the plan",
    )
    expect(
        any(
            item.option.name == "precision-8"
            and any("enclosure width" in failure for failure in item.failures)
            for item in log_range.candidates
        ),
        "the lower precision is rejected at the tighter endpoint",
    )

    feedback = solve_route("sqrt-feedback")
    expect(
        feedback.status == "solved"
        and feedback.selected is not None
        and feedback.selected.option.name == "gain-1000000"
        and feedback.selected.option.cost == 2,
        "the cheapest feedback gain that closes the loop is selected",
    )
    feedback_budget = solve_route("sqrt-feedback", max_cost=Fraction(1))
    expect(
        feedback_budget.status == "gap",
        "a one-unit budget cannot buy the passing feedback gain",
    )
    expect(
        any(
            "cost 2 exceeds declared maximum 1" in failure
            for item in feedback_budget.candidates
            for failure in item.failures
        ),
        "the feedback candidate reports its over-budget cost",
    )
    feedback_tight = solve_route(
        "sqrt-feedback", accuracy=Fraction(1, 500)
    )
    expect(
        feedback_tight.status == "gap",
        "the declared feedback alternatives honestly fail a 0.2% target",
    )
    feedback_bandwidth = solve_route(
        "sqrt-feedback", min_bandwidth=Fraction(100_000)
    )
    expect(
        feedback_bandwidth.status == "solved"
        and feedback_bandwidth.selected is not None
        and feedback_bandwidth.selected.bandwidth is not None
        and feedback_bandwidth.selected.bandwidth.passed
        and feedback_bandwidth.selected.bandwidth.slowest is not None
        and feedback_bandwidth.selected.bandwidth.slowest.symbol == "tau_cl",
        "a 100 kHz minimum passes the declared feedback closed-loop pole",
    )
    log_bandwidth = solve_route("sqrt-log", min_bandwidth=Fraction(100_000))
    expect(
        log_bandwidth.status == "gap"
        and log_bandwidth.selected is None
        and any(
            "bandwidth:" in failure
            for item in log_bandwidth.candidates
            for failure in item.failures
        ),
        "the slower log-domain pole is rejected with an exact bandwidth reason",
    )
    delta_bandwidth = solve_route(
        "delta-sigma", min_bandwidth=Fraction(1_000)
    )
    expect(
        delta_bandwidth.status == "solved"
        and delta_bandwidth.selected is not None
        and delta_bandwidth.selected.bandwidth is not None
        and delta_bandwidth.selected.bandwidth.passed
        and delta_bandwidth.selected.bandwidth.slowest is not None
        and delta_bandwidth.selected.bandwidth.slowest.symbol == "tau",
        "the delta-sigma integrator pole passes a 1 kHz minimum",
    )
    expect(
        feedback.ranking is not None
        and feedback.ranking.front == ("gain-1000000", "gain-10000000")
        and feedback.ranking.excluded == ("gain-100000",)
        and feedback.selected is not None
        and feedback.selected.pareto_rank == 1,
        "the feedback front excludes the infeasible gain and keeps both passing points",
    )

    expect(
        delta_bandwidth.ranking is not None
        and delta_bandwidth.ranking.profile == "dynamic-aware"
        and [item.name for item in delta_bandwidth.ranking.objectives]
        == ["cost", "max_relative_error", "certified_bandwidth"]
        and delta_bandwidth.ranking.selected == "offset-1/200",
        "a bandwidth request switches to the dynamic-aware front",
    )
    explicit_static = solve_route(
        "delta-sigma", min_bandwidth=Fraction(1_000), ranking="exact-static"
    )
    expect(
        explicit_static.ranking is not None
        and explicit_static.ranking.profile == "exact-static"
        and len(explicit_static.ranking.objectives) == 2,
        "an explicit static profile keeps the bandwidth filter but omits its objective",
    )
    layers = _pareto_layers(
        {
            "cheap": (Fraction(1), Fraction(5)),
            "mid": (Fraction(2), Fraction(2)),
            "dominated": (Fraction(3), Fraction(6)),
            "precise": (Fraction(4), Fraction(1)),
        },
        ("min", "min"),
    )
    expect(
        layers[0] == ("cheap", "mid", "precise")
        and layers[1] == ("dominated",),
        "exact non-dominated sorting reports a dominated second layer",
    )

    feedback_binding = bind_feedback_sqrt()
    feedback_tau = next(
        item.time_constant
        for item in feedback_binding.poles
        if item.symbol == "tau_cl"
    )
    straddle = _bandwidth_result(
        feedback_binding, 1 / (2 * PI_BOUNDS.midpoint * feedback_tau)
    )
    expect(
        straddle.status == "gap" and "straddles" in straddle.detail,
        "a target inside the certified pi enclosure stays an explicit gap",
    )

    try:
        payload = delta.as_dict()
        json.dumps(payload, ensure_ascii=False)
        serialisable = True
    except (TypeError, ValueError):
        payload = {}
        serialisable = False
    expect(serialisable, "the design result is JSON-serialisable")
    expect(
        payload.get("schema") == "cent-design/1"
        and payload.get("selected", {}).get("binding", {}).get("passed") is True
        and payload.get("fabrication_audit", {}).get("status") == "drc-pass",
        "the selected JSON carries the passing exact binding and advisory audit",
    )
    expect(
        payload.get("ranking", {}).get("profile") == "exact-static"
        and payload.get("ranking", {}).get("front")
        == ["offset-1/200", "offset-1/500", "offset-1/1000", "offset-1/2000"]
        and payload.get("selected", {}).get("pareto_rank") == 1,
        "the design JSON carries the exact Pareto front and rank",
    )

    expect(
        raises_code(
            lambda: solve_route("sqrt-log", accuracy=Fraction(0)),
            ErrorCode.DOMAIN_ERROR,
        ),
        "a nonpositive accuracy is rejected",
    )
    expect(
        raises_code(
            lambda: solve_route("sqrt-log", min_bandwidth=Fraction(0)),
            ErrorCode.DOMAIN_ERROR,
        ),
        "a nonpositive minimum bandwidth is rejected",
    )
    expect(
        raises_code(
            lambda: solve_route(
                "sqrt-log", input_min=Fraction(2), input_max=Fraction(1)
            ),
            ErrorCode.INVALID_INPUT,
        ),
        "an inverted input range is rejected",
    )
    expect(
        raises_code(
            lambda: solve_route(
                "sqrt-log",
                input_value=Fraction(1, 2),
                input_min=Fraction(1),
                input_max=Fraction(1),
            ),
            ErrorCode.INVALID_INPUT,
        ),
        "an operating point outside the declared range is rejected",
    )
    expect(
        raises_code(
            lambda: solve_route("unknown-route"),
            ErrorCode.UNSUPPORTED,
        ),
        "an unknown design space is rejected",
    )
    expect(
        raises_code(
            lambda: solve_route("sqrt-log", ranking="weighted"),
            ErrorCode.INVALID_INPUT,
        ),
        "an unknown ranking profile is rejected",
    )
    expect(
        raises_code(
            lambda: solve_route("sqrt-log", ranking="dynamic-aware"),
            ErrorCode.INVALID_INPUT,
        ),
        "dynamic-aware ranking requires a declared bandwidth target",
    )
    rendered = log_range.render_text()
    expect(
        "CONSTRAINED DESIGN" in rendered
        and "precision-20" in rendered
        and "Pareto ranking" in rendered
        and "rank 1" in rendered
        and "Verification plan" in rendered
        and "Reference netlist / floorplan" in rendered,
        "the human renderer shows the selected design and plan",
    )

    command = [
        sys.executable,
        str(ROOT / "cent"),
        "solve",
        "sqrt-feedback",
        "--min-bandwidth",
        "100000",
        "--json",
    ]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, timeout=120
    )
    cli_payload = {}
    cli_ok = result.returncode == 0
    if cli_ok:
        try:
            cli_payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            cli_ok = False
    expect(cli_ok, f"cent solve sqrt-feedback succeeds: {result.stderr[:160]}")
    expect(
        cli_payload.get("schema") == "cent-design/1"
        and cli_payload.get("design", {}).get("status") == "solved"
        and cli_payload.get("design", {}).get("selected", {})
        .get("binding", {})
        .get("passed")
        is True
        and cli_payload.get("design", {}).get("constraints", {})
        .get("min_bandwidth")
        == {"num": "100000", "den": "1"}
        and cli_payload.get("design", {})
        .get("fabrication_audit", {})
        .get("status")
        == "drc-pass",
        "the solve CLI emits a passing JSON design with the bandwidth constraint",
    )
    ranked = subprocess.run(
        command[:-1] + ["--ranking", "dynamic-aware", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    ranked_payload = {}
    ranked_ok = ranked.returncode == 0
    if ranked_ok:
        try:
            ranked_payload = json.loads(ranked.stdout)
        except json.JSONDecodeError:
            ranked_ok = False
    expect(
        ranked_ok
        and ranked_payload.get("design", {})
        .get("ranking", {})
        .get("profile")
        == "dynamic-aware"
        and ranked_payload.get("design", {})
        .get("selected", {})
        .get("option", {})
        .get("name")
        == "gain-1000000",
        f"the solve CLI propagates the ranking profile: {ranked.stderr[:160]}",
    )

    human = subprocess.run(
        [
            sys.executable,
            str(ROOT / "cent"),
            "solve",
            "sqrt-log",
            "--range",
            "1/2:1",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    expect(
        human.returncode == 0
        and "CONSTRAINED DESIGN" in human.stdout
        and "precision-20" in human.stdout
        and "Fabrication audit (advisory)" in human.stdout
        and "Reference netlist / floorplan" in human.stdout,
        f"the solve human renderer works: {human.stderr[:160]}",
    )

    physical = subprocess.run(
        [
            sys.executable,
            str(ROOT / "cent"),
            "physical",
            "sqrt-feedback",
            "--min-bandwidth",
            "100000",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    physical_payload = {}
    physical_ok = physical.returncode == 0
    if physical_ok:
        try:
            physical_payload = json.loads(physical.stdout)
        except json.JSONDecodeError:
            physical_ok = False
    expect(
        physical_ok
        and physical_payload.get("physical", {})
        .get("constraints", {})
        .get("min_bandwidth")
        == {"num": "100000", "den": "1"}
        and physical_payload.get("physical", {})
        .get("selected", {})
        .get("option")
        == "gain-1000000",
        f"cent physical propagates the bandwidth constraint: {physical.stderr[:160]}",
    )

    dynamic = subprocess.run(
        [
            sys.executable,
            str(ROOT / "cent"),
            "dynamics",
            "sqrt-feedback",
            "--min-bandwidth",
            "100000",
            "--samples",
            "8",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    dynamic_payload = {}
    dynamic_ok = dynamic.returncode == 0
    if dynamic_ok:
        try:
            dynamic_payload = json.loads(dynamic.stdout)
        except json.JSONDecodeError:
            dynamic_ok = False
    expect(
        dynamic_ok
        and (dynamic_payload.get("dynamics") or {}).get("selected_option")
        == "gain-1000000"
        and len((dynamic_payload.get("dynamics") or {}).get("trace", ())) == 8,
        f"cent dynamics propagates the bandwidth constraint: {dynamic.stderr[:160]}",
    )

    comparison = compare_routes()
    expect(
        comparison.routes
        == ("delta-sigma", "sqrt-log", "sqrt-feedback")
        and len(comparison.results) == 3,
        "the default comparison covers all three declared routes in order",
    )
    default_rows = comparison.rows()
    expect(
        comparison.solved_count == 3
        and all(row["status"] == "solved" for row in default_rows)
        and all(row["selected_option"] for row in default_rows),
        "every route has a selected declared design at its default input",
    )
    expect(
        comparison.profile == "exact-static"
        and all(row["profile"] == "exact-static" for row in default_rows)
        and all(row["pareto_rank"] == 1 for row in default_rows),
        "each compared route keeps its own exact-static Pareto rank",
    )
    comparison_doc = comparison.as_dict()
    expect(
        comparison_doc.get("schema") == COMPARISON_SCHEMA
        and comparison_doc.get("solved_count") == 3
        and len(comparison_doc.get("rows", ())) == 3
        and set(comparison_doc.get("results", {}))
        == {"delta-sigma", "sqrt-log", "sqrt-feedback"}
        and comparison_doc.get("markdown", "").startswith("# Method comparison")
        and "cross-route scalar" in comparison_doc.get("note", ""),
        "the comparison JSON carries rows, full results and a Markdown export",
    )
    shared = compare_routes(
        ("sqrt-log", "delta-sigma"),
        input_value=Fraction(1, 2),
        input_min=Fraction(1, 2),
        input_max=Fraction(1),
    )
    shared_rows = shared.rows()
    expect(
        shared.routes == ("sqrt-log", "delta-sigma")
        and all(
            row["constraints"]["input"] == {"num": "1", "den": "2"}
            and row["constraints"]["input_range"]
            == {"min": {"num": "1", "den": "2"}, "max": {"num": "1", "den": "1"}}
            for row in shared_rows
        ),
        "shared input and range constraints are applied to each selected route",
    )
    dynamic_comparison = compare_routes(min_bandwidth=Fraction(1000))
    expect(
        dynamic_comparison.profile == "dynamic-aware"
        and all(
            [item.name for item in result.ranking.objectives]
            == ["cost", "max_relative_error", "certified_bandwidth"]
            for result in dynamic_comparison.results
            if result.ranking is not None
        ),
        "a shared bandwidth target switches the comparison to dynamic-aware",
    )
    expect(
        raises_code(
            lambda: compare_routes(("sqrt-log", "unknown-route")),
            ErrorCode.UNSUPPORTED,
        )
        and raises_code(
            lambda: compare_routes(()),
            ErrorCode.INVALID_INPUT,
        ),
        "comparison rejects unknown and empty route selections",
    )

    compare_command = [
        sys.executable,
        str(ROOT / "cent"),
        "compare",
        "sqrt-log",
        "--json",
    ]
    compared = subprocess.run(
        compare_command, cwd=ROOT, capture_output=True, text=True, timeout=120
    )
    compare_payload = {}
    compare_ok = compared.returncode == 0
    if compare_ok:
        try:
            compare_payload = json.loads(compared.stdout)
        except json.JSONDecodeError:
            compare_ok = False
    expect(
        compare_ok
        and compare_payload.get("schema") == COMPARISON_SCHEMA
        and compare_payload.get("comparison", {}).get("routes") == ["sqrt-log"]
        and compare_payload.get("comparison", {}).get("rows", [{}])[0].get(
            "status"
        )
        == "solved",
        f"cent compare emits a JSON comparison: {compared.stderr[:160]}",
    )
    compared_md = subprocess.run(
        compare_command[:-1] + ["--markdown"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    expect(
        compared_md.returncode == 0
        and compared_md.stdout.startswith("# Method comparison")
        and "| Route | Status | Selected |" in compared_md.stdout
        and "## Note" in compared_md.stdout,
        f"cent compare emits a Markdown export: {compared_md.stderr[:160]}",
    )

    print()
    print("=" * 78)
    print(f"CONSTRAINED DESIGN: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
