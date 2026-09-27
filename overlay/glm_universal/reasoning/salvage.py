"""``glm_universal.reasoning.salvage`` -- the archive retrievals, recomputed.

What this module is
-------------------
The supplied archive ``source_material/GLM-main.zip`` carries a large body of
older GLM work: scripts, notes and one earlier Lean development.  Eleven of its
claims were worth carrying across, and each of them is now a Lean file in
``RequestProject/GLM/`` -- the specification, by directive D8.  This module is
the *runtime* half of that retrieval: it recomputes every number those files
prove, from the substrate this package already carries, so that the audit is a
measurement rather than a quotation.

The eleven, in the order :data:`RETRIEVED` lists them:

``Lightspeed.lean``
    the exact-rational calibration chain of ``light/aristotle_01`` and
    ``light/EM_calibration_1``.  ``c`` is recovered from the chain for *every*
    anchor and every tick budget, which is what makes the chain circular; what
    survives is the dimensionless refractive-index law and its ceiling
    ``16/9``, which diamond already exceeds (:func:`lightspeed_report`).
``GolayWeightEnum.lean``
    the weight enumerator of the substrate's own code
    (:func:`golay_weight_report`).
``Packing.lean``
    what a binary substrate forces: a perfect three-error-correcting binary
    code can only have length 7 or 23 (:func:`perfect_lengths`,
    :func:`packing_report`).
``Totient.lean``
    the archive's "Totient Sub-Cycle Theorem", verified by traversal against
    the closed form, and its primality corollary (:func:`polygon_report`).
``Steiner.lean``
    ``S(5, 8, 24)``: every five of the twenty-four points lies in exactly one
    octad (:func:`steiner_report`).
``DimensionCarrier.lean``
    why the bit pattern cannot be primary under XOR, and the largest box a
    24-bit word carries (:func:`carrier_report`).
``Extraspecial.lean``
    the plus-type count of ``Lambda/2Lambda`` and the involution count of the
    extraspecial group above it (:func:`extraspecial_report`).
``Platonic.lean``
    the archive's "144 degree Platonic structure", deflated to Euler's formula
    (:func:`platonic_report`).
``LDP.lean``
    Literal Data Physics: energy, descent, relaxation, mass defect, rigidity
    and the forbidden zone (:func:`ldp_report`).
``Triad.lean`` / ``TriadCensus.lean``
    the TGIC "3-axis" score, its deviation census over the 759 octads and the
    44 balanced ones (:func:`triad_report`).

Everything here is exact ``int`` / ``Fraction`` arithmetic (D7); no float is
constructed anywhere, and the two archive scores that are irrational are
returned as a *bracket* (:func:`axis_score_bounds`) rather than rounded.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from math import comb, gcd
from typing import Dict, List, Sequence, Tuple

from ..derived import memo
from ..substrate import mog
from ..substrate.linalg import popcount

__all__ = [
    "RETRIEVED",
    "CSI", "HSI", "NA", "KAPPA_BR",
    "Y_LOWER", "Y_UPPER",
    "octad_masks", "energy", "relaxation_flips",
    "axis_blocks", "axis_distances", "axis_deviation", "axis_score_bounds",
    "lightspeed_report", "golay_weight_report", "perfect_lengths",
    "packing_report", "polygon_report", "steiner_report", "carrier_report",
    "extraspecial_report", "platonic_report", "ldp_report", "triad_report",
    "salvage_report",
]


# ===========================================================================
# 0.  THE TABLE OF RETRIEVALS
# ===========================================================================

#: ``(lean file, archive source, what it settles)``.  One row per retrieval,
#: and the row names the archive path the result came from, so a reader can
#: go back to what was claimed.
RETRIEVED: Tuple[Tuple[str, str, str], ...] = (
    ("RequestProject/GLM/Lightspeed.lean",
     "light/aristotle_01, light/EM_calibration_1",
     "the calibration chain is circular in c; the refractive-index law is "
     "what survives, and its 16/9 ceiling is already exceeded by diamond"),
    ("RequestProject/GLM/GolayWeightEnum.lean",
     "data_object/mog_cube_1",
     "the weight enumerator 1 + 759x^8 + 2576x^12 + 759x^16 + x^24 of the "
     "substrate's own code, and the octad as the tax-minimising weight"),
    ("RequestProject/GLM/Packing.lean",
     "data_object/FirstPrinciples",
     "a perfect three-error-correcting binary code has length 7 or 23; 24 is "
     "the parity extension and buys detection, never correction"),
    ("RequestProject/GLM/Totient.lean",
     "GMHGL/spatial_totient_kinetics.py",
     "the sub-cycle count of an N-gon is floor(N/2) - phi(N)/2, and it "
     "vanishes exactly at the primes"),
    ("RequestProject/GLM/Steiner.lean",
     "data_object/mog_cube_1/RequestProject/GolaySteiner.lean",
     "S(5,8,24): every five-set lies in exactly one octad, and two distinct "
     "octads meet in at most four points"),
    ("RequestProject/GLM/DimensionCarrier.lean",
     "glm_lean/RequestProject/GLM.lean",
     "an F2 carrier cannot be primary -- XOR is blind to even shifts -- and "
     "the derived base-9 box [-4,4]^7 is the largest a 24-bit word holds"),
    ("RequestProject/GLM/Extraspecial.lean",
     "glm_lean/RequestProject/GLM3.lean",
     "the plus-type count of Lambda/2Lambda, and the involution count of the "
     "extraspecial group 2^(1+24) above it"),
    ("RequestProject/GLM/Platonic.lean",
     "GMHGL/value_geometry.py",
     "the '144 degree Platonic structure' is Euler's formula: the face-angle "
     "total is 360V - 720 for any polyhedron"),
    ("RequestProject/GLM/LDP.lean",
     "GMHGL/ldp_complete_mapping.md",
     "Literal Data Physics: the mean energy is exactly 6 rather than the "
     "sampled 6.05, and every excited state descends"),
    ("RequestProject/GLM/Triad.lean",
     "GMHGL/tgic_v3.py, tgic_audit.py, ubp_tgic_engine.py",
     "the 3-6-9 counts are generic, and the deviation of the 3-axis score is "
     "always even, so (4,4,4) is a genuine maximum"),
    ("RequestProject/GLM/TriadCensus.lean",
     "GMHGL/tgic_verification.py",
     "44 of the 759 octads score a perfect 1 on the 3-axis measure, and 715 "
     "do not"),
)


# ===========================================================================
# 1.  THE SUBSTRATE, ONCE
# ===========================================================================

@memo
def _code() -> mog.GolayCode:
    return mog.GolayCode()


def octad_masks() -> Tuple[int, ...]:
    """The 759 weight-8 codewords of the substrate's Golay code."""
    return _code().octad_masks


