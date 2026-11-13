#!/usr/bin/env python3
"""Focused tests for typed component contracts and exact route assembly.

Run without pytest: ``python3 tests/test_assembly.py``.
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

from cent_compiler.assembly import (  # noqa: E402
    AMP_CONTRACT,
    COMPONENT_CONTRACT_SCHEMA,
    COMPONENT_CONTRACTS,
    EXP_CONTRACT,
    LOG_CONTRACT,
    MULT_CONTRACT,
    QUANTIZE_CONTRACT,
    SCALE_CONTRACT,
    audit_route_topology,
    component_contract,
    delta_sigma_route,
    fluid_sum_route,
    kcl_sum_route,
    log_domain_sqrt_route,
    opamp_multiplier_sqrt_route,
)
from cent_compiler.exact import CentError, ErrorCode  # noqa: E402
from cent_compiler.program import analyse  # noqa: E402
from cent_compiler.typed_graph import SCHEMA as TYPED_GRAPH_SCHEMA, typed_graph  # noqa: E402
from cent_compiler.ui import build_report  # noqa: E402

PASS = 0
FAIL = 0

# Operations with an exact assembled route.  Everything else in the fixture
# matrix has an exact program and/or a structural template, but no exact route.
ASSEMBLED_OPERATIONS = {"sum", "neg", "sqrt"}

# label, formula, DAG operation, structural template, exact program, first gap.
OPERATION_FIXTURES = (
    (
        "multiplication",
        "y = x * z",
        "mult",
        "multiplier",
        True,
        "no exact assembled route; structural template only",
    ),
    (
        "division",
        "y = x / z",
        "div",
        "divider",
        True,
        "no exact assembled route; structural template only",
    ),
    (
        "exponential",
        "y = exp(x)",
        "exp",
        "diode_exp",
        True,
        "no exact assembled route; structural template only",
    ),
    (
        "logarithm",
        "y = log(x)",
        "log",
        "log_amp",
        True,
        "no exact assembled route; structural template only",
    ),
    (
        "square root",
        "y = sqrt(5)",
        "sqrt",
        "opamp_sqrt",
        True,
        "no fabrication or measured-device evidence",
    ),
    (
        "tanh saturation",
        "y = tanh(x)",
        "sat",
        "clipper",
        False,
        "missing required sat parameters lo and hi",
    ),
)


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


def main() -> int:
    print("=" * 78)
    print("TYPED ROUTE ASSEMBLY")
    print("=" * 78)

    expect(
        set(COMPONENT_CONTRACTS)
        == {"accum", "quantize", "delay", "scale", "mult", "amp", "log", "exp", "sum", "neg"},
        "the assembly layer declares carry and compute contracts",
    )
    expect(
        "gain * a * b" in MULT_CONTRACT.law
        and "op-amp" in AMP_CONTRACT.material
        and AMP_CONTRACT.parameters[0].name == "gain",
        "the feedback route has typed multiplier and amplifier contracts",
    )
    expect(
        component_contract("quantize") is QUANTIZE_CONTRACT,
        "the quantizer contract is addressable by primitive",
    )
    expect(
        {port.name for port in QUANTIZE_CONTRACT.ports} == {"signal", "level"},
        "the quantizer has typed signal and level ports",
    )
    expect(
        {parameter.name for parameter in QUANTIZE_CONTRACT.parameters}
        == {"quantum", "full_scale"},
        "the quantizer declares quantum and full-scale parameters",
    )
    expect(
        "clamp" in QUANTIZE_CONTRACT.law and "ties away" in QUANTIZE_CONTRACT.law,
        "the quantizer law includes saturation and tie handling",
    )
    expect(
        "flash ADC" in QUANTIZE_CONTRACT.material
        and "comparator offset" in QUANTIZE_CONTRACT.failure_modes,
        "the quantizer names its material and failure modes",
    )

    route = delta_sigma_route()
    topology = audit_route_topology(route)
    expect(
        topology["status"] == "pass"
        and topology["checked"] >= 5
        and not topology["failures"],
        "the delta-sigma route passes its structural topology audit",
    )
    analysis = analyse(route.program)
    expect(analysis.has_feedback, "the route program has a state-founded feedback edge")
    expect(
        {component.op for component in route.components}
        == {"accum", "quantize", "delay"},
        "the route instances expose its typed physical components",
    )
    expect(
        {instruction.op for instruction in route.program.instructions}
        == {"neg", "sum", "accum", "quantize", "sat", "delay"},
        "the exact program includes arithmetic glue, quantization and saturation",
    )
    expect(
        route.parameters["levels"] == 2,
        "the default quantizer has two declared levels",
    )

    run = route.simulate(Fraction(1, 2), samples=12)
    expect(run.passed, "the default route passes its exact loop check")
    expect(run.mean == Fraction(1, 2), "a half-scale input has an exact mean of 1/2")
    expect(
        run.bitstream == (1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0),
        f"the bitstream is the expected repeating pattern: {run.bitstream}",
    )
    expect(
        len(run.trace) == 12 and all(item["level"] in (0, 1) for item in run.trace),
        "every trace sample is a bounded 0/1 level",
    )
    expect(
        run.peak_integrator <= route.integrator_limit,
        "the integrator stays within its declared bound",
    )

    third = route.simulate(Fraction(1, 3), samples=12)
    expect(
        third.mean == Fraction(1, 3) and third.passed,
        "a one-third input is carried exactly by its repeating code",
    )

    expect(
        raises_domain(lambda: route.simulate(Fraction(3, 2), samples=4)),
        "an out-of-range input is rejected, not clipped silently",
    )
    expect(
        raises_domain(lambda: delta_sigma_route(quantum=0)),
        "a nonpositive quantum is rejected",
    )
    expect(
        raises_domain(lambda: delta_sigma_route(quantum=Fraction(2, 3), full_scale=1)),
        "a non-integral number of levels is rejected",
    )

    sqrt_route = log_domain_sqrt_route()
    expect(
        {component.op for component in sqrt_route.components}
        == {"log", "scale", "exp"},
        "the square-root route instances its log, gain and antilog components",
    )
    expect(
        audit_route_topology(sqrt_route)["status"] == "pass",
        "the log-domain route passes its structural topology audit",
    )
    expect(
        {instruction.op for instruction in sqrt_route.program.instructions}
        == {"log", "scale", "exp"},
        "the square-root route has no hidden sqrt instruction",
    )
    sqrt_run = sqrt_route.simulate(Fraction(2))
    expect(sqrt_run.passed, "the log-domain square-root route passes its bracket check")
    expect(
        sqrt_run.overlap is not None and sqrt_run.root.width <= sqrt_route.tolerance,
        "the route root overlaps the independent sqrt bracket within tolerance",
    )
    expect(
        sqrt_run.checker.width <= sqrt_route.tolerance,
        "the independent sqrt bracket is at least as tight as the declared tolerance",
    )
    expect(
        sqrt_route.simulate(Fraction(4)).overlap is not None,
        "a perfect-square input still yields a consistent certified enclosure",
    )
    expect(
        raises_domain(lambda: sqrt_route.simulate(Fraction(0))),
        "a nonpositive log-domain input is rejected",
    )
    expect(
        LOG_CONTRACT.ports[1].kind == "interval"
        and EXP_CONTRACT.ports[0].kind == "interval"
        and SCALE_CONTRACT.parameters[0].name == "factor",
        "the compute contracts expose interval ports and an explicit gain",
    )
    try:
        json.dumps(sqrt_route.as_dict(), ensure_ascii=False)
        sqrt_json = True
    except TypeError:
        sqrt_json = False
    expect(sqrt_json, "the sqrt route plan is JSON-serialisable")

    feedback_route = opamp_multiplier_sqrt_route()
    expect(
        {component.op for component in feedback_route.components} == {"mult", "amp"},
        "the feedback route instances a multiplier and a high-gain amplifier",
    )
    expect(
        audit_route_topology(feedback_route)["status"] == "pass",
        "the algebraic feedback route passes its structural topology audit",
    )
    broken_route = replace(
        route,
        components=(
            replace(route.components[0], role="quantizer"),
        )
        + route.components[1:],
    )
    broken_topology = audit_route_topology(broken_route)
    expect(
        broken_topology["status"] == "gap"
        and "unique component roles" in broken_topology["failures"],
        "a duplicate component role is rejected by the topology audit",
    )
    feedback_plan = feedback_route.as_dict()
    expect(
        feedback_plan["program"] is None
        and feedback_plan["solver"]["ops"] == ["mult", "amp", "sum"]
        and "sqrt" not in feedback_plan["solver"]["ops"],
        "the feedback route has no exact-core program and no sqrt instruction",
    )
    delta_graph = typed_graph(route).as_dict()
    expect(
        delta_graph["schema"] == TYPED_GRAPH_SCHEMA
        and [node["op"] for node in delta_graph["nodes"]]
        == ["neg", "sum", "accum", "quantize", "sat", "delay"]
        and delta_graph["summary"]["loop"] == "stateful",
        "the delta-sigma route expands into ordered typed ¢ nodes with a stateful loop",
    )
    expect(
        delta_graph["summary"]["component_nodes"] == 3
        and delta_graph["summary"]["exact_core_nodes"] == 3
        and any(edge["feedback"] for edge in delta_graph["edges"]),
        "delta-sigma lowers three component nodes, three glue nodes and marks its feedback edge",
    )
    log_graph = typed_graph(sqrt_route).as_dict()
    expect(
        [node["op"] for node in log_graph["nodes"]] == ["log", "scale", "exp"]
        and log_graph["summary"]["component_nodes"] == 3
        and not log_graph["feedback_edges"],
        "the log-domain route lowers directly to its three component contracts",
    )
    feedback_graph = typed_graph(feedback_route).as_dict()
    expect(
        [node["op"] for node in feedback_graph["nodes"]]
        == ["neg", "sum", "amp", "mult"]
        and feedback_graph["summary"]["loop"] == "algebraic"
        and feedback_graph["summary"]["component_nodes"] == 2
        and feedback_graph["summary"]["exact_core_nodes"] == 2
        and bool(feedback_graph["feedback_edges"]),
        "the feedback route exposes its algebraic loop, two component nodes and two glue nodes",
    )

    sum_route = kcl_sum_route()
    sum_run = sum_route.simulate(Fraction(1, 2), Fraction(1, 3))
    expect(
        audit_route_topology(sum_route)["status"] == "pass"
        and sum_run.passed
        and sum_run.result == Fraction(5, 6),
        "the KCL sum route passes its audit and computes 1/2 + 1/3 exactly",
    )
    difference_route = kcl_sum_route(operation="difference")
    difference_run = difference_route.simulate(Fraction(1, 2), Fraction(1, 3))
    expect(
        difference_run.passed
        and difference_run.result == Fraction(1, 6)
        and [instruction.op for instruction in difference_route.program.instructions]
        == ["neg", "sum"],
        "the KCL difference route uses exact negation and returns 1/6",
    )
    sum_graph = typed_graph(sum_route).as_dict()
    difference_graph = typed_graph(difference_route).as_dict()
    expect(
        sum_graph["summary"]["component_nodes"] == 1
        and difference_graph["summary"]["exact_core_nodes"] == 1,
        "the KCL detail exposes one declared junction and its exact negation glue",
    )

    fluid_route = fluid_sum_route()
    fluid_run = fluid_route.simulate(Fraction(1, 2), Fraction(1, 3))
    fluid_graph = typed_graph(fluid_route).as_dict()
    fluid_component = fluid_route.components[0]
    expect(
        audit_route_topology(fluid_route)["status"] == "pass"
        and fluid_run.passed
        and fluid_run.result == Fraction(5, 6)
        and fluid_component.contract.domain == "fluidic"
        and fluid_component.contract.source
        == "DELTA_SUBSTRATE: sum / fluid pipe junction"
        and "flow-conservation" in fluid_component.contract.law,
        "the fluid pipe-junction route passes its audit and computes 1/2 + 1/3 exactly",
    )
    expect(
        fluid_graph["summary"]["component_nodes"] == 1
        and [node["op"] for node in fluid_graph["nodes"]] == ["sum"]
        and not fluid_graph["feedback_edges"],
        "the fluid sum expands to one stateless continuity component",
    )

    graphs = (delta_graph, log_graph, feedback_graph)
    all_nodes = [node for graph in graphs for node in graph["nodes"]]
    try:
        json.dumps(graphs, ensure_ascii=False)
        graphs_json = True
    except TypeError:
        graphs_json = False
    expect(
        all(node["lowering"]["port_map"] for node in all_nodes)
        and all(
            node["lowering"]["contract"]["schema"] == COMPONENT_CONTRACT_SCHEMA
            for node in all_nodes
            if node["lowering"]["kind"] == "component"
        )
        and all(
            node["lowering"]["kind"] == "exact-core"
            for node in all_nodes
            if node["lowering"]["component_key"] is None
        )
        and graphs_json,
        "every graph node has an explicit port map and component or exact-core lowering",
    )

    graph_command = [
        sys.executable, str(ROOT / "cent"), "graph", "sqrt-log", "--json",
    ]
    graph_result = subprocess.run(
        graph_command, cwd=ROOT, capture_output=True, text=True, timeout=60
    )
    graph_payload = {}
    graph_cli_ok = graph_result.returncode == 0
    if graph_cli_ok:
        try:
            graph_payload = json.loads(graph_result.stdout)
        except json.JSONDecodeError:
            graph_cli_ok = False
    expect(
        graph_cli_ok
        and graph_payload.get("schema") == TYPED_GRAPH_SCHEMA
        and graph_payload.get("graph", {}).get("route") == "sqrt-log-domain"
        and graph_payload.get("graph", {}).get("summary", {}).get("component_nodes") == 3,
        f"cent graph emits the typed route graph: {graph_result.stderr[:160]}",
    )

    feedback_run = feedback_route.simulate(Fraction(2))
    expect(
        feedback_run.passed and feedback_run.overlap is not None,
        "the finite-gain feedback solve passes its independent quadratic check",
    )
    expect(
        feedback_run.root.width <= feedback_route.tolerance
        and feedback_run.gain_error <= feedback_route.tolerance,
        "the feedback bracket and finite-gain bias stay inside tolerance",
    )
    expect(
        feedback_run.root.hi < feedback_run.ideal.lo,
        "finite amplifier gain leaves the root just below the ideal square root",
    )
    scaled_feedback = opamp_multiplier_sqrt_route(
        multiplier_gain=2
    ).simulate(Fraction(2))
    expect(
        scaled_feedback.passed and scaled_feedback.ideal.midpoint == 1,
        "a non-unit multiplier gain targets sqrt(x/k)",
    )
    expect(
        raises_domain(lambda: feedback_route.simulate(Fraction(0))),
        "a nonpositive feedback-route input is rejected",
    )
    try:
        json.dumps(feedback_plan, ensure_ascii=False)
        feedback_json = True
    except TypeError:
        feedback_json = False
    expect(feedback_json, "the feedback route plan is JSON-serialisable")

    wide = delta_sigma_route(full_scale=2, quantum=1)
    expect(wide.parameters["levels"] == 3, "a wider quantizer declares three levels")
    expect(
        wide.simulate(Fraction(1, 2), samples=12).bitstream == (),
        "a multi-level route does not expose its levels as a bitstream",
    )

    try:
        json.dumps(route.as_dict(), ensure_ascii=False)
        route_json = True
    except TypeError:
        route_json = False
    expect(route_json, "the route plan is JSON-serialisable")

    command = [
        sys.executable, str(ROOT / "cent"), "assemble", "delta-sigma",
        "--input", "1/2", "--samples", "12", "--json",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    payload = {}
    cli_ok = result.returncode == 0
    if cli_ok:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            cli_ok = False
    expect(cli_ok, f"cent assemble succeeds: {result.stderr[:160]}")
    expect(
        payload.get("schema") == "cent-route/1"
        and payload.get("simulation", {}).get("passed") is True,
        "the assemble CLI emits the exact route and simulation payload",
    )

    sqrt_command = [
        sys.executable, str(ROOT / "cent"), "assemble", "sqrt-log",
        "--input", "2", "--precision", "20", "--json",
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
    expect(sqrt_cli_ok, f"cent assemble sqrt-log succeeds: {sqrt_result.stderr[:160]}")
    expect(
        sqrt_payload.get("route", {}).get("kind") == "certified-enclosure"
        and sqrt_payload.get("simulation", {}).get("passed") is True,
        "the sqrt-log CLI emits the certified enclosure payload",
    )

    human_delta = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "assemble", "delta-sigma",
         "--input", "1/2", "--samples", "4"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        human_delta.returncode == 0
        and "First-order delta-sigma loop" in human_delta.stdout
        and "passed: True" in human_delta.stdout,
        f"the delta-sigma human renderer works: {human_delta.stderr[:160]}",
    )
    human_sqrt = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "assemble", "sqrt-log",
         "--input", "2", "--precision", "20"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        human_sqrt.returncode == 0
        and "Log-domain square-root extractor" in human_sqrt.stdout
        and "passed: True" in human_sqrt.stdout,
        f"the sqrt-log human renderer works: {human_sqrt.stderr[:160]}",
    )

    sum_command = [
        sys.executable, str(ROOT / "cent"), "assemble", "sum-kcl",
        "--input", "1/2", "--input-b", "1/3", "--json",
    ]
    sum_result = subprocess.run(
        sum_command, cwd=ROOT, capture_output=True, text=True, timeout=60
    )
    sum_payload = {}
    sum_cli_ok = sum_result.returncode == 0
    if sum_cli_ok:
        try:
            sum_payload = json.loads(sum_result.stdout)
        except json.JSONDecodeError:
            sum_cli_ok = False
    expect(
        sum_cli_ok
        and sum_payload.get("route", {}).get("kind") == "exact-sum"
        and sum_payload.get("simulation", {}).get("result")
        == {"num": "5", "den": "6"}
        and sum_payload.get("route", {}).get("topology_audit", {}).get("status") == "pass",
        f"the sum-kcl CLI emits the exact route payload: {sum_result.stderr[:160]}",
    )

    fluid_result = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "assemble", "sum-fluid",
            "--input", "1/2", "--input-b", "1/3", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    fluid_payload = {}
    fluid_cli_ok = fluid_result.returncode == 0
    if fluid_cli_ok:
        try:
            fluid_payload = json.loads(fluid_result.stdout)
        except json.JSONDecodeError:
            fluid_cli_ok = False
    expect(
        fluid_cli_ok
        and fluid_payload.get("route", {}).get("id") == "sum-fluid"
        and fluid_payload.get("route", {}).get("kind") == "exact-fluid-sum"
        and fluid_payload.get("simulation", {}).get("result")
        == {"num": "5", "den": "6"}
        and fluid_payload.get("route", {}).get("topology_audit", {}).get("status") == "pass",
        f"the sum-fluid CLI emits the exact route payload: {fluid_result.stderr[:160]}",
    )

    fluid_difference_result = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "assemble", "sum-fluid",
            "--operation", "difference", "--input", "1/2", "--input-b",
            "1/3", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    fluid_difference_payload = {}
    fluid_difference_cli_ok = fluid_difference_result.returncode == 0
    if fluid_difference_cli_ok:
        try:
            fluid_difference_payload = json.loads(fluid_difference_result.stdout)
        except json.JSONDecodeError:
            fluid_difference_cli_ok = False
    expect(
        fluid_difference_cli_ok
        and fluid_difference_payload.get("route", {}).get("id") == "sum-fluid"
        and fluid_difference_payload.get("route", {}).get("parameters", {}).get(
            "operation"
        ) == "difference"
        and [
            instruction.get("op")
            for instruction in fluid_difference_payload.get("route", {}).get(
                "program", {}
            ).get("instructions", [])
        ] == ["neg", "sum"]
        and fluid_difference_payload.get("simulation", {}).get("result")
        == {"num": "1", "den": "6"}
        and fluid_difference_payload.get("route", {}).get(
            "topology_audit", {}
        ).get("status") == "pass",
        f"the sum-fluid CLI emits the reversed-port difference route: {fluid_difference_result.stderr[:160]}",
    )

    opamp_difference_result = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "assemble", "sum-opamp",
            "--operation", "difference", "--input", "1/2", "--input-b",
            "1/3", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    opamp_difference_payload = {}
    opamp_difference_ok = opamp_difference_result.returncode == 0
    if opamp_difference_ok:
        try:
            opamp_difference_payload = json.loads(
                opamp_difference_result.stdout
            )
        except json.JSONDecodeError:
            opamp_difference_ok = False
    expect(
        opamp_difference_ok
        and opamp_difference_payload.get("route", {}).get("id") == "sum-opamp"
        and opamp_difference_payload.get("route", {}).get("parameters", {}).get(
            "operation"
        ) == "difference"
        and [
            instruction.get("op")
            for instruction in opamp_difference_payload.get("route", {}).get(
                "program", {}
            ).get("instructions", [])
        ] == ["neg", "sum"]
        and opamp_difference_payload.get("route", {}).get(
            "typed_graph", {}
        ).get("summary", {}).get("component_nodes") == 2
        and opamp_difference_payload.get("simulation", {}).get("result")
        == {"num": "1", "den": "6"}
        and opamp_difference_payload.get("route", {}).get(
            "topology_audit", {}
        ).get("status") == "pass",
        f"the sum-opamp CLI emits the inverting-buffer difference route: {opamp_difference_result.stderr[:160]}",
    )

    feedback_command = [
        sys.executable, str(ROOT / "cent"), "assemble", "sqrt-feedback",
        "--input", "2", "--precision", "64", "--iterations", "64", "--json",
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
        feedback_cli_ok
        and feedback_payload.get("route", {}).get("kind")
        == "certified-algebraic-feedback"
        and feedback_payload.get("simulation", {}).get("passed") is True,
        f"the sqrt-feedback CLI emits the algebraic-feedback payload: {feedback_result.stderr[:160]}",
    )
    human_feedback = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "assemble", "sqrt-feedback",
         "--input", "2", "--precision", "64"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        human_feedback.returncode == 0
        and "Op-amp + analog-multiplier square-root route" in human_feedback.stdout
        and "passed: True" in human_feedback.stdout,
        f"the sqrt-feedback human renderer works: {human_feedback.stderr[:160]}",
    )

    for label, formula, operation, template, has_program, expected_gap in OPERATION_FIXTURES:
        report = build_report(formula)
        observed_ops = {op.op for op in report.ops}
        if has_program:
            program_ok = report.program is not None and not report.notes
        else:
            program_ok = (
                report.program is None
                and any("missing required parameter" in note for note in report.notes)
            )
        if report.program is None:
            observed_gap = "missing required sat parameters lo and hi"
        elif operation not in ASSEMBLED_OPERATIONS:
            observed_gap = "no exact assembled route; structural template only"
        else:
            observed_gap = "no fabrication or measured-device evidence"
        expect(
            observed_ops == {operation}
            and report.template == template
            and report.template_status == "match"
            and program_ok
            and observed_gap == expected_gap,
            f"{label}: op={operation}, template={template}, first gap={observed_gap}",
        )

    print()
    print("=" * 78)
    print(f"TYPED ROUTE ASSEMBLY: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
