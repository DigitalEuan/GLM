"""
Per-bit 24D Leech address encoder.

Each of the 24 bits in a Data Object gets its OWN 24D Leech point (not just
the GID). This opens a per-bit geometry space that the GID-level metrics
cannot see.

Four assignment schemes are tested (wide search):

  Scheme A — Standard basis (control, NOT a Leech point)
    bit i → vector e_i with magnitude = bit_value
    v_i = bit_value, v_j = 0 for j != i
    Norm² = bit_value² ∈ {0, 1}. NOT a Leech minimal vector.
    Purpose: baseline. If this works as well as Leech schemes, the Leech
    structure isn't adding signal.

  Scheme B — Class A pair (±4, ±4, 0²²)
    bit i → vector with +4 at position i and +4 at position (i + 12) mod 24,
    sign-flipped if bit_value = 0.
    v_i = +4 if bit=1 else -4
    v_{(i+12) mod 24} = +4 if bit=1 else -4
    All others = 0.
    Norm² = 32. ✓ Leech minimal vector (Class A).
    Purpose: pure Z^24 feature, no Golay involvement.

  Scheme C — Class C single-coordinate (±3, ±1²³)
    bit i → vector with v_i = ±3, v_j = +1 for j != i.
    Sign of v_i depends on bit_value: +3 if bit=1, -3 if bit=0.
    Norm² = 9 + 23 = 32. ✓ Leech minimal vector (Class C, using c=0 codeword).
    Purpose: cleanest Leech minimal vector, one per bit position.

  Scheme D — Class B octad (±2⁸, 0¹⁶)
    bit i → expand the i-th canonical octad (from the 759), use Class B
    vector with all +2's at octad positions.
    Norm² = 32. ✓ Leech minimal vector (Class B).
    Purpose: brings in octad structure (Golay depth).
    NOTE: 24 bits, 759 octads. We pick 24 canonical octads — one per bit
    position — by selecting the octad whose k-th active position is i,
    where k = i mod 8. This gives a deterministic, position-canonical map.

For each scheme, we provide:
  - bit_to_leech(i, bit_value) -> List[int] (24-integer coordinate)
  - encode(bits24) -> List[List[int]] (24 Leech points, one per bit)
  - intra_object_geometry(bits24) -> Dict of geometric quantities
  - inter_object_geometry(bits_a, bits_b) -> Dict of pair quantities
"""

from __future__ import annotations

import sys
import math
import statistics
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa


# ════════════════════════════════════════════════════════════════════════════════
# Pre-compute the 24 canonical octads for Scheme D
# ════════════════════════════════════════════════════════════════════════════════

def _build_canonical_octads() -> List[List[int]]:
    """For each bit position i in [0, 24], pick one octad that contains i.

    We pick the octad whose (i mod 8)-th active position is i, choosing the
    first such octad in the canonical Golay octad list. This is deterministic.
    """
    octads = ubp.GOLAY_ENGINE.get_octads()  # 759 octads
    canonical = []
    for i in range(24):
        k = i % 8  # which active position should be i
        found = None
        for octad in octads:
            active = [j for j, b in enumerate(octad) if b]
            if len(active) == 8 and active[k] == i:
                found = list(octad)
                break
        if found is None:
            # Fallback: pick the first octad containing i
            for octad in octads:
                if octad[i] == 1:
                    found = list(octad)
                    break
        canonical.append(found if found else [0]*24)
    return canonical


CANONICAL_OCTADS = _build_canonical_octads()


# ════════════════════════════════════════════════════════════════════════════════
# Scheme encoders
# ════════════════════════════════════════════════════════════════════════════════

def bit_to_leech_scheme_a(i: int, bit_value: int) -> List[int]:
    """Scheme A: standard basis. v_i = bit_value, else 0. NOT Leech."""
    v = [0] * 24
    v[i] = int(bit_value)
    return v


def bit_to_leech_scheme_b(i: int, bit_value: int) -> List[int]:
    """Scheme B: Class A pair (±4, ±4, 0²²) at positions i and (i+12) mod 24."""
    v = [0] * 24
    sign = +4 if bit_value else -4
    v[i] = sign
    v[(i + 12) % 24] = sign
    return v


