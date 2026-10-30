"""``glm_universal.reasoning.pi_machine_study`` -- the marks of
``studies/PI_MACHINE_STUDY.md`` (Phase 166): the machine sums ``pi``.

*Created 19 October 2026.*

Since Phase 163 the batch machine GLM-BAT computed ``e`` and ``sqrt(m)`` but
held ``pi`` as a declared constant (Mathlib's twenty-digit decimals).  Phase
166 has it sum ``pi`` by Machin's formula
(:func:`glm_universal.reasoning.tool_machine.pi_lines`), by rules proved in
``RequestProject/GLM/PiMachine.lean``.  What is measured:

* **L1** -- the Lean file states the theorems of the study and has no
  ``sorry`` (the build itself is ``lake build RequestProject.GLM.PiMachine``).
* **M1** -- the machine, run on :func:`pi_lines`, halts with exit 0 and
  leaves exactly the four integers of ``piEnds 40 12``
  (:func:`tool_machine.pi_ends`, the Python mirror); the mirror agrees with
  the value Lean itself evaluates for ``piEnds 3 1`` (:data:`LEAN_EVAL_3_1`).
* **M2** -- the summed enclosure lies strictly inside Mathlib's twenty-digit
  decimals (two proved enclosures of the same number, one nested in the
  other) and is narrower than :data:`WIDTH_CAP`.
* **M3** -- the continued-fraction terms certified by Euclid's algorithm in
  lockstep on the two ends: at least as many as the declared constant
  certifies, at least the :data:`MAX_TERM` the tool answers, and every one
  equal to the tool's own term.
* **C1** -- the control: Machin's formula with ``239`` replaced by ``237``,
  summed by the same loop and widened by the same bound, gives an interval
  disjoint from Mathlib's decimals; so a wrong formula is caught by the
  proved constant, not passed.
* **K1** -- one-step chains asking the ``pi`` tools (convergents 1 to
  :data:`MAX_CONVERGENT`, the term at every index below :data:`MAX_TERM`,
  the nearest fraction under ten bounds) run with :data:`PI_SUMMED` off and
  on: every chain the declared constant admits is admitted by the summed
  enclosure with the same value, and no chain the tool refuses is written.

Exactness
---------
Integers, :class:`fractions.Fraction`, strings, booleans.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from . import tool_machine as tm

__all__ = [
    "LEAN_EVAL_3_1", "WIDTH_CAP", "MAX_CONVERGENT", "MAX_TERM", "BOUNDS",
    "switch", "lockstep_terms", "machine_marks", "enclosure_marks",
    "term_marks", "control_marks", "chain_marks", "pi_machine_marks",
]

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / tm.PI_LEAN_FILE

#: ``#eval GLM.PiMachine.piEnds 3 1``, each end as Lean prints it (reduced).
LEAN_EVAL_3_1: Tuple[Tuple[int, int], Tuple[int, int]] = (
    (70364361601808, 22397679609375), (23455225520344, 7465893203125))

#: M2: the summed enclosure is narrower than this.
WIDTH_CAP: Fraction = Fraction(1, 10 ** 56)

#: K1: the questions asked.
MAX_CONVERGENT: int = 30
MAX_TERM: int = 40
BOUNDS: Tuple[int, ...] = tuple(10 ** k for k in range(1, 11))


@contextmanager
def switch(on: bool) -> Iterator[None]:
    """:data:`tool_machine.PI_SUMMED`, set for the block and restored after."""
    old = tm.PI_SUMMED
    tm.PI_SUMMED = on
    try:
        yield
    finally:
        tm.PI_SUMMED = old


def _sci(x: Fraction, digits: int = 4) -> str:
    """A positive fraction in scientific notation with ``digits``
    significant digits, rounded down, by integer arithmetic only."""
    if x <= 0:
        return "0"
    e = len(str(x.numerator)) - len(str(x.denominator))
    while Fraction(10) ** e > x:
        e -= 1
    while Fraction(10) ** (e + 1) <= x:
        e += 1
    m = x / Fraction(10) ** (e - digits + 1)
    q = m.numerator // m.denominator
    t = str(q)
    return f"{t[0]}.{t[1:]}e{e:+03d}"


def _declared() -> Tuple[Fraction, Fraction]:
    return Fraction(*tm.PI_LOW), Fraction(*tm.PI_HIGH)


def _summed(terms: Optional[Tuple[int, int]] = None) -> Tuple[Fraction, Fraction]:
    lo, hi = tm.pi_ends(*(terms or tm.PI_TERMS))
    return Fraction(*lo), Fraction(*hi)


def lockstep_terms(lo: Fraction, hi: Fraction, cap: int = 200) -> List[int]:
    """Euclid's algorithm on both ends in lockstep: the terms on which the two
    runs agree (``GLM.ToolMachine.lockstep_certified``)."""
    a, b, c, d = lo.numerator, lo.denominator, hi.numerator, hi.denominator
    out: List[int] = []
    while b and d and len(out) < cap:
        q1, q2 = a // b, c // d
        if q1 != q2:
            break
        out.append(q1)
        a, b = b, a - q1 * b
        c, d = d, c - q2 * d
    return out


def lean_marks() -> Dict[str, object]:
    text = _LEAN.read_text(encoding="utf-8") if _LEAN.exists() else ""
    stated = [n for n in tm.PI_LEAN_THEOREMS if f"theorem {n}" in text]
    return {"file": tm.PI_LEAN_FILE, "present": bool(text),
            "theorems": len(stated), "declared": len(tm.PI_LEAN_THEOREMS),
            "sorry": "sorry" in text,
            "met": bool(text) and len(stated) == len(tm.PI_LEAN_THEOREMS)
            and "sorry" not in text}


def machine_marks() -> Dict[str, object]:
    from . import batch_machine as bm
    run = bm.run_program(bm.parse_program(tm.pi_lines(0)))
    env = run.env
    got = tuple((int(env[n]), int(env[d]))
                for n, d in (("XLA", "XLB"), ("XUA", "XUB")))
    want = tm.pi_ends(*tm.PI_TERMS)
    mirror = tuple(tuple(int(v) for v in (Fraction(*e).numerator,
                                          Fraction(*e).denominator))
                   for e in tm.pi_ends(3, 1))
    return {"status": run.status, "exit": run.exit_code, "steps": run.steps,
            "lines": len(tm.pi_lines(0)), "terms": list(tm.PI_TERMS),
            "ends_equal": got == want, "lean_eval_equal":
            mirror == LEAN_EVAL_3_1,
            "met": run.status == "halted" and run.exit_code == 0
            and got == want and mirror == LEAN_EVAL_3_1}


def enclosure_marks() -> Dict[str, object]:
    dlo, dhi = _declared()
    slo, shi = _summed()
    width = shi - slo
    nested = dlo < slo and shi < dhi
    return {"declared_width": _sci(dhi - dlo),
            "summed_width": _sci(width), "nested": nested,
            "under_cap": width < WIDTH_CAP,
            "met": nested and width < WIDTH_CAP}


def term_marks() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    dec = lockstep_terms(*_declared())
    summ = lockstep_terms(*_summed())
    n = len(summ)
    asked = min(n, MAX_TERM)
    got = run_tool(f"tool continued fraction pi terms {asked}")
    tool = list(got.figures.get("terms", [])) if got.ok else []
    agree = tool == summ[:len(tool)] if tool else None
    return {"declared_terms": len(dec), "summed_terms": n,
            "prefix": dec == summ[:len(dec)], "tool_terms": len(tool),
            "tool_agrees": agree,
            "met": n >= len(dec) and dec == summ[:len(dec)]
            and n >= MAX_TERM and agree is True}


def control_marks() -> Dict[str, object]:
    """C1: ``239`` replaced by ``237`` in Machin's formula."""
    a, b = tm.PI_TERMS
    p5, q5 = tm._horner(5, a)
    p2, q2 = tm._horner(237, b)
    s = 16 * Fraction(p5, 5 * q5) - 4 * Fraction(p2, 237 * q2)
    e = 16 * Fraction(1, (2 * a + 1) * 5 ** (2 * a + 1)) + \
        4 * Fraction(1, (2 * b + 1) * 237 ** (2 * b + 1))
    lo, hi = s - e, s + e
    dlo, dhi = _declared()
    disjoint = hi < dlo or lo > dhi
    return {"wrong_formula": "16 arctan(1/5) - 4 arctan(1/237)",
            "distance": _sci(min(abs(lo - dhi), abs(dlo - hi))),
            "disjoint": disjoint, "met": disjoint}


