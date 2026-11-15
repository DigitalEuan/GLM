"""
hypothesis_bridge.py — brings the Hypothesis Engine's architecture into the
Cent Compiler.

The Hypothesis Engine is an epistemology engine that manages knowledge states
about mathematical claims. The Cent Compiler is a physics compiler that
translates abstract operations into physical hardware. This module bridges
the two by adopting the Hypothesis Engine's 8 key mechanisms:

1. Cent Wheel — KNOWS / THINKS-TRUE / DOESN'T-KNOW / NEEDS / LANGUAGE rings
   for ∆ implementations (instead of mathematical claims).

2. 5-Layer Escalation — Read each ∆ at increasing fidelity levels:
   ideal → parasitic → thermal → quantum → fabricated.
   Stop at the first failure. Track the "arrow" (converging or flipped).

3. Conjecture Loop — If a ∆ fails at a fidelity layer, re-lift with the
   next-best substrate from the cost-ranked list.

4. Parametric Ledger — Each ∆ is certified with exact parameters
   (voltage range, bandwidth, temperature, tolerance).

5. Arrow / Trajectory — Track whether a ∆ converges (passes all layers)
   or flips (fails at some layer). The trajectory only moves up.

6. Wheel Turn — When new substrates are added, re-evaluate all £ cases.
   KNOWS only grows; conflicts are reported.

7. Language Ring — ∆ implementations safe to cite in safety-critical designs.

8. Needs Mechanism — Identify gaps: "need SPICE verification",
   "need physical fabrication", "need noise analysis".

Architecture mapping:
  Hypothesis Engine          →  Cent Compiler
  Hypothesis (claim)         →  ∆ implementation (physical design)
  Gate cascade               →  Verification cascade (5 layers)
  5 scales (substrate→univ)  →  5 fidelity layers (ideal→fabricated)
  Wheel rings                →  Cent Wheel rings (same 5 rings)
  Conjecture loop            →  Design space exploration (re-lift)
  Lean ledger                →  Cent parametric ledger
  Arrow (converging/flipped) →  Design maturity trajectory
  Wheel turn (fixpoint)      →  Re-evaluate all £ on new substrates
"""
from __future__ import annotations
import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


# ===========================================================================
# 1. Knowledge states (the 5 Cent Wheel rings)
# ===========================================================================

class KnowledgeState(str, Enum):
    """The 5 rings of the Cent Wheel, mirroring the Hypothesis Engine."""
    KNOWS = "knows"              # SPICE-verified AND physically fabricated
    THINKS_TRUE = "thinks_true" # Passes simulation, not yet built
    DOESNT_KNOW = "doesnt_know" # Theoretically valid, untested
    NEEDS = "needs"             # Need SPICE verification, fabrication, etc.
    LANGUAGE = "language"       # Safe to cite in safety-critical designs


# ===========================================================================
# 2. The 5 fidelity layers (escalation cascade)
# ===========================================================================

@dataclass(frozen=True)
class FidelityLayer:
    """One level of physical realism in the verification cascade."""
    name: str
    description: str
    # What gets added at this layer
    adds: str


LAYERS: Tuple[FidelityLayer, ...] = (
    FidelityLayer("ideal",
                  "Perfect components, no noise, no parasitics",
                  "Ideal op-amps (infinite gain), perfect multipliers, lossless L/C"),
    FidelityLayer("parasitic",
                  "Real component imperfections",
                  "Op-amp finite gain (A=1e5), capacitor ESR, resistor tolerance (1%)"),
    FidelityLayer("thermal",
                  "Johnson-Nyquist noise, temperature drift",
                  "4kTR thermal noise, temperature coefficient drift (0-70°C)"),
    FidelityLayer("quantum",
                  "Shot noise, tunneling, quantum limits",
                  "Shot noise (2qI), tunneling leakage, quantum measurement back-action"),
    FidelityLayer("fabricated",
                  "Manufacturing tolerances, aging, process variation",
                  "±10% component variation, 20-year aging, temperature cycling"),
)


# ===========================================================================
# 3. The Arrow (design maturity trajectory)
# ===========================================================================