def bit_to_leech_scheme_c(i: int, bit_value: int) -> List[int]:
    """Scheme C: Class C single-coordinate (±3, ±1²³). v_i = ±3, v_j = +1."""
    v = [1] * 24
    v[i] = +3 if bit_value else -3
    return v


def bit_to_leech_scheme_d(i: int, bit_value: int) -> List[int]:
    """Scheme D: Class B octad (±2⁸, 0¹⁶) on canonical octad for position i.

    Bit value modulates the sign of all 8 active coordinates.
    """
    octad = CANONICAL_OCTADS[i]
    v = [0] * 24
    sign = +2 if bit_value else -2
    for j in range(24):
        if octad[j] == 1:
            v[j] = sign
    return v


SCHEMES = {
    "A_basis":    bit_to_leech_scheme_a,
    "B_classA":   bit_to_leech_scheme_b,
    "C_classC":   bit_to_leech_scheme_c,
    "D_classB":   bit_to_leech_scheme_d,
}


def encode_bits_to_leech(bits24: List[int], scheme: str = "C_classC") -> List[List[int]]:
    """Encode a 24-bit Data Object into 24 Leech points (one per bit)."""
    fn = SCHEMES[scheme]
    return [fn(i, bits24[i]) for i in range(24)]


# ════════════════════════════════════════════════════════════════════════════════
# Intra-object geometry (per single Data Object)
# ════════════════════════════════════════════════════════════════════════════════

def _euclidean_sq(a: List[int], b: List[int]) -> int:
    """Squared Euclidean distance between two 24D integer vectors."""
    return sum((a[i] - b[i])**2 for i in range(24))


def _euclidean(a: List[int], b: List[int]) -> float:
    return math.sqrt(_euclidean_sq(a, b))


def intra_object_geometry(bits24: List[int], scheme: str = "C_classC") -> Dict:
    """Compute intra-object geometry: 24 Leech points' structural properties.

    Returns:
      - leech_points : List of 24 Leech points (24-int tuples)
      - centroid : 24-D centroid (mean of 24 points)
      - centroid_norm_sq : squared norm of centroid
      - rms_spread : RMS distance of points from centroid
      - max_pairwise_dist : max distance between any two bit-Leech points
      - mean_pairwise_dist : mean distance between all C(24,2)=276 pairs
      - pairwise_dist_matrix : 24x24 distance matrix
      - active_only_centroid : centroid of points where bit_value=1
      - active_only_rms : RMS spread of active-bit points
      - active_only_max_dist : max pairwise distance among active bits
      - per_bit_norm_sq : list of 24 norm² values (one per bit)
      - per_bit_tax : list of 24 symmetry_tax values (one per bit)
      - per_bit_nrci : list of 24 NRCI values
      - total_tax : sum of per-bit taxes
      - mean_tax : mean of per-bit taxes
      - anisotropy : ratio of largest to smallest eigenvalue of covariance matrix
                     (24x24 covariance of the 24 Leech points; needs numpy)
    """
    pts = encode_bits_to_leech(bits24, scheme)
    n = len(pts)  # 24
    dim = 24

    # Centroid
    centroid = [sum(p[i] for p in pts) / n for i in range(dim)]

    # RMS spread
    rms_sq = sum(_euclidean_sq(p, [int(round(c)) for c in centroid]) for p in pts) / n
    rms_spread = math.sqrt(rms_sq)

    # Pairwise distances
    pairwise = [[0.0]*n for _ in range(n)]
    dists = []
    for i in range(n):
        for j in range(i+1, n):
            d = _euclidean(pts[i], pts[j])
            pairwise[i][j] = d
            pairwise[j][i] = d
            dists.append(d)
    max_pairwise = max(dists) if dists else 0.0
    mean_pairwise = statistics.mean(dists) if dists else 0.0
    std_pairwise = statistics.pstdev(dists) if len(dists) > 1 else 0.0

    # Active-only stats (bits that are ON)
    active_indices = [i for i, b in enumerate(bits24) if b == 1]
    if len(active_indices) >= 2:
        active_pts = [pts[i] for i in active_indices]
        active_centroid = [sum(p[i] for p in active_pts) / len(active_pts) for i in range(dim)]
        active_rms = math.sqrt(sum(_euclidean_sq(p, [int(round(c)) for c in active_centroid])
                                    for p in active_pts) / len(active_pts))
        active_dists = []
        for i in range(len(active_pts)):
            for j in range(i+1, len(active_pts)):
                active_dists.append(_euclidean(active_pts[i], active_pts[j]))
        active_max = max(active_dists)
        active_mean = statistics.mean(active_dists)
    else:
        active_centroid = [0.0] * dim
        active_rms = 0.0
        active_max = 0.0
        active_mean = 0.0

    # Per-bit norm², tax, NRCI
    per_bit_norm_sq = [_euclidean_sq(p, [0]*dim) for p in pts]
    per_bit_tax = [float(ubp.LEECH_ENGINE.symmetry_tax(p)) for p in pts]
    per_bit_nrci = [float(ubp.LEECH_ENGINE.calculate_nrci(p)) for p in pts]
    total_tax = sum(per_bit_tax)
    mean_tax = statistics.mean(per_bit_tax)

    # Centroid norm² (as float)
    centroid_norm_sq = sum(c*c for c in centroid)

    return {
        "scheme": scheme,
        "leech_points": pts,
        "centroid": centroid,
        "centroid_norm_sq": centroid_norm_sq,
        "rms_spread": rms_spread,
        "max_pairwise_dist": max_pairwise,
        "mean_pairwise_dist": mean_pairwise,
        "std_pairwise_dist": std_pairwise,
        "pairwise_dist_matrix": pairwise,
        "active_count": len(active_indices),
        "active_only_centroid": active_centroid,
        "active_only_rms": active_rms,
        "active_only_max_dist": active_max,
        "active_only_mean_dist": active_mean,
        "per_bit_norm_sq": per_bit_norm_sq,
        "per_bit_tax": per_bit_tax,
        "per_bit_nrci": per_bit_nrci,
        "total_tax": total_tax,
        "mean_tax": mean_tax,
        "bits24": bits24,
    }


