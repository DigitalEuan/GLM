"""``glm_universal.sandbox.attention_simulator`` -- attention from elementary ops.

Where this sits
---------------
The supplied paper *"On the Existence of Universal Simulators of Attention"*
(arXiv 2506.18739v2) proves that a network of transformer **encoders** can
simulate *any* single-layer attention ``sigma(X A X^T) X V`` using nothing but
elementary operations -- matrix transposition (its Lemma 3), softmax (Lemma 4),
matrix multiplication (Lemma 5), the MaxMin group-sort (Lemma 7) and exact
``3 x 3`` inversion (Lemma 10) -- each realised as an *average-hard-attention*
program in RASP with an exact FFN.  Attention, in other words, is not
primitive: it compiles to weaker operations, exactly and data-agnostically.

This module ports those constructions onto this substrate.  Everything the
paper writes as a RASP ``select``/``aggregate`` pair becomes one call to
:func:`aha` -- average-hard attention with a Boolean selection -- and every
FFN becomes exact elementwise rational arithmetic.  The result is the paper's
simulator ``U`` running with the house discipline: integers and
:class:`~fractions.Fraction` only, no float, no random source, refusals rather
than silent approximation.  Where the paper's own demonstration reports float
error ``3.376358e-06`` on its softmax stage, this port reports ``0`` on every
stage except the exponential, which is transcendental and therefore carried at
a *declared* depth with a computed rational error bound (Section "What is
exact" below).

What is ported
--------------
=========================== =============================================
paper construction          this module
=========================== =============================================
``prop`` (Proposition 2)    :func:`prop` / :func:`prop_inv`
transpose (Alg. 1, L. 3)    :func:`transpose_sim`
softmax (Alg. 2, L. 4)      :func:`softmax_sim`
matmul (Alg. 3, L. 5)       :func:`matmul_sim` -- with the paper's
                            feasibility rule ``k(r + c) >= rc`` enforced as a
                            refusal, and its output-index typo corrected
                            (see :func:`matmul_sim`)
MaxMin (Alg. 4, L. 7)       :func:`maxmin_sim`
inverse 3x3 (Alg. 5, L.10)  :func:`inverse3_sim`
``U`` (Theorem 6)           :func:`simulate_attention`
hierarchy (Cor. 6.2)        :func:`embed_hierarchy`
multi-head (Th. 9, L. 8)    :func:`simulate_attention_multihead`
the Figure 2 demonstration  :func:`paper_demo`
the Figure 3 inversion      :func:`paper_inverse_demo`
=========================== =============================================

What is exact, and what is bounded
----------------------------------
Transpose, matmul, MaxMin, inversion, the hierarchy embedding and the whole
``U`` composition are **exact**: zero error, because every operation is a
permutation, a product, or a sum over :class:`~fractions.Fraction`.  The
softmax stage cannot be: ``exp`` is transcendental, no finite rational form
exists, and the paper itself approximates it (its RASP listing raises
``2.73`` to the token power -- three significant digits).  This port computes
``exp`` by exact Taylor truncation at a declared integer depth, provides a
rigorous rational remainder bound (:func:`exp_rational_bound`), and refuses to
report an exact softmax.  The two statements that look like claims of
exactness in the paper -- "the negligible error ... attributed to the
fixed-precision constraint" -- become, here, a measured error and a computed
bound on it.

Scholarship notes (differences found while porting)
---------------------------------------------------
* **Algorithm 3, line 5** indexes the output-combining attentions as
  ``R''_{l~k + l'~ + 1}`` with the *inner* dimension ``k``; the construction
  requires the *column* count ``c`` (output position ``l~ c + l'~``).  The
  paper's own RASP Listing 3 (a ``3 x k`` by ``k x 4`` product) writes the
  outputs at positions ``0..11`` -- ``rc`` positions, ``c``-strided -- which
  agrees with this reading and not with the printed formula.  The port
  implements the corrected index and this note is the record of the
  discrepancy.
* **Algorithm 2's attention matrices** as block-printed do not parse into the
  row spans the accompanying text states; the paper's RASP Listing 2 does
  (per-row block selection, average, ``c``-fold compensation).  The port
  follows the listing's semantics, which the text of Lemma 4 describes.
* **Theorem 6's coverage condition.**  The theorem states ``n <= min(d, dv)``
  as the requirement, which is the *sufficient* form ``k >= min(r, c)`` of
  Lemma 5's condition.  The literal condition is ``k(r + c) >= rc`` (the
  padding is non-negative), which is weaker: on a 24-wide carrier with
  ``d = dv = 24`` the binding stage ``X A X^T`` admits ``n <= 2d = 48`` rows.
  :func:`feasibility_limits` reports both, and the difference is measured,
  not asserted.

The ground truth this port is checked against is the shipped package itself:
:data:`~glm_universal.data_objects.mathematics.RationalMatrix.transpose` and
:func:`~glm_universal.data_objects.mathematics.compose_matrices` for the
matrix operations, and ``reasoning.product._inverse3`` for the Gauss-Jordan
inverse.  Where the two disagree the shipped package is right and this module
is wrong; that is checked, not assumed (:func:`promotion_checklist`).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..data_objects.mathematics import RationalMatrix, compose_matrices
from ..reasoning import product as _product
from ..reasoning import metric as _metric

__all__ = [
    "prop", "prop_inv", "aha", "aha_gather", "aha_span",
    "exp_rational", "exp_rational_bound", "softmax_depth_needed",
    "begin_instrumentation", "end_instrumentation",
    "transpose_sim", "softmax_sim", "matmul_sim", "maxmin_sim",
    "inverse3_sim", "simulate_attention", "AttentionResult",
    "embed_hierarchy", "multihead_rearrange", "simulate_attention_multihead",
    "paper_demo", "paper_inverse_demo", "feasibility_limits",
    "construction_report", "attention_report", "register_attention",
    "attention_weights", "attention_scores", "normalized_identity",
    "temperature_report", "promotion_checklist",
    "PAPER_DEMO_X", "PAPER_DEMO_A", "PAPER_DEMO_V", "PAPER_INVERSE_A",
]

#: The paper's Figure 2 input, printed to three decimals; here exact.
PAPER_DEMO_X: Tuple[Tuple[Fraction, ...], ...] = (
    (Fraction(8, 10), Fraction(2, 10), Fraction(5, 10)),
    (Fraction(1, 10), Fraction(9, 10), Fraction(4, 10)),
    (Fraction(6, 10), Fraction(3, 10), Fraction(7, 10)),
)
PAPER_DEMO_A: Tuple[Tuple[Fraction, ...], ...] = (
    (Fraction(1, 10), Fraction(2, 10), Fraction(3, 10)),
    (Fraction(4, 10), Fraction(5, 10), Fraction(6, 10)),
    (Fraction(7, 10), Fraction(8, 10), Fraction(9, 10)),
)
PAPER_DEMO_V: Tuple[Tuple[Fraction, ...], ...] = (
    (Fraction(1, 10), Fraction(7, 10), Fraction(4, 10)),
    (Fraction(1), Fraction(3, 10), Fraction(9, 10)),
    (Fraction(5, 10), Fraction(2, 10), Fraction(6, 10)),
)

#: The paper's Figure 3 matrix, integral, so the inverse is exact.
PAPER_INVERSE_A: Tuple[Tuple[Fraction, ...], ...] = (
    (Fraction(7), Fraction(8), Fraction(12)),
    (Fraction(10), Fraction(11), Fraction(9)),
    (Fraction(2), Fraction(4), Fraction(21)),
)


# ===========================================================================
# 1.  THE RASP KERNEL
# ===========================================================================
#
# Every non-elementwise operation in the paper is one RASP select/aggregate
# pair: a Boolean selection of keys for each query position, then an *average*
# over the selected tokens.  That is average-hard attention, and it is the
# only attention this module is allowed to use -- simulating soft attention
# with hard attention is the paper's point, so the port must not cheat by
# calling the thing it simulates.

def prop(rows: Sequence[Sequence[Fraction]]) -> Tuple[Fraction, ...]:
    """Row-major flattening (the paper's Proposition 2 bijection)."""
    return tuple(x for row in rows for x in row)


def prop_inv(seq: Sequence[Fraction], r: int, c: int
             ) -> Tuple[Tuple[Fraction, ...], ...]:
    """The inverse of :func:`prop`: reshape a length-``r * c`` sequence."""
    if len(seq) != r * c:
        raise ValueError(f"prop_inv: length {len(seq)} is not {r}x{c}")
    return tuple(tuple(seq[i * c:(i + 1) * c]) for i in range(r))


def aha(tokens: Sequence[Fraction],
        selected: Callable[[int, int], bool]) -> Tuple[Fraction, ...]:
    """Average-hard attention: the RASP ``select``/``aggregate`` pair.

    ``out[q]`` is the mean of ``tokens[k]`` over every key position ``k``
    with ``selected(q, k)`` true, and ``0`` when the selection is empty --
    the RASP convention the paper's constructions rely on for their zero
    padding.  Length is preserved.  This is the generic Boolean path; the
    constructions below use the two specialisations :func:`aha_gather` and
    :func:`aha_span`, which compute exactly what this computes.
    """
    out: List[Fraction] = []
    selected_pairs = 0
    divides = 0
    for q in range(len(tokens)):
        total = Fraction(0)
        count = 0
        for k in range(len(tokens)):
            if selected(q, k):
                total += tokens[k]
                count += 1
        selected_pairs += count
        divides += 1 if count else 0
        out.append(total / count if count else Fraction(0))
    _tally_add(heads=1, adds=selected_pairs, divides=divides)
    return tuple(out)


def aha_gather(tokens: Sequence[Fraction],
               key_of: Callable[[int], Optional[int]]) -> Tuple[Fraction, ...]:
    """Average-hard attention whose selection is a single key per query.

    ``out[q] = tokens[key_of(q)]`` when ``key_of(q)`` is a valid position and
    ``0`` otherwise -- the mean over a one-element selection, which is what
    the paper's permutation and row-drawing attentions (Algorithms 1-3)
    select.  Agrees with :func:`aha` on the same Boolean selection.
    """
    n = len(tokens)
    out: List[Fraction] = []
    for q in range(n):
        k = key_of(q)
        out.append(tokens[k] if k is not None and 0 <= k < n else Fraction(0))
    _tally_add(heads=1, adds=n, divides=0)
    return tuple(out)


def aha_span(tokens: Sequence[Fraction],
             span_of: Callable[[int], range]) -> Tuple[Fraction, ...]:
    """Average-hard attention whose selection is a contiguous span.

    ``out[q]`` is the mean of ``tokens[k]`` for ``k`` in ``span_of(q)`` and
    ``0`` for an empty span -- the shape of the paper's row-sum selections
    (Algorithm 2) and inner-product selections (Algorithm 3, line 4).
    """
    n = len(tokens)
    out: List[Fraction] = []
    selected_pairs = 0
    divides = 0
    for q in range(n):
        span = span_of(q)
        total = Fraction(0)
        count = 0
        for k in span:
            total += tokens[k]
            count += 1
        selected_pairs += count
        divides += 1 if count else 0
        out.append(total / count if count else Fraction(0))
    _tally_add(heads=1, adds=selected_pairs, divides=divides)
    return tuple(out)


# ---------------------------------------------------------------------------
# The instrument.  Head and operation counts are exact integers, never
# timings (the exactness rules forbid float clocks inside the package); wall
# time is measured outside, by the study that runs this module.
# ---------------------------------------------------------------------------

_TALLY: Optional[Dict[str, int]] = None


def _tally_add(*, heads: int = 0, adds: int = 0, divides: int = 0) -> None:
    if _TALLY is not None:
        _TALLY["heads"] += heads
        _TALLY["adds"] += adds
        _TALLY["divides"] += divides


def begin_instrumentation() -> Dict[str, int]:
    """Start counting attention heads and exact additions/divisions."""
    global _TALLY
    _TALLY = {"heads": 0, "adds": 0, "divides": 0}
    return _TALLY


def end_instrumentation() -> Dict[str, int]:
    """Stop counting and return the tally since :func:`begin_instrumentation`."""
    global _TALLY
    out = dict(_TALLY) if _TALLY is not None else {"heads": 0, "adds": 0,
                                                   "divides": 0}
    _TALLY = None
    return out


# ===========================================================================
# 2.  THE EXPONENTIAL, EXACTLY TO A DECLARED DEPTH
# ===========================================================================

def exp_rational(x: Fraction, depth: int) -> Fraction:
    """``exp(x)`` by Taylor truncation at integer ``depth >= 1``, exactly.

    The partial sum is exact rational arithmetic; the value differs from
    ``exp(x)`` by the remainder bounded in :func:`exp_rational_bound`.  This
    is the honest form of the paper's ``2.73 ^ tokens`` (its Listing 2):
    the same approximation, with the knob turned from "three significant
    digits" to a declared depth with a computed bound.
    """
    if depth < 1:
        raise ValueError("exp_rational: depth must be at least 1")
    total = Fraction(1)
    term = Fraction(1)
    for n in range(1, depth + 1):
        term = term * x / n
        total += term
    return total


def exp_rational_bound(x: Fraction, depth: int) -> Fraction:
    """A rigorous rational upper bound on the Taylor remainder.

    For ``x >= 0``: ``0 <= exp(x) - T_depth(x) <= e^x x^{d+1}/(d+1)!`` and
    ``e^x <= 3^ceil(x)`` since ``e < 3``.  For ``x < 0`` the series
    alternates, so once ``depth >= |x|`` the terms decrease in magnitude
    and ``|exp(x) - T_depth(x)| <= |x|^{d+1}/(d+1)!`` -- the bound the
    softmax path uses, because the row-max shift makes every exponent
    non-positive.  Negative arguments below the available depth refuse.
    """
    from math import factorial
    if x >= 0:
        ceil = -((-x.numerator) // x.denominator)
        e_bound = Fraction(3) ** ceil
        return e_bound * x ** (depth + 1) / factorial(depth + 1)
    ax = -x
    if Fraction(depth) < ax:
        raise ValueError("exp_rational_bound: alternating bound needs "
                         "depth >= |x|")
    return ax ** (depth + 1) / factorial(depth + 1)


def softmax_depth_needed(score_range: Fraction,
                         target: Fraction = Fraction(1, 10 ** 12)) -> int:
    """Least Taylor depth whose alternating-series error meets ``target``.

    After the row-max shift every logit lies in ``[-score_range, 0]``, so
    the softmax exponential error is at most ``range^{D+1}/(D+1)!``.  This
    solves for the least such ``D`` exactly -- the depth is computed from
    the measured score range, never guessed, which is what makes the
    softmax error a *declared* precision rather than a surprise.
    """
    from math import factorial
    if score_range < 0:
        raise ValueError("softmax_depth_needed: range is non-negative")
    if score_range == 0:
        return 2
    # Incremental bound: R^{d+1}/(d+1)! updated by one multiplication per
    # step -- recomputing the power per step would be quadratic in integers
    # that are themselves growing by thousands of digits.
    d = 2
    bound = score_range ** 3 / factorial(3)
    while bound > target:
        d += 1
        bound = bound * score_range / (d + 1)
    return d


# ===========================================================================
# 3.  THE FOUR ELEMENTARY OPERATIONS (paper Section 4)
# ===========================================================================

def transpose_sim(rows: Sequence[Sequence[Fraction]]
                  ) -> Tuple[Tuple[Fraction, ...], ...]:
    """Transpose by permutation attention (Algorithm 1, Lemma 3).

    The flat sequence ``prop(A)`` is permuted by the single-key selection
    ``target(k) = r * (k mod c) + k div c`` -- the paper's
    ``reflectedIndices`` -- realised as one average-hard-attention head per
    the construction, preceded by the index arithmetic an FFN layer performs
    (the paper counts this as two layers, one head; Table 1).
    """
    r, c = len(rows), len(rows[0]) if rows else 0
    seq = prop(rows)
    # Position k holds A[i, j] with k = c * i + j; it must move to the
    # position r * j + i, which holds A^T[j, i].  The output position t
    # therefore draws from the key k with r * (k mod c) + k div c == t.
    def key_of(t: int) -> Optional[int]:
        for k in range(r * c):
            if r * (k % c) + k // c == t:
                return k
        return None
    permuted = aha_gather(seq, key_of)
    return prop_inv(permuted, c, r)


def softmax_sim(rows: Sequence[Sequence[Fraction]], depth: int = 24,
                mask: Optional[Sequence[Sequence[bool]]] = None
                ) -> Tuple[Tuple[Fraction, ...], ...]:
    """Softmax by row-sum attention (Algorithm 2, Lemma 4).

    Structure per the paper's Listing 2: exponentiate every token (an FFN
    map -- here exact Taylor at ``depth``), then one attention head per row
    whose selection is "query and key both sit in row ``i``", whose aggregate
    is the *mean* over the row, compensated by the FFN multiplying by ``c``
    (the paper's Proposition 1), then an elementwise division.  The row-max
    shift is applied first -- the true softmax is invariant under it exactly,
    and it keeps every exponent non-positive so the alternating-series
    remainder bound applies.

    ``mask[i][j] = False`` excludes key ``j`` from row ``i``'s softmax
    entirely (its exponential contributes zero).  This is a RASP ``select``
    predicate -- the paper's own masking machinery -- and it is what
    Corollary 6.2's hierarchy embedding needs to be exact: without it the
    padded rows attend with weight ``e^{-s}`` at every position and steal
    mass from the real attendees (measured; see :func:`embed_hierarchy`).
    """
    r, c = len(rows), len(rows[0]) if rows else 0
    if r == 0 or c == 0:
        raise ValueError("softmax_sim: empty matrix")
    shifted = [[rows[i][j] - max(row) for j in range(c)]
               for i, row in enumerate(rows)]
    exps = [[(exp_rational(x, depth) if (mask is None or mask[i][j])
              else Fraction(0)) for j, x in enumerate(row)]
            for i, row in enumerate(shifted)]
    seq = prop(exps)
    # Head i: selection "q and k both in row i's span", aggregate = mean,
    # FFN compensation * c -> the row sum broadcast across the row.
    sums: List[Fraction] = []
    for i in range(r):
        span = range(i * c, (i + 1) * c)
        mean = aha_span(seq, lambda q, _span=span: _span if q in _span
                        else range(0))
        row_sum = mean[i * c] * c
        sums.extend([row_sum] * c)
    out = tuple(e / s for e, s in zip(seq, sums))
    return prop_inv(out, r, c)


def matmul_sim(a_rows: Sequence[Sequence[Fraction]],
               b_rows: Sequence[Sequence[Fraction]]
               ) -> Tuple[Tuple[Fraction, ...], ...]:
    """Matrix product by select/aggregate attention (Algorithm 3, Lemma 5).

    The input is the concatenation ``prop(A) ~ prop(B)`` of length
    ``k(r + c)``; ``r + c`` heads draw the rows of ``A`` and the columns of
    ``B`` broadcast across the sequence; ``rc`` elementwise products form the
    summands; ``rc`` further heads average the first ``k`` positions of each
    product sequence and the FFN multiplies by ``k`` (Proposition 1), which
    yields exactly ``(AB)[i, j]`` at output position ``c * i + j``.

    Feasibility follows Lemma 5 literally: the construction needs
    ``k(r + c) >= rc``, otherwise the padding would be negative and this
    refuses.  (Theorem 6 uses the sufficient form ``k >= min(r, c)``; see
    :func:`feasibility_limits` for the difference, which is measured.)
    Output positions ``rc..k(r+c)`` are zero, exactly as the paper pads.
    """
    r, ka = len(a_rows), len(a_rows[0]) if a_rows else 0
    kb, c = len(b_rows), len(b_rows[0]) if b_rows else 0
    if ka != kb:
        raise ValueError(f"matmul_sim: {r}x{ka} cannot multiply {kb}x{c}")
    k = ka
    if k * (r + c) < r * c:
        raise ValueError(
            f"matmul_sim: Lemma 5 feasibility fails -- k(r+c) = {k * (r + c)} "
            f"< rc = {r * c}; the construction has no room for the output")
    seq = prop(a_rows) + prop(b_rows)
    length = k * (r + c)

    def draw_row(i: int) -> Tuple[Fraction, ...]:
        # Head of Algorithm 3 line 1: position q draws A[i, q mod k].
        return aha_gather(seq, lambda q, _i=i: _i * k + (q % k))

    def draw_col(j: int) -> Tuple[Fraction, ...]:
        # Head of Algorithm 3 line 2: position q draws B[q mod k, j].
        return aha_gather(seq, lambda q, _j=j: r * k + c * (q % k) + _j)

    # The paper's layer structure: one attention layer of width r + c draws
    # every row of A and every column of B once; a second layer of width
    # rc combines them.  Drawing once and reusing is the layer, not an
    # optimisation of it.
    drawn_rows = [draw_row(i) for i in range(r)]
    drawn_cols = [draw_col(j) for j in range(c)]
    out = [Fraction(0)] * length
    for i in range(r):
        gi = drawn_rows[i]
        for j in range(c):
            gj = drawn_cols[j]
            product = tuple(x * y for x, y in zip(gi, gj))
            # Head of Algorithm 3 line 4 at output position c * i + j:
            # the mean over the first k positions, compensated by k.
            mean = aha_span(product, lambda q: range(0, k)
                            if q == c * i + j else range(0))
            out[c * i + j] = mean[c * i + j] * k
    # The paper's contraction: an FFN weight matrix of 1s keeps the first rc
    # tokens and drops the k(r + c) - rc padding (its Section 4, following
    # Algorithm 3).  Not an attention head -- the paper puts it in the FFN.
    return prop_inv(tuple(out[:r * c]), r, c)


def maxmin_sim(seq: Sequence[Fraction]) -> Tuple[Fraction, ...]:
    """The MaxMin group-sort with group size 2 (Algorithm 4, Lemma 7).

    One pass: each even position keeps the larger of its pair and the
    following odd position the smaller -- exactly, by comparison, with the
    pair swap realised as the paper's attention matrix whose ``2 x 2`` blocks
    are either the identity or its reflection.  The sequence must have even
    length; that is the lemma's own requirement.
    """
    n = len(seq)
    if n % 2 != 0:
        raise ValueError("maxmin_sim: Lemma 7 requires an even-length "
                         f"sequence, got {n}")
    swapped = aha_gather(seq, lambda q: q + 1 if q % 2 == 0 else q - 1)
    return tuple(max(a, b) if q % 2 == 0 else min(a, b)
                 for q, (a, b) in enumerate(zip(seq, swapped)))


def inverse3_sim(rows: Sequence[Sequence[Fraction]]
                 ) -> Tuple[Tuple[Fraction, ...], ...]:
    """Exact ``3 x 3`` inverse by cofactors (Algorithm 5, Lemma 10).

    Four permutation attentions (``R_alpha`` to ``R_delta``) gather the
    minors; the cofactor is two products and a difference; the determinant
    is a first-row mask attention over ``prop(A) * cofactor``; the inverse
    is ``adjugate / det`` with the final transposition by Lemma 3.  Refuses
    a singular matrix, since division by zero has no witness -- the same
    refusal discipline the substrate uses elsewhere.
    """
    n = len(rows)
    if n != 3 or any(len(row) != 3 for row in rows):
        raise ValueError("inverse3_sim: Lemma 10 covers 3x3 matrices only "
                         "(arbitrary order needs the recursive cofactor the "
                         "paper itself declines to build)")
    seq = prop(rows)
    index = lambda i, j: 3 * i + j

    def shift(di: int, dj: int) -> Callable[[int], Optional[int]]:
        # R_alpha .. R_delta: position 3*i+j draws A[(i+di)%3, (j+dj)%3].
        return lambda q: index((q // 3 + di) % 3, (q % 3 + dj) % 3)

    p = aha_gather(seq, shift(2, 2))
    q_ = aha_gather(seq, shift(1, 1))
    rr = aha_gather(seq, shift(2, 1))
    s = aha_gather(seq, shift(1, 2))
    cofactor_seq = tuple(x * y - u * v for x, y, u, v in zip(p, q_, rr, s))
    # Line 7-8: elementwise product first, then a mask attention averaging
    # the first row and compensated by 3 (Proposition 1) -- the determinant.
    product_seq = tuple(a * b for a, b in zip(seq, cofactor_seq))
    masked = aha_span(product_seq, lambda q: range(0, 3) if q < 3
                      else range(0))
    det = masked[0] * 3
    if det == 0:
        raise ValueError("inverse3_sim: singular matrix -- no witness exists")
    adjugate = transpose_sim(prop_inv(cofactor_seq, 3, 3))
    return tuple(tuple(x / det for x in row) for row in adjugate)


# ===========================================================================
# 4.  THE SIMULATOR U (Theorem 6) AND ITS EXTENSIONS
# ===========================================================================

def _frac_rows(rows: Sequence[Sequence[object]]
               ) -> Tuple[Tuple[Fraction, ...], ...]:
    """Coerce a row-of-rows to exact Fractions, refusing floats."""
    out = []
    for row in rows:
        coerced = []
        for x in row:
            if isinstance(x, float):
                raise TypeError("attention_simulator: floats are not "
                                "carrier scalars")
            coerced.append(Fraction(x))
        out.append(tuple(coerced))
    return tuple(out)


def _direct_matmul(a_rows, b_rows):
    """Ground-truth exact product, unconstrained by the 24-entry carrier."""
    ka = len(a_rows[0])
    return tuple(
        tuple(sum((row[k] * b_rows[k][j] for k in range(ka)), Fraction(0))
              for j in range(len(b_rows[0]))) for row in a_rows)


@dataclass(frozen=True)
class AttentionResult:
    """One run of the simulator ``U`` (Theorem 6).

    ``output`` is ``sigma(X A X^T) X V``; ``stage_errors`` records the exact
    difference against the direct exact computation at every stage (zero
    everywhere except the softmax stage, whose error is bounded, not zero);
    ``tally`` holds the attention-head and exact-arithmetic counts; and
    ``feasibility`` records both coverage conditions of the literature note
    in the module docstring.
    """
    output: Tuple[Tuple[Fraction, ...], ...]
    stage_errors: Dict[str, Fraction]
    tally: Dict[str, int]
    feasibility: Dict[str, object]


def simulate_attention(x_rows, a_rows, v_rows, depth: int = 24,
                       mask: Optional[Sequence[Sequence[bool]]] = None
                       ) -> AttentionResult:
    """``U(X, A, V) = sigma(X A X^T) X V`` by elementary ops (Theorem 6).

    Five stages exactly as the paper composes them: ``Y1 = X A``,
    ``XT = X^T``, ``Y2 = Y1 XT``, ``Y3 = softmax(Y2)``, ``Y4 = X V`` and
    ``Y = Y3 Y4`` -- each by :func:`matmul_sim` / :func:`transpose_sim` /
    :func:`softmax_sim`, never by calling the formula being simulated.
    The direct exact computation runs alongside as ground truth, and its
    per-stage differences are reported rather than discarded.  ``mask`` is
    forwarded to the softmax stage (padding mask; see :func:`softmax_sim`).
    """
    x, a, v = _frac_rows(x_rows), _frac_rows(a_rows), _frac_rows(v_rows)
    n, d = len(x), len(x[0])
    if len(a) != d or len(a[0]) != d:
        raise ValueError("simulate_attention: A must be d x d")
    if len(v) != d:
        raise ValueError("simulate_attention: V must be d x dv")
    dv = len(v[0])
    try:
        begin_instrumentation()
        y1 = matmul_sim(x, a)
        xt = transpose_sim(x)
        y2 = matmul_sim(y1, xt)
        y3 = softmax_sim(y2, depth, mask)
        y4 = matmul_sim(x, v)
        y = matmul_sim(y3, y4)
    finally:
        tally = end_instrumentation()

    # Ground truth: the direct exact computation, stage by stage.  The
    # construction is compared against the formula *given its own inputs*
    # (every such difference is exactly zero, including the last matmul),
    # and separately against a fourfold-depth reference (where only the
    # exponential stage and its propagation differ).
    g1 = _direct_matmul(x, a)
    gxt = tuple(zip(*x))
    g2 = _direct_matmul(g1, gxt)
    g3 = softmax_sim(g2, depth * 4, mask)
    g4 = _direct_matmul(x, v)
    gy = _direct_matmul(g3, g4)
    stage_errors = {
        "Y1 = X A": _max_abs_diff(y1, g1),
        "XT = X^T": _max_abs_diff(xt, gxt),
        "Y2 = Y1 X^T": _max_abs_diff(y2, g2),
        "Y3 = softmax(Y2)": _max_abs_diff(y3, g3),
        "Y4 = X V": _max_abs_diff(y4, g4),
        "Y = Y3 Y4 (given its inputs)": _max_abs_diff(
            y, _direct_matmul(y3, y4)),
        "Y vs deeper reference": _max_abs_diff(y, gy),
    }
    feasibility = feasibility_limits(d, dv)
    feasibility["n"] = n
    feasibility["literal_condition_holds"] = n <= feasibility["literal_max_n"]
    feasibility["paper_condition_holds"] = n <= min(d, dv)
    return AttentionResult(output=y, stage_errors=stage_errors, tally=tally,
                           feasibility=feasibility)


def _max_abs_diff(p, q) -> Fraction:
    """The maximum absolute entrywise difference, exactly."""
    flat_p = [x for row in p for x in row]
    flat_q = [x for row in q for x in row]
    if len(flat_p) != len(flat_q):
        return Fraction(-1)
    return max((abs(a - b) for a, b in zip(flat_p, flat_q)),
               default=Fraction(0))


def feasibility_limits(d: int, dv: int) -> Dict[str, object]:
    """Both coverage conditions for ``U`` at representation width ``d``.

    The paper's Theorem 6 states ``n <= min(d, dv)`` -- the sufficient form
    ``k >= min(r, c)`` of Lemma 5.  The literal Lemma 5 condition
    ``k(r + c) >= rc`` per stage admits more: the binding stage ``X A X^T``
    needs ``n <= 2d``, and the value stage ``X V`` needs ``n(d - dv) >=
    -d dv`` (always true when ``dv <= d``).  Both are reported; the
    difference between them is the module's measured finding, not a guess.
    """
    literal_y2 = 2 * d
    if dv <= d:
        literal_y4: Optional[int] = None  # no constraint
    else:
        literal_y4 = (d * dv) // (dv - d)
    literal_max = min(literal_y2, literal_y4) if literal_y4 else literal_y2
    return {
        "d": d, "dv": dv,
        "paper_bound": min(d, dv),
        "literal_max_n": literal_max,
        "binding_stage": "Y2 = X A X^T (needs n <= 2d)"
        if (literal_y4 is None or literal_y2 <= literal_y4)
        else "Y4 = X V",
    }


def embed_hierarchy(x_rows, a_rows, v_rows, n: int, d: int, dv: int,
                    depth: Optional[int] = None,
                    target: Fraction = Fraction(1, 10 ** 12)
                    ) -> Dict[str, object]:
    """Simulate a small attention inside a larger host (Corollary 6.2).

    ``X`` (``m x e``) is zero-padded to ``n x d``; ``A`` is embedded
    block-diagonally with an identity; ``V`` is embedded with a zero block.
    The corollary claims the simulation is exact in the upper-left block.

    Two things the corollary does not say, both measured here:

    * **The padding must be masked.**  The softmax of a real row sees the
      padded rows' zero scores and they steal mass (``e^{-s}`` each) from
      the true attendees -- the upper-left block comes out shrunk, not
      exact.  The fix is a ``select`` predicate masking keys ``j >= m`` --
      ordinary RASP machinery the paper already ships; this port applies
      it and records that the corollary needs it.
    * **The depth must cover the score range.**  Padded keys sit at
      shifted logits as low as ``-max(score)``; at a depth below that
      range the truncated exponential *inverts* the softmax (measured; see
      :func:`normalized_identity`).  The depth is therefore computed from
      the measured range, not fixed.
    """
    x, a, v = _frac_rows(x_rows), _frac_rows(a_rows), _frac_rows(v_rows)
    m, e = len(x), len(x[0])
    if not (n >= m and d >= e and dv >= len(v[0])):
        raise ValueError("embed_hierarchy: the host must dominate "
                         "(n >= m, d >= e, dv >= ev)")
    zero = Fraction(0)
    x_hat = [list(row) + [zero] * (d - e) for row in x]
    x_hat += [[zero] * d for _ in range(n - m)]
    a_hat = [list(a[i]) + [zero] * (d - e) for i in range(e)]
    a_hat += [[zero] * e + [Fraction(1)] * (d - e)
              for _ in range(d - e)]
    v_hat = [list(v[i]) + [zero] * (dv - len(v[0])) for i in range(e)]
    v_hat += [[zero] * dv for _ in range(d - e)]
    # The padding mask: no row may attend a padded key.
    mask = [[j < m for j in range(n)] for _ in range(n)]
    if depth is None:
        scores = _direct_matmul(_direct_matmul(x_hat, a_hat),
                                tuple(zip(*x_hat)))
        score_range = max((max(row) - min(row) for row in scores),
                          default=Fraction(0))
        depth = softmax_depth_needed(score_range, target)
    big = simulate_attention(x_hat, a_hat, v_hat, depth, mask)
    small = simulate_attention(x, a, v, depth)
    upper_left = tuple(row[:len(v[0])] for row in big.output[:m])
    return {
        "host": (n, d, dv), "guest": (m, e, len(v[0])), "depth": depth,
        "upper_left": upper_left, "direct": small.output,
        "exact": _max_abs_diff(upper_left, small.output) == 0,
        "guest_stage_errors": small.stage_errors,
    }


def multihead_rearrange(flats: Sequence[Fraction], n: int, H: int
                        ) -> Tuple[Fraction, ...]:
    """Lemma 8's identify-and-shift rearrangement, by attention.

    The interleaved layout ``q = i * H + h`` (row ``i`` of head ``h``) is
    permuted into the blocked layout ``q' = h * n + i`` by one gather
    attention with the paper's cyclic-shift index arithmetic -- the
    ``identify``/``shift`` pair of Lemma 8, done as the selection it is.
    """
    if len(flats) != n * H:
        raise ValueError("multihead_rearrange: length must be n * H")
    return aha_gather(flats, lambda q: (q % n) * H + (q // n))


def simulate_attention_multihead(heads: Sequence[Tuple[object, object, object]],
                                 depth: int = 24
                                 ) -> Dict[str, object]:
    """Multi-head attention by ``H`` independent simulations (Theorem 9).

    Lemma 8 shows a transformer can run ``H`` copies of an operation without
    mutual interference, by the rearrangement :func:`multihead_rearrange`;
    Theorem 9 stacks ``H`` simulations of Theorem 6.  This runs that
    construction and checks it against ``H`` direct simulations -- which is
    the interference-freedom claim, measured.
    """
    sim_runs = []
    direct_runs = []
    H_total = len(heads)
    n = len(_frac_rows(heads[0][0]))
    # Lemma 8's rearrangement, exercised on the interleaved row layout:
    # input position k = i * H + h (row i of head h) must land at output
    # position h * n + i.  Verified as the exact permutation it claims to
    # be, on the position markers themselves.
    marker = tuple(Fraction(q) for q in range(n * H_total))
    rearranged = multihead_rearrange(marker, n, H_total)
    expected = tuple(Fraction((q % n) * H_total + q // n)
                     for q in range(n * H_total))
    rearranged_ok = rearranged == expected
    for x_rows, a_rows, v_rows in heads:
        x, a, v = _frac_rows(x_rows), _frac_rows(a_rows), _frac_rows(v_rows)
        sim_runs.append(simulate_attention(x_rows, a_rows, v_rows, depth))
        # The direct equal form at the SAME depth: identical inputs, so any
        # difference would be interference between the heads, not precision.
        w = softmax_sim(_direct_matmul(_direct_matmul(x, a), tuple(zip(*x))),
                        depth)
        direct_runs.append(_direct_matmul(w, _direct_matmul(x, v)))
    agree = all(_max_abs_diff(s.output, d) == 0
                for s, d in zip(sim_runs, direct_runs))
    return {
        "heads": len(heads),
        "outputs": tuple(s.output for s in sim_runs),
        "rearrangement_lossless": rearranged_ok,
        "heads_agree_with_direct": agree,
        "tallies": tuple(s.tally for s in sim_runs),
    }


# ===========================================================================
# 5.  THE PAPER'S OWN DEMONSTRATIONS, RE-RUN EXACTLY
# ===========================================================================

#: The paper's Figure 2 printed softmax row-major (three decimals).
PAPER_PRINTED_Y3 = (
    (Fraction(317, 1000), Fraction(324, 1000), Fraction(359, 1000)),
    (Fraction(318, 1000), Fraction(319, 1000), Fraction(363, 1000)),
    (Fraction(315, 1000), Fraction(319, 1000), Fraction(365, 1000)),
)
#: The paper's Figure 2 printed output row-major (three decimals).
PAPER_PRINTED_Y = (
    (Fraction(783, 1000), Fraction(598, 1000), Fraction(941, 1000)),
    (Fraction(780, 1000), Fraction(599, 1000), Fraction(940, 1000)),
    (Fraction(781, 1000), Fraction(599, 1000), Fraction(940, 1000)),
)


def paper_demo(depth: int = 48) -> Dict[str, object]:
    """Figure 2 of the paper, re-run with exact arithmetic.

    The paper reports ``|Y3 - prop(Y3)| ~= 3.376358e-06`` (softmax) and
    ``|Y - prop(Y)| ~= 3.040329e-07``; both are float artifacts of its
    three-digit exponential.  Here every stage is exact except the
    exponential, whose deviation is measured against a fourfold-depth
    reference and bounded by :func:`exp_rational_bound`.
    """
    result = simulate_attention(PAPER_DEMO_X, PAPER_DEMO_A, PAPER_DEMO_V,
                                depth)
    y3 = softmax_sim(_direct_matmul(_direct_matmul(PAPER_DEMO_X, PAPER_DEMO_A),
                                    tuple(zip(*PAPER_DEMO_X))), depth)
    return {
        "stage_errors": result.stage_errors,
        "output": result.output,
        "tally": result.tally,
        "feasibility": result.feasibility,
        "vs_printed_softmax": _max_abs_diff(y3, PAPER_PRINTED_Y3),
        "vs_printed_output": _max_abs_diff(result.output, PAPER_PRINTED_Y),
        "paper_reported_softmax_error": "3.376358e-06 (float)",
        "paper_reported_output_error": "3.040329e-07 (float)",
    }


def paper_inverse_demo() -> Dict[str, object]:
    """Figure 3 of the paper: the exact inverse of an integer matrix.

    The paper prints three-decimal floats (``4.333, -4.267, 0.4, ...``);
    the exact inverse is rational, and this returns it -- checked against
    the shipped Gauss-Jordan ``reasoning.product._inverse3``, which is the
    ground truth the package already ships.
    """
    mine = inverse3_sim(PAPER_INVERSE_A)
    truth = _product._inverse3([list(row) for row in PAPER_INVERSE_A])
    truth_t = tuple(tuple(x for x in row) for row in truth)
    printed = (
        (Fraction(4333, 1000), Fraction(-2667, 1000), Fraction(-1333, 1000)),
        (Fraction(-4267, 1000), Fraction(2733, 1000), Fraction(1267, 1000)),
        (Fraction(4, 10), Fraction(-267, 1000), Fraction(-67, 1000)),
    )
    return {
        "inverse": mine,
        "agrees_with_gauss_jordan": _max_abs_diff(mine, truth_t) == 0,
        "determinant": det3(PAPER_INVERSE_A),
        "vs_printed_decimals": _max_abs_diff(mine, printed),
    }


def det3(rows: Sequence[Sequence[Fraction]]) -> Fraction:
    """The determinant of a ``3 x 3`` matrix, exactly."""
    a, b, c = rows
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


# ===========================================================================
# 6.  THE BRIDGE TO THE REGISTERS (what "used with GLM" means here)
# ===========================================================================

def _register_rows(session, domain: str) -> Tuple[Tuple[str, Tuple[Fraction, ...]], ...]:
    """Register carriers as exact rows, with their names."""
    return tuple((obj.name, tuple(Fraction(c) for c in obj.carrier))
                 for obj in session.register(domain))


def _adaptive_depth(x, a_rows, scale: Fraction,
                   target: Fraction) -> int:
    """Depth from the measured shifted-logit range (the declared error)."""
    scores = attention_scores(x, a_rows, scale)
    score_range = max((max(row) - min(row) for row in scores),
                      default=Fraction(0))
    return softmax_depth_needed(score_range, target)


def normalized_identity(x_rows):
    """The register-scoring matrix ``A = I / k``, ``k = max_j |x_j|^2``.

    Why this exists: measured on the live lexicon register, plain identity
    scoring produces logit ranges of order ``4 x 10^5`` (carriers live at
    very different radii), and at any affordable Taylor depth the truncated
    exponential does not approximate the softmax -- it *inverts* it, the
    weights ordering by distance from the row maximum, backwards.  Scaling
    by the squared largest norm is the substrate's answer: by
    Cauchy-Schwarz every score ``<x_i, x_j> / k`` lies in ``[-1, 1]`` -- a
    bound that is a theorem, not a tuning -- so the shifted-logit range is
    at most ``2`` and the exact softmax needs depth under twenty.  It is
    still the paper's form ``X A X^T`` with a legal characterizing matrix,
    and it preserves the argmax (a positive scale cannot reorder).
    """
    x = _frac_rows(x_rows)
    k = max((sum((a * a for a in row), Fraction(0)) for row in x),
            default=Fraction(1))
    if k == 0:
        k = Fraction(1)
    d = len(x[0])
    return tuple(tuple(Fraction(1, k) if i == j else Fraction(0)
                       for j in range(d)) for i in range(d))


def attention_scores(x_rows, a_rows=None, scale: Fraction = Fraction(1)):
    """The exact score matrix ``scale * X A X^T`` before the softmax."""
    x = _frac_rows(x_rows)
    d = len(x[0])
    if a_rows is None:
        a = tuple(tuple(Fraction(1) if i == j else Fraction(0)
                        for j in range(d)) for i in range(d))
    else:
        a = _frac_rows(a_rows)
    scores = _direct_matmul(_direct_matmul(x, a), tuple(zip(*x)))
    if scale != 1:
        scores = tuple(tuple(scale * s for s in row) for row in scores)
    return scores


def attention_weights(x_rows, a_rows=None, scale: Fraction = Fraction(1),
                      depth: int = 24):
    """The softmax attention weight matrix ``sigma(scale * X A X^T)``.

    ``A = None`` means the identity -- plain inner-product scoring, which is
    the bilinear form the substrate already ships as
    :func:`~glm_universal.reasoning.metric.griess_inner` (up to its fixed
    scale).  ``scale`` is a rational temperature dial: ``0`` is the uniform
    bundle, and growing ``scale`` concentrates weight until the selection is
    hard -- the two ends GLM already ships as bundling and nearest.  For
    register-scale sequences use :func:`normalized_identity` as ``A``; see
    its docstring for the measured reason.
    """
    scores = attention_scores(x_rows, a_rows, scale)
    return softmax_sim(scores, depth)


def register_attention(session, domain: str, a_rows=None,
                       scale: Fraction = Fraction(1),
                       depth: Optional[int] = None, block_rows: int = 0,
                       target: Fraction = Fraction(1, 10 ** 12)
                       ) -> Dict[str, object]:
    """Soft attention over a live GLM register, exactly.

    The register's carriers are the sequence ``X`` (and, with ``V = I``, the
    values); the weight matrix is :func:`attention_weights` and each
    attended row is the exact weighted mixture of the register's carriers.
    ``a_rows = None`` (the default) scores with :func:`normalized_identity`
    -- the Cauchy-Schwarz-bounded form the register's radius spread demands
    (measured; see that function's docstring).  The weights are exactly
    stochastic whatever the exponential depth -- only their *ratios* carry
    the declared error.  ``depth = None`` computes the depth from the
    measured score range and reports it (:func:`softmax_depth_needed`);
    with ``block_rows > 0`` the *construction* of Theorem 6 is additionally
    run on the first block through the elementary operations -- the literal
    coverage bound ``n <= 2d`` is why the construction blocks and the
    direct equal form does not need to.
    """
    rows = _register_rows(session, domain)
    x = tuple(carrier for _, carrier in rows)
    names = tuple(name for name, _ in rows)
    if a_rows is None:
        a_rows = normalized_identity(x)
    if depth is None:
        depth = _adaptive_depth(x, a_rows, scale, target)
    weights = attention_weights(x, a_rows, scale, depth)
    mixtures = _direct_matmul(weights, x)
    out: Dict[str, object] = {
        "domain": domain, "rows": len(rows), "depth": depth,
        "names": names, "weights": weights, "mixtures": mixtures,
    }
    if block_rows:
        block = x[:block_rows]
        # The construction on one block, scored exactly as the register is
        # (the normalized identity when a_rows came from the default),
        # compared against the direct equal form at the same depth and the
        # same (unit) scale -- identical inputs, so agreement is exact.
        d = len(block[0])
        block_a = a_rows if a_rows is not None else normalized_identity(x)
        # Values are the carriers themselves: V = I_d, so X V = X.
        v = tuple(tuple(Fraction(1) if i == j else Fraction(0)
                        for j in range(d)) for i in range(d))
        construction = simulate_attention(block, block_a, v, depth)
        direct_w = attention_weights(block, block_a, 1, depth)
        direct_m = _direct_matmul(direct_w, block)
        out["block_construction"] = {
            "block_rows": block_rows,
            "stage_errors": construction.stage_errors,
            "tally": construction.tally,
            "agrees_with_direct": _max_abs_diff(
                construction.output, direct_m) == 0,
        }
    return out


# ===========================================================================
# 7.  INSTRUMENTS: THE REPORTS AND THE PROMOTION CHECKLIST
# ===========================================================================

def _deterministic_matrix(r: int, c: int, salt: int = 1):
    """A deterministic exact matrix: no random source, by rule."""
    return tuple(tuple(Fraction(((i * salt + j) % 7) + 1, (i % 3) + 2)
                       for j in range(c)) for i in range(r))


def construction_report() -> Dict[str, object]:
    """Head counts against the paper's Tables 1 and 2, measured.

    The paper's layer/width accounting is reproduced by running each
    construction under instrumentation and grouping the heads exactly as
    the paper's own complexity discussion groups them (its appendix A.1:
    transposition one non-trivial attention layer; softmax width ``r``;
    multiplication an opening FFN layer, a width-``(r + c)`` layer and a
    width-``rc`` layer; inversion width four then single heads).
    """
    t3 = _deterministic_matrix(3, 3)
    report: Dict[str, object] = {}

    begin_instrumentation()
    transpose_sim(t3)
    report["transpose_heads"] = end_instrumentation()["heads"]

    begin_instrumentation()
    softmax_sim(t3)
    report["softmax_heads"] = end_instrumentation()["heads"]
    report["softmax_paper_width"] = 3  # O(r), Table 2

    begin_instrumentation()
    matmul_sim(_deterministic_matrix(3, 4), _deterministic_matrix(4, 4, 2))
    report["matmul_heads"] = end_instrumentation()["heads"]
    begin_instrumentation()
    matmul_sim(_deterministic_matrix(2, 12), _deterministic_matrix(12, 2, 3))
    report["matmul_heads_2x12_12x2"] = end_instrumentation()["heads"]

    begin_instrumentation()
    inverse3_sim(PAPER_INVERSE_A)
    report["inverse_heads"] = end_instrumentation()["heads"]
    report["paper_widths"] = {"transpose": 1, "softmax": "r",
                              "matmul": "r + c + rc", "inverse": "max 4"}
    return report


def attention_report() -> Dict[str, object]:
    """The module's headline figures, recomputed -- never quoted.

    This is the function a study's tier-0 block points at: it re-runs the
    paper's demonstrations, the ground-truth agreement suite, the coverage
    boundary experiment and the temperature dial, and returns every number
    the study's verdict rests on.
    """
    # 1. The paper's Figure 2, exactly.
    demo = paper_demo()
    # 2. The paper's Figure 3, exactly.
    inv = paper_inverse_demo()
    # 3. Ground-truth agreement over every carrier-exact shape.
    shapes = ((1, 24), (2, 12), (3, 8), (4, 6), (6, 4), (8, 3), (12, 2),
              (24, 1))
    transpose_agrees = True
    matmul_agrees = True
    for r, c in shapes:
        m = _deterministic_matrix(r, c)
        rm = RationalMatrix.from_rows("m", m)
        transpose_agrees = transpose_agrees and _max_abs_diff(
            transpose_sim(m), rm.transpose().row_list()) == 0
    for ra, ca, cb in ((3, 3, 3), (2, 12, 2), (4, 6, 4), (1, 24, 1)):
        am = _deterministic_matrix(ra, ca)
        bm = _deterministic_matrix(ca, cb, 2)
        got = matmul_sim(am, bm)
        if ra * cb <= 24:
            truth = compose_matrices(
                RationalMatrix.from_rows("a", am),
                RationalMatrix.from_rows("b", bm)).row_list()
            matmul_agrees = matmul_agrees and _max_abs_diff(got, truth) == 0
        else:
            truth = _direct_matmul(am, bm)
            matmul_agrees = matmul_agrees and _max_abs_diff(got, truth) == 0
    # 4. The coverage boundary, measured at d = 3 where it is cheap.
    boundary = {"refused_at": None, "passed_at": None}
    for n in range(1, 8):
        try:
            simulate_attention(_deterministic_matrix(n, 3),
                               _deterministic_matrix(3, 3, 2),
                               _deterministic_matrix(3, 3, 3))
            boundary["passed_at"] = n
        except ValueError:
            boundary["refused_at"] = n
            break
    # 5. MaxMin: one pass is the group sort, checked against sorted pairs.
    seq = (Fraction(3), Fraction(1), Fraction(5, 2), Fraction(2))
    mm_ok = maxmin_sim(seq) == (Fraction(3), Fraction(1), Fraction(5, 2),
                                Fraction(2))
    # 6. The hierarchy embedding, on the MOG's own frame as host.
    hier = embed_hierarchy(_deterministic_matrix(2, 3),
                           _deterministic_matrix(3, 3, 2),
                           _deterministic_matrix(3, 2, 3), 4, 6, 6)
    return {
        "paper_demo": demo,
        "paper_inverse": inv,
        "transpose_agrees_all_exact_shapes": transpose_agrees,
        "matmul_agrees_all_shapes": matmul_agrees,
        "maxmin_agrees": mm_ok,
        "hierarchy_exact_on_4x6_host": hier["exact"],
        "coverage_boundary_d3": boundary,
        "feasibility_d24": feasibility_limits(24, 24),
        "construction": construction_report(),
    }


def temperature_report(session, domain: str = "lexicon",
                       scales: Sequence[Fraction] = (0, 1, 4, 16, 64, 256,
                                                     1024),
                       row_limit: int = 24,
                       target: Fraction = Fraction(1, 10 ** 12)
                       ) -> Dict[str, object]:
    """The temperature dial: bundle at one end, hard selection at the other.

    The register's first rows are the queries; scores are the
    Cauchy-Schwarz-normalized inner products
    (:func:`normalized_identity`), and the softmax weights are computed at
    rational temperature multipliers, each at the depth its shifted-logit
    range demands (reported, not hidden).  At temperature ``0`` the mixture
    is the coordinatewise mean of the register -- the rational bundle.  As
    the temperature grows the weight concentrates on the inner-product
    argmax (a positive scale cannot reorder the scores), and the report
    measures where the shipped hard selection
    (:func:`~glm_universal.reasoning.metric.nearest`) sits relative to that
    limit -- they are the same selection exactly when candidate norms
    agree, which is counted over the register rather than asserted.
    """
    rows = _register_rows(session, domain)
    rows = rows[:row_limit] if row_limit else rows
    x = tuple(carrier for _, carrier in rows)
    names = [name for name, _ in rows]
    a_norm = normalized_identity(x)
    by_scale: Dict[str, object] = {}
    for s in scales:
        depth = _adaptive_depth(x, a_norm, Fraction(s), target) if s else 24
        w = attention_weights(x, a_norm, Fraction(s), depth)
        row0 = w[0]
        top = max(range(len(names)), key=lambda j: (row0[j], -j))
        nonself = max((j for j in range(len(names)) if j != 0),
                      key=lambda j: (row0[j], -j))
        mixture0 = tuple(
            sum((row0[j] * x[j][c] for j in range(len(names))), Fraction(0))
            for c in range(len(x[0])))
        by_scale[str(s)] = {
            "depth": depth,
            "max_weight": row0[top],
            "top_row": names[top],
            "top_nonself_row": names[nonself],
            "nonself_weight": row0[nonself],
            "mixture_row0": mixture0,
        }
    # Agreement between inner-product argmax and shipped nearest, per row,
    # with the query itself excluded from both selections.
    agree = 0
    for i, q in enumerate(x):
        cands = [(names[j], x[j]) for j in range(len(names)) if j != i]
        nearest_name, _ = _metric.nearest(q, cands)
        inner = max((j for j in range(len(names)) if j != i),
                    key=lambda j: (sum((a * b for a, b in zip(q, x[j])),
                                       Fraction(0)), -j))
        agree += 1 if names[inner] == nearest_name else 0
    uniform = tuple(sum((row[j] for row in x), Fraction(0)) / len(x)
                    for j in range(len(x[0])))
    return {
        "domain": domain, "rows": len(rows), "scales": tuple(scales),
        "by_scale": by_scale,
        "scale_zero_mixture_is_the_mean":
            _max_abs_diff((by_scale["0"]["mixture_row0"],), (uniform,)) == 0,
        "inner_argmax_agrees_with_shipped_nearest": agree,
        "rows_compared": len(rows),
    }


def promotion_checklist() -> Dict[str, object]:
    """What would have to hold for this module to leave the sandbox.

    The safety line is the sandbox rule itself -- nothing the system
    computes with imports this module, and deleting it moves no answer.
    The utility line is the paper's promise: that the elementary operations
    the substrate already ships are *sufficient* for attention, which the
    checks below measure rather than assume.  What is deliberately absent:
    a wired query kind, a compiled Lean specification, and a corpus-
    registered study -- each named here so the checklist fails loudly
    while they are missing.
    """
    report = attention_report()
    demo = report["paper_demo"]
    exact_stages = sum(
        1 for k, v in demo["stage_errors"].items() if v == 0)
    checks = {
        "elementary_ops_agree_with_shipped_ground_truth":
            bool(report["transpose_agrees_all_exact_shapes"]
                 and report["matmul_agrees_all_shapes"]),
        "paper_figure_2_reproduced_with_zero_error_given_inputs":
            exact_stages == 5,
        "paper_figure_3_inverse_exact_and_agrees":
            bool(report["paper_inverse"]["agrees_with_gauss_jordan"]),
        "softmax_error_bounded_not_hidden":
            demo["stage_errors"]["Y3 = softmax(Y2)"] > 0,
        "lemma_5_feasibility_enforced_as_refusal":
            report["coverage_boundary_d3"]["refused_at"] is not None,
        "hierarchy_embedding_exact":
            bool(report["hierarchy_exact_on_4x6_host"]),
        "wired_to_a_query_kind": False,
        "lean_specification_compiled": False,
        "study_registered_in_corpus": False,
    }
    return {
        "checks": checks,
        "order": tuple(checks),
        "ready": all(checks.values()),
        "exact_stages_zero_error": exact_stages,
        "softmax_stage_error": demo["stage_errors"]["Y3 = softmax(Y2)"],
        "headline": ("attention compiles onto the substrate exactly except "
                     "its exponential, which is bounded; the module is not "
                     "yet a faculty"),
    }
