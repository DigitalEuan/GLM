# ══════════════════════════════════════════════════════════════════════════════
# §24  CONTINUOUS LEARNER (v3.16.0 NEW)
# ══════════════════════════════════════════════════════════════════════════════
# The user's vision: "learned vectors would be added to and reorganized as a
# chat/test is run — a continuous learning and improving loop."
#
# This module implements continuous learning WITHIN the GLM substrate —
# NOT a bolted-on ML model.  The vectors ARE the learned data, and they
# improve as the system processes more queries.
#
# HOW IT WORKS (all within the substrate, no external ML):
#
#   1. CO-OCCURRENCE UPDATE: When two words appear in the same query,
#      their co-occurrence count increases.  This is stored as a
#      lightweight in-memory matrix (not the full corpus).
#
#   2. VECTOR REFINEMENT: When a word's co-occurrence profile changes
#      significantly, its 24-bit vector is refined by:
#        a. Computing the new SVD signal from the updated co-occurrence
#        b. Re-snapping to the nearest Golay codeword that preserves
#           the grammatical quadrant
#        c. Updating the vocab entry in-place
#
#   3. NEW WORD LEARNING: When a query contains a word not in the vocab,
#      the learner:
#        a. Infers its grammatical role from suffix + context
#        b. Derives a vector from its co-occurrence with known words
#        c. Snaps to a Golay codeword (quadrant-preserving)
#        d. Adds it to the vocab
#
#   4. CRG EDGE LEARNING: When two words co-occur frequently, a new
#      CRG edge is proposed (label = "co_occurs").  If the edge already
#      exists, its weight is reinforced.
#
#   5. PERSISTENCE: The learned vectors + co-occurrence matrix are saved
#      to disk (glm_learned_state.json) so learning persists across sessions.
#
# DESIGN PRINCIPLE: This is NOT a neural network.  There are no weights,
# no gradients, no backpropagation.  The "learning" is geometric: vectors
# move on the 24-bit lattice as co-occurrence statistics accumulate.
# The Golay code's error-correction structure ensures vectors stay on
# the lattice manifold.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import json, re, hashlib, os
import atexit
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import numpy as np

from GLM00_config import UBP_CORE_PATH
from GLM01_substrate import (
    WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category,
    vector_to_hex_int, MOG_CATEGORIES,
)
from GLM22_ontological_grammar import dominant_quadrant, QUADRANT_RANGES, GRAMMAR_ROLE
from GLM23_grammar_vectors import (
    ROLE_TO_QUADRANT, infer_role, snap_to_golay_preserving_quadrant,
    QUADRANT_FORCING_ENABLED,
)

# ── 1. LEARNED STATE ─────────────────────────────────────────────────────────

LEARNED_STATE_PATH = Path("glm_learned_state.json")

@dataclass
class LearnedState:
    """Persistent state for continuous learning."""
    # Co-occurrence counts: word_a → word_b → count
    cooccurrence: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    # New words learned (not in original vocab)
    learned_words: Dict[str, Dict] = field(default_factory=dict)  # word → {vector, role, nrci}
    # CRG edges learned
    learned_edges: List[Tuple[str, str, str]] = field(default_factory=list)  # (src, label, dst)
    # Query count (how many queries processed)
    query_count: int = 0
    # Vectors refined (how many times vectors were updated)
    vectors_refined: int = 0

    def to_dict(self) -> dict:
        return {
            "cooccurrence": {k: dict(v) for k, v in self.cooccurrence.items()},
            "learned_words": self.learned_words,
            "learned_edges": self.learned_edges,
            "query_count": self.query_count,
            "vectors_refined": self.vectors_refined,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LearnedState":
        state = cls()
        state.cooccurrence = defaultdict(lambda: defaultdict(int))
        for k, v in d.get("cooccurrence", {}).items():
            state.cooccurrence[k] = defaultdict(int, v)
        state.learned_words = d.get("learned_words", {})
        state.learned_edges = [tuple(e) for e in d.get("learned_edges", [])]
        state.query_count = d.get("query_count", 0)
        state.vectors_refined = d.get("vectors_refined", 0)
        return state

    def save(self, path: Path = LEARNED_STATE_PATH):
        try:
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"[GLM24] Warning: could not save learned state: {e}")

    @classmethod
    def load(cls, path: Path = LEARNED_STATE_PATH) -> "LearnedState":
        if not path.exists():
            return cls()
        try:
            with open(path) as f:
                return cls.from_dict(json.load(f))
        except Exception:
            return cls()