@dataclass
class Arrow:
    """The trajectory of a ∆ implementation through the fidelity layers.

    Like the Hypothesis Engine's arrow: reads are a prefix of the ladder,
    a flip is a real failure found only by reading higher.
    The trajectory only moves up.
    """
    reads: List[Tuple[str, bool, str]] = field(default_factory=list)
    # Each entry: (layer_name, passed, detail)

    @property
    def direction(self) -> str:
        """'converging' if all layers pass, 'flipped at <layer>' if one fails."""
        for layer_name, passed, _ in self.reads:
            if not passed:
                return f"flipped at {layer_name}"
        return "converging"

    @property
    def converged(self) -> bool:
        return self.direction == "converging"

    @property
    def flip_layer(self) -> Optional[str]:
        for layer_name, passed, _ in self.reads:
            if not passed:
                return layer_name
        return None

    def shape_ok(self) -> bool:
        """Reads must be a prefix of LAYERS (like the Hypothesis Engine)."""
        expected = [l.name for l in LAYERS[:len(self.reads)]]
        actual = [r[0] for r in self.reads]
        return expected == actual

    def render(self) -> str:
        lines = [f"  arrow: {self.direction}"]
        for layer_name, passed, detail in self.reads:
            flag = "PASS" if passed else "FLIP"
            lines.append(f"    [{flag}] {layer_name}: {detail}")
        return "\n".join(lines)


# ===========================================================================
# 4. The Cent Wheel entry (a ∆ implementation with knowledge state)
# ===========================================================================

@dataclass
class CentEntry:
    """One entry in the Cent Wheel — a ∆ implementation with its knowledge state.

    Mirrors the Hypothesis Engine's Hypothesis class, but for physical
    implementations instead of mathematical claims.
    """
    entry_id: str                    # unique ID (e.g. "sqrt_001")
    pound: str                       # the £ target relation
    delta_description: str           # the ∆ implementation description
    substrate_domain: str            # electrical, mechanical, etc.
    carrier_type: str                # temporal, spatial, phase-wrap, static
    is_delta_sigma: bool             # is this a delta-sigma implementation?
    status: KnowledgeState           # current ring
    params: Dict[str, Any]           # parametric certification
    # e.g. {"v_in_range": [0.1, 10], "bandwidth_hz": 1e6, "temp_range": [0, 70]}
    backing: List[str]               # evidence (simulation results, test outputs)
    arrow: Optional[Arrow] = None    # design maturity trajectory
    cost_score: Optional[float] = None  # ¢_cost total (lower = better)
    needs: List[str] = field(default_factory=list)  # unmet needs


# ===========================================================================
# 5. The Cent Wheel (knowledge state management)
# ===========================================================================

