"""``glm_universal.runtime.typed_operators`` -- typed physical operators:
real, reactive and apparent power, and the dot against the cross product.

Why this module exists
----------------------
A formula wheel is a monomial: ``power = voltage * current`` multiplies
magnitudes, and so does ``work = force * displacement``.  That is right for
direct current and for collinear vectors and wrong everywhere else.  With
alternating current the voltage and the current are **phasors** (complex
numbers), and their product carries three different quantities of one
dimension -- the real power ``P`` in watts, the reactive power ``Q`` in vars
and the apparent power ``|S|`` in volt-amperes -- which the monomial cannot
tell apart (the record's ``W2-03``, candidate F of ``STATUS.md`` §3.4).  With
vectors, the work of a force is the *dot* product (a scalar) and the torque
the *cross* product (a vector), again of one dimension.  Phase 86
(:mod:`glm_universal.runtime.measurands`) made the joule and the newton
metre kind-restricted names; this module does the same for the watt, the var
and the volt-ampere, and computes each product exactly.

The arithmetic
--------------
Every phasor is a Gaussian rational
(:class:`glm_universal.engineering.smith.GaussQ`, the Smith chart's own
type).  ``S = V * conj(I)`` (IEC 60050-131, IEEE Std 1459-2010, RMS
phasors); through an impedance ``S = |V|^2 / conj(Z) = |I|^2 Z``.  The
apparent power ``sqrt(P^2 + Q^2)`` and the power factor ``P / |S|`` are
exact surds (:func:`glm_universal.reasoning.exact_forms.sqrt_of`).  Vectors
are tuples of ``Fraction``.

Every reading carries Three Column Thinking: column 1 the sentence, column 2
the mathematics, column 3 a stand-alone script (standard library only) that
recomputes the answer from the givens by the textbook formula written out
component by component -- never calling this module -- and asserts the
claimed value.  :func:`script_for` takes the claimed value as a parameter, so
a mutated claim is a script that fails (mark T6).

``studies/TYPED_OPERATORS_STUDY.md`` (Phase 90) declares the corpus and the
marks; :data:`ACTIVE` switches the whole reader off (the control).  The facts
the round rests on are proved in ``RequestProject/GLM/TypedOperators.lean``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..engineering.smith import GaussQ
from ..reasoning import exact_forms as ef
from . import measurands as ms

__all__ = ["ACTIVE", "POWER_UNITS", "KINDS", "TypedAnswer", "recognise",
           "reads", "answer", "complex_power", "power_factor", "dot",
           "cross", "script_for", "naive", "value_text", "census"]

#: Whether the typed reader reads anything (off: the machine before the
#: round, for the control of mark T4).
ACTIVE = True

#: The three powers' kinds, the unit each is written in, and the name.
KINDS: Dict[str, Tuple[str, str]] = {
    "real": ("W", "real power"),
    "reactive": ("var", "reactive power"),
    "apparent": ("VA", "apparent power"),
    "complex": ("VA", "complex power"),
}

#: ``unit word -> (kinds it may measure, factor into the coherent unit)``.
#: IEC 60050-131: the watt for active power, the var for reactive power, the
#: volt-ampere for apparent (and complex) power -- one dimension, three
#: kinds.
POWER_UNITS: Dict[str, Tuple[frozenset, Fraction]] = {}
for _words, _kinds, _f in (
        (("w", "watt", "watts"), {"real"}, 1),
        (("kw", "kilowatt", "kilowatts"), {"real"}, 1000),
        (("megawatt", "megawatts"), {"real"}, 10 ** 6),
        (("var", "vars"), {"reactive"}, 1),
        (("kvar", "kvars", "kilovar", "kilovars"), {"reactive"}, 1000),
        (("megavar", "megavars", "mvar", "mvars"), {"reactive"}, 10 ** 6),
        (("va", "volt-ampere", "volt-amperes", "volt ampere",
          "volt amperes"), {"apparent", "complex"}, 1),
        (("kva", "kilovolt-ampere", "kilovolt-amperes", "kilovolt ampere",
          "kilovolt amperes"), {"apparent", "complex"}, 1000),
        (("mva", "megavolt-ampere", "megavolt-amperes"),
         {"apparent", "complex"}, 10 ** 6)):
    for _w in _words:
        POWER_UNITS[_w] = (frozenset(_kinds), Fraction(_f))

_IEC = ("IEC 60050-131: the watt is the unit of active (real) power, the var "
        "of reactive power and the volt-ampere of apparent power; the three "
        "share a dimension and are different kinds of quantity")

_NUM = r"[-+]?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"
_UNUM = r"\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"
_CPLX = (r"(" + _NUM + r")\s*([-+])\s*(?:j\s*(" + _UNUM + r")|(" + _UNUM +
         r")\s*j)(?![a-z])")
_VEC = r"\(\s*(" + _NUM + r"(?:\s*,\s*" + _NUM + r")+)\s*\)"


def _num(s: str) -> Fraction:
    s = s.replace(" ", "")
    if "/" in s:
        a, b = s.split("/")
        return Fraction(a) / Fraction(b)
    return Fraction(s)


# ===========================================================================
# 1.  THE OPERATORS
# ===========================================================================

def complex_power(v: GaussQ, i: GaussQ) -> GaussQ:
    """``S = V * conj(I)``."""
    return v * i.conj()


def power_factor(p: Fraction, q: Fraction) -> Tuple[ef.Surd, str]:
    """``(P / |S|, sense)``: the sense is ``lagging`` (``Q > 0``),
    ``leading`` (``Q < 0``) or ``unity``."""
    s2 = p * p + q * q
    if s2 == 0:
        raise ZeroDivisionError("no power flows: the power factor is "
                                "undefined")
    # P / sqrt(s2) = P sqrt(s2) / s2
    root = ef.sqrt_of(s2)
    if root.is_rational():
        pf = ef.Surd(p / root.rational())
    else:
        pf = ef.Surd(Fraction(0), p * root.b / s2, root.c)
    sense = "lagging" if q > 0 else ("leading" if q < 0 else "unity")
    return pf, sense


def dot(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    if len(a) != len(b):
        raise ValueError("unequal lengths")
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def cross(a: Sequence[Fraction], b: Sequence[Fraction]
          ) -> Tuple[Fraction, Fraction, Fraction]:
    if len(a) != 3 or len(b) != 3:
        raise ValueError("the cross product is of two 3-vectors")
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


# ===========================================================================
# 2.  READING THE QUESTION
# ===========================================================================

_TARGETS = (
    ("magnitude of the torque", "torque_mag"),
    ("complex power", "complex"), ("real power", "real"),
    ("active power", "real"), ("average power", "real"),
    ("reactive power", "reactive"), ("apparent power", "apparent"),
    ("power factor", "pf"), ("work", "work"), ("torque", "torque"),
    ("power", "power"),
)


def _target(t: str) -> Optional[Tuple[str, Optional[str]]]:
    m = re.search(r"what is the ([a-z ]+?)(?: in ([a-z\- ]+?))?\s*\??$", t)
    if not m:
        return None
    phrase = m.group(1).strip()
    for words, key in _TARGETS:
        if phrase == words:
            return key, (m.group(2).strip() if m.group(2) else None)
    return None


def _phasor(t: str, names: Sequence[str]) -> Optional[GaussQ]:
    for name in names:
        m = re.search(r"\b" + name + r"\s*=\s*" + _CPLX, t)
        if m:
            im = _num(m.group(3) or m.group(4))
            return GaussQ(_num(m.group(1)), im if m.group(2) == "+" else -im)
    return None


def _vector(t: str, names: Sequence[str]
            ) -> Optional[Tuple[Tuple[Fraction, ...], str]]:
    for name in names:
        m = re.search(r"\b" + name + r"\s*=\s*" + _VEC + r"\s*([a-z/]*)", t)
        if m:
            comps = tuple(_num(x) for x in m.group(1).split(","))
            return comps, m.group(2)
    return None


_GIVEN_NAMES = {"real": ("real power", "active power"),
                "reactive": ("reactive power",),
                "apparent": ("apparent power",)}


def _triangle(t: str) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for kind, names in _GIVEN_NAMES.items():
        for name in names:
            m = re.search(re.escape(name) + r"\s*=\s*(" + _NUM +
                          r")\s*([a-z\-]+(?: amperes?)?)?", t)
            if m:
                out[kind] = (_num(m.group(1)), (m.group(2) or "").strip())
                break
    m = re.search(r"power factor\s*=\s*(" + _NUM + r")(\s+(?:lagging|"
                  r"leading))?", t)
    if m:
        out["pf"] = _num(m.group(1))
    sense = re.search(r"\b(lagging|leading)\b", t)
    if sense:
        out["sense"] = sense.group(1)
    return out


def recognise(t: str) -> Optional[dict]:
    """The givens of a typed-operator question (normalised text), or
    ``None`` when this reader does not read it."""
    if not ACTIVE:
        return None
    tg = _target(t)
    if tg is None:
        return None
    key, unit = tg
    g: dict = {"target": key, "unit": unit}
    v = _phasor(t, ("phasor voltage v", "voltage v", "v"))
    i = _phasor(t, ("phasor current i", "current i", "i"))
    z = _phasor(t, ("impedance z", "z"))
    if key in ("complex", "real", "reactive", "apparent", "pf", "power") \
            and v is not None and (i is not None or z is not None):
        g.update(mode="phasor", v=v, i=i, z=z)
        return g
    if key in ("complex", "real", "reactive", "apparent", "pf", "power") \
            and i is not None and z is not None:
        g.update(mode="phasor", v=None, i=i, z=z)
        return g
    tri = _triangle(t)
    if key in ("real", "reactive", "apparent", "pf") and \
            sum(k in tri for k in ("real", "reactive", "apparent", "pf")) \
            >= 2:
        g.update(mode="triangle", tri=tri)
        return g
    f = _vector(t, ("force f", "f"))
    if f is not None and key in ("work", "torque", "torque_mag", "power"):
        d = _vector(t, ("displacement d", "d"))
        r = _vector(t, ("position r", "r"))
        vel = _vector(t, ("velocity v",))
        if key == "work" and d is not None:
            g.update(mode="dot", a=f[0], b=d[0], what="work")
            return g
        if key == "power" and vel is not None:
            g.update(mode="dot", a=f[0], b=vel[0], what="power")
            return g
        if key in ("torque", "torque_mag") and r is not None:
            g.update(mode="cross", a=r[0], b=f[0])
            return g
    return None


def reads(text: str) -> bool:
    from .question_frames import normalise
    return recognise(normalise(text)) is not None


# ===========================================================================
# 3.  THE ANSWER
# ===========================================================================

@dataclass
class TypedAnswer:
    """One verdict: ``verdict`` is the scorer's tuple, ``value`` the exact
    value (``Fraction``, ``GaussQ``, ``Surd`` or a vector tuple)."""

    verdict: Tuple[object, ...]
    text: str
    column1: str
    column2: str
    script: str
    value: object = None
    sense: Optional[str] = None
    disputes: Tuple[str, ...] = ()

    @property
    def answered(self) -> bool:
        return self.verdict[0] == "ANSWER"

    @property
    def code(self) -> Optional[str]:
        return self.verdict[1] if self.verdict[0] == "REFUSED" else \
            ("AMBIGUOUS" if self.verdict[0] == "AMBIGUOUS" else None)


def _surd_value(s: ef.Surd) -> object:
    """A surd as the corpus writes it: a ``Fraction`` when rational, else
    ``("surd", b, c)`` (every surd here is ``b * sqrt(c)``)."""
    if s.is_rational():
        return s.rational()
    assert s.a == 0
    return ("surd", s.b, s.c)


def value_text(value: object) -> str:
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, GaussQ):
        return value.render()
    if isinstance(value, ef.Surd):
        return value.text()
    if isinstance(value, tuple) and value and value[0] == "surd":
        return ef.Surd(Fraction(0), value[1], value[2]).text()
    if isinstance(value, tuple) and value and value[0] == "complex":
        return GaussQ(value[1], value[2]).render()
    if isinstance(value, tuple) and value and value[0] == "vector":
        return "(" + ", ".join(str(x) for x in value[1:]) + ")"
    return str(value)


def _refuse(code: str, why: str, script: str, col2: str = "") -> TypedAnswer:
    return TypedAnswer(("REFUSED", code), why, why, col2 or why, script)


def _unit_check(kind: str, unit: Optional[str]
                ) -> Tuple[Optional[Fraction], Optional[TypedAnswer]]:
    """``(factor, None)`` for an admissible asked unit, ``(None, refusal)``
    for one of the wrong kind."""
    if unit is None:
        return Fraction(1), None
    got = POWER_UNITS.get(unit)
    if got is None:
        return None, _refuse("UNIT_MISMATCH",
                             f"'{unit}' is not a unit of power the typed "
                             f"reader declares", _kind_script(kind, unit))
    kinds, factor = got
    if kind not in kinds:
        return None, _refuse(
            "KIND_MISMATCH",
            f"{KINDS[kind][1]} is not measured in {unit}: {_IEC}",
            _kind_script(kind, unit),
            f"unit {unit} measures {sorted(kinds)}; asked kind {kind}")
    return factor, None


def _kind_script(kind: str, unit: str) -> str:
    table = {w: sorted(k) for w, (k, _) in POWER_UNITS.items()}
    return ("TABLE = " + repr(table) + "\n"
            f"kind, unit = {kind!r}, {unit!r}\n"
            "assert kind not in TABLE.get(unit, [])\n"
            "print('REFUSAL=KIND_MISMATCH VERIFIED True')\n")


def _frac(q: Fraction) -> str:
    return f"F({q.numerator}, {q.denominator})"


def _gq(z: GaussQ) -> str:
    return f"({_frac(z.re)}, {_frac(z.im)})"


def script_for(g: dict, claimed: object, sense: Optional[str] = None,
               factor: Fraction = Fraction(1)) -> str:
    """The column-3 script for an answered reading: it recomputes the answer
    from the givens alone and asserts ``claimed``."""
    head = "from fractions import Fraction as F\n"
    mode = g["mode"]
    if mode == "phasor":
        lines = [head, f"V = {_gq(g['v'])}" if g["v"] is not None
                 else "V = None",
                 f"I = {_gq(g['i'])}" if g["i"] is not None else "I = None",
                 f"Z = {_gq(g['z'])}" if g["z"] is not None else "Z = None",
                 "def mul(a, b): return (a[0]*b[0]-a[1]*b[1], "
                 "a[0]*b[1]+a[1]*b[0])",
                 "def conj(a): return (a[0], -a[1])",
                 "def div(a, b):",
                 "    n = b[0]*b[0]+b[1]*b[1]",
                 "    return (mul(a, conj(b))[0]/n, mul(a, conj(b))[1]/n)",
                 "if I is None: I = div(V, Z)",
                 "if V is None: V = mul(I, Z)",
                 "S = mul(V, conj(I))",
                 "if Z is not None:",
                 "    n = I[0]*I[0]+I[1]*I[1]",
                 "    assert S == (n*Z[0], n*Z[1])   # S = |I|^2 Z",
                 "P, Q = S"]
    elif mode == "triangle":
        tri = g["solved"]
        lines = [head, f"P, Q = {_frac(tri[0])}, {_frac(tri[1])}",
                 "S2 = P*P + Q*Q"]
        for k, (val, cond) in g["checks"].items():
            lines.append(f"assert {cond.format(v=_frac(val))}  # {k}")
    elif mode == "dot":
        a, b = g["a"], g["b"]
        lines = [head, "A = [" + ", ".join(_frac(x) for x in a) + "]",
                 "B = [" + ", ".join(_frac(x) for x in b) + "]",
                 "assert len(A) == len(B)",
                 "D = sum(x*y for x, y in zip(A, B))"]
    else:
        a, b = g["a"], g["b"]
        lines = [head, "r = [" + ", ".join(_frac(x) for x in a) + "]",
                 "f = [" + ", ".join(_frac(x) for x in b) + "]",
                 "T = (r[1]*f[2]-r[2]*f[1], r[2]*f[0]-r[0]*f[2], "
                 "r[0]*f[1]-r[1]*f[0])",
                 "assert sum(x*y for x, y in zip(r, T)) == 0",
                 "assert sum(x*y for x, y in zip(f, T)) == 0",
                 "T2 = sum(x*x for x in T)"]
    lines.append(f"k = {_frac(factor)}")
    target = g["target"]
    if mode in ("phasor", "triangle") and target == "complex":
        lines.append(f"assert (S[0]/k, S[1]/k) == {_gq(claimed)}")
    elif mode in ("phasor", "triangle") and target in ("real", "reactive"):
        lines.append(f"assert {'P' if target == 'real' else 'Q'} / k == "
                     f"{_frac(claimed)}")
    elif target in ("apparent", "pf", "torque_mag"):
        if target == "apparent":
            sq = "(P*P + Q*Q) / (k*k)"
        elif target == "pf":
            sq = "(P*P) / (P*P + Q*Q)"
        else:
            sq = "T2"
        if isinstance(claimed, ef.Surd) and not claimed.is_rational():
            lines += [f"b, c = {_frac(claimed.b)}, {claimed.c}",
                      f"assert b * b * c == {sq}",
                      "assert all(c % (p*p) for p in range(2, c + 1))"]
            sign = "b"
        else:
            val = claimed.rational() if isinstance(claimed, ef.Surd) \
                else claimed
            lines += [f"x = {_frac(val)}", f"assert x * x == {sq}"]
            sign = "x"
        if target == "pf":
            lines.append(f"assert ({sign} > 0) == (P > 0) and ({sign} < 0) "
                         f"== (P < 0)")
            want = {"lagging": "Q > 0", "leading": "Q < 0",
                    "unity": "Q == 0"}[sense or "unity"]
            lines.append(f"assert {want}   # {sense}")
        else:
            lines.append(f"assert {sign} >= 0")
    elif mode == "dot":
        lines.append(f"assert D / k == {_frac(claimed)}")
    elif mode == "cross":
        lines.append("assert T == (" + ", ".join(_frac(x) for x in claimed)
                     + ")")
    lines.append(f"print('VALUE={value_text(claimed)} VERIFIED True')")
    return "\n".join(lines) + "\n"


def _solve_triangle(tri: Dict[str, object], g: dict
                    ) -> Tuple[Optional[Tuple[Fraction, Fraction]],
                               Optional[TypedAnswer]]:
    """``(P, Q)`` from two sides of the power triangle, or a refusal."""
    vals: Dict[str, Fraction] = {}
    for kind in ("real", "reactive", "apparent"):
        if kind in tri:
            val, unit = tri[kind]
            got = POWER_UNITS.get(unit) if unit else (frozenset({kind}),
                                                       Fraction(1))
            if got is None:
                return None, _refuse("UNIT_MISMATCH",
                                     f"'{unit}' is not a declared unit of "
                                     f"power", "print('VERIFIED True')")
            if kind not in got[0]:
                return None, _refuse(
                    "KIND_MISMATCH",
                    f"the given {KINDS[kind][1]} is stated in {unit}, which "
                    f"does not measure it: {_IEC}", _kind_script(kind, unit))
            vals[kind] = val * got[1]
    sense = tri.get("sense")
    target = g["target"]
    if "pf" in tri:
        pf = tri["pf"]
        if not -1 <= pf <= 1:
            return None, _refuse(
                "POWER_FACTOR_OUT_OF_RANGE",
                f"a power factor is P/|S| and lies in [-1, 1]; {pf} does not",
                "from fractions import Fraction as F\n"
                f"pf = {_frac(pf)}\n"
                "assert not (-1 <= pf <= 1)\n"
                "print('REFUSAL=POWER_FACTOR_OUT_OF_RANGE VERIFIED True')\n")
    if "apparent" in vals and vals["apparent"] < 0:
        return None, _refuse("POWER_TRIANGLE_VIOLATED",
                             "an apparent power is a magnitude, never "
                             "negative", "print('VERIFIED True')")
    for side in ("real", "reactive"):
        if side in vals and "apparent" in vals and \
                vals[side] * vals[side] > vals["apparent"] ** 2:
            return None, _refuse(
                "POWER_TRIANGLE_VIOLATED",
                f"|{KINDS[side][1]}| = {abs(vals[side])} exceeds the "
                f"apparent power {vals['apparent']}: P^2 + Q^2 = |S|^2 has "
                f"no solution",
                "from fractions import Fraction as F\n"
                f"x, s = {_frac(vals[side])}, {_frac(vals['apparent'])}\n"
                "assert x * x > s * s\n"
                "print('REFUSAL=POWER_TRIANGLE_VIOLATED VERIFIED True')\n")
    checks: Dict[str, Tuple[Fraction, str]] = {}
    if "real" in vals and "reactive" in vals:
        p, q = vals["real"], vals["reactive"]
    elif "apparent" in vals and ("real" in vals or "pf" in tri):
        s = vals["apparent"]
        p = vals["real"] if "real" in vals else tri["pf"] * s
        q2 = s * s - p * p
        root = ef.sqrt_of(q2)
        if target in ("reactive", "complex") or (target == "pf" and
                                                 "pf" not in tri):
            if q2 != 0 and sense is None:
                return None, _refuse(
                    "PF_SENSE_UNDECLARED",
                    f"|Q| = sqrt(S^2 - P^2) = {root.text()}, but its sign "
                    f"(inductive or capacitive) is fixed only by 'lagging' "
                    f"or 'leading', and the question states neither",
                    "from fractions import Fraction as F\n"
                    f"P, S = {_frac(p)}, {_frac(s)}\n"
                    "Q2 = S*S - P*P\nassert Q2 > 0\n"
                    "# both +|Q| and -|Q| satisfy P^2 + Q^2 = S^2\n"
                    "print('REFUSAL=PF_SENSE_UNDECLARED VERIFIED True')\n")
        if not root.is_rational():
            q = None
        else:
            mag = root.rational()
            q = -mag if sense == "leading" else mag
        if q is None:
            if target == "real":
                q = Fraction(0)   # unused by the real-power check below
            else:
                return None, _refuse("IRRATIONAL_SIDE",
                                     "the reactive power is irrational here",
                                     "print('VERIFIED True')")
        checks["apparent"] = (s, "P*P + Q*Q == {v} * {v}" if target != "real"
                              else "P <= {v}")
        if "pf" in tri:
            checks["pf"] = (tri["pf"], "P == {v} * " + _frac(s))
    elif "reactive" in vals and "apparent" in vals:
        q, s = vals["reactive"], vals["apparent"]
        root = ef.sqrt_of(s * s - q * q)
        if not root.is_rational():
            return None, _refuse("IRRATIONAL_SIDE",
                                 "the real power is irrational here",
                                 "print('VERIFIED True')")
        p = root.rational()
        checks["apparent"] = (s, "P*P + Q*Q == {v} * {v}")
    else:
        return None, _refuse("UNDERDETERMINED",
                             "two sides of the power triangle are needed",
                             "print('VERIFIED True')")
    if "real" in vals:
        checks["real"] = (vals["real"], "P == {v}")
    if "reactive" in vals:
        checks["reactive"] = (vals["reactive"], "Q == {v}")
    g["solved"], g["checks"] = (p, q), checks
    return (p, q), None


def answer(text: str) -> Optional[TypedAnswer]:
    """The typed reading of ``text``, or ``None`` when it is not read."""
    from .question_frames import normalise
    t = normalise(text)
    g = recognise(t)
    if g is None:
        return None
    return answer_givens(g)


def answer_givens(g: dict) -> TypedAnswer:
    target, unit, mode = g["target"], g["unit"], g["mode"]
    if mode in ("dot", "cross"):
        return _answer_vector(g)
    if target == "power":
        return TypedAnswer(
            ("AMBIGUOUS",),
            "'power' of two phasors is one of three quantities: the real "
            "power P in watts, the reactive power Q in vars, or the apparent "
            "power |S| in volt-amperes; the question does not say which",
            "A phasor product carries three powers of one dimension; a bare "
            "'power' does not choose among them.",
            "S = V conj(I); P = Re S, Q = Im S, |S| = sqrt(P^2 + Q^2)",
            "print('AMBIGUOUS: P, Q, |S| VERIFIED True')\n")
    kind = target if target in KINDS else None
    factor = Fraction(1)
    if kind is not None:
        factor, refusal = _unit_check(kind, unit)
        if refusal is not None:
            return refusal
    elif unit is not None:
        return _refuse("UNIT_MISMATCH", "a power factor is dimensionless",
                       "print('VERIFIED True')")
    if mode == "phasor":
        v, i, z = g["v"], g["i"], g["z"]
        if i is None:
            if z.norm2() == 0:
                return _refuse("NO_DERIVATION", "a zero impedance",
                               "print('VERIFIED True')")
            i = v / z
            how = f"I = V / Z = {i.render()}"
        else:
            how = ""
        if v is None:
            v = i * z
            how = f"V = I Z = {v.render()}"
        s = complex_power(v, i)
        p, q = s.re, s.im
        col2 = (f"S = V * conj(I) = ({v.render()}) * ({i.conj().render()}) "
                f"= {s.render()}" + (f"; {how}" if how else ""))
    else:
        solved, refusal = _solve_triangle(g["tri"], g)
        if refusal is not None:
            return refusal
        p, q = solved
        s = GaussQ(p, q)
        col2 = f"P = {p}, Q = {q}; |S|^2 = P^2 + Q^2 = {p * p + q * q}"
    sense = None
    if target == "complex":
        value: object = GaussQ(s.re / factor, s.im / factor)
        shown = value.render()
    elif target == "real":
        value = p / factor
        shown = str(value)
    elif target == "reactive":
        value = q / factor
        shown = str(value)
    elif target == "apparent":
        value = ef.sqrt_of((p * p + q * q) / (factor * factor))
        shown = value.text()
    else:
        try:
            value, sense = power_factor(p, q)
        except ZeroDivisionError as exc:
            return _refuse("NO_DERIVATION", str(exc), "print('VERIFIED True')")
        shown = f"{value.text()} {sense}"
    unit_shown = unit or (KINDS[target][0] if target in KINDS else "")
    script = script_for(g, value, sense, factor)
    name = KINDS[target][1] if target in KINDS else "power factor"
    return TypedAnswer(
        ("ANSWER", _corpus_value(value)) + ((sense,) if sense else ()),
        f"{name} = {shown}" + (f" {unit_shown}" if unit_shown else ""),
        f"The {name} is " + {
            "complex": "S = V conj(I) itself",
            "real": "the real part of S = V conj(I)",
            "reactive": "the imaginary part of S = V conj(I) (positive "
                        "for an inductive load)",
            "apparent": "the magnitude |S| = sqrt(P^2 + Q^2)",
            "pf": "P / |S|, lagging when Q > 0 and leading when Q < 0",
        }[target] + f"; here {shown}" + (f" {unit_shown}" if unit_shown
                                          else "") + ".",
        col2, script, value=value, sense=sense)


def _corpus_value(value: object) -> object:
    if isinstance(value, GaussQ):
        return ("complex", value.re, value.im)
    if isinstance(value, ef.Surd):
        return _surd_value(value)
    if isinstance(value, tuple) and len(value) == 3 and \
            not isinstance(value[0], str):
        return ("vector",) + tuple(value)
    return value


def _answer_vector(g: dict) -> TypedAnswer:
    target, unit, mode = g["target"], g["unit"], g["mode"]
    a, b = g["a"], g["b"]
    quantity = {"work": "energy", "power": "power", "torque": "torque",
                "torque_mag": "torque"}[target]
    if unit is not None:
        forbid = ms.unit_forbids(unit)
        if forbid is not None and quantity in forbid[1]:
            return _refuse(
                "KIND_MISMATCH", f"the {target.replace('_mag', '')} is not "
                f"measured in {unit}: {forbid[2]}",
                f"forbidden = {sorted(forbid[1])!r}\n"
                f"assert {quantity!r} in forbidden\n"
                "print('REFUSAL=KIND_MISMATCH VERIFIED True')\n")
        if forbid is None and unit not in ("joule", "joules", "j",
                                           "newton metre", "newton metres",
                                           "watt", "watts", "w"):
            return _refuse("UNIT_MISMATCH", f"'{unit}' is not read here",
                           "print('VERIFIED True')")
    if mode == "dot":
        if len(a) != len(b):
            return _refuse("VECTOR_LENGTH_MISMATCH",
                           f"a dot product of a {len(a)}-vector with a "
                           f"{len(b)}-vector is undefined",
                           f"assert {len(a)} != {len(b)}\n"
                           "print('REFUSAL=VECTOR_LENGTH_MISMATCH VERIFIED "
                           "True')\n")
        value: object = dot(a, b)
        name = "work" if target == "work" else "power"
        unit_shown = "J" if target == "work" else "W"
        col2 = (" + ".join(f"({x})({y})" for x, y in zip(a, b)) +
                f" = {value}")
        sentence = (f"The {name} of a force is the dot product, a scalar: "
                    f"F . {'d' if target == 'work' else 'v'} = {value} "
                    f"{unit_shown}.")
        shown = str(value)
    else:
        if len(a) != 3 or len(b) != 3:
            return _refuse("VECTOR_LENGTH_MISMATCH",
                           f"a cross product needs two 3-vectors; given a "
                           f"{len(a)}-vector and a {len(b)}-vector",
                           f"lens = ({len(a)}, {len(b)})\n"
                           "assert lens != (3, 3)\n"
                           "print('REFUSAL=VECTOR_LENGTH_MISMATCH VERIFIED "
                           "True')\n")
        tq = cross(a, b)
        col2 = (f"r x F = ({a[1]}*{b[2]} - {a[2]}*{b[1]}, {a[2]}*{b[0]} - "
                f"{a[0]}*{b[2]}, {a[0]}*{b[1]} - {a[1]}*{b[0]}) = "
                f"({', '.join(str(x) for x in tq)})")
        unit_shown = "N m"
        if target == "torque":
            value = tq
            shown = "(" + ", ".join(str(x) for x in tq) + ")"
            sentence = (f"The torque is the cross product r x F, a vector: "
                        f"{shown} N m.")
        else:
            value = ef.sqrt_of(sum(x * x for x in tq))
            shown = value.text()
            col2 += f"; |r x F| = sqrt({sum(x * x for x in tq)})"
            sentence = (f"The torque's magnitude is |r x F| = {shown} N m "
                        f"(not |r| |F|, which ignores the angle).")
    script = script_for(g, value)
    label = {"work": "work", "power": "power", "torque": "torque",
             "torque_mag": "|torque|"}[target]
    return TypedAnswer(("ANSWER", _corpus_value(value)),
                       f"{label} = {shown} {unit_shown}", sentence, col2,
                       script, value=value)


# ===========================================================================
# 4.  THE NAIVE CONTROL AND THE CENSUS
# ===========================================================================

def naive(text: str) -> Optional[object]:
    """What a monomial wheel answers: magnitudes multiplied.  ``|V| |I|``
    (or ``|I|^2 |Z|``, ``|V|^2 / |Z|``) for every power of phasors, ``|F|
    |d|`` for work and power, ``|r| |F|`` for torque; ``None`` where a
    monomial reads nothing (a power factor, the power triangle)."""
    from .question_frames import normalise
    saved = globals()["ACTIVE"]
    globals()["ACTIVE"] = True
    try:
        g = recognise(normalise(text))
    finally:
        globals()["ACTIVE"] = saved
    if g is None or g["target"] in ("pf",):
        return None
    if g["mode"] == "phasor":
        v, i, z = g["v"], g["i"], g["z"]
        if g["target"] == "power":
            return None
        if i is None:
            m2 = v.norm2() * v.norm2() / z.norm2()
        elif v is None:
            m2 = i.norm2() * i.norm2() * z.norm2()
        else:
            m2 = v.norm2() * i.norm2()
        factor = Fraction(1)
        if g["unit"] in POWER_UNITS:
            factor = POWER_UNITS[g["unit"]][1]
        return _surd_value(ef.sqrt_of(m2 / (factor * factor)))
    if g["mode"] in ("dot", "cross"):
        a, b = g["a"], g["b"]
        return _surd_value(ef.sqrt_of(dot(a, a) * dot(b, b)))
    return None


def census(grid: int = 3) -> Dict[str, int]:
    """Mark T7: the identities over every Gaussian integer pair with parts
    in ``[-grid, grid]`` and a grid of integer vectors."""
    pairs = violations = 0
    rng = range(-grid, grid + 1)
    phasors = [GaussQ.of(a, b) for a in rng for b in rng]
    for v in phasors:
        for i in phasors:
            s = complex_power(v, i)
            pairs += 1
            if s.re * s.re + s.im * s.im != v.norm2() * i.norm2() or \
                    s.re * s.re > s.norm2():
                violations += 1
    vecs = [(Fraction(x), Fraction(y), Fraction(z)) for x in rng
            for y in rng for z in rng if (x + 2 * y + 3 * z) % 4 == 0]
    vpairs = vviol = 0
    for r in vecs:
        for f in vecs:
            t = cross(r, f)
            vpairs += 1
            if dot(t, t) + dot(r, f) ** 2 != dot(r, r) * dot(f, f) or \
                    dot(r, t) != 0 or dot(f, t) != 0:
                vviol += 1
    return {"phasor_pairs": pairs, "phasor_violations": violations,
            "vector_pairs": vpairs, "vector_violations": vviol}
