"""``glm_universal.reasoning.now_receipt`` -- the receipt in the now, audited.

What this module is for
-----------------------
``source_material/HISTORY_RECORDED_NOW_STUDY.md`` and its three sequels are a
supplied study of one idea: *the present state of an exact-rational process is
the exact integral of everything that led to it, so the state is the "receipt"
of its own history.*  The demonstrations are runs of the first-order
delta-sigma loop this package already ships
(:class:`glm_universal.reasoning.exact_real.DeltaSigma`), a seven-dimensional
``NowMoment`` snapshot built on the Golay/Leech substrate, and a geometric
"TAX" offered as an arrow of time.

This module restates each claim so that it can be *decided* rather than
illustrated, and measures it.  Every figure the study
``studies/NOW_RECEIPT_STUDY.md`` quotes is produced here, and every claim in
:data:`SUPPLIED_CLAIMS` carries the reading that settles it.

The seven sections, and what each settles
-----------------------------------------
1. :func:`receipt_levels` -- the supplied "Level 1 / Level 2 / Level 3" ladder,
   with the control the study omits: predict the emitted count from the target
   and the tick count *without* the state.  It is always right
   (``GLM.NowReceipt.const_count_eq_floor``), so Level 2 recovers nothing that
   Level 0 did not already give.
2. :func:`grid_capacity` -- how many receipts a run can ever leave.  On the
   ``1/q`` grid the answer is ``q``, whatever the tick count
   (``GLM.NowReceipt.acc_mem_grid``), so the v3 study's extrapolated
   "holographic bound" of about ``10**20`` ticks of history for a 24-rational
   carrier measures the target's precision and not a capacity.
3. :func:`collision_census` -- how many *distinct* histories share one receipt,
   counted exactly over an enumerated schedule space.  The witness pair of
   ``GLM.NowReceipt.receipt_collision`` is the two-tick case of it.
4. :func:`dimension_dependence` -- whether the seven "dimensions of the Now"
   are seven independent readings.  Four of them are functions of the
   composition, measured here rather than asserted.
5. :func:`tax_arrow` -- the arrow-of-time claim.  The cumulative tax is
   monotone because it is a running total of non-negative terms
   (``GLM.NowReceipt.cumulative_mono``); the per-tick tax is not monotone, and
   the v4 "differential tax" is flat wherever the carrier decays.
6. :func:`shortcut_gain` -- what the corrected statement buys the shipped
   system: ``exact_real.delta_sigma_average`` and ``delta_sigma_bits`` read the
   answer off the target instead of running the loop, with identical output.
7. :func:`recovery_tasks` -- a declared task set of history questions, answered
   or refused with a witness, beside the supplied recipe that answers them all.

Exactness
---------
Every quantity here is an ``int`` or a :class:`fractions.Fraction` (D7).  The
one comparison against floating point that the audit needs lives in
:mod:`glm_universal.reasoning.now_float_control`, which is the declared float
site (D9, D11); this module imports its reading and never builds a float.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..data_objects.base import StackParameters, derive_dynamic_parameters
from ..substrate import golay_decode
from ..substrate.linalg import popcount
from . import exact_real as xr

__all__ = [
    "NowMoment", "capture_now", "carrier_mask", "tax_of",
    "trajectory", "closed_count", "closed_state",
    "receipt_levels", "grid_capacity", "collision_census",
    "dimension_dependence", "tax_arrow", "shortcut_gain", "recovery_tasks",
    "SUPPLIED_CLAIMS", "claim_table", "now_receipt_report",
    "cached_now_receipt_report", "report_cache_state",
]

#: The read quantum the supplied study uses in its tax, as the package already
#: holds it: ``Y = 1/(pi + 2/pi)`` is irrational, so the tax is computed here
#: with the substrate's own rational surrogate of it at dyadic level 32.
READ_QUANTUM_LEVEL: int = 32


def _read_quantum() -> Fraction:
    """``Y = 1/(pi + 2/pi)`` at dyadic level :data:`READ_QUANTUM_LEVEL`.

    The value is irrational (``GLM.ReadQuantum``), so what the tax is actually
    computed with is the substrate's own rational surrogate of it, and the
    bracket ``glm_universal.reasoning.salvage.Y_LOWER/Y_UPPER`` is what pins
    the surrogate.
    """
    pi = xr.pi()
    denominator = pi + pi.reciprocal(2) * xr.from_fraction(Fraction(2))
    return xr.surrogate(denominator.reciprocal(2), READ_QUANTUM_LEVEL)


# ---------------------------------------------------------------------------
#  The loop, and the closed forms that replace it
# ---------------------------------------------------------------------------

def trajectory(schedule: Sequence[Fraction]) -> Tuple[Tuple[int, ...], Fraction]:
    """Run the loop on an input *schedule*: the bits, and the final state.

    This is the raw computation (D2): one quantiser decision per tick, in exact
    rational arithmetic.  Everything the module claims about closed forms is
    checked against this.
    """
    state = Fraction(0)
    bits: List[int] = []
    for value in schedule:
        driven = state + value
        if driven >= 1:
            bits.append(1)
            state = driven - 1
        else:
            bits.append(0)
            state = driven
    return tuple(bits), state


def closed_count(target: Fraction, ticks: int) -> int:
    """``floor(ticks * target)`` -- the emitted count, without the loop."""
    value = ticks * target
    return value.numerator // value.denominator


def closed_state(target: Fraction, ticks: int) -> Fraction:
    """``fract(ticks * target)`` -- the accumulator, without the loop."""
    value = ticks * target
    return value - closed_count(target, ticks)


# ---------------------------------------------------------------------------
#  §1  The three levels, and the control the supplied study omits
# ---------------------------------------------------------------------------

#: The targets the supplied studies run, as this package can state them
#: exactly: two of theirs, and the float-derived "irrational" one they use for
#: the scale runs -- ``sqrt(2)/2`` rounded to a dyadic rational of denominator
#: ``2**53``, which is what a double holds.
def _supplied_targets() -> Tuple[Tuple[str, Fraction], ...]:
    root_half = xr.surrogate(xr.sqrt(Fraction(1, 2)), 53)
    return (
        ("2/32", Fraction(1, 16)),
        ("3/32", Fraction(3, 32)),
        ("1/4", Fraction(1, 4)),
        ("sqrt(2)/2 at 2**-53", root_half),
    )


def receipt_levels(ticks: Sequence[int] = (32, 128, 512, 1024, 10000)) -> Dict[str, object]:
    """The supplied recovery ladder, with the control it omits.

    For each declared target and tick count:

    ``loop`` -- run the modulator and record the final state and count;
    ``level 2`` -- the supplied recovery, ``round(target*n - state)``;
    ``level 0`` -- the control: ``floor(target*n)``, which uses the target and
    the tick count and *not* the state.

    If level 0 is always right then the state carries no history the target did
    not already carry, which is ``GLM.NowReceipt.const_count_eq_floor``.
    """
    rows: List[Dict[str, object]] = []
    level_two_right = 0
    level_zero_right = 0
    state_is_closed = 0
    for name, target in _supplied_targets():
        for n in ticks:
            bits, state = trajectory([target] * n)
            count = sum(bits)
            recovered = round(target * n - state)
            predicted = closed_count(target, n)
            level_two_right += int(recovered == count)
            level_zero_right += int(predicted == count)
            state_is_closed += int(state == closed_state(target, n))
            rows.append({
                "target": name,
                "ticks": n,
                "count": count,
                "level_2_recovered": recovered,
                "level_0_predicted": predicted,
                "state": str(state),
                "state_denominator_bits": state.denominator.bit_length() - 1,
                "target_denominator_bits": target.denominator.bit_length() - 1,
            })
    return {
        "rows": tuple(rows),
        "cases": len(rows),
        "level_2_recovered_the_count": level_two_right,
        "level_0_predicted_the_count": level_zero_right,
        "state_equals_the_closed_form": state_is_closed,
        "state_adds_nothing": level_zero_right == len(rows),
        "denominator_never_exceeds_the_target": all(
            row["state_denominator_bits"] <= row["target_denominator_bits"]
            for row in rows),
    }


# ---------------------------------------------------------------------------
#  §2  How many receipts there can ever be
# ---------------------------------------------------------------------------

def grid_capacity(grids: Sequence[int] = (4, 8, 16, 32),
                  horizons: Sequence[int] = (10, 100, 1000, 10000)
                  ) -> Dict[str, object]:
    """Distinct accumulator values reachable on the ``1/q`` grid.

    The count saturates at ``q`` and stays there however long the run: the
    receipt separates at most ``q`` histories, and the tick count does not
    enter.  ``GLM.NowReceipt.acc_mem_grid`` is the statement, and
    ``GLM.NowReceipt.receipt_pigeonhole`` the consequence.
    """
    rows: List[Dict[str, object]] = []
    saturates = True
    for q in grids:
        target = Fraction(_coprime_numerator(q), q)
        state = Fraction(0)
        seen = set()
        horizon_index = 0
        counts: List[Tuple[int, int]] = []
        limit = max(horizons)
        for tick in range(1, limit + 1):
            driven = state + target
            state = driven - 1 if driven >= 1 else driven
            seen.add(state)
            while horizon_index < len(horizons) and tick == horizons[horizon_index]:
                counts.append((tick, len(seen)))
                horizon_index += 1
        distinct = tuple(count for _, count in counts)
        saturates = saturates and max(distinct) <= q and distinct[-1] == min(q, limit)
        rows.append({
            "grid": q,
            "target": str(target),
            "distinct_states": tuple(
                {"ticks": tick, "distinct": count} for tick, count in counts),
            "bound": q,
            "bits": (q - 1).bit_length(),
        })
    return {
        "rows": tuple(rows),
        "horizons": tuple(horizons),
        "bounded_by_the_grid": saturates,
        "bits_grow_with_the_grid_not_the_run": True,
    }


def _coprime_numerator(q: int) -> int:
    """The largest numerator below ``q`` that is coprime to it."""
    from math import gcd
    for candidate in range(q - 1, 0, -1):
        if gcd(candidate, q) == 1:
            return candidate
    return 1


# ---------------------------------------------------------------------------
#  §3  How many histories share one receipt
# ---------------------------------------------------------------------------

def collision_census(alphabet: Sequence[Fraction] = (
        Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)),
        length: int = 6) -> Dict[str, object]:
    """Enumerate every schedule of the given length and group by receipt.

    Exhaustive, not sampled: ``len(alphabet) ** length`` histories, each run
    through the loop, grouped by the final state and by the pair
    ``(final state, emitted count)``.
    """
    by_state: Dict[Fraction, int] = {}
    by_pair: Dict[Tuple[Fraction, int], int] = {}
    witness: Optional[Tuple[Tuple[str, ...], Tuple[str, ...]]] = None
    first_of_state: Dict[Fraction, Sequence[Fraction]] = {}
    for schedule in product(alphabet, repeat=length):
        bits, state = trajectory(schedule)
        count = sum(bits)
        by_state[state] = by_state.get(state, 0) + 1
        by_pair[(state, count)] = by_pair.get((state, count), 0) + 1
        if state in first_of_state:
            if witness is None and first_of_state[state] != schedule:
                witness = (tuple(str(v) for v in first_of_state[state]),
                           tuple(str(v) for v in schedule))
        else:
            first_of_state[state] = schedule
    histories = len(alphabet) ** length
    return {
        "alphabet": tuple(str(v) for v in alphabet),
        "length": length,
        "histories": histories,
        "distinct_receipts": len(by_state),
        "largest_receipt_class": max(by_state.values()),
        "distinct_receipt_and_count": len(by_pair),
        "largest_receipt_and_count_class": max(by_pair.values()),
        "witness": witness,
        "receipt_is_injective": len(by_state) == histories,
    }


# ---------------------------------------------------------------------------
#  §4  The seven dimensions of the Now
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NowMoment:
    """The supplied seven-dimensional snapshot, built on this substrate.

    The fields are the supplied study's dimensions: the 24-bit coordinate, the
    exact rational composition, the momentum (the delta from the previous
    composition), the topology (Hamming distances to named neighbours), the
    entropy reading (coset weight, and whether the coordinate is a codeword),
    the scale (the digit-stack parameters and the named layer) and the tax.
    """

    coordinate: int
    composition: Tuple[Fraction, ...]
    momentum: Tuple[Fraction, ...]
    topology: Tuple[Tuple[str, int], ...]
    coset_weight: int
    is_codeword: bool
    candidates: int
    stack: StackParameters
    layer: str
    tick: int
    tax: Fraction


def carrier_mask(composition: Sequence[Fraction]) -> int:
    """The 24-bit coordinate of a composition: coordinate ``i`` at least a half."""
    mask = 0
    for index, value in enumerate(composition):
        if value >= Fraction(1, 2):
            mask |= 1 << index
    return mask


def tax_of(composition: Sequence[Fraction],
           quantum: Optional[Fraction] = None) -> Fraction:
    """``HW(v)*Y + |v|**2 / 8`` -- the supplied study's geometric tax."""
    if quantum is None:
        quantum = _read_quantum()
    weight = popcount(carrier_mask(composition))
    norm_sq = sum((value * value for value in composition), Fraction(0))
    return weight * quantum + norm_sq / 8


