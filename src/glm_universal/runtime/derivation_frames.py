"""``glm_universal.runtime.derivation_frames`` -- derivations and proofs as
question frames (Phase 106, ``studies/DERIVATION_STUDY.md``).

Four operations, each read from one line of text and gated by its
column-3 script (:mod:`glm_universal.runtime.derivation_scripts`) before it
is output, like every other frame:

* ``prove: PREMISES |- GOAL`` -- :mod:`glm_universal.reasoning.proof_search`;
* ``derive equations of motion for Q1, Q2[, small oscillations]: L = ...``;
* ``derive transfer functions from U1, U2 to Y1: EQ; EQ``;
* ``solve boundary value problem for Y(X): d/dX(P*d(Y)/dX) = G; BC; BC`` --
  the three of :mod:`glm_universal.reasoning.derivation`.

And four **outside frames** for the class-P questions of the outside set
(``studies/QUESTION_SET_B_STUDY.md`` §8): each recognises the situation,
writes the law that governs it -- the Lagrangian of a chain pendulum built
from its links, the energy balance of a stirred tank, the flux law of a
spherical shell, the sequent of a self-referential conditional -- and hands
it to the same operation.  Nothing is looked up by question: a triple
pendulum, a second input or a cylindrical film changes the law and the
answer with it.  Where a question also asks *why* (the threat Curry's
paradox poses), the computed part is answered and the rest is named as the
refusal ``EXPLANATION`` inside the reading.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from ..reasoning import derivation as D
from ..reasoning import proof_search as PS
from ..reasoning import symbolic as S
from . import derivation_scripts as DS
from .question_frames import Frame, Reading

__all__ = ["PROVE", "MOTION", "TRANSFER", "PROFILE", "PREFIXES", "match_raw",
           "read_operation", "OPERATION_FRAME", "OUTSIDE_P_FRAMES", "MUTATE",
           "mutated_operation", "mutated_outside", "chain_lagrangian"]

PROVE = "prove:"
MOTION = "derive equations of motion for "
TRANSFER = "derive transfer functions from "
PROFILE = "solve boundary value problem for "
PREFIXES = (PROVE, MOTION, TRANSFER, PROFILE)

#: Set by the mutated readings: every claim is altered (the column-3
#: control: its script must reject it).
MUTATE = [False]


def _refusal(frame: str, code: str, why: str, col1: str) -> Reading:
    return Reading(frame, False, why, col1, f"refused {code}",
                   f"print('REFUSED {code} VERIFIED True')\n", code=code,
                   backing="reasoning.derivation / reasoning.proof_search")


# ===========================================================================
# 1.  PROOFS
# ===========================================================================

def prove_reading(sequent: str, frame: str = "proof_search",
                  col1: str = "") -> Reading:
    try:
        prem, goal = PS.parse_sequent(sequent)
        v = PS.decide(prem, goal)
    except PS.ProofError as e:
        return _refusal(frame, e.code, e.why, col1 or "a sequent")
    seq = ", ".join(PS.show(p) for p in prem) + " |- " + PS.show(goal)
    label = "PROOF " + seq
    claimed_goal = goal
    if MUTATE[0]:
        claimed_goal = ("and", goal, ("atom", "mutant_atom")) \
            if v.kind != "NOT_VALID" else goal
    valuation = v.valuation
    if MUTATE[0] and valuation:
        k = sorted(valuation)[0]
        valuation = dict(valuation)
        valuation[k] = not valuation[k]
    script = DS.proof_script(prem, claimed_goal, v.kind, v.proof, valuation,
                             v.excluded_middle, v.kripke, label)
    col1 = col1 or f"does {PS.show(goal)} follow from " \
                   f"{', '.join(PS.show(p) for p in prem) or 'nothing'}?"
    if v.kind == "NOT_VALID":
        vt = ", ".join(f"{a} = {'true' if b else 'false'}"
                       for a, b in sorted(v.valuation.items()))
        return Reading(frame, False,
                       f"{PS.show(goal)} does not follow: with {vt} every "
                       f"premise is true and the conclusion false",
                       col1, f"truth table over {len(v.valuation)} atom(s); "
                             f"falsifying valuation {vt}", script,
                       code="NOT_VALID",
                       backing="reasoning.proof_search.truth_table")
    lines = PS.proof_lines(v.proof)
    if v.kind == "intuitionistic":
        head = (f"{seq} holds constructively: a G4ip proof of "
                f"{v.proof.size()} steps (rules {', '.join(PS.rules_used(v.proof))})")
    else:
        km = ""
        if v.kripke is not None:
            up, val = v.kripke
            km = (f"; no constructive proof exists (a Kripke model of "
                  f"{len(up)} worlds refutes it: "
                  + "; ".join(f"world {w} sees {up[w]} and forces "
                              f"{val[w] or 'nothing'}" for w in sorted(up))
                  + ")")
        head = (f"{seq} holds classically but not constructively: a G4ip "
                f"proof from excluded middle on "
                f"{', '.join(v.excluded_middle)}{km}")
    return Reading(frame, True, head, col1,
                   "G4ip proof:\n    " + "\n    ".join(lines), script,
                   backing="reasoning.proof_search (G4ip, truth table, "
                           "Kripke models)")


# ===========================================================================
# 2.  EQUATIONS OF MOTION
# ===========================================================================

def _mutate_eq(text: str, coords: Sequence[str]) -> str:
    return f"{text} + {coords[0]}" if MUTATE[0] else text


def motion_reading(lagrangian: str, coords: Sequence[str], small: bool,
                   frame: str = "equations_of_motion", col1: str = "",
                   source: str = "", preface: str = "") -> Reading:
    col1 = col1 or (f"the equations of motion of L = {lagrangian} in "
                    f"{', '.join(coords)}" +
                    (" and its small oscillations" if small else ""))
    try:
        mo = D.equations_of_motion(lagrangian, coords, small)
    except S.SymbolicError as e:
        return _refusal(frame, e.code, e.why, col1)
    pr = D.Printer(source or lagrangian, mo.ctx)
    eq_texts = [pr.equation(e, mo.coords) for e in mo.equations]
    lin_texts = [pr.equation(e, mo.coords) for e in mo.linear] \
        if mo.linear is not None else None
    freq_texts = [pr.text(f) for f in mo.frequencies] \
        if mo.frequencies is not None else None
    parts = [preface] if preface else []
    parts.append("Euler-Lagrange: " + "; ".join(eq_texts))
    if lin_texts is not None:
        parts.append("small oscillations about the origin: " +
                     "; ".join(lin_texts))
        if freq_texts is not None:
            parts.append("normal modes: w^2 = " + ", ".join(freq_texts))
        elif mo.modes_cubic is not None:
            parts.append(modes_stepwise_text(mo, pr))
        elif mo.modes_poly is not None:
            parts.append(modes_higher_text(mo, pr))
        elif mo.frequency_note:
            if mo.characteristic is not None:
                parts.append(f"normal modes: w2 = w^2 solves "
                             f"{pr.text(mo.characteristic)} = 0, but "
                             f"{mo.frequency_note}")
            else:
                parts.append(mo.frequency_note)
    conds = []
    for c in mo.conditions:
        if c and c not in conds:
            conds.append(c)
    if conds:
        parts.append("each equation divided by a factor stated nonzero: " +
                     "; ".join(conds))
    py = lambda t: t.split(" = ")[0]
    claims = [_mutate_eq(py(t), mo.coords) for t in eq_texts]
    lin_claims = [_mutate_eq(py(t), mo.coords) for t in lin_texts] \
        if lin_texts is not None else None
    fq = None
    aliases: Dict[str, tuple] = {}
    if freq_texts is not None:
        fq = [_py_expr(t) for t in freq_texts]
        # Phase 108: an algebraic number root(f, lo, hi) is handed to the
        # script under an alias, with its polynomial and interval
        for i, (name, alg) in enumerate(sorted(mo.frequency_algs.items())):
            alias = f"alg{i + 1}"
            fq = [t.replace(name, alias) for t in fq]
            aliases[alias] = alg
        if MUTATE[0] and fq:
            fq[0] = f"2*({fq[0]})"
    cubic = None
    stepped = mo.modes_cubic if mo.modes_cubic is not None else mo.modes_poly
    if stepped is not None:
        # the column-3 check is the same for every degree (Phase 109): the
        # polynomial against the script's own det(K - w2 M), and Sturm's
        # count of its real (positive) roots
        cubic = [_py_expr(pr.text(c)) for c in stepped]
        if MUTATE[0]:
            cubic[0] = f"2*({cubic[0]})"
    script = DS.motion_script(_py_expr(S.normalise_text(lagrangian)),
                              mo.coords, [_py_expr(c) for c in claims],
                              [_py_expr(c) for c in lin_claims]
                              if lin_claims is not None else None, fq,
                              "MOTION " + ", ".join(mo.coords),
                              [_py_expr(S.to_text(dv)) for dv in mo.divisors],
                              aliases or None, cubic,
                              positive=bool(mo.definite.get("K")))
    col2 = (f"L = {pr.sum(mo.lagrangian, mo.coords)}; for each q: d/dt(dL/dq_dot) - "
            f"dL/dq = 0, the time derivative by the chain rule q -> q_dot "
            f"-> q_ddot")
    if mo.characteristic is not None:
        col2 += f"; det(K - w2*M) = {pr.text(mo.characteristic)} = 0"
    if mo.modes_route:
        col2 += f"; {mo.modes_route}"
    return Reading(frame, True, ". ".join(parts), col1, col2, script,
                   backing="reasoning.derivation.equations_of_motion "
                           "(+ symbolic_nonlinear for the modes)")


def modes_stepwise_text(mo: D.Motion, pr: D.Printer) -> str:
    """The normal modes of a definite three-degree-of-freedom system whose
    characteristic cubic does not scale (sharpening pass): built in steps --
    the cubic's coefficients, the depressed coefficients ``P`` and ``Q``,
    the angle argument ``K``, then Viete's three roots -- rather than one
    expanded formula.  ``RequestProject/GLM/CubicTrig.lean``
    (``vieta_roots_iff``) is the theorem the last step rests on; the column-3
    script checks the cubic against the Lagrangian and counts its roots."""
    c0, c1, c2, c3 = (pr.text(c) for c in mo.modes_cubic)
    s1 = pr.text(-mo.modes_cubic[2] / mo.modes_cubic[3])
    s3 = pr.text(-mo.modes_cubic[0] / mo.modes_cubic[3])
    if mo.definite.get("K"):
        sign = ("real and positive (M and K are symmetric and positive "
                "definite for positive letters)")
    else:
        sign = ("real (M and K are symmetric and M is positive definite for "
                "positive letters)")
    return (f"normal modes, stepwise: w2 = w^2 solves "
            f"a*w2^3 + b*w2^2 + c*w2 + d = 0 with a = {c3}, b = {c2}, "
            f"c = {c1}, d = {c0}; all three roots are {sign}; with "
            f"P = (3*a*c - b^2)/(3*a^2), Q = (2*b^3 - 9*a*b*c + "
            f"27*a^2*d)/(27*a^3) and K = (3*Q/(2*P))*sqrt(-3/P), "
            f"w2_k = -b/(3*a) + 2*sqrt(-P/3)*cos(acos(K)/3 - 2*pi*k/3) for "
            f"k = 0, 1, 2 in decreasing order; their sum is {s1} and their "
            f"product {s3}")


def modes_higher_text(mo: D.Motion, pr: D.Printer) -> str:
    """The normal modes of a definite system of four or more degrees of
    freedom, in steps (Phase 109, route ``modes.higher``).

    * **ferrari** (a quartic): the coefficients ``a..e``; the shift
      ``w2 = y - b/(4a)`` to ``y^4 + p y^2 + q y + r``; the resolvent cubic
      ``z^3 + 2p z^2 + (p^2 - 4r) z - q^2``, whose three roots
      ``(y_i + y_j)^2`` are real and non-negative and are named by Viete as
      in the three-degree case; then ``s1 = sqrt(z1)``, ``s2 = sqrt(z2)``,
      ``s3 = -q/(s1 s2)`` and the four half-sums.
      ``RequestProject/GLM/QuarticResolvent.lean`` (``ferrari_roots``).
    * **named** (degree five or more): the coefficients, the roots stated
      real and positive and named in decreasing order, with their sum and
      product -- Abel-Ruffini: no general radical form exists; and, since
      Phase 114, the reason no radical formula gives *these* roots when a
      positive point of the letters passes a radical-free certificate
      (``Motion.modes_radical``).

    The column-3 script checks the polynomial against the Lagrangian and
    counts its real roots by Sturm's theorem, as for the cubic."""
    cs = mo.modes_poly
    n = len(cs) - 1
    word = D._NUMBER_WORDS.get(n, str(n))
    if mo.definite.get("K"):
        sign = ("real and positive (M and K are symmetric and positive "
                "definite for positive letters)")
    else:
        sign = ("real (M and K are symmetric and M is positive definite for "
                "positive letters)")
    total = pr.text(-cs[n - 1] / cs[n])
    product = pr.text(cs[0] / cs[n] if n % 2 == 0 else -cs[0] / cs[n])
    if mo.modes_method == "ferrari":
        a, b, c, d, e = (pr.text(cs[i]) for i in (4, 3, 2, 1, 0))
        return (f"normal modes, stepwise: w2 = w^2 solves a*w2^4 + b*w2^3 + "
                f"c*w2^2 + d*w2 + e = 0 with a = {a}, b = {b}, c = {c}, "
                f"d = {d}, e = {e}; all four roots are {sign}; "
                f"step 1, with w2 = y - b/(4*a): y^4 + p*y^2 + q*y + r = 0, "
                f"p = (8*a*c - 3*b^2)/(8*a^2), "
                f"q = (b^3 - 4*a*b*c + 8*a^2*d)/(8*a^3), "
                f"r = (16*a*b^2*c - 64*a^2*b*d - 3*b^4 + 256*a^3*e)/"
                f"(256*a^4); step 2, the resolvent cubic z^3 + A*z^2 + B*z "
                f"+ C = 0 with A = 2*p, B = p^2 - 4*r, C = -q^2 has the "
                f"three real roots z = (y_i + y_j)^2 >= 0: with "
                f"P = (3*B - A^2)/3, Q = (2*A^3 - 9*A*B + 27*C)/27 and "
                f"K = (3*Q/(2*P))*sqrt(-3/P), z_k = -A/3 + "
                f"2*sqrt(-P/3)*cos(acos(K)/3 - 2*pi*k/3) for k = 0, 1, 2, "
                f"so z1 >= z2 >= z3; step 3, s1 = sqrt(z1), s2 = sqrt(z2), "
                f"s3 = -q/(s1*s2) (when z2 = 0, q = 0 and s3 = sqrt(z3)), "
                f"and w2 = -b/(4*a) + (s1 + s2 + s3)/2, "
                f"-b/(4*a) + (s1 - s2 - s3)/2, -b/(4*a) + (-s1 + s2 - s3)/2, "
                f"-b/(4*a) + (-s1 - s2 + s3)/2; their sum is {total} and "
                f"their product {product}")
    coeffs = ", ".join(f"a{i} = {pr.text(cs[i])}" for i in range(n, -1, -1))
    terms = " + ".join(f"a{i}*w2^{i}" if i > 1 else
                       ("a1*w2" if i == 1 else "a0")
                       for i in range(n, -1, -1))
    why = (f"; {mo.modes_radical}" if mo.modes_radical else "")
    return (f"normal modes, stepwise: w2 = w^2 solves {terms} = 0 with "
            f"{coeffs}; all {word} roots are {sign}; a polynomial of degree "
            f"{n} has no general solution in radicals (Abel-Ruffini), so "
            f"the roots are named, not formed: w2_1 >= ... >= w2_{n}, the "
            f"eigenvalues of M^-1*K; their sum is {total} and their product "
            f"{product}{why}")


