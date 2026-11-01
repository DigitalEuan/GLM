"""``glm_universal.wheels.cent_wheels`` -- the formula wheels absorbed from the
supplied ``cent_compiler_v12``, and the rational-power engine that reads them.

*Created 31 October 2026 (intake of ``source_material/ToDo/cent_compiler_v12``,
directive D22; ``studies/CENT_WHEELS_STUDY.md``).*
*PROVISIONAL (31 October 2026, the owner's decision): installed in the wheels
folder ahead of the Lean build; the item stays in ``source_material/ToDo/``
at Lean written until ``scripts/rebuild_lean.sh`` confirms
``Wheels/CentWheels.lean``, and :func:`glm_universal.wheels.answer_derivability`
says so when a cent wheel answers (``glm_universal.wheels.provisional_status``).*

The engine
----------
The same reading as :mod:`glm_universal.engineering.wheels`: an equation is
its *relation vector* (the exponent of every quantity, left minus right, and
the prime exponents of the coefficient ratio, under keys ``#p``), and a formula
*follows from* a wheel exactly when that vector lies in the rational span of
the axioms' vectors.  The one difference: exponents are rational, so a
fractional power ``(...)^(1/2)`` is read (it multiplies every exponent inside
it, the coefficient's primes included) where the integer engine refuses it
("a power must be an integer literal").  On every equation the integer engine
reads, this engine gives the same vector and the same verdict (the study's
mark E1, checked in ``tests/test_cent_wheels.py``).  A derivation comes with a
*certificate* (the rational weights of the axioms) and a refusal with a
*separating functional* (an integer vector orthogonal to every axiom and not
to the formula) -- the two certificates ``Wheels/CentWheels.lean`` checks.

Dimensions are read from each wheel's own table over the eight axes
``L M T I H N J A`` (rational exponents).  The angle convention is the
repository's: **SI7 decides** (the first seven axes; angle dimensionless, as
D4 of ``DOMAIN_WHEELS_STUDY.md`` and ``expected_dimensional`` of
``engineering/wheels.py``), and the residual on ``A`` is recorded.

Exact throughout (directive D7): ``int`` and ``Fraction``, never a float.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "AXES", "SI7_AXES", "parse_monomial_q", "relation_vector_q",
    "certificate", "separating_functional", "is_derivable_q", "residual",
    "balanced_si7", "columns",
]

#: The eight axes of every cent dimension table (the repository's reference
#: axes: SI7 plus an explicit plane angle).
AXES: Tuple[str, ...] = ("L", "M", "T", "I", "H", "N", "J", "A")
#: The number of axes that decide dimensional soundness (angle dimensionless).
SI7_AXES = 7

Vector = Dict[str, Fraction]


# ===========================================================================
# 1.  RELATION VECTORS WITH RATIONAL EXPONENTS
# ===========================================================================

def _prime_exponents(n: int) -> Vector:
    out: Vector = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[f"#{d}"] = out.get(f"#{d}", Fraction(0)) + 1
            n //= d
        d += 1
    if n > 1:
        out[f"#{n}"] = out.get(f"#{n}", Fraction(0)) + 1
    return out


def _rational(node: ast.AST) -> Fraction:
    """A rational literal exponent: integers, unary minus, ``/`` and ``*``."""
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        return Fraction(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_rational(node.operand)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        den = _rational(node.right)
        if den == 0:
            raise ValueError("a zero denominator in an exponent")
        return _rational(node.left) / den
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return _rational(node.left) * _rational(node.right)
    raise ValueError("a power must be a rational literal")


def _add(a: Vector, b: Vector, scale: Fraction = Fraction(1)) -> Vector:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, Fraction(0)) + scale * v
    return {k: v for k, v in out.items() if v}


def parse_monomial_q(text: str) -> Tuple[int, Vector]:
    """``(sign, exponents)`` of a monomial: names, nonzero integer literals,
    ``*``, ``/``, unary minus and rational literal powers written ``^`` or
    ``**``.  The coefficient is carried as prime exponents (``#p``), so a
    root of a number stays exact.  Anything else raises ``ValueError``."""
    try:
        tree = ast.parse(text.replace("^", "**").strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"not a monomial: {text!r}") from exc

    def visit(node: ast.AST) -> Tuple[int, Vector]:
        if isinstance(node, ast.Name):
            return 1, {node.id: Fraction(1)}
        if (isinstance(node, ast.Constant) and isinstance(node.value, int)
                and not isinstance(node.value, bool)):
            if node.value == 0:
                raise ValueError("zero is not a quantity expression")
            return (1 if node.value > 0 else -1), _prime_exponents(abs(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            s, e = visit(node.operand)
            return -s, e
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            (s1, e1), (s2, e2) = visit(node.left), visit(node.right)
            return s1 * s2, _add(e1, e2)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            (s1, e1), (s2, e2) = visit(node.left), visit(node.right)
            return s1 * s2, _add(e1, e2, Fraction(-1))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            r = _rational(node.right)
            s, e = visit(node.left)
            if r.denominator != 1 and s < 0:
                raise ValueError("a fractional power of a negative number")
            sign = s ** abs(r.numerator) if r.denominator == 1 else 1
            return sign, {k: v * r for k, v in e.items() if v * r}
        raise ValueError(f"unsupported syntax in {text!r}")

    return visit(tree.body)


def relation_vector_q(text: str) -> Vector:
    """The relation vector of ``L = R`` with rational exponents.  A negative
    coefficient ratio is refused, as in ``engineering.wheels.relation_vector``:
    the wheels relate positive magnitudes."""
    if text.count("=") != 1:
        raise ValueError("an equation needs exactly one '='")
    lhs, rhs = (part.strip() for part in text.split("="))
    if not lhs or not rhs:
        raise ValueError("both sides of an equation are required")
    (sl, el), (sr, er) = parse_monomial_q(lhs), parse_monomial_q(rhs)
    if sl * sr < 0:
        raise ValueError("a negative coefficient ratio is not a magnitude relation")
    return _add(el, er, Fraction(-1))


# ===========================================================================
# 2.  EXACT SPAN MEMBERSHIP, WITH BOTH CERTIFICATES
# ===========================================================================

def columns(*vectors: Mapping[str, Fraction]) -> Tuple[str, ...]:
    """The coordinates of a set of relation vectors: quantity names first
    (sorted), then the primes (in increasing order)."""
    keys = {k for v in vectors for k in v}
    names = sorted(k for k in keys if not k.startswith("#"))
    primes = sorted((k for k in keys if k.startswith("#")), key=lambda k: int(k[1:]))
    return tuple(names) + tuple(primes)


def _rref(rows: List[List[Fraction]], ncols: int) -> Tuple[List[List[Fraction]], List[int]]:
    rows = [list(r) for r in rows]
    pivots: List[int] = []
    r = 0
    for c in range(ncols):
        p = next((i for i in range(r, len(rows)) if rows[i][c]), None)
        if p is None:
            continue
        rows[r], rows[p] = rows[p], rows[r]
        pv = rows[r][c]
        rows[r] = [x / pv for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c]:
                f = rows[i][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
        if r == len(rows):
            break
    return rows, pivots


def certificate(target: str, axioms: Sequence[str]) -> Optional[Tuple[Fraction, ...]]:
    """Rational weights ``x`` with ``sum x_i * axiom_i == target`` as relation
    vectors (one solution, free weights 0), or ``None`` when ``target`` does
    not follow from ``axioms``."""
    rels = [relation_vector_q(a) for a in axioms]
    goal = relation_vector_q(target)
    cols = columns(goal, *rels)
    n = len(rels)
    aug = [[rels[i].get(c, Fraction(0)) for i in range(n)] + [goal.get(c, Fraction(0))]
           for c in cols]
    red, pivots = _rref(aug, n)
    if any(all(x == 0 for x in row[:n]) and row[n] for row in red):
        return None
    x = [Fraction(0)] * n
    for i, c in enumerate(pivots):
        x[c] = red[i][n]
    return tuple(x)


def _lcm(a: int, b: int) -> int:
    from math import gcd
    return a * b // gcd(a, b)


def _integral(vec: Sequence[Fraction]) -> Tuple[int, ...]:
    from math import gcd
    d = 1
    for x in vec:
        d = _lcm(d, x.denominator)
    ints = [int(x * d) for x in vec]
    g = 0
    for x in ints:
        g = gcd(g, abs(x))
    g = g or 1
    first = next((x for x in ints if x), 1)
    sign = 1 if first > 0 else -1
    return tuple(sign * x // g for x in ints)


def separating_functional(target: str, axioms: Sequence[str]) -> Optional[Dict[str, int]]:
    """An integer vector ``w`` (over the coordinates of ``target`` and the
    axioms) with ``w . axiom_i == 0`` for every axiom and ``w . target != 0``
    -- the certificate that ``target`` does not follow -- or ``None`` when it
    does.  Of the null-space basis vectors that separate, the one with the
    fewest nonzero entries (then the smallest entries) is returned."""
    rels = [relation_vector_q(a) for a in axioms]
    goal = relation_vector_q(target)
    cols = columns(goal, *rels)
    n = len(cols)
    mat = [[r.get(c, Fraction(0)) for c in cols] for r in rels]
    red, pivots = _rref(mat, n) if mat else ([], [])
    best: Optional[Tuple[int, ...]] = None
    for f in (c for c in range(n) if c not in pivots):
        v = [Fraction(0)] * n
        v[f] = Fraction(1)
        for i, c in enumerate(pivots):
            v[c] = -red[i][f]
        if sum(v[j] * goal.get(cols[j], Fraction(0)) for j in range(n)) == 0:
            continue
        w = _integral(v)
        key = (sum(1 for x in w if x), max(abs(x) for x in w))
        if best is None or key < (sum(1 for x in best if x), max(abs(x) for x in best)):
            best = w
    if best is None:
        return None
    return {c: x for c, x in zip(cols, best) if x}


def is_derivable_q(target: str, axioms: Sequence[str]) -> bool:
    """Does ``target`` follow from ``axioms`` (rational span membership)?"""
    return certificate(target, axioms) is not None


# ===========================================================================
# 3.  DIMENSIONS FROM A WHEEL'S OWN TABLE
# ===========================================================================

def residual(text: str, table: Mapping[str, Sequence[Fraction]]
             ) -> Optional[Tuple[Fraction, ...]]:
    """The eight-axis residual (left minus right) of ``text`` on ``table``,
    or ``None`` when a quantity it names has no entry (prime coordinates are
    dimensionless)."""
    total = [Fraction(0)] * len(AXES)
    for k, e in relation_vector_q(text).items():
        if k.startswith("#"):
            continue
        if k not in table:
            return None
        for i, x in enumerate(table[k]):
            total[i] += e * Fraction(x)
    return tuple(total)


def balanced_si7(text: str, table: Mapping[str, Sequence[Fraction]]) -> Optional[bool]:
    """Is ``text`` dimensionally balanced at SI7 on ``table`` (``None`` when
    the table does not hold every quantity)?"""
    r = residual(text, table)
    return None if r is None else all(x == 0 for x in r[:SI7_AXES])


# ===========================================================================
# 4.  THE ABSORBED WHEELS (the sound ones among W16-W35, after rule R)
# ===========================================================================
#
# Transcribed from the supplied ``wheels/W16.json`` ... ``W34.json`` of
# ``cent_compiler_v12`` (31 October 2026); held here as Python literals so the
# package never reads ``source_material/`` at run time (D20).  Every axiom,
# case and table entry is the supplied one except where :data:`CORRECTIONS`
# records a correction under the study's rule R, or :data:`DROPPED` a drop;
# ``tests/test_cent_wheels.py`` checks that against the supplied files.

from ..engineering.wheels import FormulaCase, Wheel  # noqa: E402

SUPPORTED = "physically_supported"
UNDERSPECIFIED = "physically_underspecified"
CONVENTION = "model_convention"
NEGATIVE = "negative_control"


def _c(cid: str, eq: str, dim: bool, der: bool, status: str,
       explicit: Optional[bool] = None, note: str = "") -> FormulaCase:
    return FormulaCase(cid, eq, dim, der, status, explicit, note)


def _d(**p) -> Tuple[Fraction, ...]:
    return tuple(Fraction(p.get(a, 0)) for a in AXES)


_SETTLED = "settled 31 October 2026 (CENT_WHEELS_STUDY §8): "
_CORRECTED = "corrected 31 October 2026 under rule R (CENT_WHEELS_STUDY §8): "


@dataclass(frozen=True)
class Correction:
    """One change from the supplied wheel: ``what`` is ``axiom``, ``table``,
    ``case`` or ``flag``; ``rule`` the clause of rule R (``a``-``d``) or
    ``span``/``table`` for a flag settled by span membership or by the
    table's dimension verdict."""

    wheel: str
    what: str
    item: str
    supplied: str
    absorbed: str
    rule: str
    reason: str


@dataclass(frozen=True)
class Dropped:
    """A supplied axiom that rule R cannot correct without guessing."""

    wheel: str
    supplied: str
    reason: str


#: The absorbed wheels: W16-W25, W28, W29, W32-W34 (W26, W27, W30, W31 were
#: never supplied; W35 lost both axioms to rule R and is not absorbed).
CENT_WHEELS: Tuple[Wheel, ...] = (
    Wheel("W16", "Magnetic flux and induction", (
        "flux = magnetic_field * area",
        "flux = inductance * current",
        "emf = flux / time",
    ), (
        _c("W16-01", "magnetic_field = flux / area", True, True, SUPPORTED),
        _c("W16-02", "inductance = flux / current", True, True, SUPPORTED),
        _c("W16-03", "emf = flux / time", True, True, SUPPORTED, None,
           note="Faraday's law magnitude; full law has a sign and a derivative"),
        _c("W16-N1", "flux = magnetic_field / area", False, False, NEGATIVE),
    )),
    Wheel("W17", "Gravitation and orbital mechanics", (
        "surface_gravity = gravitational_constant * source_mass / distance^2",
        "period^2 = distance^3 / (gravitational_constant * source_mass)",
    ), (
        _c("W17-01", "gravitational_constant = surface_gravity * distance^2 / source_mass",
           True, True, SUPPORTED),
        _c("W17-02", "source_mass = surface_gravity * distance^2 / gravitational_constant",
           True, True, SUPPORTED),
        _c("W17-03", "period^2 = distance^3 / (gravitational_constant * source_mass)",
           True, True, CONVENTION, True,
           note="Kepler third law; convention drops the 4π² factor (radial convention). "
                + _SETTLED + "expected_dimensional_explicit True (supplied False): no "
                "quantity of W17 carries the angle axis"),
        _c("W17-N1", "surface_gravity = distance^2 / (gravitational_constant * source_mass)",
           False, False, NEGATIVE),
    )),
    Wheel("W18", "Ideal gas law", (
        "pressure * volume = amount * gas_constant * temperature",
    ), (
        _c("W18-01", "volume = amount * gas_constant * temperature / pressure", True, True, SUPPORTED),
        _c("W18-02", "temperature = pressure * volume / (amount * gas_constant)", True, True, SUPPORTED),
        _c("W18-03", "amount = pressure * volume / (gas_constant * temperature)", True, True, SUPPORTED),
        _c("W18-N1", "pressure = amount * gas_constant * temperature * volume", False, False, NEGATIVE),
    )),
    Wheel("W19", "Electromagnetic waves", (
        "speed_of_light^2 = 1 / (permittivity * permeability)",
        "electric_field = speed_of_light * magnetic_field",
    ), (
        _c("W19-01", "permittivity * permeability = 1 / speed_of_light^2", True, True, SUPPORTED),
        _c("W19-02", "magnetic_field = electric_field / speed_of_light", True, True, SUPPORTED),
        _c("W19-03", "permittivity = 1 / (permeability * speed_of_light^2)", True, True, SUPPORTED),
        _c("W19-N1", "speed_of_light = permittivity * permeability", False, False, NEGATIVE),
    )),
    Wheel("W20", "Elasticity & Continuum Mechanics", (
        "stress = youngs_modulus * strain",
        "bending_moment = youngs_modulus * area_moment_inertia / radius_curvature",
        "flexural_rigidity = youngs_modulus * area_moment_inertia",
    ), (
        _c("W20-01", "youngs_modulus = stress / strain", True, True, SUPPORTED),
        _c("W20-02", "strain = stress / youngs_modulus", True, True, SUPPORTED),
        _c("W20-03", "radius_curvature = youngs_modulus * area_moment_inertia / bending_moment",
           True, True, SUPPORTED),
        _c("W20-N1", "stress = youngs_modulus / strain", True, False, NEGATIVE, None,
           note=_SETTLED + "expected_dimensional True (supplied False): strain is "
                "dimensionless, so this control is refused by derivability, not by dimension"),
    )),
    Wheel("W21", "Fracture Mechanics & Plasticity", (
        "fracture_toughness = (2 * youngs_modulus * surface_energy / crack_length)^(1/2)",
        "stress_intensity_factor = dimensionless_factor * stress * crack_length^(1/2)",
    ), (
        _c("W21-01", "surface_energy = fracture_toughness^2 * crack_length / (2 * youngs_modulus)",
           True, True, SUPPORTED),
        _c("W21-02", "crack_length = (stress_intensity_factor / (dimensionless_factor * stress))^2",
           True, True, SUPPORTED),
        _c("W21-03", "stress = stress_intensity_factor / (dimensionless_factor * crack_length^(1/2))",
           True, True, SUPPORTED),
        _c("W21-N1", "fracture_toughness = stress / crack_length", False, False, NEGATIVE),
    )),
    Wheel("W22", "Chemical Kinetics & Transport", (
        "reaction_rate = rate_constant * concentration",
    ), (
        _c("W22-01", "rate_constant = reaction_rate / concentration", True, True, SUPPORTED),
        _c("W22-02", "concentration = reaction_rate / rate_constant", True, True, SUPPORTED),
        _c("W22-03", "diffusion_coefficient = diffusion_flux / concentration_gradient",
           True, False, SUPPORTED, None,
           note=_SETTLED + "expected_derivable False (supplied True): Fick's first law is a "
                "law, but none of its three quantities is in a W22 axiom (or table), so the "
                "wheel cannot derive it; its dimension is not checkable on the table"),
        _c("W22-N1", "reaction_rate = rate_constant / concentration", False, False, NEGATIVE),
    )),
    Wheel("W23", "Electrochemistry & Energy Storage", (
        "mass = charge * molar_mass / faraday_constant",
        "charge = current * time",
    ), (
        _c("W23-01", "molar_mass = mass * faraday_constant / charge", True, True, SUPPORTED),
        _c("W23-02", "charge = mass * faraday_constant / molar_mass", True, True, SUPPORTED),
        _c("W23-03", "current = charge / time", True, True, SUPPORTED),
        _c("W23-N1", "mass = charge / faraday_constant", False, False, NEGATIVE),
    )),
    Wheel("W24", "Semiconductor Device Physics", (
        "saturation_current = current",
        "diffusion_constant = mobility * thermal_voltage",
    ), (
        _c("W24-01", "mobility = diffusion_constant / thermal_voltage", True, True, SUPPORTED),
        _c("W24-02", "thermal_voltage = diffusion_constant / mobility", True, True, SUPPORTED),
        _c("W24-03", "debye_length = (permittivity * thermal_voltage / (2 * carrier_concentration))^(1/2)",
           True, False, CONVENTION, None,
           note="Debye length involves sqrt; full derivation needs the charge term. Its "
                "quantities are not in the W24 table (the supplied dimension flag is kept; "
                "with SI dimensions it is wrong without the elementary charge)"),
        _c("W24-N1", "current = saturation_current / voltage", False, False, NEGATIVE),
    )),
    Wheel("W25", "Plasma Physics & Magnetohydrodynamics", (
        "cyclotron_frequency = charge * magnetic_field / mass",
        "alfven_velocity = magnetic_field / (permeability * mass_density)^(1/2)",
    ), (
        _c("W25-01", "magnetic_field = cyclotron_frequency * mass / charge", True, True, SUPPORTED, None,
           note=_CORRECTED + "supplied 'magnetic_field = cyclotron_frequency * mass' (the charge "
                "of omega_c = q B / m added, with the axiom)"),
        _c("W25-02", "mass = charge * magnetic_field / cyclotron_frequency", True, True, SUPPORTED, None,
           note=_CORRECTED + "supplied 'mass = magnetic_field / cyclotron_frequency' (the charge "
                "added, with the axiom)"),
        _c("W25-03", "mass_density = magnetic_field^2 / (permeability * alfven_velocity^2)",
           True, True, SUPPORTED, None,
           note=_CORRECTED + "supplied 'mass_density = (magnetic_field / alfven_velocity)^2' "
                "(the permeability of v_A = B / (mu0 rho)^(1/2) added, with the axiom)"),
        _c("W25-N1", "cyclotron_frequency = mass / magnetic_field", False, False, NEGATIVE),
    )),
    Wheel("W28", "Superconductivity & Josephson Effects", (
        "josephson_voltage = magnetic_flux / time",
        "flux_quantum = magnetic_flux",
    ), (
        _c("W28-01", "magnetic_flux = josephson_voltage * time", True, True, SUPPORTED),
        _c("W28-02", "time = magnetic_flux / josephson_voltage", True, True, SUPPORTED),
        _c("W28-03", "magnetic_flux = flux_quantum", True, True, SUPPORTED),
        _c("W28-N1", "josephson_voltage = time / magnetic_flux", False, False, NEGATIVE),
    )),
    Wheel("W29", "Spintronics & Spin Transport", (
        "larmor_frequency = gyromagnetic_ratio * magnetic_field",
        "spin_diffusion_length = (diffusion_coefficient * time)^(1/2)",
    ), (
        _c("W29-01", "gyromagnetic_ratio = larmor_frequency / magnetic_field", True, True, SUPPORTED),
        _c("W29-02", "magnetic_field = larmor_frequency / gyromagnetic_ratio", True, True, SUPPORTED),
        _c("W29-03", "time = spin_diffusion_length^2 / diffusion_coefficient", True, True, SUPPORTED, None,
           note=_CORRECTED + "supplied 'time = (spin_diffusion_length / diffusion_coefficient)^2' "
                "(lambda = (D tau)^(1/2): the root binds D tau, with the axiom)"),
        _c("W29-N1", "larmor_frequency = magnetic_field / gyromagnetic_ratio", False, False, NEGATIVE),
    )),
    Wheel("W32", "Capillarity & Surface Phenomena", (
        "pressure = surface_tension / capillary_radius",
    ), (
        _c("W32-01", "surface_tension = pressure * capillary_radius", True, True, SUPPORTED),
        _c("W32-02", "capillary_radius = surface_tension / pressure", True, True, SUPPORTED),
        _c("W32-03", "viscosity = surface_tension * wetting_coefficient / (capillary_height * capillary_radius)",
           False, False, SUPPORTED, None,
           note=_SETTLED + "expected_dimensional False and expected_derivable False (supplied "
                "True, True): it rearranges the dropped capillary-height axiom, and it is "
                "dimensionally wrong on the W32 table"),
        _c("W32-N1", "pressure = capillary_radius / surface_tension", False, False, NEGATIVE),
    )),
    Wheel("W33", "Multi-Phase Heat & Mass Transfer", (
        "nusselt_number = heat_transfer_coefficient * characteristic_length / thermal_conductivity",
    ), (
        _c("W33-01", "thermal_conductivity = heat_transfer_coefficient * characteristic_length",
           True, False, SUPPORTED, None,
           note=_SETTLED + "expected_derivable False (supplied True): true only when the "
                "Nusselt number is 1; it followed from the dropped axiom "
                "heat_transfer_coefficient = thermal_conductivity / characteristic_length"),
        _c("W33-02", "characteristic_length = thermal_conductivity / heat_transfer_coefficient",
           True, False, SUPPORTED, None,
           note=_SETTLED + "expected_derivable False (supplied True): true only when the "
                "Nusselt number is 1"),
        _c("W33-03", "heat_transfer_coefficient = nusselt_number * thermal_conductivity / characteristic_length",
           True, True, SUPPORTED),
        _c("W33-N1", "nusselt_number = thermal_conductivity / heat_transfer_coefficient",
           False, False, NEGATIVE),
    )),
    Wheel("W34", "Biomechanics & Hemodynamics", (
        "vascular_resistance = viscosity * length / pipe_radius^4",
        "volume_flow_rate = pressure / vascular_resistance",
    ), (
        _c("W34-01", "viscosity = vascular_resistance * pipe_radius^4 / length", True, True, SUPPORTED),
        _c("W34-02", "pipe_radius = (viscosity * length / vascular_resistance)^(1/4)",
           True, True, CONVENTION, None,
           note="4th root; dimensionally consistent but fractional power. " + _SETTLED
                + "expected_derivable True (supplied False): over rational exponents it is "
                "one quarter of the resistance axiom"),
        _c("W34-03", "pressure = volume_flow_rate * vascular_resistance", True, True, SUPPORTED),
        _c("W34-N1", "vascular_resistance = pipe_radius^4 / (viscosity * length)",
           False, False, NEGATIVE),
    )),
)

#: Each absorbed wheel's dimension table (eight axes, rational exponents):
#: the supplied table, with the corrections :data:`CORRECTIONS` records.
CENT_TABLES: Dict[str, Dict[str, Tuple[Fraction, ...]]] = {
    "W16": {"area": _d(L=2), "current": _d(I=1), "emf": _d(L=2, M=1, T=-3, I=-1),
            "flux": _d(L=2, M=1, T=-2, I=-1), "inductance": _d(L=2, M=1, T=-2, I=-2),
            "magnetic_field": _d(M=1, T=-2, I=-1), "time": _d(T=1)},
    "W17": {"distance": _d(L=1), "gravitational_constant": _d(L=3, M=-1, T=-2),
            "period": _d(T=1), "source_mass": _d(M=1), "surface_gravity": _d(L=1, T=-2)},
    "W18": {"amount": _d(N=1), "gas_constant": _d(L=2, M=1, T=-2, H=-1, N=-1),
            "pressure": _d(L=-1, M=1, T=-2), "temperature": _d(H=1), "volume": _d(L=3)},
    "W19": {"electric_field": _d(L=1, M=1, T=-3, I=-1), "magnetic_field": _d(M=1, T=-2, I=-1),
            "permeability": _d(L=1, M=1, T=-2, I=-2), "permittivity": _d(L=-3, M=-1, T=4, I=2),
            "speed_of_light": _d(L=1, T=-1)},
    "W20": {"area_moment_inertia": _d(L=4), "bending_moment": _d(L=2, M=1, T=-2),
            "flexural_rigidity": _d(L=3, M=1, T=-2), "radius_curvature": _d(L=1),
            "strain": _d(), "stress": _d(L=-1, M=1, T=-2), "youngs_modulus": _d(L=-1, M=1, T=-2)},
    "W21": {"crack_length": _d(L=1), "dimensionless_factor": _d(),
            "fracture_toughness": _d(L=-1, M=1, T=-2), "stress": _d(L=-1, M=1, T=-2),
            "stress_intensity_factor": _d(L=Fraction(-1, 2), M=1, T=-2),
            "surface_energy": _d(M=1, T=-2), "youngs_modulus": _d(L=-1, M=1, T=-2)},
    "W22": {"concentration": _d(L=-3, N=1), "pre_exponential_factor": _d(T=-1),
            "rate_constant": _d(T=-1), "reaction_rate": _d(L=-3, T=-1, N=1)},
    "W23": {"charge": _d(T=1, I=1), "current": _d(I=1), "faraday_constant": _d(T=1, I=1, N=-1),
            "mass": _d(M=1), "molar_mass": _d(M=1, N=-1), "time": _d(T=1)},
    "W24": {"current": _d(I=1), "diffusion_constant": _d(L=2, T=-1),
            "mobility": _d(M=-1, T=2, I=1), "saturation_current": _d(I=1),
            "thermal_voltage": _d(L=2, M=1, T=-3, I=-1)},
    "W25": {"alfven_velocity": _d(L=1, T=-1), "charge": _d(T=1, I=1),
            "cyclotron_frequency": _d(T=-1), "magnetic_field": _d(M=1, T=-2, I=-1),
            "mass": _d(M=1), "mass_density": _d(L=-3, M=1),
            "permeability": _d(L=1, M=1, T=-2, I=-2)},
    "W28": {"flux_quantum": _d(L=2, M=1, T=-2, I=-1), "josephson_voltage": _d(L=2, M=1, T=-3, I=-1),
            "magnetic_flux": _d(L=2, M=1, T=-2, I=-1), "time": _d(T=1)},
    "W29": {"diffusion_coefficient": _d(L=2, T=-1), "gyromagnetic_ratio": _d(M=-1, T=1, I=1),
            "larmor_frequency": _d(T=-1), "magnetic_field": _d(M=1, T=-2, I=-1),
            "spin_diffusion_length": _d(L=1), "time": _d(T=1)},
    "W32": {"capillary_height": _d(L=1), "capillary_radius": _d(L=1),
            "pressure": _d(L=-1, M=1, T=-2), "surface_tension": _d(M=1, T=-2),
            "viscosity": _d(L=-1, M=1, T=-1), "wetting_coefficient": _d()},
    "W33": {"characteristic_length": _d(L=1), "heat_transfer_coefficient": _d(M=1, T=-3, H=-1),
            "nusselt_number": _d(), "thermal_conductivity": _d(L=1, M=1, T=-3, H=-1)},
    "W34": {"length": _d(L=1), "pipe_radius": _d(L=1), "pressure": _d(L=-1, M=1, T=-2),
            "vascular_resistance": _d(L=-4, M=1, T=-1), "viscosity": _d(L=-1, M=1, T=-1),
            "volume_flow_rate": _d(L=3, T=-1)},
}

#: Every change from the supplied wheels, with its reason.
CORRECTIONS: Tuple[Correction, ...] = (
    Correction("W21", "axiom", "axiom 1",
               "fracture_toughness = (2 * youngs_modulus * surface_energy / (314159265 * crack_length))^(1/2)",
               "fracture_toughness = (2 * youngs_modulus * surface_energy / crack_length)^(1/2)",
               "d", "314159265 stands for pi (it is pi times 10^8, and pi is irrational): dropped as "
                    "W17-03 drops 4 pi^2; the item's own case W21-01 already drops it"),
    Correction("W21", "table", "stress_intensity_factor", "L^-1 M T^-2", "L^-1/2 M T^-2", "c",
               "K = Y sigma a^(1/2) is in Pa m^(1/2); the supplied entry made axiom 2 fail at SI7"),
    Correction("W25", "axiom", "axiom 1", "cyclotron_frequency = magnetic_field / mass",
               "cyclotron_frequency = charge * magnetic_field / mass", "a",
               "omega_c = q B / m: the charge was missing (the table gains charge = T I)"),
    Correction("W25", "axiom", "axiom 2", "alfven_velocity = magnetic_field / mass_density^(1/2)",
               "alfven_velocity = magnetic_field / (permeability * mass_density)^(1/2)", "a",
               "v_A = B / (mu0 rho)^(1/2): the permeability was missing (the table gains "
               "permeability = L M T^-2 I^-2, W19's entry)"),
    Correction("W25", "case", "W25-01", "magnetic_field = cyclotron_frequency * mass",
               "magnetic_field = cyclotron_frequency * mass / charge", "a", "with axiom 1"),
    Correction("W25", "case", "W25-02", "mass = magnetic_field / cyclotron_frequency",
               "mass = charge * magnetic_field / cyclotron_frequency", "a", "with axiom 1"),
    Correction("W25", "case", "W25-03", "mass_density = (magnetic_field / alfven_velocity)^2",
               "mass_density = magnetic_field^2 / (permeability * alfven_velocity^2)", "a",
               "with axiom 2"),
    Correction("W29", "axiom", "axiom 2", "spin_diffusion_length = diffusion_coefficient * time^(1/2)",
               "spin_diffusion_length = (diffusion_coefficient * time)^(1/2)", "b",
               "lambda = (D tau)^(1/2): the root binds D tau"),
    Correction("W29", "case", "W29-03", "time = (spin_diffusion_length / diffusion_coefficient)^2",
               "time = spin_diffusion_length^2 / diffusion_coefficient", "b", "with axiom 2"),
    Correction("W34", "table", "vascular_resistance", "L^-4 M T^1", "L^-4 M T^-1", "c",
               "hydraulic resistance is Pa s / m^3; the supplied entry made both W34 axioms fail "
               "at SI7 (8 / pi of Poiseuille dropped, as declared)"),
    Correction("W17", "flag", "W17-03 expected_dimensional_explicit", "False", "True", "table",
               "no W17 quantity carries the angle axis"),
    Correction("W20", "flag", "W20-N1 expected_dimensional", "False", "True", "table",
               "strain is dimensionless"),
    Correction("W22", "flag", "W22-03 expected_derivable", "True", "False", "span",
               "no W22 axiom names its quantities"),
    Correction("W32", "flag", "W32-03 expected_dimensional, expected_derivable", "True, True",
               "False, False", "span",
               "it rearranges the dropped axiom and fails at SI7 on the W32 table"),
    Correction("W33", "flag", "W33-01 expected_derivable", "True", "False", "span",
               "true only at Nusselt number 1, which followed from the dropped axiom"),
    Correction("W33", "flag", "W33-02 expected_derivable", "True", "False", "span",
               "true only at Nusselt number 1, which followed from the dropped axiom"),
    Correction("W34", "flag", "W34-02 expected_derivable", "False", "True", "span",
               "over rational exponents it is one quarter of the resistance axiom"),
)

#: The supplied axioms rule R drops (correcting them would be a guess).
DROPPED: Tuple[Dropped, ...] = (
    Dropped("W22", "rate_constant = pre_exponential_factor * concentration / rate_constant",
            "self-referential; the Arrhenius law k = A exp(-Ea / R T) is not a monomial, and any "
            "monomial reading would invent a quantity"),
    Dropped("W32", "capillary_height = surface_tension * wetting_coefficient / (viscosity * capillary_radius)",
            "fails at SI7; Jurin's law has rho g and no viscosity, Washburn's has a viscosity and a "
            "time: which law was meant is a guess"),
    Dropped("W33", "heat_transfer_coefficient = thermal_conductivity / characteristic_length",
            "balances, but with the Nusselt definition it puts nusselt_number = 1 in the span "
            "(mark S5): true only for pure conduction"),
    Dropped("W35", "membrane_voltage = temperature / valence",
            "fails at SI7; the Nernst law needs k_B / e and a logarithm, which is not a monomial"),
    Dropped("W35", "ion_flux = diffusion_coefficient * ion_concentration",
            "fails at SI7; Fick's law needs a 1/length -- a concentration gradient or a membrane "
            "thickness: which was meant is a guess"),
)

#: Supplied new wheels that are not absorbed, and why.
NOT_ABSORBED: Dict[str, str] = {
    "W35": "both axioms dropped under rule R; with no axiom the wheel derives nothing",
}


# ===========================================================================
# 5.  THE W4 / W6 ADDITIONS AND THE W11-W15 CASES (data beside the registry)
# ===========================================================================
#
# Absorbed as data with their Lean evidence; the W4 and W6 of
# ``engineering/wheels.py`` and the wheels of ``wheels/w11.py``-``w15.py`` are
# unchanged (attaching these is a separate decision).

#: ``wheel id -> (added axiom, case)``: the supplied W4 and W6 additions.
ENGINEERING_ADDITIONS: Dict[str, Tuple[str, FormulaCase]] = {
    "W4": ("energy = 1/2 * moment_of_inertia * angular_velocity^2",
           _c("W4-04", "energy = 1/2 * moment_of_inertia * angular_velocity^2", True, True,
              SUPPORTED, None, note="PREDICTED by W4<->W5 isomorphism; standard rotational KE")),
    "W6": ("power = pressure * volume_flow_rate",
           _c("W6-03", "power = pressure * volume_flow_rate", True, True, SUPPORTED, None,
              note="PREDICTED by W4<->W6 isomorphism; previously the 'union flip'")),
}

#: The supplied tables of W4 and W6 (for the balance of the additions).
ADDITION_TABLES: Dict[str, Dict[str, Tuple[Fraction, ...]]] = {
    "W4": {"angular_acceleration": _d(T=-2, A=1), "angular_momentum": _d(L=2, M=1, T=-1, A=-1),
           "angular_velocity": _d(T=-1, A=1), "energy": _d(L=2, M=1, T=-2),
           "moment_of_inertia": _d(L=2, M=1, A=-2), "power": _d(L=2, M=1, T=-3),
           "torque": _d(L=2, M=1, T=-2, A=-1)},
    "W6": {"area": _d(L=2), "force": _d(L=1, M=1, T=-2), "power": _d(L=2, M=1, T=-3),
           "pressure": _d(L=-1, M=1, T=-2), "velocity": _d(L=1, T=-1),
           "volume_flow_rate": _d(L=3, T=-1)},
}

#: The 14 supplied cases of W11-W15 (the package's wheels have none).
DOMAIN_CASES: Dict[str, Tuple[FormulaCase, ...]] = {
    "W11": (
        _c("W11-01", "length = velocity * time", True, True, SUPPORTED),
        _c("W11-02", "time = length / velocity", True, True, SUPPORTED),
    ),
    "W12": (
        _c("W12-01", "volume = mass / density", True, True, SUPPORTED),
        _c("W12-02", "length = volume / area", True, True, SUPPORTED),
        _c("W12-03", "molar_mass = mass / amount", True, True, SUPPORTED),
    ),
    "W13": (
        _c("W13-01", "period = 1 / frequency", True, True, SUPPORTED),
        _c("W13-02", "angular_frequency = angle * frequency", True, True, CONVENTION, None,
           note="numerically omega = 2*pi*f; angle is one turn"),
        _c("W13-03", "spring_constant = mass * angular_frequency^2", True, True, SUPPORTED),
    ),
    "W14": (
        _c("W14-01", "angular_frequency = 1 / (inductance * capacitance * angular_frequency)",
           True, True, SUPPORTED, None, note="rearranged: omega^2 = 1/(LC)"),
        _c("W14-02", "reactance = inductance * angular_frequency", True, True, SUPPORTED),
        _c("W14-03", "energy = 1/2 * inductance * current^2", True, True, SUPPORTED),
    ),
    "W15": (
        _c("W15-01", "current = charge / time", True, True, SUPPORTED),
        _c("W15-02", "power = energy / time", True, True, SUPPORTED),
        _c("W15-03", "time = charge / current", True, True, SUPPORTED),
    ),
}

#: The supplied tables of W11-W15 (the explicit-angle registry).
DOMAIN_TABLES: Dict[str, Dict[str, Tuple[Fraction, ...]]] = {
    "W11": {"length": _d(L=1), "time": _d(T=1), "velocity": _d(L=1, T=-1)},
    "W12": {"amount": _d(N=1), "area": _d(L=2), "density": _d(L=-3, M=1), "length": _d(L=1),
            "mass": _d(M=1), "molar_mass": _d(M=1, N=-1), "volume": _d(L=3)},
    "W13": {"angle": _d(A=1), "angular_frequency": _d(T=-1, A=1), "frequency": _d(T=-1),
            "mass": _d(M=1), "period": _d(T=1), "spring_constant": _d(M=1, T=-2)},
    "W14": {"angular_frequency": _d(T=-1, A=1), "capacitance": _d(L=-2, M=-1, T=4, I=2),
            "current": _d(I=1), "energy": _d(L=2, M=1, T=-2),
            "inductance": _d(L=2, M=1, T=-2, I=-2), "reactance": _d(L=2, M=1, T=-3, I=-2)},
    "W15": {"charge": _d(T=1, I=1), "current": _d(I=1), "energy": _d(L=2, M=1, T=-2),
            "power": _d(L=2, M=1, T=-3), "time": _d(T=1)},
}


# ===========================================================================
# 6.  LOOKUP AND THE ANSWERING FUNCTION
# ===========================================================================

def cent_wheel(wheel_id: str) -> Wheel:
    """The absorbed cent wheel with this ``id`` (``"W16"`` ... ``"W34"``).

    Raises ``KeyError`` if there is none (W26, W27, W30, W31 were never
    supplied; W35 is not absorbed)."""
    for w in CENT_WHEELS:
        if w.id == wheel_id:
            return w
    raise KeyError(f"no absorbed cent wheel with id {wheel_id!r}")


def extended_wheel(wheel_id: str) -> Wheel:
    """W4 or W6 of ``engineering/wheels.py`` with the supplied addition --
    a new ``Wheel`` object; the registry's W4 and W6 are not changed."""
    from ..engineering.wheels import wheel_named
    base = wheel_named(wheel_id)
    axiom, case = ENGINEERING_ADDITIONS[wheel_id]
    cases = tuple(case if c.id == case.id else c for c in base.cases)
    if case.id not in {c.id for c in base.cases}:
        cases = cases + (case,)
    return Wheel(base.id, base.title, base.axioms + (axiom,), cases)


def _licensing(equation: str, wheels: Sequence[Wheel], integer: bool) -> Optional[Tuple[str, object]]:
    for w in wheels:
        try:
            if integer:
                from ..engineering.wheels import derivation_certificate
                cert = derivation_certificate(equation, w.axioms)
                if cert is not None:
                    return w.id, tuple((a, x) for a, x in cert.weights)
            else:
                x = certificate(equation, w.axioms)
                if x is not None:
                    return w.id, tuple(zip(w.axioms, x))
        except ValueError:
            continue
    return None


def answer_derivability(equation: str, wheel_id: Optional[str] = None,
                        with_registry: bool = True) -> Dict[str, object]:
    """Does ``equation`` follow from the GLM's wheels?  The query surface's
    entry point for the cent wheels.

    With ``wheel_id`` the question is put to that absorbed cent wheel (or, for
    ``"W1"`` ... ``"W15"``, to that registry wheel); without it, to the fifteen
    registry wheels (integer engine) when ``with_registry`` and then to every
    absorbed cent wheel (rational-power engine), one wheel at a time.  Returns
    ``{"equation", "verdict", "wheel", "certificate", "functional"}`` where
    ``verdict`` is ``"derivable"`` (``wheel`` derives it; ``certificate`` the
    ``(axiom, weight)`` pairs), ``"not derivable"`` (no wheel tried derives it;
    ``functional`` the separating functional of the named wheel when one was
    named) or ``"unreadable"`` (not a monomial equation).
    """
    out: Dict[str, object] = {"equation": equation, "verdict": "not derivable",
                              "wheel": wheel_id, "certificate": None, "functional": None}
    try:
        relation_vector_q(equation)
    except ValueError:
        out["verdict"] = "unreadable"
        return out
    if wheel_id is not None:
        try:
            w = cent_wheel(wheel_id)
        except KeyError:
            from . import wheel_by_id
            w = wheel_by_id(wheel_id)
        x = certificate(equation, w.axioms)
        if x is not None:
            out.update(verdict="derivable", certificate=tuple(zip(w.axioms, x)))
        else:
            out["functional"] = separating_functional(equation, w.axioms)
        return out
    found = None
    if with_registry:
        from . import ALL_WHEELS
        found = _licensing(equation, ALL_WHEELS, integer=True)
    if found is None:
        found = _licensing(equation, CENT_WHEELS, integer=False)
    if found is not None:
        out.update(verdict="derivable", wheel=found[0], certificate=found[1])
    return out
