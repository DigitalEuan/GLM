"""``glm_universal.wheels.cent_wheels_study`` -- the question battery of
``studies/CENT_WHEELS_STUDY.md``.

*Created 31 October 2026 (intake of ``source_material/ToDo/cent_compiler_v12``,
directive D22).*  The constants below were written before the rational-power
engine, the absorbed wheels (:mod:`glm_universal.wheels.cent_wheels`) or the
Lean file existed, and before any question was put to an engine (the study's
§0 and §4).  The gold answer of each question comes from the physics the
question states, as the reviewer knows it, never from an engine: a *law* is a
true relation between the magnitudes it names (under the model conventions the
study's §4 declares: numeric factors standing for pi dropped, magnitudes only,
one flux quantum in W28); *not a law* is a formula that is dimensionally wrong,
has a wrong coefficient, confuses two quantities, or holds only in a special
case.

Each question is ``(qid, wheel, equation, gold, source, reason)``:

* ``wheel`` -- the supplied wheel whose domain it is in (``W16`` ... ``W35``);
* ``gold`` -- :data:`LAW` or :data:`NOT_A_LAW`;
* ``source`` -- :data:`CASE` (a supplied case, as supplied or as corrected
  under the study's rule R), :data:`CONTROL` (a supplied ``-N`` negative
  control), :data:`SUPPLIED_FORM` (a supplied axiom or case the study corrects
  or drops, in its supplied text) or :data:`HELD_OUT` (written for this study,
  not in the item).

Exact throughout (directive D7): equations are text; nothing here is a float.
"""
from __future__ import annotations

from typing import Tuple

#: A true relation between the magnitudes it names.
LAW = "law"
#: Dimensionally wrong, a wrong coefficient, two quantities confused, or true
#: only in a special case.
NOT_A_LAW = "not a law"

CASE = "case"
CONTROL = "control"
SUPPLIED_FORM = "supplied form"
HELD_OUT = "held-out"

Question = Tuple[str, str, str, str, str, str]


def _q(qid: str, wheel: str, equation: str, gold: str, source: str,
       reason: str) -> Question:
    return (qid, wheel, equation, gold, source, reason)


# ---------------------------------------------------------------------------
# 4. The battery: derivability questions in the new domains (W16-W35)
# ---------------------------------------------------------------------------

