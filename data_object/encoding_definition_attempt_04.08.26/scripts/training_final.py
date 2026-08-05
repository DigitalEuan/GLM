"""
training_final.py — Final Training Round Using Long-Term Memory

Reads from long_term_memory/, applies learned knowledge, refines benchmarks.
This is the mind using what it knows to learn more.
"""

from __future__ import annotations
import sys, json, math, statistics, time, random
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb
from training_iteration import (
    EncodingSpec, encode_element, golay_snap, pearson_r, HAS_GOLAY,
)
from training_bond_geometry import snap_with_cost, encode_bond_and, BOND_DATA
from training_benchmark import Benchmark, DataObject, SpatialEngine

if HAS_GOLAY:
    from training_iteration import GOLAY_ENGINE

Y = 0.2646754304045269672


# ═══════════════════════════════════════════════════════════════════════════════
# Read long-term memory
# ═══════════════════════════════════════════════════════════════════════════════

def read_long_term_memory():
    """Read what the mind already knows."""
    ltm_path = SCRIPT_DIR.parent.parent / "long_term_memory"
    knowledge = {}
    for f in ltm_path.glob("*.md"):
        with open(f) as fh:
            knowledge[f.stem] = fh.read()
    return knowledge


# ═══════════════════════════════════════════════════════════════════════════════
# Refined training: use what we know
# ═══════════════════════════════════════════════════════════════════════════════

def train_refined_bonds(spec: EncodingSpec, bench: Benchmark, verbose: bool = True):
    """Refined bond training using AND encoding (our best method)."""
    if verbose:
        print("\n" + "=" * 70)
        print("REFINED BOND TRAINING — Using AND Encoding")
        print("=" * 70)

    engine = SpatialEngine()
    records = []

    for ea, eb, bo, be, label in BOND_DATA:
        if kb.get_element(ea) is None or kb.get_element(eb) is None:
            continue

        # AND encoding (our best)
        raw = encode_bond_and(ea, eb, spec)
        snap = snap_with_cost(raw)

        # Spatial metrics
        do_raw = DataObject(raw, f"{ea}-{eb}")

        # Element Data Objects
        va = encode_element(ea, spec)
        vb = encode_element(eb, spec)
        da = DataObject(va, ea)
        db = DataObject(vb, eb)

        # Relationship metrics
        dist = engine.scene_distance(da, db)
        angle = engine.scene_angle(da, db)
        pert_cost = engine.perturbation_cost(da, db)
        coh_delta = engine.coherence_delta(da, db)

        records.append({
            "pair": label,
            "bond_order": bo,
            "be": be,
            "hw_raw": snap["hw_raw"],
            "nrci_raw": snap["nrci_raw"],
            "bits_changed": snap["bits_changed"],
            "distance": dist,
            "angle": angle,
            "pert_cost": pert_cost,
            "coh_delta": coh_delta,
            "compactness": do_raw.compactness,
            "area": do_raw.area,
        })

    be_vals = [r["be"] for r in records]
    bo_vals = [r["bond_order"] for r in records]

    # Test all metrics
    metrics = [
        "hw_raw", "nrci_raw", "bits_changed", "distance",
        "angle", "pert_cost", "coh_delta", "compactness", "area",
    ]

    correlations = {}
    for m in metrics:
        vals = [r[m] for r in records]
        correlations[f"r_{m}_be"] = pearson_r(vals, be_vals)
        correlations[f"r_{m}_bo"] = pearson_r(vals, bo_vals)

    # Combined metrics
    combined = {
        "nrci × bo": [r["nrci_raw"] * r["bond_order"] for r in records],
        "hw × bo": [r["hw_raw"] * r["bond_order"] for r in records],
        "area × bo": [r["area"] * r["bond_order"] for r in records],
        "compact × bo": [r["compactness"] * r["bond_order"] for r in records],
        "nrci × dist": [r["nrci_raw"] * r["distance"] for r in records],
        "coh_delta × bo": [r["coh_delta"] * r["bond_order"] for r in records],
    }
    for name, vals in combined.items():
        correlations[f"r_{name}_be"] = pearson_r(vals, be_vals)

    best_be = max(correlations.items(), key=lambda x: abs(x[1]) if "_be" in x[0] else 0)
    best_bo = max(correlations.items(), key=lambda x: abs(x[1]) if "_bo" in x[0] else 0)

    # Benchmark: does NRCI × BO predict BE?
    nrci_x_bo = [r["nrci_raw"] * r["bond_order"] for r in records]
    r_nrcibo_be = pearson_r(nrci_x_bo, be_vals)
    bench.correlation_score("refined_nrci_x_bo_be", r_nrcibo_be, 0.5)

    if verbose:
        print(f"  Best r(BE): {best_be[1]:+.4f} via {best_be[0]}")
        print(f"  Best r(BO): {best_bo[1]:+.4f} via {best_bo[0]}")
        print(f"  NRCI × BO → r(BE) = {r_nrcibo_be:+.4f}")

        # Show predictions vs actuals
        print(f"\n  Predictions vs Actuals (sorted by BE):")
        sorted_records = sorted(records, key=lambda r: r["be"])
        for r in sorted_records:
            predicted = r["nrci_raw"] * r["bond_order"] * 200  # rough scaling
            error = abs(predicted - r["be"]) / max(r["be"], 1)
            status = "✓" if error < 0.3 else "✗"
            print(f"    {r['pair']:12s} BE={r['be']:4d} BO={r['bond_order']} "
                  f"NRCI={r['nrci_raw']:.4f} {status}")

    return records