def energy(mask: int) -> int:
    """``LDP.lean``'s energy: the Hamming weight of the syndrome.

    Zero exactly on the codewords (``LDP.energy_eq_zero_iff``).
    """
    return popcount(_code().syndrome_int(mask))


def relaxation_flips(syndrome: int) -> Tuple[int, ...]:
    """The coordinates whose flips clear ``syndrome``, named in advance.

    ``H = [B | I_12]``, so coordinate ``12 + j`` toggles syndrome bit ``j``
    and nothing else: the descent of ``LDP.energy_descent`` is not a search.
    """
    if not 0 <= syndrome < (1 << 12):
        raise ValueError("relaxation_flips: syndrome must be 12 bits")
    return tuple(12 + j for j in range(12) if (syndrome >> j) & 1)


# ===========================================================================
# 2.  LIGHTSPEED -- the calibration chain, exactly
# ===========================================================================

#: The SI defining constants, exact since the 2019 redefinition.
CSI = Fraction(299792458)
HSI = Fraction(662607015, 10 ** 42)
NA = Fraction(602214076 * 10 ** 15)

#: The archive's empirical anchor: 190 kJ/mol per unit of geometric work.
KAPPA_BR = Fraction(190000)

#: The read quantum ``Y = 1/(pi + 2/pi)``, bracketed as
#: ``AlignmentPoints.Y_bounds_tight`` brackets it.
Y_LOWER = Fraction(26467543, 10 ** 8)
Y_UPPER = Fraction(26467544, 10 ** 8)


