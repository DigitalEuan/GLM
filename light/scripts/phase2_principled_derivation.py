"""
Phase 2 — Principled derivation attempt.

Goal: try to derive c from UBP first principles WITHOUT search.

Approach:
  1. State the dimensional analysis problem (Buckingham Pi).
  2. State the SI-definition problem (c = 299792458 by definition since 1983).
  3. Attempt a small number of "natural" derivations from UBP substrate objects
     (Leech minimal vector count, Golay codeword count, Monad, Y, etc.) and
     document how far each lands from c.
  4. Attempt an a-priori derivation that does not consult the target value.

The goal is not to find a formula that works, but to honestly test whether
ANY principled derivation can land near c without parameter fitting.
"""
from __future__ import annotations
import json
import math
from fractions import Fraction as F
from typing import Any

from ubp_constants import PI, PHI, E, Y_INV, Y, MONAD, WOBBLE, L, U_E, SIGMA, C_SI

OUT_PATH = "/home/z/my-project/work/phase2_results.json"
TARGET = float(C_SI)

# UBP substrate object counts (from README §4)
LEECH_MINIMAL_VECTORS = 196_560          # |Λ_24 kissing sphere|
GOLAY_CODEWORDS        = 4_096           # |[24,12,8] code|
GOLAY_OCTADS           = 759             # weight-8 codewords
LEECH_NORM2            = 32              # minimal norm² (scaled ×8)
LEECH_NORM2_PHYSICAL   = 4               # physical norm²
MONSTER_GROUP_ORDER    = 808017424794512875886459904961710757005754368000000000  # |M|

# Other UBP structural numbers
N_DIMS                 = 24
N_HEXACODE_SYMBOLS     = 6
N_HEXACODE_ALPHABET    = 4
N_MOOD_GRID            = 24              # 4×6 MOG cells
N_GOLAY_ERROR_CORRECT  = 3               # bits correctable
N_GOLAY_DETECT         = 7               # bits detectable


def dimensional_analysis_block() -> dict:
    """
    Buckingham Pi theorem analysis.

    c has dimensions [L][T]^-1.
    UBP substrate objects (Golay code, Leech lattice, Y, MONAD, etc.) are
    dimensionless pure numbers.

    By Buckingham Pi: any function of dimensionless inputs is dimensionless.
    Therefore UBP cannot produce a quantity with dimensions [L][T]^-1 without
    an external dimensional anchor (a length scale, a time scale, or a
    dimensionful constant like ℏ, G, or k_B).

    The user's formula 13 · U_E · MONAD² · Y⁻³ · L · σ⁵ is a product of
    dimensionless numbers, so its output is dimensionless. The number
    299,800,508 happens to be close to c expressed in m/s — but m/s is a
    unit choice, not a fact of nature.
    """
    return {
        "claim": "UBP substrate is dimensionless; c has dimensions [L][T]^-1",
        "substrate_objects": [
            {"name": "Golay code [24,12,8]",   "type": "pure integer", "dimensions": "none"},
            {"name": "Leech lattice Λ_24",      "type": "integer lattice", "dimensions": "none (norm²=32 in scaled rep)"},
            {"name": "Y = 1/(π+2/π)",            "type": "dimensionless", "dimensions": "none"},
            {"name": "MONAD = π·φ·e",            "type": "dimensionless", "dimensions": "none"},
            {"name": "WOBBLE = frac(MONAD)",     "type": "dimensionless", "dimensions": "none"},
            {"name": "U_E = 24³",                "type": "dimensionless integer", "dimensions": "none"},
            {"name": "σ = 29/24",                "type": "dimensionless rational", "dimensions": "none"},
        ],
        "target_c": {"name": "speed of light", "value_si": 299792458, "dimensions": "[L][T]^-1"},
        "buckingham_pi_verdict": (
            "A function of dimensionless inputs is dimensionless. "
            "UBP cannot produce c in m/s without an external dimensional anchor "
            "(ℏ, G, k_B, or a chosen unit scale). The match between a dimensionless "
            "UBP output and the SI numerical value of c is therefore a coincidence "
            "of unit choice, not a physical prediction."
        ),
        "si_definition_problem": (
            "Since 1983, c = 299,792,458 m/s is exact by SI definition. The meter is "
            "defined as the distance light travels in 1/299,792,458 s; the second is "
            "defined by the Cs-133 hyperfine transition (Δν_Cs = 9,192,631,770 Hz exactly). "
            "Matching 299,792,458 is matching a convention, not a fact of nature. "
            "To genuinely predict c, UBP would need to derive either Δν_Cs or the SI "
            "choice of meter/second — neither of which the substrate addresses."
        ),
    }


