"""Run the end-to-end CLI evaluation.

    PYTHONPATH=. python3 -m glm_universal.evaluation
    PYTHONPATH=. python3 -m glm_universal.evaluation --only report --jobs 8
    PYTHONPATH=. python3 -m glm_universal.evaluation --json results.json
    PYTHONPATH=. python3 -m glm_universal.evaluation --replay --jobs 8
    PYTHONPATH=. python3 -m glm_universal.evaluation --replay-only --jobs 8

``--replay`` (Phase 171) also runs column 3 for every case expected answered
(``evaluation/replay.py``) and fails when a replay does not verify.
``--replay-only`` (Phase 174) runs the replay gate without the evaluation: it
is the command of the sign-off's ``replay`` instrument, so the gate is a step
of ``signoff --close`` and re-runs only when what it read has moved.

*Last altered 20 October 2026 (Phase 174: ``--replay-only``; Phase 171:
``--replay``).*

Exit code 0 when every case passes, 1 when any case fails.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .cases import CASES
from .harness import evaluation_report, format_report, write_json


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.evaluation",
        description="drive the CLI over a fixed question set and score it")
    parser.add_argument("--only", metavar="KIND", default=None,
                        help="restrict to one query kind")
    parser.add_argument("--case", metavar="ID", default=None,
                        help="run a single case by id")
    parser.add_argument("--jobs", type=int, default=4,
                        help="how many CLI processes to run at once")
    parser.add_argument("--timeout", type=int, default=300,
                        help="per-case timeout in seconds")
    parser.add_argument("--json", metavar="PATH", default=None,
                        help="also write the full report as JSON")
    parser.add_argument("--replay", action="store_true",
                        help="also replay column 3 for every case expected "
                             "answered and fail if any does not verify "
                             "(Phase 171)")
    parser.add_argument("--replay-only", action="store_true",
                        help="run only the replay gate, not the evaluation "
                             "(the sign-off's replay instrument; Phase 174)")
    parser.add_argument("--replay-timeout", type=int, default=None,
                        help="per-case timeout of the replay gate in seconds "
                             "(default: evaluation.replay.REPLAY_TIMEOUT)")
    parser.add_argument("--list", action="store_true",
                        help="list the cases and exit")
    args = parser.parse_args()

    cases = CASES
    if args.only:
        cases = tuple(c for c in cases if c.kind == args.only)
    if args.case:
        cases = tuple(c for c in cases if c.id == args.case)
    if not cases:
        print("no cases selected")
        return 2

    if args.list:
        for case in cases:
            print(f"{case.id:<28} {case.kind:<10} {case.expect:<8} "
                  f"{case.question}")
        return 0

    ok = True
    if not args.replay_only:
        report = evaluation_report(cases, jobs=args.jobs,
                                   timeout=args.timeout)
        print(format_report(report))
        if args.json:
            write_json(report, Path(args.json))
        ok = report["passed"] == report["cases"]
    if args.replay or args.replay_only:
        from .replay import (REPLAY_TIMEOUT, format_replay, gate_passes,
                             replay_gate)
        replayed = replay_gate(cases, jobs=args.jobs,
                               timeout=args.replay_timeout or REPLAY_TIMEOUT)
        print(format_replay(replayed))
        ok = ok and gate_passes(replayed)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
