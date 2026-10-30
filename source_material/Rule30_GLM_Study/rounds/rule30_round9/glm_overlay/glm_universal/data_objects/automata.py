"""``glm_universal.data_objects.automata`` -- the cellular-automaton carrier ("the Wheel").

A register of **deterministic one-dimensional processes**: the 256 elementary cellular
automata, each named by the eight output bits of its local rule, and a set of exact carriers
for one particular run, wheel ``00011110`` (decimal 30) started from the impulse row
``delta_0`` and read at column 0.

Nothing here is named by an English description.  A wheel is named by its truth table, so
the rule is carried inside the name:

    wheel_00011110   the local map  f(L, C, R) = bit (4L + 2C + R) of 0b00011110
                     = L + C + R + C*R  over GF(2)  = L xor (C or R)

and every carrier records the exact statement it stands for, its evidence class and the Lean
theorem that certifies it (Lean package ``RequestProject/GLM/Rule30``, namespace
``GLM.Rule30``).  The evidence classes are the ones of the Lean package's ``claims.csv``:

    FORMAL  Lean proof for every parameter
    CERT    exact-integer certificate checked in Lean over a stated finite range
    EXH     exhaustive finite check in Lean
    EMP     exact-integer computation outside Lean (here: this module); not a theorem
    OPEN    stated precisely, not proved

Arithmetic is integer / ``Fraction`` / GF(2) only.  No float is built.

Carrier layout (24 exact coordinates) for a wheel::

    0..7    out_000 .. out_111      the local rule's truth table (index 4L + 2C + R)
    8..15   anf_1 .. anf_LCR        its algebraic normal form over GF(2)
                                    (monomials 1, R, C, CR, L, LR, LC, LCR)
    16      left_permutive          1 if flipping L always flips the output
    17      right_permutive         1 if flipping R always flips the output
    18      affine                  1 if the ANF has degree <= 1
    19      mirror_number           the wheel read in a mirror (c -> -c)
    20      complement_number       the wheel with the colours swapped
    21      class_rep               least number in the symmetry class
    22      anf_degree              degree of the local ANF
    23      number                  the wheel number itself

Run carriers use the layout ``RUN_LAYOUT`` below; their headline exact value is attribute
``value`` (an ``int`` or ``Fraction``), or ``None`` for an OPEN statement.
"""

from __future__ import annotations

import re
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from .base import DataObject

__all__ = [
    "WHEEL_LAYOUT", "RUN_LAYOUT", "table_bits", "wheel_name", "local_rule", "local_anf",
    "mirror_number", "complement_number", "class_rep", "is_left_permutive",
    "is_right_permutive", "evolve_impulse_column", "wobble", "anf_of_cone",
    "essential_inputs", "left_edge_derivative_is_one", "lag_mismatches", "automata_objects",
    "value_of", "substitute_values", "LEAN_PACKAGE",
]

LEAN_PACKAGE = "RequestProject/GLM/Rule30 (namespace GLM.Rule30)"

WHEEL_LAYOUT: Tuple[str, ...] = (
    "out_000", "out_001", "out_010", "out_011", "out_100", "out_101", "out_110", "out_111",
    "anf_1", "anf_R", "anf_C", "anf_CR", "anf_L", "anf_LR", "anf_LC", "anf_LCR",
    "left_permutive", "right_permutive", "affine", "mirror_number", "complement_number",
    "class_rep", "anf_degree", "number")

RUN_LAYOUT: Tuple[str, ...] = (
    "wheel_number", "parameter", "value_num", "value_den", "evidence_rank",
    "aux00", "aux01", "aux02", "aux03", "aux04", "aux05", "aux06", "aux07",
    "aux08", "aux09", "aux10", "aux11", "aux12", "aux13", "aux14", "aux15",
    "aux16", "aux17", "aux18")

EVIDENCE_RANK = {"FORMAL": 4, "CERT": 3, "EXH": 2, "EMP": 1, "OPEN": 0}


