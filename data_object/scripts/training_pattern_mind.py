"""
training_pattern_mind.py — Training the GLM to Solve Patterns From Within

The mind doesn't use external solvers. It:
1. Perceives a pattern (input → output transformation)
2. Classifies the driving style (Machining, Resonant, Differential, Geodesic, Entropic, Flow)
3. Generates candidate transformations using the substrate
4. Evaluates candidates using TAX/NRCI (Substrate Evaluator)
5. Gets yes/no feedback on its guesses
6. Accumulates experience: pattern signature → working style

This is the GLM learning to think, not to look up rules.
"""

from __future__ import annotations
import sys, json, math, time, random
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
LTM_DIR = SCRIPT_DIR.parent / "long_term_memory"
sys.path.insert(0, str(SCRIPT_DIR / "data_object" / "scripts"))

Y = 0.2646754304045269672

try:
    import ubp_unified_v5 as ubp
    GOLAY = ubp.GOLAY_ENGINE
    HAS_GOLAY = True
except:
    HAS_GOLAY = False


# ═══════════════════════════════════════════════════════════════════════════════
# Synthetic Pattern Library — designed training problems
# ═══════════════════════════════════════════════════════════════════════════════

def make_grid(cells): return cells
def grid_h(g): return len(g)
def grid_w(g): return len(g[0])

