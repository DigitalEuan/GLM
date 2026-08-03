# Golay–MOG / Spatial Arithmetic Periodic-Table Research Plan

**Status:** proposal for refinement before further large-scale computation  
**Scope reviewed:** the attached Python files and the public `data_object` directory of `DigitalEuan/GLM` as available on 2026-08-02.

## 1. Executive recommendation

The project is worth continuing as a **controlled representation-learning experiment**, but the present results do not yet establish that Golay/MOG geometry predicts chemistry.

The strongest defensible interpretation is currently:

- a 24-coordinate MOG display is a compact, structured feature container;
- user-chosen encodings and user-chosen 3D embeddings produce geometric descriptors;
- some descriptors correlate with a small, manually assembled chemistry table;
- those correlations are hypotheses to test on clean, larger, externally sourced data.

The next milestone should not be another broad parameter sweep. It should be a reproducible benchmark that separates:

1. **faithful element identification**;
2. **recovery of periodic structure**;
3. **prediction of held-out atomic properties**;
4. **prediction of compound and reaction outcomes**;
5. **incremental value of MOG/3D features over ordinary chemistry baselines**.

A successful result is not merely a high in-sample correlation. MOG/Spatial Arithmetic features must improve genuinely held-out predictions over equally expressive non-MOG controls, under a search protocol that prevents target leakage and multiple-testing bias.

## 2. What the current repository already contains

The repository has a useful exploratory foundation:

- a 24-bit, 4×6 row-major data-object layout;
- Gray-coded property encodings;
- Golay-code operations and MOG decomposition;
- per-bit candidate 24-dimensional embeddings;
- stacked 3D grids of bit-polygons;
- geometric descriptors such as overlap, clearance, normal alignment, and scene spread;
- results and a chronological E0–E7 test ledger;
- explicit documentation of some null results and one floating-point false positive.

The ledger itself already identifies several important limitations: Golay XOR quantities are strongly quantized, early small-sample effects did not survive expansion, and bond-energy performance has a large train/CV gap.

### Important audit findings before accepting current predictive claims

1. **The labels are not a single physical endpoint.** The 37-row table mixes homonuclear bond dissociation energies, selected bond energies in molecules, ionic lattice-related values, and formation enthalpies of compounds. A pair such as `(Al,O)` does not uniquely identify `Al₂O₃`, its phase, temperature, pressure, stoichiometry, or reaction.
2. **Stoichiometry is discarded.** `H+O`, `C+O`, and `Fe+O` can describe many compounds and bond orders. Formation enthalpy is a property of a specified compound/reaction, not of an unordered element pair alone.
3. **Some zero ΔH values have a different meaning from the other targets.** Standard formation enthalpy zero for an element in its reference state is not the same quantity as a molecular bond energy.
4. **Configuration selection and evaluation reuse the same small dataset.** Row permutations, feature schemes, grid dimensions, and especially polygon seed offsets were searched using the data later used to report performance. Ordinary cross-validation after this search does not account for the search; selection must happen inside each training fold.
5. **The seed/orientation signal is not currently intrinsic.** Polygon orientations come from deterministic pseudo-random rotations, and the best offset was selected from a wide sweep. Until it succeeds in nested validation and on a locked test set, this is a tunable feature map rather than evidence for a privileged physical geometry.
6. **“A_basis” is correctly documented as a control, not a Leech-lattice construction.** Results from it should be named standard-basis geometry, not Leech geometry.
7. **Encoding choices can directly contain the answer.** Electronegativity, radius, and valence are legitimate predictors, but a model cannot then claim to have independently discovered those properties. Every target needs a declared allowed-input set.
8. **Modulo-64 and coarse quantization create collisions.** Distinct physical values can map to the same row or wrap around. Collision tables and sensitivity analysis are required.
9. **Pair orientation is confounded.** The current “B” element was often chosen as the more electronegative atom. Ordered and unordered tasks must be explicitly separated.
10. **Several geometric quantities are constructed to hit operator clearances.** Exact ADD/SUBTRACT/etc. hits show that the codec works as designed; they do not by themselves show chemical meaning.
11. **Correlation is not prediction accuracy.** Pearson `r` omits scale error, bias, uncertainty, and calibration. MAE/RMSE and confidence intervals are needed.
12. **Reproducibility is incomplete.** Scripts contain machine-specific absolute paths, and the element knowledge-base file used to generate key results is not in the reviewed `data_object` directory.

