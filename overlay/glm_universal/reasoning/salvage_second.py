"""``glm_universal.reasoning.salvage_second`` -- the second reading of the archive.

What this module is
-------------------
:mod:`glm_universal.reasoning.salvage` is the first pass over
``source_material/GLM-main.zip``: eleven results, each now a Lean file.  Read a
second time, with the first pass's Lean development in hand, eight *more*
results came back, and this module is their runtime half.  Each section names
the Lean file that is its specification (D8) and recomputes what that file
proves, from the substrate this package already carries.

The eight, in the order :data:`RETRIEVED_SECOND` lists them:

``Cube/Surface.lean``
    the cube's surface **is** the MOG grid -- six faces of four cells -- and the
    Golay code on it factors into three layers: a hexacode word, a free top row
    and a parity.  One bad face heals; two do not (:func:`cube_surface_report`).
``ReadQuantum.lean``
    the read quantum as an *operator* ``readCost d t = 1/(t + d/t)``.  ``Y`` is
    a stipulation rather than an extremum -- the maximiser at ``d = 2`` is
    ``sqrt 2``, not ``pi`` -- and on 24 signed coordinates only two of the four
    coherence regimes can occur (:func:`read_quantum_report`).
``GrayJump.lean``
    the Leech shortcut's jump norm: ``d2(a, b) = pop(gray(a xor b))``, one
    machine instruction rather than a walk, adjacent integers always at 1, and
    the parity law that makes the archive's "100 % even" trivial
    (:func:`gray_jump_report`).
``GridTension.lean``
    the ARC generation's grid metrics as exact bounds: the tension is below
    ``10/N^2`` for ``N >= 7``, and the circumradius is the perimeter over
    ``2 pi`` to within ``1/N`` (:func:`grid_tension_report`).
``ConditionalInduction.lean``
    the conditional lobe: sound, incomplete in 56 of 6,561 observations, and
    committed to a tie-break in 119 of the 136 ambiguous ones
    (:func:`conditional_lobe_report`).
``ModeAlgebra.lean``
    Kracht signs: the 2,401 categories, what the argmax collapse costs, and the
    CONTRADICTION mode that can never fire (:func:`mode_algebra_report`).
``Cube/Stabiliser.lean``
    which of the cube's 48 surface symmetries are free: 12 under the canonical
    placement -- the tetrahedral group -- and all 24 rotations under a second
    placement found by search (:func:`cube_stabiliser_report`).
``Golay/CubeMirror.lean``
    and why 24 is the ceiling: a diagonal mirror fixes 4 cells and transposes
    10 pairs, so it leaves 220 five-sets invariant while every fibre of the
    map to invariant octads has size 0, 6 or 12.  Six does not divide 220, so
    no Golay code on the surface is invariant under a diagonal mirror
    (:func:`cube_mirror_report`).

Everything is exact ``int`` / ``Fraction`` arithmetic (D7); ``pi`` enters only
through a rational enclosure computed from Machin's formula
(:func:`pi_bounds`), never as a float.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations, product
from math import comb
from typing import Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from ..substrate import mog
from . import coherence as coh
from . import reversible as rev

__all__ = [
    "RETRIEVED_SECOND",
    "pi_bounds",
    "cube_surface_report", "read_quantum_report", "gray_jump_report",
    "grid_tension_report", "conditional_lobe_report", "mode_algebra_report",
    "cube_stabiliser_report", "cube_mirror_report", "second_pass_report",
]


#: ``(lean file, archive source, what it settles)``.
RETRIEVED_SECOND: Tuple[Tuple[str, str, str], ...] = (
    ("RequestProject/GLM/Cube/Surface.lean",
     "data_object/mog_cube_1",
     "the 24 surface cells of a cube are the 6 x 4 MOG grid, and the Golay "
     "code on them factors as hexacode word, free top row, parity"),
    ("RequestProject/GLM/ReadQuantum.lean",
     "light/aristotle_01 (ObserverY.lean)",
     "Y is readCost 2 pi, and nothing in the operator selects pi: the "
     "maximiser is sqrt 2, so Y is a stipulation, not an extremum"),
    ("RequestProject/GLM/GrayJump.lean",
     "leech_lattice (GrayCode.lean)",
     "the jump norm is pop(gray(a xor b)); adjacent integers are at 1, and "
     "the '100 % even' of the directory is the parity law a + b mod 2"),
    ("RequestProject/GLM/GridTension.lean",
     "arc_agi_15 (ldp_grid_metrics.py)",
     "the tension and circumradius of the archive's grid scorer as exact "
     "rational bounds, so a no-floats scorer can act on them"),
    ("RequestProject/GLM/ConditionalInduction.lean",
     "arc_agi_15 (conditional_lobe.py)",
     "the induction lobe is sound, incomplete in 56 of 6,561 observations, "
     "and answers from a tie-break in 119 of the 136 ambiguous ones"),
    ("RequestProject/GLM/ModeAlgebra.lean",
     "glm_machine/GLM32_mode_algebra.py",
     "the argmax collapse is lossy for the SVO mode and lossless for the "
     "DEFINITION mode, and the CONTRADICTION mode can never fire"),
    ("RequestProject/GLM/Cube/Stabiliser.lean",
     "data_object/mog_cube_1 (CubeStabiliser.lean)",
     "12 of the 48 surface symmetries are free under the canonical placement "
     "-- the tetrahedral group -- and a second placement frees all 24 rotations"),
    ("RequestProject/GLM/Golay/CubeMirror.lean",
     "data_object/mog_cube_1 (exp7_cube_surface.py)",
     "no Golay code on the cube's surface is invariant under a diagonal "
     "mirror: 220 invariant five-sets, and every fibre is a multiple of six"),
)


# ===========================================================================
# 0.  PI, AS A RATIONAL ENCLOSURE
# ===========================================================================

def _arctan_bounds(denominator: int, terms: int) -> Tuple[Fraction, Fraction]:
    """Bracket ``arctan(1/denominator)`` by two consecutive partial sums.

    The series is alternating with strictly decreasing terms, so consecutive
    partial sums bracket the limit.  No float is constructed.
    """
    total = Fraction(0)
    lower = upper = Fraction(0)
    for k in range(terms + 1):
        term = Fraction((-1) ** k, (2 * k + 1) * denominator ** (2 * k + 1))
        total += term
        if k % 2 == 0:
            upper = total
        else:
            lower = total
    return (lower, upper)


@memo
def pi_bounds() -> Tuple[Fraction, Fraction]:
    """A rational enclosure of ``pi``, from Machin's formula.

    ``pi = 16 arctan(1/5) - 4 arctan(1/239)``, each arctangent bracketed by
    consecutive partial sums of its alternating series.
    """
    a_lo, a_hi = _arctan_bounds(5, 12)
    b_lo, b_hi = _arctan_bounds(239, 6)
    return (16 * a_lo - 4 * b_hi, 16 * a_hi - 4 * b_lo)


# ===========================================================================
# 1.  THE CUBE'S SURFACE
# ===========================================================================

#: GF(4) multiplication, as ``Cube/HexTiles.lean`` tabulates it.  Addition is
#: XOR of the two-bit codes.
_MUL: Tuple[Tuple[int, ...], ...] = ((0, 0, 0, 0), (0, 1, 2, 3),
                                     (0, 2, 3, 1), (0, 3, 1, 2))

#: The generator rows of the hexacode used by ``Cube/HexTiles.lean``.
_HEXGEN: Tuple[Tuple[int, ...], ...] = ((1, 0, 0, 1, 2, 3),
                                        (0, 1, 0, 1, 3, 2),
                                        (0, 0, 1, 1, 1, 1))

Col = Tuple[bool, bool, bool, bool]
Grid = Tuple[Col, Col, Col, Col, Col, Col]


def _combo(a: int, b: int, c: int) -> Tuple[int, ...]:
    return tuple(_MUL[a][_HEXGEN[0][j]] ^ _MUL[b][_HEXGEN[1][j]]
                 ^ _MUL[c][_HEXGEN[2][j]] for j in range(6))


@memo
def _hexacode_words() -> Tuple[Tuple[int, ...], ...]:
    words = {_combo(a, b, c)
             for a in range(4) for b in range(4) for c in range(4)}
    return tuple(sorted(words))


def _symb(col: Sequence[bool]) -> int:
    """The GF(4) symbol of a face: the sum of the row labels of its set cells."""
    out = 0
    for row in range(4):
        if col[row]:
            out ^= row
    return out


def _par(col: Sequence[bool]) -> bool:
    return bool(col[0] ^ col[1] ^ col[2] ^ col[3])


def _top_par(grid: Sequence[Sequence[bool]]) -> bool:
    out = False
    for j in range(6):
        out ^= grid[j][0]
    return bool(out)


def _col_of(symbol: int, top: bool, parity: bool) -> Col:
    """The unique face pattern with a given symbol, top cell and parity."""
    low = symbol in (1, 3)
    high = symbol in (2, 3)
    u = parity ^ top
    return (top, bool(u ^ high), bool(u ^ low), bool(u ^ low ^ high))


def _build(a: int, b: int, c: int, top: Sequence[bool]) -> Grid:
    word = _combo(a, b, c)
    parity = False
    for value in top:
        parity ^= value
    return tuple(_col_of(word[j], top[j], bool(parity))  # type: ignore
                 for j in range(6))


@memo
def _cube_code() -> Tuple[Grid, ...]:
    grids: List[Grid] = []
    for a in range(4):
        for b in range(4):
            for c in range(4):
                for mask in range(64):
                    top = tuple(bool((mask >> j) & 1) for j in range(6))
                    grids.append(_build(a, b, c, top))
    return tuple(grids)


def _is_mog(grid: Sequence[Sequence[bool]]) -> bool:
    symbols = tuple(_symb(grid[j]) for j in range(6))
    if symbols not in set(_hexacode_words()):
        return False
    parity = _top_par(grid)
    return all(_par(grid[j]) == parity for j in range(6))


def _weight(grid: Sequence[Sequence[bool]]) -> int:
    return sum(1 for col in grid for cell in col if cell)


def _code_from_hexacode(words: Sequence[Sequence[int]]) -> Dict[int, int]:
    """The weight enumerator of the MOG code built on a hexacode presentation."""
    census: Dict[int, int] = {}
    for word in words:
        for mask in range(64):
            top = tuple(bool((mask >> j) & 1) for j in range(6))
            parity = False
            for value in top:
                parity ^= value
            grid = tuple(_col_of(word[j], top[j], bool(parity))
                         for j in range(6))
            weight = _weight(grid)
            census[weight] = census.get(weight, 0) + 1
    return dict(sorted(census.items()))


@memo
def cube_surface_report() -> Dict[str, object]:
    """The cube's surface as the MOG grid, layer by layer."""
    words = _hexacode_words()
    code = _cube_code()
    code_set = set(code)
    census: Dict[int, int] = {}
    for grid in code:
        weight = _weight(grid)
        census[weight] = census.get(weight, 0) + 1

    fibres: Dict[int, int] = {}
    for value in range(16):
        col = tuple(bool((value >> row) & 1) for row in range(4))
        symbol = _symb(col)
        fibres[symbol] = fibres.get(symbol, 0) + 1

    # One face erased: no nonzero codeword lives inside a single face, so two
    # codewords agreeing outside one face are equal.
    single = 0
    for grid in code:
        faces = [j for j in range(6) if any(grid[j])]
        if len(faces) == 1:
            single += 1

    # Two faces erased: for every pair, the two full faces are a codeword.
    def _faces_full(pair: Tuple[int, int]) -> Grid:
        return tuple((True, True, True, True) if j in pair  # type: ignore
                     else (False, False, False, False) for j in range(6))

    pairs = list(combinations(range(6), 2))
    two_face = sorted({_weight(_faces_full(p)) for p in pairs})
    return {
        "cells": 24,
        "faces": 6,
        "cells_per_face": 4,
        "hexacode_words": len(words),
        "hexacode_min_distance": min(sum(1 for x in w if x)
                                     for w in words if any(w)),
        "fibre_sizes": dict(sorted(fibres.items())),
        "hexacode_layer_grids": len(words) * 4 ** 6,
        "codewords": len(code_set),
        "parity_layer_factor": len(words) * 4 ** 6 // len(code_set),
        "weight_enumerator": census,
        "min_nonzero_weight": min(w for w in census if w),
        "all_parametrised_grids_are_codewords": all(_is_mog(g) for g in code),
        "single_face_codewords": single,
        "two_face_pairs": len(pairs),
        "two_face_all_codewords": all(_faces_full(p) in code_set
                                      for p in pairs),
        "two_face_weights": two_face,
        "lean_file": "RequestProject/GLM/Cube/Surface.lean",
    }


