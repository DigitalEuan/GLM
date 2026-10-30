"""
Faithful Python port of the GLM formula-wheel system from
DigitalEuan/GLM :: glm_universal/engineering/wheels.py.

This file reproduces the wheel definitions (W1..W10), the relation_vector
machinery (with #p scalar prime tracking), the exact rational linear algebra
(_rref, _solve, _null_space), and the case_table measurement.

Run as:  python3 glm_wheels.py
"""
from __future__ import annotations
import ast
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

# ===========================================================================
# 1. MONOMIALS AND RELATION VECTORS  (verbatim port)
# ===========================================================================

@dataclass(frozen=True)
class Monomial:
    coefficient: Fraction
    powers: Tuple[Tuple[str, Fraction], ...]

    @staticmethod
    def make(coefficient, powers: Mapping[str, Fraction]) -> "Monomial":
        return Monomial(
            Fraction(coefficient),
            tuple(sorted((k, Fraction(v)) for k, v in powers.items() if v)),
        )

    def as_dict(self) -> Dict[str, Fraction]:
        return dict(self.powers)

    def mul(self, other: "Monomial") -> "Monomial":
        p = self.as_dict()
        for k, v in other.powers:
            p[k] = p.get(k, Fraction(0)) + v
        return Monomial.make(self.coefficient * other.coefficient, p)

    def pow(self, n: int) -> "Monomial":
        return Monomial.make(
            self.coefficient ** n, {k: v * n for k, v in self.powers}
        )


def parse_monomial(text: str) -> Monomial:
    try:
        tree = ast.parse(text.replace("^", "**").strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"not a monomial: {text!r}") from exc

    def _dotted_name(node: ast.AST):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
            return ".".join(reversed(parts))
        return None

    def visit(node: ast.AST) -> Monomial:
        if isinstance(node, ast.Attribute):
            dn = _dotted_name(node)
            if dn is None:
                raise ValueError(f"unsupported attribute chain in {text!r}")
            return Monomial.make(1, {dn: Fraction(1)})
        if isinstance(node, ast.Name):
            return Monomial.make(1, {node.id: Fraction(1)})
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, int)
            and not isinstance(node.value, bool)
        ):
            if node.value == 0:
                raise ValueError("zero is not a quantity expression")
            return Monomial.make(node.value, {})
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = visit(node.operand)
            return Monomial(-inner.coefficient, inner.powers)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return visit(node.left).mul(visit(node.right))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return visit(node.left).mul(visit(node.right).pow(-1))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            exponent = visit(node.right)
            if exponent.powers or exponent.coefficient.denominator != 1:
                raise ValueError("a power must be an integer literal")
            return visit(node.left).pow(exponent.coefficient.numerator)
        raise ValueError(f"unsupported syntax in {text!r}")

    return visit(tree.body)


def parse_equation(text: str) -> Tuple[Monomial, Monomial]:
    if text.count("=") != 1:
        raise ValueError("an equation needs exactly one '='")
    lhs, rhs = (part.strip() for part in text.split("="))
    if not lhs or not rhs:
        raise ValueError("both sides of an equation are required")
    return parse_monomial(lhs), parse_monomial(rhs)


def _prime_exponents(n: int) -> Dict[str, Fraction]:
    out: Dict[str, Fraction] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[f"#{d}"] = out.get(f"#{d}", Fraction(0)) + 1
            n //= d
        d += 1
    if n > 1:
        out[f"#{n}"] = out.get(f"#{n}", Fraction(0)) + 1
    return out


