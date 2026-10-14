"""``glm_universal.evaluation.tool_verdicts_cases`` -- the Phase 138 cases
(``studies/TOOL_VERDICTS_STUDY.md``).

Two held-out sets, written **before** any reader of this phase existed and
committed on their own, so that neither the new verdict readers nor the
widened value patterns could be fitted to them:

* :data:`REWORDINGS_TWO` -- sixteen fresh rewordings of tool values (the
  follow-up to Phase 137's twelve, two of which were not read).  Expected
  values were computed independently of the GLM (a 200-digit Machin / series
  / integer-square-root computation of the reals, their continued fractions,
  convergents and an exhaustive nearest-fraction search), and the three
  lattice/moonshine values were read off the GLM's own canonical phrasing.
* :data:`VERDICTS_HELD_OUT` -- fourteen questions that use a tool's yes/no
  answer: as the answer, as the test of a conditional, and as the stopping
  test of a search.

``None`` as the expected value means the question should be **refused**.
"""

from __future__ import annotations

from typing import Optional, Tuple

#: ``(id, question, expected answer or None for a refusal)``.
REWORDINGS_TWO: Tuple[Tuple[str, str, Optional[str]], ...] = (
    ("r01", "the third partial quotient of e", "2"),
    ("r02", "the convergent number 3 of sqrt(2)", "7/5"),
    ("r03", "the 5th coefficient in the continued fraction expansion of pi",
     "292"),
    ("r04", "the denominator of convergent 6 of e", "32"),
    ("r05", "the numerator of the third convergent of phi", "3"),
    ("r06", "the sum of the first four partial quotients of sqrt(3)", "5"),
    ("r07", "the fraction closest to e with denominator at most 50",
     "106/39"),
    ("r08", "the best rational approximation of pi with a denominator below "
     "100", "311/99"),
    ("r09", "the largest of the first five partial quotients of pi", "292"),
    ("r10", "the kissing number of the 24-dimensional leech lattice",
     "196560"),
    ("r11", "the number of norm 6 vectors in the leech lattice", "16773120"),
    ("r12", "the 2nd term of the continued fraction for sqrt(7)", "1"),
    ("r13", "convergent 2 of pi", "22/7"),
    ("r14", "the fourth partial quotient in the expansion of e", "1"),
    ("r15", "the dimension of v2 of the moonshine module", "196884"),
    ("r16", "the minimum number of gate moves to go from 0x7 to 0x3", "1"),
)

#: ``(id, question, expected answer or None for a refusal)``.
VERDICTS_HELD_OUT: Tuple[Tuple[str, str, Optional[str]], ...] = (
    ("v01", "is 0xff reachable from 0x0 by gate moves", "False"),
    ("v02", "can 0x7 reach 0x3 by gate moves", "True"),
    ("v03", "is 355/113 the closest fraction to pi with denominator at most "
     "1000", "True"),
    ("v04", "is 22/7 the best rational approximation of pi with denominator "
     "at most 100", "False"),
    ("v05", "if 0x3 is reachable from 0x7, the number of gate moves from 0x7 "
     "to 0x3, otherwise 0", "1"),
    ("v06", "if 0xff is reachable from 0x0, the number of gate moves from "
     "0x0 to 0xff, otherwise -1", "-1"),
    ("v07", "if 113 is prime, 1, otherwise 0", "1"),
    ("v08", "the first convergent of pi whose denominator is above 1000",
     "103993/33102"),
    ("v09", "the first convergent of sqrt(2) whose denominator exceeds 100",
     "239/169"),
    ("v10", "the first convergent of e with denominator greater than 30",
     "87/32"),
    ("v11", "is the third term of the continued fraction of e equal to 2",
     "True"),
    ("v12", "is 7 the second term of the continued fraction of pi", "True"),
    ("v13", "the first convergent of 22/7 whose denominator is above 100",
     None),
    ("v14", "if 0xff is reachable from 0x0, 1, otherwise the number of gate "
     "moves from 0x0 to 0xff", None),
)


# ---------------------------------------------------------------------------
# The measurement (marks T1-T6 of studies/TOOL_VERDICTS_STUDY.md §4)
# ---------------------------------------------------------------------------

LEAN_FILE = "RequestProject/GLM/NearestFraction.lean"
LEAN_THEOREMS = ("farey_denominator", "endpoint_nearest", "farey_certificate",
                 "complete_quotient", "conv_denominators",
                 "between_candidates", "nearest_fraction_candidates",
                 "conv_denominators_fib", "search_terminates")

#: ``(written real, bound)`` -- the Farey certificate far past the old
#: exhaustive bound of 20,000 (mark T6).
LARGE_BOUNDS: Tuple[Tuple[str, int], ...] = tuple(
    (x, n) for x in ("pi", "e", "sqrt(2)", "(1+sqrt(5))/2", "sqrt(7)")
    for n in (20001, 10 ** 6, 10 ** 12, 10 ** 30, 10 ** 60))


