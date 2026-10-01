"""``glm_universal.reasoning.rate_posterior_marks`` -- the rate posterior, measured.

``studies/RATE_POSTERIOR_STUDY.md`` (Phase 82) declared the marks J1-J9 before
:mod:`glm_universal.reasoning.rate_posterior` existed;
:func:`rate_posterior_report` measures every one of them.

The exact operating characteristic
----------------------------------
A call of ``n`` single reads (the subject and ``n - 1`` corpus reads) at a
true rate ``r``: each read's coset weight is one of five classes, with
probability ``N_d W_d(r)``, and the posterior depends on the reads only
through the **count vector** of classes.  So the whole soft channel is a sum
over count vectors with exact multinomial weights -- no sampling.  The
subject's own class decides the answer (weight ``<= 3``: answered; 4: the
refused tie) and whether it is right (its error was the coset leader, mass
``C(24, d) r^d (1-r)^(24-d)``).

Exactness: ``int`` masks, ``int`` weights and :class:`fractions.Fraction`
only.  No float, no RNG.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from math import comb, factorial, gcd
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.golay_decode import decode_complete
from ..substrate.mog import GOLAY_MASKS
from . import confidence_floor_marks as cfm
from . import law_absorption as la
from . import rate_posterior as rp
from .decoder_confidence import ConfidenceRefusal, N, likelihood

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "SIZES", "FIXED_RATES", "vectors",
    "posterior_of_counts", "soft_cell", "oracle_cell", "j1_likelihood",
    "j2_prior_promise", "j3_fixed_rate", "j4_price", "j5_identifiability",
    "j6_naive", "j7_refusals_are_evidence", "DECLARED_PROGRAMS",
    "j8_runtime", "rate_posterior_report", "REPAIRS", "repair_cell",
    "fixed_rate_identity", "repair_table",
]

LEAN_FILE = "RequestProject/GLM/RatePosterior.lean"

#: The theorems of ``RequestProject/GLM/RatePosterior.lean`` (mark J9).
LEAN_THEOREMS: Tuple[str, ...] = (
    "soft_floor_error_le", "rate_posterior_prod", "naive_rate_underestimates",
    "read_marginal_eq_coset_mass",
)

#: The declared call sizes.
SIZES: Tuple[int, ...] = (1, 2, 5, 10, 20)
_HUNT = rp.GRID[:-1]


def _fixed_rates() -> Tuple[Fraction, ...]:
    mids = tuple((a + b) / 2 for a, b in zip(_HUNT, _HUNT[1:]))
    out = set(_HUNT) | set(mids) | {p / 2 for p in _HUNT} | {2 * p
                                                            for p in _HUNT}
    return tuple(sorted(out))


#: J3's true rates: the grid, the midpoints, half and twice each rate.
FIXED_RATES: Tuple[Fraction, ...] = _fixed_rates()


# ===========================================================================
# 1.  THE COUNT-VECTOR ENGINE
# ===========================================================================

@lru_cache(maxsize=None)
def vectors(n: int) -> Tuple[Tuple[int, ...], ...]:
    """Every count vector of ``n`` reads over the five coset classes."""
    out: List[Tuple[int, ...]] = []

    def rec(prefix: Tuple[int, ...], left: int) -> None:
        if len(prefix) == 4:
            out.append(prefix + (left,))
            return
        for k in range(left + 1):
            rec(prefix + (k,), left - k)

    rec((), n)
    return tuple(out)


@lru_cache(maxsize=None)
def _class_mass(d: int, p: Fraction) -> Fraction:
    return rp.coset_class_mass(d, p)


@lru_cache(maxsize=None)
def _int_class(d: int, p: Fraction) -> int:
    """``W_d(p)`` times ``b^24`` at ``p = a/b``: an integer."""
    a, b = p.numerator, p.denominator
    return sum(k * a ** w * (b - a) ** (N - w)
               for w, k in enumerate(la.coset_enumerator(d)) if k)


def _lcm(values: Sequence[int]) -> int:
    out = 1
    for v in values:
        out = out * v // gcd(out, v)
    return out


#: The common denominator of the grid rates.
_SCALE = _lcm([p.denominator for p in rp.GRID])
#: Each prior as integers on a common scale.
_PRIOR_INT: Dict[str, Tuple[int, ...]] = {
    name: tuple(int(x * _lcm([y.denominator for y in w])) for x in w)
    for name, w in rp.PRIORS.items()}


@lru_cache(maxsize=None)
def _unnormalized(counts: Tuple[int, ...], prior: str = "uniform"
                  ) -> Tuple[int, ...]:
    """The posterior over the grid from a count vector, as integers on one
    common scale (each rate's likelihood times ``(L / b)^(24 n)``)."""
    n = sum(counts)
    out = []
    for w, p in zip(_PRIOR_INT[prior], rp.GRID):
        x = w * (_SCALE // p.denominator) ** (N * n)
        for d, k in enumerate(counts):
            if k:
                x *= _int_class(d, p) ** k
        out.append(x)
    return tuple(out)


def posterior_of_counts(counts: Tuple[int, ...], prior: str = "uniform"
                        ) -> Tuple[Fraction, ...]:
    """The posterior over the grid from a count vector of classes."""
    u = _unnormalized(tuple(counts), prior)
    total = sum(u)
    return tuple(Fraction(x, total) for x in u)


@lru_cache(maxsize=None)
def _top(counts: Tuple[int, ...], prior: str = "uniform"
         ) -> Tuple[Fraction, ...]:
    u = _unnormalized(counts, prior)
    best = max(u)
    return tuple(p for p, x in zip(rp.GRID, u) if x == best)


@lru_cache(maxsize=None)
def _confidence(d: int, p: Fraction) -> Fraction:
    return la.confidence(d, p)


@lru_cache(maxsize=None)
def _answer(counts: Tuple[int, ...], d: int, prior: str
            ) -> Tuple[bool, Optional[Fraction]]:
    """For a call with class counts ``counts`` whose subject is of class
    ``d <= 3``: ``(edge refused, marginal confidence)``."""
    if rp.GUARD in _top(counts, prior):
        return (True, None)
    u = _unnormalized(counts, prior)
    return (False, sum((x * _confidence(d, p) for x, p in zip(u, rp.GRID)),
                       Fraction(0)) / sum(u))


def _multinomial(counts: Sequence[int]) -> int:
    out = factorial(sum(counts))
    for k in counts:
        out //= factorial(k)
    return out


@lru_cache(maxsize=None)
def _corpus_probabilities(n1: int, r: Fraction
                          ) -> Tuple[Tuple[Tuple[int, ...], int], ...]:
    """The distribution of the class counts of ``n1`` corpus reads at ``r``,
    as integers over ``b^(24 n1)``."""
    cls = [rp.COSET_COUNTS[d] * _int_class(d, r) for d in range(5)]
    out = []
    for m in vectors(n1):
        x = _multinomial(m)
        for d, k in enumerate(m):
            if k:
                x *= cls[d] ** k
        out.append((m, x))
    return tuple(out)


def _subject_masses(d: int, r: Fraction) -> Tuple[int, int]:
    """``(right, wrong)`` mass of a subject of class ``d <= 3`` at ``r``, as
    integers over ``b^24``."""
    a, b = r.numerator, r.denominator
    right = comb(N, d) * a ** d * (b - a) ** (N - d)
    total = rp.COSET_COUNTS[d] * _int_class(d, r)
    return right, total - right


@lru_cache(maxsize=None)
def _soft_groups(n: int, r: Fraction, prior: str
                 ) -> Tuple[Tuple[Optional[Fraction], int, int], ...]:
    """Per (corpus counts, subject class ``<= 3``): ``(marginal confidence or
    None if edge-refused, right, wrong)``, masses over ``b^(24 n)``."""
    out = []
    subject = [_subject_masses(d, r) for d in range(4)]
    for m, pm in _corpus_probabilities(n - 1, r):
        for d in range(4):
            full = tuple(k + (1 if j == d else 0) for j, k in enumerate(m))
            _edge, conf = _answer(full, d, prior)
            right, wrong = subject[d]
            out.append((conf, pm * right, pm * wrong))
    return tuple(out)


def soft_cell(n: int, r: Fraction, t: Optional[Fraction],
              prior: str = "uniform") -> Dict[str, object]:
    """The exact measure of the soft decoder at true rate ``r`` for calls of
    ``n`` reads, floored at ``t`` (``None``: unfloored)."""
    groups = _soft_groups(n, r, prior)
    den = r.denominator ** (N * n)
    right = sum(g[1] for g in groups
                if g[0] is not None and (t is None or g[0] >= t))
    wrong = sum(g[2] for g in groups
                if g[0] is not None and (t is None or g[0] >= t))
    edge = sum(g[1] + g[2] for g in groups if g[0] is None)
    decoder_right = sum(_subject_masses(d, r)[0] for d in range(4)) \
        * r.denominator ** (N * (n - 1))
    answered = right + wrong
    return {"n": n, "rate": r, "floor": t, "prior": prior,
            "p_right": Fraction(right, den), "p_wrong": Fraction(wrong, den),
            "p_edge": Fraction(edge, den),
            "residual": Fraction(wrong, answered) if answered else Fraction(0),
            "retention": Fraction(right, decoder_right)}


def oracle_cell(r: Fraction, t: Optional[Fraction]) -> Dict[str, object]:
    """The decoder floored on its confidence at the true rate ``r``."""
    right = wrong = 0
    for d in range(4):
        if t is None or _confidence(d, r) >= t:
            a, b = _subject_masses(d, r)
            right += a
            wrong += b
    decoder_right = sum(_subject_masses(d, r)[0] for d in range(4))
    answered = right + wrong
    den = r.denominator ** N
    return {"rate": r, "floor": t, "p_right": Fraction(right, den),
            "p_wrong": Fraction(wrong, den),
            "residual": Fraction(wrong, answered) if answered else Fraction(0),
            "retention": Fraction(right, decoder_right)}


# ===========================================================================
# 2.  THE MARKS
# ===========================================================================

def _stride_reads() -> List[int]:
    errors = [0, 0b1, 0b101, 0b1110, 0b1111, 0b11111, 0b100000000011,
              0b111111000000000000]
    return [GOLAY_MASKS[(97 * i) % len(GOLAY_MASKS)] ^ e
            for i, e in enumerate(errors)]


def j1_likelihood() -> Dict[str, object]:
    """J1: the classes sum to one; per-read and pair likelihoods equal the
    brute-force sums."""
    sums_ok = all(
        sum((rp.COSET_COUNTS[d] * _class_mass(d, p) for d in range(5)),
            Fraction(0)) == 1 for p in rp.GRID)
    checked = disagreements = 0
    p = Fraction(1, 10)
    for y in _stride_reads():
        brute = sum((likelihood([y], c, p) for c in GOLAY_MASKS),
                    Fraction(0)) / len(GOLAY_MASKS)
        checked += 1
        disagreements += rp.read_likelihood(y, p) != brute
    pairs = [(GOLAY_MASKS[5] ^ 0b111, GOLAY_MASKS[5] ^ 0b111000),
             (0b1111, 0b11110000), (GOLAY_MASKS[9], GOLAY_MASKS[9] ^ 1)]
    for a, b in pairs:
        brute = sum((likelihood([a, b], c, p) for c in GOLAY_MASKS),
                    Fraction(0)) / len(GOLAY_MASKS)
        checked += 1
        disagreements += rp.pair_likelihood(a, b, p) != brute
    return {"classes_sum_to_one": sums_ok, "checked": checked,
            "disagreements": disagreements,
            "passed": sums_ok and disagreements == 0 and checked > 0}


def _prior_cell(n: int, t: Optional[Fraction]) -> Dict[str, object]:
    right = wrong = Fraction(0)
    for w, r in zip(rp.PRIORS["uniform"], rp.GRID):
        c = soft_cell(n, r, t)
        right += w * c["p_right"]
        wrong += w * c["p_wrong"]
    answered = right + wrong
    return {"n": n, "floor": t, "p_right": right, "p_wrong": wrong,
            "residual": wrong / answered if answered else Fraction(0)}


def j2_prior_promise() -> Dict[str, object]:
    """J2: the promise averaged over the declared prior."""
    rows = [_prior_cell(n, t) for n in SIZES for t in cfm.THRESHOLDS]
    broken = [r for r in rows if r["residual"] > 1 - r["floor"]]
    return {"cells": len(rows), "broken": len(broken), "rows": rows,
            "passed": not broken and len(rows) == len(SIZES) * 7}


def j3_fixed_rate() -> Dict[str, object]:
    """J3: every (true rate, n, floor) cell at a fixed rate."""
    rows = []
    for r in FIXED_RATES:
        for n in SIZES:
            for t in cfm.THRESHOLDS:
                c = soft_cell(n, r, t)
                rows.append({"rate": r, "n": n, "floor": t,
                             "residual": c["residual"],
                             "retention": c["retention"],
                             "p_edge": c["p_edge"],
                             "promise": c["residual"] <= 1 - t,
                             "on_grid": r in _HUNT})
    broken = [x for x in rows if not x["promise"]]
    grid_broken = [x for x in broken if x["on_grid"]]
    expectation = not [x for x in grid_broken if x["n"] >= 5]
    worst = max(broken, key=lambda x: x["residual"] / (1 - x["floor"]),
                default=None)
    return {"cells": len(rows), "broken": len(broken),
            "grid_broken": len(grid_broken),
            "broken_rows": broken, "worst": worst, "rows": rows,
            "expectation_holds_on_grid_n_ge_5": expectation,
            "passed": len(rows) == len(FIXED_RATES) * len(SIZES) * 7}


def j4_price() -> Dict[str, object]:
    """J4: soft against oracle, per grid rate, size and floor."""
    rows = []
    for r in _HUNT:
        for t in (Fraction(99, 100), Fraction(999, 1000)):
            o = oracle_cell(r, t)
            for n in SIZES:
                c = soft_cell(n, r, t)
                rows.append({"rate": r, "floor": t, "n": n,
                             "soft_retention": c["retention"],
                             "oracle_retention": o["retention"],
                             "soft_residual": c["residual"],
                             "oracle_residual": o["residual"],
                             "p_edge": c["p_edge"]})
    return {"rows": rows}


def j5_identifiability(max_n: int = 20,
                       least: Fraction = Fraction(9, 10)) -> Dict[str, object]:
    """J5: the smallest ``n`` at which the most probable rate is the true
    one with probability at least ``least``."""
    out: Dict[str, Optional[int]] = {}
    curve: Dict[str, List[Fraction]] = {}
    for r in _HUNT:
        found = None
        probs = []
        for n in range(1, max_n + 1):
            hit = sum(pm for m, pm in _corpus_probabilities(n, r)
                      if _top(m) == (r,))
            hit = Fraction(hit, r.denominator ** (N * n))
            probs.append(hit)
            if found is None and hit >= least:
                found = n
        out[str(r)] = found
        curve[str(r)] = probs
    return {"smallest_n": out, "curve": curve, "least": least,
            "max_n": max_n}


def j6_naive() -> Dict[str, object]:
    """J6: the mean coset weight is below ``24p`` at every grid rate."""
    rows = []
    for p in rp.GRID:
        mean = sum((d * rp.COSET_COUNTS[d] * _class_mass(d, p)
                    for d in range(5)), Fraction(0))
        rows.append({"rate": p, "mean_coset_weight": mean,
                     "mean_flips": N * p, "below": mean < N * p})
    return {"rows": rows, "passed": all(r["below"] for r in rows)}


def _mean_rate(post: Sequence[Fraction]) -> Fraction:
    return sum((x * p for x, p in zip(post, rp.GRID)), Fraction(0))


def j7_refusals_are_evidence() -> Dict[str, object]:
    """J7: a tie read, and a contradicted pair, move the rate up."""
    tie_mass = [rp.COSET_COUNTS[4] * _class_mass(4, p) for p in rp.GRID]
    rising = all(a < b for a, b in zip(tie_mass, tie_mass[1:]))
    prior_mean = _mean_rate(rp.PRIORS["uniform"])
    tie_read = GOLAY_MASKS[3] ^ 0b1111
    after_tie = _mean_rate(rp.rate_posterior([tie_read]))
    octad = next(c for c in GOLAY_MASKS if c.bit_count() == 8)
    outside = [i for i in range(N) if not (octad >> i) & 1][:3]
    y2 = octad ^ sum(1 << i for i in outside)
    y1 = 0b111 if not octad & 0b111 else sum(1 << i for i in outside)
    contradicted = False
    try:
        from .decoder_confidence import agree_confidence
        agree_confidence([y1, y2], Fraction(1, 10))
    except ConfidenceRefusal as e:
        contradicted = e.name == "UNCORRECTABLE"
    after_pair = _mean_rate(rp.rate_posterior(pairs=[(y1, y2)]))
    clean = _mean_rate(rp.rate_posterior(pairs=[(GOLAY_MASKS[3],
                                                 GOLAY_MASKS[3])]))
    return {"tie_mass": tie_mass, "tie_mass_rises": rising,
            "prior_mean": prior_mean, "after_tie": after_tie,
            "pair_contradicted": contradicted, "after_contradicted_pair":
            after_pair, "after_clean_pair": clean,
            "passed": (rising and after_tie > prior_mean and contradicted
                       and after_pair > prior_mean and clean < prior_mean)}


def _predict(kind: str, floor: Optional[Fraction], reads: Sequence[int]
             ) -> Tuple[str, Optional[Fraction]]:
    """A program's outcome computed by the count-vector engine (single
    reads) or the pair histogram, before the runtime is run."""
    if kind == "agree":
        from .decoder_confidence import agree_confidence
        try:
            agree_confidence(list(reads[:2]), rp.GRID[0])
        except ConfidenceRefusal as e:
            return (e.name, None)
        post = rp.rate_posterior(reads[2:], [(reads[0], reads[1])])
        if rp.GUARD in rp.most_probable(post):
            return ("RATE_GRID_EXCEEDED", None)
        conf = sum((x * agree_confidence(list(reads[:2]), p)["confidence"]
                    for x, p in zip(post, rp.GRID)), Fraction(0))
        return ("answer", conf)
    classes = [decode_complete(y).weight for y in reads]
    if classes[0] == 4:
        return ("TIE", None)
    counts = tuple(classes.count(d) for d in range(5))
    edge, conf = _answer(counts, classes[0], "uniform")
    if edge:
        return ("RATE_GRID_EXCEEDED", None)
    if floor is not None and conf < floor:
        return ("BELOW_FLOOR", conf)
    return ("answer", conf)


def _w(i: int, e: int) -> int:
    return GOLAY_MASKS[i] ^ e


#: J8's declared programs: ``(kind, floor, reads)``; ``kind`` is
#: ``decode`` (``decode_soft`` / ``decode_soft_floor``) or ``agree``.
DECLARED_PROGRAMS: Tuple[Tuple[str, Optional[Fraction], Tuple[int, ...]],
                         ...] = (
    ("decode", None, (_w(5, 0b111),)),
    ("decode", None, (_w(5, 0b111), _w(6, 0), _w(7, 0), _w(8, 1))),
    ("decode", Fraction(99, 100), (_w(5, 0b11), _w(6, 0), _w(7, 0))),
    ("decode", Fraction(999, 1000), (_w(5, 0b111), _w(6, 0b1), _w(7, 0b11))),
    ("decode", None, (_w(5, 0b1111),)),
    ("decode", None, (_w(5, 0b111), _w(6, 0b1111), _w(7, 0b1111),
                      _w(8, 0b1111))),
    ("decode", Fraction(9, 10), (_w(9, 0b1), _w(10, 0b111), _w(11, 0b11))),
    ("agree", None, (_w(12, 0b111), _w(12, 0b111000))),
    ("agree", None, (_w(12, 0b111), _w(12, 0b111000), _w(1, 0), _w(2, 0))),
    ("agree", None, (_w(13, 0b1111), _w(13, 0b11110000))),
)


def j8_runtime() -> Dict[str, object]:
    """J8: every declared program's outcome computed first, then the runtime
    run and its scripts checked; the old builtins unmoved."""
    from . import python_speech as sp
    rows = []
    for kind, floor, reads in DECLARED_PROGRAMS:
        computed, conf = _predict(kind, floor, reads)
        args = ", ".join(str(r) for r in reads)
        if kind == "agree":
            src = f"agree_soft({args})"
        elif floor is None:
            src = f"decode_soft({args})"
        else:
            src = (f"decode_soft_floor(Fraction({floor.numerator}, "
                   f"{floor.denominator}), {args})")
        payload = sp.speak(src)
        got = payload.refusal or "answer"
        verified = None
        if got == "answer":
            verified = bool(sp.verify_payload(payload)["verified"])
        rows.append({"source": src, "computed": computed, "confidence": conf,
                     "got": got, "verified": verified,
                     "as_computed": got == computed
                     and verified in (None, True)})
    wrong = sum(1 for r in rows if not r["as_computed"])
    return {"rows": rows, "programs": len(rows),
            "as_computed": len(rows) - wrong, "wrong": wrong,
            "passed": wrong == 0}


def _lean_has(names: Sequence[str]) -> bool:
    """Whether the Lean file states every named theorem and holds no
    ``sorry`` (the build itself is the release's Lean instrument)."""
    import re
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "sorry" not in text and all(
        re.search(rf"\btheorem {n}\b", text) for n in names)


def rate_posterior_report() -> Dict[str, object]:
    """Every mark of the study, measured."""
    j1 = j1_likelihood()
    j2 = j2_prior_promise()
    j3 = j3_fixed_rate()
    j4 = j4_price()
    j5 = j5_identifiability()
    j6 = j6_naive()
    j7 = j7_refusals_are_evidence()
    j8 = j8_runtime()
    j9 = {"file": LEAN_FILE, "theorems": list(LEAN_THEOREMS),
          "passed": _lean_has(LEAN_THEOREMS)}
    marks = {"J1": j1["passed"], "J2": j2["passed"], "J3": j3["passed"],
             "J6": j6["passed"], "J7": j7["passed"], "J8": j8["passed"],
             "J9": j9["passed"]}
    return {"J1": j1, "J2": j2, "J3": j3, "J4": j4, "J5": j5, "J6": j6,
            "J7": j7, "J8": j8, "J9": j9, "marks": marks,
            "met": sum(marks.values()), "of": len(marks)}


# ===========================================================================
# 5.  THE REPAIRS (Phase 86): what Phase 82's section 3 named, measured
# ===========================================================================
#
# Phase 82 left the fixed-rate breaks (2 cells on the grid at 1/10, every cell
# at 1/5) with three candidate repairs: a finer grid, a higher guard point, a
# larger corpus.  Each is a different grid and rule over the same count-vector
# engine.  One further rule is declared beside them, the standard one for a
# guarantee at every fixed parameter rather than on the prior average: answer
# with the confidence at the *upper end of a credible set* of rates (the
# largest grid rate carrying posterior mass at least ``eps``), which by
# Phase 80's antitonicity is never above the confidence at any rate inside the
# set.  The declarations are written here before the table is read; the study
# (RATE_POSTERIOR_STUDY.md section 4) records what they gave.

_MIDS = tuple((a + b) / 2 for a, b in zip(_HUNT, _HUNT[1:]))

#: The declared repairs: ``name -> (hunted rates, guard, rule)``; ``rule`` is
#: ``marginal`` (Phase 82's) or ``upper`` (confidence at the largest rate of
#: posterior mass at least :data:`UPPER_EPS`).
REPAIRS: Dict[str, Tuple[Tuple[Fraction, ...], Fraction, str]] = {
    "R0 as shipped": (_HUNT, Fraction(1, 5), "marginal"),
    "R1 finer grid": (tuple(sorted(set(_HUNT) | set(_MIDS))), Fraction(1, 5),
                      "marginal"),
    "R2 guard raised": (_HUNT + (Fraction(1, 5),), Fraction(3, 10),
                        "marginal"),
    "R3 finer and raised": (tuple(sorted(set(_HUNT) | set(_MIDS)
                                         | {Fraction(3, 20), Fraction(1, 5)})),
                            Fraction(3, 10), "marginal"),
    "R4 upper credible": (_HUNT, Fraction(1, 5), "upper"),
    "R5 upper and raised": (_HUNT + (Fraction(1, 5),), Fraction(3, 10),
                            "upper"),
}
#: The credible-set threshold of the ``upper`` rule.
UPPER_EPS = Fraction(1, 100)


@lru_cache(maxsize=None)
def _repair_unnormalized(name: str, counts: Tuple[int, ...]
                         ) -> Tuple[int, ...]:
    hunt, guard, _rule = REPAIRS[name]
    grid = hunt + (guard,)
    scale = _lcm([p.denominator for p in grid])
    n = sum(counts)
    out = []
    for p in grid:
        x = (scale // p.denominator) ** (N * n)
        for d, k in enumerate(counts):
            if k:
                x *= _int_class(d, p) ** k
        out.append(x)
    return tuple(out)


@lru_cache(maxsize=None)
def _repair_answer(name: str, counts: Tuple[int, ...], d: int
                   ) -> Optional[Fraction]:
    """The confidence a repair answers a class-``d`` subject with, or
    ``None`` when the guard refuses (uniform prior over its grid)."""
    hunt, guard, rule = REPAIRS[name]
    grid = hunt + (guard,)
    u = _repair_unnormalized(name, counts)
    if u[-1] == max(u):
        return None
    total = sum(u)
    if rule == "marginal":
        return sum((x * _confidence(d, p) for x, p in zip(u, grid)),
                   Fraction(0)) / total
    hi = max(p for x, p in zip(u, grid) if Fraction(x, total) >= UPPER_EPS)
    if hi == guard:
        return None
    return _confidence(d, hi)


def repair_cell(name: str, n: int, r: Fraction, t: Fraction
                ) -> Dict[str, object]:
    """One repair's exact residual and retention at true rate ``r``, calls
    of ``n`` reads, floor ``t``; ``by_class`` is the answered mass per
    subject class (for the identity of :func:`fixed_rate_identity`)."""
    subject = [_subject_masses(d, r) for d in range(4)]
    right = wrong = 0
    by_class = [0, 0, 0, 0]
    for m, pm in _corpus_probabilities(n - 1, r):
        for d in range(4):
            full = tuple(k + (1 if j == d else 0) for j, k in enumerate(m))
            c = _repair_answer(name, full, d)
            if c is not None and c >= t:
                right += pm * subject[d][0]
                wrong += pm * subject[d][1]
                by_class[d] += pm * (subject[d][0] + subject[d][1])
    decoder_right = sum(s[0] for s in subject) * r.denominator ** (N * (n - 1))
    answered = right + wrong
    return {"repair": name, "n": n, "rate": r, "floor": t,
            "residual": Fraction(wrong, answered) if answered else Fraction(0),
            "retention": Fraction(right, decoder_right),
            "by_class": tuple(by_class)}


def fixed_rate_identity(cell: Dict[str, object]) -> bool:
    """At a fixed true rate the corpus is independent of whether the subject
    is right given its class, so the residual of *any* rule that decides from
    (corpus, subject class) is the answered-mass average of ``1 - conf_r(d)``
    over the classes: checked exactly on one cell."""
    r = cell["rate"]
    mass = cell["by_class"]
    total = sum(mass)
    if not total:
        return cell["residual"] == 0
    avg = sum((Fraction(w) * (1 - _confidence(d, r))
               for d, w in enumerate(mass)), Fraction(0)) / total
    return avg == cell["residual"]


def repair_table(sizes: Sequence[int] = SIZES) -> Dict[str, object]:
    """Every declared repair over J3's 15 true rates, the sizes and the
    seven floors: broken cells (all, and on the hunted grid), retention at
    two reference cells, and the identity checked on every broken cell."""
    rows = []
    for name in REPAIRS:
        broken = on_grid = 0
        identity = True
        at_1_5 = 0
        for r in FIXED_RATES:
            for n in sizes:
                for t in cfm.THRESHOLDS:
                    c = repair_cell(name, n, r, t)
                    if c["residual"] > 1 - t:
                        broken += 1
                        on_grid += r in _HUNT
                        at_1_5 += r == Fraction(1, 5)
                        identity = identity and fixed_rate_identity(c)
        ref = {f"{r}@{t}": repair_cell(name, max(sizes), r, t)["retention"]
               for r, t in ((Fraction(1, 20), Fraction(999, 1000)),
                            (Fraction(1, 10), Fraction(999, 1000)))}
        rows.append({"repair": name, "broken": broken, "on_grid": on_grid,
                     "at_one_fifth": at_1_5, "identity_holds": identity,
                     "retention": ref})
    return {"rows": rows, "sizes": tuple(sizes),
            "cells_each": len(FIXED_RATES) * len(sizes) * 7}
