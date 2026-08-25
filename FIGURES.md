# Figures

**Every number the documentation quotes, recomputed by the code that reports it.**

This file is generated.  Do not edit it by hand -- run

```
python -m glm_universal.figures --write
```

from the directory holding `glm_universal/`, and commit the result alongside whatever changed.  `tests/test_figures.py` compares this file against a fresh computation, so a stale figure fails the suite rather than reaching a reader.

Two rows are measured from outside the package and are marked as such: the collected test count needs `pytest` to walk the suite (`--with-tests`), and the Lean counts are read off the repository tree.

## At a glance

**6 registers** holding 1040 carriers, reached through **18 query kinds** of which one dispatches **25 report subjects**; **118 elements** and **51 molecules**; **357 meanings** in the lexicon; **33 probes** of which 20 hold and 13 break; **83 cases** end to end; **37 test files**; **27 Lean files** carrying 0 sorries.

## Package surface

| figure | value |
|---|---|
| `version` | 1.3.0 |
| `subpackages` | substrate, data_objects, reasoning, semantics, runtime, migration, benchmarks, capabilities, evaluation |
| `subpackage_count` | 9 |
| `modules_by_subpackage` | substrate 8, data_objects 7, reasoning 27, semantics 6, runtime 3, migration 3, benchmarks 2, capabilities 3, evaluation 2 |
| `module_count` | 61 |
| `query_kinds` | verify, analogy, describe, nearest, product, cluster, spatial, project, trilinear, coherence, report, angle, task, pi_groups, meaning, real, compare, unknown |
| `query_kind_count` | 18 |
| `report_subjects` | relations, leech distribution, theta, subalgebra, information loss, golay decoding, superposition, leech construction, facets, monster stack, multiresolution, migration, state migration, concept store, fusion, benchmarks, semantics, infinite values, capabilities, analogies, transform decoder, deep holes, units, molecules, chemistry coverage |
| `report_subject_count` | 25 |
| `domains` | physics, chemistry, molecules, mathematics, lexicon, spatial |
| `domain_count` | 6 |
| `tasks` | grid, physics, concepts |
| `task_count` | 3 |

## Registers

| figure | value |
|---|---|
| `by_domain` | physics 726, chemistry 118, molecules 51, mathematics 22, lexicon 95, spatial 28 |
| `total_carriers` | 1040 |

## Chemistry: the element register and its coverage

| figure | value |
|---|---|
| `elements` | 118 |
| `diatomics` | 52 |
| `measured_fields` | 14 |
| `total_cells` | 1652 |
| `filled_cells` | 1257 |
| `complete_fields` | atomic_weight_u, group_block_code, standard_state_code |
| `sparse_fields` | homonuclear_bde_kJ_per_mol, covalent_radius_pm, electron_affinity_eV |
| `sparsest_field` | homonuclear_bde_kJ_per_mol |
| `sparsest_count` | 21 |
| `covalent_radius_measured` | 24 |
| `covalent_radius_estimated` | 75 |
| `covalent_radius_absent` | 19 |
| `covalent_coverage_before` | 12/59 |
| `covalent_coverage_after` | 99/118 |
| `fit_slope` | 40097/37562 |
| `fit_intercept_pm` | -910587/10732 |
| `fit_mean_absolute_residual_pm` | 5825791/450744 |
| `fit_worst_element` | Mg |
| `fit_max_absolute_residual_pm` | 3093031/75124 |
| `derived_attributes` | 4 |
| `derived_new_cells` | 344 |
| `cross_check_compared` | 14 |
| `cross_check_agree_within_20` | 10 |
| `cross_check_disagree` | P, C, S, Si |
| `cross_check_largest_difference_element` | P |
| `cross_check_largest_difference` | 569/2 |

## Chemistry: the molecules register

| figure | value |
|---|---|
| `molecules` | 51 |
| `ions` | 5 |
| `distinct_elements_used` | 17 |
| `coordinates` | 24 |
| `derived_fields` | 19 |
| `missing_by_field` | degree_of_unsaturation 14 |
| `bundle_is_faithful` | True |
| `distinct_bundles` | 51 |
| `bundle_collisions` | 0 |
| `distinct_composites` | 51 |
| `composite_collisions` | 0 |
| `largest_by_mass` | iron(III) sulfate |
| `largest_by_mass_u` | 199939/500 |
| `largest_by_atom_count` | sucrose |
| `largest_atom_count` | 45 |

## Meaning

| figure | value |
|---|---|
| `meanings` | 357 |
| `notations` | 1705 |
| `binary_edges` | 6210 |
| `ternary_edges` | 6649 |
| `all_edges_reverified` | True |
| `refused_terms` | 63 |
| `nodes_by_kind` | compound 29, dimension 156, element 118, number 39, operation 8, quantity 7 |
| `isolated_meanings` | 73 |
| `collapsed_meanings` | 250 |
| `inherited_concepts` | 4282 |
| `inherited_grounded` | 83 |
| `inherited_edges` | 4015 |
| `inherited_derivable_edges` | 2 |
| `inherited_edge_classes` | about_the_pipeline 39, derivable 2, endpoint_ungrounded 815, not_derivable 2, proximity_artefact 3157 |
| `mean_hamming_related` | 4547/376 |
| `mean_hamming_unrelated` | 12077/1009 |

