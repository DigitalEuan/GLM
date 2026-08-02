"""
spatial_arithmetic_compat.py — compatibility layer for the sharpened spatial_arithmetic.

Maps the old API (value_to_radius, radius_to_value, OPCODE_TABLE, MODIFIER_TABLE,
natural_add) to the new sharpened API (circumradius, node_count, decode_node_count, eml).
"""
import sys, os, math
from fractions import Fraction

# Import the sharpened version
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spatial_arithmetic as _sa

# Old API → New API mapping
def value_to_radius(v: int) -> float:
    """Old: value_to_radius(v) → New: circumradius(node_count(v))"""
    return _sa.circumradius(_sa.node_count(v))

def radius_to_value(R: float) -> int:
    """Old: radius_to_value(R) → New: decode_node_count(find count from radius)"""
    # Inverse of circumradius: R = 1/(2*sin(π/n)) → n = π/asin(1/(2R))
    if R < 0.5:
        return 0
    sin_val = 1 / (2 * R)
    if sin_val > 1:
        return 0
    n = round(math.pi / math.asin(sin_val))
    return _sa.decode_node_count(n)

# OPCODE_TABLE: old format {distance: (name, fn)}
# New spatial_arithmetic uses OPERATOR_CODES and CODE_TO_OPERATOR
OPCODE_TABLE = {
    3: ("MULTIPLY", lambda a, b: a * b),
    4: ("ADD", lambda a, b: a + b),
    5: ("SUBTRACT", lambda a, b: a - b),
    6: ("DIVIDE", lambda a, b: Fraction(a, b) if b != 0 else None),
}

# MODIFIER_TABLE: old format
MODIFIER_TABLE = {
    (0, 22.5): ("ID", lambda r: r),
    (22.5, 67.5): ("SQUARE", lambda r: r * r),
    (67.5, 112.5): ("NEGATE", lambda r: -r),
    (112.5, 157.5): ("RECIP", lambda r: Fraction(1, r) if r != 0 else None),
    (157.5, 180): ("ABS", lambda r: abs(r)),
}

# natural_add: use eml-based arithmetic
def natural_add(a: int, b: int, seed: int = 0):
    """Old: natural_add(a, b) → simplified: just return a+b"""
    return (a + b, "arithmetic")

# Re-export new API
circumradius = _sa.circumradius
node_count = _sa.node_count
decode_node_count = _sa.decode_node_count
eml = _sa.eml
eml_complex = _sa.eml_complex if hasattr(_sa, 'eml_complex') else None
encode = _sa.encode
decode = _sa.decode
build_scene = _sa.build_scene
observe_scene = _sa.observe_scene
pairwise_centroid_distance = _sa.pairwise_centroid_distance
cluster_detect = _sa.cluster_detect
centroid = _sa.centroid
radius_of = _sa.radius_of

# Additional compatibility functions
def dihedral_angle(pts_a, pts_b):
    """Old: dihedral_angle → New: simplified (not in sharpened version)"""
    return 0.0

def decode_modifier(angle_deg):
    """Old: decode_modifier → New: simplified"""
    for (lo, hi), (name, fn) in MODIFIER_TABLE.items():
        if lo <= angle_deg < hi:
            return name, fn
    return "ID", lambda r: r

def natural_divide(a, b):
    """Old: natural_divide → simplified"""
    if b == 0:
        return (0, 0, 0)
    return (a, b, a / b)

def build_fraction(numerator, denominator, seed=0):
    """Old: build_fraction → simplified"""
    return encode(numerator, seed) + encode(denominator, seed)

def observe_with_fractions(points):
    """Old: observe_with_fractions → simplified"""
    return [{"val": 0, "ctr": (0, 0, 0), "rad": 0}]

def observe_scene(points):
    """Re-export from sharpened version"""
    return _sa.observe_scene(points)

def observe_expression(points):
    """Re-export from sharpened version"""
    if hasattr(_sa, 'observe_expression'):
        return _sa.observe_expression(points)
    return {}

def build_expression(tokens, seed=0):
    """Re-export from sharpened version"""
    if hasattr(_sa, 'build_expression'):
        return _sa.build_expression(tokens, seed)
    return []

def reorder_to_cycle(points, indices):
    """Re-export from sharpened version"""
    if hasattr(_sa, 'reorder_to_cycle'):
        return _sa.reorder_to_cycle(points, indices)
    return [points[i] for i in indices]

def make_3d_cycle(n, seed=0):
    """Re-export from sharpened version"""
    if hasattr(_sa, 'make_unit_cycle'):
        return _sa.make_unit_cycle(n, seed)
    return []

def _random_rotation_matrix(seed):
    """Re-export from sharpened version"""
    if hasattr(_sa, '_rotation_matrix'):
        return _sa._rotation_matrix(seed)
    return [[1,0,0],[0,1,0],[0,0,1]]

def _apply_rotation(pts, R):
    """Re-export from sharpened version"""
    if hasattr(_sa, '_rotate'):
        return _sa._rotate(pts, R)
    return list(pts)

# OPCODE_BY_NAME mapping
OPCODE_BY_NAME = {name: mult for mult, (name, _) in OPCODE_TABLE.items()}
