"""``glm_universal.sandbox.aggregation_bench`` -- which mixing method the
substrate should keep.

Why this module exists
----------------------
The attention-simulator study (:mod:`glm_universal.sandbox.
attention_simulator`, arXiv 2506.18739v2) measured that the paper's soft
attention runs on this substrate exactly, but is norm-dominated on the
meaning registers, needs a declared exponential depth, and sits at one point
of a dial whose two ends -- the coordinatewise *bundle* and the hard
*nearest* -- are faculties the substrate already ships.  Attention is
therefore one point in a space of aggregation methods.  This module is that
space: a bench of **fifteen** mixing methods, each returning exact weights
over a register given a query, measured against the same instruments so they
can be compared honestly.

The pile
--------
| # | method | family | exactness | provenance |
|---|---|---|---|---|
| 1 | ``bundle`` | shipped | E0 | the coordinatewise mean (the t=0 end) |
| 2 | ``nearest_weights`` | shipped | E0 | the hard selector (the t=inf end) |
| 3 | ``attention_raw`` | literature | E1 | the paper's ``sigma(X A X^T) X V`` with raw scores |
| 4 | ``attention_cs`` | literature | E1 | the study's Cauchy-Schwarz fix, made two-sided |
| 5 | ``linear_attention`` | literature | E0 | linear attention (no exponential) |
| 6 | ``power_attention`` | literature | E0 | polynomial-kernel softmax ``u^p`` |
| 7 | ``rbf`` | literature | E1 | Gaussian kernel on distance, ``sigma^2 = mean d^2`` |
| 8 | ``idw`` | literature | E0 | Shepard inverse-distance-squared weighting |
| 9 | ``sparse_topk`` | literature | E1 | top-k sparse attention |
| 10 | ``rank_borda`` | literature | E0 | rank (Borda) weights by distance |
| 11 | ``pade_softmax`` | literature | E2 | ``[m/m]`` Pade of ``e^x``, exact rational function |
| 12 | ``neighbor_mean`` | original | E0 | hard attention to a soft neighborhood (top-k uniform) |
| 13 | ``exact_bridge`` | original | E0 | the literal rational dial ``(1-lam) bundle + lam nearest`` |
| 14 | ``range_softmax`` | original | E1 | softmax with the exponent range normalised to exactly ``t`` |
| 15 | ``cosine_softmax`` | original | E1 | softmax over the shipped ``signed_cosine_squared`` |

The four originals are devised from the attention study's own measured
results: (12) from the finding that the norm term decides and the dial is
real; (13) from the finding that the substrate's two ends are the exact
limits; (14) from the finding that *depth < range inverts the softmax* --
making the range a design parameter caps the depth by construction; and (15)
from the finding that the shipped cosine-squared is a semantically valid
selector, here given the soft mixture the study measured around it.

Exactness classes
-----------------
``E0``  fully exact over the rationals; no transcendental anywhere.
``E1``  a transcendental (the exponential) carried at a *declared* Taylor
        depth, computed from the measured score range by the alternating-
        series remainder bound -- the attention study's discipline, never a
        guessed constant.
``E2``  the exponential replaced by its ``[m/m]`` Pade approximant, which is
        a *rational function*: the arithmetic is exact, the function is
        approximate, and the validity range (the smallest root of the
        numerator) is computed exactly and enforced as a refusal.

Conventions
-----------
Everything inside this module is :class:`fractions.Fraction`, ``int`` or
``bool``; there are no floats and no clocks (the experiment harness that
drives the bench measures wall time outside the package).  A method that
cannot answer raises :class:`ValueError` -- a refusal is an answer, and the
bench records it as one.  Ties are broken by label so every method is a
deterministic function of its inputs, never of dict ordering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from math import factorial
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..reasoning import analogy as _an
from ..reasoning import metric as _metric

__all__ = [
    "Method", "METHODS", "METHOD_NAMES", "RefusalError",
    "bundle", "nearest_weights", "attention_raw", "attention_cs",
    "linear_attention", "power_attention", "rbf", "idw", "sparse_topk",
    "rank_borda", "pade_softmax", "neighbor_mean", "exact_bridge",
    "range_softmax", "cosine_softmax",
    "exp_depth_needed", "softmax_exact", "cs_shifted_scores",
    "validity_report", "analogy_suite", "norm_robustness", "depth_audit",
    "dial_report", "cost_report", "bench_report", "promotion_checklist",
]

#: A row set: ``(name, carrier)`` pairs, carriers exact.
Rows = Sequence[Tuple[str, Sequence[Fraction]]]
#: A weight vector: one non-negative fraction per row name, summing to 1.
Weights = Dict[str, Fraction]

#: The declared softmax precision every E1 method computes its depth for.
DEFAULT_TARGET: Fraction = Fraction(1, 10 ** 30)

#: The declared depth budget.  A range whose rigorous bound needs more than
#: this many Taylor terms is *refused*, not approximated -- the bench never
#: trades exactness for reach silently.
MAX_DECLARED_DEPTH: int = 512


class RefusalError(ValueError):
    """A method declined to answer, saying why.

    The bench distinguishes a refusal from a wrong answer: a method that
    refuses has said something true about its own validity range, which is
    the substrate's discipline, not a failure of it.
    """


# ===========================================================================
# 1.  EXACT PRIMITIVES
# ===========================================================================

def _dot(u: Sequence[Fraction], v: Sequence[Fraction]) -> Fraction:
    """The plain rational inner product (the attention family's form)."""
    return sum((a * b for a, b in zip(u, v)), Fraction(0))


def _plain_norm2(u: Sequence[Fraction]) -> Fraction:
    return _dot(u, u)


def _d2(u: Sequence[Fraction], v: Sequence[Fraction]) -> Fraction:
    """Squared Griess distance -- the shipped metric's own."""
    return _metric.distance2(u, v)


def _ranked_by_distance(query: Sequence[Fraction],
                        rows: Rows) -> List[Tuple[str, Fraction]]:
    """Rows sorted by increasing squared distance, ties by label.

    This is exactly the order :func:`glm_universal.reasoning.metric.
    rank_by_distance` produces, so every distance-space method here ranks
    exactly as the shipped selector does.
    """
    return sorted(((name, _d2(query, vec)) for name, vec in rows),
                  key=lambda nv: (nv[1], nv[0]))


def _cs_scale(query: Sequence[Fraction], rows: Rows) -> Fraction:
    """The two-sided Cauchy-Schwarz scale ``k``.

    The attention study scaled by ``max_j ||k_j||^2`` alone, which bounds
    the scores only when the *query* is itself a register row (self-attention).
    The bench's queries are arbitrary -- analogy targets -- so the scale is
    taken two-sided: ``k = max(||q||^2, max_j ||k_j||^2)``.  Then for every
    pair, ``|<q, k_j>| <= ||q|| ||k_j|| <= k`` (both norms squared are at
    most ``k``), so every score lands in ``[-1, 1]`` *by theorem, for any
    query*.
    """
    k = _plain_norm2(query)
    for _, vec in rows:
        n2 = _plain_norm2(vec)
        if n2 > k:
            k = n2
    if k == 0:
        raise RefusalError(
            "cs_scale: the query and every row are zero, so no direction "
            "is defined")
    return k


def cs_shifted_scores(query: Sequence[Fraction],
                      rows: Rows) -> Dict[str, Fraction]:
    """Shifted Cauchy-Schwarz scores ``u_j = 1 + <q, k_j> / k``.

    Every score lies in ``[0, 2]`` for any query (see :func:`_cs_scale`),
    which is what makes the exact power family and the bounded-depth
    softmaxes below possible.
    """
    k = _cs_scale(query, rows)
    return {name: Fraction(1) + _dot(query, vec) / k
            for name, vec in rows}


def exp_depth_needed(score_range: Fraction,
                     target: Fraction = DEFAULT_TARGET,
                     max_depth: int = MAX_DECLARED_DEPTH) -> int:
    """Least Taylor depth whose alternating-series error meets ``target``.

    After the row-max shift every exponent lies in ``[-score_range, 0]``,
    so the truncated-exponential error is at most ``range^(D+1)/(D+1)!``.
    Ported from the attention study: the depth is *computed* from the
    measured range, never guessed.  A range whose rigorous bound needs
    more than ``max_depth`` terms raises :class:`RefusalError` -- the
    declared budget is part of the discipline, and the bench records the
    refusal rather than trade exactness for reach.
    """
    if score_range < 0:
        raise ValueError("exp_depth_needed: range is non-negative")
    if score_range == 0:
        return 2
    d = 2
    bound = score_range ** 3 / factorial(3)
    while bound > target:
        if d >= max_depth:
            raise RefusalError(
                f"exp_depth_needed: the measured range {score_range} needs "
                f"more than the declared depth budget {max_depth}; lower "
                f"the temperature or scale the scores")
        d += 1
        bound = bound * score_range / (d + 1)
    return d


def _taylor_exp(x: Fraction, depth: int) -> Fraction:
    """``e^x`` truncated at ``depth``, exact -- for ``x <= 0`` the error is
    bounded by ``|x|^(depth+1)/(depth+1)!``."""
    if depth < 1:
        raise ValueError("_taylor_exp: depth is at least 1")
    term = Fraction(1)
    total = Fraction(1)
    for j in range(1, depth + 1):
        term = term * x / j
        total += term
    return total


def softmax_exact(scores: Dict[str, Fraction], t: Fraction = Fraction(1),
                  depth: Optional[int] = None,
                  target: Fraction = DEFAULT_TARGET) -> Weights:
    """The exact softmax over ``t * scores`` at a declared depth.

    The row-max shift puts every exponent at or below zero; the depth is
    computed from the measured range unless it is given explicitly (the
    fixed-depth control of the depth audit uses exactly that).
    """
    if not scores:
        raise RefusalError("softmax_exact: no scores to normalise")
    shifted = {name: t * (s - max(scores.values()))
               for name, s in scores.items()}
    if depth is None:
        rng = max(shifted.values()) - min(shifted.values())
        depth = exp_depth_needed(rng, target)
    exps = {name: _taylor_exp(x, depth) for name, x in shifted.items()}
    total = sum(exps.values())
    if total == 0:
        raise RefusalError(
            "softmax_exact: every truncated exponential is zero; the "
            "declared depth cannot represent this range")
    return {name: e / total for name, e in exps.items()}


def _top1_by_weight(w: Weights, query: Sequence[Fraction],
                    rows: Rows) -> str:
    """The top-weighted row; ties by shipped distance, then by label.

    Weight ties are real for the exact families (the neighborhood mean's
    ``k`` equal weights; the bundle's ``n``), and reading them off by
    label order would make the answer an alphabet artefact.  The bench's
    declared read-out convention: among equally-weighted rows the shipped
    metric decides, then the label -- deterministic, and consistent with
    how the substrate's own selector breaks distance ties.
    """
    return min(rows, key=lambda nv: (-w.get(nv[0], Fraction(0)),
                                     _d2(query, nv[1]), nv[0]))[0]


def _onehot(rows: Rows, name: str) -> Weights:
    return {n: (Fraction(1) if n == name else Fraction(0)) for n, _ in rows}


def _normalize(raw: Dict[str, Fraction]) -> Weights:
    total = sum(raw.values())
    if total <= 0:
        raise RefusalError(
            "the unnormalised weights sum to " + f"{total}, which is not a "
            "positive mass; this method cannot answer here")
    return {name: w / total for name, w in raw.items()}


def _bit_cost(x: Fraction) -> int:
    return x.numerator.bit_length() + x.denominator.bit_length()


def weight_bit_cost(weights: Weights) -> int:
    """The largest numerator-plus-denominator size among nonzero weights.

    The in-package cost instrument: exactness is not free, and this counts
    what it costs in integer growth.  (Wall time is measured outside the
    package; bits are the substrate's own currency.)
    """
    return max((_bit_cost(w) for w in weights.values() if w != 0),
               default=0)


def inverse_participation(weights: Weights) -> Fraction:
    """``1 / sum w^2`` -- the effective number of attended rows.

    Exactly 1 for a hard selection, exactly ``n`` for the bundle, and a
    rational in between otherwise: the dial coordinate, measured.
    """
    s = sum((w * w for w in weights.values()), Fraction(0))
    if s == 0:
        raise RefusalError("inverse_participation: no mass")
    return 1 / s


def mixture_vector(weights: Weights, rows: Rows) -> Tuple[Fraction, ...]:
    """The attended output ``sum_j w_j k_j``, exactly."""
    if not rows:
        raise RefusalError("mixture_vector: no rows")
    dim = len(rows[0][1])
    out = [Fraction(0)] * dim
    for name, vec in rows:
        w = weights.get(name, Fraction(0))
        if w:
            for i in range(dim):
                out[i] += w * vec[i]
    return tuple(out)


# ---------------------------------------------------------------------------
# The Pade machinery (class E2)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _pade_coeffs(m: int) -> Tuple[Fraction, ...]:
    """Numerator coefficients of the ``[m/m]`` Pade approximant of ``e^x``.

    ``R_m(x) = P_m(x) / P_m(-x)`` with
    ``P_m(x) = sum_j [(2m-j)! m! / ((2m)! j! (m-j)!)] x^j`` -- a polynomial
    with rational coefficients, so the whole approximant is a *rational
    function*: evaluated exactly it carries zero arithmetic error.
    """
    if m < 1:
        raise ValueError("_pade_coeffs: m is at least 1")
    return tuple(
        Fraction(factorial(2 * m - j) * factorial(m),
                 factorial(2 * m) * factorial(j) * factorial(m - j))
        for j in range(m + 1))


@lru_cache(maxsize=8)
def _pade_validity(m: int) -> Fraction:
    """The validity bound of the ``[m/m]`` approximant's numerator, computed.

    ``R_m(x) = P_m(x) / P_m(-x)``; for ``x <= 0`` a *negative* numerator
    would make a Pade "weight" negative -- a silent sign inversion, exactly
    the failure mode the attention study measured for the truncated Taylor
    exponential.  Here it is *computed* and enforced as a refusal instead.

    ``P_m(-x)`` for ``x >= 0`` starts at 1 and crosses zero at most once
    (the reverse-Bessel numerator of the diagonal approximant has exactly
    one negative real root for odd ``m`` and none for even ``m``).  The
    crossing is bracketed by an exact grid scan over the Cauchy *root* bound
    ``1 + max_{j<m} |c_j| / |c_m|`` -- the leading coefficient divides, so
    the bound is on the roots and not on the coefficients -- and refined by
    exact bisection on the polynomial's sign to the declared epsilon.  When
    no crossing is found (even ``m``: the numerator stays positive on the
    whole ray), the Cauchy bound itself is returned as the declared ceiling:
    conservative, never silent.
    """
    coefs = _pade_coeffs(m)
    # Cauchy's root bound for c_0 + c_1 x + ... + c_m x^m: every root zeta
    # satisfies |zeta| <= 1 + max_{j<m} |c_j| / |c_m|.  (An earlier version
    # took 1 + max_j |c_j|, which brackets only |zeta| <= 2 and so reported
    # the bound itself as the root whenever P_m(-2) > 0.)
    hi = Fraction(1) + max(abs(c) for c in coefs[:-1]) / abs(coefs[-1])

    def f(x: Fraction) -> Fraction:
        return _poly_at(coefs, -x)

    # Exact grid scan for the first + -> - crossing of P_m(-x).
    steps = 4096
    prev_x, prev_f = Fraction(0), Fraction(1)
    lo = up = None
    for i in range(1, steps + 1):
        x = hi * i / steps
        fx = f(x)
        if fx == 0:
            return x                       # an exact grid hit: the root
        if prev_f > 0 > fx:
            lo, up = prev_x, x
            break
        prev_x, prev_f = x, fx
    if lo is None:
        return hi                           # no crossing: the ceiling
    eps = Fraction(1, 10 ** 12)
    while up - lo > eps:
        mid = (lo + up) / 2
        if f(mid) > 0:
            lo = mid
        else:
            up = mid
    # The left endpoint keeps the numerator non-negative on [0, lo].
    return lo


def _poly_at(coefs: Sequence[Fraction], x: Fraction) -> Fraction:
    """``P(x)`` for ascending coefficients ``c_0 .. c_m``, exactly.

    Horner runs from the *top* coefficient down, so the iteration is
    reversed: ``P(x) = c_0 + x (c_1 + x (c_2 + ...))``.  (An earlier
    version iterated forward, which evaluates the reversed polynomial
    ``x^m P(1/x)`` -- and made the whole E2 class answer at ``1/x`` with
    a sign flip for odd ``m``.)
    """
    total = Fraction(0)
    for c in reversed(tuple(coefs)):
        total = total * x + c
    return total


def _pade_exp(x: Fraction, m: int) -> Fraction:
    """``R_m(x) = P_m(x) / P_m(-x)``, evaluated exactly.

    For ``x <= 0`` the denominator is a positive-coefficient polynomial at
    a non-negative argument, hence positive; the caller has already checked
    the numerator's sign against :func:`_pade_validity`.
    """
    coefs = _pade_coeffs(m)
    return _poly_at(coefs, x) / _poly_at(coefs, -x)


# ===========================================================================
# 2.  THE PILE -- fifteen methods
# ===========================================================================

def bundle(query: Sequence[Fraction], rows: Rows) -> Weights:
    """**Shipped, E0.**  The uniform mixture -- the coordinatewise bundle."""
    if not rows:
        raise RefusalError("bundle: no rows")
    w = Fraction(1, len(rows))
    return {name: w for name, _ in rows}


def nearest_weights(query: Sequence[Fraction], rows: Rows) -> Weights:
    """**Shipped, E0.**  The hard selector's own weights: all mass on the
    nearest row by squared Griess distance, ties by label -- the weight
    vector whose argmax is exactly :func:`metric.nearest`'s answer."""
    if not rows:
        raise RefusalError("nearest_weights: no rows")
    return _onehot(rows, _ranked_by_distance(query, rows)[0][0])


def attention_raw(query: Sequence[Fraction], rows: Rows,
                  t: Fraction = Fraction(1),
                  depth: Optional[int] = None,
                  target: Fraction = DEFAULT_TARGET) -> Weights:
    """**Literature, E1.**  The paper's attention with raw inner-product
    scores and temperature ``t`` -- kept faithfully unmodified, including
    the norm-domination the attention study measured on live registers."""
    scores = {name: _dot(query, vec) for name, vec in rows}
    return softmax_exact(scores, t, depth, target)


def attention_cs(query: Sequence[Fraction], rows: Rows,
                 t: Fraction = Fraction(1),
                 depth: Optional[int] = None,
                 target: Fraction = DEFAULT_TARGET) -> Weights:
    """**Literature, E1.**  The study's Cauchy-Schwarz fix, two-sided for
    arbitrary queries: scores ``u_j`` in ``[0, 2]`` by theorem, so the
    exponent range is at most ``2 t`` whatever the register's radii."""
    return softmax_exact(cs_shifted_scores(query, rows), t, depth, target)


def linear_attention(query: Sequence[Fraction], rows: Rows) -> Weights:
    """**Literature, E0.**  Linear attention: weights proportional to the
    shifted scores themselves, no exponential at all.  (This is ``p = 1``
    of the power family, listed separately because it is the literature's
    own name for the point.)"""
    return _normalize(cs_shifted_scores(query, rows))


def power_attention(query: Sequence[Fraction], rows: Rows,
                    p: int = 2) -> Weights:
    """**Literature, E0.**  The polynomial-kernel softmax ``w propto u^p``.

    ``p = 0`` is the bundle, ``p = 1`` linear attention, and ``p -> inf``
    the hard argmax of the inner product: an *exact* temperature dial with
    an integer knob, no transcendental anywhere.
    """
    if p < 0:
        raise ValueError("power_attention: p is non-negative")
    if p == 0:
        return bundle(query, rows)
    return _normalize({name: u ** p
                       for name, u in cs_shifted_scores(query, rows).items()})


def rbf(query: Sequence[Fraction], rows: Rows,
        t: Fraction = Fraction(1),
        sigma2: Optional[Fraction] = None,
        depth: Optional[int] = None,
        target: Fraction = DEFAULT_TARGET) -> Weights:
    """**Literature, E1.**  The Gaussian kernel ``exp(-t d^2 / sigma^2)``
    with ``sigma^2`` the register's mean squared distance (declared; a
    fixed bandwidth is the parameter).  The exponent range is *not* bounded
    -- it grows with the register's spread, and so does the depth."""
    d2s = {name: _d2(query, vec) for name, vec in rows}
    if sigma2 is None:
        sigma2 = sum(d2s.values()) / len(d2s)
    if sigma2 == 0:
        return bundle(query, rows)
    scores = {name: -t * d / sigma2 for name, d in d2s.items()}
    return softmax_exact(scores, Fraction(1), depth, target)


def idw(query: Sequence[Fraction], rows: Rows,
        alpha: int = 1) -> Weights:
    """**Literature, E0.**  Shepard's inverse-distance weighting
    ``w propto 1 / d^(2 alpha)``; an exact hit (``d = 0``) collapses to the
    one-hot, which is the nearest selector's own convention."""
    if alpha < 1:
        raise ValueError("idw: alpha is at least 1")
    d2s = {name: _d2(query, vec) for name, vec in rows}
    if any(d == 0 for d in d2s.values()):
        zero = min(n for n, d in d2s.items() if d == 0)
        return _onehot(rows, zero)
    return _normalize({name: Fraction(1) / (d ** alpha)
                       for name, d in d2s.items()})


def sparse_topk(query: Sequence[Fraction], rows: Rows,
                k: int = 4, t: Fraction = Fraction(1),
                depth: Optional[int] = None,
                target: Fraction = DEFAULT_TARGET) -> Weights:
    """**Literature, E1.**  Sparse attention: keep the ``k`` rows with the
    highest shifted scores, softmax over those, zero elsewhere.  The depth
    is computed from the *top-k* range only -- the measured discount of
    sparsity."""
    if k < 1:
        raise ValueError("sparse_topk: k is at least 1")
    u = cs_shifted_scores(query, rows)
    keep = sorted(u.items(), key=lambda nv: (-nv[1], nv[0]))[:k]
    kept_scores = {name: s for name, s in keep}
    kept_weights = softmax_exact(kept_scores, t, depth, target)
    return {name: kept_weights.get(name, Fraction(0)) for name, _ in rows}


def rank_borda(query: Sequence[Fraction], rows: Rows) -> Weights:
    """**Literature, E0.**  Borda weights by distance rank: the i-th
    nearest row (1-indexed) carries weight ``n - i + 1``.  Order without
    magnitude -- what the ranking alone knows, with no metric scale."""
    ranked = _ranked_by_distance(query, rows)
    n = len(ranked)
    return _normalize({name: Fraction(n - i)
                       for i, (name, _) in enumerate(ranked)})


def pade_softmax(query: Sequence[Fraction], rows: Rows,
                 t: Fraction = Fraction(1), m: int = 3) -> Weights:
    """**Literature, class E2.**  Softmax through the ``[m/m]`` Pade
    approximant of ``e^x`` -- a rational function, so the arithmetic is
    exact.  The validity range is *computed* (the smallest root of ``P_m``,
    exactly) and enforced: if the exponent range ``t * (u_max - u_min)``
    reaches it, the method refuses rather than emit a negative weight --
    the inversion the attention study measured, here designed out."""
    if m < 1:
        raise ValueError("pade_softmax: m is at least 1")
    u = cs_shifted_scores(query, rows)
    shifted = {name: t * (s - max(u.values())) for name, s in u.items()}
    rng = max(shifted.values()) - min(shifted.values())
    valid = _pade_validity(m)
    if rng >= valid:
        raise RefusalError(
            f"pade_softmax: exponent range {float(rng):.3g} reaches the "
            f"[{m}/{m}] validity bound {float(valid):.3g}; raise m or "
            f"lower t")
    raw = {name: _pade_exp(x, m) for name, x in shifted.items()}
    return _normalize(raw)


def neighbor_mean(query: Sequence[Fraction], rows: Rows,
                  k: int = 4) -> Weights:
    """**Original, E0.**  Hard attention to a soft neighborhood: the ``k``
    nearest rows by Griess distance, uniformly -- ``k = 1`` is exactly the
    shipped selector, ``k = n`` exactly the bundle, and the whole dial in
    between is exact rationals.  Devised from the study's findings that the
    distance (norm) term decides semantics and that the two shipped ends
    are the limits of every dial."""
    if k < 1:
        raise ValueError("neighbor_mean: k is at least 1")
    ranked = _ranked_by_distance(query, rows)[:k]
    w = Fraction(1, len(ranked))
    return {name: (w if name in {n for n, _ in ranked} else Fraction(0))
            for name, _ in rows}


def exact_bridge(query: Sequence[Fraction], rows: Rows,
                 lam: Fraction = Fraction(1, 2)) -> Weights:
    """**Original, E0.**  The literal dial: ``(1 - lam) * bundle +
    lam * nearest``.  What the attention study measured the temperature
    dial to be doing between the substrate's two shipped ends, written
    down exactly -- one rational parameter, no exponential at any point."""
    if not 0 <= lam <= 1:
        raise ValueError("exact_bridge: lam lies in [0, 1]")
    n = len(rows)
    hard = nearest_weights(query, rows)
    return {name: (1 - lam) * Fraction(1, n) + lam * hard[name]
            for name, _ in rows}


def range_softmax(query: Sequence[Fraction], rows: Rows,
                  t: Fraction = Fraction(1),
                  depth: Optional[int] = None,
                  target: Fraction = DEFAULT_TARGET) -> Weights:
    """**Original, E1.**  The range-normalised softmax: exponents
    ``-(d_j^2 - d_min^2) / (d_max^2 - d_min^2) * t``, so the exponent range
    is *exactly* ``t`` by construction, whatever the register's scale.
    Devised from the study's flagship negative result -- *depth below the
    range inverts the softmax*: here the range is the design parameter, so
    the computed depth is a function of ``t`` alone and can never surprise."""
    d2s = {name: _d2(query, vec) for name, vec in rows}
    lo, hi = min(d2s.values()), max(d2s.values())
    if hi == lo:
        return bundle(query, rows)
    scores = {name: -(d - lo) / (hi - lo) for name, d in d2s.items()}
    return softmax_exact(scores, t, depth, target)


def cosine_softmax(query: Sequence[Fraction], rows: Rows,
                   t: Fraction = Fraction(1),
                   depth: Optional[int] = None,
                   target: Fraction = DEFAULT_TARGET) -> Weights:
    """**Original, E1.**  Softmax over the shipped ``signed_cosine_squared``
    -- the study measured the substrate's cosine-squared to be a
    semantically valid selector on the meaning registers; this is the soft
    mixture around it.  Scores lie in ``[-1, 1]``, so the exponent range is
    at most ``2 t`` by construction."""
    scores = {name: _metric.signed_cosine_squared(query, vec)
              for name, vec in rows}
    return softmax_exact(scores, t, depth, target)


@dataclass(frozen=True)
class Method:
    """One bench entry: a weighting function plus its provenance."""

    name: str
    category: str                       # "shipped" | "literature" | "original"
    exactness: str                      # "E0" | "E1" | "E2"
    provenance: str
    fn: Callable[..., Weights]
    defaults: Dict[str, object] = field(default_factory=dict)
    #: ``(parameter, values)`` for the dial instrument, when the method has
    #: a knob whose endpoints are the two shipped ends.
    dial: Optional[Tuple[str, Tuple[object, ...]]] = None

    def weights(self, query: Sequence[Fraction], rows: Rows,
                **overrides) -> Weights:
        params = dict(self.defaults)
        params.update(overrides)
        return self.fn(query, rows, **params)


METHODS: Dict[str, Method] = {m.name: m for m in (
    Method("bundle", "shipped", "E0",
           "the coordinatewise mean (the t=0 end of the study's dial)",
           bundle),
    Method("nearest_weights", "shipped", "E0",
           "the hard selector's own weights (the t=inf end)",
           nearest_weights),
    Method("attention_raw", "literature", "E1",
           "arXiv 2506.18739v2, sigma(X A X^T) X V with raw scores",
           attention_raw, {"t": Fraction(1)},
           ("t", (Fraction(1, 10 ** 6), Fraction(1, 1000), Fraction(1, 256),
                  Fraction(1, 64), Fraction(1, 16), Fraction(1, 4),
                  Fraction(1)))),
    Method("attention_cs", "literature", "E1",
           "the attention study's Cauchy-Schwarz fix, two-sided",
           attention_cs, {"t": Fraction(1)},
           ("t", (Fraction(1, 10 ** 6), Fraction(1, 1024),
                  Fraction(1, 256), Fraction(1, 64), Fraction(1, 16),
                  Fraction(1, 4), Fraction(1), Fraction(4), Fraction(16),
                  Fraction(64), Fraction(256)))),
    Method("linear_attention", "literature", "E0",
           "linear attention (Katharopoulos et al.): scores as weights",
           linear_attention),
    Method("power_attention", "literature", "E0",
           "polynomial-kernel softmax u^p (p=1 is linear attention)",
           power_attention, {"p": 2},
           ("p", (0, 1, 2, 4, 8, 16, 32, 64))),
    Method("rbf", "literature", "E1",
           "Gaussian kernel on distance, sigma^2 = mean d^2",
           rbf, {"t": Fraction(1)}),
    Method("idw", "literature", "E0",
           "Shepard inverse-distance-squared weighting",
           idw, {"alpha": 1},
           ("alpha", (1, 2, 3, 4, 5, 6))),
    Method("sparse_topk", "literature", "E1",
           "top-k sparse attention over shifted scores",
           sparse_topk, {"k": 4, "t": Fraction(1)},
           ("k", (1, 2, 4, 8, 16, 32, 64))),
    Method("rank_borda", "literature", "E0",
           "Borda weights by distance rank",
           rank_borda),
    Method("pade_softmax", "literature", "E2",
           "[m/m] Pade of e^x as an exact rational function",
           pade_softmax, {"t": Fraction(1), "m": 3}),
    Method("neighbor_mean", "original", "E0",
           "hard attention to a soft neighborhood (top-k uniform)",
           neighbor_mean, {"k": 4},
           ("k", (1, 2, 4, 8, 16, 32, 64, 128))),
    Method("exact_bridge", "original", "E0",
           "the literal rational dial (1-lam) bundle + lam nearest",
           exact_bridge, {"lam": Fraction(1, 2)},
           ("lam", (Fraction(0), Fraction(1, 8), Fraction(1, 4),
                    Fraction(1, 2), Fraction(3, 4), Fraction(7, 8),
                    Fraction(1)))),
    Method("range_softmax", "original", "E1",
           "softmax with the exponent range normalised to exactly t",
           range_softmax, {"t": Fraction(1)},
           ("t", (Fraction(1, 10 ** 6), Fraction(1, 1024),
                  Fraction(1, 256), Fraction(1, 64), Fraction(1, 16),
                  Fraction(1, 4), Fraction(1), Fraction(4), Fraction(16),
                  Fraction(64), Fraction(256), Fraction(1024)))),
    Method("cosine_softmax", "original", "E1",
           "softmax over the shipped signed_cosine_squared",
           cosine_softmax, {"t": Fraction(1)},
           ("t", (Fraction(1, 10 ** 6), Fraction(1, 1024),
                  Fraction(1, 256), Fraction(1, 64), Fraction(1, 16),
                  Fraction(1, 4), Fraction(1), Fraction(4), Fraction(16),
                  Fraction(64), Fraction(256)))),
)}

METHOD_NAMES: Tuple[str, ...] = tuple(METHODS)


# ===========================================================================
# 3.  INSTRUMENT I -- validity and the shipped endpoints
# ===========================================================================

def _probe_register() -> Tuple[Tuple[str, Tuple[Fraction, ...]], ...]:
    """A small deterministic exact register for the validity probe.

    Six rows of ``Q^24`` with small integers and deliberately different
    radii, so that every method has something to be wrong about.
    """
    base = (
        (2, 1, -1, 0, 3, 0, 0, 1, -2, 0, 1, 0,
         0, 0, 4, -1, 0, 2, 0, 0, 1, 0, -3, 0),
        (0, -1, 0, 2, 0, 1, 5, 0, 0, -2, 0, 1,
         3, 0, 0, 0, 1, 0, -1, 0, 0, 2, 0, 1),
        (1, 0, 0, 0, -2, 0, 0, 1, 0, 6, 0, 0,
         0, -1, 0, 2, 0, 0, 1, 0, -4, 0, 0, 1),
        (-3, 0, 1, 0, 0, 2, 0, 0, 1, 0, 0, -1,
         0, 3, 0, 0, -2, 0, 0, 1, 0, 0, 5, 0),
        (0, 1, 0, -1, 0, 0, 2, 0, 3, 0, -1, 0,
         0, 0, 1, 0, 0, -5, 0, 2, 0, 0, 0, -1),
        (1, -2, 0, 0, 1, 0, 0, 3, 0, 0, 2, 0,
         -1, 0, 0, 1, 0, 0, -2, 0, 1, 0, 0, 4),
    )
    scales = (1, 2, 4, 8, 16, 32)
    return tuple(
        (f"row{i}", tuple(Fraction(scales[i] * v) for v in base[i]))
        for i in range(6))


def _probe_query() -> Tuple[Fraction, ...]:
    """The validity probe's query: a mid-register point, exact."""
    return tuple(Fraction(v) for v in
                 (1, 2, -1, 0, 1, 0, 3, 0, 0, -2, 1, 0,
                  0, 1, 2, 0, -1, 0, 0, 4, 0, 0, 1, 0))


def validity_report() -> Dict[str, object]:
    """Instrument I: every method returns a distribution, and the family
    endpoints are exactly the two shipped ends.

    The endpoint checks are the pre-registered identities: ``p = 0`` of the
    power family is the bundle; ``k = n`` of the neighborhood family is the
    bundle and ``k = 1`` is the shipped selector's own one-hot; ``lam = 0``
    and ``lam = 1`` of the exact bridge are the bundle and the one-hot.
    A method that fails any of these is not a dial, and the report says so.
    """
    rows = _probe_register()
    query = _probe_query()
    methods_ok: Dict[str, bool] = {}
    notes: List[str] = []
    for name in METHOD_NAMES:
        try:
            w = METHODS[name].weights(query, rows)
            total = sum(w.values())
            methods_ok[name] = (total == 1 and all(v >= 0 for v in w.values())
                                and set(w) == {n for n, _ in rows})
            if not methods_ok[name]:
                notes.append(f"{name}: sum={total}, min={min(w.values())}")
        except (RefusalError, ValueError) as exc:
            # A depth-budget refusal is a *feasibility* fact, recorded by
            # the depth audit; the validity probe re-tests the method at a
            # feasible temperature (the argmax is a temperature invariant,
            # and the distribution shape is what is being probed here).
            probed = False
            if "t" in METHODS[name].defaults:
                try:
                    w = METHODS[name].weights(query, rows,
                                              t=Fraction(1, 1000))
                    total = sum(w.values())
                    methods_ok[name] = (total == 1
                                        and all(v >= 0 for v in w.values())
                                        and set(w) == {n for n, _ in rows})
                    notes.append(
                        f"{name}: probed at t=1/1000 (default temperature "
                        f"exceeds the declared depth budget: {exc})")
                    probed = True
                except (RefusalError, ValueError):
                    pass
            if not probed:
                methods_ok[name] = False
                notes.append(f"{name}: refused ({exc})")
    n = len(rows)
    endpoints = {
        "power_p0_is_bundle":
            power_attention(query, rows, p=0) == bundle(query, rows),
        "neighbor_k1_is_nearest":
            neighbor_mean(query, rows, k=1) == nearest_weights(query, rows),
        "neighbor_kn_is_bundle":
            neighbor_mean(query, rows, k=n) == bundle(query, rows),
        "bridge_lam0_is_bundle":
            exact_bridge(query, rows, lam=Fraction(0)) == bundle(query, rows),
        "bridge_lam1_is_nearest":
            exact_bridge(query, rows, lam=Fraction(1))
            == nearest_weights(query, rows),
        "bundle_ipr_is_n":
            inverse_participation(bundle(query, rows)) == n,
        "nearest_ipr_is_1":
            inverse_participation(nearest_weights(query, rows)) == 1,
    }
    return {
        "probe_rows": n,
        "methods_ok": methods_ok,
        "all_valid": all(methods_ok.values()),
        "endpoints": endpoints,
        "all_endpoints_hold": all(endpoints.values()),
        "notes": notes,
    }


# ===========================================================================
# 4.  INSTRUMENT II -- the analogy ground truth
# ===========================================================================

#: The two read-outs.  ``argmax`` takes the top-weighted row as the answer
#: (selection semantics); ``mixture`` decodes the attended mixture vector by
#: the shipped nearest (the read-out the attention paper implies).  Hard
#: methods make them coincide; soft ones do not, and the difference is a
#: finding.
READOUTS: Tuple[str, ...] = ("argmax", "mixture")


def analogy_suite(session, method_name: str, readout: str = "argmax",
                  **overrides) -> Dict[str, object]:
    """Instrument II: the shipped analogy benchmarks, retrieval swapped.

    The construction is exactly the shipped solver's: ``D* = C + (B - A)``
    over full carriers, projected onto the session's own default subspace
    for the domain, with ``A``, ``B`` and ``C`` excluded from the pool.  The
    *only* thing that varies between methods is the retrieval scoring that
    turns ``D*`` into an answer -- the step the shipped session performs
    with ``metric.nearest``.  Ground truth is external (the periodic table,
    ordinary English, SI dimensional analysis), taken from the package's
    own benchmark suites.

    ``readout`` selects the answer rule (see :data:`READOUTS`); the bundle
    has no selection and is scored in the mixture read-out only.  A refusal
    is recorded as a refusal, never as a wrong answer.
    """
    from ..benchmarks import suites as _suites
    from ..runtime.session import DEFAULT_SUBSPACE

    if readout not in READOUTS:
        raise ValueError(f"analogy_suite: readout {readout!r}")
    method = METHODS[method_name]
    domains = (
        ("chemistry", _suites.CHEMISTRY_ANALOGIES, "name"),
        ("lexicon", _suites.SEMANTIC_ANALOGIES, "name"),
        ("physics", _suites.PHYSICS_ANALOGIES, "dimension"),
    )
    per_domain: Dict[str, Dict[str, object]] = {}
    items: List[Dict[str, object]] = []
    refusals = 0
    passed_total = 0
    total_total = 0
    for domain, cases, scoring in domains:
        objs = {o.name: o for o in session.register(domain)}
        layout = tuple(next(iter(objs.values())).layout)
        subspace = DEFAULT_SUBSPACE[domain]
        names = _an.SUBSPACES[subspace]
        idx = _an.subspace_indices(layout, names)
        rows_full = [(name, tuple(Fraction(c) for c in obj.carrier))
                     for name, obj in objs.items()]
        pool = [(name, _an.project_subspace(vec, idx))
                for name, vec in rows_full]
        physics_exps: Dict[str, object] = {}
        if scoring == "dimension":
            from ..data_objects import physics as do_physics
            physics_exps = {q.name: q.exps_ext10
                            for q in do_physics.load_physics_register()}
        domain_passed = 0
        domain_refusals = 0
        for a, b, c, target in cases:
            dstar = _an.analogy_target(objs[a].carrier, objs[b].carrier,
                                       objs[c].carrier)
            query = _an.project_subspace(dstar, idx)
            candidates = [(name, vec) for name, vec in pool
                          if name not in (a, b, c)]
            item = {"domain": domain, "task": f"{a} : {b} :: {c} : ?",
                    "expected": target}
            if readout == "argmax" and method_name == "bundle":
                item["observed"] = None
                item["note"] = ("the bundle carries no selection; scored in "
                                "the mixture read-out only")
                items.append(item)
                continue
            try:
                w = method.weights(query, candidates, **overrides)
            except (RefusalError, ValueError) as exc:
                item["observed"] = None
                item["refusal"] = str(exc)
                items.append(item)
                domain_refusals += 1
                refusals += 1
                continue
            if readout == "argmax":
                answer = _top1_by_weight(w, query, candidates)
            else:
                m = mixture_vector(w, candidates)
                answer = _metric.rank_by_distance(m, candidates)[0][0]
            item["observed"] = answer
            if scoring == "name":
                item_ok = answer == target
            else:
                item_ok = (physics_exps.get(answer)
                           == physics_exps.get(target))
                item["exact_name"] = answer == target
            item["passed"] = item_ok
            items.append(item)
            domain_passed += item_ok
            passed_total += item_ok
            total_total += 1
        per_domain[domain] = {
            "passed": domain_passed, "total": len(cases),
            "score": (Fraction(domain_passed, len(cases))
                      if len(cases) else None),
            "refusals": domain_refusals, "scoring": scoring,
        }
    return {
        "method": method_name, "readout": readout,
        "per_domain": per_domain,
        "total": {"passed": passed_total, "total": total_total,
                  "score": (Fraction(passed_total, total_total)
                            if total_total else None)},
        "refusals": refusals,
        "items": items,
    }


# ===========================================================================
# 5.  INSTRUMENT III -- the norm-domination probe
# ===========================================================================

#: Directions of the planted register: eight pairwise-orthogonal supports
#: of three coordinates each (so semantic membership is exact, not graded).
_PLANTED_DIRS: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(pat[i - 3 * d] if 3 * d <= i < 3 * d + 3 else 0
          for i in range(24))
    for d, pat in enumerate(((1, 2, -1), (2, -1, 1), (-1, 1, 2), (1, -2, 1),
                             (2, 1, -1), (-2, 1, 1), (1, 1, -2), (-1, 2, 1))))
