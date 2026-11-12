#!/usr/bin/env python3
"""
exp1_selection.py — does the MOG encoding carry real selectional information?

Task: pseudo-disambiguation (Rooth-style).  Given a verb and two nouns, one of
which really was observed in that slot in a corpus and one of which was drawn
from the slot's noun distribution, does the GLM prefer the real one (strictly
fewer violated MOG cells)?  Ties count 0.5, so a model with no opinion scores
exactly 0.500.

Training counts: the Brown corpus (balanced, POS-tagged, shallow chunking).
Test items: the WSJ / Penn Treebank sample with gold parses.  Different corpus,
different genre, gold syntax — nothing about the test items is in training.

Ablations are printed whether they help or hurt.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glm_clean.semantics.encoding import SCHEMA_MOG, SCHEMA_WIDE, Composer, Layout
from glm_clean.semantics.features import ClassInventory, Lexicon
from glm_clean.semantics.learn import (LEXNAME_GROUPS_6, LEXNAME_GROUPS_9,
                                       FitParams, Pairs, PseudoTask,
                                       evaluate_pseudo, fit_model, seed_layout,
                                       split_pairs)

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)


def attested_map(rows):
    d = {}
    for v, n, _c in rows:
        d.setdefault(v, set()).add(n)
    return d


def noun_pool(rows):
    pool = []
    for _v, n, c in rows:
        pool.extend([n] * min(c, 5))
    return pool


def build_everything():
    lex = Lexicon.load()
    inv = ClassInventory.build(lex)
    pairs = Pairs.load().filtered(lex)
    train_subj, dev_subj = split_pairs(pairs.brown_subj, 0.15, seed=1)
    train_obj, dev_obj = split_pairs(pairs.brown_obj, 0.15, seed=2)
    att_subj = attested_map(pairs.brown_subj + pairs.wsj_subj)
    att_obj = attested_map(pairs.brown_obj + pairs.wsj_obj)
    dev_tasks = [
        PseudoTask.build(dev_subj, "subj", noun_pool(pairs.brown_subj), att_subj, 11),
        PseudoTask.build(dev_obj, "obj", noun_pool(pairs.brown_obj), att_obj, 12),
    ]
    test_tasks = [
        PseudoTask.build(pairs.wsj_subj, "subj", noun_pool(pairs.brown_subj), att_subj, 21),
        PseudoTask.build(pairs.wsj_obj, "obj", noun_pool(pairs.brown_obj), att_obj, 22),
    ]
    return lex, inv, pairs, train_subj, train_obj, dev_tasks, test_tasks


def main():
    lex, inv, pairs, train_subj, train_obj, dev_tasks, test_tasks = build_everything()
    print(f"classes: {len(inv)}")
    print(f"pair types: brown_subj={len(pairs.brown_subj)} brown_obj={len(pairs.brown_obj)} "
          f"wsj_subj={len(pairs.wsj_subj)} wsj_obj={len(pairs.wsj_obj)}")
    print(f"dev items: {[len(t.items) for t in dev_tasks]}  "
          f"test items: {[len(t.items) for t in test_tasks]}")
    report = {}

    def run(name, layout, par=FitParams(), inv_=None, quiet=False):
        iv = inv_ or inv
        model = fit_model(layout, iv, lex, train_subj, train_obj, par)
        comp = Composer(lex, iv, model)
        row = {}
        for tag, tasks in (("dev", dev_tasks), ("test", test_tasks)):
            for t in tasks:
                r = evaluate_pseudo(comp, t)
                row[f"{tag}_{t.slot}"] = round(r["acc"], 4)
                row[f"{tag}_{t.slot}_tie"] = round(r["tie_rate"], 3)
        row["dev_mean"] = round((row["dev_subj"] + row["dev_obj"]) / 2, 4)
        row["test_mean"] = round((row["test_subj"] + row["test_obj"]) / 2, 4)
        report[name] = row
        if not quiet:
            print(f"{name:38s} dev={row['dev_mean']:.4f} test={row['test_mean']:.4f}"
                  f"  (subj {row['test_subj']:.4f} / obj {row['test_obj']:.4f}"
                  f"  ties {row['test_subj_tie']:.2f}/{row['test_obj_tie']:.2f})")
        return row

    print("\n--- hyper-parameter sweep on DEV (test shown for information only) ---")
    base6 = seed_layout(inv, LEXNAME_GROUPS_6)
    best = (None, -1)
    for theta_req in (0.5, 0.7, 0.8, 0.9, 0.95):
        for theta_forb in (0.0, 0.01, 0.05, 0.1):
            par = FitParams(theta_req=theta_req, theta_forb=theta_forb)
            row = run(f"m=6 req>={theta_req} forb<={theta_forb}", base6, par)
            if row["dev_mean"] > best[1]:
                best = (par, row["dev_mean"])
    par = best[0]
    print(f"\nbest on dev: theta_req={par.theta_req} theta_forb={par.theta_forb} "
          f"dev={best[1]:.4f}")

    print("\n--- smoothing sweep ---")
    for k1 in (0.0, 1.0, 4.0, 16.0):
        p = FitParams(par.theta_req, par.theta_forb, par.base_min, k1, par.k2)
        run(f"k1={k1}", base6, p)

    print("\n--- cell budget ---")
    base9 = seed_layout(inv, LEXNAME_GROUPS_9, "lexname-seeded-9")
    run("m=9 (schema 9/9/6)", base9, par)

    print("\n--- ablations ---")
    rnd = random.Random(7)
    run("ABLATION random layout m=6",
        Layout(6, [rnd.randrange(6) for _ in inv.classes], "random"), par)
    inv_lex = ClassInventory.build(lex, use_ancestors=False)
    run("ABLATION lexnames only (no ancestors)",
        seed_layout(inv_lex, LEXNAME_GROUPS_6), par, inv_=inv_lex)

    (RESULTS / "exp1_selection.json").write_text(json.dumps(report, indent=2))
    print(f"\nwrote {RESULTS/'exp1_selection.json'}")


if __name__ == "__main__":
    main()
