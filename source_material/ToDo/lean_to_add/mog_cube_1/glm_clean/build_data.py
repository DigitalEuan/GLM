#!/usr/bin/env python3
"""
build_data.py — extract the two external, non-invented data sources the GLM
needs, and vendor them into `data/` as JSON so every later experiment is
reproducible without NLTK.

Source 1 — WordNet (Princeton).  For every word in the working vocabulary we
read off, for the first (most frequent) sense:
    * the lexicographer file  (noun.animal, noun.artifact, verb.motion, ...)
    * the full hypernym closure (nouns)
    * the WordNet sentence frames (verbs) — "Somebody ----s something" etc.,
      which are WordNet's own selectional restrictions.
None of this is invented by us.

Source 2 — corpora.
    * Brown (1.16M words, POS-tagged with the detailed Brown tagset) is the
      TRAINING corpus.  We extract (verb, subject-head) and (verb, object-head)
      with an explicit NP-boundary heuristic: only finite/base verb tags count
      as the verb, the argument must be the head of an adjacent NP, and an NP
      introduced by a preposition is rejected (it is a PP, not an argument).
    * The Penn Treebank sample (WSJ, gold parse trees with -SBJ function tags)
      is the TEST corpus.  Different genre, different annotation, gold syntax.

Usage:  python3 build_data.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from nltk.corpus import brown, treebank
from nltk.corpus import wordnet as wn

DATA = Path(__file__).resolve().parent / "data"
DATA.mkdir(exist_ok=True)

AUX = {
    "be", "have", "do", "will", "would", "shall", "should", "can", "could",
    "may", "might", "must", "let", "get", "make", "go", "come", "say",
}
# Brown tags
FINITE_VERB = {"VB", "VBD", "VBZ"}          # base / past / 3sg present
NOUN_TAGS = {"NN", "NNS", "NP", "NPS"}
NP_INTERNAL = {"AT", "AP", "ABN", "ABX", "AP$", "CD", "OD", "JJ", "JJR", "JJT",
               "JJS", "PP$", "QL", "QLP", "DT", "DTI", "DTS", "DTX", "NN", "NNS",
               "NP", "NPS", "NN$", "NP$", "NNS$", "NPS$", "*"}
PREP = {"IN", "TO"}
ADV = {"RB", "RBR", "RBT", "RP", "*", "NOT"}


def _clean(tag: str) -> str:
    """Brown tags carry suffixes like NN-TL, VBD-HL, NN+BEZ."""
    for sep in ("-", "+"):
        if sep in tag:
            tag = tag.split(sep)[0]
    return tag.upper()


def verb_lemma(w: str):
    w = w.lower()
    return wn.morphy(w, "v") or (w if wn.synsets(w, "v") else None)


def noun_lemma(w: str):
    w = w.lower()
    return wn.morphy(w, "n") or (w if wn.synsets(w, "n") else None)


# ── Brown extraction ─────────────────────────────────────────────────────────

def brown_pairs():
    subj = collections.Counter()
    obj = collections.Counter()
    for sent in brown.tagged_sents():
        toks = [(w, _clean(t)) for w, t in sent]
        n = len(toks)
        for i, (w, t) in enumerate(toks):
            if t not in FINITE_VERB:
                continue
            v = verb_lemma(w)
            if v is None or v in AUX:
                continue

            # ── object: the NP immediately to the right ──
            j = i + 1
            while j < n and toks[j][1] in ADV:
                j += 1
            start = j
            while j < n and toks[j][1] in NP_INTERNAL:
                j += 1
            # head = last noun of that NP
            head = None
            for k in range(start, j):
                if toks[k][1] in NOUN_TAGS:
                    head = toks[k][0]
            if head is not None and j > start:
                o = noun_lemma(head)
                if o:
                    obj[(v, o)] += 1

            # ── subject: the NP immediately to the left, not inside a PP ──
            j = i - 1
            while j >= 0 and toks[j][1] in ADV:
                j -= 1
            end = j
            while j >= 0 and toks[j][1] in NP_INTERNAL:
                j -= 1
            if end > j and (j < 0 or toks[j][1] not in PREP):
                head = None
                for k in range(j + 1, end + 1):
                    if toks[k][1] in NOUN_TAGS:
                        head = toks[k][0]
                if head is not None:
                    s = noun_lemma(head)
                    if s:
                        subj[(v, s)] += 1
    return subj, obj


# ── Treebank extraction (gold trees) ─────────────────────────────────────────

def _np_head(tree):
    """Head of a flat NP: its rightmost NN* token, ignoring embedded PPs."""
    head = None
    for child in tree:
        if not hasattr(child, "label"):
            continue
        if child.label() in ("PP", "SBAR", "S", "VP", "ADVP"):
            break
        for w, t in child.pos() if hasattr(child, "pos") else []:
            if t.startswith("NN"):
                head = w
    if head is None:
        for w, t in tree.pos():
            if t.startswith("NN"):
                head = w
                break
    return head


def treebank_pairs():
    subj = collections.Counter()
    obj = collections.Counter()
    triples = collections.Counter()
    for tree in treebank.parsed_sents():
        for st in tree.subtrees():
            if st.label() != "S":
                continue
            sbj_tree = vp = None
            for child in st:
                lbl = child.label() if hasattr(child, "label") else ""
                if lbl.startswith("NP-SBJ") and sbj_tree is None:
                    sbj_tree = child
                elif lbl == "VP" and vp is None:
                    vp = child
            if vp is None:
                continue
            while True:
                inner = [c for c in vp if hasattr(c, "label") and c.label() == "VP"]
                if not inner:
                    break
                vp = inner[0]
            verb = None
            for w, t in vp.pos():
                if t.startswith("VB"):
                    verb = w
                    break
            if verb is None:
                continue
            v = verb_lemma(verb)
            if v is None or v in AUX:
                continue
            sh = None
            if sbj_tree is not None:
                h = _np_head(sbj_tree)
                if h:
                    sh = noun_lemma(h)
                    if sh:
                        subj[(v, sh)] += 1
            oh = None
            for child in vp:
                if hasattr(child, "label") and child.label() == "NP":
                    h = _np_head(child)
                    if h:
                        oh = noun_lemma(h)
                        if oh:
                            obj[(v, oh)] += 1
                    break
            if sh and oh:
                triples[(sh, v, oh)] += 1
    return subj, obj, triples


# ── WordNet records ──────────────────────────────────────────────────────────

def noun_record(word: str):
    ss = wn.synsets(word, "n")
    if not ss:
        return None
    s = ss[0]
    anc = {a.name() for path in s.hypernym_paths() for a in path}
    return {"synset": s.name(), "definition": s.definition(),
            "lexname": s.lexname(), "ancestors": sorted(anc),
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
    print("extracting Brown pairs ...", flush=True)
    b_subj, b_obj = brown_pairs()
    print(f"  brown: {len(b_subj)} subj types / {sum(b_subj.values())} tokens, "
          f"{len(b_obj)} obj types / {sum(b_obj.values())} tokens")
    print("  most common objects:", b_obj.most_common(10))
    print("  most common subjects:", b_subj.most_common(10))
    print("extracting Treebank pairs ...", flush=True)
    t_subj, t_obj, t_tri = treebank_pairs()
    print(f"  wsj: {len(t_subj)} subj types, {len(t_obj)} obj types")

    pairs = {
        "brown_subj": [[v, n, c] for (v, n), c in b_subj.items()],
        "brown_obj": [[v, n, c] for (v, n), c in b_obj.items()],
        "wsj_subj": [[v, n, c] for (v, n), c in t_subj.items()],
        "wsj_obj": [[v, n, c] for (v, n), c in t_obj.items()],
    }
    (DATA / "corpus_pairs.json").write_text(json.dumps(pairs))
    (DATA / "wsj_triples.json").write_text(json.dumps(
        [[s_, v, o, c] for (s_, v, o), c in t_tri.items()]))
    print(f"wrote data/wsj_triples.json ({len(t_tri)} triples)")
    print("wrote data/corpus_pairs.json")

    verbs = {v for (v, _) in list(b_subj) + list(b_obj) + list(t_subj) + list(t_obj)}
    nouns = {n for (_, n) in list(b_subj) + list(b_obj) + list(t_subj) + list(t_obj)}
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
