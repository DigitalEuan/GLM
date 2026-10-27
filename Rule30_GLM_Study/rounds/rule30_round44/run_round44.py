"""Round 44 runner: does giving the GLM what it says it needs help, measurably?

Runs three experiments and writes `out/round44_results.json` and `out/round44_results.md`:

1. Rule 30 (`needs_rule30.py`): the 40 statements of the owner's `glm_wheel.json` plus held-out
   ones. The engine states its needs; provisions (exact recomputation, the Lean ledger, checked
   implications) are put on the wheel; we score right / wrong / overclaim / abstain against a
   ground truth fixed in advance.
2. Synthetic ARC (`needs_arc.py`): development puzzles produce needs; the requested provisions are
   scored on held-out puzzle families against random provisions of the same size.
3. Real ARC (optional): the 50 ARC training tasks shipped in `../glm_repo.zip`
   (`overlay/arc_agi_17/data/training`), on-demand needs, with provision sets V1 and V2.

Usage:  python3 run_round44.py [--no-real-arc]
Pure Python 3 standard library. Takes a few minutes.
"""
import json
import os
import sys
import time
import zipfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import glm_needs  # noqa: E402
import needs_rule30 as R  # noqa: E402
import needs_arc as A  # noqa: E402


def rule30():
    tids, truth = R.tasks_and_truth()
    out = glm_needs.run_conditions(tids, truth, R.base_answer, R.guard, R.needs_of,
                                   R.make_wheel(), ctx={})
    table = {k: v["score"] for k, v in out["conditions"].items() if "score" in v}
    table["random same-size + guard"] = [d["score"] for d in
                                         out["conditions"]["random same-size + guard"]["draws"]]
    # Leave-one-out ablation. The Rule 30 wheel has 7 provisions and all 7 are requested, so the
    # random same-size control coincides with the requested set; removing one provision at a time
    # shows what each one contributes.
    wheel = R.make_wheel()
    needs = {t: R.needs_of(t, {}) for t in tids}
    ablation = {}
    for p in wheel.provisions:
        provs = [q for q in wheel.provisions if q is not p]
        ans = {}
        for t in tids:
            v, w = glm_needs.answer(provs, R.base_answer, t, {})
            if w == "base":
                v = R.guard(t, {}, v, list(needs[t]))
            ans[t] = v
        ablation["without " + p.pid] = glm_needs.score(ans, truth)
    return {"tasks": len(tids), "scores": table, "requested": out["requested"],
            "unmet_needs": out["unmet_needs"], "ablation": ablation, "full": out}


def load_real_arc(zip_path):
    tasks = []
    prefix = "glm_repo/overlay/arc_agi_17/data/training/"
    with zipfile.ZipFile(zip_path) as z:
        for name in sorted(z.namelist()):
            if name.startswith(prefix) and name.endswith(".json"):
                d = json.loads(z.read(name))
                demos = [(A.G(p["input"]), A.G(p["output"])) for p in d["train"]]
                for k, t in enumerate(d["test"]):
                    if "output" in t:
                        tasks.append({"family": os.path.basename(name)[:-5] + f"#{k}",
                                      "demos": demos, "test_in": A.G(t["input"]),
                                      "test_out": A.G(t["output"])})
    return tasks


