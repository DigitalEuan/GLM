"""Console UI for the £ → ¢ → ∆ pipeline.

Given a target relation (the £), this module builds one report containing:

* the ¢ DAG the formula decomposes into, and the primitive census;
* every ∆ implementation, with the top few ranked by ¢_cost;
* the structurally matched SPICE netlist, or an explicit template gap;
* an exact-core program when the DAG maps onto the evaluator's vocabulary.

The same report can be written as a self-contained *material bundle*
(``cent-material/1``): a JSON document holding the DAG, the exact program, its
initial bindings, the SPICE netlist and the notes, plus the ``.cir`` and a text
report.  Nothing is written unless you ask for it, and no path is absolute.

This module is deliberately UI-only: it renders what the pipeline reports and
never substitutes a result for an error.  When a formula cannot be expressed as
an exact program (an unsupported primitive, or a parameter a £ cannot supply),
the report says so in its notes and leaves the program empty.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .cost_function import rank_and_prune
from .evaluator import Evaluator
from .exact import CentError, ErrorCode, format_q, q_to_json
from .grammar import CGraph, COp, decompose_formula, preprocess_formula
from .hypothesis_bridge import LAYERS, escalate
from .interval import Interval
from .port import PhysicalPort
from .program import (
    Instruction,
    Program,
    analyse,
    decode_exact,
    program_from_dict,
)
from .output_certificate import attach_certificate
from .spice_emitter import (
    SpiceTemplateMatch,
    generate_spice_netlist,
    select_spice_template,
)
from .substrate_library import enumerate_delta
from .vocabulary import ATOMIC_PRIMITIVES, COMPOSITE_PRIMITIVES, NUMERIC

MATERIAL_SCHEMA = "cent-material/1"
COMPILE_SCHEMA = "cent-compile/1"
CONST_PREFIX = "const:"

#: Reference values for the existing electrical fidelity model.  These are
#: screening defaults, not datasheet or measured device values.  Non-electrical
#: candidates do not inherit Johnson/shot-noise checks they cannot justify.
REFERENCE_FIDELITY_PARAMS: dict[str, Any] = {
    "v_in_range": [0, 10],
    "opamp_gain": 1e5,
    "bandwidth_hz": 1e6,
    "temperature": 300,
    "resistance": 1000,
    "signal_level": 1.0,
    "current": 1e-3,
    "component_tolerance": 0.01,
    "n_components": 3,
}


def fidelity_trace(impl: Any) -> dict[str, Any]:
    """Run or explicitly gap the five-layer cascade for one ∆ candidate.

    The existing layer model is electrical.  Applying its Johnson-noise and
    shot-noise checks to a mechanical or fluidic candidate would be a category
    error, so those domains keep all five layer slots with explicit gaps.
    """
    domain = str(impl.substrate_domain)
    component = ", ".join(impl.components[:2]) or "(no component)"
    if domain != "electrical":
        layers = [{
            "layer": LAYERS[0].name,
            "status": "pass",
            "detail": "declared proposal; ideal operator model only",
        }]
        for layer in LAYERS[1:]:
            layers.append({
                "layer": layer.name,
                "status": "gap",
                "detail": f"no declared {layer.name} model for the {domain} domain",
            })
        return {
            "component": component,
            "domain": domain,
            "profile": "domain-aware; no cross-domain noise model borrowed",
            "direction": "not escalated",
            "converged": False,
            "flip_layer": None,
            "layers": layers,
        }

    params = {
        **REFERENCE_FIDELITY_PARAMS,
        "n_components": max(1, len(impl.components)),
        "carrier": impl.carrier_type,
        "is_delta_sigma": bool(impl.is_delta_sigma),
    }
    arrow = escalate(params)
    layers = [
        {
            "layer": name,
            "status": "pass" if passed else "gap",
            "detail": detail,
        }
        for name, passed, detail in arrow.reads
    ]
    return {
        "component": component,
        "domain": domain,
        "profile": "reference electrical screening defaults; not datasheet or measured values",
        "direction": arrow.direction,
        "converged": arrow.converged,
        "flip_layer": arrow.flip_layer,
        "layers": layers,
    }


def render_fidelity_trace(fidelity: Iterable[Mapping[str, Any]]) -> list[str]:
    """Render the layer trace shared by the CLI and the report renderer."""
    lines = ["   Fidelity trace (reference profile; not device values):"]
    items = list(fidelity)
    if not items:
        lines.append("     (no ranked candidate to escalate)")
        return lines
    for item in items:
        lines.append(
            f"     {item['component']} [{item['domain']}]: {item['direction']}"
        )
        for layer in item["layers"]:
            lines.append(
                f"       [{layer['status']:<4}] {layer['layer']}: {layer['detail']}"
            )
    return lines


def proposal_boundary() -> dict[str, Any]:
    """The limitation carried by every compile proposal."""
    return {
        "status": "not-fabricated",
        "claim": "This is a declared ∆ proposal, not a fabricated or measured device.",
        "missing_evidence": [
            "fabricated and measured device",
            "manufacturing sign-off",
        ],
    }

HELP = """\
Commands
  <relation>      compile a £, e.g.  velocity = (2 * energy / mass)^(1/2)
  :top N          show the top N ∆ implementations (default 6)
  :save [dir]     save the last report's material to dir (default cent_out)
  :nosave         stop auto-saving after each report
  :help           show this help
  :quit           leave