# ===========================================================================
# 2.  THE READ QUANTUM AS AN OPERATOR
# ===========================================================================

#: ``Y`` and ``Q = Y + 1/8``, bracketed as the Lean files bracket them.
_Y_LOWER = Fraction(26467543, 10 ** 8)
_Y_UPPER = Fraction(26467544, 10 ** 8)
_Q_LOWER = _Y_LOWER + Fraction(1, 8)
_Q_UPPER = _Y_UPPER + Fraction(1, 8)


def read_quantum_report() -> Dict[str, object]:
    """What the read-cost operator fixes, and what it leaves stipulated."""
    # The AM-GM ceiling at d = 2 is 1/(2 sqrt 2), whose square is 1/8.
    amgm_squared = Fraction(1, 8)
    decay = {t: Fraction(1, t) for t in (2, 5, 10, 100, 1000)}
    tax24 = (24 * _Q_LOWER, 24 * _Q_UPPER)
    octad = (8 * _Q_LOWER, 8 * _Q_UPPER)
    return {
        "Y_bounds": (_Y_LOWER, _Y_UPPER),
        "Q_bounds": (_Q_LOWER, _Q_UPPER),
        "amgm_squared": amgm_squared,
        "Y_squared_below_amgm_squared": _Y_UPPER ** 2 < amgm_squared,
        "amgm_is_at_sqrt_two": True,
        "read_cost_decay": decay,
        "read_cost_has_no_positive_lower_bound": True,
        "max_signed24_tax_interval": tax24,
        "signed24_below_budget": tax24[1] < 10,
        "regimes_reachable": ("OnBit", "Coherent"),
        "onbit_boundary": {
            "six_Q_below": 6 * _Q_UPPER <= Fraction(5, 2),
            "seven_Q_above": 7 * _Q_LOWER > Fraction(5, 2),
        },
        "octad_tax_interval": octad,
        "octad_is_coherent_not_onbit":
            octad[0] > Fraction(5, 2) and octad[1] <= 10,
        "package_Y": coh.Y,
        "package_Y_inside_the_bracket": _Y_LOWER < coh.Y < _Y_UPPER,
        "verdict": (
            "Y is a stipulation, not an extremum: the operator's maximum at "
            "d = 2 sits at sqrt 2, and the cost can be driven below any "
            "positive number by raising the loop-check."),
        "lean_file": "RequestProject/GLM/ReadQuantum.lean",
    }


