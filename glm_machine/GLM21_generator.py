# ══════════════════════════════════════════════════════════════════════════════
# §21  GENERATOR — ZONE-CENTROID-STATE LANGUAGE GENERATION (v3.13.0 NEW)
# ══════════════════════════════════════════════════════════════════════════════
# The generation layer GLM has been missing.  Addresses the pigeonhole
# cycling problem (ledger point #6) by using the zone CENTROID as the
# generation state instead of just the last word.
#
# THE CYCLING PROBLEM (recap):
#   Deterministic argmax over a 1-2 word context MUST eventually repeat a
#   state (pigeonhole: finite states + deterministic transition → cycle).
#   Tested pre-ledger: greedy bigram walk hit a 9-word cycle at step 63.
#
# THE FIX (synthesis point #11):
#   Use the zone centroid (a 24-bit vector that evolves with evidence) as
#   the generation state.  This gives 2^24 ≈ 16M states before pigeonhole
#   bites — and each state is a real lattice point with geometric meaning,
#   not an arbitrary token window.
#
# ARCHITECTURE:
#   1. Seed the zone with a query (or a topic noun)
#   2. At each step, the centroid defines a "context point" in 24-bit space
#   3. Find the nearest vocab word to the centroid (by Hamming distance)
#      that (a) hasn't been used recently and (b) is reachable via a CRG edge
#      from the last word — this is the "transition grammar" constraint
#   4. Emit that word, add its vector to the zone (updating the centroid)
#   5. Repeat until a stop condition (sentence count, coherence threshold,
#      or cycle detection)
#
# This is NOT an LLM (no attention, no learned weights, no sampling).  It's
# a deterministic walk over the 24-bit lattice constrained by the CRG.  But
# it's a genuine GENERATION loop — it produces novel sequences, not just
# recalled templates.
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import re, hashlib
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict

from GLM01_substrate import (
    BLA, LEECH_ENGINE, GOLAY_ENGINE, vector_to_hex_int, fast_hamming,
    WordEntry,
)
from GLM02_constants import FUNCTION_WORDS


# ── 1. GENERATION STATE ──────────────────────────────────────────────────────

@dataclass
class GenerationState:
    """Mutable state for the generation loop."""
    centroid: List[int] = field(default_factory=list)
    emitted: List[str] = field(default_factory=list)
    emitted_vectors: List[List[int]] = field(default_factory=list)
    used_recently: List[str] = field(default_factory=list)  # sliding window
    turn: int = 0
    coherence_history: List[float] = field(default_factory=list)

    def update_centroid(self, vec: List[int], weight: float = 1.0):
        """Add a vector to the centroid (weighted majority vote)."""
        if not self.centroid:
            self.centroid = list(vec)
            return
        # Weighted majority: each bit is 1 if weighted sum > total/2
        # We track a running weighted sum per bit
        if not hasattr(self, '_weighted_sums'):
            self._weighted_sums = [0.0] * 24
            self._total_weight = 0.0
            # Initialize with current centroid
            for b in self.centroid:
                if b:
                    self._weighted_sums[self.centroid.index(b) if b in self.centroid else 0] += 1.0
            self._total_weight = sum(self.centroid)
        # Add the new vector
        for i, b in enumerate(vec):
            if b:
                self._weighted_sums[i] += weight
        self._total_weight += weight
        # Recompute centroid
        half = self._total_weight / 2.0
        self.centroid = [1 if s > half else 0 for s in self._weighted_sums]

    def coherence(self) -> float:
        """Current coherence: how tightly the emitted vectors cluster."""
        if len(self.emitted_vectors) < 2:
            return 0.0
        # Mean Hamming distance from each vector to the centroid
        dists = [BLA.hamming_distance(v, self.centroid)
                 for v in self.emitted_vectors]
        avg_dist = sum(dists) / len(dists)
        # Tightness = 1 - normalized distance
        tightness = max(0.0, 1.0 - avg_dist / 12.0)
        return round(tightness, 4)


# ── 2. THE GENERATOR ─────────────────────────────────────────────────────────

