"""``glm_universal.substrate.lattice32`` -- the 32-dimensional extremal lattice.

Why there is a 32 next to the 24
--------------------------------
The spatial layer of this package stops at the Leech lattice: 24 coordinates,
minimum 4, kissing number 196,560, and a hull census that says exactly which
targets a 24-dimensional carrier can hold.  The *next* even unimodular lattice
whose minimum is as large as the dimension allows -- **extremal** -- lives in 32
dimensions and has minimum 4 with 146,880 minimal vectors.  This module builds
one, exactly, and certifies it rather than quoting it.

The construction
----------------
Not Construction A: over a binary code, Construction A in 32 coordinates always
keeps the vectors ``2 e_i`` and so stops at minimum 2.  What is needed is a
*two-level* lift, Construction D, over a nested pair of Reed-Muller codes::

    L  =  4 Z^32  +  2 C1  +  C2,        C2 = RM(1,5)  subset  C1 = RM(3,5),

with the true lattice being ``L / 2``.  In this unscaled integer model a
lattice norm is ``|x|^2 / 4``: minimum 4 means ``|x|^2 >= 16``, and evenness
means ``8 | |x|^2``.

The two codes carry one property each, and each property closes one case of the
minimum:

============  ======================  =====================================
code          property (verified)     what it forces
============  ======================  =====================================
``C2``        ``[32, 6, 16]``         a coordinate carrying a ``C2`` bit is
                                      odd, so a vector visible at the coarse
                                      resolution has ``|x|^2 >= 16``
``C1``        ``[32, 26, 4]``         a coordinate carrying a ``C1`` bit is
                                      ``2 (mod 4)``, so ``|x|^2 >= 4 * 4``
``C2 = C1^T`` duality                 the overlap ``|b & c|`` is even, which
                                      is what makes ``|x|^2`` divisible by 8
============  ======================  =====================================

Those three lines are the whole proof, and they are machine-checked in
``RequestProject/GLM/HigherLattices.lean``
(``BarnesWall.norm_ge_of_ne_zero``, ``BarnesWall.norm_dvd_eight``).  This module
supplies the codes the theorem needs and checks that they have the properties
it assumes: :func:`code_report` computes both minimum weights (16 by
enumerating all 64 outer codewords, 4 by exhausting every vector of weight 1,
2, 3 against the inner code's parity checks) and the duality.

Multi-resolution addressing
---------------------------
The construction is also an **address at three resolutions**, which is the
thing the 24-dimensional layer does not have.  Every point has a unique
decomposition ``x = 4a + 2b + c``, and the three parts are read off by
reduction:

* ``c = x mod 2``     -- the *coarse* address, one of 64 outer codewords;
* ``b = ((x - c)/2) mod 2`` -- the *middle* address, one of 2^26 inner
  codewords;
* ``a = (x - c - 2b)/4``    -- the *fine* address, an arbitrary integer vector.

:func:`address` returns the triple, :func:`from_address` puts it back together,
and :func:`resolution_sieve` reports the *first* resolution at which a vector
fails to be a lattice point -- the 32-dimensional analogue of
:func:`glm_universal.substrate.leech_construct.mod_sieve`.  Uniqueness is
``BarnesWall.mk_injective``; the two reductions are ``mk_emod_two`` and
``mk_emod_four``.

The kissing number, counted rather than quoted
----------------------------------------------
:func:`minimal_vectors` enumerates all 146,880 of them in three classes, one
per resolution, and the census is exact:

=======================  ========  =============================================
shape                    count     where it comes from
=======================  ========  =============================================
``(+-4, 0^31)``            64      the fine level alone: ``a = +-e_i``
``(+-2^4, 0^28)``       19,840     1,240 weight-4 inner codewords, 16 signs
``(+-1^16, 0^16)``     126,976     62 weight-16 outer codewords, and for each
                                   the 2^11 inner codewords supported inside it
=======================  ========  =============================================

The third row is the interesting one: the sign pattern of a minimal vector on a
weight-16 outer codeword is not free -- the negative positions must themselves
form an inner codeword, and the number of those is computed here by solving for
the subcode supported in the 16-set, not assumed.

Everything is exact integer arithmetic; no float is constructed anywhere.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from fractions import Fraction

from .linalg import det_int, hermite_normal_form, popcount

__all__ = [
    "DIM", "MIN_NORM2", "KISSING", "SCALE",
    "monomial_mask", "outer_basis", "inner_basis", "outer_code",
    "in_outer", "in_inner", "weight",
    "code_report",
    "mk", "in_lattice", "address", "from_address", "resolution_sieve",
    "norm2", "lattice_norm",
    "supported_subcode", "minimal_vectors", "minimal_shape_census",
    "kissing_number",
    "generator_matrix", "determinant_report", "index_ladder",
    "minimum_certificate", "lattice32_report",
]

#: Number of coordinates.
DIM = 32

#: A true lattice vector is a model vector over this scale.
SCALE = 2

#: The least squared length of a nonzero point, in the unscaled model.
#: The lattice minimum is ``MIN_NORM2 / SCALE**2 = 4``.
MIN_NORM2 = 16

#: The number of minimal vectors, enumerated by :func:`minimal_vectors`.
KISSING = 146880


# ---------------------------------------------------------------------------
# The Reed-Muller pair
# ---------------------------------------------------------------------------

def monomial_mask(variables: Sequence[int]) -> int:
    """The evaluation vector of the monomial in the named variables.

    Coordinate ``p`` of ``F_2^32`` is read as the 5-bit point
    ``(p_0, ..., p_4)``; the monomial is 1 exactly where every named variable
    is 1, so the empty tuple gives the all-ones vector.
    """
    mask = 0
    for point in range(DIM):
        if all((point >> v) & 1 for v in variables):
            mask |= 1 << point
    return mask


@lru_cache(maxsize=None)
def outer_basis() -> Tuple[int, ...]:
    """A basis of ``C2 = RM(1,5)``: the constant and the five coordinates."""
    return tuple([monomial_mask(())]
                 + [monomial_mask((v,)) for v in range(5)])


@lru_cache(maxsize=None)
def inner_basis() -> Tuple[int, ...]:
    """A basis of ``C1 = RM(3,5)``: every monomial of degree at most 3."""
    return tuple(monomial_mask(S)
                 for degree in range(4)
                 for S in combinations(range(5), degree))


@lru_cache(maxsize=None)
def outer_code() -> Tuple[int, ...]:
    """All 64 codewords of the outer code, in increasing order."""
    words = {0}
    for generator in outer_basis():
        words |= {word ^ generator for word in words}
    return tuple(sorted(words))


def weight(mask: int) -> int:
    """Hamming weight of a 32-bit mask."""
    return popcount(mask)


def in_outer(mask: int) -> bool:
    """Is ``mask`` a codeword of ``C2 = RM(1,5)``?"""
    return mask in _outer_set()


@lru_cache(maxsize=None)
def _outer_set() -> frozenset:
    return frozenset(outer_code())


def in_inner(mask: int) -> bool:
    """Is ``mask`` a codeword of ``C1 = RM(3,5)``?

    Checked by parity against the outer basis, which is exactly the statement
    ``C1 = C2^perp`` -- see :func:`code_report`, which verifies that identity
    rather than assuming it.
    """
    return all(popcount(mask & check) % 2 == 0 for check in outer_basis())


@lru_cache(maxsize=None)
def code_report() -> Dict[str, object]:
    """What the two codes are, with every stated property recomputed.

    The three properties the lattice theorem needs, and how each is checked:

    * outer minimum 16 -- every one of the 64 codewords is weighed;
    * inner minimum 4 -- every vector of weight 1, 2 and 3 (5,488 of them) is
      tested against the parity checks and none passes, and a weight-4
      codeword is exhibited;
    * ``C2 subset C1`` and ``C1 = C2^perp`` -- the first by membership, the
      second by dimension count plus orthogonality.
    """
    words = outer_code()
    outer_weights = sorted({weight(word) for word in words})
    outer_min = min(weight(word) for word in words if word)

    light: List[Tuple[int, ...]] = []
    for size in (1, 2, 3):
        for support in combinations(range(DIM), size):
            mask = 0
            for position in support:
                mask |= 1 << position
            if in_inner(mask):
                light.append(support)
    quad = [support for support in combinations(range(DIM), 4)
            if in_inner(_mask_of(support))]

    return {
        "outer": {"length": DIM, "dimension": 6, "words": len(words),
                  "weights": outer_weights, "minimum_weight": outer_min,
                  "weight_16_words": sum(1 for w in words if weight(w) == 16)},
        "inner": {"length": DIM, "dimension": len(inner_basis()),
                  "minimum_weight": 4 if not light and quad else None,
                  "sub_minimum_witnesses": len(light),
                  "weight_4_words": len(quad),
                  "example_weight_4": list(quad[0]) if quad else None},
        "nested": all(in_inner(word) for word in words),
        "dual": {
            "orthogonal": all(popcount(a & b) % 2 == 0
                              for a in words for b in inner_basis()),
            "dimensions_sum": 6 + len(inner_basis()),
            "is_dual_pair": (6 + len(inner_basis()) == DIM
                             and all(popcount(a & b) % 2 == 0
                                     for a in words for b in inner_basis())),
        },
    }


def _mask_of(support: Sequence[int]) -> int:
    mask = 0
    for position in support:
        mask |= 1 << position
    return mask


# ---------------------------------------------------------------------------
# Points, addresses and membership
# ---------------------------------------------------------------------------

def mk(fine: Sequence[int], middle: int, coarse: int) -> Tuple[int, ...]:
    """Assemble ``4a + 2b + c`` from a fine vector and two codeword masks."""
    return tuple(4 * fine[i] + 2 * ((middle >> i) & 1) + ((coarse >> i) & 1)
                 for i in range(DIM))


def norm2(point: Sequence[int]) -> int:
    """Squared length in the unscaled model."""
    return sum(int(value) * int(value) for value in point)


def lattice_norm(point: Sequence[int]) -> Fraction:
    """The true lattice norm ``|x|^2 / 4`` -- exact, as a ``Fraction``."""
    return Fraction(norm2(point), SCALE * SCALE)


def address(point: Sequence[int]) -> Optional[Dict[str, object]]:
    """The three-level address of a lattice point, or ``None`` if outside.

    Returns the coarse codeword mask, the middle codeword mask and the fine
    integer vector.  The decomposition is unique
    (``BarnesWall.mk_injective``), so this is an address and not a choice.
    """
    if len(point) != DIM:
        raise ValueError("lattice32.address: expected %d coordinates" % DIM)
    coarse = 0
    for i, value in enumerate(point):
        if int(value) % 2:
            coarse |= 1 << i
    if not in_outer(coarse):
        return None
    middle = 0
    for i, value in enumerate(point):
        residue = (int(value) - ((coarse >> i) & 1)) // 2
        if residue % 2:
            middle |= 1 << i
    if not in_inner(middle):
        return None
    fine = tuple((int(point[i]) - ((coarse >> i) & 1)
                  - 2 * ((middle >> i) & 1)) // 4 for i in range(DIM))
    return {"coarse": coarse, "middle": middle, "fine": fine}


def from_address(addr: Dict[str, object]) -> Tuple[int, ...]:
    """Put a three-level address back together."""
    return mk(addr["fine"], int(addr["middle"]), int(addr["coarse"]))


def in_lattice(point: Sequence[int]) -> bool:
    """Is the integer vector a point of the (unscaled) 32-dimensional lattice?"""
    return address(point) is not None


def resolution_sieve(point: Sequence[int]) -> Dict[str, object]:
    """Run the conditions coarsest first and name the one that fails.

    A vector that fails at the coarse level is not "nearly" a lattice point:
    it is outside at the lowest resolution, and this says which.
    """
    coarse = 0
    for i, value in enumerate(point):
        if int(value) % 2:
            coarse |= 1 << i
    coarse_ok = in_outer(coarse)
    middle = 0
    for i, value in enumerate(point):
        residue = (int(value) - ((coarse >> i) & 1)) // 2
        if residue % 2:
            middle |= 1 << i
    middle_ok = in_inner(middle)
    if not coarse_ok:
        first = "coarse (x mod 2 is not an outer codeword)"
    elif not middle_ok:
        first = "middle ((x - c)/2 mod 2 is not an inner codeword)"
    else:
        first = None
    return {
        "coarse_mask": coarse, "coarse_ok": coarse_ok,
        "middle_mask": middle, "middle_ok": middle_ok,
        "in_lattice": coarse_ok and middle_ok,
        "first_failure": first,
        "norm2": norm2(point),
    }


def index_ladder() -> Dict[str, object]:
    """The chain of resolutions and the index of each step.

    ``4 Z^32 subset 4 Z^32 + 2 C1 subset L``, of indices ``2^26`` and ``2^6``;
    the whole tower has index ``2^32`` in ``4 Z^32``, which is what makes the
    determinant come out at 1 after scaling.
    """
    return {
        "levels": ["4 Z^32", "4 Z^32 + 2 C1", "4 Z^32 + 2 C1 + C2"],
        "step_indices": [2 ** len(inner_basis()), 2 ** 6],
        "total_index": 2 ** (len(inner_basis()) + 6),
        "addresses_per_level": {"coarse": 2 ** 6,
                                "middle": 2 ** len(inner_basis()),
                                "fine": "Z^32"},
    }


# ---------------------------------------------------------------------------
# The minimal vectors
# ---------------------------------------------------------------------------

def supported_subcode(support_mask: int) -> Tuple[int, ...]:
    """Every inner codeword whose support lies inside ``support_mask``.

    Solved rather than searched: the inner basis is reduced against the
    coordinates *outside* the mask and the kernel is enumerated.
    """
    outside = ((1 << DIM) - 1) & ~support_mask
    # Row-reduce the basis by the outside coordinates, keeping track of the
    # combination that produced each row.
    rows: List[Tuple[int, int]] = [(g & outside, 1 << i)
                                   for i, g in enumerate(inner_basis())]
    pivots: Dict[int, Tuple[int, int]] = {}
    kernel: List[int] = []
    for value, combo in rows:
        while value:
            low = value & -value
            if low in pivots:
                pvalue, pcombo = pivots[low]
                value ^= pvalue
                combo ^= pcombo
            else:
                pivots[low] = (value, combo)
                break
        if not value:
            kernel.append(combo)
    basis = inner_basis()
    words = {0}
    for combo in kernel:
        word = 0
        for i in range(len(basis)):
            if (combo >> i) & 1:
                word ^= basis[i]
        words |= {existing ^ word for existing in words}
    return tuple(sorted(words))


def minimal_vectors() -> Iterator[Tuple[int, ...]]:
    """Every one of the 146,880 minimal vectors, class by class.

    The classes are the three resolutions: a vector may be visible at the fine
    level only (``(+-4, 0^31)``), at the middle level (``(+-2^4, 0^28)`` on a
    weight-4 inner codeword) or at the coarse level (``(+-1^16, 0^16)`` on a
    weight-16 outer codeword, with the negative positions an inner codeword).
    """
    zero = [0] * DIM
    for i in range(DIM):
        for sign in (4, -4):
            vector = list(zero)
            vector[i] = sign
            yield tuple(vector)
    for support in combinations(range(DIM), 4):
        if not in_inner(_mask_of(support)):
            continue
        for signs in range(16):
            vector = list(zero)
            for k, position in enumerate(support):
                vector[position] = 2 if (signs >> k) & 1 else -2
            yield tuple(vector)
    for word in outer_code():
        if weight(word) != 16:
            continue
        positions = [i for i in range(DIM) if (word >> i) & 1]
        for negatives in supported_subcode(word):
            vector = list(zero)
            for position in positions:
                vector[position] = -1 if (negatives >> position) & 1 else 1
            yield tuple(vector)


@lru_cache(maxsize=None)
def minimal_shape_census(verify: bool = False) -> Dict[str, object]:
    """Count the minimal vectors by shape, optionally verifying every one.

    With ``verify=True`` each vector is put through :func:`in_lattice` and its
    squared length is checked to be 16 -- 146,880 membership tests, which takes
    a few seconds.  With ``verify=False`` a sample of each class is checked.
    """
    counts: Dict[str, int] = {}
    seen = set()
    checked = 0
    for vector in minimal_vectors():
        shape = "(+-%d^%d, 0^%d)" % (
            max(abs(value) for value in vector),
            sum(1 for value in vector if value),
            sum(1 for value in vector if not value))
        counts[shape] = counts.get(shape, 0) + 1
        seen.add(vector)
        if verify or counts[shape] <= 3:
            assert norm2(vector) == MIN_NORM2, vector
            assert in_lattice(vector), vector
            checked += 1
    return {
        "counts": dict(sorted(counts.items())),
        "total": sum(counts.values()),
        "distinct": len(seen),
        "checked": checked,
        "verified_all": bool(verify),
    }


def kissing_number() -> int:
    """The number of minimal vectors, by enumeration."""
    return sum(1 for _ in minimal_vectors())


# ---------------------------------------------------------------------------
# Even, unimodular
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def generator_matrix() -> Tuple[Tuple[int, ...], ...]:
    """A 32 x 32 integer basis of the unscaled lattice.

    Built as the Hermite normal form of the natural generating set: the six
    outer codewords, twice the twenty-six inner codewords, and ``4 e_i``.
    """
    rows: List[List[int]] = []
    for word in outer_basis():
        rows.append([(word >> i) & 1 for i in range(DIM)])
    for word in inner_basis():
        rows.append([2 * ((word >> i) & 1) for i in range(DIM)])
    for i in range(DIM):
        row = [0] * DIM
        row[i] = 4
        rows.append(row)
    basis = hermite_normal_form(rows, DIM)
    return tuple(tuple(row) for row in basis)


@lru_cache(maxsize=None)
def determinant_report() -> Dict[str, object]:
    """The determinant, unscaled and scaled, and the evenness check.

    The Gram determinant of the unscaled lattice is ``2^64``; dividing every
    vector by 2 divides the Gram determinant by ``2^64``, so the true lattice
    is **unimodular**.  Evenness is checked on the basis: every basis vector
    has ``8 | |x|^2`` and every pair has ``4 | <x, y>``, which makes the scaled
    Gram matrix integral with even diagonal.
    """
    basis = generator_matrix()
    detb = det_int([list(row) for row in basis])
    gram_det = detb * detb
    diagonal = [norm2(row) for row in basis]
    products = [sum(a * b for a, b in zip(basis[i], basis[j]))
                for i in range(DIM) for j in range(i + 1, DIM)]
    return {
        "basis_determinant": detb,
        "gram_determinant": gram_det,
        "gram_determinant_is_2_to_64": gram_det == 2 ** 64,
        "scaled_determinant": Fraction(gram_det, 2 ** (2 * DIM)),
        "unimodular": Fraction(gram_det, 2 ** (2 * DIM)) == 1,
        "diagonal_divisible_by_8": all(value % 8 == 0 for value in diagonal),
        "products_divisible_by_4": all(value % 4 == 0 for value in products),
        "even": (all(value % 8 == 0 for value in diagonal)
                 and all(value % 4 == 0 for value in products)),
        "minimum_over_basis": min(diagonal),
    }


@lru_cache(maxsize=None)
def minimum_certificate() -> Dict[str, object]:
    """The three-case argument for minimum 4, with its inputs recomputed.

    Each case is closed by one property of one code, and this returns the
    property together with the bound it forces.  The machine-checked statement
    is ``GLM.HigherLattices.BarnesWall.norm_ge_of_ne_zero``.
    """
    codes = code_report()
    return {
        "cases": [
            {"case": "c != 0 (visible at the coarse resolution)",
             "reason": "a coordinate with c_i = 1 is odd, so contributes >= 1",
             "code_input": "outer minimum weight %d"
                           % codes["outer"]["minimum_weight"],
             "bound": codes["outer"]["minimum_weight"]},
            {"case": "c = 0, b != 0 (visible at the middle resolution)",
             "reason": "a coordinate with b_i = 1 is 2 (mod 4), so "
                       "contributes >= 4",
             "code_input": "inner minimum weight %s"
                           % codes["inner"]["minimum_weight"],
             "bound": 4 * (codes["inner"]["minimum_weight"] or 0)},
            {"case": "c = 0, b = 0, a != 0 (fine resolution only)",
             "reason": "a nonzero coordinate is a nonzero multiple of 4",
             "code_input": "none",
             "bound": 16},
        ],
        "minimum_norm2": MIN_NORM2,
        "lattice_minimum": Fraction(MIN_NORM2, SCALE * SCALE),
        "extremal_minimum_in_dimension_32": 4,
        "is_extremal": Fraction(MIN_NORM2, SCALE * SCALE) == 4,
        "theorem": "GLM.HigherLattices.BarnesWall.norm_ge_of_ne_zero",
    }


@lru_cache(maxsize=None)
def lattice32_report(verify_all: bool = False) -> Dict[str, object]:
    """Everything this module establishes, recomputed on demand."""
    census = minimal_shape_census(verify_all)
    return {
        "dimension": DIM,
        "codes": code_report(),
        "minimum": minimum_certificate(),
        "determinant": determinant_report(),
        "kissing": {"census": census, "expected": KISSING,
                    "agrees": census["total"] == KISSING
                    and census["distinct"] == KISSING},
        "addressing": index_ladder(),
    }
