#!/usr/bin/env python3
"""Canonical current test gate: run all suites and fail on any failure."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

from check_docs_consistency import check_readme_consistency

ROOT = Path(__file__).resolve().parent.parent

SUITES = (
    "test_assembly.py",
    "test_discovery.py",
    "test_workflow.py",
    "test_hypothesis_promotion.py",
    "test_transfer_contracts.py",
    "test_transfer_evaluation.py",
    "test_evaluation_sabotage.py",
    "test_ablation.py",
    "test_log_domain.py",
    "test_self_target.py",
    "test_refutation.py",
    "test_holdout.py",
    "test_moves.py",
    "test_proposals.py",
    "test_machine.py",
    "test_question_corpus.py",
    "test_glm_application_audit.py",
    "test_glm_direct_questions.py",
    "test_webui.py",
    "test_core.py",
    "test_ui.py",
    "test_binding.py",
    "test_design.py",
    "test_physical.py",
    "test_fabrication.py",
    "test_dynamics.py",
)


def main() -> int:
    print("=" * 78)
    print("CENT COMPILER — CURRENT TEST GATE")
    print("=" * 78)

    started = time.monotonic()
    passed = 0
    suite_counts: dict[str, tuple[int, int]] = {}
    for suite in SUITES:
        path = ROOT / "tests" / suite
        print(f"\n>>> {suite}", flush=True)
        suite_started = time.monotonic()
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        elapsed = time.monotonic() - suite_started
        ok = result.returncode == 0
        passed += int(ok)
        counts = re.findall(r"(\d+)/(\d+) checks passed", result.stdout)
        if counts:
            suite_counts[suite] = (int(counts[-1][0]), int(counts[-1][1]))
        print(
            f"<<< {suite}: {'PASS' if ok else 'FAIL'} ({elapsed:.1f}s)",
            flush=True,
        )

    elapsed = time.monotonic() - started
    problems = check_readme_consistency(ROOT, suite_counts)
    print("\n" + "=" * 78)
    print(f"GATE SUMMARY: {passed}/{len(SUITES)} suites passed ({elapsed:.1f}s)")
    if problems:
        print("README CONSISTENCY: FAIL")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("README CONSISTENCY: OK (package tree, total and test_ui counts)")
    print("=" * 78)
    return 0 if passed == len(SUITES) and not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
