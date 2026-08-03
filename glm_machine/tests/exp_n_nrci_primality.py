#!/usr/bin/env python3
"""
Experiment N — Do NRCI/pressure features carry primality signal?

Exp L showed syndrome_weight perfectly classifies codewords (trivially — it
IS the membership function).  But the is_prime method uses NRCI and pressure
for PRIMALITY, where syndrome_weight isn't the answer.

This experiment tests: can NRCI/pressure distinguish primes from composites?
If yes, the is_prime pipeline has real signal beyond syndrome_weight.

Method:
  1. Sample N primes and N composites in range [100, 10000].
  2. For each, compute: syndrome_weight, nrci, pressure, gray_nrci, gray_pressure
     (the is_prime pipeline).
  3. Train MLP + LogReg on these 5 features.
  4. Compare against: syndrome_weight alone, frequency baseline.

If NRCI/pressure add discriminative power beyond syndrome_weight, the is_prime
method's substrate-native features carry real primality signal.
"""
from __future__ import annotations
import sys, os, math, random
from pathlib import Path
import numpy as np

os.chdir(Path(__file__).resolve().parent.parent / "glm_work")
sys.path.insert(0, str(Path(".").resolve()))

from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from fractions import Fraction

def is_prime_classical(n):
    """Classical primality test (ground truth)."""
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0: return False
    for d in range(3, math.isqrt(n) + 1, 2):
        if n % d == 0: return False
    return True

def compute_is_prime_features(n):
    """Compute the is_prime pipeline features for integer n."""
    n_val = abs(int(n))

    # Gray code the integer
    v_target = [(n_val ^ (n_val >> 1) >> i) & 1 for i in range(23, -1, -1)]
    decoded, _, _ = GOLAY_ENGINE.decode(v_target)
    snapped = GOLAY_ENGINE.encode(decoded)
    sw = GOLAY_ENGINE.syndrome_weight(v_target)
    tax = LEECH_ENGINE.calculate_symmetry_tax(snapped)
    nrci = float(Fraction(10, 1) / (Fraction(10, 1) + tax))

    # Neighbor pressure
    max_neighbor_nrci = Fraction(0)
    for offset in (-1, 1):
        nv = n_val + offset
        v_neigh = [(nv ^ (nv >> 1) >> i) & 1 for i in range(23, -1, -1)]
        dec_n, _, _ = GOLAY_ENGINE.decode(v_neigh)
        snap_n = GOLAY_ENGINE.encode(dec_n)
        tax_n = LEECH_ENGINE.calculate_symmetry_tax(snap_n)
        nrci_n = Fraction(10, 1) / (Fraction(10, 1) + tax_n)
        if nrci_n > max_neighbor_nrci:
            max_neighbor_nrci = nrci_n
    pressure = float(max(Fraction(0), max_neighbor_nrci - Fraction(10, 1) / (Fraction(10, 1) + tax)))

    # Gray-coded version (the is_prime method already uses Gray code, so this
    # is the same as the above; but we also compute the "raw" version for comparison)
    # Raw (non-Gray) version: use the binary representation directly
    v_raw = [(n_val >> i) & 1 for i in range(23, -1, -1)]
    decoded_r, _, _ = GOLAY_ENGINE.decode(v_raw)
    snapped_r = GOLAY_ENGINE.encode(decoded_r)
    sw_r = GOLAY_ENGINE.syndrome_weight(v_raw)
    tax_r = LEECH_ENGINE.calculate_symmetry_tax(snapped_r)
    nrci_r = float(Fraction(10, 1) / (Fraction(10, 1) + tax_r))

    max_neighbor_r = Fraction(0)
    for offset in (-1, 1):
        nv = n_val + offset
        v_neigh = [(nv >> i) & 1 for i in range(23, -1, -1)]
        dec_n, _, _ = GOLAY_ENGINE.decode(v_neigh)
        snap_n = GOLAY_ENGINE.encode(dec_n)
        tax_n = LEECH_ENGINE.calculate_symmetry_tax(snap_n)
        nrci_n = Fraction(10, 1) / (Fraction(10, 1) + tax_n)
        if nrci_n > max_neighbor_r:
            max_neighbor_r = nrci_n
    pressure_r = float(max(Fraction(0), max_neighbor_r - Fraction(10, 1) / (Fraction(10, 1) + tax_r)))

    return [sw, nrci, pressure, sw_r, nrci_r, pressure_r]

