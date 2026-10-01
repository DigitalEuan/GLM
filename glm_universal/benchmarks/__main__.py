"""Run the benchmark suites from the command line.

```bash
PYTHONPATH=. python3 -m glm_universal.benchmarks
PYTHONPATH=. python3 -m glm_universal.benchmarks --write
PYTHONPATH=. python3 -m glm_universal.benchmarks golay_correction
```

Exit code 0 when every suite beat its baseline, 1 when any suite returned a
null or below-baseline result.  A null result is not a crash, so it is not
reported as one — but it is not a success either, and the exit code says so.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from .harness import benchmark_report, suite_names, write_results


def _format(report: dict) -> List[str]:
    lines: List[str] = []
    lines.append(f"run {report['run_id']}: "
                 f"{report['passed_count']}/{report['task_count']} tasks "
                 f"across {report['suite_count']} suites "
                 f"({report['overall_score']})")
    lines.append("")
    for suite in report["suites"]:
        lines.append(f"  {suite['name']}  [{suite['tier']['tier']}]")
        lines.append(f"    {suite['question']}")
        lines.append(f"    score {suite['passed']}/{suite['total']} "
                     f"= {suite['score']}, baseline {suite['baseline']}, "
                     f"verdict {suite['verdict']}")
        for key, value in sorted(suite["measurements"].items()):
            lines.append(f"    {key}: {value}")
        for finding in suite["findings"]:
            lines.append(f"    finding [{finding['key']}]: "
                         f"{finding['statement']}")
        lines.append("")
    if report["null_results"]:
        lines.append(f"null or below-baseline suites: "
                     f"{', '.join(report['null_results'])}")
    else:
        lines.append("every suite beat its declared baseline")
    return lines


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.benchmarks",
        description="Run the GLM benchmark suites and score them against "
                    "their declared baselines.")
    parser.add_argument("suite", nargs="*", default=None,
                        help=f"suites to run (default: all). "
                             f"Known: {', '.join(suite_names())}")
    parser.add_argument("--write", action="store_true",
                        help="write the scores into benchmarks/results/")
    parser.add_argument("--list", action="store_true",
                        help="list the suites and exit")
    args = parser.parse_args(argv)

    if args.list:
        for name in suite_names():
            print(name)
        return 0

    chosen = args.suite or None
    report = (write_results(names=chosen) if args.write
              else benchmark_report(chosen))
    print("\n".join(_format(report)))
    return 1 if report["null_results"] else 0


if __name__ == "__main__":            # pragma: no cover -- entry point
    sys.exit(main())