def _chain(tool: str, rec: List[str]):
    from ..runtime.toolbox import run_tool
    from ..runtime import tool_values as tv
    from .stepwise_script import Chain, Step
    got = run_tool(tool)
    try:
        if rec[0] == "tool":
            if not got.ok:
                raise ValueError(got.text)
            value = tv.select(got.figures, rec[2:])
        else:
            value = tv.verdict_of_figures(got.ok, got.figures, rec[2:])
    except ValueError:
        value = None
    detail = {"computation": "pi machine", "question": tool, "recompute": rec}
    claim = value if value is not None else Fraction(0)
    step = Step(1, "planned", (), claim, tool, detail)
    return Chain("pi machine", (step,), "composition"), value


def _questions() -> List[Tuple[str, List[str]]]:
    from ..runtime.toolbox import run_tool
    qs: List[Tuple[str, List[str]]] = []
    for k in range(1, MAX_CONVERGENT + 1):
        t = f"tool convergent {k} of pi"
        qs.append((t, ["tool", t, "value", "value"]))
    full = run_tool(f"tool continued fraction pi terms {MAX_TERM}")
    terms = list(full.figures.get("terms", [])) if full.ok else []
    for j in range(MAX_TERM):
        t = f"tool continued fraction pi terms {j + 1}"
        true = terms[j] if j < len(terms) else 0
        qs.append((t, ["verdict", t, "equals", "index", "terms", str(j),
                       str(true)]))
    for n in BOUNDS:
        t = f"tool best approximation pi denominator {n}"
        qs.append((t, ["tool", t, "value", "value"]))
    return qs


