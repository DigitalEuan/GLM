#!/usr/bin/env python3
"""
GLM Stress Tests — probe actual reasoning vs lookup.

These tests deliberately push the system into territory where
hardcoded answers would fail. The goal is to find where and WHY
it breaks.
"""

import sys
import os
from pathlib import Path
from fractions import Fraction as F

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from GLM import GLM


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_novel_equations(glm):
    """Verify equations the system has never seen in combination."""
    section("TEST 1: Novel equation combinations (not in any test set)")

    # These combine known concepts in ways NOT tested before
    tests = [
        # Should PASS (dimensions + rank + parity all match)
        ("kinetic_energy", "mass*speed^2", True, "KE = ½mv² (kinetic_energy = mass*speed²)"),
        ("gravitational_constant", "force*length^2/mass^2", True, "G = Fr²/m²"),
        ("boltzmann_constant", "energy/temperature", True, "kB = E/T"),
        ("planck_constant", "energy*time", True, "h = Et"),
        ("impulse", "mass*velocity", True, "J = mv (impulse = momentum)"),
        ("action", "momentum*length", True, "S = p·x"),
        ("angular_frequency", "1/time", True, "ω = 1/t"),
        ("wavenumber", "1/length", True, "k = 1/λ"),
        ("energy_density", "pressure", True, "u = p (energy density = pressure)"),
        ("specific_energy", "speed^2", True, "e = v²"),
        # Should FAIL (wrong dimensions)
        ("energy", "mass*speed", False, "E = mc (wrong — missing speed)"),
        ("force", "mass*acceleration^2", False, "F = ma² (wrong — extra acceleration)"),
        ("entropy", "energy", False, "S = E (wrong — missing temperature)"),
        ("voltage", "current*resistance^2", False, "V = IR² (wrong — extra resistance)"),
        ("frequency", "speed", False, "f = v (wrong — different dims)"),
    ]

    passed = 0
    failed = 0
    for lhs, rhs, expected, desc in tests:
        try:
            result = glm.verify(lhs, rhs)
            status = "✓" if result == expected else "✗ WRONG"
            if result != expected:
                failed += 1
                print(f"  {status} {desc}  (got {result}, expected {expected})")
            else:
                passed += 1
                print(f"  {status} {desc}")
        except Exception as e:
            failed += 1
            print(f"  ? {desc}  EXCEPTION: {e}")

    print(f"\n  Result: {passed}/{passed+failed}")
    return failed == 0


def test_formula_derivation_depth(glm):
    """Test formula discovery for unusual target/source combos."""
    section("TEST 2: Formula derivation for unusual combinations")

    tests = [
        ("wavenumber", ["length"], "k = 1/l"),
        ("angular_frequency", ["time"], "ω = 1/t"),
        ("energy_density", ["energy", "volume"], "u = E/V"),
        ("specific_energy", ["energy", "mass"], "e = E/m"),
        ("impulse", ["mass", "velocity"], "J = mv"),
        ("action", ["energy", "time"], "S = Et"),
        ("power", ["energy", "time"], "P = E/t"),
        ("voltage", ["energy", "charge"], "V = E/Q"),
        ("capacitance", ["charge", "voltage"], "C = Q/V"),
        ("inductance", ["magnetic_flux", "current"], "L = Φ/I"),
        ("resistance", ["voltage", "current"], "R = V/I"),
        # Unusual: derive speed from wavelength and frequency
        ("speed", ["wavelength", "frequency"], "v = λf"),
        # Unusual: derive gravitational_constant from force, mass, length
        ("gravitational_constant", ["force", "length", "mass"], "G = Fl²/m²"),
    ]

    passed = 0
    failed = 0
    for target, sources, expected in tests:
        try:
            result = glm.solve(target, sources)
            formula = result.get("formula", "not found")
            solvable = result.get("solvable", False)
            if solvable:
                passed += 1
                print(f"  ✓ {target} = f({', '.join(sources)}): {formula}")
            else:
                failed += 1
                print(f"  ✗ {target} = f({', '.join(sources)}): NOT SOLVABLE")
        except Exception as e:
            failed += 1
            print(f"  ? {target} = f({', '.join(sources)}): {e}")

    print(f"\n  Result: {passed}/{passed+failed}")
    return failed == 0


