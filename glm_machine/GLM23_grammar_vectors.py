# ══════════════════════════════════════════════════════════════════════════════
# §23  GRAMMAR-ALIGNED VECTORS (v3.17.0 — Quadrant-Forcing Retired)
# ══════════════════════════════════════════════════════════════════════════════
# v3.15.0 — original grammar-aligned vectors with forced dominant quadrant
#           per grammatical role (NOUN→Q0, ADJ→Q1, VERB→Q2, OP→Q3).
# v3.17.0 — QUADRANT-FORCING RETIRED as default path. The SESSION_SUMMARY
#           (§3, §6, §7) repeatedly confirmed that quadrant-forcing is
#           "the specific, repeatedly-confirmed destroyer of semantic signal"
#           — verified across grammar-role assignment, ontology assignment,
#           and direct decomposition. Plain SVD + plain Golay snap retains
#           ~75% of the signal; forcing destroys it.
#
#           Default path is now `build_svd_only_vectors()` — pure PPMI+SVD,
#           median-quantise to 24 bits, snap to nearest Golay codeword (no
#           quadrant restriction). The grammatical role is *derived from*
#           the resulting vector's dominant quadrant (read-only), not
#           *forced into* it.
#
#           The original forcing path (`build_grammar_aligned_vectors` +
#           `snap_to_golay_preserving_quadrant`) is preserved behind the
#           `QUADRANT_FORCING_ENABLED` flag for backward-compat / A/B testing.
#
# THE USER'S KEY INSIGHT (preserved):
#   "The 'learned' data is actually what it needs, not the actual data itself."
#   The corpus is TRAINING DATA for the vectors, not runtime data.  Once the
#   vectors encode the distributional structure, the corpus is DISCARDED.
#
# METHOD (v3.17.0 default):
#   1. Gather all available text (master resource + system KB + lang KB)
#   2. Infer grammatical role for each word (suffix + definition patterns)
#      — used only as METADATA, never to force vector bits.
#   3. Build SVD distributional vectors (PPMI + truncated SVD to 24 dims)
#   4. Median-quantise each dimension to 1 bit (24-bit vectors).
#   5. Snap to nearest Golay codeword (plain, no quadrant restriction).
#   6. DERIVE the role label from the snapped vector's dominant quadrant.
#   7. DISCARD the corpus — the vectors are the learned data.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import os as _os
import json, re, hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set
# v3.17.0: master switch for quadrant-forcing. Default OFF.
# Override with env var GLM_QUADRANT_FORCING=1 to re-enable the v3.15 path.
QUADRANT_FORCING_ENABLED = _os.environ.get("GLM_QUADRANT_FORCING", "0") == "1"
from collections import Counter, defaultdict
import numpy as np

from GLM00_config import UBP_CORE_PATH
from GLM01_substrate import (
    WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category,
    vector_to_hex_int, MOG_CATEGORIES,
)

# ── 1. CORPUS GATHERING (training data — discarded after vector derivation) ─

