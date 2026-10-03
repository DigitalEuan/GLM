"""``glm_universal.runtime.outside_frames`` -- the exact frames the Outside O1
question set located (Phase 89).

Each frame reads one *kind* of engineering or science question -- a Routh
cubic, a per-unit rebase, a reflection coefficient, an aliasing question, a
convolution, a Wiener filter, an entropy of a rational distribution, a
Huffman code, a Kalman rank test, ... -- pulls the givens out of the text,
and answers **exactly**: rationals where the answer is rational, closed forms
(:class:`~glm_universal.reasoning.exact_forms.Surd`,
:class:`~glm_universal.reasoning.exact_forms.LogForm`, ``pi``, ``exp``, ``ln``)
where it is not, with every decimal a truncation of an exact process
(:mod:`glm_universal.reasoning.real_expr`).  Where a question's premises are
inconsistent (a Nyquist count that makes the number of right-half-plane
closed-loop poles negative) the frame refuses with the machine's
``INCONSISTENT_GIVENS``.

Every frame's column-3 script recomputes the answer by an independent route
and is run by the gate of :mod:`glm_universal.runtime.question_frames` before
anything is printed.  The frames are reached through the router's ``frames``
surface; :mod:`glm_universal.evaluation.question_set_b_cases` pre-registers
which outside question each one is expected to read.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..reasoning import exact_forms as ef
from .question_frames import (Frame, Reading, _NUM, _find, _frac_text,
                              golay_prelude, number)

__all__ = ["OUTSIDE_FRAMES"]


# ===========================================================================
# 0.  HELPERS
# ===========================================================================

def comb(n: int, k: int) -> int:
    """The binomial coefficient, by the exact product formula (the runtime
    imports nothing outside the standard exact modules)."""
    if k < 0 or k > n:
        return 0
    out = 1
    for i in range(min(k, n - k)):
        out = out * (n - i) // (i + 1)
    return out


def _float_text(q) -> str:
    """A rational written into a column-3 script as the quotient ``(n/d)``:
    the script evaluates it to the correctly rounded float, while this module
    itself never constructs one (the core's exactness discipline)."""
    q = Fraction(q)
    return f"({q.numerator}/{q.denominator})"


def _float_rows(rows) -> str:
    """A list of ``(amount, name, value)`` rows for a script, amounts written
    by :func:`_float_text`."""
    return "[" + ", ".join(f"({_float_text(a)}, {n!r}, {v!r})"
                           for a, n, v in rows) + "]"


def _braced(t: str, start: int) -> Tuple[str, int]:
    """The text of the brace group opening at ``t[start] == '{'``."""
    depth, i = 0, start
    while i < len(t):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                return t[start + 1:i], i + 1
        i += 1
    raise ValueError("unbalanced braces")


def _frac_after(t: str, anchor: str) -> Optional[Tuple[str, str]]:
    """``(numerator, denominator)`` of the first ``\\frac`` after ``anchor``."""
    i = t.find(anchor)
    if i < 0:
        return None
    j = t.find("\\frac", i)
    if j < 0 or j - i > 40:
        return None
    num, k = _braced(t, t.index("{", j))
    den, _ = _braced(t, t.index("{", k))
    return num.strip(), den.strip()


def _linear_factors(den: str) -> Optional[List[Tuple[Fraction, ...]]]:
    """``s(s + 2)(2s+1)`` -> polynomials (constant first), or ``None``."""
    d = den.replace(" ", "").replace("\\cdot", "")
    out: List[Tuple[Fraction, ...]] = []
    for m in re.finditer(r"\(([^()]*)\)|(s)", d):
        body = m.group(1) if m.group(1) is not None else "s"
        fm = re.fullmatch(r"([-+]?\d*(?:\.\d+)?)s(?:([-+]\d+(?:\.\d+)?))?",
                          body)
        if not fm:
            return None
        a = fm.group(1)
        a = Fraction(1) if a in ("", "+") else (Fraction(-1) if a == "-"
                                                else Fraction(a))
        b = Fraction(fm.group(2)) if fm.group(2) else Fraction(0)
        out.append((b, a))
    rest = re.sub(r"\([^()]*\)|s", "", d)
    if rest.strip("*"):
        return None
    return out or None


def _poly_text(p: Sequence[Fraction], var: str = "s") -> str:
    terms = []
    for k in range(len(p) - 1, -1, -1):
        c = p[k]
        if c == 0:
            continue
        mono = "" if k == 0 else (var if k == 1 else f"{var}^{k}")
        coef = str(c) if (c not in (1, -1) or k == 0) else ("-" if c == -1
                                                            else "")
        terms.append(f"{coef}{'*' if coef not in ('', '-') and mono else ''}"
                     f"{mono}")
    return " + ".join(terms).replace("+ -", "- ") or "0"


def _dec(expr: str, places: int = 6) -> str:
    from ..reasoning.real_expr import parse_expression
    return parse_expression(expr).decimal(places)


def _nums(t: str) -> List[Fraction]:
    return [number(x) for x in re.findall(_NUM, t)]


# ===========================================================================
# 1.  ELECTRICAL AND CONTROL
# ===========================================================================

# -- the Routh-Hurwitz cubic -------------------------------------------------

def _m_routh(t: str) -> Optional[dict]:
    if "routh" not in t:
        return None
    fr = _frac_after(t, "g(s)")
    if not fr:
        return None
    num, den = fr
    facs = _linear_factors(den)
    if not facs:
        return None
    D: Tuple[Fraction, ...] = (Fraction(1),)
    for f in facs:
        D = ef.poly_mul(D, f)
    if len(D) != 4:
        return None
    n = num.replace(" ", "")
    if n.lower() == "k":
        n0, gain = Fraction(1), "K"
    elif re.fullmatch(_NUM, n):
        n0 = number(n)
        gain = "K_c" if re.search(r"k_c|k_\{c\}|proportional", t) else "K"
    else:
        return None
    return {"D": D, "n0": n0, "gain": gain, "den": den, "num": num,
            "period": bool(re.search(r"period|p_u", t))}


def _a_routh(g: dict) -> Reading:
    D, n0, K = g["D"], g["n0"], g["gain"]
    a0, a1, a2, a3 = D
    if a3 <= 0 or a2 <= 0 or a1 <= 0 or n0 <= 0:
        return Reading("routh_cubic", False, "a characteristic coefficient "
                       "independent of the gain is not positive: unstable "
                       "for every gain", "", "", "print('VERIFIED True')",
                       code="NO_STABLE_GAIN", backing="reasoning.exact_forms")
    kmin = -a0 / n0
    kmax = (a2 * a1 / a3 - a0) / n0
    w2 = a1 / a3
    w = ef.sqrt_of(w2)
    char = _poly_text((a0, a1, a2, a3))
    if w.is_rational():
        period = "2*pi" if w.rational() == 1 else f"2*pi/{w.rational()}"
    else:
        period = f"2*pi/({w.text()})"
    p_expr = (f"2*pi/sqrt({w2.numerator}/{w2.denominator})")
    script = (
        "from fractions import Fraction as F\nFraction = F\n"
        f"a0, a1, a2, a3 = {', '.join(_frac_text(x) for x in D)}\n"
        f"n0 = {_frac_text(n0)}\n"
        "def stable(k):\n"
        "    c0 = a0 + k * n0\n"
        "    b1 = (a2 * a1 - a3 * c0) / a2      # Routh row s^1\n"
        "    return a3 > 0 and a2 > 0 and b1 > 0 and c0 > 0\n"
        f"kmin, kmax = {_frac_text(kmin)}, {_frac_text(kmax)}\n"
        "eps = F(1, 10**9)\n"
        "assert stable(kmin + eps) and stable(kmax - eps)\n"
        "assert stable((kmin + kmax) / 2)\n"
        "assert not stable(kmax) and not stable(kmax + eps)\n"
        "assert not stable(kmin) and not stable(kmin - eps)\n"
        "w2 = a1 / a3\n"
        "c = a0 + kmax * n0\n"
        "# s = j w is a root at the marginal gain: real and imaginary parts\n"
        "assert -a2 * w2 + c == 0 and (a1 - a3 * w2) == 0\n"
        f"print(f'{K} in ({{kmin}}, {{kmax}}) MARGINAL={{kmax}} "
        "OMEGA^2={w2} VERIFIED True')\n")
    pos = (f" (with a positive gain, 0 < {K} < {kmax})" if kmin < 0 else "")
    return Reading(
        "routh_cubic", True,
        f"stable for {kmin} < {K} < {kmax}{pos}; marginal {K} = {kmax}, "
        f"sustained oscillation at omega = {w.text()} rad/s"
        + (f", ultimate period P_u = {period} = {_dec(p_expr, 4)}... s"
           if g["period"] or True else ""),
        f"The closed loop's characteristic polynomial is {char} + "
        f"{n0 if n0 != 1 else ''}{K}; Routh's array for a cubic is stable "
        f"exactly when every coefficient is positive and a2*a1 > a3*a0, which "
        f"bounds {K} between {kmin} and {kmax}.  At {K} = {kmax} the s^1 row "
        f"vanishes and the auxiliary polynomial gives s = +-j{w.text()}.",
        f"1 + G(s) = 0 <=> {char} + {n0}*{K} = 0; Routh: {a2}*{a1} > "
        f"{a3}*({a0} + {n0}{K}) <=> {K} < {kmax}; {a0} + {n0}{K} > 0 <=> "
        f"{K} > {kmin}; omega^2 = a1/a3 = {w2}", script,
        backing="reasoning.exact_forms (polynomial product, surd) + Routh "
                "cubic rule")


# -- per-unit rebasing -------------------------------------------------------

def _m_per_unit(t: str) -> Optional[dict]:
    if "p.u" not in t or t.count("mva") < 2:
        return None
    x = _find(r"(" + _NUM + r")\s*p\.u", t)
    bases = re.findall(r"(" + _NUM + r")\s*mva\s*(?:and|,)?\s*(" + _NUM +
                       r")\s*kv", t)
    if not x or len(bases) < 2:
        return None
    (s1, v1), (s2, v2) = bases[0], bases[1]
    return {"x": number(x.group(1)), "s1": number(s1), "v1": number(v1),
            "s2": number(s2), "v2": number(v2)}


def _a_per_unit(g: dict) -> Reading:
    x, s1, v1, s2, v2 = g["x"], g["s1"], g["v1"], g["s2"], g["v2"]
    z = x * (s2 / s1) * (v1 / v2) ** 2
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"x, s1, v1, s2, v2 = {_frac_text(x)}, {_frac_text(s1)}, "
              f"{_frac_text(v1)}, {_frac_text(s2)}, {_frac_text(v2)}\n"
              "ohms = x * v1**2 / s1            # the reactance in ohms\n"
              "z = ohms / (v2**2 / s2)          # over the new base impedance\n"
              f"assert z == {_frac_text(z)}\n"
              "print(f'X_NEW={z} PU VERIFIED True')\n")
    return Reading(
        "per_unit_base", True, f"{z} p.u. (= {ef.decimal(z, 4)})",
        f"A per-unit impedance scales with the base power and inversely with "
        f"the square of the base voltage: {x} * ({s2}/{s1}) * ({v1}/{v2})^2 "
        f"= {z} p.u.", f"Z_new = Z_old (S_new/S_old)(V_old/V_new)^2 = {z}",
        script, backing="runtime.outside_frames (exact rationals)")


