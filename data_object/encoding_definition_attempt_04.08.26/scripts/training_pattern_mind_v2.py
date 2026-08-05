"""
training_pattern_mind_v2.py — Pattern Mind Using Trained Substrate Knowledge

Does the element/geometry training help with pattern solving?
Loads long_term_memory/ data and uses substrate metrics to:
1. Classify patterns (using NRCI, compactness, AND encoding)
2. Generate candidates (using driving styles from README)
3. Evaluate candidates (using TAX minimisation, NRCI maximisation)
4. Track benchmarks across runs
"""

from __future__ import annotations
import sys, json, math, time, random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
LTM_DIR = SCRIPT_DIR.parent.parent / "long_term_memory"
sys.path.insert(0, str(SCRIPT_DIR))

Y = 0.2646754304045269672

try:
    import ubp_unified_v5 as ubp
    GOLAY = ubp.GOLAY_ENGINE
    HAS_GOLAY = True
except:
    HAS_GOLAY = False


# ═══════════════════════════════════════════════════════════════════════════════
# Load trained substrate knowledge
# ═══════════════════════════════════════════════════════════════════════════════

def load_trained_knowledge():
    """Load what the mind learned from elements/geometry training."""
    knowledge = {}

    # Element encodings
    elem_path = LTM_DIR / "element_encodings.json"
    if elem_path.exists():
        with open(elem_path) as f:
            knowledge["elements"] = json.load(f)

    # Bond encodings
    bond_path = LTM_DIR / "bond_encodings.json"
    if bond_path.exists():
        with open(bond_path) as f:
            knowledge["bonds"] = json.load(f)

    # Learned patterns
    patterns_path = LTM_DIR / "learned_patterns.json"
    if patterns_path.exists():
        with open(patterns_path) as f:
            knowledge["patterns"] = json.load(f)

    # Experience
    exp_path = LTM_DIR / "experience.json"
    if exp_path.exists():
        with open(exp_path) as f:
            knowledge["experience"] = json.load(f)

    return knowledge


# ═══════════════════════════════════════════════════════════════════════════════
# Grid → Data Object (using trained encoding principles)
# ═══════════════════════════════════════════════════════════════════════════════

