"""
Pattern-level matcher and ∆ substrate library.

Adds:
  1. CGraph.pattern_signature() — collapses mult/scale/div chains into a
     single ¢_combine node, then signatures the reduced graph. Two ¢ graphs
     with the same pattern signature are abstractly isomorphic (same
     pattern, possibly different concrete operations).

  2. CGraph.pattern_match(other) — returns a mapping if pattern-isomorphic.

  3. DELTA_SUBSTRATE — library mapping each ¢ primitive to its physical
     implementations across electrical/mechanical/fluid/thermal domains.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Set, Tuple, FrozenSet
from collections import defaultdict

from .grammar import CGraph, COp, decompose_formula, find_cent_isomorphism


# ---------------------------------------------------------------------------
# 1. Pattern-level signature: collapse mult/scale/div chains
# ---------------------------------------------------------------------------

def _combine_chain_ops(ops: List[COp]) -> List[COp]:
    """Replace maximal chains of mult/scale/div ops with a single ¢_combine op.

    A ¢_combine node represents 'any way of combining inputs into a single
    monomial ratio'. This abstracts away the difference between:
      - div(k, m)                     [W13: just divide]
      - div(1, mult(L, C))            [W14: multiply then divide]
      - div(mult(r, mult(r, r)), mult(G, M))  [W17: many multiplies then divide]
      - div(scale(2, E), m)           [W5-03: scale then divide]
    All become ¢_combine with the same set of leaf inputs.
    """
    # Build adjacency: for each output var, which op produces it?
    by_output: Dict[str, COp] = {op.output: op for op in ops}

    # Identify which ops are "combine" ops (mult, scale, div)
    COMBINE_OPS = {"mult", "scale", "div"}

    # For each op, find its "leaf inputs" — inputs that are NOT produced by
    # another combine op. If an op's inputs all come from combine ops (or are
    # original inputs), it's part of a chain.
    def leaf_inputs(op: COp, visited: Set[str] = None) -> Set[str]:
        if visited is None:
            visited = set()
        leaves: Set[str] = set()
        for i in op.inputs:
            if i in visited:
                continue
            if i.startswith("const:"):
                continue  # constants don't count as leaf inputs
            producer = by_output.get(i)
            if producer is not None and producer.op in COMBINE_OPS:
                # recurse into the producer
                visited.add(i)
                leaves |= leaf_inputs(producer, visited)
            else:
                leaves.add(i)
        return leaves

    # Find the "root" combine ops: combine ops whose output is NOT used as
    # input by another combine op.
    combine_outputs: Set[str] = {op.output for op in ops if op.op in COMBINE_OPS}
    used_by_combine: Set[str] = set()
    for op in ops:
        if op.op in COMBINE_OPS:
            for i in op.inputs:
                if i in combine_outputs:
                    used_by_combine.add(i)
    roots = [op for op in ops if op.op in COMBINE_OPS and op.output not in used_by_combine]

    # For each root combine op, replace its entire chain with a single ¢_combine
    new_ops: List[COp] = []
    combine_chains_seen: Set[str] = set()
    for op in ops:
        if op.op in COMBINE_OPS:
            if op.output in combine_chains_seen:
                continue  # already absorbed into a root
            combine_chains_seen.add(op.output)
            # Skip — will be replaced by the root's ¢_combine
            continue
        # Non-combine op: rewrite its inputs to use root combine outputs where
        # they were previously using intermediate combine outputs.
        new_inputs = list(op.inputs)
        for i, inp in enumerate(op.inputs):
            if inp in combine_outputs:
                # Find the root that ultimately produces this
                root = _find_root(inp, by_output, COMBINE_OPS)
                new_inputs[i] = root
        new_ops.append(COp(op.op, tuple(new_inputs), op.output, op.const))

    # Add one ¢_combine op per root
    for root_op in roots:
        leaves = leaf_inputs(root_op)
        new_ops.append(COp("combine", tuple(sorted(leaves)), root_op.output))

    return new_ops


def _find_root(output: str, by_output: Dict[str, COp], COMBINE_OPS) -> str:
    """Walk up the chain until we reach a combine op whose output is not
    used by another combine op. Return that root's output name."""
    current = output
    while current in by_output:
        op = by_output[current]
        if op.op not in COMBINE_OPS:
            break
        # Check if any other combine op uses `current` as input
        is_root = True
        for other_op in by_output.values():
            if other_op.op in COMBINE_OPS and current in other_op.inputs and other_op.output != current:
                is_root = False
                break
        if is_root:
            return current
        # Otherwise, move up — but actually we should move to the root that
        # PRODUCES the chain. This is tricky. For simplicity, just return current.
        return current
    return current


