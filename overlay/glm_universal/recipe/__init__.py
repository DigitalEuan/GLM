"""The recipe made into an object.

Every capability in this package was built by hand from one recipe: a register
of carriers whose coordinates derive from something already held, a reading
over them, an audit of what the reading gains and gives up, a query that
answers where the registers decide and refuses where they do not, and a
machine-checked statement of the part that is not a measurement.

This sub-package is that recipe's input and its single generic path.

``glm_universal.recipe.spec``
    A :class:`~glm_universal.recipe.spec.DomainSpec` -- the declarative
    description of a domain -- and the shared primitives a description is
    written in, with the domain-specific *judgements* marked apart so they can
    be counted rather than hidden.
``glm_universal.recipe.build``
    The one path: description to carriers, readings, widening audit, query
    surface and refusal boundary, knowing nothing about any domain.
``glm_universal.recipe.descriptions``
    Three domains built by hand in earlier rounds -- comparison classes,
    harmonics and prices -- written down as descriptions.
``glm_universal.recipe.report``
    The measured result: each of the three deleted and regenerated from its
    description, compared carrier by carrier and figure by figure against the
    register the hand-written module ships.

``RequestProject/GLM/Recipe.lean`` proves the part of the path that is not a
measurement: that a wider selection of coordinates always refines a narrower
one and is the least reading keeping both, that what a widening gains is
exactly the pairs it splits, that keys which determine the objects give a
lossless carrier, that a coordinate a description does not derive is refused,
and that two descriptions agreeing on the coordinates agree on the carriers,
the reading and every answer -- which is regeneration, stated formally.
"""

from __future__ import annotations

from .spec import Coordinate, Derivation, DomainSpec, Reading, judgement
from .build import (answer, boundary, carrier, carriers, classes, describe,
                    domain_report, read_back, read_back_audit, refines,
                    refusal_audit, regenerate, regeneration, register,
                    resolution, view, widening_audit)
from .descriptions import (COMPARISON_DESCRIPTION, DESCRIPTIONS,
                           ECONOMICS_DESCRIPTION, HARMONIC_DESCRIPTION,
                           described_domains, description_by_name)
from .report import ask, recipe_report

__all__ = [
    "Coordinate", "Derivation", "DomainSpec", "Reading", "judgement",
    "answer", "boundary", "carrier", "carriers", "classes", "describe",
    "domain_report", "read_back", "read_back_audit", "refines",
    "refusal_audit", "regenerate", "regeneration", "register", "resolution",
    "view", "widening_audit",
    "COMPARISON_DESCRIPTION", "DESCRIPTIONS", "ECONOMICS_DESCRIPTION",
    "HARMONIC_DESCRIPTION", "described_domains", "description_by_name",
    "ask", "recipe_report",
]
