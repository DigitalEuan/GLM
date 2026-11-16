#!/usr/bin/env python3
"""Census of the received Lean deliveries against the build tree.

*Created 15 November 2026 (platform round, P4 intake; Phase 189).*

The measurement lives in the package, at
``glm_universal.corpus.lean_deliveries.census_report`` — the tier-0 block of
[`studies/LEAN_DELIVERIES_CENSUS_STUDY.md`](../LEAN_DELIVERIES_CENSUS_STUDY.md)
has to name something that resolves, and a study script is not importable from
the package.  This runner is the same command the study quotes.

Run from the repository root (reads `source_material/` and `src/lean/`, writes
nothing)::

    PYTHONPATH=src python3 studies/scripts/lean_to_add_census.py
    PYTHONPATH=src python3 studies/scripts/lean_to_add_census.py --json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from glm_universal.corpus.lean_deliveries import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