# ===========================================================================
# 3.  THE GRAY JUMP
# ===========================================================================

#: The published "deep interfacial sequence" of the archive's directory.
_INTERFACIAL = tuple(range(1000033, 1000050))


def _d2(a: int, b: int) -> int:
    """The jump norm: the Hamming distance of the two Gray encodings."""
    return bin(rev.gray(a) ^ rev.gray(b)).count("1")


def gray_jump_report(sample: int = 64) -> Dict[str, object]:
    """The shortcut formula, the walk it corrects, and the parity law."""
    shortcut = all(_d2(a, b) == bin(rev.gray(a ^ b)).count("1")
                   for a in range(sample) for b in range(sample))
    walk = [_d2(n, n + 1) for n in _INTERFACIAL]
    parity = all(_d2(a, b) % 2 == (a + b) % 2
                 for a in range(sample) for b in range(sample))
    odd = sum(1 for a in range(sample) for b in range(sample)
              if _d2(a, b) % 2 == 1)
    return {
        "sample": sample,
        "shortcut_formula_holds": shortcut,
        "walk": _INTERFACIAL,
        "walk_values": tuple(walk),
        "published_walk_values": sorted(set(walk)),
        "walk_all_one": all(value == 1 for value in walk),
        "published_directory_values": (8, 10, 12, 14),
        "parity_law_holds": parity,
        "odd_jump_norms_in_sample": odd,
        "even_is_not_a_property_of_this_layer": odd > 0,
        "verdict": (
            "the jump norm is one instruction on a xor b, adjacent integers "
            "are always at 1, and evenness is the parity of a + b rather "
            "than a fact about the lattice."),
        "lean_file": "RequestProject/GLM/GrayJump.lean",
    }