def _py_expr(t: str) -> str:
    """A printed formula as the scripts read it (``2^(1/2)`` -> a square
    root, ``^`` stays: the scripts translate it)."""
    t = re.sub(r"(\d+)\^\((\d+)/(\d+)\)", r"(\1)^(\2/\3)", t)
    return t


# ===========================================================================
# 3.  TRANSFER FUNCTIONS
# ===========================================================================

def transfer_reading(equations: Sequence[str], inputs: Sequence[str],
                     outputs: Sequence[str], frame: str = "transfer_functions",
                     col1: str = "", source: str = "",
                     preface: str = "") -> Reading:
    col1 = col1 or (f"the transfer functions from {', '.join(inputs)} to "
                    f"{', '.join(outputs)} of " + "; ".join(equations))
    try:
        tr = D.transfer_functions(equations, inputs, outputs)
    except S.SymbolicError as e:
        return _refusal(frame, e.code, e.why, col1)
    pr = D.Printer(source or " ".join(equations), tr.ctx)
    parts = [preface] if preface else []
    claims: Dict[Tuple[str, str], str] = {}
    shown = []
    for (y, u), G in tr.functions.items():
        txt = pr.text(G)
        claims[(y, u)] = f"2*({txt})" if MUTATE[0] else txt
        std = _std(pr, G) if tr.standard[(y, u)] else ""
        shown.append(f"{y}(s)/{u}(s) = {txt}" + (f" ({std})" if std else ""))
    parts.append("; ".join(shown))
    unknowns = sorted(set(tr.states) | set(tr.outputs))
    script = DS.transfer_script([S.normalise_text(e) for e in equations],
                                tr.inputs, tr.outputs, unknowns, claims,
                                "TRANSFER " + ", ".join(tr.outputs))
    col2 = ("deviation form: " + "; ".join(D.deviation_text(e, pr)
                                           for e in tr.deviation) +
            "; Laplace with zero initial deviations, solved for each output "
            "with the other inputs held at zero")
    return Reading(frame, True, ". ".join(parts), col1, col2, script,
                   backing="reasoning.derivation.transfer_functions")


