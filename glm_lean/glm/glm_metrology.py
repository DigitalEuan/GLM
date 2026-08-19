#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM MEANING  —  the primary object: the group (Z^7, +)
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  Tier 1 — exact dimensional meaning.  This is the state of the
            system; everything else in the GLM is a function of it.
  Deps   :  standard library only (no substrate dependency: this layer is
            deliberately independent and can be tested on its own).

  Contents
  --------
    §1  Dimension        an element of (Z^7, +) with exact arithmetic
    §2  QUANTITIES       a library of ~90 named SI quantities
    §3  parser           a small recursive-descent parser for expressions
                         such as  "mass * speed^2"  or  "energy/(area*time)"
    §4  equation audit   the exact check — the only verdict the system gives
    §5  library reports  dimensional collisions
    §6  appendix         the rejected F_2 carrier: what a mod-2 substrate
                         would have concluded, kept as evidence only

  Meaning is primary; the bit pattern is derived
  ----------------------------------------------
  A concept IS its exponent vector in (Z^7, +).  That vector is the whole of
  the system's state: it is what is stored, what is composed, and what every
  verdict is computed from.  The 24-bit carrier word of `glm_codec.py` is a
  DERIVED quantity — the image `word = encode(d)` of an injective map with a
  computable inverse — and it is recomputed from the meaning whenever it is
  needed.  Nothing in the system holds a bit pattern as independent state, and
  no decision is ever taken on the bits.

  The arrow runs that way round for a reason, and the reason is a theorem.  A
  carrier can only be primary if composition can be performed on it; a bit
  pattern composes by XOR; and XOR is F_2-linear, so it can only ever compare
  exponents modulo 2.  Under such a rule  E = m c^2  and  E = m c^4  are
  indistinguishable, because (2,1,-2) and (4,1,-4) agree mod 2.  Worse, no
  F_2-linear encoder of (Z^7,+) can be injective at all: every one of them
  kills 2Z^7 (Proposition 1 of the paper; `GLM.xor_blind` and
  `GLM.f2_carrier_cannot_be_primary` in the Lean companion).  So the bits
  cannot carry meaning, and meaning must carry the bits.

  §6 keeps that negative result measurable — it is the justification for the
  architecture — but nothing in §1-§5 consults it, and no verdict anywhere in
  the GLM depends on a mod-2 quantity.

  Everything here is exact integer arithmetic: no floats, no tolerances.

      python3 glm_metrology.py        # runs the metrology self-audit
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "DIM_NAMES", "DIM_LONG_NAMES", "Dimension",
    "QUANTITIES", "ALIASES", "resolve", "quantity_names",
    "ParseError", "parse_expression",
    "EquationAudit", "audit_equation",
    "dimensional_collisions",
    "mod2_shadow", "mod2_would_accept", "mod2_collapse_report",
    "mod2_perturbation_sweep", "mod2_box_census", "metrology_audit",
]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  THE GROUP (Z^7, +)
# ══════════════════════════════════════════════════════════════════════════════

#: The seven SI base dimensions, in the order used everywhere in the GLM.
DIM_NAMES: Tuple[str, ...] = ("L", "M", "T", "I", "Th", "N", "J")
DIM_LONG_NAMES: Tuple[str, ...] = (
    "length", "mass", "time", "electric current",
    "thermodynamic temperature", "amount of substance", "luminous intensity",
)


