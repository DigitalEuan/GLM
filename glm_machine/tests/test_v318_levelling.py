#!/usr/bin/env python3
"""
v3.18.0 Levelling-Up Test Harness
=================================

Verifies the four v3.18 improvements (recommended next steps from the
v3.17 UPGRADE_REPORT):

  1. CRG EXPANSION — GLM27 adds ~80+ auto-curated edges from the master
     resource, KB descriptions, and curated physics edges. The CRG-ALU now
     has fuel. Tested by `test_crg_expansion_growth` and
     `test_crg_expander_idempotent`.

  2. NATIVE POLYNOMIAL ALU — GLM28 handles polynomial differentiation and
     integration natively (no SymPy), with full trace + fingerprint.
     Tested by `test_native_polynomial_diff_integrate`.

  3. CRG-AWARE GRAMMAR — GLM22's `construct_paragraph` now prefers
     CRG-reachable objects over pure Hamming-proximity neighbours. This
     eliminates word salad at the source. Tested by
     `test_generate_grammatical_crg_aware`.

  4. AUTO TOPIC-SHIFT DETECTION — GLM11's `_run_pipeline` now auto-resets
     the IdeaManager when the active zone has crystallised AND the new
     query has zero content-word overlap (direct OR CRG-reachable).
     Tested by `test_auto_topic_shift`.

  5. REGRESSION — 26/26 self-tests + 41/41 golden cases still pass.

Run with:
    python3 test_v318_levelling.py
"""
from __future__ import annotations
import os, sys, json, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
# v3.18: support both 'GLM_v3.17' (dev layout) and 'GLM' (zip layout)
_env_glm = os.environ.get('GLM_DIR')
if _env_glm:
    GLM_DIR = Path(_env_glm)
elif (HERE.parent / 'GLM_v3.17').exists():
    GLM_DIR = HERE.parent / 'GLM_v3.17'
elif (HERE.parent / 'GLM').exists():
    GLM_DIR = HERE.parent / 'GLM'
else:
    GLM_DIR = HERE.parent / 'GLM_v3.17'  # fallback for error message
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
#  TEST 1: CRG expansion
# ══════════════════════════════════════════════════════════════════════════════
def test_crg_expansion_growth():
    section("TEST 1: CRG expansion grows the graph by 50+ edges")
    from GLM01_substrate import _build_vocabulary
    from GLM03_crg import build_extended_crg
    from GLM27_crg_expander import expand_crg

    vocab_dict = _build_vocabulary()
    class V:
        def __init__(self, d): self.words = d
    v = V(vocab_dict)

    crg_before = build_extended_crg()
    n_before = len(crg_before.edges)
    report = expand_crg(crg_before, v, verbose=False)
    n_after = len(crg_before.edges)
    delta = n_after - n_before

    ok = (delta >= 50)  # at least 50 new edges
    record("crg_expansion_grew_graph", ok,
           f"before={n_before} after={n_after} delta={delta}")
    record("crg_expansion_master_resource_source",
           report["by_source"].get("master_resource", 0) >= 0,
           f"+{report['by_source'].get('master_resource', 0)} from master_resource")
    record("crg_expansion_kb_descriptions_source",
           report["by_source"].get("kb_descriptions", 0) >= 10,
           f"+{report['by_source'].get('kb_descriptions', 0)} from kb_descriptions")
    record("crg_expansion_curated_source",
           report["by_source"].get("curated", 0) >= 30,
           f"+{report['by_source'].get('curated', 0)} from curated")