# ════════════════════════════════════════════════════════════════════════════════
# Inter-object geometry (between two Data Objects)
# ════════════════════════════════════════════════════════════════════════════════

def inter_object_geometry(bits_a: List[int], bits_b: List[int],
                          scheme: str = "C_classC") -> Dict:
    """Compute inter-object bit-pair geometry.

    For each bit position i, we have Leech point A_i (from object A) and
    Leech point B_i (from object B). Compute:
      - per_bit_distance[i] : Euclidean distance between A_i and B_i
      - per_bit_dot[i]      : dot product A_i · B_i
      - per_bit_xor_tax[i]  : symmetry_tax of (A_i XOR B_i) — but XOR of two
                              Leech points isn't well-defined; instead use
                              symmetry_tax of (A_i - B_i) as a difference vector
      - sum_distance, mean_distance, min_distance, max_distance
      - alignment_count : how many bit positions have A_i "close to" B_i
                          (distance < threshold)
      - bit_alignment_score : fraction of bit positions where the sign of
                              A_i's dominant coord matches B_i's
      - centroid_distance : distance between centroids of A and B's Leech points
      - active_overlap : for bits where BOTH A and B have bit=1, count and mean dist
      - sign_flip_count : for each bit position, did the bit value flip?
                          (just sum(bits_a XOR bits_b))
    """
    pts_a = encode_bits_to_leech(bits_a, scheme)
    pts_b = encode_bits_to_leech(bits_b, scheme)

    per_bit_distance = []
    per_bit_dot = []
    per_bit_diff_tax = []
    alignment_count = 0
    sign_flip_count = 0
    active_overlap_dists = []

    for i in range(24):
        a = pts_a[i]
        b = pts_b[i]
        d = _euclidean(a, b)
        per_bit_distance.append(d)
        dot = sum(a[j] * b[j] for j in range(24))
        per_bit_dot.append(dot)

        # Difference vector and its tax
        diff = [a[j] - b[j] for j in range(24)]
        diff_tax = float(ubp.LEECH_ENGINE.symmetry_tax(diff))
        per_bit_diff_tax.append(diff_tax)

        # Alignment: distance < threshold (1.0 means "essentially identical")
        if d < 1.0:
            alignment_count += 1

        # Sign flip?
        if bits_a[i] != bits_b[i]:
            sign_flip_count += 1

        # Active overlap (both bits ON)
        if bits_a[i] == 1 and bits_b[i] == 1:
            active_overlap_dists.append(d)

    sum_distance = sum(per_bit_distance)
    mean_distance = statistics.mean(per_bit_distance)
    min_distance = min(per_bit_distance)
    max_distance = max(per_bit_distance)
    std_distance = statistics.pstdev(per_bit_distance)

    # Centroid distance
    ca = [sum(p[i] for p in pts_a) / 24 for i in range(24)]
    cb = [sum(p[i] for p in pts_b) / 24 for i in range(24)]
    centroid_distance = _euclidean(ca, cb)

    return {
        "scheme": scheme,
        "per_bit_distance": per_bit_distance,
        "per_bit_dot": per_bit_dot,
        "per_bit_diff_tax": per_bit_diff_tax,
        "sum_distance": sum_distance,
        "mean_distance": mean_distance,
        "min_distance": min_distance,
        "max_distance": max_distance,
        "std_distance": std_distance,
        "alignment_count": alignment_count,
        "alignment_score": alignment_count / 24,
        "sign_flip_count": sign_flip_count,
        "centroid_distance": centroid_distance,
        "active_overlap_count": len(active_overlap_dists),
        "active_overlap_mean_dist": (statistics.mean(active_overlap_dists)
                                      if active_overlap_dists else 0.0),
        "total_diff_tax": sum(per_bit_diff_tax),
        "mean_diff_tax": statistics.mean(per_bit_diff_tax),
    }