@dataclass(frozen=True)
class Dimension:
    """
    A physical dimension as an exponent vector in Z^7.

    This is the primary object of the GLM: a concept's meaning, and the only
    state the system keeps.  Carriers, shadows and snap telemetry are all
    functions of it, computed on demand.

    The group operation is addition, and it is a homomorphism from the
    multiplicative structure of physical quantities:

        dim(A * B) = dim(A) + dim(B)
        dim(A / B) = dim(A) - dim(B)
        dim(A^n)   = n * dim(A)

    Equality is exact integer equality.  There is deliberately no mod-2 view
    on this class: the characteristic-2 shadow is an appendix diagnostic
    (`mod2_shadow`, §6) and no operation here can reach it.
    """

    exps: Tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.exps) != 7:
            raise ValueError("Dimension: 7 exponents required")
        if not all(isinstance(e, int) for e in self.exps):
            raise TypeError("Dimension: exponents must be integers")

    # ── constructors ─────────────────────────────────────────────────────────
    @staticmethod
    def of(*exps: int) -> "Dimension":
        return Dimension(tuple(exps))

    @staticmethod
    def zero() -> "Dimension":
        return Dimension((0,) * 7)

    @staticmethod
    def base(index: int) -> "Dimension":
        e = [0] * 7
        e[index] = 1
        return Dimension(tuple(e))

    # ── group operations ─────────────────────────────────────────────────────
    def __add__(self, other: "Dimension") -> "Dimension":
        return Dimension(tuple(a + b for a, b in zip(self.exps, other.exps)))

    def __sub__(self, other: "Dimension") -> "Dimension":
        return Dimension(tuple(a - b for a, b in zip(self.exps, other.exps)))

    def __neg__(self) -> "Dimension":
        return Dimension(tuple(-a for a in self.exps))

    def __mul__(self, n: int) -> "Dimension":
        if not isinstance(n, int):
            raise TypeError("Dimension can only be scaled by an integer power")
        return Dimension(tuple(a * n for a in self.exps))

    __rmul__ = __mul__

    # ── predicates and views ─────────────────────────────────────────────────
    @property
    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.exps)

    def max_abs(self) -> int:
        return max((abs(e) for e in self.exps), default=0)

    def l1(self) -> int:
        return sum(abs(e) for e in self.exps)

    def as_list(self) -> List[int]:
        return list(self.exps)

    def __str__(self) -> str:
        parts = []
        for name, e in zip(DIM_NAMES, self.exps):
            if e == 1:
                parts.append(name)
            elif e != 0:
                parts.append(f"{name}^{e}")
        return "*".join(parts) if parts else "1 (dimensionless)"

    def __repr__(self) -> str:
        return f"Dimension({list(self.exps)}) = {self}"


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE QUANTITY LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

def _D(L: int = 0, M: int = 0, T: int = 0, I: int = 0,
       Th: int = 0, N: int = 0, J: int = 0) -> Dimension:
    return Dimension((L, M, T, I, Th, N, J))


