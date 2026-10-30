"""``glm_universal.runtime.derivation_three_marks`` -- the marks of Phase 118
that stay below the frames (``studies/DERIVATION_THREE_STUDY.md``).

N1-N4, N6-N8 and N10 of :mod:`glm_universal.evaluation.derivation_three_cases`
are measured here on the reasoning layer itself
(:mod:`~glm_universal.reasoning.non_shannon`,
:mod:`~glm_universal.reasoning.hamming_rd`,
:mod:`~glm_universal.reasoning.robin`) and the stand-alone scripts
(:mod:`.derivation_three_scripts`), so a unit that holds them does not take
the router -- and with it the whole Lean development -- into its closure
(``ITERATION_COST_STUDY.md`` §5k).  N5 and N9, which read through the frames
the CLI uses, are :mod:`.derivation_three_report`.

The batteries run their scripts in-process (``exec`` of the same stand-alone
text, which imports nothing of the package).  No float is made anywhere
(D7): the two independent cross-checks the marks name (Blahut-Arimoto,
Newton) and the pool screen run in integer fixed point, and every verdict is
exact.
"""

from __future__ import annotations

import io
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..evaluation import derivation_three_cases as C
from ..reasoning import coding_theory as CT
from ..reasoning import hamming_rd as HR
from ..reasoning import info_inequality as II
from ..reasoning import non_shannon as NS
from ..reasoning import robin as RB
from . import derivation_three_scripts as S3
from . import derivation_two_scripts as DS

__all__ = ["decide_all", "inequality_marks", "rd_marks", "robin_marks",
           "refusal_marks_low", "random_beyond_claim", "inequality_battery",
           "rd_battery", "robin_battery", "lean_mark", "exec_script",
           "inequality_script", "LEAN_FILE", "Lcg"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "lean" /
             "RequestProject" / "GLM" / "NonShannon.lean")


class Lcg:
    def __init__(self, seed: int):
        self.s = seed

    def next(self, n: int) -> int:
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) \
            % (1 << 64)
        return (self.s >> 33) % n


def exec_script(script: str) -> bool:
    out = io.StringIO()
    saved, sys.stdout = sys.stdout, out
    try:
        exec(compile(script, "<column-3>", "exec"), {"__name__": "c3"})
    except AssertionError:
        return False
    finally:
        sys.stdout = saved
    lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
    return bool(lines) and lines[-1].strip().endswith("VERIFIED True")


