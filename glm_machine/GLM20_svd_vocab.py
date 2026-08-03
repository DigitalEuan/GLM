# ══════════════════════════════════════════════════════════════════════════════
# §20  SVD+GOLAY-SNAPPED VOCABULARY (v3.12.0 NEW MODULE)
# ══════════════════════════════════════════════════════════════════════════════
# Builds distributional 24-bit vectors from the corpus of dictionary
# definitions, snaps them to real Golay codewords, and injects them into
# the GLM vocabulary.
#
# This is the practical realisation of Experiments F, G, and M:
#   - Exp F: SVD/LSA on PPMI co-occurrence produces real distributional signal
#   - Exp G: Snapping to Golay codewords ENHANCES the signal (154.5% retention)
#   - Exp M: The snapped vectors outperform hash vectors on all language tasks
#
# The result: GLM now has a vocabulary where every word's vector is BOTH a
# real Golay codeword AND carries distributional signal from real English text.
# This is the foundation for a non-random language machine within UBP.
#
# Design rules:
#   * Deterministic — same corpus + same SVD → same vectors
#   * Additive — doesn't replace existing vectors, only ENRICHES words that
#     have corpus definitions
#   * KB + physics-pack entries take precedence (their vectors are already
#     grounded in the substrate; we only override hash-derived priority-vocab
#     and master-resource entries that have no real grounding)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import json, re, hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
import numpy as np

from GLM00_config import UBP_CORE_PATH
from GLM01_substrate import (
    WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category,
    vector_to_hex_int,
)

# ── 1. CORPUS BUILDER ────────────────────────────────────────────────────────

def build_corpus() -> Tuple[List[str], Dict[str, str]]:
    """Build a token corpus from the master resource dictionary definitions.

    Returns (tokens, word_definitions).
    """
    path = UBP_CORE_PATH / "glm_master_resource_v1.json"
    if not path.exists():
        return [], {}
    with open(path) as f:
        mr = json.load(f)
    tokens: List[str] = []
    word_defs: Dict[str, str] = {}
    for word, entry in mr.get("vocabulary", {}).items():
        if not isinstance(entry, dict):
            continue
        if " " in word or "-" in word:
            continue
        if len(word) < 3:
            continue
        defn = entry.get("definition", "")
        if not defn or len(defn) < 20:
            continue
        toks = re.findall(r"[a-z]+", defn.lower())
        toks = [t for t in toks if len(t) >= 3]
        tokens.extend(toks)
        word_defs[word.lower()] = defn
    return tokens, word_defs


# ── 2. CO-OCCURRENCE + SVD ───────────────────────────────────────────────────

def build_cooccurrence(corpus: List[str], vocab_list: List[str],
                       window: int = 5, n_context: int = 300) -> np.ndarray:
    """Build a PPMI co-occurrence matrix."""
    vocab_idx = {w: i for i, w in enumerate(vocab_list)}
    freq = Counter(corpus)
    context_words = [w for w, _ in freq.most_common(n_context) if w in vocab_idx]
    context_idx = {w: i for i, w in enumerate(context_words)}

    cooc = np.zeros((len(vocab_list), len(context_words)), dtype=np.float64)
    for i, token in enumerate(corpus):
        if token not in vocab_idx:
            continue
        wi = vocab_idx[token]
        for j in range(max(0, i - window), min(len(corpus), i + window + 1)):
            if j == i:
                continue
            ctx = corpus[j]
            if ctx in context_idx:
                cooc[wi, context_idx[ctx]] += 1
    return cooc


def build_svd_bit_vectors(cooc: np.ndarray, n_dims: int = 24) -> np.ndarray:
    """Build 24-bit vectors via SVD on PPMI matrix, median-quantized."""
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
    return bit_vecs


def snap_to_golay(bit_vecs: np.ndarray) -> Tuple[np.ndarray, int]:
    """Snap each 24-bit vector to the nearest Golay codeword."""
    snapped = []
    n_correctable = 0
    for vec in bit_vecs:
        vec_list = [int(b) for b in vec]
        sn, meta = GOLAY_ENGINE.snap_to_codeword(vec_list)
        snapped.append(sn)
        if meta.get("correctable", True):
            n_correctable += 1
    return np.array(snapped), n_correctable


# ── 3. INJECTION ─────────────────────────────────────────────────────────────

_svd_cache: Optional[Dict[str, List[int]]] = None

