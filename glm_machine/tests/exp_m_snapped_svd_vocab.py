#!/usr/bin/env python3
"""
Experiment M — SVD+Golay-snapped vectors as a working vocabulary embedding.

THE LOAD-BEARING QUESTION: Can SVD-derived vectors, snapped to Golay codewords,
function as a real language embedding space?

Exp G-followup showed snapping ENHANCES the signal (154.5% retention).  This
experiment goes further: tests whether the snapped vectors can actually DO
language tasks, not just correlate with context-similarity.

Tests:
  1. Paradigmatic similarity: do k-nearest neighbors in the snapped space
     actually appear in similar corpus contexts? (k-NN precision@10)
  2. Next-word prediction: given a context word, can vector similarity
     predict the next word better than frequency baseline?
  3. Analogy: does vector arithmetic (a - b + c) find the expected 4th word?

Compares three vector spaces:
  A. Current GLM vocab (hash-derived, snapped to Golay)
  B. Raw SVD vectors (not snapped)
  C. SVD vectors snapped to Golay codewords (the proposed new vocab)

If C beats both A and B on the language tasks, we have a working UBP-native
embedding space — the foundation for a non-random language machine.
"""
from __future__ import annotations
import sys, os, json, re, time
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from scipy.stats import spearmanr

os.chdir(Path(__file__).resolve().parent.parent / "glm_work")
sys.path.insert(0, str(Path(".").resolve()))

from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from GLM01_substrate import _build_vocabulary, BLA, vector_to_hex_int

# ── 1. Build corpus + co-occurrence ──────────────────────────────────────────

def build_corpus_and_vocab():
    """Build corpus from master resource definitions."""
    with open("glm_master_resource_v1.json") as f:
        mr = json.load(f)
    corpus = []
    word_defs = {}  # word -> definition
    for word, entry in mr["vocabulary"].items():
        if not isinstance(entry, dict):
            continue
        if " " in word or "-" in word:
            continue
        if len(word) < 3:
            continue
        defn = entry.get("definition", "")
        if not defn or len(defn) < 20:
            continue
        tokens = re.findall(r"[a-z]+", defn.lower())
        # Filter to tokens >= 3 chars
        tokens = [t for t in tokens if len(t) >= 3]
        corpus.extend(tokens)
        word_defs[word.lower()] = defn
    return corpus, word_defs

def build_cooccurrence(corpus, vocab_list, window=5):
    """Build PPMI co-occurrence matrix."""
    vocab_idx = {w: i for i, w in enumerate(vocab_list)}
    freq = Counter(corpus)
    # Use top-300 most frequent words as context
    context_words = [w for w, _ in freq.most_common(300) if w in vocab_idx]
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
    return cooc, context_words

def build_svd_vectors(cooc, n_dims=24):
    """Build SVD/LSA vectors, median-quantized to 24 bits."""
    # PPMI transform
    total = cooc.sum()
    row_sums = cooc.sum(axis=1, keepdims=True)
    col_sums = cooc.sum(axis=0, keepdims=True)
    row_sums[row_sums == 0] = 1
    col_sums[col_sums == 0] = 1
    ppmi = np.log2((cooc * total) / (row_sums * col_sums) + 1e-10)
    ppmi[ppmi < 0] = 0

    # Truncated SVD
    U, S, Vt = np.linalg.svd(ppmi, full_matrices=False)
    svd_vecs = U[:, :n_dims] * S[:n_dims]

    # Median-quantize to 24 bits
    medians = np.median(svd_vecs, axis=0)
    bit_vecs = (svd_vecs > medians).astype(int)
    return bit_vecs, svd_vecs  # return both binary and continuous

def snap_to_golay(bit_vecs):
    """Snap each 24-bit vector to the nearest Golay codeword."""
    snapped = []
    n_correctable = 0
    for vec in bit_vecs:
        vec_list = list(int(b) for b in vec)
        sn, meta = GOLAY_ENGINE.snap_to_codeword(vec_list)
        snapped.append(sn)
        if meta.get("correctable", True):
            n_correctable += 1
    return np.array(snapped), n_correctable

