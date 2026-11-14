#!/usr/bin/env python3
"""Focused tests for declared fabrication geometry, DRC and thermal placement.

Run without pytest: ``python3 tests/test_fabrication.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import fabrication  # noqa: E402
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


def check(plan: fabrication.FabricationPlan, name: str) -> fabrication.FabricationCheck:
    return next(item for item in plan.checks if item.name == name)


def footprint(plan: fabrication.FabricationPlan, ref: str) -> fabrication.Footprint:
    return next(item for item in plan.footprints if item.ref == ref)


def main() -> int:
    print("=" * 78)
    print("DECLARED FABRICATION GEOMETRY")
    print("=" * 78)

    log = fabrication.emit_fabrication(
        "sqrt-log", input_min=Fraction(1, 2), input_max=Fraction(1)
    )
    expect(
        log.physical.route_key == "sqrt-log"
        and log.physical.selected is not None
        and log.physical.selected.option.name == "precision-20",
        "the log-domain reference design is retained in the geometry",
    )
    expect(
        {item.ref for item in log.footprints}
        == {"VIN", "RIN", "BLOG", "EDIV", "BANTI", "ROUT"},
        "every reference part receives exactly one footprint",
    )
    expect(
        all(
            item.package.pad_count == len(item.pads)
            for item in log.footprints
        ),
        "each declared land pattern carries its declared pad count",
    )
    expect(
        footprint(log, "RIN").package.name == "chip-0603"
        and footprint(log, "BLOG").package.name == "module-2"
        and footprint(log, "EDIV").package.name == "module-4",
        "footprint packages follow the declared part kinds and pin counts",
    )
    expect(
        footprint(log, "BLOG").row == "quiet"
        and footprint(log, "BANTI").row == "quiet"
        and footprint(log, "RIN").row == "logger",
        "temperature-sensitive junctions are moved to the declared quiet row",
    )
    log_vin = next(part.value for part in log.physical.parts if part.ref == "VIN")
    log_rin = next(part.value for part in log.physical.parts if part.ref == "RIN")
    expect(
        footprint(log, "RIN").dissipation == log_vin * log_vin / log_rin
        and footprint(log, "RIN").junction_temperature
        == Fraction(298) + footprint(log, "RIN").dissipation * 200,
        "the input resistor dissipation and junction rise are computed exactly",
    )
    expect(
        footprint(log, "ROUT").dissipation > 0
        and footprint(log, "ROUT").junction_temperature > 298,
        "the output resistor carries the certified output-current bound",
    )
    expect(
        footprint(log, "EDIV").dissipation == 0
        and "ideal or passive" in footprint(log, "EDIV").dissipation_source,
        "ideal behavioral parts declare zero dissipation explicitly",
    )
    expect(
        check(log, "Thermal keep-out").value >= Fraction(5)
        and check(log, "Thermal keep-out").status == "pass",
        "the quiet row clears the declared sensitive/dissipator keep-out",
    )
    expect(
        check(log, "Junction temperature").value
        == max(item.junction_temperature for item in log.footprints)
        and check(log, "Junction temperature").status == "pass",
        "the hottest declared junction is checked against the limit",
    )
    expect(
        [item.name for item in log.checks] == [
            "Reference coverage",
            "Net routability",
            "Board edge",
            "Trace width",
            "Footprint courtyards",
            "Copper clearance",
            "Via annular ring",
            "Thermal keep-out",
            "Junction temperature",
            "Stackup",
        ],
        "the geometry exposes every declared design-rule check",
    )
    expect(
        log.status == "drc-pass" and log.passed
        and all(item.status == "pass" for item in log.checks),
        "the default log-domain geometry satisfies every declared rule",
    )

    expect(
        [layer.name for layer in log.stackup.layers]
        == ["top", "in1", "in2", "bottom"],
        "the declared stackup has the four expected copper layers",
    )
    expect(
        log.stackup.total_thickness == Fraction(122, 100)
        and log.stackup.relative_permittivity == Fraction(22, 5),
        "the total stackup thickness and permittivity are exact",
    )
    expect(
        len(log.traces) == 10 and len(log.vias) == 20
        and len({(trace.net, trace.layer) for trace in log.traces}) == 6,
        "multi-pin nets route as vertical escapes on in1 and buses on in2",
    )
    expect(
        all(trace.width == Fraction(1, 4) for trace in log.traces),
        "every trace carries the declared width",
    )
    expect(
        all(via.annular_ring == Fraction(3, 20) for via in log.vias),
        "every via exposes the declared annular ring",
    )
    expect(
        log.unrouted == ("half",)
        and "control label" in check(log, "Net routability").detail,
        "the single-pin half-gain control label is declared rather than invented",
    )

    net = next(item for item in log.parasitics if item.net == "in")
    expected_length = sum(
        trace.length for trace in log.traces if trace.net == "in"
    )
    expect(
        net.length == expected_length and net.length > 0,
        "net length is the exact sum of its routed segment lengths",
    )
    expect(
        net.resistance
        == fabrication.COPPER_RESISTIVITY
        * net.length
        / (Fraction(1, 4) * fabrication.COPPER_THICKNESS),
        "trace resistance follows the declared resistivity and cross-section",
    )
    expect(
        net.capacitance
        == fabrication.EPSILON_0
        * fabrication.RELATIVE_PERMITTIVITY
        * Fraction(1, 4)
        * net.length
        / (1000 * fabrication.DIELECTRIC_THICKNESS),
        "trace capacitance follows the declared parallel-plate lumped model",
    )
    expect(
        net.inductance == net.length / 10 ** 9
        and "declared 1 nH/mm" in net.rule,
        "inductance is the declared per-unit-length constant, not a field solve",
    )
    expect(
        all(
            pad.rect[0] >= log.rules.edge_margin
            and pad.rect[1] >= log.rules.edge_margin
            and pad.rect[2] <= log.width - log.rules.edge_margin
            and pad.rect[3] <= log.height - log.rules.edge_margin
            for item in log.footprints
            for pad in item.pads
        ),
        "every pad lies inside the declared board edge margin",
    )
    expect(
        log.ground_plane[0] == log.rules.edge_margin
        and log.ground_plane[2] == log.width - log.rules.edge_margin,
        "the ground plane is inset by the declared edge margin",
    )

    delta = fabrication.emit_fabrication("delta-sigma")
    expect(
        len(delta.footprints) == 10 and len(delta.traces) == 14
        and len(delta.vias) == 28,
        "the delta-sigma route emits its ten reference parts and routing",
    )
    expect(
        delta.unrouted == ("level", "off", "ref", "thr"),
        "the delta-sigma behavioral control labels are declared unrouted",
    )
    expect(
        check(delta, "Reference coverage").status == "pass"
        and check(delta, "Net routability").status == "pass",
        "the geometry still covers the full reference net list",
    )
    expect(
        footprint(delta, "RIN").dissipation == Fraction(1, 400_000)
        and footprint(delta, "RFB").dissipation == Fraction(1, 100_000),
        "the sampled-data resistor bounds are exact worst-case values",
    )
    expect(
        delta.status == "drc-pass" and delta.passed,
        "the delta-sigma declared geometry passes its own rule set",
    )

    feedback = fabrication.emit_fabrication("sqrt-feedback")
    expect(
        len(feedback.footprints) == 4 and feedback.unrouted == ("out", "ref"),
        "the feedback route declares its ideal-block control labels",
    )
    expect(
        footprint(feedback, "EMULT").row == "quiet"
        and footprint(feedback, "EMULT").dissipation == 0,
        "the multiplier is placed in the quiet row with zero declared dissipation",
    )
    expect(
        all(item.dissipation == 0 for item in feedback.footprints)
        and check(feedback, "Thermal keep-out").value is None,
        "a route without dissipators reports no thermal pair instead of inventing one",
    )
    expect(
        feedback.status == "drc-pass"
        and check(feedback, "Junction temperature").value == 298,
        "the feedback geometry stays at ambient and passes the rule set",
    )

    tight_bus = fabrication.build_fabrication(
        log.physical, fabrication.DRCRules(bus_pitch=Fraction(1, 4))
    )
    expect(
        check(tight_bus, "Copper clearance").status == "gap"
        and not tight_bus.passed
        and tight_bus.status == "drc-gap",
        "a bus pitch below the clearance rule fails the independent DRC",
    )
    hot = fabrication.build_fabrication(
        log.physical, fabrication.DRCRules(thermal_keepout=Fraction(50))
    )
    expect(
        check(hot, "Thermal keep-out").status == "gap",
        "an unreachable thermal keep-out is reported as a gap",
    )
    over_temp = fabrication.build_fabrication(
        log.physical,
        fabrication.DRCRules(max_junction_temperature=Fraction(298)),
    )
    expect(
        check(over_temp, "Junction temperature").status == "gap",
        "a junction limit below the computed rise fails explicitly",
    )
    thin_ring = fabrication.build_fabrication(
        log.physical,
        fabrication.DRCRules(min_annular_ring=Fraction(1, 4)),
    )
    expect(
        check(thin_ring, "Via annular ring").status == "gap",
        "too small a declared annular ring fails explicitly",
    )
    expect(
        raises_code(
            lambda: fabrication.DRCRules(min_clearance=Fraction(0)),
            ErrorCode.DOMAIN_ERROR,
        ),
        "a non-positive clearance rule is rejected",
    )
    expect(
        raises_code(
            lambda: fabrication.DRCRules(min_width=Fraction(1, 2)),
            ErrorCode.DOMAIN_ERROR,
        ),
        "a declared trace narrower than the minimum width is rejected",
    )
    expect(
        raises_code(
            lambda: fabrication.DRCRules(drill=Fraction(1), via_pad=Fraction(1, 2)),
            ErrorCode.DOMAIN_ERROR,
        ),
        "a drill larger than the via pad is rejected",
    )

    payload = log.as_dict()
    expect(
        payload["schema"] == fabrication.SCHEMA
        and payload["units"] == "mm"
        and "not a fabricated" in payload["claim"],
        "the payload states its schema, units and non-fabrication claim",
    )
    expect(
        json.loads(json.dumps(payload))["schema"] == fabrication.SCHEMA,
        "the fabrication payload is JSON serialisable",
    )
    expect(no_floats(payload), "the fabrication payload contains no binary floats")
    expect(
        payload["board"]["width"] == {
            "num": str(log.width.numerator),
            "den": str(log.width.denominator),
        }
        and payload["selected"]["option"] == "precision-20",
        "exact dimensions and the selected option survive the JSON representation",
    )
    expect(
        payload["unrouted_nets"] == ["half"]
        and len(payload["checks"]) == 10
        and payload["passed"] is True,
        "the payload exposes unrouted labels, checks and the overall result",
    )
    expect(
        any("field solve" in gap for gap in payload["gaps"])
        and any("single-node" in gap for gap in payload["gaps"]),
        "the payload keeps its parasitic and thermal model boundaries explicit",
    )
    expect(
        fabrication.build_fabrication(log.physical).as_dict() == payload,
        "the geometry build is deterministic",
    )

    expect(
        raises_code(
            lambda: fabrication.emit_fabrication("sqrt-feedback", max_cost=1),
            ErrorCode.DOMAIN_ERROR,
        ),
        "no geometry is invented when no declared design is selected",
    )
    expect(
        raises_code(
            lambda: fabrication.emit_fabrication("not-a-route"),
            ErrorCode.UNSUPPORTED,
        ),
        "an unknown route has no fabrication emitter",
    )

    cli = subprocess.run(
        [
            sys.executable, "cent", "fabricate", "sqrt-log",
            "--range", "1/2:1", "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == "cent-fabrication/1"
        and cli_payload["fabrication"]["passed"] is True
        and len(cli_payload["fabrication"]["footprints"]) == 6,
        "cent fabricate --json emits the declared geometry payload",
    )
    human = subprocess.run(
        [sys.executable, "cent", "fabricate", "sqrt-feedback"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expect(
        human.returncode == 0
        and "DECLARED FABRICATION GEOMETRY" in human.stdout
        and "not fabricated" in human.stdout
        and "Design-rule checks" in human.stdout
        and "Remaining gaps" in human.stdout,
        "the human renderer shows geometry, checks and remaining gaps",
    )
    missing = subprocess.run(
        [
            sys.executable, "cent", "fabricate", "sqrt-feedback",
            "--max-cost", "1",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expect(
        missing.returncode == 2
        and "no declared design satisfies" in missing.stdout,
        "the CLI refuses to derive geometry without a selected design",
    )
    bad_range = subprocess.run(
        [sys.executable, "cent", "fabricate", "sqrt-log", "--range", "1:2:3"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expect(
        bad_range.returncode == 2 and "--range expects MIN:MAX" in bad_range.stdout,
        "the CLI validates the declared input range",
    )

    total = PASS + FAIL
    print()
    print("=" * 78)
    print(f"DECLARED FABRICATION GEOMETRY: {PASS}/{total} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
