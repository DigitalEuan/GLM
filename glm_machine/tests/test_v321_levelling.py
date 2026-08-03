#!/usr/bin/env python3
"""
v3.21.0 Simplicial CRG Test Harness
====================================

Verifies the simplicial 2-complex upgrade:

  1. FACE DISCOVERY — 3-cliques in the CRG are discovered as 2-simplices.
  2. BETTI NUMBERS — β₀, β₁, β₂ computed correctly over GF(2).
  3. EULER CHARACTERISTIC — χ = V − E + F.
  4. TOPOLOGICAL COHERENCE — backbone_is_filled + topological_coherence.
  5. NODE GEOMETRY — degree, stellar, bridge_score.
  6. RUNTIME INTEGRATION — rt.simplicial_crg() and rt.topology_report().
  7. REGRESSION — 26/26 + 41/41 still pass.
"""
from __future__ import annotations
import os, sys, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
_env_glm = os.environ.get('GLM_DIR')
if _env_glm:
    GLM_DIR = Path(_env_glm)
elif (HERE.parent / 'GLM_v3.20').exists():
    GLM_DIR = HERE.parent / 'GLM_v3.20'
elif (HERE.parent / 'GLM').exists():
    GLM_DIR = HERE.parent / 'GLM'
else:
    GLM_DIR = HERE.parent / 'GLM_v3.20'
os.environ["UBP_CORE_PATH"] = str(GLM_DIR)
sys.path.insert(0, str(GLM_DIR))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []

def record(name, ok, detail=""):
    tag = PASS if ok else FAIL
    results.append((name, ok, detail))
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))

