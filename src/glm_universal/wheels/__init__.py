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

*Provision wheels (a second family, beside the 15) -- PROVISIONAL:*

  * ``PROVISION_WHEELS`` -- wheels that answer a *claim* (an integer
    prefix, a group order) with an identifier or stay silent, rather than
    derive a formula: ``IW`` the Integer Wheel
    (:mod:`glm_universal.wheels.integer_wheel`, OEIS sequences) and ``MW``
    the Monster Wheel (:mod:`glm_universal.wheels.monster_wheel`, the
    Integer Wheel plus the 26 sporadic simple groups), taken from the
    supplied ``glm_wheels_bundle`` (``studies/INTEGER_WHEEL_STUDY.md``;
    contracts in ``Wheels/IntegerWheel.lean`` and
    ``Wheels/SporadicOrders.lean``).  They are *not* ``Wheel`` objects and
    are not in ``WHEELS``/``ALL_WHEELS``, whose 15 monomial-law wheels are
    unchanged; each is a :class:`ProvisionWheel` descriptor whose
    ``build()`` imports its module only when called.  The query surface
    over them is :func:`glm_universal.wheels.sequence_query.answer_sequence_query`.

*The cent family (a third family, beside the 15 and the provision wheels)
-- PROVISIONAL:*

  * ``CENT_WHEEL_IDS`` / :func:`cent_family` -- fifteen monomial-law
    wheels (W16-W25, W28, W29, W32-W34: induction, gravitation, gases,
    electromagnetism, beams, fracture, kinetics, electrochemistry,
    semiconductors, plasma, Josephson, spin, capillarity, heat transfer,
    haemodynamics), taken from the supplied ``cent_compiler_v12`` with
    the corrections and drops ``studies/CENT_WHEELS_STUDY.md`` records
    (:mod:`glm_universal.wheels.cent_wheels`; balance, certificates and
    refusals in ``Wheels/CentWheels.lean``).  They are ``Wheel`` objects
    read by a rational-power engine (fractional exponents exact), kept out
    of ``WHEELS``/``ALL_WHEELS`` so the 15-wheel registry and every
    measurement over it are unchanged.  The query surface is
    :func:`answer_derivability` (the registry first, then the cent wheels).