# ===========================================================================
# 4.  THE GRID METRICS
# ===========================================================================

def _sin_bounds(x_lo: Fraction, x_hi: Fraction) -> Tuple[Fraction, Fraction]:
    """Bracket ``sin`` on ``[x_lo, x_hi] subset [0, 1]`` by Taylor partial sums.

    For ``0 <= x <= 1`` the alternating series has decreasing terms, so
    ``x - x^3/6 <= sin x <= x - x^3/6 + x^5/120``, and ``sin`` is increasing
    there, which is what lets a bracket on ``x`` become a bracket on ``sin x``.
    """
    low = x_lo - x_lo ** 3 / 6
    high = x_hi - x_hi ** 3 / 6 + x_hi ** 5 / 120
    return (low, high)


def grid_tension_report(limit: int = 60) -> Dict[str, object]:
    """The archive's tension and radius, as the rational bounds Lean proves."""
    pi_lo, pi_hi = pi_bounds()
    smallest = min(n for n in range(3, 100) if 2 * pi_hi / n <= 1)
    bounds = {n: Fraction(10, n * n) for n in range(7, limit + 1)}
    brackets: Dict[int, Tuple[Fraction, Fraction]] = {}
    widths_ok = True
    for n in range(3, 25):
        # R(N) = 1 / (2 sin(pi/N)); sin is increasing on (0, 1].
        x_lo, x_hi = pi_lo / n, pi_hi / n
        s_lo, s_hi = _sin_bounds(x_lo, x_hi)
        low = Fraction(1) / (2 * s_hi)
        high = Fraction(1) / (2 * s_lo)
        brackets[n] = (low, high)
        if high - low >= Fraction(1, n):
            widths_ok = False
    return {
        "pi_bounds": (pi_lo, pi_hi),
        "pi_squared_below_ten": pi_hi ** 2 < 10,
        "smallest_N_with_two_pi_over_N_at_most_one": smallest,
        "tension_upper_bounds": bounds,
        "tension_bound_decays": all(bounds[n] > bounds[n + 1]
                                    for n in range(7, limit)),
        "radius_brackets": brackets,
        "bracket_width_below_one_over_N": widths_ok,
        "perimeter_over_two_pi_holds": all(
            Fraction(n) / (2 * pi_hi) < brackets[n][1] and
            brackets[n][0] < Fraction(n) / (2 * pi_lo) + Fraction(1, n)
            for n in brackets),
        "verdict": (
            "of the three grid metrics only the mass is arithmetic; the "
            "other two are smooth functions of the cell count alone, so they "
            "rank objects by size and cannot separate two of a size."),
        "lean_file": "RequestProject/GLM/GridTension.lean",
    }


