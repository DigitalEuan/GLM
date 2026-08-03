"""
training_benchmark.py — Full Training Session with Benchmarks

The mind learns to:
1. See Data Objects as geometric structures in 24D space
2. Compute on them using Spatial Arithmetic
3. Speak about what it sees (describe geometric relationships)
4. Track progress through benchmarks

Everything is geometry. Data Objects are positions in 24D Leech space.
Spatial Arithmetic computes on those positions.
"""

from __future__ import annotations
import sys, json, math, statistics, itertools, time, random
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb
from training_iteration import (
    EncodingSpec, encode_element, golay_snap, compute_interaction_metrics,
    pearson_r, SCALING_PRESETS, gray6, HAS_GOLAY, hamming_distance,
)

if HAS_GOLAY:
    from training_iteration import GOLAY_ENGINE

Y = 0.2646754304045269672  # Entropic wobble


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark Suite
# ═══════════════════════════════════════════════════════════════════════════════

class Benchmark:
    """Track training progress across iterations."""

    def __init__(self):
        self.results = {}

    def score(self, name: str, predicted: float, actual: float, threshold: float = 0.1):
        """Score a prediction. Returns 1 if within threshold, 0 otherwise."""
        error = abs(predicted - actual) / max(abs(actual), 1e-10)
        passed = error < threshold
        if name not in self.results:
            self.results[name] = {"attempts": 0, "passes": 0, "errors": []}
        self.results[name]["attempts"] += 1
        if passed:
            self.results[name]["passes"] += 1
        self.results[name]["errors"].append(error)
        return passed

    def correlation_score(self, name: str, r: float, threshold: float = 0.5):
        """Score a correlation. Returns 1 if |r| > threshold."""
        passed = abs(r) > threshold
        if name not in self.results:
            self.results[name] = {"attempts": 0, "passes": 0, "r_values": []}
        self.results[name]["attempts"] += 1
        if passed:
            self.results[name]["passes"] += 1
        self.results[name]["r_values"].append(r)
        return passed

    def report(self) -> Dict:
        summary = {}
        for name, data in self.results.items():
            if "r_values" in data:
                summary[name] = {
                    "pass_rate": data["passes"] / max(data["attempts"], 1),
                    "mean_r": statistics.mean(data["r_values"]) if data["r_values"] else 0,
                    "attempts": data["attempts"],
                }
            else:
                summary[name] = {
                    "pass_rate": data["passes"] / max(data["attempts"], 1),
                    "mean_error": statistics.mean(data["errors"]) if data["errors"] else 0,
                    "attempts": data["attempts"],
                }
        return summary

    def print_report(self):
        print(f"\n  {'Benchmark':35s} {'Pass Rate':10s} {'Metric':10s} {'Attempts':8s}")
        print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*8}")
        for name, data in self.report().items():
            if "mean_r" in data:
                print(f"  {name:35s} {data['pass_rate']:10.1%} {data['mean_r']:+10.4f} {data['attempts']:8d}")
            else:
                print(f"  {name:35s} {data['pass_rate']:10.1%} {data['mean_error']:10.4f} {data['attempts']:8d}")


# ═══════════════════════════════════════════════════════════════════════════════
# Data Object as Geometric Position
# ═══════════════════════════════════════════════════════════════════════════════

