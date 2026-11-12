#!/usr/bin/env python3
"""Verification suite for the console UI (`cent ui` / `cent report` / `cent eval`).

Runs without pytest: ``python3 tests/test_ui.py``.

Checks cover the report contents, the exact-program mapping, the material
bundle's JSON round-trip, saving, the interactive shell and the CLI wiring.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler.evaluator import Evaluator  # noqa: E402
from cent_compiler.exact import CentError  # noqa: E402
from cent_compiler.grammar import CGraph, COp  # noqa: E402
from cent_compiler.hypothesis_bridge import LAYERS  # noqa: E402
from cent_compiler.interval import Interval  # noqa: E402
from cent_compiler.output_certificate import attach_certificate  # noqa: E402
from cent_compiler.program import program_from_dict  # noqa: E402
from cent_compiler.ui import (  # noqa: E402
    Shell,
    build_report,
    load_material,
    program_from_dag,
    render_report,
    run_material,
    save_material,
)

CHECKS: list[tuple[str, str, object]] = []


def check(group: str, name: str):
    def register(fn):
        CHECKS.append((group, name, fn))
        return fn

    return register


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


VELOCITY = "velocity = (2 * energy / mass)^(1/2)"
CROSS_DOMAIN_FIXTURES = (
    ("electrical", "y = sqrt(5)", "electrical"),
    ("mechanical", "pressure = force / area", "mechanical"),
    ("fluidic", "flow = sqrt(pressure)", "fluidic"),
)
RELATION_ARTIFACT_GAP = "compile material is a relation artifact, not a physical route"


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

@check("report", "a £ yields its DAG, primitive census, ∆ ranking and material")
def _():
    report = build_report(VELOCITY)
    expect(
        {op.op for op in report.ops} == {"scale", "div", "sqrt"},
        f"ops: {[op.op for op in report.ops]}",
    )
    expect(report.primitive_counts == {"scale": 1, "div": 1, "sqrt": 1}, "census")
    expect(
        report.atomic_count + report.composite_count == len(report.ops),
        "every primitive is classified",
    )
    expect(report.impl_count > 0, "the DAG must enumerate implementations")
    expect(report.template == "opamp_sqrt", f"template: {report.template}")
    expect(report.template_status == "match", f"template status: {report.template_status}")
    expect(
        report.template_decision.get("structural") is True
        and report.template_decision.get("proposal_effect") == "none",
        f"template decision: {report.template_decision}",
    )
    expect(bool(report.netlist) and "sqrt" in report.netlist.lower(), "netlist")
    expect(set(report.inputs) == {"energy", "mass"}, f"inputs: {report.inputs}")
    expect(report.program is not None, f"program notes: {report.notes}")
    expect(
        len(report.fidelity) == len(report.top)
        and all(1 <= len(item["layers"]) <= 5 for item in report.fidelity),
        f"fidelity trace: {report.fidelity}",
    )
    expect(
        any(
            item["domain"] == "electrical"
            and item["converged"]
            and [layer["layer"] for layer in item["layers"]]
            == [layer.name for layer in LAYERS]
            for item in report.fidelity
        ),
        f"an electrical candidate must run the full layer cascade: {report.fidelity}",
    )

    # A DAG that merely contains sqrt must not inherit the sqrt template when
    # its complete operation set does not fit that topology.
    gap = build_report("y = sqrt(5) * pressure")
    expect(gap.template is None, f"unexpected template: {gap.template}")
    expect(gap.template_status == "gap", f"template status: {gap.template_status}")
    expect(gap.netlist is None, "a gap must not invent a netlist")
    expect(
        gap.template_decision.get("structural") is True
        and gap.template_decision.get("proposal_effect") == "none",
        f"gap decision: {gap.template_decision}",
    )
    gap_domains = {impl.substrate_domain for impl, _ in gap.top}
    expect(
        "mechanical" in gap_domains,
        f"a template gap suppressed a non-electrical proposal: {gap_domains}",
    )
    expect(
        "does not filter ∆ proposals" in render_report(gap),
        "the report must state the template decision does not filter proposals",
    )
    expect(
        any("complete ¢ operation set" in note for note in gap.notes),
        f"missing explicit template gap: {gap.notes}",
    )


@check("report", "a thermal £ exposes a non-electrical ∆ proposal")
def _():
    report = build_report(
        "heat_rate = thermal_conductivity * area * temperature_gradient"
    )
    expect(report.top, "the thermal £ must rank implementations")
    domains = {impl.substrate_domain for impl, _ in report.top}
    expect(
        "mechanical" in domains,
        f"top-N lost the mechanical candidate; domains={domains}",
    )
    expect(report.delta_sigma_count == 0, "this thermal DAG needs no ∆Σ carrier")

    mechanical = [
        (impl, cost) for impl, cost in report.top
        if impl.substrate_domain == "mechanical"
    ]
    expect(bool(mechanical), "the mechanical candidate must carry its ranking")
    impl, _cost = mechanical[0]
    expect(impl.carrier_type == "spatial", f"carrier: {impl.carrier_type}")
    mechanical_fidelity = [
        item for item in report.fidelity if item["domain"] == "mechanical"
    ]
    expect(
        mechanical_fidelity
        and any(
            layer["status"] == "gap"
            for layer in mechanical_fidelity[0]["layers"]
        ),
        f"mechanical fidelity must not borrow electrical noise checks: {mechanical_fidelity}",
    )
    components = " ".join(impl.components).lower()
    expect(
        "rack" in components and "pinion" in components,
        f"mechanical components: {impl.components}",
    )
    gaps = report.material().get("output_certificate", {}).get("gaps") or []
    expect(gaps and gaps[0] == RELATION_ARTIFACT_GAP, f"first gap: {gaps}")


@check("report", "cross-domain fixtures expose expected domains and first gap")
def _():
    for name, formula, expected_domain in CROSS_DOMAIN_FIXTURES:
        report = build_report(formula)
        expect(report.impl_count > 0, f"{name}: no ∆ candidates")
        domains = {impl.substrate_domain for impl, _ in report.top}
        expect(
            expected_domain in domains,
            f"{name}: expected {expected_domain}, got {sorted(domains)}",
        )
        gaps = report.material().get("output_certificate", {}).get("gaps") or []
        expect(
            gaps and gaps[0] == RELATION_ARTIFACT_GAP,
            f"{name}: first gap {gaps}",
        )


@check("report", "the generated exact program evaluates exactly")
def _():
    material = json.loads(json.dumps(build_report(VELOCITY).material()))
    rows = run_material(
        material, overrides={"energy": Fraction(8), "mass": Fraction(1)}
    )
    expect(
        rows[0]["velocity"] == Interval.point(4),
        f"sqrt(16) must be exactly 4, got {rows[0]['velocity']}",
    )


@check("report", "a numeric literal becomes an exact binding, not a float")
def _():
    report = build_report("y = sqrt(5)")
    expect(report.program is not None, f"notes: {report.notes}")
    expect(report.bindings.get("_one") == 1, "the synthetic unit wire is bound to 1")
    material = report.material()
    expect("_one" in material["program"]["inputs"], "the binding is a program input")
    value = run_material(material)[0]["y"]
    expect(value.contains(value.midpoint), "the output is an enclosure")
    expect(
        abs(value.midpoint**2 - 5) < Fraction(1, 10**9),
        f"got {value.midpoint}",
    )


@check("report", "an unsupported primitive is reported, never guessed")
def _():
    dag = CGraph(ops=[COp("eq", ("error",), "y")], inputs={"error"}, outputs={"y"})
    program, bindings, notes = program_from_dag(dag)
    expect(program is None, "eq with one input cannot be an exact program")
    expect(bool(notes), "the reason must be recorded")
    expect("eq" in notes[0], f"note: {notes[0]}")
    expect(bindings == {}, "no bindings for a rejected program")


@check("report", "binary addition and subtraction decompose to sum and neg")
def _():
    add = build_report("y = x + z")
    expect({op.op for op in add.ops} == {"sum"}, f"addition ops: {add.ops}")
    expect(add.program is not None, f"addition program notes: {add.notes}")
    expect(add.template == "kcl_summer", f"addition template: {add.template}")

    sub = build_report("y = x - z")
    expect([op.op for op in sub.ops] == ["neg", "sum"], f"subtraction ops: {sub.ops}")
    expect(sub.program is not None, f"subtraction program notes: {sub.notes}")
    expect(sub.template == "kcl_summer", f"subtraction template: {sub.template}")


@check("report", "the rendered report shows every section")
def _():
    text = render_report(build_report(VELOCITY))
    for section in ("1. ¢ DAG", "2. ¢ primitives", "3. ∆ implementations",
                    "4. Top ∆", "5. Generated material"):
        expect(section in text, f"missing section {section!r}")


# ---------------------------------------------------------------------------
# material bundle
# ---------------------------------------------------------------------------

@check("bundle", "the bundle is complete and JSON-serialisable")
def _():
    material = build_report("y = sqrt(5)").material()
    json.dumps(material, sort_keys=True)  # must not raise on Fractions
    expect(material["schema"] == "cent-material/1", "schema")
    for key in ("relation", "target", "dag", "summary", "program", "bindings",
                "spice", "notes"):
        expect(key in material, f"missing key {key!r}")
    expect(material["spice"]["netlist"], "the netlist is embedded")
    certificate = material.get("output_certificate") or {}
    expect(
        certificate.get("schema") == "cent-output-certificate/1"
        and certificate.get("subject_schema") == "cent-material/1"
        and certificate.get("status") == "partial"
        and any("not a physical route" in str(gap) for gap in certificate.get("gaps", ()))
        and any(
            check.get("name") == "structural template decision"
            and check.get("status") == "pass"
            for check in certificate.get("checks", ())
        ),
        f"material certificate: {certificate}",
    )


@check("bundle", "saving writes material, netlist and report")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        report = build_report("y = sqrt(5)")
        paths = save_material(report, tmp)
        expect(len(paths) == 3, f"expected 3 files, got {[p.name for p in paths]}")
        for path in paths:
            expect(path.exists() and path.stat().st_size > 0, f"empty: {path}")
        expect("sqrt" in paths[1].name, f"netlist name: {paths[1].name}")
        expect(load_material(paths[0])["schema"] == "cent-material/1", "round-trip")


@check("bundle", "a saved bundle runs through the exact core")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        paths = save_material(build_report(VELOCITY), tmp)
        material = load_material(paths[0])
        rows = run_material(material, overrides={"energy": 8, "mass": 1})
        expect(rows[0]["velocity"] == Interval.point(4), f"got {rows[0]['velocity']}")


@check("bundle", "a material with no exact program is refused explicitly")
def _():
    dag = CGraph(ops=[COp("eq", ("error",), "y")], inputs={"error"}, outputs={"y"})
    material = build_report("y = sqrt(5)").material()
    material["program"] = None
    try:
        run_material(material)
    except CentError as exc:
        expect("no exact program" in exc.message, exc.message)
        return
    raise AssertionError("run_material must refuse a missing program")


# ---------------------------------------------------------------------------
# shell and CLI
# ---------------------------------------------------------------------------

@check("shell", "the interactive shell reports and quits cleanly")
def _():
    script = iter(["help", "y = sqrt(5)", ":quit"])
    out: list[str] = []
    code = Shell(out=out.append).run(lambda prompt: next(script))
    text = "\n".join(out)
    expect(code == 0, "clean exit")
    for expected in ("¢ primitives", "∆ implementations", "Exact program"):
        expect(expected in text, f"missing {expected!r}")


@check("shell", "auto-save writes a bundle after each report")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        script = iter([f":save {tmp}", "y = sqrt(5)", ":quit"])
        out: list[str] = []
        code = Shell(out=out.append).run(lambda prompt: next(script))
        expect(code == 0, "clean exit")
        expect(any("wrote" in line for line in out), "save must be reported")
        expect(list(pathlib.Path(tmp).glob("*.material.json")), "bundle written")


@check("cli", "cent report runs end to end")
def _():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "report", "y = sqrt(5)"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(result.returncode == 0, result.stderr)
    expect("¢ primitives" in result.stdout, result.stdout[:400])


@check("cli", "cent eval runs a saved bundle with --set overrides")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        paths = save_material(build_report(VELOCITY), tmp)
        result = subprocess.run(
            [sys.executable, str(ROOT / "cent"), "eval", str(paths[0]),
             "--set", "energy=8", "--set", "mass=1"],
            cwd=ROOT, capture_output=True, text=True,
        )
        expect(result.returncode == 0, result.stderr)
        expect("velocity = [4]" in result.stdout, result.stdout)


@check("cli", "cent guide explains £ syntax and the cross-domain ∆ pipeline")
def _():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "guide"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(result.returncode == 0, result.stderr)
    expect(
        "ENTERING A £" in result.stdout
        and "cent compile" in result.stdout
        and "sqrt(x)" in result.stdout
        and "cross-domain" in result.stdout.lower()
        and "∆" in result.stdout,
        result.stdout[:500],
    )


@check("cli", "cent compile --json exposes ranked domain/carrier proposals")
def _():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "compile",
         "heat_rate = thermal_conductivity * area * temperature_gradient",
         "--json"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    expect(payload["schema"] == "cent-compile/1", payload)
    expect(payload["summary"]["implementations"] > 0, payload["summary"])
    expect(payload["proposals"], "the payload must carry ranked proposals")
    expect(
        payload.get("fidelity")
        and len(payload["fidelity"]) == len(payload["proposals"])
        and any(
            item["domain"] == "mechanical"
            and any(
                layer["status"] == "gap"
                for layer in item["layers"][1:]
            )
            for item in payload["fidelity"]
        ),
        f"compile payload fidelity: {payload.get('fidelity')}",
    )
    spice_decision = (payload.get("spice") or {}).get("decision") or {}
    expect(
        spice_decision.get("structural") is True
        and spice_decision.get("proposal_effect") == "none"
        and spice_decision.get("basis") == "complete ¢ operation set",
        f"spice decision: {spice_decision}",
    )
    boundary = payload.get("boundary") or {}
    expect(
        boundary.get("status") == "not-fabricated"
        and "not a fabricated or measured device" in boundary.get("claim", "")
        and boundary.get("missing_evidence"),
        f"top-level boundary: {boundary}",
    )
    for proposal in payload["proposals"]:
        for key in ("rank", "domain", "carrier", "components", "boundary", "cost"):
            expect(key in proposal, f"missing proposal key {key!r}: {proposal}")
        proposal_boundary = proposal["boundary"]
        expect(
            proposal_boundary.get("status") == "not-fabricated"
            and "not a fabricated or measured device"
            in proposal_boundary.get("claim", ""),
            f"proposal boundary: {proposal_boundary}",
        )
        for key in ("total", "component_count", "domain_consistency",
                    "carrier_consistency", "implementation", "precision", "speed"):
            expect(key in proposal["cost"], f"missing cost key {key!r}: {proposal}")
    expect(
        any(
            proposal["domain"] == "mechanical"
            and proposal["carrier"] == "spatial"
            and any("rack" in component.lower() for component in proposal["components"])
            for proposal in payload["proposals"]
        ),
        payload["proposals"],
    )
    certificate = payload.get("output_certificate") or {}
    expect(
        certificate.get("schema") == "cent-output-certificate/1"
        and certificate.get("subject_schema") == "cent-compile/1",
        certificate,
    )
    expect(
        any(
            check.get("name") == "fabrication boundary"
            and check.get("status") == "pass"
            for check in certificate.get("checks", [])
        ),
        certificate,
    )
    expect(
        any(
            check.get("name") == "structural template decision"
            and check.get("status") == "pass"
            for check in certificate.get("checks", [])
        ),
        certificate,
    )

    # A tooling consumer must be able to reject a payload that omits the
    # explicit no-filtering contract, rather than trusting the rest of the
    # compile output by default.
    missing = json.loads(result.stdout)
    missing.pop("output_certificate", None)
    missing["spice"].pop("decision", None)
    missing_certificate = attach_certificate(missing).get("output_certificate") or {}
    expect(
        any(
            check.get("name") == "structural template decision"
            and check.get("status") == "gap"
            for check in missing_certificate.get("checks", [])
        ),
        missing_certificate,
    )

    # The contract is value-sensitive: a present but contradictory effect
    # must be rejected just like an omitted decision.
    tampered = json.loads(result.stdout)
    tampered.pop("output_certificate", None)
    tampered["spice"]["decision"]["proposal_effect"] = "filters-proposals"
    tampered_certificate = attach_certificate(tampered).get("output_certificate") or {}
    expect(
        any(
            check.get("name") == "structural template decision"
            and check.get("status") == "gap"
            and "proposal_effect='filters-proposals'" in check.get("detail", "")
            for check in tampered_certificate.get("checks", [])
        ),
        tampered_certificate,
    )


@check("cli", "cent compile states the no-fabrication boundary")
def _():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "compile",
         "heat_rate = thermal_conductivity * area * temperature_gradient"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(result.returncode == 0, result.stderr)
    expect(
        "Proposal boundary:" in result.stdout
        and "not a fabricated or measured device" in result.stdout
        and "structural selection" in result.stdout
        and "proposal_effect=none" in result.stdout,
        result.stdout[-800:],
    )


@check("cli", "parse errors offer accepted symbols and a fixed example")
def _():
    cases = (
        ("y = sqr(5)", "nearest accepted function: sqrt", True),
        ("y = 5 % 2", "accepted: operator", True),
        ("y = sqrt(5", "parenthes", False),
    )
    for formula, expected, check_no_echo in cases:
        result = subprocess.run(
            [sys.executable, str(ROOT / "cent"), "compile", formula],
            cwd=ROOT, capture_output=True, text=True,
        )
        expect(result.returncode == 2, (formula, result.returncode, result.stderr))
        expect(expected in result.stderr, (formula, result.stderr))
        expect(
            'cent compile "y = sqrt(5)"' in result.stderr,
            (formula, result.stderr),
        )
        if check_no_echo:
            expect(formula not in result.stderr, (formula, result.stderr))


@check("cli", "cent mechanism list shows the seeded registry and JSON")
def _():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "mechanism", "list"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(result.returncode == 0, result.stderr)
    expect(
        "MECHANISM REGISTRY" in result.stdout
        and "8 seeded cent-mechanism/1 cards" in result.stdout,
        result.stdout[:600],
    )
    ids = (
        "delta-sigma-error-feedback",
        "log-domain-sqrt",
        "kcl-conservation",
        "fluid-continuity",
        "opamp-summing",
        "cam-profile",
        "orifice-pressure-flow",
        "pll-phase-tracking",
    )
    for card_id in ids:
        expect(card_id in result.stdout, f"missing {card_id}: {result.stdout[:600]}")

    json_result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "mechanism", "list", "--json"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(json_result.returncode == 0, json_result.stderr)
    payload = json.loads(json_result.stdout)
    expect(
        payload.get("schema") == "cent-mechanism-registry/1"
        and payload.get("count") == 8
        and len(payload.get("mechanisms") or ()) == 8,
        payload,
    )
    expect(
        all(
            item.get("schema") == "cent-mechanism/1"
            and item.get("id") in ids
            and item.get("gaps")
            for item in payload["mechanisms"]
        ),
        payload["mechanisms"],
    )


@check("cli", "cent mechanism id emits one card and rejects unknown ids")
def _():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "mechanism",
         "delta-sigma-error-feedback", "--json"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(result.returncode == 0, result.stderr)
    card = json.loads(result.stdout)
    expect(
        card.get("schema") == "cent-mechanism/1"
        and card.get("id") == "delta-sigma-error-feedback"
        and card.get("evidence_level") == "source-simulated"
        and card.get("provenance")
        and card.get("gaps"),
        card,
    )

    human = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "mechanism", "cam-profile"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(human.returncode == 0, human.stderr)
    expect(
        "MECHANISM CARD" in human.stdout
        and "cam-profile" in human.stdout
        and "Gaps" in human.stdout,
        human.stdout[:600],
    )

    unknown = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "mechanism", "not-a-mechanism"],
        cwd=ROOT, capture_output=True, text=True,
    )
    expect(unknown.returncode == 2, unknown.returncode)
    expect(
        "unknown mechanism id" in unknown.stderr
        and "known:" in unknown.stderr,
        unknown.stderr,
    )


@check("docs", "local Markdown links resolve")
def _():
    import re

    files = [ROOT / "README.md", ROOT / "PHYSICAL_COMPILER_ROADMAP.md"]
    files += sorted((ROOT / "docs").glob("*.md"))
    files += sorted((ROOT / "docs" / "archive").glob("*.md"))
    missing = []
    for path in files:
        for raw in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            target = raw.strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if target and "{" not in target and not (path.parent / target).exists():
                missing.append((str(path.relative_to(ROOT)), raw))
    expect(not missing, f"missing local documentation links: {missing}")


@check("cli", "cent ui accepts a piped £ session")
def _():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "ui"],
        cwd=ROOT, input="y = sqrt(5)\n:quit\n", capture_output=True, text=True,
    )
    expect(result.returncode == 0, result.stderr)
    expect("£  y = sqrt(5)" in result.stdout, result.stdout[:400])


# ---------------------------------------------------------------------------

def main() -> int:
    failures: list[tuple[str, str, BaseException]] = []
    group = None
    for current_group, name, fn in CHECKS:
        if current_group != group:
            print(f"\n[{current_group}]")
            group = current_group
        try:
            fn()
        except BaseException as exc:  # noqa: BLE001 - the harness reports everything
            failures.append((current_group, name, exc))
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"  PASS  {name}")

    total = len(CHECKS)
    print("\n" + "=" * 78)
    if failures:
        print(f"CONSOLE UI: {total - len(failures)}/{total} checks passed, {len(failures)} failed")
        return 1
    print(f"CONSOLE UI: {total}/{total} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