_PLANTED_RADII: Tuple[int, ...] = (1, 8, 64, 512)
#: Giant decoys: huge-radius rows whose support meets every direction, so
#: they are related to everything and belong to nothing -- the register's
#: norm-decoys, the failure mode the attention study measured.
_GIANT_PATTERNS: Tuple[Tuple[int, ...], ...] = (
    tuple(1 if i % 2 == 0 else -1 for i in range(24)),
    tuple(1 if i % 3 == 0 else -1 for i in range(24)),
    tuple(1 if i % 4 == 0 else 2 for i in range(24)),
    tuple(2 if i % 5 == 0 else -1 for i in range(24)),
)


def _planted_register() -> Tuple[Rows, Tuple[Fraction, ...], List[str]]:
    """The synthetic register, its first query, and the giant names.

    Returns ``(rows, query, giant_names)`` -- full detail for the audit;
    :func:`norm_robustness` walks all eight queries.
    """
    rows: List[Tuple[str, Tuple[Fraction, ...]]] = []
    for d, direction in enumerate(_PLANTED_DIRS):
        for r in _PLANTED_RADII:
            rows.append((f"sem{d}_r{r}",
                         tuple(Fraction(r * v) for v in direction)))
    giant_names: List[str] = []
    for l, pattern in enumerate(_GIANT_PATTERNS):
        name = f"giant{l}"
        giant_names.append(name)
        rows.append((name, tuple(Fraction(10 ** 6 * v) for v in pattern)))
    query = _planted_query(0)
    return tuple(rows), query, giant_names


