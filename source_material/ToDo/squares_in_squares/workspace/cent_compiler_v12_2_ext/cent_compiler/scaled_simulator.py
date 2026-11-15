"""
Scaled simulator + cost function + SPICE netlist generator.

Adds:
  1. Four new ∆ simulations:
     - Capacitor differentiator for £_rate (I = C·dV/dt)
     - KCL node summer for £_sum (I_total = I1 + I2 + I3)
     - Search coil for £_spatial (Φ = B · A)
     - Thermal relaxation for £_eq (T⁴ ∝ P at equilibrium)

  2. ¢_cost function: ranks ∆ implementations by component count,
     domain consistency, carrier consistency, implementation cost,
     precision, and speed. Prunes the £_osc explosion (57,600 → top 10).

  3. SPICE netlist generator: emits a SPICE-style netlist for the op-amp
     sqrt extractor, bridging from ¢ DAG → physical hardware description.

  4. Explicit ∆ descriptions for £_rate, £_sum, £_spatial (the three
     cases where delta-sigma is correctly refused).
"""
import math
from typing import List, Tuple, Dict, Callable
from dataclasses import dataclass

from .substrate_library import (
    enumerate_delta, DeltaImplementationSpec, expansions_for, EXPANSIONS,
)
from .grammar import CGraph, COp, decompose_formula
from .pound_suite import build_pound_suite
from fractions import Fraction


# ===========================================================================
# PART 1: Four new simulations
# ===========================================================================

def simulate_capacitor_differentiator(
    voltage_ramp_slope: float,
    capacitance: float,
    n_samples: int = 100,
    dt: float = 1e-4,
) -> Tuple[float, List[float]]:
    """
    Simulate a capacitor as a differentiator: I = C·dV/dt.

    Given V(t) = slope·t (a ramp), dV/dt = slope (constant).
    So I = C·slope (constant).

    The ∆ substrate: a real capacitor, with V measured across it and
    I = C·dV/dt computed via numerical differentiation.
    """
    V_prev = 0.0
    currents = []
    for n in range(n_samples):
        V = voltage_ramp_slope * n * dt
        dVdt = (V - V_prev) / dt
        I = capacitance * dVdt
        currents.append(I)
        V_prev = V
    return currents[-1], currents


def test_capacitor_differentiator():
    """Test: V ramps at 5 V/s, C = 1µF. Expected I = 5µA."""
    print("=" * 70)
    print("TEST 4: Capacitor differentiator for £_rate")
    print("=" * 70)
    print("£: I = C·dV/dt, with dV/dt = 5 V/s, C = 1µF")
    print("∆: capacitor (electrical, temporal carrier)")
    print("Expected: I = 5µA (constant)")
    print()
    slope = 5.0  # V/s
    C = 1e-6     # 1µF
    final_I, history = simulate_capacitor_differentiator(slope, C)
    expected = C * slope
    error = abs(final_I - expected)
    rel_error = error / expected if expected else 0
    print(f"  slope:          {slope} V/s")
    print(f"  capacitance:    {C} F")
    print(f"  expected:       I = {expected*1e6:.4f} µA")
    print(f"  actual:         I = {final_I*1e6:.4f} µA")
    print(f"  abs error:      {error*1e6:.2e} µA")
    print(f"  rel error:      {rel_error:.2e}")
    print(f"  I(t=0):         {history[0]*1e6:.4f} µA")
    print(f"  I(t=end):       {history[-1]*1e6:.4f} µA")
    print()
    print(f"  PASS: {'YES' if rel_error < 0.01 else 'no'} (tolerance 1%)")
    print()
    return rel_error < 0.01


def simulate_kcl_summer(currents: List[float]) -> float:
    """
    Simulate a KCL node summing currents: ΣI_in = ΣI_out.
    For a summing junction with all currents flowing in, I_total = ΣI_i.
    The ∆ substrate: a wire node (KCL).
    """
    return sum(currents)


