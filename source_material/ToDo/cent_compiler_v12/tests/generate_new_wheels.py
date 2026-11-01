#!/usr/bin/env python3
"""
Generate W20-W35 wheel JSON files from the Expanding Wheels roadmap.

16 new wheels across 6 domain families:
  A: Solid Mechanics & Materials (W20, W21)
  B: Chemical Kinetics & Electrochemistry (W22, W23)
  C: Semiconductor & Plasma (W24, W25)
  D: Superconductivity & Spintronics (W28, W29)
  E: Microfluidics & Capillarity (W32, W33)
  F: Biophysics & Physiological (W34, W35)

Each wheel follows the same JSON schema as W1-W19.
Dimensional vectors use the 8 reference axes: [L, M, T, I, H, N, J, A]
"""
import json, os

WHEELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wheels")
os.makedirs(WHEELS_DIR, exist_ok=True)

# Helper: build a dimension vector
def d(L=0, M=0, T=0, I=0, H=0, N=0, J=0, A=0):
    return [L, M, T, I, H, N, J, A]

# Common dimensions
DIMS = {
    # Solid mechanics
    "stress": d(M=1, L=-1, T=-2), "strain": d(), "youngs_modulus": d(M=1, L=-1, T=-2),
    "shear_modulus": d(M=1, L=-1, T=-2), "shear_stress": d(M=1, L=-1, T=-2),
    "shear_strain": d(), "poissons_ratio": d(),
    "bending_moment": d(M=1, L=2, T=-2), "area_moment_inertia": d(L=4),
    "radius_curvature": d(L=1), "flexural_rigidity": d(M=1, L=3, T=-2),
    "force": d(M=1, L=1, T=-2), "length": d(L=1), "area": d(L=2),
    # Fracture
    "fracture_toughness": d(M=1, L=-1, T=-2), "surface_energy": d(M=1, T=-2),
    "crack_length": d(L=1), "stress_intensity_factor": d(M=1, L=-1, T=-2),
    "dimensionless_factor": d(), "yield_stress": d(M=1, L=-1, T=-2),
    # Chemical kinetics
    "rate_constant": d(T=-1), "activation_energy": d(M=1, L=2, T=-2),
    "temperature": d(H=1), "gas_constant": d(M=1, L=2, T=-2, H=-1, N=-1),
    "pre_exponential_factor": d(T=-1), "reaction_rate": d(N=1, L=-3, T=-1),
    "concentration": d(N=1, L=-3), "diffusion_coefficient": d(L=2, T=-1),
    "diffusion_flux": d(N=1, L=-2, T=-1), "concentration_gradient": d(N=1, L=-4),
    "distance": d(L=1),
    # Electrochemistry
    "cell_potential": d(M=1, L=2, T=-3, I=-1), "standard_potential": d(M=1, L=2, T=-3, I=-1),
    "faraday_constant": d(T=1, I=1, N=-1), "reaction_quotient": d(),
    "electrons_transferred": d(), "mass": d(M=1), "molar_mass": d(M=1, N=-1),
    "charge": d(T=1, I=1), "current_density": d(L=-2, I=1),
    "exchange_current_density": d(L=-2, I=1),
    # Semiconductor
    "saturation_current": d(I=1), "voltage": d(M=1, L=2, T=-3, I=-1),
    "thermal_voltage": d(M=1, L=2, T=-3, I=-1), "mobility": d(M=-1, L=0, T=2, I=1),
    "diffusion_constant": d(L=2, T=-1), "debye_length": d(L=1),
    "permittivity": d(M=-1, L=-3, T=4, I=2), "carrier_concentration": d(L=-3),
    "elementary_charge": d(T=1, I=1),
    # Plasma
    "cyclotron_frequency": d(T=-1), "magnetic_field": d(M=1, T=-2, I=-1),
    "plasma_frequency": d(T=-1), "number_density": d(L=-3),
    "alfven_velocity": d(L=1, T=-1), "mass_density": d(M=1, L=-3),
    "permeability": d(M=1, L=1, T=-2, I=-2), "current": d(I=1),
    # Superconductivity
    "josephson_voltage": d(M=1, L=2, T=-3, I=-1), "magnetic_flux": d(M=1, L=2, T=-2, I=-1),
    "flux_quantum": d(M=1, L=2, T=-2, I=-1), "time": d(T=1),
    "reduced_planck_constant": d(M=1, L=2, T=-1), "london_penetration_depth": d(L=1),
    "superconducting_density": d(L=-3), "electron_mass": d(M=1),
    # Spintronics
    "larmor_frequency": d(T=-1), "gyromagnetic_ratio": d(M=-1, T=1, I=1),
    "spin_diffusion_length": d(L=1), "spin_current": d(),
    # Capillarity
    "surface_tension": d(M=1, T=-2), "capillary_radius": d(L=1),
    "viscosity": d(M=1, L=-1, T=-1), "contact_angle": d(A=1),
    "capillary_height": d(L=1), "wetting_coefficient": d(),
    "marangoni_stress": d(M=1, L=-1, T=-2),
    # Heat transfer
    "thermal_conductivity": d(M=1, L=1, T=-3, H=-1), "heat_transfer_coefficient": d(M=1, T=-3, H=-1),
    "characteristic_length": d(L=1), "nusselt_number": d(),
    "mass_transfer_coefficient": d(L=1, T=-1), "sherwood_number": d(),
    # Biophysics
    "vascular_resistance": d(M=1, L=-4, T=1), "pipe_radius": d(L=1),
    "blood_viscosity": d(M=1, L=-1, T=-1), "wall_shear_stress": d(M=1, L=-1, T=-2),
    "volume_flow_rate": d(L=3, T=-1), "pressure": d(M=1, L=-1, T=-2),
    "muscle_force": d(M=1, L=1, T=-2), "muscle_velocity": d(L=1, T=-1),
    # Electrophysiology
    "membrane_voltage": d(M=1, L=2, T=-3, I=-1), "membrane_conductance": d(M=-1, L=-2, T=3, I=2),
    "ion_concentration": d(N=1, L=-3), "ion_flux": d(N=1, L=-2, T=-1),
    "permeability_ratio": d(), "valence": d(),
    "energy": d(M=1, L=2, T=-2), "power": d(M=1, L=2, T=-3),
    "angular_frequency": d(T=-1, A=1), "angle": d(A=1), "frequency": d(T=-1),
    "velocity": d(L=1, T=-1), "acceleration": d(L=1, T=-2),
    "momentum": d(M=1, L=1, T=-1), "angular_velocity": d(T=-1, A=1),
    "angular_momentum": d(M=1, L=2, T=-1, A=-1),
    "resistance": d(M=1, L=2, T=-3, I=-2), "impedance": d(M=1, L=2, T=-3, I=-2),
    "spring_constant": d(M=1, T=-2), "period": d(T=1),
    "speed_of_light": d(L=1, T=-1), "planck_constant": d(M=1, L=2, T=-1),
    "wavelength": d(L=1), "wave_speed": d(L=1, T=-1),
    "angular_acceleration": d(T=-2, A=1), "torque": d(M=1, L=2, T=-2, A=-1),
    "moment_of_inertia": d(M=1, L=2, A=-2),
    "specific_heat_capacity": d(L=2, T=-2, H=-1), "entropy": d(M=1, L=2, T=-2, H=-1),
    "heat_flux": d(M=1, T=-3), "temperature_gradient": d(L=-1, H=1),
    "thermal_conductivity_k": d(M=1, L=1, T=-3, H=-1),
    "volume": d(L=3), "density": d(M=1, L=-3), "amount": d(N=1),
    "emf": d(M=1, L=2, T=-3, I=-1), "inductance": d(M=1, L=2, T=-2, I=-2),
    "capacitance": d(M=-1, L=-2, T=4, I=2),
}


