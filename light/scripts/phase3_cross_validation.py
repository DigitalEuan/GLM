"""
Phase 3 — Within-c cross-validation.

Goal: test whether the UBP substrate's flexibility is *specific* to c or whether
the same substrate can match ANY similarly-sized target just as easily.

Tests:
  3A. Search for matches to c in different unit systems (ft/s, mi/s, furlongs/fortnight).
      If the substrate is "tuned to c," it should NOT match c-in-other-units.
  3B. Search for matches to c², 1/c, sqrt(c).
  3C. Search for matches to ANCHOR SI constants (Δν_Cs = 9,192,631,770 Hz exactly;
      this is what *actually* defines the second, hence c).
  3D. Search for matches to DECOY targets (random 9-digit integers, pi*10^8, etc.).
      If the substrate matches decoys as well as it matches c, the c-match is not special.
  3E. Sensitivity analysis: perturb each UBP constant by ±1% and measure how much
      c_derived changes. Tight tuning => overfitting.

All results saved to /home/z/my-project/work/phase3_results.json.
"""
from __future__ import annotations
import json
import math
import itertools
import time
import numpy as np
from fractions import Fraction as F
from typing import Any

from ubp_constants import (
    PI, PHI, E, Y_INV, Y, MONAD, WOBBLE, L, U_E, SIGMA, C_SI, C_DERIVED_UBP,
)
from phase1_falsification import (
    UBP_VAR_NAMES, UBP_VAR_VALS, UBP_VAR_LOGS,
    EXP_RANGE_MACRO, COEFFS_MACRO, COEFF_NAMES, COEFF_LOGS,
    enumerate_search_space, UBP_ERROR,
)

OUT_PATH = "/home/z/my-project/work/phase3_results.json"
TARGET = float(C_SI)

# Conversion factors
M_TO_FT   = 3.2808398950131     # 1 m = 3.28084 ft (exact: 1250/381)
M_TO_MI   = 1.0 / 1609.344      # 1 mi = 1609.344 m (exact)
M_TO_FURLONG = 1.0 / 201.168    # 1 furlong = 201.168 m (exact)
SEC_PER_FORTNIGHT = 14 * 24 * 3600  # 1,209,600 s

# Other SI-defined constants
DELTA_NU_CS = 9_192_631_770.0    # Hz, exact (defines the second)
BOLTZMANN_K = 1.380649e-23       # J/K, exact (SI 2019)
PLANCK_H    = 6.62607015e-34     # J·s, exact (SI 2019)
ELEMENTARY_CHARGE = 1.602176634e-19  # C, exact (SI 2019)
AVOGADRO_N  = 6.02214076e23      # mol^-1, exact (SI 2019)
K_PLANCK_CONSTANT = 1.380649e-23 # J/K (duplicate for clarity)

# Decoy targets (9-digit integers and similar)
DECOY_TARGETS = [
    ("random_9digit_1", 123_456_789.0),
    ("random_9digit_2", 987_654_321.0),
    ("random_9digit_3", 555_555_555.0),
    ("pi_x_1e8",        math.pi * 1e8),
    ("e_x_1e8",         math.e * 1e8),
    ("sqrt2_x_1e8",     math.sqrt(2) * 1e8),
    ("first_9_primes_concat", 235711131719.0),  # 2,3,5,7,11,13,17,19,23 concat
    ("fibonacci_index", 13 * 21 * 34 * 55 * 89),  # Fibonacci product
]