def _std(pr: D.Printer, G) -> str:
    """The standard form with its coefficients in the question's letters
    (the caller has checked that ``G`` is a first- or second-order lag)."""
    cs = G.den.coeffs("s")
    c0 = S.RF(cs.get(0, S.Poly()))
    K = S.RF(G.num) / c0
    if G.den.deg("s") == 1:
        tau = S.RF(cs.get(1, S.Poly())) / c0
        return f"K/(tau*s + 1) with K = {pr.text(K)}, tau = {pr.text(tau)}"
    a2 = S.RF(cs.get(2, S.Poly())) / c0
    a1 = S.RF(cs.get(1, S.Poly())) / c0
    return (f"K/(tau^2*s^2 + 2*zeta*tau*s + 1) with K = {pr.text(K)}, "
            f"tau^2 = {pr.text(a2)}, 2*zeta*tau = {pr.text(a1)}")


# ===========================================================================
# 4.  PROFILES
# ===========================================================================

def profile_text(pf: D.Profile, pr: D.Printer) -> str:
    """The profile as a sum over its basis functions (``A + B/r``,
    ``A + B*ln(r)``, ``A + B*x + C*x^2``)."""
    x = pf.x
    rf = pf.profile
    lnx = f"ln({x})"
    groups: Dict[Tuple, S.Poly] = {}
    num, den = rf.num, rf.den
    dx = {v: e for v, e in dict(den.monomial_content()).items() if v == x}
    if dx:
        den = S.divide_exact(den, S.Poly({tuple(dx.items()): 1}))
    if x in den.vars() or lnx in den.vars():
        return pr.text(rf)
    shift = dx.get(x, 0)
    for m, c in num.t.items():
        d = dict(m)
        key = (d.pop(x, 0) - shift, d.pop(lnx, 0))
        groups[key] = groups.get(key, S.Poly()) + \
            S.Poly({tuple(sorted(d.items())): c})
    out = ""
    for i, key in enumerate(sorted(groups, key=lambda k: (k[1] > 0, k[0] < 0,
                                                          abs(k[0])))):
        k, l = key
        coef = S.RF(groups[key]) / S.RF(den)
        ct = pr.text(coef)
        neg = ct.startswith("-")
        ct = ct[1:] if neg else ct
        basis = ""
        if l:
            basis = lnx if l == 1 else f"{lnx}^{l}"
        if k > 0:
            basis = "*".join(b for b in (f"{x}" if k == 1 else f"{x}^{k}",
                                         basis) if b)
        if " " in ct and (basis or k < 0) and not (
                ct.startswith("(") and ct.endswith(")")):
            ct = f"({ct})"
        if k < 0:
            term = pr.text(coef * S.RF(S.Poly.var(x)) ** k)
            if basis:
                term = f"({term})*{basis}"
            neg = term.startswith("-")
            term = term[1:] if neg else term
        elif basis:
            term = basis if ct == "1" else f"{ct}*{basis}"
        else:
            term = ct
        if i == 0:
            out = ("-" if neg else "") + term
        else:
            out += (" - " if neg else " + ") + term
    return out


