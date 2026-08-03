"""
training_accumulate.py — Build Growing Training Data Files

Creates JSON files that grow with each training session:
1. element_encodings.json — all encoded elements with geometric metrics
2. bond_encodings.json — all encoded bonds with predictions
3. learned_patterns.json — patterns the mind has discovered
4. training_log.json — append-only log of every training run
"""

from __future__ import annotations
import sys, json, math, time, statistics
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb
from training_iteration import (
    EncodingSpec, encode_element, golay_snap, pearson_r, HAS_GOLAY,
)
from training_bond_geometry import snap_with_cost, encode_bond_and, BOND_DATA

if HAS_GOLAY:
    from training_iteration import GOLAY_ENGINE

Y = 0.2646754304045269672

DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Element Encodings — grows with each encoding we test
# ═══════════════════════════════════════════════════════════════════════════════

def build_element_encodings():
    """Encode all elements with multiple specs, save to JSON."""
    elements = kb.get_all_elements()

    specs = {
        "v0_baseline": EncodingSpec(
            name="v0_baseline", prop_set=["Z","Rad","EN","Valence_e"],
            row_assignment=[0,1,2,3],
            scaling={"Z":"identity","Rad":"div4","EN":"en_x15","Valence_e":"valence_redundant"}),
        "v1_best_dh": EncodingSpec(
            name="v1_best_dh", prop_set=["EN","BP","MP","Rho"],
            row_assignment=[0,1,2,3],
            scaling={"EN":"en_x10","BP":"div40","MP":"div40","Rho":"rho_x10"}),
        "v2_z_log": EncodingSpec(
            name="v2_z_log", prop_set=["Z","Rad","EN","M"],
            row_assignment=[0,1,2,3],
            scaling={"Z":"log2","Rad":"div8","EN":"en_x10","M":"log2"}),
    }

    result = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_elements": len(elements),
        "specs": {},
    }

    for spec_name, spec in specs.items():
        encodings = {}
        for sym, elem in elements.items():
            vec_raw = encode_element(sym, spec)
            vec_snapped = golay_snap(vec_raw)
            hw_raw = sum(vec_raw)
            hw_snapped = sum(vec_snapped)
            bits_changed = sum(1 for i in range(24) if vec_raw[i] != vec_snapped[i])

            # 2D projection
            points = []
            for i, v in enumerate(vec_raw):
                if v:
                    angle = 2 * math.pi * i / 24
                    points.append([round(math.cos(angle), 4), round(math.sin(angle), 4)])

            # Centroid
            if points:
                cx = sum(p[0] for p in points) / len(points)
                cy = sum(p[1] for p in points) / len(points)
            else:
                cx, cy = 0, 0

            # TAX/NRCI
            tax = hw_raw * Y + sum(v*v for v in vec_raw) / 8.0
            nrci = 10.0 / (10.0 + tax)

            encodings[sym] = {
                "z": int(elem.properties.get("Z", 0)),
                "vec_raw": vec_raw,
                "vec_snapped": vec_snapped,
                "hw_raw": hw_raw,
                "hw_snapped": hw_snapped,
                "bits_changed": bits_changed,
                "nrci": round(nrci, 6),
                "centroid": [round(cx, 4), round(cy, 4)],
                "properties": {k: str(v) for k, v in elem.properties.items()},
            }

        # Statistics
        hws = [e["hw_raw"] for e in encodings.values()]
        nrcis = [e["nrci"] for e in encodings.values()]
        unique_vecs = len(set(tuple(e["vec_snapped"]) for e in encodings.values()))

        result["specs"][spec_name] = {
            "spec": spec.to_dict(),
            "encodings": encodings,
            "stats": {
                "unique_vectors": unique_vecs,
                "mean_hw": round(statistics.mean(hws), 2),
                "mean_nrci": round(statistics.mean(nrcis), 4),
                "hw_distribution": dict(Counter(hws)),
            }
        }

    out_path = DATA_DIR / "element_encodings.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  element_encodings.json: {len(elements)} elements × {len(specs)} specs")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Bond Encodings — grows with each bond analysis
# ═══════════════════════════════════════════════════════════════════════════════