# ===========================================================================
# 1.  THE FAMILY: local rules as exact objects
# ===========================================================================

def table_bits(r: int) -> str:
    """The eight output bits of wheel ``r``, pattern ``111`` first (Wolfram's order)."""
    if not 0 <= r < 256:
        raise ValueError(f"table_bits: a wheel number is in [0, 256), got {r}")
    return format(r, "08b")


def wheel_name(r: int) -> str:
    """The register name of wheel ``r``: its truth table."""
    return f"wheel_{table_bits(r)}"


def local_rule(r: int, L: int, C: int, R: int) -> int:
    """Output of wheel ``r`` for the neighbourhood ``(L, C, R)``: bit ``4L + 2C + R``."""
    return (r >> (4 * L + 2 * C + R)) & 1


def local_anf(r: int) -> Tuple[int, ...]:
    """ANF coefficients over GF(2), monomial index ``4l + 2c + r'`` (bit set = variable in).

    Moebius transform of the truth table: the coefficient of ``prod_{i in S} x_i`` is the XOR
    of the outputs over all sub-patterns of ``S``.
    """
    f = [local_rule(r, (i >> 2) & 1, (i >> 1) & 1, i & 1) for i in range(8)]
    for bit in (1, 2, 4):
        for i in range(8):
            if i & bit:
                f[i] ^= f[i ^ bit]
    return tuple(f)


def anf_degree_local(r: int) -> int:
    coeffs = local_anf(r)
    return max((bin(i).count("1") for i in range(8) if coeffs[i]), default=0)


def _from_table(f) -> int:
    return sum(f((i >> 2) & 1, (i >> 1) & 1, i & 1) << i for i in range(8))


def mirror_number(r: int) -> int:
    """Lean: ``mirrorNum``."""
    return _from_table(lambda L, C, R: local_rule(r, R, C, L))


def complement_number(r: int) -> int:
    """Lean: ``complementNum``."""
    return _from_table(lambda L, C, R: 1 - local_rule(r, 1 - L, 1 - C, 1 - R))


def symmetry_class(r: int) -> Tuple[int, ...]:
    m, c = mirror_number(r), complement_number(r)
    return tuple(sorted({r, m, c, mirror_number(c)}))


def class_rep(r: int) -> int:
    return symmetry_class(r)[0]


def is_left_permutive(r: int) -> bool:
    return all(local_rule(r, 1, C, R) != local_rule(r, 0, C, R) for C in (0, 1) for R in (0, 1))


def is_right_permutive(r: int) -> bool:
    return all(local_rule(r, L, C, 1) != local_rule(r, L, C, 0) for L in (0, 1) for C in (0, 1))


# ===========================================================================
# 2.  THE PROCESS: exact evolution (bit-parallel on Python integers)
# ===========================================================================

def _step(r: int, row: int, mask: int) -> int:
    """One synchronous step of wheel ``r`` on a finite window (bit p = cell p - offset)."""
    left = (row << 1) & mask     # bit p holds cell p-1  (the left neighbour)
    right = row >> 1             # bit p holds cell p+1  (the right neighbour)
    out = 0
    for i in range(8):
        if (r >> i) & 1:
            a = left if (i >> 2) & 1 else (~left & mask)
            b = row if (i >> 1) & 1 else (~row & mask)
            c = right if i & 1 else (~right & mask)
            out |= a & b & c
    return out & mask


