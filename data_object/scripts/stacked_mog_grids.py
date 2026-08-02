"""
Stacked MOG Grids — Spatial Arithmetic bit-pair interaction engine.

Each bit in a 24-bit Data Object becomes a Spatial Arithmetic polygon placed
at its MOG grid position (4 rows × 6 columns). Two elements' grids are stacked
in 3D space (one at Z=0, one at Z=+offset). The 24×24 = 576 bit-pair
interactions have geometry that Spatial Arithmetic can calculate:

  - Clearance (centroid_distance - radius_A - radius_B) — if this matches
    an operator code (4=MULTIPLY, 5=DIVIDE, 6=ADD, 7=SUBTRACT), the bit pair
    "encodes" that arithmetic operator.
  - Normal-vector alignment (dot product of polygon plane normals)
  - Bounding-sphere overlap

The user's intuition: "a mog grid in a virtual space made of polygons placed
next to (like up 1 Z axis) another mog grid will have interactions between
individual bits in a Spatial Arithmetic level."

This module computes those interactions.
"""

from __future__ import annotations

import sys
import math
import statistics
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import spatial_arithmetic as sa

# MOG grid layout: 4 rows × 6 columns
# Bit index = row * 6 + col
ROW_NAMES = ["Reality", "Info", "Activation", "Potential"]


def bit_to_grid_pos(bit_index: int) -> Tuple[int, int]:
    """Convert bit index (0-23) to (row, col) in the 4×6 MOG grid."""
    return bit_index // 6, bit_index % 6


def grid_pos_to_bit(row: int, col: int) -> int:
    """Convert (row, col) to bit index."""
    return row * 6 + col


# ════════════════════════════════════════════════════════════════════════════════
# Polygon construction per bit
# ════════════════════════════════════════════════════════════════════════════════

def build_bit_polygon(bit_index: int, bit_value: int,
                      seed_offset: int = 0) -> Tuple[List[Tuple[float, float, float]],
                                                       Tuple[float, float, float],
                                                       float]:
    """Build a Spatial Arithmetic polygon for a single bit.

    bit_value=1 → encode(1, seed) → 6-vertex hexagon (circumradius 1.0)
    bit_value=0 → encode(0, seed) → 4-vertex square (circumradius ≈ 0.707)

    The seed is the bit index + seed_offset, giving each bit position a
    deterministic 3D orientation.

    Returns:
      (vertices, centroid, circumradius)
    """
    seed = bit_index + seed_offset
    pts = sa.encode(bit_value, seed=seed)
    c = sa.centroid(pts)
    r = sa.radius_of(pts)
    return pts, c, r


def get_polygon_normal(bit_index: int, seed_offset: int = 0) -> Tuple[float, float, float]:
    """Get the 3D normal vector of the polygon's plane for a given bit position.

    The polygon starts in the XY plane (normal = (0, 0, 1)) and is rotated
    by the deterministic rotation matrix from spatial_arithmetic.
    The rotated normal is the third column of the rotation matrix.
    """
    seed = bit_index + seed_offset
    M = sa._rotation_matrix(seed)
    # Normal (0,0,1) rotated by M = third column of M
    return (M[0][2], M[1][2], M[2][2])


# ════════════════════════════════════════════════════════════════════════════════
# Stacked MOG grid scene
# ════════════════════════════════════════════════════════════════════════════════