def search_for_target(target: float, threshold: float = UBP_ERROR) -> dict:
    """Run the full UBP search space against an arbitrary target."""
    log_vals, exp_tuples = enumerate_search_space(UBP_VAR_LOGS, EXP_RANGE_MACRO, COEFF_LOGS)
    values = np.exp(log_vals)
    rel_err = np.abs(values - target) / target
    n_total = rel_err.size

    # Count hits at multiple thresholds (inclusive of UBP-c's own error)
    hits = {}
    for thresh, name in [(1e-2, "lt_1pct"), (1e-3, "lt_0.1pct"),
                          (1e-4, "lt_0.01pct"), (1e-5, "lt_0.001pct"),
                          (UBP_ERROR * 1.0001, "lte_ubp_err")]:
        hits[name] = int(np.sum(rel_err <= thresh))

    # Best match
    best_flat = int(np.argmin(rel_err))
    n_tuples, n_coeffs = rel_err.shape
    i, j = divmod(best_flat, n_coeffs)
    exps = exp_tuples[i].tolist()
    terms = []
    if COEFF_NAMES[j] != "1": terms.append(COEFF_NAMES[j])
    for name, e in zip(UBP_VAR_NAMES, exps):
        if e == 0: continue
        terms.append(name if e == 1 else f"{name}^{e}")
    best_expr = " * ".join(terms)

    return {
        "target": target,
        "n_total_combinations": n_total,
        "hits_at_thresholds": hits,
        "best_match": {
            "expr": best_expr,
            "value": float(values[i, j]),
            "rel_err": float(rel_err[i, j]),
            "rel_err_pct": float(rel_err[i, j] * 100),
            "exponents": exps,
            "coeff": COEFF_NAMES[j],
        },
    }


def phase3a_cross_unit() -> dict:
    """Test if substrate matches c in other unit systems."""
    print("\n[3A] Cross-unit test: does substrate match c in non-SI units?")
    targets = [
        ("c (m/s, SI)",            TARGET),
        ("c (ft/s)",                TARGET * M_TO_FT),
        ("c (mi/s)",                TARGET * M_TO_MI),
        ("c (furlong/fortnight)",   TARGET * M_TO_FURLONG / SEC_PER_FORTNIGHT * 1),
        ("c (km/s)",                TARGET / 1000.0),
        ("c (knots)",               TARGET * 1.9438444924406),  # 1 m/s = 1.94384 knots
    ]
    results = []
    for name, target in targets:
        r = search_for_target(target)
        r["target_name"] = name
        results.append(r)
        bm = r["best_match"]
        h = r["hits_at_thresholds"]
        print(f"  {name:<30} target={target:>20.4f}  best_err={bm['rel_err_pct']:.6f}%  "
              f"hits@UBP={h['lte_ubp_err']}  hits@0.01%={h['lt_0.01pct']}")
    return results


def phase3b_c_powers() -> dict:
    """Test if substrate matches c², c³, 1/c, √c, ln(c)."""
    print("\n[3B] Powers of c: does substrate match c^k or 1/c?")
    targets = [
        ("c",       TARGET),
        ("c^2",     TARGET**2),
        ("c^3",     TARGET**3),
        ("1/c",     1.0 / TARGET),
        ("sqrt(c)", math.sqrt(TARGET)),
        ("ln(c)",   math.log(TARGET)),
        ("log10(c)",math.log10(TARGET)),
        ("c^(1/3)", TARGET**(1.0/3.0)),
    ]
    results = []
    for name, target in targets:
        r = search_for_target(target)
        r["target_name"] = name
        results.append(r)
        bm = r["best_match"]
        h = r["hits_at_thresholds"]
        print(f"  {name:<10} target={target:>25.6e}  best_err={bm['rel_err_pct']:.6f}%  "
              f"hits@UBP={h['lte_ubp_err']}  hits@0.01%={h['lt_0.01pct']}")
    return results


def phase3c_si_anchors() -> dict:
    """Test if substrate matches other SI-defined constants."""
    print("\n[3C] SI-defined anchors: does substrate match Δν_Cs, h, e, N_A, k_B?")
    targets = [
        ("Δν_Cs (Hz, defines second)",   DELTA_NU_CS),
        ("h (Planck, J·s)",              PLANCK_H),
        ("e (elementary charge, C)",     ELEMENTARY_CHARGE),
        ("N_A (Avogadro, mol^-1)",       AVOGADRO_N),
        ("k_B (Boltzmann, J/K)",         BOLTZMANN_K),
        ("c·Δν_Cs (m·Hz/s = m·s^-2)",    TARGET * DELTA_NU_CS),
    ]
    results = []
    for name, target in targets:
        r = search_for_target(target)
        r["target_name"] = name
        results.append(r)
        bm = r["best_match"]
        h = r["hits_at_thresholds"]
        print(f"  {name:<35} target={target:>20.6e}  best_err={bm['rel_err_pct']:.6f}%  "
              f"hits@UBP={h['lte_ubp_err']}  hits@0.01%={h['lt_0.01pct']}")
    return results