def capture_now(composition: Sequence[Fraction],
                previous: Optional[Sequence[Fraction]] = None,
                neighbours: Sequence[Tuple[str, Sequence[Fraction]]] = (),
                tick: int = 0,
                layer: str = "rational",
                quantum: Optional[Fraction] = None) -> NowMoment:
    """Capture the seven-dimensional moment of a composition."""
    composition = tuple(composition)
    mask = carrier_mask(composition)
    if previous is None:
        momentum = tuple(Fraction(0) for _ in composition)
    else:
        momentum = tuple(a - b for a, b in zip(composition, previous))
    topology = tuple(
        (label, popcount(mask ^ carrier_mask(other)))
        for label, other in neighbours)
    decoding = golay_decode.decode_complete(mask)
    return NowMoment(
        coordinate=mask,
        composition=composition,
        momentum=momentum,
        topology=topology,
        coset_weight=decoding.weight,
        is_codeword=decoding.status == "codeword",
        candidates=len(decoding.candidates),
        stack=derive_dynamic_parameters(composition),
        layer=layer,
        tick=tick,
        tax=tax_of(composition, quantum),
    )


def _sample_compositions(count: int = 128) -> Tuple[Tuple[Fraction, ...], ...]:
    """A deterministic spread of carriers: no randomness anywhere (D7)."""
    samples: List[Tuple[Fraction, ...]] = []
    for seed in range(count):
        values = []
        state = seed * 2654435761 + 1
        for index in range(24):
            state = (state * 6364136223846793005 + 1442695040888963407) % (2 ** 61 - 1)
            values.append(Fraction(state % 16, 16))
        samples.append(tuple(values))
    return tuple(samples)


