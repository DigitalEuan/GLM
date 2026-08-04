"""
Golay MOG Data Object investigation.

Pipeline:
  1. Take a real element from the periodic table.
  2. Encode 4 of its measurable properties (Z, mass, EN, valence) as
     4 Gray-coded 6-bit rows -> a 24-bit "Data Object".
  3. Snap that object to the nearest Golay [24,12,8] codeword.
  4. Decompose via MOG (4x6 grid) -> 6 Hexacode GF(4) symbols.
  5. Measure per-bit "spatial skew" using 3 different rules
     against the spatial_arithmetic polygon codec.
  6. For each pair of elements, compute interaction metrics
     (Golay XOR snap, Hexacode shadow diff, spatial scene merge,
     spatial arithmetic op) and compare against known chemistry.

This is exploratory. We are looking for ANY emergent correlation,
not assuming one will appear.
"""

from __future__ import annotations

import sys
import os
import json
import math
import random
import statistics
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Make the local modules importable
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa
import element_data as ed


# ════════════════════════════════════════════════════════════════════════════════
#  PART A — DATA OBJECT ENCODING (real element -> 24-bit MOG payload)
# ════════════════════════════════════════════════════════════════════════════════

# The 4 rows of the MOG grid (row-major, 6 cols each, 4 rows = 24 bits).
# Row mapping follows the UBP semantics described in driving_ubp_glm.txt:
#   Row 0 = Reality/Mass        (Z, the identity bit)
#   Row 1 = Information         (mass, how much "stuff")
#   Row 2 = Activation          (EN, electronegativity pull)
#   Row 3 = Potential           (valence, available bonding)
ROW_NAMES = ["Reality", "Info", "Activation", "Potential"]


def gray6(n: int) -> List[int]:
    """6-bit Gray code of an integer in [0, 63]. Returns MSB-first list."""
    n &= 0x3F
    g = n ^ (n >> 1)
    return [(g >> (5 - i)) & 1 for i in range(6)]


def ungray6(bits: List[int]) -> int:
    """Decode 6-bit Gray code back to integer (for verification only)."""
    g = 0
    for b in bits:
        g = (g << 1) | (b & 1)
    n = g
    mask = g >> 1
    while mask:
        n ^= mask
        mask >>= 1
    return n


