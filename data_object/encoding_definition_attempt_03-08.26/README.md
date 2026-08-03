This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# Golay–MOG / Spatial Arithmetic experiments

This project contains the supplied UBP, TGIC, language, and Spatial Arithmetic programs plus a reproducible periodic-table pilot.

## New deliverables  [Likely too rigid for any good exploration and development, misses the point and tries many complicated methods that don't work well]

- `STUDY_SESSION_DATA_OBJECT_METHOD.md` — full cross-domain study-session synthesis: the current evidence-aware architecture, completed experiments and non-results, reusable workflow, guardrails, and Geometry/Language adaptations. 
- `data_object_workbench.py` — heavily commented standard-library builder and auditor for manifest-driven Data Objects from CSV, JSON, or JSONL, with optional exact Gray/Golay/MOG identity and claim-index views.
- `tests/test_data_object_workbench.py` — deterministic construction, missingness, integrity, and failure-mode tests for the reusable workbench.
- `golay_mog_experiments.py` — standard-library experiment runner.
- `data/raw/pubchem_periodic_table.csv` — immutable 118-element source snapshot.
- `data/processed/elements.csv` — generated normalized table.
- `data/SOURCES.md` — provenance, citation, access date, and checksum.
- `results/metrics.csv` — 224 held-out metric records.
- `results/predictions.csv` — per-element held-out predictions.
- `results/summary.json` — exact audits and overall configuration ranking.
- `reports/EXPERIMENT_REPORT.md` — methods, findings, limitations, and recommendation.
- `tests/test_golay_mog_experiments.py` — exact and metamorphic software tests.
- `RequestProject/GolayMOG.lean` — machine-checked Gray, MOG, and Leech-address invariants.
- `gray_leech_data_objects.py` — v2 full-table Data Object generator and exact audit.
- `schemas/element_data_object_v2.json` — Gray/Golay/MOG/Leech schema and address table.
- `data/objects/elements.jsonl` — complete 118-element object table with typed channels.
- `results/gray_leech_audit.json` — locality, uniqueness, norm, and rank checks.
- `reports/GRAY_LEECH_REFINEMENT.md` — second-round design, results, limits, and next tests.
- `spatial_chemistry_discovery.py` — discrete-time, blast-radius, pair-similarity, and nested arrangement search.
- `results/spatial_discovery.json` — exact transition audits and summarized held-out pair AUC.
- `results/spatial_pair_metrics.csv` — all fold-level pair and training-selected-layout results.
- `reports/SPATIAL_DISCOVERY_ROUND.md` — third-round findings, interpretation, and next interaction-object design.
- `tests/test_spatial_chemistry_discovery.py` — exact and leakage-control checks for the third round.
- `leech_class_data_objects.py` — exact enumeration of all 196,560 minimal vectors and v3 relationship experiment.
- `schemas/element_data_object_v3.json` — lossless typed channels with deterministic addresses in Classes A, B, and C.
- `data/objects/elements_v3.jsonl` — all 118 v3 element objects.
- `results/leech_class_audit.json` — exact class counts, disjointness, Golay weights, and norm audit.
- `results/leech_class_relationships.csv` / `.json` — held-out relationship tests and summaries.
- `reports/LEECH_CLASS_VALIDATION.md` — fourth-round design, results, limitations, and next interaction test.
- `tests/test_leech_class_data_objects.py` — exhaustive class and generated-object checks.
- `diatomic_interaction_experiment.py` — predeclared A/B/C operators and complete-element-holdout D0 experiment.
- `data/processed/diatomic_dissociation_0k.csv` — 52 typed neutral gas-phase diatomic endpoints from the retained NIST CCCBDB snapshot.
- `results/diatomic_interaction_summary.json`, `diatomic_complete_element_holdout.csv`, and `diatomic_predictions.csv` — interaction results.
- `structured_element_data_objects.py` — v4 generator with identity, electron occupancy, observations, and nine explicit 3D MOG layers.
- `schemas/element_data_object_v4.json` and `data/objects/elements_v4.jsonl` — structured schema and all 118 objects.
- `reports/DIATOMIC_INTERACTION_AND_ELEMENT_OBJECT_V4.md` — methods, findings, limitations, and next gate.
- `tests/test_diatomic_and_structured_objects.py` — endpoint leakage, operator, and v4 object audits.
- `ubp_element_mog_experiment.py` — UBP TAX/NRCI, fixed-MOG, Hexacode, and XOR-trajectory test on the diatomic endpoint.
- `results/ubp_element_mog_summary.json`, `ubp_element_mog_holdout.csv`, and `ubp_element_mog_predictions.csv` — complete-element-holdout UBP results.
- `reports/UBP_ONTOLOGY_ELEMENT_MOG_EXPERIMENT.md` — operational definitions, exact deductions, empirical findings, guardrails, and next experiments.
- `tests/test_ubp_element_mog_experiment.py` — UBP grammar, score-identity, symmetry, and generated-result checks.
- `ubp_fundamental_kb_experiment.py` — fundamental-constant dependency audit, particle-formula reproduction audit, standardized KB Element extraction, peer-relative NRCI analysis, and Y-twin holdout pilot.
- `data/processed/ubp_kb_elements_standardized.csv` — all 118 KB Element records with exact, positionally safe core channels and explicit metadata limitations.
- `results/ubp_particle_formula_audit.csv`, `ubp_kb_element_holdout.csv`, and `ubp_fundamental_kb_summary.json` — formula, schema, coherence, and interaction results.
- `reports/FUNDAMENTAL_FIRST_KB_AND_GEOMETRY_AUDIT.md` — interpretation of the ~0.7 threshold, KB standardization, particle-level dependencies, and MOG/Leech/3D/Monster boundaries.
- `tests/test_ubp_fundamental_kb_experiment.py` — KB integrity, threshold, Y-twin, formula-status, and generated-output checks.
- `ubp_kb_geometry_protocol.py` — typed five-channel KB companion, exact Golay-octad zones, audited 24→3 visualization, and frozen particle-test protocol.
- `data/processed/ubp_kb_elements_typed_long.csv` — 590 lossless channel records with explicit unit/condition/uncertainty/source/status fields and unresolved metadata kept visible.
- `results/ubp_mog_octad_zones.json`, `leech_24d_to_3d_projection.json`, and `prospective_particle_protocol.json` — exact regions, full projection matrix/distortion audit, and prospective test specification.
- `reports/KB_COMPLETION_OCTAD_3D_AND_PARTICLE_PROTOCOL.md` — answers to the five requested points, findings, limits, and recommended use.
- `tests/test_ubp_kb_geometry_protocol.py` — completeness, Octad, projection-loss, and protocol-status checks.

