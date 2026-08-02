"""
v037_lucas_lehmer.py — Lucas-Lehmer Trajectory Fingerprint for ARC
===================================================================

Implements the Lucas-Lehmer trajectory sensor:
- For each integer n, compute s_{k+1} = s_k² - 2 (mod n)
- Track Rotation Sign Changes (RSC) — direction reversals
- Generate 4D prime-residue fingerprint trajectory

The RSC acts as an internal state machine that oscillates based on
the structural properties of n, providing a dynamic "clock" for
the GLM grammar.

Key insight: ARC colours are not static labels — they have dynamic
trajectories that encode their structural behaviour.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
import sys, os, signal
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)


def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c]
               for r in range(g1.height) for c in range(g1.width))


# ═══════════════════════════════════════════════════════════════════
# 1. LUCAS-LEHMER TRAJECTORY
# ═══════════════════════════════════════════════════════════════════

def lucas_lehmer_trajectory(n: int, max_steps: int = 20) -> List[int]:
    """
    Compute the Lucas-Lehmer trajectory for integer n.
    s_0 = 4, s_{k+1} = s_k² - 2 (mod n)
    
    For n=0 or n=1, returns [4] (degenerate case).
    """
    if n <= 1:
        return [4]
    
    trajectory = [4 % n]
    for _ in range(max_steps - 1):
        s = trajectory[-1]
        next_s = (s * s - 2) % n
        trajectory.append(next_s)
        if next_s == trajectory[0] and len(trajectory) > 1:
            break  # Cycle detected
    
    return trajectory


def rotation_sign_changes(trajectory: List[int]) -> int:
    """
    Count Rotation Sign Changes (RSC) — direction reversals in the trajectory.
    
    A direction reversal occurs when:
    - trajectory[k] > trajectory[k-1] AND trajectory[k+1] < trajectory[k]
    - OR trajectory[k] < trajectory[k-1] AND trajectory[k+1] > trajectory[k]
    """
    if len(trajectory) < 3:
        return 0
    
    rsc = 0
    for i in range(1, len(trajectory) - 1):
        prev_diff = trajectory[i] - trajectory[i-1]
        next_diff = trajectory[i+1] - trajectory[i]
        
        # Direction reversal: signs differ
        if (prev_diff > 0 and next_diff < 0) or (prev_diff < 0 and next_diff > 0):
            rsc += 1
    
    return rsc


def trajectory_features(n: int) -> Dict[str, float]:
    """
    Compute Lucas-Lehmer trajectory features for integer n.
    Returns a feature vector for use in the Minkowski sweep.
    """
    traj = lucas_lehmer_trajectory(n, max_steps=20)
    rsc = rotation_sign_changes(traj)
    
    # Trajectory statistics
    traj_arr = np.array(traj, dtype=float)
    
    features = {
        'll_rsc': rsc,
        'll_mean': np.mean(traj_arr),
        'll_std': np.std(traj_arr),
        'll_range': np.max(traj_arr) - np.min(traj_arr),
        'll_length': len(traj),
        'll_first': traj[0],
        'll_last': traj[-1],
        'll_cycle_len': len(traj) if traj[-1] == traj[0] else 0,
    }
    
    # 4D prime-residue fingerprint
    # Residues at steps 1, 2, 4, 8 (if available)
    for i, step in enumerate([0, 1, 2, 4]):
        if step < len(traj):
            features[f'll_residue_{step}'] = traj[step]
        else:
            features[f'll_residue_{step}'] = 0
    
    return features


# ═══════════════════════════════════════════════════════════════════
# 2. RSC FIELD — Dynamic "Clock" for ARC Grids
# ═══════════════════════════════════════════════════════════════════

def compute_rsc_field(grid: Grid) -> np.ndarray:
    """
    Compute the RSC field for an ARC grid.
    Each cell's colour value generates its own RSC "heartbeat".
    """
    h, w = grid.height, grid.width
    rsc_field = np.zeros((h, w))
    
    # Cache RSC values for colours 0-9
    rsc_cache = {}
    for c in range(10):
        rsc_cache[c] = trajectory_features(c)['ll_rsc']
    
    for r in range(h):
        for c in range(w):
            rsc_field[r, c] = rsc_cache[grid.cells[r][c]]
    
    return rsc_field


def compute_trajectory_feature_field(grid: Grid, feature_name: str) -> np.ndarray:
    """Compute a specific trajectory feature field for an ARC grid."""
    h, w = grid.height, grid.width
    field = np.zeros((h, w))
    
    # Cache feature values for colours 0-9
    cache = {}
    for c in range(10):
        cache[c] = trajectory_features(c)[feature_name]
    
    for r in range(h):
        for c in range(w):
            field[r, c] = cache[grid.cells[r][c]]
    
    return field


# ═══════════════════════════════════════════════════════════════════
# 3. RSC-BASED RULE DISCOVERY
# ═══════════════════════════════════════════════════════════════════

def try_rsc_based_rule(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Try to find rules based on Lucas-Lehmer trajectory features.
    
    Approach: for each cell that changes, record its trajectory features.
    Search for features that perfectly separate changed from unchanged cells.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Collect trajectory features for changed vs unchanged cells
    changed_features = []
    unchanged_features = []
    
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic = pair.input.cells[r][c]
                oc = pair.output.cells[r][c]
                feats = trajectory_features(ic)
                
                if ic != oc:
                    changed_features.append(feats)
                else:
                    unchanged_features.append(feats)
    
    if not changed_features:
        return None
    
    # Find features that separate changed from unchanged
    feat_names = list(changed_features[0].keys())
    
    for feat_name in feat_names:
        changed_vals = set(f[feat_name] for f in changed_features)
        unchanged_vals = set(f[feat_name] for f in unchanged_features)
        
        # Find values unique to changed cells
        unique_to_changed = changed_vals - unchanged_vals
        
        if unique_to_changed:
            # Check if this rule works for all train pairs
            all_pass = True
            for pair in task.train:
                h, w = pair.input.height, pair.input.width
                cells = [row[:] for row in pair.input.cells]
                
                for r in range(h):
                    for c in range(w):
                        ic = pair.input.cells[r][c]
                        feat = trajectory_features(ic)[feat_name]
                        if feat in unique_to_changed:
                            # What should this cell become?
                            oc = pair.output.cells[r][c]
                            if ic != oc:
                                cells[r][c] = oc
                
                if not grids_equal(Grid(cells), pair.output):
                    all_pass = False
                    break
            
            if all_pass:
                # Apply to test
                test = task.test[0].input
                h, w = test.height, test.width
                
                # Determine fill colour from train
                fill_colours = []
                for pair in task.train:
                    for r in range(pair.input.height):
                        for c in range(pair.input.width):
                            ic = pair.input.cells[r][c]
                            oc = pair.output.cells[r][c]
                            feat = trajectory_features(ic)[feat_name]
                            if feat in unique_to_changed and ic != oc:
                                fill_colours.append(oc)
                
                if not fill_colours:
                    continue
                
                fill = Counter(fill_colours).most_common(1)[0][0]
                
                cells = [row[:] for row in test.cells]
                for r in range(h):
                    for c in range(w):
                        ic = test.cells[r][c]
                        feat = trajectory_features(ic)[feat_name]
                        if feat in unique_to_changed:
                            cells[r][c] = fill
                
                pred = Grid(cells)
                return pred, f"ll_{feat_name}_{len(unique_to_changed)}vals"
    
    return None


def try_rsc_neighbourhood_rule(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Try rules combining RSC with neighbourhood information.
    
    Pattern: cells with RSC=X and neighbour with RSC=Y → change to Z
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Pre-compute RSC cache
    rsc_cache = {}
    for c in range(10):
        rsc_cache[c] = trajectory_features(c)['ll_rsc']
    
    # Collect changed cell data
    changed_data = []  # (rsc, neighbour_rscs, output_colour)
    
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic != oc:
                    rsc = rsc_cache[ic]
                    neighbour_rscs = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w:
                            neighbour_rscs.append(rsc_cache[pair.input.cells[nr][nc]])
                    
                    changed_data.append((rsc, tuple(sorted(neighbour_rscs)), oc))
    
    if not changed_data:
        return None
    
    # Find consistent rules: (rsc, neighbour_rscs) → output_colour
    rule_counts = Counter()
    for rsc, n_rscs, oc in changed_data:
        rule_counts[(rsc, n_rscs)] += 1
    
    # Check if any rule is consistent
    for (rsc, n_rscs), count in rule_counts.most_common(5):
        # Verify consistency
        outputs = set()
        for r2, n2, oc in changed_data:
            if r2 == rsc and n2 == n_rscs:
                outputs.add(oc)
        
        if len(outputs) == 1:
            fill = list(outputs)[0]
            
            # Verify on train
            all_pass = True
            for pair in task.train:
                h, w = pair.input.height, pair.input.width
                cells = [row[:] for row in pair.input.cells]
                
                for r in range(h):
                    for c in range(w):
                        ic = pair.input.cells[r][c]
                        if rsc_cache[ic] == rsc:
                            n_rscs_test = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w:
                                    n_rscs_test.append(rsc_cache[pair.input.cells[nr][nc]])
                            if tuple(sorted(n_rscs_test)) == n_rscs:
                                cells[r][c] = fill
                
                if not grids_equal(Grid(cells), pair.output):
                    all_pass = False
                    break
            
            if all_pass:
                test = task.test[0].input
                h, w = test.height, test.width
                cells = [row[:] for row in test.cells]
                
                for r in range(h):
                    for c in range(w):
                        ic = test.cells[r][c]
                        if rsc_cache[ic] == rsc:
                            n_rscs_test = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w:
                                    n_rscs_test.append(rsc_cache[test.cells[nr][nc]])
                            if tuple(sorted(n_rscs_test)) == n_rscs:
                                cells[r][c] = fill
                
                pred = Grid(cells)
                return pred, f"ll_rsc_n_{rsc}_{n_rscs}_to_{fill}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 4. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try Lucas-Lehmer trajectory approaches."""
    strategies = [
        ("ll_feature", try_rsc_based_rule),
        ("ll_neighbourhood", try_rsc_neighbourhood_rule),
    ]
    
    for name, fn in strategies:
        try:
            signal.setitimer(signal.ITIMER_REAL, 10.0)
            result = fn(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
            if result is not None:
                pred, src = result
                return pred, src, {"strategy": name}
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            continue
    
    return None


if __name__ == "__main__":
    # First, show the trajectory features for ARC colours
    print("Lucas-Lehmer Trajectory Features for ARC Colours (0-9):")
    print(f"{'Col':>4} | {'RSC':>4} | {'Mean':>8} | {'Std':>8} | {'Range':>6} | {'Len':>4} | {'Residues':>20}")
    print("-" * 70)
    for c in range(10):
        f = trajectory_features(c)
        print(f"{c:>4} | {f['ll_rsc']:>4} | {f['ll_mean']:>8.2f} | {f['ll_std']:>8.2f} | {f['ll_range']:>6.0f} | {f['ll_length']:>4} | "
              f"{f['ll_residue_0']},{f['ll_residue_1']},{f['ll_residue_2']},{f['ll_residue_4']}")
    
    print()
    
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--max-tasks", type=int, default=None)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    
    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
    if args.max_tasks:
        files = files[:args.max_tasks]
    
    solved = total = 0
    sources = {}
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        result = predict(task)
        if result is not None:
            pred, src, diag = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            if args.verbose or ok:
                print(f"  {fname}: {'OK' if ok else 'X'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            if args.verbose:
                print(f"  {fname}: X src=none")
    
    print(f"\n═══ Lucas-Lehmer ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
