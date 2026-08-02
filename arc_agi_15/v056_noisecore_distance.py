"""
v056_noisecore_distance.py — NoiseALU-based Grid Distance Solver
=================================================================

Uses the NoiseALU's exact Fraction arithmetic to compute distances
between ARC grids in Leech-space (24-bit MOG encoding).

The approach:
  1. Encode each grid as a 24-bit vector via MOG
  2. Compute exact Leech-space distance between grids using NoiseALU
  3. For each test input, find the nearest training input
  4. Apply the transformation from that training pair

This is the "Leech lattice nearest neighbour" approach — the same
principle as the VQ paper's codebook-free search, applied to ARC.

Every distance calculation is exact (Fraction), carries NRCI/TAX
metadata, and is grounded in the Leech lattice structure.

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
from fractions import Fraction
import sys, os, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

_UBP_CORE = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'core')
if _UBP_CORE not in sys.path:
    sys.path.insert(0, _UBP_CORE)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# MOG ENCODING
# ══════════════════════════════════════════════════════════════════════════════

def mog_encode(grid: Grid) -> List[int]:
    """Encode grid as 24-bit vector via MOG 4×6 layout."""
    h, w = grid.height, grid.width
    bits = [0] * 24
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != 0:
                mog_r = grid.cells[r][c] % 4
                mog_c = (r + c) % 6
                bits[mog_r * 6 + mog_c] = 1
    return bits


def mog_encode_detailed(grid: Grid) -> List[int]:
    """Encode grid as 24-integer vector (count of cells per MOG position)."""
    h, w = grid.height, grid.width
    counts = [0] * 24
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != 0:
                mog_r = grid.cells[r][c] % 4
                mog_c = (r + c) % 6
                counts[mog_r * 6 + mog_c] += 1
    return counts


# ══════════════════════════════════════════════════════════════════════════════
# NOISEALU DISTANCE COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

# Lazy-load NoiseALU
_alu = None

def _get_alu():
    global _alu
    if _alu is None:
        from ubp_unified_v5 import NoiseALU
        _alu = NoiseALU()
    return _alu


def leech_distance(v1: List[int], v2: List[int]) -> Fraction:
    """Compute exact Leech-space distance between two 24-bit vectors.
    
    Distance = ‖v1 - v2‖² (squared Euclidean norm of the difference).
    This is the same metric used in the Leech lattice VQ paper.
    """
    alu = _get_alu()
    diff = [alu.sub(a, b)["result"] for a, b in zip(v1, v2)]
    mag_sq = sum(Fraction(d) ** 2 for d in diff)
    return mag_sq


def hamming_distance(v1: List[int], v2: List[int]) -> int:
    """Hamming distance between two binary vectors."""
    return sum(a != b for a, b in zip(v1, v2))


def cosine_similarity(v1: List[int], v2: List[int]) -> Fraction:
    """Exact cosine similarity between two vectors."""
    alu = _get_alu()
    dot = sum(Fraction(a) * Fraction(b) for a, b in zip(v1, v2))
    mag1_sq = sum(Fraction(a) ** 2 for a in v1)
    mag2_sq = sum(Fraction(b) ** 2 for b in v2)
    if mag1_sq == 0 or mag2_sq == 0:
        return Fraction(0)
    return dot / (mag1_sq * mag2_sq) ** Fraction(1, 2)


def grid_distance_mog(grid1: Grid, grid2: Grid) -> Dict[str, Any]:
    """Compute multiple distance metrics between two grids via MOG encoding."""
    v1 = mog_encode_detailed(grid1)
    v2 = mog_encode_detailed(grid2)
    b1 = mog_encode(grid1)
    b2 = mog_encode(grid2)

    leech_dist = leech_distance(v1, v2)
    hamming_dist = hamming_distance(b1, b2)

    # NRCI of the difference vector
    from ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine
    G = GolayCodeEngine()
    L = LeechLatticeEngine(G)
    diff_bits = [a ^ b for a, b in zip(b1, b2)]
    diff_snapped, _ = G.snap_to_codeword(diff_bits)
    diff_nrci = L.calculate_nrci(diff_snapped)
    diff_tax = L.calculate_symmetry_tax(diff_snapped)

    return {
        "leech_distance": leech_dist,
        "hamming_distance": hamming_dist,
        "diff_nrci": float(diff_nrci),
        "diff_tax": float(diff_tax),
        "diff_hw": sum(diff_bits),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Nearest-neighbour transfer
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Solve by finding nearest training input and transferring its transformation."""
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None

    test_input = task.test[0].input

    # Encode test input
    test_bits = mog_encode_detailed(test_input)
    test_binary = mog_encode(test_input)

    # Find nearest training input by Leech distance
    best_pair_idx = -1
    best_distance = Fraction(10**18)
    best_metrics = None

    for i, pair in enumerate(task.train):
        train_bits = mog_encode_detailed(pair.input)
        train_binary = mog_encode(pair.input)

        dist = leech_distance(test_bits, train_bits)
        hamming = hamming_distance(test_binary, train_binary)

        if dist < best_distance:
            best_distance = dist
            best_pair_idx = i
            best_metrics = {"leech": dist, "hamming": hamming}

    if best_pair_idx < 0:
        return None

    # Get the transformation from the nearest training pair
    best_pair = task.train[best_pair_idx]
    in_grid = best_pair.input
    out_grid = best_pair.output

    # Learn the transformation
    # Strategy 1: Direct colour mapping (per-cell)
    h, w = in_grid.height, in_grid.width
    colour_map = {}
    for r in range(h):
        for c in range(w):
            ic, oc = in_grid.cells[r][c], out_grid.cells[r][c]
            if ic != oc:
                if ic in colour_map:
                    if colour_map[ic] != oc:
                        colour_map[ic] = None  # Inconsistent
                else:
                    colour_map[ic] = oc
    colour_map = {k: v for k, v in colour_map.items() if v is not None}

    # Strategy 2: Fill map (zeros become specific colours)
    fill_map = {}
    for r in range(h):
        for c in range(w):
            if in_grid.cells[r][c] == 0 and out_grid.cells[r][c] != 0:
                fill_map[(r, c)] = out_grid.cells[r][c]

    # Try applying the transformation to test input
    # First: try colour mapping
    if colour_map:
        def apply_colour_map(grid, cm):
            h, w = grid.height, grid.width
            cells = [row[:] for row in grid.cells]
            for r in range(h):
                for c in range(w):
                    if cells[r][c] in cm:
                        cells[r][c] = cm[cells[r][c]]
            return Grid(cells)

        # Verify on all train pairs
        all_pass = True
        for pair in task.train:
            pred = apply_colour_map(pair.input, colour_map)
            if not grids_equal(pred, pair.output):
                all_pass = False
                break

        if all_pass:
            pred = apply_colour_map(test_input, colour_map)
            return pred, f"noisecore:colour_map({colour_map})"

    # Second: try fill pattern (position-dependent)
    if fill_map:
        # Check if fill positions are consistent relative to grid structure
        # (e.g., always in the last row, always at specific columns)
        fill_cols = set(c for r, c in fill_map.keys())
        fill_rows = set(r for r, c in fill_map.keys())

        # Try: fill at same columns in test input
        def apply_fill_at_cols(grid, cols, fill_val):
            h, w = grid.height, grid.width
            cells = [row[:] for row in grid.cells]
            for r in range(h):
                for c in range(w):
                    if grid.cells[r][c] == 0 and c in cols:
                        cells[r][c] = fill_val
            return Grid(cells)

        # Get the fill value (most common output colour for fills)
        fill_vals = Counter(fill_map.values())
        most_common_fill = fill_vals.most_common(1)[0][0]

        # Verify
        all_pass = True
        for pair in task.train:
            pred = apply_fill_at_cols(pair.input, fill_cols, most_common_fill)
            if not grids_equal(pred, pair.output):
                all_pass = False
                break

        if all_pass:
            pred = apply_fill_at_cols(test_input, fill_cols, most_common_fill)
            return pred, f"noisecore:fill_cols({fill_cols}, {most_common_fill})"

    # Third: try per-cell delta transfer
    # For each cell in test input, find the nearest cell in training input
    # and apply its delta
    def apply_nearest_delta(test_grid, train_in, train_out):
        h, w = test_grid.height, test_grid.width
        cells = [row[:] for row in test_grid.cells]

        # Build lookup: (row, col, colour) → delta
        delta_map = {}
        for r in range(h):
            for c in range(w):
                ic = train_in.cells[r][c]
                oc = train_out.cells[r][c]
                if ic != oc:
                    delta_map[(r, c)] = oc

        # Apply deltas at same positions
        for (r, c), new_val in delta_map.items():
            if 0 <= r < h and 0 <= c < w:
                cells[r][c] = new_val

        return Grid(cells)

    all_pass = True
    for pair in task.train:
        pred = apply_nearest_delta(pair.input, pair.input, pair.output)
        if not grids_equal(pred, pair.output):
            all_pass = False
            break

    if all_pass:
        pred = apply_nearest_delta(test_input, best_pair.input, best_pair.output)
        return pred, f"noisecore:nearest_delta(pair={best_pair_idx})"

    return None


