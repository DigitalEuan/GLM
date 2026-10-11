"""``glm_universal.reasoning.derivation`` -- derivations in letters
(Phase 106, ``studies/DERIVATION_STUDY.md``).

Why it exists
-------------
Class P of the outside question set (``studies/QUESTION_SET_B_STUDY.md``
§8) asks the machine to *derive*: equations of motion from a Lagrangian, a
transfer function from a dynamic model, a concentration or temperature
profile from a conservation law.  Phase 98's symbolic layer could solve
equations in letters and differentiate through its atoms; this module
builds three derivations on it, each a general procedure rather than a
stored answer:

* :func:`equations_of_motion` -- the Euler-Lagrange equations
  ``d/dt dL/dq_dot - dL/dq = 0`` with the total time derivative taken by the
  chain rule (``q -> q_dot -> q_ddot``); for small oscillations the
  linearisation about the origin (refused ``NOT_EQUILIBRIUM`` when the
  origin is not one), the mass and stiffness matrices and the squared
  normal-mode frequencies, the roots of ``det(K - w2 M) = 0`` found by the
  nonlinear layer of Phase 103.
* :func:`transfer_functions` -- a dynamic model linearised about its steady
  state (the steady value of ``X`` is ``X_s``), in deviation variables,
  Laplace-transformed with zero initial deviations, and solved for each
  output over each input by exact Gaussian elimination over rational
  functions of ``s``; a first-order lag is also given as ``K/(tau*s + 1)``.
* :func:`boundary_value_profile` -- the flux form ``d/dx(P dy/dx) = G``
  with ``P = c x^n`` and ``G`` a polynomial in ``x``, solved by two
  quadratures (``x^-1`` integrates to ``ln(x)``), the two constants fixed by
  the boundary conditions: a value, a derivative, or ``bounded at 0``.

Nothing here uses a float (D7).  Each answer is checked by a column-3
script that differentiates the texts with its own code
(:mod:`glm_universal.runtime.derivation_frames`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import symbolic as S
from .symbolic import RF, Poly, SymbolicError

__all__ = ["subs", "canonical_trig", "trig_normal", "Motion",
           "equations_of_motion", "Transfer", "transfer_functions",
           "Profile", "boundary_value_profile", "rf_solve_linear",
           "equation_text", "proportional", "dynamic_names"]


# ===========================================================================
# 1.  SUBSTITUTION AND NORMAL FORMS
# ===========================================================================

def subs(rf: RF, mapping: Dict[str, RF], ctx: S.Context) -> RF:
    """``rf`` with every variable of ``mapping`` replaced, inside atoms too
    (an atom whose argument changes is rebuilt, so ``sin(0)`` is ``0``)."""
    rf = RF.of(rf)
    cache: Dict[str, RF] = {}

    def val(v: str) -> Optional[RF]:
        if v in cache:
            return cache[v]
        out = None
        if v in mapping:
            out = RF.of(mapping[v])
        elif v in ctx.atoms:
            a = ctx.atoms[v]
            if a.arg is not None and a.kind in ("sin", "cos", "exp", "ln",
                                                "sqrt"):
                new = subs(a.arg, mapping, ctx)
                if not (new - a.arg).is_zero():
                    out = S.apply_function(a.kind, new, ctx)
        cache[v] = out
        return out

    def sp(p: Poly) -> RF:
        total = RF(Poly())
        for m, c in p.t.items():
            term = RF(Poly.const(c))
            for v, e in m:
                w = val(v)
                term = term * (RF(Poly.var(v, e)) if w is None else w ** e)
            total = total + term
        return total

    return sp(rf.num) / sp(rf.den)


def canonical_trig(rf: RF, ctx: S.Context) -> RF:
    """``sin(-a) = -sin(a)``, ``cos(-a) = cos(a)``: every trigonometric atom
    whose argument gives its alphabetically first letter a negative
    coefficient is replaced by the atom of the negated argument."""
    mapping: Dict[str, RF] = {}
    for name, a in list(ctx.atoms.items()):
        if a.kind in ("sin", "cos") and a.arg is not None and \
                a.arg.den.is_const() and not a.arg.num.is_zero():
            first = min(a.arg.num.vars(), default=None)
            if first is None:
                continue
            lead = a.arg.num.coeffs(first)
            top = max(k for k in lead if k)
            if lead[top].leading()[1] < 0:
                flipped = ctx.atom(a.kind, -a.arg)
                mapping[name] = -flipped if a.kind == "sin" else flipped
    return subs(rf, mapping, ctx) if mapping else rf


def trig_normal(rf: RF, ctx: S.Context) -> RF:
    """A normal form for comparison only: ``cos(a)^2`` reduced to
    ``1 - sin(a)^2`` for every argument."""
    out = canonical_trig(rf, ctx)
    for name, a in list(ctx.atoms.items()):
        if a.kind != "cos" or name not in out.num.vars() | out.den.vars():
            continue
        s = ctx.atom("sin", a.arg)
        out = out.num.reduce_power(name, 2, 1 - s * s) / \
            out.den.reduce_power(name, 2, 1 - s * s)
    return out


def proportional(a: RF, b: RF, dynamic: Sequence[str], ctx: S.Context
                 ) -> bool:
    """Whether ``a = c b`` with ``c`` nonzero and free of every dynamic
    name (and of every atom built on one)."""
    a, b = trig_normal(a, ctx), trig_normal(b, ctx)
    if a.is_zero() or b.is_zero():
        return a.is_zero() and b.is_zero()
    r = a / b
    dyn = set(dynamic) | {n for n, at in ctx.atoms.items()
                          if at.arg is not None and
                          at.arg.vars() & set(dynamic)}
    return not (r.vars() & dyn)


def dynamic_names(coords: Sequence[str]) -> List[str]:
    out = []
    for q in coords:
        out += [q, q + "_dot", q + "_ddot"]
    return out


def _dynamic_closure(names: Sequence[str], ctx: S.Context) -> set:
    dyn = set(names)
    grew = True
    while grew:
        grew = False
        for n, at in ctx.atoms.items():
            if n not in dyn and at.arg is not None and at.arg.vars() & dyn:
                dyn.add(n)
                grew = True
    return dyn


def _strip_factor(rf: RF, dyn: set, coords: Sequence[str]
                  ) -> Tuple[RF, str, RF]:
    """Divide ``rf`` by the factor of its numerator that is free of every
    dynamic name (the gcd of its coefficients as a polynomial in the dynamic
    names) and by the monomial content in the coordinates; make the first
    acceleration term's coefficient positive.  ``(result, condition text,
    divisor)`` with ``rf = divisor * result``."""
    num = rf.num
    groups: Dict[Tuple, Poly] = {}
    for m, c in num.t.items():
        dpart = tuple((v, e) for v, e in m if v in dyn)
        rest = tuple((v, e) for v, e in m if v not in dyn)
        groups[dpart] = groups.get(dpart, Poly()) + Poly({rest: c})
    g = None
    for coef in groups.values():
        g = coef if g is None else S.poly_gcd(g, coef)
    cond = []
    out = rf
    divisor = RF(Poly.const(1))
    if g is not None and not g.is_const():
        out = RF(S.divide_exact(num, g), rf.den)
        cond.append(S.to_text(RF(g)))
        divisor = divisor * RF(g)
    mc = dict(out.num.monomial_content())
    mono = {v: e for v, e in mc.items() if v in coords}
    if mono:
        mp = Poly({tuple(sorted(mono.items())): Fraction(1)})
        out = RF(S.divide_exact(out.num, mp), out.den)
        cond.append(S.to_text(RF(mp)))
        divisor = divisor * RF(mp)
    # sign: the leading term among accelerations positive
    accs = sorted((v for v in out.num.vars() if v.endswith("_ddot")))
    lead = None
    for m, c in sorted(out.num.t.items(), key=lambda kv: repr(kv[0])):
        if any(v in accs for v, _ in m):
            lead = c
            break
    if lead is None and out.num.t:
        lead = out.num.leading()[1]
    if lead is not None and lead < 0:
        out, divisor = -out, -divisor
    return out, " and ".join(f"{c} != 0" for c in cond), divisor


def _sqrt_text(t: str) -> str:
    """``2^(1/2)`` written ``sqrt(2)``."""
    return re.sub(r"\b(\d+)\^\(1/2\)", r"sqrt(\1)", t)


class Printer:
    """Formulas written with the letters in the order the question wrote
    them (``rho*F*Cp``, not ``Cp*F*rho``), a sum factor before a monomial
    (``(C1 - C2)*R1*R2``), and equations grouped by their dynamic part
    (``(m1 + m2)*x_ddot - (m1 - m2)*g = 0``)."""

    def __init__(self, source: str, ctx: S.Context):
        self.ctx = ctx
        seen: List[str] = []
        for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]*",
                            S.normalise_text(source)):
            if w not in seen:
                seen.append(w)
        self.order = seen

    def _alias(self, names) -> Dict[str, str]:
        plain = sorted((n for n in names if n not in self.ctx.atoms and
                        n not in S.RADICALS),
                       key=lambda n: (self.order.index(n) if n in self.order
                                      else len(self.order), n))
        atoms = sorted((n for n in names if n in self.ctx.atoms), key=str)
        out = {n: f"zz{i:03d}" for i, n in enumerate(plain)}
        out.update({n: f"zzz{i:03d}" for i, n in enumerate(atoms)})
        return out

    @staticmethod
    def _ren(p: Poly, al: Dict[str, str]) -> Poly:
        return Poly({tuple(sorted((al.get(v, v), e) for v, e in m)): c
                     for m, c in p.t.items()})

    @staticmethod
    def _back(text: str, al: Dict[str, str]) -> str:
        inv = {v: k for k, v in al.items()}
        return re.sub(r"\bzzz?\d{3}\b", lambda m: inv[m.group(0)], text)

    def _parts(self, p: Poly, al) -> Tuple[Fraction, str, str, int]:
        """``(rational factor, sum text, monomial text, terms in the sum)``."""
        if p.is_zero():
            return Fraction(0), "", "", 0
        c = p.content()
        negative = sum(1 for v in p.t.values() if v < 0)
        if 2 * negative > len(p.t):        # a tie keeps the sign inside
            c = -c
        q = p.scale(1 / c)
        mc = q.monomial_content()
        if mc:
            mp = Poly({mc: Fraction(1)})
            q = S.divide_exact(q, mp)
        mono = self._back(S._mono_text(tuple(sorted(
            (al.get(v, v), e) for v, e in mc))), al) if mc else ""
        if len(q.t) == 1:
            (m, v), = q.t.items()
            c = c * v
            extra = self._back(S._mono_text(tuple(sorted(
                (al.get(x, x), e) for x, e in m))), al) if m else ""
            mono = "*".join(x for x in (extra, mono) if x)
            return c, "", mono, 1
        return c, self._back(S._poly_text(self._ren(q, al)), al), mono, \
            len(q.t)

    def text(self, rf) -> str:
        rf = RF.of(rf)
        if rf.is_zero():
            return "0"
        al = self._alias(rf.vars())
        cn, sn, mn, _ = self._parts(rf.num, al)
        cd, sd, md, _ = self._parts(rf.den, al)
        c = cn / cd
        sign = "-" if c < 0 else ""
        a = abs(c)
        top = [str(a.numerator)] if a.numerator != 1 else []
        top += [f"({sn})"] if sn else []
        top += [mn] if mn else []
        bot = [str(a.denominator)] if a.denominator != 1 else []
        bot += [f"({sd})"] if sd else []
        bot += [md] if md else []
        num = "*".join(top) or "1"
        if bot == [str(a.denominator)] and (sn or mn):
            rest = "*".join(x for x in ([f"({sn})"] if sn else []) +
                            ([mn] if mn else []))
            lead = f"({a.numerator}/{a.denominator})"
            return _sqrt_text(f"{sign}{lead}*{rest}")
        if not bot:
            if not sign and sn and len(top) == 1:
                return _sqrt_text(sn)          # a bare sum needs no brackets
            return _sqrt_text(sign + num)
        den = "*".join(bot)
        if len(bot) > 1 or (md and "*" in md):
            den = f"({den})"
        return _sqrt_text(f"{sign}{num}/{den}")

    def equation(self, rf, coords: Sequence[str]) -> str:
        """``rf = 0`` grouped by dynamic monomial: accelerations, then
        velocities, then coordinates (in coordinate order), then the rest."""
        return self.sum(rf, coords) + " = 0"

    def sum(self, rf, coords: Sequence[str]) -> str:
        """``rf`` grouped by dynamic monomial, as :meth:`equation`."""
        rf = RF.of(rf)
        dyn = _dynamic_closure(dynamic_names(coords), self.ctx)
        groups: Dict[Tuple, Poly] = {}
        for m, c in rf.num.t.items():
            dpart = tuple((v, e) for v, e in m if v in dyn)
            rest = tuple((v, e) for v, e in m if v not in dyn)
            groups[dpart] = groups.get(dpart, Poly()) + Poly({rest: c})

        def rank(dpart):
            names = [v for v, _ in dpart]
            for level, suffix in enumerate(("_ddot", "_dot")):
                for i, q in enumerate(coords):
                    if q + suffix in names:
                        return (level, i, repr(dpart))
            for i, q in enumerate(coords):
                if q in names:
                    return (2, i, repr(dpart))
            return (3 if dpart else 4, 0, repr(dpart))

        den_dyn = {v: e for v, e in dict(rf.den.monomial_content()).items()
                   if v in dyn} if len(rf.den.t) == 1 else {}
        den_rest = rf.den
        if den_dyn:
            den_rest = S.divide_exact(rf.den, Poly(
                {tuple(sorted(den_dyn.items())): Fraction(1)}))
        out = ""
        for i, dpart in enumerate(sorted(groups, key=rank)):
            coef = RF(groups[dpart]) / RF(den_rest)
            mono = RF(Poly({dpart: Fraction(1)}))
            if den_dyn:
                mono = mono / RF(Poly({tuple(sorted(den_dyn.items())):
                                       Fraction(1)}))
            ct = self.text(coef)
            neg = ct.startswith("-")
            if neg:
                ct = ct[1:]
            mt = self.text(mono) if dpart or den_dyn else ""
            if mt == "1":
                mt = ""
            if mt.startswith("1/"):
                term = f"{ct}{mt[1:]}" if ct != "1" else mt
                if ct != "1" and (" " in ct):
                    term = f"({ct}){mt[1:]}"
            elif not mt:
                term = ct
            elif ct == "1":
                term = mt
            else:
                if " " in ct and not (ct.startswith("(") and
                                      ct.endswith(")")):
                    ct = f"({ct})"
                term = f"{ct}*{mt}"
            if i == 0:
                out = ("-" if neg else "") + term
            else:
                out += (" - " if neg else " + ") + term
        return out or "0"


def equation_text(rf: RF, coords: Sequence[str] = (), source: str = "",
                  ctx: Optional[S.Context] = None) -> str:
    """``rf = 0`` as :class:`Printer` writes it."""
    return Printer(source, ctx or S.Context()).equation(rf, coords)


# ===========================================================================
# 2.  EULER-LAGRANGE
# ===========================================================================

@dataclass
class Motion:
    coords: List[str]
    lagrangian: RF
    ctx: S.Context
    equations: List[RF]
    conditions: List[str]
    divisors: List[RF] = field(default_factory=list)
    linear: Optional[List[RF]] = None
    mass: Optional[List[List[RF]]] = None
    stiffness: Optional[List[List[RF]]] = None
    damping_free: bool = True
    characteristic: Optional[RF] = None
    frequencies: Optional[List[RF]] = None
    frequency_note: str = ""
    #: Phase 108: the algebraic numbers the frequencies hold, name ->
    #: (monic polynomial from the constant term up, lo, hi)
    frequency_algs: Dict[str, tuple] = field(default_factory=dict)
    #: sharpening pass: the characteristic cubic answered stepwise -- its
    #: coefficients ``[c0, c1, c2, c3]`` in ``w2`` (``c3 > 0``) when the
    #: route ``modes.cubic:stepwise`` is taken, with the route's reason
    modes_cubic: Optional[List[RF]] = None
    modes_route: str = ""
    #: Phase 109: four or more degrees of freedom answered stepwise -- the
    #: characteristic polynomial's coefficients ``[c0, ..., cn]`` in ``w2``
    #: (``cn > 0``) and the route taken at ``modes.higher`` (``"ferrari"``
    #: for a quartic, ``"named"`` for degree five or more)
    modes_poly: Optional[List[RF]] = None
    modes_method: str = ""
    #: Phase 114: on the ``named`` route, the reason no formula in radicals
    #: of the letters gives the roots (a positive point where the polynomial
    #: passes a radical-free certificate), or ``""``
    modes_radical: str = ""
    #: the symmetric pair read off the Lagrangian (``M`` from the
    #: velocities, ``K`` from the coordinates) and what was decided of it
    definite: Dict[str, bool] = field(default_factory=dict)


def _ddt(f: RF, coords: Sequence[str], ctx: S.Context) -> RF:
    out = RF(Poly())
    for q in coords:
        out = out + S.diff(f, q, ctx) * RF(Poly.var(q + "_dot"))
        out = out + S.diff(f, q + "_dot", ctx) * RF(Poly.var(q + "_ddot"))
    return out


def equations_of_motion(lagrangian_text: str, coords: Sequence[str],
                        small: bool = False) -> Motion:
    """The Euler-Lagrange equations of ``L`` in ``coords``; with ``small``
    the linearisation about the origin and the normal modes."""
    coords = [S.normalise_text(q) for q in coords]
    ctx = S.Context()
    L = S.parse(lagrangian_text, ctx)
    L = canonical_trig(L, ctx)
    for q in coords:
        if q.endswith("_dot") or q.endswith("_ddot"):
            raise SymbolicError("UNREADABLE", f"{q} is a velocity, not a "
                                              f"coordinate")
    names = set(L.vars())
    for a in ctx.atoms.values():
        if a.arg is not None:
            names |= a.arg.vars()
    for q in coords:
        if q not in names and q + "_dot" not in names:
            raise SymbolicError("NOT_IN_LAGRANGIAN",
                                f"neither {q} nor {q}_dot occurs in L")
    dyn = _dynamic_closure(dynamic_names(coords), ctx)
    for v in names:
        if v.endswith("_ddot"):
            raise SymbolicError("UNREADABLE", f"{v}: a Lagrangian holds no "
                                              f"acceleration")
    eqs, conds, divs = [], [], []
    for q in coords:
        e = _ddt(S.diff(L, q + "_dot", ctx), coords, ctx) - S.diff(L, q, ctx)
        e = canonical_trig(e, ctx)
        e, c, dv = _strip_factor(e, _dynamic_closure(dynamic_names(coords),
                                                     ctx), coords)
        eqs.append(e)
        conds.append(c)
        divs.append(dv)
    mo = Motion(list(coords), L, ctx, eqs, conds, divs)
    if small:
        _linearise(mo)
    return mo


def _linearise(mo: Motion) -> None:
    ctx, coords = mo.ctx, mo.coords
    zero = {v: RF(Poly()) for v in dynamic_names(coords)}
    lin, M, K = [], [], []
    damping = False
    for e in mo.equations:
        try:
            e0 = subs(e, zero, ctx)
        except ZeroDivisionError:
            raise SymbolicError("SINGULAR", "the equations are singular at "
                                            "the origin")
        if not e0.is_zero():
            raise SymbolicError("NOT_EQUILIBRIUM",
                                f"the origin is not an equilibrium: the "
                                f"equation reads {S.to_text(e0)} = 0 there")
        row_m, row_k = [], []
        total = RF(Poly())
        for q in coords:
            cm = subs(S.diff(e, q + "_ddot", ctx), zero, ctx)
            cv = subs(S.diff(e, q + "_dot", ctx), zero, ctx)
            ck = subs(S.diff(e, q, ctx), zero, ctx)
            if not cv.is_zero():
                damping = True
            row_m.append(cm)
            row_k.append(ck)
            total = total + cm * RF(Poly.var(q + "_ddot")) + \
                cv * RF(Poly.var(q + "_dot")) + ck * RF(Poly.var(q))
        total = _strip_factor(total, set(dynamic_names(coords)), [])[0]
        lin.append(total)
        M.append(row_m)
        K.append(row_k)
    mo.linear, mo.mass, mo.stiffness = lin, M, K
    mo.damping_free = not damping
    if damping:
        mo.frequency_note = ("a velocity term survives the linearisation, so "
                             "the modes are not undamped oscillations; no "
                             "frequencies are given")
        return
    w2 = RF(Poly.var("w2"))
    n = len(coords)
    A = [[K[i][j] - w2 * M[i][j] for j in range(n)] for i in range(n)]
    det = _rf_det(A)
    mo.characteristic = det
    if det.is_zero():
        mo.frequency_note = "the characteristic polynomial vanishes"
        return
    # sharpening pass: what the Lagrangian itself decides about the modes.
    # M and K read off L at the origin are symmetric; when every leading
    # minor of M is plainly positive (every coefficient positive, the
    # letters positive) the pencil is definite and every root w2 is real
    # (and positive when K is so too) -- a fact the solver, handed only the
    # polynomial, cannot see.  It is passed on as a stated fact, and for a
    # cubic in letters whose coefficients do not scale together it selects
    # the stepwise route, which names the roots through the coefficients
    # instead of expanding them.
    from . import routes as R
    Ms, Ks = _symmetric_pair(mo)
    mo.definite = {"M": _plainly_definite(Ms), "K": _plainly_definite(Ks)}
    from .symbolic_nonlinear import solve_nonlinear
    if n >= 4:
        # Phase 109: four or more degrees of freedom.  The branch layer is
        # not reached when the pair is definite: a quartic in letters sent
        # there ran for minutes in its gcds and a quintic has no radical
        # form at all.  The roots are written in steps instead.
        poly = _char_poly(det, n)
        why = ("M and K are symmetric and M is positive definite (every "
               "leading minor has positive coefficients, the letters "
               "positive), so the " + _NUMBER_WORDS.get(n, str(n)) +
               " roots are real" + (" and positive (K definite too)"
                                    if mo.definite["K"] else ""))
        dec = R.choose("modes.higher", [
            ("ferrari", mo.definite["M"] and poly is not None and n == 4,
             why + "; a quartic: depressed, its resolvent cubic solved by "
                   "Viete, the roots from square roots of its roots"),
            ("named", mo.definite["M"] and poly is not None and n >= 5,
             why + "; degree " + str(n) + ": no general radical form, so "
                   "the roots are named through the coefficients"),
            ("solver", True, "the characteristic equation goes to the "
                             "branch layer"),
        ])
        mo.modes_route = dec.text()
        if dec.route in ("ferrari", "named"):
            mo.modes_poly = poly
            mo.modes_method = dec.route
            if dec.route == "named":
                # Phase 114 (studies/PRIMITIVE_RADICAL_STUDY.md): say why no
                # radical formula exists for these roots, not only that no
                # general one does.
                from .symbolic_nonlinear import modes_radical_reason
                mo.modes_radical = modes_radical_reason(poly) or ""
            return
    else:
        cub = _char_cubic(det) if n == 3 else None
        dec = R.choose("modes.cubic", [
            ("stepwise", n == 3 and mo.definite["M"] and cub is not None
             and not _scales_together(cub),
             "M and K are symmetric and M is positive definite (every leading "
             "minor has positive coefficients, the letters positive), so the "
             "three roots are real" + (" and positive (K definite too)"
                                       if mo.definite["K"] else "") +
             "; the coefficients do not scale together, so the roots are "
             "named through them rather than expanded"),
            ("solver", True, "the characteristic equation goes to the branch "
                             "layer" + (" with its roots stated real"
                                        if mo.definite["M"] else "")),
        ])
        mo.modes_route = dec.text()
        if dec.route == "stepwise":
            mo.modes_cubic = cub
            return
    try:
        with R.facts(real_roots=mo.definite["M"]):
            br = solve_nonlinear([(det, RF(Poly()))], {"w2"}, ["w2"],
                                 extended=True)
    except SymbolicError as exc:
        mo.frequency_note = f"the characteristic equation was not solved " \
                            f"({exc.code})"
        return
    roots = []
    algs = {}
    for sol in br.solutions:
        k, v = sol.values["w2"]
        if k == 1 and not any((v - r).is_zero() for r in roots):
            roots.append(v)
            ext = getattr(sol, "ext", None)
            if ext is not None:
                if any(g in ext.trig for g in v.vars()):
                    # a Viete root, which the motion script does not
                    # carry: the modes are stated, not listed
                    mo.frequency_note = ("the characteristic equation's "
                                         "roots hold a generator the motion "
                                         "check does not carry")
                    return
                for g in v.vars():
                    if g in ext.algs:
                        a = ext.algs[g]
                        algs[g] = (list(a.m), a.lo, a.hi)
    mo.frequencies = roots
    mo.frequency_algs = algs


def _symmetric_pair(mo: Motion) -> Tuple[List[List[RF]], List[List[RF]]]:
    """``(M, K)`` with ``M_ij = d2L/dqi_dot dqj_dot`` and ``K_ij =
    -d2L/dqi dqj`` at the origin: the symmetric pair of the quadratic
    Lagrangian (the rows of the linearised equations may be scaled, these
    are not)."""
    ctx, coords = mo.ctx, mo.coords
    zero = {v: RF(Poly()) for v in dynamic_names(coords)}
    Ms, Ks = [], []
    for qi in coords:
        dv = S.diff(mo.lagrangian, qi + "_dot", ctx)
        dq = S.diff(mo.lagrangian, qi, ctx)
        Ms.append([subs(S.diff(dv, qj + "_dot", ctx), zero, ctx)
                   for qj in coords])
        Ks.append([-subs(S.diff(dq, qj, ctx), zero, ctx) for qj in coords])
    return Ms, Ks


def _plainly_positive(v: RF) -> bool:
    return not v.is_zero() and all(c > 0 for c in v.num.t.values()) and \
        all(c > 0 for c in v.den.t.values())


def _plainly_definite(A: List[List[RF]]) -> bool:
    """Sylvester's criterion with every leading minor plainly positive
    (all coefficients positive, so positive whenever the letters are)."""
    n = len(A)
    if any(not (A[i][j] - A[j][i]).is_zero() for i in range(n)
           for j in range(n)):
        return False
    return all(_plainly_positive(_rf_det([row[:k] for row in A[:k]]))
               for k in range(1, n + 1))


def _char_cubic(det: RF) -> Optional[List[RF]]:
    """``[c0, c1, c2, c3]`` of ``det`` as a cubic in ``w2`` with ``c3``'s
    leading coefficient positive, or ``None`` when it is not one."""
    if not det.den.is_const() or det.num.deg("w2") != 3:
        return None
    cs = det.num.coeffs("w2")
    sgn = -1 if cs[3].leading()[1] < 0 else 1
    out = [RF(cs.get(i, Poly()).scale(Fraction(sgn) / det.den.const_value()))
           for i in range(4)]
    if any(v.vars() & {"w2"} for v in out) or out[3].is_const() and \
            all(v.is_const() for v in out):
        return None
    return out


_NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
                 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def _char_poly(det: RF, n: int) -> Optional[List[RF]]:
    """``[c0, ..., cn]`` of ``det`` as a polynomial of degree ``n`` in
    ``w2`` with ``cn``'s leading coefficient positive, or ``None`` when it is
    not one with coefficients in the letters (Phase 109)."""
    if not det.den.is_const() or det.num.deg("w2") != n:
        return None
    cs = det.num.coeffs("w2")
    sgn = -1 if cs[n].leading()[1] < 0 else 1
    out = [RF(cs.get(i, Poly()).scale(Fraction(sgn) / det.den.const_value()))
           for i in range(n + 1)]
    if any(v.vars() & {"w2"} for v in out):
        return None
    return out


def _scales_together(cs: List[RF]) -> bool:
    """Whether ``P^3/Q^2`` of the depressed cubic is a number (the
    homogeneous route then answers it exactly), decided cheaply: compared at
    three rational points first, and exactly only if they agree."""
    c0, c1, c2, c3 = cs
    Pn = c3 * c1 * 3 - c2 * c2
    Qn = c2 * c2 * c2 * 2 - c3 * c2 * c1 * 9 + c3 * c3 * c0 * 27
    if Qn.is_zero() or Pn.is_zero():
        return True
    # P^3/Q^2 = Pn^3 * 27^2 c3^6 / (27 c3^6 ... ): up to a number,
    # Pn^3 / Qn^2
    names = sorted(set().union(*(v.vars() for v in cs)))
    seen = None
    for k in range(3):
        pt = {v: Fraction(3 + 2 * i + k, 2 + (i + k) % 3)
              for i, v in enumerate(names)}
        try:
            q = Qn.evaluate(pt)
            r = Pn.evaluate(pt) ** 3 / (q * q)
        except ZeroDivisionError:
            continue
        if seen is not None and r != seen:
            return False
        seen = r
    return (Pn * Pn * Pn / (Qn * Qn)).is_const()


def _rf_det(A: List[List[RF]]) -> RF:
    n = len(A)
    if n == 1:
        return A[0][0]
    total = RF(Poly())
    for j in range(n):
        minor = [row[:j] + row[j + 1:] for row in A[1:]]
        term = A[0][j] * _rf_det(minor)
        total = total + (term if j % 2 == 0 else -term)
    return total


# ===========================================================================
# 3.  LINEAR SYSTEMS OVER RATIONAL FUNCTIONS
# ===========================================================================

def rf_solve_linear(rows: List[List[RF]], rhs: List[RF]
                    ) -> Tuple[str, Optional[List[RF]]]:
    """Gaussian elimination: ``("unique", x)``, ``("inconsistent", None)``
    or ``("underdetermined", None)``."""
    n = len(rows[0]) if rows else 0
    A = [list(r) + [b] for r, b in zip(rows, rhs)]
    piv_cols = []
    r = 0
    for c in range(n):
        p = next((i for i in range(r, len(A)) if not A[i][c].is_zero()), None)
        if p is None:
            continue
        A[r], A[p] = A[p], A[r]
        inv = 1 / A[r][c]
        A[r] = [x * inv for x in A[r]]
        for i in range(len(A)):
            if i != r and not A[i][c].is_zero():
                f = A[i][c]
                A[i] = [x - f * y for x, y in zip(A[i], A[r])]
        piv_cols.append(c)
        r += 1
    for i in range(r, len(A)):
        if not A[i][n].is_zero():
            return "inconsistent", None
    if r < n:
        return "underdetermined", None
    x = [RF(Poly())] * n
    for i, c in enumerate(piv_cols):
        x[c] = A[i][n]
    return "unique", x


# ===========================================================================
# 4.  TRANSFER FUNCTIONS
# ===========================================================================

_D2 = re.compile(r"d2\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*/\s*dt2")
_D1 = re.compile(r"d\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*/\s*dt")


@dataclass
class Transfer:
    inputs: List[str]
    outputs: List[str]
    states: List[str]
    ctx: S.Context
    deviation: List[RF]
    functions: Dict[Tuple[str, str], RF] = field(default_factory=dict)
    standard: Dict[Tuple[str, str], str] = field(default_factory=dict)


def _model_text(t: str) -> Tuple[str, set, set]:
    t = S.normalise_text(t)
    d2 = set(_D2.findall(t))
    t = _D2.sub(lambda m: f"{m.group(1)}__dd", t)
    d1 = set(_D1.findall(t))
    t = _D1.sub(lambda m: f"{m.group(1)}__d", t)
    return t, d1, d2


def transfer_functions(equation_texts: Sequence[str], inputs: Sequence[str],
                       outputs: Sequence[str]) -> Transfer:
    """Every ``output(s)/input(s)`` of the model, linearised about its
    steady state, in deviation variables."""
    inputs = [S.normalise_text(u) for u in inputs]
    outputs = [S.normalise_text(y) for y in outputs]
    ctx = S.Context()
    texts, states = [], set()
    for e in equation_texts:
        t, d1, d2 = _model_text(e)
        texts.append(t)
        states |= d1 | d2
    eqs = []
    for t in texts:
        lhs, rhs = S.parse_equation(t, ctx)
        eqs.append(lhs - rhs)
    present = set()
    for g in eqs:
        present |= g.vars()
        for a in ctx.atoms.values():
            if a.arg is not None and a.name in g.vars():
                present |= a.arg.vars()
    for y in outputs:
        if y not in present and y + "__d" not in present:
            raise SymbolicError("NOT_IN_SYSTEM", f"{y} occurs in no equation")
    for u in inputs:
        if u not in present:
            raise SymbolicError("NOT_IN_SYSTEM", f"{u} occurs in no equation")
        if u in states:
            raise SymbolicError("UNREADABLE", f"{u} is an input and has a "
                                              f"derivative")
    unknowns = sorted(states | set(outputs))
    if len(unknowns) > len(eqs):
        raise SymbolicError("UNDERDETERMINED",
                            f"{len(eqs)} equation(s) for {len(unknowns)} "
                            f"unknown(s): {', '.join(unknowns)}")
    dyn = unknowns + inputs
    ss: Dict[str, RF] = {}
    for v in dyn:
        ss[v] = RF(Poly.var(v + "_s"))
        ss[v + "__d"] = RF(Poly())
        ss[v + "__dd"] = RF(Poly())
    s = RF(Poly.var("s"))
    dev, rows, rhs_cols = [], [], []
    for g in eqs:
        total = RF(Poly())
        row = []
        for v in unknowns:
            c0 = subs(S.diff(g, v, ctx), ss, ctx)
            c1 = subs(S.diff(g, v + "__d", ctx), ss, ctx)
            c2 = subs(S.diff(g, v + "__dd", ctx), ss, ctx)
            row.append(c0 + c1 * s + c2 * s * s)
            total = total + c0 * RF(Poly.var(v)) + \
                c1 * RF(Poly.var(v + "__d")) + c2 * RF(Poly.var(v + "__dd"))
        cols = []
        for u in inputs:
            cu = subs(S.diff(g, u, ctx), ss, ctx)
            cols.append(cu)
            total = total + cu * RF(Poly.var(u))
        dev.append(total)
        rows.append(row)
        rhs_cols.append(cols)
    tr = Transfer(list(inputs), list(outputs), sorted(states), ctx, dev)
    for j, u in enumerate(inputs):
        status, x = rf_solve_linear(rows, [-c[j] for c in rhs_cols])
        if status != "unique":
            raise SymbolicError("UNDERDETERMINED" if status ==
                                "underdetermined" else "INCONSISTENT",
                                f"the transformed model has no unique "
                                f"solution for input {u}")
        for y in outputs:
            G = x[unknowns.index(y)]
            tr.functions[(y, u)] = G
            tr.standard[(y, u)] = standard_form(G)
    return tr


def standard_form(G: RF) -> str:
    """``K/(tau*s + 1)`` for a first-order lag, ``K/(tau^2*s^2 + 2*zeta*tau*s
    + 1)`` written by its coefficients for a second-order one, else ``""``."""
    if "s" in G.num.vars():
        return ""
    cs = G.den.coeffs("s")
    deg = G.den.deg("s")
    c0 = cs.get(0, Poly())
    if c0.is_zero() or deg not in (1, 2):
        return ""
    K = RF(G.num) / RF(c0)
    if deg == 1:
        tau = RF(cs.get(1, Poly())) / RF(c0)
        return f"K/(tau*s + 1) with K = {S.to_text(K)}, tau = {S.to_text(tau)}"
    a2 = RF(cs.get(2, Poly())) / RF(c0)
    a1 = RF(cs.get(1, Poly())) / RF(c0)
    return (f"K/(tau^2*s^2 + 2*zeta*tau*s + 1) with K = {S.to_text(K)}, "
            f"tau^2 = {S.to_text(a2)}, 2*zeta*tau = {S.to_text(a1)}")


def deviation_text(rf: RF, printer: Optional["Printer"] = None) -> str:
    """A deviation equation with ``X'`` for the deviation of ``X``."""
    t = printer.text(rf) if printer is not None else S.to_text(rf)
    t = re.sub(r"([A-Za-z_][A-Za-z0-9_]*)__dd", r"d2(\1')/dt2", t)
    t = re.sub(r"([A-Za-z_][A-Za-z0-9_]*)__d", r"d(\1')/dt", t)
    return t + " = 0"


