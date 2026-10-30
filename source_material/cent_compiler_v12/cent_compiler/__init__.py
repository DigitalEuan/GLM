"""
cent_compiler — the £ → ¢ → ∆ physical compiler.

A cross-domain physical compiler that takes any abstract operation £,
decomposes it into atomic ¢ steps, enumerates all valid physical ∆
implementations across electrical/mechanical/fluidic/thermal/optical/digital
domains, ranks them by cost, and emits a SPICE netlist for the chosen ∆.

NOTATION (corrected per audit):
  £  — a target relation, always named (e.g. £: v = √(2E/m))
  ¢_x — the closed vocabulary of IR primitives (¢_accum, ¢_sqrt, etc.)
  ∆  — a realised implementation, keyed by (substrate, topology, carrier)
  Delta-Sigma — one named topology, NEVER used as a synonym for ∆

Delta-Sigma is NOT a property of a single substrate. It is a property of a
COMPOSED LOOP: ¢_accum + ¢_wrap + ¢_eq with oversampling. A capacitor is a
CONSTITUENT of delta-sigma, not delta-sigma itself.
"""
from .grammar import (
    CGraph, COp, decompose_formula, find_cent_isomorphism,
    ATOMIC_PRIMITIVES, COMPOSITE_PRIMITIVES, ALL_PRIMITIVES,
    preprocess_formula,
)
from .pattern_matcher import (
    pattern_signature, pattern_match, pattern_isomorphism_mapping,
    DELTA_SUBSTRATE, DeltaImplementation,
)
from .substrate_library import (
    enumerate_delta, DeltaImplementationSpec, Expansion, EXPANSIONS, expansions_for,
)
from .isomorphism_gate import (
    classify_delta, DeltaClassification,
    gate_isomorphism, IsomorphismGate,
    DeclaredAnalogy, DECLARED_ANALOGIES, find_declared_analogy,
)
from .cost_function import compute_cost, rank_and_prune, CostBreakdown
from .simulator import (
    simulate_delta_sigma_integrator, simulate_opamp_sqrt, simulate_pll,
)
from .scaled_simulator import (
    simulate_capacitor_differentiator, simulate_kcl_summer,
    simulate_search_coil, simulate_thermal_relaxation,
)
from .spice_emitter import generate_spice_netlist, write_spice_netlist
from .delta_sigma import DeltaSigmaEngine, flagship_demonstration
from .pound_suite import build_pound_suite, PoundCase
from .hypothesis_bridge import (
    CentWheel, CentEntry, KnowledgeState, Arrow,
    FidelityLayer, LAYERS, escalate,
    conjecture_loop, compile_with_knowledge,
    CentLedger, LedgerEntry,
)

__version__ = "2.0.0"
__all__ = [
    "CGraph", "COp", "decompose_formula", "find_cent_isomorphism",
    "ATOMIC_PRIMITIVES", "COMPOSITE_PRIMITIVES", "ALL_PRIMITIVES",
    "preprocess_formula",
    "pattern_signature", "pattern_match", "DELTA_SUBSTRATE",
    "enumerate_delta", "DeltaImplementationSpec", "Expansion", "EXPANSIONS",
    "classify_delta", "DeltaClassification",
    "gate_isomorphism", "IsomorphismGate",
    "DeclaredAnalogy", "DECLARED_ANALOGIES", "find_declared_analogy",
    "compute_cost", "rank_and_prune", "CostBreakdown",
    "simulate_delta_sigma_integrator", "simulate_opamp_sqrt", "simulate_pll",
    "simulate_capacitor_differentiator", "simulate_kcl_summer",
    "simulate_search_coil", "simulate_thermal_relaxation",
    "generate_spice_netlist", "write_spice_netlist", "DeltaSigmaEngine", "flagship_demonstration",
    "build_pound_suite", "PoundCase",
    "CentWheel", "CentEntry", "KnowledgeState", "Arrow",
    "FidelityLayer", "LAYERS", "escalate",
    "conjecture_loop", "compile_with_knowledge",
    "CentLedger", "LedgerEntry",
]