def profile_reading(ode: str, conditions: Sequence[str],
                    frame: str = "boundary_value", col1: str = "",
                    source: str = "", preface: str = "",
                    second: Optional[Tuple[str, Sequence[str], str]] = None
                    ) -> Reading:
    col1 = col1 or f"{ode} with " + "; ".join(conditions)
    try:
        pf = D.boundary_value_profile(ode, conditions)
    except S.SymbolicError as e:
        return _refusal(frame, e.code, e.why, col1)
    pr = D.Printer(source or (ode + " " + " ".join(conditions)), pf.ctx)
    text = profile_text(pf, pr)
    parts = [preface] if preface else []
    parts.append(f"{pf.y}({pf.x}) = {text}")
    claim = pr.text(pf.profile)
    claim = f"2*({claim})" if MUTATE[0] else claim
    extra = []
    if second is not None:
        ode2, conds2, label2 = second
        pf2 = D.boundary_value_profile(ode2, conds2)
        pr2 = D.Printer(source or ode2, pf2.ctx)
        parts.append(f"{label2}: {pf2.y}({pf2.x}) = {profile_text(pf2, pr2)}")
        extra.append((pf2.y, pr2.text(pf2.profile), ";".join(conds2)))
    flux = S.to_text(pf.flux)
    script = DS.profile_script(pf.y, pf.x, flux, S.to_text(pf.source),
                               [S.normalise_text(c) for c in conditions],
                               claim, "PROFILE " + pf.y, extra)
    col2 = (f"{pf.y}' = (integral of {S.to_text(pf.source)} + c1)/"
            f"({flux}), {pf.y} = integral of that + c2: "
            f"{pf.y} = {pr.text(pf.general).replace('c__', 'c')}; the "
            f"constants fixed by " + "; ".join(pf.conditions))
    return Reading(frame, True, ". ".join(parts), col1, col2, script,
                   backing="reasoning.derivation.boundary_value_profile")


