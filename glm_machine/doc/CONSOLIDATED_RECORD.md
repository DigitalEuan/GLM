# UBP/GLM Research Session — Consolidated Record

Every number below is from code actually executed against the real codebase
(`core_studio_v4.0`, `ubp_unified_v5.py`, `ubp_kb_architect.py`, plus a
real (if tiny) trained transformer). Organized by what actually worked,
not by chronology. ✅ = real, working, positive. ⚠️ = real but caveated.
❌ = clean, tested null. 🔧 = scoping/methodology note.

---

## WORKING PARTS

### 1. ✅ Graph Laplacian spectral embedding (best result this session)
Real co-occurrence counts (a physical, measurable quantity — no XOR
anywhere) as graph edge weights → real eigendecomposition of the
normalized graph Laplacian (a genuine joint solve across all 2,808 words
simultaneously, not sequential/greedy) → real Golay-snap.

| | ρ vs real semantic similarity | significance |
|---|---|---|
| Raw continuous embedding | −0.1689 | p=2.7e-52 |
| Quantized + Golay-snapped | −0.1704 | p=3.4e-53 |

Survives discretization **almost losslessly** (~100% signal retention) —
unlike every other construction tried this session. This is the strongest
evidence so far that the destructive-quantization problem isn't
inevitable; it depends on what kind of continuous structure you're
quantizing. Built with zero XOR, per your steer on data-preservation.

### 2. ✅ GF(2) Gaussian elimination — exact Golay code recovery
From exactly 12 labeled codeword examples, real linear algebra over GF(2)
recovers the entire 24-bit code exactly: **100.00%** held-out accuracy on
500 unseen codewords + 500 unseen non-codewords, every time. Below 12
examples (rank-deficient): chance level. Sharp, clean threshold — the
right tool for a genuinely linear structure.

### 3. ✅ MOG-grounded vectors — real semantic scoring, no quadrant-forcing
Scored real word definitions against the 24 actually-existing MOG category
names (Mass/Charge/Space/Time/.../Coherence/Phase — already computed
throughout GLM03-24, previously only used as a post-hoc label). Kept as
full 24-dimensional data, snapped only at the end.
**ρ=−0.0814, p=3.16e-13.** Beats every "aligned" (quadrant-forced)
construction, though weaker than plain SVD due to identified, fixable
coverage gaps (58% keyword fallback).

### 4. ✅ Golay/Leech/Monster engines in `ubp_unified_v5.py` are real
`ExactMath`, `ExactRoot`, `BinaryLinearAlgebra`, `NoiseALU`, `PhysicsALU`,
`LinearAlgebraALU` all genuinely implement native, exact, traceable
computation with real substrate metrics (`AdaptiveManifold.fingerprint()`:
Gray-code transform → Golay-weight lattice classification → NRCI as an
exact Fraction → Monster-group grade). Confirmed live: `gcd(54,24)` via
this path returns a full trace plus real metrics, not just `6`.

### 5. ✅ Prose composer / `chat_prose()`
Long-form natural-language GLM output, additive, non-destructive to
existing tested behavior. Genuinely good on isolated queries (confirmed
via fresh-instance control).

---

## CLEAN NULLS (tested and ruled out, not just untried)

### 6. ❌ Quadrant-forcing (any labeling scheme)
Forcing a "dominant" 6-bit quadrant and zeroing most of the other 18 bits
destroys real signal regardless of what decides the quadrant:
- Grammar-role-aligned: ρ=−0.0094 (p=0.40, dead)
- Ontology-aligned (Reality/Information/Activation/Potential): ρ=−0.0014 (p=0.90, dead)
- Decomposition proved it precisely: quadrant-forcing alone → ρ=−0.0022 (dead); Golay-snap alone → ρ=−0.1859 (mostly alive).

### 7. ❌ Gradient-based ML learning Golay codeword membership
LogReg 48.44%, RandomForest 20.48%, MLP 100%train/56.74%test — all ≈chance
on held-out codewords. Theoretically expected: codeword membership is a
GF(2) parity function, the textbook hard case for gradient descent.

### 8. ❌ Directed curriculum vs. random reinforcement (GLM24 continuous learner)
60 real queries each condition, controlled for volume. Directed sat
inside the random spread, not above it; one random seed produced a
byte-for-byte identical result to the directed run. The refinement
mechanism (average → median-split → snap) discards the distinction
between "chosen" and "random" partners before it can matter.

