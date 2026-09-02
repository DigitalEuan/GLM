"""``glm_universal.data_objects`` -- typed carriers over the substrate.

Five domains, one carrier shape.  Every object in this package is a point of
``Q^24`` with an exact 2-adic digit stack behind it, and every codec is held to
the same two-legged losslessness contract described in :mod:`.base`:

* the **substrate** leg -- ``class_stack_rebuild(class_stack(v)) == v``;
* the **semantic** leg -- ``decode(encode(x)) == x``.

Modules
-------
``base``
    :class:`~.base.DataObject`, the :class:`~.base.Codec` protocol, and the
    dynamic stack-parameter derivation that fits an offset and a depth to
    whatever range the data actually occupies -- no hardcoded ceiling.
``physics``
    660 physical quantities in the EXT10 basis with their SI7 projection,
    plus the collision census that shows what SI7 loses.
``elements``
    All 118 chemical elements with exact rational attributes, an explicit
    missingness mask, and a Golay address per element; plus 52 diatomic
    species with measured dissociation energies.
``molecules``
    Molecules as multi-carriers: a name and a formula are stored and nothing
    else, the faithful representation is the bundle of the constituent
    element carriers with their multiplicities, and the composite carrier
    beside it is labelled a summary and checked for collisions.
``mathematics``
    Rational matrices, exact reflections, and ``GF(2)`` / ``GF(4)`` elements.
``lexicon``
    Relational concepts over an interned -- not hashed -- vocabulary.
``harmonics``
    28 musical intervals as exact rational frequency ratios, with every
    coordinate -- equal-tempered step, tempering error, Euler's gradus,
    Tenney height -- derived from the pair ``(n, d)`` by integer comparison
    rather than by a logarithm.
``economics_register``
    21 quoted prices as exact rationals -- seven instruments over three
    consecutive quarters -- each with the magnitude bucket and mantissa in
    base 2 and base 10 computed by integer comparison rather than by a
    logarithm, and the EXT10 exponents of the quantity the price is per.
``comparison_classes``
    45 comparison classes -- *tea*, *weather*, *stellar_surface* -- each an
    exact bracket on a quantity the physics register already holds, beside
    the measure scales that place a degree word such as ``hot`` at an exact
    position on ``[0, 1]``.  A word and a class together name a magnitude,
    which is what makes ``hot`` a relative measure rather than a standalone
    concept.
``denotation``
    36 decided names -- *motion*, *magnitude*, *photon*, *cause* -- one
    verdict each on what the word denotes, with the reason it was decided
    that way.  Only one of the six verdicts makes a name dimensional, and it
    supplies no coordinate: it names a quantity the physics register already
    holds.  The other five record, on purpose, that the name is not a
    quantity at all.

Invariants
----------
Exact arithmetic (``int`` / ``fractions.Fraction``), no randomness, standard
library only.  ``float`` is refused at construction by
:func:`~.base.as_exact`, and the two frozen JSON registers under ``_data/``
store every numeric value as an ``"n/d"`` rational string so that no float
appears even in serialisation.
"""

from __future__ import annotations

from . import (base, comparison_classes, denotation, economics_register,
               elements, harmonics, lexicon,
               mathematics, molecules, physics, semantic_lexicon)
from .denotation import (DENOTATIONS, DIMENSIONAL_VERDICT, VERDICTS,
                         Denotation, decided_names, denotation_audit,
                         denotations_with_verdict, denotes_quantity,
                         verdict_of)
from .economics_register import (ECONOMICS_LAYOUT, SECTORS, WINDOWS,
                                 PriceCodec, PriceRecord,
                                 bucket_bounds_hold,
                                 compute_exact_log_bucket,
                                 denominator_quantities, economics_objects,
                                 instrument_identifiers, instrument_series,
                                 load_price_register, record_by_key,
                                 register_summary)
from .comparison_classes import (COMPARISON_CLASSES, COMPARISON_LAYOUT,
                                 MEASURE_SCALES, ComparisonClass,
                                 ComparisonClassCodec, DegreeWord,
                                 MeasureScale, class_by_name,
                                 classes_for_quantity,
                                 comparison_class_objects,
                                 comparison_classes as comparison_class_list,
                                 degree_word, lexicon_agreement,
                                 measure_scales, scale_for_quantity,
                                 scaled_quantities,
                                 QUANTITY_ALIASES, alias_audit,
                                 resolve_quantity)
from .base import (Carrier, Codec, DataObject, RoundTripFailure, Scalar,
                   StackParameters, as_exact, carrier_from_json,
                   carrier_to_json, derive_dynamic_parameters, dyadic_exponent,
                   exact_vector)
from .elements import (ELEMENT_LAYOUT, MEASURED_FIELDS, Diatomic, Element,
                       ElementCodec, element_by_symbol, element_by_z,
                       element_objects, golay_address, load_diatomic_register,
                       load_element_register, period_of,
                       periodic_separation_report)
from .harmonics import (COMMAS, HARMONIC_LAYOUT, JUST_INTERVALS,
                        SEPTIMAL_INTERVALS, Interval, IntervalCodec,
                        euler_gradus, harmonic_objects, interval_by_name,
                        interval_register, prime_exponents,
                        product_complexity, tet_error, tet_step)
from .lexicon import (LEXICON_LAYOUT, Concept, LexiconCodec, Vocabulary,
                      default_vocabulary, lexicon_objects)
from .mathematics import (EXACT_SHAPES, MATRIX_LAYOUT, FieldElement,
                          FieldElementCodec, MatrixCodec, RationalMatrix,
                          Reflection, ReflectionCodec, compose_matrices,
                          mathematics_objects, reflect)