#: name -> (dimension, symbol, SI unit).  Names are the canonical keys; see
#: ALIASES for the additional spellings the resolver accepts.
QUANTITIES: Dict[str, Tuple[Dimension, str, str]] = {
    # ── the seven base quantities ────────────────────────────────────────────
    "length":                 (_D(L=1), "l", "m"),
    "mass":                   (_D(M=1), "m", "kg"),
    "time":                   (_D(T=1), "t", "s"),
    "current":                (_D(I=1), "I", "A"),
    "temperature":            (_D(Th=1), "Theta", "K"),
    "amount":                 (_D(N=1), "n", "mol"),
    "luminous_intensity":     (_D(J=1), "Iv", "cd"),

    # ── geometry and kinematics ──────────────────────────────────────────────
    "area":                   (_D(L=2), "A", "m^2"),
    "volume":                 (_D(L=3), "V", "m^3"),
    "wavenumber":             (_D(L=-1), "k", "1/m"),
    "speed":                  (_D(L=1, T=-1), "v", "m/s"),
    "acceleration":           (_D(L=1, T=-2), "a", "m/s^2"),
    "jerk":                   (_D(L=1, T=-3), "j", "m/s^3"),
    "frequency":              (_D(T=-1), "f", "Hz"),
    "angular_velocity":       (_D(T=-1), "omega", "rad/s"),
    "volumetric_flow":        (_D(L=3, T=-1), "Q", "m^3/s"),

    # ── mechanics ────────────────────────────────────────────────────────────
    "force":                  (_D(L=1, M=1, T=-2), "F", "N"),
    "momentum":               (_D(L=1, M=1, T=-1), "p", "kg*m/s"),
    "impulse":                (_D(L=1, M=1, T=-1), "J_imp", "N*s"),
    "energy":                 (_D(L=2, M=1, T=-2), "E", "J"),
    "torque":                 (_D(L=2, M=1, T=-2), "tau", "N*m"),
    "work":                   (_D(L=2, M=1, T=-2), "W", "J"),
    "power":                  (_D(L=2, M=1, T=-3), "P", "W"),
    "action":                 (_D(L=2, M=1, T=-1), "S", "J*s"),
    "angular_momentum":       (_D(L=2, M=1, T=-1), "L_ang", "kg*m^2/s"),
    "pressure":               (_D(L=-1, M=1, T=-2), "p_s", "Pa"),
    "stress":                 (_D(L=-1, M=1, T=-2), "sigma", "Pa"),
    "energy_density":         (_D(L=-1, M=1, T=-2), "u", "J/m^3"),
    "density":                (_D(L=-3, M=1), "rho", "kg/m^3"),
    "surface_density":        (_D(L=-2, M=1), "rho_A", "kg/m^2"),
    "specific_volume":        (_D(L=3, M=-1), "v_s", "m^3/kg"),
    "moment_of_inertia":      (_D(L=2, M=1), "I_m", "kg*m^2"),
    "surface_tension":        (_D(M=1, T=-2), "gamma", "N/m"),
    "spring_constant":        (_D(M=1, T=-2), "k_s", "N/m"),
    "dynamic_viscosity":      (_D(L=-1, M=1, T=-1), "mu", "Pa*s"),
    "kinematic_viscosity":    (_D(L=2, T=-1), "nu", "m^2/s"),
    "mass_flow":              (_D(M=1, T=-1), "m_dot", "kg/s"),
    "gravitational_constant": (_D(L=3, M=-1, T=-2), "G", "m^3/(kg*s^2)"),

    # ── electromagnetism ─────────────────────────────────────────────────────
    "charge":                 (_D(T=1, I=1), "q", "C"),
    "voltage":                (_D(L=2, M=1, T=-3, I=-1), "U", "V"),
    "resistance":             (_D(L=2, M=1, T=-3, I=-2), "R", "Ohm"),
    "conductance":            (_D(L=-2, M=-1, T=3, I=2), "G_e", "S"),
    "capacitance":            (_D(L=-2, M=-1, T=4, I=2), "C", "F"),
    "inductance":             (_D(L=2, M=1, T=-2, I=-2), "L_ind", "H"),
    "magnetic_flux":          (_D(L=2, M=1, T=-2, I=-1), "Phi_B", "Wb"),
    "magnetic_flux_density":  (_D(M=1, T=-2, I=-1), "B", "T"),
    "electric_field":         (_D(L=1, M=1, T=-3, I=-1), "E_f", "V/m"),
    "electric_displacement":  (_D(L=-2, T=1, I=1), "D", "C/m^2"),
    "magnetic_field_h":       (_D(L=-1, I=1), "H", "A/m"),
    "permittivity":           (_D(L=-3, M=-1, T=4, I=2), "epsilon", "F/m"),
    "permeability":           (_D(L=1, M=1, T=-2, I=-2), "mu_0", "H/m"),
    "resistivity":            (_D(L=3, M=1, T=-3, I=-2), "rho_e", "Ohm*m"),
    "conductivity":           (_D(L=-3, M=-1, T=3, I=2), "sigma_e", "S/m"),
    "charge_density":         (_D(L=-3, T=1, I=1), "rho_q", "C/m^3"),
    "current_density":        (_D(L=-2, I=1), "J_e", "A/m^2"),

    # ── thermodynamics ───────────────────────────────────────────────────────
    "entropy":                (_D(L=2, M=1, T=-2, Th=-1), "S_th", "J/K"),
    "heat_capacity":          (_D(L=2, M=1, T=-2, Th=-1), "C_th", "J/K"),
    "specific_heat_capacity": (_D(L=2, T=-2, Th=-1), "c_p", "J/(kg*K)"),
    "thermal_conductivity":   (_D(L=1, M=1, T=-3, Th=-1), "k_th", "W/(m*K)"),
    "heat_flux":              (_D(M=1, T=-3), "q_flux", "W/m^2"),
    "thermal_resistance":     (_D(L=-2, M=-1, T=3, Th=1), "R_th", "K/W"),
    "stefan_boltzmann":       (_D(M=1, T=-3, Th=-4), "sigma_SB", "W/(m^2*K^4)"),
    "boltzmann_constant":     (_D(L=2, M=1, T=-2, Th=-1), "k_B", "J/K"),
    "gas_constant":           (_D(L=2, M=1, T=-2, Th=-1, N=-1), "R_gas", "J/(mol*K)"),

    # ── chemistry ────────────────────────────────────────────────────────────
    "molar_mass":             (_D(M=1, N=-1), "M_molar", "kg/mol"),
    "concentration":          (_D(L=-3, N=1), "c_n", "mol/m^3"),
    "molar_volume":           (_D(L=3, N=-1), "V_m", "m^3/mol"),
    "catalytic_activity":     (_D(T=-1, N=1), "kat", "kat"),
    "avogadro_constant":      (_D(N=-1), "N_A", "1/mol"),
    "molar_energy":           (_D(L=2, M=1, T=-2, N=-1), "E_m", "J/mol"),

    # ── photometry and radiometry ────────────────────────────────────────────
    "luminous_flux":          (_D(J=1), "Phi_v", "lm"),
    "illuminance":            (_D(L=-2, J=1), "E_v", "lx"),
    "luminance":              (_D(L=-2, J=1), "L_v", "cd/m^2"),
    "luminous_energy":        (_D(T=1, J=1), "Q_v", "lm*s"),
    "luminous_exposure":      (_D(L=-2, T=1, J=1), "H_v", "lx*s"),
    "luminous_efficacy":      (_D(L=-2, M=-1, T=3, J=1), "K", "lm/W"),
    "radiant_flux":           (_D(L=2, M=1, T=-3), "Phi_e", "W"),
    "irradiance":             (_D(M=1, T=-3), "E_e", "W/m^2"),
    "radiance":               (_D(M=1, T=-3), "L_e", "W/(m^2*sr)"),
    "spectral_flux":          (_D(L=1, M=1, T=-3), "Phi_lambda", "W/m"),

    # ── radioactivity and dosimetry ──────────────────────────────────────────
    "activity":               (_D(T=-1), "A_r", "Bq"),
    "absorbed_dose":          (_D(L=2, T=-2), "D_dose", "Gy"),
    "dose_rate":              (_D(L=2, T=-3), "D_rate", "Gy/s"),
    "exposure_xray":          (_D(M=-1, T=1, I=1), "X", "C/kg"),

    # ── dimensionless ────────────────────────────────────────────────────────
    "dimensionless":          (_D(), "1", "1"),
    "angle":                  (_D(), "theta", "rad"),
    "solid_angle":            (_D(), "Omega", "sr"),
    "refractive_index":       (_D(), "n_r", "1"),
    "reynolds_number":        (_D(), "Re", "1"),
    "fine_structure":         (_D(), "alpha_fs", "1"),
}

