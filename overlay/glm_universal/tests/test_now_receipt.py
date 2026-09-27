"""Tests for ``reasoning/now_receipt`` -- the audit of the supplied study.

``source_material/HISTORY_RECORDED_NOW_STUDY.md`` and its three sequels claim
that the state of an exact-rational process is the receipt of its own history.
:mod:`glm_universal.reasoning.now_receipt` decides that claim rather than
illustrating it, and these tests pin every reading the study
``studies/NOW_RECEIPT_STUDY.md`` quotes against an independent computation --
usually the raw loop, which is what the closed forms are supposed to replace.

The machine-checked counterparts are in ``RequestProject/GLM/NowReceipt.lean``:
``acc_eq_fract`` and ``count_eq_floor`` (what the accumulator records),
``receipt_collision``, ``acc_mem_grid`` and ``receipt_pigeonhole`` (what it
does not), ``const_count_eq_floor`` and ``const_bit_eq_floor_diff`` (the closed
forms the shipped modulator now uses) and ``cumulative_mono`` (how little the
arrow-of-time claim says).
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

from glm_universal.reasoning import exact_real as xr
from glm_universal.reasoning import now_float_control as fc
from glm_universal.reasoning import now_receipt as nr

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "NowReceipt.lean")

TARGETS = (Fraction(0), Fraction(1, 16), Fraction(3, 32), Fraction(1, 3),
           Fraction(97, 128), Fraction(6369051672525773, 2 ** 53),
           Fraction(999999, 10 ** 6))


@pytest.fixture(scope="module")
def report():
    return nr.now_receipt_report()


# -- the closed forms against the raw loop ----------------------------------

def test_closed_average_matches_the_loop():
    """``delta_sigma_average`` reads the answer off the target; the loop agrees."""
    for target in TARGETS:
        for steps in (1, 2, 7, 32, 64, 257):
            modulator = xr.DeltaSigma(target)
            modulator.run(steps)
            assert xr.delta_sigma_average(target, steps) == modulator.average
            assert xr.delta_sigma_error(target, steps) == modulator.error


def test_closed_bits_match_the_loop():
    for target in TARGETS:
        for steps in (0, 1, 5, 64, 129):
            assert xr.delta_sigma_bits(target, steps) == xr.DeltaSigma(target).run(steps)


def test_closed_average_keeps_its_refusals():
    with pytest.raises(xr.PrecisionError):
        xr.delta_sigma_average(Fraction(1, 3), 0)
    with pytest.raises(ValueError):
        xr.delta_sigma_average(Fraction(3, 2), 8)
    with pytest.raises(TypeError):
        xr.delta_sigma_average(0.5, 8)


def test_average_is_within_the_proved_bound():
    """``GLM.Info.dsAverage_error_le``: the error is below ``1/N``."""
    for target in TARGETS:
        for steps in (4, 64, 1024):
            assert xr.delta_sigma_error(target, steps) <= Fraction(1, steps)


@pytest.mark.exhaustive
def test_closed_forms_agree_with_the_loop_at_length():
    target = Fraction(6369051672525773, 2 ** 53)
    steps = 20000
    modulator = xr.DeltaSigma(target)
    bits = modulator.run(steps)
    assert xr.delta_sigma_bits(target, steps) == bits
    assert xr.delta_sigma_average(target, steps) == modulator.average
    assert nr.closed_state(target, steps) == modulator.state


# -- §1  what the accumulator records ---------------------------------------

def test_state_and_count_are_the_closed_forms():
    """``GLM.NowReceipt.const_acc_eq_fract`` and ``const_count_eq_floor``."""
    for target in TARGETS:
        for steps in (1, 3, 40, 333):
            bits, state = nr.trajectory([target] * steps)
            assert state == nr.closed_state(target, steps)
            assert sum(bits) == nr.closed_count(target, steps)
            assert 0 <= state < 1


def test_variable_schedule_state_is_the_fractional_integral():
    """``GLM.NowReceipt.acc_eq_fract`` on schedules that are not constant."""
    schedules = [
        [Fraction(1, 4), Fraction(3, 4), Fraction(1, 2)],
        [Fraction(7, 8)] * 5 + [Fraction(1, 8)] * 3,
        [Fraction(i % 5, 5) for i in range(17)],
    ]
    for schedule in schedules:
        bits, state = nr.trajectory(schedule)
        total = sum(schedule, Fraction(0))
        assert state == total - (total.numerator // total.denominator)
        assert sum(bits) == total.numerator // total.denominator


def test_levels_show_the_state_adds_nothing(report):
    levels = report["levels"]
    assert levels["cases"] == 20
    assert levels["level_2_recovered_the_count"] == levels["cases"]
    assert levels["level_0_predicted_the_count"] == levels["cases"]
    assert levels["state_equals_the_closed_form"] == levels["cases"]
    assert levels["state_adds_nothing"] is True
    assert levels["denominator_never_exceeds_the_target"] is True


# -- §2  what it does not record --------------------------------------------

def test_grid_capacity_is_bounded_by_the_grid(report):
    capacity = report["capacity"]
    assert capacity["bounded_by_the_grid"] is True
    for row in capacity["rows"]:
        for reading in row["distinct_states"]:
            assert reading["distinct"] <= row["bound"]
        assert row["distinct_states"][-1]["distinct"] == row["bound"]


def test_grid_capacity_against_brute_force():
    """Enumerate the states of a small grid directly and compare."""
    q = 8
    target = Fraction(7, 8)
    seen = set()
    state = Fraction(0)
    for _ in range(500):
        driven = state + target
        state = driven - 1 if driven >= 1 else driven
        seen.add(state)
    assert seen == {Fraction(j, q) for j in range(q)}


def test_collision_census_is_exhaustive_and_correct(report):
    census = report["collisions"]
    assert census["histories"] == 4 ** 6
    assert census["receipt_is_injective"] is False
    assert census["distinct_receipts"] == 4
    assert census["largest_receipt_class"] == 1024
    counted = 0
    states = set()
    alphabet = (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4))
    for schedule in product(alphabet, repeat=6):
        total = sum(schedule, Fraction(0))
        states.add(total - (total.numerator // total.denominator))
        counted += 1
    assert counted == census["histories"]
    assert len(states) == census["distinct_receipts"]


def test_the_witness_pair_really_collides(report):
    left, right = report["collisions"]["witness"]
    left_bits, left_state = nr.trajectory([Fraction(v) for v in left])
    right_bits, right_state = nr.trajectory([Fraction(v) for v in right])
    assert left != right
    assert left_state == right_state
    assert sum(left_bits) == sum(right_bits)


def test_the_lean_witness_pair_collides():
    """``GLM.NowReceipt.receipt_collision``, run rather than read."""
    left_bits, left_state = nr.trajectory([Fraction(3, 4), Fraction(3, 4)])
    right_bits, right_state = nr.trajectory([Fraction(1, 2), Fraction(1)])
    assert left_state == right_state == Fraction(1, 2)
    assert sum(left_bits) == sum(right_bits) == 1
    assert nr.trajectory([Fraction(3, 4)])[1] != nr.trajectory([Fraction(1, 2)])[1]


# -- §3  the seven dimensions -----------------------------------------------

def test_dimensions_collapse(report):
    dimensions = report["dimensions"]
    assert dimensions["claimed_dimensions"] == 7
    assert dimensions["independent_readings"] == 3
    assert dimensions["coordinate_agrees"] == dimensions["pairs_with_the_same_coordinate"]
    assert dimensions["entropy_agrees_on_every_pair"] is True
    assert dimensions["composition_differs_on_every_pair"] is True
    assert dimensions["fibre_of_one_coordinate"] == 8 ** 24


def test_capture_now_is_exact():
    composition = tuple(Fraction(index % 3, 4) for index in range(24))
    moment = nr.capture_now(composition, previous=tuple(Fraction(0) for _ in range(24)),
                            neighbours=(("north", composition),), tick=3)
    assert moment.coordinate == nr.carrier_mask(composition)
    assert moment.topology == (("north", 0),)
    assert all(isinstance(value, Fraction) for value in moment.momentum)
    assert isinstance(moment.tax, Fraction)
    assert moment.tax == nr.tax_of(composition)


# -- §4  the arrow of time ---------------------------------------------------

def test_tax_arrow_readings(report):
    tax = report["tax"]
    assert tax["cumulative_monotone"] is True
    assert tax["per_tick_monotone"] is False
    assert tax["differential_non_negative"] is True
    assert tax["cumulative_differential_strictly_increasing"] is False
    assert tax["cumulative_differential_is_flat"] is True


def test_cumulative_monotone_holds_of_anything_non_negative():
    """The content of ``GLM.NowReceipt.cumulative_mono``, in one line."""
    values = [Fraction(index % 7, 3) for index in range(20)]
    running = Fraction(0)
    totals = []
    for value in values:
        running += value
        totals.append(running)
    assert all(a <= b for a, b in zip(totals, totals[1:]))


# -- §5  the float control ---------------------------------------------------

def test_float_control_finds_no_divergence(report):
    control = report["float_control"]
    assert control["first_bit_divergence"] is None
    assert control["first_count_divergence"] is None
    assert control["float_recovery_always_holds"] is True


@pytest.mark.exhaustive
def test_float_control_at_two_million_ticks():
    control = fc.float_control(horizon=2_000_000,
                               checkpoints=(1_000_000, 2_000_000))
    assert control["first_bit_divergence"] is None
    assert control["float_recovery_always_holds"] is True


# -- §6  what the shipped system gains --------------------------------------

def test_shortcut_output_is_identical(report):
    shortcut = report["shortcut"]
    assert shortcut["identical_output"] is True
    assert shortcut["shipped_tick_count"] == 512
    for row in shortcut["rows"]:
        assert row["average_closed_us"] <= row["average_loop_us"]
        assert row["bits_closed_us"] <= row["bits_loop_us"]


def test_the_real_query_kind_still_answers():
    """The shipped path that runs 512 ticks per question."""
    from glm_universal.runtime.session import GeometricSession
    session = GeometricSession()
    solution = session.ask("approximate sqrt(2) to 12 places")
    assert solution.kind == "real"
    assert "1.414213562373" in " ".join(str(step) for step in solution.steps)


# -- §7  the declared task set ----------------------------------------------

def test_recovery_tasks_answer_and_refuse(report):
    tasks = report["tasks"]
    assert tasks["tasks"] == 9
    assert len(tasks["answered"]) == 5
    assert len(tasks["refused"]) == 4
    assert tasks["every_refusal_carries_a_witness"] is True
    assert tasks["wrong_answers_removed"] == 4
    assert tasks["refusals_paid"] == 4


def test_claim_table_names_a_function_that_settles_each_claim(report):
    names = {"receipt_levels", "grid_capacity", "collision_census",
             "dimension_dependence", "tax_arrow", "now_float_control"}
    for row in report["claims"]:
        assert row["settled_by"] in names
        assert row["verdict"]


def test_the_lean_file_states_what_the_module_cites():
    text = LEAN.read_text(encoding="utf-8")
    for name in ("acc_eq_fract", "count_eq_floor", "acc_eq_iff_fract_eq",
                 "receipt_collision", "acc_mem_grid", "receipt_pigeonhole",
                 "const_count_eq_floor", "const_bit_eq_floor_diff",
                 "cumulative_mono"):
        assert f"theorem {name}" in text
    assert "sorry" not in text