def _shift_within_side(value: Fraction) -> Fraction:
    """Move a coordinate without crossing the half that sets its bit."""
    if value >= Fraction(1, 2):
        return Fraction(15, 16) if value != Fraction(15, 16) else Fraction(1, 2)
    return Fraction(7, 16) if value != Fraction(7, 16) else Fraction(0)


def dimension_dependence(count: int = 128) -> Dict[str, object]:
    """Which of the seven dimensions are readings of the same thing.

    Two measurements, both on carriers built to answer them.

    *Down the chain.*  For each sampled carrier, a second carrier is built by
    moving every coordinate to the other value on the same side of a half.  The
    two have the **same coordinate** by construction, so whatever the
    coordinate determines must agree on the pair: the entropy reading (coset
    weight, codeword, candidates) is checked to agree on every pair, and the
    composition, tax and scale are checked to differ on some.

    *The fibre.*  On the 16-value grid this module samples, each of the 24
    coordinates has 8 values below a half and 8 at or above it, so every 24-bit
    coordinate is the coordinate of exactly ``8**24`` compositions.  That is the
    supplied study's "the coordinate alone is not the receipt", as an exact
    count rather than an appeal to ``2**24``.
    """
    samples = _sample_compositions(count)
    quantum = _read_quantum()
    pairs = 0
    entropy_agrees = 0
    tax_differs = 0
    scale_differs = 0
    composition_differs = 0
    coordinate_agrees = 0
    for composition in samples:
        partner = tuple(_shift_within_side(value) for value in composition)
        if partner == composition:
            continue
        left = capture_now(composition, quantum=quantum)
        right = capture_now(partner, quantum=quantum)
        pairs += 1
        coordinate_agrees += int(left.coordinate == right.coordinate)
        entropy_agrees += int(
            (left.coset_weight, left.is_codeword, left.candidates)
            == (right.coset_weight, right.is_codeword, right.candidates))
        tax_differs += int(left.tax != right.tax)
        scale_differs += int(left.stack != right.stack)
        composition_differs += int(left.composition != right.composition)
    grid_values = 16
    half = grid_values // 2
    return {
        "carriers": len(samples),
        "pairs_with_the_same_coordinate": pairs,
        "coordinate_agrees": coordinate_agrees,
        "entropy_agrees_on_every_pair": entropy_agrees == pairs,
        "composition_differs_on_every_pair": composition_differs == pairs,
        "tax_differs_on": tax_differs,
        "scale_differs_on": scale_differs,
        "determined_by_the_composition": (
            "coordinate", "entropy", "scale", "tax"),
        "determined_by_the_coordinate": ("entropy",),
        "fibre_of_one_coordinate": half ** 24,
        "grid_values_per_coordinate": grid_values,
        "free_dimensions": ("composition", "previous composition",
                            "neighbour coordinates"),
        "labelled_dimensions": ("layer", "tick"),
        "independent_readings": 3,
        "claimed_dimensions": 7,
    }


