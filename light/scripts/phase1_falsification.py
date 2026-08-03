"""
Phase 1 — Falsification suite for UBP-c claim.

Sub-phases:
  1A. Enumerate the exact UBP search space (search_macro_c.py equivalent),
      count hits at multiple error thresholds, return top-N formulas.
  1B. Random-transcendentals null model: pick K random sets of transcendental
      constants, run the same exponent search, count how often a <= 0.0027%
      match to c appears by chance.
  1C. Permutation null: keep UBP constants fixed; permute which exponent
      goes to which variable; count matches.
  1D. Information theory / MDL: bits to specify the UBP formula vs. bits to
      specify c directly. Fisher exact test, bootstrap CIs.

All results written to /home/z/my-project/work/phase1_results.json.
"""
from __future__ import annotations
import json
import itertools
import time
import math
import random
from fractions import Fraction as F
from typing import Any

import numpy as np

from ubp_constants import (
    PI, PHI, E, Y_INV, Y, MONAD, WOBBLE, L, U_E, SIGMA,
    C_SI, C_DERIVED_UBP,
)

OUT_PATH = "/home/z/my-project/work/phase1_results.json"
UBP_ERROR = abs(float(C_DERIVED_UBP) - float(C_SI)) / float(C_SI)  # ≈ 2.685e-05

# ─────────────────────────────────────────────────────────────────────────────
# Search space definition (mirrors search_macro_c.py exactly)
# ─────────────────────────────────────────────────────────────────────────────
UBP_VAR_NAMES = ["U_E", "MONAD", "Y", "L", "SIGMA"]
UBP_VAR_VALS  = [float(U_E), float(MONAD), float(Y), float(L), float(SIGMA)]
UBP_VAR_LOGS  = np.log(UBP_VAR_VALS)

EXP_RANGE_MACRO = list(range(-5, 6))           # 11 values, matches search_macro_c
COEFFS_MACRO    = [1.0, 2.0, 0.5, 4.0, 0.25, 8.0, 13.0, 24.0, 10.0, 100.0]
COEFF_NAMES     = ["1", "2", "1/2", "4", "1/4", "8", "13", "24", "10", "100"]
COEFF_LOGS      = np.log(COEFFS_MACRO)

TARGET = float(C_SI)                            # 299792458.0
LOG_TARGET = math.log(TARGET)

# Error thresholds to scan (relative)
THRESHOLDS = [1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7, UBP_ERROR * 1.0001]
THRESHOLD_NAMES = ["1%", "0.1%", "0.01%", "0.001%", "0.0001%", "0.00001%", "UBP-c (2.685e-5)"]