def train_refined_geometry(bench: Benchmark, verbose: bool = True):
    """Refined geometry training — shapes with known properties."""
    if verbose:
        print("\n" + "=" * 70)
        print("REFINED GEOMETRY — Shapes with Known Properties")
        print("=" * 70)

    engine = SpatialEngine()

    # Shapes with known compactness
    shapes = {
        "point": [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "line_3": [1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "line_6": [1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "line_12": [1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
        "triangle": [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
        "square": [1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0],
        "hexagon": [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
        "octagon": [1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,0],
    }

    expected_compactness = {
        "point": 0.0, "line_3": 0.0, "line_6": 0.0, "line_12": 0.0,
        "triangle": 0.60, "square": 0.79, "hexagon": 0.91, "octagon": 0.95,
    }

    if verbose:
        print(f"\n  {'Shape':12s} {'HW':4s} {'Compact':8s} {'Expected':8s} {'Error':7s} {'NRCI':7s}")

    for name, bits in shapes.items():
        do = DataObject(bits, name)
        expected = expected_compactness.get(name, 0)
        error = abs(do.compactness - expected)
        passed = error < 0.15
        bench.score("shape_compactness", do.compactness, expected, 0.15)

        if verbose:
            status = "✓" if passed else "✗"
            print(f"  {name:12s} {do.hw:4d} {do.compactness:8.4f} {expected:8.4f} "
                  f"{error:7.4f} {do.nrci:7.4f} {status}")

    # Shape intersections
    if verbose:
        print(f"\n  Shape Intersections:")

    intersection_tests = [
        ("triangle", "square", "overlap", True),
        ("hexagon", "hexagon", "identical", True),
        ("line_3", "line_12", "contained", True),
        ("point", "line_6", "disjoint", False),
    ]

    for s1, s2, expected, should_overlap in intersection_tests:
        d1 = DataObject(shapes[s1], s1)
        d2 = DataObject(shapes[s2], s2)
        d_and = d1.and_with(d2)
        has_overlap = d_and.hw > 0
        correct = has_overlap == should_overlap
        bench.score("shape_intersection_refined", 1 if correct else 0, 1, 0.01)

        if verbose:
            status = "✓" if correct else "✗"
            print(f"    {s1} ∩ {s2} ({expected}): AND_HW={d_and.hw} {status}")


def train_refined_golay(bench: Benchmark, verbose: bool = True):
    """Refined Golay self-training with systematic error patterns."""
    if verbose:
        print("\n" + "=" * 70)
        print("REFINED GOLAY — Systematic Error Correction")
        print("=" * 70)

    if not HAS_GOLAY:
        print("  Golay engine not available")
        return

    engine = GOLAY_ENGINE

    # Generate a known codeword
    random.seed(42)
    raw = [random.randint(0, 1) for _ in range(24)]
    codeword, _ = engine.snap_to_codeword(raw)
    cw_hw = sum(codeword)

    if verbose:
        print(f"  Test codeword: HW={cw_hw}")

    # Systematic error injection
    for n_errors in range(1, 6):
        successes = 0
        trials = 20
        for trial in range(trials):
            random.seed(trial * 100 + n_errors)
            corrupted = codeword[:]
            error_positions = random.sample(range(24), n_errors)
            for pos in error_positions:
                corrupted[pos] = 1 - corrupted[pos]
            corrected, _ = engine.snap_to_codeword(corrupted)
            if corrected == codeword:
                successes += 1

        rate = successes / trials
        passed = rate > 0.5 if n_errors <= 3 else rate > 0.1
        bench.score("golay_systematic_correction", rate, 1.0 if n_errors <= 3 else 0.5, 0.5)

        if verbose:
            print(f"    {n_errors} errors: {successes}/{trials} corrected ({rate:.0%})")


# ═══════════════════════════════════════════════════════════════════════════════
# Update long-term memory
# ═══════════════════════════════════════════════════════════════════════════════

def update_long_term_memory(bench: Benchmark, bond_records: List[Dict]):
    """Update long-term memory with new findings."""
    ltm_path = SCRIPT_DIR.parent.parent / "long_term_memory"

    # Update benchmarks
    benchmarks_path = ltm_path / "benchmarks.md"
    with open(benchmarks_path, "w") as f:
        f.write("# Benchmarks — Latest Run\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("| Benchmark | Pass Rate | Metric |\n")
        f.write("|-----------|-----------|--------|\n")
        for name, data in bench.report().items():
            if "mean_r" in data:
                f.write(f"| {name} | {data['pass_rate']:.0%} | r = {data['mean_r']:+.4f} |\n")
            else:
                f.write(f"| {name} | {data['pass_rate']:.0%} | error = {data['mean_error']:.4f} |\n")

    # Update encoding knowledge with bond analysis
    enc_path = ltm_path / "encoding_knowledge.md"
    with open(enc_path, "a") as f:
        f.write("\n\n## Refined Bond Analysis (Iteration 12)\n\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M')}\n\n")

        # Best predictions
        sorted_records = sorted(bond_records, key=lambda r: r["be"])
        f.write("### Best Bond Energy Predictions\n\n")
        f.write("| Pair | BE | BO | NRCI | NRCI×BO |\n")
        f.write("|------|-----|-----|------|--------|\n")
        for r in sorted_records[:10]:
            f.write(f"| {r['pair']} | {r['be']} | {r['bond_order']} | "
                    f"{r['nrci_raw']:.4f} | {r['nrci_raw']*r['bond_order']:.4f} |\n")

    print(f"  Long-term memory updated")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_final_training():
    """Final training round — refined, using long-term memory."""
    print("=" * 70)
    print("GLM FINAL TRAINING — Using Long-Term Memory")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Read what we know
    knowledge = read_long_term_memory()
    print(f"Long-term memory: {len(knowledge)} files loaded")

    bench = Benchmark()

    # Use v0_baseline (proven to work with AND encoding)
    spec = EncodingSpec(
        name="v0_baseline",
        prop_set=["Z", "Rad", "EN", "Valence_e"],
        row_assignment=[0, 1, 2, 3],
        scaling={"Z": "identity", "Rad": "div4", "EN": "en_x15", "Valence_e": "valence_redundant"},
    )

    # Refined training
    bond_records = train_refined_bonds(spec, bench)
    train_refined_geometry(bench)
    train_refined_golay(bench)

    # Benchmark report
    print("\n" + "=" * 70)
    print("FINAL BENCHMARK REPORT")
    print("=" * 70)
    bench.print_report()

    # Update long-term memory
    update_long_term_memory(bench, bond_records)

    # Save benchmark
    out_path = SCRIPT_DIR.parent / "data" / f"benchmark_final_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(bench.report(), f, indent=2, default=str)
    print(f"\n  Benchmark saved to {out_path}")

    return bench


if __name__ == "__main__":
    run_final_training()
