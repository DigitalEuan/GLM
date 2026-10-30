"""``glm_universal.reasoning.deep_dive`` -- the two questions the audit left open.

What this module is
-------------------
:mod:`glm_universal.reasoning.salvage` retrieved eleven results from the
supplied archive and closed each of them.  Two questions it raised were left
open, and this module is the deep dive into them.  Each result here is also a
theorem of ``RequestProject/GLM/TriadChance.lean`` or
``RequestProject/GLM/Relaxation.lean``, which are the specification (D8).

**1.  Is the archive's "44 balanced octads" a property of the code, or of
chance?**  The archive counted 44 of the 759 octads whose three eight-bit
blocks are pairwise at Hamming distance four, and read the count as structure.
:func:`chance_census` walks *all* 735,471 eight-subsets of the 24 coordinates --
the null distribution, which knows nothing about the code -- and finds 37,800
of them balanced, so chance alone predicts ``759 * 37800 / 735471 = 12600/323``,
just over **39**.  The observed 44 exceeds that by ``1612/323``, under five
octads.  Worse, balance is not even an invariant of the labelling:
:func:`transposition_range` relabels by each of the 276 transpositions of the
coordinates and finds the count ranging over **27 to 63**, with the identity's
44 attained by 21 of them.  The measure is near-blind, and the 44 is a
coincidence of the coordinate order rather than a fact about the code.

**2.  Is the archive's "relaxation" a decoder?**  ``LDP.lean`` proved that
every excited word descends and reaches the code.  It does not follow that it
reaches the *nearest* codeword, and it does not:
:func:`trapped_census` finds **792 of the 4,096 cosets** where the fastest
strictly-descending path is longer than the coset leader -- 66 cosets whose
leader has weight 2 need six steps, and 726 of weight 3 need five.  The 66 are
exactly the pairs of message-half coordinates
(``worst_case_is_the_message_pairs``).  Descent is a relaxation, not a decoder.

Around those two the module also carries the descent arithmetic the Lean files
prove: the drop identity, the best-drop census, the fastest and greedy descent
censuses, and the energy bound, which is tight
(:func:`longest_path_census`: the longest strictly-descending path from a
syndrome is exactly its weight).

Everything is exact ``int`` / ``Fraction`` arithmetic (D7).
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Tuple

from ..derived import memo
from ..substrate import mog
from ..substrate.linalg import popcount
from . import salvage as slv

__all__ = [
    "chance_census", "chance_expected_balanced", "observed_census",
    "deviation", "block_deviation", "deviation_eight_octads",
    "transposition_range", "swap_witness",
    "column_weights", "syndrome_columns",
    "best_drop_census", "fastest_descent_census", "greedy_descent_census",
    "longest_path_census", "leader_census", "trapped_census",
    "deep_dive_report",
]


# ===========================================================================
# 0.  THE SUBSTRATE
# ===========================================================================

@memo
def _code() -> mog.GolayCode:
    return mog.GolayCode()


def syndrome_columns() -> Tuple[int, ...]:
    """The 24 columns of ``H``: the syndrome of a single flipped coordinate."""
    return _syndrome_columns()


@memo
def _syndrome_columns() -> Tuple[int, ...]:
    code = _code()
    return tuple(code.syndrome_int(1 << k) for k in range(24))


def column_weights() -> Tuple[int, ...]:
    """The Hamming weights of those columns.

    Every one is odd (``Golay24.colWt_odd``) and none exceeds eleven
    (``colWt_le_eleven``): twelve unit columns, eleven of weight seven, and the
    first row of ``B``, of weight eleven.
    """
    return tuple(popcount(column) for column in syndrome_columns())


# ===========================================================================
# 1.  BALANCE: THE CODE, OR CHANCE?
# ===========================================================================

def deviation(mask: int) -> int:
    """``Triad.axisDev`` of a 24-bit word: how far its blocks are from 4-4-4."""
    return slv.axis_deviation(mask)


@memo
def chance_census() -> Dict[int, int]:
    """The deviation census of *every* eight-subset of the 24 coordinates.

    The null distribution: 735,471 subsets, no code anywhere in sight.
    """
    census: Dict[int, int] = {}
    for cells in combinations(range(24), 8):
        mask = 0
        for cell in cells:
            mask |= 1 << cell
        value = deviation(mask)
        census[value] = census.get(value, 0) + 1
    return dict(sorted(census.items()))


def chance_expected_balanced() -> Fraction:
    """How many balanced octads chance alone predicts among 759 draws."""
    census = chance_census()
    return Fraction(759 * census[0], sum(census.values()))


def observed_census() -> Dict[int, int]:
    """The deviation census the code actually gives, over its 759 octads."""
    return dict(slv.triad_report()["deviation_census"])  # type: ignore[arg-type]


def block_deviation() -> Tuple[int, int, int]:
    """The deviation of each of the three all-ones blocks.

    Each sits at 12, the largest value the measure can take, and no octad
    reaches it: the extreme of the score is a word the code does not contain.
    """
    return tuple(deviation(0xFF << (8 * t)) for t in range(3))  # type: ignore


@memo
def deviation_eight_octads() -> Tuple[Dict[str, object], ...]:
    """The nine octads at the extreme of the observed census.

    They are not a family: six different block splits and seven different
    distance triples between them.
    """
    rows: List[Dict[str, object]] = []
    for mask in _code().octad_masks:
        if deviation(mask) != 8:
            continue
        rows.append({
            "cells": tuple(k for k in range(24) if (mask >> k) & 1),
            "block_split": tuple(popcount((mask >> (8 * t)) & 0xFF)
                                 for t in range(3)),
            "distances": slv.axis_distances(mask),
        })
    return tuple(rows)


def _transpose(mask: int, i: int, j: int) -> int:
    """The word with coordinates ``i`` and ``j`` exchanged."""
    if ((mask >> i) & 1) == ((mask >> j) & 1):
        return mask
    return mask ^ (1 << i) ^ (1 << j)


@memo
def transposition_range() -> Dict[str, object]:
    """Relabel by every transposition and count the balanced octads again."""
    octads = _code().octad_masks
    counts: List[int] = []
    for i, j in combinations(range(24), 2):
        counts.append(sum(1 for mask in octads
                          if deviation(_transpose(mask, i, j)) == 0))
    identity = sum(1 for mask in octads if deviation(mask) == 0)
    return {
        "transpositions": len(counts),
        "identity_value": identity,
        "minimum": min(counts),
        "maximum": max(counts),
        "mean": Fraction(sum(counts), len(counts)),
        "transpositions_giving_the_identity_value":
            sum(1 for c in counts if c == identity),
        "balance_is_not_invariant": min(counts) != max(counts),
    }


def swap_witness(i: int, j: int) -> Dict[str, object]:
    """One relabelling, in full: what swapping two coordinates does.

    ``Triad.balanced_after_swap`` and ``deviation_ten_after_swap``: swapping
    coordinates 0 and 8 raises the balanced count from 44 to 49 and creates a
    deviation-ten octad where the identity labelling has none.
    """
    octads = _code().octad_masks
    before = [deviation(mask) for mask in octads]
    after = [deviation(_transpose(mask, i, j)) for mask in octads]
    return {
        "swap": (i, j),
        "balanced_before": sum(1 for d in before if d == 0),
        "balanced_after": sum(1 for d in after if d == 0),
        "deviation_ten_before": sum(1 for d in before if d == 10),
        "deviation_ten_after": sum(1 for d in after if d == 10),
        "balance_is_not_invariant":
            sum(1 for d in before if d == 0) != sum(1 for d in after if d == 0),
    }


# ===========================================================================
# 2.  DESCENT: HOW FAR ONE FLIP GOES
# ===========================================================================

@memo
def best_drop_census() -> Dict[int, int]:
    """For each excited coset, the largest drop a single flip can achieve.

    The drop identity behind it -- ``wt s - wt (s ^ c) = 2 |s & c| - |c|`` --
    is why every drop is odd: every column weight is odd.
    """
    columns = syndrome_columns()
    census: Dict[int, int] = {}
    for syndrome in range(1, 1 << 12):
        weight = popcount(syndrome)
        best = max(weight - popcount(syndrome ^ column) for column in columns)
        census[best] = census.get(best, 0) + 1
    return dict(sorted(census.items()))


@memo
def _fastest_steps() -> Tuple[int, ...]:
    """The fewest strictly-descending flips that clear each syndrome."""
    columns = syndrome_columns()
    steps = [0] * (1 << 12)
    for syndrome in sorted(range(1 << 12), key=popcount):
        if syndrome == 0:
            continue
        weight = popcount(syndrome)
        best = 1 << 20
        for column in columns:
            lower = syndrome ^ column
            if popcount(lower) < weight:
                best = min(best, steps[lower] + 1)
        steps[syndrome] = best
    return tuple(steps)


def fastest_descent_census() -> Dict[str, object]:
    """The census of those step counts, and the bounds it gives."""
    steps = _fastest_steps()
    census: Dict[int, int] = {}
    for value in steps:
        census[value] = census.get(value, 0) + 1
    census = dict(sorted(census.items()))
    return {
        "census": census,
        "within_four": sum(v for k, v in census.items() if k <= 4),
        "within_five": sum(v for k, v in census.items() if k <= 5),
        "within_six": sum(v for k, v in census.items() if k <= 6),
        "mean_steps": Fraction(sum(steps), len(steps)),
        "worst_case": max(census),
    }


@memo
def _greedy_totals() -> Dict[bool, int]:
    columns = syndrome_columns()
    totals: Dict[bool, int] = {}
    for prefer_last in (False, True):
        order = range(23, -1, -1) if prefer_last else range(24)
        total = 0
        for syndrome in range(1 << 12):
            current = syndrome
            while current:
                weight = popcount(current)
                best = -1
                pick = 0
                for k in order:
                    drop = weight - popcount(current ^ columns[k])
                    if drop > best:
                        best = drop
                        pick = k
                current ^= columns[pick]
                total += 1
        totals[prefer_last] = total
    return totals


def greedy_descent_census(prefer_last: bool = False) -> Dict[str, object]:
    """What the greedy rule costs: always take the largest available drop.

    The tie-break is a convention, and it is not free: breaking ties towards
    the last column costs 132 more steps over the 4,096 cosets than breaking
    them towards the first, and both are worse than the fastest descent.
    """
    totals = _greedy_totals()
    total = totals[bool(prefer_last)]
    return {
        "prefer_last": bool(prefer_last),
        "total_steps": total,
        "mean_steps": Fraction(total, 1 << 12),
        "fastest_total_steps": sum(_fastest_steps()),
        "greedy_is_not_optimal": total > sum(_fastest_steps()),
    }


@memo
def longest_path_census() -> Dict[str, object]:
    """The longest strictly-descending path from each syndrome.

    It is exactly the syndrome's weight -- the energy bound of ``LDP.lean`` is
    tight, and the unit columns are what attain it.
    """
    columns = syndrome_columns()
    longest = [0] * (1 << 12)
    for syndrome in sorted(range(1 << 12), key=popcount):
        if syndrome == 0:
            continue
        weight = popcount(syndrome)
        best = 0
        for column in columns:
            lower = syndrome ^ column
            if popcount(lower) < weight:
                best = max(best, longest[lower] + 1)
        longest[syndrome] = best
    census: Dict[int, int] = {}
    for value in longest:
        census[value] = census.get(value, 0) + 1
    return {
        "census": dict(sorted(census.items())),
        "total": sum(longest),
        "equals_popcount": all(longest[s] == popcount(s)
                               for s in range(1 << 12)),
        "mean": Fraction(sum(longest), 1 << 12),
    }


# ===========================================================================
# 3.  RELAXATION IS NOT DECODING
# ===========================================================================

@memo
def _leaders() -> Tuple[int, ...]:
    """The coset leader weight of each syndrome, by exhaustive search."""
    columns = syndrome_columns()
    leaders = [1 << 20] * (1 << 12)
    leaders[0] = 0
    for weight in range(1, 5):
        for cells in combinations(range(24), weight):
            syndrome = 0
            for cell in cells:
                syndrome ^= columns[cell]
            if weight < leaders[syndrome]:
                leaders[syndrome] = weight
    return tuple(leaders)


def leader_census() -> Dict[int, int]:
    """The coset weight census: 1, 24, 276, 2024, 1771."""
    census: Dict[int, int] = {}
    for value in _leaders():
        census[value] = census.get(value, 0) + 1
    return dict(sorted(census.items()))


@memo
def trapped_census() -> Dict[str, object]:
    """Where descent and decoding disagree, counted."""
    leaders = _leaders()
    steps = _fastest_steps()
    joint: Dict[str, int] = {}
    trapped = 0
    for syndrome in range(1 << 12):
        if steps[syndrome] != leaders[syndrome]:
            trapped += 1
            key = f"{leaders[syndrome]},{steps[syndrome]}"
            joint[key] = joint.get(key, 0) + 1
    worst = max(steps)
    columns = syndrome_columns()
    message_pairs = {columns[i] ^ columns[j]
                     for i, j in combinations(range(12), 2)}
    worst_cosets = {s for s in range(1 << 12) if steps[s] == worst}
    return {
        "trapped": trapped,
        "joint_census": dict(sorted(joint.items())),
        "descent_is_not_decoding": trapped > 0,
        "worst_case_steps": worst,
        "worst_case_cosets": len(worst_cosets),
        "message_pairs": len(message_pairs),
        "worst_case_is_the_message_pairs": worst_cosets == message_pairs,
    }


# ===========================================================================
# 4.  ONE CALL FOR THE WHOLE DIVE
# ===========================================================================

def deep_dive_report() -> Dict[str, object]:
    """Every section of ``studies/ARCHIVE_DEEP_DIVE_STUDY.md``, recomputed."""
    chance = chance_census()
    expected = chance_expected_balanced()
    observed = observed_census()
    return {
        "codewords": 1 << 12,
        "balance": {
            "chance_census": chance,
            "eight_subsets": sum(chance.values()),
            "expected_balanced_by_chance": expected,
            "observed_census": observed,
            "observed_balanced": observed[0],
            "excess_over_chance": Fraction(observed[0]) - expected,
            "relabelling": transposition_range(),
            "swap_witness": swap_witness(0, 8),
            "block_deviation": block_deviation(),
            "extreme_octads": deviation_eight_octads(),
            "verdict": (
                "the measure is near-blind: chance alone predicts just over "
                "39 of the 759, the observed 44 exceeds that by under five, "
                "and relabelling by a single transposition moves the count "
                "anywhere between 27 and 63."),
        },
        "relaxation": {
            "column_weights": column_weights(),
            "best_drop_census": best_drop_census(),
            "fastest_descent": fastest_descent_census(),
            "greedy_descent": greedy_descent_census(),
            "greedy_descent_prefer_last": greedy_descent_census(True),
            "longest_path": longest_path_census(),
            "leader_census": leader_census(),
            "trapped": trapped_census(),
            "verdict": (
                "descent reaches the code but not the coset leader: 792 of "
                "the 4,096 cosets need more strictly-descending flips than "
                "their leader has weight, and the worst 66 are exactly the "
                "pairs of message-half coordinates."),
        },
        "lean_files": ("RequestProject/GLM/TriadChance.lean",
                       "RequestProject/GLM/Relaxation.lean"),
        "study": "studies/ARCHIVE_DEEP_DIVE_STUDY.md",
    }
