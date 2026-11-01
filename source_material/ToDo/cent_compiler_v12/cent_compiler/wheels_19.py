"""
Extension to 19 wheels: adds W16 (magnetic flux), W17 (gravitation),
W18 (ideal gas), W19 (EM waves). Each adds new dimensional vectors and
junctions that bridge to existing wheels.

The new wheels are chosen to surface delta-sigma-LIKE carrier patterns:
  - W16: explicit integral carrier (flux = ∫B·dA, emf = -dΦ/dt)
  - W17: period-carrier with implicit 4π² (Kepler)
  - W18: PV=nRT chemistry bridge (state-equation carrier)
  - W19: square-root irrational carrier (c = 1/√(με))
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Optional, Tuple

from .wheels import (
    Wheel, FormulaCase, SUPPORTED, UNDERSPECIFIED, CONVENTION, NEGATIVE,
    REFERENCE_DIMENSIONS, _d, wheel_quantities,
)
from .wheels_extended import (
    WHEELS_15, JUNCTIONS, NON_IDENTITIES, Junction, NonIdentity,
)


def _c(cid, eq, dim, der, status, explicit=None, note=""):
    return FormulaCase(cid, eq, dim, der, status, explicit, note)


# ---------------------------------------------------------------------------
# W16: Magnetic flux and induction
# ---------------------------------------------------------------------------

# Quantities and their SI dimensions:
#   magnetic_field (B):  [M T^-2 I^-1]   (tesla)
#   flux (Φ):            [M L^2 T^-2 I^-1]  (weber)
#   emf:                 [M L^2 T^-3 I^-1]  (volt; same as voltage)
#   inductance, current, area already exist in earlier wheels

REFERENCE_DIMENSIONS["magnetic_field"] = _d(M=1, T=-2, I=-1)
REFERENCE_DIMENSIONS["flux"]           = _d(L=2, M=1, T=-2, I=-1)
REFERENCE_DIMENSIONS["emf"]            = _d(L=2, M=1, T=-3, I=-1)  # same as voltage

W16 = Wheel("W16", "Magnetic flux and induction", (
    "flux = magnetic_field * area",              # Φ = B · A  (perpendicular)
    "flux = inductance * current",               # Φ = L · I  (flux linkage)
    "emf = flux / time",                          # |ε| = dΦ/dt ≈ Φ/t
), (
    _c("W16-01", "magnetic_field = flux / area", True, True, SUPPORTED),
    _c("W16-02", "inductance = flux / current", True, True, SUPPORTED),
    _c("W16-03", "emf = flux / time", True, True, SUPPORTED,
       note="Faraday's law magnitude; full law has a sign and a derivative"),
    _c("W16-N1", "flux = magnetic_field / area", False, False, NEGATIVE),
))


# ---------------------------------------------------------------------------
# W17: Gravitation and orbital mechanics
# ---------------------------------------------------------------------------

# Quantities and SI dimensions:
#   gravitational_constant (G):  [M^-1 L^3 T^-2]   (m^3/(kg·s^2))
#   source_mass (M):             [M]
#   distance (r):                [L]
#   surface_gravity (g):         [L T^-2]   (acceleration; same as W5 acceleration)
#   period:                      [T]        (already exists in W13)

REFERENCE_DIMENSIONS["gravitational_constant"] = _d(L=3, M=-1, T=-2)
REFERENCE_DIMENSIONS["source_mass"]            = _d(M=1)
REFERENCE_DIMENSIONS["distance"]               = _d(L=1)  # same as length
REFERENCE_DIMENSIONS["surface_gravity"]        = _d(L=1, T=-2)  # same as acceleration

W17 = Wheel("W17", "Gravitation and orbital mechanics", (
    "surface_gravity = gravitational_constant * source_mass / distance^2",   # g = GM/r^2
    "period^2 = distance^3 / (gravitational_constant * source_mass)",        # T^2 = r^3/(GM)  (Kepler, drops 4π²)
), (
    _c("W17-01", "gravitational_constant = surface_gravity * distance^2 / source_mass",
       True, True, SUPPORTED),
    _c("W17-02", "source_mass = surface_gravity * distance^2 / gravitational_constant",
       True, True, SUPPORTED),
    _c("W17-03", "period^2 = distance^3 / (gravitational_constant * source_mass)",
       True, True, CONVENTION, False,
       note="Kepler third law; convention drops the 4π² factor (radial convention)"),
    _c("W17-N1", "surface_gravity = distance^2 / (gravitational_constant * source_mass)",
       False, False, NEGATIVE),
))


# ---------------------------------------------------------------------------
# W18: Ideal gas law
# ---------------------------------------------------------------------------

# Quantities and SI dimensions:
#   gas_constant (R):  [M L^2 T^-2 Θ^-1 N^-1]   (J/(mol·K))
#   amount (n):        [N]                       (already in W12)
#   pressure, volume, temperature already exist

REFERENCE_DIMENSIONS["gas_constant"] = _d(L=2, M=1, T=-2, H=-1, N=-1)

W18 = Wheel("W18", "Ideal gas law", (
    "pressure * volume = amount * gas_constant * temperature",  # PV = nRT
), (
    # For monomial form: pressure = amount * gas_constant * temperature / volume
    _c("W18-01", "volume = amount * gas_constant * temperature / pressure",
       True, True, SUPPORTED),
    _c("W18-02", "temperature = pressure * volume / (amount * gas_constant)",
       True, True, SUPPORTED),
    _c("W18-03", "amount = pressure * volume / (gas_constant * temperature)",
       True, True, SUPPORTED),
    _c("W18-N1", "pressure = amount * gas_constant * temperature * volume",
       False, False, NEGATIVE),
))


# ---------------------------------------------------------------------------
# W19: Electromagnetic waves
# ---------------------------------------------------------------------------

# Quantities and SI dimensions:
#   permittivity (ε):    [M^-1 L^-3 T^4 I^2]   (F/m)
#   permeability (μ):    [M L T^-2 I^-2]        (H/m)
#   electric_field (E):  [M L T^-3 I^-1]        (V/m)
#   magnetic_field (B):  [M T^-2 I^-1]          (tesla; same as W16)
#   speed_of_light:      [L T^-1]               (already in W10)

REFERENCE_DIMENSIONS["permittivity"]    = _d(L=-3, M=-1, T=4, I=2)
REFERENCE_DIMENSIONS["permeability"]    = _d(L=1, M=1, T=-2, I=-2)
REFERENCE_DIMENSIONS["electric_field"]  = _d(L=1, M=1, T=-3, I=-1)

W19 = Wheel("W19", "Electromagnetic waves", (
    "speed_of_light^2 = 1 / (permittivity * permeability)",   # c^2 = 1/(με)
    "electric_field = speed_of_light * magnetic_field",       # E = cB
), (
    _c("W19-01", "permittivity * permeability = 1 / speed_of_light^2",
       True, True, SUPPORTED),
    _c("W19-02", "magnetic_field = electric_field / speed_of_light",
       True, True, SUPPORTED),
    _c("W19-03", "permittivity = 1 / (permeability * speed_of_light^2)",
       True, True, SUPPORTED),
    _c("W19-N1", "speed_of_light = permittivity * permeability",
       False, False, NEGATIVE),
))


# Build the plugged W4 and W6 (with the rotational-KE and hydraulic-power
# axioms added — these were predicted by the useful isomorphisms in the
# previous round and verified by plug_gaps.py).
from dataclasses import dataclass as _dc

W4_PLUGGED = Wheel("W4", "Rotational mechanics (with kinetic energy)", (
    "torque = moment_of_inertia * angular_acceleration",
    "power = torque * angular_velocity",
    "angular_momentum = moment_of_inertia * angular_velocity",
    "energy = 1/2 * moment_of_inertia * angular_velocity^2",   # PREDICTED by W4<->W5
), (
    _c("W4-01", "angular_acceleration = torque / moment_of_inertia", True, True, SUPPORTED),
    _c("W4-02", "power = torque * angular_velocity", True, True, SUPPORTED),
    _c("W4-03", "angular_momentum = moment_of_inertia * angular_velocity", True, True, SUPPORTED),
    _c("W4-04", "energy = 1/2 * moment_of_inertia * angular_velocity^2", True, True, SUPPORTED,
       note="PREDICTED by W4<->W5 isomorphism; standard rotational KE"),
    _c("W4-N1", "torque = moment_of_inertia * angular_velocity", False, False, NEGATIVE),
))

W6_PLUGGED = Wheel("W6", "Fluid statics and flow (with hydraulic power)", (
    "pressure = force / area",
    "volume_flow_rate = area * velocity",
    "force = pressure * area",
    "power = pressure * volume_flow_rate",   # PREDICTED by W4<->W6
), (
    _c("W6-01", "force = pressure * area", True, True, SUPPORTED),
    _c("W6-02", "velocity = volume_flow_rate / area", True, True, SUPPORTED),
    _c("W6-03", "power = pressure * volume_flow_rate", True, True, SUPPORTED,
       note="PREDICTED by W4<->W6 isomorphism; previously the 'union flip'"),
    _c("W6-N1", "pressure = force * area", False, False, NEGATIVE),
))

# Replace W4 and W6 with their plugged versions
WHEELS_15_PLUGGED: Tuple[Wheel, ...] = tuple(
    W4_PLUGGED if w.id == "W4" else
    W6_PLUGGED if w.id == "W6" else
    w for w in WHEELS_15
)

WHEELS_19: Tuple[Wheel, ...] = WHEELS_15_PLUGGED + (W16, W17, W18, W19)


# ---------------------------------------------------------------------------
# New junctions (in addition to the 12 from the 15-wheel plugged system)
# ---------------------------------------------------------------------------

NEW_JUNCTIONS_19: Tuple[Junction, ...] = JUNCTIONS + (
    # EM wave ↔ wave kinematics: light IS a wave, so its wave_speed = c
    # (already bridged for W9/W10; now bridge W9/W19 too)
    Junction("W9",  "W19", "wave_speed",     "an EM wave's wave_speed = speed_of_light",
             name_b="speed_of_light"),
    # Magnetic field is the same quantity in W16 and W19 (both are B-field)
    Junction("W16", "W19", "magnetic_field", "the magnetic field in the EM wave is the same field B"),
    # EMF (W16) is voltage (W1) — same SI dimensions and physical role
    Junction("W1",  "W16", "voltage",        "EMF and voltage are the same physical quantity",
             name_b="emf"),
    # Inductance appears in W2, W14, and W16 — bridge them
    Junction("W2",  "W16", "inductance",     "the inductor's L is the same inductance everywhere"),
    Junction("W14", "W16", "inductance",     "the LC circuit's inductor is the same L"),
    # Gravitational acceleration is the same as linear-dynamics acceleration
    Junction("W5",  "W17", "acceleration",   "surface gravity is an acceleration",
             name_b="surface_gravity"),
    # Gravitational source_mass and W5 mass are both masses (mass is extensive)
    Junction("W5",  "W17", "mass",           "mass is extensive; gravitational source_mass is a mass",
             name_b="source_mass"),
    # W17 distance is a length
    Junction("W11", "W17", "length",         "an orbital distance is a length",
             name_b="distance"),
    # W17 period is the same as W13 period
    Junction("W13", "W17", "period",         "an orbital period is a period"),
    # W18 temperature is the same as W8 temperature
    Junction("W8",  "W18", "temperature",    "thermodynamic temperature is the same quantity"),
    # W18 amount is the same as W12 amount
    Junction("W12", "W18", "amount",         "amount of substance is extensive"),
    # W18 volume is the same as W12 volume
    Junction("W12", "W18", "volume",         "the gas occupies a volume"),
    # W18 pressure is the same as W6 pressure
    Junction("W6",  "W18", "pressure",       "pressure is the same quantity"),
)


# ---------------------------------------------------------------------------
# Quick self-check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"WHEELS_19: {len(WHEELS_19)} wheels, "
          f"{sum(len(w.axioms) for w in WHEELS_19)} axioms, "
          f"{sum(len(w.cases) for w in WHEELS_19)} cases")
    print(f"NEW_JUNCTIONS_19: {len(NEW_JUNCTIONS_19)} junctions")
    # Sanity: dimensional consistency of every new axiom
    from glm_wheels import consistency
    for w in (W16, W17, W18, W19):
        print(f"\n{w.id} {w.title}:")
        for ax in w.axioms:
            ref = consistency(ax, "reference")
            si = consistency(ax, "si7")
            ext = consistency(ax, "ext10")
            print(f"  [{'OK' if ref and ref['consistent'] else 'XX'}] "
                  f"[{'OK' if si and si['consistent'] else 'XX'}] "
                  f"[{'OK' if ext and ext['consistent'] else 'XX'}]  {ax}")
