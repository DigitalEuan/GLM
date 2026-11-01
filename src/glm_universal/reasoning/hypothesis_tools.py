"""``glm_universal.reasoning.hypothesis_tools`` -- the Rule 30 study's
hypothesis engine on the GLM's answering path: ``tool rule30``, ``tool
conjecture`` and the plan search behind ``tool arc``.

*Created 1 November 2026 (Phase 186: the intake items absorbed where they
measurably help, directive D22).  Absorbed ahead of the owner's Lean build by
the owner's decision of 1 November 2026, on its measurements
(``studies/INTAKE_CAPABILITY_STUDY.md``) and a standalone Lean check
(``IntakeChecks/RuleThirtyBits.lean``); every answer says so while the
register ``wheels/_data/provisional.json`` lists the intake item
``Rule30_GLM_Study`` (:func:`glm_universal.wheels.provisional_status`).*

What it answers
---------------
``tool rule30 centre N``
    the first ``N`` cells of Rule 30's centre column from one black cell
    (``N`` at most :data:`MAX_CENTRE`), with the count of black cells; for
    ``N`` up to 64 the cells are the list ``centreBits_64`` proves, and the
    step the engine computes is Rule 30 by ``testBit_step_succ``
    (``IntakeChecks/RuleThirtyBits.lean``).
``tool rule30 claim SENTENCE``
    a sentence about Rule 30 read by the engine's recognisers
    (:data:`glm_universal.reasoning.hypothesis_engine.RECOGNISERS`), put
    through its gates -- the exact computation, the escalation over five
    nested scales, the implication edges and the Lean ledger -- and answered
    with its ring: *knows* (proved in Lean, verified exactly, or refuted with a
    counterexample or a Lean theorem), *thinks true* (no counterexample at any
    scale read: never called proved) or *doesn't know* (open, with the need
    that would settle it).  Every Lean name the answer cites is looked up in
    the development (:func:`glm_universal.reasoning.lean_address.declaration_names`)
    and marked if it is not there.
``tool rule30 battery``
    the engine's own Rule 30 domain: its 39 claims, scored against the truth
    fixed in advance.
``tool conjecture CLAIM``
    a claim about every integer ``n`` -- a predicate in ``n`` written with
    integers, ``+ - * / // % **``, comparisons and the functions
    ``isprime gcd comb abs min max`` (``n^2`` and ``2n`` are read as
    ``n**2`` and ``2*n``; ``EXPR is prime`` as ``isprime(EXPR)``), optionally
    ``for every n >= K`` -- read at five nested scales; a counterexample
    refutes it, and a claim that survives every read is reported as surviving
    to the largest scale and open beyond, never as proved.  The reading has a
    work bound (:data:`CONJECTURE_BUDGET`): a claim whose values grow beyond
    reach (``n ** n``) is read only at the scales the bound allows, and the
    answer says where it stopped.  ``tool conjecture
    NAME`` runs one of the general domain's registered claims (``euler``,
    ``fermat``, ``fermat coprime``, ``two squares``, ``circle regions``,
    ``josephus``, ``collatz bound``, ``collatz``, ``gcd trap``) through the
    engine with its Lean ledger (``HypothesisEngine/Benchmarks.lean``).
``tool arc NAME`` (through :func:`arc_combined_text`)
    the colour solver of ``tool induce`` first; a test input it refuses goes
    to the engine's plan search (:func:`glm_universal.reasoning.hypothesis_engine.solve_arc`
    over every step of its library), which answers only when every consistent
    program of least depth agrees on the test input; each answer is graded
    against the stored output.

Nothing here constructs a float: the engine is exact, and the counts are
integers and fractions.
"""
from __future__ import annotations

import json
import re
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from . import hypothesis_engine as E

