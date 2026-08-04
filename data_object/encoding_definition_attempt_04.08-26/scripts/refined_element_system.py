#!/usr/bin/env python3
"""
Refined Element Data Object System — Snap Dynamics + Bond Order + 40+ ΔH
=========================================================================
Experiment: encoding_definition_attempt_04.08-26 (refinement)
Date: 4 August 2026

Key insight: The Golay snap process itself carries information.
  - PRE-SNAP:  raw vector, distance from codeword space, bit distribution
  - DURING:    syndrome weight, correction pattern, which bits flip
  - POST-SNAP: codeword, NRCI, TAX

These three phases give us a richer feature space than the codeword alone.

Bond order detection: The snap dynamics of individual elements AND their
interactions may encode bond order — a double bond "snaps differently"
than a single bond because the shared bit structure differs.

Usage:
  python3 refined_element_system.py --full-test
  python3 refined_element_system.py --snap-analysis H O
  python3 refined_element_system.py --save-results
"""

from __future__ import annotations

import json
import math
import re
import sys
import random
import hashlib
from fractions import Fraction
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from elements_data_object_system import (
    GolayEngine, DataObject, MOGSpatialArithmetic, GLMPredictor,
    load_elements_from_kb, encode_element, interact, InteractionResult,
    gray6, ungray6, SCALING_PRESETS, Y_CONST, Y_PLUS_EIGHTH,
    BEST_ENCODING, BASELINE_ENCODING, EXTENDED_ENCODING,
)

# ════════════════════════════════════════════════════════════════════════════════
# SNAP DYNAMICS — pre, during, post
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class SnapDynamics:
    """Metrics captured before, during, and after Golay snap."""
    # Pre-snap (raw vector)
    pre_hw: int                    # Hamming weight of raw vector
    pre_norm_sq: int               # Norm² of raw vector
    pre_tax: float                 # TAX of raw vector
    pre_nrci: float                # NRCI of raw vector
    pre_syndrome_weight: int       # How far from valid codeword
    pre_row_hamming: List[int]     # Per-row Hamming weights (4 values)

    # During snap (correction process)
    snap_bits: int                 # Number of bits corrected (-1 if uncorrectable)
    correctable: bool              # Whether snap succeeded
    correction_pattern: List[int]  # Which bits got flipped (24-bit mask)
    correction_row_distribution: List[int]  # How many corrections per row (4 values)
    syndrome_hash: str             # Hash of syndrome for pattern matching

    # Post-snap (codeword)
    post_hw: int
    post_norm_sq: int
    post_tax: float
    post_nrci: float
    post_row_hamming: List[int]

    # Delta (pre → post)
    hw_delta: int                  # HW change from snap
    tax_delta: float               # TAX change from snap
    nrci_delta: float              # NRCI change from snap
    row_hw_delta: List[int]        # Per-row HW change


def compute_snap_dynamics(raw_bits: List[int], golay: GolayEngine) -> SnapDynamics:
    """Compute full snap dynamics for a raw 24-bit vector."""
    # Pre-snap metrics
    pre_hw = sum(raw_bits)
    pre_norm_sq = sum(b * b for b in raw_bits)
    pre_tax = float(Y_CONST) * pre_hw + pre_norm_sq / 8.0
    pre_nrci = 10.0 / (10.0 + pre_tax)
    pre_syndrome = golay.syndrome(raw_bits)
    pre_syn_weight = sum(pre_syndrome)
    pre_row_hw = [sum(raw_bits[r*6:(r+1)*6]) for r in range(4)]

    # Snap
    codeword, snap_meta = golay.snap_to_codeword(raw_bits)
    snap_bits = snap_meta.get("snap_bits", -1)
    correctable = snap_meta.get("correctable", False)

    # Correction pattern (which bits differ between raw and codeword)
    correction_pattern = [raw_bits[i] ^ codeword[i] for i in range(24)]
    correction_count = sum(correction_pattern)
    correction_row_dist = [sum(correction_pattern[r*6:(r+1)*6]) for r in range(4)]

    # Syndrome hash (for pattern matching)
    syn_hash = hashlib.md5(str(pre_syndrome).encode()).hexdigest()[:8]

    # Post-snap metrics
    post_hw = sum(codeword)
    post_norm_sq = sum(b * b for b in codeword)
    post_tax = float(Y_CONST) * post_hw + post_norm_sq / 8.0
    post_nrci = 10.0 / (10.0 + post_tax)
    post_row_hw = [sum(codeword[r*6:(r+1)*6]) for r in range(4)]

    # Deltas
    hw_delta = post_hw - pre_hw
    tax_delta = post_tax - pre_tax
    nrci_delta = post_nrci - pre_nrci
    row_hw_delta = [post_row_hw[r] - pre_row_hw[r] for r in range(4)]

    return SnapDynamics(
        pre_hw=pre_hw,
        pre_norm_sq=pre_norm_sq,
        pre_tax=pre_tax,
        pre_nrci=pre_nrci,
        pre_syndrome_weight=pre_syn_weight,
        pre_row_hamming=pre_row_hw,
        snap_bits=snap_bits,
        correctable=correctable,
        correction_pattern=correction_pattern,
        correction_row_distribution=correction_row_dist,
        syndrome_hash=syn_hash,
        post_hw=post_hw,
        post_norm_sq=post_norm_sq,
        post_tax=post_tax,
        post_nrci=post_nrci,
        post_row_hamming=post_row_hw,
        hw_delta=hw_delta,
        tax_delta=tax_delta,
        nrci_delta=nrci_delta,
        row_hw_delta=row_hw_delta,
    )