def main():
    print("=" * 80)
    print("EXPERIMENT N: Do NRCI/pressure features carry primality signal?")
    print("=" * 80)

    # Generate dataset
    print("\nGenerating dataset (primes + composites in [100, 10000])...")
    rng = random.Random(42)
    primes = []
    composites = []
    for n in range(100, 10001):
        if is_prime_classical(n):
            primes.append(n)
        else:
            composites.append(n)

    # Sample
    N = 1000
    sample_primes = rng.sample(primes, min(N, len(primes)))
    sample_composites = rng.sample(composites, min(N, len(composites)))
    print(f"  Primes: {len(sample_primes)}, Composites: {len(sample_composites)}")

    # Compute features
    print("\nComputing is_prime pipeline features...")
    import time
    t0 = time.time()

    X = []
    y = []
    for n in sample_primes:
        X.append(compute_is_prime_features(n))
        y.append(1)
    for n in sample_composites:
        X.append(compute_is_prime_features(n))
        y.append(0)

    X = np.array(X)
    y = np.array(y)
    print(f"  Features computed in {time.time()-t0:.1f}s")
    print(f"  Feature matrix: {X.shape}")

    # Feature statistics
    feature_names = ["sw_gray", "nrci_gray", "pressure_gray",
                     "sw_raw", "nrci_raw", "pressure_raw"]
    print("\nFeature statistics (prime vs composite):")
    print(f"  {'Feature':<20} {'Prime mean':>12} {'Composite mean':>14} {'Diff':>10}")
    for i, name in enumerate(feature_names):
        p_vals = X[y == 1, i]
        c_vals = X[y == 0, i]
        print(f"  {name:<20} {p_vals.mean():>12.4f} {c_vals.mean():>14.4f} {p_vals.mean()-c_vals.mean():>10.4f}")

    # Train/test split
    from sklearn.neural_network import MLPClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.5, random_state=42, stratify=y)

    # MLP on all 6 features
    print("\n--- MLP (6 features) ---")
    mlp = MLPClassifier(hidden_layer_sizes=(64, 32), activation='relu',
                        max_iter=500, random_state=42)
    mlp.fit(X_train, y_train)
    mlp_train = mlp.score(X_train, y_train)
    mlp_test = mlp.score(X_test, y_test)
    print(f"  Train: {mlp_train:.4f}, Test: {mlp_test:.4f}")

    # LogReg on all 6 features
    print("\n--- LogReg (6 features) ---")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_train = lr.score(X_train, y_train)
    lr_test = lr.score(X_test, y_test)
    print(f"  Train: {lr_train:.4f}, Test: {lr_test:.4f}")

    # Individual feature accuracies (threshold-based)
    print("\n--- Individual feature discrimination ---")
    for i, name in enumerate(feature_names):
        # Find best threshold
        vals = X[:, i]
        best_acc = 0
        for t in np.linspace(vals.min(), vals.max(), 100):
            pred = (vals > t).astype(int)
            acc = (pred == y).mean()
            if acc > best_acc:
                best_acc = acc
        # Also try < threshold
        for t in np.linspace(vals.min(), vals.max(), 100):
            pred = (vals < t).astype(int)
            acc = (pred == y).mean()
            if acc > best_acc:
                best_acc = acc
        print(f"  {name:<20}: best single-feature accuracy = {best_acc:.4f}")

    # The is_prime method's actual rule: pressure > 0 AND trial division
    print("\n--- is_prime method's actual rule (pressure_gray > 0) ---")
    pressure_pred = (X[:, 2] > 0).astype(int)
    pressure_acc = (pressure_pred == y).mean()
    print(f"  Accuracy of 'pressure_gray > 0': {pressure_acc:.4f}")

    # Frequency baseline (predict majority class)
    majority = 1 if y.mean() > 0.5 else 0
    freq_base = (y == majority).mean()
    print(f"  Majority-class baseline: {freq_base:.4f}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Majority-class baseline:       {freq_base*100:.2f}%")
    print(f"  MLP (6 is_prime features):     {mlp_test*100:.2f}% test")
    print(f"  LogReg (6 is_prime features):  {lr_test*100:.2f}% test")
    print(f"  is_prime rule (pressure > 0):  {pressure_acc*100:.2f}%")

    if mlp_test > freq_base + 0.05:
        print("\n  ✅ NRCI/pressure features carry real primality signal")
        print("  (MLP significantly beats majority baseline)")
    elif mlp_test > freq_base:
        print("\n  ⚠️ Weak signal — MLP slightly beats baseline but not strongly")
    else:
        print("\n  ❌ No primality signal in NRCI/pressure features")

    return 0

if __name__ == "__main__":
    sys.exit(main())