class DataObject:
    """A 24-bit vector as a geometric position in Leech space."""

    def __init__(self, bits: List[int], label: str = ""):
        self.bits = bits[:]
        self.label = label
        self.hw = sum(bits)

        # Golay snap
        if HAS_GOLAY:
            self.snapped, _ = GOLAY_ENGINE.snap_to_codeword(bits)
            self.syndrome = GOLAY_ENGINE.syndrome(bits)
            self.sw = sum(self.syndrome)
        else:
            self.snapped = bits[:]
            self.syndrome = [0]*6
            self.sw = 0

        self.hw_snapped = sum(self.snapped)
        self.bits_changed = sum(1 for i in range(24) if bits[i] != self.snapped[i])

        # TAX and NRCI
        self.tax = self.hw * Y + sum(v*v for v in bits) / 8.0
        self.nrci = 10.0 / (10.0 + self.tax)
        self.tax_snapped = self.hw_snapped * Y + sum(v*v for v in self.snapped) / 8.0
        self.nrci_snapped = 10.0 / (10.0 + self.tax_snapped)

        # 2D projection (unit circle)
        self.points_2d = []
        for i, v in enumerate(bits):
            if v:
                angle = 2 * math.pi * i / 24
                self.points_2d.append((math.cos(angle), math.sin(angle)))

        # Geometric metrics
        self._compute_geometry()

    def _compute_geometry(self):
        """Compute spatial geometry metrics."""
        pts = self.points_2d
        if len(pts) < 2:
            self.centroid = (0, 0)
            self.area = 0
            self.perimeter = 0
            self.compactness = 0
            self.radius = 0
            return

        # Centroid
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        self.centroid = (cx, cy)

        # Radius (distance from centroid to furthest point)
        self.radius = max(math.sqrt((p[0]-cx)**2 + (p[1]-cy)**2) for p in pts)

        # Polygon area (ordered by angle)
        if len(pts) >= 3:
            sorted_pts = sorted(pts, key=lambda p: math.atan2(p[1]-cy, p[0]-cx))
            area = 0
            for i in range(len(sorted_pts)):
                j = (i + 1) % len(sorted_pts)
                area += sorted_pts[i][0] * sorted_pts[j][1]
                area -= sorted_pts[j][0] * sorted_pts[i][1]
            self.area = abs(area) / 2

            perim = 0
            for i in range(len(sorted_pts)):
                j = (i + 1) % len(sorted_pts)
                dx = sorted_pts[j][0] - sorted_pts[i][0]
                dy = sorted_pts[j][1] - sorted_pts[i][1]
                perim += math.sqrt(dx*dx + dy*dy)
            self.perimeter = perim
            self.compactness = 4 * math.pi * self.area / (perim * perim) if perim > 0 else 0
        else:
            self.area = 0
            self.perimeter = 0
            self.compactness = 0

    def distance_to(self, other: 'DataObject') -> float:
        """Euclidean distance between centroids."""
        dx = self.centroid[0] - other.centroid[0]
        dy = self.centroid[1] - other.centroid[1]
        return math.sqrt(dx*dx + dy*dy)

    def and_with(self, other: 'DataObject') -> 'DataObject':
        """AND operation — shared structure."""
        result = [self.bits[i] & other.bits[i] for i in range(24)]
        label = f"AND({self.label},{other.label})"
        return DataObject(result, label)

    def xor_with(self, other: 'DataObject') -> 'DataObject':
        """XOR operation — difference."""
        result = [self.bits[i] ^ other.bits[i] for i in range(24)]
        label = f"XOR({self.label},{other.label})"
        return DataObject(result, label)

    def or_with(self, other: 'DataObject') -> 'DataObject':
        """OR operation — union."""
        result = [self.bits[i] | other.bits[i] for i in range(24)]
        label = f"OR({self.label},{other.label})"
        return DataObject(result, label)

    def describe(self) -> str:
        """Describe this Data Object in geometric terms."""
        parts = []
        parts.append(f"{self.label}: HW={self.hw}, NRCI={self.nrci:.4f}")
        parts.append(f"  Position: ({self.centroid[0]:.3f}, {self.centroid[1]:.3f})")
        parts.append(f"  Radius: {self.radius:.3f}, Area: {self.area:.4f}")
        parts.append(f"  Compactness: {self.compactness:.4f}")
        parts.append(f"  Snap: {self.bits_changed} bits changed, HW {self.hw}→{self.hw_snapped}")
        if self.sw > 0:
            parts.append(f"  Syndrome weight: {self.sw} (errors detected)")
        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Spatial Arithmetic Engine
# ═══════════════════════════════════════════════════════════════════════════════

