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

from . import (analogy, analogy_models, coherence, deep_holes,
               dimension_layers, element_coverage, exact_real, facets,
               fwht_decode, information_loss, metric, monster_stack, multires,
               niemeier, periodic_table, product, real_expr, tasks,
               term_arithmetic, transcendental, units, verifier, voronoi_walk)
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