These points do not invalidate the software as an exploratory system. They define the controls needed to find out which effects survive.

## 3. Precise research questions

Replace the broad phrase “predict elemental behavior” with the following staged questions.

### RQ1 — Can a MOG data object identify every element without collisions?

Given atomic number `Z ∈ {1,…,118}`, produce a deterministic, versioned representation with exact round-trip decoding. This is an engineering correctness test, not a predictive test.

### RQ2 — Does MOG geometry recover periodic organization from minimal inputs?

Using only atomic number (and, in a separate experiment, ground-state electron configuration), predict or cluster:

- period;
- group;
- s/p/d/f block;
- valence-shell occupancy;
- metal/metalloid/nonmetal category.

This tests whether the representation preserves periodic structure.

### RQ3 — Does it predict held-out atomic properties?

One target at a time:

- first ionization energy;
- electron affinity;
- electronegativity (with a named scale);
- covalent/atomic/van der Waals radius (kept separate);
- melting and boiling points;
- density and standard-state phase;
- common oxidation states.

For each target, remove that target and any direct transformation of it from the encoder.

### RQ4 — Does pair geometry predict a well-defined binary interaction?

Start with narrow tasks:

- diatomic bond existence, equilibrium distance, bond order, and dissociation energy;
- binary-compound formula/stoichiometry;
- binary-compound formation enthalpy for a specified phase;
- preferred oxidation-state pair;
- whether a documented balanced reaction proceeds under specified conditions.

Do not combine these into one response variable.

### RQ5 — Is any gain specifically due to Golay/MOG/3D structure?

Compare against controls with the same information and similar dimension. A claimed MOG contribution requires reproducible out-of-sample improvement over these controls.

## 4. Representation architecture

Use three explicitly separate layers so identity, chemistry inputs, and geometry cannot be confused.

### Layer A — Lossless identity address

Use `Z` as the canonical identity. Encode it injectively, with a published bit order and round-trip decoder.

Recommended candidates:

- **A0:** 7-bit binary `Z`, padded to 24 bits (simple control);
- **A1:** 12-bit message containing `Z` plus version/parity fields, encoded by one fixed extended binary Golay `[24,12,8]` generator matrix;
- **A2:** Gray-coded `Z` control.

A1 gives a genuine codeword while retaining exact provenance. Publish the generator/parity-check matrices, coordinate order, and bit-endianness. Verify all 118 addresses are unique and decode to their source element.

### Layer B — Periodic/electronic state

Represent physically interpretable categorical state without target leakage:

- period, group, block;
- shell/subshell occupancy;
- valence electron count;
- optional common oxidation-state mask.

Run two modes:

- **discovery mode:** only `Z` is supplied, so periodic properties are targets;
- **application mode:** known electronic properties may be supplied as predictors for downstream chemistry.

### Layer C — Continuous measured properties

Keep continuous values in a versioned side channel rather than forcing every quantity through a 6-bit modulo map. If a 24-bit property object is required, use:

- declared physical units;
- training-only normalization limits;
- saturating rather than wrapping quantization;
- a missing-value mask;
- collision and quantization-error reports.

The existing `[Z, Valence_e, EN, Rad]` vector remains one candidate feature encoding, not the definition of an element.

## 5. MOG arrangements to test

A MOG is first a combinatorial arrangement of 24 coordinates. A 3D embedding is additional structure and must be declared separately.

### 5.1 Canonical combinatorial layer

Fix one reference 4×6 layout and verify:

- index ↔ `(row,column)` is a bijection;
- Golay encoding/decoding and syndrome calculations;
- codeword closure under XOR;
- minimum-distance and weight-distribution checks for the implemented code;
- known octad/dodecad membership tests;
- permutation behavior under declared coordinate relabelings.