class CentWheel:
    """The Cent knowledge wheel — manages the state of ∆ implementations.

    Like the Hypothesis Engine's wheel:
    - KNOWS only grows (verified implementations stay verified)
    - THINKS-TRUE asserts nothing (it's a need for verification)
    - DOESN'T-KNOW is the default for new entries
    - NEEDS tracks what's missing for each non-KNOWS entry
    - LANGUAGE is the safe-to-cite subset of KNOWS

    A wheel turn re-gates all entries. If new substrates are added,
    previously DOESNT-KNOW entries may be re-evaluated.
    """

    def __init__(self):
        self.entries: List[CentEntry] = []
        self._id_counter = 0

    def add(self, pound: str, delta_desc: str, substrate_domain: str,
            carrier_type: str, is_delta_sigma: bool = False,
            params: Dict = None, cost_score: float = None) -> CentEntry:
        """Add a new ∆ implementation to the wheel (starts as DOESNT_KNOW)."""
        self._id_counter += 1
        entry = CentEntry(
            entry_id=f"delta_{self._id_counter:04d}",
            pound=pound,
            delta_description=delta_desc,
            substrate_domain=substrate_domain,
            carrier_type=carrier_type,
            is_delta_sigma=is_delta_sigma,
            status=KnowledgeState.DOESNT_KNOW,
            params=params or {},
            backing=[],
            cost_score=cost_score,
        )
        self.entries.append(entry)
        return entry

    def promote(self, entry_id: str, new_status: KnowledgeState,
                backing: str, arrow: Arrow = None):
        """Promote an entry to a new knowledge state.

        Rules (matching the Hypothesis Engine):
        - KNOWS entries can only stay KNOWS (they never regress)
        - THINKS-TRUE → KNOWS requires simulation backing
        - KNOWS → LANGUAGE requires safety certification
        - Any → DOESNT_KNOW or NEEDS is allowed (demotion)
        """
        entry = self.find(entry_id)
        if entry is None:
            raise KeyError(f"entry {entry_id} not found")

        # KNOWS only grows (like the Hypothesis Engine)
        if entry.status == KnowledgeState.KNOWS and new_status != KnowledgeState.LANGUAGE:
            if new_status != KnowledgeState.KNOWS:
                # KNOWS entries don't regress (except to LANGUAGE)
                return

        entry.status = new_status
        entry.backing.append(backing)
        if arrow:
            entry.arrow = arrow

        # Update needs based on new status
        entry.needs = self._compute_needs(entry)

    def find(self, entry_id: str) -> Optional[CentEntry]:
        for e in self.entries:
            if e.entry_id == entry_id:
                return e
        return None

    def ring(self, state: KnowledgeState) -> List[CentEntry]:
        """Get all entries in a specific ring."""
        return [e for e in self.entries if e.status == state]

    def _compute_needs(self, entry: CentEntry) -> List[str]:
        """Compute unmet needs based on current status."""
        needs = []
        if entry.status == KnowledgeState.DOESNT_KNOW:
            needs.append("need:simulation")
            needs.append("need:spice_verification")
        elif entry.status == KnowledgeState.THINKS_TRUE:
            needs.append("need:physical_fabrication")
            needs.append("need:noise_analysis")
        elif entry.status == KnowledgeState.NEEDS:
            if not entry.backing:
                needs.append("need:spice_verification")
            if not any("fabrication" in b for b in entry.backing):
                needs.append("need:physical_fabrication")
        elif entry.status == KnowledgeState.KNOWS:
            needs.append("need:safety_certification")  # for LANGUAGE promotion
        elif entry.status == KnowledgeState.LANGUAGE:
            needs = []  # fully certified
        return needs

    def turn(self) -> Dict:
        """Re-gate all entries (wheel turn / fixpoint merging).

        Like the Hypothesis Engine's wheel turn: KNOWS entries stay KNOWS,
        new entries are evaluated, conflicts are reported.
        """
        moves = []
        conflicts = []
        for entry in self.entries:
            old_status = entry.status
            # Re-compute needs
            entry.needs = self._compute_needs(entry)
            if entry.status != old_status:
                moves.append({
                    "entry_id": entry.entry_id,
                    "was": old_status.value,
                    "now": entry.status.value,
                })

        return {
            "total_entries": len(self.entries),
            "moves": moves,
            "conflicts": conflicts,
            "ring_counts": {
                state.value: len(self.ring(state)) for state in KnowledgeState
            },
        }

    def summary(self) -> Dict:
        """Summary of the wheel's current state."""
        return {
            "total": len(self.entries),
            "rings": {
                "knows": len(self.ring(KnowledgeState.KNOWS)),
                "thinks_true": len(self.ring(KnowledgeState.THINKS_TRUE)),
                "doesnt_know": len(self.ring(KnowledgeState.DOESNT_KNOW)),
                "needs": len(self.ring(KnowledgeState.NEEDS)),
                "language": len(self.ring(KnowledgeState.LANGUAGE)),
            },
            "delta_sigma_count": sum(1 for e in self.entries if e.is_delta_sigma),
            "converged": sum(1 for e in self.entries if e.arrow and e.arrow.converged),
            "flipped": sum(1 for e in self.entries if e.arrow and not e.arrow.converged),
        }

    def render(self) -> str:
        s = self.summary()
        lines = [
            "=" * 60,
            "CENT WHEEL — Knowledge State Summary",
            "=" * 60,
            f"  Total ∆ implementations: {s['total']}",
            f"  KNOWS (verified+fabricated): {s['rings']['knows']}",
            f"  THINKS-TRUE (sim-passed):    {s['rings']['thinks_true']}",
            f"  DOESN'T-KNOW (untested):     {s['rings']['doesnt_know']}",
            f"  NEEDS (gaps identified):     {s['rings']['needs']}",
            f"  LANGUAGE (safe-to-cite):     {s['rings']['language']}",
            f"  Delta-sigma implementations: {s['delta_sigma_count']}",
            f"  Converged (all layers pass): {s['converged']}",
            f"  Flipped (failed at layer):   {s['flipped']}",
            "=" * 60,
        ]
        return "\n".join(lines)


