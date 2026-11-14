#!/usr/bin/env python3
"""Focused tests for declared device bindings.

Run without pytest: ``python3 tests/test_binding.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler.device import (  # noqa: E402
    BOLTZMANN,
    ELEMENTARY_CHARGE,
    bind_delta_sigma,
    bind_feedback_sqrt,
    bind_kcl_sum,
    bind_log_domain_sqrt,
)
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


def raises_domain(callable_) -> bool:
    try:
        callable_()
    except CentError as exc:
        return exc.code == ErrorCode.DOMAIN_ERROR
    return False


def by_symbol(binding, symbol):
    return next(item for item in binding.quantities if item.symbol == symbol)


def main() -> int:
    print("=" * 78)
    print("DEVICE BINDINGS")
    print("=" * 78)

    delta = bind_delta_sigma()
    expect(
        delta.route_id == "delta-sigma-first-order"
        and delta.kind == "declared-reference-design",
        "the delta-sigma binding names its route and status",
    )
    expect(delta.passed, "the default delta-sigma reference design passes")
    expect(
        by_symbol(delta, "RC_f").value == 1,
        "R_in * C_int * f_clock is exactly one",
    )
    expect(
        by_symbol(delta, "V_lsb").value == 1
        and by_symbol(delta, "V_threshold").value == Fraction(1, 2),
        "the one-bit quantizer maps to 1 V with a 0.5 V threshold",
    )
    peak = by_symbol(delta, "V_int_peak").value
    expect(
        peak > 0 and peak <= by_symbol(delta, "V_int_limit").value,
        f"the exact run peak maps to {peak} V inside the declared 8 V range",
    )
    expect(
        delta.total_error == Fraction(521, 100000),
        f"the delta-sigma static budget is exactly 521/100000: {delta.total_error}",
    )
    expect(
        delta.total_error <= delta.error_limit
        and all(check.passed for check in delta.checks),
        "every delta-sigma check and the total budget pass",
    )
    expect(
        any(check.name == "half-LSB margin" for check in delta.checks),
        "the delta-sigma budget includes a half-LSB margin check",
    )
    delta_audit = delta.parameter_audit
    expect(
        delta_audit["status"] == "pass"
        and delta_audit["checked"] >= 6
        and not delta_audit["failures"],
        "the delta-sigma derived quantities pass an independent exact audit",
    )

    try:
        json.dumps(delta.as_dict(), ensure_ascii=False)
        delta_json = True
    except TypeError:
        delta_json = False
    expect(delta_json, "the delta-sigma binding is JSON-serialisable")

    sin = bind_log_domain_sqrt()
    expect(
        sin.route_id == "sqrt-log-domain"
        and sin.kind == "declared-reference-design",
        "the sqrt binding names its route and status",
    )
    expect(sin.passed, "the default log-domain reference design passes")
    v_ref = by_symbol(sin, "V_ref").value
    r_in = by_symbol(sin, "R_in").value
    i_ref = by_symbol(sin, "I_ref").value
    expect(i_ref == v_ref / r_in, "the reference current is exactly V_ref / R_in")
    v_t = by_symbol(sin, "V_T").value
    expect(
        v_t == BOLTZMANN * 300 / ELEMENTARY_CHARGE,
        "the thermal voltage uses exact SI constants at 300 K",
    )
    v_out_ref = by_symbol(sin, "V_out_ref").value
    r_out = by_symbol(sin, "R_out").value
    i_s = by_symbol(sin, "I_s").value
    expect(
        v_out_ref * v_out_ref == r_out * r_out * i_s * i_ref,
        "the squared full-scale relation is exact",
    )
    expect(
        by_symbol(sin, "V_out").value.width <= 100 * v_out_ref / 1_000_000,
        "the independently evaluated output enclosure is narrow",
    )
    expect(
        sin.total_error <= sin.error_limit,
        "the sqrt static budget is inside its limit",
    )
    expect(
        any(term.name == "junction saturation mismatch" for term in sin.errors),
        "the sqrt budget includes saturation-current mismatch",
    )
    expect(
        any(term.name == "gain / temperature / ideality mismatch" for term in sin.errors),
        "the sqrt budget includes gain and thermal mismatch",
    )
    expect(
        by_symbol(sin, "C_j").value == Fraction(1, 10**11)
        and by_symbol(sin, "C_out").value == Fraction(1, 10**11),
        "the log binding declares junction and output capacitances",
    )
    expect(
        by_symbol(sin, "tau_log").value < by_symbol(sin, "tau_out").value,
        "the log binding declares a dominant 10 us output pole",
    )
    expect(
        sin.parameter_audit["status"] == "pass"
        and sin.parameter_audit["checked"] >= 7,
        "the log-domain derived quantities pass an independent exact audit",
    )

    try:
        json.dumps(sin.as_dict(), ensure_ascii=False)
        sqrt_json = True
    except TypeError:
        sqrt_json = False
    expect(sqrt_json, "the sqrt binding is JSON-serialisable")

    feedback = bind_feedback_sqrt()
    expect(
        feedback.route_id == "sqrt-opamp-multiplier"
        and feedback.kind == "declared-reference-design",
        "the feedback binding names its route and status",
    )
    expect(feedback.passed, "the default feedback reference design passes")
    v_in_fb = by_symbol(feedback, "V_in").value
    v_ref_fb = by_symbol(feedback, "V_ref").value
    v_out_fb = by_symbol(feedback, "V_out").value
    v_target_fb = by_symbol(feedback, "V_target").value
    a_fb = by_symbol(feedback, "A").value
    k_fb = by_symbol(feedback, "k").value
    expect(
        v_in_fb == 2 * v_ref_fb,
        "the feedback binding maps x=2 to the declared input voltage",
    )
    expect(
        v_out_fb.width <= v_ref_fb / 1_000_000,
        "the feedback output enclosure is narrow in volts",
    )
    feedback_mid = k_fb * v_out_fb.midpoint * v_out_fb.midpoint / v_ref_fb
    drive_mid = a_fb * (v_in_fb - feedback_mid)
    expect(
        abs(drive_mid - v_out_fb.midpoint) <= v_ref_fb / 1_000_000,
        "the independently evaluated multiplier and amplifier close the loop",
    )
    expect(
        abs(v_out_fb.midpoint - v_target_fb.midpoint)
        <= v_ref_fb / 1_000_000,
        "the finite-gain output stays within the ideal-target tolerance",
    )
    expect(
        feedback.total_error <= feedback.error_limit
        and any(term.name == "finite amplifier gain" for term in feedback.errors),
        "the feedback budget includes the finite-gain bias and passes",
    )
    expect(
        any(term.name == "multiplier feedback offset" for term in feedback.errors),
        "the feedback budget includes multiplier offset",
    )
    expect(
        by_symbol(feedback, "tau_cl").value == Fraction(1, 10_000_000)
        and by_symbol(feedback, "tau_out").value == Fraction(1, 100_000_000),
        "the feedback binding declares 100 ns and 10 ns dynamic poles",
    )
    expect(
        by_symbol(feedback, "C_out").value == Fraction(1, 10**11)
        and by_symbol(feedback, "R_out").value == 1_000,
        "the feedback binding declares its output load pole",
    )
    expect(
        feedback.parameter_audit["status"] == "pass"
        and feedback.parameter_audit["checked"] >= 3,
        "the feedback derived quantities pass an independent exact audit",
    )
    bad_tau = replace(
        next(item for item in feedback.quantities if item.symbol == "tau_out"),
        value=Fraction(1),
    )
    broken = replace(
        feedback,
        quantities=tuple(
            bad_tau if item.symbol == "tau_out" else item
            for item in feedback.quantities
        ),
    )
    expect(
        broken.parameter_audit["status"] == "gap"
        and "tau_out" in broken.parameter_audit["failures"],
        "a tampered derived quantity is caught by the independent audit",
    )

    try:
        json.dumps(feedback.as_dict(), ensure_ascii=False)
        feedback_json = True
    except TypeError:
        feedback_json = False
    expect(feedback_json, "the feedback binding is JSON-serialisable")

    sum_binding = bind_kcl_sum()
    expect(
        sum_binding.route_id == "sum-kcl"
        and sum_binding.kind == "declared-normalized-reference"
        and sum_binding.passed
        and by_symbol(sum_binding, "total").value == Fraction(5, 6)
        and sum_binding.input_value_b == Fraction(1, 3),
        "the KCL binding preserves both exact inputs and the 5/6 result",
    )
    expect(
        sum_binding.parameter_audit["status"] == "pass"
        and sum_binding.parameter_audit["checked"] >= 1,
        "the KCL derived result passes its independent exact audit",
    )
    difference_binding = bind_kcl_sum(operation="difference")
    expect(
        difference_binding.passed
        and by_symbol(difference_binding, "total").value == Fraction(1, 6)
        and "No physical voltage/current mapping" in difference_binding.gaps[0],
        "the KCL difference binding exposes its exact result and physical gap",
    )

    sum_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "bind", "sum-kcl",
         "--input", "1/2", "--input-b", "1/3", "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    sum_cli_payload = {}
    sum_cli_ok = sum_cli.returncode == 0
    if sum_cli_ok:
        try:
            sum_cli_payload = json.loads(sum_cli.stdout)
        except json.JSONDecodeError:
            sum_cli_ok = False
    expect(
        sum_cli_ok
        and sum_cli_payload.get("schema") == "cent-device/1"
        and sum_cli_payload.get("binding", {}).get("input_b").get("num") == "1",
        f"cent bind sum-kcl emits both exact inputs: {sum_cli.stderr[:160]}",
    )

    expect(
        raises_domain(lambda: bind_feedback_sqrt(input_value=Fraction(5))),
        "an out-of-range feedback device input is rejected",
    )
    expect(
        raises_domain(lambda: bind_feedback_sqrt(amplifier_gain=0)),
        "a nonpositive feedback amplifier gain is rejected",
    )
    expect(
        bind_feedback_sqrt(
            input_value=Fraction(2), multiplier_gain=Fraction(2)
        ).passed,
        "the feedback binding can declare a non-unit multiplier gain",
    )

    expect(
        raises_domain(lambda: bind_delta_sigma(input_value=Fraction(3, 2))),
        "an out-of-range delta-sigma device input is rejected",
    )
    expect(
        raises_domain(lambda: bind_log_domain_sqrt(input_value=Fraction(0))),
        "a nonpositive sqrt device input is rejected",
    )
    expect(
        raises_domain(lambda: bind_log_domain_sqrt(precision=0)),
        "an invalid sqrt precision is rejected",
    )

    command = [
        sys.executable, str(ROOT / "cent"), "bind", "delta-sigma",
        "--json",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    payload = {}
    cli_ok = result.returncode == 0
    if cli_ok:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            cli_ok = False
    expect(cli_ok, f"cent bind delta-sigma succeeds: {result.stderr[:160]}")
    expect(
        payload.get("schema") == "cent-device/1"
        and payload.get("binding", {}).get("passed") is True,
        "the delta-sigma bind CLI emits a passing payload",
    )

    sqrt_command = [
        sys.executable, str(ROOT / "cent"), "bind", "sqrt-log",
        "--input", "1/2", "--json",
    ]
    sqrt_result = subprocess.run(
        sqrt_command, cwd=ROOT, capture_output=True, text=True, timeout=60
    )
    sqrt_payload = {}
    sqrt_cli_ok = sqrt_result.returncode == 0
    if sqrt_cli_ok:
        try:
            sqrt_payload = json.loads(sqrt_result.stdout)
        except json.JSONDecodeError:
            sqrt_cli_ok = False
    expect(sqrt_cli_ok, f"cent bind sqrt-log succeeds: {sqrt_result.stderr[:160]}")
    expect(
        sqrt_payload.get("schema") == "cent-device/1"
        and sqrt_payload.get("binding", {}).get("passed") is True,
        "the sqrt-log bind CLI emits a passing payload",
    )

    feedback_command = [
        sys.executable, str(ROOT / "cent"), "bind", "sqrt-feedback",
        "--input", "2", "--json",
    ]
    feedback_result = subprocess.run(
        feedback_command, cwd=ROOT, capture_output=True, text=True, timeout=60
    )
    feedback_payload = {}
    feedback_cli_ok = feedback_result.returncode == 0
    if feedback_cli_ok:
        try:
            feedback_payload = json.loads(feedback_result.stdout)
        except json.JSONDecodeError:
            feedback_cli_ok = False
    expect(
        feedback_cli_ok,
        f"cent bind sqrt-feedback succeeds: {feedback_result.stderr[:160]}",
    )
    expect(
        feedback_payload.get("schema") == "cent-device/1"
        and feedback_payload.get("binding", {}).get("passed") is True,
        "the feedback bind CLI emits a passing payload",
    )

    human = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "bind", "sqrt-log"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        human.returncode == 0
        and "PHYSICAL DEVICE BINDING" in human.stdout
        and "declared reference design" in human.stdout
        and "passed" in human.stdout,
        f"the bind human renderer works: {human.stderr[:160]}",
    )
    feedback_human = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "bind", "sqrt-feedback"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        feedback_human.returncode == 0
        and "Op-amp + analog-multiplier" in feedback_human.stdout
        and "passed" in feedback_human.stdout,
        f"the feedback bind human renderer works: {feedback_human.stderr[:160]}",
    )

    print()
    print("=" * 78)
    print(f"DEVICE BINDINGS: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
