#!/usr/bin/env python3
"""Reproducible formula-wheel study for the GLM project.

This program deliberately separates four questions that the original study
conflated:

1. Can every symbol be parsed and grounded in the quantity registry?
2. Is the equation dimensionally homogeneous?
3. Is its monomial form derivable from the wheel's declared axioms?
4. Is the equation physically supported under the stated assumptions?

Dimensional homogeneity is necessary, but never sufficient, evidence for a
physical law.  Physical support is therefore preregistered in the cases below
and is not inferred by this program.

The implementation uses only the Python standard library.  Arithmetic for
dimensions, powers, coefficients, and algebraic rank tests is exact
(`fractions.Fraction`).  It never edits package data and uses no randomness.

Examples:
    python glm_formula_wheel_study_v2.py
    python glm_formula_wheel_study_v2.py --angle-policy explicit --verbose
    python glm_formula_wheel_study_v2.py --json-out formula_wheel_results.json
    python glm_formula_wheel_study_v2.py --self-test
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


VERSION = "2.0.0"
BASE_AXES = ("L", "M", "T", "I", "Theta", "N", "J", "A")
ZERO_DIM = tuple(Fraction(0) for _ in BASE_AXES)


def D(**powers: int) -> Tuple[Fraction, ...]:
    """Construct an exact dimension vector in BASE_AXES order."""
    unknown = set(powers) - set(BASE_AXES)
    if unknown:
        raise ValueError(f"unknown dimension axes: {sorted(unknown)}")
    return tuple(Fraction(powers.get(axis, 0)) for axis in BASE_AXES)


class PhysicalStatus(str, Enum):
    SUPPORTED = "physically_supported"
    UNDERSPECIFIED = "physically_underspecified"
    MODEL_CONVENTION = "model_convention"
    NEGATIVE_CONTROL = "negative_control"


class Outcome(str, Enum):
    DIMENSIONALLY_CONSISTENT = "dimensionally_consistent"
    DIMENSIONALLY_INCONSISTENT = "dimensionally_inconsistent"
    ALGEBRAICALLY_DERIVED = "algebraically_derived"
    NOT_ALGEBRAICALLY_DERIVED = "not_algebraically_derived"
    UNRESOLVED = "unresolved"
    EXECUTION_ERROR = "execution_error"


@dataclass(frozen=True)
class Quantity:
    name: str
    si_dim: Tuple[Fraction, ...]
    explicit_angle_dim: Optional[Tuple[Fraction, ...]] = None
    kind: str = "scalar"

    def dimension(self, angle_policy: str) -> Tuple[Fraction, ...]:
        if angle_policy == "explicit" and self.explicit_angle_dim is not None:
            return self.explicit_angle_dim
        return self.si_dim


def quantity_registry() -> Dict[str, Quantity]:
    """Return the immutable study registry.

    Under ``si``, plane angle has dimension one.  Under ``explicit``, A is a
    bookkeeping axis.  The latter is a GLM modelling convention, not SI.
    """
    E = D(L=2, M=1, T=-2)
    force = D(L=1, M=1, T=-2)
    power = D(L=2, M=1, T=-3)
    pressure = D(L=-1, M=1, T=-2)
    voltage = D(L=2, M=1, T=-3, I=-1)
    resistance = D(L=2, M=1, T=-3, I=-2)
    capacitance = D(L=-2, M=-1, T=4, I=2)
    inductance = D(L=2, M=1, T=-2, I=-2)
    q: Dict[str, Quantity] = {}

    def add(name: str, dim: Tuple[Fraction, ...], *, explicit=None,
            kind: str = "scalar") -> None:
        q[name] = Quantity(name, dim, explicit, kind)

    add("dimensionless", ZERO_DIM)
    add("length", D(L=1)); add("area", D(L=2)); add("volume", D(L=3))
    add("time", D(T=1)); add("mass", D(M=1)); add("temperature", D(Theta=1))
    add("amount", D(N=1)); add("current", D(I=1)); add("charge", D(T=1, I=1))
    add("frequency", D(T=-1)); add("velocity", D(L=1, T=-1), kind="vector")
    add("acceleration", D(L=1, T=-2), kind="vector")
    add("force", force, kind="vector"); add("momentum", D(L=1, M=1, T=-1), kind="vector")
    add("energy", E); add("work", E); add("power", power); add("pressure", pressure)
    add("density", D(L=-3, M=1)); add("volume_flow_rate", D(L=3, T=-1))
    add("dynamic_viscosity", D(L=-1, M=1, T=-1))
    add("voltage", voltage); add("resistance", resistance); add("impedance", resistance)
    add("reactance", resistance); add("conductance", tuple(-x for x in resistance))
    add("admittance", tuple(-x for x in resistance)); add("capacitance", capacitance)
    add("inductance", inductance); add("electric_field", D(L=1, M=1, T=-3, I=-1), kind="vector")
    add("magnetic_flux_density", D(M=1, T=-2, I=-1), kind="pseudovector")
    add("magnetic_flux", D(L=2, M=1, T=-2, I=-1))
    add("moment_of_inertia", D(L=2, M=1), explicit=D(L=2, M=1, A=-2))
    add("angle", ZERO_DIM, explicit=D(A=1))
    add("angular_velocity", D(T=-1), explicit=D(T=-1, A=1), kind="pseudovector")
    add("angular_acceleration", D(T=-2), explicit=D(T=-2, A=1), kind="pseudovector")
    add("torque", E, explicit=D(L=2, M=1, T=-2, A=-1), kind="pseudovector")
    add("angular_momentum", D(L=2, M=1, T=-1),
        explicit=D(L=2, M=1, T=-1, A=-1), kind="pseudovector")
    add("spring_constant", D(M=1, T=-2)); add("damping_coefficient", D(M=1, T=-1))
    add("acoustic_pressure", pressure); add("particle_velocity", D(L=1, T=-1), kind="vector")
    add("acoustic_impedance", D(L=-2, M=1, T=-1))
    # Acoustic intensity is power per area.
    add("acoustic_intensity", D(M=1, T=-3))
    add("wavelength", D(L=1)); add("wave_speed", D(L=1, T=-1))
    add("speed_of_light", D(L=1, T=-1)); add("planck_constant", D(L=2, M=1, T=-1))
    add("reduced_planck_constant", D(L=2, M=1, T=-1),
        explicit=D(L=2, M=1, T=-1, A=-1))
    add("boltzmann_constant", D(L=2, M=1, T=-2, Theta=-1))
    add("entropy", D(L=2, M=1, T=-2, Theta=-1))
    add("specific_heat_capacity", D(L=2, T=-2, Theta=-1))
    add("heat_capacity", D(L=2, M=1, T=-2, Theta=-1))
    add("thermal_conductivity", D(L=1, M=1, T=-3, Theta=-1))
    add("heat_flux", D(M=1, T=-3)); add("temperature_gradient", D(L=-1, Theta=1))
    add("stefan_boltzmann_constant", D(M=1, T=-3, Theta=-4))
    add("permittivity", D(L=-3, M=-1, T=4, I=2))
    add("coulomb_constant", D(L=3, M=1, T=-4, I=-2))
    return q


@dataclass(frozen=True)
class Monomial:
    coefficient: Fraction
    powers: Mapping[str, Fraction]

    def multiply(self, other: "Monomial") -> "Monomial":
        powers = dict(self.powers)
        for key, value in other.powers.items():
            powers[key] = powers.get(key, Fraction(0)) + value
            if powers[key] == 0:
                del powers[key]
        return Monomial(self.coefficient * other.coefficient, powers)

    def divide(self, other: "Monomial") -> "Monomial":
        if other.coefficient == 0:
            raise ZeroDivisionError("division by zero")
        return self.multiply(other.power(Fraction(-1)))

    def power(self, exponent: Fraction) -> "Monomial":
        if exponent.denominator != 1:
            raise ValueError("fractional expression powers are not supported")
        n = exponent.numerator
        return Monomial(self.coefficient ** n,
                        {key: value * n for key, value in self.powers.items()})


def parse_monomial(expression: str) -> Monomial:
    """Parse a safe monomial expression; addition and function calls fail."""
    # Formula-wheel notation writes powers with ``^``.  Normalize that to
    # Python exponentiation before constructing the restricted AST.
    tree = ast.parse(expression.replace("^", "**"), mode="eval")

    def visit(node: ast.AST) -> Monomial:
        if isinstance(node, ast.Name):
            return Monomial(Fraction(1), {node.id: Fraction(1)})
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return Monomial(Fraction(node.value), {})
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            value = visit(node.operand)
            return Monomial(-value.coefficient, value.powers)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return visit(node.left).multiply(visit(node.right))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return visit(node.left).divide(visit(node.right))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            base = visit(node.left)
            exponent = visit(node.right)
            if exponent.powers or exponent.coefficient.denominator != 1:
                raise ValueError("power must be an integer literal")
            return base.power(exponent.coefficient)
        raise ValueError(f"unsupported syntax: {ast.dump(node, include_attributes=False)}")

    result = visit(tree.body)
    if result.coefficient == 0:
        raise ValueError("zero is not a monomial quantity expression")
    return result


def parse_equation(equation: str) -> Tuple[Monomial, Monomial]:
    if equation.count("=") != 1:
        raise ValueError("equation must contain exactly one '='")
    lhs, rhs = (part.strip() for part in equation.split("=", 1))
    if not lhs or not rhs:
        raise ValueError("both sides of an equation are required")
    return parse_monomial(lhs), parse_monomial(rhs)


def expression_dimension(expr: Monomial, registry: Mapping[str, Quantity],
                         angle_policy: str) -> Tuple[Fraction, ...]:
    result = list(ZERO_DIM)
    unknown = sorted(set(expr.powers) - set(registry))
    if unknown:
        raise KeyError(f"unknown quantities: {', '.join(unknown)}")
    for name, exponent in expr.powers.items():
        for index, value in enumerate(registry[name].dimension(angle_policy)):
            result[index] += exponent * value
    return tuple(result)


def prime_factors(value: int) -> Dict[str, Fraction]:
    """Prime-exponent representation used to retain exact coefficients."""
    if value == 0:
        raise ValueError("zero has no multiplicative factorisation")
    factors: Dict[str, Fraction] = {}
    if value < 0:
        factors["coefficient_sign"] = Fraction(1)
        value = -value
    divisor = 2
    while divisor * divisor <= value:
        while value % divisor == 0:
            key = f"coefficient_prime_{divisor}"
            factors[key] = factors.get(key, Fraction(0)) + 1
            value //= divisor
        divisor += 1
    if value > 1:
        key = f"coefficient_prime_{value}"
        factors[key] = factors.get(key, Fraction(0)) + 1
    return factors


def equation_relation(equation: str) -> Dict[str, Fraction]:
    """Map lhs/rhs to an exact multiplicative relation vector."""
    lhs, rhs = parse_equation(equation)
    relation: Dict[str, Fraction] = dict(lhs.powers)
    for name, exponent in rhs.powers.items():
        relation[name] = relation.get(name, Fraction(0)) - exponent
    ratio = lhs.coefficient / rhs.coefficient
    numerator = prime_factors(ratio.numerator)
    denominator = prime_factors(ratio.denominator)
    # A negative sign has order two, not a rational-vector exponent.  Formula
    # wheels here use positive magnitudes; reject negative coefficient ratios.
    if "coefficient_sign" in numerator:
        relation["coefficient_sign"] = Fraction(1)
        del numerator["coefficient_sign"]
    for key, exponent in numerator.items():
        relation[key] = relation.get(key, Fraction(0)) + exponent
    for key, exponent in denominator.items():
        relation[key] = relation.get(key, Fraction(0)) - exponent
    return {key: value for key, value in relation.items() if value}


def matrix_rank(rows: Sequence[Sequence[Fraction]]) -> int:
    matrix = [list(row) for row in rows if any(row)]
    if not matrix:
        return 0
    nrows, ncols = len(matrix), len(matrix[0])
    rank = 0
    for column in range(ncols):
        pivot = next((r for r in range(rank, nrows) if matrix[r][column]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        pivot_value = matrix[rank][column]
        matrix[rank] = [value / pivot_value for value in matrix[rank]]
        for row in range(nrows):
            if row != rank and matrix[row][column]:
                factor = matrix[row][column]
                matrix[row] = [a - factor * b
                               for a, b in zip(matrix[row], matrix[rank])]
        rank += 1
        if rank == nrows:
            break
    return rank


def is_derivable(target: str, axioms: Sequence[str]) -> bool:
    """Test exact multiplicative derivability by rational row-span."""
    axiom_relations = [equation_relation(axiom) for axiom in axioms]
    target_relation = equation_relation(target)
    columns = sorted({key for row in axiom_relations + [target_relation]
                      for key in row})
    rows = [[row.get(column, Fraction(0)) for column in columns]
            for row in axiom_relations]
    target_row = [target_relation.get(column, Fraction(0)) for column in columns]
    return matrix_rank(rows) == matrix_rank(rows + [target_row])


@dataclass(frozen=True)
class FormulaCase:
    id: str
    equation: str
    expected_dimensional: bool
    expected_derivable: bool
    physical_status: PhysicalStatus
    assumptions: Tuple[str, ...]
    source: str
    note: str = ""
    expected_dimensional_explicit: Optional[bool] = None


@dataclass(frozen=True)
class Wheel:
    id: str
    title: str
    axioms: Tuple[str, ...]
    cases: Tuple[FormulaCase, ...]


def C(case_id: str, equation: str, dim: bool, derivable: bool,
      status: PhysicalStatus, assumptions: Sequence[str], source: str,
      note: str = "", explicit_dim: Optional[bool] = None) -> FormulaCase:
    return FormulaCase(case_id, equation, dim, derivable, status,
                       tuple(assumptions), source, note, explicit_dim)


OPENSTAX = "https://openstax.org/details/books/university-physics-volume-1"
OPENSTAX_2 = "https://openstax.org/details/books/university-physics-volume-2"
BIPM = "https://doi.org/10.59161/AUEZ1291"


def study_wheels() -> Tuple[Wheel, ...]:
    """Ten preregistered domains with positive and negative controls."""
    S, U, N, M = (PhysicalStatus.SUPPORTED, PhysicalStatus.UNDERSPECIFIED,
                  PhysicalStatus.NEGATIVE_CONTROL, PhysicalStatus.MODEL_CONVENTION)
    return (
        Wheel("W1", "DC Ohm and power", (
            "voltage = current * resistance", "power = voltage * current"), (
            C("W1-01", "resistance = voltage / current", True, True, S,
              ("DC", "ohmic element", "current != 0"), OPENSTAX_2),
            C("W1-02", "power = current^2 * resistance", True, True, S,
              ("DC", "ohmic resistor"), OPENSTAX_2),
            C("W1-03", "power = voltage^2 / resistance", True, True, S,
              ("DC", "ohmic resistor", "resistance != 0"), OPENSTAX_2),
            C("W1-N1", "power = voltage * resistance", False, False, N,
              ("negative control",), OPENSTAX_2))),
        Wheel("W2", "Sinusoidal AC impedance and power", (
            "voltage = current * impedance", "power = voltage * current"), (
            C("W2-01", "impedance = voltage / current", True, True, S,
              ("phasor magnitudes or complex phasors", "current != 0"), OPENSTAX_2),
            C("W2-02", "reactance = inductance * angular_velocity", True, False, S,
              ("ideal inductor", "sinusoidal steady state"), OPENSTAX_2,
              "Requires an inductor-reactance axiom. An independent angle "
              "axis makes omega*L dimensionally incompatible unless the "
              "quantity model supplies a compensating angle convention.", False),
            C("W2-03", "power = voltage * current", True, True, U,
              ("must specify RMS/phasor convention and phase"), OPENSTAX_2,
              "Dimensions cannot distinguish P, Q, S, or complex conjugation."),
            C("W2-N1", "impedance = voltage * current", False, False, N,
              ("negative control",), OPENSTAX_2))),
        Wheel("W3", "Electrostatics and capacitors", (
            "charge = capacitance * voltage", "energy = 1/2 * capacitance * voltage^2"), (
            C("W3-01", "capacitance = charge / voltage", True, True, S,
              ("voltage != 0",), OPENSTAX_2),
            C("W3-02", "energy = 1/2 * charge * voltage", True, True, S,
              ("linear capacitor",), OPENSTAX_2),
            C("W3-03", "energy = 1/2 * charge^2 / capacitance", True, True, S,
              ("linear capacitor", "capacitance != 0"), OPENSTAX_2),
            C("W3-N1", "energy = charge * capacitance", False, False, N,
              ("negative control",), OPENSTAX_2))),
        Wheel("W4", "Rotational mechanics", (
            "torque = moment_of_inertia * angular_acceleration",
            "power = torque * angular_velocity",
            "angular_momentum = moment_of_inertia * angular_velocity"), (
            C("W4-01", "angular_acceleration = torque / moment_of_inertia", True, True, S,
              ("rigid body about a fixed principal axis", "moment_of_inertia != 0"), OPENSTAX),
            C("W4-02", "power = torque * angular_velocity", True, True, S,
              ("collinear scalar magnitudes; otherwise dot product"), OPENSTAX),
            C("W4-03", "angular_momentum = moment_of_inertia * angular_velocity", True, True, S,
              ("rotation about a principal axis; otherwise tensor relation"), OPENSTAX),
            C("W4-N1", "torque = moment_of_inertia * angular_velocity", False, False, N,
              ("negative control",), OPENSTAX),
            C("W4-M1", "angular_velocity = frequency", True, False, M,
              ("SI dimensions only",), BIPM,
              "Dimensionally equal under SI but numerically omega = 2*pi*f.", False))),
        Wheel("W5", "Linear dynamics and work-energy", (
            "force = mass * acceleration", "momentum = mass * velocity",
            "power = force * velocity", "energy = 1/2 * mass * velocity^2"), (
            C("W5-01", "acceleration = force / mass", True, True, S,
              ("constant nonzero mass", "net force",), OPENSTAX),
            C("W5-02", "momentum = mass * velocity", True, True, S,
              ("nonrelativistic mechanics",), OPENSTAX),
            C("W5-03", "energy = 1/2 * mass * velocity^2", True, True, S,
              ("translational nonrelativistic kinetic energy",), OPENSTAX),
            C("W5-N1", "force = mass * velocity", False, False, N,
              ("negative control",), OPENSTAX))),
        Wheel("W6", "Fluid statics and flow", (
            "pressure = force / area", "volume_flow_rate = area * velocity",
            "force = pressure * area"), (
            C("W6-01", "force = pressure * area", True, True, S,
              ("uniform normal pressure", "planar area"), OPENSTAX),
            C("W6-02", "velocity = volume_flow_rate / area", True, True, S,
              ("mean speed", "steady incompressible flow", "area != 0"), OPENSTAX),
            C("W6-03", "power = pressure * volume_flow_rate", True, False, S,
              ("hydraulic power without losses"), OPENSTAX,
              "Requires a hydraulic-power axiom."),
            C("W6-N1", "pressure = force * area", False, False, N,
              ("negative control",), OPENSTAX))),
        Wheel("W7", "Linear plane-wave acoustics", (
            "acoustic_pressure = acoustic_impedance * particle_velocity",
            "acoustic_intensity = acoustic_pressure * particle_velocity"), (
            C("W7-01", "acoustic_impedance = acoustic_pressure / particle_velocity", True, True, S,
              ("progressive plane wave", "particle_velocity != 0"), OPENSTAX),
            C("W7-02", "acoustic_intensity = acoustic_pressure * particle_velocity", True, True, U,
              ("instantaneous intensity; vectors require a dot product"), OPENSTAX,
              "Time-averaged harmonic intensity also requires phase/averaging."),
            C("W7-03", "acoustic_intensity = acoustic_pressure^2 / acoustic_impedance", True, True, S,
              ("progressive plane wave", "real characteristic impedance"), OPENSTAX),
            C("W7-N1", "acoustic_intensity = acoustic_pressure^2 / particle_velocity", False, False, N,
              ("negative control",), OPENSTAX))),
        Wheel("W8", "Thermal physics and heat transfer", (
            "energy = mass * specific_heat_capacity * temperature",
            "entropy = energy / temperature",
            "heat_flux = thermal_conductivity * temperature_gradient"), (
            C("W8-01", "specific_heat_capacity = energy / (mass * temperature)", True, True, S,
              ("temperature denotes a temperature change", "constant heat capacity"), OPENSTAX_2),
            C("W8-02", "entropy = energy / temperature", True, True, U,
              ("reversible heat transfer if interpreted as dS = deltaQ_rev/T",), OPENSTAX_2,
              "Dimensional form alone is not a general finite entropy law."),
            C("W8-03", "heat_flux = thermal_conductivity * temperature_gradient", True, True, U,
              ("Fourier conduction",), OPENSTAX_2,
              "The vector law contains a minus sign."),
            C("W8-N1", "power = stefan_boltzmann_constant * temperature^4", False, False, N,
              ("negative control: emitting area is absent",), OPENSTAX_2))),
        Wheel("W9", "Wave kinematics", (
            "wave_speed = frequency * wavelength",
            "angular_velocity = angle * frequency"), (
            C("W9-01", "frequency = wave_speed / wavelength", True, True, S,
              ("nondispersive phase relation", "wavelength != 0"), OPENSTAX),
            C("W9-02", "wavelength = wave_speed / frequency", True, True, S,
              ("nondispersive phase relation", "frequency != 0"), OPENSTAX),
            C("W9-03", "angular_velocity = angle * frequency", True, True, M,
              ("angle represents a dimensionless full-cycle factor under SI",), BIPM,
              "A numerical 2*pi factor is required for omega = 2*pi*f."),
            C("W9-N1", "wave_speed = frequency / wavelength", False, False, N,
              ("negative control",), OPENSTAX))),
        Wheel("W10", "Photon energy and momentum", (
            "energy = planck_constant * frequency",
            "energy = speed_of_light * momentum"), (
            C("W10-01", "frequency = energy / planck_constant", True, True, S,
              ("photon", "planck_constant != 0"), OPENSTAX_2),
            C("W10-02", "momentum = energy / speed_of_light", True, True, S,
              ("photon in vacuum",), OPENSTAX_2),
            C("W10-03", "momentum = planck_constant / wavelength", True, False, S,
              ("photon or de Broglie relation",), OPENSTAX_2,
              "Requires wave_speed = frequency*wavelength and wave_speed = c."),
            C("W10-N1", "energy = planck_constant / frequency", False, False, N,
              ("negative control",), OPENSTAX_2))),
    )


@dataclass(frozen=True)
class CaseResult:
    wheel_id: str
    case_id: str
    equation: str
    parse_grounding: str
    dimensional_outcome: str
    dimensional_observed: Optional[bool]
    dimensional_expected: bool
    dimensional_correct: bool
    derivation_outcome: str
    derivable_observed: Optional[bool]
    derivable_expected: bool
    derivation_correct: bool
    physical_status: str
    assumptions: Tuple[str, ...]
    source: str
    note: str
    lhs_dimension: str
    rhs_dimension: str
    error: Optional[str] = None


def format_dimension(vector: Tuple[Fraction, ...]) -> str:
    parts = []
    for axis, exponent in zip(BASE_AXES, vector):
        if exponent:
            shown = str(exponent.numerator) if exponent.denominator == 1 else str(exponent)
            parts.append(axis if exponent == 1 else f"{axis}^{shown}")
    return "1" if not parts else " ".join(parts)


def evaluate_case(wheel: Wheel, case: FormulaCase,
                  registry: Mapping[str, Quantity], angle_policy: str) -> CaseResult:
    try:
        lhs, rhs = parse_equation(case.equation)
        lhs_dim = expression_dimension(lhs, registry, angle_policy)
        rhs_dim = expression_dimension(rhs, registry, angle_policy)
        dimensional = lhs_dim == rhs_dim
        expected_dimensional = (
            case.expected_dimensional_explicit
            if angle_policy == "explicit" and
            case.expected_dimensional_explicit is not None
            else case.expected_dimensional)
        derivable = is_derivable(case.equation, wheel.axioms)
        return CaseResult(
            wheel.id, case.id, case.equation, "grounded",
            (Outcome.DIMENSIONALLY_CONSISTENT.value if dimensional else
             Outcome.DIMENSIONALLY_INCONSISTENT.value),
            dimensional, expected_dimensional,
            dimensional == expected_dimensional,
            (Outcome.ALGEBRAICALLY_DERIVED.value if derivable else
             Outcome.NOT_ALGEBRAICALLY_DERIVED.value),
            derivable, case.expected_derivable,
            derivable == case.expected_derivable,
            case.physical_status.value, case.assumptions, case.source, case.note,
            format_dimension(lhs_dim), format_dimension(rhs_dim))
    except (SyntaxError, ValueError, KeyError, ZeroDivisionError) as error:
        expected_dimensional = (
            case.expected_dimensional_explicit
            if angle_policy == "explicit" and
            case.expected_dimensional_explicit is not None
            else case.expected_dimensional)
        return CaseResult(
            wheel.id, case.id, case.equation, Outcome.UNRESOLVED.value,
            Outcome.EXECUTION_ERROR.value, None, expected_dimensional, False,
            Outcome.EXECUTION_ERROR.value, None, case.expected_derivable, False,
            case.physical_status.value, case.assumptions, case.source, case.note,
            "?", "?", f"{type(error).__name__}: {error}")


def protocol_hash(wheels: Sequence[Wheel]) -> str:
    encoded = json.dumps([asdict(wheel) for wheel in wheels], sort_keys=True,
                         separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_study(angle_policy: str) -> Tuple[Tuple[Wheel, ...], List[CaseResult]]:
    wheels = study_wheels()
    registry = quantity_registry()
    results = [evaluate_case(wheel, case, registry, angle_policy)
               for wheel in wheels for case in wheel.cases]
    return wheels, results


def result_document(wheels: Sequence[Wheel], results: Sequence[CaseResult],
                    angle_policy: str) -> Dict[str, object]:
    dim_correct = sum(result.dimensional_correct for result in results)
    deriv_correct = sum(result.derivation_correct for result in results)
    errors = sum(result.error is not None for result in results)
    return {
        "schema": "glm.formula-wheel-study.v2",
        "version": VERSION,
        "angle_policy": angle_policy,
        "angle_policy_note": (
            "SI: plane angle has dimension one" if angle_policy == "si" else
            "Exploratory GLM convention: plane angle uses independent axis A"),
        "protocol_sha256": protocol_hash(wheels),
        "wheel_count": len(wheels),
        "case_count": len(results),
        "score": {
            "dimensional_expected_outcome_accuracy": [dim_correct, len(results)],
            "derivation_expected_outcome_accuracy": [deriv_correct, len(results)],
            "execution_errors": errors,
        },
        "interpretation": (
            "Dimensional and derivation results do not independently verify "
            "physical truth. See physical_status, assumptions, source, and note."),
        "results": [asdict(result) for result in results],
    }


def print_report(wheels: Sequence[Wheel], results: Sequence[CaseResult],
                 angle_policy: str, verbose: bool) -> None:
    print("GLM FORMULA-WHEEL STUDY v2")
    print("=" * 72)
    print(f"Angle policy: {angle_policy}")
    print(f"Protocol SHA-256: {protocol_hash(wheels)}")
    print(f"Wheels: {len(wheels)} | Preregistered cases: {len(results)}")
    print()
    by_wheel = {wheel.id: [r for r in results if r.wheel_id == wheel.id]
                for wheel in wheels}
    for wheel in wheels:
        group = by_wheel[wheel.id]
        dim_score = sum(r.dimensional_correct for r in group)
        drv_score = sum(r.derivation_correct for r in group)
        print(f"{wheel.id} — {wheel.title}: dimensional {dim_score}/{len(group)}, "
              f"derivation {drv_score}/{len(group)}")
        if verbose:
            for result in group:
                mark = "PASS" if result.dimensional_correct and result.derivation_correct else "FAIL"
                print(f"  [{mark}] {result.case_id}: {result.equation}")
                print(f"         dimension={result.dimensional_outcome} "
                      f"({result.lhs_dimension} vs {result.rhs_dimension}); "
                      f"derivation={result.derivation_outcome}")
                print(f"         physical={result.physical_status}")
                if result.error:
                    print(f"         error={result.error}")
                if result.note:
                    print(f"         note={result.note}")
    print()
    print("SCORECARD (accuracy against preregistered expected outcomes)")
    print("-" * 72)
    print(f"Dimensional outcomes: {sum(r.dimensional_correct for r in results)}/{len(results)}")
    print(f"Algebraic derivability: {sum(r.derivation_correct for r in results)}/{len(results)}")
    print(f"Execution errors: {sum(r.error is not None for r in results)}")
    print()
    print("Interpretation: a dimensionally consistent or algebraically derived")
    print("expression is not thereby a verified physical law.")


def self_test() -> None:
    registry = quantity_registry()
    assert len(study_wheels()) == 10
    assert parse_monomial("1/2 * mass * velocity^2").coefficient == Fraction(1, 2)
    assert is_derivable("power = current^2 * resistance", (
        "voltage = current * resistance", "power = voltage * current"))
    assert is_derivable("energy = 1/2 * charge^2 / capacitance", (
        "charge = capacitance * voltage", "energy = 1/2 * capacitance * voltage^2"))
    assert not is_derivable("power = torque^2 / angular_acceleration", (
        "torque = moment_of_inertia * angular_acceleration",
        "power = torque * angular_velocity"))
    lhs, rhs = parse_equation("power = voltage * current")
    assert expression_dimension(lhs, registry, "si") == expression_dimension(rhs, registry, "si")
    _, results_si = run_study("si")
    assert not [result for result in results_si if result.error]
    assert all(result.dimensional_correct for result in results_si)
    assert all(result.derivation_correct for result in results_si)
    _, results_explicit = run_study("explicit")
    assert not [result for result in results_explicit if result.error]
    print("Self-test passed")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--angle-policy", choices=("si", "explicit"), default="si",
                        help="SI dimension-one angle or exploratory explicit A axis")
    parser.add_argument("--json-out", type=Path,
                        help="write the complete machine-readable evidence document")
    parser.add_argument("--verbose", action="store_true", help="print every case")
    parser.add_argument("--strict", action="store_true",
                        help="exit nonzero on an expectation mismatch or execution error")
    parser.add_argument("--self-test", action="store_true", help="run invariant tests and exit")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    wheels, results = run_study(args.angle_policy)
    print_report(wheels, results, args.angle_policy, args.verbose)
    document = result_document(wheels, results, args.angle_policy)
    if args.json_out:
        args.json_out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        print(f"Results written to: {args.json_out}")
    failed = any(result.error or not result.dimensional_correct or
                 not result.derivation_correct for result in results)
    return 1 if args.strict and failed else 0


if __name__ == "__main__":
    sys.exit(main())