@lru_cache(maxsize=64)
def evolve_impulse_column(r: int, steps: int, column: int = 0) -> Tuple[int, ...]:
    """Column ``column`` of wheel ``r`` from the impulse row ``delta_0``, times ``0..steps-1``.

    The row is held exactly on a window ``[-h, h]`` with ``h = steps + |column| + 2``.  Every
    cell outside the impulse's light cone carries the same value ``bg(t)`` (white for even
    ``r``; for odd ``r`` the quiescent background itself flips), and the window is padded with
    that value at each step, so the values are exact and not approximations of an infinite row.
    """
    if steps < 0:
        raise ValueError("evolve_impulse_column: steps must be non-negative")
    half = steps + abs(column) + 2
    width = 2 * half + 1
    mask = (1 << width) - 1
    ext_mask = (1 << (width + 2)) - 1
    row = 1 << half
    bg = 0
    out: List[int] = []
    for _ in range(steps):
        out.append((row >> (half + column)) & 1)
        ext = bg | (row << 1) | (bg << (width + 1))
        row = (_step(r, ext, ext_mask) >> 1) & mask
        bg = local_rule(r, bg, bg, bg)
    return tuple(out)


def ones(bits: Sequence[int], n: int) -> int:
    return sum(bits[:n])


def wobble(bits: Sequence[int], n: int) -> int:
    """The delta-sigma accumulator ``D(n) = 2 * #{i < n : a(i) = 1} - n`` (Lean: ``wobble``)."""
    return 2 * ones(bits, n) - n


def lag_mismatches(bits: Sequence[int], lag: int, n: int) -> int:
    """``#{lag <= t < n : a(t) != a(t - lag)}`` -- the errors of the lag-``lag`` predictor."""
    return sum(1 for t in range(lag, n) if bits[t] != bits[t - lag])


# ---------------------------------------------------------------------------
# bit-sliced truth tables of the n-step light-cone map (all 2^(2n+1) rows at once)
# ---------------------------------------------------------------------------

MAX_CONE_INPUTS = 17


def _cone_table(r: int, n: int) -> Tuple[int, int]:
    """Truth table of ``(x_{-n}, ..., x_n) -> a_r(n)(0)`` as one integer of ``2^(2n+1)`` bits.

    Input ``j`` (cell ``j - n``) is the pattern "bit ``j`` of the row index", so one Boolean
    operation on these integers evaluates every input row at once.
    """
    k = 2 * n + 1
    if k > MAX_CONE_INPUTS:
        raise ValueError(f"cone tables are built for 2n+1 <= {MAX_CONE_INPUTS}; asked n = {n}")
    size = 1 << k
    full = (1 << size) - 1
    cells = []
    for j in range(k):
        block = (1 << (1 << j)) - 1
        pattern = 0
        for start in range(1 << j, size, 1 << (j + 1)):
            pattern |= block << start
        cells.append(pattern)
    for _ in range(n):
        new = []
        for p in range(1, len(cells) - 1):
            L, C, R = cells[p - 1], cells[p], cells[p + 1]
            acc = 0
            for i in range(8):
                if (r >> i) & 1:
                    a = L if (i >> 2) & 1 else (~L & full)
                    b = C if (i >> 1) & 1 else (~C & full)
                    c = R if i & 1 else (~R & full)
                    acc |= a & b & c
            new.append(acc)
        cells = new
    return cells[0], k


def _low_mask(size: int, step: int) -> int:
    block = (1 << step) - 1
    lo = 0
    for start in range(0, size, 2 * step):
        lo |= block << start
    return lo


def anf_of_cone(r: int, n: int) -> Dict[str, object]:
    """Exact ANF of the ``n``-step light-cone map of wheel ``r`` (``2n+1 <= 17``)."""
    f, k = _cone_table(r, n)
    size = 1 << k
    for j in range(k):
        step = 1 << j
        f ^= (f & _low_mask(size, step)) << step
    degree, count, top = 0, 0, []
    g = f
    while g:
        low = g & -g
        idx = low.bit_length() - 1
        w = bin(idx).count("1")
        count += 1
        if w > degree:
            degree, top = w, [idx]
        elif w == degree:
            top.append(idx)
        g ^= low
    tops = [[j - n for j in range(k) if (idx >> j) & 1] for idx in top]
    return {"degree": degree, "monomials": count, "top_monomials": tops}


