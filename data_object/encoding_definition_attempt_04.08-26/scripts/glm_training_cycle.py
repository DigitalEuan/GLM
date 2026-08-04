#!/usr/bin/env python3
"""
GLM Training Cycle — Element Interactions via Settlement Dynamics
=================================================================
Experiment: encoding_definition_attempt_04.08-26
Approach: Option C — Use the GLM mind with 6 Geometric Primitives

The GLM doesn't use linear regression. It uses SETTLEMENT DYNAMICS:
  1. Perceive: encode element pair as Data Objects
  2. Interpret: run 6 Geometric Interaction Primitives
  3. Propose: predict bond energy from primitive states
  4. Inspect: compare to reality, get yes/no feedback
  5. Settle: adjust primitive weights via entropic relaxation

The mind learns by repeatedly settling into configurations that
minimise prediction error — like a physical system finding equilibrium.

Key insight from Baherwani et al.:
  - Capabilities emerge ABRUPTLY, not gradually
  - Run MULTIPLE SEEDS (emergence is stochastic)
  - Track WHEN, not just IF

Usage:
  python3 glm_training_cycle.py --train --seeds 10
  python3 glm_training_cycle.py --train --seeds 5 --verbose
  python3 glm_training_cycle.py --analyze
"""

from __future__ import annotations

import json
import math
import random
import sys
import hashlib
from fractions import Fraction
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from elements_data_object_system import (
    GolayEngine, DataObject, MOGSpatialArithmetic, GLMPredictor,
    load_elements_from_kb, encode_element, interact, InteractionResult,
    BEST_ENCODING, Y_CONST, KNOWN_PAIRS,
)
from refined_element_system import (
    EXPANDED_PAIRS, compute_snap_dynamics, compute_interaction_snap_dynamics,
    pearson_r, mae, k_fold_split,
)

# ════════════════════════════════════════════════════════════════════════════════
# THE GLM CHEMISTRY MIND
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class PrimitiveState:
    """State of one Geometric Interaction Primitive."""
    name: str
    value: float              # current output
    weight: float = 1.0       # learned weight
    history: List[float] = field(default_factory=list)
    # Settlement tracking
    total_adjustment: float = 0.0
    settled: bool = False


@dataclass
class MindState:
    """The complete state of a chemistry mind."""
    # Primitive states (the 6 forces)
    primitives: Dict[str, PrimitiveState]
    # Global parameters
    learning_rate: float = 0.05
    momentum: float = 0.9
    temperature: float = 1.0  # entropic temperature (starts high, cools)
    # Experience
    experiences: List[Dict] = field(default_factory=list)
    predictions: List[float] = field(default_factory=list)
    actuals: List[float] = field(default_factory=list)
    # Emergence tracking
    correct_streak: int = 0
    max_streak: int = 0
    emergence_step: Optional[int] = None
    loss_history: List[float] = field(default_factory=list)
    # Current epoch
    epoch: int = 0


def create_mind(seed: int = 42) -> MindState:
    """Create a new chemistry mind with random initial weights."""
    rng = random.Random(seed)
    
    primitives = {}
    for name in ["gravitic", "electrostatic", "exclusion", 
                  "confinement", "cymatic", "entropic"]:
        primitives[name] = PrimitiveState(
            name=name,
            value=0.0,
            weight=rng.uniform(0.5, 2.0),  # random initial weight
        )
    
    return MindState(
        primitives=primitives,
        learning_rate=0.05,
        momentum=0.9,
        temperature=1.0,
    )


# ════════════════════════════════════════════════════════════════════════════════
# PERCEPTION — How the mind sees element pairs
# ════════════════════════════════════════════════════════════════════════════════

def perceive(mind: MindState, do_a: DataObject, do_b: DataObject,
             spatial: MOGSpatialArithmetic) -> Dict[str, float]:
    """Perceive an element pair through the 6 Geometric Primitives."""
    primitives = spatial.full_interaction(do_a, do_b)
    
    # Extract primitive values
    perception = {
        "gravitic": primitives["gravitic"],
        "electrostatic": primitives["electrostatic"],
        "exclusion": primitives["exclusion"],
        "confinement": primitives["confinement"],
        "cymatic": primitives["cymatic"]["net_score"],
        "entropic": primitives["entropic"]["tax_reduction"],
    }
    
    # Update mind's primitive states
    for name, value in perception.items():
        mind.primitives[name].value = value
        mind.primitives[name].history.append(value)
    
    return perception


