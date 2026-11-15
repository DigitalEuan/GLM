"""
Extension of glm_wheels.py to the 15-wheel system (W1..W15) with
declared junctions, non-identities, the licensed union, and the
wave_speed = speed_of_light bridge.

W11..W15 are taken verbatim from the DOMAIN_WHEELS_STUDY.md table:
    W11  Uniform motion                              velocity = length / time
    W12  Density, volume and amount                  density = mass / volume
                                                    volume = area * length
                                                    amount = mass / molar_mass
    W13  Period and the mass-spring oscillator       frequency = 1 / period
                                                    angular_frequency = angle * frequency
                                                    spring_constant = mass * angular_frequency^2
    W14  Inductors and the LC circuit                reactance = inductance * angular_frequency
                                                    inductance * capacitance * angular_frequency^2 = 1
                                                    energy = 1/2 * inductance * current^2
    W15  Charge and energy over time                 charge = current * time
                                                    energy = power * time

Junctions are from DOMAIN_WHEELS_STUDY.md §2.3, with the Phase 158
revision of W9/W13 (frequency only, angle split as a non-identity).

The wave_speed = speed_of_light junction (W9/W10) is added to plug
the W10-03 gap.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .wheels import (
    Wheel, WHEELS as WHEELS_10, FormulaCase,
    SUPPORTED, UNDERSPECIFIED, CONVENTION, NEGATIVE,
    REFERENCE_AXES, REFERENCE_DIMENSIONS, _d,
    parse_equation, parse_monomial, relation_vector,
    Monomial, _rref, _solve, _null_space,
    derivation_certificate, is_derivable, consistency, _reference_si,
    wheel_quantities,
)


# ---------------------------------------------------------------------------
# 1. The five new wheels (W11..W15)
# ---------------------------------------------------------------------------

def _c(cid, eq, dim, der, status, explicit=None, note=""):
    return FormulaCase(cid, eq, dim, der, status, explicit, note)


W11 = Wheel("W11", "Uniform motion", (
    "velocity = length / time",
), (
    _c("W11-01", "length = velocity * time", True, True, SUPPORTED),
    _c("W11-02", "time = length / velocity", True, True, SUPPORTED),
))

W12 = Wheel("W12", "Density, volume and amount of substance", (
    "density = mass / volume",
    "volume = area * length",
    "amount = mass / molar_mass",
), (
    _c("W12-01", "volume = mass / density", True, True, SUPPORTED),
    _c("W12-02", "length = volume / area", True, True, SUPPORTED),
    _c("W12-03", "molar_mass = mass / amount", True, True, SUPPORTED),
))

W13 = Wheel("W13", "Period and the mass-spring oscillator", (
    "frequency = 1 / period",
    "angular_frequency = angle * frequency",
    "spring_constant = mass * angular_frequency^2",
), (
    _c("W13-01", "period = 1 / frequency", True, True, SUPPORTED),
    _c("W13-02", "angular_frequency = angle * frequency", True, True, CONVENTION,
       note="numerically omega = 2*pi*f; angle is one turn"),
    _c("W13-03", "spring_constant = mass * angular_frequency^2", True, True, SUPPORTED),
))

W14 = Wheel("W14", "Inductors and the LC circuit", (
    "reactance = inductance * angular_frequency",
    "inductance * capacitance * angular_frequency^2 = 1",
    "energy = 1/2 * inductance * current^2",
), (
    _c("W14-01", "angular_frequency = 1 / (inductance * capacitance * angular_frequency)",
       True, True, SUPPORTED, note="rearranged: omega^2 = 1/(LC)"),
    _c("W14-02", "reactance = inductance * angular_frequency", True, True, SUPPORTED),
    _c("W14-03", "energy = 1/2 * inductance * current^2", True, True, SUPPORTED),
))

W15 = Wheel("W15", "Charge and energy over time", (
    "charge = current * time",
    "energy = power * time",
), (
    _c("W15-01", "current = charge / time", True, True, SUPPORTED),
    _c("W15-02", "power = energy / time", True, True, SUPPORTED),
    _c("W15-03", "time = charge / current", True, True, SUPPORTED),
))

WHEELS_15: Tuple[Wheel, ...] = WHEELS_10 + (W11, W12, W13, W14, W15)


# ---------------------------------------------------------------------------
# 2. New quantities needed by W11..W15 (extend REFERENCE_DIMENSIONS)
# ---------------------------------------------------------------------------

# The quantities new to W11..W15 that are not in REFERENCE_DIMENSIONS:
#   length       -- already present
#   time         -- already present
#   area         -- already present
#   volume       -- already present
#   mass         -- already present
#   molar_mass   -- NEW  (M / N)
#   amount       -- NEW  (N)
#   density      -- already present
#   frequency    -- already present
#   period       -- NEW  (T)
#   angular_frequency -- NEW  (T^-1 A^1; same axes as angular_velocity but a
#                       different physical quantity in EXT10 because of the
#                       angle axis. The study splits W13.angular_frequency
#                       from W9.angular_velocity via the Phase 158 revision.)
#   spring_constant -- already present
#   reactance    -- already present (= resistance)
#   inductance   -- already present
#   capacitance  -- already present
#   current      -- already present
#   charge       -- already present
#   power        -- already present
#   energy       -- already present

_EXTENDED_DIMENSIONS: Dict[str, Tuple[Fraction, ...]] = {
    **REFERENCE_DIMENSIONS,
    # amount of substance (mole) on the N axis
    "amount":             _d(N=1),
    # molar mass: mass per amount
    "molar_mass":         _d(M=1, N=-1),
    # period: time of one cycle
    "period":             _d(T=1),
    # angular_frequency: angle per time. NOTE: same EXT10 axes as
    # angular_velocity (T^-1 A^1). The study deliberately keeps
    # W13.angular_frequency and W9.angular_velocity as distinct
    # physical quantities joined only across `frequency` (Phase 158).
    "angular_frequency":  _d(T=-1, A=1),
}

# Patch REFERENCE_DIMENSIONS so consistency() picks these up.
REFERENCE_DIMENSIONS.update(_EXTENDED_DIMENSIONS)


# ---------------------------------------------------------------------------
# 3. Junctions and non-identities  (Phase 157 + Phase 158 revision)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Junction:
    wheel_a: str
    wheel_b: str
    name: str          # name in wheel_a
    reason: str
    name_b: Optional[str] = None   # name in wheel_b (defaults to same as name_a)

@dataclass(frozen=True)
class NonIdentity:
    wheel_a: str
    wheel_b: str
    name: str
    reason: str


# Phase 157 declared junctions (10 of them), with the Phase 158 revision
# of W9/W13 (frequency only, angle split).
JUNCTIONS: Tuple[Junction, ...] = (
    Junction("W5",  "W11", "velocity",       "moving body's velocity = uniform-motion velocity"),
    Junction("W5",  "W12", "mass",           "the body whose density is read is the body that moves"),
    Junction("W6",  "W12", "area",           "the flow's cross-section = swept-prism cross-section"),
    Junction("W11", "W12", "length",         "the length the fluid moves = length of the swept prism"),
    # Phase 158 revision: only frequency is joined across W9/W13, angle is split.
    Junction("W9",  "W13", "frequency",      "the oscillator's frequency = the wave's frequency"),
    Junction("W5",  "W13", "mass",           "the oscillating body = the dynamic body"),
    Junction("W3",  "W14", "capacitance",    "the LC circuit's capacitor = the electrostatics capacitor"),
    Junction("W1",  "W14", "current",        "the inductor's current = the circuit's current"),
    Junction("W1",  "W15", "current",        "the charge and energy are carried by the circuit's current"),
    Junction("W1",  "W15", "power",          "the energy is delivered by the circuit's power"),
    Junction("W3",  "W15", "charge",         "the charge moved = the charge stored"),
    # NEW: bridges the W10-03 gap. The photon's wave_speed IS the speed of light,
    # AND the photon's frequency IS the wave's frequency (a photon is a wave).
    # These are "alias junctions" -- the two names differ but refer to the
    # same physical quantity. Both together make W10-03 (momentum = h / λ)
    # derivable from the licensed union.
    Junction("W9",  "W10", "wave_speed",     "a photon's wave_speed = speed_of_light (light is the wave)",
             name_b="speed_of_light"),
    Junction("W9",  "W10", "frequency",      "a photon's frequency = the wave's frequency (a photon is a wave)"),
)

NON_IDENTITIES: Tuple[NonIdentity, ...] = (
    NonIdentity("W13", "W14", "angular_frequency",
                "a mechanical oscillator against an electrical one; identifying them "
                "would give spring_constant = mass / (inductance * capacitance)"),
    NonIdentity("W3",  "W14", "energy",
                "the capacitor's stored energy against the inductor's"),
    NonIdentity("W3",  "W15", "energy",
                "energy stored in a capacitor against energy delivered over a time"),
    NonIdentity("W11", "W15", "time",
                "a travel time against a charging time"),
    NonIdentity("W9",  "W13", "angle",
                "Phase 158 split: the oscillator's angle convention vs the wave's "
                "angle reference; only frequency is joined"),
)


# ---------------------------------------------------------------------------
# 4. Prefix-aware axiom rewriting
# ---------------------------------------------------------------------------

import ast


def _walk_rename(node, wheel_id: str) -> Monomial:
    """Rename every Name in a parsed monomial AST to wheel_id.name."""
    if isinstance(node, ast.Name):
        return Monomial.make(1, {f"{wheel_id}.{node.id}": Fraction(1)})
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        if node.value == 0:
            raise ValueError("zero is not a quantity expression")
        return Monomial.make(node.value, {})
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _walk_rename(node.operand, wheel_id)
        return Monomial(-inner.coefficient, inner.powers)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return _walk_rename(node.left, wheel_id).mul(_walk_rename(node.right, wheel_id))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _walk_rename(node.left, wheel_id).mul(_walk_rename(node.right, wheel_id).pow(-1))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        exponent = _walk_rename(node.right, wheel_id)
        if exponent.powers or exponent.coefficient.denominator != 1:
            raise ValueError("a power must be an integer literal")
        return _walk_rename(node.left, wheel_id).pow(exponent.coefficient.numerator)
    raise ValueError(f"unsupported syntax in node: {ast.dump(node)}")


def prefix_axiom(axiom: str, wheel_id: str) -> str:
    """Rewrite `voltage = current * resistance` (in wheel W1) as
    `W1.voltage = W1.current * W1.resistance`."""
    if axiom.count("=") != 1:
        raise ValueError(f"axiom needs one '=': {axiom!r}")
    lhs, rhs = (s.strip() for s in axiom.split("="))
    lhs_m = _walk_rename(ast.parse(lhs.replace("^", "**"), mode="eval").body, wheel_id)
    rhs_m = _walk_rename(ast.parse(rhs.replace("^", "**"), mode="eval").body, wheel_id)
    def render(m: Monomial) -> str:
        if not m.powers:
            return str(m.coefficient)
        body = " * ".join(
            (n if e == 1 else f"{n}^{e}") for n, e in m.powers
        )
        if m.coefficient != 1:
            body = f"{m.coefficient} * {body}"
        return body
    return f"{render(lhs_m)} = {render(rhs_m)}"


def _wheel_holding(name: str, wheels: Tuple[Wheel, ...] = WHEELS_15,
                   prefer: Optional[str] = None) -> Optional[str]:
    """Find the wheel that holds `name`. If `prefer` is given and holds the
    name, return it. If exactly one wheel holds the name, return it. If
    multiple hold it but `prefer` is one of them, return prefer. Otherwise
    return the first holder (and the caller should disambiguate)."""
    holders = [w.id for w in wheels if name in wheel_quantities(w)]
    if not holders:
        return None
    if prefer and prefer in holders:
        return prefer
    return holders[0]


def prefix_case_equation(equation: str, target_wheel_id: str,
                         wheels: Tuple[Wheel, ...] = WHEELS_15) -> str:
    """Prefix every quantity name in `equation` with the wheel that holds it.
    Names in `target_wheel_id` get that prefix; names only in another wheel
    get that wheel's prefix. Raises if any name is ambiguous (in multiple
    non-target wheels) or unknown."""
    if equation.count("=") != 1:
        raise ValueError(f"equation needs one '=': {equation!r}")
    lhs, rhs = (s.strip() for s in equation.split("="))
    def walk_and_prefix(node):
        from glm_wheels import Monomial as _M, Fraction as _F
        if isinstance(node, ast.Name):
            holder = _wheel_holding(node.id, wheels, prefer=target_wheel_id)
            if holder is None:
                raise ValueError(f"name {node.id!r} not held by any wheel")
            return _M.make(1, {f"{holder}.{node.id}": _F(1)})
        if isinstance(node, ast.Attribute):
            # Already prefixed; reconstruct dotted name
            parts = []
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
                return _M.make(1, {".".join(reversed(parts)): _F(1)})
            raise ValueError("bad attribute chain")
        if (isinstance(node, ast.Constant) and isinstance(node.value, int)
                and not isinstance(node.value, bool)):
            if node.value == 0:
                raise ValueError("zero is not a quantity expression")
            return _M.make(node.value, {})
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = walk_and_prefix(node.operand)
            return _M(-inner.coefficient, inner.powers)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return walk_and_prefix(node.left).mul(walk_and_prefix(node.right))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return walk_and_prefix(node.left).mul(walk_and_prefix(node.right).pow(-1))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            exponent = walk_and_prefix(node.right)
            if exponent.powers or exponent.coefficient.denominator != 1:
                raise ValueError("a power must be an integer literal")
            return walk_and_prefix(node.left).pow(exponent.coefficient.numerator)
        raise ValueError(f"unsupported syntax: {ast.dump(node)}")
    lhs_m = walk_and_prefix(ast.parse(lhs.replace("^", "**"), mode="eval").body)
    rhs_m = walk_and_prefix(ast.parse(rhs.replace("^", "**"), mode="eval").body)
    def render(m):
        if not m.powers:
            return str(m.coefficient)
        body = " * ".join(
            (n if e == 1 else f"{n}^{e}") for n, e in m.powers
        )
        if m.coefficient != 1:
            body = f"{m.coefficient} * {body}"
        return body
    return f"{render(lhs_m)} = {render(rhs_m)}"


def junction_axiom(j: Junction) -> str:
    """`W1.current = W15.current` for same-name junctions, or
    `W9.wave_speed = W10.speed_of_light` for alias junctions."""
    name_b = j.name_b if j.name_b is not None else j.name
    return f"{j.wheel_a}.{j.name} = {j.wheel_b}.{name_b}"


# ---------------------------------------------------------------------------
# 5. Licensed union
# ---------------------------------------------------------------------------

def build_licensed_union(wheels: Tuple[Wheel, ...] = WHEELS_15,
                         junctions: Tuple[Junction, ...] = JUNCTIONS
                         ) -> List[str]:
    """Return the list of all axioms in the licensed union:
       - every wheel's axioms, with quantities prefixed by wheel id
       - every junction as an equality axiom bridging the two wheel-local names
       Non-identities are respected by NOT appearing in `junctions`."""
    axioms: List[str] = []
    for w in wheels:
        for ax in w.axioms:
            axioms.append(prefix_axiom(ax, w.id))
    for j in junctions:
        axioms.append(junction_axiom(j))
    return axioms


def build_naive_union(wheels: Tuple[Wheel, ...] = WHEELS_15) -> List[str]:
    """The naive union: all axioms with names UN-prefixed, every shared name
    silently conflated. This is what wheels.py's case_table uses."""
    return [a for w in wheels for a in w.axioms]