def _planted_query(d: int) -> Tuple[Fraction, ...]:
    """A mid-radius point of direction ``d`` with a one-percent leak
    into the next -- the register's honest idea of a noisy query."""
    return tuple(
        Fraction(64 * _PLANTED_DIRS[d][i])
        + Fraction(_PLANTED_DIRS[(d + 1) % 8][i], 100)
        for i in range(24))


def norm_robustness(method_name: str, **overrides) -> Dict[str, object]:
    """Instrument III: does the method's selection track meaning or mass?

    The planted register: eight orthogonal semantic directions at radii
    spanning 1 to 512 (four rows each), plus four giant decoys at radius a
    million whose support touches every direction.  Each query is a
    mid-radius point of one direction with a one-percent leak into the
    next.  The truth for query ``i`` is the rows of direction ``i``.

    Reported per method: how often the top-1 row is the query's own
    direction (semantic recovery), how often it is a giant (capture -- the
    attention study's norm-domination, planted and reproducible), and how
    often the mixture decodes to the right direction.  When the softmax
    itself is beyond the declared depth budget the selection is re-taken at
    a temperature of ``10^-8``: a positive scale cannot reorder, so the
    argmax is a temperature invariant -- and the report says the mixture
    was refused rather than silently approximated.
    """
    method = METHODS[method_name]
    rows, _, giant_names = _planted_register()
    giants = set(giant_names)
    top1_semantic = 0
    top1_giant = 0
    mixture_semantic = 0
    mixture_refused = 0
    selection_refused = 0
    notes: List[str] = []
    for d in range(8):
        query = _planted_query(d)
        truth = {f"sem{d}_r{r}" for r in _PLANTED_RADII}
        w = None
        try:
            w = method.weights(query, rows, **overrides)
        except (RefusalError, ValueError) as exc:
            if "t" in method.defaults or method_name in (
                    "attention_raw", "attention_cs", "rbf", "sparse_topk",
                    "range_softmax", "cosine_softmax"):
                try:
                    w = method.weights(query, rows,
                                       t=Fraction(1, 10 ** 8), **overrides)
                    notes.append(
                        f"direction {d}: softmax beyond the declared depth "
                        f"budget at default temperature; selection re-taken "
                        f"at t=10^-8 (a positive scale cannot reorder); "
                        f"mixture refused: {exc}")
                except (RefusalError, ValueError):
                    selection_refused += 1
            else:
                selection_refused += 1
        if w is None:
            continue
        top1 = _top1_by_weight(w, query, rows)
        if top1 in truth:
            top1_semantic += 1
        elif top1 in giants:
            top1_giant += 1
        try:
            m = mixture_vector(w, rows)
            decoded = _metric.rank_by_distance(m, rows)[0][0]
            mixture_semantic += decoded in truth
        except (RefusalError, ValueError):
            mixture_refused += 1
    return {
        "method": method_name,
        "queries": 8, "rows": len(rows), "giants": len(giants),
        "top1_semantic": Fraction(top1_semantic, 8),
        "top1_giant_capture": Fraction(top1_giant, 8),
        "mixture_semantic": Fraction(mixture_semantic, 8),
        "mixture_refused": mixture_refused,
        "selection_refused": selection_refused,
        "notes": notes,
    }


