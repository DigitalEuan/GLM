"""
Phase 18 — The 24-Cell, Schwinger Correction, and Exponent Derivation

Testing three claims from the quantum_leap document:
  1. The exponents 4,4 come from the 24-cell (4D regular polytope)
  2. The Schwinger correction α/(2π) collapses the 0.009% error
  3. Group-theoretic (Haar) measures eliminate the π-dependence

  18A: Test the 24-cell structural derivation of exponents
  18B: Test the Schwinger correction (does α/(2π) help or hurt?)
  18C: Test what the exact correction IS (is it a substrate expression?)
  18D: Precision stability + null model with 24-cell constraints
  18E: Honest assessment

All results saved to /home/z/my-project/work/phase18_results.json
"""
from __future__ import annotations
import json, math, sys, os, random
from typing import Any
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from ubp_unified_v5 import PARTICLE_PHYSICS

OUT_PATH = "/home/z/my-project/work/phase18_results.json"

PI = math.pi; PHI = (1+math.sqrt(5))/2; E_CONST = math.e
MONAD = PI * PHI * E_CONST; WOBBLE = MONAD - 13; Y = 1.0/(PI+2.0/PI)
H_PLANCK = 6.62607015e-34; C_LIGHT = 299792458.0; DELTA_NU_CS = 9192631770.0
M_ELECTRON = 9.1093837015e-31
ALPHA = 1/137.035999084

# Phase 17 result
M_DERIVED = Y**2 * WOBBLE * 24**4 * 29**4 * H_PLANCK * DELTA_NU_CS / C_LIGHT**2
ERROR_RAW = abs(M_DERIVED - M_ELECTRON)/M_ELECTRON * 100
CORRECTION_NEEDED = M_ELECTRON / M_DERIVED - 1


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18A — 24-cell structural derivation
# ─────────────────────────────────────────────────────────────────────────────

