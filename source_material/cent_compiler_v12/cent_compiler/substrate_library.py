"""
The ∆ enumerator.

For a given £ (abstract operation) decomposed into a ¢ DAG, enumerate ALL
valid ∆ implementations — not just one canonical one.

Key idea: each composite ¢ primitive (sqrt, eq, recip, div) can be EXPANDED
multiple ways before substrate matching:

  ¢_sqrt  →  {analog-feedback, mechanical-cam, digital-delta-sigma, fluidic-orifice}
  ¢_eq    →  {op-amp-feedback, mechanical-servo, hydraulic-servo, thermal-relaxation}
  ¢_accum →  {capacitor, inductor-flux, mass, thermal-mass, flywheel}
  ¢_wrap  →  {rotary-encoder, pll-phase-detector, interferometer}

Each expansion path produces a DIFFERENT ∆ implementation. The cartesian
product of expansions × substrates = all valid ∆ for the £.

Includes the delta-sigma signature check: does any expansion of the ¢ DAG
contain the subgraph ¢_accum → ¢_wrap → ¢_eq? If yes, the £ is
delta-sigma-implementable (one of many valid ∆).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from itertools import product

from .grammar import CGraph, COp, decompose_formula
from .pattern_matcher import DELTA_SUBSTRATE, DeltaImplementation


# ---------------------------------------------------------------------------
# 1. Expansion rules for composite ¢ primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Expansion:
    """One way to expand a composite ¢ primitive into a subgraph + substrate."""
    primitive: str           # the ¢ primitive being expanded (e.g. "sqrt")
    name: str                # human-readable name (e.g. "analog-feedback")
    expands_to: Tuple[str, ...]  # the ¢ subgraph it becomes (e.g. ("mult", "eq"))
    substrate_domain: str    # domain (electrical, mechanical, digital, fluidic, thermal)
    substrate_component: str # the physical component
    carrier_type: str        # temporal, phase-wrap, spatial, static
    is_delta_sigma: bool     # does this expansion contain ¢_accum+¢_wrap+¢_eq?
    description: str


EXPANSIONS: List[Expansion] = [
    # ¢_sqrt expansions (4 ways)
    Expansion("sqrt", "analog-feedback",
              ("mult", "eq"),
              "electrical", "op-amp + analog multiplier in feedback loop",
              "temporal", False,
              "V_out driven until V_out² = V_in. Static equilibrium via op-amp's huge gain."),
    Expansion("sqrt", "mechanical-cam",
              ("spatial",),
              "mechanical", "square-root cam (shaped profile)",
              "spatial", False,
              "Cam profile encodes y = √x geometrically. Input displacement → output displacement."),
    Expansion("sqrt", "digital-delta-sigma",
              ("accum", "wrap", "eq"),
              "digital", "delta-sigma modulator + sqrt lookup in feedback",
              "temporal", True,
              "Oversampled ADC quantizes the input; sqrt lookup in feedback path; bitstream average → √x. THIS is delta-sigma."),
    Expansion("sqrt", "fluidic-orifice",
              ("mult", "eq"),
              "fluidic", "nonlinear orifice with pressure feedback",
              "temporal", False,
              "Pressure-flow relation through a shaped orifice; feedback via pressure differential."),

    # ¢_eq expansions (5 ways — including delta-sigma)
    Expansion("eq", "op-amp-feedback",
              ("eq",),
              "electrical", "op-amp with feedback network",
              "temporal", False,
              "Op-amp's huge gain drives V_− = V_+ (virtual short). The canonical equilibrium finder."),
    Expansion("eq", "mechanical-servo",
              ("eq",),
              "mechanical", "servo motor with position feedback",
              "temporal", False,
              "Motor drives until encoder reads setpoint; error → 0."),
    Expansion("eq", "hydraulic-servo",
              ("eq",),
              "fluidic", "hydraulic valve with pressure feedback",
              "temporal", False,
              "Valve opens until pressure matches setpoint."),
    Expansion("eq", "thermal-relaxation",
              ("eq",),
              "thermal", "radiative equilibrium (Stefan-Boltzmann)",
              "temporal", False,
              "Body radiates until T⁴ ∝ P. NOTE: gives 4th-root, not sqrt — only valid for £ = 4th-root."),
    Expansion("eq", "digital-delta-sigma-eq",
              ("accum", "wrap", "eq"),
              "digital", "delta-sigma modulator with equilibrium feedback",
              "temporal", True,
              "Oversampled loop seeks equilibrium via bitstream feedback. THIS is delta-sigma applied to equilibrium-finding."),

    # ¢_accum expansions (6 ways — including delta-sigma)
    Expansion("accum", "capacitor",
              ("accum",),
              "electrical", "capacitor (Q = ∫I dt)",
              "temporal", False,
              "The canonical temporal integrator. Carries ∫I as charge."),
    Expansion("accum", "inductor-flux",
              ("accum",),
              "electrical", "inductor flux linkage (λ = ∫V dt)",
              "temporal", False,
              "Flux linkage is integral of voltage. Dual of capacitor."),
    Expansion("accum", "mass",
              ("accum",),
              "mechanical", "mass (p = ∫F dt)",
              "temporal", False,
              "Momentum is integral of force."),
    Expansion("accum", "thermal-mass",
              ("accum",),
              "thermal", "thermal mass (Q = ∫P dt)",
              "temporal", False,
              "Heat is integral of power."),
    Expansion("accum", "flywheel",
              ("accum",),
              "rotational", "flywheel (L = ∫τ dt)",
              "temporal", False,
              "Angular momentum is integral of torque."),
    Expansion("accum", "digital-delta-sigma-integrator",
              ("accum", "wrap", "eq"),
              "digital", "delta-sigma modulator (bitstream sum → integral)",
              "temporal", True,
              "Oversampled ADC; bitstream's running SUM converges to ∫input dt. THIS is delta-sigma as integrator."),

    # ¢_wrap expansions (4 ways — including delta-sigma)
    Expansion("wrap", "rotary-encoder",
              ("wrap",),
              "rotational", "rotary encoder (θ mod 2π)",
              "phase-wrap", False,
              "Reads phase modulo one revolution."),
    Expansion("wrap", "pll-phase-detector",
              ("wrap",),
              "electrical", "PLL phase detector (Δφ mod 2π)",
              "phase-wrap", False,
              "Outputs phase error modulo 2π."),
    Expansion("wrap", "interferometer",
              ("wrap",),
              "optical", "interferometer fringe (Δφ mod π)",
              "phase-wrap", False,
              "Fringe pattern carries phase modulo π."),
    Expansion("wrap", "digital-delta-sigma-phase",
              ("accum", "wrap", "eq"),
              "digital", "delta-sigma phase tracker (bitstream → phase mod 2π)",
              "phase-wrap", True,
              "Delta-sigma with phase feedback; bitstream encodes phase wraps. THIS is delta-sigma for phase."),

    # ¢_div expansions (2 ways)
    Expansion("div", "analog-divider",
              ("mult", "eq"),
              "electrical", "op-amp + multiplier in feedback (a/b)",
              "temporal", False,
              "Multiplier in feedback computes a/b via equilibrium."),
    Expansion("div", "lever-ratio",
              ("scale",),
              "mechanical", "lever or gear train",
              "static", False,
              "Geometric division via ratio."),

    # ¢_recip expansions (2 ways)
    Expansion("recip", "analog-reciprocal",
              ("mult", "eq"),
              "electrical", "op-amp + multiplier in feedback (1/a)",
              "temporal", False,
              "Find y where y·a = 1 via feedback equilibrium."),

    # === v2.0: NEW SUBSTRATES (Computational Depth expansion) ===

    # ¢_exp expansions
    Expansion("exp", "translinear-bjt",
              ("exp",),
              "electrical", "BJT/diode (I = Is·exp(V/Vt))",
              "temporal", False,
              "Translinear principle: exponential I-V of semiconductor junction."),
    Expansion("exp", "enzyme-kinetic",
              ("exp",),
              "bio-chemical", "Arrhenius rate (k = A·exp(-Ea/RT))",
              "temporal", False,
              "Mass-action reaction rate with Arrhenius activation energy."),

    # ¢_log expansions
    Expansion("log", "translinear-log",
              ("log",),
              "electrical", "translinear log amplifier (V = Vt·ln(I/Is))",
              "temporal", False,
              "Log compression via semiconductor junction."),

    # ¢_sat expansions
    Expansion("sat", "op-amp-clipper",
              ("sat",),
              "electrical", "op-amp clipper with zener diodes",
              "temporal", False,
              "Hard/soft saturation via voltage clamping."),

    # ¢_hysteresis expansions
    Expansion("hysteresis", "magnetic-tunnel-junction",
              ("hysteresis",),
              "spintronics", "MTJ spin-transfer torque switching",
              "static", False,
              "Magnetic Tunnel Junction: spin-transfer torque state switching."),

    # ¢_grad expansions
    Expansion("grad", "thermal-conduction-bar",
              ("grad",),
              "thermal", "Fourier's law bar (q = -k·∇T)",
              "spatial", False,
              "Thermal conduction: heat flux proportional to temperature gradient."),

    # ¢_accum expansions (new substrates)
    Expansion("accum", "microfluidic-chamber",
              ("accum",),
              "fluidic", "microfluidic compliance chamber (V = ∫Q dt)",
              "temporal", False,
              "Flexible membrane storage: volume integrates flow rate."),
    Expansion("accum", "photonic-cavity",
              ("accum",),
              "optical", "photonic cavity (E = ∫P dt)",
              "temporal", False,
              "Photon storage/accumulation in optical resonator."),

    # ¢_wrap expansions (new substrate)
    Expansion("wrap", "mach-zehnder-interferometer",
              ("wrap",),
              "optical", "Mach-Zehnder (I = I0·cos²(Δφ/2 mod π))",
              "phase-wrap", False,
              "Optical interferometer: phase wrapping via path difference."),

    # ¢_rate expansions (new substrate)
    Expansion("rate", "piezoelectric-bimorph",
              ("rate",),
              "mechanical", "piezo bimorph (I = d33·dF/dt)",
              "temporal", False,
              "Piezoelectric charge rate proportional to force derivative."),

    # ¢_delay expansions
    Expansion("delay", "acoustic-waveguide",
              ("delay",),
              "fluidic", "acoustic delay line (y(t) = x(t - L/c))",
              "temporal", False,
              "Propagation delay in acoustic waveguide."),
    Expansion("delay", "optical-fiber",
              ("delay",),
              "optical", "optical fiber delay (y(t) = x(t - nL/c))",
              "temporal", False,
              "Propagation delay in optical fiber."),

    # ¢_translinear composite expansion
    Expansion("translinear", "translinear-cell",
              ("log", "mult", "exp"),
              "electrical", "translinear cell (y = a^b via log→mult→exp)",
              "temporal", False,
              "BJT translinear loop: computes arbitrary power via log-multiply-exp."),
]


def expansions_for(primitive: str) -> List[Expansion]:
    """All expansion ways for a composite ¢ primitive."""
    return [e for e in EXPANSIONS if e.primitive == primitive]


# ---------------------------------------------------------------------------
# 2. The ∆ enumerator
# ---------------------------------------------------------------------------

@dataclass
class DeltaImplementationSpec:
    """One complete ∆ implementation of a £."""
    substrate_domain: str       # electrical, mechanical, digital, fluidic, thermal, optical
    components: List[str]       # list of physical components used
    carrier_type: str           # temporal, phase-wrap, spatial, static
    is_delta_sigma: bool        # does this ∆ contain ¢_accum + ¢_wrap + ¢_eq?
    description: str            # human-readable description
    expansion_path: List[str]   # the expansion choices made (for traceability)


def enumerate_delta(cent_dag: CGraph) -> List[DeltaImplementationSpec]:
    """Enumerate ALL valid ∆ implementations for a ¢ DAG.

    For each ¢ primitive in the DAG (atomic OR composite), try:
      (a) every expansion (if any exist for this primitive)
      (b) every direct substrate (if any exist in DELTA_SUBSTRATE)

    The cartesian product across all ops = all valid ∆.
    """
    ATOMIC = {"sum", "neg", "mult", "scale", "accum", "rate", "wrap", "spatial",
              # v2.0 new atomics:
              "exp", "log", "sat", "hysteresis", "grad", "div_spatial", "curl", "delay"}
    COMPOSITE = {"sqrt", "eq", "recip", "div",
                 # v2.0 new composites:
                 "translinear", "state_space"}

    choices_per_op: List[List[Tuple]] = []

    for op in cent_dag.ops:
        op_choices: List[Tuple] = []

        # (a) Try every expansion (works for both atomic and composite primitives)
        for exp in expansions_for(op.op):
            op_choices.append((
                f"expand:{op.op}→{exp.name}",
                [exp.substrate_component],
                exp.carrier_type,
                exp.is_delta_sigma,
                f"{op.op} via {exp.name}: {exp.description}",
            ))

        # (b) Try every direct substrate (for atomic primitives)
        if op.op in ATOMIC:
            for sub in DELTA_SUBSTRATE:
                if sub.primitive == op.op:
                    op_choices.append((
                        f"substrate:{op.op}→{sub.component}",
                        [sub.component],
                        sub.carrier_type,
                        False,
                        f"{op.op} via {sub.component}: {sub.law}",
                    ))

        if not op_choices:
            op_choices.append(("unimplemented:" + op.op, [], "n/a", False,
                               f"no substrate available for ¢_{op.op}"))

        choices_per_op.append(op_choices)

    # Cartesian product across all ops
    results: List[DeltaImplementationSpec] = []
    for combo in product(*choices_per_op):
        components: List[str] = []
        carrier_types: Set[str] = set()
        is_ds = False
        descriptions: List[str] = []
        path: List[str] = []

        for op, choice in zip(cent_dag.ops, combo):
            _, comps, carrier, ds_flag, desc = choice
            components.extend(comps)
            if carrier != "n/a" and carrier != "unknown":
                carrier_types.add(carrier)
            if ds_flag:
                is_ds = True
            if desc:
                descriptions.append(desc)
            path.append(choice[0])

        if "phase-wrap" in carrier_types:
            overall_carrier = "phase-wrap"
        elif "spatial" in carrier_types:
            overall_carrier = "spatial"
        elif "static" in carrier_types:
            overall_carrier = "static"
        elif "temporal" in carrier_types:
            overall_carrier = "temporal"
        else:
            overall_carrier = "mixed"

        results.append(DeltaImplementationSpec(
            substrate_domain=_infer_domain(components),
            components=components,
            carrier_type=overall_carrier,
            is_delta_sigma=is_ds,
            description=" | ".join(descriptions),
            expansion_path=path,
        ))

    return results


def _infer_domain(components: List[str]) -> str:
    """Infer the dominant substrate domain from the components used."""
    text = " ".join(components).lower()
    if any(w in text for w in ["op-amp", "capacitor", "inductor", "resistor", "gilbert", "pll", "diode"]):
        return "electrical"
    if any(w in text for w in ["mass", "lever", "gear", "cam", "servo motor", "rack", "flywheel", "damper"]):
        return "mechanical"
    if any(w in text for w in ["orifice", "valve", "hydraulic", "pipe"]):
        return "fluidic"
    if any(w in text for w in ["thermal", "radiative", "stefan"]):
        return "thermal"
    if any(w in text for w in ["encoder", "rotor", "rotational"]):
        return "rotational"
    if any(w in text for w in ["interferometer", "optical"]):
        return "optical"
    if any(w in text for w in ["delta-sigma", "adc", "digital"]):
        return "digital"
    return "mixed"


# ---------------------------------------------------------------------------
# 3. Delta-sigma signature check
# ---------------------------------------------------------------------------

def is_delta_sigma_implementable(cent_dag: CGraph) -> bool:
    """Check if the ¢ DAG can be expanded to contain ¢_accum + ¢_wrap + ¢_eq.

    This is true iff at least one of the ∆ implementations returned by
    enumerate_delta has is_delta_sigma=True.
    """
    impls = enumerate_delta(cent_dag)
    return any(impl.is_delta_sigma for impl in impls)


def delta_sigma_implementations(cent_dag: CGraph) -> List[DeltaImplementationSpec]:
    """Return only the ∆ implementations that ARE delta-sigma."""
    impls = enumerate_delta(cent_dag)
    return [impl for impl in impls if impl.is_delta_sigma]


# ---------------------------------------------------------------------------
# 4. Test cases
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("∆ ENUMERATOR TEST — multiple ∆ per £")
    print("=" * 78)

    test_cases = [
        ("W5-03",  "velocity",          "(2 * energy / mass)^(1/2)"),
        ("W13",    "angular_frequency", "(spring_constant / mass)^(1/2)"),
        ("W14",    "angular_frequency", "(1 / (inductance * capacitance))^(1/2)"),
        ("W19",    "speed_of_light",    "(1 / (permittivity * permeability))^(1/2)"),
        ("W11-01", "length",            "velocity * time"),
        ("W3-02",  "energy",            "1/2 * charge * voltage"),
        ("W1-01",  "resistance",        "voltage / current"),
    ]

    for wheel, target, formula in test_cases:
        print(f"\n{'='*78}")
        print(f"£ = {wheel}: {target} = {formula}")
        print(f"{'='*78}")

        try:
            dag = decompose_formula(formula, target)
        except Exception as e:
            print(f"  (decomposition failed: {e})")
            continue

        print(f"\n¢ DAG:")
        for op in dag.ops:
            print(f"  {op.op}({op.inputs}) → {op.output}")

        impls = enumerate_delta(dag)
        print(f"\n{len(impls)} valid ∆ implementations:")
        print(f"{'#':<4}{'domain':<14}{'carrier':<12}{'∆Σ?':<6}components")
        print("-" * 90)
        for i, impl in enumerate(impls):
            comps = ", ".join(impl.components)
            if len(comps) > 50: comps = comps[:47] + "..."
            ds_flag = "YES" if impl.is_delta_sigma else "no"
            print(f"{i+1:<4}{impl.substrate_domain:<14}{impl.carrier_type:<12}{ds_flag:<6}{comps}")

        ds_impls = delta_sigma_implementations(dag)
        print(f"\nDelta-sigma implementable: {'YES' if ds_impls else 'NO'}")
        if ds_impls:
            for impl in ds_impls:
                print(f"  → {impl.substrate_domain}: {impl.components}")
                print(f"    {impl.description}")


if __name__ == "__main__":
    main()
