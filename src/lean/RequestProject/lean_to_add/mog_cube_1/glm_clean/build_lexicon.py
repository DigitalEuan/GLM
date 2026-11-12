#!/usr/bin/env python3
"""
build_lexicon.py — WordNet records for every word appearing in any pair file.

Run after build_data.py and build_bigdata.py.  Rebuilds
data/wordnet_lexicon.json over the union of the vocabularies so that the large
dependency-parsed corpus is fully covered.
"""
from __future__ import annotations

import json
from pathlib import Path

from nltk.corpus import wordnet as wn

DATA = Path(__file__).resolve().parent / "data"


def noun_record(word: str):
    ss = wn.synsets(word, "n")
    if not ss:
        return None
    s = ss[0]
    anc = {a.name() for path in s.hypernym_paths() for a in path}
    anc3 = {a.name() for syn in ss[:3] for path in syn.hypernym_paths()
            for a in path}
    return {"synset": s.name(), "definition": s.definition(),
            "lexname": s.lexname(), "ancestors": sorted(anc),
            "ancestors3": sorted(anc3),
            "lexnames3": sorted({syn.lexname() for syn in ss[:3]}),
            "n_senses": len(ss), "depth": s.max_depth()}


def verb_record(word: str):
    ss = wn.synsets(word, "v")
    if not ss:
        return None
    s = ss[0]
    frames = sorted({f for l in s.lemmas() for f in l.frame_ids()})
    all_frames = sorted({f for syn in ss[:3] for l in syn.lemmas()
                         for f in l.frame_ids()})
    anc = {a.name() for path in s.hypernym_paths() for a in path}
    return {"synset": s.name(), "definition": s.definition(),
            "lexname": s.lexname(), "frames": frames, "frames_top3": all_frames,
            "ancestors": sorted(anc), "n_senses": len(ss)}


def main():
    verbs, nouns = set(), set()
    for fn in ("corpus_pairs.json", "dep_pairs.json"):
        p = DATA / fn
        if not p.exists():
            continue
        for _key, rows in json.loads(p.read_text()).items():
            for v, n, _c in rows:
                verbs.add(v)
                nouns.add(n)
    p = DATA / "dep_triples.json"
    if p.exists():
        for s, v, o, _c in json.loads(p.read_text()):
            verbs.add(v)
            nouns.add(s)
            nouns.add(o)
    print(f"vocabulary: {len(verbs)} verbs, {len(nouns)} nouns")

    lex = {"nouns": {}, "verbs": {}}
    for w in sorted(nouns):
        r = noun_record(w)
        if r:
            lex["nouns"][w] = r
    for w in sorted(verbs):
        r = verb_record(w)
        if r:
            lex["verbs"][w] = r
    (DATA / "wordnet_lexicon.json").write_text(json.dumps(lex))
    print(f"wrote data/wordnet_lexicon.json ({len(lex['nouns'])} nouns, "
          f"{len(lex['verbs'])} verbs)")


if __name__ == "__main__":
    main()
