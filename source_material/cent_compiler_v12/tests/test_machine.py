#!/usr/bin/env python3
"""Whole-machine composition side-arm checks.

Run without pytest: ``python3 tests/test_machine.py``.
"""
from __future__ import annotations

import json
import math
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import machine  # noqa: E402

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


def _stage(payload: dict, path: str) -> dict:
    root = (payload.get("tree") or {}).get("root") or {}
    for stage in [root, *machine._flatten(root.get("children") or ())]:
        if stage.get("path") == path:
            return stage
    raise AssertionError(f"missing stage {path}")


def _cli(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "cent"), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def main() -> int:
    print("=" * 78)
    print("WHOLE-MACHINE COMPOSER")
    print("=" * 78)

    payload = machine.build_machine()
    expect(
        payload.get("schema") == machine.MACHINE_SCHEMA
        and payload.get("id") == "sigma-delta-sqrt"
        and payload.get("ok") is True
        and payload.get("status") == "executable-digital-branch",
        "the sigma-delta sqrt machine builds and executes its digital branch",
    )

    tree = payload.get("tree") or {}
    root = tree.get("root") or {}
    root_children = root.get("children") or []
    stages = [root, *machine._flatten(root_children)]
    expect(
        tree.get("schema") == machine.TREE_SCHEMA
        and len(root_children) == 4
        and len(stages) >= 20,
        f"the concept is a four-branch, {len(stages)}-stage function tree",
    )

    coverage = payload.get("coverage") or {}
    expect(
        coverage.get("missing_roles") == []
        and len(coverage.get("required_roles") or ()) == 12
        and len(coverage.get("present_roles") or ()) == 12,
        "every declared surrounding role is present in the tree",
    )
    expect(
        "stages" not in tree
        and all(
            child.get("path") in {"1", "2", "3", "4"}
            for child in root_children
        ),
        "the tree has one canonical child list, without a duplicate stages array",
    )

    selections = payload.get("selections") or {}
    selected = {
        name: (selection.get("selected") or {}).get("mechanism")
        for name, selection in selections.items()
    }
    expect(
        selected
        == {
            "sum": "kcl-conservation",
            "sign": "threshold-comparator",
            "quantized_carry": "delta-sigma-error-feedback",
        }
        and all(selection.get("complete") for selection in selections.values()),
        "core parts are selected from compatible compiler rankings",
    )
    expect(
        (selections["sum"].get("selected") or {}).get("rank") == 2
        and (selections["sign"].get("selected") or {}).get("rank") == 1
        and (selections["quantized_carry"].get("selected") or {}).get("rank") == 1,
        "the selection records the actual compiler rank of each part",
    )

    validation = payload.get("validation") or {}
    metrics = validation.get("metrics") or {}
    checks = validation.get("checks") or []
    expect(
        validation.get("ok") is True
        and all(check.get("status") == "pass" for check in checks)
        and len(checks) == 4,
        "the executable model passes its four declared checks",
    )
    reference = _stage(payload, "1.3")["implementation"]
    expect(
        abs(float(reference.get("input_scale")) - 0.700035713374682) < 1e-15
        and abs(float(reference.get("normalized_input")) - 0.99) < 1e-15
        and abs(
            float(reference.get("reconstruction_scale"))
            - 1.0 / 0.700035713374682
        ) < 1e-12,
        "the reference stage exposes the input scale and reconstruction factor",
    )
    expect(
        validation.get("ntf_fit", {}).get("bins") == 50
        and "20.00 dB/dec" in validation.get("ntf_slope_note", "")
        and "finite-window" in validation.get("ntf_slope_note", ""),
        "the NTF slope is explicitly a finite-window fit, not the asymptotic order",
    )
    expect(
        abs(float(metrics.get("digital_output")) - math.sqrt(2)) <= 1e-4
        and float(metrics.get("inband_noise_suppression_db")) >= 30.0
        and float(metrics.get("ntf_slope_db_per_dec")) >= 20.0,
        "the decimated output, suppression and NTF slope are measured",
    )
    expect(
        "√2" in (payload.get("label") or "")
        and "sqrt(2)" in (payload.get("target") or {}).get("label", "")
        and "no measured device" in payload.get("claim", ""),
        "the payload states the concept and its evidence boundary",
    )

    gaps = " ".join(payload.get("gaps") or ())
    expect(
        "analog" in gaps
        and "clock jitter" in gaps
        and "supply" in gaps
        and "not a fabrication netlist" in gaps,
        "unmodeled physical stages remain explicit gaps",
    )

    rendered = machine.render_machine(payload)
    expect(
        "INPUT & REFERENCE CONDITIONING" in rendered
        and "CORE SIGMA-DELTA MODULATOR LOOP" in rendered
        and "RECONSTRUCTION / DEMODULATION STAGE" in rendered
        and "part: sum -> kcl-conservation" in rendered,
        "the text view shows the complete staged concept and selected parts",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        paths = machine.write_machine(payload, tmpdir)
        names = {path.name for path in paths}
        markdown = (pathlib.Path(tmpdir) / "machine.md").read_text()
        cir = (pathlib.Path(tmpdir) / "machine.cir").read_text()
        document = json.loads((pathlib.Path(tmpdir) / "machine.json").read_text())
        expect(
            names == {"machine.json", "machine.md", "machine.cir"}
            and document.get("schema") == machine.MACHINE_SCHEMA
            and "MACHINE: Y_out(t) ≈ √2" in markdown
            and ".END" in cir
            and "Delta-Sigma modulator" in cir,
            "the bundle writes machine JSON, Markdown and the core .cir",
        )

    listed = _cli("machine", "list")
    expect(
        listed.returncode == 0
        and "CENT MACHINE LIBRARY" in listed.stdout
        and "sigma-delta-sqrt" in listed.stdout,
        "cent machine list names the declared machine",
    )

    cli_payload = _cli("machine", "sigma-delta-sqrt", "--samples", "5000", "--json")
    try:
        cli_document = json.loads(cli_payload.stdout)
    except json.JSONDecodeError:
        cli_document = {}
    expect(
        cli_payload.returncode == 0
        and cli_document.get("schema") == machine.MACHINE_SCHEMA
        and cli_document.get("ok") is True
        and cli_document.get("output_certificate", {}).get("status") == "partial",
        "the CLI emits a machine payload and a partial certificate for the gap boundary",
    )
    expect(
        payload.get("artifacts", {}).get("core_cir", {}).get("active_transient") is False
        and payload.get("artifacts", {}).get("core_cir", {}).get("fabrication") is False,
        "the bundle marks machine.cir as a non-transient, non-fabrication core",
    )

    route = machine.build_machine("sum-kcl", load_domain="mechanical")
    route_root = (route.get("tree") or {}).get("root") or {}
    route_stages = machine._flatten(route_root.get("children") or ())
    expect(
        route.get("schema") == machine.MACHINE_SCHEMA
        and route.get("kind") == "route-wrapper"
        and route.get("ok") is True
        and route.get("load", {}).get("domain") == "mechanical"
        and route.get("load", {}).get("transducer")
        and route.get("load", {}).get("scale_note")
        and all(
            isinstance(value, str)
            for value in (route.get("load", {}).get("unit_scale_matrix") or {}).values()
        )
        and any(stage.get("kind") == "load-transducer" for stage in route_stages),
        "an assembled route is wrapped in the four-stage template with a TIER 3 load",
    )
    expect(
        (route.get("selections", {}).get("sum", {}).get("selected") or {}).get("mechanism")
        == "kcl-conservation"
        and route.get("coverage", {}).get("missing_roles") == [],
        "the route wrapper queries and records compiler selections for its primitives",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        paths = machine.write_machine(route, tmpdir)
        route_cir = (pathlib.Path(tmpdir) / "machine.cir").read_text()
        expect(
            {path.name for path in paths} == {"machine.json", "machine.md", "machine.cir"}
            and "No route-specific electrical netlist emitter" in route_cir
            and "declared gap" in route_cir,
            "a route wrapper writes a comment-only .cir instead of a false netlist",
        )

    library = machine.library_payload()
    expect(
        len(library.get("machines") or ()) == 1 + len(machine.ROUTE_MACHINE_IDS)
        and set(library.get("load_domains") or ()) == set(machine.LOAD_DOMAINS),
        "the library exposes the hand-authored machine, route wrappers and load domains",
    )

    route_cli = _cli("machine", "sum-kcl", "--load", "fluid", "--json")
    try:
        route_document = json.loads(route_cli.stdout)
    except json.JSONDecodeError:
        route_document = {}
    expect(
        route_cli.returncode == 0
        and route_document.get("kind") == "route-wrapper"
        and route_document.get("load", {}).get("domain") == "fluidics"
        and route_document.get("load", {}).get("transducer"),
        "the CLI exposes the route-wrapper and --load mechanical/fluid paths",
    )

    unknown = _cli("machine", "not-a-machine")
    expect(
        unknown.returncode == 2
        and "unknown machine" in unknown.stderr,
        "an unknown machine fails explicitly",
    )

    print("\n" + "=" * 78)
    if FAIL:
        print(f"MACHINE COMPOSER: {PASS}/{PASS + FAIL} checks passed, {FAIL} failed")
        return 1
    print(f"MACHINE COMPOSER: {PASS}/{PASS + FAIL} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