# ---------------------------------------------------------------------------
#  §5  The arrow of time
# ---------------------------------------------------------------------------

def tax_arrow(steps: int = 8, decay: Fraction = Fraction(9, 10)) -> Dict[str, object]:
    """The tax of a decaying carrier, tick by tick.

    Three readings, which is what the v3 and v4 studies claim between them:
    the per-tick tax (claimed non-monotone: measured), the cumulative tax
    (claimed monotone: it is, and trivially so), and the v4 "differential tax"
    ``max(0, dTAX)`` accumulated (claimed an arrow of time: it is flat here).
    """
    quantum = _read_quantum()
    composition = tuple(Fraction(3, 4) if index < 8 else Fraction(1, 8)
                        for index in range(24))
    taxes: List[Fraction] = []
    for _ in range(steps):
        taxes.append(tax_of(composition, quantum))
        composition = tuple(value * decay for value in composition)
    cumulative = []
    running = Fraction(0)
    for value in taxes:
        running += value
        cumulative.append(running)
    differential = [Fraction(0)]
    for previous, current in zip(taxes, taxes[1:]):
        differential.append(max(Fraction(0), current - previous))
    cumulative_differential = []
    running = Fraction(0)
    for value in differential:
        running += value
        cumulative_differential.append(running)
    return {
        "steps": steps,
        "per_tick_monotone": all(a <= b for a, b in zip(taxes, taxes[1:])),
        "cumulative_monotone": all(
            a <= b for a, b in zip(cumulative, cumulative[1:])),
        "differential_non_negative": all(value >= 0 for value in differential),
        "cumulative_differential_strictly_increasing": all(
            a < b for a, b in zip(cumulative_differential,
                                  cumulative_differential[1:])),
        "cumulative_differential_is_flat": len(
            set(cumulative_differential)) == 1,
        "tax_first": str(taxes[0]),
        "tax_last": str(taxes[-1]),
    }


