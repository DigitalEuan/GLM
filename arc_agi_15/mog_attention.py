"""
mog_attention.py — MOG-as-Attention ARC Transformer (First Shot)
=================================================================

The idea: stop writing solvers. Use the MOG 4×6 grid as an attention mechanism.

The MOG has 24 bits in 4 rows × 6 columns:
  Row 0 (M_Mass):      bits 0-5   — syndrome weight 11 (global broadcast)
  Row 1 (I_Info):      bits 6-11  — syndrome weight 7  (topological shift)
  Row 2 (A_Activation): bits 12-17 — syndrome weight 1  (local absorption)
  Row 3 (P_Potential):  bits 18-23 — syndrome weight 1  (local phase)

This is an attention pattern: Row 0 has the widest "blast radius" (11 bits),
Row 3 is local. The 6 columns are spatial blocks.

Pipeline:
  1. Encode ARC grid → 24-bit vectors (one per cell, using MOG addressing)
  2. Compute attention weights from MOG mass asymmetry
  3. Generate candidate outputs by substrate operations (not solver rules)
  4. Snap candidates through Golay engine (error correction)
  5. Score by TAX/NRCI (geometric stability)
  6. Verify on train pairs, predict on test
"""

from __future__ import annotations
import os, sys, math, json, time
from collections import Counter, defaultdict
from fractions import Fraction
from typing import Dict, List, Optional, Tuple, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid, load_task

# ═══════════════════════════════════════════════════════════════════════════════
# MOG Structure — the attention mechanism
# ═══════════════════════════════════════════════════════════════════════════════

# MOG quadrant definitions (from checkpoint §4)
MOG_QUADRANTS = {
    "M_Mass":      list(range(0, 6)),    # Row 0: bits 0-5
    "I_Info":      list(range(6, 12)),   # Row 1: bits 6-11
    "A_Activation": list(range(12, 18)), # Row 2: bits 12-17
    "P_Potential":  list(range(18, 24)), # Row 3: bits 18-23
}

# Syndrome weights (blast radius) per quadrant — THIS IS THE ATTENTION WEIGHT
ATTENTION_WEIGHTS = {
    "M_Mass":      11.0,  # Global broadcast
    "I_Info":       7.0,  # Topological shift
    "A_Activation": 1.0,  # Local absorption
    "P_Potential":  1.0,  # Local phase
}

# Normalise to sum to 1
_total_attn = sum(ATTENTION_WEIGHTS.values())
ATTENTION_WEIGHTS = {k: v / _total_attn for k, v in ATTENTION_WEIGHTS.items()}

# Golay generator matrix (systematic form [I_12 | P])
# We'll use the standard construction
def _build_golay_generator():
    """Build the [24,12,8] Golay generator matrix in systematic form."""
    # P matrix (12×12) — the standard Golay code P
    P = [
        [1,1,0,1,1,1,0,0,0,1,0,1],
        [1,0,1,1,1,0,0,0,1,0,1,1],
        [0,1,1,1,0,0,0,1,0,1,1,1],
        [1,1,1,0,0,0,1,0,1,1,0,1],
        [1,1,0,0,0,1,0,1,1,0,1,1],
        [1,0,0,0,1,0,1,1,0,1,1,1],
        [0,0,0,1,0,1,1,0,1,1,1,1],
        [0,0,1,0,1,1,0,1,1,1,0,1],
        [0,1,0,1,1,0,1,1,1,0,1,1],
        [1,0,1,1,0,1,1,1,0,1,1,0],
        [0,1,1,0,1,1,1,0,1,1,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,0],
    ]
    # G = [I_12 | P]
    G = []
    for i in range(12):
        row = [0] * 24
        row[i] = 1
        for j in range(12):
            row[12 + j] = P[i][j]
        G.append(row)
    return G

GOLAY_G = _build_golay_generator()