# ===========================================================================
# 5.  PROFILES BY TWO QUADRATURES
# ===========================================================================

@dataclass
class Profile:
    y: str
    x: str
    ctx: S.Context
    flux: RF                         # P
    source: RF                       # G
    general: RF                      # with constants c__1, c__2
    profile: RF
    conditions: List[str]


_ODE = re.compile(r"^d/d([A-Za-z_][A-Za-z0-9_]*)\((.*)d\(\s*([A-Za-z_]"
                  r"[A-Za-z0-9_]*)\s*\)/d([A-Za-z_][A-Za-z0-9_]*)\)$")


def _split_flux(inner: str) -> str:
    inner = inner.strip()
    if not inner:
        return "1"
    if not inner.endswith("*"):
        raise SymbolicError("UNREADABLE", "write d/dx(P*d(y)/dx)")
    return inner[:-1]


def _poly_in(rf: RF, x: str) -> Dict[int, RF]:
    """``rf`` as ``sum c_k x^k`` (``k`` may be negative when the denominator
    is a power of ``x``), coefficients free of ``x``."""
    den = rf.den
    shift = 0
    if x in den.vars():
        if len(den.t) != 1:
            raise SymbolicError("UNSUPPORTED", "a denominator in x that is "
                                               "not a power of x")
        (m, c), = den.t.items()
        shift = dict(m).get(x, 0)
        den = Poly({tuple((v, e) for v, e in m if v != x): c})
    out: Dict[int, RF] = {}
    for k, coef in rf.num.coeffs(x).items():
        out[k - shift] = out.get(k - shift, RF(Poly())) + RF(coef) / RF(den)
    return out