def property_to_rowval(prop_name: str, element: dict) -> int:
    """Scale a physical property to a 6-bit Gray-code-able integer in [0, 63]."""
    if prop_name == "Z":
        # Z in [1, 26] for our sweep -> use directly (subset of [0,63])
        return element["Z"] & 0x3F
    if prop_name == "mass":
        # mass up to ~56 (Fe) -> scale: mass mod 64
        return element["mass"] & 0x3F
    if prop_name == "EN":
        # Pauling EN in [0, 4.0] -> ×100 -> [0, 400] -> take /8 -> [0, 50]
        return (element["EN"] // 8) & 0x3F
    if prop_name == "valence":
        # valence in [1, 8] -> encode as (val<<3) | val for redundancy
        v = element["val"] & 0x07
        return ((v << 3) | v) & 0x3F
    if prop_name == "IE":
        # IE in ~[490, 2400] kJ/mol -> /40 -> [12, 60]
        return (element["IE"] // 40) & 0x3F
    if prop_name == "radius":
        # covalent radius [28, 166] pm -> /4 -> [7, 41]
        return (element["radius"] // 4) & 0x3F
    raise ValueError(f"unknown property: {prop_name}")


def encode_data_object(symbol: str,
                       prop_set: List[str] = None) -> Dict[str, Any]:
    """
    Encode an element as a 24-bit MOG Data Object.

    Default property set: Z, mass, EN, valence (one per MOG row).
    Returns a dict with the 24-bit vector, MOG grid (4x6), per-row values,
    the Gray-coded values, and pre-snapped Golay info.
    """
    if prop_set is None:
        prop_set = ["Z", "mass", "EN", "valence"]

    el = ed.get(symbol)
    bits = []
    rows = []
    row_meta = []
    for r, prop in enumerate(prop_set):
        val = property_to_rowval(prop, el)
        gbits = gray6(val)
        rows.append(gbits)
        bits.extend(gbits)
        row_meta.append({
            "row": r,
            "row_name": ROW_NAMES[r],
            "property": prop,
            "raw_value": val,
            "physical_value": el.get(prop, None),
            "gray_bits": gbits,
            "gray_decimal": int("".join(str(b) for b in gbits), 2),
            "hamming_weight": sum(gbits),
        })

    # Build MOG grid (4x6, row-major)
    mog_grid = [bits[r*6:(r+1)*6] for r in range(4)]

    # Snap to nearest Golay codeword
    snapped, snap_meta = ubp.GOLAY_ENGINE.snap_to_codeword(bits)
    # Decompose original via MOG -> Hexacode shadow
    hex_symbols, col_vals = ubp.GOLAY_ENGINE.mog_decompose(bits)
    # Decompose snapped codeword too
    hex_snapped, col_snapped = ubp.GOLAY_ENGINE.mog_decompose(snapped)

    # Leech metrics on both
    tax_raw = ubp.LEECH_ENGINE.symmetry_tax(bits)
    tax_snapped = ubp.LEECH_ENGINE.symmetry_tax(snapped)
    nrci_raw = ubp.LEECH_ENGINE.calculate_nrci(bits)
    nrci_snapped = ubp.LEECH_ENGINE.calculate_nrci(snapped)

    # Hamming weight, syndrome weight
    hw = sum(bits)
    sw = ubp.GOLAY_ENGINE.syndrome_weight(bits)
    hw_snapped = sum(snapped)

    # Ontological health (4-layer)
    onto = ubp.LEECH_ENGINE.ontological_health(bits)

    return {
        "symbol": symbol,
        "element": el,
        "prop_set": prop_set,
        "bits24": bits,
        "mog_grid": mog_grid,
        "rows": row_meta,
        "hamming_weight": hw,
        "syndrome_weight": sw,
        "snapped": snapped,
        "snap_meta": snap_meta,
        "hex_symbols_raw": hex_symbols,
        "col_vals_raw": col_vals,
        "hex_symbols_snapped": hex_snapped,
        "col_vals_snapped": col_snapped,
        "is_codeword": sw == 0,
        "tax_raw": tax_raw,
        "tax_snapped": tax_snapped,
        "nrci_raw": nrci_raw,
        "nrci_snapped": nrci_snapped,
        "ontological_health": onto,
    }


# ════════════════════════════════════════════════════════════════════════════════
#  PART B — BIT SKEW MEASUREMENT  (3 different rules)
# ════════════════════════════════════════════════════════════════════════════════

def skew_rule_weight_as_polygon(bits24: List[int]) -> List[Dict[str, Any]]:
    """
    Rule 1 — Weight-as-polygon.

    For each bit i that is ON, encode its positional weight class (i+1,
    since the raw 2^i is far beyond the codec's 100k-vertex safety limit)
    as a polygon in 3D. Bit OFF -> no polygon. Skew(bit i) = signed distance
    of that polygon's centroid from the MOG-grid origin (which we place at (0,0,0)).

    Higher bit positions produce polygons with more vertices (i+1 encoded
    -> 2(i+1)+4 vertices), so higher bits are 'bigger shapes' AND carry more
    positional weight. Each bit gets its own deterministic rotation seed (= i)
    so its centroid sits at a distinct point in space.

    The raw positional weight 2^i is still recorded as metadata, but the
    geometric 'weight' that determines polygon size is the bit position i+1.
    """
    out = []
    # We will lay bits out along the +X axis with deterministic spacing.
    # Each ON-bit polygon is encoded from its own seed (=bit position) so the
    # rotation is deterministic per bit-position.
    for i, bit in enumerate(bits24):
        if bit == 0:
            out.append({
                "bit": i, "on": False, "skew_x": 0.0, "skew_y": 0.0, "skew_z": 0.0,
                "skew_magnitude": 0.0, "vertex_count": 0,
                "weight_log2": i, "weight_raw": 2**i,
            })
            continue
        # encode value = i+1 -> polygon with 2*(i+1)+4 = 2i+6 vertices
        encoded_val = i + 1
        # encode the value as a polygon
        pts = sa.encode(encoded_val, seed=i)
        # translate along X by an offset that depends on bit position
        # so different bits don't overlap (helps with later scene merging)
        offset_x = float(i * 3.0)  # 3 units per bit slot
        pts_t = sa.translate(pts, (offset_x, 0.0, 0.0))
        c = sa.centroid(pts_t)
        mag = math.sqrt(c[0]**2 + c[1]**2 + c[2]**2)
        out.append({
            "bit": i, "on": True,
            "skew_x": c[0], "skew_y": c[1], "skew_z": c[2],
            "skew_magnitude": mag,
            "vertex_count": len(pts_t),
            "weight_log2": i, "weight_raw": 2**i,
            "encoded_value": encoded_val,
            "radius": sa.radius_of(pts_t),
        })
    return out


def skew_rule_index_as_polygon(bits24: List[int]) -> List[Dict[str, Any]]:
    """
    Rule 2 — Index-as-polygon.

    Each bit POSITION i is encoded as a polygon with (i + 4) sides
    (i=0 -> square, i=23 -> 27-gon). Bit ON -> polygon present, OFF -> absent.
    Skew = polygon's circumradius (its 'prominence' in space).
    """
    out = []
    for i, bit in enumerate(bits24):
        if bit == 0:
            out.append({
                "bit": i, "on": False, "circumradius": 0.0,
                "vertex_count": 0, "prominence": 0.0,
            })
            continue
        n_sides = i + 4
        pts = sa.make_unit_cycle(n_sides, seed=i)
        r = sa.radius_of(pts)
        c = sa.centroid(pts)
        mag = math.sqrt(c[0]**2 + c[1]**2 + c[2]**2)
        out.append({
            "bit": i, "on": True,
            "circumradius": r,
            "vertex_count": n_sides,
            "prominence": r,  # circumradius IS the prominence in this rule
            "centroid_mag": mag,
        })
    return out


def skew_rule_mog_grid_scene(bits24: List[int]) -> Dict[str, Any]:
    """
    Rule 3 — MOG grid scene.

    Lay out 24 small polygons in a literal 4x6 spatial grid mirroring MOG.
    Each cell holds a polygon scaled by bit value (ON -> 4 sides full-size,
    OFF -> 4 sides scaled down to 0.5 unit edge, almost invisible).
    Skew per bit = cell's centroid offset from grid centroid.

    Returns the full scene with per-bit skew info and grid-level metrics.
    """
    # Grid layout: 4 rows x 6 cols, cell spacing = 4 units in X, 4 units in Y
    cell_w = 4.0
    cell_h = 4.0
    grid_origin_x = -(5 * cell_w / 2.0)  # center the grid at (0,0)
    grid_origin_y = -(3 * cell_h / 2.0)

    # Build scene points and per-cell records
    all_points: List[Tuple[float, float, float]] = []
    cells = []
    grid_centroid_x = 0.0
    grid_centroid_y = 0.0
    n_active = 0

    for r in range(4):
        for c in range(6):
            bit_idx = r * 6 + c
            bit = bits24[bit_idx]
            cell_center = (
                grid_origin_x + c * cell_w + cell_w / 2.0,
                grid_origin_y + r * cell_h + cell_h / 2.0,
                0.0,
            )
            if bit:
                # active cell: 4-vertex polygon, unit edge
                pts = sa.make_unit_cycle(4, seed=bit_idx)
                pts_t = sa.translate(pts, cell_center)
                n_active += 1
            else:
                # inactive cell: 4-vertex polygon scaled down to 0.5 edge
                pts = sa.make_unit_cycle(4, seed=bit_idx + 100)
                # scale around centroid
                c_centroid = sa.centroid(pts)
                pts = tuple(
                    (c_centroid[0] + 0.5 * (p[0] - c_centroid[0]),
                     c_centroid[1] + 0.5 * (p[1] - c_centroid[1]),
                     c_centroid[2] + 0.5 * (p[2] - c_centroid[2]))
                    for p in pts
                )
                pts_t = sa.translate(pts, cell_center)

            all_points.extend(pts_t)
            cell_centroid = sa.centroid(pts_t)
            cells.append({
                "bit": bit_idx,
                "row": r, "col": c,
                "row_name": ROW_NAMES[r],
                "on": bool(bit),
                "centroid": cell_centroid,
                "radius": sa.radius_of(pts_t),
            })
            grid_centroid_x += cell_centroid[0]
            grid_centroid_y += cell_centroid[1]

    n_cells = 24
    grid_centroid_x /= n_cells
    grid_centroid_y /= n_cells
    grid_centroid = (grid_centroid_x, grid_centroid_y, 0.0)

    # Per-bit skew = distance of cell centroid from grid centroid
    for cell in cells:
        cx, cy, cz = cell["centroid"]
        gx, gy, gz = grid_centroid
        cell["skew_x"] = cx - gx
        cell["skew_y"] = cy - gy
        cell["skew_z"] = cz - gz
        cell["skew_magnitude"] = math.sqrt(
            (cx - gx)**2 + (cy - gy)**2 + (cz - gz)**2
        )

    # Compute grid asymmetry: how far is the "active centroid" from grid centroid?
    if n_active > 0:
        active_cells = [c for c in cells if c["on"]]
        ax = sum(c["centroid"][0] for c in active_cells) / n_active
        ay = sum(c["centroid"][1] for c in active_cells) / n_active
        active_centroid = (ax, ay, 0.0)
        active_offset = math.sqrt(
            (ax - grid_centroid_x)**2 + (ay - grid_centroid_y)**2
        )
    else:
        active_centroid = grid_centroid
        active_offset = 0.0

    # Compute the bounding-box spread of active bits (a different "skew" view:
    # how spread out is the active information across the grid?)
    if n_active > 0:
        xs = [c["centroid"][0] for c in cells if c["on"]]
        ys = [c["centroid"][1] for c in cells if c["on"]]
        bbox_w = max(xs) - min(xs) if len(xs) > 1 else 0.0
        bbox_h = max(ys) - min(ys) if len(ys) > 1 else 0.0
    else:
        bbox_w = bbox_h = 0.0

    return {
        "rule": "mog_grid_scene",
        "cells": cells,
        "grid_centroid": grid_centroid,
        "active_centroid": active_centroid,
        "active_offset_from_grid_centroid": active_offset,
        "n_active": n_active,
        "bbox_width": bbox_w,
        "bbox_height": bbox_h,
        "bbox_aspect": bbox_w / bbox_h if bbox_h > 0 else 0.0,
        "all_points_count": len(all_points),
    }


# ════════════════════════════════════════════════════════════════════════════════
#  PART C — INTERACTION METRICS  (between two Data Objects)
# ════════════════════════════════════════════════════════════════════════════════

def interaction_golay_xor_snap(a: Dict, b: Dict) -> Dict[str, Any]:
    """
    XOR the two 24-bit Data Object vectors, snap to nearest Golay codeword,
    read syndrome weight + anchor distance = "interaction tax".
    """
    av, bv = a["bits24"], b["bits24"]
    xor = [av[i] ^ bv[i] for i in range(24)]
    snapped, meta = ubp.GOLAY_ENGINE.snap_to_codeword(xor)
    hw_xor = sum(xor)
    sw_xor = sum(ubp.GOLAY_ENGINE.syndrome(xor))
    tax_xor = ubp.LEECH_ENGINE.symmetry_tax(xor)
    tax_snapped = ubp.LEECH_ENGINE.symmetry_tax(snapped)
    # Hexacode shadow of XOR
    hex_xor, col_xor = ubp.GOLAY_ENGINE.mog_decompose(xor)
    hex_snap, col_snap = ubp.GOLAY_ENGINE.mog_decompose(snapped)
    return {
        "method": "golay_xor_snap",
        "xor_bits": xor,
        "xor_hamming_weight": hw_xor,
        "xor_syndrome_weight": sw_xor,
        "snapped": snapped,
        "snap_meta": meta,
        "tax_xor": str(tax_xor),
        "tax_snapped": str(tax_snapped),
        "nrci_xor": str(ubp.LEECH_ENGINE.calculate_nrci(xor)),
        "nrci_snapped": str(ubp.LEECH_ENGINE.calculate_nrci(snapped)),
        "hex_xor": hex_xor,
        "hex_snapped": hex_snap,
        "is_codeword": sw_xor == 0,
    }


def interaction_hexacode_shadow_diff(a: Dict, b: Dict) -> Dict[str, Any]:
    """
    Compare the 6 Hexacode GF(4) symbols of each Data Object symbol-wise.
    Measures "grammatical compatibility".
    """
    ha, hb = a["hex_symbols_raw"], b["hex_symbols_raw"]
    agreements = sum(1 for x, y in zip(ha, hb) if x == y)
    disagreements = 6 - agreements
    # GF(4) "distance": 0=identical, 1=differ by 1, 2=differ by 2, 3=differ by 3
    # In GF(4), nonzero differences form a 3-element group; treat as Lee-style.
    diffs = [x ^ y for x, y in zip(ha, hb)]  # GF(4) add = XOR
    nonzero_diffs = [d for d in diffs if d != 0]
    # Symbol-pair pattern: which positions agree / disagree
    pattern = ["=" if x == y else f"Δ{x}^{y}" for x, y in zip(ha, hb)]
    return {
        "method": "hexacode_shadow_diff",
        "hex_a": ha,
        "hex_b": hb,
        "agreements": agreements,
        "disagreements": disagreements,
        "diff_vector": diffs,
        "nonzero_diff_count": len(nonzero_diffs),
        "pattern": pattern,
        # A simple "grammatical distance" score
        "grammatical_distance": disagreements / 6.0,
    }


def interaction_spatial_scene_merge(a: Dict, b: Dict) -> Dict[str, Any]:
    """
    Build a combined 3D scene with both objects' MOG grids (using rule 3)
    placed side-by-side along the Y axis. Measure pairwise centroid distances
    and bounding-sphere overlap.
    """
    scene_a = skew_rule_mog_grid_scene(a["bits24"])
    scene_b = skew_rule_mog_grid_scene(b["bits24"])

    # Compute pairwise centroid distances between ACTIVE cells of A and B
    active_a = [c for c in scene_a["cells"] if c["on"]]
    active_b = [c for c in scene_b["cells"] if c["on"]]

    if not active_a or not active_b:
        return {
            "method": "spatial_scene_merge",
            "n_active_a": len(active_a),
            "n_active_b": len(active_b),
            "min_distance": None,
            "mean_distance": None,
            "overlap_count": 0,
            "note": "one or both objects have no active bits",
        }

    # Offset scene B by a fixed Y displacement (5 units above scene A's grid)
    y_offset = 5.0
    active_b_offset = [
        {**c, "centroid_offset": (c["centroid"][0], c["centroid"][1] + y_offset, c["centroid"][2])}
        for c in active_b
    ]

    distances = []
    overlap_count = 0
    for ca in active_a:
        for cb in active_b_offset:
            d = math.dist(ca["centroid"], cb["centroid_offset"])
            distances.append(d)
            # "overlap" if cells are within (radius_a + radius_b)
            if d < (ca["radius"] + cb["radius"]):
                overlap_count += 1

    return {
        "method": "spatial_scene_merge",
        "n_active_a": len(active_a),
        "n_active_b": len(active_b),
        "min_distance": min(distances),
        "mean_distance": statistics.mean(distances),
        "max_distance": max(distances),
        "std_distance": statistics.pstdev(distances) if len(distances) > 1 else 0.0,
        "overlap_count": overlap_count,
        "overlap_ratio": overlap_count / len(distances),
        # Asymmetry: ratio of active-cell counts
        "active_ratio": len(active_a) / max(len(active_b), 1),
    }


def interaction_spatial_arithmetic_op(a: Dict, b: Dict) -> Dict[str, Any]:
    """
    Encode each Data Object's integer fingerprint (the 24-bit vector
    interpreted as a binary integer) as a spatial_arithmetic operand,
    then build A + B, A * B, A - B scenes and observe the result polygon's
    properties.

    NOTE: the spatial_arithmetic codec caps polygon vertices at 100k
    (MAX_VERTICES). A full 24-bit value would need up to 2^25 vertices,
    so we cap the encoded integer at 50 (giving 104 vertices max). We keep
    two distinct fingerprints: the *full* integer (for arithmetic) and the
    *capped* integer (for polygon encoding).
    """
    # Convert 24-bit vector to integer (MSB first)
    int_a_full = sum((a["bits24"][i] << (23 - i)) for i in range(24))
    int_b_full = sum((b["bits24"][i] << (23 - i)) for i in range(24))

    # Cap for polygon encoding (avoid hitting MAX_VERTICES)
    # Use the lower 6 bits + 1 so polygon sizes stay modest (4..130 verts)
    int_a_cap = (int_a_full & 0x3F) + 1
    int_b_cap = (int_b_full & 0x3F) + 1

    # Encode each as a polygon
    poly_a = sa.encode(int_a_cap, seed=1)
    poly_b = sa.encode(int_b_cap, seed=2)

    ra = sa.radius_of(poly_a)
    rb = sa.radius_of(poly_b)
    ca = sa.centroid(poly_a)
    cb = sa.centroid(poly_b)
    dist_cents = math.dist(ca, cb)

    # Use radius_ratio as a proxy for "magnitude ratio"
    ra_norm, rb_norm, ratio = sa.radius_ratio(int_a_cap, int_b_cap)

    # natural_add (node-count identity) — use capped values
    nat_sum, note = sa.natural_add(int_a_cap, int_b_cap)

    # Build a formal scene A + B using build_scene (capped values)
    try:
        scene_pts = sa.build_scene(int_a_cap, int_b_cap, "ADD", seed=42)
        observed = sa.observe_scene(scene_pts)
        add_result = observed.get("result")
        add_ok = observed.get("ok")
    except Exception as e:
        add_result = None
        add_ok = False
        scene_pts = []
        observed = {"error": str(e)}

    # Build A * B scene (capped)
    try:
        scene_mul = sa.build_scene(int_a_cap, int_b_cap, "MULTIPLY", seed=43)
        observed_mul = sa.observe_scene(scene_mul)
        mul_result = observed_mul.get("result")
        mul_ok = observed_mul.get("ok")
    except Exception as e:
        mul_result = None
        mul_ok = False
        observed_mul = {"error": str(e)}

    # Build A - B scene (capped) — only meaningful if a >= b
    try:
        scene_sub = sa.build_scene(int_a_cap, int_b_cap, "SUBTRACT", seed=44) \
                    if int_a_cap >= int_b_cap else \
                    sa.build_scene(int_b_cap, int_a_cap, "SUBTRACT", seed=44)
        observed_sub = sa.observe_scene(scene_sub)
        sub_result = observed_sub.get("result")
        sub_ok = observed_sub.get("ok")
    except Exception as e:
        sub_result = None
        sub_ok = False
        observed_sub = {"error": str(e)}

    return {
        "method": "spatial_arithmetic_op",
        "int_a_full": int_a_full,
        "int_b_full": int_b_full,
        "int_a_cap": int_a_cap,
        "int_b_cap": int_b_cap,
        "int_a_full_log2": math.log2(int_a_full) if int_a_full > 0 else 0,
        "int_b_full_log2": math.log2(int_b_full) if int_b_full > 0 else 0,
        "poly_a_vertex_count": len(poly_a),
        "poly_b_vertex_count": len(poly_b),
        "poly_a_radius": ra,
        "poly_b_radius": rb,
        "poly_a_centroid": ca,
        "poly_b_centroid": cb,
        "centroid_distance": dist_cents,
        "radius_ratio": ratio,
        "natural_sum": nat_sum,
        "add_result": str(add_result) if add_result is not None else None,
        "add_ok": add_ok,
        "mul_result": str(mul_result) if mul_result is not None else None,
        "mul_ok": mul_ok,
        "sub_result": str(sub_result) if sub_result is not None else None,
        "sub_ok": sub_ok,
    }


# ════════════════════════════════════════════════════════════════════════════════
#  PART D — FULL PER-OBJECT REPORT
# ════════════════════════════════════════════════════════════════════════════════

def full_object_report(symbol: str,
                       prop_set: List[str] = None) -> Dict[str, Any]:
    """Compute the full per-object report including all 3 skew rules."""
    obj = encode_data_object(symbol, prop_set=prop_set)

    skew1 = skew_rule_weight_as_polygon(obj["bits24"])
    skew2 = skew_rule_index_as_polygon(obj["bits24"])
    skew3 = skew_rule_mog_grid_scene(obj["bits24"])

    # Aggregate skew statistics
    active_skew1 = [s["skew_magnitude"] for s in skew1 if s["on"]]
    active_skew2 = [s["prominence"] for s in skew2 if s["on"]]

    obj["skew_rule_1_weight_as_polygon"] = {
        "per_bit": skew1,
        "active_count": len(active_skew1),
        "mean_skew": statistics.mean(active_skew1) if active_skew1 else 0.0,
        "max_skew": max(active_skew1) if active_skew1 else 0.0,
        "min_skew": min(active_skew1) if active_skew1 else 0.0,
        "std_skew": statistics.pstdev(active_skew1) if len(active_skew1) > 1 else 0.0,
    }
    obj["skew_rule_2_index_as_polygon"] = {
        "per_bit": skew2,
        "active_count": len(active_skew2),
        "mean_prominence": statistics.mean(active_skew2) if active_skew2 else 0.0,
        "max_prominence": max(active_skew2) if active_skew2 else 0.0,
        "min_prominence": min(active_skew2) if active_skew2 else 0.0,
        "std_prominence": statistics.pstdev(active_skew2) if len(active_skew2) > 1 else 0.0,
    }
    obj["skew_rule_3_mog_grid_scene"] = {
        "cells": skew3["cells"],
        "n_active": skew3["n_active"],
        "active_offset_from_grid_centroid": skew3["active_offset_from_grid_centroid"],
        "bbox_width": skew3["bbox_width"],
        "bbox_height": skew3["bbox_height"],
        "bbox_aspect": skew3["bbox_aspect"],
    }
    return obj


# ════════════════════════════════════════════════════════════════════════════════
#  PART E — PAIR INTERACTION REPORT
# ════════════════════════════════════════════════════════════════════════════════

def full_pair_report(sym_a: str, sym_b: str,
                     prop_set: List[str] = None) -> Dict[str, Any]:
    """Compute the full pair interaction report."""
    obj_a = full_object_report(sym_a, prop_set=prop_set)
    obj_b = full_object_report(sym_b, prop_set=prop_set)

    known = ed.reaction_for(sym_a, sym_b)

    interactions = {
        "golay_xor_snap": interaction_golay_xor_snap(obj_a, obj_b),
        "hexacode_shadow_diff": interaction_hexacode_shadow_diff(obj_a, obj_b),
        "spatial_scene_merge": interaction_spatial_scene_merge(obj_a, obj_b),
        "spatial_arithmetic_op": interaction_spatial_arithmetic_op(obj_a, obj_b),
    }

    return {
        "pair": (sym_a, sym_b),
        "known_chemistry": known,
        "object_a": obj_a,
        "object_b": obj_b,
        "interactions": interactions,
    }


# ════════════════════════════════════════════════════════════════════════════════
#  PART F — SANITY SELF-TEST  (cheap, runs at import time if asked)
# ════════════════════════════════════════════════════════════════════════════════

def self_test():
    """Quick sanity check on a single element."""
    print("=" * 72)
    print("SELF TEST: encoding C (carbon)")
    print("=" * 72)
    rep = full_object_report("C")
    print(f"Element: {rep['symbol']}")
    print(f"Bits24:  {''.join(str(b) for b in rep['bits24'])}")
    print(f"MOG grid:")
    for r, name in enumerate(ROW_NAMES):
        row_bits = ''.join(str(b) for b in rep['mog_grid'][r])
        meta = rep['rows'][r]
        print(f"  Row {r} ({name:10s}) {row_bits}  "
              f"prop={meta['property']:8s} gray={meta['raw_value']:3d}  hw={meta['hamming_weight']}")
    print(f"Hamming weight: {rep['hamming_weight']}")
    print(f"Syndrome weight: {rep['syndrome_weight']}  (0 = already a Golay codeword)")
    print(f"Hexacode shadow (raw):    {rep['hex_symbols_raw']}")
    print(f"Hexacode shadow (snapped):{rep['hex_symbols_snapped']}")
    print(f"NRCI raw:     {float(rep['nrci_raw']):.4f}")
    print(f"NRCI snapped: {float(rep['nrci_snapped']):.4f}")
    print()
    print("Skew rule 1 (weight-as-polygon):")
    for s in rep["skew_rule_1_weight_as_polygon"]["per_bit"]:
        if s["on"]:
            print(f"  bit {s['bit']:2d}  weight=2^{s['weight_log2']:2d}={s['weight_raw']:>10d}  "
                  f"skew_mag={s['skew_magnitude']:8.4f}  verts={s['vertex_count']}")
    print()
    print("Skew rule 3 (MOG grid scene):")
    s3 = rep["skew_rule_3_mog_grid_scene"]
    print(f"  n_active: {s3['n_active']}")
    print(f"  active offset from grid centroid: {s3['active_offset_from_grid_centroid']:.4f}")
    print(f"  bbox: {s3['bbox_width']:.2f} x {s3['bbox_height']:.2f}  aspect={s3['bbox_aspect']:.3f}")
    print()
    print("Self-test OK.")


if __name__ == "__main__":
    self_test()