def grid_to_do(grid: List[List[int]]) -> List[int]:
    """Encode grid as 24-bit Data Object using trained principles."""
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]

    # Row 0 (Reality): colour presence
    cc = Counter(flat)
    top6 = [c for c, _ in cc.most_common(6)]
    row0 = [1 if i < len(top6) and top6[i] != 0 else 0 for i in range(6)]

    # Row 1 (Info): structural flags
    has_border = any(grid[0][c] != 0 for c in range(w)) or any(grid[h-1][c] != 0 for c in range(w))
    has_interior = any(grid[r][c] != 0 for r in range(1, h-1) for c in range(1, w-1)) if h > 2 and w > 2 else False
    h_sym = all(grid[r] == grid[h-1-r] for r in range(h//2))
    v_sym = all(grid[r][c] == grid[r][w-1-c] for r in range(h) for c in range(w//2))
    density = sum(1 for v in flat if v != 0) / max(len(flat), 1)
    row1 = [int(has_border), int(has_interior), int(density > 0.5), int(h_sym), int(v_sym), int(h == w)]

    # Row 2 (Activation): complexity
    n_col = len(set(flat)) - (1 if 0 in flat else 0)
    row2_val = min(n_col * 8, 63)
    row2 = [(row2_val >> (5-i)) & 1 for i in range(6)]

    # Row 3 (Potential): size
    row3_val = min(h * 4 + w, 63)
    row3 = [(row3_val >> (5-i)) & 1 for i in range(6)]

    return row0 + row1 + row2 + row3


def do_metrics(vec: List[int]) -> Dict:
    hw = sum(vec)
    tax = hw * Y + sum(v*v for v in vec) / 8.0
    nrci = 10.0 / (10.0 + tax)
    return {"hw": hw, "nrci": nrci, "tax": tax}


def do_and(a, b): return [a[i] & b[i] for i in range(24)]
def do_xor(a, b): return [a[i] ^ b[i] for i in range(24)]


def golay_snap(vec):
    if HAS_GOLAY:
        s, _ = GOLAY.snap_to_codeword(vec)
        return s
    return vec[:]


# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced Pattern Mind — uses substrate knowledge
# ═══════════════════════════════════════════════════════════════════════════════

class SubstratePatternMind:
    """Pattern mind that uses trained substrate knowledge."""

    def __init__(self):
        self.knowledge = load_trained_knowledge()
        self.style_scores = {
            "machining": 0, "resonant": 0, "differential": 0,
            "geodesic": 0, "entropic": 0, "flow": 0,
        }
        self.n_runs = 0

        # Load learned patterns
        self.learned = {}
        if "patterns" in self.knowledge:
            for p in self.knowledge["patterns"].get("patterns", []):
                self.learned[p["id"]] = p

        # Substrate thresholds from training
        self.and_nrci_high = 0.80  # from bond training: high overlap
        self.and_nrci_low = 0.65   # from bond training: low overlap
        self.nrci_vacuum = 1.0     # from element training: noble gas

    def perceive(self, inp, out) -> Dict:
        """Enhanced perception using substrate metrics."""
        ih, iw = len(inp), len(inp[0])
        oh, ow = len(out), len(out[0])

        # Data Object encoding
        inp_do = grid_to_do(inp)
        out_do = grid_to_do(out)

        # AND encoding (shared structure — from bond training)
        and_vec = do_and(inp_do, out_do)
        and_m = do_metrics(and_vec)

        # XOR encoding (difference)
        xor_vec = do_xor(inp_do, out_do)
        xor_m = do_metrics(xor_vec)

        # Golay snap costs (from training: pre-snap > post-snap)
        inp_snap = golay_snap(inp_do)
        out_snap = golay_snap(out_do)
        inp_bits_changed = sum(1 for i in range(24) if inp_do[i] != inp_snap[i])
        out_bits_changed = sum(1 for i in range(24) if out_do[i] != out_snap[i])

        # Colour analysis
        in_flat = [v for row in inp for v in row]
        out_flat = [v for row in out for v in row]
        in_colours = set(in_flat)
        out_colours = set(out_flat)

        # Density (from element training: density correlates with NRCI)
        in_density = sum(1 for v in in_flat if v != 0) / max(len(in_flat), 1)
        out_density = sum(1 for v in out_flat if v != 0) / max(len(out_flat), 1)

        # Symmetry
        h_sym = all(inp[r] == inp[ih-1-r] for r in range(ih//2))
        v_sym = all(inp[r][c] == inp[r][iw-1-c] for r in range(ih) for c in range(iw//2))

        # Change
        size_changed = (ih != oh or iw != ow)
        if not size_changed:
            n_changed = sum(1 for r in range(ih) for c in range(iw) if inp[r][c] != out[r][c])
            pct_changed = n_changed / max(ih*iw, 1)
        else:
            n_changed = -1
            pct_changed = -1

        return {
            "ih": ih, "iw": iw, "oh": oh, "ow": ow,
            "size_changed": size_changed,
            "n_changed": n_changed,
            "pct_changed": round(pct_changed, 3),
            "in_colours": sorted(in_colours),
            "out_colours": sorted(out_colours),
            "new_colours": sorted(out_colours - in_colours),
            "removed_colours": sorted(in_colours - out_colours),
            "in_density": round(in_density, 3),
            "out_density": round(out_density, 3),
            "h_sym": h_sym, "v_sym": v_sym,
            # Substrate metrics (from training)
            "and_nrci": and_m["nrci"],
            "and_hw": and_m["hw"],
            "xor_hw": xor_m["hw"],
            "inp_nrci": do_metrics(inp_do)["nrci"],
            "out_nrci": do_metrics(out_do)["nrci"],
            "delta_nrci": do_metrics(out_do)["nrci"] - do_metrics(inp_do)["nrci"],
            "inp_bits_changed": inp_bits_changed,
            "out_bits_changed": out_bits_changed,
        }

    def classify_style(self, p: Dict) -> str:
        """Classify using substrate metrics + heuristics."""
        # Size change → resonant (tile) or machining (crop)
        if p["size_changed"]:
            if p["oh"] > p["ih"] or p["ow"] > p["iw"]:
                return "resonant"
            else:
                return "machining"

        # High AND_NRCI → lots of shared structure → differential (small change)
        if p["and_nrci"] > self.and_nrci_high:
            if p["pct_changed"] < 0.3:
                return "entropic"  # small change, high overlap = simplification
            return "differential"  # small change = colour/position shift

        # Low AND_NRCI → little shared → flow (complete transformation)
        if p["and_nrci"] < self.and_nrci_low:
            return "flow"

        # XOR_HW = 0 → invisible → geodesic (rotation preserves encoding)
        if p["xor_hw"] == 0:
            return "geodesic"

        # Symmetry present → geodesic
        if p["h_sym"] or p["v_sym"]:
            return "geodesic"

        # Colour changes → differential
        if p["new_colours"] or p["removed_colours"]:
            return "differential"

        # Density change → flow or entropic
        if p["out_density"] > p["in_density"]:
            return "flow"
        if p["out_density"] < p["in_density"]:
            return "entropic"

        return "differential"

    def generate(self, inp, style: str) -> List[Tuple[str, List]]:
        """Generate candidates using driving style."""
        ih, iw = len(inp), len(inp[0])
        candidates = []

        if style == "machining":
            # Interior extraction
            if ih > 2 and iw > 2:
                out = [[0]*iw for _ in range(ih)]
                for r in range(1, ih-1):
                    for c in range(1, iw-1):
                        out[r][c] = inp[r][c]
                candidates.append(("interior", out))

            # Keep unique
            counts = Counter(v for row in inp for v in row)
            rarest = min((v for v in counts if v != 0), key=lambda v: counts[v], default=0)
            if rarest:
                out = [[v if v == rarest else 0 for v in row] for row in inp]
                candidates.append(("keep_rarest", out))

            # Crop center
            if ih > 2 and iw > 2:
                out = [row[1:-1] for row in inp[1:-1]]
                candidates.append(("crop_center", out))

            # Crop top-left
            if ih > 1 and iw > 1:
                out = [row[:iw//2] for row in inp[:ih//2]]
                candidates.append(("crop_tl", out))

        elif style == "resonant":
            # Tile 2x
            out = [[inp[r % ih][c % iw] for c in range(iw*2)] for r in range(ih*2)]
            candidates.append(("tile_2x", out))

            # Tile 3x
            out = [[inp[r % ih][c % iw] for c in range(iw*3)] for r in range(ih*3)]
            candidates.append(("tile_3x", out))

            # Tile 4x
            out = [[inp[r % ih][c % iw] for c in range(iw*4)] for r in range(ih*4)]
            candidates.append(("tile_4x", out))

        elif style == "differential":
            # Swap colours
            flat = [v for row in inp for v in row]
            non_zero = sorted(set(v for v in flat if v != 0))
            if len(non_zero) >= 2:
                mapping = {non_zero[0]: non_zero[1], non_zero[1]: non_zero[0]}
                out = [[mapping.get(v, v) for v in row] for row in inp]
                candidates.append(("swap_colours", out))

            # Map each colour to next
            if len(non_zero) >= 2:
                mapping = {non_zero[i]: non_zero[(i+1) % len(non_zero)] for i in range(len(non_zero))}
                out = [[mapping.get(v, v) for v in row] for row in inp]
                candidates.append(("rotate_colours", out))

            # Reverse rows
            candidates.append(("reverse_rows", inp[::-1]))

            # Reverse cols
            candidates.append(("reverse_cols", [row[::-1] for row in inp]))

            # Shift right
            out = [[0]*iw for _ in range(ih)]
            for r in range(ih):
                for c in range(1, iw):
                    out[r][c] = inp[r][c-1]
            candidates.append(("shift_right", out))

            # Shift down
            out = [[0]*iw for _ in range(ih)]
            for r in range(1, ih):
                for c in range(iw):
                    out[r][c] = inp[r-1][c]
            candidates.append(("shift_down", out))

            # Diagonal shift
            out = [[0]*iw for _ in range(ih)]
            for r in range(1, ih):
                for c in range(1, iw):
                    out[r][c] = inp[r-1][c-1]
            candidates.append(("shift_diag", out))

            # Fill colour: replace 0 with most common non-zero
            if non_zero:
                mc = Counter(non_zero).most_common(1)[0][0]
                out = [[v if v != 0 else mc for v in row] for row in inp]
                candidates.append(("fill_zeros", out))

        elif style == "geodesic":
            # Mirror H
            candidates.append(("mirror_h", [row[::-1] for row in inp]))

            # Mirror V
            candidates.append(("mirror_v", inp[::-1]))

            # Rotate 90
            out = [[inp[ih-1-c][r] for c in range(ih)] for r in range(iw)]
            candidates.append(("rotate_90", out))

            # Rotate 180
            out = [row[::-1] for row in inp[::-1]]
            candidates.append(("rotate_180", out))

            # Transpose
            out = [[inp[c][r] for c in range(ih)] for r in range(iw)]
            candidates.append(("transpose", out))

        elif style == "entropic":
            # Keep center only
            out = [[0]*iw for _ in range(ih)]
            out[ih//2][iw//2] = inp[ih//2][iw//2]
            candidates.append(("center_only", out))

            # Remove background (keep non-zero)
            out = [[v if v != 0 else 0 for v in row] for row in inp]
            candidates.append(("remove_bg", out))

            # Keep most common non-zero
            flat = [v for row in inp for v in row if v != 0]
            if flat:
                mc = Counter(flat).most_common(1)[0][0]
                out = [[v if v == mc else 0 for v in row] for row in inp]
                candidates.append(("keep_mc", out))

            # Remove border
            out = [row[:] for row in inp]
            for c in range(iw):
                out[0][c] = 0
                out[ih-1][c] = 0
            for r in range(ih):
                out[r][0] = 0
                out[r][iw-1] = 0
            candidates.append(("remove_border", out))

        elif style == "flow":
            # Flood fill with first non-zero
            fill = None
            for r in range(ih):
                for c in range(iw):
                    if inp[r][c] != 0:
                        fill = inp[r][c]
                        break
                if fill:
                    break
            if fill:
                out = [[fill]*iw for _ in range(ih)]
                candidates.append(("flood_fill", out))

            # Fill with most common
            flat = [v for row in inp for v in row]
            mc = Counter(flat).most_common(1)[0][0]
            out = [[mc]*iw for _ in range(ih)]
            candidates.append(("fill_mc", out))

        return candidates

    def evaluate(self, candidate, inp, target) -> Dict:
        """Evaluate using substrate metrics."""
        exact = (candidate == target)

        if len(candidate) == len(target) and len(candidate[0]) == len(target[0]):
            total = len(target) * len(target[0])
            correct = sum(1 for r in range(len(target)) for c in range(len(target[0]))
                         if candidate[r][c] == target[r][c])
            accuracy = correct / max(total, 1)
        else:
            accuracy = 0

        # Substrate evaluation (from README: minimise TAX)
        cand_do = grid_to_do(candidate)
        target_do = grid_to_do(target)
        cand_m = do_metrics(cand_do)
        target_m = do_metrics(target_do)
        tax_delta = abs(cand_m["tax"] - target_m["tax"])

        # AND between candidate and target (should be high if correct)
        and_vec = do_and(cand_do, target_do)
        and_m = do_metrics(and_vec)

        return {
            "exact": exact,
            "accuracy": round(accuracy, 4),
            "tax_delta": round(tax_delta, 4),
            "and_nrci_with_target": round(and_m["nrci"], 4),
        }

    def solve(self, inp, out) -> Tuple:
        """Solve a pattern."""
        percept = self.perceive(inp, out)
        style = self.classify_style(percept)
        candidates = self.generate(inp, style)

        best = None
        best_ev = None

        for name, cand in candidates:
            ev = self.evaluate(cand, inp, out)
            if ev["exact"]:
                return cand, style, {"candidate": name, **ev}
            if best_ev is None or ev["accuracy"] > best_ev["accuracy"]:
                best = (name, cand)
                best_ev = ev

        if best_ev:
            self.style_scores[style] = self.style_scores.get(style, 0) + (1 if best_ev["exact"] else 0)

        return None, style, {"candidate": best[0] if best else "none", **(best_ev or {})}


# ═══════════════════════════════════════════════════════════════════════════════
# Pattern Library (same as v1 + new patterns)
# ═══════════════════════════════════════════════════════════════════════════════

PATTERNS = [
    ("mach_01", "machining", [[1,0,0],[0,0,0],[0,0,1]], [[1,0,0],[0,0,0],[0,0,1]], "Identity"),
    ("mach_02", "machining", [[1,1,1],[1,0,1],[1,1,1]], [[0,0,0],[0,1,0],[0,0,0]], "Keep interior"),
    ("mach_03", "machining", [[2,2,2],[2,3,2],[2,2,2]], [[0,0,0],[0,3,0],[0,0,0]], "Keep unique"),
    ("reso_01", "resonant", [[1,0],[0,0]], [[1,0,1,0],[0,0,0,0],[1,0,1,0],[0,0,0,0]], "Tile 2→4"),
    ("reso_02", "resonant", [[1,2],[3,4]], [[1,2,1,2],[3,4,3,4],[1,2,1,2],[3,4,3,4]], "Tile 2→4 pattern"),
    ("reso_03", "resonant", [[1,0,0],[0,1,0],[0,0,1]], [[1,0,0,1,0,0],[0,1,0,0,1,0],[0,0,1,0,0,1],[1,0,0,1,0,0],[0,1,0,0,1,0],[0,0,1,0,0,1]], "Tile 3→6"),
    ("diff_01", "differential", [[1,0,0],[0,0,0],[0,0,0]], [[0,0,0],[0,0,0],[0,0,1]], "Move TL→BR"),
    ("diff_02", "differential", [[1,0,0],[1,0,0],[1,0,0]], [[0,0,1],[0,0,1],[0,0,1]], "Move col L→R"),
    ("diff_03", "differential", [[1,1,0],[1,1,0],[0,0,0]], [[0,0,0],[0,1,1],[0,1,1]], "Move block"),
    ("diff_04", "differential", [[2,0,0],[0,0,0],[0,0,0]], [[0,0,2],[0,0,0],[0,0,0]], "Move pixel"),
    ("geo_01", "geodesic", [[1,0,0],[1,0,0],[1,0,0]], [[0,0,1],[0,0,1],[0,0,1]], "Mirror H"),
    ("geo_02", "geodesic", [[1,1,1],[0,0,0],[0,0,0]], [[0,0,0],[0,0,0],[1,1,1]], "Mirror V"),
    ("geo_03", "geodesic", [[1,0,0],[0,1,0],[0,0,1]], [[0,0,1],[0,1,0],[1,0,0]], "Anti-diag"),
    ("geo_04", "geodesic", [[1,0],[0,0]], [[0,1],[0,0]], "Rotate 90"),
    ("geo_05", "geodesic", [[1,0,0],[0,0,0],[0,0,0]], [[0,0,0],[0,0,0],[0,0,1]], "Rotate 180"),
    ("entr_01", "entropic", [[1,2,1],[2,3,2],[1,2,1]], [[0,0,0],[0,3,0],[0,0,0]], "Keep center"),
    ("entr_02", "entropic", [[5,5,5],[5,1,5],[5,5,5]], [[0,0,0],[0,1,0],[0,0,0]], "Remove bg"),
    ("entr_03", "entropic", [[1,0,2],[0,3,0],[4,0,5]], [[0,0,0],[0,3,0],[0,0,0]], "Center only"),
    ("flow_01", "flow", [[1,0,0],[0,0,0],[0,0,0]], [[1,1,1],[1,1,1],[1,1,1]], "Flood fill"),
    ("flow_02", "flow", [[0,0,0],[0,1,0],[0,0,0]], [[1,1,1],[1,1,1],[1,1,1]], "Expand fill"),
    ("flow_03", "flow", [[2,0,0],[0,0,0],[0,0,3]], [[2,2,2],[2,2,2],[2,2,2]], "Fill first"),
    ("cmap_01", "differential", [[1,2,3],[1,2,3],[1,2,3]], [[3,2,1],[3,2,1],[3,2,1]], "Reverse colours"),
    ("cmap_02", "differential", [[1,0,2],[0,0,0],[2,0,1]], [[2,0,1],[0,0,0],[1,0,2]], "Swap 1↔2"),
    ("cmap_03", "differential", [[1,1,0],[1,0,1],[0,1,1]], [[2,2,0],[2,0,2],[0,2,2]], "Map 1→2"),
    ("size_01", "resonant", [[1,2],[3,4]], [[1,2,1,2],[3,4,3,4],[1,2,1,2],[3,4,3,4]], "Tile 2→4"),
    ("size_02", "machining", [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]], [[1,2],[5,6]], "Crop TL"),
    ("size_03", "machining", [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]], [[6,7],[10,11]], "Crop center"),
    ("obj_01", "entropic", [[1,0,2],[0,0,0],[3,0,4]], [[4,0,3],[0,0,0],[2,0,1]], "Swap diagonal"),
    ("obj_02", "differential", [[1,1,0],[1,1,0],[0,0,2]], [[2,2,0],[2,2,0],[0,0,1]], "Swap obj colours"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark Tracker
# ═══════════════════════════════════════════════════════════════════════════════

class Benchmark:
    def __init__(self):
        self.history = []
        self.load()

    def load(self):
        path = LTM_DIR / "pattern_benchmark.json"
        if path.exists():
            with open(path) as f:
                self.history = json.load(f).get("runs", [])

    def record(self, run_id, n_solved, n_total, style_scores, details):
        self.history.append({
            "run": run_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "n_solved": n_solved,
            "n_total": n_total,
            "pct": round(100*n_solved/n_total, 1),
            "style_scores": style_scores,
        })
        self.save()

    def save(self):
        path = LTM_DIR / "pattern_benchmark.json"
        with open(path, "w") as f:
            json.dump({"runs": self.history}, f, indent=2)

    def print_history(self):
        print(f"\n  Benchmark History ({len(self.history)} runs):")
        print(f"  {'Run':4s} {'Solved':7s} {'Pct':6s} {'Styles'}")
        for r in self.history[-5:]:
            styles = ", ".join(f"{k}:{v}" for k, v in r.get("style_scores", {}).items() if v > 0)
            print(f"  {r['run']:4d} {r['n_solved']}/{r['n_total']:3d} {r['pct']:5.1f}% {styles}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    print("=" * 70)
    print("PATTERN MIND v2 — Using Trained Substrate Knowledge")
    print("=" * 70)

    mind = SubstratePatternMind()
    bench = Benchmark()

    print(f"Knowledge loaded:")
    if "elements" in mind.knowledge:
        print(f"  Elements: {mind.knowledge['elements']['n_elements']}")
    if "bonds" in mind.knowledge:
        print(f"  Bonds: {mind.knowledge['bonds']['n_bonds']}")
    if "patterns" in mind.knowledge:
        print(f"  Learned patterns: {len(mind.knowledge['patterns'].get('patterns', []))}")
    print(f"  Past benchmark runs: {len(bench.history)}")
    print(f"  Patterns to solve: {len(PATTERNS)}")
    print()

    results = []
    for name, expected_style, inp, out, desc in PATTERNS:
        solution, style, ev = mind.solve(inp, out)
        success = solution is not None

        results.append({
            "name": name, "expected": expected_style, "actual": style,
            "style_ok": style == expected_style, "success": success,
            "accuracy": ev.get("accuracy", 0), "candidate": ev.get("candidate", "?"),
        })

        s = "✓" if success else "✗"
        sm = "==" if style == expected_style else "!="
        print(f"  {name:10s} {s} {style:12s} {sm} {expected_style:12s} "
              f"acc={ev.get('accuracy',0):.2f} cand={ev.get('candidate','?'):15s} | {desc}")

    n_solved = sum(1 for r in results if r["success"])
    n_style = sum(1 for r in results if r["style_ok"])

    print(f"\n{'='*70}")
    print(f"SOLVED: {n_solved}/{len(results)} ({100*n_solved/len(results):.0f}%)")
    print(f"STYLE MATCH: {n_style}/{len(results)} ({100*n_style/len(results):.0f}%)")
    print(f"{'='*70}")

    # Style breakdown
    for style in ["machining", "resonant", "differential", "geodesic", "entropic", "flow"]:
        tried = sum(1 for r in results if r["actual"] == style)
        ok = sum(1 for r in results if r["actual"] == style and r["success"])
        if tried > 0:
            print(f"  {style:15s}: {ok}/{tried}")

    # Benchmark
    run_id = len(bench.history) + 1
    bench.record(run_id, n_solved, len(results), mind.style_scores, results)
    bench.print_history()

    # Save detailed results
    out_path = LTM_DIR / "pattern_v2_run_latest.json"
    with open(out_path, "w") as f:
        json.dump({"n_solved": n_solved, "n_total": len(results), "results": results}, f, indent=2)
    print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    run()