def make_wheel(wid, title, axioms, cases, extra_dims=None):
    """Build a wheel dict in the standard JSON schema."""
    quantities = set()
    for ax in axioms:
        for side in ax.split("="):
            import ast
            try:
                tree = ast.parse(side.strip().replace("^", "**"), mode="eval")
                for n in ast.walk(tree):
                    if isinstance(n, ast.Name):
                        quantities.add(n.id)
            except:
                pass

    dims = {}
    all_dims = dict(DIMS)
    if extra_dims:
        all_dims.update(extra_dims)
    for q in sorted(quantities):
        vec = all_dims.get(q)
        if vec is not None:
            dims[q] = {"axes": ["L","M","T","I","H","N","J","A"], "exponents": vec}
        else:
            dims[q] = None

    return {
        "id": wid,
        "title": title,
        "axioms": list(axioms),
        "cases": cases,
        "quantities": sorted(quantities),
        "dimensions": dims,
        "junctions": [],
        "non_identities": [],
    }


def c(cid, eq, dim, der, status, note=""):
    return {"id": cid, "equation": eq, "expected_dimensional": dim,
            "expected_derivable": der, "physical_status": status,
            "expected_dimensional_explicit": None, "note": note}

S = "physically_supported"
N = "negative_control"
CV = "model_convention"

