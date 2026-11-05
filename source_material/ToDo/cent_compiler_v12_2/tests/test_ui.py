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
from cent_compiler.interval import Interval  # noqa: E402
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
    expect(bool(report.netlist) and "sqrt" in report.netlist.lower(), "netlist")
    expect(set(report.inputs) == {"energy", "mass"}, f"inputs: {report.inputs}")
    expect(report.program is not None, f"program notes: {report.notes}")


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
