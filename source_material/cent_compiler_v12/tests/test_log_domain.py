#!/usr/bin/env python3
"""D3 gate: recover exp, log, mult, div and reciprocal from the identity.

Run without pytest: ``python3 tests/test_log_domain.py``.

The gate exercises the source routes, independent target adapters, fixed
vectors and tolerance decisions.  A tolerance failure is a blocker, not a
reason to relabel the operation as supported.
"""
from __future__ import annotations

import pathlib
import sys
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler.assembly import (
    ArithmeticRoute,
    log_domain_arithmetic_route,
    log_domain_sqrt_route,
)
from cent_compiler.exact import CentError
from cent_compiler.mechanisms import (
    GENERATED_MECHANISM_CARDS,
    INTERPRETATIONS,
    MECHANISM_BY_ID,
    generate_mechanism_card,
)
from cent_compiler.targets import glm
from cent_compiler.transfer_engine import OPERATION_BY_ID, retrieve
from cent_compiler.transfer_evaluation import (
    NEGATIVE_CONTROLS,
    POSITIVE_CASES,
    UNADAPTED_CASES,
    evaluate_corpus,
)
from cent_compiler.transfer_validation import validate_transfer

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


def _rejects(callable_, code: str) -> bool:
    try:
        callable_()
    except CentError as exc:
        return exc.code.value == code
    return False