def build_bond_encodings():
    """Encode all bonds with AND encoding, save to JSON."""
    spec = EncodingSpec(
        name="v0_baseline", prop_set=["Z","Rad","EN","Valence_e"],
        row_assignment=[0,1,2,3],
        scaling={"Z":"identity","Rad":"div4","EN":"en_x15","Valence_e":"valence_redundant"})

    records = []
    for ea, eb, bo, be, label in BOND_DATA:
        if kb.get_element(ea) is None or kb.get_element(eb) is None:
            continue

        # AND encoding
        raw = encode_bond_and(ea, eb, spec)
        snap = snap_with_cost(raw)

        # Element vectors
        va = encode_element(ea, spec)
        vb = encode_element(eb, spec)

        # 2D projection of AND result
        points = []
        for i, v in enumerate(raw):
            if v:
                angle = 2 * math.pi * i / 24
                points.append([round(math.cos(angle), 4), round(math.sin(angle), 4)])

        # Centroid
        if points:
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
        else:
            cx, cy = 0, 0

        # Distance between element centroids
        pts_a = []
        for i, v in enumerate(va):
            if v:
                angle = 2 * math.pi * i / 24
                pts_a.append((math.cos(angle), math.sin(angle)))
        pts_b = []
        for i, v in enumerate(vb):
            if v:
                angle = 2 * math.pi * i / 24
                pts_b.append((math.cos(angle), math.sin(angle)))

        if pts_a and pts_b:
            cax = sum(p[0] for p in pts_a) / len(pts_a)
            cay = sum(p[1] for p in pts_a) / len(pts_a)
            cbx = sum(p[0] for p in pts_b) / len(pts_b)
            cby = sum(p[1] for p in pts_b) / len(pts_b)
            dist = math.sqrt((cax-cbx)**2 + (cay-cby)**2)
        else:
            dist = 0

        records.append({
            "pair": label,
            "elem_a": ea,
            "elem_b": eb,
            "bond_order": bo,
            "be_measured": be,
            "and_bits": raw,
            "and_hw": snap["hw_raw"],
            "and_nrci": round(snap["nrci_raw"], 6),
            "centroid": [round(cx, 4), round(cy, 4)],
            "bits_changed_by_snap": snap["bits_changed"],
            "element_distance": round(dist, 4),
            "be_predicted_nrci_bo": round(snap["nrci_raw"] * bo * 200, 1),
            "prediction_error_pct": round(abs(snap["nrci_raw"] * bo * 200 - be) / max(be, 1) * 100, 1),
        })

    # Correlations
    be_vals = [r["be_measured"] for r in records]
    nrci_x_bo = [r["and_nrci"] * r["bond_order"] for r in records]
    r_nrcibo = pearson_r(nrci_x_bo, be_vals)

    result = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_bonds": len(records),
        "encoding": "AND",
        "spec": spec.to_dict(),
        "correlations": {
            "r_nrci_x_bo_vs_be": round(r_nrcibo, 4),
        },
        "bonds": records,
    }

    out_path = DATA_DIR / "bond_encodings.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  bond_encodings.json: {len(records)} bonds, r(NRCI×BO, BE) = {r_nrcibo:+.4f}")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Learned Patterns — grows as we discover patterns
# ═══════════════════════════════════════════════════════════════════════════════

def build_learned_patterns():
    """Record patterns the mind has discovered."""
    patterns = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "patterns": [
            {
                "id": "P001",
                "name": "AND encoding captures shared structure",
                "domain": "bond_energy",
                "evidence": "r(NRCI×BO, BE) = +0.90",
                "confidence": 0.90,
                "description": "The AND of two element vectors captures shared electron density. Combined with bond order, it predicts bond energy with high fidelity.",
            },
            {
                "id": "P002",
                "name": "Pre-snap metrics carry more signal",
                "domain": "encoding",
                "evidence": "Raw NRCI correlates with chemistry better than snapped NRCI",
                "confidence": 0.85,
                "description": "The raw vector before Golay snap contains more physical information than the snapped vector. The snap cost itself is signal.",
            },
            {
                "id": "P003",
                "name": "Noble gases are the vacuum state",
                "domain": "elements",
                "evidence": "HW=0, NRCI=1.0 for He, Ne, Ar, Kr, Xe",
                "confidence": 1.0,
                "description": "Noble gas Data Objects encode as the zero vector — perfect coherence, no perturbation. They are the substrate's vacuum.",
            },
            {
                "id": "P004",
                "name": "Same-element pairs are invisible",
                "domain": "bond_energy",
                "evidence": "AND/XOR gives HW=0 for C-C, N-N, O-O",
                "confidence": 1.0,
                "description": "When both elements are identical, their AND and XOR produce zero vectors. The substrate cannot distinguish C-C from C≡C.",
            },
            {
                "id": "P005",
                "name": "Bond order partially inferable from geometry",
                "domain": "bond_energy",
                "evidence": "r(BO, HW) = +0.52",
                "confidence": 0.52,
                "description": "The HW of the AND encoding correlates moderately with bond order. The substrate can partially infer single/double/triple from geometry.",
            },
            {
                "id": "P006",
                "name": "Compactness measures geometric regularity",
                "domain": "geometry",
                "evidence": "Triangle=0.58, Square=0.79, Hexagon=0.91, Dodecagon=0.98",
                "confidence": 0.95,
                "description": "The compactness metric (4π·Area/Perimeter²) approaches 1.0 as shapes become more circular. The substrate naturally measures regularity.",
            },
            {
                "id": "P007",
                "name": "NRCI decreases with pure-element chain length",
                "domain": "molecules",
                "evidence": "H-F NRCI=0.93, C-C NRCI=0.66, N-N NRCI=0.65",
                "confidence": 0.80,
                "description": "Heteronuclear bonds have higher NRCI than homonuclear chains. The substrate sees electron asymmetry as coherence.",
            },
            {
                "id": "P008",
                "name": "Golay corrects exactly 3 errors",
                "domain": "substrate",
                "evidence": "100% correction for 1-3 errors, 0% for 4-5 errors",
                "confidence": 1.0,
                "description": "The Golay [24,12,8] code corrects exactly 3 errors as predicted by theory. No more, no less.",
            },
            {
                "id": "P009",
                "name": "Small integers snap to zero",
                "domain": "numbers",
                "evidence": "Integers 0-7 all snap to HW=0",
                "confidence": 0.90,
                "description": "Small integers encoded as 24-bit vectors are 'close to zero' in the Golay metric. The substrate treats them as near-vacuum states.",
            },
            {
                "id": "P010",
                "name": "Golden ratio appears in decagon radius",
                "domain": "geometry",
                "evidence": "R(10) = 1.618034",
                "confidence": 1.0,
                "description": "The regular decagon radius R(10) = 1/(2·sin(π/10)) = φ (golden ratio). Mathematical constants emerge from the substrate's geometry.",
            },
        ],
    }

    out_path = DATA_DIR / "learned_patterns.json"
    with open(out_path, "w") as f:
        json.dump(patterns, f, indent=2)
    print(f"  learned_patterns.json: {len(patterns['patterns'])} patterns")
    return patterns


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Training Log — append-only record of every training run
# ═══════════════════════════════════════════════════════════════════════════════