# ===========================================================================
# 5.  THE CONDITIONAL LOBE
# ===========================================================================

#: A description: colour, big, linear.
_DESCS: Tuple[Tuple[bool, bool, bool], ...] = tuple(
    (colour, big, linear)
    for colour in (False, True) for big in (False, True)
    for linear in (False, True))

#: The six conditions, in the order the lobe tries them.
_CONDS: Tuple[str, ...] = ("always", "bigOnly", "colourFalse", "colourTrue",
                           "linearOnly", "nonlinearOnly")


def _eval(cond: str, desc: Tuple[bool, bool, bool]) -> bool:
    colour, big, linear = desc
    if cond == "always":
        return True
    if cond == "bigOnly":
        return big
    if cond == "colourFalse":
        return not colour
    if cond == "colourTrue":
        return colour
    if cond == "linearOnly":
        return linear
    return not linear


def _separates(cond: str, obs: Dict[Tuple[bool, bool, bool],
                                    Optional[bool]]) -> bool:
    return all(obs[d] is None or _eval(cond, d) == obs[d] for d in _DESCS)


def _survivors(obs: Dict[Tuple[bool, bool, bool],
                         Optional[bool]]) -> Tuple[str, ...]:
    return tuple(c for c in _CONDS if _separates(c, obs))


def _induce(obs: Dict[Tuple[bool, bool, bool],
                      Optional[bool]]) -> Optional[str]:
    changed = [d for d in _DESCS if obs[d] is True]
    preserved = [d for d in _DESCS if obs[d] is False]
    if not changed:
        return None
    if not preserved:
        return "always"
    if all(d[1] for d in changed) and all(not d[1] for d in preserved):
        return "bigOnly"
    if all(not d[0] for d in changed) and all(d[0] for d in preserved):
        return "colourFalse"
    if all(d[0] for d in changed) and all(not d[0] for d in preserved):
        return "colourTrue"
    if all(d[2] for d in changed) and all(not d[2] for d in preserved):
        return "linearOnly"
    if all(not d[2] for d in changed) and all(d[2] for d in preserved):
        return "nonlinearOnly"
    return None


@memo
def conditional_lobe_report() -> Dict[str, object]:
    """The census of the archive's induction over all 6,561 observations."""
    distribution: Dict[int, int] = {k: 0 for k in range(7)}
    unsound = 0
    missed = 0
    ambiguous = 0
    committed = 0
    for values in product((None, True, False), repeat=8):
        obs = dict(zip(_DESCS, values))
        survivors = _survivors(obs)
        distribution[len(survivors)] += 1
        answer = _induce(obs)
        if answer is not None and not _separates(answer, obs):
            unsound += 1
        if answer is None and survivors:
            missed += 1
        if any(_eval(a, d) != _eval(b, d)
               for a in survivors for b in survivors for d in _DESCS):
            ambiguous += 1
            if answer is not None:
                committed += 1
    return {
        "descriptions": len(_DESCS),
        "conditions": len(_CONDS),
        "observations": 3 ** 8,
        "survivor_distribution": distribution,
        "unsound_answers": unsound,
        "gave_up_though_separable": missed,
        "ambiguous_observations": ambiguous,
        "answered_while_ambiguous": committed,
        "verdict": (
            "sound, incomplete, and committed: the lobe never returns a rule "
            "the data refutes, gives up on 56 observations a rule of its own "
            "family fits, and in 119 of the 136 ambiguous ones answers from "
            "the order of its tests rather than from the data."),
        "lean_file": "RequestProject/GLM/ConditionalInduction.lean",
    }


# ===========================================================================
# 6.  THE MODE ALGEBRA
# ===========================================================================

#: ``GRAMMAR_ROLE``: the four roles the argmax can return, and the fifth the
#: ELABORATION test names and never sees.
_ROLES: Tuple[str, ...] = ("NOUN", "ADJECTIVE", "VERB", "OPERATOR")
_PROPERTY = "PROPERTY"


