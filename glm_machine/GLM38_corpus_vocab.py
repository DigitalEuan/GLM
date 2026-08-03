#!/usr/bin/env python3
"""
GLM38: CORPUS-DRIVEN VOCABULARY BUILDER
=========================================
Builds SVD-derived 24-bit vectors from arbitrary text corpora.
Feeds the vectors into the GLM vocabulary.

Usage:
    from GLM38_corpus_vocab import build_vocab_from_corpus
    vocab = build_vocab_from_corpus('corpus.txt', existing_vocab, crg)
"""

import re
import hashlib
from collections import Counter
from typing import List, Dict, Tuple, Any
import numpy as np

from GLM01_substrate import (
    WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category,
    vector_to_hex_int,
)


def tokenize_corpus(text: str) -> List[str]:
    """Tokenize text into lowercase words."""
    return [w.lower() for w in re.findall(r'[a-z]+', text.lower()) if len(w) >= 3]


def build_cooccurrence_matrix(tokens: List[str], vocab_words: List[str],
                               window: int = 5, n_context: int = 500) -> np.ndarray:
    """Build a PPMI co-occurrence matrix."""
    vocab_idx = {w: i for i, w in enumerate(vocab_words)}
    freq = Counter(tokens)
    context_words = [w for w, _ in freq.most_common(n_context) if w in vocab_idx]
    context_idx = {w: i for i, w in enumerate(context_words)}

    cooc = np.zeros((len(vocab_words), len(context_words)), dtype=np.float64)
    for i, token in enumerate(tokens):
        if token not in vocab_idx:
            continue
        wi = vocab_idx[token]
        for j in range(max(0, i - window), min(len(tokens), i + window + 1)):
            if j == i:
                continue
            ctx = tokens[j]
            if ctx in context_idx:
                cooc[wi, context_idx[ctx]] += 1
    return cooc


def svd_to_bit_vectors(cooc: np.ndarray, n_dims: int = 24) -> np.ndarray:
    """SVD on PPMI matrix, median-quantize to 24 bits."""
    total = cooc.sum()
    row_sums = cooc.sum(axis=1, keepdims=True)
    col_sums = cooc.sum(axis=0, keepdims=True)
    row_sums[row_sums == 0] = 1
    col_sums[col_sums == 0] = 1
    ppmi = np.log2((cooc * total) / (row_sums * col_sums) + 1e-10)
    ppmi[ppmi < 0] = 0

    U, S, Vt = np.linalg.svd(ppmi, full_matrices=False)
    svd_vecs = U[:, :n_dims] * S[:n_dims]

    medians = np.median(svd_vecs, axis=0)
    bit_vecs = (svd_vecs > medians).astype(int)
    return bit_vecs


def snap_to_golay(bit_vecs: np.ndarray) -> List[List[int]]:
    """Snap each 24-bit vector to nearest Golay codeword."""
    snapped = []
    for vec in bit_vecs:
        vec_list = [int(b) for b in vec]
        sn, meta = GOLAY_ENGINE.snap_to_codeword(vec_list)
        snapped.append(list(sn))
    return snapped


def build_vocab_from_corpus(corpus_path: str, existing_vocab: Dict[str, Any],
                             min_freq: int = 3, max_words: int = 3000) -> Dict[str, Any]:
    """Build vocabulary entries from a text corpus.
    
    Args:
        corpus_path: Path to plain text corpus
        existing_vocab: Current vocabulary dict (will be extended)
        min_freq: Minimum word frequency to include
        max_words: Maximum new words to add
        
    Returns:
        Extended vocabulary dict
    """
    print(f"[GLM38] Reading corpus: {corpus_path}")
    with open(corpus_path, 'r') as f:
        text = f.read()
    
    tokens = tokenize_corpus(text)
    freq = Counter(tokens)
    print(f"[GLM38] Corpus: {len(tokens)} tokens, {len(freq)} unique words")
    
    # Filter by frequency and exclude existing vocab
    candidate_words = [w for w, c in freq.most_common(max_words * 2)
                       if c >= min_freq and w not in existing_vocab and len(w) >= 3]
    candidate_words = candidate_words[:max_words]
    print(f"[GLM38] Candidates: {len(candidate_words)} new words")
    
    if not candidate_words:
        print("[GLM38] No new words to add")
        return existing_vocab
    
    # Build co-occurrence and SVD
    print("[GLM38] Building co-occurrence matrix...")
    cooc = build_cooccurrence_matrix(tokens, candidate_words, window=5, n_context=500)
    
    print("[GLM38] Running SVD...")
    bit_vecs = svd_to_bit_vectors(cooc, n_dims=24)
    
    print("[GLM38] Snapping to Golay codewords...")
    snapped_vecs = snap_to_golay(bit_vecs)
    
    # Create WordEntry objects
    added = 0
    for word, vec in zip(candidate_words, snapped_vecs):
        if sum(vec) < 3 or sum(vec) > 21:  # Skip degenerate vectors
            continue
        
        nrci = float(LEECH_ENGINE.calculate_nrci(vec))
        entry = WordEntry(
            word=word,
            vector=vec,
            role="NOUN",
            ubp_id=f"CORPUS_{word.upper()}",
            nrci=nrci,
            golay_codeword=vec,
            fold3=BLA.fold24_to3(vec),
            mog_category=_get_mog_category(vec),
        )
        # Attach frequency as a rough "importance" score
        entry.freq = freq.get(word, 0)
        existing_vocab[word] = entry
        added += 1
    
    print(f"[GLM38] Added {added} corpus-derived words to vocabulary")
    return existing_vocab


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 GLM38_corpus_vocab.py <corpus.txt>")
        sys.exit(1)
    
    vocab = build_vocab_from_corpus(sys.argv[1], {})
    print(f"Total vocabulary: {len(vocab)} words")