def essential_inputs(r: int, n: int) -> List[int]:
    """Cells ``c in [-n, n]`` on which ``a_r(n)(0)`` depends essentially (``2n+1 <= 17``)."""
    f, k = _cone_table(r, n)
    size = 1 << k
    out = []
    for j in range(k):
        step = 1 << j
        lo = _low_mask(size, step)
        swapped = ((f & lo) << step) | ((f >> step) & lo)
        if swapped != f:
            out.append(j - n)
    return out


def left_edge_derivative_is_one(r: int, n: int) -> bool:
    """Whether flipping ``x_{-n}`` flips ``a_r(n)(0)`` on every row (``2n+1 <= 17``)."""
    f, k = _cone_table(r, n)
    size = 1 << k
    lo = _low_mask(size, 1)
    swapped = ((f & lo) << 1) | ((f >> 1) & lo)
    return (swapped ^ f) == (1 << size) - 1


# ===========================================================================
# 3.  THE REGISTER
# ===========================================================================

_MONOMIAL_NAMES = ["1", "R", "C", "C*R", "L", "L*R", "L*C", "L*C*R"]


#: Monomial indices in reading order: 1, L, C, R, L*C, L*R, C*R, L*C*R.
_MONOMIAL_ORDER = (0, 4, 2, 1, 6, 5, 3, 7)


def anf_text(r: int) -> str:
    anf = local_anf(r)
    terms = [_MONOMIAL_NAMES[i] for i in _MONOMIAL_ORDER if anf[i]]
    return " + ".join(terms) if terms else "0"


def _wheel_object(r: int) -> DataObject:
    anf = local_anf(r)
    m, c = mirror_number(r), complement_number(r)
    carrier = [local_rule(r, (i >> 2) & 1, (i >> 1) & 1, i & 1) for i in range(8)]
    carrier += list(anf)
    carrier += [int(is_left_permutive(r)), int(is_right_permutive(r)),
                int(anf_degree_local(r) <= 1), m, c, class_rep(r), anf_degree_local(r), r]
    poly = anf_text(r)
    return DataObject(
        name=wheel_name(r), domain="automata", carrier=carrier, layout=WHEEL_LAYOUT,
        attributes={
            "kind": "wheel", "number": r, "symbol": f"wheel_{r}",
            "table": table_bits(r), "anf": poly, "value": r,
            "statement": (f"local map f(L,C,R) = bit (4L+2C+R) of {r} = 0b{table_bits(r)}; "
                          f"over GF(2): f = {poly}"),
            "evidence": "FORMAL",
            "lean": "GLM.Rule30.ecaRule, ecaEvolve, ecaColumn (ElementaryCA.lean)",
            "mirror": m, "complement": c, "class": list(symmetry_class(r)),
            "left_permutive": is_left_permutive(r), "right_permutive": is_right_permutive(r),
        },
        provenance={"source": "glm_universal.data_objects.automata._wheel_object",
                    "lean": LEAN_PACKAGE})


def _run_object(name: str, aliases: Tuple[str, str], parameter: int, value,
                evidence: str, statement: str, lean: str, aux: Sequence[int] = (),
                extra: Optional[Dict[str, object]] = None, wheel: int = 30,
                about: str = "run") -> DataObject:
    if value is None:
        num, den = 0, 0
    else:
        v = Fraction(value)
        num, den = v.numerator, v.denominator
    aux = list(aux)[:19]
    carrier = [wheel, parameter, num, den, EVIDENCE_RANK[evidence]] + aux + [0] * (19 - len(aux))
    attrs: Dict[str, object] = {
        "kind": "run", "wheel": wheel, "table": table_bits(wheel), "row": "delta_0",
        "column": 0, "name": aliases[0], "symbol": aliases[1], "value": value,
        "evidence": evidence, "statement": statement, "lean": lean, "parameter": parameter,
        "about": about,
    }
    if extra:
        attrs.update(extra)
    return DataObject(name=name, domain="automata", carrier=carrier, layout=RUN_LAYOUT,
                      attributes=attrs,
                      provenance={"source": "glm_universal.data_objects.automata",
                                  "lean": LEAN_PACKAGE})