# ===========================================================================
# 6.  INSTRUMENT IV -- the depth audit and the inversion control
# ===========================================================================


def _score_range(method_name: str, query: Sequence[Fraction], rows: Rows,
                 **overrides) -> Optional[Fraction]:
    """The exponent range a method's softmax will see, measured.

    ``None`` for the exact classes (no exponential); the quantity the
    computed depth is a function of, for the declared-depth ones.
    """
    params = dict(METHODS[method_name].defaults)
    params.update(overrides)
    t = params.get("t", Fraction(1))
    if method_name == "attention_raw":
        scores = [_dot(query, vec) for _, vec in rows]
        return t * (max(scores) - min(scores))
    if method_name in ("attention_cs", "pade_softmax"):
        u = cs_shifted_scores(query, rows)
        return t * (max(u.values()) - min(u.values()))
    if method_name == "rbf":
        d2s = [_d2(query, vec) for _, vec in rows]
        sigma2 = params.get("sigma2") or (sum(d2s) / len(d2s))
        return t * (max(d2s) - min(d2s)) / sigma2
    if method_name == "sparse_topk":
        u = cs_shifted_scores(query, rows)
        keep = sorted(u.values(), reverse=True)[:params.get("k", 4)]
        return t * (max(keep) - min(keep))
    if method_name == "range_softmax":
        # The design point: the range *is* the temperature, exactly.
        return t
    if method_name == "cosine_softmax":
        cs = [_metric.signed_cosine_squared(query, vec) for _, vec in rows]
        return t * (max(cs) - min(cs))
    return None


