# GLM / UBP Research Session — Full Summary

Everything below was actually run, not estimated. Numbers are real, taken
directly from executed code against your real codebase (`core_studio_v4.0`,
`ubp_unified_v5.py`, `ubp_kb_architect.py`, `ubp_observer_dynamics.py`) and,
where noted, the v3.16.0 update you pushed mid-session. Verdicts are stated
plainly: ✅ real/positive, ❌ clean null, ⚠️ real-but-caveated, 🔧 methodology
note.

---

## 1. Natural-language output quality (v3.9.0, first pass)

Built `GLM19_prose_composer.py` — an additive module producing long-form
prose instead of GLM10's terse bracket-tag output, without touching any
existing tested code path (24/24 self-tests, 28/28 golden cases unchanged).
Real before/after example on "what is time?": tagged output ~30 words vs
prose output ~70 words, same underlying data, fuller definitions retained
instead of clipped to first sentence. ✅ You later integrated this into
v3.16.0 as `chat_prose()`.

## 2. Can GLM "learn" toward LLM-like behavior? (Experiments A–H)

| # | Test | Result | Verdict |
|---|---|---|---|
| A | Held-out n-gram generalization | Bigram 12.59% vs 5.76% baseline (1,295/10,290) | ✅ real signal, tiny corpus |
| B | Hamming distance vs grammatical role | d=0.36 on 75 non-noun words | ⚠️ real but tiny sample |
| C | NRCI vs real corpus frequency | ρ=0.0092 | ❌ flat null |
| D | Naive PMI-sign vector construction | ρ=+0.174 (wrong sign) | ❌ construction doesn't work |
| E | Golay structure in existing vectors | 5.76% exact codewords (236x random-chance enrichment), but 310/311 are chemical elements only | ⚠️ real but fully concentrated in one hand-built subsystem |
| F | Proper SVD/LSA embedding | ρ=−0.220, correctly signed | ✅ first construction that actually works |
| G | Snap SVD vectors to nearest codeword | 82.8% nominal retention, but 43.8% of vectors were uncorrectable and left unchanged (blended figure, not clean) | ⚠️ caveated |
| H | Can gradient-based ML learn Golay codeword membership? | LogReg 48.44%, RandomForest 20.48%, MLP 100%train/56.74%test — all ≈chance | ❌ clean null, theoretically expected (parity-function hardness) |

## 3. Fringe / non-standard methods (Experiments I–K)

| # | Test | Result | Verdict |
|---|---|---|---|
| I | Gray-code re-encoding for Exp H's task | 74.18%±2.0% vs 49.35%±4.7% across 5 seeds — real, robust | ⚠️✅ real effect, but exact GF(2) analysis showed the "reduced parity order" explanation is **wrong** (mean syndrome weight went *up* under Gray transform, 8.33→12.00) — mechanism still unexplained |
| J | GF(2) Gaussian elimination (exact linear algebra, not ML) | 100.00% held-out accuracy from exactly 12 labeled codewords, every time | ✅ dramatic, clean, exact — the right tool for a linear code |
| K | Genuine Leech lattice embedding | Blocked before running: verified construction needs a real Golay codeword input + extra parity-constrained integers; only 5.76% of vocabulary qualifies | 🔧 scoping finding, not a null — needs real codewords to lift from, which mostly don't exist yet |

## 4. Testing your v3.16.0 update against its own documentation

