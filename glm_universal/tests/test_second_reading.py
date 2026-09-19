"""Tests for the second reading and the guards built on it.

``reasoning/second_reading`` asks whether requiring a second, independent
reading to agree before answering removes the wrong answers the program-text
operation produces, and what that costs.  What is pinned here is the
*protocol* rather than the outcome: the two readings, the two guards and their
algebra, the two controls, the four declared marks and the arithmetic that
applies them.  The measured figures are read from the cache, which must still
describe the sources it was taken from, and the properties checked against
them are the ones ``RequestProject/GLM/SecondReading.lean`` proves.

Directive D7 -- no float anywhere -- is checked statically.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import operation_escalation as OE
from glm_universal.reasoning import second_reading as SR


@pytest.fixture(scope="module")
def stored():
    data = SR.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools second-reading --write")
    return data


class TestGuards:
    """The algebra the Lean file proves, checked on this implementation."""

    def test_strict_answers_only_on_agreement(self):
        assert SR.strict_guard("a", "a") == "a"
        assert SR.strict_guard("a", "b") is None
        assert SR.strict_guard("a", None) is None
        assert SR.strict_guard(None, "a") is None

    def test_veto_lets_a_silent_second_reading_stand_aside(self):
        assert SR.veto_guard("a", "a") == "a"
        assert SR.veto_guard("a", "b") is None
        assert SR.veto_guard("a", None) == "a"
        assert SR.veto_guard(None, "a") is None

    def test_a_guard_invents_nothing(self):
        # GLM.SecondReading.strictGuard_sound / vetoGuard_sound.
        for primary in (None, "a", "b"):
            for second in (None, "a", "b"):
                for guard in (SR.strict_guard, SR.veto_guard):
                    answer = guard(primary, second)
                    assert answer is None or answer == primary

    def test_strict_is_below_veto(self):
        # GLM.SecondReading.strictGuard_le_vetoGuard.
        for primary in (None, "a", "b"):
            for second in (None, "a", "b"):
                strict = SR.strict_guard(primary, second)
                if strict is not None:
                    assert SR.veto_guard(primary, second) == strict

    def test_a_wrong_answer_needs_the_second_reading_to_repeat_it(self):
        # GLM.SecondReading.strict_blocks_unless_second_repeats.
        assert SR.strict_guard("wrong", "right") is None
        assert SR.strict_guard("wrong", None) is None


class TestReadings:

    def test_the_median_is_exact_and_per_coordinate(self):
        entries = (("x", 1, tuple(Fraction(0) for _ in range(24))),
                   ("y", 2, tuple(Fraction(4) for _ in range(24))),
                   ("z", 3, tuple(Fraction(2) for _ in range(24))))
        assert SR.medians(entries) == tuple(Fraction(2) for _ in range(24))

    def test_the_word_is_a_comparison_against_the_median(self):
        thresholds = tuple(Fraction(1) for _ in range(24))
        vector = tuple(Fraction(2) if j % 2 == 0 else Fraction(0)
                       for j in range(24))
        word = SR.binary_word(vector, thresholds)
        assert word == sum(1 << j for j in range(0, 24, 2))

    def test_the_code_reading_refuses_rather_than_breaking_a_tie(self):
        from glm_universal.substrate import golay_decode as GD
        # A word at distance 4 from the code has six equally near codewords,
        # and the reading must refuse there rather than pick one.
        ambiguous = next(mask for mask in range(1 << 12)
                         if GD.decode_or_detect(mask)[0] is None)
        thresholds = tuple(Fraction(0) for _ in range(24))
        query = tuple(Fraction(1) if (ambiguous >> j) & 1 else Fraction(-1)
                      for j in range(24))
        assert SR.read_code(query, thresholds, {}) is None

    def test_the_margin_reading_refuses_when_a_rival_is_within_the_margin(self):
        entries = (("a", "one", tuple(Fraction(0) for _ in range(24))),
                   ("b", "two", tuple(Fraction(1) if j == 0 else Fraction(0)
                                      for j in range(24))))
        query = tuple(Fraction(1, 4) if j == 0 else Fraction(0)
                      for j in range(24))
        # nearest is 1/4 away, the rival 3/4: 3/4 <= 2*(1/4) is false, so the
        # reading answers; move the query to the midpoint and it must refuse.
        assert SR.read_margin(query, entries) == "one"
        midpoint = tuple(Fraction(1, 2) if j == 0 else Fraction(0)
                         for j in range(24))
        assert SR.read_margin(midpoint, entries) is None

    def test_the_reshuffle_keeps_the_labels_and_moves_them(self):
        operation = [o for o in OE.OPERATIONS if o.key == "harmony"][0]
        entries = operation.carriers()
        shuffled = SR._reshuffled_labels(entries)
        original = tuple(label for _, label, _ in entries)
        assert sorted(map(repr, shuffled)) == sorted(map(repr, original))
        assert shuffled != original
        # Deterministic: no random source anywhere.
        assert SR._reshuffled_labels(entries) == shuffled


class TestMeasurement:

    def test_the_cache_describes_the_sources(self):
        assert SR.state()["verdict"] == "fresh"

    def test_every_reading_reports_all_three_outcomes(self, stored):
        for row in stored["operations"]:
            for score in row["readings"].values():
                assert (score["correct"] + score["wrong"] + score["refused"]
                        == score["queries"])
            for configuration in row["configurations"].values():
                score = configuration["score"]
                assert (score["correct"] + score["wrong"] + score["refused"]
                        == score["queries"])

    def test_every_declared_configuration_is_measured(self, stored):
        expected = {f"{guard}+{reading}"
                    for guard in SR.GUARDS for reading in SR.READINGS}
        for row in stored["operations"]:
            assert set(row["configurations"]) == expected

    def test_a_guard_never_gains_a_correct_answer(self, stored):
        # GLM.SecondReading.strict_correctCount_le / veto_correctCount_le.
        for row in stored["operations"]:
            bare = row["readings"]["primary"]
            for key, configuration in row["configurations"].items():
                assert configuration["score"]["correct"] <= bare["correct"], key
                assert configuration["score"]["wrong"] <= bare["wrong"], key

    def test_strict_is_never_above_veto(self, stored):
        # GLM.SecondReading.strict_correctCount_le_veto.
        for row in stored["operations"]:
            for reading in SR.READINGS:
                strict = row["configurations"][f"strict+{reading}"]["score"]
                veto = row["configurations"][f"veto+{reading}"]["score"]
                assert strict["correct"] <= veto["correct"]

    def test_the_matched_control_gives_up_the_same_number_of_answers(self, stored):
        for row in stored["operations"]:
            bare = row["readings"]["primary"]
            for key, configuration in row["configurations"].items():
                matched = configuration["control_matched_refusal"]
                given_up = configuration["answers_given_up"]
                assert (bare["correct"] + bare["wrong"] - given_up
                        == matched["correct"] + matched["wrong"]), key

    def test_the_marks_are_applied_as_declared(self, stored):
        marks = stored["marks_report"]
        program = [row for row in stored["operations"]
                   if row["operation"] == "program"][0]
        for key, verdict in marks["verdicts"].items():
            score = program["configurations"][key]["score"]
            assert verdict["M1"] == (score["wrong"] == 0)
            assert verdict["M2"] == (score["correct"] >= SR.M2_FLOOR)
            assert verdict["adopted"] == all(verdict[mark] for mark in
                                             ("M1", "M2", "M3", "M4"))

    def test_the_shipped_configuration_is_adopted_and_cheapest(self, stored):
        marks = stored["marks_report"]
        shipped = marks["shipped"]
        if shipped is None:
            assert not marks["adopted"]
            return
        assert shipped in marks["adopted"]
        cost = marks["verdicts"][shipped]["answers_given_up"]
        for key in marks["adopted"]:
            assert marks["verdicts"][key]["answers_given_up"] >= cost

    def test_the_operation_the_round_is_about_is_still_unsafe_unguarded(self, stored):
        # The premise of the round: without a guard the program-text
        # operation answers wrongly.  If that ever stops being true the study
        # is about nothing and should be re-read rather than quietly passing.
        program = [row for row in stored["operations"]
                   if row["operation"] == "program"][0]
        assert program["readings"]["primary"]["wrong"] > 0


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(SR.__file__)) == {}
