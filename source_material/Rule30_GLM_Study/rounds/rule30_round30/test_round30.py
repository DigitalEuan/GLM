#!/usr/bin/env python3
"""Round 30 checks (run from the directory holding GLM.py, PYTHONPATH=.).

1. stage 1: a scale factor read from the grid (number of objects) is fitted and applied; a
   recolouring followed by a symmetry is answered; goal-shape pruning skips expansions and gives
   the same decision as the unpruned search (``shapePrune_skip``);
2. stage 2: a puzzle refused for an unseen colour is answered after one question, and the asked
   cell determines every cell with the same key (``askLoop_correct``);
3. stage 3: with two demonstrations the leave-one-out gate starts at plan depth 1;
4. stage 4: the statement planner's fitted offset for ``HalfLineLinear 2 2 _`` at ``d <= 12`` is 9
   (certified sharp in Lean, ``PipelineData.sharp_2_2_9``);
5. the toolbox: ``tool pipeline`` and ``tool pipeline frontier`` answer; ``tool induce`` answers a
   scale-by-objects puzzle that the Round 29 planner refuses.
"""
import sys

from glm_universal.reasoning import glm_pipeline as P
from glm_universal.reasoning import grid_planner as gp
from glm_universal.reasoning import statement_planner as SP
from glm_universal.runtime.toolbox import run_tool

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


L = lambda g: [list(r) for r in g]


def scale_by_objects(g):
    k = len(gp.components(gp.G(g), 0, diag=True))
    return L(gp.s_upscale(k)(gp.G(g)))


# 1. stage 1 -----------------------------------------------------------------------------------
demos = [[[1, 0, 0], [0, 0, 1]], [[1, 0, 1], [0, 0, 0], [1, 0, 0]], [[1, 0, 1], [0, 0, 0]]]
query = [[1, 0, 1], [0, 0, 0], [0, 1, 0]]
train = [(d, scale_by_objects(d)) for d in demos]
r = P.solve(train, [query])
check("scale factor read from the grid (number of objects)",
      r["status"] == "answered" and r["answer"][0] == scale_by_objects(query)
      and "scale-fit" in r["plan"])
r29 = gp.solve(train, [query], max_depth=2)
check("... which the Round 29 planner refuses", r29["status"] == "refused")

rec_t = lambda g: L(gp.transpose(gp.G([[{1: 4, 2: 6}.get(v, v) for v in row] for row in g])))
d2 = [[[1, 2, 0], [0, 1, 2]], [[2, 2], [1, 0], [0, 0]], [[0, 1, 1], [2, 0, 0], [1, 1, 2]]]
q2 = [[2, 1], [0, 2], [1, 0]]
r = P.solve([(d, rec_t(d)) for d in d2], [q2])
check("recolour, then transpose", r["status"] == "answered" and r["answer"][0] == rec_t(q2))

S1 = P.Search(train, [query], 2)
S0 = P.Search(train, [query], 2, prune=False)
check("goal-shape pruning skips expansions", S1.stats["pruned"] > 0 and
      S1.stats["applied"] < S0.stats["applied"])
check("... and gives the same decision", S1.decide().get("answer") == S0.decide().get("answer"))

# 2. stage 2 -----------------------------------------------------------------------------------
cm = lambda g: [[{1: 2, 4: 5, 3: 7}.get(v, v) for v in row] for row in g]
d3 = [[[1, 0], [0, 4]], [[0, 1, 4], [1, 0, 0]], [[4, 1], [0, 0]]]
q3 = [[3, 1, 0], [0, 3, 4]]
S = P.Search([(d, cm(d)) for d in d3], [q3], 1)
r0 = S.decide()
a = P.ask_loop(S, [cm(q3)], max_questions=3)
check("unseen colour: refused without a question", r0["status"] == "refused")
check("... answered rightly after one question", a["status"] == "answered" and
      a["answer"][0] == cm(q3) and a["questions"] == 1)

# 3. stage 3 -----------------------------------------------------------------------------------
S2 = P.Search([(d, cm(d)) for d in d3[:2]], [d3[2]], 1)
check("two demonstrations: the gate starts at depth 1",
      S2.hypotheses(1, "auto") == S2.hypotheses(1, 1))

# 4. stage 4 -----------------------------------------------------------------------------------
pd = SP.PeriodData(2, 12)
check("statement planner: HalfLineLinear 2 2 _ fitted offset 9 at d <= 12",
      pd.fit_lin(2, 12)[0] == 9)

# 5. toolbox -----------------------------------------------------------------------------------
r = run_tool("tool pipeline")
check("tool pipeline", r.ok and "stage 4" in r.text)
r = run_tool("tool pipeline frontier")
check("tool pipeline frontier (30 certified statements)", r.ok and r.text.count("refuted") == 30)
txt = lambda g: " / ".join("".join(str(v) for v in row) for row in g)
arg = " ; ".join(txt(d) + " -> " + txt(o) for d, o in train)
r = run_tool("tool induce " + arg + " ? " + txt(query))
check("tool induce answers a scale-by-objects puzzle", r.ok and txt(scale_by_objects(query)) in r.text)

print("round 30: all checks pass" if not fails else "round 30: %d FAILED" % len(fails))
sys.exit(1 if fails else 0)