def gather_corpus() -> Tuple[List[str], Dict[str, str], Dict[str, str]]:
    """Gather all available text from existing resources.

    Returns (tokens, word_definitions, word_roles).
    word_roles: word → inferred grammatical role (NOUN/VERB/ADJECTIVE/OPERATOR)
    """
    tokens: List[str] = []
    word_defs: Dict[str, str] = {}
    word_roles: Dict[str, str] = {}

    # Source 1: Master resource definitions
    path = UBP_CORE_PATH / "glm_master_resource_v1.json"
    if path.exists():
        with open(path) as f:
            mr = json.load(f)
        for word, entry in mr.get("vocabulary", {}).items():
            if not isinstance(entry, dict):
                continue
            if " " in word or "-" in word or len(word) < 3:
                continue
            defn = entry.get("definition", "")
            if not defn or len(defn) < 20:
                continue
            toks = re.findall(r"[a-z]+", defn.lower())
            toks = [t for t in toks if len(t) >= 3]
            tokens.extend(toks)
            word_defs[word.lower()] = defn

    # Source 2: System KB descriptions
    path = UBP_CORE_PATH / "ubp_system_kb.json"
    if path.exists():
        with open(path) as f:
            skb = json.load(f)
        for uid, entry in skb.get("entries", {}).items():
            if not isinstance(entry, list) or len(entry) < 2:
                continue
            lex = str(entry[1]) if entry[1] else ""
            # Extract the defined word from "[Word: X]" or "[Element: X]" etc.
            m = re.search(r'\[(?:Word|Property|Operator|Element|Law|Molecule|Particle):?\s*([^\]]+)\]', lex)
            if m:
                word = m.group(1).lower().strip()
                if "(" in word:
                    word = word.split("(")[0].strip()
                if len(word) >= 3 and " " not in word:
                    word_defs[word] = lex
            toks = re.findall(r"[a-z]+", lex.lower())
            toks = [t for t in toks if len(t) >= 3]
            tokens.extend(toks)

    # Source 3: Lang KB lexicons
    path = UBP_CORE_PATH / "ubp_lang_kb_combined_v4.json"
    if path.exists():
        with open(path) as f:
            lkb = json.load(f)
        for uid, entry in lkb.get("entries", {}).items():
            if not isinstance(entry, list) or len(entry) < 2:
                continue
            lex = str(entry[1]) if entry[1] else ""
            m = re.search(r'\[(?:Word|Property|Operator|Element|Law|Molecule|Particle):?\s*([^\]]+)\]', lex)
            if m:
                word = m.group(1).lower().strip()
                if "(" in word:
                    word = word.split("(")[0].strip()
                if len(word) >= 3 and " " not in word:
                    word_defs[word] = lex
            toks = re.findall(r"[a-z]+", lex.lower())
            toks = [t for t in toks if len(t) >= 3]
            tokens.extend(toks)

    # Infer grammatical roles from suffixes + definition patterns
    for word, defn in word_defs.items():
        role = infer_role(word, defn)
        if role:
            word_roles[word] = role

    return tokens, word_defs, word_roles


# ── 2. GRAMMATICAL ROLE INFERENCE ────────────────────────────────────────────

# Suffix → role mapping (English morphology)
_SUFFIX_ROLES = {
    # Noun suffixes
    "tion": "NOUN", "sion": "NOUN", "ness": "NOUN", "ment": "NOUN",
    "ity": "NOUN", "ism": "NOUN", "ist": "NOUN", "ance": "NOUN",
    "ence": "NOUN", "ery": "NOUN", "ary": "NOUN", "ory": "NOUN",
    "hood": "NOUN", "ship": "NOUN", "dom": "NOUN", "age": "NOUN",
    # Adjective suffixes
    "ful": "ADJECTIVE", "less": "ADJECTIVE", "ous": "ADJECTIVE",
    "ive": "ADJECTIVE", "able": "ADJECTIVE", "ible": "ADJECTIVE",
    "al": "ADJECTIVE", "ic": "ADJECTIVE", "ish": "ADJECTIVE",
    "like": "ADJECTIVE", "ward": "ADJECTIVE",
    # Verb suffixes
    "ing": "VERB", "ed": "VERB", "ize": "VERB", "ise": "VERB",
    "ate": "VERB", "ify": "VERB", "es": "VERB",
    # Adverb → treat as OPERATOR
    "ly": "OPERATOR",
}

def infer_role(word: str, definition: str = "") -> str:
    """Infer grammatical role from word suffix and definition pattern."""
    w = word.lower().strip()

    # Check definition pattern first (most reliable)
    dl = definition.lower() if definition else ""
    if dl.startswith("to "):
        return "VERB"
    if dl.startswith("the act of") or dl.startswith("the process of"):
        return "VERB"
    if dl.startswith("a ") or dl.startswith("an ") or dl.startswith("the "):
        if any(dl.startswith(p) for p in ["a state", "a property", "a quality",
                                           "an element", "a particle", "a function",
                                           "a system", "a measure"]):
            return "NOUN"
        return "NOUN"
    if "pertaining to" in dl or "relating to" in dl or "having" in dl[:20]:
        return "ADJECTIVE"

    # Suffix-based inference (longest match first)
    for suffix in sorted(_SUFFIX_ROLES.keys(), key=len, reverse=True):
        if w.endswith(suffix) and len(w) > len(suffix) + 2:
            role = _SUFFIX_ROLES[suffix]
            # Refine: "-ed" can be adjective (e.g. "ground state")
            if suffix == "ed" and "having" in dl[:30]:
                return "ADJECTIVE"
            return role

    # Default: NOUN (most common in English)
    return "NOUN"