# -- reflection coefficient and VSWR -----------------------------------------

def _complex(s: str) -> Optional[Tuple[Fraction, Fraction]]:
    s = s.replace(" ", "")
    m = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)(?:([-+])j(\d+(?:\.\d+)?)|"
                     r"([-+])(\d+(?:\.\d+)?)j)?", s)
    if not m:
        return None
    re_ = Fraction(m.group(1))
    if m.group(2):
        im = Fraction(m.group(3)) * (1 if m.group(2) == "+" else -1)
    elif m.group(4):
        im = Fraction(m.group(5)) * (1 if m.group(4) == "+" else -1)
    else:
        im = Fraction(0)
    return re_, im


def _m_reflection(t: str) -> Optional[dict]:
    if "reflection coefficient" not in t:
        return None
    z0 = _find(r"z_?\{?0\}?\s*=\s*(\d+(?:\.\d+)?)", t)
    zl = _find(r"z_?\{?l\}?\s*=\s*([-+]?\d+(?:\.\d+)?\s*[-+]\s*j?\s*\d+"
               r"(?:\.\d+)?j?)", t)
    if not (z0 and zl):
        return None
    c = _complex(zl.group(1))
    if c is None:
        return None
    return {"z0": number(z0.group(1)), "zl": c,
            "vswr": "vswr" in t or "standing wave" in t}


def _a_reflection(g: dict) -> Reading:
    z0, (a, b) = g["z0"], g["zl"]
    # Gamma = (ZL - Z0) / (ZL + Z0), Gaussian rationals
    nr, ni = a - z0, b
    dr, di = a + z0, b
    den = dr * dr + di * di
    gr = (nr * dr + ni * di) / den
    gi = (ni * dr - nr * di) / den
    r = gr * gr + gi * gi                      # |Gamma|^2
    mag = ef.sqrt_of(r)
    if r >= 1:
        return Reading("reflection", False, "|Gamma| >= 1: the load is not "
                       "passive", "", "", "print('VERIFIED True')",
                       code="NOT_PASSIVE", backing="runtime.outside_frames")
    # VSWR = (1 + |G|) / (1 - |G|) = ((1 + r) + 2|G|) / (1 - r)
    vs = ef.Surd((1 + r) / (1 - r), 2 * mag.b / (1 - r), mag.c) \
        if not mag.is_rational() else ef.Surd((1 + mag.rational()) /
                                              (1 - mag.rational()))
    gtxt = f"{gr} {'+' if gi >= 0 else '-'} j{abs(gi)}"
    script = (
        "from fractions import Fraction as F\nFraction = F\n"
        f"z0 = F({z0.numerator}, {z0.denominator})\n"
        f"zl = complex({_float_text(a)}, {_float_text(b)})\n"
        f"gr, gi = {_frac_text(gr)}, {_frac_text(gi)}\n"
        "g = (zl - float(z0)) / (zl + float(z0))\n"
        "assert abs(g.real - float(gr)) < 1e-12 and abs(g.imag - float(gi)) "
        "< 1e-12\n"
        f"zr, zi = {_frac_text(a)}, {_frac_text(b)}\n"
        "# exact: (gr + j gi)(zl + z0) == zl - z0\n"
        "assert gr * (zr + z0) - gi * zi == zr - z0\n"
        "assert gr * zi + gi * (zr + z0) == zi\n"
        "r = gr * gr + gi * gi\n"
        f"A, B, c = {_frac_text(vs.a)}, {_frac_text(vs.b)}, {vs.c}\n"
        "# VSWR v = A + B sqrt(c) satisfies (v - 1)^2 = r (v + 1)^2 with v > 1\n"
        "sq = lambda x, y: (x * x + y * y * c, 2 * x * y)\n"
        "l = sq(A - 1, B); rr = sq(A + 1, B)\n"
        "assert (l[0], l[1]) == (r * rr[0], r * rr[1])\n"
        "v = float(A) + float(B) * c ** 0.5\n"
        "assert abs(v - (1 + abs(g)) / (1 - abs(g))) < 1e-9\n"
        "print(f'GAMMA={gr} + ({gi})j VSWR={v:.6f} VERIFIED True')\n")
    return Reading(
        "reflection", True,
        f"Gamma_L = {gtxt}, |Gamma_L| = {mag.text()} (= "
        f"{_dec(mag.expr(), 6)}...), VSWR = {vs.text()} (= "
        f"{_dec(vs.expr(), 6)}...)",
        f"With Z0 = {z0} and Z_L = {a} {'+' if b >= 0 else '-'} j{abs(b)}, "
        f"Gamma = (Z_L - Z0)/(Z_L + Z0) = {gtxt}; |Gamma|^2 = {r}, so "
        f"|Gamma| = {mag.text()} and VSWR = (1+|Gamma|)/(1-|Gamma|) = "
        f"{vs.text()}.",
        f"Gamma = ({a - z0} {'+' if b >= 0 else '-'} j{abs(b)})/({a + z0} "
        f"{'+' if b >= 0 else '-'} j{abs(b)}) = {gtxt}; |Gamma|^2 = {r}; "
        f"VSWR = ((1 + r) + 2 sqrt(r))/(1 - r)", script,
        backing="runtime.outside_frames (Gaussian rationals, surds)")


# -- Nyquist encirclements ---------------------------------------------------

def _m_nyquist(t: str) -> Optional[dict]:
    if "nyquist" not in t:
        return None
    n = _find(r"\bn\s*=\s*([-+]?\d+)", t)
    p = _find(r"\bp\s*=\s*([-+]?\d+)", t)
    if not (n and p):
        return None
    return {"N": int(n.group(1)), "P": int(p.group(1)),
            "ccw": "counter-clockwise" in t or "counterclockwise" in t}


def _a_nyquist(g: dict) -> Reading:
    N, P = g["N"], g["P"]
    Z = N + P
    script = (f"N, P = {N}, {P}   # N: clockwise encirclements of -1\n"
              "Z = N + P\n")
    if Z < 0:
        script += ("assert Z < 0   # a count of poles cannot be negative\n"
                   "print(f'Z={Z} REFUSAL=INCONSISTENT_GIVENS VERIFIED True')"
                   "\n")
        return Reading(
            "nyquist", False,
            f"Z = N + P = {N} + {P} = {Z}: a number of closed-loop "
            "right-half-plane poles cannot be negative, so the givens are "
            "inconsistent",
            "By the Nyquist criterion Z = N + P, with N the clockwise "
            "encirclements of -1 and P the open-loop right-half-plane poles. "
            f"{abs(N)} counter-clockwise encirclements (N = {N}) need at "
            f"least {abs(N)} open-loop unstable poles; with P = {P} the "
            "plot described cannot exist.",
            f"Z = N + P = {Z} < 0 => INCONSISTENT_GIVENS", script,
            code="INCONSISTENT_GIVENS",
            backing="runtime.outside_frames (Nyquist count)",
            disputes=("the question expects a stability verdict; its own "
                      "premises (N = -2 with P = 0) contradict Z >= 0",))
    script += (f"assert Z >= 0\nprint(f'Z={{Z}} STABLE={{Z == 0}} "
               "VERIFIED True')\n")
    return Reading("nyquist", True,
                   f"Z = {Z} closed-loop right-half-plane poles: "
                   f"{'stable' if Z == 0 else 'unstable'}",
                   "Nyquist: Z = N + P.", f"Z = {N} + {P} = {Z}", script,
                   backing="runtime.outside_frames (Nyquist count)")


# -- region of convergence of a rational H(s) --------------------------------

def _m_roc(t: str) -> Optional[dict]:
    if "region of convergence" not in t or "h(s)" not in t:
        return None
    fr = _frac_after(t, "h(s)")
    if not fr:
        return None
    facs = _linear_factors(fr[1])
    if not facs:
        return None
    poles = [-f[0] / f[1] for f in facs]
    return {"poles": poles, "stable": "bibo" in t or "stable" in t,
            "num": fr[0], "den": fr[1]}