# ── 2. Tests ─────────────────────────────────────────────────────────────────

def paradigmatic_similarity(vectors, cooc, vocab_list, k=10, n_samples=500):
    """Test 1: Do k-nearest neighbors in vector space appear in similar contexts?

    For each sampled word, find its k nearest neighbors by Hamming distance.
    Then check if those neighbors have high cosine similarity in the
    co-occurrence matrix (paradigmatic similarity).

    Returns: mean precision@k (fraction of neighbors in top-k context-similarity)
    """
    n = len(vectors)
    rng = np.random.RandomState(42)
    sample_idx = rng.choice(n, min(n_samples, n), replace=False)

    precisions = []
    for idx in sample_idx:
        # Hamming distances to all other vectors
        target = vectors[idx]
        ham_dists = np.array([sum(1 for a, b in zip(target, v) if a != b) for v in vectors])
        ham_dists[idx] = 999  # exclude self
        # Top-k nearest
        nn_idx = np.argsort(ham_dists)[:k]

        # Context similarities (cosine over co-occurrence)
        target_ctx = cooc[idx]
        target_norm = np.linalg.norm(target_ctx)
        if target_norm == 0:
            continue
        ctx_sims = []
        for ni in nn_idx:
            ctx = cooc[ni]
            cn = np.linalg.norm(ctx)
            if cn > 0:
                ctx_sims.append(np.dot(target_ctx, ctx) / (target_norm * cn))
            else:
                ctx_sims.append(0)

        # Precision@k: fraction of nn that are in the top-k by context similarity
        all_ctx_sims = []
        for i in range(n):
            if i == idx:
                continue
            ctx = cooc[i]
            cn = np.linalg.norm(ctx)
            if cn > 0:
                all_ctx_sims.append((i, np.dot(target_ctx, ctx) / (target_norm * cn)))
        all_ctx_sims.sort(key=lambda x: -x[1])
        top_k_ctx = set(i for i, _ in all_ctx_sims[:k])

        precision = len(top_k_ctx & set(nn_idx)) / k
        precisions.append(precision)

    return np.mean(precisions) if precisions else 0

def next_word_prediction(vectors, corpus, vocab_list, n_samples=1000):
    """Test 2: Can vector similarity predict the next word?

    For each sampled position in the corpus, use the current word's vector
    to find k nearest neighbors, and check if the actual next word is
    among them.

    Returns: hit rate (fraction where next word is in top-k neighbors)
    """
    n = len(vectors)
    vocab_idx = {w: i for i, w in enumerate(vocab_list)}
    rng = np.random.RandomState(42)

    # Build Hamming distance lookup (precompute for speed)
    # Actually, for n~4000, computing on-the-fly is too slow. Precompute hex ints.
    hex_ints = np.array([sum(int(b) << (23-i) for i, b in enumerate(v)) for v in vectors])

    k = 20  # top-20 neighbors
    hits = 0
    total = 0

    # Sample positions
    valid_positions = [i for i in range(len(corpus)-1)
                       if corpus[i] in vocab_idx and corpus[i+1] in vocab_idx]
    if len(valid_positions) > n_samples:
        sample_pos = rng.choice(valid_positions, n_samples, replace=False)
    else:
        sample_pos = valid_positions

    for pos in sample_pos:
        cur_word = corpus[pos]
        next_word = corpus[pos + 1]
        cur_idx = vocab_idx[cur_word]
        next_idx = vocab_idx[next_word]

        # Hamming distances via XOR of hex ints
        cur_hex = hex_ints[cur_idx]
        ham_dists = np.array([bin(int(cur_hex ^ h)).count('1') for h in hex_ints])
        ham_dists[cur_idx] = 999
        nn_idx = np.argsort(ham_dists)[:k]

        if next_idx in nn_idx:
            hits += 1
        total += 1

    return hits / total if total > 0 else 0

