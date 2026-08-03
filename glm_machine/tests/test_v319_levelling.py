#!/usr/bin/env python3
"""
v3.19.0 Levelling-Up Test Harness
=================================

Verifies the 6 feedback items from the user's evaluation:

  1. OUTPUT PARSING — [Answer] block appears in terse output; "The answer is X."
     sentence appears in prose output. Tested by `test_answer_block_terse`
     and `test_answer_block_prose`.

  2. NOISE REDUCTION — pure-math queries skip KB recall entirely (no
     chemistry/physics bleed). Tested by `test_domain_filter_pure_math`
     and `test_domain_filter_chemistry_kept`.

  3. VERIFICATION LAYER — [Verified] block appears for medium/hard problems.
     Tested by `test_verification_block_appears` and
     `test_verification_difficulty_classification`.

  4. COMPLETENESS — deliberation answers are now surfaced in prose (the
     bug where _fmt_deliberation dropped `answer` is fixed). Tested by
     `test_deliberation_answer_in_prose`.

  5. SCALABILITY — larger combinatorics (C(20,10), factorial(20)) compute
     correctly with native ALU. Tested by `test_scalability_large_combinatorics`.

  6. DIVERSITY — proof-writing test cases (inequalities with equality cases).
     Tested by `test_diversity_proof_queries`.

  7. REGRESSION — 26/26 self-tests + 41/41 golden cases still pass.

Run with:
    python3 test_v319_levelling.py
"""
from __future__ import annotations
import os, sys, json, subprocess, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Support both 'GLM_v3.19' (dev layout) and 'GLM' (zip layout)
_env_glm = os.environ.get('GLM_DIR')
if _env_glm:
    GLM_DIR = Path(_env_glm)
elif (HERE.parent / 'GLM_v3.19').exists():
    GLM_DIR = HERE.parent / 'GLM_v3.19'
elif (HERE.parent / 'GLM').exists():
    GLM_DIR = HERE.parent / 'GLM'
else:
    GLM_DIR = HERE.parent / 'GLM_v3.19'
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
#  TEST 1: Output Parsing — [Answer] block in terse output
# ══════════════════════════════════════════════════════════════════════════════
def test_answer_block_terse():
    section("TEST 1: [Answer] block appears in terse chat() output")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()

    queries_with_expected_answer = [
        ("What is gcd(54, 24)?", "6"),
        ("Find the determinant of [[1, 2, 3], [4, 5, 6], [7, 8, 10]]", "-3"),
        ("differentiate x^3 with respect to x", "3*x"),  # 3*x^2 (native) or 3*x**2 (sympy)
        ("Compute 7!", "5040"),
        ("Is 97 prime?", "Yes"),
    ]
    all_ok = True
    for query, expected_substring in queries_with_expected_answer:
        rt.reset_idea()
        response = rt.chat(query)
        has_answer_tag = "[Answer]" in response
        has_expected = expected_substring in response
        ok = has_answer_tag and has_expected
        if not ok:
            all_ok = False
        record(f"terse_answer_{query[:30]}", ok,
               f"[Answer]={'present' if has_answer_tag else 'MISSING'} "
               f"expected={expected_substring!r} in_response={has_expected}")
    record("TERSE_ANSWER_OVERALL", all_ok,
           f"{sum(1 for _, ok, _ in results if ok)} passed")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 2: Output Parsing — "The answer is X." in prose output
# ══════════════════════════════════════════════════════════════════════════════
def test_answer_block_prose():
    section("TEST 2: 'The answer is X.' sentence in chat_prose() output")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()

    queries_with_expected = [
        ("What is gcd(54, 24)?", "The answer is"),
        ("differentiate x^3 with respect to x", "The answer is"),
        ("Compute 7!", "The answer is"),
    ]
    all_ok = True
    for query, expected_phrase in queries_with_expected:
        rt.reset_idea()
        response = rt.chat_prose(query, fresh=True)
        has_phrase = expected_phrase in response
        if not has_phrase:
            all_ok = False
        record(f"prose_answer_{query[:30]}", has_phrase,
               f"phrase={expected_phrase!r} in_response={has_phrase}")
    record("PROSE_ANSWER_OVERALL", all_ok, f"{len(queries_with_expected)} queries")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 3: Noise Reduction — pure-math queries skip KB recall
