#!/usr/bin/env python3
"""Focused tests for topology-derived reference netlists and floorplans.

Run without pytest: ``python3 tests/test_physical.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import physical  # noqa: E402
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


def part(plan: physical.PhysicalPlan, ref: str) -> physical.PhysicalPart:
    return next(item for item in plan.parts if item.ref == ref)


def main() -> int:
    print("=" * 78)
    print("REFERENCE NETLIST AND FLOORPLAN")
    print("=" * 78)

    delta = physical.emit_physical("delta-sigma")
    expect(
        delta.route_key == "delta-sigma"
        and delta.route_id == "delta-sigma-first-order",
        "the delta-sigma route is emitted under its declared route id",
    )
    expect(
        delta.selected is not None
        and delta.selected.option.name == "offset-1/200",
        "the default selected delta-sigma option is retained",
    )
    expect(
        len(delta.parts) == 10 and len({item.ref for item in delta.parts}) == 10,
        "the delta-sigma reference has ten uniquely referenced parts",
    )
    expect(
        part(delta, "VIN").value == Fraction(1, 2),
        "the input source uses the exact declared operating point",
    )
    expect(
        part(delta, "RIN").value == Fraction(100_000)
        and part(delta, "CINT").value == Fraction(1, 1_000_000_000),
        "the integrator parts carry the exact binding quantities",
    )
    expect(
        part(delta, "VOFF").value == Fraction(1, 200),
        "the comparator offset is copied exactly from the selected binding",
    )
    expect(
        part(delta, "EINT").value == physical.IDEAL_OPAMP_GAIN
        and "ideal" in part(delta, "EINT").note,
        "the ideal integrator gain is explicitly labelled, not passed off as a device quantity",
    )
    expect(
        "V(int)" in (part(delta, "BQ").expression or "")
        and "V(thr)" in (part(delta, "BQ").expression or "")
        and "V(off)" in (part(delta, "BQ").expression or ""),
        "the comparator expression references the derived threshold and offset nets",
    )
    expect(
        any(net.name == "sum" and len(net.connections) == 4 for net in delta.nets),
        "the summing junction net connects all four integrator/feedback pins",
    )
    expect(
        "NOT A FABRICATION NETLIST" in delta.spice
        and ".END" in delta.spice
        and "RIN in sum 100000" in delta.spice,
        "the SPICE deck is marked as non-fabrication and carries the exact-value representation",
    )
    expect(
        len(delta.layout.blocks) == 4
        and [block.stage for block in delta.layout.blocks]
        == ["input", "integrator", "quantizer", "feedback"],
        "the delta-sigma floorplan exposes the four declared stages",
    )
    expect(
        {ref for block in delta.layout.blocks for ref in block.parts}
        == {item.ref for item in delta.parts},
        "every delta-sigma part is assigned to a floorplan stage",
    )
    expect(
        all(
            left.x + left.width <= right.x
            for index, left in enumerate(delta.layout.blocks)
            for right in delta.layout.blocks[index + 1 :]
        ),
        "schematic stage rectangles do not overlap",
    )
    expect(
        "not mm" in delta.layout.coordinate_unit
        and any("DRC" in gap for gap in delta.layout.gaps),
        "the floorplan states its schematic units and missing DRC boundary",
    )
    expect(
        [check.status for check in delta.checks] == [
            "pass", "pass", "pass", "pass", "pass", "pass", "gap"
        ],
        "all reference checks pass while fabrication remains an explicit gap",
    )
    expect(
        "has not been simulator-validated" in next(
            check.detail for check in delta.checks if check.name == "SPICE emission"
        ),
        "the SPICE check does not claim a simulation",
    )

    log = physical.emit_physical("sqrt-log", input_min=Fraction(1, 2), input_max=Fraction(1))
    expect(
        log.selected is not None
        and log.selected.option.name == "precision-20",
        "the range-safe log-domain precision is retained in the reference plan",
    )
    expect(
        part(log, "RIN").value == 1000
        and part(log, "BLOG").kind == "behavioral-current"
        and part(log, "BLOG").nodes == ("log", "0"),
        "the log route puts an exponential junction at the declared input net",
    )
    expect(
        part(log, "BLOG").parameters.get("I_s") == Fraction(1, 1_000_000_000)
        and part(log, "BLOG").parameters.get("V_T") is not None,
        "the junction block keeps the exact saturation current and thermal voltage",
    )
    expect(
        part(log, "EDIV").value == Fraction(1, 2)
        and part(log, "BANTI").nodes == ("0", "out"),
        "the half-gain and antilog stages preserve their declared direction",
    )
    expect(
        any(
            link.net == "log" and link.from_stage == "logger"
            and link.to_stage == "half_gain"
            for link in log.layout.links
        ),
        "the log signal link follows the declared stage order",
    )

    feedback = physical.emit_physical("sqrt-feedback")
    expect(
        feedback.selected is not None
        and feedback.selected.option.name == "gain-1000000",
        "the default feedback design is retained",
    )
    expect(
        part(feedback, "VIN").value == 2
        and part(feedback, "VREF").value == 1,
        "the feedback input and reference sources carry exact binding values",
    )
    expect(
        part(feedback, "EOUT").value == 1_000_000,
        "the error amplifier carries the selected finite gain",
    )
    expect(
        part(feedback, "EMULT").parameters.get("k") == 1
        and "V(out)*V(out)/V(ref)" in (part(feedback, "EMULT").expression or ""),
        "the multiplier feedback expression exposes its declared law",
    )
    expect(
        [block.stage for block in feedback.layout.blocks]
        == ["input", "error_amp", "multiplier"],
        "the feedback floorplan follows signal flow rather than source declaration order",
    )

    payload = delta.as_dict()
    expect(
        json.loads(json.dumps(payload))["schema"] == physical.SCHEMA,
        "the physical payload is JSON serialisable",
    )
    expect(no_floats(payload), "the physical payload contains no binary floats")
    expect(
        payload["parts"][0]["value"] == {"num": "1", "den": "2"},
        "exact rational values survive the JSON representation as numerator/denominator pairs",
    )

    expect(
        raises_code(
            lambda: physical.emit_physical("sqrt-feedback", max_cost=1),
            ErrorCode.DOMAIN_ERROR,
        ),
        "no reference artifacts are invented when no declared design is selected",
    )
    expect(
        raises_code(
            lambda: physical.build_physical(
                solve_route("sqrt-feedback", max_cost=Fraction(1))
            ),
            ErrorCode.DOMAIN_ERROR,
        ),
        "build_physical refuses a design with no selected binding",
    )
    expect(
        raises_code(
            lambda: physical.emit_physical("not-a-route"),
            ErrorCode.UNSUPPORTED,
        ),
        "an unknown route has no physical emitter",
    )

    cli = subprocess.run(
        [sys.executable, "cent", "physical", "sqrt-log", "--range", "1/2:1", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == "cent-physical/1"
        and cli_payload["physical"]["selected"]["option"] == "precision-20",
        "cent physical --json emits the selected reference plan",
    )
    expect(
        len(cli_payload.get("physical", {}).get("parts", [])) == 6,
        "the CLI payload carries the full log-domain part list",
    )
    human = subprocess.run(
        [sys.executable, "cent", "physical", "sqrt-feedback"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expect(
        human.returncode == 0
        and "REFERENCE NETLIST AND FLOORPLAN" in human.stdout
        and "NOT A FABRICATION NETLIST" in human.stdout
        and "Schematic floorplan" in human.stdout,
        "the human renderer shows the netlist and schematic floorplan boundary",
    )
    missing = subprocess.run(
        [sys.executable, "cent", "physical", "sqrt-feedback", "--max-cost", "1"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expect(
        missing.returncode == 2 and "no physical reference" in missing.stdout,
        "the CLI refuses to emit when the design constraints have no solution",
    )

    total = PASS + FAIL
    print()
    print("=" * 78)
    print(f"REFERENCE NETLIST AND FLOORPLAN: {PASS}/{total} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
