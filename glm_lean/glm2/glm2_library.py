#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 LIBRARY  —  the concept register
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Layer  :  Tier 1b — named concepts, exactly typed.
  Deps   :  glm2_meaning (standard library only).

  This module answers the question "how many concepts can this system encode
  with full meaning?" in two ways.

  (1) In principle: the encodable meaning module is the whole lattice
      (1/12)Z^11 (+) Z (+) (Z/2)^3 (+) labels, which glm2_codec puts in
      bijection with Z^24 and hence with the Leech lattice.  That is a
      countably infinite set of concepts, every one of them distinguished
      from every other by an exact test, and every one of them separated
      from every other in the carrier by the Leech minimal distance.

  (2) In practice: this register names CONCEPTS, a curated set of physical,
      chemical, informational and dimensionless quantities, each with

          * an exact meaning (ten rational exponents, decimal scale,
            tensor rank, P/T/C parities, nominal kind, domain),
          * a symbol, an SI expression and a short gloss,
          * aliases.

      RELATIONS then records defining laws between them ("force = mass *
      acceleration", "hbar = action / angle", ...) which the audit checks
      exactly.  Those checks are what keeps the register honest: a wrong
      exponent anywhere shows up as a failed relation.

  A deliberate design point: the register distinguishes quantities that a
  seven-exponent system must conflate.

      torque              L^2 M T^-2 A^-1     energy per radian
      energy              L^2 M T^-2
      frequency           T^-1                nominal kind "cycle"
      activity            T^-1                nominal kind "decay"
      angular frequency   A T^-1
      radiance            M T^-3 S^-1
      irradiance          M T^-3
      Planck constant     L^2 M T^-1          per cycle
      reduced Planck      L^2 M T^-1 A^-1     per radian
      entropy             L^2 M T^-2 H^-1     nominal kind "entropy"
      heat capacity       L^2 M T^-2 H^-1     nominal kind "capacity"
      Shannon entropy     B                   information

      python3 glm2_library.py       # register audit
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from typing import Dict, List, Optional, Sequence, Tuple

from glm2_meaning import AXES, Meaning, ParseError

__all__ = [
    "Concept", "CONCEPTS", "ALIASES", "DOMAINS", "KINDS",
    "RELATIONS", "AFFINE_SCALES",
    "resolve", "lookup", "concept_names", "by_domain",
    "check_relations", "library_audit",
]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  DOMAINS AND NOMINAL KINDS
# ══════════════════════════════════════════════════════════════════════════════

DOMAINS: Dict[int, str] = {
    0: "base",
    1: "kinematics",
    2: "mechanics",
    3: "electromagnetism",
    4: "thermodynamics",
    5: "chemistry",
    6: "photometry",
    7: "radiometry",
    8: "radiation",
    9: "information",
    10: "fluids",
    11: "acoustics",
    12: "astronomy",
    13: "quantum",
    14: "materials",
    15: "geophysics",
    16: "dimensionless",
    17: "scaled units",
    18: "relativity",
    19: "plasma",
    20: "optics",
    21: "signals and control",
    22: "statistical mechanics",
    23: "biophysics",
    24: "meteorology",
    25: "electrochemistry",
}

#: nominal kinds separate quantities that share every exponent but are not
#: interchangeable.  Two labelled concepts are commensurable only if their
#: kinds agree.
KINDS: Dict[int, str] = {
    0: "unlabelled",
    1: "cycle rate",
    2: "nuclear decay rate",
    3: "entropy",
    4: "heat capacity",
    5: "energy",
    6: "torque-like",
    7: "absorbed dose",
    8: "dose equivalent",
    9: "electric potential",
    10: "magnetomotive force",
    11: "catalytic activity",
    12: "action",
    13: "seismic moment",
    14: "bandwidth",
    15: "count",
    16: "photon count rate",
    44: "particle electric dipole moment",
}


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE REGISTER
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Concept:
    name: str
    meaning: Meaning
    symbol: str
    unit: str
    gloss: str
    aliases: Tuple[str, ...] = ()

    def __str__(self) -> str:
        return f"{self.name} [{self.symbol}] = {self.meaning}  ({self.unit})"


CONCEPTS: Dict[str, Concept] = {}
ALIASES: Dict[str, str] = {}


_CURRENT_DOMAIN = 0


def _dom(index: int) -> None:
    """Set the domain that subsequent Q() registrations belong to."""
    global _CURRENT_DOMAIN
    _CURRENT_DOMAIN = index


def Q(name: str, symbol: str, unit: str, gloss: str = "",
      aliases: Sequence[str] = (), **fields) -> Concept:
    """Register one concept.  Keyword fields are axis exponents plus any of
    scale, rank, p, t, c, kind, domain."""
    fields.setdefault("domain", _CURRENT_DOMAIN)
    if name in CONCEPTS:
        raise ValueError(f"duplicate concept {name!r}")
    m = Meaning.make(**fields)
    con = Concept(name, m, symbol, unit, gloss, tuple(aliases))
    CONCEPTS[name] = con
    for a in aliases:
        key = a.strip().lower()
        if key in ALIASES and ALIASES[key] != name:
            raise ValueError(f"alias {a!r} already points at {ALIASES[key]!r}")
        ALIASES[key] = name
    return con


H = F  # short alias for exact rationals in the table below


# ── §2.1  base quantities ─────────────────────────────────────────────────────
_dom(0)
Q("length", "l", "m", "extent along a line", ("distance", "len"), L=1)
Q("mass", "m", "kg", "inertial mass", (), M=1)
Q("time", "t", "s", "duration", ("duration",), T=1)
Q("current", "I", "A", "electric current", ("electric_current",), I=1)
Q("temperature", "Th", "K", "thermodynamic temperature", ("temp",), H=1)
Q("amount", "n", "mol", "amount of substance", ("substance",), N=1)
Q("luminous_intensity", "Iv", "cd", "luminous intensity", ("candela",), J=1)
Q("angle", "th", "rad", "plane angle", ("plane_angle", "radian"), A=1)
Q("solid_angle", "Om", "sr", "solid angle", ("steradian",), S=1)
Q("information", "Inf", "bit", "Shannon information", ("bit", "shannon"), B=1)

# ── §2.2  kinematics ──────────────────────────────────────────────────────────
_dom(1)
Q("position", "r", "m", "position vector", ("displacement",), L=1, rank=1, p=1)
Q("area", "A", "m^2", "surface area", (), L=2)
Q("volume", "V", "m^3", "spatial volume", (), L=3)
Q("hypervolume", "V4", "m^4", "four-dimensional volume", (), L=4)
Q("wavenumber", "k", "1/m", "spatial frequency", (), L=-1)
Q("angular_wavenumber", "kw", "rad/m", "radians per metre", (), L=-1, A=1)
Q("curvature", "kap", "1/m", "reciprocal radius of curvature", (), L=-1)
Q("torsion_geom", "tau_g", "1/m", "torsion of a space curve", (), L=-1)
Q("speed", "v", "m/s", "magnitude of velocity", ("celerity",), L=1, T=-1)
Q("velocity", "vv", "m/s", "velocity vector", (), L=1, T=-1, rank=1, p=1)
Q("acceleration", "a", "m/s^2", "rate of change of velocity", (),
  L=1, T=-2, rank=1, p=1)
Q("jerk", "j", "m/s^3", "rate of change of acceleration", (), L=1, T=-3,
  rank=1, p=1)
Q("snap", "s4", "m/s^4", "rate of change of jerk", ("jounce",), L=1, T=-4,
  rank=1, p=1)
Q("angular_velocity", "om", "rad/s", "rate of rotation", ("spin_rate",),
  A=1, T=-1, rank=1)
Q("angular_acceleration", "al", "rad/s^2", "rate of change of rotation", (),
  A=1, T=-2, rank=1)
Q("frequency", "f", "Hz", "cycles per second", ("hertz",), T=-1, kind=1)
Q("angular_frequency", "omg", "rad/s", "radians per second", (), A=1, T=-1)
Q("period", "Tp", "s", "duration of one cycle", (), T=1)
Q("wavelength", "lam", "m", "spatial period", (), L=1)
Q("volumetric_flow", "Qv", "m^3/s", "volume per time", ("flow_rate",),
  L=3, T=-1)
Q("area_rate", "Ar", "m^2/s", "area swept per time", (), L=2, T=-1)
Q("strain_rate", "eps_dot", "1/s", "rate of deformation", (), T=-1)
Q("velocity_gradient", "gradv", "1/s", "spatial gradient of velocity", (),
  T=-1, rank=2)

# ── §2.3  mechanics ───────────────────────────────────────────────────────────
_dom(2)
Q("force", "F", "N", "Newtonian force", ("weight",), L=1, M=1, T=-2,
  rank=1, p=1)
Q("momentum", "p", "kg*m/s", "linear momentum", (), L=1, M=1, T=-1,
  rank=1, p=1)
Q("impulse", "Jimp", "N*s", "integral of force over time", (), L=1, M=1, T=-1,
  rank=1, p=1)
Q("energy", "E", "J", "energy", ("work", "heat"), L=2, M=1, T=-2, kind=5)
Q("kinetic_energy", "KE", "J", "energy of motion", (), L=2, M=1, T=-2, kind=5)
Q("potential_energy", "PE", "J", "energy of configuration", (),
  L=2, M=1, T=-2, kind=5)
Q("torque", "tau", "N*m/rad", "energy per radian of rotation", ("moment",),
  L=2, M=1, T=-2, A=-1, rank=1, kind=6)
Q("power", "P", "W", "energy per time", (), L=2, M=1, T=-3)
Q("action", "S", "J*s", "action", (), L=2, M=1, T=-1, kind=12)
Q("angular_momentum", "Lang", "J*s/rad", "moment of momentum", (),
  L=2, M=1, T=-1, A=-1, rank=1)
Q("moment_of_inertia", "Im", "kg*m^2/rad^2", "rotational inertia", (),
  L=2, M=1, A=-2)
Q("pressure", "pr", "Pa", "isotropic normal stress", (), L=-1, M=1, T=-2)
Q("stress", "sig", "Pa", "Cauchy stress tensor", (), L=-1, M=1, T=-2, rank=2)
Q("strain", "eps", "1", "relative deformation", (), rank=2)
Q("youngs_modulus", "Ey", "Pa", "tensile stiffness", ("elastic_modulus",),
  L=-1, M=1, T=-2)
Q("shear_modulus", "Gs", "Pa", "shear stiffness", (), L=-1, M=1, T=-2)
Q("bulk_modulus", "Kb", "Pa", "volumetric stiffness", (), L=-1, M=1, T=-2)
Q("compressibility", "kT", "1/Pa", "reciprocal bulk modulus", (),
  L=1, M=-1, T=2)
Q("elastic_compliance", "Sc", "1/Pa", "reciprocal stiffness", (),
  L=1, M=-1, T=2, rank=2)
Q("energy_density", "u", "J/m^3", "energy per volume", (), L=-1, M=1, T=-2)
Q("power_density", "pd", "W/m^3", "power per volume", (), L=-1, M=1, T=-3)
Q("specific_energy", "e_s", "J/kg", "energy per mass", (), L=2, T=-2)
Q("specific_power", "p_s", "W/kg", "power per mass", (), L=2, T=-3)
Q("density", "rho", "kg/m^3", "mass per volume", (), L=-3, M=1)
Q("surface_density", "rhoA", "kg/m^2", "mass per area", (), L=-2, M=1)
Q("linear_density", "rhoL", "kg/m", "mass per length", (), L=-1, M=1)
Q("specific_volume", "vs", "m^3/kg", "volume per mass", (), L=3, M=-1)
Q("surface_tension", "gam", "N/m", "energy per area", (), M=1, T=-2)
Q("spring_constant", "ks", "N/m", "force per extension", ("stiffness",),
  M=1, T=-2)
Q("rotational_stiffness", "kr", "N*m/rad^2", "torque per radian", (),
  L=2, M=1, T=-2, A=-2)
Q("damping_coefficient", "cd", "N*s/m", "force per velocity", (), M=1, T=-1)
Q("dynamic_viscosity", "mu", "Pa*s", "momentum diffusivity per density", (),
  L=-1, M=1, T=-1)
Q("kinematic_viscosity", "nu", "m^2/s", "momentum diffusivity", (), L=2, T=-1)
Q("mass_flow", "mdot", "kg/s", "mass per time", (), M=1, T=-1)
Q("mass_flux", "Jm", "kg/(m^2*s)", "mass per area per time", (),
  L=-2, M=1, T=-1)
Q("yank", "Y", "N/s", "rate of change of force", (), L=1, M=1, T=-3, rank=1,
  p=1)
Q("gravitational_constant", "G", "m^3/(kg*s^2)", "Newton constant", (),
  L=3, M=-1, T=-2)
Q("gravitational_field", "g", "m/s^2", "gravitational acceleration", (),
  L=1, T=-2, rank=1, p=1)
Q("gravitational_potential", "Phi_g", "J/kg", "potential per mass", (),
  L=2, T=-2)
Q("gravitational_parameter", "mu_G", "m^3/s^2", "GM of a body", (),
  L=3, T=-2)
Q("fracture_toughness", "KIC", "Pa*m^(1/2)", "critical stress intensity", (),
  L=H(-1, 2), M=1, T=-2)
Q("stress_intensity", "KI", "Pa*m^(1/2)", "crack-tip stress intensity", (),
  L=H(-1, 2), M=1, T=-2)
Q("fracture_energy", "Gc", "J/m^2", "energy per created area", (), M=1, T=-2)
Q("areal_moment", "Ia", "m^4", "second moment of area", (), L=4)
Q("section_modulus", "Zs", "m^3", "elastic section modulus", (), L=3)
Q("specific_impulse", "Isp", "s", "impulse per weight flow", (), T=1)
Q("mass_moment", "Mm", "kg*m", "first moment of mass", (), L=1, M=1)

# ── §2.4  electromagnetism ────────────────────────────────────────────────────
_dom(3)
Q("charge", "q", "C", "electric charge", (), T=1, I=1)
Q("voltage", "U", "V", "electric potential difference", ("emf", "potential"),
  L=2, M=1, T=-3, I=-1, kind=9)
Q("resistance", "R", "Ohm", "electrical resistance", (),
  L=2, M=1, T=-3, I=-2)
Q("impedance", "Z", "Ohm", "complex electrical impedance", (),
  L=2, M=1, T=-3, I=-2)
Q("reactance", "X", "Ohm", "imaginary part of impedance", (),
  L=2, M=1, T=-3, I=-2)
Q("conductance", "Ge", "S", "reciprocal resistance", (),
  L=-2, M=-1, T=3, I=2)
Q("admittance", "Ya", "S", "reciprocal impedance", (), L=-2, M=-1, T=3, I=2)
Q("capacitance", "Cc", "F", "charge per voltage", (), L=-2, M=-1, T=4, I=2)
Q("inductance", "Li", "H", "flux per current", (), L=2, M=1, T=-2, I=-2)
Q("magnetic_flux", "PhiB", "Wb", "magnetic flux", (), L=2, M=1, T=-2, I=-1)
Q("magnetic_flux_density", "B", "T", "magnetic flux density (axial)", (),
  M=1, T=-2, I=-1, rank=1)
Q("electric_field", "Ef", "V/m", "electric field strength (polar)", (),
  L=1, M=1, T=-3, I=-1, rank=1, p=1)
Q("electric_displacement", "D", "C/m^2", "electric displacement field", (),
  L=-2, T=1, I=1, rank=1, p=1)
Q("magnetic_field_h", "Hf", "A/m", "magnetic field strength", (),
  L=-1, I=1, rank=1)
Q("magnetic_vector_potential", "Av", "T*m", "magnetic vector potential", (),
  L=1, M=1, T=-2, I=-1, rank=1, p=1)
Q("permittivity", "eps_e", "F/m", "electric permittivity", (),
  L=-3, M=-1, T=4, I=2)
Q("permeability", "mu_m", "H/m", "magnetic permeability", (),
  L=1, M=1, T=-2, I=-2)
Q("resistivity", "rho_e", "Ohm*m", "electrical resistivity", (),
  L=3, M=1, T=-3, I=-2)
Q("conductivity", "sig_e", "S/m", "electrical conductivity", (),
  L=-3, M=-1, T=3, I=2)
Q("charge_density", "rho_q", "C/m^3", "charge per volume", (),
  L=-3, T=1, I=1)
Q("surface_charge_density", "sig_q", "C/m^2", "charge per area", (),
  L=-2, T=1, I=1)
Q("linear_charge_density", "lam_q", "C/m", "charge per length", (),
  L=-1, T=1, I=1)
Q("current_density", "Je", "A/m^2", "current per area", (),
  L=-2, I=1, rank=1, p=1)
Q("surface_current_density", "Ks", "A/m", "current per length", (),
  L=-1, I=1, rank=1, p=1)
Q("polarization", "Pe", "C/m^2", "electric dipole moment per volume", (),
  L=-2, T=1, I=1, rank=1, p=1)
Q("magnetization", "Mm_v", "A/m", "magnetic moment per volume", (),
  L=-1, I=1, rank=1)
Q("electric_dipole_moment", "pe", "C*m", "electric dipole moment", (),
  L=1, T=1, I=1, rank=1, p=1)
Q("magnetic_dipole_moment", "mu_d", "A*m^2", "magnetic dipole moment", (),
  L=2, I=1, rank=1)
Q("electric_quadrupole_moment", "Qe", "C*m^2", "electric quadrupole", (),
  L=2, T=1, I=1, rank=2)
# The one genuine T-anomaly in the register.  Dimensionally a permanent
# electric dipole moment of a particle is charge x length, which the T
# convention (e_T + e_I mod 2) grades even; but a permanent EDM aligned with
# the spin is T-odd, which is precisely why measuring one would signal
# CP violation.  The departure from the convention is recorded as t=1.
Q("particle_electric_dipole_moment", "d_EDM", "C*m",
  "permanent electric dipole moment of a particle (T-odd)", ("edm",),
  L=1, T=1, I=1, rank=1, p=1, t=1, kind=44)
Q("magnetomotive_force", "Fm", "A", "magnetomotive force", (), I=1, kind=10)
Q("reluctance", "Rm", "1/H", "magnetic reluctance", (),
  L=-2, M=-1, T=2, I=2)
Q("permeance", "Pm", "H", "reciprocal reluctance", (), L=2, M=1, T=-2, I=-2)
Q("poynting_vector", "Sp", "W/m^2", "electromagnetic energy flux", (),
  M=1, T=-3, rank=1, p=1)
Q("electron_mobility", "mob", "m^2/(V*s)", "drift velocity per field", (),
  M=-1, T=2, I=1)
Q("hall_coefficient", "RH", "m^3/C", "Hall coefficient", (),
  L=3, T=-1, I=-1)
Q("elementary_charge", "e_q", "C", "elementary charge", (), T=1, I=1)
Q("vacuum_permittivity", "eps0", "F/m", "electric constant", (),
  L=-3, M=-1, T=4, I=2)
Q("vacuum_permeability", "mu0", "H/m", "magnetic constant", (),
  L=1, M=1, T=-2, I=-2)
Q("vacuum_impedance", "Z0", "Ohm", "impedance of free space", (),
  L=2, M=1, T=-3, I=-2)
Q("capacitance_per_length", "Cl", "F/m", "distributed capacitance", (),
  L=-3, M=-1, T=4, I=2)
Q("inductance_per_length", "Ll", "H/m", "distributed inductance", (),
  L=1, M=1, T=-2, I=-2)
Q("electric_flux", "PhiE", "V*m", "electric flux", (), L=3, M=1, T=-3, I=-1)
Q("magnetic_susceptibility_volume", "chi_m", "1", "volume susceptibility", ())
Q("charge_mobility_product", "sigq", "S*m^2/mol", "molar conductivity", (),
  M=-1, T=3, I=2, N=-1)

# ── §2.5  thermodynamics ──────────────────────────────────────────────────────
_dom(4)
Q("entropy", "S_th", "J/K", "thermodynamic entropy", (),
  L=2, M=1, T=-2, H=-1, kind=3)
Q("heat_capacity", "C_th", "J/K", "heat capacity", (),
  L=2, M=1, T=-2, H=-1, kind=4)
Q("specific_heat_capacity", "cp", "J/(kg*K)", "heat capacity per mass", (),
  L=2, T=-2, H=-1)
Q("molar_heat_capacity", "Cm", "J/(mol*K)", "heat capacity per mole", (),
  L=2, M=1, T=-2, H=-1, N=-1)
Q("specific_entropy", "s_e", "J/(kg*K)", "entropy per mass", (),
  L=2, T=-2, H=-1)
Q("molar_entropy", "Sm", "J/(mol*K)", "entropy per mole", (),
  L=2, M=1, T=-2, H=-1, N=-1)
Q("thermal_conductivity", "k_th", "W/(m*K)", "Fourier conductivity", (),
  L=1, M=1, T=-3, H=-1)
Q("thermal_diffusivity", "alph", "m^2/s", "heat diffusivity", (), L=2, T=-1)
Q("thermal_resistance", "Rth", "K/W", "temperature drop per watt", (),
  L=-2, M=-1, T=3, H=1)
Q("thermal_conductance", "Gth", "W/K", "reciprocal thermal resistance", (),
  L=2, M=1, T=-3, H=-1)
Q("heat_transfer_coefficient", "h_c", "W/(m^2*K)", "convective coefficient",
  (), M=1, T=-3, H=-1)
Q("heat_flux", "q_f", "W/m^2", "power per area", (), M=1, T=-3)
Q("heat_flow", "Qdot", "W", "heat per time", (), L=2, M=1, T=-3)
Q("temperature_gradient", "gradT", "K/m", "temperature per length", (),
  L=-1, H=1, rank=1, p=1)
Q("thermal_expansion", "alpha_T", "1/K", "linear expansion coefficient", (),
  H=-1)
Q("stefan_boltzmann", "sig_SB", "W/(m^2*K^4)", "Stefan-Boltzmann constant",
  (), M=1, T=-3, H=-4)
Q("boltzmann_constant", "kB", "J/K", "Boltzmann constant", (),
  L=2, M=1, T=-2, H=-1, kind=3)
Q("gas_constant", "Rg", "J/(mol*K)", "molar gas constant", (),
  L=2, M=1, T=-2, H=-1, N=-1)
Q("enthalpy", "Hth", "J", "enthalpy", (), L=2, M=1, T=-2, kind=5)
Q("gibbs_energy", "Gth_e", "J", "Gibbs free energy", (),
  L=2, M=1, T=-2, kind=5)
Q("helmholtz_energy", "Ath", "J", "Helmholtz free energy", (),
  L=2, M=1, T=-2, kind=5)
Q("internal_energy", "Uth", "J", "internal energy", (), L=2, M=1, T=-2,
  kind=5)
Q("chemical_potential", "mu_c", "J/mol", "energy per mole", (),
  L=2, M=1, T=-2, N=-1)
Q("latent_heat", "Lh", "J/kg", "phase-change energy per mass", (), L=2, T=-2)
Q("calorific_value", "cv_e", "J/kg", "energy content per mass", (),
  L=2, T=-2)
Q("thermal_effusivity", "eff", "W*s^(1/2)/(m^2*K)", "thermal effusivity", (),
  M=1, T=H(-5, 2), H=-1)
Q("entropy_production_rate", "Sdot", "W/K", "entropy per time", (),
  L=2, M=1, T=-3, H=-1)

# ── §2.6  chemistry ───────────────────────────────────────────────────────────
_dom(5)
Q("molar_mass", "Mmol", "kg/mol", "mass per mole", (), M=1, N=-1)
Q("concentration", "cn", "mol/m^3", "amount per volume", ("molarity",),
  L=-3, N=1)
Q("molality", "bm", "mol/kg", "amount per solvent mass", (), M=-1, N=1)
Q("molar_volume", "Vm", "m^3/mol", "volume per mole", (), L=3, N=-1)
Q("catalytic_activity", "kat", "kat", "moles converted per second", (),
  T=-1, N=1, kind=11)
Q("reaction_rate", "r_rx", "mol/(m^3*s)", "amount per volume per time", (),
  L=-3, T=-1, N=1)
Q("rate_constant_first", "k1", "1/s", "first-order rate constant", (), T=-1)
Q("rate_constant_second", "k2", "m^3/(mol*s)", "second-order rate constant",
  (), L=3, T=-1, N=-1)
Q("avogadro_constant", "NA", "1/mol", "entities per mole", (), N=-1)
Q("faraday_constant", "Far", "C/mol", "charge per mole", (), T=1, I=1, N=-1)
Q("molar_energy", "Em", "J/mol", "energy per mole", (), L=2, M=1, T=-2, N=-1)
Q("diffusion_coefficient", "Dd", "m^2/s", "Fickian diffusivity", (),
  L=2, T=-1)
Q("mass_transfer_coefficient", "kc", "m/s", "mass transfer coefficient", (),
  L=1, T=-1)
Q("surface_concentration", "Gam", "mol/m^2", "amount per area", (),
  L=-2, N=1)
Q("partial_pressure", "pp", "Pa", "partial pressure", (), L=-1, M=1, T=-2)
Q("henry_constant", "kH", "Pa*m^3/mol", "Henry law constant", (),
  L=2, M=1, T=-2, N=-1)
Q("molar_absorptivity", "eps_a", "m^2/mol", "molar attenuation", (),
  L=2, N=-1)

# ── §2.7  photometry ──────────────────────────────────────────────────────────
_dom(6)
Q("luminous_flux", "Phi_v", "lm", "luminous power", ("lumen",), J=1, S=1)
Q("illuminance", "Ev", "lx", "luminous flux per area", ("lux",),
  L=-2, J=1, S=1)
Q("luminance", "Lv", "cd/m^2", "luminous intensity per area", ("nit",),
  L=-2, J=1)
Q("luminous_energy", "Qv", "lm*s", "luminous energy", (), T=1, J=1, S=1)
Q("luminous_exposure", "Hv", "lx*s", "illuminance integrated in time", (),
  L=-2, T=1, J=1, S=1)
Q("luminous_efficacy", "Kl", "lm/W", "luminous flux per watt", (),
  L=-2, M=-1, T=3, J=1, S=1)
Q("luminous_emittance", "Mv", "lm/m^2", "luminous flux emitted per area", (),
  L=-2, J=1, S=1)
Q("luminous_exitance_time", "Hvt", "lm*s/m^2", "time-integrated exitance", (),
  L=-2, T=1, J=1, S=1)

# ── §2.8  radiometry ──────────────────────────────────────────────────────────
_dom(7)
Q("radiant_flux", "Phi_e", "W", "radiant power", (), L=2, M=1, T=-3)
Q("radiant_intensity", "Ie", "W/sr", "radiant power per solid angle", (),
  L=2, M=1, T=-3, S=-1)
Q("irradiance", "Ee", "W/m^2", "radiant flux per area", (), M=1, T=-3)
Q("radiance", "Le", "W/(m^2*sr)", "radiant flux per area per solid angle", (),
  M=1, T=-3, S=-1)
Q("radiosity", "Je_r", "W/m^2", "radiant flux leaving a surface", (),
  M=1, T=-3)
Q("radiant_exposure", "He", "J/m^2", "irradiance integrated in time", (),
  M=1, T=-2)
Q("spectral_radiance_wl", "Le_lam", "W/(m^3*sr)", "radiance per wavelength",
  (), L=-1, M=1, T=-3, S=-1)
Q("spectral_irradiance_wl", "Ee_lam", "W/m^3", "irradiance per wavelength", (),
  L=-1, M=1, T=-3)
Q("spectral_flux_freq", "Phi_nu", "W/Hz", "radiant flux per frequency", (),
  L=2, M=1, T=-2)
Q("radiant_energy", "Qe", "J", "radiant energy", (), L=2, M=1, T=-2, kind=5)
Q("radiant_energy_density", "we", "J/m^3", "radiant energy per volume", (),
  L=-1, M=1, T=-2)

# ── §2.9  radiation and dosimetry ─────────────────────────────────────────────
_dom(8)
Q("activity", "Ar", "Bq", "nuclear decays per second", ("becquerel",),
  T=-1, kind=2)
Q("specific_activity", "a_s", "Bq/kg", "activity per mass", (),
  M=-1, T=-1, kind=2)
Q("absorbed_dose", "Dabs", "Gy", "energy absorbed per mass", ("gray",),
  L=2, T=-2, kind=7)
Q("equivalent_dose", "Heq", "Sv", "biologically weighted dose", ("sievert",),
  L=2, T=-2, kind=8)
Q("dose_rate", "Ddot", "Gy/s", "absorbed dose per time", (),
  L=2, T=-3, kind=7)
Q("kerma", "Kk", "Gy", "kinetic energy released per mass", (),
  L=2, T=-2, kind=7)
Q("exposure_xray", "Xx", "C/kg", "ionisation per mass", (), M=-1, T=1, I=1)
Q("particle_fluence", "Ph_f", "1/m^2", "particles per area", (), L=-2)
Q("fluence_rate", "phi_f", "1/(m^2*s)", "particles per area per time", (),
  L=-2, T=-1)
Q("cross_section", "sig_x", "m^2", "interaction cross section", ("barn_dim",),
  L=2)
Q("macroscopic_cross_section", "Sig_x", "1/m", "cross section per volume", (),
  L=-1)
Q("linear_attenuation", "mu_att", "1/m", "attenuation per length", (), L=-1)
Q("mass_attenuation", "mu_rho", "m^2/kg", "attenuation per areal density", (),
  L=2, M=-1)
Q("linear_energy_transfer", "LET", "J/m", "energy deposited per length", (),
  L=1, M=1, T=-2)
Q("neutron_flux", "phi_n", "1/(m^2*s)", "neutron fluence rate", (),
  L=-2, T=-1)

# ── §2.10  information ────────────────────────────────────────────────────────
_dom(9)
Q("information_rate", "Rb", "bit/s", "bits per second", ("bitrate",),
  T=-1, B=1)
Q("channel_capacity", "Cch", "bit/s", "Shannon capacity", (), T=-1, B=1)
Q("bandwidth", "Bw", "Hz", "frequency bandwidth", (), T=-1, kind=14)
Q("spectral_efficiency", "eta_s", "bit/s/Hz", "bits per second per hertz", (),
  B=1)
Q("information_density_area", "rho_iA", "bit/m^2", "bits per area", (),
  L=-2, B=1)
Q("information_density_volume", "rho_iV", "bit/m^3", "bits per volume", (),
  L=-3, B=1)
Q("landauer_energy", "E_L", "J/bit", "energy cost per bit", (),
  L=2, M=1, T=-2, B=-1)
Q("thermodynamic_bit_entropy", "S_b", "J/(K*bit)", "entropy per bit", (),
  L=2, M=1, T=-2, H=-1, B=-1)
Q("information_entropy", "Hs", "bit", "Shannon entropy", (), B=1, kind=3)
Q("mutual_information", "Imi", "bit", "mutual information", (), B=1)
Q("kolmogorov_complexity", "Kc", "bit", "description length", (), B=1)
Q("code_rate", "Rc", "1", "information bits per channel bit", ())
Q("noise_temperature", "Tn", "K", "equivalent noise temperature", (), H=1)
Q("noise_spectral_density", "N0", "W/Hz", "noise power per hertz", (),
  L=2, M=1, T=-2)
Q("computational_rate", "Rops", "1/s", "operations per second", (), T=-1)

# ── §2.11  fluids ─────────────────────────────────────────────────────────────
_dom(10)
Q("dynamic_pressure", "qdyn", "Pa", "kinetic pressure of a flow", (),
  L=-1, M=1, T=-2)
Q("kinematic_pressure", "Pk", "m^2/s^2", "pressure over density", (),
  L=2, T=-2)
Q("pressure_gradient", "gradp", "Pa/m", "gradient of pressure", (),
  L=-2, M=1, T=-2, rank=1, p=1)
Q("vorticity", "omg_v", "1/(rad s)", "curl of velocity (axial)", (),
  A=-1, T=-1, rank=1)
Q("circulation", "Gam_c", "m^2/s", "line integral of velocity", (),
  L=2, T=-1)
Q("stream_function", "psi_s", "m^2/s", "two-dimensional stream function", (),
  L=2, T=-1)
Q("velocity_potential", "phi_v", "m^2/s", "potential flow function", (),
  L=2, T=-1)
Q("hydraulic_conductivity", "Khyd", "m/s", "Darcy conductivity", (),
  L=1, T=-1)
Q("intrinsic_permeability", "kperm", "m^2", "Darcy permeability", (), L=2)
Q("hydraulic_head", "hh", "m", "pressure expressed as height", (), L=1)
Q("shear_stress", "tau_w", "Pa", "wall shear stress", (), L=-1, M=1, T=-2)
Q("friction_velocity", "u_tau", "m/s", "shear velocity", (), L=1, T=-1)
Q("bulk_viscosity", "zeta_v", "Pa*s", "volume viscosity", (),
  L=-1, M=1, T=-1)
Q("volumetric_flux", "qflux", "m/s", "volume per area per time", (),
  L=1, T=-1)
Q("drag_force", "Fd", "N", "resistive force of a flow", (),
  L=1, M=1, T=-2, rank=1, p=1)
Q("lift_force", "Fl", "N", "transverse aerodynamic force", (),
  L=1, M=1, T=-2, rank=1, p=1)
Q("sound_speed", "c_s", "m/s", "speed of sound", (), L=1, T=-1)
Q("mass_source_density", "Sm", "kg/(m^3*s)", "mass added per volume-time", (),
  L=-3, M=1, T=-1)

# ── §2.12  acoustics ──────────────────────────────────────────────────────────
_dom(11)
Q("sound_pressure", "p_a", "Pa", "acoustic pressure", (), L=-1, M=1, T=-2)
Q("sound_intensity", "I_a", "W/m^2", "acoustic power per area", (),
  M=1, T=-3)
Q("sound_power", "W_a", "W", "acoustic power", (), L=2, M=1, T=-3)
Q("acoustic_impedance", "Za", "Pa*s/m", "specific acoustic impedance", (),
  L=-2, M=1, T=-1)
Q("particle_velocity", "u_a", "m/s", "acoustic particle velocity", (),
  L=1, T=-1, rank=1, p=1)
Q("sound_exposure", "Ea", "Pa^2*s", "time-integrated squared pressure", (),
  L=-2, M=2, T=-3)
Q("acoustic_absorption", "aa", "1", "absorption coefficient", ())
Q("reverberation_time", "T60", "s", "decay time of a room", (), T=1)
Q("sound_energy_density", "w_a", "J/m^3", "acoustic energy per volume", (),
  L=-1, M=1, T=-2)

# ── §2.13  astronomy ──────────────────────────────────────────────────────────
_dom(12)
Q("luminosity", "Lstar", "W", "radiated power of a star", (),
  L=2, M=1, T=-3)
Q("flux_density_jansky", "Snu", "W/(m^2*Hz)", "spectral flux density", (),
  M=1, T=-2)
Q("surface_brightness", "Sb", "W/(m^2*sr)", "flux per solid angle", (),
  M=1, T=-3, S=-1)
Q("hubble_parameter", "H0", "1/s", "expansion rate", (), T=-1)
Q("critical_density", "rho_c", "kg/m^3", "closure density", (), L=-3, M=1)
Q("escape_velocity", "vesc", "m/s", "escape speed", (), L=1, T=-1)
Q("orbital_period", "Torb", "s", "period of an orbit", (), T=1)
Q("semi_major_axis", "a_orb", "m", "semi-major axis", (), L=1)
Q("specific_angular_momentum", "h_orb", "m^2/(s*rad)",
  "angular momentum per mass", (), L=2, T=-1, A=-1)
Q("schwarzschild_radius", "rs", "m", "gravitational radius", (), L=1)
Q("proper_motion", "mu_pm", "rad/s", "angular motion on the sky", (),
  A=1, T=-1)
Q("angular_diameter", "th_d", "rad", "apparent angular size", (), A=1)
Q("parallax", "pi_p", "rad", "trigonometric parallax", (), A=1)
Q("redshift", "z_r", "1", "cosmological redshift", ())
Q("mass_loss_rate", "Mdot_star", "kg/s", "stellar mass loss", (), M=1, T=-1)
Q("column_density", "N_col", "1/m^2", "particles along a line of sight", (),
  L=-2)
Q("optical_depth", "tau_o", "1", "optical depth", ())
Q("emission_measure", "EM_a", "1/m^5", "squared density along a path", (),
  L=-5)
Q("gravitational_wave_strain", "h_gw", "1", "dimensionless strain", (),
  rank=2)
Q("tidal_field", "Tt", "1/s^2", "tidal tensor", (), T=-2, rank=2)
Q("cosmological_constant", "Lam_c", "1/m^2", "cosmological constant", (),
  L=-2)
Q("solar_constant", "S0", "W/m^2", "irradiance at 1 au", (), M=1, T=-3)
Q("apparent_magnitude", "mag", "1", "logarithmic brightness", ())
Q("stellar_surface_gravity", "gstar", "m/s^2", "surface gravity", (),
  L=1, T=-2)

# ── §2.14  quantum and particle physics ───────────────────────────────────────
_dom(13)
Q("planck_constant", "h_p", "J*s", "action per cycle", (),
  L=2, M=1, T=-1, kind=12)
Q("reduced_planck", "hbar", "J*s/rad", "action per radian", (),
  L=2, M=1, T=-1, A=-1, kind=12)
Q("electron_mass", "me", "kg", "electron rest mass", (), M=1)
Q("bohr_radius", "a0", "m", "Bohr radius", (), L=1)
Q("rydberg_energy", "Ry", "J", "Rydberg energy", (), L=2, M=1, T=-2, kind=5)
Q("compton_wavelength", "lam_C", "m", "Compton wavelength", (), L=1)
Q("de_broglie_wavelength", "lam_dB", "m", "de Broglie wavelength", (), L=1)
Q("bohr_magneton", "mu_B", "J/T", "Bohr magneton", (), L=2, I=1, rank=1)
Q("nuclear_magneton", "mu_N", "J/T", "nuclear magneton", (),
  L=2, I=1, rank=1)
Q("gyromagnetic_ratio", "gam_g", "rad/(s*T)", "moment over angular momentum",
  (), M=-1, T=1, I=1, A=1)
Q("magnetic_flux_quantum", "Phi0", "Wb", "flux quantum", (),
  L=2, M=1, T=-2, I=-1)
Q("conductance_quantum", "G0", "S", "conductance quantum", (),
  L=-2, M=-1, T=3, I=2)
Q("von_klitzing_constant", "RK", "Ohm", "quantum Hall resistance", (),
  L=2, M=1, T=-3, I=-2)
Q("josephson_constant", "KJ", "Hz/V", "Josephson constant", (),
  L=-2, M=-1, T=2, I=1)
Q("decay_constant", "lam_d", "1/s", "probability of decay per time", (),
  T=-1, kind=2)
Q("half_life", "t_half", "s", "half life", (), T=1)
Q("mean_lifetime", "tau_l", "s", "mean lifetime", (), T=1)
Q("binding_energy", "Eb", "J", "nuclear binding energy", (),
  L=2, M=1, T=-2, kind=5)
Q("wavefunction_3d", "psi", "m^(-3/2)", "position-space wavefunction", (),
  L=H(-3, 2))
Q("probability_density_3d", "rho_psi", "1/m^3", "position probability", (),
  L=-3)
Q("quantum_of_circulation", "hqc", "m^2/s", "h/2m", (), L=2, T=-1)
Q("spin", "s_spin", "J*s/rad", "intrinsic angular momentum", (),
  L=2, M=1, T=-1, A=-1, rank=1)
Q("magnetic_moment_density", "Mmd", "A/m", "moment per volume", (),
  L=-1, I=1, rank=1)
Q("coupling_constant", "g_c", "1", "dimensionless coupling", ())
Q("scattering_length", "a_sc", "m", "s-wave scattering length", (), L=1)
Q("density_of_states", "gE", "1/J", "states per unit energy", (),
  L=-2, M=-1, T=2)
Q("fermi_energy", "EF", "J", "Fermi energy", (), L=2, M=1, T=-2, kind=5)
Q("plasma_frequency", "wp", "rad/s", "plasma oscillation frequency", (),
  A=1, T=-1)
Q("debye_length", "lD", "m", "plasma screening length", (), L=1)
Q("larmor_radius", "rL", "m", "gyroradius", (), L=1)

# ── §2.15  materials and engineering ──────────────────────────────────────────
_dom(14)
Q("hardness", "Hv", "Pa", "indentation hardness", (), L=-1, M=1, T=-2)
Q("toughness_volumetric", "Ut", "J/m^3", "energy absorbed per volume", (),
  L=-1, M=1, T=-2)
Q("creep_rate", "eps_c", "1/s", "strain per time", (), T=-1)
Q("fatigue_limit", "sig_f", "Pa", "endurance stress", (), L=-1, M=1, T=-2)
Q("seebeck_coefficient", "Sse", "V/K", "thermopower", (),
  L=2, M=1, T=-3, I=-1, H=-1)
Q("peltier_coefficient", "Ppe", "V", "Peltier coefficient", (),
  L=2, M=1, T=-3, I=-1, kind=9)
Q("thomson_coefficient", "Tth", "V/K", "Thomson coefficient", (),
  L=2, M=1, T=-3, I=-1, H=-1)
Q("piezoelectric_d", "d_pz", "C/N", "piezoelectric charge constant", (),
  L=-1, M=-1, T=3, I=1)
Q("magnetostriction", "lam_ms", "1", "relative length change", ())
Q("coercivity", "Hc", "A/m", "coercive field", (), L=-1, I=1)
Q("remanence", "Br", "T", "remanent flux density", (), M=1, T=-2, I=-1)
Q("work_function", "Wf", "J", "electron escape energy", (),
  L=2, M=1, T=-2, kind=5)
Q("surface_energy", "gam_s", "J/m^2", "energy per area of surface", (),
  M=1, T=-2)
Q("adhesion_energy", "Wad", "J/m^2", "work of adhesion", (), M=1, T=-2)
Q("wear_rate", "kw", "m^3/(N*m)", "volume removed per work", (),
  L=1, M=-1, T=2)
Q("permeation_coefficient", "Pperm", "mol/(m*s*Pa)", "gas permeation", (),
  L=2, M=-1, T=1, N=1)
Q("specific_stiffness", "Es", "m^2/s^2", "modulus over density", (),
  L=2, T=-2)
Q("specific_strength", "sig_sp", "m^2/s^2", "strength over density", (),
  L=2, T=-2)
Q("thermal_shock_parameter", "Rts", "W/m", "thermal shock resistance", (),
  L=1, M=1, T=-3)

# ── §2.16  geophysics ─────────────────────────────────────────────────────────
_dom(15)
Q("seismic_moment", "M0", "N*m", "seismic moment", (),
  L=2, M=1, T=-2, kind=13)
Q("gravity_anomaly", "dg", "m/s^2", "gravity anomaly", (), L=1, T=-2)
Q("geothermal_gradient", "gT", "K/m", "temperature per depth", (),
  L=-1, H=1)
Q("heat_flow_density", "qgeo", "W/m^2", "geothermal heat flux", (),
  M=1, T=-3)
Q("magnetic_declination", "decl", "rad", "angle from true north", (), A=1)
Q("strain_seismic", "eps_s", "1", "seismic strain", (), rank=2)
Q("seismic_velocity", "vp", "m/s", "P-wave velocity", (), L=1, T=-1)
Q("porosity_geo", "phi_g", "1", "void fraction of rock", ())
Q("darcy_flux", "qD", "m/s", "Darcy velocity", (), L=1, T=-1)
Q("erosion_rate", "Er", "m/s", "surface lowering rate", (), L=1, T=-1)

# ── §2.17  dimensionless groups ───────────────────────────────────────────────
_dom(16)
for _name, _sym, _gloss in [
    ("reynolds_number", "Re", "inertia over viscosity"),
    ("mach_number", "Ma", "speed over sound speed"),
    ("prandtl_number", "Pr", "momentum over thermal diffusivity"),
    ("nusselt_number", "Nu", "convective over conductive transfer"),
    ("sherwood_number", "Sh", "convective over diffusive mass transfer"),
    ("schmidt_number", "Sc", "momentum over mass diffusivity"),
    ("peclet_number", "Pe", "advection over diffusion"),
    ("grashof_number", "Gr", "buoyancy over viscous forces"),
    ("rayleigh_number", "Ra", "buoyancy-driven convection"),
    ("weber_number", "We", "inertia over surface tension"),
    ("froude_number", "Fr", "inertia over gravity"),
    ("bond_number", "Bo", "gravity over surface tension"),
    ("capillary_number", "Ca", "viscous over surface tension"),
    ("knudsen_number", "Kn", "mean free path over length"),
    ("strouhal_number", "St", "oscillation over flow speed"),
    ("biot_number", "Bi", "surface over internal thermal resistance"),
    ("fourier_number", "Fo", "diffusive time over storage"),
    ("lewis_number", "Le", "thermal over mass diffusivity"),
    ("stanton_number", "Stn", "heat transfer over thermal capacity"),
    ("euler_number", "Eu", "pressure over inertial forces"),
    ("cauchy_number", "Cau", "inertia over elastic forces"),
    ("deborah_number", "De", "relaxation over observation time"),
    ("ohnesorge_number", "Oh", "viscous over inertia and surface tension"),
    ("richardson_number", "Ri", "buoyancy over shear"),
    ("rossby_number", "Ro", "inertia over Coriolis"),
    ("ekman_number", "Ek", "viscous over Coriolis"),
    ("stokes_number", "Stk", "particle response over flow time"),
    ("damkohler_number", "Da", "reaction over transport rate"),
    ("archimedes_number", "Arc", "gravitational over viscous forces"),
    ("atwood_number", "At", "density contrast"),
    ("brinkman_number", "Br_n", "viscous heating over conduction"),
    ("eckert_number", "Ec", "kinetic energy over enthalpy"),
    ("galilei_number", "Ga", "gravity over viscous forces"),
    ("jakob_number", "Ja", "sensible over latent heat"),
    ("laplace_number", "La", "surface tension over momentum transport"),
    ("marangoni_number", "Mg", "surface tension gradient driven flow"),
    ("morton_number", "Mo", "bubble shape parameter"),
    ("power_number", "Np", "impeller power coefficient"),
    ("bejan_number", "Be", "pressure drop parameter"),
    ("hartmann_number", "Ha", "magnetic over viscous forces"),
    ("lundquist_number", "Lu", "Alfven over resistive time"),
    ("magnetic_reynolds_number", "Rem", "advection over magnetic diffusion"),
    ("prater_number", "Pra", "reaction thermicity"),
    ("thiele_modulus", "Thi", "reaction over diffusion in a pellet"),
    ("womersley_number", "Wo", "pulsatile over viscous forces"),
    ("taylor_number", "Ta", "rotational over viscous forces"),
    ("dean_number", "Dn", "curved-pipe secondary flow"),
    ("bagnold_number", "Ba", "grain collision over viscous stress"),
    ("shields_parameter", "Shi", "sediment mobility"),
    ("courant_number", "Cou", "numerical advection stability"),
    ("fine_structure", "alpha_fs", "electromagnetic coupling"),
    ("refractive_index", "n_r", "phase velocity ratio"),
    ("relative_permittivity", "eps_r", "dielectric constant"),
    ("relative_permeability", "mu_r", "magnetic permeability ratio"),
    ("quality_factor", "Qf", "resonator sharpness"),
    ("poisson_ratio", "nu_p", "transverse over axial strain"),
    ("friction_coefficient", "mu_f", "friction over normal force"),
    ("drag_coefficient", "Cd", "drag over dynamic pressure and area"),
    ("lift_coefficient", "Cl_a", "lift over dynamic pressure and area"),
    ("emissivity", "eps_em", "radiative efficiency of a surface"),
    ("albedo", "alb", "reflected over incident radiation"),
    ("reflectance", "Rfl", "reflected fraction"),
    ("transmittance", "Trn", "transmitted fraction"),
    ("absorptance", "Abs", "absorbed fraction"),
    ("efficiency", "eta_e", "output over input"),
    ("mass_fraction", "wf", "mass of component over total"),
    ("mole_fraction", "xf", "moles of component over total"),
    ("void_fraction", "vf", "void volume over total"),
    ("porosity", "por", "pore volume over total"),
    ("tortuosity", "tor", "path length ratio"),
    ("safety_factor", "SF", "capacity over demand"),
    ("signal_to_noise", "SNR", "signal over noise power"),
    ("strain_ratio", "sr", "ratio of strains"),
    ("compression_ratio", "CR", "volume ratio"),
    ("aspect_ratio", "AR", "length over width"),
    ("duty_cycle", "DC", "on-time fraction"),
    ("packing_fraction", "pf", "occupied volume fraction"),
]:
    Q(_name, _sym, "1", _gloss, (), domain=16)

# ── §2.18  decimally scaled units ─────────────────────────────────────────────
_dom(17)
for _name, _sym, _unit, _fields in [
    ("kilometre", "km", "km", dict(L=1, scale=3)),
    ("centimetre", "cm", "cm", dict(L=1, scale=-2)),
    ("millimetre", "mm", "mm", dict(L=1, scale=-3)),
    ("micrometre", "um", "um", dict(L=1, scale=-6)),
    ("nanometre", "nm", "nm", dict(L=1, scale=-9)),
    ("picometre", "pm", "pm", dict(L=1, scale=-12)),
    ("angstrom", "Ang", "A", dict(L=1, scale=-10)),
    ("femtometre", "fm", "fm", dict(L=1, scale=-15)),
    ("gram", "g", "g", dict(M=1, scale=-3)),
    ("milligram", "mg", "mg", dict(M=1, scale=-6)),
    ("microgram", "ug", "ug", dict(M=1, scale=-9)),
    ("tonne", "tn", "t", dict(M=1, scale=3)),
    ("kilotonne", "ktn", "kt", dict(M=1, scale=6)),
    ("millisecond", "ms", "ms", dict(T=1, scale=-3)),
    ("microsecond", "us", "us", dict(T=1, scale=-6)),
    ("nanosecond", "ns", "ns", dict(T=1, scale=-9)),
    ("picosecond", "ps", "ps", dict(T=1, scale=-12)),
    ("femtosecond", "fs", "fs", dict(T=1, scale=-15)),
    ("kilohertz", "kHz", "kHz", dict(T=-1, scale=3, kind=1)),
    ("megahertz", "MHz", "MHz", dict(T=-1, scale=6, kind=1)),
    ("gigahertz", "GHz", "GHz", dict(T=-1, scale=9, kind=1)),
    ("terahertz", "THz", "THz", dict(T=-1, scale=12, kind=1)),
    ("litre", "L_v", "L", dict(L=3, scale=-3)),
    ("millilitre", "mL", "mL", dict(L=3, scale=-6)),
    ("hectare", "ha", "ha", dict(L=2, scale=4)),
    ("bar_pressure", "bar", "bar", dict(L=-1, M=1, T=-2, scale=5)),
    ("millibar", "mbar", "mbar", dict(L=-1, M=1, T=-2, scale=2)),
    ("kilopascal", "kPa", "kPa", dict(L=-1, M=1, T=-2, scale=3)),
    ("megapascal", "MPa", "MPa", dict(L=-1, M=1, T=-2, scale=6)),
    ("gigapascal", "GPa", "GPa", dict(L=-1, M=1, T=-2, scale=9)),
    ("kilojoule", "kJ", "kJ", dict(L=2, M=1, T=-2, scale=3, kind=5)),
    ("megajoule", "MJ", "MJ", dict(L=2, M=1, T=-2, scale=6, kind=5)),
    ("kilowatt", "kW", "kW", dict(L=2, M=1, T=-3, scale=3)),
    ("megawatt", "MW", "MW", dict(L=2, M=1, T=-3, scale=6)),
    ("gigawatt", "GW", "GW", dict(L=2, M=1, T=-3, scale=9)),
    ("millivolt", "mV", "mV", dict(L=2, M=1, T=-3, I=-1, scale=-3, kind=9)),
    ("kilovolt", "kV", "kV", dict(L=2, M=1, T=-3, I=-1, scale=3, kind=9)),
    ("milliampere", "mA", "mA", dict(I=1, scale=-3)),
    ("microampere", "uA", "uA", dict(I=1, scale=-6)),
    ("kiloohm", "kOhm", "kOhm", dict(L=2, M=1, T=-3, I=-2, scale=3)),
    ("megaohm", "MOhm", "MOhm", dict(L=2, M=1, T=-3, I=-2, scale=6)),
    ("microfarad", "uF", "uF", dict(L=-2, M=-1, T=4, I=2, scale=-6)),
    ("nanofarad", "nF", "nF", dict(L=-2, M=-1, T=4, I=2, scale=-9)),
    ("millitesla", "mT", "mT", dict(M=1, T=-2, I=-1, scale=-3, rank=1)),
    ("kilobit", "kbit", "kbit", dict(B=1, scale=3)),
    ("megabit", "Mbit", "Mbit", dict(B=1, scale=6)),
    ("gigabit", "Gbit", "Gbit", dict(B=1, scale=9)),
    ("terabit", "Tbit", "Tbit", dict(B=1, scale=12)),
    ("kilobit_per_second", "kbps", "kbit/s", dict(B=1, T=-1, scale=3)),
    ("megabit_per_second", "Mbps", "Mbit/s", dict(B=1, T=-1, scale=6)),
    ("gigabit_per_second", "Gbps", "Gbit/s", dict(B=1, T=-1, scale=9)),
    ("kilogram_per_litre", "kgL", "kg/L", dict(L=-3, M=1, scale=3)),
    ("micromole", "umol", "umol", dict(N=1, scale=-6)),
    ("millimole", "mmol", "mmol", dict(N=1, scale=-3)),
    ("kilomole", "kmol", "kmol", dict(N=1, scale=3)),
    ("milliradian", "mrad", "mrad", dict(A=1, scale=-3)),
    ("microradian", "urad", "urad", dict(A=1, scale=-6)),
]:
    Q(_name, _sym, _unit, "decimally scaled unit", (), domain=17, **_fields)


# ── §2.19  relativity and gravitation ─────────────────────────────────────────
#: The relativistic block is where the tensor rank earns its keep: the metric,
#: the Christoffel symbols, the Riemann tensor and the stress-energy tensor all
#: share their exponents with much simpler quantities and are separated from
#: them only by rank.  The Planck units are given by their defining relations
#: (below) up to the usual numeric factors of 2*pi, which are not dimensional
#: statements and are therefore not the register's business.
_dom(18)
Q("lorentz_factor", "gam", "1", "1/sqrt(1 - v^2/c^2)", ("gamma_factor",))
Q("rapidity", "phi_r", "1", "hyperbolic velocity parameter", ())
Q("proper_time", "tau", "s", "time in the comoving frame", ())
Q("proper_distance", "d_p", "m", "distance on a spacelike slice", ())
Q("spacetime_interval_squared", "s2", "m^2", "invariant interval", (), L=2)
Q("four_velocity", "U", "m/s", "tangent to the world line", (),
  L=1, T=-1, rank=1, p=1)
Q("four_acceleration", "A4", "m/s^2", "derivative of four-velocity", (),
  L=1, T=-2, rank=1, p=1)
Q("four_momentum", "P4", "kg*m/s", "energy-momentum four-vector", (),
  L=1, M=1, T=-1, rank=1, p=1)
Q("four_current_density", "J4", "A/m^2", "charge-current four-vector", (),
  L=-2, I=1, rank=1, p=1)
Q("metric_tensor", "g", "1", "spacetime metric", (), rank=2)
Q("christoffel_symbol", "Gam", "1/m", "affine connection coefficients", (),
  L=-1, rank=3)
Q("riemann_tensor", "Riem", "1/m^2", "Riemann curvature", (), L=-2, rank=4)
Q("ricci_tensor", "Ric", "1/m^2", "Ricci curvature", (), L=-2, rank=2)
Q("ricci_scalar", "Rs", "1/m^2", "scalar curvature", (), L=-2)
Q("kretschmann_scalar", "K_r", "1/m^4", "Riemann squared", (), L=-4)
Q("stress_energy_tensor", "Tmn", "Pa", "energy-momentum density", (),
  L=-1, M=1, T=-2, rank=2)
Q("faraday_tensor", "Fmn", "T", "electromagnetic field tensor", (),
  M=1, T=-2, I=-1, rank=2)
Q("einstein_gravitational_constant", "kap_E", "m^-1*kg^-1*s^2",
  "8*pi*G/c^4, the constant of the field equation", (), L=-1, M=-1, T=2)
Q("surface_gravity", "kap_H", "m/s^2", "horizon surface gravity", (),
  L=1, T=-2)
Q("hawking_temperature", "T_H", "K", "horizon temperature", (), H=1)
Q("bekenstein_hawking_entropy", "S_BH", "J/K", "horizon entropy", (),
  L=2, M=1, T=-2, H=-1, kind=3)
Q("rest_energy", "E0", "J", "m c^2", (), L=2, M=1, T=-2, kind=5)
Q("planck_length", "l_P", "m", "Planck length", (), L=1)
Q("planck_time", "t_P", "s", "Planck time", (), T=1)
Q("planck_mass", "m_P", "kg", "Planck mass", (), M=1)
Q("planck_energy", "E_P", "J", "Planck energy", (), L=2, M=1, T=-2, kind=5)
Q("planck_temperature", "T_P", "K", "Planck temperature", (), H=1)
Q("planck_charge", "q_P", "C", "Planck charge", (), T=1, I=1)

# ── §2.20  plasma physics ─────────────────────────────────────────────────────
_dom(19)
Q("plasma_beta", "beta_p", "1", "thermal over magnetic pressure", ())
Q("alfven_speed", "v_A", "m/s", "speed of an Alfven wave", (), L=1, T=-1)
Q("ion_sound_speed", "c_s", "m/s", "ion acoustic speed", (), L=1, T=-1)
Q("cyclotron_frequency", "om_c", "rad/s", "gyrofrequency q B / m", (),
  T=-1, A=1)
Q("collision_frequency", "nu_c", "1/s", "binary collision rate", (), T=-1)
Q("coulomb_logarithm", "lnL", "1", "ln(Lambda)", ())
Q("magnetic_diffusivity", "eta_m", "m^2/s", "resistive diffusivity", (),
  L=2, T=-1)
Q("magnetic_pressure", "p_B", "Pa", "B^2 / (2 mu0)", (), L=-1, M=1, T=-2)
Q("magnetic_energy_density", "u_B", "J/m^3", "energy stored in B", (),
  L=-1, M=1, T=-2)
Q("magnetic_tension_force_density", "f_T", "N/m^3",
  "curvature force per unit volume", (), L=-2, M=1, T=-2, rank=1, p=1)
Q("electron_temperature", "T_e", "K", "electron kinetic temperature", (), H=1)
Q("ion_temperature", "T_i", "K", "ion kinetic temperature", (), H=1)
Q("electron_number_density", "n_e", "1/m^3", "electrons per volume", (), L=-3)
Q("ion_number_density", "n_i", "1/m^3", "ions per volume", (), L=-3)
Q("plasma_skin_depth", "del_p", "m", "collisionless skin depth", (), L=1)
Q("bohm_diffusivity", "D_B", "m^2/s", "kT/(16 q B)", (), L=2, T=-1)
Q("debye_sphere_population", "N_D", "1", "particles in a Debye sphere", ())
Q("ionization_degree", "alp_i", "1", "ionized fraction", ())
Q("magnetic_helicity", "H_m", "Wb^2", "integral of A.B", (),
  L=4, M=2, T=-4, I=-2)
Q("current_sheet_thickness", "del_J", "m", "width of a current sheet", (),
  L=1)
Q("pinch_current", "I_p", "A", "total current in a pinch", (), I=1)
Q("radiation_pressure", "p_rad", "Pa", "momentum flux of radiation", (),
  L=-1, M=1, T=-2)

# ── §2.21  optics and photonics ───────────────────────────────────────────────
_dom(20)
Q("optical_power_dioptre", "D_o", "1/m", "reciprocal focal length",
  ("dioptre",), L=-1)
Q("focal_length", "f_l", "m", "focal length of an element", (), L=1)
Q("numerical_aperture", "NA", "1", "n sin(theta)", ())
Q("f_number", "f_N", "1", "focal length over aperture", ())
Q("beam_waist", "w0", "m", "Gaussian beam waist radius", (), L=1)
Q("rayleigh_range", "z_R", "m", "confocal parameter", (), L=1)
Q("etendue", "Et", "m^2*sr", "geometric extent", (), L=2, S=1)
Q("group_velocity", "v_g", "m/s", "envelope velocity", (), L=1, T=-1)
Q("phase_velocity", "v_p", "m/s", "velocity of constant phase", (),
  L=1, T=-1)
Q("group_index", "n_g", "1", "c over group velocity", ())
Q("chromatic_dispersion", "D_c", "s/m^2", "delay per length per wavelength",
  (), L=-2, T=1)
Q("optical_absorption_coefficient", "alp_o", "1/m", "Beer-Lambert alpha", (),
  L=-1)
Q("scattering_coefficient", "mu_s", "1/m", "scattering per length", (), L=-1)
Q("optical_extinction_index", "k_o", "1", "imaginary refractive index", ())
Q("birefringence", "dn", "1", "difference of refractive indices", ())
Q("optical_path_length", "OPL", "m", "n times geometric length", (), L=1)
Q("coherence_length", "l_c", "m", "length over which phase persists", (),
  L=1)
Q("coherence_time", "tau_c", "s", "time over which phase persists", (), T=1)
Q("finesse", "F_c", "1", "cavity finesse", ())
Q("free_spectral_range", "FSR", "Hz", "cavity mode spacing", (), T=-1)
Q("fringe_visibility", "V_f", "1", "interference contrast", ())
Q("photon_flux", "Phi_ph", "1/s", "photons per second", (), T=-1, kind=16)
Q("photon_irradiance", "E_ph", "1/(m^2*s)", "photons per area per time", (),
  L=-2, T=-1)
Q("nonlinear_index", "n2", "m^2/W", "Kerr coefficient", (), M=-1, T=3)
Q("laser_gain_coefficient", "g_l", "1/m", "small-signal gain", (), L=-1)
Q("beam_divergence", "th_d", "rad", "far-field half angle", (), A=1)
Q("saturation_intensity", "I_sat", "W/m^2", "gain saturation intensity", (),
  M=1, T=-3)
Q("spectral_linewidth", "dnu", "Hz", "width of a spectral line", (), T=-1)
Q("quantum_efficiency", "eta_q", "1", "carriers per photon", ())
Q("responsivity", "R_d", "A/W", "photodetector responsivity", (),
  L=-2, M=-1, T=3, I=1)
Q("optical_density", "OD", "1", "decadic absorbance", ("absorbance",))
Q("polarisation_degree", "P_pol", "1", "degree of polarisation", ())
Q("verdet_constant", "V_v", "rad/(T*m)", "Faraday rotation constant", (),
  L=-1, M=-1, T=2, I=1, A=1)

# ── §2.22  signals and control ────────────────────────────────────────────────
#: This block is the clearest demonstration of why the exponents are rational:
#: an amplitude spectral density is a quantity per root hertz, and its time
#: exponent is -5/2.  No integer-exponent system can hold it.
_dom(21)
Q("sampling_rate", "f_s", "1/s", "samples per second", (), T=-1)
Q("sample_period", "T_s", "s", "time between samples", (), T=1)
Q("time_constant", "tau_s", "s", "first-order time constant", (), T=1)
Q("rise_time", "t_r", "s", "10-90 per cent rise time", (), T=1)
Q("settling_time", "t_set", "s", "time to enter the error band", (), T=1)
Q("group_delay", "t_g", "s", "derivative of phase with frequency", (), T=1)
Q("jitter", "t_j", "s", "timing uncertainty", (), T=1)
Q("natural_frequency", "om_n", "rad/s", "undamped natural frequency", (),
  T=-1, A=1)
Q("damping_ratio", "zeta", "1", "fraction of critical damping", ())
Q("phase_margin", "PM", "rad", "phase margin at unity gain", (), A=1)
Q("gain_margin", "GM", "1", "gain margin at phase crossover", ())
Q("loop_gain", "L_g", "1", "open-loop gain", ())
Q("overshoot", "M_p", "1", "peak overshoot fraction", ())
Q("noise_figure", "NF", "1", "noise factor", ())
Q("crest_factor", "CF", "1", "peak over rms", ())
Q("transfer_gain", "K_g", "1", "dimensionless transfer gain", ())
Q("bit_error_rate", "BER", "1", "errored bits per bit", ())
Q("symbol_rate", "R_sym", "1/s", "symbols per second", ("baud",), T=-1)
Q("slew_rate", "SR", "V/s", "maximum rate of output change", (),
  L=2, M=1, T=-4, I=-1)
Q("voltage_noise_density", "e_n", "V/Hz^(1/2)",
  "amplitude spectral density of a voltage noise", (),
  L=2, M=1, T=H(-5, 2), I=-1)
Q("current_noise_density", "i_n", "A/Hz^(1/2)",
  "amplitude spectral density of a current noise", (), T=H(1, 2), I=1)
Q("power_spectral_density_voltage", "S_v", "V^2/Hz",
  "power spectral density of a voltage", (), L=4, M=2, T=-5, I=-2)
Q("phase_noise_density", "S_ph", "rad^2/Hz", "phase noise spectral density",
  (), T=1, A=2)

# ── §2.23  statistical mechanics ──────────────────────────────────────────────
_dom(22)
Q("partition_function", "Z_p", "1", "sum over states", ())
Q("boltzmann_factor", "bf", "1", "E over kT", ())
Q("occupation_number", "n_occ", "1", "mean occupancy of a state", ())
Q("number_density", "n_v", "1/m^3", "particles per volume", (), L=-3)
Q("number_flux_density", "J_n", "1/(m^2*s)", "particles per area per time",
  (), L=-2, T=-1, rank=1, p=1)
Q("mean_free_path", "lam_mfp", "m", "mean distance between collisions", (),
  L=1)
Q("thermal_de_broglie_wavelength", "lam_th", "m", "thermal wavelength", (),
  L=1)
Q("correlation_length", "xi_c", "m", "range of correlations", (), L=1)
Q("correlation_time", "tau_cor", "s", "memory time of a fluctuation", (),
  T=1)
Q("relaxation_rate", "gam_r", "1/s", "inverse relaxation time", (), T=-1)
Q("collision_rate", "Z_c", "1/s", "collisions per particle per second", (),
  T=-1)
Q("phase_space_volume", "Om_ps", "(J*s)^3", "volume in a 6D phase space", (),
  L=6, M=3, T=-3)
Q("entropy_per_particle", "s_1", "J/K", "entropy of one particle", (),
  L=2, M=1, T=-2, H=-1, kind=3)
Q("free_energy_density", "f_v", "J/m^3", "Helmholtz energy per volume", (),
  L=-1, M=1, T=-2)
Q("fugacity", "f_g", "Pa", "effective pressure of a real gas", (),
  L=-1, M=1, T=-2)
Q("chemical_activity", "a_c", "1", "activity of a species", ())
Q("order_parameter", "psi_o", "1", "order parameter of a phase", ())
Q("critical_exponent", "nu_cr", "1", "exponent of a critical law", ())
Q("specific_gas_constant", "R_s", "J/(kg*K)", "gas constant per mass", (),
  L=2, T=-2, H=-1)

# ── §2.24  biophysics and medicine ────────────────────────────────────────────
_dom(23)
Q("metabolic_rate", "P_met", "W", "whole-body power", (), L=2, M=1, T=-3)
Q("specific_absorption_rate", "SAR", "W/kg", "absorbed power per mass", (),
  L=2, T=-3)
Q("cardiac_output", "CO", "m^3/s", "volumetric blood flow", (), L=3, T=-1)
Q("vascular_resistance", "R_vas", "Pa*s/m^3", "pressure per flow", (),
  L=-4, M=1, T=-1)
Q("blood_pressure", "p_bl", "Pa", "arterial pressure", (), L=-1, M=1, T=-2)
Q("osmotic_pressure", "Pi_os", "Pa", "van 't Hoff pressure", (),
  L=-1, M=1, T=-2)
Q("wall_shear_stress", "tau_w", "Pa", "shear at a vessel wall", (),
  L=-1, M=1, T=-2)
Q("membrane_potential", "V_m", "V", "transmembrane voltage", (),
  L=2, M=1, T=-3, I=-1, kind=9)
Q("membrane_capacitance_area", "c_m", "F/m^2", "capacitance per area", (),
  L=-4, M=-1, T=4, I=2)
Q("nerve_conduction_speed", "v_nc", "m/s", "action potential speed", (),
  L=1, T=-1)
Q("respiratory_rate", "f_resp", "1/s", "breaths per second", (), T=-1)
Q("tidal_volume", "V_T", "m^3", "volume of one breath", (), L=3)
Q("oxygen_uptake", "VO2", "mol/s", "moles of oxygen per second", (),
  N=1, T=-1)
Q("tissue_perfusion", "om_perf", "1/s", "blood volume per tissue volume per"
  " second", (), T=-1)
Q("drug_clearance", "CL", "m^3/s", "volume cleared per time", (), L=3, T=-1)
Q("michaelis_constant", "K_M", "mol/m^3", "half-saturation concentration",
  (), L=-3, N=1)
Q("binding_affinity", "K_a", "m^3/mol", "association constant", (),
  L=3, N=-1)
Q("hill_coefficient", "n_H", "1", "cooperativity exponent", ())
Q("enzyme_turnover_number", "k_cat", "1/s", "catalytic rate constant", (),
  T=-1)
Q("biological_half_life", "t_bio", "s", "elimination half life", (), T=1)
Q("bone_mineral_density", "BMD", "kg/m^2", "areal bone density", (),
  L=-2, M=1)
Q("body_surface_area", "BSA", "m^2", "external body area", (), L=2)
Q("receptor_density", "n_rec", "1/m^2", "receptors per area", (), L=-2)

# ── §2.25  meteorology and climate ────────────────────────────────────────────
_dom(24)
Q("precipitation_rate", "P_r", "m/s", "depth of water per time", (),
  L=1, T=-1)
Q("evaporation_rate", "E_r", "kg/(m^2*s)", "mass evaporated per area per"
  " time", (), L=-2, M=1, T=-1)
Q("specific_humidity", "q_h", "1", "water mass per moist air mass", ())
Q("mixing_ratio", "w_mr", "1", "water mass per dry air mass", ())
Q("relative_humidity", "RH", "1", "vapour pressure over saturation", ())
Q("vapour_pressure", "e_v", "Pa", "partial pressure of water vapour", (),
  L=-1, M=1, T=-2)
Q("potential_temperature", "th_p", "K", "temperature at reference pressure",
  (), H=1)
Q("lapse_rate", "Gam_l", "K/m", "temperature fall with height", (),
  L=-1, H=1)
Q("geopotential", "Phi_g", "J/kg", "gravitational potential of the"
  " atmosphere", (), L=2, T=-2)
Q("geopotential_height", "Z_g", "m", "geopotential over standard gravity",
  (), L=1)
Q("scale_height", "H_s", "m", "e-folding height of pressure", (), L=1)
Q("boundary_layer_height", "z_i", "m", "depth of the mixed layer", (), L=1)
Q("coriolis_parameter", "f_C", "rad/s", "2 Omega sin(latitude)", (),
  T=-1, A=1)
Q("brunt_vaisala_frequency", "N_BV", "rad/s", "buoyancy frequency", (),
  T=-1, A=1)
Q("wind_speed", "U_w", "m/s", "horizontal wind speed", (), L=1, T=-1)
Q("wind_stress", "tau_wind", "Pa", "momentum flux to the surface", (),
  L=-1, M=1, T=-2)
Q("radiative_forcing", "RF", "W/m^2", "change in net irradiance", (),
  M=1, T=-3)
Q("convective_available_potential_energy", "CAPE", "J/kg",
  "buoyant energy per mass", (), L=2, T=-2)
Q("cloud_liquid_water_content", "LWC", "kg/m^3", "condensed water per"
  " volume", (), L=-3, M=1)
Q("air_density", "rho_a", "kg/m^3", "density of moist air", (), L=-3, M=1)
Q("eddy_diffusivity", "K_e", "m^2/s", "turbulent transport coefficient", (),
  L=2, T=-1)
Q("greenhouse_gas_concentration", "c_GHG", "mol/m^3", "molar concentration"
  " of a trace gas", (), L=-3, N=1)

# ── §2.26  electrochemistry and energy storage ────────────────────────────────
_dom(25)
Q("electrode_potential", "E_el", "V", "potential against a reference", (),
  L=2, M=1, T=-3, I=-1, kind=9)
Q("overpotential", "eta_ov", "V", "potential beyond equilibrium", (),
  L=2, M=1, T=-3, I=-1, kind=9)
Q("cell_voltage", "U_cell", "V", "terminal voltage of a cell", (),
  L=2, M=1, T=-3, I=-1, kind=9)
Q("tafel_slope", "b_T", "V", "volts per decade of current", (),
  L=2, M=1, T=-3, I=-1, kind=9)
Q("exchange_current_density", "j0", "A/m^2", "equilibrium rate as a current",
  (), L=-2, I=1)
Q("limiting_current_density", "j_lim", "A/m^2", "transport-limited current",
  (), L=-2, I=1)
Q("charge_transfer_coefficient", "alp_ct", "1", "Butler-Volmer alpha", ())
Q("transference_number", "t_pl", "1", "fraction of current carried", ())
Q("coulombic_efficiency", "eta_C", "1", "charge out over charge in", ())
Q("state_of_charge", "SOC", "1", "fraction of capacity remaining", ())
Q("ionic_strength", "I_s", "mol/m^3", "ionic strength of an electrolyte", (),
  L=-3, N=1)
Q("molar_conductivity", "Lam_m", "S*m^2/mol", "conductivity per"
  " concentration", (), M=-1, T=3, I=2, N=-1)
Q("ionic_mobility", "u_ion", "m^2/(V*s)", "drift speed per field", (),
  M=-1, T=2, I=1)
Q("electrolyte_conductivity", "kap_e", "S/m", "conductivity of an"
  " electrolyte", (), L=-3, M=-1, T=3, I=2)
Q("electrochemical_equivalent", "z_eq", "kg/C", "mass deposited per charge",
  (), M=1, T=-1, I=-1)
Q("specific_capacity", "q_sp", "A*s/kg", "charge per mass", (),
  M=-1, T=1, I=1)
Q("double_layer_capacitance_area", "C_dl", "F/m^2", "double layer"
  " capacitance per area", (), L=-4, M=-1, T=4, I=2)
Q("diffusion_layer_thickness", "del_N", "m", "Nernst layer thickness", (),
  L=1)
Q("corrosion_rate", "v_cor", "m/s", "recession of a surface", (),
  L=1, T=-1)
Q("faradaic_efficiency", "eta_F", "1", "product per charge passed", ())
Q("energy_density_gravimetric", "e_g", "J/kg", "stored energy per mass", (),
  L=2, T=-2)
Q("power_density_gravimetric", "p_g", "W/kg", "power per mass", (),
  L=2, T=-3)

# ── §2.27  vector flux densities ──────────────────────────────────────────────
#: Several transport laws are vector equations whose scalar magnitudes are
#: already in the register.  These are the rank-1 carriers of those fluxes:
#: they are what makes `div(...)` of a flux, and hence a continuity equation,
#: expressible at the level of the full meaning.
Q("heat_current_density", "q_v", "W/m^2", "heat flux as a vector", (),
  M=1, T=-3, rank=1, p=1, domain=4)
Q("entropy_flux_density", "J_S", "W/(m^2*K)", "entropy flux as a vector", (),
  M=1, T=-3, H=-1, rank=1, p=1, domain=4)
Q("mass_current_density", "j_m", "kg/(m^2*s)", "mass flux as a vector", (),
  L=-2, M=1, T=-1, rank=1, p=1, domain=2)
Q("diffusion_flux", "J_d", "mol/(m^2*s)", "molar flux as a vector", (),
  L=-2, N=1, T=-1, rank=1, p=1, domain=5)
Q("seepage_velocity", "q_D", "m/s", "Darcy flux as a vector", (),
  L=1, T=-1, rank=1, p=1, domain=15)
Q("probability_current", "j_psi", "1/(m^2*s)", "quantum probability flux",
  (), L=-2, T=-1, rank=1, p=1, domain=13)


# ── §2.28  affine (non-multiplicative) scales ─────────────────────────────────
#: name -> (meaning of the *interval*, offset description).  An affine scale
#: is NOT a group element: 20 degC is not twice 10 degC.  The reasoner refuses
#: to multiply or divide these, and converts to the linear scale first.
AFFINE_SCALES: Dict[str, Tuple[str, str, str]] = {
    "celsius": ("temperature", "K", "T/K = T/degC + 273.15"),
    "fahrenheit": ("temperature", "K", "T/K = (T/degF + 459.67) * 5/9"),
    "decibel": ("dimensionless", "1", "logarithmic ratio, 10^(dB/10)"),
    "neper": ("dimensionless", "1", "logarithmic ratio, e^(Np)"),
    "ph": ("concentration", "mol/m^3", "-log10(a_H+)"),
    "magnitude_astronomical": ("dimensionless", "1",
                               "-2.5 log10(flux ratio)"),
}


# ══════════════════════════════════════════════════════════════════════════════
# §3.  RESOLUTION
# ══════════════════════════════════════════════════════════════════════════════

_SYMBOL_INDEX: Dict[str, str] = {}
for _n, _c in CONCEPTS.items():
    _SYMBOL_INDEX.setdefault(_c.symbol.lower(), _n)


def concept_names() -> List[str]:
    return sorted(CONCEPTS)


def by_domain() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for name, con in CONCEPTS.items():
        out.setdefault(DOMAINS[con.meaning.domain], []).append(name)
    return {k: sorted(v) for k, v in sorted(out.items())}


def lookup(key: str) -> Optional[Concept]:
    """Resolve a name, alias or symbol to a Concept."""
    k = key.strip().lower()
    if k in CONCEPTS:
        return CONCEPTS[k]
    if k in ALIASES:
        return CONCEPTS[ALIASES[k]]
    if k in _SYMBOL_INDEX:
        return CONCEPTS[_SYMBOL_INDEX[k]]
    return None


def resolve(key: str) -> Optional[Meaning]:
    con = lookup(key)
    return None if con is None else con.meaning


# ══════════════════════════════════════════════════════════════════════════════
# §4.  DEFINING RELATIONS  (the register's own error check)
# ══════════════════════════════════════════════════════════════════════════════

#: (left concept, right expression) pairs that must hold exactly.  The right
#: hand side is written in the expression language of glm2_parse.
RELATIONS: Tuple[Tuple[str, str], ...] = (
    ("speed", "length / time"),
    ("acceleration", "speed / time"),
    ("jerk", "acceleration / time"),
    ("snap", "jerk / time"),
    ("force", "mass * acceleration"),
    ("momentum", "mass * speed"),
    ("impulse", "force * time"),
    ("energy", "force * length"),
    ("energy", "mass * speed^2"),
    ("power", "energy / time"),
    ("action", "energy * time"),
    ("pressure", "force / area"),
    ("energy_density", "energy / volume"),
    ("density", "mass / volume"),
    ("torque", "energy / angle"),
    ("angular_momentum", "action / angle"),
    ("moment_of_inertia", "mass * area / angle^2"),
    ("angular_velocity", "angle / time"),
    ("angular_momentum", "moment_of_inertia * angular_velocity"),
    ("energy", "moment_of_inertia * angular_velocity^2"),
    ("power", "torque * angular_velocity"),
    ("reduced_planck", "planck_constant / angle"),
    ("surface_tension", "energy / area"),
    ("dynamic_viscosity", "pressure * time"),
    ("kinematic_viscosity", "dynamic_viscosity / density"),
    ("gravitational_constant", "force * area / mass^2"),
    ("gravitational_potential", "energy / mass"),
    ("fracture_toughness", "stress * length^(1/2)"),
    ("charge", "current * time"),
    ("voltage", "power / current"),
    ("resistance", "voltage / current"),
    ("conductance", "current / voltage"),
    ("capacitance", "charge / voltage"),
    ("inductance", "magnetic_flux / current"),
    ("magnetic_flux", "voltage * time"),
    ("magnetic_flux_density", "magnetic_flux / area"),
    ("electric_field", "voltage / length"),
    ("electric_field", "force / charge"),
    ("permittivity", "capacitance / length"),
    ("permeability", "inductance / length"),
    ("resistivity", "resistance * length"),
    ("conductivity", "1 / resistivity"),
    ("current_density", "current / area"),
    ("poynting_vector", "electric_field * magnetic_field_h"),
    ("electron_mobility", "speed / electric_field"),
    ("entropy", "energy / temperature"),
    ("specific_heat_capacity", "heat_capacity / mass"),
    ("molar_heat_capacity", "heat_capacity / amount"),
    ("thermal_conductivity", "power / (length * temperature)"),
    ("thermal_diffusivity", "thermal_conductivity / (density * specific_heat_capacity)"),
    ("heat_flux", "power / area"),
    ("stefan_boltzmann", "heat_flux / temperature^4"),
    ("gas_constant", "boltzmann_constant * avogadro_constant"),
    ("chemical_potential", "energy / amount"),
    ("molar_mass", "mass / amount"),
    ("concentration", "amount / volume"),
    ("faraday_constant", "charge * avogadro_constant"),
    ("catalytic_activity", "amount / time"),
    ("luminous_flux", "luminous_intensity * solid_angle"),
    ("illuminance", "luminous_flux / area"),
    ("luminance", "luminous_intensity / area"),
    ("luminous_efficacy", "luminous_flux / power"),
    ("radiant_intensity", "radiant_flux / solid_angle"),
    ("irradiance", "radiant_flux / area"),
    ("radiance", "irradiance / solid_angle"),
    ("radiant_exposure", "irradiance * time"),
    ("absorbed_dose", "energy / mass"),
    ("dose_rate", "absorbed_dose / time"),
    ("exposure_xray", "charge / mass"),
    ("mass_attenuation", "linear_attenuation / density"),
    ("linear_energy_transfer", "energy / length"),
    ("information_rate", "information / time"),
    ("landauer_energy", "energy / information"),
    ("spectral_efficiency", "information_rate / bandwidth"),
    ("thermodynamic_bit_entropy", "entropy / information"),
    ("dynamic_pressure", "density * speed^2"),
    ("circulation", "speed * length"),
    ("vorticity", "rot(velocity)"),
    ("hydraulic_conductivity", "intrinsic_permeability * density * gravitational_field / dynamic_viscosity"),
    ("sound_intensity", "sound_pressure * particle_velocity"),
    ("acoustic_impedance", "sound_pressure / particle_velocity"),
    ("sound_exposure", "sound_pressure^2 * time"),
    ("flux_density_jansky", "irradiance / bandwidth"),
    ("surface_brightness", "irradiance / solid_angle"),
    ("gravitational_parameter", "gravitational_constant * mass"),
    ("specific_angular_momentum", "angular_momentum / mass"),
    ("proper_motion", "angle / time"),
    ("bohr_magneton", "energy / magnetic_flux_density"),
    ("gyromagnetic_ratio", "angular_velocity / magnetic_flux_density"),
    ("magnetic_flux_quantum", "action / charge"),
    ("von_klitzing_constant", "1 / conductance_quantum"),
    ("josephson_constant", "1 / magnetic_flux_quantum"),
    ("decay_constant", "1 / mean_lifetime"),
    ("wavefunction_3d", "volume^(-1/2)"),
    ("density_of_states", "1 / energy"),
    ("seebeck_coefficient", "voltage / temperature"),
    ("piezoelectric_d", "charge / force"),
    ("specific_stiffness", "youngs_modulus / density"),
    ("wear_rate", "volume / energy"),
    ("seismic_moment", "shear_modulus * area * length"),
    ("geothermal_gradient", "temperature / length"),
    ("kilometre", "1000 * length"),
    ("gram", "mass / 1000"),
    ("megapascal", "1000000 * pressure"),
    ("gigabit_per_second", "1000000000 * information / time"),
    # relativity and gravitation
    ("rest_energy", "mass * speed^2"),
    ("schwarzschild_radius", "gravitational_constant * mass / speed^2"),
    ("einstein_gravitational_constant", "gravitational_constant / speed^4"),
    ("surface_gravity", "gravitational_constant * mass / area"),
    ("hawking_temperature", "energy / boltzmann_constant"),
    ("ricci_scalar", "1 / area"),
    ("kretschmann_scalar", "ricci_scalar^2"),
    ("christoffel_symbol", "1 / length"),
    ("stress_energy_tensor", "energy / volume"),
    ("einstein_gravitational_constant", "ricci_scalar / stress_energy_tensor"),
    ("planck_length", "(planck_constant * gravitational_constant / speed^3)^(1/2)"),
    ("planck_time", "(planck_constant * gravitational_constant / speed^5)^(1/2)"),
    ("planck_mass", "(planck_constant * speed / gravitational_constant)^(1/2)"),
    ("planck_energy", "planck_mass * speed^2"),
    ("planck_temperature", "planck_energy / boltzmann_constant"),
    ("planck_charge", "(vacuum_permittivity * planck_constant * speed)^(1/2)"),
    ("planck_time", "planck_length / speed"),
    ("bekenstein_hawking_entropy",
     "boltzmann_constant * area / planck_length^2"),
    ("four_momentum", "mass * four_velocity"),
    ("faraday_tensor", "magnetic_flux_density"),
    # plasma physics
    ("alfven_speed", "magnetic_flux_density / (vacuum_permeability * density)^(1/2)"),
    ("magnetic_pressure", "magnetic_flux_density^2 / vacuum_permeability"),
    ("magnetic_energy_density", "magnetic_pressure"),
    ("plasma_beta", "pressure / magnetic_pressure"),
    ("magnetic_diffusivity", "resistivity / vacuum_permeability"),
    ("ion_sound_speed", "(boltzmann_constant * electron_temperature / mass)^(1/2)"),
    ("cyclotron_frequency", "charge * magnetic_flux_density * angle / mass"),
    ("bohm_diffusivity",
     "boltzmann_constant * electron_temperature / (charge * magnetic_flux_density)"),
    ("magnetic_helicity", "magnetic_vector_potential * magnetic_flux_density * volume"),
    ("electron_number_density", "1 / volume"),
    ("plasma_skin_depth", "speed * angle / plasma_frequency"),
    ("magnetic_tension_force_density", "magnetic_pressure / length"),
    ("radiation_pressure", "energy_density"),
    ("collision_frequency", "1 / time"),
    # optics and photonics
    ("optical_power_dioptre", "1 / focal_length"),
    ("etendue", "area * solid_angle"),
    ("rayleigh_range", "beam_waist^2 / wavelength"),
    ("chromatic_dispersion", "time / (length * wavelength)"),
    ("responsivity", "current / radiant_flux"),
    ("nonlinear_index", "1 / irradiance"),
    ("coherence_length", "speed * coherence_time"),
    ("free_spectral_range", "speed / optical_path_length"),
    ("optical_path_length", "refractive_index * length"),
    ("group_velocity", "speed / group_index"),
    ("beam_divergence", "wavelength * angle / beam_waist"),
    ("verdet_constant", "angle / (magnetic_flux_density * length)"),
    ("photon_irradiance", "photon_flux / area"),
    ("saturation_intensity", "irradiance"),
    ("laser_gain_coefficient", "1 / length"),
    ("spectral_linewidth", "1 / coherence_time"),
    # signals and control
    ("sampling_rate", "1 / sample_period"),
    ("natural_frequency", "angle / time"),
    ("slew_rate", "voltage / time"),
    ("voltage_noise_density", "voltage / frequency^(1/2)"),
    ("current_noise_density", "current / frequency^(1/2)"),
    ("power_spectral_density_voltage", "voltage_noise_density^2"),
    ("power_spectral_density_voltage", "voltage^2 / frequency"),
    ("phase_noise_density", "angle^2 / frequency"),
    ("symbol_rate", "1 / time"),
    ("group_delay", "angle / (angle / time)"),
    # statistical mechanics
    ("number_density", "1 / volume"),
    ("mean_free_path", "1 / (number_density * cross_section)"),
    ("collision_rate", "number_density * cross_section * speed"),
    ("relaxation_rate", "1 / correlation_time"),
    ("phase_space_volume", "action^3"),
    ("entropy_per_particle", "boltzmann_constant"),
    ("free_energy_density", "energy / volume"),
    ("fugacity", "pressure"),
    ("specific_gas_constant", "gas_constant / molar_mass"),
    ("boltzmann_factor", "energy / (boltzmann_constant * temperature)"),
    ("thermal_de_broglie_wavelength",
     "planck_constant / (mass * boltzmann_constant * temperature)^(1/2)"),
    ("correlation_length", "speed * correlation_time"),
    # biophysics and medicine
    ("metabolic_rate", "energy / time"),
    ("specific_absorption_rate", "power / mass"),
    ("cardiac_output", "volume / time"),
    ("vascular_resistance", "blood_pressure / cardiac_output"),
    ("membrane_capacitance_area", "capacitance / area"),
    ("nerve_conduction_speed", "length / time"),
    ("drug_clearance", "volume / time"),
    ("tissue_perfusion", "volumetric_flow / volume"),
    ("oxygen_uptake", "amount / time"),
    ("binding_affinity", "1 / michaelis_constant"),
    ("michaelis_constant", "concentration"),
    ("bone_mineral_density", "mass / area"),
    ("receptor_density", "1 / area"),
    ("wall_shear_stress", "dynamic_viscosity * strain_rate"),
    ("osmotic_pressure", "concentration * gas_constant * temperature"),
    ("enzyme_turnover_number", "1 / time"),
    # meteorology and climate
    ("precipitation_rate", "volume / (area * time)"),
    ("evaporation_rate", "mass / (area * time)"),
    ("lapse_rate", "temperature / length"),
    ("geopotential", "energy / mass"),
    ("scale_height", "specific_gas_constant * temperature / gravitational_field"),
    ("coriolis_parameter", "angular_velocity"),
    ("brunt_vaisala_frequency", "angle / time"),
    ("radiative_forcing", "power / area"),
    ("wind_stress", "air_density * wind_speed^2"),
    ("cloud_liquid_water_content", "mass / volume"),
    ("eddy_diffusivity", "length * wind_speed"),
    ("convective_available_potential_energy", "energy / mass"),
    ("greenhouse_gas_concentration", "concentration"),
    ("vapour_pressure", "pressure"),
    # electrochemistry and energy storage
    ("electrode_potential", "voltage"),
    ("overpotential", "voltage"),
    ("tafel_slope", "voltage"),
    ("exchange_current_density", "current / area"),
    ("molar_conductivity", "electrolyte_conductivity / concentration"),
    ("ionic_mobility", "speed / electric_field"),
    ("electrochemical_equivalent", "molar_mass / faraday_constant"),
    ("specific_capacity", "charge / mass"),
    ("double_layer_capacitance_area", "capacitance / area"),
    ("corrosion_rate", "length / time"),
    ("electrolyte_conductivity", "conductivity"),
    ("energy_density_gravimetric", "energy / mass"),
    ("power_density_gravimetric", "power / mass"),
    ("ionic_strength", "concentration"),
    ("faraday_constant", "elementary_charge * avogadro_constant"),
)


#: The relations above are stated the way a table of units states them: in
#: scalar-magnitude form, so they are checked at the level of the ten
#: exponents and the decimal scale.  The relations below are stated in the
#: FULL meaning: the two sides must agree in rank, in space-inversion parity
#: and in the derived T and C gradings as well.  They are the ones that use
#: the operator algebra of glm2_parse, and they are what makes the tensor
#: layer more than decoration — `energy = force * position` is false at this
#: level (the right-hand side is a rank-2 tensor) while
#: `energy = dot(force, position)` is true.
TENSOR_RELATIONS: Tuple[Tuple[str, str], ...] = (
    # kinematics
    ("velocity", "ddt(position)"),
    ("acceleration", "ddt(velocity)"),
    ("jerk", "ddt(acceleration)"),
    ("snap", "ddt(jerk)"),
    ("velocity", "moment(angular_velocity, position)"),
    ("angular_acceleration", "ddt(angular_velocity)"),
    # dynamics
    ("momentum", "mass * velocity"),
    ("force", "ddt(momentum)"),
    ("force", "mass * acceleration"),
    ("yank", "ddt(force)"),
    ("impulse", "integral_dt(force)"),
    ("energy", "dot(force, position)"),
    ("energy", "integral_dt(power)"),
    ("power", "dot(force, velocity)"),
    ("angular_momentum", "moment(position, momentum)"),
    ("torque", "moment(position, force)"),
    ("torque", "ddt(angular_momentum)"),
    ("gravitational_field", "grad(gravitational_potential)"),
    ("gravitational_field", "ddt(velocity)"),
    # continuum and fluids
    ("vorticity", "rot(velocity)"),
    ("energy", "integral_dV(energy_density)"),
    ("pressure_gradient", "grad(pressure)"),
    ("temperature_gradient", "grad(temperature)"),
    ("current_density", "curl(magnetization)"),
    # electromagnetism: all four Maxwell equations, at full meaning
    ("charge_density", "div(electric_displacement)"),
    ("current_density", "curl(magnetic_field_h)"),
    ("current_density", "ddt(electric_displacement)"),
    ("current_density", "charge_density * velocity"),
    ("magnetic_flux_density", "curl(magnetic_vector_potential)"),
    ("electric_field", "grad(voltage)"),
    ("electric_field", "ddt(magnetic_vector_potential)"),
    ("poynting_vector", "cross(electric_field, magnetic_field_h)"),
    ("charge", "integral_dV(charge_density)"),
    ("electric_dipole_moment", "charge * position"),
    ("magnetization", "magnetic_dipole_moment / volume"),
    ("polarization", "electric_displacement"),
    # the Lorentz force, where the parity bookkeeping is the whole point:
    # v is a polar vector, B is axial, and their cross product is polar again,
    # which is what a force has to be.
    ("force", "charge * electric_field"),
    ("force", "charge * cross(velocity, magnetic_flux_density)"),
    ("electric_field", "cross(velocity, magnetic_flux_density)"),
    ("torque", "moment(magnetic_dipole_moment, magnetic_flux_density)"),
    ("torque", "moment(electric_dipole_moment, electric_field)"),
    ("energy", "dot(electric_dipole_moment, electric_field)"),
    ("energy_density", "dot(electric_displacement, electric_field)"),
    ("energy_density", "dot(magnetic_field_h, magnetic_flux_density)"),
    ("power_density", "dot(current_density, electric_field)"),
    ("current_density", "conductivity * electric_field"),
    ("magnetic_field_h", "curl(magnetic_vector_potential) / vacuum_permeability"),
    ("charge_density", "permittivity * div(electric_field)"),
    ("charge_density", "permittivity * laplacian(voltage)"),
    # transport laws, as vector equations
    ("heat_current_density", "thermal_conductivity * grad(temperature)"),
    ("entropy_flux_density", "heat_current_density / temperature"),
    ("heat_current_density", "entropy_flux_density * temperature"),
    ("diffusion_flux", "diffusion_coefficient * grad(concentration)"),
    ("seepage_velocity", "hydraulic_conductivity * grad(hydraulic_head)"),
    ("number_flux_density", "number_density * velocity"),
    ("mass_current_density", "density * velocity"),
    ("probability_current", "probability_density_3d * velocity"),
    ("mass_source_density", "div(mass_current_density)"),
    ("strain_rate", "div(velocity)"),
    ("acceleration", "kinematic_viscosity * laplacian(velocity)"),
    ("pressure_gradient", "density * acceleration"),
    ("magnetic_tension_force_density", "pressure_gradient"),
    # field equations, stated as equalities between differential expressions.
    # Both sides are parsed, so the left of a pair need not be a bare name.
    ("ddt(temperature)", "thermal_diffusivity * laplacian(temperature)"),
    ("ddt(concentration)", "diffusion_coefficient * laplacian(concentration)"),
    ("ddt(magnetic_flux_density)",
     "magnetic_diffusivity * laplacian(magnetic_flux_density)"),
    ("ddt(vorticity)", "kinematic_viscosity * laplacian(vorticity)"),
    ("ddt(ddt(velocity_potential))",
     "sound_speed^2 * laplacian(velocity_potential)"),
    ("ddt(ddt(electric_field))", "speed^2 * laplacian(electric_field)"),
    ("ddt(ddt(position))", "acceleration"),
    ("div(heat_current_density)", "power_density"),
    ("div(current_density)", "ddt(charge_density)"),
)


def check_relations(strict: bool = False) -> Tuple[int, int, List[str]]:
    """
    Verify every defining relation of `RELATIONS` exactly.

    With `strict=False` (the default) the two sides must agree in the ten
    exponents and in the decimal scale: that is what a scalar-magnitude
    relation asserts.  With `strict=True` they must agree in the full
    meaning, rank and parities included.

    Returns (ok, total, failures).
    """
    return _check(RELATIONS, strict)


def check_tensor_relations() -> Tuple[int, int, List[str]]:
    """Verify `TENSOR_RELATIONS` at the level of the full meaning."""
    return _check(TENSOR_RELATIONS, True)


def _check(table, strict: bool) -> Tuple[int, int, List[str]]:
    from glm2_parse import parse  # local import: parser depends on this module
    ok = 0
    failures: List[str] = []
    for lhs, rhs in table:
        left = resolve(lhs)
        if left is None:
            # not a registered name: the left side may itself be an
            # expression, which is how a field equation is stated.
            try:
                left = parse(lhs)
            except ParseError:
                failures.append(f"{lhs}: unknown concept")
                continue
        try:
            right = parse(rhs)
        except ParseError as exc:
            failures.append(f"{lhs} = {rhs}: {exc}")
            continue
        good = (left.same_quantity(right) if strict else
                (left.exps == right.exps and left.scale == right.scale))
        if good:
            ok += 1
        else:
            failures.append(f"{lhs} = {rhs}: {left} vs {right}")
    return ok, len(table), failures


# ══════════════════════════════════════════════════════════════════════════════
# §5.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def library_audit() -> Dict[str, object]:
    ok, total, failures = check_relations()
    tok, ttotal, tfailures = check_tensor_relations()
    sok, _, _ = check_relations(strict=True)
    meanings = [c.meaning for c in CONCEPTS.values()]
    distinct = len({(m.exps, m.scale, m.rank, m.p, m.t, m.c, m.kind)
                    for m in meanings})
    frac = sum(1 for m in meanings if not m.is_integral())
    scaled = sum(1 for m in meanings if m.scale != 0)
    tensor = sum(1 for m in meanings if m.rank != 0)
    pseudo = sum(1 for m in meanings if m.is_pseudo())
    kinds = sum(1 for m in meanings if m.kind != 0)
    return {
        "concepts": len(CONCEPTS),
        "aliases": len(ALIASES),
        "domains": len(by_domain()),
        "distinct_meanings": distinct,
        "with_fractional_exponents": frac,
        "with_decimal_scale": scaled,
        "with_nonzero_rank": tensor,
        "pseudo_quantities": pseudo,
        "with_nominal_kind": kinds,
        "affine_scales": len(AFFINE_SCALES),
        "relations_checked": total,
        "relations_ok": ok,
        "relation_failures": failures,
        "relations_also_exact_at_full_meaning": sok,
        "tensor_relations_checked": ttotal,
        "tensor_relations_ok": tok,
        "tensor_relation_failures": tfailures,
        "all_encodable": all(m.encodable() for m in meanings),
    }


if __name__ == "__main__":  # pragma: no cover
    print("GLM-2 LIBRARY — register audit")
    rep = library_audit()
    for k, v in rep.items():
        if k == "relation_failures":
            print(f"  {k:28s} {len(v)}")
            for f in v:
                print(f"      ! {f}")
        else:
            print(f"  {k:28s} {v}")
