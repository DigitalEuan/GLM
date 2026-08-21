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

from . import analogy, metric, product, verifier
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
                      class_translation, fusion_spectrum, griess_form,
                      is_automorphism, is_two_a_pair, miyamoto_sigma,
                      miyamoto_tau, pair_invariant_classes, position_name,
                      preserves_form, sakuma_third_axis, sample_two_a_pairs,
                      two_a_closure_report, two_a_subalgebra, zero)
from .verifier import (NABLA, OPERATORS, RELATION_LAYOUT, SCALAR_SENSE,
                       SEMANTICS, RelationError, RelationVerdict, Sense,
                       facet_attribution_census, load_relations, parse,
                       relation_table, resolve_name, sense_carrier,
                       sense_of_quantity, tokenise, verifier_report,
                       verify_all, verify_expression_pair, verify_relation)

__all__ = [
    "product", "metric", "analogy", "verifier",
    # product
    "AlgebraVector", "TwoASubalgebra", "ClassTranslation", "PositionError",
    "TWO_A_PRODUCT_COEFF", "TWO_A_INNER", "SELF_INNER",
    "POSITION_BY_INVARIANT", "axis", "zero", "axis_product",
    "algebra_product", "griess_form", "pair_invariant_classes",
    "position_name", "is_two_a_pair", "sakuma_third_axis",
    "two_a_subalgebra", "two_a_closure_report", "sample_two_a_pairs",
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
    }
    if full:
        out["two_a_algebra"] = product.two_a_closure_report()
    return out