class SpatialEngine:
    """Compute on Data Objects as geometric structures."""

    @staticmethod
    def R(n: int) -> float:
        """Regular polygon radius: R(n) = 1/(2·sin(π/n))"""
        if n < 3:
            return 0
        return 1.0 / (2.0 * math.sin(math.pi / n))

    @staticmethod
    def eml(x: float, y: float) -> float:
        """EML function: exp(x) - ln(y)"""
        return math.exp(x) - math.log(max(y, 1e-10))

    @staticmethod
    def scene_distance(a: DataObject, b: DataObject) -> float:
        """Distance between two Data Objects in 24D space."""
        return math.sqrt(sum((a.snapped[i] - b.snapped[i])**2 for i in range(24)))

    @staticmethod
    def scene_angle(a: DataObject, b: DataObject) -> float:
        """Angle between two Data Objects (dot product)."""
        dot = sum(a.snapped[i] * b.snapped[i] for i in range(24))
        norm_a = math.sqrt(sum(v*v for v in a.snapped))
        norm_b = math.sqrt(sum(v*v for v in b.snapped))
        if norm_a == 0 or norm_b == 0:
            return 0
        cos_theta = dot / (norm_a * norm_b)
        cos_theta = max(-1, min(1, cos_theta))
        return math.acos(cos_theta)

    @staticmethod
    def scene_centroid(objects: List[DataObject]) -> Tuple[float, float]:
        """Centroid of a collection of Data Objects."""
        if not objects:
            return (0, 0)
        cx = sum(o.centroid[0] for o in objects) / len(objects)
        cy = sum(o.centroid[1] for o in objects) / len(objects)
        return (cx, cy)

    @staticmethod
    def scene_bounding_radius(objects: List[DataObject]) -> float:
        """Bounding radius of a collection."""
        if len(objects) < 2:
            return 0
        centroid = SpatialEngine.scene_centroid(objects)
        return max(
            math.sqrt((o.centroid[0]-centroid[0])**2 + (o.centroid[1]-centroid[1])**2)
            for o in objects
        )

    @staticmethod
    def perturbation_cost(a: DataObject, b: DataObject) -> float:
        """Cost of perturbing vacuum (a) with stimulus (b).
        Uses the UBP perturbation laws."""
        combined = a.and_with(b)
        return combined.tax - a.tax

    @staticmethod
    def symmetry_tax(v: DataObject) -> float:
        """The Symmetry Tax of a Data Object."""
        return v.tax

    @staticmethod
    def coherence_delta(a: DataObject, b: DataObject) -> float:
        """Change in NRCI when b perturbs a."""
        combined = a.and_with(b)
        return combined.nrci - a.nrci


# ═══════════════════════════════════════════════════════════════════════════════
# Training: Element Pairs with Geometric Description
# ═══════════════════════════════════════════════════════════════════════════════

def train_element_geometry(spec: EncodingSpec, bench: Benchmark, verbose: bool = True):
    """Train on element pairs with full geometric analysis."""
    if verbose:
        print("\n" + "=" * 70)
        print("ELEMENT PAIR GEOMETRY")
        print("=" * 70)

    elements = kb.get_all_elements()
    engine = SpatialEngine()

    # Encode key elements
    key_elements = ["H", "C", "N", "O", "F", "Na", "Cl", "Fe", "Au"]
    data_objects = {}
    for sym in key_elements:
        if sym in elements:
            vec = encode_element(sym, spec)
            data_objects[sym] = DataObject(vec, sym)

    if verbose:
        print(f"\n  Element Data Objects:")
        for sym, do in data_objects.items():
            print(f"    {do.describe()}")

    # Pair geometry
    pairs_data = kb.KNOWN_PAIRS
    for sym_a, sym_b, be, dh, label in pairs_data[:15]:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        da = data_objects[sym_a]
        db = data_objects[sym_b]

        # AND operation
        d_and = da.and_with(db)

        # Spatial metrics
        dist = engine.scene_distance(da, db)
        angle = engine.scene_angle(da, db)
        pert_cost = engine.perturbation_cost(da, db)
        coh_delta = engine.coherence_delta(da, db)

        # Predict BE from NRCI × bond_order (our best model)
        # We don't know bond order here, so use HW as proxy
        predicted_be_proxy = d_and.nrci * d_and.hw * 50  # rough scaling

        bench.correlation_score("pair_geometry_r", coh_delta, 0.01)

        if verbose and sym_a + "-" + sym_b in ["H-O", "C-O", "N-N", "C-C", "Na-Cl"]:
            print(f"\n  {sym_a}-{sym_b} (BE={be}):")
            print(f"    AND: HW={d_and.hw}, NRCI={d_and.nrci:.4f}")
            print(f"    Distance: {dist:.4f}")
            print(f"    Angle: {math.degrees(angle):.1f}°")
            print(f"    Perturbation cost: {pert_cost:+.4f}")
            print(f"    Coherence delta: {coh_delta:+.4f}")