def relation_vector(text: str) -> Dict[str, Fraction]:
    """Relation vector of `L = R`: prod q^v_q * prod p^v_p = 1.

    Quantity keys are names; scalar keys are `#p` for prime `p`.
    A negative coefficient ratio is refused.
    """
    lhs, rhs = parse_equation(text)
    v: Dict[str, Fraction] = dict(lhs.powers)
    for k, e in rhs.powers:
        v[k] = v.get(k, Fraction(0)) - e
    ratio = lhs.coefficient / rhs.coefficient
    if ratio < 0:
        raise ValueError("a negative coefficient ratio is not a magnitude relation")
    for k, e in _prime_exponents(ratio.numerator).items():
        v[k] = v.get(k, Fraction(0)) + e
    for k, e in _prime_exponents(ratio.denominator).items():
        v[k] = v.get(k, Fraction(0)) - e
    return {k: e for k, e in v.items() if e}


# ===========================================================================
# 2. EXACT LINEAR ALGEBRA
# ===========================================================================

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


def _solve(vectors: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> Optional[List[Fraction]]:
    n = len(vectors)
    aug = [[vectors[i][j] for i in range(n)] + [rhs[j]] for j in range(len(rhs))]
    red, pivots = _rref(aug, n)
    if any(all(x == 0 for x in row[:n]) and row[n] for row in red):
        return None
    x = [Fraction(0)] * n
    for i, c in enumerate(pivots):
        x[c] = red[i][n]
    return x


def _null_space(mat: List[List[Fraction]], n: int) -> List[List[Fraction]]:
    red, pivots = _rref(mat, n) if mat else ([], [])
    basis = []
    for f in (c for c in range(n) if c not in pivots):
        v = [Fraction(0)] * n
        v[f] = Fraction(1)
        for i, c in enumerate(pivots):
            v[c] = -red[i][f]
        basis.append(v)
    return basis


@dataclass(frozen=True)
class Derivation:
    target: str
    weights: Tuple[Tuple[str, Fraction], ...]

    def render(self) -> str:
        parts = [f"{w} x [{a}]" for a, w in self.weights if w]
        return " + ".join(parts) if parts else "(trivial)"


def derivation_certificate(target: str, axioms: Sequence[str]) -> Optional[Derivation]:
    rels = [relation_vector(a) for a in axioms]
    goal = relation_vector(target)
    cols = sorted({k for r in rels + [goal] for k in r})
    vecs = [[r.get(c, Fraction(0)) for c in cols] for r in rels]
    x = _solve(vecs, [goal.get(c, Fraction(0)) for c in cols])
    if x is None:
        return None
    return Derivation(target, tuple(zip(axioms, x)))


def is_derivable(target: str, axioms: Sequence[str]) -> bool:
    return derivation_certificate(target, axioms) is not None


# ===========================================================================
# 3. THE TEN WHEELS AND 41 CASES  (verbatim from wheels.py)
# ===========================================================================

SUPPORTED = "physically_supported"
UNDERSPECIFIED = "physically_underspecified"
CONVENTION = "model_convention"
NEGATIVE = "negative_control"


@dataclass(frozen=True)
class FormulaCase:
    id: str
    equation: str
    expected_dimensional: bool
    expected_derivable: bool
    physical_status: str
    expected_dimensional_explicit: Optional[bool] = None
    note: str = ""


@dataclass(frozen=True)
class Wheel:
    id: str
    title: str
    axioms: Tuple[str, ...]
    cases: Tuple[FormulaCase, ...]


@dataclass(frozen=True)
class Junction:
    wheel_a: str
    wheel_b: str
    name: str
    reason: str
    name_b: Optional[str] = None


@dataclass(frozen=True)
class NonIdentity:
    wheel_a: str
    wheel_b: str
    name: str
    reason: str


def _c(cid, eq, dim, der, status, explicit=None, note=""):
    return FormulaCase(cid, eq, dim, der, status, explicit, note)


WHEELS: Tuple[Wheel, ...] = (
    Wheel("W1", "DC Ohm and power", (
        "voltage = current * resistance", "power = voltage * current"), (
        _c("W1-01", "resistance = voltage / current", True, True, SUPPORTED),
        _c("W1-02", "power = current^2 * resistance", True, True, SUPPORTED),
        _c("W1-03", "power = voltage^2 / resistance", True, True, SUPPORTED),
        _c("W1-N1", "power = voltage * resistance", False, False, NEGATIVE))),
    Wheel("W2", "Sinusoidal AC impedance and power", (
        "voltage = current * impedance", "power = voltage * current"), (
        _c("W2-01", "impedance = voltage / current", True, True, SUPPORTED),
        _c("W2-02", "reactance = inductance * angular_velocity", True, False,
           SUPPORTED, False, "needs an inductor-reactance axiom"),
        _c("W2-03", "power = voltage * current", True, True, UNDERSPECIFIED,
           note="dimensions cannot tell P, Q, S or conjugation apart"),
        _c("W2-N1", "impedance = voltage * current", False, False, NEGATIVE))),
    Wheel("W3", "Electrostatics and capacitors", (
        "charge = capacitance * voltage",
        "energy = 1/2 * capacitance * voltage^2"), (
        _c("W3-01", "capacitance = charge / voltage", True, True, SUPPORTED),
        _c("W3-02", "energy = 1/2 * charge * voltage", True, True, SUPPORTED),
        _c("W3-03", "energy = 1/2 * charge^2 / capacitance", True, True, SUPPORTED),
        _c("W3-N1", "energy = charge * capacitance", False, False, NEGATIVE))),
    Wheel("W4", "Rotational mechanics", (
        "torque = moment_of_inertia * angular_acceleration",
        "power = torque * angular_velocity",
        "angular_momentum = moment_of_inertia * angular_velocity"), (
        _c("W4-01", "angular_acceleration = torque / moment_of_inertia", True, True, SUPPORTED),
        _c("W4-02", "power = torque * angular_velocity", True, True, SUPPORTED),
        _c("W4-03", "angular_momentum = moment_of_inertia * angular_velocity", True, True, SUPPORTED),
        _c("W4-N1", "torque = moment_of_inertia * angular_velocity", False, False, NEGATIVE),
        _c("W4-M1", "angular_velocity = frequency", True, False, CONVENTION, False,
           "numerically omega = 2*pi*f"))),
    Wheel("W5", "Linear dynamics and work-energy", (
        "force = mass * acceleration", "momentum = mass * velocity",
        "power = force * velocity", "energy = 1/2 * mass * velocity^2"), (
        _c("W5-01", "acceleration = force / mass", True, True, SUPPORTED),
        _c("W5-02", "momentum = mass * velocity", True, True, SUPPORTED),
        _c("W5-03", "energy = 1/2 * mass * velocity^2", True, True, SUPPORTED),
        _c("W5-N1", "force = mass * velocity", False, False, NEGATIVE))),
    Wheel("W6", "Fluid statics and flow", (
        "pressure = force / area", "volume_flow_rate = area * velocity",
        "force = pressure * area"), (
        _c("W6-01", "force = pressure * area", True, True, SUPPORTED),
        _c("W6-02", "velocity = volume_flow_rate / area", True, True, SUPPORTED),
        _c("W6-03", "power = pressure * volume_flow_rate", True, False, SUPPORTED,
           note="needs a hydraulic-power axiom"),
        _c("W6-N1", "pressure = force * area", False, False, NEGATIVE))),
    Wheel("W7", "Linear plane-wave acoustics", (
        "acoustic_pressure = acoustic_impedance * particle_velocity",
        "acoustic_intensity = acoustic_pressure * particle_velocity"), (
        _c("W7-01", "acoustic_impedance = acoustic_pressure / particle_velocity", True, True, SUPPORTED),
        _c("W7-02", "acoustic_intensity = acoustic_pressure * particle_velocity", True, True, UNDERSPECIFIED),
        _c("W7-03", "acoustic_intensity = acoustic_pressure^2 / acoustic_impedance", True, True, SUPPORTED),
        _c("W7-N1", "acoustic_intensity = acoustic_pressure^2 / particle_velocity", False, False, NEGATIVE))),
    Wheel("W8", "Thermal physics and heat transfer", (
        "energy = mass * specific_heat_capacity * temperature",
        "entropy = energy / temperature",
        "heat_flux = thermal_conductivity * temperature_gradient"), (
        _c("W8-01", "specific_heat_capacity = energy / (mass * temperature)", True, True, SUPPORTED),
        _c("W8-02", "entropy = energy / temperature", True, True, UNDERSPECIFIED),
        _c("W8-03", "heat_flux = thermal_conductivity * temperature_gradient", True, True, UNDERSPECIFIED),
        _c("W8-N1", "power = stefan_boltzmann_constant * temperature^4", False, False, NEGATIVE,
           note="emitting area absent"))),
    Wheel("W9", "Wave kinematics", (
        "wave_speed = frequency * wavelength",
        "angular_velocity = angle * frequency"), (
        _c("W9-01", "frequency = wave_speed / wavelength", True, True, SUPPORTED),
        _c("W9-02", "wavelength = wave_speed / frequency", True, True, SUPPORTED),
        _c("W9-03", "angular_velocity = angle * frequency", True, True, CONVENTION),
        _c("W9-N1", "wave_speed = frequency / wavelength", False, False, NEGATIVE))),
    Wheel("W10", "Photon energy and momentum", (
        "energy = planck_constant * frequency",
        "energy = speed_of_light * momentum"), (
        _c("W10-01", "frequency = energy / planck_constant", True, True, SUPPORTED),
        _c("W10-02", "momentum = energy / speed_of_light", True, True, SUPPORTED),
        _c("W10-03", "momentum = planck_constant / wavelength", True, False, SUPPORTED,
           note="needs wave_speed = c as well"),
        _c("W10-N1", "energy = planck_constant / frequency", False, False, NEGATIVE))),
)


def wheel_named(wheel_id: str) -> Wheel:
    for w in WHEELS:
        if w.id == wheel_id:
            return w
    raise KeyError(wheel_id)


def _names_in(text: str) -> List[str]:
    tree = ast.parse(text.replace("^", "**").strip(), mode="eval")
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    return sorted(names, key=lambda n: (text.find(n), n))


def wheel_quantities(wheel: Wheel) -> Tuple[str, ...]:
    seen: List[str] = []
    for axiom in wheel.axioms:
        for side in axiom.split("="):
            for tok in _names_in(side):
                if tok not in seen:
                    seen.append(tok)
    return tuple(seen)


# ===========================================================================
# 4. DIMENSIONS AT THREE LAYERS  (verbatim)
# ===========================================================================

REFERENCE_AXES: Tuple[str, ...] = ("L", "M", "T", "I", "H", "N", "J", "A")
_EXT10_AXES = ("L", "M", "T", "I", "H", "N", "J", "A", "S", "B")


def _d(**p: int) -> Tuple[Fraction, ...]:
    return tuple(Fraction(p.get(a, 0)) for a in REFERENCE_AXES)


_E = _d(L=2, M=1, T=-2)
_R = _d(L=2, M=1, T=-3, I=-2)
_P = _d(L=-1, M=1, T=-2)

REFERENCE_DIMENSIONS: Dict[str, Tuple[Fraction, ...]] = {
    "length": _d(L=1), "area": _d(L=2), "volume": _d(L=3), "time": _d(T=1),
    "mass": _d(M=1), "temperature": _d(H=1), "current": _d(I=1),
    "charge": _d(T=1, I=1), "frequency": _d(T=-1),
    "velocity": _d(L=1, T=-1), "acceleration": _d(L=1, T=-2),
    "force": _d(L=1, M=1, T=-2), "momentum": _d(L=1, M=1, T=-1),
    "energy": _E, "power": _d(L=2, M=1, T=-3), "pressure": _P,
    "density": _d(L=-3, M=1), "volume_flow_rate": _d(L=3, T=-1),
    "voltage": _d(L=2, M=1, T=-3, I=-1), "resistance": _R, "impedance": _R,
    "reactance": _R, "conductance": tuple(-x for x in _R),
    "capacitance": _d(L=-2, M=-1, T=4, I=2),
    "inductance": _d(L=2, M=1, T=-2, I=-2),
    "magnetic_flux": _d(L=2, M=1, T=-2, I=-1),
    "moment_of_inertia": _d(L=2, M=1, A=-2), "angle": _d(A=1),
    "angular_velocity": _d(T=-1, A=1), "angular_acceleration": _d(T=-2, A=1),
    "torque": _d(L=2, M=1, T=-2, A=-1),
    "angular_momentum": _d(L=2, M=1, T=-1, A=-1),
    "spring_constant": _d(M=1, T=-2), "damping_coefficient": _d(M=1, T=-1),
    "acoustic_pressure": _P, "particle_velocity": _d(L=1, T=-1),
    "acoustic_impedance": _d(L=-2, M=1, T=-1),
    "acoustic_intensity": _d(M=1, T=-3), "wavelength": _d(L=1),
    "wave_speed": _d(L=1, T=-1), "speed_of_light": _d(L=1, T=-1),
    "planck_constant": _d(L=2, M=1, T=-1),
    "reduced_planck_constant": _d(L=2, M=1, T=-1, A=-1),
    "entropy": _d(L=2, M=1, T=-2, H=-1),
    "specific_heat_capacity": _d(L=2, T=-2, H=-1),
    "thermal_conductivity": _d(L=1, M=1, T=-3, H=-1),
    "heat_flux": _d(M=1, T=-3), "temperature_gradient": _d(L=-1, H=1),
    "stefan_boltzmann_constant": _d(M=1, T=-3, H=-4),
}


def _axes(layer: str) -> Tuple[str, ...]:
    return {
        "reference": REFERENCE_AXES,
        "ext10": _EXT10_AXES,
        "si7": _EXT10_AXES[:7],
    }[layer]


def dimension_ref(name: str, layer: str) -> Optional[Tuple[Fraction, ...]]:
    """Use REFERENCE_DIMENSIONS only (we don't have the GLM register locally)."""
    if layer == "reference":
        return REFERENCE_DIMENSIONS.get(name)
    vec = REFERENCE_DIMENSIONS.get(name)
    if vec is None:
        return None
    # ext10 keeps all 8; si7 drops A (and S, B which we never set)
    if layer == "ext10":
        # extend to 10 axes with S=0, B=0
        return vec + (Fraction(0), Fraction(0))
    # si7: take first 7 (drop A)
    return vec[:7]


def _monomial_dimension(m: Monomial, layer: str) -> Optional[Tuple[Fraction, ...]]:
    total = [Fraction(0)] * len(_axes(layer))
    for name, e in m.powers:
        vec = dimension_ref(name, layer)
        if vec is None:
            return None
        for i, x in enumerate(vec):
            total[i] += e * x
    return tuple(total)


def consistency(equation: str, layer: str) -> Optional[Dict[str, object]]:
    lhs, rhs = parse_equation(equation)
    a = _monomial_dimension(lhs, layer)
    b = _monomial_dimension(rhs, layer)
    if a is None or b is None:
        return None
    residual = {ax: x - y for ax, x, y in zip(_axes(layer), a, b) if x != y}
    return {"consistent": not residual, "residual": residual}


def _reference_si(equation: str) -> Optional[bool]:
    lhs, rhs = parse_equation(equation)
    a = _monomial_dimension(lhs, "reference")
    b = _monomial_dimension(rhs, "reference")
    if a is None or b is None:
        return None
    return a[:7] == b[:7]


# ===========================================================================
# 5. SPOKE GENERATION  (verbatim port)
# ===========================================================================

def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def _fmt_power(name: str, e: Fraction) -> str:
    return name if e == 1 else f"{name}^{e}"


def render_monomial(coefficient_primes: Mapping[int, Fraction],
                    powers: Sequence[Tuple[str, Fraction]]) -> str:
    d = 1
    for e in [e for _, e in powers] + list(coefficient_primes.values()):
        d = d * e.denominator // _gcd(d, e.denominator)
    coef = Fraction(1)
    for p, k in sorted(coefficient_primes.items()):
        coef *= Fraction(p) ** (k * d).numerator
    pos = [(n, e * d) for n, e in powers if e > 0]
    neg = [(n, -e * d) for n, e in powers if e < 0]
    head = " * ".join(_fmt_power(n, e) for n, e in pos)
    if coef != 1:
        head = f"{coef} * {head}" if head else f"{coef}"
    body = (head or "1") + "".join(f" / {_fmt_power(n, e)}" for n, e in neg)
    return body if d == 1 else f"({body})^(1/{d})"


@dataclass(frozen=True)
class Spoke:
    wheel: str
    target: str
    inputs: Tuple[str, ...]
    formula: str
    certificate: Derivation
    exponents: Tuple[Tuple[str, Fraction], ...] = ()
    primes: Tuple[Tuple[int, Fraction], ...] = ()

    def text(self) -> str:
        return f"{self.target} = {self.formula}"


def derive_from(target: str, inputs: Sequence[str], axioms: Sequence[str],
                wheel_id: str = "") -> Optional[Spoke]:
    rels = [relation_vector(a) for a in axioms]
    names = sorted({k for r in rels for k in r if not k.startswith("#")})
    if target not in names or any(y not in names for y in inputs):
        return None
    if target in inputs or len(set(inputs)) != len(inputs) or not inputs:
        return None
    constrained = [n for n in names if n not in inputs]
    vecs = [[r.get(c, Fraction(0)) for c in constrained] for r in rels]
    x = _solve(vecs, [Fraction(1) if c == target else Fraction(0) for c in constrained])
    if x is None:
        return None
    n = len(rels)
    null = _null_space([[rels[i].get(c, Fraction(0)) for i in range(n)] for c in constrained], n)
    for vec in null:
        for key in set(inputs) | {k for r in rels for k in r if k.startswith("#")}:
            if sum(vec[i] * rels[i].get(key, Fraction(0)) for i in range(n)):
                return None
    combo: Dict[str, Fraction] = {}
    for w, r in zip(x, rels):
        for k, v in r.items():
            combo[k] = combo.get(k, Fraction(0)) + w * v
    powers = [(y, -combo.get(y, Fraction(0))) for y in inputs]
    if all(e == 0 for _, e in powers):
        return None
    primes = {int(k[1:]): -v for k, v in combo.items() if k.startswith("#") and v}
    kept = [(y, e) for y, e in powers if e]
    formula = render_monomial(primes, kept)
    return Spoke(wheel_id, target, tuple(inputs), formula,
                 Derivation(f"{target} = {formula}", tuple(zip(axioms, x))),
                 tuple(kept), tuple(sorted(primes.items())))


def wheel_spokes(wheel: Wheel, target: str) -> Tuple[Spoke, ...]:
    qs = [q for q in wheel_quantities(wheel) if q != target]
    out: List[Spoke] = []
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            s = derive_from(target, (qs[i], qs[j]), wheel.axioms, wheel.id)
            if s is not None:
                out.append(s)
    return tuple(out)


# ===========================================================================
# 6. THE MEASUREMENT: 41 CASES, EVERY LAYER, AND THE UNION OF WHEELS
# ===========================================================================

def case_table() -> List[Dict[str, object]]:
    union = [a for w in WHEELS for a in w.axioms]
    rows: List[Dict[str, object]] = []
    for w in WHEELS:
        for c in w.cases:
            ref = consistency(c.equation, "reference")
            ext = consistency(c.equation, "ext10")
            si = consistency(c.equation, "si7")
            rows.append({
                "wheel": w.id, "case": c.id, "equation": c.equation,
                "status": c.physical_status,
                "dim_reference_si": _reference_si(c.equation),
                "dim_reference_explicit": None if ref is None else ref["consistent"],
                "dim_ext10": None if ext is None else ext["consistent"],
                "dim_si7": None if si is None else si["consistent"],
                "expected_dim_si": c.expected_dimensional,
                "expected_dim_explicit": (
                    c.expected_dimensional if c.expected_dimensional_explicit is None
                    else c.expected_dimensional_explicit),
                "derivable": is_derivable(c.equation, w.axioms),
                "expected_derivable": c.expected_derivable,
                "derivable_union": is_derivable(c.equation, union),
                "note": c.note,
            })
    return rows


# ===========================================================================
# JSON loading: override hardcoded data with JSON from wheels/ directory
# ===========================================================================

import json as _json
import os as _os

_WHEELS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "wheels")


