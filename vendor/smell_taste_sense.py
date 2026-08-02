"""
smell_taste_sense.py — smell and taste in the digital world
=============================================================

The user's question: "what is smell and taste in the digital world?"

In nature:
  - SMELL is volatile chemical detection at a distance.  You can smell
    something cooking from across the house without seeing it.  Smell
    is LONG-RANGE, LOW-RESOLUTION identity recognition.
  - TASTE is direct chemical analysis on contact.  When you bite into
    food, your taste buds tell you its composition.  Taste is
    SHORT-RANGE, HIGH-RESOLUTION composition analysis.

In the digital / ARC world:
  - SMELL = the GESTALT signature of a distant region.  Downsample the
    grid to a small icon (e.g., 4×4) and compute its MOG meaning
    signature.  Two grids with the same smell share the same overall
    structure, even if their cells differ.
  - TASTE = the COMPOSITION of a region.  When you "bite into" a region
    (a 3×3 or 5×5 neighbourhood), the taste is the histogram of values,
    the texture features, the local statistics.  Two regions with the
    same taste are made of the same "stuff".

Why these matter for ARC
------------------------

Many ARC tasks involve:
  - "Find the region that smells like X and recolour it" (smell)
  - "Replace every region that tastes like X with Y" (taste)
  - "The output should smell like the train output" (smell match)

The arm (touch) can feel one cell's neighbourhood.  The eye (sight)
can see one cell's colour.  But neither can answer "is this whole
region made of the same stuff as that other region?" — that's taste.
And neither can answer "does this grid have the same overall structure
as that grid?" — that's smell.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid


# ══════════════════════════════════════════════════════════════════════════════
# SMELL — long-range Gestalt signature
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SmellSignature:
    """The smell of a grid — its long-range Gestalt identity.

    The smell is computed by downsampling the grid to a small icon
    (default 4×4) and recording:
      - the downsampled icon (each cell = most common colour in that block)
      - the icon's hash (a compact fingerprint)
      - the dominant colour (most common overall)
      - the colour diversity (number of distinct colours)
      - the spatial moment (centre of mass of non-zero cells)
    """
    icon: List[List[int]] = field(default_factory=list)
    icon_hash: int = 0
    dominant_colour: int = 0
    colour_diversity: int = 0
    spatial_centre: Tuple[float, float] = (0.0, 0.0)
    icon_size: int = 4

    def as_dict(self) -> Dict[str, Any]:
        return {
            "icon": self.icon,
            "icon_hash": self.icon_hash,
            "dominant_colour": self.dominant_colour,
            "colour_diversity": self.colour_diversity,
            "spatial_centre": self.spatial_centre,
            "icon_size": self.icon_size,
        }


def downsample_grid(grid: Grid, target_size: int = 4) -> List[List[int]]:
    """Downsample a grid to target_size × target_size.

    Each cell of the downsampled icon is the most common colour in the
    corresponding block of the original grid.
    """
    h, w = grid.shape
    out = []
    for r in range(target_size):
        row = []
        for c in range(target_size):
            # Block boundaries
            r0 = r * h // target_size
            r1 = (r + 1) * h // target_size
            c0 = c * w // target_size
            c1 = (c + 1) * w // target_size
            # Most common colour in block
            block_colours = []
            for rr in range(r0, r1):
                for cc in range(c0, c1):
                    block_colours.append(grid.cells[rr][cc])
            if block_colours:
                most_common = Counter(block_colours).most_common(1)[0][0]
            else:
                most_common = 0
            row.append(most_common)
        out.append(row)
    return out


def smell_grid(grid: Grid, icon_size: int = 4) -> SmellSignature:
    """Smell a grid — compute its long-range Gestalt signature."""
    icon = downsample_grid(grid, icon_size)

    # Icon hash
    icon_hash = hash(tuple(tuple(row) for row in icon))

    # Dominant colour
    all_colours = [grid.cells[r][c] for r in range(grid.height) for c in range(grid.width)]
    dominant = Counter(all_colours).most_common(1)[0][0] if all_colours else 0

    # Colour diversity
    diversity = len(set(all_colours))

    # Spatial centre of non-zero cells
    non_zero = [(r, c) for r in range(grid.height) for c in range(grid.width)
                if grid.cells[r][c] != 0]
    if non_zero:
        cr = sum(r for r, _ in non_zero) / len(non_zero)
        cc = sum(c for _, c in non_zero) / len(non_zero)
        # Normalise to 0-1
        cr /= max(grid.height - 1, 1)
        cc /= max(grid.width - 1, 1)
        centre = (cr, cc)
    else:
        centre = (0.5, 0.5)

    return SmellSignature(
        icon=icon, icon_hash=icon_hash,
        dominant_colour=dominant, colour_diversity=diversity,
        spatial_centre=centre, icon_size=icon_size,
    )


def smell_distance(smell_a: SmellSignature, smell_b: SmellSignature) -> float:
    """Distance between two smells (0 = identical, higher = more different).

    Combines:
      - icon Hamming distance (0-16 for 4×4 icons)
      - dominant colour mismatch (0 or 1)
      - diversity difference (0-10)
      - spatial centre distance (0-sqrt(2))
    """
    # Icon Hamming distance
    icon_dist = sum(1 for ra, rb in zip(smell_a.icon, smell_b.icon)
                    for ca, cb in zip(ra, rb) if ca != cb)
    icon_dist /= (smell_a.icon_size * smell_a.icon_size)

    # Dominant colour mismatch
    dom_dist = 0.0 if smell_a.dominant_colour == smell_b.dominant_colour else 0.3

    # Diversity difference
    div_dist = abs(smell_a.colour_diversity - smell_b.colour_diversity) / 10.0

    # Spatial centre distance
    cr1, cc1 = smell_a.spatial_centre
    cr2, cc2 = smell_b.spatial_centre
    centre_dist = math.sqrt((cr1 - cr2) ** 2 + (cc1 - cc2) ** 2) / math.sqrt(2)

    return icon_dist + dom_dist + div_dist + centre_dist


def smell_similarity(smell_a: SmellSignature, smell_b: SmellSignature) -> float:
    """Similarity in [0, 1].  1 = identical smell."""
    return max(0.0, 1.0 - smell_distance(smell_a, smell_b) / 4.0)


# ══════════════════════════════════════════════════════════════════════════════
# TASTE — local composition / histogram
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TasteProfile:
    """The taste of a region — its composition.

    The taste is the histogram of values in a local neighbourhood,
    plus texture features (number of colour transitions, edge density).

    Two regions with the same taste are made of the same stuff.
    """
    histogram: Dict[int, int] = field(default_factory=dict)
    total_cells: int = 0
    distinct_colours: int = 0
    colour_transitions: int = 0  # horizontal + vertical
    edge_density: float = 0.0    # fraction of cells that are edges
    dominant_colour: int = 0
    dominant_fraction: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "histogram": self.histogram,
            "total_cells": self.total_cells,
            "distinct_colours": self.distinct_colours,
            "colour_transitions": self.colour_transitions,
            "edge_density": self.edge_density,
            "dominant_colour": self.dominant_colour,
            "dominant_fraction": self.dominant_fraction,
        }


def taste_region(grid: Grid, r: int, c: int, radius: int = 1) -> TasteProfile:
    """Taste a region around (r, c) — compute its composition.

    The region is a (2*radius+1) × (2*radius+1) neighbourhood.
    """
    h, w = grid.shape
    cells_in_region = []
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                cells_in_region.append(grid.cells[nr][nc])

    if not cells_in_region:
        return TasteProfile()

    histogram = dict(Counter(cells_in_region))
    total = len(cells_in_region)
    distinct = len(histogram)
    dominant, dom_count = Counter(cells_in_region).most_common(1)[0]
    dom_frac = dom_count / total

    # Colour transitions (horizontal + vertical within the region)
    transitions = 0
    edges = 0
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius):
            nr, nc = r + dr, c + dc
            nr2, nc2 = r + dr, c + dc + 1
            if (0 <= nr < h and 0 <= nc < w and 0 <= nr2 < h and 0 <= nc2 < w):
                if grid.cells[nr][nc] != grid.cells[nr2][nc2]:
                    transitions += 1
                    edges += 1
    for dr in range(-radius, radius):
        for dc in range(-radius, radius + 1):
            nr, nc = r + dr, c + dc
            nr2, nc2 = r + dr + 1, c + dc
            if (0 <= nr < h and 0 <= nc < w and 0 <= nr2 < h and 0 <= nc2 < w):
                if grid.cells[nr][nc] != grid.cells[nr2][nc2]:
                    transitions += 1
                    edges += 1

    edge_density = edges / max(total, 1)

    return TasteProfile(
        histogram=histogram, total_cells=total,
        distinct_colours=distinct, colour_transitions=transitions,
        edge_density=edge_density, dominant_colour=dominant,
        dominant_fraction=dom_frac,
    )


def taste_grid(grid: Grid, radius: int = 1) -> List[List[TasteProfile]]:
    """Taste every cell of a grid.  Returns a 2D list of TasteProfile."""
    h, w = grid.shape
    return [[taste_region(grid, r, c, radius) for c in range(w)]
            for r in range(h)]


def taste_distance(taste_a: TasteProfile, taste_b: TasteProfile) -> float:
    """Distance between two tastes (0 = identical composition)."""
    # Histogram distance (total variation)
    all_colours = set(taste_a.histogram.keys()) | set(taste_b.histogram.keys())
    total_a = max(taste_a.total_cells, 1)
    total_b = max(taste_b.total_cells, 1)
    hist_dist = sum(
        abs(taste_a.histogram.get(k, 0) / total_a - taste_b.histogram.get(k, 0) / total_b)
        for k in all_colours
    ) / 2.0  # normalise to 0-1

    # Distinct colours difference
    div_dist = abs(taste_a.distinct_colours - taste_b.distinct_colours) / 10.0

    # Edge density difference
    edge_dist = abs(taste_a.edge_density - taste_b.edge_density)

    return hist_dist + div_dist + edge_dist


def taste_similarity(taste_a: TasteProfile, taste_b: TasteProfile) -> float:
    """Similarity in [0, 1].  1 = identical taste."""
    return max(0.0, 1.0 - taste_distance(taste_a, taste_b) / 3.0)


# ══════════════════════════════════════════════════════════════════════════════
# Find regions by taste
# ══════════════════════════════════════════════════════════════════════════════

def find_regions_by_taste(grid: Grid, target_taste: TasteProfile,
                           threshold: float = 0.7,
                           radius: int = 1) -> List[Tuple[int, int]]:
    """Find all cells whose taste matches the target above threshold."""
    h, w = grid.shape
    matches = []
    for r in range(h):
        for c in range(w):
            t = taste_region(grid, r, c, radius)
            if taste_similarity(t, target_taste) >= threshold:
                matches.append((r, c))
    return matches


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Smell & Taste self-test")
    print("=" * 60)

    # Smell test
    print("\n[Smell] Two grids with same structure")
    grid1 = Grid([
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [3, 3, 4, 4],
        [3, 3, 4, 4],
    ])
    grid2 = Grid([
        [5, 5, 6, 6],
        [5, 5, 6, 6],
        [7, 7, 8, 8],
        [7, 7, 8, 8],
    ])
    smell1 = smell_grid(grid1)
    smell2 = smell_grid(grid2)
    print(f"  grid1 icon: {smell1.icon}")
    print(f"  grid2 icon: {smell2.icon}")
    print(f"  similarity: {smell_similarity(smell1, smell2):.3f}")

    grid3 = Grid([
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 1, 2, 3],
        [4, 5, 6, 7],
    ])
    smell3 = smell_grid(grid3)
    print(f"  grid3 icon: {smell3.icon}")
    print(f"  grid1 vs grid3 similarity: {smell_similarity(smell1, smell3):.3f}")

    # Taste test
    print("\n[Taste] Two regions with same composition")
    grid = Grid([
        [1, 1, 2, 2, 1, 1, 2, 2],
        [1, 1, 2, 2, 1, 1, 2, 2],
        [3, 3, 4, 4, 3, 3, 4, 4],
        [3, 3, 4, 4, 3, 3, 4, 4],
    ])
    taste_a = taste_region(grid, 1, 1, radius=1)
    taste_b = taste_region(grid, 1, 5, radius=1)
    taste_c = taste_region(grid, 2, 2, radius=1)
    print(f"  taste at (1,1): {taste_a.as_dict()}")
    print(f"  taste at (1,5): {taste_b.as_dict()}")
    print(f"  taste at (2,2): {taste_c.as_dict()}")
    print(f"  sim((1,1),(1,5)): {taste_similarity(taste_a, taste_b):.3f}")
    print(f"  sim((1,1),(2,2)): {taste_similarity(taste_a, taste_c):.3f}")

    # Find regions by taste
    print("\n[Find by taste] cells matching taste at (1,1)")
    matches = find_regions_by_taste(grid, taste_a, threshold=0.8)
    print(f"  matches: {matches}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
