"""``glm_universal.reasoning.harmony`` -- the harmonic register, measured.

The supplied study catalogue makes a universality claim: chemical equilibria,
musical harmony and market price discovery are all said to be proximity in the
Leech lattice.  ``reasoning/catalog.py`` has carried that claim as *not
implemented* because there was nothing musical to run it against.
:mod:`glm_universal.data_objects.harmonics` supplies the register -- 28
intervals as exact frequency ratios -- and this module is what tests the claim
rather than repeating it.

Five things are computed, all exactly, and none of them is a logarithm.

1. **Equal temperament, decided by integer comparison.**  For each interval,
   the 12-tone step it is nearest to and the exact rational
   ``(n/d)^12 / 2^k`` by which equal temperament misses it.  The fifth is
   missed by ``531441/524288`` -- the Pythagorean comma -- and the major third
   by far more, which is the whole history of keyboard tuning in two
   fractions.

2. **No cycle of fifths closes.**  ``(3/2)^n`` is never a power of two for
   ``n > 0``: checked here for every ``n`` up to a bound, and proved in
   general in ``RequestProject/GLM/Harmony.lean``, where the argument is
   unique factorisation rather than arithmetic on approximations.  The
   catalogue's phrase "the octave is closed" is therefore false of just
   intonation and true only of the tempered scale, and the two commas measure
   the difference exactly.

3. **Two orderings of consonance.**  Tenney height without the logarithm
   (``n * d``) and Euler's *gradus suavitatis* disagree; how much they agree
   is reported as an exact Kendall tau -- a rational, counted over all pairs,
   not estimated.

4. **The claim itself.**  Each interval is given a 24-coordinate *tuning
   vector* -- its exponents over 2, 3, 5, 7 and nothing else -- scaled and
   decoded to the nearest Leech point by the same exact decoder the rest of
   the package uses.  Two questions are then asked of the geometry, and both
   answers are counted rather than asserted: at which scale does the lattice
   stop conflating distinct intervals, and does distance from the unison's
   point order the intervals the way consonance does?

5. **What the verdict is.**  Reported as one of the four verdicts the claim
   ledgers use, with the statistic that decides it printed beside it.

Nothing here is sampled and no float is constructed.
"""

from __future__ import annotations

from functools import lru_cache

from fractions import Fraction
from typing import Dict, List, Mapping, Sequence, Tuple

from ..data_objects import harmonics as hm
from . import analogy

__all__ = [
    "CLAIM",
    "SCALES",
    "consonance_orderings",
    "fifth_never_closes",
    "harmony_report",
    "kendall_tau",
    "lattice_separation",
    "temperament_table",
    "tuning_vector",
]

#: The catalogue sentence this module exists to settle.
CLAIM = ("chemical equilibria, musical harmony and market price discovery "
         "all map to proximity in the Leech lattice")

#: The scales the tuning vectors are swept over before being decoded.  Powers
#: of two and the odd scale ``9`` that :mod:`.lean_address` settled on, so the
#: sweep can show what a scale below the covering radius costs.
SCALES: Tuple[int, ...] = (1, 2, 4, 8, 9, 16, 32)


# ===========================================================================
# 1.  EQUAL TEMPERAMENT
# ===========================================================================

def _error_magnitude(error: Fraction) -> Fraction:
    """How far from 1 a multiplicative error is, either side.

    ``max(e, 1/e)``, so a sharp miss and a flat miss of the same size compare
    equal, and the comparison is exact.
    """
    return error if error >= 1 else 1 / error


def temperament_table() -> Tuple[Dict[str, object], ...]:
    """Every interval against the equal step it is nearest to."""
    rows: List[Dict[str, object]] = []
    for interval in hm.interval_register():
        error = hm.tet_error(interval.ratio)
        rows.append({
            "name": interval.name,
            "ratio": interval.ratio,
            "step": hm.tet_step(interval.ratio),
            "error": error,
            "magnitude": _error_magnitude(error),
            "tempered": error == 1,
            "sharper": error > 1,
        })
    return tuple(rows)


def fifth_never_closes(bound: int = 200) -> Dict[str, object]:
    """``(3/2)^n`` is a power of two for no ``0 < n <= bound``.

    The check is exact: a power of two is a positive integer whose numerator
    has no factor of 3, and ``(3/2)^n = 3^n / 2^n`` is in lowest terms, so the
    numerator is ``3^n`` and the ratio is an integer power of two only when
    ``n = 0``.  Counted here, proved in ``Harmony.lean``.
    """
    closures = []
    for n in range(1, bound + 1):
        ratio = Fraction(3, 2) ** n
        numerator = ratio.numerator
        if numerator == 1 or (numerator & (numerator - 1)) == 0:
            closures.append(n)
    twelve = Fraction(3, 2) ** 12 / Fraction(2) ** 7
    return {
        "bound": bound,
        "closures": tuple(closures),
        "closes": bool(closures),
        "twelve_fifths_over_seven_octaves": twelve,
        "pythagorean_comma": twelve,
        "syntonic_comma": Fraction(81, 80),
        "four_fifths_over_major_third": (Fraction(3, 2) ** 4
                                         / (Fraction(2) ** 2 * Fraction(5, 4))),
    }