def enumerate_search_space(var_logs: np.ndarray, exp_range: list[int],
                            coeff_logs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Enumerate the full combinatorial search space.

    Returns:
      log_values: shape (N_exp_tuples, N_coeffs) — log of the formula value for each
                  (exponent-tuple, coefficient) pair.
      exp_tuples: shape (N_exp_tuples, n_vars) — the exponent tuples as int array.

    Given N vars with |exp_range| values each, and C coefficients:
      N_exp_tuples = |exp_range|^n_vars
      total combinations = N_exp_tuples * C
    """
    exp_tuples = np.array(list(itertools.product(exp_range, repeat=len(var_logs))),
                          dtype=np.int8)
    log_per_tuple = exp_tuples.astype(np.float64) @ var_logs   # shape (N_exp_tuples,)
    log_all = log_per_tuple[:, None] + coeff_logs[None, :]     # shape (N_exp_tuples, C)
    return log_all, exp_tuples


def hits_at_thresholds(log_values: np.ndarray, thresholds: list[float],
                        target: float = TARGET) -> dict[str, int]:
    """Count hits at each relative-error threshold."""
    log_target = math.log(target)
    # |log(value) - log(target)| ≈ |value - target| / target  for small errors
    # For large errors, fall back to direct comparison.
    values = np.exp(log_values)
    rel_err = np.abs(values - target) / target
    out = {}
    for thresh, name in zip(thresholds, THRESHOLD_NAMES):
        out[name] = int(np.sum(rel_err < thresh))
    out["_total_combinations"] = int(rel_err.size)
    return out


def top_n_formulas(log_values: np.ndarray, exp_tuples: np.ndarray,
                    var_names: list[str], coeff_names: list[str],
                    target: float = TARGET, n: int = 20) -> list[dict]:
    """Return the n closest formulas to target."""
    values = np.exp(log_values)
    rel_err = np.abs(values - target) / target
    n_tuples, n_coeffs = rel_err.shape
    flat = rel_err.flatten()
    # Get the indices of the n smallest errors
    n = min(n, flat.size)
    candidate_idx = np.argpartition(flat, n-1)[:n]
    candidate_idx = candidate_idx[np.argsort(flat[candidate_idx])]
    rows = []
    for idx in candidate_idx:
        idx = int(idx)
        i, j = divmod(idx, n_coeffs)
        exps = exp_tuples[i].tolist()
        terms = []
        if coeff_names[j] != "1":
            terms.append(coeff_names[j])
        for name, e in zip(var_names, exps):
            if e == 0: continue
            terms.append(name if e == 1 else f"{name}^{e}")
        expr = " * ".join(terms) if terms else "1"
        rows.append({
            "expr": expr,
            "value": float(values[i, j]),
            "rel_err": float(rel_err[i, j]),
            "rel_err_pct": float(rel_err[i, j] * 100),
            "exponents": exps,
            "coeff": coeff_names[j],
        })
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1A — Full enumeration of UBP search space
# ─────────────────────────────────────────────────────────────────────────────
def phase1a() -> dict[str, Any]:
    print("[1A] Enumerating UBP search space (search_macro_c equivalent)...")
    t0 = time.time()
    log_vals, exp_tuples = enumerate_search_space(UBP_VAR_LOGS, EXP_RANGE_MACRO, COEFF_LOGS)
    elapsed = time.time() - t0
    print(f"     {log_vals.size:,} combinations enumerated in {elapsed:.2f}s")

    hits = hits_at_thresholds(log_vals, THRESHOLDS)
    for name, count in hits.items():
        if name == "_total_combinations": continue
        print(f"     Threshold {name:<20}: {count:>6} hits ({count/hits['_total_combinations']*100:.5f}%)")

    top = top_n_formulas(log_vals, exp_tuples, UBP_VAR_NAMES, COEFF_NAMES, n=20)
    print(f"\n     Top 5 formulas by relative error:")
    for i, r in enumerate(top[:5]):
        print(f"       {i+1}. {r['expr']:<45} = {r['value']:>15.2f}  err={r['rel_err_pct']:.7f}%")

    # Verify user's formula is in the search space
    user_exps = [1, 2, -3, 1, 5]  # U_E^1, MONAD^2, Y^-3, L^1, SIGMA^5
    user_coeff_idx = COEFF_NAMES.index("13")
    # Find the exponent tuple
    match_mask = np.all(exp_tuples == np.array(user_exps, dtype=np.int8), axis=1)
    match_idx = np.where(match_mask)[0]
    if len(match_idx) == 1:
        i = match_idx[0]
        user_val = float(np.exp(log_vals[i, user_coeff_idx]))
        user_err = abs(user_val - TARGET) / TARGET
        print(f"\n     [VERIFIED] User's formula found in search space:")
        print(f"                expr = 13 * U_E * MONAD^2 * Y^-3 * L * SIGMA^5")
        print(f"                value = {user_val:,.6f}, err = {user_err*100:.7f}%")
        user_rank = int(np.sum(np.abs(np.exp(log_vals) - TARGET)/TARGET < user_err)) - 1
        print(f"                rank by error: #{user_rank} of {log_vals.size:,}")
    else:
        print(f"\n     [WARNING] User's exponent tuple not found in search space.")
        user_rank = None

    return {
        "search_space_size": int(log_vals.size),
        "n_vars": len(UBP_VAR_NAMES),
        "exp_range": EXP_RANGE_MACRO,
        "n_coeffs": len(COEFFS_MACRO),
        "elapsed_sec": elapsed,
        "hits_at_thresholds": hits,
        "top_20_formulas": top,
        "user_formula": {
            "expr": "13 * U_E * MONAD^2 * Y^-3 * L * SIGMA^5",
            "exponents": user_exps,
            "coeff": "13",
            "value": float(C_DERIVED_UBP),
            "rel_err": float(UBP_ERROR),
            "rel_err_pct": float(UBP_ERROR * 100),
            "rank_by_error": user_rank,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1B — Random-transcendentals null model
# ─────────────────────────────────────────────────────────────────────────────
# Pool of "natural" transcendental / irrational constants
TRANSCENDENTAL_POOL = {
    "pi":     math.pi,
    "e":      math.e,
    "phi":    (1 + math.sqrt(5)) / 2,
    "sqrt2":  math.sqrt(2),
    "sqrt3":  math.sqrt(3),
    "sqrt5":  math.sqrt(5),
    "sqrt7":  math.sqrt(7),
    "ln2":    math.log(2),
    "ln3":    math.log(3),
    "ln5":    math.log(5),
    "ln10":   math.log(10),
    "zeta3":  1.2020569031595942,           # Apery's constant
    "euler":  0.5772156649015329,           # Euler-Mascheroni
    "catalan":0.9159655941772190,           # Catalan's constant
    "khinchin":2.6854520010653065,          # Khinchin's constant
    "glaisher":1.2824271291006226,          # Glaisher-Kinkelin
    "feigenbaum_delta": 4.6692016091029909,
    "feigenbaum_alpha": 2.5029078750958928,
    "e_pi":   math.e ** math.pi,            # Gelfond's constant
    "pi_e":   math.pi ** math.e,
    "e_e":    math.e ** math.e,
    "pi_pi":  math.pi ** math.pi,
    "ln_pi":  math.log(math.pi),
    "sqrt_pi":math.sqrt(math.pi),
    "2_sqrt_pi": 2 / math.sqrt(math.pi),
    "golden_squared": ((1 + math.sqrt(5)) / 2) ** 2,
    "e_squared": math.e ** 2,
    "pi_squared": math.pi ** 2,
    "zeta2":  math.pi ** 2 / 6,             # Basel problem
    "zeta4":  math.pi ** 4 / 90,
}

def phase1b(n_trials: int = 200, seed: int = 42) -> dict[str, Any]:
    """
    Random-transcendentals null model.

    For each trial:
      - Sample 5 distinct constants from TRANSCENDENTAL_POOL
      - Run the same exponent search as Phase 1A
      - Find the best (minimum) relative error
      - Count hits at UBP_ERROR threshold

    Returns the distribution of best-errors across trials. The p-value for the
    UBP-c match is the fraction of trials whose best error <= UBP_ERROR.
    """
    print(f"\n[1B] Random-transcendentals null model ({n_trials} trials)...")
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    pool_names = list(TRANSCENDENTAL_POOL.keys())
    pool_vals  = np.array([TRANSCENDENTAL_POOL[n] for n in pool_names])

    best_errors = []
    hits_at_ubp_threshold = 0
    hits_at_1pct = 0
    hits_at_01pct = 0
    hits_at_001pct = 0
    trial_details = []

    t0 = time.time()
    for trial_i in range(n_trials):
        # Sample 5 distinct constants
        chosen_idx = rng.sample(range(len(pool_names)), 5)
        chosen_names = [pool_names[i] for i in chosen_idx]
        chosen_vals = np.array([pool_vals[i] for i in chosen_idx])
        chosen_logs = np.log(chosen_vals)

        # Run the search
        log_vals, exp_tuples = enumerate_search_space(chosen_logs, EXP_RANGE_MACRO, COEFF_LOGS)
        values = np.exp(log_vals)
        rel_err = np.abs(values - TARGET) / TARGET
        best_err = float(rel_err.min())
        best_errors.append(best_err)

        if best_err < UBP_ERROR * 1.0001:
            hits_at_ubp_threshold += 1
        if best_err < 1e-2: hits_at_1pct += 1
        if best_err < 1e-3: hits_at_01pct += 1
        if best_err < 1e-4: hits_at_001pct += 1

        if trial_i < 5 or best_err < UBP_ERROR * 1.0001:
            best_flat = int(np.argmin(rel_err))
            i, j = divmod(best_flat, len(COEFFS_MACRO))
            exps = exp_tuples[i].tolist()
            terms = []
            if COEFF_NAMES[j] != "1": terms.append(COEFF_NAMES[j])
            for name, e in zip(chosen_names, exps):
                if e == 0: continue
                terms.append(name if e == 1 else f"{name}^{e}")
            expr = " * ".join(terms)
            trial_details.append({
                "trial": trial_i,
                "constants": chosen_names,
                "best_err": best_err,
                "expr": expr,
                "value": float(values[i, j]),
            })

        if (trial_i + 1) % 20 == 0:
            elapsed = time.time() - t0
            print(f"     {trial_i+1}/{n_trials} trials done ({elapsed:.1f}s), "
                  f"hits at UBP threshold so far: {hits_at_ubp_threshold}")

    elapsed = time.time() - t0
    best_errors = np.array(best_errors)

    # Bootstrap 95% CI for the false-positive rate
    n_boot = 10000
    boot_fps = []
    for _ in range(n_boot):
        sample = np_rng.choice(best_errors, size=len(best_errors), replace=True)
        boot_fps.append(np.mean(sample < UBP_ERROR * 1.0001))
    boot_fps = np.array(boot_fps)

    p_value = hits_at_ubp_threshold / n_trials

    print(f"\n     Results over {n_trials} random-transcendental trials:")
    print(f"       Best error distribution:")
    print(f"         min:    {best_errors.min():.3e}")
    print(f"         median: {np.median(best_errors):.3e}")
    print(f"         mean:   {best_errors.mean():.3e}")
    print(f"         max:    {best_errors.max():.3e}")
    print(f"       Hits at thresholds:")
    print(f"         < 1%:        {hits_at_1pct}/{n_trials} ({hits_at_1pct/n_trials*100:.1f}%)")
    print(f"         < 0.1%:      {hits_at_01pct}/{n_trials} ({hits_at_01pct/n_trials*100:.1f}%)")
    print(f"         < 0.01%:     {hits_at_001pct}/{n_trials} ({hits_at_001pct/n_trials*100:.1f}%)")
    print(f"         < UBP-c ({UBP_ERROR:.3e}): {hits_at_ubp_threshold}/{n_trials} "
          f"({hits_at_ubp_threshold/n_trials*100:.2f}%)")
    print(f"       Empirical p-value for UBP-c match: {p_value:.4f}")
    print(f"       Bootstrap 95% CI on p-value: [{np.percentile(boot_fps, 2.5):.4f}, "
          f"{np.percentile(boot_fps, 97.5):.4f}]")
    print(f"       Elapsed: {elapsed:.1f}s")

    return {
        "n_trials": n_trials,
        "seed": seed,
        "pool_size": len(pool_names),
        "pool_names": pool_names,
        "elapsed_sec": elapsed,
        "best_error_distribution": {
            "min":    float(best_errors.min()),
            "p05":    float(np.percentile(best_errors, 5)),
            "p25":    float(np.percentile(best_errors, 25)),
            "median": float(np.median(best_errors)),
            "p75":    float(np.percentile(best_errors, 75)),
            "p95":    float(np.percentile(best_errors, 95)),
            "max":    float(best_errors.max()),
            "mean":   float(best_errors.mean()),
            "std":    float(best_errors.std()),
        },
        "hits_at_thresholds": {
            "lt_1pct":      hits_at_1pct,
            "lt_0.1pct":    hits_at_01pct,
            "lt_0.01pct":   hits_at_001pct,
            "lt_ubp_error": hits_at_ubp_threshold,
        },
        "p_value_ubp_match": p_value,
        "bootstrap_ci_95": {
            "low":  float(np.percentile(boot_fps, 2.5)),
            "high": float(np.percentile(boot_fps, 97.5)),
            "n_bootstrap": n_boot,
        },
        "best_5_trials": sorted(trial_details, key=lambda x: x["best_err"])[:5],
        "all_best_errors": best_errors.tolist(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1C — Permutation null model
# ─────────────────────────────────────────────────────────────────────────────
def phase1c() -> dict[str, Any]:
    """
    Permutation null: keep UBP constants fixed, but assign the user's specific
    exponents {1, 2, -3, 1, 5} and coefficient {13} to the 5 variables in all
    120 possible ways. Count how many permutations yield a match at UBP_ERROR.

    This tests whether the *specific* role-assignment matters or whether any
    permutation would do equally well.
    """
    print(f"\n[1C] Permutation null model...")
    user_exps = [1, 2, -3, 1, 5]   # U_E^1, MONAD^2, Y^-3, L^1, SIGMA^5
    user_coeff = 13.0

    # Generate all 5! = 120 permutations of exponents across variables
    perms = list(itertools.permutations(user_exps))
    print(f"     {len(perms)} permutations of exponents {user_exps} across {UBP_VAR_NAMES}")

    results = []
    hits_at_ubp = 0
    hits_at_1pct = 0
    hits_at_01pct = 0
    hits_at_001pct = 0

    for perm in perms:
        # Compute value = coeff * prod(var_i ^ perm_i)
        log_val = math.log(user_coeff) + sum(p * math.log(v) for p, v in zip(perm, UBP_VAR_VALS))
        val = math.exp(log_val)
        err = abs(val - TARGET) / TARGET
        results.append({
            "perm": list(perm),
            "value": val,
            "rel_err": err,
            "rel_err_pct": err * 100,
        })
        if err < UBP_ERROR * 1.0001: hits_at_ubp += 1
        if err < 1e-2: hits_at_1pct += 1
        if err < 1e-3: hits_at_01pct += 1
        if err < 1e-4: hits_at_001pct += 1

    results.sort(key=lambda x: x["rel_err"])
    print(f"     Hits at thresholds:")
    print(f"       < 1%:        {hits_at_1pct}/{len(perms)} ({hits_at_1pct/len(perms)*100:.1f}%)")
    print(f"       < 0.1%:      {hits_at_01pct}/{len(perms)} ({hits_at_01pct/len(perms)*100:.1f}%)")
    print(f"       < 0.01%:     {hits_at_001pct}/{len(perms)} ({hits_at_001pct/len(perms)*100:.1f}%)")
    print(f"       < UBP-c ({UBP_ERROR:.3e}): {hits_at_ubp}/{len(perms)} ({hits_at_ubp/len(perms)*100:.1f}%)")

    # Find the user's original permutation's rank
    user_perm = tuple(user_exps)
    user_rank = next((i for i, r in enumerate(results) if tuple(r["perm"]) == user_perm), None)
    print(f"\n     User's permutation rank: #{user_rank+1 if user_rank is not None else '?'} "
          f"of {len(results)} (err = {UBP_ERROR*100:.7f}%)")
    print(f"     Top 5 permutations by error:")
    for i, r in enumerate(results[:5]):
        is_user = "  <= USER" if tuple(r["perm"]) == user_perm else ""
        print(f"       {i+1}. exps={r['perm']}  err={r['rel_err_pct']:.7f}%{is_user}")

    return {
        "n_permutations": len(perms),
        "user_exponents": user_exps,
        "user_coefficient": user_coeff,
        "hits_at_thresholds": {
            "lt_1pct":      hits_at_1pct,
            "lt_0.1pct":    hits_at_01pct,
            "lt_0.01pct":   hits_at_001pct,
            "lt_ubp_error": hits_at_ubp,
        },
        "fraction_at_ubp_threshold": hits_at_ubp / len(perms),
        "user_permutation_rank": user_rank,
        "top_10_permutations": results[:10],
        "bottom_5_permutations": results[-5:],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1D — Information-theoretic / MDL analysis
# ─────────────────────────────────────────────────────────────────────────────
def phase1d() -> dict[str, Any]:
    """
    Minimum Description Length (MDL) comparison.

    Cost of storing c directly:
      c = 299792458 (integer). log2(c) ≈ 28.16 bits.

    Cost of UBP-c formula:
      - Structural cost: choosing 5 of ~10 UBP substrate objects
      - Exponent cost: 5 exponents, each from {-5..+5} (11 options)
      - Coefficient cost: 1 of 10 options
      - Residual cost: bits needed to specify the offset from formula's output to true c

    The formula is favourable only if its total cost < cost of storing c directly.
    """
    print(f"\n[1D] Information-theoretic / MDL analysis...")

    # Cost of c directly (assuming c is a 9-digit integer)
    c_int = int(C_SI)
    bits_c_direct = math.log2(c_int + 1)  # ~28.16 bits
    print(f"     Cost to store c directly: log2({c_int}+1) = {bits_c_direct:.4f} bits")

    # Cost of UBP-c formula (lower bound, being generous to UBP)
    # Assume UBP has ~10 substrate objects to choose from (Y, MONAD, WOBBLE, L, U_E, SIGMA, PI, PHI, E, ...).
    n_substrate_objects = 10
    bits_structural_choice = 5 * math.log2(n_substrate_objects)  # choose 5 of 10 with replacement
    bits_exponents = 5 * math.log2(len(EXP_RANGE_MACRO))         # 5 exponents × log2(11)
    bits_coefficient = math.log2(len(COEFFS_MACRO))              # log2(10)
    bits_formula_total = bits_structural_choice + bits_exponents + bits_coefficient

    # Residual: how many bits to specify the offset (formula → true c)?
    # c_derived ≈ 299800507.93, true c = 299792458.
    # |offset| ≈ 8050. To uniquely identify the integer offset within ±2^k,
    # need log2(|offset|) bits + 1 sign bit.
    offset = abs(float(C_DERIVED_UBP) - float(C_SI))
    bits_residual = math.log2(offset + 1) + 1   # +1 for sign
    bits_total_with_residual = bits_formula_total + bits_residual

    print(f"     UBP formula cost (generous lower bound):")
    print(f"       Structural (5 of {n_substrate_objects} substrate objects): {bits_structural_choice:.2f} bits")
    print(f"       Exponents (5 × log2(11)):                              {bits_exponents:.2f} bits")
    print(f"       Coefficient (log2(10)):                                 {bits_coefficient:.2f} bits")
    print(f"       Subtotal (formula specification):                       {bits_formula_total:.2f} bits")
    print(f"     Residual to recover exact c:")
    print(f"       |c_derived - c| = {offset:.2f} m/s")
    print(f"       bits_residual = log2({offset:.2f}+1) + 1 sign =        {bits_residual:.2f} bits")
    print(f"     Total UBP-c description:                                  {bits_total_with_residual:.2f} bits")
    print(f"     Total direct c description:                              {bits_c_direct:.2f} bits")
    print(f"     MDL penalty of UBP-c: {bits_total_with_residual - bits_c_direct:+.2f} bits")
    verdict = "UBP-c is FAVOURABLE under MDL" if bits_total_with_residual < bits_c_direct \
              else "UBP-c is UNFAVOURABLE under MDL (formula costs more than the value it predicts)"
    print(f"     Verdict: {verdict}")

    # Effective information content of the match
    # If formula gives value v with |v - c|/c = ε, the match "explains" log2(c) - log2(c·ε) bits
    # = -log2(ε) bits.
    bits_explained = -math.log2(UBP_ERROR)
    bits_formula_cost = bits_formula_total
    info_ratio = bits_explained / bits_formula_cost
    print(f"\n     Alternative view: information content of match")
    print(f"       Bits 'explained' by the match = -log2({UBP_ERROR:.3e}) = {bits_explained:.2f} bits")
    print(f"       Bits 'spent' on formula spec   = {bits_formula_cost:.2f} bits")
    print(f"       Information ratio (explained / spent) = {info_ratio:.3f}")
    print(f"       (ratio < 1 means formula carries less info than it costs to specify => overfit)")

    # Fisher exact test on Phase 1B results would go here, but we'll compute it
    # in the aggregation step after Phase 1B finishes.

    return {
        "c_direct_bits": bits_c_direct,
        "formula_cost_bits": {
            "structural": bits_structural_choice,
            "exponents": bits_exponents,
            "coefficient": bits_coefficient,
            "subtotal": bits_formula_total,
            "n_substrate_objects_assumed": n_substrate_objects,
        },
        "residual_bits": bits_residual,
        "offset_abs": offset,
        "total_ubp_description_bits": bits_total_with_residual,
        "mdl_penalty_bits": bits_total_with_residual - bits_c_direct,
        "mdl_verdict": verdict,
        "information_content": {
            "bits_explained_by_match": bits_explained,
            "bits_spent_on_formula": bits_formula_cost,
            "info_ratio": info_ratio,
            "interpretation": "favourable" if info_ratio > 1 else "overfit (formula costs more info than it explains)",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 80)
    print(" PHASE 1 — FALSIFICATION SUITE FOR UBP-c CLAIM")
    print("=" * 80)
    print(f" Target c = {TARGET} m/s (exact SI)")
    print(f" UBP-c error = {UBP_ERROR*100:.7f}%  ({UBP_ERROR:.3e})")
    print(f" Search space: {len(EXP_RANGE_MACRO)}^{len(UBP_VAR_NAMES)} exponents × {len(COEFFS_MACRO)} coeffs "
          f"= {len(EXP_RANGE_MACRO)**len(UBP_VAR_NAMES) * len(COEFFS_MACRO):,} combinations")
    print("=" * 80)

    results = {
        "metadata": {
            "target_c": TARGET,
            "ubp_error": UBP_ERROR,
            "ubp_error_pct": UBP_ERROR * 100,
            "search_space_vars": UBP_VAR_NAMES,
            "exp_range": EXP_RANGE_MACRO,
            "coefficients": COEFF_NAMES,
            "total_search_space": len(EXP_RANGE_MACRO)**len(UBP_VAR_NAMES) * len(COEFFS_MACRO),
        },
    }

    results["phase1a_search_enumeration"] = phase1a()
    results["phase1b_random_transcendentals"] = phase1b(n_trials=200, seed=42)
    results["phase1c_permutation_null"] = phase1c()
    results["phase1d_information_theory"] = phase1d()

    # Fisher exact test: UBP search vs. random transcendentals
    # Contingency table:
    #                    | hit at UBP threshold | no hit |
    # UBP search (1.6M)  |          N_ubp       |  rest  |
    # Random transc (avg)|       N_random_avg   |  rest  |
    # Actually, the right test is: given that UBP-c found a hit at 2.685e-5 in a
    # 1.6M-combination search, what's the probability a random search of the
    # same size finds an equally good hit? That's exactly Phase 1B's p-value.
    p1b = results["phase1b_random_transcendentals"]
    p_value = p1b["p_value_ubp_match"]
    ci_low = p1b["bootstrap_ci_95"]["low"]
    ci_high = p1b["bootstrap_ci_95"]["high"]

    # Multiple comparison correction: we tested 7 thresholds; Bonferroni
    bonferroni_alpha = 0.05 / 7
    significant = p_value < bonferroni_alpha

    print("\n" + "=" * 80)
    print(" PHASE 1 SUMMARY")
    print("=" * 80)
    print(f"  Phase 1A: UBP search space has {results['phase1a_search_enumeration']['hits_at_thresholds']['UBP-c (2.685e-5)']} hits at UBP-c threshold")
    print(f"            out of {results['phase1a_search_enumeration']['search_space_size']:,} combinations")
    print(f"  Phase 1B: Empirical p-value for UBP-c match = {p_value:.4f}")
    print(f"            Bootstrap 95% CI = [{ci_low:.4f}, {ci_high:.4f}]")
    print(f"            Bonferroni-corrected alpha (7 thresholds) = {bonferroni_alpha:.4f}")
    print(f"            Significant after correction? {significant}")
    print(f"  Phase 1C: {results['phase1c_permutation_null']['hits_at_thresholds']['lt_ubp_error']}/120 "
          f"permutations hit at UBP-c threshold")
    print(f"  Phase 1D: MDL penalty = {results['phase1d_information_theory']['mdl_penalty_bits']:+.2f} bits")
    print(f"            {results['phase1d_information_theory']['mdl_verdict']}")

    results["phase1_summary"] = {
        "p_value_ubp_match": p_value,
        "bootstrap_ci_95": [ci_low, ci_high],
        "bonferroni_alpha": bonferroni_alpha,
        "significant_after_correction": significant,
        "mdl_penalty_bits": results["phase1d_information_theory"]["mdl_penalty_bits"],
        "mdl_verdict": results["phase1d_information_theory"]["mdl_verdict"],
    }

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[Saved] {OUT_PATH}")


if __name__ == "__main__":
    main()
