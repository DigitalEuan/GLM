#!/usr/bin/env python3
"""
exp5_generate.py — does the GLM actually say anything sensible?

Four measurements, all on material the encoder never fitted, and all reported
whatever they come out as.

 1  LICENSING RATE.  For a sample of verbs, what fraction of the noun
    vocabulary gets an empty violation object (TAX = 0) in each slot?  If that
    fraction is near 1 then "licensed" means nothing and the generator is only
    a random word picker with extra steps.  This is the number that decides
    whether the rest of the experiment is worth anything.

 2  SENTENCE-LEVEL DISCRIMINATION.  Gold WSJ (subject, verb, object) triples
    against corrupted copies of themselves (one argument replaced by a noun the
    verb is never attested with).  Decision by total TAX of the sentence.

 3  GENERATION + AN INDEPENDENT JUDGE.  The GLM generates one sentence per
    verb by sampling uniformly from the licensed nouns in each slot -- no
    ranking, no cherry-picking, first sample kept.  GPT-2 (which knows nothing
    about this project) scores every sentence; we compare against (a) the same
    surface realiser fed uniformly random nouns and (b) the same realiser fed
    real corpus triples.  GPT-2 is not truth, but it is not ours either.

 4  ATTESTATION.  How often is a generated (verb, object) pair actually
    attested?  Reported twice: against the whole corpus (the encoder saw those
    counts -- this measures recall of what it learned) and against the 10%
    held-out split alone (it did not).

Everything it produces is written to results/generated_sentences.txt.
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glm_clean.semantics.encoding import Composer
from glm_clean.semantics.features import ClassInventory, Lexicon
from glm_clean.semantics.generate import Speaker, realise, repair
from glm_clean.semantics.learn import Pairs, split_pairs
from glm_clean.semantics.rules import PerVerbRuleEncoder, VerbStats
from glm_clean.substrate import popcount

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)

N_NOUNS = 2000
N_VERBS = 150
N_SENTENCES = 60


def topn(rows, n, key=1):
    c = Counter()
    for r in rows:
        c[r[key]] += r[2]
    return [w for w, _ in c.most_common(n)]


class Judge:
    """GPT-2 log-probability per token.  An outside opinion, not ours."""

    def __init__(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained("gpt2")
        self.model = AutoModelForCausalLM.from_pretrained("gpt2")
        self.model.eval()

    def score(self, text: str) -> float:
        t = self.torch
        ids = self.tok(text, return_tensors="pt").input_ids
        with t.no_grad():
            out = self.model(ids, labels=ids)
        return -float(out.loss)


def main():
    rnd = random.Random(0)
    lex = Lexicon.load()
    inv = ClassInventory.build(lex, senses=3)
    pairs = Pairs.load().filtered(lex)
    train_subj, dev_subj = split_pairs(pairs.get("dep_subj"), 0.10, seed=1)
    train_obj, dev_obj = split_pairs(pairs.get("dep_obj"), 0.10, seed=2)
    stats = {"subj": VerbStats(inv, lex, train_subj),
             "obj": VerbStats(inv, lex, train_obj)}
    enc = PerVerbRuleEncoder(inv, stats["subj"], stats["obj"], m=24)
    comp = Composer(lex, inv, enc)

    nouns = topn(pairs.get("dep_subj") + pairs.get("dep_obj"), N_NOUNS)
    verbs = topn(pairs.get("dep_obj"), N_VERBS, key=0)
    verbs = [v for v in verbs if stats["obj"].evidence(v) >= 50
             and stats["subj"].evidence(v) >= 50]
    speaker = Speaker(comp, lex, nouns, verbs)
    print(f"vocabulary {len(nouns)} nouns, {len(verbs)} verbs")

    report = {}
    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)

    # ── 1  licensing rate ────────────────────────────────────────────────
    say("=" * 78)
    say("1  LICENSING RATE  (fraction of the noun vocabulary with TAX = 0)")
    say("=" * 78)
    weights = {}
    for v in verbs:
        for slot in ("subj", "obj"):
            weights[(v, slot)] = [popcount(comp.slot_violation(v, slot, n))
                                  for n in nouns]
    for slot in ("subj", "obj"):
        for thr in (0, 3):
            r = sorted(sum(1 for w in weights[(v, slot)] if w <= thr) / len(nouns)
                       for v in verbs)
            report[f"licensing_{slot}_le{thr}_mean"] = round(sum(r) / len(r), 5)
            report[f"licensing_{slot}_le{thr}_median"] = round(r[len(r) // 2], 5)
            report[f"licensing_{slot}_le{thr}_max"] = round(r[-1], 5)
            say(f"  {slot} HW<={thr}: mean {sum(r)/len(r):.4f}  "
                f"median {r[len(r)//2]:.4f}  max {r[-1]:.4f}")
        mins = sorted(min(weights[(v, slot)]) for v in verbs)
        report[f"min_weight_{slot}_median"] = mins[len(mins) // 2]
        say(f"  {slot}: median over verbs of the best achievable HW = "
            f"{mins[len(mins)//2]}  (range {mins[0]}..{mins[-1]})")
    say("")

    # ── 2  sentence-level discrimination on gold WSJ triples ─────────────
    say("=" * 78)
    say("2  SENTENCE DISCRIMINATION  (gold WSJ triples vs corrupted copies)")
    say("=" * 78)
    triples = [t for t in json.loads((Path(__file__).resolve().parent /
                                      "data" / "wsj_triples.json").read_text())
               if t[0] in lex.nouns and t[1] in lex.verbs and t[2] in lex.nouns]
    att = {}
    for src in ("dep_subj", "dep_obj", "wsj_subj", "wsj_obj",
                "brown_subj", "brown_obj"):
        for v, n, _c in pairs.get(src):
            att.setdefault((v, "subj" if src.endswith("subj") else "obj"),
                           set()).add(n)
    pool = nouns
    for corrupt in ("obj", "subj", "both"):
        ok = ties = 0
        for s, v, o, _c in triples:
            ss, oo = s, o
            if corrupt in ("subj", "both"):
                for _ in range(20):
                    x = rnd.choice(pool)
                    if x != s and x not in att.get((v, "subj"), ()):
                        ss = x
                        break
            if corrupt in ("obj", "both"):
                for _ in range(20):
                    x = rnd.choice(pool)
                    if x != o and x not in att.get((v, "obj"), ()):
                        oo = x
                        break
            wg = comp.compose(s, v, o).weight
            wb = comp.compose(ss, v, oo).weight
            if wg < wb:
                ok += 1
            elif wg == wb:
                ok += 0.5
                ties += 1
        n = len(triples)
        report[f"triples_{corrupt}"] = round(ok / n, 4)
        report[f"triples_{corrupt}_tie"] = round(ties / n, 3)
        say(f"  corrupt {corrupt:5s}: accuracy {ok/n:.4f}  ties {ties/n:.3f}  "
            f"(n={n})")
    say("")

    # ── 3  generation ────────────────────────────────────────────────────
    say("=" * 78)
    say("3  GENERATION  (uniform sample of the least-TAX nouns, nothing reranked)")
    say("=" * 78)
    # An empty violation object is almost unreachable (section 1), so the
    # generator does the next thing down: it says the words of least TAX.
    # Among the nouns that tie at the minimum it samples uniformly; nothing is
    # reranked afterwards and the first sample is kept.
    def least_tax(v, slot):
        ws = weights[(v, slot)]
        lo = min(ws)
        return [n for n, w in zip(nouns, ws) if w == lo], lo

    freq = Counter()
    for _v, n, c in pairs.get("dep_subj") + pairs.get("dep_obj"):
        if n in set(nouns):
            freq[n] += c
    freq_nouns = [n for n in nouns for _ in range(max(1, freq[n] // 200))]

    gen, base, freqbase = [], [], []
    vs = list(verbs)
    rnd.shuffle(vs)
    for v in vs:
        subs, _ls = least_tax(v, "subj")
        objs, _lo = least_tax(v, "obj")
        s, o = rnd.choice(subs), rnd.choice(objs)
        if s == o:
            continue
        gen.append((s, v, o))
        base.append((rnd.choice(nouns), v, rnd.choice(nouns)))
        freqbase.append((rnd.choice(freq_nouns), v, rnd.choice(freq_nouns)))
        if len(gen) >= N_SENTENCES:
            break
    rnd.shuffle(triples)
    real = [(s, v, o) for s, v, o, _c in triples[:N_SENTENCES]]
    say(f"  generated {len(gen)} sentences, one per verb")
    for tag, group in (("generated", gen), ("frequency baseline", freqbase)):
        say(f"  distinct subjects/objects among {len(group)} {tag} sentences: "
            f"{len({t[0] for t in group})}/{len({t[2] for t in group})}")

    def text(t):
        return realise(lex, t[0], t[1], t[2])

    judge = Judge()
    scores = {}
    for name, group in (("GLM generated", gen), ("random nouns", base),
                        ("frequency baseline", freqbase),
                        ("real WSJ triples", real)):
        xs = [judge.score(text(t)) for t in group]
        scores[name] = round(sum(xs) / len(xs), 4)
        say(f"  GPT-2 mean log-prob/token, {name:18s}: {scores[name]:.4f}")
    report["gpt2"] = scores

    # attestation
    def attested(t, sets):
        return t[2] in sets.get((t[1], "obj"), ())
    heldout = {}
    for v, n, _c in dev_obj:
        heldout.setdefault((v, "obj"), set()).add(n)
    for name, group in (("GLM generated", gen), ("random nouns", base),
                        ("frequency baseline", freqbase)):
        a_all = sum(attested(t, att) for t in group) / len(group)
        a_held = sum(attested(t, heldout) for t in group) / len(group)
        report[f"attested_all_{name}"] = round(a_all, 4)
        report[f"attested_heldout_{name}"] = round(a_held, 4)
        say(f"  (verb,object) attested, {name:14s}: whole corpus {a_all:.3f}   "
            f"held-out 10% only {a_held:.3f}")
    say("")
    say("  --- every generated sentence, in the order produced ---")
    for t in gen:
        u = comp.compose(*t)
        say(f"    {text(t):55s} HW={u.weight} TAX={float(u.tax):.3f} "
            f"NRCI={float(u.nrci):.5f}")
    say("")
    say("  --- the random-noun baseline, same verbs, for comparison ---")
    for t in base:
        u = comp.compose(*t)
        say(f"    {text(t):55s} HW={u.weight} TAX={float(u.tax):.3f}")
    say("")

    # ── 4  repair demo ───────────────────────────────────────────────────
    say("=" * 78)
    say("4  REPAIR  (a broken sentence, what the grid says, the smallest fix)")
    say("=" * 78)
    for s, v, o in base[:8]:
        u = comp.compose(s, v, o)
        d = comp.diagnose(u)
        say(f"  {text((s, v, o))}")
        say(f"    HW={u.weight}  subject cells {popcount(u.subj_obj)}  "
            f"object cells {popcount(u.obj_obj)}  "
            f"exactly diagnosable: subj={d['subject']['exact']} "
            f"obj={d['object']['exact']}")
        for tag, slot, w in (("subject", "subj", s), ("object", "obj", o)):
            vio = comp.slot_violation(v, slot, w)
            if vio:
                labs = enc.labels_for(v, slot)
                names = [labs[i] for i in range(len(labs)) if (vio >> i) & 1]
                say(f"    {tag} '{w}' violates: {', '.join(names[:6])}"
                    + (" ..." if len(names) > 6 else ""))
        fix = repair(speaker, s, v, o, k=3)
        for k, vv in fix["suggestions"].items():
            say(f"    smallest fix, {k}: "
                + ", ".join(f"{n} (HW={w})" for n, w in vv))
        say("")

    (RESULTS / "generated_sentences.txt").write_text("\n".join(lines))
    (RESULTS / "exp5_generate.json").write_text(json.dumps(report, indent=2))
    print("wrote results/generated_sentences.txt and results/exp5_generate.json")


if __name__ == "__main__":
    main()