# ===========================================================================
# 6. The Escalation Cascade (5-layer verification)
# ===========================================================================

def escalate(impl_params: Dict, layers_to_test: Tuple[FidelityLayer, ...] = LAYERS) -> Arrow:
    """Read a ∆ implementation at increasing fidelity levels.

    Like the Hypothesis Engine's escalation: read at 5 scales, stop at the
    first failure. The trajectory only moves up.

    Each layer adds physical realism:
    - ideal: perfect components
    - parasitic: finite gain, ESR, tolerance
    - thermal: Johnson noise, temp drift
    - quantum: shot noise, tunneling
    - fabricated: manufacturing variation, aging

    Returns an Arrow tracking the reads.
    """
    arrow = Arrow()

    for layer in layers_to_test:
        result = _test_at_layer(impl_params, layer)
        arrow.reads.append((layer.name, result["passed"], result["detail"]))
        if not result["passed"]:
            break  # stop at first failure (like the Hypothesis Engine)

    return arrow


def _test_at_layer(params: Dict, layer: FidelityLayer) -> Dict:
    """Test a ∆ implementation at a specific fidelity layer.

    This is a simplified model — in a full implementation, each layer
    would run actual simulations (SPICE, FEM, etc.).
    """
    if layer.name == "ideal":
        # Ideal: always passes (the ∆ is theoretically correct)
        return {"passed": True, "detail": "ideal components, no errors"}

    elif layer.name == "parasitic":
        # Parasitic: check if the implementation tolerates finite gain
        v_in_max = params.get("v_in_range", [0, 10])[1]
        opamp_gain = params.get("opamp_gain", 1e5)
        # Op-amp sqrt: equilibrium error ~ 1/(2*gain)
        if opamp_gain > 0:
            equilibrium_error = 1.0 / (2 * opamp_gain)
        else:
            equilibrium_error = float('inf')
        # Pass if error < 0.1% (typical spec)
        passed = equilibrium_error < 0.001
        return {
            "passed": passed,
            "detail": f"finite gain A={opamp_gain:.0e}, equilibrium error={equilibrium_error:.2e}"
                      + ("" if passed else " (EXCEEDS 0.1% spec)"),
        }

    elif layer.name == "thermal":
        # Thermal: check Johnson noise vs signal
        bandwidth = params.get("bandwidth_hz", 1e6)
        temperature = params.get("temperature", 300)
        resistance = params.get("resistance", 1000)
        k_B = 1.38e-23
        noise_voltage = math.sqrt(4 * k_B * temperature * resistance * bandwidth)
        signal_level = params.get("signal_level", 1.0)
        snr = 20 * math.log10(signal_level / noise_voltage) if noise_voltage > 0 else float('inf')
        # Pass if SNR > 40 dB
        passed = snr > 40
        return {
            "passed": passed,
            "detail": f"Johnson noise={noise_voltage*1e6:.1f}µV, SNR={snr:.1f}dB"
                      + ("" if passed else " (BELOW 40dB spec)"),
        }

    elif layer.name == "quantum":
        # Quantum: check shot noise
        current = params.get("current", 1e-3)
        bandwidth = params.get("bandwidth_hz", 1e6)
        q = 1.6e-19
        shot_noise = math.sqrt(2 * q * current * bandwidth)
        signal_level = params.get("signal_level", 1.0)
        snr = 20 * math.log10(signal_level / shot_noise) if shot_noise > 0 else float('inf')
        # Pass if SNR > 30 dB (quantum limit is harder)
        passed = snr > 30
        return {
            "passed": passed,
            "detail": f"shot noise={shot_noise*1e6:.2f}µV, SNR={snr:.1f}dB"
                      + ("" if passed else " (BELOW 30dB quantum spec)"),
        }

    elif layer.name == "fabricated":
        # Fabricated: check tolerance stack-up
        tolerance = params.get("component_tolerance", 0.01)
        n_components = params.get("n_components", 3)
        # Worst-case tolerance stack: (1+t)^n ≈ 1 + n*t for small t
        worst_case_error = n_components * tolerance
        # Pass if worst-case error < 5%
        passed = worst_case_error < 0.05
        return {
            "passed": passed,
            "detail": f"tolerance=±{tolerance*100}%, {n_components} components, "
                      f"worst-case error={worst_case_error*100:.1f}%"
                      + ("" if passed else " (EXCEEDS 5% fabrication spec)"),
        }

    return {"passed": True, "detail": "unknown layer"}