def licensed_is_derivable(target_equation: str, target_wheel_id: str,
                          wheels: Tuple[Wheel, ...] = WHEELS_15,
                          junctions: Tuple[Junction, ...] = JUNCTIONS) -> bool:
    """Is `target = formula` (with names possibly drawn from any wheel)
    derivable from the licensed union + junctions?"""
    try:
        prefixed_target = prefix_case_equation(target_equation, target_wheel_id, wheels)
    except ValueError:
        return False
    axioms = build_licensed_union(wheels, junctions)
    return is_derivable(prefixed_target, axioms)


def licensed_derivation_certificate(target_equation: str, target_wheel_id: str,
                                    wheels: Tuple[Wheel, ...] = WHEELS_15,
                                    junctions: Tuple[Junction, ...] = JUNCTIONS):
    try:
        prefixed_target = prefix_case_equation(target_equation, target_wheel_id, wheels)
    except ValueError:
        return None, None, None
    axioms = build_licensed_union(wheels, junctions)
    return derivation_certificate(prefixed_target, axioms), prefixed_target, axioms


# ---------------------------------------------------------------------------
# 6. Extended case table
# ---------------------------------------------------------------------------

def extended_case_table() -> List[Dict[str, object]]:
    """Run every case of every wheel through:
       - dimensional consistency at reference / ext10 / si7
       - local derivability (within own wheel)
       - naive-union derivability (all axioms, names conflated)
       - licensed-union derivability (prefixed + junctions; uses
         prefix_case_equation so cross-wheel cases like W10-03 work)
    """
    naive = build_naive_union()
    licensed = build_licensed_union()
    rows: List[Dict[str, object]] = []
    for w in WHEELS_15:
        for c in w.cases:
            ref = consistency(c.equation, "reference")
            ext = consistency(c.equation, "ext10")
            si = consistency(c.equation, "si7")
            try:
                prefixed_target = prefix_case_equation(c.equation, w.id)
                licensed_ok = is_derivable(prefixed_target, licensed)
                licensed_err = None
            except ValueError as e:
                licensed_ok = False
                licensed_err = str(e)
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
                "derivable_local":      is_derivable(c.equation, w.axioms),
                "derivable_naive":      is_derivable(c.equation, naive),
                "derivable_licensed":   licensed_ok,
                "licensed_error":       licensed_err,
                "expected_derivable":   c.expected_derivable,
                "note":                 c.note,
            })
    return rows


