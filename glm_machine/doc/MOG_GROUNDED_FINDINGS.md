# MOG-Grounded Vector Construction — Findings

## Context / redirect that produced this test
Prior turn's finding: quadrant-forcing (grammar-role OR ontology-based)
destroys real semantic signal (rho -0.247 -> ~0), regardless of which label
picks the dominant quadrant. Euan's redirect: audit the existing GLM/UBP
codebase more thoroughly before building new constructs, and pointed at two
documents (a "Tilt" note on gradients/eigenstates/Lagrange multipliers/
tensors, and a neutron-scattering symmetry-classification paper) as
possibly relevant to working around the bottleneck.

## Audit finding (real, verified)
`MOG_CATEGORIES` in `ubp_unified_v5.py` is a REAL, already-existing,
24-name semantic schema -- one named dimension per bit position:
M_Mass/Charge/Space/Time/Thermal/Count (bits 0-5), I_Topology/Symmetry/
Density/Connectivity/Dimension/Complexity (6-11), A_Energy/Force/Velocity/
Flux/Resonance/Spin (12-17), P_Probability/Ratio/Limit/Tax/Coherence/Phase
(18-23). Pervasively imported and computed in GLM03, GLM04, GLM15, GLM16,
GLM18, GLM20, GLM23, GLM24. BUT: `_get_mog_category()` is purely
descriptive -- it derives a label from an ALREADY-BUILT vector (same
dominant-quadrant-weight logic as the destructive forcing step), never
used as real semantic input to CONSTRUCT a vector. Confirmed by reading
the function directly, not inferred.

## Document connections (stated plainly, not just asserted)
- **UBP_Tilt.txt**, eigenstate/superposition section: "a quantum system may
  be a superposition of several eigenstates, each with a precise
  probability" -- directly names the error in quadrant-forcing: collapsing
  a word to one dominant category before analysis is a premature
  measurement-collapse; the real SVD signal is a genuine superposition
  across all 24 dimensions and should be kept that way as long as possible.
- **UBP_Tilt.txt**, Lagrange multiplier section: constrained optimization
  finds the best point *subject to* a real constraint. Golay-snap (nearest
  valid codeword) IS a real, necessary constraint and was already shown to
  preserve ~75% of signal alone. Quadrant-forcing is a second, unnecessary,
  over-constraining step bolted on top -- not something the system actually
  needs, just extra information loss.
- **Neutron-scattering paper**: classifies continuous parameter space via
  (a) comparison against real analytically-motivated reference patterns
  (least-squares match, not arbitrary cutoffs) and (b) exact boundary
  conditions where a coefficient genuinely vanishes. Template for how any
  future discretization step in GLM should work, instead of percentile
  guesses.

## Experiment: use the REAL 24 MOG names as real per-dimension semantic
targets, full data, no forced dominant quadrant
Built `experiment_mog_grounded_vectors.py`: scores each word's actual
definition against all 24 real category names via explicit, inspectable
keyword sets (hand-authored per category, matching the real names already
in the codebase, not invented labels). Keeps this as full continuous
24-dim data (no single dominant quadrant chosen). Falls back to real SVD
signal only for words with zero keyword overlap (2,485/4,261 = 58% --
a real coverage gap in the keyword lists, stated plainly). Per-dimension
median split (each of the 24 real categories gets its own threshold).
Golay-snap at the end only (85.4% correctable).

## Result
| Construction | Spearman rho | p-value | Significant? |
|---|---|---|---|
| Plain SVD (no forcing, no snap) | -0.2473 | 9.05e-112 | yes |
| Golay-snap ONLY (no forcing) | -0.1859 | 3.95e-63 | yes |
| **MOG-grounded (full-data, no forcing)** | **-0.0814** | **3.16e-13** | **yes** |
| Quadrant-forcing ONLY (no snap) | -0.0022 | 0.84 | no |
| Grammar-aligned (both steps, production) | -0.0094 | 0.40 | no |
| Ontology-aligned (both steps) | -0.0014 | 0.90 | no |

## Verdict
✅ Partial confirmation. Avoiding quadrant-forcing and using real per-category
semantic grounding recovers genuine, statistically solid signal (p=3e-13) --
decisively better than either "aligned" production method, both of which
are statistically indistinguishable from noise. ⚠️ But it's weaker than
plain SVD or Golay-snap-alone, for two identified, fixable reasons: sparse
keyword coverage (58% fallback) and mixing two differently-scaled signals
(integer keyword counts vs. continuous SVD loadings) in one un-normalized
median split. Neither is a flaw in the underlying idea -- both are
construction details worth fixing before concluding how much of the
plain-SVD signal is recoverable this way.

## Concrete next step
Re-run with (a) properly z-score-normalized keyword-scores and SVD-scores
before combining, and (b) an expanded keyword list built semi-automatically
(e.g. from WordNet synonyms per category) to close the 58% coverage gap.
Not yet done -- a real next experiment, not a guess at the outcome.
