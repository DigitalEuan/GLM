# Golay–MOG periodic-table pilot: E8–E14 report

## Scope

This report records the first reproducible experiment pass following `GOLAY_MOG_PERIODIC_TABLE_PLAN.md`. It tests a fixed Golay/MOG data-object representation against atomic properties. It does **not** yet test compounds or reactions, because those require species, stoichiometry, phase, conditions, and independently sourced endpoint tables rather than element-pair labels.

## Data and provenance

The raw snapshot is `data/raw/pubchem_periodic_table.csv`, downloaded from the PubChem Periodic Table PUG REST CSV endpoint on 2026-08-02. Its SHA-256 is:

`efcadb3dd180bd06fc0fa069a81082e86553ba2b8b5d679b7827bb8c03afd3ce`

It contains all 118 atomic numbers and fields including electron configuration, electronegativity, atomic radius, ionization energy, electron affinity, standard state, melting point, boiling point, density, and group/block. Missing values remain missing; they are never replaced by zero. `data/processed/elements.csv` adds deterministic period and coarse group columns. Units are those documented by PubChem for this table; no unit conversion was performed.

External source:

- PubChem, “Periodic Table of Elements,” National Center for Biotechnology Information, PUG REST periodic-table CSV, accessed 2026-08-02: <https://pubchem.ncbi.nlm.nih.gov/periodic-table/>
- API snapshot endpoint: <https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/CSV>

The Golay convention and fixed MOG permutation come from the supplied `ubp_unified_v5.py`; no external Golay arrangement was silently substituted.

## Representation and configurations

For atomic number `Z`, the experiment forms a 12-bit message from seven low-endian identity bits plus five zero version bits, then encodes it using the supplied systematic extended binary Golay `[24,12,8]` parity block. This deliberately keeps identity independent from measured target properties.

Compared configurations:

1. cubic atomic-number baseline (`z_poly`);
2. raw 12 message bits;
3. raw 24 Golay bits;
4. fixed MOG arrangement with planar, stacked, cylindrical, and spherical embeddings;
5. eight seeded random coordinate permutations with the same aggregate/geometric feature construction.

MOG/3-D features include row and column occupancy, active-bit centroid, axis moments, mean and maximum pair distance, and radius of gyration. Raw cell bits are omitted from the geometry models to keep model complexity modest.

## Validation

Seven endpoints were tested separately: electronegativity, atomic radius, ionization energy, electron affinity, melting point, boiling point, and density. Each uses only rows with an observed target.

The suite runs:

- leave-period-out regression;
- leave-group-out regression;
- shuffled-target negative controls for representative baseline and MOG models;
- four Z-only classification tests (period, group, group/block category, and standard state) with deterministic five-fold splits;
- ridge regression with a predeclared regularization of 10;
- MAE, RMSE, and R²;
- deterministic seeds and complete per-element predictions.

The generated `results/metrics.csv` has 224 result rows. `results/predictions.csv` has 9,675 held-out predictions for the leave-period-out comparisons. `results/classification_metrics.csv` adds 68 classification comparisons.

## Exact audit results

`results/summary.json` records:

- 118 distinct identity codewords;
- 118/118 identity round trips;
- 4,096 distinct Golay codewords;
- weight distribution `1, 759, 2576, 759, 1` at weights `0, 8, 12, 16, 24`;
- all generated codewords satisfy the parity checks;
- the fixed MOG coordinates form a permutation of 0–23;
- rigid rotation/translation changed the tested mean pair distance by only `6.66e-16` (floating-point roundoff).

Lean file `RequestProject/GolayMOG.lean` independently proves identity round-trip, identity injectivity, MOG coordinate bijectivity, and symmetry of XOR interaction.

## Main result

Averaging each configuration's held-out MAE after normalizing by the atomic-number baseline for every endpoint and split, the ranking begins:

| Configuration | normalized MAE |
|---|---:|
| `z_poly` | 1.0000 |
| `message_bits` | 1.0254 |
| `golay_bits` | 1.1001 |
| best random layout (`random_06`) | 1.1152 |
| fixed MOG planar | 1.1682 |
| fixed MOG cylinder | 1.1795 |
| fixed MOG stacked | 1.1870 |
| fixed MOG sphere | 1.1958 |

Thus the optimal tested configuration for this pilot is the simple cubic atomic-number baseline, **not** a MOG geometry. This is a result about these seven atomic endpoints, this model class, and these holdout schemes—not a universal optimum for every Data Object.

There are endpoint-specific variations. For example, fixed planar MOG was second on leave-period-out electron affinity and melting point, while random layouts led electronegativity. Those isolated rankings do not establish a privileged arrangement because they are inconsistent across endpoints and random arrangements can perform similarly or better.

The classification tests likewise do not identify one universal layout. Raw message bits led period classification (balanced accuracy 0.465) and group/block classification (0.193); stacked MOG led the difficult 18-group task (0.077 versus 0.068 for the cubic-Z baseline), but all group scores were low. Standard-state balanced accuracy was 0.2 across the principal configurations because the dominant-class prediction failed to recover minority classes. These are diagnostic results rather than evidence of useful chemical classification.

## Interpretation

The experiment supports using the 12-bit message as the permanent lossless identity layer: it is close to the strongest overall baseline, compact, and exactly invertible. The Golay codeword can be retained as an error-correcting transport/storage layer. On current evidence, geometry should be stored as a versioned, optional view rather than treated as the unique carrier of semantic meaning.

No measured property was encoded into the identity object, so performance here is not produced by directly placing the answer in the bits. Conversely, this minimal identity-only input is not expected to match modern chemistry predictors using electron configuration and measured covariates.

## Recommended default Data Object configuration

Until a task-specific geometry passes stronger controls:

1. **Canonical identity:** atomic number in an explicit versioned 12-bit message.
2. **Integrity layer:** supplied systematic Golay `[24,12,8]` codeword.
3. **Display layer:** fixed 4×6 MOG permutation, clearly labeled as a coordinate view.
4. **Physical/property layer:** typed side-channel fields with units, uncertainty, conditions, source, and missingness—not modulo-wrapped into identity bits.
5. **Interaction layer:** task-specific, symmetric for unordered tasks, and inclusive of stoichiometry/species/phase.
6. **Geometry selection:** compare fixed MOG with random layouts and ordinary baselines under held-out validation; do not reuse the target test set to choose layouts.

This gives data a stable computational “thing” (address + protected codeword + declared coordinates) without forcing all semantic and physical information into one lossy 24-bit object.

## Limitations and next experiments

- PubChem's compact table aggregates heterogeneous measurement provenance and includes predicted/expected entries. A future atomic benchmark should retain per-value citations, uncertainties, and conditions.
- Group assignment for detached f-block elements is a coarse group-3 convention.
- Seven atomic properties do not establish compound or reaction behavior.
- The table is small and periodic groups are uneven; R² can be unstable, so MAE is the ranking statistic.
- Only four fixed 3-D embeddings and eight random layouts were tested.
- No external locked dataset has yet been revealed.

Next, build a clean diatomic dissociation-energy dataset, then a phase-specific binary formation-enthalpy dataset. In both cases preserve species identity and stoichiometry and use leave-element/composition-family-out validation. Only after that should complete balanced-reaction prediction be attempted.

## Reproduction

From the project root:

```bash
python3 golay_mog_experiments.py --run
python3 -m unittest discover -s tests -v
lake build RequestProject.GolayMOG
```

The first command regenerates the processed data and all CSV/JSON result artifacts using only Python's standard library.
