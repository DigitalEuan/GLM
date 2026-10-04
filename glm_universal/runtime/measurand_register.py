"""``glm_universal.runtime.measurand_register`` -- measurands, declared.

Why this module exists
----------------------
Phase 86 (:mod:`glm_universal.runtime.measurands`) gave the stepwise planner
kinds of quantity on **units**.  Two things were still read by unit alone:

* A **register value** fed the formula wheels through the unit of its
  declared scale (:mod:`glm_universal.reasoning.scale_conversion`).  That
  table holds a first ionization energy as a *molar energy* -- electronvolts
  per atom carried into kilojoules per mole, which is right for comparing it
  with a bond dissociation energy -- so the planner could not feed it to a
  wheel at all, although what it *is* (the least energy one photon must carry
  to ionize the free atom) is a photon's energy.
* The junction table of :mod:`glm_universal.engineering.union` keeps
  electrical and mechanical power apart, because they are related by a
  conversion and not an identity; with no conversion law, a motor question
  was refused outright.

``studies/MEASURAND_REGISTER_STUDY.md`` (Phase 87) declares what this module
holds.  Three declarations, nothing inferred:

* :data:`REGISTER_MEASURANDS` -- per register scale, the **measurand** it
  holds: its name, kind of quantity, the entity it is per, the exact factor
  carrying one register reading into the coherent SI unit per entity, and the
  wheel quantity (and which wheels' copy of it) it is read as **by name**,
  with the argument.  A measurand with no wheel quantity by name (a radius:
  not a wavelength) is refused when given bare, and answered when the
  question itself writes the identification (``wavelength = the atomic
  radius of iron``), because both are of the kind *length*.
* :data:`CONVERSION_LAWS` -- a named efficiency ``eta`` with
  ``0 < eta <= 1`` relating the power out of a declared conversion to the
  power in, ``P_out = eta * P_in``, across one of the junction table's
  declared non-identities.  Each law is a pseudo-wheel (``C1``-``C4``) whose
  one axiom joins two wheel copies of ``power``.
* :data:`SPECIAL_UNITS` -- the elementary charge (exact since 2019) and the
  percent, read as units.

Three switches, for the study's controls: :data:`ACTIVE` (off: Phase 86 as
it was), :data:`RESTRICT` (off: a register measurand by name feeds every
wheel's copy of its quantity) and :data:`NAIVE` (on: each conversion read as
an identity, the efficiency dropped).  Exact throughout: ``int`` and
``Fraction``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Optional, Tuple

__all__ = ["ACTIVE", "RESTRICT", "NAIVE", "RegisterMeasurand",
           "REGISTER_MEASURANDS", "ConversionLaw", "CONVERSION_LAWS",
           "SPECIAL_UNITS", "ELEMENTARY_CHARGE", "measurand_of",
           "law_named", "law_of_id", "efficiency_name", "fold_units",
           "special_unit", "comparability_census", "EFFICIENCY_RANGE"]

#: Whether the register is read at all (off: Phase 86's planner).
ACTIVE = True
#: Whether a register measurand read by name is restricted to its declared
#: wheels' copy (off: the unrestricted control).
RESTRICT = True
#: Whether each conversion is read as an identity with the efficiency dropped
#: (the naive control).
NAIVE = False

#: The elementary charge in coulombs, exact by the 2019 SI definition.
ELEMENTARY_CHARGE: Fraction = Fraction(1602176634, 10 ** 28)

_EV = ELEMENTARY_CHARGE        # one electronvolt in joules, exactly


@dataclass(frozen=True)
class RegisterMeasurand:
    """One register scale, read as the measurand it holds."""

    scale: str                      # 'element:ionization_energy_eV'
    name: str                       # 'first ionization energy'
    kind: str                       # kind of quantity, for comparability
    per: str                        # the entity one reading is per
    factor: Optional[Fraction]      # into the coherent SI unit, per entity
    symbol: str                     # the coherent SI unit's symbol
    by_name: Optional[str]          # the wheel quantity it is read as
    wheels: Tuple[str, ...]         # whose copy (empty: every copy)
    argument: str                   # why
    offset: Fraction = Fraction(0)  # added after the factor (a level in
                                    # degrees Celsius: 273.15 K; Phase 99)


_PHOTON = ("one photon of this energy is the least that ")

#: **The declared register.**  One row per register scale the planner reads.
REGISTER_MEASURANDS: Tuple[RegisterMeasurand, ...] = (
    RegisterMeasurand(
        "element:ionization_energy_eV", "first ionization energy",
        "binding energy", "atom", _EV, "J", "energy", ("W10",),
        "the first ionization energy is the least energy that removes one "
        "electron from the free atom; " + _PHOTON + "ionizes it (the "
        "photoionization threshold), so by name it is a photon's energy, "
        "wheel W10, per atom: 1 eV = 1.602176634e-19 J exactly"),
    RegisterMeasurand(
        "element:electron_affinity_eV", "electron affinity",
        "binding energy", "atom", _EV, "J", "energy", ("W10",),
        "the electron affinity is the energy released when the free atom "
        "takes one electron, equal to the least energy that detaches it from "
        "the anion; " + _PHOTON + "detaches it (the photodetachment "
        "threshold), so by name it is a photon's energy, wheel W10, per atom"),
    RegisterMeasurand(
        "element:homonuclear_bde_kJ_per_mol", "bond dissociation energy",
        "binding energy", "mole of bonds", Fraction(1000), "J/mol", None, (),
        "a molar energy; no wheel names an energy per mole, so it feeds no "
        "wheel by name"),
    RegisterMeasurand(
        "element:melting_point_K", "melting point",
        "thermodynamic temperature", "substance", Fraction(1), "K",
        "temperature", (),
        "a thermodynamic temperature (a level), read by name as temperature"),
    RegisterMeasurand(
        "element:boiling_point_K", "boiling point",
        "thermodynamic temperature", "substance", Fraction(1), "K",
        "temperature", (),
        "a thermodynamic temperature (a level), read by name as temperature"),
    RegisterMeasurand(
        "fixed_point:temperature_C", "ITS-90 fixed-point temperature",
        "thermodynamic temperature", "substance", Fraction(1), "K",
        "temperature", (),
        "an assigned thermodynamic temperature (a level) held in degrees "
        "Celsius, read by name as temperature; a level in degrees Celsius is "
        "carried into kelvins by the factor 1 and the offset 273.15, exactly "
        "(Phase 99, studies/CELSIUS_REGISTER_STUDY.md)",
        Fraction(27315, 100)),
    RegisterMeasurand(
        "element:atomic_radius_pm", "atomic radius", "length", "atom",
        Fraction(1, 10 ** 12), "m", None, (),
        "a radius is a length (ISO 80000-3), and the only wheel length is a "
        "wavelength; an atom's radius is not a wave's wavelength, so it feeds "
        "no wheel by name -- written wavelength = ..., the question makes the "
        "identification itself"),
    RegisterMeasurand(
        "element:covalent_radius_pm", "covalent radius", "length", "atom",
        Fraction(1, 10 ** 12), "m", None, (),
        "a radius is a length, not a wavelength; it feeds no wheel by name"),
    RegisterMeasurand(
        "element:atomic_weight_u", "standard atomic weight",
        "mass of one entity", "atom", None, "kg", "mass", (),
        "a mass in unified atomic mass units, which is a measured mass in "
        "kilograms, not a defined one"),
    RegisterMeasurand(
        "molecule:molar_mass_u", "molar mass", "mass of one entity",
        "molecule", None, "kg", "mass", (),
        "summed from the same atomic weights, in the same unit"),
)


def measurand_of(scale: str) -> Optional[RegisterMeasurand]:
    """The register row of ``scale``, or ``None``."""
    for row in REGISTER_MEASURANDS:
        if row.scale == scale:
            return row
    return None


# ===========================================================================
# CONVERSIONS THROUGH A STATED EFFICIENCY
# ===========================================================================

#: The range an efficiency is read in: ``0 < eta <= 1``.
EFFICIENCY_RANGE = (Fraction(0), Fraction(1))


@dataclass(frozen=True)
class ConversionLaw:
    """One declared conversion: ``out = efficiency * in``, joining two wheel
    copies of ``power`` across a declared non-identity."""

    id: str                         # 'C1' -- a pseudo-wheel id
    efficiency: str                 # 'motor_efficiency'
    out_name: str                   # 'shaft_power'
    out_label: str                  # 'power@W4'
    in_name: str                    # 'electrical_power'
    in_label: str                   # 'power@W1'
    argument: str

    @property
    def axiom(self) -> str:
        """The law as an axiom over its own names."""
        if NAIVE:
            return f"{self.out_name} = {self.in_name}"
        return f"{self.out_name} = {self.efficiency} * {self.in_name}"

    @property
    def axioms(self) -> Tuple[str, ...]:
        return (self.axiom,)

    def labels(self) -> Dict[str, str]:
        out = {self.out_name: self.out_label, self.in_name: self.in_label}
        if not NAIVE:
            out[self.efficiency] = self.efficiency
        return out


#: **The declared conversions.**  Each crosses a non-identity of the junction
#: table: DC electrical power (W1) is not shaft power (W4), and shaft power is
#: not the hydraulic power ``force * velocity`` of the joined W5/W6 column.
CONVERSION_LAWS: Tuple[ConversionLaw, ...] = (
    ConversionLaw("C1", "motor_efficiency", "shaft_power", "power@W4",
                  "electrical_power", "power@W1",
                  "a motor takes DC electrical power (W1) and gives shaft "
                  "power (W4); the efficiency is the fraction delivered"),
    ConversionLaw("C2", "generator_efficiency", "electrical_power",
                  "power@W1", "shaft_power", "power@W4",
                  "a generator takes shaft power (W4) and gives DC "
                  "electrical power (W1)"),
    ConversionLaw("C3", "pump_efficiency", "hydraulic_power", "power@W5",
                  "shaft_power", "power@W4",
                  "a pump takes shaft power (W4) and gives the fluid column "
                  "the hydraulic power force * velocity (W5, joined to W6)"),
    ConversionLaw("C4", "turbine_efficiency", "shaft_power", "power@W4",
                  "hydraulic_power", "power@W5",
                  "a turbine takes the fluid column's hydraulic power (W5) "
                  "and gives shaft power (W4)"),
)


def law_named(name: Optional[str]) -> Optional[ConversionLaw]:
    """The law whose efficiency is ``name``, or ``None``."""
    for law in CONVERSION_LAWS:
        if law.efficiency == name:
            return law
    return None


def law_of_id(wheel: str) -> Optional[ConversionLaw]:
    """The law with pseudo-wheel id ``wheel``, or ``None``."""
    for law in CONVERSION_LAWS:
        if law.id == wheel:
            return law
    return None


def efficiency_name(name: Optional[str]) -> bool:
    """Whether ``name`` speaks of an efficiency at all (declared or not)."""
    return bool(name) and (name == "efficiency"
                           or name.endswith("_efficiency"))


# ===========================================================================
# UNITS: THE ELEMENTARY CHARGE AND THE PERCENT
# ===========================================================================

#: ``token -> (phrase pattern, factor, SI symbol or '' for dimension one,
#: source)``.  The pattern is matched as whole words in a unit phrase.
SPECIAL_UNITS: Dict[str, Tuple[str, Fraction, str, str]] = {
    "elementarycharge": (r"elementary charges?", ELEMENTARY_CHARGE, "C",
                         "e = 1.602176634e-19 C, exact by the 2019 SI "
                         "definition"),
    "percent": (r"percent|per cent", Fraction(1, 100), "",
                "exact by definition: one hundredth"),
}


def fold_units(text: str) -> str:
    """A unit phrase with each special unit folded into its one-word
    token (unchanged while :data:`ACTIVE` is off)."""
    if not ACTIVE:
        return text
    for token, (pattern, _f, _s, _src) in SPECIAL_UNITS.items():
        text = re.sub(r"\b(?:" + pattern + r")\b", token, text)
    return text


def special_unit(word: str) -> Optional[Tuple[Fraction, str, str]]:
    """``(factor, SI symbol, source)`` of a folded token, or ``None``."""
    if not ACTIVE or word not in SPECIAL_UNITS:
        return None
    _p, factor, symbol, source = SPECIAL_UNITS[word]
    return factor, symbol, source


# ===========================================================================
# COMPARABILITY: what the register says about the unit table's pairs
# ===========================================================================

def comparability_census() -> Dict[str, object]:
    """Every pair of scales the Phase 55 unit table relates, read against
    the register's kinds: a pair of two kinds would be a comparison the unit
    table licensed and the register withdraws."""
    from ..reasoning.scale_conversion import CONVERSIONS
    pairs, same, withdrawn, unregistered = 0, 0, [], []
    rows = list(CONVERSIONS)
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a.quantity != b.quantity:
                continue
            pairs += 1
            ma, mb = measurand_of(a.scale), measurand_of(b.scale)
            if ma is None or mb is None:
                unregistered.append((a.scale, b.scale))
            elif ma.kind == mb.kind:
                same += 1
            else:
                withdrawn.append((a.scale, b.scale))
    return {"related_pairs": pairs, "same_kind": same,
            "withdrawn": tuple(withdrawn),
            "unregistered": tuple(unregistered),
            "scales": len(rows),
            "registered": sum(1 for r in rows
                              if measurand_of(r.scale) is not None)}