# ---------------------------------------------------------------------------
# 7. Spoke census over the 15-wheel licensed union
# ---------------------------------------------------------------------------

def all_licensed_quantities(wheels: Tuple[Wheel, ...] = WHEELS_15,
                            junctions: Tuple[Junction, ...] = JUNCTIONS
                            ) -> List[str]:
    """Every wheel-prefixed quantity name that appears in the licensed union,
       plus aliases created by junctions (a junction makes Wa.x and Wb.x the
       same quantity; we keep both labels for census enumeration but they
       refer to the same column in the relation matrix)."""
    qs = set()
    for w in wheels:
        for q in wheel_quantities(w):
            qs.add(f"{w.id}.{q}")
    return sorted(qs)


def census_licensed_union(wheels: Tuple[Wheel, ...] = WHEELS_15,
                          junctions: Tuple[Junction, ...] = JUNCTIONS,
                          limit_targets: Optional[int] = None
                          ) -> Dict[str, object]:
    """For every (target, [y, z]) triple over the licensed union's quantity
    names (with target in the same wheel as y or z, since cross-wheel targets
    would need a junction), check:
       - in-wheel:  some single wheel derives it (over its OWN axioms)
       - gained:    the licensed union derives it, no single wheel does
       - refused:   neither does
    Returns counts plus a list of gained derivations (with certificates).
    """
    axioms = build_licensed_union(wheels, junctions)
    # Map each prefixed quantity to its wheel for in-wheel checks.
    quantities_by_wheel: Dict[str, List[str]] = {}
    for w in wheels:
        quantities_by_wheel[w.id] = [f"{w.id}.{q}" for q in wheel_quantities(w)]

    # For each wheel, enumerate its quantities as targets, with input pairs
    # drawn from ANY wheel's quantities (cross-domain derivation).
    # The census is bounded by |targets| * |pairs|, so for each wheel
    # we iterate its own quantities as targets.
    in_wheel_count = 0
    gained_count = 0
    refused_count = 0
    gained_examples = []

    targets_done = 0
    for w in wheels:
        if limit_targets is not None and targets_done >= limit_targets:
            break
        for target_q in wheel_quantities(w):
            if limit_targets is not None and targets_done >= limit_targets:
                break
            targets_done += 1
            prefixed_target = f"{w.id}.{target_q}"
            # enumerate all pairs (y, z) from the union's quantities
            all_qs = []
            for w2 in wheels:
                for q2 in wheel_quantities(w2):
                    if q2 != target_q:
                        all_qs.append(f"{w2.id}.{q2}")
            # local wheel's quantities for in-wheel check
            local_qs = [f"{w.id}.{q}" for q in wheel_quantities(w) if q != target_q]
            for i in range(len(all_qs)):
                for j in range(i + 1, len(all_qs)):
                    y, z = all_qs[i], all_qs[j]
                    # in-wheel?
                    in_wheel = False
                    if y in local_qs and z in local_qs:
                        # try derivation within this wheel's own axioms
                        # (need to express target as a function of two local inputs)
                        # Use derive_from with unprefixed axiom and unprefixed names.
                        # This is the local two-input spoke check.
                        # For census brevity we use the existing derive_from via
                        # the unprefixed wheel axioms:
                        from glm_wheels import derive_from as _df
                        y_local = y.split(".", 1)[1]
                        z_local = z.split(".", 1)[1]
                        if y_local in wheel_quantities(w) and z_local in wheel_quantities(w):
                            spoke = _df(target_q, (y_local, z_local), w.axioms, w.id)
                            in_wheel = spoke is not None
                    # licensed union derivation?
                    # Goal: target = y * z  (or any combination; we just test
                    # whether target's relation is in the span with only y, z,
                    # and the junction-equalities allowed to mention other names).
                    # The cleanest test is: can we derive `prefixed_target = y * z`
                    # from the licensed union?
                    try:
                        licensed_derivable = is_derivable(
                            f"{prefixed_target} = {y} * {z}", axioms)
                    except Exception:
                        licensed_derivable = False
                    if licensed_derivable and not in_wheel:
                        gained_count += 1
                        if len(gained_examples) < 200:
                            gained_examples.append({
                                "wheel": w.id, "target": target_q,
                                "y": y, "z": z,
                                "formula": f"{prefixed_target} = {y} * {z}",
                            })
                    elif in_wheel:
                        in_wheel_count += 1
                    else:
                        refused_count += 1
    return {
        "in_wheel":  in_wheel_count,
        "gained":    gained_count,
        "refused":   refused_count,
        "examples":  gained_examples,
    }