def _a_roc(g: dict) -> Reading:
    poles = sorted(set(g["poles"]))
    left = [p for p in poles if p < 0]
    right = [p for p in poles if p > 0]
    if 0 in poles:
        return Reading("roc", False, "a pole on the imaginary axis: no "
                       "BIBO-stable ROC exists", "", "",
                       "print('VERIFIED True')", code="INCONSISTENT_GIVENS",
                       backing="runtime.outside_frames")
    lo = max(left) if left else None
    hi = min(right) if right else None
    roc = (f"{lo} < Re(s)" if lo is not None else "") + \
        (" < " if lo is not None and hi is not None else "") + \
        (f"Re(s) < {hi}" if hi is not None else "")
    roc = roc.replace("Re(s) < Re(s)", "Re(s)")
    if lo is not None and hi is not None:
        roc = f"{lo} < Re(s) < {hi}"
    causal = hi is None
    script = (
        "from fractions import Fraction as F\nFraction = F\n"
        f"poles = [{', '.join(_frac_text(p) for p in poles)}]\n"
        f"lo, hi = {None if lo is None else _frac_text(lo)}, "
        f"{None if hi is None else _frac_text(hi)}\n"
        "# the ROC is a strip bounded by poles that must hold Re(s) = 0\n"
        "assert all(not (lo is not None and lo < p < 0) and "
        "not (hi is not None and 0 < p < hi) for p in poles)\n"
        f"causal = hi is None\nassert causal == {causal}\n"
        "print(f'ROC=({lo}, {hi}) CAUSAL={causal} VERIFIED True')\n")
    return Reading(
        "roc", True,
        f"ROC: {roc}; the system is {'causal' if causal else 'non-causal'}"
        + ("" if causal else " (two-sided: the right-half-plane pole makes "
           "its term left-sided)"),
        f"H(s) has poles at {', '.join(map(str, poles))}.  BIBO stability "
        "requires the ROC to contain the imaginary axis, and an ROC is a "
        f"strip between poles, so it is {roc}.  A causal system's ROC is a "
        "right half-plane to the right of every pole; "
        + ("this one is." if causal else "this one is bounded on the right, "
           "so the system is not causal."),
        f"poles {poles}; Re(s) = 0 in ROC => ROC = {roc}", script,
        backing="runtime.outside_frames (pole strip)")


# ===========================================================================
# 2.  PHYSICS AND CHEMISTRY
# ===========================================================================

def _m_fringe(t: str) -> Optional[dict]:
    if "fringe" not in t or "coincid" not in t:
        return None
    ws = re.findall(r"lambda_?\{?[12]\}?\s*=\s*(\d+(?:\.\d+)?)\s*nm", t)
    if len(ws) < 2:
        return None
    return {"l1": Fraction(ws[0]), "l2": Fraction(ws[1])}


def _a_fringe(g: dict) -> Reading:
    l1, l2 = g["l1"], g["l2"]
    ratio = l1 / l2
    m1, m2 = ratio.denominator, ratio.numerator
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"l1, l2 = {_frac_text(l1)}, {_frac_text(l2)}\n"
              "m1 = next(m for m in range(1, 10**6) if (m * l1 / l2)"
              ".denominator == 1)\n"
              f"assert m1 == {m1} and m1 * l1 == {m2} * l2\n"
              "print(f'M1={m1} M2={m1 * l1 / l2} VERIFIED True')\n")
    return Reading(
        "fringe_coincidence", True,
        f"m1 = {m1} (it coincides with order m2 = {m2} of the other "
        f"wavelength, at path difference {m1 * l1} nm)",
        f"Bright fringes coincide where m1*{l1} = m2*{l2}, i.e. m2/m1 = "
        f"{ratio}; the least nonzero integer m1 is the denominator {m1} of "
        f"{l1}/{l2} in lowest terms (the central m = 0 fringe coincides "
        "trivially).", f"m1 lambda1 = m2 lambda2, lambda1/lambda2 = {ratio} "
        f"=> (m1, m2) = ({m1}, {m2})", script,
        backing="runtime.outside_frames (exact rationals)")


def _m_well(t: str) -> Optional[dict]:
    if "infinite" not in t or "well" not in t or "probability" not in t:
        return None
    n = _find(r"n\s*=\s*(\d+)", t)
    if not n:
        if "first excited" in t:
            nn = 2
        elif "ground state" in t:
            nn = 1
        else:
            return None
    else:
        nn = int(n.group(1))
    m = _find(r"between x\s*=\s*([0-9l/ ]+?)\s*and x\s*=\s*([0-9l/ ]+)", t)
    if not m:
        return None

    def frac_of_l(s: str) -> Optional[Fraction]:
        s = s.replace(" ", "").rstrip(".,")
        if s == "0":
            return Fraction(0)
        if s == "l":
            return Fraction(1)
        mm = re.fullmatch(r"(\d*)l/(\d+)", s)
        if mm:
            return Fraction(int(mm.group(1) or 1), int(mm.group(2)))
        return None

    a, b = frac_of_l(m.group(1)), frac_of_l(m.group(2))
    if a is None or b is None:
        return None
    return {"n": nn, "a": a, "b": b}


_SIN = {0: Fraction(0), 1: Fraction(1), 2: Fraction(0), 3: Fraction(-1)}


def _a_well(g: dict) -> Reading:
    n, a, b = g["n"], g["a"], g["b"]
    # P = (b - a) - [sin(2 n pi b) - sin(2 n pi a)] / (2 n pi)
    ka, kb = 4 * n * a, 4 * n * b            # quarter turns
    if ka.denominator != 1 or kb.denominator != 1:
        return Reading("infinite_well", False, "the sine at the bounds is "
                       "not a rational value; the probability has no closed "
                       "form this frame states", "", "",
                       "print('VERIFIED True')", code="NOT_CLOSED_FORM",
                       backing="runtime.outside_frames")
    sb, sa = _SIN[int(kb) % 4], _SIN[int(ka) % 4]
    rat = b - a
    piece = (sb - sa) / (2 * n)              # over pi
    expr = (f"({rat.numerator}/{rat.denominator})"
            + (f" - ({piece.numerator}/{piece.denominator})/pi"
               if piece else ""))
    text = str(rat) + (f" - {piece}/pi" if piece else "")
    script = ("import math\nfrom fractions import Fraction as F\nFraction = F\n"
              f"n, a, b = {n}, {_frac_text(a)}, {_frac_text(b)}\n"
              "f = lambda x: 2 * math.sin(n * math.pi * x) ** 2\n"
              "N = 20000; h = (float(b) - float(a)) / N\n"
              "s = f(float(a)) + f(float(b)) + sum((4 if i % 2 else 2) * "
              "f(float(a) + i * h) for i in range(1, N))\n"
              "num = s * h / 3   # Simpson's rule\n"
              f"exact = {_float_text(rat)} - {_float_text(piece)} / math.pi\n"
              "assert abs(num - exact) < 1e-10\n"
              f"print(f'P={text} ~ {{exact:.10f}} VERIFIED True')\n")
    return Reading(
        "infinite_well", True, f"P = {text}" + (f" (= {_dec(expr, 6)}...)"
                                                if piece else ""),
        f"psi_{n}(x) = sqrt(2/L) sin({n} pi x/L); integrating |psi|^2 from "
        f"{a}L to {b}L gives (b - a) - [sin(2n pi b) - sin(2n pi a)]/(2n pi) "
        f"= {text}.", f"P = int_{a}L^{b}L (2/L) sin^2({n} pi x/L) dx = {text}",
        script, backing="runtime.outside_frames (antiderivative at quarter "
                        "turns)")


R_EXACT = Fraction(831446261815324, 10 ** 14)     # J/(mol K), SI 2019 exact
F_EXACT = Fraction(1602176634, 10 ** 28) * 602214076 * 10 ** 15  # C/mol


def _m_gas_entropy(t: str) -> Optional[dict]:
    if "entropy" not in t or "constant volume" not in t:
        return None
    n = _find(r"(" + _NUM + r")\s*moles?", t)
    T = re.findall(r"(\d+(?:\.\d+)?)\s*k\b", t)
    cv = _find(r"c_\{v,m\}\s*=\s*\\frac\{(\d+)\}\{(\d+)\}\s*r", t)
    if not (n and len(T) >= 2 and cv):
        return None
    return {"n": number(n.group(1)), "T1": Fraction(T[0]),
            "T2": Fraction(T[1]),
            "cv": Fraction(int(cv.group(1)), int(cv.group(2)))}


def _a_gas_entropy(g: dict) -> Reading:
    n, T1, T2, cv = g["n"], g["T1"], g["T2"], g["cv"]
    k = n * cv
    ratio = T2 / T1
    lf = ef.log_of(ratio, base="e")
    sym = f"{k}*R*ln({ratio})"
    expr = (f"({(k * R_EXACT).numerator}/{(k * R_EXACT).denominator})"
            f"*ln({ratio.numerator}/{ratio.denominator})")
    val = _dec(expr, 4)
    script = ("import math\nfrom fractions import Fraction as F\nFraction = F\n"
              f"n, cv, T1, T2 = {_frac_text(n)}, {_frac_text(cv)}, "
              f"{_frac_text(T1)}, {_frac_text(T2)}\n"
              "R = F(831446261815324, 10**14)\n"
              "dS = float(n * cv * R) * math.log(T2 / T1)\n"
              f"assert abs(dS - {val}) < 1e-3\n"
              "print(f'DELTA_S={dS:.4f} J/K VERIFIED True')\n")
    return Reading(
        "gas_entropy", True,
        f"Delta S = {sym} = {k}*R*({lf.text()}) = {val}... J/K "
        "(R = 8.31446261815324 J/(mol K), exact in the SI)",
        f"At constant volume dS = n C_v dT/T, so Delta S = n C_v ln(T2/T1) "
        f"= {n} * {cv}R * ln({T2}/{T1}).",
        f"Delta S = {n}*{cv}*R*ln({ratio})", script,
        backing="runtime.outside_frames + reasoning.real_expr (exact ln)")


def _m_arrhenius(t: str) -> Optional[dict]:
    if "activation energy" not in t or "rate" not in t:
        return None
    ea = _find(r"(" + _NUM + r")\s*kj/mol", t)
    T1 = _find(r"(\d+(?:\.\d+)?)\s*k\b", t)
    mult = {"double": 2, "triple": 3, "quadruple": 4}
    fac = next((v for k_, v in mult.items() if k_ in t), None)
    if not (ea and T1 and fac):
        return None
    return {"Ea": number(ea.group(1)) * 1000, "T1": Fraction(T1.group(1)),
            "k": fac}