# ══════════════════════════════════════════════════════════════════════════════
def test_domain_filter_pure_math():
    section("TEST 3: Pure-math queries skip KB recall (no chemistry/physics bleed)")
    from GLM30_domain_filter import classify_domain, should_suppress_recall
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()

    # Pure-math queries that previously got physics/chemistry KB recalls
    pure_math_queries = [
        "What is gcd(54, 24)?",
        "differentiate x^3 with respect to x",
        "Find the determinant of [[1, 2, 3], [4, 5, 6], [7, 8, 10]]",
        "Prove that the fraction (21n+4)/(14n+3) is irreducible",
    ]
    all_ok = True
    for query in pure_math_queries:
        domain = classify_domain(query, "computation")
        suppress = should_suppress_recall(domain)
        # Also verify in the actual runtime
        rt.reset_idea()
        state = rt._run_pipeline(query)
        recalled = state.get("recalled", [])
        # Pure-math queries should have NO recalled entries (or very few
        # that are explicitly named in the query)
        has_physics_recall = any(
            e.get("ubp_id", "").startswith(("LAW_", "PARTICLE_", "ELEM_", "MOLECULE_"))
            for e in recalled
        )
        ok = (domain == "pure_math") and suppress and not has_physics_recall
        if not ok:
            all_ok = False
        record(f"pure_math_no_bleed_{query[:25]}", ok,
               f"domain={domain} suppress={suppress} "
               f"physics_recall={has_physics_recall} recalled_count={len(recalled)}")
    record("PURE_MATH_NO_BLEED_OVERALL", all_ok, f"{len(pure_math_queries)} queries")


def test_domain_filter_chemistry_kept():
    section("TEST 4: Chemistry queries KEEP chemistry KB recall")
    from GLM30_domain_filter import classify_domain, should_suppress_recall
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()

    chemistry_queries = [
        "Define oxygen",
        "What is the chemical element oxygen?",
    ]
    all_ok = True
    for query in chemistry_queries:
        domain = classify_domain(query, "definition")
        suppress = should_suppress_recall(domain)
        # Chemistry queries should NOT suppress recall
        rt.reset_idea()
        state = rt._run_pipeline(query)
        recalled = state.get("recalled", [])
        has_chemistry_recall = any(
            e.get("ubp_id", "").startswith(("ELEM_", "MOLECULE_"))
            for e in recalled
        )
        ok = (domain == "chemistry") and not suppress and has_chemistry_recall
        if not ok:
            all_ok = False
        record(f"chemistry_recall_kept_{query[:25]}", ok,
               f"domain={domain} suppress={suppress} "
               f"chem_recall={has_chemistry_recall}")
    record("CHEMISTRY_RECALL_OVERALL", all_ok, f"{len(chemistry_queries)} queries")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 5: Verification Layer — [Verified] block for medium/hard
# ══════════════════════════════════════════════════════════════════════════════
def test_verification_block_appears():
    section("TEST 5: [Verified] block appears for medium/hard problems")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()

    # Medium problems (determinant, differentiate) should have [Verified]
    medium_queries = [
        "Find the determinant of [[1, 2, 3], [4, 5, 6], [7, 8, 10]]",
        "differentiate x^3 with respect to x",
    ]
    all_ok = True
    for query in medium_queries:
        rt.reset_idea()
        response = rt.chat(query)
        has_verified = "[Verified]" in response
        if not has_verified:
            all_ok = False
        record(f"verified_medium_{query[:30]}", has_verified,
               f"[Verified]={'present' if has_verified else 'MISSING'}")
    record("VERIFIED_MEDIUM_OVERALL", all_ok, f"{len(medium_queries)} queries")


def test_verification_difficulty_classification():
    section("TEST 6: Difficulty classification (easy/medium/hard)")
    from GLM31_verification import classify_difficulty

    cases = [
        ("What is gcd(54, 24)?", "computation",
         {"compute": {"computation": {"kind": "gcd"}, "result": {"exact": "6"}}},
         "easy"),
        ("Find the determinant of [[1,2,3],[4,5,6],[7,8,10]]", "computation",
         {"compute": {"computation": {"kind": "determinant"}, "result": {"exact": "-3"}}},
         "medium"),
        ("differentiate x^3", "computation",
         {"symbolic": {"computation": {"kind": "differentiate"}, "result": {"exact": "3*x**2"}}},
         "medium"),
        ("Prove that (21n+4)/(14n+3) is irreducible", "proof",
         {"deliberation": {"pattern": "gcd_proof", "answer": "Irreducible (GCD=1)"}},
         "hard"),
        ("What is energy?", "definition", {}, "easy"),
    ]
    all_ok = True
    for query, qtype, state_extra, expected_diff in cases:
        state = {"query": query, "qtype": qtype, **state_extra}
        diff = classify_difficulty(state)
        ok = (diff == expected_diff)
        if not ok:
            all_ok = False
        record(f"difficulty_{expected_diff}_{query[:25]}", ok,
               f"got={diff} expected={expected_diff}")
    record("DIFFICULTY_OVERALL", all_ok, f"{len(cases)} cases")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 7: Completeness — deliberation answer in prose (bug fix)
