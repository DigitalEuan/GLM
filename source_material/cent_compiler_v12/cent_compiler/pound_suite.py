"""
The fluid £ test suite.

Each £ is an abstract operation spanning the full ¢ primitive vocabulary,
not just the monomial operations that appear in wheel spokes. This makes
the £ side of ∆ = £ as fluid as the ∆ side.

Eight £ cases, one per ¢ primitive family:
  £_accum    — temporal integration       (¢_accum)
  £_rate     — temporal differentiation   (¢_rate)
  £_wrap     — phase wrapping mod 2π      (¢_wrap + ¢_accum)
  £_sum      — addition of multiple flows (¢_sum)
  £_eq       — equilibrium finding        (¢_mult + ¢_sum + ¢_eq)
  £_spatial  — spatial integration        (¢_spatial)
  £_sqrt     — square root extraction     (¢_scale + ¢_div + ¢_sqrt)
  £_osc      — second-order oscillator    (¢_rate + ¢_rate + ¢_sum + ¢_accum + ¢_accum)

For each £:
  - the ¢ DAG is built directly (not via the wheel-spoke decomposer)
  - enumerate_delta produces all valid ∆ implementations
  - selected ∆ are simulated to verify computational correctness
"""
from __future__ import annotations
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Tuple, Callable
from .grammar import CGraph, COp
from .substrate_library import enumerate_delta, is_delta_sigma_implementable

# Alias for clarity in op construction
C = Fraction


# ---------------------------------------------------------------------------
# 1. The £ test suite
# ---------------------------------------------------------------------------

@dataclass
class PoundCase:
    """One £ test case."""
    id: str
    description: str
    operation: str           # human-readable description of the £
    cent_dag: CGraph
    test_inputs: Dict[str, float]  # concrete values for verification
    expected_output: float
    verify_tolerance: float = 1e-3


