"""
v057_glm_arc_reasoning.py — Inject ARC Knowledge into GLM and Test Reasoning
=============================================================================

Injects ARC-specific concepts into the GLM's CRG and vocabulary, then tests
whether the GLM can reason about ARC tasks using Three Column Thinking.

Uses:
  - GLM24_continuous_learner.py for co-occurrence learning
  - GLM34_simplicial_crg.py for ternary relations
  - GLM36_reasoning_engine.py for pattern detection
  - GLM18_hex_colour.py for colour operations

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict
import sys, os, json, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

_GLM_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'GLM')
_CORE_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'core')
if _GLM_DIR not in sys.path:
    sys.path.insert(0, _GLM_DIR)
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# ARC KNOWLEDGE BASE — concepts, definitions, relationships
# ══════════════════════════════════════════════════════════════════════════════

ARC_CONCEPTS = {
    # Core grid concepts
    "grid": {"def": "A 2D array of integer cells (0-9) representing a visual pattern", "role": "NOUN"},
    "cell": {"def": "A single position in a grid, identified by (row, col) and a colour value 0-9", "role": "NOUN"},
    "row": {"def": "A horizontal line of cells in a grid", "role": "NOUN"},
    "column": {"def": "A vertical line of cells in a grid", "role": "NOUN"},
    "colour": {"def": "An integer value 0-9 assigned to a cell. 0 = background/black", "role": "NOUN"},
    "background": {"def": "Cells with colour 0, representing empty space", "role": "NOUN"},
    
    # Object concepts
    "object": {"def": "A connected component of non-zero cells (4-neighbour adjacency)", "role": "NOUN"},
    "connected_component": {"def": "A group of same-colour cells connected by sharing edges (up/down/left/right)", "role": "NOUN"},
    "bounding_box": {"def": "The smallest rectangle containing all cells of an object", "role": "NOUN"},
    "centroid": {"def": "The center of mass of an object (average row, average column)", "role": "NOUN"},
    "size": {"def": "The number of cells in a connected component", "role": "NOUN"},
    
    # Transformation concepts
    "fill": {"def": "Replace background (0) cells with a non-zero colour", "role": "VERB"},
    "erase": {"def": "Replace non-zero cells with background (0)", "role": "VERB"},
    "recolour": {"def": "Change one non-zero colour to another non-zero colour", "role": "VERB"},
    "swap": {"def": "Exchange two colours throughout the grid", "role": "VERB"},
    "propagate": {"def": "Spread colour from non-zero cells into adjacent zeros", "role": "VERB"},
    "extend": {"def": "Expand an object by adding cells in a direction", "role": "VERB"},
    "rotate": {"def": "Turn the grid by 90, 180, or 270 degrees", "role": "VERB"},
    "mirror": {"def": "Reflect the grid horizontally or vertically", "role": "VERB"},
    "tile": {"def": "Repeat the grid pattern to fill a larger area", "role": "VERB"},
    "crop": {"def": "Extract a sub-region of the grid", "role": "VERB"},
    
    # Pattern concepts
    "interior": {"def": "Zero cells completely surrounded by non-zero cells (not connected to border)", "role": "NOUN"},
    "enclosed": {"def": "Same as interior — zeros not reachable from the grid border", "role": "ADJ"},
    "border": {"def": "Cells on the edge of the grid (row 0, row h-1, col 0, col w-1)", "role": "NOUN"},
    "adjacent": {"def": "Cells sharing an edge (up/down/left/right, 4-neighbour)", "role": "ADJ"},
    "diagonal": {"def": "Cells sharing a corner (8-neighbour including diagonals)", "role": "ADJ"},
    
    # Conditional concepts
    "condition": {"def": "A property that determines whether a transformation applies", "role": "NOUN"},
    "threshold": {"def": "A numeric boundary that triggers a transformation", "role": "NOUN"},
    "predicate": {"def": "A test on an object property (size >= 4, colour == 2, etc.)", "role": "NOUN"},
    
    # Spatial concepts
    "gravity": {"def": "Moving all non-zero cells downward to fill gaps below them", "role": "NOUN"},
    "distance": {"def": "The number of steps between two cells (Manhattan or Chebyshev)", "role": "NOUN"},
    "direction": {"def": "A vector from one cell to another (up, down, left, right)", "role": "NOUN"},
}

ARC_RELATIONSHIPS = [
    # is-a relationships
    ("object", "is_a", "connected_component"),
    ("connected_component", "is_a", "group_of_cells"),
    ("background", "is_a", "colour"),
    ("interior", "is_a", "pattern"),
    ("predicate", "is_a", "condition"),
    
    # has-property relationships
    ("object", "has_property", "size"),
    ("object", "has_property", "colour"),
    ("object", "has_property", "centroid"),
    ("object", "has_property", "bounding_box"),
    ("grid", "has_property", "row"),
    ("grid", "has_property", "column"),
    ("cell", "has_property", "colour"),
    ("cell", "has_property", "adjacent"),
    
    # operates-on relationships
    ("fill", "operates_on", "background"),
    ("erase", "operates_on", "colour"),
    ("recolour", "operates_on", "colour"),
    ("propagate", "operates_on", "adjacent"),
    ("extend", "operates_on", "object"),
    
    # produces relationships
    ("fill", "produces", "colour"),
    ("erase", "produces", "background"),
    ("recolour", "produces", "colour"),
    ("propagate", "produces", "fill"),
    
    # requires relationships
    ("fill", "requires", "background"),
    ("erase", "requires", "colour"),
    ("recolour", "requires", "colour"),
    ("interior", "requires", "border"),
    ("connected_component", "requires", "adjacent"),
    
    # inverse relationships
    ("fill", "inverse_of", "erase"),
    ("erase", "inverse_of", "fill"),
    
    # composes relationships
    ("propagate", "composes", "fill"),
    ("extend", "composes", "fill"),
    ("tile", "composes", "grid"),
    
    # part-of relationships
    ("cell", "part_of", "row"),
    ("cell", "part_of", "column"),
    ("row", "part_of", "grid"),
    ("column", "part_of", "grid"),
    ("object", "part_of", "grid"),
]


# ══════════════════════════════════════════════════════════════════════════════
# GLM INITIALIZATION WITH ARC KNOWLEDGE
# ══════════════════════════════════════════════════════════════════════════════

def init_glm_with_arc():
    """Initialize the GLM and inject ARC-specific knowledge."""
    from GLM import GLM
    from GLM24_continuous_learner import ContinuousLearner
    
    glm = GLM()
    
    # Get the vocabulary and CRG
    vocab = glm.vocab
    crg = glm.crg
    
    # Inject ARC concepts into vocabulary
    injected = 0
    target = vocab.words if hasattr(vocab, 'words') else vocab
    
    for concept, data in ARC_CONCEPTS.items():
        if concept not in target:
            # Create a 24-bit vector from the concept name
            import hashlib
            h = hashlib.sha256(concept.encode()).digest()
            seed_bits = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
            
            from GLM01_substrate import WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category
            snapped, _ = GOLAY_ENGINE.snap_to_codeword(seed_bits)
            nrci = float(LEECH_ENGINE.calculate_nrci(snapped))
            
            target[concept] = WordEntry(
                word=concept, vector=snapped, role=data["role"],
                ubp_id=f"ARC_{concept.upper()}", nrci=nrci,
                golay_codeword=snapped, fold3=BLA.fold24_to3(snapped),
                mog_category=_get_mog_category(snapped),
            )
            injected += 1
    
    # Inject ARC relationships into CRG
    edges_added = 0
    for src, label, dst in ARC_RELATIONSHIPS:
        try:
            ok = crg.add_edge(src, label, dst)
            if ok:
                edges_added += 1
        except:
            pass
    
    # Initialize continuous learner
    learner = ContinuousLearner(vocab, crg)
    
    # Learn from ARC task descriptions
    arc_descriptions = [
        "grid transformation fill background with colour",
        "connected component object size threshold recolour",
        "erase colour replace with background zero",
        "propagate spread colour from object to adjacent zeros",
        "interior fill enclosed region not connected to border",
        "gravity move non-zero cells downward",
        "rotate grid 90 degrees clockwise",
        "mirror reflect grid horizontally",
        "swap exchange two colours throughout grid",
        "distance manhattan between cells",
        "adjacent cells sharing edge four neighbour",
        "bounding box smallest rectangle containing object",
        "centroid center of mass average row column",
        "condition predicate test object property threshold",
        "fill colour determined by position row column",
        "recolour object based on size larger than threshold",
        "tile repeat grid pattern larger area",
        "crop extract sub-region bounding box",
        "extend object expand direction outward",
        "colour distance euclidean RGB hex comparison",
    ]
    
    for desc in arc_descriptions:
        words = [w for w in desc.lower().split() if len(w) > 2]
        learner.process_query(desc, words)
    
    # Force save
    learner.state.save()
    
    print(f"[ARC] Injected {injected} concepts, {edges_added} edges")
    print(f"[ARC] Vocab: {len(target)} words, CRG: {len(crg.edges)} edges")
    
    return glm, learner


# ══════════════════════════════════════════════════════════════════════════════
# ARC TASK → NATURAL LANGUAGE DESCRIPTION
# ══════════════════════════════════════════════════════════════════════════════

def describe_task(task: ARCTask) -> str:
    """Convert an ARC task to a natural language description for the GLM."""
    pair = task.train[0]
    h, w = pair.input.height, pair.input.width
    
    # Analyse transformation
    same_size = pair.input.height == pair.output.height and pair.input.width == pair.output.width
    
    if same_size:
        fill = sum(1 for r in range(h) for c in range(w) if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0)
        erase = sum(1 for r in range(h) for c in range(w) if pair.input.cells[r][c] != 0 and pair.output.cells[r][c] == 0)
        recolour = sum(1 for r in range(h) for c in range(w) if pair.input.cells[r][c] != 0 and pair.output.cells[r][c] != 0 and pair.input.cells[r][c] != pair.output.cells[r][c])
        
        parts = []
        if fill > 0:
            fills = Counter()
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fills[pair.output.cells[r][c]] += 1
            fill_desc = ', '.join(f'colour {col} ({cnt} cells)' for col, cnt in fills.most_common(3))
            parts.append(f"fill {fill} background cells with {fill_desc}")
        if erase > 0:
            parts.append(f"erase {erase} cells to background")
        if recolour > 0:
            cmap = {}
            for r in range(h):
                for c in range(w):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic != 0 and oc != 0 and ic != oc:
                        cmap[ic] = oc
            rc_desc = ', '.join(f'{k}→{v}' for k, v in list(cmap.items())[:5])
            parts.append(f"recolour {recolour} cells: {rc_desc}")
        
        description = f"A {h}x{w} grid transformation: " + "; ".join(parts) + "."
    else:
        h2, w2 = pair.output.height, pair.output.width
        description = f"A grid transformation from {h}x{w} to {h2}x{w2} (size change)."
    
    # Add object information
    inp_objs = []
    visited = set()
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or pair.input.cells[r][c] == 0:
                continue
            colour = pair.input.cells[r][c]
            cells = set()
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in cells:
                    continue
                cells.add((cr, cc))
                visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells and pair.input.cells[nr][nc] == colour:
                        queue.append((nr, nc))
            inp_objs.append((colour, len(cells)))
    
    obj_desc = ', '.join(f'colour {c} size {s}' for c, s in inp_objs[:5])
    description += f" Input objects: {obj_desc}."
    
    return description


def describe_task_reasoning(task: ARCTask) -> str:
    """Generate a Three Column Thinking description of the task."""
    pair = task.train[0]
    h, w = pair.input.height, pair.input.width
    
    lines = []
    lines.append(f"TASK: {task.name}")
    lines.append(f"Grid: {h}x{w}")
    lines.append("")
    
    # Column 1: Language
    lines.append("=== LANGUAGE ===")
    lines.append(describe_task(task))
    lines.append("")
    
    # Column 2: Math
    lines.append("=== MATH ===")
    # Compute NRCI/TAX
    import sys
    sys.path.insert(0, _CORE_DIR)
    from ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine
    
    def mog_encode(grid):
        h, w = grid.height, grid.width
        bits = [0] * 24
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] != 0:
                    mog_r = grid.cells[r][c] % 4
                    mog_c = (r + c) % 6
                    bits[mog_r * 6 + mog_c] = 1
        return bits
    
    G = GolayCodeEngine()
    L = LeechLatticeEngine(G)
    
    in_bits = mog_encode(pair.input)
    out_bits = mog_encode(pair.output)
    in_snapped, _ = G.snap_to_codeword(in_bits)
    out_snapped, _ = G.snap_to_codeword(out_bits)
    
    in_nrci = float(L.calculate_nrci(in_snapped))
    out_nrci = float(L.calculate_nrci(out_snapped))
    delta_hw = sum(out_snapped) - sum(in_snapped)
    
    lines.append(f"Input NRCI: {in_nrci:.4f}, Output NRCI: {out_nrci:.4f}")
    lines.append(f"ΔNRCI: {out_nrci - in_nrci:+.4f}, ΔHW: {delta_hw:+d}")
    lines.append(f"Input HW: {sum(in_snapped)}, Output HW: {sum(out_snapped)}")
    lines.append("")
    
    # Column 3: Script
    lines.append("=== SCRIPT ===")
    lines.append("# Verify transformation")
    lines.append(f"assert input.shape == ({h}, {w})")
    lines.append(f"assert output.shape == ({pair.output.height}, {pair.output.width})")
    
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# GLM REASONING ON ARC TASKS
# ══════════════════════════════════════════════════════════════════════════════

def glm_reason_about_task(glm, task: ARCTask) -> Dict[str, Any]:
    """Use the GLM to reason about an ARC task."""
    description = describe_task(task)
    
    # Ask the GLM to reason about the task
    query = f"What transformation rule applies to this task? {description}"
    
    try:
        response = glm.chat(query, fresh=True)
    except Exception as e:
        response = f"Error: {e}"
    
    # Get verbose response with Three Column Thinking
    try:
        verbose = glm.chat_verbose(query, fresh=True)
    except Exception as e:
        verbose = f"Error: {e}"
    
    return {
        "task": task.name,
        "description": description,
        "response": response,
        "verbose": verbose,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--task", type=str, default=None, help="Specific task to reason about")
    p.add_argument("--inject-only", action="store_true", help="Just inject knowledge, don't reason")
    args = p.parse_args()
    
    print("═" * 60)
    print(" GLM + ARC REASONING v057")
    print("═" * 60)
    print()
    
    # Initialize GLM with ARC knowledge
    glm, learner = init_glm_with_arc()
    
    if args.inject_only:
        print("Knowledge injected. Exiting.")
        sys.exit(0)
    
    # Reason about specific task or all tasks
    if args.task:
        task = load_task(os.path.join(args.batch, args.task), name=os.path.splitext(args.task)[0])
        result = glm_reason_about_task(glm, task)
        print(f"\nTask: {result['task']}")
        print(f"Description: {result['description']}")
        print(f"\nGLM Response:")
        print(result['response'])
        print(f"\nThree Column Thinking:")
        print(result['verbose'])
    else:
        # Test on a few tasks
        tasks_dir = args.batch
        files = sorted(f for f in os.listdir(tasks_dir) if f.endswith('.json'))
        
        test_tasks = ['ae58858e.json', '00dbd492.json', '54d82841.json', 'a85d4709.json', '2bcee788.json']
        
        for fname in test_tasks:
            if fname not in files:
                continue
            task = load_task(os.path.join(tasks_dir, fname), name=os.path.splitext(fname)[0])
            result = glm_reason_about_task(glm, task)
            
            print(f"\n{'─' * 60}")
            print(f"Task: {result['task']}")
            print(f"Description: {result['description']}")
            print(f"\nGLM Response (first 500 chars):")
            print(result['response'][:500])
            print()