*Provisional families (the owner's decision of 31 October 2026):*

  Both families above are installed here **provisionally**: they passed
  their intake's tests and measurement and their Lean files are written
  (``Wheels/IntegerWheel.lean``, ``Wheels/SporadicOrders.lean``,
  ``Wheels/CentWheels.lean``, in the build tree and the axiom audit), but
  no Lean build has confirmed those files yet.  The owner decided to keep
  them "in the wheels folder now, clearly marked provisional until my Lean
  build log confirms them".  The register of provisional families is
  :data:`PROVISIONAL_REGISTER` (``wheels/_data/provisional.json``, one entry
  per intake item, with the decision, the wheels, the modules and the Lean
  files); :func:`provisional_status` gives the note an answer carries, the
  ``sequence`` kind and :func:`answer_derivability` attach it, and
  ``python3 -m glm_universal.intake check`` requires the register and the
  ledger's ``provisional`` parts to agree.  When ``scripts/rebuild_lean.sh``
  passes, ``python3 -m glm_universal.intake advance <item> absorbed`` (or
  ``absorb-staged <item>`` while other parts of the item stay open) checks the
  build record against the Lean files, marks the parts absorbed and removes
  the item's entry from the register; nothing else changes.

*Created 29 October 2026 (Iteration 6 of the reorganisation, Phase R2).
This package is the structural face of D12 ("a layer ships with its
refinement check") for wheels: the registry is the single source of
truth for "what is a wheel?", and the junction registry is the single
source of truth for "what joins what?".*

*Last altered 31 October 2026 (intake of glm_wheels_bundle, directive D22:
the provision family ``PROVISION_WHEELS`` added; the 15-wheel registry is
untouched.  Intake of cent_compiler_v12, directive D22: the cent family
``CENT_WHEEL_IDS`` / ``cent_family`` / ``answer_derivability`` added; the
15-wheel registry and the provision family are untouched.  Then, the same
day, the owner's decision: both families stay here, marked provisional until
the Lean build confirms them -- :data:`PROVISIONAL_REGISTER`,
:func:`provisional_items`, :func:`provisional_status`,
:attr:`ProvisionWheel.status`; :func:`answer_derivability` adds the note).*
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from ..constants import WHEELS_DIR

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
    # The provision family
    "ProvisionWheel", "PROVISION_WHEELS", "provision_wheel",
    # The cent family
    "CENT_WHEEL_IDS", "CENT_STUDY", "CENT_LEAN", "cent_family", "answer_derivability",
    # Families installed provisionally (Lean written, build pending)
    "PROVISIONAL_REGISTER", "provisional_items", "provisional_status",
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


# ---------------------------------------------------------------------------
# The provision family (added 31 October 2026, intake of glm_wheels_bundle)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProvisionWheel:
    """A provision wheel: answers a claim with an identifier, or is silent.

    ``module`` is the module (below this package) holding the wheel,
    ``builder`` the name of the function there that builds the absorbed
    wheel, ``lean`` the Lean files stating its contract.
    """

    id: str
    title: str
    module: str
    builder: str
    study: str
    lean: Tuple[str, ...]

    def build(self):
        """The wheel (imports its module now, never at package import;
        touches no network)."""
        return getattr(import_module(f"{__name__}.{self.module}"), self.builder)()

    @property
    def status(self) -> str:
        """``"provisional: ..."`` while the wheel is in
        :data:`PROVISIONAL_REGISTER` (Lean written, the owner's build
        pending), else ``"absorbed"``."""
        return provisional_status(self.id) or "absorbed"


#: The provision wheels, a family separate from the 15 monomial-law wheels.
PROVISION_WHEELS: Tuple[ProvisionWheel, ...] = (
    ProvisionWheel("IW", "Integer Wheel (audited OEIS sequences)", "integer_wheel",
                   "default_wheel", "studies/INTEGER_WHEEL_STUDY.md",
                   ("Wheels/IntegerWheel.lean",)),
    ProvisionWheel("MW", "Monster Wheel (Integer Wheel + the 26 sporadic groups)",
                   "monster_wheel", "default_monster_wheel",
                   "studies/INTEGER_WHEEL_STUDY.md",
                   ("Wheels/IntegerWheel.lean", "Wheels/SporadicOrders.lean")),
)


def provision_wheel(wheel_id: str) -> ProvisionWheel:
    """The provision wheel with this ``id`` (``"IW"`` or ``"MW"``).

    Raises ``KeyError`` if there is none.
    """
    for p in PROVISION_WHEELS:
        if p.id == wheel_id:
            return p
    raise KeyError(f"no provision wheel with id {wheel_id!r}")


# ---------------------------------------------------------------------------
# The cent family (added 31 October 2026, intake of cent_compiler_v12)
# ---------------------------------------------------------------------------

#: The ids of the absorbed cent wheels, in order (W26, W27, W30 and W31 were
#: never supplied; W35 lost both axioms under the study's rule R).
CENT_WHEEL_IDS: Tuple[str, ...] = (
    "W16", "W17", "W18", "W19", "W20", "W21", "W22", "W23", "W24", "W25",
    "W28", "W29", "W32", "W33", "W34",
)

#: The study and the Lean file of the cent family.
CENT_STUDY = "studies/CENT_WHEELS_STUDY.md"
CENT_LEAN: Tuple[str, ...] = ("Wheels/CentWheels.lean",)


def cent_family() -> Tuple[Wheel, ...]:
    """The absorbed cent wheels (imports
    :mod:`glm_universal.wheels.cent_wheels` now, never at package import; the
    function is not named after the module, whose import would rebind it)."""
    return import_module(f"{__name__}.cent_wheels").CENT_WHEELS


def answer_derivability(equation: str, wheel_id=None, with_registry: bool = True):
    """Does ``equation`` follow from the GLM's wheels?  The 15 registry wheels
    first (integer engine), then the cent wheels (rational-power engine); with
    ``wheel_id`` that one wheel only.  See
    :func:`glm_universal.wheels.cent_wheels.answer_derivability`.

    When the answer rests on a wheel installed provisionally (a cent wheel
    while ``cent_compiler_v12`` is in :data:`PROVISIONAL_REGISTER`), the
    result carries ``"provisional"``: the note of :func:`provisional_status`.
    """
    out = import_module(f"{__name__}.cent_wheels").answer_derivability(
        equation, wheel_id=wheel_id, with_registry=with_registry)
    note = provisional_status(out.get("wheel")) if out.get("wheel") else None
    if note:
        out["provisional"] = note
    return out


# ---------------------------------------------------------------------------
# Families installed provisionally (the owner's decision, 31 October 2026)
# ---------------------------------------------------------------------------

#: The register of wheel families installed ahead of their Lean build:
#: ``{"items": {<intake item id>: {"wheels", "modules", "lean", "decision",
#: "date"}}}``.  Written by the intake (``glm_universal.intake``), which removes
#: an item's entry when it absorbs the item on a build record that verifies
#: its Lean files; read here, never written.
PROVISIONAL_REGISTER: Path = WHEELS_DIR / "_data" / "provisional.json"

#: The ``state`` of a register entry whose item was absorbed ahead of its
#: Lean build by the owner's decision of 1 November 2026, on its measurements
#: and a standalone Lean check (an entry without ``state`` is provisional);
#: the same words as :data:`glm_universal.intake.ledger.AHEAD_STATE`.
AHEAD_STATE = "absorbed ahead of the build"


def provisional_items(path: Optional[Path] = None) -> Dict[str, Mapping[str, Any]]:
    """The register's entries, by intake item id (empty when the register is
    absent or lists nothing).  Read afresh on every call: the intake may have
    just absorbed an item."""
    target = Path(path) if path is not None else PROVISIONAL_REGISTER
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    items = data.get("items") or {}
    return {str(k): v for k, v in items.items() if isinstance(v, Mapping)}


def provisional_status(key: Optional[str], path: Optional[Path] = None) -> Optional[str]:
    """The note an answer carries when ``key`` -- a wheel id (``"IW"``,
    ``"MW"``, ``"W16"`` ...) or a module below this package
    (``"wheels/sequence_query"``) -- belongs to a family installed
    provisionally; ``None`` when it does not (an absorbed wheel, or one of
    the 15)."""
    if not key:
        return None
    for item, entry in provisional_items(path).items():
        if key in tuple(entry.get("wheels") or ()) or key in tuple(entry.get("modules") or ()):
            #  The register names Lean modules without their suffix; the
            #  note quotes them so (a literal suffix here would read, to the
            #  sign-off ledger, as a glob over the whole Lean development).
            lean = ", ".join(str(n) for n in entry.get("lean") or ())
            if entry.get("state") == AHEAD_STATE:
                return (f"{AHEAD_STATE}: absorbed by the owner's decision of "
                        f"{entry.get('date', 'an unrecorded date')} (intake item {item}) "
                        f"on its measurements and a standalone Lean check; the owner's "
                        f"build (scripts/rebuild_lean.sh) has still to confirm its Lean "
                        f"({lean})")
            return (f"provisional: installed ahead of its Lean build by the owner's "
                    f"decision of {entry.get('date', 'an unrecorded date')} (intake item "
                    f"{item}); its Lean ({lean}) is written and awaits the owner's "
                    f"build (scripts/rebuild_lean.sh)")
    return None