def build_svd_vocab() -> Dict[str, List[int]]:
    """Build the SVD+Golay-snapped vocabulary (cached).

    Returns a dict mapping word -> 24-bit snapped vector.
    """
    global _svd_cache
    if _svd_cache is not None:
        return _svd_cache

    print("[GLM20] Building SVD+Golay-snapped vocabulary...")
    corpus, word_defs = build_corpus()
    if not corpus:
        _svd_cache = {}
        return _svd_cache

    # Vocab list = words that have definitions
    vocab_list = sorted(word_defs.keys())
    print(f"  Corpus: {len(corpus)} tokens, {len(vocab_list)} defined words")

    cooc = build_cooccurrence(corpus, vocab_list)
    print(f"  Co-occurrence matrix: {cooc.shape}")

    bit_vecs = build_svd_bit_vectors(cooc)
    print(f"  SVD bit vectors: {bit_vecs.shape}")

    snapped, n_correctable = snap_to_golay(bit_vecs)
    print(f"  Golay-snapped: {n_correctable}/{len(snapped)} correctable "
          f"({n_correctable/len(snapped)*100:.1f}%)")

    _svd_cache = {w: list(snapped[i]) for i, w in enumerate(vocab_list)}
    print(f"  Built {len(_svd_cache)} SVD+Golay-snapped vectors")
    return _svd_cache


def inject_svd_vocab(words: dict) -> dict:
    """Inject SVD+Golay-snapped vectors into a live vocabulary.

    Only overrides words that:
      - Have a definition in the master resource (so we can build their SVD vector)
      - Are currently in the vocab as a priority-vocab or master-resource entry
        (NOT KB-derived or physics-pack entries — those have real grounding)

    Returns a report dict.
    """
    report = {"injected": 0, "skipped_kb": 0, "skipped_physics": 0,
              "skipped_no_svd": 0, "errors": 0}
    svd_vocab = build_svd_vocab()
    if not svd_vocab:
        return report

    for word, svd_vec in svd_vocab.items():
        if word not in words:
            continue  # only enrich words already in vocab
        entry = words[word]
        ubp_id = getattr(entry, 'ubp_id', '')
        # Skip KB-derived entries (they have real grounding)
        if ubp_id.startswith('ELEM_') or ubp_id.startswith('LAW_') or ubp_id.startswith('PARTICLE_') or ubp_id.startswith('MOLECULE_') or ubp_id.startswith('MATH_'):
            report["skipped_kb"] += 1
            continue
        # Skip physics-pack entries (they have definitions)
        if ubp_id.startswith('PVE_'):
            report["skipped_physics"] += 1
            continue
        # Override priority-vocab and master-resource entries
        if ubp_id.startswith('PV_') or ubp_id.startswith('MR_'):
            try:
                nrci = float(LEECH_ENGINE.calculate_nrci(svd_vec))
                # Update the vector in-place
                entry.vector = list(svd_vec)
                entry.nrci = nrci
                entry.golay_codeword = list(svd_vec)
                entry.fold3 = BLA.fold24_to3(svd_vec)
                entry.mog_category = _get_mog_category(svd_vec)
                # Mark as SVD-enriched
                entry.svd_enriched = True  # type: ignore[attr-defined]
                report["injected"] += 1
            except Exception:
                report["errors"] += 1
        else:
            report["skipped_no_svd"] += 1

    return report


# ── 4. STATUS ────────────────────────────────────────────────────────────────

def svd_vocab_status() -> dict:
    """Report SVD vocab status without building it."""
    return {
        "available": UBP_CORE_PATH.exists() and (UBP_CORE_PATH / "glm_master_resource_v1.json").exists(),
        "cached": _svd_cache is not None,
        "cache_size": len(_svd_cache) if _svd_cache else 0,
    }


# ── 5. ISOLATION TEST ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testing Module 20: SVD+Golay-snapped Vocabulary (v3.12.0) ===")
    print()
    print("Status:", svd_vocab_status())
    print()
    svd_vocab = build_svd_vocab()
    if svd_vocab:
        print(f"Total SVD vectors: {len(svd_vocab)}")
        # Show a few examples
        for w in ["energy", "time", "force", "power", "light"]:
            vec = svd_vocab.get(w)
            if vec:
                hex_int = vector_to_hex_int(vec)
                print(f"  {w:15s}: weight={sum(vec):2d}, hex=#{hex_int:06x}")
        print()
        # Test injection
        from GLM01_substrate import _build_vocabulary
        vocab = _build_vocabulary()
        report = inject_svd_vocab(vocab)
        print(f"Injection report: {report}")