### 5.2 Arrangement families

Test arrangement families rather than isolated hand-picked layouts:

1. canonical 4×6 MOG;
2. row/column permutations;
3. coordinate permutations induced by verified Golay-code automorphisms;
4. random coordinate permutations as null controls;
5. property-to-coordinate assignments;
6. learned assignments selected only inside training folds.

Report orbit-equivalent layouts together. If a metric changes under a symmetry that is supposed to preserve meaning, either average over the symmetry orbit or explain why the symmetry is intentionally broken.

### 5.3 3D embeddings

Predeclare a small set:

- planar 4×6 grid;
- two stacked parallel grids;
- orthogonal grid planes;
- cylindrical wrap;
- spherical projection;
- 24-cell-like or other fixed symmetric point clouds where mathematically appropriate;
- random rigid embeddings and random rotations as controls.

Translation and global rotation should not affect intrinsic descriptors. Scale-dependent descriptors must state the length unit. Arbitrary pseudo-random per-bit normals should be treated as learned/random features unless a physical derivation is supplied.

## 6. Spatial Arithmetic descriptor programme

Separate exact codec behavior from candidate chemistry features.

### 6.1 Exact structural descriptors

- Hamming weight and row/column weights;
- syndrome and codeword class;
- octad/dodecad incidence;
- Hamming and symmetric-difference distances;
- row/column cross-correlations;
- automorphism-orbit identifiers.

### 6.2 Euclidean/3D descriptors

- centroid separation;
- pairwise distance spectrum;
- radius of gyration and inertia eigenvalues;
- convex-hull area/volume;
- contact/overlap graph statistics;
- nearest-neighbor and clearance distributions;
- normal-vector alignment distributions;
- chirality/orientation invariants;
- topological summaries of point clouds over a declared filtration.

Prefer full distributions or stable summaries over one cherry-picked statistic.

### 6.3 Interaction constructions

For element objects `A` and `B`, test:

- unordered superposition, explicitly symmetric in `A,B`;
- ordered donor→acceptor construction for directed tasks;
- XOR and other code operations;
- stack separation scans with separation chosen inside training folds;
- rotations averaged over a fixed rotation set;
- minimal/mean interaction over symmetry-equivalent arrangements;
- stoichiometric scenes such as `A₂B₃`, not merely one `A` plus one `B`.

### 6.4 Required invariance tests

For every descriptor declare expected behavior under:

- swapping A/B;
- global translation;
- global rigid rotation/reflection;
- uniform scaling;
- MOG automorphisms;
- reordering atoms of the same species.

Automated metamorphic tests should enforce these expectations.

## 7. Data model and provenance

Create normalized tables rather than embedding labels in experiment scripts.

### Elements

`element_id, Z, symbol, property_name, value, unit, uncertainty, conditions, source_id`

### Species/compounds

`species_id, formula, charge, phase, structure_id, temperature, pressure`

### Bonds

`species_id, atom_types, bond_order, bond_length, dissociation_energy, method, uncertainty`

### Reactions

`reaction_id, balanced_stoichiometry, species_ids, phases, temperature, pressure, delta_H, delta_G, uncertainty`

Every numeric result should retain source, unit, conditions, and missingness. Do not silently replace missing data with zero.

Use authoritative, independently checkable chemistry datasets. Keep raw snapshots immutable and generate a machine-readable data audit containing duplicates, conflicts, unit conversions, exclusions, and hashes.

## 8. Leakage-safe benchmark design

### Splits

Use several increasingly difficult evaluations:

1. **pair holdout:** unseen pairs but possibly seen elements;
2. **leave-one-element-out:** every test pair contains an unseen element;
3. **leave-one-group-out:** tests extrapolation across periodic families;
4. **composition-family holdout:** e.g. oxides or halides held out together;
5. **locked external test:** untouched until model/configuration selection is complete.

Put `(A,B)` and `(B,A)` in the same split. Put multiple measurements of the same compound/reaction in the same split.

### Nested selection

