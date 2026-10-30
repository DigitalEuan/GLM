"""``glm_universal.runtime.typed_operators_report`` -- the measurement of the
typed-operators round.

``studies/TYPED_OPERATORS_STUDY.md`` (Phase 90) declares eight marks over the
corpus of :mod:`glm_universal.evaluation.typed_operator_cases`; this module
takes the seven that are measured (the eighth is the Lean file,
``RequestProject/GLM/TypedOperators.lean``).  The reader itself is
:mod:`glm_universal.runtime.typed_operators`, reached through the declared
frame ``typed_operator`` of :mod:`glm_universal.runtime.question_frames` and
so through the router and ``GLM.py -q``.

Two controls: **typed off** (``typed_operators.ACTIVE = False``: the machine
before the round, every case routed as it was) and **naive** (a monomial
wheel: magnitudes multiplied).
"""

from __future__ import annotations

import importlib
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from ..engineering.smith import GaussQ
from ..evaluation import typed_operator_cases as C
from ..reasoning import exact_forms as ef
from . import typed_operators as to

__all__ = ["group_report", "control_report", "earlier_report",
           "scripts_report", "census_report", "typed_operators_report",
           "earlier_questions"]

_GROUPS = (("phasor", C.PHASOR_CASES), ("kind", C.KIND_CASES),
           ("vector", C.VECTOR_CASES))


def _session():
    from .session import GeometricSession
    return GeometricSession()


def _routed_as_declared(r, want: tuple) -> bool:
    """Whether a routed verdict (any surface) is the declared one, read from
    its text: the value for an answer, the code for a refusal."""
    text = r.text or ""
    if want[0] == "ANSWER":
        return bool(r.answered) and to.value_text(want[1]) in text
    if want[0] == "AMBIGUOUS":
        return "AMBIGUOUS" in text
    return (not r.answered) and want[1] in text


def group_report(session=None, route: bool = True) -> Dict[str, Dict]:
    """T1--T3: each group's cases as declared; through the router, before
    (typed off) and after."""
    from . import router
    session = session or (_session() if route else None)
    out: Dict[str, Dict] = {}
    for name, cases in _GROUPS:
        met, wrong, before, after, rows = 0, [], 0, 0, []
        answered_before = 0
        for cid, q, want in cases:
            a = to.answer(q)
            got = None if a is None else a.verdict
            ok = got == want
            met += ok
            if not ok and a is not None and a.answered:
                wrong.append(cid)
            row = {"id": cid, "verdict": got, "declared": want, "ok": ok}
            if route:
                saved = to.ACTIVE
                to.ACTIVE = False
                try:
                    r0 = router.route(session, q)
                finally:
                    to.ACTIVE = saved
                r1 = router.route(session, q)
                b = _routed_as_declared(r0, want)
                f = (r1.surface == "frames"
                     and getattr(r1.payload, "frame", None) == "typed_operator"
                     and r1.payload.gate is not None and r1.payload.gate[0]
                     and ok)
                before += b
                answered_before += bool(r0.answered)
                after += f
                row.update(before_surface=r0.surface, before_ok=b,
                           after_surface=r1.surface, after_ok=f)
            rows.append(row)
        out[name] = {"cases": len(cases), "met": met, "wrong": wrong,
                     "routed_before": before if route else None,
                     "routed_after": after if route else None,
                     "answered_before": answered_before if route else None,
                     "rows": rows}
    return out


def control_report() -> Dict[str, object]:
    """T4's naive half: the monomial control on every answered phasor and
    vector case."""
    answered = wrong = right = 0
    wrong_ids: List[Tuple[str, str]] = []
    for cid, q, want in C.ALL_CASES:
        if want[0] != "ANSWER":
            continue
        n = to.naive(q)
        if n is None:
            continue
        answered += 1
        if n == want[1]:
            right += 1
        else:
            wrong += 1
            wrong_ids.append((cid, to.value_text(n)))
    return {"naive_answers": answered, "naive_wrong": wrong,
            "naive_right": right, "wrong_ids": wrong_ids,
            "at_least": C.NAIVE_WRONG_AT_LEAST,
            "met": wrong >= C.NAIVE_WRONG_AT_LEAST}


def _strings(x, depth: int = 0):
    if depth > 8:
        return
    if isinstance(x, str):
        yield x
    elif isinstance(x, (list, tuple, set, frozenset)):
        for y in x:
            yield from _strings(y, depth + 1)
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from _strings(k, depth + 1)
            yield from _strings(v, depth + 1)
    elif hasattr(x, "__dataclass_fields__") and not isinstance(x, type):
        for f in x.__dataclass_fields__:
            yield from _strings(getattr(x, f, None), depth + 1)