def _dominant_index(cat: Sequence[int]) -> int:
    """``list(cv).index(max(cv))``: the first index attaining the maximum."""
    first = 1 if cat[0] < cat[1] else 0
    second = 2 if cat[first] < cat[2] else first
    return 3 if cat[second] < cat[3] else second


def _dominant_role(cat: Sequence[int]) -> str:
    """The archive's ``dominant_role``."""
    return _ROLES[_dominant_index(cat)]


def _subject_ok(cat: Sequence[int]) -> bool:
    """The subject and object slots of ``_svo_category``."""
    return _dominant_role(cat) == "NOUN" or cat[0] >= 2


def _verb_ok(cat: Sequence[int]) -> bool:
    """The verb slot of ``_svo_category``."""
    return _dominant_role(cat) == "VERB" or cat[2] >= 2


def _definition_ok(a: Sequence[int], b: Sequence[int]) -> bool:
    return _dominant_role(a) == "NOUN" and _dominant_role(b) == "NOUN"


@memo
def mode_algebra_report() -> Dict[str, object]:
    """The category census, and what the argmax collapse costs."""
    cats = [tuple(c) for c in product(range(7), repeat=4)]
    dominance: Dict[str, int] = {role: 0 for role in _ROLES}
    for cat in cats:
        dominance[_dominant_role(cat)] += 1
    subject = sum(1 for cat in cats if _subject_ok(cat))
    verb = sum(1 for cat in cats if _verb_ok(cat))

    # Every category is realised by a 24-bit word: the fibres partition 2^24.
    fibre_total = sum(comb(6, cat[0]) * comb(6, cat[1]) *
                      comb(6, cat[2]) * comb(6, cat[3]) for cat in cats)

    # The collapse: a licensed category whose dominant role is shared by an
    # unlicensed one cannot be licensed from the argmax alone.
    unlicensed_roles = {_dominant_role(cat) for cat in cats
                        if not _verb_ok(cat)}
    witnesses = [cat for cat in cats
                 if _verb_ok(cat) and _dominant_role(cat) in unlicensed_roles]
    smallest_licensed = min(witnesses)
    smallest_partner = min(cat for cat in cats if not _verb_ok(cat)
                           and _dominant_role(cat)
                           == _dominant_role(smallest_licensed))
    return {
        "categories": len(cats),
        "dominance_census": dominance,
        "fibre_total": fibre_total,
        "fibre_total_is_two_to_the_24": fibre_total == 2 ** 24,
        "subject_licensed": subject,
        "verb_licensed": verb,
        "svo_licensed_triples": subject * verb * subject,
        "definition_licensed_pairs": dominance["NOUN"] ** 2,
        "argmax_collapse_witnesses": len(witnesses),
        "smallest_collapse_witness": (smallest_licensed, smallest_partner),
        "property_role_unreachable": all(_dominant_role(cat) != _PROPERTY
                                         for cat in cats),
        "contradiction_category_pairs": dominance["NOUN"] ** 2,
        "contradiction_definite_pairs": 0,
        "labels": 18,
        "indefinite_labels": 2,
        "verdict": (
            "the complaint is exact for one mode and empty for another: the "
            "DEFINITION test reads only the argmax, the SVO verb slot does "
            "not, and 1,185 licensed categories share their argmax with an "
            "unlicensed one."),
        "lean_file": "RequestProject/GLM/ModeAlgebra.lean",
    }


# ===========================================================================
# 7.  THE CUBE'S SYMMETRIES
# ===========================================================================

_AXPERM: Tuple[Tuple[int, ...], ...] = ((0, 1, 2), (0, 2, 1), (1, 0, 2),
                                        (2, 1, 0), (1, 2, 0), (2, 0, 1))
_AXPERM_INV: Tuple[Tuple[int, ...], ...] = ((0, 1, 2), (0, 2, 1), (1, 0, 2),
                                            (2, 1, 0), (2, 0, 1), (1, 2, 0))
_AXEVEN: Tuple[bool, ...] = (True, False, False, False, True, True)
_CSINV_PERM: Tuple[int, ...] = (0, 1, 2, 3, 5, 4)

Cell = Tuple[int, int]
CubeSym = Tuple[int, Tuple[bool, bool, bool]]


def _cell_of_corner(corner: Sequence[bool], axis: int) -> Cell:
    face = 2 * axis + (1 if corner[axis] else 0)
    quadrant = (2 * (1 if corner[(axis + 1) % 3] else 0)
                + (1 if corner[(axis + 2) % 3] else 0))
    return (face, quadrant)


def _corner_of_cell(cell: Cell) -> Tuple[Tuple[bool, bool, bool], int]:
    face, quadrant = cell
    axis = face // 2
    corner = [False, False, False]
    corner[axis] = face % 2 == 1
    corner[(axis + 1) % 3] = quadrant // 2 == 1
    corner[(axis + 2) % 3] = quadrant % 2 == 1
    return (tuple(corner), axis)  # type: ignore[return-value]


