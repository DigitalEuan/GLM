# Fundamental-first UBP, knowledge-base, and geometry audit

## Status and purpose

This round responds to four refinements: use a context-dependent NRCI level near 0.7; use the Element records in `ubp_system_kb.json`; inspect the constants and particle module before returning to elements; and make the MOG/Leech/3D/physical-channel relationship explicit.

The supplied UBP implementation and knowledge base are unchanged. The standardized extractor, dependency audit, held-out test, Y-twin operationalization, controls, and this report are experimental additions.

## 1. Coherence: absolute and peer-relative

An absolute reference of **NRCI = 0.7** is now reported, not silently treated as a universal physical phase transition. On the 118 stored element vectors:

- 49 pass NRCI ≥ 0.7;
- 69 do not;
- the only stored NRCI levels are approximately 0.762346, 0.681380, and 0.615961, inherited from vector weights 8, 12, and 16.

A separate peer-relative rule is also reported:

`NRCI(subject) ≥ 0.7 × median NRCI(peer group)`.

Peer groups are calculated both by period and by declared chemical class. Every stored element passes this permissive relative rule. That is informative about calibration: multiplying a group median by 0.7 creates a cutoff below even the lowest stored class. It therefore cannot discriminate these records. A useful future relative score should instead be calibrated for a declared endpoint, or expressed as a robust standardized deviation from the peer median.

The two notions must remain separate:

1. **absolute NRCI** compares the score with 0.7;
2. **relative coherence** compares a subject with a declared, versioned peer population and measurement method.

Neither is currently established as physical coherence by an external experiment.

## 2. What the KB Element `mog_tensor` contains

The file declares eight top-level fields; the field referred to as “math” is named `mog_tensor` in this snapshot. It contains 118 tagged Element entries, ordered and cross-checked by atomic number.

A standardized, lossless table was generated at `data/processed/ubp_kb_elements_standardized.csv`. Rational values remain exact strings/Fractions. The five safely aligned core channels are:

- atomic mass;
- boiling point;
- melting point;
- atomic number;
- density.

All five are populated in all 118 Element entries. However, the KB does not declare their units, per-value uncertainty, conditions, or per-value provenance. “Complete” therefore means structurally populated, not metrologically complete.

### Schema issue found

Several tensor category lengths do not match their `_params` tables:

- `M_Charge`: stored 45, declared 47;
- `M_Time`: scalar stored, 2 declared;
- `I_Connectivity`: scalar stored, 1 declared;
- `I_Complexity`: stored 742, declared 780;
- `A_Energy`, `A_Force`, `A_Velocity`: scalar stored, 1 declared.

Positional names in these categories can shift or be undefined. The extractor consequently refuses to assign parameter names there. This is the monitoring rule to retain: a category is positionally decoded only when its observed tensor length exactly equals the declared parameter count.

Recommended KB revision:

- replace positional arrays with named channel objects;
- give every channel `value`, `unit`, `condition`, `uncertainty`, `source`, and `status`;
- distinguish measured, calculated, imputed, ontology-derived, and missing values;
- preserve zero as a real value by using `null` for missingness rather than a global numeric null token.

## 3. Fundamental constants before particle and element layers

The implementation constructs finite continued-fraction rational approximations to π, φ, and e. At ordinary floating precision they agree with the standard library values, but the important qualification is:

> The resulting Fractions are exact rational numbers; they are not exactly equal to the irrational constants.

The dependency chain is:

- `Y_INV = π + 2/π`;
- `Y = 1/Y_INV`;
- `Y_CONST = 1/(Y_INV + 2/Y_INV)`;
- `MONAD = π φ e`;
- `WOBBLE = fractional_part(MONAD)`;
- `SINK_L = WOBBLE/13`.

This layer is deterministic and auditable. It does not by itself show that a derived quantity is a physical constant; that requires dimensional consistency and independent empirical validation.

## 4. Particle formula audit

The two supplied formula tables were reproduced exactly as implemented:

- 9 canonical φ-grammar formulae;
- 21 ultimate-atlas formulae.

For the canonical table, 2/9 formulae have reported relative error below 0.1%, 5/9 below 1%, and 3/9 have error at or above 100%. The ultimate table's mean reported relative error is about 0.11455%.

