"""``glm_universal.reasoning.search_loop`` -- the archive's reasoning loop,
measured.

What this module is
-------------------
The computational half of ``studies/SEARCH_LOOP_STUDY.md``.  The archive's ARC
solvers converge on one shape -- propose candidate programs, keep exactly those
that reproduce every training pair (the **hard gate**), and rank what is left
by description cost -- and its own ledger records the alternative, accepting a
candidate because a coherence score is high, as *catastrophic*.  This module
measures what that shape leaves behind, on the smallest instance the archive
itself used: the eight symmetries of the square acting on ``3 x 3`` binary
grids.

``act`` / ``group_is_closed`` / ``group_is_faithful``
    the candidate set: eight distinct permutations, closed under composition;
``survivors`` / ``stabiliser`` / ``stabiliser_census``
    what one example leaves -- a coset of the stabiliser of its input, so the
    survivor count is ``|Stab g|`` whatever the observed output was;
``ambiguity`` / ``predictions`` / ``ambiguity_census``
    what that leaves undetermined: not how many candidates survive but how many
    different answers they give on a fresh question, which is an *orbit* under
    the stabiliser and is 1 exactly when every symmetry of the example is also
    a symmetry of the question;
``second_example_census``
    what a second example buys;
``gate_beats_score_witness``
    the four-line refutation of the soft gate: one observation, two candidates,
    and a score that prefers the one the observation has already refuted.

The formal development is ``RequestProject/GLM/SearchLoop.lean``, which proves
the general statements -- soundness, monotonicity, blindness, termination --
for an arbitrary candidate set, and by D8 it is the specification.  Everything
here is exact (D7).
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

__all__ = [
    "SIDE", "CELLS", "GRIDS", "GROUP_ORDER", "GROUP_NAMES", "PERMUTATIONS",
    "act", "compose", "group_is_closed", "group_is_faithful",
    "survivors", "stabiliser", "stabiliser_card", "stabiliser_census",
    "orbit_count", "mean_survivors",
    "predictions", "ambiguity", "ambiguity_census", "mean_ambiguity",
    "determined_fraction", "second_example_census",
    "gate_beats_score_witness", "search_loop_report",
]

#: The grid is 3 x 3, so a grid is one of 512 bitmasks.
SIDE = 3
CELLS = SIDE * SIDE
GRIDS = 1 << CELLS

#: The candidate set: the eight symmetries of the square.
GROUP_NAMES: Tuple[str, ...] = (
    "identity", "rot90", "rot180", "rot270",
    "flip_horizontal", "flip_vertical", "transpose", "anti_transpose",
)
GROUP_ORDER = len(GROUP_NAMES)


def _cell(row: int, col: int) -> int:
    return SIDE * row + col


def _permutation(name: str) -> Tuple[int, ...]:
    """Where each cell comes *from* under the named symmetry."""
    out: List[int] = []
    last = SIDE - 1
    for row in range(SIDE):
        for col in range(SIDE):
            if name == "identity":
                source = (row, col)
            elif name == "rot90":
                source = (last - col, row)
            elif name == "rot180":
                source = (last - row, last - col)
            elif name == "rot270":
                source = (col, last - row)
            elif name == "flip_horizontal":
                source = (row, last - col)
            elif name == "flip_vertical":
                source = (last - row, col)
            elif name == "transpose":
                source = (col, row)
            elif name == "anti_transpose":
                source = (last - col, last - row)
            else:  # pragma: no cover
                raise ValueError(f"_permutation: unknown symmetry {name!r}")
            out.append(_cell(*source))
    return tuple(out)


#: ``PERMUTATIONS[k][i]`` is the cell whose value lands in cell ``i``.
PERMUTATIONS: Tuple[Tuple[int, ...], ...] = tuple(
    _permutation(name) for name in GROUP_NAMES)


def act(k: int, grid: int) -> int:
    """Apply candidate ``k`` to ``grid``, as a bitmask of the nine cells."""
    if not 0 <= k < GROUP_ORDER:
        raise ValueError("act: k must name one of the eight symmetries")
    if not 0 <= grid < GRIDS:
        raise ValueError("act: grid must be nine bits")
    permutation = PERMUTATIONS[k]
    out = 0
    for target, source in enumerate(permutation):
        if (grid >> source) & 1:
            out |= 1 << target
    return out


def compose(a: int, b: int) -> Tuple[int, ...]:
    """The permutation of ``a`` after ``b``."""
    pa, pb = PERMUTATIONS[a], PERMUTATIONS[b]
    return tuple(pb[pa[i]] for i in range(CELLS))


def group_is_closed() -> bool:
    """Every composite of two candidates is a candidate -- ``d4_closed``."""
    known = set(PERMUTATIONS)
    return all(compose(a, b) in known
               for a in range(GROUP_ORDER) for b in range(GROUP_ORDER))


def group_is_faithful() -> bool:
    """The eight tables are eight *different* permutations -- ``d4_faithful``."""
    return len(set(PERMUTATIONS)) == GROUP_ORDER


# ---------------------------------------------------------------------------
# 1.  What one example leaves
# ---------------------------------------------------------------------------
def survivors(grid: int, observed: int) -> Tuple[int, ...]:
    """The candidates that reproduce the example -- the hard gate, D1.

    Nothing about the candidate is consulted except what it computes: a
    candidate is kept when its output on ``grid`` is exactly ``observed``.
    """
    return tuple(k for k in range(GROUP_ORDER) if act(k, grid) == observed)


def stabiliser(grid: int) -> Tuple[int, ...]:
    """The candidates that leave ``grid`` alone."""
    return survivors(grid, grid)


def stabiliser_card(grid: int) -> int:
    """How many candidates survive one example on ``grid`` -- ``|Stab g|``."""
    return len(stabiliser(grid))


_STAB_CARD: Optional[Tuple[int, ...]] = None
_STAB_SET: Optional[Tuple[FrozenSet[int], ...]] = None


def _stabiliser_tables() -> Tuple[Tuple[int, ...], Tuple[FrozenSet[int], ...]]:
    global _STAB_CARD, _STAB_SET
    if _STAB_CARD is None or _STAB_SET is None:
        sets = tuple(frozenset(stabiliser(g)) for g in range(GRIDS))
        _STAB_SET = sets
        _STAB_CARD = tuple(len(s) for s in sets)
    return _STAB_CARD, _STAB_SET


def stabiliser_census() -> Dict[int, int]:
    """How many grids have each stabiliser size -- ``stab_census``."""
    cards, _ = _stabiliser_tables()
    census: Dict[int, int] = {}
    for card in cards:
        census[card] = census.get(card, 0) + 1
    return dict(sorted(census.items()))


def orbit_count() -> int:
    """The number of orbits, by Burnside -- ``burnside_orbits``.

    The sum of the stabiliser sizes is ``|G|`` times the number of orbits, so
    the count is read off the same census rather than computed again.
    """
    cards, _ = _stabiliser_tables()
    total = sum(cards)
    if total % GROUP_ORDER:  # pragma: no cover
        raise AssertionError("orbit_count: Burnside's total is not divisible")
    return total // GROUP_ORDER


def mean_survivors() -> Fraction:
    """The mean number of survivors of one example."""
    cards, _ = _stabiliser_tables()
    return Fraction(sum(cards), GRIDS)


# ---------------------------------------------------------------------------
# 2.  What that leaves undetermined
# ---------------------------------------------------------------------------
def predictions(grid: int, observed: int, question: int) -> Tuple[int, ...]:
    """The distinct answers the survivors give on a fresh ``question``."""
    return tuple(sorted({act(k, question)
                         for k in survivors(grid, observed)}))


def ambiguity(grid: int, question: int) -> int:
    """How many different answers the survivors give -- the orbit of the
    question under the stabiliser of the example."""
    _, sets = _stabiliser_tables()
    return len({act(k, question) for k in sets[grid]})


def ambiguity_census() -> Dict[int, int]:
    """The census over all ``512 x 512`` (example, question) pairs."""
    _, sets = _stabiliser_tables()
    census: Dict[int, int] = {}
    by_stabiliser: Dict[FrozenSet[int], Dict[int, int]] = {}
    for grid in range(GRIDS):
        key = sets[grid]
        rows = by_stabiliser.get(key)
        if rows is None:
            rows = {}
            for question in range(GRIDS):
                size = len({act(k, question) for k in key})
                rows[size] = rows.get(size, 0) + 1
            by_stabiliser[key] = rows
        for size, count in rows.items():
            census[size] = census.get(size, 0) + count
    return dict(sorted(census.items()))


def mean_ambiguity() -> Fraction:
    """The mean number of distinct answers, over every pair."""
    census = ambiguity_census()
    return Fraction(sum(k * v for k, v in census.items()),
                    sum(census.values()))


def determined_fraction() -> Fraction:
    """The fraction of pairs on which one example determines the answer."""
    census = ambiguity_census()
    return Fraction(census.get(1, 0), sum(census.values()))


def second_example_census() -> Dict[str, object]:
    """What a second example buys: the survivors of both are the candidates
    fixing both, so the count is ``|Stab g1 ∩ Stab g2|``."""
    _, sets = _stabiliser_tables()
    seen: Dict[Tuple[FrozenSet[int], FrozenSet[int]], int] = {}
    census: Dict[int, int] = {}
    counts: Dict[FrozenSet[int], int] = {}
    for s in sets:
        counts[s] = counts.get(s, 0) + 1
    for a, na in counts.items():
        for b, nb in counts.items():
            size = len(a & b)
            census[size] = census.get(size, 0) + na * nb
    del seen
    pairs = sum(census.values())
    single: Dict[int, int] = {}
    for s, n in counts.items():
        single[len(s)] = single.get(len(s), 0) + n * GRIDS
    return {
        "pairs": pairs,
        "census": dict(sorted(census.items())),
        "single_example_census": dict(sorted(single.items())),
        "pinned_by_two": census.get(1, 0),
        "pinned_by_one": single.get(1, 0),
        "mean": Fraction(sum(k * v for k, v in census.items()), pairs),
        "lean": "GLM.SearchLoop.survivors_antitone",
    }


# ---------------------------------------------------------------------------
# 3.  The soft gate, refuted
# ---------------------------------------------------------------------------
def gate_beats_score_witness() -> Dict[str, object]:
    """``score_gate_unsound``, run rather than quoted.

    Two candidates over one bit -- ``False`` computes the identity, ``True``
    computes negation -- and one observation, ``(True, True)``.  The gate keeps
    ``False`` and refutes ``True``; the score prefers ``True``.
    """
    def semantics(candidate: bool, argument: bool) -> bool:
        return candidate != argument          # xor

    observations = ((True, True),)
    candidates = (False, True)
    score = {False: 0, True: 1}
    kept = tuple(h for h in candidates
                 if all(semantics(h, a) == b for a, b in observations))
    choice = max(candidates, key=lambda h: score[h])
    truth = kept[0]
    return {
        "candidates": candidates,
        "observations": observations,
        "survivors": kept,
        "truth": truth,
        "truth_survives": truth in kept,
        "score": dict(score),
        "score_choice": choice,
        "score_choice_is_refuted": choice not in kept,
        "lean": "GLM.SearchLoop.score_gate_unsound",
    }


# ---------------------------------------------------------------------------
# 4.  One call for the study
# ---------------------------------------------------------------------------
def search_loop_report() -> Dict[str, object]:
    """Every census of ``studies/SEARCH_LOOP_STUDY.md``, recomputed."""
    stabilisers = stabiliser_census()
    ambiguities = ambiguity_census()
    second = second_example_census()
    return {
        "grids": GRIDS,
        "candidates": GROUP_ORDER,
        "group_is_closed": group_is_closed(),
        "group_is_faithful": group_is_faithful(),
        "stabiliser_census": stabilisers,
        "stabiliser_total": sum(k * v for k, v in stabilisers.items()),
        "orbits": orbit_count(),
        "mean_survivors": mean_survivors(),
        "pairs": sum(ambiguities.values()),
        "ambiguity_census": ambiguities,
        "ambiguity_total": sum(k * v for k, v in ambiguities.items()),
        "mean_ambiguity": mean_ambiguity(),
        "determined_fraction": determined_fraction(),
        "every_ambiguity_divides_eight":
            all(GROUP_ORDER % k == 0 for k in ambiguities),
        "second_example": second,
        "soft_gate": gate_beats_score_witness(),
        "study": "studies/SEARCH_LOOP_STUDY.md",
        "lean_file": "RequestProject/GLM/SearchLoop.lean",
    }
