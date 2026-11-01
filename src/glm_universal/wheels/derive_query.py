"""``glm_universal.wheels.derive_query`` -- *is emf = magnetic_field * area /
time a law?*: the derivability engine of the formula wheels on the answering
path.

*Created 1 November 2026 (Phase 186: intake absorption).*

:func:`derive_text` takes an equation between named physical quantities (a
monomial on each side: names, integer literals, ``*``, ``/`` and integer or
rational powers written ``^`` or ``**``), optionally followed by ``in W16`` /
``wheel W16`` / ``in wheel W16`` to put it to one wheel, and answers through
:func:`glm_universal.wheels.answer_derivability` -- the fifteen registry
wheels first (integer engine), then the fifteen cent wheels W16-W25, W28,
W29, W32-W34 (rational-power engine), one wheel at a time (their axioms are
never pooled: ``studies/CENT_WHEELS_STUDY.md`` §8 shows the naive union of all
axioms licensing not-a-laws by conflating quantities of different wheels).

It returns the toolbox's ``(ok, text, figures)``:

* **derivable** (``ok`` true) -- the wheel that derives it and the explicit
  rational combination of that wheel's axioms whose relation (the exponents,
  left minus right, and the coefficient's prime exponents) is the equation's:
  the engine's certificate, re-checked here exactly before it is said;
* **not derivable** (``ok`` true: a decided answer) -- with the separating
  reason: for a named wheel, or the first wheel whose axioms name every
  quantity of the equation, an integer *separating functional* (zero on every
  axiom of the wheel, nonzero on the equation; re-checked here); when no
  single wheel names every quantity, which wheels name each one;
* **refused** (``ok`` false) -- the text is not an equation the engine reads
  (the reason is given), a literal is out of all proportion to a physical
  law, the wheel named is not one of the thirty, or the equation names a
  quantity no wheel knows (named in no wheel's axioms and in no cent wheel's
  dimension table; the names are given).  Nothing is guessed.

When the answer rests on a wheel installed provisionally (a cent wheel while
``cent_compiler_v12`` is in :data:`glm_universal.wheels.PROVISIONAL_REGISTER`)
the text ends with the note of :func:`glm_universal.wheels.provisional_status`
in square brackets and ``figures["provisional"]`` holds it.  A *derivable*
answer rests on the wheel that derives it (no note for a registry wheel); a
*not derivable* answer over all the wheels rests on the cent wheels too (they
were asked), so it carries the cent family's note while that family is
provisional; one put to a single wheel carries that wheel's note, if any.

Figures hold exact values only: ``int``, ``str``, ``Fraction`` and tuples of
them (directive D7: no float anywhere).  Deterministic.
"""
from __future__ import annotations

import ast
import re
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = ["derive_text", "known_quantities", "split_wheel", "MAX_LITERAL",
           "MAX_POWER", "MAX_LENGTH"]

#: An integer literal above this is not read (the engines factor every
#: coefficient by trial division; no physical law needs a larger one).
MAX_LITERAL = 10 ** 9
#: A power whose numerator or denominator exceeds this is not read.
MAX_POWER = 100
#: A longer equation is not read.
MAX_LENGTH = 2000

_WHEEL_SUFFIX = re.compile(r"\s+(?:in\s+wheel|in|wheel)\s+(?P<wid>[Ww]\d{1,3})\s*$")
_NOT_ABSORBED = ("W26, W27, W30 and W31 were never supplied; W35 lost both axioms "
                 "under the cent study's rule R")


# ---------------------------------------------------------------------------
# The wheels and the quantities they know
# ---------------------------------------------------------------------------

def _registry():
    from . import ALL_WHEELS
    return ALL_WHEELS


def _cent():
    from .cent_wheels import CENT_WHEELS
    return CENT_WHEELS


def _all_wheels():
    """The thirty wheels in the engine's order: the registry, then the cent
    family."""
    return tuple(_registry()) + tuple(_cent())


def _names(text: str) -> Tuple[str, ...]:
    tree = ast.parse(text.replace("^", "**").strip(), mode="eval")
    return tuple(sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}))