# ══════════════════════════════════════════════════════════════════════════════
def test_deliberation_answer_in_prose():
    section("TEST 7: Deliberation answer surfaced in prose (bug fix)")
    from GLM19_prose_composer import _fmt_deliberation

    # The bug: _fmt_deliberation used to drop `answer` entirely, only surfacing `trace`.
    # The fix: now appends "The conclusion is: {answer}."
    result = {
        "pattern": "stars_and_bars",
        "method": "stars_and_bars",
        "answer": "C(9, 3) = 84",
        "trace": ["n = 10 identical balls", "k = 4 distinct boxes",
                  "Stars and bars: C(n-1, k-1)"],
    }
    prose = _fmt_deliberation(result, turn=0, query="test")
    has_answer = "84" in prose
    has_conclusion = "conclusion" in prose.lower()
    ok = has_answer and has_conclusion
    record("deliberation_answer_in_prose", ok,
           f"answer_present={has_answer} conclusion_present={has_conclusion}")
    print(f"    prose output: {prose!r}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 8: Scalability — larger combinatorics
# ══════════════════════════════════════════════════════════════════════════════
def test_scalability_large_combinatorics():
    section("TEST 8: Scalability — larger combinatorics (C(20,10), factorial(20))")
    from GLM25_native_alu import native_compute

    cases = [
        ("combination", (20, 10), 184756),   # C(20,10) = 184756
        ("combination", (30, 15), 155117520), # C(30,15) = 155117520
        ("factorial", (20,), 2432902008176640000),  # 20! = 2432902008176640000
        ("factorial", (15,), 1307674368000),  # 15! = 1307674368000
        ("modpow", (2, 100, 1000000007), 976371285),  # 2^100 mod 10^9+7
    ]
    all_ok = True
    for kind, operands, expected in cases:
        r = native_compute(kind, operands, validate=True)
        ok = (r.result == expected)
        sym_ok = (r.sympy_check or {}).get("matches", False) if r.sympy_check else None
        has_trace = len(r.trace) > 0
        has_fp = "nrci" in r.fingerprint
        full_ok = ok and has_trace and has_fp
        if not full_ok:
            all_ok = False
        record(f"scalable_{kind}_{operands}", full_ok,
               f"result={r.result} expected={expected} match={ok} "
               f"sympy={sym_ok} trace={len(r.trace)} fp={'yes' if has_fp else 'no'}")
    record("SCALABILITY_OVERALL", all_ok, f"{len(cases)} cases")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 9: Diversity — proof queries
# ══════════════════════════════════════════════════════════════════════════════
def test_diversity_proof_queries():
    section("TEST 9: Diversity — proof queries classified as 'hard'")
    from GLM31_verification import classify_difficulty
    from GLM30_domain_filter import classify_domain

    proof_queries = [
        "Prove that a^2 + b^2 >= 2ab",
        "Show that the fraction (21n+4)/(14n+3) is irreducible",
        "Prove that for any positive integers a and b, gcd(a,b) * lcm(a,b) = a*b",
        "Show that the median of a triangle satisfies m_a <= (b+c)/2",
    ]
    all_ok = True
    for query in proof_queries:
        state = {"query": query, "qtype": "proof",
                 "deliberation": {"pattern": "gcd_proof", "answer": "..."}}
        diff = classify_difficulty(state)
        domain = classify_domain(query, "proof")
        ok = (diff == "hard") and (domain == "pure_math")
        if not ok:
            all_ok = False
        record(f"proof_{query[:30]}", ok,
               f"difficulty={diff} domain={domain}")
    record("PROOF_DIVERSITY_OVERALL", all_ok, f"{len(proof_queries)} queries")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 10: Metrics tag renamed (Verify -> Metrics)
# ══════════════════════════════════════════════════════════════════════════════
def test_metrics_tag_renamed():
    section("TEST 10: [Verify] tag renamed to [Metrics] to avoid confusion")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()
    rt.reset_idea()
    # A definition query that would have had [Verify] in v3.18
    response = rt.chat("Tell me about the hamiltonian.")
    has_metrics = "[Metrics]" in response
    has_old_verify = "[Verify] NRCI" in response  # the old tag format
    ok = has_metrics and not has_old_verify
    record("metrics_tag_renamed", ok,
           f"[Metrics]={has_metrics} old_[Verify]_NRCI={has_old_verify}")


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 11: Regression — 26/26 + 41/41
# ══════════════════════════════════════════════════════════════════════════════
def test_regression_self_tests():
    section("TEST 11a: Regression — 26/26 self-tests still pass")
    env = os.environ.copy()
    env["UBP_CORE_PATH"] = str(GLM_DIR)
    r = subprocess.run([sys.executable, "GLM12_cli_entry.py", "--test"],
                       cwd=str(GLM_DIR), env=env,
                       capture_output=True, text=True, timeout=300)
    ok = "26/26 tests passed" in r.stdout
    record("self_tests_26_of_26", ok,
           "26/26 passed" if ok else f"stdout tail: {r.stdout[-300:]!r}")


def test_regression_golden_cases():
    section("TEST 11b: Regression — 41/41 golden cases still pass")
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
    print("v3.19.0 Levelling-Up Test Harness")
    print(f"GLM dir: {GLM_DIR}")
    print(f"Python:  {sys.version.split()[0]}")

    test_answer_block_terse()
    test_answer_block_prose()
    test_domain_filter_pure_math()
    test_domain_filter_chemistry_kept()
    test_verification_block_appears()
    test_verification_difficulty_classification()
    test_deliberation_answer_in_prose()
    test_scalability_large_combinatorics()
    test_diversity_proof_queries()
    test_metrics_tag_renamed()
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