def _load_wheels_from_json():
    """Load all wheels from JSON files in the wheels/ directory."""
    index_path = _os.path.join(_WHEELS_DIR, "index.json")
    if not _os.path.exists(index_path):
        return None, {}, [], []
    with open(index_path) as f:
        index = _json.load(f)
    wheels = []
    for wid in sorted(index["wheels"].keys(), key=lambda w: (len(w), w)):
        wheel_path = _os.path.join(_WHEELS_DIR, f"{wid}.json")
        if not _os.path.exists(wheel_path):
            continue
        with open(wheel_path) as f:
            data = _json.load(f)
        cases = tuple(
            FormulaCase(
                id=c["id"], equation=c["equation"],
                expected_dimensional=c["expected_dimensional"],
                expected_derivable=c["expected_derivable"],
                physical_status=c["physical_status"],
                expected_dimensional_explicit=c.get("expected_dimensional_explicit"),
                note=c.get("note", ""),
            )
            for c in data["cases"]
        )
        wheels.append(Wheel(
            id=data["id"], title=data["title"],
            axioms=tuple(data["axioms"]), cases=cases,
        ))
    # Load dimensions from wheel files
    dims = {}
    for wf in sorted(_os.listdir(_WHEELS_DIR)):
        if not wf.endswith(".json") or wf == "index.json":
            continue
        with open(_os.path.join(_WHEELS_DIR, wf)) as f:
            data = _json.load(f)
        for qname, qdim in data.get("dimensions", {}).items():
            if qdim is not None and qname not in dims:
                dims[qname] = tuple(Fraction(x) for x in qdim["exponents"])
    # Load junctions
    junctions = []
    for j in index.get("junctions", []):
        junctions.append(Junction(
            wheel_a=j["wheel_a"], wheel_b=j["wheel_b"],
            name=j["name_a"], reason=j["reason"],
            name_b=j.get("name_b") or j["name_a"],
        ))
    # Load non-identities
    non_identities = []
    for n in index.get("non_identities", []):
        non_identities.append(NonIdentity(
            wheel_a=n["wheel_a"], wheel_b=n["wheel_b"],
            name=n["name"], reason=n["reason"],
        ))
    return tuple(wheels), dims, tuple(junctions), tuple(non_identities)


# Override hardcoded data with JSON if available
_json_wheels, _json_dims, _json_juncs, _json_nonids = _load_wheels_from_json()
if _json_wheels:
    WHEELS = _json_wheels
    REFERENCE_DIMENSIONS.update(_json_dims)
    JUNCTIONS = _json_juncs
    NON_IDENTITIES = _json_nonids
else:
    JUNCTIONS = ()
    NON_IDENTITIES = ()


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    print("GLM Wheel Engine loaded.")
    print(f"Wheels: {len(WHEELS)}")
    print(f"Axioms: {sum(len(w.axioms) for w in WHEELS)}")
    print(f"Cases : {sum(len(w.cases) for w in WHEELS)}")
    print(f"Junctions: {len(JUNCTIONS)}")
    print(f"Non-identities: {len(NON_IDENTITIES)}")
