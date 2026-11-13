"""Mechanism cards for cross-domain transfer.

A mechanism is not a substrate and not a route.  It is the causal or structural
principle that can be realized in more than one domain (feedback equilibrium,
error-feedback noise shaping, conservation at a junction, and so on).

The registry has two layers.  `MechanismCard` is the schema/data layer: six
hand-authored principle cards plus generated Δ interpretations.  The two
generated cards are produced by running executable mapping operators over
`kcl-conservation`; Phase 0 fixtures live in the test suite, and no card is a
claim that every mechanism has been validated in a target.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from . import vocabulary
from .mapping import OPERATOR_BY_ID

SCHEMA = "cent-mechanism/1"
REGISTRY_SCHEMA = "cent-mechanism-registry/1"

EVIDENCE_LEVELS = (
    "proposed",
    "structural",
    "admissible",
    "source-simulated",
    "target-simulated",
    "target-integrated",
)

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")


def _text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty text")
    return text


def _identifier(value: Any, field_name: str) -> str:
    text = _text(value, field_name)
    if not _ID_RE.fullmatch(text):
        raise ValueError(f"{field_name} must match {_ID_RE.pattern!s}: {text!r}")
    return text


def _text_tuple(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if isinstance(value, str):
        value = (value,)
    if value is None:
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        items = tuple(_text(item, field_name) for item in value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    if not items and not allow_empty:
        raise ValueError(f"{field_name} must contain at least one entry")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


@dataclass(frozen=True)
class MechanismCard:
    """A domain-independent mechanism and its declared source evidence."""

    id: str
    name: str
    principle: str
    source_domains: tuple[str, ...]
    supported_operations: tuple[str, ...]
    primitive_chain: tuple[str, ...]
    carrier: str
    stateful: bool
    invariants: tuple[str, ...]
    laws: tuple[str, ...]
    validity: tuple[str, ...]
    failure_modes: tuple[str, ...]
    evidence_level: str
    provenance: tuple[str, ...]
    gaps: tuple[str, ...] = ()
    principle_id: str = ""
    operators: tuple[str, ...] = ()
    schema: str = SCHEMA

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ValueError(f"mechanism.schema must be {SCHEMA!r}: {self.schema!r}")
        _identifier(self.id, "mechanism.id")
        _text(self.name, "mechanism.name")
        _text(self.principle, "mechanism.principle")
        _text_tuple(self.source_domains, "mechanism.source_domains")
        _text_tuple(self.supported_operations, "mechanism.supported_operations")
        _text_tuple(self.primitive_chain, "mechanism.primitive_chain")
        unknown = [
            op for op in self.primitive_chain
            if vocabulary.canonical_op(op) not in vocabulary.ALL_PRIMITIVES
        ]
        if unknown:
            raise ValueError(f"mechanism.primitive_chain has unknown primitive(s): {unknown}")
        _text(self.carrier, "mechanism.carrier")
        if not isinstance(self.stateful, bool):
            raise ValueError("mechanism.stateful must be boolean")
        _text_tuple(self.invariants, "mechanism.invariants")
        _text_tuple(self.laws, "mechanism.laws")
        _text_tuple(self.validity, "mechanism.validity")
        _text_tuple(self.failure_modes, "mechanism.failure_modes")
        if self.evidence_level not in EVIDENCE_LEVELS:
            raise ValueError(
                f"mechanism.evidence_level must be one of {list(EVIDENCE_LEVELS)}: "
                f"{self.evidence_level!r}"
            )
        _text_tuple(self.provenance, "mechanism.provenance")
        _text_tuple(self.gaps, "mechanism.gaps", allow_empty=True)
        if self.principle_id:
            _identifier(self.principle_id, "mechanism.principle_id")
        if self.operators:
            _text_tuple(self.operators, "mechanism.operators")
            unknown_ops = [op for op in self.operators if op not in OPERATOR_BY_ID]
            if unknown_ops:
                raise ValueError(
                    f"mechanism.operators has unknown operator(s): {unknown_ops}"
                )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "id": self.id,
            "name": self.name,
            "principle": self.principle,
            "source_domains": list(self.source_domains),
            "supported_operations": list(self.supported_operations),
            "primitive_chain": list(self.primitive_chain),
            "carrier": self.carrier,
            "stateful": self.stateful,
            "invariants": list(self.invariants),
            "laws": list(self.laws),
            "validity": list(self.validity),
            "failure_modes": list(self.failure_modes),
            "evidence_level": self.evidence_level,
            "provenance": list(self.provenance),
            "gaps": list(self.gaps),
            "principle_id": self.principle_id,
            "operators": list(self.operators),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MechanismCard":
        if not isinstance(data, Mapping):
            raise ValueError("mechanism card must be a mapping")
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            principle=str(data.get("principle", "")),
            source_domains=_text_tuple(
                data.get("source_domains", ()), "mechanism.source_domains"
            ),
            supported_operations=_text_tuple(
                data.get("supported_operations", ()),
                "mechanism.supported_operations",
            ),
            primitive_chain=_text_tuple(
                data.get("primitive_chain", ()), "mechanism.primitive_chain"
            ),
            carrier=str(data.get("carrier", "")),
            stateful=data.get("stateful") is True,
            invariants=_text_tuple(
                data.get("invariants", ()), "mechanism.invariants"
            ),
            laws=_text_tuple(data.get("laws", ()), "mechanism.laws"),
            validity=_text_tuple(data.get("validity", ()), "mechanism.validity"),
            failure_modes=_text_tuple(
                data.get("failure_modes", ()), "mechanism.failure_modes"
            ),
            evidence_level=str(data.get("evidence_level", "")),
            provenance=_text_tuple(
                data.get("provenance", ()), "mechanism.provenance"
            ),
            gaps=_text_tuple(data.get("gaps", ()), "mechanism.gaps", allow_empty=True),
            principle_id=str(data.get("principle_id", "")),
            operators=_text_tuple(
                data.get("operators", ()), "mechanism.operators", allow_empty=True
            ),
            schema=str(data.get("schema", SCHEMA)),
        )


# ---------------------------------------------------------------------------
# Phase 1 production registry
# ---------------------------------------------------------------------------
#
# These cards are normalized from declarations already present in this package.
# They do not add measured behavior.  ``structural`` means the mechanism has a
# declared material/topology row; ``source-simulated`` means a declared source
# model or exact route has been exercised.  No card claims target evidence.

_BASE_MECHANISM_CARDS: tuple[MechanismCard, ...] = (
    MechanismCard(
        id="delta-sigma-error-feedback",
        name="delta-sigma error feedback",
        principle=(
            "Quantize the accumulated error, feed the quantized code back, and "
            "reconstruct the input from the code mean."
        ),
        source_domains=("audio", "electronics"),
        supported_operations=("quantized_carry",),
        primitive_chain=("neg", "sum", "accum", "quantize", "sat", "delay"),
        carrier="bitstream",
        stateful=True,
        invariants=(
            "the loop state stays inside the declared integrator limit for the declared input range",
            "the exact code mean reconstructs a constant input within the declared quantum",
        ),
        laws=(
            "error = input - feedback; integrator = integrator + error; "
            "level = clamp(quantize(integrator), 0, full_scale); feedback = delayed level",
        ),
        validity=(
            "input in [0, full_scale]",
            "positive quantum with an integral full_scale/quantum ladder",
            "finite exact runs are evidence for the tested inputs, not a general convergence theorem",
        ),
        failure_modes=(
            "input outside the declared range is rejected",
            "integrator excursion beyond the declared limit",
            "comparator offset, metastability, clock jitter and reference mismatch are not modeled",
        ),
        evidence_level="source-simulated",
        provenance=(
            "cent_compiler/assembly.py",
            "cent_compiler/delta_sigma.py",
            "tests/test_assembly.py",
            "docs/DELTA_SIGMA_DEMO.md",
        ),
        gaps=(
            "target coverage is reference-only; no live GLM carry adapter",
            "no measured bit-budget or latency contract",
        ),
    ),
    MechanismCard(
        id="log-domain-sqrt",
        name="log-domain exponential/logarithm",
        principle=(
            "Use a logarithmic junction, an exact gain and an exponential "
            "junction so a half-gain in the log domain realizes a square root."
        ),
        source_domains=("electronics",),
        supported_operations=("sqrt",),
        primitive_chain=("log", "scale", "exp"),
        carrier="junction voltage/current (normalized)",
        stateful=False,
        invariants=(
            "the input remains in the declared positive domain x > 0",
            "the route enclosure overlaps the independent sqrt_q bracket",
            "the route enclosure width stays within the declared tolerance",
        ),
        laws=(
            "ln_x = ln(x); half_ln = (1/2) * ln_x; root = exp(half_ln) = exp((1/2) * ln(x))",
            "log and exp return certified rational enclosures; no hidden binary float is used",
        ),
        validity=(
            "x > 0",
            "precision in 1..64 bits",
            "junction bias remains in the declared logarithmic/exponential region",
        ),
        failure_modes=(
            "nonpositive input is rejected",
            "thermal-voltage drift, junction ideality mismatch and offset are not modeled",
            "finite bandwidth and measured parasitics are not modeled",
        ),
        evidence_level="source-simulated",
        provenance=(
            "cent_compiler/assembly.py",
            "cent_compiler/device.py",
            "tests/test_assembly.py",
            "docs/LOG_DOMAIN_SQRT.md",
        ),
        gaps=(
            "target evidence is software-only; no measured junction or physical route",
            "no measured bit-budget or latency contract",
        ),
    ),
    MechanismCard(
        id="kcl-conservation",
        name="KCL conservation",
        principle=(
            "At a declared ideal junction, signed currents sum to zero; the "
            "junction therefore realizes exact signed addition, with "
            "subtraction supplied by exact negation glue."
        ),
        source_domains=("electronics",),
        supported_operations=("sum", "difference"),
        primitive_chain=("sum", "neg"),
        carrier="normalized current",
        stateful=False,
        invariants=(
            "the declared junction preserves the signed current sum",
            "sum and difference remain exact rational operations",
        ),
        laws=(
            "total = a + b at a declared Kirchhoff current-law junction; "
            "difference is total = a + (-b) with exact negation glue",
        ),
        validity=(
            "two normalized exact rational inputs",
            "both inputs are inside the declared linear junction range",
            "the exact route carries no voltage/current scaling",
        ),
        failure_modes=(
            "floating node, source loading and compliance limit are not modeled",
            "physical units, source/load impedance and a reference netlist are not declared",
            "no fabrication or measured-device evidence",
        ),
        evidence_level="source-simulated",
        provenance=(
            "cent_compiler/assembly.py",
            "cent_compiler/device.py",
            "tests/test_assembly.py",
            "docs/PHYSICAL_NETLIST.md",
        ),
        gaps=(
            "no physical voltage/current mapping or reference netlist",
            "target coverage is software reference/live KCL only; no physical junction measurement",
        ),
    ),
    MechanismCard(
        id="cam-profile",
        name="mechanical cam profile",
        principle=(
            "A shaped spatial profile maps input displacement to output "
            "displacement according to the declared profile law."
        ),
        source_domains=("mechanical",),
        supported_operations=("sqrt",),
        primitive_chain=("spatial",),
        carrier="position",
        stateful=False,
        invariants=(
            "the profile fixes the input-to-output displacement relation",
            "the operation is evaluated geometrically rather than by a sqrt instruction",
        ),
        laws=(
            "a square-root cam profile encodes y = sqrt(x) as a spatial lookup table",
        ),
        validity=(
            "fixed cam profile",
            "declared displacement range",
        ),
        failure_modes=(
            "profile manufacturing tolerance and wear are not modeled",
            "no exact cam solver or fabricated profile is declared",
        ),
        evidence_level="structural",
        provenance=(
            "cent_compiler/substrate_library.py",
            "cent_compiler/pattern_matcher.py",
        ),
        gaps=(
            "no exact cam solver or fabricated profile",
            "no target adapter or target test",
        ),
    ),
    MechanismCard(
        id="orifice-pressure-flow",
        name="orifice pressure-flow square root",
        principle=(
            "A nonlinear orifice provides the pressure/flow restriction and a "
            "pressure-feedback path is declared as the square-root realization."
        ),
        source_domains=("fluidics",),
        supported_operations=("sqrt",),
        primitive_chain=("mult", "eq"),
        carrier="pressure/flow",
        stateful=False,
        invariants=(
            "the declared orifice restriction and pressure-feedback topology are preserved",
            "the feedback is algebraic; no time-integrated state is declared",
        ),
        laws=(
            "pressure-flow relation through a shaped orifice; feedback via the pressure differential",
        ),
        validity=(
            "declared pressure and flow operating range",
            "fluid properties, orifice geometry and discharge behavior must be declared",
        ),
        failure_modes=(
            "reverse flow, cavitation and compressibility are not modeled",
            "no calibrated discharge coefficient or pressure/flow data are declared",
            "no exact fluidic solver is declared",
        ),
        evidence_level="structural",
        provenance=(
            "cent_compiler/substrate_library.py",
            "cent_compiler/pattern_matcher.py",
        ),
        gaps=(
            "no exact pressure-flow law or calibrated orifice model",
            "no target adapter or target test",
        ),
    ),
    MechanismCard(
        id="pll-phase-tracking",
        name="phase-locked loop phase tracking",
        principle=(
            "A phase detector, PI loop filter and VCO form a feedback loop "
            "that drives phase error toward zero and tracks a reference frequency."
        ),
        source_domains=("electronics",),
        supported_operations=("track_phase", "synthesize_frequency"),
        primitive_chain=("accum", "wrap", "sum", "scale"),
        carrier="phase",
        stateful=True,
        invariants=(
            "the VCO phase is the accumulated frequency state",
            "the phase detector compares reference and VCO phase modulo 2*pi",
            "the declared type-2 loop drives frequency error and phase error toward zero in the test",
        ),
        laws=(
            "pd = kpd * sin(phi_ref - phi_vco); integral += ki * pd; "
            "control = loop_gain * pd + integral; f_vco = f0 + kvco * control; "
            "phi_vco += 2*pi * f_vco / sample_rate",
        ),
        validity=(
            "declared numerical test: 5 Hz reference, 1 kHz sample rate, 5000 samples",
            "declared type-2 parameters kvco=10, kpd=1, loop_gain=0.3 and ki=0.01",
            "float simulation only; not an exact route or measured device",
        ),
        failure_modes=(
            "lock outside the declared numerical point is not characterized",
            "cycle slip and lock-range limits are not modeled",
            "phase-detector nonlinearity, VCO noise and measured-device behavior are not modeled",
        ),
        evidence_level="source-simulated",
        provenance=(
            "cent_compiler/simulator.py",
            "cent_compiler/evaluator.py",
            "tests/test_all.py",
            "cent_compiler/concepts.py",
        ),
        gaps=(
            "no exact or target phase-tracking adapter",
            "no lock-range, noise or measured-device evidence",
        ),
    ),
    MechanismCard(
        id="threshold-comparator",
        name="bounded threshold comparator",
        principle=(
            "A high-gain differential stage with bounded rails and a declared "
            "zero crossing realizes the three-level sign: below zero it "
            "saturates low, at zero it holds the null code, and above zero it "
            "saturates high."
        ),
        source_domains=("electronics", "information"),
        supported_operations=("sign",),
        primitive_chain=("sat", "sum"),
        carrier="normalized voltage/current",
        stateful=False,
        invariants=(
            "the output is one of -1, 0 or +1",
            "the declared zero crossing is exact",
            "negative and positive inputs saturate to opposite bounded rails",
        ),
        laws=(
            "y = -1 if x < 0; y = 0 if x = 0; y = +1 if x > 0",
            "the comparator is the ideal infinite-gain limit of a bounded saturating differential stage with a zero threshold and no hysteresis",
        ),
        validity=(
            "x is an exact rational",
            "zero threshold, zero offset and no hysteresis are declared",
            "the output rails are exactly -1 and +1",
        ),
        failure_modes=(
            "input offset, finite gain, hysteresis, metastability and noise are not modeled",
            "no measured comparator, propagation delay or rail recovery is declared",
        ),
        evidence_level="structural",
        provenance=(
            "cent_compiler/exact.py",
            "cent_compiler/material_contracts.py",
            "docs/DEVICE_BINDING.md",
            "tests/test_transfer_contracts.py",
        ),
        gaps=(
            "target evidence is a software reference only; no measured comparator",
            "comparator offset, hysteresis and metastability are not modeled",
        ),
    ),
    MechanismCard(
        id="transcendental-identity",
        name="transcendental identity via constitutive exponential law",
        principle=(
            "A logarithmic junction followed by an antilog junction realizes the "
            "identity x = exp(log(x)) on the declared positive domain. Adding "
            "logarithms multiplies; subtracting them divides; negating one "
            "logarithm reciprocates. The shared law is the slide-rule "
            "composition, not a sqrt-specific instruction."
        ),
        source_domains=("mechanical", "electronics"),
        supported_operations=("exp", "log", "mult", "div", "reciprocal"),
        primitive_chain=("log", "sum", "neg", "exp"),
        carrier="log-domain signal",
        stateful=False,
        invariants=(
            "log and antilog are inverse constitutive laws on the declared positive domain",
            "signed addition in the log domain maps to multiplication in the linear domain",
            "negating a single logarithm maps to exact reciprocal",
            "the composition preserves the declared normalized value",
        ),
        laws=(
            "log(exp(x)) = x and exp(log(x)) = x on the declared domain",
            "exp(log(a) + log(b)) = a * b; exp(log(a) - log(b)) = a / b",
            "exp(-log(x)) = 1 / x on the declared positive domain",
        ),
        validity=(
            "log/mult/div/reciprocal inputs are strictly positive; exp accepts any exact rational",
            "junction bias remains in its declared logarithmic/exponential region",
            "precision is a declared finite-resolution parameter",
        ),
        failure_modes=(
            "nonpositive log input is rejected",
            "thermal-voltage drift, ideality mismatch and offset are not modeled",
            "signed mult/div/reciprocal outside the positive log domain is not declared",
        ),
        evidence_level="structural",
        provenance=(
            "cent_compiler/assembly.py",
            "cent_compiler/interval.py",
            "docs/LOG_DOMAIN_SQRT.md",
        ),
        gaps=(
            "no measured junction or physical log/antilog calibration",
            "mult/div/reciprocal are declared only on positive normalized inputs",
        ),
    ),
)


@dataclass(frozen=True)
class DeltaInterpretation:
    """A declared domain interpretation of one shared mechanism principle.

    The interpretation is data.  The card is generated by running its operator
    chain over the principle card, so deleting the generated card and replaying
    this record reconstructs it.
    """

    id: str
    base_id: str
    operators: tuple[str, ...]
    name: str
    principle: str
    source_domains: tuple[str, ...]
    carrier: str
    invariants: tuple[str, ...]
    laws: tuple[str, ...]
    validity: tuple[str, ...]
    failure_modes: tuple[str, ...]
    provenance: tuple[str, ...]
    gaps: tuple[str, ...]
    duality: tuple[tuple[str, str], ...] = ()
    scale: float = 1.0
    offset: float = 0.0
    evidence_level: str = "source-simulated"

    def validate(self) -> None:
        _identifier(self.id, "interpretation.id")
        _identifier(self.base_id, "interpretation.base_id")
        _text_tuple(self.operators, "interpretation.operators")
        unknown = [op for op in self.operators if op not in OPERATOR_BY_ID]
        if unknown:
            raise ValueError(f"interpretation has unknown operator(s): {unknown}")
        _text(self.name, "interpretation.name")
        _text(self.principle, "interpretation.principle")
        _text_tuple(self.source_domains, "interpretation.source_domains")
        _text(self.carrier, "interpretation.carrier")
        _text_tuple(self.invariants, "interpretation.invariants")
        _text_tuple(self.laws, "interpretation.laws")
        _text_tuple(self.validity, "interpretation.validity")
        _text_tuple(self.failure_modes, "interpretation.failure_modes")
        _text_tuple(self.provenance, "interpretation.provenance")
        _text_tuple(self.gaps, "interpretation.gaps")
        if not isinstance(self.scale, (int, float)) or self.scale == 0:
            raise ValueError("interpretation.scale must be a nonzero number")
        if not isinstance(self.offset, (int, float)):
            raise ValueError("interpretation.offset must be a number")
        if self.duality:
            keys = [key for key, _value in self.duality]
            if len(set(keys)) != len(keys):
                raise ValueError("interpretation.duality keys must be unique")
            _text_tuple(
                tuple(value for _key, value in self.duality),
                "interpretation.duality values",
            )


INTERPRETATIONS = (
    DeltaInterpretation(
        id="opamp-summing",
        base_id="kcl-conservation",
        operators=("scale-offset", "composition"),
        name="op-amp summing/difference amplifier",
        principle=(
            "A high-gain op-amp with a matched resistor network realizes a "
            "weighted voltage sum; an inverting buffer on one input turns the "
            "same summing block into a difference."
        ),
        source_domains=("electronics",),
        carrier="normalized voltage",
        invariants=(
            "the matched input network preserves the normalized voltage sum",
            "the inverting buffer changes the sign of the second input",
            "sum and difference remain exact rational operations in the ideal block model",
        ),
        laws=(
            "total = a + b with 1/2 input attenuation and closed-loop gain 2",
            "total = a - b via an ideal inverting buffer and the same summing block",
        ),
        validity=(
            "ideal closed-loop gain with matched input and feedback resistors",
            "both normalized voltages inside the declared linear output range",
            "no source loading, offset, slew or finite-bandwidth model",
        ),
        failure_modes=(
            "resistor mismatch and finite open-loop gain",
            "input offset voltage, bias current and output saturation",
            "finite bandwidth, slew limiting and source loading are not modeled",
            "no device values, reference netlist or measured-voltage evidence",
        ),
        provenance=(
            "cent_compiler/assembly.py",
            "tests/test_assembly.py",
            "docs/OPAMP_SUM.md",
        ),
        gaps=(
            "no device values, reference netlist or physical voltage scaling",
            "target coverage is normalized-voltage software only; no measured amplifier",
        ),
        scale=2.0,
        offset=0.0,
    ),
    DeltaInterpretation(
        id="fluid-continuity",
        base_id="kcl-conservation",
        operators=("effort-flow-duality", "composition"),
        name="fluid pipe-junction continuity",
        principle=(
            "At a declared ideal pipe junction, normalized volumetric flows "
            "conserve; the junction therefore realizes exact addition of two "
            "flows without a pressure or mass parameter. A declared reversed "
            "port supplies exact negation for difference."
        ),
        source_domains=("fluidics",),
        carrier="normalized volumetric flow",
        invariants=(
            "the declared junction preserves the signed flow sum",
            "a reversed port changes the sign of one incoming flow",
            "sum and difference remain exact rational operations",
        ),
        laws=(
            "q_total = q_a + q_b at a declared flow-conservation junction",
            "q_total = q_a - q_b via a declared reversed port and the same junction",
        ),
        validity=(
            "two normalized exact rational flows",
            "both flows are inside the declared linear junction range",
            "the exact route carries no pressure/flow scaling",
            "difference uses an ideal reversed-port sign convention",
        ),
        failure_modes=(
            "leakage, compressibility, junction loss and finite response are not modeled",
            "no pressure/flow scaling, device binding or reference netlist is declared",
            "no fabrication or measured-flow evidence",
        ),
        provenance=(
            "cent_compiler/assembly.py",
            "tests/test_assembly.py",
            "docs/FLUID_SUM.md",
        ),
        gaps=(
            "no pressure/flow scaling, device binding or reference netlist",
            "target coverage is normalized-flow software only; no measured junction",
        ),
        duality=(
            ("source_effort", "voltage"),
            ("source_flow", "current"),
            ("target_effort", "pressure"),
            ("target_flow", "volumetric flow"),
        ),
    ),
    DeltaInterpretation(
        id="log-domain-arithmetic",
        base_id="transcendental-identity",
        operators=("composition",),
        name="log-domain slide-rule arithmetic",
        principle=(
            "A logging junction, exact signed addition and an antilog junction "
            "compute exp, log, multiplication, division and reciprocal from the "
            "shared transcendental identity. Multiplication adds logarithms; "
            "division negates one and adds; reciprocal negates the single "
            "logarithm."
        ),
        source_domains=("mechanical", "electronics"),
        carrier="log-domain signal",
        invariants=(
            "the log/antilog pair preserves the declared value identity",
            "signed log-domain addition maps to exact multiplication",
            "signed log-domain subtraction maps to exact division",
            "negating one logarithm maps to exact reciprocal",
        ),
        laws=(
            "exp(x) is the antilog junction output",
            "log(x) is the logging junction output",
            "exp(log(a) + log(b)) = a * b",
            "exp(log(a) - log(b)) = a / b",
            "exp(-log(x)) = 1 / x",
        ),
        validity=(
            "exp accepts any exact rational; log/mult/div/reciprocal require positive inputs",
            "precision is a declared finite-resolution parameter",
            "the result is a certified rational enclosure, not a stored irrational",
        ),
        failure_modes=(
            "nonpositive log input is rejected",
            "signed mult/div/reciprocal outside the positive log domain is not declared",
            "junction temperature, ideality, offset and finite bandwidth are not modeled",
        ),
        provenance=(
            "cent_compiler/assembly.py",
            "cent_compiler/interval.py",
            "cent_compiler/targets/glm.py",
            "docs/LOG_DOMAIN_SQRT.md",
        ),
        gaps=(
            "target coverage is software reference only; no measured junction",
            "mult/div/reciprocal are declared only on positive normalized inputs",
            "no voltage/current scaling or device netlist",
        ),
    ),
)

_BASE_IDS = {card.id for card in _BASE_MECHANISM_CARDS}
for _interpretation in INTERPRETATIONS:
    _interpretation.validate()
    if _interpretation.base_id not in _BASE_IDS:
        raise RuntimeError(
            f"interpretation {_interpretation.id!r} names unknown base "
            f"{_interpretation.base_id!r}"
        )

_BASE_BY_ID: dict[str, MechanismCard] = {
    card.id: card for card in _BASE_MECHANISM_CARDS
}


def generate_mechanism_card(
    interpretation: DeltaInterpretation,
    base: MechanismCard | None = None,
) -> MechanismCard:
    """Generate a domain card by executing its operator chain over a principle."""
    base_card = base or _BASE_BY_ID[interpretation.base_id]
    if base_card.id != interpretation.base_id:
        raise ValueError(
            f"interpretation {interpretation.id!r} expects base "
            f"{interpretation.base_id!r}, got {base_card.id!r}"
        )
    model: dict[str, Any] = {
        "operation": base_card.supported_operations[0],
        "primitive_chain": base_card.primitive_chain,
        "stateful": base_card.stateful,
        "feedback": False,
        "domain": base_card.source_domains[0],
        "carrier": base_card.carrier,
        "target_domain": interpretation.source_domains[0],
        "target_carrier": interpretation.carrier,
        "target_units": interpretation.carrier,
        "scale": interpretation.scale,
        "offset": interpretation.offset,
    }
    if interpretation.duality:
        model["duality"] = dict(interpretation.duality)
    for operator_id in interpretation.operators:
        operator = OPERATOR_BY_ID[operator_id]
        if not operator.check(model):
            raise ValueError(
                f"cannot derive {interpretation.id}: operator {operator_id} "
                f"rejected the model ({operator.precondition})"
            )
        model = operator.apply(model)
    card = MechanismCard(
        id=interpretation.id,
        name=interpretation.name,
        principle=interpretation.principle,
        source_domains=(model.get("domain", interpretation.source_domains[0]),),
        supported_operations=base_card.supported_operations,
        primitive_chain=base_card.primitive_chain,
        carrier=model.get("carrier", interpretation.carrier),
        stateful=base_card.stateful,
        invariants=interpretation.invariants,
        laws=interpretation.laws,
        validity=interpretation.validity,
        failure_modes=interpretation.failure_modes,
        evidence_level=interpretation.evidence_level,
        provenance=interpretation.provenance,
        gaps=interpretation.gaps,
        principle_id=base_card.id,
        operators=interpretation.operators,
    )
    card.validate()
    return card


GENERATED_MECHANISM_CARDS = tuple(
    generate_mechanism_card(interpretation)
    for interpretation in INTERPRETATIONS
)

# Preserve the original registry order: op-amp and fluid sit immediately after
# their shared KCL principle, before the cam/orifice/PLL cards.
_LIVE_BASE_CARDS = tuple(
    card for card in _BASE_MECHANISM_CARDS
    if card.id != "transcendental-identity"
)
MECHANISM_CARDS = (
    *_LIVE_BASE_CARDS[:3],
    *GENERATED_MECHANISM_CARDS,
    *_LIVE_BASE_CARDS[3:],
)

MECHANISM_BY_ID: dict[str, MechanismCard] = {
    card.id: card for card in MECHANISM_CARDS
}


def validate_mechanism_registry(
    cards: tuple[MechanismCard, ...] = MECHANISM_CARDS,
) -> None:
    """Validate a registry and reject duplicate ids or malformed cards."""
    ids = [card.id for card in cards]
    if len(set(ids)) != len(ids):
        raise ValueError("mechanism registry ids must be unique")
    for card in cards:
        card.validate()


def get_mechanism(card_id: str) -> MechanismCard:
    """Return one registered card or raise a keyed error with known ids."""
    key = str(card_id).strip()
    try:
        return MECHANISM_BY_ID[key]
    except KeyError as exc:
        known = ", ".join(sorted(MECHANISM_BY_ID))
        raise KeyError(f"unknown mechanism id {key!r}; known: {known}") from exc


def _render_items(items: tuple[str, ...]) -> list[str]:
    return [f"  - {item}" for item in items]


def render_mechanism_list(
    cards: tuple[MechanismCard, ...] = MECHANISM_CARDS,
) -> str:
    """Render the registry index for the terminal."""
    lines = [
        "=" * 78,
        "MECHANISM REGISTRY",
        "=" * 78,
        f"{len(cards)} seeded cent-mechanism/1 cards; source order",
        "",
    ]
    for card in cards:
        lines.extend(
            [
                card.id,
                f"  name: {card.name}",
                f"  evidence: {card.evidence_level}",
                f"  domains: {', '.join(card.source_domains)}",
                f"  operations: {', '.join(card.supported_operations)}",
                f"  first gap: {card.gaps[0] if card.gaps else 'none declared'}",
                "",
            ]
        )
    lines.append("Use `cent mechanism <id>` for one card; add --json for machine output.")
    return "\n".join(lines)


def render_mechanism(card: MechanismCard) -> str:
    """Render one full mechanism card for the terminal."""
    lines = [
        "=" * 78,
        "MECHANISM CARD",
        "=" * 78,
        f"id: {card.id}",
        f"name: {card.name}",
        f"evidence: {card.evidence_level}",
        f"carrier: {card.carrier}",
        f"stateful: {'yes' if card.stateful else 'no'}",
        f"source domains: {', '.join(card.source_domains)}",
        f"operations: {', '.join(card.supported_operations)}",
        f"primitive chain: {' -> '.join(card.primitive_chain)}",
        f"principle: {card.principle_id or 'self'}",
        f"operators: {', '.join(card.operators) or 'none'}",
        "",
        "Principle",
        f"  {card.principle}",
        "",
        "Invariants",
        *_render_items(card.invariants),
        "",
        "Laws",
        *_render_items(card.laws),
        "",
        "Validity",
        *_render_items(card.validity),
        "",
        "Failure modes",
        *_render_items(card.failure_modes),
        "",
        "Provenance",
        *_render_items(card.provenance),
        "",
        "Gaps",
        *_render_items(card.gaps),
    ]
    return "\n".join(lines)


if len(MECHANISM_BY_ID) != len(MECHANISM_CARDS):
    raise RuntimeError("mechanism registry contains duplicate ids")
validate_mechanism_registry()