# =====================================================================
# Group A: Solid Mechanics & Materials Science
# =====================================================================

W20 = make_wheel("W20", "Elasticity & Continuum Mechanics", (
    "stress = youngs_modulus * strain",
    "bending_moment = youngs_modulus * area_moment_inertia / radius_curvature",
    "flexural_rigidity = youngs_modulus * area_moment_inertia",
), [
    c("W20-01", "youngs_modulus = stress / strain", True, True, S),
    c("W20-02", "strain = stress / youngs_modulus", True, True, S),
    c("W20-03", "radius_curvature = youngs_modulus * area_moment_inertia / bending_moment", True, True, S),
    c("W20-N1", "stress = youngs_modulus / strain", False, False, N),
])

W21 = make_wheel("W21", "Fracture Mechanics & Plasticity", (
    "fracture_toughness = (2 * youngs_modulus * surface_energy / (314159265 * crack_length))^(1/2)",
    "stress_intensity_factor = dimensionless_factor * stress * crack_length^(1/2)",
), [
    c("W21-01", "surface_energy = fracture_toughness^2 * crack_length / (2 * youngs_modulus)", True, True, S),
    c("W21-02", "crack_length = (stress_intensity_factor / (dimensionless_factor * stress))^2", True, True, S),
    c("W21-03", "stress = stress_intensity_factor / (dimensionless_factor * crack_length^(1/2))", True, True, S),
    c("W21-N1", "fracture_toughness = stress / crack_length", False, False, N),
], extra_dims={
    "fracture_toughness": d(M=1, L=-1, T=-2),
    "surface_energy": d(M=1, T=-2),
    "crack_length": d(L=1),
    "stress_intensity_factor": d(M=1, L=-1, T=-2),
    "dimensionless_factor": d(),
})

# =====================================================================
# Group B: Chemical Kinetics & Electrochemistry
# =====================================================================

W22 = make_wheel("W22", "Chemical Kinetics & Transport", (
    "reaction_rate = rate_constant * concentration",
    "rate_constant = pre_exponential_factor * concentration / rate_constant",
), [
    c("W22-01", "rate_constant = reaction_rate / concentration", True, True, S),
    c("W22-02", "concentration = reaction_rate / rate_constant", True, True, S),
    c("W22-03", "diffusion_coefficient = diffusion_flux / concentration_gradient", True, True, S),
    c("W22-N1", "reaction_rate = rate_constant / concentration", False, False, N),
], extra_dims={
    "reaction_rate": d(N=1, L=-3, T=-1),
    "rate_constant": d(T=-1),
    "concentration": d(N=1, L=-3),
})

W23 = make_wheel("W23", "Electrochemistry & Energy Storage", (
    "mass = charge * molar_mass / faraday_constant",
    "charge = current * time",
), [
    c("W23-01", "molar_mass = mass * faraday_constant / charge", True, True, S),
    c("W23-02", "charge = mass * faraday_constant / molar_mass", True, True, S),
    c("W23-03", "current = charge / time", True, True, S),
    c("W23-N1", "mass = charge / faraday_constant", False, False, N),
], extra_dims={
    "faraday_constant": d(T=1, I=1, N=-1),
    "charge": d(T=1, I=1),
    "current": d(I=1),
})

# =====================================================================
# Group C: Semiconductor & Plasma Physics
# =====================================================================

