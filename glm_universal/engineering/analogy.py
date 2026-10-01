"""``glm_universal.engineering.analogy`` -- speaking mechanics in circuits.

Two standard dictionaries
-------------------------
A mass on a spring with a damper and a series R-L-C circuit obey the same
second-order equation, and engineers have two ways to line them up:

* the **force-voltage** (impedance, Maxwell) analogy: force <-> voltage,
  velocity <-> current, mass <-> inductance, damping <-> resistance,
  spring constant <-> 1/capacitance;
* the **force-current** (mobility, Firestone) analogy: force <-> current,
  velocity <-> voltage, mass <-> capacitance, damping <-> 1/resistance,
  spring constant <-> 1/inductance.

Each is a map on quantity *names* with an exponent: ``spring_constant`` maps
to ``capacitance^-1``.  Extended multiplicatively, it carries a monomial
formula of one domain to a monomial formula of the other.  That is what
"translate" means here, and nothing looser.

Structure, checked rather than assumed
--------------------------------------
A dictionary is only worth speaking through if it sends laws to laws.
:func:`structure_check` translates every axiom of the electrical wheel and
asks whether the result is *derivable* in the mechanical wheel (and back).
When every axiom lands in the span, every derived formula does too -- the
translation is linear on relation vectors -- which is
``GLM.Engineering.translate_derivable`` in
``RequestProject/GLM/EngineeringWheels.lean``.  So a derivation done in one
domain is a derivation in the other, and the GLM can solve a mechanical
question with the circuit wheel and check it against the mechanical wheel:
two routes, one answer, or a refusal.

An unnamed analogy is ambiguous (mass is an inductance in one dictionary and
a capacitance in the other), and the question surface refuses it rather than
choosing.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Tuple

from .wheels import (Monomial, is_derivable, parse_equation, relation_vector,
                     render_monomial)

__all__ = [
    "Analogy", "FORCE_VOLTAGE", "FORCE_CURRENT", "ANALOGIES", "SCRAMBLED",
    "ELECTRICAL_AXIOMS", "MECHANICAL_AXIOMS", "translate_equation", "degeneracy",
    "counterpart", "structure_check", "analogy_report",
]


@dataclass(frozen=True)
class Analogy:
    """A name map ``mechanical -> (electrical, exponent)``."""

    name: str
    aliases: Tuple[str, ...]
    to_electrical: Tuple[Tuple[str, str, int], ...]

    def forward(self) -> Dict[str, Tuple[str, int]]:
        return {m: (e, k) for m, e, k in self.to_electrical}

    def backward(self) -> Dict[str, Tuple[str, int]]:
        return {e: (m, k) for m, e, k in self.to_electrical}


_SHARED = (("power", "power", 1), ("energy", "energy", 1),
           ("time", "time", 1), ("angular_frequency", "angular_frequency", 1),
           ("quality_factor", "quality_factor", 1),
           ("damping_ratio", "damping_ratio", 1))

FORCE_VOLTAGE = Analogy(
    "force-voltage", ("force-voltage", "force voltage", "impedance analogy",
                      "maxwell"),
    (("force", "voltage", 1), ("velocity", "current", 1),
     ("kinetic_energy", "magnetic_energy", 1),
     ("potential_energy", "electric_energy", 1),
     ("displacement", "charge", 1), ("momentum", "magnetic_flux", 1),
     ("mass", "inductance", 1), ("damping_coefficient", "resistance", 1),
     ("spring_constant", "capacitance", -1)) + _SHARED)

FORCE_CURRENT = Analogy(
    "force-current", ("force-current", "force current", "mobility analogy",
                      "firestone"),
    (("force", "current", 1), ("velocity", "voltage", 1),
     ("kinetic_energy", "electric_energy", 1),
     ("potential_energy", "magnetic_energy", 1),
     ("displacement", "magnetic_flux", 1), ("momentum", "charge", 1),
     ("mass", "capacitance", 1), ("damping_coefficient", "resistance", -1),
     ("spring_constant", "inductance", -1)) + _SHARED)

ANALOGIES: Tuple[Analogy, ...] = (FORCE_VOLTAGE, FORCE_CURRENT)

#: Each wheel names its two stored energies apart.  A first version wrote
#: both as ``energy``; with ``voltage = current * resistance`` that forces
#: ``inductance = capacitance * resistance^2`` -- every circuit critically
#: tuned at ``Q = 1`` -- and :func:`degeneracy` exists to catch exactly that.
#:
#: The lumped series-circuit wheel.  The quality factor is the *series*
#: R-L-C one, ``omega0 L / R``; a parallel circuit's is ``R / (omega0 L)``.
ELECTRICAL_AXIOMS: Tuple[str, ...] = (
    "voltage = current * resistance",
    "power = voltage * current",
    "charge = capacitance * voltage",
    "magnetic_flux = inductance * current",
    "magnetic_energy = 1/2 * inductance * current^2",
    "electric_energy = 1/2 * capacitance * voltage^2",
    "angular_frequency^2 * inductance * capacitance = 1",
    "quality_factor = angular_frequency * inductance / resistance",
    "damping_ratio * quality_factor = 1/2",
)

#: The lumped mass-spring-damper wheel.
MECHANICAL_AXIOMS: Tuple[str, ...] = (
    "force = damping_coefficient * velocity",
    "power = force * velocity",
    "force = spring_constant * displacement",
    "momentum = mass * velocity",
    "kinetic_energy = 1/2 * mass * velocity^2",
    "potential_energy = 1/2 * force^2 / spring_constant",
    "angular_frequency^2 * mass = spring_constant",
    "quality_factor = angular_frequency * mass / damping_coefficient",
    "damping_ratio * quality_factor = 1/2",
)


def _map_monomial(m: Monomial, table: Mapping[str, Tuple[str, int]]
                  ) -> Optional[Monomial]:
    out: Dict[str, Fraction] = {}
    for name, e in m.powers:
        if name not in table:
            return None
        image, k = table[name]
        out[image] = out.get(image, Fraction(0)) + e * k
    return Monomial.make(m.coefficient, out)


def _render_side(m: Monomial, order: List[str]) -> str:
    """Render ``m`` keeping the names in ``order`` (the source's order)."""
    primes: Dict[int, Fraction] = {}
    from .wheels import _prime_exponents
    for key, e in _prime_exponents(m.coefficient.numerator).items():
        primes[int(key[1:])] = primes.get(int(key[1:]), Fraction(0)) + e
    for key, e in _prime_exponents(m.coefficient.denominator).items():
        primes[int(key[1:])] = primes.get(int(key[1:]), Fraction(0)) - e
    rank = {n: i for i, n in enumerate(order)}
    powers = sorted(m.powers, key=lambda p: (rank.get(p[0], len(rank)), p[0]))
    return render_monomial(primes, powers)


def translate_equation(equation: str, analogy: Analogy,
                       direction: str) -> Optional[str]:
    """``equation`` carried across ``analogy``: ``direction`` is
    ``"to_mechanical"`` or ``"to_electrical"``.  ``None`` when some name has
    no counterpart."""
    table = (analogy.backward() if direction == "to_mechanical"
             else analogy.forward())
    from .wheels import _names_in
    lhs, rhs = parse_equation(equation)
    a, b = _map_monomial(lhs, table), _map_monomial(rhs, table)
    if a is None or b is None:
        return None
    sides = [part.strip() for part in equation.split("=")]
    orders = [[table[n][0] for n in _names_in(side)] for side in sides]
    return f"{_render_side(a, orders[0])} = {_render_side(b, orders[1])}"


def counterpart(name: str, analogy: Analogy, direction: str
                ) -> Optional[str]:
    """The name ``name`` corresponds to, rendered with its exponent."""
    table = (analogy.backward() if direction == "to_mechanical"
             else analogy.forward())
    if name not in table:
        return None
    image, k = table[name]
    return image if k == 1 else f"1/{image}"


def structure_check(analogy: Analogy) -> Dict[str, object]:
    """Does ``analogy`` send every axiom of one wheel into the other's span,
    in both directions?"""
    e2m = []
    for ax in ELECTRICAL_AXIOMS:
        t = translate_equation(ax, analogy, "to_mechanical")
        e2m.append((ax, t, t is not None and is_derivable(t,
                                                           MECHANICAL_AXIOMS)))
    m2e = []
    for ax in MECHANICAL_AXIOMS:
        t = translate_equation(ax, analogy, "to_electrical")
        m2e.append((ax, t, t is not None and is_derivable(t,
                                                           ELECTRICAL_AXIOMS)))
    return {"analogy": analogy.name,
            "electrical_to_mechanical": sum(ok for *_, ok in e2m),
            "mechanical_to_electrical": sum(ok for *_, ok in m2e),
            "axioms": (len(ELECTRICAL_AXIOMS), len(MECHANICAL_AXIOMS)),
            "failures": [(a, t) for a, t, ok in e2m + m2e if not ok]}


def _dimension_changes(analogy: Analogy) -> int:
    """How many of the analogy's name pairs change dimension (SI7).

    An analogy is a map on laws, not on dimensions: force and voltage do not
    share a dimension.  Counting the pairs that change is the control that
    shows the structure check is not a dimensional identity in disguise.
    """
    from .wheels import dimension
    changed = 0
    for m, e, k in analogy.to_electrical:
        dm, de = dimension(m, "si7"), dimension(e, "si7")
        if dm is None or de is None:
            continue
        if tuple(x for x in dm) != tuple(k * x for x in de):
            changed += 1
    return changed


#: The control: the force-voltage dictionary with the images of mass and
#: damping exchanged.  Every name still has a counterpart; the laws do not
#: survive, and the structure check must say so.
SCRAMBLED = Analogy(
    "scrambled-control", (),
    tuple((m, {"inductance": "resistance", "resistance": "inductance"}.get(
        e, e), k) for m, e, k in FORCE_VOLTAGE.to_electrical))


def degeneracy() -> Dict[str, Optional[str]]:
    """Formulas tying element parameters to one another that the wheels
    must *not* imply: resistance from inductance and capacitance, damping
    from mass and spring constant.  ``None`` is the healthy answer."""
    from .wheels import derive_from
    e = derive_from("resistance", ("inductance", "capacitance"),
                    ELECTRICAL_AXIOMS)
    m = derive_from("damping_coefficient", ("mass", "spring_constant"),
                    MECHANICAL_AXIOMS)
    return {"electrical": None if e is None else e.text(),
            "mechanical": None if m is None else m.text()}


def analogy_report() -> Dict[str, object]:
    out = {a.name: {**structure_check(a),
                    "pairs": len(a.to_electrical),
                    "dimension_changing_pairs": _dimension_changes(a)}
           for a in ANALOGIES}
    control = structure_check(SCRAMBLED)
    out["scrambled-control"] = {
        "electrical_to_mechanical": control["electrical_to_mechanical"],
        "mechanical_to_electrical": control["mechanical_to_electrical"]}
    out["degeneracy"] = degeneracy()
    return out