## Capability probes

| figure | value |
|---|---|
| `probes` | 33 |
| `holds` | 20 |
| `breaks` | 13 |
| `errors` | 0 |
| `surprises` | (none) |
| `areas` | 9 |
| `by_area` | algebra {'holds': 0, 'breaks': 1, 'error': 0}, carriers {'holds': 2, 'breaks': 1, 'error': 0}, dynamic carrier {'holds': 4, 'breaks': 2, 'error': 0}, layers {'holds': 1, 'breaks': 2, 'error': 0}, reals {'holds': 6, 'breaks': 4, 'error': 0}, runtime {'holds': 5, 'breaks': 0, 'error': 0}, scale {'holds': 1, 'breaks': 1, 'error': 0}, semantics {'holds': 1, 'breaks': 1, 'error': 0}, substrate {'holds': 0, 'breaks': 1, 'error': 0} |
| `breaking_probes` | algebra_product_is_associative, carrier_non_dyadic_denominator, dynamic_24d_arbitrary_target, dynamic_repair_is_single_valued, layers_can_compute_addition, real_division_by_an_undecided_value, real_equality_is_decidable, real_surrogate_on_a_grid_point, real_value_as_carrier, scale_more_than_24_coordinates, semantics_open_vocabulary, substrate_repair_radius, tax_conservation_above_bits |

## End-to-end evaluation set

| figure | value |
|---|---|
| `cases` | 83 |
| `kinds_covered` | 18 |
| `by_kind` | analogy 10, angle 1, cluster 1, coherence 1, compare 4, describe 8, meaning 6, nearest 4, pi_groups 2, product 1, project 1, real 5, report 26, spatial 1, task 3, trilinear 2, unknown 1, verify 6 |
| `expected_answers` | 73 |
| `expected_refusals` | 10 |
| `refusals_boundary` | 9 |
| `refusals_gap` | 1 |
| `gap_cases` | nearest-unregistered-molecule |
| `report_subjects_exercised` | 25 |

## Benchmarks

| figure | value |
|---|---|
| `suites` | 5 |
| `tasks` | 2390 |
| `passed` | 2389 |
| `overall_score` | 2389/2390 |
| `null_results` | 0 |
| `by_suite` | analogy_chemistry 12/12 (1/1) against a baseline of 1/4, analogy_physics 13/13 (1/1) against a baseline of 0/1, analogy_semantic 10/10 (1/1) against a baseline of 0/1, golay_correction 2325/2325 (1/1) against a baseline of 1/2325, physics_equations 29/30 (29/30) against a baseline of 2/3 |

## The Lean development

| figure | value |
|---|---|
| `root` | glm_lean |
| `files` | 27 |
| `lines` | 6390 |
| `sorries` | 0 |
| `file_names` | RequestProject/GLM/Computable.lean, RequestProject/GLM/Constants.lean, RequestProject/GLM/Cumulative.lean, RequestProject/GLM/DeltaSigma.lean, RequestProject/GLM/Endianness.lean, RequestProject/GLM/Facets.lean, RequestProject/GLM/Golay/Census.lean, RequestProject/GLM/Golay/Cesaro.lean, RequestProject/GLM/Golay/Code.lean, RequestProject/GLM/Golay/Dynamics.lean, RequestProject/GLM/Golay/Sextet.lean, RequestProject/GLM/GolayBoundary.lean, RequestProject/GLM/HullExpansion.lean, RequestProject/GLM/Irrational.lean, RequestProject/GLM/Layers.lean, RequestProject/GLM/Permutation.lean, RequestProject/GLM/Reachable.lean, RequestProject/GLM/Sakuma.lean, RequestProject/GLM/Semantics/Grounding.lean, RequestProject/GLM/Semantics/Meaning.lean, RequestProject/GLM/Stack.lean, RequestProject/GLM/Superposition.lean, RequestProject/GLM/TaxConservation.lean, RequestProject/GLM/Tower.lean, RequestProject/GLM/Transcendental.lean, RequestProject/GLM/VOA.lean, RequestProject/GLM/Wobble.lean |

## The test suite

| figure | value |
|---|---|
| `test_files` | 37 |
| `file_names` | test_analogy_models.py, test_benchmarks.py, test_capabilities.py, test_coherence.py, test_data_objects.py, test_deep_holes.py, test_directive.py, test_element_coverage.py, test_evaluation.py, test_exact_real.py, test_figures.py, test_fusion.py, test_fwht_decode.py, test_information_loss.py, test_inherited_graph.py, test_lexicon_subspaces.py, test_molecules.py, test_multires_tasks.py, test_phase1_migration.py, test_phase2_algebra.py, test_physics_constants.py, test_physics_expansion.py, test_physics_expansion_v2.py, test_reasoning.py, test_reasoning_showcase.py, test_runtime.py, test_semantic_lexicon.py, test_semantic_lexicon_runtime.py, test_semantics.py, test_state_migration.py, test_substantive.py, test_substrate.py, test_superposition.py, test_term_arithmetic.py, test_transcendental.py, test_units.py, test_wiring.py |
| `collected` | 1677 |