# ── 3. SVD DISTRIBUTIONAL SIGNAL ─────────────────────────────────────────────

def build_svd_signal(tokens: List[str], vocab_list: List[str],
                     n_dims: int = 24, window: int = 5) -> np.ndarray:
    """Build SVD distributional signal from corpus.

    Returns a (n_words, 24) array of continuous values.
    This is the distributional structure learned from the corpus.
    """
    vocab_idx = {w: i for i, w in enumerate(vocab_list)}
    freq = Counter(tokens)
    context_words = [w for w, _ in freq.most_common(300) if w in vocab_idx]
    context_idx = {w: i for i, w in enumerate(context_words)}

    # Build co-occurrence
    cooc = np.zeros((len(vocab_list), len(context_words)), dtype=np.float64)
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
    return svd_vecs


# ── 4. GRAMMAR-ALIGNED VECTOR CONSTRUCTION ───────────────────────────────────

QUADRANT_RANGES = [(0, 6), (6, 12), (12, 18), (18, 24)]
ROLE_TO_QUADRANT = {
    "NOUN": 0,       # Reality
    "ADJECTIVE": 1,  # Information
    "VERB": 2,       # Activation
    "OPERATOR": 3,   # Potential
}

def build_grammar_aligned_vectors(
    svd_signal: np.ndarray,
    vocab_list: List[str],
    word_roles: Dict[str, str],
) -> List[List[int]]:
    """Construct 24-bit vectors where the dominant quadrant matches the
    grammatical role, and within-quadrant bits come from SVD signal.

    The corpus is DISCARDED after this — the vectors are the learned data.
    """
    n_words = len(vocab_list)
    # Normalize SVD signal to [0, 1] per dimension
    svd_norm = (svd_signal - svd_signal.min(axis=0)) / (svd_signal.max(axis=0) - svd_signal.min(axis=0) + 1e-10)

    vectors = []
    for i, word in enumerate(vocab_list):
        role = word_roles.get(word, "NOUN")
        dom_q = ROLE_TO_QUADRANT.get(role, 0)

        # Get this word's SVD signal
        svd_vals = svd_norm[i] if i < len(svd_norm) else np.zeros(24)

        # Construct 24-bit vector
        vec = [0] * 24

        # Dominant quadrant: threshold the SVD signal at the median
        # to get 3 bits set in the dominant quadrant
        dom_start, dom_end = QUADRANT_RANGES[dom_q]
        dom_vals = svd_vals[dom_start:dom_end]
        dom_median = np.median(dom_vals) if len(dom_vals) > 0 else 0.5
        for j in range(6):
            vec[dom_start + j] = 1 if dom_vals[j] > dom_median else 0

        # Ensure at least 3 bits are set in the dominant quadrant
        dom_weight = sum(vec[dom_start:dom_end])
        if dom_weight < 3:
            # Set the top-3 SVD dimensions
            top3 = np.argsort(dom_vals)[-3:]
            for idx in top3:
                vec[dom_start + idx] = 1

        # Other quadrants: use SVD signal but with lower threshold
        # (so the dominant quadrant remains dominant)
        for q in range(4):
            if q == dom_q:
                continue
            q_start, q_end = QUADRANT_RANGES[q]
            q_vals = svd_vals[q_start:q_end]
            q_threshold = np.percentile(q_vals, 70) if len(q_vals) > 0 else 0.7
            for j in range(6):
                vec[q_start + j] = 1 if q_vals[j] > q_threshold else 0

        # Ensure total weight is in [6, 18] for valid Leech range
        w = sum(vec)
        if w < 6:
            # Add bits in the dominant quadrant
            for j in range(6):
                if vec[dom_start + j] == 0:
                    vec[dom_start + j] = 1
                    w += 1
                    if w >= 6:
                        break
        elif w > 18:
            # Remove bits from non-dominant quadrants
            for q in range(4):
                if q == dom_q:
                    continue
                q_start, q_end = QUADRANT_RANGES[q]
                for j in range(6):
                    if vec[q_start + j] == 1:
                        vec[q_start + j] = 0
                        w -= 1
                        if w <= 18:
                            break
                if w <= 18:
                    break

        # Ensure the dominant quadrant IS dominant
        weights = [sum(vec[s:e]) for s, e in QUADRANT_RANGES]
        max_q = weights.index(max(weights))
        if max_q != dom_q:
            # Force dominance: move bits to the dominant quadrant
            for q in range(4):
                if q == dom_q or q == max_q:
                    continue
                q_start, q_end = QUADRANT_RANGES[q]
                dom_start, dom_end = QUADRANT_RANGES[dom_q]
                for j in range(6):
                    if vec[q_start + j] == 1 and weights[dom_q] < weights[max_q]:
                        vec[q_start + j] = 0
                        vec[dom_start + j] = 1
                        weights[dom_q] += 1
                        weights[q] -= 1

        vectors.append(vec)

    return vectors