def test_meaning_consistency(glm):
    """Check that meanings are mathematically consistent."""
    section("TEST 3: Meaning consistency (energy = force × distance)")

    # If meaning is real, these relationships must hold:
    # energy = force * length  →  L²MT⁻² = LMT⁻² × L
    # momentum = mass * velocity  →  LMT⁻¹ = M × LT⁻¹
    # power = energy / time  →  L²MT⁻³ = L²MT⁻² / T
    # voltage = energy / charge  →  L²MT⁻³I⁻¹ = L²MT⁻² / (TI)

    from reasoner import GLMReasoner
    r = GLMReasoner()

    def get_exps(concept):
        m = r.meaning(concept)
        return {k: F(v) for k, v in m["exponents"].items()}

    def add_exps(a, b):
        return {k: a.get(k, F(0)) + b.get(k, F(0)) for k in set(a) | set(b)}

    def sub_exps(a, b):
        return {k: a.get(k, F(0)) - b.get(k, b.get(k, F(0))) for k in set(a) | set(b)}

    checks = [
        # (concept_a, op, concept_b, should_equal)
        ("energy", "+", None, "force", "length"),      # energy = force + length
        ("momentum", "+", None, "mass", "velocity"),    # momentum = mass + velocity
        ("power", "-", None, "energy", "time"),         # power = energy - time
        ("voltage", "-", None, "energy", "charge"),     # voltage = energy - charge
        ("impulse", "+", None, "force", "time"),        # impulse = force + time
        ("action", "+", None, "energy", "time"),        # action = energy + time
        ("resistance", "-", None, "voltage", "current"),# resistance = voltage - current
    ]

    passed = 0
    failed = 0
    for lhs, op, _, rhs_a, rhs_b in checks:
        try:
            lhs_exp = get_exps(lhs)
            a_exp = get_exps(rhs_a)
            b_exp = get_exps(rhs_b)

            if op == "+":
                expected = add_exps(a_exp, b_exp)
            else:
                expected = sub_exps(a_exp, b_exp)

            match = all(lhs_exp.get(k, F(0)) == expected.get(k, F(0))
                       for k in set(lhs_exp) | set(expected))
            if match:
                passed += 1
                print(f"  ✓ {lhs} = {rhs_a} {op} {rhs_b}  (dimensions match)")
            else:
                failed += 1
                print(f"  ✗ {lhs} ≠ {rhs_a} {op} {rhs_b}")
                print(f"    LHS: {lhs_exp}")
                print(f"    RHS: {expected}")
        except Exception as e:
            failed += 1
            print(f"  ? {lhs} = {rhs_a} {op} {rhs_b}: {e}")

    print(f"\n  Result: {passed}/{passed+failed}")
    return failed == 0


def test_concept_not_in_library(glm):
    """What happens with concepts NOT in the 660 library?"""
    section("TEST 4: Concepts NOT in the library (should fail gracefully)")

    fake_concepts = [
        "dark_energy",
        "quantum_foam",
        "information_entropy_rate",
        "consciousness",
        "gravity_wave_strain",
        "higgs_field_coupling",
    ]

    for c in fake_concepts:
        try:
            m = glm.meaning(c)
            print(f"  !! {c}: MEANING FOUND (unexpected!) dims={m['exponents']}")
        except Exception as e:
            err = str(e)[:60]
            print(f"  ✓ {c}: correctly rejected — {err}")

    print()
    return True


def test_nearest_semantic_quality(glm):
    """Check if nearest neighbours are semantically sensible."""
    section("TEST 5: Nearest neighbour semantic quality")

    tests = [
        ("energy", ["kinetic_energy", "potential_energy", "work"]),
        ("force", ["drag_force", "lift_force"]),
        ("entropy", ["boltzmann_constant"]),
        ("voltage", ["membrane_potential", "cell_voltage", "electrode_potential"]),
        ("frequency", ["angular_frequency"]),
        ("pressure", ["energy_density"]),
        ("current", ["elementary_charge"]),
        ("temperature", ["boltzmann_constant"]),
    ]

    passed = 0
    failed = 0
    for concept, expected_near in tests:
        try:
            nearest = glm.nearest(concept, 5)
            names = [n for n, s in nearest]
            found = [e for e in expected_near if e in names]
            if found:
                passed += 1
                print(f"  ✓ {concept}: found {found} in top 5")
            else:
                failed += 1
                print(f"  ✗ {concept}: expected {expected_near}, got {names}")
        except Exception as e:
            failed += 1
            print(f"  ? {concept}: {e}")

    print(f"\n  Result: {passed}/{passed+failed}")
    return failed == 0