#: extra spellings accepted by `resolve` (alias -> canonical name)
ALIASES: Dict[str, str] = {
    "l": "length", "len": "length", "distance": "length", "displacement": "length",
    "m": "mass", "t": "time", "duration": "time",
    "i": "current", "electric_current": "current",
    "theta": "temperature", "temp": "temperature",
    "n": "amount", "mol": "amount", "substance": "amount",
    "j": "luminous_intensity", "candela": "luminous_intensity",
    "v": "speed", "velocity": "speed", "c": "speed",
    "a": "acceleration", "g": "acceleration",
    "f": "force", "e": "energy", "ke": "energy", "pe": "energy", "heat": "energy",
    "p": "power", "w": "work", "s": "action", "hbar": "action", "h": "action",
    "q": "charge", "u": "voltage", "emf": "voltage", "potential": "voltage",
    "r": "resistance", "c_cap": "capacitance", "phi_b": "magnetic_flux",
    "b": "magnetic_flux_density", "rho": "density",
    "phi_v": "luminous_flux", "lumen": "luminous_flux",
    "e_v": "illuminance", "lux": "illuminance", "q_v": "luminous_energy",
    "one": "dimensionless", "scalar": "dimensionless", "unitless": "dimensionless",
}


def quantity_names() -> List[str]:
    return sorted(QUANTITIES)


