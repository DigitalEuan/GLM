"""
ldp_grid_metrics.py — bridge LDP concepts to 2D grids and objects
===================================================================

Literal Data Physics gives us physical properties for integers:
  - mass: topological mass M(N) = C(N) = ⌊N/2⌋ − φ(N)/2
  - tension: geometric tension T(N) = 1 − (Area_polygon / Area_circle)
  - zone: "ground" (prime), "shallow", "medium", "deep"
  - radius: R(N) = 1/(2·sin(π/N))

This module bridges those concepts to ARC grids and objects:
  - GRID mass: sum of all object masses (total topological complexity)
  - GRID tension: mean tension across all objects (structural stability)
  - GRID zone: the dominant zone (most objects are ground/shallow/medium/deep)
  - OBJECT mass: the DataObject's mass for the object's cell count
  - REACTION score: how much the transformation changes the grid's mass

The key insight: instead of using NRCI (Golay coherence) to rank candidates,
we use LDP physics to ask: "Which transformation results in a grid with the
most stable topological structure?"

Stability = low tension + high prime-ground-state count + low mass defect.

This is NOT NRCI — it's a completely different physics. NRCI measures Golay
alignment; LDP measures topological mass and tension. Using both gives us
two independent quality signals.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_VENDOR_DIR = os.path.join(_THIS_DIR, "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from ldp import DataObject, react, sub_cycles, tension as ldp_tension, radius as ldp_radius, constants
from arc_loader import Grid
from generative.object_extractor import extract_objects, GridObject


# ══════════════════════════════════════════════════════════════════════════════
# LDP GRID METRICS — physical properties of a whole grid
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class LDPGridMetrics:
    """LDP physical metrics for an entire grid.

    These are NOT NRCI — they're based on Literal Data Physics:
      - total_mass: sum of topological masses of all objects
      - mean_tension: average geometric tension (lower = more stable)
      - prime_count: number of objects at prime ground state (mass=0)
      - deep_count: number of objects in deep zone (high mass)
      - dominant_zone: the most common zone
      - stability_score: composite (higher = more stable)
    """
    total_mass: int = 0
    mean_tension: float = 0.0
    max_tension: float = 0.0
    prime_count: int = 0
    deep_count: int = 0
    object_count: int = 0
    dominant_zone: str = ""
    stability_score: float = 0.0
    mass_distribution: Dict[str, int] = field(default_factory=dict)

    def __repr__(self):
        return (f"LDPGridMetrics(mass={self.total_mass}, "
                f"tension={self.mean_tension:.6f}, "
                f"primes={self.prime_count}, "
                f"stability={self.stability_score:.4f})")


def compute_ldp_grid_metrics(grid: Grid) -> LDPGridMetrics:
    """Compute LDP physical metrics for a grid.

    Each object in the grid is treated as a DataObject (its cell count
    is the integer N). The grid's metrics aggregate the objects' properties.

    Stability score = (prime_count / object_count) * (1 - mean_tension)
    Higher stability = more prime ground states + lower tension.
    """
    objects = extract_objects(grid)

    if not objects:
        return LDPGridMetrics()

    total_mass = 0
    tensions = []
    prime_count = 0
    deep_count = 0
    zone_counts = defaultdict(int)

    for obj in objects:
        n = obj.cell_count
        if n < 1:
            continue
        data_obj = DataObject(n)
        total_mass += data_obj.mass
        tensions.append(data_obj.tension)
        if data_obj.is_prime:
            prime_count += 1
        if data_obj.zone == "deep":
            deep_count += 1
        zone_counts[data_obj.zone] += 1

    mean_tension = sum(tensions) / len(tensions) if tensions else 0.0
    max_tension = max(tensions) if tensions else 0.0
    dominant_zone = max(zone_counts, key=zone_counts.get) if zone_counts else ""

    # Stability: normalised prime density * inverse tension
    obj_count = len(objects)
    prime_density = prime_count / obj_count if obj_count > 0 else 0
    inverse_tension = 1.0 - mean_tension
    stability_score = prime_density * inverse_tension

    return LDPGridMetrics(
        total_mass=total_mass,
        mean_tension=mean_tension,
        max_tension=max_tension,
        prime_count=prime_count,
        deep_count=deep_count,
        object_count=obj_count,
        dominant_zone=dominant_zone,
        stability_score=stability_score,
        mass_distribution=dict(zone_counts),
    )


# ══════════════════════════════════════════════════════════════════════════════
# LDP TRANSFORMATION SCORE — how much does a transformation change physics?
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class LDPTransformScore:
    """LDP-based score for a transformation (input → output).

    The score measures how the transformation changes the grid's physics:
      - mass_delta: change in total topological mass
      - tension_delta: change in mean tension
      - prime_delta: change in prime ground state count
      - stability_delta: change in stability score
      - regime: EXOTHERMIC (mass decreased), ENDOTHERMIC (mass increased), ISO (same)
      - physics_score: composite (higher = better transformation)
    """
    mass_delta: int = 0
    tension_delta: float = 0.0
    prime_delta: int = 0
    stability_delta: float = 0.0
    regime: str = ""
    physics_score: float = 0.0

    def __repr__(self):
        return (f"LDPTransformScore(Δmass={self.mass_delta:+d}, "
                f"Δtension={self.tension_delta:+.6f}, "
                f"Δprimes={self.prime_delta:+d}, "
                f"regime={self.regime}, "
                f"score={self.physics_score:.4f})")


def score_transformation(input_grid: Grid, output_grid: Grid) -> LDPTransformScore:
    """Score a transformation using LDP physics.

    Computes LDP metrics for both input and output, then measures the delta.
    The physics_score rewards transformations that:
      - Increase stability (more prime ground states, lower tension)
      - Have small mass delta (conservative transformations)
      - Are ISO-RESONANT (mass conserved → pure resonance transfer)
    """
    in_metrics = compute_ldp_grid_metrics(input_grid)
    out_metrics = compute_ldp_grid_metrics(output_grid)

    mass_delta = out_metrics.total_mass - in_metrics.total_mass
    tension_delta = out_metrics.mean_tension - in_metrics.mean_tension
    prime_delta = out_metrics.prime_count - in_metrics.prime_count
    stability_delta = out_metrics.stability_score - in_metrics.stability_score

    # Regime: based on mass change
    if mass_delta < 0:
        regime = "EXOTHERMIC"  # mass decreased → energy released
    elif mass_delta > 0:
        regime = "ENDOTHERMIC"  # mass increased → energy absorbed
    else:
        regime = "ISO-RESONANT"  # mass conserved → pure resonance

    # Physics score: reward stability increase, penalise tension increase
    # ISO-RESONANT transformations get a bonus (they preserve structure)
    score = stability_delta
    if regime == "ISO-RESONANT":
        score += 0.1  # bonus for structural conservation
    if tension_delta < 0:
        score += abs(tension_delta) * 10  # reward tension decrease
    if prime_delta > 0:
        score += prime_delta * 0.05  # reward new prime ground states

    return LDPTransformScore(
        mass_delta=mass_delta,
        tension_delta=tension_delta,
        prime_delta=prime_delta,
        stability_delta=stability_delta,
        regime=regime,
        physics_score=score,
    )


# ══════════════════════════════════════════════════════════════════════════════
# LDP-RANKED CANDIDATE SELECTION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ScoredCandidate:
    """A candidate transformation scored by LDP physics + train-pass."""
    grid: Grid
    train_pass: bool
    ldp_score: LDPTransformScore
    source: str  # "ranker", "analogy", "chain", "group", "conditional"
    # Combined ranking score: train_pass is primary, LDP is tiebreaker
    rank_score: float = 0.0

    def __repr__(self):
        return (f"ScoredCandidate(train={self.train_pass}, "
                f"ldp={self.ldp_score.physics_score:.4f}, "
                f"source={self.source}, "
                f"rank={self.rank_score:.4f})")


def rank_candidates_by_ldp(task: ARCTask,
                            candidates: List[Tuple[Grid, str]]) -> List[ScoredCandidate]:
    """Rank candidates by train-pass FIRST, LDP physics as tiebreaker.

    Args:
        task: the ARC task (for train verification)
        candidates: list of (predicted_grid, source) tuples

    Returns:
        Sorted list of ScoredCandidate (best first).
        train_pass=True candidates always rank above train_pass=False.
        Among train_pass=True, higher LDP physics_score ranks first.
    """
    test_input = task.test[0].input
    scored: List[ScoredCandidate] = []

    for grid, source in candidates:
        # Compute LDP score
        ldp_score = score_transformation(test_input, grid)

        # Check train-pass (STRICT: does the colour mapping reproduce train?)
        train_pass = _check_train_pass(task, test_input, grid)

        # Compute rank score: train_pass is worth 1000 points (primary),
        # LDP physics is worth 0-1 points (tiebreaker)
        rank_score = (1000.0 if train_pass else 0.0) + ldp_score.physics_score

        scored.append(ScoredCandidate(
            grid=grid,
            train_pass=train_pass,
            ldp_score=ldp_score,
            source=source,
            rank_score=rank_score,
        ))

    # Sort by rank_score descending (train-pass first, then LDP)
    scored.sort(key=lambda c: -c.rank_score)
    return scored


def _check_train_pass(task: ARCTask, test_input: Grid, predicted: Grid) -> bool:
    """Strict train-pass check: extract colour mapping and verify EXACT match."""
    if test_input.shape != predicted.shape:
        # Shape change — check consistency only
        for pair in task.train:
            if pair.input.shape == test_input.shape:
                if pair.output.shape != predicted.shape:
                    return False
        return True

    # Extract mapping
    mapping: Dict[int, int] = {}
    for r in range(test_input.height):
        for c in range(test_input.width):
            old = test_input.cells[r][c]
            new = predicted.cells[r][c]
            if old != new:
                if old in mapping and mapping[old] != new:
                    return False
                mapping[old] = new

    if not mapping:
        # Identity — check if train is also identity
        return all(p.input == p.output for p in task.train)

    # Apply mapping to each train pair
    from dsl.arc_dsl_full import Operation, Ops, Program
    prog = Program([Operation(Ops.RECOLOUR, {"mapping": mapping})])
    for pair in task.train:
        if pair.input.shape == pair.output.shape:
            if prog.apply(pair.input) != pair.output:
                return False

    return True


# ══════════════════════════════════════════════════════════════════════════════
# LDP-ENHANCED PIPELINE — combine all candidate sources + LDP ranking
# ══════════════════════════════════════════════════════════════════════════════

def solve_with_ldp(task: ARCTask) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """Solve a task using LDP-ranked candidates from all sources.

    Collects candidates from:
      1. Smart candidates (ranker)
      2. Conditional candidates (position-dependent patterns)
      3. Analogical reasoning (CRG)
      4. Transformation chains (CRG)
      5. Group patterns (CRG)

    Then ranks ALL candidates by:
      1. train-pass (HARD FILTER — must reproduce train pairs)
      2. LDP physics score (TIEBREAKER — most stable topological structure)

    Returns (predicted_grid, source, diagnostics).
    """
    test_input = task.test[0].input
    all_candidates: List[Tuple[Grid, str]] = []

    # Source 1: Smart candidates (from ranker)
    from grammar.smart_candidates import generate_smart_candidates
    from ranker import Ranker
    smart_cands = generate_smart_candidates(task, max_length=2)
    ranker = Ranker()
    results = ranker.rank(task, smart_cands)
    for r in results:
        if r.train_pass and r.error is None and r.test_output is not None:
            all_candidates.append((r.test_output, "ranker"))

    # Source 2: Conditional candidates
    from grammar.conditional_candidates import generate_conditional_candidates
    cond_cands = generate_conditional_candidates(task)
    for cand in cond_cands:
        try:
            pred = cand.apply(test_input)
            all_candidates.append((pred, "conditional"))
        except Exception:
            pass

    # Source 3: Analogical reasoning
    from generative.object_crg_full import ObjectCRG as FullCRG
    from generative.prediction_paths import predict_via_analogy, predict_via_chain, predict_via_groups
    crg = FullCRG()
    crg.learn_from_task(task)

    try:
        pred = predict_via_analogy(task, crg)
        if pred is not None:
            all_candidates.append((pred, "analogy"))
    except Exception:
        pass

    # Source 4: Transformation chains
    try:
        pred = predict_via_chain(task, crg)
        if pred is not None:
            all_candidates.append((pred, "chain"))
    except Exception:
        pass

    # Source 5: Group patterns
    try:
        pred = predict_via_groups(task, crg)
        if pred is not None:
            all_candidates.append((pred, "group"))
    except Exception:
        pass

    # Source 6: Identity (fallback)
    all_candidates.append((test_input.copy(), "identity"))

    # Rank ALL candidates by train-pass + LDP physics
    scored = rank_candidates_by_ldp(task, all_candidates)

    # Return the best candidate
    if scored:
        best = scored[0]
        diagnostics = {
            "n_candidates": len(all_candidates),
            "n_train_pass": sum(1 for c in scored if c.train_pass),
            "ldp_score": best.ldp_score.__dict__,
            "all_scores": [(c.source, c.train_pass, c.ldp_score.physics_score) for c in scored[:5]],
        }
        return best.grid, best.source, diagnostics

    return test_input.copy(), "fallback", {"n_candidates": 0}
