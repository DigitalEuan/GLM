# Figures

**Every number the documentation quotes, recomputed by the code that reports it.**

This file is generated.  Do not edit it by hand -- run

```
python -m glm_universal.figures --write
```

from the directory holding `glm_universal/`, and commit the result alongside whatever changed.  `tests/test_figures.py` compares this file against a fresh computation, so a stale figure fails the suite rather than reaching a reader.

Two rows are measured from outside the package and are marked as such: the collected test count needs `pytest` to walk the suite (`--with-tests`), and the Lean counts are read off the repository tree.

## At a glance

**8 registers** holding 1089 carriers, reached through **21 query kinds** of which one dispatches **48 report subjects**; **118 elements** and **51 molecules**; **357 meanings** in the lexicon; **33 probes** of which 20 hold and 13 break; **131 cases** end to end; **62 test files**; **48 Lean files** carrying 0 sorries.

## Sentences

Quote these verbatim.  `tests/test_figures.py` finds every phrase of the shape in the third column in the documentation and requires it to be the sentence in the second, so a superseded phrasing fails the suite without anyone having to list it.

| name | sentence | shape | counts |
|---|---|---|---|
| `evaluation_cases` | 131 CLI cases | `\b\d+ CLI cases\b` | the evaluation set |
| `lean_files` | 48 Lean files | `\b\d+ Lean files\b` | the Lean development |
| `query_kinds` | 21 query kinds | `\b\d+ query kinds\b` | how many query kinds |
| `registers` | 8 registers | `\b\d+ registers\b` | how many registers there are |
| `report_subjects` | 48 report subjects | `\b\d+ report subjects\b` | how many subjects |
| `suite` | 2,872 tests across 61 of the 62 test files, 11,665 subtests, outside the document check | `\b[\d,]+ tests across \d+(?: of the \d+)? test files, [\d,]+ subtests(?:, outside the document check)?` | what a complete run counts |
| `test_files` | 62 test files | `\b\d+ test files\b` | how many test files |

## Package surface

| figure | value |
|---|---|
| `version` | 1.14.0 |
| `subpackages` | substrate, data_objects, reasoning, semantics, recipe, language, runtime, migration, benchmarks, capabilities, evaluation |
| `subpackage_count` | 11 |
| `modules_by_subpackage` | substrate 10, data_objects 11, reasoning 49, semantics 6, recipe 4, language 7, runtime 5, migration 3, benchmarks 2, capabilities 3, evaluation 2 |
| `module_count` | 102 |
| `query_kinds` | verify, analogy, describe, nearest, product, cluster, spatial, project, trilinear, coherence, report, angle, task, pi_groups, meaning, real, compare, measure, comparative, derive, unknown |
| `query_kind_count` | 21 |
| `report_subjects` | relations, leech distribution, theta, subalgebra, information loss, golay decoding, superposition, leech construction, facets, monster stack, multiresolution, migration, state migration, concept store, fusion, benchmarks, semantics, infinite values, capabilities, analogies, transform decoder, deep holes, units, molecules, chemistry coverage, blueprint, reversible, mantissa, engine, noise, signature, drift, catalog, containers, companion, lattices, shells, llvq, harmony, economics, lean, directives, pipeline, escalation, measure, names, recipe, language |
| `report_subject_count` | 48 |
| `domains` | physics, chemistry, molecules, mathematics, lexicon, spatial, harmonics, economics |
| `domain_count` | 8 |
| `tasks` | grid, physics, concepts |
| `task_count` | 3 |

## Registers

| figure | value |
|---|---|
| `by_domain` | physics 726, chemistry 118, molecules 51, mathematics 22, lexicon 95, spatial 28, harmonics 28, economics 21 |
| `total_carriers` | 1089 |

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
| `cases` | 131 |
| `kinds_covered` | 21 |
| `by_kind` | analogy 10, angle 2, cluster 2, coherence 2, comparative 7, compare 4, derive 4, describe 8, meaning 6, measure 9, nearest 4, pi_groups 2, product 1, project 1, real 5, report 50, spatial 2, task 3, trilinear 2, unknown 1, verify 6 |
| `expected_answers` | 115 |
| `expected_refusals` | 16 |
| `refusals_boundary` | 16 |
| `refusals_gap` | 0 |
| `gap_cases` | (none) |
| `report_subjects_exercised` | 49 |

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
| `files` | 48 |
| `lines` | 13826 |
| `sorries` | 0 |
| `file_names` | RequestProject/GLM/Address.lean, RequestProject/GLM/Cascade.lean, RequestProject/GLM/Comparative.lean, RequestProject/GLM/Computable.lean, RequestProject/GLM/Constants.lean, RequestProject/GLM/Cumulative.lean, RequestProject/GLM/DeltaSigma.lean, RequestProject/GLM/Denotation.lean, RequestProject/GLM/Endianness.lean, RequestProject/GLM/Escalation.lean, RequestProject/GLM/Facets.lean, RequestProject/GLM/Feedback.lean, RequestProject/GLM/Golay/Census.lean, RequestProject/GLM/Golay/Cesaro.lean, RequestProject/GLM/Golay/Code.lean, RequestProject/GLM/Golay/Dynamics.lean, RequestProject/GLM/Golay/Sextet.lean, RequestProject/GLM/GolayBoundary.lean, RequestProject/GLM/Harmony.lean, RequestProject/GLM/Heisenberg.lean, RequestProject/GLM/HigherLattices.lean, RequestProject/GLM/HullExpansion.lean, RequestProject/GLM/Irrational.lean, RequestProject/GLM/LLVQTable.lean, RequestProject/GLM/LayerChain.lean, RequestProject/GLM/Layers.lean, RequestProject/GLM/LogBucket.lean, RequestProject/GLM/Mantiss... |

## The test suite

| figure | value |
|---|---|
| `test_files` | 62 |
| `file_names` | test_analogy_models.py, test_benchmarks.py, test_blueprint.py, test_capabilities.py, test_catalog.py, test_coherence.py, test_companion.py, test_comparative.py, test_comparison_classes.py, test_containers.py, test_data_objects.py, test_deep_holes.py, test_denotation.py, test_derived.py, test_directive.py, test_drift.py, test_economics.py, test_element_coverage.py, test_escalation.py, test_evaluation.py, test_exact_real.py, test_figures.py, test_fusion.py, test_fwht_decode.py, test_harmonics.py, test_information_loss.py, test_inherited_graph.py, test_language.py, test_lattice_high.py, test_lean_address.py, test_lexicon_subspaces.py, test_llvq_table.py, test_measure_words.py, test_molecules.py, test_multires_tasks.py, test_name_coordinate.py, test_noise_lab.py, test_phase1_migration.py, test_phase2_algebra.py, test_physics_constants.py, test_physics_expansion.py, test_physics_expansion_v2.py, test_pipeline.py, test_project_directives.py, test_reasoning.py, test_reasoning_showcase.py, ... |
| `collected` | 2900 |

## What a complete run counted

| figure | value |
|---|---|
| `test_files` | 61 |
| `of_test_files` | 62 |
| `tests` | 2872 |
| `subtests` | 11665 |
| `excludes` | test_figures.py |
| `measured_by` | the sign-off ledger, at the last complete run |
| `python` | python3.11.14 |