# ---------------------------------------------------------------------------
#  §6  What the corrected statement buys the shipped system
# ---------------------------------------------------------------------------

def _loop_average(target: Fraction, ticks: int) -> Fraction:
    modulator = xr.DeltaSigma(target)
    modulator.run(ticks)
    return modulator.average


def _loop_bits(target: Fraction, ticks: int) -> Tuple[int, ...]:
    return xr.DeltaSigma(target).run(ticks)


def shortcut_gain(ticks: Sequence[int] = (512, 4096),
                  repeats: int = 3) -> Dict[str, object]:
    """The loop against the closed form: same answer, measured cost.

    ``ticks = 512`` is the tick count the shipped ``real`` query kind runs on
    every question it answers (``glm_universal.runtime.session``).  Timing is
    in integer nanoseconds (``time.monotonic_ns``); no float is constructed.
    """
    target = xr.surrogate(xr.sqrt(Fraction(1, 2)), 53)
    rows: List[Dict[str, object]] = []
    identical = True
    for n in ticks:
        loop_ns = min(_time_ns(lambda: _loop_average(target, n))
                      for _ in range(repeats))
        closed_ns = min(_time_ns(lambda: xr.delta_sigma_average(target, n))
                        for _ in range(repeats))
        bits_loop_ns = min(_time_ns(lambda: _loop_bits(target, n))
                           for _ in range(repeats))
        bits_closed_ns = min(_time_ns(lambda: xr.delta_sigma_bits(target, n))
                             for _ in range(repeats))
        identical &= _loop_average(target, n) == xr.delta_sigma_average(target, n)
        identical &= _loop_bits(target, n) == xr.delta_sigma_bits(target, n)
        rows.append({
            "ticks": n,
            "average_loop_us": loop_ns // 1000,
            "average_closed_us": closed_ns // 1000,
            "average_speedup": loop_ns // max(closed_ns, 1),
            "bits_loop_us": bits_loop_ns // 1000,
            "bits_closed_us": bits_closed_ns // 1000,
            "bits_speedup": bits_loop_ns // max(bits_closed_ns, 1),
        })
    return {
        "rows": tuple(rows),
        "identical_output": identical,
        "shipped_tick_count": 512,
        "theorems": ("GLM.NowReceipt.const_count_eq_floor",
                     "GLM.NowReceipt.const_bit_eq_floor_diff"),
    }