class StackedMOGScene:
    """Two MOG grids stacked in 3D space, with bit-pair interaction computation.

    Grid A is at Z=0, Grid B is at Z=z_offset.
    Each grid is a 4×6 arrangement of polygons, one per bit position.
    """

    def __init__(self,
                 cell_w: float = 4.0,
                 cell_h: float = 4.0,
                 z_offset: float = 7.0,
                 seed_offset_a: int = 0,
                 seed_offset_b: int = 0):
        """
        Args:
            cell_w: horizontal spacing between grid columns
            cell_h: vertical spacing between grid rows
            z_offset: Z-axis distance between the two grids
            seed_offset_a: seed offset for grid A polygons (default 0)
            seed_offset_b: seed offset for grid B polygons (default 0;
                           use different value to give B different orientations)
        """
        self.cell_w = cell_w
        self.cell_h = cell_h
        self.z_offset = z_offset
        self.seed_offset_a = seed_offset_a
        self.seed_offset_b = seed_offset_b

        # Pre-compute polygon positions and normals for all 24 bit positions
        # Grid is centered at origin
        grid_origin_x = -(5 * cell_w / 2.0)  # 6 columns
        grid_origin_y = -(3 * cell_h / 2.0)  # 4 rows

        self.bit_positions = []  # (x, y) for each bit index
        for i in range(24):
            r, c = bit_to_grid_pos(i)
            x = grid_origin_x + c * cell_w + cell_w / 2.0
            y = grid_origin_y + r * cell_h + cell_h / 2.0
            self.bit_positions.append((x, y))

        # Pre-compute normals for all bit positions (for both grids)
        self.normals_a = [get_polygon_normal(i, seed_offset_a) for i in range(24)]
        self.normals_b = [get_polygon_normal(i, seed_offset_b) for i in range(24)]

    def build_grid(self, bits24: List[int], grid: str = "A") -> List[Dict]:
        """Build 24 polygons for one element's bits, placed at grid positions.

        grid="A" → Z=0, seed_offset_a
        grid="B" → Z=z_offset, seed_offset_b

        Returns list of 24 dicts with polygon info.
        """
        z_plane = 0.0 if grid == "A" else self.z_offset
        seed_offset = self.seed_offset_a if grid == "A" else self.seed_offset_b

        polygons = []
        for i in range(24):
            pts, centroid_local, radius = build_bit_polygon(i, bits24[i], seed_offset)
            # Translate to grid position
            gx, gy = self.bit_positions[i]
            pts_t = sa.translate(pts, (gx, gy, z_plane))
            centroid = (gx, gy, z_plane)  # centroid is at grid position (rotation doesn't move centroid)
            # Actually, the centroid of the rotated polygon is at origin before translation.
            # After translation, centroid = (gx + 0, gy + 0, z_plane) = (gx, gy, z_plane)
            # Wait, the centroid of the LOCAL polygon might not be at origin after rotation.
            # Let me recompute.
            c_local = sa.centroid(pts)
            # The translated centroid is (gx + c_local[0], gy + c_local[1], z_plane + c_local[2])
            # But actually, pts are already rotated around origin, so c_local is the rotated centroid.
            # For a regular polygon centered at origin, the centroid IS at origin.
            # The rotation preserves this (rotation is about origin).
            # So c_local should be (0, 0, 0) or very close.
            # After translate((gx, gy, z_plane)), centroid = (gx, gy, z_plane).

            normal = self.normals_a[i] if grid == "A" else self.normals_b[i]

            polygons.append({
                "bit_index": i,
                "bit_value": bits24[i],
                "vertices": pts_t,
                "centroid": (gx, gy, z_plane),
                "radius": radius,
                "normal": normal,
                "row": i // 6,
                "col": i % 6,
                "row_name": ROW_NAMES[i // 6],
                "grid": grid,
            })
        return polygons

    def compute_bit_pair_interaction(self, poly_a: Dict, poly_b: Dict) -> Dict:
        """Compute the spatial interaction between one polygon from A and one from B.

        Returns clearance, nearest operator, normal alignment, etc.
        """
        ca = poly_a["centroid"]
        cb = poly_b["centroid"]
        dist = math.dist(ca, cb)
        clearance = dist - poly_a["radius"] - poly_b["radius"]

        # Find nearest operator code
        operators = sa.OPERATOR_CODES  # {"MULTIPLY": 4, "DIVIDE": 5, "ADD": 6, "SUBTRACT": 7}
        code_to_op = sa.CODE_TO_OPERATOR  # {4: "MULTIPLY", ...}

        nearest_code = min(code_to_op.keys(), key=lambda c: abs(clearance - c))
        nearest_op = code_to_op[nearest_code]
        residual = abs(clearance - nearest_code)
        is_exact = residual < sa.CODE_TOLERANCE

        # Normal vector alignment (dot product)
        na = poly_a["normal"]
        nb = poly_b["normal"]
        normal_dot = na[0]*nb[0] + na[1]*nb[1] + na[2]*nb[2]

        # Bounding sphere overlap
        overlap = clearance < 0

        # Grid position difference
        dr = poly_b["row"] - poly_a["row"]
        dc = poly_b["col"] - poly_a["col"]

        return {
            "bit_a": poly_a["bit_index"],
            "bit_b": poly_b["bit_index"],
            "row_a": poly_a["row"], "col_a": poly_a["col"],
            "row_b": poly_b["row"], "col_b": poly_b["col"],
            "delta_row": dr, "delta_col": dc,
            "bit_a_val": poly_a["bit_value"],
            "bit_b_val": poly_b["bit_value"],
            "centroid_distance": dist,
            "clearance": clearance,
            "nearest_operator": nearest_op if is_exact else "NONE",
            "nearest_operator_code": nearest_code,
            "operator_residual": residual,
            "is_operator": is_exact,
            "normal_dot": normal_dot,
            "normal_angle_deg": math.degrees(math.acos(max(-1.0, min(1.0, normal_dot)))),
            "bounding_overlap": overlap,
            "radius_a": poly_a["radius"],
            "radius_b": poly_b["radius"],
        }

    def compute_all_interactions(self, bits_a: List[int],
                                  bits_b: List[int]) -> List[Dict]:
        """Compute all 24×24 = 576 bit-pair interactions between two stacked grids."""
        grid_a = self.build_grid(bits_a, "A")
        grid_b = self.build_grid(bits_b, "B")
        interactions = []
        for pa in grid_a:
            for pb in grid_b:
                interactions.append(self.compute_bit_pair_interaction(pa, pb))
        return interactions

    def compute_pair_metrics(self, bits_a: List[int],
                              bits_b: List[int]) -> Dict:
        """Compute aggregate pair-level metrics from all 576 bit-pair interactions."""
        interactions = self.compute_all_interactions(bits_a, bits_b)

        # Operator-encoding pairs
        op_pairs = [i for i in interactions if i["is_operator"]]
        op_counts = {"MULTIPLY": 0, "DIVIDE": 0, "ADD": 0, "SUBTRACT": 0, "NONE": 0}
        for i in interactions:
            op_counts[i["nearest_operator"]] += 1

        # Same-position interactions (bit i in A vs bit i in B)
        same_pos = [i for i in interactions if i["bit_a"] == i["bit_b"]]
        same_pos_op = [i for i in same_pos if i["is_operator"]]

        # Active-active pairs (both bits ON)
        active_active = [i for i in interactions if i["bit_a_val"] == 1 and i["bit_b_val"] == 1]
        active_active_op = [i for i in active_active if i["is_operator"]]

        # Normal alignment stats
        normal_dots = [i["normal_dot"] for i in interactions]
        normal_angles = [i["normal_angle_deg"] for i in interactions]

        # Clearance stats
        clearances = [i["clearance"] for i in interactions]
        residuals = [i["operator_residual"] for i in interactions]

        # By operator type for active-active pairs
        aa_op_counts = {"MULTIPLY": 0, "DIVIDE": 0, "ADD": 0, "SUBTRACT": 0}
        for i in active_active:
            if i["is_operator"]:
                aa_op_counts[i["nearest_operator"]] += 1

        # By operator type for same-position pairs
        sp_op_counts = {"MULTIPLY": 0, "DIVIDE": 0, "ADD": 0, "SUBTRACT": 0}
        for i in same_pos:
            if i["is_operator"]:
                sp_op_counts[i["nearest_operator"]] += 1

        # Normal alignment for same-position pairs (matching bit indices)
        same_pos_normal_dots = [i["normal_dot"] for i in same_pos]
        same_pos_normal_angles = [i["normal_angle_deg"] for i in same_pos]

        # Normal alignment for active-active pairs
        aa_normal_dots = [i["normal_dot"] for i in active_active]
        aa_normal_angles = [i["normal_angle_deg"] for i in active_active]

        # Bounding sphere overlaps
        overlaps = sum(1 for i in interactions if i["bounding_overlap"])

        # Cross-row interactions (bits in different MOG rows)
        cross_row = [i for i in interactions if i["delta_row"] != 0]
        cross_row_op = [i for i in cross_row if i["is_operator"]]

        # Cross-col interactions (bits in different MOG columns)
        cross_col = [i for i in interactions if i["delta_col"] != 0]
        cross_col_op = [i for i in cross_col if i["is_operator"]]

        return {
            "config": {
                "cell_w": self.cell_w,
                "cell_h": self.cell_h,
                "z_offset": self.z_offset,
                "seed_offset_a": self.seed_offset_a,
                "seed_offset_b": self.seed_offset_b,
            },
            "n_interactions": len(interactions),
            "n_operator_pairs": len(op_pairs),
            "operator_counts": op_counts,
            "same_position_count": len(same_pos),
            "same_position_op_count": len(same_pos_op),
            "same_position_op_breakdown": sp_op_counts,
            "active_active_count": len(active_active),
            "active_active_op_count": len(active_active_op),
            "active_active_op_breakdown": aa_op_counts,
            "mean_clearance": statistics.mean(clearances),
            "std_clearance": statistics.pstdev(clearances),
            "min_clearance": min(clearances),
            "max_clearance": max(clearances),
            "mean_operator_residual": statistics.mean(residuals),
            "min_operator_residual": min(residuals),
            "mean_normal_dot": statistics.mean(normal_dots),
            "std_normal_dot": statistics.pstdev(normal_dots),
            "mean_normal_angle": statistics.mean(normal_angles),
            "std_normal_angle": statistics.pstdev(normal_angles),
            "same_pos_mean_normal_dot": statistics.mean(same_pos_normal_dots) if same_pos_normal_dots else 0.0,
            "same_pos_mean_normal_angle": statistics.mean(same_pos_normal_angles) if same_pos_normal_angles else 0.0,
            "aa_mean_normal_dot": statistics.mean(aa_normal_dots) if aa_normal_dots else 0.0,
            "aa_mean_normal_angle": statistics.mean(aa_normal_angles) if aa_normal_angles else 0.0,
            "bounding_overlap_count": overlaps,
            "cross_row_op_count": len(cross_row_op),
            "cross_col_op_count": len(cross_col_op),
            "interactions_sample": interactions[:10],  # first 10 for debugging
        }


# ════════════════════════════════════════════════════════════════════════════════
# Configuration search: find (cell_w, cell_h, z_offset) that produce operator hits
# ════════════════════════════════════════════════════════════════════════════════

def find_operator_configs(bits_sample: List[int]) -> List[Dict]:
    """Sweep over grid configurations to find ones that produce operator-encoding pairs.

    For a sample element's bits, try many (cell_w, cell_h, z_offset) combinations
    and report which produce exact operator-code clearances for any bit pair.
    """
    configs = []
    # Sweep cell spacing
    for cell_w in [3.0, 4.0, 5.0, 6.0]:
        for cell_h in [3.0, 4.0, 5.0, 6.0]:
            # Sweep z_offset with fine granularity
            for z_offset_10 in range(40, 120):  # 4.0 to 12.0 in steps of 0.1
                z_offset = z_offset_10 / 10.0
                scene = StackedMOGScene(cell_w=cell_w, cell_h=cell_h, z_offset=z_offset)
                metrics = scene.compute_pair_metrics(bits_sample, bits_sample)

                if metrics["n_operator_pairs"] > 0:
                    configs.append({
                        "cell_w": cell_w,
                        "cell_h": cell_h,
                        "z_offset": z_offset,
                        "n_op_pairs": metrics["n_operator_pairs"],
                        "op_counts": metrics["operator_counts"],
                        "same_pos_op": metrics["same_position_op_count"],
                        "aa_op": metrics["active_active_op_count"],
                        "sp_breakdown": metrics["same_position_op_breakdown"],
                        "aa_breakdown": metrics["active_active_op_breakdown"],
                    })

    # Sort by number of operator pairs (descending)
    configs.sort(key=lambda c: -c["n_op_pairs"])
    return configs


# ════════════════════════════════════════════════════════════════════════════════
# Self-test
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 78)
    print("STACKED MOG GRIDS — SELF TEST")
    print("=" * 78)

    # Use Carbon's KB-hardened vector
    import ubp_kb_loader as kb
    c = kb.get_element("C")
    bits = c.vector24
    o = kb.get_element("O")

    print(f"\nElement C: bits={bits}  HW={sum(bits)}")
    print(f"Element O: bits={o.vector24}  HW={sum(o.vector24)}")

    # Test with z=7, cell=4 (our predicted config: same-pos→DIVIDE, diagonal→SUBTRACT)
    print(f"\n── Config: cell_w=4, cell_h=4, z_offset=7.0 ──")
    scene = StackedMOGScene(cell_w=4.0, cell_h=4.0, z_offset=7.0)
    metrics = scene.compute_pair_metrics(bits, o.vector24)
    print(f"  Total interactions: {metrics['n_interactions']}")
    print(f"  Operator-encoding pairs: {metrics['n_operator_pairs']}")
    print(f"  Operator breakdown: {metrics['operator_counts']}")
    print(f"  Same-position op pairs: {metrics['same_position_op_count']}")
    print(f"  Same-position breakdown: {metrics['same_position_op_breakdown']}")
    print(f"  Active-active op pairs: {metrics['active_active_op_count']}")
    print(f"  Active-active breakdown: {metrics['active_active_op_breakdown']}")
    print(f"  Mean clearance: {metrics['mean_clearance']:.4f}")
    print(f"  Mean normal dot: {metrics['mean_normal_dot']:.4f}")
    print(f"  Same-pos mean normal dot: {metrics['same_pos_mean_normal_dot']:.4f}")
    print(f"  Same-pos mean normal angle: {metrics['same_pos_mean_normal_angle']:.2f}°")
    print(f"  Bounding overlaps: {metrics['bounding_overlap_count']}")

    # Show sample interactions
    print(f"\n  Sample interactions (first 5 same-position):")
    sp_ints = [i for i in metrics["interactions_sample"] if i["bit_a"] == i["bit_b"]]
    for i in sp_ints[:5]:
        print(f"    bit {i['bit_a']:2d} (A={i['bit_a_val']}, B={i['bit_b_val']}): "
              f"clearance={i['clearance']:.4f} → {i['nearest_operator']} "
              f"(residual={i['operator_residual']:.6f})  "
              f"normal_dot={i['normal_dot']:.4f}")

    # Find best configurations
    print(f"\n── Searching for operator-encoding configurations ──")
    print(f"  (sweeping cell_w ∈ {{3,4,5,6}}, cell_h ∈ {{3,4,5,6}}, z_offset ∈ [4.0, 12.0])")
    print(f"  (using C vs O as test pair)")
    configs = find_operator_configs(bits)
    print(f"\n  Top 20 configurations by operator-pair count:")
    print(f"  {'cell_w':>6} {'cell_h':>6} {'z_off':>6} {'n_ops':>6} "
          f"{'same':>5} {'aa':>5} {'MULT':>5} {'DIV':>5} {'ADD':>5} {'SUB':>5}")
    for cfg in configs[:20]:
        oc = cfg["op_counts"]
        print(f"  {cfg['cell_w']:>6.1f} {cfg['cell_h']:>6.1f} {cfg['z_offset']:>6.1f} "
              f"{cfg['n_op_pairs']:>6} {cfg['same_pos_op']:>5} {cfg['aa_op']:>5} "
              f"{oc['MULTIPLY']:>5} {oc['DIVIDE']:>5} {oc['ADD']:>5} {oc['SUBTRACT']:>5}")