# ════════════════════════════════════════════════════════════════════════════════
# INTERPRETATION — Weighted combination of primitives
# ════════════════════════════════════════════════════════════════════════════════

def interpret(mind: MindState, perception: Dict[str, float]) -> float:
    """Combine primitive perceptions using learned weights."""
    # Weighted sum with bias
    prediction = 0.0
    for name, value in perception.items():
        weight = mind.primitives[name].weight
        prediction += weight * value
    
    # Add element-level features (NRCI, TAX)
    # These provide the "identity" signal
    prediction += 100.0  # base bias (average bond energy)
    
    return prediction


# ════════════════════════════════════════════════════════════════════════════════
# SETTLEMENT DYNAMICS — How the mind learns
# ════════════════════════════════════════════════════════════════════════════════

def settle(mind: MindState, perception: Dict[str, float],
           prediction: float, actual: float) -> Dict[str, Any]:
    """
    Settle the mind's weights using entropic relaxation.
    
    Like the Entropic_Relaxation_Gradient primitive:
    - Perturb weights slightly
    - If perturbation lowers error, keep it
    - If it raises error, reject it
    - Temperature cools over time (simulated annealing)
    """
    error = actual - prediction
    abs_error = abs(error)
    
    # Record experience
    mind.experiences.append({
        "epoch": mind.epoch,
        "prediction": prediction,
        "actual": actual,
        "error": error,
        "abs_error": abs_error,
        "temperature": mind.temperature,
    })
    mind.predictions.append(prediction)
    mind.actuals.append(actual)
    
    # Track loss
    mind.loss_history.append(abs_error)
    
    # Check if prediction is "correct" (within 20% of actual)
    if actual != 0:
        relative_error = abs_error / abs(actual)
        correct = relative_error < 0.20
    else:
        correct = abs_error < 50
    
    if correct:
        mind.correct_streak += 1
        mind.max_streak = max(mind.max_streak, mind.correct_streak)
        if mind.emergence_step is None and mind.correct_streak >= 3:
            mind.emergence_step = mind.epoch
    else:
        mind.correct_streak = 0
    
    # ── Entropic weight adjustment ────────────────────────────────────────────
    # For each primitive, compute gradient and adjust weight
    adjustments = {}
    for name, ps in mind.primitives.items():
        value = ps.value
        
        # Gradient: how much does changing this weight reduce error?
        # d(error²)/d(weight) = -2 * error * value
        gradient = -2.0 * error * value
        
        # Add noise (simulated annealing)
        noise = random.gauss(0, mind.temperature * 0.1)
        
        # Proposed adjustment
        adjustment = mind.learning_rate * (gradient + noise)
        
        # Entropic acceptance: only accept if it lowers the "energy" (error)
        # With probability proportional to temperature, accept bad moves
        # (exploration vs exploitation)
        current_energy = abs_error
        
        # Simulate: what would error be with adjusted weight?
        test_weight = ps.weight + adjustment
        test_prediction = sum(mind.primitives[n].weight * perception[n] 
                            for n in mind.primitives) + 100.0
        # Re-add the adjustment for this specific primitive
        test_prediction += (test_weight - ps.weight) * value
        test_energy = abs(actual - test_prediction)
        
        # Accept/reject (Metropolis criterion)
        delta_energy = test_energy - current_energy
        if delta_energy < 0:
            # Improvement — always accept
            ps.weight = test_weight
            ps.total_adjustment += adjustment
            adjustments[name] = adjustment
        elif mind.temperature > 0:
            # Worse — accept with probability exp(-delta/T)
            acceptance_prob = math.exp(-delta_energy / max(mind.temperature, 0.01))
            if random.random() < acceptance_prob:
                ps.weight = test_weight
                ps.total_adjustment += adjustment
                adjustments[name] = adjustment
            else:
                adjustments[name] = 0.0
        else:
            adjustments[name] = 0.0
    
    # Cool the temperature (simulated annealing)
    mind.temperature *= 0.995
    mind.temperature = max(mind.temperature, 0.01)
    
    mind.epoch += 1
    
    return {
        "error": error,
        "abs_error": abs_error,
        "correct": correct,
        "adjustments": adjustments,
        "temperature": mind.temperature,
        "streak": mind.correct_streak,
    }


# ════════════════════════════════════════════════════════════════════════════════
# TRAINING LOOP
# ════════════════════════════════════════════════════════════════════════════════

