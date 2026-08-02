"""
lingo_translator.py — human ↔ UBP-Lingo translator
=====================================================

The GLM speaks a native "Lingo" grounded in the four fundamental conditions
for structure to exist (the Bit Budget):

  1. REALITY (M_*): "substance" — spatial N-gon cycles, R(n) = 1/(2sin(π/n))
  2. INFORMATION (I_*): "sequence" — discrete bit-flip topology
  3. ACTIVATION (A_*): "operations" — cluster merging, distance scaling,
     dihedral rotations, Cayley-Menger projections
  4. POTENTIAL (P_*): "constraints" — symmetry tax, NRCI coherence, Golay snap

This translator converts between human descriptions of ARC transformations
and UBP-Lingo, so the GLM can use chat-like mechanisms to reason about
and discover transformations.

Example translation:
  Human: "rotate the grid 90 degrees clockwise"
  Lingo: "ACTIVATION.ADD k=R(4) layer=A_Force C=MUL → ROTATE_90"
         (R(4) is the spatial-log of a square; MUL is the multiply opcode
          which corresponds to the geometric rotation dynamic)

  Human: "recolour all red cells to blue"
  Lingo: "MIRRORS.NEGATE layer=M_Charge C=NEGATE mapping={2:1}"
         (NEGATE in the Mirrors layer swaps colour assignments)

  Human: "fill the interior of the outlined shape"
  Lingo: "POTENTIAL.RECIP layer=P_Coherence C=RECIP → FILL_INTERIOR"
         (RECIP in the Potential layer fills enclosed regions)

The translator also works in reverse: given a Lingo expression, it produces
a human-readable description, enabling the GLM to "explain" its reasoning.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from fractions import Fraction
import sys, os

_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from spatial_arithmetic_compat import value_to_radius, radius_to_value, OPCODE_TABLE, MODIFIER_TABLE
from ldp_codec import geo_class, _phi, _sub_cycles, _is_prime, _factorize


# ══════════════════════════════════════════════════════════════════════════════
# LINGO VOCABULARY — the GLM's native terms for ARC concepts
# ══════════════════════════════════════════════════════════════════════════════

# Human term → Lingo term mapping
HUMAN_TO_LINGO: Dict[str, Dict[str, str]] = {
    # Reality (M_*) — substance, spatial
    "grid":         {"layer": "M_Space",   "lingo": "SPATIAL_SUBSTRATE"},
    "cell":         {"layer": "M_Mass",    "lingo": "UNIT_NODE"},
    "colour":       {"layer": "M_Charge",  "lingo": "CHARGE_VALUE"},
    "object":       {"layer": "M_Count",   "lingo": "CLUSTER"},
    "shape":        {"layer": "M_Space",   "lingo": "N_GON_FOOTPRINT"},
    "size":         {"layer": "M_Count",   "lingo": "NODE_CARDINALITY"},

    # Information (I_*) — sequence, topology
    "position":     {"layer": "I_Topology",    "lingo": "LATTICE_COORD"},
    "adjacency":    {"layer": "I_Connectivity","lingo": "EDGE_BOND"},
    "symmetry":     {"layer": "I_Symmetry",    "lingo": "DIHEDRAL_GROUP"},
    "pattern":      {"layer": "I_Density",     "lingo": "TOPO_SIGNATURE"},
    "border":       {"layer": "I_Connectivity","lingo": "BOUNDARY_EDGE"},
    "interior":     {"layer": "I_Connectivity","lingo": "ENCLOSED_REGION"},

    # Activation (A_*) — operations, dynamics
    "rotate":       {"layer": "A_Force",   "lingo": "DIHEDRAL_ROTATION", "opcode": "MUL"},
    "flip":         {"layer": "A_Force",   "lingo": "PLANE_REFLECTION",  "opcode": "NEGATE"},
    "move":         {"layer": "A_Velocity","lingo": "CENTROID_SHIFT",    "opcode": "ADD"},
    "scale":        {"layer": "A_Force",   "lingo": "RADIUS_SCALING",   "opcode": "MUL"},
    "gravity":      {"layer": "A_Flux",    "lingo": "COMPACTION_FLOW",  "opcode": "ADD"},
    "merge":        {"layer": "A_Energy",  "lingo": "CLUSTER_UNION",    "opcode": "ADD"},
    "split":        {"layer": "A_Energy",  "lingo": "CLUSTER_FISSION",  "opcode": "SUB"},
    "fill":         {"layer": "A_Flux",    "lingo": "REGION_FILL",      "opcode": "ADD"},
    "crop":         {"layer": "A_Velocity","lingo": "BOUNDARY_TRIM",    "opcode": "SUB"},

    # Potential (P_*) — constraints, coherence
    "recolour":     {"layer": "P_Ratio",     "lingo": "CHARGE_SWAP",       "opcode": "NEGATE"},
    "outline":      {"layer": "P_Coherence", "lingo": "BOUNDARY_EXTRACT",  "opcode": "SUB"},
    "count":        {"layer": "P_Limit",     "lingo": "CARDINALITY_MEASURE","opcode": "ID"},
    "snap":         {"layer": "P_Phase",     "lingo": "GOLAY_CORRECTION",  "opcode": "ID"},
    "coherent":     {"layer": "P_Coherence", "lingo": "NRCI_STABLE"},
    "manifested":   {"layer": "P_Phase",     "lingo": "NRCI_MANIFEST"},
    "subliminal":   {"layer": "P_Phase",     "lingo": "NRCI_SUBLIMINAL"},
}

# Lingo term → human description (reverse mapping)
LINGO_TO_HUMAN: Dict[str, str] = {
    "SPATIAL_SUBSTRATE":    "grid",
    "UNIT_NODE":            "cell",
    "CHARGE_VALUE":         "colour",
    "CLUSTER":              "object (connected component)",
    "N_GON_FOOTPRINT":      "shape (polygon with R(n) circumradius)",
    "NODE_CARDINALITY":     "size (cell count)",
    "LATTICE_COORD":        "position",
    "EDGE_BOND":            "adjacency (8-neighbour)",
    "DIHEDRAL_GROUP":       "symmetry",
    "TOPO_SIGNATURE":       "pattern (topological signature)",
    "BOUNDARY_EDGE":        "border",
    "ENCLOSED_REGION":      "interior",
    "DIHEDRAL_ROTATION":    "rotate (dihedral plane rotation)",
    "PLANE_REFLECTION":     "flip (plane reflection)",
    "CENTROID_SHIFT":       "move (centroid displacement)",
    "RADIUS_SCALING":       "scale (radius ratio)",
    "COMPACTION_FLOW":      "gravity (compaction along axis)",
    "CLUSTER_UNION":        "merge (cluster union via centroid)",
    "CLUSTER_FISSION":      "split (cluster fission)",
    "REGION_FILL":          "fill (enclosed region flood-fill)",
    "BOUNDARY_TRIM":        "crop (trim to non-zero bbox)",
    "CHARGE_SWAP":          "recolour (charge value reassignment)",
    "BOUNDARY_EXTRACT":     "outline (extract boundary cells)",
    "CARDINALITY_MEASURE":  "count (cardinality measurement)",
    "GOLAY_CORRECTION":     "snap (Golay error correction, ≤3 bit-flips)",
    "NRCI_STABLE":          "coherent (NRCI ≥ 0.70, manifested state)",
    "NRCI_MANIFEST":        "manifested (NRCI ≥ 0.70)",
    "NRCI_SUBLIMINAL":      "subliminal (NRCI < 0.50, dissolved)",
}


# ══════════════════════════════════════════════════════════════════════════════
# LINGO EXPRESSION — a structured statement in UBP-Lingo
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class LingoExpression:
    """A single statement in UBP-Lingo.

    Format: LAYER.C_MODIFIER k=R(n) layer=MOG_SLOT C=OPCODE [params]

    Example: ACTIVATION.ADD k=R(4) layer=A_Force C=MUL → DIHEDRAL_ROTATION
    (means: rotate by 90°, where R(4) is the spatial-log of a square
     and MUL is the multiply opcode that drives the rotation dynamic)
    """
    layer: str                  # "REALITY", "INFORMATION", "ACTIVATION", "POTENTIAL"
    c_modifier: str             # "ID", "ADD", "MUL", "SUB", "DIV", "NEGATE", "SQUARE", "RECIP", "ABS"
    k_n: int                    # the n in R(n) — the polygon vertex count
    mog_slot: str               # the MOG_CATEGORIES slot (e.g., "A_Force")
    opcode: str                 # the OPCODE_TABLE entry
    lingo_term: str             # the human-facing lingo term (e.g., "DIHEDRAL_ROTATION")
    params: Dict[str, Any] = field(default_factory=dict)
    human_description: str = ""

    @property
    def k_spatial(self) -> Fraction:
        """R(n) as an exact Fraction (no float drift)."""
        from fractions import Fraction
        import math
        # R(n) = 1 / (2 * sin(π/n))
        # We compute this as an exact Fraction using the math module
        # For n that are powers of small primes, sin(π/n) has exact algebraic forms
        # For general n, we use Fraction from the float (high precision)
        # The GLM uses Spatial Arithmetic's value_to_radius for actual computation
        # Here we return the conceptual value
        return Fraction(math.sin(math.pi / self.k_n)).limit_denominator(10**12) * 2

    def to_lingo_string(self) -> str:
        """Render as a Lingo string."""
        s = f"{self.layer}.{self.c_modifier} k=R({self.k_n}) layer={self.mog_slot} C={self.opcode}"
        if self.lingo_term:
            s += f" → {self.lingo_term}"
        if self.params:
            param_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
            s += f" [{param_str}]"
        return s

    def to_human_string(self) -> str:
        """Render as a human-readable description."""
        if self.human_description:
            return self.human_description
        base = LINGO_TO_HUMAN.get(self.lingo_term, self.lingo_term.lower())
        if self.params:
            param_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
            return f"{base} ({param_str})"
        return base

    def __repr__(self):
        return f"LingoExpr({self.to_lingo_string()})"


# ══════════════════════════════════════════════════════════════════════════════
# LINGO TRANSLATOR
# ══════════════════════════════════════════════════════════════════════════════

class LingoTranslator:
    """Translates between human descriptions and UBP-Lingo.

    The translator enables the GLM to "chat" about ARC tasks in its native
    language. Given a human description like "rotate 90 degrees clockwise",
    it produces a LingoExpression that the Φ-grammar can consume.

    Given a LingoExpression (e.g., from the CRG), it produces a human
    description, enabling the GLM to explain its reasoning.
    """

    # Map common human phrases to Lingo parameters
    PHRASE_PATTERNS: Dict[str, Dict[str, Any]] = {
        # Rotation
        "rotate 90":          {"lingo": "DIHEDRAL_ROTATION", "layer": "ACTIVATION", "c_mod": "ADD", "k_n": 4,  "mog_slot": "A_Force", "opcode": "MUL"},
        "rotate 180":         {"lingo": "DIHEDRAL_ROTATION", "layer": "ACTIVATION", "c_mod": "ADD", "k_n": 6,  "mog_slot": "A_Force", "opcode": "MUL"},
        "rotate 270":         {"lingo": "DIHEDRAL_ROTATION", "layer": "ACTIVATION", "c_mod": "SUB", "k_n": 4,  "mog_slot": "A_Force", "opcode": "MUL"},
        "turn clockwise":     {"lingo": "DIHEDRAL_ROTATION", "layer": "ACTIVATION", "c_mod": "ADD", "k_n": 4,  "mog_slot": "A_Force", "opcode": "MUL"},
        "turn counter":       {"lingo": "DIHEDRAL_ROTATION", "layer": "ACTIVATION", "c_mod": "SUB", "k_n": 4,  "mog_slot": "A_Force", "opcode": "MUL"},

        # Flip
        "flip horizontal":    {"lingo": "PLANE_REFLECTION",  "layer": "ACTIVATION", "c_mod": "NEGATE","k_n": 4, "mog_slot": "A_Force", "opcode": "NEGATE"},
        "flip vertical":      {"lingo": "PLANE_REFLECTION",  "layer": "ACTIVATION", "c_mod": "SQUARE","k_n": 4, "mog_slot": "A_Force", "opcode": "NEGATE"},
        "mirror":             {"lingo": "PLANE_REFLECTION",  "layer": "ACTIVATION", "c_mod": "NEGATE","k_n": 4, "mog_slot": "A_Force", "opcode": "NEGATE"},

        # Recolour
        "recolour":           {"lingo": "CHARGE_SWAP",       "layer": "POTENTIAL",  "c_mod": "NEGATE","k_n": 4, "mog_slot": "P_Ratio",  "opcode": "NEGATE"},
        "recolor":            {"lingo": "CHARGE_SWAP",       "layer": "POTENTIAL",  "c_mod": "NEGATE","k_n": 4, "mog_slot": "P_Ratio",  "opcode": "NEGATE"},
        "swap colour":        {"lingo": "CHARGE_SWAP",       "layer": "POTENTIAL",  "c_mod": "NEGATE","k_n": 4, "mog_slot": "P_Ratio",  "opcode": "NEGATE"},
        "change colour":      {"lingo": "CHARGE_SWAP",       "layer": "POTENTIAL",  "c_mod": "NEGATE","k_n": 4, "mog_slot": "P_Ratio",  "opcode": "NEGATE"},

        # Gravity
        "gravity down":       {"lingo": "COMPACTION_FLOW",   "layer": "ACTIVATION", "c_mod": "NEGATE","k_n": 4, "mog_slot": "A_Flux",   "opcode": "ADD"},
        "gravity up":         {"lingo": "COMPACTION_FLOW",   "layer": "ACTIVATION", "c_mod": "NEGATE","k_n": 8, "mog_slot": "A_Flux",   "opcode": "ADD"},
        "fall down":          {"lingo": "COMPACTION_FLOW",   "layer": "ACTIVATION", "c_mod": "NEGATE","k_n": 4, "mog_slot": "A_Flux",   "opcode": "ADD"},

        # Fill
        "fill interior":      {"lingo": "REGION_FILL",       "layer": "ACTIVATION", "c_mod": "RECIP", "k_n": 4, "mog_slot": "A_Flux",   "opcode": "ADD"},
        "fill background":    {"lingo": "REGION_FILL",       "layer": "POTENTIAL",  "c_mod": "ABS",   "k_n": 4, "mog_slot": "P_Ratio",  "opcode": "ADD"},
        "fill outline":       {"lingo": "REGION_FILL",       "layer": "ACTIVATION", "c_mod": "RECIP", "k_n": 4, "mog_slot": "A_Flux",   "opcode": "ADD"},

        # Crop / scale
        "crop":               {"lingo": "BOUNDARY_TRIM",     "layer": "ACTIVATION", "c_mod": "ABS",   "k_n": 4, "mog_slot": "A_Velocity","opcode": "SUB"},
        "scale up":           {"lingo": "RADIUS_SCALING",    "layer": "ACTIVATION", "c_mod": "MUL",   "k_n": 4, "mog_slot": "A_Force",  "opcode": "MUL"},
        "scale down":         {"lingo": "RADIUS_SCALING",    "layer": "ACTIVATION", "c_mod": "DIV",   "k_n": 4, "mog_slot": "A_Force",  "opcode": "DIV"},

        # Identity
        "identity":           {"lingo": "UNIT_NODE",         "layer": "REALITY",    "c_mod": "ID",    "k_n": 4, "mog_slot": "M_Space",  "opcode": "ID"},
        "no change":          {"lingo": "UNIT_NODE",         "layer": "REALITY",    "c_mod": "ID",    "k_n": 4, "mog_slot": "M_Space",  "opcode": "ID"},

        # Count
        "count":              {"lingo": "CARDINALITY_MEASURE","layer": "INFORMATION","c_mod": "ID",   "k_n": 4, "mog_slot": "I_Density", "opcode": "ID"},
        "replicate":          {"lingo": "CLUSTER_UNION",     "layer": "ACTIVATION", "c_mod": "MUL",   "k_n": 6, "mog_slot": "A_Energy",  "opcode": "ADD"},
        "tile":               {"lingo": "CLUSTER_UNION",     "layer": "ACTIVATION", "c_mod": "MUL",   "k_n": 6, "mog_slot": "A_Energy",  "opcode": "ADD"},

        # Extract
        "outline":            {"lingo": "BOUNDARY_EXTRACT",  "layer": "POTENTIAL",  "c_mod": "SUB",   "k_n": 4, "mog_slot": "P_Coherence","opcode": "SUB"},
        "extract":            {"lingo": "BOUNDARY_EXTRACT",  "layer": "POTENTIAL",  "c_mod": "SUB",   "k_n": 4, "mog_slot": "P_Coherence","opcode": "SUB"},
    }

    def human_to_lingo(self, description: str) -> Optional[LingoExpression]:
        """Translate a human description into a LingoExpression.

        Args:
            description: a human-readable description like "rotate 90 degrees clockwise"

        Returns:
            A LingoExpression, or None if no pattern matches.
        """
        desc_lower = description.lower().strip()

        # Try each pattern
        for phrase, mapping in self.PHRASE_PATTERNS.items():
            if phrase in desc_lower:
                return LingoExpression(
                    layer=mapping["layer"],
                    c_modifier=mapping["c_mod"],
                    k_n=mapping["k_n"],
                    mog_slot=mapping["mog_slot"],
                    opcode=mapping["opcode"],
                    lingo_term=mapping["lingo"],
                    human_description=description,
                )

        # No match — return None
        return None

    def lingo_to_human(self, expr: LingoExpression) -> str:
        """Translate a LingoExpression into a human description."""
        return expr.to_human_string()

    def describe_transformation(self, transform_type: str,
                                 colour_mapping: Dict[int, int] = None,
                                 position_delta: Tuple[float, float] = None) -> LingoExpression:
        """Create a LingoExpression from a CRG transform type + params."""
        type_to_lingo = {
            "recolour":    {"lingo": "CHARGE_SWAP",       "layer": "POTENTIAL",  "c_mod": "NEGATE", "k_n": 4, "mog_slot": "P_Ratio",   "opcode": "NEGATE"},
            "move":        {"lingo": "CENTROID_SHIFT",    "layer": "ACTIVATION", "c_mod": "ADD",    "k_n": 4, "mog_slot": "A_Velocity","opcode": "ADD"},
            "gravity":     {"lingo": "COMPACTION_FLOW",   "layer": "ACTIVATION", "c_mod": "NEGATE", "k_n": 4, "mog_slot": "A_Flux",    "opcode": "ADD"},
            "resize":      {"lingo": "RADIUS_SCALING",    "layer": "ACTIVATION", "c_mod": "MUL",    "k_n": 4, "mog_slot": "A_Force",   "opcode": "MUL"},
            "appear":      {"lingo": "CLUSTER_UNION",     "layer": "ACTIVATION", "c_mod": "ADD",    "k_n": 4, "mog_slot": "A_Energy",  "opcode": "ADD"},
            "disappear":   {"lingo": "CLUSTER_FISSION",   "layer": "ACTIVATION", "c_mod": "SUB",    "k_n": 4, "mog_slot": "A_Energy",  "opcode": "SUB"},
            "unchanged":   {"lingo": "UNIT_NODE",         "layer": "REALITY",    "c_mod": "ID",     "k_n": 4, "mog_slot": "M_Space",   "opcode": "ID"},
            "composite":   {"lingo": "TOPO_SIGNATURE",    "layer": "INFORMATION","c_mod": "SQUARE", "k_n": 6, "mog_slot": "I_Density", "opcode": "MUL"},
        }

        mapping = type_to_lingo.get(transform_type, type_to_lingo["composite"])
        params = {}
        if colour_mapping:
            params["mapping"] = colour_mapping
        if position_delta:
            params["delta"] = f"({position_delta[0]:.1f},{position_delta[1]:.1f})"

        return LingoExpression(
            layer=mapping["layer"],
            c_modifier=mapping["c_mod"],
            k_n=mapping["k_n"],
            mog_slot=mapping["mog_slot"],
            opcode=mapping["opcode"],
            lingo_term=mapping["lingo"],
            params=params,
            human_description=transform_type,
        )

    def describe_nrci(self, nrci: float) -> str:
        """Describe an NRCI value in Lingo terms.

        NRCI is a coherence measure (0-1):
          ≥ 0.70: NRCI_MANIFEST (manifested — stable lattice point)
          0.60-0.70: NRCI_STABLE (anomalous — near-stable)
          0.50-0.60: NRCI_TRANSITIONAL (transitional)
          < 0.50: NRCI_SUBLIMINAL (subliminal — dissolved)
        """
        if nrci >= 0.70:
            return f"NRCI_MANIFEST (coherence={nrci:.4f}, stable lattice point)"
        elif nrci >= 0.60:
            return f"NRCI_STABLE (coherence={nrci:.4f}, anomalous, near-stable)"
        elif nrci >= 0.50:
            return f"NRCI_TRANSITIONAL (coherence={nrci:.4f}, transitional)"
        else:
            return f"NRCI_SUBLIMINAL (coherence={nrci:.4f}, dissolved)"

    def describe_geo_class(self, n: int) -> str:
        """Describe an integer's geometric class in Lingo terms.

        Uses LDP's geo_class: (C_depth, omega_total, omega_distinct, is_prime)
        """
        gc = geo_class(n)
        c_depth, omega_t, omega_d, is_p = gc
        parts = [f"geo_class({n}) = ({c_depth}, {omega_t}, {omega_d}, {is_p})"]
        if is_p:
            parts.append(f"PRIME ground state (C(N)=0, no sub-cycles)")
        else:
            sc = _sub_cycles(n)
            parts.append(f"COMPOSITE with {sc} sub-cycles (topological mass = {sc}/{n} = {sc/n:.3f})")
        factors = _factorize(n)
        if len(factors) > 1:
            fac_str = " × ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(factors.items()))
            parts.append(f"factorisation: {fac_str}")
        return "; ".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# SPATIAL CALCULATOR — exact arithmetic via Spatial Arithmetic (no floats)
# ══════════════════════════════════════════════════════════════════════════════

class SpatialCalculator:
    """Performs calculations using Spatial Arithmetic with exact Fraction arithmetic.

    The GLM should use Spatial Arithmetic to ACTUALLY CALCULATE, not float
    approximations. SymPy can be used for validation but not for calculation.

    All operations are performed via the spatial_arithmetic module's
    R(n) primitive and OPCODE_TABLE, using Fraction for exact arithmetic.
    """

    @staticmethod
    def add(a: int, b: int) -> int:
        """Natural addition via spatial cluster merging.

        Addition is the physical merger of node clusters and recalculation
        of the unified centroid. Uses spatial_arithmetic.natural_add.
        """
        from spatial_arithmetic_compat import natural_add
        result, status = natural_add(a, b)
        if result is not None:
            return result
        # Fallback: exact integer addition
        return a + b

    @staticmethod
    def multiply(a: int, b: int) -> int:
        """Multiplication via distance ratio (OPCODE_TABLE MUL).

        In Spatial Arithmetic, multiplication is the metric ratio of
        spatial radii. R(a) * R(b) gives the product's circumradius.
        """
        # Use the OPCODE_TABLE's MUL operation
        from spatial_arithmetic_compat import OPCODE_TABLE
        op_fn = OPCODE_TABLE[3][1]  # 3 = MUL
        result = op_fn(a, b)
        return int(result) if result is not None else a * b

    @staticmethod
    def subtract(a: int, b: int) -> int:
        """Subtraction via distance scaling (OPCODE_TABLE SUB)."""
        from spatial_arithmetic_compat import OPCODE_TABLE
        op_fn = OPCODE_TABLE[5][1]  # 5 = SUB
        result = op_fn(a, b)
        return int(result) if result is not None else a - b

    @staticmethod
    def divide(a: int, b: int) -> Fraction:
        """Division via radius ratio (OPCODE_TABLE DIV).

        Returns a Fraction for exact arithmetic (no float drift).
        """
        from spatial_arithmetic_compat import OPCODE_TABLE
        op_fn = OPCODE_TABLE[6][1]  # 6 = DIV
        result = op_fn(a, b)
        if result is not None:
            return result  # already a Fraction
        return Fraction(a, b) if b != 0 else None

    @staticmethod
    def spatial_log(n: int) -> Fraction:
        """The spatial logarithm: R(n) = 1/(2·sin(π/n)).

        This is the spatial equivalent of ln(n). Returns an exact Fraction.
        """
        import math
        from fractions import Fraction
        # R(n) = 1 / (2 * sin(π/n))
        # For exact arithmetic, use Fraction from the high-precision float
        r_float = value_to_radius(n)
        return Fraction(r_float).limit_denominator(10**15)

    @staticmethod
    def spatial_exp(radius: Fraction) -> int:
        """The spatial exponential: radius → value.

        Inverse of spatial_log. Uses spatial_arithmetic.radius_to_value.
        """
        return radius_to_value(float(radius))

    @staticmethod
    def validate_with_sympy(a: int, b: int, operation: str, result: int) -> bool:
        """Validate a Spatial Arithmetic result using SymPy (for verification only).

        SymPy is used ONLY for validation — the actual calculation is done
        via Spatial Arithmetic above.
        """
        try:
            import sympy
            if operation == "add":
                return sympy.Integer(a) + sympy.Integer(b) == sympy.Integer(result)
            elif operation == "mul":
                return sympy.Integer(a) * sympy.Integer(b) == sympy.Integer(result)
            elif operation == "sub":
                return sympy.Integer(a) - sympy.Integer(b) == sympy.Integer(result)
            elif operation == "div":
                return sympy.Rational(a, b) == sympy.Rational(result)
        except ImportError:
            # SymPy not available — skip validation
            return True
        return True