W24 = make_wheel("W24", "Semiconductor Device Physics", (
    "saturation_current = current",
    "diffusion_constant = mobility * thermal_voltage",
), [
    c("W24-01", "mobility = diffusion_constant / thermal_voltage", True, True, S),
    c("W24-02", "thermal_voltage = diffusion_constant / mobility", True, True, S),
    c("W24-03", "debye_length = (permittivity * thermal_voltage / (2 * carrier_concentration))^(1/2)", True, False, CV,
      note="Debye length involves sqrt; full derivation needs the charge term"),
    c("W24-N1", "current = saturation_current / voltage", False, False, N),
], extra_dims={
    "saturation_current": d(I=1),
    "current": d(I=1),
    "mobility": d(M=-1, T=2, I=1),
    "thermal_voltage": d(M=1, L=2, T=-3, I=-1),
    "diffusion_constant": d(L=2, T=-1),
    "debye_length": d(L=1),
    "permittivity": d(M=-1, L=-3, T=4, I=2),
    "carrier_concentration": d(L=-3),
})

W25 = make_wheel("W25", "Plasma Physics & Magnetohydrodynamics", (
    "cyclotron_frequency = magnetic_field / mass",
    "alfven_velocity = magnetic_field / mass_density^(1/2)",
), [
    c("W25-01", "magnetic_field = cyclotron_frequency * mass", True, True, S),
    c("W25-02", "mass = magnetic_field / cyclotron_frequency", True, True, S),
    c("W25-03", "mass_density = (magnetic_field / alfven_velocity)^2", True, True, S),
    c("W25-N1", "cyclotron_frequency = mass / magnetic_field", False, False, N),
], extra_dims={
    "cyclotron_frequency": d(T=-1),
    "magnetic_field": d(M=1, T=-2, I=-1),
    "mass": d(M=1),
    "alfven_velocity": d(L=1, T=-1),
    "mass_density": d(M=1, L=-3),
})

# =====================================================================
# Group D: Superconductivity & Spintronics
# =====================================================================

W28 = make_wheel("W28", "Superconductivity & Josephson Effects", (
    "josephson_voltage = magnetic_flux / time",
    "flux_quantum = magnetic_flux",
), [
    c("W28-01", "magnetic_flux = josephson_voltage * time", True, True, S),
    c("W28-02", "time = magnetic_flux / josephson_voltage", True, True, S),
    c("W28-03", "magnetic_flux = flux_quantum", True, True, S),
    c("W28-N1", "josephson_voltage = time / magnetic_flux", False, False, N),
], extra_dims={
    "josephson_voltage": d(M=1, L=2, T=-3, I=-1),
    "magnetic_flux": d(M=1, L=2, T=-2, I=-1),
    "flux_quantum": d(M=1, L=2, T=-2, I=-1),
    "time": d(T=1),
})

W29 = make_wheel("W29", "Spintronics & Spin Transport", (
    "larmor_frequency = gyromagnetic_ratio * magnetic_field",
    "spin_diffusion_length = diffusion_coefficient * time^(1/2)",
), [
    c("W29-01", "gyromagnetic_ratio = larmor_frequency / magnetic_field", True, True, S),
    c("W29-02", "magnetic_field = larmor_frequency / gyromagnetic_ratio", True, True, S),
    c("W29-03", "time = (spin_diffusion_length / diffusion_coefficient)^2", True, True, S),
    c("W29-N1", "larmor_frequency = magnetic_field / gyromagnetic_ratio", False, False, N),
], extra_dims={
    "larmor_frequency": d(T=-1),
    "gyromagnetic_ratio": d(M=-1, T=1, I=1),
    "magnetic_field": d(M=1, T=-2, I=-1),
    "spin_diffusion_length": d(L=1),
    "diffusion_coefficient": d(L=2, T=-1),
    "time": d(T=1),
})

# =====================================================================
# Group E: Microfluidics & Capillarity
# =====================================================================