# ---------------------------------------------------------------------------
# 8. Full + subgraph isomorphism search across all 15 wheels
# ---------------------------------------------------------------------------

def axiom_signature(axiom: str) -> Tuple[tuple, tuple, tuple]:
    """Shape signature of an axiom, ignoring names:
       (multiset_of_exponents, multiset_of_prime_exponents, n_pos_names, n_neg_names)."""
    rel = relation_vector(axiom)
    exp_ms = tuple(sorted(v for k, v in rel.items() if not k.startswith('#')))
    prime_ms = tuple(sorted((k, v) for k, v in rel.items() if k.startswith('#')))
    n_pos = sum(1 for k, v in rel.items() if not k.startswith('#') and v > 0)
    n_neg = sum(1 for k, v in rel.items() if not k.startswith('#') and v < 0)
    return (exp_ms, prime_ms, n_pos, n_neg)


def find_full_isomorphism(wi: Wheel, wj: Wheel) -> Optional[Dict[str, str]]:
    """Same-axiom-count isomorphism: bijection on names that maps Wi's axiom
    set onto Wj's (modulo permutation). Returns the name mapping or None."""
    if len(wi.axioms) != len(wj.axioms):
        return None
    names_i = sorted(wheel_quantities(wi))
    names_j = sorted(wheel_quantities(wj))
    if len(names_i) != len(names_j):
        return None
    rels_i = [relation_vector(a) for a in wi.axioms]
    rels_j = [relation_vector(a) for a in wj.axioms]
    def ms(rel):
        return tuple(sorted(v for k, v in rel.items() if not k.startswith('#')))
    def primsig(rel):
        return tuple(sorted((k, v) for k, v in rel.items() if k.startswith('#')))
    cand = []
    for ri in rels_i:
        c = [k for k, rj in enumerate(rels_j)
             if ms(ri) == ms(rj) and primsig(ri) == primsig(rj)]
        cand.append(c)
        if not c:
            return None
    from itertools import permutations
    for perm in permutations(range(len(rels_j))):
        if all(perm[i] in cand[i] for i in range(len(rels_i))):
            f = _try_assign(names_i, names_j, rels_i, [rels_j[p] for p in perm])
            if f is not None:
                return f
    return None