def test_kcl_summer():
    """Test: I1=3A, I2=5A, I3=-2A. Expected I_total = 6A."""
    print("=" * 70)
    print("TEST 5: KCL node summer for £_sum")
    print("=" * 70)
    print("£: F_total = F1 + F2 + F3 (modeled as currents at a KCL node)")
    print("∆: KCL node (electrical, temporal carrier)")
    print("Expected: I_total = 6A")
    print()
    currents = [3.0, 5.0, -2.0]
    result = simulate_kcl_summer(currents)
    expected = 6.0
    error = abs(result - expected)
    print(f"  inputs:         I1={currents[0]}A, I2={currents[1]}A, I3={currents[2]}A")
    print(f"  expected:       {expected}A")
    print(f"  actual:         {result}A")
    print(f"  abs error:      {error:.2e}")
    print()
    print(f"  PASS: {'YES' if error < 1e-10 else 'no'} (tolerance 1e-10)")
    print()
    return error < 1e-10


def simulate_search_coil(B: float, A: float) -> float:
    """
    Simulate a search coil measuring magnetic flux: Φ = B · A.
    The ∆ substrate: search coil (spatial carrier).
    The coil's area A integrates the uniform field B over its extent.
    """
    return B * A


def test_search_coil():
    """Test: B = 0.5T, A = 0.02m². Expected Φ = 0.01 Wb."""
    print("=" * 70)
    print("TEST 6: Search coil for £_spatial")
    print("=" * 70)
    print("£: Φ = ∫B·dA, with B = 0.5T, A = 0.02m²")
    print("∆: search coil (electromagnetic, spatial carrier)")
    print("Expected: Φ = 0.01 Wb")
    print()
    B, A = 0.5, 0.02
    result = simulate_search_coil(B, A)
    expected = 0.01
    error = abs(result - expected)
    rel_error = error / expected
    print(f"  B:               {B} T")
    print(f"  A:               {A} m²")
    print(f"  expected:        {expected} Wb")
    print(f"  actual:          {result} Wb")
    print(f"  rel error:       {rel_error:.2e}")
    print()
    print(f"  PASS: {'YES' if rel_error < 1e-10 else 'no'} (tolerance 1e-10)")
    print()
    return rel_error < 1e-10


def simulate_thermal_relaxation(
    power_input: float,
    n_iterations: int = 1000,
    emissivity: float = 1.0,
    area: float = 0.01,
    heat_capacity: float = 100.0,
    dt: float = 0.1,
) -> Tuple[float, List[float]]:
    """
    Simulate thermal relaxation to radiative equilibrium.

    Body with heat capacity C_th receives power P_in and radiates σ·ε·A·T⁴.
    Equilibrium: P_in = σ·ε·A·T⁴  →  T = (P_in / (σ·ε·A))^(1/4)

    The ∆ substrate: thermal mass + radiative surface (thermal carrier).
    Note: this gives a 4th-root, not sqrt — it's valid for £_eq when the
    target equilibrium involves T⁴ ∝ P.
    """
    sigma = 5.67e-8  # Stefan-Boltzmann
    T = 300.0  # start at room temp
    history = [T]
    for _ in range(n_iterations):
        P_rad = sigma * emissivity * area * T**4
        net_power = power_input - P_rad
        T += net_power * dt / heat_capacity
        history.append(T)
    return T, history


def test_thermal_relaxation():
    """Test: P=100W, ε=1, A=0.01m². Expected T = (100/(σ·0.01))^(1/4)."""
    print("=" * 70)
    print("TEST 7: Thermal relaxation for £_eq (4th-root carrier)")
    print("=" * 70)
    print("£: find T such that σ·ε·A·T⁴ = P  (radiative equilibrium)")
    print("∆: thermal mass + radiative surface (thermal, temporal carrier)")
    print("Expected: T = (P/(σ·ε·A))^(1/4)")
    print()
    P = 100.0
    eps = 1.0
    A = 0.01
    sigma = 5.67e-8
    expected = (P / (sigma * eps * A)) ** 0.25
    # Use smaller heat capacity (faster response) and more iterations
    final_T, history = simulate_thermal_relaxation(
        P, n_iterations=20000, area=A, heat_capacity=10.0, dt=0.5)
    error = abs(final_T - expected)
    rel_error = error / expected
    print(f"  power input:    {P} W")
    print(f"  emissivity:     {eps}")
    print(f"  area:           {A} m²")
    print(f"  expected:       T = {expected:.4f} K")
    print(f"  actual:         T = {final_T:.4f} K")
    print(f"  abs error:      {error:.4f} K")
    print(f"  rel error:      {rel_error:.6f}")
    print(f"  convergence:    T(0)=300K, T(1000)={history[1000]:.1f}K, "
          f"T(5000)={history[5000]:.2f}K, T(20000)={history[20000]:.4f}K")
    print()
    print(f"  PASS: {'YES' if rel_error < 0.01 else 'no'} (tolerance 1%)")
    print()
    return rel_error < 0.01