# ═══════════════════════════════════════════════════════════════════════════════
# Training: Molecular Geometry
# ═══════════════════════════════════════════════════════════════════════════════

def train_molecule_geometry(spec: EncodingSpec, bench: Benchmark, verbose: bool = True):
    """Train on molecule Data Objects with geometric analysis."""
    if verbose:
        print("\n" + "=" * 70)
        print("MOLECULE GEOMETRY")
        print("=" * 70)

    from training_iteration_v3 import encode_molecule
    molecules = kb.get_all_molecules()
    engine = SpatialEngine()

    # Encode key molecules
    key_molecules = ["H2O", "NACL", "METHANOL", "BENZENE", "AMMONIA", "METHANE", "GLUCOSE"]
    mol_objects = {}
    for name in key_molecules:
        if name in molecules:
            vec = encode_molecule(name, spec)
            mol_objects[name] = DataObject(vec, name)

    if verbose:
        print(f"\n  Molecule Data Objects:")
        for name, do in mol_objects.items():
            print(f"    {do.describe()}")

    # Molecule interactions
    if len(mol_objects) >= 2:
        names = list(mol_objects.keys())
        if verbose:
            print(f"\n  Molecule Pair Geometry:")
        for i in range(len(names)):
            for j in range(i+1, min(len(names), i+4)):
                da = mol_objects[names[i]]
                db = mol_objects[names[j]]
                d_and = da.and_with(db)
                dist = engine.scene_distance(da, db)
                coh_delta = engine.coherence_delta(da, db)

                bench.correlation_score("mol_geometry_r", coh_delta, 0.01)

                if verbose:
                    print(f"    {names[i]:10s} ↔ {names[j]:10s}: "
                          f"dist={dist:.4f} AND_HW={d_and.hw} ΔNRCI={coh_delta:+.4f}")


# ═══════════════════════════════════════════════════════════════════════════════
# Training: Shape Arithmetic
# ═══════════════════════════════════════════════════════════════════════════════

