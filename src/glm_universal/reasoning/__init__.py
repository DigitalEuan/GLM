"""``glm_universal.reasoning`` -- the algebraic and geometric reasoning kernel.

Four modules, in dependency order:

``product``
    The Norton-Sakuma ``2A`` algebra over the substrate's own type-2 classes:
    the Sakuma relation ``a . b = (1/8)(a + b - a_ab)``, the Griess form on
    axes, the three-dimensional subalgebra with its checked closure,
    commutativity and non-associativity, the exact Ising fusion spectrum of
    ``ad_a``, and the Miyamoto maps derived from that spectrum.
``metric``
    The positive-definite Griess form on ``Q^24``, exact squared distances,
    float-free angular comparison, the triangle inequality decided by
    clearing its single square root, and exact single- and complete-linkage
    agglomerative clustering with rational merge heights.
``analogy``
    Proportional analogy ``A : B :: C : D`` as ``D* = C + (B - A)`` followed
    by projection: onto a candidate set of :class:`~glm_universal.
    data_objects.base.DataObject` carriers, onto the Golay code, or onto the
    Leech lattice by exact -- and provably optimal -- nearest-point decoding.
``verifier``
    The multi-plane physical equation audit: the operator algebra and parser
    for the register's 222 scalar and 71 tensor relations, and the attribution
    of every discrepancy to the 31 named MOG facets.
``fwht_decode``
    The transform-driven decoder: the 4,096 Golay coset costs the Leech
    nearest-point search minimises, read off one Walsh-Hadamard transform,
    and the constant-time lookup that either proves its own answer from the
    code's minimum distance or hands over to the exact route.
``voronoi_walk`` and ``deep_holes``
    The Niemeier classification held as potential rather than as a table: a
    walk slides to a vertex of the Leech lattice's Voronoi diagram and
    climbs to the covering radius, the modulator's trajectory supplies the
    hole's vertices, and a marked-barycentre identity certifies the reading.
    The 196,560 facets are never built and no hole centre is stored.
``units``
    Unit strings read as dimensions: ten base units are stored, every other
    unit is a definition in terms of units already defined, and each
    quantity's unit string is checked against the EXT10 exponents declared
    beside it.  The steradian is carried as a dimension rather than read the
    SI way as a ratio, and the cost of the SI reading is measured.
``element_coverage``
    Widening the chemistry register without inventing a measurement: exact
    derivations from fields already present, a rational least-squares model
    for the covalent radius with its residuals reported beside every
    estimate, and a cross-check against the diatomic register that reports
    the disagreement rather than merging the two quantities.
``escalation``
    The five-layer stack audited on the machine's own data rather than on
    seven hand-picked carriers: every named object of every register, keyed
    by each layer's zero-measure reading so the audit is linear rather than
    quadratic, with the keys re-derived from the layers themselves on a
    sample.  It measures where escalation stops -- the number of distinct
    carriers is a ceiling no layer can pass, and the registers sit below it.
``name_coordinate``
    The resolution ceiling ``escalation`` measured, attacked where it lives.
    A layer's view is a function of the carrier, so 283 entries sharing a
    carrier are beyond every layer; this module adds an exact integer
    coordinate computed from the entry's own name, measures what it recovers
    at each width, and measures the same for four coordinates that are not
    the name -- the register label among them, which recovers nothing.
``measure_view``
    A measure word read as a measurement rather than a concept: ``hot``
    against a comparison class is an exact magnitude, the relative reading is
    added to the static one as a *widening* (and the audit measures what the
    rejected replacement would cost), and the ``related_to`` residue is
    converted wherever the physics register can decide it.
``denotation_view``
    The rest of that residue, decided rather than searched.  Every endpoint
    the register could not dimension now has a verdict in
    ``data_objects.denotation``; this module reads the verdicts back over the
    residue and measures what they change, and its ``closure`` is the claim
    that no triple is declined any longer for want of an entry.
``harmony``
    The musical third of the catalogue's universality claim, tested rather
    than asserted: exact tempering errors, the fifth that never closes,
    Kendall's tau between lattice proximity and the two classical consonance
    measures, and -- decisively -- an undecoded control that shows the
    ordering survives without the lattice, so the claim is recorded as *not
    reproduced*.
``economics``
    The economic third of the same claim, measured the same way: prices as
    exact rationals become 24-vectors through their magnitude buckets,
    mantissas and EXT10 exponents, the lattice separates all 21 records only
    at scale 1024, and every nearest neighbour is another quarter of the same
    instrument -- but so is every nearest neighbour of the undecoded control,
    so this third is recorded as *not reproduced* as well.
``term_arithmetic``
    Arithmetic over register *names*: ``energy divided by time`` is rewritten
    into the verifier's grammar, evaluated exactly, and answered by naming
    every register quantity of the resulting dimension.

Invariants, inherited unchanged from the substrate
--------------------------------------------------
* **Exact arithmetic only** -- ``int`` and ``fractions.Fraction``.  Every
  entry point refuses a ``float`` with a ``TypeError`` rather than coercing
  it; no square root is ever taken in floating point, and quantities that are
  genuinely irrational (a Griess distance, an angle) are returned as exact
  squared or trigonometric-squared surrogates instead of being rounded.
* **No randomness** -- ``random`` is not imported here or anywhere in the
  package.  Where a sample of axes or pairs is needed it is taken in sorted
  order from the exhaustive class table.
* **Standard library only.**
* **Facts computed, not quoted** -- the ``*_report`` functions recompute the
  algebra's closure, the form's definiteness, and the relation tallies on
  demand rather than restating them from a docstring.
"""