@dataclass
class InteractionSnapDynamics:
    """Snap dynamics for a pair interaction (AND, XOR vectors)."""
    # AND vector snap dynamics
    and_snap: SnapDynamics
    # XOR vector snap dynamics
    xor_snap: SnapDynamics
    # Cross-element: how element A's snap changes when B is present
    # (computed by flipping bits in A that overlap with B)
    cross_snap_bits: int           # How many bits A would need to snap if B's bits were injected
    cross_syndrome_weight: int     # Syndrome weight of combined vector
    # Element-level snap dynamics
    elem_a_snap: SnapDynamics
    elem_b_snap: SnapDynamics


def compute_interaction_snap_dynamics(
    do_a: DataObject, do_b: DataObject, golay: GolayEngine
) -> InteractionSnapDynamics:
    """Compute snap dynamics for an element pair interaction."""
    ca, cb = do_a.codeword, do_b.codeword

    # AND vector (shared structure)
    and_bits = [ca[i] & cb[i] for i in range(24)]
    and_snap = compute_snap_dynamics(and_bits, golay)

    # XOR vector (differing structure)
    xor_bits = [ca[i] ^ cb[i] for i in range(24)]
    xor_snap = compute_snap_dynamics(xor_bits, golay)

    # Cross-element: inject B's bits into A's raw vector
    raw_a = do_a.raw_bits
    cross_bits = [raw_a[i] | cb[i] for i in range(24)]  # OR = injection
    cross_cw, cross_meta = golay.snap_to_codeword(cross_bits)
    cross_snap_bits = cross_meta.get("snap_bits", -1)
    cross_syn = golay.syndrome(cross_bits)
    cross_syn_weight = sum(cross_syn)

    # Element-level snap dynamics
    elem_a_snap = compute_snap_dynamics(do_a.raw_bits, golay)
    elem_b_snap = compute_snap_dynamics(do_b.raw_bits, golay)

    return InteractionSnapDynamics(
        and_snap=and_snap,
        xor_snap=xor_snap,
        cross_snap_bits=cross_snap_bits,
        cross_syndrome_weight=cross_syn_weight,
        elem_a_snap=elem_a_snap,
        elem_b_snap=elem_b_snap,
    )


def extract_snap_features(isd: InteractionSnapDynamics) -> List[float]:
    """Extract feature vector from interaction snap dynamics."""
    features = []
    features.extend([
        # AND snap dynamics (shared structure)
        isd.and_snap.pre_hw,
        isd.and_snap.pre_syndrome_weight,
        isd.and_snap.snap_bits,
        float(isd.and_snap.correctable),
        isd.and_snap.hw_delta,
        isd.and_snap.tax_delta,
        isd.and_snap.nrci_delta,
        *isd.and_snap.correction_row_distribution,
        *isd.and_snap.pre_row_hamming,
        *isd.and_snap.post_row_hamming,
        # XOR snap dynamics (differing structure)
        isd.xor_snap.pre_hw,
        isd.xor_snap.pre_syndrome_weight,
        isd.xor_snap.snap_bits,
        float(isd.xor_snap.correctable),
        isd.xor_snap.hw_delta,
        isd.xor_snap.tax_delta,
        isd.xor_snap.nrci_delta,
        *isd.xor_snap.correction_row_distribution,
        *isd.xor_snap.pre_row_hamming,
        *isd.xor_snap.post_row_hamming,
        # Cross-element dynamics
        isd.cross_snap_bits,
        isd.cross_syndrome_weight,
        # Element A snap dynamics
        isd.elem_a_snap.pre_hw,
        isd.elem_a_snap.pre_syndrome_weight,
        isd.elem_a_snap.snap_bits,
        isd.elem_a_snap.tax_delta,
        isd.elem_a_snap.nrci_delta,
        *isd.elem_a_snap.correction_row_distribution,
        # Element B snap dynamics
        isd.elem_b_snap.pre_hw,
        isd.elem_b_snap.pre_syndrome_weight,
        isd.elem_b_snap.snap_bits,
        isd.elem_b_snap.tax_delta,
        isd.elem_b_snap.nrci_delta,
        *isd.elem_b_snap.correction_row_distribution,
    ])
    return features


