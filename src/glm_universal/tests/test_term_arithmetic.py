"""Tests for arithmetic inside a description.

Three questions used to stop at the same place -- ``resolve: ... names no
carrier`` -- although the machine held everything needed to answer all three:

* ``describe H2O``                  a notation that denotes a species,
* ``what is 2 + 2``                 a notation that denotes a number,
* ``what is energy divided by time`` arithmetic over register *names*.

The first two are answered by the reference resolver, which already decides
what a notation denotes; the third by ``reasoning/term_arithmetic.py``, which
rewrites the English operator words into the verifier's dimensional grammar and
then names every register quantity of the resulting dimension.

What these tests pin is as much what the routes *refuse* as what they answer:
``describe unobtainium`` must still be refused, since nothing denotes it, and
the arithmetic route must decline any expression that names no register
quantity rather than parsing it into something.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.data_objects import physics as ph
from glm_universal.reasoning import term_arithmetic as TA
from glm_universal.reasoning import verifier as vf
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


@pytest.fixture(scope="module")
def report():
    return TA.term_arithmetic_report()


# ===========================================================================
# 1.  NORMALISATION -- a string rewrite, and nothing else
# ===========================================================================

class TestNormalise:

    def test_divided_by_becomes_a_slash(self):
        assert TA.normalise("energy divided by time") == "energy / time"

    def test_times_becomes_a_star(self):
        assert TA.normalise("mass times acceleration") == "mass * acceleration"

    def test_per_and_over_are_division(self):
        assert TA.normalise("length per time") == "length / time"
        assert TA.normalise("length over time") == "length / time"

    def test_squared_and_cubed_are_postfix_powers(self):
        assert TA.normalise("length squared") == "length ^ 2"
        assert TA.normalise("length cubed") == "length ^ 3"

    def test_the_longest_operator_word_wins(self):
        """``multiplied by`` must not be read as ``by`` or as ``multiplied``."""
        assert TA.normalise("force multiplied by length") == "force * length"

    def test_filler_words_are_dropped(self):
        assert TA.normalise("the energy divided by the time") == "energy / time"

    def test_case_is_folded(self):
        assert TA.normalise("Energy Divided By Time") == "energy / time"

    def test_normalisation_does_no_arithmetic(self):
        """It knows no register names: an unknown word survives unchanged."""
        assert TA.normalise("banana divided by banana") == "banana / banana"


# ===========================================================================
# 2.  THE ARITHMETIC -- exact, and refused when it is not understood
# ===========================================================================

class TestEvaluate:

    def test_energy_over_time_is_a_power(self):
        result = TA.evaluate("energy divided by time")
        assert result.ext10 == "L^2 M T^-3"
        assert "power" in result.names

    def test_the_dimension_agrees_with_the_verifier(self):
        """The English route and the symbolic route must not disagree."""
        english = TA.evaluate("mass times acceleration").sense
        symbolic = vf.parse("mass * acceleration")
        assert english.exps == symbolic.exps
        assert english.scale == symbolic.scale

    def test_the_dimension_agrees_with_the_register_entry(self):
        """``force`` is in the register; the arithmetic must land on it."""
        result = TA.evaluate("mass times acceleration")
        force = ph.quantity_by_name("force")
        assert tuple(result.sense.exps) == tuple(force.exps_ext10)
        assert "force" in result.names

    def test_exponents_are_exact_rationals(self):
        result = TA.evaluate("energy divided by time")
        assert all(isinstance(e, Fraction) for e in result.sense.exps)

    def test_a_ratio_of_like_quantities_is_dimensionless(self):
        result = TA.evaluate("velocity divided by velocity")
        assert result.is_dimensionless
        assert all(e == 0 for e in result.sense.exps)

    def test_multiplying_then_dividing_returns_the_start(self):
        there = TA.evaluate("power times time")
        back = TA.evaluate("energy")
        assert there.sense.exps == back.sense.exps

    def test_si7_is_the_first_seven_axes(self):
        result = TA.evaluate("energy divided by time")
        assert result.si7 == ph.dimension_string(result.sense.exps, "SI7")

    def test_a_term_naming_nothing_is_refused(self):
        with pytest.raises(TA.ArithmeticError_):
            TA.evaluate("unobtainium")

    def test_an_expression_over_unknown_words_is_refused(self):
        with pytest.raises(TA.ArithmeticError_):
            TA.evaluate("banana divided by banana")

    def test_an_empty_expression_is_refused(self):
        with pytest.raises(TA.ArithmeticError_):
            TA.evaluate("   ")

    def test_mentions_register_name_is_the_guard(self):
        assert TA.mentions_register_name("energy divided by time")
        assert not TA.mentions_register_name("unobtainium")


# ===========================================================================
# 3.  WHAT THE ANSWER SAYS -- a dimension does not determine a name
# ===========================================================================

class TestDescribeLine:

    def test_a_shared_dimension_is_reported_as_shared(self):
        line = TA.evaluate("energy divided by time").describe()
        assert "power" in line
        assert "L^2 M T^-3" in line

    def test_the_line_never_claims_a_unique_name_it_does_not_have(self):
        result = TA.evaluate("energy divided by time")
        assert len(result.names) > 1
        assert result.name is None
        assert str(len(result.names)) in result.describe()

    def test_a_dimensionless_result_says_so(self):
        line = TA.evaluate("velocity divided by velocity").describe()
        assert "dimensionless" in line

    def test_long_name_lists_are_truncated_with_a_count(self):
        result = TA.evaluate("length divided by time")
        assert len(result.names) > TA.NAMES_SHOWN
        assert "more" in result.describe()

    def test_as_dict_keeps_the_full_count(self):
        result = TA.evaluate("length divided by time")
        record = result.as_dict()
        assert record["name_count"] == len(result.names)
        assert len(record["names"]) == TA.NAMES_SHOWN


# ===========================================================================
# 4.  THE REPORT -- recomputed, never quoted
# ===========================================================================

class TestReport:

    def test_every_listed_expression_is_evaluated(self, report):
        assert report["expressions"] == len(TA.REPORT_EXPRESSIONS)
        assert len(report["rows"]) == len(TA.REPORT_EXPRESSIONS)

    def test_every_expression_lands_on_a_named_dimension(self, report):
        assert report["named"] == report["expressions"]

    def test_no_expression_in_the_table_has_a_unique_name(self, report):
        """The register is wide enough that a dimension never names one thing."""
        assert report["uniquely_named"] == 0

    def test_the_register_size_is_the_live_one(self, report):
        assert report["register_size"] == len(ph.load_physics_register())

    def test_the_report_is_float_free(self, report):
        def walk(value):
            assert not isinstance(value, float)
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(report)


# ===========================================================================
# 5.  THE RUNTIME -- the three questions, end to end
# ===========================================================================

class TestDescribeRoutes:

    def test_a_formula_is_described_by_what_it_denotes(self, sess):
        """A formula no register spells still denotes something determinate.

        The case moved from `H2O` to `PbCl2` when the molecules register
        arrived: water is now a register entry, so `describe H2O` takes the
        carrier route.  What this route is for is a formula the register
        does *not* carry, which the reference resolver can still pin down
        from the element register alone.
        """
        sol = sess.ask("describe PbCl2")
        assert sol.ok
        assert sol.kind == "describe"
        assert "compound" in sol.answer

    def test_a_registered_formula_is_described_by_its_carrier(self, sess):
        sol = sess.ask("describe H2O")
        assert sol.ok
        assert sol.kind == "describe"
        assert sol.expected["domain"] == "molecules"
        assert "water" in sol.answer

    def test_a_numeral_expression_is_described_by_its_value(self, sess):
        sol = sess.ask("what is 2 + 2")
        assert sol.ok
        assert "4" in sol.answer

    def test_arithmetic_over_register_names_is_answered(self, sess):
        sol = sess.ask("what is energy divided by time")
        assert sol.ok
        assert "power" in sol.answer
        assert "L^2 M T^-3" in sol.answer

    def test_the_arithmetic_route_reports_its_two_steps_separately(self, sess):
        sol = sess.ask("what is energy divided by time")
        labels = [step.label for step in sol.steps]
        assert labels == ["normalise", "dimension", "naming"]

    def test_a_register_name_still_takes_the_carrier_route(self, sess):
        """The fallback must not shadow the ordinary description."""
        sol = sess.ask("describe energy")
        assert sol.ok
        assert "physics" in sol.answer
        assert sol.script_spec["template"] == "describe"

    def test_a_term_denoting_nothing_is_still_refused(self, sess):
        sol = sess.ask("describe unobtainium")
        assert not sol.ok
        assert "names no carrier" in sol.error

    def test_the_refusal_survives_both_fallbacks(self, sess):
        """Neither route may claim a term the registers do not pin down."""
        for question in ("describe unobtainium", "describe flibbertigibbet"):
            assert not sess.ask(question).ok


# ===========================================================================
# 6.  COLUMN 3 -- recomputed in a fresh interpreter
# ===========================================================================

class TestColumnThree:

    def test_the_generated_script_is_exact(self, sess):
        source = tct.render_script(sess.ask("what is energy divided by time"))
        ok, offenders = tct.script_is_exact(source)
        assert ok, offenders

    def test_the_arithmetic_script_reproduces_column_two(self, sess):
        trace = tct.verify_trace(tct.build_trace(
            sess.ask("what is energy divided by time")))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_reference_route_reproduces_column_two(self, sess):
        trace = tct.verify_trace(tct.build_trace(sess.ask("describe H2O")))
        assert trace.verdict is not None
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