@lru_cache(maxsize=None)
def _axiom_names() -> Dict[str, Tuple[str, ...]]:
    """``wheel id -> the quantities its axioms name``."""
    out: Dict[str, Tuple[str, ...]] = {}
    for w in _all_wheels():
        seen = set()
        for a in w.axioms:
            for side in a.split("="):
                seen.update(_names(side))
        out[w.id] = tuple(sorted(seen))
    return out


@lru_cache(maxsize=None)
def _table_names() -> Dict[str, Tuple[str, ...]]:
    """``cent wheel id -> the quantities its own dimension table holds``."""
    from .cent_wheels import CENT_TABLES
    return {wid: tuple(sorted(t)) for wid, t in CENT_TABLES.items()}


@lru_cache(maxsize=None)
def known_quantities() -> Tuple[str, ...]:
    """Every quantity some wheel knows: named in an axiom of one of the thirty
    wheels, or held by a cent wheel's dimension table."""
    names = set()
    for v in _axiom_names().values():
        names.update(v)
    for v in _table_names().values():
        names.update(v)
    return tuple(sorted(names))


def _wheel_ids() -> Tuple[str, ...]:
    return tuple(w.id for w in _all_wheels())


def _wheel(wid: str):
    for w in _all_wheels():
        if w.id == wid:
            return w
    raise KeyError(wid)


def _note_for(wid: Optional[str]) -> Optional[str]:
    from . import provisional_status
    return provisional_status(wid) if wid else None


# ---------------------------------------------------------------------------
# Reading the argument
# ---------------------------------------------------------------------------

def split_wheel(arg: str) -> Tuple[str, Optional[str]]:
    """``(equation, wheel id or None)``: a trailing ``in W16`` / ``wheel W16``
    / ``in wheel W16`` names one wheel (``W01`` is ``W1``)."""
    text = (arg or "").strip()
    while text and text[-1] in "?.!":
        text = text[:-1].rstrip()
    m = _WHEEL_SUFFIX.search(text)
    if not m:
        return text, None
    return text[:m.start()].strip(), "W" + str(int(m.group("wid")[1:]))


def _literal_problem(equation: str) -> Optional[str]:
    """Why the equation's literals are out of all proportion, or ``None``.
    Raises ``ValueError`` when the text is not an expression at all."""
    if equation.count("=") != 1:
        raise ValueError("an equation needs exactly one '='")
    for side in equation.split("="):
        try:
            tree = ast.parse(side.replace("^", "**").strip(), mode="eval")
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"not a monomial: {side.strip()!r}") from exc
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, int)
                    and not isinstance(node.value, bool) and abs(node.value) > MAX_LITERAL):
                return (f"the literal {node.value} is above {MAX_LITERAL}; no law on the "
                        f"wheels needs one so large, and it is not factored")
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
                for sub in ast.walk(node.right):
                    if (isinstance(sub, ast.Constant) and isinstance(sub.value, int)
                            and not isinstance(sub.value, bool)
                            and abs(sub.value) > MAX_POWER):
                        return (f"a power with {sub.value} in it is above {MAX_POWER}; "
                                f"it is not computed")
    return None


# ---------------------------------------------------------------------------
# Rendering and re-checking the certificates
# ---------------------------------------------------------------------------