# ===========================================================================
# 2.  TWO ORDERINGS OF CONSONANCE
# ===========================================================================

def kendall_tau(left: Sequence[object],
                right: Sequence[object]) -> Fraction:
    """Exact Kendall tau-a between two rankings of the same items.

    ``(concordant - discordant) / pairs``, as a :class:`~fractions.Fraction`.
    Pairs tied in either sequence count as neither, which is the conservative
    reading: a statistic that cannot distinguish two items should not claim
    they agree.
    """
    if len(left) != len(right):
        raise ValueError("kendall_tau: the two rankings differ in length")
    size = len(left)
    pairs = size * (size - 1) // 2
    if pairs == 0:
        return Fraction(0)
    concordant = discordant = 0
    for i in range(size):
        for j in range(i + 1, size):
            a = (left[i] > left[j]) - (left[i] < left[j])
            b = (right[i] > right[j]) - (right[i] < right[j])
            if a * b > 0:
                concordant += 1
            elif a * b < 0:
                discordant += 1
    return Fraction(concordant - discordant, pairs)


def consonance_orderings() -> Dict[str, object]:
    """Tenney height against Euler's gradus, and how far they agree."""
    intervals = hm.interval_register()
    names = tuple(i.name for i in intervals)
    tenney = tuple(hm.product_complexity(i.ratio) for i in intervals)
    gradus = tuple(hm.euler_gradus(i.ratio) for i in intervals)
    tau = kendall_tau(tenney, gradus)
    by_tenney = tuple(n for _, n in sorted(zip(tenney, names)))
    by_gradus = tuple(n for _, n in sorted(zip(gradus, names)))
    return {
        "names": names,
        "tenney": tenney,
        "gradus": gradus,
        "tau": tau,
        "simplest_by_tenney": by_tenney[:5],
        "simplest_by_gradus": by_gradus[:5],
        "same_first_five": by_tenney[:5] == by_gradus[:5],
    }


# ===========================================================================
# 3.  THE LATTICE CLAIM
# ===========================================================================

def tuning_vector(interval: hm.Interval, scale: int = 1) -> Tuple[int, ...]:
    """The 24-coordinate vector an interval is decoded from.

    Its exponents over 2, 3, 5 and 7, scaled, and zero in the other twenty
    coordinates.  Deliberately *not* the register carrier: the carrier holds
    ``n * d`` and the gradus outright, so a distance computed from it would
    measure consonance by construction, and the claim being tested would be
    true by definition rather than by geometry.
    """
    exponents = interval.exponents
    head = [scale * exponents.get(p, 0) for p in (2, 3, 5, 7)]
    return tuple(head + [0] * 20)


def _distance2(left: Sequence[int], right: Sequence[int]) -> int:
    return sum((int(a) - int(b)) ** 2 for a, b in zip(left, right))


def _reordered_pairs(decoded: Sequence[int], raw: Sequence[int]) -> int:
    """Pairs the decoding puts in a different order than the raw vectors.

    Zero means the quantiser contributed nothing to the ordering: the lattice
    is then a change of coordinates, not a source of structure.
    """
    changed = 0
    for i in range(len(decoded)):
        for j in range(i + 1, len(decoded)):
            a = (decoded[i] > decoded[j]) - (decoded[i] < decoded[j])
            b = (raw[i] > raw[j]) - (raw[i] < raw[j])
            if a != b:
                changed += 1
    return changed


def lattice_separation(scales: Sequence[int] = SCALES) -> Dict[str, object]:
    """Decode every tuning vector at each scale, and count what survives.

    Reports, per scale: how many distinct lattice points the 28 intervals
    reach, how many collapse onto the unison's own point, and the exact
    Kendall tau between squared distance from the unison and each of the two
    consonance orderings.  A scale at which everything lands on one point
    tells the claim's story as clearly as one at which nothing does.
    """
    intervals = hm.interval_register()
    tenney = tuple(hm.product_complexity(i.ratio) for i in intervals)
    gradus = tuple(hm.euler_gradus(i.ratio) for i in intervals)
    # The control: the same vectors, *not* decoded.  Scaling every coordinate
    # by one factor cannot change the order of the distances, so this is one
    # number for the whole sweep, and it is what the lattice has to beat.
    raw = tuple(_distance2(tuning_vector(i, 1),
                           tuning_vector(intervals[0], 1))
                for i in intervals)
    control = {
        "tau_tenney": kendall_tau(raw, tenney),
        "tau_gradus": kendall_tau(raw, gradus),
        "distinct": len(set(raw)),
    }
    rows: List[Dict[str, object]] = []
    for scale in scales:
        points = []
        for interval in intervals:
            vector = [Fraction(v) for v in tuning_vector(interval, scale)]
            points.append(tuple(int(c) for c in
                                analogy.nearest_lattice_point(vector).point))
        origin = points[0]          # the unison, whose exponents are all zero
        distances = tuple(_distance2(p, origin) for p in points)
        rows.append({
            "scale": scale,
            "distinct_points": len({p for p in points}),
            "on_the_unison": sum(1 for p in points if p == origin),
            "max_distance2": max(distances),
            "tau_tenney": kendall_tau(distances, tenney),
            "tau_gradus": kendall_tau(distances, gradus),
            "reordered_pairs": _reordered_pairs(distances, raw),
        })
    best = max(rows, key=lambda r: (r["distinct_points"],
                                    r["tau_tenney"]))
    return {
        "scales": tuple(scales),
        "rows": tuple(rows),
        "interval_count": len(intervals),
        "best_scale": best["scale"],
        "best_distinct": best["distinct_points"],
        "best_tau_tenney": best["tau_tenney"],
        "best_tau_gradus": best["tau_gradus"],
        "best_reordered_pairs": best["reordered_pairs"],
        "control": control,
        "beats_control": (best["tau_tenney"] > control["tau_tenney"]
                          or best["tau_gradus"] > control["tau_gradus"]),
        "fully_separated": tuple(r["scale"] for r in rows
                                 if r["distinct_points"] == len(intervals)),
    }


