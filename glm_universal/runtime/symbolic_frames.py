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

__all__ = ["PREFIX", "PHASE", "read_system", "solve_text", "solve_branches",
           "convention", "canonical",
           "SYMBOLIC_FRAME",
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


_MATH = re.compile(r"[A-Za-z0-9_\s+\-*/^().=;,]+")
_NAMES = r"[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*"


def _equations(body: str) -> Optional[List[str]]:
    body = body.strip().rstrip("?.").strip()
    if not body or not _MATH.fullmatch(body) or "=" not in body:
        return None
    parts = [x.strip() for x in re.split(r";|,(?![^()]*\))|\band\b", body)
             if x.strip()]
    if not parts or any(x.count("=") != 1 for x in parts):
        return None
    for x in parts:
        # two operands side by side with no operator between them is prose
        # ("= 30 in integers"), not an equation; and each must parse
        if re.search(r"[A-Za-z0-9_)]\s+[A-Za-z_(0-9]", x):
            return None
        try:
            S.parse_equation(S.normalise_text(x), S.Context())
        except (S.SymbolicError, ValueError, ZeroDivisionError):
            return None
    return parts


def canonical(text: str) -> Optional[str]:
    """Plain phrasings of the operation, rewritten to its own form
    (sharpening pass: the operation was reachable only through the words
    ``solve symbolically for``).  Read: ``solve for X[, Y] [in terms of
    ...]: EQ; EQ``, ``solve EQ[; EQ] for X[, Y]``, and ``solve EQ`` /
    ``(find|what are) the (real) roots of EQ`` with the unknown ``x`` (or the
    one letter the equation holds).  Anything else is ``None``: the text must
    be equations and names only."""
    t = " ".join(text.strip().split())
    low = t.lower()
    if low.startswith(PREFIX):
        return None
    m = re.fullmatch(rf"solve\s+for\s+({_NAMES})(\s+in\s+terms\s+of\s+"
                     rf"{_NAMES})?\s*:\s*(.+)", t, flags=re.I)
    if m:
        eqs = _equations(m.group(3))
        if eqs is None:
            return None
        return f"{PREFIX}{m.group(1)}{m.group(2) or ''}: " + "; ".join(eqs)
    m = re.fullmatch(rf"solve\s+(.+?)\s+for\s+({_NAMES})\s*[?.]?", t,
                     flags=re.I)
    if m:
        eqs = _equations(m.group(1))
        if eqs is None:
            return None
        return f"{PREFIX}{m.group(2)}: " + "; ".join(eqs)
    m = re.fullmatch(r"(?:solve|(?:find|what\s+are)\s+the\s+(?:real\s+)?"
                     r"roots\s+of|(?:real\s+)?roots\s+of)\s+(.+)", t,
                     flags=re.I)
    if m:
        eqs = _equations(m.group(1))
        if eqs is None or len(eqs) != 1:
            return None
        names = sorted(_letters(eqs) - set(S.CONSTANTS))
        target = "x" if "x" in names else (names[0] if len(names) == 1
                                           else None)
        if target is None:
            return None
        return f"{PREFIX}{target}: {eqs[0]}"
    return None


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


def _setup(text: str):
    """``(equations, unknowns, targets, ctx, equation texts, params,
    letters)`` exactly as :func:`solve_text` reads the operation."""
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
    pars = sorted((syms - unknowns) | (S.CONSTANTS & syms))
    return eqs, unknowns, targets, ctx, eq_texts, pars, letters


#: The operation as each round left it: 98 (substitution only), 103 (the
#: branch layer on a ``NONLINEAR`` refusal), 104 (the branch layer with
#: algebraic numbers, towers and Cardano's root, and the two tracks for a
#: positive-root reading -- ``studies/CUBIC_RADICAL_STUDY.md``).
PHASE = 104


def solve_branches(text: str, phase: int = PHASE):
    """``(branches, ctx, equation texts, params)`` from the nonlinear layer
    of Phase 103 (``reasoning.symbolic_nonlinear``), which the operation
    consults when substitution refuses ``NONLINEAR`` -- and, from Phase 104,
    when substitution answers by the positive-root convention."""
    from ..reasoning.symbolic_nonlinear import solve_nonlinear
    eqs, unknowns, targets, ctx, eq_texts, pars, _ = _setup(text)
    return (solve_nonlinear(eqs, unknowns, targets,
                            extended=phase >= 104), ctx, eq_texts, pars)


def _branch_text(sol: S.Solution, ans: Dict[str, str]) -> str:
    from ..reasoning.symbolic_nonlinear import approximate
    parts = []
    for t in sol.targets:
        a = approximate(sol, t)
        parts.append(f"{t} = {ans[t]}" + (f" (about {a})" if a else ""))
    return ", ".join(parts)


def _real_text(br) -> str:
    seen: List[str] = []
    for sol in br.solutions:
        ext = getattr(sol, "ext", None)
        for r in (ext.real if ext is not None else ()):
            if r not in seen:
                seen.append(r)
    if not seen:
        return ""
    return "; real when " + ", ".join(seen)


def _case_groups(br) -> List[Tuple[Tuple[str, ...], List[int]]]:
    """The solutions grouped by their real conditions, in order of first
    appearance: more than one group means the answer splits into cases."""
    groups: List[Tuple[Tuple[str, ...], List[int]]] = []
    for i, sol in enumerate(br.solutions):
        ext = getattr(sol, "ext", None)
        key = tuple(ext.real) if ext is not None else ()
        for g, idx in groups:
            if g == key:
                idx.append(i)
                break
        else:
            groups.append((key, [i]))
    return groups


def _branch_alternative(text: str, scale_first: Optional[Fraction],
                        phase: int = PHASE) -> Reading:
    from ..reasoning.symbolic_nonlinear import branch_script
    try:
        br, ctx, eq_texts, pars = solve_branches(text, phase)
    except S.SymbolicError as e:
        return Reading("symbolic_system", False, e.why,
                       f"The system was not solved: {e.why}.",
                       "refused " + e.code, _refusal_script(e.code),
                       code=e.code, backing="reasoning.symbolic_nonlinear")
    parts, scripts = [], []
    for n, sol in enumerate(br.solutions, 1):
        ans = answer_texts(sol)
        ext = getattr(sol, "ext", None)
        if ext is not None:
            parts.append(_branch_text(sol, ans))
        else:
            parts.append(", ".join(f"{t} = {ans[t]}" for t in sol.targets))
        if ext is not None and ext.needs_script:
            scripts.append(branch_script(eq_texts, sol, ctx, pars, ans,
                                         label=f"SYMBOLIC BRANCH {n}",
                                         scale_first=scale_first))
        else:
            scripts.append(S.system_script(eq_texts, sol, ctx, pars, ans,
                                           label=f"SYMBOLIC BRANCH {n}",
                                           scale_first=scale_first))
    k = len(br.solutions)
    split = phase >= 104 and any(getattr(getattr(s, "ext", None), "trig",
                                         None) for s in br.solutions)
    groups = _case_groups(br) if split else []
    if len(groups) > 1:
        # sharpening pass: branches valid under different conditions on
        # the letters (a cubic whose discriminant's sign is not decided)
        # are printed as cases, each with its own condition, not one
        # merged list of conditions
        cases = []
        for conds, idx in groups:
            sub = [parts[i] for i in idx]
            body = sub[0] if len(sub) == 1 else "; ".join(
                f"({i + 1}) {parts[i]}" for i in idx)
            cases.append(f"when {', '.join(conds) or 'always'}: {body}")
        value = f"{k} solutions by cases: " + " || ".join(cases)
        value += _conditions_text(br.solutions[0])
    else:
        if k == 1:
            value = parts[0]
        else:
            value = f"{k} solutions: " + "; ".join(f"({n}) {p}" for n, p in
                                                  enumerate(parts, 1))
        value += _conditions_text(br.solutions[0])
        if phase >= 104:
            value += _real_text(br)
    steps = " | ".join("; ".join(s) for s in br.steps)
    if br.dropped:
        steps += " | discarded: " + "; ".join(br.dropped)
    col1 = (f"Substitution alone cannot isolate the unknowns of these "
            f"{len(eq_texts)} equation{'s' if len(eq_texts) != 1 else ''}, "
            f"so they are eliminated by isolation through any coefficient, "
            f"roots of the equation left in one unknown, and resultants; "
            f"every branch is checked against every equation; so {value}.")
    return Reading("symbolic_system", True, value, col1, steps,
                   "\n".join(scripts),
                   backing="reasoning.symbolic_nonlinear (elimination by "
                           "isolation, roots and resultants over exact "
                           "rational functions with named square roots)")


def convention(sol: S.Solution) -> List[str]:
    """Why a substitution reading is not every real solution: a target given
    as a positive root, or a target whose value holds an unknown known only
    through a root (which the reading does not print).  Empty when neither
    (Phase 104)."""
    why = []
    roots = list(sol.positive_roots())
    if roots:
        why.append("the positive root of " + ", ".join(roots))
    hidden = sorted({g for t in sol.targets
                     for g in sol.values[t][1].vars() & set(sol.generators)
                     if g not in sol.targets})
    if hidden:
        why.append("a value holding " + ", ".join(hidden) +
                   ", which is not printed")
    return why


def _two_tracks(text: str, scale_first: Optional[Fraction], r98: Reading,
                why: List[str]) -> Reading:
    """Phase 104, the owner's rule: keep both tracks, default to the
    stronger.  The branch layer claims every real solution, so when it
    answers its branch set is the answer and the substitution reading is
    kept beside it; when it refuses, the substitution reading stands and
    the refusal is noted in column 2."""
    alt = _branch_alternative(text, scale_first)
    if not alt.answered:
        return Reading(r98.frame, r98.answered, r98.value, r98.column1,
                       r98.column2 + f" | the branch layer refused: "
                                     f"{alt.code}", r98.script,
                       backing=r98.backing)
    # the substitution track is shown only as it checks: its own column-3
    # script is run here, and a track that fails it is marked, not kept
    from .question_frames import run_gate
    ok98 = run_gate(r98.script)[0]
    track = r98.value if ok98 else (f"{r98.value} -- its own check failed, "
                                    f"so it is not kept")
    value = (f"{alt.value} [every real solution; by substitution alone "
             f"({'; '.join(why)}): {track}]")
    col1 = (f"Substitution answers by a convention ({'; '.join(why)}), so "
            f"the branch layer is consulted too: it eliminates the unknowns "
            f"by isolation, roots and resultants and checks every branch "
            f"against every equation; the stronger answer, every real "
            f"solution, is given, with the substitution track beside it; so "
            f"{value}.")
    return Reading("symbolic_system", True, value, col1,
                   alt.column2 + " | substitution track: " + r98.column2,
                   alt.script + ("\n" + r98.script if ok98 else ""),
                   backing="reasoning.symbolic_nonlinear and "
                           "reasoning.symbolic (two tracks)")


def read_system(text: str, scale_first: Optional[Fraction] = None,
                nonlinear: bool = True, phase: int = PHASE) -> Reading:
    """The operation's reading.  ``nonlinear=False`` is the operation as
    Phase 98 shipped it (a ``NONLINEAR`` refusal stands); ``phase=103`` is
    the operation as Phase 103 shipped it."""
    try:
        sol, ctx, eq_texts, pars = solve_text(text)
    except S.SymbolicError as e:
        if nonlinear and e.code == "NONLINEAR":
            return _branch_alternative(text, scale_first, phase)
        return Reading("symbolic_system", False, e.why,
                       f"The system was not solved: {e.why}.",
                       "refused " + e.code, _refusal_script(e.code),
                       code=e.code, backing="reasoning.symbolic")
    for t in sol.targets:
        # an even root of a negative number is no real value (before Phase
        # 103 the printer was handed sqrt(-1) and the script raised)
        k, v = sol.values[t]
        c = v.const_value()
        if k % 2 == 0 and c is not None and c < 0:
            why = f"{t}^{k} = {S.to_text(v)} has no real root"
            return Reading("symbolic_system", False, why,
                           f"The system was not solved: {why}.",
                           "refused NO_REAL_ROOT",
                           _refusal_script("NO_REAL_ROOT"),
                           code="NO_REAL_ROOT", backing="reasoning.symbolic")
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
    r98 = Reading("symbolic_system", True, value, col1, steps, script,
                  backing="reasoning.symbolic (declared substitution over "
                          "exact rational functions)")
    if nonlinear and phase >= 104:
        why = convention(sol)
        if why:
            return _two_tracks(text, scale_first, r98, why)
    return r98


def _refusal_script(code: str) -> str:
    return f"print('REFUSED {code} VERIFIED True')\n"


def mutated(text: str, nonlinear: bool = True, phase: int = PHASE
            ) -> Reading:
    """The same reading with the first target's value doubled (the column-3
    control: its script must fail)."""
    return read_system(text, scale_first=Fraction(2), nonlinear=nonlinear,
                       phase=phase)


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
