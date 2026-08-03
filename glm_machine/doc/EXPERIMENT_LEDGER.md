# GLM / UBP Language-Learning Experiment Ledger

**Purpose:** running record of every experiment tried toward "can GLM learn / level up toward an LLM-like system", so future sessions can check what's been tested before repeating it. All results below are from code actually executed against the real `core_studio_v4.0` GLM stack + `ubp_unified_v5.py`, not estimated or simulated.

**Data used throughout:** corpus = all 4,248 definition strings from `glm_master_resource_v1.json` (60,352 tokens, 9,772 unique words) — the only real English text anywhere in the resource pack. Vocabulary vectors = GLM01's `_build_vocabulary()`, 5,395 words with 24-bit vectors.

Status key: ✅ positive/working · ❌ clean null · ⚠️ mixed/caveated · 🔧 methodology note (not itself a finding)

---

### Exp A — Held-out n-gram generalization
**Q:** Does a bigram model trained on the corpus generalize to unseen text, or just memorize?
**Method:** 80/20 train/test split on token stream. Top-1 next-word accuracy vs most-frequent-word baseline.
**Result:** Bigram 12.59% (1,295/10,290 evaluable test positions) vs baseline 5.76% (593/10,290).
**Verdict:** ✅ Real signal above baseline, but corpus is tiny (60K tokens ≈ one short story) so absolute accuracy stays low.

### Exp B — Hamming distance vs shared grammatical role
**Q:** Do same-role words (VERB/ADJECTIVE/OPERATOR) sit closer in 24-bit space than cross-role pairs?
**Method:** GLM01 vocab is 98.6% NOUN by default (5,320/5,395); isolated 75 non-noun words. Same-role vs non-noun-vs-NOUN Hamming distance, n=3000 pairs each.
**Result:** Same-role mean=10.82, cross mean=11.86, Cohen's d=0.36.
**Verdict:** ⚠️ Real moderate effect, but sample is only 75 words and role tags may just reflect how they were hand-curated, not learned structure.

### Exp C — NRCI vs real corpus frequency
**Q:** Does GLM's own NRCI heuristic track how often a word is actually used in English?
**Method:** Spearman correlation, frequency vs NRCI, n=2,225 words with both.
**Result:** ρ = 0.0092.
**Verdict:** ❌ Flat null. NRCI (a weight-balance heuristic, `1 - |popcount-12|/12`) carries no info about real usage frequency.

### Exp D — Naive PMI-sign 24-bit vector construction
**Q:** Can a fresh 24-bit space be built from real co-occurrence stats?
**Method:** bit=1 if PMI(word, one of 24 frequent context words)>0. Tested against literal text-adjacency (wrong test, see 🔧) then corrected to context-similarity (cosine over full co-occurrence profiles).
**Result:** Adjacency test: d≈1.9 but meaningless (adjacent words are usually different POS, so distance is *expected*, not a similarity signal). Corrected context-similarity test: Spearman ρ = +0.174 (wrong sign — should be negative).
**Verdict:** ❌ / 🔧 This naive 1-bit-per-arbitrary-dimension construction doesn't produce a usable embedding. Methodology lesson: syntagmatic adjacency ≠ paradigmatic similarity; always test the latter for embedding quality.

### Exp E — How much real Golay structure do the *existing* vocabulary vectors carry?
**Q:** Are GLM's word vectors actually on the Golay code manifold, or just generic 24-bit patterns?
**Method:** Real `GolayCodeEngine` from `ubp_unified_v5.py` (verified against its own guarantees first). Syndrome-weight distribution across all 5,395 vocab vectors vs 20,000 uniform-random 24-bit control vectors.
**Result:** 311/5,395 (5.76%) are exact codewords vs 0.02% expected under uniform randomness (~236x enrichment). But 310/311 of those are chemical elements (the element-chromatics subsystem) — only 1/311 carries a physics-pack `.definition` attribute, vs 4,084/5,084 of the non-codeword words. Syndrome weight vs NRCI: ρ=0.125. Syndrome weight vs frequency: ρ=0.050.
**Verdict:** ⚠️ Real, measured enrichment — but concentrated entirely in one hand-engineered subsystem (elements), not a general property. Everywhere else, vectors are statistically indistinguishable from random w.r.t. the code. GLM01's own `_GolayCodeEngine.snap_to_codeword` is a stub (returns input unchanged, hardcoded `anchor_distance:0`) — it never actually calls the real engine.