# ===========================================================================
# 5.  THE OPERATIONS
# ===========================================================================

def match_raw(text: str) -> Optional[dict]:
    t = text.strip()
    low = t.lower()
    for p in PREFIXES:
        if low.startswith(p) and ":" in (t[len(p):] if p != PROVE else ":"):
            return {"raw": t, "op": p}
    return None


def read_operation(text: str) -> Reading:
    t = text.strip()
    low = t.lower()
    if low.startswith(PROVE):
        return prove_reading(t[len(PROVE):])
    head, body = t.split(":", 1)
    if low.startswith(MOTION):
        spec = head[len(MOTION):]
        small = bool(re.search(r",\s*small oscillations\s*$", spec, re.I))
        spec = re.sub(r",\s*small oscillations\s*$", "", spec, flags=re.I)
        coords = [c.strip() for c in spec.split(",") if c.strip()]
        lag = body.strip()
        if not re.match(r"^L\s*=", lag):
            return _refusal("equations_of_motion", "UNREADABLE",
                            "write L = ...", t)
        return motion_reading(lag.split("=", 1)[1].strip(), coords, small,
                              source=t)
    if low.startswith(TRANSFER):
        m = re.match(r"(.*)\s+to\s+(.*)$", head[len(TRANSFER):])
        if not m:
            return _refusal("transfer_functions", "UNREADABLE",
                            "write from U1, U2 to Y: EQ; EQ", t)
        ins = [x.strip() for x in m.group(1).split(",") if x.strip()]
        outs = [x.strip() for x in m.group(2).split(",") if x.strip()]
        eqs = [e.strip() for e in body.split(";") if e.strip()]
        return transfer_reading(eqs, ins, outs, source=t)
    parts = [p.strip() for p in body.split(";") if p.strip()]
    if not parts:
        return _refusal("boundary_value", "UNREADABLE", "no equation", t)
    return profile_reading(parts[0], parts[1:], source=t)