# ════════════════════════════════════════════════════════════════════════════════
# Spatial Arithmetic integration
# ════════════════════════════════════════════════════════════════════════════════

def spatial_arithmetic_on_per_bit_leech(bits24: List[int],
                                         scheme: str = "C_classC") -> Dict:
    """Encode each bit's Leech point as a Spatial Arithmetic polygon.

    For each bit's Leech point, compute:
      - norm² (integer)
      - symmetry_tax (Fraction -> float)
      - hamming_weight (int)

    Then encode these as Spatial Arithmetic polygons:
      - Encode norm² / 8 as a polygon (capped at 50 to avoid 100k vertex limit)
      - Compute pairwise centroid distances between polygons
      - Compute the "spatial signature" of the Data Object

    Returns a dict with per-bit polygon stats and overall scene stats.
    """
    pts = encode_bits_to_leech(bits24, scheme)

    # Encode each bit's norm² as a polygon (capped)
    per_bit_polygons = []
    for i, p in enumerate(pts):
        ns = sum(c*c for c in p)  # integer
        # Cap at 50 to avoid 100k vertex limit (encode value = min(ns, 50))
        encoded_val = min(ns, 50)
        if encoded_val == 0:
            per_bit_polygons.append(None)
            continue
        try:
            poly = sa.encode(encoded_val, seed=i)
            per_bit_polygons.append(poly)
        except Exception:
            per_bit_polygons.append(None)

    # Compute centroid of each polygon (in 3D)
    centroids_3d = []
    for poly in per_bit_polygons:
        if poly is None:
            centroids_3d.append(None)
        else:
            centroids_3d.append(sa.centroid(poly))

    # Compute pairwise 3D distances between polygon centroids
    pairwise_3d_dists = []
    for i in range(24):
        if centroids_3d[i] is None:
            continue
        for j in range(i+1, 24):
            if centroids_3d[j] is None:
                continue
            d = math.dist(centroids_3d[i], centroids_3d[j])
            pairwise_3d_dists.append(d)

    # Overall scene stats
    scene_stats = {
        "n_polygons": sum(1 for p in per_bit_polygons if p is not None),
        "mean_3d_dist": statistics.mean(pairwise_3d_dists) if pairwise_3d_dists else 0.0,
        "max_3d_dist": max(pairwise_3d_dists) if pairwise_3d_dists else 0.0,
        "min_3d_dist": min(pairwise_3d_dists) if pairwise_3d_dists else 0.0,
        "std_3d_dist": statistics.pstdev(pairwise_3d_dists) if len(pairwise_3d_dists) > 1 else 0.0,
    }

    # Build a scene with all polygons laid out along X axis (with spacing)
    # and measure overall centroid, bounding box
    all_points = []
    for i, poly in enumerate(per_bit_polygons):
        if poly is None:
            continue
        offset_x = float(i * 5.0)  # space polygons along X
        poly_t = sa.translate(poly, (offset_x, 0.0, 0.0))
        all_points.extend(poly_t)

    if all_points:
        overall_centroid = (
            sum(p[0] for p in all_points) / len(all_points),
            sum(p[1] for p in all_points) / len(all_points),
            sum(p[2] for p in all_points) / len(all_points),
        )
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        zs = [p[2] for p in all_points]
        bbox = (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
    else:
        overall_centroid = (0, 0, 0)
        bbox = (0, 0, 0)

    return {
        "scheme": scheme,
        "per_bit_norm_sq": [sum(c*c for c in p) for p in pts],
        "per_bit_hamming_weight": [sum(1 for c in p if c != 0) for p in pts],
        "per_bit_tax": [float(ubp.LEECH_ENGINE.symmetry_tax(p)) for p in pts],
        "per_bit_nrci": [float(ubp.LEECH_ENGINE.calculate_nrci(p)) for p in pts],
        "scene_stats": scene_stats,
        "overall_centroid_3d": overall_centroid,
        "bbox_3d": bbox,
        "n_scene_points": len(all_points),
    }


# ════════════════════════════════════════════════════════════════════════════════
# Self-test
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 78)
    print("PER-BIT LEECH ENCODER — SELF TEST")
    print("=" * 78)

    # Use Carbon's KB-hardened vector
    import ubp_kb_loader as kb
    c = kb.get_element("C")
    bits = c.vector24

    print(f"\nElement: C  bits={bits}  HW={sum(bits)}")
    print()

    for scheme in SCHEMES:
        print(f"── Scheme {scheme} ──")
        pts = encode_bits_to_leech(bits, scheme)
        # Show first 3 points
        for i in range(3):
            print(f"  bit {i} (val={bits[i]}): {pts[i][:8]}... norm²={sum(c*c for c in pts[i])}")
        # Intra-object geometry
        intra = intra_object_geometry(bits, scheme)
        print(f"  RMS spread: {intra['rms_spread']:.4f}")
        print(f"  Max pairwise dist: {intra['max_pairwise_dist']:.4f}")
        print(f"  Mean pairwise dist: {intra['mean_pairwise_dist']:.4f}")
        print(f"  Active bits: {intra['active_count']}")
        print(f"  Active RMS: {intra['active_only_rms']:.4f}")
        print(f"  Total per-bit tax: {intra['total_tax']:.4f}")
        print(f"  Mean per-bit tax: {intra['mean_tax']:.4f}")
        print()

    # Inter-object test: C vs O
    o = kb.get_element("O")
    print(f"\n── Inter-object: C vs O ──")
    for scheme in SCHEMES:
        inter = inter_object_geometry(bits, o.vector24, scheme)
        print(f"  Scheme {scheme}:")
        print(f"    Sum distance: {inter['sum_distance']:.4f}")
        print(f"    Mean distance: {inter['mean_distance']:.4f}")
        print(f"    Min distance: {inter['min_distance']:.4f}")
        print(f"    Max distance: {inter['max_distance']:.4f}")
        print(f"    Alignment count: {inter['alignment_count']}/24")
        print(f"    Sign flips: {inter['sign_flip_count']}")
        print(f"    Centroid distance: {inter['centroid_distance']:.4f}")
        print(f"    Total diff tax: {inter['total_diff_tax']:.4f}")
        print()