def _q(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _combination(weights: Sequence[Tuple[str, Fraction]]) -> str:
    parts: List[str] = []
    for axiom, w in weights:
        if not w:
            continue
        mag = _q(abs(w))
        term = f"{mag} × ({axiom})"
        if not parts:
            parts.append(term if w > 0 else f"-{term}")
        else:
            parts.append(("+ " if w > 0 else "- ") + term)
    return " ".join(parts)


def _coordinate(key: str) -> str:
    return f"the power of {key[1:]} in the coefficient" if key.startswith("#") else key


def _functional_text(functional: Mapping[str, int]) -> str:
    return ", ".join(f"{_coordinate(k)} ↦ {v}" for k, v in functional.items())


def _vector(text: str) -> Dict[str, Fraction]:
    from .cent_wheels import relation_vector_q
    return relation_vector_q(text)


def _certificate_holds(equation: str, weights: Sequence[Tuple[str, Fraction]]) -> bool:
    """Exactly: the weighted sum of the axioms' relation vectors is the
    equation's."""
    total: Dict[str, Fraction] = {}
    for axiom, w in weights:
        for k, v in _vector(axiom).items():
            total[k] = total.get(k, Fraction(0)) + Fraction(w) * v
    total = {k: v for k, v in total.items() if v}
    return total == _vector(equation)


def _functional_value(equation: str, functional: Mapping[str, int]) -> Fraction:
    goal = _vector(equation)
    return sum((Fraction(v) * goal.get(k, Fraction(0)) for k, v in functional.items()),
               Fraction(0))


def _functional_holds(equation: str, axioms: Sequence[str],
                      functional: Mapping[str, int]) -> bool:
    """Exactly: the functional is zero on every axiom and nonzero on the
    equation."""
    for a in axioms:
        rel = _vector(a)
        if sum((Fraction(v) * rel.get(k, Fraction(0)) for k, v in functional.items()),
               Fraction(0)) != 0:
            return False
    return _functional_value(equation, functional) != 0


# ---------------------------------------------------------------------------
# The answer
# ---------------------------------------------------------------------------

def _with_note(text: str, figures: Dict[str, object], note: Optional[str]) -> str:
    if note:
        figures["provisional"] = note
        return f"{text} [{note}]"
    return text


def _separation(equation: str, wheel) -> Tuple[Optional[Dict[str, int]], str]:
    """The separating functional of ``wheel`` for ``equation`` (re-checked)
    and its sentence; ``(None, reason)`` when it does not re-check."""
    from .cent_wheels import separating_functional
    functional = separating_functional(equation, wheel.axioms)
    if functional is None or not _functional_holds(equation, wheel.axioms, functional):
        return None, f"the separating functional of {wheel.id} did not re-check"
    value = _functional_value(equation, functional)
    return functional, (f"the functional ({_functional_text(functional)}) is 0 on every "
                        f"axiom of {wheel.id} and {_q(value)} on the equation, so no "
                        f"rational combination of {wheel.id}'s axioms gives it")


def derive_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool derive <equation> [in W16]`` -- does the equation follow from the
    GLM's formula wheels?  See the module docstring."""
    from . import answer_derivability
    equation, wheel_id = split_wheel(arg)
    usage = ("derive takes an equation between named quantities, e.g. 'emf = "
             "magnetic_field * area / time', optionally followed by 'in W16'")
    if not equation:
        return False, f"derive: {usage}", {}
    if len(equation) > MAX_LENGTH:
        return False, (f"derive: the equation is longer than {MAX_LENGTH} characters; "
                       f"it is not read"), {}
    try:
        problem = _literal_problem(equation)
        if problem is None:
            _vector(equation)
    except (ValueError, RecursionError, MemoryError) as exc:
        return False, (f"derive: cannot read {equation!r} as an equation between "
                       f"monomials ({exc}); {usage}"), {"equation": equation}
    if problem is not None:
        return False, f"derive: {problem}", {"equation": equation}
    names = _names(equation.replace("=", "*"))
    known = set(known_quantities())
    unknown = tuple(n for n in names if n not in known)
    if unknown:
        return False, (f"derive: no wheel knows {', '.join(unknown)} -- named in no "
                       f"axiom of the {len(_wheel_ids())} wheels and in no cent "
                       f"wheel's dimension table; nothing is guessed"), {
                           "equation": equation, "unknown": unknown}
    if wheel_id is not None and wheel_id not in _wheel_ids():
        return False, (f"derive: there is no wheel {wheel_id}: the wheels are W1-W15 "
                       f"(the registry) and W16-W25, W28, W29, W32-W34 (the cent "
                       f"family; {_NOT_ABSORBED})"), {"equation": equation,
                                                       "wheel": wheel_id}
    try:
        out = answer_derivability(equation, wheel_id=wheel_id)
    except (ValueError, KeyError) as exc:
        return False, f"derive: the engine could not read it ({exc})", {"equation": equation}
    verdict = out.get("verdict")
    figures: Dict[str, object] = {"equation": equation, "verdict": str(verdict)}
    if verdict == "unreadable":
        return False, (f"derive: cannot read {equation!r} as an equation between "
                       f"monomials; {usage}"), figures
    if verdict == "derivable":
        wid = str(out["wheel"])
        w = _wheel(wid)
        weights = tuple((str(a), Fraction(x)) for a, x in (out.get("certificate") or ()))
        if not _certificate_holds(equation, weights):
            return False, (f"derive: {wid}'s certificate did not re-check exactly; "
                           f"nothing is said"), figures
        used = tuple((a, x) for a, x in weights if x)
        figures.update(wheel=wid, wheel_title=w.title, certificate=used,
                       axioms_used=len(used),
                       engine="integer" if wid in {x.id for x in _registry()}
                       else "rational")
        if not used:
            text = (f"derive: derivable -- {equation} is an identity (its two sides are "
                    f"the same monomial); every wheel derives it with all weights 0 "
                    f"({wid} was asked first)")
        else:
            text = (f"derive: derivable in {wid} ({w.title}) -- the relation of "
                    f"{equation} (exponents left minus right, and the coefficient's "
                    f"prime exponents) is exactly {_combination(used)}")
        return True, _with_note(text, figures, _note_for(wid)), figures
    # Not derivable.
    if wheel_id is not None:
        w = _wheel(wheel_id)
        functional, sentence = _separation(equation, w)
        if functional is None:
            return False, f"derive: {sentence}; nothing is said", figures
        figures.update(wheel=wheel_id, wheel_title=w.title,
                       functional=tuple(sorted(functional.items())),
                       functional_value=_functional_value(equation, functional))
        text = f"derive: not derivable in {wheel_id} ({w.title}) -- {sentence}"
        return True, _with_note(text, figures, _note_for(wheel_id)), figures
    goal = _vector(equation)
    quantities = tuple(sorted(k for k in goal if not k.startswith("#")))
    axiom_names = _axiom_names()
    covering = tuple(w for w in _all_wheels()
                     if set(quantities) <= set(axiom_names[w.id]))
    figures["wheels_asked"] = len(_wheel_ids())
    if covering:
        first = covering[0]
        functional, sentence = _separation(equation, first)
        if functional is None:
            return False, f"derive: {sentence}; nothing is said", figures
        others = tuple(w.id for w in covering[1:])
        figures.update(wheel=first.id, wheel_title=first.title,
                       functional=tuple(sorted(functional.items())),
                       functional_value=_functional_value(equation, functional),
                       covering=tuple(w.id for w in covering))
        also = (f"; {', '.join(others)} also name{'s' if len(others) == 1 else ''} every "
                f"quantity of it and refuse{'s' if len(others) == 1 else ''} it too"
                if others else "")
        text = (f"derive: not derivable -- none of the {len(_wheel_ids())} wheels derives "
                f"it. {first.id} ({first.title}) names every quantity of it, but "
                f"{sentence}{also}")
    else:
        tables = _table_names()
        where = []
        for q in quantities:
            named = [wid for wid in _wheel_ids() if q in axiom_names[wid]]
            if named:
                where.append(f"{q}: {', '.join(named)}")
            else:
                held = [wid for wid, names in tables.items() if q in names]
                where.append(f"{q}: in no axiom (only in the dimension table of "
                             f"{', '.join(held)})")
        figures["covering"] = ()
        text = (f"derive: not derivable -- none of the {len(_wheel_ids())} wheels derives "
                f"it, and no single wheel's axioms name all of its quantities (each "
                f"wheel is asked on its own; pooling the axioms of different wheels "
                f"conflates their quantities). Named by: {'; '.join(where)}")
    from .cent_wheels import CENT_WHEELS
    return True, _with_note(text, figures, _note_for(CENT_WHEELS[0].id)), figures