def _try_assign(names_i, names_j, rels_i, rels_j_paired):
    f = {}
    used = set()
    def backtrack(idx):
        if idx == len(names_i):
            for ri, rj in zip(rels_i, rels_j_paired):
                for k, v in ri.items():
                    if k.startswith('#'):
                        continue
                    if rj.get(f[k], Fraction(0)) != v:
                        return False
            return True
        n = names_i[idx]
        allowed = None
        for ri, rj in zip(rels_i, rels_j_paired):
            if n in ri:
                e = ri[n]
                cands = [nj for nj in names_j
                         if nj not in used and rj.get(nj, Fraction(0)) == e]
                if allowed is None:
                    allowed = set(cands)
                else:
                    allowed &= set(cands)
                if not allowed:
                    return False
        if allowed is None:
            allowed = set(nj for nj in names_j if nj not in used)
        for tgt in sorted(allowed):
            f[n] = tgt
            used.add(tgt)
            if backtrack(idx + 1):
                return True
            used.discard(tgt)
            del f[n]
        return False
    if backtrack(0):
        return f
    return None


def find_subgraph_isomorphism(wi: Wheel, wj: Wheel
                              ) -> Optional[Tuple[Dict[str, str], List[str], List[str]]]:
    """Largest subgraph isomorphism: find the largest subset S of Wi's axioms
    and subset T of Wj's axioms (with |S|=|T|) and a name bijection between
    the quantities in S and those in T that maps S axiom-by-axiom onto T.
    Returns (mapping, axioms_S, axioms_T) or None.
    """
    # Try sizes from min(|Wi|, |Wj|) down to 1.
    max_size = min(len(wi.axioms), len(wj.axioms))
    for size in range(max_size, 0, -1):
        from itertools import combinations, permutations
        for subset_i in combinations(range(len(wi.axioms)), size):
            axioms_i = [wi.axioms[k] for k in subset_i]
            for subset_j in combinations(range(len(wj.axioms)), size):
                axioms_j = [wj.axioms[k] for k in subset_j]
                # Find a bijection
                mapping = _find_bijection_for_subsets(axioms_i, axioms_j)
                if mapping is not None:
                    return mapping, axioms_i, axioms_j
    return None


