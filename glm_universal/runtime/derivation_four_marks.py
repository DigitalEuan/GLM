"""``glm_universal.runtime.derivation_four_marks`` -- the marks of Phase 119
that stay below the router (``studies/DERIVATION_FOUR_STUDY.md``).

P1-P4 (the layer half), P6-P8 and P10 of
:mod:`glm_universal.evaluation.derivation_four_cases` are measured here on the
reasoning layer (:mod:`~glm_universal.reasoning.copy_chain`,
:mod:`~glm_universal.reasoning.general_rd`,
:mod:`~glm_universal.reasoning.robin_two`) and the stand-alone scripts
(:mod:`.derivation_four_scripts`).  P4 through the frames, P5 and P9 are
:mod:`.derivation_four_report`.

The batteries run their scripts in-process (``exec`` of the same stand-alone
text).  No float anywhere (D7): the Newton cross-check of P8 runs in integer
fixed point (Phase 118's), every verdict is exact.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..evaluation import derivation_four_cases as C
from ..reasoning import copy_chain as CC
from ..reasoning import general_rd as GR
from ..reasoning import hamming_rd as HR
from ..reasoning import info_inequality as II
from ..reasoning import non_shannon as NS
from ..reasoning import robin as RB
from ..reasoning import robin_two as R2
from . import derivation_four_frames as D4
from . import derivation_four_scripts as S4
from . import derivation_three_marks as M3

__all__ = ["decide_any", "inequality_marks", "rd_marks", "robin_marks",
           "refusal_marks_low", "random_five_claim", "inequality_battery",
           "phase_118_battery", "rd_battery", "robin_battery", "lean_mark",
           "split_eigen"]

LEAN_DIR = (Path(__file__).resolve().parent.parent.parent / "glm_lean")

exec_script = M3.exec_script
_summary = M3._summary


# ---------------------------------------------------------------------------
# P1: the declared inequalities
# ---------------------------------------------------------------------------

def _body(q: str) -> str:
    return q.split(":", 1)[1]


def decide_any(text: str):
    """``(kind, problem, data)`` with ``kind`` one of the declared verdicts;
    ``data`` the chain list, the :class:`~copy_chain.Five`, or Phase 118's
    triple."""
    try:
        pr, v, b, kind = M3.decide_all(text)
    except II.InequalityError as e:
        if e.code != "TOO_MANY_VARIABLES":
            raise
        pr = CC.parse_five(text)
        f = CC.decide_five(pr)
        return f.kind, pr, f
    if kind == "NOT_SHANNON":
        chains = CC.decide_chain(pr)
        if chains is not None:
            return "proved_by_copies", pr, chains
    return kind, pr, (v, b)


def script_of(kind: str, pr: II.Problem, data) -> str:
    if kind == "proved_by_copies":
        return D4.chain_report(pr, data, False)[2]
    if isinstance(data, CC.Five):
        f = data
        if kind == "proved_non_shannon":
            zys = [(i,) + tuple(NS.zy_copy_certificate(*i))
                   for i in f.instances()]
            return S4.five_zy_script(pr.names, pr.given_texts, pr.claim_text,
                                     f.certificates, zys)
        if kind == "NOT_VALID_ENTROPIC":
            from . import derivation_three_scripts as S3
            return S3.beyond_script(pr.names, pr.given_texts, pr.claim_text,
                                    kind, law=f.law, violated=f.violated,
                                    claimed_value=f.violation)
        return M3.inequality_script(pr, f.shannon, None) \
            if kind in ("proved", "NOT_VALID") else ""
    v, b = data
    return M3.inequality_script(pr, v, b)


def inequality_marks() -> Dict[str, object]:
    rows = []
    for cid, q, want in C.INEQUALITIES:
        kind, pr, data = decide_any(_body(q))
        ok = kind == want and exec_script(script_of(kind, pr, data))
        rows.append({"id": cid, "kind": kind, "want": want,
                     "as_declared": ok})
    return _summary(rows)


# ---------------------------------------------------------------------------
# P2: rate distortion
# ---------------------------------------------------------------------------

def _rd_text(q: str) -> str:
    return q.split(" for ", 1)[1]


def rd_marks() -> Dict[str, object]:
    rows = []
    half = Fraction(5, 10 ** 7)
    for cid, q, dmin, dmax, pts in C.RATE_DISTORTION:
        p, d, at = GR.parse_rd(_rd_text(q))
        g = GR.general_rd(p, d, at)
        ok = str(g.d_min) == dmin and str(g.d_max) == dmax
        got = {str(e.D): e for e in g.points}
        ok = ok and sorted(got) == sorted(D for D, _ in pts)
        for D, text in pts:
            e = got.get(D)
            if e is None:
                ok = False
                continue
            val = Fraction(text)
            ok = ok and e.decimal() == text and \
                e.upper - e.lower < Fraction(1, 10 ** 6) and \
                e.lower - half <= val <= e.upper + half
        rows.append({"id": cid, "d_min": str(g.d_min), "d_max": str(g.d_max),
                     "values": {k: v.decimal() for k, v in got.items()},
                     "as_declared": ok})
    return _summary(rows)


# ---------------------------------------------------------------------------
# P3: Robin
# ---------------------------------------------------------------------------

def split_eigen(q: str) -> Tuple[str, List[str]]:
    parts = [s.strip() for s in _body(q).split(";") if s.strip()]
    return parts[0], parts[1:]


def robin_marks() -> Dict[str, object]:
    rows = []
    for cid, q, eq, iv, lams in C.ROBIN:
        r = R2.robin_two(*split_eigen(q))
        got = [RB.decimal_text(a, b) for a, b in r.eigenvalues()]
        ok = (r.kind == "both" and r.equation == eq and r.interval == iv and
              (got == list(lams) if lams else not got))
        rows.append({"id": cid, "equation": r.equation, "eigenvalues": got,
                     "as_declared": ok})
    for cid, q, eq, cases in C.ROBIN_SYMBOLIC:
        r = R2.robin_two(*split_eigen(q))
        mine = tuple((c.condition, c.interval, c.nonpositive)
                     for c in r.cases)
        rows.append({"id": cid, "equation": r.equation,
                     "as_declared": r.equation == eq and mine == cases})
    for cid, q, lo, hi in C.ROBIN_BOUNDS:
        r = RB.robin_problem(*split_eigen(q))
        rows.append({"id": cid, "bounds": R2.bounds_for(r),
                     "as_declared": R2.bounds_for(r) == (lo, hi)})
    return _summary(rows)


# ---------------------------------------------------------------------------
# P4 at the layer
# ---------------------------------------------------------------------------

def refusal_marks_low() -> Dict[str, object]:
    rows = []
    for cid, text, want in C.REFUSALS:
        code = None
        try:
            if text.startswith("prove information inequality"):
                CC.parse_five(_body(text))
            elif text.startswith("derive rate distortion"):
                p, d, at = GR.parse_rd(_rd_text(text))
                GR.general_rd(p, d, at)
            else:
                R2.robin_two(*split_eigen(text))
        except (II.InequalityError, GR.RDError, RB.RobinError) as e:
            code = e.code
        rows.append({"id": cid, "code": code, "want": want,
                     "as_declared": code == want})
    return _summary(rows)


# ---------------------------------------------------------------------------
# P6: the inequality battery
# ---------------------------------------------------------------------------

_FIVE = ("A", "B", "C", "D", "E")


def random_five_claim(rng: M3.Lcg, bound: int = 2) -> str:
    """A random combination over five variables of a Zhang-Yeung instance
    and an Ingleton instance (each on four of the five), elemental terms,
    and one elemental term subtracted at random."""
    def four():
        names = list(_FIVE)
        out = []
        for _ in range(4):
            out.append(names.pop(rng.next(len(names))))
        return out
    els = II.elementals(list(_FIVE))
    parts = []
    k = rng.next(bound + 1)
    if k:
        parts.append(f"{k}*({M3._zy_text(*four())})")
    if rng.next(2):
        parts.append(f"({M3._ingleton_text(*four())})")
    for _ in range(3):
        k = rng.next(bound + 1)
        if k:
            parts.append(f"{k}*" +
                         II.elemental_text(els[rng.next(len(els))], _FIVE))
    if rng.next(2):
        parts.append("-" + II.elemental_text(els[rng.next(len(els))], _FIVE))
    if not parts:
        parts = [f"({M3._ingleton_text(*four())})"]
    text = " + ".join(parts).replace("+ -", "- ")
    return f"|- {text} >= 0"


def inequality_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed = C.INEQUALITY_BATTERY
    n = count or n
    rng = M3.Lcg(seed)
    kinds: Dict[str, int] = {}
    unsound = inconsistent = script_fail = other = 0
    for _ in range(n):
        text = random_five_claim(rng)
        pr = CC.parse_five(text)
        if len(pr.names) < 5:
            # fewer than five variables appear: Phase 118's path decides it
            kind, pr, data = decide_any(text)
        else:
            f = CC.decide_five(pr)
            kind, data = f.kind, f
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind not in ("proved", "proved_non_shannon", "proved_by_copies",
                        "NOT_VALID", "NOT_VALID_ENTROPIC", "NOT_SHANNON"):
            other += 1
            continue
        if kind.startswith("proved") and len(pr.names) == 5:
            law = CC._lifted_counterexample(pr, 0)[0]
            if law is not None:
                unsound += 1
        if kind == "NOT_VALID_ENTROPIC" and isinstance(data, CC.Five) and \
                CC._zy_certificate(pr, pr.claims[data.violated]) is not None:
            inconsistent += 1
        if kind != "NOT_SHANNON" and \
                not exec_script(script_of(kind, pr, data)):
            script_fail += 1
    return {"claims": n, "kinds": kinds, "unsound": unsound,
            "inconsistent": inconsistent, "script_failures": script_fail,
            "met": unsound == inconsistent == script_fail == other == 0}


def phase_118_battery() -> Dict[str, object]:
    """Phase 118's battery: only its ``NOT_SHANNON`` claims can move (the
    chains are tried on nothing else); how many of them the chains now
    decide is reported, and every certificate found is re-checked."""
    from ..evaluation import derivation_three_cases as C3
    n, seed, bound = C3.INEQUALITY_BATTERY
    rng = M3.Lcg(seed)
    texts = [M3.random_beyond_claim(rng, bound) for _ in range(n)]
    undecided, decided, failed = [], 0, 0
    for k, text in enumerate(texts):
        pr = II.parse_problem(text)
        v = II.decide(pr)
        if v.kind != "NOT_SHANNON":
            continue
        b = NS.decide_beyond(pr, v)
        if b.kind != "NOT_SHANNON":
            continue
        undecided.append(k)
        chains = CC.decide_chain(pr)
        if chains is not None:
            decided += 1
            if not exec_script(D4.chain_report(pr, chains, False)[2]):
                failed += 1
    return {"claims": n, "not_shannon": undecided, "decided_by_copies":
            decided, "script_failures": failed, "met": failed == 0}


# ---------------------------------------------------------------------------
# P7: the rate-distortion battery
# ---------------------------------------------------------------------------

def _lf_bounds(f: Dict[int, Fraction]) -> Tuple[Fraction, Fraction]:
    lo = hi = Fraction(0)
    for p, e in f.items():
        a, b = GR.log2_bounds(Fraction(p))
        lo += min(e * a, e * b)
        hi += max(e * a, e * b)
    return lo, hi


def rd_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed, largest, dmax = C.RD_BATTERY
    n = count or n
    rng = M3.Lcg(seed)
    fails = {"script": 0, "width": 0, "monotone": 0, "convex": 0,
             "hamming": 0, "channel": 0}
    hamming = degenerate = 0
    for k in range(n):
        m = 2 + rng.next(largest - 1)
        ws = [1 + rng.next(6) for _ in range(m)]
        p = [Fraction(w, sum(ws)) for w in ws]
        if k % 5 == 0:
            d = [[Fraction(0 if x == y else 1) for y in range(m)]
                 for x in range(m)]
        elif k % 2:
            # a zero diagonal (D_min = 0) and positive integers off it
            d = [[Fraction(0 if x == y else 1 + rng.next(dmax))
                  for y in range(m)] for x in range(m)]
        else:
            d = [[Fraction(rng.next(dmax + 1)) for _ in range(m)]
                 for _ in range(m)]
        g = GR.general_rd(p, d)
        if not g.points:
            degenerate += 1
            continue
        texts = [e.decimal() for e in g.points]
        if None in texts or not exec_script(S4.rd_script(
                g.probs, g.d, g.d_min, g.d_max,
                [(e.D, e.channel, e.t, e.q, s)
                 for e, s in zip(g.points, texts)])):
            fails["script"] += 1
        for e in g.points:
            if e.upper - e.lower >= Fraction(1, 10 ** 6):
                fails["width"] += 1
            if e.distortion > e.D:
                fails["channel"] += 1
        pts = g.points
        for a, b in zip(pts, pts[1:]):
            if b.lower > a.upper:
                fails["monotone"] += 1
        if len(pts) == 3 and pts[1].lower > (pts[0].upper + pts[2].upper) / 2:
            fails["convex"] += 1
        if g.hamming:
            hamming += 1
            src = "[" + ", ".join(str(x) for x in p) + "]"
            r = HR.hamming_rd(src)
            for e in pts:
                lo, hi = _lf_bounds(HR.formula_logform(r, e.D))
                if hi < e.lower or lo > e.upper:
                    fails["hamming"] += 1
    return {"sources": n, "degenerate": degenerate, "hamming": hamming,
            "failures": fails, "met": not any(fails.values())}


# ---------------------------------------------------------------------------
# P8: the Robin battery
# ---------------------------------------------------------------------------

def _newton_both(a: Fraction, b: Fraction, L: Fraction, x0: Fraction
                 ) -> Fraction:
    """Newton on ``(ab - k^2) sin(kL) + k(a + b) cos(kL)`` in integer fixed
    point with Phase 118's series -- independent of the enclosures."""
    F_, one = M3._FX, M3._ONE
    A, B, Lf, x = (M3._to_fixed(a), M3._to_fixed(b), M3._to_fixed(L),
                   M3._to_fixed(x0))
    mul = M3._mul
    for _ in range(100):
        t = mul(x, Lf)
        s_, c_ = M3._sin_cos_fixed(t)
        ab, apb = mul(A, B), A + B
        f = mul(ab - mul(x, x), s_) + mul(mul(x, apb), c_)
        df = (-2 * mul(x, s_) + mul(mul(ab - mul(x, x), Lf), c_) +
              mul(apb, c_) - mul(mul(mul(x, apb), Lf), s_))
        step = (f << F_) // df
        x -= step
        if abs(step) < (one >> 50):
            break
    return Fraction(x, one)


