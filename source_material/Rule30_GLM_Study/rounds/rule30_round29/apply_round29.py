#!/usr/bin/env python3
"""Round 29: hook the stepwise grid planner into ``glm_universal/runtime/toolbox.py``
(idempotent).  Run from the directory holding ``GLM.py`` after the Round 28 setup.

* ``tool induce`` (both colour and binary routes) and ``tool arc``: when the existing solvers
  and the Round 28 local-rule ladder refuse, the task is offered to the multi-step planner
  (``reasoning/grid_planner.py``; Lean ``GLM.PlanSearch``).  The planner answers only when
  every consistent plan of the cheapest tier agrees; otherwise the refusal stands.

Each hook only adds a fallback; it never changes an answer the GLM already gives.
"""
import sys

PATH = "glm_universal/runtime/toolbox.py"

HOOKS = [
    # tool induce, colour route
    ("""            lok, ltext, lfig = lri.induce_grids_text(pairs, query)
            if lok:
                return ToolResult(True, ltext, dict(lfig, colour_status=figures.get("status")))
        return ToolResult(ok, text, figures)""",
     """            lok, ltext, lfig = lri.induce_grids_text(pairs, query)
            if lok:
                return ToolResult(True, ltext, dict(lfig, colour_status=figures.get("status")))
            from ..reasoning import grid_planner as gpl  # Rule 30 study, Round 29: planner
            pok, ptext, pfig = gpl.induce_text(pairs, query)
            if pok:
                return ToolResult(True, ptext, dict(pfig, colour_status=figures.get("status")))
        return ToolResult(ok, text, figures)"""),
    # tool induce, binary route
    ("""        lok, ltext, lfig = lri.induce_grids_text(pairs, query)
        if lok:
            return ToolResult(True, ltext, dict(lfig, kit_status=figures.get("status")))
    return ToolResult(ok, text, figures)""",
     """        lok, ltext, lfig = lri.induce_grids_text(pairs, query)
        if lok:
            return ToolResult(True, ltext, dict(lfig, kit_status=figures.get("status")))
        from ..reasoning import grid_planner as gpl  # Rule 30 study, Round 29: planner
        pok, ptext, pfig = gpl.induce_text(pairs, query)
        if pok:
            return ToolResult(True, ptext, dict(pfig, kit_status=figures.get("status")))
    return ToolResult(ok, text, figures)"""),
    # tool arc
    ("""        lok, ltext, lfig = lri.arc_text(arg)
        if lfig.get("status") in ("right", "wrong"):
            return ToolResult(lok, ltext, dict(lfig, colour_status=figures.get("status")))
    return ToolResult(ok, text, figures)""",
     """        lok, ltext, lfig = lri.arc_text(arg)
        if lfig.get("status") in ("right", "wrong"):
            return ToolResult(lok, ltext, dict(lfig, colour_status=figures.get("status")))
        from ..reasoning import grid_planner as gpl  # Rule 30 study, Round 29: planner
        pok, ptext, pfig = gpl.arc_text(arg)
        if pfig.get("status") in ("right", "wrong"):
            return ToolResult(pok, ptext, dict(pfig, colour_status=figures.get("status")))
    return ToolResult(ok, text, figures)"""),
]


def main() -> int:
    src = open(PATH).read()
    done = 0
    for old, new in HOOKS:
        if new in src:
            done += 1
            continue
        if old not in src:
            print("round 29: hook site not found (run the Round 28 setup first?):\n"
                  + old.splitlines()[0])
            return 1
        src = src.replace(old, new, 1)
        done += 1
    open(PATH, "w").write(src)
    print("round 29: %d toolbox hooks in place" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