def _match_op(t: str) -> Optional[dict]:
    return None                   # read on the raw text, see match_raw


OPERATION_FRAME = Frame("derivation", "prove a sequent; equations of motion; "
                        "transfer functions; a profile by two quadratures",
                        _match_op, lambda g: read_operation(g["raw"]),
                        source="P")


def mutated_operation(text: str) -> Reading:
    MUTATE[0] = True
    try:
        return read_operation(text)
    finally:
        MUTATE[0] = False


# ===========================================================================
# 6.  THE OUTSIDE FRAMES (class P)
# ===========================================================================

_NUMBERS = {"double": 2, "two": 2, "triple": 3, "three": 3, "simple": 1,
            "single": 1, "quadruple": 4, "four": 4, "quintuple": 5,
            "five": 5, "sextuple": 6, "six": 6}


def chain_lagrangian(n: int, masses: Sequence[str], lengths: Sequence[str]
                     ) -> str:
    """The Lagrangian of a planar chain of ``n`` point masses on massless
    rods, angles ``th1..thn`` from the downward vertical: bob ``i`` moves
    with velocity ``sum_{j<=i} l_j th_j_dot (cos th_j, sin th_j)``, so its
    kinetic energy is ``(1/2) m_i sum_{j,k<=i} l_j l_k th_j_dot th_k_dot
    cos(th_j - th_k)``, and its height is ``-sum_{j<=i} l_j cos th_j``."""
    terms = []
    for i in range(n):
        m = masses[i]
        for j in range(i + 1):
            for k in range(i + 1):
                lj, lk = lengths[j], lengths[k]
                vel = f"th{j + 1}_dot*th{k + 1}_dot"
                ang = "" if j == k else f"*cos(th{j + 1} - th{k + 1})"
                terms.append(f"(1/2)*{m}*{lj}*{lk}*{vel}{ang}")
        for j in range(i + 1):
            terms.append(f"{m}*g*{lengths[j]}*cos(th{j + 1})")
    return " + ".join(terms)


