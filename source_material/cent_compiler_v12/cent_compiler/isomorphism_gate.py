"""
The corrected ∆ classifier and three-tier isomorphism gate.

FIXES the structural bug identified in audit:
  - is_delta_sigma is NO LONGER a property of individual substrate rows.
  - It is a property of a COMPOSED LOOP: ¢_accum + ¢_wrap + ¢_eq in closed
    loop WITH explicit oversampling.

A capacitor is a CONSTITUENT of delta-sigma, not delta-sigma itself.

Three classifications:
  - delta_sigma       — closed loop with accum + wrap + eq + oversampling
  - equilibrium_seeking — has ¢_eq (feedback) but not the full ∆Σ loop
  - direct            — no feedback; pure feedforward computation

Three-tier isomorphism gate:
  TIER 1 — shape match only → CANDIDATE (never a solution)
  TIER 2 — axiom-verified + dim-consistent + residual empty → ADMISSIBLE
  TIER 3 — declared analogy + transducer equations → COMPILABLE
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from .substrate_library import DeltaImplementationSpec, expansions_for, EXPANSIONS


# ---------------------------------------------------------------------------
# 1. ∆ classification (composed-loop predicate)
# ---------------------------------------------------------------------------

@dataclass
class DeltaClassification:
    """How a ∆ implementation should be classified."""
    classification: str  # "delta_sigma", "equilibrium_seeking", or "direct"
    has_accum: bool
    has_wrap: bool
    has_eq: bool
    is_oversampled: bool
    reason: str


def classify_delta(impl: DeltaImplementationSpec) -> DeltaClassification:
    """Classify a ∆ implementation by its composed structure.

    Delta-sigma is NOT a property of a single substrate. It is a property
    of a closed loop containing ¢_accum + ¢_wrap + ¢_eq with oversampling.
    """
    # Look at the expansion path to see which ¢ primitives are present
    # The expansion_path is a list of strings like "expand:sqrt→digital-delta-sigma"
    # or "substrate:accum→capacitor"
    has_accum = False
    has_wrap = False
    has_eq = False
    is_oversampled = False

    for step in impl.expansion_path:
        step_lower = step.lower()
        # Check if this step provides a ∆Σ constituent
        if "accum" in step_lower or "capacitor" in step_lower or "inductor-flux" in step_lower or "mass" in step_lower or "thermal-mass" in step_lower or "flywheel" in step_lower:
            has_accum = True
        if "wrap" in step_lower or "encoder" in step_lower or "pll" in step_lower or "interferometer" in step_lower:
            has_wrap = True
        if "eq" in step_lower and ("feedback" in step_lower or "servo" in step_lower or "equilibrium" in step_lower or "delta-sigma" in step_lower):
            has_eq = True
        if "delta-sigma" in step_lower or "digital" in step_lower or "oversampl" in step_lower:
            is_oversampled = True

    # The classification:
    # delta_sigma: closed loop with accum + wrap + eq + oversampling
    # equilibrium_seeking: has eq (feedback) but not the full ∆Σ loop
    # direct: no feedback
    if has_accum and has_wrap and has_eq and is_oversampled:
        return DeltaClassification(
            "delta_sigma", has_accum, has_wrap, has_eq, is_oversampled,
            "Closed loop with ¢_accum + ¢_wrap + ¢_eq + oversampling. "
            "This IS a delta-sigma modulator."
        )
    elif has_eq:
        return DeltaClassification(
            "equilibrium_seeking", has_accum, has_wrap, has_eq, is_oversampled,
            "Has ¢_eq (feedback equilibrium) but not the full ∆Σ loop "
            "(missing accum/wrap/oversampling). This is equilibrium-seeking "
            "but NOT delta-sigma."
        )
    else:
        return DeltaClassification(
            "direct", has_accum, has_wrap, has_eq, is_oversampled,
            "No feedback loop. Direct feedforward computation."
        )


# ---------------------------------------------------------------------------
# 2. Three-tier isomorphism gate
# ---------------------------------------------------------------------------

@dataclass
class IsomorphismGate:
    """Three-tier classification of a cross-domain isomorphism."""
    tier: int           # 1, 2, or 3
    label: str          # "CANDIDATE", "ADMISSIBLE", or "COMPILABLE"
    shape_match: bool   # TIER 1: axiom shapes match under name bijection
    axiom_verified: bool    # TIER 2: each axiom maps to a real axiom
    dim_consistent: bool    # TIER 2: dimensional residual is empty
    residual_empty: bool    # TIER 2: no leftover dimensions
    declared_analogy: bool  # TIER 3: declared convention + transducer equations
    reason: str


def gate_isomorphism(
    shape_match: bool,
    axiom_verified: bool = False,
    dim_consistent: bool = False,
    residual: Optional[Dict] = None,
    declared_analogy: bool = False,
) -> IsomorphismGate:
    """Apply the three-tier gate to an isomorphism candidate.

    TIER 1 (CANDIDATE): shape match only. Never a solution.
      - The structural analyzer's "SHAPE COINCIDENCE" cases go here.
      - These are NEVER executable as cross-domain routes.

    TIER 2 (ADMISSIBLE): shape match + axiom-verified + dim-consistent + residual empty.
      - The analyzer's "USEFUL" cases (predictions are known laws) go here.
      - These can be used for axiom transfer but need explicit transducer
        equations to be compilable.

    TIER 3 (COMPILABLE): TIER 2 + declared analogy convention + transducer equations.
      - Paynter effort-flow analogy with declared impedance/mobility convention.
      - These can be compiled to SPICE netlists.
    """
    residual_empty = (residual is None or len(residual) == 0)

    if shape_match and axiom_verified and dim_consistent and residual_empty and declared_analogy:
        return IsomorphismGate(
            3, "COMPILABLE", True, True, True, True, True,
            "Shape match + axiom-verified + dim-consistent + residual empty + "
            "declared analogy with transducer equations. Can be compiled to "
            "a physical implementation."
        )
    elif shape_match and axiom_verified and dim_consistent and residual_empty:
        return IsomorphismGate(
            2, "ADMISSIBLE", True, True, True, True, False,
            "Shape match + axiom-verified + dim-consistent + residual empty. "
            "Can be used for axiom transfer but needs explicit transducer "
            "equations to be compilable."
        )
    elif shape_match:
        return IsomorphismGate(
            1, "CANDIDATE", True, axiom_verified, dim_consistent, residual_empty,
            declared_analogy,
            "Shape match only. This is a CANDIDATE, never a solution. "
            "Cannot be used for cross-domain transfer without TIER 2 "
            "verification (axiom-verified + dim-consistent + residual empty)."
        )
    else:
        return IsomorphismGate(
            0, "NONE", False, False, False, False, False,
            "No shape match. Not an isomorphism candidate."
        )


# ---------------------------------------------------------------------------
# 3. Known declared analogies (TIER 3 candidates)
# ---------------------------------------------------------------------------

@dataclass
class DeclaredAnalogy:
    """A formally declared cross-domain analogy with transducer equations."""
    name: str
    wheel_pair: Tuple[str, str]
    convention: str  # "impedance" or "mobility"
    mapping: Dict[str, str]
    transducer_equations: List[str]
    unit_scale_matrix: Dict[str, float]


DECLARED_ANALOGIES: List[DeclaredAnalogy] = [
    DeclaredAnalogy(
        name="Paynter effort-flow (impedance convention)",
        wheel_pair=("W1", "W7"),
        convention="impedance",
        mapping={
            "voltage": "acoustic_pressure",
            "current": "particle_velocity",
            "resistance": "acoustic_impedance",
            "power": "acoustic_intensity",
        },
        transducer_equations=[
            "V = k_V · P  (voltage proportional to pressure via piezoelectric constant)",
            "I = k_I · v  (current proportional to particle velocity via electromagnetic transducer)",
            "k_V · k_I = 1  (power conservation: V·I = P·v)",
        ],
        unit_scale_matrix={
            "k_V": 1e-3,  # V/Pa (example: 1mV per Pa)
            "k_I": 1e3,   # A/(m/s) (example: 1A per m/s)
        },
    ),
    DeclaredAnalogy(
        name="Rotational-linear (textbook)",
        wheel_pair=("W4", "W5"),
        convention="impedance",
        mapping={
            "moment_of_inertia": "mass",
            "angular_velocity": "velocity",
            "torque": "force",
            "angular_momentum": "momentum",
            "angular_acceleration": "acceleration",
            "power": "power",
            "energy": "energy",
        },
        transducer_equations=[
            "τ = r · F  (torque = radius × force, via a lever arm)",
            "ω = v / r  (angular velocity = linear velocity / radius)",
        ],
        unit_scale_matrix={
            "r": 1.0,  # 1 meter lever arm (example)
        },
    ),
    DeclaredAnalogy(
        name="Capacitor-inductor duality",
        wheel_pair=("W3", "W14"),
        convention="impedance",
        mapping={
            "capacitance": "inductance",
            "voltage": "current",
            "charge": "flux_linkage",
            "energy": "energy",
        },
        transducer_equations=[
            "Q = C·V ↔ λ = L·I  (charge-voltage ↔ flux-current)",
            "E = ½CV² ↔ E = ½LI²  (energy duality)",
        ],
        unit_scale_matrix={},
    ),
    # === v2.0: NEW TIER 3 TRANSDUCERS (Computational Depth expansion) ===
    DeclaredAnalogy(
        name="Electromechanical (Piezoelectric & Lorentz Force)",
        wheel_pair=("W1", "W5"),
        convention="mobility",
        mapping={
            "voltage": "force",
            "current": "velocity",
            "power": "power",
        },
        transducer_equations=[
            "F_motor = k_e · I  (Lorentz motor force constant)",
            "V_emf = k_e · v  (Back-EMF constant)",
            "q = d33 · F  (Piezoelectric charge constant)",
        ],
        unit_scale_matrix={
            "k_e": 1.0,       # N/A (motor constant)
            "d33": 300e-12,   # C/N (piezo coefficient)
        },
    ),
    DeclaredAnalogy(
        name="Thermoelectric (Seebeck & Peltier)",
        wheel_pair=("W1", "W8"),
        convention="impedance",
        mapping={
            "voltage": "temperature_difference",
            "current": "heat_flow_rate",
            "power": "power",
        },
        transducer_equations=[
            "V_seebeck = S · ΔT  (Seebeck coefficient)",
            "Q_peltier = Π · I = S · T_abs · I  (Peltier heat rate)",
        ],
        unit_scale_matrix={
            "S": 200e-6,  # V/K (Seebeck coefficient, e.g. Bi2Te3)
        },
    ),
    DeclaredAnalogy(
        name="Optoelectronic (Photodiode & Electro-Optic Modulator)",
        wheel_pair=("W1", "W19"),
        convention="impedance",
        mapping={
            "current": "optical_power",
            "voltage": "phase_shift",
        },
        transducer_equations=[
            "I_photo = R_lambda · P_opt  (Photodiode responsivity)",
            "Δφ = π · V / V_pi  (Electro-optic phase modulator)",
        ],
        unit_scale_matrix={
            "R_lambda": 0.85,  # A/W (photodiode responsivity at 1550nm)
            "V_pi": 3.5,       # V (EOM half-wave voltage)
        },
    ),
    DeclaredAnalogy(
        name="Electro-Hydrodynamic (Piezoresistive & Peristaltic Pump)",
        wheel_pair=("W1", "W6"),
        convention="impedance",
        mapping={
            "voltage": "pressure",
            "current": "volume_flow_rate",
        },
        transducer_equations=[
            "P_fluid = k_pump · I  (Active pump flow-pressure transducer)",
            "I_sense = k_piezo · P  (Piezoresistive pressure sense)",
        ],
        unit_scale_matrix={
            "k_pump": 1e6,    # Pa/A (pump constant)
            "k_piezo": 1e-6,  # A/Pa (sense constant)
        },
    ),
]


def find_declared_analogy(wheel_a: str, wheel_b: str) -> Optional[DeclaredAnalogy]:
    """Find a declared analogy between two wheels."""
    for analogy in DECLARED_ANALOGIES:
        a, b = analogy.wheel_pair
        if (a == wheel_a and b == wheel_b) or (a == wheel_b and b == wheel_a):
            return analogy
    return None