Reproduced independently, not taken on faith:
- **26/26 self-tests, 41/41 golden cases** — confirmed exactly. ✅
- **Golay/Leech engines are genuinely real**, not stubs. ✅
- **All 6 new experiment scripts** (`exp_l/m/n/o/p`, `exp_g_followup`) fail immediately on a fresh clone — hardcoded path to an uncommitted `glm_work/` directory. ❌ real reproducibility gap
- **SVD-embedding result (Exp F) is hyperparameter-fragile** — re-implementing with different but reasonable window/frequency choices swung the correlation from −0.220 to +0.06, sign and all. ⚠️
- **Continuous learning causes uncaught output drift** — corrected from an initial overstatement: it's not "a different topic recalled," it's a fixed 3-candidate recall list's *order* flipping after enough accumulated learning (stable runs 1–3, flips at run 4). Self-tests pass either way because assertions are loose. ⚠️
- **`chat_prose()` is genuinely good on isolated queries**, confirmed via fresh-instance control, but has **cross-topic bleed in multi-turn conversations** (confirmed via controlled A/B). ⚠️✅
- **`generate_grammatical()` produces incoherent word-salad**, confirmed on a completely fresh instance (not drift I caused): *"Time ent beweeping. Beweeping minus_eleven over."* ❌

## 5. Directed curriculum vs random reinforcement (`test_directed_framework.py`)

Built a real, controlled test: does deliberately co-occurring a target word
with *chosen* semantic partners produce better learning than the same
volume of random partners? Fixed 3 real bugs found along the way (protected
ubp_id categories silently blocking refinement; learned edges never
re-applied to the live graph on reload; no flush-on-exit save losing up to
4 queries per session). Final controlled result on `river`, 60 queries each:

| Condition | avg_log_prob | vectors_refined |
|---|---|---|
| baseline | −9.1855 | 0 |
| directed (real semantic partners) | −9.1857 | 15 |
| random × 6 seeds | −9.1854 to **−8.9617** (best of all 7) | 7–41 |

**Directed sat inside the random spread, not above it** — one random seed
produced a byte-for-byte identical vector to directed despite completely
different input; the best-scoring condition overall was random. ❌ Clean
null: the refinement mechanism (average→median-split→quadrant-preserving
Golay-snap) discards the semantic distinction between "chosen" and
"random" partners before it can matter.

## 6. Ontological-layer reorganization (Reality/Information/Activation/Potential)

Verified the real 4-layer structure from `gravity/04/d3_layer_grammar_theory.py`
(bits 0-5/6-11/12-17/18-23) and the real `ObserverDynamicsEngine`. Built a
parallel construction swapping grammar-role for ontological classification,
reusing GLM23's exact SVD+Golay machinery unchanged.

| Construction | ρ | Significant? |
|---|---|---|
| Plain SVD (no forcing) | −0.2473 | yes (p=9e-112) |
| Ontology-aligned (new) | −0.0014 | no (p=0.90) |
| Grammar-aligned (production) | −0.0094 | no (p=0.40) |

❌ Same failure either way — the destructive step is **quadrant-forcing
itself**, not which label picks the quadrant. Decomposition confirmed this
precisely: quadrant-forcing alone → ρ=−0.0022 (dead); Golay-snap alone →
ρ=−0.1859 (mostly alive, ~75% of plain-SVD signal retained).

## 7. MOG-grounded vectors — full data, no forcing

Audited the codebase per your redirect and found `MOG_CATEGORIES` — a real,
already-existing 24-name schema (Mass/Charge/Space/Time/Thermal/Count/
Topology/Symmetry/Density/Connectivity/Dimension/Complexity/Energy/Force/
Velocity/Flux/Resonance/Spin/Probability/Ratio/Limit/Tax/Coherence/Phase)
— pervasively computed but only ever used to *label* a vector after
construction, never to build one. Built real keyword-grounded scoring
against all 24 actual names, kept as full continuous data (no dominant
quadrant), snapped only at the end.

**Result: ρ=−0.0814, p=3.16e-13.** ✅ Statistically solid, decisively beats
both "aligned" methods — but weaker than plain SVD, for two identified,
fixable reasons: 58% of words got zero keyword signal and fell back to SVD
(coverage gap in the hand-authored keyword lists), and two differently-scaled
signals were mixed in one un-normalized median split.

## 8. Tilt mechanism (`ubp_kb_architect.calculate_tilt`)

Verified the real formula: 24-bit vector → 3 octet sums (bits 0-7/8-15/
16-23) minus 4 each → normalized 3D vector → angle from a fixed reference
direction (`UNIVERSAL_NORTH`). Sanity-checked against known cases.