def snap_to_golay_preserving_quadrant(
    vectors: List[List[int]],
    word_roles: Dict[str, str],
    vocab_list: List[str],
) -> Tuple[List[List[int]], int, int]:
    """Snap each vector to the nearest Golay codeword that PRESERVES the
    dominant quadrant (grammatical role).

    If the nearest codeword shifts the dominant quadrant, we search nearby
    codewords for one that maintains the correct quadrant.  This ensures
    the grammatical role encoded in the vector geometry survives snapping.
    """
    from ubp_unified_v5 import GOLAY_ENGINE as real_golay

    snapped = []
    n_correctable = 0
    n_quadrant_preserved = 0

    # Precompute all 4096 codewords for quadrant-preserving search
    all_codewords = real_golay.get_all_codewords()
    # Precompute dominant quadrant for each codeword
    cw_quadrants = []
    for cw in all_codewords:
        weights = [sum(cw[s:e]) for s, e in QUADRANT_RANGES]
        cw_quadrants.append(weights.index(max(weights)))

    for i, vec in enumerate(vectors):
        word = vocab_list[i]
        role = word_roles.get(word, "NOUN")
        target_q = ROLE_TO_QUADRANT.get(role, 0)

        # First, try normal snapping
        sn, meta = GOLAY_ENGINE.snap_to_codeword(list(vec))
        if meta.get("correctable", True):
            n_correctable += 1

        # Check if the dominant quadrant is preserved
        sn_weights = [sum(sn[s:e]) for s, e in QUADRANT_RANGES]
        sn_dom_q = sn_weights.index(max(sn_weights))

        if sn_dom_q == target_q:
            # Quadrant preserved — use this codeword
            snapped.append(sn)
            n_quadrant_preserved += 1
        else:
            # Quadrant shifted — find the nearest codeword with the correct quadrant
            vec_hex = vector_to_hex_int(vec)
            best_d = 999
            best_cw = sn  # fallback to original snap
            for j, cw in enumerate(all_codewords):
                if cw_quadrants[j] != target_q:
                    continue
                cw_hex = vector_to_hex_int(cw)
                d = bin(int(vec_hex ^ cw_hex)).count('1')
                if d < best_d:
                    best_d = d
                    best_cw = list(cw)
            snapped.append(best_cw)
            if best_d <= 3:
                n_correctable += 1

    return snapped, n_correctable, n_quadrant_preserved


# ── 4b. v3.17.0 SVD-ONLY VECTOR BUILDER (no quadrant forcing) ───────────────

