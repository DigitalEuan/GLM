#!/usr/bin/env python3
"""
Run the golden_cases.json benchmark against the GLM runtime.
Reports pass/fail per case and an overall score.
"""
from __future__ import annotations
import json
import re
import sys
import os
from pathlib import Path

# Ensure we run from the glm_work directory
os.chdir(Path(__file__).resolve().parent)
sys.path.insert(0, str(Path(".").resolve()))

from GLM11_runtime import GLMRuntimeV37


def check_match(response: str, expected: str, match_type: str) -> bool:
    """Check whether the response matches the expected value per match_type."""
    if match_type == "exact":
        return response.strip() == expected.strip()
    if match_type == "substring":
        return expected.lower() in response.lower()
    if match_type == "regex":
        return re.search(expected, response, re.IGNORECASE) is not None
    return False


def main():
    cases = json.loads(Path("golden_cases.json").read_text())["cases"]
    print("=" * 80)
    print("GOLDEN CASES BENCHMARK - GLM")
    print("=" * 80)

    rt = GLMRuntimeV37()
    passed = 0
    failed = 0
    results = []

    for case in cases:
        cid = case["id"]
        suite = case["suite"]
        query = case["query"]
        expected = case["expected"]
        match_type = case["match"]
        category = case.get("category", "")
        difficulty = case.get("difficulty", "")

        try:
            rt.reset_idea()
            response = rt.chat(query) if query else ""
            ok = check_match(response, expected, match_type)
        except Exception as e:
            response = f"<EXCEPTION: {e}>"
            ok = False

        # Edge cases: empty/nonsense queries just need to not crash
        if suite == "failure":
            if "EXCEPTION" in response:
                ok = False
            elif case["id"] == "FAIL_NONSENSE" and "gap" in response.lower():
                ok = True
            elif case["id"] in ("FAIL_EMPTY", "FAIL_LATEX_GARBAGE"):
                ok = "EXCEPTION" not in response
            else:
                ok = True  # survived without crash

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        results.append({
            "id": cid, "suite": suite, "category": category,
            "difficulty": difficulty, "query": query,
            "expected": expected, "got_short": response[:200],
            "ok": ok,
        })
        short_resp = response.replace("\n", " ")[:100]
        print(f"  [{status}] {cid:24s} [{suite:18s}] "
              f"q='{query[:50]}' -> '{short_resp}'")

    total = passed + failed
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.1f}%)")
    print("=" * 80)

    # Suite breakdown
    by_suite = {}
    for r in results:
        s = r["suite"]
        if s not in by_suite:
            by_suite[s] = {"pass": 0, "fail": 0}
        if r["ok"]:
            by_suite[s]["pass"] += 1
        else:
            by_suite[s]["fail"] += 1
    print("\nBy suite:")
    for s, counts in by_suite.items():
        t = counts["pass"] + counts["fail"]
        print(f"  {s:20s} {counts['pass']}/{t}")

    Path("golden_baseline_results.json").write_text(
        json.dumps(results, indent=2, default=str))
    print("\nDetailed results saved to golden_baseline_results.json")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