def _find_bijection_for_subsets(axioms_i: List[str], axioms_j: List[str]
                                ) -> Optional[Dict[str, str]]:
    """Find a name bijection f such that applying f to each axiom of axioms_i
    gives (a permutation of) axioms_j."""
    rels_i = [relation_vector(a) for a in axioms_i]
    rels_j = [relation_vector(a) for a in axioms_j]
    def ms(rel):
        return tuple(sorted(v for k, v in rel.items() if not k.startswith('#')))
    def primsig(rel):
        return tuple(sorted((k, v) for k, v in rel.items() if k.startswith('#')))
    cand = []
    for ri in rels_i:
        c = [k for k, rj in enumerate(rels_j)
             if ms(ri) == ms(rj) and primsig(ri) == primsig(rj)]
        cand.append(c)
        if not c:
            return None
    from itertools import permutations
    for perm in permutations(range(len(rels_j))):
        if all(perm[i] in cand[i] for i in range(len(rels_i))):
            names_i = sorted({k for r in rels_i for k in r if not k.startswith('#')})
            names_j = sorted({k for r in rels_j for k in r if not k.startswith('#')})
            if len(names_i) != len(names_j):
                continue
            f = _try_assign(names_i, names_j, rels_i, [rels_j[p] for p in perm])
            if f is not None:
                return f
    return None


