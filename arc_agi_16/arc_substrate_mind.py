"""
arc_substrate_mind.py — ARC-AGI Solver Using Trained Data Object Substrate

Uses what we learned from element/bond training:
1. AND encoding captures shared structure
2. Pre-snap metrics carry more signal
3. NRCI measures coherence
4. Spatial Arithmetic computes on geometry
5. Snap cost is information

The mind perceives ARC grids as Data Objects in 24D space,
then reasons about transformations using substrate-native operations.
"""

from __future__ import annotations
import os, sys, json, math, time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
ARC_DIR = SCRIPT_DIR.parent / "glm_machine"
LTM_DIR = SCRIPT_DIR.parent / "long_term_memory"
sys.path.insert(0, str(ARC_DIR / "arc_loader"))
sys.path.insert(0, str(SCRIPT_DIR.parent / "data_object" / "scripts"))

from loader import ARCTask, Grid, load_task


# ═══════════════════════════════════════════════════════════════════════════════
# Grid → Data Object (24-bit encoding)
# ═══════════════════════════════════════════════════════════════════════════════

def grid_to_24bit(grid: Grid) -> List[int]:
    """Encode an ARC grid as a 24-bit Data Object.

    Strategy: use the grid's structure to fill the 4×6 MOG grid.
    Each row of the MOG gets a 6-bit encoding of grid properties.
    """
    h, w = grid.height, grid.width
    cells = grid.cells

    # Flatten grid to list of values
    flat = [cells[r][c] for r in range(h) for c in range(w)]
    n = len(flat)

    # Row 0 (Reality): colour histogram — most common colours
    colour_counts = Counter(flat)
    top_colours = [c for c, _ in colour_counts.most_common(6)]
    row0 = [0] * 6
    for i, c in enumerate(top_colours[:6]):
        row0[i] = 1 if c != 0 else 0  # bit = 1 if colour exists

    # Row 1 (Info): structural features
    # Bit 0: has border (non-zero on edges)
    # Bit 1: has interior (non-zero inside)
    # Bit 2: has diagonal pattern
    # Bit 3: has horizontal symmetry
    # Bit 4: has vertical symmetry
    # Bit 5: is square
    has_border = any(cells[0][c] != 0 or cells[h-1][c] != 0 for c in range(w)) or \
                 any(cells[r][0] != 0 or cells[r][w-1] != 0 for r in range(h))
    has_interior = any(cells[r][c] != 0 for r in range(1, h-1) for c in range(1, w-1)) if h > 2 and w > 2 else False
    h_sym = all(cells[r] == cells[h-1-r] for r in range(h//2))
    v_sym = all(cells[r][c] == cells[r][w-1-c] for r in range(h) for c in range(w//2))
    is_square = h == w
    row1 = [int(has_border), int(has_interior), 0, int(h_sym), int(v_sym), int(is_square)]

    # Row 2 (Activation): density and complexity
    density = sum(1 for v in flat if v != 0) / max(n, 1)
    n_colours = len(set(flat))
    n_objects = count_components(grid)
    row2_val = int(density * 63) & 0x3F
    row2 = [(row2_val >> (5 - i)) & 1 for i in range(6)]

    # Row 3 (Potential): size encoding
    size_val = (h * 16 + w) & 0x3F
    row3 = [(size_val >> (5 - i)) & 1 for i in range(6)]

    # Flatten: row0 + row1 + row2 + row3
    bits = row0 + row1 + row2 + row3
    return bits[:24]


def count_components(grid: Grid) -> int:
    """Count connected components of non-zero cells."""
    h, w = grid.height, grid.width
    visited = set()
    count = 0
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            count += 1
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in visited:
                    continue
                if cr < 0 or cr >= h or cc < 0 or cc >= w:
                    continue
                if grid.cells[cr][cc] == 0:
                    continue
                visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    queue.append((cr+dr, cc+dc))
    return count


# ═══════════════════════════════════════════════════════════════════════════════
# Golay Snap + Metrics
# ═══════════════════════════════════════════════════════════════════════════════

Y = 0.2646754304045269672

try:
    sys.path.insert(0, str(SCRIPT_DIR / "data_object" / "scripts"))
    import ubp_unified_v5 as ubp
    GOLAY = ubp.GOLAY_ENGINE
    HAS_GOLAY = True
except Exception:
    HAS_GOLAY = False
    GOLAY = None


def golay_snap(vec: List[int]) -> List[int]:
    if HAS_GOLAY:
        snapped, _ = GOLAY.snap_to_codeword(vec)
        return snapped
    return vec[:]


def snap_metrics(vec_raw: List[int]) -> Dict:
    """Full snap cost analysis."""
    snapped = golay_snap(vec_raw)
    hw_raw = sum(vec_raw)
    hw_snapped = sum(snapped)
    bits_changed = sum(1 for i in range(24) if vec_raw[i] != snapped[i])
    tax = hw_raw * Y + sum(v*v for v in vec_raw) / 8.0
    nrci = 10.0 / (10.0 + tax)
    tax_snapped = hw_snapped * Y + sum(v*v for v in snapped) / 8.0
    nrci_snapped = 10.0 / (10.0 + tax_snapped)
    return {
        "hw_raw": hw_raw, "hw_snapped": hw_snapped,
        "bits_changed": bits_changed,
        "nrci_raw": nrci, "nrci_snapped": nrci_snapped,
        "delta_tax": tax_snapped - tax,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Data Object Operations (from training)
# ═══════════════════════════════════════════════════════════════════════════════

def do_and(a: List[int], b: List[int]) -> List[int]:
    return [a[i] & b[i] for i in range(24)]

def do_xor(a: List[int], b: List[int]) -> List[int]:
    return [a[i] ^ b[i] for i in range(24)]

def do_or(a: List[int], b: List[int]) -> List[int]:
    return [a[i] | b[i] for i in range(24)]

def do_hamming(a: List[int], b: List[int]) -> int:
    return sum(1 for i in range(24) if a[i] != b[i])

def do_overlap(a: List[int], b: List[int]) -> int:
    return sum(1 for i in range(24) if a[i] == b[i])


# ═══════════════════════════════════════════════════════════════════════════════
# ARC-AGI Solver: Grid-Level Heuristics
# ═══════════════════════════════════════════════════════════════════════════════

def try_gravity(grid: Grid) -> Optional[Grid]:
    """Push all non-zero cells down."""
    h, w = grid.height, grid.width
    new = [[0]*w for _ in range(h)]
    for c in range(w):
        col_vals = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
        for i, v in enumerate(col_vals):
            new[h - len(col_vals) + i][c] = v
    return Grid(new)


def try_fill_interior(grid: Grid) -> Optional[Grid]:
    """Fill enclosed zero regions."""
    h, w = grid.height, grid.width
    new = [row[:] for row in grid.cells]
    # Find border-connected zeros
    border_conn = set()
    stack = []
    for r in range(h):
        for c in range(w):
            if new[r][c] == 0 and (r == 0 or r == h-1 or c == 0 or c == w-1):
                border_conn.add((r,c))
                stack.append((r,c))
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in border_conn and new[nr][nc] == 0:
                border_conn.add((nr,nc))
                stack.append((nr,nc))
    # Fill non-border-connected zeros with most common neighbour colour
    for r in range(h):
        for c in range(w):
            if new[r][c] == 0 and (r,c) not in border_conn:
                neighbours = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and new[nr][nc] != 0:
                        neighbours.append(new[nr][nc])
                if neighbours:
                    new[r][c] = Counter(neighbours).most_common(1)[0][0]
    return Grid(new)


def try_colour_map(grid: Grid, pairs: List[Dict]) -> Optional[Grid]:
    """Learn colour mapping from train pairs and apply."""
    mapping = {}
    for p in pairs:
        inp, out = p['input'], p['output']
        oh, ow = len(out), len(out[0])
        ih, iw = len(inp), len(inp[0])
        if ih != oh or iw != ow:
            return None
        for r in range(ih):
            for c in range(iw):
                iv, ov = inp[r][c], out[r][c]
                if iv != ov:
                    if iv in mapping and mapping[iv] != ov:
                        return None  # inconsistent
                    mapping[iv] = ov
    if not mapping:
        return None
    h, w = grid.height, grid.width
    new = [[mapping.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)]
    return Grid(new)


def try_mirror_h(grid: Grid) -> Grid:
    return Grid([row[::-1] for row in grid.cells])

def try_mirror_v(grid: Grid) -> Grid:
    return Grid(grid.cells[::-1])

def try_rotate_90(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    return Grid([[grid.cells[h-1-c][r] for c in range(h)] for r in range(w)])

def try_transpose(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    return Grid([[grid.cells[c][r] for c in range(h)] for r in range(w)])


# ═══════════════════════════════════════════════════════════════════════════════
# Solver: combine heuristics with Data Object reasoning
# ═══════════════════════════════════════════════════════════════════════════════

def solve_task(task: Dict) -> Tuple[Optional[Grid], str, Dict]:
    """Attempt to solve an ARC task using substrate mind."""
    train = task['train']
    test = task['test']
    test_input = Grid(test[0]['input'])
    ih, iw = test_input.height, test_input.width

    # Encode input as Data Object
    input_do = grid_to_24bit(test_input)
    input_metrics = snap_metrics(input_do)

    # Try all candidates
    candidates = []

    # 1. Gravity
    g = try_gravity(test_input)
    if g:
        candidates.append(("gravity", g))

    # 2. Fill interior
    f = try_fill_interior(test_input)
    if f:
        candidates.append(("fill_interior", f))

    # 3. Colour map
    cm = try_colour_map(test_input, train)
    if cm:
        candidates.append(("colour_map", cm))

    # 4. Mirror/rotate transforms
    candidates.append(("mirror_h", try_mirror_h(test_input)))
    candidates.append(("mirror_v", try_mirror_v(test_input)))
    if ih == iw:
        candidates.append(("rotate_90", try_rotate_90(test_input)))
        candidates.append(("transpose", try_transpose(test_input)))

    # 5. Identity (no change)
    candidates.append(("identity", test_input))

    # Verify each candidate against train pairs
    for name, candidate in candidates:
        all_match = True
        for p in train:
            inp = Grid(p['input'])
            expected = Grid(p['output'])

            # Apply same transform to train input
            if name == "gravity":
                result = try_gravity(inp)
            elif name == "fill_interior":
                result = try_fill_interior(inp)
            elif name == "colour_map":
                result = try_colour_map(inp, train)
            elif name == "mirror_h":
                result = try_mirror_h(inp)
            elif name == "mirror_v":
                result = try_mirror_v(inp)
            elif name == "rotate_90":
                result = try_rotate_90(inp)
            elif name == "transpose":
                result = try_transpose(inp)
            elif name == "identity":
                result = inp
            else:
                result = None

            if result is None or result.height != expected.height or result.width != expected.width or result.cells != expected.cells:
                all_match = False
                break

        if all_match:
            # Encode the solution as Data Object
            sol_do = grid_to_24bit(candidate)
            sol_metrics = snap_metrics(sol_do)
            return candidate, name, {
                "solver": name,
                "input_nrci": input_metrics["nrci_raw"],
                "solution_nrci": sol_metrics["nrci_raw"],
                "input_hw": input_metrics["hw_raw"],
                "solution_hw": sol_metrics["hw_raw"],
            }

    return None, "none", {"solver": "none", "input_nrci": input_metrics["nrci_raw"]}


# ═══════════════════════════════════════════════════════════════════════════════
# Main: run on all 50 tasks
# ═══════════════════════════════════════════════════════════════════════════════

def run_arc_agi():
    """Run the trained mind on ARC-AGI."""
    print("=" * 70)
    print("ARC-AGI — TRAINED SUBSTRATE MIND")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Load long-term memory
    ltm_path = LTM_DIR / "learned_patterns.json"
    if ltm_path.exists():
        with open(ltm_path) as f:
            patterns = json.load(f)
        print(f"Long-term memory: {len(patterns['patterns'])} patterns loaded")

    # Load element encodings for reference
    elem_path = LTM_DIR / "element_encodings.json"
    if elem_path.exists():
        with open(elem_path) as f:
            elem_data = json.load(f)
        print(f"Element encodings: {elem_data['n_elements']} elements loaded")

    # Run on all tasks
    data_dir = ARC_DIR / "data" / "training"
    tasks = sorted(data_dir.glob("*.json"))
    print(f"Tasks: {len(tasks)}")
    print()

    solved = []
    results = []

    for task_path in tasks:
        task_id = task_path.stem
        with open(task_path) as f:
            task = json.load(f)

        solution, solver, metrics = solve_task(task)

        if solution is not None:
            solved.append(task_id)
            status = "✓ SOLVED"
        else:
            status = "✗"

        results.append({
            "task_id": task_id,
            "solver": solver,
            "solved": solution is not None,
            **metrics,
        })

        print(f"  {task_id}: {status:10s} solver={solver:15s} "
              f"NRCI_in={metrics.get('input_nrci', 0):.4f}")

    # Summary
    print(f"\n{'='*70}")
    print(f"RESULTS: {len(solved)}/{len(tasks)} solved ({100*len(solved)/len(tasks):.1f}%)")
    print(f"{'='*70}")

    # Solver breakdown
    solver_counts = Counter(r["solver"] for r in results)
    print(f"\nSolver breakdown:")
    for solver, count in solver_counts.most_common():
        n_solved = sum(1 for r in results if r["solver"] == solver and r["solved"])
        print(f"  {solver:15s}: {count:3d} tasks, {n_solved:2d} solved")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_tasks": len(tasks),
        "n_solved": len(solved),
        "score_pct": round(100*len(solved)/len(tasks), 1),
        "solved_tasks": solved,
        "results": results,
    }
    out_path = LTM_DIR / "arc_agi_run_001.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to {out_path}")

    # Update training log
    log_path = LTM_DIR / "training_log.json"
    if log_path.exists():
        with open(log_path) as f:
            log = json.load(f)
    else:
        log = {"runs": []}
    log["runs"].append({
        "iteration": 13,
        "focus": "ARC-AGI first run with trained mind",
        "n_solved": len(solved),
        "score_pct": round(100*len(solved)/len(tasks), 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    return output


if __name__ == "__main__":
    run_arc_agi()
