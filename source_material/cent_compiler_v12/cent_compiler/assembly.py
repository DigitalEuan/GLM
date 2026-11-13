"""Typed component contracts and exact route assembly.

This module is the first assembly layer above method discovery.  It does not
invent a fabrication netlist: it generates a checked exact-core ``Program`` from
declared component contracts, runs that program on exact rationals, and states
the remaining physical gaps.

The initial route is a first-order delta-sigma loop:

    error      = x - feedback
    integrator = accum(error)
    level      = quantize(integrator, quantum)
    feedback   = delay(level, 1)

``accum``, ``quantize`` and ``delay`` carry typed ports, laws, parameters and
declared material mappings.  ``sum`` and ``neg`` are exact arithmetic glue, not
claims about a separate physical device.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from .exact import CentError, ErrorCode, Q, q, q_to_json
from .evaluator import run_program
from .interval import Interval, exp_q, log_q, sqrt_q
from .program import Instruction, Program, analyse
from .vocabulary import NUMERIC
from .typed_graph import typed_graph

SCHEMA = "cent-route/1"
COMPONENT_CONTRACT_SCHEMA = "cent-component-contract/1"


def _json(value: Any) -> Any:
    """Encode exact rationals and certified intervals for the public payload."""
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Interval):
        return {
            "lo": _json(value.lo),
            "hi": _json(value.hi),
            "width": _json(value.width),
        }
    if isinstance(value, Mapping):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(v) for v in value]
    return value


def _as_fraction(value: Any, name: str) -> Q:
    # ``q`` accepts exact decimal strings; route users naturally write "1/2".
    if isinstance(value, str) and "/" in value:
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError) as exc:
            raise CentError(
                ErrorCode.INVALID_INPUT,
                f"{name}: not an exact fraction: {value!r}",
            ) from exc
    try:
        return q(value, name)
    except CentError:
        raise
    except (TypeError, ValueError) as exc:  # pragma: no cover - q normalises this
        raise CentError(ErrorCode.TYPE_ERROR, f"{name}: expected an exact rational") from exc


@dataclass(frozen=True)
class PortSpec:
    """A typed route or component port."""

    name: str
    direction: str
    kind: str
    domain: str
    description: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "direction": self.direction,
            "kind": self.kind,
            "domain": self.domain,
            "description": self.description,
        }


@dataclass(frozen=True)
class ParameterSpec:
    """A declared component parameter."""

    name: str
    kind: str
    domain: str
    default: Any
    description: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "domain": self.domain,
            "default": _json(self.default),
            "description": self.description,
        }


@dataclass(frozen=True)
class ComponentContract:
    """A typed physical ingredient, with its law and declared material."""

    op: str
    name: str
    ports: tuple[PortSpec, ...]
    parameters: tuple[ParameterSpec, ...]
    law: str
    state: str
    operating_range: str
    material: str
    domain: str
    carrier: str
    failure_modes: tuple[str, ...]
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": COMPONENT_CONTRACT_SCHEMA,
            "op": self.op,
            "name": self.name,
            "ports": [port.as_dict() for port in self.ports],
            "parameters": [parameter.as_dict() for parameter in self.parameters],
            "law": self.law,
            "state": self.state,
            "operating_range": self.operating_range,
            "material": self.material,
            "domain": self.domain,
            "carrier": self.carrier,
            "failure_modes": list(self.failure_modes),
            "source": self.source,
        }


ACCUM_CONTRACT = ComponentContract(
    op="accum",
    name="Exact temporal integrator",
    ports=(
        PortSpec("x", "input", "numeric", "exact rational", "increment added this tick"),
        PortSpec("y", "output", "numeric", "exact rational", "running sum"),
    ),
    parameters=(),
    law="y_t = y_{t-1} + x_t; y_0 = 0",
    state="one exact rational accumulator",
    operating_range="any exact rational; the route bounds the peak separately",
    material="capacitor integrator (switched-capacitor or op-amp)",
    domain="electrical",
    carrier="temporal",
    failure_modes=("capacitor leakage", "op-amp offset and finite gain", "clock feedthrough"),
    source="DELTA_SUBSTRATE: accum / capacitor",
)

QUANTIZE_CONTRACT = ComponentContract(
    op="quantize",
    name="Uniform nearest-level quantizer",
    ports=(
        PortSpec("signal", "input", "numeric", "exact rational", "value to quantize"),
        PortSpec(
            "level",
            "output",
            "numeric",
            "exact multiple of quantum",
            "nearest declared level",
        ),
    ),
    parameters=(
        ParameterSpec(
            "quantum",
            "rational",
            "quantum > 0",
            Fraction(1),
            "distance between adjacent output levels",
        ),
        ParameterSpec(
            "full_scale",
            "rational",
            "full_scale >= quantum",
            Fraction(1),
            "largest declared output level",
        ),
    ),
    law=(
        "level = clamp(quantum * round(signal / quantum), 0, full_scale), "
        "ties away from zero"
    ),
    state="none",
    operating_range=(
        "quantum > 0 and full_scale >= quantum; the flash ADC saturates at "
        "its reference rails"
    ),
    material="flash ADC / comparator bank",
    domain="electrical",
    carrier="temporal",
    failure_modes=(
        "comparator offset",
        "metastability near a threshold",
        "reference-ladder mismatch",
    ),
    source="DELTA_SUBSTRATE: quantize / flash ADC",
)

DELAY_CONTRACT = ComponentContract(
    op="delay",
    name="Clocked one-sample delay",
    ports=(
        PortSpec("x", "input", "numeric", "exact rational", "current sample"),
        PortSpec("y", "output", "numeric", "exact rational", "previous sample"),
    ),
    parameters=(
        ParameterSpec("ticks", "integer", "ticks >= 1", 1, "delay length in ticks"),
        ParameterSpec("initial", "rational", "exact rational", Fraction(0), "first-tick output"),
    ),
    law="y_t = x_{t-1}; y_0 = initial",
    state="one held sample per delay cell",
    operating_range="ticks >= 1; exact rational samples",
    material="clocked register / sample-and-hold",
    domain="digital / mixed-signal",
    carrier="temporal",
    failure_modes=("clock feedthrough", "aperture jitter", "metastability"),
    source="DELTA_SUBSTRATE: delay / clocked register",
)

SCALE_CONTRACT = ComponentContract(
    op="scale",
    name="Exact gain stage",
    ports=(
        PortSpec("x", "input", "numeric or interval", "exact rational", "signal to scale"),
        PortSpec("y", "output", "numeric or interval", "exact rational", "scaled signal"),
    ),
    parameters=(
        ParameterSpec(
            "factor",
            "rational",
            "any exact rational",
            Fraction(1, 2),
            "fixed gain applied to every input sample",
        ),
    ),
    law="y = factor * x",
    state="none",
    operating_range="exact rational or certified interval input",
    material="resistor divider / op-amp gain stage",
    domain="electrical",
    carrier="static",
    failure_modes=("gain error", "input offset", "finite gain-bandwidth"),
    source="DELTA_SUBSTRATE: scale / resistor divider, op-amp gain",
)

LOG_CONTRACT = ComponentContract(
    op="log",
    name="Logarithmic junction stage",
    ports=(
        PortSpec("x", "input", "numeric", "x > 0", "positive normalized signal"),
        PortSpec("y", "output", "interval", "certified rational enclosure", "ln(x)"),
    ),
    parameters=(
        ParameterSpec(
            "precision",
            "integer",
            "1 <= precision <= 64",
            20,
            "declared enclosure precision in bits",
        ),
    ),
    law="y = ln(x); certified rational enclosure, exact only at x = 1",
    state="none",
    operating_range="x > 0; the junction bias must remain in its logarithmic region",
    material="diode / BJT logging stage",
    domain="electrical",
    carrier="static",
    failure_modes=("thermal-voltage drift", "junction ideality mismatch", "offset"),
    source="DELTA_SUBSTRATE: sqrt / diode (log/antilog)",
)

EXP_CONTRACT = ComponentContract(
    op="exp",
    name="Exponential junction stage",
    ports=(
        PortSpec("x", "input", "interval", "certified rational enclosure", "log-domain signal"),
        PortSpec("y", "output", "interval", "certified rational enclosure", "exp(x)"),
    ),
    parameters=(
        ParameterSpec(
            "precision",
            "integer",
            "1 <= precision <= 64",
            20,
            "declared enclosure precision in bits",
        ),
    ),
    law="y = exp(x); certified rational enclosure, exact only at x = 0",
    state="none",
    operating_range="junction bias in its exponential region; result must stay finite",
    material="diode / BJT antilog stage",
    domain="electrical",
    carrier="static",
    failure_modes=("thermal-voltage drift", "junction ideality", "saturation"),
    source="DELTA_SUBSTRATE: sqrt / diode (log/antilog)",
)

MULT_CONTRACT = ComponentContract(
    op="mult",
    name="Analog multiplier",
    ports=(
        PortSpec("a", "input", "numeric or interval", "exact rational", "first multiplicand"),
        PortSpec("b", "input", "numeric or interval", "exact rational", "second multiplicand"),
        PortSpec("product", "output", "numeric or interval", "exact rational", "a * b"),
    ),
    parameters=(
        ParameterSpec(
            "gain",
            "rational",
            "any exact rational",
            Fraction(1),
            "multiplier scale factor",
        ),
    ),
    law="product = gain * a * b",
    state="none",
    operating_range="both inputs inside the multiplier's declared linear range",
    material="Gilbert-cell / AD633 analog multiplier",
    domain="electrical",
    carrier="static",
    failure_modes=("multiplier nonlinearity", "input offset", "feedthrough", "finite bandwidth"),
    source="DELTA_SUBSTRATE: mult / Gilbert cell multiplier",
)

AMP_CONTRACT = ComponentContract(
    op="amp",
    name="High-gain error amplifier",
    ports=(
        PortSpec("error", "input", "numeric or interval", "exact rational", "input error"),
        PortSpec("drive", "output", "numeric or interval", "exact rational", "amplified drive"),
    ),
    parameters=(
        ParameterSpec(
            "gain",
            "rational",
            "positive exact rational",
            Fraction(1_000_000),
            "finite open-loop gain",
        ),
    ),
    law="drive = gain * error",
    state="none",
    operating_range="error small enough that drive remains inside the output rails",
    material="op-amp error amplifier",
    domain="electrical",
    carrier="static",
    failure_modes=("finite gain", "input offset", "slew limiting", "output saturation"),
    source="DELTA_SUBSTRATE: scale / op-amp gain",
)

SUM_CONTRACT = ComponentContract(
    op="sum",
    name="Declared KCL summing junction",
    ports=(
        PortSpec("a", "input", "numeric", "exact rational", "first normalized current"),
        PortSpec("b", "input", "numeric", "exact rational", "second normalized current"),
        PortSpec("total", "output", "numeric", "exact rational", "normalized current sum"),
    ),
    parameters=(),
    law="total = a + b at a declared Kirchhoff current-law junction",
    state="none",
    operating_range="both normalized currents inside the declared linear junction range",
    material="KCL node (topological summing junction)",
    domain="electrical",
    carrier="static",
    failure_modes=("floating node", "source loading", "compliance limit"),
    source="DELTA_SUBSTRATE: sum / KCL node",
)

OPAMP_SUM_CONTRACT = ComponentContract(
    op="sum",
    name="Ideal op-amp non-inverting summing amplifier",
    ports=(
        PortSpec("a", "input", "numeric", "exact rational", "first normalized voltage"),
        PortSpec("b", "input", "numeric", "exact rational", "second normalized voltage"),
        PortSpec("total", "output", "numeric", "exact rational", "normalized voltage sum"),
    ),
    parameters=(),
    law=(
        "total = a + b with a matched input network (1/2 attenuation per input) "
        "and closed-loop gain 2"
    ),
    state="none",
    operating_range=(
        "both normalized voltages inside the declared linear output range; "
        "matched resistors and ideal closed-loop gain assumed"
    ),
    material="op-amp non-inverting summing amplifier with matched input resistors",
    domain="electrical",
    carrier="static",
    failure_modes=(
        "input-resistor mismatch",
        "finite open-loop gain and bandwidth",
        "input offset voltage and bias current",
        "output saturation or source loading",
    ),
    source="DELTA_SUBSTRATE: sum / op-amp summing amplifier",
)

OPAMP_INVERT_CONTRACT = ComponentContract(
    op="neg",
    name="Ideal op-amp inverting buffer",
    ports=(
        PortSpec("b", "input", "numeric", "exact rational", "normalized voltage"),
        PortSpec("neg_b", "output", "numeric", "exact rational", "inverted normalized voltage"),
    ),
    parameters=(),
    law="neg_b = -b with matched input and feedback resistors (gain -1)",
    state="none",
    operating_range="normalized voltage inside the declared linear output range",
    material="op-amp inverting buffer with matched resistors",
    domain="electrical",
    carrier="static",
    failure_modes=(
        "resistor mismatch",
        "finite open-loop gain and bandwidth",
        "input offset voltage and bias current",
        "output saturation or source loading",
    ),
    source="DELTA_SUBSTRATE: difference / op-amp inverting buffer",
)

FLUID_SUM_CONTRACT = ComponentContract(
    op="sum",
    name="Declared fluid pipe junction",
    ports=(
        PortSpec("q_a", "input", "numeric", "exact rational", "first normalized flow"),
        PortSpec("q_b", "input", "numeric", "exact rational", "second normalized flow"),
        PortSpec("q_total", "output", "numeric", "exact rational", "normalized flow sum"),
    ),
    parameters=(),
    law="q_total = q_a + q_b at a declared flow-conservation junction",
    state="none",
    operating_range="two normalized incompressible flows at the declared junction; no measured pressure/flow range",
    material="fluid pipe junction (continuity node)",
    domain="fluidic",
    carrier="temporal",
    failure_modes=(
        "no leakage or compressibility model declared",
        "no junction loss or measured flow evidence declared",
    ),
    source="DELTA_SUBSTRATE: sum / fluid pipe junction",
)

FLUID_REVERSE_CONTRACT = ComponentContract(
    op="neg",
    name="Declared reversed fluid port",
    ports=(
        PortSpec("q_b", "input", "numeric", "exact rational", "incoming normalized flow"),
        PortSpec("q_neg_b", "output", "numeric", "exact rational", "reversed normalized flow"),
    ),
    parameters=(),
    law="q_neg_b = -q_b at a declared reversed port",
    state="none",
    operating_range="normalized flow inside the declared linear junction range",
    material="reversed pipe port (signed-flow reference)",
    domain="fluidic",
    carrier="temporal",
    failure_modes=(
        "reversal is an ideal signed-flow convention; no valve or pump is modeled",
        "no leakage, compressibility or measured flow evidence declared",
    ),
    source="DELTA_SUBSTRATE: difference / reversed fluid port",
)

COMPONENT_CONTRACTS: dict[str, ComponentContract] = {
    contract.op: contract
    for contract in (
        ACCUM_CONTRACT,
        QUANTIZE_CONTRACT,
        DELAY_CONTRACT,
        SCALE_CONTRACT,
        MULT_CONTRACT,
        AMP_CONTRACT,
        LOG_CONTRACT,
        EXP_CONTRACT,
        SUM_CONTRACT,
        OPAMP_INVERT_CONTRACT,
    )
}


def component_contract(op: str) -> ComponentContract:
    """Return a typed contract for a physical route ingredient."""
    try:
        return COMPONENT_CONTRACTS[str(op)]
    except KeyError as exc:
        raise CentError(
            ErrorCode.UNSUPPORTED,
            f"no typed route contract for ¢_{op}",
        ) from exc


@dataclass(frozen=True)
class RouteComponent:
    """One component instance in an assembled route."""

    role: str
    op: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    parameters: Mapping[str, Any]
    contract: ComponentContract

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "op": self.op,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "parameters": _json(dict(self.parameters)),
            "contract": self.contract.as_dict(),
        }


@dataclass(frozen=True)
class RouteRun:
    """Result of executing one exact route simulation."""

    route_id: str
    input_value: Q
    samples: int
    quantum: Q
    full_scale: Q
    mean: Q
    error: Q
    tolerance: Q
    peak_integrator: Q
    range_ok: bool
    passed: bool
    trace: tuple[Mapping[str, Any], ...]

    @property
    def bitstream(self) -> tuple[int, ...]:
        """Return 0/1 codes only when the route is a one-bit quantizer."""
        if self.quantum != 1 or self.full_scale != 1:
            return ()
        return tuple(int(item["level"] / self.quantum) for item in self.trace)

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route_id,
            "input": q_to_json(self.input_value),
            "samples": self.samples,
            "quantum": q_to_json(self.quantum),
            "full_scale": q_to_json(self.full_scale),
            "mean": q_to_json(self.mean),
            "error": q_to_json(self.error),
            "tolerance": q_to_json(self.tolerance),
            "peak_integrator": q_to_json(self.peak_integrator),
            "range_ok": self.range_ok,
            "passed": self.passed,
            "bitstream": list(self.bitstream),
            "trace": [_json(item) for item in self.trace],
        }


@dataclass(frozen=True)
class RouteSpec:
    """A checked exact route graph plus its typed physical components."""

    id: str
    name: str
    description: str
    components: tuple[RouteComponent, ...]
    ports: tuple[PortSpec, ...]
    parameters: Mapping[str, Any]
    program: Program
    full_scale: Q
    quantum: Q
    integrator_limit: Q
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": "exact route model",
            "components": [component.as_dict() for component in self.components],
            "ports": [port.as_dict() for port in self.ports],
            "parameters": _json(dict(self.parameters)),
            "program": self.program.as_dict(),
            "topology_audit": audit_route_topology(self),
            "typed_graph": typed_graph(self).as_dict(),
            "gaps": list(self.gaps),
        }

    def simulate(self, input_value: Any = Fraction(1, 2), samples: int = 16) -> RouteRun:
        """Run the route exactly and return an auditable trace.

        The input and every internal wire are :class:`fractions.Fraction`.
        ``passed`` only claims the exact loop tracked the input within one
        quantizer step and stayed inside the declared integrator bound.  It is
        not device or fabrication evidence.
        """
        x = _as_fraction(input_value, "input")
        if not (Fraction(0) <= x <= self.full_scale):
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                f"delta-sigma input must be in [0, {self.full_scale}], got {x}",
            )
        if int(samples) < 1:
            raise CentError(ErrorCode.DOMAIN_ERROR, "samples must be >= 1")

        ticks = int(samples)
        outputs = run_program(self.program, [{"x": x}] * ticks)
        trace: list[Mapping[str, Any]] = []
        total = Fraction(0)
        peak = Fraction(0)
        for index, values in enumerate(outputs, start=1):
            level = values["level"]
            integrator = values["integrator"]
            total += level
            peak = max(peak, abs(integrator))
            trace.append(
                {
                    "tick": index,
                    "input": x,
                    "error": values["error"],
                    "integrator": integrator,
                    "raw_level": values["raw_level"],
                    "level": level,
                    "feedback": values["feedback"],
                }
            )

        mean = total / ticks
        error = mean - x
        tolerance = self.quantum
        range_ok = peak <= self.integrator_limit
        passed = range_ok and abs(error) <= tolerance
        return RouteRun(
            route_id=self.id,
            input_value=x,
            samples=ticks,
            quantum=self.quantum,
            full_scale=self.full_scale,
            mean=mean,
            error=error,
            tolerance=tolerance,
            peak_integrator=peak,
            range_ok=range_ok,
            passed=passed,
            trace=tuple(trace),
        )

    def render_text(self) -> str:
        """Render the route plan for the terminal."""
        lines = [
            "=" * 78,
            "PHYSICAL ROUTE ASSEMBLY",
            "=" * 78,
            f"Route: {self.name}",
            f"Status: exact route model; no fabrication netlist",
            "",
            "Typed components",
        ]
        for component in self.components:
            lines.append(
                f"  {component.role:<12} ¢_{component.op:<9} "
                f"{component.contract.material}"
            )
            lines.append(f"    law: {component.contract.law}")
            lines.append(
                "    ports: "
                + ", ".join(
                    f"{port.name}:{port.direction}:{port.kind}"
                    for port in component.contract.ports
                )
            )
        lines.append("")
        lines.append("Exact route graph")
        lines.append("  inputs: " + ", ".join(self.program.inputs))
        for index, instruction in enumerate(self.program.instructions, start=1):
            lines.append(
                f"  {index}. {instruction.out} <- ¢_{instruction.op}"
                f"({', '.join(instruction.inputs)})"
            )
        lines.append("  outputs: " + ", ".join(self.program.outputs))
        lines.append("")
        lines.append("Declared gaps")
        for gap in self.gaps:
            lines.append(f"  - {gap}")
        return "\n".join(lines)


def _delta_sigma_program(quantum: Q, full_scale: Q) -> Program:
    program = Program(
        name="delta-sigma-first-order",
        inputs={"x": NUMERIC},
        instructions=(
            Instruction("neg", ("feedback",), "neg_feedback"),
            Instruction("sum", ("x", "neg_feedback"), "error"),
            Instruction("accum", ("error",), "integrator"),
            Instruction("quantize", ("integrator",), "raw_level", {"quantum": quantum}),
            Instruction(
                "sat",
                ("raw_level",),
                "level",
                {"lo": Fraction(0), "hi": full_scale},
            ),
            Instruction(
                "delay",
                ("level",),
                "feedback",
                {"ticks": 1, "initial": Fraction(0)},
            ),
        ),
        outputs={
            "level": "level",
            "raw_level": "raw_level",
            "error": "error",
            "integrator": "integrator",
            "feedback": "feedback",
        },
    )
    analyse(program)
    return program


def delta_sigma_route(
    *,
    quantum: Any = Fraction(1),
    full_scale: Any = Fraction(1),
    integrator_limit: Any = Fraction(8),
) -> RouteSpec:
    """Assemble the first-order delta-sigma route from typed components.

    ``full_scale / quantum`` must be an integer so the declared quantizer is a
    finite uniform ladder.  This is a one-bit route when ``quantum == full_scale``.
    The route uses exact arithmetic and normalized quantities; voltage/current
    scaling belongs to a future device-level mapping.
    """
    quantum_q = _as_fraction(quantum, "quantum")
    full_scale_q = _as_fraction(full_scale, "full_scale")
    limit_q = _as_fraction(integrator_limit, "integrator_limit")

    if quantum_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "quantum must be positive")
    if full_scale_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "full_scale must be positive")
    if quantum_q > full_scale_q:
        raise CentError(ErrorCode.DOMAIN_ERROR, "quantum cannot exceed full_scale")
    levels = full_scale_q / quantum_q
    if levels.denominator != 1:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "full_scale must be an integer multiple of quantum",
        )
    if limit_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "integrator_limit must be positive")

    program = _delta_sigma_program(quantum_q, full_scale_q)
    components = (
        RouteComponent(
            "integrator",
            "accum",
            ("error",),
            ("integrator",),
            {},
            ACCUM_CONTRACT,
        ),
        RouteComponent(
            "quantizer",
            "quantize",
            ("integrator",),
            ("level",),
            {"quantum": quantum_q, "full_scale": full_scale_q},
            QUANTIZE_CONTRACT,
        ),
        RouteComponent(
            "feedback",
            "delay",
            ("level",),
            ("feedback",),
            {"ticks": 1, "initial": Fraction(0)},
            DELAY_CONTRACT,
        ),
    )
    ports = (
        PortSpec(
            "x",
            "input",
            "numeric",
            f"[0, {full_scale_q}]",
            "normalized input signal",
        ),
        PortSpec(
            "level",
            "output",
            "numeric",
            f"{{0, {quantum_q}, ..., {full_scale_q}}}",
            "quantized level; a 0/1 bit when quantum == full_scale",
        ),
    )
    gaps = (
        "exact normalized route only; no voltage/current scaling or device netlist",
        "comparator metastability, clock jitter and capacitor leakage are not modeled",
        "no fabrication or measured-device evidence",
    )
    return RouteSpec(
        id="delta-sigma-first-order",
        name="First-order delta-sigma loop",
        description=(
            "A switched-capacitor integrator, uniform quantizer and clocked "
            "feedback delay closed around an exact error sum."
        ),
        components=components,
        ports=ports,
        parameters={
            "quantum": quantum_q,
            "full_scale": full_scale_q,
            "integrator_limit": limit_q,
            "levels": int(levels) + 1,
        },
        program=program,
        full_scale=full_scale_q,
        quantum=quantum_q,
        integrator_limit=limit_q,
        gaps=gaps,
    )


def render_run(run: RouteRun) -> str:
    """Render a route simulation for the CLI."""
    lines = [
        "Exact route simulation",
        f"  input: {run.input_value}",
        f"  samples: {run.samples}",
        f"  bitstream: {''.join(str(bit) for bit in run.bitstream) or '(not one-bit)'}",
        f"  mean: {run.mean}",
        f"  error: {run.error}",
        f"  tolerance: {run.tolerance}",
        f"  peak integrator: {run.peak_integrator}",
        f"  range ok: {run.range_ok}",
        f"  passed: {run.passed}",
    ]
    if run.trace:
        first = run.trace[0]
        last = run.trace[-1]
        lines.append(
            "  first tick: "
            f"error={first['error']} integrator={first['integrator']} "
            f"level={first['level']} feedback={first['feedback']}"
        )
        lines.append(
            "  last tick:  "
            f"error={last['error']} integrator={last['integrator']} "
            f"level={last['level']} feedback={last['feedback']}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Certified log-domain square-root route
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SqrtRun:
    """Exact finite-precision evaluation of the log-domain square-root route."""

    route_id: str
    input_value: Q
    precision: int
    tolerance: Q
    ln_x: Interval
    half_ln: Interval
    root: Interval
    checker: Interval
    overlap: Interval | None
    passed: bool
    trace: tuple[Mapping[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route_id,
            "kind": "certified-enclosure",
            "input": q_to_json(self.input_value),
            "precision": self.precision,
            "tolerance": q_to_json(self.tolerance),
            "root": _json(self.root),
            "checker": _json(self.checker),
            "overlap": _json(self.overlap) if self.overlap is not None else None,
            "root_width": q_to_json(self.root.width),
            "checker_width": q_to_json(self.checker.width),
            "passed": self.passed,
            "trace": [_json(item) for item in self.trace],
        }


@dataclass(frozen=True)
class SqrtRoute:
    """A typed log-domain route whose result is a certified rational enclosure."""

    id: str
    name: str
    description: str
    components: tuple[RouteComponent, ...]
    ports: tuple[PortSpec, ...]
    parameters: Mapping[str, Any]
    program: Program
    precision: int
    tolerance: Q
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "kind": "certified-enclosure",
            "name": self.name,
            "description": self.description,
            "status": "exact certified-enclosure route",
            "components": [component.as_dict() for component in self.components],
            "ports": [port.as_dict() for port in self.ports],
            "parameters": _json(dict(self.parameters)),
            "program": self.program.as_dict(),
            "topology_audit": audit_route_topology(self),
            "typed_graph": typed_graph(self).as_dict(),
            "gaps": list(self.gaps),
        }

    def simulate(self, input_value: Any = Fraction(2)) -> SqrtRun:
        """Evaluate the route once and check it against the independent sqrt bracket.

        ``passed`` means the route's rational enclosure overlaps the core's
        independently constructed ``sqrt_q`` enclosure and its width is within
        the declared tolerance.  It does not mean the irrational value was
        stored exactly.
        """
        x = _as_fraction(input_value, "input")
        if x <= 0:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                f"log-domain sqrt input must be positive, got {x}",
            )

        values = run_program(self.program, [{"x": x}])[0]
        ln_x = values["ln_x"]
        half_ln = values["half_ln"]
        root = values["root"]
        if not all(isinstance(value, Interval) for value in (ln_x, half_ln, root)):
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                "log-domain route did not produce certified interval wires",
            )

        checker = sqrt_q(x, self.precision)
        overlap = _overlap(root, checker)
        passed = overlap is not None and root.width <= self.tolerance
        trace = (
            {
                "stage": "log",
                "op": "log",
                "input": x,
                "output": ln_x,
                "width": ln_x.width,
            },
            {
                "stage": "half-gain",
                "op": "scale",
                "factor": Fraction(1, 2),
                "input": ln_x,
                "output": half_ln,
                "width": half_ln.width,
            },
            {
                "stage": "antilog",
                "op": "exp",
                "input": half_ln,
                "output": root,
                "width": root.width,
            },
        )
        return SqrtRun(
            route_id=self.id,
            input_value=x,
            precision=self.precision,
            tolerance=self.tolerance,
            ln_x=ln_x,
            half_ln=half_ln,
            root=root,
            checker=checker,
            overlap=overlap,
            passed=passed,
            trace=trace,
        )


def _overlap(left: Interval, right: Interval) -> Interval | None:
    lo = max(left.lo, right.lo)
    hi = min(left.hi, right.hi)
    return Interval(lo, hi) if lo <= hi else None


def _log_domain_sqrt_program(precision: int) -> Program:
    program = Program(
        name="sqrt-log-domain",
        inputs={"x": NUMERIC},
        instructions=(
            Instruction("log", ("x",), "ln_x", {"precision": precision}),
            Instruction("scale", ("ln_x",), "half_ln", {"factor": Fraction(1, 2)}),
            Instruction("exp", ("half_ln",), "root", {"precision": precision}),
        ),
        outputs={"root": "root", "ln_x": "ln_x", "half_ln": "half_ln"},
    )
    analyse(program)
    return program


def log_domain_sqrt_route(
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> SqrtRoute:
    """Assemble ``exp((1/2) log(x))`` from declared analog stages.

    The route is an exact finite-precision calculation: ``log`` and ``exp``
    return rational enclosures, and the independent ``sqrt_q`` check bounds the
    true irrational result.  The precision is a declared device/model
    parameter; no hidden binary float is used.
    """
    if isinstance(precision, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    try:
        precision_i = int(precision)
    except (TypeError, ValueError) as exc:
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer") from exc
    if not 1 <= precision_i <= 64:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "precision must be in 1..64 bits for the declared log-domain route",
        )
    tolerance_q = _as_fraction(tolerance, "tolerance")
    if tolerance_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "tolerance must be positive")

    program = _log_domain_sqrt_program(precision_i)
    components = (
        RouteComponent(
            "logger",
            "log",
            ("x",),
            ("ln_x",),
            {"precision": precision_i},
            LOG_CONTRACT,
        ),
        RouteComponent(
            "half_gain",
            "scale",
            ("ln_x",),
            ("half_ln",),
            {"factor": Fraction(1, 2)},
            SCALE_CONTRACT,
        ),
        RouteComponent(
            "antilog",
            "exp",
            ("half_ln",),
            ("root",),
            {"precision": precision_i},
            EXP_CONTRACT,
        ),
    )
    ports = (
        PortSpec("x", "input", "numeric", "x > 0", "positive normalized signal"),
        PortSpec(
            "root",
            "output",
            "interval",
            "certified rational enclosure of sqrt(x)",
            "root extractor output",
        ),
    )
    gaps = (
        "certified enclosure only; the irrational result is not stored exactly",
        "exact normalized route only; no voltage/current scaling or device netlist",
        "junction temperature, ideality, offset and finite bandwidth are not modeled",
        "no fabrication or measured-device evidence",
    )
    return SqrtRoute(
        id="sqrt-log-domain",
        name="Log-domain square-root extractor",
        description=(
            "A logging junction stage, an exact one-half gain stage and an "
            "antilog junction stage compute exp((1/2) ln x) = sqrt(x)."
        ),
        components=components,
        ports=ports,
        parameters={
            "precision": precision_i,
            "tolerance": tolerance_q,
            "gain": Fraction(1, 2),
            "operation": "exp((1/2) * log(x))",
        },
        program=program,
        precision=precision_i,
        tolerance=tolerance_q,
        gaps=gaps,
    )


@dataclass(frozen=True)
class ArithmeticRun:
    """One source-side log-domain arithmetic evaluation."""

    route_id: str
    operation: str
    inputs: Mapping[str, Q]
    precision: int
    tolerance: Q
    result: Interval
    checker: Interval
    passed: bool
    trace: tuple[Mapping[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route_id,
            "operation": self.operation,
            "inputs": {name: q_to_json(value) for name, value in self.inputs.items()},
            "precision": self.precision,
            "tolerance": q_to_json(self.tolerance),
            "result": _json(self.result),
            "checker": _json(self.checker),
            "width": q_to_json(self.result.width),
            "passed": self.passed,
            "trace": [_json(item) for item in self.trace],
        }


@dataclass(frozen=True)
class ArithmeticRoute:
    """Typed log-domain composition for exp/log/mult/div.

    The route is generated from the shared transcendental identity
    ``x = exp(log(x))``.  Multiplication adds logarithms; division subtracts
    one; the antilog junction returns the result as a certified enclosure.
    """

    id: str
    name: str
    description: str
    operation: str
    components: tuple[RouteComponent, ...]
    ports: tuple[PortSpec, ...]
    parameters: Mapping[str, Any]
    program: Program
    precision: int
    tolerance: Q
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "kind": "certified-enclosure",
            "name": self.name,
            "description": self.description,
            "operation": self.operation,
            "status": "exact certified-enclosure route",
            "components": [component.as_dict() for component in self.components],
            "ports": [port.as_dict() for port in self.ports],
            "parameters": _json(dict(self.parameters)),
            "program": self.program.as_dict(),
            "gaps": list(self.gaps),
        }

    def simulate(self, **inputs: Any) -> ArithmeticRun:
        values_in: dict[str, Q] = {}
        for name in self.program.inputs:
            if name not in inputs:
                raise CentError(
                    ErrorCode.INVALID_INPUT,
                    f"log-domain arithmetic input {name!r} is required",
                )
            values_in[name] = _as_fraction(inputs[name], name)
        if self.operation in {
            "log", "mult", "div", "reciprocal", "mult-div", "mult-reciprocal",
            "div-mult",
        } and any(value <= 0 for value in values_in.values()):
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                "log-domain log/mult/div/reciprocal inputs must be positive",
            )
        values = run_program(self.program, [values_in])[0]
        result = values["value"]
        if not isinstance(result, Interval):
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                "log-domain arithmetic route did not produce an interval result",
            )
        checker_precision = min(64, self.precision + 8)
        if self.operation == "exp":
            checker = exp_q(values_in["x"], checker_precision)
        elif self.operation == "log":
            checker = log_q(values_in["x"], checker_precision)
        elif self.operation == "mult":
            checker = Interval.point(values_in["a"] * values_in["b"])
        elif self.operation == "reciprocal":
            checker = Interval.point(Fraction(1) / values_in["x"])
        elif self.operation == "mult-div":
            checker = Interval.point(
                values_in["a"] * values_in["b"] / values_in["c"]
            )
        elif self.operation == "mult-reciprocal":
            checker = Interval.point(
                Fraction(1) / (values_in["a"] * values_in["b"])
            )
        elif self.operation == "div-mult":
            checker = Interval.point(
                values_in["a"] * values_in["c"] / values_in["b"]
            )
        else:
            checker = Interval.point(values_in["a"] / values_in["b"])
        overlap = max(result.lo, checker.lo) <= min(result.hi, checker.hi)
        passed = overlap and result.width <= self.tolerance
        trace = (
            {
                "stage": "log-domain arithmetic",
                "operation": self.operation,
                "inputs": values_in,
                "result": result,
                "width": result.width,
            },
        )
        return ArithmeticRun(
            route_id=self.id,
            operation=self.operation,
            inputs=values_in,
            precision=self.precision,
            tolerance=self.tolerance,
            result=result,
            checker=checker,
            passed=passed,
            trace=trace,
        )


def _log_domain_arithmetic_program(operation: str, precision: int) -> Program:
    if operation not in {"exp", "log", "mult", "div", "reciprocal"}:
        raise CentError(
            ErrorCode.UNSUPPORTED,
            f"log-domain arithmetic does not declare {operation!r}",
        )
    if operation == "exp":
        instructions = (
            Instruction("exp", ("x",), "value", {"precision": precision}),
        )
        inputs = {"x": NUMERIC}
    elif operation == "log":
        instructions = (
            Instruction("log", ("x",), "value", {"precision": precision}),
        )
        inputs = {"x": NUMERIC}
    elif operation == "mult":
        instructions = (
            Instruction("log", ("a",), "ln_a", {"precision": precision}),
            Instruction("log", ("b",), "ln_b", {"precision": precision}),
            Instruction("sum", ("ln_a", "ln_b"), "ln_ab"),
            Instruction("exp", ("ln_ab",), "value", {"precision": precision}),
        )
        inputs = {"a": NUMERIC, "b": NUMERIC}
    elif operation == "reciprocal":
        instructions = (
            Instruction("log", ("x",), "ln_x", {"precision": precision}),
            Instruction("neg", ("ln_x",), "neg_ln_x"),
            Instruction("exp", ("neg_ln_x",), "value", {"precision": precision}),
        )
        inputs = {"x": NUMERIC}
    else:
        instructions = (
            Instruction("log", ("a",), "ln_a", {"precision": precision}),
            Instruction("log", ("b",), "ln_b", {"precision": precision}),
            Instruction("neg", ("ln_b",), "neg_ln_b"),
            Instruction("sum", ("ln_a", "neg_ln_b"), "ln_ab"),
            Instruction("exp", ("ln_ab",), "value", {"precision": precision}),
        )
        inputs = {"a": NUMERIC, "b": NUMERIC}
    program = Program(
        name=f"log-domain-{operation}",
        inputs=inputs,
        instructions=instructions,
        outputs={"value": "value"},
    )
    analyse(program)
    return program


def log_domain_arithmetic_route(
    operation: str,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticRoute:
    """Assemble one log-domain arithmetic composition from typed stages."""
    op = str(operation).strip()
    if op not in {"exp", "log", "mult", "div", "reciprocal"}:
        raise CentError(
            ErrorCode.UNSUPPORTED,
            f"log-domain arithmetic does not declare {op!r}",
        )
    if isinstance(precision, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    try:
        precision_i = int(precision)
    except (TypeError, ValueError) as exc:
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer") from exc
    if not 1 <= precision_i <= 64:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "precision must be in 1..64 bits for the declared log-domain route",
        )
    tolerance_q = _as_fraction(tolerance, "tolerance")
    if tolerance_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "tolerance must be positive")

    program = _log_domain_arithmetic_program(op, precision_i)
    component_list: list[RouteComponent] = []
    if op == "exp":
        component_list.append(
            RouteComponent("antilog", "exp", ("x",), ("value",),
                           {"precision": precision_i}, EXP_CONTRACT)
        )
    elif op == "log":
        component_list.append(
            RouteComponent("logger", "log", ("x",), ("value",),
                           {"precision": precision_i}, LOG_CONTRACT)
        )
    elif op == "reciprocal":
        component_list.extend((
            RouteComponent("logger", "log", ("x",), ("ln_x",),
                           {"precision": precision_i}, LOG_CONTRACT),
            RouteComponent("inverter", "neg", ("ln_x",), ("neg_ln_x",),
                           {}, OPAMP_INVERT_CONTRACT),
            RouteComponent("antilog", "exp", ("neg_ln_x",), ("value",),
                           {"precision": precision_i}, EXP_CONTRACT),
        ))
    else:
        component_list.extend((
            RouteComponent("logger_a", "log", ("a",), ("ln_a",),
                           {"precision": precision_i}, LOG_CONTRACT),
            RouteComponent("logger_b", "log", ("b",), ("ln_b",),
                           {"precision": precision_i}, LOG_CONTRACT),
        ))
        if op == "div":
            component_list.append(
                RouteComponent("inverter", "neg", ("ln_b",), ("neg_ln_b",),
                               {}, OPAMP_INVERT_CONTRACT)
            )
        component_list.extend((
            RouteComponent("log_sum", "sum", ("ln_a", "ln_b" if op == "mult" else "neg_ln_b"),
                           ("ln_ab",), {}, SUM_CONTRACT),
            RouteComponent("antilog", "exp", ("ln_ab",), ("value",),
                           {"precision": precision_i}, EXP_CONTRACT),
        ))
    ports = tuple(
        PortSpec(name, "input", "numeric", "exact rational", f"log-domain {name}")
        for name in program.inputs
    ) + (
        PortSpec("value", "output", "interval", "certified rational enclosure",
                 f"certified enclosure of {op}"),
    )
    gaps = (
        "certified enclosure only; the irrational result is not stored exactly",
        "exact normalized route only; no voltage/current scaling or device netlist",
        "junction temperature, ideality, offset and finite bandwidth are not modeled",
        "no fabrication or measured-device evidence",
    )
    return ArithmeticRoute(
        id=f"log-domain-{op}",
        name=f"Log-domain {op}",
        description=(
            "A logarithmic junction, exact signed sum and antilog junction "
            f"compute {op} from the shared exp(log(x)) identity."
        ),
        operation=op,
        components=tuple(component_list),
        ports=ports,
        parameters={"precision": precision_i, "tolerance": tolerance_q,
                    "operation": op},
        program=program,
        precision=precision_i,
        tolerance=tolerance_q,
        gaps=gaps,
    )


def log_domain_mult_reciprocal_route(
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticRoute:
    """Assemble the declared ``mult -> reciprocal`` log-domain chain.

    The composition is ``1 / (a * b)``: two logging junctions, an exact sum,
    one inversion, and one antilog junction.
    """
    if isinstance(precision, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    try:
        precision_i = int(precision)
    except (TypeError, ValueError) as exc:
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer") from exc
    if not 1 <= precision_i <= 64:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "precision must be in 1..64 bits for the declared log-domain route",
        )
    tolerance_q = _as_fraction(tolerance, "tolerance")
    if tolerance_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "tolerance must be positive")

    program = Program(
        name="log-domain-mult-reciprocal",
        inputs={"a": NUMERIC, "b": NUMERIC},
        instructions=(
            Instruction("log", ("a",), "ln_a", {"precision": precision_i}),
            Instruction("log", ("b",), "ln_b", {"precision": precision_i}),
            Instruction("sum", ("ln_a", "ln_b"), "ln_ab"),
            Instruction("neg", ("ln_ab",), "neg_ln_ab"),
            Instruction("exp", ("neg_ln_ab",), "value", {"precision": precision_i}),
        ),
        outputs={"value": "value"},
    )
    analyse(program)
    components = (
        RouteComponent("logger_a", "log", ("a",), ("ln_a",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("logger_b", "log", ("b",), ("ln_b",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("log_sum", "sum", ("ln_a", "ln_b"), ("ln_ab",),
                       {}, SUM_CONTRACT),
        RouteComponent("inverter", "neg", ("ln_ab",), ("neg_ln_ab",),
                       {}, OPAMP_INVERT_CONTRACT),
        RouteComponent("antilog", "exp", ("neg_ln_ab",), ("value",),
                       {"precision": precision_i}, EXP_CONTRACT),
    )
    ports = tuple(
        PortSpec(name, "input", "numeric", "exact rational", f"log-domain {name}")
        for name in ("a", "b")
    ) + (
        PortSpec("value", "output", "interval", "certified rational enclosure",
                 "certified enclosure of 1 / (a * b)"),
    )
    return ArithmeticRoute(
        id="log-domain-mult-reciprocal",
        name="Log-domain mult -> reciprocal",
        description=(
            "Two logging junctions are summed, inverted and returned through "
            "the antilog junction as 1/(a*b)."
        ),
        operation="mult-reciprocal",
        components=components,
        ports=ports,
        parameters={
            "precision": precision_i,
            "tolerance": tolerance_q,
            "operation": "mult-reciprocal",
        },
        program=program,
        precision=precision_i,
        tolerance=tolerance_q,
        gaps=(
            "certified enclosure only; the irrational result is not stored exactly",
            "exact normalized route only; no voltage/current scaling or device netlist",
            "junction temperature, ideality, offset and finite bandwidth are not modeled",
            "no fabrication or measured-device evidence",
        ),
    )


def log_domain_div_mult_route(
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticRoute:
    """Assemble the declared ``div -> mult`` log-domain chain.

    The composition is ``(a / b) * c``: logging junctions for a, b and c,
    an inverted b, two exact sums, and one antilog junction.
    """
    if isinstance(precision, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    try:
        precision_i = int(precision)
    except (TypeError, ValueError) as exc:
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer") from exc
    if not 1 <= precision_i <= 64:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "precision must be in 1..64 bits for the declared log-domain route",
        )
    tolerance_q = _as_fraction(tolerance, "tolerance")
    if tolerance_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "tolerance must be positive")

    program = Program(
        name="log-domain-div-mult",
        inputs={"a": NUMERIC, "b": NUMERIC, "c": NUMERIC},
        instructions=(
            Instruction("log", ("a",), "ln_a", {"precision": precision_i}),
            Instruction("log", ("b",), "ln_b", {"precision": precision_i}),
            Instruction("neg", ("ln_b",), "neg_ln_b"),
            Instruction("sum", ("ln_a", "neg_ln_b"), "ln_ab"),
            Instruction("log", ("c",), "ln_c", {"precision": precision_i}),
            Instruction("sum", ("ln_ab", "ln_c"), "ln_abc"),
            Instruction("exp", ("ln_abc",), "value", {"precision": precision_i}),
        ),
        outputs={"value": "value"},
    )
    analyse(program)
    components = (
        RouteComponent("logger_a", "log", ("a",), ("ln_a",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("logger_b", "log", ("b",), ("ln_b",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("inverter", "neg", ("ln_b",), ("neg_ln_b",),
                       {}, OPAMP_INVERT_CONTRACT),
        RouteComponent("log_sum", "sum", ("ln_a", "neg_ln_b"), ("ln_ab",),
                       {}, SUM_CONTRACT),
        RouteComponent("logger_c", "log", ("c",), ("ln_c",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("result_sum", "sum", ("ln_ab", "ln_c"), ("ln_abc",),
                       {}, SUM_CONTRACT),
        RouteComponent("antilog", "exp", ("ln_abc",), ("value",),
                       {"precision": precision_i}, EXP_CONTRACT),
    )
    ports = tuple(
        PortSpec(name, "input", "numeric", "exact rational", f"log-domain {name}")
        for name in ("a", "b", "c")
    ) + (
        PortSpec("value", "output", "interval", "certified rational enclosure",
                 "certified enclosure of (a / b) * c"),
    )
    return ArithmeticRoute(
        id="log-domain-div-mult",
        name="Log-domain div -> mult",
        description=(
            "Logging junctions for a and b, an inverted b, an exact division "
            "sum, and a multiplied c are returned as (a/b)*c."
        ),
        operation="div-mult",
        components=components,
        ports=ports,
        parameters={
            "precision": precision_i,
            "tolerance": tolerance_q,
            "operation": "div-mult",
        },
        program=program,
        precision=precision_i,
        tolerance=tolerance_q,
        gaps=(
            "certified enclosure only; the irrational result is not stored exactly",
            "exact normalized route only; no voltage/current scaling or device netlist",
            "junction temperature, ideality, offset and finite bandwidth are not modeled",
            "no fabrication or measured-device evidence",
        ),
    )


def log_domain_mult_div_route(
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticRoute:
    """Assemble the declared ``mult -> div`` log-domain chain.

    The composition is ``(a * b) / c``: two logging junctions, an exact signed
    sum, a third logging junction with inversion, and one antilog junction.
    """
    if isinstance(precision, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    try:
        precision_i = int(precision)
    except (TypeError, ValueError) as exc:
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer") from exc
    if not 1 <= precision_i <= 64:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "precision must be in 1..64 bits for the declared log-domain route",
        )
    tolerance_q = _as_fraction(tolerance, "tolerance")
    if tolerance_q <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "tolerance must be positive")

    program = Program(
        name="log-domain-mult-div",
        inputs={"a": NUMERIC, "b": NUMERIC, "c": NUMERIC},
        instructions=(
            Instruction("log", ("a",), "ln_a", {"precision": precision_i}),
            Instruction("log", ("b",), "ln_b", {"precision": precision_i}),
            Instruction("sum", ("ln_a", "ln_b"), "ln_ab"),
            Instruction("log", ("c",), "ln_c", {"precision": precision_i}),
            Instruction("neg", ("ln_c",), "neg_ln_c"),
            Instruction("sum", ("ln_ab", "neg_ln_c"), "ln_abc"),
            Instruction("exp", ("ln_abc",), "value", {"precision": precision_i}),
        ),
        outputs={"value": "value"},
    )
    analyse(program)
    components = (
        RouteComponent("logger_a", "log", ("a",), ("ln_a",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("logger_b", "log", ("b",), ("ln_b",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("log_sum", "sum", ("ln_a", "ln_b"), ("ln_ab",),
                       {}, SUM_CONTRACT),
        RouteComponent("logger_c", "log", ("c",), ("ln_c",),
                       {"precision": precision_i}, LOG_CONTRACT),
        RouteComponent("inverter", "neg", ("ln_c",), ("neg_ln_c",),
                       {}, OPAMP_INVERT_CONTRACT),
        RouteComponent("result_sum", "sum", ("ln_ab", "neg_ln_c"), ("ln_abc",),
                       {}, SUM_CONTRACT),
        RouteComponent("antilog", "exp", ("ln_abc",), ("value",),
                       {"precision": precision_i}, EXP_CONTRACT),
    )
    ports = tuple(
        PortSpec(name, "input", "numeric", "exact rational", f"log-domain {name}")
        for name in ("a", "b", "c")
    ) + (
        PortSpec("value", "output", "interval", "certified rational enclosure",
                 "certified enclosure of (a * b) / c"),
    )
    return ArithmeticRoute(
        id="log-domain-mult-div",
        name="Log-domain mult -> div",
        description=(
            "Two logging junctions and one inverted logging junction are summed "
            "exactly and returned through the antilog junction as (a*b)/c."
        ),
        operation="mult-div",
        components=components,
        ports=ports,
        parameters={
            "precision": precision_i,
            "tolerance": tolerance_q,
            "operation": "mult-div",
        },
        program=program,
        precision=precision_i,
        tolerance=tolerance_q,
        gaps=(
            "certified enclosure only; the irrational result is not stored exactly",
            "exact normalized route only; no voltage/current scaling or device netlist",
            "junction temperature, ideality, offset and finite bandwidth are not modeled",
            "no fabrication or measured-device evidence",
        ),
    )


# ---------------------------------------------------------------------------
# Exact KCL sum/difference route
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KCLSumRun:
    """Exact two-input evaluation of the KCL sum/difference route."""

    route_id: str
    operation: str
    input_a: Q
    input_b: Q
    result: Q
    expected: Q
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route_id,
            "kind": "exact-sum",
            "operation": self.operation,
            "a": q_to_json(self.input_a),
            "b": q_to_json(self.input_b),
            "result": q_to_json(self.result),
            "expected": q_to_json(self.expected),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class KCLSumRoute:
    """A declared KCL junction with an exact sum or difference program."""

    id: str
    name: str
    description: str
    components: tuple[RouteComponent, ...]
    ports: tuple[PortSpec, ...]
    parameters: Mapping[str, Any]
    program: Program
    operation: str
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "kind": "exact-sum",
            "name": self.name,
            "description": self.description,
            "status": "exact route model",
            "components": [component.as_dict() for component in self.components],
            "ports": [port.as_dict() for port in self.ports],
            "parameters": _json(dict(self.parameters)),
            "program": self.program.as_dict(),
            "topology_audit": audit_route_topology(self),
            "typed_graph": typed_graph(self).as_dict(),
            "gaps": list(self.gaps),
        }

    def simulate(
        self,
        input_a: Any = Fraction(1, 2),
        input_b: Any = Fraction(1, 3),
    ) -> KCLSumRun:
        """Evaluate the declared two-input operation exactly."""
        a = _as_fraction(input_a, "a")
        b = _as_fraction(input_b, "b")
        values = run_program(self.program, [{"a": a, "b": b}])[0]
        result = values["total"]
        expected = a + b if self.operation == "sum" else a - b
        return KCLSumRun(
            route_id=self.id,
            operation=self.operation,
            input_a=a,
            input_b=b,
            result=result,
            expected=expected,
            passed=result == expected,
        )

    def render_text(self) -> str:
        lines = [
            "=" * 78,
            "PHYSICAL ROUTE ASSEMBLY",
            "=" * 78,
            f"Route: {self.name}",
            "Status: exact route model; no device binding or fabrication netlist",
            "",
            "Typed components",
        ]
        for component in self.components:
            lines.append(
                f"  {component.role:<12} ¢_{component.op:<9} "
                f"{component.contract.material}"
            )
            lines.append(f"    law: {component.contract.law}")
            lines.append(
                "    ports: "
                + ", ".join(
                    f"{port.name}:{port.direction}:{port.kind}"
                    for port in component.contract.ports
                )
            )
        lines.append("")
        lines.append("Exact route graph")
        lines.append("  inputs: " + ", ".join(self.program.inputs))
        for index, instruction in enumerate(self.program.instructions, start=1):
            lines.append(
                f"  {index}. {instruction.out} <- ¢_{instruction.op}"
                f"({', '.join(instruction.inputs)})"
            )
        lines.append("  outputs: " + ", ".join(self.program.outputs))
        lines.append("")
        lines.append("Declared gaps")
        for gap in self.gaps:
            lines.append(f"  - {gap}")
        return "\n".join(lines)


def _kcl_sum_program(operation: str) -> Program:
    if operation == "sum":
        instructions = (Instruction("sum", ("a", "b"), "total"),)
    elif operation == "difference":
        instructions = (
            Instruction("neg", ("b",), "neg_b"),
            Instruction("sum", ("a", "neg_b"), "total"),
        )
    else:
        raise CentError(ErrorCode.INVALID_INPUT, f"unknown KCL operation: {operation}")
    program = Program(
        name=f"sum-kcl-{operation}",
        inputs={"a": NUMERIC, "b": NUMERIC},
        instructions=instructions,
        outputs={"total": "total"},
    )
    analyse(program)
    return program


def kcl_sum_route(*, operation: str = "sum") -> KCLSumRoute:
    """Assemble the declared KCL sum/difference route.

    The KCL junction is a declared topological sum contract, not a fabricated
    device.  Addition is one `sum` instruction; subtraction is `neg` on the
    second input followed by `sum`, with the negation kept as exact-core glue.
    """
    if operation not in {"sum", "difference"}:
        raise CentError(ErrorCode.INVALID_INPUT, f"unknown KCL operation: {operation}")
    program = _kcl_sum_program(operation)
    components = (
        RouteComponent("junction", "sum", ("a", "b"), ("total",), {}, SUM_CONTRACT),
    )
    ports = (
        PortSpec("a", "input", "numeric", "any exact rational", "first normalized current"),
        PortSpec("b", "input", "numeric", "any exact rational", "second normalized current"),
        PortSpec("total", "output", "numeric", "a + b or a - b", "declared result"),
    )
    gaps = (
        "declared KCL junction topology only; no voltage/current scaling or device binding",
        "source/load compliance, offset and finite bandwidth are not modeled",
        "no fabrication or measured-device evidence",
    )
    name = "KCL exact sum route" if operation == "sum" else "KCL exact difference route"
    return KCLSumRoute(
        id="sum-kcl",
        name=name,
        description=(
            "A declared Kirchhoff current-law junction computes a normalized sum; "
            "the difference mode negates the second input with exact-core glue."
        ),
        components=components,
        ports=ports,
        parameters={"operation": operation, "law": "total = a + b" if operation == "sum" else "total = a - b"},
        program=program,
        operation=operation,
        gaps=gaps,
    )


@dataclass(frozen=True)
class FluidSumRun:
    """Exact two-input evaluation of the fluid pipe-junction route."""

    route_id: str
    operation: str
    input_a: Q
    input_b: Q
    result: Q
    expected: Q
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route_id,
            "kind": "exact-fluid-sum",
            "operation": self.operation,
            "a": q_to_json(self.input_a),
            "b": q_to_json(self.input_b),
            "result": q_to_json(self.result),
            "expected": q_to_json(self.expected),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class FluidSumRoute:
    """A declared fluid continuity junction with an exact sum program."""

    id: str
    name: str
    description: str
    components: tuple[RouteComponent, ...]
    ports: tuple[PortSpec, ...]
    parameters: Mapping[str, Any]
    program: Program
    operation: str
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "kind": "exact-fluid-sum",
            "name": self.name,
            "description": self.description,
            "status": "exact route model",
            "components": [component.as_dict() for component in self.components],
            "ports": [port.as_dict() for port in self.ports],
            "parameters": _json(dict(self.parameters)),
            "program": self.program.as_dict(),
            "topology_audit": audit_route_topology(self),
            "typed_graph": typed_graph(self).as_dict(),
            "gaps": list(self.gaps),
        }

    def simulate(
        self,
        input_a: Any = Fraction(1, 2),
        input_b: Any = Fraction(1, 3),
    ) -> FluidSumRun:
        """Evaluate the declared fluid sum or difference exactly."""
        a = _as_fraction(input_a, "q_a")
        b = _as_fraction(input_b, "q_b")
        values = run_program(self.program, [{"q_a": a, "q_b": b}])[0]
        result = values["q_total"]
        expected = a + b if self.operation == "sum" else a - b
        return FluidSumRun(
            route_id=self.id,
            operation=self.operation,
            input_a=a,
            input_b=b,
            result=result,
            expected=expected,
            passed=result == expected,
        )

    def render_text(self) -> str:
        lines = [
            "=" * 78,
            "PHYSICAL ROUTE ASSEMBLY",
            "=" * 78,
            f"Route: {self.name}",
            "Status: exact route model; no device binding or fabrication netlist",
            "",
            "Typed components",
        ]
        for component in self.components:
            lines.append(
                f"  {component.role:<12} ¢_{component.op:<9} "
                f"{component.contract.material}"
            )
            lines.append(f"    law: {component.contract.law}")
            lines.append(
                "    ports: "
                + ", ".join(
                    f"{port.name}:{port.direction}:{port.kind}"
                    for port in component.contract.ports
                )
            )
        lines.append("")
        lines.append("Exact route graph")
        lines.append("  inputs: " + ", ".join(self.program.inputs))
        for index, instruction in enumerate(self.program.instructions, start=1):
            lines.append(
                f"  {index}. {instruction.out} <- ¢_{instruction.op}"
                f"({', '.join(instruction.inputs)})"
            )
        lines.append("  outputs: " + ", ".join(self.program.outputs))
        lines.append("")
        lines.append("Declared gaps")
        for gap in self.gaps:
            lines.append(f"  - {gap}")
        return "\n".join(lines)


def opamp_sum_route(*, operation: str = "sum") -> KCLSumRoute:
    """Assemble the declared ideal op-amp sum/difference route.

    Sum is one non-inverting summing amplifier with a matched input network
    (1/2 attenuation per input) and closed-loop gain 2. Difference is an
    inverting buffer on the second input followed by the same exact summing
    block. The route is a declared ideal block model, not a device binding.
    """
    if operation not in {"sum", "difference"}:
        raise CentError(ErrorCode.INVALID_INPUT, f"unknown op-amp operation: {operation}")
    if operation == "sum":
        instructions = (Instruction("sum", ("a", "b"), "total"),)
        components = (
            RouteComponent(
                "summing-amp",
                "sum",
                ("a", "b"),
                ("total",),
                {},
                OPAMP_SUM_CONTRACT,
            ),
        )
        name = "Op-amp summing amplifier exact sum route"
        description = (
            "A declared ideal non-inverting summing amplifier with a matched "
            "input network and closed-loop gain 2 computes total = a + b."
        )
        law = "total = a + b via a matched input network and closed-loop gain 2"
    else:
        instructions = (
            Instruction("neg", ("b",), "neg_b"),
            Instruction("sum", ("a", "neg_b"), "total"),
        )
        components = (
            RouteComponent(
                "inverting-input",
                "neg",
                ("b",),
                ("neg_b",),
                {},
                OPAMP_INVERT_CONTRACT,
            ),
            RouteComponent(
                "summing-amp",
                "sum",
                ("a", "neg_b"),
                ("total",),
                {},
                OPAMP_SUM_CONTRACT,
            ),
        )
        name = "Op-amp summing amplifier exact difference route"
        description = (
            "A declared ideal inverting buffer negates the second normalized "
            "voltage; the summing amplifier then computes total = a - b."
        )
        law = "total = a - b via an inverting buffer and the exact summing amplifier"
    program = Program(
        name=f"sum-opamp-{operation}",
        inputs={"a": NUMERIC, "b": NUMERIC},
        instructions=instructions,
        outputs={"total": "total"},
    )
    analyse(program)
    ports = (
        PortSpec("a", "input", "numeric", "any exact rational", "first normalized voltage"),
        PortSpec("b", "input", "numeric", "any exact rational", "second normalized voltage"),
        PortSpec(
            "total",
            "output",
            "numeric",
            "a + b or a - b",
            "normalized voltage result",
        ),
    )
    gaps = (
        "declared ideal op-amp blocks only; no device values or reference netlist",
        "resistor mismatch, finite gain/bandwidth, offset, slew and source loading are not modeled",
        "no fabrication or measured-device evidence",
    )
    if operation == "difference":
        gaps = (
            "difference uses an ideal inverting buffer and matched resistor ratios",
            *gaps,
        )
    return KCLSumRoute(
        id="sum-opamp",
        name=name,
        description=description,
        components=components,
        ports=ports,
        parameters={
            "operation": operation,
            "law": law,
            "carrier": "normalized voltage",
            "input_attenuation": Fraction(1, 2),
            "closed_loop_gain": 2,
        },
        program=program,
        operation=operation,
        gaps=gaps,
    )


def fluid_sum_route(*, operation: str = "sum") -> FluidSumRoute:
    """Assemble the declared fluid pipe-junction sum or difference route.

    The substrate row is the non-electrical ``sum`` continuity entry:
    ``ΣQ_in = ΣQ_out``.  Inputs and the result are normalized exact flows; no
    pressure/flow scaling, device values or netlist are invented.  Difference
    is a declared reversed port followed by the same exact continuity junction.
    """
    if operation not in {"sum", "difference"}:
        raise CentError(ErrorCode.INVALID_INPUT, f"unknown fluid operation: {operation}")
    if operation == "sum":
        instructions = (Instruction("sum", ("q_a", "q_b"), "q_total"),)
        components = (
            RouteComponent(
                "junction",
                "sum",
                ("q_a", "q_b"),
                ("q_total",),
                {},
                FLUID_SUM_CONTRACT,
            ),
        )
        name = "Fluid pipe-junction exact sum route"
        description = (
            "A declared flow-conservation junction computes the normalized sum "
            "q_total = q_a + q_b, selected from the non-electrical sum substrate row."
        )
        law = "q_total = q_a + q_b"
        output_range = "q_a + q_b"
    else:
        instructions = (
            Instruction("neg", ("q_b",), "q_neg_b"),
            Instruction("sum", ("q_a", "q_neg_b"), "q_total"),
        )
        components = (
            RouteComponent(
                "reverse-port",
                "neg",
                ("q_b",),
                ("q_neg_b",),
                {},
                FLUID_REVERSE_CONTRACT,
            ),
            RouteComponent(
                "junction",
                "sum",
                ("q_a", "q_neg_b"),
                ("q_total",),
                {},
                FLUID_SUM_CONTRACT,
            ),
        )
        name = "Fluid reversed-port exact difference route"
        description = (
            "A declared reversed pipe port negates the second normalized flow; "
            "the same flow-conservation junction then computes q_total = q_a - q_b."
        )
        law = "q_total = q_a - q_b via a reversed port and the exact junction"
        output_range = "q_a - q_b"
    program = Program(
        name=f"sum-fluid-{operation}",
        inputs={"q_a": NUMERIC, "q_b": NUMERIC},
        instructions=instructions,
        outputs={"q_total": "q_total"},
    )
    analyse(program)
    ports = (
        PortSpec("q_a", "input", "numeric", "any exact rational", "first normalized flow"),
        PortSpec("q_b", "input", "numeric", "any exact rational", "second normalized flow"),
        PortSpec("q_total", "output", "numeric", output_range, "normalized flow result"),
    )
    gaps = (
        "declared fluid pipe-junction topology only; no pressure/flow scaling or device binding",
        "leakage, compressibility, junction loss and finite response are not modeled",
        "no fabrication or measured-flow evidence",
    )
    if operation == "difference":
        gaps = (
            "declared reversed-port sign convention only; no valve, pump or device binding",
            *gaps,
        )
    return FluidSumRoute(
        id="sum-fluid",
        name=name,
        description=description,
        components=components,
        ports=ports,
        parameters={
            "operation": operation,
            "law": law,
            "carrier": "normalized volumetric flow",
        },
        program=program,
        operation=operation,
        gaps=gaps,
    )


def render_fluid_sum_route(route: FluidSumRoute) -> str:
    return route.render_text()


def render_sum_run(run: KCLSumRun) -> str:
    return "\n".join(
        [
            "Exact route simulation",
            f"  operation: {run.operation}",
            f"  a: {run.input_a}",
            f"  b: {run.input_b}",
            f"  result: {run.result}",
            f"  expected: {run.expected}",
            f"  passed: {run.passed}",
        ]
    )


def _decimal(value: Q, places: int = 12) -> str:
    """Deterministic decimal truncation using integer arithmetic only."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    scaled = value.numerator * scale // value.denominator
    return f"{sign}{scaled // scale}.{scaled % scale:0{places}d}"