def _verdict(separation: Mapping[str, object]) -> Dict[str, object]:
    """The claim's verdict, from the statistic rather than from taste.

    Three conditions, and the third is the one that decides it.

    * the lattice must **separate** the intervals -- each at its own point;
    * distance from the unison must **order** them, at a Kendall tau of at
      least ``1/2`` against one of the two consonance measures;
    * and it must do so **better than the control**, which is the same
      distance taken before the decoder is applied.

    The first two can hold for a reason that has nothing to do with the Leech
    lattice: a tuning vector's length already measures how many primes an
    interval spends, and so does Tenney height.  Only the third condition
    separates "maps to proximity in the Leech lattice" from "maps to proximity
    in Z^4, and was afterwards decoded".  Where the decoder reorders no pair,
    the claim is recorded as *not reproduced*: what was measured is real, and
    it is not what the sentence says.
    """
    separated = bool(separation["fully_separated"])
    tau = max(separation["best_tau_tenney"], separation["best_tau_gradus"])
    control = separation["control"]
    control_tau = max(control["tau_tenney"], control["tau_gradus"])
    ordered = tau >= Fraction(1, 2)
    beats_control = bool(separation["beats_control"])
    reordered = separation["best_reordered_pairs"]
    if separated and ordered and beats_control:
        verdict = "confirmed"
        because = ("the lattice separates every interval, orders them by "
                   "consonance, and does so better than the same distance "
                   "taken before the decoder")
    elif separated and ordered:
        verdict = "not reproduced"
        because = (f"proximity does order the intervals -- tau {tau} against "
                   f"consonance -- but the undecoded control orders them just "
                   f"as well ({control_tau}) with no lattice at all, and the "
                   f"decoder reorders {reordered} pairs, so what is measured "
                   f"is the prime-exponent vector rather than the geometry of "
                   f"the Leech lattice")
    else:
        verdict = "refuted"
        because = ("distance from the unison does not order the intervals by "
                   "either consonance measure")
    return {
        "claim": CLAIM,
        "separated": separated,
        "ordered": ordered,
        "best_tau": tau,
        "control_tau": control_tau,
        "beats_control": beats_control,
        "reordered_pairs": reordered,
        "threshold": Fraction(1, 2),
        "verdict": verdict,
        "because": because,
    }


# ===========================================================================
# 4.  THE REPORT
# ===========================================================================

@lru_cache(maxsize=None)
def harmony_report(scales: Sequence[int] = SCALES,
                   bound: int = 200) -> Dict[str, object]:
    """Everything above, in one exact dictionary."""
    table = temperament_table()
    # Commas are excluded from "how far equal temperament misses": their
    # nearest step is the unison, so the miss is the comma itself and says
    # nothing about temperament.  They are reported under ``closure``.
    scale_tones = tuple(r for r in table
                        if Fraction(1) <= r["ratio"] <= Fraction(2)
                        and not hm.interval_by_name(r["name"]).is_comma)
    worst = max(scale_tones, key=lambda r: r["magnitude"])
    best = min((r for r in scale_tones if r["ratio"] not in
                (Fraction(1), Fraction(2))),
               key=lambda r: r["magnitude"])
    separation = lattice_separation(scales)
    return {
        "register": dict(hm.register_summary()),
        "temperament": {
            "rows": table,
            "tempered_exactly": tuple(r["name"] for r in table
                                      if r["tempered"]),
            "worst_missed": worst["name"],
            "worst_error": worst["error"],
            "best_missed": best["name"],
            "best_error": best["error"],
            "fifth_error": hm.tet_error(Fraction(3, 2)),
            "third_error": hm.tet_error(Fraction(5, 4)),
        },
        "closure": fifth_never_closes(bound),
        "consonance": consonance_orderings(),
        "lattice": separation,
        "verdict": _verdict(separation),
    }