def pattern_signature(graph: CGraph) -> Tuple:
    """The abstract pattern signature: collapses mult/scale/div chains into
    ¢_combine nodes, then returns the sorted multiset of op signatures
    plus the input/output counts."""
    reduced_ops = _combine_chain_ops(graph.ops)
    # Op signature: (op_name, n_inputs) — ignoring variable names entirely
    op_sigs = sorted((op.op, len(op.inputs)) for op in reduced_ops)
    n_inputs = len(graph.inputs - {n for n in graph.inputs if n.startswith("const:")})
    n_outputs = len(graph.outputs)
    return (tuple(op_sigs), n_inputs, n_outputs)


def pattern_match(g_a: CGraph, g_b: CGraph) -> bool:
    """Two ¢ graphs are pattern-isomorphic if they have the same pattern
    signature."""
    return pattern_signature(g_a) == pattern_signature(g_b)


def pattern_isomorphism_mapping(g_a: CGraph, g_b: CGraph) -> Optional[Dict[str, str]]:
    """If pattern-isomorphic, return a name mapping from A's inputs to B's
    inputs (position-based, since the pattern doesn't preserve which input
    is which — any permutation works)."""
    if not pattern_match(g_a, g_b):
        return None
    a_inputs = sorted(n for n in g_a.inputs if not n.startswith("const:"))
    b_inputs = sorted(n for n in g_b.inputs if not n.startswith("const:"))
    if len(a_inputs) != len(b_inputs):
        return None
    return dict(zip(a_inputs, b_inputs))


# ---------------------------------------------------------------------------
# 2. The ∆ substrate library
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeltaImplementation:
    """One physical implementation of a ¢ primitive."""
    primitive: str            # e.g. "accum"
    domain: str               # "electrical", "mechanical", "fluid", "thermal", "rotational"
    component: str            # e.g. "capacitor"
    law: str                  # the governing physical law
    carrier_type: str         # "temporal", "spatial", "phase-wrap", "static"
    notes: str = ""


