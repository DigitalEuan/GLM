"""``glm_universal.reasoning.pipeline_tool`` -- ``tool pipeline`` (Round 30 of the Rule 30 study).

Reports the four stages of the pipeline and the statement frontier that stage 4 generated and
Lean certified (``_data/r30_frontier.json``; Lean ``GLM.Rule30.PipelineData``).  Kept apart from
``glm_pipeline.py`` so that the planner module stays byte-identical to the version frozen for the
Round 30 held-out scoring.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Tuple

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_data", "r30_frontier.json")

STAGES = [
    ("1 plan", "breadth-first plans with merging (Round 29), plus fitted middle steps read "
     "backwards from the goal through a symmetry or upscale, a scale factor read from the grid, "
     "line drawing, per-object moves, positional crops; the last layer pruned by the goal's "
     "shape", "GLM.Pipeline.semMid_eq_some_iff, GLM.Pipeline.shapePrune_skip"),
    ("2 ask", "on a refusal, ask the oracle for the cell (or output size) the refusal names and "
     "decide again on the same search", "GLM.Pipeline.askLoop_correct"),
    ("3 gate", "leave-one-out from plan depth 1 when there are at most two demonstrations, from "
     "depth 2 otherwise; every wrong answer is an Occam failure",
     "GLM.Pipeline.minAgree_wrong_imp, GLM.Pipeline.gated_correct"),
    ("4 statements", "the same planner over Lean statement families: steps steeper / implies / "
     "analogy, fitted offset = the least surviving one, frontier certified in Lean",
     "GLM.Rule30.PipelineData.frontier_round30"),
]


def pipeline_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    arg = (arg or "").strip().lower()
    if arg.startswith("frontier"):
        try:
            data = json.load(open(DATA))
        except (OSError, ValueError):
            return False, "pipeline: frontier data missing (%s)" % DATA, {}
        lines = ["statement frontier (sharp on its range; Lean %s):" % data["lean"]]
        for row in data["frontier"]:
            lines.append("  %s p=%d %s=%d offset=%d  holds for d <= %d, offset-1 refuted  [%s]" % (
                row["family"], row["period"], row["param_name"], row["param"], row["offset"],
                row["range"], row["lean"]))
        return True, "\n".join(lines), dict(data)
    lines = ["Rule 30 pipeline (Round 30):"]
    for name, what, lean in STAGES:
        lines.append("  stage %s: %s  [%s]" % (name, what, lean))
    lines.append("  `tool pipeline frontier` lists the certified statement frontier")
    return True, "\n".join(lines), {"stages": [s[0] for s in STAGES]}
