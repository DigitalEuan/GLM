"""
v036_cayley_menger.py — Cayley-Menger Distance Geometry for ARC
================================================================

Implements coordinate-free object analysis using Cayley-Menger determinants.

Key capabilities:
1. Object identity via Menger matrix (translation/rotation invariant)
2. Containment detection via betweenness property
3. Intrinsic area/volume computation
4. Dimensionality testing (coplanarity check)

The Menger matrix for a set of points {P1, ..., Pn} is:
  M = [0    1       1       ...  1    ]
      [1    0       d12²    ...  d1n² ]
      [1    d21²    0       ...  d2n² ]
      [...  ...     ...     ...  ...  ]
      [1    dn1²    dn2²    ...  0    ]

This matrix is invariant under translation and rotation.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Set, Any
from collections import Counter, deque
import sys, os, signal, hashlib
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
# 1. OBJECT SEGMENTATION
# ═══════════════════════════════════════════════════════════════════

def find_objects(grid: Grid) -> Dict[int, List[List[Tuple[int, int]]]]:
    """
    Find connected components for each non-zero colour.
    Returns: {colour: [component1, component2, ...]}
    """
    h, w = grid.height, grid.width
    objects = {}
    
    for target_col in set(grid.cells[r][c] for r in range(h) for c in range(w)):
        if target_col == 0:
            continue
        
        visited = set()
        components = []
        
        for r in range(h):
            for c in range(w):
                if (r, c) in visited or grid.cells[r][c] != target_col:
                    continue
                
                comp = []
                queue = deque([(r, c)])
                visited.add((r, c))
                
                while queue:
                    cr, cc = queue.popleft()
                    comp.append((cr, cc))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if (0 <= nr < h and 0 <= nc < w 
                            and (nr, nc) not in visited 
                            and grid.cells[nr][nc] == target_col):
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                
                components.append(comp)
        
        if components:
            objects[target_col] = components
    
    return objects


# ═══════════════════════════════════════════════════════════════════
# 2. CAYLEY-MENGER MATRIX
# ═══════════════════════════════════════════════════════════════════

def pairwise_distance_matrix(points: List[Tuple[int, int]]) -> np.ndarray:
    """Compute squared Euclidean distance matrix for a set of 2D points."""
    n = len(points)
    if n == 0:
        return np.array([[]])
    
    coords = np.array(points, dtype=float)
    # deltas: (n, n, 2)
    deltas = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    # squared distances: (n, n)
    dist_sq = np.sum(deltas**2, axis=-1)
    return dist_sq


def cayley_menger_matrix(points: List[Tuple[int, int]]) -> np.ndarray:
    """
    Build the Cayley-Menger matrix for a set of points.
    
    M = [0    1       1       ...  1    ]
        [1    0       d12²    ...  d1n² ]
        [1    d21²    0       ...  d2n² ]
        [...  ...     ...     ...  ...  ]
        [1    dn1²    dn2²    ...  0    ]
    """
    n = len(points)
    dist_sq = pairwise_distance_matrix(points)
    
    # Build (n+1) x (n+1) matrix
    M = np.zeros((n + 1, n + 1))
    M[0, 0] = 0
    M[0, 1:] = 1
    M[1:, 0] = 1
    M[1:, 1:] = dist_sq
    
    return M


def cayley_menger_determinant(points: List[Tuple[int, int]]) -> float:
    """
    Compute the Cayley-Menger determinant.
    
    For a triangle: CM = det(M), Area² = CM / 16
    For a tetrahedron: CM = det(M), Volume² = CM / 288
    If CM = 0, points are coplanar.
    """
    M = cayley_menger_matrix(points)
    return np.linalg.det(M)


def intrinsic_area(points: List[Tuple[int, int]]) -> float:
    """Compute intrinsic area of a polygon from its Menger matrix."""
    if len(points) < 3:
        return 0.0
    cm = cayley_menger_determinant(points)
    if cm < 0:
        return 0.0  # Numerical error
    return np.sqrt(cm / 16.0)


# ═══════════════════════════════════════════════════════════════════
# 3. MENGER HASH (Object Identity)
# ═══════════════════════════════════════════════════════════════════

def menger_hash(points: List[Tuple[int, int]]) -> str:
    """
    Compute a hash of the Menger matrix for object identity.
    This is invariant under translation and rotation.
    """
    if len(points) == 0:
        return "empty"
    
    dist_sq = pairwise_distance_matrix(points)
    
    # Sort the upper triangle of distances for canonical form
    n = len(points)
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            distances.append(dist_sq[i, j])
    
    distances.sort()
    
    # Hash the sorted distance profile
    dist_str = ','.join(f'{d:.2f}' for d in distances)
    return hashlib.md5(dist_str.encode()).hexdigest()[:12]


def menger_signature(points: List[Tuple[int, int]]) -> Tuple[float, ...]:
    """
    Compute a canonical signature from the Menger matrix.
    Returns sorted eigenvalues of the Gram matrix (translation/rotation invariant).
    """
    if len(points) < 2:
        return (0.0,)
    
    dist_sq = pairwise_distance_matrix(points)
    
    # Convert to Gram matrix: G_ij = (d_i0² + d_j0² - d_ij²) / 2
    n = len(points)
    G = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            G[i, j] = (dist_sq[i, 0] + dist_sq[j, 0] - dist_sq[i, j]) / 2.0
    
    # Eigenvalues of Gram matrix are translation/rotation invariant
    eigenvalues = np.linalg.eigvalsh(G)
    eigenvalues = np.sort(np.abs(eigenvalues))[::-1]
    
    return tuple(float(v) for v in eigenvalues[:5])  # Top 5


# ═══════════════════════════════════════════════════════════════════
# 4. CONTAINMENT DETECTION (Betweenness)
# ═══════════════════════════════════════════════════════════════════

def is_between(A: Tuple[int, int], B: Tuple[int, int], C: Tuple[int, int]) -> bool:
    """
    Check if point B is between A and C using the betweenness property:
    d(A,C) = d(A,B) + d(B,C)
    """
    dAC = np.sqrt((A[0]-C[0])**2 + (A[1]-C[1])**2)
    dAB = np.sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)
    dBC = np.sqrt((B[0]-C[0])**2 + (B[1]-C[1])**2)
    
    return abs(dAC - dAB - dBC) < 1e-6


def containment_score(point: Tuple[int, int], 
                      boundary: List[Tuple[int, int]]) -> float:
    """
    Compute a containment score for a point relative to a boundary.
    
    Uses the Menger matrix approach:
    - Compute distances from point to all boundary points
    - If point is inside, distances are constrained (low variance relative to bbox)
    - If point is outside, distances scale with distance from boundary
    
    Returns a score: lower = more likely inside, higher = more likely outside.
    """
    if not boundary:
        return 0.0
    
    # Compute distances to boundary
    distances = []
    for bp in boundary:
        d = np.sqrt((point[0]-bp[0])**2 + (point[1]-bp[1])**2)
        distances.append(d)
    
    distances = np.array(distances)
    
    # Bounding box of boundary
    min_r = min(r for r, c in boundary)
    max_r = max(r for r, c in boundary)
    min_c = min(c for r, c in boundary)
    max_c = max(c for r, c in boundary)
    
    bbox_diag = np.sqrt((max_r - min_r)**2 + (max_c - min_c)**2)
    
    if bbox_diag == 0:
        return 0.0
    
    # Normalize distances by bbox diagonal
    norm_dists = distances / bbox_diag
    
    # Inside points have low max distance and low variance
    # Outside points have high max distance or high variance
    score = np.max(norm_dists) + np.std(norm_dists)
    
    return score


def detect_frame_interior(grid: Grid, frame_colour: int) -> List[Tuple[int, int]]:
    """
    Detect interior cells of a hollow frame.
    
    Uses Menger-based containment:
    1. Find boundary cells of the frame
    2. For each non-frame cell, compute containment score
    3. Interior cells have low containment scores
    """
    h, w = grid.height, grid.width
    
    # Find frame cells
    frame_cells = []
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == frame_colour:
                frame_cells.append((r, c))
    
    if not frame_cells:
        return []
    
    # Find boundary of frame (frame cells with non-frame neighbours)
    boundary = []
    for r, c in frame_cells:
        has_non_frame_neighbour = False
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if (0 <= nr < h and 0 <= nc < w 
                and grid.cells[nr][nc] != frame_colour):
                has_non_frame_neighbour = True
                break
        if has_non_frame_neighbour:
            boundary.append((r, c))
    
    if not boundary:
        return []
    
    # Compute containment score for all non-frame cells
    interior = []
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != frame_colour:
                score = containment_score((r, c), boundary)
                # Interior cells have low score
                if score < 0.5:  # Threshold
                    interior.append((r, c))
    
    return interior


# ═══════════════════════════════════════════════════════════════════
# 5. PREDICTION: MENGER-BASED RULES
# ═══════════════════════════════════════════════════════════════════

def try_menger_containment(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Try to solve tasks using Menger-based containment detection.
    
    Pattern: find hollow frames, fill interior with a colour.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Find colours that form frames
    all_cols = set()
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                all_cols.add(pair.input.cells[r][c])
    
    for frame_col in all_cols:
        if frame_col == 0:
            continue
        
        # Check if this colour forms a frame in train pairs
        frame_detected = False
        interior_colours = []
        
        for pair in task.train:
            interior = detect_frame_interior(pair.input, frame_col)
            if interior:
                frame_detected = True
                # What colour does the interior become?
                for r, c in interior:
                    oc = pair.output.cells[r][c]
                    if pair.input.cells[r][c] != oc:
                        interior_colours.append(oc)
        
        if not frame_detected or not interior_colours:
            continue
        
        # Determine fill colour
        fill_counter = Counter(interior_colours)
        fill = fill_counter.most_common(1)[0][0]
        
        # Verify on train
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            interior = detect_frame_interior(pair.input, frame_col)
            
            cells = [row[:] for row in pair.input.cells]
            for r, c in interior:
                if cells[r][c] != frame_col:
                    cells[r][c] = fill
            
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            # Apply to test
            test = task.test[0].input
            h, w = test.height, test.width
            interior = detect_frame_interior(test, frame_col)
            
            cells = [row[:] for row in test.cells]
            for r, c in interior:
                if cells[r][c] != frame_col:
                    cells[r][c] = fill
            
            pred = Grid(cells)
            return pred, f"menger_contain_{frame_col}_to_{fill}"
    
    return None


def try_menger_object_identity(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Try to solve tasks using Menger-based object identity.
    
    Pattern: objects with the same Menger hash get the same transformation.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # For each train pair, compute object hashes and their transformations
    hash_transforms = {}  # hash → (input_colour, output_colour)
    
    for pair in task.train:
        objects = find_objects(pair.input)
        
        for col, components in objects.items():
            for comp in components:
                h = menger_hash(comp)
                
                # What does this object become in the output?
                output_cols = set()
                for r, c in comp:
                    output_cols.add(pair.output.cells[r][c])
                
                if len(output_cols) == 1:
                    oc = list(output_cols)[0]
                    if h in hash_transforms:
                        if hash_transforms[h] != (col, oc):
                            hash_transforms[h] = None  # Inconsistent
                    else:
                        hash_transforms[h] = (col, oc)
    
    # Filter out inconsistent hashes
    hash_transforms = {h: t for h, t in hash_transforms.items() if t is not None}
    
    if not hash_transforms:
        return None
    
    # Check if this explains all changes
    all_pass = True
    for pair in task.train:
        objects = find_objects(pair.input)
        cells = [row[:] for row in pair.input.cells]
        
        for col, components in objects.items():
            for comp in components:
                h = menger_hash(comp)
                if h in hash_transforms:
                    _, oc = hash_transforms[h]
                    for r, c in comp:
                        cells[r][c] = oc
        
        if not grids_equal(Grid(cells), pair.output):
            all_pass = False
            break
    
    if all_pass:
        test = task.test[0].input
        objects = find_objects(test)
        cells = [row[:] for row in test.cells]
        
        for col, components in objects.items():
            for comp in components:
                h = menger_hash(comp)
                if h in hash_transforms:
                    _, oc = hash_transforms[h]
                    for r, c in comp:
                        cells[r][c] = oc
        
        pred = Grid(cells)
        return pred, f"menger_identity_{len(hash_transforms)}rules"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 6. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try Menger-based approaches."""
    strategies = [
        ("menger_containment", try_menger_containment),
        ("menger_identity", try_menger_object_identity),
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
    
    print(f"\n═══ Cayley-Menger ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