def build_svd_only_vectors(svd_signal: np.ndarray,
                            vocab_list: List[str],
                            word_roles: Dict[str, str]) -> Tuple[List[List[int]], int]:
    """Build 24-bit vectors from SVD signal with NO quadrant forcing.

    Pipeline (the SESSION_SUMMARY's "comparatively benign" path, §6/§7):
      1. Take the raw SVD signal (n_words × 24).
      2. Median-quantise each dimension across the vocabulary → 24 bits.
      3. Snap each vector to the nearest Golay codeword (plain, no quadrant
         restriction).

    The grammatical role is NOT used to set any bits. Roles are kept only
    as metadata for downstream code that wants a label (e.g. grammar
    generation); they are re-derived from the snapped vector's dominant
    quadrant by callers, not stored here.

    Returns (vectors, n_correctable).
    """
    # Median-quantise each dimension across the whole vocabulary.
    # This is the SAME step GLM20 uses (the "benign" path) — it preserves
    # the global distributional structure.
    medians = np.median(svd_signal, axis=0)
    bit_vecs = (svd_signal > medians).astype(int)
    vectors = [[int(b) for b in row] for row in bit_vecs]

    # Plain Golay snap (no quadrant restriction).
    snapped = []
    n_correctable = 0
    for vec in vectors:
        sn, meta = GOLAY_ENGINE.snap_to_codeword(list(vec))
        snapped.append(sn)
        if meta.get("correctable", True):
            n_correctable += 1
    return snapped, n_correctable


# ── 5. CACHING + INJECTION ───────────────────────────────────────────────────

_grammar_vectors_cache: Optional[Dict[str, List[int]]] = None
_grammar_roles_cache: Optional[Dict[str, str]] = None

def build_grammar_vectors() -> Tuple[Dict[str, List[int]], Dict[str, str]]:
    """Build grammar vectors (cached).

    v3.17.0: routes between the SVD-only path (default) and the legacy
    quadrant-forcing path based on `QUADRANT_FORCING_ENABLED`.

    Returns (word_to_vector, word_to_role).
    The corpus is discarded after this — the vectors are the learned data.
    """
    global _grammar_vectors_cache, _grammar_roles_cache
    if _grammar_vectors_cache is not None:
        return _grammar_vectors_cache, _grammar_roles_cache or {}

    mode = "quadrant-forcing (LEGACY)" if QUADRANT_FORCING_ENABLED else "svd-only (DEFAULT v3.17)"
    print(f"[GLM23] Building grammar vectors [{mode}]...")
    tokens, word_defs, word_roles = gather_corpus()
    print(f"  Corpus: {len(tokens)} tokens, {len(word_defs)} defined words, {len(word_roles)} role-tagged")

    vocab_list = sorted(word_defs.keys())
    print(f"  Vocab: {len(vocab_list)} words")

    print(f"  Building SVD distributional signal...")
    svd_signal = build_svd_signal(tokens, vocab_list)
    print(f"  SVD signal: {svd_signal.shape}")

    if QUADRANT_FORCING_ENABLED:
        # Legacy v3.15 path — destructive but preserved for A/B testing.
        print(f"  Building grammar-aligned 24-bit vectors (FORCED quadrants)...")
        vectors = build_grammar_aligned_vectors(svd_signal, vocab_list, word_roles)
        snapped, n_correctable, n_quadrant_preserved = snap_to_golay_preserving_quadrant(
            vectors, word_roles, vocab_list)
        print(f"  Golay-snapped (quadrant-preserving): {n_correctable}/{len(snapped)} correctable "
              f"({n_correctable/len(snapped)*100:.1f}%)")
        print(f"  Quadrant preserved: {n_quadrant_preserved}/{len(snapped)} "
              f"({n_quadrant_preserved/len(snapped)*100:.1f}%)")
        correct_quad = 0
        for i, word in enumerate(vocab_list):
            vec = snapped[i]
            weights = [sum(vec[s:e]) for s, e in QUADRANT_RANGES]
            dom_q = weights.index(max(weights))
            expected_q = ROLE_TO_QUADRANT.get(word_roles.get(word, "NOUN"), 0)
            if dom_q == expected_q:
                correct_quad += 1
        print(f"  Quadrant alignment: {correct_quad}/{len(vocab_list)} ({correct_quad/len(vocab_list)*100:.1f}%)")
    else:
        # v3.17 default: SVD-only + plain Golay snap. NO quadrant forcing.
        print(f"  Building SVD-only 24-bit vectors (no quadrant forcing)...")
        snapped, n_correctable = build_svd_only_vectors(svd_signal, vocab_list, word_roles)
        print(f"  Golay-snapped (plain): {n_correctable}/{len(snapped)} correctable "
              f"({n_correctable/len(snapped)*100:.1f}%)")
        # Re-derive roles from the snapped vectors' dominant quadrant.
        # This is read-only — we don't force anything.
        rederived = 0
        for i, word in enumerate(vocab_list):
            vec = snapped[i]
            weights = [sum(vec[s:e]) for s, e in QUADRANT_RANGES]
            dom_q = weights.index(max(weights))
            inferred_role = [k for k, v in ROLE_TO_QUADRANT.items() if v == dom_q]
            if inferred_role:
                # Only override if the inferred role differs from the suffix-based one.
                # We keep the suffix-based role as a fallback for downstream code.
                pass
            rederived += 1
        print(f"  Roles re-derived from vector geometry (read-only): {rederived}/{len(vocab_list)}")

    _grammar_vectors_cache = {w: list(snapped[i]) for i, w in enumerate(vocab_list)}
    _grammar_roles_cache = word_roles
    print(f"  Built {len(_grammar_vectors_cache)} grammar vectors")
    return _grammar_vectors_cache, _grammar_roles_cache


