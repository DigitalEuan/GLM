"""Drive the CLI the way a user would, and score what comes back.

Every case in :mod:`glm_universal.evaluation.cases` is run by starting
``GLM.py`` in a **fresh interpreter** -- one subprocess per question, no shared
session, no warm caches, nothing the evaluation itself can prime.  What is
scored is exactly what a user would see: the process's exit code and the
``ANSWER`` or ``UNSOLVED`` line it printed.

The scoring is deliberately asymmetric.  Declining to answer is a small
failure; answering confidently and wrongly is a large one, because a refusal
tells the user where the machine stops and a wrong answer does not.  So an
outcome is one of

``correct``
    the question was answered and the answer contains the ground truth;
``refused_as_expected``
    the honest answer was a refusal and the machine refused;
``unexpected_refusal``
    the machine refused a question it should have answered -- a *gap*, worth
    zero;
``wrong_answer``
    the machine answered where it should have refused, or answered something
    that contradicts the ground truth -- worth **minus one**;
``error``
    the process crashed, timed out, or printed neither an answer nor a
    refusal -- also worth minus one, since a traceback is a wrong answer with
    extra steps.

``accuracy`` counts the first two as passes.  ``score`` is the weighted total
divided by the number of cases, so a run that is right about everything scores
``1`` and a run that is confidently wrong about everything scores ``-1``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .cases import CASES, EvalCase, cases_by_kind

__all__ = [
    "CLI_PATH", "PACKAGE_ROOT", "OUTCOMES", "WEIGHTS",
    "CaseResult", "run_case", "run_all", "evaluation_report", "format_report",
]

#: The directory that holds ``GLM.py`` and the package -- the directory a user
#: would be standing in.
PACKAGE_ROOT: Path = Path(__file__).resolve().parents[2]

#: The command-line entry point under test.
CLI_PATH: Path = PACKAGE_ROOT / "GLM.py"

#: The outcomes a case can have, worst last.
OUTCOMES: Tuple[str, ...] = (
    "correct", "refused_as_expected", "unexpected_refusal", "wrong_answer",
    "error")

#: What each outcome is worth.
WEIGHTS: Mapping[str, int] = {
    "correct": 1,
    "refused_as_expected": 1,
    "unexpected_refusal": 0,
    "wrong_answer": -1,
    "error": -1,
}

#: Phrases that mark an answer as a refusal even when the exit code is 0.
#: Each is a way the machine says "I will not guess".
REFUSAL_MARKERS: Tuple[str, ...] = (
    "unsolved:",
    "denotes nothing determinate",
    "no determinate referent",
    "are not distinguished",
    "unknown subject",
    "was not recognised",
    "did not resolve",
    "names no carrier",
)


@dataclass(frozen=True)
class CaseResult:
    """What running one case produced."""

    id: str
    kind: str
    question: str
    expect: str
    classification: str
    outcome: str
    returncode: int
    answer: str
    refused: bool
    stopped_at: str
    milliseconds: int

    @property
    def passed(self) -> bool:
        return self.outcome in ("correct", "refused_as_expected")

    @property
    def weight(self) -> int:
        return WEIGHTS[self.outcome]

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


def _answer_line(stdout: str) -> Tuple[str, bool]:
    """The answer the CLI printed, and whether it was a refusal."""
    answer = ""
    refused = False
    for line in stdout.splitlines():
        if line.startswith("ANSWER"):
            answer = line[len("ANSWER"):].strip()
        elif line.startswith("UNSOLVED"):
            answer = line[len("UNSOLVED"):].strip()
            refused = True
    lowered = answer.lower()
    if any(marker in lowered for marker in REFUSAL_MARKERS):
        refused = True
    return answer, refused


def _seconds_text(milliseconds: int) -> str:
    """Integer milliseconds as seconds to one decimal, without a float.

    The elapsed time is measured with :func:`time.monotonic_ns`, so it is an
    exact integer of nanoseconds throughout; this renders it for a human
    without ever constructing a floating-point number (directive D7).
    """
    tenths = (int(milliseconds) + 50) // 100
    return f"{tenths // 10}.{tenths % 10}"


def _missing(case: EvalCase, answer: str) -> List[str]:
    lowered = answer.lower()
    missing = [want for want in case.contains if want.lower() not in lowered]
    missing += [f"forbidden: {bad}" for bad in case.forbids
                if bad.lower() in lowered]
    return missing


def run_case(case: EvalCase, timeout: int = 300) -> CaseResult:
    """Run one case in a fresh interpreter and score it."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_ROOT)
    started = time.monotonic_ns()
    try:
        proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "-q", case.question,
             "--no-banner", "-c", "1"],
            cwd=str(PACKAGE_ROOT), env=env, capture_output=True, text=True,
            timeout=timeout)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return CaseResult(
            id=case.id, kind=case.kind, question=case.question,
            expect=case.expect, classification=case.classification,
            outcome="error", returncode=-1, answer="", refused=False,
            stopped_at=f"timed out after {timeout}s",
            milliseconds=(time.monotonic_ns() - started) // 1_000_000)
    milliseconds = (time.monotonic_ns() - started) // 1_000_000
    answer, refused = _answer_line(stdout)

    if code not in (0, 1) or "Traceback (most recent call last)" in stderr:
        tail = (stderr.strip().splitlines() or ["no stderr"])[-1]
        return CaseResult(
            id=case.id, kind=case.kind, question=case.question,
            expect=case.expect, classification=case.classification,
            outcome="error", returncode=code, answer=answer, refused=refused,
            stopped_at=f"exit {code}: {tail}",
            milliseconds=milliseconds)
    if not answer:
        return CaseResult(
            id=case.id, kind=case.kind, question=case.question,
            expect=case.expect, classification=case.classification,
            outcome="error", returncode=code, answer="", refused=False,
            stopped_at="the CLI printed neither an answer nor a refusal",
            milliseconds=milliseconds)

    if case.expect == "refusal":
        if refused:
            outcome, stopped = "refused_as_expected", ""
        else:
            outcome = "wrong_answer"
            stopped = (f"answered where the honest answer is a refusal "
                       f"({case.classification}): {answer}")
    else:
        if refused:
            outcome = "unexpected_refusal"
            stopped = answer
        else:
            missing = _missing(case, answer)
            if missing:
                outcome = "wrong_answer"
                stopped = (f"answer lacks {missing}: {answer}")
            else:
                outcome, stopped = "correct", ""

    return CaseResult(
        id=case.id, kind=case.kind, question=case.question,
        expect=case.expect, classification=case.classification,
        outcome=outcome, returncode=code, answer=answer, refused=refused,
        stopped_at=stopped, milliseconds=milliseconds)


def run_all(cases: Sequence[EvalCase] = CASES, jobs: int = 4,
            timeout: int = 300) -> Tuple[CaseResult, ...]:
    """Run every case, in parallel processes, and return the results in order."""
    if jobs <= 1:
        return tuple(run_case(case, timeout) for case in cases)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return tuple(pool.map(lambda c: run_case(c, timeout), cases))


def evaluation_report(cases: Sequence[EvalCase] = CASES, jobs: int = 4,
                      timeout: int = 300) -> Dict[str, object]:
    """Run the whole set and summarise it: totals, per kind, every failure."""
    started = time.monotonic_ns()
    results = run_all(cases, jobs=jobs, timeout=timeout)
    counts = {outcome: 0 for outcome in OUTCOMES}
    for result in results:
        counts[result.outcome] += 1
    total = len(results)
    passes = counts["correct"] + counts["refused_as_expected"]

    per_kind: Dict[str, Dict[str, object]] = {}
    for kind in cases_by_kind():
        group = [r for r in results if r.kind == kind]
        if not group:
            continue
        good = sum(1 for r in group if r.passed)
        per_kind[kind] = {
            "cases": len(group),
            "passed": good,
            "accuracy": f"{good}/{len(group)}",
            "wrong_answers": sum(1 for r in group
                                 if r.outcome == "wrong_answer"),
            "unexpected_refusals": sum(1 for r in group
                                       if r.outcome == "unexpected_refusal"),
            "errors": sum(1 for r in group if r.outcome == "error"),
        }

    failures = [r for r in results if not r.passed]
    return {
        "cases": total,
        "passed": passes,
        "accuracy": f"{passes}/{total}",
        "counts": counts,
        "score_numerator": sum(r.weight for r in results),
        "confidently_wrong": counts["wrong_answer"] + counts["error"],
        "per_kind": per_kind,
        "expected_refusals_boundary": sum(
            1 for r in results
            if r.expect == "refusal" and r.classification == "boundary"),
        "expected_refusals_gap": sum(
            1 for r in results
            if r.expect == "refusal" and r.classification == "gap"),
        "failures": [r.as_dict() for r in failures],
        "results": [r.as_dict() for r in results],
        "milliseconds": (time.monotonic_ns() - started) // 1_000_000,
    }


def format_report(report: Mapping[str, object]) -> str:
    """The report as a page of text."""
    lines: List[str] = []
    counts = report["counts"]                       # type: ignore[index]
    lines.append(
        f"{report['cases']} CLI cases: {report['accuracy']} passed "
        f"({counts['correct']} answered correctly, "
        f"{counts['refused_as_expected']} refused as expected), "
        f"{counts['unexpected_refusal']} unexpected refusals, "
        f"{counts['wrong_answer']} confidently wrong, "
        f"{counts['error']} errored")
    lines.append("")
    lines.append("PER QUERY KIND")
    for kind, stats in sorted(report["per_kind"].items()):  # type: ignore
        lines.append(
            f"  {kind:<12} {stats['accuracy']:>8}"
            f"   wrong {stats['wrong_answers']}"
            f"   refused {stats['unexpected_refusals']}"
            f"   errors {stats['errors']}")
    failures = report["failures"]                   # type: ignore[index]
    lines.append("")
    if not failures:
        lines.append("no failures")
    else:
        lines.append("FAILURES")
        for failure in failures:                    # type: ignore[union-attr]
            lines.append(f"  {failure['id']}  [{failure['outcome']}]"
                         f"  ({failure['kind']})")
            lines.append(f"    q: {failure['question']}")
            lines.append(f"    stops at: {failure['stopped_at']}")
    lines.append("")
    lines.append(
        f"expected refusals: {report['expected_refusals_boundary']} boundary, "
        f"{report['expected_refusals_gap']} gap")
    lines.append(f"ran in {_seconds_text(report['milliseconds'])}s")
    return "\n".join(lines)


def write_json(report: Mapping[str, object], path: Path) -> None:
    """Save a report for comparison with a later run."""
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
