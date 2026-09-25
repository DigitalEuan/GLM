"""``glm_universal.engineering.speak`` -- asking the GLM in engineering terms.

The surface
-----------
Seven frames read an engineering question into one of the exact operations
of this package, and each either answers with the working shown or refuses
with the reason:

``derive``      *derive power from voltage and resistance* -- a wheel spoke,
                solved from the declared axioms, with its certificate;
``wheel``       *complete the formula wheel for power* -- every spoke, per
                wheel, labelled;
``check``       *is torque = moment_of_inertia * angular_velocity
                dimensionally consistent?* -- read at SI7 and at EXT10 from
                the register, both layers named when they disagree;
``smith``       reflection coefficient, VSWR, reflected power, normalised
                impedance, the inverse map and passivity, after the load and
                the reference are checked to share a dimension;
``analogy``     the counterpart of a quantity, or a whole formula translated,
                under a *named* analogy -- unnamed and disagreeing is refused;
``resonance``   resonant angular frequency, quality factor and damping ratio
                from component values, derived in the component's own wheel
                and again through the force-voltage analogy in the other
                wheel -- two routes, answered only when they agree;
``delta-sigma`` bits, averages and periods of the first-order loop, and
                whether an input's bitstream is periodic, by theorem.

A question no frame reads is not answered here: :func:`ask_engineering`
hands it to :meth:`GeometricSession.ask_planned` unchanged, so this surface
only ever adds to what the machine already answers.

Every answer carries the faculty it exercised (directive D15): ``derive``
for a computation no register holds, ``address`` for a counterpart read off
a declared dictionary.  Exact and float-free.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import isqrt
from typing import Dict, List, Mapping, Optional, Tuple

from . import analogy as an
from . import delta_sigma as ds
from . import smith as sm
from . import wheels as wh

__all__ = ["EngAnswer", "Refusal", "FRAMES", "answer", "ask_engineering",
           "UNIT_QUANTITY"]


class Refusal(ValueError):
    """A frame read the question and declines to answer it, with a reason."""


@dataclass(frozen=True)
class EngAnswer:
    """What a frame gave."""

    frame: str
    text: str
    faculty: str
    working: Tuple[str, ...] = ()
    values: Mapping[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# shared reading helpers
# ---------------------------------------------------------------------------

_NUM = r"-?\d+(?:\.\d+)?(?:/\d+)?"


def _clean(text: str) -> str:
    t = text.strip().lower().rstrip("?.! ")
    return re.sub(r"\s+", " ", t)


def _name(words: str) -> str:
    w = re.sub(r"^(?:the|a|an)\s+", "", words.strip())
    return re.sub(r"\s+", "_", w)


def _frac(text: str) -> Fraction:
    return Fraction(text.replace(" ", ""))


def _root(value: Fraction, d: int) -> Tuple[Optional[Fraction], str]:
    """The exact ``d``-th root of ``value`` when rational, else a radical."""
    if d == 1:
        return value, f"{value}"
    if value >= 0:
        num, den = value.numerator, value.denominator
        a = _iroot(num, d)
        b = _iroot(den, d)
        if a is not None and b is not None:
            r = Fraction(a, b)
            return r, f"{r}"
    return None, f"({value})^(1/{d})"


def _iroot(n: int, d: int) -> Optional[int]:
    """The exact integer ``d``-th root of ``n >= 0``, or ``None``."""
    if d == 2:
        r = isqrt(n)
        return r if r * r == n else None
    lo, hi = 0, n + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if mid ** d < n:
            lo = mid + 1
        else:
            hi = mid
    return lo if lo ** d == n else None


# ---------------------------------------------------------------------------
# frame: derive
# ---------------------------------------------------------------------------

_DERIVE = [
    re.compile(r"^derive (.+?) from (.+?) and (.+)$"),
    re.compile(r"^express (.+?) in terms of (.+?) and (.+)$"),
    re.compile(r"^how is (.+?) given by (.+?) and (.+)$"),
]


def frame_derive(t: str) -> Optional[EngAnswer]:
    for pat in _DERIVE:
        m = pat.match(t)
        if m:
            break
    else:
        return None
    target, y, z = (_name(g) for g in m.groups())
    found: Dict[str, List[wh.Spoke]] = {}
    for w in wh.WHEELS:
        qs = wh.wheel_quantities(w)
        if target in qs and y in qs and z in qs:
            s = wh.derive_from(target, (y, z), w.axioms, w.id)
            if s is not None:
                found.setdefault(s.formula, []).append(s)
    if not found:
        raise Refusal(f"no declared wheel derives {target} from {y} and {z} "
                      f"alone; the axioms leave another quantity in, or no "
                      f"wheel names all three")
    if len(found) > 1:
        raise Refusal("ambiguous: the wheels disagree -- " + "; ".join(
            f"{target} = {f} ({', '.join(s.wheel for s in ss)})"
            for f, ss in found.items()))
    formula, spokes = next(iter(found.items()))
    s = spokes[0]
    wheels = ", ".join(f"{x.wheel} {wh.wheel_named(x.wheel).title}"
                       for x in spokes)
    return EngAnswer(
        "derive", f"{target} = {formula}  [derived in {wheels}; "
                  f"certificate: {s.certificate.render()}]", "derive",
        (f"axioms of {s.wheel}: " + "; ".join(wh.wheel_named(
            s.wheel).axioms), f"combination: {s.certificate.render()}"),
        {"formula": formula})


# ---------------------------------------------------------------------------
# frame: wheel
# ---------------------------------------------------------------------------

def frame_wheel(t: str) -> Optional[EngAnswer]:
    m = re.match(r"^(?:complete|generate|give) the (?:formula )?wheel for "
                 r"(.+)$", t)
    if not m:
        return None
    target = _name(m.group(1))
    parts = []
    for w in wh.WHEELS:
        if target in wh.wheel_quantities(w):
            spokes = wh.wheel_spokes(w, target)
            if spokes:
                parts.append(f"{w.id} ({w.title}): " + "; ".join(
                    s.text() for s in spokes))
    if not parts:
        raise Refusal(f"no declared wheel has {target} as a spoke")
    return EngAnswer("wheel", " | ".join(parts), "derive", tuple(parts))


# ---------------------------------------------------------------------------
# frame: dimensional check
# ---------------------------------------------------------------------------

def frame_check(t: str) -> Optional[EngAnswer]:
    m = re.match(r"^(?:is|does) (.+?=.+?) (?:dimensionally consistent|have "
                 r"consistent dimensions|dimensionally homogeneous)$", t)
    if not m:
        return None
    eq = m.group(1).strip()
    try:
        verdicts = {layer: wh.consistency(eq, layer)
                    for layer in ("si7", "ext10")}
    except ValueError as exc:
        raise Refusal(f"not an equation of named quantities: {exc}")
    if any(v is None for v in verdicts.values()):
        raise Refusal("some quantity in the equation is not in the "
                      "register, so no layer can read it")
    si, ext = verdicts["si7"], verdicts["ext10"]

    def say(v, layer):
        if v["consistent"]:
            return f"consistent at {layer.upper()}"
        res = ", ".join(f"{k}^{x}" for k, x in v["residual"].items())
        return f"inconsistent at {layer.upper()} (residual {res})"

    if si["consistent"] == ext["consistent"]:
        word = "consistent" if si["consistent"] else "inconsistent"
        detail = "" if si["consistent"] else " -- " + say(ext, "ext10")
        text = (f"{eq} is dimensionally {word} at both SI7 and "
                f"EXT10{detail}.  Consistency is necessary for a law, not "
                f"sufficient.")
    else:
        text = (f"{eq}: {say(si, 'si7')}, {say(ext, 'ext10')} -- the "
                f"verdict depends on the layer (SI treats plane angle as "
                f"dimensionless; EXT10 keeps it).")
    return EngAnswer("check", text, "derive")


# ---------------------------------------------------------------------------
# frame: Smith chart
# ---------------------------------------------------------------------------

#: Unit words the RF frames ground, and the quantity each measures.
UNIT_QUANTITY: Dict[str, str] = {
    "ohm": "resistance", "ohms": "resistance", "farad": "capacitance",
    "farads": "capacitance", "henry": "inductance", "henries": "inductance",
    "siemens": "conductance", "volt": "voltage", "volts": "voltage",
    "amp": "current", "amps": "current", "watt": "power", "watts": "power",
}

_CPLX = rf"({_NUM}(?:\s*[+-]\s*(?:\d+(?:\.\d+)?(?:/\d+)?)?\s*j)?|{_NUM}?j)"


def _parse_complex(text: str) -> sm.GaussQ:
    s = text.replace(" ", "")
    m = re.fullmatch(rf"({_NUM})?(?:([+-])(\d+(?:\.\d+)?(?:/\d+)?)?j)?", s)
    if m and s.endswith("j") and m.group(2) is None:
        m = None
    if m:
        re_part = _frac(m.group(1)) if m.group(1) else Fraction(0)
        im = Fraction(0)
        if m.group(2):
            mag = _frac(m.group(3)) if m.group(3) else Fraction(1)
            im = mag if m.group(2) == "+" else -mag
        return sm.GaussQ(re_part, im)
    m = re.fullmatch(rf"({_NUM})?j", s)
    if m:
        return sm.GaussQ(Fraction(0), _frac(m.group(1)) if m.group(1)
                         else Fraction(1))
    raise Refusal(f"cannot read {text!r} as a complex number")


def _same_dimension(q1: str, q2: str) -> bool:
    return wh.dimension(q1, "si7") == wh.dimension(q2, "si7")


def _reference(t: str) -> Optional[Fraction]:
    m = re.search(rf"(?:on|with) an? ({_NUM}) (\w+) (?:line|reference|"
                  rf"system)", t)
    if not m:
        return None
    unit = m.group(2)
    if unit not in UNIT_QUANTITY:
        raise Refusal(f"the reference unit {unit!r} is not one the RF frame "
                      f"grounds")
    if not _same_dimension(UNIT_QUANTITY[unit], "impedance"):
        raise Refusal(f"a {unit} reference measures {UNIT_QUANTITY[unit]}, "
                      f"not impedance: Z and Z0 must share a dimension before "
                      f"z = Z/Z0 means anything")
    z0 = _frac(m.group(1))
    if z0 <= 0:
        raise Refusal("the reference impedance must be positive; a zero or "
                      "negative Z0 normalises nothing")
    return z0


def _load(t: str) -> Optional[sm.GaussQ]:
    if "short circuit" in t:
        return sm.GaussQ.of(0)
    m = re.search(rf"{_CPLX} (\w+) load", t)
    if not m:
        return None
    unit = m.group(2)
    if unit not in UNIT_QUANTITY:
        raise Refusal(f"the load unit {unit!r} is not one the RF frame "
                      f"grounds")
    if not _same_dimension(UNIT_QUANTITY[unit], "impedance"):
        raise Refusal(f"a {unit} load measures {UNIT_QUANTITY[unit]}, not "
                      f"impedance")
    return _parse_complex(m.group(1))


def frame_smith(t: str) -> Optional[EngAnswer]:
    m = re.match(rf"^is a load with reflection coefficient {_CPLX} passive$",
                 t)
    if m:
        g = _parse_complex(m.group(1))
        n2 = g.norm2()
        if n2 <= 1:
            edge = " (lossless: on the unit circle)" if n2 == 1 else ""
            text = f"passive{edge}: |Gamma|^2 = {n2} <= 1"
        else:
            text = (f"not passive (active): |Gamma|^2 = {n2} > 1, so the "
                    f"load returns more power than it receives")
        return EngAnswer("smith", text, "derive")
    m = re.match(rf"^what load impedance gives a reflection coefficient of "
                 rf"{_CPLX} (.+)$", t)
    if m:
        g = _parse_complex(m.group(1))
        z0 = _reference(m.group(2))
        if z0 is None:
            return None
        try:
            z = sm.z_of(g)
        except ZeroDivisionError as exc:
            raise Refusal(str(exc))
        big = sm.GaussQ(z.re * z0, z.im * z0)
        return EngAnswer("smith", f"Z = {big.render()} ohm (z = "
                                  f"{z.render()} = (1 + Gamma)/(1 - Gamma), "
                                  f"times Z0 = {z0})", "derive")
    asks = [("vswr", ("vswr", "standing wave ratio")),
            ("power", ("fraction of power", "reflected power")),
            ("z", ("normalized impedance", "normalised impedance")),
            ("gamma", ("reflection coefficient", "gamma"))]
    what = next((k for k, words in asks if any(w in t for w in words)),
                None)
    if what is None:
        return None
    load = _load(t)
    z0 = _reference(t)
    if load is None or z0 is None:
        return None
    z = sm.normalise(load, z0)
    if what == "z":
        return EngAnswer("smith", f"z = Z/Z0 = {z.render()}", "derive")
    try:
        g = sm.gamma_of(z)
    except ZeroDivisionError as exc:
        raise Refusal(f"{exc}: the load {load.render()} ohm on {z0} ohm has "
                      f"no finite reflection coefficient")
    base = f"z = {z.render()}, Gamma = (z - 1)/(z + 1) = {g.render()}"
    if what == "gamma":
        return EngAnswer("smith", f"Gamma = {g.render()}  ({base})",
                         "derive")
    if what == "power":
        return EngAnswer("smith", f"reflected fraction |Gamma|^2 = "
                                  f"{sm.reflected_power(g)}  ({base})",
                         "derive")
    try:
        _, shown = sm.vswr(g)
    except ValueError as exc:
        raise Refusal(str(exc))
    return EngAnswer("smith", f"vswr = {shown}  ({base}, VSWR = "
                              f"(1 + |Gamma|)/(1 - |Gamma|))", "derive")


# ---------------------------------------------------------------------------
# frame: analogy
# ---------------------------------------------------------------------------

def _named_analogy(t: str) -> Optional[an.Analogy]:
    for a in an.ANALOGIES:
        if any(alias in t for alias in a.aliases):
            return a
    return None


def frame_analogy(t: str) -> Optional[EngAnswer]:
    m = re.match(r"^translate (.+?=.+?) into (mechanics|mechanical|"
                 r"electrical|circuits?)(?: terms)?(?: under the (.+))?$", t)
    if m:
        eq, dom, which = m.group(1), m.group(2), m.group(3) or ""
        a = _named_analogy(which)
        if a is None:
            raise Refusal("name the analogy (force-voltage or force-current): "
                          "the two translate differently")
        direction = ("to_mechanical" if dom.startswith("mechanic")
                     else "to_electrical")
        out = an.translate_equation(eq, a, direction)
        if out is None:
            raise Refusal(f"some quantity in {eq!r} has no counterpart in "
                          f"the {a.name} analogy")
        src, dst = ((an.ELECTRICAL_AXIOMS, an.MECHANICAL_AXIOMS)
                    if direction == "to_mechanical"
                    else (an.MECHANICAL_AXIOMS, an.ELECTRICAL_AXIOMS))
        note = ""
        try:
            if wh.is_derivable(eq, src):
                note = ("; the source follows from its wheel and the "
                        "translation follows from the target wheel: "
                        f"{wh.is_derivable(out, dst)}")
        except ValueError:
            pass
        return EngAnswer("analogy", f"{out}  (the {a.name} analogy{note})",
                         "derive")
    m = (re.match(r"^(?:in the (.+?) analogy, )?what is the (mechanical|"
                  r"electrical) analog(?:ue)? of (.+?)(?: in the (.+?) "
                  r"analogy)?$", t)
         or re.match(r"^which (mechanical|electrical) quantity corresponds to "
                     r"(.+?) in the (.+?) analogy$", t))
    if not m:
        return None
    g = m.groups()
    if len(g) == 4:
        which = (g[0] or "") + " " + (g[3] or "")
        side, name = g[1], _name(g[2])
    else:
        side, name, which = g[0], _name(g[1]), g[2]
    direction = "to_mechanical" if side == "mechanical" else "to_electrical"
    named = _named_analogy(which)
    pool = (named,) if named else an.ANALOGIES
    images = {a.name: an.counterpart(name, a, direction) for a in pool}
    if all(v is None for v in images.values()):
        raise Refusal(f"{name} is outside the declared correspondence of "
                      f"{'the ' + named.name if named else 'either'} analogy")
    if len(set(images.values())) > 1:
        raise Refusal("ambiguous: the analogies disagree -- " + "; ".join(
            f"{k}: {v}" for k, v in images.items()) + ".  Name one.")
    image = next(iter(images.values()))
    label = named.name if named else "both analogies"
    return EngAnswer("analogy", f"{image}  ({side} counterpart of {name} "
                                f"under {label})", "address")


# ---------------------------------------------------------------------------
# frame: resonance, quality factor, damping ratio
# ---------------------------------------------------------------------------

_COMPONENT_UNITS = [
    (r"n\s*s/m", "damping_coefficient"), (r"n/m", "spring_constant"),
    (r"kg", "mass"), (r"henry|henries|h\b", "inductance"),
    (r"farad|farads|f\b", "capacitance"), (r"ohms?", "resistance"),
]


def _components(t: str) -> Dict[str, Fraction]:
    out: Dict[str, Fraction] = {}
    for pattern, qty in _COMPONENT_UNITS:
        for m in re.finditer(rf"({_NUM})\s*(?:{pattern})", t):
            if qty in out:
                raise Refusal(f"two values given for {qty}")
            out[qty] = _frac(m.group(1))
            t = t[:m.start()] + " " * (m.end() - m.start()) + t[m.end():]
    return out


def frame_resonance(t: str) -> Optional[EngAnswer]:
    targets = [("angular_frequency", ("resonant angular frequency",
                                      "natural angular frequency",
                                      "resonant frequency")),
               ("quality_factor", ("quality factor",)),
               ("damping_ratio", ("damping ratio",))]
    target = next((q for q, words in targets if any(w in t for w in words)),
                  None)
    if target is None:
        return None
    vals = _components(t)
    if not vals:
        return None
    mech = {"mass", "spring_constant", "damping_coefficient"}
    elec = {"inductance", "capacitance", "resistance"}
    if set(vals) <= mech:
        home, away = an.MECHANICAL_AXIOMS, an.ELECTRICAL_AXIOMS
        direction = "to_electrical"
    elif set(vals) <= elec:
        home, away = an.ELECTRICAL_AXIOMS, an.MECHANICAL_AXIOMS
        direction = "to_mechanical"
    else:
        raise Refusal("mixed mechanical and electrical components: say which "
                      "system they belong to")
    if any(v <= 0 for v in vals.values()):
        raise Refusal("component values must be positive")
    inputs = tuple(sorted(vals))
    s1 = wh.derive_from(target, inputs, home)
    if s1 is None:
        raise Refusal(f"the given components do not determine {target}")
    v1, d1 = s1.evaluate(vals)
    # the second route: carry the components across the force-voltage
    # analogy, derive in the other wheel, evaluate there
    table = (an.FORCE_VOLTAGE.forward() if direction == "to_electrical"
             else an.FORCE_VOLTAGE.backward())
    moved: Dict[str, Fraction] = {}
    for q, v in vals.items():
        image, k = table[q]
        moved[image] = v if k == 1 else 1 / v
    s2 = wh.derive_from(target, tuple(sorted(moved)), away)
    if s2 is None:
        raise Refusal("the second route (through the force-voltage analogy) "
                      "does not determine the answer; not licensed")
    v2, d2 = s2.evaluate(moved)
    if (v1, d1) != (v2, d2):
        raise Refusal(f"the two routes disagree ({v1}^(1/{d1}) vs "
                      f"{v2}^(1/{d2})); not licensed")
    _, shown = _root(v1, d1)
    unit = {"angular_frequency": " rad/s"}.get(target, "")
    sym = {"angular_frequency": "omega0", "quality_factor": "q",
           "damping_ratio": "zeta"}[target]
    return EngAnswer(
        "resonance", f"{sym} = {shown}{unit}  [{s1.text()} in the home "
                     f"wheel; {s2.text()} after the force-voltage "
                     f"translation; both routes agree]", "derive",
        (s1.certificate.render(), s2.certificate.render()),
        {"value": shown})


# ---------------------------------------------------------------------------
# frame: delta-sigma
# ---------------------------------------------------------------------------

def _dc(text: str) -> Fraction:
    try:
        return _frac(text)
    except (ValueError, ZeroDivisionError):
        raise Refusal(f"cannot read {text!r} as an exact input")


def frame_delta_sigma(t: str) -> Optional[EngAnswer]:
    if "delta-sigma" not in t and "delta sigma" not in t:
        return None
    m = re.search(rf"(?:bits|bitstream) of (?:a first-order delta-sigma "
                  rf"modulator for )?({_NUM}),? (?:over )?(\d+) steps", t)
    if m:
        x, n = _dc(m.group(1)), int(m.group(2))
        if not 0 <= x < 1:
            raise Refusal("the one-bit loop is declared on [0, 1)")
        bits = "".join(str(b) for b in ds.first_order_bits(x, n))
        return EngAnswer("delta-sigma", f"bits = {bits}  (bit n = "
                                        f"floor((n+1)t) - floor(nt), t = {x})",
                         "derive")
    m = re.search(rf"period of dc input ({_NUM})", t)
    if m:
        x = _dc(m.group(1))
        try:
            p = ds.rational_period(x)
        except ValueError as exc:
            raise Refusal(str(exc))
        return EngAnswer("delta-sigma", f"period {p}  (t = {x} in lowest "
                                        f"terms has denominator {p}; the "
                                        f"state is n*t mod 1)", "derive")
    m = re.search(rf"average of ({_NUM}) after (\d+) steps", t)
    if m:
        x, n = _dc(m.group(1)), int(m.group(2))
        if not 0 <= x < 1 or n <= 0:
            raise Refusal("the one-bit loop is declared on [0, 1), N > 0")
        avg = ds.delta_sigma_average(x, n)
        return EngAnswer("delta-sigma", f"average = {avg}  (floor(N t)/N "
                                        f"with N = {n}; within 1/N of t)",
                         "derive")
    m = re.search(r"bitstream of (.+?) periodic", t)
    if m:
        expr = m.group(1).replace(" ", "")
        q = re.fullmatch(r"sqrt\((\d+)\)-(\d+)", expr)
        if q:
            n, k = int(q.group(1)), int(q.group(2))
            r = isqrt(n)
            if r * r == n:
                raise Refusal("that input is rational; ask for its period")
            if not (k * k < n < (k + 1) * (k + 1)):
                raise Refusal("the input is not in [0, 1)")
            return EngAnswer("delta-sigma", f"never periodic: sqrt({n}) - "
                                            f"{k} is irrational, and an "
                                            f"irrational input gives a "
                                            f"bitstream that is never "
                                            f"periodic (proved)", "derive")
        try:
            x = _frac(expr)
        except (ValueError, ZeroDivisionError):
            raise Refusal("only rational inputs and sqrt(n) - k are decided")
        if not 0 <= x < 1:
            raise Refusal("the one-bit loop is declared on [0, 1)")
        return EngAnswer("delta-sigma", f"periodic with period "
                                        f"{x.denominator}", "derive")
    return None


FRAMES = (("derive", frame_derive), ("wheel", frame_wheel),
          ("check", frame_check), ("smith", frame_smith),
          ("analogy", frame_analogy), ("resonance", frame_resonance),
          ("delta-sigma", frame_delta_sigma))


def answer(text: str) -> Tuple[str, Optional[EngAnswer], str]:
    """``(verdict, answer, reason)``: verdict is ``answered``, ``refused``
    (a frame read it and declined) or ``unread`` (no frame read it)."""
    t = _clean(text)
    for _, frame in FRAMES:
        try:
            got = frame(t)
        except Refusal as exc:
            return "refused", None, str(exc)
        except (ValueError, ZeroDivisionError, KeyError) as exc:
            return "refused", None, f"could not be computed: {exc}"
        if got is not None:
            return "answered", got, ""
    return "unread", None, ""


def ask_engineering(session, text: str):
    """Answer ``text`` through the engineering frames, or hand it on.

    Returns a :class:`glm_universal.runtime.solution.Solution`.  An
    unread question is answered exactly as
    :meth:`GeometricSession.ask_planned` answers it.
    """
    from ..runtime.parser import Query
    from ..runtime.solution import Solution, Step
    verdict, got, reason = answer(text)
    if verdict == "unread":
        return session.ask_planned(text)
    # The grammar is not consulted for a question a frame has read: its
    # parser rejects some engineering phrasings ("derive X from Y and Z")
    # as malformed, and the frame has already decided what was asked.
    query = Query(raw=text, normalised=_clean(text), kind="unknown",
                  rule="engineering", trace=(f"engineering frame: "
                                             f"{got.frame if got else 'refused'}",))
    if verdict == "refused":
        return Solution(query=query, kind="engineering",
                        answer=f"refused: {reason}", ok=False, error=reason,
                        steps=(Step("refuse", reason, "refused"),),
                        payload={"engineering": "refused"})
    steps = tuple(Step(got.frame, w, w) for w in got.working) or (
        Step(got.frame, got.text, got.text),)
    return Solution(query=query, kind=f"engineering-{got.frame}",
                    answer=got.text, steps=steps,
                    expected={"faculty": got.faculty, **dict(got.values)},
                    payload={"engineering": got.frame,
                             "faculty": got.faculty}, ok=True)