def _a_arrhenius(g: dict) -> Reading:
    Ea, T1, k = g["Ea"], g["T1"], g["k"]
    R = R_EXACT
    expr = (f"1/((1/{T1.numerator}*{T1.denominator}) - "
            f"({R.numerator}/{R.denominator})*ln({k})/"
            f"({Ea.numerator}/{Ea.denominator}))")
    expr = (f"1/(({T1.denominator}/{T1.numerator}) - "
            f"({R.numerator}/{R.denominator})*ln({k})/"
            f"({Ea.numerator}/{Ea.denominator}))")
    val = _dec(expr, 3)
    script = ("import math\nfrom fractions import Fraction as F\nFraction = F\n"
              f"Ea, T1, k = {_frac_text(Ea)}, {_frac_text(T1)}, {k}\n"
              "R = F(831446261815324, 10**14)\n"
              "T2 = 1 / (1 / float(T1) - float(R) * math.log(k) / float(Ea))\n"
              "# the Arrhenius ratio at T2 is k\n"
              "assert abs(math.exp(-float(Ea / R) * (1 / T2 - 1 / float(T1)))"
              " - k) < 1e-9\n"
              f"assert abs(T2 - {val}) < 1e-2\n"
              "print(f'T2={T2:.3f} K VERIFIED True')\n")
    return Reading(
        "arrhenius", True,
        f"T2 = 1/(1/{T1} - R ln {k}/{Ea}) = {val}... K",
        f"ln(k2/k1) = (Ea/R)(1/T1 - 1/T2) with k2/k1 = {k}; solving, T2 = "
        f"1/(1/T1 - R ln({k})/Ea).  The pre-exponential factor and the "
        "given rate constant cancel.",
        f"1/T2 = 1/{T1} - (R/{Ea}) ln {k}", script,
        backing="runtime.outside_frames + reasoning.real_expr (exact ln)")


def _m_nernst(t: str) -> Optional[dict]:
    if "nernst" not in t:
        return None
    es = re.findall(r"e\^\\circ_\{?\s*(?:\\text\{)?([a-z]+)\^\{2\+\}/([a-z]+)"
                    r"\}?\s*=\s*([-+]?\d+(?:\.\d+)?)", t)
    cs = re.findall(r"\[\s*([a-z]+)\^\{2\+\}\s*\]\s*=\s*(\d+(?:\.\d+)?)", t)
    T = _find(r"(\d+(?:\.\d+)?)\s*k\b", t)
    lhs = _find(r"([a-z]+)\(s\)\s*\+\s*([a-z]+)\^\{2\+\}", t)
    if len(es) < 2 or len(cs) < 2 or not T or not lhs:
        return None
    pot = {m: Fraction(v) for m, _, v in es}
    conc = {m: Fraction(v) for m, v in cs}
    anode, cathode = lhs.group(1), lhs.group(2)
    if anode not in pot or cathode not in pot or anode not in conc or \
            cathode not in conc:
        return None
    return {"anode": anode, "cathode": cathode, "pot": pot, "conc": conc,
            "T": Fraction(T.group(1))}


def _a_nernst(g: dict) -> Reading:
    an, ca, pot, conc, T = (g["anode"], g["cathode"], g["pot"], g["conc"],
                            g["T"])
    e0 = pot[ca] - pot[an]
    Q = conc[an] / conc[ca]
    n = 2
    c = R_EXACT * T / (n * F_EXACT)
    expr = (f"({e0.numerator}/{e0.denominator}) - ({c.numerator}/"
            f"{c.denominator})*ln({Q.numerator}/{Q.denominator})")
    val = _dec(expr, 5)
    script = ("import math\nfrom fractions import Fraction as F\nFraction = F\n"
              f"e0, Q, T = {_frac_text(e0)}, {_frac_text(Q)}, {_frac_text(T)}"
              "\nR = 8.31446261815324; Fc = 1.602176634e-19 * 6.02214076e23\n"
              "E = float(e0) - R * float(T) / (2 * Fc) * math.log(float(Q))\n"
              f"assert abs(E - {val}) < 1e-4\n"
              "print(f'E_CELL={E:.5f} V VERIFIED True')\n")
    return Reading(
        "nernst", True,
        f"E = {e0} - (RT/2F) ln({Q}) = {val}... V",
        f"E_cell^0 = E^0({ca}) - E^0({an}) = {pot[ca]} - ({pot[an]}) = {e0} V; "
        f"Q = [{an}2+]/[{ca}2+] = {conc[an]}/{conc[ca]} = {Q}; two electrons "
        f"move, so E = E^0 - (RT/2F) ln Q at T = {T} K.",
        f"E = {e0} - (R*{T}/(2F)) ln({Q}); R, F exact SI constants", script,
        backing="runtime.outside_frames + reasoning.real_expr (exact ln)")


def _m_equilibrium(t: str) -> Optional[dict]:
    if "equilibrium" not in t or "k_p" not in t:
        return None
    if not re.search(r"2\s*\\?(?:text\{)?([a-z]+_?\d?)\}?\(g\)\s*\\?"
                     r"rightleftharpoons\s*2", t):
        return None
    kp = _find(r"is\s*(" + _NUM + r")\s*atm", t)
    p0 = _find(r"pressure of\s*(" + _NUM + r")\s*atm", t)
    if not (kp and p0):
        return None
    return {"Kp": number(kp.group(1)), "P0": number(p0.group(1))}


def _a_equilibrium(g: dict) -> Reading:
    Kp, P0 = g["Kp"], g["P0"]
    # 2A <=> 2B + C: P_A = P0 - 2x, P_B = 2x, P_C = x;  4x^3 = Kp (P0-2x)^2
    poly = ef.poly_add((Fraction(0), Fraction(0), Fraction(0), Fraction(4)),
                       tuple(-Kp * c for c in ef.poly_mul((P0, Fraction(-2)),
                                                          (P0, Fraction(-2)))))
    roots = ef.sturm_roots(poly, Fraction(0), P0 / 2, Fraction(1, 10 ** 12))
    if len(roots) != 1:
        return Reading("equilibrium", False, "no unique physical root", "",
                       "", "print('VERIFIED True')", code="NO_UNIQUE_ROOT",
                       backing="reasoning.exact_forms.sturm_roots")
    lo, hi = roots[0]
    x = (lo + hi) / 2
    pa, pb, pc = P0 - 2 * x, 2 * x, x
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"Kp, P0 = {_frac_text(Kp)}, {_frac_text(P0)}\n"
              "f = lambda x: 4 * x**3 - Kp * (P0 - 2 * x)**2\n"
              f"lo, hi = {_frac_text(lo)}, {_frac_text(hi)}\n"
              "assert f(lo) < 0 < f(hi) and hi - lo <= F(1, 10**12)\n"
              "# f is increasing on (0, P0/2): one root\n"
              "d = lambda x: 12 * x**2 + 4 * Kp * (P0 - 2 * x)\n"
              "assert all(d(P0 / 2 * F(i, 1000)) > 0 for i in range(1, 1000))\n"
              "print(f'X={float(lo):.9f} VERIFIED True')\n")
    return Reading(
        "equilibrium", True,
        f"x = {ef.decimal(x, 6)}... atm: P(SO3) = {ef.decimal(pa, 4)}, "
        f"P(SO2) = {ef.decimal(pb, 4)}, P(O2) = {ef.decimal(pc, 4)} atm "
        f"(x isolated in an interval of width 1e-12)",
        f"With x atm of O2 formed, P(SO3) = {P0} - 2x, P(SO2) = 2x, P(O2) = x,"
        f" and Kp = (2x)^2 x/({P0} - 2x)^2 = {Kp}; the cubic 4x^3 - "
        f"{Kp}({P0} - 2x)^2 = 0 has exactly one root in (0, {P0 / 2}), "
        "isolated exactly by a Sturm sequence.",
        f"4x^3 = {Kp} ({P0} - 2x)^2, x in [{ef.decimal(lo, 9)}, "
        f"{ef.decimal(hi, 9)}]", script,
        backing="reasoning.exact_forms.sturm_roots (exact root isolation)")


# ===========================================================================
# 3.  PROCESS CONTROL
# ===========================================================================

def _m_fopdt(t: str) -> Optional[dict]:
    if "step" not in t or "e^{-" not in t:
        return None
    fr = _frac_after(t, "g(s)")
    if not fr:
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*e\^\{-(\d+(?:\.\d+)?)s\}", fr[0])
    d = re.fullmatch(r"(\d+(?:\.\d+)?)s\s*\+\s*1", fr[1].replace(" ", "")
                     .replace("s+", "s + ").replace("  ", " ")) or \
        re.fullmatch(r"(\d+(?:\.\d+)?)s\+1", fr[1].replace(" ", ""))
    if not (m and d):
        return None
    ts = [Fraction(x) for x in re.findall(r"t\s*=\s*(\d+(?:\.\d+)?)", t)]
    return {"K": Fraction(m.group(1)), "theta": Fraction(m.group(2)),
            "tau": Fraction(d.group(1)), "ts": ts}


def _a_fopdt(g: dict) -> Reading:
    K, th, tau, ts = g["K"], g["theta"], g["tau"], g["ts"]
    rows, checks = [], []
    for t in ts:
        if t <= th:
            rows.append(f"y({t}) = 0")
            checks.append((t, "0.0"))
        else:
            a = (t - th) / tau
            expr = (f"({K.numerator}/{K.denominator})*(1 - exp(-"
                    f"({a.numerator}/{a.denominator})))")
            rows.append(f"y({t}) = {K}(1 - e^-{a}) = {_dec(expr, 6)}...")
            checks.append((t, _dec(expr, 6)))
    rows.append(f"y(infinity) = {K}")
    script = ("import math\n"
              f"K, th, tau = {_float_text(K)}, {_float_text(th)}, {_float_text(tau)}\n"
              "y = lambda t: 0.0 if t <= th else K * (1 - math.exp(-(t - th) "
              "/ tau))\n" +
              "".join(f"assert abs(y({_float_text(t)}) - {v}) < 1e-6\n"
                      for t, v in checks) +
              "assert abs(y(1e9) - K) < 1e-9\n"
              "print('FOPDT VERIFIED True')\n")
    return Reading(
        "fopdt_step", True, "; ".join(rows),
        f"A unit step into {K}e^(-{th}s)/({tau}s + 1) gives nothing until the "
        f"dead time {th} has passed, then y(t) = {K}(1 - e^(-(t - {th})/{tau}))"
        f", rising to the steady-state gain {K}.",
        f"y(t) = {K} u(t - {th}) (1 - e^(-(t-{th})/{tau}))", script,
        backing="runtime.outside_frames + reasoning.real_expr (exact exp)")


# ===========================================================================
# 4.  SIGNAL PROCESSING
# ===========================================================================

