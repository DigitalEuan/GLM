"""``glm_universal.reasoning.element_coverage`` -- filling a sparse register.

The problem
-----------
The element register holds 118 elements and sixteen measured fields, and
several of those fields are mostly empty: covalent radius and homonuclear
bond dissociation energy are the worst.  The obvious repair is to paste in
a bigger table.  This module does not do that.  Nothing here invents a
measurement.

Three honest ways to widen coverage
-----------------------------------
1. **Derive.**  Some attributes are exact functions of ones already
   present: molar volume is atomic weight over density, the liquid range is
   the boiling point less the melting point, the Mulliken electronegativity
   is the mean of the ionisation energy and the electron affinity.  These
   are new attributes, exactly computed, and they are as reliable as what
   they are computed from.  They are labelled ``derived``.

2. **Estimate, with the error measured.**  Covalent radius correlates with
   atomic radius.  Fitting a line, in exact rational arithmetic, on the
   elements where *both* are known gives a rule that extends the attribute
   to every element with an atomic radius -- but an estimate is not a
   measurement, so each is labelled ``estimated`` and the fit's residuals
   are reported beside it.  A caller that wants only measurements can have
   only measurements.

3. **Cross-check.**  Where two registers hold the same-sounding quantity,
   compare them.  The element register's homonuclear bond dissociation
   energy and the diatomic register's ``D0`` agree for some elements and
   differ by hundreds of kJ/mol for others -- because they are not the same
   quantity: one is a single-bond enthalpy, the other the dissociation
   energy of the diatomic molecule, and for carbon and phosphorus the
   molecule is not held together by one single bond.  The comparison is
   reported as a comparison, and the two are *not* merged.  That is the
   same rule the rest of the package works to: a layer may add, never
   conflate.

Everything is exact ``Fraction`` arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Tuple

from ..data_objects import elements as el

__all__ = [
    "PROVENANCES",
    "DERIVED_ATTRIBUTES",
    "Attribute",
    "coverage_table",
    "derived_attribute",
    "derived_coverage",
    "covalent_radius_model",
    "estimated_covalent_radii",
    "diatomic_cross_check",
    "attributes_of",
    "element_coverage_report",
]

#: How a value came to be.  Nothing is ever promoted from one to another.
PROVENANCES: Tuple[str, ...] = ("measured", "derived", "estimated")


@dataclass(frozen=True)
class Attribute:
    """One attribute of one element, with where it came from."""

    name: str
    value: Optional[Fraction]
    unit: str
    provenance: str
    basis: str


# ===========================================================================
# 1.  WHAT IS THERE
# ===========================================================================

def coverage_table() -> Dict[str, object]:
    """How many of the 118 elements carry each measured field."""
    elements = el.load_element_register()
    counts: Dict[str, int] = {}
    for field in el.MEASURED_FIELDS:
        if field in ("period", "electron_count_check"):
            continue
        counts[field] = sum(1 for e in elements
                            if getattr(e, field, None) is not None)
    total = len(elements)
    sparse = tuple(sorted((name for name, n in counts.items()
                           if n * 2 < total),
                          key=lambda name: counts[name]))
    return {
        "elements": total,
        "counts": dict(sorted(counts.items())),
        "complete_fields": tuple(sorted(name for name, n in counts.items()
                                        if n == total)),
        "sparse_fields": sparse,
        "sparsest": sparse[0] if sparse else None,
        "total_cells": total * len(counts),
        "filled_cells": sum(counts.values()),
    }


# ===========================================================================
# 2.  DERIVED ATTRIBUTES -- EXACT FUNCTIONS OF WHAT IS ALREADY THERE
# ===========================================================================

def _molar_volume(element: el.Element) -> Optional[Fraction]:
    if element.atomic_weight_u is None or element.density_g_per_cm3 is None:
        return None
    if element.density_g_per_cm3 == 0:
        return None
    return Fraction(element.atomic_weight_u) / element.density_g_per_cm3


def _liquid_range(element: el.Element) -> Optional[Fraction]:
    if element.melting_point_K is None or element.boiling_point_K is None:
        return None
    return Fraction(element.boiling_point_K) - Fraction(element.melting_point_K)


def _mulliken(element: el.Element) -> Optional[Fraction]:
    if element.ionization_energy_eV is None \
            or element.electron_affinity_eV is None:
        return None
    return (Fraction(element.ionization_energy_eV)
            + Fraction(element.electron_affinity_eV)) / 2


def _valence_shell_load(element: el.Element) -> Optional[Fraction]:
    """Valence electrons per unit of atomic radius -- a crowding measure."""
    if element.valence_electrons is None or element.atomic_radius_pm is None:
        return None
    if element.atomic_radius_pm == 0:
        return None
    return Fraction(element.valence_electrons) / element.atomic_radius_pm


#: The derived attributes, each with the exact rule that produces it.
DERIVED_ATTRIBUTES: Dict[str, Tuple[Callable[[el.Element],
                                             Optional[Fraction]], str, str]] = {
    "molar_volume_cm3_per_mol": (
        _molar_volume, "cm^3/mol", "atomic_weight_u / density_g_per_cm3"),
    "liquid_range_K": (
        _liquid_range, "K", "boiling_point_K - melting_point_K"),
    "mulliken_electronegativity_eV": (
        _mulliken, "eV",
        "(ionization_energy_eV + electron_affinity_eV) / 2"),
    "valence_density_per_pm": (
        _valence_shell_load, "1/pm",
        "valence_electrons / atomic_radius_pm"),
}


def derived_attribute(element: el.Element, name: str) -> Attribute:
    """One derived attribute of one element, or an absent one with a reason."""
    if name not in DERIVED_ATTRIBUTES:
        raise KeyError(f"derived_attribute: unknown attribute {name!r}")
    rule, unit, basis = DERIVED_ATTRIBUTES[name]
    return Attribute(name=name, value=rule(element), unit=unit,
                     provenance="derived", basis=basis)


def derived_coverage() -> Dict[str, object]:
    """How far each derived attribute reaches, and what it is derived from."""
    elements = el.load_element_register()
    rows: Dict[str, Dict[str, object]] = {}
    for name, (rule, unit, basis) in sorted(DERIVED_ATTRIBUTES.items()):
        available = tuple(e.symbol for e in elements if rule(e) is not None)
        rows[name] = {
            "unit": unit,
            "basis": basis,
            "available": len(available),
            "of": len(elements),
            "examples": tuple(available[:6]),
        }
    return {
        "attributes": rows,
        "attribute_count": len(DERIVED_ATTRIBUTES),
        "new_cells": sum(int(row["available"]) for row in rows.values()),
    }


# ===========================================================================
# 3.  ESTIMATES, WITH THE ERROR MEASURED
# ===========================================================================

def covalent_radius_model() -> Dict[str, object]:
    """An exact rational least-squares line: covalent radius vs atomic radius.

    The fit is computed on the elements where both are known, and its
    residuals on exactly those elements are reported.  There is no held-out
    set here and the report says so: what is measured is how well the line
    reproduces the data it was fitted to, which is an upper bound on how
    well it does anywhere else.
    """
    elements = el.load_element_register()
    pairs = [(e.symbol, Fraction(e.atomic_radius_pm),
              Fraction(e.covalent_radius_pm))
             for e in elements
             if e.atomic_radius_pm is not None
             and e.covalent_radius_pm is not None]
    n = len(pairs)
    if n < 2:
        return {"fitted": False, "reason": "fewer than two elements carry both"}
    sx = sum(p[1] for p in pairs)
    sy = sum(p[2] for p in pairs)
    sxx = sum(p[1] * p[1] for p in pairs)
    sxy = sum(p[1] * p[2] for p in pairs)
    denominator = n * sxx - sx * sx
    if denominator == 0:
        return {"fitted": False, "reason": "the atomic radii are all equal"}
    slope = (n * sxy - sx * sy) / denominator
    intercept = (sy * sxx - sx * sxy) / denominator
    residuals = [(symbol, covalent - (slope * atomic + intercept))
                 for symbol, atomic, covalent in pairs]
    worst = max(residuals, key=lambda r: abs(r[1]))
    return {
        "fitted": True,
        "fitted_on": n,
        "slope": slope,
        "intercept_pm": intercept,
        "mean_absolute_residual_pm": sum(abs(r[1]) for r in residuals) / n,
        "max_absolute_residual_pm": abs(worst[1]),
        "worst_element": worst[0],
        "residuals": tuple((symbol, value) for symbol, value in
                           sorted(residuals, key=lambda r: -abs(r[1]))[:8]),
        "caveat": (
            "The residuals are in-sample: the line is scored on the same "
            "elements it was fitted to, so they are a floor on the error "
            "anywhere else, not an estimate of it.  Values produced by this "
            "line are labelled estimated and are never written back into the "
            "register."),
    }


def estimated_covalent_radii() -> Dict[str, object]:
    """Covalent radii for elements that have an atomic radius but no measured one."""
    model = covalent_radius_model()
    elements = el.load_element_register()
    if not model["fitted"]:
        return {"model": model, "estimates": (), "estimate_count": 0}
    slope = model["slope"]
    intercept = model["intercept_pm"]
    estimates: List[Tuple[str, Fraction]] = []
    for element in elements:
        if element.covalent_radius_pm is not None:
            continue
        if element.atomic_radius_pm is None:
            continue
        estimates.append((element.symbol,
                          slope * Fraction(element.atomic_radius_pm)
                          + intercept))
    measured = sum(1 for e in elements if e.covalent_radius_pm is not None)
    return {
        "model": model,
        "estimates": tuple(estimates),
        "estimate_count": len(estimates),
        "measured_count": measured,
        "coverage_before": Fraction(measured, len(elements)),
        "coverage_after": Fraction(measured + len(estimates), len(elements)),
        "still_absent": tuple(sorted(
            e.symbol for e in elements
            if e.covalent_radius_pm is None and e.atomic_radius_pm is None)),
    }


# ===========================================================================
# 4.  CROSS-CHECK -- TWO REGISTERS, ONE NAME, TWO QUANTITIES
# ===========================================================================

def diatomic_cross_check() -> Dict[str, object]:
    """Compare the element register's bond energy with the diatomic ``D0``."""
    elements = {e.symbol: e for e in el.load_element_register()}
    rows: List[Dict[str, object]] = []
    for diatomic in el.load_diatomic_register():
        if not diatomic.homonuclear or diatomic.charge != 0:
            continue
        if diatomic.d0_kJ_per_mol is None:
            continue
        element = elements.get(diatomic.element_a)
        if element is None or element.homonuclear_bde_kJ_per_mol is None:
            continue
        single = Fraction(element.homonuclear_bde_kJ_per_mol)
        rows.append({
            "element": diatomic.element_a,
            "single_bond_kJ_per_mol": single,
            "diatomic_d0_kJ_per_mol": Fraction(diatomic.d0_kJ_per_mol),
            "difference": Fraction(diatomic.d0_kJ_per_mol) - single,
        })
    rows.sort(key=lambda row: -abs(row["difference"]))
    close = tuple(row["element"] for row in rows
                  if abs(row["difference"]) <= 20)
    far = tuple(row["element"] for row in rows
                if abs(row["difference"]) > 20)
    # The elements that disagree are read off the comparison rather than
    # listed here, so the sentence cannot drift away from the data.  On the
    # register as it stands nitrogen is among the *agreeing* elements, which
    # is itself the finding: the element register's homonuclear field is a
    # single-bond enthalpy for carbon, silicon, phosphorus and sulfur, but
    # for nitrogen it already holds the triple-bond value.
    named = ", ".join(f"{symbol}2" for symbol in far) if far else "none"
    return {
        "compared": len(rows),
        "rows": tuple(rows),
        "agree_within_20": close,
        "agree_within_20_count": len(close),
        "largest_difference": rows[0] if rows else None,
        "new_elements_from_diatomics": tuple(sorted(
            {d.element_a for d in el.load_diatomic_register()
             if d.homonuclear and d.charge == 0
             and d.d0_kJ_per_mol is not None}
            - {symbol for symbol, e in elements.items()
               if e.homonuclear_bde_kJ_per_mol is not None})),
        "disagree_beyond_20": far,
        "disagree_beyond_20_count": len(far),
        "statement": (
            f"These are not the same quantity.  The element register's field "
            f"is a bond dissociation enthalpy for the homonuclear single "
            f"bond; the diatomic register's D0 is the dissociation energy of "
            f"the diatomic molecule.  Where the molecule is held together by "
            f"one single bond the two agree, and {len(close)} of "
            f"{len(rows)} do, within 20 kJ/mol.  Where it is not -- "
            f"{named} -- they differ by up to "
            f"{abs(rows[0]['difference']) if rows else 0} kJ/mol.  Nitrogen "
            f"is worth naming among the agreements rather than the "
            f"disagreements: the element register already holds the "
            f"triple-bond figure for it, so the two registers coincide there "
            f"for a reason that does not generalise.  The two are therefore "
            f"reported side by side and never merged, and the diatomic "
            f"register adds no element the element register does not already "
            f"have."),
    }