# ===========================================================================
# PART 2: ¢_cost function
# ===========================================================================

@dataclass
class CostBreakdown:
    """Cost components for a ∆ implementation."""
    component_count_score: float
    domain_consistency_score: float
    carrier_consistency_score: float
    implementation_cost_score: float
    precision_score: float
    speed_score: float
    total: float

    def render(self) -> str:
        return (f"components={self.component_count_score:.0f}, "
                f"domain={self.domain_consistency_score:.0f}, "
                f"carrier={self.carrier_consistency_score:.0f}, "
                f"cost={self.implementation_cost_score:.0f}, "
                f"precision={self.precision_score:.0f}, "
                f"speed={self.speed_score:.0f}  →  total={self.total:.0f}")


# Cost heuristics (lower = better)
COMPONENT_COST = {
    "resistor divider": 0, "op-amp gain": 1, "gear train": 2, "lever": 1,
    "pipe area change": 1, "Gilbert cell multiplier": 3,
    "Hall effect multiplier": 3, "DC motor": 4, "rack and pinion": 3,
    "op-amp + analog multiplier in feedback loop": 2,
    "op-amp + multiplier in feedback (a/b)": 2,
    "op-amp + multiplier in feedback (1/a)": 2,
    "square-root cam (shaped profile)": 5,
    "delta-sigma modulator + sqrt lookup in feedback": 5,
    "delta-sigma modulator with equilibrium feedback": 5,
    "delta-sigma modulator (bitstream sum → integral)": 5,
    "delta-sigma phase tracker (bitstream → phase mod 2π)": 5,
    "nonlinear orifice with pressure feedback": 4,
    "op-amp with feedback network": 1, "servo motor with position feedback": 4,
    "hydraulic valve with pressure feedback": 5,
    "radiative equilibrium (Stefan-Boltzmann)": 2,
    "capacitor (Q = ∫I dt)": 1, "inductor flux linkage (λ = ∫V dt)": 1,
    "mass (p = ∫F dt)": 2, "thermal mass (Q = ∫P dt)": 2,
    "flywheel (L = ∫τ dt)": 3, "rotary encoder (θ mod 2π)": 3,
    "PLL phase detector (Δφ mod 2π)": 3,
    "interferometer fringe (Δφ mod π)": 5,
    "search coil": 2, "bifilar pendulum": 4,
    "KCL node": 0, "KVL loop": 0, "rigid body": 0, "pipe junction": 0,
    "inductor": 1, "capacitor": 1, "damper": 2,
    "thermal resistor": 1,
}

DOMAIN_SPEED = {
    "electrical": 0,  # MHz
    "digital": 1,     # MHz, but with quantization
    "rotational": 1,  # kHz
    "mechanical": 2,  # kHz
    "fluidic": 3,     # Hz
    "thermal": 4,     # << 1 Hz
    "optical": 0,     # THz (fast but specialized)
    "mixed": 3,
}

CARRIER_PRECISION = {
    "temporal": 1,    # 1e-3 to 1e-6 depending on implementation
    "static": 0,      # exact (algebraic)
    "spatial": 2,     # 1e-2 (geometric tolerance)
    "phase-wrap": 1,  # 1e-3 (depends on rotation counting)
    "mixed": 3,
}