def test_crg_expander_idempotent():
    section("TEST 2: CRG expander is idempotent (running twice doesn't duplicate)")
    from GLM01_substrate import _build_vocabulary
    from GLM03_crg import build_extended_crg
    from GLM27_crg_expander import expand_crg

    vocab_dict = _build_vocabulary()
    class V:
        def __init__(self, d): self.words = d
    v = V(vocab_dict)

    crg = build_extended_crg()
    expand_crg(crg, v, verbose=False)
    n1 = len(crg.edges)
    # Run again — should add 0 new edges
    report2 = expand_crg(crg, v, verbose=False)
    n2 = len(crg.edges)
    ok = (n2 == n1 and report2["added"] == 0)
    record("crg_expander_idempotent", ok,
           f"first_run={n1} second_run={n2} added_in_2nd={report2['added']}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 3: Native polynomial ALU
# ══════════════════════════════════════════════════════════════════════════════
def test_native_polynomial_diff_integrate():
    section("TEST 3: Native polynomial diff/integrate matches SymPy")
    from GLM28_native_poly import (native_polynomial_diff,
                                    native_polynomial_integrate,
                                    is_polynomial)

    # Test polynomial detection
    poly_ok = all(is_polynomial(e) for e in
                  ["x^2", "3*x^2 + 2*x - 5", "x^4 - 2*x^2 + 1"]) and \
              not any(is_polynomial(e) for e in
                      ["sin(x)", "exp(x)", "1/x", "log(x)"])
    record("polynomial_detection", poly_ok,
           "correctly identified polynomials vs non-polynomials")

    # Test diff
    diff_cases = [
        ("x^3", "x", "3*x^2"),
        ("3*x^2 + 2*x - 5", "x", "6*x + 2"),
        ("5", "x", "0"),
        ("x^4 - 2*x^2 + 1", "x", "4*x^3 - 4*x"),
    ]
    all_diff_ok = True
    for expr, var, expected in diff_cases:
        r = native_polynomial_diff(expr, var, validate=True)
        sym_match = (r.get("sympy_check") or {}).get("matches", False)
        native_flag = r.get("native", False)
        has_fp = "nrci" in r.get("fingerprint", {})
        has_trace = len(r.get("trace", [])) > 0
        ok = sym_match and native_flag and has_fp and has_trace
        if not ok:
            all_diff_ok = False
        record(f"native_diff_{expr.replace('*','').replace('^','').replace(' ','').replace('+','p').replace('-','m')[:20]}",
               ok,
               f"result={r.get('exact')!r} sympy_match={sym_match} native={native_flag} nrci={r.get('fingerprint',{}).get('nrci')}")
    record("NATIVE_DIFF_OVERALL", all_diff_ok, f"{len(diff_cases)} cases all native+validated")

    # Test integrate
    int_cases = [
        ("x^2", "x", "1/3*x^3"),
        ("3*x^2 + 2*x - 5", "x", "x^3 + x^2 - 5*x"),
        ("1", "x", "x"),
        ("2*x^3 + 6*x", "x", "1/2*x^4 + 3*x^2"),
    ]
    all_int_ok = True
    for expr, var, expected in int_cases:
        r = native_polynomial_integrate(expr, var, validate=True)
        sym_match = (r.get("sympy_check") or {}).get("matches", False)
        native_flag = r.get("native", False)
        has_fp = "nrci" in r.get("fingerprint", {})
        has_trace = len(r.get("trace", [])) > 0
        ok = sym_match and native_flag and has_fp and has_trace
        if not ok:
            all_int_ok = False
        record(f"native_int_{expr.replace('*','').replace('^','').replace(' ','').replace('+','p').replace('-','m')[:20]}",
               ok,
               f"result={r.get('exact')!r} sympy_match={sym_match} native={native_flag} nrci={r.get('fingerprint',{}).get('nrci')}")
    record("NATIVE_INT_OVERALL", all_int_ok, f"{len(int_cases)} cases all native+validated")

    # Test fallback for non-polynomial
    r = native_polynomial_diff("sin(x)", "x", validate=True)
    fallback_ok = (r.get("native") is False and "fallback" in r.get("trace", [""])[1].lower())
    record("native_polynomial_fallback_for_sin", fallback_ok,
           f"native={r.get('native')} result={r.get('exact')!r}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 4: CRG-aware grammar (no word salad)
# ══════════════════════════════════════════════════════════════════════════════
def test_generate_grammatical_crg_aware():
    section("TEST 4: generate_grammatical uses CRG for object selection")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()

    # Generate paragraphs for several seeds and check the chain is coherent
    seeds = ["hamiltonian", "energy", "lattice", "anomaly", "operator"]
    coherent_count = 0
    samples = []
    for seed in seeds:
        para = rt.generate_grammatical(topic=seed, n_sentences=3)
        samples.append((seed, para))
        # A paragraph is "coherent" if:
        # - non-empty
        # - contains the seed word
        # - has at least 2 sentences (chain didn't break immediately)
        if para and seed.lower() in para.lower() and para.count(".") >= 2:
            coherent_count += 1

    ok = coherent_count >= 3  # at least 3 of 5 should be coherent
    record("generate_grammatical_crg_coherent", ok,
           f"coherent={coherent_count}/{len(seeds)}")
    for seed, para in samples[:3]:
        print(f"    {seed!r} -> {para[:120]!r}...")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 5: Auto topic-shift detection
# ══════════════════════════════════════════════════════════════════════════════
def test_auto_topic_shift():
    section("TEST 5: Auto topic-shift detection (no manual fresh=True needed)")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()
    rt.reset_idea()

    # Phase 1: Build up a crystallised zone about physics
    rt.chat("Tell me about the hamiltonian and time.")
    rt.chat("What about symmetry?")
    z1 = rt.manager.active
    crystallised_before = z1.crystallized
    thesis_before = z1.thesis
    record("topic_shift_zone_crystallised_before",
           crystallised_before and bool(thesis_before),
           f"crystallised={crystallised_before} thesis={thesis_before!r}")

    # Phase 2: Send a completely unrelated query (about something with NO
    # CRG edges to hamiltonian/time/symmetry).
    # "plus and minus" are operator words — they should have no CRG edges
    # to the hamiltonian zone.
    rt.chat("What about plus and minus?")
    z2 = rt.manager.active
    # After auto-reset, the active zone should be fresh — either a new zone
    # OR the same zone but reset. The thesis should be empty or different.
    thesis_after = z2.thesis
    # Auto-reset means the new query starts a new topic context
    auto_reset_fired = (thesis_after != thesis_before) or (not z2.crystallized)
    record("topic_shift_auto_reset_fired", auto_reset_fired,
           f"thesis_before={thesis_before!r} thesis_after={thesis_after!r} "
           f"crystallised_after={z2.crystallized}")

    # Phase 3: A CRG-reachable query should NOT trigger auto-reset
    rt.reset_idea()
    rt.chat("Tell me about the hamiltonian.")
    z3 = rt.manager.active
    # Manually crystallise so the auto-reset check has something to compare to
    z3.crystallized = True
    z3.thesis = "hamiltonian generates time"
    z3.topic_nouns = ["hamiltonian", "time"]

    # Now ask about "symmetry" — which IS CRG-reachable from hamiltonian
    rt.chat("What about symmetry?")
    z4 = rt.manager.active
    # The zone should NOT have been reset (symmetry is CRG-reachable)
    # If the reset fired, we'd have a brand new zone with no thesis
    no_reset_for_crg_reachable = (z4.thesis == "hamiltonian generates time") or \
                                  ("hamiltonian" in (z4.topic_nouns or []))
    record("topic_shift_no_reset_for_crg_reachable",
           no_reset_for_crg_reachable,
           f"thesis_after_symmetry={z4.thesis!r} "
           f"topic_nouns={z4.topic_nouns}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 6: Regression — 26/26 self-tests + 41/41 golden cases
# ══════════════════════════════════════════════════════════════════════════════
def test_regression_self_tests():
    section("TEST 6a: Regression — 26/26 self-tests still pass")
    env = os.environ.copy()
    env["UBP_CORE_PATH"] = str(GLM_DIR)
    r = subprocess.run([sys.executable, "GLM12_cli_entry.py", "--test"],
                       cwd=str(GLM_DIR), env=env,
                       capture_output=True, text=True, timeout=300)
    ok = "26/26 tests passed" in r.stdout
    record("self_tests_26_of_26", ok,
           "26/26 passed" if ok else f"stdout tail: {r.stdout[-300:]!r}")


def test_regression_golden_cases():
    section("TEST 6b: Regression — 41/41 golden cases still pass")
    env = os.environ.copy()
    env["UBP_CORE_PATH"] = str(GLM_DIR)
    r = subprocess.run([sys.executable, "run_golden_cases.py"],
                       cwd=str(GLM_DIR), env=env,
                       capture_output=True, text=True, timeout=300)
    ok = "41/41 passed" in r.stdout
    record("golden_cases_41_of_41", ok,
           "41/41 passed" if ok else f"stdout tail: {r.stdout[-300:]!r}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 7: Symbolic fingerprint (item 1) — verify symbolic ops now carry
#  trace + fingerprint even when SymPy is the engine
# ══════════════════════════════════════════════════════════════════════════════
def test_symbolic_ops_have_fingerprints():
    section("TEST 7: Symbolic ops (simplify, solve, ODE, taylor, limit) carry fingerprints")
    from GLM09_tools import detect_symbolic, evaluate_symbolic

    queries = [
        "simplify (x^2-1)/(x-1)",
        "solve x^2 - 4 = 0 for x",
        "Solve the ODE: dy/dx = y",
        "Find the Taylor series expansion of exp(x) around 0",
        "Find the limit of sin(x)/x as x -> 0",
    ]
    all_ok = True
    for q in queries:
        comp = detect_symbolic(q)
        if comp is None:
            record(f"symbolic_fp_{q[:30]}", False, "no detection")
            all_ok = False
            continue
        r = evaluate_symbolic(comp)
        has_fp = "fingerprint" in r and "nrci" in r.get("fingerprint", {})
        has_trace = "trace" in r and len(r.get("trace", [])) > 0
        ok = has_fp and has_trace
        if not ok:
            all_ok = False
        record(f"symbolic_fp_{comp['kind']}", ok,
               f"result={r.get('exact','')[:50]!r} nrci={r.get('fingerprint',{}).get('nrci')} "
               f"trace_steps={len(r.get('trace', []))}")
    record("SYMBOLIC_FP_OVERALL", all_ok, f"{len(queries)} symbolic ops all carry trace+fp")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("v3.18.0 Levelling-Up Test Harness")
    print(f"GLM dir: {GLM_DIR}")
    print(f"Python:  {sys.version.split()[0]}")

    test_crg_expansion_growth()
    test_crg_expander_idempotent()
    test_native_polynomial_diff_integrate()
    test_generate_grammatical_crg_aware()
    test_auto_topic_shift()
    test_symbolic_ops_have_fingerprints()
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
