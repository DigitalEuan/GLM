"""``glm_universal.reasoning.kappa_anchor`` -- the work-energy anchor
``kappa = 190 kJ/mol``: what it fixes, what it cannot, where it comes from in
the GLM's own data, and how far it could be refined (Phase 177).

*Created 21 October 2026.*

The owner's document ``source_material/Lorentz boosts.pdf`` sets ``kappa``
beside ``c`` as a calibration dial: ``tau = h N_A / kappa`` is the tick,
``(24 + T)`` ticks a cell, ``l_cell = c T_cell`` its length.  The archive's
chain and its circularity are already machine-checked
(``RequestProject/GLM/Calibration.lean``; ``tool salvage``).  This module
answers the owner's three questions about the anchor itself, exactly:

* **How it works for calibration.**  ``kappa`` is a unit.  Every
  dimensionful output of the chain is proportional to ``1/kappa``, and every
  dimensionless output -- the refractive-index law ``(24+T)/(24+T0)``, any
  ratio of two cells -- is free of it
  (``GLM.KappaAnchor.cellLength_ratio_kappa_free``).  Setting ``kappa = 1``
  is the substrate's "natural units", exactly as ``c = 1`` is relativity's:
  nothing testable moves.
* **How much more refined it could be.**  The GLM's diatomic register holds
  ``D0(Br2) = 190.2 +/- 0.3 kJ/mol``; ``kappa = 190`` lies inside that
  interval, so the anchor *is* the bromine dissociation energy to its stated
  precision.  A relative error in ``kappa`` is the same relative error in
  every output (``tick_relative_change``).  Three knobs are compared:
  the third significant figure (``190 -> 190.2``: 0.105 %), the register's
  uncertainty (0.16 %), the choice of tabulated quantity (``D0`` against the
  element register's 298 K bond energy ``193``: 1.55 %), and the rounding of
  the tick budget ``24 + 8Q = 27.117...`` to ``27`` (0.43 %).  The digits of
  ``kappa`` are the smallest of the four.
* **What use it has for the GLM.**  As a declared *unit* -- the "units"
  family of ``tool frame``, an operator that rescales every component and
  is identified from one example -- and as a guard: a claim whose truth
  changes with ``kappa`` is a claim about units, never about the substrate.
  It is *not* a predictor: the archive's own Step 3 measured ``r^2 =
  0.0011`` between its dimensionless geometric work and 24 bond energies
  (quoted from the archive README, not re-measured here).

Exactness
---------
``Fraction`` throughout (D7); ``Y`` enters only through its rational bracket.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from .salvage import CSI, HSI, NA, KAPPA_BR, Y_LOWER, Y_UPPER

__all__ = ["E_SI", "LEAN_FILE", "LEAN_THEOREMS", "chain", "br2_register",
           "kappa_report", "kappa_text"]

#: The elementary charge, C (exact, SI 2019).
E_SI = Fraction(1602176634, 10 ** 28)

LEAN_FILE = "RequestProject/GLM/KappaAnchor.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "cellLength_ratio_kappa_free", "ratio_free_of_c", "tick_scale_inv",
    "tick_relative_change", "kappa_within_br2_d0", "kappa_tick_ratio_d0",
    "kappa_tick_ratio_bde", "quantity_choice_dominates",
    "kappa_relative_uncertainty_lt", "tax_rounding_dominates_kappa",
    "kappa_eV_bounds")

#: The archive's Step 3 correlation of geometric work with bond energy,
#: quoted from ``GLM-main/README.md`` (24 bonds), not re-measured here.
ARCHIVE_WORK_BDE_R2 = Fraction(11, 10000)


def chain(kappa_j_per_mol: Fraction, tax: Fraction = Fraction(3)
          ) -> Dict[str, Fraction]:
    """The calibration chain at one anchor, exactly."""
    k = Fraction(kappa_j_per_mol)
    tick = HSI * NA / k
    cell_t = (24 + tax) * tick
    return {"work_energy_J": k / NA, "tick_s": tick, "cell_duration_s": cell_t,
            "cell_length_m": CSI * cell_t, "wavelength_m": CSI * tick,
            "eV_per_particle": k / (E_SI * NA)}


def br2_register() -> Dict[str, object]:
    """``D0(Br2)`` and its uncertainty from the diatomic register, and the
    element register's homonuclear bond energy of bromine, in J/mol."""
    from ..data_objects import elements as E
    d0 = unc = None
    for d in E.load_diatomic_register():
        if d.species == "Br2" and d.charge == 0:
            d0 = d.d0_kJ_per_mol * 1000
            unc = (d.uncertainty_kJ_per_mol * 1000
                   if d.uncertainty_kJ_per_mol is not None else None)
    bde = E.element_by_symbol("Br").homonuclear_bde_kJ_per_mol
    near: List[Tuple[Fraction, str]] = sorted(
        (abs(d.d0_kJ_per_mol * 1000 - KAPPA_BR), d.species)
        for d in E.load_diatomic_register() if d.charge == 0)
    return {"d0": d0, "d0_unc": unc,
            "element_bde": None if bde is None else bde * 1000,
            "nearest_species": near[0][1], "nearest_gap": near[0][0],
            "second_species": near[1][1], "second_gap": near[1][0],
            "species": len(near)}