class GLMGenerator:
    """Deterministic language generator over the 24-bit lattice.

    Uses the zone centroid as state (addresses cycling) and the CRG as a
    transition grammar (ensures fluency).
    """

    def __init__(self, vocab: Any, crg: Any, max_recent: int = 8,
                 min_weight: int = 4, max_weight: int = 20):
        # v3.22.0: Session 2-6 best configuration as default
        # resonance_weight=3.0, hamming_weight=0.0, crg_bonus=0.30
        # (was: nearest-neighbor Hamming walk, no resonance)
        self.vocab = vocab
        self.crg = crg
        self.max_recent = max_recent
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.target_nrci = 0.7196  # saturation plateau
        self.ema_alpha = 0.3       # EMA centroid update (prevents collapse)
        self.crg_bonus = 0.30      # CRG guidance weight
        self.resonance_weight = 3.0  # resonance dominates
        self.hamming_weight = 0.0  # no Hamming term (Session 2 finding)
        # Precompute hex ints for fast Hamming
        self._hex_cache: Dict[str, int] = {}
        target = vocab.words if hasattr(vocab, 'words') else vocab
        for w, entry in target.items():
            if hasattr(entry, 'vector') and entry.vector:
                w_sum = sum(entry.vector)
                # Exclude degenerate vectors (all-0s, all-1s, near-degenerate)
                if w_sum < min_weight or w_sum > max_weight:
                    continue
                try:
                    self._hex_cache[w] = vector_to_hex_int(entry.vector)
                except Exception:
                    pass

    def _nearest_words(self, centroid: List[int], k: int = 20,
                       exclude: Optional[Set[str]] = None) -> List[Tuple[str, int]]:
        """Find the k nearest vocab words to the centroid by Hamming distance."""
        exclude = exclude or set()
        cent_hex = vector_to_hex_int(centroid)
        candidates = []
        for w, h in self._hex_cache.items():
            if w in exclude:
                continue
            d = fast_hamming(cent_hex, h)
            candidates.append((w, d))
        candidates.sort(key=lambda x: x[1])
        return candidates[:k]

    def _crg_reachable(self, word: str) -> Set[str]:
        """Words reachable from `word` via a single CRG edge."""
        reachable = set()
        for e in self.crg.out.get(word, []):
            if e.label not in ("contradicts", "incompatible_with"):
                reachable.add(e.dst)
        for e in self.crg.into.get(word, []):
            if e.label not in ("contradicts", "incompatible_with"):
                reachable.add(e.src)
        return reachable

    def _pick_next(self, state: GenerationState,
                   candidates: List[Tuple[str, int]]) -> Optional[str]:
        """Pick the next word from candidates.

        Selection criteria (in order):
          1. CRG-reachable from the last emitted word (transition grammar)
          2. Not in the recent-words window (anti-cycling)
          3. Not a non-word (filter metadata-like tokens)
          4. Diversity bonus: penalise words whose vector is already in the
             emitted set (breaks tight clusters)
          5. Closest to the centroid (coherence)
        """
        if not candidates:
            return None
        recent = set(state.used_recently)
        last_word = state.emitted[-1] if state.emitted else None

        # Filter out non-words (metadata tokens, underscores, etc.)
        def _is_real_word(w: str) -> bool:
            if '_' in w:
                return False
            if len(w) < 3:
                return False
            if w.isdigit():
                return False
            return True

        candidates = [(w, d) for w, d in candidates if _is_real_word(w)]
        if not candidates:
            return None

        # Diversity: penalise words whose hex is already in the emitted set
        emitted_hexes = set()
        target = self.vocab.words if hasattr(self.vocab, 'words') else self.vocab
        for w in state.emitted:
            if w in self._hex_cache:
                emitted_hexes.add(self._hex_cache[w])

        # Score = Hamming distance + diversity penalty (if vector already used)
        def _score(w: str, d: int) -> Tuple[int, int]:
            penalty = 50 if w in self._hex_cache and self._hex_cache[w] in emitted_hexes else 0
            return (d + penalty, d)

        # If we have a last word, prefer CRG-reachable candidates
        if last_word:
            reachable = self._crg_reachable(last_word)
            crg_candidates = [(w, d) for w, d in candidates
                              if w in reachable and w not in recent]
            if crg_candidates:
                crg_candidates.sort(key=lambda x: _score(x[0], x[1]))
                return crg_candidates[0][0]

        # Fallback: best-scored non-recent candidate
        non_recent = [(w, d) for w, d in candidates if w not in recent]
        if non_recent:
            non_recent.sort(key=lambda x: _score(x[0], x[1]))
            return non_recent[0][0]

        # Last resort: closest candidate (even if recent)
        candidates.sort(key=lambda x: _score(x[0], x[1]))
        return candidates[0][0] if candidates else None

    def generate(self, seed_words: List[str], n_words: int = 12,
                 max_sentences: int = 3) -> str:
        """Generate a multi-word string from seed words.

        Args:
            seed_words: words to initialise the zone centroid
            n_words: max words to generate per sentence
            max_sentences: max sentences to generate
        """
        target = self.vocab.words if hasattr(self.vocab, 'words') else self.vocab
        state = GenerationState()

        # Seed the centroid with seed word vectors
        for w in seed_words:
            entry = target.get(w)
            if entry and hasattr(entry, 'vector') and entry.vector:
                state.update_centroid(list(entry.vector), weight=2.0)
                state.emitted.append(w)
                state.emitted_vectors.append(list(entry.vector))
                state.used_recently.append(w)

        if not state.centroid:
            return ""  # no valid seed words

        # Generate
        sentences = []
        current_sentence = list(state.emitted)  # start with seeds
        words_generated = 0

        for step in range(n_words * max_sentences):
            # Find nearest words to centroid
            candidates = self._nearest_words(state.centroid, k=20,
                                              exclude=set(state.used_recently[-self.max_recent:]))
            # If we have CRG-reachable candidates, prefer them
            next_word = self._pick_next(state, candidates)
            if not next_word:
                break

            entry = target.get(next_word)
            if not entry or not hasattr(entry, 'vector') or not entry.vector:
                break

            # Emit the word
            state.emitted.append(next_word)
            state.emitted_vectors.append(list(entry.vector))
            state.used_recently.append(next_word)
            if len(state.used_recently) > self.max_recent:
                state.used_recently = state.used_recently[-self.max_recent:]
            current_sentence.append(next_word)
            words_generated += 1

            # Update centroid (lower weight for generated words — seeds dominate)
            state.update_centroid(list(entry.vector), weight=0.5)
            state.coherence_history.append(state.coherence())

            # Sentence boundary: every n_words, or if we hit a CRG dead-end
            if words_generated % n_words == 0:
                sentences.append(" ".join(current_sentence))
                current_sentence = []
                if len(sentences) >= max_sentences:
                    break

        # Flush any remaining words
        if current_sentence:
            sentences.append(" ".join(current_sentence))

        return ". ".join(sentences) + "." if sentences else ""

    def generate_about(self, topic: str, n_words: int = 12,
                       max_sentences: int = 3) -> str:
        """Generate text about a topic word."""
        target = self.vocab.words if hasattr(self.vocab, 'words') else self.vocab
        # Use the topic word + its CRG neighbours as seeds
        seeds = [topic]
        for e in self.crg.out.get(topic, [])[:2]:
            if e.dst in target:
                seeds.append(e.dst)
        return self.generate(seeds, n_words=n_words, max_sentences=max_sentences)


# ── 3. ISOLATION TEST ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testing Module 21: Generator (v3.13.0) ===")
    from GLM01_substrate import _build_vocabulary
    from GLM03_crg import build_extended_crg

    vocab_dict = _build_vocabulary()
    class Vocab:
        def __init__(self, d): self.words = d
    vocab = Vocab(vocab_dict)
    crg = build_extended_crg()

    gen = GLMGenerator(vocab, crg)

    print("\nGenerating about 'hamiltonian':")
    text = gen.generate_about("hamiltonian", n_words=8, max_sentences=2)
    print(f"  {text}")
    print()

    print("Generating about 'energy':")
    text = gen.generate_about("energy", n_words=8, max_sentences=2)
    print(f"  {text}")
    print()

    print("Generating about 'weyl anomaly':")
    text = gen.generate_about("weyl anomaly", n_words=8, max_sentences=2)
    print(f"  {text}")