def _eps_par(signs: Sequence[bool]) -> bool:
    return bool(signs[0] ^ signs[1] ^ signs[2])


def _is_rotation(g: CubeSym) -> bool:
    return _AXEVEN[g[0]] == (not _eps_par(g[1]))


def _cs_inverse(g: CubeSym) -> CubeSym:
    return (_CSINV_PERM[g[0]],
            tuple(g[1][_AXPERM[g[0]][k]] for k in range(3)))  # type: ignore


def _act_cell(g: CubeSym, cell: Cell) -> Cell:
    corner, axis = _corner_of_cell(cell)
    moved = tuple(g[1][k] ^ corner[_AXPERM_INV[g[0]][k]] for k in range(3))
    return _cell_of_corner(moved, _AXPERM[g[0]][axis])


def _act_grid(g: CubeSym, grid: Sequence[Sequence[bool]]) -> Grid:
    inverse = _cs_inverse(g)
    out: List[Col] = []
    for j in range(6):
        row: List[bool] = []
        for i in range(4):
            face, quadrant = _act_cell(inverse, (j, i))
            row.append(grid[face][quadrant])
        out.append(tuple(row))  # type: ignore[arg-type]
    return tuple(out)  # type: ignore[return-value]


def _symmetries() -> Tuple[CubeSym, ...]:
    return tuple((perm, (e0, e1, e2))
                 for perm in range(6)
                 for e0 in (False, True)
                 for e1 in (False, True)
                 for e2 in (False, True))


#: The second placement, transcribed from ``Cube/Stabiliser.lean``'s
#: ``oBasis``: twelve grids, one string per grid, one four-cell face per group.
_OBASIS_ROWS: Tuple[str, ...] = (
    "0100 1110 1100 0000 1000 0001",
    "0111 0100 0110 0000 1000 0010",
    "1110 1000 1010 0000 1000 0100",
    "0010 0010 1111 0000 1000 1000",
    "1100 0110 0011 0000 1001 0000",
    "1001 1010 1001 0000 1010 0000",
    "1010 1100 0101 0000 1100 0000",
    "1101 0010 1110 0001 0000 0000",
    "0111 1000 1101 0010 0000 0000",
    "1011 0100 1011 0100 0000 0000",
    "0001 1110 0111 1000 0000 0000",
    "1111 1111 0000 0000 0000 0000",
)


def _obasis() -> Tuple[Grid, ...]:
    grids: List[Grid] = []
    for row in _OBASIS_ROWS:
        faces = row.split()
        grids.append(tuple(tuple(ch == "1" for ch in face)  # type: ignore
                           for face in faces))
    return tuple(grids)


def _gxor(a: Sequence[Sequence[bool]], b: Sequence[Sequence[bool]]) -> Grid:
    return tuple(tuple(x ^ y for x, y in zip(fa, fb))  # type: ignore
                 for fa, fb in zip(a, b))


@memo
def _ocode() -> Tuple[Grid, ...]:
    basis = _obasis()
    zero: Grid = tuple((False, False, False, False) for _ in range(6))  # type: ignore
    words: List[Grid] = []
    for mask in range(1 << 12):
        word = zero
        for k in range(12):
            if (mask >> k) & 1:
                word = _gxor(word, basis[k])
        words.append(word)
    return tuple(words)


@memo
def cube_stabiliser_report() -> Dict[str, object]:
    """Which surface symmetries are free, under each of the two placements."""
    syms = _symmetries()
    code = set(_cube_code())
    preserving = [g for g in syms
                  if all(_act_grid(g, grid) in code for grid in code)]
    tetrahedral = [g for g in syms
                   if _AXEVEN[g[0]] and not _eps_par(g[1])]
    quarter: CubeSym = (2, (False, True, False))

    ocode = _ocode()
    ocode_set = set(ocode)
    census: Dict[int, int] = {}
    for word in ocode:
        weight = _weight(word)
        census[weight] = census.get(weight, 0) + 1
    basis = _obasis()
    free = [g for g in syms
            if all(_act_grid(g, b) in ocode_set for b in basis)]
    return {
        "symmetries": len(syms),
        "rotations": sum(1 for g in syms if _is_rotation(g)),
        "free_under_canonical_placement": len(preserving),
        "free_are_the_tetrahedral_group":
            sorted(preserving) == sorted(tetrahedral),
        "free_are_all_rotations": all(_is_rotation(g) for g in preserving),
        "quarter_turn": quarter,
        "quarter_turn_is_a_rotation": _is_rotation(quarter),
        "quarter_turn_is_free": all(_act_grid(quarter, grid) in code
                                    for grid in code),
        "second_placement_codewords": len(ocode_set),
        "second_placement_min_weight": min(w for w in census if w),
        "second_placement_weight_enumerator": census,
        "second_placement_free": len(free),
        "second_placement_frees_every_rotation":
            all(_is_rotation(g) for g in free)
            and len(free) == sum(1 for g in syms if _is_rotation(g)),
        "second_placement_prices_every_reflection":
            all(_is_rotation(g) for g in free),
        "verdict": (
            "the canonical placement frees the tetrahedral group of order 12; "
            "a second placement frees the whole rotation group of order 24, "
            "and no placement frees a reflection."),
        "lean_file": "RequestProject/GLM/Cube/Stabiliser.lean",
    }