Outer folds estimate generalization. Within each outer training fold, inner folds select:

- property encoding;
- MOG coordinate assignment;
- quantization;
- embedding family;
- seed/rotation set;
- grid spacing and z-offset;
- descriptor subset;
- model hyperparameters.

The locked test set is evaluated once after the protocol and candidate families are frozen.

### Metrics

Regression: MAE, RMSE, median absolute error, `R²`, Pearson/Spearman correlation, calibrated prediction intervals.  
Classification: balanced accuracy, macro-F1, AUROC/average precision where appropriate, log loss, and calibration.  
Ranking: top-k accuracy and rank correlation.

Always report sample count, uncertainty intervals, and per-family errors.

## 9. Baselines and null models

MOG features must be compared with:

1. mean/majority predictor;
2. atomic-number-only model;
3. ordinary tabular features using exactly the same source inputs;
4. periodic-table features (group, period, block);
5. electron-configuration fingerprints;
6. established composition descriptors for compounds;
7. same 24 bits with no MOG geometry;
8. random coordinate permutations;
9. random bit assignments preserving Hamming weight;
10. random rotations/seeds with the same search budget;
11. non-Golay linear codes or random `[24,12]` codes;
12. ablations: Golay only, MOG only, 3D only, and combined.

Match model complexity and tuning budgets. A geometry model does not demonstrate added value if an ordinary regression on the four encoded properties performs equally well.

## 10. Statistical safeguards

- Pre-register primary endpoints and a small primary descriptor set.
- Treat broad geometry/configuration scans as discovery only.
- Correct or control for multiple comparisons; report all attempted configurations.
- Use permutation tests that rerun the complete selection pipeline, not just the final fit.
- Bootstrap at the element or compound level, not at rows that share the same chemistry.
- Report effect sizes and uncertainty, not only p-values.
- Check residuals by group, period, bond type, phase, and stoichiometry.
- Repeat with and without influential families such as hydrogen compounds and metal oxides.
- Use negative controls, including shuffled targets and synthetic datasets with known generating rules.

## 11. Proposed experiment sequence

### E8 — Reproducibility and data audit

**Deliverables:** portable paths, dependency lock, included/versioned data manifest, one command to regenerate every table, unit tests, exact reproduction report for E0–E7.

**Gate:** all published result rows regenerate from declared inputs; unexplained discrepancies are resolved before new claims.

### E9 — Canonical Golay/MOG correctness

Implement and independently verify generator/parity-check matrices, coordinate conventions, all 118 identity encodings, weight enumerator checks, and arrangement invariants.

**Gate:** no collisions, exact round trips, and all algebraic tests pass.

### E10 — Clean chemistry benchmark

Replace the 37-row mixed table with separate atomic, diatomic, compound, and reaction datasets. Normalize units and conditions. Freeze train/validation/locked-test partitions.

**Gate:** a domain-auditable schema with at least enough independent examples per endpoint to support the intended model complexity; otherwise simplify the model.

### E11 — Periodic-table reconstruction

From Z-only and electron-configuration-only inputs, test period/group/block prediction and clustering. Compare MOG, raw-bit, and tabular controls.

**Gate:** quantify where MOG helps, ties, or hurts; no geometry tuning on the test split.

### E12 — Atomic-property prediction

Run one endpoint per experiment with target-excluded encoders and leave-element/group-out validation.

**Gate:** performance and uncertainty reported against simple periodic baselines.

### E13 — Arrangement and symmetry study

Compare canonical, automorphism-equivalent, random-permuted, and learned layouts under nested CV. Determine whether effects are arrangement-invariant or due to coordinate search.

**Gate:** a predeclared arrangement family improves over matched random layouts across repeated outer splits.

### E14 — 3D Spatial Arithmetic study

Evaluate fixed embedding families and invariant geometric summaries. Seeds, offsets, and orientations are either fixed a priori, orbit-averaged, or selected only in inner folds.

**Gate:** improvement survives random-seed controls, permutation testing, and the locked test.

### E15 — Binary compounds and stoichiometry

