# UBP ontology applied to the Element–MOG interaction pilot

## Status and authorship boundary

This round evaluates the supplied **Universal Binary Principal (UBP) v5.4.1** perspective against the existing Element Data Object and diatomic-bond pilot.

> **ARISTOTLE EXPERIMENTAL CONTRIBUTION:** the operational definitions, leakage-controlled experiment, controls, analysis, software tests, formal lemmas, and this report were added in this round. The UBP five-pillar perspective, Golay/MOG/Hexacode implementation, TAX formula, NRCI formula, and 0.500 “coherence horizon” came from the supplied materials and were not silently changed.

The goal is constructive but falsifiable: retain the ontology where it gives exact structure, then test whether its derived quantities add held-out chemical information.

## 1. What was made operational

The following route was fixed before fitting the endpoint:

1. **Subject identity:** atomic number `Z` from the v4 Element Data Object.
2. **Gray translation:** 12-bit reflected Gray identity.
3. **Golay state:** systematic extended binary Golay `[24,12,8]` encoding.
4. **Observer view:** the supplied fixed cyclic-to-MOG permutation.
5. **Grammar view:** six MOG columns decomposed into their GF(4) Hexacode symbols and four-bit column patterns.
6. **State scoring:** supplied TAX and NRCI formulas.
7. **Interaction/trajectory:** XOR of the two element codewords, alongside symmetric A/B/C composition of participant descriptors.
8. **Endpoint:** the retained 52-record neutral gas-phase diatomic dissociation-energy (`D0`, 0 K) table.

This preserves the project’s ontology boundary: elements are subjects; a bond measurement belongs to a species-resolved interaction record. An XOR of identical identities means zero **identity contrast**, not zero physical interaction.

### Descriptor components

For each participant and XOR transition, the experiment derives:

- Golay Hamming weight;
- TAX and NRCI;
- four MOG row occupancies;
- six MOG column occupancies;
- counts of the four Hexacode symbols;
- Hamming weights of the six column patterns.

Participant features are combined symmetrically with coordinate sum, absolute difference, and product. The XOR transition is also symmetric. Consequently, swapping a diatomic’s element labels cannot alter its descriptor.

## 2. Controls and validation

The validation design is complete-element holdout. For each of the 19 represented elements, every species containing that element is excluded from training. Missing-value imputation and scaling for measured atomic channels are refit using training species only.

The compared configurations are:

- training mean;
- the earlier raw measured atomic-property A/B/C descriptor;
- UBP permutation-invariant quantities (weight/TAX/NRCI);
- fixed MOG/Hexacode UBP descriptor;
- raw properties plus fixed UBP descriptor;
- 16 seeded random coordinate permutations with the same UBP feature construction.

The random permutations are essential. MOG row/column occupancy changes under coordinate assignment, so a fixed-layout score is only informative if it improves on the corresponding random-layout distribution.

No endpoint values were used to choose a layout, feature family, ridge penalty, or horizon.

## 3. Exact structural findings

### 3.1 Hexacode validity is an encoding invariant

All 118 element identity codewords have valid Hexacode shadows under the supplied alignment: **0 invalid out of 118**. The supplied implementation also exhaustively verifies all 4,096 Golay codewords.

This confirms consistency of the selected Gray → Golay → MOG → Hexacode route. It does **not** discriminate chemical behavior: validity follows from encoding every element as a Golay codeword.

### 3.2 TAX and NRCI collapse to Hamming weight on binary states

The supplied score is

`TAX(v) = HW(v)·Y + ||v||²/8`.

For a binary vector, every coordinate satisfies `x² = x`, hence `||v||² = HW(v)`. Therefore

`TAX(v) = HW(v)·(Y + 1/8)`

and

`NRCI(v) = 10 / (10 + TAX(v))`.

Thus, on these binary Golay states, TAX is a positive linear rescaling of Hamming weight and NRCI is a monotone transform of the same single quantity. They are useful transparent summaries, but they do not add independent information to Golay weight.

The new Lean development proves TAX monotonicity for nonnegative `Y`, and proves an exact sufficient condition under which all binary states of weight at most 16 lie above the 0.500 horizon.

### 3.3 The 0.500 horizon does not separate these element states

The 118 identity-code weights are:

- weight 8: 70 elements;
- weight 12: 47 elements;
- weight 16: 1 element.