def _register_rows(session, domain: str) -> Tuple[Rows, Tuple[Fraction, ...]]:
    rows = tuple((obj.name, tuple(Fraction(c) for c in obj.carrier))
                 for obj in session.register(domain))
    return rows, rows[0][1]


def depth_audit(session, domain: str = "lexicon") -> Dict[str, object]:
    """Instrument IV: what exactness costs, and why it is declared.

    For every method with a transcendental, the measured exponent range on
    the live register, the computed depth at the declared precision, and a
    refusal when the range exceeds the declared budget.  For the Pade
    class: the computed validity bound, and the measured disagreement
    against a fourfold-depth Taylor reference (the attention study's
    "deeper reference" discipline, applied to class E2).

    The closing control reproduces the attention study's flagship negative
    result: raw-register attention at a FIXED depth below its score range
    inverts the softmax -- the top-1 orders backwards while the weights
    still look like a distribution.  It is the reason the computed-depth
    discipline exists, re-measured here as the bench's own control.
    """
    rows, query = _register_rows(session, domain)
    entries: Dict[str, Dict[str, object]] = {}
    for name in METHOD_NAMES:
        method = METHODS[name]
        rng = _score_range(name, query, rows)
        entry: Dict[str, object] = {"exactness": method.exactness}
        if rng is not None:
            entry["range"] = rng
            try:
                depth = exp_depth_needed(rng)
                entry["depth"] = depth
                entry["feasible"] = True
            except RefusalError as exc:
                entry["feasible"] = False
                entry["refusal"] = str(exc)
        if method.exactness == "E2":
            m = method.defaults.get("m", 3)
            valid = _pade_validity(m)
            entry["validity_bound"] = valid
            entry["bound_is_computed"] = True
            try:
                w_pade = method.weights(query, rows)
                ref_depth = 4 * exp_depth_needed(
                    _score_range("attention_cs", query, rows))
                w_ref = attention_cs(query, rows, depth=ref_depth)
                entry["max_weight_disagreement_vs_4x_reference"] = max(
                    (abs(w_pade[n] - w_ref[n]) for n in w_pade), default=0)
            except (RefusalError, ValueError) as exc:
                entry["refusal"] = str(exc)
        entries[name] = entry

    # The inversion control: raw attention, temperature 1/1000, on the
    # first four rows -- one query per row, fixed depths swept.
    block = rows[:4]
    depths = (4, 8, 12, 16, 20, 24, 28, 32, 48, 64, 96)
    control: List[Dict[str, object]] = []
    for d in depths:
        correct = 0
        for name, vec in block:
            q = vec
            scores = {n: _dot(q, v) for n, v in block}
            true_top1 = sorted(scores.items(),
                               key=lambda nv: (-nv[1], nv[0]))[0][0]
            try:
                w = attention_raw(q, block, t=Fraction(1, 1000), depth=d)
                got = sorted(w.items(),
                             key=lambda nv: (-nv[1], nv[0]))[0][0]
                correct += got == true_top1
            except (RefusalError, ValueError):
                pass
        control.append({"depth": d, "top1_correct": correct})
    return {
        "register": domain, "rows": len(rows), "entries": entries,
        "declared_target": DEFAULT_TARGET,
        "max_declared_depth": MAX_DECLARED_DEPTH,
        "inversion_control": {
            "method": "attention_raw", "temperature": Fraction(1, 1000),
            "queries": 4, "depths": control,
            "reproduced": any(c["top1_correct"] < 4 for c in control),
        },
    }