def phase3d_decoys() -> dict:
    """Test if substrate matches arbitrary decoy targets."""
    print("\n[3D] Decoy targets: does substrate match random/arbitrary 9-digit numbers?")
    results = []
    for name, target in DECOY_TARGETS:
        r = search_for_target(target)
        r["target_name"] = name
        results.append(r)
        bm = r["best_match"]
        h = r["hits_at_thresholds"]
        print(f"  {name:<28} target={target:>20.4f}  best_err={bm['rel_err_pct']:.6f}%  "
              f"hits@UBP={h['lte_ubp_err']}  hits@0.01%={h['lt_0.01pct']}")
    return results


def phase3e_sensitivity() -> dict:
    """
    Sensitivity analysis: perturb each UBP constant by ±1% and ±0.1% and measure
    how much c_derived changes.

    A robust, principled formula should respond proportionally to perturbations.
    A finely-tuned, overfit formula will have a 'cliff' where small perturbations
    break the match dramatically.
    """
    print("\n[3E] Sensitivity analysis: perturb each UBP constant, measure c_derived change")
    base_value = float(C_DERIVED_UBP)
    base_err = abs(base_value - TARGET) / TARGET

    var_names = ["PI", "PHI", "E", "Y", "MONAD", "WOBBLE", "L", "U_E", "SIGMA"]
    var_vals_base = [float(PI), float(PHI), float(E), float(Y), float(MONAD),
                     float(WOBBLE), float(L), float(U_E), float(SIGMA)]
    perturbations = [0.999, 0.9999, 1.0001, 1.001]  # ±0.1%, ±1%

    # The formula: c = 13 * U_E * MONAD^2 * Y^-3 * L * SIGMA^5
    # Each variable's exponent:
    var_exps = {
        "PI": 0, "PHI": 0, "E": 0,  # via MONAD
        "Y": -3, "MONAD": 2, "WOBBLE": 0,  # WOBBLE only via L
        "L": 1, "U_E": 1, "SIGMA": 5,
    }
    # Note: PI, PHI, E appear only via MONAD (with exponent 2 on MONAD).
    # MONAD = PI * PHI * E, so ∂ln(MONAD)/∂ln(PI) = 1, etc.
    # Therefore: ∂ln(c)/∂ln(PI) = 2 (via MONAD^2)
    # Same for PHI and E.

    results = []
    for vname, vbase in zip(var_names, var_vals_base):
        # The variable's effective exponent in the c formula
        if vname in ("PI", "PHI", "E"):
            eff_exp = 2  # via MONAD^2
        elif vname == "MONAD":
            eff_exp = 2
        elif vname == "WOBBLE":
            eff_exp = 1  # via L (since L = WOBBLE/13, c depends linearly on L)
        else:
            eff_exp = var_exps[vname]

        row = {
            "variable": vname,
            "base_value": vbase,
            "effective_exponent_in_c": eff_exp,
            "perturbations": [],
        }
        for p in perturbations:
            new_val = vbase * p
            # Compute new c_derived
            # Easiest: c scales as variable^eff_exp, so new_c = base_c * (p^eff_exp)
            # (This is exact because the formula is a monomial product.)
            new_c = base_value * (p ** eff_exp)
            new_err = abs(new_c - TARGET) / TARGET
            row["perturbations"].append({
                "factor": p,
                "delta_pct": (p - 1) * 100,
                "new_c": new_c,
                "new_rel_err": new_err,
                "new_rel_err_pct": new_err * 100,
                "err_change_factor": new_err / base_err if base_err > 0 else float("inf"),
            })
        # Report the ±1% case
        plus_1 = row["perturbations"][3]  # 1.001
        minus_1 = row["perturbations"][0]  # 0.999
        print(f"  {vname:<8} exp={eff_exp:+d}  base={vbase:>15.6f}  "
              f"±1% -> err {minus_1['new_rel_err_pct']:.5f}% / {plus_1['new_rel_err_pct']:.5f}%  "
              f"(base err {base_err*100:.5f}%)")
        results.append(row)

    # Compute "elasticity": how much does relative error change per % perturbation?
    # If a 1% perturbation in a constant causes a 100× change in error, the formula
    # is finely-tuned to that constant's specific value.
    elasticity_summary = []
    for r in results:
        for p in r["perturbations"]:
            if abs(p["factor"] - 1.001) < 1e-6:
                elasticity = p["err_change_factor"]
                elasticity_summary.append({
                    "variable": r["variable"],
                    "effective_exponent": r["effective_exponent_in_c"],
                    "err_change_for_1pct_perturbation": elasticity,
                })
    elasticity_summary.sort(key=lambda x: x["err_change_for_1pct_perturbation"], reverse=True)
    print(f"\n  Elasticity ranking (error multiplier per +1% perturbation):")
    for e in elasticity_summary:
        print(f"    {e['variable']:<8} exp={e['effective_exponent']:+d}  error×{e['err_change_for_1pct_perturbation']:.2f}")

    return {
        "base_c_derived": base_value,
        "base_rel_err": base_err,
        "per_variable": results,
        "elasticity_ranking": elasticity_summary,
    }


