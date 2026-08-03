"""
arc_learning_mind.py — A Mind That Learns Through Experimentation

Not a fixed toolkit. A mind that:
1. Encodes every task as a Data Object
2. Classifies tasks by substrate signature
3. Tries strategies and remembers what works
4. Builds a routing table: task signature → successful strategy
5. Gets better with each task it sees

The key: EXPERIENCE ACCUMULATION. Failed attempts teach as much as successes.
"""

from __future__ import annotations
import os, sys, json, math, time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

SCRIPT_DIR = Path(__file__).resolve().parent
ARC_DIR = SCRIPT_DIR.parent / "glm_machine"
LTM_DIR = SCRIPT_DIR.parent / "long_term_memory"
sys.path.insert(0, str(ARC_DIR / "arc_loader"))
sys.path.insert(0, str(ARC_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parent / "data_object" / "scripts"))

from loader import ARCTask, Grid, load_task
import consolidated_mind as cm
from collections import Counter as Counter2

Y = 0.2646754304045269672

try:
    import ubp_unified_v5 as ubp
    GOLAY = ubp.GOLAY_ENGINE
    HAS_GOLAY = True
except:
    HAS_GOLAY = False
    GOLAY = None


# ═══════════════════════════════════════════════════════════════════════════════
# Data Object Encoding
# ═══════════════════════════════════════════════════════════════════════════════