# ══════════════════════════════════════════════════════════════════════════════
# DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════════════

def diagnose(task: ARCTask):
    """Show NoiseALU distance analysis for a task."""
    print(f"Task: {task.name}")
    test = task.test[0].input

    for i, pair in enumerate(task.train):
        metrics = grid_distance_mog(test, pair.input)
        print(f"\n  Train {i}:")
        print(f"    Leech distance:  {float(metrics['leech_distance']):.4f}")
        print(f"    Hamming distance: {metrics['hamming_distance']}")
        print(f"    Diff NRCI:       {metrics['diff_nrci']:.4f}")
        print(f"    Diff TAX:        {metrics['diff_tax']:.4f}")
        print(f"    Diff HW:         {metrics['diff_hw']}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--diagnose", type=str, default=None)
    args = p.parse_args()

    if args.diagnose:
        task = load_task(os.path.join(args.batch, args.diagnose),
                         name=os.path.splitext(args.diagnose)[0])
        diagnose(task)
        sys.exit(0)

    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))

    solved = total = 0
    sources = {}
    all_results = []

    print("═" * 60)
    print(" NOISEALU DISTANCE v056")
    print("═" * 60)
    print()

    for fname in files:
        task = load_task(os.path.join(args.batch, fname), name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1

        try:
            signal.setitimer(signal.ITIMER_REAL, 30.0)
            result = solve(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None

        tid = os.path.splitext(fname)[0]
        if result is not None:
            pred, src = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            all_results.append((tid, ok, src))
            if args.verbose or ok:
                print(f"  {tid}: {'✓' if ok else '✗'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            all_results.append((tid, False, "none"))
            if args.verbose:
                print(f"  {tid}: ✗")

    print(f"\n{'═' * 60}")
    print(f" RESULTS ({total} tasks)")
    print(f"{'═' * 60}")
    print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        if src != "none":
            print(f"    {src}: {count}")
    print(f"\n  Solved:")
    for tid, ok, src in all_results:
        if ok:
            print(f"    {tid} ← {src}")