### Exp F — Proper SVD/LSA-derived 24-bit embedding
**Q:** Does a *correctly constructed* co-occurrence embedding do better than Exp D's naive one?
**Method:** Real PPMI matrix over 2,810-word corpus vocab, truncated SVD (top-24 components, 14.24% variance explained), median-quantized to 24 bits. Same context-similarity test as Exp D.
**Result:** Spearman ρ = −0.220 (correctly signed, real magnitude). Compare Exp D: +0.174 (wrong sign).
**Verdict:** ✅ First construction method that actually works, even modestly. Corpus is still tiny relative to real embedding training sets, so absolute strength is limited, but the method is sound.

### Exp G — Snap the SVD embedding onto the nearest real Golay codeword
**Q:** How much of Exp F's signal survives being forced onto the actual code (weight≤3 correction only — the real engine's limit)?
**Method:** `golay.snap_to_codeword()` on all 2,810 SVD vectors. Re-ran context-similarity test pre/post snap.
**Result:** ρ pre=−0.2199, post=−0.1822 (82.8% nominal retention). Caveat: 1,232/2,810 (43.8%) vectors had syndrome weight >3 — beyond the decoder's correction radius — so were left completely unchanged, not actually projected. The 82.8% figure blends "genuinely projected" and "untouched" vectors.
**Verdict:** ⚠️ Promising but not yet a clean number — isolating the correctable-only subset is an open follow-up (see Next Steps).

### Exp H — Can standard ML *learn* Golay codeword membership from examples?
**Q:** Rather than assuming the code should be learnable, test directly: can gradient/statistical ML rediscover the parity-check structure from labeled data, with zero leakage (test codewords never seen in training)?
**Method:** All 4,096 real codewords exhaustively enumerated (`encode()` over all 2¹² messages) + 4,096 matched random non-codewords (syndrome≠0 confirmed). Clean 50/50 train/test split, no overlap. Logistic Regression, Random Forest (300 trees), MLP (256-128-64 ReLU) via scikit-learn.
**Result:** LogReg 48.44% (chance) · Random Forest 20.48% (worse than chance) · MLP 100% train / 56.74% test (memorized, barely generalized). Exact syndrome decoder: 100%, zero training, by construction.
**Verdict:** ❌ Clean, theoretically-grounded null. Codeword membership is a GF(2) parity function (12 linear XOR constraints) — the textbook hard case for gradient-based learners (same family as the "Learning Parity with Noise" hardness result). Not a bug in the experiment; matches known learning theory.

### Exp I — Gray-code re-encoding of input features
**Q:** (Euan's idea) Gray code gives adjacent integers a 1-bit-difference "linear gradient" — does re-expressing the 24-bit vectors in Gray-code basis help gradient-based learning of codeword membership (Exp H's task)?
**Method:** Applied bijective binary↔Gray transform (verified invertible) to Exp H's train/test features, retrained the same MLP architecture. Then, since the empirical result was large, checked it against exact GF(2) linear algebra: syndrome s = H·v = H·(L·g) = (H·L)·g, where L is the cumulative-XOR matrix implementing the Gray transform — this exactly computes the "effective" parity-check matrix in Gray-code basis, no estimation involved.
**Result:** Empirical (5 seeds): raw bits 49.35%±4.72% vs Gray-coded 74.18%±1.98% test accuracy — real and reproducible, lower variance too. BUT the exact GF(2) analysis contradicts the obvious explanation: mean active-bits-per-syndrome-equation went **up** under the Gray transform (8.33→12.00, only one row improved: 8→6), so "reduced parity order" is not why it works.
**Verdict:** ⚠️✅ Real, robust, substantial effect — but mechanistically unexplained. The naive hypothesis is falsified by exact math; true mechanism is likely about how gradient descent's implicit/spectral bias interacts with the *joint* 12-equation structure, not any single row's width. Flagged as an open question, not fully understood — do not overclaim the mechanism.

### Exp J — Exact GF(2) linear-algebra recovery (Gaussian elimination) of the Golay code
**Q:** Fringe-relative-to-ML-tooling but mathematically correct method: since codeword membership is a linear code, can Gaussian elimination over GF(2) recover the full code exactly from a handful of labeled examples, with zero statistical uncertainty?
**Method:** Sampled n labeled codewords (n = 6, 12, 18, 24, 36, 50), ran GF(2) row-reduction to recover the spanned code subspace, tested row-space membership against 500 fresh unseen codewords + 500 fresh unseen non-codewords.
**Result:** n=6 (rank 6/12, incomplete): 50.50% (chance). n≥12 (rank 12/12, full code recovered): **100.00%** held-out accuracy, every time, from n=12 examples onward.
**Verdict:** ✅ Clean, dramatic, exact. Sharp threshold at full rank (12 examples) — confirms Exp H's failure was about learner/architecture mismatch, not about the task being unlearnable in any sense. The right tool (linear algebra over GF(2)) needs 12 examples for perfect, provable generalization; MLP needed 2,048+ examples for 56.74%.