# a basis function: ("pow", k) for x^k, ("ln", 0) for ln(x)
Basis = Tuple[str, int]


def _integrate(terms: Dict[Basis, RF]) -> Dict[Basis, RF]:
    out: Dict[Basis, RF] = {}
    for (kind, k), c in terms.items():
        if kind == "ln":
            raise SymbolicError("UNSUPPORTED", "a logarithm under the "
                                               "integral")
        if k == -1:
            b, v = ("ln", 0), c
        else:
            b, v = ("pow", k + 1), c / (k + 1)
        out[b] = out.get(b, RF(Poly())) + v
    return out


def _basis_rf(b: Basis, x: str, ctx: S.Context) -> RF:
    if b[0] == "ln":
        return ctx.atom("ln", RF(Poly.var(x)))
    return RF(Poly.var(x)) ** b[1]


def _basis_at(b: Basis, at: RF, ctx: S.Context) -> RF:
    if b[0] == "ln":
        return S.apply_function("ln", at, ctx)
    if b[1] < 0 and at.is_zero():
        raise SymbolicError("SINGULAR", "a boundary condition at a "
                                        "singular point")
    return at ** b[1]


def _basis_diff(b: Basis) -> Tuple[Basis, Fraction]:
    if b[0] == "ln":
        return ("pow", -1), Fraction(1)
    return ("pow", b[1] - 1), Fraction(b[1])