MEASURE_BATTERY: Tuple[Question, ...] = (
    # W16 Magnetic flux and induction
    _q("W16-01", "W16", "magnetic_field = flux / area", LAW, CASE, "flux = B A"),
    _q("W16-02", "W16", "inductance = flux / current", LAW, CASE, "flux linkage = L I"),
    _q("W16-03", "W16", "emf = flux / time", LAW, CASE, "Faraday, magnitude of a flux change over a time"),
    _q("W16-N1", "W16", "flux = magnetic_field / area", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H16-1", "W16", "emf = magnetic_field * area / time", LAW, HELD_OUT, "Faraday with flux = B A"),
    _q("H16-2", "W16", "inductance * current = magnetic_field * area", LAW, HELD_OUT, "both are the flux"),
    _q("H16-3", "W16", "emf = inductance * current / time", LAW, HELD_OUT, "self-induction, L dI/dt in magnitude"),
    _q("H16-F", "W16", "flux = 2 * magnetic_field * area", NOT_A_LAW, HELD_OUT, "wrong coefficient"),
    # W17 Gravitation and orbital mechanics
    _q("W17-01", "W17", "gravitational_constant = surface_gravity * distance^2 / source_mass", LAW, CASE, "g = G M / d^2"),
    _q("W17-02", "W17", "source_mass = surface_gravity * distance^2 / gravitational_constant", LAW, CASE, "g = G M / d^2"),
    _q("W17-03", "W17", "period^2 = distance^3 / (gravitational_constant * source_mass)", LAW, CASE, "Kepler III, 4 pi^2 dropped (declared convention)"),
    _q("W17-N1", "W17", "surface_gravity = distance^2 / (gravitational_constant * source_mass)", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H17-1", "W17", "period^2 = distance / surface_gravity", LAW, HELD_OUT, "circular orbit: T^2 = 4 pi^2 d / g, 4 pi^2 dropped"),
    _q("H17-2", "W17", "gravitational_constant * source_mass = surface_gravity * distance^2", LAW, HELD_OUT, "g = G M / d^2"),
    _q("H17-F", "W17", "period^2 = 2 * distance / surface_gravity", NOT_A_LAW, HELD_OUT, "wrong coefficient (neither 1 nor 4 pi^2)"),
    # W18 Ideal gas law
    _q("W18-01", "W18", "volume = amount * gas_constant * temperature / pressure", LAW, CASE, "p V = n R T"),
    _q("W18-02", "W18", "temperature = pressure * volume / (amount * gas_constant)", LAW, CASE, "p V = n R T"),
    _q("W18-03", "W18", "amount = pressure * volume / (gas_constant * temperature)", LAW, CASE, "p V = n R T"),
    _q("W18-N1", "W18", "pressure = amount * gas_constant * temperature * volume", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H18-1", "W18", "pressure = amount * gas_constant * temperature / volume", LAW, HELD_OUT, "p V = n R T"),
    _q("H18-2", "W18", "gas_constant = pressure * volume / (amount * temperature)", LAW, HELD_OUT, "p V = n R T"),
    _q("H18-F", "W18", "pressure * volume = 2 * amount * gas_constant * temperature", NOT_A_LAW, HELD_OUT, "wrong coefficient"),
    # W19 Electromagnetic waves
    _q("W19-01", "W19", "permittivity * permeability = 1 / speed_of_light^2", LAW, CASE, "c^2 = 1 / (epsilon mu)"),
    _q("W19-02", "W19", "magnetic_field = electric_field / speed_of_light", LAW, CASE, "E = c B in a plane wave"),
    _q("W19-03", "W19", "permittivity = 1 / (permeability * speed_of_light^2)", LAW, CASE, "c^2 = 1 / (epsilon mu)"),
    _q("W19-N1", "W19", "speed_of_light = permittivity * permeability", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H19-1", "W19", "electric_field^2 = magnetic_field^2 / (permittivity * permeability)", LAW, HELD_OUT, "E = c B with c^2 = 1 / (epsilon mu)"),
    _q("H19-2", "W19", "electric_field = magnetic_field / (permittivity * permeability)^(1/2)", LAW, HELD_OUT, "E = c B with c = (epsilon mu)^(-1/2)"),
    _q("H19-F", "W19", "electric_field = magnetic_field * speed_of_light^2", NOT_A_LAW, HELD_OUT, "dimensionally wrong"),
    # W20 Elasticity
    _q("W20-01", "W20", "youngs_modulus = stress / strain", LAW, CASE, "Hooke"),
    _q("W20-02", "W20", "strain = stress / youngs_modulus", LAW, CASE, "Hooke"),
    _q("W20-03", "W20", "radius_curvature = youngs_modulus * area_moment_inertia / bending_moment", LAW, CASE, "M = E I / R"),
    _q("W20-N1", "W20", "stress = youngs_modulus / strain", NOT_A_LAW, CONTROL, "inverts Hooke"),
    _q("H20-1", "W20", "bending_moment = flexural_rigidity / radius_curvature", LAW, HELD_OUT, "M = E I / R with D = E I"),
    _q("H20-2", "W20", "flexural_rigidity = stress * area_moment_inertia / strain", LAW, HELD_OUT, "D = E I with E = stress / strain"),
    _q("H20-F", "W20", "stress = youngs_modulus", NOT_A_LAW, HELD_OUT, "the strain is dropped (same dimension, not equal)"),
    # W21 Fracture mechanics
    _q("W21-01", "W21", "surface_energy = fracture_toughness^2 * crack_length / (2 * youngs_modulus)", LAW, CASE, "Griffith, pi dropped (declared convention)"),
    _q("W21-02", "W21", "crack_length = (stress_intensity_factor / (dimensionless_factor * stress))^2", LAW, CASE, "K = Y sigma a^(1/2)"),
    _q("W21-03", "W21", "stress = stress_intensity_factor / (dimensionless_factor * crack_length^(1/2))", LAW, CASE, "K = Y sigma a^(1/2)"),
    _q("W21-N1", "W21", "fracture_toughness = stress / crack_length", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("F21-ax1", "W21", "fracture_toughness = (2 * youngs_modulus * surface_energy / (314159265 * crack_length))^(1/2)", NOT_A_LAW, SUPPLIED_FORM, "314159265 is not pi (pi is irrational; the literal is pi times 10^8)"),
    _q("H21-1", "W21", "youngs_modulus = fracture_toughness^2 * crack_length / (2 * surface_energy)", LAW, HELD_OUT, "Griffith, pi dropped"),
    _q("H21-2", "W21", "stress_intensity_factor^2 = dimensionless_factor^2 * stress^2 * crack_length", LAW, HELD_OUT, "K = Y sigma a^(1/2), squared"),
    _q("H21-F", "W21", "fracture_toughness = youngs_modulus", NOT_A_LAW, HELD_OUT, "two quantities of one dimension confused"),
    # W22 Chemical kinetics
    _q("W22-01", "W22", "rate_constant = reaction_rate / concentration", LAW, CASE, "first-order rate law"),
    _q("W22-02", "W22", "concentration = reaction_rate / rate_constant", LAW, CASE, "first-order rate law"),
    _q("W22-03", "W22", "diffusion_coefficient = diffusion_flux / concentration_gradient", LAW, CASE, "Fick's first law, magnitude"),
    _q("W22-N1", "W22", "reaction_rate = rate_constant / concentration", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("F22-ax2", "W22", "rate_constant = pre_exponential_factor * concentration / rate_constant", NOT_A_LAW, SUPPLIED_FORM, "self-referential; Arrhenius is k = A exp(-Ea / R T)"),
    _q("H22-F", "W22", "reaction_rate = rate_constant * concentration^2", NOT_A_LAW, HELD_OUT, "second order with a first-order rate constant: dimensionally wrong"),
    # W23 Electrochemistry
    _q("W23-01", "W23", "molar_mass = mass * faraday_constant / charge", LAW, CASE, "Faraday's law of electrolysis (valence 1)"),
    _q("W23-02", "W23", "charge = mass * faraday_constant / molar_mass", LAW, CASE, "Faraday's law of electrolysis (valence 1)"),
    _q("W23-03", "W23", "current = charge / time", LAW, CASE, "Q = I t"),
    _q("W23-N1", "W23", "mass = charge / faraday_constant", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H23-1", "W23", "mass = current * time * molar_mass / faraday_constant", LAW, HELD_OUT, "Faraday's law with Q = I t"),
    _q("H23-2", "W23", "time = mass * faraday_constant / (current * molar_mass)", LAW, HELD_OUT, "Faraday's law with Q = I t"),
    _q("H23-F", "W23", "mass = 2 * charge * molar_mass / faraday_constant", NOT_A_LAW, HELD_OUT, "coefficient 1 / z is never 2"),
    # W24 Semiconductor device physics
    _q("W24-01", "W24", "mobility = diffusion_constant / thermal_voltage", LAW, CASE, "Einstein relation D = mu V_T"),
    _q("W24-02", "W24", "thermal_voltage = diffusion_constant / mobility", LAW, CASE, "Einstein relation"),
    _q("W24-03", "W24", "debye_length = (permittivity * thermal_voltage / (2 * carrier_concentration))^(1/2)", NOT_A_LAW, CASE, "the elementary charge is missing: dimensionally wrong"),
    _q("W24-N1", "W24", "current = saturation_current / voltage", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H24-F", "W24", "diffusion_constant = mobility / thermal_voltage", NOT_A_LAW, HELD_OUT, "inverts the Einstein relation"),
    # W25 Plasma physics (cyclotron and Alfven corrected under rule R)
    _q("W25-01", "W25", "magnetic_field = cyclotron_frequency * mass / charge", LAW, CASE, "omega_c = q B / m (corrected: charge added)"),
    _q("W25-02", "W25", "mass = charge * magnetic_field / cyclotron_frequency", LAW, CASE, "omega_c = q B / m (corrected: charge added)"),
    _q("W25-03", "W25", "mass_density = magnetic_field^2 / (permeability * alfven_velocity^2)", LAW, CASE, "v_A = B / (mu0 rho)^(1/2) (corrected: permeability added)"),
    _q("W25-N1", "W25", "cyclotron_frequency = mass / magnetic_field", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("F25-01", "W25", "magnetic_field = cyclotron_frequency * mass", NOT_A_LAW, SUPPLIED_FORM, "the charge is missing"),
    _q("F25-02", "W25", "mass = magnetic_field / cyclotron_frequency", NOT_A_LAW, SUPPLIED_FORM, "the charge is missing"),
    _q("F25-03", "W25", "mass_density = (magnetic_field / alfven_velocity)^2", NOT_A_LAW, SUPPLIED_FORM, "the permeability is missing"),
    _q("F25-ax1", "W25", "cyclotron_frequency = magnetic_field / mass", NOT_A_LAW, SUPPLIED_FORM, "the charge is missing"),
    _q("F25-ax2", "W25", "alfven_velocity = magnetic_field / mass_density^(1/2)", NOT_A_LAW, SUPPLIED_FORM, "the permeability is missing"),
    _q("H25-1", "W25", "charge = cyclotron_frequency * mass / magnetic_field", LAW, HELD_OUT, "omega_c = q B / m"),
    _q("H25-2", "W25", "alfven_velocity^2 = magnetic_field^2 / (permeability * mass_density)", LAW, HELD_OUT, "v_A^2 = B^2 / (mu0 rho)"),
    _q("H25-F", "W25", "cyclotron_frequency = charge * magnetic_field * mass", NOT_A_LAW, HELD_OUT, "dimensionally wrong"),
    # W28 Josephson effects
    _q("W28-01", "W28", "magnetic_flux = josephson_voltage * time", LAW, CASE, "AC Josephson: V = Phi_0 f, one quantum per period"),
    _q("W28-02", "W28", "time = magnetic_flux / josephson_voltage", LAW, CASE, "AC Josephson"),
    _q("W28-03", "W28", "magnetic_flux = flux_quantum", LAW, CASE, "one flux quantum (declared convention, n = 1)"),
    _q("W28-N1", "W28", "josephson_voltage = time / magnetic_flux", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H28-1", "W28", "josephson_voltage = flux_quantum / time", LAW, HELD_OUT, "AC Josephson: V = Phi_0 / period"),
    _q("H28-2", "W28", "time = flux_quantum / josephson_voltage", LAW, HELD_OUT, "AC Josephson"),
    _q("H28-F", "W28", "josephson_voltage = flux_quantum * time", NOT_A_LAW, HELD_OUT, "dimensionally wrong"),
    # W29 Spintronics (spin diffusion length corrected under rule R)
    _q("W29-01", "W29", "gyromagnetic_ratio = larmor_frequency / magnetic_field", LAW, CASE, "omega_L = gamma B"),
    _q("W29-02", "W29", "magnetic_field = larmor_frequency / gyromagnetic_ratio", LAW, CASE, "omega_L = gamma B"),
    _q("W29-03", "W29", "time = spin_diffusion_length^2 / diffusion_coefficient", LAW, CASE, "lambda = (D tau)^(1/2) (corrected: the root binds D tau)"),
    _q("W29-N1", "W29", "larmor_frequency = magnetic_field / gyromagnetic_ratio", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("F29-03", "W29", "time = (spin_diffusion_length / diffusion_coefficient)^2", NOT_A_LAW, SUPPLIED_FORM, "dimensionally wrong"),
    _q("F29-ax2", "W29", "spin_diffusion_length = diffusion_coefficient * time^(1/2)", NOT_A_LAW, SUPPLIED_FORM, "dimensionally wrong: the root must bind D tau"),
    _q("H29-1", "W29", "diffusion_coefficient = spin_diffusion_length^2 / time", LAW, HELD_OUT, "lambda^2 = D tau"),
    _q("H29-F", "W29", "spin_diffusion_length = diffusion_coefficient * time", NOT_A_LAW, HELD_OUT, "dimensionally wrong"),
    # W32 Capillarity
    _q("W32-01", "W32", "surface_tension = pressure * capillary_radius", LAW, CASE, "Laplace pressure of a cylindrical surface"),
    _q("W32-02", "W32", "capillary_radius = surface_tension / pressure", LAW, CASE, "Laplace pressure"),
    _q("W32-03", "W32", "viscosity = surface_tension * wetting_coefficient / (capillary_height * capillary_radius)", NOT_A_LAW, CASE, "dimensionally wrong (Jurin's law has rho g, not a viscosity)"),
    _q("W32-N1", "W32", "pressure = capillary_radius / surface_tension", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("F32-ax2", "W32", "capillary_height = surface_tension * wetting_coefficient / (viscosity * capillary_radius)", NOT_A_LAW, SUPPLIED_FORM, "dimensionally wrong"),
    _q("H32-F", "W32", "pressure = surface_tension * capillary_radius", NOT_A_LAW, HELD_OUT, "dimensionally wrong"),
    # W33 Heat and mass transfer
    _q("W33-01", "W33", "thermal_conductivity = heat_transfer_coefficient * characteristic_length", NOT_A_LAW, CASE, "true only when the Nusselt number is 1"),
    _q("W33-02", "W33", "characteristic_length = thermal_conductivity / heat_transfer_coefficient", NOT_A_LAW, CASE, "true only when the Nusselt number is 1"),
    _q("W33-03", "W33", "heat_transfer_coefficient = nusselt_number * thermal_conductivity / characteristic_length", LAW, CASE, "definition of the Nusselt number"),
    _q("W33-N1", "W33", "nusselt_number = thermal_conductivity / heat_transfer_coefficient", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("F33-ax1", "W33", "heat_transfer_coefficient = thermal_conductivity / characteristic_length", NOT_A_LAW, SUPPLIED_FORM, "true only when the Nusselt number is 1"),
    _q("H33-1", "W33", "characteristic_length = nusselt_number * thermal_conductivity / heat_transfer_coefficient", LAW, HELD_OUT, "definition of the Nusselt number"),
    _q("H33-F", "W33", "nusselt_number = 1", NOT_A_LAW, HELD_OUT, "the Nusselt number is not 1 in general"),
    # W34 Haemodynamics (resistance table entry corrected under rule R)
    _q("W34-01", "W34", "viscosity = vascular_resistance * pipe_radius^4 / length", LAW, CASE, "Poiseuille resistance, 8 / pi dropped (declared convention)"),
    _q("W34-02", "W34", "pipe_radius = (viscosity * length / vascular_resistance)^(1/4)", LAW, CASE, "Poiseuille resistance, solved for r"),
    _q("W34-03", "W34", "pressure = volume_flow_rate * vascular_resistance", LAW, CASE, "hydraulic Ohm's law"),
    _q("W34-N1", "W34", "vascular_resistance = pipe_radius^4 / (viscosity * length)", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("H34-1", "W34", "pressure = viscosity * length * volume_flow_rate / pipe_radius^4", LAW, HELD_OUT, "Hagen-Poiseuille, 8 / pi dropped"),
    _q("H34-2", "W34", "volume_flow_rate = pressure * pipe_radius^4 / (viscosity * length)", LAW, HELD_OUT, "Hagen-Poiseuille, 8 / pi dropped"),
    _q("H34-F", "W34", "vascular_resistance = viscosity * length / pipe_radius^3", NOT_A_LAW, HELD_OUT, "dimensionally wrong"),
    # W35 Electrophysiology
    _q("W35-01", "W35", "valence = temperature / membrane_voltage", NOT_A_LAW, CASE, "k_B / e and the logarithm are missing"),
    _q("W35-02", "W35", "temperature = membrane_voltage * valence", NOT_A_LAW, CASE, "k_B / e and the logarithm are missing"),
    _q("W35-03", "W35", "ion_concentration = ion_flux / diffusion_coefficient", NOT_A_LAW, CASE, "dimensionally wrong (a gradient or a thickness is missing)"),
    _q("W35-N1", "W35", "membrane_voltage = valence / temperature", NOT_A_LAW, CONTROL, "dimensionally wrong"),
    _q("F35-ax1", "W35", "membrane_voltage = temperature / valence", NOT_A_LAW, SUPPLIED_FORM, "Nernst needs k_B / e and a logarithm"),
    _q("F35-ax2", "W35", "ion_flux = diffusion_coefficient * ion_concentration", NOT_A_LAW, SUPPLIED_FORM, "dimensionally wrong (Fick needs a gradient)"),
)

#: The pre-registered bars of marks M1-M3 (the study's §3).
BAR_WRONG_MAX = 0
BAR_LAWS_LICENSED_MIN = 56
BAR_BASELINE_LAWS_MAX = 4


# ===========================================================================
# The measurement (added 31 October 2026, after the battery above was fixed)
# ===========================================================================
#
# *Last altered 31 October 2026 (the measurement of the study's §8 added below
# the battery, after the engine and the absorbed wheels existed: the readers
# of the supplied item, one function per mark, the Lean source the round
# wrote, and :func:`cent_wheels_report`).*  The constants above were not
# changed by it.

import json  # noqa: E402
from fractions import Fraction  # noqa: E402
from typing import Dict, List, Mapping, Optional, Sequence  # noqa: E402

from . import cent_wheels as CW  # noqa: E402

#: The supplied item and its wheels folder, as names
#: :func:`glm_universal.constants.source_material_item` resolves.
ITEM = "cent_compiler_v12"
WHEELS_DIR = "cent_compiler_v12/wheels"
#: The Lean file of the round, as :func:`glm_universal.constants.lean_file`
#: resolves it.
LEAN_FILE = "Wheels/CentWheels.lean"
#: The item tests of mark I1, as the intake record names them.
ITEM_TESTS: Tuple[str, ...] = ("item:cent test", "item:tests/show_work.py")
#: The new modules of the round (mark I4's subjects).
NEW_MODULES: Tuple[str, ...] = (
    "wheels/cent_wheels.py", "wheels/cent_wheels_study.py", "wheels/lean_cent_data.py",
)


# ---------------------------------------------------------------------------
# The supplied wheels (read from the item, for the marks only)
# ---------------------------------------------------------------------------

def supplied_wheels() -> Dict[str, dict]:
    """``{id: wheel}`` of the 31 supplied JSON wheels, read from the item
    (``{}`` when the item is not in this checkout)."""
    from ..constants import source_material_item
    folder = source_material_item(WHEELS_DIR)
    out: Dict[str, dict] = {}
    if not folder.is_dir():
        return out
    for path in folder.glob("W*.json"):
        w = json.loads(path.read_text(encoding="utf-8"))
        out[w["id"]] = w
    return dict(sorted(out.items(), key=lambda kv: int(kv[0][1:])))


def supplied_table(wheel: Mapping) -> Dict[str, Tuple[Fraction, ...]]:
    """A supplied wheel's dimension table, axes in the order of ``CW.AXES``."""
    out: Dict[str, Tuple[Fraction, ...]] = {}
    for q, entry in wheel["dimensions"].items():
        axes = list(entry["axes"])
        out[q] = tuple(Fraction(entry["exponents"][axes.index(a)]) for a in CW.AXES)
    return out


def _fmt(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _vec(v: Sequence[Fraction]) -> str:
    return "(" + ", ".join(_fmt(Fraction(x)) for x in v) + ")"


# ---------------------------------------------------------------------------
# D1, A1, S3 -- the dimension verdict of every supplied axiom
# ---------------------------------------------------------------------------

def mark_d1() -> Dict[str, object]:
    """Every supplied axiom's eight-axis residual on its own table: the SI7
    verdict, the angle residual, and the axioms that fail."""
    rows = []
    for wid, w in supplied_wheels().items():
        table = supplied_table(w)
        for i, a in enumerate(w["axioms"]):
            r = CW.residual(a, table)
            rows.append({
                "wheel": wid, "axiom": i + 1, "text": a,
                "residual": None if r is None else _vec(r),
                "si7": None if r is None else not any(r[:CW.SI7_AXES]),
                "angle": None if r is None else _fmt(r[CW.SI7_AXES]),
            })
    fails = [(r["wheel"], r["axiom"], r["text"], r["residual"]) for r in rows if r["si7"] is False]
    angle_only = [(r["wheel"], r["axiom"], r["text"], r["angle"]) for r in rows
                  if r["si7"] is True and r["angle"] != "0"]
    return {
        "axioms": len(rows),
        "verdicts": sum(r["si7"] is not None for r in rows),
        "unknown": sum(r["si7"] is None for r in rows),
        "balanced_si7": sum(r["si7"] is True for r in rows),
        "failing_si7": fails,
        "angle_only": angle_only,
        "met": bool(rows) and all(r["si7"] is not None for r in rows),
    }


def mark_s3() -> Dict[str, object]:
    """Each axiom failing at SI7 and what rule R did with it; and the
    absorbed axioms' SI7 verdicts (0 failing is the bar)."""
    fates = []
    corrected_axioms = {(c.wheel, c.supplied) for c in CW.CORRECTIONS if c.what == "axiom"}
    table_fixed = {c.wheel for c in CW.CORRECTIONS if c.what == "table"}
    dropped = {(d.wheel, d.supplied) for d in CW.DROPPED}
    for wid, _, text, res in mark_d1()["failing_si7"]:
        if (wid, text) in dropped:
            fate = "dropped"
        elif (wid, text) in corrected_axioms:
            fate = "corrected"
        elif wid in table_fixed and any(text == a for w in CW.CENT_WHEELS if w.id == wid
                                        for a in w.axioms):
            fate = "table corrected"
        else:
            fate = "UNSETTLED"
        fates.append((wid, text, res, fate))
    absorbed_fail = [(w.id, a) for w in CW.CENT_WHEELS for a in w.axioms
                     if CW.balanced_si7(a, CW.CENT_TABLES[w.id]) is not True]
    return {"failing": fates, "unsettled": [f for f in fates if f[3] == "UNSETTLED"],
            "absorbed_failing_si7": absorbed_fail,
            "met": not absorbed_fail and all(f[3] != "UNSETTLED" for f in fates)}


def mark_a1() -> Dict[str, object]:
    """The axioms whose only residual is on the angle axis."""
    rows = mark_d1()["angle_only"]
    return {"angle_only": rows, "count": len(rows)}


# ---------------------------------------------------------------------------
# D2 -- the tables against the repository registry
# ---------------------------------------------------------------------------

def mark_d2() -> Dict[str, object]:
    from ..engineering.wheels import REFERENCE_DIMENSIONS
    shared = disagree = 0
    rows = []
    seen: Dict[str, set] = {}
    for wid, w in supplied_wheels().items():
        for q, v in supplied_table(w).items():
            seen.setdefault(q, set()).add(v)
            if q in REFERENCE_DIMENSIONS:
                shared += 1
                if tuple(REFERENCE_DIMENSIONS[q]) != v:
                    disagree += 1
                    rows.append((wid, q, _vec(v), _vec(REFERENCE_DIMENSIONS[q])))
    return {"shared_entries": shared, "disagreements": rows,
            "names_differing_across_tables": sorted(q for q, s in seen.items() if len(s) > 1),
            "met": shared > 0 and not rows}


# ---------------------------------------------------------------------------
# E1, E2 -- the engine and what is new in W1-W15
# ---------------------------------------------------------------------------

def mark_e1() -> Dict[str, object]:
    """The rational-power engine against ``engineering.wheels`` on every
    supplied axiom and case the integer engine reads."""
    from ..engineering import wheels as EW
    read = unread = 0
    disagreements: List[Tuple[str, str]] = []
    for wid, w in supplied_wheels().items():
        axioms = w["axioms"]
        for text in list(axioms) + [c["equation"] for c in w["cases"]]:
            try:
                iv = EW.relation_vector(text)
            except ValueError:
                unread += 1
                continue
            read += 1
            if iv != CW.relation_vector_q(text):
                disagreements.append((wid, "vector: " + text))
        for c in w["cases"]:
            try:
                iv = EW.is_derivable(c["equation"], axioms)
            except ValueError:
                continue
            if iv != CW.is_derivable_q(c["equation"], axioms):
                disagreements.append((wid, "verdict: " + c["id"]))
    return {"read_by_integer_engine": read, "unread_by_integer_engine": unread,
            "disagreements": disagreements, "met": read > 0 and not disagreements}


def _case_key(c) -> Tuple:
    if isinstance(c, Mapping):
        return (c["id"], c["equation"], c["expected_dimensional"], c["expected_derivable"],
                c["physical_status"], c.get("expected_dimensional_explicit"), c.get("note") or "")
    return (c.id, c.equation, c.expected_dimensional, c.expected_derivable, c.physical_status,
            c.expected_dimensional_explicit, c.note or "")


def mark_e2() -> Dict[str, object]:
    """W1-W3, W5, W7-W10 against ``engineering/wheels.py``; W4 and W6 against
    it plus the two additions; W11-W15 axioms (as relations) against
    ``wheels/w11``-``w15``."""
    from ..engineering.wheels import wheel_named
    from . import DOMAIN_WHEELS
    sup = supplied_wheels()
    problems: List[str] = []
    differences: List[Dict[str, object]] = []
    for i in range(1, 11):
        wid = f"W{i}"
        if wid not in sup:
            problems.append(f"{wid} not supplied")
            continue
        w, base = sup[wid], wheel_named(wid)
        axioms, cases = tuple(w["axioms"]), [_case_key(c) for c in w["cases"]]
        if wid in CW.ENGINEERING_ADDITIONS:
            add_axiom, add_case = CW.ENGINEERING_ADDITIONS[wid]
            want_axioms = base.axioms + (add_axiom,)
            want_cases = [_case_key(add_case) if c.id == add_case.id else _case_key(c)
                          for c in base.cases]
            if add_case.id not in {c.id for c in base.cases}:
                want_cases.insert(len(want_cases) - 1, _case_key(add_case))
        else:
            want_axioms, want_cases = base.axioms, [_case_key(c) for c in base.cases]
        if axioms != want_axioms:
            problems.append(f"{wid} axioms differ")
        if sorted(cases) != sorted(want_cases):
            only_sup = sorted(c[0] for c in set(cases) - set(want_cases))
            only_rep = sorted(c[0] for c in set(want_cases) - set(cases))
            problems.append(f"{wid} cases differ")
            differences.append({"wheel": wid, "only_supplied": only_sup,
                                "only_repository": only_rep})
    for base in DOMAIN_WHEELS:
        w = sup.get(base.id)
        if w is None:
            problems.append(f"{base.id} not supplied")
            continue
        if sorted(map(_rel_key, w["axioms"])) != sorted(map(_rel_key, base.axioms)):
            problems.append(f"{base.id} axioms differ as relations")
        if [_case_key(c) for c in w["cases"]] != [_case_key(c) for c in CW.DOMAIN_CASES[base.id]]:
            problems.append(f"{base.id} cases differ from the absorbed DOMAIN_CASES")
    textual = [(b.id, a) for b in DOMAIN_WHEELS for a in b.axioms
               if b.id in sup and a not in sup[b.id]["axioms"]]
    return {"problems": problems, "case_differences": differences,
            "textual_differences_w11_w15": textual, "met": not problems}


def _rel_key(text: str) -> Tuple:
    return tuple(sorted(CW.relation_vector_q(text).items()))


# ---------------------------------------------------------------------------
# S1, S2, S4, S5 -- the supplied flags, the controls, W22-03, hidden numbers
# ---------------------------------------------------------------------------

def mark_s1() -> Dict[str, object]:
    """Every supplied case's ``expected_derivable`` against span membership
    over its supplied axioms; and over the absorbed wheels, the settled
    flags against the absorbed axioms."""
    rows = []
    for wid, w in supplied_wheels().items():
        for c in w["cases"]:
            got = CW.is_derivable_q(c["equation"], w["axioms"])
            rows.append((wid, c["id"], c["expected_derivable"], got))
    disagree = [(cid, exp, got) for _, cid, exp, got in rows if exp != got]
    absorbed_disagree = [(c.id, c.expected_derivable) for w in CW.CENT_WHEELS for c in w.cases
                         if CW.is_derivable_q(c.equation, w.axioms) != c.expected_derivable]
    settled = [c.item for c in CW.CORRECTIONS if c.what == "flag" and "derivable" in c.item]
    return {"cases": len(rows), "agree": len(rows) - len(disagree), "disagreements": disagree,
            "absorbed_cases": sum(len(w.cases) for w in CW.CENT_WHEELS),
            "absorbed_disagreements": absorbed_disagree, "settled_flags": settled,
            "met": not absorbed_disagree}


def mark_s1_dimension_flags() -> Dict[str, object]:
    """The supplied cases' ``expected_dimensional`` against the SI7 verdict on
    their own table (reported; ``None`` where the table lacks a quantity)."""
    rows = []
    for wid, w in supplied_wheels().items():
        table = supplied_table(w)
        for c in w["cases"]:
            got = CW.balanced_si7(c["equation"], table)
            if got != c["expected_dimensional"]:
                rows.append((c["id"], c["expected_dimensional"], got))
    return {"disagreements": rows, "count": len(rows)}


def mark_s2() -> Dict[str, object]:
    """Every ``-N`` control refused, over the supplied and the absorbed axioms."""
    sup = supplied_wheels()
    supplied_rows = [(wid, c["id"], CW.is_derivable_q(c["equation"], w["axioms"]))
                     for wid, w in sup.items() for c in w["cases"]
                     if c["physical_status"] == "negative_control"]
    absorbed_rows = [(w.id, c.id, CW.is_derivable_q(c.equation, w.axioms))
                     for w in CW.CENT_WHEELS for c in w.cases if c.physical_status == CW.NEGATIVE]
    licensed = [r for r in supplied_rows + absorbed_rows if r[2]]
    return {"supplied_controls": len(supplied_rows), "absorbed_controls": len(absorbed_rows),
            "licensed": licensed, "met": bool(supplied_rows) and not licensed}


def mark_s4() -> Dict[str, object]:
    """W22-03 over W22's supplied axioms and over the absorbed ones."""
    sup = supplied_wheels().get("W22")
    eq = "diffusion_coefficient = diffusion_flux / concentration_gradient"
    absorbed = CW.cent_wheel("W22").axioms
    return {"case": "W22-03", "equation": eq,
            "supplied_flag": None if sup is None else next(
                c["expected_derivable"] for c in sup["cases"] if c["id"] == "W22-03"),
            "derivable_supplied_axioms": None if sup is None else CW.is_derivable_q(eq, sup["axioms"]),
            "derivable_absorbed_axioms": CW.is_derivable_q(eq, absorbed),
            "functional": CW.separating_functional(eq, absorbed),
            "met": not CW.is_derivable_q(eq, absorbed)}


def hidden_relations(axioms: Sequence[str], table: Mapping[str, Sequence[Fraction]]
                     ) -> List[Dict[str, Fraction]]:
    """A basis of the relations in the span of ``axioms`` that involve only
    SI7-dimensionless quantities and numbers (a hidden ``nusselt_number = 1``
    or ``2 = 1``).  An untabled name counts as dimensioned."""
    rels = [CW.relation_vector_q(a) for a in axioms]
    cols = CW.columns(*rels)

    def dimless(c: str) -> bool:
        return c.startswith("#") or (c in table and not any(Fraction(x) for x in
                                                             list(table[c])[:CW.SI7_AXES]))

    outside = [c for c in cols if not dimless(c)]
    n = len(rels)
    mat = [[rels[i].get(c, Fraction(0)) for i in range(n)] for c in outside]
    red, pivots = CW._rref(mat, n) if mat else ([], [])
    out = []
    for f in (j for j in range(n) if j not in pivots):
        x = [Fraction(0)] * n
        x[f] = Fraction(1)
        for i, c in enumerate(pivots):
            x[c] = -red[i][f]
        combo: Dict[str, Fraction] = {}
        for xi, r in zip(x, rels):
            for k, v in r.items():
                combo[k] = combo.get(k, Fraction(0)) + xi * v
        combo = {k: v for k, v in combo.items() if v}
        if combo:
            out.append(combo)
    return out


def _aliases(axioms: Sequence[str]) -> List[str]:
    out = []
    for a in axioms:
        r = CW.relation_vector_q(a)
        if len(r) == 2 and sorted(r.values()) == [Fraction(-1), Fraction(1)] \
                and not any(k.startswith("#") for k in r):
            out.append(a)
    return out


def mark_s5() -> Dict[str, object]:
    """Hidden dimensionless relations in every supplied and every absorbed
    wheel's span, and the axioms equating two names."""
    sup = supplied_wheels()
    supplied = {wid: hidden_relations(w["axioms"], supplied_table(w)) for wid, w in sup.items()}
    absorbed = {w.id: hidden_relations(w.axioms, CW.CENT_TABLES[w.id]) for w in CW.CENT_WHEELS}
    fmt = lambda rs: [" + ".join(f"{_fmt(v)}*{k}" for k, v in sorted(r.items())) for r in rs]
    return {
        "supplied": {k: fmt(v) for k, v in supplied.items() if v},
        "absorbed": {k: fmt(v) for k, v in absorbed.items() if v},
        "aliases_supplied": {wid: _aliases(w["axioms"]) for wid, w in sup.items()
                             if _aliases(w["axioms"])},
        "met": not any(absorbed.values()),
    }


def mark_absorption() -> Dict[str, object]:
    """The absorption rule over W16-W35: which wheels pass it."""
    sup = supplied_wheels()
    new = [wid for wid in sup if int(wid[1:]) >= 16]
    absorbed = [w.id for w in CW.CENT_WHEELS]
    ok = {}
    for w in CW.CENT_WHEELS:
        t = CW.CENT_TABLES[w.id]
        ok[w.id] = (bool(w.axioms)
                    and all(CW.balanced_si7(a, t) for a in w.axioms)
                    and not hidden_relations(w.axioms, t)
                    and all(CW.is_derivable_q(c.equation, w.axioms) == c.expected_derivable
                            for c in w.cases)
                    and not any(CW.is_derivable_q(c.equation, w.axioms)
                                for c in w.cases if c.physical_status == CW.NEGATIVE))
    return {"new_wheels_supplied": new, "absorbed": absorbed,
            "not_absorbed": sorted(set(new) - set(absorbed), key=lambda s: int(s[1:])),
            "rule_holds": ok, "met": all(ok.values()) and set(absorbed) | set(CW.NOT_ABSORBED) == set(new)}


# ---------------------------------------------------------------------------
# M1-M4 -- the battery
# ---------------------------------------------------------------------------

RIGHT = "right"
WRONG = "wrong"
MISS = "miss"


def _licensed_by(equation: str, wheels: Sequence, integer: bool) -> Optional[str]:
    from ..engineering.wheels import is_derivable
    for w in wheels:
        try:
            if (is_derivable(equation, w.axioms) if integer
                    else CW.is_derivable_q(equation, w.axioms)):
                return w.id
        except ValueError:
            continue
    return None


def _outcome(gold: str, licensed: bool) -> str:
    if gold == LAW:
        return RIGHT if licensed else MISS
    return WRONG if licensed else RIGHT


def battery_rows() -> List[Dict[str, object]]:
    """Every question of :data:`MEASURE_BATTERY`, answered by the baseline
    (the fifteen wheels, integer engine) and with the absorbed cent wheels
    (one wheel at a time), and over the naive union of all their axioms."""
    from . import ALL_WHEELS
    union = [a for w in ALL_WHEELS for a in w.axioms] + [a for w in CW.CENT_WHEELS for a in w.axioms]
    rows = []
    for qid, wheel, eq, gold, source, reason in MEASURE_BATTERY:
        base = _licensed_by(eq, ALL_WHEELS, integer=True)
        cent = base or _licensed_by(eq, CW.CENT_WHEELS, integer=False)
        uni = CW.is_derivable_q(eq, union)
        rows.append({"qid": qid, "wheel": wheel, "equation": eq, "gold": gold, "source": source,
                     "baseline": base, "with_cent": cent, "union": uni,
                     "baseline_outcome": _outcome(gold, base is not None),
                     "cent_outcome": _outcome(gold, cent is not None),
                     "union_outcome": _outcome(gold, uni)})
    return rows


def mark_battery() -> Dict[str, object]:
    rows = battery_rows()
    laws = [r for r in rows if r["gold"] == LAW]
    nots = [r for r in rows if r["gold"] == NOT_A_LAW]
    out = {
        "questions": len(rows), "laws": len(laws), "not_laws": len(nots),
        "cent_laws_licensed": sum(r["with_cent"] is not None for r in laws),
        "cent_wrong": [r["qid"] for r in nots if r["with_cent"] is not None],
        "cent_misses": [r["qid"] for r in laws if r["with_cent"] is None],
        "baseline_laws_licensed": [r["qid"] for r in laws if r["baseline"] is not None],
        "baseline_wrong": [r["qid"] for r in nots if r["baseline"] is not None],
        "new_laws": sum(r["with_cent"] is not None and r["baseline"] is None for r in laws),
        "union_laws_licensed": sum(r["union"] for r in laws),
        "union_wrong": [r["qid"] for r in nots if r["union"]],
    }
    out["m1_met"] = len(out["cent_wrong"]) <= BAR_WRONG_MAX
    out["m2_met"] = out["cent_laws_licensed"] >= BAR_LAWS_LICENSED_MIN
    out["m3_met"] = len(out["baseline_laws_licensed"]) <= BAR_BASELINE_LAWS_MAX
    return out


def battery_markdown() -> str:
    """The outcome of every question of §4, as the Markdown table of §8."""
    head = ("| Question | Wheel | Source | Gold | Fifteen wheels | With the cent wheels | Outcome "
            "| Naive union |\n|---|---|---|---|---|---|---|---|")
    lines = [head]
    for r in battery_rows():
        lines.append(f"| {r['qid']} | {r['wheel']} | {r['source']} | {r['gold']} "
                     f"| {r['baseline'] or 'refused'} | {r['with_cent'] or 'refused'} "
                     f"| {r['cent_outcome']} | {r['union_outcome']} |")
    return "\n".join(lines)


def union_conflations() -> List[Dict[str, object]]:
    """For each not-a-law the naive union licenses: the wheels whose axioms
    the union's certificate uses (a conflation is a certificate that crosses
    wheels where a shared name means two things)."""
    from . import ALL_WHEELS
    wheels = list(ALL_WHEELS) + list(CW.CENT_WHEELS)
    axioms = [(w.id, a) for w in wheels for a in w.axioms]
    out = []
    for r in battery_rows():
        if r["gold"] != NOT_A_LAW or not r["union"]:
            continue
        x = CW.certificate(r["equation"], [a for _, a in axioms])
        used = sorted({wid for (wid, _), xi in zip(axioms, x) if xi},
                      key=lambda s: int(s[1:])) if x else []
        out.append({"qid": r["qid"], "equation": r["equation"], "wheels_used": used})
    return out


# ---------------------------------------------------------------------------
# I1, L1 -- the item tests and the Lean file
# ---------------------------------------------------------------------------

def mark_i1() -> Dict[str, object]:
    """The last recorded result of each named item test (from the intake
    ledger; the tests themselves run in ``intake advance ... tested``)."""
    from ..intake import gates, ledger
    rec = ledger.record_by_id(ledger.load(), ITEM)
    latest = gates.latest_results(rec)
    rows = {t: (latest.get(t) or {}).get("result") for t in ITEM_TESTS}
    test_all = (latest.get("item:tests/test_all.py") or {}).get("detail")
    return {"results": rows, "test_all_detail": test_all,
            "met": all(v == "pass" for v in rows.values())}


def mark_l1() -> Dict[str, object]:
    """``Wheels/CentWheels.lean`` read back and checked against the Python
    (:func:`glm_universal.wheels.lean_cent_data.agreement`)."""
    from . import lean_cent_data as L
    from .. import lean_check
    agree = L.agreement()
    audited = lean_check.audited_or_held(LEAN_FILE)
    return {"agreement": agree, "audited_or_held": audited,
            "met": bool(agree.get("ok")) and bool(audited)}


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

def cent_wheels_report(lean: bool = True) -> Dict[str, object]:
    """The figures of ``studies/CENT_WHEELS_STUDY.md`` §8, recomputed.  Every
    mark is a mapping with ``met`` where the study sets a bar."""
    b = mark_battery()
    rep: Dict[str, object] = {
        "d1": mark_d1(), "d2": mark_d2(), "e1": mark_e1(), "e2": mark_e2(),
        "s1": mark_s1(), "s2": mark_s2(), "s3": mark_s3(), "s4": mark_s4(), "s5": mark_s5(),
        "a1": mark_a1(), "absorption": mark_absorption(), "battery": b,
        "union_conflations": union_conflations(),
    }
    if lean:
        rep["l1"] = mark_l1()
    try:
        rep["i1"] = mark_i1()
    except Exception as exc:  # the ledger is not part of every checkout
        rep["i1"] = {"met": False, "error": str(exc)}
    rep["all_met"] = (all(rep[k]["met"] for k in ("d1", "d2", "e1", "e2", "s1", "s2", "s3",
                                                   "s4", "s5", "absorption"))
                      and b["m1_met"] and b["m2_met"] and b["m3_met"]
                      and (not lean or rep["l1"]["met"]))
    return rep


# ---------------------------------------------------------------------------
# The Lean source the round wrote (Wheels/CentWheels.lean)
# ---------------------------------------------------------------------------

def _lean_q(x: Fraction) -> str:
    return _fmt(Fraction(x))


def _lean_row(v: Sequence[Fraction]) -> str:
    return "![" + ", ".join(_lean_q(x) for x in v) + "]"


def _lean_matrix(rows: Sequence[Sequence[Fraction]], indent: str = "    ") -> str:
    return "![" + (",\n" + indent + " ").join(_lean_row(r) for r in rows) + "]"


def lean_name(qid: str) -> str:
    """The Lean theorem name of a question: ``W16-01`` -> ``q_W16_01``."""
    return "q_" + qid.replace("-", "_")


def wheel_questions(wheel) -> List[Tuple[str, str]]:
    """``(qid, equation)`` of an absorbed wheel's cases and its §4 questions
    (a question that is also a case is listed once; the texts agree)."""
    out: Dict[str, str] = {c.id: c.equation for c in wheel.cases}
    for qid, wid, eq, *_ in MEASURE_BATTERY:
        if wid == wheel.id:
            if qid in out and out[qid] != eq:
                raise ValueError(f"{qid}: the battery and the wheel disagree")
            out[qid] = eq
    return list(out.items())


def _lean_block(ns: str, title: str, axioms: Sequence[str], table: Mapping,
                questions: Sequence[Tuple[str, str]], extra: str = "") -> List[str]:
    rels = [CW.relation_vector_q(a) for a in axioms]
    qrels = [CW.relation_vector_q(eq) for _, eq in questions]
    cols = CW.columns(*rels, *qrels)
    n, k = len(cols), len(axioms)
    zero = (Fraction(0),) * len(CW.AXES)
    # one axiom: `fin_cases i` leaves one goal, so `;` (the linter's preference)
    seq = " <;> " if k > 1 else "; "
    L: List[str] = []
    L.append(f"/-! ### {ns} — {title} -/")
    L.append("")
    L.append(f"namespace {ns}")
    L.append("")
    L.append("/-- The coordinates: quantities, then the primes of the coefficients. -/")
    L.append("def coords : List String :=")
    L.append("  [" + ", ".join(f'"{c}"' for c in cols) + "]")
    L.append("")
    L.append("/-- The axioms' relation vectors, in the order of the wheel: -/")
    for i, a in enumerate(axioms):
        L.append(f"-- {i}: {a}")
    L.append(f"def ax : Fin {k} → Fin {n} → ℚ :=")
    L.append("  " + _lean_matrix([[r.get(c, Fraction(0)) for c in cols] for r in rels], "  "))
    L.append("")
    L.append("/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`")
    L.append("(the zero row for a prime or a name no axiom uses). -/")
    L.append(f"def dim : Fin {n} → Fin 8 → ℚ :=")
    L.append("  " + _lean_matrix([table.get(c, zero) if not c.startswith("#") else zero
                                   for c in cols], "  "))
    L.append("")
    residuals = []
    for i, a in enumerate(axioms):
        r = CW.residual(a, table)
        if r is None:
            raise ValueError(f"{ns}: axiom {a!r} has an untabled quantity")
        residuals.append(r)
    if all(not any(r) for r in residuals):
        L.append("/-- Every axiom balances on all eight axes. -/")
        L.append("theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by")
        L.append("  intro i")
        L.append(f"  fin_cases i{seq}(funext a; fin_cases a <;> "
                 "norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])")
        L.append("")
    else:
        for i, r in enumerate(residuals):
            what = ("balances on all eight axes" if not any(r) else
                    f"balances at SI7; its residual on the angle axis A is {_lean_q(r[7])}"
                    if not any(r[:7]) else "does not balance at SI7")
            L.append(f"/-- Axiom {i} {what}. -/")
            L.append(f"theorem axiom_{i}_residual : dimL dim (ax {i}) = {_lean_row(r)} := by")
            L.append("  funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ]")
            L.append("")
    for (qid, eq), rel in zip(questions, qrels):
        v = [rel.get(c, Fraction(0)) for c in cols]
        x = CW.certificate(eq, axioms)
        name = lean_name(qid)
        L.append(f"/-- `{qid}`: {eq} -/")
        if x is not None:
            L.append(f"theorem {name} : Derivable (Set.range ax) {_lean_row(v)} :=")
            L.append(f"  derivable_of_combo ax {_lean_row(x)} _")
            L.append("    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])")
        else:
            w = CW.separating_functional(eq, axioms)
            wv = [Fraction(w.get(c, 0)) for c in cols]
            L.append(f"theorem {name} : ¬ Derivable (Set.range ax) {_lean_row(v)} :=")
            L.append(f"  not_derivable_of_dot ax {_lean_row(wv)} _")
            L.append(f"    (by intro i; fin_cases i{seq}norm_num [ax, Fin.sum_univ_succ])")
            L.append("    (by norm_num [Fin.sum_univ_succ])")
        L.append("")
    if extra:
        L.append(extra)
        L.append("")
    L.append(f"end {ns}")
    L.append("")
    return L


_LEAN_HEADER = '''module

public import Mathlib
public import RequestProject.GLM.ConnectedMachine

/-!
# The cent compiler's wheels: balance, derivations and refusals

*Created 31 October 2026 (repository check; the intake of cent_compiler_v12, directive D22).*
The formal half of `studies/CENT_WHEELS_STUDY.md` (§5). The supplied item
`source_material/ToDo/cent_compiler_v12` carries 31 formula wheels; this file proves, for the
wheels absorbed into `src/glm_universal/wheels/cent_wheels.py`, the finite facts their absorption
rests on.

A relation `L = R` is the vector of exponents of `L / R` (quantities, then the primes of the
coefficient), as `wheels.relation_vector` writes it; exponents are rational, so a fractional
power `(…)^(1/2)` is read exactly. A formula is derivable when its vector lies in the rational
span of the axioms' vectors (`GLM.ConnectedMachine.Derivable`).

* `dimL D` is a wheel's dimension map: a relation vector `v` goes to `∑ j, v j • D j`, the
  difference of the exponent vectors (over `L M T I H N J A`) of its two sides. An axiom's two
  sides have equal exponent vectors exactly when `dimL D` sends it to `0`. Each wheel proves
  `axioms_balanced`, or, where an axiom has a residual, states it exactly (`axiom_i_residual`):
  the angle convention is the repository's — SI7 decides (the first seven axes), the angle axis
  `A` is recorded.
* `derivable_of_combo` — a question is derivable when it equals an explicit rational combination
  of the axioms (the certificate, checked coordinate by coordinate).
* `not_derivable_of_dot` — a question is not derivable when an explicit rational functional
  vanishes on every axiom and not on it (`GLM.ConnectedMachine.not_derivable_of_functional`).

Sections: the absorbed wheels W16–W25, W28, W29, W32–W34 (each with its cases and the
questions of the study's §4 attributed to it, as corrected under the study's rule R); the W4 and
W6 additions; the W11–W15 axioms and their 14 supplied cases; and the supplied axioms that fail at
SI7 on their own tables (`Supplied`), each with its exact residual. `tests/test_cent_wheels.py`
reads every vector, table, certificate and verdict below and re-checks it against the Python in
exact arithmetic. Everything here is formal (`norm_num`; no `native_decide`).
-/

@[expose] public section

namespace GLM.CentWheels

open GLM.ConnectedMachine

/-! ## The dimension map and the two certificates -/

/-- The dimension map of a table `D` (one row of exponents over `L M T I H N J A` per
coordinate). -/
def dimL {n : ℕ} (D : Fin n → Fin 8 → ℚ) : (Fin n → ℚ) →ₗ[ℚ] (Fin 8 → ℚ) where
  toFun v := ∑ j, v j • D j
  map_add' x y := by simp [add_smul, Finset.sum_add_distrib]
  map_smul' c x := by simp [smul_smul, Finset.smul_sum]

theorem dimL_apply {n : ℕ} (D : Fin n → Fin 8 → ℚ) (v : Fin n → ℚ) :
    dimL D v = ∑ j, v j • D j := rfl

/-- The functional `v ↦ ∑ j, w j * v j`. -/
def dotL {n : ℕ} (w : Fin n → ℚ) : (Fin n → ℚ) →ₗ[ℚ] ℚ where
  toFun v := ∑ j, w j * v j
  map_add' x y := by simp [mul_add, Finset.sum_add_distrib]
  map_smul' c x := by
    simp only [Pi.smul_apply, smul_eq_mul, RingHom.id_apply, Finset.mul_sum]
    exact Finset.sum_congr rfl fun j _ => by ring

/-- **A rational combination of the axioms is derivable.** -/
theorem derivable_of_combo {n k : ℕ} (ax : Fin k → Fin n → ℚ) (c : Fin k → ℚ)
    (v : Fin n → ℚ) (h : v = ∑ i, c i • ax i) : Derivable (Set.range ax) v := by
  rw [h, Derivable]
  exact Submodule.sum_mem _ fun i _ => Submodule.smul_mem _ _ (Submodule.subset_span ⟨i, rfl⟩)

/-- **A separating functional refuses.** -/
theorem not_derivable_of_dot {n k : ℕ} (ax : Fin k → Fin n → ℚ) (w v : Fin n → ℚ)
    (hax : ∀ i, ∑ j, w j * ax i j = 0) (hv : ∑ j, w j * v j ≠ 0) :
    ¬ Derivable (Set.range ax) v :=
  not_derivable_of_functional (dotL w) (by rintro _ ⟨i, rfl⟩; exact hax i) hv
'''


def lean_source() -> str:
    """The text of ``Wheels/CentWheels.lean`` as this round wrote it, from the
    absorbed data (every vector, table and certificate computed here)."""
    from ..engineering.wheels import wheel_named
    from . import DOMAIN_WHEELS
    L: List[str] = [_LEAN_HEADER, "/-! ## The absorbed wheels -/", ""]
    for w in CW.CENT_WHEELS:
        L += _lean_block(w.id, w.title, w.axioms, CW.CENT_TABLES[w.id], wheel_questions(w))
    L += ["/-! ## The W4 and W6 additions (W4 and W6 of `engineering/wheels.py` are unchanged) -/", ""]
    for wid in ("W4", "W6"):
        ext = CW.extended_wheel(wid)
        qs = [(c.id, c.equation) for c in ext.cases]
        extra = ""
        if wid == "W6":
            base = wheel_named("W6")
            add_axiom, add_case = CW.ENGINEERING_ADDITIONS["W6"]
            rels = [CW.relation_vector_q(a) for a in ext.axioms]
            cols = CW.columns(*rels, *[CW.relation_vector_q(e) for _, e in qs])
            v = CW.relation_vector_q(add_case.equation)
            w = CW.separating_functional(add_case.equation, base.axioms)
            wv = [Fraction(w.get(c, 0)) for c in cols]
            k0 = len(base.axioms)
            extra = "\n".join([
                "/-- Without the addition, W6-03 is not derivable: the hydraulic-power axiom is",
                "what makes it so (`engineering/wheels.py` records W6-03 as not derivable). -/",
                f"theorem q_W6_03_without_addition :",
                f"    ¬ Derivable (Set.range (fun i : Fin {k0} => ax (Fin.castSucc i))) "
                f"{_lean_row([v.get(c, Fraction(0)) for c in cols])} :=",
                f"  not_derivable_of_dot _ {_lean_row(wv)} _",
                "    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])",
                "    (by norm_num [Fin.sum_univ_succ])",
            ])
        L += _lean_block(f"{wid}Ext", ext.title + " (with the supplied addition)", ext.axioms,
                         CW.ADDITION_TABLES[wid], qs, extra)
    L += ["/-! ## The W11–W15 axioms and their supplied cases -/", ""]
    for base in DOMAIN_WHEELS:
        L += _lean_block(f"{base.id}Dom", base.title, base.axioms, CW.DOMAIN_TABLES[base.id],
                         [(c.id, c.equation) for c in CW.DOMAIN_CASES[base.id]])
    L += ["/-! ## The supplied axioms that fail at SI7, on their own tables -/", "",
          "/-! Numbered from 1, as in the study; each with its supplied table's rows. -/", "",
          "namespace Supplied", ""]
    sup = supplied_wheels()
    for wid, i, text, _ in mark_d1()["failing_si7"]:
        table = supplied_table(sup[wid])
        rel = CW.relation_vector_q(text)
        cols = CW.columns(rel)
        r = CW.residual(text, table)
        zero = (Fraction(0),) * len(CW.AXES)
        nm = f"{wid}_axiom_{i}"
        L.append(f"/-- {wid} axiom {i} as supplied: {text} -/")
        L.append(f"def {nm}_coords : List String :=")
        L.append("  [" + ", ".join(f'"{c}"' for c in cols) + "]")
        L.append(f"def {nm} : Fin {len(cols)} → ℚ := {_lean_row([rel[c] for c in cols])}")
        L.append(f"def {nm}_dim : Fin {len(cols)} → Fin 8 → ℚ :=")
        L.append("  " + _lean_matrix([table.get(c, zero) if not c.startswith("#") else zero
                                       for c in cols], "  "))
        axis = next(j for j in range(7) if r[j])
        L.append(f"/-- Its residual on the supplied table: not zero at SI7 (axis "
                 f"{CW.AXES[axis]}). -/")
        L.append(f"theorem {nm}_residual : dimL {nm}_dim {nm} = {_lean_row(r)} := by")
        L.append(f"  funext a; fin_cases a <;> norm_num [dimL_apply, {nm}, {nm}_dim, Fin.sum_univ_succ]")
        L.append(f"theorem {nm}_unbalanced : dimL {nm}_dim {nm} ≠ 0 := by")
        L.append(f"  rw [{nm}_residual]; intro h; have := congrFun h {axis}; norm_num at this")
        L.append("")
    L += ["end Supplied", "", "end GLM.CentWheels", ""]
    return "\n".join(L)
