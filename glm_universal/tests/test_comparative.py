"""Tests for the comparative -- *hotter than*, *as hot as*.

``test_measure_words.py`` pins the reading of one use; what is pinned here is
the relation between **two** of them, which is a different thing and was the
open item ``studies/RELATIVE_MEASURE_STUDY.md`` §6 recorded: ``above_on``
orders the words of a scale, but a comparative is asked of uses, and across
comparison classes the words do not decide it.

Five things could go wrong and each has a class:

* the comparison could be inexact, or built from a float
  (``TestTheComparison``);
* the direction a marker asserts could be hard-coded rather than read off the
  register (``TestTheMarker``);
* the claim that the words decide the order within a class, and often not
  across them, could be an assertion rather than a measurement
  (``TestTheAudit``);
* the query could answer where the registers hold nothing
  (``TestTheRefusals``);
* the runtime path could disagree with the reasoning layer, or fail to
  re-derive itself in a fresh interpreter (``TestTheQuery``).

The machine-checked counterparts are in ``RequestProject/GLM/Comparative.lean``:
``hotterThan_trichotomy`` (greater, equal or less, and exactly one),
``hotterThan_iff_position_lt`` (within one class the word order *is* the
magnitude order), ``comparative_not_determined_by_word_order`` and
``comparative_not_static`` (across classes it is not, and the static concept
cannot answer), ``hotterThan_congr`` (the widened view can), and
``not_comparable_left_of_unmeasured`` / ``hotTea_not_comparable_fastWalking``
(the two refusals).
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import measure_view as mvw
from glm_universal.runtime import parser as PA
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession, SolverError


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


@pytest.fixture(scope="module")
def audit():
    return mvw.comparative_audit()


class TestTheComparison:
    """Two uses, compared as exact rationals."""

    def test_the_two_magnitudes_and_their_order(self):
        comparison = mvw.compare_uses("cold", "stellar_surface", "hot", "tea")
        assert comparison.left.magnitude == Fraction(8000)
        assert comparison.right.magnitude == Fraction(363)
        assert comparison.order == 1
        assert comparison.quantity == "temperature"

    def test_the_difference_and_ratio_are_exact(self):
        comparison = mvw.compare_uses("cold", "stellar_surface", "hot", "tea")
        assert comparison.difference == Fraction(7637)
        assert comparison.ratio == Fraction(8000, 363)
        assert isinstance(comparison.difference, Fraction)
        assert isinstance(comparison.ratio, Fraction)

    def test_no_float_is_constructed(self, subtests):
        comparison = mvw.compare_uses("hot", "tea", "cold", "tea")
        for name, value in comparison.as_dict().items():
            with subtests.test(field=name):
                assert not isinstance(value, float)

    def test_equal_magnitudes_give_order_zero(self):
        comparison = mvw.compare_uses("hot", "tea", "hot", "tea")
        assert comparison.order == 0
        assert comparison.difference == 0

    def test_the_order_is_antisymmetric(self, subtests):
        pairs = ((("cold", "stellar_surface"), ("hot", "tea")),
                 (("hot", "tea"), ("cold", "tea")),
                 (("fast", "walking"), ("slow", "airliner")))
        for left, right in pairs:
            with subtests.test(pair=(left, right)):
                forward = mvw.compare_uses(left[0], left[1],
                                           right[0], right[1])
                back = mvw.compare_uses(right[0], right[1], left[0], left[1])
                assert forward.order == -back.order


class TestTheMarker:
    """Which degree word a comparative is built from, and which way it points."""

    @pytest.mark.parametrize("form,stem", [
        ("hotter", "hot"), ("cooler", "cool"), ("faster", "fast"),
        ("heavier", "heavy"), ("larger", "large"), ("denser", "dense"),
        ("warmer", "warm"), ("brighter", "bright"), ("darker", "dark"),
        ("hot", "hot"), ("small", "small"),
    ])
    def test_the_stem_is_recovered_from_the_register(self, form, stem):
        assert mvw.comparative_stem(form) == stem

    @pytest.mark.parametrize("form", ["bigger", "juster", "wetter", "eviller"])
    def test_a_form_the_register_does_not_hold_is_not_invented(self, form):
        assert mvw.comparative_stem(form) is None

    @pytest.mark.parametrize("word,direction", [
        ("hot", "greater"), ("cold", "less"), ("scalding", "greater"),
        ("freezing", "less"), ("fast", "greater"), ("slow", "less"),
        ("heavy", "greater"), ("large", "greater"), ("small", "less"),
        ("dark", "less"), ("bright", "greater"),
    ])
    def test_the_direction_is_the_position_on_the_scale(self, word, direction):
        assert mvw.comparative_direction(word) == direction

    @pytest.mark.parametrize("word", ["tepid", "middling", "medium",
                                      "nominal", "ordinary"])
    def test_a_word_at_the_midpoint_names_no_direction(self, word):
        with pytest.raises(mvw.MeasureBoundary) as raised:
            mvw.comparative_direction(word)
        assert raised.value.reason == "no direction"

    def test_every_degree_word_is_either_directed_or_at_the_midpoint(
            self, subtests):
        for word in mvw.degree_words():
            with subtests.test(word=word):
                entry = mvw.word_by_name(word)
                try:
                    direction = mvw.comparative_direction(word)
                except mvw.MeasureBoundary as boundary:
                    assert boundary.reason == "no direction"
                    assert entry.position == Fraction(1, 2)
                else:
                    assert direction in ("greater", "less")
                    assert (entry.position > Fraction(1, 2)) == (
                        direction == "greater")


class TestTheClaim:
    """A comparative claim, decided -- and the reversal that motivates it."""

    def test_cold_for_a_star_is_hotter_than_hot_for_tea(self):
        verdict = mvw.answer_comparative("hotter", "cold", "stellar_surface",
                                         "hot", "tea")
        assert verdict["holds"] is True
        assert verdict["order"] == 1
        assert verdict["word_order"] == -1        # cold is the lower word

    def test_the_same_pair_read_the_other_way(self):
        verdict = mvw.answer_comparative("cooler", "hot", "tea",
                                         "cold", "stellar_surface")
        assert verdict["direction"] == "less"
        assert verdict["holds"] is True

    def test_within_one_class_the_words_decide(self):
        verdict = mvw.answer_comparative("hotter", "hot", "tea",
                                         "cold", "tea")
        assert verdict["holds"] is True
        assert verdict["word_order"] == verdict["order"] == 1
        assert verdict["same_class"] is True

    def test_a_false_claim_is_reported_false_rather_than_refused(self):
        verdict = mvw.answer_comparative("hotter", "cold", "tea", "hot", "tea")
        assert verdict["holds"] is False
        assert verdict["order"] == -1

    def test_the_equative_is_equality_of_magnitudes(self):
        near = mvw.answer_comparative("hot", "warm", "tea",
                                      "cold", "stellar_surface",
                                      equative=True)
        assert near["holds"] is False
        same = mvw.answer_comparative("hot", "hot", "tea", "hot", "tea",
                                      equative=True)
        assert same["holds"] is True
        assert same["direction"] == "equal"

    def test_exactly_one_of_the_three_relations_holds(self, subtests):
        """``GLM.Info.hotterThan_trichotomy``, on the shipped register."""
        cases = ((("cold", "stellar_surface"), ("hot", "tea")),
                 (("hot", "tea"), ("hot", "tea")),
                 (("hot", "tea"), ("cold", "tea")))
        for left, right in cases:
            with subtests.test(pair=(left, right)):
                greater = mvw.answer_comparative(
                    "hotter", left[0], left[1], right[0], right[1])["holds"]
                equal = mvw.answer_comparative(
                    "hot", left[0], left[1], right[0], right[1],
                    equative=True)["holds"]
                less = mvw.answer_comparative(
                    "cooler", left[0], left[1], right[0], right[1])["holds"]
                assert [greater, equal, less].count(True) == 1


class TestTheAudit:
    """How far the word order decides the comparative -- measured."""

    def test_the_use_set_and_the_comparable_pairs(self, audit):
        assert audit["uses"] == 56
        assert audit["comparable_pairs"] == 228
        assert (audit["same_class"]["pairs"] + audit["cross_class"]["pairs"]
                == audit["comparable_pairs"])

    def test_within_a_class_the_words_never_get_it_backwards(self, audit):
        """The Python counterpart of ``hotterThan_iff_position_lt``."""
        assert audit["same_class"]["disagree"] == 0
        assert audit["word_order_decides_within_class"] is True
        assert audit["same_class"]["agree"] == audit["same_class"]["pairs"]

    def test_across_classes_they_often_do(self, audit):
        assert audit["cross_class"]["pairs"] == 204
        assert audit["cross_class"]["disagree"] == 151
        assert audit["cross_class_disagreement"] == Fraction(151, 204)
        assert isinstance(audit["cross_class_disagreement"], Fraction)

    def test_the_buckets_add_up(self, audit, subtests):
        for name in ("same_class", "cross_class"):
            with subtests.test(bucket=name):
                bucket = audit[name]
                assert bucket["agree"] + bucket["disagree"] == bucket["pairs"]

    def test_every_example_is_a_real_reversal(self, audit, subtests):
        assert audit["examples"]
        for row in audit["examples"]:
            with subtests.test(example=row["lower_word"]):
                assert row["lower_magnitude"] > row["higher_magnitude"]
                assert isinstance(row["lower_magnitude"], Fraction)

    def test_the_audit_is_a_measurement_of_the_register(self, audit):
        """Recomputed here from the readings, without the audit's own code."""
        measured = [u for u in mvw.uses() if u.measured]
        assert len(measured) == audit["uses"]
        readings = {u.name: mvw.read(u.word, u.comparison_class)
                    for u in measured}
        disagreements = 0
        for i, a in enumerate(measured):
            for b in measured[i + 1:]:
                ra, rb = readings[a.name], readings[b.name]
                if ra.quantity != rb.quantity:
                    continue
                word = (ra.position > rb.position) - (ra.position
                                                      < rb.position)
                mag = (ra.magnitude > rb.magnitude) - (ra.magnitude
                                                       < rb.magnitude)
                if word != mag:
                    disagreements += 1
        assert disagreements == audit["disagreements"]