def render_sqrt_route(route: SqrtRoute) -> str:
    """Render the log-domain route plan for the terminal."""
    lines = [
        "=" * 78,
        "PHYSICAL ROUTE ASSEMBLY",
        "=" * 78,
        f"Route: {route.name}",
        "Status: exact certified-enclosure route; no fabrication netlist",
        "",
        "Typed components",
    ]
    for component in route.components:
        lines.append(
            f"  {component.role:<12} ¢_{component.op:<9} "
            f"{component.contract.material}"
        )
        lines.append(f"    law: {component.contract.law}")
        lines.append(
            "    ports: "
            + ", ".join(
                f"{port.name}:{port.direction}:{port.kind}"
                for port in component.contract.ports
            )
        )
    lines.append("")
    lines.append("Exact route graph")
    lines.append("  inputs: " + ", ".join(route.program.inputs))
    for index, instruction in enumerate(route.program.instructions, start=1):
        lines.append(
            f"  {index}. {instruction.out} <- ¢_{instruction.op}"
            f"({', '.join(instruction.inputs)})"
        )
    lines.append("  outputs: " + ", ".join(route.program.outputs))
    lines.append("")
    lines.append("Declared gaps")
    for gap in route.gaps:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


def render_sqrt_run(run: SqrtRun) -> str:
    """Render a certified-enclosure route simulation for the CLI."""
    if run.overlap is None:
        overlap = "none"
    else:
        overlap = f"[{_decimal(run.overlap.lo, 16)}, {_decimal(run.overlap.hi, 16)}]"
    lines = [
        "Exact certified-enclosure simulation",
        f"  input: {run.input_value}",
        f"  precision: {run.precision} bits",
        f"  tolerance: {run.tolerance}",
        f"  route root: ≈ [{_decimal(run.root.lo, 16)}, {_decimal(run.root.hi, 16)}]",
        f"  independent sqrt bracket: ≈ [{_decimal(run.checker.lo, 16)}, {_decimal(run.checker.hi, 16)}]",
        f"  overlap: {overlap}",
        f"  root width: {_decimal(run.root.width, 18)}",
        f"  passed: {run.passed}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Op-amp + analog-multiplier feedback square-root route
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeedbackSqrtRun:
    """Steady-state solve of the finite-gain multiplier feedback loop."""

    route_id: str
    input_value: Q
    amplifier_gain: Q
    multiplier_gain: Q
    tolerance: Q
    precision: int
    iterations: int
    root: Interval
    checker: Interval
    ideal: Interval
    overlap: Interval | None
    gain_error: Q
    residual: Q
    passed: bool
    trace: tuple[Mapping[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route_id,
            "kind": "certified-algebraic-feedback",
            "input": q_to_json(self.input_value),
            "amplifier_gain": q_to_json(self.amplifier_gain),
            "multiplier_gain": q_to_json(self.multiplier_gain),
            "tolerance": q_to_json(self.tolerance),
            "precision": self.precision,
            "iterations": self.iterations,
            "root": _json(self.root),
            "checker": _json(self.checker),
            "ideal": _json(self.ideal),
            "overlap": _json(self.overlap) if self.overlap is not None else None,
            "root_width": q_to_json(self.root.width),
            "checker_width": q_to_json(self.checker.width),
            "gain_error": q_to_json(self.gain_error),
            "residual": q_to_json(self.residual),
            "passed": self.passed,
            "trace": [_json(item) for item in self.trace],
        }


@dataclass(frozen=True)
class FeedbackSqrtRoute:
    """A finite-gain algebraic feedback route with an exact steady-state solve."""

    id: str
    name: str
    description: str
    components: tuple[RouteComponent, ...]
    ports: tuple[PortSpec, ...]
    parameters: Mapping[str, Any]
    amplifier_gain: Q
    multiplier_gain: Q
    tolerance: Q
    precision: int
    iterations: int
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "kind": "certified-algebraic-feedback",
            "name": self.name,
            "description": self.description,
            "status": "exact steady-state algebraic route",
            "components": [component.as_dict() for component in self.components],
            "ports": [port.as_dict() for port in self.ports],
            "parameters": _json(dict(self.parameters)),
            "program": None,
            "solver": {
                "method": "monotone bisection on the finite-gain feedback residual",
                "residual": "A * (x - k * y^2) - y",
                "ops": ["mult", "amp", "sum"],
                "iterations": self.iterations,
                "checker": "independent quadratic formula with sqrt_q enclosure",
            },
            "topology_audit": audit_route_topology(self),
            "typed_graph": typed_graph(self).as_dict(),
            "gaps": list(self.gaps),
        }

    def simulate(self, input_value: Any = Fraction(2)) -> FeedbackSqrtRun:
        """Solve the finite-gain feedback equilibrium by exact bisection.

        The loop law is ``A*(x - k*y^2) - y = 0``.  It is monotone for
        ``y >= 0`` because ``A,k > 0``.  Bisection uses only exact rational
        midpoints, so it does not suffer the denominator growth of an explicit
        Euler iteration.  The independent checker uses the quadratic formula
        with an exact ``sqrt_q`` enclosure; that checker is not an instruction
        in the route.
        """
        x = _as_fraction(input_value, "input")
        if x <= 0:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                f"op-amp feedback sqrt input must be positive, got {x}",
            )

        a = self.amplifier_gain
        k = self.multiplier_gain

        def residual(y: Q) -> Q:
            return a * (x - k * y * y) - y

        lo = Fraction(0)
        hi = max(Fraction(1), x / k)
        f_lo = residual(lo)
        f_hi = residual(hi)
        if not (f_lo > 0 and f_hi < 0):
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                "the declared feedback bracket does not straddle the root",
                detail={"lo": f_lo, "hi": f_hi},
            )

        trace: list[Mapping[str, Any]] = []
        for step in range(1, self.iterations + 1):
            mid = (lo + hi) / 2
            f_mid = residual(mid)
            if step <= 4 or step % max(1, self.iterations // 8) == 0 or step == self.iterations:
                trace.append(
                    {
                        "iteration": step,
                        "lo": lo,
                        "hi": hi,
                        "mid": mid,
                        "residual": f_mid,
                    }
                )
            if f_mid == 0:
                lo = hi = mid
                break
            if f_mid > 0:
                lo = mid
            else:
                hi = mid

        root = Interval(lo, hi)
        # Positive root of A*k*y^2 + y - A*x = 0.
        disc = 1 + 4 * a * a * k * x
        checker = (sqrt_q(disc, self.precision) - 1) / (2 * a * k)
        # The unity-gain route targets sqrt(x); with a declared multiplier
        # gain k the normalized target is sqrt(x / k).
        ideal = sqrt_q(x / k, self.precision)
        overlap = _overlap(root, checker)
        gain_error = abs(root.midpoint - ideal.midpoint)
        residual_value = abs(residual(root.midpoint))
        passed = (
            overlap is not None
            and root.width <= self.tolerance
            and gain_error <= self.tolerance
        )
        return FeedbackSqrtRun(
            route_id=self.id,
            input_value=x,
            amplifier_gain=a,
            multiplier_gain=k,
            tolerance=self.tolerance,
            precision=self.precision,
            iterations=self.iterations,
            root=root,
            checker=checker,
            ideal=ideal,
            overlap=overlap,
            gain_error=gain_error,
            residual=residual_value,
            passed=passed,
            trace=tuple(trace),
        )


def opamp_multiplier_sqrt_route(
    *,
    amplifier_gain: Any = Fraction(1_000_000),
    multiplier_gain: Any = Fraction(1),
    tolerance: Any = Fraction(1, 1_000_000),
    precision: int = 64,
    iterations: int = 64,
) -> FeedbackSqrtRoute:
    """Assemble the op-amp + analog-multiplier feedback square-root route.

    The loop is evaluated at steady state.  It is not a transient simulation:
    it solves the algebraic equilibrium that the high-gain amplifier drives the
    multiplier feedback toward.  The finite amplifier gain is explicit, so the
    result differs from the ideal square root by a reported ``gain_error``.
    """
    a = _as_fraction(amplifier_gain, "amplifier_gain")
    k = _as_fraction(multiplier_gain, "multiplier_gain")
    tol = _as_fraction(tolerance, "tolerance")
    if a <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "amplifier_gain must be positive")
    if k <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "multiplier_gain must be positive")
    if tol <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "tolerance must be positive")
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    if not 1 <= precision <= 64:
        raise CentError(ErrorCode.DOMAIN_ERROR, "precision must be in 1..64 bits")
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        raise CentError(ErrorCode.TYPE_ERROR, "iterations must be an integer")
    if not 1 <= iterations <= 128:
        raise CentError(ErrorCode.DOMAIN_ERROR, "iterations must be in 1..128")

    components = (
        RouteComponent(
            "multiplier",
            "mult",
            ("drive", "drive"),
            ("square",),
            {"gain": k},
            MULT_CONTRACT,
        ),
        RouteComponent(
            "error_amp",
            "amp",
            ("error",),
            ("drive",),
            {"gain": a},
            AMP_CONTRACT,
        ),
    )
    ports = (
        PortSpec("x", "input", "numeric", "x > 0", "normalized input voltage"),
        PortSpec(
            "root",
            "output",
            "interval",
            "certified enclosure of the finite-gain equilibrium",
            "op-amp drive / square-root output",
        ),
    )
    gaps = (
        "steady-state algebraic equilibrium only; no transient settling, slew or stability analysis",
        "normalized multiplier gain; the declared device binding is a reference design, not an AD633 /10 netlist",
        "finite amplifier gain intentionally leaves a small bias from the ideal square root",
        "no noise, offset, nonlinearity or fabrication evidence",
    )
    return FeedbackSqrtRoute(
        id="sqrt-opamp-multiplier",
        name="Op-amp + analog-multiplier square-root route",
        description=(
            "A high-gain error amplifier drives a unity-gain analog multiplier "
            "until the multiplier output equals the input; the finite-gain "
            "equilibrium is solved exactly and checked against an independent "
            "quadratic enclosure."
        ),
        components=components,
        ports=ports,
        parameters={
            "amplifier_gain": a,
            "multiplier_gain": k,
            "tolerance": tol,
            "precision": precision,
            "iterations": iterations,
            "residual": "A * (x - k * y^2) - y",
        },
        amplifier_gain=a,
        multiplier_gain=k,
        tolerance=tol,
        precision=precision,
        iterations=iterations,
        gaps=gaps,
    )