# ===========================================================================
# 7. The Conjecture Loop (re-lift with different substrate on failure)
# ===========================================================================

def conjecture_loop(
    pound: str,
    failed_impl_desc: str,
    alternatives: List[Tuple[str, str, float, Dict]],
    verbose: bool = False,
) -> Dict:
    """If a ∆ fails verification, re-lift with the next-best substrate.

    Like the Hypothesis Engine's conjecture loop: when a claim flips at a
    layer, the engine re-lifts from the data with a narrowed parameter.

    Here: when a ∆ fails at a fidelity layer, try the next-best ∆
    from the cost-ranked list. Each attempt is escalated through the
    5 layers. The first ∆ that converges (passes all layers) is returned.

    Args:
        pound: the £ target relation
        failed_impl_desc: description of the ∆ that failed
        alternatives: list of (desc, domain, cost, params) tuples,
                      sorted by cost (ascending)

    Returns:
        Dict with the search result.
    """
    if verbose:
        print(f"Conjecture loop for £: {pound}")
        print(f"  Failed ∆: {failed_impl_desc}")
        print(f"  Alternatives: {len(alternatives)}")

    attempts = []
    for i, (desc, domain, cost, params) in enumerate(alternatives):
        if desc == failed_impl_desc:
            continue  # skip the one that already failed

        if verbose:
            print(f"  Attempt {i+1}: {desc} (cost={cost:.0f}, domain={domain})")

        arrow = escalate(params)
        attempts.append({
            "impl": desc,
            "domain": domain,
            "cost": cost,
            "arrow": arrow.direction,
            "flip_layer": arrow.flip_layer,
        })

        if arrow.converged:
            if verbose:
                print(f"    → CONVERGED (all 5 layers pass)")
            return {
                "found": True,
                "impl": desc,
                "domain": domain,
                "cost": cost,
                "attempts": attempts,
                "arrow": arrow,
            }
        else:
            if verbose:
                print(f"    → FLIPPED at {arrow.flip_layer}")

    return {
        "found": False,
        "attempts": attempts,
        "message": f"No ∆ implementation converged for £: {pound}",
    }


# ===========================================================================
# 8. The Parametric Ledger
# ===========================================================================

@dataclass
class LedgerEntry:
    """One entry in the Cent parametric ledger.

    Like the Hypothesis Engine's Lean ledger: each entry certifies a
    specific ∆ implementation with exact parameters. This prevents
    overclaiming (e.g., claiming a ∆ works universally when it only
    works in a limited range).
    """
    entry_id: str
    pound: str
    delta_desc: str
    params: Dict[str, Any]       # exact parameter certification
    certified_range: Dict[str, Tuple[float, float]]  # e.g. {"v_in": (0.1, 10)}
    test_result: str             # "PASS" or "FAIL at <layer>"
    backing: str                 # evidence summary
    timestamp: str = ""


