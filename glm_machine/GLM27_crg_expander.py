
import os
import json
import re

def expand_crg(crg, vocab, sources=None, verbose=True):
    from GLM01_substrate import _CONCEPT_ALIASES, WordEntry, LEECH_ENGINE, BLA, _get_mog_category
    from GLM11_runtime import WordMath, geometricize_word, encode_semantic_octad

    added = 0
    # Build a robust reverse map (handling multiple formats)
    rev_aliases = {}
    for word, uid in _CONCEPT_ALIASES.items():
        rev_aliases[uid.lower()] = word
        rev_aliases[uid.upper()] = word

    target_vocab = vocab.words if hasattr(vocab, 'words') else vocab

    files = [f for f in os.listdir('.') if f.endswith('.json') or f.endswith('.md')]

    for filename in files:
        try:
            with open(filename, 'r') as f:
                if filename.endswith('.json'):
                    data = json.load(f)
                    # 1. Aggressive Relation Mining
                    for rel in data.get('relations', []):
                        if len(rel) >= 3:
                            # Resolve IDs to words
                            src = rev_aliases.get(rel[0]) or rel[0].lower()
                            dst = rev_aliases.get(rel[2]) or rel[2].lower()

                            # Ensure words exist in vocab (Learn them if missing)
                            for w in [src, dst]:
                                if w not in target_vocab and len(w) > 2:
                                    tag = geometricize_word(w)
                                    wm = WordMath(tag["layer"], tag["arm"], tag["category"], 0, w)
                                    vec = encode_semantic_octad(wm)
                                    target_vocab[w] = WordEntry(
                                        word=w, vector=vec, role=tag["category"].upper(),
                                        ubp_id=f"MINED_{w.upper()}", nrci=float(LEECH_ENGINE.calculate_nrci(vec)),
                                        golay_codeword=vec, fold3=BLA.fold24_to3(vec),
                                        mog_category=_get_mog_category(vec)
                                    )

                            if crg.add_edge(src, rel[1], dst): added += 1
                else:
                    # 2. MD Co-occurrence Mining
                    txt = f.read().lower()
                    words = re.findall(r'\b[a-z]{5,}\b', txt)
                    for i in range(len(words)-1):
                        w1, w2 = words[i], words[i+1]
                        if w1 in target_vocab and w2 in target_vocab:
                            if crg.add_edge(w1, 'relates_to', w2): added += 1
        except: continue

    if verbose: print(f"[GLM27] Aggressive Mining Complete: +{added} edges anchored.")
    return {"added": added}