def attempt_natural_derivations() -> list[dict]:
    """
    Try a small set of derivations that one might motivate from UBP first principles,
    WITHOUT consulting the target. For each, report the value and the ratio to c.

    These are not exhaustive — they are representative 'natural' constructions
    a UBP theorist might write down on the back of an envelope.
    """
    attempts = []

    # ─── Attempt 1: c as a count of substrate atoms ─────────────────────────
    # "Maybe c is the number of minimal Leech vectors times something."
    attempts.append({
        "id": "D1",
        "rationale": "c ≈ |Λ_24 minimal vectors| × Y × (scale factor)",
        "formula": "|Λ_24| × Y",
        "value": LEECH_MINIMAL_VECTORS * float(Y),
        "expected_to_be_near": TARGET,
    })
    attempts.append({
        "id": "D2",
        "rationale": "c ≈ |Λ_24| × |Golay| (substrate atom count)",
        "formula": "|Λ_24| × |Golay|",
        "value": LEECH_MINIMAL_VECTORS * GOLAY_CODEWORDS,
        "expected_to_be_near": TARGET,
    })
    attempts.append({
        "id": "D3",
        "rationale": "c ≈ 24^k for some k (24D unit volume)",
        "formula": "24^6",
        "value": 24**6,
        "expected_to_be_near": TARGET,
    })
    attempts.append({
        "id": "D4",
        "rationale": "c ≈ 24^k for some k",
        "formula": "24^7",
        "value": 24**7,
        "expected_to_be_near": TARGET,
    })

    # ─── Attempt 2: c as a Leech-norm-based quantity ────────────────────────
    # Minimal Leech vector has norm² = 32 (scaled) = 4 (physical). Maybe c is
    # related to this length scale.
    leech_length = math.sqrt(LEECH_NORM2)  # √32 = 4√2 ≈ 5.657
    attempts.append({
        "id": "D5",
        "rationale": "c ≈ √(Leech norm²) × something",
        "formula": "√32 × |Λ_24|",
        "value": leech_length * LEECH_MINIMAL_VECTORS,
        "expected_to_be_near": TARGET,
    })

    # ─── Attempt 3: c as a Y-resonance ─────────────────────────────────────
    # Y is the 'Observer' constant ≈ 0.2647. Maybe c = k / Y^n for small k, n.
    for n in [1, 2, 3, 4, 5, 6]:
        attempts.append({
            "id": f"D{5+n}",
            "rationale": f"c ≈ k × Y^(-{n}) for small integer k",
            "formula": f"Y^(-{n})",
            "value": float(Y) ** (-n),
            "expected_to_be_near": TARGET,
        })

    # ─── Attempt 4: c as a Monad resonance ─────────────────────────────────
    # MONAD ≈ 13.82. Maybe c ≈ MONAD^k for some k.
    for k in [1, 2, 3, 4, 5, 6, 7, 8]:
        attempts.append({
            "id": f"D{11+k}",
            "rationale": f"c ≈ MONAD^{k}",
            "formula": f"MONAD^{k}",
            "value": float(MONAD) ** k,
            "expected_to_be_near": TARGET,
        })

    # ─── Attempt 5: c as a Planck-unit-style ratio ──────────────────────────
    # In Planck units c = 1. Maybe UBP predicts c=1 (trivially).
    attempts.append({
        "id": "D19",
        "rationale": "In natural/Planck units c = 1 (trivial)",
        "formula": "1",
        "value": 1.0,
        "expected_to_be_near": 1.0,  # In Planck units, c IS 1.
        "note": "True in Planck units but provides no information about c in SI.",
    })

    # ─── Attempt 6: c via the 759 Golay octads ─────────────────────────────
    attempts.append({
        "id": "D20",
        "rationale": "c ≈ |Golay octads| × MONAD × Y × ...",
        "formula": "759 × MONAD × Y^(-1)",
        "value": GOLAY_OCTADS * float(MONAD) / float(Y),
        "expected_to_be_near": TARGET,
    })
    attempts.append({
        "id": "D21",
        "rationale": "c ≈ |Golay octads| × 24^4 × Y",
        "formula": "759 × 24^4 × Y",
        "value": GOLAY_OCTADS * (24**4) * float(Y),
        "expected_to_be_near": TARGET,
    })

    # Compute ratios and verdicts
    for a in attempts:
        if a["expected_to_be_near"] == TARGET:
            ratio = a["value"] / TARGET
            log10_ratio = math.log10(ratio) if ratio > 0 else float("-inf")
            a["ratio_to_c"] = ratio
            a["log10_ratio_to_c"] = log10_ratio
            a["order_of_magnitude_off"] = round(abs(log10_ratio))
            a["verdict"] = (
                "HIT" if 0.99 < ratio < 1.01
                else "near miss (within 10×)" if 0.1 < ratio < 10
                else "miss (off by > 10×)"
            )
        else:
            a["ratio_to_c"] = None
            a["log10_ratio_to_c"] = None
            a["order_of_magnitude_off"] = None
            a["verdict"] = "N/A (different target)"

    return attempts