from __future__ import annotations

from . import (analogy, analogy_models, blueprint, catalog, coherence,
               companion, containers,
               deep_holes, dimension_layers, drift, element_coverage, engine,
               denotation_view, economics, escalation, exact_real, facets,
               harmony,
               fwht_decode, information_loss, mantissa, measure_view, metric,
               monster_stack,
               multires, name_coordinate, niemeier, noise_lab,
               periodic_table, product,
               real_expr,
               reversible, tasks, term_arithmetic, transcendental, units,
               verifier, voronoi_walk, wobble)
from .analogy import (SUBSPACES, AnalogyResult, LatticeAnalogyResult,
                      analogy_target, domain_analogy, element_analogy,
                      lattice_analogy, nearest_golay_codeword,
                      nearest_lattice_point, physics_analogy,
                      project_subspace, solve_analogy, solve_analogy_objects,
                      subspace_indices)
from .metric import (DIM, GRIESS_SCALE, Dendrogram, Merge, angular_order,
                     as_exact_vector, complete_linkage, compare_cosines,
                     cut_tree, distance2, distance_matrix, exact_distance,
                     griess_inner, griess_norm2, leech_gram, nearest,
                     positive_definite_report, rank_by_distance,
                     signed_cosine_squared, single_linkage,
                     triangle_inequality_holds)
from .product import (POSITION_BY_INVARIANT, SELF_INNER, TWO_A_INNER,
                      TWO_A_PRODUCT_COEFF, AlgebraVector, ClassTranslation,
                      PositionError, TwoASubalgebra, adjoint_matrix,
                      algebra_product, apply_map, axis, axis_product,
                      axis_trilinear, class_translation, coherence_of_product,
                      fusion_spectrum, griess_form, griess_trilinear,
                      is_automorphism, is_two_a_pair, miyamoto_sigma,
                      miyamoto_tau, pair_invariant_classes, position_name,
                      preserves_form, sakuma_third_axis, sample_two_a_pairs,
                      semantic_distance2, semantic_similarity,
                      trilinear_on_axes, trilinear_report,
                      two_a_closure_report, two_a_subalgebra, zero)
from .verifier import (NABLA, OPERATORS, RELATION_LAYOUT, SCALAR_SENSE,
                       SEMANTICS, RelationError, RelationVerdict, Sense,
                       facet_attribution_census, load_relations, parse,
                       relation_table, resolve_name, sense_carrier,
                       sense_of_quantity, tokenise, verifier_report,
                       verify_all, verify_expression_pair, verify_relation)