def boundary_value_profile(ode_text: str, conditions: Sequence[str]
                           ) -> Profile:
    t = S.normalise_text(ode_text).replace(" ", "")
    if t.count("=") != 1:
        raise SymbolicError("UNREADABLE", "one equation d/dx(P*d(y)/dx) = G")
    lhs, rhs = t.split("=")
    m = _ODE.match(lhs)
    if not m or not (m.group(1) == m.group(4)):
        raise SymbolicError("UNREADABLE", "write d/dx(P*d(y)/dx) = G")
    x, y = m.group(1), m.group(3)
    ctx = S.Context()
    P = S.parse(_split_flux(m.group(2)), ctx)
    G = S.parse(rhs, ctx)
    if ctx.atoms:
        raise SymbolicError("UNSUPPORTED", "a function of x in the flux or "
                                           "the source")
    pt = _poly_in(P, x)
    if len(pt) != 1:
        raise SymbolicError("UNSUPPORTED", "the flux coefficient is not a "
                                           "monomial c*x^n")
    (n, c), = pt.items()
    gt = _poly_in(G, x)
    if any(k < 0 for k in gt):
        raise SymbolicError("UNSUPPORTED", "the source is not a polynomial "
                                           "in x")
    c1, c2 = RF(Poly.var("c__1")), RF(Poly.var("c__2"))
    # P y' = int G + c1
    flux = _integrate({("pow", k): v for k, v in gt.items() if not
                       v.is_zero()})
    flux[("pow", 0)] = flux.get(("pow", 0), RF(Poly())) + c1
    yprime = {("pow", b[1] - n): v / c for b, v in flux.items()}
    ysol = _integrate(yprime)
    ysol[("pow", 0)] = ysol.get(("pow", 0), RF(Poly())) + c2
    eqs: List[RF] = []
    taken: List[str] = []
    for cond in conditions:
        ct = S.normalise_text(cond).strip()
        mb = re.fullmatch(rf"{re.escape(y)}\s+bounded\s+at\s+0", ct)
        mv = re.fullmatch(rf"{re.escape(y)}\((.+)\)\s*=\s*(.+)", ct)
        md = re.fullmatch(rf"d\({re.escape(y)}\)/d{re.escape(x)}\((.+)\)\s*="
                          rf"\s*(.+)", ct)
        if mb:
            for b, v in ysol.items():
                if b[0] == "ln" or b[1] < 0:
                    eqs.append(v)
            taken.append(f"{y} bounded at 0")
        elif md:
            at, val = S.parse(md.group(1), ctx), S.parse(md.group(2), ctx)
            tot = RF(Poly())
            for b, v in ysol.items():
                db, f = _basis_diff(b)
                if f:
                    tot = tot + v * f * _basis_at(db, at, ctx)
            eqs.append(tot - val)
            taken.append(ct)
        elif mv:
            at, val = S.parse(mv.group(1), ctx), S.parse(mv.group(2), ctx)
            tot = RF(Poly())
            for b, v in ysol.items():
                tot = tot + v * _basis_at(b, at, ctx)
            eqs.append(tot - val)
            taken.append(ct)
        else:
            raise SymbolicError("UNREADABLE", f"a boundary condition: {cond}")
    if len(taken) < 2:
        raise SymbolicError("UNDERDETERMINED", "two boundary conditions are "
                                               "needed")
    rows, rhs_ = [], []
    for e in eqs:
        a1 = S.diff(e, "c__1", ctx)
        a2 = S.diff(e, "c__2", ctx)
        rest = subs(e, {"c__1": RF(Poly()), "c__2": RF(Poly())}, ctx)
        rows.append([a1, a2])
        rhs_.append(-rest)
    status, sol = rf_solve_linear(rows, rhs_)
    if status != "unique":
        raise SymbolicError("INCONSISTENT" if status == "inconsistent"
                            else "UNDERDETERMINED",
                            f"the boundary conditions fix no unique profile "
                            f"({status})")
    general = RF(Poly())
    for b, v in ysol.items():
        general = general + v * _basis_rf(b, x, ctx)
    prof = subs(general, {"c__1": sol[0], "c__2": sol[1]}, ctx)
    return Profile(y, x, ctx, P, G, general, prof, taken)
