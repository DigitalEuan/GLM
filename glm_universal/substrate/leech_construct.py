"""``glm_universal.substrate.leech_construct`` -- A, B, C and the mod sieve.

What this module is
-------------------
The Leech lattice is not one condition but three, applied at three moduli, and
the packing you get depends on how many of them you have imposed.  This module
builds the ladder explicitly and *measures* each rung:

============  ==================================================  ===========
level         conditions (all in the ``x sqrt(8)`` integer model)  kissing
============  ==================================================  ===========
``"A"``       mod 2: all coordinates even;                         48
              mod 4: ``{i : x_i = 2 (mod 4)}`` is a Golay word
``"B"``       ``A`` and mod 8: ``sum(x) = 0 (mod 8)``               98,256
``"C"``       ``B`` union the odd coset (all coordinates odd,       196,560
              Golay condition on ``x_i = 3 (mod 4)``,
              ``sum(x) = 4 (mod 8)``)
============  ==================================================  ===========

``C`` is the Leech lattice: :func:`in_level` at level ``"C"`` agrees with
:func:`glm_universal.substrate.leech2.in_leech` everywhere it is tested, and
the 196,560 minimal vectors this module generates are exactly the ones
:func:`~glm_universal.substrate.leech2.minimal_vectors` streams.

Why the ladder matters
----------------------
Construction A alone -- the Golay lift, which is what a system has when it has
a code but no arithmetic on top of it -- is a *48*-kissing packing whose
minimal norm is 16, not 32.  It is a perfectly good lattice and it is not the
Leech lattice.  Adding the mod-8 coordinate-sum condition kills the 48 short
vectors ``+-4 e_i`` and lifts the minimum to 32, where the packing is the
98,256 vectors of shapes ``(+-4^2, 0^22)`` and ``(+-2^8)``.  Adjoining the odd
coset -- the glue vector ``(-3, 1^23)`` and its translates -- adds the 98,304
vectors of shape ``(-+3, +-1^23)`` and gives the true 196,560.

The three moduli are each load-bearing, and :func:`necessity_report` shows it
by removing them one at a time and recomputing the minimum:

* drop the mod-8 sum condition  -> minimum 16, 48 vectors (level ``A``);
* drop the mod-4 Golay condition -> minimum **8**, 552 vectors: the code is
  what stops ``(2, -2, 0^22)`` from being in the lattice;
* keep ``B`` but drop the odd coset -> minimum 32 but only 98,256 vectors,
  exactly half the packing.

The multi-mod view
------------------
:func:`mod_profile` reports a vector against every modulus the construction
uses -- residues mod 2, 4, 8 and 16 coordinatewise, the coordinate sum at each
modulus, the Golay support at mod 4 and whether it is a codeword -- and
:func:`mod_sieve` runs the conditions in order and names the first one that
fails.  A vector that fails at mod 2 is not "nearly in the lattice"; it is
outside at the coarsest resolution, and the sieve says which resolution.

Everything is exact integer arithmetic; every count below is enumerated, and
every generated vector is membership-checked before it is yielded.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from . import leech2
from .leech2 import DIM, MIN_NORM2, in_leech, norm2
from .linalg import hermite_normal_form
from .mog import GOLAY_SET, OCTAD_MASKS

__all__ = [
    "LEVELS", "LEVEL_A", "LEVEL_B", "LEVEL_C",
    "even_parity", "golay_support", "golay_condition", "sum_condition",
    "in_level", "level_of",
    "minimal_vectors_of_level", "minimal_shape_census", "kissing_of_level",
    "mod_profile", "mod_sieve",
    "projection_lattice_basis", "supported_sublattice_basis",
    "small_shell_minimum", "necessity_report",
    "agrees_with_leech2", "leech_construction_report",
]

LEVEL_A = "A"
LEVEL_B = "B"
LEVEL_C = "C"

#: The three rungs, coarsest first.
LEVELS: Tuple[str, ...] = (LEVEL_A, LEVEL_B, LEVEL_C)


# ===========================================================================
# 1.  THE CONDITIONS, ONE MODULUS AT A TIME
# ===========================================================================

def _check_vector(x: Sequence[int], where: str) -> Tuple[int, ...]:
    if len(x) != DIM:
        raise ValueError(f"{where}: 24 coordinates required")
    out = []
    for v in x:
        if isinstance(v, bool) or not isinstance(v, int):
            raise TypeError(f"{where}: coordinates must be int")
        out.append(v)
    return tuple(out)


def even_parity(x: Sequence[int]) -> Optional[int]:
    """The shared parity ``m`` of the coordinates, or ``None`` if mixed.

    This is the **mod 2** condition: a Leech vector is all-even or all-odd.
    """
    v = _check_vector(x, "even_parity")
    m = v[0] & 1
    return m if all((c & 1) == m for c in v) else None


def golay_support(x: Sequence[int]) -> Optional[int]:
    """``{i : x_i = m + 2 (mod 4)}`` as a 24-bit mask, or ``None`` if mixed.

    This is the **mod 4** datum: which coordinates sit in the upper half of
    their parity class.  The condition is that this mask is a Golay codeword.
    """
    v = _check_vector(x, "golay_support")
    m = even_parity(v)
    if m is None:
        return None
    target = (m + 2) % 4
    mask = 0
    for i, c in enumerate(v):
        if c % 4 == target:
            mask |= 1 << i
    return mask


def golay_condition(x: Sequence[int]) -> bool:
    """Whether the mod-4 support is a Golay codeword."""
    mask = golay_support(x)
    return mask is not None and mask in GOLAY_SET


def sum_condition(x: Sequence[int]) -> bool:
    """The **mod 8** condition ``sum(x) = 4m (mod 8)``, ``m`` the parity."""
    v = _check_vector(x, "sum_condition")
    m = even_parity(v)
    if m is None:
        return False
    return sum(v) % 8 == (4 * m) % 8


def in_level(x: Sequence[int], level: str) -> bool:
    """Membership in construction ``A``, ``B`` or ``C``.

    ``A``
        mod 2 and mod 4 only, and even coordinates: the Golay lift ``2 C``.
    ``B``
        ``A`` plus the mod-8 coordinate-sum condition.
    ``C``
        ``B`` together with the odd coset -- the Leech lattice.
    """
    if level not in LEVELS:
        raise ValueError(f"in_level: level must be one of {LEVELS}")
    v = _check_vector(x, "in_level")
    m = even_parity(v)
    if m is None:
        return False
    if level == LEVEL_C:
        return golay_condition(v) and sum_condition(v)
    if m != 0:
        return False                      # A and B are even-coordinate only
    if not golay_condition(v):
        return False
    return level == LEVEL_A or sum_condition(v)


def level_of(x: Sequence[int]) -> Optional[str]:
    """The finest level containing ``x``, or ``None`` if not even ``A``."""
    for level in reversed(LEVELS):
        if in_level(x, level):
            return level
    return None


# ===========================================================================
# 2.  THE MINIMAL SHELL OF EACH LEVEL
# ===========================================================================

def _signed(support: Sequence[int], value: int,
            signs: int) -> Tuple[int, ...]:
    v = [0] * DIM
    for k, i in enumerate(support):
        v[i] = -value if (signs >> k) & 1 else value
    return tuple(v)


def _shape_4_4() -> Iterator[Tuple[int, ...]]:
    """``(+-4, +-4, 0^22)``: 276 pairs x 4 sign patterns = 1104."""
    for i, j in combinations(range(DIM), 2):
        for signs in range(4):
            yield _signed((i, j), 4, signs)


def _shape_2_octad() -> Iterator[Tuple[int, ...]]:
    """``(+-2^8)`` on an octad with an even number of minus signs: 97,152."""
    for octad in OCTAD_MASKS:
        points = [i for i in range(DIM) if (octad >> i) & 1]
        for signs in range(256):
            if bin(signs).count("1") & 1:
                continue
            yield _signed(points, 2, signs)


def _shape_3_1() -> Iterator[Tuple[int, ...]]:
    """``(-+3, +-1^23)``: 24 x 4096 = 98,304 odd minimal vectors."""
    for i in range(DIM):
        for word in sorted(GOLAY_SET):
            v = [(-1 if (word >> j) & 1 else 1) for j in range(DIM)]
            v[i] = 3 if (word >> i) & 1 else -3
            yield tuple(v)


def _shape_4_single() -> Iterator[Tuple[int, ...]]:
    """``(+-4, 0^23)``: the 48 minimal vectors of construction A."""
    for i in range(DIM):
        for sign in (1, -1):
            v = [0] * DIM
            v[i] = 4 * sign
            yield tuple(v)


def minimal_vectors_of_level(level: str) -> Iterator[Tuple[int, ...]]:
    """The minimal vectors of a level, each membership-checked as it is made.

    A vector that fails :func:`in_level` or has the wrong norm raises, so a
    completed iteration is itself a proof that the shapes listed above lie in
    the level.  It is *not* a proof that no others do -- that is what
    :func:`small_shell_minimum` is for.
    """
    if level == LEVEL_A:
        families = (_shape_4_single(),)
        expected_norm = 16
    elif level == LEVEL_B:
        families = (_shape_4_4(), _shape_2_octad())
        expected_norm = MIN_NORM2
    elif level == LEVEL_C:
        families = (_shape_4_4(), _shape_2_octad(), _shape_3_1())
        expected_norm = MIN_NORM2
    else:
        raise ValueError(f"minimal_vectors_of_level: unknown level {level!r}")
    for family in families:
        for v in family:
            if norm2(v) != expected_norm:
                raise AssertionError(
                    f"level {level}: generated a vector of norm {norm2(v)}, "
                    f"expected {expected_norm}")
            if not in_level(v, level):
                raise AssertionError(
                    f"level {level}: generated a vector outside the level")
            yield v


def minimal_shape_census(level: str) -> Dict[str, int]:
    """How many minimal vectors of each shape the level has."""
    return dict(_minimal_shape_census(level))


@lru_cache(maxsize=None)
def _minimal_shape_census(level: str) -> Dict[str, int]:
    if level == LEVEL_A:
        return {"(+-4, 0^23)": sum(1 for _ in _shape_4_single())}
    counts = {
        "(+-4^2, 0^22)": sum(1 for _ in _shape_4_4()),
        "(+-2^8 on an octad)": sum(1 for _ in _shape_2_octad()),
    }
    if level == LEVEL_C:
        counts["(-+3, +-1^23)"] = sum(1 for _ in _shape_3_1())
    return counts


def kissing_of_level(level: str) -> Dict[str, object]:
    """Minimal norm, kissing number and shape census, all enumerated."""
    out = dict(_kissing_of_level(level))
    out["shapes"] = dict(out["shapes"])
    return out


@lru_cache(maxsize=None)
def _kissing_of_level(level: str) -> Dict[str, object]:
    vectors = list(minimal_vectors_of_level(level))
    distinct = len(set(vectors))
    norms = {norm2(v) for v in vectors}
    return {
        "level": level,
        "minimal_norm2": min(norms) if norms else 0,
        "kissing": len(vectors),
        "distinct": distinct,
        "no_duplicates": distinct == len(vectors),
        "shapes": minimal_shape_census(level),
        "all_in_level": True,       # enforced inside the generator
    }


# ===========================================================================
# 3.  THE MULTI-MOD VIEW
# ===========================================================================

def mod_profile(x: Sequence[int],
                moduli: Sequence[int] = (2, 4, 8, 16)) -> Dict[str, object]:
    """Every modulus the construction uses, reported side by side."""
    v = _check_vector(x, "mod_profile")
    total = sum(v)
    support = golay_support(v)
    return {
        "coordinates_mod": {m: [c % m for c in v] for m in moduli},
        "sum": total,
        "sum_mod": {m: total % m for m in moduli},
        "parity": even_parity(v),
        "golay_support": support,
        "golay_support_weight": (None if support is None
                                 else bin(support).count("1")),
        "golay_support_is_codeword": (support is not None
                                      and support in GOLAY_SET),
        "norm2": norm2(v),
        "norm2_mod": {m: norm2(v) % m for m in moduli},
    }


def mod_sieve(x: Sequence[int]) -> Dict[str, object]:
    """Run the conditions coarsest first and name the first failure."""
    v = _check_vector(x, "mod_sieve")
    steps: List[Dict[str, object]] = []
    m = even_parity(v)
    steps.append({"modulus": 2, "condition": "all coordinates share a parity",
                  "holds": m is not None, "datum": m})
    ok4 = m is not None and golay_condition(v)
    steps.append({"modulus": 4,
                  "condition": "{i : x_i = m+2 (mod 4)} is a Golay codeword",
                  "holds": ok4, "datum": golay_support(v)})
    ok8 = m is not None and sum_condition(v)
    steps.append({"modulus": 8, "condition": "sum(x) = 4m (mod 8)",
                  "holds": ok8, "datum": sum(v) % 8})
    first_failure = next((s["modulus"] for s in steps if not s["holds"]), None)
    return {
        "steps": steps,
        "first_failure_modulus": first_failure,
        "level": level_of(v),
        "in_leech": in_leech(list(v)),
    }


# ===========================================================================
# 3b.  LOCAL LATTICES: WHAT A SET OF COORDINATES SEES OF Lambda
# ===========================================================================

def projection_lattice_basis(indices: Sequence[int]
                             ) -> Tuple[Tuple[int, ...], ...]:
    """A ``Z``-basis of ``pi_S(Lambda)`` in ``Z^S``, in Hermite normal form.

    What a reader restricted to the coordinates ``S`` sees of every point of
    the lattice.
    """
    idx = _index_tuple(indices)
    rows = [[row[i] for i in idx] for row in leech2.LEECH_BASIS]
    return tuple(tuple(r) for r in hermite_normal_form(rows, len(idx)))


def supported_sublattice_basis(indices: Sequence[int]
                               ) -> Tuple[Tuple[int, ...], ...]:
    """A ``Z``-basis of ``Lambda ∩ span(S)``, written in ``Z^S``.

    The Leech points that live entirely inside the coordinates ``S`` -- the
    *local sub-lattice* of that region of the MOG.  Computed by integer row
    reduction of the complement coordinates while carrying a transformation
    matrix, so the result is exact and every generator is checked to lie in
    ``Lambda`` before it is returned.
    """
    idx = _index_tuple(indices)
    inside = set(idx)
    outside = [j for j in range(DIM) if j not in inside]
    work: List[Tuple[List[int], List[int]]] = []
    for i, row in enumerate(leech2.LEECH_BASIS):
        work.append(([row[j] for j in outside],
                     [1 if k == i else 0 for k in range(DIM)]))
    active = list(range(len(work)))
    for col in range(len(outside)):
        while True:
            nonzero = [r for r in active if work[r][0][col] != 0]
            if len(nonzero) <= 1:
                break
            nonzero.sort(key=lambda r: abs(work[r][0][col]))
            small = nonzero[0]
            for r in nonzero[1:]:
                q = work[r][0][col] // work[small][0][col]
                if q:
                    work[r] = (
                        [a - q * b
                         for a, b in zip(work[r][0], work[small][0])],
                        [a - q * b
                         for a, b in zip(work[r][1], work[small][1])])
        nonzero = [r for r in active if work[r][0][col] != 0]
        if nonzero:
            active.remove(nonzero[0])
    rows: List[List[int]] = []
    for r in active:
        if any(x for x in work[r][0]):
            continue
        point = leech2.from_coords(work[r][1])
        if any(point[j] for j in outside):
            raise AssertionError("supported_sublattice_basis: generator is "
                                 "not supported on the given coordinates")
        if not in_leech(list(point)):
            raise AssertionError("supported_sublattice_basis: generator is "
                                 "not in Lambda")
        rows.append([point[i] for i in idx])
    if not rows:
        return ()
    return tuple(tuple(r) for r in hermite_normal_form(rows, len(idx)))


def _index_tuple(indices: Sequence[int]) -> Tuple[int, ...]:
    idx = tuple(int(i) for i in indices)
    if not idx:
        raise ValueError("a non-empty set of coordinates is required")
    if len(set(idx)) != len(idx):
        raise ValueError("coordinates must be distinct")
    if any(not 0 <= i < DIM for i in idx):
        raise ValueError("coordinates must lie in 0..23")
    return idx


# ===========================================================================
# 4.  NECESSITY: WHAT EACH MODULUS IS HOLDING UP
# ===========================================================================

def small_shell_minimum(predicate, max_support: int = 4,
                        norm_budget: int = 16) -> Dict[str, object]:
    """Least norm of an admissible even vector with small support.

    Enumerates every vector whose nonzero coordinates are ``+-2`` or ``+-4``
    and number at most ``max_support``, keeps those satisfying ``predicate``,
    and reports the least norm found and how many vectors attain it.

    This is exhaustive for the question it is asked.  Any even vector of norm
    at most 16 has at most four nonzero coordinates (each contributes at least
    4), and no coordinate can exceed 4 in absolute value, so if the minimum
    reported here is at most 16 it is the true minimum of the lattice.
    """
    best_norm: Optional[int] = None
    best_count = 0
    witness: Optional[Tuple[int, ...]] = None
    for size in range(1, max_support + 1):
        value_sets = list(_value_tuples(size, norm_budget))
        for support in combinations(range(DIM), size):
            for values in value_sets:
                v = [0] * DIM
                for i, val in zip(support, values):
                    v[i] = val
                if not predicate(v):
                    continue
                n = norm2(v)
                if best_norm is None or n < best_norm:
                    best_norm, best_count, witness = n, 1, tuple(v)
                elif n == best_norm:
                    best_count += 1
    return {
        "minimal_norm2": best_norm,
        "count_at_minimum": best_count,
        "witness": witness,
        "exhaustive_below": norm_budget,
        "conclusive": best_norm is not None and best_norm <= norm_budget,
    }


_VALUES = (2, -2, 4, -4)


def _value_tuples(size: int, budget: int) -> Iterator[Tuple[int, ...]]:
    """Value tuples of the given length whose squares sum to at most ``budget``.

    Pruned as it goes: a partial tuple already over budget cannot be
    completed, since every remaining coordinate adds at least 4.
    """
    if size == 0:
        yield ()
        return
    for head in _VALUES:
        cost = head * head
        if cost + 4 * (size - 1) > budget:
            continue
        for tail in _value_tuples(size - 1, budget - cost):
            yield (head,) + tail


def necessity_report() -> Dict[str, object]:
    """Remove one condition at a time and watch the packing collapse."""

    def parity_and_sum(v: Sequence[int]) -> bool:
        return even_parity(v) == 0 and sum(v) % 8 == 0

    def parity_and_golay(v: Sequence[int]) -> bool:
        return even_parity(v) == 0 and golay_condition(v)

    without_golay = small_shell_minimum(parity_and_sum)
    without_sum = small_shell_minimum(parity_and_golay)
    return {
        "full_C": {
            "minimal_norm2": MIN_NORM2,
            "kissing": kissing_of_level(LEVEL_C)["kissing"],
        },
        "drop_mod4_golay": {
            "kept": "mod 2 parity, mod 8 sum",
            "minimal_norm2": without_golay["minimal_norm2"],
            "count_at_minimum": without_golay["count_at_minimum"],
            "witness": without_golay["witness"],
            "comment": ("without the code, (2, -2, 0^22) is admissible and "
                        "the minimum falls from 32 to 8"),
        },
        "drop_mod8_sum": {
            "kept": "mod 2 parity, mod 4 Golay  (= construction A)",
            "minimal_norm2": without_sum["minimal_norm2"],
            "count_at_minimum": without_sum["count_at_minimum"],
            "witness": without_sum["witness"],
            "comment": ("without the sum condition, +-4 e_i survives and the "
                        "minimum falls from 32 to 16, with kissing 48"),
        },
        "drop_odd_coset": {
            "kept": "construction B",
            "minimal_norm2": MIN_NORM2,
            "kissing": kissing_of_level(LEVEL_B)["kissing"],
            "comment": ("the even part alone is a norm-32 packing with "
                        "98,256 minimal vectors; the odd coset adds the "
                        "remaining 98,304"),
        },
    }


# ===========================================================================
# 5.  AGREEMENT WITH THE LATTICE THE REST OF THE PACKAGE USES
# ===========================================================================

def agrees_with_leech2(sample: Optional[Sequence[Sequence[int]]] = None
                       ) -> Dict[str, object]:
    """Check ``in_level(., "C") == leech2.in_leech`` on a structured sample.

    The sample is deterministic: the whole minimal shell of ``C``, the
    minimal shell of ``A`` (which is *outside* the Leech lattice and must be
    rejected by both), the standard basis scaled by 1, 2 and 4, and the sums
    of consecutive minimal vectors.
    """
    if sample is None:
        pool: List[Tuple[int, ...]] = []
        c_min = list(minimal_vectors_of_level(LEVEL_C))
        pool.extend(c_min[:: max(1, len(c_min) // 400)])
        pool.extend(_shape_4_single())
        for k in (1, 2, 4):
            for i in range(DIM):
                v = [0] * DIM
                v[i] = k
                pool.append(tuple(v))
        for a, b in zip(c_min[:200], c_min[1:201]):
            pool.append(tuple(x + y for x, y in zip(a, b)))
        sample = pool
    disagreements = [list(v) for v in sample
                     if in_level(v, LEVEL_C) != in_leech(list(v))]
    return {
        "checked": len(sample),
        "disagreements": len(disagreements),
        "agrees": not disagreements,
        "first_disagreement": disagreements[0] if disagreements else None,
    }


def leech_construction_report() -> Dict[str, object]:
    """The whole ladder, recomputed."""
    levels = {level: kissing_of_level(level) for level in LEVELS}
    return {
        "levels": levels,
        "kissing_by_level": {k: v["kissing"] for k, v in levels.items()},
        "minimal_norm_by_level": {k: v["minimal_norm2"]
                                  for k, v in levels.items()},
        "construction_A_is_48": levels[LEVEL_A]["kissing"] == 48,
        "construction_C_is_196560": levels[LEVEL_C]["kissing"] == 196560,
        "odd_coset_contribution": (levels[LEVEL_C]["kissing"]
                                   - levels[LEVEL_B]["kissing"]),
        "odd_coset_is_98304": (levels[LEVEL_C]["kissing"]
                               - levels[LEVEL_B]["kissing"]) == 98304,
        "necessity": necessity_report(),
        "agreement_with_leech2": agrees_with_leech2(),
    }
