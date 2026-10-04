"""``glm_universal.runtime.symbolic_frames`` -- answers that are formulas in
letters (Phase 98, ``studies/SYMBOLIC_PARAMETERS_STUDY.md``).

Two kinds of reader, both registered as question frames (so the router's
``frames`` surface reads them and every reading is gated by its column-3
script under ``python3 -I`` before it is output):

* **the operation** ``solve symbolically for T1, T2 [in terms of P1, ...]:
  EQ; EQ; ...`` -- any system of equations in letters, solved by the
  declared substitution of :func:`glm_universal.reasoning.symbolic.
  solve_system`.  With ``in terms of`` every other letter is an unknown to
  eliminate; without it only the targets are unknown.  ``pi`` is always a
  known constant.  A root is the positive root, and says so.
* **the outside frames** of :mod:`glm_universal.runtime.symbolic_outside`
  -- one per kind of class-S question of the outside set: each recognises
  the physical situation and its givens, writes the **laws** that govern it
  as equations in letters, and hands them to the same solver (or to the
  derivative, the series or the entailment of the symbolic layer).  Nothing
  is looked up by question; the variants of
  :data:`glm_universal.evaluation.symbolic_cases.VARIANTS` change a given
  and the answer moves.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from ..reasoning import symbolic as S
from .question_frames import Frame, Reading

__all__ = ["PREFIX", "read_system", "solve_text", "SYMBOLIC_FRAME",
           "SYMBOLIC_FRAMES", "mutated"]

PREFIX = "solve symbolically for "


def _m_system(t: str) -> Optional[dict]:
    """The normalised text starts with the operation (frames see lower
    case; the original letters are recovered from the raw text)."""
    return None


def split_question(text: str) -> Tuple[List[str], Optional[List[str]],
                                       List[str]]:
    """``(targets, params or None, equation texts)``."""
    t = text.strip()
    if not t.lower().startswith(PREFIX) or ":" not in t:
        raise S.SymbolicError("UNREADABLE", "solve symbolically for T, ...: "
                                            "EQ; EQ")
    head, body = t.split(":", 1)
    head = head[len(PREFIX):]
    m = re.split(r"\s+in\s+terms\s+of\s+", head, flags=re.I)
    targets = [x.strip() for x in m[0].split(",") if x.strip()]
    params = [x.strip() for x in m[1].split(",") if x.strip()] \
        if len(m) > 1 else None
    eqs = [e.strip() for e in body.split(";") if e.strip()]
    if not targets or not eqs:
        raise S.SymbolicError("UNREADABLE", "no target or no equation")
    for x in targets + (params or []):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",
                            S.normalise_text(x)):
            raise S.SymbolicError("UNREADABLE", f"not a letter: {x!r}")
    return ([S.normalise_text(x) for x in targets],
            None if params is None else [S.normalise_text(x)
                                         for x in params],
            [S.normalise_text(e) for e in eqs])


def _letters(eq_texts: List[str]) -> set:
    out = set()
    for e in eq_texts:
        for name in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", e):
            if name not in S.FUNCTIONS:
                out.add(name)
    return out


def solve_text(text: str):
    """``(solution, ctx, equation texts, params)`` for the operation, or a
    :class:`SymbolicError`."""
    targets, params, eq_texts = split_question(text)
    ctx = S.Context()
    eqs = [S.parse_equation(e, ctx) for e in eq_texts]
    letters = _letters(eq_texts)
    syms = set()
    for lhs, rhs in eqs:
        syms |= lhs.vars() | rhs.vars()
    syms -= set(ctx.atoms) | set(S.RADICALS)
    if params is not None:
        unknowns = (syms | set(targets)) - set(params) - S.CONSTANTS
    else:
        unknowns = set(targets)
    sol = S.solve_system(eqs, unknowns, targets, mentioned=letters)
    pars = sorted((syms - unknowns) | (S.CONSTANTS & syms))
    return sol, ctx, eq_texts, pars


def answer_texts(sol: S.Solution) -> Dict[str, str]:
    """The printed right-hand side of each target."""
    out = {}
    for t in sol.targets:
        out[t] = sol.root_text(t).split(" = ", 1)[1]
    return out


def _conditions_text(sol: S.Solution) -> str:
    if not sol.conditions:
        return ""
    return "; derived assuming " + ", ".join(f"{S.to_text(c)} != 0"
                                        for c in sol.conditions)


def read_system(text: str, scale_first: Optional[Fraction] = None
                ) -> Reading:
    try:
        sol, ctx, eq_texts, pars = solve_text(text)
    except S.SymbolicError as e:
        return Reading("symbolic_system", False, e.why,
                       f"The system was not solved: {e.why}.",
                       "refused " + e.code, _refusal_script(e.code),
                       code=e.code, backing="reasoning.symbolic")
    ans = answer_texts(sol)
    roots = list(sol.positive_roots())
    value = "; ".join(f"{t} = {ans[t]}" for t in sol.targets)
    if roots:
        value += " (the positive root" + ("s" if len(roots) > 1 else "") + \
            ")"
    value += _conditions_text(sol)
    steps = "; ".join(s.text() for s in sol.steps)
    col1 = (f"From the {len(eq_texts)} equation"
            f"{'s' if len(eq_texts) != 1 else ''}, each unknown is isolated "
            f"where it appears alone and substituted into the rest, in "
            f"{len(sol.steps)} step{'s' if len(sol.steps) != 1 else ''}; "
            f"so {value}.")
    script = S.system_script(eq_texts, sol, ctx, pars, ans,
                             label="SYMBOLIC", scale_first=scale_first)
    return Reading("symbolic_system", True, value, col1, steps, script,
                   backing="reasoning.symbolic (declared substitution over "
                           "exact rational functions)")


def _refusal_script(code: str) -> str:
    return f"print('REFUSED {code} VERIFIED True')\n"


def mutated(text: str) -> Reading:
    """The same reading with the first target's value doubled (the column-3
    control: its script must fail)."""
    return read_system(text, scale_first=Fraction(2))


def _match_system(t: str) -> Optional[dict]:
    if t.startswith(PREFIX):
        return {"raw": None}
    return None


def _answer_system(g: dict) -> Reading:
    return read_system(g["raw"])


#: The operation as a frame; the frame layer passes the raw text (the
#: letters' case matters), see :func:`frame_match`.
SYMBOLIC_FRAME = Frame("symbolic_system", "a system of equations in letters, "
                       "solved for named unknowns", _match_system,
                       _answer_system, source="S")


def _outside() -> Tuple[Frame, ...]:
    from .symbolic_outside import OUTSIDE_S_FRAMES
    return OUTSIDE_S_FRAMES


SYMBOLIC_FRAMES: List[Frame] = []