| Vector source | Tilt-distance ρ | Full Hamming ρ |
|---|---|---|
| Plain SVD | −0.0472 (p=2.4e-05) | −0.2473 |
| MOG-grounded | −0.0457 (p=4.3e-05) | −0.0814 |
| Grammar-aligned (forced) | −0.0002 (p=0.98, dead) | −0.0094 (dead) |

**Partial correlation (Tilt's unique contribution after removing what
Hamming distance already explains): −0.0216, p=0.0534.** ⚠️ Real signal,
consistently weaker than full Hamming distance, mostly (not entirely,
borderline-inconclusively) redundant with it. Best honest use: a cheap
single-scalar triage/pre-filter, not a standalone semantic carrier — and
it dies under quadrant-forcing exactly like everything else.

## 9. Addendum — "Rosetta Study" verification

You asked me to check this if useful, so I verified it the same way as
everything above rather than take the numbers on trust:

- **All Tilt values and Hamming distances in the document are independently
  reproducible** from the real vectors using the real `calculate_tilt`
  function — confirmed by recomputing them myself. Not fabricated.
- **Hamiltonian/Wavefunction sharing an identical Tilt (67.0331°) is real**
  — but it's 1 collision out of 231 possible pairs among the 22 listed
  concepts, and both vectors happen to share the same 3-octet imbalance
  pattern (−1, 0, 1) despite being different 24-bit vectors overall. Worth
  treating as suggestive, not yet strong statistical evidence, given how
  coarse Tilt's compression is (Section 8).
- **The "Dodecad"/"Octad" classification is internally consistent with raw
  Hamming weight** (Dodecad-labeled vectors do have weight exactly 12;
  Octad-labeled has weight 8) — **but none of the checked vectors are
  actually valid Golay codewords** (syndrome_weight ≠ 0 for all of
  Hamiltonian, Wavefunction, Tensor, Divergence, Zero Point). So the
  terminology describes raw bit-weight, not genuine code membership — the
  same distinction Exp E already established (only the deliberately-built
  element vectors are real codewords).
- The interpretive claims (phase-lock, deriving the Schrödinger equation
  from lattice alignment, proposed laws) are a layer on top of these
  verified numbers that the arithmetic alone doesn't establish either way
  — I can confirm the computation, not the physics thesis.

---

## Overall synthesis

Three things are now solid, cross-confirmed findings, not single
experiments:

1. **Real semantic signal exists and is recoverable** from your actual
   corpus (n-grams, SVD/PMI embeddings, MOG-category keyword grounding all
   independently found it, always in the −0.05 to −0.25 ρ range depending
   on method).
2. **Quadrant-forcing (picking one dominant 6-bit range, zeroing the rest)
   is the specific, identified, repeatedly-confirmed destroyer of that
   signal** — confirmed across grammar-role assignment, ontology
   assignment, and directly via decomposition. It doesn't matter which
   label picks the quadrant; the forcing step itself is the problem.
3. **Golay-snapping alone is comparatively benign** (~75% signal retention)
   and is a real, necessary constraint (confirmed via Lagrange-multiplier-
   style reasoning and the GF(2) exact-recovery result) — it should stay;
   quadrant-forcing should not, at least not in its current form.

## File manifest (everything produced this session)

- `GLM19_prose_composer.py`, `GLM11_runtime.diff`, `GLM11_runtime_MODIFIED.py` — prose output integration
- `glm_experiments/EXPERIMENT_LEDGER.md` + saved datasets — Experiments A–K
- `test_directed_framework.py` + `directed_framework_test/` — curriculum test, all raw results
- `v316_curriculum_experiment/` — earlier v3.16.0-specific curriculum findings
- `experiment_ontological_vectors.py` + `ONTOLOGICAL_LAYER_FINDINGS.md`
- `experiment_mog_grounded_vectors.py` + `MOG_GROUNDED_FINDINGS.md`
- This file — full session summary
