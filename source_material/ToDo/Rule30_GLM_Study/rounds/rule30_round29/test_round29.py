#!/usr/bin/env python3
"""Round 29 checks (run from the directory holding GLM.py, PYTHONPATH=.).

1. the planner: a two-step task (crop, then mirror) is answered with the right plan; a task no
   plan expresses is refused; two consistent plans that disagree on the query make it refuse
   (``planner_agree_all``); merging uses the queries as probes (``train_only_signature_unsound``);
2. the toolbox hooks: ``tool induce`` answers a multi-step task that the one-step ladder refuses;
   ``tool arc`` answers a stored task by a plan;
3. Round 28 still passes (run separately by ``setup_round28.sh``).
"""
import sys

from glm_universal.reasoning import grid_planner as gp
from glm_universal.runtime.toolbox import run_tool

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# 1. the planner -------------------------------------------------------------------------------
def task(rule, grids):
    return [(g, [list(r) for r in rule(gp.G(g))]) for g in grids]


crop_mirror = lambda g: gp.s_mirror_h(gp.s_crop_bbox(g))
demos = [[[0, 0, 0, 0], [0, 1, 2, 0], [0, 0, 3, 0], [0, 0, 0, 0]],
         [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 4, 4, 0, 0], [0, 5, 0, 0, 0]],
         [[2, 0, 0], [6, 7, 0], [0, 0, 0]]]
query = [[0, 0, 0], [0, 8, 1], [0, 1, 0]]
r = gp.solve(task(crop_mirror, demos), [query], max_depth=2)
check("two-step task answered (crop, then mirror)",
      r["status"] == "answered" and r["answer"][0] == [list(x) for x in crop_mirror(gp.G(query))])
check("the chosen plan has two steps", r.get("depth") == 2)

sort_rows = lambda g: sorted(g, key=lambda row: (sum(v != 0 for v in row), row))
d2 = [[[0, 1, 0], [1, 1, 0], [0, 0, 0]], [[2, 2, 2], [0, 0, 0], [0, 2, 0]],
      [[0, 0, 3], [3, 3, 3], [3, 0, 0]]]
r = gp.solve(task(sort_rows, d2), [[[4, 4, 0], [0, 0, 0], [4, 4, 4]]], max_depth=2, budget_s=10)
check("a task outside the alphabet is refused", r["status"] == "refused")

# flip_h and flip_v (equal Occam weight) agree on the demonstration but not on the query
demo = [[1, 2], [2, 1]]
r = gp.solve([(demo, [list(x) for x in gp.flip_h(gp.G(demo))])], [[[1, 2], [3, 4]]],
             max_depth=1, finishers=[("identity", None)])
check("consistent plans that disagree on the query: refused",
      r["status"] == "refused" and "disagree" in r.get("why", ""))

# 2. toolbox hooks -----------------------------------------------------------------------------
txt = lambda g: " / ".join("".join(str(v) for v in row) for row in g)
arg = " ; ".join(txt(d) + " -> " + txt(crop_mirror(gp.G(d))) for d, _ in task(crop_mirror, demos))
r = run_tool("tool induce " + arg + " ? " + txt(query))
check("tool induce answers a multi-step task", r.ok and txt(crop_mirror(gp.G(query))) in r.text)
r = run_tool("tool arc 1e0a9b12")
check("tool arc answers a stored task with a plan (gravity)", r.ok and "RIGHT" in r.text)

print("round 29: all checks pass" if not fails else "round 29: %d FAILED" % len(fails))
sys.exit(1 if fails else 0)
