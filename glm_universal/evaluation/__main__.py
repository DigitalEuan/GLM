"""Run the end-to-end CLI evaluation.

    PYTHONPATH=. python3 -m glm_universal.evaluation
    PYTHONPATH=. python3 -m glm_universal.evaluation --only report --jobs 8
    PYTHONPATH=. python3 -m glm_universal.evaluation --json results.json

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
    parser.add_argument("--timeout", type=float, default=300.0,
                        help="per-case timeout in seconds")
    parser.add_argument("--json", metavar="PATH", default=None,
                        help="also write the full report as JSON")
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

    report = evaluation_report(cases, jobs=args.jobs, timeout=args.timeout)
    print(format_report(report))
    if args.json:
        write_json(report, Path(args.json))
    return 0 if report["passed"] == report["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