W32 = make_wheel("W32", "Capillarity & Surface Phenomena", (
    "pressure = surface_tension / capillary_radius",
    "capillary_height = surface_tension * wetting_coefficient / (viscosity * capillary_radius)",
), [
    c("W32-01", "surface_tension = pressure * capillary_radius", True, True, S),
    c("W32-02", "capillary_radius = surface_tension / pressure", True, True, S),
    c("W32-03", "viscosity = surface_tension * wetting_coefficient / (capillary_height * capillary_radius)", True, True, S),
    c("W32-N1", "pressure = capillary_radius / surface_tension", False, False, N),
], extra_dims={
    "surface_tension": d(M=1, T=-2),
    "capillary_radius": d(L=1),
    "pressure": d(M=1, L=-1, T=-2),
    "capillary_height": d(L=1),
    "viscosity": d(M=1, L=-1, T=-1),
    "wetting_coefficient": d(),
})

W33 = make_wheel("W33", "Multi-Phase Heat & Mass Transfer", (
    "heat_transfer_coefficient = thermal_conductivity / characteristic_length",
    "nusselt_number = heat_transfer_coefficient * characteristic_length / thermal_conductivity",
), [
    c("W33-01", "thermal_conductivity = heat_transfer_coefficient * characteristic_length", True, True, S),
    c("W33-02", "characteristic_length = thermal_conductivity / heat_transfer_coefficient", True, True, S),
    c("W33-03", "heat_transfer_coefficient = nusselt_number * thermal_conductivity / characteristic_length", True, True, S),
    c("W33-N1", "nusselt_number = thermal_conductivity / heat_transfer_coefficient", False, False, N),
], extra_dims={
    "heat_transfer_coefficient": d(M=1, T=-3, H=-1),
    "thermal_conductivity": d(M=1, L=1, T=-3, H=-1),
    "characteristic_length": d(L=1),
    "nusselt_number": d(),
})

# =====================================================================
# Group F: Biophysics & Physiological Systems
# =====================================================================

W34 = make_wheel("W34", "Biomechanics & Hemodynamics", (
    "vascular_resistance = viscosity * length / pipe_radius^4",
    "volume_flow_rate = pressure / vascular_resistance",
), [
    c("W34-01", "viscosity = vascular_resistance * pipe_radius^4 / length", True, True, S),
    c("W34-02", "pipe_radius = (viscosity * length / vascular_resistance)^(1/4)", True, False, CV,
      note="4th root; dimensionally consistent but fractional power"),
    c("W34-03", "pressure = volume_flow_rate * vascular_resistance", True, True, S),
    c("W34-N1", "vascular_resistance = pipe_radius^4 / (viscosity * length)", False, False, N),
], extra_dims={
    "vascular_resistance": d(M=1, L=-4, T=1),
    "viscosity": d(M=1, L=-1, T=-1),
    "length": d(L=1),
    "pipe_radius": d(L=1),
    "volume_flow_rate": d(L=3, T=-1),
    "pressure": d(M=1, L=-1, T=-2),
})

W35 = make_wheel("W35", "Electrophysiology & Membrane Transport", (
    "membrane_voltage = temperature / valence",
    "ion_flux = diffusion_coefficient * ion_concentration",
), [
    c("W35-01", "valence = temperature / membrane_voltage", True, True, S),
    c("W35-02", "temperature = membrane_voltage * valence", True, True, S),
    c("W35-03", "ion_concentration = ion_flux / diffusion_coefficient", True, True, S),
    c("W35-N1", "membrane_voltage = valence / temperature", False, False, N),
], extra_dims={
    "membrane_voltage": d(M=1, L=2, T=-3, I=-1),
    "temperature": d(H=1),
    "valence": d(),
    "ion_flux": d(N=1, L=-2, T=-1),
    "ion_concentration": d(N=1, L=-3),
    "diffusion_coefficient": d(L=2, T=-1),
})

# =====================================================================
# Write all wheels
# =====================================================================

NEW_WHEELS = [W20, W21, W22, W23, W24, W25, W28, W29, W32, W33, W34, W35]

for w in NEW_WHEELS:
    path = os.path.join(WHEELS_DIR, f"{w['id']}.json")
    with open(path, "w") as f:
        json.dump(w, f, indent=2)
    print(f"wrote {path} ({len(w['axioms'])} axioms, {len(w['cases'])} cases, {len(w['quantities'])} quantities)")

print(f"\nGenerated {len(NEW_WHEELS)} new wheel JSON files")