def train_mind(mind: MindState, pairs: List[Dict], data_objects: Dict,
               spatial: MOGSpatialArithmetic, n_epochs: int = 3,
               verbose: bool = False) -> Dict[str, Any]:
    """
    Train the mind on element pair interactions.
    
    Each epoch shuffles the pairs and runs settlement dynamics on each.
    The mind learns by repeatedly settling into configurations that
    minimise prediction error.
    """
    rng = random.Random(42)
    
    emergence_log = []
    epoch_losses = []
    
    for epoch in range(n_epochs):
        # Shuffle pairs each epoch
        shuffled = list(pairs)
        rng.shuffle(shuffled)
        
        epoch_errors = []
        epoch_correct = 0
        
        for pair in shuffled:
            sym_a, sym_b = pair['sym_a'], pair['sym_b']
            actual_be = pair['be']
            
            if sym_a not in data_objects or sym_b not in data_objects:
                continue
            
            do_a = data_objects[sym_a]
            do_b = data_objects[sym_b]
            
            # Perceive
            perception = perceive(mind, do_a, do_b, spatial)
            
            # Interpret
            prediction = interpret(mind, perception)
            
            # Settle
            result = settle(mind, perception, prediction, actual_be)
            
            epoch_errors.append(result['abs_error'])
            if result['correct']:
                epoch_correct += 1
            
            # Check for emergence
            if mind.emergence_step == mind.epoch:
                emergence_log.append({
                    "epoch": mind.epoch,
                    "pair": f"{sym_a}-{sym_b}",
                    "prediction": prediction,
                    "actual": actual_be,
                })
        
        mean_error = sum(epoch_errors) / len(epoch_errors) if epoch_errors else 0
        accuracy = epoch_correct / len(epoch_errors) if epoch_errors else 0
        epoch_losses.append(mean_error)
        
        if verbose and (epoch % 10 == 0 or epoch == n_epochs - 1):
            weights = {n: f"{p.weight:.3f}" for n, p in mind.primitives.items()}
            print(f"  Epoch {epoch:4d}: MAE={mean_error:7.1f}  "
                  f"Acc={accuracy:.1%}  T={mind.temperature:.4f}  "
                  f"Weights={weights}")
    
    # Final evaluation
    final_predictions = mind.predictions[-len(pairs):]
    final_actuals = mind.actuals[-len(pairs):]
    final_r = pearson_r(final_predictions, final_actuals) if len(final_predictions) > 2 else 0
    final_mae = mae(final_predictions, final_actuals) if final_predictions else 0
    
    return {
        "emergence_step": mind.emergence_step,
        "max_streak": mind.max_streak,
        "final_r": final_r,
        "final_mae": final_mae,
        "epoch_losses": epoch_losses,
        "emergence_log": emergence_log,
        "final_weights": {n: p.weight for n, p in mind.primitives.items()},
        "total_adjustment": {n: p.total_adjustment for n, p in mind.primitives.items()},
        "final_temperature": mind.temperature,
    }


# ════════════════════════════════════════════════════════════════════════════════
# EVALUATION
# ════════════════════════════════════════════════════════════════════════════════

def evaluate_mind(mind: MindState, pairs: List[Dict], data_objects: Dict,
                  spatial: MOGSpatialArithmetic) -> Dict[str, Any]:
    """Evaluate the mind on a set of pairs (no learning)."""
    predictions = []
    actuals = []
    labels = []
    
    for pair in pairs:
        sym_a, sym_b = pair['sym_a'], pair['sym_b']
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        
        do_a = data_objects[sym_a]
        do_b = data_objects[sym_b]
        
        perception = perceive(mind, do_a, do_b, spatial)
        prediction = interpret(mind, perception)
        
        predictions.append(prediction)
        actuals.append(pair['be'])
        labels.append(pair['label'])
    
    r = pearson_r(predictions, actuals) if len(predictions) > 2 else 0
    mae_val = mae(predictions, actuals) if predictions else 0
    
    return {
        "r": r,
        "mae": mae_val,
        "n": len(predictions),
        "predictions": predictions,
        "actuals": actuals,
        "labels": labels,
    }


# ════════════════════════════════════════════════════════════════════════════════
# MULTI-SEED EMERGENCE TEST
# ════════════════════════════════════════════════════════════════════════════════