### 9. ❌ Golay/Leech-dimensional "sweet spot" in transformer attention
Swept head_dim across all 7 valid divisors of hidden_size=192 (a real,
trained, tiny transformer, matched parameter counts). head_dim=24 ranked
5th of 7 — below average, not a peak. Sweep variation (std=0.0134) was
only 1.7x the seed-to-seed noise floor (std=0.0079) — not distinguishable
from noise. Mechanistically expected: standard scaled-dot-product
attention has no real connection to coding theory.

### 10. ❌ Golay-syndrome-scored attention (replacing dot-product with real syndrome weight)
Trained stably (real achievement given the mechanism), but scored
slightly worse than standard attention (mean diff 0.0142, p=0.075, not
significant). Honest cause: the straight-through estimator means weights
are updated via a smooth dot-product surrogate's gradients, not the real
discrete computation the forward pass actually uses — a genuine mismatch
between what's computed and what's learned.

### 11. ❌ Syndrome-guided native bit-flip learning (sequential, XOR-based)
Real, exact, non-gradient mechanism (single-bit flips chosen via real GF(2)
syndrome-column linearity) — but purely local/greedy/pairwise. ρ≈0 at 1
epoch AND at 20 epochs (no convergence; "valid codeword count" oscillates
299↔640↔353↔674... rather than settling). Diagnosis: no global-consistency
mechanism, unlike the Laplacian's joint eigendecomposition — this is
likely *why* item #1 above worked and this didn't.

### 12. ❌ Tilt as a standalone semantic carrier
Real, verified, significant on non-destroyed vectors (ρ=−0.047 on plain
SVD, p=2.4e-5) but consistently ~5x weaker than full Hamming distance,
and partial correlation after controlling for Hamming distance is
borderline (−0.0216, p=0.053) — mostly redundant, not an independent
signal. Dies completely under quadrant-forcing like everything else.

---

## SCOPING / METHODOLOGY NOTES (real findings about the codebase itself)

### 13. 🔧 Real "sovereign computation" isn't wired into GLM09
`GLM09_tools.py` calls plain stdlib `math` or SymPy for every numeric
operation — zero calls to the real native `ExactMath`/`NoiseALU` classes
that already exist in `ubp_unified_v5.py`. Confirmed live, side by side.
Fixable wiring gap, not a fundamental limitation.

### 14. 🔧 CRG is drastically under-built relative to vocabulary
4,248 words, only 70 relation edges (60.7 words per edge). CRG traversal
is GLM's only mechanism that behaves like math does (explicit fact →
exact lookup, not statistical inference) — and it's real, connected via
live demonstration to the same `fingerprint()` mechanism used for numbers.

### 15. 🔧 Three real, distinct bugs found in GLM24's continuous learner
(1) Protected `ubp_id` prefixes silently exclude words from refinement.
(2) `learned_edges` are recorded to disk but never re-applied to the live
CRG graph on reload. (3) No flush-on-exit save — loses up to 4 queries of
real learning per session (`query_count % 5` boundary).

### 16. 🔧 v3.16.0's own new test scripts are broken on a fresh clone
`exp_l/m/n/o/p`, `exp_g_followup` all reference an uncommitted `glm_work/`
directory. SVD-embedding result reproduces in direction but not magnitude
under different (equally reasonable) hyperparameters.

---

## The honest through-line

Two things now have multiple, independent confirmations, not single data
points:
1. **Real semantic signal is recoverable from real data by more than one
   method** — n-grams, PPMI-SVD, MOG-category grounding, and now graph
   Laplacian spectral embedding all find it independently, in the same
   general ρ range (−0.05 to −0.25), and the Laplacian version is the
   first to survive discretization almost losslessly.
2. **What destroys signal, specifically, is quadrant-forcing and purely
   local/sequential update rules** — anything that either (a) collapses
   24 real dimensions down to one arbitrarily-privileged 6-bit range, or
   (b) tries to build global structure from purely pairwise, greedy,
   un-coordinated local moves. What preserves or builds signal is either
   (a) a real joint solve across the whole structure at once (SVD,
   Laplacian eigendecomposition, GF(2) Gaussian elimination), or (b) exact
   snapping to the nearest valid codeword without first forcing a
   dominant quadrant.

## Files from this session
- `SESSION_SUMMARY.md` (glm_v316/) — the longer, chronological version of sections 1-10
- `test_directed_framework.py`, `experiment_ontological_vectors.py`, `experiment_mog_grounded_vectors.py` — reusable scripts
- `tiny_gpt.py`, `golay_attention.py`, `golay_gpt.py`, `syndrome_guided_learning.py` (golay_llm_test/) — the transformer/native-learning experiments
- `laplacian_embedding.npy`, `cooc_weight_matrix.npy` — the best-performing construction's actual output, ready to reuse
- This file — the consolidated, working-parts-first record