#: Exact wobble values beyond the in-module run, with their evidence.
QUOTED_WOBBLE = {
    1000000: (1536, "CERT", "GLM.Rule30.wobble_1e6 : wobble centerCol 1000000 = 1536"),
}

#: The length of the wheel-30 impulse run computed when the register loads.
RUN_LENGTH = 10000


@lru_cache(maxsize=1)
def automata_objects() -> Tuple[DataObject, ...]:
    """The register: 256 wheels, the family carrier, and the wheel-30 impulse-run carriers."""
    out: List[DataObject] = [_wheel_object(r) for r in range(256)]

    reps = sorted({class_rep(r) for r in range(256)})
    lp = [r for r in range(256) if is_left_permutive(r)]
    out.append(DataObject(
        name="wheel_family", domain="automata",
        carrier=[256, len(reps), len(lp), sum(1 for r in range(256) if is_right_permutive(r)),
                 sum(1 for r in range(256) if anf_degree_local(r) <= 1)] + [0] * 19,
        attributes={
            "kind": "family", "symbol": "elementary_wheels",
            "value": len(reps), "evidence": "FORMAL",
            "statement": (f"256 local maps GF(2)^3 -> GF(2); {len(reps)} classes under "
                          f"mirror (c -> -c) and colour swap; {len(lp)} left-permutive "
                          f"(wheel 30 among them)"),
            "lean": ("GLM.Rule30.card_equivalence_classes (= 88), card_leftPermutive (= 16), "
                     "ecaEvolve_mirror, ecaEvolve_complement"),
            "left_permutive_wheels": lp,
        },
        provenance={"source": "glm_universal.data_objects.automata", "lean": LEAN_PACKAGE}))

    bits = evolve_impulse_column(30, RUN_LENGTH)

    # -- the delta-sigma accumulator D(N) ------------------------------------------------
    for N in (10, 100, 1000, 10000):
        D = wobble(bits, N)
        out.append(_run_object(
            f"wheel_30_wobble_D_{N}", (f"r30_wobble_D_{N}", f"wheel_00011110_wobble_D_{N}"),
            N, D, "EMP",
            f"D({N}) = 2*#{{i < {N} : a(i) = 1}} - {N} = {D},  a(n) = T_30^n(delta_0)(0)",
            ("GLM.Rule30.wobble (definition); value computed exactly by this register.  "
             "Lean certifies 24979*D(N)^2 <= 175561*N for all N <= 10^6 "
             "(wobble_sq_ratio_cert)"),
            aux=[ones(bits, N)]))
    for N, (D, ev, lean) in QUOTED_WOBBLE.items():
        out.append(_run_object(
            f"wheel_30_wobble_D_{N}", (f"r30_wobble_D_{N}", f"wheel_00011110_wobble_D_{N}"),
            N, D, ev, f"D({N}) = {D},  a(n) = T_30^n(delta_0)(0)", lean, aux=[(D + N) // 2]))

    out.append(_run_object(
        "wheel_30_delta_sigma_accumulator",
        ("r30_delta_sigma_accumulator", "wheel_00011110_accumulator"),
        RUN_LENGTH, None, "OPEN",
        ("D(N) = 2*sum_{i<N} a(i) - N.  PROVED: D(N+1) = D(N) + (2a(N) - 1); |D(N)| <= N; "
         "D(N) = N mod 2; frequency -> 1/2  <=>  D(N)/N -> 0;  |D(N)| <= C*sqrt(N) eventually "
         "=> frequency -> 1/2.  OPEN: D(N)/N -> 0 for this run (question 2).  The observer's "
         "arrow is -sign D(N)."),
        ("GLM.Rule30.wobble_succ, abs_wobble_le, wobble_parity, problem2_iff_wobble, "
         "problem2_of_sqrt_bound; Perspective.lean (arrow)")))

    # -- algebraic degree of the n-step map ----------------------------------------------
    for n in range(1, 21):
        deg = 2 if n == 1 else 2 * n - 1
        out.append(_run_object(
            f"wheel_30_anf_degree_{n}", (f"r30_anf_degree_{n}", f"wheel_00011110_degree_{n}"),
            n, deg, "FORMAL",
            (f"deg_GF(2) of x -> T_30^{n}(x)(0) = {deg}"
             + ("" if n == 1 else f" = 2n-1; top monomial x_{{{2 - n}}}...x_{{{n}}}")),
            ("GLM.Rule30.center_anfDegree_eq (every n >= 2)" if n > 1
             else "local ANF L + C + R + C*R (degree 2)"), about="map"))

    # -- essential inputs / light-cone dependency -----------------------------------------
    for n in range(0, 21):
        out.append(_run_object(
            f"wheel_30_essential_inputs_{n}",
            (f"r30_essential_inputs_{n}", f"r30_light_cone_dependency_{n}"),
            n, 2 * n + 1, "FORMAL",
            (f"x -> T_30^{n}(x)(0) depends essentially on all {2 * n + 1} cells "
             f"x_{{-{n}}}..x_{{{n}}} of its light cone; every fan-in-2 circuit for it has "
             f">= {n} gates"),
            "GLM.Rule30.wholeConeDependence_holds, circuit_size_ge (WholeCone.lean)",
            about="map"))

    out.append(_run_object(
        "wheel_30_cone_separation_derivative",
        ("r30_cone_separation_derivative", "wheel_00011110_left_edge_derivative"),
        0, 1, "FORMAL",
        ("d T_30^n(x)(c) / d x_{c-n} = 1 for every row x and every n (left-permutivity of the "
         "n-step map); the right-edge derivative is the product of (1 + x) along the inner "
         "diagonal, so it is not constant.  Holds for all 16 left-permutive wheels."),
        ("GLM.Rule30.evolve_flip_left_edge, booleanDerivative_right_edge, "
         "ecaEvolve_flip_left_edge (family)"), about="map"))

    # -- lag predictors (finite-state observers of the simplest kind) ---------------------
    lag_counts = [lag_mismatches(bits, p, RUN_LENGTH) for p in range(1, 17)]
    rates = [Fraction(lag_counts[i], RUN_LENGTH - (i + 1)) for i in range(16)]
    best = min(range(16), key=lambda i: rates[i])
    out.append(_run_object(
        "wheel_30_lag_predictor", ("r30_lag_predictor", "r30_fs_observer_error_rate"),
        RUN_LENGTH, rates[best], "EMP",
        (f"lag-p predictor guesses a(t) = a(t-p); errors on p <= t < {RUN_LENGTH} for "
         f"p = 1..16: {lag_counts}; least error rate {rates[best]} at p = {best + 1}.  "
         f"PROVED: question 1  <=>  every finite-state observer (in particular every lag "
         f"predictor) errs infinitely often."),
        ("GLM.Rule30.problem1_iff_fsObservers_fail (FiniteState.lean); lag form in "
         "Spectral.lean and RuleSpace.lean"),
        aux=lag_counts[:16]))

    # -- the three questions -------------------------------------------------------------
    out.append(_run_object(
        "wheel_30_question_1", ("r30_question_aperiodicity", "wheel_00011110_q1"),
        1, None, "OPEN",
        ("NOT exists p > 0, N : for all n >= N, a(n+p) = a(n),  a(n) = T_30^n(delta_0)(0).  "
         "PROVED partial: no column is eventually constant (p = 1); at most one column of the "
         "run is eventually periodic; no two adjacent columns are; same answer as for wheel 86 "
         "(mirror) and for wheel 135 on the complemented impulse."),
        ("GLM.Rule30.Problem1 = WheelProblem1 30 seed 0 (problem1_iff_wheel); "
         "column_not_eventually_constant, seed_at_most_one_periodic_column, "
         "problem1_iff_eightySix, problem1_iff_oneThirtyFive"), about="question"))
    out.append(_run_object(
        "wheel_30_question_2", ("r30_question_balance", "wheel_00011110_q2"),
        2, None, "OPEN",
        ("#{i < N : a(i) = 1} / N -> 1/2, equivalently D(N)/N -> 0.  PROVED: holds for "
         "almost every initial row (fair-coin measure); no finite prefix decides it; "
         "SeedFSTypical => questions 1 and 2."),
        ("GLM.Rule30.Problem2 = WheelProblem2 30 seed 0; problem2_iff_wobble, "
         "ae_fsTypical, no_finite_certificate_problem2, problems_one_and_two_of_seed_fsTypical"), about="question"))
    out.append(_run_object(
        "wheel_30_question_3", ("r30_question_cost", "wheel_00011110_q3"),
        3, None, "OPEN",
        ("no multi-tape Turing machine computes n -> a(n) (n in binary) in time o(n).  PROVED "
         "nearby: the n-step light-cone map needs all 2n+1 inputs and >= n gates; but that is a "
         "different function (2n+1 input bits instead of log n)."),
        ("GLM.Rule30.Problem3 = WheelProblem3 30 (problem3_iff_wheel); "
         "wholeConeDependence_holds, circuit_size_ge, nonuniform_trivial"), about="question"))

    # -- a settled neighbour in the family -------------------------------------------------
    out.append(_run_object(
        "wheel_90_impulse_centre", ("r90_impulse_centre", "wheel_01011010_impulse_centre"),
        0, 1, "FORMAL",
        ("wheel 90 (f = L + R) from delta_0: column 0 is 1, 0, 0, 0, ...; questions 1 and 2 "
         "both have answer NO, although wheel 90 is left-permutive like wheel 30"),
        ("GLM.Rule30.ecaColumn_ninety_centre, not_wheelProblem1_ninety, "
         "not_wheelProblem2_ninety"), wheel=90))
    return tuple(out)


# ===========================================================================
# 4.  EXACT VALUES FOR compare / real
# ===========================================================================

def _aliases(obj: DataObject) -> Tuple[str, ...]:
    attrs = obj.attributes or {}
    return tuple(a.lower() for a in (obj.name, str(attrs.get("name", "")),
                                     str(attrs.get("symbol", ""))) if a)


def value_of(name: str):
    """``(carrier, exact value)`` for an automata carrier named by any alias, else ``None``."""
    key = name.strip().lower()
    for obj in automata_objects():
        if key in _aliases(obj):
            return obj, (obj.attributes or {}).get("value")
    return None


def mentions_carrier(text: str) -> bool:
    return any(value_of(w) is not None for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))


def substitute_values(text: str) -> Tuple[str, List[str]]:
    """Replace automata carrier names in ``text`` by their exact values.

    Returns the rewritten text and one note per substitution (value, evidence class, Lean
    reference).  An OPEN carrier has no value: naming it in an arithmetic expression raises
    ``ValueError`` carrying the statement, so the refusal says what is open instead of
    computing with an invented number.
    """
    notes: List[str] = []

    def repl(match):
        word = match.group(0)
        found = value_of(word)
        if found is None:
            return word
        obj, value = found
        if value is None:
            raise ValueError(
                f"{word} is an OPEN statement and has no value: "
                f"{obj.attributes.get('statement')}")
        v = Fraction(value)
        notes.append(f"{word} = {v} [{obj.attributes.get('evidence')}: "
                     f"{obj.attributes.get('lean')}]")
        return f"({v.numerator}/{v.denominator})" if v.denominator != 1 else f"({v.numerator})"

    return re.sub(r"[A-Za-z_][A-Za-z0-9_]*", repl, text), notes