from .dimension_layers import (
    LAYER_GRIESS, LAYER_INTEGER, LAYER_RATIONAL, LAYER_SUBSTRATE,
    LAYER_UNIVERSAL, LAYERS, DimensionLayer, escalate, projection_report,
)

from .information_loss import (
    Witness, boundary, capacity, carrier_sum, classes, congruence_witness,
    indistinguishable, information_loss_report, is_congruent, loss_count,
    refinement_violations, resolution, sample_carriers,
)

from .reversible import (BLOCKS_8x3, BLOCKS_MOG, DEMO_CARRIER, TAX_SCALE,
                         channel_report, flip_deltas, fredkin, gate_period,
                         gray, gray_inverse, kink_rotation_orbit, kinks,
                         reversibility_report, reversible_report, rotate,
                         soliton_report, symmetry_tax, toffoli)

from .noise_lab import (DITHER_ALPHA, DITHER_AMPLITUDES, CascadeRun,
                        ModulatorRun, Signal, cascade_bound, cascade_run,
                        constant_signal, convergence_table,
                        demonstration_mix, dither_experiment, dither_sweep,
                        equidistributed, first_order_bound,
                        first_order_triangular, mix_tones, noise_report,
                        orbit_closure, run_signal, square_tone,
                        tone_strength, triangle_tone, walsh_spectrum)

from .wobble import (ENTROPY_BITS, OSCILLATOR_DENSITIES, RESONANCE_Q,
                     RESONANCE_RATIOS, TARGET_PRECISION, WOBBLE_STEPS,
                     entropy_bits, longest_run, mean_run_length,
                     mean_run_length_law, ones_count, ones_count_law,
                     oscillator_table, pearson_autocorrelation,
                     pearson_autocorrelation_law, product_autocorrelation,
                     product_autocorrelation_law, resonance, resonance_gain,
                     resonance_q_scan, resonance_sweep, round_str, run_bound,
                     runs, sci_str, signature, signature_table,
                     signature_targets, stream_bits, transition_law,
                     transitions, wobble_report)

from .drift import (DIVERGENCE_THRESHOLD, RULES, STEPS, divergence_onset,
                    drift_report, drift_row, drift_table, final_values,
                    onset_table, orbit, significant_round, step_double,
                    step_exact)

from .catalog import (catalog_ledger, catalog_report, construction_a,
                      construction_a_leech_only, exponential_term_cost,
                      generator_step_costs, heron_step_cost, hull_norms,
                      lattice_ladder, liouville_term_cost, machin_term_cost,
                      minimum_weight, first_order_reed_muller,
                      section_1_claims, section_2_claims, section_3_claims,
                      section_4_claims, section_5_claims, section_6_claims)

from .blueprint import (BLUEPRINT_SIGMA, CONFIRMED, NOT_IMPLEMENTED,
                        NOT_REPRODUCED, REFUTED, VERDICTS, blueprint_ledger,
                        blueprint_report, delta_sigma_rate_table,
                        part_i_claims, part_ii_claims, part_iii_claims,
                        part_iv_claims, part_v_claims, roadmap_claims,
                        ubp_source_audit, verdict_tally)

from .engine import (ESCAPEMENT_MODULI, GEARS, SNAP_MODES,
                     SNAP_OPERATION_COST, TAX_CAPACITY, EngineConfig,
                     EngineRun, accumulate, classify_target,
                     convergent_sequence, engine_report, escapement_period,
                     escapements, gearbox, heron_sequence, multi_fuel,
                     precision_leap, run_engine, snap, tax_of)

from .mantissa import (ODD_PRIMES, PRECISION, PROJECTION_BITS, binary_period,
                       doubling_orbit, dyadic_bits, mantissa_report,
                       projection, projection_drift, projection_weights,
                       repeating_block, retained_bits, rounding_report,
                       to_double)

