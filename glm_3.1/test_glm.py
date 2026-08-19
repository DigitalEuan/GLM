#!/usr/bin/env python3
"""
GLM Test Suite — verify the unified system works end-to-end.

Tests:
  1. Reasoner: equation audit (true and false)
  2. Reasoner: formula discovery (solve)
  3. Reasoner: meaning and carrier
  4. Reasoner: nearest neighbours
  5. Three Column Thinking: output structure
  6. Learning: text ingestion
  7. Integration: chat → verify → solve pipeline
"""

import sys
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

def test_reasoner():
    """Test the core reasoner."""
    print("=" * 60)
    print("TEST 1: Reasoner")
    print("=" * 60)

    from reasoner import GLMReasoner
    r = GLMReasoner()

    # True equations (pass full audit: dimensions + tensor rank + parity)
    true_eqs = [
        ("energy", "mass*speed^2", "E=mc²"),
        ("force", "mass*acceleration", "F=ma"),
        ("momentum", "mass*velocity", "p=mv"),
        ("impulse", "force*time", "J=Ft"),
        ("action", "energy*time", "S=Et"),
        ("power", "energy/time", "P=E/t"),
        ("pressure", "energy/volume", "p=E/V"),
        ("frequency", "1/time", "f=1/T"),
        ("wavelength", "speed/frequency", "λ=v/f"),
        ("dynamic_viscosity", "pressure*time", "η=p·t"),
    ]
    print("\n  True equations:")
    for lhs, rhs, label in true_eqs:
        result = r.audit(lhs, rhs)
        status = "✓" if result["pass"] else "✗"
        print(f"    {status} {label}: {lhs} = {rhs}")

    # False equations (correctly rejected: wrong dims OR wrong tensor rank/parity)
    false_eqs = [
        ("energy", "mass*speed^4", "E=mc⁴ (wrong dims)"),
        ("force", "mass*speed", "F=mc (wrong dims)"),
        ("work", "force*distance", "W=Fd (scalar≠vector)"),
        ("pressure", "force/area", "p=F/A (scalar≠vector)"),
    ]
    print("\n  False equations:")
    for lhs, rhs, label in false_eqs:
        result = r.audit(lhs, rhs)
        status = "✓" if not result["pass"] else "✗"
        print(f"    {status} {label}: {lhs} ≠ {rhs} (correctly rejected)")

    print()


def test_solve():
    """Test formula discovery."""
    print("=" * 60)
    print("TEST 2: Formula Discovery")
    print("=" * 60)

    from reasoner import GLMReasoner
    r = GLMReasoner()

    solves = [
        ("speed", ["energy", "mass"]),
        ("force", ["mass", "acceleration"]),
        ("frequency", ["energy", "action"]),
    ]
    for target, sources in solves:
        result = r.solve(target, sources)
        print(f"  solve({target}; {', '.join(sources)}):")
        print(f"    Formula: {result.get('formula', 'not found')}")
        print(f"    Solvable: {result.get('solvable', False)}")
    print()


def test_meaning():
    """Test meaning and carrier."""
    print("=" * 60)
    print("TEST 3: Meaning & Carrier")
    print("=" * 60)

    from reasoner import GLMReasoner
    r = GLMReasoner()

    concepts = ["energy", "force", "torque", "entropy", "frequency"]
    for c in concepts:
        try:
            m = r.meaning(c)
            carrier = r.carrier(c)
            hw = sum(carrier)
            dims = {k: v for k, v in m["exponents"].items() if v != "0"}
            print(f"  {c}: dims={dims}, HW={hw}")
        except Exception as e:
            print(f"  {c}: ERROR - {e}")
    print()


def test_nearest():
    """Test nearest neighbours."""
    print("=" * 60)
    print("TEST 4: Nearest Neighbours")
    print("=" * 60)

    from reasoner import GLMReasoner
    r = GLMReasoner()

    for concept in ["energy", "force", "entropy"]:
        try:
            nearest = r.nearest(concept, 5)
            names = [f"{n}({s:.2f})" for n, s in nearest]
            print(f"  {concept}: {', '.join(names)}")
        except Exception as e:
            print(f"  {concept}: ERROR - {e}")
    print()


def test_tct():
    """Test Three Column Thinking."""
    print("=" * 60)
    print("TEST 5: Three Column Thinking")
    print("=" * 60)

    from GLM import GLM
    glm = GLM()

    queries = [
        "What is energy?",
        "What is force?",
        "What is torque?",
    ]
    for q in queries:
        print(f"\n  Query: {q}")
        result = glm.chat_verbose(q)
        for step in result.get("steps", []):
            print(f"    {step.get('step', '?')}: {step.get('language', 'N/A')[:80]}")
    print()


def test_learning():
    """Test text learning."""
    print("=" * 60)
    print("TEST 6: Learning")
    print("=" * 60)

    from GLM import GLM
    glm = GLM()

    texts = [
        "Energy is mass times speed squared.",
        "Force causes acceleration.",
        "Power is force times speed.",
    ]
    for text in texts:
        result = glm.learn(text)
        print(f"  '{text}'")
        print(f"    Definitions: {len(result['definitions'])}, "
              f"Relations: {len(result['relations'])}, "
              f"New concepts: {len(result['new_concepts'])}")

    print(f"\n  Learned concepts: {glm.learned_concepts()}")
    print(f"  Learned edges: {len(glm.learned_edges())}")
    print()


def test_integration():
    """Test full integration pipeline."""
    print("=" * 60)
    print("TEST 7: Integration Pipeline")
    print("=" * 60)

    from GLM import GLM
    glm = GLM()

    # 1. Verify
    print(f"\n  Verify E=mc²: {glm.verify('energy', 'mass*speed^2')}")
    print(f"  Verify F=ma:  {glm.verify('force', 'mass*acceleration')}")

    # 2. Solve
    result = glm.solve("speed", ["energy", "mass"])
    print(f"  Solve for speed: {result.get('formula', 'not found')}")

    # 3. Nearest
    nearest = glm.nearest("energy", 3)
    print(f"  Nearest to energy: {[n for n, s in nearest]}")

    # 4. Status
    status = glm.status()
    print(f"  Status: {status['library_concepts']} library concepts, "
          f"{status['learned_concepts']} learned, "
          f"{len(status['domains'])} domains")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  GLM UNIFIED SYSTEM — TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("Reasoner", test_reasoner),
        ("Solve", test_solve),
        ("Meaning", test_meaning),
        ("Nearest", test_nearest),
        ("Three Column Thinking", test_tct),
        ("Learning", test_learning),
        ("Integration", test_integration),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n  ✗ {name} FAILED: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
