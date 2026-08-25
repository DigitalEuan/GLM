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
``golay_decode``
    Complete syndrome decoding of the Golay code: the coset leader table, the
    exact distance to the code, *every* nearest codeword, and the proof (via
    the Steiner system ``S(5,8,24)``) that a weight-5 error is decoded
    confidently and wrongly by any nearest-codeword rule.  This module retired
    the package's legacy ``snap`` decode.
``isomorphism``
    The legacy-to-core coordinate permutation: the only sanctioned bridge
    between the project's earlier Golay frame and this package's canonical
    one, the proof that it is an isometry and therefore safe to wrap around
    the decoder, and the bulk migration of concepts, CRG edges and
    hexcolour addresses.
``leech_construct``
    The construction ladder for ``Lambda_24``: Construction A (kissing 48),
    Construction B (98,256) and Construction C with the mod-8 coordinate-sum
    condition, which restores the true 196,560 minimal vectors; the multi-mod
    sieve (mod 2 / 4 / 8) that decides membership; and the shared lattice
    helpers used by the six-facet decomposition.
``digit_stack``
    The 10-plane 2-adic digit stack over Q / Z: lossless carrier
    reconstruction, plus bitwise facet projection and failing-facet
    attribution for vector equations.

Everything here is pure Python standard library, exact (``int`` and
``fractions.Fraction`` only), and deterministic -- no RNG is imported
anywhere in the package.
"""

from __future__ import annotations

from . import (digit_stack, golay_decode, isomorphism, leech2,
               leech_construct, linalg, mog, superposition)
from .isomorphism import (CONCEPT_SPEC, CORE_TO_LEGACY, EDGE_SPEC,
                          HEXCOLOUR_SPEC, LEGACY_TO_CORE, MigrationSpec,
                          code_report, compose_permutations, decode_legacy,
                          hexcolour_to_mask, invert_permutation,
                          is_golay_automorphism, is_permutation,
                          isometry_report, legacy_code,
                          legacy_decoder_comparison,
                          legacy_snap_in_legacy_frame, mask_to_hexcolour,
                          migrate_dataset, migrate_hexcolour, migrate_record,
                          migrate_records, migration_report, permute_indices,
                          permute_mask, permute_vector, sample_dataset,
                          shared_codewords, to_core_mask, to_core_vector,
                          to_legacy_mask, to_legacy_vector,
                          weight_distribution)
from .leech_construct import (LEVEL_A, LEVEL_B, LEVEL_C, LEVELS,
                              agrees_with_leech2, even_parity,
                              golay_condition, golay_support, in_level,
                              kissing_of_level, leech_construction_report,
                              level_of, minimal_shape_census,
                              minimal_vectors_of_level, mod_profile,
                              mod_sieve, necessity_report,
                              projection_lattice_basis, small_shell_minimum,
                              sum_condition, supported_sublattice_basis)
from .golay_decode import (COVERING_RADIUS, PACKING_RADIUS, Decoding,
                           coset_census, coset_leaders, coset_table,
                           coset_weight, decode_complete, decode_or_detect,
                           decoder_comparison_report, golay_decode_report,
                           is_guaranteed_decodable, steiner_system_report,
                           weight5_miscorrection_report)
from .superposition import (ALL_ONES, TIE_COUNT, Collapse, Superposition,
                            alphabet_expansion_report, bundle_f2,
                            bundle_rational, bundling_report, collapse,
                            collapse_report, recover_from_bundle,
                            sextet_cycle_reading, sextet_partition_report,
                            superpose, superposition_report)
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
    "linalg", "mog", "leech2", "digit_stack", "golay_decode",
    "leech_construct", "isomorphism", "superposition",
    # isomorphism
    "LEGACY_TO_CORE", "CORE_TO_LEGACY", "MigrationSpec", "CONCEPT_SPEC",
    "EDGE_SPEC", "HEXCOLOUR_SPEC", "is_permutation", "invert_permutation",
    "compose_permutations", "permute_mask", "permute_vector",
    "permute_indices", "to_core_mask", "to_legacy_mask", "to_core_vector",
    "to_legacy_vector", "hexcolour_to_mask", "mask_to_hexcolour",
    "migrate_hexcolour", "legacy_code", "shared_codewords",
    "weight_distribution", "is_golay_automorphism", "isometry_report",
    "code_report", "decode_legacy", "legacy_snap_in_legacy_frame",
    "legacy_decoder_comparison", "migrate_record", "migrate_records",
    "migrate_dataset", "sample_dataset", "migration_report",
    # leech_construct
    "LEVEL_A", "LEVEL_B", "LEVEL_C", "LEVELS", "even_parity",
    "golay_support", "golay_condition", "sum_condition", "in_level",
    "level_of", "minimal_vectors_of_level", "minimal_shape_census",
    "kissing_of_level", "mod_profile", "mod_sieve",
    "projection_lattice_basis", "supported_sublattice_basis",
    "small_shell_minimum", "necessity_report", "agrees_with_leech2",
    "leech_construction_report",
    # golay_decode
    "Decoding", "PACKING_RADIUS", "COVERING_RADIUS",
    "coset_table", "coset_leaders", "coset_weight", "coset_census",
    "decode_complete", "decode_or_detect", "is_guaranteed_decodable",
    "decoder_comparison_report", "steiner_system_report",
    "weight5_miscorrection_report", "golay_decode_report",
    # superposition
    "ALL_ONES", "TIE_COUNT", "Superposition", "Collapse", "superpose",
    "bundle_f2", "bundle_rational", "recover_from_bundle", "collapse",
    "sextet_cycle_reading", "sextet_partition_report", "bundling_report",
    "collapse_report", "alphabet_expansion_report", "superposition_report",
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
