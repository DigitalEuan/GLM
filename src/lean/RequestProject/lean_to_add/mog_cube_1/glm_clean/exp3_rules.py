#!/usr/bin/env python3
"""
exp3_rules.py — MOG cells as graded semantic rules (encoding v6).

Same protocol as exp2: train on the dependency-parsed corpus, search the cells
on a held-out development split of it, and test on the WSJ (gold parses) and
Brown extractions, which the search never sees.

Reference points reported alongside:
  * the continuous class-based association model (not a 24-cell object at all);
    this is the information ceiling of the same class inventory and the same
    counts, and it tells us what the binary MOG object costs
  * the v5 class-cell encoding
  * a random choice of 24 rules
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glm_clean.semantics.encoding import Composer
from glm_clean.semantics.features import ClassInventory, Lexicon
from glm_clean.semantics.learn import (FitParams, Pairs, PseudoTask,
                                       evaluate_pseudo, fit_class_masks,
                                       model_from_masks, split_pairs)
from glm_clean.semantics.rules import (FORBID_TAUS, REQUIRE_TAUS, CellSpec,
                                       RuleEncoder, RuleSearch, VerbStats)

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)


def attested_map(*rowsets):
    d = {}
    for rows in rowsets:
        for v, n, _c in rows:
            d.setdefault(v, set()).add(n)
    return d


def noun_pool(rows, cap=5):
    pool = []
    for _v, n, c in rows:
        pool.extend([n] * min(c, cap))
    return pool


def main():
    senses = 3 if "--senses3" in sys.argv else 1
    quick = "--quick" in sys.argv
    lex = Lexicon.load()
    inv = ClassInventory.build(lex, senses=senses)
    print(f"word senses used per noun: {senses}")
    pairs = Pairs.load().filtered(lex)
    train_subj, dev_subj = split_pairs(pairs.get("dep_subj"), 0.10, seed=1)
    train_obj, dev_obj = split_pairs(pairs.get("dep_obj"), 0.10, seed=2)
    att_subj = attested_map(pairs.get("dep_subj"), pairs.get("wsj_subj"),
                            pairs.get("brown_subj"))
    att_obj = attested_map(pairs.get("dep_obj"), pairs.get("wsj_obj"),
                           pairs.get("brown_obj"))
    pool_subj = noun_pool(pairs.get("dep_subj"))
    pool_obj = noun_pool(pairs.get("dep_obj"))

    dev_tasks = [PseudoTask.build(dev_subj, "subj", pool_subj, att_subj, 11, 2500),
                 PseudoTask.build(dev_obj, "obj", pool_obj, att_obj, 12, 2500)]
    tests = [("wsj_subj", PseudoTask.build(pairs.get("wsj_subj"), "subj", pool_subj, att_subj, 21)),
             ("wsj_obj", PseudoTask.build(pairs.get("wsj_obj"), "obj", pool_obj, att_obj, 22)),
             ("brown_subj", PseudoTask.build(pairs.get("brown_subj"), "subj", pool_subj, att_subj, 23)),
             ("brown_obj", PseudoTask.build(pairs.get("brown_obj"), "obj", pool_obj, att_obj, 24))]
    print(f"classes {len(inv)}  dev {[len(t.items) for t in dev_tasks]}  "
          f"test {[len(t.items) for _n, t in tests]}")

    report = {}

    def evaluate(name, comp):
        row = {}
        for t in dev_tasks:
            r = evaluate_pseudo(comp, t)
            row[f"dev_{t.slot}"] = round(r["acc"], 4)
            row[f"dev_{t.slot}_tie"] = round(r["tie_rate"], 3)
        for nm, t in tests:
            r = evaluate_pseudo(comp, t)
            row[nm] = round(r["acc"], 4)
            row[nm + "_tie"] = round(r["tie_rate"], 3)
        row["dev_mean"] = round((row["dev_subj"] + row["dev_obj"]) / 2, 4)
        row["test_mean"] = round(sum(row[nm] for nm, _ in tests) / len(tests), 4)
        report[name] = row
        print(f"{name:32s} dev={row['dev_mean']:.4f} test={row['test_mean']:.4f}  "
              + " ".join(f"{nm}={row[nm]:.3f}" for nm, _ in tests)
              + f"  ties {row['dev_obj_tie']:.2f}")
        return row

    # ── reference: continuous class-based association (no MOG object) ────
    print("\n--- reference: continuous class model (information ceiling) ---")
    ceiling = {}
    stats = {"subj": VerbStats(inv, lex, train_subj),
             "obj": VerbStats(inv, lex, train_obj)}
    def cont(slot, verb, noun):
        st = stats[slot]
        cls = inv.of(noun)
        if not cls:
            return 0.0
        return sum(math.log(max(st.p(verb, c), 1e-9) / max(st.p0[c], 1e-9))
                   for c in cls) / len(cls)
    for tag, tks in (("dev", [(f"dev_{t.slot}", t) for t in dev_tasks]),
                     ("test", tests)):
        for nm, t in tks:
            c = 0.0
            for v, g, b in t.items:
                x, y = cont(t.slot, v, g), cont(t.slot, v, b)
                c += 1 if x > y else (0.5 if x == y else 0.0)
            ceiling[nm] = round(c / len(t.items), 4)
    ceiling["test_mean"] = round(sum(ceiling[nm] for nm, _ in tests) / len(tests), 4)
    report["REF continuous class model"] = ceiling
    print("  ", ceiling)

    # ── v5 class-cell encoding, for comparison ───────────────────────────
    print("\n--- v5: 24 cells = 24 WordNet classes ---")
    par = FitParams(theta_req=0.4, theta_forb=0.08, k1=1.0)
    cms = (fit_class_masks(inv, lex, train_subj, par),
           fit_class_masks(inv, lex, train_obj, par))
    sel_names = json.loads((RESULTS / "layout_v5.json").read_text())["classes"]
    sel = [inv.index[c] for c in sel_names if c in inv.index]
    if len(sel) < len(sel_names):
        print(f"  note: {len(sel_names) - len(sel)} of the v5 classes do not "
              f"exist in this inventory (senses={senses}); comparing on the "
              f"{len(sel)} that do")
    if sel:
        evaluate("v5 searched 24 classes",
                 Composer(lex, inv, model_from_masks(inv, sel, cms[0], cms[1])))

    # ── v6: graded rules ─────────────────────────────────────────────────
    print("\n--- v6: 24 cells = graded rules, searched ---")
    search = RuleSearch(inv, lex, [("subj", dev_tasks[0]), ("obj", dev_tasks[1])],
                        stats)
    cells, dev_score, history = search.run(k=24, sweeps=2)
    print(f"search dev score {dev_score:.4f}")
    enc = RuleEncoder(inv, cells, stats["subj"], stats["obj"])
    for i, lab in enumerate(enc.labels()):
        print(f"  cell {i:2d}  {lab}")
    evaluate("v6 searched 24 rules", Composer(lex, inv, enc))

    rnd = random.Random(3)
    rand_cells = [CellSpec(rnd.randrange(len(inv)),
                           rnd.choice(["forbid", "require"]),
                           rnd.choice(FORBID_TAUS + REQUIRE_TAUS))
                  for _ in range(24)]
    evaluate("ABLATION 24 random rules",
             Composer(lex, inv, RuleEncoder(inv, rand_cells, stats["subj"], stats["obj"])))

    if not quick:
        for k in (6, 12, 48):
            cs, _ds, _ = search.run(k=k, sweeps=1)
            evaluate(f"v6 {k} rules",
                     Composer(lex, inv, RuleEncoder(inv, cs, stats["subj"], stats["obj"])))

    tag = f"_senses{senses}" if senses != 1 else ""
    (RESULTS / f"exp3_rules{tag}.json").write_text(json.dumps(
        {"report": report, "dev_score": dev_score, "history": history,
         "cells": [{"class": inv.classes[c.cls], "direction": c.direction,
                    "tau": c.tau} for c in cells]}, indent=2))
    (RESULTS / f"encoder_v6{tag}.json").write_text(enc.to_json())
    print(f"\nwrote results/exp3_rules{tag}.json and encoder_v6{tag}.json")


if __name__ == "__main__":
    main()