# ===========================================================================
# 7.  INSTRUMENT V -- the dial
# ===========================================================================

def dial_report(session, domain: str = "lexicon") -> Dict[str, object]:
    """Instrument V: every knob, swept -- max weight and effective support.

    The dial coordinate is the inverse participation ratio
    (:func:`inverse_participation`): exactly 1 at the hard end, exactly
    ``n`` at the bundle end, a rational in between.  A refusal at a dial
    setting is recorded as one -- the temperature ceilings are findings,
    not gaps.
    """
    rows, query = _register_rows(session, domain)
    out: Dict[str, Dict[str, object]] = {}
    for name in METHOD_NAMES:
        method = METHODS[name]
        if method.dial is None:
            continue
        param, values = method.dial
        curve: List[Dict[str, object]] = []
        for value in values:
            try:
                w = method.weights(query, rows, **{param: value})
                curve.append({
                    "value": value,
                    "max_weight": max(w.values()),
                    "ipr": inverse_participation(w),
                })
            except (RefusalError, ValueError) as exc:
                curve.append({"value": value, "refusal": str(exc)})
        out[name] = {"param": param, "curve": curve}
    return {"register": domain, "rows": len(rows), "dials": out}


# ===========================================================================
# 8.  INSTRUMENT VI -- cost in the substrate's own currency
# ===========================================================================

