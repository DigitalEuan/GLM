#!/usr/bin/env python3
"""Round 28: hook the new modules into ``glm_universal/runtime/toolbox.py`` (idempotent).

Run from the directory holding ``GLM.py`` after the Round 12 setup and the Round 13/16 overlays.

* ``tool induce``: a colour or shape task that the colour solver refuses is offered to the
  local-rule ladder (``reasoning/local_rule_induction.py``); answers the colour solver gives are
  unchanged.
* ``tool arc``: a stored task the colour solver refuses is offered to the local-rule ladder.
* ``tool theorem`` / ``tool discuss``: read over the Round 28 wheel
  (``reasoning/theorem_wheel_round28.py``): ledger carriers, P3 vocabulary, narrowest rungs.

Each hook only adds a fallback or a reading; it never changes an answer the GLM already gives.
"""
import sys

PATH = "glm_universal/runtime/toolbox.py"
MARK = "# Rule 30 study, Round 28"

HOOKS = [
    # tool induce: colour-task fallback
    ("""        ok, text, figures = ci.induce_colour_text(pairs, query)
        return ToolResult(ok, text, figures)""",
     """        ok, text, figures = ci.induce_colour_text(pairs, query)
        if not ok:  # Rule 30 study, Round 28: local-rule fallback (LocalRuleInduction.lean)
            from ..reasoning import local_rule_induction as lri
            lok, ltext, lfig = lri.induce_grids_text(pairs, query)
            if lok:
                return ToolResult(True, ltext, dict(lfig, colour_status=figures.get("status")))
        return ToolResult(ok, text, figures)"""),
    # tool arc: stored-task fallback
    ("""    ok, text, figures = ci.arc_text(arg)
    return ToolResult(ok, text, figures)""",
     """    ok, text, figures = ci.arc_text(arg)
    if not ok and figures.get("status") not in ("wrong",):  # Rule 30 study, Round 28
        from ..reasoning import local_rule_induction as lri
        lok, ltext, lfig = lri.arc_text(arg)
        if lfig.get("status") in ("right", "wrong"):
            return ToolResult(lok, ltext, dict(lfig, colour_status=figures.get("status")))
    return ToolResult(ok, text, figures)"""),
    # tool theorem
    ("""    from ..reasoning import theorem_wheel as tw
    ok, text, figures = tw.theorem_text(arg)
    return ToolResult(ok, text, figures)""",
     """    from ..reasoning import theorem_wheel_round28 as tw28  # Rule 30 study, Round 28
    ok, text, figures = tw28.theorem28_text(arg)
    return ToolResult(ok, text, figures)"""),
    # tool discuss
    ("""    from ..reasoning import theorem_wheel as tw
    ok, text, figures = tw.discuss_text(arg)
    return ToolResult(ok, text, figures)""",
     """    from ..reasoning import theorem_wheel_round28 as tw28  # Rule 30 study, Round 28
    ok, text, figures = tw28.discuss28_text(arg)
    return ToolResult(ok, text, figures)"""),
    ("""                return ToolResult(wok, "induce (wheel family; no kit family fits): " + wtext,
                                  wfig)
    return ToolResult(ok, text, figures)""",
     """                return ToolResult(wok, "induce (wheel family; no kit family fits): " + wtext,
                                  wfig)
    if not ok and pairs is not None:  # Rule 30 study, Round 28: local-rule fallback
        from ..reasoning import local_rule_induction as lri
        lok, ltext, lfig = lri.induce_grids_text(pairs, query)
        if lok:
            return ToolResult(True, ltext, dict(lfig, kit_status=figures.get("status")))
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
            print("round 28: hook site not found (toolbox changed?):\n" + old.splitlines()[0])
            return 1
        src = src.replace(old, new, 1)
        done += 1
    open(PATH, "w").write(src)
    print("round 28: %d toolbox hooks in place" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