def test_tensor_rank_awareness(glm):
    """Test that the system distinguishes scalars from vectors."""
    section("TEST 6: Tensor rank awareness (scalar vs vector)")

    # These should FAIL because scalar ≠ vector, even though
    # the dimensional exponents (L, M, T) match
    should_fail = [
        ("work", "force*distance", "scalar work ≠ vector force×distance"),
        ("energy", "force*length", "scalar energy ≠ vector force×length"),
        ("pressure", "force/area", "scalar pressure ≠ vector force/area"),
        ("power", "force*velocity", "scalar power ≠ vector force×velocity"),
    ]

    # These should PASS because both sides have the same rank
    should_pass = [
        ("energy", "mass*speed^2", "scalar energy = scalar mass×speed²"),
        ("momentum", "mass*velocity", "vector momentum = scalar×vector"),
        ("impulse", "force*time", "vector impulse = vector×scalar"),
        ("action", "energy*time", "scalar action = scalar×scalar"),
    ]

    print("  Should REJECT (scalar ≠ vector):")
    rej_passed = 0
    rej_failed = 0
    for lhs, rhs, desc in should_fail:
        result = glm.verify(lhs, rhs)
        if not result:
            rej_passed += 1
            print(f"    ✓ Correctly rejected: {desc}")
        else:
            rej_failed += 1
            print(f"    ✗ Incorrectly accepted: {desc}")

    print("\n  Should ACCEPT (matching ranks):")
    acc_passed = 0
    acc_failed = 0
    for lhs, rhs, desc in should_pass:
        result = glm.verify(lhs, rhs)
        if result:
            acc_passed += 1
            print(f"    ✓ Correctly accepted: {desc}")
        else:
            acc_failed += 1
            print(f"    ✗ Incorrectly rejected: {desc}")

    total = rej_passed + acc_passed
    total_f = rej_failed + acc_failed
    print(f"\n  Result: {total}/{total+total_f}")
    return total_f == 0


def test_buckingham_pi(glm):
    """Test Buckingham Pi dimensionless group extraction."""
    section("TEST 7: Buckingham Pi dimensionless groups")

    # Reynolds number: Re = ρvL/μ
    try:
        groups = glm.pi_groups(["density", "speed", "length", "dynamic_viscosity"])
        print(f"  Reynolds-like groups: {len(groups)} found")
        for g in groups:
            print(f"    {g}")
    except Exception as e:
        print(f"  ? Reynolds: {e}")

    # Mach number: Ma = v/c
    try:
        groups = glm.pi_groups(["speed", "speed"])
        print(f"  Speed ratio groups: {len(groups)} found")
    except Exception as e:
        print(f"  ? Mach: {e}")

    print()
    return True


def test_learning_doesnt_override_library(glm):
    """Ensure learned concepts don't corrupt the library."""
    section("TEST 8: Learning doesn't corrupt the library")

    # Store original meaning
    original = glm.meaning("energy")

    # Try to "learn" a wrong definition
    glm.learn("Energy is force times distance.")

    # Check that the library meaning is unchanged
    after = glm.meaning("energy")
    match = original["exponents"] == after["exponents"]

    print(f"  Original meaning: {original['exponents']}")
    print(f"  After learning:   {after['exponents']}")
    print(f"  Library preserved: {'✓' if match else '✗ CORRUPTED'}")
    return match


def test_determinism(glm):
    """Verify same inputs always give same outputs."""
    section("TEST 9: Determinism (same input = same output)")

    queries = [
        "What is energy?",
        "What is torque?",
        "verify energy mass*speed^2",
    ]

    all_match = True
    for q in queries:
        r1 = glm.chat(q)
        r2 = glm.chat(q)
        match = r1 == r2
        if not match:
            all_match = False
            print(f"  ✗ Non-deterministic: '{q}'")
        else:
            print(f"  ✓ Deterministic: '{q[:40]}...'")

    return all_match


def main():
    glm = GLM()

    tests = [
        ("Novel equations", test_novel_equations),
        ("Formula derivation", test_formula_derivation_depth),
        ("Meaning consistency", test_meaning_consistency),
        ("Unknown concepts", test_concept_not_in_library),
        ("Nearest quality", test_nearest_semantic_quality),
        ("Tensor rank", test_tensor_rank_awareness),
        ("Buckingham Pi", test_buckingham_pi),
        ("Learning safety", test_learning_doesnt_override_library),
        ("Determinism", test_determinism),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            if fn(glm):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"\n  ✗ {name} CRASHED: {e}")

    section("FINAL RESULTS")
    print(f"  {passed}/{passed+failed} test groups passed")
    print(f"  {failed} groups had failures")


if __name__ == "__main__":
    main()