PATTERN_LIBRARY = [
    # Each: (name, driving_style, input_grid, output_grid, description)
    # ─── Machining (Reduce to essence) ───
    ("mach_01", "machining",
     [[1,0,0],[0,0,0],[0,0,1]],
     [[1,0,0],[0,0,0],[0,0,1]],
     "Identity — already minimal"),

    ("mach_02", "machining",
     [[1,1,1],[1,0,1],[1,1,1]],
     [[0,0,0],[0,1,0],[0,0,0]],
     "Keep only interior"),

    ("mach_03", "machining",
     [[2,2,2],[2,3,2],[2,2,2]],
     [[0,0,0],[0,3,0],[0,0,0]],
     "Keep only unique cell"),

    # ─── Resonant (Pattern repetition) ───
    ("reso_01", "resonant",
     [[1,0],[0,0]],
     [[1,0,1,0],[0,0,0,0],[1,0,1,0],[0,0,0,0]],
     "Tile 2x2 → 4x4"),

    ("reso_02", "resonant",
     [[1,2],[3,4]],
     [[1,2,1,2],[3,4,3,4],[1,2,1,2],[3,4,3,4]],
     "Tile 2x2 → 4x4 preserving pattern"),

    ("reso_03", "resonant",
     [[1,0,0],[0,1,0],[0,0,1]],
     [[1,0,0,1,0,0],[0,1,0,0,1,0],[0,0,1,0,0,1],[1,0,0,1,0,0],[0,1,0,0,1,0],[0,0,1,0,0,1]],
     "Tile 3x3 → 6x6 diagonal"),

    # ─── Differential (Transform the difference) ───
    ("diff_01", "differential",
     [[1,0,0],[0,0,0],[0,0,0]],
     [[0,0,0],[0,0,0],[0,0,1]],
     "Move object: top-left → bottom-right"),

    ("diff_02", "differential",
     [[1,0,0],[1,0,0],[1,0,0]],
     [[0,0,1],[0,0,1],[0,0,1]],
     "Move column: left → right"),

    ("diff_03", "differential",
     [[1,1,0],[1,1,0],[0,0,0]],
     [[0,0,0],[0,1,1],[0,1,1]],
     "Move block: top-left → bottom-right"),

    ("diff_04", "differential",
     [[2,0,0],[0,0,0],[0,0,0]],
     [[0,0,2],[0,0,0],[0,0,0]],
     "Move pixel: left → right (row 0)"),

    # ─── Geodesic (Rotation/Reflection) ───
    ("geo_01", "geodesic",
     [[1,0,0],[1,0,0],[1,0,0]],
     [[0,0,1],[0,0,1],[0,0,1]],
     "Horizontal mirror"),

    ("geo_02", "geodesic",
     [[1,1,1],[0,0,0],[0,0,0]],
     [[0,0,0],[0,0,0],[1,1,1]],
     "Vertical mirror"),

    ("geo_03", "geodesic",
     [[1,0,0],[0,1,0],[0,0,1]],
     [[0,0,1],[0,1,0],[1,0,0]],
     "Anti-diagonal mirror"),

    ("geo_04", "geodesic",
     [[1,0],[0,0]],
     [[0,1],[0,0]],
     "Rotate 90° CW"),

    ("geo_05", "geodesic",
     [[1,0,0],[0,0,0],[0,0,0]],
     [[0,0,0],[0,0,0],[0,0,1]],
     "Rotate 180°"),

    # ─── Entropic (Simplify / Remove noise) ───
    ("entr_01", "entropic",
     [[1,2,1],[2,3,2],[1,2,1]],
     [[0,0,0],[0,3,0],[0,0,0]],
     "Remove all but center"),

    ("entr_02", "entropic",
     [[5,5,5],[5,1,5],[5,5,5]],
     [[0,0,0],[0,1,0],[0,0,0]],
     "Remove background, keep unique"),

    ("entr_03", "entropic",
     [[1,0,2],[0,3,0],[4,0,5]],
     [[0,0,0],[0,3,0],[0,0,0]],
     "Keep only center cell"),

    # ─── Flow (Expand / Fill) ───
    ("flow_01", "flow",
     [[1,0,0],[0,0,0],[0,0,0]],
     [[1,1,1],[1,1,1],[1,1,1]],
     "Flood fill from top-left"),

    ("flow_02", "flow",
     [[0,0,0],[0,1,0],[0,0,0]],
     [[1,1,1],[1,1,1],[1,1,1]],
     "Expand center to fill all"),

    ("flow_03", "flow",
     [[2,0,0],[0,0,0],[0,0,3]],
     [[2,2,2],[2,2,2],[2,2,2]],
     "Flood fill with first colour"),

    # ─── Colour mapping ───
    ("cmap_01", "differential",
     [[1,2,3],[1,2,3],[1,2,3]],
     [[3,2,1],[3,2,1],[3,2,1]],
     "Reverse colour order"),

    ("cmap_02", "differential",
     [[1,0,2],[0,0,0],[2,0,1]],
     [[2,0,1],[0,0,0],[1,0,2]],
     "Swap colours 1↔2"),

    ("cmap_03", "differential",
     [[1,1,0],[1,0,1],[0,1,1]],
     [[2,2,0],[2,0,2],[0,2,2]],
     "Map 1→2, keep 0"),

    # ─── Size change ───
    ("size_01", "machining",
     [[1,2],[3,4]],
     [[1,2,1,2],[3,4,3,4],[1,2,1,2],[3,4,3,4]],
     "2x → 4x tile"),

    ("size_02", "machining",
     [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]],
     [[1,2],[5,6]],
     "4x → 2x crop top-left"),

    ("size_03", "machining",
     [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]],
     [[6,7],[10,11]],
     "4x → 2x crop center"),

    # ─── Object-level ───
    ("obj_01", "entropic",
     [[1,0,2],[0,0,0],[3,0,4]],
     [[4,0,3],[0,0,0],[2,0,1]],
     "Swap object positions (diagonal)"),

    ("obj_02", "differential",
     [[1,1,0],[1,1,0],[0,0,2]],
     [[2,2,0],[2,2,0],[0,0,1]],
     "Swap object colours"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# The Mind — perception, reasoning, generation, evaluation
# ═══════════════════════════════════════════════════════════════════════════════

class PatternMind:
    """The GLM mind that learns to solve patterns."""

    def __init__(self):
        self.experience = []  # list of (pattern_sig, style, success)
        self.style_scores = {
            "machining": 0, "resonant": 0, "differential": 0,
            "geodesic": 0, "entropic": 0, "flow": 0,
        }

    def perceive(self, inp: List[List[int]], out: List[List[int]]) -> Dict:
        """What does the mind see?"""
        ih, iw = grid_h(inp), grid_w(inp)
        oh, ow = grid_h(out), grid_w(out)

        # Colour analysis
        in_colours = set(v for row in inp for v in row)
        out_colours = set(v for row in out for v in row)
        new_colours = out_colours - in_colours
        removed_colours = in_colours - out_colours

        # Size change
        size_changed = (ih != oh or iw != ow)

        # Density
        in_flat = [v for row in inp for v in row]
        out_flat = [v for row in out for v in row]
        in_density = sum(1 for v in in_flat if v != 0) / max(len(in_flat), 1)
        out_density = sum(1 for v in out_flat if v != 0) / max(len(out_flat), 1)

        # Symmetry
        h_sym = all(inp[r] == inp[ih-1-r] for r in range(ih//2))
        v_sym = all(inp[r][c] == inp[r][iw-1-c] for r in range(ih) for c in range(iw//2))

        # Change analysis
        if not size_changed and ih == oh and iw == ow:
            n_changed = sum(1 for r in range(ih) for c in range(iw) if inp[r][c] != out[r][c])
            pct_changed = n_changed / max(ih*iw, 1)
        else:
            n_changed = -1
            pct_changed = -1

        return {
            "ih": ih, "iw": iw, "oh": oh, "ow": ow,
            "size_changed": size_changed,
            "in_colours": sorted(in_colours),
            "out_colours": sorted(out_colours),
            "new_colours": sorted(new_colours),
            "removed_colours": sorted(removed_colours),
            "in_density": round(in_density, 3),
            "out_density": round(out_density, 3),
            "h_sym": h_sym, "v_sym": v_sym,
            "n_changed": n_changed,
            "pct_changed": round(pct_changed, 3),
        }

    def classify_style(self, percept: Dict) -> str:
        """Which driving style fits this pattern?"""
        if percept["size_changed"]:
            if percept["oh"] > percept["ih"] or percept["ow"] > percept["iw"]:
                return "resonant"  # expansion = tiling
            else:
                return "machining"  # compression = reduction

        if percept["pct_changed"] > 0.8:
            return "flow"  # most cells changed = flood fill

        if percept["new_colours"] or percept["removed_colours"]:
            return "differential"  # colour change

        if percept["h_sym"] or percept["v_sym"]:
            return "geodesic"  # symmetric = rotation/mirror

        if percept["pct_changed"] < 0.3:
            return "entropic"  # few changes = simplification

        return "differential"  # default

    def generate(self, inp: List[List[int]], style: str) -> List[List[List[int]]]:
        """Generate candidate outputs using the driving style."""
        ih, iw = grid_h(inp), grid_w(inp)
        candidates = []

        if style == "machining":
            # Remove everything except interior
            if ih > 2 and iw > 2:
                out = [[0]*iw for _ in range(ih)]
                for r in range(1, ih-1):
                    for c in range(1, iw-1):
                        out[r][c] = inp[r][c]
                candidates.append(out)

            # Keep only unique (non-duplicate) cells
            counts = Counter(v for row in inp for v in row)
            rare = min(counts, key=lambda k: counts[k]) if counts else 0
            out = [[v if v == rare else 0 for v in row] for row in inp]
            candidates.append(out)

            # Crop center
            if ih > 2 and iw > 2:
                out = [row[1:-1] for row in inp[1:-1]]
                candidates.append(out)

        elif style == "resonant":
            # Tile 2x
            out = []
            for r in range(ih * 2):
                row = []
                for c in range(iw * 2):
                    row.append(inp[r % ih][c % iw])
                out.append(row)
            candidates.append(out)

            # Tile 3x
            out = []
            for r in range(ih * 3):
                row = []
                for c in range(iw * 3):
                    row.append(inp[r % ih][c % iw])
                out.append(row)
            candidates.append(out)

        elif style == "differential":
            # Swap colours
            flat = [v for row in inp for v in row]
            unique = sorted(set(flat))
            if len(unique) >= 2:
                # Swap first two non-zero
                non_zero = [v for v in unique if v != 0]
                if len(non_zero) >= 2:
                    mapping = {non_zero[0]: non_zero[1], non_zero[1]: non_zero[0]}
                    out = [[mapping.get(v, v) for v in row] for row in inp]
                    candidates.append(out)

            # Reverse rows
            candidates.append(inp[::-1])

            # Reverse columns
            candidates.append([row[::-1] for row in inp])

            # Move objects by shifting
            # Shift right
            out = [[0]*iw for _ in range(ih)]
            for r in range(ih):
                for c in range(iw):
                    if c > 0:
                        out[r][c] = inp[r][c-1]
            candidates.append(out)

            # Shift down
            out = [[0]*iw for _ in range(ih)]
            for r in range(ih):
                for c in range(iw):
                    if r > 0:
                        out[r][c] = inp[r-1][c]
            candidates.append(out)

        elif style == "geodesic":
            # Mirror horizontal
            candidates.append([row[::-1] for row in inp])

            # Mirror vertical
            candidates.append(inp[::-1])

            # Rotate 90 CW
            out = [[inp[ih-1-c][r] for c in range(ih)] for r in range(iw)]
            candidates.append(out)

            # Rotate 180
            out = [row[::-1] for row in inp[::-1]]
            candidates.append(out)

            # Transpose
            out = [[inp[c][r] for c in range(ih)] for r in range(iw)]
            candidates.append(out)

        elif style == "entropic":
            # Keep only center
            out = [[0]*iw for _ in range(ih)]
            out[ih//2][iw//2] = inp[ih//2][iw//2]
            candidates.append(out)

            # Keep only most common
            counts = Counter(v for row in inp for v in row)
            bg = counts.most_common(1)[0][0]
            out = [[v if v != bg else 0 for v in row] for row in inp]
            candidates.append(out)

            # Remove background
            out = [[v if v != 0 else 0 for v in row] for row in inp]
            candidates.append(out)

        elif style == "flow":
            # Flood fill from first non-zero
            out = [row[:] for row in inp]
            fill_colour = None
            for r in range(ih):
                for c in range(iw):
                    if inp[r][c] != 0:
                        fill_colour = inp[r][c]
                        break
                if fill_colour:
                    break
            if fill_colour:
                out = [[fill_colour]*iw for _ in range(ih)]
                candidates.append(out)

            # Fill with most common
            counts = Counter(v for row in inp for v in row)
            if counts:
                mc = counts.most_common(1)[0][0]
                out = [[mc]*iw for _ in range(ih)]
                candidates.append(out)

        return candidates

    def evaluate(self, candidate: List[List[int]], inp: List[List[int]], 
                 target: List[List[int]]) -> Dict:
        """Score a candidate using substrate metrics."""
        # Exact match
        exact = (candidate == target)

        # Cell accuracy
        if grid_h(candidate) == grid_h(target) and grid_w(candidate) == grid_w(target):
            total = grid_h(target) * grid_w(target)
            correct = sum(1 for r in range(grid_h(target)) for c in range(grid_w(target))
                         if candidate[r][c] == target[r][c])
            accuracy = correct / max(total, 1)
        else:
            accuracy = 0

        # TAX of input, output, candidate
        def grid_tax(g):
            flat = [v for row in g for v in row]
            hw = sum(1 for v in flat if v != 0)
            norm_sq = sum(v*v for v in flat)
            return hw * Y + norm_sq / 8.0

        def grid_nrci(g):
            tax = grid_tax(g)
            return 10.0 / (10.0 + tax)

        inp_tax = grid_tax(inp)
        target_tax = grid_tax(target)
        cand_tax = grid_tax(candidate)

        # Is the candidate closer to target TAX than input?
        tax_delta = abs(cand_tax - target_tax)
        inp_tax_delta = abs(inp_tax - target_tax)
        tax_improved = tax_delta < inp_tax_delta

        return {
            "exact": exact,
            "accuracy": round(accuracy, 4),
            "tax_delta": round(tax_delta, 4),
            "tax_improved": tax_improved,
        }

    def solve(self, inp: List[List[int]], out: List[List[int]]) -> Tuple[Optional[List[List[int]]], str, Dict]:
        """Attempt to solve a pattern."""
        percept = self.perceive(inp, out)
        style = self.classify_style(percept)
        candidates = self.generate(inp, style)

        best_candidate = None
        best_eval = None

        for cand in candidates:
            ev = self.evaluate(cand, inp, out)
            if ev["exact"]:
                return cand, style, {"style": style, "exact": True, "accuracy": 1.0}
            if best_eval is None or ev["accuracy"] > best_eval["accuracy"]:
                best_candidate = cand
                best_eval = ev

        # Record experience
        self.experience.append({
            "style": style,
            "exact": best_eval["exact"] if best_eval else False,
            "accuracy": best_eval["accuracy"] if best_eval else 0,
        })

        if best_eval and best_eval["exact"]:
            self.style_scores[style] = self.style_scores.get(style, 0) + 1

        return best_candidate if best_eval and best_eval["exact"] else None, style, best_eval or {}

    def feedback(self, style: str, success: bool):
        """Yes/no feedback from the user."""
        if success:
            self.style_scores[style] = self.style_scores.get(style, 0) + 1


# ═══════════════════════════════════════════════════════════════════════════════
# Training Session
# ═══════════════════════════════════════════════════════════════════════════════

def run_training():
    """Run a full pattern-solving training session."""
    print("=" * 70)
    print("PATTERN MIND TRAINING — Learning to Solve From Within")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Patterns: {len(PATTERN_LIBRARY)}")
    print()

    mind = PatternMind()
    results = []

    for name, expected_style, inp, out, desc in PATTERN_LIBRARY:
        solution, style, ev = mind.solve(inp, out)

        success = solution is not None
        mind.feedback(style, success)

        results.append({
            "name": name,
            "expected_style": expected_style,
            "actual_style": style,
            "style_match": style == expected_style,
            "success": success,
            "accuracy": ev.get("accuracy", 0),
        })

        status = "✓" if success else "✗"
        style_ok = "==" if style == expected_style else "!="
        print(f"  {name:10s} {status} style={style:12s} {style_ok} {expected_style:12s} "
              f"acc={ev.get('accuracy',0):.2f} | {desc}")

    # Summary
    n_solved = sum(1 for r in results if r["success"])
    n_style_match = sum(1 for r in results if r["style_match"])
    print(f"\n{'='*70}")
    print(f"SOLVED: {n_solved}/{len(results)} ({100*n_solved/len(results):.0f}%)")
    print(f"STYLE MATCH: {n_style_match}/{len(results)} ({100*n_style_match/len(results):.0f}%)")
    print(f"{'='*70}")

    # Style breakdown
    print(f"\nStyle scores (from experience):")
    for style, score in sorted(mind.style_scores.items(), key=lambda x: -x[1]):
        n_tried = sum(1 for r in results if r["actual_style"] == style)
        n_ok = sum(1 for r in results if r["actual_style"] == style and r["success"])
        print(f"  {style:15s}: {n_ok}/{n_tried} solved, experience score={score}")

    # Save
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_patterns": len(results),
        "n_solved": n_solved,
        "n_style_match": n_style_match,
        "style_scores": mind.style_scores,
        "results": results,
    }
    out_path = SCRIPT_DIR.parent.parent / "long_term_memory" / "pattern_training_run_001.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved to {out_path}")

    return output


if __name__ == "__main__":
    run_training()