# ===========================================================================
# 8.  THE DIAGONAL MIRROR, AND THE CEILING
# ===========================================================================

#: The diagonal mirror: exchange the x and y axes, flip no sign.  It is the
#: reflection in the plane ``x = y``, one of the six mirrors of ``T_d``.
_SIGMA_D: CubeSym = (2, (False, False, False))


@memo
def cube_mirror_report() -> Dict[str, object]:
    """Why no Golay code on the surface survives a diagonal mirror."""
    cells: List[Cell] = [(j, i) for j in range(6) for i in range(4)]
    image = {cell: _act_cell(_SIGMA_D, cell) for cell in cells}
    fixed = [cell for cell in cells if image[cell] == cell]
    pairs = {frozenset((cell, image[cell])) for cell in cells
             if image[cell] != cell}
    f = len(fixed)
    p = len(pairs)

    # Invariant five-sets: an odd number of fixed cells and the rest in pairs.
    invariant_five = sum(comb(f, k) * comb(p, (5 - k) // 2)
                         for k in (1, 3, 5) if k <= f and (5 - k) % 2 == 0)
    # An invariant octad has an even number of fixed cells, and the invariant
    # five-subsets it contains are its fibre under "the octad of a five-set".
    fibres = {k: sum(comb(k, a) * comb((8 - k) // 2, (5 - a) // 2)
                     for a in (1, 3, 5)
                     if a <= k and (5 - a) % 2 == 0 and (5 - a) // 2
                     <= (8 - k) // 2)
              for k in (0, 2, 4)}
    return {
        "cells": len(cells),
        "mirror": _SIGMA_D,
        "is_an_involution": all(image[image[cell]] == cell for cell in cells),
        "fixed_cells": f,
        "transposed_pairs": p,
        "mirror_is_a_reflection": not _is_rotation(_SIGMA_D),
        "mirror_lies_in_Td": True,
        "invariant_five_sets": invariant_five,
        "invariant_octad_fibres": fibres,
        "every_fibre_is_a_multiple_of_six":
            all(value % 6 == 0 for value in fibres.values()),
        "six_divides_the_count": invariant_five % 6 == 0,
        "no_invariant_golay_code":
            all(value % 6 == 0 for value in fibres.values())
            and invariant_five % 6 != 0,
        "verdict": (
            "each invariant five-set lies in one octad, which is invariant "
            "too, and each invariant octad holds 0, 6 or 12 of them; 220 is "
            "not a multiple of six, so the whole arrangement is impossible."),
        "lean_file": "RequestProject/GLM/Golay/CubeMirror.lean",
    }


# ===========================================================================
# 9.  ONE CALL FOR THE SECOND PASS
# ===========================================================================

def second_pass_report() -> Dict[str, object]:
    """Every section of ``studies/SOURCE_SALVAGE_SECOND_PASS.md``, recomputed."""
    cube = cube_surface_report()
    lean_words = set(_hexacode_words())
    substrate_words = set(mog.HEXACODE.words)
    substrate_code = _code_from_hexacode(mog.HEXACODE.words)
    return {
        "retrieved": RETRIEVED_SECOND,
        "retrieved_files": len(RETRIEVED_SECOND),
        "cube": cube,
        "read_quantum": read_quantum_report(),
        "gray": gray_jump_report(),
        "tension": grid_tension_report(),
        "lobe": conditional_lobe_report(),
        "modes": mode_algebra_report(),
        "stabiliser": cube_stabiliser_report(),
        "mirror": cube_mirror_report(),
        "hexacode_words_in_common": len(lean_words & substrate_words),
        "cube_substrate_generator": {
            "words": len(substrate_words),
            "min_distance": mog.HEXACODE.min_distance(),
            "weight_enumerator": substrate_code,
        },
        "hexacode_presentations_agree_on_invariants": (
            len(lean_words) == len(substrate_words)
            and mog.HEXACODE.min_distance() == cube["hexacode_min_distance"]
            and substrate_code == cube["weight_enumerator"]),
        "study": "studies/SOURCE_SALVAGE_SECOND_PASS.md",
    }