__all__ = [
    "Answer", "MAX_CENTRE", "LEAN_CENTRE", "ITEM", "MODULE", "rule30_text", "conjecture_text",
    "CONJECTURE_SCALES", "CONJECTURE_BUDGET",
    "arc_plan", "arc_combined_text", "lean_citations", "build_note", "parse_conjecture",
    "REGISTRY",
]

#: ``(ok, text, figures)``, the shape every tool of the toolbox returns.
Answer = Tuple[bool, str, Dict[str, object]]

#: The intake item the engine came from, and this module's name in the
#: register of provisional families.
ITEM = "Rule30_GLM_Study"
MODULE = "reasoning/hypothesis_tools"

#: The longest centre column ``tool rule30 centre N`` computes.
MAX_CENTRE = 100_000

#: The Lean theorem that proves the first 64 cells of the centre column.
LEAN_CENTRE = "GLM.IntakeChecks.RuleThirtyBits.centreBits_64"

#: The Lean theorem that proves the engine's step is Rule 30.
LEAN_STEP = "GLM.IntakeChecks.RuleThirtyBits.testBit_step_succ"

#: The general domain's registered claims, by the name a caller uses.
REGISTRY: Dict[str, str] = {
    "euler": "GEN.euler.prime", "euler below 40": "GEN.euler.prime.below40",
    "fermat": "GEN.fermat.prime", "fermat coprime": "GEN.fermat.coprime",
    "two squares": "GEN.two.squares", "circle regions": "GEN.circle.regions",
    "josephus": "GEN.josephus", "collatz bound": "GEN.collatz.bound", "collatz": "GEN.collatz",
    "gcd trap": "GEN.gcd.trap",
}

#: The five nested scales a free conjecture is read at.
CONJECTURE_SCALES = (10, 100, 1000, 5000, 20000)

#: The work bound of one free conjecture's reading, in the evaluator's units
#: (:func:`glm_universal.reasoning.hypothesis_engine.safe_predicate`; about a
#: nanosecond each): the scales are read in turn, each from its first value,
#: and the reading stops at the first scale it cannot finish within the bound.
CONJECTURE_BUDGET = 4_000_000_000

_RINGS = {E.KNOWS: "knows", E.THINKS: "thinks true", E.DONT_KNOW: "doesn't know"}


# ---------------------------------------------------------------------------
# The build-pending note and the Lean citations
# ---------------------------------------------------------------------------

def build_note() -> Optional[str]:
    """The note every answer of this module carries while the register of
    provisional families lists it (absorbed ahead of the owner's build)."""
    from ..wheels import provisional_status
    return provisional_status(MODULE)


def _finish(ok: bool, text: str, figures: Dict[str, object]) -> Answer:
    note = build_note()
    if note:
        figures = dict(figures, provisional=note)
        text = f"{text} [{note}]"
    return ok, text, figures


_LEAN_TOKEN = re.compile(r"\b([A-Z][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)+)")


def lean_citations(backing: List[str]) -> Tuple[List[str], List[str]]:
    """The Lean names a ``FORMAL`` or ``CERT`` backing line cites, each
    resolved to a full name of the development: ``(declared, not_found)``.

    The engine cites a theorem by its file and its name
    (``Diagonals.rdiag_periodic`` is ``rdiag_periodic`` in
    ``Rule30/Diagonals.lean``, whose full name is ``GLM.Rule30.rdiag_periodic``);
    a name is resolved exactly, then under ``GLM.``, then as the declaration
    of that file whose full name ends with the rest of the citation."""
    from .lean_address import declaration_names, declarations
    names = declaration_names()
    by_file: Dict[str, List[str]] = {}
    found: List[str] = []
    missing: List[str] = []
    for line in backing:
        if not line.startswith(("FORMAL", "CERT")):
            continue
        for token in _LEAN_TOKEN.findall(line):
            token = token.rstrip(".")
            full = token if token in names else ("GLM." + token if "GLM." + token in names
                                                 else None)
            if full is None:
                if not by_file:
                    for d in declarations():
                        stem = d.file.rsplit("/", 1)[-1].removesuffix(".lean")
                        by_file.setdefault(stem, []).append(d.name)
                stem, rest = token.split(".", 1)
                hits = [n for n in by_file.get(stem, []) if n == rest or n.endswith("." + rest)]
                full = hits[0] if len(hits) == 1 else None
            if full is None:
                if token not in missing:
                    missing.append(token)
            elif full not in found:
                found.append(full)
    return found, missing


