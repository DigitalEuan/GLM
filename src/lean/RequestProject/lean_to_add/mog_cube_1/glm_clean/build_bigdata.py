#!/usr/bin/env python3
"""
build_bigdata.py — the large training corpus.

The Brown corpus (1.1M words, shallow chunking) turned out to be far too small
and too noisy to estimate what a verb expects of its arguments: even an
unrestricted continuous class model only reached ~0.60 on pseudo-disambiguation
(results/exp1_selection.json).  So we parse a much larger corpus with a real
dependency parser.

  text     the NLTK literary corpora (gutenberg, webtext, reuters) plus
           WikiText-103 (Wikipedia)
  parser   spaCy en_core_web_sm  (tagger + parser + lemmatizer)
  extract  for every VERB token: its `nsubj` and its `dobj`, lemmatised,
           restricted to common nouns (PROPN excluded: mostly outside WordNet)

The work is sharded: run one single-process job per shard (spaCy's built-in
multiprocessing deadlocked on long documents) and then merge.

  python3 build_bigdata.py --shard 0 --nshards 8 --words 30000000
  python3 build_bigdata.py --merge
"""
from __future__ import annotations

import argparse
import collections
import json
import time
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
SHARDS = DATA / "shards"
DATA.mkdir(exist_ok=True)

AUX_LEMMAS = {"be", "have", "do", "will", "would", "shall", "should", "can",
              "could", "may", "might", "must"}
PIECE = 40_000          # characters per document handed to spaCy


def pieces(max_chars: int):
    """Yield ~40k-character documents: literary corpora first, then Wikipedia."""
    used = 0
    from nltk.corpus import gutenberg, webtext, reuters
    for corpus in (gutenberg, webtext, reuters):
        buf = []
        n = 0
        for fid in corpus.fileids():
            t = corpus.raw(fid)
            for k in range(0, len(t), PIECE):
                p = t[k:k + PIECE]
                buf.append(p)
                n += len(p)
                if n >= PIECE:
                    used += n
                    yield "".join(buf)
                    buf, n = [], 0
                    if used >= max_chars:
                        return
        if buf:
            used += n
            yield "".join(buf)

    from datasets import load_dataset
    ds = load_dataset("Salesforce/wikitext", "wikitext-103-raw-v1", split="train")
    buf, n = [], 0
    for row in ds:
        t = row["text"].strip()
        if not t or t.startswith("="):
            continue
        buf.append(t)
        n += len(t)
        if n >= PIECE:
            used += n
            yield " ".join(buf)
            buf, n = [], 0
            if used >= max_chars:
                return


def run_shard(shard: int, nshards: int, max_chars: int):
    import spacy
    nlp = spacy.load("en_core_web_sm", exclude=["ner"])
    nlp.max_length = 200_000
    subj = collections.Counter()
    obj = collections.Counter()
    triples = collections.Counter()
    t0 = time.time()
    ntok = 0
    ndoc = 0
    mine = (p for i, p in enumerate(pieces(max_chars)) if i % nshards == shard)
    for doc in nlp.pipe(mine, batch_size=8):
        ndoc += 1
        ntok += len(doc)
        for tok in doc:
            if tok.pos_ != "VERB":
                continue
            v = tok.lemma_.lower()
            if not v.isalpha() or v in AUX_LEMMAS:
                continue
            s = o = None
            for ch in tok.children:
                if ch.dep_ == "nsubj" and ch.pos_ == "NOUN":
                    s = ch.lemma_.lower()
                elif ch.dep_ == "dobj" and ch.pos_ == "NOUN":
                    o = ch.lemma_.lower()
            if s and s.isalpha():
                subj[(v, s)] += 1
            if o and o.isalpha():
                obj[(v, o)] += 1
            if s and o and s.isalpha() and o.isalpha():
                triples[(s, v, o)] += 1
        if ndoc % 100 == 0:
            print(f"  shard {shard}: {ndoc} docs {ntok/1e6:.2f}M tok "
                  f"{time.time()-t0:.0f}s", flush=True)
    SHARDS.mkdir(exist_ok=True)
    (SHARDS / f"shard{shard}.json").write_text(json.dumps({
        "tokens": ntok,
        "subj": [[v, n, c] for (v, n), c in subj.items()],
        "obj": [[v, n, c] for (v, n), c in obj.items()],
        "triples": [[s, v, o, c] for (s, v, o), c in triples.items()],
    }))
    print(f"shard {shard} done: {ntok/1e6:.2f}M tokens, {time.time()-t0:.0f}s")


def merge(min_count: int = 2):
    subj = collections.Counter()
    obj = collections.Counter()
    tri = collections.Counter()
    tok = 0
    for p in sorted(SHARDS.glob("shard*.json")):
        d = json.loads(p.read_text())
        tok += d["tokens"]
        for v, n, c in d["subj"]:
            subj[(v, n)] += c
        for v, n, c in d["obj"]:
            obj[(v, n)] += c
        for s, v, o, c in d["triples"]:
            tri[(s, v, o)] += c
    print(f"merged {tok/1e6:.1f}M tokens")
    print(f"  subj {len(subj)} types / {sum(subj.values())} tokens")
    print(f"  obj  {len(obj)} types / {sum(obj.values())} tokens")
    print(f"  triples {len(tri)} types / {sum(tri.values())} tokens")
    print("  top objects:", obj.most_common(12))
    print("  top triples:", tri.most_common(8))
    (DATA / "dep_pairs.json").write_text(json.dumps({
        "dep_subj": [[v, n, c] for (v, n), c in subj.items() if c >= min_count],
        "dep_obj": [[v, n, c] for (v, n), c in obj.items() if c >= min_count],
    }))
    (DATA / "dep_triples.json").write_text(json.dumps(
        [[s, v, o, c] for (s, v, o), c in tri.items() if c >= min_count]))
    print("wrote data/dep_pairs.json, data/dep_triples.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--words", type=int, default=30_000_000)
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()
    if args.merge:
        merge()
    else:
        run_shard(args.shard, args.nshards, args.words * 6)


if __name__ == "__main__":
    main()