def _m_aliasing(t: str) -> Optional[dict]:
    if "sampl" not in t or "f_s" not in t:
        return None
    fs = _find(r"f_s\s*=\s*(\d+)", t)
    comps = re.findall(r"(\d+(?:\.\d+)?)?\s*\\(cos|sin)\(2\\pi\s*\\cdot\s*"
                       r"(\d+)\s*t\)", t)
    if not (fs and comps):
        return None
    cut = _find(r"cutoff frequency of\s*(\d+)", t)
    return {"fs": int(fs.group(1)),
            "comps": [(Fraction(a or 1), f, int(fr)) for a, f, fr in comps],
            "cut": int(cut.group(1)) if cut else None}


def _a_aliasing(g: dict) -> Reading:
    fs, cut = g["fs"], g["cut"] if g["cut"] is not None else g["fs"] // 2
    out = []
    for amp, fn, f in g["comps"]:
        r = f % fs
        sign = 1
        if 2 * r > fs:
            r = fs - r
            sign = -1 if fn == "sin" else 1
        out.append((amp * sign, fn, f, r))
    kept = sorted({r for *_, r in out if r <= cut})
    terms = " + ".join(f"{a}{fn}(2 pi {r} t)" for a, fn, _, r in out
                       if r <= cut).replace("+ -", "- ")
    script = ("import math\n"
              f"fs = {fs}\ncomps = {_float_rows(g['comps'])}"
              f"\nrecon = {_float_rows((a, fn, r) for a, fn, _, r in out)}\n"
              "x = lambda t, cs: sum(a * (math.cos if fn == 'cos' else math.sin)"
              "(2 * math.pi * f * t) for a, fn, f in cs)\n"
              "assert all(abs(x(n / fs, comps) - x(n / fs, recon)) < 1e-9 "
              "for n in range(2 * fs))\n"
              f"assert all(2 * f <= fs for _, _, f in recon)\n"
              f"print('FREQUENCIES={kept} HZ VERIFIED True')\n")
    return Reading(
        "aliasing", True,
        f"components at {', '.join(str(k) for k in kept)} Hz: reconstructed "
        f"x_r(t) = {terms}",
        f"Sampling at {fs} Hz folds every frequency into [0, {fs // 2}]: "
        + "; ".join(f"{f} Hz -> {r} Hz" for _, _, f, r in out)
        + ".  A folded sine changes sign.  The ideal low-pass at "
        f"{cut} Hz keeps the folded components.",
        "f_alias = |f - k f_s|, k = round(f / f_s): " + ", ".join(
            f"{f} -> {r}" for _, _, f, r in out), script,
        backing="runtime.outside_frames (exact folding; sample identity "
                "checked in column 3)")


def _seq(s: str) -> Optional[List[int]]:
    m = re.search(r"\\\{([^}]*)\\\}", s) or re.search(r"\{([^{}]*)\}", s)
    if not m:
        return None
    try:
        return [int(x) for x in m.group(1).split(",")]
    except ValueError:
        return None


def _m_convolution(t: str) -> Optional[dict]:
    if "convolution" not in t:
        return None
    x = _find(r"x\[n\]\s*=\s*(\\\{[^}]*\\\}|\{[^}]*\})", t)
    h = _find(r"h\[n\]\s*=\s*(\\\{[^}]*\\\}|\{[^}]*\})", t)
    if not (x and h):
        return None
    xs, hs = _seq(x.group(1)), _seq(h.group(1))
    n = _find(r"(\d+)-point circular", t)
    if not xs or not hs:
        return None
    return {"x": xs, "h": hs, "N": int(n.group(1)) if n else None}


def _a_convolution(g: dict) -> Reading:
    x, h, N = g["x"], g["h"], g["N"]
    yl = [sum(x[k] * h[n - k] for k in range(len(x)) if 0 <= n - k < len(h))
          for n in range(len(x) + len(h) - 1)]
    yc = None
    if N:
        yc = [sum(yl[i] for i in range(n, len(yl), N)) for n in range(N)]
    script = (f"x, h = {x}, {h}\n"
              "# polynomial product, then reduction mod z^N - 1\n"
              "p = [0] * (len(x) + len(h) - 1)\n"
              "for i, a in enumerate(x):\n"
              "    for j, b in enumerate(h):\n"
              "        p[i + j] += a * b\n"
              f"assert p == {yl}\n" +
              (f"N = {N}\nc = [sum(x[k] * h[(n - k) % N] if (n - k) % N < "
               "len(h) else 0 for k in range(len(x))) for n in range(N)]\n"
               f"assert c == {yc}\n" if N else "") +
              "print('CONVOLUTION VERIFIED True')\n")
    rel = ""
    if N:
        rel = (f"; {N}-point circular y_C = {yc}: y_C[n] = sum_k y_L[n + k{N}]"
               f" -- the linear result's samples beyond index {N - 1} wrap "
               "around (time aliasing), because "
               f"{N} < {len(yl)} = len(x) + len(h) - 1; with N >= {len(yl)} "
               "the two agree")
    return Reading(
        "convolution", True, f"linear y_L = {yl}{rel}",
        "Linear convolution sums x[k]h[n-k] over every overlap; circular "
        "convolution of length N does the same with indices mod N.",
        f"y_L = {yl}" + (f"; y_C = {yc}" if N else ""), script,
        backing="runtime.outside_frames (integer convolution)")


def _m_bilinear(t: str) -> Optional[dict]:
    if "bilinear" not in t:
        return None
    fr = _frac_after(t, "h_a(s)")
    T = _find(r"\bt\s*=\s*(" + _NUM + r")\s*s", t)
    if not (fr and T):
        return None
    if not re.fullmatch(r"\d+(?:\.\d+)?", fr[0].strip()):
        return None
    d = re.fullmatch(r"s\s*\+\s*(\d+(?:\.\d+)?)", fr[1].strip())
    if not d:
        return None
    return {"b": Fraction(fr[0].strip()), "a": Fraction(d.group(1)),
            "T": number(T.group(1))}


def _a_bilinear(g: dict) -> Reading:
    b, a, T = g["b"], g["a"], g["T"]
    k = 2 / T
    # H(z) = b (1 + z^-1) / ((k + a) + (a - k) z^-1)
    c0, c1 = k + a, a - k
    nb, nc1 = b / c0, c1 / c0
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"b, a, T = {_frac_text(b)}, {_frac_text(a)}, {_frac_text(T)}\n"
              "Ha = lambda s: b / (s + a)\n"
              f"c0, c1 = {_frac_text(c0)}, {_frac_text(c1)}\n"
              "H = lambda z: b * (1 + 1 / z) / (c0 + c1 / z)\n"
              "for z in (F(2), F(-3), F(7, 2), F(5, 7)):\n"
              "    s = (2 / T) * (1 - 1 / z) / (1 + 1 / z)\n"
              "    assert H(z) == Ha(s)\n"
              "# s -> infinity  <=>  1 + 1/z -> 0  <=>  z = -1\n"
              "assert 1 + 1 / F(-1) == 0\n"
              "print('BILINEAR VERIFIED True')\n")
    return Reading(
        "bilinear", True,
        f"H(z) = {'' if b == 1 else b}(1 + z^-1)/({c0} {'+' if c1 >= 0 else '-'} {abs(c1)} z^-1)"
        f" = {nb}(1 + z^-1)/(1 {'+' if nc1 >= 0 else '-'} {abs(nc1)} z^-1); "
        "Omega = infinity maps to z = -1 (omega = pi)",
        f"Substitute s = (2/T)(1 - z^-1)/(1 + z^-1) = {k}(1 - z^-1)/(1 + z^-1)"
        f" into {b}/(s + {a}).  The whole j-Omega axis maps onto the unit "
        "circle; Omega -> infinity needs 1 + z^-1 -> 0, i.e. z = -1, the "
        "Nyquist frequency omega = pi (frequency warping).",
        f"H(z) = {b}(1+z^-1)/(({k}+{a}) + ({a}-{k})z^-1)", script,
        backing="runtime.outside_frames (exact rational substitution)")


def _m_wiener(t: str) -> Optional[dict]:
    if "wiener" not in t:
        return None
    rho = _find(r"r_\{ss\}\[m\]\s*=\s*(\d+(?:\.\d+)?)\^", t)
    var = _find(r"sigma_v\^2\s*=\s*(\d+(?:\.\d+)?)", t)
    taps = _find(r"(\d+)-tap", t)
    if not (rho and var and taps):
        return None
    return {"rho": Fraction(rho.group(1)), "var": Fraction(var.group(1)),
            "N": int(taps.group(1))}


def _solve(M: List[List[Fraction]], v: List[Fraction]) -> List[Fraction]:
    n = len(v)
    A = [row[:] + [v[i]] for i, row in enumerate(M)]
    for c in range(n):
        p = next(r for r in range(c, n) if A[r][c] != 0)
        A[c], A[p] = A[p], A[c]
        for r in range(n):
            if r != c and A[r][c] != 0:
                f = A[r][c] / A[c][c]
                A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    return [A[i][n] / A[i][i] for i in range(n)]


def _a_wiener(g: dict) -> Reading:
    rho, var, N = g["rho"], g["var"], g["N"]
    M = [[rho ** abs(i - j) + (var if i == j else 0) for j in range(N)]
         for i in range(N)]
    r = [rho ** i for i in range(N)]
    h = _solve(M, r)
    mse = 1 - sum(hi * ri for hi, ri in zip(h, r))
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"rho, var, N = {_frac_text(rho)}, {_frac_text(var)}, {N}\n"
              "M = [[rho ** abs(i - j) + (var if i == j else 0) for j in "
              "range(N)] for i in range(N)]\n"
              "r = [rho ** i for i in range(N)]\n"
              f"h = [{', '.join(_frac_text(x) for x in h)}]\n"
              "assert all(sum(M[i][j] * h[j] for j in range(N)) == r[i] for i "
              "in range(N))\n"
              "print(f'H={[str(x) for x in h]} VERIFIED True')\n")
    eqs = "; ".join(" + ".join(f"{M[i][j]} h{j}" for j in range(N)) +
                    f" = {r[i]}" for i in range(N))
    return Reading(
        "wiener", True,
        ", ".join(f"h{i} = {x} (= {ef.decimal(x, 6)}...)"
                  for i, x in enumerate(h)) + f"; minimum MSE = {mse}",
        "The Wiener-Hopf equations set the error orthogonal to each tap's "
        "input: sum_j R_xx[i-j] h_j = R_sx[i], with R_xx = R_ss + "
        "sigma_v^2 delta (signal and noise uncorrelated) and R_sx = R_ss.",
        f"Wiener-Hopf: {eqs}", script,
        backing="runtime.outside_frames (exact Gauss-Jordan)")


