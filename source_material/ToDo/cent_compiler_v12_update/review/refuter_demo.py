#!/usr/bin/env python3
"""Working Tier-D demonstration: print the generated refutation ledger."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler.refutation import build_ledger, render_ledger  # noqa: E402


def main() -> int:
    payload = build_ledger()
    if "--json" in sys.argv[1:]:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_ledger(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