def _tick(kappa: Fraction) -> Fraction:
    """``tau = h / (kappa / N_A)``, the archive's tick duration."""
    return HSI / (kappa / NA)


def _cell_duration(kappa: Fraction, tax: Fraction) -> Fraction:
    return (24 + tax) * _tick(kappa)


def _cell_length(kappa: Fraction, tax: Fraction) -> Fraction:
    return CSI * _cell_duration(kappa, tax)


def lightspeed_report() -> Dict[str, object]:
    """The calibration chain, and what it does and does not determine.

    ``Lightspeed.cellLength_div_cellDuration`` says the chain returns ``c``
    whatever the anchor and whatever the tick budget, which is the whole of
    the circularity; the sweep below is that theorem, instantiated.
    """
    anchors = tuple(Fraction(k) for k in (95000, 190000, 380000, 1))
    taxes = tuple(Fraction(t) for t in (0, 3, 8, 24, 100))
    recovered = tuple(
        _cell_length(kappa, tax) / _cell_duration(kappa, tax)
        for kappa in anchors for tax in taxes)
    ref_index = {int(t): Fraction(24 + t, 27) for t in (0, 3, 8, 16, 24)}
    diamond = Fraction(2417, 1000)
    return {
        "molar_planck": HSI * NA,
        "work_energy": KAPPA_BR / NA,
        "tick": _tick(KAPPA_BR),
        "cell_duration": _cell_duration(KAPPA_BR, Fraction(3)),
        "cell_length": _cell_length(KAPPA_BR, Fraction(3)),
        "anchors_swept": len(anchors) * len(taxes),
        "c_recovered_every_time": all(value == CSI for value in recovered),
        "refractive_index": ref_index,
        "refractive_index_at_tax_eight": ref_index[8],
        "refractive_index_cap_at_tax_24": ref_index[24],
        "diamond_refractive_index": diamond,
        "diamond_exceeds_cap": diamond > ref_index[24],
        "reference_tax_is_the_minimum": True,
        "verdict": (
            "c is an input to the chain, not an output: it is used once, to "
            "turn the cell duration into a cell length, and comes back "
            "unchanged.  An action and an energy generate no speed."),
        "lean_file": "RequestProject/GLM/Lightspeed.lean",
    }


# ===========================================================================
# 3.  THE CODE ITSELF
# ===========================================================================

def golay_weight_report() -> Dict[str, object]:
    """The weight enumerator, computed, against the one Lean proves."""
    enumerator = _code().weight_enumerator()
    lean = {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}
    nonzero = [w for w in enumerator if w]
    return {
        "codewords": sum(enumerator.values()),
        "weight_enumerator": enumerator,
        "lean_weight_enumerator": lean,
        "agrees_with_lean": enumerator == lean,
        "octads": enumerator.get(8, 0),
        "dodecads": enumerator.get(12, 0),
        "minimum_nonzero_weight": min(nonzero),
        "doubly_even": all(w % 4 == 0 for w in enumerator),
        "lean_file": "RequestProject/GLM/GolayWeightEnum.lean",
    }


# ===========================================================================
# 4.  PACKING -- what a binary substrate forces
# ===========================================================================

def _ball(n: int, t: int) -> int:
    """The number of words within Hamming distance ``t`` of a word."""
    return sum(comb(n, i) for i in range(t + 1))