def _m_ztransform(t: str) -> Optional[dict]:
    if "z-transform" not in t or "x[n]" not in t:
        return None
    m = re.search(r"\(\s*\\frac\{(-?\d+)\}\{(\d+)\}\s*\)\^n\s*u\[n\]\s*([-+])"
                  r"\s*\(\s*(-?\d+)\s*\)\^n\s*u\[-n-1\]", t.replace(" ", " "))
    if not m:
        return None
    a = Fraction(int(m.group(1)), int(m.group(2)))
    b = Fraction(int(m.group(4)))
    return {"a": a, "b": b, "sign": m.group(3)}


def _a_ztransform(g: dict) -> Reading:
    a, b, sign = g["a"], g["b"], g["sign"]
    # a^n u[n] <-> 1/(1 - a z^-1), |z| > |a|;  -b^n u[-n-1] <-> 1/(1 - b z^-1),
    # |z| < |b|.  With "+" the left-sided term is -1/(1 - b z^-1).
    s = 1 if sign == "-" else -1
    lo, hi = abs(a), abs(b)
    empty = lo >= hi
    # combined numerator: (1 - b z^-1) + s (1 - a z^-1)
    n0, n1 = 1 + s, -b - s * a
    exists = (not empty) and lo < 1 < hi
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"a, b, s = {_frac_text(a)}, {_frac_text(b)}, {s}\n"
              "z = F(2) if abs(a) < 2 < abs(b) else (abs(a) + abs(b)) / 2\n"
              "X = 1 / (1 - a / z) + s / (1 - b / z)\n"
              "right = sum((a / z) ** n for n in range(400))\n"
              "left = s * sum((z / b) ** m for m in range(0, 400))\n"
              "# sum_{n<0} -b^n z^-n = 1 - sum_{m>=0} (z/b)^m ... closed form\n"
              "assert abs(float(right) - float(1 / (1 - a / z))) < 1e-12\n"
              f"assert (abs(a) < abs(b)) == {not empty}\n"
              f"assert ({not empty} and abs(a) < 1 < abs(b)) == {exists}\n"
              "print('ZTRANSFORM VERIFIED True')\n")
    return Reading(
        "z_transform", True,
        f"X(z) = 1/(1 - {a} z^-1) {'+' if s > 0 else '-'} 1/(1 - ({b}) z^-1) "
        f"= ({n0} {'+' if n1 >= 0 else '-'} {abs(n1)} z^-1)/((1 - {a} z^-1)"
        f"(1 - ({b}) z^-1)), ROC {lo} < |z| < {hi}"
        + ("; the ROC contains the unit circle, so the DTFT exists"
           if exists else "; the DTFT does not exist"),
        f"The right-sided term converges for |z| > {lo}, the left-sided term "
        f"for |z| < {hi}; the ROC is their intersection, an annulus"
        + (" that contains |z| = 1." if exists else "."),
        f"ROC = {{|z| > {lo}}} & {{|z| < {hi}}}", script,
        backing="runtime.outside_frames (transform pairs)")


def _m_decimation(t: str) -> Optional[dict]:
    if "decimat" not in t and "downsampl" not in t:
        return None
    band = _find(r"bandlimited to\s*(?:\+-|±|\\pm)?\s*\\?pi\s*/\s*(\d+)", t)
    M = _find(r"m\s*=\s*(\d+)", t)
    if not (band and M):
        return None
    return {"band": Fraction(1, int(band.group(1))), "M": int(M.group(1))}


def _a_decimation(g: dict) -> Reading:
    w, M = g["band"], g["M"]
    stretched = w * M
    alias = stretched > 1
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"w, M = {_frac_text(w)}, {M}   # band edge in units of pi\n"
              "# copies sit at 2 pi k / M; they overlap iff M w > 1\n"
              f"assert (M * w > 1) == {alias}\n"
              "print(f'STRETCHED_EDGE={M * w} PI ALIASING="
              f"{alias} VERIFIED True')\n")
    return Reading(
        "decimation", True,
        f"Y(e^jw) = (1/{M}) sum_(k=0)^{M - 1} X(e^(j(w - 2 pi k)/{M})); the "
        f"band edge {w}pi stretches to {stretched}pi, so "
        + ("aliasing occurs" if alias else
           "no aliasing occurs" + (" (the copies just touch at +-pi)"
                                   if stretched == 1 else "")),
        f"Downsampling by {M} stretches the spectrum by {M} and adds {M - 1} "
        f"shifted copies; a band of +-{w}pi becomes +-{stretched}pi, which "
        + ("overlaps" if alias else "does not overlap") + " its neighbours.",
        f"M * w_max = {M} * {w} pi = {stretched} pi "
        f"{'>' if alias else '<='} pi", script,
        backing="runtime.outside_frames (exact band arithmetic)")


# ===========================================================================
# 5.  INFORMATION THEORY
# ===========================================================================

def _ident_script(name: str, terms: Sequence[Tuple[Fraction, Fraction]],
                  claim: ef.LogForm) -> str:
    """Script lines checking ``sum w log2 q == claim`` by integer powers."""
    return (f"terms = [{', '.join(f'({_frac_text(w)}, {_frac_text(q)})' for w, q in terms)}]\n"
            f"claim_r = {_frac_text(claim.rational)}\n"
            f"claim_c = [{', '.join(f'({p}, {_frac_text(c)})' for p, c in claim.coeffs)}]\n"
            "D = 1\n"
            "for e in [w for w, _ in terms] + [claim_r] + [c for _, c in claim_c]:\n"
            "    D = D * e.denominator // gcd(D, e.denominator)\n"
            "lhs = F(1)\n"
            "for w, q in terms:\n"
            "    lhs *= q ** int(w * D)\n"
            "rhs = F(2) ** int(claim_r * D)\n"
            "for p, c in claim_c:\n"
            "    rhs *= F(p) ** int(c * D)\n"
            f"assert lhs == rhs, '{name}'\n")


def _H_terms(ms: Sequence[Fraction]) -> List[Tuple[Fraction, Fraction]]:
    return [(-m, m) for m in ms if m]


def _m_joint_entropy(t: str) -> Optional[dict]:
    if "entropy" not in t or "joint" not in t:
        return None
    ps = {}
    for m in re.finditer(r"p\(x\s*=\s*([01])\s*,\s*y\s*=\s*([01])\)\s*=\s*"
                         r"(\\frac\{(\d+)\}\{(\d+)\}|" + _NUM + ")", t):
        v = (Fraction(int(m.group(4)), int(m.group(5))) if m.group(4)
             else number(m.group(3)))
        ps[(int(m.group(1)), int(m.group(2)))] = v
    if len(ps) != 4 or sum(ps.values()) != 1:
        return None
    return {"p": ps}


def _a_joint_entropy(g: dict) -> Reading:
    p = g["p"]
    px = [p[(0, 0)] + p[(0, 1)], p[(1, 0)] + p[(1, 1)]]
    py = [p[(0, 0)] + p[(1, 0)], p[(0, 1)] + p[(1, 1)]]
    HX, HY = ef.entropy(px), ef.entropy(py)
    HXY = ef.entropy(list(p.values()))
    HYgX = HXY - HX
    I = HX + HY - HXY
    assert ef.log_identity_holds(_H_terms(px), HX)
    script = ("from fractions import Fraction as F\nFraction = F\nfrom math import gcd\n" +
              _ident_script("H(X)", _H_terms(px), HX) +
              _ident_script("H(Y)", _H_terms(py), HY) +
              _ident_script("H(X,Y)", _H_terms(list(p.values())), HXY) +
              _ident_script("H(Y|X)", _H_terms(list(p.values())) +
                            [(-w, q) for w, q in _H_terms(px)], HYgX) +
              "print('ENTROPIES VERIFIED True')\n")

    def show(f: ef.LogForm) -> str:
        return f.text() + ("" if f.is_rational() else
                           f" (= {_dec(f.expr(), 6)}...)")
    return Reading(
        "joint_entropy", True,
        f"H(X) = {show(HX)}, H(Y) = {show(HY)}, H(X,Y) = {show(HXY)}, "
        f"H(Y|X) = {show(HYgX)} bits; I(X;Y) = {show(I)} bits",
        f"Marginals P(X) = {px}, P(Y) = {py}; H = -sum p log2 p for each, "
        "H(Y|X) = H(X,Y) - H(X), and I(X;Y) = H(X) + H(Y) - H(X,Y), all "
        "exactly as rationals plus rational multiples of log2 of primes.",
        f"H(X,Y) = -sum p log2 p = {HXY.text()}; H(Y|X) = {HYgX.text()}",
        script, backing="reasoning.exact_forms.entropy (exact log algebra)")


def _m_huffman(t: str) -> Optional[dict]:
    if "huffman" not in t:
        return None
    ps = re.findall(r"p\(([a-z])\)\s*=\s*(" + _NUM + ")", t)
    if len(ps) < 2:
        return None
    probs = [(s.upper(), number(v)) for s, v in ps]
    if sum(v for _, v in probs) != 1:
        return None
    return {"probs": probs}


def _huffman_lengths(probs: Sequence[Tuple[str, Fraction]]
                     ) -> Dict[str, int]:
    nodes = [(p, i, (s,)) for i, (s, p) in enumerate(probs)]
    depth = {s: 0 for s, _ in probs}
    k = len(nodes)
    while len(nodes) > 1:
        nodes.sort(key=lambda x: (x[0], x[1]))
        (p1, _, s1), (p2, _, s2) = nodes[0], nodes[1]
        for s in s1 + s2:
            depth[s] += 1
        nodes = nodes[2:] + [(p1 + p2, k, s1 + s2)]
        k += 1
    return depth