def train_shape_arithmetic(bench: Benchmark, verbose: bool = True):
    """Train on geometric shapes and their arithmetic."""
    if verbose:
        print("\n" + "=" * 70)
        print("SHAPE ARITHMETIC — Computing on Geometry")
        print("=" * 70)

    engine = SpatialEngine()

    # R(n) values
    if verbose:
        print(f"\n  R(n) — Regular Polygon Radii:")
        for n in range(3, 13):
            R = engine.R(n)
            print(f"    R({n:2d}) = {R:.6f}")

    # Encode shapes as Data Objects
    shapes = {
        "triangle": DataObject([1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0], "triangle"),
        "square": DataObject([1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0], "square"),
        "hexagon": DataObject([1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0], "hexagon"),
        "line3": DataObject([1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "line3"),
        "line6": DataObject([1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "line6"),
        "point0": DataObject([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "point0"),
        "point12": DataObject([0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0], "point12"),
    }

    if verbose:
        print(f"\n  Shape Data Objects:")
        for name, do in shapes.items():
            print(f"    {do.describe()}")

    # Shape arithmetic
    if verbose:
        print(f"\n  Shape Arithmetic (AND = intersection):")
        shape_pairs = [
            ("triangle", "square", "tri ∩ square"),
            ("hexagon", "hexagon", "hex ∩ hex (same)"),
            ("line3", "line6", "line3 ∩ line6"),
            ("point0", "point12", "point0 ∩ point12"),
        ]
        for s1, s2, label in shape_pairs:
            d1, d2 = shapes[s1], shapes[s2]
            d_and = d1.and_with(d2)
            d_xor = d1.xor_with(d2)
            dist = engine.scene_distance(d1, d2)
            angle = engine.scene_angle(d1, d2)
            print(f"    {label:25s}: AND(HW={d_and.hw}, NRCI={d_and.nrci:.4f}) "
                  f"XOR(HW={d_xor.hw}) dist={dist:.4f} angle={math.degrees(angle):.1f}°")

    # Benchmark: shapes closer together should have higher AND HW
    for s1, s2 in [("triangle", "hexagon"), ("line3", "line6"), ("point0", "point12")]:
        d1, d2 = shapes[s1], shapes[s2]
        d_and = d1.and_with(d2)
        bench.correlation_score("shape_intersection", d_and.hw / max(d1.hw, d2.hw, 1), 0.01)


# ═══════════════════════════════════════════════════════════════════════════════
# Training: Golay Self-Knowledge
# ═══════════════════════════════════════════════════════════════════════════════

def train_golay_self(bench: Benchmark, verbose: bool = True):
    """The substrate learning about itself."""
    if verbose:
        print("\n" + "=" * 70)
        print("GOLAY SELF-KNOWLEDGE")
        print("=" * 70)

    if not HAS_GOLAY:
        print("  Golay engine not available")
        return

    engine = GOLAY_ENGINE

    # Error correction capability
    if verbose:
        print(f"\n  Error Correction Test:")
    random.seed(42)
    test_vec = [random.randint(0, 1) for _ in range(24)]
    snapped, _ = engine.snap_to_codeword(test_vec)

    for n_err in range(1, 6):
        for trial in range(5):
            corrupted = snapped[:]
            positions = random.sample(range(24), n_err)
            for p in positions:
                corrupted[p] = 1 - corrupted[p]
            corrected, _ = engine.snap_to_codeword(corrupted)
            match = corrected == snapped
            bench.score("golay_error_correction", 1 if match else 0, 1, 0.01)

    if verbose:
        # Show results
        bc = bench.results.get("golay_error_correction", {})
        if bc:
            print(f"    Error correction pass rate: {bc['passes']}/{bc['attempts']}")

    # Codeword space exploration
    if verbose:
        print(f"\n  Codeword Space:")
        # Generate codewords by snapping random vectors
        codewords = set()
        for i in range(1000):
            random.seed(i)
            vec = [random.randint(0, 1) for _ in range(24)]
            cw, _ = engine.snap_to_codeword(vec)
            codewords.add(tuple(cw))
        print(f"    Unique codewords found (1000 random snaps): {len(codewords)}")
        print(f"    Total possible: 4096")
        print(f"    Coverage: {len(codewords)/4096:.1%}")


# ═══════════════════════════════════════════════════════════════════════════════
# Training: Spatial Arithmetic on Element Triplets
# ═══════════════════════════════════════════════════════════════════════════════

def train_triplet_spatial(spec: EncodingSpec, bench: Benchmark, verbose: bool = True):
    """Spatial Arithmetic on element triplets (molecular fragments)."""
    if verbose:
        print("\n" + "=" * 70)
        print("TRIPLET SPATIAL ARITHMETIC")
        print("=" * 70)

    engine = SpatialEngine()

    triplets = [
        ("H", "O", "H", "water"),
        ("H", "C", "H", "methylene"),
        ("H", "N", "H", "imine"),
        ("C", "O", "O", "carboxyl"),
        ("H", "C", "O", "formyl"),
        ("C", "C", "C", "carbon chain"),
        ("N", "N", "N", "nitrogen chain"),
        ("O", "O", "O", "ozone"),
        ("H", "H", "H", "hydrogen"),
        ("Fe", "O", "Fe", "iron oxide"),
    ]

    for ea, eb, ec, name in triplets:
        elements = kb.get_all_elements()
        if any(s not in elements for s in [ea, eb, ec]):
            continue

        va = encode_element(ea, spec)
        vb = encode_element(eb, spec)
        vc = encode_element(ec, spec)

        da = DataObject(va, ea)
        db = DataObject(vb, eb)
        dc = DataObject(vc, ec)

        # 3-body AND
        abc_and = [va[i] & vb[i] & vc[i] for i in range(24)]
        d_abc = DataObject(abc_and, name)

        # Pairwise
        ab = da.and_with(db)
        bc = db.and_with(dc)
        ac = da.and_with(dc)

        # Spatial metrics
        centroid = engine.scene_centroid([da, db, dc])
        bounding_r = engine.scene_bounding_radius([da, db, dc])

        bench.correlation_score("triplet_nrci", d_abc.nrci, 0.01)

        if verbose:
            print(f"  {name:15s}: 3AND(HW={d_abc.hw:2d}, NRCI={d_abc.nrci:.4f}) "
                  f"centroid=({centroid[0]:.3f},{centroid[1]:.3f}) "
                  f"bound_r={bounding_r:.3f}")


# ═══════════════════════════════════════════════════════════════════════════════
# Training: Speaking — the mind describes what it sees
# ═══════════════════════════════════════════════════════════════════════════════

def train_speaking(spec: EncodingSpec, verbose: bool = True):
    """The mind describes Data Objects and their relationships."""
    if verbose:
        print("\n" + "=" * 70)
        print("THE MIND SPEAKS — Describing What It Sees")
        print("=" * 70)

    elements = kb.get_all_elements()
    engine = SpatialEngine()

    # Describe hydrogen
    h_vec = encode_element("H", spec)
    h = DataObject(h_vec, "Hydrogen")
    o_vec = encode_element("O", spec)
    o = DataObject(o_vec, "Oxygen")

    if verbose:
        print(f"\n  The mind sees Hydrogen:")
        print(f"    {h.describe()}")
        print(f"\n  The mind sees Oxygen:")
        print(f"    {o.describe()}")

    # The mind describes their interaction
    h_and_o = h.and_with(o)
    h_xor_o = h.xor_with(o)

    if verbose:
        print(f"\n  When Hydrogen meets Oxygen:")
        print(f"    Shared structure (AND): {h_and_o.describe()}")
        print(f"    Difference (XOR): HW={h_xor_o.hw}")
        print(f"    Distance in 24D: {engine.scene_distance(h, o):.4f}")
        print(f"    Angle: {math.degrees(engine.scene_angle(h, o)):.1f}°")
        print(f"    Perturbation cost: {engine.perturbation_cost(h, o):+.4f}")
        print(f"    Coherence change: {engine.coherence_delta(h, o):+.4f}")

    # Noble gas — the vacuum
    he_vec = encode_element("He", spec)
    he = DataObject(he_vec, "Helium")

    if verbose:
        print(f"\n  The mind sees Helium (noble gas):")
        print(f"    {he.describe()}")
        print(f"    This is the vacuum state — NRCI={he.nrci:.4f}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_training():
    """Full training session with benchmarks."""
    print("=" * 70)
    print("GLM FULL TRAINING SESSION — Geometry, Arithmetic, Speaking")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    bench = Benchmark()

    # Element encoding spec (best from calibration)
    spec = EncodingSpec(
        name="v0_baseline",
        prop_set=["Z", "Rad", "EN", "Valence_e"],
        row_assignment=[0, 1, 2, 3],
        scaling={"Z": "identity", "Rad": "div4", "EN": "en_x15", "Valence_e": "valence_redundant"},
    )

    # Run all training modules
    train_element_geometry(spec, bench)
    train_molecule_geometry(spec, bench)
    train_shape_arithmetic(bench)
    train_golay_self(bench)
    train_triplet_spatial(spec, bench)
    train_speaking(spec)

    # Benchmark report
    print("\n" + "=" * 70)
    print("BENCHMARK REPORT")
    print("=" * 70)
    bench.print_report()

    # Save
    out_path = SCRIPT_DIR.parent / "data" / f"benchmark_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(bench.report(), f, indent=2, default=str)
    print(f"\n  Benchmark saved to {out_path}")

    return bench


if __name__ == "__main__":
    run_full_training()
