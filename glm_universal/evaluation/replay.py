"""The evaluation's replay gate: column 3 run for every answered case.

*Created 20 October 2026 (Phase 171: ``studies/EVIDENCE_IN_USE_STUDY.md``).*

Why this module exists
----------------------
The evaluation (:mod:`glm_universal.evaluation.harness`) scores what a user
sees: the answer line and the exit code.  It never runs an answer's column 3,
so a replay that no longer reproduces its answer goes unseen.  Phase 169 found
two such defects the first time every answer was read beside its replay
(``studies/EVIDENCE_MODEL_STUDY.md`` §7.3: ``trilinear 127 432 463`` and
``report language``), both invisible to the evaluation.

This gate closes that gap.  Every case the evaluation expects answered is run
the way the evaluation runs it -- a fresh interpreter per question, through
``GLM.py`` -- with ``--result --verify-tct``, which reads the answer into the
common result model (:mod:`glm_universal.runtime.evidence`) and replays its
column 3.  The gate fails when any replay that ran does not verify, when the
model's status disagrees with what the case expects, or when the process
errs.  An answer with no column 3 (``replayed`` is ``None``) is counted, not
failed: the surfaces without a column 3 are named in the study.

    PYTHONPATH=. python3 -m glm_universal.evaluation --replay --jobs 8
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Mapping, Sequence

from .cases import CASES, EvalCase
from .harness import CLI_PATH, PACKAGE_ROOT

#: The per-case time limit of the gate, in seconds.  A case's replay runs
#: its column 3 after its answer, and the Lean-corpus reports recompute their
#: measurement in column 3: `report relay` took about seven minutes, so the
#: evaluation's own 300 s would time them out (the first take of Phase 171).
REPLAY_TIMEOUT = 1200

__all__ = ["REPLAY_TIMEOUT", "replay_case", "replay_gate", "summarise", "format_replay",
           "gate_passes"]


def replay_case(case: EvalCase, timeout: int = REPLAY_TIMEOUT
                ) -> Dict[str, object]:
    """One case through ``GLM.py -q ... --result --verify-tct`` in a fresh
    interpreter; its result-model row, or the error that stopped it."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_ROOT)
    started = time.monotonic_ns()
    row: Dict[str, object] = {"id": case.id, "question": case.question,
                              "expect": case.expect}
    try:
        proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "-q", case.question, "--result",
             "--verify-tct"],
            cwd=str(PACKAGE_ROOT), env=env, capture_output=True, text=True,
            timeout=timeout)
    except subprocess.TimeoutExpired:
        row["error"] = f"timed out after {timeout}s"
        return row
    row["milliseconds"] = (time.monotonic_ns() - started) // 1_000_000
    if "Traceback (most recent call last)" in proc.stderr \
            or proc.returncode not in (0, 1):
        tail = (proc.stderr.strip().splitlines() or ["no stderr"])[-1]
        row["error"] = f"exit {proc.returncode}: {tail}"
        return row
    try:
        result = json.loads(proc.stdout)[0]
    except (ValueError, IndexError) as error:
        row["error"] = f"unreadable result: {error}"
        return row
    for key in ("status", "surface", "kind", "boundary", "replayed",
                "answer"):
        row[key] = result.get(key)
    return row


def replay_gate(cases: Sequence[EvalCase] = CASES, jobs: int = 4,
                timeout: int = REPLAY_TIMEOUT) -> Dict[str, object]:
    """Replay every case the evaluation expects answered; summarise."""
    chosen = [c for c in cases if c.expect == "answer"]
    started = time.monotonic_ns()
    if jobs <= 1:
        rows = [replay_case(c, timeout) for c in chosen]
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            rows = list(pool.map(lambda c: replay_case(c, timeout), chosen))
    report = summarise(rows)
    report["seconds"] = (time.monotonic_ns() - started) // 1_000_000_000
    return report


def summarise(rows: Sequence[Mapping[str, object]]) -> Dict[str, object]:
    """The gate's reading of the replayed rows (kept apart from running
    them, so that the rule can be checked on rows written by hand)."""
    errors = [r["id"] for r in rows if "error" in r]
    good = [r for r in rows if "error" not in r]
    disagree = [r["id"] for r in good
                if r["status"] not in ("answered", "open")]
    replayable = [r for r in good if r["replayed"] is not None]
    failed = [r["id"] for r in replayable if r["replayed"] is False]
    unreplayable = [r["id"] for r in good if r["replayed"] is None]
    return {"cases": len(rows), "replayable": len(replayable),
            "verified": len(replayable) - len(failed), "failed": failed,
            "unreplayable": unreplayable, "status_disagree": disagree,
            "errors": errors, "rows": list(rows), "seconds": 0}


def gate_passes(report: Mapping[str, object]) -> bool:
    """No replay failed, no status disagreed, no process erred, and at least
    one replay ran."""
    return (not report["failed"] and not report["status_disagree"]
            and not report["errors"] and report["replayable"] > 0)


def format_replay(report: Mapping[str, object]) -> str:
    lines: List[str] = [
        "replay gate (column 3 run for every case expected answered)",
        f"  cases {report['cases']}: replayable {report['replayable']}, "
        f"verified {report['verified']}, without a column 3 "
        f"{len(report['unreplayable'])}, in {report['seconds']} s"]
    for key, label in (("failed", "replay did not verify"),
                       ("status_disagree", "result model not answered"),
                       ("errors", "process error")):
        for cid in report[key]:
            lines.append(f"  FAIL {cid}: {label}")
    lines.append("  PASS" if gate_passes(report) else "  FAILED")
    return "\n".join(lines)