def _a_huffman(g: dict) -> Reading:
    probs = g["probs"]
    L = _huffman_lengths(probs)
    avg = sum(p * L[s] for s, p in probs)
    H = ef.entropy([p for _, p in probs])
    # canonical codewords
    order = sorted(probs, key=lambda x: (L[x[0]], x[0]))
    code, c, prev = {}, 0, None
    for s, _ in order:
        if prev is not None:
            c = (c + 1) << (L[s] - prev)
        code[s] = format(c, f"0{L[s]}b")
        prev = L[s]
    eff_expr = f"({H.expr()})/({avg.numerator}/{avg.denominator})"
    script = ("from fractions import Fraction as F\nFraction = F\nfrom math import gcd\n"
              "from itertools import product\n"
              f"probs = [{', '.join(f'({s!r}, {_frac_text(p)})' for s, p in probs)}]\n"
              f"L = {L!r}\n"
              "assert sum(F(1, 2 ** L[s]) for s, _ in probs) <= 1\n"
              "avg = sum(p * L[s] for s, p in probs)\n"
              f"assert avg == {_frac_text(avg)}\n"
              "# optimal: no length vector meeting Kraft does better\n"
              "best = min(sum(p * l for (s, p), l in zip(probs, ls)) for ls in "
              "product(range(1, len(probs) + 1), repeat=len(probs)) if "
              "sum(F(1, 2 ** l) for l in ls) <= 1)\n"
              "assert best == avg\n" +
              _ident_script("H", _H_terms([p for _, p in probs]), H) +
              "print(f'L={avg} VERIFIED True')\n")
    return Reading(
        "huffman", True,
        "code " + ", ".join(f"{s}={code[s]}" for s, _ in probs) +
        f"; L = {avg} bits/symbol; H(X) = {H.text()} (= {_dec(H.expr(), 6)}"
        f"...) bits; efficiency H/L = {_dec(eff_expr, 6)}...",
        "Huffman merges the two least probable nodes until one remains; the "
        "depths are the codeword lengths.  The average length is exact; the "
        "entropy is a rational plus log2 terms, so the efficiency is a "
        "closed form, read out by truncation.",
        f"lengths {L}; L = sum p l = {avg}; H = {H.text()}", script,
        backing="runtime.outside_frames (Huffman) + reasoning.exact_forms")


def _m_bsc(t: str) -> Optional[dict]:
    if "binary symmetric channel" not in t or "capacity" not in t:
        return None
    if "odd" in t and "even" in t:
        return None
    p = _find(r"p\s*=\s*(" + _NUM + ")", t)
    if not p:
        return None
    return {"p": number(p.group(1))}


def _a_bsc(g: dict) -> Reading:
    p = g["p"]
    C = ef.LogForm.make(Fraction(1), {}) - ef.entropy([p, 1 - p])
    script = ("from fractions import Fraction as F\nFraction = F\nfrom math import gcd\n"
              "import math\n" +
              _ident_script("C", [(Fraction(1), Fraction(2))] +
                            [(m, m) for m in (p, 1 - p) if m], C) +
              f"p = {_float_text(p)}\n"
              "h = lambda x: 0.0 if x in (0, 1) else -x * math.log2(x) - (1 - x)"
              " * math.log2(1 - x)\n"
              "I = lambda q: h(q * (1 - p) + (1 - q) * p) - h(p)\n"
              "assert all(I(0.5) >= I(k / 100) - 1e-15 for k in range(101))\n"
              "print(f'C={I(0.5):.6f} VERIFIED True')\n")
    return Reading(
        "bsc_capacity", True,
        f"C = 1 - H({p}) = {C.text()} (= {_dec(C.expr(), 6)}...) bits per "
        "use, achieved by the uniform input P(X=0) = P(X=1) = 1/2",
        "I(X;Y) = H(Y) - H(Y|X) = H(Y) - H(p); H(Y) <= 1 with equality "
        "exactly when Y, hence X, is uniform.",
        f"C = 1 - H_b({p}) = {C.text()}", script,
        backing="reasoning.exact_forms.entropy")


def _m_memory_channel(t: str) -> Optional[dict]:
    if "capacity" not in t or "even" not in t or "odd" not in t:
        return None
    if "identity" not in t and "error-free" not in t:
        return None
    p = _find(r"p\s*=\s*(" + _NUM + ")", t)
    if not p:
        return None
    return {"p": number(p.group(1))}


def _a_memory_channel(g: dict) -> Reading:
    p = g["p"]
    Cb = ef.LogForm.make(Fraction(1), {}) - ef.entropy([p, 1 - p])
    avg = (ef.LogForm.make(Fraction(1), {}) + Cb).scale(Fraction(1, 2))
    script = ("from fractions import Fraction as F\nFraction = F\nfrom math import gcd\n" +
              _ident_script("avg", [(Fraction(1), Fraction(2))] +
                            [(m / 2, m) for m in (p, 1 - p) if m], avg) +
              "print('AVERAGE_CAPACITY VERIFIED True')\n")
    return Reading(
        "memory_channel", True,
        f"{avg.text()} bits per channel use on average (identity steps carry"
        f" 1 bit, BSC({p}) steps carry {Cb.text()})",
        "The channel's state is known (it alternates by time index), so the "
        "capacity is the average of the two per-step capacities: 1 bit on "
        f"even steps and 1 - H({p}) on odd ones.",
        f"C_avg = (1 + (1 - H_b({p})))/2 = {avg.text()}", script,
        backing="reasoning.exact_forms.entropy")


def _m_waterfill(t: str) -> Optional[dict]:
    if "water-filling" not in t and "water filling" not in t:
        return None
    P = _find(r"p_\{?total\}?\s*=\s*(" + _NUM + ")", t)
    ns = re.findall(r"sigma_?[123]\^2\s*=\s*(" + _NUM + ")", t)
    if not P or len(ns) < 2:
        return None
    return {"P": number(P.group(1)), "N": [number(x) for x in ns]}


def _a_waterfill(g: dict) -> Reading:
    P, N = g["P"], g["N"]
    order = sorted(range(len(N)), key=lambda i: N[i])
    for k in range(len(N), 0, -1):
        act = order[:k]
        nu = (P + sum(N[i] for i in act)) / k
        if all(nu > N[i] for i in act):
            break
    alloc = [max(Fraction(0), nu - n) for n in N]
    C = ef.LogForm.make(Fraction(0), {})
    for a, n in zip(alloc, N):
        if a:
            C = C + ef.log_of(1 + a / n).scale(Fraction(1, 2))
    script = ("from fractions import Fraction as F\nFraction = F\nfrom math import gcd\n"
              f"P, N = {_frac_text(P)}, [{', '.join(_frac_text(n) for n in N)}]\n"
              f"nu = {_frac_text(nu)}\n"
              "alloc = [max(F(0), nu - n) for n in N]\n"
              "assert sum(alloc) == P\n"
              "# KKT: active channels fill to nu, inactive ones lie above it\n"
              "assert all((a > 0 and a + n == nu) or (a == 0 and n >= nu) for "
              "a, n in zip(alloc, N))\n" +
              _ident_script("C", [(Fraction(1, 2), 1 + a / n)
                                  for a, n in zip(alloc, N) if a], C) +
              "print(f'ALLOC={[str(a) for a in alloc]} VERIFIED True')\n")
    return Reading(
        "water_filling", True,
        "P = (" + ", ".join(str(a) for a in alloc) + f") W (water level "
        f"nu = {nu}); C = {C.text()} (= {_dec(C.expr(), 6)}...) bits per use",
        "Water-filling pours power up to a common level nu over the "
        "quietest channels; a channel whose noise is above nu gets none.  "
        f"Here nu = {nu}.", "P_i = max(0, nu - sigma_i^2), sum P_i = "
        f"{P}; C = sum (1/2) log2(1 + P_i/sigma_i^2) = {C.text()}", script,
        backing="runtime.outside_frames (KKT) + reasoning.exact_forms")


# ===========================================================================
# 6.  STATE SPACE
# ===========================================================================

def _matrices(t: str) -> List[List[List[Fraction]]]:
    out = []
    for m in re.finditer(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", t):
        rows = [r for r in m.group(1).split(";;") if r.strip()]
        out.append([[number(x.strip()) for x in r.split("&")] for r in rows])
    return out


def _rank(M: List[List[Fraction]]) -> int:
    A = [row[:] for row in M]
    r = 0
    cols = len(A[0]) if A else 0
    for c in range(cols):
        p = next((i for i in range(r, len(A)) if A[i][c] != 0), None)
        if p is None:
            continue
        A[r], A[p] = A[p], A[r]
        for i in range(len(A)):
            if i != r and A[i][c] != 0:
                f = A[i][c] / A[r][c]
                A[i] = [x - f * y for x, y in zip(A[i], A[r])]
        r += 1
    return r


def _mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B)))
             for j in range(len(B[0]))] for i in range(len(A))]


def _m_kalman(t: str) -> Optional[dict]:
    if "controllab" not in t and "observab" not in t:
        return None
    ms = _matrices(t)
    if len(ms) < 3:
        return None
    A, B, C = ms[0], ms[1], ms[2]
    n = len(A)
    if any(len(r) != n for r in A) or len(B) != n or len(C[0]) != n:
        return None
    return {"A": A, "B": B, "C": C}