class TestTheRefusals:
    """Four boundaries, each declined with the reason the register gives."""

    @pytest.mark.parametrize("args,reason", [
        ((("hotter", "hot", "tea", "fast", "walking"), False),
         "different quantities"),
        ((("hotter", "fast", "walking", "slow", "airliner"), False),
         "comparative quantity mismatch"),
        ((("hotter", "expensive", "market", "hot", "tea"), False),
         "no such measure word"),
        ((("tepider", "tepid", "tea", "cold", "tea"), False),
         "no direction"),
    ])
    def test_the_reason_is_stated(self, args, reason):
        call, equative = args
        with pytest.raises(mvw.MeasureBoundary) as raised:
            mvw.answer_comparative(*call, equative=equative)
        assert raised.value.reason == reason

    def test_a_marker_the_register_does_not_hold_is_refused(self):
        with pytest.raises(mvw.MeasureBoundary) as raised:
            mvw.answer_comparative("bigger", "hot", "tea", "cold", "tea")
        assert raised.value.reason == "unknown comparative"

    def test_a_class_of_the_wrong_quantity_is_refused(self):
        with pytest.raises(mvw.MeasureBoundary):
            mvw.compare_uses("hot", "walking", "cold", "tea")


class TestTheQuery:
    """The runtime path: the parse, the answers, the refusals, the script."""

    def test_comparative_is_a_declared_query_kind(self):
        assert "comparative" in PA.KINDS

    def test_the_parser_classifies_the_kind(self, sess):
        query = PA.parse_query(
            "is cold in stellar_surface hotter than hot in tea", sess.index)
        assert query.kind == "comparative"
        assert query.options["form"] == "hotter"
        assert query.options["left_word"] == "cold"
        assert query.options["left_class"] == "stellar_surface"
        assert query.options["right_word"] == "hot"
        assert query.options["right_class"] == "tea"
        assert query.options["equative"] is False

    def test_the_parser_reads_the_equative(self, sess):
        query = PA.parse_query(
            "is warm in tea as hot as cold in stellar_surface", sess.index)
        assert query.kind == "comparative"
        assert query.options["equative"] is True
        assert query.options["form"] == "hot"

    @pytest.mark.parametrize("text", [
        "is sqrt(2) greater than 7/5",
        "compare sqrt(2) and 7/5",
    ])
    def test_the_exact_real_comparison_is_untouched(self, sess, text):
        """The rule fires on the shape of the operands, not on the keyword."""
        assert PA.parse_query(text, sess.index).kind == "compare"

    def test_the_answer_and_the_reversal(self, sess):
        solution = sess.ask(
            "is cold in stellar_surface hotter than hot in tea")
        assert solution.ok is True
        assert solution.kind == "comparative"
        assert solution.payload["holds"] is True
        assert solution.expected["left_magnitude"] == "8000/1"
        assert solution.expected["right_magnitude"] == "363/1"
        assert solution.expected["word_order"] == "-1"
        assert solution.expected["order"] == "1"

    def test_a_false_claim_answers_rather_than_failing(self, sess):
        solution = sess.ask("is cold in tea hotter than hot in tea")
        assert solution.ok is True
        assert solution.payload["holds"] is False
        assert solution.answer.startswith("No:")

    @pytest.mark.parametrize("text", [
        "is hot in tea hotter than fast in walking",
        "is fast in walking hotter than slow in airliner",
        "is expensive in market hotter than hot in tea",
        "is tepid in tea tepider than cold in tea",
    ])
    def test_the_query_refuses_at_the_boundary(self, sess, text):
        solution = sess.ask(text)
        assert solution.ok is False
        assert solution.error is not None
        assert solution.error.startswith("comparative: ")

    def test_the_solver_itself_raises_the_refusal(self, sess):
        query = PA.parse_query("is hot in tea hotter than fast in walking",
                               sess.index)
        with pytest.raises(SolverError):
            sess._solve_comparative(query)

    def test_the_solution_carries_the_audit(self, sess):
        solution = sess.ask("is hot in tea hotter than cold in tea")
        audit = solution.payload["audit"]
        assert audit["same_class_disagree"] == 0
        assert audit["cross_class_disagree"] == 151
        assert int(solution.expected["cross_class_pairs"]) == 204

    def test_the_script_re_derives_the_verdict_in_a_fresh_interpreter(
            self, sess):
        solution = sess.ask(
            "is cold in stellar_surface hotter than hot in tea")
        trace = tct.verify_trace(tct.build_trace(solution))
        assert trace.verified is True