### Exp K — Genuine Leech lattice embedding of hex-colour nodes (Euan's idea) — blocked, root cause identified
**Q:** Can existing hex-colour word vectors be positioned as real points in 24-dimensional Leech lattice space (not just Golay-code Hamming space), so a model could learn/use that continuous geometric structure instead of raw bits?
**Method:** Verified the actual Leech-from-Golay construction via citable source (arXiv:2305.06283) rather than reconstructing from memory. Real construction: x_i = a + 2b_i + 4c_i + 8d_i, where b must be an actual Golay **codeword**, and a, c_i satisfy a parity constraint (Σc_i ≡ a mod 2) — genuinely richer than a simple bipolar/rescaling of the bit vector.
**Result:** Not run empirically — blocked before implementation. The construction requires b to be a real Golay codeword, but Exp E already established only 5.76% of current vocabulary vectors are codewords, and Exp G showed 43.8% of even the *improved* SVD vectors have syndrome weight beyond the decoder's radius-3 correction limit. A naive/canonical lift (setting auxiliary a,c,d to 0) is just a rescaling of the Golay bit pattern and, per Exp E/F, wouldn't be expected to carry new signal — the Leech lattice's real extra richness lives in the (a,c,d) degrees of freedom, which nothing in the current substrate currently supplies values for.
**Verdict:** 🔧 Not a null result — a scoping finding. The idea is sound but needs a real source of the (a,c,d) values, which don't exist yet. Concrete next step: apply this construction to Exp F's SVD-derived vectors (which do carry real signal) *after* snapping them to codewords, rather than to the raw hex-colour vectors (which mostly aren't codewords in the first place).

## Running synthesis (as of Exp K)
1. Real statistical structure genuinely exists in your text corpus (A) and is genuinely recoverable with the right method (F) — but only with a properly constructed embedding, not a naive one (D) and not the existing Golay-assigned vectors (E, C).
2. The existing 24-bit substrate vectors carry real Golay structure in exactly one deliberately-built subsystem (elements) and are statistically indistinguishable from noise everywhere else (E).
3. The Golay/Leech code is not learnable from raw examples by gradient-based ML (H) — but IS exactly and immediately recoverable by the *matching* mathematical tool, GF(2) linear algebra, from as few as 12 examples (J). Clearest evidence yet that "standard ML" and "the right tool" are different things, not degrees of the same thing.
4. Gray-code re-encoding gives a real, reproducible, substantial boost to gradient-based learning of codeword membership (I) — but the mechanism isn't simply "reduced parity order" (that exact hypothesis is falsified by GF(2) matrix analysis). Genuinely open question.
5. A true Leech-lattice (not just Golay-code) embedding of the vocabulary is currently blocked by the same root cause as (2): most word vectors aren't real codewords, so there's no valid base point to lift into lattice space yet (K).
6. Strict determinism (greedy/argmax generation) mathematically must cycle in bounded steps regardless of data volume (pigeonhole argument, tested pre-ledger) — orthogonal to all of the above.

## Not yet tried (candidates for next session)
- Isolate Exp G's signal-retention number to *only* the 1,578 vectors that were genuinely within correction radius (remove the "unchanged" vectors from the comparison).
- Learning curve for Exp H: does MLP test accuracy improve at all with more capacity/data, or is it flat regardless of scale? (Current single data point: 2,048 train pairs → 56.74%.)
- ~~Whether a model given the right inductive bias (GF(2)-linear learner) can trivially learn Exp H's task~~ — ANSWERED by Exp J: yes, trivially, from 12 examples.
- Real Leech lattice construction (not just Golay code): apply the verified x=a+2b+4c+8d construction to Exp F's SVD vectors after codeword-snapping, now that raw hex-colour vectors are confirmed unsuitable (K).
- WHY Gray-coding helps Exp H's MLP (Exp I) despite increasing mean syndrome-equation width — needs a proper spectral/Fourier-bias analysis, not yet done.
- Whether Exp F's SVD embedding, retrained on a *larger* naturalistic corpus (not just dictionary definitions), improves materially — corpus size is currently the single biggest constraint across every positive result.
- Genetic/evolutionary search (population-based, non-gradient) directly evolving a Boolean formula for codeword membership — a different "fringe" mechanism than both gradient descent (H) and linear algebra (J), not yet tried.