def chain_marks() -> Dict[str, object]:
    from . import planner_ladder as pl
    m = {"questions": 0, "tool_answers": 0, "declared_admitted": 0,
         "summed_admitted": 0, "lost": 0, "gained": 0, "wrote_unanswered": 0,
         "max_steps": 0}
    lost: List[str] = []
    gained: List[str] = []
    for tool, rec in _questions():
        chain, value = _chain(tool, rec)
        m["questions"] += 1
        res = {}
        for on in (False, True):
            with switch(on):
                c = pl.check_chain(chain, say=False, read=True, files={})
            res[on] = c
            if on:
                m["max_steps"] = max(m["max_steps"],
                                     int(c["machine_steps"] or 0))
        if value is None:
            wrote = res[True]["status"] == "halted" and \
                res[True]["exit"] == 0 and 1 in res[True]["computed"]
            m["wrote_unanswered"] += wrote
            continue
        m["tool_answers"] += 1
        d = bool(res[False]["admitted"] and 1 in res[False]["computed"])
        s = bool(res[True]["admitted"] and 1 in res[True]["computed"])
        m["declared_admitted"] += d
        m["summed_admitted"] += s
        if d and not s:
            m["lost"] += 1
            lost.append(tool)
        if s and not d:
            m["gained"] += 1
            gained.append(tool)
    m["lost_questions"] = lost
    m["gained_questions"] = gained
    m["met"] = m["lost"] == 0 and m["wrote_unanswered"] == 0 and \
        m["summed_admitted"] == m["tool_answers"]
    return m


def pi_machine_marks(chains: bool = True) -> Dict[str, object]:
    """Every mark of the study, recomputed live."""
    out = {"L1": lean_marks(), "M1": machine_marks(),
           "M2": enclosure_marks(), "M3": term_marks(),
           "C1": control_marks()}
    if chains:
        out["K1"] = chain_marks()
    out["met"] = sum(1 for v in out.values()
                     if isinstance(v, dict) and v.get("met"))
    out["marks"] = sum(1 for v in out.values() if isinstance(v, dict))
    return out