from .element_coverage import (DERIVED_ATTRIBUTES, PROVENANCES, Attribute,
                               attributes_of, covalent_radius_model,
                               coverage_table, derived_attribute,
                               derived_coverage, diatomic_cross_check,
                               element_coverage_report,
                               estimated_covalent_radii)

from .exact_real import (ExactReal, PrecisionError, decide_equal,
                         delta_sigma_average, delta_sigma_bits,
                         delta_sigma_error, exact_real_report, from_fraction,
                         golay_delta_sigma, hull_certificate, nonzero_witness,
                         nth_root, parse_real, real_carrier, sqrt, surrogate,
                         surrogate_sequence)

from .real_expr import (ExpressionError, expression_report, parse_expression)

from .transcendental import (cos, exp, log, positive_witness, rpow, sin, tan,
                             transcendental_report)

from .facets import (FACET_DESCRIPTION, FACET_INDICES, FACET_ORDER,
                     decompose, facet_coordinates, facet_distance_breakdown,
                     facet_lattice_report, facet_of_coordinate, facets_report,
                     intersection_lattice_basis, linearity_report,
                     partition_report, project, projector_matrix,
                     pythagoras_report, reassemble)

from .monster_stack import (DEPTH, MonsterAddress, PlaneAddress, PlaneProduct,
                            address_census, associativity_report,
                            compose_sakuma, compose_xor, geometric_tiebreak,
                            monster_address, monster_stack_report,
                            nearest_two_a_partner, nearest_type2_classes,
                            plane_address, position_census,
                            shortcut_loss_report)

from .multires import (KERNEL, ROW_LABELS, SAMPLE_GRIDS, MicroAddress,
                       census_collision_witness, column_sublattice,
                       column_to_fibre, cross_inner, cross_level_report,
                       cross_tensor, fibre_bijection_report, fibre_to_column,
                       grid_address, grid_carrier, grid_census, grid_shape,
                       grid_signature, micro_address, multires_report,
                       reflect_horizontal, reflect_vertical, rotate180,
                       scale_invariance_report, upscale)

from .tasks import (GRID_TASK, TRANSFORMATIONS, grid_task, physics_task,
                    tasks_report)

from .term_arithmetic import (NAMES_SHOWN, REPORT_EXPRESSIONS, TermArithmetic,
                              WORD_OPERATORS, mentions_register_name,
                              term_arithmetic_report)

from .periodic_table import (MAX_Z, PERIOD_BOUNDS, Position, PositionError,
                             atomic_number_at, periodic_report, position_of,
                             position_of_symbol, symbol_at)

from .containers import (AUTOCORRELATION_LAGS, INSIDE_L1_BOUND,
                         INSIDE_LINF_BOUND, PRECISION_THRESHOLDS,
                         PROJECTION_SCALE, REFERENCE_BITS,
                         SEPARATING_DIRECTIONS, Constant, apparent_period,
                         constant_by_name, containers_report,
                         critical_scales, hull_status, hull_table,
                         implied_value, inside_certificate,
                         near_period_coincidence, outside_certificate,
                         precision_bits, precision_profile, stream_of,
                         stream_period, wobble_row, wobble_table)

from .companion import (CONVERGENCE_TABLE_1, HULL_TABLE_3, STUDIES,
                        WOBBLE_TABLE_2, companion_ledger, companion_report,
                        hull_claims, recurrence_claims, wobble_claims)

from .escalation import (KEYED_LAYERS, REGISTERS, RegisterCarrier,
                         boundary_at_scale, class_key,
                         congruence_witness_at_scale, escalation_report,
                         key_agreement, keyed_classes, keyed_loss,
                         keyed_resolution, refines_at_scale,
                         register_carriers, resolution_ceiling)

from .name_coordinate import (BIT_WIDTHS, CONTROLS, SCHEMES, bit_sweep,
                              control_row, coordinate_function,
                              largest_prime_below, low_bits_code, name_code,
                              name_report, named_ceiling, prime_mod_code)

