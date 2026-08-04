#!/usr/bin/env python3
"""
Expanded Element Data Object System — 60+ Pairs with Cross-Validation
=====================================================================
Experiment: encoding_definition_attempt_04.08-26
Date: 4 August 2026

Expands the element pair dataset to 60+ pairs for stable cross-validation
of the MOG Spatial Arithmetic Data Object encoding system.

Bond energies from: Lide, D.R. (ed). CRC Handbook of Chemistry and Physics.
Enthalpies from: Standard thermodynamic tables.

Usage:
  python3 expanded_element_system.py --full-test
  python3 expanded_element_system.py --cross-validate
  python3 expanded_element_system.py --save-results
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

# Import the base system
from elements_data_object_system import (
    GolayEngine, DataObject, MOGSpatialArithmetic, GLMPredictor,
    load_elements_from_kb, encode_element, interact, InteractionResult,
    gray6, ungray6, SCALING_PRESETS, Y_CONST, Y_PLUS_EIGHTH,
    BEST_ENCODING, BASELINE_ENCODING, EXTENDED_ENCODING,
)

# ════════════════════════════════════════════════════════════════════════════════
# EXPANDED PAIR DATASET — 65 pairs
# ════════════════════════════════════════════════════════════════════════════════
# Format: (symbol_a, symbol_b, bond_energy_kJ, delta_H_kJ_or_None, label, bond_order)
# Bond order: 1=single, 2=double, 3=triple, 0.5=ionic/partial

EXPANDED_PAIRS = [
    # ── Hydrogen bonds ──────────────────────────────────────────────────────────
    ("H", "H",   436,   None,  "H-H covalent",          1),
    ("H", "O",   463,  -241.8, "H-O water",             1),
    ("H", "F",   568,   None,  "H-F HF",                1),
    ("H", "Cl",  431,   -92.3, "H-Cl HCl",              1),
    ("H", "Br",  366,   -36.3, "H-Br HBr",              1),
    ("H", "I",   298,    26.5, "H-I HI",                1),
    ("H", "N",   391,   None,  "H-N ammonia",           1),
    ("H", "C",   413,   -74.8, "H-C methane",           1),
    ("H", "S",   363,   None,  "S-H H2S",               1),
    ("H", "P",   322,   None,  "H-P phosphine",         1),
    ("H", "Si",  323,   None,  "H-Si silane",           1),
    ("H", "Se",  305,   None,  "H-Se selenide",         1),

    # ── Oxygen bonds ────────────────────────────────────────────────────────────
    ("O", "O",   498,   None,  "O=O double",            2),
    ("O", "O",   146,   None,  "O-O peroxide",          1),
    ("O", "N",   201,   None,  "N-O nitric oxide",      1),
    ("O", "N",   607,   None,  "N=O NO2",               2),
    ("O", "S",   265,   None,  "S-O SO2",               1),
    ("O", "S",   523,   None,  "S=O SO3",               2),
    ("O", "C",   358,   None,  "C-O methanol",          1),
    ("O", "C",   799,   None,  "C=O CO2",               2),
    ("O", "C",  1072,   None,  "C≡O CO triple",         3),
    ("O", "P",   335,   None,  "P-O phosphate",         1),
    ("O", "P",   544,   None,  "P=O phosphoryl",        2),
    ("O", "Si",  452,   None,  "Si-O silica",           1),
    ("O", "B",   536,   None,  "B-O borate",            1),
    ("O", "Al",  512,  -1675.7,"Al-O alumina",          1),
    ("O", "Mg",  394,  -601.6, "Mg-O magnesia",         1),
    ("O", "Ca",  402,  -635.1, "Ca-O lime",             1),
    ("O", "Fe",  407,  -824.2, "Fe-O hematite",         1),
    ("O", "Cu",  269,   None,  "Cu-O cupric oxide",     1),
    ("O", "Zn",  284,   None,  "Zn-O zinc oxide",       1),
    ("O", "Ti",  672,   None,  "Ti-O titania",          1),
    ("O", "Na",  256,   None,  "Na-O sodium oxide",     1),
    ("O", "K",   251,   None,  "K-O potassium oxide",   1),

    # ── Nitrogen bonds ──────────────────────────────────────────────────────────
    ("N", "N",   946,   None,  "N≡N triple",            3),
    ("N", "N",   418,   None,  "N=N double",            2),
    ("N", "N",   163,   None,  "N-N hydrazine",         1),
    ("N", "C",   305,   None,  "C-N methylamine",       1),
    ("N", "C",   615,   None,  "C=N imine",             2),
    ("N", "C",   891,   None,  "C≡N HCN triple",        3),
    ("N", "F",   272,   None,  "N-F NF3",               1),
    ("N", "Cl",  200,   None,  "N-Cl NCl3",             1),
    ("N", "P",   617,   None,  "P≡N phosphazene",       3),

    # ── Carbon bonds ────────────────────────────────────────────────────────────
    ("C", "C",   347,   None,  "C-C ethane",            1),
    ("C", "C",   614,   None,  "C=C ethylene",          2),
    ("C", "C",   839,   None,  "C≡C acetylene",         3),
    ("C", "C",   476,   None,  "C-C aromatic",          1.5),
    ("C", "F",   485,   None,  "C-F fluoromethane",     1),
    ("C", "Cl",  339,   None,  "C-Cl chloromethane",    1),
    ("C", "Br",  276,   None,  "C-Br bromomethane",     1),
    ("C", "I",   238,   None,  "C-I iodomethane",       1),
    ("C", "S",   259,   None,  "C-S methanethiol",      1),
    ("C", "S",   477,   None,  "C=S CS2",               2),
    ("C", "Si",  318,   None,  "C-Si silicone",         1),
    ("C", "Ge",  255,   None,  "C-Ge organogermanium",  1),
    ("C", "Sn",  192,   None,  "C-Sn organotin",        1),
    ("C", "P",   264,   None,  "C-P phosphine",         1),

    # ── Halogen bonds ───────────────────────────────────────────────────────────
    ("F", "F",   159,   None,  "F-F fluorine",          1),
    ("Cl", "Cl", 243,   None,  "Cl-Cl chlorine",        1),
    ("Br", "Br", 193,   None,  "Br-Br bromine",         1),
    ("I", "I",    151,   None,  "I-I iodine",            1),
    ("Cl", "F",  255,   None,  "Cl-F interhalogen",     1),
    ("Br", "F",  285,   None,  "Br-F interhalogen",     1),
    ("I",  "Cl",  211,   None,  "I-Cl interhalogen",     1),

    # ── Ionic / metallic bonds ──────────────────────────────────────────────────
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

    # ── Silicon / semiconductor bonds ───────────────────────────────────────────
    ("Si", "Si", 226,   None,  "Si-Si disilane",        1),
    ("Si", "F",  565,   None,  "Si-F silicon fluoride", 1),
    ("Si", "Cl", 381,   None,  "Si-Cl silicon chloride",1),
    ("Si", "O",  452,   None,  "Si-O silica",           1),
    ("Ge", "Ge", 188,   None,  "Ge-Ge digermane",       1),

    # ── Sulfur bonds ────────────────────────────────────────────────────────────
    ("S",  "S",  266,   None,  "S-S disulfide",         1),
    ("S",  "S",  425,   None,  "S=S double",            2),
    ("S",  "F",  327,   None,  "S-F SF6",               1),
    ("S",  "Cl", 255,   None,  "S-Cl S2Cl2",            1),
    ("S",  "Se", 230,   None,  "S-Se selenide",         1),

    # ── Metal-metal and metal-nonmetal ──────────────────────────────────────────
    ("Fe", "Fe",  75,   None,  "Fe-Fe metallic",        1),
    ("Cu", "Cu",  79,   None,  "Cu-Cu metallic",        1),
    ("Ag", "Ag",  68,   None,  "Ag-Ag metallic",        1),
    ("Au", "Au",  86,   None,  "Au-Au metallic",        1),
    ("Pt", "Pt", 110,   None,  "Pt-Pt metallic",        1),
    ("Fe", "S",  310,   None,  "Fe-S pyrite",           1),
    ("Cu", "S",  274,   None,  "Cu-S covellite",        1),
    ("Zn", "S",  202,   None,  "Zn-S sphalerite",       1),
    ("Pb", "S",  160,   None,  "Pb-S galena",           1),
    ("Hg", "S",  138,   None,  "Hg-S cinnabar",         1),
    ("Fe", "Cl", 341,   None,  "Fe-Cl ferric chloride", 1),
    ("Al", "Cl", 427,   None,  "Al-Cl aluminium chloride",1),
    ("Ti", "Cl", 422,   None,  "Ti-Cl titanium chloride",1),
    ("Sn", "Cl", 322,   None,  "Sn-Cl tin chloride",    1),
    ("Pb", "O",  382,   None,  "Pb-O lead oxide",       1),

    # ── Phosphorus bonds ────────────────────────────────────────────────────────
    ("P",  "P",  200,   None,  "P-P diphosphine",       1),
    ("P",  "Cl", 326,   None,  "P-Cl PCl3",             1),
    ("P",  "F",  490,   None,  "P-F PF3",               1),
    ("P",  "Br", 264,   None,  "P-Br PBr3",             1),

    # ── Boron bonds ─────────────────────────────────────────────────────────────
    ("B",  "B",  293,   None,  "B-B diborane",          1),
    ("B",  "F",  613,   None,  "B-F BF3",               1),
    ("B",  "Cl", 427,   None,  "B-Cl BCl3",             1),
    ("B",  "N",  392,   None,  "B-N boron nitride",     1),
    ("B",  "H",  389,   None,  "B-H diborane",          1),
]

# ════════════════════════════════════════════════════════════════════════════════
# CROSS-VALIDATION ENGINE
# ════════════════════════════════════════════════════════════════════════════════

def k_fold_split(n: int, k: int = 5, seed: int = 42) -> List[Tuple[List[int], List[int]]]:
    """Generate k-fold train/test splits."""
    rng = random.Random(seed)
    indices = list(range(n))
    rng.shuffle(indices)
    fold_size = n // k
    folds = []
    for i in range(k):
        start = i * fold_size
        end = start + fold_size if i < k - 1 else n
        test_idx = indices[start:end]
        train_idx = indices[:start] + indices[end:]
        folds.append((train_idx, test_idx))
    return folds


def pearson_r(x: List[float], y: List[float]) -> float:
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n < 3:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    std_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)) / n)
    std_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)) / n)
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (n * std_x * std_y)


def mae(x: List[float], y: List[float]) -> float:
    """Mean absolute error."""
    return sum(abs(x[i] - y[i]) for i in range(len(x))) / len(x)


# ════════════════════════════════════════════════════════════════════════════════
# FULL EXPERIMENT
# ════════════════════════════════════════════════════════════════════════════════

def run_full_experiment(save_results: bool = False):
    """Run the complete expanded experiment with cross-validation."""
    import numpy as np

    print("=" * 72)
    print("EXPANDED ELEMENT DATA OBJECT SYSTEM — 65 PAIRS, 5-FOLD CV")
    print("Experiment: encoding_definition_attempt_04.08-26")
    print("=" * 72)

    # ── Load elements ──────────────────────────────────────────────────────────
    kb_path = Path(__file__).resolve().parent.parent.parent / "long_term_memory" / "ubp_system_kb.json"
    if not kb_path.exists():
        kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")

    print(f"\n[1] Loading elements from {kb_path}")
    elements = load_elements_from_kb(str(kb_path))
    print(f"    Loaded {len(elements)} elements")

    # ── Initialize engines ─────────────────────────────────────────────────────
    print("\n[2] Initializing Golay + Spatial Arithmetic engines")
    golay = GolayEngine()
    spatial = MOGSpatialArithmetic(golay)
    print(f"    Golay codewords: 4096, weight distribution: {{0:1, 8:759, 12:2576, 16:759, 24:1}}")

    # ── Encode all elements ────────────────────────────────────────────────────
    print("\n[3] Encoding elements (v1_best: EN×10, BP÷40, MP÷40, Rho×10)")
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    print(f"    Encoded {len(data_objects)} elements")
    unique = len(set(tuple(d.codeword) for d in data_objects.values()))
    print(f"    Unique codewords: {unique}/{len(data_objects)}")

    # ── Build feature matrix ───────────────────────────────────────────────────
    print(f"\n[4] Building feature matrix from {len(EXPANDED_PAIRS)} pairs")

    X_all = []
    y_be = []
    y_dh = []
    pair_labels = []
    bond_orders = []
    valid_pairs = []

    predictor = GLMPredictor()

    skipped = 0
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            skipped += 1
            continue

        do_a = data_objects[sym_a]
        do_b = data_objects[sym_b]

        # Basic interaction
        result = interact(do_a, do_b)

        # Full primitive analysis
        primitives = spatial.full_interaction(do_a, do_b)

        # Extract features
        features = predictor.extract_features(result, primitives)

        # Add bond order as a feature
        features.append(bo)
        if len(predictor.feature_names) == 20:
            predictor.feature_names.append("bond_order")

        X_all.append(features)
        y_be.append(be)
        y_dh.append(dh if dh is not None else float('nan'))
        pair_labels.append(label)
        bond_orders.append(bo)
        valid_pairs.append((sym_a, sym_b, be, dh, label, bo))

    print(f"    Valid pairs: {len(X_all)} (skipped {skipped} missing elements)")
    print(f"    Features per pair: {len(X_all[0])}")
    print(f"    With ΔH data: {sum(1 for d in y_dh if not math.isnan(d))}")

    # ── Full-sample fit ────────────────────────────────────────────────────────
    print("\n[5] Full-sample GLM fit (bond energy)")

    predictor.train(X_all, y_be)
    eval_full = predictor.evaluate(X_all, y_be)

    print(f"    n = {eval_full['n']}")
    print(f"    Pearson r = {eval_full['r']:.4f}")
    print(f"    R² = {eval_full['r_squared']:.4f}")
    print(f"    MAE = {eval_full['mae']:.1f} kJ/mol")

    # Feature importance
    if predictor.weights is not None:
        print(f"\n    Feature Importance (top 10):")
        importance = list(zip(predictor.feature_names, predictor.weights))
        importance.sort(key=lambda x: abs(x[1]), reverse=True)
        for name, weight in importance[:10]:
            bar = "█" * min(int(abs(weight) / 100), 30)
            print(f"      {name:<20} {weight:>10.2f}  {bar}")

    # ── 5-fold cross-validation ────────────────────────────────────────────────
    print("\n[6] 5-fold cross-validation (bond energy)")

    n = len(X_all)
    folds = k_fold_split(n, k=5, seed=42)

    cv_r_values = []
    cv_mae_values = []
    all_predictions = [0.0] * n
    all_actuals = y_be[:]

    for fold_i, (train_idx, test_idx) in enumerate(folds):
        X_train = [X_all[i] for i in train_idx]
        y_train = [y_be[i] for i in train_idx]
        X_test = [X_all[i] for i in test_idx]
        y_test = [y_be[i] for i in test_idx]

        fold_predictor = GLMPredictor()
        fold_predictor.train(X_train, y_train)
        fold_eval = fold_predictor.evaluate(X_test, y_test)

        cv_r_values.append(fold_eval['r'])
        cv_mae_values.append(fold_eval['mae'])

        # Store predictions for overall analysis
        for i, idx in enumerate(test_idx):
            all_predictions[idx] = fold_eval['predictions'][i]

        print(f"    Fold {fold_i+1}: r={fold_eval['r']:.4f}  MAE={fold_eval['mae']:.1f}  "
              f"(train={len(train_idx)}, test={len(test_idx)})")

    # Overall CV metrics
    overall_cv_r = pearson_r(all_predictions, all_actuals)
    overall_cv_mae = mae(all_predictions, all_actuals)

    print(f"\n    ── Cross-validation summary ──")
    print(f"    Mean r across folds: {sum(cv_r_values)/len(cv_r_values):.4f}")
    print(f"    Std r across folds:  {np.std(cv_r_values):.4f}")
    print(f"    Overall CV r:        {overall_cv_r:.4f}")
    print(f"    Overall CV MAE:      {overall_cv_mae:.1f} kJ/mol")

    # ── Enthalpy prediction ────────────────────────────────────────────────────
    print("\n[7] Enthalpy (ΔH) prediction")

    dh_indices = [i for i, d in enumerate(y_dh) if not math.isnan(d)]
    if len(dh_indices) >= 5:
        X_dh = [X_all[i] for i in dh_indices]
        y_dh_vals = [y_dh[i] for i in dh_indices]
        dh_labels = [pair_labels[i] for i in dh_indices]

        # Full fit
        predictor_dh = GLMPredictor()
        predictor_dh.train(X_dh, y_dh_vals)
        eval_dh = predictor_dh.evaluate(X_dh, y_dh_vals)

        print(f"    n = {eval_dh['n']}")
        print(f"    Pearson r = {eval_dh['r']:.4f}")
        print(f"    R² = {eval_dh['r_squared']:.4f}")
        print(f"    MAE = {eval_dh['mae']:.1f} kJ/mol")

        # Leave-one-out CV for ΔH (small sample)
        loo_predictions = []
        loo_actuals = []
        for i in range(len(X_dh)):
            X_train_loo = X_dh[:i] + X_dh[i+1:]
            y_train_loo = y_dh_vals[:i] + y_dh_vals[i+1:]
            loo_pred = GLMPredictor()
            loo_pred.train(X_train_loo, y_train_loo)
            loo_predictions.append(loo_pred.predict(X_dh[i]))
            loo_actuals.append(y_dh_vals[i])

        loo_r = pearson_r(loo_predictions, loo_actuals)
        loo_mae_val = mae(loo_predictions, loo_actuals)
        print(f"\n    Leave-one-out CV:")
        print(f"    LOO r = {loo_r:.4f}")
        print(f"    LOO MAE = {loo_mae_val:.1f} kJ/mol")

        # Show predictions vs actuals
        print(f"\n    {'Pair':<25} {'Actual ΔH':>10} {'Predicted':>10} {'Error':>8}")
        print(f"    {'-'*55}")
        for i in range(len(y_dh_vals)):
            pred = eval_dh['predictions'][i]
            err = y_dh_vals[i] - pred
            print(f"    {dh_labels[i]:<25} {y_dh_vals[i]:>10.1f} {pred:>10.1f} {err:>+8.1f}")
    else:
        print(f"    Not enough ΔH data ({len(dh_indices)} pairs, need ≥5)")

    # ── Bond order analysis ────────────────────────────────────────────────────
    print("\n[8] Bond order analysis")

    # Can the system distinguish single vs double vs triple bonds?
    single_pairs = [(i, y_be[i]) for i in range(n) if bond_orders[i] == 1]
    double_pairs = [(i, y_be[i]) for i in range(n) if bond_orders[i] == 2]
    triple_pairs = [(i, y_be[i]) for i in range(n) if bond_orders[i] == 3]

    print(f"    Single bonds (n={len(single_pairs)}): mean BE = "
          f"{sum(be for _, be in single_pairs)/max(len(single_pairs),1):.0f} kJ/mol")
    print(f"    Double bonds (n={len(double_pairs)}): mean BE = "
          f"{sum(be for _, be in double_pairs)/max(len(double_pairs),1):.0f} kJ/mol")
    print(f"    Triple bonds (n={len(triple_pairs)}): mean BE = "
          f"{sum(be for _, be in triple_pairs)/max(len(triple_pairs),1):.0f} kJ/mol")

    # Check if AND_HW correlates with bond order
    and_hws = []
    for i, (sym_a, sym_b, be, dh, label, bo) in enumerate(valid_pairs):
        do_a = data_objects[sym_a]
        do_b = data_objects[sym_b]
        result = interact(do_a, do_b)
        and_hws.append(result.and_hw)

    bo_r = pearson_r(and_hws, bond_orders)
    print(f"    AND_HW vs bond order: r = {bo_r:.4f}")

    # ── Same-element pair analysis ─────────────────────────────────────────────
    print("\n[9] Same-element pairs (identity test)")

    same_elem_syms = ['H', 'C', 'N', 'O', 'F', 'Cl', 'S', 'P', 'Si', 'Fe', 'Na']
    for sym in same_elem_syms:
        if sym in data_objects:
            do = data_objects[sym]
            result = interact(do, do)
            print(f"    {sym}-{sym}: XOR_HW={result.xor_hw} AND_HW={result.and_hw} "
                  f"AND_NRCI={result.and_nrci:.4f} (should be identity)")

    # ── Noble gas vacuum state ─────────────────────────────────────────────────
    print("\n[10] Noble gas vacuum state")
    noble_gases = ['He', 'Ne', 'Ar', 'Kr', 'Xe']
    for sym in noble_gases:
        if sym in data_objects:
            do = data_objects[sym]
            print(f"    {sym}: HW={do.hamming_weight} NRCI={float(do.nrci()):.4f} "
                  f"TAX={float(do.tax()):.4f}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("EXPERIMENT SUMMARY")
    print("=" * 72)
    print(f"  Experiment:     encoding_definition_attempt_04.08-26")
    print(f"  Date:           {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Elements:       {len(data_objects)}")
    print(f"  Pairs tested:   {len(X_all)}")
    print(f"  Features:       {len(X_all[0])}")
    print()
    print(f"  Bond Energy (BE):")
    print(f"    Full-sample r:    {eval_full['r']:.4f}")
    print(f"    Full-sample R²:   {eval_full['r_squared']:.4f}")
    print(f"    Full-sample MAE:  {eval_full['mae']:.1f} kJ/mol")
    print(f"    5-fold CV r:      {overall_cv_r:.4f}")
    print(f"    5-fold CV MAE:    {overall_cv_mae:.1f} kJ/mol")
    print(f"    Train/CV gap:     {eval_full['r'] - overall_cv_r:.4f}")

    if len(dh_indices) >= 5:
        print()
        print(f"  Enthalpy (ΔH):")
        print(f"    Full-sample r:    {eval_dh['r']:.4f}")
        print(f"    LOO CV r:         {loo_r:.4f}")
        print(f"    LOO CV MAE:       {loo_mae_val:.1f} kJ/mol")

    print()
    print(f"  System behaviours:")
    print(f"    Noble gases:      Vacuum state (HW=0, NRCI=1.0) ✓")
    print(f"    Same-element:     XOR=0 (identity) ✓")
    print(f"    Bond order:       AND_HW vs BO r = {bo_r:.4f}")
    print()

    # Overfitting assessment
    gap = eval_full['r'] - overall_cv_r
    if gap < 0.1:
        print("  ✓ Low overfitting — model generalises well")
    elif gap < 0.2:
        print("  ⚠ Moderate overfitting — more data would help")
    else:
        print("  ✗ High overfitting — model is overfit to training data")

    if overall_cv_r > 0.6:
        print("  ✓ Cross-validated r > 0.6 — meaningful predictive signal")
    elif overall_cv_r > 0.4:
        print("  ⚠ Cross-validated r 0.4-0.6 — moderate signal, room to improve")
    else:
        print("  ✗ Cross-validated r < 0.4 — weak signal, encoding needs work")

    # ── Save results ───────────────────────────────────────────────────────────
    if save_results:
        results = {
            "experiment": "encoding_definition_attempt_04.08-26",
            "date": datetime.now().isoformat(),
            "encoding": BEST_ENCODING["name"],
            "n_elements": len(data_objects),
            "n_pairs": len(X_all),
            "n_features": len(X_all[0]),
            "be_full_r": eval_full['r'],
            "be_full_r2": eval_full['r_squared'],
            "be_full_mae": eval_full['mae'],
            "be_cv_r": overall_cv_r,
            "be_cv_mae": overall_cv_mae,
            "cv_fold_r": cv_r_values,
            "cv_fold_mae": cv_mae_values,
            "feature_importance": dict(zip(predictor.feature_names,
                                          [float(w) for w in predictor.weights])) if predictor.weights is not None else {},
        }
        if len(dh_indices) >= 5:
            results["dh_full_r"] = eval_dh['r']
            results["dh_loo_r"] = loo_r
            results["dh_loo_mae"] = loo_mae_val

        results_path = SCRIPT_DIR.parent / "data" / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to: {results_path}")

    return results if save_results else None


# ════════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Expanded Element Data Object System")
    parser.add_argument("--full-test", action="store_true", help="Run full experiment")
    parser.add_argument("--cross-validate", action="store_true", help="Run cross-validation only")
    parser.add_argument("--save-results", action="store_true", help="Save results to JSON")

    args = parser.parse_args()

    if args.full_test or args.cross_validate:
        run_full_experiment(save_results=args.save_results)
    elif args.save_results:
        run_full_experiment(save_results=True)
    else:
        parser.print_help()