"""


# ---------------------------------------------------------------------------
# relation parsing and reporting
# ---------------------------------------------------------------------------

def split_relation(text: str) -> tuple[str, str]:
    """Split ``target = expression`` and tolerate a leading ``£`` marker."""
    cleaned = text.strip()
    if cleaned.startswith("£"):
        cleaned = cleaned[1:].lstrip()
        if cleaned.startswith(":"):
            cleaned = cleaned[1:].lstrip()
    if "=" in cleaned:
        target, expression = cleaned.split("=", 1)
        target = target.strip() or "result"
    else:
        target, expression = "result", cleaned
    expression = expression.strip()
    if not expression:
        raise CentError(ErrorCode.INVALID_INPUT, "the £ needs a right-hand side")
    return target, expression


def select_template(dag: CGraph) -> SpiceTemplateMatch:
    """Return a structural SPICE-template decision for the whole DAG."""
    return select_spice_template(dag)


def program_from_dag(dag: CGraph, name: str = "relation") -> tuple[Program | None, dict[str, Fraction], list[str]]:
    """Map a ¢ DAG onto an exact-core :class:`Program`.

    Returns ``(program, bindings, notes)``.  ``bindings`` supplies the synthetic
    ``_one`` wire used to materialise numeric literals.  A primitive the exact
    core cannot run — or one whose parameters a £ cannot supply — yields
    ``(None, {}, notes)`` rather than a guessed program.
    """
    notes: list[str] = []
    bindings: dict[str, Fraction] = {}
    const_wires: dict[Fraction, str] = {}
    instructions: list[Instruction] = []

    def wire_for_const(token: str) -> str:
        value = Fraction(token.split(":", 1)[1])
        if value not in const_wires:
            if "_one" not in bindings:
                bindings["_one"] = Fraction(1)
            wire = f"_k{len(const_wires) + 1}"
            const_wires[value] = wire
            instructions.append(
                Instruction("scale", ("_one",), wire, {"factor": value})
            )
        return const_wires[value]

    for op in dag.ops:
        inputs: list[str] = []
        for token in op.inputs:
            inputs.append(wire_for_const(token) if token.startswith(CONST_PREFIX) else token)

        params: dict[str, Any] = {}
        if op.op == "scale":
            if op.const is None:
                notes.append(f"{op.output}: ¢_scale has no factor")
                return None, {}, notes
            params["factor"] = op.const

        try:
            analysis_kinds = None
            candidate = Instruction(op.op, tuple(inputs), op.output, params)
            # Validate the single instruction in an empty program: this checks
            # the primitive name, arity, required parameters and input kinds.
            probe = Program(
                name,
                {wire: NUMERIC for wire in set(inputs)},
                (candidate,),
                {op.output: op.output},
            )
            analyse(probe)
        except CentError as exc:
            notes.append(f"{op.output}: {exc.message}")
            return None, {}, notes

        instructions.append(candidate)

    program = Program(
        name,
        {wire: NUMERIC for wire in sorted(dag.inputs)} | (
            {"_one": NUMERIC} if "_one" in bindings else {}
        ),
        tuple(instructions),
        {wire: wire for wire in sorted(dag.outputs)},
    )
    try:
        analyse(program)
    except CentError as exc:
        notes.append(f"program rejected: {exc.message}")
        return None, {}, notes
    return program, bindings, notes


@dataclass(frozen=True)
class Report:
    """Everything the UI shows for one £."""

    relation: str
    target: str
    expression: str
    ops: tuple[COp, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    primitive_counts: Mapping[str, int]
    atomic_count: int
    composite_count: int
    impl_count: int
    delta_sigma_count: int
    top: tuple[tuple[Any, Any], ...]
    template: str | None
    template_status: str
    template_detail: str
    template_decision: Mapping[str, Any]
    netlist: str | None
    program: Program | None
    bindings: Mapping[str, Fraction]
    notes: tuple[str, ...]
    fidelity: tuple[dict[str, Any], ...] = ()

    # -- serialisation ----------------------------------------------------
    def material(self) -> dict[str, Any]:
        """A self-contained, JSON-serialisable material bundle."""
        return attach_certificate({
            "schema": MATERIAL_SCHEMA,
            "relation": self.relation,
            "target": self.target,
            "expression": self.expression,
            "dag": {
                "inputs": list(self.inputs),
                "outputs": list(self.outputs),
                "ops": [
                    {
                        "op": op.op,
                        "inputs": list(op.inputs),
                        "output": op.output,
                        "const": None if op.const is None else q_to_json(op.const),
                    }
                    for op in self.ops
                ],
            },
            "summary": {
                "primitives": dict(self.primitive_counts),
                "atomic": self.atomic_count,
                "composite": self.composite_count,
                "implementations": self.impl_count,
                "delta_sigma": self.delta_sigma_count,
            },
            "program": None if self.program is None else self.program.as_dict(),
            "bindings": {wire: q_to_json(value) for wire, value in self.bindings.items()},
            "spice": {
                "template": self.template,
                "status": self.template_status,
                "detail": self.template_detail,
                "decision": dict(self.template_decision),
                "netlist": self.netlist,
            },
            "fidelity": list(self.fidelity),
            "notes": list(self.notes),
        })


def compile_payload(relation: str, top_n: int = 6) -> dict[str, Any]:
    """Return the tooling view of one £ compile.

    This wraps :func:`build_report`; it is not a second solver.  Each proposal
    carries its domain, carrier, components and the declared six-axis cost
    breakdown so a rank can be audited without parsing the text view.
    """
    report = build_report(relation, top_n=top_n)
    proposals = [
        {
            "rank": index,
            "domain": impl.substrate_domain,
            "carrier": impl.carrier_type,
            "delta_sigma": bool(impl.is_delta_sigma),
            "components": list(impl.components),
            "boundary": proposal_boundary(),
            "cost": {
                "total": cost.total,
                "component_count": cost.component_count_score,
                "domain_consistency": cost.domain_consistency_score,
                "carrier_consistency": cost.carrier_consistency_score,
                "implementation": cost.implementation_cost_score,
                "precision": cost.precision_score,
                "speed": cost.speed_score,
            },
        }
        for index, (impl, cost) in enumerate(report.top, 1)
    ]
    return {
        "ok": bool(report.impl_count and report.top),
        "schema": COMPILE_SCHEMA,
        "relation": report.relation,
        "target": report.target,
        "expression": report.expression,
        "dag": [
            {
                "op": op.op,
                "inputs": list(op.inputs),
                "output": op.output,
                "const": None if op.const is None else q_to_json(op.const),
            }
            for op in report.ops
        ],
        "summary": {
            "primitives": dict(report.primitive_counts),
            "atomic": report.atomic_count,
            "composite": report.composite_count,
            "implementations": report.impl_count,
            "delta_sigma": report.delta_sigma_count,
        },
        "proposals": proposals,
        "boundary": proposal_boundary(),
        "spice": {
            "template": report.template,
            "status": report.template_status,
            "detail": report.template_detail,
            "decision": dict(report.template_decision),
            "netlist": report.netlist,
        },
        "fidelity": list(report.fidelity),
        "notes": list(report.notes),
    }


def build_report(relation: str, top_n: int = 6) -> Report:
    """Run the pipeline for one £ and collect everything the UI shows."""
    target, expression = split_relation(relation)
    expr = preprocess_formula(expression)
    dag = decompose_formula(expr, target)

    notes: list[str] = []
    try:
        implementations = enumerate_delta(dag)
    except Exception as exc:  # noqa: BLE001 - reported, never hidden
        notes.append(f"∆ enumeration failed: {exc}")
        implementations = []
    try:
        top = tuple(rank_and_prune(implementations, top_n=top_n)) if implementations else ()
    except Exception as exc:  # noqa: BLE001
        notes.append(f"∆ ranking failed: {exc}")
        top = ()

    template_match = select_template(dag)
    template = template_match.template
    netlist = generate_spice_netlist(template) if template else None
    if template_match.status != "match":
        notes.append(template_match.detail)
    program, bindings, program_notes = program_from_dag(dag, name=target)
    notes.extend(program_notes)

    counts = Counter(op.op for op in dag.ops)
    fidelity = tuple(fidelity_trace(impl) for impl, _ in top)
    return Report(
        relation=relation.strip(),
        target=target,
        expression=expression,
        ops=tuple(dag.ops),
        inputs=tuple(sorted(dag.inputs)),
        outputs=tuple(sorted(dag.outputs)),
        primitive_counts=dict(counts),
        atomic_count=sum(n for op, n in counts.items() if op in ATOMIC_PRIMITIVES),
        composite_count=sum(n for op, n in counts.items() if op in COMPOSITE_PRIMITIVES),
        impl_count=len(implementations),
        delta_sigma_count=sum(1 for impl in implementations if impl.is_delta_sigma),
        top=top,
        template=template,
        template_status=template_match.status,
        template_detail=template_match.detail,
        template_decision={
            "structural": template_match.structural,
            "basis": template_match.selection_basis,
            "proposal_effect": template_match.proposal_effect,
        },
        netlist=netlist,
        program=program,
        bindings=bindings,
        notes=tuple(notes),
        fidelity=fidelity,
    )


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def format_value(value: Any) -> str:
    """Human-readable exact wire value."""
    if isinstance(value, Interval):
        lo, hi = format_q(value.lo), format_q(value.hi)
        return f"[{lo}, {hi}]" if lo != hi else f"[{lo}]"
    if isinstance(value, PhysicalPort):
        return f"port(e={format_q(value.effort)}, f={format_q(value.flow)})"
    if isinstance(value, Fraction):
        return format_q(value)
    if isinstance(value, tuple):
        return "(" + ", ".join(format_value(v) for v in value) + ")"
    return str(value)


def render_report(report: Report) -> str:
    """Render the report as terminal text."""
    lines = ["=" * 78, f"£  {report.relation}", "=" * 78, ""]

    lines.append(f"1. ¢ DAG — {len(report.ops)} primitive(s)")
    for op in report.ops:
        const = f"  [factor {format_q(op.const)}]" if op.const is not None else ""
        lines.append(f"   {op.output:<14} = {op.op}({', '.join(op.inputs)}){const}")
    if not report.ops:
        lines.append("   (the expression is a bare input)")

    counts = ", ".join(f"{name} x{n}" for name, n in sorted(report.primitive_counts.items()))
    lines.append("")
    lines.append("2. ¢ primitives")
    lines.append(f"   {counts or '(none)'}")
    lines.append(f"   atomic: {report.atomic_count}   composite: {report.composite_count}")

    lines.append("")
    lines.append("3. ∆ implementations")
    lines.append(f"   {report.impl_count} total, {report.delta_sigma_count} delta-sigma")

    lines.append("")
    lines.append("4. Top ∆ by ¢_cost")
    if report.top:
        lines.append(
            f"   {'#':<4}{'cost':<6}{'domain':<14}{'carrier':<12}{'∆Σ':<5}components"
        )
        for index, (impl, cost) in enumerate(report.top, 1):
            components = ", ".join(impl.components)
            if len(components) > 38:
                components = components[:35] + "..."
            flag = "YES" if impl.is_delta_sigma else "no"
            lines.append(
                f"   {index:<4}{cost.total:<6}{impl.substrate_domain:<14}"
                f"{impl.carrier_type:<12}{flag:<5}{components}"
            )
    else:
        lines.append("   (no ranked implementations)")

    lines.append("")
    lines.extend(render_fidelity_trace(report.fidelity))

    lines.append("")
    lines.append("5. Generated material")
    if report.template and report.netlist:
        lines.append(
            f"   SPICE: {report.template} ({len(report.netlist.splitlines())} lines)"
        )
    else:
        lines.append("   SPICE: no structural template; see Notes for the gap")
    lines.append(
        "   Template decision is structural; it does not filter ∆ proposals."
    )
    if report.program is not None:
        lines.append(
            f"   Exact program: {len(report.program.instructions)} instruction(s), "
            f"inputs: {', '.join(sorted(report.program.inputs)) or '(none)'}, "
            f"outputs: {', '.join(sorted(report.program.outputs))}"
        )
    else:
        lines.append("   Exact program: unavailable (see notes)")
    lines.append('   Save with:  cent report "<£>" --save cent_out')

    if report.notes:
        lines.append("")
        lines.append("6. Notes")
        for note in report.notes:
            lines.append(f"   - {note}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# material bundles
# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", text.strip()).strip("._")
    return cleaned or "relation"


def save_material(report: Report, directory: str | Path = "cent_out") -> tuple[Path, ...]:
    """Write ``<slug>.material.json``, ``<slug>.<template>.cir`` and ``.report.txt``."""
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    slug = _slug(report.target)
    written: list[Path] = []

    material_path = out / f"{slug}.material.json"
    material_path.write_text(
        json.dumps(report.material(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    written.append(material_path)

    if report.netlist and report.template:
        netlist_path = out / f"{slug}.{report.template}.cir"
        netlist_path.write_text(report.netlist, encoding="utf-8")
        written.append(netlist_path)

    report_path = out / f"{slug}.report.txt"
    report_path.write_text(render_report(report), encoding="utf-8")
    written.append(report_path)
    return tuple(written)


def load_material(path: str | Path) -> dict[str, Any]:
    """Load a material bundle or a bare exact program."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CentError(ErrorCode.VALIDATION_ERROR, "material file is not a JSON object")
    if data.get("schema") == MATERIAL_SCHEMA:
        return data
    if data.get("schema") == "cent-program/1":
        return {"schema": MATERIAL_SCHEMA, "program": data, "bindings": {}}
    raise CentError(
        ErrorCode.VALIDATION_ERROR,
        f"{path}: expected schema {MATERIAL_SCHEMA!r} or 'cent-program/1'",
    )