def _summary(rows: List[Dict[str, object]]) -> Dict[str, object]:
    return {"rows": rows, "as_declared": sum(bool(r["as_declared"])
                                             for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


# ---------------------------------------------------------------------------
# N1: the declared inequalities
# ---------------------------------------------------------------------------

def decide_all(text: str):
    """``(problem, Phase 107 verdict, Phase 118 verdict or None, kind)``."""
    pr = II.parse_problem(text)
    v = II.decide(pr)
    if v.kind != "NOT_SHANNON":
        return pr, v, None, v.kind
    b = NS.decide_beyond(pr, v)
    return pr, v, b, b.kind


def inequality_script(pr, v, b) -> str:
    """The column-3 script of whichever verdict decided the claim."""
    if b is None:
        if v.kind == "proved":
            return DS.inequality_script(pr.names, pr.given_texts,
                                        pr.claim_text, "proved",
                                        v.certificates)
        claimed = II._value(pr.claims[v.violated], v.entropies)
        return DS.inequality_script(pr.names, pr.given_texts, pr.claim_text,
                                    "NOT_VALID", [], v.distribution,
                                    v.violated, claimed)
    if b.kind == "proved_non_shannon":
        zys = [(i,) + tuple(NS.zy_copy_certificate(*i)) for i in b.instances()]
        return S3.beyond_script(pr.names, pr.given_texts, pr.claim_text,
                                b.kind, b.certificates, zys)
    if b.kind == "NOT_VALID_ENTROPIC":
        return S3.beyond_script(pr.names, pr.given_texts, pr.claim_text,
                                b.kind, law=b.law, violated=b.violated,
                                claimed_value=b.violation)
    return DS.inequality_script(pr.names, pr.given_texts, pr.claim_text,
                                "NOT_SHANNON", [], None, b.violated,
                                II._value(pr.claims[b.violated],
                                          b.polymatroid), b.polymatroid)


def inequality_marks() -> Dict[str, object]:
    rows = []
    for cid, q, verdict in C.INEQUALITIES:
        _, _, _, kind = decide_all(q.split(":", 1)[1])
        rows.append({"id": cid, "kind": kind, "want": verdict,
                     "as_declared": kind == verdict})
    return _summary(rows)


# ---------------------------------------------------------------------------
# N2: rate distortion
# ---------------------------------------------------------------------------

def _source(q: str) -> str:
    return q.split(" for ", 1)[1].rsplit(" source", 1)[0]


_TERM = re.compile(r"([+-])?\s*\((\d+(?:/\d+)?)\)\*log2\((\d+(?:/\d+)?)\)")


def logform_of_text(expr: str) -> Dict[int, Fraction]:
    """A declared sample ``±(c)*log2(q) ± ...`` as an exact sum of
    logarithms of primes (the declared samples are all of that shape)."""
    out: Dict[int, Fraction] = {}
    pos = 0
    for m in _TERM.finditer(expr):
        if expr[pos:m.start()].strip():
            raise ValueError(f"unreadable sample: {expr!r}")
        pos = m.end()
        c = Fraction(m.group(2)) * (-1 if m.group(1) == "-" else 1)
        for p, e in NS.factor_log2(Fraction(m.group(3))).items():
            out[p] = out.get(p, Fraction(0)) + c * e
    if expr[pos:].strip():
        raise ValueError(f"unreadable sample: {expr!r}")
    return {p: e for p, e in out.items() if e}


def rd_marks() -> Dict[str, object]:
    rows = []
    for cid, q, bps, letters, samples in C.RATE_DISTORTION:
        r = HR.hamming_rd(_source(q))
        ok = ([str(b) for b in r.breakpoints] == list(bps) and
              r.letters_per_piece == list(letters))
        for D, expr in samples:
            want = logform_of_text(expr)
            got = HR.formula_logform(r, Fraction(D))
            diff = dict(want)
            for q, e in got.items():
                diff[q] = diff.get(q, Fraction(0)) - e
            ok = ok and NS.lf_sign(diff) == 0      # equal exactly
        rows.append({"id": cid, "breakpoints": [str(b) for b in r.breakpoints],
                     "letters": r.letters_per_piece, "as_declared": ok})
    return _summary(rows)


# ---------------------------------------------------------------------------
# N3: Robin
# ---------------------------------------------------------------------------

def _robin(q: str) -> RB.Robin:
    parts = [p.strip() for p in q.split(":", 1)[1].split(";")]
    return RB.robin_problem(parts[0], parts[1:])


def robin_marks() -> Dict[str, object]:
    rows = []
    for cid, q, eq, iv, neg, first in C.ROBIN:
        r = _robin(q)
        lams = tuple(RB.decimal_text(a, b) for a, b in r.eigenvalues())
        nv = RB.decimal_text(*r.negative_value) if r.negative_value else None
        ok = (r.equation == eq and r.interval == iv and nv == neg and
              (first is None and not lams or lams == first))
        rows.append({"id": cid, "equation": r.equation, "eigenvalues": lams,
                     "negative": nv, "as_declared": ok})
    return _summary(rows)


# ---------------------------------------------------------------------------
# N4 (below the frames): the refusal codes of the layer itself
# ---------------------------------------------------------------------------

def refusal_marks_low() -> Dict[str, object]:
    rows = []
    for cid, text, code in C.REFUSALS:
        got = None
        body = text.split(":", 1)[1] if ":" in text else text
        try:
            if text.startswith("prove information inequality"):
                II.parse_problem(body)
            elif text.startswith("derive rate distortion"):
                m = re.match(r"(.*?)\s+source\s+with\s+(.*?)(?:\s+distortion)?"
                             r"\s*$", text.split(" for ", 1)[1])
                CT.hamming_rate_distortion(m.group(1), m.group(2))
            else:
                parts = [p.strip() for p in body.split(";")]
                RB.robin_problem(parts[0], parts[1:])
        except (II.InequalityError, CT.CodingError, RB.RobinError) as e:
            got = e.code
        rows.append({"id": cid, "code": got, "want": code,
                     "as_declared": got == code})
    return _summary(rows)


# ---------------------------------------------------------------------------
# N6: the inequality battery
# ---------------------------------------------------------------------------

_NAMES = ("A", "B", "C", "D")


def _zy_text(a, b, c, d) -> str:
    return (f"I({a};{b}) + I({a};{c},{d}) + 3*I({c};{d}|{a}) + "
            f"I({c};{d}|{b}) - 2*I({c};{d})")


def _ingleton_text(a, b, c, d) -> str:
    return f"I({a};{b}|{c}) + I({a};{b}|{d}) + I({c};{d}) - I({a};{b})"


def random_beyond_claim(rng: Lcg, bound: int) -> str:
    """A random nonnegative combination of two Zhang-Yeung instances, an
    Ingleton instance and three elemental terms, less one elemental term at
    random: valid and invalid claims past the Shannon cone both occur."""
    perms = [(a, b) for a in _NAMES for b in _NAMES if a != b]

    def inst():
        a, b = perms[rng.next(len(perms))]
        c, d = [x for x in _NAMES if x not in (a, b)]
        return a, b, c, d
    els = II.elementals(list(_NAMES))
    parts = []
    for _ in range(2):
        k = rng.next(bound + 1)
        if k:
            parts.append(f"{k}*({_zy_text(*inst())})")
    if rng.next(2):
        parts.append(f"({_ingleton_text(*inst())})")
    for _ in range(3):
        k = rng.next(bound + 1)
        if k:
            parts.append(f"{k}*" +
                         II.elemental_text(els[rng.next(len(els))], _NAMES))
    if rng.next(2):
        parts.append("-" + II.elemental_text(els[rng.next(len(els))], _NAMES))
    if not parts:
        parts = [f"({_zy_text(*inst())})"]
    text = " + ".join(parts).replace("+ -", "- ")
    return f"|- {text} >= 0"


def _pool_violates(pr: II.Problem) -> bool:
    """Does any law of the search pool violate the (first) claim, exactly?"""
    names = pr.names
    c0, terms, scale = NS._fixed_coeffs(pr.claims[0], names)
    tol = NS._scaled_tol(NS.CLAIM_TOL, scale)
    pool = NS.law_pool(len(names))
    for idx, vec in enumerate(NS._pool_vectors(len(names))):
        if c0 + sum(c * vec[i] for i, c in terms) < -tol:
            atoms, weights = pool[idx]
            h = NS.log_entropies(atoms, weights, names)
            if NS.lf_sign(NS.lf_value(pr.claims[0], h)) < 0:
                return True
    return False


def inequality_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed, bound = C.INEQUALITY_BATTERY
    n = count or n
    rng = Lcg(seed)
    kinds: Dict[str, int] = {}
    unsound = inconsistent = script_fail = other = 0
    for _ in range(n):
        text = random_beyond_claim(rng, bound)
        pr, v, b, kind = decide_all(text)
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind not in ("proved", "proved_non_shannon", "NOT_VALID",
                        "NOT_VALID_ENTROPIC", "NOT_SHANNON"):
            other += 1
            continue
        if not pr.givens and pr.op == ">=" and \
                kind in ("proved", "proved_non_shannon") and \
                _pool_violates(pr):
            unsound += 1
        if kind == "NOT_VALID_ENTROPIC" and \
                NS._zy_certificate(pr, pr.claims[b.violated]) is not None:
            inconsistent += 1
        if not exec_script(inequality_script(pr, v, b)):
            script_fail += 1
    return {"claims": n, "kinds": kinds, "unsound": unsound,
            "inconsistent": inconsistent, "script_failures": script_fail,
            "undecided": kinds.get("NOT_SHANNON", 0),
            "met": unsound == 0 and inconsistent == 0 and script_fail == 0
            and other == 0}


# ---------------------------------------------------------------------------
# integer fixed point, for the two independent cross-checks (D7)
# ---------------------------------------------------------------------------

#: Fractional bits of the cross-checks' fixed point.
_FX = 64
_ONE = 1 << _FX
#: N8's widening of every enclosure.
_SLACK = Fraction(1, 10 ** 9)


def _to_fixed(q) -> int:
    q = Fraction(q)
    return (q.numerator << _FX) // q.denominator


def _mul(a: int, b: int) -> int:
    return (a * b) >> _FX


def _log2_fixed(x: int) -> int:
    """``log2(x / 2**_FX) * 2**_FX`` for a positive fixed-point ``x``."""
    return NS.log2_fixed(x, _FX) - (_FX << _FX)


def _exp_neg_fixed(s: Fraction) -> int:
    """``e**(-s)`` for a rational ``s >= 0``, as fixed point (the series in
    exact rationals, rounded once)."""
    total, term, n = Fraction(0), Fraction(1), 0
    while abs(term) > Fraction(1, 1 << (_FX + 8)) or n < 4:
        total += term
        n += 1
        term = term * (-s) / n
    return _to_fixed(total)


def _sin_cos_fixed(t: int) -> Tuple[int, int]:
    t2 = _mul(t, t)
    s_, c_ = 0, 0
    term, n = t, 1                          # t^n / n!, odd n
    while term:
        s_ += term
        term = -(_mul(term, t2) // ((n + 1) * (n + 2)))
        n += 2
    term, n = _ONE, 0
    while term:
        c_ += term
        term = -(_mul(term, t2) // ((n + 1) * (n + 2)))
        n += 2
    return s_, c_


def _sinh_cosh_fixed(t: int) -> Tuple[int, int]:
    t2 = _mul(t, t)
    s_, c_ = 0, 0
    term, n = t, 1
    while term:
        s_ += term
        term = _mul(term, t2) // ((n + 1) * (n + 2))
        n += 2
    term, n = _ONE, 0
    while term:
        c_ += term
        term = _mul(term, t2) // ((n + 1) * (n + 2))
        n += 2
    return s_, c_


def sci_text(x: Fraction, digits: int = 1) -> str:
    """``x >= 0`` in scientific notation, read with integers only."""
    if x <= 0:
        return "0"
    e = 0
    while x >= 10:
        x /= 10
        e += 1
    while x < 1:
        x *= 10
        e -= 1
    q = (x * 10 ** digits).numerator // (x * 10 ** digits).denominator
    return f"{q // 10 ** digits}.{q % 10 ** digits:0{digits}d}e{e:+03d}"


def blahut_arimoto_fixed(probs: List[Fraction], s: Fraction, iters: int
                         ) -> Tuple[int, int]:
    """``(D, R)`` in fixed point at slope ``s`` (``beta = e**(-s)``) by the
    Blahut-Arimoto iteration, Hamming distortion; independent of the closed
    form."""
    m = len(probs)
    p = [_to_fixed(x) for x in probs]
    b = _exp_neg_fixed(s)
    q = [_ONE // m] * m
    W: List[List[int]] = []
    for _ in range(iters):
        W = []
        for x in range(m):
            row = [q[j] if x == j else _mul(q[j], b) for j in range(m)]
            z = sum(row)
            W.append([(w << _FX) // z for w in row])
        q = [sum(_mul(p[x], W[x][j]) for x in range(m)) for j in range(m)]
    D = sum(_mul(p[x], W[x][j]) for x in range(m) for j in range(m) if x != j)
    R = 0
    for x in range(m):
        for j in range(m):
            if W[x][j] > 0 and q[j] > 0:
                R += _mul(_mul(p[x], W[x][j]),
                          _log2_fixed(W[x][j]) - _log2_fixed(q[j]))
    return D, R


def rate_fixed(r: HR.HammingRD, D: int) -> int:
    """The closed form ``R(D)`` at a fixed-point ``D``, in fixed point."""
    if D >= _to_fixed(r.d_max):
        return 0
    for piece in r.pieces:
        if _to_fixed(piece.lo) <= D <= _to_fixed(piece.hi):
            k = piece.k
            break
    else:                                              # pragma: no cover
        raise ValueError(D)
    srt = [r.probs[i] for i in r.order]
    out = 0
    for x in srt[:k]:
        lg = NS.log2_fixed(x.numerator, _FX) - NS.log2_fixed(x.denominator,
                                                             _FX)
        out -= (x.numerator * lg) // x.denominator
    lam = _ONE - D
    if lam > 0:
        out += _mul(lam, _log2_fixed(lam))
    T = D - _to_fixed(1 - sum(srt[:k], Fraction(0)))
    if T > 0:
        out += _mul(T, _log2_fixed(T // (k - 1)))
    return out


# ---------------------------------------------------------------------------
# N7: the rate-distortion battery
# ---------------------------------------------------------------------------

def random_source(rng: Lcg, largest: int, den: int) -> List[Fraction]:
    m = 3 + rng.next(largest - 2)
    cuts = set()
    while len(cuts) < m - 1:
        cuts.add(1 + rng.next(den - 1))
    pts = [0] + sorted(cuts) + [den]
    return [Fraction(b - a, den) for a, b in zip(pts, pts[1:])]


def rd_battery(count: Optional[int] = None,
               slopes: Tuple[Fraction, ...] = (Fraction(7, 10), Fraction(3, 2),
                                               Fraction(3)),
               iters: int = 2500) -> Dict[str, object]:
    n, seed, largest, den = C.RD_BATTERY
    n = count or n
    rng = Lcg(seed)
    tiling = continuity = slb_fail = above_fail = script_fail = 0
    ba_fail = 0
    ba_worst = 0
    beyond = 0
    for _ in range(n):
        ps = random_source(rng, largest, den)
        r = HR.hamming_rd("[" + ", ".join(str(p) for p in ps) + "]")
        if r.slb_end < r.d_max:
            beyond += 1
        bps = r.breakpoints
        if bps[0] != 0 or bps[-1] != r.d_max or any(
                a.hi != b.lo for a, b in zip(r.pieces, r.pieces[1:])):
            tiling += 1
        for a, b in zip(r.pieces, r.pieces[1:]):
            if HR.piece_logform(r, a, a.hi) != HR.piece_logform(r, b, a.hi):
                continuity += 1
        first = r.pieces[0]
        if first.k == r.m:
            D = (first.lo + first.hi) / 2
            if HR.piece_logform(r, first, D) != HR.slb_logform(r, D):
                slb_fail += 1
        for j in range(1, 21):
            D = r.d_max * j / 20
            slb = HR.slb_logform(r, D)
            if j < 20:
                gap = dict(HR.formula_logform(r, D))
                for q, e in slb.items():
                    gap[q] = gap.get(q, Fraction(0)) - e
            else:                               # R(D_max) = 0
                gap = {q: -e for q, e in slb.items()}
            if NS.lf_sign(gap) < 0:
                above_fail += 1
                break
        if not exec_script(S3.rd_full_script(
                r.probs, [(p.lo, p.hi, p.k) for p in r.pieces])):
            script_fail += 1
        for s in slopes:
            Ds, Rs = blahut_arimoto_fixed(r.probs, s, iters)
            if Ds >= _to_fixed(r.d_max) - (_ONE >> 30):
                continue
            err = abs(rate_fixed(r, Ds) - Rs)
            ba_worst = max(ba_worst, err)
            if err > _ONE // 10 ** 6:
                ba_fail += 1
    met = (tiling == continuity == slb_fail == above_fail == script_fail ==
           ba_fail == 0)
    return {"sources": n, "past_the_bound": beyond, "tiling_failures": tiling,
            "discontinuities": continuity, "slb_mismatches": slb_fail,
            "below_slb": above_fail, "script_failures": script_fail,
            "blahut_arimoto_failures": ba_fail,
            "blahut_arimoto_worst": sci_text(Fraction(ba_worst, _ONE)),
            "met": met}


# ---------------------------------------------------------------------------
# N8: the Robin battery
# ---------------------------------------------------------------------------

def _newton(fam: str, h: Fraction, L: Fraction, x0: Fraction) -> Fraction:
    """Newton's method on the characteristic function, in integer fixed
    point with its own series -- independent of the enclosures."""
    h, L, x = _to_fixed(h), _to_fixed(L), _to_fixed(x0)
    for _ in range(100):
        t = _mul(x, L)
        if fam in ("D", "N"):
            s_, c_ = _sin_cos_fixed(t)
        else:
            s_, c_ = _sinh_cosh_fixed(t)
        if fam == "D":
            f = _mul(x, c_) + _mul(h, s_)
            df = c_ - _mul(t, s_) + _mul(_mul(h, L), c_)
        elif fam == "N":
            f = -_mul(x, s_) + _mul(h, c_)
            df = -s_ - _mul(t, c_) - _mul(_mul(h, L), s_)
        elif fam == "Dneg":
            f = _mul(x, c_) + _mul(h, s_)
            df = c_ + _mul(t, s_) + _mul(_mul(h, L), c_)
        else:
            f = _mul(x, s_) + _mul(h, c_)
            df = s_ + _mul(t, c_) + _mul(_mul(h, L), s_)
        step = (f << _FX) // df
        x -= step
        if abs(step) < (_ONE >> 50):
            break
    return Fraction(x, _ONE)


def robin_battery(count: Optional[int] = None) -> Dict[str, object]:
    n, seed = C.ROBIN_BATTERY
    n = count or n
    rng = Lcg(seed)
    script_fail = newton_fail = neg_wrong = interval_fail = 0
    cases: Dict[str, int] = {}
    for _ in range(n):
        num = rng.next(11) - 5 or 1
        h = Fraction(num, 1 + rng.next(3))
        L = Fraction(1 + rng.next(6), 2)
        fam = "D" if rng.next(2) else "N"
        left = "y(0) = 0" if fam == "D" else "d(y)/dx(0) = 0"
        right = f"d(y)/dx({L}) + {h}*y({L}) = 0" if h > 0 else \
            f"d(y)/dx({L}) - {-h}*y({L}) = 0"
        r = RB.robin_problem("d2(y)/dx2 + lambda*y = 0", [left, right])
        cases[r.case] = cases.get(r.case, 0) + 1
        mults = [RB.interval_mults(r.case, k) for k in (1, 2, 3)]
        lams = [RB.decimal_text(a, b) for a, b in r.eigenvalues()]
        neg = RB.decimal_text(*r.negative_value) if r.negative_value else None
        if None in lams or (r.negative_value and neg is None):
            script_fail += 1
            continue
        if not exec_script(S3.robin_script(r.family, r.h, r.L, mults, r.roots,
                                           lams, r.negative_mu, neg, r.case)):
            script_fail += 1
        want_neg = (h * L < -1) if fam == "D" else (h < 0)
        if want_neg != (r.negative_value is not None):
            neg_wrong += 1
        for (lo, hi), (a, b) in zip(r.roots, mults):
            if not (lo > a * RB.PI_LO / L or a == 0) or hi > b * RB.PI_HI / L:
                interval_fail += 1
            x = _newton(fam, h, L, (lo + hi) / 2)
            if not lo - _SLACK <= x <= hi + _SLACK:
                newton_fail += 1
        if r.negative_mu:
            lo, hi = r.negative_mu
            x = _newton("Dneg" if fam == "D" else "Nneg", h, L, (lo + hi) / 2)
            if not lo - _SLACK <= x <= hi + _SLACK:
                newton_fail += 1
    return {"problems": n, "cases": cases, "script_failures": script_fail,
            "newton_outside": newton_fail, "negative_wrong": neg_wrong,
            "interval_failures": interval_fail,
            "met": script_fail == newton_fail == neg_wrong == interval_fail
            == 0}


# ---------------------------------------------------------------------------
# N10: the Lean file
# ---------------------------------------------------------------------------

def lean_mark() -> Dict[str, object]:
    """N10 (the source half; the build is ``lake build``)."""
    if not LEAN_FILE.exists():
        return {"exists": False, "met": False}
    src = LEAN_FILE.read_text(encoding="utf-8")
    code = re.sub(r"/-.*?-/", "", src, flags=re.S)
    code = re.sub(r"--[^\n]*", "", code)
    missing = [t for t in C.LEAN_THEOREMS
               if not re.search(rf"theorem\s+{t}\b", code)]
    has_sorry = bool(re.search(r"\bsorry\b", code))
    return {"exists": True, "missing": missing, "sorry": has_sorry,
            "met": not missing and not has_sorry}
