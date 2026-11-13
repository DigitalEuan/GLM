"""Experimental whole-machine composition side-arm.

A transfer candidate answers "can this operation be mapped to that mechanism?".
A machine answers a different question: "what surrounding stages does the
concept need before it can run, and which of those stages are actually
executed?"

This module is deliberately outside the main compile pipeline.  It composes a
complete signal-chain tree, uses the existing transfer retrieval rankings to
choose compatible core parts, runs the first executable machine model, and
keeps every unmodeled stage visible as a declared gap.  It is not a D-item, a
fabrication flow, or a measured-device claim.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import assembly
from .delta_sigma import DeltaSigmaEngine
from .isomorphism_gate import DECLARED_ANALOGIES
from .output_certificate import attach_certificate
from .spice_emitter import generate_spice_netlist
from .transfer_engine import transfer_payload

MACHINE_SCHEMA = "cent-machine/1"
TREE_SCHEMA = "cent-machine-tree/1"
SELECTION_SCHEMA = "cent-machine-selection/1"
VALIDATION_SCHEMA = "cent-machine-validation/1"
LIBRARY_SCHEMA = "cent-machine-library/1"
BUNDLE_SCHEMA = "cent-machine-bundle/1"
MACHINE_ID = "sigma-delta-sqrt"
CLAIM = (
    "A machine composes declared stages into a complete concept and executes "
    "only the stages named in its validation. It is not a fabricated device, "
    "no measured device is claimed, and it is not a proof that every declared "
    "physical stage works."
)
DEFAULT_SAMPLES = 100_000
DEFAULT_OSR = 64
DEFAULT_SAMPLE_RATE = 1_000_000.0
MIN_SAMPLES = 1_000
MAX_SAMPLES = 500_000
MAX_OSR = 4_096
DIGITAL_TOLERANCE = 1e-4
ROUTE_MACHINE_IDS = (
    "delta-sigma",
    "sqrt-log",
    "sqrt-feedback",
    "sum-kcl",
    "sum-fluid",
    "sum-opamp",
)
LOAD_DOMAINS = ("analog", "electrical", "mechanical", "fluid")
LOAD_DOMAIN_ALIASES = {
    "analog": "electrical",
    "electrical": "electrical",
    "mechanical": "mechanical",
    "fluid": "fluidics",
}
LOAD_ANALOGY_NAMES = {
    "mechanical": (
        "Electromechanical (Piezoelectric & Lorentz Force)",
        "Rotational-linear (textbook)",
    ),
    "fluidics": (
        "Electro-Hydrodynamic (Piezoresistive & Peristaltic Pump)",
        "Paynter effort-flow (impedance convention)",
    ),
}
ROUTE_OP_CONTRACTS = {
    "sum": "sum",
    "mult": "mult",
    "div": "div",
    "exp": "exp",
    "log": "log",
    "recip": "reciprocal",
    "sqrt": "sqrt",
    "quantize": "quantized_carry",
    "sign": "sign",
}
ROUTE_PREFERRED_MECHANISMS = {
    "delta-sigma": {"sum": "kcl-conservation", "quantize": "delta-sigma-error-feedback"},
    "sqrt-log": {"log": "log-domain-arithmetic", "exp": "log-domain-arithmetic"},
    "sqrt-feedback": {"sum": "kcl-conservation", "mult": "log-domain-arithmetic"},
    "sum-kcl": {"sum": "kcl-conservation"},
    "sum-fluid": {"sum": "fluid-continuity"},
    "sum-opamp": {"sum": "opamp-summing"},
}


def _text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} must be non-empty text")
    return text


DOMAIN_ALIASES = {
    "electronic": "electronics",
    "electrical": "electronics",
    "fluidic": "fluidics",
    "fluid": "fluidics",
    "mechanical": "mechanical",
    "audio": "audio",
}


def _normalize_domain(value: Any) -> str:
    text = str(value or "").strip().lower()
    return DOMAIN_ALIASES.get(text, text)


def _candidate_row(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Keep the reviewable part of a transfer candidate, not the full payload."""
    from .mechanisms import MECHANISM_BY_ID

    mechanism = MECHANISM_BY_ID.get(str(candidate.get("mechanism") or ""))
    mapping = []
    for step in candidate.get("mapping") or ():
        if isinstance(step, Mapping):
            mapping.append(
                {
                    "law": step.get("law"),
                    "kind": step.get("kind"),
                    "source": step.get("source"),
                    "target": step.get("target"),
                }
            )
    return {
        "id": candidate.get("id"),
        "rank": candidate.get("rank"),
        "mechanism": candidate.get("mechanism"),
        "source_domain": candidate.get("source_domain"),
        "target": candidate.get("target"),
        "evidence_level": candidate.get("evidence_level"),
        "status": candidate.get("status"),
        "declared_support": list(mechanism.supported_operations) if mechanism else [],
        "preserved": list(candidate.get("preserved") or ()),
        "mapping_laws": mapping,
        "gaps": list(candidate.get("gaps") or ()),
    }


def _candidate_ref(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": candidate.get("id"),
        "rank": candidate.get("rank"),
        "mechanism": candidate.get("mechanism"),
        "source_domain": candidate.get("source_domain"),
        "evidence_level": candidate.get("evidence_level"),
    }


def select_core_part(
    operation: str,
    *,
    target_id: str = "glm-reference",
    limit: int = 3,
    preferred_domains: Sequence[str] = ("electronics",),
    preferred_mechanisms: Sequence[str] = (),
) -> dict[str, Any]:
    """Select the highest-ranked compatible part for one machine stage.

    The policy is a domain-constrained ranking, not a global optimum.  A fluid
    sum is ranked first for the bare ``sum`` contract, for example, but it is
    not composable with the electrical/audio loop this machine declares.
    """
    payload = transfer_payload(operation, target_id=target_id, limit=limit)
    candidates = [
        _candidate_row(candidate)
        for candidate in payload.get("candidates") or ()
        if isinstance(candidate, Mapping)
    ]
    preferred = tuple(_normalize_domain(domain) for domain in preferred_domains)
    supported = [
        candidate
        for candidate in candidates
        if operation in (candidate.get("declared_support") or ())
    ]
    pool = supported or candidates
    preferred_mechanisms = tuple(str(mechanism) for mechanism in preferred_mechanisms)
    by_mechanism = [
        candidate
        for mechanism in preferred_mechanisms
        for candidate in pool
        if candidate.get("mechanism") == mechanism
    ]
    compatible = [
        candidate
        for candidate in pool
        if _normalize_domain(candidate.get("source_domain")) in preferred
    ]
    selected = (
        by_mechanism[0]
        if by_mechanism
        else (compatible[0] if compatible else (pool[0] if pool else None))
    )
    if selected is None:
        gap = f"no compiler candidate was retrieved for {operation!r}"
    elif selected is not None and selected.get("mechanism") in preferred_mechanisms:
        gap = None
    elif compatible:
        gap = None
    elif supported:
        gap = (
            f"no {operation!r} supported candidate declares a source domain in "
            f"{list(preferred)}; selected the top-ranked supported candidate"
        )
    else:
        gap = (
            f"no {operation!r} candidate declares explicit support; selected "
            "the top-ranked structural fallback"
        )
    return {
        "schema": SELECTION_SCHEMA,
        "operation": operation,
        "target": target_id,
        "preferred_domains": list(preferred),
        "policy": (
            "highest compiler rank with declared operation support and a "
            "source domain compatible with the machine path; otherwise the "
            "top-ranked supported candidate"
        ),
        "selected": selected,
        "alternatives": [_candidate_ref(candidate) for candidate in candidates],
        "declared_support_count": len(supported),
        "complete": selected is not None,
        "gap": gap,
    }