def real_arc(zip_path):
    puzzles = load_real_arc(zip_path)
    res = {"tests": len(puzzles)}
    for label, table in [("V1", A.PROVISION_STEPS), ("V2", A.PROVISION_STEPS_V2)]:
        counts = {"right": 0, "wrong": 0, "refused": 0}
        needs = Counter()
        for p in puzzles:
            ans, _ = A.solve(p["demos"], p["test_in"], A.BASE_STEPS)
            if ans is None:
                ns = A.diagnose(p["demos"], A.BASE_STEPS)
                needs.update(n.signature for n in ns)
                sigs = {n.signature for n in ns}
                names = [nm for nm, (_, serves) in table.items() if any(s in sigs for s in serves)]
                if names:
                    ans, _ = A.solve(p["demos"], p["test_in"],
                                     A.BASE_STEPS + [table[n][0] for n in names])
            k = "refused" if ans is None else ("right" if ans == p["test_out"] else "wrong")
            counts[k] += 1
        res[label] = {"on-demand": counts, "stated_needs": dict(needs.most_common())}
    base = Counter()
    for p in puzzles:
        ans, _ = A.solve(p["demos"], p["test_in"], A.BASE_STEPS)
        base["refused" if ans is None else ("right" if ans == p["test_out"] else "wrong")] += 1
    res["base"] = dict(base)
    return res


def md(results):
    L = ["# Round 44 results: the needs wheel", ""]
    r = results["rule30"]
    L += ["## Rule 30 (" + str(r["tasks"]) + " statements)", "",
          "| condition | right | wrong | overclaim | abstain |", "|---|---|---|---|---|"]
    for k, s in r["scores"].items():
        if isinstance(s, list):
            for i, d in enumerate(s):
                L.append(f"| {k} #{i + 1} | {d['right']} | {d['wrong']} | {d['overclaim']} | {d['abstain']} |")
        else:
            L.append(f"| {k} | {s['right']} | {s['wrong']} | {s['overclaim']} | {s['abstain']} |")
    L += ["", "Leave-one-out (all other provisions + guard):", "",
          "| removed | right | wrong | overclaim | abstain |", "|---|---|---|---|---|"]
    for k, s in r["ablation"].items():
        L.append(f"| {k} | {s['right']} | {s['wrong']} | {s['overclaim']} | {s['abstain']} |")
    L += ["", "Requested provisions: " + ", ".join(r["requested"]),
          "", "Needs no provision could meet: " + (", ".join(r["unmet_needs"]) or "none"), ""]
    a = results["arc_synthetic"]
    L += ["## Synthetic ARC", "", f"development {a['dev_size']} puzzles, held-out {a['heldout_size']}"
          " (held-out families are different from the development families)", "",
          "| condition | right | wrong | refused |", "|---|---|---|---|"]
    for k, v in a["conditions"].items():
        if k == "random same-size":
            for i, d in enumerate(v):
                s = d["score"]
                L.append(f"| random same-size #{i + 1} | {s['right']} | {s['wrong']} | {s['refused']} |")
        else:
            s = v[0] if isinstance(v, (list, tuple)) else v
            L.append(f"| {k} | {s['right']} | {s['wrong']} | {s['refused']} |")
    L += ["", "Requested from development needs: " + ", ".join(a["requested"]),
          "", "Diagnosis on held-out refusals: " + json.dumps(a["diagnosis"]), ""]
    if "arc_real" in results:
        q = results["arc_real"]
        L += ["## Real ARC (tasks shipped in glm_repo.zip)", "", f"{q['tests']} test grids", "",
              f"* base: {q['base']}", f"* on-demand, provisions V1: {q['V1']['on-demand']}",
              f"* on-demand, provisions V2 (+ recolour_by_feature): {q['V2']['on-demand']}",
              f"* stated needs: {q['V1']['stated_needs']}", ""]
    return "\n".join(L)


def main():
    t0 = time.time()
    results = {"rule30": rule30()}
    a = A.run()
    a.pop("dev_need_log", None)
    results["arc_synthetic"] = a
    zp = os.path.join(HERE, "..", "glm_repo.zip")
    if "--no-real-arc" not in sys.argv and os.path.exists(zp):
        results["arc_real"] = real_arc(zp)
    results["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    glm_needs.dump(os.path.join(HERE, "out", "round44_results.json"), results)
    with open(os.path.join(HERE, "out", "round44_results.md"), "w") as f:
        f.write(md(results))
    print(md(results))
    print("seconds", results["seconds"])


if __name__ == "__main__":
    main()
