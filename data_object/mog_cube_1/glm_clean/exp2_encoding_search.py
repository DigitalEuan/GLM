#!/usr/bin/env python3
"""
exp2_encoding_search.py — searching the encoding space.

Question: which 24 WordNet classes should occupy the 24 MOG cells, and how much
selectional knowledge does a 24-cell binary object actually hold?

  train   dependency-parsed corpus (build_bigdata.py) — Wikipedia + literary
  dev     a held-out 10% split of the training pairs (used by the search and
          by the hyper-parameter sweep)
  test    WSJ / Penn Treebank sample with gold parses, plus the Brown corpus
          extraction — both from corpora the search never sees

Everything is reported, including the ablations that lose.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glm_clean.semantics.features import ClassInventory, Lexicon
from glm_clean.semantics.learn import (FitParams, ItemMatrix, Pairs, PseudoTask,
                                       evaluate_pseudo, fit_class_masks,
                                       model_from_masks, search_selection,
                                       split_pairs)
from glm_clean.semantics.encoding import Composer

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
    lex = Lexicon.load()
    inv = ClassInventory.build(lex)
    pairs = Pairs.load().filtered(lex)
    print(f"classes: {len(inv)}")
    for k, rows in sorted(pairs.rows.items()):
        print(f"  {k:12s} {len(rows):7d} types  {sum(r[2] for r in rows):8d} tokens")

    train_subj, dev_subj = split_pairs(pairs.get("dep_subj"), 0.10, seed=1)
    train_obj, dev_obj = split_pairs(pairs.get("dep_obj"), 0.10, seed=2)
    print(f"train: {len(train_subj)} subj / {len(train_obj)} obj pair types")

    att_subj = attested_map(pairs.get("dep_subj"), pairs.get("wsj_subj"),
                            pairs.get("brown_subj"))
    att_obj = attested_map(pairs.get("dep_obj"), pairs.get("wsj_obj"),
                           pairs.get("brown_obj"))
    pool_subj = noun_pool(pairs.get("dep_subj"))
    pool_obj = noun_pool(pairs.get("dep_obj"))

    dev_tasks = [PseudoTask.build(dev_subj, "subj", pool_subj, att_subj, 11),
                 PseudoTask.build(dev_obj, "obj", pool_obj, att_obj, 12)]
    test_tasks = [PseudoTask.build(pairs.get("wsj_subj"), "subj", pool_subj, att_subj, 21),
                  PseudoTask.build(pairs.get("wsj_obj"), "obj", pool_obj, att_obj, 22),
                  PseudoTask.build(pairs.get("brown_subj"), "subj", pool_subj, att_subj, 23),
                  PseudoTask.build(pairs.get("brown_obj"), "obj", pool_obj, att_obj, 24)]
    test_names = ["wsj_subj", "wsj_obj", "brown_subj", "brown_obj"]
    print(f"dev items {[len(t.items) for t in dev_tasks]}  "
          f"test items {[len(t.items) for t in test_tasks]}")

    report = {}

    def fit(par):
        return (fit_class_masks(inv, lex, train_subj, par),
                fit_class_masks(inv, lex, train_obj, par))

    def evaluate(name, sel, cms, quiet=False):
        model = model_from_masks(inv, sel, cms[0], cms[1], name)
        comp = Composer(lex, inv, model)
        row = {"k": len(sel)}
        for t in dev_tasks:
            r = evaluate_pseudo(comp, t)
            row[f"dev_{t.slot}"] = round(r["acc"], 4)
            row[f"dev_{t.slot}_tie"] = round(r["tie_rate"], 3)
        for nm, t in zip(test_names, test_tasks):
            r = evaluate_pseudo(comp, t)
            row[nm] = round(r["acc"], 4)
            row[nm + "_tie"] = round(r["tie_rate"], 3)
        row["dev_mean"] = round((row["dev_subj"] + row["dev_obj"]) / 2, 4)
        row["test_mean"] = round(sum(row[n] for n in test_names) / 4, 4)
        report[name] = row
        if not quiet:
            print(f"{name:34s} dev={row['dev_mean']:.4f} test={row['test_mean']:.4f}"
                  f"  " + " ".join(f"{n}={row[n]:.3f}" for n in test_names))
        return row

    # ── 1. hyper-parameters, chosen on dev with the full inventory ───────
    print("\n--- hyper-parameter sweep (all 171 classes as cells; dev only) ---")
    best_par, best_dev = None, -1.0
    for theta_req in (0.4, 0.6, 0.8):
        for theta_forb in (0.0, 0.02, 0.08):
            for k1 in (1.0, 4.0):
                par = FitParams(theta_req=theta_req, theta_forb=theta_forb, k1=k1)
                cms = fit(par)
                row = evaluate(f"all171 req{theta_req} forb{theta_forb} k1={k1}",
                               list(range(len(inv))), cms, quiet=True)
                print(f"  req={theta_req} forb={theta_forb} k1={k1}: "
                      f"dev={row['dev_mean']:.4f} test={row['test_mean']:.4f} "
                      f"tie={row['dev_obj_tie']:.2f}")
                if row["dev_mean"] > best_dev:
                    best_par, best_dev = par, row["dev_mean"]
    print(f"best on dev: theta_req={best_par.theta_req} "
          f"theta_forb={best_par.theta_forb} k1={best_par.k1} ({best_dev:.4f})")
    cms = fit(best_par)

    print("\n--- reference points ---")
    evaluate("REF all 171 classes (not MOG-legal)", list(range(len(inv))), cms)
    lexsel = [inv.index[c] for c in inv.classes if c.startswith("LEX:")][:24]
    evaluate("REF 24 WordNet lexnames", lexsel, cms)
    rnd = random.Random(5)
    evaluate("REF 24 random classes",
             rnd.sample(range(len(inv)), 24), cms)

    # ── 2. the search ────────────────────────────────────────────────────
    print("\n--- greedy search for the best 24 cells (dev-scored) ---")
    mats = [ItemMatrix(inv, lex, cms[0 if t.slot == "subj" else 1], t)
            for t in dev_tasks]
    sel, dev_score, history = search_selection(inv, mats, k=24, swaps=2)
    print(f"search dev score {dev_score:.4f}")
    print("cells:")
    for i, c in enumerate(sel):
        print(f"  {i:2d}  {inv.classes[c]}")
    evaluate("SEARCHED 24 cells", sel, cms)

    # smaller budgets, for the record
    for k in (6, 12, 48):
        s2, d2, _ = search_selection(inv, mats, k=k, swaps=1, verbose=False)
        evaluate(f"SEARCHED {k} cells", s2, cms)

    (RESULTS / "exp2_encoding_search.json").write_text(json.dumps(
        {"report": report,
         "params": vars(best_par),
         "selection": [inv.classes[c] for c in sel],
         "dev_score": dev_score,
         "history": history}, indent=2))
    (RESULTS / "layout_v5.json").write_text(json.dumps({
        "classes": [inv.classes[c] for c in sel],
        "params": vars(best_par)}, indent=2))
    print(f"\nwrote {RESULTS/'exp2_encoding_search.json'} and layout_v5.json")


if __name__ == "__main__":
    main()