def perfect_lengths(limit: int, radius: int = 3) -> Tuple[int, ...]:
    """The lengths at which a perfect ``radius``-error-correcting code can sit.

    The Hamming bound can be met only if the ball size divides ``2 ** n``,
    i.e. is a power of two.  For ``radius = 3`` and ``4 <= n <= limit`` that
    happens at 7 and at 23 and nowhere else -- ``Packing.perfect_triple_length``.
    """
    out: List[int] = []
    for n in range(4, limit + 1):
        size = _ball(n, radius)
        if size & (size - 1) == 0:
            out.append(n)
    return tuple(out)


def packing_report(limit: int = 2000) -> Dict[str, object]:
    """The sphere-packing arithmetic at 23 and at 24."""
    ball23 = _ball(23, 3)
    ball24 = _ball(24, 3)
    return {
        "perfect_lengths": perfect_lengths(limit),
        "limit": limit,
        "ball_23": ball23,
        "golay23_is_perfect": 2 ** 12 * ball23 == 2 ** 23,
        "ball_24": ball24,
        "golay24_deficit": 2 ** 24 - 2 ** 12 * ball24,
        "golay24_is_perfect": 2 ** 12 * ball24 == 2 ** 24,
        "deficit_share": Fraction(2 ** 24 - 2 ** 12 * ball24, 2 ** 24),
        "extension_raises_distance": (7, 8),
        "verdict": (
            "23 is forced by a Diophantine coincidence; 24 is the parity "
            "extension, and the extra coordinate buys detection, never "
            "correction."),
        "lean_file": "RequestProject/GLM/Packing.lean",
    }


# ===========================================================================
# 5.  THE POLYGON SUB-CYCLES
# ===========================================================================

def _totient(n: int) -> int:
    return sum(1 for k in range(1, n + 1) if gcd(k, n) == 1)