def cost_report(session, domain: str = "lexicon") -> Dict[str, object]:
    """Instrument VI: exactness priced in integer growth.

    Bits, not seconds: the largest numerator-plus-denominator size among
    the weights, and the same for the attended mixture vector.  Wall time
    is the harness's business (clocks live outside the package); this is
    what the *arithmetic itself* costs, which is the cost the substrate
    can see.  Declared depth is reported beside it, and a refusal is
    recorded as one.
    """
    rows, query = _register_rows(session, domain)
    out: Dict[str, Dict[str, object]] = {}
    for name in METHOD_NAMES:
        method = METHODS[name]
        rng = _score_range(name, query, rows)
        entry: Dict[str, object] = {
            "exactness": method.exactness,
            "range": rng,
        }
        if rng is not None:
            try:
                entry["depth"] = exp_depth_needed(rng)
            except RefusalError as exc:
                entry["depth_refusal"] = str(exc)
        try:
            w = method.weights(query, rows)
            entry["weight_bits"] = weight_bit_cost(w)
            entry["mixture_bits"] = _bit_cost_of_vector(
                mixture_vector(w, rows))
            entry["ipr"] = inverse_participation(w)
        except (RefusalError, ValueError) as exc:
            entry["refusal"] = str(exc)
        out[name] = entry
    return {"register": domain, "rows": len(rows), "methods": out}


def _bit_cost_of_vector(vec: Sequence[Fraction]) -> int:
    return max((_bit_cost(x) for x in vec), default=0)


# ===========================================================================
# 9.  THE BENCH REPORT -- the pre-registered verdict
# ===========================================================================

#: The pre-registered definition of "best", fixed before any measurement
#: was taken.  A method is *substrate-best* iff it (1) returns a valid
#: distribution, (2) is fully exact over the rationals (class E0), (3)
#: matches or beats the shipped selector's analogy total in the argmax
#: read-out, (4) recovers the planted semantic direction on at least 7 of
#: 8 norm-domination queries, and (5) costs at most a hundred times the
#: bundle's weight bits.  Among methods that meet the bar, the incumbent
#: (a shipped method) wins exact ties; a newcomer must strictly exceed it.
BEST_BAR: Dict[str, object] = {
    "valid_distribution": True,
    "exactness": "E0",
    "analogy_argmax_at_least_the_shipped_selector": True,
    "norm_top1_semantic_at_least": Fraction(7, 8),
    "weight_bits_at_most_bundle_times": 100,
}