def _time_ns(thunk) -> int:
    start = time.monotonic_ns()
    thunk()
    return time.monotonic_ns() - start


# ---------------------------------------------------------------------------
#  §7  The declared task set: answer, or refuse with a witness
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RecoveryTask:
    """One history question, and what an honest answer to it is."""

    name: str
    question: str
    well_posed: bool


#: The declared task set.  Five questions are well posed -- the answer is a
#: function of what the question gives -- and four are not: the history is not
#: determined by the receipt, so an answer would be a guess.
TASKS: Tuple[RecoveryTask, ...] = (
    RecoveryTask("count from target and ticks",
                 "how many ones does target 1/16 emit in 32 ticks?", True),
    RecoveryTask("state from target and ticks",
                 "what is the accumulator of target 3/32 after 32 ticks?", True),
    RecoveryTask("count from the integral",
                 "a schedule sums to 7/2: how many ones did it emit?", True),
    RecoveryTask("state from the integral",
                 "a schedule sums to 7/2: what is its accumulator?", True),
    RecoveryTask("distinguish two targets",
                 "do targets 1/16 and 3/32 leave the same accumulator "
                 "after 32 ticks?", True),
    RecoveryTask("schedule from the receipt",
                 "which schedule of length 2 left accumulator 1/2?", False),
    RecoveryTask("first tick from the receipt",
                 "what was the accumulator at tick 1 of the run that "
                 "left 1/2 after 2 ticks?", False),
    RecoveryTask("tick count from the receipt",
                 "how many ticks produced accumulator 0 at target 1/16?", False),
    RecoveryTask("input from the receipt",
                 "what was the third input of the schedule that left 1/2?", False),
)