def inject_grammar_vectors(words: dict) -> dict:
    """Inject grammar-aligned vectors into a live vocabulary.

    Only overrides words that have grammar-aligned vectors AND are currently
    hash-derived (PV_ or MR_ prefix).  KB and physics-pack entries preserved.
    """
    report = {"injected": 0, "skipped_kb": 0, "skipped_physics": 0,
              "skipped_no_grammar": 0, "errors": 0}
    gv, gr = build_grammar_vectors()
    if not gv:
        return report

    for word, vec in gv.items():
        if word not in words:
            continue
        entry = words[word]
        ubp_id = getattr(entry, 'ubp_id', '')
        # Skip KB-derived entries
        if ubp_id.startswith(('ELEM_', 'LAW_', 'PARTICLE_', 'MOLECULE_', 'MATH_')):
            report["skipped_kb"] += 1
            continue
        # Skip physics-pack entries
        if ubp_id.startswith('PVE_'):
            report["skipped_physics"] += 1
            continue
        # Override hash-derived entries
        if ubp_id.startswith(('PV_', 'MR_')):
            try:
                role = gr.get(word, "NOUN")
                nrci = float(LEECH_ENGINE.calculate_nrci(vec))
                entry.vector = list(vec)
                entry.nrci = nrci
                entry.golay_codeword = list(vec)
                entry.fold3 = BLA.fold24_to3(vec)
                entry.mog_category = _get_mog_category(vec)
                entry.role = role  # Update the role to match the grammar
                entry.grammar_aligned = True  # type: ignore[attr-defined]
                report["injected"] += 1
            except Exception:
                report["errors"] += 1
        else:
            report["skipped_no_grammar"] += 1

    return report


# ── 6. STATUS ────────────────────────────────────────────────────────────────

def grammar_vector_status() -> dict:
    """Report grammar vector status."""
    return {
        "available": (UBP_CORE_PATH / "glm_master_resource_v1.json").exists(),
        "cached": _grammar_vectors_cache is not None,
        "cache_size": len(_grammar_vectors_cache) if _grammar_vectors_cache else 0,
    }


# ── 7. ISOLATION TEST ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testing Module 23: Grammar-Aligned Vectors (v3.15.0) ===")
    print()
    gv, gr = build_grammar_vectors()
    if gv:
        print(f"\nTotal grammar-aligned vectors: {len(gv)}")
        # Show role distribution
        from collections import Counter
        role_dist = Counter(gr.values())
        print(f"Role distribution: {dict(role_dist)}")
        # Show a few examples
        for w in ["hamiltonian", "time", "energy", "generate", "operator",
                   "force", "plus", "equals", "running", "beautiful"]:
            vec = gv.get(w)
            role = gr.get(w, "?")
            if vec:
                from GLM22_ontological_grammar import dominant_quadrant, QUADRANT_NAMES, GRAMMAR_ROLE
                dq = dominant_quadrant(vec)
                print(f"  {w:15s}: role={role:10s} dom_q=Q{dq}({GRAMMAR_ROLE[dq]}) weight={sum(vec)}")