Construct scenes for candidate stoichiometries and predict formula, oxidation states, phase-specific formation enthalpy, and stability labels.

**Gate:** test on unseen composition families and compare with standard composition descriptors.

### E16 — Reaction model

Represent complete balanced reactions, not pairs. Test reaction enthalpy/free energy and outcome under declared conditions, enforcing conservation and permutation invariance.

**Gate:** external reaction test and calibrated uncertainty.

### E17 — Prospective predictions

Freeze code and parameters, publish predictions for withheld known entries or subsequently measured cases, and reveal outcomes only after commitment.

## 12. Formal and software verification

Use Lean for the exact discrete core, not for empirical correlation claims. Candidate formal targets:

- 4×6 MOG indexing is a bijection with 24 coordinates;
- Gray encoding/decoding round trips on six-bit words;
- the chosen Golay generator maps 12-bit messages to codewords;
- parity checks vanish on generated codewords;
- codewords are closed under XOR;
- minimum-distance and finite weight-enumerator checks;
- identity encoding is injective for `Z=1…118`;
- symmetric interaction definitions satisfy `f(A,B)=f(B,A)`;
- exact operator-code calculations for rational/symbolic configurations.

Python remains appropriate for floating-point geometry and statistics, with cross-language golden test vectors linking it to the formal definitions.

Recommended repository structure:

```text
data/raw/                 immutable source snapshots
data/processed/           generated normalized tables
schemas/                  machine-readable schemas
src/encoding/             identity/property encoders
src/golay/                matrices, MOG, automorphisms
src/geometry/             embeddings and invariants
src/models/               baselines and MOG models
experiments/E08_.../       frozen configs and outputs
tests/                    unit, property, metamorphic tests
formal/                   Lean definitions and proofs
reports/                  generated result cards
```

Each run should save configuration, input hashes, software revision, random seeds, selected features, fold assignments, predictions, and metrics.

## 13. Decision rules

### Evidence supporting the approach

Proceed toward application if, on a locked test set:

- MOG/Spatial features repeatedly improve appropriate error metrics over matched tabular and random-layout controls;
- gains survive leave-element/group/family-out splits;
- selected arrangements are stable or interpretable;
- predictions have calibrated uncertainty;
- improvements reproduce from a clean checkout.

### Useful negative result

If MOG features do not beat controls, retain the framework as a visualization/error-correcting codec if it is useful, but do not describe it as a chemistry predictor. A negative result still tells us which structure is representational rather than predictive.

### Stop/rethink conditions

Rethink the model if performance disappears under nested selection, depends on one seed/layout, fails target shuffles, relies on target-derived inputs, or does not survive a chemistry-family holdout.

## 14. Questions for refinement

1. Which first endpoint matters most: periodic classification, atomic properties, diatomic bonds, binary compounds, or complete reactions?
2. Should the primary scientific claim be that MOG is a useful **representation**, or that its geometry adds predictive information beyond the encoded chemistry?
3. Is the full element knowledge-base and the script that generated the “KB-hardened” vectors available for a reproducible E8 audit?
4. Should an element have one permanent identity codeword, with measured properties in separate layers, or may its 24-bit object change with the task?
5. Which 3D embeddings have a theoretical motivation that should be privileged over controls?
6. Are predictions intended for neutral ground-state atoms only, or also ions, isotopes, excited states, phases, and environmental conditions?

## 15. Recommended immediate scope

The fastest rigorous next step is **E8 + E9 + a small E10 pilot**:

1. make the existing pipeline portable and reproduce its results;
2. freeze the exact Golay/MOG conventions and prove the discrete indexing/core invariants;
3. build one clean endpoint dataset—preferably diatomic dissociation energy or one phase-specific binary-compound formation-enthalpy table;
4. compare the current dual encoding against simple tabular, raw-bit, random-layout, and random-seed controls using nested leave-element-out validation;
5. only then choose which 3D configuration family deserves a larger computation.

This sequence preserves the creative geometric search while making a positive result scientifically distinguishable from encoding leakage, small-sample noise, and configuration selection.