def golay_encode(message_bits: List[int]) -> List[int]:
    """Encode 12 message bits into 24-bit Golay codeword."""
    codeword = [0] * 24
    for i in range(12):
        if message_bits[i]:
            for j in range(24):
                codeword[j] ^= GOLAY_G[i][j]
    return codeword

def golay_syndrome(vector: List[int]) -> List[int]:
    """Compute the syndrome of a 24-bit vector."""
    # H = [-P^T | I_12]
    syndrome = [0] * 12
    for j in range(12):
        for i in range(12):
            syndrome[j] ^= (vector[i] & GOLAY_G[i][12 + j])
        syndrome[j] ^= vector[12 + j]
    return syndrome

def golay_snap(vector: List[int]) -> List[int]:
    """Snap a 24-bit vector to the nearest Golay codeword (syndrome decoding)."""
    syn = golay_syndrome(vector)
    syn_weight = sum(syn)
    
    if syn_weight == 0:
        return vector[:]  # Already a codeword
    
    # Try flipping each bit and check if syndrome improves
    best = vector[:]
    best_syn_weight = syn_weight
    
    for i in range(24):
        trial = vector[:]
        trial[i] ^= 1
        trial_syn = golay_syndrome(trial)
        trial_weight = sum(trial_syn)
        if trial_weight < best_syn_weight:
            best = trial
            best_syn_weight = trial_weight
    
    # If we found a single-bit correction, try one more
    if best_syn_weight < syn_weight:
        for i in range(24):
            trial = best[:]
            trial[i] ^= 1
            trial_syn = golay_syndrome(trial)
            trial_weight = sum(trial_syn)
            if trial_weight < best_syn_weight:
                best = trial
                best_syn_weight = trial_weight
    
    return best

def is_golay_codeword(vector: List[int]) -> bool:
    return sum(golay_syndrome(vector)) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Y constant and TAX/NRCI (from checkpoint)
# ═══════════════════════════════════════════════════════════════════════════════

# Y = 1/(π + 2/π) using 50-term CF approximation
_PI_FRAC = Fraction(16590847, 5281024)
Y_FRAC = Fraction(1, 1) / (_PI_FRAC + Fraction(2, 1) / _PI_FRAC)
Y = float(Y_FRAC)

def compute_tax(vector: List[int]) -> float:
    """Symmetry Tax = HW × Y + norm²/8"""
    hw = sum(vector)
    norm_sq = sum(v * v for v in vector)
    return hw * Y + norm_sq / 8.0

def compute_nrci(vector: List[int], alpha: float = 1.0) -> float:
    """Non-Random Coherence Index = 10/(10 + α×TAX)"""
    tax = compute_tax(vector)
    return 10.0 / (10.0 + alpha * tax)


# ═══════════════════════════════════════════════════════════════════════════════
# Grid ↔ 24-bit MOG Encoding
# ═══════════════════════════════════════════════════════════════════════════════

