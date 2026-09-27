"""``glm_universal.substrate.lattice48`` -- the 48-dimensional extremal lattice.

Why there is a 48 next to the 32
--------------------------------
:mod:`glm_universal.substrate.lattice32` builds the next extremal even
unimodular lattice after the Leech lattice: 32 coordinates, minimum 4, kissing
146,880, and a three-level address.  The rung after that is dimension **48**,
where the extremal minimum is ``2 + 2 * floor(48/24) = 6``.  Everything gets
harder there, and the honest reason is worth stating: in 24 and 32 dimensions
a binary code carries the whole construction, and in 48 dimensions it does
not.

The binary route stops early
----------------------------
There is a beautiful binary code of the right size -- the extended quadratic
residue code ``QR(47)``, a ``[48, 24, 12]`` self-dual doubly even code, built
here from the quadratic residues mod 47.  :func:`binary_code_report` verifies
self-duality, double evenness and (behind a flag, by exhausting all ``2^24``
codewords with a Gray code) the minimum distance 12.  But Construction A over
a *binary* code always contains ``2 e_i``, whose norm in the ``|x|^2 / 2``
model is 2.  The binary lattice is therefore stuck at minimum 2, four short of
extremal, and no amount of glue over that code reaches 6.

The ternary route works
-----------------------
Over ``F_3`` the same idea has room: Construction A over a *ternary* code,
``A = {x in Z^48 : x mod 3 in C}`` with the form ``|x|^2 / 3``, has shortest
"trivial" vectors ``3 e_i`` of norm **3**, not 2.  The code used is the Pless
symmetry code ``C(23)``: the generator is ``[I_24 | S]`` where ``S`` is the
bordered Jacobsthal matrix of the prime 23.  Its properties, all recomputed by
:func:`ternary_code_report`, are

============================  ==================================================
``S S^T = -I`` over ``F_3``   makes ``[I | S]`` self-orthogonal, hence (having
                              dimension 24 in length 48) **self-dual**
``S^T = -S``                  the code is a symmetry code: both halves are
                              information sets, since ``S^{-1} = -S^T``
weights divisible by 3        automatic for a self-dual ternary code
minimum distance **15**       verified exhaustively over both information sets

The ladder to an extremal lattice
---------------------------------
============  ============================================  ========  ========
lattice       definition                                    det       minimum
============  ============================================  ========  ========
``A``         ``{x in Z^48 : x mod 3 in C}``, ``|x|^2 / 3``  1         3 (odd)
``L0``        ``{x in A : sum(x) even}``                     4         **6**
``N1``        ``L0 + Z h``,       ``h = (3/2) * 1``          1         4
``N2``        ``L0 + Z h'``,      ``h' = 3 e_0 + h``         1         **6**
============  ============================================  ========  ========

``L0`` reaching 6 is the machine-checked part: it is
``GLM.HigherLattices.Ternary.even_norm_ge_eighteen``, which says that a nonzero
vector of an even lattice built over a ternary code of minimum weight 15 has
``|x|^2 >= 18``.  ``N1`` and ``N2`` are the two even unimodular *neighbours* of
``L0``; both have determinant 1 and even norms, and they differ only in which
coset of ``L0`` is glued on.

Every vector in the glued coset has all 48 coordinates half-odd-integers, so
its norm is at least ``48 * (1/4) / 3 * 3 = 4``, with equality **iff** every
coordinate is ``+-1/2``.  Translating that back through ``x = y - h`` turns the
equality case into a statement about the code: the norm-4 vectors of ``N1``
correspond exactly to the codewords of ``C`` of full weight 48 whose number of
``2``-coordinates is *even*, and those of ``N2`` to the full-weight codewords
whose number of ``2``-coordinates is *odd*.

:func:`full_weight_census` settles that by enumeration: there are exactly **96**
full-weight codewords, and **all 96** have an even number of ``2``s.  So all of
them land in ``N1`` -- which therefore has minimum 4 -- and *none* land in
``N2``.  Since the coset norms of ``N2`` are even integers with no value 4, and
``L0`` already has minimum 6, ``N2`` has minimum 6: an extremal even unimodular
lattice in 48 dimensions, certified rather than quoted.

The count 96 is cross-checked independently: :func:`weight_enumerator` solves
for the extremal ternary weight enumerator in the Gleason basis
``phi_4 = x^4 + 8 x y^3``, ``phi_12 = y^3 (x^3 - y^3)^3`` from
``A_0 = 1, A_3 = A_6 = A_9 = A_12 = 0``, and reads off ``A_48 = 96``.

Cost
----
Two routines are exhaustive searches and are therefore opt-in:

* :func:`binary_minimum_distance` -- ``2^24`` Gray-code steps, a few seconds;
* :func:`full_weight_census` and :func:`ternary_minimum_distance` -- ``2^23``
  and ``~4.3M`` steps respectively, a few seconds each.

:func:`lattice48_report` runs the cheap certificates by default and takes
``exhaustive=True`` to recompute the expensive ones.  All results are exact
integer or :class:`~fractions.Fraction` arithmetic; nothing here uses floats.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

__all__ = [
    "DIM",
    "TERNARY_PRIME",
    "BINARY_PRIME",
    "TERNARY_MIN_WEIGHT",
    "BINARY_MIN_WEIGHT",
    "FULL_WEIGHT_WORDS",
    "legendre",
    "jacobsthal",
    "symmetry_matrix",
    "ternary_generator",
    "ternary_code_report",
    "ternary_minimum_distance",
    "weight_enumerator",
    "full_weight_census",
    "binary_generator",
    "binary_code_report",
    "binary_minimum_distance",
    "construction_a_report",
    "even_sublattice_report",
    "neighbour_report",
    "lattice48_report",
]


DIM = 48
TERNARY_PRIME = 3
BINARY_PRIME = 2
TERNARY_Q = 23
BINARY_Q = 47

#: minimum distance of the Pless symmetry code ``C(23)``
TERNARY_MIN_WEIGHT = 15
#: minimum distance of the extended quadratic residue code ``QR(47)``
BINARY_MIN_WEIGHT = 12
#: number of weight-48 codewords of ``C(23)`` (``A_48`` of the extremal
#: weight enumerator)
FULL_WEIGHT_WORDS = 96
#: extremal minimum for an even unimodular lattice of rank 48
EXTREMAL_MINIMUM = 6


# ---------------------------------------------------------------------------
# quadratic residues
# ---------------------------------------------------------------------------

def legendre(x: int, q: int) -> int:
    """The Legendre symbol ``(x | q)`` as ``-1``, ``0`` or ``1``."""
    x %= q
    if x == 0:
        return 0
    return 1 if pow(x, (q - 1) // 2, q) == 1 else -1


@lru_cache(maxsize=None)
def jacobsthal(q: int = TERNARY_Q) -> Tuple[Tuple[int, ...], ...]:
    """The Jacobsthal matrix ``Q_ij = (j - i | q)`` of order ``q``.

    For ``q = 3 (mod 4)`` it is skew-symmetric, which is what makes the
    bordered matrix a *symmetry* matrix.
    """
    return tuple(tuple(legendre(j - i, q) for j in range(q)) for i in range(q))


@lru_cache(maxsize=None)
def symmetry_matrix(q: int = TERNARY_Q) -> Tuple[Tuple[int, ...], ...]:
    """The bordered Jacobsthal matrix ``S`` of order ``q + 1``.

    Row 0 is ``(0, 1, 1, ..., 1)``, column 0 is ``(0, -1, -1, ..., -1)``, and
    the interior is the Jacobsthal matrix.  Entries are ``-1``, ``0``, ``1``
    as integers; the code uses them mod 3.
    """
    n = q + 1
    inner = jacobsthal(q)
    rows: List[List[int]] = [[0] * n for _ in range(n)]
    for j in range(1, n):
        rows[0][j] = 1
    for i in range(1, n):
        rows[i][0] = -1
    for i in range(q):
        for j in range(q):
            rows[i + 1][j + 1] = inner[i][j]
    return tuple(tuple(row) for row in rows)


# ---------------------------------------------------------------------------
# the ternary Pless symmetry code C(23)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def ternary_generator() -> Tuple[Tuple[int, ...], ...]:
    """The ``24 x 48`` generator ``[I | S]`` of ``C(23)`` over ``F_3``."""
    S = symmetry_matrix()
    n = len(S)
    rows: List[Tuple[int, ...]] = []
    for i in range(n):
        left = [1 if k == i else 0 for k in range(n)]
        rows.append(tuple(left) + tuple(x % 3 for x in S[i]))
    return tuple(rows)


@lru_cache(maxsize=None)
def dual_ternary_generator() -> Tuple[Tuple[int, ...], ...]:
    """The generator ``[-S^T | I]`` -- the same code, other information set.

    ``S S^T = -I`` and ``S^T = -S`` give ``S^{-1} = -S^T``; multiplying
    ``[I | S]`` on the left by ``-S^T`` therefore produces ``[-S^T | I]``,
    which generates the same code with the *right* half as information set.
    """
    S = symmetry_matrix()
    n = len(S)
    rows: List[Tuple[int, ...]] = []
    for i in range(n):
        left = tuple((-S[k][i]) % 3 for k in range(n))
        right = tuple(1 if k == i else 0 for k in range(n))
        rows.append(left + right)
    return tuple(rows)


def _weight(vec: Sequence[int]) -> int:
    return sum(1 for x in vec if x % 3 != 0)


def _dot3(a: Sequence[int], b: Sequence[int]) -> int:
    return sum(x * y for x, y in zip(a, b)) % 3


@lru_cache(maxsize=None)
def ternary_code_report() -> Dict[str, object]:
    """Self-duality, skewness and weight divisibility of ``C(23)``."""
    S = symmetry_matrix()
    n = len(S)
    skew = all(S[i][j] == -S[j][i] for i in range(n) for j in range(n))
    prod_ok = all(
        sum(S[i][k] * S[j][k] for k in range(n)) % 3
        == ((-1) % 3 if i == j else 0)
        for i in range(n) for j in range(n)
    )
    G = ternary_generator()
    self_orth = all(_dot3(a, b) == 0 for a in G for b in G)
    Gd = dual_ternary_generator()
    # the second generator really does generate the same code
    same_code = all(_dot3(a, b) == 0 for a in Gd for b in G)
    row_weights = sorted({_weight(row) for row in G})
    pair_weights = sorted({
        _weight([(a + c * b) % 3 for a, b in zip(x, y)])
        for x, y in combinations(G, 2) for c in (1, 2)
    })
    return {
        "name": "Pless symmetry code C(23)",
        "length": 2 * n,
        "dimension": n,
        "words": 3 ** n,
        "skew_symmetric": skew,
        "S_times_S_transpose_is_minus_I_mod_3": prod_ok,
        "self_orthogonal": self_orth,
        "self_dual": self_orth and len(G) == n,
        "second_information_set": same_code,
        "generator_row_weights": row_weights,
        "pair_weights": pair_weights,
        "all_weights_divisible_by_3": all(w % 3 == 0 for w in row_weights)
        and all(w % 3 == 0 for w in pair_weights),
        "minimum_weight": TERNARY_MIN_WEIGHT,
    }


# --- packed F_3 arithmetic -------------------------------------------------
#
# A vector over F_3 of length 48 is a pair of 48-bit masks ``(ones, twos)``.
# Addition is branch-free bit arithmetic, so a search step costs a handful of
# machine integer operations rather than a Python loop over coordinates.

_MASK48 = (1 << DIM) - 1


def _pack(vec: Sequence[int]) -> Tuple[int, int]:
    ones = twos = 0
    for i, x in enumerate(vec):
        x %= 3
        if x == 1:
            ones |= 1 << i
        elif x == 2:
            twos |= 1 << i
    return ones, twos


def _unpack(word: Tuple[int, int]) -> Tuple[int, ...]:
    ones, twos = word
    return tuple(1 if (ones >> i) & 1 else (2 if (twos >> i) & 1 else 0)
                 for i in range(DIM))


def _add(x: Tuple[int, int], y: Tuple[int, int]) -> Tuple[int, int]:
    x1, x2 = x
    y1, y2 = y
    nx = ~(x1 | x2)
    ny = ~(y1 | y2)
    return (((x1 & ny) | (y1 & nx) | (x2 & y2)) & _MASK48,
            ((x2 & ny) | (y2 & nx) | (x1 & y1)) & _MASK48)


def _double(x: Tuple[int, int]) -> Tuple[int, int]:
    return (x[1], x[0])


def _packed_weight(x: Tuple[int, int]) -> int:
    return bin(x[0] | x[1]).count("1")


def _search_low_weight(rows: Sequence[Tuple[int, int]],
                       max_support: int) -> int:
    """Smallest nonzero weight over combinations of ``<= max_support`` rows.

    Scalar multiples are quotiented out by fixing the leading coefficient
    to 1.
    """
    best = DIM + 1
    L = len(rows)

    def rec(idx: int, cur: Tuple[int, int], remaining: int) -> None:
        nonlocal best
        if remaining == 0:
            w = _packed_weight(cur)
            if 0 < w < best:
                best = w
            return
        for i in range(idx, L - remaining + 1):
            r = rows[i]
            rec(i + 1, _add(cur, r), remaining - 1)
            rec(i + 1, _add(cur, _double(r)), remaining - 1)

    for i in range(L):
        for extra in range(max_support):
            rec(i + 1, rows[i], extra)
    return best


@lru_cache(maxsize=None)
def ternary_minimum_distance(max_support: int = 4) -> Dict[str, object]:
    """Minimum distance of ``C(23)`` by search over both information sets.

    A codeword of weight ``w`` has left-half weight ``a`` and right-half
    weight ``b`` with ``a + b = w``, so ``min(a, b) <= w / 2``.  The left half
    is the information vector for ``[I | S]`` and the right half is the
    information vector for ``[-S^T | I]``, so searching *both* generators over
    information vectors of support ``<= k`` proves that there is no codeword
    of weight ``<= 2k``.  With ``k = 6`` that rules out every weight up to 12,
    and weights are multiples of 3, so the minimum is 15 -- which is attained.

    ``max_support = 6`` is the certifying value and costs a few seconds;
    smaller values give a weaker (but still sound) bound.
    """
    rows_a = tuple(_pack(row) for row in ternary_generator())
    rows_b = tuple(_pack(row) for row in dual_ternary_generator())
    best = min(_search_low_weight(rows_a, max_support),
               _search_low_weight(rows_b, max_support))
    proves = 2 * max_support
    return {
        "max_information_support": max_support,
        "best_weight_found": best,
        "excludes_weights_up_to": proves,
        "certifies_minimum_15": max_support >= 6 and best == TERNARY_MIN_WEIGHT,
        "minimum_weight": TERNARY_MIN_WEIGHT,
    }


# ---------------------------------------------------------------------------
# the extremal ternary weight enumerator
# ---------------------------------------------------------------------------

def _poly_mul(a: Sequence[Fraction], b: Sequence[Fraction]) -> List[Fraction]:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    out[i + j] += ai * bj
    return out


def _poly_pow(a: Sequence[Fraction], n: int) -> List[Fraction]:
    out: List[Fraction] = [Fraction(1)]
    for _ in range(n):
        out = _poly_mul(out, a)
    return out


@lru_cache(maxsize=None)
def weight_enumerator() -> Dict[str, object]:
    """The extremal weight enumerator of a self-dual ternary ``[48, 24]`` code.

    Gleason's theorem says the weight enumerator lies in the polynomial ring
    generated by ``phi_4 = x^4 + 8 x y^3`` and ``phi_12 = y^3 (x^3 - y^3)^3``.
    In degree 48 that is a 5-dimensional space, and demanding
    ``A_0 = 1`` and ``A_3 = A_6 = A_9 = A_12 = 0`` pins it down uniquely.  The
    result has non-negative integer coefficients summing to ``3^24``, so it is
    a possible enumerator, and it is the one ``C(23)`` has.

    The coefficient this module needs is ``A_48 = 96``.
    """
    phi4 = [Fraction(1), Fraction(0), Fraction(0), Fraction(8), Fraction(0)]
    cube = _poly_pow([Fraction(1), Fraction(0), Fraction(0), Fraction(-1)], 3)
    phi12 = [Fraction(0)] * 3 + cube
    basis = [_poly_mul(_poly_pow(phi4, 12 - 3 * b), _poly_pow(phi12, b))
             for b in range(5)]
    targets = [(0, Fraction(1)), (3, Fraction(0)), (6, Fraction(0)),
               (9, Fraction(0)), (12, Fraction(0))]
    n = 5
    M = [[basis[b][idx] for b in range(n)] + [val] for idx, val in targets]
    for col in range(n):
        piv = next(r for r in range(col, n) if M[r][col] != 0)
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [v / pv for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [a - f * b for a, b in zip(M[r], M[col])]
    coeffs = [M[i][n] for i in range(n)]
    W = [sum((coeffs[b] * basis[b][i] for b in range(n)), Fraction(0))
         for i in range(DIM + 1)]
    return {
        "gleason_coefficients": tuple(coeffs),
        "coefficients": tuple(W),
        "nonzero": tuple((i, W[i]) for i in range(DIM + 1) if W[i] != 0),
        "all_nonnegative_integers": all(v.denominator == 1 and v >= 0
                                        for v in W),
        "total": sum(W, Fraction(0)),
        "total_is_3_to_24": sum(W, Fraction(0)) == 3 ** 24,
        "minimum_weight": next(i for i in range(1, DIM + 1) if W[i] != 0),
        "A_48": W[DIM],
    }


# ---------------------------------------------------------------------------
# the full-weight census -- the certificate that separates N1 from N2
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def full_weight_census(exhaustive: bool = False) -> Dict[str, object]:
    """Every codeword of ``C(23)`` with no zero coordinate, split by parity.

    A full-weight codeword ``v`` in ``{1, 2}^48`` is ``1 + e`` with ``e`` a
    0/1 vector, and since the all-ones vector is in the code, ``e`` is too.
    So full-weight codewords correspond to 0/1 vectors of the code, and the
    quantity that decides which neighbour a norm-4 vector belongs to is the
    parity of ``#{i : v_i = 2} = weight(e)``.

    The enumeration is a Gray code over the ``2^23`` information vectors in
    ``{1, 2}^24`` whose first entry is 1 (the other half of the codewords are
    their scalar doubles), each step a single packed ``F_3`` addition.  With
    ``exhaustive=False`` only the recorded conclusion is returned.
    """
    if not exhaustive:
        return {
            "exhaustive": False,
            "total": FULL_WEIGHT_WORDS,
            "even_number_of_twos": FULL_WEIGHT_WORDS,
            "odd_number_of_twos": 0,
            "cross_check_A_48": weight_enumerator()["A_48"],
            "note": "recorded result; pass exhaustive=True to recompute",
        }
    G = ternary_generator()
    rows = tuple(_pack(row) for row in G)
    cur = (0, 0)
    for r in rows:
        cur = _add(cur, r)
    info = [1] * len(rows)
    even = odd = 0
    found: List[str] = []

    def record(word: Tuple[int, int]) -> None:
        nonlocal even, odd
        ones, twos = word
        if ((ones | twos) & _MASK48) != _MASK48:
            return
        twos_count = bin(twos).count("1")
        if twos_count % 2 == 0:
            even += 1
        else:
            odd += 1
        if len(found) < 3:
            found.append("".join(str(x) for x in _unpack(word)))

    record(cur)
    free = len(rows) - 1
    for step in range(1, 1 << free):
        j = ((step & -step).bit_length() - 1) + 1
        if info[j] == 1:
            cur = _add(cur, rows[j])
            info[j] = 2
        else:
            cur = _add(cur, _double(rows[j]))
            info[j] = 1
        record(cur)
    return {
        "exhaustive": True,
        "steps": 1 << free,
        "with_leading_one": even + odd,
        "total": 2 * (even + odd),
        "even_number_of_twos": 2 * even,
        "odd_number_of_twos": 2 * odd,
        "cross_check_A_48": weight_enumerator()["A_48"],
        "agrees_with_enumerator": 2 * (even + odd)
        == weight_enumerator()["A_48"],
        "examples": tuple(found),
    }


# ---------------------------------------------------------------------------
# the binary route, and why it stops
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def binary_generator() -> Tuple[int, ...]:
    """Generator of the extended quadratic residue code ``QR(47)``.

    Coordinates ``0 .. 46`` are indexed by ``Z/47`` and coordinate 47 is the
    overall parity bit.  The 24 generators are the cyclic shifts of the
    quadratic-residue indicator, each extended so that its weight is even.
    Rows are returned as 48-bit masks.
    """
    q = BINARY_Q
    residues = {(k * k) % q for k in range(1, q)}
    base = 0
    for r in residues:
        base |= 1 << r
    rows: List[int] = []
    for shift in range(24):
        word = 0
        for i in range(q):
            if (base >> i) & 1:
                word |= 1 << ((i + shift) % q)
        if bin(word).count("1") % 2 == 1:
            word |= 1 << q
        rows.append(word)
    return tuple(rows)


@lru_cache(maxsize=None)
def binary_code_report() -> Dict[str, object]:
    """Self-duality and double evenness of ``QR(47)``."""
    rows = binary_generator()
    # reduce to row echelon form to confirm the dimension is 24
    basis: List[int] = []
    for row in rows:
        cur = row
        for b in basis:
            top = b.bit_length() - 1
            if (cur >> top) & 1:
                cur ^= b
        if cur:
            basis.append(cur)
            basis.sort(reverse=True)
    weights = sorted({bin(r).count("1") for r in rows})
    orth = all(bin(a & b).count("1") % 2 == 0 for a in rows for b in rows)
    pair_weights = sorted({bin(a ^ b).count("1") for a in rows for b in rows
                           if a != b})
    return {
        "name": "extended quadratic residue code QR(47)",
        "length": DIM,
        "dimension": len(basis),
        "generator_weights": weights,
        "self_orthogonal": orth,
        "self_dual": orth and len(basis) == 24,
        "doubly_even_generators": all(w % 4 == 0 for w in weights),
        "doubly_even_pairs": all(w % 4 == 0 for w in pair_weights),
        "minimum_weight": BINARY_MIN_WEIGHT,
    }


@lru_cache(maxsize=None)
def binary_minimum_distance(exhaustive: bool = False) -> Dict[str, object]:
    """Minimum distance of ``QR(47)``, optionally by exhausting ``2^24`` words.

    The enumeration is a Gray code over the information vectors: each step
    flips one generator in or out with a single ``xor``, so the whole code is
    swept in ``2^24`` machine operations.
    """
    if not exhaustive:
        return {"exhaustive": False, "minimum_weight": BINARY_MIN_WEIGHT,
                "note": "recorded result; pass exhaustive=True to recompute"}
    rows = binary_generator()
    basis: List[int] = []
    for row in rows:
        cur = row
        for b in basis:
            top = b.bit_length() - 1
            if (cur >> top) & 1:
                cur ^= b
        if cur:
            basis.append(cur)
            basis.sort(reverse=True)
    k = len(basis)
    cur = 0
    best = DIM + 1
    counts: Dict[int, int] = {}
    for step in range(1, 1 << k):
        j = (step & -step).bit_length() - 1
        cur ^= basis[j]
        w = bin(cur).count("1")
        counts[w] = counts.get(w, 0) + 1
        if 0 < w < best:
            best = w
    return {
        "exhaustive": True,
        "dimension": k,
        "words": 1 << k,
        "minimum_weight": best,
        "agrees": best == BINARY_MIN_WEIGHT,
        "weight_distribution": tuple(sorted(counts.items())),
    }


# ---------------------------------------------------------------------------
# the lattices
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def construction_a_report() -> Dict[str, object]:
    """``A = {x in Z^48 : x mod 3 in C}`` with the form ``|x|^2 / 3``.

    The index of ``A`` in ``Z^48`` is ``3^24``, so the Gram determinant of the
    integral model is ``3^48``; dividing every vector by ``sqrt(3)`` divides
    the Gram determinant by ``3^48``, leaving 1.  The shortest vectors are
    ``3 e_i`` of norm 3 (from the zero codeword) and the lifts of minimum
    weight codewords, of norm ``15 / 3 = 5``, so the minimum is 3 and the
    lattice is **odd**.
    """
    index = 3 ** 24
    gram = index * index
    return {
        "definition": "{x in Z^48 : x mod 3 in C(23)}, norm = |x|^2 / 3",
        "index_in_Z48": index,
        "integral_gram_determinant": gram,
        "scaled_determinant": Fraction(gram, 3 ** DIM),
        "unimodular": Fraction(gram, 3 ** DIM) == 1,
        "short_vector_norms": {
            "3 e_i (zero codeword)": Fraction(9, 3),
            "minimum weight lift": Fraction(TERNARY_MIN_WEIGHT, 3),
        },
        "minimum": Fraction(3),
        "even": False,
        "reason_odd": "3 e_i has odd norm 3",
    }


@lru_cache(maxsize=None)
def even_sublattice_report() -> Dict[str, object]:
    """``L0 = {x in A : sum(x) even}``: index 2, determinant 4, minimum 6.

    ``|x|^2 = sum(x_i^2)`` has the parity of ``sum(x_i)``, so the even
    sublattice of ``A`` -- the vectors whose norm ``|x|^2 / 3`` is an even
    integer -- is exactly the coordinate-sum-even sublattice.  Its minimum is
    the machine-checked statement
    ``GLM.HigherLattices.Ternary.even_norm_ge_eighteen``: with the code
    minimum 15 in hand, ``6 | |x|^2`` and ``x != 0`` force ``|x|^2 >= 18``.
    """
    return {
        "definition": "{x in A : sum(x) even}",
        "index_in_A": 2,
        "determinant": 4,
        "case_off_code": {
            "hypothesis": "x mod 3 != 0, so the support has size >= 15",
            "bound": "|x|^2 >= 15, and 6 | |x|^2, so |x|^2 >= 18",
        },
        "case_on_code": {
            "hypothesis": "x mod 3 == 0, so 9 | |x|^2",
            "bound": "9 | |x|^2 and 6 | |x|^2 force 18 | |x|^2",
        },
        "minimum_norm2": 18,
        "minimum": Fraction(18, 3),
        "attained_by": "3 e_0 + 3 e_1",
        "theorem": "GLM.HigherLattices.Ternary.even_norm_ge_eighteen",
    }


def _coset_analysis(shift_first: int) -> Dict[str, object]:
    """Norm-4 vectors of the coset ``L0 + h`` with ``h = shift_first*e_0 + 3/2``.

    Coordinates of a coset vector ``y`` are half-odd-integers, so
    ``|y|^2 >= 48/4 = 12`` and the norm ``|y|^2/3 >= 4``, with equality iff
    every ``y_i = +-1/2``.  Writing ``x = y - h`` in that equality case gives
    ``x_i in {-1, -2}`` (shifted by ``-shift_first`` in coordinate 0), so
    ``x mod 3`` is a **full weight** codeword ``v``, with ``v_i = 2`` exactly
    where ``y_i = 1/2``.  The membership condition ``sum(x) even`` then reads
    off as a parity condition on ``#{i : v_i = 1}``.
    """
    # x_i = -1 when v_i = 2, x_i = -2 when v_i = 1, plus -shift_first at i = 0
    # sum(x) = -(48 + #{v_i = 1}) - shift_first
    # even  <=>  #{v_i = 1} + shift_first  is even
    needs_even_ones = (shift_first % 2 == 0)
    # #{v_i=1} + #{v_i=2} = 48, so the parities agree
    return {
        "shift_in_coordinate_0": shift_first,
        "coordinates": "all half-odd-integers",
        "norm_lower_bound": Fraction(4),
        "equality_case": "every coordinate +-1/2",
        "codeword_condition": "x mod 3 is a full-weight codeword",
        "parity_required_on_twos": "even" if needs_even_ones else "odd",
    }


@lru_cache(maxsize=None)
def neighbour_report(exhaustive: bool = False) -> Dict[str, object]:
    """The two even unimodular neighbours of ``L0``, and which one is extremal.

    ``h = (3/2) * 1`` has ``2h = 3 * 1`` in ``L0`` and pairs integrally with
    ``L0``, so ``N1 = L0 + Z h`` is an even unimodular lattice; replacing
    ``h`` by ``h' = 3 e_0 + h`` (``3 e_0`` lies in ``A`` but not ``L0``) gives
    the other one, ``N2``.  The census of full-weight codewords decides both
    minima at once.
    """
    census = full_weight_census(exhaustive)
    even = census["even_number_of_twos"]
    odd = census["odd_number_of_twos"]
    h_norm = Fraction(DIM * 9, 4 * 3)
    hp_norm = Fraction(Fraction(81, 4) + 47 * Fraction(9, 4), 3)
    n1 = _coset_analysis(0)
    n2 = _coset_analysis(3)
    n1_min = Fraction(4) if even else Fraction(EXTREMAL_MINIMUM)
    n2_min = Fraction(4) if odd else Fraction(EXTREMAL_MINIMUM)
    return {
        "glue_vectors": {
            "h": "(3/2, 3/2, ..., 3/2)",
            "h_norm": h_norm,
            "h_prime": "(9/2, 3/2, ..., 3/2)",
            "h_prime_norm": hp_norm,
            "both_even": h_norm % 2 == 0 and hp_norm % 2 == 0,
            "difference": "3 e_0, which lies in A but not in L0",
        },
        "census": census,
        "N1": {"coset": n1, "norm_4_vectors": even, "minimum": n1_min,
               "extremal": n1_min == EXTREMAL_MINIMUM},
        "N2": {"coset": n2, "norm_4_vectors": odd, "minimum": n2_min,
               "extremal": n2_min == EXTREMAL_MINIMUM},
        "coset_norms_are_even": "coset norms lie in 4 + 2Z, so 5 is impossible",
        "conclusion": ("N2 = L0 + Z(3 e_0 + h) is an extremal even unimodular "
                       "lattice of rank 48: minimum 6"),
        "extremal_minimum": EXTREMAL_MINIMUM,
    }


@lru_cache(maxsize=None)
def lattice48_report(exhaustive: bool = False) -> Dict[str, object]:
    """Everything this module establishes, recomputed on demand."""
    return {
        "dimension": DIM,
        "extremal_minimum": EXTREMAL_MINIMUM,
        "binary_route": {
            "code": binary_code_report(),
            "distance": binary_minimum_distance(exhaustive),
            "lattice_minimum": 2,
            "why_it_stops": "Construction A over a binary code contains 2 e_i, "
                            "of norm 2",
        },
        "ternary_route": {
            "code": ternary_code_report(),
            "distance": ternary_minimum_distance(6 if exhaustive else 4),
            "weight_enumerator": {
                k: weight_enumerator()[k]
                for k in ("all_nonnegative_integers", "total_is_3_to_24",
                          "minimum_weight", "A_48")
            },
        },
        "construction_a": construction_a_report(),
        "even_sublattice": even_sublattice_report(),
        "neighbours": neighbour_report(exhaustive),
    }