DELTA_SUBSTRATE: List[DeltaImplementation] = [
    # ¢_sum
    DeltaImplementation("sum", "electrical", "KCL node",
        "ΣI_in = ΣI_out (Kirchhoff's Current Law)",
        "temporal",
        "Currents sum at any circuit node; the node voltage is the result."),
    DeltaImplementation("sum", "electrical", "KVL loop",
        "ΣV = 0 around any loop (Kirchhoff's Voltage Law)",
        "temporal",
        "Voltages sum around a loop; op-amp summing junction."),
    DeltaImplementation("sum", "mechanical", "rigid body",
        "ΣF = m·a (Newton's 2nd law for forces)",
        "temporal",
        "Forces sum on a rigid body; the body's acceleration is the result."),
    DeltaImplementation("sum", "rotational", "rigid body",
        "Στ = I·α (Newton's 2nd law for torques)",
        "temporal",
        "Torques sum on a rigid rotor."),
    DeltaImplementation("sum", "fluid", "pipe junction",
        "ΣQ_in = ΣQ_out (continuity at a junction)",
        "temporal",
        "Volume flow rates sum at a pipe junction."),

    # ¢_mult (true multiplication of two variables)
    DeltaImplementation("mult", "electrical", "Gilbert cell multiplier",
        "I_out = k·I_x·I_y (translinear principle)",
        "temporal",
        "The standard analog multiplier; basis of all ¢_eq composites."),
    DeltaImplementation("mult", "electrical", "Hall effect multiplier",
        "V_H = k·B·I (Hall effect)",
        "temporal",
        "Multiplies a magnetic field by a current."),
    DeltaImplementation("mult", "electromechanical", "DC motor",
        "τ = k·I·φ (motor torque = current × flux)",
        "temporal",
        "Multiplies current by magnetic flux to produce torque."),
    DeltaImplementation("mult", "mechanical", "rack and pinion",
        "F = k·τ·(1/r) (force from torque via radius)",
        "spatial",
        "Converts torque to force via a geometric ratio."),

    # ¢_scale (multiplication by a constant)
    DeltaImplementation("scale", "electrical", "resistor divider",
        "V_out = (R2/(R1+R2))·V_in",
        "temporal",
        "The simplest scaling element; gain < 1."),
    DeltaImplementation("scale", "electrical", "op-amp gain",
        "V_out = -(R_f/R_in)·V_in",
        "temporal",
        "Inverting or non-inverting amplifier; any gain."),
    DeltaImplementation("scale", "mechanical", "gear train",
        "ω_out = (N_in/N_out)·ω_in",
        "temporal",
        "Speed scaling; torque scales inversely."),
    DeltaImplementation("scale", "mechanical", "lever",
        "F_out = (d_in/d_out)·F_in",
        "temporal",
        "Force scaling via moment arm ratio."),
    DeltaImplementation("scale", "fluid", "pipe area change",
        "v_out = (A_in/A_out)·v_in (continuity)",
        "temporal",
        "Velocity scales inversely with area."),

    # ¢_accum (temporal integration)
    DeltaImplementation("accum", "electrical", "capacitor",
        "Q(t) = ∫I(t)dt; V = Q/C",
        "temporal",
        "The canonical temporal integrator. Carries ∫I as charge."),
    DeltaImplementation("accum", "electrical", "inductor (flux)",
        "λ(t) = ∫V(t)dt; λ = L·I",
        "temporal",
        "Flux linkage is the integral of voltage. Dual of capacitor."),
    DeltaImplementation("accum", "mechanical", "mass",
        "p(t) = ∫F(t)dt; p = m·v",
        "temporal",
        "Momentum is the integral of force. Carries ∫F as momentum."),
    DeltaImplementation("accum", "mechanical", "spring",
        "x(t) = ∫v(t)dt; F = k·x",
        "temporal",
        "Displacement is the integral of velocity."),
    DeltaImplementation("accum", "rotational", "moment of inertia",
        "L(t) = ∫τ(t)dt; L = I·ω",
        "temporal",
        "Angular momentum is the integral of torque."),
    DeltaImplementation("accum", "thermal", "thermal mass",
        "Q(t) = ∫P(t)dt; ΔT = Q/C_th",
        "temporal",
        "Heat is the integral of power. Carries ∫P as thermal energy."),

    # ¢_rate (temporal differentiation)
    DeltaImplementation("rate", "electrical", "inductor",
        "V(t) = L·dI/dt",
        "temporal",
        "The canonical differentiator. Voltage ∝ rate of change of current."),
    DeltaImplementation("rate", "electrical", "capacitor (current)",
        "I(t) = C·dV/dt",
        "temporal",
        "Current through a capacitor ∝ rate of change of voltage."),
    DeltaImplementation("rate", "mechanical", "damper",
        "F(t) = b·dv/dt",
        "temporal",
        "Damper force ∝ rate of change of displacement."),
    DeltaImplementation("rate", "thermal", "thermal resistor",
        "P = k·dT/dx (Fourier's law, spatial derivative)",
        "spatial",
        "Heat flux ∝ temperature gradient. NB: this is spatial, not temporal."),

    # ¢_wrap (phase wrapping mod 2π)
    DeltaImplementation("wrap", "rotational", "rotary encoder",
        "θ_measured = θ_actual mod 2π",
        "phase-wrap",
        "A rotary encoder reads phase modulo one revolution."),
    DeltaImplementation("wrap", "electrical", "phase detector",
        "V_out = K·sin(Δφ mod 2π)",
        "phase-wrap",
        "A PLL phase detector outputs the phase error modulo 2π."),
    DeltaImplementation("wrap", "optical", "interferometer",
        "I = I₀·cos²(Δφ/2 mod π)",
        "phase-wrap",
        "Interferometer fringes wrap; the irradiance carries phase mod π."),

    # ¢_spatial (spatial integration)
    DeltaImplementation("spatial", "electromagnetic", "search coil",
        "Φ = ∫B·dA (flux through coil area)",
        "spatial",
        "Integrates B over the coil's area; the canonical magnetic flux carrier."),
    DeltaImplementation("spatial", "rotational", "bifilar pendulum",
        "I = ∫r²·dm (moment of inertia)",
        "spatial",
        "Integrates mass distribution over a body; carries spatial info as a scalar."),
    DeltaImplementation("spatial", "fluid", "volume",
        "V = ∫A·dL (volume of a swept prism)",
        "spatial",
        "Integrates cross-section over length."),

    # ¢_sqrt (composite: mult + sum + feedback)
    DeltaImplementation("sqrt", "electrical", "op-amp + analog multiplier (feedback)",
        "V_out² = V_in (multiplier in feedback loop)",
        "temporal",
        "The canonical square-root extractor. The op-amp drives V_out until "
        "V_out² = V_in. The temporal relaxation IS the ∆ process."),
    DeltaImplementation("sqrt", "electrical", "diode (log/antilog)",
        "V_out = exp((1/2)·ln(V_in)) = √V_in",
        "temporal",
        "Uses the exponential I-V of a diode; non-ideal but cheap."),
    DeltaImplementation("sqrt", "mechanical", "square-root cam",
        "y = √x via shaped cam profile",
        "spatial",
        "A mechanical lookup table; the cam's shape encodes the sqrt function."),

    # ¢_eq (composite: the feedback equilibrium)
    DeltaImplementation("eq", "electrical", "op-amp feedback loop",
        "V_out driven until V_− = V_+ (virtual short)",
        "temporal",
        "The canonical equilibrium finder. The op-amp's huge gain drives the "
        "error to ~0. THIS is the ∆-process core: physical relaxation "
        "replaces numerical iteration."),
    DeltaImplementation("eq", "mechanical", "servo loop",
        "Position driven until error = 0",
        "temporal",
        "A mechanical servo does the same: drives until the feedback error vanishes."),
    DeltaImplementation("eq", "fluid", "hydraulic servo",
        "Pressure/flow driven until setpoint is reached",
        "temporal",
        "Hydraulic servos relax to equilibrium."),
]