def render_feedback_sqrt_route(route: FeedbackSqrtRoute) -> str:
    """Render the algebraic feedback route plan for the terminal."""
    lines = [
        "=" * 78,
        "PHYSICAL ROUTE ASSEMBLY",
        "=" * 78,
        f"Route: {route.name}",
        "Status: exact steady-state algebraic route; no fabrication netlist",
        "",
        "Typed components",
    ]
    for component in route.components:
        lines.append(
            f"  {component.role:<12} ¢_{component.op:<9} "
            f"{component.contract.material}"
        )
        lines.append(f"    law: {component.contract.law}")
        lines.append(
            "    ports: "
            + ", ".join(
                f"{port.name}:{port.direction}:{port.kind}"
                for port in component.contract.ports
            )
        )
    lines.append("")
    lines.append("Algebraic feedback law")
    lines.append("  residual: A * (x - k * y^2) - y = 0")
    lines.append(f"  amplifier gain: {route.amplifier_gain}")
    lines.append(f"  multiplier gain: {route.multiplier_gain}")
    lines.append("  solver: exact monotone bisection; independent quadratic check")
    lines.append("  no sqrt instruction in the route")
    lines.append("")
    lines.append("Declared gaps")
    for gap in route.gaps:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


GLUE_OPS = frozenset({"sum", "neg", "sat"})