def _bounds_hold(h: Fraction, L: Fraction, roots) -> bool:
    for n, (lo, hi) in enumerate(roots, 1):
        th_min = lo * L - (2 * n - 1) * RB.PI_HI / 2
        th_max = hi * L - (2 * n - 1) * RB.PI_LO / 2
        if not 0 < th_min < th_max < RB.PI_LO / 2:
            return False
        (s1, _), (_, c1) = RB.sin_cos_bounds(th_min)
        (_, s2), (c2, _) = RB.sin_cos_bounds(th_max)
        c = h * L
        if not (s1 / c1 > c / (n * RB.PI_LO) and
                s2 / c2 < c / ((n - Fraction(1, 2)) * RB.PI_HI)):
            return False
    return True


def robin_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed = C.ROBIN_BATTERY
    n = count or n
    rng = M3.Lcg(seed)
    fails = {"script": 0, "newton": 0, "interval": 0, "cases": 0,
             "bounds": 0}
    ode = "d2(y)/dx2 + lambda*y = 0"
    for k in range(n):
        a = Fraction(1 + rng.next(6), 1 + rng.next(3))
        b = Fraction(1 + rng.next(6), 1 + rng.next(3))
        L = Fraction(1 + rng.next(6), 2)
        r = R2.robin_two(ode, [f"d(y)/dx(0) - {a}*y(0) = 0",
                               f"d(y)/dx({L}) + {b}*y({L}) = 0"])
        lams = [RB.decimal_text(x, y) for x, y in r.eigenvalues()]
        if None in lams or not exec_script(S4.robin_both_script(
                r.a, r.b, r.L, r.roots, lams, r.equation)):
            fails["script"] += 1
        for j, (lo, hi) in enumerate(r.roots, 1):
            if not (lo > (j - 1) * RB.PI_LO / L and hi < j * RB.PI_HI / L):
                fails["interval"] += 1
            x = _newton_both(a, b, L, (lo + hi) / 2)
            if not lo - M3._SLACK <= x <= hi + M3._SLACK:
                fails["newton"] += 1
        # the symbolic cases at random points of every class
        fam = "D" if k % 2 == 0 else "N"
        left = "y(0) = 0" if fam == "D" else "d(y)/dx(0) = 0"
        Ls = "L" if k % 4 < 2 else str(L)
        s = R2.robin_two(ode, [left, f"d(y)/dx({Ls}) + h*y({Ls}) = 0"])
        cases = []
        for c in s.cases:
            Lv = s.L if s.L is not None else L
            u = Fraction(1 + rng.next(9), 10)          # in (0, 1)
            h = {"D+": 1 / u, "D0": Fraction(0), "D-weak": -u / Lv,
                 "D-0": -1 / Lv, "D-neg": -(1 + 1 / u) / Lv, "N+": 1 / u,
                 "N0": Fraction(0), "N-": -1 / u}[c.case]
            cases.append(([(h, Lv)], D4.case_mults(c.case), c.nonpositive))
        if not exec_script(S4.robin_cases_script(s.family, cases)):
            fails["cases"] += 1
        # the closed-form bounds on a random numeric instance
        hb = Fraction(1 + rng.next(8), 1 + rng.next(3))
        rb = RB.robin_problem(ode, ["y(0) = 0",
                                    f"d(y)/dx({L}) + {hb}*y({L}) = 0"])
        if not _bounds_hold(hb, L, rb.roots):
            fails["bounds"] += 1
    return {"problems": n, "failures": fails, "met": not any(fails.values())}


# ---------------------------------------------------------------------------
# P10: the Lean files
# ---------------------------------------------------------------------------

def lean_mark() -> Dict[str, object]:
    """P10 (the source half; the build is ``lake build``)."""
    srcs = []
    for rel in C.LEAN_FILES:
        f = LEAN_DIR / rel
        if not f.exists():
            return {"exists": False, "missing_file": rel, "met": False}
        code = re.sub(r"/-.*?-/", "", f.read_text(encoding="utf-8"),
                      flags=re.S)
        srcs.append(re.sub(r"--[^\n]*", "", code))
    missing = [t for i, t in C.LEAN_THEOREMS
               if not re.search(rf"theorem\s+{t}\b", srcs[i])]
    has_sorry = any(re.search(r"\bsorry\b", s) for s in srcs)
    return {"exists": True, "missing": missing, "sorry": has_sorry,
            "met": not missing and not has_sorry}