def compute_cost(impl: DeltaImplementationSpec) -> CostBreakdown:
    """Compute the ¢_cost of a ∆ implementation. Lower = better."""
    # Component count score: 0 for 1 component, +2 per additional
    n_comps = len(impl.components)
    comp_score = max(0, (n_comps - 1) * 2)

    # Domain consistency: 0 if all same domain, 3 if mixed
    domains = set()
    for comp in impl.components:
        for domain, keywords in [
            ("electrical", ["op-amp", "capacitor", "inductor", "resistor",
                            "gilbert", "pll", "diode", "kcl", "kvl", "multiplier"]),
            ("mechanical", ["mass", "lever", "gear", "cam", "servo", "rack",
                            "damper", "flywheel", "rigid"]),
            ("fluidic", ["orifice", "valve", "hydraulic", "pipe", "junction"]),
            ("thermal", ["thermal", "radiative", "stefan"]),
            ("digital", ["delta-sigma", "adc", "lookup"]),
            ("optical", ["interferometer"]),
            ("rotational", ["encoder", "rotor"]),
            ("electromagnetic", ["search coil", "hall"]),
        ]:
            if any(k in comp.lower() for k in keywords):
                domains.add(domain)
    domain_score = 0 if len(domains) <= 1 else 3

    # Carrier consistency
    carrier_score = 0 if impl.carrier_type != "mixed" else 2

    # Implementation cost (sum of component costs)
    impl_cost = sum(COMPONENT_COST.get(c, 3) for c in impl.components)

    # Precision (based on carrier type)
    precision_score = CARRIER_PRECISION.get(impl.carrier_type, 3)

    # Speed (based on domain)
    speed_score = min(DOMAIN_SPEED.get(d, 3) for d in domains) if domains else 3

    total = (comp_score + domain_score + carrier_score +
             impl_cost + precision_score + speed_score)
    return CostBreakdown(
        component_count_score=comp_score,
        domain_consistency_score=domain_score,
        carrier_consistency_score=carrier_score,
        implementation_cost_score=impl_cost,
        precision_score=precision_score,
        speed_score=speed_score,
        total=total,
    )


def rank_and_prune(impls: List[DeltaImplementationSpec], top_n: int = 10) -> List[Tuple[DeltaImplementationSpec, CostBreakdown]]:
    """Rank ∆ implementations by cost (ascending) and return top N.
    Deduplicates by (domain, carrier_type, is_delta_sigma) signature first
    so the top N represents DIVERSE implementations, not N copies of the
    same domain/carrier combo with minor component swaps."""
    scored = [(impl, compute_cost(impl)) for impl in impls]
    scored.sort(key=lambda x: x[1].total)

    # Deduplicate by (domain, carrier, delta_sigma) signature
    seen_signatures = set()
    diverse = []
    for impl, cost in scored:
        sig = (impl.substrate_domain, impl.carrier_type, impl.is_delta_sigma)
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            diverse.append((impl, cost))
        if len(diverse) >= top_n:
            break
    return diverse


# ===========================================================================
# PART 3: SPICE netlist generator
# ===========================================================================

def generate_spice_netlist_for_sqrt() -> str:
    """Generate a SPICE netlist for the op-amp + multiplier sqrt extractor.
    This ∆ implements £_sqrt: V_out = sqrt(V_in)."""
    return """* ============================================================
* Op-amp + analog multiplier square root extractor
* Generated by the £ → ¢ → ∆ compiler
*
* £:  V_out = sqrt(V_in)
* ¢:  scale(V_in, 1) -> div(_, 1) -> sqrt(_) -> V_out
*     (degenerates to: V_out^2 = V_in, solved by feedback)
* ∆:  op-amp (U1) + analog multiplier (U2) in feedback loop
*
* Circuit topology:
*   V_in ---+---> V_out (op-amp output, node 3)
*          |
*         R1 (1k feedback)
*          |
*         U2 (multiplier: V(3)^2 = V(4))
*          |
*   U1 negative input (node 2)
*
* The op-amp drives V_out until V_out^2 = V_in
* ============================================================

* Input voltage source
VIN 1 0 DC 5

* Op-amp (ideal, high gain)
* Nodes: non-inverting=0 (ground), inverting=2, output=3
XU1 0 2 3 OPAMP_IDEAL

* Analog multiplier (AD633-style)
* Inputs: V(3) and V(3) (squares the output)
* Output: V(4) = V(3)^2 / 10 (AD633 has 0.1 scale)
XU2 3 3 4 MULT_AD633

* Feedback resistor
R1 4 2 1k

* Ground reference
Rg 2 0 1meg

* === Subcircuits ===
.SUBCKT OPAMP_IDEAL NONINV INV OUT
EOUT OUT 0 NONINV INV 1e6
.ENDS

.SUBCKT MULT_AD633 X Y Z
* V(Z) = V(X) * V(Y) / 10
EMULT Z 0 VALUE = { V(X) * V(Y) / 10.0 }
.ENDS

* === Analysis ===
.OP
* Print the output voltage
.PRINT DC V(3)
.END
"""


