"""
Phase 8 — The 'Put a Known Object in the Path' Experiment

The user's productive framing: instead of fitting formulas to constants,
put a known physical object (a medium) in the path of light and see if
the UBP model reproduces the correct behavior (refraction, refractive index).

The framework's document proposes:
  - Light in vacuum: c = 1.0 (substrate speed limit)
  - In a medium: phase shift Δφ < 90°, v = c·sin(Δφ), n = 1/sin(Δφ)
  - The 48° phase shift gives n ≈ 1.3456, matching water (n = 1.333) within 0.9%
  - 48° is claimed to be the "Lucas-Lehmer trisection angle (144°/3)"

This phase audits:
  8A: Reproduce the simulation; verify the 48° → n=1.3456 claim
  8B: Test against REAL refractive indices of 10 materials — does UBP predict each?
  8C: Null-model test — how often does a random angle match some real material?
  8D: Test Snell's law behavior — does the UBP model reproduce angled refraction?
  8E: Audit the 48° "Lucas-Lehmer trisection" derivation — derived or fabricated?
  8F: Constructive assessment — is this a real prediction or post-hoc fitting?

All results saved to /home/z/my-project/work/phase8_results.json
"""
from __future__ import annotations
import json
import math
import sys
import time
import os
import random
from fractions import Fraction as F
from typing import Any
import itertools

import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from ubp_constants import PI, PHI, E, Y_INV, Y, MONAD, WOBBLE, L, U_E, SIGMA, C_SI

OUT_PATH = "/home/z/my-project/work/phase8_results.json"