# ===========================================================================
# 5.  EVERYTHING ABOUT ONE ELEMENT, WITH PROVENANCE
# ===========================================================================

def attributes_of(symbol: str, include_estimates: bool = True
                  ) -> Tuple[Attribute, ...]:
    """Every attribute of one element, each labelled with where it came from."""
    element = el.element_by_symbol(symbol)
    out: List[Attribute] = []
    units = {
        "atomic_weight_u": "u", "electronegativity_pauling": "1",
        "atomic_radius_pm": "pm", "covalent_radius_pm": "pm",
        "valence_electrons": "1", "homonuclear_bde_kJ_per_mol": "kJ/mol",
        "ionization_energy_eV": "eV", "electron_affinity_eV": "eV",
        "melting_point_K": "K", "boiling_point_K": "K",
        "density_g_per_cm3": "g/cm^3", "group_block_code": "1",
        "standard_state_code": "1", "year_discovered": "1",
    }
    for field, unit in sorted(units.items()):
        value = getattr(element, field, None)
        if value is None:
            continue
        out.append(Attribute(name=field, value=Fraction(value), unit=unit,
                             provenance="measured", basis="element register"))
    for name in sorted(DERIVED_ATTRIBUTES):
        attribute = derived_attribute(element, name)
        if attribute.value is not None:
            out.append(attribute)
    if include_estimates and element.covalent_radius_pm is None \
            and element.atomic_radius_pm is not None:
        model = covalent_radius_model()
        if model["fitted"]:
            value = (model["slope"] * Fraction(element.atomic_radius_pm)
                     + model["intercept_pm"])
            out.append(Attribute(
                name="covalent_radius_pm", value=value, unit="pm",
                provenance="estimated",
                basis=f"least-squares line on atomic radius, fitted on "
                      f"{model['fitted_on']} elements, mean absolute "
                      f"residual {model['mean_absolute_residual_pm']} pm"))
    return tuple(out)


def element_coverage_report() -> Dict[str, object]:
    """Everything this module knows, recomputed on call."""
    coverage = coverage_table()
    derived = derived_coverage()
    estimates = estimated_covalent_radii()
    cross = diatomic_cross_check()
    return {
        "coverage": coverage,
        "derived": derived,
        "estimates": estimates,
        "cross_check": cross,
        "method": (
            "Coverage is widened three ways and none of them invents a "
            "measurement.  Attributes that are exact functions of fields "
            "already present are derived and labelled derived.  Covalent "
            "radius is extended by a rational least-squares line on atomic "
            "radius, labelled estimated, with the fit's residuals reported "
            "beside it.  And where two registers hold a similarly named "
            "quantity they are compared rather than merged."),
        "limits": (
            "No value here is written back into the element register, so a "
            "caller that wants only measurements still gets only "
            "measurements.  The covalent-radius residuals are in-sample and "
            "are a floor on the error, not an estimate of it.  The elements "
            "with neither a measured covalent radius nor an atomic radius "
            "get nothing, and are listed rather than filled."),
    }