from .measure_view import (FACTOR_BASIS, MEASURE_RELATIONS, MeasureBoundary,
                           MeasureWord, Reading, Use, above_on,
                           basis_dimension_audit, basis_sweep, classify,
                           compare_words, measure_relations, measure_report,
                           measure_words, read, relation_repair,
                           repaired_triples, scaled_words,
                           static_agrees_with_rational_layer,
                           transport_audit,
                           unscaled_words, uses, widening_audit,
                           word_by_name)

#  Re-exported under qualified names: ``closure``, ``coverage`` and
#  ``second_pass`` are natural inside the module and far too general at the
#  package surface.
from .denotation_view import (DECIDED_RELATIONS, denotation_report)
from .denotation_view import closure as denotation_closure
from .denotation_view import coverage as denotation_coverage
from .denotation_view import dimension_of as denoted_dimension_of
from .denotation_view import second_pass as denotation_second_pass

from .economics import (comovement, decoded_points, economics_report,
                        magnitude_table, price_vector)

from .harmony import (consonance_orderings, fifth_never_closes,
                      harmony_report, kendall_tau, lattice_separation,
                      temperament_table, tuning_vector)

from .analogy_models import (MODEL_NAMES, MODELS_BY_DOMAIN, RELATION_SYNONYMS,
                             REPORT_CASES, VAGUE_RELATIONS, ModelResult,
                             analogy_models_report, explain_analogy,
                             lexicon_relation, periodic_step,
                             reciprocal_dimension, scale_shift)