def run_material(
    material: Mapping[str, Any],
    *,
    ticks: int = 1,
    overrides: Mapping[str, Any] | None = None,
    seed: int = 0,
) -> tuple[dict[str, Any], ...]:
    """Evaluate the exact program inside a material bundle."""
    if not material.get("program"):
        raise CentError(
            ErrorCode.UNSUPPORTED,
            "this material has no exact program; see its notes for why",
        )
    program = program_from_dict(material["program"])
    feed: dict[str, Any] = {
        str(wire): decode_exact(value)
        for wire, value in dict(material.get("bindings", {})).items()
    }
    feed.update(overrides or {})

    for wire, kind in program.inputs.items():
        if wire in feed:
            continue
        if kind == NUMERIC:
            feed[wire] = Fraction(0)
        else:
            raise CentError(
                ErrorCode.INVALID_INPUT,
                f"input {wire!r} of kind {kind!r} needs an explicit --set value",
            )
    if ticks < 1:
        raise CentError(ErrorCode.INVALID_INPUT, "ticks must be at least 1")
    return Evaluator(program, seed=seed).run([dict(feed) for _ in range(int(ticks))])


# ---------------------------------------------------------------------------
# interactive shell
# ---------------------------------------------------------------------------

class Shell:
    """A small line-oriented console: type a £, read the report."""

    def __init__(
        self,
        *,
        out: Callable[[str], None] = print,
        top_n: int = 6,
        save_dir: str | None = None,
    ):
        self.out = out
        self.top_n = int(top_n)
        self.save_dir = save_dir
        self.last: Report | None = None

    def run(self, inp: Callable[[str], str] = input) -> int:
        self.out("cent ui — enter a £ (target relation). :help for commands, :quit to leave.")
        while True:
            try:
                line = inp("£ > ")
            except (EOFError, KeyboardInterrupt):
                self.out("")
                return 0
            text = line.strip()
            if not text:
                continue
            if text in {":q", ":quit", "quit", "exit"}:
                return 0
            if text in {":h", ":help", "help"}:
                self.out(HELP)
                continue
            if text.startswith(":top"):
                raw = text[4:].strip()
                try:
                    self.top_n = max(1, int(raw))
                except ValueError:
                    self.out(f"error: :top needs an integer, got {raw!r}")
                    continue
                self.out(f"top N = {self.top_n}")
                continue
            if text.startswith(":nosave"):
                self.save_dir = None
                self.out("auto-save off")
                continue
            if text.startswith(":save"):
                raw = text[5:].strip()
                self.save_dir = raw or self.save_dir or "cent_out"
                if self.last is None:
                    self.out(f"auto-save on: {self.save_dir} (no report yet)")
                else:
                    for path in save_material(self.last, self.save_dir):
                        self.out(f"wrote {path}")
                continue

            try:
                report = build_report(text, top_n=self.top_n)
            except Exception as exc:  # noqa: BLE001 - the UI reports, never hides
                self.out(f"error: {exc}")
                continue
            self.last = report
            self.out(render_report(report))
            if self.save_dir:
                for path in save_material(report, self.save_dir):
                    self.out(f"wrote {path}")