def _m_chain_pendulum(t: str) -> Optional[dict]:
    # Phase 109: four and five links (and "an N-link pendulum") as well;
    # Phase 114: six (the composite-degree radical certificate's chain)
    m = re.search(r"\b(double|triple|quadruple|quintuple|sextuple|two|three|"
                  r"four|five|six)(?:-link)?\s+pendulum", t) or \
        re.search(r"\b([2-6])-link\s+pendulum", t)
    # sharpening pass: the frame read only texts that named the Lagrangian;
    # asking for the normal modes, the equations of motion or the small
    # oscillations of a chain pendulum is the same derivation
    asks = ("lagrangian", "normal mode", "equations of motion",
            "small oscillation", "eigenfrequenc", "mode frequenc")
    if not m or not any(a in t for a in asks):
        return None
    n = _NUMBERS.get(m.group(1)) or int(m.group(1))
    same = "identical" in t
    if same:
        masses, lengths = ["m"] * n, ["l"] * n
    else:
        masses = [f"m{i + 1}" for i in range(n)]
        lengths = [f"l{i + 1}" for i in range(n)]
    small = any(a in t for a in ("small-angle", "small angle",
                                 "small oscillation", "normal mode",
                                 "eigenfrequenc", "mode frequenc"))
    return {"n": n, "masses": masses, "lengths": lengths, "small": small}


def _a_chain_pendulum(g: dict) -> Reading:
    n = g["n"]
    lag = chain_lagrangian(n, g["masses"], g["lengths"])
    coords = [f"th{i + 1}" for i in range(n)]
    pre = (f"with th1..th{n} = theta_1..theta_{n} from the downward "
           f"vertical, the Lagrangian T - V built from the {n} links is "
           f"L = ")
    mo = None
    try:
        mo = D.equations_of_motion(lag, coords, g["small"])
    except S.SymbolicError:
        pass
    order = " ".join(g["masses"] + g["lengths"] + coords +
                     [c + "_dot" for c in coords] + ["g"])
    if mo is not None:
        pre += D.Printer(order, mo.ctx).sum(mo.lagrangian, coords)
    rd = motion_reading(lag, coords, g["small"], frame="chain_pendulum",
                        col1=f"a {n}-link pendulum: its Lagrangian and "
                             f"equations of motion" +
                             (" for small angles" if g["small"] else ""),
                        source=order, preface=pre)
    return rd


_LATEX = ((r"\iff", "<->"), (r"\leftrightarrow", "<->"), (r"\to", "->"),
          (r"\rightarrow", "->"), (r"\land", "&"), (r"\lor", "|"),
          (r"\neg", "~"), (r"\lnot", "~"))


def _m_curry(t: str) -> Optional[dict]:
    """``c \\iff (c \\to f)`` in the (lower-cased, dollar-free) text of a
    question about Curry's paradox."""
    if "curry" not in t:
        return None
    m = re.search(r"\b([a-z])\s*\\(?:iff|leftrightarrow)\s*\(([^()]*)\)", t)
    if not m:
        return None
    body = m.group(2)
    for a, b in _LATEX:
        body = body.replace(a, b)
    conseq = re.search(r"->\s*([a-z])\s*$", body.strip())
    if "->" not in body or not conseq:
        return None
    return {"premise": f"{m.group(1).upper()} <-> ({body.strip().upper()})",
            "goal": conseq.group(1).upper()}


