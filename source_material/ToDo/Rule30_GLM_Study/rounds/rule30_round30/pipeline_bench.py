#!/usr/bin/env python3
"""Round 30 benchmark: the GLM pipeline (plan -> fitted middle steps -> ask -> measure).

Stand-alone (no GLM checkout needed).  One search per puzzle is built and then re-read by every
stage, so all numbers below are on the same hypothesis spaces.

Sections (EMP: measured, not proved):

A. **Planning** (To Do 23).  Round 29 planner vs the Round 30 pipeline at plan depth <= 2, on the
   stored ARC tasks, the Round 28 local-rule sets and the Round 29 multi-step sets; the pipeline
   with and without the fitted middle steps; the cost of the search with and without the
   goal-shape pruning (step expansions and seconds).
B. **Asking** (To Do 24).  On every puzzle the pipeline refuses, a simulated oracle answers the
   question the refusal names (a query cell, or the output size), up to 5 questions.  Reported:
   right / wrong / still refused after 1, 2, 3, 5 questions, and the share of output cells asked.
C. **Occam** (To Do 26).  The multi-step families with k = 1..5 demonstrations; the leave-one-out
   gate off, from depth 2 (Round 29) and from depth 1.  Reported: right / wrong / refused, and
   every wrong answer with the plan that caused it.
D. **Fresh held-out set** (``r30_heldout.py``, written after the pipeline was frozen; the
   pipeline's sha256 is printed).  Sections A-C on it, scored once.

Usage::

    python3 pipeline_bench.py [ARC_DIR] [--only A,B,C,D] [--json out.json]
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning"),
          os.path.join(HERE, "..", "rule30_round29", "glm_overlay", "glm_universal", "reasoning"),
          os.path.join(HERE, "..", "rule30_round28", "glm_overlay", "glm_universal", "reasoning"),
          os.path.join(HERE, "..", "rule30_round29"), os.path.join(HERE, "..", "rule30_round28"),
          HERE):
    sys.path.insert(0, p)
import glm_pipeline as P  # noqa: E402
import grid_planner as gp  # noqa: E402
import r29_benchmark as B29  # noqa: E402

DEPTH = 2
BUDGET = 20.0
INSTANCES = 12


def tasks_families(families, seed_base, k=3, instances=INSTANCES):
    out = []
    for fi, (name, gen, rule, expr) in enumerate(families):
        for i in range(instances):
            g = B29.LCG(seed_base + 1000 * fi + i + 1)
            demos = [B29.draw(g, gen, rule) for _ in range(5)]
            query = B29.draw(g, gen, rule)
            train = [(d, B29.L(rule(d))) for d in demos[:k]]
            out.append(dict(family=name, train=train, queries=[query],
                            truth=[B29.L(rule(query))], expressible=expr,
                            pool=[(d, B29.L(rule(d))) for d in demos]))
    return out


def tasks_r28():
    r28 = B29._load_r28()
    sets = {}
    for key, fams, base in (("B1", r28.FAMILIES, 0), ("B2", r28.HELDOUT, 50000)):
        out = []
        for fi, (name, rule, cols, dens, _loc) in enumerate(fams):
            for i in range(r28.INSTANCES):
                g = r28.LCG(base + 1000 * fi + i + 1)
                demos = [r28.rand_grid(g, cols, dens) for _ in range(3)]
                query = r28.rand_grid(g, cols, dens)
                out.append(dict(family=name, train=[(d, rule(d)) for d in demos],
                                queries=[query], truth=[rule(query)], expressible=True))
        sets[key] = out
    return sets


def tasks_arc(arc_dir):
    out = []
    for f in sorted(glob.glob(os.path.join(arc_dir, "*.json"))):
        t = json.load(open(f))
        if any("output" not in p for p in t["test"]):
            continue
        out.append(dict(family=os.path.basename(f)[:-5],
                        train=[(p["input"], p["output"]) for p in t["train"]],
                        queries=[p["input"] for p in t["test"]],
                        truth=[p["output"] for p in t["test"]], expressible=None))
    return out


def verdict(res, truth):
    if res["status"] != "answered":
        return "refused"
    return "right" if [list(map(list, a)) for a in res["answer"]] == \
        [list(map(list, t)) for t in truth] else "wrong"


def tally(vs):
    return {k: sum(1 for v in vs if v == k) for k in ("right", "wrong", "refused")}


def fmt(t):
    return "RIGHT %3d  WRONG %2d  REFUSED %3d" % (t["right"], t["wrong"], t["refused"])


# ---------------------------------------------------------------------------------------------

def section_AB(name, tasks, r29=True, out=None):
    """Planning (A) and asking (B) on one task set."""
    rows = {"r29": [], "p_nomid": [], "p": [], "ask": {1: [], 2: [], 3: [], 5: []}}
    cost = {"applied": 0, "pruned": 0, "sec_prune": 0.0, "sec_noprune": 0.0,
            "applied_noprune": 0}
    asked_cells, out_cells, qcount = 0, 0, []
    fam_rows = {}
    for t in tasks:
        if r29:
            rows["r29"].append(verdict(gp.solve(t["train"], t["queries"], max_depth=DEPTH,
                                                budget_s=BUDGET), t["truth"]))
        S = P.Search(t["train"], t["queries"], DEPTH, BUDGET)
        cost["applied"] += S.stats["applied"]
        cost["pruned"] += S.stats["pruned"]
        cost["sec_prune"] += S.stats["seconds"]
        S0 = P.Search(t["train"], t["queries"], DEPTH, BUDGET, prune=False)
        cost["applied_noprune"] += S0.stats["applied"]
        cost["sec_noprune"] += S0.stats["seconds"]
        v0 = verdict(S.decide(middle=False), t["truth"])
        r = S.decide()
        v = verdict(r, t["truth"])
        # pruning loses nothing: the unpruned search gives the same decision
        r_np = S0.decide()
        assert verdict(r_np, t["truth"]) == v or S.stats["budget_hit"] or S0.stats["budget_hit"], \
            (t["family"], v, verdict(r_np, t["truth"]))
        rows["p_nomid"].append(v0)
        rows["p"].append(v)
        fam_rows.setdefault(t["family"], []).append(v)
        if v == "refused":
            a = P.ask_loop(S, t["truth"], max_questions=5)
            n = sum(len(x) * len(x[0]) for x in t["truth"])
            truth_l = [list(map(list, x)) for x in t["truth"]]
            for b in rows["ask"]:
                # within b questions: the ask-mode answer if there is one, else the plain
                # decision after the questions asked (at most b)
                ans = [e for e in a["trace"] if e[0] <= b and e[1] == "answered"]
                if ans:
                    got = ans[0][3]
                else:
                    last = [e for e in a["trace"] if e[0] <= b][-1]
                    got = last[5] if last[4] == "answered" else None
                if got is None:
                    rows["ask"][b].append("refused")
                else:
                    good = [list(map(list, x)) for x in got] == truth_l
                    rows["ask"][b].append("right" if good else "wrong")
            if a["status"] == "answered":
                qcount.append(a["questions"])
                asked_cells += a["questions"]
                out_cells += n
        else:
            for b in rows["ask"]:
                rows["ask"][b].append(v)
    print("--- %s (%d puzzles) ---" % (name, len(tasks)))
    if r29:
        print("   Round 29 planner (depth <= %d):           %s" % (DEPTH, fmt(tally(rows["r29"]))))
    print("   pipeline, no fitted middle steps:          %s" % fmt(tally(rows["p_nomid"])))
    print("   pipeline (stage 1):                        %s" % fmt(tally(rows["p"])))
    for b in (1, 2, 3, 5):
        print("   + ask loop, <= %d question(s):              %s" % (b, fmt(tally(rows["ask"][b]))))
    if qcount:
        print("   answered after asking: %d puzzles, mean %.2f questions, %d of %d output cells "
              "asked (%.1f%%)" % (len(qcount), sum(qcount) / len(qcount), asked_cells, out_cells,
                                  100.0 * asked_cells / max(out_cells, 1)))
    print("   search cost: %d step expansions with shape pruning (%d skipped) vs %d without; "
          "%.1f s vs %.1f s" % (cost["applied"], cost["pruned"], cost["applied_noprune"],
                                cost["sec_prune"], cost["sec_noprune"]))
    for fam, vs in fam_rows.items():
        if len(vs) > 1:
            print("      %-26s %s" % (fam, fmt(tally(vs))))
    if out is not None:
        out[name] = dict(rows=rows, cost=cost, questions=qcount)


def section_C(name, tasks_by_k, out=None):
    """Occam: the number of demonstrations and the leave-one-out gate."""
    print("--- %s: Occam failures by number of demonstrations ---" % name)
    res = {}
    for k, tasks in sorted(tasks_by_k.items()):
        res[k] = {}
        searches = [P.Search(t["train"], t["queries"], DEPTH, BUDGET) for t in tasks]
        for gate_name, lf in (("gate off", None), ("gate from depth 2", 2),
                              ("gate from depth 1", 1), ("auto (Round 30)", "auto")):
            vs, wrongs = [], []
            for t, S in zip(tasks, searches):
                r = S.decide(listen_from=lf)
                v = verdict(r, t["truth"])
                vs.append(v)
                if v == "wrong":
                    wrongs.append("%s: %s" % (t["family"], r.get("plan")))
            res[k][gate_name] = dict(tally=tally(vs), wrong=wrongs)
            print("   k=%d  %-18s %s" % (k, gate_name, fmt(tally(vs))))
            for w in sorted(set(wrongs))[:4]:
                print("          wrong: %s (x%d)" % (w, wrongs.count(w)))
    if out is not None:
        out[name] = res


def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1)
           if not a.startswith("--") and not sys.argv[i - 1].startswith("--")]
    arc_dir = pos[0] if pos else os.environ.get("ARC_DIR", "arc_agi_17/data/training")
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv \
        else {"A", "B", "C", "D"}
    src = os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning", "glm_pipeline.py")
    print("pipeline sha256:", hashlib.sha256(open(src, "rb").read()).hexdigest())
    print("plan depth <= %d, search budget %.0f s per puzzle" % (DEPTH, BUDGET))
    rep = {}
    t0 = time.time()
    if only & {"A", "B"}:
        print("\n=== A/B. planning and asking (development sets) ===")
        section_AB("stored ARC tasks (development)", tasks_arc(arc_dir), out=rep)
        r28 = tasks_r28()
        section_AB("Round 28 development local-rule puzzles", r28["B1"], out=rep)
        section_AB("Round 28 held-out local-rule puzzles", r28["B2"], out=rep)
        section_AB("Round 29 development multi-step puzzles",
                   tasks_families(B29.DEV29, 290000), out=rep)
        section_AB("Round 29 held-out multi-step puzzles",
                   tasks_families(B29.HELDOUT29, 291000), out=rep)
    if "C" in only:
        print("\n=== C. Occam (development families) ===")
        fams = [f for f in B29.DEV29 + B29.HELDOUT29 if f[3]]
        section_C("Round 29 multi-step families",
                  {k: tasks_families(fams, 295000, k=k, instances=6) for k in (1, 2, 3, 4, 5)},
                  out=rep)
    if "D" in only:
        import r30_heldout as H
        print("\n=== D. fresh held-out set (scored once) ===")
        print("held-out file sha256:", hashlib.sha256(
            open(os.path.join(HERE, "r30_heldout.py"), "rb").read()).hexdigest())
        section_AB("Round 30 held-out puzzles", tasks_families(H.HELDOUT30, 300000), out=rep)
        section_C("Round 30 held-out families",
                  {k: tasks_families([f for f in H.HELDOUT30 if f[3]], 305000, k=k,
                                     instances=6) for k in (1, 2, 3, 4, 5)}, out=rep)
    print("\n(%.0f s)" % (time.time() - t0))
    if "--json" in sys.argv:
        json.dump(rep, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