def earlier_questions() -> List[Tuple[str, str]]:
    """Every string of twelve characters or more held by an earlier declared
    corpus (every module of :mod:`glm_universal.evaluation` but this
    round's), and the two outside question sets."""
    from pathlib import Path
    from .. import evaluation as ev
    out: List[Tuple[str, str]] = []
    names = sorted(p.stem for p in Path(ev.__file__).parent.glob("*.py")
                   if p.stem not in ("typed_operator_cases", "__main__",
                                     "__init__"))
    for name_ in names:
        mod = importlib.import_module(f"glm_universal.evaluation.{name_}")
        seen = set()
        for name in dir(mod):
            if name.startswith("_"):
                continue
            for s in _strings(getattr(mod, name)):
                if len(s) >= 12 and s not in seen:
                    seen.add(s)
                    out.append((name_, s))
    from ..evaluation import question_set_b_cases as qc
    out += [("set_b", it.query) for it in qc.set_b()]
    out += [("outside_o1", it.text) for it in qc.outside()]
    return out


def earlier_report() -> Dict[str, object]:
    """T5: the typed reader recognises none of the earlier questions."""
    qs = earlier_questions()
    hits = [(m, s[:80]) for m, s in qs if to.reads(s)]
    return {"strings": len(qs), "modules": len({m for m, _ in qs}),
            "read": hits, "met": not hits}


def _mutate(value: object) -> object:
    if isinstance(value, Fraction):
        return value + 1
    if isinstance(value, GaussQ):
        return GaussQ(value.re + 1, value.im)
    if isinstance(value, ef.Surd):
        if value.is_rational():
            return ef.Surd(value.rational() + 1)
        return ef.Surd(value.a, value.b + 1, value.c)
    if isinstance(value, tuple):
        return (value[0] + 1,) + tuple(value[1:])
    raise TypeError(value)


def scripts_report() -> Dict[str, object]:
    """T6: every reading's script verifies; every answered reading's script
    with the claimed value moved by one fails."""
    from .question_frames import normalise, run_gate
    verified = mutated = caught = 0
    failed: List[str] = []
    escaped: List[str] = []
    for cid, q, _ in C.ALL_CASES:
        g = to.recognise(normalise(q))
        a = to.answer_givens(g)
        ok, _last = run_gate(a.script)
        verified += ok
        if not ok:
            failed.append(cid)
        if a.answered:
            bad = to.script_for(g, _mutate(a.value), a.sense,
                                _factor_of(g))
            mutated += 1
            if run_gate(bad)[0]:
                escaped.append(cid)
            else:
                caught += 1
    return {"scripts": len(C.ALL_CASES), "verified": verified,
            "failed": failed, "mutants": mutated, "caught": caught,
            "escaped": escaped,
            "met": not failed and not escaped and caught == mutated}


def _factor_of(g: dict) -> Fraction:
    unit = g.get("unit")
    if g["mode"] in ("phasor", "triangle") and unit in to.POWER_UNITS:
        return to.POWER_UNITS[unit][1]
    return Fraction(1)


def census_report() -> Dict[str, object]:
    """T7: the identities over the declared grid."""
    c = to.census(C.GRID)
    c["met"] = c["phasor_violations"] == 0 and c["vector_violations"] == 0
    return c


def typed_operators_report(scripts: bool = True, route: bool = True
                           ) -> Dict[str, object]:
    """Every measured mark of the study."""
    groups = group_report(route=route)
    control = control_report()
    before = sum(g["routed_before"] or 0 for g in groups.values()) \
        if route else None
    after = sum(g["routed_after"] or 0 for g in groups.values()) \
        if route else None
    rep: Dict[str, object] = {
        "groups": groups, "control": control,
        "answered_before": sum(g["answered_before"] or 0
                               for g in groups.values()) if route else None,
        "routed_before": before, "routed_after": after,
        "earlier": earlier_report(),
        "scripts": scripts_report() if scripts else None,
        "census": census_report(),
    }
    marks = {
        "T1": groups["phasor"]["met"] == groups["phasor"]["cases"],
        "T2": groups["kind"]["met"] == groups["kind"]["cases"],
        "T3": groups["vector"]["met"] == groups["vector"]["cases"],
        "T4": control["met"] and (before == 0 if route else True),
        "T5": rep["earlier"]["met"],
        "T6": rep["scripts"]["met"] if scripts else None,
        "T7": rep["census"]["met"],
    }
    rep["marks"] = marks
    return rep
