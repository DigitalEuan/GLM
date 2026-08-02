"""
v055_mog_router.py — MOG-based Task Router using NRCI/TAX/DQI
================================================================

Uses the UBP metrics (NRCI, TAX, DQI) to classify ARC tasks and route
them to the appropriate solver category.

Key finding: ΔNRCI between input and output grids is QUANTIZED — it maps
directly to ΔHW (Hamming Weight change in MOG-encoded 24-bit vectors).

ΔHW = 0:  Recolour/preserve (coherence unchanged)
ΔHW < 0:  Simplification (erase/compress, coherence increases)
ΔHW > 0:  Complexity (fill/expand, coherence decreases)

This gives us a deterministic task classifier that routes to the right
solver category based on the MOG-encoded transformation signature.

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
import sys, os, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# Add UBP core to path
_UBP_CORE = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'core')
if _UBP_CORE not in sys.path:
    sys.path.insert(0, _UBP_CORE)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# MOG ENCODING + UBP METRICS
# ══════════════════════════════════════════════════════════════════════════════

# Lazy-load UBP engines
_G = None
_L = None
_RNRCI = None

def _get_engines():
    global _G, _L, _RNRCI
    if _G is None:
        from ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine
        _G = GolayCodeEngine()
        _L = LeechLatticeEngine(_G)
    if _RNRCI is None:
        try:
            import sys as _sys
            _glm_dir = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'GLM')
            if _glm_dir not in _sys.path:
                _sys.path.insert(0, _glm_dir)
            from refined_nrci import RefinedNRCI
            _RNRCI = RefinedNRCI(golay_engine=_G)
        except ImportError:
            _RNRCI = None
    return _G, _L


def mog_encode(grid: Grid) -> List[int]:
    """Encode a grid as a 24-bit vector via MOG layout.
    
    MOG row = colour mod 4 (layer)
    MOG col = (row + col) mod 6 (spatial block)
    Bit = 1 if any non-zero cell maps to this position
    """
    h, w = grid.height, grid.width
    bits = [0] * 24
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != 0:
                mog_r = grid.cells[r][c] % 4
                mog_c = (r + c) % 6
                bits[mog_r * 6 + mog_c] = 1
    return bits


def mog_encode_signed(grid: Grid) -> List[int]:
    """Encode grid as 24-integer vector via MOG (signed by colour value)."""
    h, w = grid.height, grid.width
    counts = [0] * 24
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != 0:
                mog_r = grid.cells[r][c] % 4
                mog_c = (r + c) % 6
                counts[mog_r * 6 + mog_c] += grid.cells[r][c]
    return counts


def compute_mog_metrics(grid: Grid) -> Dict[str, Any]:
    """Compute MOG-encoded NRCI, TAX, HW for a grid."""
    G, L = _get_engines()
    bits = mog_encode(grid)
    signed = mog_encode_signed(grid)
    snapped, _ = G.snap_to_codeword(bits)
    hw = sum(snapped)
    tax = L.calculate_symmetry_tax(snapped)
    nrci = L.calculate_nrci(snapped)
    
    result = {
        'hw': hw,
        'tax': float(tax),
        'nrci': float(nrci),
        'bits': bits,
        'snapped': signed,
    }
    
    # Add refined NRCI shells if available
    if _RNRCI is not None:
        try:
            shell_desc = _RNRCI.describe(signed)
            result['shells'] = shell_desc
            result['refined_nrci'] = _RNRCI.compute(signed)
        except Exception:
            pass
    
    return result


def compute_dqi(nrci: float) -> float:
    """Compute Design Quality Index."""
    from ubp_unified_v5 import UBPQualityMetrics, F
    return float(UBPQualityMetrics.calculate_dqi(
        Fraction(nrci), Fraction(1), Fraction(1)))


# ══════════════════════════════════════════════════════════════════════════════
# TASK CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskSignature:
    """MOG-based signature of an ARC task."""
    delta_hw: int          # HW change between input and output
    delta_nrci: float      # NRCI change
    in_hw: int             # Input Hamming weight
    out_hw: int            # Output Hamming weight
    in_nrci: float         # Input NRCI
    out_nrci: float        # Output NRCI
    category: str          # Classification
    delta_shell2: float = 0.0   # Sextet-balance change
    delta_shell3: float = 0.0   # Coset-type change
    delta_shell4: float = 0.0   # Sextet-signed change


def classify_task(task: ARCTask) -> TaskSignature:
    """Classify a task based on MOG-encoded metrics."""
    pair = task.train[0]
    
    in_mog = compute_mog_metrics(pair.input)
    out_mog = compute_mog_metrics(pair.output)
    
    delta_hw = out_mog['hw'] - in_mog['hw']
    delta_nrci = out_mog['nrci'] - in_mog['nrci']
    
    # Classify based on ΔHW
    if delta_hw == 0:
        category = "preserve"  # Recolour/spatial-preserving
    elif delta_hw < -6:
        category = "compress"  # Major simplification
    elif delta_hw < 0:
        category = "simplify"  # Moderate simplification
    elif delta_hw > 6:
        category = "expand"    # Major expansion
    elif delta_hw > 0:
        category = "enrich"    # Moderate enrichment
    else:
        category = "unknown"
    
    # Compute shell deltas if available
    delta_shell2 = 0.0
    delta_shell3 = 0.0
    delta_shell4 = 0.0
    if 'shells' in in_mog and 'shells' in out_mog:
        delta_shell2 = out_mog['shells'].get('shell2_sextet_balance', 0) - in_mog['shells'].get('shell2_sextet_balance', 0)
        delta_shell3 = out_mog['shells'].get('shell3_coset_type', 0) - in_mog['shells'].get('shell3_coset_type', 0)
        delta_shell4 = out_mog['shells'].get('shell4_sextet_signed', 0) - in_mog['shells'].get('shell4_sextet_signed', 0)
    
    return TaskSignature(
        delta_hw=delta_hw,
        delta_nrci=delta_nrci,
        in_hw=in_mog['hw'],
        out_hw=out_mog['hw'],
        in_nrci=in_mog['nrci'],
        out_nrci=out_mog['nrci'],
        category=category,
        delta_shell2=delta_shell2,
        delta_shell3=delta_shell3,
        delta_shell4=delta_shell4,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER ROUTING
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Route task to appropriate solver based on MOG classification."""
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None

    sig = classify_task(task)
    
    # ═══ Category: PRESERVE (ΔHW = 0) ═══
    # These are recolour-only or spatial-preserving tasks.
    # Try: unconditional recolour, conditional recolour, local swap
    if sig.category == "preserve":
        # Try recolour map
        cmap = {}
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic != oc:
                        if ic in cmap:
                            if cmap[ic] != oc:
                                cmap[ic] = None
                        else:
                            cmap[ic] = oc
        cmap = {k: v for k, v in cmap.items() if v is not None}
        
        if cmap:
            def make_rc(cm):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c] in cm:
                                cells[r][c] = cm[cells[r][c]]
                    return Grid(cells)
                return fn
            
            fn = make_rc(cmap)
            if _verify(fn, task):
                return _predict(fn, task), f"preserve:recolour({cmap})"
        
        # Try local colour swap
        def local_swap(grid):
            h, w = grid.height, grid.width
            cells = [row[:] for row in grid.cells]
            visited = set()
            for r in range(h):
                for c in range(w):
                    if (r,c) in visited or grid.cells[r][c] == 0:
                        continue
                    comp = set()
                    queue = [(r,c)]
                    while queue:
                        cr, cc = queue.pop()
                        if (cr,cc) in comp:
                            continue
                        comp.add((cr,cc))
                        visited.add((cr,cc))
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = cr+dr, cc+dc
                            if 0<=nr<h and 0<=nc<w and (nr,nc) not in comp and grid.cells[nr][nc]!=0:
                                queue.append((nr,nc))
                    comp_cols = set(grid.cells[rr][cc] for rr,cc in comp)
                    if len(comp_cols) == 2:
                        cols = sorted(comp_cols)
                        for rr, cc in comp:
                            if grid.cells[rr][cc] == cols[0]:
                                cells[rr][cc] = cols[1]
                            elif grid.cells[rr][cc] == cols[1]:
                                cells[rr][cc] = cols[0]
            return Grid(cells)
        
        if _verify(local_swap, task):
            return _predict(local_swap, task), "preserve:local_swap"
    
    # ═══ Category: ENRICH (ΔHW > 0) ═══
    # These add complexity (fill, expand).
    # Try: fill, conditional fill, object extension
    if sig.category in ("enrich", "expand"):
        # Try fill with learned colour
        fills = set()
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fills.add(pair.output.cells[r][c])
        
        if len(fills) == 1:
            fc = fills.pop()
            def make_fill(col):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c] == 0:
                                cells[r][c] = col
                    return Grid(cells)
                return fn
            
            fn = make_fill(fc)
            if _verify(fn, task):
                return _predict(fn, task), f"enrich:fill({fc})"
        
        # Try interior fill
        if len(fills) == 1:
            fc = fills.pop()
            def make_int_fill(col):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    border_connected = set()
                    queue = []
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c] == 0:
                                if r==0 or r==h-1 or c==0 or c==w-1:
                                    queue.append((r,c))
                                    border_connected.add((r,c))
                    while queue:
                        cr, cc = queue.pop()
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = cr+dr, cc+dc
                            if 0<=nr<h and 0<=nc<w and (nr,nc) not in border_connected:
                                if cells[nr][nc]==0:
                                    border_connected.add((nr,nc))
                                    queue.append((nr,nc))
                    changed = False
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c]==0 and (r,c) not in border_connected:
                                cells[r][c] = col
                                changed = True
                    return Grid(cells) if changed else None
                return fn
            
            fn = make_int_fill(fc)
            if _verify(fn, task):
                return _predict(fn, task), f"enrich:interior_fill({fc})"
        
        # Try conditional recolour (object-level)
        prop_obs = defaultdict(lambda: defaultdict(set))
        for pair_idx, pair in enumerate(task.train):
            inp_objs = _extract_objects(pair.input)
            out_objs = _extract_objects(pair.output)
            for in_obj in inp_objs:
                best_out, best_dist = None, float('inf')
                for out_obj in out_objs:
                    dr = in_obj['centroid'][0] - out_obj['centroid'][0]
                    dc = in_obj['centroid'][1] - out_obj['centroid'][1]
                    dist = (dr*dr + dc*dc)**0.5
                    if dist < best_dist:
                        best_dist = dist
                        best_out = out_obj
                if best_out and best_dist < 5.0 and in_obj['colour'] != best_out['colour']:
                    outcome = best_out['colour']
                    for t in range(2, max(o['size'] for o in inp_objs)+1):
                        if in_obj['size'] >= t:
                            prop_obs[('size', '>=', t)][pair_idx].add(outcome)
        
        n_pairs = len(task.train)
        for (prop, op, val), pair_outcomes in prop_obs.items():
            if len(pair_outcomes) != n_pairs:
                continue
            outcomes = set()
            for pi in range(n_pairs):
                po = pair_outcomes.get(pi, set())
                if len(po) != 1:
                    outcomes = set()
                    break
                outcomes.add(next(iter(po)))
            if len(outcomes) != 1:
                continue
            outcome = next(iter(outcomes))
            
            # Check not true for unchanged
            only_rc = True
            for pair in task.train:
                inp_objs = _extract_objects(pair.input)
                out_objs = _extract_objects(pair.output)
                for in_obj in inp_objs:
                    best_out, best_dist = None, float('inf')
                    for out_obj in out_objs:
                        dr = in_obj['centroid'][0] - out_obj['centroid'][0]
                        dc = in_obj['centroid'][1] - out_obj['centroid'][1]
                        dist = (dr*dr + dc*dc)**0.5
                        if dist < best_dist:
                            best_dist = dist
                            best_out = out_obj
                    if best_out and best_dist < 5.0 and in_obj['colour'] == best_out['colour']:
                        if in_obj['size'] >= val:
                            only_rc = False
                            break
                if not only_rc:
                    break
            
            if not only_rc:
                continue
            
            def make_cond(p, o, v, oc):
                def fn(grid):
                    objs = _extract_objects(grid)
                    cells = [row[:] for row in grid.cells]
                    for obj in objs:
                        if obj['size'] >= v:
                            for r, c in obj['cells']:
                                cells[r][c] = oc
                    return Grid(cells)
                return fn
            
            fn = make_cond(prop, op, val, outcome)
            if _verify(fn, task):
                return _predict(fn, task), f"enrich:N(size>={val}→{outcome})"
    
    # ═══ Category: SIMPLIFY (ΔHW < 0) ═══
    # These reduce complexity (erase, compress).
    if sig.category in ("simplify", "compress"):
        # Try erase
        erase_cols = set()
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] != 0 and pair.output.cells[r][c] == 0:
                        erase_cols.add(pair.input.cells[r][c])
        
        for ec in erase_cols:
            def make_erase(col):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c] == col:
                                cells[r][c] = 0
                    return Grid(cells)
                return fn
            
            fn = make_erase(ec)
            if _verify(fn, task):
                return _predict(fn, task), f"simplify:erase({ec})"
    
    return None


