"""``glm_universal.evaluation.connected_two_cases`` -- the declared batteries of
the second connected-machine round (Phase 136).

``studies/CONNECTED_MACHINE_TWO_STUDY.md`` §3 declares them.  Phase 136 puts
operations that studies measured but no question reached behind the toolbox
(:mod:`glm_universal.runtime.toolbox`), lets a refused English question reach a
tool through a declared opening (:data:`~glm_universal.runtime.toolbox.
TOOL_PHRASES`), and makes every reasoning module either reached from the
answering path or declared measurement-only (:func:`~glm_universal.runtime.
toolbox.wiring_census`).  This module holds what that is measured against:

* :data:`PHRASED` -- English questions, each with a fragment its answer must
  contain or ``"refuse"``;
* the independent checks of the two stream tools: the continued fraction of a
  quadratic irrational by the integer recurrence (no exact-real layer, no
  interval), and the continued fraction of ``e`` by its pattern;
* :func:`measure` -- the marks W1-W8 of the study, taken.

Exact throughout: integers and ``Fraction``.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Dict, List, Sequence, Tuple

__all__ = ["PHRASED", "TOOL_CASES", "PI_TERMS", "RATIONAL_EXPRESSIONS",
           "MOBIUS_CASES", "LEAN_FILE", "LEAN_THEOREMS", "quadratic_cf", "mobius_quadratic_cf", "e_terms",
           "measure"]


#: ``(question, fragment or "refuse")`` -- English the planner refuses, read by
#: a tool's declared opening, or left refused.
PHRASED: Tuple[Tuple[str, str], ...] = (
    ("what is the continued fraction of pi?", "[3, 7, 15, 1, 292"),
    ("continued fraction of sqrt(2)", "[1, 2, 2, 2"),
    ("expand sqrt(3) as a continued fraction", "[1, 1, 2, 1, 2"),
    ("the first 15 terms of the continued fraction of e",
     "1, 1, 8, 1, 1, 10]"),
    ("give me the continued fraction of (1+sqrt(5))/2", "[1, 1, 1, 1"),
    ("compute the continued fraction expansion of 355/113", "[3, 7, 16]"),
    ("how many tag bits are needed for distance 5", "at least 11 bits"),
    ("how many bits does a tag need for weight 3", "at least 9 bits"),
    ("what is the shortest tag for distance 1", "at least 7 bits"),
    ("can 0x000007 reach 0x000003 by reversible gates", "exactly 1 "),
    ("how many gate moves from 0x000007 to 0x000005", "exactly 2 "),
    ("bind causes C O in chemistry", "reads the filler back as O"),
    ("what happened to LAW_BIO_007", "the fate retired"),
    ("which reasoning modules can a query reach",
     "reached from the answering path"),
    # refusals: the opening is read, the tool refuses, the refusal stands
    ("continued fraction of banana", "refuse"),
    ("can 0x000006 reach 0x000004 by reversible gates", "refuse"),
    ("bind causes C Ba in chemistry", "refuse"),
    ("what happened to LAW_NOT_A_LAW", "refuse"),
    ("how many tag bits are needed for distance 0", "refuse"),
    # not an opening at all
    ("what is the colour of the continued sky", "refuse"),
)

#: ``(tool text, answers?, fragment)`` -- one question per new tool behaviour.
TOOL_CASES: Tuple[Tuple[str, bool, str], ...] = (
    ("tool continued fraction pi terms 12", True,
     "[3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1]"),
    ("tool continued fraction 355/113", True, "[3, 7, 16]"),
    ("tool continued fraction sqrt(4)", False, "only 0 of the 10"),
    ("tool continued fraction banana", False, "refused"),
    ("tool mobius 1 1 1 0 of sqrt(2)", True, "[1, 1, 2, 2, 2"),
    ("tool mobius 2 1 0 1 of pi terms 8", True, "[7, 3, 1, 1, 7, 2, 146, 3]"),
    ("tool mobius 1 2 2 4 of pi", False, "ad - bc = 0"),
    ("tool mobius 3 1 1 0 of 2/5", True, "11/2 exactly"),
    ("tool bind causes C O in chemistry", True, "0xc48506"),
    ("tool bind causes C Ba in chemistry", False, "ambiguous-recovery"),
    ("tool bind rhymes_with C O in chemistry", False, "unknown-role"),
    ("tool gates 0x000007 to 0x000005", True, "exactly 2 "),
    ("tool gates 0xffffff to 0xfedcbf", False, "applyWord_control"),
    ("tool gates 0x000006 to 0x000004", False, "gates_fix_of_control_clear"),
    ("tool tag length 5", True, "at least 11 bits"),
    ("tool tag length 7", True, "at least 13 bits"),
    ("tool tag length 0", False, "at least 1"),
    ("tool law register LAW_BIO_007", True, "the fate retired"),
    ("tool law register LAW_NOT_A_LAW", False, "nor of the 106"),
    ("tool wiring stray_blind", True, "reached by no query"),
    ("tool wiring role_binding", True, "answers `tool bind`"),
)

#: The first twenty terms of the continued fraction of pi, as published
#: (OEIS A001203) -- the one reference not recomputed here.
PI_TERMS: Tuple[int, ...] = (3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1,
                             1, 2, 2, 2, 2)

#: Rationals written as expressions: the exact-real layer cannot know they end,
#: so the tool must refuse past their last term and never emit a wrong one.
RATIONAL_EXPRESSIONS: Tuple[Tuple[str, Fraction], ...] = (
    ("sqrt(4)", Fraction(2)), ("sqrt(9)/2", Fraction(3, 2)),
    ("sqrt(2)*sqrt(2)", Fraction(2)), ("sqrt(49/4)", Fraction(7, 2)),
    ("(sqrt(2)+1)*(sqrt(2)-1)", Fraction(1)), ("sqrt(16)/5", Fraction(4, 5)),
)

#: ``(a, b, c, d, n)``: the transform ``(a X + b)/(c X + d)`` at ``X = sqrt(n)``.
MOBIUS_CASES: Tuple[Tuple[int, int, int, int, int], ...] = (
    (1, 1, 1, 0, 2), (1, 0, 0, 1, 3), (2, 1, 0, 1, 5), (1, -1, 1, 1, 2),
    (3, 2, 1, 4, 7), (0, 1, 1, 0, 11), (5, -3, 2, 1, 13), (1, 7, 2, -1, 6),
    (-1, 4, 1, 2, 10), (4, 1, -1, 3, 17), (2, -5, 3, 1, 19), (7, 0, 1, -2, 23),
)

N_TERMS = 20

LEAN_FILE = "RequestProject/GLM/CertifiedStreams.lean"

#: The theorems of :data:`LEAN_FILE` (mark W2).
LEAN_THEOREMS: Tuple[str, ...] = (
    "step_between", "fract_pos_of_prefix", "cfPrefix_between",
    "cfPrefix_certified", "mobius_between_pos", "mobius_between",
    "gosper_emit_sound", "sqrt2_interval_prefix",
)


def quadratic_cf(p: int, d: int, q: int, count: int) -> Tuple[int, ...]:
    """The continued fraction of ``(p + sqrt(d))/q`` by the integer recurrence,
    with ``d`` not a square and ``q`` dividing ``d - p*p``."""
    assert q != 0 and (d - p * p) % q == 0
    r = isqrt(d)
    out: List[int] = []
    for _ in range(count):
        a = (p + r) // q if q > 0 else (p + r + 1) // q
        out.append(a)
        p = a * q - p
        q = (d - p * p) // q
    return tuple(out)


def mobius_quadratic_cf(a: int, b: int, c: int, d: int, n: int,
                        count: int) -> Tuple[int, ...]:
    """The continued fraction of ``(a sqrt(n) + b)/(c sqrt(n) + d)``, rewritten
    as ``(P + sqrt(D))/Q`` and expanded by :func:`quadratic_cf`."""
    k = b * c - a * d
    p, q = a * c * n - b * d, c * c * n - d * d
    if k < 0:
        p, q, k = -p, -q, -k
    big_d = k * k * n
    # scale so that Q divides D - P^2
    p, big_d, q = p * abs(q), big_d * q * q, q * abs(q)
    return quadratic_cf(p, big_d, q, count)


def e_terms(count: int) -> Tuple[int, ...]:
    """``e = [2; 1, 2, 1, 1, 4, 1, 1, 6, ...]`` by its pattern."""
    out = [2]
    k = 1
    while len(out) < count:
        out.extend((1, 2 * k, 1))
        k += 1
    return tuple(out[:count])


def _gate_bfs(source: int, target: int, depth: int) -> int:
    """Breadth-first search over the 16 moves on the whole 24-bit word."""
    from ..reasoning import substrate_cognition as sc
    frontier, seen = {source}, {source: 0}
    for step in range(1, depth + 1):
        nxt = set()
        for s in frontier:
            for move in sc._MOVES:
                u = sc._apply(s, move)
                if u not in seen:
                    seen[u] = step
                    nxt.add(u)
        frontier = nxt
        if target in seen:
            break
    return seen.get(target, -1)


def measure() -> Dict[str, object]:
    """The marks W1-W8 of ``studies/CONNECTED_MACHINE_TWO_STUDY.md`` §4."""
    from ..reasoning import exact_real as xr
    from ..reasoning import substrate_cognition as sc
    from ..runtime import router
    from ..runtime import toolbox as tb
    from ..runtime.session import GeometricSession
    from . import connected_cases as cc

    marks: Dict[str, Dict[str, object]] = {}

    # W1 -- every reasoning module reached or declared
    w = tb.wiring_census()
    marks["W1"] = {"census": w, "met": not w["undeclared"]
                   and not w["stale_declarations"]}

    # W2 -- the Lean file: present, free of sorry, every declared theorem
    from pathlib import Path
    lean = Path(__file__).resolve().parents[2] / "lean" / LEAN_FILE
    text = lean.read_text(encoding="utf-8") if lean.exists() else ""
    missing = [t for t in LEAN_THEOREMS if f"theorem {t} " not in text]
    marks["W2"] = {"file": LEAN_FILE, "missing": missing,
                   "sorry": "sorry" in text,
                   "met": bool(text) and not missing and "sorry" not in text}

    # W3 -- continued fractions against independent references
    rows = []
    for n in range(2, 51):
        if isqrt(n) ** 2 == n:
            continue
        got = sc.cf_certified(xr.parse_real(f"sqrt({n})"), N_TERMS)[0]
        rows.append(got == quadratic_cf(0, n, 1, N_TERMS))
    pi_ok = sc.cf_certified(xr.parse_real("pi"), N_TERMS)[0] == PI_TERMS
    e_ok = sc.cf_certified(xr.parse_real("e"), 30)[0] == e_terms(30)
    phi_ok = sc.cf_certified(xr.parse_real("phi"), 30)[0] == (1,) * 30
    marks["W3"] = {"surds": len(rows), "surds_agree": sum(rows), "pi": pi_ok,
                   "e": e_ok, "phi": phi_ok,
                   "met": all(rows) and pi_ok and e_ok and phi_ok}

    # W4 -- Moebius transforms against the quadratic recurrence
    mrows = []
    for a, b, c, d, n in MOBIUS_CASES:
        got = tb.run_tool(f"tool mobius {a} {b} {c} {d} of sqrt({n}) "
                          f"terms {N_TERMS}")
        ref = mobius_quadratic_cf(a, b, c, d, n, N_TERMS)
        mrows.append({"case": (a, b, c, d, n), "ok": got.ok,
                      "agree": got.ok and tuple(got.figures["terms"]) == ref,
                      "direct": got.figures.get("direct_agrees")})
    marks["W4"] = {"cases": len(mrows),
                   "agree": sum(r["agree"] for r in mrows),
                   "direct_agree": sum(bool(r["direct"]) for r in mrows),
                   "met": all(r["agree"] and r["direct"] for r in mrows)}

    # W5 -- rationals written as expressions: no wrong term, ever
    rrows = []
    for text, value in RATIONAL_EXPRESSIONS:
        terms, _, complete = sc.cf_certified(xr.parse_real(text), 10)
        truth = xr.continued_fraction(value, 12)
        rrows.append({"text": text, "emitted": len(terms),
                      "complete": complete,
                      "sound": tuple(terms) == truth[:len(terms)]})
    marks["W5"] = {"rows": rrows,
                   "met": all(r["sound"] and not r["complete"]
                              for r in rrows)}

    # W6 -- non-interference
    sets = router._declared_sets()
    texts = [t for v in sets.values() for t in v] + \
        [t for t, _ in cc.ROUTED_MIXED]
    matched = [t for t in texts if tb.phrase_tool(t) is not None]
    marks["W6"] = {"declared_texts": len(texts), "matched": len(matched),
                   "met": not matched}

    # W7 -- the phrased battery, through the router
    session = GeometricSession()
    prows = []
    for question, expect in PHRASED:
        r = router.route(session, question)
        if expect == "refuse":
            ok = not r.answered
        else:
            ok = r.answered and r.surface == "toolbox" and expect in r.text
        prows.append({"question": question, "ok": ok,
                      "surface": r.surface, "answered": r.answered})
    marks["W7"] = {"questions": len(prows),
                   "as_declared": sum(r["ok"] for r in prows),
                   "answered": sum(r["answered"] for r in prows),
                   "met": all(r["ok"] for r in prows)}

    # W8 -- the tool battery, and the gate certificate against search
    trows = [(q, (g := tb.run_tool(q)).ok == ok and frag in g.text)
             for q, ok, frag in TOOL_CASES]
    seed, grows = 20261013, []
    for i in range(48):
        seed = (1103515245 * seed + 12345) % (1 << 31)
        source = seed % (1 << 24)
        target = source
        for j in range(1 + i % 3):
            seed = (1103515245 * seed + 12345) % (1 << 31)
            target = sc._apply(target, sc._MOVES[seed % len(sc._MOVES)])
        cert = sc.reachability_certificate(source, target)
        grows.append(cert is not None and cert == _gate_bfs(source, target, 3))
    marks["W8"] = {"tool_cases": len(trows),
                   "tool_as_declared": sum(ok for _, ok in trows),
                   "gate_pairs": len(grows), "gate_agree": sum(grows),
                   "met": all(ok for _, ok in trows) and all(grows)}

    return {"marks": marks,
            "met": sum(bool(m["met"]) for m in marks.values()),
            "taken": len(marks)}