def _fmt(x: Fraction, digits: int = 6) -> str:
    """A decimal rendering by integer arithmetic (no float), ``digits``
    significant figures, plain between 1e-3 and 1e6, else ``m x 10^e``;
    for prose only."""
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    x = abs(Fraction(x))
    e = 0
    while x >= 10:
        x /= 10
        e += 1
    while x < 1:
        x *= 10
        e -= 1
    m = round(x * 10 ** (digits - 1))
    if m >= 10 ** digits:
        m //= 10
        e += 1
    s = str(m)
    if -3 <= e < 6:
        if e >= 0:
            whole, frac = s[:e + 1].ljust(e + 1, "0"), s[e + 1:]
        else:
            whole, frac = "0", "0" * (-e - 1) + s
        frac = frac.rstrip("0") if len(frac) > 0 and e >= digits - 1 else frac
        return sign + whole + ("." + frac if frac else "")
    return f"{sign}{s[0]}{'.' + s[1:] if len(s) > 1 else ''} x 10^{e}"


def kappa_report(kappa_kj: Optional[Fraction] = None) -> Dict[str, object]:
    """Every figure the study quotes about the anchor, computed."""
    reg = br2_register()
    k0 = KAPPA_BR if kappa_kj is None else Fraction(kappa_kj) * 1000
    base = chain(k0)
    d0, unc, bde = reg["d0"], reg["d0_unc"], reg["element_bde"]
    within = (d0 is not None and unc is not None and abs(KAPPA_BR - d0) <= unc)
    # the four refinement knobs, as relative shifts of every output
    shift_digit = 1 - KAPPA_BR / d0            # 190 -> 190.2
    shift_unc = unc / d0                        # half-width of the interval
    shift_quantity = 1 - KAPPA_BR / bde         # D0 -> 298 K bond energy
    q_lo, q_hi = Y_LOWER + Fraction(1, 8), Y_UPPER + Fraction(1, 8)
    budget_lo, budget_hi = 24 + 8 * q_lo, 24 + 8 * q_hi
    shift_tax = (budget_lo / 27 - 1, budget_hi / 27 - 1)
    # kappa-free dimensionless content: a sweep of anchors and taxes
    anchors = [Fraction(k) for k in (1, 95000, 190000, 190200, 193000, 380000)]
    taxes = [Fraction(t) for t in (3, 8, 16, 24)]
    ratios = {(a, t): chain(a, t)["cell_length_m"] / chain(a, Fraction(3))["cell_length_m"]
              for a in anchors for t in taxes}
    kappa_free = all(r == (24 + t) / 27 for (a, t), r in ratios.items())
    return {
        "kappa_J_per_mol": k0, "chain": base,
        "register": reg, "within_br2_interval": within,
        "shift_digit": shift_digit, "shift_uncertainty": shift_unc,
        "shift_quantity": shift_quantity, "shift_tax": shift_tax,
        "ordering": sorted(
            [("third significant figure", shift_digit),
             ("register uncertainty", shift_unc),
             ("tick-budget rounding", shift_tax[0]),
             ("which tabulated quantity", shift_quantity)],
            key=lambda kv: kv[1]),
        "ratio_sweep": len(ratios), "kappa_free": kappa_free,
        "archive_work_bde_r2": ARCHIVE_WORK_BDE_R2,
        "lean_file": LEAN_FILE,
    }


def kappa_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool kappa [VALUE in kJ/mol]``: the anchor read as a unit."""
    arg = arg.strip().removesuffix("kJ/mol").strip()
    val: Optional[Fraction] = None
    if arg:
        try:
            val = Fraction(arg)
        except (ValueError, ZeroDivisionError):
            return False, ("refused: give the anchor in kJ/mol, e.g. "
                           "'tool kappa 190.2', or nothing"), {}
        if val <= 0:
            return False, "refused: the anchor must be positive", {}
    r = kappa_report(val)
    c, reg = r["chain"], r["register"]
    k_kj = r["kappa_J_per_mol"] / 1000
    figures = {"kappa_kJ_per_mol": str(k_kj),
               "tick_s": str(c["tick_s"]), "within_br2_interval":
               r["within_br2_interval"], "kappa_free": r["kappa_free"]}
    order = ", ".join(f"{n} {_fmt(100 * s, 3)} %" for n, s in r["ordering"])
    text = (
        f"kappa: at {_fmt(k_kj, 6)} kJ/mol one work unit is "
        f"{_fmt(c['work_energy_J'])} J = {_fmt(c['eV_per_particle'])} eV per "
        f"particle, the tick h N_A/kappa is {_fmt(c['tick_s'])} s, the cell "
        f"(27 ticks) is {_fmt(c['cell_duration_s'])} s and "
        f"{_fmt(c['cell_length_m'])} m, the one-work-unit photon is "
        f"{_fmt(c['wavelength_m'])} m. "
        f"Calibration: kappa is a unit -- over {r['ratio_sweep']} anchor and "
        f"tax pairs every ratio of two cells is (24+T)/27, whatever kappa "
        f"({'held' if r['kappa_free'] else 'FAILED'}; "
        "GLM.KappaAnchor.cellLength_ratio_kappa_free), and c comes back as "
        "put in (GLM.Calibration.substrate_c_is_circular). "
        f"Source: the diatomic register gives D0(Br2) = "
        f"{_fmt(reg['d0'] / 1000, 4)} +/- {_fmt(reg['d0_unc'] / 1000, 1)} "
        f"kJ/mol, and 190 lies "
        f"{'inside' if r['within_br2_interval'] else 'outside'} it "
        f"(nearest of {reg['species']} species: {reg['nearest_species']}; "
        f"next {reg['second_species']}, {_fmt(reg['second_gap'] / 1000, 3)} "
        "kJ/mol away); the element register's bromine bond energy is "
        f"{_fmt(reg['element_bde'] / 1000, 3)} kJ/mol. "
        f"Refinement, as relative shifts of every output: {order} "
        "(GLM.KappaAnchor.tax_rounding_dominates_kappa, "
        "quantity_choice_dominates). Use: a declared unit and a guard -- a "
        "claim that moves with kappa is about units; as a predictor of bond "
        "energies the archive measured r^2 = 0.0011 (quoted, not re-measured)")
    return True, text, figures