# Real refractive indices (CODATA / standard optics references)
REAL_MATERIALS = [
    ("Vacuum",           1.00000,  "Reference"),
    ("Air (STP, 0°C)",   1.00029,  "Atmospheric"),
    ("Water (20°C)",     1.33300,  "Common liquid"),
    ("Ethanol",          1.36100,  "Common liquid"),
    ("Glass (crown)",    1.52000,  "Optical glass"),
    ("Glass (flint)",    1.62000,  "Optical glass"),
    ("Sapphire",         1.77000,  "Crystal"),
    ("Diamond",          2.41700,  "Crystal"),
    ("Silicon",          3.42000,  "Semiconductor (IR)"),
    ("Germanium",        4.00000,  "Semiconductor (IR)"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8A — Reproduce the UBP light-obstacle simulation
# ─────────────────────────────────────────────────────────────────────────────

def phase8a_reproduce_simulation() -> dict:
    """Reproduce the UBP light-obstacle simulation and verify the 48° → n=1.3456 claim."""
    print("=" * 80)
    print("[8A] REPRODUCING THE UBP LIGHT-OBSTACLE SIMULATION")
    print("=" * 80)

    # Base photon
    octads = GOLAY_ENGINE.get_octads()
    photon_vec = octads[0]
    tax_vacuum = float(LEECH_ENGINE.calculate_symmetry_tax(photon_vec))
    nrci_vacuum = float(F(10, 1) / (F(10, 1) + LEECH_ENGINE.calculate_symmetry_tax(photon_vec)))

    print(f"Vacuum Photon: Tax={tax_vacuum:.4f}, NRCI={nrci_vacuum:.4f}")

    # The 48° claim
    phase_deg = 48.0
    v_step = math.sin(math.radians(phase_deg))
    n_effective = 1.0 / v_step
    drift = 1.0 - v_step
    added_tax = tax_vacuum + (drift * float(LEECH_ENGINE.Y) * 12.0)
    nrci_medium = 10.0 / (10.0 + added_tax)

    print(f"\n48° phase shift (the UBP claim):")
    print(f"  v = sin(48°) = {v_step:.4f}")
    print(f"  n = 1/sin(48°) = {n_effective:.4f}")
    print(f"  Water n = 1.333")
    print(f"  Error vs water = {abs(n_effective - 1.333)/1.333*100:.2f}%")
    print(f"  Added Tax = {added_tax:.4f}")
    print(f"  NRCI in medium = {nrci_medium:.4f} (above 0.70 barrier: {nrci_medium >= 0.70})")

    # The "instant speed restoration" claim
    print(f"\nThe 'instant speed restoration' claim:")
    print(f"  At Tick 10 (exiting medium), v snaps from {v_step:.4f} back to 1.0000")
    print(f"  This is presented as a UBP discovery.")
    print(f"  REALITY: This is standard wave mechanics. Phase velocity in a medium")
    print(f"  is c/n; when the wave exits, it returns to c. This is not a discovery;")
    print(f"  it's a restatement of how refraction works in any wave model.")

    return {
        "photon_baseline": {
            "tax": tax_vacuum,
            "nrci": nrci_vacuum,
        },
        "ubp_48deg_claim": {
            "phase_deg": 48.0,
            "velocity": v_step,
            "refractive_index": n_effective,
            "water_target": 1.333,
            "error_vs_water_pct": abs(n_effective - 1.333)/1.333 * 100,
            "added_tax": added_tax,
            "nrci_in_medium": nrci_medium,
            "above_manifestation_barrier": nrci_medium >= 0.70,
        },
        "instant_restoration_claim": {
            "finding": "The 'instant speed restoration' is standard wave mechanics (phase velocity returns to c when exiting medium), not a UBP discovery.",
        },
        "verdict": "The 48° → n=1.3456 → water (0.95% error) claim is reproduced. But this is one data point, and the 'instant restoration' is standard physics, not a discovery.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8B — Test against REAL refractive indices of 10 materials
# ─────────────────────────────────────────────────────────────────────────────

def phase8b_multiple_materials() -> dict:
    """Test the UBP model against real refractive indices of 10 materials.
    Does the model predict the right n for each?"""
    print()
    print("=" * 80)
    print("[8B] TESTING UBP MODEL AGAINST 10 REAL MATERIALS")
    print("=" * 80)
    print("If UBP can predict refractive indices, it should work for ALL materials,")
    print("not just water. Let's see what angle each material requires.")
    print()

    print(f"{'Material':<22} {'n (real)':>10} {'θ = arcsin(1/n)':>18} {'Is θ a UBP angle?':>20}")
    print("-" * 75)

    results = []
    for name, n_real, category in REAL_MATERIALS:
        if n_real >= 1.0 and n_real <= 100:
            theta_required = math.degrees(math.asin(1.0 / n_real))
            # Is this angle a "nice" UBP angle? (integer, or derived from substrate?)
            is_integer = abs(theta_required - round(theta_required)) < 0.5
            results.append({
                "material": name,
                "n_real": n_real,
                "theta_required": theta_required,
                "theta_rounded": round(theta_required),
                "is_integer_angle": is_integer,
                "category": category,
            })
            print(f"{name:<22} {n_real:>10.5f} {theta_required:>15.2f}° {'YES (integer)' if is_integer else 'NO':>20}")

    print()
    print("FINDING: Different materials require different angles (14° to 90°).")
    print("  Water: 48.61° (close to UBP's 48°)")
    print("  Diamond: 24.44° (NOT close to any obvious UBP angle)")
    print("  Silicon: 17.00° (integer, but why 17?)")
    print("  Glass (crown): 41.14° (NOT integer)")
    print()
    print("The UBP model only provides ONE angle (48°) for ONE material (water).")
    print("It does NOT predict the refractive indices of other materials.")
    print("A real model of refraction must explain ALL materials, not just one.")

    return {
        "materials_tested": results,
        "finding": "The UBP model provides one angle (48°) for one material (water). It does not predict the refractive indices of the other 9 materials tested. A real model of refraction must explain all materials.",
        "verdict": "The UBP model is not a model of refraction; it is a single data point cherry-picked to match water.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8C — Null-model test: how often does a random angle match a material?
# ─────────────────────────────────────────────────────────────────────────────

def phase8c_null_model() -> dict:
    """Null model: if you pick a random angle, how often does 1/sin(θ) match
    some real material's refractive index within 2%?"""
    print()
    print("=" * 80)
    print("[8C] NULL-MODEL TEST: RANDOM ANGLES vs REAL MATERIALS")
    print("=" * 80)
    print("If you pick a random angle θ, n = 1/sin(θ) will match SOME real material")
    print("within 2% a certain fraction of the time. This is the null model.")
    print()

    # Test all integer angles 1° to 89°
    n_matches_within_2pct = 0
    n_matches_within_1pct = 0
    n_matches_within_0_5pct = 0
    matches = []

    for deg in range(1, 90):
        n_val = 1.0 / math.sin(math.radians(deg))
        # Find closest material (excluding vacuum)
        best_match = None
        best_err = float('inf')
        for name, n_real, _ in REAL_MATERIALS:
            if name == "Vacuum":
                continue
            if n_real > 0:
                err = abs(n_val - n_real) / n_real
                if err < best_err:
                    best_err = err
                    best_match = name

        if best_err < 0.02:
            n_matches_within_2pct += 1
            matches.append({"angle": deg, "n": n_val, "material": best_match, "error_pct": best_err * 100})
        if best_err < 0.01:
            n_matches_within_1pct += 1
        if best_err < 0.005:
            n_matches_within_0_5pct += 1

    total_angles = 89
    print(f"Integer angles 1° to 89° ({total_angles} angles):")
    print(f"  Match some real material within 2.0%: {n_matches_within_2pct}/{total_angles} ({n_matches_within_2pct/total_angles*100:.1f}%)")
    print(f"  Match some real material within 1.0%: {n_matches_within_1pct}/{total_angles} ({n_matches_within_1pct/total_angles*100:.1f}%)")
    print(f"  Match some real material within 0.5%: {n_matches_within_0_5pct}/{total_angles} ({n_matches_within_0_5pct/total_angles*100:.1f}%)")
    print()

    print(f"All matches within 2%:")
    print(f"  {'Angle':>6} {'n = 1/sin(θ)':>14} {'Closest material':<22} {'Error %':>10}")
    print("  " + "-" * 55)
    for m in matches:
        print(f"  {m['angle']:>5}° {m['n']:>14.4f} {m['material']:<22} {m['error_pct']:>10.2f}%")

    print()
    print(f"FINDING: {n_matches_within_2pct}/{total_angles} ({n_matches_within_2pct/total_angles*100:.1f}%) of integer angles match some real material within 2%.")
    print(f"  The UBP's 48° → water match is one of {n_matches_within_2pct} such matches.")
    print(f"  This is NOT a prediction; it's a coincidence.")
    print(f"  Any angle in {sorted([m['angle'] for m in matches])} would give a comparable 'match'.")
    print()

    # The specific 48° claim
    ubp_match = next((m for m in matches if m["angle"] == 48), None)
    if ubp_match:
        print(f"The UBP's specific claim (48° → water):")
        print(f"  Error: {ubp_match['error_pct']:.2f}%")
        # How many other angles match water even better?
        water_matches = [m for m in matches if m["material"] == "Water (20°C)"]
        water_matches_sorted = sorted(water_matches, key=lambda x: x["error_pct"])
        print(f"  Angles that match water within 2%: {len(water_matches)}")
        print(f"  Best angle for water: {water_matches_sorted[0]['angle']}° (error {water_matches_sorted[0]['error_pct']:.2f}%)")
        print(f"  48° is the {next(i+1 for i, m in enumerate(water_matches_sorted) if m['angle'] == 48)}th best angle for water.")

    return {
        "total_angles_tested": total_angles,
        "matches_within_2pct": n_matches_within_2pct,
        "matches_within_1pct": n_matches_within_1pct,
        "matches_within_0_5pct": n_matches_within_0_5pct,
        "fraction_within_2pct": n_matches_within_2pct / total_angles,
        "all_matches": matches,
        "ubp_48deg_context": {
            "error_vs_water": ubp_match["error_pct"] if ubp_match else None,
            "rank_for_water": next((i+1 for i, m in enumerate(sorted([m for m in matches if m["material"] == "Water (20°C)"], key=lambda x: x["error_pct"])) if m["angle"] == 48), None),
            "finding": "48° is just one of many integer angles that match some real material. It is not a unique prediction.",
        },
        "verdict": f"{n_matches_within_2pct}/{total_angles} ({n_matches_within_2pct/total_angles*100:.1f}%) of integer angles match some real material within 2%. The UBP's 48° → water match is a coincidence, not a prediction.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8D — Test Snell's law behavior
# ─────────────────────────────────────────────────────────────────────────────

def phase8d_snells_law() -> dict:
    """Test whether the UBP model reproduces Snell's law correctly.
    Snell's law: sin(θ1)/sin(θ2) = n2/n1 = v1/v2

    The UBP model says v = c·sin(Δφ) where Δφ is the phase angle.
    For this to reproduce Snell's law, the phase angle must transform
    correctly at the interface."""
    print()
    print("=" * 80)
    print("[8D] SNELL'S LAW TEST")
    print("=" * 80)
    print("Snell's law: sin(θ1)/sin(θ2) = n2/n1 = v1/v2")
    print()
    print("The UBP model says v = c·sin(Δφ). For Snell's law to emerge:")
    print("  sin(θ1)/sin(θ2) = sin(Δφ1)/sin(Δφ2)")
    print("  where Δφ1 is the phase angle in medium 1, Δφ2 in medium 2.")
    print()
    print("This means the UBP model CAN reproduce Snell's law IF the phase angle")
    print("transforms as sin(Δφ) at the interface. But this is just RESTATING")
    print("Snell's law in different notation — it's not a derivation.")
    print()

    # Test: does the UBP model predict the CORRECT refraction angle for a known scenario?
    # Scenario: light enters water (n=1.333) at 30° from normal
    # Snell's law: sin(30°)/sin(θ2) = 1.333 → sin(θ2) = sin(30°)/1.333 = 0.375 → θ2 = 22.0°
    theta1 = 30.0
    n_water = 1.333
    sin_theta2 = math.sin(math.radians(theta1)) / n_water
    theta2_snell = math.degrees(math.asin(sin_theta2))

    print(f"Scenario: light enters water (n=1.333) at θ1 = {theta1}°")
    print(f"  Snell's law: θ2 = {theta2_snell:.2f}°")
    print()

    # UBP model: what phase angle does water correspond to?
    # UBP says n = 1/sin(Δφ), so sin(Δφ) = 1/n = 1/1.333 = 0.750, Δφ = 48.6°
    delta_phi_water = math.degrees(math.asin(1.0 / n_water))
    print(f"  UBP: water corresponds to Δφ = {delta_phi_water:.2f}° (they use 48°)")
    print(f"  UBP: v_in_water = sin(48°) = {math.sin(math.radians(48)):.4f}")
    print()

    # For the UBP model to predict θ2, it would need to derive θ2 from Δφ
    # But the UBP model only gives v = c·sin(Δφ). It does NOT give a refraction angle.
    # The refraction angle comes from Snell's law, which the UBP model assumes, not derives.
    print(f"  PROBLEM: The UBP model gives v = c·sin(Δφ), but does NOT give a refraction angle.")
    print(f"  To get θ2, you must USE Snell's law directly.")
    print(f"  The UBP model does not DERIVE Snell's law; it ASSUMES it.")
    print()

    # The deeper issue: the UBP model is just a relabeling
    print(f"  DEEPER ISSUE: The UBP model is just a relabeling of standard optics:")
    print(f"    Standard: v = c/n")
    print(f"    UBP:      v = c·sin(Δφ), where sin(Δφ) = 1/n")
    print(f"    These are identical: v = c·(1/n) = c/n")
    print(f"  The UBP model adds the variable Δφ = arcsin(1/n) but this is just")
    print(f"  a coordinate change. It does not add any new physics.")
    print()

    # Test with multiple scenarios
    print(f"Multiple refraction scenarios (all just apply Snell's law):")
    scenarios = [
        ("Air → Water", 1.00029, 1.333, 30.0),
        ("Air → Glass", 1.00029, 1.520, 45.0),
        ("Water → Air", 1.333, 1.00029, 30.0),
        ("Glass → Diamond", 1.520, 2.417, 20.0),
    ]
    print(f"  {'Scenario':<20} {'θ1':>6} {'n1':>8} {'n2':>8} {'θ2 (Snell)':>12} {'UBP Δφ2':>10}")
    print("  " + "-" * 65)
    for name, n1, n2, t1 in scenarios:
        t2 = math.degrees(math.asin(math.sin(math.radians(t1)) * n1 / n2)) if n1/n2 * math.sin(math.radians(t1)) <= 1 else 90.0
        delta_phi2 = math.degrees(math.asin(1.0/n2)) if n2 >= 1 else 90.0
        print(f"  {name:<20} {t1:>5.0f}° {n1:>8.4f} {n2:>8.4f} {t2:>11.2f}° {delta_phi2:>9.2f}°")

    print()
    print(f"  FINDING: The UBP model computes θ2 by APPLYING Snell's law, not deriving it.")
    print(f"  The Δφ2 column is just arcsin(1/n2), which is a relabeling of n2.")
    print(f"  No new physics is added.")

    return {
        "snells_law_test": {
            "scenario": "Light enters water at 30°",
            "snell_theta2": theta2_snell,
            "ubp_approach": "Applies Snell's law directly; does not derive it",
        },
        "relabeling_finding": {
            "standard": "v = c/n",
            "ubp": "v = c·sin(Δφ) where sin(Δφ) = 1/n",
            "identical": True,
            "finding": "The UBP model is a coordinate change (n → Δφ = arcsin(1/n)), not new physics.",
        },
        "verdict": "The UBP model does not derive Snell's law; it assumes it. The variable Δφ is just a relabeling of n. No new physics is added.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8E — Audit the 48° "Lucas-Lehmer trisection" claim
# ─────────────────────────────────────────────────────────────────────────────

def phase8e_lucas_lehmer_audit() -> dict:
    """Audit the claim that 48° = 144°/3 where 144° is a 'Lucas-Lehmer trisection angle'."""
    print()
    print("=" * 80)
    print("[8E] AUDIT: THE 48° 'LUCAS-LEHMER TRISECTION' CLAIM")
    print("=" * 80)
    print("The document claims: '48° is the Lucas-Lehmer trisection angle (144°/3)'")
    print("This is presented as the derivation of why 48° is special.")
    print()

    # 1. Is 144 in the Lucas-Lehmer sequence?
    print(f"[1] Is 144 in the Lucas-Lehmer sequence?")
    # Lucas-Lehmer sequence: s(0)=4, s(n+1) = s(n)^2 - 2
    # Used to test Mersenne primes: M_p is prime iff s(p-2) ≡ 0 (mod M_p)
    ll_seq = [4]
    for i in range(8):
        ll_seq.append(ll_seq[-1]**2 - 2)
    print(f"  Lucas-Lehmer sequence (first 9 terms): {ll_seq}")
    print(f"  144 in sequence? {144 in ll_seq}")
    print(f"  => The 'Lucas-Lehmer' label is FABRICATED. 144 is not a Lucas-Lehmer number.")
    print()

    # 2. What is 144 actually?
    print(f"[2] What is 144 actually?")
    # 144 = 12^2
    # 144 = Fibonacci number F(12)
    fib = [0, 1]
    for i in range(20):
        fib.append(fib[-1] + fib[-2])
    print(f"  144 = 12² = {12**2}")
    print(f"  144 = Fibonacci F(12) = {fib[12]}")
    print(f"  144 = 2^4 × 3² = {2**4 * 3**2}")
    print(f"  144 is a 'gross' (12 dozen)")
    print(f"  None of these are 'Lucas-Lehmer'.")
    print()

    # 3. Why 144°/3 = 48°?
    print(f"[3] Why 144°/3 = 48°?")
    print(f"  144°/3 = 48° (arithmetic fact)")
    print(f"  But WHY 144°? And WHY divide by 3?")
    print(f"  The document does not explain why 144° is special or why trisection is meaningful.")
    print(f"  The 'trisection' label suggests angle trisection (a classical geometric problem),")
    print(f"  but 144°/3 = 48° is just division, not trisection of an arbitrary angle.")
    print()

    # 4. Is 48° derived from any UBP substrate object?
    print(f"[4] Is 48° derived from any UBP substrate object?")
    substrate_objects = {
        "Y": float(Y),
        "Y_inv": float(Y_INV),
        "MONAD": float(MONAD),
        "wobble": float(WOBBLE),
        "L": float(L),
        "U_e": float(U_E),
        "sigma": float(SIGMA),
        "pi": float(PI),
        "phi": float(PHI),
        "e": float(E),
    }
    print(f"  Checking if 48 or 48° can be derived from substrate objects:")
    found_derivations = []
    for name, val in substrate_objects.items():
        # Check various simple operations
        if abs(val - 48) < 0.1:
            found_derivations.append(f"{name} = {val:.6f} ≈ 48")
        if abs(val * 180 / math.pi - 48) < 0.5:  # radians to degrees
            found_derivations.append(f"{name} in degrees = {val*180/math.pi:.2f}° ≈ 48°")
        if abs(math.degrees(val) - 48) < 0.5:
            found_derivations.append(f"degrees({name}) = {math.degrees(val):.2f}° ≈ 48°")
        if abs(1/val * 180 - 48) < 1:
            found_derivations.append(f"(1/{name})×180 = {1/val*180:.2f} ≈ 48")

    if found_derivations:
        print(f"  Found: {found_derivations}")
    else:
        print(f"  No substrate object gives 48 or 48° under simple operations.")
        print(f"  48° is NOT derived from the UBP substrate. It is a chosen value.")
    print()

    # 5. The real source of 48°
    print(f"[5] The real source of 48°:")
    print(f"  48° was chosen BECAUSE sin(48°) = 1/1.3456, which is close to 1/n_water = 1/1.333.")
    print(f"  The 'Lucas-Lehmer trisection' label was added AFTER finding that 48° works.")
    print(f"  This is post-hoc justification, not derivation.")
    print()

    # 6. What angle would EXACTLY match water?
    exact_water_angle = math.degrees(math.asin(1.0/1.333))
    print(f"[6] What angle would EXACTLY match water?")
    print(f"  arcsin(1/1.333) = {exact_water_angle:.4f}°")
    print(f"  UBP uses 48° (off by {abs(48 - exact_water_angle):.2f}°)")
    print(f"  If UBP used {exact_water_angle:.2f}°, the match would be exact.")
    print(f"  Why didn't they? Because {exact_water_angle:.2f}° doesn't have a 'nice' label")
    print(f"  like 'Lucas-Lehmer trisection'. 48° was chosen for marketability, not accuracy.")

    return {
        "lucas_lehmer_check": {
            "ll_sequence": ll_seq,
            "144_in_sequence": 144 in ll_seq,
            "finding": "144 is NOT in the Lucas-Lehmer sequence. The label is fabricated.",
        },
        "what_is_144": {
            "value": 144,
            "identities": ["12²", "Fibonacci F(12)", "2⁴×3²", "one gross"],
            "none_are_lucas_lehmer": True,
        },
        "substrate_derivation": {
            "found_derivations": found_derivations,
            "finding": "48° is not derivable from UBP substrate objects under simple operations.",
        },
        "real_source": {
            "exact_water_angle": exact_water_angle,
            "ubp_uses": 48.0,
            "error_degrees": abs(48.0 - exact_water_angle),
            "finding": "48° was chosen because sin(48°) ≈ 1/n_water. The 'Lucas-Lehmer' label was added post-hoc.",
        },
        "verdict": "The 48° 'Lucas-Lehmer trisection' derivation is fabricated. 144 is not a Lucas-Lehmer number. 48° was chosen because it matches water's refractive index, and a mathematical label was invented to justify it.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8F — Constructive assessment
# ─────────────────────────────────────────────────────────────────────────────

def phase8f_assessment(p8a, p8b, p8c, p8d, p8e) -> dict:
    """Constructive assessment: is this a real prediction or post-hoc fitting?"""
    print()
    print("=" * 80)
    print("[8F] CONSTRUCTIVE ASSESSMENT")
    print("=" * 80)

    print("The user's question: 'put a known object in the path of light and see which")
    print("model does the correct thing.'")
    print()
    print("This is the right experimental design. The audit's findings:")
    print()
    print("1. The UBP model CAN reproduce one data point (water, n=1.333) within 0.95%.")
    print()
    print("2. BUT this is one of 22 integer angles that match some real material within 2%.")
    print(f"   {p8c['fraction_within_2pct']*100:.1f}% of integer angles match SOME material.")
    print("   The UBP's 48° → water match is a coincidence, not a prediction.")
    print()
    print("3. The UBP model does NOT predict refractive indices for other materials.")
    print("   Diamond (n=2.417), glass (n=1.520), silicon (n=3.420) — none are predicted.")
    print()
    print("4. The UBP model does NOT derive Snell's law. It ASSUMES Snell's law and")
    print("   relabels n as Δφ = arcsin(1/n). This is a coordinate change, not new physics.")
    print()
    print("5. The 48° 'Lucas-Lehmer trisection' derivation is FABRICATED. 144 is not in")
    print("   the Lucas-Lehmer sequence. The label was invented to justify the chosen angle.")
    print()
    print("6. The 'instant speed restoration' is standard wave mechanics, not a UBP discovery.")
    print()
    print("OVERALL ASSESSMENT:")
    print()
    print("The 'put a known object in the path' experiment is the RIGHT approach, but the")
    print("UBP model fails it. The model:")
    print("  - Matches ONE material (water) by coincidence")
    print("  - Does not predict the other 9 materials tested")
    print("  - Does not derive Snell's law (just relabels it)")
    print("  - Uses a fabricated mathematical label for the chosen angle")
    print()
    print("WHAT WOULD MAKE THIS A REAL PREDICTION:")
    print()
    print("For the UBP model to genuinely predict refractive indices, it would need to:")
    print("  1. Derive the phase angle Δφ for EACH material from the material's substrate")
    print("     representation (e.g., from the bit pattern of the medium)")
    print("  2. Predict n = 1/sin(Δφ) for each material BEFORE measuring it")
    print("  3. Match all 10 materials (not just water) within measurement uncertainty")
    print("  4. Derive Snell's law from substrate principles (not assume it)")
    print()
    print("None of these are met. The UBP model is a relabeling of standard optics")
    print("with one cherry-picked match to water.")

    return {
        "summary": {
            "n_materials_predicted": 1,
            "n_materials_tested": 10,
            "null_model_match_rate": p8c["fraction_within_2pct"],
            "snells_law_derived": False,
            "lucas_lehmer_valid": False,
            "instant_restoration_is_new": False,
        },
        "what_would_make_real": [
            "Derive Δφ for each material from its substrate representation",
            "Predict n for each material before measuring",
            "Match all 10 materials within measurement uncertainty",
            "Derive Snell's law from substrate principles",
        ],
        "verdict": (
            "The 'put a known object in the path' experiment is the right approach, but the UBP model fails it. "
            "The model matches one material (water) by coincidence (1 of 22 integer angles that match some material), "
            "does not predict the other 9 materials, does not derive Snell's law (just relabels it), "
            "and uses a fabricated 'Lucas-Lehmer trisection' label for the chosen angle."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 80)
    print(" PHASE 8 — THE 'PUT A KNOWN OBJECT IN THE PATH' EXPERIMENT")
    print("=" * 80)
    print(f" Source: User's 'put a known object in the path' framing + UBP light-obstacle sim")
    print(f" Stance: Neutral scientist, Popperian falsificationism")
    print("=" * 80)

    results = {
        "metadata": {
            "source": "User's 'put a known object in the path' framing + UBP light-obstacle simulation",
            "phases_audited": [
                "8A: Reproduce the UBP light-obstacle simulation",
                "8B: Test against 10 real materials",
                "8C: Null-model test (random angles vs real materials)",
                "8D: Snell's law test",
                "8E: Lucas-Lehmer trisection audit",
                "8F: Constructive assessment",
            ],
        },
    }

    p8a = phase8a_reproduce_simulation()
    p8b = phase8b_multiple_materials()
    p8c = phase8c_null_model()
    p8d = phase8d_snells_law()
    p8e = phase8e_lucas_lehmer_audit()
    p8f = phase8f_assessment(p8a, p8b, p8c, p8d, p8e)

    results["phase8a_simulation"] = p8a
    results["phase8b_materials"] = p8b
    results["phase8c_null_model"] = p8c
    results["phase8d_snells_law"] = p8d
    results["phase8e_lucas_lehmer"] = p8e
    results["phase8f_assessment"] = p8f

    # Summary
    print()
    print("=" * 80)
    print(" PHASE 8 SUMMARY")
    print("=" * 80)
    print(f"  8A: 48° → n=1.3456 reproduced (0.95% vs water)")
    print(f"  8B: UBP predicts 1/10 materials (water only)")
    print(f"  8C: {p8c['fraction_within_2pct']*100:.1f}% of integer angles match SOME material — 48° is a coincidence")
    print(f"  8D: UBP does not derive Snell's law; it relabels n as Δφ")
    print(f"  8E: 'Lucas-Lehmer trisection' is FABRICATED (144 not in LL sequence)")
    print(f"  8F: Model fails the 'put a known object in the path' test")

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[Saved] {OUT_PATH}")


if __name__ == "__main__":
    main()
