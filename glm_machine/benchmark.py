#!/usr/bin/env python3
"""
GLM Benchmark Suite
====================
Comprehensive benchmark comparing GLM to standard LLM capabilities.
Tests across 8 categories with scored responses.
"""

import json
import time
import sys
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
SERVER_DIR = BASE_DIR / "server"
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(SERVER_DIR))
os.environ['UBP_CORE_PATH'] = str(DATA_DIR)

# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

BENCHMARKS = {
    "1_factual_recall": {
        "description": "Can the GLM recall factual knowledge?",
        "weight": 1.0,
        "tests": [
            {
                "id": "F1",
                "query": "What is the atomic number of hydrogen?",
                "must_contain": ["1"],
                "should_contain": ["hydrogen", "element"],
                "category": "chemistry",
            },
            {
                "id": "F2",
                "query": "What is the speed of light?",
                "must_contain": ["299", "300", "3×10", "3e8", "2.998"],
                "should_contain": ["speed", "light", "meter", "second"],
                "category": "physics",
            },
            {
                "id": "F3",
                "query": "What is the chemical formula for water?",
                "must_contain": ["H2O", "H₂O"],
                "should_contain": ["hydrogen", "oxygen"],
                "category": "chemistry",
            },
            {
                "id": "F4",
                "query": "What planet is closest to the Sun?",
                "must_contain": ["mercury"],
                "should_contain": ["planet", "sun", "closest"],
                "category": "astronomy",
            },
            {
                "id": "F5",
                "query": "What is the value of pi?",
                "must_contain": ["3.14", "π"],
                "should_contain": ["pi", "constant", "circle"],
                "category": "mathematics",
            },
        ],
    },
    "2_ubp_knowledge": {
        "description": "Does the GLM understand UBP-specific concepts?",
        "weight": 2.0,  # Double weight — this is the GLM's domain
        "tests": [
            {
                "id": "U1",
                "query": "What is the Universal Binary Principle?",
                "must_contain": ["substrate", "24", "bit", "binary", "principle"],
                "should_contain": ["golay", "leech", "coherence", "computational"],
                "category": "ubp_core",
            },
            {
                "id": "U2",
                "query": "What is NRCI and what does it measure?",
                "must_contain": ["nrci", "coherence"],
                "should_contain": ["normalized", "root", "measure", "index"],
                "category": "ubp_core",
            },
            {
                "id": "U3",
                "query": "Explain the Golay code and its role in the substrate.",
                "must_contain": ["golay", "error"],
                "should_contain": ["24", "12", "correction", "codeword", "bit"],
                "category": "ubp_core",
            },
            {
                "id": "U4",
                "query": "What is the Observer Constant?",
                "must_contain": ["observer", "constant"],
                "should_contain": ["Y", "pi", "coherence"],
                "category": "ubp_core",
            },
            {
                "id": "U5",
                "query": "How does the Leech lattice relate to the Golay code?",
                "must_contain": ["leech", "golay"],
                "should_contain": ["lattice", "24", "dimension", "sphere", "packing"],
                "category": "ubp_core",
            },
            {
                "id": "U6",
                "query": "What is the Triadic Monad?",
                "must_contain": ["pi", "phi", "e"],
                "should_contain": ["monad", "triadic", "product", "constant"],
                "category": "ubp_core",
            },
            {
                "id": "U7",
                "query": "What are the four ontological layers of the substrate?",
                "must_contain": ["reality", "information", "activation", "potential"],
                "should_contain": ["layer", "6-bit", "sextet", "ontological"],
                "category": "ubp_core",
            },
        ],
    },
    "3_mathematical_reasoning": {
        "description": "Can the GLM solve mathematical problems?",
        "weight": 1.5,
        "tests": [
            {
                "id": "M1",
                "query": "What is gcd(54, 24)?",
                "must_contain": ["6"],
                "should_contain": ["gcd", "greatest", "common", "divisor"],
                "category": "arithmetic",
            },
            {
                "id": "M2",
                "query": "Differentiate x^2 with respect to x.",
                "must_contain": ["2*x", "2x", "2"],
                "should_contain": ["derivative", "differentiate"],
                "category": "calculus",
            },
            {
                "id": "M3",
                "query": "What is 7 factorial?",
                "must_contain": ["5040"],
                "should_contain": ["factorial", "7"],
                "category": "arithmetic",
            },
            {
                "id": "M4",
                "query": "Find the dot product of <3, -1, 4> and <2, 5, -3>.",
                "must_contain": ["-11"],
                "should_contain": ["dot", "product"],
                "category": "linear_algebra",
            },
            {
                "id": "M5",
                "query": "Solve x^2 - 4 = 0 for x.",
                "must_contain": ["2", "-2"],
                "should_contain": ["solve", "x"],
                "category": "algebra",
            },
        ],
    },
    "4_reasoning": {
        "description": "Can the GLM perform logical reasoning?",
        "weight": 1.0,
        "tests": [
            {
                "id": "R1",
                "query": "If all mammals are warm-blooded, and a whale is a mammal, is a whale warm-blooded?",
                "must_contain": ["yes", "warm-blooded"],
                "should_contain": ["whale", "mammal"],
                "category": "logic",
            },
            {
                "id": "R2",
                "query": "What comes next in the sequence: 2, 4, 8, 16, ...?",
                "must_contain": ["32"],
                "should_contain": ["sequence", "double", "multiply"],
                "category": "pattern",
            },
            {
                "id": "R3",
                "query": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
                "must_contain": ["5 minutes", "5"],
                "should_contain": ["machine", "widget"],
                "category": "logic",
            },
        ],
    },
    "5_language_understanding": {
        "description": "Does the GLM understand natural language nuances?",
        "weight": 1.0,
        "tests": [
            {
                "id": "L1",
                "query": "What is the opposite of 'hot'?",
                "must_contain": ["cold"],
                "should_contain": ["opposite", "temperature"],
                "category": "semantics",
            },
            {
                "id": "L2",
                "query": "Explain the difference between 'affect' and 'effect'.",
                "must_contain": ["affect", "effect"],
                "should_contain": ["verb", "noun", "difference"],
                "category": "language",
            },
            {
                "id": "L3",
                "query": "What does 'ubiquitous' mean?",
                "must_contain": ["everywhere", "omnipresent", "universal", "widespread", "pervasive"],
                "should_contain": ["mean", "definition"],
                "category": "vocabulary",
            },
        ],
    },
    "6_conversation": {
        "description": "Can the GLM maintain multi-turn conversation?",
        "weight": 1.0,
        "tests": [
            {
                "id": "C1",
                "query": "My name is Alice. What is my name?",
                "must_contain": ["alice"],
                "should_contain": ["name"],
                "category": "context",
            },
            {
                "id": "C2",
                "query": "I just told you my name. What was it?",
                "must_contain": ["alice"],
                "should_contain": ["name", "told"],
                "category": "context",
                "depends_on": "C1",
            },
        ],
    },
    "7_explanation": {
        "description": "Can the GLM explain concepts clearly?",
        "weight": 1.0,
        "tests": [
            {
                "id": "E1",
                "query": "Explain gravity in simple terms.",
                "must_contain": ["gravity", "force", "mass"],
                "should_contain": ["attract", "pull", "object", "earth"],
                "category": "explanation",
                "min_length": 50,
            },
            {
                "id": "E2",
                "query": "What is photosynthesis?",
                "must_contain": ["photosynthesis", "plant", "light"],
                "should_contain": ["energy", "carbon dioxide", "oxygen", "glucose"],
                "category": "biology",
            },
        ],
    },
    "8_computation": {
        "description": "Can the GLM perform computational tasks?",
        "weight": 1.5,
        "tests": [
            {
                "id": "X1",
                "query": "Compute the magnitude of the vector <3, 4, 12>.",
                "must_contain": ["13"],
                "should_contain": ["magnitude", "vector"],
                "category": "computation",
            },
            {
                "id": "X2",
                "query": "Find the determinant of the matrix [[1, 2], [3, 4]].",
                "must_contain": ["-2"],
                "should_contain": ["determinant", "matrix"],
                "category": "linear_algebra",
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def score_response(response: str, test: dict) -> dict:
    """Score a GLM response against expected criteria."""
    resp_lower = response.lower()
    result = {
        "id": test["id"],
        "query": test["query"],
        "response_length": len(response),
        "must_score": 0,
        "should_score": 0,
        "length_score": 0,
        "total_score": 0,
        "max_score": 0,
        "details": {},
    }

    # Must-contain checks (critical — each is pass/fail)
    must_items = test.get("must_contain", [])
    must_hits = 0
    must_details = []
    for item in must_items:
        found = item.lower() in resp_lower
        if found:
            must_hits += 1
        must_details.append(f"{'✓' if found else '✗'} '{item}'")
    result["must_score"] = must_hits / max(len(must_items), 1)
    result["details"]["must"] = must_details

    # Should-contain checks (partial credit)
    should_items = test.get("should_contain", [])
    should_hits = 0
    should_details = []
    for item in should_items:
        found = item.lower() in resp_lower
        if found:
            should_hits += 1
        should_details.append(f"{'✓' if found else '✗'} '{item}'")
    result["should_score"] = should_hits / max(len(should_items), 1)
    result["details"]["should"] = should_details

    # Length score (longer = more thorough, up to a point)
    min_len = test.get("min_length", 30)
    if len(response) >= min_len:
        result["length_score"] = min(1.0, len(response) / 200)
    else:
        result["length_score"] = len(response) / min_len

    # Total: must-contain is pass/fail gate, should-contain and length are bonus
    if result["must_score"] >= 0.5:  # At least half of must-contain items found
        result["total_score"] = (
            result["must_score"] * 0.5 +
            result["should_score"] * 0.3 +
            result["length_score"] * 0.2
        )
    else:
        result["total_score"] = result["must_score"] * 0.5  # Partial credit for some must-hits

    result["max_score"] = 1.0
    result["pass"] = result["must_score"] >= 0.5

    return result


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_benchmark(rt):
    """Run the full benchmark suite against the GLM runtime."""
    print("=" * 70)
    print("GLM BENCHMARK SUITE v1.0")
    print("=" * 70)
    print(f"Testing against {sum(len(b['tests']) for b in BENCHMARKS.values())} test cases")
    print(f"across {len(BENCHMARKS)} categories")
    print("=" * 70)

    all_results = {}
    category_scores = {}
    total_tests = 0
    total_passed = 0
    total_score = 0.0
    total_max = 0.0

    for cat_name, cat_data in BENCHMARKS.items():
        print(f"\n{'─' * 60}")
        print(f"Category: {cat_name}")
        print(f"  {cat_data['description']}")
        print(f"  Weight: {cat_data['weight']}x")
        print(f"{'─' * 60}")

        cat_results = []
        cat_score = 0.0
        cat_max = 0.0
        cat_passed = 0

        for test in cat_data["tests"]:
            # Reset idea state between tests
            rt.reset_idea()

            # Run the query
            start = time.time()
            try:
                response = rt.chat(test["query"])
                elapsed = time.time() - start
            except Exception as e:
                response = f"ERROR: {e}"
                elapsed = 0.0

            # Score the response
            result = score_response(response, test)
            result["elapsed_ms"] = int(elapsed * 1000)
            result["response_preview"] = response[:200]
            cat_results.append(result)

            # Accumulate scores
            weighted_score = result["total_score"] * cat_data["weight"]
            weighted_max = result["max_score"] * cat_data["weight"]
            cat_score += weighted_score
            cat_max += weighted_max

            total_tests += 1
            total_score += weighted_score
            total_max += weighted_max

            if result["pass"]:
                cat_passed += 1
                total_passed += 1

            # Print result
            status = "PASS" if result["pass"] else "FAIL"
            print(f"\n  [{status}] {test['id']}: {test['query']}")
            print(f"    Score: {result['total_score']:.2f} | "
                  f"Must: {result['must_score']:.0%} | "
                  f"Should: {result['should_score']:.0%} | "
                  f"Time: {result['elapsed_ms']}ms")
            if not result["pass"]:
                print(f"    Response: {response[:150]}...")
                print(f"    Missing must-have: {[d for d in result['details']['must'] if '✗' in d]}")

        category_scores[cat_name] = {
            "score": cat_score,
            "max": cat_max,
            "pct": (cat_score / cat_max * 100) if cat_max > 0 else 0,
            "passed": cat_passed,
            "total": len(cat_data["tests"]),
            "weight": cat_data["weight"],
            "results": cat_results,
        }
        all_results[cat_name] = cat_results

        print(f"\n  Category Score: {cat_score:.2f}/{cat_max:.2f} "
              f"({category_scores[cat_name]['pct']:.1f}%) | "
              f"Passed: {cat_passed}/{len(cat_data['tests'])}")

    # ── FINAL REPORT ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("FINAL BENCHMARK REPORT")
    print("=" * 70)

    overall_pct = (total_score / total_max * 100) if total_max > 0 else 0
    print(f"\nOverall Score: {total_score:.2f}/{total_max:.2f} ({overall_pct:.1f}%)")
    print(f"Tests Passed: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")

    print(f"\n{'Category':<35} {'Score':>8} {'Pass Rate':>10} {'Weight':>8}")
    print("─" * 65)
    for cat_name, scores in category_scores.items():
        print(f"  {cat_name:<33} {scores['pct']:>6.1f}% "
              f"{scores['passed']}/{scores['total']:>8} "
              f"{scores['weight']:>6.1f}x")

    # ── STRENGTHS & WEAKNESSES ───────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("STRENGTHS (score >= 60%):")
    print(f"{'─' * 60}")
    for cat_name, scores in category_scores.items():
        if scores["pct"] >= 60:
            print(f"  ✓ {cat_name}: {scores['pct']:.1f}%")

    print(f"\n{'─' * 60}")
    print("WEAKNESSES (score < 60%):")
    print(f"{'─' * 60}")
    for cat_name, scores in category_scores.items():
        if scores["pct"] < 60:
            print(f"  ✗ {cat_name}: {scores['pct']:.1f}%")
            # List failed tests
            for r in scores["results"]:
                if not r["pass"]:
                    print(f"    - {r['id']}: {r['query'][:60]}")

    # ── COMPARISON TO MODERN LLMs ────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("COMPARISON TO MODERN LLMs (estimated)")
    print(f"{'=' * 70}")
    print("""
    Category               GLM      GPT-4    Claude   Gemini
    ─────────────────────────────────────────────────────────
    Factual Recall         {:.0f}%      95%      93%      92%
    UBP Knowledge          {:.0f}%      30%      25%      20%
    Math Reasoning         {:.0f}%      90%      88%      85%
    Logical Reasoning      {:.0f}%      88%      90%      87%
    Language Understanding {:.0f}%      95%      96%      93%
    Conversation           {:.0f}%      90%      92%      88%
    Explanation            {:.0f}%      92%      94%      90%
    Computation            {:.0f}%      85%      82%      80%
    ─────────────────────────────────────────────────────────
    Overall                {:.0f}%      88%      87%      84%
    """.format(
        category_scores.get("1_factual_recall", {}).get("pct", 0),
        category_scores.get("2_ubp_knowledge", {}).get("pct", 0),
        category_scores.get("3_mathematical_reasoning", {}).get("pct", 0),
        category_scores.get("4_reasoning", {}).get("pct", 0),
        category_scores.get("5_language_understanding", {}).get("pct", 0),
        category_scores.get("6_conversation", {}).get("pct", 0),
        category_scores.get("7_explanation", {}).get("pct", 0),
        category_scores.get("8_computation", {}).get("pct", 0),
        overall_pct,
    ))

    return {
        "overall_score": total_score,
        "overall_max": total_max,
        "overall_pct": overall_pct,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "category_scores": category_scores,
        "all_results": all_results,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from GLM00_config import KB_SYSTEM_PATH, KB_LANG_PATH
    GLM00_config = __import__('GLM00_config')
    GLM00_config.KB_SYSTEM_PATH = DATA_DIR / "ubp_system_kb.json"
    GLM00_config.KB_LANG_PATH = DATA_DIR / "ubp_lang_kb_combined_v4.json"

    from GLM11_runtime import GLMRuntimeV37

    print("Initializing GLM Runtime...")
    rt = GLMRuntimeV37(auto_expand=True)
    print(f"Vocab: {len(rt.vocab_dict)}, Edges: {len(rt.crg.edges)}")
    print()

    results = run_benchmark(rt)

    # Save results
    output_file = BASE_DIR / "benchmark_results.json"
    # Convert for JSON serialization
    save_data = {
        "overall_pct": results["overall_pct"],
        "total_tests": results["total_tests"],
        "total_passed": results["total_passed"],
        "categories": {},
    }
    for cat_name, scores in results["category_scores"].items():
        save_data["categories"][cat_name] = {
            "pct": scores["pct"],
            "passed": scores["passed"],
            "total": scores["total"],
            "weight": scores["weight"],
        }

    output_file.write_text(json.dumps(save_data, indent=2))
    print(f"\nResults saved to {output_file}")
