"""``glm_universal.runtime.symbolic_outside`` -- the class-S (and class-T)
outside questions of Phase 89, read as laws in letters (Phase 98,
``studies/SYMBOLIC_PARAMETERS_STUDY.md``).

Each frame recognises a *kind* of situation and its givens (which body
rolls, which gas expands and how far, which levels a particle may occupy,
where a disturbance enters a loop, ...), writes the laws that govern it as
equations in letters, and hands them to :mod:`glm_universal.reasoning.
symbolic` -- the declared substitution, the derivative through atoms, the
geometric series, the entailment by exact division.  No answer is stored:
change a given and the laws change, and so does the answer
(:data:`glm_universal.evaluation.symbolic_cases.VARIANTS`).

Column 3 is a stand-alone script that never calls the symbolic layer:

* for a system of laws, the laws **as written** are evaluated at rational
  points with the solution substituted (roots carried as formal generators
  reduced by their own relations), and the **printed** answer is
  transliterated and compared (:func:`glm_universal.reasoning.symbolic.
  system_script`);
* for a statistical sum, the thermal average is recomputed by brute force
  over every microstate of 1, 2 and 3 particles;
* for a derivative or an integral, dual numbers differentiate the laws and
  the antiderivative is checked against the integrand;
* for a series, the finite geometric identity and the tail bound are checked
  exactly; for a spectrum, Gaussian rationals on the unit circle;
* for crystal-field energies, every placement of the electrons is
  enumerated and the ground state taken;
* for the transcendental root, the arctangent and pi are bracketed by their
  own alternating series and the sign change is checked at both ends.

Where a question also asks *why* (the physical origin of the body effect,
the rotor at cryogenic temperatures) or for a drawing (the splitting
diagram), the computed part is answered and the rest is named as refused --
``EXPLANATION`` or ``DESIGN`` -- in the reading itself.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..reasoning import symbolic as S
from .question_frames import Frame, Reading

__all__ = ["OUTSIDE_S_FRAMES", "MUTATE", "laws_reading", "arctan_bounds",
           "pi_bounds"]

#: Set by :func:`mutated_reading`: every answerer alters its claimed value
#: (the column-3 control).
MUTATE = [False]


def _mut() -> Fraction:
    return Fraction(2) if MUTATE[0] else Fraction(1)


def _frac_py(q: Fraction) -> str:
    return f"F({q.numerator}, {q.denominator})"


def _c(q: Fraction) -> str:
    """A coefficient as the formulas print it."""
    q = Fraction(q)
    if q.denominator == 1:
        return str(q.numerator)
    return f"({q.numerator}/{q.denominator})"


# ===========================================================================
# 0.  LAWS -> SOLUTION -> READING
# ===========================================================================

def laws_reading(frame: str, laws: Sequence[str], targets: Sequence[str],
                 params: Sequence[str],
                 printed: Dict[str, Tuple[str, str]], col1: str,
                 claims: Sequence[str] = (), disputes: Sequence[str] = (),
                 tail: str = "", backing: str = "", label: str = "",
                 show: Optional[Sequence[str]] = None) -> Reading:
    """Solve ``laws`` for ``targets``; ``printed[t] = (label, text)``
    overrides how a target is printed (the script checks the printed text).
    ``show`` orders the targets in the answer (default: all)."""
    ctx = S.Context()
    eqs = [S.parse_equation(x, ctx) for x in laws]
    syms = set()
    for lhs, rhs in eqs:
        syms |= lhs.vars() | rhs.vars()
    syms -= set(ctx.atoms) | set(S.RADICALS)
    unknowns = syms - set(params) - S.CONSTANTS
    sol = S.solve_system(eqs, unknowns, list(targets))
    ans: Dict[str, str] = {}
    shown = []
    for t in (show if show is not None else targets):
        if t in printed:
            lab, txt = printed[t]
        else:
            lab, txt = t, sol.root_text(t).split(" = ", 1)[1]
        ans[t] = txt
        shown.append(f"{lab} = {txt}")
    for t in targets:
        if t not in ans:
            ans[t] = printed[t][1] if t in printed else \
                sol.root_text(t).split(" = ", 1)[1]
    value = "; ".join(shown) + tail
    steps = "; ".join(s.text() for s in sol.steps)
    script = S.system_script(list(laws), sol, ctx, list(params), ans,
                             label=label or frame.upper(),
                             scale_first=Fraction(2) if MUTATE[0] else None,
                             claims=claims)
    return Reading(frame, True, value, col1,
                   "laws: " + "; ".join(laws) + " || " + steps, script,
                   backing=backing or "reasoning.symbolic.solve_system "
                                      "(declared substitution)",
                   disputes=tuple(disputes))


# ===========================================================================
# 1.  THE ROLLING BODY (O010)
# ===========================================================================

#: moment of inertia factor k in I = k M R^2, by the body's name.
BODIES: Tuple[Tuple[str, Fraction], ...] = (
    ("hollow cylinder", Fraction(1)), ("thin hoop", Fraction(1)),
    ("hoop", Fraction(1)), ("ring", Fraction(1)),
    ("hollow sphere", Fraction(2, 3)), ("spherical shell", Fraction(2, 3)),
    ("solid sphere", Fraction(2, 5)), ("solid cylinder", Fraction(1, 2)),
    ("disk", Fraction(1, 2)), ("disc", Fraction(1, 2)),
)


def _m_rolling(t: str) -> Optional[dict]:
    if "rolls without slipping" not in t or "inclin" not in t:
        return None
    for name, k in BODIES:
        if name in t:
            return {"body": name, "k": k}
    return None


def _a_rolling(g: dict) -> Reading:
    k = g["k"]
    laws = ["M*a = M*g*sin(theta) - f", "f*R = I*alpha",
            f"I = {_c(k)}*M*R^2", "a = alpha*R", "N = M*g*cos(theta)",
            "f = mu*N"]
    mu = k / (1 + k)
    return laws_reading(
        "rolling_body", laws, ["a", "mu"], ["M", "g", "theta", "R"],
        {"mu": ("mu_min", f"{_c(mu)}*tan(theta)")},
        f"For a {g['body']} (I = {k} M R^2): Newton's second law along the "
        "incline, the torque of static friction about the centre, the "
        "rolling constraint a = alpha R and the normal force; the friction "
        "needed is f = mu N at the threshold, so the least coefficient is "
        "f/N.",
        backing="reasoning.symbolic.solve_system over Newton's laws for "
                "translation and rotation")


# ===========================================================================
# 2.  THE ADIABATIC EXPANSION (O011)
# ===========================================================================

def _decimal_root(c: Fraction, q: int, places: int = 6) -> str:
    """The positive c^(1/q) to ``places`` decimals, truncated (exact)."""
    scale = 10 ** places
    n = c.numerator * scale ** q // c.denominator
    lo = 0
    hi = 1
    while hi ** q <= n:
        hi *= 2
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** q <= n:
            lo = mid
        else:
            hi = mid - 1
    return f"{lo // scale}.{str(lo % scale).zfill(places)}"


def _m_adiabatic(t: str) -> Optional[dict]:
    if "adiabatic" not in t or "work" not in t:
        return None
    gas = "monatomic" if "monatomic" in t else \
        "diatomic" if "diatomic" in t else None
    m = re.search(r"final volume (?:of )?(\d+)\s*v_0", t)
    if not gas or not m:
        return None
    n = Fraction(1)
    mm = re.search(r"(\d+) moles", t)
    if mm:
        n = Fraction(int(mm.group(1)))
    return {"gas": gas, "r": int(m.group(1)), "n": n}


def _a_adiabatic(g: dict) -> Reading:
    cv = Fraction(3, 2) if g["gas"] == "monatomic" else Fraction(5, 2)
    gm1 = 1 / cv                          # gamma - 1 = R / C_v
    p, q = gm1.numerator, gm1.denominator
    r, n = g["r"], g["n"]
    laws = [f"T1^{q}*({r}*V0)^{p} = T0^{q}*V0^{p}",
            f"W = {_c(n * cv)}*R*(T0 - T1)"]
    rd = _decimal_root(Fraction(1, r ** p), q, 6)
    coef = n * cv * (1 - Fraction(rd))
    return laws_reading(
        "adiabatic_work", laws, ["W"], ["T0", "R", "V0"], {},
        f"For an ideal {g['gas']} gas C_v = {cv} R and gamma - 1 = {gm1}; "
        f"along a reversible adiabat T V^(gamma-1) is constant, written "
        f"without a fractional power as T^{q} V^{p} = constant; with no heat "
        f"exchanged the work done by the gas is the fall in internal "
        f"energy, W = n C_v (T0 - T1).",
        tail=f" (= {n * cv}*(1 - {rd}...)*R*T0, about "
             f"{_dec_places(coef)}*R*T0)",
        backing="reasoning.symbolic.solve_system + radical atom "
                f"{r}^(-{p}/{q}) with its relation")


def _dec_places(q: Fraction, places: int = 4) -> str:
    s = "-" if q < 0 else ""
    q = abs(q)
    n = q.numerator * 10 ** places // q.denominator
    return f"{s}{n // 10 ** places}.{str(n % 10 ** places).zfill(places)}"


# ===========================================================================
# 3.  GAUSS'S LAW FOR THE COAXIAL SHELL (O012)
# ===========================================================================

def _m_coax(t: str) -> Optional[dict]:
    if "line charge density" not in t or "coaxial" not in t or \
            "gauss" not in t:
        return None
    m = re.search(r"net line charge density (\S+?)[.,]", t)
    if m:
        name = {"μ": "mu", "mu": "mu"}.get(m.group(1), None)
        if name is None:
            return None
        return {"shell": name}
    if "uncharged" in t:
        return {"shell": None}
    return None


def _a_coax(g: dict) -> Reading:
    sh = g["shell"]
    Q = "lambda" if sh is None else f"(lambda + {sh})"
    laws = ["E1*2*pi*r*L = lambda*L/epsilon0",
            "lambda*L + sigma_in*2*pi*a*L = 0",
            f"sigma_in*2*pi*a + sigma_out*2*pi*b = {sh or 0}",
            f"E3*2*pi*r*L = {Q}*L/epsilon0"]
    params = ["r", "L", "a", "b", "epsilon0", "lambda"] + ([sh] if sh else [])
    out = f"{Q}/(2*pi*epsilon0*r)"
    return laws_reading(
        "gauss_coax", laws, ["E1", "E3", "sigma_in", "sigma_out"], params,
        {"E1": ("for r < a: E", "lambda/(2*pi*epsilon0*r)"),
         "E3": ("for r > b: E", out),
         "sigma_in": ("sigma_in", "-lambda/(2*pi*a)"),
         "sigma_out": ("sigma_out", f"{Q}/(2*pi*b)")},
        "Gauss's law on a coaxial cylinder of radius r and length L: the "
        "flux E 2 pi r L equals the enclosed charge over epsilon0.  Inside "
        "the conducting material the field is zero in electrostatic "
        "equilibrium (the conductor's own law, not derived), so a Gaussian "
        "cylinder there encloses no net charge: the inner surface carries "
        "-lambda per length, and the shell's net charge fixes the outer "
        "surface.",
        tail="; for a < r < b: E = 0 (inside the conductor); the field is "
             "radial",
        show=["E1", "E3", "sigma_in", "sigma_out"],
        backing="reasoning.symbolic.solve_system over Gauss's law per "
                "region")


# ===========================================================================
# 4.  THE FUSED PARTICLE (O014)
# ===========================================================================

def _m_fusion(t: str) -> Optional[dict]:
    if "rest mass" not in t or "collides" not in t or \
            not re.search(r"fuse|composite", t):
        return None
    k = 1
    m = re.search(r"particle of rest mass (\d+)\s*m_0 at rest", t)
    if m:
        k = int(m.group(1))
    elif "identical particle" not in t:
        return None
    return {"k": k, "stationary": "stationary" in t}


def _a_fusion(g: dict) -> Reading:
    k = g["k"]
    laws = [f"E = gamma*m0*c^2 + {k}*m0*c^2", "p = gamma*m0*v",
            "v^2 = c^2*(1 - 1/gamma^2)", "M^2*c^4 = E^2 - p^2*c^2",
            "V*E = p*c^2"]
    disputes = []
    if g["stationary"]:
        disputes.append(
            "the composite cannot be stationary: the incoming momentum "
            "gamma*m0*v is not zero and is conserved, so the composite "
            f"moves with V = gamma*v/(gamma + {k}); its rest mass M is "
            "frame-independent and is the answer")
    return laws_reading(
        "fusion_mass", laws, ["M", "V"], ["m0", "gamma", "c"], {},
        "Energy and momentum are both conserved: E = gamma m0 c^2 + "
        f"{k} m0 c^2 and p = gamma m0 v, with v^2 = c^2 (1 - 1/gamma^2) from "
        "the Lorentz factor; the composite's rest mass is the invariant "
        "M^2 c^4 = E^2 - p^2 c^2, and its velocity is p c^2 / E.",
        disputes=disputes,
        backing="reasoning.symbolic.solve_system (M through its square, the "
                "positive root)")


# ===========================================================================
# 5.  CONDUCTOR BOUNDARY ANGLES (O008)
# ===========================================================================

def _m_interface(t: str) -> Optional[dict]:
    if "tan" not in t or "boundary" not in t or "theta_1" not in t:
        return None
    if "permittivit" in t:
        return {"F": "E", "m": "epsilon", "tang": "E", "norm": "D"}
    if "permeabilit" in t:
        return {"F": "H", "m": "mu", "tang": "H", "norm": "B"}
    return None


def _a_interface(g: dict) -> Reading:
    F, m = g["F"], g["m"]
    laws = [f"{F}1*sin(theta1) = {F}2*sin(theta2)",
            f"{m}1*{F}1*cos(theta1) = {m}2*{F}2*cos(theta2)"]
    claim = f"tan(theta1)/tan(theta2) = {m}1/{m}2"
    ctx = S.Context()
    eqs = [S.parse_equation(x, ctx) for x in laws]
    rels: List[S.RF] = []
    S.solve_system(eqs, {f"{F}2"}, [f"{F}2"], relations=rels)
    c = S.parse_equation(claim, ctx)
    q = S.entails(rels, c)
    if q is None:
        return Reading("interface_angles", False, "the relation does not "
                       "follow", "", "", "print('VERIFIED False')",
                       code="NOT_ENTAILED", backing="reasoning.symbolic")
    rel_text = S.to_text(rels[0]) if rels else "0"
    r = laws_reading(
        "interface_angles", laws, [f"{F}2", f"{m}2"],
        [f"{F}1", f"{m}1", "theta1", "theta2"], {},
        f"Tangential {g['tang']} is continuous across the interface and, "
        f"with no free surface source, so is normal {g['norm']} = {m} "
        f"{F}.  Eliminating {F}2 between the two boundary equations "
        f"leaves the relation {rel_text} = 0 among the angles and the "
        f"materials; "
        + (f"the claimed ratio minus its right side has numerator "
           f"({S.to_text(q[1])}) times that relation"
           if q[0] == "multiple" else
           f"that relation is ({S.to_text(q[1])}) times the numerator of the "
           f"claimed ratio minus its right side, so with "
           f"{S.to_text(q[1])} != 0 the numerator vanishes")
        + "; so the claim follows wherever the angles' sines and cosines "
          "are nonzero.",
        claims=[claim],
        backing="reasoning.symbolic.entails (exact division by the derived "
                "relation)")
    r.value = f"proved: {claim} (" + r.value + ")"
    return r


# ===========================================================================
# 6.  THE CLOSED LOOP WITH A DISTURBANCE (O033)
# ===========================================================================

def _m_loop(t: str) -> Optional[dict]:
    if "negative feedback" not in t or "disturbance" not in t or \
            "g_d" not in t:
        return None
    if "after the actuator" in t:
        return {"where": "actuator"}
    if "process output" in t or "at the output" in t:
        return {"where": "output"}
    return None


def _a_loop(g: dict) -> Reading:
    if g["where"] == "actuator":
        plant = "Y = Gp*(Gv*U + Gd*D)"
        num = "Gd*Gp"
    else:
        plant = "Y = Gp*Gv*U + Gd*D"
        num = "Gd"
    laws = ["E = -Gm*Y", "U = Gc*E", plant, "H*D = Y"]
    return laws_reading(
        "disturbance_loop", laws, ["H"],
        ["Gc", "Gv", "Gp", "Gm", "Gd", "D"],
        {"H": ("Y/D", f"{num}/(1 + Gc*Gv*Gp*Gm)")},
        "With the setpoint at zero the error is E = -Gm Y, the controller "
        "output U = Gc E, and the disturbance passes Gd into the loop "
        + ("after the actuator, so the process sees Gv U + Gd D"
           if g["where"] == "actuator" else "at the process output")
        + "; eliminating E and U leaves Y in terms of D alone.",
        backing="reasoning.symbolic.solve_system over the block equations")


# ===========================================================================
# 7.  THE BODY EFFECT (O007)
# ===========================================================================

def _m_body(t: str) -> Optional[dict]:
    if "body effect" in t and "threshold" in t:
        return {"channel": "n" if "n-channel" in t else "?"}
    return None


def _a_body(g: dict) -> Reading:
    laws = ["V_t = V_FB + 2*phi_F + K*sqrt(2*phi_F + V_SB)/C_ox",
            "V_t0 = V_FB + 2*phi_F + K*sqrt(2*phi_F)/C_ox",
            "K = gamma*C_ox", "dV_t = V_t - V_t0"]
    r = laws_reading(
        "body_effect", laws, ["dV_t"],
        ["V_FB", "phi_F", "V_SB", "C_ox", "gamma"],
        {"dV_t": ("Delta V_t = V_t - V_t0",
                  "gamma*(sqrt(2*phi_F + V_SB) - sqrt(2*phi_F))")},
        "The threshold is V_t = V_FB + 2 phi_F + Q_B / C_ox, where the "
        "depletion charge at inversion is Q_B = sqrt(2 q eps_s N_A "
        "(2 phi_F + V_SB)); writing gamma = sqrt(2 q eps_s N_A)/C_ox and "
        "subtracting the threshold at V_SB = 0 gives the shift.",
        tail=", with gamma = sqrt(2*q*epsilon_s*N_A)/C_ox; since "
             "2*phi_F + V_SB > 2*phi_F when V_SB > 0, the shift is "
             "positive: the threshold rises.  The physical explanation "
             "asked for is refused (EXPLANATION): no exact frame answers "
             "why",
        backing="reasoning.symbolic.solve_system with sqrt atoms")
    return r


# ===========================================================================
# 8.  THE TWO-LEVEL (n-LEVEL) PARTICLES (O016)
# ===========================================================================

def _m_levels(t: str) -> Optional[dict]:
    if "partition function" not in t or "distinguishable" not in t or \
            "energy levels" not in t:
        return None
    seg = t.split("energy levels", 1)[1].split(".")[0]
    seg = seg.replace(":", " ")
    items = [x.strip() for x in re.split(r",|\bor\b|\band\b", seg)
             if x.strip()]
    levels = []
    for it in items:
        if it == "0":
            levels.append(0)
            continue
        m = re.fullmatch(r"(\d*)\s*(?:ε|epsilon)", it)
        if not m:
            return None
        levels.append(int(m.group(1) or 1))
    if len(levels) < 2 or 0 not in levels or len(set(levels)) != len(levels):
        return None
    return {"levels": tuple(sorted(levels))}


def _e_term(n: int, sign: str = "-") -> str:
    if n == 0:
        return "1"
    lead = "" if n == 1 else f"{n}*"
    return f"e^({sign}{lead}epsilon/(k*T))"


def _a_levels(g: dict) -> Reading:
    levels = g["levels"]
    ctx = S.Context()
    x = S.parse("exp(-beta*epsilon)", ctx)
    Z1 = sum((x ** n for n in levels), S.RF(S.Poly()))
    dZ = S.diff(Z1, "beta", ctx)
    N = S.parse("N", ctx)
    U = -N * dZ / Z1
    xname = next(iter(x.num.vars()))
    y = S.RF(S.Poly.var("y"))
    Uy = U.num.reduce_power(xname, 1, 1 / y) / U.den.reduce_power(
        xname, 1, 1 / y)
    Uy = Uy * _mut()
    u_text = re.sub(r"\by\b", _e_term(1, ""), S.to_text(Uy))
    z_text = "(" + " + ".join(_e_term(n) for n in levels) + ")^N"
    names = {"y": "y", "N": "N", "epsilon": "epsilon"}
    upy = S.to_python(Uy, names)
    lv = list(levels)
    script = (
        "from fractions import Fraction as F\nfrom itertools import product\n"
        f"LEVELS = {lv!r}\n"
        f"def U_claim(y, N, epsilon):\n    return {upy}\n"
        "checked = 0\n"
        "for x0 in (F(1, 3), F(2, 5), F(3, 7), F(5, 6)):\n"
        "    for eps in (F(1), F(3, 2), F(2, 7)):\n"
        "        z1 = sum(x0 ** n for n in LEVELS)\n"
        "        for N in (1, 2, 3):\n"
        "            Z = F(0)\n            E = F(0)\n"
        "            for state in product(LEVELS, repeat=N):\n"
        "                w = x0 ** sum(state)\n"
        "                Z += w\n                E += eps * sum(state) * w\n"
        "            assert Z == z1 ** N\n"
        "            assert E / Z == U_claim(1 / x0, N, eps), (x0, eps, N)\n"
        "            checked += 1\n"
        "print(f'LEVELS={LEVELS} BRUTE_FORCE_STATES_CHECKED={checked} "
        "VERIFIED True')\n")
    return Reading(
        "level_particles", True,
        f"Z = {z_text}; U = {u_text}",
        f"Each particle's partition function is the sum of Boltzmann "
        f"factors over its levels {', '.join(str(n) + 'ε' if n else '0' for n in levels)}; "
        "distinguishable, non-interacting particles multiply, so Z = Z1^N, "
        "and U = -d ln Z / d beta = -N Z1'/Z1 with beta = 1/(kT).",
        f"Z1 = {S.to_text(Z1)} with x = exp(-beta*epsilon); "
        f"U = -N dZ1/dbeta / Z1 = {S.to_text(U)}", script,
        backing="reasoning.symbolic.diff through the exp atom; column 3 "
                "averages over every microstate")


# ===========================================================================
# 9.  THE DISSIPATING LOOP (O017)
# ===========================================================================

def _m_loop_heat(t: str) -> Optional[dict]:
    if "resistance" not in t or "dissipated" not in t or \
            not re.search(r"b_0\s*e\^\{-\\alpha\s*t\}", t):
        return None
    if re.search(r"circular loop of wire with radius a", t):
        return {"shape": "circle", "A": "pi*a^2"}
    if re.search(r"square loop of wire with side a", t):
        return {"shape": "square", "A": "a^2"}
    return None


DUAL = '''from fractions import Fraction as F


class D:
    """a + b eps with eps^2 = 0: the value and its derivative."""
    def __init__(self, a, b=0):
        self.a, self.b = F(a), F(b)
    def _c(o):
        return o if isinstance(o, D) else D(o)
    def __add__(s, o):
        o = D._c(o); return D(s.a + o.a, s.b + o.b)
    __radd__ = __add__
    def __neg__(s):
        return D(-s.a, -s.b)
    def __sub__(s, o):
        return s + (-D._c(o))
    def __rsub__(s, o):
        return D._c(o) - s
    def __mul__(s, o):
        o = D._c(o); return D(s.a * o.a, s.a * o.b + s.b * o.a)
    __rmul__ = __mul__
    def __truediv__(s, o):
        o = D._c(o); return D(s.a / o.a, (s.b * o.a - s.a * o.b) / o.a ** 2)
    def __pow__(s, n):
        out = D(1)
        for _ in range(n):
            out = out * s
        return out
'''


def _a_loop_heat(g: dict) -> Reading:
    ctx = S.Context()
    A = S.parse(g["A"], ctx)
    x = S.parse("exp(-alpha*t)", ctx)
    B0 = S.parse("B0", ctx)
    R = S.parse("R", ctx)
    Phi = A * B0 * x
    emf = -S.diff(Phi, "t", ctx)
    P = emf * emf / R
    xname = next(iter(x.num.vars()))
    alpha = S.parse("alpha", ctx)
    Q = S.RF(S.Poly())
    for e, c in P.num.coeffs(xname).items():
        if e == 0:
            raise S.SymbolicError("DIVERGES", "a constant power never decays")
        Q = Q + S.RF(c) / (P.den * e) / alpha
    Q = Q * _mut()
    a2 = "pi^2*a^4" if g["shape"] == "circle" else "a^4"
    printed = f"{a2}*alpha*B0^2/(2*R)"
    if S.parse(printed) != Q:
        printed = S.to_text(Q)
    names = {v: v for v in ("a", "alpha", "B0", "R", "pi", "x")}
    tr = S.transliterate(printed.replace("^", "^"), names)
    area = S.transliterate(g["A"], names)
    script = DUAL + (
        f"def area(a, pi):\n    return {area}\n"
        f"def Q_claim(a, alpha, B0, R, pi):\n    return {tr}\n"
        "checked = 0\n"
        "for a, alpha, B0, R, pi in [(F(1, 2), F(3), F(2), F(5), F(22, 7)),\n"
        "        (F(2), F(1, 4), F(3, 5), F(7, 3), F(355, 113)),\n"
        "        (F(3, 4), F(5, 2), F(1), F(1, 2), F(3))]:\n"
        "    for x0 in (F(1), F(1, 2), F(1, 9)):\n"
        "        x = D(x0, -alpha * x0)        # x = exp(-alpha t), dx/dt\n"
        "        phi = area(a, pi) * B0 * x\n"
        "        emf = -phi.b                   # Faraday: -dPhi/dt\n"
        "        P = emf * emf / R\n"
        "        Fa = -area(a, pi) ** 2 * B0 ** 2 * alpha * x * x / (2 * R)\n"
        "        assert Fa.b == P, (Fa.b, P)     # antiderivative of P\n"
        "        checked += 1\n"
        "    # x -> 0 as t -> infinity (alpha > 0): Q = F(inf) - F(0)\n"
        "    assert alpha > 0\n"
        "    F0 = -area(a, pi) ** 2 * B0 ** 2 * alpha / (2 * R)\n"
        "    assert 0 - F0 == Q_claim(a, alpha, B0, R, pi)\n"
        "print(f'DUAL_CHECKS={checked} Q=INTEGRAL_OF_P VERIFIED True')\n")
    return Reading(
        "loop_dissipation", True, f"Q = {printed}",
        f"The flux through the loop is Phi = A B(t) with A = {g['A']}; "
        "Faraday's law gives emf = -dPhi/dt, the power dissipated is "
        "emf^2/R, and its integral from t = 0 to infinity converges "
        "because alpha > 0.",
        f"Phi = {S.to_text(Phi)}; emf = {S.to_text(emf)}; P = "
        f"{S.to_text(P)}; integral of exp(-n alpha t) over (0, inf) is "
        f"1/(n alpha)", script,
        backing="reasoning.symbolic.diff + exponential-polynomial integral; "
                "column 3 checks by dual numbers")


# ===========================================================================
# 10.  THE RIGID ROTOR (O026)
# ===========================================================================

def _m_rotor(t: str) -> Optional[dict]:
    if "rigid rotor" not in t or "partition function" not in t or \
            "heat capacity" not in t:
        return None
    if "nonlinear" in t or "non-linear" in t:
        return {"s": Fraction(3, 2), "kind": "nonlinear"}
    if "diatomic" in t or "linear" in t:
        return {"s": Fraction(1), "kind": "linear"}
    return None


def _a_rotor(g: dict) -> Reading:
    s = g["s"]
    ctx = S.Context()
    lnq = S.parse(f"{_c(s)}*ln(T) - ln(sigma*Theta)", ctx)
    d = S.diff(lnq, "T", ctx)
    U = S.parse("R*T^2", ctx) * d
    C = S.diff(U, "T", ctx) * _mut()
    ctext = S.to_text(C)
    q_text = ("q_rot = T/(sigma*Theta_rot), Theta_rot = h^2/(8*pi^2*I*k)"
              if s == 1 else
              "q_rot = sqrt(pi)*T^(3/2)/(sigma*sqrt(Theta_A*Theta_B*Theta_C))")
    pnum, pden = s.numerator, s.denominator
    cpy = S.to_python(C, {"R": "R"})
    script = DUAL + (
        f"P, Q = {pnum}, {pden}           # q_rot proportional to T^(P/Q)\n"
        "checked = 0\n"
        "for u0 in (F(3, 2), F(2), F(5, 3)):\n"
        "    for sig_theta in (F(1, 7), F(2), F(9, 4)):\n"
        "        for R in (F(1), F(8314, 1000)):\n"
        "            u = D(u0, 1)             # T = u^Q, so T^(P/Q) = u^P\n"
        "            T = u ** Q\n"
        "            q = u ** P / sig_theta\n"
        "            dlnq_dT = (q.b / q.a) / T.b\n"
        "            U = R * T.a ** 2 * dlnq_dT\n"
        f"            C = {cpy}\n"
        "            assert U == C * T.a       # U linear in T: C = dU/dT\n"
        "            checked += 1\n"
        "print(f'ROTOR_POINTS={checked} VERIFIED True')\n")
    return Reading(
        "rigid_rotor", True,
        f"{q_text} (high temperature, T >> Theta_rot); U_m = R*T^2 "
        f"d(ln q_rot)/dT = {S.to_text(U)}; C_V,m = {ctext}.  Why it changes "
        "at cryogenic temperatures is refused (EXPLANATION): what the "
        "machine can state is that the high-temperature form holds only "
        "for T >> Theta_rot",
        "In the high-temperature limit the sum over rotational levels "
        f"becomes an integral, q_rot proportional to T^{s}; the molar "
        "energy is R T^2 d ln q / dT and the heat capacity its temperature "
        "derivative.",
        f"ln q_rot = {S.to_text(lnq)} + const; d/dT = {S.to_text(d)}; "
        f"U = {S.to_text(U)}; C = dU/dT = {ctext}", script,
        backing="reasoning.symbolic.diff through the ln atom; column 3 by "
                "dual numbers")


# ===========================================================================
# 11.  CRYSTAL-FIELD STABILISATION (O027)
# ===========================================================================

def _m_cfse(t: str) -> Optional[dict]:
    if "crystal field" not in t or "octahedral" not in t:
        return None
    m = re.search(r"\bd\^(\d+)", t)
    if not m:
        return None
    n = int(m.group(1))
    spin = "low" if "low-spin" in t else "high" if "high-spin" in t else None
    if spin is None or not 1 <= n <= 10:
        return None
    return {"n": n, "spin": spin, "tetra": "tetrahedral" in t}


def _fill(n: int, levels: Sequence[Tuple[int, Fraction]], low: bool
          ) -> Tuple[Fraction, int]:
    """``(orbital energy in units of Delta, electron pairs)``: high spin puts
    one electron in every orbital before pairing; low spin fills the lower
    set completely first."""
    orbs = []
    for count, e in levels:
        orbs += [e] * count
    occ = [0] * len(orbs)
    order = sorted(range(len(orbs)), key=lambda i: orbs[i])
    left = n
    if low:
        for i in order:
            put = min(2, left)
            occ[i] = put
            left -= put
    else:
        for rnd in (1, 2):
            for i in order:
                if left and occ[i] < rnd:
                    occ[i] += 1
                    left -= 1
    energy = sum(o * e for o, e in zip(occ, orbs))
    pairs = sum(1 for o in occ if o == 2)
    return energy, pairs


OCT = ((3, Fraction(-2, 5)), (2, Fraction(3, 5)))
TET = ((2, Fraction(-3, 5)), (3, Fraction(2, 5)))


def _cfse_text(e: Fraction, pairs: int, delta: str) -> str:
    parts = []
    if e:
        parts.append(f"{'-' if e < 0 else ''}{_c(abs(e))}*{delta}")
    if pairs:
        parts.append(f"{pairs}*P")
    if not parts:
        return "0"
    out = parts[0]
    for p in parts[1:]:
        out += f" + {p}"
    return out


def _a_cfse(g: dict) -> Reading:
    n, low = g["n"], g["spin"] == "low"
    free_pairs = max(0, n - 5)
    e_o, p_o = _fill(n, OCT, low)
    if MUTATE[0]:
        # additive: doubling would leave a zero stabilisation unchanged
        e_o = e_o + Fraction(1, 5)
    oct_t = _cfse_text(e_o, p_o - free_pairs, "Delta_o")
    lines = [f"octahedral: CFSE = {oct_t}"]
    e_t = p_t = None
    if g["tetra"]:
        e_t, p_t = _fill(n, TET, False)
        lines.append(f"tetrahedral: CFSE = "
                     f"{_cfse_text(e_t, p_t - free_pairs, 'Delta_t')}")
    script = (
        "from fractions import Fraction as F\nfrom itertools import product\n"
        f"N = {n}\nLOW = {low}\n"
        "OCT = [F(-2, 5)] * 3 + [F(3, 5)] * 2\n"
        "TET = [F(-3, 5)] * 2 + [F(2, 5)] * 3\n"
        "def ground(orbs, delta, P):\n"
        "    best = None\n"
        "    for occ in product((0, 1, 2), repeat=5):\n"
        "        if sum(occ) != N:\n            continue\n"
        "        E = sum(o * e * delta for o, e in zip(occ, orbs)) + "
        "P * sum(1 for o in occ if o == 2)\n"
        "        best = E if best is None else min(best, E)\n"
        "    return best\n"
        "checked = 0\n"
        "for P in (F(1), F(5, 2)):\n"
        "    free = ground(OCT, F(0), P)       # spherical ion\n"
        "    for delta in ((P * 3, P * 5) if LOW else (P / 3, P / 7)):\n"
        f"        claim = {_frac_py(e_o)} * delta + {p_o - free_pairs} * P\n"
        "        assert ground(OCT, delta, P) - free == claim, (delta, P)\n"
        "        checked += 1\n"
        + (f"    for delta in (P / 3, P / 7):\n"
           f"        claim = {_frac_py(e_t)} * delta + {p_t - free_pairs} * P\n"
           "        assert ground(TET, delta, P) - free == claim\n"
           "        checked += 1\n" if g["tetra"] else "")
        + "print(f'GROUND_STATES_ENUMERATED={checked} VERIFIED True')\n")
    return Reading(
        "crystal_field", True,
        "; ".join(lines) + " (pairing energy counted relative to the free "
        "ion's pairs; the splitting diagram is refused (DESIGN): the "
        "machine draws no diagram)",
        f"d{n}, {'low' if low else 'high'} spin in the octahedral field: "
        "t2g lies 2/5 Delta_o below the barycentre and eg 3/5 above; "
        "the tetrahedral field inverts and shrinks the splitting (e at "
        "-3/5 Delta_t, t2 at +2/5) and is always high spin.",
        f"octahedral occupation energy {e_o} Delta_o with {p_o} pairs "
        f"(free ion {free_pairs})"
        + (f"; tetrahedral {e_t} Delta_t with {p_t} pairs"
           if g["tetra"] else ""), script,
        backing="runtime.symbolic_outside crystal-field filling; column 3 "
                "enumerates every placement")


# ===========================================================================
# 12.  THE FILTERED WHITE NOISE (O047)
# ===========================================================================

def _m_ar1(t: str) -> Optional[dict]:
    if "white noise" not in t or "autocorrelation" not in t or \
            not re.search(r"h\[n\]\s*=\s*a\^n\s*u\[n\]", t):
        return None
    m = re.search(r"variance\s*(?:sigma\^2|σ\^2)?\s*=\s*(\d+(?:/\d+)?)", t)
    return {"s2": Fraction(m.group(1)) if m else None}


def _a_ar1(g: dict) -> Reading:
    s2 = g["s2"]
    ctx = S.Context()
    a = S.parse("a", ctx)
    geo = 1 / (1 - a * a)                 # sum_{n>=0} (a^2)^n, |a| < 1
    lead = S.RF(S.Poly.const(s2)) if s2 is not None else S.parse("sigma^2")
    R0 = lead * geo * _mut()
    st = "" if s2 == 1 else (_c(s2) + "*" if s2 is not None else "sigma^2*")
    sm = (s2 if s2 is not None else Fraction(1)) * _mut()
    st = "" if sm == 1 and s2 is not None else st
    if MUTATE[0]:
        st = f"{_c(sm)}*"
    r_text = f"R_yy[m] = {st}a^|m|/(1 - a^2)"
    s_text = f"S_yy(e^(j*omega)) = {_c(sm) if sm != 1 else 1}/" \
             "(1 - 2*a*cos(omega) + a^2)"
    sval = _frac_py(sm)
    script = (
        "from fractions import Fraction as F\n"
        f"S2 = {sval}\n"
        "def R_claim(a, m):\n    return S2 * a ** abs(m) / (1 - a * a)\n"
        "def S_claim(a, c):\n    return S2 / (1 - 2 * a * c + a * a)\n"
        "def gmul(x, y):\n"
        "    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])\n"
        "def ginv(x):\n"
        "    n = x[0] ** 2 + x[1] ** 2\n    return (x[0] / n, -x[1] / n)\n"
        "checked = 0\n"
        "K = 40\n"
        f"base = {_frac_py(s2) if s2 is not None else 'F(1)'}\n"
        "for a in (F(1, 2), F(-2, 3), F(3, 10), F(-1, 7)):\n"
        "    assert abs(a) < 1\n"
        "    for m in range(-4, 5):\n"
        "        # R[m] = s2 * sum_n h[n] h[n + |m|], h[n] = a^n\n"
        "        part = base * sum(a ** n * a ** (n + abs(m)) for n in range(K))\n"
        "        tail = base * a ** (abs(m) + 2 * K) / (1 - a * a)\n"
        "        assert part + tail == R_claim(a, m), (a, m)\n"
        "        assert abs(tail) < F(1, 10 ** 6)\n"
        "        checked += 1\n"
        "    for t in (F(1, 2), F(2, 3), F(3)):\n"
        "        c, s = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)\n"
        "        z = (c, s)\n"
        "        H1 = ginv((1 - a * ginv(z)[0], -a * ginv(z)[1]))\n"
        "        H2 = ginv((1 - a * z[0], -a * z[1]))\n"
        "        S = gmul(H1, H2)\n"
        "        assert S[1] == 0 and base * S[0] == S_claim(a, c)\n"
        "        checked += 1\n"
        "print(f'SERIES_AND_SPECTRUM_CHECKS={checked} VERIFIED True')\n")
    return Reading(
        "ar1_output", True, f"{r_text}; {s_text}",
        "The output is the input convolved with h[n] = a^n u[n]; for white "
        "input the output autocorrelation is the input variance times the "
        "deterministic autocorrelation of h, a geometric series in a^2 that "
        "converges because |a| < 1; the spectrum is the variance times "
        "|H(e^(j omega))|^2.",
        f"R_yy[m] = s2 sum_(n>=0) a^n a^(n+|m|) = s2 a^|m| * "
        f"{S.to_text(geo)}; S_yy = s2/((1 - a e^(-j omega))"
        "(1 - a e^(j omega)))", script,
        backing="reasoning.symbolic geometric series; column 3 by exact "
                "partial sums and Gaussian rationals")


# ===========================================================================
# 13.  DFT LEAKAGE (O045)
# ===========================================================================

def _m_dft(t: str) -> Optional[dict]:
    if "dft" in t and "leakage" in t and "cos(\\omega_0 n)" in t:
        return {}
    return None


def _a_dft(g: dict) -> Reading:
    two = 2 * _mut()
    script = (
        "from fractions import Fraction as F\n"
        "def mul(x, y):\n"
        "    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])\n"
        "def add(x, y):\n    return (x[0] + y[0], x[1] + y[1])\n"
        "def pw(x, n):\n"
        "    out = (F(1), F(0))\n"
        "    for _ in range(n):\n        out = mul(out, x)\n    return out\n"
        "def inv(x):\n"
        "    n = x[0] ** 2 + x[1] ** 2\n    return (x[0] / n, -x[1] / n)\n"
        "def Dn(u, N):\n"
        "    # sum_{n<N} u^n\n"
        "    s = (F(0), F(0))\n"
        "    for n in range(N):\n        s = add(s, pw(u, n))\n    return s\n"
        "checked = 0\n"
        "N = 4\n"
        "W = [(F(1), F(0)), (F(0), F(-1)), (F(-1), F(0)), (F(0), F(1))]\n"
        "# no leakage: omega0 = 2 pi k0 / N, e.g. k0 = 1, z0 = j\n"
        "z0 = (F(0), F(1))\n"
        "x = [pw(z0, n)[0] for n in range(N)]\n"
        "X = [(sum(x[n] * pw(W[k], n)[0] for n in range(N)),\n"
        "      sum(x[n] * pw(W[k], n)[1] for n in range(N))) for k in range(N)]\n"
        f"assert X == [(F(0), F(0)), (F({two}), F(0)), (F(0), F(0)), "
        f"(F({two}), F(0))], X\n"
        "checked += 1\n"
        "# leakage: cos(omega0) = 3/5 is no multiple of 2 pi / N\n"
        "for t in (F(1, 2), F(1, 3), F(2, 7)):\n"
        "    z0 = ((1 - t * t) / (1 + t * t), 2 * t / (1 + t * t))\n"
        "    x = [pw(z0, n)[0] for n in range(N)]\n"
        "    for k in range(N):\n"
        "        Xk = (sum(x[n] * pw(W[k], n)[0] for n in range(N)),\n"
        "              sum(x[n] * pw(W[k], n)[1] for n in range(N)))\n"
        "        u1, u2 = mul(z0, W[k]), mul(inv(z0), W[k])\n"
        "        half = add(Dn(u1, N), Dn(u2, N))\n"
        "        assert Xk == (half[0] / 2, half[1] / 2)\n"
        "        assert Xk != (F(0), F(0))         # every bin leaks\n"
        "        # |D_N(u)|^2 = (1 - Re u^N)/(1 - Re u) = sin^2(N th/2)/sin^2(th/2)\n"
        "        for u in (u1, u2):\n"
        "            d = Dn(u, N)\n"
        "            assert d[0] ** 2 + d[1] ** 2 == (1 - pw(u, N)[0]) / (1 - u[0])\n"
        "        checked += 1\n"
        "print(f'DFT_CHECKS={checked} VERIFIED True')\n")
    return Reading(
        "dft_leakage", True,
        "no leakage exactly when omega0 = 2*pi*k0/N for an integer k0 (a "
        "whole number of periods in the window): then X[k] = N/2 at "
        "k = k0 and k = N - k0 and 0 elsewhere; otherwise X[k] = "
        "(1/2)*[D_N(omega0 - 2*pi*k/N) + D_N(-omega0 - 2*pi*k/N)] with "
        "D_N(theta) = sum_(n<N) e^(j*theta*n) = e^(j*theta*(N-1)/2)*"
        "sin(N*theta/2)/sin(theta/2), so |X[k]| is set by "
        "|sin(N*theta/2)/sin(theta/2)| at theta = omega0 -+ 2*pi*k/N and "
        "no bin is zero",
        "cos(omega0 n) = (e^(j omega0 n) + e^(-j omega0 n))/2, and each "
        "exponential's DFT is a finite geometric sum (u^N - 1)/(u - 1) "
        "with u = e^(j(+-omega0 - 2 pi k/N)); it vanishes exactly when "
        "u^N = 1 and u != 1.",
        "X[k] = (1/2)[D_N(u+) + D_N(u-)], D_N(u) = (u^N - 1)/(u - 1), "
        "|D_N|^2 = (1 - cos N theta)/(1 - cos theta)", script,
        backing="geometric sums over Gaussian rationals; column 3 computes "
                "the DFT exactly at N = 4")


# ===========================================================================
# 14.  THE TRANSCENDENTAL CROSSOVER (O035, class T)
# ===========================================================================

def arctan_bounds(x: Fraction, terms: int = 40) -> Tuple[Fraction, Fraction]:
    """Exact bounds on arctan(x) for 0 <= x <= 1 by the alternating
    series (the error is below the first omitted term)."""
    x = Fraction(x)
    s = Fraction(0)
    p = x
    for k in range(terms):
        s += (-1) ** k * p / (2 * k + 1)
        p *= x * x
    nxt = p / (2 * terms + 1)
    return (s - nxt, s + nxt) if terms % 2 == 0 else (s - nxt, s + nxt)


def pi_bounds() -> Tuple[Fraction, Fraction]:
    a = arctan_bounds(Fraction(1, 5))
    b = arctan_bounds(Fraction(1, 239))
    return (16 * a[0] - 4 * b[1], 16 * a[1] - 4 * b[0])


def atan_any(x: Fraction) -> Tuple[Fraction, Fraction]:
    if x <= 1:
        return arctan_bounds(x)
    lo, hi = arctan_bounds(1 / x)
    plo, phi = pi_bounds()
    return (plo / 2 - hi, phi / 2 - lo)


def _m_crossover(t: str) -> Optional[dict]:
    m = re.search(r"g\(s\)\s*=\s*\\frac\{e\^\{-(\d+(?:\.\d+)?)s\}\}"
                  r"\{s\s*\+\s*(\d+(?:\.\d+)?)\}", t)
    if not m or "crossover" not in t:
        return None
    return {"tau": Fraction(m.group(1)), "p": Fraction(m.group(2))}


def _phase_excess(w: Fraction, tau: Fraction, p: Fraction
                  ) -> Tuple[Fraction, Fraction]:
    """Bounds on tau*w + arctan(w/p) - pi."""
    lo, hi = atan_any(w / p)
    plo, phi = pi_bounds()
    return (tau * w + lo - phi, tau * w + hi - plo)


def _a_crossover(g: dict) -> Reading:
    tau, p = g["tau"], g["p"]
    lo, hi = Fraction(0), Fraction(1000)
    while hi - lo > Fraction(1, 10 ** 6):
        mid = (lo + hi) / 2
        a, b = _phase_excess(mid, tau, p)
        if b < 0:
            lo = mid
        elif a > 0:
            hi = mid
        else:
            break
    shift = Fraction(1, 100) if MUTATE[0] else Fraction(0)
    lo4 = Fraction(int(lo * 10 ** 4), 10 ** 4) + shift
    hi4 = lo4 + Fraction(1, 10 ** 4)
    ar_hi = 1 / (lo4 * lo4 + p * p)          # AR^2 bounds
    ar_lo = 1 / (hi4 * hi4 + p * p)
    ar_txt = f"{_sqrt_dec(ar_lo)}..{_sqrt_dec(ar_hi)}"
    gm_txt = f"{_sqrt_dec(1 / ar_hi)}..{_sqrt_dec(1 / ar_lo)}"
    script = (
        "from fractions import Fraction as F\n"
        f"TAU, P = {_frac_py(tau)}, {_frac_py(p)}\n"
        f"LO, HI = {_frac_py(lo4)}, {_frac_py(hi4)}\n"
        "def atan01(x, n=60):\n"
        "    s, p = F(0), x\n"
        "    for k in range(n):\n"
        "        s += (-1) ** k * p / (2 * k + 1)\n        p *= x * x\n"
        "    e = p / (2 * n + 1)\n    return s - e, s + e\n"
        "a5, a239 = atan01(F(1, 5)), atan01(F(1, 239))\n"
        "PI = (16 * a5[0] - 4 * a239[1], 16 * a5[1] - 4 * a239[0])\n"
        "assert PI[0] < F(355, 113) < PI[1] + F(1, 10**6)\n"
        "def atan(x):\n"
        "    if x <= 1:\n        return atan01(x)\n"
        "    l, h = atan01(1 / x)\n"
        "    return PI[0] / 2 - h, PI[1] / 2 - l\n"
        "def excess(w):\n"
        "    l, h = atan(w / P)\n"
        "    return TAU * w + l - PI[1], TAU * w + h - PI[0]\n"
        "assert excess(LO)[1] < 0, 'phase not yet -180 at LO'\n"
        "assert excess(HI)[0] > 0, 'phase past -180 at HI'\n"
        "print(f'OMEGA_CO IN [{LO}, {HI}] VERIFIED True')\n")
    return Reading(
        "crossover_frequency", True,
        f"omega_co in [{_dec4(lo4)}, {_dec4(hi4)}] rad/time (the root of "
        f"{_dec4(tau)}*omega + arctan(omega/{p}) = pi); amplitude ratio "
        f"AR = 1/sqrt(omega^2 + {p ** 2}) = {ar_txt}; gain margin "
        f"GM = 1/AR = {gm_txt}",
        f"The phase of e^(-{tau}s)/(s + {p}) is -{tau} omega - "
        f"arctan(omega/{p}); it reaches -180 degrees where {tau} omega + "
        f"arctan(omega/{p}) = pi, an equation with no closed form, so the "
        "root is bracketed by bisection on exact bounds of arctan and pi.",
        "f(omega) = tau omega + arctan(omega/p) - pi is increasing; "
        "f(LO) < 0 < f(HI) with arctan and pi bracketed by alternating "
        "series", script,
        backing="runtime.symbolic_outside.atan_any (alternating-series "
                "bounds, Machin's pi)")


def _dec4(q: Fraction) -> str:
    return _dec_places(q, 4)


def _sqrt_dec(q: Fraction, places: int = 4) -> str:
    return _decimal_root(q, 2, places)


# ===========================================================================
# 15.  THE REGISTER
# ===========================================================================

OUTSIDE_S_FRAMES: Tuple[Frame, ...] = tuple(
    Frame(n, s, m, a, "S") for n, s, m, a in (
        ("rolling_body", "a body rolling without slipping on an incline",
         _m_rolling, _a_rolling),
        ("adiabatic_work", "work of a reversible adiabatic expansion",
         _m_adiabatic, _a_adiabatic),
        ("gauss_coax", "Gauss's law for a line charge in a coaxial shell",
         _m_coax, _a_coax),
        ("fusion_mass", "rest mass of a relativistic fusion product",
         _m_fusion, _a_fusion),
        ("interface_angles", "the tangent law at a material interface",
         _m_interface, _a_interface),
        ("disturbance_loop", "a disturbance's closed-loop transfer function",
         _m_loop, _a_loop),
        ("body_effect", "the MOSFET threshold shift with source-body bias",
         _m_body, _a_body),
        ("level_particles", "N distinguishable particles on given levels",
         _m_levels, _a_levels),
        ("loop_dissipation", "heat dissipated in a loop under a decaying "
         "field", _m_loop_heat, _a_loop_heat),
        ("rigid_rotor", "rotational partition function and heat capacity",
         _m_rotor, _a_rotor),
        ("crystal_field", "crystal-field stabilisation energy",
         _m_cfse, _a_cfse),
        ("ar1_output", "white noise through a first-order filter",
         _m_ar1, _a_ar1),
        ("dft_leakage", "spectral leakage of a windowed sinusoid",
         _m_dft, _a_dft),
        ("crossover_frequency", "phase crossover of a dead-time lag "
         "(transcendental)", _m_crossover, _a_crossover),
    ))


def mutated_reading(frame: Frame, givens: dict) -> Reading:
    """The frame's reading with its claimed value altered (column-3
    control)."""
    MUTATE[0] = True
    try:
        return frame.answer(givens)
    finally:
        MUTATE[0] = False