def resolve(key: str) -> Optional[Dimension]:
    """Resolve a quantity name, alias or symbol to its Dimension."""
    k = key.strip().lower()
    if k in QUANTITIES:
        return QUANTITIES[k][0]
    if k in ALIASES:
        return QUANTITIES[ALIASES[k]][0]
    for name, (dim, sym, _unit) in QUANTITIES.items():
        if sym.lower() == k:
            return dim
    return None


def describe(key: str) -> Optional[str]:
    k = key.strip().lower()
    name = k if k in QUANTITIES else ALIASES.get(k)
    if name is None:
        return None
    dim, sym, unit = QUANTITIES[name]
    return f"{name} [{sym}] = {dim}  ({unit})"


# ══════════════════════════════════════════════════════════════════════════════
# §3.  EXPRESSION PARSER
# ══════════════════════════════════════════════════════════════════════════════

class ParseError(ValueError):
    """Raised when an expression cannot be parsed or a name is unknown."""


_OPS = {"*", "/", "^", "(", ")"}


def _tokenise(text: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    # normalise the typographic operators used in earlier GLM versions
    text = text.replace("\u00b7", "*").replace("\u00d7", "*").replace("\u00f7", "/")
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch in _OPS:
            tokens.append(ch)
            i += 1
        elif ch == "-" or ch.isdigit():
            j = i + 1
            while j < len(text) and text[j].isdigit():
                j += 1
            tokens.append(text[i:j])
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tokens.append(text[i:j])
            i = j
        else:
            raise ParseError(f"unexpected character {ch!r} in {text!r}")
    return tokens


class _Parser:
    """
    Grammar:
        expr   := term (('*' | '/') term)*
        term   := factor ('^' integer)?
        factor := NAME | INTEGER | '(' expr ')'

    An integer literal is dimensionless (numeric prefactors do not affect
    dimensional bookkeeping); an exponent must be an integer literal, so the
    result always lies in Z^7.
    """

    def __init__(self, tokens: Sequence[str]) -> None:
        self.tokens = list(tokens)
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> str:
        tok = self.peek()
        if tok is None:
            raise ParseError("unexpected end of expression")
        self.pos += 1
        return tok

    def parse(self) -> Dimension:
        d = self.expr()
        if self.pos != len(self.tokens):
            raise ParseError(f"trailing input at token {self.tokens[self.pos]!r}")
        return d

    def expr(self) -> Dimension:
        d = self.term()
        while self.peek() in ("*", "/"):
            op = self.next()
            rhs = self.term()
            d = d + rhs if op == "*" else d - rhs
        return d

    def term(self) -> Dimension:
        d = self.factor()
        if self.peek() == "^":
            self.next()
            tok = self.next()
            try:
                power = int(tok)
            except ValueError:
                raise ParseError(f"exponent must be an integer, got {tok!r}")
            d = d * power
        return d

    def factor(self) -> Dimension:
        tok = self.next()
        if tok == "(":
            d = self.expr()
            if self.next() != ")":
                raise ParseError("missing closing parenthesis")
            return d
        if tok == ")":
            raise ParseError("unexpected ')'")
        if tok.lstrip("-").isdigit():
            return Dimension.zero()          # numeric prefactor: dimensionless
        dim = resolve(tok)
        if dim is None:
            raise ParseError(f"unknown quantity {tok!r}")
        return dim


def parse_expression(text: str) -> Dimension:
    """Parse a product/quotient/power expression into its Dimension."""
    if not text or not text.strip():
        raise ParseError("empty expression")
    return _Parser(_tokenise(text)).parse()


# ══════════════════════════════════════════════════════════════════════════════
# §4.  EQUATION AUDIT — the exact verdict, and nothing else
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EquationAudit:
    """
    The result of checking one proposed equation for dimensional homogeneity.

    The verdict is exact equality of the two meanings in (Z^7, +).  That is
    the only verdict the system issues: there is no second, approximate
    opinion carried alongside it.  What a characteristic-2 carrier would have
    said is measurable in §6, but it is not part of an audit.
    """

    label: str
    lhs_text: str
    rhs_text: str
    lhs_dim: Dimension
    rhs_dim: Dimension

    @property
    def accepted(self) -> bool:
        """Exact verdict in (Z^7, +): dimensional homogeneity."""
        return self.lhs_dim == self.rhs_dim

    @property
    def residual(self) -> Dimension:
        return self.lhs_dim - self.rhs_dim

    def summary(self) -> str:
        head = "ACCEPT" if self.accepted else "REJECT"
        return (f"[{head}] {self.label or (self.lhs_text + ' = ' + self.rhs_text)}"
                f"\n         {self.lhs_text} : {self.lhs_dim}"
                f"\n         {self.rhs_text} : {self.rhs_dim}")


def audit_equation(lhs: str, rhs: str, label: str = "") -> EquationAudit:
    """Parse both sides and compare them exactly in (Z^7, +)."""
    return EquationAudit(label, lhs, rhs, parse_expression(lhs), parse_expression(rhs))


# ══════════════════════════════════════════════════════════════════════════════
# §5.  LIBRARY-LEVEL REPORTS
# ══════════════════════════════════════════════════════════════════════════════

def dimensional_collisions() -> Dict[str, List[str]]:
    """
    Named quantities that share a dimension vector.  Dimensional analysis
    cannot separate these (energy and torque, illuminance and luminance,
    frequency and activity, ...), and the GLM does not pretend to: it reports
    the collision instead of guessing.
    """
    buckets: Dict[Tuple[int, ...], List[str]] = {}
    for name, (dim, _s, _u) in QUANTITIES.items():
        buckets.setdefault(dim.exps, []).append(name)
    return {str(Dimension(k)): sorted(v) for k, v in sorted(buckets.items())
            if len(v) > 1}


# ══════════════════════════════════════════════════════════════════════════════
# §6.  APPENDIX — THE REJECTED F_2 CARRIER
# ══════════════════════════════════════════════════════════════════════════════
#
#  Nothing below this line is part of the system.  These functions measure the
#  design that the GLM rejected — a bit pattern composed by XOR, i.e. an
#  F_2-linear encoder of (Z^7,+) — so that the reason for making the integer
#  vector primary and the bit pattern derived stays a measurement rather than
#  an assertion.  No `Dimension`, `EquationAudit`, `Concept` or reasoner
#  verdict calls anything in this section.
# ──────────────────────────────────────────────────────────────────────────────

def mod2_shadow(dim: Dimension) -> Tuple[int, ...]:
    """
    The characteristic-2 shadow of a meaning: the most an F_2 carrier can see.

    Diagnostic only.  It is a module-level function and not a method of
    `Dimension` precisely so that it cannot be reached from the meaning layer
    by accident.
    """
    return tuple(e % 2 for e in dim.exps)


def mod2_would_accept(a: Dimension, b: Dimension) -> bool:
    """Would an XOR / F_2 carrier have called these two meanings equal?"""
    return mod2_shadow(a) == mod2_shadow(b)


def mod2_collapse_report() -> Dict[str, object]:
    """
    Measure the mod-2 ceiling over the whole library.

    For every ordered pair of distinct named dimensions (x, y) we ask: does an
    XOR substrate consider them equal?  Each such pair is one equation an
    F_2-linear checker would wrongly accept.  The exact (Z^7, +) checker
    accepts none of them.
    """
    dims = sorted({q[0].exps for q in QUANTITIES.values()})
    n = len(dims)
    pairs = 0
    collapsed = 0
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
            if tuple(e % 2 for e in dims[i]) == tuple(e % 2 for e in dims[j]):
                collapsed += 1
    return {
        "distinct_dimensions": n,
        "unordered_pairs": pairs,
        "pairs_indistinguishable_mod2": collapsed,
        "mod2_false_positive_rate": collapsed / pairs if pairs else 0.0,
        "exact_false_positive_rate": 0.0,
        "distinct_mod2_shadows": len({tuple(e % 2 for e in d) for d in dims}),
    }


def mod2_perturbation_sweep(shift: int = 2) -> Dict[str, object]:
    """
    The mod-2 ceiling on a family with a well-defined denominator.

    Earlier GLM drafts quoted "100% precision versus 89% for the mod-2
    substrate over 6,793 equation pairs" without saying how the 6,793 pairs
    were generated, so the number could not be reproduced.  This is a
    reproducible replacement.

    Take every named quantity q and every one of the seven exponent slots i,
    and form the *false* equation

        q  =  q * (base_i)^(+/- shift),      shift even (default 2),

    i.e. compare dim(q) with dim(q) + 2u for a unit vector u.  Every such
    equation is dimensionally false, so a perfect checker rejects all of them.
    By Proposition 1 every XOR/F_2 substrate accepts all of them: the
    theoretical false-positive rate of a mod-2 checker on this family is
    exactly 1, and the measurement below confirms it on the shipped library.

    `named_traps` counts the sub-family where the perturbed dimension is
    itself a named library quantity — the E = m c^4 phenomenon, where the
    false equation is one a user might actually write.
    """
    if shift % 2 != 0:
        raise ValueError("mod2_perturbation_sweep: shift must be even")
    by_dim = {q[0].exps: name for name, q in QUANTITIES.items()}
    total = mod2_accepts = exact_accepts = named = 0
    examples: List[str] = []
    for name, (dim, _s, _u) in sorted(QUANTITIES.items()):
        for i in range(len(DIM_NAMES)):
            for sgn in (+1, -1):
                exps = list(dim.exps)
                exps[i] += sgn * shift
                other = Dimension(tuple(exps))
                total += 1
                if mod2_would_accept(dim, other):
                    mod2_accepts += 1
                if dim.exps == other.exps:
                    exact_accepts += 1
                if other.exps in by_dim:
                    named += 1
                    if len(examples) < 8:
                        examples.append(f"{name} = {by_dim[other.exps]}")
    return {
        "shift": shift,
        "false_equations": total,
        "mod2_accepted": mod2_accepts,
        "mod2_false_positive_rate": mod2_accepts / total if total else 0.0,
        "exact_accepted": exact_accepts,
        "exact_false_positive_rate": exact_accepts / total if total else 0.0,
        "named_traps": named,
        "named_trap_examples": examples,
    }


def mod2_box_census(bound: int = 2) -> Dict[str, object]:
    """
    The mod-2 ceiling over a whole exponent box, counted exactly.

    Let B = [-bound, bound]^7 (all exponent vectors with |d_i| <= bound).  Two
    vectors are confusable by an XOR substrate exactly when they share a mod-2
    shadow, so the number of confusable unordered pairs is

        sum over shadows s of  C(n_s, 2),

    where n_s is the number of box vectors with shadow s.  This is computed
    from the per-coordinate even/odd counts rather than by enumerating pairs,
    so it is exact and instant even for large boxes.  The exact (Z^7, +)
    checker confuses none of them.
    """
    evens = len([e for e in range(-bound, bound + 1) if e % 2 == 0])
    odds = (2 * bound + 1) - evens
    # Each mod-2 shadow s in F_2^7 has n_s = prod_i (evens if s_i = 0 else odds).
    total_pairs = 0
    shadow_count = 0
    for mask in range(1 << len(DIM_NAMES)):
        n_s = 1
        for i in range(len(DIM_NAMES)):
            n_s *= odds if (mask >> i) & 1 else evens
        if n_s:
            shadow_count += 1
        total_pairs += n_s * (n_s - 1) // 2
    size = (2 * bound + 1) ** len(DIM_NAMES)
    all_pairs = size * (size - 1) // 2
    return {
        "bound": bound,
        "box_size": size,
        "unordered_pairs": all_pairs,
        "pairs_confused_mod2": total_pairs,
        "mod2_false_positive_rate": total_pairs / all_pairs if all_pairs else 0.0,
        "pairs_confused_exactly": 0,
        "occupied_shadows": shadow_count,
    }


def metrology_audit() -> Dict[str, object]:
    return {
        "quantities": len(QUANTITIES),
        "aliases": len(ALIASES),
        "collisions": dimensional_collisions(),
        "mod2_collapse": mod2_collapse_report(),
        "mod2_perturbation": mod2_perturbation_sweep(),
        "mod2_box": mod2_box_census(),
    }


def _print_audit() -> Dict[str, object]:
    a = metrology_audit()
    print("=" * 78)
    print("  GLM MEANING SELF-AUDIT   (Z^7, +), the primary object")
    print("=" * 78)
    print(f"\n  library: {a['quantities']} named quantities, {a['aliases']} aliases")
    m = a["mod2_collapse"]
    print("\n[Appendix: the rejected F_2 carrier, measured over the library]")
    print(f"  distinct dimension vectors      : {m['distinct_dimensions']}")
    print(f"  distinct mod-2 shadows          : {m['distinct_mod2_shadows']}")
    print(f"  unordered pairs                 : {m['unordered_pairs']}")
    print(f"  pairs an XOR substrate confuses : {m['pairs_indistinguishable_mod2']}"
          f"  ({100 * m['mod2_false_positive_rate']:.1f}%)")
    print("  pairs (Z^7,+) confuses          : 0  (0.0%)")
    pert = a["mod2_perturbation"]
    print("\n[Exponent-perturbation family  q  vs  q * base^(+-2)]")
    print(f"  false equations generated       : {pert['false_equations']}")
    print(f"  accepted by an XOR substrate    : {pert['mod2_accepted']}"
          f"  ({100 * pert['mod2_false_positive_rate']:.1f}%)")
    print(f"  accepted by (Z^7,+)             : {pert['exact_accepted']}  (0.0%)")
    print(f"  of which are named-quantity traps: {pert['named_traps']}"
          f"   e.g. {', '.join(pert['named_trap_examples'][:3])}")
    box = a["mod2_box"]
    print(f"\n[Whole exponent box [-{box['bound']},{box['bound']}]^7, counted exactly]")
    print(f"  vectors                         : {box['box_size']:,}")
    print(f"  unordered pairs                 : {box['unordered_pairs']:,}")
    print(f"  pairs an XOR substrate confuses : {box['pairs_confused_mod2']:,}"
          f"  ({100 * box['mod2_false_positive_rate']:.2f}%)")
    print("\n[Dimensional collisions inside the library (honest ambiguity)]")
    for dim, names in list(a["collisions"].items()):
        print(f"  {dim:<28} {', '.join(names)}")
    print("\n[Worked examples]")
    for lhs, rhs, label in (
        ("energy", "mass*speed^2", "E = m c^2"),
        ("energy", "mass*speed^4", "E = m c^4  (mod-2 trap)"),
        ("power", "voltage*current", "P = U I"),
        ("illuminance", "luminous_flux/area", "E_v = Phi_v / A"),
        ("illuminance", "luminous_flux*area", "E_v = Phi_v A  (mod-2 trap)"),
    ):
        print("  " + audit_equation(lhs, rhs, label).summary().replace("\n", "\n  "))
    print("=" * 78)
    return a


if __name__ == "__main__":
    _print_audit()
