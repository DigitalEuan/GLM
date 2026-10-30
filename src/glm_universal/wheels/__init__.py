"""``glm_universal.wheels`` -- all wheels in one place.

The wheel registry: a single package that holds the 15 monomial-law
wheels (W01-W10 engineering, W11-W15 domain) and their declared
junctions.  The existing :mod:`glm_universal.engineering.wheels` module
remains the answering surface (the ``Wheel`` dataclass, ``WHEELS`` tuple,
``derive_from``, etc.); this package re-exports those names and adds the
five domain wheels and the junction tables.

*Numbering scheme (Reading A of the reorganisation plan):*

  * W01-W10 -- the ten engineering formula wheels, unchanged from
    :mod:`glm_universal.engineering.wheels` (ids stay ``"W1"``-``"W10"``).
  * W11-W15 -- the five domain wheels, declared in
    ``studies/DOMAIN_WHEELS_STUDY.md`` and previously unimplemented.

*Junctions:*

  * ``junctions.phase66`` -- the five Phase-66 junctions between W01-W10.
  * ``junctions.domain`` -- the ten Phase-157 junctions between W01-W15,
    plus four non-identities and two aliases.
  * ``junctions.oscillator`` -- the four variants of the W09/W13
    junction (A/B/C/D), with B (``rate_only``) as the shipped choice.

*Created 29 October 2026 (Iteration 6 of the reorganisation, Phase R2).
This package is the structural face of D12 ("a layer ships with its
refinement check") for wheels: the registry is the single source of
truth for "what is a wheel?", and the junction registry is the single
source of truth for "what joins what?".*
"""
from __future__ import annotations

from typing import Dict, Tuple

# Re-export the engineering wheel infrastructure for convenience.
from ..engineering.wheels import (
    Wheel,
    FormulaCase,
    Monomial,
    parse_monomial,
    parse_equation,
    relation_vector,
    Derivation,
    derivation_certificate,
    is_derivable,
    Spoke,
    derive_from,
    wheel_spokes,
    wheel_named,
    wheel_quantities,
    render_monomial,
    case_table,
    wheels_report,
    REFERENCE_AXES,
    REFERENCE_DIMENSIONS,
    REGISTER_ALIASES,
    LAYERS,
    dimension,
    consistency,
)

# Re-export the existing engineering WHEELS tuple (W1-W10).
from ..engineering.wheels import WHEELS as _ENGINEERING_WHEELS

# Import the five domain wheels.
from .w11 import WHEEL as _W11
from .w12 import WHEEL as _W12
from .w13 import WHEEL as _W13
from .w14 import WHEEL as _W14
from .w15 import WHEEL as _W15

__all__ = [
    # Re-exported from engineering.wheels
    "Wheel", "FormulaCase", "Monomial", "parse_monomial", "parse_equation",
    "relation_vector", "Derivation", "derivation_certificate",
    "is_derivable", "Spoke", "derive_from", "wheel_spokes",
    "wheel_named", "wheel_quantities", "render_monomial", "case_table",
    "wheels_report", "REFERENCE_AXES", "REFERENCE_DIMENSIONS",
    "REGISTER_ALIASES", "LAYERS", "dimension", "consistency",
    # The registry
    "WHEELS", "DOMAIN_WHEELS", "ALL_WHEELS", "wheel_by_id",
    # Junctions
    "JUNCTIONS", "NON_IDENTITIES", "ALIASES",
]


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

#: The five domain wheels W11-W15.
DOMAIN_WHEELS: Tuple[Wheel, ...] = (_W11, _W12, _W13, _W14, _W15)

#: All 15 wheels, in order W01-W15.
ALL_WHEELS: Tuple[Wheel, ...] = _ENGINEERING_WHEELS + DOMAIN_WHEELS

#: Alias for ``ALL_WHEELS``, matching the existing ``WHEELS`` name.
WHEELS: Tuple[Wheel, ...] = ALL_WHEELS


def wheel_by_id(wheel_id: str) -> Wheel:
    """Look up a wheel by its ``id`` (e.g. ``"W9"`` or ``"W13"``).

    Raises ``KeyError`` if no wheel has that id.
    """
    for w in ALL_WHEELS:
        if w.id == wheel_id:
            return w
    raise KeyError(f"no wheel with id {wheel_id!r}")


# ---------------------------------------------------------------------------
# The junction tables (aggregated from the junctions/ subpackage)
# ---------------------------------------------------------------------------

from .junctions.phase66 import JUNCTIONS as _PHASE66_JUNCTIONS
from .junctions.phase66 import NON_IDENTITIES as _PHASE66_NON_IDENTITIES
from .junctions.domain import JUNCTIONS as _DOMAIN_JUNCTIONS
from .junctions.domain import NON_IDENTITIES as _DOMAIN_NON_IDENTITIES
from .junctions.domain import ALIASES as _DOMAIN_ALIASES

#: All declared junctions: the five Phase-66 junctions (W01-W10) plus the
#: ten Phase-157 junctions (W01-W15).
JUNCTIONS: Dict[Tuple[str, str], Tuple[str, ...]] = {}
JUNCTIONS.update(_PHASE66_JUNCTIONS)
JUNCTIONS.update(_DOMAIN_JUNCTIONS)

#: All declared non-identities.
NON_IDENTITIES: Dict[Tuple[str, str], str] = {}
NON_IDENTITIES.update(_PHASE66_NON_IDENTITIES)
NON_IDENTITIES.update(_DOMAIN_NON_IDENTITIES)

#: The aliases (e.g. ``"speed"`` -> ``"velocity"``).
ALIASES: Dict[str, str] = dict(_DOMAIN_ALIASES)
