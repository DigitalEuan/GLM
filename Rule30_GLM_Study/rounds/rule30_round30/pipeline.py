#!/usr/bin/env python3
"""Round 30: run the whole GLM Rule 30 pipeline in one command.

    python3 pipeline.py [ARC_DIR] [statements|grids|all]      (default: all)

* ``statements`` -- stage 4: the planner over statements (``statement_planner.py``).  Writes
  ``statement_frontier.json`` (the frontier with its refutation witnesses, the input of the Lean
  certificates in ``RequestProject/GLM/Rule30/PipelineData.lean``) and ``proposals.json`` (the
  planner's surviving statements, in the format of the Round 27 GLM plug-in), and prints the
  Occam measurement for statements and the comparison with the Round 27 strategies.
* ``grids`` -- stages 1-3 on puzzles (``pipeline_bench.py``: plan, ask, gate; development sets and
  the fresh held-out set).

The outputs of the Round 30 run are stored next to this file (``*_output.txt``).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    args = [a for a in sys.argv[1:]]
    what = next((a for a in args if a in ("statements", "grids", "all")), "all")
    arc = next((a for a in args if a not in ("statements", "grids", "all")),
               os.environ.get("ARC_DIR", "arc_agi_17/data/training"))
    rc = 0
    if what in ("statements", "all"):
        print("=== stage 4: the planner over statements ===", flush=True)
        rc |= subprocess.call([sys.executable, os.path.join(
            HERE, "glm_overlay", "glm_universal", "reasoning", "statement_planner.py")])
    if what in ("grids", "all"):
        print("\n=== stages 1-3: plan, ask, gate (puzzles) ===", flush=True)
        rc |= subprocess.call([sys.executable, os.path.join(HERE, "pipeline_bench.py"), arc])
    return rc


if __name__ == "__main__":
    sys.exit(main())