def phase18a_24cell() -> dict:
    """Test whether the 24-cell (4D regular polytope) derives the exponents."""
    print("=" * 80)
    print("[18A] 24-CELL STRUCTURAL DERIVATION OF EXPONENTS")
    print("=" * 80)
    print()
    print("The 24-cell (Icositetrachoron):")
    print("  4D regular polytope, self-dual")
    print("  24 vertices, 96 edges, 96 triangular faces, 24 octahedral cells")
    print("  Euler characteristic: 24 - 96 + 96 - 24 = 0")
    print("  It exists ONLY in 4D (no 3D equivalent)")
    print()
    print("Claim: the exponents 4,4 come from the 4-dimensionality of the 24-cell.")
    print()

    # If the exponent 4 comes from 4D, then using 24-cell numbers:
    # Instead of 24^4 × 29^4, try 24-cell structural numbers to the 4th power
    cell_numbers = {
        "24 (vertices/cells)": 24,
        "96 (edges/faces)": 96,
        "24×96 = 2304": 24*96,
        "24+96 = 120": 24+96,
        "96-24 = 72": 96-24,
        "24² = 576": 24**2,
        "96² = 9216": 96**2,
    }

    print("Testing 24-cell numbers as replacements for 29:")
    print(f"  Current: 24⁴ × 29⁴ = {24**4 * 29**4:.4e}")
    print()

    # The needed scale (from Phase 17): 24⁴ × 29⁴ × Y² × WOBBLE ≈ 5.078×10¹⁰
    # If we replace 29⁴ with a 24-cell number, does it still work?
    needed = 5.078e10 / (Y**2 * WOBBLE)  # the integer part needed

    for name, val in cell_numbers.items():
        # Try val^4 as replacement for 29^4
        if val > 0:
            test_scale = 24**4 * val**4 * Y**2 * WOBBLE
            err = abs(test_scale - 5.078e10) / 5.078e10 * 100
            m_test = test_scale * H_PLANCK * DELTA_NU_CS / C_LIGHT**2
            m_err = abs(m_test - M_ELECTRON) / M_ELECTRON * 100
            print(f"  24⁴ × {name}⁴ × Y² × WOBBLE: scale={test_scale:.4e}, m_err={m_err:.4f}%")

    print()

    # Also test: does the 24-cell's 4-dimensionality explain why BOTH exponents are 4?
    print("Why exponent = 4?")
    print("  The 24-cell is a 4D object → its 'volume' is 4-dimensional")
    print("  Raising to the 4th power = computing a 4D hypervolume")
    print("  If BOTH 24 and 29 represent axes of a 4D space, their 4th powers")
    print("  give the 4D hypervolume of the Virtual XYZ space.")
    print()
    print("  This is a STRUCTURAL argument, not a search result.")
    print("  But 29 is NOT a 24-cell number (24-cell has 24, 96).")
    print("  So the argument works for 24⁴ but not for 29⁴.")
    print()

    # Can we replace 29 with a 24-cell-derived number?
    # The 24-cell's dual is itself. Its symmetry group has order 1152.
    # 1152 = 24 × 48 = 24 × 2⁴ × 3
    print("24-cell symmetry group: order 1152")
    print(f"  1152 = 24 × 48 = 24 × 2⁴ × 3")
    print(f"  1152/4 = {1152/4} = 288")
    print(f"  1152/24 = {1152/24} = 48")
    print()

    # Test: 24⁴ × 48⁴ × Y² × WOBBLE (using 48 from the symmetry group)
    for repl in [48, 96, 288, 1152, 12, 6, 8]:
        test_scale = 24**4 * repl**4 * Y**2 * WOBBLE
        m_test = test_scale * H_PLANCK * DELTA_NU_CS / C_LIGHT**2
        m_err = abs(m_test - M_ELECTRON) / M_ELECTRON * 100
        print(f"  24⁴ × {repl}⁴ × Y² × WOBBLE: m_err = {m_err:.4f}%")

    print()
    return {
        "24_cell_numbers": [24, 96, 1152],
        "exponent_argument": "4D polytope → 4th power = 4D hypervolume. Works for 24 but not 29.",
        "finding": "The 24-cell explains exponent 4 for the 24 axis, but 29 is NOT a 24-cell number. The structural argument is partial.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18B — Schwinger correction test
# ─────────────────────────────────────────────────────────────────────────────

def phase18b_schwinger() -> dict:
    """Test the Schwinger correction claim."""
    print()
    print("=" * 80)
    print("[18B] SCHWINGER CORRECTION TEST")
    print("=" * 80)
    print()
    print(f"Phase 17 result: m = {M_DERIVED:.10e} kg")
    print(f"m_e = {M_ELECTRON:.10e} kg")
    print(f"Raw error: {ERROR_RAW:.6f}% (UBP is too LOW)")
    print(f"Exact correction needed: {CORRECTION_NEEDED:.10e} = {CORRECTION_NEEDED*100:.8f}%")
    print()

    schwinger = ALPHA / (2 * PI)
    print(f"Schwinger term α/(2π) = {schwinger:.10f} = {schwinger*100:.6f}%")
    print(f"  This is {schwinger/CORRECTION_NEEDED:.1f}× LARGER than the correction needed")
    print()

    # Test: apply Schwinger correction
    m_schwinger_add = M_DERIVED * (1 + schwinger)
    err_add = abs(m_schwinger_add - M_ELECTRON) / M_ELECTRON * 100
    print(f"m × (1 + α/2π) = {m_schwinger_add:.10e}, error = {err_add:.4f}%")

    m_schwinger_div = M_DERIVED / (1 + schwinger)
    err_div = abs(m_schwinger_div - M_ELECTRON) / M_ELECTRON * 100
    print(f"m / (1 + α/2π) = {m_schwinger_div:.10e}, error = {err_div:.4f}%")
    print()

    # The Schwinger correction makes things WORSE
    print(f"RESULT: The Schwinger correction does NOT help.")
    print(f"  It is {schwinger/CORRECTION_NEEDED:.1f}× too large.")
    print(f"  Applying it increases the error from {ERROR_RAW:.4f}% to {err_add:.4f}%.")
    print()

    # What IS the correction?
    print(f"What IS the exact correction needed?")
    print(f"  correction = {CORRECTION_NEEDED:.10e}")
    print(f"  = α² × √3? {ALPHA**2 * math.sqrt(3):.10e} (error {abs(ALPHA**2*math.sqrt(3)/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print(f"  = α² × φ?  {ALPHA**2 * PHI:.10e} (error {abs(ALPHA**2*PHI/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print(f"  = α² × e?  {ALPHA**2 * E_CONST:.10e} (error {abs(ALPHA**2*E_CONST/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print(f"  = α² × π?  {ALPHA**2 * PI:.10e} (error {abs(ALPHA**2*PI/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print(f"  = α² / Y?  {ALPHA**2 / Y:.10e} (error {abs(ALPHA**2/Y/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print(f"  = α × Y⁴?  {ALPHA * Y**4:.10e} (error {abs(ALPHA*Y**4/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print(f"  = α × Y³?  {ALPHA * Y**3:.10e} (error {abs(ALPHA*Y**3/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print(f"  = Y⁵?      {Y**5:.10e} (error {abs(Y**5/CORRECTION_NEEDED - 1)*100:.3f}%)")
    print()

    # The correction is closest to α² × √3 (0.35% error)
    # But √3 is not a UBP constant
    # However, √3 = √(3) and 3 is a UBP structural integer (spatial axes)
    print(f"  The correction is closest to α² × √3 (0.35% error)")
    print(f"  √3 = √(3) where 3 = number of spatial axes (TGIC)")
    print(f"  This is suggestive but not exact.")
    print()

    return {
        "schwinger_claim": "FALSE — α/(2π) is 12.6× too large; applying it increases error",
        "exact_correction": CORRECTION_NEEDED,
        "closest_match": {"expression": "α² × √3", "error": 0.35},
        "finding": "The Schwinger correction claim is numerically wrong. The exact correction (9.19e-5) is closest to α² × √3 but not exact.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18C — Test the corrected formula
# ─────────────────────────────────────────────────────────────────────────────

def phase18c_corrected_formula() -> dict:
    """Test: m_e = Y² × WOBBLE × 24⁴ × 29⁴ × (1 + α²×√3) × h × Δν_Cs / c²"""
    print()
    print("=" * 80)
    print("[18C] CORRECTED FORMULA TEST")
    print("=" * 80)
    print()
    print(f"Testing: m_e = Y² × WOBBLE × 24⁴ × 29⁴ × (1 + α²√3) × h × Δν_Cs / c²")
    print()

    correction = ALPHA**2 * math.sqrt(3)
    m_corrected = M_DERIVED * (1 + correction)
    err_corrected = abs(m_corrected - M_ELECTRON) / M_ELECTRON * 100

    print(f"  α²√3 = {correction:.10e}")
    print(f"  m_corrected = {m_corrected:.10e} kg")
    print(f"  m_e = {M_ELECTRON:.10e} kg")
    print(f"  Error: {err_corrected:.6f}%")
    print()

    # This improves from 0.0092% to... let's see
    print(f"  Improvement: {ERROR_RAW:.6f}% → {err_corrected:.6f}%")
    print()

    # But this uses α (which itself needs derivation) and √3 (not a UBP constant)
    # Can we replace √3 with a substrate quantity?
    print("Can √3 be replaced by a substrate quantity?")
    sqrt3 = math.sqrt(3)
    candidates = {
        "Y_INV/MONAD": Y / (PI+2/PI) / MONAD,
        "WOBBLE×2": WOBBLE * 2,
        "MONAD/8": MONAD / 8,
        "φ/φ": 1.0,
        "π/e": PI / E_CONST,
        "e/π": E_CONST / PI,
        "φ²/φ": PHI,
        "MONAD/13 = γ": MONAD / 13,
        "Y_INV/π": (PI + 2/PI) / PI,
        "1+Y": 1 + Y,
        "2-Y": 2 - Y,
        "WOBBLE+1": WOBBLE + 1,
        "MONAD-12": MONAD - 12,
        "π/2": PI/2,
        "e-1": E_CONST - 1,
        "φ-0.3": PHI - 0.3,
    }
    for name, val in candidates.items():
        err = abs(val - sqrt3) / sqrt3 * 100
        if err < 5:
            print(f"  {name:<20} = {val:.6f}, error vs √3 = {err:.3f}%")

    print()

    # Also: does the correction work BETTER if we use a different form?
    # correction = α² × k for various k
    k_needed = CORRECTION_NEEDED / ALPHA**2
    print(f"k needed for α² × k = correction: k = {k_needed:.6f}")
    print(f"  = √3? {abs(k_needed - math.sqrt(3))/math.sqrt(3)*100:.3f}% error")
    print(f"  = φ? {abs(k_needed - PHI)/PHI*100:.3f}% error")
    print(f"  = e/φ? {abs(k_needed - E_CONST/PHI)/(E_CONST/PHI)*100:.3f}% error")
    print(f"  = π/φ? {abs(k_needed - PI/PHI)/(PI/PHI)*100:.3f}% error")
    print(f"  = φ/e? {abs(k_needed - PHI/E_CONST)/(PHI/E_CONST)*100:.3f}% error")
    print(f"  = MONAD/8? {abs(k_needed - MONAD/8)/(MONAD/8)*100:.3f}% error")
    print(f"  = Y_INV/2? {abs(k_needed - (PI+2/PI)/2)/((PI+2/PI)/2)*100:.3f}% error")

    return {
        "corrected_error": err_corrected,
        "improvement": ERROR_RAW - err_corrected,
        "k_needed": k_needed,
        "finding": f"The α²√3 correction improves error from {ERROR_RAW:.4f}% to {err_corrected:.4f}%, but √3 is not a UBP constant.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18D — Null model with 24-cell constraints
# ─────────────────────────────────────────────────────────────────────────────

def phase18d_null_model() -> dict:
    """If we constrain to 24-cell numbers (24, 96), how does the null model change?"""
    print()
    print("=" * 80)
    print("[18D] NULL MODEL WITH 24-CELL CONSTRAINTS")
    print("=" * 80)
    print()
    print("If exponents MUST be 4 (from 4D geometry), and integers MUST be")
    print("24-cell numbers (24, 96, 1152), how many matches exist?")
    print()

    # Allowed integers: 24, 96, 1152 (24-cell structural)
    # Allowed exponent: 4 (from 4D)
    # Formula: a⁴ × b⁴ × Y² × WOBBLE × h × Δν_Cs / c²

    allowed_ints = [24, 96, 1152, 12, 8, 6, 4, 3, 2, 1]
    # Also include 29 (UBP structural) for comparison

    print(f"Testing a⁴ × b⁴ × Y² × WOBBLE × h × Δν_Cs / c² for a,b in {allowed_ints}:")
    print()

    matches = []
    for a in allowed_ints:
        for b in allowed_ints:
            m_test = a**4 * b**4 * Y**2 * WOBBLE * H_PLANCK * DELTA_NU_CS / C_LIGHT**2
            err = abs(m_test - M_ELECTRON) / M_ELECTRON * 100
            matches.append((a, b, m_test, err))
            if err < 1.0:
                print(f"  {a}⁴ × {b}⁴: m = {m_test:.6e}, error = {err:.4f}%")

    matches.sort(key=lambda x: x[3])
    print()
    print(f"Top 5 (a, b) pairs:")
    for a, b, m, err in matches[:5]:
        print(f"  {a}⁴ × {b}⁴: error = {err:.4f}%")

    print()

    # Now the null model: random integers with exponent 4
    print("Null model: random integers with exponent 4 (50,000 trials)")
    rng = random.Random(42)
    n_match = 0
    best_random = float('inf')
    for _ in range(50000):
        a = rng.randint(2, 100)
        b = rng.randint(2, 100)
        m_test = a**4 * b**4 * Y**2 * WOBBLE * H_PLANCK * DELTA_NU_CS / C_LIGHT**2
        err = abs(m_test - M_ELECTRON) / M_ELECTRON * 100
        if err < best_random:
            best_random = err
        if err < 0.01:
            n_match += 1

    print(f"  Matches within 0.01%: {n_match}/50000")
    print(f"  Best random error: {best_random:.6f}%")
    print(f"  UBP (24, 29) error: {ERROR_RAW:.6f}%")
    print()

    # If the exponent is FIXED at 4, does the false-positive rate change?
    print(f"  With exponent fixed at 4: {n_match}/50000 false positives ({n_match/50000*100:.3f}%)")
    print(f"  Phase 17 (variable exponents): 5/50000 (0.010%)")
    print(f"  {'FEWER' if n_match < 5 else 'MORE'} false positives with fixed exponent 4")

    return {
        "24_cell_matches": [(a, b, err) for a, b, _, err in matches[:5]],
        "null_model_fixed_exp4": {"n_match": n_match, "best_random": best_random},
        "finding": f"Fixing exponent at 4 gives {n_match}/50000 false positives.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18E — Honest assessment
# ─────────────────────────────────────────────────────────────────────────────

def phase18e_assessment(p18a, p18b, p18c, p18d) -> dict:
    """Honest assessment."""
    print()
    print("=" * 80)
    print("[18E] HONEST ASSESSMENT")
    print("=" * 80)
    print()
    print("Three claims from the quantum_leap document were tested:")
    print()
    print(f"  18A (24-cell exponents):")
    print(f"    The 24-cell is a 4D object → exponent 4 = 4D hypervolume")
    print(f"    This works for the 24 axis but NOT for 29 (not a 24-cell number)")
    print(f"    Partial structural justification only")
    print()
    print(f"  18B (Schwinger correction):")
    print(f"    CLAIM: α/(2π) collapses the 0.009% error into ppb regime")
    print(f"    REALITY: α/(2π) = 0.116% is 12.6× LARGER than the 0.009% error")
    print(f"    Applying it INCREASES the error from 0.009% to 0.107%")
    print(f"    THE CLAIM IS NUMERICALLY WRONG")
    print()
    print(f"  18C (exact correction):")
    print(f"    The exact correction (9.19×10⁻⁵) is closest to α²×√3 (0.35% error)")
    print(f"    But √3 is not a UBP constant")
    print(f"    The correction is NOT a known QED quantity")
    print()
    print(f"  18D (null model with fixed exponent 4):")
    n_match = p18d["null_model_fixed_exp4"]["n_match"]
    print(f"    With exponent fixed at 4: {n_match}/50000 false positives")
    print(f"    This is {'BETTER' if n_match < 5 else 'WORSE'} than Phase 17's variable exponent (5/50000)")
    print()
    print("=" * 80)
    print(" OVERALL ASSESSMENT")
    print("=" * 80)
    print()
    print("  The quantum_leap document's three claims:")
    print()
    print("  1. 24-cell exponents: PARTIALLY CORRECT")
    print("     The 4D argument justifies exponent 4 for the 24 axis")
    print("     But 29 is not a 24-cell number — the argument is incomplete")
    print()
    print("  2. Schwinger correction: FALSE")
    print("     α/(2π) is 12.6× too large; applying it makes things worse")
    print("     The document's claim is numerically incorrect")
    print()
    print("  3. Haar measure / group theory: UNTESTED (but conceptually sound)")
    print("     Replacing linear WOBBLE with SO(3)/SU(2) invariants could")
    print("     eliminate the 0.0066% precision shift — but this requires")
    print("     implementing geometric algebra, which is beyond this script")
    print()
    print("  THE CORRECTION NEEDED:")
    print(f"    Exact correction = {CORRECTION_NEEDED:.6e} = {CORRECTION_NEEDED*100:.6f}%")
    print(f"    Closest match: α² × √3 (0.35% error)")
    print(f"    This is NOT the Schwinger correction")
    print(f"    It is NOT a known QED quantity")
    print(f"    It is a small, unexplained residual")
    print()
    print("  THE HONEST STATUS:")
    print("    Phase 17's formula (0.009% error) remains the best result")
    print("    The Schwinger correction does NOT improve it")
    print("    The 24-cell provides partial justification for exponent 4")
    print("    The 0.0066% precision shift remains (mildly unstable)")
    print("    The null model still has false positives")
    print()
    print("    This is NOT a derivation. It is the closest APPROXIMATION")
    print("    found in 18 phases, but the remaining gap is unexplained.")

    return {
        "claims": {
            "24_cell_exponents": "PARTIALLY CORRECT (works for 24, not 29)",
            "schwinger_correction": "FALSE (12.6× too large)",
            "haar_measure": "UNTESTED (conceptually sound but not implemented)",
        },
        "exact_correction": {
            "value": CORRECTION_NEEDED,
            "closest_match": "α² × √3 (0.35% error)",
            "is_schwinger": False,
            "is_known_qed": False,
        },
        "status": "Phase 17's 0.009% error remains the best. The Schwinger correction does not help. The 24-cell provides partial structural justification.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 80)
    print(" PHASE 18 — 24-CELL, SCHWINGER CORRECTION, EXPONENT DERIVATION")
    print("=" * 80)

    results = {}
    results["phase18a_24cell"] = phase18a_24cell()
    results["phase18b_schwinger"] = phase18b_schwinger()
    results["phase18c_corrected"] = phase18c_corrected_formula()
    results["phase18d_null_model"] = phase18d_null_model()
    results["phase18e_assessment"] = phase18e_assessment(
        results["phase18a_24cell"],
        results["phase18b_schwinger"],
        results["phase18c_corrected"],
        results["phase18d_null_model"],
    )

    print()
    print("=" * 80)
    print(" PHASE 18 SUMMARY")
    print("=" * 80)
    print(f"  18A: 24-cell partially justifies exponent 4 (for 24, not 29)")
    print(f"  18B: Schwinger correction is FALSE (12.6× too large)")
    print(f"  18C: Exact correction ≈ α²×√3 (not a known QED quantity)")
    print(f"  18D: Null model with fixed exponent 4: {results['phase18d_null_model']['null_model_fixed_exp4']['n_match']}/50000")
    print(f"  18E: Phase 17's 0.009% remains best; Schwinger doesn't help")

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[Saved] {OUT_PATH}")


if __name__ == "__main__":
    main()
