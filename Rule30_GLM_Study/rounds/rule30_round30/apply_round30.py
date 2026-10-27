#!/usr/bin/env python3
"""Round 30: hook the pipeline into ``glm_universal/runtime/toolbox.py`` (idempotent).  Run from
the directory holding ``GLM.py`` after the Round 29 setup.

* ``tool induce`` (both routes) and ``tool arc``: when the Round 29 planner also refuses, the task
  is offered to the Round 30 pipeline (``reasoning/glm_pipeline.py``; Lean ``GLM.Pipeline``),
  whose hypothesis space adds fitted middle steps, line drawing, per-object moves and positional
  crops.  It answers only under the same agreement rule; a refusal names the question to ask.
* ``tool pipeline``: the four stages, and the statement planner's certified frontier
  (``reasoning/_data/r30_frontier.json``; Lean ``GLM.Rule30.PipelineData.frontier_round30``).

Each hook only adds a fallback; it never changes an answer the GLM already gives.
"""
import sys

PATH = "glm_universal/runtime/toolbox.py"

HOOKS = [
    # tool induce, colour route
    ("""            pok, ptext, pfig = gpl.induce_text(pairs, query)
            if pok:
                return ToolResult(True, ptext, dict(pfig, colour_status=figures.get("status")))
        return ToolResult(ok, text, figures)""",
     """            pok, ptext, pfig = gpl.induce_text(pairs, query)
            if pok:
                return ToolResult(True, ptext, dict(pfig, colour_status=figures.get("status")))
            from ..reasoning import glm_pipeline as gpp  # Rule 30 study, Round 30: pipeline
            qok, qtext, qfig = gpp.induce_text(pairs, query)
            if qok:
                return ToolResult(True, qtext, dict(qfig, colour_status=figures.get("status")))
        return ToolResult(ok, text, figures)"""),
    # tool induce, binary route
    ("""        pok, ptext, pfig = gpl.induce_text(pairs, query)
        if pok:
            return ToolResult(True, ptext, dict(pfig, kit_status=figures.get("status")))
    return ToolResult(ok, text, figures)""",
     """        pok, ptext, pfig = gpl.induce_text(pairs, query)
        if pok:
            return ToolResult(True, ptext, dict(pfig, kit_status=figures.get("status")))
        from ..reasoning import glm_pipeline as gpp  # Rule 30 study, Round 30: pipeline
        qok, qtext, qfig = gpp.induce_text(pairs, query)
        if qok:
            return ToolResult(True, qtext, dict(qfig, kit_status=figures.get("status")))
    return ToolResult(ok, text, figures)"""),
    # tool arc
    ("""        pok, ptext, pfig = gpl.arc_text(arg)
        if pfig.get("status") in ("right", "wrong"):
            return ToolResult(pok, ptext, dict(pfig, colour_status=figures.get("status")))
    return ToolResult(ok, text, figures)""",
     """        pok, ptext, pfig = gpl.arc_text(arg)
        if pfig.get("status") in ("right", "wrong"):
            return ToolResult(pok, ptext, dict(pfig, colour_status=figures.get("status")))
        from ..reasoning import glm_pipeline as gpp  # Rule 30 study, Round 30: pipeline
        qok, qtext, qfig = gpp.arc_text(arg)
        if qfig.get("status") in ("right", "wrong"):
            return ToolResult(qok, qtext, dict(qfig, colour_status=figures.get("status")))
    return ToolResult(ok, text, figures)"""),
    # tool pipeline: the runner and its registry entry
    ("""TOOLS: Tuple[Tool, ...] = (
""",
     """def _pipeline(arg: str) -> ToolResult:  # Rule 30 study, Round 30
    \"\"\"``[frontier]``: the Round 30 pipeline's stages, or the statement planner's frontier
    certified in Lean (``reasoning/_data/r30_frontier.json``).\"\"\"
    from ..reasoning import pipeline_tool as ptl
    ok, text, figures = ptl.pipeline_text(arg)
    return ToolResult(ok, text, figures)


TOOLS: Tuple[Tool, ...] = (
    Tool("pipeline", "reasoning.pipeline_tool", "the Rule 30 pipeline of Round 30: plan (with "
         "fitted middle steps and goal-shape pruning), ask the question a refusal names, gate "
         "by leave-one-out when demonstrations are few, and plan over statements; "
         "`tool pipeline frontier` lists the statement frontier certified in Lean",
         "derive, refusal", ("RequestProject/GLM/Rule30/Pipeline.lean",
                             "RequestProject/GLM/Rule30/PipelineData.lean"),
         "rule30_round30/README.md", _pipeline, takes="nothing, or `frontier`"),
"""),
]


def main() -> int:
    src = open(PATH).read()
    done = 0
    for old, new in HOOKS:
        if new in src:
            done += 1
            continue
        if old not in src:
            print("round 30: hook site not found (run the Round 29 setup first?):\n"
                  + old.splitlines()[0])
            return 1
        src = src.replace(old, new, 1)
        done += 1
    open(PATH, "w").write(src)
    print("round 30: %d toolbox hooks in place" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