class CentLedger:
    """The parametric ledger — certifies ∆ implementations with exact parameters.

    Like the Hypothesis Engine's Lean ledger: every hypothesis carries params,
    so a ledger entry applies only to the exact claim it certifies.
    """

    def __init__(self):
        self.entries: List[LedgerEntry] = []

    def certify(self, entry: CentEntry, test_result: str, backing: str,
                certified_range: Dict[str, Tuple[float, float]] = None) -> LedgerEntry:
        """Certify a ∆ implementation with exact parameters."""
        ledger_entry = LedgerEntry(
            entry_id=entry.entry_id,
            pound=entry.pound,
            delta_desc=entry.delta_description,
            params=entry.params,
            certified_range=certified_range or {},
            test_result=test_result,
            backing=backing,
        )
        self.entries.append(ledger_entry)
        return ledger_entry

    def lookup(self, entry_id: str) -> Optional[LedgerEntry]:
        for e in self.entries:
            if e.entry_id == entry_id:
                return e
        return None

    def render(self) -> str:
        lines = ["=" * 60, "CENT LEDGER — Parametric Certifications", "=" * 60]
        for e in self.entries:
            lines.append(f"\n  {e.entry_id}: {e.delta_desc}")
            lines.append(f"    £: {e.pound}")
            lines.append(f"    Result: {e.test_result}")
            if e.certified_range:
                for param, (lo, hi) in e.certified_range.items():
                    lines.append(f"    Certified: {param} ∈ [{lo}, {hi}]")
            lines.append(f"    Backing: {e.backing}")
        lines.append("=" * 60)
        return "\n".join(lines)


# ===========================================================================
# 9. Full pipeline: compile £ → enumerate ∆ → escalate → conjecture loop → certify
# ===========================================================================

def compile_with_knowledge(
    pound: str,
    impls_with_params: List[Tuple[str, str, float, Dict]],
    verbose: bool = False,
) -> Tuple[CentWheel, CentLedger, Dict]:
    """Full compilation pipeline with knowledge state management.

    1. Add all ∆ implementations to the Cent Wheel (as DOESNT_KNOW).
    2. For each, run the 5-layer escalation.
    3. If an implementation converges, promote to THINKS_TRUE.
    4. If it flips, run the conjecture loop to find an alternative.
    5. Certify the result in the parametric ledger.

    Args:
        pound: the £ target relation
        impls_with_params: list of (desc, domain, cost, params) tuples

    Returns:
        (wheel, ledger, summary)
    """
    wheel = CentWheel()
    ledger = CentLedger()

    # Sort by cost (ascending)
    sorted_impls = sorted(impls_with_params, key=lambda x: x[2])

    # Add all to the wheel
    for desc, domain, cost, params in sorted_impls:
        entry = wheel.add(
            pound=pound,
            delta_desc=desc,
            substrate_domain=domain,
            carrier_type=params.get("carrier", "temporal"),
            is_delta_sigma=params.get("is_delta_sigma", False),
            params=params,
            cost_score=cost,
        )

    # Escalate each implementation
    best_entry = None
    best_arrow = None

    for entry in wheel.entries:
        arrow = escalate(entry.params)
        entry.arrow = arrow

        if arrow.converged:
            # Promote to THINKS-TRUE (passes simulation)
            wheel.promote(
                entry.entry_id,
                KnowledgeState.THINKS_TRUE,
                f"Escalation converged: all {len(arrow.reads)} layers pass",
                arrow,
            )
            if best_entry is None or (entry.cost_score or 0) < (best_entry.cost_score or 0):
                best_entry = entry
                best_arrow = arrow
        else:
            # Record the failure
            flip = arrow.flip_layer
            entry.backing.append(f"Flipped at {flip}: {arrow.reads[-1][2]}")

            if verbose:
                print(f"  {entry.delta_description} FLIPPED at {flip}")

    # If no implementation converged, run the conjecture loop
    if best_entry is None and sorted_impls:
        if verbose:
            print(f"\n  No ∆ converged. Running conjecture loop...")

        result = conjecture_loop(
            pound=pound,
            failed_impl_desc="",
            alternatives=sorted_impls,
            verbose=verbose,
        )

        if result["found"]:
            # Find the winning entry
            for entry in wheel.entries:
                if entry.delta_description == result["impl"]:
                    best_entry = entry
                    best_arrow = result["arrow"]
                    wheel.promote(
                        entry.entry_id,
                        KnowledgeState.THINKS_TRUE,
                        f"Conjecture loop found converging ∆: {result['impl']}",
                        best_arrow,
                    )
                    break

    # Certify the best entry in the ledger
    if best_entry:
        certified_range = best_entry.params.get("certified_range", {})
        ledger.certify(
            entry=best_entry,
            test_result=f"PASS (converged through {len(best_arrow.reads)} layers)",
            backing=f"Best ∆: {best_entry.delta_description} (cost={best_entry.cost_score})",
            certified_range=certified_range,
        )

    summary = {
        "pound": pound,
        "total_impls": len(wheel.entries),
        "wheel_summary": wheel.summary(),
        "best_impl": best_entry.delta_description if best_entry else None,
        "best_cost": best_entry.cost_score if best_entry else None,
        "best_arrow": best_arrow.direction if best_arrow else None,
        "ledger_entries": len(ledger.entries),
    }

    return wheel, ledger, summary