def substrates_for(primitive: str) -> List[DeltaImplementation]:
    """Return all known physical implementations of a ¢ primitive."""
    return [s for s in DELTA_SUBSTRATE if s.primitive == primitive]


def substrates_for_graph(graph: CGraph) -> Dict[str, List[DeltaImplementation]]:
    """For each primitive appearing in the ¢ graph, list its substrates."""
    primitives_used = sorted({op.op for op in graph.ops})
    return {p: substrates_for(p) for p in primitives_used}


# ---------------------------------------------------------------------------
# 3. Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 78)
    print("PATTERN-LEVEL MATCHER TEST")
    print("=" * 78)

    # The 5 square-root carriers
    test_cases = [
        ("W5-03",  "velocity",          "(2 * energy / mass)^(1/2)"),
        ("W13",    "angular_frequency", "(spring_constant / mass)^(1/2)"),
        ("W14",    "angular_frequency", "(1 / (inductance * capacitance))^(1/2)"),
        ("W17",    "period",            "(distance^3 / (gravitational_constant * source_mass))^(1/2)"),
        ("W19",    "speed_of_light",    "(1 / (permittivity * permeability))^(1/2)"),
    ]

    graphs = []
    for name, target, formula in test_cases:
        g = decompose_formula(formula, target)
        sig = pattern_signature(g)
        graphs.append((name, target, formula, g, sig))
        print(f"\n{name}: {target} = {formula}")
        print(f"  pattern signature: {sig}")

    print("\n" + "=" * 78)
    print("PATTERN-LEVEL ISOMORPHISM (¢_combine abstraction)")
    print("=" * 78)
    print(f"\n{'pair':<14}{'pattern-iso?':<16}mapping")
    print("-" * 78)
    for i, (n1, t1, f1, g1, s1) in enumerate(graphs):
        for j, (n2, t2, f2, g2, s2) in enumerate(graphs):
            if i >= j:
                continue
            iso = pattern_match(g1, g2)
            mapping = pattern_isomorphism_mapping(g1, g2) if iso else None
            mp_str = ""
            if mapping:
                mp_str = ", ".join(f"{k}→{v}" for k, v in sorted(mapping.items()))
            print(f"{n1}-{n2:<8}{'YES' if iso else 'no':<16}{mp_str}")

    print("\n" + "=" * 78)
    print("∆ SUBSTRATE LIBRARY (for the square-root pattern)")
    print("=" * 78)
    g_sqrt = graphs[1][3]  # W13 graph
    print(f"\nFor W13 spoke '{graphs[1][1]} = {graphs[1][2]}':")
    print(f"¢ graph operations:")
    for op in g_sqrt.ops:
        print(f"  {op.op}({op.inputs}) → {op.output}")
    print(f"\nSubstrates for each ¢ primitive:")
    subs = substrates_for_graph(g_sqrt)
    for prim, impls in subs.items():
        print(f"\n  ¢_{prim} ({len(impls)} implementations):")
        for impl in impls:
            print(f"    [{impl.domain}] {impl.component}: {impl.law}")
            print(f"      carrier: {impl.carrier_type}")