def append_training_log(entry: Dict):
    """Append a training run to the log."""
    log_path = DATA_DIR / "training_log.json"

    if log_path.exists():
        with open(log_path) as f:
            log = json.load(f)
    else:
        log = {"runs": []}

    entry["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    log["runs"].append(entry)

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"  training_log.json: {len(log['runs'])} runs recorded")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Molecule Encodings
# ═══════════════════════════════════════════════════════════════════════════════

def build_molecule_encodings():
    """Encode all molecules with the best spec."""
    from training_iteration_v3 import encode_molecule

    molecules = kb.get_all_molecules()

    # Use M, MP encoding (best for molecules)
    spec = EncodingSpec(
        name="mol_m_mp", prop_set=["M","MP","M","MP"],
        row_assignment=[0,1,2,3],
        scaling={"M":"log2","MP":"div40"})

    encodings = {}
    for name, mol in molecules.items():
        vec_raw = encode_molecule(name, spec)
        vec_snapped = golay_snap(vec_raw)
        hw = sum(vec_snapped)
        nrci = 10.0 / (10.0 + hw * Y + sum(v*v for v in vec_snapped) / 8.0)

        encodings[name] = {
            "vec_snapped": vec_snapped,
            "hw": hw,
            "nrci": round(nrci, 6),
            "nrci_kb": round(mol.nrci_val, 6),
            "properties": {k: str(v) for k, v in mol.properties.items()},
        }

    unique_vecs = len(set(tuple(e["vec_snapped"]) for e in encodings.values()))

    result = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_molecules": len(molecules),
        "spec": spec.to_dict(),
        "stats": {
            "unique_vectors": unique_vecs,
            "hw_distribution": dict(Counter(e["hw"] for e in encodings.values())),
        },
        "molecules": encodings,
    }

    out_path = DATA_DIR / "molecule_encodings.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  molecule_encodings.json: {len(molecules)} molecules, {unique_vecs} unique vectors")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def build_all_training_data():
    """Build all growing training data files."""
    print("=" * 70)
    print("BUILDING TRAINING DATA FILES")
    print("=" * 70)

    t0 = time.time()

    elem_data = build_element_encodings()
    bond_data = build_bond_encodings()
    mol_data = build_molecule_encodings()
    patterns = build_learned_patterns()

    # Append training log
    append_training_log({
        "iteration": 12,
        "focus": "Full data accumulation",
        "n_elements": elem_data["n_elements"],
        "n_bonds": bond_data["n_bonds"],
        "n_molecules": mol_data["n_molecules"],
        "n_patterns": len(patterns["patterns"]),
        "best_r_be": bond_data["correlations"]["r_nrci_x_bo_vs_be"],
    })

    elapsed = time.time() - t0
    print(f"\n  All files built in {elapsed:.1f}s")
    print(f"  Location: {DATA_DIR}")

    # List files with sizes
    print(f"\n  Files:")
    for f in sorted(DATA_DIR.glob("*.json")):
        size = f.stat().st_size
        print(f"    {f.name:35s} {size:8,} bytes")

    # Consolidate into long_term_memory/glm_training_data.json
    LTM_DIR = SCRIPT_DIR.parent.parent / "long_term_memory"
    LTM_DIR.mkdir(exist_ok=True)
    consolidated = {
        "version": 2,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "description": "GLM consolidated training data",
        "elements": elem_data,
        "bonds": bond_data,
        "molecules": mol_data,
        "patterns": patterns,
    }
    ltm_path = LTM_DIR / "glm_training_data.json"
    with open(ltm_path, "w") as f:
        json.dump(consolidated, f, indent=2, default=str)
    print(f"\n  Consolidated → {ltm_path} ({ltm_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build_all_training_data()
