#!/usr/bin/env python3
"""
exp4_perverb.py — encoding v7: the 24 MOG cells are chosen per verb.

v5 and v6 spend the 24-cell budget once for the whole language.  That is a bad
bargain: a rule that matters for `eat` is dead weight for `sign`.  v7 spends the
same 24 cells per (verb, slot), on the classes where that verb's own argument
distribution departs most from the corpus-wide one.  The object is still 24
binary cells and still exactly diagnosable at weight <= 3.

Measured against the same held-out tasks as exp3, plus the continuous class
model, which is the information ceiling of the same counts.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glm_clean.semantics.encoding import Composer
from glm_clean.semantics.features import ClassInventory, Lexicon
from glm_clean.semantics.learn import (Pairs, PseudoTask, evaluate_pseudo,
                                       split_pairs)
from glm_clean.semantics.rules import PerVerbRuleEncoder, RuleEncoder, VerbStats, CellSpec

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


def build(senses: int = 3):
    lex = Lexicon.load()
    inv = ClassInventory.build(lex, senses=senses)
    pairs = Pairs.load().filtered(lex)
    train_subj, dev_subj = split_pairs(pairs.get("dep_subj"), 0.10, seed=1)
    train_obj, dev_obj = split_pairs(pairs.get("dep_obj"), 0.10, seed=2)
    stats = {"subj": VerbStats(inv, lex, train_subj),
             "obj": VerbStats(inv, lex, train_obj)}
    att_subj = attested_map(pairs.get("dep_subj"), pairs.get("wsj_subj"),
                            pairs.get("brown_subj"))
    att_obj = attested_map(pairs.get("dep_obj"), pairs.get("wsj_obj"),
                           pairs.get("brown_obj"))
    pools = {"subj": noun_pool(pairs.get("dep_subj")),
             "obj": noun_pool(pairs.get("dep_obj"))}
    att = {"subj": att_subj, "obj": att_obj}
    dev_tasks = [PseudoTask.build(dev_subj, "subj", pools["subj"], att_subj, 11, 2500),
                 PseudoTask.build(dev_obj, "obj", pools["obj"], att_obj, 12, 2500)]
    tests = [("wsj_subj", PseudoTask.build(pairs.get("wsj_subj"), "subj", pools["subj"], att_subj, 21)),
             ("wsj_obj", PseudoTask.build(pairs.get("wsj_obj"), "obj", pools["obj"], att_obj, 22)),
             ("brown_subj", PseudoTask.build(pairs.get("brown_subj"), "subj", pools["subj"], att_subj, 23)),
             ("brown_obj", PseudoTask.build(pairs.get("brown_obj"), "obj", pools["obj"], att_obj, 24))]
    return dict(lex=lex, inv=inv, pairs=pairs, stats=stats, pools=pools,
                att=att, dev_tasks=dev_tasks, tests=tests)


def main():
    senses = 1 if "--senses1" in sys.argv else 3
    ctx = build(senses)
    lex, inv, stats = ctx["lex"], ctx["inv"], ctx["stats"]
    dev_tasks, tests = ctx["dev_tasks"], ctx["tests"]
    print(f"classes {len(inv)}  senses {senses}  "
          f"test sizes {[len(t.items) for _n, t in tests]}")
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
        row["test_mean"] = round(sum(row[nm] for nm, _ in tests) / len(tests), 4)
        row["tie_mean"] = round(sum(row[nm + "_tie"] for nm, _ in tests) / len(tests), 3)
        report[name] = row
        print(f"{name:34s} test={row['test_mean']:.4f}  "
              + " ".join(f"{nm}={row[nm]:.3f}" for nm, _ in tests)
              + f"  ties={row['tie_mean']:.2f}")
        return row

    # reference: continuous class model
    def cont(slot, verb, noun):
        st = stats[slot]
        cls = inv.of(noun)
        if not cls:
            return 0.0
        return sum(math.log(max(st.p(verb, c), 1e-9) / max(st.p0[c], 1e-9))
                   for c in cls) / len(cls)
    ceiling = {}
    for nm, t in tests:
        c = 0.0
        for v, g, b in t.items:
            x, y = cont(t.slot, v, g), cont(t.slot, v, b)
            c += 1 if x > y else (0.5 if x == y else 0.0)
        ceiling[nm] = round(c / len(t.items), 4)
    ceiling["test_mean"] = round(sum(ceiling[nm] for nm, _ in tests) / len(tests), 4)
    report["REF continuous class model"] = ceiling
    print(f"{'REF continuous class model':34s} test={ceiling['test_mean']:.4f}  "
          + " ".join(f"{nm}={ceiling[nm]:.3f}" for nm, _ in tests))

    # v6, reloaded from disk
    tag = f"_senses{senses}" if senses != 1 else ""
    p6 = RESULTS / f"encoder_v6{tag}.json"
    if p6.exists():
        spec = json.loads(p6.read_text())["cells"]
        cells = [CellSpec(inv.index[c["class"]], c["direction"], c["tau"])
                 for c in spec if c["class"] in inv.index]
        evaluate("v6 global 24 rules",
                 Composer(lex, inv, RuleEncoder(inv, cells, stats["subj"], stats["obj"])))

    # v7, per-verb cells, at several budgets
    for m in (6, 12, 24, 48):
        enc = PerVerbRuleEncoder(inv, stats["subj"], stats["obj"], m=m)
        evaluate(f"v7 per-verb {m} cells", Composer(lex, inv, enc))

    # ablation: 24 per-verb cells drawn at random rather than by divergence
    rnd = random.Random(7)
    class RandomPerVerb(PerVerbRuleEncoder):
        def cells_for(self, verb, slot):
            key = (verb, slot)
            cs = self._cells.get(key)
            if cs is None:
                allc = super().cells_for(verb, slot)
                del self._cells[key]
                # same directions, but on 24 classes chosen at random
                from glm_clean.semantics.rules import VerbCell
                st = self.stats[slot]
                pick = rnd.sample(range(len(self.inv)), self.m)
                cs = [VerbCell(c, "forbid" if st.p(verb, c) < st.p0[c] else "require")
                      for c in pick]
                self._cells[key] = cs
            return cs
    evaluate("ABLATION 24 random per-verb",
             Composer(lex, inv, RandomPerVerb(inv, stats["subj"], stats["obj"], m=24)))

    (RESULTS / f"exp4_perverb{tag}.json").write_text(json.dumps(report, indent=2))
    print(f"\nwrote results/exp4_perverb{tag}.json")


if __name__ == "__main__":
    main()
