#!/usr/bin/env python3
"""
Experiment L — Gray-code + Golay-decode + symmetry-tax features for codeword classification.

This is the experiment that was cut off when the previous session ran out of
messages.  The idea (from chat.md): use the is_prime method's pipeline
(Gray code → Golay decode/snap → symmetry tax → NRCI → pressure) as ENGINEERED
FEATURES for the Exp H codeword classification task.

Exp H showed: MLP on raw 24-bit vectors → 56.74% test accuracy.
Exp I showed: MLP on Gray-coded 24-bit vectors → 74.18% test accuracy.
Exp J showed: GF(2) Gaussian elimination → 100% from 12 examples.

Exp L asks: can we engineer a small set of substrate-native features (NRCI,
tax, pressure, syndrome weight) that give a gradient-based learner a much
better signal than raw bits?
"""
from __future__ import annotations
import sys, os, random, time
import numpy as np
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent / "glm_work")
sys.path.insert(0, str(Path(".").resolve()))

from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from fractions import Fraction

def generate_dataset(n_per_class=500, seed=42):
    rng = random.Random(seed)
    all_codewords = GOLAY_ENGINE.get_all_codewords()
    codewords = all_codewords[:n_per_class]
    non_codewords = []
    attempts = 0
    while len(non_codewords) < n_per_class and attempts < n_per_class * 10:
        vec = [rng.randint(0, 1) for _ in range(24)]
        sw = GOLAY_ENGINE.syndrome_weight(vec)
        if sw != 0:
            non_codewords.append(vec)
        attempts += 1
    print(f"Dataset: {len(codewords)} codewords + {len(non_codewords)} non-codewords")
    return codewords, non_codewords

def compute_features(vec):
    """Compute 5 substrate-native features for a 24-bit vector."""
    # 1. syndrome weight
    sw = GOLAY_ENGINE.syndrome_weight(vec)

    # 2. snapped NRCI
    snapped, meta = GOLAY_ENGINE.snap_to_codeword(vec)
    tax = LEECH_ENGINE.calculate_symmetry_tax(snapped)
    nrci = float(Fraction(10, 1) / (Fraction(10, 1) + tax))

    # 3. pressure (max Hamming-1 neighbor NRCI - target NRCI)
    max_neighbor_nrci = 0.0
    for i in range(24):
        neighbor = list(vec)
        neighbor[i] ^= 1
        snapped_n, _ = GOLAY_ENGINE.snap_to_codeword(neighbor)
        tax_n = LEECH_ENGINE.calculate_symmetry_tax(snapped_n)
        nrci_n = float(Fraction(10, 1) / (Fraction(10, 1) + tax_n))
        if nrci_n > max_neighbor_nrci:
            max_neighbor_nrci = nrci_n
    pressure = max(0.0, max_neighbor_nrci - nrci)

    # 4 & 5: Gray-coded version
    n_val = 0
    for i, b in enumerate(vec):
        if b:
            n_val |= (1 << (23 - i))
    gray_val = n_val ^ (n_val >> 1)
    gray_vec = [(gray_val >> i) & 1 for i in range(23, -1, -1)]

    snapped_g, _ = GOLAY_ENGINE.snap_to_codeword(gray_vec)
    tax_g = LEECH_ENGINE.calculate_symmetry_tax(snapped_g)
    gray_nrci = float(Fraction(10, 1) / (Fraction(10, 1) + tax_g))

    max_neighbor_g = 0.0
    for i in range(24):
        neighbor = list(gray_vec)
        neighbor[i] ^= 1
        snapped_ng, _ = GOLAY_ENGINE.snap_to_codeword(neighbor)
        tax_ng = LEECH_ENGINE.calculate_symmetry_tax(snapped_ng)
        nrci_ng = float(Fraction(10, 1) / (Fraction(10, 1) + tax_ng))
        if nrci_ng > max_neighbor_g:
            max_neighbor_g = nrci_ng
    gray_pressure = max(0.0, max_neighbor_g - gray_nrci)

    return [sw, nrci, pressure, gray_nrci, gray_pressure]

def build_feature_matrix(codewords, non_codewords):
    X, y = [], []
    t0 = time.time()
    print("Computing features for codewords...")
    for i, vec in enumerate(codewords):
        X.append(compute_features(vec))
        y.append(1)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(codewords)} ({time.time()-t0:.1f}s)")
    print("Computing features for non-codewords...")
    for i, vec in enumerate(non_codewords):
        X.append(compute_features(vec))
        y.append(0)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(non_codewords)} ({time.time()-t0:.1f}s)")
    return np.array(X), np.array(y)

def main():
    print("=" * 80)
    print("EXPERIMENT L: Gray-code + Golay-decode + symmetry-tax features")
    print("=" * 80)

    N = 500
    codewords, non_codewords = generate_dataset(n_per_class=N)
    print()
    print("Computing engineered features...")
    X, y = build_feature_matrix(codewords, non_codewords)

    print(f"\nFeature matrix: {X.shape}")
    print("Feature statistics:")
    for i, name in enumerate(["syndrome_weight", "snapped_nrci", "pressure",
                               "gray_nrci", "gray_pressure"]):
        cw = X[y == 1, i]
        nc = X[y == 0, i]
        print(f"  {name:20s}: CW mean={cw.mean():.4f} std={cw.std():.4f} | NC mean={nc.mean():.4f} std={nc.std():.4f}")

    from sklearn.neural_network import MLPClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.5, random_state=42, stratify=y)

    mlp = MLPClassifier(hidden_layer_sizes=(64, 32), activation='relu',
                        max_iter=500, random_state=42)
    mlp.fit(X_train, y_train)
    mlp_train = mlp.score(X_train, y_train)
    mlp_test = mlp.score(X_test, y_test)

    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_train = lr.score(X_train, y_train)
    lr_test = lr.score(X_test, y_test)

    # Syndrome weight alone
    sw_acc = ((X_test[:, 0] == 0) == (y_test == 1)).mean()

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"  Exp H (MLP, 24 raw bits):            56.74% test")
    print(f"  Exp I (MLP, 24 Gray-coded bits):     74.18% test")
    print(f"  Exp J (GF(2) Gaussian elim):         100.00% test (12 examples)")
    print(f"  Exp L (MLP, 5 engineered features):  {mlp_test*100:.2f}% test (train: {mlp_train*100:.2f}%)")
    print(f"  Exp L (LogReg, 5 features):          {lr_test*100:.2f}% test (train: {lr_train*100:.2f}%)")
    print(f"  Exp L (syndrome_weight alone):       {sw_acc*100:.2f}% test")
    print()
    if sw_acc > 0.99:
        print("  NOTE: syndrome_weight=0 is a PERFECT classifier by definition")
        print("  (syndrome_weight is 0 if and only if the vector is a codeword).")
        print("  The engineered features contain this trivial signal, so the")
        print("  MLP/LogReg accuracy is dominated by it.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