def _stage(
    path: str,
    name: str,
    kind: str,
    law: str,
    *,
    inputs: Sequence[str] = (),
    outputs: Sequence[str] = (),
    status: str,
    evidence: str,
    implementation: Mapping[str, Any],
    children: Sequence[Mapping[str, Any]] = (),
    constraints: Sequence[str] = (),
    gaps: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "path": path,
        "name": name,
        "kind": kind,
        "law": law,
        "inputs": list(inputs),
        "outputs": list(outputs),
        "status": status,
        "evidence": evidence,
        "implementation": dict(implementation),
        "constraints": list(constraints),
        "gaps": list(gaps),
        "children": list(children),
    }


def _stage_from_selection(
    path: str,
    name: str,
    kind: str,
    law: str,
    selection: Mapping[str, Any],
    *,
    inputs: Sequence[str],
    outputs: Sequence[str],
    constraints: Sequence[str] = (),
    status: str = "executed",
    evidence: str = "executed-model",
    gaps: Sequence[str] = (),
) -> dict[str, Any]:
    selected = selection.get("selected") or {}
    implementation = {
        "kind": "compiler-selected-part",
        "operation": selection.get("operation"),
        "mechanism": selected.get("mechanism"),
        "candidate": selected.get("id"),
        "rank": selected.get("rank"),
        "source_domain": selected.get("source_domain"),
        "evidence_level": selected.get("evidence_level"),
    }
    stage = _stage(
        path,
        name,
        kind,
        law,
        inputs=inputs,
        outputs=outputs,
        status=status,
        evidence=evidence,
        implementation=implementation,
        constraints=constraints,
        gaps=gaps,
    )
    stage["selection"] = dict(selection)
    return stage