from .molecules import (MOLECULE_FIELDS, MOLECULE_LAYOUT, MOLECULES,
                        FormulaError, Molecule, MoleculeCodec,
                        composite_collisions, format_formula,
                        formula_from_bundle, load_molecule_register,
                        molecule_bundle, molecule_by_name,
                        molecule_from_formula, molecule_objects,
                        molecules_report, object_from_formula, parse_formula)
from .physics import (AXES_EXT10, AXES_SI7, PHYSICS_LAYOUT, PhysicsCodec,
                      Quantity, basis_collision_report, dimension_string,
                      load_physics_register, physics_objects,
                      quantity_by_name, si7_projection_lossy)
from .semantic_lexicon import (MAX_SEMANTIC_RELATIONS, SEMANTIC_LAYOUT,
                               SEMANTIC_PRIMITIVE_NAMES, SEMANTIC_PRIMITIVES,
                               SEMANTIC_SAMPLE_CONCEPTS, SemanticConcept,
                               SemanticLexiconCodec, default_semantic_vocabulary,
                               semantic_lexicon_objects)

__all__ = [
    "base", "physics", "elements", "mathematics", "lexicon",
    "semantic_lexicon", "molecules", "harmonics", "comparison_classes",
    "denotation", "economics_register",
    # denotation -- what the undimensioned names denote, decided by hand
    "DENOTATIONS", "DIMENSIONAL_VERDICT", "VERDICTS", "Denotation",
    "decided_names", "denotation_audit", "denotations_with_verdict",
    "denotes_quantity", "verdict_of",
    # economics -- quoted prices as exact rationals, with a magnitude
    "ECONOMICS_LAYOUT", "SECTORS", "WINDOWS", "PriceRecord", "PriceCodec",
    "compute_exact_log_bucket", "bucket_bounds_hold",
    "denominator_quantities", "economics_objects", "instrument_identifiers",
    "instrument_series", "load_price_register", "record_by_key",
    "register_summary",
    # comparison classes and measure scales
    "COMPARISON_LAYOUT", "COMPARISON_CLASSES", "MEASURE_SCALES",
    "ComparisonClass", "ComparisonClassCodec", "DegreeWord", "MeasureScale",
    "comparison_class_list", "class_by_name", "classes_for_quantity",
    "measure_scales", "scale_for_quantity", "degree_word",
    "scaled_quantities", "comparison_class_objects", "lexicon_agreement",
    "QUANTITY_ALIASES", "resolve_quantity", "alias_audit",
    # harmonics
    "HARMONIC_LAYOUT", "Interval", "IntervalCodec", "JUST_INTERVALS",
    "SEPTIMAL_INTERVALS", "COMMAS", "prime_exponents", "product_complexity",
    "euler_gradus", "tet_step", "tet_error", "interval_register",
    "interval_by_name", "harmonic_objects",
    # base
    "DataObject", "Codec", "StackParameters", "RoundTripFailure",
    "Carrier", "Scalar", "as_exact", "exact_vector",
    "derive_dynamic_parameters", "dyadic_exponent",
    "carrier_to_json", "carrier_from_json",
    # physics
    "AXES_EXT10", "AXES_SI7", "PHYSICS_LAYOUT", "Quantity", "PhysicsCodec",
    "load_physics_register", "physics_objects", "quantity_by_name",
    "si7_projection_lossy", "basis_collision_report", "dimension_string",
    # elements
    "ELEMENT_LAYOUT", "MEASURED_FIELDS", "Element", "Diatomic",
    "ElementCodec", "load_element_register", "load_diatomic_register",
    "element_objects", "element_by_symbol", "element_by_z", "period_of",
    "golay_address", "periodic_separation_report",
    # molecules
    "MOLECULE_LAYOUT", "MOLECULE_FIELDS", "MOLECULES", "FormulaError",
    "Molecule", "MoleculeCodec", "parse_formula", "format_formula",
    "molecule_by_name", "load_molecule_register", "molecule_objects",
    "molecule_from_formula", "object_from_formula",
    "molecule_bundle", "formula_from_bundle", "composite_collisions",
    "molecules_report",
    # mathematics
    "EXACT_SHAPES", "MATRIX_LAYOUT", "RationalMatrix", "Reflection",
    "FieldElement", "MatrixCodec", "ReflectionCodec", "FieldElementCodec",
    "mathematics_objects", "reflect", "compose_matrices",
    # lexicon (legacy index-based)
    "LEXICON_LAYOUT", "Vocabulary", "Concept", "LexiconCodec",
    "default_vocabulary", "lexicon_objects",
    # semantic_lexicon (meaning-based)
    "SEMANTIC_LAYOUT", "SEMANTIC_PRIMITIVES", "SEMANTIC_PRIMITIVE_NAMES",
    "SEMANTIC_SAMPLE_CONCEPTS", "MAX_SEMANTIC_RELATIONS",
    "SemanticConcept", "SemanticLexiconCodec",
    "default_semantic_vocabulary", "semantic_lexicon_objects",
]


def all_objects() -> dict:
    """Every carrier this package can build, grouped by domain.

    The lexicon's codec is returned with its objects because its vocabulary is
    needed to read them back.
    """
    lex_objects, lex_codec = lexicon_objects()
    return {
        "physics": physics_objects(),
        "chemistry": element_objects(),
        "molecules": molecule_objects(),
        "mathematics": mathematics_objects(),
        "harmonics": harmonic_objects(),
        "economics": economics_objects(),
        "comparison": comparison_class_objects(),
        "lexicon": lex_objects,
        "lexicon_codec": lex_codec,
    }