def _verify(fn, task: ARCTask) -> bool:
    for pair in task.train:
        pred = fn(pair.input)
        if pred is None or not grids_equal(pred, pair.output):
            return False
    return True


def _predict(fn, task: ARCTask) -> Grid:
    return fn(task.test[0].input)


def _extract_objects(grid: Grid) -> List[Dict]:
    h, w = grid.height, grid.width
    visited = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if (r,c) in visited or grid.cells[r][c] == 0:
                continue
            colour = grid.cells[r][c]
            cells = []
            queue = [(r,c)]
            while queue:
                cr, cc = queue.pop()
                if (cr,cc) in visited:
                    continue
                visited.add((cr,cc))
                cells.append((cr,cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in visited and grid.cells[nr][nc]==colour:
                        queue.append((nr,nc))
            centroid_r = sum(r for r,_ in cells)/len(cells)
            centroid_c = sum(c for _,c in cells)/len(cells)
            objects.append({'cells': cells, 'colour': colour, 'size': len(cells),
                          'centroid': (centroid_r, centroid_c)})
    return objects


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--classify", action="store_true", help="Show classification only")
    args = p.parse_args()

    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))

    if args.classify:
        print(f"{'Task':<12} {'ΔHW':>5} {'ΔNRCI':>10} {'ΔShell2':>8} {'ΔShell3':>8} {'ΔShell4':>8} {'Category':<12}")
        print("-" * 75)
        for fname in files:
            task = load_task(os.path.join(args.batch, fname), name=os.path.splitext(fname)[0])
            sig = classify_task(task)
            tid = os.path.splitext(fname)[0]
            print(f"{tid:<12} {sig.delta_hw:>5} {sig.delta_nrci:>10.4f} {sig.delta_shell2:>+8.3f} {sig.delta_shell3:>+8.3f} {sig.delta_shell4:>+8.3f} {sig.category:<12}")
        sys.exit(0)

    solved = total = 0
    sources = {}
    all_results = []

    print("═" * 60)
    print(" MOG ROUTER v055 — NRCI/TAX/DQI Classification")
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