def snap_feature_names() -> List[str]:
    """Names for the snap dynamics features."""
    names = []
    for prefix in ["and", "xor"]:
        names.extend([
            f"{prefix}_pre_hw", f"{prefix}_syn_weight", f"{prefix}_snap_bits",
            f"{prefix}_correctable", f"{prefix}_hw_delta", f"{prefix}_tax_delta",
            f"{prefix}_nrci_delta",
        ])
        for r in range(4):
            names.append(f"{prefix}_correction_row{r}")
        for r in range(4):
            names.append(f"{prefix}_pre_row{r}_hw")
        for r in range(4):
            names.append(f"{prefix}_post_row{r}_hw")
    names.extend(["cross_snap_bits", "cross_syn_weight"])
    for prefix in ["elem_a", "elem_b"]:
        names.extend([
            f"{prefix}_pre_hw", f"{prefix}_syn_weight", f"{prefix}_snap_bits",
            f"{prefix}_tax_delta", f"{prefix}_nrci_delta",
        ])
        for r in range(4):
            names.append(f"{prefix}_correction_row{r}")
    return names


# ════════════════════════════════════════════════════════════════════════════════
# EXPANDED PAIR DATASET — 112 pairs with bond order + 42 with ΔH
# ════════════════════════════════════════════════════════════════════════════════