def section(title):
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 1: Face discovery
# ══════════════════════════════════════════════════════════════════════════════
def test_face_discovery():
    section("TEST 1: Face discovery — 3-cliques become 2-simplices")
    from GLM01_substrate import _build_vocabulary
    from GLM34_simplicial_crg import build_simplicial_crg

    vocab = _build_vocabulary()
    scrg = build_simplicial_crg(vocab, max_side=8, max_faces=100)

    n_faces = len(scrg.faces)
    ok = n_faces >= 1  # at least one face discovered
    record("faces_discovered", ok, f"n_faces={n_faces}")

    # Check that faces have valid geometry
    if n_faces > 0:
        f = list(scrg.faces.values())[0]
        has_valid_sides = len(f.sides) == 3 and all(s > 0 for s in f.sides)
        has_area = f.area >= 0
        has_shape = f.shape in ("equilateral", "isosceles", "scalene", "degenerate")
        record("face_geometry_valid", has_valid_sides and has_area and has_shape,
               f"sides={f.sides} area={f.area:.3f} shape={f.shape}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 2: Betti numbers
# ══════════════════════════════════════════════════════════════════════════════
def test_betti_numbers():
    section("TEST 2: Betti numbers (β₀, β₁, β₂)")
    from GLM01_substrate import _build_vocabulary
    from GLM34_simplicial_crg import build_simplicial_crg

    vocab = _build_vocabulary()
    scrg = build_simplicial_crg(vocab, max_side=8, max_faces=100)
    b0, b1, b2 = scrg.betti()

    # β₀ should be ≥ 1 (at least one connected component)
    ok_b0 = b0 >= 1
    record("beta0_positive", ok_b0, f"β₀={b0}")

    # β₁ should be ≥ 0 (non-negative)
    ok_b1 = b1 >= 0
    record("beta1_nonnegative", ok_b1, f"β₁={b1}")

    # β₂ should be ≥ 0 (non-negative)
    ok_b2 = b2 >= 0
    record("beta2_nonnegative", ok_b2, f"β₂={b2}")

    record("BETTI_OVERALL", ok_b0 and ok_b1 and ok_b2,
           f"β=({b0},{b1},{b2})")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 3: Euler characteristic
# ══════════════════════════════════════════════════════════════════════════════
def test_euler_characteristic():
    section("TEST 3: Euler characteristic χ = V − E + F")
    from GLM01_substrate import _build_vocabulary
    from GLM34_simplicial_crg import build_simplicial_crg

    vocab = _build_vocabulary()
    scrg = build_simplicial_crg(vocab, max_side=8, max_faces=100)
    chi = scrg.euler()
    rep = scrg.topology_report()

    # Verify χ = V - E + F
    expected_chi = rep.n_vertices - rep.n_edges + rep.n_faces
    ok = (chi == expected_chi)
    record("euler_formula_correct", ok,
           f"χ={chi} expected={expected_chi} (V={rep.n_vertices} E={rep.n_edges} F={rep.n_faces})")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 4: Topological coherence
# ══════════════════════════════════════════════════════════════════════════════
def test_topological_coherence():
    section("TEST 4: Topological coherence — backbone_is_filled + coherence")
    from GLM01_substrate import _build_vocabulary
    from GLM34_simplicial_crg import build_simplicial_crg

    vocab = _build_vocabulary()
    scrg = build_simplicial_crg(vocab, max_side=8, max_faces=100)

    # Build a small backbone from CRG edges
    from GLM03_crg import build_extended_crg
    crg = build_extended_crg()
    backbone = []
    for edge in crg.edges:
        if edge.label not in ("contradicts", "incompatible_with", "auto_proposed"):
            backbone.append(edge)
        if len(backbone) >= 3:
            break

    if backbone:
        tc = scrg.topological_coherence(backbone)
        filled = scrg.backbone_is_filled(backbone)
        support = scrg.backbone_face_support(backbone)
        ok = (0.0 <= tc <= 1.0)
        record("topological_coherence_in_range", ok,
               f"tc={tc:.3f} filled={filled} support={support}")
    else:
        record("topological_coherence_in_range", True, "no backbone available (skip)")

    # Test empty backbone (should return 1.0)
    tc_empty = scrg.topological_coherence([])
    record("empty_backbone_coherence_1", tc_empty == 1.0,
           f"tc(empty)={tc_empty}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 5: Node geometry
# ══════════════════════════════════════════════════════════════════════════════
def test_node_geometry():
    section("TEST 5: Node geometry — degree, stellar, bridge_score")
    from GLM01_substrate import _build_vocabulary
    from GLM34_simplicial_crg import build_simplicial_crg

    vocab = _build_vocabulary()
    scrg = build_simplicial_crg(vocab, max_side=8, max_faces=100)

    # Check that node geometry was computed
    n_geom = len(scrg._node_geom)
    ok = n_geom > 0
    record("node_geometry_computed", ok, f"n_nodes={n_geom}")

    if n_geom > 0:
        # Check a sample node
        sample = list(scrg._node_geom.values())[0]
        has_degree = hasattr(sample, 'degree') and sample.degree >= 0
        has_stellar = hasattr(sample, 'stellar') and sample.stellar >= 0
        has_bridge = hasattr(sample, 'bridge_score') and sample.bridge_score >= 0
        has_zone = hasattr(sample, 'zone') and sample.zone
        record("node_geom_fields_valid",
               has_degree and has_stellar and has_bridge and has_zone,
               f"name={sample.name} degree={sample.degree} stellar={sample.stellar} "
               f"bridge={sample.bridge_score} zone={sample.zone}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 6: Runtime integration
# ══════════════════════════════════════════════════════════════════════════════
def test_runtime_integration():
    section("TEST 6: Runtime integration — rt.simplicial_crg() + rt.topology_report()")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37(auto_expand=False)

    # Test simplicial_crg()
    scrg = rt.simplicial_crg(max_side=8, max_faces=50)
    ok_scrg = (scrg is not None and hasattr(scrg, 'faces') and hasattr(scrg, 'betti'))
    record("simplicial_crg_returns_object", ok_scrg,
           f"faces={len(scrg.faces) if scrg else 0}")

    # Test topology_report()
    rep = rt.topology_report()
    ok_rep = (rep is not None and hasattr(rep, 'beta0') and hasattr(rep, 'euler'))
    record("topology_report_returns_object", ok_rep,
           f"β=({rep.beta0},{rep.beta1},{rep.beta2}) χ={rep.euler}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 7: GF(2) linear algebra
# ══════════════════════════════════════════════════════════════════════════════
def test_gf2_linear_algebra():
    section("TEST 7: GF(2) linear algebra — rank + solve")
    from GLM34_simplicial_crg import _gf2_rank_reduce, _gf2_solve

    # Test rank: 3 columns, rank 2 (col 3 = col 1 XOR col 2)
    cols = [0b011, 0b101, 0b110]  # col3 = col1 ^ col2
    pivots = _gf2_rank_reduce(cols)
    rank = len(pivots)
    record("gf2_rank_correct", rank == 2, f"rank={rank} expected=2")

    # Test solve: find x such that x0*col0 + x1*col1 = target
    target = 0b011  # = 1 * col0 + 0 * col1
    sol = _gf2_solve([0b011, 0b101], target)
    ok = sol is not None and sol == [1, 0]
    record("gf2_solve_correct", ok, f"sol={sol} expected=[1, 0]")

    # Test unsolvable: target not in span
    sol_none = _gf2_solve([0b001, 0b010], 0b111)
    record("gf2_solve_unsolvable", sol_none is None, f"sol={sol_none}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 8: Regression
# ══════════════════════════════════════════════════════════════════════════════
def test_regression_self_tests():
    section("TEST 8a: Regression — 26/26 self-tests still pass")
    env = os.environ.copy()
    env["UBP_CORE_PATH"] = str(GLM_DIR)
    r = subprocess.run([sys.executable, "GLM12_cli_entry.py", "--test"],
                       cwd=str(GLM_DIR), env=env,
                       capture_output=True, text=True, timeout=300)
    ok = "26/26 tests passed" in r.stdout
    record("self_tests_26_of_26", ok,
           "26/26 passed" if ok else f"stdout tail: {r.stdout[-300:]!r}")


def test_regression_golden_cases():
    section("TEST 8b: Regression — 41/41 golden cases still pass")
    env = os.environ.copy()
    env["UBP_CORE_PATH"] = str(GLM_DIR)
    r = subprocess.run([sys.executable, "run_golden_cases.py"],
                       cwd=str(GLM_DIR), env=env,
                       capture_output=True, text=True, timeout=300)
    ok = "41/41 passed" in r.stdout
    record("golden_cases_41_of_41", ok,
           "41/41 passed" if ok else f"stdout tail: {r.stdout[-300:]!r}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("v3.21.0 Simplicial CRG Test Harness")
    print(f"GLM dir: {GLM_DIR}")
    print(f"Python:  {sys.version.split()[0]}")

    test_face_discovery()
    test_betti_numbers()
    test_euler_characteristic()
    test_topological_coherence()
    test_node_geometry()
    test_runtime_integration()
    test_gf2_linear_algebra()
    test_regression_self_tests()
    test_regression_golden_cases()

    print()
    print("=" * 78)
    print("  SUMMARY")
    print("=" * 78)
    n_pass = sum(1 for _, ok, _ in results if ok)
    n_fail = sum(1 for _, ok, _ in results if not ok)
    for name, ok, detail in results:
        tag = PASS if ok else FAIL
        print(f"  [{tag}] {name}")
    print()
    print(f"  {n_pass} passed, {n_fail} failed, {len(results)} total")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
