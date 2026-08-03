#!/usr/bin/env python3
"""
Experiment G-followup — Isolate signal retention to correctable-only vectors.

Exp G showed SVD-derived 24-bit vectors retain 82.8% of their context-similarity
signal after Golay snapping.  But 43.8% of vectors were beyond the decoder's
3-error correction radius and were left unchanged.  This experiment isolates
the signal-retention number to ONLY the vectors that were genuinely within
correction radius.
"""
from __future__ import annotations
import sys, os, json, re
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

os.chdir(Path(__file__).resolve().parent.parent / "glm_work")
sys.path.insert(0, str(Path(".").resolve()))

from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from GLM01_substrate import BLA, _build_vocabulary

def build_corpus():
    """Build corpus from master resource definitions."""
    with open("glm_master_resource_v1.json") as f:
        mr = json.load(f)
    corpus = []
    vocab_set = set()
    for word, entry in mr["vocabulary"].items():
        if " " in word or "-" in word:
            continue
        if len(word) < 3:
            continue
        if not isinstance(entry, dict):
            continue
        defn = entry.get("definition", "")
        if not defn:
            continue
        tokens = re.findall(r"[a-z]+", defn.lower())
        corpus.extend(tokens)
        vocab_set.add(word.lower())
    return corpus, vocab_set

def build_cooccurrence(corpus, vocab_set, window=5):
    """Build word-context co-occurrence matrix."""
    vocab_list = sorted(vocab_set)
    vocab_idx = {w: i for i, w in enumerate(vocab_list)}

    # Use top-N most frequent words as context
    freq = Counter(corpus)
    context_words = [w for w, _ in freq.most_common(200) if w in vocab_set]
    context_idx = {w: i for i, w in enumerate(context_words)}

    cooc = np.zeros((len(vocab_list), len(context_words)), dtype=np.float64)
    for i, token in enumerate(corpus):
        if token not in vocab_idx:
            continue
        wi = vocab_idx[token]
        for j in range(max(0, i-window), min(len(corpus), i+window+1)):
            if j == i:
                continue
            ctx = corpus[j]
            if ctx in context_idx:
                cooc[wi, context_idx[ctx]] += 1
    return vocab_list, cooc

def build_svd_vectors(cooc, n_dims=24):
    """Build SVD/LSA vectors, median-quantized to 24 bits."""
    # PPMI transform
    total = cooc.sum()
    row_sums = cooc.sum(axis=1, keepdims=True)
    col_sums = cooc.sum(axis=0, keepdims=True)
    # Avoid division by zero
    row_sums[row_sums == 0] = 1
    col_sums[col_sums == 0] = 1
    ppmi = np.log2((cooc * total) / (row_sums * col_sums) + 1e-10)
    ppmi[ppmi < 0] = 0

    # Truncated SVD
    from numpy.linalg import svd
    U, S, Vt = np.linalg.svd(ppmi, full_matrices=False)
    svd_vecs = U[:, :n_dims] * S[:n_dims]

    # Median-quantize to 24 bits
    medians = np.median(svd_vecs, axis=0)
    bit_vecs = (svd_vecs > medians).astype(int)
    return bit_vecs