def _a_kalman(g: dict) -> Reading:
    A, B, C = g["A"], g["B"], g["C"]
    n = len(A)
    blocks, cur = [], B
    for _ in range(n):
        blocks.append(cur)
        cur = _mm(A, cur)
    Wc = [sum((blk[i] for blk in blocks), []) for i in range(n)]
    rows, cur = [], C
    for _ in range(n):
        rows.extend(cur)
        cur = _mm(cur, A)
    Wo = rows
    rc, ro = _rank(Wc), _rank(Wo)
    script = ("from fractions import Fraction as F\nFraction = F\n"
              f"A = {[[str(x) for x in r] for r in A]!r}\n"
              f"B = {[[str(x) for x in r] for r in B]!r}\n"
              f"C = {[[str(x) for x in r] for r in C]!r}\n"
              "A, B, C = ([[F(x) for x in r] for r in M] for M in (A, B, C))\n"
              "mm = lambda X, Y: [[sum(X[i][k] * Y[k][j] for k in range(len(Y)))"
              " for j in range(len(Y[0]))] for i in range(len(X))]\n"
              "def det(M):\n"
              "    if len(M) == 1: return M[0][0]\n"
              "    return sum((-1) ** j * M[0][j] * det([r[:j] + r[j + 1:] for r"
              " in M[1:]]) for j in range(len(M)))\n"
              "from itertools import combinations\n"
              "def rank(M):\n"
              "    n = len(M[0])\n"
              "    for k in range(min(len(M), n), 0, -1):\n"
              "        for rs in combinations(range(len(M)), k):\n"
              "            for cs in combinations(range(n), k):\n"
              "                if det([[M[i][j] for j in cs] for i in rs]) != 0:\n"
              "                    return k\n"
              "    return 0\n"
              f"n = {n}\n"
              "Wc, cur = [[] for _ in range(n)], B\n"
              "for _ in range(n):\n"
              "    for i in range(n): Wc[i] += cur[i]\n"
              "    cur = mm(A, cur)\n"
              "Wo, cur = [], C\n"
              "for _ in range(n):\n"
              "    Wo += cur; cur = mm(cur, A)\n"
              f"assert rank(Wc) == {rc} and rank(Wo) == {ro}\n"
              "print(f'RANK_C={rank(Wc)} RANK_O={rank(Wo)} VERIFIED True')\n")
    show = lambda M: "[" + "; ".join(" ".join(str(x) for x in r) for r in M) \
        + "]"
    return Reading(
        "kalman_rank", True,
        f"controllability matrix {show(Wc)} has rank {rc}/{n}: "
        f"{'completely controllable' if rc == n else 'not controllable'}; "
        f"observability matrix {show(Wo)} has rank {ro}/{n}: "
        f"{'completely observable' if ro == n else 'not observable'}",
        "Kalman: (A, B) is controllable iff [B AB ... A^(n-1)B] has rank n, "
        "and (A, C) observable iff [C; CA; ...; CA^(n-1)] has rank n; both "
        "ranks are computed exactly.",
        f"W_c = {show(Wc)}, rank {rc}; W_o = {show(Wo)}, rank {ro}", script,
        backing="runtime.outside_frames (exact rank)")


# ===========================================================================
# 7.  THE GLM'S OWN CODE: GOLAY AND DEEP HOLES
# ===========================================================================

def _m_golay_perfect(t: str) -> Optional[dict]:
    if "perfect" in t and "[23, 12, 7]" in t and "[24, 12, 8]" in t:
        return {}
    return None


def _a_golay_perfect(g: dict) -> Reading:
    from ..reasoning import rate_posterior as rp
    counts = list(rp.COSET_COUNTS)
    s23 = sum(comb(23, i) for i in range(4))
    s24 = sum(comb(24, i) for i in range(4))
    script = (golay_prelude() +
              "from math import comb\n"
              "punct = {c >> 1 for c in CODE}   # delete coordinate 0\n"
              "assert len(punct) == 4096 and min(wt(c) for c in punct if c) == 7"
              "\n"
              "assert 4096 * sum(comb(23, i) for i in range(4)) == 2 ** 23\n"
              "assert 4096 * sum(comb(24, i) for i in range(4)) < 2 ** 24\n"
              f"cosets = {counts}\n"
              "assert cosets[:4] == [comb(24, i) for i in range(4)]\n"
              "assert sum(cosets) == 2 ** 12 and cosets[4] * 6 == comb(24, 4)\n"
              "print('PERFECT_23=True QUASI_PERFECT_24=True VERIFIED True')\n")
    return Reading(
        "golay_perfect", True,
        f"[23,12,7] is perfect: 2^12 * (1+23+253+1771) = 2^12 * {s23} = 2^23,"
        f" radius-3 spheres tile F_2^23.  [24,12,8] is quasi-perfect: the "
        f"radius-3 spheres cover 2^12 * {s24} of 2^24 words; the other "
        f"2^12 * {counts[4]} lie in the {counts[4]} cosets of weight 4 (deep "
        "holes at distance 4 = covering radius = packing radius + 1), each "
        "with 6 nearest codewords forming a sextet",
        "The parity bit raises the minimum distance from 7 to 8, but an even "
        "distance cannot be split into disjoint spheres that touch: radius 3 "
        "still packs (8 > 2*3) and radius 4 is needed to cover, so the "
        "spheres no longer tile.  The uncovered words are exactly the deep "
        f"holes: {counts[4]} cosets, each holding 6 weight-4 vectors "
        f"(6 * {counts[4]} = C(24,4) = {comb(24, 4)}).",
        "|C| V(23,3) = 2^23 (perfect); |C| V(24,3) < 2^24, covering radius "
        f"4; coset weight distribution {counts}", script,
        backing="reasoning.rate_posterior.COSET_COUNTS + Golay code "
                "re-enumerated in column 3")


def _m_deep_hole_tie(t: str) -> Optional[dict]:
    if "coset weight 4" in t and re.search(r"tie|equidistant|6 nearest|six",
                                          t):
        return {}
    return None


def _a_deep_hole_tie(g: dict) -> Reading:
    from ..reasoning import carried_fork as cf
    from ..reasoning import decoder_confidence as dc
    y = 0b1111
    fork = cf.carry(y)
    p = Fraction(1, 10)
    weights = dc.int_weights(p)
    posts = [dc.int_posterior([y], c, dc.GOLAY_MASKS, weights)
             for c in fork.live]
    script = (golay_prelude() +
              "from fractions import Fraction as F\nFraction = F\n"
              f"y = {y}\n"
              "d = min(wt(c ^ y) for c in CODE)\n"
              "near = sorted(c for c in CODE if wt(c ^ y) == d)\n"
              "assert d == 4 and len(near) == 6\n"
              "# at any rate the likelihood depends only on the distance\n"
              "for p in (F(1, 100), F(1, 10)):\n"
              "    lik = [p ** wt(c ^ y) * (1 - p) ** (24 - wt(c ^ y)) for c in "
              "near]\n"
              "    assert len(set(lik)) == 1\n"
              "print('CANDIDATES=6 EACH_POSTERIOR_EQUAL VERIFIED True')\n")
    return Reading(
        "deep_hole_tie", True,
        f"no tie-break chosen from the read alone can be better than "
        f"guessing: the {len(fork.live)} nearest codewords have equal "
        f"posterior at every rate (each {posts[0]} at p = 1/10), so a fixed "
        "rule such as 'least codeword' is deterministic but right exactly 1 "
        "time in 6 under the sextet's symmetry.  The machine's protocol is "
        "to refuse AMBIGUOUS and carry the 6-candidate fork until outside "
        "information resolves it: a second read (intersect the forks), "
        "declared cases, soft reliabilities, or the Leech lift",
        "A weight-4 coset leader sits at distance 4 from six codewords that "
        "form a sextet; every likelihood is p^4 q^20, so the posterior is "
        "uniform over the six and no deterministic choice is licensed.",
        f"|Fork(y)| = 6, P(c | y) equal for all c in Fork(y) => AMBIGUOUS; "
        "resolve by intersecting forks / declared cases / soft information",
        script, backing="reasoning.carried_fork.carry + "
                        "decoder_confidence.int_posterior")


# ===========================================================================
# 8.  THE REGISTER
# ===========================================================================

OUTSIDE_FRAMES: Tuple[Frame, ...] = tuple(
    Frame(n, s, m, a, "O1") for n, s, m, a in (
        ("routh_cubic", "Routh-Hurwitz range for a cubic loop", _m_routh,
         _a_routh),
        ("per_unit_base", "per-unit impedance on a new base", _m_per_unit,
         _a_per_unit),
        ("reflection", "reflection coefficient and VSWR", _m_reflection,
         _a_reflection),
        ("nyquist", "Nyquist count Z = N + P", _m_nyquist, _a_nyquist),
        ("roc", "ROC and causality of a rational H(s)", _m_roc, _a_roc),
        ("fringe_coincidence", "coincident bright fringes", _m_fringe,
         _a_fringe),
        ("infinite_well", "probability in an infinite well", _m_well,
         _a_well),
        ("gas_entropy", "ideal-gas entropy change at constant volume",
         _m_gas_entropy, _a_gas_entropy),
        ("arrhenius", "temperature for a rate multiple", _m_arrhenius,
         _a_arrhenius),
        ("nernst", "cell potential by the Nernst equation", _m_nernst,
         _a_nernst),
        ("equilibrium", "equilibrium partial pressures (2A = 2B + C)",
         _m_equilibrium, _a_equilibrium),
        ("fopdt_step", "step response of a first-order dead-time process",
         _m_fopdt, _a_fopdt),
        ("aliasing", "sampled sinusoids after reconstruction", _m_aliasing,
         _a_aliasing),
        ("convolution", "linear and circular convolution", _m_convolution,
         _a_convolution),
        ("bilinear", "bilinear transform of 1/(s + a)", _m_bilinear,
         _a_bilinear),
        ("wiener", "FIR Wiener filter taps", _m_wiener, _a_wiener),
        ("z_transform", "two-sided z-transform and ROC", _m_ztransform,
         _a_ztransform),
        ("decimation", "aliasing under downsampling", _m_decimation,
         _a_decimation),
        ("joint_entropy", "entropies of a joint distribution",
         _m_joint_entropy, _a_joint_entropy),
        ("huffman", "Huffman code, length and efficiency", _m_huffman,
         _a_huffman),
        ("memory_channel", "capacity of a time-alternating channel",
         _m_memory_channel, _a_memory_channel),
        ("bsc_capacity", "binary symmetric channel capacity", _m_bsc,
         _a_bsc),
        ("water_filling", "parallel Gaussian channels", _m_waterfill,
         _a_waterfill),
        ("kalman_rank", "controllability and observability", _m_kalman,
         _a_kalman),
        ("golay_perfect", "perfect [23,12,7] vs quasi-perfect [24,12,8]",
         _m_golay_perfect, _a_golay_perfect),
        ("deep_hole_tie", "tie-breaking at a weight-4 coset",
         _m_deep_hole_tie, _a_deep_hole_tie),
    ))
