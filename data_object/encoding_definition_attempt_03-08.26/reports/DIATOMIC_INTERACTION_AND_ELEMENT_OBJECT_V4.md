# Gas-phase diatomic interaction pilot and structured Element Object v4

## Scope

This round does two things that earlier relationship tests deliberately did not:

1. tests a real interaction endpoint, neutral gas-phase diatomic dissociation energy at 0 K (`D0`), under complete-element holdout; and
2. defines an Element Knowledge Object whose spatial views organize actual identity, electronic-configuration, and observation records rather than treating geometry as the information itself.

The two outputs remain separate. A chemical element is not a molecule; the interaction dataset references two element identities and a particular molecular state.

## Endpoint dataset

The source snapshot is NIST Computational Chemistry Comparison and Benchmark Database (CCCBDB), **Experimental Atomization Energies**, retrieved 2026-08-03. For a neutral diatomic at 0 K, atomization into ground-state atoms is its dissociation endpoint `D0`.

The processed table has 52 neutral gas-phase species spanning 19 elements. Every row records:

- molecular formula and both element participants;
- total charge (zero in this locked pilot);
- selected electronic record (CCCBDB state 1/configuration 1, used as the ground-state record);
- gas phase and 0 K endpoint condition;
- `D0` in kJ mol⁻¹;
- reported uncertainty, or explicit `not_reported` missingness;
- row-level provenance.

Fifty-one of the 52 values have a source uncertainty in the returned table. H₂ has no displayed uncertainty; it remains missing rather than being interpreted as zero. The raw HTML selection and result pages are retained under `data/raw/nist_cccbdb/`. The processed table is `data/processed/diatomic_dissociation_0k.csv`.

This is a source snapshot, not an exhaustive CCCBDB extraction. The selected species were fixed before the predictive run, and rows without a 0 K value were excluded by the endpoint definition.

## Predeclared interaction operators

The operators were fixed in source before model fitting and are symmetric because participant order should not affect a diatomic `D0`:

- **A — co-presence:** coordinate sum, `x + y`;
- **B — contrast:** coordinatewise absolute difference, `|x − y|`;
- **C — coupling:** coordinatewise product, `x · y`.

The same names are used consistently in Python and Lean. Lean proves all three are symmetric and proves that self-contrast B is zero. Zero contrast means identical inputs, not zero physical binding.

For the fixed Leech variants, the eight numeric element channels are standardized and embedded at the previously declared deterministic Class A, B, or C addresses. A is applied to the Class-A embedding, B to Class B, and C to Class C. `fixed_ABC` concatenates all three. Sixteen random address assignments per shape class are norm-matched controls. Ordinary baselines are a training mean, cubic atomic-number pair descriptors, and A/B/C applied directly to the eight standardized raw element properties.

## Leakage controls and model

Each fold holds out one complete element. Every molecule containing that element is excluded from training, including homonuclear and heteronuclear species. Imputation means and scales are refit from only the elements appearing in that fold's training molecules. Test molecules are never used in fitting or preprocessing.

The model is ridge regression with fixed λ = 10. There is no endpoint-driven hyperparameter selection, address selection, or operator search. Metrics are macro-averaged over the 19 held-out-element folds so heavily represented elements do not silently dominate.

## Results

Macro held-out-element errors:

| Representation | MAE (kJ mol⁻¹) | mean fold RMSE (kJ mol⁻¹) |
|---|---:|---:|
| Training mean | 167.26 | 191.65 |
| Atomic-number A/B/C | 177.99 | 202.79 |
| Raw properties A/B/C | 122.33 | 140.72 |
| Fixed Class-A / operator A | 116.17 | 133.97 |
| Fixed Class-B / operator B | 140.55 | 163.77 |
| Fixed Class-C / operator C | 144.85 | 165.77 |
| Fixed A+B+C | 135.53 | 159.95 |

Random-address controls, macro-MAE across 16 assignments:

| Family | Mean | Minimum | Maximum |
|---|---:|---:|---:|
| A | 120.16 | 107.19 | 136.55 |
| B | 153.32 | 131.34 | 178.17 |
| C | 139.41 | 111.84 | 156.47 |

The fixed Class-A additive representation beats the raw-property baseline in this pilot by 6.16 kJ mol⁻¹, but it does **not** beat the best random Class-A assignment and its result lies within the random-control range. Fixed B is worse than raw properties. Fixed C is worse than raw properties and also worse than the random-C mean. Concatenating fixed A/B/C does not improve on fixed A or raw properties.

Therefore this endpoint confirms that the pipeline can represent and test a genuine molecular interaction without element leakage, but it does not establish a chemically privileged Golay/MOG/Leech geometry. Most predictive content still enters through measured atomic side channels. The sample is small and coverage is uneven, so these errors are a pilot result, not a deployable predictor.

All fold metrics and predictions are available in `results/diatomic_complete_element_holdout.csv` and `results/diatomic_predictions.csv`; the machine-readable summary is `results/diatomic_interaction_summary.json`.

## What an Element Object must embody

A successful object needs an explicit ontology, not merely enough coordinates. The v4 structure separates six concerns:

1. **Canonical element identity.** Atomic number is the key. Symbol and name are labels. Gray/Golay/MOG data is a versioned integrity/coordinate view, not the definition of the element.
2. **Electronic ground-state model.** The supplied electron configuration is parsed into orbital occupancies and audited so neutral electron count equals atomic number. It is a sourced state model, not immutable identity.
3. **Typed observations.** Every measurement retains value, unit, missingness, uncertainty, conditions, provenance, and the three exact 24-dimensional Leech address references.
4. **Explicit spatial views.** Nine stacked 4×6 layers form a declared 3D arrangement: one Golay identity layer (`z=0`), seven principal-shell layers (`z=1…7`), and one observation-index layer (`z=8`). Every layer states its origin, axes, spacing, MOG convention, and cell semantics.
5. **Exact geometry versus visualization.** Leech addresses stay in exact 24-dimensional integer coordinates. The stacked MOG is an indexable 3D view. A silent 24D→3D projection would lose information and could create artificial distances, so it is not treated as lossless geometry.
6. **State boundary and links.** Isotopes, ions, excited states, phases, molecules, and interaction events are separate typed objects referencing `element:<atomic number>`. They must not overwrite the element record.

Multiple MOG grids are useful when each grid has one declared semantic role. Adding more grids without a typed role only duplicates addresses and increases opportunities for accidental correlations. In v4, spatial adjacency is therefore a hypothesis available to later models—not an asserted chemical law.

The generator is `structured_element_data_objects.py`; the schema, all 118 generated objects, and exact audit are in:

- `schemas/element_data_object_v4.json`;
- `data/objects/elements_v4.jsonl`;
- `results/structured_element_audit.json`.

The audit confirms 118 unique identities, nine layers per object, neutral electron-count agreement for all 118 records, even-weight Golay words, and A/B/C exact addresses on every observation.

## Recommended next gate

Before geometric expansion, enlarge and freeze the interaction corpus with independently reviewed state labels and dissociation channels. Then use an untouched final set of elements, not only repeated cross-validation, and compare:

- raw atomic measurements plus explicit electronic occupancies;
- learned permutation-invariant pair models;
- fixed MOG/Leech operators;
- multiple random-address controls;
- uncertainty-weighted and unweighted scores.

Only promote a geometry if it beats ordinary chemistry features and the distribution of random layouts on the untouched element set. The v4 object can support that test because it separates identity, state, observations, geometry, and interaction events cleanly.