def grid_to_do(grid: Grid) -> List[int]:
    h, w = grid.height, grid.width
    flat = [grid.cells[r][c] for r in range(h) for c in range(w)]
    cc = Counter(flat)
    top6 = [c for c, _ in cc.most_common(6)]
    row0 = [1 if i < len(top6) and top6[i] != 0 else 0 for i in range(6)]

    has_border = any(grid.cells[0][c] != 0 for c in range(w)) or any(grid.cells[h-1][c] != 0 for c in range(w))
    has_interior = any(grid.cells[r][c] != 0 for r in range(1, h-1) for c in range(1, w-1)) if h > 2 and w > 2 else False
    h_sym = all(grid.cells[r] == grid.cells[h-1-r] for r in range(h//2))
    v_sym = all(grid.cells[r][c] == grid.cells[r][w-1-c] for r in range(h) for c in range(w//2))
    density = sum(1 for v in flat if v != 0) / max(len(flat), 1)
    row1 = [int(has_border), int(has_interior), int(density > 0.5), int(h_sym), int(v_sym), int(h == w)]

    n_col = len(set(flat)) - (1 if 0 in flat else 0)
    row2_val = min(n_col * 8, 63)
    row2 = [(row2_val >> (5-i)) & 1 for i in range(6)]
    row3_val = min(h * 4 + w, 63)
    row3 = [(row3_val >> (5-i)) & 1 for i in range(6)]

    return row0 + row1 + row2 + row3


def do_metrics(vec: List[int]) -> Dict:
    hw = sum(vec)
    tax = hw * Y + sum(v*v for v in vec) / 8.0
    nrci = 10.0 / (10.0 + tax)
    return {"hw": hw, "nrci": nrci}


def do_and(a, b): return [a[i] & b[i] for i in range(24)]
def do_xor(a, b): return [a[i] ^ b[i] for i in range(24)]


# ═══════════════════════════════════════════════════════════════════════════════
# Task Signature — what the mind "sees"
# ═══════════════════════════════════════════════════════════════════════════════

def task_signature(task: ARCTask) -> Dict:
    """Extract a task signature from the substrate."""
    test = task.test[0].input
    test_do = grid_to_do(test)

    # Compute signature from train pairs
    pair_sigs = []
    for pair in task.train:
        inp_do = grid_to_do(pair.input)
        out_do = grid_to_do(pair.output)
        and_vec = do_and(inp_do, out_do)
        xor_vec = do_xor(inp_do, out_do)
        and_m = do_metrics(and_vec)
        xor_m = do_metrics(xor_vec)
        inp_m = do_metrics(inp_do)
        out_m = do_metrics(out_do)

        ih, iw = pair.input.height, pair.input.width
        oh, ow = pair.output.height, pair.output.width

        pair_sigs.append({
            "size_change": (ih != oh or iw != ow),
            "ih": ih, "iw": iw, "oh": oh, "ow": ow,
            "and_nrci": and_m["nrci"],
            "and_hw": and_m["hw"],
            "xor_hw": xor_m["hw"],
            "inp_nrci": inp_m["nrci"],
            "out_nrci": out_m["nrci"],
            "delta_nrci": out_m["nrci"] - inp_m["nrci"],
            "inp_hw": inp_m["hw"],
            "out_hw": out_m["hw"],
        })

    # Aggregate signature
    avg_and_nrci = statistics.mean([p["and_nrci"] for p in pair_sigs])
    avg_xor_hw = statistics.mean([p["xor_hw"] for p in pair_sigs])
    avg_delta_nrci = statistics.mean([p["delta_nrci"] for p in pair_sigs])
    has_size_change = any(p["size_change"] for p in pair_sigs)
    avg_inp_hw = statistics.mean([p["inp_hw"] for p in pair_sigs])

    # Classify
    if has_size_change:
        task_type = "size_change"
    elif avg_xor_hw == 0:
        task_type = "invisible"  # transform doesn't change encoding
    elif avg_and_nrci > 0.8:
        task_type = "high_overlap"  # lots of shared structure
    elif avg_and_nrci < 0.65:
        task_type = "low_overlap"  # little shared structure
    else:
        task_type = "medium_overlap"

    return {
        "task_type": task_type,
        "and_nrci": round(avg_and_nrci, 4),
        "xor_hw": round(avg_xor_hw, 1),
        "delta_nrci": round(avg_delta_nrci, 4),
        "has_size_change": has_size_change,
        "inp_hw": round(avg_inp_hw, 1),
        "pair_sigs": pair_sigs,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Experience Store — the mind's memory of what worked
# ═══════════════════════════════════════════════════════════════════════════════

class ExperienceStore:
    """What the mind has learned about which strategies work for which tasks."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or LTM_DIR / "experience.json"
        self.experiences = []
        self.routing_table = {}  # task_type → {solver: success_rate}
        if self.path.exists():
            with open(self.path) as f:
                data = json.load(f)
                self.experiences = data.get("experiences", [])
                self.routing_table = data.get("routing_table", {})

    def record(self, task_id: str, sig: Dict, solver: str, success: bool):
        """Record an experience."""
        self.experiences.append({
            "task_id": task_id,
            "task_type": sig["task_type"],
            "and_nrci": sig["and_nrci"],
            "xor_hw": sig["xor_hw"],
            "solver": solver,
            "success": success,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })

        # Update routing table
        ttype = sig["task_type"]
        if ttype not in self.routing_table:
            self.routing_table[ttype] = {}
        if solver not in self.routing_table[ttype]:
            self.routing_table[ttype][solver] = {"attempts": 0, "successes": 0}
        self.routing_table[ttype][solver]["attempts"] += 1
        if success:
            self.routing_table[ttype][solver]["successes"] += 1

    def best_solver(self, task_type: str) -> Optional[str]:
        """Get the best solver for a task type based on experience."""
        if task_type not in self.routing_table:
            return None
        best = None
        best_rate = -1
        for solver, stats in self.routing_table[task_type].items():
            if stats["attempts"] >= 1:
                rate = stats["successes"] / stats["attempts"]
                if rate > best_rate:
                    best_rate = rate
                    best = solver
        return best

    def save(self):
        with open(self.path, "w") as f:
            json.dump({
                "experiences": self.experiences,
                "routing_table": self.routing_table,
            }, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# Solver Bank — all strategies the mind knows
# ═══════════════════════════════════════════════════════════════════════════════

def extract_objects(cells, h, w, bg):
    visited = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if (r,c) in visited or cells[r][c] == bg:
                continue
            colour = cells[r][c]
            queue = [(r,c)]
            obj_cells = set()
            while queue:
                cr, cc = queue.pop()
                if (cr,cc) in visited: continue
                if cr<0 or cr>=h or cc<0 or cc>=w: continue
                if cells[cr][cc] != colour: continue
                visited.add((cr,cc))
                obj_cells.add((cr,cc))
                for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    queue.append((cr+dr,cc+dc))
            objects.append({'colour': colour, 'cells': obj_cells, 'area': len(obj_cells)})
    objects.sort(key=lambda o: -o['area'])
    return objects


def try_concentric_nesting(task: ARCTask) -> List[Tuple[str, Grid, bool]]:
    """Try concentric nesting for size-change tasks."""
    results = []
    test = task.test[0].input
    h, w = test.height, test.width
    flat = [test.cells[r][c] for r in range(h) for c in range(w)]
    bg = Counter2(flat).most_common(1)[0][0]
    objects = extract_objects(test.cells, h, w, bg)
    k = len(objects)
    if k < 2:
        return []
    size = 2 * k - 1
    out = [[bg]*size for _ in range(size)]
    for i, obj in enumerate(objects):
        r_min = i
        r_max = size - 1 - i
        for r in range(r_min, r_max+1):
            for c in range(r_min, r_max+1):
                out[r][c] = obj['colour']
    candidate = Grid(out)
    # Verify
    for pair in task.train:
        inp = pair.input
        ih, iw = inp.height, inp.width
        flat2 = [inp.cells[r][c] for r in range(ih) for c in range(iw)]
        bg2 = Counter2(flat2).most_common(1)[0][0]
        objs = extract_objects(inp.cells, ih, iw, bg2)
        k2 = len(objs)
        if k2 < 2:
            return []
        s2 = 2*k2 - 1
        out2 = [[bg2]*s2 for _ in range(s2)]
        for i, obj in enumerate(objs):
            r_min = i
            r_max = s2 - 1 - i
            for r in range(r_min, r_max+1):
                for c in range(r_min, r_max+1):
                    out2[r][c] = obj['colour']
        if Grid(out2).height != pair.output.height or Grid(out2).width != pair.output.width:
            return []
        if Grid(out2).cells != pair.output.cells:
            return []
    results.append(("concentric_nesting", candidate, True))
    return results


def try_all_strategies(task: ARCTask) -> List[Tuple[str, Grid, bool]]:
    """Try all strategies, return (name, result, verified)."""
    results = []

    # Try concentric nesting first (for size-change tasks)
    try:
        results.extend(try_concentric_nesting(task))
    except Exception:
        pass

    # Try consolidated mind strategies
    try:
        interp = cm.interpret(task)
        candidates = cm.generate_all_candidates(task, interp)
        for cand_name, cand_grid in candidates:
            verified = True
            for pair in task.train:
                result = cm.apply_to_train(task, cand_name, pair.input)
                if result is None or not cm.grids_equal(result, pair.output):
                    verified = False
                    break
            if verified:
                results.append((cand_name, cand_grid, True))
    except Exception:
        pass

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Learning Solver — uses experience to prioritise strategies
# ═══════════════════════════════════════════════════════════════════════════════

def solve_with_learning(task: ARCTask, task_id: str, experience: ExperienceStore) -> Tuple[Optional[Grid], str, Dict]:
    """Solve using experience-guided strategy selection."""
    sig = task_signature(task)
    test = task.test[0].input

    # Get best solver from experience
    best_from_exp = experience.best_solver(sig["task_type"])

    # Try all strategies
    verified = try_all_strategies(task)

    if verified:
        # Pick the best verified candidate
        # If we have experience, prefer the solver that worked before
        if best_from_exp:
            for name, grid, _ in verified:
                if best_from_exp in name:
                    experience.record(task_id, sig, name, True)
                    return grid, name, {"solver": name, "from_experience": True, **sig}

        # Otherwise take first verified
        name, grid, _ = verified[0]
        experience.record(task_id, sig, name, True)
        return grid, name, {"solver": name, "from_experience": False, **sig}

    # Nothing worked — record failure for all attempted strategies
    experience.record(task_id, sig, "none", False)
    return None, "none", {"solver": "none", **sig}


# ═══════════════════════════════════════════════════════════════════════════════
# Main: iterative learning
# ═══════════════════════════════════════════════════════════════════════════════

import statistics

def run_learning():
    """Run the learning mind — iterates through tasks, learns from each."""
    print("=" * 70)
    print("ARC LEARNING MIND — Learning Through Experimentation")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    experience = ExperienceStore()
    print(f"Experience loaded: {len(experience.experiences)} past experiences")
    print()

    data_dir = ARC_DIR / "data" / "training"
    tasks = sorted(f for f in os.listdir(data_dir) if f.endswith('.json'))

    solved = []
    results = []
    t0 = time.time()

    for tf in tasks:
        task_id = tf[:-5]
        task = load_task(os.path.join(data_dir, tf))

        grid, solver, metrics = solve_with_learning(task, task_id, experience)

        if grid is not None:
            solved.append(task_id)
            status = "✓"
        else:
            status = "✗"

        results.append({"task_id": task_id, "solved": grid is not None, "solver": solver, **metrics})

        # Print with substrate info
        sig = metrics
        exp_str = " [EXP]" if metrics.get("from_experience") else ""
        print(f"  {task_id}: {status} {solver:35s} type={sig.get('task_type','?'):15s} "
              f"AND={sig.get('and_nrci',0):.4f}{exp_str}")

    elapsed = time.time() - t0

    # Save experience
    experience.save()

    # Summary
    print(f"\n{'='*70}")
    print(f"RESULT: {len(solved)}/{len(tasks)} solved ({100*len(solved)/len(tasks):.1f}%)")
    print(f"Time: {elapsed:.1f}s")
    print(f"{'='*70}")

    # Task type breakdown
    type_counts = Counter(r.get("task_type", "?") for r in results)
    type_solved = Counter(r.get("task_type", "?") for r in results if r["solved"])
    print(f"\nTask types:")
    for ttype, count in type_counts.most_common():
        ns = type_solved.get(ttype, 0)
        print(f"  {ttype:15s}: {ns}/{count} solved")

    # Experience routing table
    print(f"\nExperience routing table:")
    for ttype, solvers in experience.routing_table.items():
        for solver, stats in solvers.items():
            if stats["attempts"] > 0:
                rate = stats["successes"] / stats["attempts"]
                print(f"  {ttype:15s} → {solver:30s}: {stats['successes']}/{stats['attempts']} ({rate:.0%})")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_tasks": len(tasks),
        "n_solved": len(solved),
        "score_pct": round(100*len(solved)/len(tasks), 1),
        "time_s": round(elapsed, 1),
        "solved_tasks": solved,
        "results": results,
        "experience_count": len(experience.experiences),
    }
    out_path = LTM_DIR / "arc_learning_run_001.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved to {out_path}")

    # Update training log
    log_path = LTM_DIR / "training_log.json"
    if log_path.exists():
        with open(log_path) as f:
            log = json.load(f)
    else:
        log = {"runs": []}
    log["runs"].append({
        "iteration": 15,
        "focus": "ARC learning mind (experience accumulation)",
        "n_solved": len(solved),
        "score_pct": round(100*len(solved)/len(tasks), 1),
        "n_experiences": len(experience.experiences),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    return output


if __name__ == "__main__":
    run_learning()