These values are **formula reproduction, not held-out prediction**. The source contains empirical target scales and hand-selected coefficients. In particular:

- an electron target is assigned and propagated into several masses;
- `Xicc++` is an explicit anchor whose prediction equals its hard-coded target;
- a Z-boson scale and other empirical quantities occur in downstream formulae;
- coefficients and “lenses” have not been selected in training folds and evaluated once on unseen quantities.

The large errors in several canonical formulae are valuable: they show that deriving expressions from a common π/φ/e substrate does not automatically force agreement. The next valid particle-level gate is prospective:

1. freeze a grammar and coefficient-selection rule without using the test targets;
2. use dimensional units explicitly;
3. fit/select only on a declared training set;
4. predict a locked set of quantities or newer measurements;
5. compare with simple dimensional-analysis and parameter-count-matched baselines.

## 5. KB Element pilot on the existing interaction endpoint

The four non-identity KB channels (mass, boiling point, melting point, density) were standardized using training elements only, symmetrically composed with A/B/C, and evaluated on the retained 52 neutral gas-phase diatomic D0 records using 19 complete-element holdouts.

Macro held-out-element MAE:

| Configuration | MAE (kJ mol⁻¹) |
|---|---:|
| Training mean | 167.26 |
| Standardized KB channels A/B/C | 164.29 |
| KB channels with Y-twin A/B/C | 164.31 |

The KB channels improve only slightly on the training mean and are much worse than the earlier typed raw-property result (122.33 kJ mol⁻¹). The Y twin does not improve the result.

The declared twin is

`T_Y(x) = (x, Yx)`.

This is a transparent feature map, not a newly discovered dimension. Since the first half is exactly `x` and the second half is a fixed scalar multiple, it contains no new information. Its value is as a controlled implementation of the mirroring proposal. A nontrivial twin test needs a separately specified transformation whose parameters are frozen without using the endpoint.

## 6. Geometry model: what is exact and what is a view

A disciplined model has four different layers:

1. **MOG view** — a 4×6 arrangement/permutation of 24 coordinates. It is a two-dimensional coordinate display with exact combinatorial meaning.
2. **Leech space** — an exact 24-dimensional lattice. The 24 coordinates and lattice vectors should remain in 24D for calculations.
3. **3D visualization** — a projection chosen for human viewing or a declared task. It is not automatically the Leech lattice “represented in 3D.” Any projection must publish its 24→3 matrix and quantify lost distances, neighborhoods, and symmetries.
4. **Physical channels** — mass, charge, phase, energy, observations, and conditions attached to a typed subject/state. These should not be silently treated as extra Euclidean coordinates. A metric and units are required before combining them geometrically.

The Monster group is mathematically related to the Leech/Conway setting through additional algebraic constructions, but it should not be described as simply “more spatial dimensions.” Group actions, representations, and invariants are the appropriate objects. This round does not claim a full Monster-module virtual twin.

A safe virtual-twin object should therefore retain:

- exact 24D state and MOG coordinate view;
- optional, explicitly lossy 3D projection;
- typed physical observations with units and provenance;
- declared Y transformation and cost functional;
- the acting symmetry group and representation, if used;
- reconstruction error and random/projection controls.

## 7. Recommended next sequence

1. **Repair and version the KB schema.** Resolve the category-length mismatches and add units, uncertainty, conditions, provenance, and missingness.
2. **Freeze the 0.7 coherence protocol.** State the subject class, peer group, measurement method, and whether 0.7 is absolute, relative retention, or a fitted decision threshold.
3. **Run a prospective particle test.** Freeze formula grammar and coefficients, then predict locked targets with matched baselines.
4. **Define one exact 24D twin transform.** Specify the map, inverse/reconstruction, TAX/cost, and invariants. Treat a 3D view only as visualization.
5. **Only then return to Elements.** Use typed KB channels and larger interaction data, complete-element/scaffold holdouts, and random-address/projection controls.

## Reproduction

```bash
python3 ubp_fundamental_kb_experiment.py
python3 -m unittest discover -s tests -v
lake build RequestProject.GolayMOG
```

Generated artifacts:

- `data/processed/ubp_kb_elements_standardized.csv`;
- `results/ubp_particle_formula_audit.csv`;
- `results/ubp_kb_element_holdout.csv`;
- `results/ubp_fundamental_kb_summary.json`.