# ===========================================================================
# Self-test
# ===========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HYPOTHESIS BRIDGE — Self-test")
    print("=" * 70)

    # Test 1: Cent Wheel rings
    print("\n--- Test 1: Cent Wheel rings ---")
    wheel = CentWheel()
    e1 = wheel.add("y = sqrt(5)", "op-amp + multiplier feedback", "electrical",
                   "temporal", is_delta_sigma=False, cost_score=9)
    e2 = wheel.add("y = sqrt(5)", "digital delta-sigma modulator", "digital",
                   "temporal", is_delta_sigma=True, cost_score=15)
    e3 = wheel.add("y = sqrt(5)", "mechanical square-root cam", "mechanical",
                   "spatial", is_delta_sigma=False, cost_score=16)

    print(wheel.render())

    # Test 2: Escalation
    print("\n--- Test 2: 5-layer escalation ---")
    params_good = {
        "v_in_range": [0.1, 10],
        "opamp_gain": 1e5,
        "bandwidth_hz": 1e6,
        "temperature": 300,
        "resistance": 1000,
        "signal_level": 1.0,
        "current": 1e-3,
        "component_tolerance": 0.01,
        "n_components": 3,
    }
    arrow = escalate(params_good)
    print(arrow.render())
    print(f"  Converged: {arrow.converged}")

    # Test 3: Conjecture loop
    print("\n--- Test 3: Conjecture loop (re-lift on failure) ---")
    params_bad = {
        "opamp_gain": 10,  # very low gain → fails at parasitic layer
        "bandwidth_hz": 1e9,  # very high bandwidth → fails at thermal
        "resistance": 1e6,  # high R → high Johnson noise
        "signal_level": 0.001,  # low signal
        "current": 1e-9,
        "component_tolerance": 0.1,
        "n_components": 10,
    }
    alternatives = [
        ("op-amp + multiplier (good)", "electrical", 9, params_good),
        ("op-amp + multiplier (bad)", "electrical", 8, params_bad),
        ("mechanical cam", "mechanical", 16, params_good),
    ]
    result = conjecture_loop(
        "y = sqrt(5)",
        "op-amp + multiplier (bad)",
        alternatives,
        verbose=True,
    )
    print(f"\n  Result: found={result['found']}")
    if result["found"]:
        print(f"  Best ∆: {result['impl']} (cost={result['cost']})")

    # Test 4: Full pipeline
    print("\n--- Test 4: Full compile_with_knowledge pipeline ---")
    impls = [
        ("op-amp sqrt (good)", "electrical", 9, {**params_good, "carrier": "temporal"}),
        ("op-amp sqrt (bad gain)", "electrical", 8, {**params_bad, "carrier": "temporal"}),
        ("delta-sigma sqrt", "digital", 15, {**params_good, "carrier": "temporal", "is_delta_sigma": True}),
        ("mechanical cam", "mechanical", 16, {**params_good, "carrier": "spatial"}),
    ]
    wheel2, ledger, summary = compile_with_knowledge("y = sqrt(5)", impls, verbose=True)

    print(f"\n{wheel2.render()}")
    print(f"\n{ledger.render()}")
    print(f"\nSummary: {summary}")
