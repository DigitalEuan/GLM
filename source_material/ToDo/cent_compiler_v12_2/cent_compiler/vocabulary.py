"""The expanded ¢ vocabulary: 29 atomic primitives and 12 composite macros.

Reconciliation note
-------------------
``CentCalculus2`` announces a "24-primitive" atomic vocabulary, but its Lean
``CentAtomic`` block enumerates 23 constructors and omits entries its own tier
table requires (``transform``, ``store_pot``, ``store_kin``, ``transduce``,
``quantize``, ``entropy``).  Dropping them would break the bond-graph closure
that motivates the expansion, so this implementation provides the full closed
set (29 atomics) and records the discrepancy in ``docs/extensions.md``.  The 12
composite macros match the document exactly.

Every entry carries a contract: input/output types, parameters, owned state,
domain restrictions, error cases, associated theorem (if any), and an honest
capability status.  ``tools/export_capabilities.py`` renders this registry to
machine-readable JSON.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

from .exact import ErrorCode

# ---------------------------------------------------------------------------
# Capability statuses (CentCalculus2 §12)
# ---------------------------------------------------------------------------

IMPLEMENTED_VERIFIED = "implemented_verified"
IMPLEMENTED_TESTED = "implemented_tested"
IMPLEMENTED_PROOF_PENDING = "implemented_proof_pending"
SPECIFIED_PENDING = "specified_implementation_pending"
UNSUPPORTED = "unsupported"

STATUS_ORDER = (
    IMPLEMENTED_VERIFIED,
    IMPLEMENTED_TESTED,
    IMPLEMENTED_PROOF_PENDING,
    SPECIFIED_PENDING,
    UNSUPPORTED,
)

# ---------------------------------------------------------------------------
# Wire kinds used by the program type checker
# ---------------------------------------------------------------------------

NUMERIC = "numeric"          # exact scalar or certified interval
PORT = "port"
FIELD = "field"
VECTOR_FIELD = "vector_field"
TWO_FORM = "two_form"
VECTOR = "vector"            # exact rational tuple (state-space vectors)
BIT = "bit"

#: Kinds each primitive will accept on its input wires.
INPUT_KINDS: dict[str, frozenset[str]] = {}

#: Kind produced on the output wire.
OUTPUT_KIND: dict[str, str] = {}

#: Primitives whose result depends on prior ticks (they read pre-tick slots).
STATEFUL_OPS: frozenset[str] = frozenset({
    "accum", "rate", "delay", "hysteresis",
    "store_pot", "store_kin", "noise",
    "pid", "phase_locked_loop", "transmission_line", "kalman_observer",
    "delta_sigma_modulator",
})

#: Stateful primitives that make a feedback cycle well-founded.
CYCLE_BREAKERS: frozenset[str] = STATEFUL_OPS

#: Primitives with no state and deterministic output.
PURE_OPS: frozenset[str] = frozenset()

_TIERS: dict[str, tuple[str, ...]] = {
    "classical": (
        "sum", "neg", "mult", "scale", "accum", "rate", "wrap", "spatial",
        "exp", "log", "sat", "hysteresis", "delay",
    ),
    "continuum": ("grad", "div_spatial", "curl", "laplacian", "boundary"),
    "conservative": (
        "junction_0", "junction_1", "gyrator", "transformer",
        "dissipate", "store_pot", "store_kin", "transduce",
    ),
    "stochastic_topological": ("noise", "quantize", "entropy"),
}

ATOMIC_PRIMITIVES: tuple[str, ...] = tuple(
    op for tier in _TIERS.values() for op in tier
)

COMPOSITE_PRIMITIVES: tuple[str, ...] = (
    "recip", "div", "sqrt", "eq", "translinear", "state_space",
    "pid", "phase_locked_loop", "transmission_line", "kalman_observer",
    "thermo_electric", "delta_sigma_modulator",
)

ALL_PRIMITIVES: tuple[str, ...] = ATOMIC_PRIMITIVES + COMPOSITE_PRIMITIVES

#: Compatibility aliases accepted by :func:`canonical_op`.
ALIASES: dict[str, str] = {
    "pll": "phase_locked_loop",
    "phase_locked": "phase_locked_loop",
    "sigma_delta": "delta_sigma_modulator",
    "deltasigma": "delta_sigma_modulator",
    "kalman": "kalman_observer",
    "transmissionline": "transmission_line",
    "thermoelectric": "thermo_electric",
    "junction0": "junction_0",
    "junction1": "junction_1",
    "div_spatial": "div_spatial",
}


def canonical_op(op: str) -> str:
    name = op[2:] if op.startswith("¢_") else op
    return ALIASES.get(name, name)


def tier_of(op: str) -> str:
    op = canonical_op(op)
    for tier, ops in _TIERS.items():
        if op in ops:
            return tier
    if op in COMPOSITE_PRIMITIVES:
        return "composite"
    return "unknown"


@dataclass(frozen=True)
class Contract:
    """The public contract of one primitive."""

    op: str
    kind: str                    # "atomic" | "composite"
    tier: str
    inputs: str                  # human-readable signature
    output: str
    params: str
    state: str = "none"          # owned state slot contents
    domain: str = "all exact rationals"
    errors: tuple[str, ...] = ()
    theorem: Optional[str] = None
    status: str = IMPLEMENTED_TESTED
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "op": self.op,
            "kind": self.kind,
            "tier": self.tier,
            "inputs": self.inputs,
            "output": self.output,
            "params": self.params,
            "state": self.state,
            "domain": self.domain,
            "errors": list(self.errors),
            "theorem": self.theorem,
            "status": self.status,
            "notes": self.notes,
        }


def _c(op: str, kind: str, tier: str, inputs: str, output: str, params: str,
       state: str = "none", domain: str = "all exact rationals",
       errors: tuple[str, ...] = (), theorem: Optional[str] = None,
       status: str = IMPLEMENTED_TESTED, notes: str = "") -> Contract:
    return Contract(op, kind, tier, inputs, output, params, state, domain,
                    errors, theorem, status, notes)


CONTRACTS: dict[str, Contract] = {}


def _register(c: Contract) -> None:
    CONTRACTS[c.op] = c


for c in [
    # -- classical scalar arithmetic ------------------------------------
    _c("sum", "atomic", "classical", "numeric*", "numeric", "none",
       domain="at least one input; exact rational or certified interval",
       notes="pure exact addition; the accumulator is *not* used (see ¢_accum)"),
    _c("neg", "atomic", "classical", "numeric", "numeric", "none",
       notes="signed negation. Unit complement is a separate operation "
             "(density.unit_complement), not this primitive"),
    _c("mult", "atomic", "classical", "numeric*", "numeric", "none",
       domain="exact rational or certified interval"),
    _c("scale", "atomic", "classical", "numeric", "numeric", "factor: rational",
       domain="explicit rational factor (no implied 1/2)", errors=(ErrorCode.INVALID_INPUT,)),
    _c("accum", "atomic", "classical", "numeric", "numeric", "none",
       state="running sum (exact)", domain="exact rational or interval",
       notes="y_t = x_t + y_{t-1}; stores the accumulated value"),
    _c("rate", "atomic", "classical", "numeric", "numeric", "dt: positive rational",
       state="previous input", domain="dt > 0",
       errors=(ErrorCode.DOMAIN_ERROR,), notes="signed first difference / dt"),
    _c("wrap", "atomic", "classical", "numeric", "numeric", "period: positive rational",
       state="none", domain="period > 0; exact scalar input",
       errors=(ErrorCode.DOMAIN_ERROR, ErrorCode.UNSUPPORTED),
       notes="returns the representative in [0, period)"),
    _c("spatial", "atomic", "classical", "field", "numeric",
       "axis: int = 0; index: int[24] optional", domain="index inside the field",
       errors=(ErrorCode.DOMAIN_ERROR,), notes="explicit field sampling, not a metric"),
    _c("exp", "atomic", "classical", "numeric", "interval",
       "precision: int = 64", domain="all rationals",
       errors=(ErrorCode.BUDGET_EXHAUSTED,),
       theorem="interval.exp_exp_contains (Lean pending)",
       notes="certified rational enclosure; exact only at x = 0"),
    _c("log", "atomic", "classical", "numeric", "interval",
       "precision: int = 64", domain="x > 0", errors=(ErrorCode.DOMAIN_ERROR,)),
    _c("sat", "atomic", "classical", "numeric", "numeric", "lo, hi: rational",
       domain="lo <= hi", errors=(ErrorCode.DOMAIN_ERROR,),
       notes="explicit ordered bounds; idempotent clamp"),
    _c("hysteresis", "atomic", "classical", "numeric", "bit",
       "lower, upper: rational; initial: bool", state="latched bit",
       domain="lower < upper", errors=(ErrorCode.DOMAIN_ERROR,),
       theorem="core.hysteresis_deadband (Lean pending)",
       notes="two thresholds; retention strictly inside the deadband"),
    _c("delay", "atomic", "classical", "numeric", "numeric",
       "ticks: int >= 1; initial: numeric", state="ring buffer of length ticks",
       domain="ticks >= 1", errors=(ErrorCode.DOMAIN_ERROR,),
       notes="per-node delay line"),
    # -- continuum ------------------------------------------------------
    _c("grad", "atomic", "continuum", "field", "vector_field", "h: positive rational",
       domain="h > 0", errors=(ErrorCode.DOMAIN_ERROR,), theorem="geometry.curl_grad_zero (tested)"),
    _c("div_spatial", "atomic", "continuum", "vector_field", "numeric", "h: positive rational",
       domain="h > 0", errors=(ErrorCode.DOMAIN_ERROR,)),
    _c("curl", "atomic", "continuum", "vector_field", "two_form", "h: positive rational",
       domain="h > 0; 2-form has 276 components on the 24-D carrier",
       errors=(ErrorCode.DOMAIN_ERROR,), notes="exterior derivative, not a 4-coordinate scalar"),
    _c("laplacian", "atomic", "continuum", "field", "numeric",
       "h: positive rational; axes: int[] optional", domain="h > 0",
       errors=(ErrorCode.DOMAIN_ERROR,)),
    _c("boundary", "atomic", "continuum", "field", "field",
       "shape: int[]; spacing: rational; kind: dirichlet|neumann|robin; "
       "value/alpha/beta/gamma: rational", domain="consistent shape and spacing",
       errors=(ErrorCode.DOMAIN_ERROR,),
       notes="alpha*psi + beta*dpsi/dn = gamma on every face"),
    # -- conservative network ------------------------------------------
    _c("junction_0", "atomic", "conservative", "port+", "port", "resolved: int = last",
       domain="at least 2 ports with identical flow", errors=(ErrorCode.DOMAIN_ERROR,),
       theorem="power.junction_0_conserves_power (Lean pending)",
       notes="common flow; resolved effort = -sum(other efforts)"),
    _c("junction_1", "atomic", "conservative", "port+", "port", "resolved: int = last",
       domain="at least 2 ports with identical effort", errors=(ErrorCode.DOMAIN_ERROR,),
       theorem="power.junction_1_conserves_power (Lean pending)",
       notes="common effort; resolved flow = -sum(other flows)"),
    _c("gyrator", "atomic", "conservative", "port", "port", "resistance: nonzero rational",
       domain="r != 0", errors=(ErrorCode.DOMAIN_ERROR,),
       theorem="power.gyrator_conserves_power (Lean pending)",
       notes="(e,f) -> (r f, -e/r); anti-reciprocal and power conserving"),
    _c("transformer", "atomic", "conservative", "port", "port", "ratio: nonzero rational",
       domain="n != 0", errors=(ErrorCode.DOMAIN_ERROR,),
       theorem="power.transformer_conserves_power (Lean pending)"),
    _c("dissipate", "atomic", "conservative", "numeric (effort)", "port",
       "resistance, temperature: positive rational", domain="R > 0, T > 0",
       errors=(ErrorCode.DOMAIN_ERROR,),
       notes="linear dissipator; entropy rate e^2/(R T) >= 0"),
    _c("store_pot", "atomic", "conservative", "numeric (flow)", "port",
       "capacitance, dt: positive rational", state="stored charge",
       domain="C > 0, dt > 0", errors=(ErrorCode.DOMAIN_ERROR,)),
    _c("store_kin", "atomic", "conservative", "numeric (effort)", "port",
       "inductance, dt: positive rational", state="stored flux",
       domain="L > 0, dt > 0", errors=(ErrorCode.DOMAIN_ERROR,)),
    _c("transduce", "atomic", "conservative", "port", "port",
       "ratio: nonzero rational; efficiency: (0,1]", domain="0 < eta <= 1",
       errors=(ErrorCode.DOMAIN_ERROR,),
       notes="ideal transducer; eta = 1 conserves power exactly"),
    # -- stochastic / topological --------------------------------------
    _c("noise", "atomic", "stochastic_topological", "(no inputs)", "numeric",
       "amplitude: nonnegative rational; seed: int optional", state="PRNG state",
       domain="amplitude >= 0", errors=(ErrorCode.DOMAIN_ERROR,),
       theorem="noise.exact_moments (tested)",
       notes="deterministic two-point +-a distribution with probability 1/2; "
             "mean 0, variance a^2 exactly. Not a physical entropy source"),
    _c("quantize", "atomic", "stochastic_topological", "numeric", "numeric",
       "quantum: positive rational", domain="q > 0", errors=(ErrorCode.DOMAIN_ERROR,),
       notes="nearest multiple, ties away from zero"),
    _c("entropy", "atomic", "stochastic_topological", "port", "numeric",
       "temperature: positive rational", domain="T > 0 and port power >= 0",
       errors=(ErrorCode.DOMAIN_ERROR,),
       notes="entropy production rate P/T; rejects active (creating) ports"),
    # -- composites -----------------------------------------------------
    _c("recip", "composite", "composite", "numeric", "numeric", "none",
       domain="x != 0", errors=(ErrorCode.DIVISION_BY_ZERO,)),
    _c("div", "composite", "composite", "numeric, numeric", "numeric", "none",
       domain="denominator != 0", errors=(ErrorCode.DIVISION_BY_ZERO,),
       notes="exact division of a numerator operand by a denominator operand"),
    _c("sqrt", "composite", "composite", "numeric", "interval",
       "precision: int = 64", domain="x >= 0", errors=(ErrorCode.DOMAIN_ERROR,),
       notes="exact point interval for rational roots, otherwise certified"),
    _c("eq", "composite", "composite", "value, value", "bit", "none",
       notes="mathematical equality; intervals must be equal singletons"),
    _c("translinear", "composite", "composite", "numeric+", "interval",
       "exponents: rational[]", domain="positive bases for non-integer exponents",
       errors=(ErrorCode.DOMAIN_ERROR,),
       notes="product of powers prod(x_i^p_i), not exp(log(x))"),
    _c("state_space", "composite", "composite", "vector (u)", "vector",
       "A, B, C, D: rational matrices", state="x (state vector)",
       domain="dimensionally consistent matrices", errors=(ErrorCode.INVALID_INPUT,),
       notes="x' = A x + B u; y = C x + D u"),
    _c("pid", "composite", "composite", "numeric", "numeric",
       "kp, ki, kd, dt: rational; initial: rational", state="integral, previous error",
       domain="dt > 0", errors=(ErrorCode.DOMAIN_ERROR,)),
    _c("phase_locked_loop", "composite", "composite", "numeric (phase)", "numeric",
       "center_frequency, gain, dt: rational; initial_phase: rational",
       state="VCO phase", domain="dt > 0", errors=(ErrorCode.DOMAIN_ERROR,)),
    _c("transmission_line", "composite", "composite", "numeric", "numeric",
       "segments: int >= 1; reflection: rational in [-1,1]; initial: rational",
       state="delay cells", domain="segments >= 1, |reflection| <= 1",
       errors=(ErrorCode.DOMAIN_ERROR,),
       notes="documented lossless delay-line model with load reflection"),
    _c("kalman_observer", "composite", "composite", "numeric (measurement)", "numeric",
       "process_variance, measurement_variance >= 0; initial_x, initial_p",
       state="estimate x and covariance p", domain="r > 0, p >= 0",
       errors=(ErrorCode.DOMAIN_ERROR,), notes="scalar exact-rational Kalman update"),
    _c("thermo_electric", "composite", "composite", "port (electrical)", "port (thermal)",
       "seebeck, resistance, temperature: rational", state="none",
       domain="T > 0, R > 0", errors=(ErrorCode.DOMAIN_ERROR,),
       notes="Peltier heat S*T*I plus Joule heat I^2*R; sign is physical"),
    _c("delta_sigma_modulator", "composite", "composite", "numeric", "bit",
       "order: 1|2; threshold: rational", state="integrator(s) and last output",
       domain="order in {1,2}, 0 < threshold", errors=(ErrorCode.DOMAIN_ERROR,),
       notes="canonical 1st/2nd order sigma-delta loop"),
]:
    _register(c)

# Fill wire-kind tables.
_NUMERIC_OPS = {
    "sum", "neg", "mult", "scale", "accum", "rate", "wrap", "sat",
    "hysteresis", "delay", "recip", "div", "eq", "pid", "phase_locked_loop",
    "transmission_line", "kalman_observer", "noise", "quantize",
    "delta_sigma_modulator",
}
_INTERVAL_OPS = {"exp", "log", "sqrt", "translinear"}
_PORT_INPUT_OPS = {"junction_0", "junction_1", "gyrator", "transformer",
                   "transduce", "entropy", "thermo_electric"}
_FIELD_INPUT_OPS = {"grad", "laplacian", "spatial", "boundary"}
#: Conservative primitives whose *input* is a numeric effort or flow, not a port.
_NUMERIC_INPUT_CONSERVATIVE = {"dissipate", "store_pot", "store_kin"}
_VECTOR_FIELD_INPUT_OPS = {"div_spatial", "curl"}
_CONSUMER_KINDS = {
    "exp": frozenset({NUMERIC}),
    "log": frozenset({NUMERIC}),
    "sqrt": frozenset({NUMERIC}),
    "translinear": frozenset({NUMERIC}),
    "spatial": frozenset({FIELD}),
    "grad": frozenset({FIELD}),
    "laplacian": frozenset({FIELD}),
    "boundary": frozenset({FIELD}),
    "div_spatial": frozenset({VECTOR_FIELD}),
    "curl": frozenset({VECTOR_FIELD}),
    "state_space": frozenset({VECTOR}),
    "thermo_electric": frozenset({PORT}),
}
for op in _NUMERIC_OPS:
    _CONSUMER_KINDS.setdefault(op, frozenset({NUMERIC, BIT}))
for op in _PORT_INPUT_OPS:
    _CONSUMER_KINDS[op] = frozenset({PORT})

for op in ALL_PRIMITIVES:
    contract = CONTRACTS[op]
    if op in _VECTOR_FIELD_INPUT_OPS:
        INPUT_KINDS[op] = frozenset({VECTOR_FIELD})
    elif op in _CONSUMER_KINDS:
        INPUT_KINDS[op] = _CONSUMER_KINDS[op]
    elif op in _NUMERIC_INPUT_CONSERVATIVE:
        INPUT_KINDS[op] = frozenset({NUMERIC})
    elif contract.tier == "conservative":
        INPUT_KINDS[op] = frozenset({PORT})
    else:
        INPUT_KINDS[op] = frozenset({NUMERIC})

for op in ALL_PRIMITIVES:
    if op in _INTERVAL_OPS:
        OUTPUT_KIND[op] = "interval"
    elif op in {"junction_0", "junction_1", "gyrator", "transformer",
                "dissipate", "store_pot", "store_kin", "transduce",
                "thermo_electric"}:
        OUTPUT_KIND[op] = PORT
    elif op == "grad":
        OUTPUT_KIND[op] = VECTOR_FIELD
    elif op == "curl":
        OUTPUT_KIND[op] = TWO_FORM
    elif op == "boundary":
        OUTPUT_KIND[op] = FIELD
    elif op == "state_space":
        OUTPUT_KIND[op] = VECTOR
    elif op in {"eq", "hysteresis", "delta_sigma_modulator"}:
        OUTPUT_KIND[op] = BIT
    else:
        OUTPUT_KIND[op] = NUMERIC

PURE_OPS = frozenset(
    op for op in ALL_PRIMITIVES
    if op not in STATEFUL_OPS and op not in {"spatial", "boundary"}
)


def contract(op: str) -> Contract:
    name = canonical_op(op)
    if name not in CONTRACTS:
        from .exact import CentError

        raise CentError(ErrorCode.UNSUPPORTED, f"unknown ¢ primitive {op!r}")
    return CONTRACTS[name]


def capability_report() -> dict:
    """Machine-readable capability registry."""
    by_status: dict[str, list[str]] = {s: [] for s in STATUS_ORDER}
    for op in ALL_PRIMITIVES:
        by_status[CONTRACTS[op].status].append(op)
    return {
        "schema": "cent-capabilities/1",
        "atomic_count": len(ATOMIC_PRIMITIVES),
        "composite_count": len(COMPOSITE_PRIMITIVES),
        "atomic": list(ATOMIC_PRIMITIVES),
        "composite": list(COMPOSITE_PRIMITIVES),
        "tiers": {tier: list(ops) for tier, ops in _TIERS.items()},
        "by_status": by_status,
        "contracts": {op: CONTRACTS[op].as_dict() for op in ALL_PRIMITIVES},
    }