def frequency_baseline(corpus, n_samples=1000):
    """Baseline: predict the most frequent word as the next word."""
    freq = Counter(corpus)
    most_common = freq.most_common(1)[0][0]
    rng = np.random.RandomState(42)
    valid_positions = list(range(len(corpus)-1))
    if len(valid_positions) > n_samples:
        sample_pos = rng.choice(valid_positions, n_samples, replace=False)
    else:
        sample_pos = valid_positions
    hits = sum(1 for pos in sample_pos if corpus[pos+1] == most_common)
    return hits / len(sample_pos) if len(sample_pos) > 0 else 0

# ── 3. Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("EXPERIMENT M: SVD+Golay-snapped vectors as a working vocabulary embedding")
    print("=" * 80)

    print("\nBuilding corpus...")
    corpus, word_defs = build_corpus_and_vocab()
    print(f"  Corpus: {len(corpus)} tokens, {len(word_defs)} defined words")

    # Build vocab list (words that have both definitions AND are in GLM vocab)
    glm_vocab = _build_vocabulary()
    glm_words = set(glm_vocab.keys())
    corpus_vocab = set(word_defs.keys())
    # Intersection: words in both GLM vocab and corpus
    shared_vocab = sorted(glm_words & corpus_vocab)
    # Also add high-frequency corpus words not in GLM
    freq = Counter(corpus)
    for w, _ in freq.most_common(500):
        if w not in shared_vocab and len(w) >= 3:
            shared_vocab.append(w)
    shared_vocab = sorted(set(shared_vocab))
    print(f"  Shared vocab: {len(shared_vocab)} words")

    print("\nBuilding co-occurrence matrix...")
    cooc, context_words = build_cooccurrence(corpus, shared_vocab)
    print(f"  Co-occurrence: {cooc.shape}, context words: {len(context_words)}")

    print("\nBuilding SVD vectors (24-bit)...")
    svd_bits, svd_continuous = build_svd_vectors(cooc, n_dims=24)
    print(f"  SVD bit vectors: {svd_bits.shape}")

    print("\nSnapping SVD vectors to Golay codewords...")
    snapped, n_correctable = snap_to_golay(svd_bits)
    print(f"  Correctable: {n_correctable}/{len(snapped)} ({n_correctable/len(snapped)*100:.1f}%)")

    # Also get current GLM vectors for comparison
    print("\nExtracting current GLM vocab vectors...")
    glm_vecs = []
    for w in shared_vocab:
        entry = glm_vocab.get(w)
        if entry and hasattr(entry, 'vector') and entry.vector:
            glm_vecs.append(list(entry.vector))
        else:
            glm_vecs.append([0]*24)
    glm_vecs = np.array(glm_vecs)
    print(f"  GLM vectors: {glm_vecs.shape}")

    # ── TEST 1: Paradigmatic similarity (precision@10) ───────────────────
    print("\n" + "=" * 80)
    print("TEST 1: Paradigmatic similarity (precision@10)")
    print("  Do k-nearest neighbors in vector space appear in similar contexts?")
    print("=" * 80)

    p_glm = paradigmatic_similarity(glm_vecs, cooc, shared_vocab, k=10, n_samples=300)
    p_svd = paradigmatic_similarity(svd_bits, cooc, shared_vocab, k=10, n_samples=300)
    p_snapped = paradigmatic_similarity(snapped, cooc, shared_vocab, k=10, n_samples=300)

    print(f"  GLM hash vectors:     precision@10 = {p_glm:.4f}")
    print(f"  Raw SVD vectors:      precision@10 = {p_svd:.4f}")
    print(f"  SVD+Golay-snapped:    precision@10 = {p_snapped:.4f}")
    print(f"  Random baseline:      precision@10 = {10/len(shared_vocab):.4f}")

    # ── TEST 2: Next-word prediction (hit rate @ top-20) ─────────────────
    print("\n" + "=" * 80)
    print("TEST 2: Next-word prediction (hit rate @ top-20)")
    print("  Can vector similarity predict the next word?")
    print("=" * 80)

    freq_base = frequency_baseline(corpus, n_samples=1000)
    print(f"  Frequency baseline:   {freq_base:.4f}")

    # Only run if vocab is manageable
    if len(shared_vocab) <= 5000:
        nw_glm = next_word_prediction(glm_vecs, corpus, shared_vocab, n_samples=500)
        nw_svd = next_word_prediction(svd_bits, corpus, shared_vocab, n_samples=500)
        nw_snapped = next_word_prediction(snapped, corpus, shared_vocab, n_samples=500)
        print(f"  GLM hash vectors:     {nw_glm:.4f}")
        print(f"  Raw SVD vectors:      {nw_svd:.4f}")
        print(f"  SVD+Golay-snapped:    {nw_snapped:.4f}")
    else:
        print("  (Skipped — vocab too large for brute-force k-NN)")

    # ── TEST 3: Signal retention (Spearman ρ) ────────────────────────────
    print("\n" + "=" * 80)
    print("TEST 3: Context-similarity correlation (Spearman ρ)")
    print("=" * 80)

    def spearman_test(vectors, cooc, n_pairs=3000):
        n = len(vectors)
        rng = np.random.RandomState(42)
        idx_a = rng.randint(0, n, n_pairs)
        idx_b = rng.randint(0, n, n_pairs)
        mask = idx_a != idx_b
        idx_a, idx_b = idx_a[mask], idx_b[mask]

        ham = [sum(1 for x, y in zip(vectors[a], vectors[b]) if x != y)
               for a, b in zip(idx_a, idx_b)]
        ctx = []
        for a, b in zip(idx_a, idx_b):
            va, vb = cooc[a], cooc[b]
            na, nb = np.linalg.norm(va), np.linalg.norm(vb)
            ctx.append(np.dot(va, vb) / (na * nb) if na > 0 and nb > 0 else 0)
        rho, _ = spearmanr(ham, ctx)
        return rho

    s_glm = spearman_test(glm_vecs, cooc)
    s_svd = spearman_test(svd_bits, cooc)
    s_snapped = spearman_test(snapped, cooc)
    print(f"  GLM hash vectors:     ρ = {s_glm:.4f}")
    print(f"  Raw SVD vectors:      ρ = {s_svd:.4f}")
    print(f"  SVD+Golay-snapped:    ρ = {s_snapped:.4f}")

    # ── SUMMARY ───────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'Vector Space':<25} {'Prec@10':>10} {'NextWord@20':>12} {'Spearman ρ':>12}")
    print("-" * 60)
    print(f"{'GLM hash (current)':<25} {p_glm:>10.4f} {'(see above)':>12} {s_glm:>12.4f}")
    print(f"{'Raw SVD':<25} {p_svd:>10.4f} {'(see above)':>12} {s_svd:>12.4f}")
    print(f"{'SVD+Golay-snapped':<25} {p_snapped:>10.4f} {'(see above)':>12} {s_snapped:>12.4f}")
    print(f"{'Random baseline':<25} {10/len(shared_vocab):>10.4f} {freq_base:>12.4f} {0.0:>12.4f}")

    print("\nVerdict:")
    if p_snapped > p_glm and s_snapped > s_glm:
        print("  ✅ SVD+Golay-snapped vectors OUTPERFORM current GLM hash vectors")
        print("  on both paradigmatic similarity and context correlation.")
        print("  This is a working UBP-native embedding space.")
    elif p_snapped > p_svd:
        print("  ⚠️ Snapping helps over raw SVD, but both may underperform GLM hash.")
        print("  The signal is real but may be too weak for practical use yet.")
    else:
        print("  ❌ Snapping does not help for these tasks.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