__all__ = [
    "product", "metric", "analogy", "verifier", "dimension_layers",
    "coherence", "information_loss", "facets", "monster_stack",
    "multires", "tasks", "exact_real", "real_expr", "transcendental",
    "term_arithmetic", "periodic_table", "analogy_models", "fwht_decode",
    "niemeier", "voronoi_walk", "deep_holes", "units", "element_coverage",
    "reversible", "mantissa", "blueprint", "engine", "noise_lab",
    "wobble", "drift", "catalog", "containers", "companion", "harmony",
    "economics", "escalation", "measure_view", "denotation_view",
    "name_coordinate",
    # denotation_view -- the related_to residue decided by name
    "DECIDED_RELATIONS", "denotation_report", "denotation_closure",
    "denotation_coverage", "denotation_second_pass",
    "denoted_dimension_of",
    # name_coordinate -- a coordinate for the name, and what it buys
    "BIT_WIDTHS", "SCHEMES", "CONTROLS", "name_code", "low_bits_code",
    "prime_mod_code", "largest_prime_below", "coordinate_function",
    "named_ceiling", "bit_sweep", "control_row", "name_report",
    # economics -- the economic third of the universality claim
    "price_vector", "magnitude_table", "comovement", "decoded_points",
    "economics_report",
    # measure_view -- a measure word as a measurement, added as a widening
    "FACTOR_BASIS", "MEASURE_RELATIONS", "MeasureBoundary", "MeasureWord",
    "Reading", "Use", "measure_words", "word_by_name", "scaled_words",
    "unscaled_words", "read", "classify", "above_on", "compare_words",
    "measure_relations", "uses", "widening_audit",
    "static_agrees_with_rational_layer", "relation_repair",
    "basis_dimension_audit", "basis_sweep", "repaired_triples",
    "transport_audit",
    "measure_report",
    # escalation -- the layer stack audited on every register carrier
    "REGISTERS", "KEYED_LAYERS", "RegisterCarrier", "class_key",
    "keyed_classes", "keyed_resolution", "keyed_loss", "boundary_at_scale",
    "refines_at_scale", "congruence_witness_at_scale", "resolution_ceiling",
    "register_carriers", "key_agreement", "escalation_report",
    # harmony -- the musical third of the universality claim
    "temperament_table", "fifth_never_closes", "kendall_tau",
    "consonance_orderings", "tuning_vector", "lattice_separation",
    "harmony_report",
    # the three containers of a constant: generator, stream, hull.  The
    # module's own ``CONSTANTS``, ``convergence_table``, ``heron_sequence``,
    # ``projection`` and the other names ``engine``, ``noise_lab`` and
    # ``mantissa`` already export stay behind ``containers.``
    "PRECISION_THRESHOLDS", "REFERENCE_BITS", "AUTOCORRELATION_LAGS",
    "PROJECTION_SCALE", "INSIDE_L1_BOUND", "INSIDE_LINF_BOUND",
    "SEPARATING_DIRECTIONS", "Constant", "constant_by_name",
    "precision_bits", "precision_profile", "stream_of", "wobble_row",
    "wobble_table", "apparent_period", "stream_period",
    "near_period_coincidence", "inside_certificate", "outside_certificate",
    "hull_status", "hull_table", "implied_value", "critical_scales",
    "containers_report",
    # the two companion preprints read as a live claim ledger.  Its
    # ``verdict_tally`` and the four verdict constants are ``blueprint``'s,
    # already exported above.
    "STUDIES", "CONVERGENCE_TABLE_1", "WOBBLE_TABLE_2", "HULL_TABLE_3",
    "wobble_claims", "hull_claims", "recurrence_claims",
    "companion_ledger", "companion_report",
    # the spectral signature of a constant, and its laws
    "WOBBLE_STEPS", "TARGET_PRECISION", "ENTROPY_BITS",
    "OSCILLATOR_DENSITIES", "RESONANCE_RATIOS", "RESONANCE_Q",
    "stream_bits", "ones_count", "ones_count_law", "runs", "longest_run",
    "run_bound", "transitions", "transition_law", "mean_run_length",
    "mean_run_length_law", "product_autocorrelation",
    "product_autocorrelation_law", "pearson_autocorrelation",
    "pearson_autocorrelation_law", "entropy_bits", "round_str", "sci_str",
    "signature_targets", "signature", "signature_table",
    "oscillator_table", "resonance", "resonance_gain", "resonance_sweep",
    "resonance_q_scan", "wobble_report",
    # iteration drift over the odd primes, in three regimes.  The module's
    # own ODD_PRIMES stays behind ``drift.`` -- mantissa exports that name
    # too, and ``catalog.verdict_tally`` stays behind ``catalog.`` for the
    # same reason.
    "RULES", "STEPS", "DIVERGENCE_THRESHOLD",
    "significant_round", "step_exact", "step_double", "orbit",
    "final_values", "drift_row", "drift_table", "divergence_onset",
    "onset_table", "drift_report",
    # the external study findings read as a live claim ledger
    "first_order_reed_muller", "minimum_weight", "construction_a",
    "lattice_ladder", "construction_a_leech_only", "hull_norms",
    "heron_step_cost", "machin_term_cost", "exponential_term_cost",
    "liouville_term_cost", "generator_step_costs",
    "section_1_claims", "section_2_claims", "section_3_claims",
    "section_4_claims", "section_5_claims", "section_6_claims",
    "catalog_ledger", "catalog_report",
    # noise as a computation: cascaded loops, interacting tones, dither
    "Signal", "ModulatorRun", "CascadeRun", "DITHER_ALPHA",
    "DITHER_AMPLITUDES", "constant_signal", "square_tone", "triangle_tone",
    "mix_tones", "run_signal", "orbit_closure", "cascade_run",
    "first_order_triangular", "cascade_bound", "first_order_bound",
    "convergence_table", "walsh_spectrum", "tone_strength",
    "equidistributed", "dither_experiment", "dither_sweep",
    "demonstration_mix", "noise_report",
    # the thermo-dynamic carrier engine: the blueprint's Part III assembled
    "ESCAPEMENT_MODULI", "SNAP_MODES", "SNAP_OPERATION_COST", "TAX_CAPACITY",
    "GEARS", "EngineConfig", "EngineRun", "accumulate", "escapements",
    "escapement_period", "snap", "tax_of", "run_engine", "heron_sequence",
    "convergent_sequence", "multi_fuel", "classify_target", "gearbox",
    "precision_leap", "engine_report",
    # the unification blueprint read as a live claim ledger
    "VERDICTS", "CONFIRMED", "REFUTED", "NOT_REPRODUCED", "NOT_IMPLEMENTED",
    "BLUEPRINT_SIGMA", "ubp_source_audit", "delta_sigma_rate_table",
    "part_i_claims", "part_ii_claims", "part_iii_claims", "part_iv_claims",
    "part_v_claims", "roadmap_claims", "blueprint_ledger", "verdict_tally",
    "blueprint_report",
    # reversible bit dynamics: the Gray-code read channel, the Toffoli and
    # Fredkin gates on the 24 coordinates, and the kink invariant
    "TAX_SCALE", "BLOCKS_8x3", "BLOCKS_MOG", "DEMO_CARRIER", "gray",
    "gray_inverse", "symmetry_tax", "channel_report", "toffoli", "fredkin",
    "gate_period", "reversibility_report", "kinks", "rotate",
    "kink_rotation_orbit", "flip_deltas", "soliton_report",
    "reversible_report",
    # PTB/AOO mantissa metrology: IEEE-754 modelled in exact integers
    "PRECISION", "PROJECTION_BITS", "ODD_PRIMES", "to_double",
    "retained_bits", "binary_period", "repeating_block", "dyadic_bits",
    "rounding_report", "doubling_orbit", "projection", "projection_weights",
    "projection_drift", "mantissa_report",
    # widening the chemistry register without inventing a measurement
    "PROVENANCES", "DERIVED_ATTRIBUTES", "Attribute", "attributes_of",
    "coverage_table", "covalent_radius_model", "derived_attribute",
    "derived_coverage", "diatomic_cross_check", "element_coverage_report",
    "estimated_covalent_radii",
    # the table's own coordinates, derived from the period boundaries
    "PERIOD_BOUNDS", "MAX_Z", "Position", "PositionError", "position_of",
    "atomic_number_at", "symbol_at", "position_of_symbol",
    "periodic_report",
    # analogy as a named relation rather than a displacement
    "MODEL_NAMES", "MODELS_BY_DOMAIN", "VAGUE_RELATIONS",
    "RELATION_SYNONYMS",
    "REPORT_CASES",
    "ModelResult", "explain_analogy", "analogy_models_report",
    "periodic_step", "reciprocal_dimension", "scale_shift",
    "lexicon_relation",
    # arithmetic over register names, inside a description
    "TermArithmetic", "WORD_OPERATORS", "NAMES_SHOWN", "REPORT_EXPRESSIONS",
    "mentions_register_name", "term_arithmetic_report",
    # exact reals as processes, and written arithmetic over them
    "ExactReal", "PrecisionError", "ExpressionError", "decide_equal",
    "delta_sigma_average", "delta_sigma_bits", "delta_sigma_error",
    "exact_real_report", "expression_report", "from_fraction",
    "golay_delta_sigma", "hull_certificate", "nonzero_witness", "nth_root",
    "parse_expression", "parse_real", "real_carrier", "sqrt", "surrogate",
    "surrogate_sequence",
    # the transcendental layer
    "cos", "exp", "log", "positive_witness", "rpow", "sin", "tan",
    "transcendental_report",
    # product
    "AlgebraVector", "TwoASubalgebra", "ClassTranslation", "PositionError",
    "TWO_A_PRODUCT_COEFF", "TWO_A_INNER", "SELF_INNER",
    "POSITION_BY_INVARIANT", "axis", "zero", "axis_product",
    "algebra_product", "griess_form", "pair_invariant_classes",
    "position_name", "is_two_a_pair", "sakuma_third_axis",
    "two_a_subalgebra", "two_a_closure_report", "sample_two_a_pairs",
    "griess_trilinear", "trilinear_on_axes", "axis_trilinear",
    "semantic_distance2", "semantic_similarity",
    "coherence_of_product", "trilinear_report",
    "adjoint_matrix", "fusion_spectrum", "miyamoto_tau", "miyamoto_sigma",
    "apply_map", "is_automorphism", "preserves_form", "class_translation",
    # metric
    "DIM", "GRIESS_SCALE", "as_exact_vector", "griess_inner", "griess_norm2",
    "distance2", "exact_distance", "leech_gram", "positive_definite_report",
    "signed_cosine_squared", "compare_cosines", "angular_order",
    "triangle_inequality_holds", "distance_matrix", "nearest",
    "rank_by_distance", "Merge", "Dendrogram", "single_linkage",
    "complete_linkage", "cut_tree",
    # analogy
    "SUBSPACES", "AnalogyResult", "LatticeAnalogyResult", "analogy_target",
    "solve_analogy", "solve_analogy_objects", "nearest_golay_codeword",
    "nearest_lattice_point", "lattice_analogy", "physics_analogy",
    "element_analogy", "domain_analogy", "subspace_indices",
    "project_subspace",
    # verifier
    "Sense", "SCALAR_SENSE", "NABLA", "OPERATORS", "RELATION_LAYOUT",
    "SEMANTICS", "RelationError", "RelationVerdict", "tokenise", "parse",
    "resolve_name", "sense_of_quantity", "sense_carrier", "load_relations",
    "relation_table", "verify_relation", "verify_expression_pair",
    "verify_all", "facet_attribution_census", "verifier_report",
    # dimension layers
    "DimensionLayer", "LAYER_SUBSTRATE", "LAYER_INTEGER",
    "LAYER_RATIONAL", "LAYER_GRIESS", "LAYER_UNIVERSAL", "LAYERS",
    "escalate", "projection_report",
    # information loss at the layer boundaries
    "Witness", "indistinguishable", "classes", "resolution", "loss_count",
    "boundary", "refinement_violations", "congruence_witness",
    "is_congruent", "capacity", "sample_carriers", "carrier_sum",
    "information_loss_report",
    # six-facet decomposition
    "FACET_ORDER", "FACET_INDICES", "FACET_DESCRIPTION",
    "facet_of_coordinate", "partition_report", "projector_matrix",
    "project", "facet_coordinates", "decompose", "reassemble",
    "linearity_report", "facet_distance_breakdown", "pythagoras_report",
    "intersection_lattice_basis", "facet_lattice_report", "facets_report",
    # ten-plane Monster address stack
    "DEPTH", "PlaneAddress", "MonsterAddress", "PlaneProduct",
    "nearest_type2_classes", "nearest_two_a_partner", "geometric_tiebreak",
    "plane_address", "monster_address", "address_census", "compose_xor",
    "compose_sakuma", "position_census", "shortcut_loss_report",
    "associativity_report", "monster_stack_report",
    # multi-resolution Leech addressing
    "ROW_LABELS", "KERNEL", "SAMPLE_GRIDS", "MicroAddress",
    "column_to_fibre", "fibre_to_column", "fibre_bijection_report",
    "column_sublattice", "micro_address", "grid_shape", "grid_carrier",
    "grid_census", "grid_signature", "upscale", "reflect_horizontal",
    "reflect_vertical", "rotate180", "grid_address", "cross_inner",
    "cross_tensor", "cross_level_report", "scale_invariance_report",
    "census_collision_witness", "multires_report",
    # worked tasks
    "GRID_TASK", "TRANSFORMATIONS", "grid_task", "physics_task",
    "tasks_report",
]


def reasoning_report(full: bool = False) -> dict:
    """Recompute the kernel's headline facts on demand.

    Parameters
    ----------
    full
        When ``True`` the ``2A`` section is included.  It builds the
        exhaustive 98,280-class type-2 table, which takes several seconds on
        first call, so it is off by default.
    """
    out: dict = {
        "griess_form": metric.positive_definite_report(),
        "relations": verifier.verifier_report(),
        "term_arithmetic": term_arithmetic.term_arithmetic_report(),
    }
    if full:
        out["two_a_algebra"] = product.two_a_closure_report()
    return out