def _verdict(h: "E.Hypothesis") -> Dict[str, object]:
    ring = E.ring_of(h.status)
    found, missing = lean_citations(h.backing)
    need = E.need_of(h)
    reason = h.gate_log[-1].split(": ", 1)[-1] if h.gate_log else ""
    return {"status": h.status, "ring": _RINGS[ring], "answer": E.answer_of(h.status),
            "reason": reason, "lean": found, "lean_not_found": missing,
            "need": need.because if need else None, "class": h.cls, "key": h.key}


def _verdict_text(claim: str, v: Dict[str, object]) -> str:
    answer = {True: "true", False: "false", None: "not settled"}[v["answer"]]
    out = (f"{claim!r}: {answer} -- on the engine's wheel it is in the ring "
           f"'{v['ring']}' ({v['status']}: {v['reason']})")
    if v["lean"]:
        out += "; Lean: " + ", ".join(str(n) for n in v["lean"])
    if v["lean_not_found"]:
        out += "; cited but not in the development: " + ", ".join(str(n) for n in v["lean_not_found"])
    if v["need"]:
        out += f"; to settle it: {v['need']}"
    return out


# ---------------------------------------------------------------------------
# tool rule30
# ---------------------------------------------------------------------------

_DATA: Dict[bool, "E.R30Data"] = {}


def _data(quick: bool = False) -> "E.R30Data":
    if quick not in _DATA:
        _DATA[quick] = E.R30Data(quick=quick)
    return _DATA[quick]


RULE30_USAGE = ("tool rule30 centre N (the first N cells of the centre column, N <= "
                f"{MAX_CENTRE}) ; tool rule30 claim SENTENCE (a sentence about Rule 30, e.g. "
                "'the least period of right diagonal D divides 2^D') ; tool rule30 battery")


def _centre(n_text: str) -> Answer:
    if not n_text.isdigit() or not 1 <= int(n_text) <= MAX_CENTRE:
        return False, (f"rule30: refused -- the centre column is read for 1 to {MAX_CENTRE} "
                       f"cells, not {n_text!r}"), {"status": "refused"}
    n = int(n_text)
    bits = E.centre_bits(n)
    ones = sum(bits)
    shown = "".join(str(b) for b in bits[:64]) + ("..." if n > 64 else "")
    lean = (f"the cells are those {LEAN_CENTRE} proves" if n <= 64 else
            f"the first 64 cells are those {LEAN_CENTRE} proves; the rest are computed exactly "
            f"with the step {LEAN_STEP} proves to be Rule 30")
    text = (f"rule30: the first {n} cells of Rule 30's centre column from one black cell: "
            f"{shown}; {ones} black, {n - ones} white (share of black {Fraction(ones, n)}); "
            f"{lean}")
    return True, text, {"status": "answered", "cells": n, "black": ones,
                        "share": f"{Fraction(ones, n)}", "lean": [LEAN_CENTRE, LEAN_STEP],
                        "prefix": "".join(str(b) for b in bits[:64])}