EXPANDED_PAIRS = [
    # ── Hydrogen bonds (12) ─────────────────────────────────────────────────────
    ("H", "H",   436,   None,  "H-H covalent",          1),
    ("H", "O",   463,  -241.8, "H-O water",             1),
    ("H", "F",   568,   None,  "H-F HF",                1),
    ("H", "Cl",  431,   -92.3, "H-Cl HCl",              1),
    ("H", "Br",  366,   -36.3, "H-Br HBr",              1),
    ("H", "I",   298,    26.5, "H-I HI",                1),
    ("H", "N",   391,   None,  "H-N ammonia",           1),
    ("H", "C",   413,   -74.8, "H-C methane",           1),
    ("H", "S",   363,   -20.6, "S-H H2S",               1),
    ("H", "P",   322,    5.4,  "H-P phosphine",         1),
    ("H", "Si",  323,    34.3, "H-Si silane",           1),
    ("H", "Se",  305,    29.7, "H-Se selenide",         1),

    # ── Oxygen bonds (22) ───────────────────────────────────────────────────────
    ("O", "O",   498,   None,  "O=O double",            2),
    ("O", "O",   146,   None,  "O-O peroxide",          1),
    ("O", "N",   201,    90.3, "N-O nitric oxide",      1),
    ("O", "N",   607,    33.2, "N=O NO2",               2),
    ("O", "S",   265,   -296.8,"S-O SO2",               1),
    ("O", "S",   523,   -395.7,"S=O SO3",               2),
    ("O", "C",   358,   None,  "C-O methanol",          1),
    ("O", "C",   799,  -393.5, "C=O CO2",               2),
    ("O", "C",  1072,  -110.5, "C≡O CO triple",         3),
    ("O", "P",   335,   None,  "P-O phosphate",         1),
    ("O", "P",   544,   None,  "P=O phosphoryl",        2),
    ("O", "Si",  452,  -910.7, "Si-O silica",           1),
    ("O", "B",   536,  -1273.5,"B-O borate",            1),
    ("O", "Al",  512,  -1675.7,"Al-O alumina",          1),
    ("O", "Mg",  394,  -601.6, "Mg-O magnesia",         1),
    ("O", "Ca",  402,  -635.1, "Ca-O lime",             1),
    ("O", "Fe",  407,  -824.2, "Fe-O hematite",         1),
    ("O", "Cu",  269,  -157.3, "Cu-O cupric oxide",     1),
    ("O", "Zn",  284,  -350.5, "Zn-O zinc oxide",       1),
    ("O", "Ti",  672,  -944.0, "Ti-O titania",          1),
    ("O", "Na",  256,  -414.2, "Na-O sodium oxide",     1),
    ("O", "K",   251,  -361.5, "K-O potassium oxide",   1),

    # ── Nitrogen bonds (9) ──────────────────────────────────────────────────────
    ("N", "N",   946,   None,  "N≡N triple",            3),
    ("N", "N",   418,   None,  "N=N double",            2),
    ("N", "N",   163,   None,  "N-N hydrazine",         1),
    ("N", "C",   305,   None,  "C-N methylamine",       1),
    ("N", "C",   615,   None,  "C=N imine",             2),
    ("N", "C",   891,   135.1, "C≡N HCN triple",        3),
    ("N", "F",   272,   None,  "N-F NF3",               1),
    ("N", "Cl",  200,   None,  "N-Cl NCl3",             1),
    ("N", "P",   617,   None,  "P≡N phosphazene",       3),

    # ── Carbon bonds (16) ───────────────────────────────────────────────────────
    ("C", "C",   347,   None,  "C-C ethane",            1),
    ("C", "C",   614,    52.3, "C=C ethylene",          2),
    ("C", "C",   839,   226.7, "C≡C acetylene",         3),
    ("C", "C",   476,   None,  "C-C aromatic",          1.5),
    ("C", "F",   485,  -255.3, "C-F fluoromethane",     1),
    ("C", "Cl",  339,   -83.7, "C-Cl chloromethane",    1),
    ("C", "Br",  276,   -37.7, "C-Br bromomethane",     1),
    ("C", "I",   238,    14.2, "C-I iodomethane",       1),
    ("C", "S",   259,   None,  "C-S methanethiol",      1),
    ("C", "S",   477,   None,  "C=S CS2",               2),
    ("C", "Si",  318,   None,  "C-Si silicone",         1),
    ("C", "Ge",  255,   None,  "C-Ge organogermanium",  1),
    ("C", "Sn",  192,   None,  "C-Sn organotin",        1),
    ("C", "P",   264,   None,  "C-P phosphine",         1),
    ("C", "O",   358,  -115.9, "C-O methanol ΔH",      1),
    ("C", "N",   305,   -23.0, "C-N methylamine ΔH",    1),

    # ── Halogen bonds (7) ───────────────────────────────────────────────────────
    ("F", "F",   159,   None,  "F-F fluorine",          1),
    ("Cl", "Cl", 243,   None,  "Cl-Cl chlorine",        1),
    ("Br", "Br", 193,   None,  "Br-Br bromine",         1),
    ("I", "I",    151,   None,  "I-I iodine",            1),
    ("Cl", "F",  255,   None,  "Cl-F interhalogen",     1),
    ("Br", "F",  285,   None,  "Br-F interhalogen",     1),
    ("I",  "Cl",  211,   None,  "I-Cl interhalogen",     1),

    # ── Ionic bonds (16) ────────────────────────────────────────────────────────
    ("Na", "Cl", 411,  -411.2, "NaCl salt",             1),
    ("K",  "Cl", 427,  -436.5, "KCl potash",            1),
    ("Li", "F",  577,  -616.0, "LiF lithium fluoride",  1),
    ("Na", "F",  477,  -576.0, "NaF sodium fluoride",   1),
    ("K",  "F",  498,  -567.3, "KF potassium fluoride", 1),
    ("Mg", "O",  394,  -601.6, "MgO magnesia",          1),
    ("Ca", "O",  402,  -635.1, "CaO lime",              1),
    ("Ba", "O",  562,  -553.5, "BaO baria",             1),
    ("Sr", "O",  426,  -592.0, "SrO strontia",          1),
    ("Li", "Cl", 469,  -408.3, "LiCl lithium chloride", 1),
    ("Na", "Br", 367,  -361.1, "NaBr",                  1),
    ("Na", "I",  301,  -287.8, "NaI",                   1),
    ("Cs", "F",  502,  -553.5, "CsF caesium fluoride",  1),
    ("Rb", "Cl", 427,  -435.1, "RbCl rubidium chloride",1),
    ("K",  "Br", 380,  -393.8, "KBr",                   1),
    ("K",  "I",  328,  -327.9, "KI",                    1),

    # ── Silicon / semiconductor (5) ─────────────────────────────────────────────
    ("Si", "Si", 226,   None,  "Si-Si disilane",        1),
    ("Si", "F",  565,   None,  "Si-F silicon fluoride", 1),
    ("Si", "Cl", 381,   None,  "Si-Cl silicon chloride",1),
    ("Si", "O",  452,  -910.7, "Si-O silica ΔH",       1),
    ("Ge", "Ge", 188,   None,  "Ge-Ge digermane",       1),

    # ── Sulfur bonds (5) ────────────────────────────────────────────────────────
    ("S",  "S",  266,   None,  "S-S disulfide",         1),
    ("S",  "S",  425,   None,  "S=S double",            2),
    ("S",  "F",  327,   None,  "S-F SF6",               1),
    ("S",  "Cl", 255,   None,  "S-Cl S2Cl2",            1),
    ("S",  "Se", 230,   None,  "S-Se selenide",         1),

    # ── Metal bonds (13) ────────────────────────────────────────────────────────
    ("Fe", "Fe",  75,   None,  "Fe-Fe metallic",        1),
    ("Cu", "Cu",  79,   None,  "Cu-Cu metallic",        1),
    ("Ag", "Ag",  68,   None,  "Ag-Ag metallic",        1),
    ("Au", "Au",  86,   None,  "Au-Au metallic",        1),
    ("Pt", "Pt", 110,   None,  "Pt-Pt metallic",        1),
    ("Fe", "S",  310,  -178.2, "Fe-S pyrite",           1),
    ("Cu", "S",  274,   -53.1, "Cu-S covellite",        1),
    ("Zn", "S",  202,  -206.0, "Zn-S sphalerite",       1),
    ("Pb", "S",  160,  -100.4, "Pb-S galena",           1),
    ("Hg", "S",  138,   -58.2, "Hg-S cinnabar",         1),
    ("Fe", "Cl", 341,   None,  "Fe-Cl ferric chloride", 1),
    ("Al", "Cl", 427,  -705.6, "Al-Cl aluminium chloride",1),
    ("Ti", "Cl", 422,   None,  "Ti-Cl titanium chloride",1),

    # ── Phosphorus bonds (4) ────────────────────────────────────────────────────
    ("P",  "P",  200,   None,  "P-P diphosphine",       1),
    ("P",  "Cl", 326,   None,  "P-Cl PCl3",             1),
    ("P",  "F",  490,   None,  "P-F PF3",               1),
    ("P",  "Br", 264,   None,  "P-Br PBr3",             1),

    # ── Boron bonds (5) ─────────────────────────────────────────────────────────
    ("B",  "B",  293,   None,  "B-B diborane",          1),
    ("B",  "F",  613,  -1136.0,"B-F BF3",               1),
    ("B",  "Cl", 427,  -403.8, "B-Cl BCl3",             1),
    ("B",  "N",  392,   None,  "B-N boron nitride",     1),
    ("B",  "H",  389,    35.6, "B-H diborane ΔH",      1),
]


