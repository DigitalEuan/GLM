"""``glm_universal.substrate`` -- the algebraic and geometric foundation.

Four modules, in dependency order:

``linalg``
    Exact integer / F_2 linear algebra (HNF, determinant, triangular solve,
    F_2 Gaussian elimination).  No module in this package performs
    floating-point arithmetic, and neither does this one.
``mog``
    The Miracle Octad Generator: the Golay code ``[24, 12, 8]``, the hexacode
    shadow, the **trio** of three octads ``O_1, O_2, O_3``, the **sextet** of
    six tetrads, the 2x2x2 MOG-cube addressing, and bijective reshaping of a
    24-vector into its ``4 x 6`` and ``3 x 8`` presentations.
``leech2``
    The 24-dimensional Leech lattice in the ``x sqrt(8)`` integer model, its
    quotient ``Lambda / 2 Lambda`` (2^24 classes), the F_2 quadratic form with
    its Witt decomposition into 12 hyperbolic planes, exact rational inner
    products, and ``2A`` (type-2) axis detection against the exhaustively
    enumerated table of 98,280 classes.
``digit_stack``
    The 10-plane 2-adic digit stack over Q / Z: lossless carrier
    reconstruction, plus bitwise facet projection and failing-facet
    attribution for vector equations.

Everything here is pure Python standard library, exact (``int`` and
``fractions.Fraction`` only), and deterministic -- no RNG is imported
anywhere in the package.
"""

from __future__ import annotations

from . import digit_stack, leech2, linalg, mog
from .digit_stack import (FACETS, STACK_DEPTH, STACK_OFFSET, DigitStack,
                          EquationVerdict, FacetReport, class_stack,
                          class_stack_fitted, class_stack_rebuild,
                          coordinate_range, depth_report,
                          derive_stack_parameters, facet_projection,
                          failing_facets, plane_facets, stack_is_faithful,
                          verify_equation)
from .leech2 import (DIM, KISSING, LEECH_BASIS, MIN_NORM2, N_CLASSES,
                     axis_of_class, b_form, class_of, class_vector,
                     form_is_plus_type, from_coords, in_leech, inner,
                     is_2a_axis, is_type2_class, leech2_report,
                     minimal_vectors, norm2, pair_census, pair_invariant,
                     q_form, rational_inner, rational_norm2, representative,
                     singular_class_count, theta_series, to_coords,
                     type2_class_table, type2_classes, type_census,
                     witt_decomposition)
from .mog import (BRICKS, COLUMNS, GOLAY, GOLAY_MASKS, GOLAY_SET, HEXACODE,
                  OCTAD_MASKS, SEXTET, TRIO, cell_of, coordinate_of_cube,
                  cube_coordinates, cube_index, cube_profile, face_parities,
                  frame, from_grid_4x6, from_trio_3x8, hexacode_shadow,
                  mog_report, sextet_of_tetrad, to_grid_4x6, to_trio_3x8,
                  trio_census, trio_of_octad)

__all__ = [
    "linalg", "mog", "leech2", "digit_stack",
    # mog
    "GOLAY", "GOLAY_MASKS", "GOLAY_SET", "OCTAD_MASKS", "HEXACODE",
    "TRIO", "SEXTET", "BRICKS", "COLUMNS",
    "cell_of", "frame", "hexacode_shadow", "cube_coordinates", "cube_index",
    "coordinate_of_cube", "cube_profile", "face_parities",
    "to_grid_4x6", "from_grid_4x6", "to_trio_3x8", "from_trio_3x8",
    "sextet_of_tetrad", "trio_of_octad", "trio_census", "mog_report",
    # leech2
    "DIM", "MIN_NORM2", "KISSING", "N_CLASSES", "LEECH_BASIS",
    "in_leech", "norm2", "inner", "rational_inner", "rational_norm2",
    "to_coords", "from_coords", "class_of", "class_vector", "representative",
    "q_form", "b_form", "witt_decomposition", "singular_class_count",
    "form_is_plus_type", "minimal_vectors", "type2_class_table",
    "type2_classes", "is_type2_class", "is_2a_axis", "axis_of_class",
    "pair_invariant", "pair_census", "theta_series", "type_census",
    "leech2_report",
    # digit_stack
    "STACK_OFFSET", "STACK_DEPTH", "DigitStack", "FacetReport",
    "EquationVerdict", "FACETS", "class_stack", "class_stack_rebuild",
    "class_stack_fitted", "stack_is_faithful", "coordinate_range",
    "derive_stack_parameters", "depth_report", "plane_facets",
    "facet_projection", "failing_facets", "verify_equation",
]
