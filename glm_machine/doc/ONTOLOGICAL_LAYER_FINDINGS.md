# Ontological-Layer Reorganization Test — Findings

## Question
Euan's hypothesis: reorganizing vocabulary entries by real ontological meaning
(Reality/Information/Activation/Potential, the four-layer structure from
`gravity/04/d3_layer_grammar_theory.py`) rather than by grammatical role
(GLM23's current NOUN/VERB/ADJECTIVE/OPERATOR → quadrant assignment) would
place words on the lattice more meaningfully, since "words need to have
meaningful data to be placed on the lattice in a meaningful way."

## What's real vs newly constructed (stated up front)
- The Reality/Information/Activation/Potential layer definition (bits 0-5,
  6-11, 12-17, 18-23) and the `ObserverDynamicsEngine` that uses it are
  REAL, existing, verified — found in `core_studio_v4.0/core/
  ubp_observer_dynamics.py`, exactly matching GLM23's `QUADRANT_RANGES`.
- The word-level classifier (`infer_ontological_layer`) mapping arbitrary
  dictionary words into these four categories is NEW — built for this test
  from explicit, hand-authored keyword sets grounded in the layers' own
  meaning. The D.3 file's version of these labels was for physics-constant
  formulas, not general vocabulary; no pre-existing word-level mapping
  existed to reuse.

## Method
Built three parallel vector sets on the IDENTICAL corpus/vocab (4,261 words):
1. **Ontology-aligned** — new classifier, GLM23's exact SVD+Golay-snap
   machinery reused unchanged.
2. **Grammar-aligned** — GLM23's actual production method (unchanged).
3. **Plain SVD** — median-split only, no quadrant-forcing, no Golay-snap.

Scored all three with the same context-similarity Spearman test used in
Exp F/G/etc.: real co-occurrence-based paradigmatic similarity vs Hamming
distance, 8,000 random word pairs, window=5.

## Result
| Vector construction | Spearman ρ | p-value |
|---|---|---|
| Plain SVD (no forcing, no snap) | **−0.2473** | 9.05e-112 |
| Ontology-aligned (new) | −0.0014 | 0.90 (n.s.) |
| Grammar-aligned (GLM23 production) | −0.0094 | 0.40 (n.s.) |

Ontology and grammar are statistically indistinguishable from each other —
and both are statistically indistinguishable from zero. **Swapping the
classification scheme did not recover the signal.**

## Decomposition: which single step destroys it?
| Step isolated | Spearman ρ | p-value |
|---|---|---|
| Quadrant-forcing ONLY (no Golay-snap) | −0.0022 | 0.84 (n.s.) |
| Golay-snap ONLY (no quadrant-forcing) | −0.1859 | 3.95e-63 |

**Quadrant-forcing is the culprit, not Golay-snapping.** Snapping to the
nearest valid codeword costs about 25% of the correlation magnitude
(−0.247 → −0.186) and is otherwise fairly benign. Forcing the "dominant"
6-bit range (chosen by any external label — grammar OR ontology) and
zeroing most of the other 18 bits by percentile threshold destroys the
real 24-dimensional structure the SVD found, regardless of which labeling
scheme picked the dominant range.

## Verdict
❌ The specific hypothesis (ontology > grammar as the organizing principle)
is a clean null — same failure mode either way. ✅ But the diagnostic is
genuinely useful: the destruction is structural (the forcing mechanism
itself), not about which category label drives it. This reframes "what
would make a measurable improvement" — it's not about finding the right
classification scheme, it's about finding a way to encode
grammatical/ontological category information WITHOUT the "force one
quadrant, zero out the rest" step that currently erases the SVD's real
signal.

## Concrete next step
A construction that keeps the median-split-then-Golay-snap pipeline
(preserves ~75% of real signal, confirmed) while encoding category
information as a softer signal — e.g. breaking ties among near-equidistant
codewords by category preference, rather than forcing bit positions before
snapping at all. Not yet built or tested; a real next experiment, not a
guess at the answer.