def validate_sigma_delta_sqrt(
    *,
    samples: int = DEFAULT_SAMPLES,
    osr: int = DEFAULT_OSR,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
) -> dict[str, Any]:
    """Execute the first machine's declared digital branch."""
    if not isinstance(samples, int) or not MIN_SAMPLES <= samples <= MAX_SAMPLES:
        raise ValueError(
            f"samples must be an integer in [{MIN_SAMPLES}, {MAX_SAMPLES}]"
        )
    if not isinstance(osr, int) or not 1 <= osr <= MAX_OSR:
        raise ValueError(f"osr must be an integer in [1, {MAX_OSR}]")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    value = math.sqrt(2.0)
    scale = 0.99 / value
    normalized_input = value * scale
    reconstruction_scale = 1.0 / scale
    engine = DeltaSigmaEngine()
    dc = engine.carry_irrational(
        value,
        n_samples=samples,
        sample_rate=sample_rate,
        osr=osr,
    )
    bits = list(dc.bitstream)
    blocks = [
        sum(bits[index : index + osr]) / osr
        for index in range(0, len(bits) - osr + 1, osr)
    ]
    tail = max(1, len(blocks) // 4)
    decimated_scaled = sum(blocks) / len(blocks)
    digital_output = decimated_scaled / scale
    digital_error = abs(digital_output - value)
    one_bit = bool(bits) and all(bit in (-1, 1) for bit in bits)

    signal_frequency = 1_000.0
    ac = DeltaSigmaEngine().modulate(
        lambda index: 0.5
        * math.sin(2.0 * math.pi * signal_frequency * index / sample_rate),
        samples,
        sample_rate=sample_rate,
        signal_frequency=signal_frequency,
        osr=osr,
    )
    suppression = float(ac.suppression_db)
    slope = float(ac.ntf_slope_db_per_dec)
    checks = [
        {
            "name": "one-bit bitstream",
            "status": "pass" if one_bit else "fail",
            "detail": (
                f"{len(bits)} samples; values are exactly -1 and +1"
                if one_bit
                else "the modulator emitted a value outside {-1, +1}"
            ),
        },
        {
            "name": "decimated sqrt(2) output",
            "status": "pass" if digital_error <= DIGITAL_TOLERANCE else "fail",
            "detail": (
                f"decimated={digital_output:.15f}; target={value:.15f}; "
                f"error={digital_error:.3e}; tolerance={DIGITAL_TOLERANCE:.0e}"
            ),
        },
        {
            "name": "in-band noise suppression",
            "status": "pass" if suppression >= 30.0 else "fail",
            "detail": f"{suppression:.2f} dB measured against the unshaped reference",
        },
        {
            "name": "noise-transfer slope",
            "status": "pass" if slope >= 20.0 else "fail",
            "detail": f"{slope:.2f} dB/decade measured from the bitstream spectrum",
        },
    ]
    ok = all(check["status"] == "pass" for check in checks)
    return {
        "schema": VALIDATION_SCHEMA,
        "status": "pass" if ok else "fail",
        "ok": ok,
        "model": "delta-sigma first-order error-feedback engine",
        "target_value": value,
        "target_label": "sqrt(2)",
        "input_scale": scale,
        "normalized_input": normalized_input,
        "reconstruction_scale": reconstruction_scale,
        "samples": samples,
        "osr": osr,
        "sample_rate_hz": sample_rate,
        "bitstream_head": "".join("1" if bit > 0 else "0" for bit in bits[:64]),
        "metrics": {
            "digital_output": digital_output,
            "digital_error": digital_error,
            "inband_noise_suppression_db": suppression,
            "ntf_slope_db_per_dec": slope,
            "decimated_words": len(blocks),
            "tail_words": tail,
        },
        "checks": checks,
        "ntf_fit": {
            "method": "log-binned PSD linear fit",
            "bins": 50,
            "min_frequency_hz": sample_rate / samples,
            "max_frequency_hz": sample_rate / 4.0,
            "note": (
                f"The {slope:.2f} dB/dec figure is a finite-window fit near the "
                "loop corner; the ideal first-order asymptotic NTF slope is "
                "20.00 dB/dec."
            ),
        },
        "ntf_slope_note": (
            "The measured slope is a finite-window log-PSD fit, not an "
            "asymptotic filter order; the ideal first-order NTF is 20.00 dB/dec."
        ),
        "gaps": [
            "the analog reconstruction and power-buffer branches are not simulated",
            "clock jitter, supply rejection, the anti-alias filter and the reference rail are not transient-modeled",
            "the spectrum is a bitstream model, not a measured SQNR of a physical modulator",
        ],
    }


def _load_payload(load_domain: str) -> dict[str, Any]:
    requested = _text(load_domain, "load domain")
    domain = LOAD_DOMAIN_ALIASES.get(requested)
    if domain is None:
        raise ValueError(
            f"unknown load domain {requested!r}; expected one of "
            f"{', '.join(LOAD_DOMAINS)}"
        )
    if domain == "electrical":
        return {
            "requested": requested,
            "domain": "electrical",
            "status": "declared-gap",
            "transducer": None,
            "wheel_pair": [],
            "equations": [],
            "unit_scale_matrix": {},
            "scale_note": "no cross-domain scale is declared for the electrical branch",
            "gap": "the electrical reconstruction filter and power buffer are declared, not simulated",
        }
    names = LOAD_ANALOGY_NAMES.get(domain, ())
    analogy = next(
        (item for item in DECLARED_ANALOGIES if item.name in names), None
    )
    if analogy is None:
        return {
            "requested": requested,
            "domain": domain,
            "status": "declared-gap",
            "transducer": None,
            "wheel_pair": [],
            "equations": [],
            "unit_scale_matrix": {},
            "scale_note": f"no TIER 3 scale is declared for {domain}",
            "gap": f"no declared TIER 3 transducer wheel for {domain}",
        }
    return {
        "requested": requested,
        "domain": domain,
        "status": "declared-gap",
        "transducer": analogy.name,
        "wheel_pair": list(analogy.wheel_pair),
        "equations": list(analogy.transducer_equations),
        "unit_scale_matrix": dict(analogy.unit_scale_matrix),
        "scale_note": (
            "illustrative declared scale values with units; not calibrated "
            "device parameters and not used in a simulation"
        ),
        "gap": (
            f"the {analogy.name} load is declared from its wheel/transducer "
            "equations, not simulated"
        ),
    }


def _load_branch(load_domain: str) -> dict[str, Any]:
    load = _load_payload(load_domain)
    if load["domain"] == "electrical":
        reconstruction = _stage(
            "4B.1",
            "Reconstruction filter",
            "analog-filter",
            "H_rec(s) = ω0² / (s² + (ω0/Q)·s + ω0²)",
            inputs=["y_dac"],
            outputs=["y_rec"],
            status="gap",
            evidence="declared-gap",
            implementation={
                "kind": "declared-sallen-key",
                "detail": "the Sallen-Key stage is declared, not simulated",
            },
            gaps=["no ω0, Q, component values or analog transient"],
        )
        buffer = _stage(
            "4B.2",
            "Power buffer / actuator",
            "output-buffer",
            "Y_phys(t) = G_driver·(y_dac * h_rec)(t) ≈ √2",
            inputs=["y_rec"],
            outputs=["Y_phys"],
            status="gap",
            evidence="declared-gap",
            implementation={
                "kind": "declared-buffer",
                "detail": "the physical load branch is a concept, not a simulated driver",
            },
            gaps=["no load, driver, power stage or measured output"],
        )
        return _stage(
            "4B",
            "Analog / physical output branch",
            "branch",
            "reconstruct the one-bit stream into a physical load",
            status="gap",
            evidence="declared-gap",
            implementation={"kind": "stage-group"},
            children=[reconstruction, buffer],
            gaps=["the analog branch is declared but not executed"],
        )

    transducer = load.get("transducer") or f"{load['domain']} load"
    law = "; ".join(load.get("equations") or ()) or f"{transducer} transfer law"
    driver = _stage(
        "4B.1",
        f"{load['domain']} transducer",
        "load-transducer",
        law,
        inputs=["y_dac"],
        outputs=["load_input"],
        status="gap",
        evidence="declared-tier3",
        implementation={
            "kind": "declared-tier3-transducer",
            "transducer": load.get("transducer"),
            "wheel_pair": load.get("wheel_pair"),
            "unit_scale_matrix": load.get("unit_scale_matrix"),
            "scale_note": load.get("scale_note"),
            "detail": "selected from the declared TIER 3 transducer analogies",
        },
        gaps=[load.get("gap")],
    )
    output = _stage(
        "4B.2",
        f"{load['domain']} load / actuator",
        "output-buffer",
        f"Y_{load['domain']}(t) = load({transducer}(y_dac))",
        inputs=["load_input"],
        outputs=[f"Y_{load['domain']}"],
        status="gap",
        evidence="declared-gap",
        implementation={
            "kind": "declared-load",
            "detail": "the load transfer is declared, not simulated",
        },
        gaps=["no load impedance, efficiency, bandwidth or measured output"],
    )
    return _stage(
        "4B",
        f"{load['domain']} output branch",
        "branch",
        f"convert the electrical result to the {load['domain']} load",
        status="gap",
        evidence="declared-gap",
        implementation={
            "kind": "stage-group",
            "load": load,
        },
        children=[driver, output],
        gaps=[load.get("gap")],
    )


def _input_branch(validation: Mapping[str, Any] | None) -> dict[str, Any]:
    is_sqrt = bool(validation and validation.get("target_label") == "sqrt(2)")
    scale = (
        float(validation.get("input_scale", 0.99 / math.sqrt(2.0)))
        if is_sqrt and validation
        else 1.0
    )
    normalized = (
        float(validation.get("normalized_input", math.sqrt(2.0) * scale))
        if is_sqrt and validation
        else 1.0
    )
    source = _stage(
        "1.1",
        "Physical input source",
        "source",
        "x_raw(t) = A·x_target + n_env(t), A = 1.0",
        outputs=["x_raw"],
        status="declared",
        evidence="declared-input",
        implementation={
            "kind": "declared-input",
            "detail": "the route input is declared; no environmental noise is injected",
        },
        gaps=["n_env(t) is not modeled or measured"],
    )
    aaf = _stage(
        "1.2",
        "Anti-aliasing filter",
        "filter",
        "H_aaf(s) = 1 / (1 + s·R·C); x_in = x_raw * h_aaf",
        inputs=["x_raw"],
        outputs=["x_in"],
        status="declared",
        evidence="declared-law",
        implementation={
            "kind": "declared-first-order-rc",
            "detail": "no continuous-time RC transient is run",
        },
        gaps=["no RC value, bandwidth or transient response is declared"],
    )
    reference = _stage(
        "1.3",
        "Reference scaling",
        "constraint",
        "V_ref bounds the declared route input",
        outputs=["V_ref", "x_norm"],
        status="declared",
        evidence="declared-constraint",
        implementation={
            "kind": "declared-rail",
            "detail": (
                "the exact route uses normalized exact-rational inputs; "
                f"the input-conditioning scale is {scale:.15f} and the "
                f"normalized example is {normalized:.15f}"
            ),
        },
        gaps=["no actual rail voltage, headroom or overload model"],
    )
    return _stage(
        "1",
        "INPUT & REFERENCE CONDITIONING",
        "group",
        "condition a physical signal and bound the route input",
        status="declared",
        evidence="declared",
        implementation={"kind": "stage-group"},
        children=[source, aaf, reference],
        gaps=["the input conditioning chain is declared, not transient-simulated"],
    )


def _timing_branch() -> dict[str, Any]:
    clock = _stage(
        "3.1",
        "Master clock sampling",
        "timing",
        "t_n = n·T_s + Δt_jitter[n]",
        outputs=["t_n"],
        status="gap",
        evidence="declared-gap",
        implementation={
            "kind": "declared-constraint",
            "detail": "the exact route is untimed; no jitter process is run",
        },
        gaps=["clock jitter and its effect on the route are not modeled"],
    )
    supply = _stage(
        "3.2",
        "Power-supply rejection",
        "energy",
        "V_rail(t) = V_dc + PSRR·δv_digital(t)",
        outputs=["V_rail"],
        status="gap",
        evidence="declared-gap",
        implementation={
            "kind": "declared-constraint",
            "detail": "the model has no supply node or switching coupling",
        },
        gaps=["PSRR, supply impedance and digital coupling are not modeled"],
    )
    return _stage(
        "3",
        "TIMING & ENERGY BACKBONE",
        "group",
        "constraints that set the realizable clock and supply boundary",
        status="declared",
        evidence="declared",
        implementation={"kind": "stage-group"},
        children=[clock, supply],
        gaps=["timing and supply are declared constraints, not simulated"],
    )


def _tree(
    selections: Mapping[str, Mapping[str, Any]],
    validation: Mapping[str, Any] | None,
    load_domain: str = "analog",
) -> dict[str, Any]:
    sum_selection = selections["sum"]
    sign_selection = selections["sign"]
    carry_selection = selections["quantized_carry"]

    input_scale = float(validation.get("input_scale", 0.99 / math.sqrt(2.0)))
    normalized_input = float(
        validation.get("normalized_input", math.sqrt(2.0) * input_scale)
    )
    reconstruction_scale = float(validation.get("reconstruction_scale", 1.0 / input_scale))
    source = _stage(
        "1.1",
        "Physical input source",
        "source",
        "x_raw(t) = A·√2 + n_env(t), A = 1.0",
        outputs=["x_raw"],
        status="declared",
        evidence="declared-input",
        implementation={
            "kind": "declared-constant",
            "amplitude": 1.0,
            "target": math.sqrt(2.0),
            "detail": "√2 is the declared DC target; no environmental noise is injected",
        },
        gaps=["n_env(t) is not modeled or measured"],
    )
    aaf = _stage(
        "1.2",
        "Anti-aliasing filter",
        "filter",
        "H_aaf(s) = 1 / (1 + s·R·C); x_in = x_raw * h_aaf",
        inputs=["x_raw"],
        outputs=["x_in"],
        status="declared",
        evidence="declared-law",
        implementation={
            "kind": "declared-first-order-rc",
            "detail": "the DC machine does not run a continuous-time RC transient",
        },
        gaps=["no RC value, bandwidth or transient response is declared"],
    )
    reference = _stage(
        "1.3",
        "Reference scaling",
        "constraint",
        "V_ref > 1.4142·A; x_norm = x_raw·input_scale",
        outputs=["V_ref", "x_norm"],
        status="declared",
        evidence="declared-constraint",
        implementation={
            "kind": "declared-rail",
            "input_scale": input_scale,
            "normalized_input": normalized_input,
            "reconstruction_scale": reconstruction_scale,
            "detail": (
                "the model uses a normalized ±1 feedback level; "
                f"sqrt(2)·{input_scale:.15f} = {normalized_input:.15f}, "
                f"and the decimated result is multiplied by {reconstruction_scale:.15f}"
            ),
        },
        gaps=["no actual rail voltage, headroom or overload model"],
    )
    input_branch = _stage(
        "1",
        "INPUT & REFERENCE CONDITIONING",
        "group",
        "condition a physical signal and bound the loop rails",
        status="declared",
        evidence="declared",
        implementation={"kind": "stage-group"},
        children=[source, aaf, reference],
        gaps=["the input conditioning chain is declared, not transient-simulated"],
    )

    summing = _stage_from_selection(
        "2.1",
        "Summing junction (error node)",
        "summing-junction",
        "e[n] = x_in[n] - y_dac[n]",
        sum_selection,
        inputs=["x_in", "y_dac"],
        outputs=["e"],
        constraints=["signed exact sum", "error node inside the loop"],
    )
    loop_filter = _stage(
        "2.2",
        "Loop filter",
        "loop-filter",
        "u[n] = u[n-1] + e[n-1]; H_loop(z) = 1 / (1 - z^-1)",
        inputs=["e"],
        outputs=["u"],
        status="executed",
        evidence="executed-model",
        implementation={
            "kind": "executed-model",
            "model": "DeltaSigmaEngine.step",
            "detail": "first-order error-feedback integrator; the executed baseline",
        },
        constraints=["one state variable", "unit feedback"],
        gaps=[
            "the sketched leaky second-order loop is not the executed baseline",
            "no capacitor mismatch, finite gain or leakage is modeled",
        ],
    )
    quantizer = _stage_from_selection(
        "2.3",
        "1-bit quantizer",
        "quantizer",
        "b[n] = sgn(u[n]) in {-1, +1}",
        sign_selection,
        inputs=["u"],
        outputs=["b"],
        constraints=["hard threshold at zero", "no multi-bit output"],
    )
    dac = _stage(
        "2.4",
        "1-bit feedback DAC",
        "feedback-dac",
        "y_dac[n] = V_ref·b[n] (zero-order hold)",
        inputs=["b"],
        outputs=["y_dac"],
        status="executed",
        evidence="executed-model",
        implementation={
            "kind": "executed-model",
            "model": "unit feedback in DeltaSigmaEngine",
            "detail": "ideal ±1 feedback with a one-sample delay",
        },
        constraints=["ideal feedback levels", "zero-order hold"],
        gaps=["no DAC mismatch, settling, clock feedthrough or output impedance"],
    )
    closed_loop = _stage(
        "2.5",
        "Closed-loop output node",
        "output-node",
        "B(z) = STF(z)·X(z) + NTF(z)·Q(z)",
        inputs=["x_in", "q"],
        outputs=["B"],
        status="executed",
        evidence="executed-model",
        implementation={
            "kind": "executed-model",
            "model": "DeltaSigmaEngine.modulate",
            "detail": "the emitted bitstream and its measured spectrum",
            "note": validation.get("ntf_slope_note"),
        },
        constraints=["superposition is a declared linear model", "one-bit output"],
        gaps=["STF/NTF are measured from the bitstream, not from a circuit netlist"],
    )
    core = _stage(
        "2",
        "CORE SIGMA-DELTA MODULATOR LOOP",
        "group",
        "error feedback with a one-bit quantizer and a delayed DAC",
        status="executed",
        evidence="executed",
        implementation={"kind": "stage-group"},
        children=[summing, loop_filter, quantizer, dac, closed_loop],
        constraints=["closed loop", "oversampled", "one-bit quantizer"],
    )

    clock = _stage(
        "3.1",
        "Master clock sampling",
        "timing",
        "t_n = n·T_s + Δt_jitter[n]",
        outputs=["t_n"],
        status="gap",
        evidence="declared-gap",
        implementation={
            "kind": "declared-constraint",
            "detail": "a uniform sample clock is assumed; no jitter process is run",
        },
        gaps=["clock jitter variance and its SQNR floor are not modeled"],
    )
    supply = _stage(
        "3.2",
        "Power-supply rejection",
        "energy",
        "V_rail(t) = V_dc + PSRR·δv_digital(t)",
        outputs=["V_rail"],
        status="gap",
        evidence="declared-gap",
        implementation={
            "kind": "declared-constraint",
            "detail": "the model has no supply node or switching coupling",
        },
        gaps=["PSRR, supply impedance and digital coupling are not modeled"],
    )
    timing = _stage(
        "3",
        "TIMING & ENERGY BACKBONE",
        "group",
        "constraints that set the realizable clock and supply boundary",
        status="declared",
        evidence="declared",
        implementation={"kind": "stage-group"},
        children=[clock, supply],
        gaps=["timing and supply are declared constraints, not simulated"],
    )

    cic = _stage(
        "4A.1",
        "CIC / FIR low-pass filter",
        "decimator",
        "H_dec(z) = [(1 - z^-M) / (1 - z^-1)]^K",
        inputs=["B"],
        outputs=["filtered"],
        status="executed",
        evidence="executed-model",
        implementation={
            "kind": "executed-model",
            "model": "block-average decimator",
            "detail": "K=1 boxcar over M=OSR samples; the declared CIC first stage",
        },
        constraints=["M = OSR", "K = 1"],
        gaps=["higher-order CIC stages and FIR passband/stopband design are not modeled"],
    )
    downsampler = _stage(
        "4A.2",
        "Downsampler",
        "downsampler",
        "Y_dig[k] = (b * h_dec)[k·M] ≈ √2",
        inputs=["filtered"],
        outputs=["Y_dig"],
        status="executed",
        evidence="executed-model",
        implementation={
            "kind": "executed-model",
            "model": "block decimation",
            "detail": f"{validation.get('metrics', {}).get('decimated_words', 0)} words"
            if validation
            else "not run",
        },
        constraints=["M = OSR", "one output word per full block"],
    )
    digital = _stage(
        "4A",
        "Digital output branch",
        "branch",
        "decimate the bitstream and reconstruct the target value",
        status="executed",
        evidence="executed",
        implementation={"kind": "stage-group"},
        children=[cic, downsampler],
        constraints=["digital reconstruction"],
    )

    analog = _load_branch(load_domain)
    reconstruction_branch = _stage(
        "4",
        "RECONSTRUCTION / DEMODULATION STAGE",
        "group",
        "extract the target value in digital and physical forms",
        status="partial",
        evidence="mixed",
        implementation={"kind": "stage-group"},
        children=[digital, analog],
    )

    return {
        "schema": TREE_SCHEMA,
        "id": MACHINE_ID,
        "label": "MACHINE: Y_out(t) ≈ √2",
        "status": "partial",
        "permalink": "machine://sigma-delta-sqrt",
        "root": {
            "path": "0",
            "name": "Y_out(t) ≈ √2",
            "kind": "function",
            "law": "carry and recover the declared irrational sqrt(2) as a one-bit temporal stream",
            "status": "partial",
            "evidence": "executable-digital-branch",
            "implementation": {
                "kind": "machine",
                "digital_branch": "executed",
                "analog_branch": "declared-gap",
            },
            "constraints": [
                "the declared target is sqrt(2)",
                "the executed loop is first-order error feedback",
                "the one-bit stream is reconstructed by block decimation",
            ],
            "gaps": [
                "the analog output branch is not executed",
                "the timing and supply constraints are not modeled",
            ],
            "children": [input_branch, core, timing, reconstruction_branch],
        },
    }


def _flatten(stages: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for stage in stages:
        rows.append(stage)
        rows.extend(_flatten(stage.get("children") or ()))
    return rows


SIGMA_DELTA_REQUIRED_ROLES = [
    ("source", "source"),
    ("anti-alias filter", "filter"),
    ("reference scaling", "constraint"),
    ("summing junction", "summing-junction"),
    ("loop filter", "loop-filter"),
    ("quantizer", "quantizer"),
    ("feedback DAC", "feedback-dac"),
    ("master clock", "timing"),
    ("supply rejection", "energy"),
    ("decimator", "decimator"),
    ("reconstruction filter", "analog-filter"),
    ("power buffer", "output-buffer"),
]


def _coverage(
    tree: Mapping[str, Any],
    required: Sequence[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    required = list(required or SIGMA_DELTA_REQUIRED_ROLES)
    stages = _flatten((tree.get("root") or {}).get("children") or ())
    kinds = {stage.get("kind") for stage in stages}
    present = [label for label, kind in required if kind in kinds]
    missing = [label for label, kind in required if kind not in kinds]
    modeled = [
        stage.get("name")
        for stage in stages
        if stage.get("status") in {"executed", "compiler-selected"}
    ]
    declared = [
        stage.get("name")
        for stage in stages
        if stage.get("status") == "declared"
    ]
    gaps = [
        stage.get("name")
        for stage in stages
        if stage.get("status") == "gap"
    ]
    return {
        "required_roles": [label for label, _ in required],
        "present_roles": present,
        "missing_roles": missing,
        "modeled_roles": modeled,
        "declared_roles": declared,
        "gap_roles": gaps,
    }


def _build_sigma_delta_machine(
    machine_id: str = MACHINE_ID,
    *,
    target_id: str = "glm-reference",
    limit: int = 3,
    samples: int = DEFAULT_SAMPLES,
    osr: int = DEFAULT_OSR,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    validate: bool = True,
    load_domain: str = "analog",
) -> dict[str, Any]:
    """Compose the hand-authored sigma-delta sqrt machine."""
    machine_id = _text(machine_id, "machine.id")
    if machine_id != MACHINE_ID:
        raise ValueError(
            f"unknown machine {machine_id!r}; known: {MACHINE_ID} (use `cent machine list`)"
        )
    selections = {
        "sum": select_core_part(
            "sum",
            target_id=target_id,
            limit=limit,
            preferred_domains=("electronics",),
        ),
        "sign": select_core_part(
            "sign",
            target_id=target_id,
            limit=limit,
            preferred_domains=("electronics",),
        ),
        "quantized_carry": select_core_part(
            "quantized_carry",
            target_id=target_id,
            limit=limit,
            preferred_domains=("audio", "electronics"),
        ),
    }
    validation = (
        validate_sigma_delta_sqrt(
            samples=samples, osr=osr, sample_rate=sample_rate
        )
        if validate
        else {
            "schema": VALIDATION_SCHEMA,
            "status": "not-run",
            "ok": False,
            "model": "delta-sigma first-order error-feedback engine",
            "target_value": math.sqrt(2.0),
            "target_label": "sqrt(2)",
            "input_scale": 0.99 / math.sqrt(2.0),
            "samples": samples,
            "osr": osr,
            "sample_rate_hz": sample_rate,
            "bitstream_head": "",
            "metrics": {},
            "checks": [],
            "gaps": ["machine validation was skipped"],
        }
    )
    tree = _tree(selections, validation, load_domain=load_domain)
    load = _load_payload(load_domain)
    coverage = _coverage(tree)
    selection_ok = all(selection.get("complete") for selection in selections.values())
    checks = [
        {
            "name": "complete machine roles",
            "status": "pass" if not coverage["missing_roles"] else "fail",
            "detail": (
                f"{len(coverage['present_roles'])}/{len(coverage['required_roles'])} "
                "required roles are present"
            ),
        },
        {
            "name": "compiler-selected core parts",
            "status": "pass" if selection_ok else "fail",
            "detail": (
                f"{sum(1 for selection in selections.values() if selection.get('complete'))}"
                f"/{len(selections)} core stage selections are complete"
            ),
        },
        {
            "name": "executable digital branch",
            "status": "pass" if validation.get("ok") else "fail",
            "detail": (
                f"output error {validation.get('metrics', {}).get('digital_error')}"
                if validation.get("ok")
                else "the machine model did not pass every declared check"
            ),
        },
        {
            "name": "declared boundary",
            "status": "pass",
            "detail": "analog, timing and supply stages remain explicit gaps",
        },
    ]
    gaps = [
        "the analog reconstruction and power-buffer branches are declared, not simulated",
        "clock jitter and supply rejection are declared constraints, not modeled",
        "the anti-alias filter and reference rail are declared, not transient-simulated",
        "machine.cir is a behavioral electrical core, not a fabrication netlist",
        "no measured device or physical prototype is claimed",
        *([load.get("gap")] if load.get("gap") else []),
    ]
    gaps.extend(
        selection["gap"]
        for selection in selections.values()
        if selection.get("gap")
    )
    ok = (
        not coverage["missing_roles"]
        and selection_ok
        and bool(validation.get("ok"))
        and all(check["status"] == "pass" for check in checks)
    )
    headline = (
        f"{len(coverage['present_roles'])}/{len(coverage['required_roles'])} "
        f"required roles present; {sum(1 for selection in selections.values() if selection.get('complete'))}"
        f"/{len(selections)} core parts selected; "
        + (
            f"digital error {validation.get('metrics', {}).get('digital_error'):.3e}; "
            if validation.get("ok")
            else "digital branch not run; "
        )
        + f"{len(coverage['gap_roles'])} unmodeled stage(s) remain gaps."
    )
    return {
        "ok": ok,
        "schema": MACHINE_SCHEMA,
        "id": MACHINE_ID,
        "label": tree["label"],
        "status": "executable-digital-branch" if ok else "partial",
        "target": {
            "id": target_id,
            "value": validation.get("target_value"),
            "label": validation.get("target_label"),
        },
        "tree": tree,
        "selections": {name: selection for name, selection in selections.items()},
        "load": load,
        "coverage": coverage,
        "validation": validation,
        "checks": checks,
        "gaps": list(dict.fromkeys(gaps)),
        "artifacts": {
            "machine_json": "machine.json",
            "machine_markdown": "machine.md",
            "core_cir": {
                "file": "machine.cir",
                "kind": "behavioral-electrical-core",
                "active_transient": False,
                "fabrication": False,
            },
        },
        "headline": headline,
        "claim": CLAIM,
    }


def build_machine(
    machine_id: str = MACHINE_ID,
    *,
    target_id: str = "glm-reference",
    limit: int = 3,
    samples: int = DEFAULT_SAMPLES,
    osr: int = DEFAULT_OSR,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    validate: bool = True,
    load_domain: str = "analog",
) -> dict[str, Any]:
    """Compose a handcrafted machine or wrap an assembled route."""
    machine_id = _text(machine_id, "machine.id")
    if machine_id in ROUTE_MACHINE_IDS:
        return build_route_machine(
            machine_id,
            target_id=target_id,
            limit=limit,
            load_domain=load_domain,
            validate=validate,
        )
    return _build_sigma_delta_machine(
        machine_id,
        target_id=target_id,
        limit=limit,
        samples=samples,
        osr=osr,
        sample_rate=sample_rate,
        validate=validate,
        load_domain=load_domain,
    )


def _route_factory(route_id: str) -> Any:
    if route_id == "delta-sigma":
        return assembly.delta_sigma_route()
    if route_id == "sqrt-log":
        return assembly.log_domain_sqrt_route()
    if route_id == "sqrt-feedback":
        return assembly.opamp_multiplier_sqrt_route()
    if route_id == "sum-kcl":
        return assembly.kcl_sum_route()
    if route_id == "sum-fluid":
        return assembly.fluid_sum_route()
    if route_id == "sum-opamp":
        return assembly.opamp_sum_route()
    raise ValueError(f"unknown assembled route {route_id!r}")


def _route_run(route_id: str, route: Any) -> Any:
    if route_id in {"sum-kcl", "sum-fluid", "sum-opamp"}:
        return route.simulate("1/2", "1/3")
    if route_id == "delta-sigma":
        return route.simulate("1/2", samples=16)
    return route.simulate("2")


def _route_validation(route_id: str, route: Any, validate: bool) -> dict[str, Any]:
    if not validate:
        return {
            "schema": VALIDATION_SCHEMA,
            "status": "not-run",
            "ok": False,
            "model": "assembled exact route",
            "target_label": route_id,
            "checks": [],
            "metrics": {},
            "run": None,
            "gaps": ["route execution was skipped"],
        }
    run = _route_run(route_id, route)
    run_doc = run.as_dict()
    passed = bool(run_doc.get("passed"))
    return {
        "schema": VALIDATION_SCHEMA,
        "status": "pass" if passed else "fail",
        "ok": passed,
        "model": "assembled exact route",
        "target_label": route_id,
        "run": run_doc,
        "metrics": {
            "passed": passed,
            "route": route_id,
            "result": run_doc.get("result"),
        },
        "checks": [
            {
                "name": "exact route execution",
                "status": "pass" if passed else "fail",
                "detail": f"{route_id} exact route run {'passed' if passed else 'failed'}",
            }
        ],
        "gaps": [
            "the route is exact and typed, but its physical load is not simulated",
        ],
    }


def _route_selection(
    route_id: str,
    op: str,
    *,
    target_id: str,
    limit: int,
    route_domain: str,
) -> dict[str, Any] | None:
    contract = ROUTE_OP_CONTRACTS.get(op)
    if contract is None:
        return None
    return select_core_part(
        contract,
        target_id=target_id,
        limit=limit,
        preferred_domains=tuple(
            dict.fromkeys((route_domain, "electronics", "audio"))
        ),
        preferred_mechanisms=(
            (ROUTE_PREFERRED_MECHANISMS.get(route_id, {}).get(op),)
            if ROUTE_PREFERRED_MECHANISMS.get(route_id, {}).get(op)
            else ()
        ),
    )


def _route_core_stage(
    route_id: str,
    graph: Mapping[str, Any],
    selections: Mapping[str, Mapping[str, Any]],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    children: list[dict[str, Any]] = []
    for index, node in enumerate(graph.get("nodes") or (), start=1):
        if not isinstance(node, Mapping):
            continue
        op = str(node.get("op") or "")
        lowering = node.get("lowering") if isinstance(node.get("lowering"), Mapping) else {}
        selection = selections.get(op)
        inputs = [
            f"{item.get('port')}={item.get('wire')}"
            for item in node.get("inputs") or ()
            if isinstance(item, Mapping)
        ]
        outputs = [
            f"{item.get('port')}={item.get('wire')}"
            for item in node.get("outputs") or ()
            if isinstance(item, Mapping)
        ]
        stage = _stage(
            f"2.{index}",
            f"¢_{op} ({node.get('id')})",
            "route-primitive",
            str(lowering.get("law") or f"{op}: declared exact route node"),
            inputs=inputs,
            outputs=outputs,
            status="executed" if validation.get("ok") else "gap",
            evidence="route-executed" if validation.get("ok") else "declared-gap",
            implementation={
                "kind": "executed-route-node",
                "route": route_id,
                "node": node.get("id"),
                "op": op,
                "lowering": lowering.get("kind"),
                "detail": "node from the route's cent-typed-graph/1",
            },
            gaps=list(lowering.get("gaps") or ()),
        )
        if selection is not None:
            stage["selection"] = dict(selection)
        children.append(stage)
    if not children:
        children.append(
            _stage(
                "2.1",
                "Route core",
                "route-primitive",
                "the assembled route declares no typed primitive nodes",
                status="gap",
                evidence="declared-gap",
                implementation={"kind": "gap"},
                gaps=["no typed route node is available"],
            )
        )
    return _stage(
        "2",
        "CORE ROUTE GRAPH",
        "group",
        "the assembled route's exact typed primitives",
        status="executed" if validation.get("ok") else "partial",
        evidence="route-executed" if validation.get("ok") else "declared",
        implementation={"kind": "stage-group", "route": route_id},
        children=children,
        constraints=["preserve the route's typed graph and lowerings"],
        gaps=list(graph.get("gaps") or ()),
    )


def _route_tree(
    route_id: str,
    route_name: str,
    description: str,
    graph: Mapping[str, Any],
    selections: Mapping[str, Mapping[str, Any]],
    validation: Mapping[str, Any],
    load_domain: str,
) -> dict[str, Any]:
    input_branch = _input_branch(validation)
    core = _route_core_stage(route_id, graph, selections, validation)
    timing = _timing_branch()
    run = validation.get("run") or {}
    output = _stage(
        "4A.1",
        "Exact route output",
        "route-output",
        f"route {route_id} emits its declared exact result",
        inputs=[],
        outputs=["result"],
        status="executed" if validation.get("ok") else "gap",
        evidence="route-executed" if validation.get("ok") else "declared-gap",
        implementation={
            "kind": "executed-route-run",
            "route": route_id,
            "result": run.get("result"),
            "detail": "the route's own exact simulation result",
        },
        gaps=[],
    )
    digital = _stage(
        "4A",
        "ROUTE OUTPUT",
        "branch",
        "expose the assembled route's exact output",
        status="executed" if validation.get("ok") else "gap",
        evidence="route-executed" if validation.get("ok") else "declared-gap",
        implementation={"kind": "stage-group"},
        children=[output],
        constraints=["no hidden result is added"],
    )
    load = _load_branch(load_domain)
    reconstruction_branch = _stage(
        "4",
        "RECONSTRUCTION / LOAD STAGE",
        "group",
        "extract the route output and connect it to a declared load",
        status="partial" if load.get("status") == "declared-gap" else "executed",
        evidence="mixed",
        implementation={"kind": "stage-group", "load": _load_payload(load_domain)},
        children=[digital, load],
    )
    return {
        "schema": TREE_SCHEMA,
        "id": route_id,
        "label": f"MACHINE: {route_name}",
        "status": "partial",
        "permalink": f"machine://{route_id}",
        "root": {
            "path": "0",
            "name": route_name,
            "kind": "function",
            "law": description,
            "status": "partial",
            "evidence": "executable-route-core",
            "implementation": {
                "kind": "route-wrapper",
                "route": route_id,
                "load_domain": load_domain,
            },
            "constraints": [
                "the core is the assembled route, not a new simulation",
                "the load branch is declared unless the electrical default is used",
            ],
            "gaps": [
                "the load and timing stages are not simulated",
                "the route's declared gaps are preserved",
            ],
            "children": [input_branch, core, timing, reconstruction_branch],
        },
    }


def _route_required_roles(load_domain: str) -> list[tuple[str, str]]:
    load = _load_payload(load_domain)
    load_roles = (
        [("reconstruction filter", "analog-filter"), ("power buffer", "output-buffer")]
        if load.get("domain") == "electrical"
        else [("load transducer", "load-transducer"), ("load / actuator", "output-buffer")]
    )
    return [
        ("source", "source"),
        ("anti-alias filter", "filter"),
        ("reference scaling", "constraint"),
        ("route primitive", "route-primitive"),
        ("route output", "route-output"),
        ("master clock", "timing"),
        ("supply rejection", "energy"),
        *load_roles,
    ]


def build_route_machine(
    route_id: str,
    *,
    target_id: str = "glm-reference",
    limit: int = 3,
    load_domain: str = "analog",
    validate: bool = True,
) -> dict[str, Any]:
    """Wrap an assembled exact route in the four-stage machine template."""
    route_id = _text(route_id, "machine.route")
    if route_id not in ROUTE_MACHINE_IDS:
        raise ValueError(
            f"unknown route machine {route_id!r}; known: {', '.join(ROUTE_MACHINE_IDS)}"
        )
    load = _load_payload(load_domain)
    route = _route_factory(route_id)
    document = route.as_dict()
    graph = document.get("typed_graph") if isinstance(document.get("typed_graph"), Mapping) else {}
    components = document.get("components") or []
    route_domain = "electrical"
    if components and isinstance(components[0], Mapping):
        contract = components[0].get("contract") or {}
        if isinstance(contract, Mapping) and contract.get("domain"):
            route_domain = _normalize_domain(contract["domain"])
    validation = _route_validation(route_id, route, validate)
    selections: dict[str, Mapping[str, Any]] = {}
    for node in graph.get("nodes") or ():
        if not isinstance(node, Mapping):
            continue
        op = str(node.get("op") or "")
        if op in selections or op not in ROUTE_OP_CONTRACTS:
            continue
        selection = _route_selection(
            route_id, op, target_id=target_id, limit=limit, route_domain=route_domain
        )
        if selection is not None:
            selections[op] = selection
    tree = _route_tree(
        route_id,
        str(document.get("name") or route_id),
        str(document.get("description") or "assembled exact route"),
        graph,
        selections,
        validation,
        load_domain,
    )
    coverage = _coverage(tree, _route_required_roles(load_domain))
    selection_ok = bool(selections) and all(
        selection.get("complete") for selection in selections.values()
    )
    checks = [
        {
            "name": "complete machine roles",
            "status": "pass" if not coverage["missing_roles"] else "fail",
            "detail": (
                f"{len(coverage['present_roles'])}/{len(coverage['required_roles'])} "
                "required roles are present"
            ),
        },
        {
            "name": "compiler-selected route primitives",
            "status": "pass" if selection_ok else "fail",
            "detail": (
                f"{sum(1 for selection in selections.values() if selection.get('complete'))}"
                f"/{len(selections)} mapped route primitive(s) have a complete selection"
            ),
        },
        {
            "name": "executable route core",
            "status": "pass" if validation.get("ok") else "fail",
            "detail": (
                "the assembled exact route run passed"
                if validation.get("ok")
                else "the assembled exact route run did not pass"
            ),
        },
        {
            "name": "declared load boundary",
            "status": "pass",
            "detail": f"load domain {load.get('domain')} is declared; no load is measured",
        },
    ]
    gaps = list(
        dict.fromkeys(
            (
                *document.get("gaps", ()),
                "the load branch is declared, not simulated",
                *( [load.get("gap")] if load.get("gap") else [] ),
                "the route is wrapped with declared input conditioning, clock and supply stages",
                "no measured device or fabrication netlist is claimed",
            )
        )
    )
    ok = (
        not coverage["missing_roles"]
        and selection_ok
        and bool(validation.get("ok"))
        and all(check["status"] == "pass" for check in checks)
    )
    return {
        "ok": ok,
        "schema": MACHINE_SCHEMA,
        "id": route_id,
        "kind": "route-wrapper",
        "label": tree["label"],
        "status": "executable-route-core" if ok else "partial",
        "target": {
            "id": route_id,
            "value": (validation.get("run") or {}).get("result"),
            "label": str(document.get("name") or route_id),
        },
        "tree": tree,
        "selections": dict(selections),
        "load": load,
        "coverage": coverage,
        "validation": validation,
        "checks": checks,
        "gaps": gaps,
        "artifacts": {
            "machine_json": "machine.json",
            "machine_markdown": "machine.md",
            "core_cir": {
                "file": "machine.cir",
                "kind": "declared-gap",
                "active_transient": False,
                "fabrication": False,
                "gap": "no route-specific electrical netlist emitter is declared",
            },
        },
        "headline": (
            f"{len(coverage['present_roles'])}/{len(coverage['required_roles'])} "
            f"required roles present; {len(selections)} route primitive(s) "
            f"selected; core run {'passed' if validation.get('ok') else 'not passing'}; "
            f"load {load.get('domain')} is declared only."
        ),
        "claim": CLAIM,
    }


def library_payload() -> dict[str, Any]:
    """Return the declared machine library without running a model."""
    return {
        "ok": True,
        "schema": LIBRARY_SCHEMA,
        "machines": [
            {
                "id": MACHINE_ID,
                "label": "MACHINE: Y_out(t) ≈ √2",
                "kind": "hand-authored",
                "summary": (
                    "A one-bit delta-sigma signal chain with input conditioning, "
                    "a first-order loop, digital decimation and an explicit "
                    "unmodeled analog branch."
                ),
                "command": "python3 cent machine sigma-delta-sqrt",
            },
            *[
                {
                    "id": route_id,
                    "label": f"MACHINE: {route_id} route wrapper",
                    "kind": "assembled-route-wrapper",
                    "summary": (
                        "The assembled exact route wrapped in the four-stage "
                        "machine template with compiler-ranked primitive selections."
                    ),
                    "command": f"python3 cent machine {route_id} --load analog",
                }
                for route_id in ROUTE_MACHINE_IDS
            ],
        ],
        "load_domains": list(LOAD_DOMAINS),
        "checks": [
            {
                "name": "declared machine library",
                "status": "pass",
                "detail": (
                    f"1 hand-authored machine and {len(ROUTE_MACHINE_IDS)} "
                    "assembled-route wrappers are registered"
                ),
            }
        ],
    }


def _selection_line(selection: Mapping[str, Any]) -> str:
    selected = selection.get("selected") or {}
    if not selected:
        return "no compiler-selected part"
    return (
        f"{selection.get('operation')} -> {selected.get('mechanism')} "
        f"(rank {selected.get('rank')}, {selected.get('source_domain')})"
    )


def render_machine(payload: Mapping[str, Any]) -> str:
    """Render the whole staged concept and its evidence boundary."""
    lines = ["=" * 78, str(payload.get("label") or "CENT MACHINE"), "=" * 78]
    lines.append(str(payload.get("headline") or ""))
    lines.append(
        f"status: {payload.get('status')} · target: "
        f"{(payload.get('target') or {}).get('label')}"
    )
    lines.append("")

    def walk(node: Mapping[str, Any], prefix: str, last: bool) -> None:
        connector = "└── " if last else "├── "
        lines.append(
            f"{prefix}{connector}{node.get('path')} {node.get('name')} "
            f"[{node.get('status')}]"
        )
        continuation = "    " if last else "│   "
        law = node.get("law")
        if law:
            lines.append(f"{prefix}{continuation}law: {law}")
        implementation = node.get("implementation") or {}
        if "input_scale" in implementation:
            lines.append(
                f"{prefix}{continuation}scale: input "
                f"{implementation.get('input_scale'):.15f} -> normalized "
                f"{implementation.get('normalized_input'):.15f}; reconstruction "
                f"{implementation.get('reconstruction_scale'):.15f}"
            )
        if implementation.get("note"):
            lines.append(f"{prefix}{continuation}note: {implementation['note']}")
        selection = node.get("selection") or {}
        if selection:
            lines.append(
                f"{prefix}{continuation}part: {_selection_line(selection)}"
            )
        children = list(node.get("children") or ())
        for index, child in enumerate(children):
            walk(child, prefix + continuation, index == len(children) - 1)

    root = payload.get("tree", {}).get("root") or {}
    lines.append(
        f"{root.get('name')} [{root.get('status')}] — {root.get('law')}"
    )
    children = list(root.get("children") or ())
    for index, child in enumerate(children):
        walk(child, "", index == len(children) - 1)

    lines.append("")
    lines.append("COMPILER-SELECTED CORE PARTS")
    for name, selection in (payload.get("selections") or {}).items():
        lines.append(f"  {name}: {_selection_line(selection)}")
        alternatives = selection.get("alternatives") or []
        if alternatives:
            lines.append(
                "    alternatives: "
                + ", ".join(
                    f"{row.get('mechanism')} (rank {row.get('rank')}, "
                    f"{row.get('source_domain')})"
                    for row in alternatives
                    if row.get("mechanism") != (selection.get("selected") or {}).get("mechanism")
                )
            )

    lines.append("")
    lines.append("EXECUTED CORE")
    validation = payload.get("validation") or {}
    metrics = validation.get("metrics") or {}
    if validation.get("ok") and "digital_output" in metrics:
        lines.append(
            f"  sqrt(2) -> {metrics.get('digital_output'):.15f} "
            f"(error {metrics.get('digital_error'):.3e})"
        )
        lines.append(
            f"  in-band suppression {metrics.get('inband_noise_suppression_db'):.2f} dB; "
            f"NTF slope {metrics.get('ntf_slope_db_per_dec'):.2f} dB/dec"
        )
        for check in validation.get("checks") or ():
            lines.append(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
        if validation.get("ntf_slope_note"):
            lines.append(f"  note: {validation['ntf_slope_note']}")
    elif validation.get("ok"):
        run = validation.get("run") or {}
        result = run.get("result", metrics.get("result"))
        lines.append(f"  route result: {result}")
        for check in validation.get("checks") or ():
            lines.append(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    else:
        lines.append("  not run or not passing; inspect validation.checks")
    lines.append("")
    lines.append("COVERAGE")
    coverage = payload.get("coverage") or {}
    lines.append(
        f"  roles: {len(coverage.get('present_roles') or [])}/"
        f"{len(coverage.get('required_roles') or [])} present"
    )
    if coverage.get("missing_roles"):
        lines.append("  missing: " + ", ".join(coverage["missing_roles"]))
    lines.append(
        "  unmodeled: " + (", ".join(coverage.get("gap_roles") or []) or "none")
    )
    lines.append("")
    lines.append("GAPS")
    for gap in payload.get("gaps") or ():
        lines.append(f"  - {gap}")
    lines.append("")
    lines.append(str(payload.get("claim") or ""))
    return "\n".join(lines)


def render_library(payload: Mapping[str, Any]) -> str:
    lines = ["=" * 78, "CENT MACHINE LIBRARY", "=" * 78]
    for machine in payload.get("machines") or ():
        lines.append(f"{machine.get('id')}: {machine.get('label')}")
        lines.append(f"  {machine.get('summary')}")
        lines.append(f"  {machine.get('command')}")
    lines.append("")
    lines.append(
        "A machine is a complete concept tree, not a validated fabrication or a measured device."
    )
    return "\n".join(lines)


def write_machine(payload: Mapping[str, Any], directory: str | Path) -> list[Path]:
    """Write a portable machine bundle: JSON, Markdown and a core .cir."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    machine_path = root / "machine.json"
    document = attach_certificate(payload)
    machine_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    paths.append(machine_path)
    markdown_path = root / "machine.md"
    markdown_path.write_text(
        "# " + str(payload.get("label") or "Cent machine") + "\n\n"
        + "```text\n"
        + render_machine(payload)
        + "\n```\n",
        encoding="utf-8",
    )
    paths.append(markdown_path)
    validation = payload.get("validation") or {}
    netlist_path = root / "machine.cir"
    header = (
        "* Machine concept: "
        + str(payload.get("label") or "cent machine")
        + "\n* This is a declared core bundle, not a fabrication netlist.\n"
        "* It is not a measured device or a mixed-signal simulation.\n"
    )
    if payload.get("id") == MACHINE_ID:
        core = generate_spice_netlist(
            "delta_sigma",
            input_value=float(validation.get("input_scale", 0.99)),
            n_samples=int(validation.get("samples", DEFAULT_SAMPLES)),
        )
    else:
        core = (
            "* No route-specific electrical netlist emitter is declared for this "
            "assembled route.\n"
            "* The route itself remains an exact cent-route/1 model; this file is "
            "a declared gap.\n"
        )
    netlist_path.write_text(header + core, encoding="utf-8")
    paths.append(netlist_path)
    return paths


__all__ = [
    "BUNDLE_SCHEMA",
    "CLAIM",
    "DEFAULT_OSR",
    "DEFAULT_SAMPLES",
    "DIGITAL_TOLERANCE",
    "LIBRARY_SCHEMA",
    "MACHINE_ID",
    "MACHINE_SCHEMA",
    "SELECTION_SCHEMA",
    "TREE_SCHEMA",
    "VALIDATION_SCHEMA",
    "build_machine",
    "library_payload",
    "render_library",
    "render_machine",
    "select_core_part",
    "validate_sigma_delta_sqrt",
    "write_machine",
]