def _a_curry(g: dict) -> Reading:
    sequent = f"{g['premise']} |- {g['goal']}"
    rd = prove_reading(sequent, frame="curry_paradox",
                       col1=f"from the self-referential {g['premise']} alone, "
                            f"is {g['goal']} provable without negation?")
    if not rd.answered:
        return rd
    prem, goal = PS.parse_sequent(sequent)
    v = PS.decide(prem, goal)
    used = PS.rules_used(v.proof)
    neg = any(r in ("L-false", "L-false->") for r in used)
    rd.value = (f"{g['goal']} follows from {g['premise']} alone: " + rd.value +
                ". The rules used are implication introduction (R->: assume "
                "C, conclude C -> " + g['goal'] + "), modus ponens (L0->), "
                "implication on the left (L->->) and the two halves of the "
                "biconditional (L&)" +
                ("" if neg else "; no rule for negation or falsum is used") +
                ". Why this threatens naive logic more than the Liar: "
                "refused EXPLANATION (an account, not a derivation)")
    return rd


def _m_spherical_film(t: str) -> Optional[dict]:
    if not ("spherical" in t and ("film" in t or "shell" in t) and
            "diffus" in t and "profile" in t):
        return None
    if "no chemical reaction" not in t and "no reaction" not in t:
        return None
    return {"geometry": 2}


def _a_spherical_film(g: dict) -> Reading:
    ode = "d/dr(r^2*d(C)/dr) = 0"
    conds = ["C(R1) = C1", "C(R2) = C2"]
    second = ("d/dr(r^2*d(u)/dr) = 0", ["u(R1) = u1", "u(R2) = u2"],
              "A diffusing through stagnant B (bulk flow kept), with "
              "u = ln(1 - x_A), u1 = ln(1 - x_A1), u2 = ln(1 - x_A2) and "
              "x_A = C_A/c")
    pre = ("no reaction in the film, so the molar flow 4*pi*r^2*N_A is the "
           "same through every sphere: d/dr(r^2*N_A) = 0 with Fick's law "
           "N_A = -D_AB*dC_A/dr (A dilute), C1 = C_A1 at r = R1, "
           "C2 = C_A2 at r = R2")
    return profile_reading(ode, conds, frame="spherical_film",
                           col1="steady diffusion of A through a spherical "
                                "film R1 < r < R2 with no reaction",
                           source="R1 R2 C1 C2 r", preface=pre,
                           second=second)


def _m_heated_tank(t: str) -> Optional[dict]:
    if not ("tank" in t and "heat" in t and "transfer function" in t):
        return None
    if "deviation" not in t:
        return None
    return {}


def _a_heated_tank(g: dict) -> Reading:
    law = "rho*V*Cp*d(T)/dt = rho*F*Cp*(Ti - T) + Q"
    pre = ("energy balance on the perfectly mixed tank (constant V, rho, "
           "Cp; reference temperature cancels): accumulation = in - out + "
           "heater, " + law)
    return transfer_reading([law], ["Ti", "Q"], ["T"],
                            frame="heated_tank",
                            col1="a stirred tank heated at rate Q with feed "
                                 "F at Ti: T(s)/Ti(s) and T(s)/Q(s)",
                            source="rho*F*Cp*(Ti - T) + Q = rho*V*Cp*d(T)/dt",
                            preface=pre)


OUTSIDE_P_FRAMES: Tuple[Frame, ...] = (
    Frame("chain_pendulum", "a planar chain pendulum: Lagrangian, "
          "Euler-Lagrange equations, small oscillations",
          _m_chain_pendulum, _a_chain_pendulum, "P"),
    Frame("curry_paradox", "a self-referential conditional: what follows "
          "from C <-> (C -> F)", _m_curry, _a_curry, "P"),
    Frame("spherical_film", "steady diffusion through a spherical film",
          _m_spherical_film, _a_spherical_film, "P"),
    Frame("heated_tank", "a stirred heated tank: transfer functions in "
          "deviation variables", _m_heated_tank, _a_heated_tank, "P"),
)


def mutated_outside(frame: Frame, givens: dict) -> Reading:
    MUTATE[0] = True
    try:
        return frame.answer(givens)
    finally:
        MUTATE[0] = False
