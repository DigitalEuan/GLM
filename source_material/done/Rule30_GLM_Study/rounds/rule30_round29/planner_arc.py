"""Round 29: the stepwise grid planner on the 50 ARC tasks stored in the GLM archive.

Usage (from anywhere)::

    python3 planner_arc.py [ARC_DIR] [--policy ladder|strict] [--depth N] [--budget S]

Test outputs are read only to score.  Output of the default run: ``planner_arc_output.txt``.
"""
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning"))
sys.path.insert(0, os.path.join(HERE, "..", "rule30_round28", "glm_overlay", "glm_universal",
                                "reasoning"))
import grid_planner as gp  # noqa: E402


def arg(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1)
           if not a.startswith("--") and not sys.argv[i - 1].startswith("--")]
    arc_dir = pos[0] if pos else os.environ.get("ARC_DIR", "arc_agi_17/data/training")
    policy = arg("--policy", "ladder")
    depth = int(arg("--depth", "3"))
    budget = float(arg("--budget", "30"))
    files = sorted(glob.glob(os.path.join(arc_dir, "*.json")))
    tally = {"right": [], "wrong": [], "refused": []}
    t0 = time.time()
    for f in files:
        name = os.path.basename(f)[:-5]
        task = json.load(open(f))
        res = gp.solve_task(task, max_depth=depth, policy=policy, budget_s=budget)
        if res["status"] == "answered":
            right = all(a == p["output"] for a, p in zip(res["answer"], task["test"]))
            tally["right" if right else "wrong"].append(name)
            print("%s %-5s %s [%.1fs]" % (name, "RIGHT" if right else "WRONG", gp.describe(res),
                                         res["seconds"]))
        else:
            tally["refused"].append(name)
            print("%s REFUSE %s [%.1fs]" % (name, res.get("why"), res.get("seconds", 0)))
        sys.stdout.flush()
    print("\npolicy=%s depth<=%d budget=%gs: RIGHT %d  WRONG %d  REFUSED %d  (%.0fs)" % (
        policy, depth, budget, len(tally["right"]), len(tally["wrong"]), len(tally["refused"]),
        time.time() - t0))
    print("right:", tally["right"])
    print("wrong:", tally["wrong"])


if __name__ == "__main__":
    main()