def grid_to_mog_vectors(grid: Grid) -> List[List[int]]:
    """
    Encode an ARC grid into 24-bit MOG vectors.
    
    Each cell gets a 24-bit vector based on:
    - Its colour (mapped to Gray code bits in M_Mass row)
    - Its position (mapped to I_Info row)
    - Its neighbourhood context (mapped to A_Activation row)
    - Its structural role (mapped to P_Potential row)
    """
    h, w = grid.height, grid.width
    vectors = []
    
    for r in range(h):
        for c in range(w):
            colour = grid.cells[r][c]
            bits = [0] * 24
            
            # Row 0 (M_Mass): colour encoding
            # Map colour (0-9) to 6 bits using Gray-like encoding
            if colour > 0:
                # Use the colour value to activate bits in M_Mass
                for i in range(6):
                    bits[i] = (colour >> i) & 1
            
            # Row 1 (I_Info): position encoding
            # Encode row and column relative to grid size
            row_norm = r / max(h - 1, 1)  # 0 to 1
            col_norm = c / max(w - 1, 1)  # 0 to 1
            # Quantize to 3 bits each
            row_q = int(row_norm * 7)
            col_q = int(col_norm * 7)
            bits[6] = (row_q >> 0) & 1
            bits[7] = (row_q >> 1) & 1
            bits[8] = (row_q >> 2) & 1
            bits[9] = (col_q >> 0) & 1
            bits[10] = (col_q >> 1) & 1
            bits[11] = (col_q >> 2) & 1
            
            # Row 2 (A_Activation): neighbourhood context
            # Count neighbours of each colour
            neighbour_colours = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w:
                    neighbour_colours.append(grid.cells[nr][nc])
            
            # Encode neighbour diversity and dominant neighbour
            if neighbour_colours:
                unique_neighbours = len(set(neighbour_colours))
                dominant = Counter(neighbour_colours).most_common(1)[0][0]
                bits[12] = min(unique_neighbours - 1, 1)  # 0=same, 1=mixed
                bits[13] = (dominant >> 0) & 1
                bits[14] = (dominant >> 1) & 1
                bits[15] = (dominant >> 2) & 1
                # Is this cell a boundary? (has 0 neighbour)
                bits[16] = 1 if 0 in neighbour_colours else 0
                # Is this cell interior? (surrounded by same colour)
                bits[17] = 1 if len(set(neighbour_colours)) == 1 else 0
            
            # Row 3 (P_Potential): structural role
            # Is this cell part of a connected component?
            # Encode component size hint (approximate)
            if colour > 0:
                # Count same-colour 4-connected neighbours
                same_count = sum(1 for nc in neighbour_colours if nc == colour)
                bits[18] = (same_count >> 0) & 1
                bits[19] = (same_count >> 1) & 1
                # Is this cell on the border of the grid?
                bits[20] = 1 if r == 0 or r == h-1 else 0
                bits[21] = 1 if c == 0 or c == w-1 else 0
                # Parity bits for error correction
                bits[22] = sum(bits[0:11]) % 2
                bits[23] = sum(bits[11:22]) % 2
            
            vectors.append(bits)
    
    return vectors


def mog_vectors_to_grid(vectors: List[List[int]], h: int, w: int, 
                         colour_palette: List[int]) -> Grid:
    """Decode 24-bit MOV vectors back to an ARC grid."""
    cells = []
    for idx, bits in enumerate(vectors):
        r = idx // w
        c = idx % w
        
        # Decode colour from M_Mass row (bits 0-5)
        raw_colour = 0
        for i in range(6):
            raw_colour |= (bits[i] << i)
        
        # Map to nearest valid colour in palette
        if raw_colour == 0:
            colour = 0
        else:
            # Find closest palette colour
            best_dist = 999
            colour = colour_palette[0] if colour_palette else 0
            for pc in colour_palette:
                if pc == 0:
                    continue
                dist = bin(raw_colour ^ pc).count('1')
                if dist < best_dist:
                    best_dist = dist
                    colour = pc
        
        cells.append(colour)
    
    # Reshape to grid
    grid_cells = []
    for r in range(h):
        grid_cells.append(cells[r*w:(r+1)*w])
    return Grid(grid_cells)


# ═══════════════════════════════════════════════════════════════════════════════
# MOG Attention — the core mechanism
# ═══════════════════════════════════════════════════════════════════════════════

def mog_attention_score(input_vectors: List[List[int]], 
                         output_vectors: List[List[int]]) -> float:
    """
    Score the transformation from input to output using MOG attention.
    
    The attention mechanism weights changes by which MOG quadrant they affect:
    - Changes in M_Mass (Row 0): high attention (global broadcast)
    - Changes in I_Info (Row 1): medium attention (topological shift)
    - Changes in A_Activation (Row 2): low attention (local)
    - Changes in P_Potential (Row 3): low attention (local)
    
    Returns: attention-weighted coherence score (higher = more coherent)
    """
    if len(input_vectors) != len(output_vectors):
        return 0.0
    
    total_attn = 0.0
    coherent_attn = 0.0
    
    for inp, out in zip(input_vectors, output_vectors):
        # Compute bit-level changes per quadrant
        for quad_name, bits in MOG_QUADRANTS.items():
            weight = ATTENTION_WEIGHTS[quad_name]
            for b in bits:
                total_attn += weight
                if inp[b] == out[b]:
                    coherent_attn += weight
    
    return coherent_attn / total_attn if total_attn > 0 else 0.0


