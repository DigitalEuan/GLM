#!/usr/bin/env python3
"""Focused tests for the problem-to-method discovery pipeline.

Run without pytest: ``python3 tests/test_discovery.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from dataclasses import replace

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import axiom_graph, concepts, discovery, envelope, hypotheses, pipeline, vocabulary, wheel_mapping, wheels  # noqa: E402
from cent_compiler.grammar import CGraph, COp  # noqa: E402
from cent_compiler.material_contracts import SCHEMA as MATERIAL_CONTRACT_SCHEMA  # noqa: E402
from cent_compiler.pattern_matcher import DELTA_SUBSTRATE  # noqa: E402
from cent_compiler.substrate_library import EXPANSIONS, enumerate_delta  # noqa: E402
from cent_compiler.wheels_extended import prefix_case_equation  # noqa: E402

PASS = 0
FAIL = 0
QUERY = "how to compute an irrational number with an analog method"
MULTI_QUERY = "compute a square root, then carry the result as a bitstream"


def expect(condition: bool, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def main() -> int:
    print("=" * 78)
    print("METHOD DISCOVERY")
    print("=" * 78)

    problem = discovery.parse_problem(QUERY)
    expect(problem.matched, "the example problem is recognised")
    expect(problem.behavior == "compute", "compute is distinguished from carry")
    expect(problem.object == "irrational", "the object is an irrational value")
    expect(
        "compute:irrational" in problem.goals and "carry:irrational" in problem.goals,
        "compute and carry are both exposed for comparison",
    )
    expect(
        "analog/physical" in problem.constraints,
        "the analog constraint is parsed",
    )

    expect(
        set(discovery.CAPABILITIES) == set(vocabulary.ALL_PRIMITIVES)
        and all(
            discovery.CAPABILITIES[op] and discovery.CAPABILITY_BASIS.get(op)
            for op in vocabulary.ALL_PRIMITIVES
        ),
        "every exact contract has a reviewed capability record and basis",
    )
    canonical_names = [
        op for op in vocabulary.ALL_PRIMITIVES
        if not discovery.parse_problem(op).matched
    ]
    expect(
        not canonical_names,
        f"every canonical contract name is recognised: {canonical_names}",
    )
    summed = discovery.parse_problem("compute a sum")
    expect(
        summed.matched and summed.object == "sum",
        "a canonical primitive name is recognised without a special alias",
    )
    summed_result = discovery.discover("compute a sum", limit=10)
    summed_method = next(
        (method for method in summed_result["methods"]
         if method["primitive"] == "sum"),
        {},
    )
    expect(
        summed_method.get("capability_basis") == discovery.CAPABILITY_BASIS["sum"]
        and {method["primitive"] for method in summed_result["methods"]} == {"sum"},
        "an explicit primitive is scoped to its contract and carries the reviewed basis",
    )

    operation_queries = (
        ("how do I multiply two signals", "mult"),
        ("compute a ratio", "div"),
        ("exponentiate a signal", "exp"),
        ("take the logarithm of a signal", "log"),
        ("compute a reciprocal", "recip"),
        ("sum two signals", "sum"),
    )
    operation_results = []
    operation_ok = True
    for query_text, expected_op in operation_queries:
        parsed = discovery.parse_problem(query_text)
        found = discovery.discover(query_text, limit=20)
        primitives = {method["primitive"] for method in found.get("methods", [])}
        operation_ok = operation_ok and (
            parsed.matched
            and parsed.object == expected_op
            and primitives == {expected_op}
        )
        if expected_op in {"exp", "log", "mult", "div", "recip"}:
            transfer_methods = [
                method for method in found.get("methods", ())
                if method.get("route") == "transfer"
            ]
            operation_ok = operation_ok and bool(transfer_methods) and all(
                method.get("route_simulation", {}).get("passed") is True
                and (method.get("route_model") or {}).get("mechanism")
                == "log-domain-arithmetic"
                and (method.get("route_model") or {}).get("target")
                == "glm-reference"
                for method in transfer_methods
            )
        operation_results.append((query_text, expected_op, parsed.object, primitives))
    expect(
        operation_ok,
        f"operation-level queries resolve to their own contracts: {operation_results}",
    )
    operation_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "discover",
            "exponentiate a signal", "--json", "--limit", "8",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    operation_payload = {}
    if operation_cli.returncode == 0:
        try:
            operation_payload = json.loads(operation_cli.stdout)
        except json.JSONDecodeError:
            operation_payload = {}
    expect(
        operation_cli.returncode == 0
        and operation_payload.get("schema") == "cent-discovery/1"
        and operation_payload.get("problem", {}).get("object") == "exp"
        and {method["primitive"] for method in operation_payload.get("methods", [])}
        == {"exp"},
        "CLI discover supports an operation-level query",
    )

    substrate_rows = [(row, row.contract) for row in DELTA_SUBSTRATE]
    expansion_rows = [(row, row.contract) for row in EXPANSIONS]
    expect(
        len(substrate_rows) == len(DELTA_SUBSTRATE) > 0
        and all(
            contract.kind == "substrate"
            and contract.primitive == row.primitive
            and contract.component == row.component
            and contract.law == row.law
            and contract.domain == row.domain
            and contract.carrier == row.carrier_type
            for row, contract in substrate_rows
        ),
        "every declared substrate row resolves through a typed material contract",
    )
    expect(
        len(expansion_rows) == len(EXPANSIONS) > 0
        and all(
            contract.kind == "expansion"
            and contract.primitive == row.primitive
            and contract.component == row.substrate_component
            and contract.description == row.description
            and contract.law == row.description
            and contract.carrier == row.carrier_type
            for row, contract in expansion_rows
        ),
        "every declared expansion row resolves through a typed material contract",
    )
    all_contracts = [contract for _, contract in substrate_rows + expansion_rows]
    expect(
        len({contract.key for contract in all_contracts}) == len(all_contracts)
        and all(
            contract.ports
            and contract.operating_range
            and contract.failure_modes
            and contract.law
            and contract.description
            and contract.as_dict().get("schema") == MATERIAL_CONTRACT_SCHEMA
            for contract in all_contracts
        ),
        "typed material contracts have unique keys, ports, ranges, laws and failures",
    )
    sum_materials = [
        method.get("material_contract")
        for method in summed_result["methods"]
        if method.get("material_contract")
    ]
    expect(
        any(
            item.get("schema") == MATERIAL_CONTRACT_SCHEMA
            and item.get("primitive") == "sum"
            and "Kirchhoff" in item.get("law", "")
            and {port.get("name") for port in item.get("ports", ())}
            == {"a", "b", "sum"}
            for item in sum_materials
        ),
        "discovery carries the typed material contract for a substrate row",
    )

    multi = discovery.parse_problem(MULTI_QUERY)
    expect(multi.matched, "an ordered multi-step goal is recognised")
    expect(
        multi.multi_step and len(multi.steps) == 2,
        "the sequence is parsed into two ordered goal steps",
    )
    expect(
        [step.behavior for step in multi.steps] == ["compute", "carry"]
        and "compute:root" in multi.steps[0].goals
        and "carry:irrational" in multi.steps[1].goals,
        "each step keeps its own behaviour and goals",
    )
    expect(
        multi.steps[1].object == "delta_sigma_modulator"
        and "digital" in multi.constraints,
        "the bitstream carry step is typed as a digital delta-sigma goal",
    )
    malformed = discovery.parse_problem("compute a square root then zzzz")
    expect(
        not malformed.matched and len(malformed.steps) == 2,
        "an unrecognised step prevents a whole-pipeline match",
    )

    data = discovery.discover(QUERY)
    expect(data["schema"] == "cent-discovery/1", "stable discovery schema")
    expect(data["matched"] is True, "discovery returns a matched result")
    expect(len(data["methods"]) >= 8, "multiple methods are returned")
    expect(
        [stage["stage"] for stage in data["pipeline"]][:5]
        == ["interpret", "seed", "expand", "ground", "rank"],
        "the discovery pipeline records the successful middle stages",
    )
    expect(
        next(stage for stage in data["pipeline"] if stage["stage"] == "netlist")["status"]
        == "gap",
        "the missing physical emission stage is reported",
    )
    expect(
        {group["role"] for group in data["groups"]} == {"compute", "carry"},
        "results are grouped into compute and carry roles",
    )

    methods = data["methods"]
    expect(
        all(
            method.get("contract_status") in vocabulary.STATUS_ORDER
            and method.get("contract_status_label")
            == concepts.STATUS_LABEL.get(method["contract_status"])
            for method in methods
        ),
        "candidate methods carry capability status and its display label",
    )
    by_primitive: dict[str, list[dict]] = {}
    for method in methods:
        by_primitive.setdefault(method["primitive"], []).append(method)

    expect("sqrt" in by_primitive, "square-root methods are present")
    sqrt_domains = {method["domain_class"] for method in by_primitive.get("sqrt", [])}
    expect(
        {"electrical", "mechanical", "fluidic", "mixed-signal"} <= sqrt_domains,
        f"sqrt spans declared domains: {sorted(sqrt_domains)}",
    )
    sqrt_names = " ".join(method["name"].lower() for method in by_primitive["sqrt"])
    for label in ("analog feedback", "mechanical cam", "fluidic orifice", "digital delta sigma"):
        expect(label in sqrt_names, f"sqrt route present: {label}")

    expect("delta_sigma_modulator" in by_primitive, "delta-sigma is a discoverable carry method")
    ds = by_primitive["delta_sigma_modulator"][0]
    expect(ds["role"] == "carry", "delta-sigma is labelled as carry, not compute")
    expect(ds["simulation"] is True, "delta-sigma carries simulation evidence")
    expect(
        not any("quantize" in gap for gap in ds["gaps"]),
        "the declared quantizer substrate closes the ingredient-material gap",
    )
    expect(
        "3/3 ingredients" in ds["coverage"],
        "delta-sigma ingredient coverage is stated honestly",
    )
    expect(
        all(item["physical"] > 0 for item in ds["ingredient_status"]),
        "every ingredient has at least one declared physical material row",
    )
    expect(
        any("full physical netlist" in gap for gap in ds["gaps"]),
        "closing material coverage does not claim a full loop netlist",
    )
    quantizer = enumerate_delta(
        CGraph(ops=[COp("quantize", ("x",), "y")], inputs={"x"}, outputs={"y"})
    )
    expect(
        quantizer and quantizer[0].substrate_domain == "electrical",
        "quantize is registered with the ∆ enumerator as an electrical route",
    )
    expect(
        (ds.get("route_model") or {}).get("schema") == "cent-route/1",
        "delta-sigma carries a typed exact route model",
    )
    expect(
        (ds.get("route_simulation") or {}).get("passed") is True,
        "the typed delta-sigma route passes an exact simulation",
    )
    simulate_stage = next(stage for stage in data["pipeline"] if stage["stage"] == "simulate")
    expect(
        simulate_stage["status"] == "pass",
        "the discovery pipeline reports the exact route simulation",
    )
    routed_sqrt = [
        method for method in by_primitive.get("sqrt", [])
        if method.get("route_simulation") is not None
    ]
    sqrt_kinds = {
        (method.get("route_model") or {}).get("kind") for method in routed_sqrt
    }
    expect(
        len(routed_sqrt) == 2
        and all(method["route_simulation"].get("passed") for method in routed_sqrt)
        and sqrt_kinds == {"certified-enclosure", "certified-algebraic-feedback"},
        "both square-root compute routes carry passing exact models",
    )
    log_routed = next(
        method for method in routed_sqrt
        if (method.get("route_model") or {}).get("kind") == "certified-enclosure"
    )
    expect(
        (log_routed.get("device_binding") or {}).get("passed") is True,
        "the log-domain sqrt candidate carries its declared device binding",
    )
    feedback_routed = next(
        method for method in routed_sqrt
        if (method.get("route_model") or {}).get("kind") == "certified-algebraic-feedback"
    )
    expect(
        feedback_routed["route_simulation"].get("passed") is True
        and feedback_routed["route_model"]["solver"]["ops"] == ["mult", "amp", "sum"],
        "the op-amp sqrt candidate exposes its exact feedback solver",
    )
    expect(
        (feedback_routed.get("device_binding") or {}).get("passed") is True,
        "the op-amp sqrt candidate carries its declared feedback binding",
    )
    expect(
        {(method.get("design") or {}).get("route") for method in routed_sqrt}
        == {"sqrt-log", "sqrt-feedback"},
        "both square-root routes expose their declared solver spaces",
    )
    expect(
        "3/3" in simulate_stage["detail"],
        "the pipeline counts all three exact typed routes",
    )
    bind_stage = next(stage for stage in data["pipeline"] if stage["stage"] == "bind")
    expect(
        bind_stage["status"] == "pass" and "3/3" in bind_stage["detail"],
        "the pipeline reports all three declared device bindings",
    )
    expect(
        (ds.get("device_binding") or {}).get("passed") is True,
        "delta-sigma carries a passing declared device binding",
    )
    expect(
        (ds.get("design") or {}).get("route") == "delta-sigma"
        and len(ds["design"].get("options", ())) == 4,
        "delta-sigma exposes its declared solver space",
    )
    expand_stage = next(stage for stage in data["pipeline"] if stage["stage"] == "expand")
    expect(
        expand_stage["status"] == "pass",
        "a typed route is not mislabelled as an expansion gap",
    )
    netlist_stage = next(stage for stage in data["pipeline"] if stage["stage"] == "netlist")
    expect(
        "no fabrication netlist" in netlist_stage["detail"],
        "the netlist gap distinguishes an exact route from fabrication output",
    )
    expect(
        ds["application_available"] is True
        and not any("DELTA_SIGMA_DEMO.md" in gap for gap in ds["gaps"]),
        "the declared delta-sigma demo evidence is present",
    )

    expect("translinear" in by_primitive, "translinear power-law method is present")
    expect("eq" in by_primitive, "equilibrium methods are present")
    expect(
        any(method["wheel_material"] for method in methods),
        "at least one method has wheel material candidates",
    )
    expect(
        all(
            item["scope"] in {"primitive text", "component/material text"}
            for method in methods for item in method["wheel_material"]
        ),
        "wheel matches are labelled as candidate grounding",
    )

    graph_grounding = axiom_graph.ground_primitive("sqrt")
    empty_grounding = axiom_graph.ground_primitive("log")
    expect(
        graph_grounding["schema"] == axiom_graph.GROUNDING_SCHEMA
        and graph_grounding["status"] == "derived"
        and {item["wheel"] for item in graph_grounding["candidates"]}
        == {"W21", "W25", "W29"}
        and all(
            item["basis"] == "graph-proof"
            and item["status"] == "derived"
            and item["proof_steps"]
            for item in graph_grounding["candidates"]
        )
        and empty_grounding["status"] == "gap"
        and not empty_grounding["candidates"]
        and "text matches are not promoted" in empty_grounding["gaps"][0],
        "graph grounding proves monomial relations and never falls back to text",
    )

    log_method = next(
        method for method in methods
        if (method.get("route_model") or {}).get("kind") == "certified-enclosure"
    )
    bridge = next(
        (item for item in log_method["wheel_mappings"] if item["status"] == "declared"),
        {},
    )
    expect(
        bridge.get("wheel") == "W24"
        and bridge.get("bridge_id") == "log-domain-diode-w24",
        "the log-domain route has a declared W24 bridge",
    )
    expect(
        bool(bridge.get("bridge_law"))
        and {port["method_port"] for port in bridge.get("ports", ())} == {"x", "root"}
        and all(port["status"] == "pass" for port in bridge.get("ports", ())),
        "the bridge maps typed route ports through device quantities",
    )
    expect(
        bridge.get("residual_empty") is True
        and not bridge.get("residual")
        and any(
            item.get("wheel_quantity") == "thermal_voltage"
            for item in bridge.get("quantities", ())
        ),
        "the declared bridge has a zero dimensional residual and a thermal-voltage quantity",
    )
    log_grounding = log_method["wheel_grounding"]
    expect(
        log_grounding["status"] == "grounded"
        and set(log_grounding["basis"]) == {"graph-proof", "declared-bridge"}
        and {item["wheel"] for item in log_grounding["candidates"]}
        == {"W21", "W25", "W29"}
        and {item["wheel"] for item in log_grounding["declared_bridges"]}
        == {"W24"}
        and not log_grounding["text_only"],
        "discovery exposes graph proofs and the declared W24 bridge separately",
    )

    opamp_method = next(
        method for method in methods
        if (method.get("route_model") or {}).get("kind")
        == "certified-algebraic-feedback"
    )
    opamp_w24 = next(
        item for item in opamp_method["wheel_mappings"] if item["wheel"] == "W24"
    )
    expect(
        opamp_w24["status"] == "gap" and opamp_w24.get("bridge_id") is None,
        "a text match without a declared bridge remains an explicit gap",
    )
    expect(
        "W24" in {item["wheel"] for item in opamp_method["wheel_grounding"]["text_only"]}
        and "declared-bridge" not in opamp_method["wheel_grounding"]["basis"],
        "unbridged text matches stay outside declared grounding",
    )

    spec = wheel_mapping.WHEEL_BRIDGES[0]
    bad_port = replace(spec.ports[0], expected_dimension=wheel_mapping.VOLTAGE)
    bad_spec = replace(spec, ports=(bad_port,) + spec.ports[1:])
    bad_mapping = wheel_mapping.evaluate_bridge(
        log_method, bad_spec, discovery._wheel_docs()["W24"]
    )
    expect(
        bad_mapping["status"] == "gap" and bool(bad_mapping["residual"]),
        "a declared dimensional mismatch fails the bridge",
    )
    expect(
        all(
            item["residual_empty"]
            for method in methods
            for item in method["wheel_mappings"]
            if item["status"] == "declared"
        ),
        "every declared wheel bridge has an empty dimensional residual",
    )

    global_graph = axiom_graph.build_axiom_graph()
    graph_counts = global_graph["counts"]
    graph_nodes = {node["id"]: node for node in global_graph["nodes"]}
    graph_edges = global_graph["edges"]
    axiom_nodes = {node["id"] for node in global_graph["nodes"] if node["kind"] == "axiom"}
    quantity_nodes = {
        node["id"] for node in global_graph["nodes"] if node["kind"] == "quantity"
    }
    expect(
        global_graph["schema"] == axiom_graph.SCHEMA
        and graph_counts["wheels"] == 40
        and graph_counts["axioms"] == 101
        and graph_counts["contains"] == 101
        and graph_counts["mentions"] == 316,
        "the global axiom graph flattens all 40 wheels and 101 axioms",
    )
    expect(
        len(axiom_nodes) == 101
        and all(
            any(
                edge["kind"] == "contains" and edge["target"] == axiom_id
                for edge in graph_edges
            )
            for axiom_id in axiom_nodes
        )
        and all(
            any(
                edge["kind"] == "mentions" and edge["source"] == axiom_id
                for edge in graph_edges
            )
            for axiom_id in axiom_nodes
        )
        and all(
            edge["target"] in quantity_nodes
            for edge in graph_edges
            if edge["kind"] == "mentions"
        ),
        "every flattened axiom has a containing wheel and resolved quantity mentions",
    )
    expect(
        graph_counts["quantities"] == 239
        and graph_counts["typed_as"] == 239
        and graph_counts["dimensions"] == 65
        and all(
            graph_nodes[edge["source"]]["data"].get("dimension") == edge["target"]
            for edge in graph_edges
            if edge["kind"] == "typed_as"
        ),
        "all 239 declared quantities resolve to 65 exact dimension nodes",
    )
    junction_gaps = [
        gap for gap in global_graph["gaps"] if gap["kind"] == "junction-endpoint"
    ]
    non_identity_gaps = [
        gap for gap in global_graph["gaps"] if gap["kind"] == "non-identity-endpoint"
    ]
    expect(
        graph_counts["junction_edges"] == 56
        and graph_counts["junction_declared"] == 59
        and len(junction_gaps) == 3
        and graph_counts["non_identity_edges"] == 5
        and graph_counts["non_identity_declared"] == 10
        and len(non_identity_gaps) == 5
        and all(
            edge["source"] in graph_nodes and edge["target"] in graph_nodes
            for edge in graph_edges
            if edge["kind"] in {"junction", "non_identity"}
        ),
        "declared identities become edges only when both endpoints exist",
    )
    identity_pair = {"quantity:W1:power", "quantity:W5:power"}
    expect(
        identity_pair <= quantity_nodes
        and not any(
            edge["kind"] == "junction"
            and {edge["source"], edge["target"]} == identity_pair
            for edge in graph_edges
        )
        and "wheel-local" in global_graph["identity_policy"]
        and graph_counts["shared_names"] == 36,
        "shared wheel names stay distinct without a declared junction",
    )
    serialised_graph = json.dumps(global_graph, ensure_ascii=False)
    rendered_graph = axiom_graph.render_text(global_graph)
    graph_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "axioms", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    cli_graph = {}
    if graph_cli.returncode == 0:
        try:
            cli_graph = json.loads(graph_cli.stdout)
        except json.JSONDecodeError:
            cli_graph = {}
    expect(
        bool(serialised_graph)
        and "GLOBAL AXIOM GRAPH" in rendered_graph
        and graph_cli.returncode == 0
        and cli_graph.get("schema") == axiom_graph.SCHEMA
        and (cli_graph.get("graph") or {}).get("counts") == graph_counts,
        "the global graph is JSON-serialisable and emitted by the CLI",
    )

    three_input = axiom_graph.derive_from(
        "W8.energy",
        ["W8.mass", "W8.specific_heat_capacity", "W8.temperature"],
    )
    expect(
        three_input["status"] == "derived"
        and three_input["formula"]
        == "W8.mass * W8.specific_heat_capacity * W8.temperature"
        and three_input["support"] == 1
        and [item["id"] for item in three_input["used_axioms"]] == ["axiom:W8:00"]
        and [item["exponent"] for item in three_input["input_exponents"]]
        == ["1/1", "1/1", "1/1"]
        and three_input["unused_inputs"] == [],
        "the graph derivation consumes all three inputs exactly",
    )
    scaled = axiom_graph.derive_from("W5.energy", ["W5.mass", "W5.velocity"])
    expect(
        scaled["status"] == "derived"
        and scaled["formula"] == "1/2 * W5.mass * W5.velocity^2"
        and scaled["coefficient"] == "1/2"
        and [item["exponent"] for item in scaled["input_exponents"]] == ["1/1", "2/1"],
        "the exact coefficient and fractional exponents survive derivation",
    )
    cross_wheel = axiom_graph.derive_from(
        "W5.power", ["W38.input_torque", "W38.input_angular_velocity"]
    )
    cross_junctions = {
        (item["source"], item["target"])
        for item in cross_wheel["used_junctions"]
    }
    expect(
        cross_wheel["status"] == "derived"
        and cross_wheel["formula"] == "W38.input_torque * W38.input_angular_velocity"
        and [item["id"] for item in cross_wheel["used_axioms"]] == ["axiom:W38:02"]
        and cross_junctions
        == {("quantity:W38:input_power", "quantity:W5:power")},
        "a declared junction carries a cross-wheel derivation",
    )
    astro_cross = axiom_graph.derive_from(
        "W26.luminosity", ["W1.voltage", "W1.current"], max_axioms=1
    )
    astro_junctions = {
        (item["source"], item["target"])
        for item in astro_cross["used_junctions"]
    }
    expect(
        astro_cross["status"] == "derived"
        and astro_cross["formula"] == "W1.voltage * W1.current"
        and [item["id"] for item in astro_cross["used_axioms"]] == ["axiom:W1:01"]
        and astro_cross["unused_inputs"] == []
        and astro_junctions
        == {
            ("quantity:W1:power", "quantity:W15:power"),
            ("quantity:W26:luminosity", "quantity:W15:power"),
        },
        "the W26 luminosity junction carries a real cross-domain derivation",
    )
    multi_path = axiom_graph.derive_from(
        "W5.power",
        [
            "W5.force",
            "W5.velocity",
            "W38.input_torque",
            "W38.input_angular_velocity",
        ],
        k=2,
    )
    multi_formulas = {
        multi_path.get("formula"),
        *[item.get("formula") for item in multi_path.get("alternatives") or []],
    }
    expect(
        multi_path["status"] == "derived"
        and multi_path["returned"] == 2
        and len(multi_path["alternatives"]) == 1
        and multi_formulas
        == {
            "W5.force * W5.velocity",
            "W38.input_torque * W38.input_angular_velocity",
        }
        and any(
            step["kind"] == "junction"
            for step in multi_path["proof_steps"]
        )
        and multi_path["assumptions"],
        "k-best derivation returns both exact paths with proof steps",
    )
    substitution = axiom_graph.derive_from(
        "W1.power",
        ["W1.voltage", "W15.charge", "W15.time"],
        strategy="substitution",
    )
    expect(
        substitution["status"] == "derived"
        and substitution["strategy"] == "substitution"
        and substitution["formula"] == "W1.voltage * W15.charge / W15.time"
        and substitution["proof_depth"] == 2
        and [step["kind"] for step in substitution["proof_steps"]]
        == ["substitution", "substitution"]
        and substitution["proof_steps"][0]["axiom"] == "axiom:W15:00"
        and substitution["proof_steps"][1]["derives"] == "W1.power"
        and substitution["used_axioms"],
        "a bounded cross-wheel substitution path records exact steps",
    )
    unrelated = axiom_graph.derive_from(
        "W9.wavelength", ["W8.energy", "W8.temperature"]
    )
    expect(
        unrelated["status"] == "gap"
        and "disjoint" in unrelated["gaps"][0]
        and unrelated["candidate_axioms"] > 0
        and len(unrelated.get("missing_bridges") or []) == 2
        and all(
            "no declared junction" in item["detail"]
            for item in unrelated["missing_bridges"]
        ),
        "unrelated graph components return a structured missing-bridge report",
    )
    bounded = axiom_graph.derive_from("W1.power", ["W1.voltage"], max_axioms=1)
    expect(
        bounded["status"] == "gap"
        and "at most 1" in bounded["gaps"][0]
        and bounded["max_support"] == 1,
        "the exact support bound is enforced and reported",
    )
    spoke_regression = axiom_graph.regress_legacy_spokes()
    expect(
        spoke_regression["schema"] == axiom_graph.SPOKE_REGRESSION_SCHEMA
        and spoke_regression["status"] == "ok"
        and spoke_regression["total_spokes"] == 369
        and spoke_regression["derived"] == 369
        and spoke_regression["formula_matches"] == 369
        and spoke_regression["extra_input_spokes"] == 48
        and spoke_regression["extra_by_wheel"]
        == {"W13": 8, "W24": 6, "W27": 12, "W28": 4, "W36": 8, "W38": 10}
        and not spoke_regression["gaps"]
        and not spoke_regression["mismatches"],
        "all 366 spokes re-derive exactly; 48 carry extra unused inputs",
    )
    case_regression = wheels.regress_declared_cases()
    dimensional_ids = {
        item["case"] for item in case_regression["dimensional_mismatches"]
    }
    derivability_ids = {
        item["case"] for item in case_regression["derivability_mismatches"]
    }
    expect(
        case_regression["schema"] == wheels.CASE_REGRESSION_SCHEMA
        and case_regression["status"] == "ok"
        and case_regression["cases"] == 157
        and case_regression["dimensional_known"] == 157
        and case_regression["dimensional_unknown"] == 0
        and case_regression["dimensional_agreement"] == 157
        and case_regression["derivability_agreement"] == 157
        and case_regression["mismatch_count"] == 0
        and not dimensional_ids
        and not derivability_ids,
        "the 153-case corpus reconciles exactly after the dimensions/axioms were corrected",
    )
    expect(
        prefix_case_equation(
            "W14.energy = 1/2 * W14.inductance * W14.current^2", "W14"
        )
        == "W14.energy = 1/2 * W14.current^2 * W14.inductance",
        "wheel-prefix preserves an already-prefixed attribute chain and a rational constant",
    )
    expect(
        prefix_case_equation("W14.energy = 2 * W14.current", "W14")
        == "W14.energy = 2 * W14.current",
        "wheel-prefix renders a bare integer coefficient exactly",
    )
    expect(
        prefix_case_equation("W14.energy = -W15.charge", "W14")
        == "W14.energy = -1 * W15.charge",
        "wheel-prefix preserves unary negation for a cross-wheel quantity",
    )
    w26_doc = json.loads((ROOT / "wheels" / "W26.json").read_text(encoding="utf-8"))
    w27_doc = json.loads((ROOT / "wheels" / "W27.json").read_text(encoding="utf-8"))
    expect(
        w26_doc["title"] == "Astrophysics & Stellar Structure"
        and len(w26_doc["axioms"]) == 4
        and len(w26_doc["cases"]) == 5
        and w26_doc["provenance"]["status"] == "sourced"
        and len(w26_doc["provenance"]["sources"]) >= 5
        and wheels.REFERENCE_DIMENSIONS["hawking_temperature"]
        == (0, 0, 0, 0, 1, 0, 0, 0)
        and wheels.REFERENCE_DIMENSIONS["boltzmann_constant"]
        == (2, 1, -2, 0, -1, 0, 0, 0)
        and wheels.REFERENCE_DIMENSIONS["luminosity"]
        == (2, 1, -3, 0, 0, 0, 0, 0)
        and any(
            case["id"] == "W26-N1"
            and not case["expected_dimensional"]
            and not case["expected_derivable"]
            and case["physical_status"] == "negative_control"
            for case in w26_doc["cases"]
        ),
        "W26 declares sourced stellar relations, exact dimensions and a negative control",
    )
    expect(
        w27_doc["title"] == "Cosmology & Cosmic Expansion"
        and len(w27_doc["axioms"]) == 4
        and len(w27_doc["cases"]) == 5
        and w27_doc["provenance"]["status"] == "sourced"
        and len(w27_doc["provenance"]["sources"]) == 4
        and wheels.REFERENCE_DIMENSIONS["critical_density"]
        == (-3, 1, 0, 0, 0, 0, 0, 0)
        and wheels.REFERENCE_DIMENSIONS["hubble_constant"]
        == (0, 0, -1, 0, 0, 0, 0, 0)
        and wheels.REFERENCE_DIMENSIONS["horizon_distance"]
        == (1, 0, 0, 0, 0, 0, 0, 0)
        and any(
            case["id"] == "W27-N1"
            and not case["expected_dimensional"]
            and not case["expected_derivable"]
            and case["physical_status"] == "negative_control"
            for case in w27_doc["cases"]
        ),
        "W27 declares sourced expansion relations, exact dimensions and a negative control",
    )
    index_doc = json.loads((ROOT / "wheels" / "index.json").read_text(encoding="utf-8"))
    new_junction_pairs = {
        (link["wheel_a"], link["name_a"], link["wheel_b"], link["name_b"])
        for link in index_doc["junctions"]
        if link["wheel_a"] in {"W26", "W27"} or link["wheel_b"] in {"W26", "W27"}
    }
    expect(
        len(new_junction_pairs) == 10
        and ("W26", "mass", "W17", "source_mass") in new_junction_pairs
        and ("W26", "luminosity", "W15", "power") in new_junction_pairs
        and ("W27", "distance", "W11", "length") in new_junction_pairs
        and ("W27", "critical_density", "W12", "density") in new_junction_pairs
        and ("W27", "speed_of_light", "W19", "speed_of_light") in new_junction_pairs,
        "W26/W27 declare only reviewed cross-domain quantity identities",
    )
    missing_error = ""
    try:
        axiom_graph.derive_from("W20.strain", ["W1.charge"])
    except axiom_graph.DerivationLookupError as exc:
        missing_error = str(exc)
    expect(
        "W1.charge" in missing_error and "no declared" in missing_error,
        "a missing junction endpoint is refused rather than invented",
    )
    derive_cli = subprocess.run(
        [
            sys.executable,
            str(ROOT / "cent"),
            "derive",
            "W8.energy",
            "W8.mass",
            "W8.specific_heat_capacity",
            "W8.temperature",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    derive_payload = {}
    if derive_cli.returncode == 0:
        try:
            derive_payload = json.loads(derive_cli.stdout)
        except json.JSONDecodeError:
            derive_payload = {}
    derive_certificate = derive_payload.get("output_certificate") or {}
    expect(
        derive_cli.returncode == 0
        and derive_payload.get("ok") is True
        and derive_payload.get("schema") == axiom_graph.DERIVATION_SCHEMA
        and (derive_payload.get("derivation") or {}).get("formula")
        == "W8.mass * W8.specific_heat_capacity * W8.temperature"
        and derive_certificate.get("schema") == "cent-output-certificate/1"
        and derive_certificate.get("subject_schema") == "cent-derivation/1"
        and derive_certificate.get("status") == "certified",
        "CLI derive emits a successful exact derivation with a certificate",
    )
    gap_cli = subprocess.run(
        [
            sys.executable,
            str(ROOT / "cent"),
            "derive",
            "W9.wavelength",
            "W8.energy",
            "W8.temperature",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    gap_payload = {}
    if gap_cli.returncode == 0:
        try:
            gap_payload = json.loads(gap_cli.stdout)
        except json.JSONDecodeError:
            gap_payload = {}
    gap_certificate = gap_payload.get("output_certificate") or {}
    expect(
        gap_cli.returncode == 0
        and gap_payload.get("ok") is False
        and (gap_payload.get("derivation") or {}).get("status") == "gap"
        and "disjoint" in ((gap_payload.get("derivation") or {}).get("gaps") or [""])[0]
        and gap_certificate.get("status") == "gap"
        and bool(gap_certificate.get("gaps")),
        "CLI derive preserves a no-path gap instead of inventing an edge",
    )

    mechanical = discovery.discover(
        "compute a square root in a mechanical domain", domain="mechanical"
    )
    expect(mechanical["methods"], "the domain filter returns methods")
    expect(
        all(method["domain_class"] == "mechanical" for method in mechanical["methods"]),
        "the domain filter excludes other domains",
    )

    carry = discovery.discover("carry an irrational value as a physical signal")
    expect(
        {method["primitive"] for method in carry["methods"]} == {"delta_sigma_modulator"},
        "carry-only query does not mislabel a compute route as a carrier",
    )

    sequence = discovery.discover(MULTI_QUERY, limit=50)
    expect(
        sequence["multi_step"] is True and len(sequence["steps"]) == 2,
        "discovery returns both ordered goal steps",
    )
    expect(
        [step["index"] for step in sequence["steps"]] == [1, 2]
        and all(step["status"] == "pass" and step["method_count"] > 0
                for step in sequence["steps"]),
        "each ordered step has returned candidate methods",
    )
    sequence_primitives = {
        method["primitive"] for method in sequence["methods"]
    }
    expect(
        {"sqrt", "delta_sigma_modulator"} <= sequence_primitives,
        "the sequence discovers both a compute and a carry method",
    )
    expect(
        any("no declared handoff" in gap for gap in sequence["gaps"]),
        "the missing step-to-step handoff is an explicit gap",
    )
    compose_stage = next(
        stage for stage in sequence["pipeline"] if stage["stage"] == "compose"
    )
    expect(
        compose_stage["status"] == "gap"
        and "no declared handoff" in compose_stage["detail"],
        "the compose stage is present and marked incomplete",
    )
    sequence_text = discovery.render_text(sequence)
    expect(
        "Goal steps" in sequence_text
        and "compute / sqrt" in sequence_text
        and "2 ordered goal steps" in sequence_text,
        "the terminal renderer preserves the ordered step plan",
    )

    unknown = discovery.discover("zzzz")
    expect(unknown["matched"] is False, "unknown problem is not invented")
    expect(unknown["methods"] == [], "unknown problem returns no methods")
    expect(bool(unknown["suggestions"]), "unknown problem offers nearby contracts")

    try:
        json.dumps(data, ensure_ascii=False)
        serialisable = True
    except TypeError:
        serialisable = False
    expect(serialisable, "the discovery payload is JSON-serialisable")

    text = discovery.render_text(data)
    expect("PHYSICAL METHOD DISCOVERY" in text, "terminal renderer works")
    expect("Delta-sigma" in text, "terminal renderer names the carry method")

    command = [
        sys.executable, str(ROOT / "cent"), "discover", QUERY, "--json", "--limit", "8",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    cli_ok = result.returncode == 0
    cli_data = {}
    if cli_ok:
        try:
            cli_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            cli_ok = False
    expect(cli_ok, f"CLI discover command succeeds: {result.stderr[:160]}")
    expect(
        cli_data.get("schema") == "cent-discovery/1" and cli_data.get("matched"),
        "CLI emits the discovery payload",
    )

    matrix = discovery.operation_method_matrix()
    evidence_classes = set(discovery.MATRIX_EVIDENCE_CLASSES)
    expect(
        matrix["schema"] == discovery.MATRIX_SCHEMA
        and bool(matrix["rows"])
        and set(matrix["evidence_classes"]) == evidence_classes
        and json.dumps(matrix, ensure_ascii=False),
        "operation matrix exposes its declared evidence classes and is serialisable",
    )
    expect(
        all(
            row["evidence"] in evidence_classes
            and bool(row.get("domain")) and bool(row.get("carrier"))
            and bool(row.get("first_gap"))
            and row.get("role") in {"compute", "carry", "grounding"}
            for row in matrix["rows"]
        ),
        "every operation-matrix row carries evidence, role, domain, carrier and first gap",
    )
    exact_routes = {
        (row["operation"], row["route"])
        for row in matrix["rows"] if row["evidence"] == "exact-route"
    }
    expect(
        {
            ("sum", "sum-kcl"),
            ("sum", "sum-fluid"),
            ("sum", "sum-opamp"),
            ("difference", "sum-kcl"),
            ("difference", "sum-fluid"),
            ("difference", "sum-opamp"),
            ("sqrt", "sqrt-log-domain"),
            ("sqrt", "sqrt-opamp-multiplier"),
            ("delta_sigma_modulator", "delta-sigma-first-order"),
        } <= exact_routes,
        "the matrix records every exact assembled route",
    )
    templates = {
        (row["operation"], row["route"])
        for row in matrix["rows"] if row["evidence"] == "structural-template"
    }
    expect(
        {
            ("mult", "multiplier"), ("div", "divider"),
            ("exp", "diode_exp"), ("log", "log_amp"), ("sat", "clipper"),
        } <= templates,
        "the matrix records structural templates without promoting them to routes",
    )
    linked = {
        (row["operation"], row["evidence"], row["route"]): row.get("mechanism")
        for row in matrix["rows"]
        if row.get("mechanism")
    }
    expect(
        all("mechanism" in row for row in matrix["rows"])
        and linked == {
            ("difference", "exact-route", "sum-kcl"): "kcl-conservation",
            ("difference", "exact-route", "sum-fluid"): "fluid-continuity",
            ("difference", "exact-route", "sum-opamp"): "opamp-summing",
            ("sqrt", "exact-route", "sqrt-log-domain"): "log-domain-sqrt",
            ("sqrt", "declared-bridge", "W24"): "log-domain-sqrt",
            ("sum", "exact-route", "sum-kcl"): "kcl-conservation",
            ("sum", "exact-route", "sum-fluid"): "fluid-continuity",
            ("sum", "exact-route", "sum-opamp"): "opamp-summing",
            ("delta_sigma_modulator", "exact-route", "delta-sigma-first-order"):
                "delta-sigma-error-feedback",
            ("exp", "validated-transfer", "transfer-exp-log-domain-arithmetic"):
                "log-domain-arithmetic",
            ("log", "validated-transfer", "transfer-log-log-domain-arithmetic"):
                "log-domain-arithmetic",
            ("mult", "validated-transfer", "transfer-mult-log-domain-arithmetic"):
                "log-domain-arithmetic",
            ("div", "validated-transfer", "transfer-div-log-domain-arithmetic"):
                "log-domain-arithmetic",
        },
        f"the matrix attaches only explicitly declared mechanism ids: {linked}",
    )
    expect(
        all(
            row.get("mechanism") is None
            for row in matrix["rows"]
            if row["evidence"]
            in {"structural-template", "declared-analogy", "inherited-wheel-candidate", "gap"}
        )
        and all(
            row.get("mechanism") in discovery.mechanisms.MECHANISM_BY_ID
            for row in matrix["rows"]
            if row.get("mechanism")
        ),
        "weak evidence stays unlinked and every linked id is registered",
    )
    matrix_text = discovery.render_matrix(matrix)
    expect(
        matrix["summary"]["mechanism_links"] == 13
        and matrix["summary"]["validated_transfers"] == 4
        and matrix["summary"]["linked_mechanisms"] == [
            "delta-sigma-error-feedback", "fluid-continuity",
            "kcl-conservation", "log-domain-arithmetic",
            "log-domain-sqrt", "opamp-summing",
        ]
        and "mechanism: kcl-conservation" in matrix_text
        and "mechanism: delta-sigma-error-feedback" in matrix_text,
        "the matrix summary and renderer expose mechanism links",
    )
    groups = {group["role"]: group for group in matrix["groups"]}
    evidence = {row["evidence"] for row in matrix["rows"]}
    expect(
        "declared-bridge" in evidence
        and "inherited-wheel-candidate" in evidence
        and all(
            row["role"] == "carry"
            for row in groups.get("carry", {}).get("rows", [])
        )
        and not any(
            row["role"] == "carry"
            for row in groups.get("compute", {}).get("rows", [])
        ),
        "bridge/text evidence is separate and carry rows stay out of compute",
    )
    matrix_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "matrix", "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    matrix_cli_data = {}
    if matrix_cli.returncode == 0:
        try:
            matrix_cli_data = json.loads(matrix_cli.stdout)
        except json.JSONDecodeError:
            matrix_cli_data = {}
    filtered = discovery.operation_method_matrix(operation="mult")
    expect(
        matrix_cli.returncode == 0
        and matrix_cli_data.get("schema") == discovery.MATRIX_SCHEMA
        and (matrix_cli_data.get("output_certificate") or {}).get("subject_schema")
        == discovery.MATRIX_SCHEMA
        and all(row["operation"] == "mult" for row in filtered["rows"]),
        "CLI matrix emits its certificate and supports an operation filter",
    )

    shape = envelope.orientation_envelope(
        [(0, 1), (1, 0), (0, -1), (-1, 0)]
    )
    expect(
        shape["schema"] == envelope.SCHEMA
        and shape["method"] == envelope.METHOD
        and shape["summary"]["best_area"] == {"num": "2", "den": "1"}
        and shape["summary"]["global_optimal"] is False
        and len(shape["best"]["corners"]) == 4
        and shape["passed"] is True,
        "the exact orientation envelope finds the minimum area over its declared directions",
    )

    envelope_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "envelope",
            "--point", "0,1", "--point", "1,0",
            "--point", "0,-1", "--point=-1,0", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    envelope_payload = (
        json.loads(envelope_cli.stdout) if envelope_cli.returncode == 0 else {}
    )
    expect(
        envelope_cli.returncode == 0
        and envelope_payload.get("schema") == envelope.SCHEMA
        and envelope_payload.get("summary", {}).get("best_area")
        == {"num": "2", "den": "1"}
        and (envelope_payload.get("output_certificate") or {}).get("subject_schema")
        == envelope.SCHEMA,
        "the envelope CLI emits exact JSON and its certificate",
    )

    invalid_envelope = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "envelope",
            "--point", "0,0", "--direction", "0,0", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        invalid_envelope.returncode == 2
        and "direction must be nonzero" in invalid_envelope.stderr,
        "the envelope CLI rejects a zero direction instead of inventing one",
    )

    bbox = discovery.discover("compute a minimum-area bounding box for points")
    bbox_method = bbox["methods"][0] if bbox.get("methods") else {}
    bbox_model = bbox_method.get("route_model") or {}
    expect(
        bbox.get("matched") is True
        and bbox_method.get("primitive") == "bounding_box"
        and bbox_method.get("route") == "exact-algorithm"
        and bbox_model.get("kind") == "exact-algorithm"
        and bbox_method.get("contract_exact") is True
        and bbox_method.get("simulation") is False
        and (bbox_method.get("route_simulation") or {}).get("passed") is True,
        "the envelope is discoverable as a declared exact-algorithm method",
    )
    bbox_matrix = discovery.operation_method_matrix(operation="bounding_box")
    bbox_rows = bbox_matrix["rows"]
    expect(
        bbox_matrix["schema"] == discovery.MATRIX_SCHEMA
        and len(bbox_rows) == 1
        and bbox_rows[0]["evidence"] == "exact-algorithm"
        and bbox_rows[0]["route"] == "orientation-envelope"
        and bbox_rows[0]["role"] == "compute"
        and bbox_rows[0]["carrier"] == "rational point set"
        and bbox_matrix["summary"]["exact_algorithms"] == 1
        and bbox_matrix["summary"]["operations"] == 1,
        "the operation matrix has one exact-algorithm row for the envelope",
    )

    sqrt_pipe = pipeline.build_pipeline("sqrt")
    difference_pipe = pipeline.build_pipeline("difference")
    expect(
        sqrt_pipe["schema"] == pipeline.SCHEMA
        and sqrt_pipe["passed"] is True
        and sqrt_pipe["summary"]["operations"] == ["log", "scale", "exp"]
        and [handoff["wire"] for handoff in sqrt_pipe["handoffs"]]
        == ["x", "ln_x", "half_ln"]
        and difference_pipe["summary"]["operations"] == ["neg", "sum"]
        and difference_pipe["summary"]["feedback_handoffs"] == 0
        and difference_pipe["passed"] is True,
        "sqrt and difference routes decompose into their declared micro-stages",
    )
    carry_pipe = pipeline.build_pipeline("quantized_carry")
    feedback = [
        handoff for handoff in carry_pipe["handoffs"]
        if handoff["kind"] == "feedback"
    ]
    expect(
        carry_pipe["summary"]["operations"]
        == ["neg", "sum", "accum", "quantize", "sat", "delay"]
        and carry_pipe["summary"]["stages"] == 6
        and len(feedback) == 1
        and feedback[0]["from_stage"] == 6
        and feedback[0]["to_stage"] == 1
        and feedback[0]["wire"] == "feedback"
        and carry_pipe["passed"] is True,
        "the delta-sigma route exposes its individual stages and declared feedback edge",
    )
    pipeline_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "pipeline", "sqrt", "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    pipeline_payload = (
        json.loads(pipeline_cli.stdout) if pipeline_cli.returncode == 0 else {}
    )
    expect(
        pipeline_cli.returncode == 0
        and pipeline_payload.get("schema") == pipeline.SCHEMA
        and pipeline_payload.get("operation") == "sqrt"
        and (pipeline_payload.get("output_certificate") or {}).get("subject_schema")
        == pipeline.SCHEMA,
        "the pipeline CLI emits exact JSON and its certificate",
    )

    leads = hypotheses.LEADS
    lead_wheel = hypotheses.lead_wheel()
    expect(
        {lead.id for lead in leads}
        == {"nematic-q-tensor-bounding-box", "bresenham-quantized-carry"}
        and all(
            lead.status.value == "doesnt_know"
            and lead.needs
            and not hasattr(lead, "supported_operations")
            for lead in leads
        )
        and lead_wheel.summary()["rings"]["doesnt_know"] == 2
        and lead_wheel.summary()["total"] == 2,
        "pre-admission leads use the knowledge wheel without a supported_operations field",
    )
    bbox_hypotheses = hypotheses.match_operation("bounding_box")
    expect(
        bbox_hypotheses["schema"] == hypotheses.SCHEMA
        and bbox_hypotheses["summary"]["supported_operations_changed"] is False
        and bbox_hypotheses["summary"]["admitted"] == 0
        and any(
            item["mechanism"] == "cam-profile"
            and item["status"] == "doesnt_know"
            for item in bbox_hypotheses["pre_admission"]
        )
        and any(
            item["id"] == "nematic-q-tensor-bounding-box"
            for item in bbox_hypotheses["leads"]
        )
        and all(
            item["admission"] == "pre_admission_card"
            for item in bbox_hypotheses["pre_admission"]
        ),
        "the envelope query surfaces a structural card match and its Q-tensor lead before admission",
    )
    carry_hypotheses = hypotheses.match_operation("quantized_carry")
    expect(
        carry_hypotheses["summary"]["supported_operations_changed"] is False
        and any(
            item["mechanism"] == "delta-sigma-error-feedback"
            for item in carry_hypotheses["admitted"]
        )
        and any(
            item["id"] == "bresenham-quantized-carry"
            for item in carry_hypotheses["leads"]
        )
        and all(
            item["admission"] == "pre_admission_card"
            for item in carry_hypotheses["pre_admission"]
        ),
        "the carry query surfaces its Bresenham lead without promoting it",
    )
    hypothesis_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "hypothesis", "bounding_box", "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    hypothesis_payload = (
        json.loads(hypothesis_cli.stdout) if hypothesis_cli.returncode == 0 else {}
    )
    expect(
        hypothesis_cli.returncode == 0
        and hypothesis_payload.get("schema") == hypotheses.SCHEMA
        and hypothesis_payload.get("operation") == "bounding_box"
        and hypothesis_payload.get("summary", {}).get("supported_operations_changed")
        is False
        and (hypothesis_payload.get("output_certificate") or {}).get("subject_schema")
        == hypotheses.SCHEMA,
        "the hypothesis CLI emits its own pre-admission JSON certificate",
    )

    lead_id = "nematic-q-tensor-bounding-box"
    questions = hypotheses.questions_for(lead_id)
    initial = hypotheses.resolve_lead(lead_id)
    expect(
        len(questions) == 3
        and [question["kind"] for question in questions]
        == ["proof", "test", "definition"]
        and all(question["need"] for question in questions)
        and initial["schema"] == hypotheses.RESOLUTION_SCHEMA
        and initial["status"] == "needs_input"
        and initial["answered"] == 0
        and initial["next_question"]["id"] == "q1"
        and initial["knowledge_state"] == "doesnt_know"
        and initial["supported_operations_changed"] is False,
        "the resolver asks one specific unmet need at a time before any decision",
    )
    answers = {
        question["id"]: f"artifact for {question['kind']}"
        for question in questions
    }
    ready = hypotheses.resolve_lead(lead_id, answers)
    kept = hypotheses.resolve_lead(lead_id, answers, "keep")
    expect(
        ready["status"] == "ready_for_decision"
        and ready["answered"] == 3
        and ready["next_question"]["id"] == "decision"
        and kept["status"] == "retained"
        and kept["active"] is True
        and kept["decision"] == "keep"
        and kept["knowledge_state"] == "doesnt_know"
        and kept["supported_operations_changed"] is False
        and hypotheses.LEAD_BY_ID[lead_id].status.value == "doesnt_know",
        "supplied needs produce a decision point, and keep retains without promotion",
    )
    pending_retire = hypotheses.resolve_lead(lead_id, answers, "retire")
    retired = hypotheses.resolve_lead(
        lead_id, answers, "retire", "proof and negative control are still missing"
    )
    expect(
        pending_retire["status"] == "needs_note"
        and pending_retire["next_question"]["id"] == "decision_note"
        and retired["status"] == "retired"
        and retired["active"] is False
        and retired["decision_note"] == "proof and negative control are still missing"
        and retired["supported_operations_changed"] is False
        and hypotheses.LEAD_BY_ID[lead_id].status.value == "doesnt_know",
        "retire requires a reason and records retirement without erasing the lead",
    )
    resolve_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "hypothesis",
            "--resolve", lead_id,
            "--answer", "q1=artifact for proof",
            "--answer", "q2=artifact for test",
            "--answer", "q3=artifact for definition",
            "--decision", "retire",
            "--note", "proof and negative control are still missing",
            "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    resolve_payload = (
        json.loads(resolve_cli.stdout) if resolve_cli.returncode == 0 else {}
    )
    expect(
        resolve_cli.returncode == 0
        and resolve_payload.get("schema") == hypotheses.RESOLUTION_SCHEMA
        and resolve_payload.get("status") == "retired"
        and resolve_payload.get("active") is False
        and resolve_payload.get("supported_operations_changed") is False
        and (resolve_payload.get("output_certificate") or {}).get("subject_schema")
        == hypotheses.RESOLUTION_SCHEMA,
        "the resolution CLI emits a certified keep/retire decision",
    )

    print()
    print("=" * 78)
    print(f"METHOD DISCOVERY: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