def audit_route_topology(route: Any) -> dict[str, Any]:
    """Check structural feasibility of any assembled route graph.

    This is a port/role/parameter audit, not a physical placement or circuit
    simulator.  It accepts the three declared route shapes, checks that each
    instance matches its typed contract, that program wires are declared, and
    that glue operations are clearly separated from physical components.  A
    malformed or unsupported composition returns ``gap``.
    """
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "status": "pass" if passed else "gap", "detail": detail})
        if not passed:
            failures.append(name)

    components = tuple(getattr(route, "components", ()))
    ports = tuple(getattr(route, "ports", ()))
    if not components:
        record("typed components", False, "route declares no typed components")
        return {
            "status": "gap",
            "checked": len(checks),
            "failures": failures,
            "checks": checks,
            "detail": "topology audit failed: no typed components",
        }

    roles = [component.role for component in components]
    record(
        "unique component roles",
        len(roles) == len(set(roles)),
        "every component instance has one unique role"
        if len(roles) == len(set(roles))
        else "duplicate component roles: " + ", ".join(sorted({role for role in roles if roles.count(role) > 1})),
    )

    component_ok = True
    parameter_ok = True
    for component in components:
        contract = component.contract
        input_ports = [port for port in contract.ports if port.direction == "input"]
        output_ports = [port for port in contract.ports if port.direction == "output"]
        if (
            not input_ports
            or not output_ports
            or len(input_ports) != len(component.inputs)
            or len(output_ports) != len(component.outputs)
            or not component.inputs
            or not component.outputs
        ):
            component_ok = False
        declared_parameters = {parameter.name for parameter in contract.parameters}
        if not set(component.parameters).issubset(declared_parameters):
            parameter_ok = False
        if any(value is None for value in component.parameters.values()):
            parameter_ok = False
    record(
        "contract port coverage",
        component_ok,
        "every instance has one wire per typed contract port and a non-empty output"
        if component_ok
        else "a component instance does not match its contract port arity",
    )
    record(
        "contract parameter coverage",
        parameter_ok,
        "every instance parameter is declared by its contract"
        if parameter_ok
        else "a component instance has an undeclared or missing parameter",
    )

    program = getattr(route, "program", None)
    if program is None:
        record(
            "route program",
            True,
            "no exact-core program; the route is a declared steady-state algebraic composition",
        )
    else:
        try:
            analysis = analyse(program)
            declared_wires = set(program.inputs) | {
                instruction.out for instruction in program.instructions
            }
            outputs = set(program.outputs.values())
            wire_ok = all(
                wire in declared_wires
                for instruction in program.instructions
                for wire in instruction.inputs
            ) and outputs.issubset(declared_wires)
            record(
                "program wire coverage",
                wire_ok and analysis is not None,
                "every instruction input and route output is declared"
                if wire_ok
                else "the program references an undeclared wire",
            )
        except CentError as exc:
            record("program wire coverage", False, str(exc))

    port_names = [port.name for port in ports]
    input_ports = [port for port in ports if port.direction == "input"]
    output_ports = [port for port in ports if port.direction == "output"]
    record(
        "route port shape",
        len(port_names) == len(set(port_names)) and bool(input_ports) and bool(output_ports),
        "route ports are unique and declare both input and output"
        if len(port_names) == len(set(port_names)) and input_ports and output_ports
        else "route ports are duplicated or missing an input/output",
    )

    result = {
        "status": "pass" if not failures else "gap",
        "checked": len(checks),
        "failures": failures,
        "checks": checks,
        "detail": (
            f"{len(components)} component(s) passed structural port, parameter and wire checks"
            if not failures
            else "topology audit failed: " + ", ".join(failures)
        ),
    }
    return result


