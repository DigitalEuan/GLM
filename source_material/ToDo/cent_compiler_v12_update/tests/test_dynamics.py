#!/usr/bin/env python3
"""Focused tests for exact sampled-data dynamics.

Run without pytest: ``python3 tests/test_dynamics.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import dynamics  # noqa: E402
from cent_compiler.design import solve_route  # noqa: E402
from cent_compiler.exact import CentError, ErrorCode  # noqa: E402

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


def no_floats(value) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, dict):
        return all(no_floats(key) and no_floats(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(no_floats(item) for item in value)
    return True


def main() -> int:
    print("=" * 78)
    print("SAMPLED-DATA DYNAMICS")
    print("=" * 78)

    result = dynamics.simulate_route("delta-sigma")
    expect(
        result.route_key == "delta-sigma"
        and result.route_id == "delta-sigma-first-order"
        and result.samples == 64
        and result.nonlinear_transient is not None
        and result.nonlinear_transient["status"] == "pass"
        and result.nonlinear_transient["substeps"] == 4
        and result.nonlinear_transient["metrics"]["peak_volts"] > 0
        and len(result.nonlinear_transient["trace"]) == 64 * 4,
        "the default dynamic run names the route and sample count",
    )
    expect(
        result.status == "partial",
        "the dynamic run is partial because the static increment and RC gain differ",
    )
    alpha = result.metrics["settling_fraction"]
    expect(
        Fraction(63, 100) < alpha.lo < Fraction(64, 100)
        and alpha.width < Fraction(1, 10**20),
        "the one-tick step gain is a tight enclosure around 1 - exp(-1)",
    )
    expect(
        result.metrics["time_constant"] == Fraction(1, 10_000)
        and result.metrics["clock_period"] == Fraction(1, 10_000)
        and result.metrics["rc_clock_ratio"] == 1,
        "the declared RC and clock expose tau = T_clock",
    )
    expect(
        result.metrics["settling_deficit"].lo > Fraction(36, 100)
        and result.metrics["settling_deficit"].hi < Fraction(37, 100),
        "the dynamic deficit is about 36.8 percent per tick",
    )
    expect(
        result.metrics["mean"] == Fraction(31, 64)
        and result.metrics["mean_error"] == Fraction(-1, 64),
        "the sampled loop mean is 31/64 for x = 1/2",
    )
    expect(
        len(result.trace) == 64
        and result.trace[0].level == 0
        and result.trace[2].level == 1,
        "the trace holds the first comparator decisions and all 64 ticks",
    )
    expect(
        result.trace[0].state_before.lo == 0
        and result.trace[-1].state_after.lo > 0,
        "the trace retains exact integrator state endpoints",
    )
    expect(
        result.metrics["peak_volts"] < result.metrics["mean"] + 1,
        "the dynamic peak is bounded near the normalized integrator excursion",
    )
    expect(
        any(check.name == "one-tick settling gain" and check.status == "gap"
            for check in result.checks),
        "the finite one-tick gain is reported as a gap",
    )
    expect(
        any(check.name == "sampled loop tracking" and check.status == "pass"
            for check in result.checks),
        "the sampled loop still tracks its input within one LSB",
    )
    expect(
        any("static binding treats one clock" in gap for gap in result.gaps),
        "the static/dynamic mismatch is explained in the gaps",
    )

    half = dynamics.simulate_route("delta-sigma", samples=32)
    expect(
        half.samples == 32
        and len(half.trace) == 32
        and half.metrics["mean"] == Fraction(15, 32),
        "a shorter run keeps a deterministic transition count",
    )
    third = dynamics.simulate_route("delta-sigma", input_value=Fraction(1, 3))
    expect(
        third.metrics["mean"] == Fraction(21, 64)
        and third.metrics["mean_error"] == Fraction(-1, 192),
        "a one-third input produces the expected sampled mean",
    )
    full = dynamics.simulate_route("delta-sigma", input_value=Fraction(1))
    expect(
        full.metrics["mean"] == Fraction(63, 64)
        and full.metrics["mean_error"] == Fraction(-1, 64),
        "full scale exposes the one-sample boundary effect",
    )

    log = dynamics.simulate_route("sqrt-log")
    expect(
        log.status == "partial"
        and len(log.trace) == 64
        and "nonlinear large-signal" in log.model
        and "backward-Euler" in log.model
        and log.nonlinear_transient is not None
        and log.nonlinear_transient["status"] == "pass"
        and log.nonlinear_transient["samples"] == 64
        and log.nonlinear_transient["trace_source"] == "route trace",
        "the log route runs its nonlinear large-signal transient",
    )
    expect(
        log.metrics["tau_log"] < log.metrics["tau_out"]
        and log.metrics["tau_out"] == Fraction(1, 100_000)
        and log.metrics["integration_steps"] > 0
        and log.metrics["rejected_steps"] >= 1
        and log.metrics["min_step_seconds"] < log.metrics["max_step_seconds"]
        and log.metrics["max_local_error_ratio"] <= 1,
        "the log transient adapts its step inside the declared local budget",
    )
    expect(
        log.trace[0].time is not None
        and log.trace[0].output is not None
        and log.trace[0].target is not None
        and log.trace[0].aux is not None
        and log.trace[0].state_before is None,
        "the log trace carries time, output, target and the diode-node state",
    )
    expect(
        Fraction(0) < log.trace[0].output.midpoint < log.trace[0].target.midpoint
        and log.trace[-1].output.midpoint > Fraction(999, 1000)
        and Fraction(1, 3) < log.trace[-1].aux.midpoint < Fraction(2, 5),
        "the log output charges from zero while the diode node stays at its log bias",
    )
    expect(
        any(
            check.name == "adaptive step control" and check.status == "pass"
            for check in log.checks
        )
        and any(
            "Global error envelope" in gap and "certified backward-Euler" in gap
            for gap in log.gaps
        )
        and log.metrics["final_relative_error"] <= Fraction(1, 1000),
        "the log transient settles within 0.1 percent with a certified local-truncation bound",
    )
    log_bounded = log.certificates["bounded_state"]
    log_global = log.certificates["global_error"]
    expect(
        log_bounded["status"] == "pass"
        and log_bounded["trace_contained"]
        and log_bounded["box"]["v_log_hi"] >= log.trace[-1].aux.hi
        and log_bounded["box"]["v_out_hi"] >= log.trace[-1].output.hi
        and log_global["status"] == "gap"
        and log_global["certified"] is True
        and log_global["method"] == "certified local truncation + triangular contraction"
        and log_global["local_truncation_sum"] > 0
        and log_global["within_target"] is False
        and log.certificates["stability"]["status"] == "pass",
        "the log route certifies local truncation and stability while the target is still exceeded",
    )
    log_design = solve_route("sqrt-log")
    too_small_log = dynamics._log_bounded_state_certificate(
        log_design.selected.binding,
        log.trace,
        box={"v_log_hi": Fraction(1, 10), "v_out_hi": Fraction(1, 10)},
    )
    expect(
        too_small_log["status"] == "gap"
        and not too_small_log["trace_contained"]
        and "caller-supplied box" in too_small_log["detail"],
        "a too-small log certificate box fails explicitly instead of being widened",
    )
    public_log = dynamics.simulate_route(
        "sqrt-log",
        samples=8,
        certificate_box={
            "v_log_hi": Fraction(1, 10),
            "v_out_hi": Fraction(1, 10),
        },
    )
    expect(
        public_log.status == "gap"
        and public_log.certificates["bounded_state"]["source"]
        == "caller-supplied box"
        and not public_log.certificates["bounded_state"]["trace_contained"],
        "the public log route exposes a too-small certificate box as a gap",
    )

    feedback = dynamics.simulate_route("sqrt-feedback")
    expect(
        feedback.status == "partial"
        and len(feedback.trace) == 64
        and "nonlinear large-signal" in feedback.model
        and "quadratic closed-loop" in feedback.model
        and "backward-Euler" in feedback.model
        and feedback.nonlinear_transient is not None
        and feedback.nonlinear_transient["status"] == "pass"
        and feedback.nonlinear_transient["samples"] == 64
        and feedback.nonlinear_transient["trace_source"] == "route trace",
        "the feedback route runs its nonlinear quadratic transient",
    )
    expect(
        feedback.metrics["tau_cl"] == Fraction(1, 10_000_000)
        and feedback.metrics["tau_out"] == Fraction(1, 100_000_000)
        and feedback.metrics["integration_steps"] > 0
        and feedback.metrics["rejected_steps"] >= 1
        and feedback.metrics["min_step_seconds"]
        < feedback.metrics["max_step_seconds"]
        and feedback.metrics["max_local_error_ratio"] <= 1,
        "the feedback route exposes its declared poles and adaptive budget",
    )
    expect(
        feedback.trace[0].output is not None
        and feedback.trace[0].target is not None
        and feedback.trace[0].aux is None
        and feedback.trace[0].state_before is None,
        "the feedback trace carries its output and target without an auxiliary node",
    )
    expect(
        Fraction(0) < feedback.trace[0].output.midpoint < feedback.trace[0].target.midpoint
        and feedback.trace[-1].output.midpoint > Fraction(141, 100)
        and abs(
            feedback.trace[-1].target.midpoint
            - feedback.trace[-1].output.midpoint
        ) <= feedback.trace[-1].target.midpoint / 1000,
        "the quadratic loop rises to its finite-gain target",
    )
    expect(
        any(
            check.name == "adaptive step control" and check.status == "pass"
            for check in feedback.checks
        )
        and any(
            "Global error envelope" in gap and "certified backward-Euler" in gap
            for gap in feedback.gaps
        )
        and feedback.metrics["final_relative_error"] <= Fraction(1, 1000),
        "the feedback transient keeps its certified bound and target gap explicit",
    )
    feedback_bounded = feedback.certificates["bounded_state"]
    feedback_global = feedback.certificates["global_error"]
    expect(
        feedback_bounded["status"] == "pass"
        and feedback_bounded["trace_contained"]
        and feedback_bounded["box"]["v_hi"] >= feedback.trace[-1].output.hi
        and feedback_global["status"] == "gap"
        and feedback_global["certified"] is True
        and feedback_global["method"]
        == "certified local truncation + negative scalar derivative"
        and feedback_global["local_truncation_sum"] > 0
        and feedback_global["within_target"] is False
        and feedback.certificates["stability"]["status"] == "pass"
        and feedback.certificates["stability"]["derivative_negative"] is True,
        "the feedback route certifies local truncation and scalar stability while the target is exceeded",
    )
    feedback_design = solve_route("sqrt-feedback")
    too_small_feedback = dynamics._feedback_bounded_state_certificate(
        feedback_design.selected.binding,
        feedback.trace,
        box={"v_hi": Fraction(1, 2)},
    )
    expect(
        too_small_feedback["status"] == "gap"
        and not too_small_feedback["trace_contained"]
        and "caller-supplied box" in too_small_feedback["detail"],
        "a too-small feedback certificate box fails explicitly instead of being widened",
    )
    public_feedback = dynamics.simulate_route(
        "sqrt-feedback",
        samples=8,
        certificate_box={"v_hi": Fraction(1, 2)},
    )
    expect(
        public_feedback.status == "gap"
        and public_feedback.certificates["bounded_state"]["source"]
        == "caller-supplied box"
        and not public_feedback.certificates["bounded_state"]["trace_contained"],
        "the public feedback route exposes a too-small certificate box as a gap",
    )

    expect(
        raises_code(lambda: dynamics.simulate_route("delta-sigma", samples=0),
                    ErrorCode.DOMAIN_ERROR),
        "zero samples are rejected",
    )
    expect(
        raises_code(lambda: dynamics.simulate_route("delta-sigma", samples=257),
                    ErrorCode.DOMAIN_ERROR),
        "the sample budget is bounded",
    )
    expect(
        raises_code(
            lambda: dynamics.analyze_design(
                solve_route("sqrt-feedback", max_cost=Fraction(1))
            ),
            ErrorCode.DOMAIN_ERROR,
        ),
        "no dynamic model is invented for a no-solution design",
    )

    payload = result.as_dict()
    expect(
        payload["schema"] == "cent-dynamics/1"
        and payload["status"] == "partial"
        and len(payload["trace"]) == 64,
        "the dynamic payload carries the schema, status and full trace",
    )
    expect(no_floats(payload), "the dynamic payload contains no binary floats")
    expect(
        json.loads(json.dumps(payload))["checks"][1]["status"] == "gap",
        "the JSON payload preserves the dynamic gap check",
    )

    cli = subprocess.run(
        [sys.executable, "cent", "dynamics", "delta-sigma", "--samples", "16", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == "cent-dynamics/1"
        and cli_payload["dynamics"]["samples"] == 16
        and cli_payload["dynamics"]["status"] == "partial",
        "cent dynamics --json emits the sampled-data payload",
    )
    cli_box = subprocess.run(
        [
            sys.executable,
            "cent",
            "dynamics",
            "sqrt-log",
            "--samples",
            "8",
            "--certificate-box",
            json.dumps({"v_log_hi": "1/10", "v_out_hi": "1/10"}),
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    cli_box_payload = (
        json.loads(cli_box.stdout) if cli_box.returncode == 0 else {}
    )
    expect(
        cli_box.returncode == 0
        and cli_box_payload.get("dynamics", {}).get("status") == "gap"
        and cli_box_payload.get("dynamics", {})
        .get("certificates", {})
        .get("bounded_state", {})
        .get("source")
        == "caller-supplied box",
        "cent dynamics --certificate-box exposes the explicit failure result",
    )
    human = subprocess.run(
        [sys.executable, "cent", "dynamics", "sqrt-log"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expect(
        human.returncode == 0
        and "DYNAMIC CHECK" in human.stdout
        and "nonlinear large-signal" in human.stdout
        and "adaptive step control" in human.stdout
        and "Certificates" in human.stdout
        and "step-doubling" in human.stdout
        and "fixed-step integration" not in human.stdout
        and "two-pole" not in human.stdout,
        "the human renderer shows the log route's adaptive model and gap",
    )
    missing = subprocess.run(
        [sys.executable, "cent", "dynamics", "delta-sigma", "--samples", "0"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expect(
        missing.returncode == 2 and "samples must be" in missing.stdout,
        "the CLI rejects an invalid sample count",
    )

    total = PASS + FAIL
    print()
    print("=" * 78)
    print(f"SAMPLED-DATA DYNAMICS: {PASS}/{total} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