Their NRCI range is approximately **0.6160–0.7623**, so **all 118 exceed 0.500**. Adjacent-element XOR transitions have weight 8 (59 transitions) or 12 (58 transitions), and likewise all exceed the horizon.

For this representation, the horizon is therefore an automatic acceptance condition rather than a chemically selective criterion. It should not be used as a bond-stability label without a separately calibrated, prospective rationale.

## 4. Held-out diatomic result

Macro-average over the 19 held-out-element folds:

| Configuration | MAE (kJ mol⁻¹) | RMSE (kJ mol⁻¹) |
|---|---:|---:|
| Training mean | 167.26 | 191.65 |
| Raw measured properties A/B/C | **122.33** | **140.72** |
| UBP invariants only | 146.72 | 169.87 |
| Fixed MOG/Hexacode UBP | 232.44 | 262.82 |
| Raw + fixed UBP | 167.76 | 194.78 |

For the 16 random MOG coordinate controls, macro-MAE was:

- mean: **205.50 kJ mol⁻¹**;
- minimum: **157.36 kJ mol⁻¹**;
- maximum: **245.12 kJ mol⁻¹**.

The fixed UBP MOG descriptor performs inside the random-layout range and worse than its random-layout mean. Adding it to measured atomic properties degrades this small-sample held-out result. The compact invariant descriptor is better than the training mean but remains substantially worse than measured properties.

Accordingly, this experiment finds no evidence that the fixed UBP MOG/Hexacode layout adds privileged predictive information for this endpoint. This is a result about one small endpoint and one declared operationalization—not a general rejection of Golay, MOG, Hexacode, Leech geometry, or the broader ontology.

## 5. What the ontology contributes now

The ontology is useful in several concrete ways even though this prediction test is negative:

1. **Layer discipline:** Gray identity, Golay integrity, MOG view, Hexacode grammar, Leech address, observations, and interactions remain distinguishable rather than being conflated.
2. **Exact invariants:** code validity, distances, row/column counts, class membership, and symmetry can be audited deterministically.
3. **Trajectory/state distinction:** participant states and XOR contrast are represented separately.
4. **Candidate scoring discipline:** TAX/NRCI can be treated as explicit engineered scores and compared fairly with simpler quantities.
5. **Falsifiability:** random-layout controls reveal whether coordinate placement, rather than feature capacity alone, contributes reusable signal.

The key refinement is to describe TAX/NRCI as ontology-native scores unless and until an external experiment calibrates them to a physical observable. Calling them literal mass, gravity, energy, or chemical coherence would currently go beyond the evidence in this project.

## 6. Recommended next experiments

### A. Pre-register a larger interaction endpoint

Use hundreds or thousands of consistently defined species—preferably one phase and one thermochemical endpoint—with charge, state, stoichiometry, temperature, uncertainty, and provenance. Retain complete-element and scaffold/composition-family holdouts. The present 52 records are too sparse for a broad representation search.

### B. Test grammar as a perturbation-recovery mechanism

Hexacode validity is guaranteed for encoded states, so validity itself cannot predict chemistry. A meaningful test is instead to inject declared bit errors or measurement-channel corruption, decode without seeing the target, and measure whether Golay/Hexacode recovery improves downstream prediction relative to matched generic error-correcting and repetition-code controls.

### C. Learn only on training folds, then freeze

If chemical channels are to be assigned to MOG rows or Leech addresses, choose the assignment using training folds only, freeze it, and compare on untouched elements against many random assignments. This distinguishes ontology-guided discovery from retrospective semantic labeling.

### D. Calibrate state and trajectory scores separately

For reactions, define a state score for each typed species and a trajectory score for the balanced event. Require conservation and stoichiometry first. Compare TAX/NRCI-derived deltas with ordinary descriptors such as electron-count change, bond-order change, charge separation, and measured thermochemistry.

### E. Treat threshold selection as an empirical model

Do not fix 0.500 as a chemical boundary merely because it is named in the ontology. If a threshold is desired, select it on training data for a predeclared classification endpoint, report calibration and uncertainty, and evaluate it once on a locked test set.

## 7. Reproduction

```bash
python3 ubp_element_mog_experiment.py
python3 -m unittest discover -s tests -v
lake build RequestProject.GolayMOG
```

Generated artifacts:

- `results/ubp_element_mog_summary.json`;
- `results/ubp_element_mog_holdout.csv`;
- `results/ubp_element_mog_predictions.csv`.

The experiment is deterministic under the recorded seed and uses the already retained source data.