# ── 2. THE CONTINUOUS LEARNER ────────────────────────────────────────────────

class ContinuousLearner:
    """Learns and refines vectors as the system processes queries.

    All learning is WITHIN the GLM substrate — no external ML model.
    """

    def __init__(self, vocab: Any, crg: Any):
        self.vocab = vocab
        self.crg = crg
        self.state = LearnedState.load()
        # Co-occurrence threshold for edge creation
        self.edge_threshold = 3  # words must co-occur 3 times before an edge is added
        # Refinement threshold (refine when co-occurrence changes by this much)
        self.refine_threshold = 5
        # Load learned words into vocab
        self._load_learned_words()
        # v3.17.0 BUG FIX (b): re-apply learned CRG edges to the live graph.
        # Previously these were saved to disk but never re-added on reload —
        # the same bug class as the already-patched vectors-counter issue.
        self._load_learned_edges()
        # v3.17.0 BUG FIX (c): register an atexit handler so the state is
        # flushed even if the process exits between periodic saves. The
        # original code only saved at `query_count % 5 == 0`, silently
        # losing up to 4 queries of real learning per session.
        atexit.register(self._atexit_flush)

    def _atexit_flush(self):
        """Flush learned state on interpreter exit (v3.17.0 bug c fix)."""
        try:
            self.state.save()
        except Exception:
            pass

    def _load_learned_edges(self):
        """v3.17.0 BUG FIX (b): re-apply learned CRG edges on reload.

        Previously `learned_edges` were saved to disk but never re-added to
        the live CRG graph after a restart, so they accumulated as dead data.
        This method iterates the persisted edges and calls `crg.add_edge`
        for each, skipping any that already exist.

        v3.17.0 also fixes a deeper issue: the original `_check_for_new_edges`
        called `crg.add_edge(..., "co_occurs", ...)` but `co_occurs` was not
        in `EDGE_LABELS`, so the call silently returned False. The fix is in
        GLM01_substrate (added "co_occurs" to EDGE_LABELS). We additionally
        check the return value here so we don't count a "added" edge that
        was actually rejected.
        """
        added = 0
        for src, label, dst in self.state.learned_edges:
            # ConceptRelationGraph.add_edge lowercases keys, so use lowercase
            # for the existence check too.
            src_l, dst_l = src.lower().strip(), dst.lower().strip()
            existing = any(e.dst == dst_l and e.label == label
                           for e in self.crg.out.get(src_l, []))
            if not existing:
                try:
                    ok = self.crg.add_edge(src, label, dst)
                    if ok:
                        added += 1
                except Exception:
                    pass
        if added > 0:
            print(f"[GLM24] Re-applied {added} learned CRG edges from saved state")

    def _load_learned_words(self):
        """Load previously-learned words into the vocab."""
        target = self.vocab.words if hasattr(self.vocab, 'words') else self.vocab
        for word, data in self.state.learned_words.items():
            if word not in target:
                vec = data.get("vector", [])
                role = data.get("role", "NOUN")
                if vec and len(vec) == 24:
                    target[word] = WordEntry(
                        word=word, vector=list(vec), role=role,
                        ubp_id=f"LEARNED_{word}",
                        nrci=float(LEECH_ENGINE.calculate_nrci(vec)),
                        golay_codeword=list(vec),
                        fold3=BLA.fold24_to3(vec),
                        mog_category=_get_mog_category(vec),
                    )

    def process_query(self, query: str, content_words: List[str]):
        """Process a query and update the learned state.

        Args:
            query: the raw query string
            content_words: the content words extracted from the query
                          (already filtered for function words)
        """
        self.state.query_count += 1

        # 1. Update co-occurrence counts
        for i, w1 in enumerate(content_words):
            for w2 in content_words[i+1:]:
                if w1 != w2:
                    self.state.cooccurrence[w1][w2] += 1
                    self.state.cooccurrence[w2][w1] += 1

        # 2. Learn new words (words in query not in vocab)
        target = self.vocab.words if hasattr(self.vocab, 'words') else self.vocab
        for word in content_words:
            if word not in target and word not in self.state.learned_words:
                self._learn_new_word(word, content_words)

        # 3. Check if any vectors need refinement
        if self.state.query_count % 10 == 0:  # refine every 10 queries
            self._refine_vectors()

        # 4. Check for new CRG edges
        self._check_for_new_edges(content_words)

        # 5. Save state periodically
        if self.state.query_count % 5 == 0:
            self.state.save()
        # v3.17.0 BUG FIX (c): also flush after a refinement pass actually
        # changed vectors — don't wait for the next 5-query boundary.

    def _learn_new_word(self, word: str, context_words: List[str]):
        """Learn a new word by deriving its vector from co-occurrence.

        v3.17.0: quadrant-forcing is now opt-in via QUADRANT_FORCING_ENABLED.
        When disabled (the default), the vector is derived purely from the
        average of context-word vectors, median-thresholded, and snapped to
        the nearest Golay codeword with NO quadrant restriction. This is
        the "comparatively benign" path that retains ~75% of the signal.
        """
        # Infer grammatical role from suffix (kept as metadata only)
        role = infer_role(word, "")

        # Find co-occurring known words
        target = self.vocab.words if hasattr(self.vocab, 'words') else self.vocab
        known_context = [w for w in context_words if w in target and w != word]
        if not known_context:
            return  # can't learn without context

        # Derive a vector: average the vectors of co-occurring known words,
        # then threshold to 24 bits
        vec_sum = [0.0] * 24
        count = 0
        for w in known_context[:5]:  # use up to 5 context words
            entry = target[w]
            if hasattr(entry, 'vector') and entry.vector:
                for i, b in enumerate(entry.vector):
                    vec_sum[i] += b
                count += 1

        if count == 0:
            return

        # Average and threshold
        avg_vec = [s / count for s in vec_sum]
        median = sorted(avg_vec)[12]  # median threshold
        bit_vec = [1 if v > median else 0 for v in avg_vec]

        if QUADRANT_FORCING_ENABLED:
            # Legacy v3.15 path — force dominant quadrant to match role.
            target_q = ROLE_TO_QUADRANT.get(role, 0)
            q_start, q_end = QUADRANT_RANGES[target_q]
            q_vals = avg_vec[q_start:q_end]
            top3 = sorted(range(6), key=lambda i: q_vals[i], reverse=True)[:3]
            for i in range(6):
                bit_vec[q_start + i] = 1 if i in top3 else 0
            # Ensure weight in [6, 18]
            w = sum(bit_vec)
            if w < 6:
                for i in range(6):
                    if bit_vec[q_start + i] == 0:
                        bit_vec[q_start + i] = 1
                        w += 1
                        if w >= 6:
                            break

        # Snap to Golay codeword. v3.17.0: plain snap by default (no
        # quadrant restriction). Legacy path uses the quadrant-preserving
        # search when forcing is enabled.
        if QUADRANT_FORCING_ENABLED:
            target_q = ROLE_TO_QUADRANT.get(role, 0)
            snapped, meta = GOLAY_ENGINE.snap_to_codeword(bit_vec)
            if dominant_quadrant(snapped) != target_q:
                from ubp_unified_v5 import GOLAY_ENGINE as real_golay
                all_cws = real_golay.get_all_codewords()
                vec_hex = vector_to_hex_int(bit_vec)
                best_d, best_cw = 999, snapped
                for cw in all_cws:
                    cw_weights = [sum(cw[s:e]) for s, e in QUADRANT_RANGES]
                    if cw_weights.index(max(cw_weights)) != target_q:
                        continue
                    cw_hex = vector_to_hex_int(cw)
                    d = bin(int(vec_hex ^ cw_hex)).count('1')
                    if d < best_d:
                        best_d = d
                        best_cw = list(cw)
                snapped = best_cw
        else:
            # v3.17 default: plain snap, no quadrant restriction.
            snapped, meta = GOLAY_ENGINE.snap_to_codeword(bit_vec)

        # Add to vocab
        nrci = float(LEECH_ENGINE.calculate_nrci(snapped))
        target[word] = WordEntry(
            word=word, vector=snapped, role=role,
            ubp_id=f"LEARNED_{word}",
            nrci=nrci,
            golay_codeword=snapped,
            fold3=BLA.fold24_to3(snapped),
            mog_category=_get_mog_category(snapped),
        )

        # Record in learned state
        self.state.learned_words[word] = {
            "vector": snapped,
            "role": role,
            "nrci": nrci,
            "learned_at_query": self.state.query_count,
        }
        self.state.vectors_refined += 1

    def _refine_vectors(self):
        """Refine vectors based on accumulated co-occurrence data.

        For each word with significant co-occurrence changes, recompute
        its vector using the updated co-occurrence profile.

        v3.17.0 changes:
          - BUG (a) FIX: the prefix-skip was excluding every word with an
            ELEM_/LAW_/PARTICLE_/MOLECULE_/MATH_/PVE_ prefix from refinement.
            The intent was to protect hand-curated KB entries, but the proxy
            was too broad — it also froze priority-vocab and master-resource
            words that DO need refinement. Now we only skip words whose
            vector is already a *valid Golay codeword* AND was hand-curated
            (i.e. has `golay_codeword` set and matches its `vector`). Words
            whose vector equals their golay_codeword are immutable by design.
          - Quadrant-forcing is now opt-in via QUADRANT_FORCING_ENABLED.
          - BUG (c) FIX: state is now saved after refinement if any vectors
            changed, not just on the 5-query boundary.
        """
        target = self.vocab.words if hasattr(self.vocab, 'words') else self.vocab
        refined = 0

        for word, partners in list(self.state.cooccurrence.items()):
            if word not in target:
                continue
            total_cooc = sum(partners.values())
            if total_cooc < self.refine_threshold:
                continue

            entry = target[word]
            if not hasattr(entry, 'vector') or not entry.vector:
                continue

            # v3.17.0 BUG (a) FIX: replace the broad prefix-skip with a
            # precise check. We only skip words that are (1) hand-curated
            # AND (2) whose vector is already a valid Golay codeword.
            # Hand-curated = ubp_id starts with one of the protected prefixes
            # AND the entry's golay_codeword field is non-empty and equal
            # to its current vector.
            ubp_id = getattr(entry, 'ubp_id', '')
            is_protected_prefix = ubp_id.startswith(
                ('ELEM_', 'LAW_', 'PARTICLE_', 'MOLECULE_', 'MATH_'))
            gc = getattr(entry, 'golay_codeword', [])
            is_hand_curated_codeword = (
                is_protected_prefix and
                bool(gc) and
                list(gc) == list(entry.vector)
            )
            if is_hand_curated_codeword:
                continue
            # Physics-pack entries (PVE_) are no longer blanket-skipped —
                # they CAN be refined if their co-occurrence profile shifts.
                # Only the truly hand-curated codewords (above) are frozen.

            # Recompute vector: blend current vector with co-occurrence partners
            current_vec = list(entry.vector)
            partner_vecs = []
            for partner, count in partners.items():
                p_entry = target.get(partner)
                if p_entry and hasattr(p_entry, 'vector') and p_entry.vector:
                    # Weight by co-occurrence count
                    for _ in range(count):
                        partner_vecs.append(list(p_entry.vector))

            if not partner_vecs:
                continue

            # Average current + partners
            all_vecs = [current_vec] + partner_vecs
            avg = [sum(v[i] for v in all_vecs) / len(all_vecs) for i in range(24)]
            median = sorted(avg)[12]
            new_vec = [1 if v > median else 0 for v in avg]

            if QUADRANT_FORCING_ENABLED:
                # Legacy v3.15 path — preserve grammatical quadrant.
                role = getattr(entry, 'role', 'NOUN')
                target_q = ROLE_TO_QUADRANT.get(role, 0)
                q_start, q_end = QUADRANT_RANGES[target_q]
                q_vals = avg[q_start:q_end]
                top3 = sorted(range(6), key=lambda i: q_vals[i], reverse=True)[:3]
                for i in range(6):
                    new_vec[q_start + i] = 1 if i in top3 else 0
                # Ensure weight
                w = sum(new_vec)
                if w < 6:
                    for i in range(6):
                        if new_vec[q_start + i] == 0:
                            new_vec[q_start + i] = 1
                            w += 1
                            if w >= 6:
                                break
                elif w > 18:
                    for q in range(4):
                        if q == target_q:
                            continue
                        qs, qe = QUADRANT_RANGES[q]
                        for i in range(6):
                            if new_vec[qs + i] == 1:
                                new_vec[qs + i] = 0
                                w -= 1
                                if w <= 18:
                                    break
                        if w <= 18:
                            break
                # Snap to Golay codeword (quadrant-preserving)
                snapped, meta = GOLAY_ENGINE.snap_to_codeword(new_vec)
                if dominant_quadrant(snapped) != target_q:
                    from ubp_unified_v5 import GOLAY_ENGINE as real_golay
                    all_cws = real_golay.get_all_codewords()
                    vec_hex = vector_to_hex_int(new_vec)
                    best_d, best_cw = 999, snapped
                    for cw in all_cws:
                        cw_weights = [sum(cw[s:e]) for s, e in QUADRANT_RANGES]
                        if cw_weights.index(max(cw_weights)) != target_q:
                            continue
                        cw_hex = vector_to_hex_int(cw)
                        d = bin(int(vec_hex ^ cw_hex)).count('1')
                        if d < best_d:
                            best_d = d
                            best_cw = list(cw)
                    snapped = best_cw
            else:
                # v3.17 default: plain Golay snap, no quadrant restriction.
                snapped, meta = GOLAY_ENGINE.snap_to_codeword(new_vec)

            # Update if the vector changed
            if snapped != current_vec:
                entry.vector = snapped
                entry.nrci = float(LEECH_ENGINE.calculate_nrci(snapped))
                entry.golay_codeword = snapped
                entry.fold3 = BLA.fold24_to3(snapped)
                refined += 1

        if refined > 0:
            self.state.vectors_refined += refined
            print(f"[GLM24] Refined {refined} vectors from co-occurrence data")
            # v3.17.0 BUG (c) FIX: flush immediately when vectors changed,
            # so learning isn't lost if the process exits before the next
            # 5-query boundary.
            self.state.save()

    def _check_for_new_edges(self, content_words: List[str]):
        """Check if any word pairs should get a new CRG edge."""
        for i, w1 in enumerate(content_words):
            for w2 in content_words[i+1:]:
                if w1 == w2:
                    continue
                count = self.state.cooccurrence[w1].get(w2, 0)
                if count >= self.edge_threshold:
                    # Check if edge already exists
                    existing = False
                    for e in self.crg.out.get(w1, []):
                        if e.dst == w2:
                            existing = True
                            break
                    if not existing:
                        # Add new edge
                        self.crg.add_edge(w1, "co_occurs", w2)
                        self.state.learned_edges.append((w1, "co_occurs", w2))

    def get_status(self) -> dict:
        """Return learning status."""
        return {
            "queries_processed": self.state.query_count,
            "words_learned": len(self.state.learned_words),
            "edges_learned": len(self.state.learned_edges),
            "vectors_refined": self.state.vectors_refined,
            "cooccurrence_pairs": sum(len(v) for v in self.state.cooccurrence.values()),
            "state_saved": LEARNED_STATE_PATH.exists(),
        }


# ── 3. ISOLATION TEST ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testing Module 24: Continuous Learner (v3.16.0) ===")
    from GLM01_substrate import _build_vocabulary
    from GLM03_crg import build_extended_crg

    vocab_dict = _build_vocabulary()
    class Vocab:
        def __init__(self, d): self.words = d
    vocab = Vocab(vocab_dict)
    crg = build_extended_crg()

    learner = ContinuousLearner(vocab, crg)
    print(f"Initial status: {learner.get_status()}")
    print()

    # Simulate processing queries
    test_queries = [
        ["hamiltonian", "time", "energy"],
        ["symmetry", "anomaly", "dimension"],
        ["hamiltonian", "operator", "symmetry"],
        ["energy", "force", "hamiltonian"],
        ["time", "energy", "symmetry"],
    ]

    for i, words in enumerate(test_queries):
        learner.process_query(f"test query {i}", words)
        print(f"  Query {i+1}: {words} -> status: {learner.get_status()}")

    print()
    print(f"Final status: {learner.get_status()}")
    learner.state.save()
    print(f"State saved to {LEARNED_STATE_PATH}")