## Run

```bash
# Start a new cross-domain Data Object study (example manifest and records):
python3 data_object_workbench.py init examples/geometry_study
python3 data_object_workbench.py build examples/geometry_study/study.json
python3 data_object_workbench.py audit examples/geometry_study/objects.jsonl

# Reproduce the earlier element and interaction studies:
python3 gray_leech_data_objects.py
python3 golay_mog_experiments.py --run
python3 spatial_chemistry_discovery.py
python3 leech_class_data_objects.py
python3 diatomic_interaction_experiment.py
python3 structured_element_data_objects.py
python3 ubp_element_mog_experiment.py
python3 ubp_fundamental_kb_experiment.py
python3 ubp_kb_geometry_protocol.py
python3 -m unittest discover -s tests -v
lake build RequestProject.GolayMOG
```

The Python experiments use only the standard library. Results are deterministic under the recorded seed.

The v2 identity message uses reflected Gray code, so all consecutive atomic numbers 1–118 differ by exactly one message bit. Golay encoding intentionally expands that distance to 8 or 12 bits for error protection. Measurements are carried inside each structured Data Object as typed, Leech-addressed channels rather than being lossily packed into the 24-bit identity.

## Current conclusion

For the seven tested atomic-property endpoints, the simple atomic-number polynomial baseline has the lowest average normalized held-out MAE. The fixed MOG geometries do not outperform that baseline overall.