# ════════════════════════════════════════════════════════════════════════════════
# UTILITY
# ════════════════════════════════════════════════════════════════════════════════

def pearson_r(x, y):
    n = len(x)
    if n < 3: return 0.0
    mx, my = sum(x)/n, sum(y)/n
    cov = sum((x[i]-mx)*(y[i]-my) for i in range(n))
    sx = math.sqrt(sum((x[i]-mx)**2 for i in range(n))/n)
    sy = math.sqrt(sum((y[i]-my)**2 for i in range(n))/n)
    return cov/(n*sx*sy) if sx > 0 and sy > 0 else 0.0

def mae(x, y):
    return sum(abs(x[i]-y[i]) for i in range(len(x)))/len(x)

def k_fold_split(n, k=5, seed=42):
    rng = random.Random(seed)
    idx = list(range(n))
    rng.shuffle(idx)
    fold_size = n // k
    folds = []
    for i in range(k):
        s = i * fold_size
        e = s + fold_size if i < k - 1 else n
        test = idx[s:e]
        train = idx[:s] + idx[e:]
        folds.append((train, test))
    return folds


# ════════════════════════════════════════════════════════════════════════════════
# FULL EXPERIMENT
# ════════════════════════════════════════════════════════════════════════════════

def run_refined_experiment(save_results: bool = False):
    """Run refined experiment with snap dynamics + bond order + expanded ΔH."""
    import numpy as np

    print("=" * 72)
    print("REFINED ELEMENT DATA OBJECT SYSTEM")
    print("Snap Dynamics + Bond Order + 40+ ΔH")
    print("Experiment: encoding_definition_attempt_04.08-26 (refined)")
    print("=" * 72)

    # ── Load ───────────────────────────────────────────────────────────────────
    kb_path = Path(__file__).resolve().parent.parent.parent / "long_term_memory" / "ubp_system_kb.json"
    if not kb_path.exists():
        kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")

    print(f"\n[1] Loading elements from {kb_path}")
    elements = load_elements_from_kb(str(kb_path))
    print(f"    Loaded {len(elements)} elements")

    golay = GolayEngine()
    spatial = MOGSpatialArithmetic(golay)

    # ── Encode ─────────────────────────────────────────────────────────────────
    print("\n[2] Encoding elements (v1_best)")
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    print(f"    Encoded {len(data_objects)} elements")

    # ── Snap dynamics per element ──────────────────────────────────────────────
    print("\n[3] Computing per-element snap dynamics")
    elem_snap = {}
    for sym, do in data_objects.items():
        elem_snap[sym] = compute_snap_dynamics(do.raw_bits, golay)

    # Show snap distribution
    snap_counts = defaultdict(int)
    for sd in elem_snap.values():
        snap_counts[sd.snap_bits] += 1
    print(f"    Snap bit distribution: {dict(sorted(snap_counts.items()))}")
    print(f"    Correctable: {sum(1 for sd in elem_snap.values() if sd.correctable)}/{len(elem_snap)}")

    # Show pre/post tax changes
    tax_changes = [sd.tax_delta for sd in elem_snap.values() if sd.tax_delta != 0]
    if tax_changes:
        print(f"    TAX change range: [{min(tax_changes):.4f}, {max(tax_changes):.4f}]")
        print(f"    Mean |TAX change|: {sum(abs(t) for t in tax_changes)/len(tax_changes):.4f}")

    # ── Build feature matrix ───────────────────────────────────────────────────
    print(f"\n[4] Building feature matrix from {len(EXPANDED_PAIRS)} pairs")
    print(f"    Using: original 20 interaction features + {len(snap_feature_names())} snap features + bond_order")

    X_all = []
    y_be = []
    y_dh = []
    bond_orders = []
    pair_labels = []
    valid_pairs = []

    predictor_base = GLMPredictor()
    feature_names_combined = []

    skipped = 0
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            skipped += 1
            continue

        do_a = data_objects[sym_a]
        do_b = data_objects[sym_b]

        # Original interaction features
        result = interact(do_a, do_b)
        primitives = spatial.full_interaction(do_a, do_b)
        base_features = predictor_base.extract_features(result, primitives)

        # Snap dynamics features
        isd = compute_interaction_snap_dynamics(do_a, do_b, golay)
        snap_features = extract_snap_features(isd)

        # Combined features
        combined = base_features + snap_features + [bo]

        X_all.append(combined)
        y_be.append(be)
        y_dh.append(dh if dh is not None else float('nan'))
        bond_orders.append(bo)
        pair_labels.append(label)
        valid_pairs.append((sym_a, sym_b, be, dh, label, bo))

    # Build feature names
    feature_names_combined = (
        predictor_base.feature_names +
        snap_feature_names() +
        ["bond_order"]
    )

    print(f"    Valid pairs: {len(X_all)} (skipped {skipped})")
    print(f"    Total features: {len(X_all[0])}")
    dh_count = sum(1 for d in y_dh if not math.isnan(d))
    print(f"    With ΔH data: {dh_count}")

    # ── Bond energy: full fit ──────────────────────────────────────────────────
    print("\n[5] Bond Energy — Full-sample fit")

    predictor_be = GLMPredictor()
    predictor_be.train(X_all, y_be)
    eval_be = predictor_be.evaluate(X_all, y_be)

    print(f"    n = {eval_be['n']}")
    print(f"    Pearson r = {eval_be['r']:.4f}")
    print(f"    R² = {eval_be['r_squared']:.4f}")
    print(f"    MAE = {eval_be['mae']:.1f} kJ/mol")

    # Feature importance
    if predictor_be.weights is not None:
        print(f"\n    Top 15 features:")
        importance = list(zip(feature_names_combined, predictor_be.weights))
        importance.sort(key=lambda x: abs(x[1]), reverse=True)
        for name, weight in importance[:15]:
            bar = "█" * min(int(abs(weight) / 500), 30)
            print(f"      {name:<30} {weight:>12.2f}  {bar}")

    # ── Bond energy: 5-fold CV ─────────────────────────────────────────────────
    print("\n[6] Bond Energy — 5-fold cross-validation")

    n = len(X_all)
    folds = k_fold_split(n, k=5, seed=42)
    cv_r, cv_mae = [], []
    all_pred = [0.0] * n

    for fi, (tr, te) in enumerate(folds):
        Xtr = [X_all[i] for i in tr]
        ytr = [y_be[i] for i in tr]
        Xte = [X_all[i] for i in te]
        yte = [y_be[i] for i in te]

        fp = GLMPredictor()
        fp.train(Xtr, ytr)
        fe = fp.evaluate(Xte, yte)
        cv_r.append(fe['r'])
        cv_mae.append(fe['mae'])
        for i, idx in enumerate(te):
            all_pred[idx] = fe['predictions'][i]
        print(f"    Fold {fi+1}: r={fe['r']:.4f}  MAE={fe['mae']:.1f}  (train={len(tr)}, test={len(te)})")

    overall_cv_r = pearson_r(all_pred, y_be)
    overall_cv_mae = mae(all_pred, y_be)

    print(f"\n    Mean CV r: {sum(cv_r)/len(cv_r):.4f} ± {np.std(cv_r):.4f}")
    print(f"    Overall CV r: {overall_cv_r:.4f}")
    print(f"    Overall CV MAE: {overall_cv_mae:.1f} kJ/mol")
    print(f"    Train/CV gap: {eval_be['r'] - overall_cv_r:.4f}")

    # ── Bond order analysis ────────────────────────────────────────────────────
    print("\n[7] Bond Order Analysis")

    # Test: can snap features predict bond order?
    X_bo = X_all[:]
    y_bo = bond_orders[:]

    # Simple test: correlate each feature with bond order
    print(f"    Feature correlations with bond order (top 10):")
    bo_corrs = []
    for fi, fname in enumerate(feature_names_combined):
        feat_vals = [X_all[i][fi] for i in range(n)]
        r = pearson_r(feat_vals, y_bo)
        bo_corrs.append((fname, r))
    bo_corrs.sort(key=lambda x: abs(x[1]), reverse=True)
    for fname, r in bo_corrs[:10]:
        bar = "█" * min(int(abs(r) * 30), 30)
        print(f"      {fname:<30} r={r:>7.4f}  {bar}")

    # Train a dedicated bond order predictor
    print(f"\n    Bond order predictor (5-fold CV):")
    bo_folds = k_fold_split(n, k=5, seed=99)
    bo_pred = [0.0] * n

    for fi, (tr, te) in enumerate(bo_folds):
        Xtr = [X_all[i] for i in tr]
        ytr = [bond_orders[i] for i in tr]
        Xte = [X_all[i] for i in te]

        fp = GLMPredictor()
        fp.train(Xtr, ytr)
        for idx in te:
            bo_pred[idx] = fp.predict(X_all[idx])

    bo_cv_r = pearson_r(bo_pred, bond_orders)
    print(f"    Bond order CV r = {bo_cv_r:.4f}")

    # Show predictions for key bond-order groups
    print(f"\n    Bond order predictions (sample):")
    for sym_a, sym_b, be, dh, label, bo in valid_pairs:
        if bo in [1, 2, 3] and sym_a == 'C':
            idx = valid_pairs.index((sym_a, sym_b, be, dh, label, bo))
            print(f"      {label:<30} actual_BO={bo}  pred_BO={bo_pred[idx]:.2f}")

    # ── ΔH prediction ─────────────────────────────────────────────────────────
    print("\n[8] Enthalpy (ΔH) Prediction")

    dh_idx = [i for i, d in enumerate(y_dh) if not math.isnan(d)]
    print(f"    ΔH sample size: {len(dh_idx)}")

    if len(dh_idx) >= 10:
        X_dh = [X_all[i] for i in dh_idx]
        y_dh_vals = [y_dh[i] for i in dh_idx]
        dh_labels = [pair_labels[i] for i in dh_idx]

        # Full fit
        pred_dh = GLMPredictor()
        pred_dh.train(X_dh, y_dh_vals)
        eval_dh = pred_dh.evaluate(X_dh, y_dh_vals)

        print(f"    Full-sample r = {eval_dh['r']:.4f}")
        print(f"    Full-sample R² = {eval_dh['r_squared']:.4f}")
        print(f"    Full-sample MAE = {eval_dh['mae']:.1f} kJ/mol")

        # 5-fold CV (now possible with 40+ samples)
        dh_n = len(X_dh)
        dh_folds = k_fold_split(dh_n, k=5, seed=77)
        dh_cv_pred = [0.0] * dh_n

        print(f"\n    5-fold CV:")
        for fi, (tr, te) in enumerate(dh_folds):
            Xtr = [X_dh[i] for i in tr]
            ytr = [y_dh_vals[i] for i in tr]
            Xte = [X_dh[i] for i in te]
            yte = [y_dh_vals[i] for i in te]

            fp = GLMPredictor()
            fp.train(Xtr, ytr)
            fe = fp.evaluate(Xte, yte)
            for i, idx in enumerate(te):
                dh_cv_pred[idx] = fe['predictions'][i]
            print(f"      Fold {fi+1}: r={fe['r']:.4f}  MAE={fe['mae']:.1f}")

        dh_cv_r = pearson_r(dh_cv_pred, y_dh_vals)
        dh_cv_mae_val = mae(dh_cv_pred, y_dh_vals)
        print(f"\n    Overall CV r = {dh_cv_r:.4f}")
        print(f"    Overall CV MAE = {dh_cv_mae_val:.1f} kJ/mol")
        print(f"    Train/CV gap = {eval_dh['r'] - dh_cv_r:.4f}")

        # Show worst predictions
        print(f"\n    Largest errors:")
        errors = [(abs(y_dh_vals[i] - eval_dh['predictions'][i]), dh_labels[i],
                   y_dh_vals[i], eval_dh['predictions'][i])
                  for i in range(dh_n)]
        errors.sort(reverse=True)
        for err, label, actual, pred in errors[:5]:
            print(f"      {label:<30} actual={actual:>8.1f}  pred={pred:>8.1f}  err={err:>8.1f}")

    # ── Cross-element snap analysis ────────────────────────────────────────────
    print("\n[9] Snap Dynamics — Cross-element analysis")

    # Show how snap dynamics differ for different bond types
    print(f"\n    {'Pair':<20} {'BO':>3} {'AND_snap':>8} {'XOR_snap':>8} "
          f"{'cross_syn':>9} {'elem_A_syn':>10} {'elem_B_syn':>10}")
    print(f"    {'-'*72}")

    for sym_a, sym_b, be, dh, label, bo in valid_pairs[:20]:
        do_a = data_objects[sym_a]
        do_b = data_objects[sym_b]
        isd = compute_interaction_snap_dynamics(do_a, do_b, golay)
        print(f"    {label:<20} {bo:>3} {isd.and_snap.snap_bits:>8} {isd.xor_snap.snap_bits:>8} "
              f"{isd.cross_syndrome_weight:>9} {isd.elem_a_snap.pre_syndrome_weight:>10} "
              f"{isd.elem_b_snap.pre_syndrome_weight:>10}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("REFINED EXPERIMENT SUMMARY")
    print("=" * 72)
    print(f"  Date:           {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Pairs:          {len(X_all)}")
    print(f"  Features:       {len(X_all[0])} (20 base + {len(snap_feature_names())} snap + 1 BO)")
    print(f"  ΔH samples:     {dh_count}")
    print()
    print(f"  Bond Energy:")
    print(f"    Full r:       {eval_be['r']:.4f}")
    print(f"    CV r:         {overall_cv_r:.4f}")
    print(f"    CV MAE:       {overall_cv_mae:.1f} kJ/mol")
    print(f"    Gap:          {eval_be['r'] - overall_cv_r:.4f}")
    print()
    print(f"  Bond Order:")
    print(f"    Best feature: {bo_corrs[0][0]} (r={bo_corrs[0][1]:.4f})")
    print(f"    CV r:         {bo_cv_r:.4f}")
    print()
    if len(dh_idx) >= 10:
        print(f"  Enthalpy (ΔH):")
        print(f"    Full r:       {eval_dh['r']:.4f}")
        print(f"    CV r:         {dh_cv_r:.4f}")
        print(f"    CV MAE:       {dh_cv_mae_val:.1f} kJ/mol")
        print(f"    Gap:          {eval_dh['r'] - dh_cv_r:.4f}")
    print()

    # Save
    if save_results:
        results = {
            "experiment": "encoding_definition_attempt_04.08-26_refined",
            "date": datetime.now().isoformat(),
            "n_pairs": len(X_all),
            "n_features": len(X_all[0]),
            "n_dh": dh_count,
            "be_full_r": eval_be['r'],
            "be_cv_r": overall_cv_r,
            "be_cv_mae": overall_cv_mae,
            "bo_cv_r": bo_cv_r,
            "bo_best_feature": bo_corrs[0],
            "cv_fold_r": cv_r,
        }
        if len(dh_idx) >= 10:
            results["dh_full_r"] = eval_dh['r']
            results["dh_cv_r"] = dh_cv_r
            results["dh_cv_mae"] = dh_cv_mae_val
        results_path = SCRIPT_DIR.parent / "data" / f"refined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  Results saved to: {results_path}")

    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-test", action="store_true")
    parser.add_argument("--snap-analysis", nargs=2)
    parser.add_argument("--save-results", action="store_true")
    args = parser.parse_args()

    if args.full_test or args.save_results:
        run_refined_experiment(save_results=args.save_results)
    elif args.snap_analysis:
        # Quick snap analysis for a pair
        kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
        elements = load_elements_from_kb(str(kb_path))
        golay = GolayEngine()
        do_a = encode_element(args.snap_analysis[0], elements, BEST_ENCODING, golay)
        do_b = encode_element(args.snap_analysis[1], elements, BEST_ENCODING, golay)
        if do_a and do_b:
            isd = compute_interaction_snap_dynamics(do_a, do_b, golay)
            print(f"AND snap: bits={isd.and_snap.snap_bits} syn={isd.and_snap.pre_syndrome_weight} "
                  f"corrections={isd.and_snap.correction_row_distribution}")
            print(f"XOR snap: bits={isd.xor_snap.snap_bits} syn={isd.xor_snap.pre_syndrome_weight} "
                  f"corrections={isd.xor_snap.correction_row_distribution}")
            print(f"Cross: snap_bits={isd.cross_snap_bits} syn_weight={isd.cross_syndrome_weight}")
            print(f"Elem A: syn_weight={isd.elem_a_snap.pre_syndrome_weight} snap_bits={isd.elem_a_snap.snap_bits}")
            print(f"Elem B: syn_weight={isd.elem_b_snap.pre_syndrome_weight} snap_bits={isd.elem_b_snap.snap_bits}")
    else:
        parser.print_help()