def build_pound_suite() -> List[PoundCase]:
    """Build the 8 £ test cases."""

    # £_accum:  Q(t) = ∫I(t)dt   (capacitor charge from current)
    # ¢ DAG:  ¢_accum(I) → Q
    g_accum = CGraph(
        ops=[COp("accum", ("I",), "Q")],
        inputs={"I"}, outputs={"Q"}
    )

    # £_rate:  I(t) = C·dV/dt   (capacitor current from voltage rate)
    # ¢ DAG:  ¢_rate(V) → dVdt; ¢_scale(dVdt, C) → I
    g_rate = CGraph(
        ops=[COp("rate", ("V",), "dVdt"),
             COp("scale", ("dVdt",), "I", C(1e-6))],  # C = 1µF
        inputs={"V"}, outputs={"I"}
    )

    # £_wrap:  θ(t) = (∫ω dt) mod 2π   (oscillator phase from frequency)
    # ¢ DAG:  ¢_accum(ω) → θ_unbounded; ¢_wrap(θ_unbounded) → θ
    g_wrap = CGraph(
        ops=[COp("accum", ("omega",), "theta_unbounded"),
             COp("wrap", ("theta_unbounded",), "theta")],
        inputs={"omega"}, outputs={"theta"}
    )

    # £_sum:  F_total = F1 + F2 + F3   (force summation on rigid body)
    # ¢ DAG:  ¢_sum(F1, F2) → s1; ¢_sum(s1, F3) → F_total
    g_sum = CGraph(
        ops=[COp("sum", ("F1", "F2"), "s1"),
             COp("sum", ("s1", "F3"), "F_total")],
        inputs={"F1", "F2", "F3"}, outputs={"F_total"}
    )

    # £_eq:  find y such that y² = x   (square root via equilibrium)
    # ¢ DAG:  ¢_mult(y, y) → y_sq; ¢_sum(x, -y_sq) → error; ¢_eq(error) → y
    # (the eq op drives y until error = 0)
    g_eq = CGraph(
        ops=[COp("mult", ("y", "y"), "y_sq"),
             COp("sum", ("x", "y_sq"), "error"),  # using signed input convention
             COp("eq", ("error",), "y")],
        inputs={"x", "y"}, outputs={"y"}
    )

    # £_spatial:  Φ = ∫B·dA   (magnetic flux through a coil)
    # ¢ DAG:  ¢_spatial(B, A) → Φ
    g_spatial = CGraph(
        ops=[COp("spatial", ("B", "A"), "Phi")],
        inputs={"B", "A"}, outputs={"Phi"}
    )

    # £_sqrt:  v = √(2E/m)   (velocity from energy and mass — W5-03)
    # ¢ DAG:  ¢_scale(E, 2) → E2; ¢_div(E2, m) → ratio; ¢_sqrt(ratio) → v
    g_sqrt = CGraph(
        ops=[COp("scale", ("E",), "E2", C(2)),
             COp("div", ("E2", "m"), "ratio"),
             COp("sqrt", ("ratio",), "v")],
        inputs={"E", "m"}, outputs={"v"}
    )

    # £_osc:  solve  x'' + ω²·x = 0   (linear oscillator)
    # ¢ DAG (feedback loop):
    #   ¢_rate(x) → v                              (velocity from position)
    #   ¢_rate(v) → a_measured                     (acceleration from velocity)
    #   ¢_scale(x, ω²) → a_restoring               (restoring acceleration)
    #   ¢_sum(a_measured, a_restoring) → a_net     (NET = a_measured + ω²·x; when 0, satisfies ODE)
    #   ¢_accum(a_net) → v_new                     (integrate to get velocity)
    #   ¢_accum(v_new) → x_new                     (integrate to get position)
    # NOTE: this is a cyclic ¢ graph (feedback loop), which the wheels can't encode.
    g_osc = CGraph(
        ops=[COp("rate", ("x",), "v"),
             COp("rate", ("v",), "a_measured"),
             COp("scale", ("x",), "a_restoring", C(4)),  # ω² = 4 (ω = 2 rad/s)
             COp("sum", ("a_measured", "a_restoring"), "a_net"),
             COp("accum", ("a_net",), "v_new"),
             COp("accum", ("v_new",), "x_new")],
        inputs={"x", "v"}, outputs={"x_new", "v_new"}
    )

    # Rebuild with proper Fraction constants (C = Fraction alias defined above)
    g_rate = CGraph(
        ops=[COp("rate", ("V",), "dVdt"),
             COp("scale", ("dVdt",), "I", C(1, 1000000))],  # C = 1µF = 1e-6
        inputs={"V"}, outputs={"I"}
    )
    g_eq = CGraph(
        ops=[COp("mult", ("y", "y"), "y_sq"),
             COp("sum", ("x", "y_sq"), "error"),
             COp("eq", ("error",), "y")],
        inputs={"x", "y"}, outputs={"y"}
    )
    g_sqrt = CGraph(
        ops=[COp("scale", ("E",), "E2", C(2)),
             COp("div", ("E2", "m"), "ratio"),
             COp("sqrt", ("ratio",), "v")],
        inputs={"E", "m"}, outputs={"v"}
    )
    g_osc = CGraph(
        ops=[COp("rate", ("x",), "v"),
             COp("rate", ("v",), "a_measured"),
             COp("scale", ("x",), "a_restoring", C(4)),
             COp("sum", ("a_measured", "a_restoring"), "a_net"),
             COp("accum", ("a_net",), "v_new"),
             COp("accum", ("v_new",), "x_new")],
        inputs={"x", "v"}, outputs={"x_new", "v_new"}
    )

    return [
        PoundCase(
            id="£_accum",
            description="Temporal integration: Q(t) = ∫I(t)dt",
            operation="integrate a current waveform to get charge",
            cent_dag=g_accum,
            test_inputs={"I_avg": 0.7, "duration": 1000},  # I = 0.7A for 1000s
            expected_output=700.0,  # Q = 0.7 × 1000 = 700 C
        ),
        PoundCase(
            id="£_rate",
            description="Temporal differentiation: I = C·dV/dt",
            operation="differentiate a voltage ramp to get capacitor current",
            cent_dag=g_rate,
            test_inputs={"dV": 5.0, "dt": 1e-3, "C": 1e-6},  # 5V in 1ms, C=1µF
            expected_output=5e-3,  # I = C·dV/dt = 1e-6 × 5/1e-3 = 5e-3 A = 5mA
        ),
        PoundCase(
            id="£_wrap",
            description="Phase wrapping: θ = (∫ω dt) mod 2π",
            operation="integrate angular frequency and wrap mod 2π",
            cent_dag=g_wrap,
            test_inputs={"omega": 1.0, "duration": 7.5},  # ω=1 rad/s for 7.5s
            expected_output=7.5 % (2 * 3.141592653589793),  # ≈ 1.217 rad
        ),
        PoundCase(
            id="£_sum",
            description="Force summation: F_total = F1 + F2 + F3",
            operation="sum three forces on a rigid body",
            cent_dag=g_sum,
            test_inputs={"F1": 3.0, "F2": 5.0, "F3": -2.0},
            expected_output=6.0,
        ),
        PoundCase(
            id="£_eq",
            description="Equilibrium finding: find y such that y² = x",
            operation="extract square root via feedback equilibrium",
            cent_dag=g_eq,
            test_inputs={"x": 5.0},
            expected_output=2.2360679,  # √5
        ),
        PoundCase(
            id="£_spatial",
            description="Spatial integration: Φ = ∫B·dA",
            operation="integrate magnetic field over coil area to get flux",
            cent_dag=g_spatial,
            test_inputs={"B": 0.5, "A": 0.02},  # 0.5T over 0.02m²
            expected_output=0.01,  # Φ = 0.5 × 0.02 = 0.01 Wb
        ),
        PoundCase(
            id="£_sqrt",
            description="Square root extraction: v = √(2E/m)  (W5-03)",
            operation="extract velocity from energy and mass",
            cent_dag=g_sqrt,
            test_inputs={"E": 5.0, "m": 2.0},
            expected_output=(2 * 5 / 2) ** 0.5,  # √5 ≈ 2.236
        ),
        PoundCase(
            id="£_osc",
            description="Second-order oscillator: x'' + ω²x = 0  (ω=2)",
            operation="simulate one step of a harmonic oscillator",
            cent_dag=g_osc,
            test_inputs={"x": 1.0, "v": 0.0, "dt": 1e-4},  # start at x=1, v=0
            expected_output=1.0,  # after a tiny dt, x ≈ 1 (just started)
            verify_tolerance=1e-2,
        ),
    ]


# ---------------------------------------------------------------------------
# 2. Self-test: enumerate ∆ for each £
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from fractions import Fraction
    print("=" * 78)
    print("FLUID £ TEST SUITE — 8 cases spanning ALL ¢ primitives")
    print("=" * 78)

    suite = build_pound_suite()
    for pc in suite:
        print(f"\n{'='*78}")
        print(f"{pc.id}: {pc.description}")
        print(f"{'='*78}")
        print(f"¢ DAG:")
        for op in pc.cent_dag.ops:
            c = f", const={op.const}" if op.const else ""
            print(f"  {op.op}({op.inputs}) → {op.output}{c}")
        impls = enumerate_delta(pc.cent_dag)
        ds_impls = [i for i in impls if i.is_delta_sigma]
        print(f"\n{len(impls)} ∆ implementations ({len(ds_impls)} delta-sigma)")
        print(f"carrier types: {sorted({i.carrier_type for i in impls})}")
        print(f"domains: {sorted({i.substrate_domain for i in impls})}")
        print(f"delta-sigma implementable: {'YES' if ds_impls else 'no'}")