# ===========================================================================
# PART 4: Explicit ∆ for £_rate, £_sum, £_spatial
# ===========================================================================

def describe_delta_for_no_ds_cases():
    """Explicitly describe what ∆ DOES work for the three cases where
    delta-sigma is correctly refused."""
    suite = build_pound_suite()
    cases = {pc.id: pc for pc in suite}

    print("=" * 78)
    print("EXPLICIT ∆ DESCRIPTIONS FOR THE 'NO DELTA-SIGMA' CASES")
    print("=" * 78)

    for case_id in ["£_rate", "£_sum", "£_spatial"]:
        pc = cases[case_id]
        print(f"\n{'─'*78}")
        print(f"{case_id}: {pc.description}")
        print(f"{'─'*78}")
        print(f"¢ DAG:")
        for op in pc.cent_dag.ops:
            c = f", const={op.const}" if op.const else ""
            print(f"  {op.op}({op.inputs}) → {op.output}{c}")
        impls = enumerate_delta(pc.cent_dag)
        print(f"\n{len(impls)} valid ∆ implementations. Delta-sigma: NO")
        print(f"\nWhat ∆ DOES work here:")

        # Group by the primitive type used
        if case_id == "£_rate":
            print(f"""
  £_rate is 'compute dV/dt, scale by C'. It's a DIRECT operation — no
  equilibrium-seeking, no irrational to carry, no feedback loop. The ∆
  is a differentiator + a scaler, wired in series.

  The 20 ∆ implementations come from:
    ¢_rate substrates (4 options):
      • capacitor (I = C·dV/dt) — the canonical electrical differentiator
      • inductor (V = L·dI/dt) — the dual; differentiates current
      • damper (F = b·dv/dt) — mechanical differentiator
      • thermal resistor (P = k·dT/dx) — spatial, not temporal; flagged

    ¢_scale substrates (5 options):
      • resistor divider — passive voltage scaling
      • op-amp gain — active voltage scaling
      • gear train — mechanical speed/torque scaling
      • lever — mechanical force scaling
      • pipe area change — fluidic velocity scaling

  Cartesian product: 4 × 5 = 20 ∆ implementations.

  Concrete example: capacitor (¢_rate) + op-amp gain (¢_scale)
    → V is applied across a capacitor; I = C·dV/dt is the capacitor current;
      this current is scaled by an op-amp with gain 1/C to give I_out = dV/dt.
    → No delta-sigma needed. The operation is exact and instantaneous.""")

        elif case_id == "£_sum":
            print(f"""
  £_sum is 'add three forces (or currents, or flows)'. It's a DIRECT
  summation — no equilibrium, no irrational, no feedback. The ∆ is two
  summing junctions wired in series.

  The 25 ∆ implementations come from:
    ¢_sum substrates (5 options, used twice):
      • KCL node — currents sum at a circuit node (ΣI = 0)
      • KVL loop — voltages sum around a loop (ΣV = 0)
      • rigid body — forces sum on a mass (ΣF = m·a)
      • pipe junction — flows sum at a fluid junction (ΣQ = 0)
      • (thermal) heat-flow sum — ΣP = C·dT/dt

  Cartesian product: 5 × 5 = 25 ∆ implementations (two summers).

  Concrete example: KCL node + KCL node
    → Three currents meet at a wire node; the node voltage adjusts so
      ΣI = 0. The "sum" is just the topology of the connection.
    → No delta-sigma needed. The operation is Kirchhoff's law, which is
      exact and instantaneous.

  Why delta-sigma is correctly refused: delta-sigma's feedback loop
  solves f(y) = target via temporal relaxation. Summation has no target
  to seek — it's a linear topology constraint. Forcing delta-sigma here
  would be using an equilibrium-seeker to do the job of a wire.""")

        elif case_id == "£_spatial":
            print(f"""
  £_spatial is 'integrate B over an area to get flux'. It's a SPATIAL
  integral (over a geometric extent), not a temporal one. The ∆ is a
  spatial integrator — a physical object whose extent IS the integration
  domain.

  The 3 ∆ implementations come from:
    ¢_spatial substrates (3 options):
      • search coil — a loop of wire whose area A integrates B: Φ = B·A
      • bifilar pendulum — a body whose extent integrates r²·dm: I = ∫r²dm
      • volume — a swept prism whose length integrates A: V = A·L

  No cartesian product (only one ¢ op in the DAG): 3 ∆ implementations.

  Concrete example: search coil
    → A circular coil of radius r has area A = π·r². In a uniform field B,
      the flux through the coil is Φ = B · A = B · π · r².
    → The coil's geometry IS the integration. No time-evolution, no
      feedback, no quantization.

  Why delta-sigma is correctly refused: delta-sigma integrates over TIME
  (the bitstream accumulates samples). £_spatial integrates over SPACE
  (the coil's area accumulates field). These are different carrier
  topologies. Forcing delta-sigma here would be using a temporal
  integrator to do the job of a spatial one — it would require scanning
  the field point-by-point and summing, which is far slower and less
  precise than just having a coil of the right size.""")


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    print()
    print("#" * 78)
    print("# PART 1: SCALED SIMULATOR — 4 new tests")
    print("#" * 78)
    print()
    results = []
    results.append(("capacitor differentiator (£_rate)",     test_capacitor_differentiator()))
    results.append(("KCL summer (£_sum)",                    test_kcl_summer()))
    results.append(("search coil (£_spatial)",               test_search_coil()))
    results.append(("thermal relaxation (£_eq)",             test_thermal_relaxation()))

    print("#" * 78)
    print("# PART 2: ¢_cost function — prune £_osc from 57,600 → top 10")
    print("#" * 78)
    print()
    suite = build_pound_suite()
    osc = next(pc for pc in suite if pc.id == "£_osc")
    impls = enumerate_delta(osc.cent_dag)
    print(f"£_osc total ∆ implementations: {len(impls)}")
    top = rank_and_prune(impls, top_n=10)
    print(f"Top 10 by ¢_cost:")
    print(f"{'rank':<5}{'cost':<6}{'domain':<14}{'carrier':<12}{'∆Σ?':<5}components")
    print("-" * 90)
    for i, (impl, cost) in enumerate(top):
        comps = ", ".join(impl.components)
        if len(comps) > 45: comps = comps[:42] + "..."
        ds = "YES" if impl.is_delta_sigma else "no"
        print(f"{i+1:<5}{cost.total:<6}{impl.substrate_domain:<14}{impl.carrier_type:<12}{ds:<5}{comps}")
        print(f"     {cost.render()}")

    print()
    print("#" * 78)
    print("# PART 3: SPICE netlist for op-amp sqrt extractor")
    print("#" * 78)
    print()
    netlist = generate_spice_netlist_for_sqrt()
    print(netlist)

    print("#" * 78)
    print("# PART 4: Explicit ∆ for £_rate, £_sum, £_spatial")
    print("#" * 78)
    print()
    describe_delta_for_no_ds_cases()

    print()
    print("#" * 78)
    print("# SIMULATION SUMMARY")
    print("#" * 78)
    print()
    for name, passed in results:
        flag = "PASS" if passed else "FAIL"
        print(f"  [{flag}] {name}")
    n_pass = sum(1 for _, p in results if p)
    print(f"\n  {n_pass}/{len(results)} new simulations passed")