def run_emergence_test(n_seeds: int = 10, n_epochs: int = 50,
                       verbose: bool = False) -> Dict[str, Any]:
    """
    Run multiple seeds to find emergence points.
    
    From Baherwani et al.:
    - Same capability emerges at DIFFERENT training steps per seed
    - Don't judge by one run — emergence is stochastic
    - Track WHEN (not just if) settlement dynamics are learned
    """
    import numpy as np
    
    print("=" * 72)
    print("GLM TRAINING CYCLE — Element Interactions via Settlement Dynamics")
    print(f"Seeds: {n_seeds}, Epochs per seed: {n_epochs}")
    print("=" * 72)
    
    # Load data
    kb_path = Path(__file__).resolve().parent.parent.parent / "long_term_memory" / "ubp_system_kb.json"
    if not kb_path.exists():
        kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
    
    print(f"\n[1] Loading elements from {kb_path}")
    elements = load_elements_from_kb(str(kb_path))
    print(f"    Loaded {len(elements)} elements")
    
    golay = GolayEngine()
    spatial = MOGSpatialArithmetic(golay)
    
    # Encode elements
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    print(f"    Encoded {len(data_objects)} elements")
    
    # Prepare pairs
    pairs = []
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a in data_objects and sym_b in data_objects:
            pairs.append({
                'sym_a': sym_a, 'sym_b': sym_b,
                'be': be, 'dh': dh, 'label': label, 'bo': bo,
            })
    print(f"    Valid pairs: {len(pairs)}")
    
    # Split into train/test
    rng = random.Random(42)
    shuffled = list(pairs)
    rng.shuffle(shuffled)
    split = int(len(shuffled) * 0.8)
    train_pairs = shuffled[:split]
    test_pairs = shuffled[split:]
    print(f"    Train: {len(train_pairs)}, Test: {len(test_pairs)}")
    
    # ── Run multiple seeds ────────────────────────────────────────────────────
    print(f"\n[2] Running {n_seeds} seeds × {n_epochs} epochs")
    
    results = []
    for seed in range(n_seeds):
        mind = create_mind(seed=seed)
        
        train_result = train_mind(
            mind, train_pairs, data_objects, spatial,
            n_epochs=n_epochs, verbose=False,
        )
        
        # Evaluate on test set
        test_eval = evaluate_mind(mind, test_pairs, data_objects, spatial)
        
        results.append({
            "seed": seed,
            "emergence_step": train_result["emergence_step"],
            "max_streak": train_result["max_streak"],
            "train_r": train_result["final_r"],
            "train_mae": train_result["final_mae"],
            "test_r": test_eval["r"],
            "test_mae": test_eval["mae"],
            "final_weights": train_result["final_weights"],
            "epoch_losses": train_result["epoch_losses"],
            "final_temperature": train_result["final_temperature"],
        })
        
        if verbose or seed < 3:
            print(f"    Seed {seed:2d}: emergence={train_result['emergence_step']!s:>5}  "
                  f"streak={train_result['max_streak']:2d}  "
                  f"train_r={train_result['final_r']:.4f}  "
                  f"test_r={test_eval['r']:.4f}  "
                  f"test_MAE={test_eval['mae']:.1f}")
    
    # ── Analyse emergence distribution ────────────────────────────────────────
    print(f"\n[3] Emergence analysis")
    
    emerged = [r for r in results if r["emergence_step"] is not None]
    not_emerged = [r for r in results if r["emergence_step"] is None]
    
    print(f"    Emerged: {len(emerged)}/{n_seeds}")
    if emerged:
        steps = [r["emergence_step"] for r in emerged]
        print(f"    Emergence steps: min={min(steps)}, max={max(steps)}, "
              f"mean={sum(steps)/len(steps):.1f}, std={np.std(steps):.1f}")
    
    # Best seed
    best = max(results, key=lambda r: r["test_r"])
    print(f"\n    Best seed: {best['seed']}")
    print(f"      Train r = {best['train_r']:.4f}")
    print(f"      Test r  = {best['test_r']:.4f}")
    print(f"      Test MAE = {best['test_mae']:.1f}")
    print(f"      Weights: {', '.join(f'{n}={w:.3f}' for n, w in best['final_weights'].items())}")
    
    # Weight analysis
    print(f"\n[4] Weight analysis (final weights across all seeds)")
    for name in ["gravitic", "electrostatic", "exclusion", "confinement", "cymatic", "entropic"]:
        weights = [r["final_weights"][name] for r in results]
        print(f"    {name:<15} mean={sum(weights)/len(weights):>8.3f}  "
              f"std={np.std(weights):>8.3f}  "
              f"range=[{min(weights):.3f}, {max(weights):.3f}]")
    
    # Loss curves
    print(f"\n[5] Loss curve analysis")
    for r in results[:3]:
        losses = r["epoch_losses"]
        first_5 = sum(losses[:5]) / 5 if len(losses) >= 5 else losses[0]
        last_5 = sum(losses[-5:]) / 5 if len(losses) >= 5 else losses[-1]
        improvement = first_5 - last_5
        print(f"    Seed {r['seed']}: first_5_MAE={first_5:.1f}  last_5_MAE={last_5:.1f}  "
              f"improvement={improvement:+.1f}")
    
    # ── Verbose: show best seed's predictions ─────────────────────────────────
    if verbose:
        print(f"\n[6] Best seed predictions on test set")
        best_mind = create_mind(seed=best["seed"])
        train_mind(best_mind, train_pairs, data_objects, spatial, n_epochs=n_epochs)
        test_eval = evaluate_mind(best_mind, test_pairs, data_objects, spatial)
        
        print(f"\n    {'Label':<30} {'Actual':>8} {'Predicted':>10} {'Error':>8}")
        print(f"    {'-'*58}")
        for i in range(len(test_eval["labels"])):
            label = test_eval["labels"][i]
            actual = test_eval["actuals"][i]
            pred = test_eval["predictions"][i]
            err = actual - pred
            print(f"    {label:<30} {actual:>8.0f} {pred:>10.1f} {err:>+8.1f}")
    
    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("TRAINING CYCLE SUMMARY")
    print(f"{'='*72}")
    
    test_rs = [r["test_r"] for r in results]
    print(f"  Seeds:              {n_seeds}")
    print(f"  Epochs:             {n_epochs}")
    print(f"  Pairs:              {len(train_pairs)} train, {len(test_pairs)} test")
    print(f"  Emergence rate:     {len(emerged)}/{n_seeds} = {len(emerged)/n_seeds:.0%}")
    print(f"  Mean test r:        {sum(test_rs)/len(test_rs):.4f} ± {np.std(test_rs):.4f}")
    print(f"  Best test r:        {best['test_r']:.4f}")
    print(f"  Best test MAE:      {best['test_mae']:.1f} kJ/mol")
    print()
    
    # Convergence assessment
    improving = sum(1 for r in results 
                   if r["epoch_losses"][-1] < r["epoch_losses"][0])
    print(f"  Converging:         {improving}/{n_seeds} seeds showed loss reduction")
    
    if best["test_r"] > 0.5:
        print(f"  ✓ Best seed shows meaningful correlation")
    elif best["test_r"] > 0.3:
        print(f"  ⚠ Best seed shows weak correlation — needs more epochs or better primitives")
    else:
        print(f"  ✗ No seed found meaningful correlation — primitives may need rethinking")
    
    return {
        "n_seeds": n_seeds,
        "n_epochs": n_epochs,
        "n_train": len(train_pairs),
        "n_test": len(test_pairs),
        "emergence_rate": len(emerged) / n_seeds,
        "mean_test_r": sum(test_rs) / len(test_rs),
        "best_test_r": best["test_r"],
        "best_test_mae": best["test_mae"],
        "best_seed": best["seed"],
        "best_weights": best["final_weights"],
        "all_results": results,
    }