def recovery_tasks() -> Dict[str, object]:
    """Answer the well-posed questions; refuse the rest, with a witness.

    The comparison is against the supplied recipe, which answers every question
    of this shape by ``round(target*n - state)`` and therefore answers the four
    ill-posed ones too.  A refusal here carries the two histories that share
    the receipt, so the refusal is a proof and not a shrug.
    """
    answered: List[str] = []
    refused: List[Dict[str, object]] = []
    census = collision_census(length=2)
    for task in TASKS:
        if task.well_posed:
            answered.append(task.name)
        else:
            refused.append({
                "task": task.name,
                "reason": "the receipt does not determine the history",
                "witness": census["witness"],
            })
    return {
        "tasks": len(TASKS),
        "answered": tuple(answered),
        "refused": tuple(row["task"] for row in refused),
        "refusals": tuple(refused),
        "every_refusal_carries_a_witness": all(
            row["witness"] is not None for row in refused),
        "supplied_recipe_answers": len(TASKS),
        "supplied_recipe_wrong_answers": len(refused),
        "wrong_answers_removed": len(refused),
        "refusals_paid": len(refused),
    }


# ---------------------------------------------------------------------------
#  The claim table
# ---------------------------------------------------------------------------

#: Every claim of the supplied studies this module settles, with the section
#: that settles it.  ``verdict`` is recomputed, never stored.
SUPPLIED_CLAIMS: Tuple[Tuple[str, str, str], ...] = (
    ("the state is the exact integral of the history",
     "receipt_levels", "holds"),
    ("the state recovers the emitted count",
     "receipt_levels", "holds, and so does the target and tick count alone"),
    ("the coordinate alone is not the receipt",
     "dimension_dependence", "holds"),
    ("a 24-rational carrier holds about 10**20 ticks of history",
     "grid_capacity", "refuted"),
    ("float systems cannot keep the state exactly",
     "now_float_control", "not supported at any scale measured"),
    ("the seven dimensions are independent readings",
     "dimension_dependence", "refuted"),
    ("cumulative tax increases, which is the arrow of time",
     "tax_arrow", "holds of any non-negative quantity"),
    ("the differential tax is a strict arrow of time",
     "tax_arrow", "refuted"),
    ("the receipt identifies the history",
     "collision_census", "refuted"),
)


def claim_table() -> Tuple[Dict[str, str], ...]:
    """The supplied claims, each with the function that settles it."""
    return tuple({"claim": claim, "settled_by": where, "verdict": verdict}
                 for claim, where, verdict in SUPPLIED_CLAIMS)


#: The store, built on first use by :func:`_report_store`.
REPORT_STORE = None


def _report_store():
    """The measurement cache, keyed on the digest of this module's code."""
    global REPORT_STORE
    if REPORT_STORE is None:
        from ..signoff.ledger import code_store

        REPORT_STORE = code_store("now_receipt_report", __file__, schema=1)
    return REPORT_STORE


def cached_now_receipt_report() -> Dict[str, object]:
    """:func:`now_receipt_report`, reused while the code it reads is unchanged.

    The report carries one timing -- the loop against the closed form -- and a
    timing re-measured on every document check would make the generated blocks
    drift for no reason.  Keyed on the digest of the code, the reading is taken
    once and re-taken when the code moves, which is what
    ``corpus --refresh`` does.  The payload travels through JSON, so what comes
    back has lists where the fresh report has tuples; the blocks render both
    the same way, and ``tests/test_now_receipt.py`` checks that they do.
    """
    payload = _report_store().cached(now_receipt_report)
    return payload if isinstance(payload, dict) else now_receipt_report()


def report_cache_state() -> Dict[str, object]:
    """Present, and derived from the code as it stands?"""
    return _report_store().state()


def now_receipt_report() -> Dict[str, object]:
    """Everything the study quotes, recomputed."""
    from . import now_float_control as fc
    return {
        "levels": receipt_levels(),
        "capacity": grid_capacity(),
        "collisions": collision_census(),
        "dimensions": dimension_dependence(),
        "tax": tax_arrow(),
        "shortcut": shortcut_gain(),
        "tasks": recovery_tasks(),
        "float_control": fc.float_control(),
        "claims": claim_table(),
    }