def context_similarity_test(vectors_a, vectors_b, cooc, vocab_list):
    """Compute Spearman correlation between vector Hamming distance and
    context-similarity (cosine over co-occurrence profiles)."""
    from scipy.stats import spearmanr

    n = len(vectors_a)
    # Sample pairs
    rng = np.random.RandomState(42)
    n_pairs = min(5000, n * (n - 1) // 2)
    idx_a = rng.randint(0, n, size=n_pairs)
    idx_b = rng.randint(0, n, size=n_pairs)
    # Ensure different
    mask = idx_a != idx_b
    idx_a = idx_a[mask]
    idx_b = idx_b[mask]

    # Hamming distances
    ham_dists = []
    for a, b in zip(idx_a, idx_b):
        hd = sum(1 for x, y in zip(vectors_a[a], vectors_b[b]) if x != y)
        ham_dists.append(hd)

    # Context similarities (cosine)
    ctx_sims = []
    for a, b in zip(idx_a, idx_b):
        va = cooc[a]
        vb = cooc[b]
        na = np.linalg.norm(va)
        nb = np.linalg.norm(vb)
        if na > 0 and nb > 0:
            sim = np.dot(va, vb) / (na * nb)
        else:
            sim = 0
        ctx_sims.append(sim)

    rho, p = spearmanr(ham_dists, ctx_sims)
    return rho, p

def main():
    print("=" * 80)
    print("EXPERIMENT G-followup: Isolate signal retention to correctable-only vectors")
    print("=" * 80)

    print("\nBuilding corpus from master resource definitions...")
    corpus, vocab_set = build_corpus()
    print(f"  Corpus: {len(corpus)} tokens, {len(vocab_set)} unique words")

    print("\nBuilding co-occurrence matrix...")
    vocab_list, cooc = build_cooccurrence(corpus, vocab_set)
    print(f"  Co-occurrence matrix: {cooc.shape}")

    print("\nBuilding SVD-derived 24-bit vectors...")
    svd_vecs = build_svd_vectors(cooc, n_dims=24)
    print(f"  SVD vectors: {svd_vecs.shape}")

    # Test 1: Pre-snap signal
    print("\n--- Pre-snap context-similarity test ---")
    rho_pre, p_pre = context_similarity_test(svd_vecs, svd_vecs, cooc, vocab_list)
    print(f"  Spearman ρ (pre-snap) = {rho_pre:.4f} (p={p_pre:.2e})")

    # Snap all vectors
    print("\n--- Snapping SVD vectors to Golay codewords ---")
    snapped_vecs = []
    correctable = []
    for vec in svd_vecs:
        vec_list = list(vec)
        snapped, meta = GOLAY_ENGINE.snap_to_codeword(vec_list)
        snapped_vecs.append(snapped)
        correctable.append(meta.get("correctable", True) and meta.get("corrected", False) or meta.get("syndrome_weight", 0) == 0)

    correctable = np.array(correctable)
    n_correctable = correctable.sum()
    n_total = len(correctable)
    print(f"  Correctable (within 3-error radius): {n_correctable}/{n_total} ({n_correctable/n_total*100:.1f}%)")
    print(f"  Beyond correction radius: {n_total - n_correctable}/{n_total} ({(n_total-n_correctable)/n_total*100:.1f}%)")

    # Test 2: Post-snap signal (all vectors)
    print("\n--- Post-snap context-similarity test (ALL vectors) ---")
    snapped_arr = np.array(snapped_vecs)
    rho_post_all, p_post_all = context_similarity_test(snapped_arr, snapped_arr, cooc, vocab_list)
    print(f"  Spearman ρ (post-snap, all) = {rho_post_all:.4f} (p={p_post_all:.2e})")
    print(f"  Retention: {rho_post_all/rho_pre*100:.1f}%")

    # Test 3: Post-snap signal (correctable-only)
    print("\n--- Post-snap context-similarity test (CORRECTABLE-only) ---")
    if n_correctable > 10:
        snapped_correctable = snapped_arr[correctable]
        cooc_correctable = cooc[correctable]
        rho_post_corr, p_post_corr = context_similarity_test(
            snapped_correctable, snapped_correctable, cooc_correctable, vocab_list)
        print(f"  Spearman ρ (post-snap, correctable) = {rho_post_corr:.4f} (p={p_post_corr:.2e})")
        print(f"  Retention: {rho_post_corr/rho_pre*100:.1f}%")
    else:
        print("  Too few correctable vectors for a meaningful test")

    # Test 4: Pre-snap signal (correctable-only subset, for fair comparison)
    print("\n--- Pre-snap context-similarity test (correctable-only subset) ---")
    if n_correctable > 10:
        svd_correctable = svd_vecs[correctable]
        rho_pre_corr, p_pre_corr = context_similarity_test(
            svd_correctable, svd_correctable, cooc_correctable, vocab_list)
        print(f"  Spearman ρ (pre-snap, correctable subset) = {rho_pre_corr:.4f} (p={p_pre_corr:.2e})")
        if rho_pre_corr != 0:
            print(f"  Isolated retention: {rho_post_corr/rho_pre_corr*100:.1f}%")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Pre-snap ρ (all):              {rho_pre:.4f}")
    print(f"  Post-snap ρ (all):             {rho_post_all:.4f}  (retention: {rho_post_all/rho_pre*100:.1f}%)")
    if n_correctable > 10:
        print(f"  Pre-snap ρ (correctable only): {rho_pre_corr:.4f}")
        print(f"  Post-snap ρ (correctable only): {rho_post_corr:.4f}  (isolated retention: {rho_post_corr/rho_pre_corr*100:.1f}%)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
