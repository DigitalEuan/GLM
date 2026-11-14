"""Program IR, static checking and feedback analysis (CentCalculus2 §7).

A :class:`Program` is a flat list of single-assignment instructions over named
wires.  The checker is deliberately strict:

* unknown primitives, unknown parameters and missing required parameters are
  rejected (``validation_error``), never ignored;
* arity is fixed per primitive;
* every input wire must be declared as a program input or produced by exactly
  one instruction;
* wire kinds must match the primitive's accepted kinds.  A ``numeric`` wire is
  an exact rational; a ``numeric`` consumer that declares interval closure also
  accepts a certified ``interval`` wire;
* a cycle is only well founded if every back edge is produced by a stateful
  primitive, otherwise it is a combinational loop and rejected
  (``cycle_detected``).

The analysis is static: it does not evaluate anything.  Evaluation lives in
:mod:`cent_compiler.evaluator`, and back-edge wires are read from the previous
tick there.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Iterable, Mapping

from .exact import CentError, ErrorCode, q, q_from_json, q_to_json
from .interval import Interval
from .vocabulary import (
    BIT,
    FIELD,
    INPUT_KINDS,
    NUMERIC,
    OUTPUT_KIND,
    PORT,
    STATEFUL_OPS,
    TWO_FORM,
    VECTOR,
    VECTOR_FIELD,
    canonical_op,
)

#: Output kind used by the certified-transcendental primitives.
INTERVAL = "interval"

#: Kinds a wire may carry, as produced by :func:`kind_of`.
VALUE_KINDS = frozenset({NUMERIC, INTERVAL, PORT, FIELD, VECTOR_FIELD, TWO_FORM, VECTOR, BIT})

#: Numeric primitives whose handlers also accept a certified interval argument.
INTERVAL_CLOSED_OPS = frozenset({
    "sum", "neg", "mult", "scale", "accum", "rate", "recip", "div", "sqrt",
    "eq", "exp", "log",
})

#: ``op -> (min_inputs, max_inputs)``; ``None`` means unbounded.
ARITY: dict[str, tuple[int, int | None]] = {
    "sum": (1, None),
    "neg": (1, 1),
    "mult": (1, None),
    "scale": (1, 1),
    "accum": (1, 1),
    "rate": (1, 1),
    "wrap": (1, 1),
    "spatial": (1, 1),
    "exp": (1, 1),
    "log": (1, 1),
    "sat": (1, 1),
    "hysteresis": (1, 1),
    "delay": (1, 1),
    "grad": (1, 1),
    "div_spatial": (1, 1),
    "curl": (1, 1),
    "laplacian": (1, 1),
    "boundary": (1, 1),
    "junction_0": (2, None),
    "junction_1": (2, None),
    "gyrator": (1, 1),
    "transformer": (1, 1),
    "dissipate": (1, 1),
    "store_pot": (1, 1),
    "store_kin": (1, 1),
    "transduce": (1, 1),
    "noise": (0, 0),
    "quantize": (1, 1),
    "entropy": (1, 1),
    "recip": (1, 1),
    "div": (2, 2),
    "sqrt": (1, 1),
    "eq": (2, 2),
    "translinear": (1, None),
    "state_space": (1, 1),
    "pid": (1, 1),
    "phase_locked_loop": (1, 1),
    "transmission_line": (1, 1),
    "kalman_observer": (1, 1),
    "thermo_electric": (1, 1),
    "delta_sigma_modulator": (1, 1),
}

#: ``op -> {parameter: required}``.  Unknown parameters are rejected.
PARAM_SPEC: dict[str, dict[str, bool]] = {
    "sum": {},
    "neg": {},
    "mult": {},
    "scale": {"factor": True},
    "accum": {},
    "rate": {"dt": True},
    "wrap": {"period": True},
    "spatial": {"index": False},
    "exp": {"precision": False},
    "log": {"precision": False},
    "sat": {"lo": True, "hi": True},
    "hysteresis": {"lower": True, "upper": True, "initial": False},
    "delay": {"ticks": True, "initial": False},
    "grad": {"h": False},
    "div_spatial": {"h": False, "index": True},
    "curl": {"h": False, "index": True},
    "laplacian": {"h": False, "axes": False, "index": True},
    "boundary": {
        "shape": True,
        "spacing": False,
        "kind": False,
        "value": False,
        "alpha": False,
        "beta": False,
        "gamma": False,
    },
    "junction_0": {"resolved": False},
    "junction_1": {"resolved": False},
    "gyrator": {"resistance": True},
    "transformer": {"ratio": True},
    "dissipate": {"resistance": True, "temperature": True},
    "store_pot": {"capacitance": True, "dt": True},
    "store_kin": {"inductance": True, "dt": True},
    "transduce": {"ratio": True, "efficiency": False},
    "noise": {"amplitude": True, "seed": False},
    "quantize": {"quantum": True},
    "entropy": {"temperature": True},
    "recip": {},
    "div": {},
    "sqrt": {"precision": False},
    "eq": {},
    "translinear": {"exponents": True},
    "state_space": {"A": True, "B": True, "C": True, "D": True},
    "pid": {"kp": True, "ki": True, "kd": True, "dt": True, "initial": False},
    "phase_locked_loop": {
        "center_frequency": True,
        "gain": True,
        "dt": True,
        "initial_phase": False,
    },
    "transmission_line": {"segments": True, "reflection": False, "initial": False},
    "kalman_observer": {
        "process_variance": True,
        "measurement_variance": True,
        "initial_x": False,
        "initial_p": False,
    },
    "thermo_electric": {"seebeck": True, "resistance": True, "temperature": True},
    "delta_sigma_modulator": {"order": False, "threshold": True},
}


def _json_ready(value: Any) -> Any:
    """Encode exact rationals (recursively) as ``{"num", "den"}`` objects."""
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Mapping):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    return value


def decode_exact(value: Any) -> Any:
    """Decode ``{"num", "den"}`` objects produced by :func:`_json_ready`."""
    if isinstance(value, Mapping):
        if set(value) == {"num", "den"}:
            return q_from_json(value)
        return {k: decode_exact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [decode_exact(v) for v in value]
    return value


@dataclass(frozen=True)
class Instruction:
    """One single-assignment instruction: ``out <- op(inputs, params)``."""

    op: str
    inputs: tuple[str, ...] = ()
    out: str = ""
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "op", canonical_op(self.op))
        object.__setattr__(self, "inputs", tuple(self.inputs))
        object.__setattr__(self, "params", dict(self.params))
        if not self.out:
            raise CentError(ErrorCode.VALIDATION_ERROR, "instruction has no output wire")

    def as_dict(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "inputs": list(self.inputs),
            "out": self.out,
            "params": _json_ready(dict(self.params)),
        }


@dataclass(frozen=True)
class Program:
    """A checked-on-demand sequence of instructions over named wires."""

    name: str
    inputs: Mapping[str, str]
    instructions: tuple[Instruction, ...]
    outputs: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", dict(self.inputs))
        object.__setattr__(self, "outputs", dict(self.outputs))
        object.__setattr__(
            self,
            "instructions",
            tuple(
                i if isinstance(i, Instruction) else Instruction(**i)
                for i in self.instructions
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "cent-program/1",
            "name": self.name,
            "inputs": dict(self.inputs),
            "instructions": [i.as_dict() for i in self.instructions],
            "outputs": dict(self.outputs),
        }


@dataclass(frozen=True)
class Analysis:
    """Static facts about a program."""

    kinds: Mapping[str, str]
    order: tuple[int, ...]
    back_edges: Mapping[int, frozenset[str]]

    @property
    def has_feedback(self) -> bool:
        return bool(self.back_edges)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kinds": dict(self.kinds),
            "order": list(self.order),
            "back_edges": {str(k): sorted(v) for k, v in self.back_edges.items()},
        }


def accepts_kind(op: str, kind: str) -> bool:
    """Whether instruction ``op`` accepts a wire of ``kind``."""
    declared = INPUT_KINDS[op]
    if kind in declared:
        return True
    return kind == INTERVAL and op in INTERVAL_CLOSED_OPS and NUMERIC in declared


def _check_params(instr: Instruction) -> None:
    spec = PARAM_SPEC[instr.op]
    unknown = set(instr.params) - set(spec)
    if unknown:
        raise CentError(
            ErrorCode.VALIDATION_ERROR,
            f"{instr.op}: unknown parameter(s) {sorted(unknown)}",
            where=instr.out,
        )
    missing = [name for name, required in spec.items() if required and name not in instr.params]
    if missing:
        raise CentError(
            ErrorCode.VALIDATION_ERROR,
            f"{instr.op}: missing required parameter(s) {missing}",
            where=instr.out,
        )


def _check_declarations(program: Program) -> None:
    for wire, kind in program.inputs.items():
        if kind not in VALUE_KINDS:
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                f"program input {wire!r} declares unknown kind {kind!r}",
            )

    seen: dict[str, int] = {}
    for idx, instr in enumerate(program.instructions):
        if instr.out in program.inputs:
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                f"instruction writes over program input {instr.out!r}",
                where=instr.out,
            )
        if instr.out in seen:
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                f"wire {instr.out!r} assigned twice (single-assignment form)",
                where=instr.out,
            )
        seen[instr.out] = idx
        if instr.op not in ARITY:
            raise CentError(
                ErrorCode.UNSUPPORTED, f"unknown ¢ primitive {instr.op!r}", where=instr.out
            )
        low, high = ARITY[instr.op]
        if len(instr.inputs) < low or (high is not None and len(instr.inputs) > high):
            bound = f"{low}" if low == high else f"{low}..{high or 'n'}"
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                f"{instr.op}: expected {bound} input wire(s), got {len(instr.inputs)}",
                where=instr.out,
            )
        _check_params(instr)

    for name, wire in program.outputs.items():
        if wire not in program.inputs and wire not in seen:
            raise CentError(
                ErrorCode.VALIDATION_ERROR,
                f"program output {name!r} refers to unknown wire {wire!r}",
            )


def _wire_kinds(program: Program) -> dict[str, str]:
    kinds = dict(program.inputs)
    for instr in program.instructions:
        kinds[instr.out] = OUTPUT_KIND[instr.op]
    return kinds


def _check_wire_kinds(program: Program, kinds: Mapping[str, str]) -> None:
    for instr in program.instructions:
        for wire in instr.inputs:
            if wire not in kinds:
                raise CentError(
                    ErrorCode.VALIDATION_ERROR,
                    f"{instr.op}: input wire {wire!r} is neither a program input "
                    "nor produced by an instruction",
                    where=instr.out,
                )
            if not accepts_kind(instr.op, kinds[wire]):
                raise CentError(
                    ErrorCode.TYPE_ERROR,
                    f"{instr.op}: wire {wire!r} carries {kinds[wire]!r}, "
                    f"which this primitive does not accept",
                    where=instr.out,
                )


def _schedule(program: Program) -> tuple[tuple[int, ...], dict[int, frozenset[str]]]:
    instrs = program.instructions
    producers = {instr.out: idx for idx, instr in enumerate(instrs)}
    known = set(program.inputs)
    remaining = list(range(len(instrs)))
    order: list[int] = []
    back: dict[int, frozenset[str]] = {}

    while remaining:
        progressed = False
        for idx in list(remaining):
            if all(wire in known for wire in instrs[idx].inputs):
                order.append(idx)
                known.add(instrs[idx].out)
                remaining.remove(idx)
                progressed = True
        if progressed:
            continue
        if not remaining:
            break
        # No instruction is fully ready: a feedback back edge must carry the
        # value from the previous tick, and only a stateful producer has one.
        chosen = None
        for idx in remaining:
            missing = [w for w in instrs[idx].inputs if w not in known]
            if missing and all(
                w in producers and instrs[producers[w]].op in STATEFUL_OPS for w in missing
            ):
                chosen = idx
                break
        if chosen is None:
            blocked = sorted({w for idx in remaining for w in instrs[idx].inputs if w not in known})
            raise CentError(
                ErrorCode.CYCLE_DETECTED,
                "combinational cycle: every back edge must be produced by a stateful primitive",
                detail={"unresolved_wires": blocked},
            )
        back[chosen] = frozenset(w for w in instrs[chosen].inputs if w not in known)
        order.append(chosen)
        known.add(instrs[chosen].out)
        remaining.remove(chosen)

    return tuple(order), back


def analyse(program: Program) -> Analysis:
    """Validate ``program`` and return its static analysis."""
    _check_declarations(program)
    kinds = _wire_kinds(program)
    _check_wire_kinds(program, kinds)
    order, back = _schedule(program)
    return Analysis(kinds=kinds, order=order, back_edges=back)


def kind_of(value: Any) -> str:
    """Runtime kind of a wire value; raises on values outside the type system."""
    from .exact import Q
    from .geometry import ScalarField, TwoForm, VectorField
    from .interval import Interval
    from .port import PhysicalPort

    if isinstance(value, bool):
        return BIT
    if isinstance(value, int) and value in (0, 1):
        return BIT
    if isinstance(value, Q):
        return NUMERIC
    if isinstance(value, Interval):
        return INTERVAL
    if isinstance(value, PhysicalPort):
        return PORT
    if isinstance(value, VectorField):
        return VECTOR_FIELD
    if isinstance(value, TwoForm):
        return TWO_FORM
    if isinstance(value, ScalarField):
        return FIELD
    if isinstance(value, tuple) and all(isinstance(x, Q) for x in value):
        return VECTOR
    raise CentError(
        ErrorCode.TYPE_ERROR,
        f"wire value of type {type(value).__name__} is outside the ¢ type system",
    )


def coerce_input(value: Any, kind: str, where: str | None = None) -> Any:
    """Coerce a caller-supplied value to a declared program-input kind.

    A ``numeric`` wire accepts ``int``, ``Fraction`` and exact decimal strings;
    a float is rejected because the core has no binary floating point.  A
    certified interval is passed through: evaluation decides whether the
    consuming primitive is interval-closed.
    """
    if kind == NUMERIC:
        if isinstance(value, Interval):
            return value
        if isinstance(value, Fraction):
            return value
        if isinstance(value, bool):
            raise CentError(
                ErrorCode.TYPE_ERROR, "a bool is a bit, not an exact numeric wire", where
            )
        if isinstance(value, (int, str)):
            return q(value, where)
        raise CentError(
            ErrorCode.TYPE_ERROR,
            f"numeric wire cannot carry {type(value).__name__}; pass an exact rational",
            where,
        )
    require_kind(value, kind, where)
    return value


PROGRAM_SCHEMA = "cent-program/1"


def program_from_dict(data: Mapping[str, Any]) -> Program:
    """Load and validate a program encoded by :meth:`Program.as_dict`."""
    if not isinstance(data, Mapping) or data.get("schema") != PROGRAM_SCHEMA:
        raise CentError(
            ErrorCode.VALIDATION_ERROR, f"expected a {PROGRAM_SCHEMA!r} document"
        )
    try:
        inputs = {str(k): str(v) for k, v in dict(data["inputs"]).items()}
        outputs = {str(k): str(v) for k, v in dict(data["outputs"]).items()}
        raw_instructions = list(data["instructions"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CentError(ErrorCode.VALIDATION_ERROR, "malformed program JSON") from exc

    instructions = []
    for raw in raw_instructions:
        try:
            params = {
                str(k): decode_exact(v) for k, v in dict(raw.get("params", {})).items()
            }
            instructions.append(
                Instruction(
                    str(raw["op"]),
                    tuple(str(i) for i in raw["inputs"]),
                    str(raw["out"]),
                    params,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CentError(ErrorCode.VALIDATION_ERROR, "malformed instruction JSON") from exc

    program = Program(
        str(data.get("name", "program")), inputs, tuple(instructions), outputs
    )
    analyse(program)
    return program


def require_kind(value: Any, expected: str, where: str | None = None) -> None:
    """Assert that ``value`` may travel on a wire declared ``expected``."""
    actual = kind_of(value)
    if actual == expected:
        return
    if expected == NUMERIC and actual == INTERVAL:
        return
    if expected == INTERVAL and actual == NUMERIC:
        # An exact rational is a degenerate certified enclosure.
        return
    raise CentError(
        ErrorCode.TYPE_ERROR,
        f"wire declared {expected!r} received {actual!r}",
        where,
    )