def search_all_isomorphisms(wheels: Tuple[Wheel, ...] = WHEELS_15
                            ) -> List[Dict[str, object]]:
    """Search every unordered wheel pair for both full and subgraph
    isomorphism. Return a flat list of records."""
    out: List[Dict[str, object]] = []
    for i in range(len(wheels)):
        for j in range(i + 1, len(wheels)):
            wi, wj = wheels[i], wheels[j]
            # full
            full = find_full_isomorphism(wi, wj)
            if full is not None:
                out.append({
                    "type": "full",
                    "Wi": wi.id, "Wj": wj.id,
                    "mapping": full,
                    "n_axioms_matched": len(wi.axioms),
                    "Wi_axioms": list(wi.axioms),
                    "Wj_axioms": list(wj.axioms),
                })
            # subgraph (only if no full, or to find a larger partial if full fails)
            if full is None:
                sub = find_subgraph_isomorphism(wi, wj)
                if sub is not None:
                    mapping, axs_i, axs_j = sub
                    out.append({
                        "type": "subgraph",
                        "Wi": wi.id, "Wj": wj.id,
                        "mapping": mapping,
                        "n_axioms_matched": len(axs_i),
                        "Wi_axioms": axs_i,
                        "Wj_axioms": axs_j,
                    })
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Extended wheel system: {len(WHEELS_15)} wheels, "
          f"{sum(len(w.axioms) for w in WHEELS_15)} axioms, "
          f"{sum(len(w.cases) for w in WHEELS_15)} cases")
    print(f"Junctions: {len(JUNCTIONS)}")
    print(f"Non-identities: {len(NON_IDENTITIES)}")
    print(f"Licensed union axiom count: {len(build_licensed_union())}")
