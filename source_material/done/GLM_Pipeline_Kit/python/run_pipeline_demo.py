#!/usr/bin/env python3
"""Corrected pipeline demo: re-runs the study's measurements with the verified kit.

    python3 run_pipeline_demo.py            (stdlib only; writes results/demo_results.json)
"""
import json
import os
from collections import Counter

from glm_kit import analogy, golay, leech, pipeline, tasks

N = 50
FAMILIES = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]


def main():
    out = {}
    print(f"{'task':<14}{'odd/even':<10}{'4x wall':<9}{'8x in Λ24':<11}{'junctions':<11}"
          f"{'solved':<8}{'wrong':<7}rule")
    for name in FAMILIES:
        words = [tasks.grid_to_word(tasks.sample(name, s + 1)[0]) for s in range(N)]
        odd = sum(golay.popcount(w) % 2 for w in words)
        wall = sum(not leech.in_leech(leech.embed4(w)) for w in words)
        ok8 = sum(leech.in_leech(leech.embed8(w)) for w in words)
        labels = Counter(leech.junction_label(w) for w in words)
        solved = wrong = 0
        rules = Counter()
        for s in range(N):
            demos = [tasks.sample(name, 1000 * (s + 1) + k)[:2] for k in range(4)]
            q, a, _ = tasks.sample(name, 1000 * (s + 1) + 999)
            pred, rule = pipeline.solve(demos, q)
            rules[rule.split(":")[0]] += 1
            if pred is not None:
                solved += pred == a
                wrong += pred != a
        out[name] = {"odd": odd, "even": N - odd, "wall_4x": wall, "in_leech_8x": ok8,
                     "distinct_junction_labels": len(labels),
                     "junctions_with_2plus": sum(1 for c in labels.values() if c > 1),
                     "solver_correct": solved, "solver_wrong": wrong, "rules": dict(rules)}
        print(f"{name:<14}{odd}/{N-odd:<7}{wall:<9}{ok8}/{N:<8}{len(labels):<11}"
              f"{solved:<8}{wrong:<7}{dict(rules)}")
    # Iteration-8 dual snap on toggle: threshold decode (study) vs parity decode (fix)
    thr = par = 0
    for s in range(30):
        A = tasks.flatten(tasks.sample("toggle", s + 1)[0])
        C = tasks.flatten(tasks.sample("toggle", s + 100)[0])
        B = [1 - v for v in A]
        exp = [1 - v for v in C]
        thr += analogy.threshold_analogy(A, B, C) == exp
        par += analogy.parity_analogy(A, B, C) == exp
    out["toggle_dual_snap"] = {"threshold_decode_exact": thr, "parity_decode_exact": par, "n": 30}
    print(f"\nToggle analogy A:¬A::C:?  threshold decode (iteration 8): {thr}/30   "
          f"parity decode (fix): {par}/30")
    os.makedirs("results", exist_ok=True)
    with open("results/demo_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote results/demo_results.json")


if __name__ == "__main__":
    main()
