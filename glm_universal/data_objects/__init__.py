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

Invariants
----------
Exact arithmetic (``int`` / ``fractions.Fraction``), no randomness, standard
library only.  ``float`` is refused at construction by
:func:`~.base.as_exact`, and the two frozen JSON registers under ``_data/``
store every numeric value as an ``"n/d"`` rational string so that no float
appears even in serialisation.
"""

from __future__ import annotations

from . import (base, elements, lexicon, mathematics, molecules, physics,
               semantic_lexicon)
from .base import (Carrier, Codec, DataObject, RoundTripFailure, Scalar,
                   StackParameters, as_exact, carrier_from_json,
                   carrier_to_json, derive_dynamic_parameters, dyadic_exponent,
                   exact_vector)
from .elements import (ELEMENT_LAYOUT, MEASURED_FIELDS, Diatomic, Element,
                       ElementCodec, element_by_symbol, element_by_z,
                       element_objects, golay_address, load_diatomic_register,
                       load_element_register, period_of,
                       periodic_separation_report)
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
                        molecule_bundle, molecule_by_name, molecule_objects,
                        molecules_report, parse_formula)
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
    "semantic_lexicon", "molecules",
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
        "lexicon": lex_objects,
        "lexicon_codec": lex_codec,
    }
