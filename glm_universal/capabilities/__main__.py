"""Run the capability probes from the command line.

```bash
PYTHONPATH=. python3 -m glm_universal.capabilities
PYTHONPATH=. python3 -m glm_universal.capabilities --area reals
```
"""

from __future__ import annotations

import argparse
from typing import List, Optional, Sequence

from .harness import AREAS, capability_report, get_probe, probe_names


def _format(report: dict) -> List[str]:
    lines: List[str] = []
    lines.append(f"{report['probes']} capability probes: "
                 f"{report['holds']} hold, {report['breaks']} break, "
                 f"{report['errors']} errored")
    if report["surprises"]:
        lines.append("SURPRISES (verdict differs from what was expected): "
                     + ", ".join(report["surprises"]))
    lines.append("")
    for area, counts in report["by_area"].items():
        lines.append(f"  {area:<16} holds {counts['holds']:>2}   "
                     f"breaks {counts['breaks']:>2}   "
                     f"errors {counts['error']:>2}")
    lines.append("")
    lines.append("WHERE IT BREAKS")
    for boundary in report["boundaries"]:
        lines.append("")
        lines.append(f"  {boundary['name']}  [{boundary['area']}]")
        lines.append(f"    {boundary['question']}")
        for chunk in boundary["boundary"].split(". "):
            lines.append(f"      {chunk.strip()}")
    return lines


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.capabilities",
        description="Run the GLM capability probes and report the boundaries.")
    parser.add_argument("--area", choices=AREAS, default=None,
                        help="restrict to one area")
    parser.add_argument("--probe", default=None, help="run a single probe")
    arguments = parser.parse_args(argv)

    if arguments.probe is not None:
        names = (arguments.probe,)
    elif arguments.area is not None:
        names = tuple(name for name in probe_names()
                      if get_probe(name).area == arguments.area)
    else:
        names = None

    report = capability_report(names)
    print("\n".join(_format(report)))
    return 1 if report["errors"] else 0


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