def main():
    print("=" * 80)
    print(" PHASE 3 — WITHIN-c CROSS-VALIDATION")
    print("=" * 80)
    print(f" UBP-c error = {UBP_ERROR*100:.7f}%  (reference threshold)")
    print(f" Search space: 1,610,510 combinations (same as Phase 1)")

    p3a = phase3a_cross_unit()
    p3b = phase3b_c_powers()
    p3c = phase3c_si_anchors()
    p3d = phase3d_decoys()
    p3e = phase3e_sensitivity()

    # Summary: count how many targets the substrate "matches" at UBP_ERROR threshold
    print("\n" + "=" * 80)
    print(" PHASE 3 SUMMARY")
    print("=" * 80)
    print(f"  Substrate matches at UBP-c threshold (rel err < {UBP_ERROR*100:.5f}%):")
    print(f"  {'Target':<40} {'Hits at UBP err':>20}  {'Best err %':>15}")
    print("  " + "-" * 80)

    all_targets = []
    for label, items in [("3A cross-unit", p3a), ("3B c-powers", p3b),
                         ("3C SI anchors", p3c), ("3D decoys", p3d)]:
        for r in items:
            all_targets.append((label, r))
            hits = r["hits_at_thresholds"]["lte_ubp_err"]
            best = r["best_match"]["rel_err_pct"]
            name = r["target_name"]
            print(f"  [{label}] {name:<30}  {hits:>10}  {best:>15.7f}%")

    n_matched = sum(1 for _, r in all_targets if r["hits_at_thresholds"]["lte_ubp_err"] > 0)
    n_total = len(all_targets)
    print(f"\n  Substrate matched {n_matched}/{n_total} targets at UBP-c threshold")
    verdict = (
        "Substrate is OVERFLEXIBLE — matches arbitrary targets as easily as c."
        if n_matched >= n_total * 0.5
        else "Substrate is SOMEWHAT selective — but still matches many non-c targets."
        if n_matched >= n_total * 0.2
        else "Substrate is selective to c."
    )
    print(f"  Verdict: {verdict}")

    results = {
        "metadata": {
            "ubp_error_threshold": UBP_ERROR,
            "search_space_size": 1610510,
        },
        "phase3a_cross_unit": p3a,
        "phase3b_c_powers": p3b,
        "phase3c_si_anchors": p3c,
        "phase3d_decoys": p3d,
        "phase3e_sensitivity": p3e,
        "summary": {
            "n_targets_matched_at_ubp_threshold": n_matched,
            "n_total_targets": n_total,
            "fraction_matched": n_matched / n_total,
            "verdict": verdict,
        },
    }

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[Saved] {OUT_PATH}")


if __name__ == "__main__":
    main()