def _row(r, want: Optional[str]) -> dict:
    from .tool_values_cases import _verdict
    got = _verdict(r)
    ok = got == "refuse" if want is None else got == want
    return {"got": got, "want": want, "ok": ok, "surface": r.surface}


def measure(scripts: bool = True) -> dict:
    """The marks T1-T6."""
    from pathlib import Path
    from ..reasoning import exact_real as xr
    from ..reasoning import rational_approx as ra
    from ..runtime import router
    from ..runtime import stepwise as sw
    from ..runtime import tool_values as tv
    from ..runtime.session import GeometricSession
    from . import connected_cases as cc
    from . import stepwise_cases as sc_cases
    from . import tool_values_cases as tvc

    marks: dict = {}
    session = GeometricSession()

    # T1 -- the Lean file
    lean = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    text = lean.read_text(encoding="utf-8") if lean.exists() else ""
    missing = [t for t in LEAN_THEOREMS if f"theorem {t} " not in text]
    marks["T1"] = {"file": LEAN_FILE, "missing": missing,
                   "sorry": "sorry" in text,
                   "met": bool(text) and not missing and "sorry" not in text}

    # T2 -- the verdict held-out set, through the router
    rows = []
    for cid, question, want in VERDICTS_HELD_OUT:
        rows.append(dict(_row(router.route(session, question), want),
                         id=cid, question=question))
    marks["T2"] = {"questions": len(rows), "as_expected":
                   sum(r["ok"] for r in rows), "rows": rows,
                   "met": all(r["ok"] for r in rows)}

    # T3 -- column 3 on every answered verdict chain, and its mutations
    if scripts:
        from ..reasoning import stepwise_script as ss
        from ..runtime.python_tct import run_column3
        from ..runtime.tct_engine import package_root
        root = str(package_root())
        chains = verified = built = caught = 0
        for _cid, question, want in VERDICTS_HELD_OUT:
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
        marks["T3"] = {"chains": chains, "verified": verified,
                       "mutants": built, "caught": caught,
                       "met": chains > 0 and verified == chains
                       and caught == built}
    else:
        marks["T3"] = {"skipped": True, "met": False}

    # T4 -- the fresh rewordings: none wrong, and Phase 137's two misses read
    hrows = []
    for cid, question, want in REWORDINGS_TWO:
        hrows.append(dict(_row(router.route(session, question), want),
                          id=cid, question=question))
    wrong = [h for h in hrows if h["got"] != "refuse" and not h["ok"]]
    old = [tvc.HELD_OUT[0], tvc.HELD_OUT[2]]     # Phase 137's two misses
    old_rows = [_row(router.route(session, q), w) for q, w in old]
    marks["T4"] = {"questions": len(hrows),
                   "read": sum(h["got"] != "refuse" for h in hrows),
                   "right": sum(h["ok"] for h in hrows), "wrong": wrong,
                   "rows": hrows, "phase137_misses": len(old_rows),
                   "phase137_now_right": sum(r["ok"] for r in old_rows),
                   "met": not wrong and len(old_rows) == 2
                   and all(r["ok"] for r in old_rows)}

    # T5 -- non-interference: no declared text reads as a verdict, and the
    # stepwise corpus answers as before with the verdicts switched off
    sets = router._declared_sets()
    texts = [t for v in sets.values() for t in v] + \
        [t for t, _ in cc.ROUTED_MIXED]
    matched = [t for t in texts if tv.read_verdict(t) is not None]
    corpus = [q for _cid, q, *_ in sc_cases.COMPOSITION_CASES]
    sw.TOOL_VERDICTS = False
    try:
        before = [sw.answer(session, q).summary() for q in corpus]
    finally:
        sw.TOOL_VERDICTS = True
    after = [sw.answer(session, q).summary() for q in corpus]
    moved = [q for q, b, a in zip(corpus, before, after) if b != a]
    marks["T5"] = {"declared_texts": len(texts), "matched": matched,
                   "corpus": len(corpus), "moved": moved,
                   "met": not matched and not moved}

    # T6 -- the Farey certificate: on the Phase 137 grid it agrees with the
    # exhaustive search, and far past the old bound every answer carries it
    grid = []
    for x, n in tvc.APPROX_GRID:
        real = xr.parse_real(x)
        got = ra.best_approximation(real, n)
        ex = ra.exhaustive_nearest(real, n)
        grid.append(got["ok"] and "certificate" in got and ex is not None
                    and got["value"] == ex["value"])
    large = []
    for x, n in LARGE_BOUNDS:
        got = ra.best_approximation(xr.parse_real(x), n)
        large.append(bool(got["ok"]) and got.get("certificate", {}).get("ok"))
    marks["T6"] = {"grid": len(grid), "grid_agree": sum(grid),
                   "large": len(large), "large_certified": sum(large),
                   "met": all(grid) and all(large)}

    return {"marks": marks,
            "met": sum(bool(m["met"]) for m in marks.values()),
            "taken": len(marks)}