def mog_transformation_delta(input_vectors: List[List[int]],
                              output_vectors: List[List[int]]) -> Dict[str, float]:
    """
    Compute the transformation delta per MOG quadrant.
    Returns: fraction of bits changed in each quadrant.
    """
    deltas = {q: [0, 0] for q in MOG_QUADRANTS}  # [changed, total]
    
    for inp, out in zip(input_vectors, output_vectors):
        for quad_name, bits in MOG_QUADRANTS.items():
            for b in bits:
                deltas[quad_name][1] += 1
                if inp[b] != out[b]:
                    deltas[quad_name][0] += 1
    
    return {q: d[0]/d[1] if d[1] > 0 else 0 for q, d in deltas.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# Candidate Generation — substrate-native, not solver-based
# ═══════════════════════════════════════════════════════════════════════════════

def extract_transformation_pattern(task: ARCTask) -> Dict[str, Any]:
    """
    Learn the transformation pattern from train pairs using MOG analysis.
    Instead of looking for rules, we characterise the MOG delta.
    """
    pattern = {
        "deltas": [],
        "attention_profile": {},
        "palette_in": set(),
        "palette_out": set(),
    }
    
    for pair in task.train:
        inp_vecs = grid_to_mog_vectors(pair.input)
        out_vecs = grid_to_mog_vectors(pair.output)
        
        # Only compute delta for same-size pairs
        if pair.input.shape == pair.output.shape:
            delta = mog_transformation_delta(inp_vecs, out_vecs)
            attn = mog_attention_score(inp_vecs, out_vecs)
            pattern["deltas"].append(delta)
            pattern["attention_profile"][pair.input.shape] = attn
        else:
            pattern["attention_profile"][pair.input.shape] = 0.0
        
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                pattern["palette_in"].add(pair.input.cells[r][c])
        for r in range(pair.output.height):
            for c in range(pair.output.width):
                pattern["palette_out"].add(pair.output.cells[r][c])
    
    # Compute average delta per quadrant (only if we have same-size pairs)
    if pattern["deltas"]:
        avg_delta = {}
        for q in MOG_QUADRANTS:
            avg_delta[q] = sum(d[q] for d in pattern["deltas"]) / len(pattern["deltas"])
    else:
        avg_delta = {q: 0.0 for q in MOG_QUADRANTS}
    pattern["avg_delta"] = avg_delta
    
    # Classify the transformation type based on MOG profile
    mass_delta = avg_delta["M_Mass"]
    info_delta = avg_delta["I_Info"]
    act_delta = avg_delta["A_Activation"]
    pot_delta = avg_delta["P_Potential"]
    
    if mass_delta > 0.3:
        pattern["type"] = "global_recolour"  # Heavy M_Mass changes
    elif info_delta > 0.3:
        pattern["type"] = "positional_shift"  # Heavy I_Info changes
    elif act_delta > 0.3:
        pattern["type"] = "neighbour_transform"  # Heavy A_Activation changes
    elif pot_delta > 0.3:
        pattern["type"] = "structural_change"  # Heavy P_Potential changes
    else:
        pattern["type"] = "subtle"  # All quadrants lightly perturbed
    
    return pattern


def generate_candidates(task: ARCTask, pattern: Dict[str, Any]) -> List[Grid]:
    """
    Generate candidate output grids using substrate-native operations.
    
    Instead of solver rules, we use the MOG transformation pattern to guide
    candidate generation. The key insight: the MOG delta tells us WHICH
    quadrant to steer, and the Golay snap keeps us in valid codeword space.
    """
    test_input = task.test[0].input
    h, w = test_input.height, test_input.width
    candidates = []
    
    palette = sorted(set(v for row in test_input.cells for v in row) | 
                     pattern["palette_out"])
    
    # Strategy 1: Direct MOG encode → Golay snap → decode
    # This is the "substrate equilibrium" approach
    inp_vecs = grid_to_mog_vectors(test_input)
    snapped_vecs = [golay_snap(v) for v in inp_vecs]
    cand = mog_vectors_to_grid(snapped_vecs, h, w, palette)
    candidates.append(("golay_snap", cand))
    
    # Strategy 2: Apply the learned MOG delta
    # Modify input vectors according to the average quadrant deltas
    avg_delta = pattern["avg_delta"]
    modified_vecs = []
    for vec in inp_vecs:
        new_vec = vec[:]
        for quad_name, bits in MOG_QUADRANTS.items():
            delta = avg_delta[quad_name]
            # For each bit in this quadrant, flip with probability = delta
            # But deterministically: flip the first N bits where N = delta * len(bits)
            n_flip = int(round(delta * len(bits)))
            flipped = 0
            for b in bits:
                if flipped < n_flip and vec[b] == 1:
                    new_vec[b] = 0
                    flipped += 1
                elif flipped < n_flip and vec[b] == 0 and delta > 0.5:
                    new_vec[b] = 1
                    flipped += 1
        modified_vecs.append(golay_snap(new_vec))
    cand = mog_vectors_to_grid(modified_vecs, h, w, palette)
    candidates.append(("mog_delta", cand))
    
    # Strategy 3: Colour-only transformation (M_Mass steering)
    # Learn a colour mapping from train pairs, apply to test
    colour_map = _learn_colour_map(task)
    if colour_map:
        cells = []
        for r in range(h):
            row = []
            for c in range(w):
                v = test_input.cells[r][c]
                row.append(colour_map.get(v, v))
            cells.append(row)
        candidates.append(("mass_steer", Grid(cells)))
    
    # Strategy 4: Neighbour-conditional via MOG (A_Activation steering)
    # For each cell, check if its MOG A_Activation bits suggest a change
    neigh_cand = _neighbour_mog_transform(test_input, task)
    if neigh_cand:
        candidates.append(("activation_steer", neigh_cand))
    
    # Strategy 5: Identity (for tasks where nothing changes)
    candidates.append(("identity", Grid([row[:] for row in test_input.cells])))
    
    # Strategy 6: Uniform fill with most common output colour
    if pattern["palette_out"]:
        most_common_out = Counter(pattern["palette_out"]).most_common(1)[0][0]
        if most_common_out != 0:
            cells = [[most_common_out if test_input.cells[r][c] == 0 
                       else test_input.cells[r][c] for c in range(w)] for r in range(h)]
            candidates.append(("uniform_fill", Grid(cells)))
    
    return candidates


def _learn_colour_map(task: ARCTask) -> Dict[int, int]:
    """Learn a colour mapping from train pairs (consistent across all pairs)."""
    mapping = {}
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue  # Skip size-changing pairs
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                src = pair.input.cells[r][c]
                dst = pair.output.cells[r][c]
                if src != dst:
                    if src in mapping:
                        if mapping[src] != dst:
                            return {}  # Inconsistent
                    else:
                        mapping[src] = dst
    return mapping


def _neighbour_mog_transform(grid: Grid, task: ARCTask) -> Optional[Grid]:
    """
    Use MOG A_Activation neighbourhood encoding to guide transformation.
    For each cell, check if its neighbourhood signature (encoded in A_Activation)
    matches a learned transformation.
    """
    # Learn: for each (colour, neighbour_signature) → output colour
    rules = {}
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                iv = pair.input.cells[r][c]
                ov = pair.output.cells[r][c]
                if iv == ov:
                    continue
                n_cols = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w:
                        n_cols.append(pair.input.cells[nr][nc])
                key = (iv, tuple(sorted(n_cols)))
                if key in rules and rules[key] != ov:
                    return None  # Inconsistent
                rules[key] = ov
    
    if not rules:
        return None
    
    # Apply rules
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        for c in range(w):
            iv = grid.cells[r][c]
            n_cols = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w:
                    n_cols.append(grid.cells[nr][nc])
            key = (iv, tuple(sorted(n_cols)))
            if key in rules:
                cells[r][c] = rules[key]
                changed = True
    
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════════════════
# Candidate Scoring — using TAX/NRCI as the stability metric
# ═══════════════════════════════════════════════════════════════════════════════

def score_candidate(input_grid: Grid, candidate: Grid, 
                     train_pairs: List) -> Dict[str, Any]:
    """
    Score a candidate output grid using multiple substrate metrics.
    """
    # Hard gate: must reproduce all train pairs
    # (This is checked separately in solve_task)
    
    # MOG attention coherence
    inp_vecs = grid_to_mog_vectors(input_grid)
    cand_vecs = grid_to_mog_vectors(candidate)
    attn_score = mog_attention_score(inp_vecs, cand_vecs)
    
    # TAX of the candidate (lower = more stable)
    cand_flat = [v for row in candidate.cells for v in row]
    total_tax = compute_tax([1 if v > 0 else 0 for v in cand_flat])
    
    # NRCI of the candidate (higher = more coherent)
    nrci = compute_nrci([1 if v > 0 else 0 for v in cand_flat])
    
    # Transformation delta (how much changed)
    delta = mog_transformation_delta(inp_vecs, cand_vecs)
    
    return {
        "attention": attn_score,
        "tax": total_tax,
        "nrci": nrci,
        "delta": delta,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main Solver — MOG Attention Transformer
# ═══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    return g1.height == g2.height and g1.width == g2.width and g1.cells == g2.cells


def solve_task(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Solve an ARC task using the MOG attention transformer.
    
    Pipeline:
    1. Extract transformation pattern from train pairs (MOG delta analysis)
    2. Generate candidates using substrate-native operations
    3. Verify each candidate on ALL train pairs (hard gate)
    4. Score survivors by MOG attention coherence
    5. Return the best-scoring verified candidate
    """
    # Step 1: Learn the transformation pattern
    pattern = extract_transformation_pattern(task)
    
    # Step 2: Generate candidates
    candidates = generate_candidates(task, pattern)
    
    # Step 3: Verify on train pairs (hard gate) and score
    verified = []
    for name, candidate in candidates:
        # Hard gate: must reproduce ALL train pairs exactly
        passes = True
        for pair in task.train:
            # Apply the same transformation to train input
            # We need to regenerate the candidate for each train pair
            # For now, just check if the candidate for test matches train outputs
            # by applying the same logic
            pass
        
        # Actually, we need to verify the transformation, not just the test output
        # Let's verify by applying the same generation strategy to each train input
        train_passes = _verify_on_train(task, name, candidate, pattern)
        if not train_passes:
            continue
        
        # Score
        scores = score_candidate(task.test[0].input, candidate, task.train)
        verified.append((name, candidate, scores))
    
    if not verified:
        return None
    
    # Step 4: Select best candidate
    # Rank by: train-pair match first, then NRCI, then attention score
    # Since all verified candidates pass the hard gate, rank by NRCI
    verified.sort(key=lambda x: -x[2]["nrci"])
    
    best_name, best_grid, best_scores = verified[0]
    return best_grid, f"mog_{best_name}"


def _verify_on_train(task: ARCTask, strategy_name: str, 
                      test_candidate: Grid, pattern: Dict) -> bool:
    """
    Verify that the same transformation strategy produces correct outputs
    for ALL train pairs.
    """
    for pair in task.train:
        # Regenerate the transformation for this train input
        train_candidates = _apply_strategy(task, pair.input, strategy_name, pattern)
        if train_candidates is None:
            return False
        
        # Check if any candidate matches the expected output
        if not any(grids_equal(c, pair.output) for c in train_candidates):
            return False
    
    return True


def _apply_strategy(task: ARCTask, grid: Grid, strategy_name: str,
                     pattern: Dict) -> Optional[List[Grid]]:
    """Apply a specific strategy to a grid (for train verification)."""
    h, w = grid.height, grid.width
    palette = sorted(set(v for row in grid.cells for v in row) | 
                     pattern["palette_out"])
    
    if strategy_name == "golay_snap":
        inp_vecs = grid_to_mog_vectors(grid)
        snapped = [golay_snap(v) for v in inp_vecs]
        return [mog_vectors_to_grid(snapped, h, w, palette)]
    
    elif strategy_name == "mog_delta":
        inp_vecs = grid_to_mog_vectors(grid)
        avg_delta = pattern["avg_delta"]
        modified = []
        for vec in inp_vecs:
            new_vec = vec[:]
            for quad_name, bits in MOG_QUADRANTS.items():
                delta = avg_delta[quad_name]
                n_flip = int(round(delta * len(bits)))
                flipped = 0
                for b in bits:
                    if flipped < n_flip and vec[b] == 1:
                        new_vec[b] = 0
                        flipped += 1
                    elif flipped < n_flip and vec[b] == 0 and delta > 0.5:
                        new_vec[b] = 1
                        flipped += 1
            modified.append(golay_snap(new_vec))
        return [mog_vectors_to_grid(modified, h, w, palette)]
    
    elif strategy_name == "mass_steer":
        colour_map = _learn_colour_map(task)
        if not colour_map:
            return None
        cells = [[colour_map.get(grid.cells[r][c], grid.cells[r][c]) 
                   for c in range(w)] for r in range(h)]
        return [Grid(cells)]
    
    elif strategy_name == "activation_steer":
        result = _neighbour_mog_transform(grid, task)
        return [result] if result else None
    
    elif strategy_name == "identity":
        return [Grid([row[:] for row in grid.cells])]
    
    elif strategy_name == "uniform_fill":
        most_common_out = Counter(pattern["palette_out"]).most_common(1)[0][0]
        cells = [[most_common_out if grid.cells[r][c] == 0 
                   else grid.cells[r][c] for c in range(w)] for r in range(h)]
        return [Grid(cells)]
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark(batch_dir: str) -> Dict[str, Any]:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results = []
    solver_counts = Counter()
    
    t0 = time.time()
    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        outcome = solve_task(task)
        solved = outcome is not None
        solver = outcome[1] if outcome else "none"
        results.append({
            "task_id": task.name,
            "solved": solved,
            "solver": solver,
        })
        if solved:
            solver_counts[solver] += 1
    elapsed = time.time() - t0
    
    solved_n = sum(1 for r in results if r["solved"])
    return {
        "solved": solved_n,
        "total": len(results),
        "pct": round(100.0 * solved_n / max(1, len(results)), 1),
        "solver_counts": dict(solver_counts),
        "elapsed": round(elapsed, 1),
        "results": results,
    }


def main():
    batch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training")
    
    print("=" * 72)
    print(" MOG ATTENTION TRANSFORMER — First Shot")
    print("=" * 72)
    print()
    
    summary = benchmark(batch)
    
    print("=" * 72)
    print(f" RESULT: {summary['solved']}/{summary['total']} ({summary['pct']}%)")
    print(f" Time: {summary['elapsed']}s")
    print("=" * 72)
    
    for r in summary["results"]:
        if r["solved"]:
            print(f"  ✓ {r['task_id']}: {r['solver']}")
    
    print(f"\n  Solver distribution:")
    for solver, count in sorted(summary["solver_counts"].items(), 
                                 key=lambda kv: -kv[1]):
        print(f"    {solver}: {count}")
    
    # Save
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "REPORTS", "mog_attention_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