def what_would_be_required() -> dict:
    """
    State explicitly what would need to be true for UBP-c to be a real prediction
    rather than a numerological fit.
    """
    return {
        "requirements": [
            {
                "id": "R1",
                "requirement": "UBP must derive a length scale AND a time scale (or one speed scale) from pure substrate.",
                "status": "NOT MET — UBP substrate is dimensionless",
                "blocking": True,
            },
            {
                "id": "R2",
                "requirement": "The derivation must NOT depend on the target value (no fitting, no search).",
                "status": "NOT MET — current formula was found by search_macro_c.py scanning 1.6M combinations",
                "blocking": True,
            },
            {
                "id": "R3",
                "requirement": "The formula should be UNIQUE: only one natural form should give c, not 38+ candidates within 0.1%.",
                "status": "NOT MET — Phase 1A found 38 formulas within 0.1% and 303 within 1%",
                "blocking": True,
            },
            {
                "id": "R4",
                "requirement": "Random transcendentals should NOT be able to do the same trick.",
                "status": "NOT MET — Phase 1B: 39% of random sets match c at least as well as UBP",
                "blocking": True,
            },
            {
                "id": "R5",
                "requirement": "The formula's information content must exceed the bits it costs to specify (MDL).",
                "status": "NOT MET — Phase 1D: MDL penalty +23 bits",
                "blocking": True,
            },
            {
                "id": "R6",
                "requirement": "The SI value of c (299,792,458) must be a measurable fact, not a definition.",
                "status": "NOT MET — SI c is defined exactly since 1983; matching it is matching a convention",
                "blocking": True,
            },
            {
                "id": "R7",
                "requirement": "Same substrate should predict other c-related quantities (c², Z_0, α) without re-fitting.",
                "status": "TO TEST in Phase 3",
                "blocking": False,
            },
        ],
        "verdict": (
            "6 of 7 necessary conditions for UBP-c to be a real physical prediction are NOT met. "
            "The current formula is best understood as a numerological fit found by combinatorial "
            "search, not as a derivation from UBP first principles."
        ),
    }


def main():
    print("=" * 80)
    print(" PHASE 2 — PRINCIPLED DERIVATION ATTEMPT")
    print("=" * 80)

    print("\n[2.1] Dimensional analysis & SI definition problem")
    da = dimensional_analysis_block()
    print(f"  Substrate objects: {len(da['substrate_objects'])} (all dimensionless)")
    print(f"  Target c: dimensions = {da['target_c']['dimensions']}")
    print(f"  Buckingham Pi verdict: {da['buckingham_pi_verdict'][:100]}...")
    print(f"  SI definition problem: {da['si_definition_problem'][:100]}...")

    print("\n[2.2] Natural derivations (no search, no fitting)")
    attempts = attempt_natural_derivations()
    print(f"  Tried {len(attempts)} natural constructions:")
    print(f"  {'ID':<5} {'Formula':<35} {'Value':>20} {'Ratio to c':>15} {'Verdict':<25}")
    print("  " + "-" * 105)
    for a in attempts:
        val_str = f"{a['value']:,.4f}" if abs(a['value']) < 1e15 else f"{a['value']:.4e}"
        ratio_str = f"{a['ratio_to_c']:.4e}" if a['ratio_to_c'] is not None else "N/A"
        print(f"  {a['id']:<5} {a['formula']:<35} {val_str:>20} {ratio_str:>15} {a['verdict']:<25}")

    n_hits = sum(1 for a in attempts if a['verdict'] == 'HIT')
    n_near = sum(1 for a in attempts if 'near miss' in a['verdict'])
    n_miss = sum(1 for a in attempts if 'miss' in a['verdict'])
    print(f"\n  Summary: {n_hits} HIT, {n_near} near-miss, {n_miss} miss out of {len(attempts)} attempts")

    print("\n[2.3] What would be required for UBP-c to be a real prediction?")
    reqs = what_would_be_required()
    for r in reqs["requirements"]:
        marker = "[BLOCKING]" if r["blocking"] else "[info]"
        print(f"  {marker} {r['id']}: {r['requirement'][:80]}")
        print(f"           Status: {r['status']}")
    print(f"\n  VERDICT: {reqs['verdict']}")

    results = {
        "dimensional_analysis": da,
        "natural_derivations": attempts,
        "derivation_summary": {
            "n_attempts": len(attempts),
            "n_hits": n_hits,
            "n_near_misses": n_near,
            "n_misses": n_miss,
        },
        "requirements_for_real_prediction": reqs,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[Saved] {OUT_PATH}")


if __name__ == "__main__":
    main()
