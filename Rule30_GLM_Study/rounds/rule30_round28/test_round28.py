#!/usr/bin/env python3
"""Round 28 checks (run from the directory holding GLM.py, PYTHONPATH=.).

1. local-rule induction: answers a local task, refuses an unseen key, refuses a clash, and the
   refusal agrees with "the surviving encodings disagree" (LocalRuleInduction.lean);
2. the toolbox hooks: ``tool induce`` answers a colour local-rule task, ``tool arc`` still runs;
3. the Round 28 wheel: the narrowest rung of P1, the P3 spoke and control, ledger carriers.
"""
import sys

from glm_universal.reasoning import local_rule_induction as lri
from glm_universal.reasoning import theorem_wheel_round28 as tw28
from glm_universal.runtime.toolbox import run_tool

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# 1. local rules ------------------------------------------------------------------------------
recol = lambda g: [[{0: 0, 1: 4, 2: 7}[v] for v in row] for row in g]
d1, d2 = [[1, 0], [2, 1]], [[0, 2], [1, 0]]
ans, why = lri.induce_grids([(d1, recol(d1)), (d2, recol(d2))], [[2, 2], [1, 0]])
check("recolour answered by the cell reader", ans == [[7, 7], [4, 0]] and why == "cell")
ans, why = lri.induce_grids([(d1, recol(d1))], [[3, 0], [0, 0]])
check("unseen colour refused", ans is None)
clash = [([[1]], [[2]]), ([[1]], [[3]])]
check("a clash refutes every reader", lri.table(lri.r_cell, clash) is None)

# 2. toolbox hooks ----------------------------------------------------------------------------
r = run_tool("tool induce 102 / 010 -> 407 / 040 ; 210 / 001 -> 740 / 004 ? 012 / 120")
check("tool induce answers a colour local-rule task", r.ok and "047 / 470" in r.text)
r = run_tool("tool arc 00dbd492")
check("tool arc runs (refuses or answers, never crashes)", isinstance(r.text, str))

# 3. the Round 28 wheel -----------------------------------------------------------------------
ok, text, _ = tw28.theorem28_text("narrowest P1")
check("narrowest P1 names AmortizedHalving241", ok and "AmortizedHalving241" in text)
ok, text, _ = tw28.theorem28_text("derive P3Eventual => P3")
check("P3Eventual => P3 derived", "DERIVED" in text)
ok, text, _ = tw28.theorem28_text("derive LightConeCircuitBound => P3")
check("light-cone circuit bound blocked from P3", "=/=>" in text)
check("ledger carriers installed", len(tw28.carriers()) > 0)

print("round 28: all checks pass" if not fails else "round 28: %d FAILED" % len(fails))
sys.exit(1 if fails else 0)