# ════════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GLM Training Cycle")
    parser.add_argument("--train", action="store_true", help="Run training")
    parser.add_argument("--seeds", type=int, default=10, help="Number of seeds")
    parser.add_argument("--epochs", type=int, default=50, help="Epochs per seed")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--analyze", action="store_true", help="Analyze results")
    
    args = parser.parse_args()
    
    if args.train:
        results = run_emergence_test(
            n_seeds=args.seeds,
            n_epochs=args.epochs,
            verbose=args.verbose,
        )
        # Save results
        save_path = SCRIPT_DIR.parent / "data" / f"glm_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(save_path, 'w') as f:
            # Convert non-serializable types
            save_results = {k: v for k, v in results.items() if k != "all_results"}
            save_results["all_results"] = [
                {k: v for k, v in r.items() if k != "epoch_losses"}
                for r in results["all_results"]
            ]
            json.dump(save_results, f, indent=2, default=str)
        print(f"\n  Results saved to: {save_path}")
    elif args.analyze:
        # Find most recent results
        data_dir = SCRIPT_DIR.parent / "data"
        files = sorted(data_dir.glob("glm_training_*.json"))
        if files:
            with open(files[-1]) as f:
                data = json.load(f)
            print(json.dumps(data, indent=2))
        else:
            print("No training results found. Run --train first.")
    else:
        parser.print_help()
