"""
v040_conditional_recolour.py — MOG-Encoded Conditional Recolour
================================================================

The missing primitive: a recolour operation that uses MOG-encoded
per-cell context to determine which cells change.

Physical operations (gravity, rotate, flip) work because they're
deterministic spatial transforms. Informational metrics (Minkowski,
Totient, Cayley-Menger) provide features but need a physical
operation to act through. THIS is that bridge.

Architecture:
1. Per-cell MOG encoding: each cell gets a 24-bit address encoding:
   - Mirrors (bits 0-5): colour fingerprint + neighbourhood colours
   - Information (bits 6-11): position topology (row/col parity, border)
   - Activation (bits 12-17): neighbourhood structure (counts, signatures)
   - Potential (bits 18-23): relational fingerprint (distance to objects)

2. Rule discovery: for each cell that changes, record its MOG address.
   Search for bit-patterns that separate changed from unchanged cells.

3. Rule application: apply discovered patterns to test input.

Key insight: the MOG address encodes BOTH the cell's identity (colour)
AND its spatial context (position, neighbourhood) in a single24-bit
vector. Conditional rules operate on this unified representation.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
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
# 1. PER-CELL MOG ENCODING
# ═══════════════════════════════════════════════════════════════════

def encode_cell_mog(grid: Grid, r: int, c: int) -> int:
    """
    Encode a single cell into a 24-bit MOG address.
    
    Mirrors (bits 0-5): colour fingerprint
      - bits 0-3: cell colour (0-9, 4 bits)
      - bits 4-5: dominant neighbour colour (top 2 bits)
    
    Information (bits 6-11): position topology
      - bit 6: row parity (r % 2)
      - bit 7: col parity (c % 2)
      - bit 8: is border (r==0 or r==h-1 or c==0 or c==w-1)
      - bit 9: is corner
      - bits 10-11: quadrant (which quarter of grid)
    
    Activation (bits 12-17): neighbourhood structure
      - bits 12-14: count of non-zero 4-connected neighbours (0-4, 3 bits)
      - bits 15-17: count of distinct neighbour colours (0-4, 3 bits)
    
    Potential (bits 18-23): relational fingerprint
      - bits 18-20: Manhattan distance to nearest non-bg cell (0-7, 3 bits)
      - bits 21-23: neighbour colour signature (hash of sorted neighbour cols)
    """
    h, w = grid.height, grid.width
    colour = grid.cells[r][c]
    
    # Mirrors: colour fingerprint
    # 4 bits for cell colour, 2 bits for dominant neighbour
    n4_cols = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < h and 0 <= nc < w:
            n4_cols.append(grid.cells[nr][nc])
    
    # Dominant neighbour colour (most common non-zero)
    non_zero_neighbours = [x for x in n4_cols if x > 0]
    dom_neighbour = Counter(non_zero_neighbours).most_common(1)[0][0] if non_zero_neighbours else 0
    
    mirrors = (colour & 0xF) | ((dom_neighbour & 0x3) << 4)
    
    # Information: position topology
    is_border = (r == 0 or r == h-1 or c == 0 or c == w-1)
    is_corner = (r in (0, h-1) and c in (0, w-1))
    
    # Quadrant: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
    quad_r = 0 if r < h//2 else 1
    quad_c = 0 if c < w//2 else 1
    quadrant = quad_r * 2 + quad_c
    
    information = ((r % 2) << 0) | ((c % 2) << 1) | (int(is_border) << 2) | (int(is_corner) << 3) | (quadrant << 4)
    
    # Activation: neighbourhood structure
    n_nonzero = sum(1 for x in n4_cols if x > 0)
    n_distinct = len(set(n4_cols))
    
    activation = (n_nonzero << 0) | (n_distinct << 3)
    
    # Potential: relational fingerprint
    # Distance to nearest non-bg cell (capped at 7)
    non_bg_positions = []
    for nr in range(h):
        for nc in range(w):
            if grid.cells[nr][nc] != 0:
                non_bg_positions.append((nr, nc))
    
    if non_bg_positions:
        min_dist = min(abs(r-nr) + abs(c-nc) for nr, nc in non_bg_positions)
    else:
        min_dist = 7
    min_dist = min(min_dist, 7)
    
    # Neighbour colour signature (hash of sorted unique colours)
    n_sig = hash(tuple(sorted(set(n4_cols)))) % 8
    
    potential = (min_dist << 0) | (n_sig << 3)
    
    # Combine: mirrors(6) | information(6) | activation(6) | potential(6)
    address = mirrors | (information << 6) | (activation << 12) | (potential << 18)
    
    return address


def encode_grid_mog(grid: Grid) -> np.ndarray:
    """Encode all cells in a grid to MOG addresses."""
    h, w = grid.height, grid.width
    addresses = np.zeros((h, w), dtype=np.int32)
    
    for r in range(h):
        for c in range(w):
            addresses[r, c] = encode_cell_mog(grid, r, c)
    
    return addresses


# ═══════════════════════════════════════════════════════════════════
# 2. MOG-BASED RULE DISCOVERY
# ═══════════════════════════════════════════════════════════════════

def discover_mog_rules(train_pairs: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """
    Discover conditional recolour rules based on MOG addresses.
    
    For each cell that changes, record its MOG address.
    Search for bit-patterns that separate changed from unchanged cells.
    """
    # Collect MOG addresses for changed vs unchanged cells
    changed_addresses = []
    unchanged_addresses = []
    changed_outputs = {}  # address → output colour
    
    for inp, out in train_pairs:
        if inp.height != out.height or inp.width != out.width:
            return None
        
        mog = encode_grid_mog(inp)
        h, w = inp.height, inp.width
        
        for r in range(h):
            for c in range(w):
                addr = mog[r, c]
                ic, oc = inp.cells[r][c], out.cells[r][c]
                
                if ic != oc:
                    changed_addresses.append(addr)
                    if addr not in changed_outputs:
                        changed_outputs[addr] = oc
                    elif changed_outputs[addr] != oc:
                        # Inconsistent — same address, different output
                        changed_outputs[addr] = None
                else:
                    unchanged_addresses.append(addr)
    
    if not changed_addresses:
        return None
    
    # Find address values that appear ONLY in changed cells
    changed_set = set(changed_addresses)
    unchanged_set = set(unchanged_addresses)
    
    unique_to_changed = changed_set - unchanged_set
    
    if unique_to_changed:
        # Check if outputs are consistent
        consistent_rules = {}
        for addr in unique_to_changed:
            if addr in changed_outputs and changed_outputs[addr] is not None:
                consistent_rules[addr] = changed_outputs[addr]
        
        if consistent_rules:
            # Verify on all train pairs
            all_pass = True
            for inp, out in train_pairs:
                mog = encode_grid_mog(inp)
                h, w = inp.height, inp.width
                cells = [row[:] for row in inp.cells]
                
                for r in range(h):
                    for c in range(w):
                        addr = mog[r, c]
                        if addr in consistent_rules:
                            cells[r][c] = consistent_rules[addr]
                
                if not grids_equal(Grid(cells), out):
                    all_pass = False
                    break
            
            if all_pass:
                return {
                    'type': 'exact_address',
                    'rules': consistent_rules,
                }
    
    # Try bit-mask patterns: find a bitmask + mask_value that separates changed from unchanged
    # For each bit position, check if that bit alone separates
    for bit in range(24):
        bit_mask = 1 << bit
        
        changed_bits = set(addr & bit_mask for addr in changed_addresses)
        unchanged_bits = set(addr & bit_mask for addr in unchanged_addresses)
        
        # If all changed cells have bit=1 and all unchanged have bit=0 (or vice versa)
        if changed_bits == {bit_mask} and unchanged_bits == {0}:
            # All changed cells have this bit set
            # What output do they get?
            outputs = set(changed_outputs.get(addr) for addr in changed_addresses if addr & bit_mask)
            outputs.discard(None)
            
            if len(outputs) == 1:
                fill = list(outputs)[0]
                
                # Verify
                all_pass = True
                for inp, out in train_pairs:
                    mog = encode_grid_mog(inp)
                    h, w = inp.height, inp.width
                    cells = [row[:] for row in inp.cells]
                    
                    for r in range(h):
                        for c in range(w):
                            if mog[r, c] & bit_mask:
                                cells[r][c] = fill
                    
                    if not grids_equal(Grid(cells), out):
                        all_pass = False
                        break
                
                if all_pass:
                    return {
                        'type': 'bit_mask',
                        'mask': bit_mask,
                        'value': bit_mask,
                        'fill': fill,
                    }
        
        elif changed_bits == {0} and unchanged_bits == {bit_mask}:
            # All changed cells have this bit unset
            outputs = set(changed_outputs.get(addr) for addr in changed_addresses if not (addr & bit_mask))
            outputs.discard(None)
            
            if len(outputs) == 1:
                fill = list(outputs)[0]
                
                all_pass = True
                for inp, out in train_pairs:
                    mog = encode_grid_mog(inp)
                    h, w = inp.height, inp.width
                    cells = [row[:] for row in inp.cells]
                    
                    for r in range(h):
                        for c in range(w):
                            if not (mog[r, c] & bit_mask):
                                cells[r][c] = fill
                    
                    if not grids_equal(Grid(cells), out):
                        all_pass = False
                        break
                
                if all_pass:
                    return {
                        'type': 'bit_mask',
                        'mask': bit_mask,
                        'value': 0,
                        'fill': fill,
                    }
    
    # Try MOG quadrant-specific rules
    # Check each quadrant separately
    for quadrant_bits in [(0, 5), (6, 11), (12, 17), (18, 23)]:
        lo, hi = quadrant_bits
        mask = ((1 << (hi - lo + 1)) - 1) << lo
        
        changed_quad = set((addr >> lo) & ((1 << (hi - lo + 1)) - 1) for addr in changed_addresses)
        unchanged_quad = set((addr >> lo) & ((1 << (hi - lo + 1)) - 1) for addr in unchanged_addresses)
        
        unique_quad = changed_quad - unchanged_quad
        
        if unique_quad and len(unique_quad) <= 5:
            # Find consistent output for these quadrant values
            outputs = set()
            for addr in changed_addresses:
                quad_val = (addr >> lo) & ((1 << (hi - lo + 1)) - 1)
                if quad_val in unique_quad:
                    out = changed_outputs.get(addr)
                    if out is not None:
                        outputs.add(out)
            
            if len(outputs) == 1:
                fill = list(outputs)[0]
                
                all_pass = True
                for inp, out in train_pairs:
                    mog = encode_grid_mog(inp)
                    h, w = inp.height, inp.width
                    cells = [row[:] for row in inp.cells]
                    
                    for r in range(h):
                        for c in range(w):
                            quad_val = (mog[r, c] >> lo) & ((1 << (hi - lo + 1)) - 1)
                            if quad_val in unique_quad:
                                cells[r][c] = fill
                    
                    if not grids_equal(Grid(cells), out):
                        all_pass = False
                        break
                
                if all_pass:
                    return {
                        'type': 'quadrant',
                        'quadrant': (lo, hi),
                        'values': unique_quad,
                        'fill': fill,
                    }
    
    # Try composite rules: colour X AND MOG quadrant Y → Z
    for inp, out in train_pairs:
        mog = encode_grid_mog(inp)
        h, w = inp.height, inp.width
        
        # Build rules: (colour, quadrant_value) → output
        colour_quad_rules = {}
        for r in range(h):
            for c in range(w):
                ic, oc = inp.cells[r][c], out.cells[r][c]
                if ic != oc:
                    for quadrant_bits in [(0, 5), (6, 11), (12, 17), (18, 23)]:
                        lo, hi = quadrant_bits
                        quad_val = (mog[r, c] >> lo) & ((1 << (hi - lo + 1)) - 1)
                        key = (ic, quadrant_bits, quad_val)
                        if key in colour_quad_rules:
                            if colour_quad_rules[key] != oc:
                                colour_quad_rules[key] = None
                        else:
                            colour_quad_rules[key] = oc
        
        # Filter consistent rules
        consistent = {k: v for k, v in colour_quad_rules.items() if v is not None}
        
        if consistent:
            # Verify on all train pairs
            all_pass = True
            for inp2, out2 in train_pairs:
                mog2 = encode_grid_mog(inp2)
                h2, w2 = inp2.height, inp2.width
                cells = [row[:] for row in inp2.cells]
                
                for r in range(h2):
                    for c in range(w2):
                        ic = inp2.cells[r][c]
                        for (col, (lo, hi), qval), oc in consistent.items():
                            if ic == col:
                                quad_val = (mog2[r, c] >> lo) & ((1 << (hi - lo + 1)) - 1)
                                if quad_val == qval:
                                    cells[r][c] = oc
                                    break
                
                if not grids_equal(Grid(cells), out2):
                    all_pass = False
                    break
            
            if all_pass:
                return {
                    'type': 'colour_quadrant',
                    'rules': consistent,
                }
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 3. RULE APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_mog_rule(rule: Dict, grid: Grid) -> Grid:
    """Apply a MOG-based conditional recolour rule."""
    h, w = grid.height, grid.width
    mog = encode_grid_mog(grid)
    cells = [row[:] for row in grid.cells]
    
    if rule['type'] == 'exact_address':
        rules = rule['rules']
        for r in range(h):
            for c in range(w):
                addr = mog[r, c]
                if addr in rules:
                    cells[r][c] = rules[addr]
    
    elif rule['type'] == 'bit_mask':
        mask = rule['mask']
        value = rule['value']
        fill = rule['fill']
        for r in range(h):
            for c in range(w):
                if (mog[r, c] & mask) == value:
                    cells[r][c] = fill
    
    elif rule['type'] == 'quadrant':
        lo, hi = rule['quadrant']
        values = rule['values']
        fill = rule['fill']
        qmask = (1 << (hi - lo + 1)) - 1
        for r in range(h):
            for c in range(w):
                quad_val = (mog[r, c] >> lo) & qmask
                if quad_val in values:
                    cells[r][c] = fill
    
    elif rule['type'] == 'colour_quadrant':
        rules = rule['rules']
        for r in range(h):
            for c in range(w):
                ic = grid.cells[r][c]
                for (col, (lo, hi), qval), oc in rules.items():
                    if ic == col:
                        qmask = (1 << (hi - lo + 1)) - 1
                        quad_val = (mog[r, c] >> lo) & qmask
                        if quad_val == qval:
                            cells[r][c] = oc
                            break
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# 4. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Discover and apply MOG-based conditional recolour rules."""
    # Check same-size
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    train_pairs = [(p.input, p.output) for p in task.train]
    
    # Discover rules
    rule = discover_mog_rules(train_pairs)
    
    if rule is None:
        return None
    
    # Verify on train (redundant but safe)
    for inp, out in train_pairs:
        pred = apply_mog_rule(rule, inp)
        if not grids_equal(pred, out):
            return None
    
    # Apply to test
    test_input = task.test[0].input
    pred = apply_mog_rule(rule, test_input)
    
    src = f"mog_{rule['type']}"
    return pred, src, {'rule': str(rule)}


if __name__ == "__main__":
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
        
        try:
            signal.setitimer(signal.ITIMER_REAL, 15.0)
            result = predict(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None
        
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
    
    print(f"\n═══ MOG Conditional Recolour ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
