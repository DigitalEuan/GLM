#!/usr/bin/env python3
"""Render the ¢ capability registry to machine-readable JSON.

The registry is the single source of truth for what the exact core claims:
primitive names, tiers, wire kinds, parameter contracts and honest capability
statuses.  Rendering it here keeps documentation from drifting away from code.

Usage
-----
    python3 tools/export_capabilities.py                  # stdout
    python3 tools/export_capabilities.py --out capabilities.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from cent_compiler.vocabulary import capability_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="-",
        help="output path, or '-' for stdout (default: '-')",
    )
    args = parser.parse_args(argv)

    payload = capability_report()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if args.out == "-":
        sys.stdout.write(text)
        return 0

    path = pathlib.Path(args.out)
    if path.parent != pathlib.Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(
        f"wrote {path}: {payload['atomic_count']} atomic + "
        f"{payload['composite_count']} composite primitives"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
