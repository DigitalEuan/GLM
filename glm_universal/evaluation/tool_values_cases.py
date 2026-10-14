"""``glm_universal.evaluation.tool_values_cases`` -- the declared batteries of
the tool-values round (Phase 137).

``studies/TOOL_VALUES_STUDY.md`` §3 declares them.  Phase 137 lets the stepwise
planner take a number from a tool (:mod:`glm_universal.runtime.tool_values`)
for a part the typed planner refuses, adds two tools that answer with a
fraction (``convergent``, ``best approximation``;
:mod:`glm_universal.reasoning.rational_approx`), and lets a question that is
one tool value reach the toolbox after every surface refused.  This module
holds what that is measured against:

* :data:`COMPOSED` -- compound questions, each with its exact value or
  ``"refuse"``;
* :data:`SINGLE` -- questions that are one tool value;
* :data:`HELD_OUT` -- rewordings written before they were run, with the value
  each should get; the study records how many are read, whatever it is;
* :data:`APPROX_GRID` -- reals and bounds for the exhaustive check;
* :func:`measure` -- the marks V1-V8 of the study, taken.

Exact throughout: integers and ``Fraction``.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, isqrt
from typing import Dict, List, Tuple

__all__ = ["COMPOSED", "SINGLE", "HELD_OUT", "APPROX_GRID", "LEAN_FILE",
           "LEAN_THEOREMS", "measure"]

#: ``(question, value or "refuse")`` -- a tool value composed with arithmetic,
#: a predicate or a function form.
COMPOSED: Tuple[Tuple[str, str], ...] = (
    ("twice the third term of the continued fraction of pi", "30"),
    ("the fourth convergent of pi minus 3", "16/113"),
    ("is the sum of the first 5 terms of the continued fraction of sqrt(2) "
     "prime", "not prime"),
    ("the gcd of the numerator of the fourth convergent of pi and 71", "71"),
    ("the kissing number of the Leech lattice divided by 24", "8190"),
    ("the closest fraction to sqrt(2) with denominator at most 100 times 99",
     "140"),
    ("the fifth term of the continued fraction of pi plus 8", "300"),
    ("the denominator of the fifth convergent of e times 2", "14"),
    ("the largest of the first 10 terms of the continued fraction of pi "
     "minus the third term of the continued fraction of pi", "277"),
    ("is the numerator of the third convergent of sqrt(3) prime", "prime"),
    ("the number of gate moves from 0x000007 to 0x000005 plus 1", "3"),
    ("the lcm of the denominator of the fourth convergent of pi and 7",
     "791"),
    ("the product of the first 4 terms of the continued fraction of e "
     "divided by 2", "2"),
    # refusals: the tool refuses, so the step and the chain do
    ("twice the 50th term of the continued fraction of pi", "refuse"),
    ("the third term of the continued fraction of banana plus 1", "refuse"),
    ("the number of gate moves from 0x000006 to 0x000004 plus 1", "refuse"),
    ("the fourth convergent of 7/3 plus 1", "refuse"),
)

#: ``(question, fragment)`` -- one tool value asked alone.
SINGLE: Tuple[Tuple[str, str], ...] = (
    ("what is the fifth term of the continued fraction of e", "is 1,"),
    ("what is the fourth convergent of pi", "is 355/113,"),
    ("what is the closest fraction to pi with denominator at most 1000",
     "is 355/113,"),
    ("the nearest fraction to e with denominator below 100", "is 193/71,"),
    ("what is the sum of the first 10 terms of the continued fraction of "
     "(1+sqrt(5))/2", "is 10,"),
    ("what is the denominator of the 6th convergent of sqrt(2)", "is 70,"),
    ("the number of vectors of norm 8 in the Leech lattice", "is 398034000,"),
    ("what is the dimension of V_3", "is 21493760,"),
)

#: ``(question, value)`` -- rewordings written before the round ran them
#: (Phase 137, §3.3).  Not tuned after: the study reports how many are read.
HELD_OUT: Tuple[Tuple[str, str], ...] = (
    ("three times the second partial quotient of pi", "21"),
    ("what's the 2nd coefficient in the continued fraction expansion of pi "
     "plus one", "8"),
    ("the convergent number 4 of pi minus 3", "16/113"),
    ("the best rational approximation of sqrt(3) with denominator up to 50 "
     "plus 1", "112/41"),
    ("half the 4th term of the continued fraction of e", "1/2"),
    ("the mean of the first 4 terms of the continued fraction of sqrt(7)",
     "5/4"),
    ("is the 3rd convergent of pi bigger than 3", "True"),
    ("the minimum number of reversible gate moves from 0x000007 to 0x000003 "
     "times 10", "10"),
    ("the numerator of the closest fraction to pi with a denominator under "
     "100 squared", "96721"),
    ("the second convergent of the golden ratio plus 1", "3"),
    ("the smallest of the first 6 entries of the continued fraction of "
     "sqrt(19)", "1"),
    ("the denominator of the fourth convergent to pi plus the numerator of "
     "the fourth convergent to pi", "468"),
)

#: The three values of :data:`HELD_OUT` that were written wrongly by hand
#: before the round ran (the GLM's answers differed from them).  Each is
#: re-derived in :func:`measure` without continued fractions or the GLM's
#: tools, and the sheet holds the re-derived value: ``question -> (as written,
#: corrected)``.  ``studies/TOOL_VALUES_STUDY.md`` §5.3 records it.
HELD_OUT_CORRECTED: Dict[str, Tuple[str, str]] = {
    HELD_OUT[3][0]: ("123/41", "112/41"),
    HELD_OUT[5][0]: ("7/4", "5/4"),
    HELD_OUT[8][0]: ("97344", "96721"),
}

#: ``(written real, bound)`` -- the exhaustive check's grid (mark V5).
APPROX_GRID: Tuple[Tuple[str, int], ...] = tuple(
    (x, n) for x in ("pi", "e", "sqrt(2)", "sqrt(3)", "sqrt(5)", "2^(1/3)",
                     "(1+sqrt(5))/2", "pi^2", "sqrt(11)/3", "1/7+sqrt(2)")
    for n in (1, 2, 3, 7, 10, 50, 113, 500, 1000, 4000))

LEAN_FILE = "RequestProject/GLM/ToolValues.lean"

#: The theorems of :data:`LEAN_FILE` (mark V1).
LEAN_THEOREMS: Tuple[str, ...] = (
    "cfPrefix_length", "cfPrefix_take", "cfPrefix_getElem",
    "select_certified", "fold_certified", "conv_append", "conv_cons",
    "det_cvM", "conv_det", "conv_coprime", "conv_pos", "cfValue_eq_conv",
    "closer_iff_midpoint", "nearer_of_margin", "farther_than_candidate",
    "conv_pi_four",
)


def _sqrt_cf(n: int, count: int) -> Tuple[int, ...]:
    """The continued fraction of ``sqrt(n)`` by the integer recurrence."""
    r = isqrt(n)
    p, q, out = 0, 1, []
    for _ in range(count):
        a = (p + r) // q
        out.append(a)
        p = a * q - p
        q = (n - p * p) // q
    return tuple(out)


def _convergent_by_value(terms) -> Fraction:
    """The value of a finite continued fraction, folded from the right."""
    v = Fraction(terms[-1])
    for a in reversed(terms[:-1]):
        v = a + 1 / v
    return v


def _verdict(r) -> str:
    """The value a routed answer states, or ``refuse``."""
    import re
    if not r.answered:
        return "refuse"
    a = r.payload if r.surface == "planner" else None
    if a is not None and getattr(a, "chain", None) is not None:
        return a.value
    m = re.match(r".*? is (-?\d+(?:/\d+)?), selected \(", r.text)
    return m.group(1) if m else r.text


def _held_out_rederived() -> Dict[str, bool]:
    """The corrected held-out values, re-derived without continued
    fractions: the nearest fractions by trying every denominator over a
    rational reading of the real, the terms of sqrt(7) by the integer
    recurrence."""
    from ..reasoning import exact_real as xr
    from ..reasoning import rational_approx as ra
    s3 = ra.exhaustive_nearest(xr.parse_real("sqrt(3)"), 50)["value"]
    pi99 = ra.exhaustive_nearest(xr.parse_real("pi"), 99)["value"]
    s7 = _sqrt_cf(7, 4)
    return {HELD_OUT[3][0]: str(s3 + 1) == "112/41",
            HELD_OUT[5][0]: str(Fraction(sum(s7), 4)) == "5/4",
            HELD_OUT[8][0]: str(pi99.numerator ** 2) == "96721"}


def measure(scripts: bool = True) -> Dict[str, object]:
    """The marks V1-V8 of ``studies/TOOL_VALUES_STUDY.md`` §4."""
    from pathlib import Path
    from ..reasoning import exact_real as xr
    from ..reasoning import rational_approx as ra
    from ..reasoning import substrate_cognition as sc
    from ..runtime import router
    from ..runtime import stepwise as sw
    from ..runtime import tool_values as tv
    from ..runtime.session import GeometricSession
    from . import connected_cases as cc
    from . import connected_two_cases as c2
    from . import stepwise_cases as sc_cases

    marks: Dict[str, Dict[str, object]] = {}
    session = GeometricSession()

    # V1 -- the Lean file
    lean = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    text = lean.read_text(encoding="utf-8") if lean.exists() else ""
    missing = [t for t in LEAN_THEOREMS if f"theorem {t} " not in text]
    marks["V1"] = {"file": LEAN_FILE, "missing": missing,
                   "sorry": "sorry" in text,
                   "met": bool(text) and not missing and "sorry" not in text}

    # V2 -- the composed battery, through the router
    rows = []
    for question, want in COMPOSED:
        r = router.route(session, question)
        got = _verdict(r)
        rows.append({"question": question, "want": want, "got": got,
                     "surface": r.surface, "ok": got == want})
    marks["V2"] = {"questions": len(rows), "as_declared":
                   sum(r["ok"] for r in rows), "rows": rows,
                   "answered": sum(r["got"] != "refuse" for r in rows),
                   "met": all(r["ok"] for r in rows)}

    # V3 -- column 3: every answered composed chain verifies; every mutation
    # of it is caught
    if scripts:
        from ..reasoning import stepwise_script as ss
        from ..runtime.python_tct import run_column3
        from ..runtime.tct_engine import package_root
        root = str(package_root())
        verified, chains, built, caught = 0, 0, 0, 0
        for question, want in COMPOSED:
            a = sw.answer(session, question)
            if not a.answered:
                continue
            chains += 1
            verified += bool(run_column3(ss.render_script(a.chain, root))[
                "verified"])
            for _kind, data in ss.mutants(a.chain).items():
                built += 1
                caught += not run_column3(ss.render_script(
                    a.chain, root, data))["verified"]
        marks["V3"] = {"chains": chains, "verified": verified,
                       "mutants": built, "caught": caught,
                       "met": chains > 0 and verified == chains
                       and caught == built}
    else:
        marks["V3"] = {"skipped": True, "met": False}

    # V4 -- convergents against independent references
    crow = []
    for n in range(2, 41):
        if isqrt(n) ** 2 == n:
            continue
        ref = _sqrt_cf(n, 8)
        for k in (1, 3, 5, 8):
            g = __import__("glm_universal.runtime.toolbox",
                           fromlist=["run_tool"]).run_tool(
                f"tool convergent {k} of sqrt({n})")
            want = _convergent_by_value(ref[:k])
            v = Fraction(g.figures["value"]) if g.ok else None
            crow.append(g.ok and v == want and gcd(v.numerator,
                                                   v.denominator) == 1)
    pi_rows = []
    for k in range(1, 15):
        from ..runtime import toolbox as tb
        g = tb.run_tool(f"tool convergent {k} of pi")
        pi_rows.append(g.ok and Fraction(g.figures["value"]) ==
                       _convergent_by_value(c2.PI_TERMS[:k]))
    marks["V4"] = {"surd_cases": len(crow), "surd_agree": sum(crow),
                   "pi_cases": len(pi_rows), "pi_agree": sum(pi_rows),
                   "met": all(crow) and all(pi_rows)}

    # V5 -- best approximation against the exhaustive search
    arow = []
    for x, n in APPROX_GRID:
        real = xr.parse_real(x)
        got = ra.best_approximation(real, n)
        ex = ra.exhaustive_nearest(real, n)
        arow.append({"x": x, "bound": n, "ok": got["ok"] and ex is not None
                     and got["value"] == ex["value"],
                     "value": str(got.get("value"))})
    marks["V5"] = {"cases": len(arow), "agree": sum(r["ok"] for r in arow),
                   "disagree": [r for r in arow if not r["ok"]],
                   "met": all(r["ok"] for r in arow)}

    # V6 -- non-interference: the tool values read no declared text, and the
    # stepwise corpus answers as before with the tool values switched off
    sets = router._declared_sets()
    texts = [t for v in sets.values() for t in v] + \
        [t for t, _ in cc.ROUTED_MIXED]
    matched = [t for t in texts if tv.read_value(t) is not None]
    corpus = [q for _cid, q, *_ in sc_cases.COMPOSITION_CASES]
    sw.TOOL_VALUES = False
    try:
        before = [sw.answer(session, q).summary() for q in corpus]
    finally:
        sw.TOOL_VALUES = True
    after = [sw.answer(session, q).summary() for q in corpus]
    moved = [q for q, b, a in zip(corpus, before, after) if b != a]
    marks["V6"] = {"declared_texts": len(texts), "matched": len(matched),
                   "corpus": len(corpus), "moved": moved,
                   "met": not matched and not moved}

    # V7 -- one tool value asked alone, through the router
    srows = []
    for question, frag in SINGLE:
        r = router.route(session, question)
        srows.append({"question": question, "ok": r.answered and
                      r.surface == "toolbox" and frag in r.text})
    marks["V7"] = {"questions": len(srows),
                   "as_declared": sum(r["ok"] for r in srows),
                   "met": all(r["ok"] for r in srows)}

    # V8 -- the held-out rewordings: recorded, with a declared threshold
    hrows = []
    for question, want in HELD_OUT:
        r = router.route(session, question)
        got = _verdict(r)
        hrows.append({"question": question, "want": want, "got": got,
                      "read": got != "refuse", "right": got == want})
    wrong = [h for h in hrows if h["read"] and not h["right"]]
    rederived = _held_out_rederived()
    marks["V8"] = {"questions": len(hrows),
                   "read": sum(h["read"] for h in hrows),
                   "right": sum(h["right"] for h in hrows),
                   "wrong": wrong, "rows": hrows,
                   "corrected": len(HELD_OUT_CORRECTED),
                   "rederived": sum(rederived.values()),
                   "met": not wrong and all(rederived.values())
                   and sum(h["right"] for h in hrows) >= 8}

    _ = sc
    return {"marks": marks,
            "met": sum(bool(m["met"]) for m in marks.values()),
            "taken": len(marks)}