def render_feedback_sqrt_run(run: FeedbackSqrtRun) -> str:
    """Render a finite-gain feedback solve for the CLI."""
    if run.overlap is None:
        overlap = "none"
    else:
        overlap = f"[{_decimal(run.overlap.lo, 16)}, {_decimal(run.overlap.hi, 16)}]"
    return "\n".join(
        [
            "Exact algebraic-feedback simulation",
            f"  input: {run.input_value}",
            f"  amplifier gain: {run.amplifier_gain}",
            f"  multiplier gain: {run.multiplier_gain}",
            f"  iterations: {run.iterations}",
            f"  tolerance: {run.tolerance}",
            f"  root: ≈ [{_decimal(run.root.lo, 16)}, {_decimal(run.root.hi, 16)}]",
            f"  quadratic checker: ≈ [{_decimal(run.checker.lo, 16)}, {_decimal(run.checker.hi, 16)}]",
            f"  ideal sqrt(x/k) bracket: ≈ [{_decimal(run.ideal.lo, 16)}, {_decimal(run.ideal.hi, 16)}]",
            f"  overlap: {overlap}",
            f"  finite-gain error: {_decimal(run.gain_error, 18)}",
            f"  residual: {_decimal(run.residual, 18)}",
            f"  root width: {_decimal(run.root.width, 18)}",
            f"  passed: {run.passed}",
        ]
    )
