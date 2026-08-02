"""
v041_neighbourhood_bitmask.py — The Sharp Knife for the Conditional Gap
========================================================================

Replaces global recolour with neighbourhood-masked conditional recolour.

Core idea: every cell generates an 8-bit neighbourhood bitmask
(representing the 8 Moore neighbours). Rules execute as:
  Recolour(X → Y) FILTERED BY Neighbour_Has_Colour(Z)

This bridges the conditional gap without complex program synthesis.

The 8-bit bitmask (clockwise from NW):
  bit 0: NW  bit 1: N   bit 2: NE
  bit 3: W              bit 4: E
  bit 5: SW  bit 6: S   bit 7: SE

Each bit = 1 if that neighbour has the target colour, 0 otherwise.

We also compute a simplified 24-bit "Local Context Fingerprint":
  Bits 0-7:  Neighbourhood bitmask (which colours are adjacent)
  Bits 8-15: Neighbourhood counts (how many of each colour)
  Bits 16-23: Topological flags (edge, corner, isolated, etc.)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter
import sys, os, signal

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
# 1. NEIGHBOURHOOD BITMASK
# ═══════════════════════════════════════════════════════════════════

# Moore neighbourhood offsets (clockwise from NW)
MOORE_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

def neighbourhood_bitmask_for_colour(grid: Grid, r: int, c: int, 
                                       target_colour: int) -> int:
    """
    8-bit bitmask: bit i = 1 if Moore neighbour i has target_colour.
    """
    h, w = grid.height, grid.width
    mask = 0
    for i, (dr, dc) in enumerate(MOORE_OFFSETS):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == target_colour:
            mask |= (1 << i)
    return mask


def neighbourhood_bitmask_general(grid: Grid, r: int, c: int) -> int:
    """
    8-bit bitmask: bit i = 1 if Moore neighbour i is non-zero.
    """
    h, w = grid.height, grid.width
    mask = 0
    for i, (dr, dc) in enumerate(MOORE_OFFSETS):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != 0:
            mask |= (1 << i)
    return mask


def neighbourhood_colours(grid: Grid, r: int, c: int) -> List[int]:
    """Get list of Moore neighbour colours (out-of-bounds = -1)."""
    h, w = grid.height, grid.width
    colours = []
    for dr, dc in MOORE_OFFSETS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            colours.append(grid.cells[nr][nc])
        else:
            colours.append(-1)
    return colours


# ═══════════════════════════════════════════════════════════════════
# 2. LOCAL CONTEXT FINGERPRINT (Simplified 24-bit)
# ═══════════════════════════════════════════════════════════════════

def local_context_fingerprint(grid: Grid, r: int, c: int) -> int:
    """
    24-bit local context fingerprint for a cell.
    
    Bits 0-7:  Which colours (0-7) are present in Moore neighbourhood
    Bits 8-11: Count of non-zero neighbours (0-8, 4 bits)
    Bits 12-13: Row parity, col parity
    Bit 14:    Is border (r==0 or r==h-1 or c==0 or c==w-1)
    Bit 15:    Is corner
    Bits 16-19: Distinct neighbour colours count (0-8, 4 bits)
    Bits 20-23: Cell colour (0-9, 4 bits)
    """
    h, w = grid.height, grid.width
    n_cols = neighbourhood_colours(grid, r, c)
    
    # Bits 0-7: colour presence in neighbourhood
    colour_presence = 0
    for col in range(8):
        if col in n_cols:
            colour_presence |= (1 << col)
    
    # Bits 8-11: non-zero neighbour count
    n_nonzero = sum(1 for x in n_cols if x > 0)
    
    # Bits 12-13: parity
    row_parity = r % 2
    col_parity = c % 2
    
    # Bits 14-15: border/corner
    is_border = (r == 0 or r == h - 1 or c == 0 or c == w - 1)
    is_corner = (r in (0, h - 1) and c in (0, w - 1))
    
    # Bits 16-19: distinct colours
    n_distinct = len(set(x for x in n_cols if x >= 0))
    
    # Bits 20-23: cell colour
    cell_colour = grid.cells[r][c]
    
    fingerprint = (
        (colour_presence & 0xFF) |
        ((n_nonzero & 0xF) << 8) |
        (row_parity << 12) |
        (col_parity << 13) |
        (int(is_border) << 14) |
        (int(is_corner) << 15) |
        ((n_distinct & 0xF) << 16) |
        ((cell_colour & 0xF) << 20)
    )
    
    return fingerprint


# ═══════════════════════════════════════════════════════════════════
# 3. CONDITIONAL RECOLOUR RULE DISCOVERY
# ═══════════════════════════════════════════════════════════════════

def discover_neighbourhood_rules(train_pairs: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """
    Discover conditional recolour rules using neighbourhood bitmasks.
    
    For each cell that changes, record:
    - input colour
    - neighbourhood bitmask for various target colours
    
    Search for rules like:
    "colour X with bit Y set in mask for colour Z → become W"
    """
    # Collect all non-zero colours across all train pairs
    all_colours = set()
    for inp, out in train_pairs:
        for r in range(inp.height):
            for c in range(inp.width):
                if inp.cells[r][c] != 0:
                    all_colours.add(inp.cells[r][c])
    
    # For each (input_colour, target_neighbour_colour) pair,
    # build a rule: (input_col, neighbour_col, bitmask) → output_col
    rule_candidates = {}  # (input_col, neighbour_col, bitmask) → output_col
    
    for inp, out in train_pairs:
        if inp.height != out.height or inp.width != out.width:
            return None
        
        h, w = inp.height, inp.width
        for r in range(h):
            for c in range(w):
                ic, oc = inp.cells[r][c], out.cells[r][c]
                if ic == oc:
                    continue  # No change
                
                # For each possible neighbour colour, compute bitmask
                for n_col in all_colours:
                    if n_col == ic:
                        continue
                    mask = neighbourhood_bitmask_for_colour(inp, r, c, n_col)
                    key = (ic, n_col, mask)
                    
                    if key in rule_candidates:
                        if rule_candidates[key] != oc:
                            rule_candidates[key] = None  # Inconsistent
                    else:
                        rule_candidates[key] = oc
    
    # Filter to consistent rules
    consistent = {k: v for k, v in rule_candidates.items() if v is not None}
    
    if not consistent:
        return None
    
    # Find the most specific rule that covers the most changes
    # Priority: non-zero bitmask > zero bitmask
    best_rule = None
    best_coverage = 0
    
    for (ic, n_col, mask), oc in consistent.items():
        if mask == 0:
            continue  # No neighbour of that colour — too general
        
        # Count how many cells this rule covers correctly
        coverage = 0
        for inp, out in train_pairs:
            h, w = inp.height, inp.width
            for r in range(h):
                for c in range(w):
                    if inp.cells[r][c] == ic and out.cells[r][c] == oc:
                        m = neighbourhood_bitmask_for_colour(inp, r, c, n_col)
                        if m == mask:
                            coverage += 1
        
        if coverage > best_coverage:
            best_coverage = coverage
            best_rule = (ic, n_col, mask, oc)
    
    if best_rule is None:
        return None
    
    ic, n_col, mask, oc = best_rule
    
    # Verify: does this rule correctly transform ALL changed cells?
    all_pass = True
    for inp, out in train_pairs:
        h, w = inp.height, inp.width
        cells = [row[:] for row in inp.cells]
        
        for r in range(h):
            for c in range(w):
                if inp.cells[r][c] == ic:
                    m = neighbourhood_bitmask_for_colour(inp, r, c, n_col)
                    if m == mask:
                        cells[r][c] = oc
        
        if not grids_equal(Grid(cells), out):
            all_pass = False
            break
    
    if all_pass:
        return {
            'type': 'neighbourhood_mask',
            'input_colour': ic,
            'neighbour_colour': n_col,
            'bitmask': mask,
            'output_colour': oc,
        }
    
    # Try: just having ANY neighbour of colour n_col (any non-zero mask)
    any_mask_rule = (ic, n_col, 'any', oc)
    all_pass = True
    for inp, out in train_pairs:
        h, w = inp.height, inp.width
        cells = [row[:] for row in inp.cells]
        
        for r in range(h):
            for c in range(w):
                if inp.cells[r][c] == ic:
                    m = neighbourhood_bitmask_for_colour(inp, r, c, n_col)
                    if m > 0:  # Any neighbour of that colour
                        cells[r][c] = oc
        
        if not grids_equal(Grid(cells), out):
            all_pass = False
            break
    
    if all_pass:
        return {
            'type': 'has_neighbour',
            'input_colour': ic,
            'neighbour_colour': n_col,
            'output_colour': oc,
        }
    
    # Try: cardinal neighbours only (N, S, E, W — bits 1, 3, 4, 6)
    cardinal_mask = (1 << 1) | (1 << 3) | (1 << 4) | (1 << 6)
    for (ic2, n_col2, mask2), oc2 in consistent.items():
        if mask2 == 0:
            continue
        
        # Check if cardinal-only works
        all_pass = True
        for inp, out in train_pairs:
            h, w = inp.height, inp.width
            cells = [row[:] for row in inp.cells]
            
            for r in range(h):
                for c in range(w):
                    if inp.cells[r][c] == ic2:
                        m = neighbourhood_bitmask_for_colour(inp, r, c, n_col2)
                        if m & cardinal_mask:  # Has cardinal neighbour
                            cells[r][c] = oc2
            
            if not grids_equal(Grid(cells), out):
                all_pass = False
                break
        
        if all_pass:
            return {
                'type': 'has_cardinal_neighbour',
                'input_colour': ic2,
                'neighbour_colour': n_col2,
                'output_colour': oc2,
            }
    
    return None


def discover_multi_rule(train_pairs: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """
    Discover multiple conditional recolour rules (one per input colour).
    
    Pattern: "colour X with neighbour Y → Z, colour A with neighbour B → C"
    """
    # Group changes by input colour
    changes_by_input = {}  # ic → [(ic, oc, n_col, mask)]
    
    for inp, out in train_pairs:
        if inp.height != out.height or inp.width != out.width:
            return None
        
        h, w = inp.height, inp.width
        for r in range(h):
            for c in range(w):
                ic, oc = inp.cells[r][c], out.cells[r][c]
                if ic == oc:
                    continue
                
                # Find which neighbour colour triggers this change
                n_cols = neighbourhood_colours(inp, r, c)
                for n_col in set(n_cols):
                    if n_col <= 0 or n_col == ic:
                        continue
                    mask = neighbourhood_bitmask_for_colour(inp, r, c, n_col)
                    if mask > 0:
                        if ic not in changes_by_input:
                            changes_by_input[ic] = []
                        changes_by_input[ic].append((ic, oc, n_col, mask))
    
    if not changes_by_input:
        return None
    
    # For each input colour, find the most common (n_col, oc) pair
    rules = {}
    for ic, changes in changes_by_input.items():
        # Count (n_col, oc) pairs
        pair_counts = Counter((n_col, oc) for _, oc, n_col, _ in changes)
        if pair_counts:
            (best_n_col, best_oc), count = pair_counts.most_common(1)[0]
            rules[ic] = (best_n_col, best_oc)
    
    if not rules:
        return None
    
    # Verify: does applying all rules correctly transform ALL train pairs?
    all_pass = True
    for inp, out in train_pairs:
        h, w = inp.height, inp.width
        cells = [row[:] for row in inp.cells]
        
        for r in range(h):
            for c in range(w):
                ic = inp.cells[r][c]
                if ic in rules:
                    n_col, oc = rules[ic]
                    mask = neighbourhood_bitmask_for_colour(inp, r, c, n_col)
                    if mask > 0:
                        cells[r][c] = oc
        
        if not grids_equal(Grid(cells), out):
            all_pass = False
            break
    
    if all_pass:
        return {
            'type': 'multi_rule',
            'rules': rules,
        }
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 4. FINGERPRINT-BASED RULE DISCOVERY
# ═══════════════════════════════════════════════════════════════════

def discover_fingerprint_rules(train_pairs: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """
    Discover rules based on the 24-bit local context fingerprint.
    
    For each cell that changes, compute its fingerprint.
    Find fingerprints that uniquely identify changed cells.
    """
    changed_fingerprints = {}  # fingerprint → output_colour
    unchanged_fingerprints = set()
    
    for inp, out in train_pairs:
        if inp.height != out.height or inp.width != out.width:
            return None
        
        h, w = inp.height, inp.width
        for r in range(h):
            for c in range(w):
                fp = local_context_fingerprint(inp, r, c)
                ic, oc = inp.cells[r][c], out.cells[r][c]
                
                if ic != oc:
                    if fp in changed_fingerprints:
                        if changed_fingerprints[fp] != oc:
                            changed_fingerprints[fp] = None
                    else:
                        changed_fingerprints[fp] = oc
                else:
                    unchanged_fingerprints.add(fp)
    
    # Find fingerprints unique to changed cells
    unique = {fp: oc for fp, oc in changed_fingerprints.items() 
              if fp not in unchanged_fingerprints and oc is not None}
    
    if not unique:
        return None
    
    # Verify
    all_pass = True
    for inp, out in train_pairs:
        h, w = inp.height, inp.width
        cells = [row[:] for row in inp.cells]
        
        for r in range(h):
            for c in range(w):
                fp = local_context_fingerprint(inp, r, c)
                if fp in unique:
                    cells[r][c] = unique[fp]
        
        if not grids_equal(Grid(cells), out):
            all_pass = False
            break
    
    if all_pass:
        return {
            'type': 'fingerprint',
            'rules': unique,
        }
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 5. RULE APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_rule(rule: Dict, grid: Grid) -> Grid:
    """Apply a neighbourhood-based conditional recolour rule."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    if rule['type'] == 'neighbourhood_mask':
        ic = rule['input_colour']
        n_col = rule['neighbour_colour']
        mask = rule['bitmask']
        oc = rule['output_colour']
        
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == ic:
                    m = neighbourhood_bitmask_for_colour(grid, r, c, n_col)
                    if m == mask:
                        cells[r][c] = oc
    
    elif rule['type'] == 'has_neighbour':
        ic = rule['input_colour']
        n_col = rule['neighbour_colour']
        oc = rule['output_colour']
        
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == ic:
                    m = neighbourhood_bitmask_for_colour(grid, r, c, n_col)
                    if m > 0:
                        cells[r][c] = oc
    
    elif rule['type'] == 'has_cardinal_neighbour':
        ic = rule['input_colour']
        n_col = rule['neighbour_colour']
        oc = rule['output_colour']
        
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == ic:
                    m = neighbourhood_bitmask_for_colour(grid, r, c, n_col)
                    if m & ((1<<1)|(1<<3)|(1<<4)|(1<<6)):
                        cells[r][c] = oc
    
    elif rule['type'] == 'multi_rule':
        rules = rule['rules']
        for r in range(h):
            for c in range(w):
                ic = grid.cells[r][c]
                if ic in rules:
                    n_col, oc = rules[ic]
                    m = neighbourhood_bitmask_for_colour(grid, r, c, n_col)
                    if m > 0:
                        cells[r][c] = oc
    
    elif rule['type'] == 'fingerprint':
        rules = rule['rules']
        for r in range(h):
            for c in range(w):
                fp = local_context_fingerprint(grid, r, c)
                if fp in rules:
                    cells[r][c] = rules[fp]
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# 6. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Discover and apply neighbourhood-based conditional recolour rules."""
    # Check same-size
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    train_pairs = [(p.input, p.output) for p in task.train]
    
    # Try each rule type
    strategies = [
        ("fingerprint", discover_fingerprint_rules),
        ("multi_rule", discover_multi_rule),
        ("neighbourhood", discover_neighbourhood_rules),
    ]
    
    for name, fn in strategies:
        try:
            signal.setitimer(signal.ITIMER_REAL, 10.0)
            rule = fn(train_pairs)
            signal.setitimer(signal.ITIMER_REAL, 0)
            
            if rule is not None:
                # Verify
                all_pass = True
                for inp, out in train_pairs:
                    pred = apply_rule(rule, inp)
                    if not grids_equal(pred, out):
                        all_pass = False
                        break
                
                if all_pass:
                    test_input = task.test[0].input
                    pred = apply_rule(rule, test_input)
                    return pred, f"nb_{name}", {'rule': str(rule)}
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            continue
    
    return None


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
    
    print(f"\n═══ Neighbourhood Bitmask ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