def _claim(sentence: str) -> Answer:
    s = sentence.strip().rstrip("?").strip()
    if not s:
        return False, "rule30: refused -- no sentence given; " + RULE30_USAGE, {"status": "refused"}
    if E.recognise(s) is None:
        return False, (f"rule30: refused -- the engine recognises no Rule 30 family in {s!r} "
                       f"(it reads sentences such as 'the least period of right diagonal D "
                       f"divides 2^D', 'every left diagonal has eventual period dividing 16 for "
                       f"D < 1000' or 'the centre column is not eventually periodic with period "
                       f"p ≤ 100 and preperiod ≤ 1000')"), {"status": "refused", "claim": s}
    dom = E.Rule30Domain(_data())
    eng = E.Engine(use_ledger=True)
    h = eng.add(E.import_statement(dom, s))
    eng.cascade(h)
    v = _verdict(h)
    return (v["answer"] is not None or v["ring"] == "thinks true",
            "rule30: " + _verdict_text(s, v), dict(v, claim=s))


def _battery() -> Answer:
    eng, rep = E.run_rule30(_data())
    sc = rep.get("score") or {}
    rings = {k: len(v) for k, v in ((rep.get("wheel") or {}).get("rings") or {}).items()}
    text = (f"rule30: the engine's Rule 30 domain, {sc.get('n', 0)} claims scored against the "
            f"truth fixed in advance: {sc.get('right', 0)} right, {sc.get('wrong', 0)} wrong, "
            f"{sc.get('overclaim', 0)} overclaimed, {sc.get('abstain', 0)} abstained; on the "
            f"engine's wheel " + ", ".join(f"{v} {k}" for k, v in rings.items()))
    return sc.get("wrong", 1) == 0 and sc.get("overclaim", 1) == 0, text, \
        {"status": "measured", "score": dict(sc), "rings": rings}


def rule30_text(arg: str) -> Answer:
    """``tool rule30 ...`` (see the module docstring)."""
    a = " ".join(arg.split())
    low = a.lower()
    if not a:
        return _finish(True, "rule30: the Rule 30 study's hypothesis engine; " + RULE30_USAGE,
                       {"status": "usage"})
    m = re.fullmatch(r"(?:centre|center)(?: column)?\s+(\S+)", low)
    if m:
        return _finish(*_centre(m.group(1)))
    if low.startswith("claim "):
        return _finish(*_claim(a[len("claim "):]))
    if low == "battery":
        return _finish(*_battery())
    return _finish(False, f"rule30: refused -- {a!r} is not a request it reads; " + RULE30_USAGE,
                   {"status": "refused"})


# ---------------------------------------------------------------------------
# tool conjecture
# ---------------------------------------------------------------------------

_SUPERSCRIPTS = {"²": "**2", "³": "**3"}


def parse_conjecture(text: str) -> Tuple[Optional[str], int, str]:
    """``(expression, start, why)``: the claim as a predicate in ``n`` for
    :func:`glm_universal.reasoning.hypothesis_engine.safe_predicate` (or
    ``None``, with ``why``), and the least ``n`` it is claimed for."""
    t = " ".join(text.split()).rstrip("?.! ").strip()
    start = 0
    m = re.search(r",?\s*(?:for (?:every|all|each) (?:integer |natural number )?n|for n)"
                  r"(?:\s*(?:>=|≥|from)\s*(\d+))?\s*$", t, re.IGNORECASE)
    if m:
        start = int(m.group(1)) if m.group(1) else 0
        t = t[:m.start()].strip()
    for k, v in _SUPERSCRIPTS.items():
        t = t.replace(k, v)
    t = (t.replace("^", "**").replace("×", "*").replace("·", "*").replace("≤", "<=")
         .replace("≥", ">=").replace("≠", "!="))
    t = re.sub(r"(\d)\s*(n\b|\()", r"\1*\2", t)
    t = re.sub(r"\)\s*(n\b|\()", r")*\1", t)
    m = re.fullmatch(r"(.+?)\s+is (?:a )?prime", t, re.IGNORECASE)
    if m:
        t = f"isprime({m.group(1)})"
    m = re.fullmatch(r"(.+?)\s+is (even|odd)", t, re.IGNORECASE)
    if m:
        t = f"({m.group(1)}) % 2 == {0 if m.group(2).lower() == 'even' else 1}"
    m = re.fullmatch(r"(.+?)\s+divides\s+(.+)", t, re.IGNORECASE)
    if m:
        t = f"({m.group(2)}) % ({m.group(1)}) == 0"
    t = re.sub(r"(?<![<>=!])=(?!=)", "==", t)
    if not re.search(r"\bn\b", t):
        return None, start, "the claim does not mention n"
    if E.safe_predicate(t) is None:
        return None, start, f"{t!r} is not an expression the evaluator reads"
    return t, start, ""