The third round also tested a precise re-encoding blast radius, a discrete Gray transition clock, pair proximity, and training-only selection among 129 MOG layouts per fold. The exact Gray/Golay transition structure is reproducible, but neither fixed nor selected MOG geometry beats ordinary controls on held-out group/block or standard-state similarity.

The fourth round exactly enumerates the three Leech minimal-vector shape classes (1104 A, 97152 B, 98304 C; total 196560) and gives every typed element channel a deterministic address in every class. On leave-period-out tests, fixed A/B/C superpositions do not improve upon raw measured channels and behave similarly to random-address controls.

The fifth round tests 52 neutral gas-phase diatomic D0 values under complete-element holdout. Fixed Class-A/additive features score 116.17 kJ mol⁻¹ macro-MAE versus 122.33 for raw A/B/C atomic properties, but remain inside the random-Class-A range (107.19–136.55); fixed B, fixed C, and combined fixed A/B/C do not improve on raw properties. The v4 Element Object adds nine explicit MOG layers for identity, seven electron shells, and observation indexing while preserving typed measurements and exact 24D addresses. See `reports/DIATOMIC_INTERACTION_AND_ELEMENT_OBJECT_V4.md`.

The UBP ontology round operationalizes the supplied Gray → Golay → MOG → Hexacode route, TAX/NRCI, and XOR trajectory on that same endpoint. All 118 element codewords have valid Hexacode shadows, as guaranteed by the encoding. On binary states, TAX is exactly Hamming weight times a constant and NRCI is a monotone transform of weight; all 118 element identities exceed the proposed 0.500 horizon, so it is not selective here. The fixed UBP MOG/Hexacode descriptor scores 232.44 kJ mol⁻¹ macro-MAE, within the random-layout range of 157.36–245.12 and worse than raw measured properties at 122.33. See `reports/UBP_ONTOLOGY_ELEMENT_MOG_EXPERIMENT.md`.

## Fundamental-first KB refinement

The fundamental-first round audits the π/φ/e dependency chain and both particle-formula tables before reusing the KB Element tensor. An absolute NRCI threshold of 0.7 accepts 49/118 stored element vectors; a rule requiring 70% of a peer-group median accepts all 118 and is therefore non-selective. The KB has 118 populated core values for mass, boiling point, melting point, atomic number, and density, but lacks units, uncertainty, conditions, and per-value provenance, and several other positional tensor categories have schema-length mismatches.

On the same complete-element-holdout diatomic endpoint, standardized KB channels score 164.29 kJ mol⁻¹ macro-MAE and the declared Y-twin scores 164.31, compared with 167.26 for the training mean. The Y twin is information-redundant by construction. Exact 24D Leech calculations are kept separate from optional lossy 3D visualization, while Monster mathematics is treated as group-action/representation structure rather than extra Euclidean coordinates. See `reports/FUNDAMENTAL_FIRST_KB_AND_GEOMETRY_AUDIT.md`.

## Typed KB, Octad zones, and projection protocol

The latest companion table makes all five KB channels operational without inventing unavailable metrology: exact values are retained, inferred units are labelled, and missing conditions, uncertainty, and upstream provenance remain explicit. Three adjacent-column-pair regions are verified Golay octads partitioning the 24 fixed MOG coordinates, but do not override the strict category-length decoding rule. A published rank-three Walsh projection demonstrates why a 3D view is visualization only: on the 24 fixed addresses it has 65.31% mean relative distance error, 8.88% directed nearest-neighbor recall, and 15 point collisions. The particle artifact freezes a prospective protocol but does not relabel previously inspected targets as unseen predictions. See `reports/KB_COMPLETION_OCTAD_3D_AND_PARTICLE_PROTOCOL.md`.