def bench_report(session, domain: str = "lexicon") -> Dict[str, object]:
    """Every instrument, every method, one table -- recomputed from nothing.

    The winner is decided by :data:`BEST_BAR`, which was written down
    before the first measurement ran.  A second prize is reported beside
    it: the best *soft* method (effective support above 1), because the
    bar's tie-break favours the incumbent selector, and the interesting
    question for a substrate that already ships the hard end is what it
    should adopt *beside* it.
    """
    validity = validity_report()
    methods: Dict[str, Dict[str, object]] = {}
    nearest_total: Optional[Fraction] = None
    bundle_bits: Optional[int] = None
    for name in METHOD_NAMES:
        method = METHODS[name]
        argmax = analogy_suite(session, name, "argmax")
        mixture = analogy_suite(session, name, "mixture")
        norm = norm_robustness(name)
        entry: Dict[str, object] = {
            "category": method.category,
            "exactness": method.exactness,
            "provenance": method.provenance,
            "valid": validity["methods_ok"][name],
            "analogy_argmax": argmax["total"],
            "analogy_argmax_refusals": argmax["refusals"],
            "analogy_mixture": mixture["total"],
            "norm": {k: norm[k] for k in
                     ("top1_semantic", "top1_giant_capture",
                      "mixture_semantic", "mixture_refused",
                      "selection_refused")},
        }
        methods[name] = entry
        if name == "nearest_weights":
            nearest_total = argmax["total"]["score"]
        if name == "bundle":
            pass  # bits filled after the cost pass
    costs = cost_report(session, domain)
    for name in methods:
        methods[name]["depth"] = costs["methods"][name].get("depth")
        methods[name]["range"] = costs["methods"][name].get("range")
        methods[name]["weight_bits"] = costs["methods"][name].get(
            "weight_bits")
        methods[name]["mixture_bits"] = costs["methods"][name].get(
            "mixture_bits")
        methods[name]["ipr"] = costs["methods"][name].get("ipr")
        methods[name]["cost_refusal"] = costs["methods"][name].get("refusal")
    bundle_bits = methods["bundle"].get("weight_bits") or 1

    # The pre-registered bar.
    eligible: List[str] = []
    near_misses: List[Dict[str, object]] = []
    for name, entry in methods.items():
        if name == "bundle":
            continue  # no selection: cannot be the best selector
        failures: List[str] = []
        if not entry["valid"]:
            failures.append("valid_distribution")
        if entry["exactness"] != BEST_BAR["exactness"]:
            failures.append(f"exactness {entry['exactness']}")
        score = entry["analogy_argmax"]["score"]
        if score is None or nearest_total is None or score < nearest_total:
            failures.append(f"analogy argmax {score} < {nearest_total}")
        if entry["norm"]["top1_semantic"] < BEST_BAR[
                "norm_top1_semantic_at_least"]:
            failures.append(
                f"norm top1 {entry['norm']['top1_semantic']}")
        bits = entry.get("weight_bits")
        if bits is None or bits > BEST_BAR["weight_bits_at_most_bundle_times"
                                           ] * bundle_bits:
            failures.append(f"weight bits {bits}")
        if failures:
            near_misses.append({"method": name, "failed": failures})
        else:
            eligible.append(name)

    def rank_key(name: str):
        entry = methods[name]
        score = entry["analogy_argmax"]["score"]
        # The bundle carries no selection: it cannot outrank anything.
        score = Fraction(-1) if score is None else score
        return (-score,
                0 if entry["category"] == "shipped" else 1,
                entry.get("weight_bits") or 0)

    winner = sorted(eligible, key=rank_key)[0] if eligible else None

    soft = [n for n, e in methods.items()
            if e.get("ipr") is not None and e["ipr"] > 1]
    best_soft = sorted(soft, key=rank_key)[0] if soft else None

    return {
        "methods": methods,
        "nearest_argmax_total": nearest_total,
        "best_bar": {k: str(v) for k, v in BEST_BAR.items()},
        "eligible": eligible,
        "near_misses": near_misses,
        "winner": winner,
        "winner_is_incumbent": (winner is not None and
                                methods[winner]["category"] == "shipped"),
        "best_soft_method": best_soft,
        "validity": validity,
        "costs": costs,
    }


def _pade_bound_enforced() -> bool:
    """Measured: the Pade bound is exact, and beyond it the method refuses.

    Both halves are measured on the probe register, not trusted: below the
    bound (temperature 1) the method answers with a distribution, and at a
    temperature whose exponent range reaches the bound it refuses.  A bound
    that is never enforced is an assertion, and fails this check.
    """
    try:
        bound = _pade_validity(3)
        if not isinstance(bound, Fraction) or bound <= 0:
            return False
        rows = _probe_register()
        query = _probe_query()
        w = pade_softmax(query, rows, t=Fraction(1), m=3)
        if sum(w.values()) != 1 or any(v < 0 for v in w.values()):
            return False
        try:
            pade_softmax(query, rows, t=Fraction(4096), m=3)
            return False                # answered beyond the bound: not
        except RefusalError:            # enforced
            return True
    except (RefusalError, ValueError, ZeroDivisionError):
        return False


def promotion_checklist(session=None,
                        report: Optional[Dict[str, object]] = None
                        ) -> Dict[str, object]:
    """What would have to hold for this module to leave the sandbox.

    The same shape as every sandbox occupant's checklist: the safety line
    is the sandbox rule (nothing the system computes with imports this
    module, and deleting it moves no answer); the utility line is the
    pre-registered best bar; and the three absent lines -- a wired query
    kind, a compiled Lean specification, a corpus-registered study -- fail
    loudly until they are met.

    Called with no arguments (as :func:`..occupancy_report` calls every
    occupant) it builds its own session and recomputes the bench from
    nothing -- the checklist is computed, never asserted.
    """
    if report is None:
        if session is None:
            from ..runtime.session import GeometricSession
            session = GeometricSession()
        report = bench_report(session)
    methods = report["methods"]
    valid = report["validity"]
    e1 = [n for n, e in methods.items() if e["exactness"] == "E1"]
    e1_feasible = [n for n in e1 if methods[n].get("depth") is not None]
    winner = report["winner"]
    checks = {
        "all_fifteen_methods_return_valid_distributions":
            bool(valid["all_valid"]),
        "family_endpoints_are_exactly_the_shipped_ends":
            bool(valid["all_endpoints_hold"]),
        "a_method_meets_the_pre_registered_best_bar":
            winner is not None,
        "the_bar_is_met_by_a_fully_exact_method":
            winner is not None and methods[winner]["exactness"] == "E0",
        "winner_matches_or_beats_the_shipped_selector":
            winner is not None and (
                methods[winner]["analogy_argmax"]["score"]
                >= report["nearest_argmax_total"]),
        "winner_survives_the_norm_domination_probe":
            winner is not None and (
                methods[winner]["norm"]["top1_semantic"]
                >= BEST_BAR["norm_top1_semantic_at_least"]),
        "every_transcendental_carries_a_computed_depth":
            all(methods[n].get("depth") is not None for n in e1_feasible),
        "pade_validity_enforced_as_computed_bound": _pade_bound_enforced(),
        "wired_to_a_query_kind": False,
        "lean_specification_compiled": False,
        "study_registered_in_corpus": False,
    }
    headline_winner = winner if winner is not None else "none yet"
    return {
        "checks": checks,
        "order": tuple(checks),
        "ready": all(checks.values()),
        "winner": winner,
        "best_soft_method": report.get("best_soft_method"),
        "headline": (
            f"the bench's pre-registered winner is {headline_winner}, with "
            f"{report.get('best_soft_method')} the best soft method beside "
            "it; the module is a measured comparison, not yet a faculty"),
    }