def _scales_within_bound(expr: str, start: int) -> Tuple[List[int], Optional[int]]:
    """The scales of :data:`CONJECTURE_SCALES` a free conjecture can be read
    at within :data:`CONJECTURE_BUDGET`, and the first scale it cannot
    (``None`` when every scale fits).  Each scale is read as the engine reads
    it, from ``start``; a counterexample ends the reading at its scale (the
    engine refutes the claim there)."""
    budget = [CONJECTURE_BUDGET]
    f = E.safe_predicate(expr, budget=budget)
    done: List[int] = []
    for N in CONJECTURE_SCALES:
        try:
            for n in range(start, start + N):
                if not f(n):
                    return done + [N], None
        except E.WorkBound:
            return done, N
        done.append(N)
    return done, None


def _registered(key: str) -> Answer:
    dom = E.GeneralDomain()
    eng = E.Engine(use_ledger=True)
    h = eng.add(dom.build(key, {}))
    eng.cascade(h)
    v = _verdict(h)
    truth = dom.truth(h)
    return (v["answer"] is not None or v["ring"] == "thinks true",
            "conjecture: " + _verdict_text(h.text, v), dict(v, claim=h.text, truth=truth))


def conjecture_text(arg: str) -> Answer:
    """``tool conjecture ...`` (see the module docstring)."""
    a = " ".join(arg.split())
    if not a:
        return _finish(True, "conjecture: a claim about every n, read at five nested scales "
                       f"{list(CONJECTURE_SCALES)} (a counterexample refutes it; surviving every "
                       "read is never proof); or a registered claim: "
                       + ", ".join(REGISTRY), {"status": "usage", "registry": list(REGISTRY)})
    key = REGISTRY.get(a.lower())
    if key is not None:
        return _finish(*_registered(key))
    expr, start, why = parse_conjecture(a)
    if expr is None:
        return _finish(False, f"conjecture: refused -- {why}; write a predicate in n, e.g. "
                       "'isprime(n**2 + n + 41) for every n' or 'n**2 % 4 in (0, 1)'",
                       {"status": "refused", "claim": a})
    try:
        scales, stopped = _scales_within_bound(expr, start)
    except (ArithmeticError, ValueError, TypeError, RecursionError) as exc:
        return _finish(False, f"conjecture: refused -- {expr!r} cannot be evaluated "
                       f"({type(exc).__name__})", {"status": "refused", "claim": a})
    if not scales:
        return _finish(False, f"conjecture: refused -- reading {expr!r} at the first scale "
                       f"({CONJECTURE_SCALES[0]} values of n) exceeds the work bound "
                       f"({CONJECTURE_BUDGET} units)", {"status": "refused", "claim": a,
                                                         "expression": expr})
    f = E.safe_predicate(expr)
    h = E.Hypothesis("", "CLAIM.tool", a, "Pi1", "general", "tool")
    h.check = lambda N, f=f, lo=start: E._forall(range(lo, lo + N), f, lambda n: f"n = {n} fails")
    h.scales = list(scales)
    eng = E.Engine(use_ledger=True)
    eng.add(h)
    try:
        eng.cascade(h)
    except (ArithmeticError, ValueError, TypeError, RecursionError) as exc:
        return _finish(False, f"conjecture: refused -- {expr!r} cannot be evaluated "
                       f"({type(exc).__name__})", {"status": "refused", "claim": a})
    v = _verdict(h)
    text = "conjecture: " + _verdict_text(f"{expr} for every n >= {start}", v)
    if stopped is not None:
        text += (f"; read at the scales {scales} only: the read at {stopped} values would "
                 f"exceed the work bound, so nothing is said about it")
    return _finish(v["answer"] is not None or v["ring"] == "thinks true", text,
                   dict(v, claim=a, expression=expr, start=start, scales=list(scales),
                        stopped_at=stopped))