def main() -> int:
    print("=" * 78)
    print("D3 LOG-DOMAIN ARITHMETIC GATE")
    print("=" * 78)

    routes = {
        op: log_domain_arithmetic_route(op)
        for op in ("exp", "log", "mult", "div", "reciprocal")
    }
    expect(
        all(isinstance(route, ArithmeticRoute) for route in routes.values())
        and routes["exp"].program.instructions[0].op == "exp"
        and routes["log"].program.instructions[0].op == "log"
        and [item.op for item in routes["mult"].program.instructions]
        == ["log", "log", "sum", "exp"]
        and [item.op for item in routes["div"].program.instructions]
        == ["log", "log", "neg", "sum", "exp"]
        and [item.op for item in routes["reciprocal"].program.instructions]
        == ["log", "neg", "exp"],
        "exp/log are single junctions; mult/div/reciprocal follow the declared slide-rule programs",
    )
    expect(
        all(
            route.ports
            and route.components
            and route.gaps
            and route.as_dict()["kind"] == "certified-enclosure"
            for route in routes.values()
        ),
        "every arithmetic route declares typed ports, components and its remaining gaps",
    )

    runs = {
        "exp": routes["exp"].simulate(x=Fraction(1, 2)),
        "log": routes["log"].simulate(x=Fraction(2)),
        "mult": routes["mult"].simulate(a=Fraction(3, 4), b=Fraction(2, 3)),
        "div": routes["div"].simulate(a=Fraction(1, 2), b=Fraction(3, 4)),
        "reciprocal": routes["reciprocal"].simulate(x=Fraction(3, 4)),
    }
    expect(
        all(run.passed for run in runs.values())
        and all(
            max(run.result.lo, run.checker.lo) <= min(run.result.hi, run.checker.hi)
            for run in runs.values()
        ),
        "all five source routes pass their independent checker enclosure",
    )
    exact_checks = {
        "mult": runs["mult"].result.contains(Fraction(1, 2)),
        "div": runs["div"].result.contains(Fraction(2, 3)),
        "reciprocal": runs["reciprocal"].result.contains(Fraction(4, 3)),
    }
    expect(
        exact_checks["mult"] and exact_checks["div"] and exact_checks["reciprocal"],
        "mult contains 1/2, div contains 2/3 and reciprocal contains 4/3 exactly",
    )
    expect(
        _rejects(
            lambda: routes["log"].simulate(x=Fraction(0)),
            "domain_error",
        )
        and _rejects(
            lambda: routes["mult"].simulate(a=Fraction(-1), b=Fraction(2)),
            "domain_error",
        )
        and _rejects(
            lambda: routes["div"].simulate(a=Fraction(1), b=Fraction(0)),
            "domain_error",
        )
        and _rejects(
            lambda: routes["reciprocal"].simulate(x=Fraction(0)),
            "domain_error",
        ),
        "nonpositive log/mult/div/reciprocal inputs are rejected, not widened",
    )

    sqrt_route = log_domain_sqrt_route()

    # The sqrt delta stays sqrt-specific; D3 does not rewrite it.
    expect(
        [item.op for item in sqrt_route.program.instructions]
        == ["log", "scale", "exp"],
        "the sqrt delta remains log -> scale(1/2) -> exp",
    )

    widths = {op: run.result.width for op, run in runs.items()}
    expect(
        all(width <= Fraction(1, 10000) for width in widths.values())
        and all(width > 0 for width in widths.values()),
        "all five source enclosures stay strictly below the declared 1/10000 tolerance",
    )

    target_runs = {
        "exp": glm.log_domain_exp(Fraction(1, 2)),
        "log": glm.log_domain_log(Fraction(2)),
        "mult": glm.log_domain_mult(Fraction(3, 4), Fraction(2, 3)),
        "div": glm.log_domain_div(Fraction(1, 2), Fraction(3, 4)),
        "reciprocal": glm.log_domain_reciprocal(Fraction(3, 4)),
    }
    expect(
        all(run.passed for run in target_runs.values())
        and all(
            max(run.result.lo, run.checker.lo) <= min(run.result.hi, run.checker.hi)
            for run in target_runs.values()
        ),
        "all five target adapters pass their independent checker enclosure",
    )
    expect(
        all(
            glm.get_adapter(op, "log-domain-arithmetic").kind
            == "certified_enclosure"
            and glm.get_adapter(op, "log-domain-arithmetic").function
            is not None
            for op in target_runs
        ),
        "all five operations expose independent target adapters",
    )
    expect(
        all(
            len(glm.get_adapter(op, "log-domain-arithmetic").vectors) == 3
            for op in target_runs
        ),
        "each target adapter carries three fixed vectors",
    )

    # Every fixed vector is checked against the source route and exact checker.
    fixed_pass = True
    fixed_count = 0
    for op in ("exp", "log", "mult", "div", "reciprocal"):
        adapter = glm.get_adapter(op, "log-domain-arithmetic")
        for vector in adapter.vectors:
            fixed_count += 1
            source = routes[op].simulate(
                **(
                    {"x": vector.x}
                    if op in {"exp", "log", "reciprocal"}
                    else {"a": vector.a, "b": vector.b}
                )
            )
            target = adapter.function(
                **(
                    {"x": vector.x}
                    if op in {"exp", "log", "reciprocal"}
                    else {"a": vector.a, "b": vector.b}
                ),
                precision=vector.precision,
                tolerance=vector.tolerance,
            )
            fixed_pass = fixed_pass and (
                source.passed
                and target.passed
                and max(source.result.lo, target.result.lo)
                <= min(source.result.hi, target.result.hi)
                and target.result.width <= vector.tolerance
            )
    expect(
        fixed_pass and fixed_count == 15,
        "all fifteen fixed vectors pass source, target and overlap checks",
    )

    # Tolerance decisions are measurements, not labels.
    budgets_ok = True
    measured = {}
    for op, payload in (
        (op, validate_transfer(op, mechanism_id="log-domain-arithmetic"))
        for op in ("exp", "log", "mult", "div", "reciprocal")
    ):
        width = Fraction(
            int(payload["metrics"]["max_target_width"]["num"]),
            int(payload["metrics"]["max_target_width"]["den"]),
        )
        measured[op] = width
        budgets_ok = budgets_ok and (
            payload["certificate"]["status"] == "pass"
            and payload["ok"] is True
            and width <= Fraction(1, 10000)
            and payload["metrics"]["vectors"] == 3
            and payload["metrics"]["passed"] == 3
        )
    expect(
        budgets_ok,
        "all five target certificates pass the declared tolerance and three-vector budget",
    )
    expect(
        measured["log"] < measured["exp"]
        and measured["exp"] < Fraction(1, 10000),
        "the measured widths are ordered and every one is inside the declared budget",
    )

    arithmetic_card = MECHANISM_BY_ID["log-domain-arithmetic"]
    expect(
        arithmetic_card.principle_id == "transcendental-identity"
        and arithmetic_card.operators == ("composition",)
        and arithmetic_card.supported_operations == ("exp", "log", "mult", "div", "reciprocal")
        and arithmetic_card.primitive_chain == ("log", "sum", "neg", "exp"),
        "the generated card names the transcendental principle and slide-rule chain",
    )
    expect(
        arithmetic_card.id in {card.id for card in GENERATED_MECHANISM_CARDS}
        and arithmetic_card.id
        not in {card.id for card in INTERPRETATIONS if card.id == "log-domain-sqrt"},
        "the arithmetic card is generated, not a hand-authored sqrt card",
    )
    rebuilt = generate_mechanism_card(
        next(
            interpretation
            for interpretation in INTERPRETATIONS
            if interpretation.id == "log-domain-arithmetic"
        )
    )
    expect(
        rebuilt.as_dict() == arithmetic_card.as_dict(),
        "deleting and regenerating the arithmetic card reconstructs it exactly",
    )

    retrieval_ok = True
    for op in ("exp", "log", "mult", "div", "reciprocal"):
        _operation, _target, candidates, _matches = retrieve(op)
        retrieval_ok = retrieval_ok and any(
            candidate.mechanism == "log-domain-arithmetic"
            for candidate in candidates
        )
    expect(
        retrieval_ok,
        "each of the five operations retrieves the generated slide-rule candidate",
    )

    corpus = evaluate_corpus()
    positives = {case["operation"]: case for case in corpus["known_valid"]}
    negatives = {case["id"]: case for case in corpus["known_invalid"]}
    expect(
        set(positives) >= {"exp", "log", "mult", "div", "reciprocal"}
        and all(
            positives[op]["passed"]
            for op in ("exp", "log", "mult", "div", "reciprocal")
        )
        and all(
            "log-domain-arithmetic" in positives[op]["adapter_available"]
            for op in ("exp", "log", "mult", "div", "reciprocal")
        ),
        "the corpus labels all five recovered operations with passing adapters",
    )
    expect(
        negatives["exp-not-cam-profile"]["passed"]
        and negatives["log-not-cam-profile"]["passed"]
        and negatives["exp-not-cam-profile"]["forbidden_hits"] == []
        and negatives["log-not-cam-profile"]["forbidden_hits"] == []
        and "transcendental-identity" in negatives["exp-not-cam-profile"]["rationale"]
        and "transcendental-identity" in negatives["log-not-cam-profile"]["rationale"],
        "the corrected controls refuse the sqrt-specific delta and name the sibling delta",
    )
    expect(
        UNADAPTED_CASES == ()
        and all(
            case.operation not in {"exp", "log", "mult", "div", "reciprocal", "sign"}
            for case in UNADAPTED_CASES
        ),
        "the recovered operations and sign leave the unadapted corpus",
    )
    expect(
        len(POSITIVE_CASES) == 10
        and all(
            any(case.id == f"{op}-declared-mechanism" for case in POSITIVE_CASES)
            for op in ("exp", "log", "mult", "div", "reciprocal", "sign")
        ),
        "the corpus carries one authored positive case for each recovered operation and sign",
    )
    expect(
        all(
            case.operation in OPERATION_BY_ID
            for case in (*POSITIVE_CASES, *NEGATIVE_CONTROLS)
        ),
        "every D3 corpus case names a production operation contract",
    )

    profile = glm.GLM_REFERENCE_TARGET
    operations = set(profile.interface.get("operations") or ())
    interfaces = profile.interface.get("interfaces") or {}
    expect(
        {"exp", "log", "mult", "div", "reciprocal"} <= operations
        and all(
            op in interfaces
            for op in ("exp", "log", "mult", "div", "reciprocal")
        )
        and all(
            interfaces[op].get("law")
            for op in ("exp", "log", "mult", "div", "reciprocal")
        ),
        "the target profile declares all five arithmetic interfaces and laws",
    )
    expect(
        all(
            op in (profile.interface.get("latency") or {})
            and op in (profile.interface.get("bit_budget") or {})
            for op in ("exp", "log", "mult", "div", "reciprocal")
        ),
        "the target profile declares operation-local latency and bit budgets",
    )

    # JSON safety: no binary float in the arithmetic evidence.
    def no_floats(value) -> bool:
        if isinstance(value, float):
            return False
        if isinstance(value, dict):
            return all(no_floats(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return all(no_floats(item) for item in value)
        return True

    payloads = [
        validate_transfer(op, mechanism_id="log-domain-arithmetic")
        for op in ("exp", "log", "mult", "div", "reciprocal")
    ]
    expect(
        all(no_floats(payload) for payload in payloads)
        and all(payload["certificate"]["evidence_level"] == "target-simulated" for payload in payloads)
        and all(payload["validated_candidate"]["artifact"] for payload in payloads)
        and all(payload["validated_candidate"]["tests"] for payload in payloads),
        "the arithmetic certificates carry target-simulated evidence, tests and an artifact",
    )

    print("\n" + "=" * 78)
    for op in ("exp", "log", "mult", "div", "reciprocal"):
        print(
            f"  tolerance {op}: max width {float(measured[op]):.3e} "
            "<= 1/10000"
        )
    print(f"D3 LOG-DOMAIN ARITHMETIC: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