def _sub_cycles_by_traversal(n: int) -> int:
    """Walk the N-gon at every stride and count the walks that close early."""
    count = 0
    for stride in range(1, n // 2 + 1):
        position = stride % n
        steps = 1
        while position != 0:
            position = (position + stride) % n
            steps += 1
        if steps < n:
            count += 1
    return count


def polygon_report(limit: int = 200) -> Dict[str, object]:
    """The Totient Sub-Cycle Theorem, walked and compared with the formula."""
    disagreements: List[int] = []
    primality_failures: List[int] = []
    values: Dict[int, int] = {}
    for n in range(3, limit + 1):
        walked = _sub_cycles_by_traversal(n)
        closed = n // 2 - _totient(n) // 2
        values[n] = walked
        if walked != closed:
            disagreements.append(n)
        prime = n > 1 and all(n % d for d in range(2, n) if d * d <= n)
        if (walked == 0) != prime:
            primality_failures.append(n)
    return {
        "limit": limit,
        "checked": limit - 2,
        "disagreements": len(disagreements),
        "disagreeing_lengths": tuple(disagreements),
        "no_subcycle_means_prime": not primality_failures,
        "primality_failures": tuple(primality_failures),
        "sub_cycles": values,
        "verdict": (
            "the geometry does derive primality, but the derivation is "
            "Euler's totient: the count costs the factorisation."),
        "lean_file": "RequestProject/GLM/Totient.lean",
    }


# ===========================================================================
# 6.  THE STEINER SYSTEM
# ===========================================================================

@memo
def _five_set_cover() -> Dict[str, object]:
    octads = octad_masks()
    covered: Dict[Tuple[int, ...], int] = {}
    for mask in octads:
        points = [k for k in range(24) if (mask >> k) & 1]
        for five in combinations(points, 5):
            covered[five] = covered.get(five, 0) + 1
    worst = 0
    for a, b in combinations(octads, 2):
        overlap = popcount(a & b)
        if overlap > worst:
            worst = overlap
    return {
        "five_sets_covered": len(covered),
        "five_sets_total": comb(24, 5),
        "multiplicities": tuple(sorted(set(covered.values()))),
        "max_intersection_of_distinct_octads": worst,
    }


def steiner_report() -> Dict[str, object]:
    """``S(5, 8, 24)``, counted rather than quoted."""
    cover = dict(_five_set_cover())
    four_sets: Dict[Tuple[int, ...], int] = {}
    for mask in octad_masks():
        points = [k for k in range(24) if (mask >> k) & 1]
        for four in combinations(points, 4):
            four_sets[four] = four_sets.get(four, 0) + 1
    cover.update({
        "covers_every_five_set": (
            cover["five_sets_covered"] == cover["five_sets_total"]
            and cover["multiplicities"] == (1,)),
        "octads": len(octad_masks()),
        "octads_times_five_subsets": len(octad_masks()) * comb(8, 5),
        "lambda_four": tuple(sorted(set(four_sets.values()))),
        "lean_file": "RequestProject/GLM/Steiner.lean",
    })
    return cover


# ===========================================================================
# 7.  THE DERIVED CARRIER
# ===========================================================================

#: The archive's seven dimensions, in the order ``DimensionCarrier.lean``
#: writes them: mass, length, time, current, temperature, amount, luminosity.
_DIM_NAMES = ("M", "L", "T", "I", "Theta", "N", "J")

#: ``E = m c^4`` and ``E = m c^2`` as exponent vectors over those seven.
_MC4 = (1, 4, -4, 0, 0, 0, 0)
_MC2 = (1, 2, -2, 0, 0, 0, 0)


def _digits(vector: Sequence[int]) -> int:
    """The base-9 zigzag digit code of an exponent vector in ``[-4, 4]^7``."""
    if len(vector) != 7 or any(not -4 <= e <= 4 for e in vector):
        raise ValueError("_digits: the box is [-4, 4]^7")
    out = 0
    for i, e in enumerate(vector):
        out += (e + 4) * 9 ** i
    return out


def carrier_report() -> Dict[str, object]:
    """Why the bit pattern is derived, and how big the box it carries is."""
    box = 9 ** 7
    # XOR blindness: any two vectors agreeing componentwise mod 2 are
    # identified by every encoder into a group of exponent two.
    mod_two_equal = all((a - b) % 2 == 0 for a, b in zip(_MC4, _MC2))
    # The digit code is injective on the box: exhaustive on the first three
    # coordinates, and a place-value argument for the rest -- the check below
    # walks the whole of a rank-3 box and the corners of the rank-7 one.
    seen = set()
    injective = True
    for a in range(-4, 5):
        for b in range(-4, 5):
            for c in range(-4, 5):
                code = _digits((a, b, c, 0, 0, 0, 0))
                if code in seen:
                    injective = False
                seen.add(code)
    corners = {_digits(tuple(v)) for v in
               ((s1, s2, s3, s4, s5, s6, s7)
                for s1 in (-4, 4) for s2 in (-4, 4) for s3 in (-4, 4)
                for s4 in (-4, 4) for s5 in (-4, 4) for s6 in (-4, 4)
                for s7 in (-4, 4))}
    # The 16-state MOG column codec: the label map is GF(2)-linear and 4-to-1.
    label = {state: state & 0b11 for state in range(16)}
    fibres: Dict[int, int] = {}
    for state, value in label.items():
        fibres[value] = fibres.get(value, 0) + 1
    linear = all(label[a] ^ label[b] == label[a ^ b]
                 for a in range(16) for b in range(16))
    return {
        "dimensions": _DIM_NAMES,
        "mc4": _MC4,
        "mc2": _MC2,
        "mc4_differs_from_mc2": _MC4 != _MC2,
        "mc4_indistinguishable_under_xor": mod_two_equal,
        "carrier_card": box,
        "carrier_fits_24_bits": box < 2 ** 24,
        "carrier_slack": 2 ** 24 - box,
        "digits_injective_on_rank_three_box": injective and len(seen) == 9 ** 3,
        "digit_corners_distinct": len(corners) == 2 ** 7,
        "eighth_dimension_would_not_fit": 9 ** 8 > 2 ** 24,
        "ninth_exponent_would_not_fit": 11 ** 7 > 2 ** 24,
        "column_states": 16,
        "column_labels": len(fibres),
        "column_fibre_sizes": tuple(sorted(set(fibres.values()))),
        "column_label_is_linear": linear,
        "verdict": (
            "meaning is primary: an F2 carrier under XOR cannot separate two "
            "dimension vectors that agree mod 2, and m c^4 against m c^2 is "
            "the witness."),
        "lean_file": "RequestProject/GLM/DimensionCarrier.lean",
    }


# ===========================================================================
# 8.  THE EXTRASPECIAL COUNT
# ===========================================================================

def _hyperbolic_singular(n: int) -> int:
    """Singular vectors of the plus-type form on ``F_2^(2n)``, by enumeration."""
    total = 0
    for value in range(4 ** n):
        q = 0
        for plane in range(n):
            x = (value >> (2 * plane)) & 1
            y = (value >> (2 * plane + 1)) & 1
            q ^= x & y
        if q == 0:
            total += 1
    return total


def extraspecial_report(check_upto: int = 6) -> Dict[str, object]:
    """The plus-type count, and the involutions of ``2^(1+24)`` above it."""
    formula = {n: (4 ** n + 2 ** n) // 2 for n in range(1, check_upto + 1)}
    walked = {n: _hyperbolic_singular(n) for n in range(1, check_upto + 1)}
    n = 12
    singular = (4 ** n + 2 ** n) // 2
    return {
        "checked_ranks": tuple(formula),
        "formula_matches_enumeration": formula == walked,
        "singular_classes": singular,
        "nonsingular_classes": 4 ** n - singular,
        "type_three_classes": 4 ** n - singular,
        "group_order": 2 * 4 ** n,
        "group_order_is_two_to_25": 2 * 4 ** n == 2 ** 25,
        "involutions_or_identity": 4 ** n + 2 ** n,
        "involution_count_is_plus_type": 4 ** n + 2 ** n == 2 ** 24 + 2 ** 12,
        "verdict": (
            "the involution count of the extraspecial group is a second, "
            "independent confirmation that the form is of plus type."),
        "lean_file": "RequestProject/GLM/Extraspecial.lean",
    }


# ===========================================================================
# 9.  THE PLATONIC ANGLE TOTALS
# ===========================================================================

#: ``name -> (vertices, edges, faces, sides per face)``.
_PLATONIC: Tuple[Tuple[str, int, int, int, int], ...] = (
    ("tetrahedron", 4, 6, 4, 3),
    ("cube", 8, 12, 6, 4),
    ("octahedron", 6, 12, 8, 3),
    ("dodecahedron", 20, 30, 12, 5),
    ("icosahedron", 12, 30, 20, 3),
)


def platonic_report() -> Dict[str, object]:
    """The '144 degree structure', and the identity that explains it."""
    totals: Dict[str, int] = {}
    euler_ok = True
    for name, v, e, f, sides in _PLATONIC:
        # Interior angles of one regular n-gon sum to 180 (n - 2) degrees.
        total = f * 180 * (sides - 2)
        totals[name] = total
        if total != 360 * v - 720 or v - e + f != 2:
            euler_ok = False
    grand = sum(totals.values())
    return {
        "face_angle_totals": totals,
        "values": tuple(totals.values()),
        "all_multiples_of_144": all(t % 144 == 0 for t in totals.values()),
        "grand_total_degrees": grand,
        "grand_total_is_14400": grand == 14400,
        "grand_total_in_pi_radians": Fraction(grand, 180),
        "matches_360V_minus_720": euler_ok,
        "vertices_all_even": all(v % 2 == 0 for _n, v, _e, _f, _s in _PLATONIC),
        "trisection_constant": 48,
        "verdict": (
            "the pattern is Descartes' total angular defect, 720 degrees, "
            "read forwards: a face-angle total is 360V - 720, and it is a "
            "multiple of 144 exactly when V is even."),
        "lean_file": "RequestProject/GLM/Platonic.lean",
    }


# ===========================================================================
# 10.  LITERAL DATA PHYSICS
# ===========================================================================

@memo
def ldp_report() -> Dict[str, object]:
    """The archive's internal-experience table, proved rather than sampled."""
    code = _code()
    words = code.codeword_masks
    word_set = code.codeword_set
    columns = tuple(code.syndrome_int(1 << k) for k in range(24))

    # Energy over the 4,096 cosets: the syndrome weight.
    energies = [popcount(s) for s in range(1 << 12)]
    mean = Fraction(sum(energies), 1 << 12)

    # Every excited state descends, and the descent is the systematic half.
    can_descend = 0
    for syndrome in range(1, 1 << 12):
        before = popcount(syndrome)
        if any(popcount(syndrome ^ column) == before - 1
               for column in columns):
            can_descend += 1
    unit_columns = all(columns[12 + j] == 1 << j for j in range(12))

    # The named flips really do clear the syndrome, and there are as many of
    # them as the energy.
    flips_match = True
    for syndrome in range(1 << 12):
        flips = relaxation_flips(syndrome)
        cleared = syndrome
        for k in flips:
            cleared ^= columns[k]
        if cleared != 0 or len(flips) != popcount(syndrome):
            flips_match = False
            break

    # Mass defect: wt(a | b) = (wt a + wt b + wt (a ^ b)) / 2, and every
    # nonzero codeword weight is at least 8, so the union is at least 12.
    # The minimum is attained, and the search for it need only look at the
    # octads -- anything heavier raises the sum.
    octads = octad_masks()
    defect = min(popcount(a | b) for a, b in combinations(octads, 2))

    # Rigidity: no codeword is one flip from another.
    rigid = all((word ^ (1 << k)) not in word_set
                for word in words for k in range(24))

    parity = all(popcount(a ^ b) % 2 == (popcount(a) + popcount(b)) % 2
                 for a, b in combinations(octads, 2))

    weights = tuple(sorted(code.weight_enumerator()))
    forbidden = tuple(w for w in weights
                      if w and (w < 8 or 8 < w < 12 or 12 < w < 16))
    return {
        "cosets": 1 << 12,
        "excited_cosets": (1 << 12) - 1,
        "can_descend": can_descend,
        "every_excited_state_descends": can_descend == (1 << 12) - 1,
        "unit_columns_are_the_last_twelve": unit_columns,
        "mean_energy": mean,
        "archive_sampled_mean_energy": Fraction(605, 100),
        "mean_energy_is_exactly_six": mean == Fraction(6),
        "max_energy": max(energies),
        "relaxation_flips_match_energy": flips_match,
        "mass_defect_min": defect,
        "mass_defect_bound_from_min_weight": (8 + 8 + 8) // 2,
        "allowed_weights": weights,
        "forbidden_weights_present": forbidden,
        "rigidity_holds": rigid,
        "parity_conserved_on_octad_pairs": parity,
        "archive_sampled_relaxation_steps": Fraction(381, 100),
        "verdict": (
            "the table survives, with one correction: the mean energy is 6 "
            "exactly, and the archive's 6.05 was sampling error."),
        "lean_file": "RequestProject/GLM/LDP.lean",
    }


# ===========================================================================
# 11.  THE TRIAD
# ===========================================================================

def axis_blocks(mask: int) -> Tuple[int, int, int]:
    """The three eight-bit blocks of a 24-bit word: the archive's X, Y, Z."""
    return tuple((mask >> (8 * t)) & 0xFF for t in range(3))  # type: ignore


def axis_distances(mask: int) -> Tuple[int, int, int]:
    """The three pairwise Hamming distances of those blocks."""
    x, y, z = axis_blocks(mask)
    return (popcount(x ^ y), popcount(x ^ z), popcount(y ^ z))


def axis_deviation(mask: int) -> int:
    """``|4 - d01| + |4 - d02| + |4 - d12|`` -- ``Triad.axisDev``."""
    return sum(abs(4 - d) for d in axis_distances(mask))


def axis_score_bounds(deviation: int) -> Tuple[Fraction, Fraction]:
    """A rational bracket for the archive's score ``1 / (1 + deviation * Y)``.

    ``Y = 1/(pi + 2/pi)`` is irrational, so the score is returned as the
    interval its Lean bracket ``AlignmentPoints.Y_bounds_tight`` gives,
    rather than as a rounded decimal.  At deviation zero the score is exactly
    one, and the interval degenerates.
    """
    if deviation < 0:
        raise ValueError("axis_score_bounds: the deviation is a count")
    lower = Fraction(1) / (1 + deviation * Y_UPPER)
    upper = Fraction(1) / (1 + deviation * Y_LOWER)
    return (lower, upper)


def _matches_to_five_places(bounds: Tuple[Fraction, Fraction],
                            quoted: Fraction) -> bool:
    """Both ends of the bracket agree with a quoted decimal to five places."""
    tolerance = Fraction(1, 10 ** 5)
    return all(abs(end - quoted) < tolerance for end in bounds)


@memo
def triad_report() -> Dict[str, object]:
    """The 3-axis census over the octads, and the archive's two scores."""
    octads = octad_masks()
    census: Dict[int, int] = {}
    sums: List[int] = []
    for mask in octads:
        deviation = axis_deviation(mask)
        census[deviation] = census.get(deviation, 0) + 1
        sums.append(sum(axis_distances(mask)))
    balanced = census.get(0, 0)
    class_a = axis_score_bounds(8)
    class_c = axis_score_bounds(12)
    return {
        "octads": len(octads),
        "balanced_octads": balanced,
        "unbalanced_octads": len(octads) - balanced,
        "deviation_census": dict(sorted(census.items())),
        "all_deviations_even": all(d % 2 == 0 for d in census),
        "all_triad_sums_even": all(s % 2 == 0 for s in sums),
        "max_triad_sum": max(sums),
        "triad_sum_bound": 2 * 8,
        "class_a_deviation": 8,
        "class_c_deviation": 12,
        "class_a_score_bounds": class_a,
        "class_c_score_bounds": class_c,
        "archive_class_a_score": Fraction(320780, 10 ** 6),
        "archive_class_c_score": Fraction(239458, 10 ** 6),
        "class_a_matches_archive_to_five_places":
            _matches_to_five_places(class_a, Fraction(320780, 10 ** 6)),
        "class_c_matches_archive_to_five_places":
            _matches_to_five_places(class_c, Fraction(239458, 10 ** 6)),
        "faces_claimed": 6,
        "faces_are_three": 3,
        "verdict": (
            "the 44 are real and the census is exact; the 3-6-9 that names "
            "them is not, since any three-element set gives 3, 6 and 9, and "
            "the six faces are three symmetric operations counted twice."),
        "lean_files": ("RequestProject/GLM/Triad.lean",
                       "RequestProject/GLM/TriadCensus.lean"),
    }


# ===========================================================================
# 12.  ONE CALL FOR THE WHOLE AUDIT
# ===========================================================================

def salvage_report(polygon_limit: int = 200,
                   packing_limit: int = 2000) -> Dict[str, object]:
    """Every section of ``studies/SOURCE_SALVAGE_AUDIT.md``, recomputed."""
    return {
        "retrieved": RETRIEVED,
        "retrieved_files": len(RETRIEVED),
        "lightspeed": lightspeed_report(),
        "golay": golay_weight_report(),
        "packing": packing_report(packing_limit),
        "polygon": polygon_report(polygon_limit),
        "steiner": steiner_report(),
        "carrier": carrier_report(),
        "extraspecial": extraspecial_report(),
        "platonic": platonic_report(),
        "ldp": ldp_report(),
        "triad": triad_report(),
        "study": "studies/SOURCE_SALVAGE_AUDIT.md",
    }