# ---------------------------------------------------------------------------
# tool arc: the plan search after the colour solver
# ---------------------------------------------------------------------------

def arc_plan(train: List[dict], test_input: List[List[int]]) -> Tuple[Optional[tuple], List[str], str]:
    """The engine's plan search on one test input: ``(answer or None,
    programs, note)``; an answer only when every consistent program of least
    depth agrees."""
    demos = [(E.G(p["input"]), E.G(p["output"])) for p in train]
    return E.solve_arc(demos, E.G(test_input), list(E.STEP_LIBRARY))


def _grid(g) -> str:
    return "/".join("".join(str(v) for v in row) for row in g)


def arc_combined_text(name: str) -> Answer:
    """``tool arc NAME``: the colour solver's answer where it answers; where it
    refuses a test input, the engine's plan search; every answer graded
    against the stored output.  The colour solver's text is returned
    unchanged when it answers every test input."""
    from . import colour_induction as ci
    task = ci.arc_task(name.strip())
    if task is None:
        return ci.arc_text(name)
    ok, text, fig = ci.arc_text(name)
    r = ci.arc_solve(task)
    refused = [i for i, t in enumerate(r["tests"]) if t["grade"] == "refused"]
    if not refused:
        return ok, text, fig
    rows = []
    for i, t in enumerate(r["tests"]):
        want = task["test"][i].get("output")
        if i not in refused:
            rows.append({"test": i, "solver": "colour", "grade": t["grade"]})
            continue
        ans, progs, note = arc_plan(task["train"], task["test"][i]["input"])
        grade = ("refused" if ans is None else "unchecked" if want is None
                 else "right" if ans == E.G(want) else "wrong")
        rows.append({"test": i, "solver": "plan search", "grade": grade, "note": note,
                     "programs": progs[:3], "answer": None if ans is None else _grid(ans)})
    counts = {g: sum(1 for x in rows if x["grade"] == g) for g in ("right", "wrong", "refused")}
    status = ("wrong" if counts["wrong"] else
              "right" if counts["right"] == len(rows) else "refused")
    parts = []
    for x in rows:
        if x["solver"] == "colour":
            parts.append(f"test {x['test'] + 1}: {x['grade'].upper()} by the colour solver")
        elif x["grade"] == "refused":
            parts.append(f"test {x['test'] + 1}: refused by both (plan search: {x['note']})")
        else:
            parts.append(f"test {x['test'] + 1}: {x['answer']} -- {x['grade'].upper()} by the "
                         f"plan search ({', '.join(x['programs'])}; {x['note']})")
    head = {"right": "RIGHT", "wrong": "WRONG", "refused": "refused"}[status]
    out = (f"arc {name.strip()}: {head} from {r['demonstrations']} training pairs; the colour "
           f"solver of tool induce refused {len(refused)} of {len(rows)} test input(s), which went "
           f"to the hypothesis engine's plan search (an answer only when every consistent program "
           f"of least depth agrees); {'; '.join(parts)} (each answer graded against the stored "
           f"output)")
    figures = {"status": status, "task": name.strip(), "tests": len(rows),
               "answered": len(rows) - counts["refused"], **counts,
               "solvers": [x["solver"] for x in rows], "rows": rows}
    if any(x["solver"] == "plan search" and x["grade"] != "refused" for x in rows):
        return _finish(status == "right", out, figures)
    return status == "right", out, figures
