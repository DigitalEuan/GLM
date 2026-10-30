"""Tests for the exact reals, the written value grammar, and their wiring.

A carrier holds twenty-four exact rationals, and no rational is ``sqrt(2)``.
:mod:`~glm_universal.reasoning.exact_real` therefore holds a real number as a
*process*: a rule that returns, for any precision asked of it, an exact
rational within that precision.  :mod:`~glm_universal.reasoning.real_expr`
reads written arithmetic over those processes, and the runtime answers
``approximate`` and comparison queries with them.

These tests pin the things a user would notice: the digits (against
independently known ones), the ``1/N`` law of the one-bit dynamic carrier, the
convex-hull boundary of the twenty-four-dimensional one -- with its exact
separating certificate -- the two refusals that are theorems rather than gaps
(division by a value not known to be nonzero, and equality of two processes),
and the new query kinds end to end, including the third column that re-derives
each answer in a fresh interpreter.

The machine-checked counterparts are in ``RequestProject/GLM/``:
``DeltaSigma.lean`` (the ``1/N`` bound and the separating tower),
``Irrational.lean`` (the wall, the stand-ins, the tower's faithfulness) and
``Reachable.lean`` (the hull and the unreachability certificate).
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import exact_real as xr
from glm_universal.reasoning import real_expr as rx
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return xr.exact_real_report()


@pytest.fixture(scope="module")
def grammar_report():
    return rx.expression_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


#: The first twenty decimal places of four constants, from their classical
#: expansions.  The module must reproduce them digit for digit.
KNOWN_DIGITS = {
    "sqrt2": "1.41421356237309504880",
    "pi": "3.14159265358979323846",
    "e": "2.71828182845904523536",
    "phi": "1.61803398874989484820",
}


# ===========================================================================
# 1.  THE REPRESENTATION
# ===========================================================================

class TestExactRealRepresentation:

    def test_approximation_is_within_the_precision_asked(self):
        root2 = xr.sqrt(Fraction(2))
        for k in (0, 1, 8, 64, 200):
            value = root2.at(k)
            assert isinstance(value, Fraction)
            assert value ** 2 <= 2
            assert (value + xr._eps(k)) ** 2 >= 2

    def test_no_float_is_ever_produced(self):
        root2 = xr.sqrt(Fraction(2))
        for k in (4, 40, 400):
            assert not isinstance(root2.at(k), float)
        assert not isinstance(xr.pi().at(64), float)

    def test_precision_must_be_a_non_negative_int(self):
        root2 = xr.sqrt(Fraction(2))
        with pytest.raises(TypeError):
            root2.at(2.0)
        with pytest.raises(xr.PrecisionError):
            root2.at(-1)

    def test_a_rational_knows_it_is_one(self):
        third = xr.from_fraction(Fraction(1, 3))
        assert third.exact == Fraction(1, 3)
        assert third.at(100) == Fraction(1, 3)
        assert xr.sqrt(Fraction(2)).exact is None

    def test_arithmetic_keeps_a_known_rational_known(self):
        left = xr.from_fraction(Fraction(1, 3))
        right = xr.from_fraction(Fraction(1, 6))
        assert (left + right).exact == Fraction(1, 2)
        assert (left * right).exact == Fraction(1, 18)
        assert (-left).exact == Fraction(-1, 3)
        assert (left / 2).exact == Fraction(1, 6)
        # A process that is not known rational stays unknown.
        assert (left + xr.sqrt(Fraction(2))).exact is None

    def test_decimal_digits_match_the_classical_expansions(self):
        assert xr.sqrt(Fraction(2)).decimal(20) == KNOWN_DIGITS["sqrt2"]
        assert xr.pi().decimal(20) == KNOWN_DIGITS["pi"]
        assert xr.e().decimal(20) == KNOWN_DIGITS["e"]
        assert xr.phi().decimal(20) == KNOWN_DIGITS["phi"]

    def test_the_hundredth_digit_costs_only_time(self):
        digits = xr.sqrt(Fraction(2)).decimal(100)
        assert digits.startswith(KNOWN_DIGITS["sqrt2"])
        assert len(digits) == 102          # "1." and 100 places

    def test_deterministic(self):
        assert xr.pi().decimal(40) == xr.pi().decimal(40)
        assert (xr.delta_sigma_bits(Fraction(3, 7), 64)
                == xr.delta_sigma_bits(Fraction(3, 7), 64))


# ===========================================================================
# 2.  ROOTS
# ===========================================================================

class TestRoots:

    @pytest.mark.parametrize("degree,radicand", [
        (2, 2), (3, 2), (3, 10), (5, 7), (7, 3), (4, Fraction(1, 3)),
    ])
    def test_root_satisfies_its_defining_equation(self, degree, radicand):
        value = xr.nth_root(Fraction(radicand), degree).at(80)
        low = value ** degree
        high = (value + xr._eps(80)) ** degree
        assert low <= Fraction(radicand) <= high + Fraction(1, 2 ** 60)

    def test_integer_root_is_exact_on_perfect_powers(self):
        assert xr._iroot(1024, 10) == 2
        assert xr._iroot(3 ** 17, 17) == 3
        assert xr._iroot(3 ** 17 - 1, 17) == 2

    def test_cube_root_of_two_matches_its_known_digits(self):
        assert xr.nth_root(Fraction(2), 3).decimal(20) == "1.25992104989487316476"

    def test_a_negative_radicand_is_refused(self):
        with pytest.raises(ValueError):
            xr.nth_root(Fraction(-1), 3)
        with pytest.raises(ValueError):
            xr.sqrt(Fraction(-1))


# ===========================================================================
# 3.  COMPARISON: WHAT IS DECIDABLE AND WHAT IS NOT
# ===========================================================================

class TestComparison:

    def test_inequality_is_decided(self):
        root2 = xr.sqrt(Fraction(2))
        assert xr.compare(root2, xr.from_fraction(Fraction(7, 5)), 16) == 1
        assert xr.compare(root2, xr.from_fraction(Fraction(3, 2)), 16) == -1

    def test_equality_is_never_claimed(self):
        root2 = xr.sqrt(Fraction(2))
        product = root2 * root2
        for k in (8, 32, 64, 128):
            assert xr.decide_equal(product, xr.from_fraction(Fraction(2)), k) is None

    def test_inequality_is_reported_as_false(self):
        assert xr.decide_equal(xr.sqrt(Fraction(2)),
                               xr.from_fraction(Fraction(3, 2)), 8) is False

    def test_a_nonzero_witness_is_found_when_there_is_one(self):
        gap = xr.sqrt(Fraction(3)) - xr.sqrt(Fraction(2))
        witness = xr.nonzero_witness(gap, 32)
        assert witness is not None
        assert abs(gap.at(witness + 4)) > xr._eps(witness)

    def test_no_witness_is_invented_where_there_is_none(self):
        zero = xr.sqrt(Fraction(2)) - xr.sqrt(Fraction(2))
        assert xr.nonzero_witness(zero, 40) is None


# ===========================================================================
# 4.  THE WRITTEN GRAMMAR
# ===========================================================================

class TestWrittenGrammar:

    @pytest.mark.parametrize("text,expected", [
        ("(1+sqrt(5))/2", KNOWN_DIGITS["phi"]),
        ("sqrt(2)", KNOWN_DIGITS["sqrt2"]),
        ("pi", KNOWN_DIGITS["pi"]),
        ("sqrt(2)+sqrt(3)", "3.14626436994197234232"),
        ("root(3, 2)", "1.25992104989487316476"),
        ("pi/4", "0.78539816339744830961"),
        ("2*phi-1", "2.23606797749978969640"),      # = sqrt(5)
    ])
    def test_expressions_produce_the_right_digits(self, text, expected):
        assert rx.parse_expression(text).decimal(20) == expected

    def test_decimal_literals_are_read_exactly(self):
        assert rx.parse_expression("0.1+0.2").at(80) == Fraction(3, 10)

    def test_integer_powers(self):
        assert rx.parse_expression("2^10").at(4) == Fraction(1024)
        assert rx.parse_expression("2^-3").at(40) == Fraction(1, 8)
        squared = rx.parse_expression("sqrt(2)^2")
        assert abs(squared.at(60) - 2) < Fraction(1, 2 ** 55)

    def test_unicode_and_spacing_do_not_change_the_value(self):
        assert (rx.parse_expression("π / 4").decimal(15)
                == rx.parse_expression("pi/4").decimal(15))

    @pytest.mark.parametrize("text", [
        "asin(1)", "arctan(1)", "sinh(1)", "erf(1)", "gamma(2)",
        "1+", "sqrt(-1)", "", "sqrt(2) 3",
    ])
    def test_what_it_does_not_read_is_refused_by_name(self, text):
        with pytest.raises(rx.ExpressionError):
            rx.parse_expression(text)

    def test_division_by_a_value_not_known_nonzero_is_refused(self):
        with pytest.raises(xr.PrecisionError):
            rx.parse_expression("1/(sqrt(2)-sqrt(2))", depth=48)

    def test_division_by_a_value_that_is_nonzero_goes_through(self):
        value = rx.parse_expression("1/(sqrt(3)-sqrt(2))")
        # 1/(sqrt3 - sqrt2) = sqrt3 + sqrt2.
        reference = rx.parse_expression("sqrt(3)+sqrt(2)")
        assert abs(value.at(60) - reference.at(60)) < Fraction(1, 2 ** 50)

    def test_parse_real_accepts_the_whole_grammar(self):
        assert xr.parse_real("(1+sqrt(5))/2").decimal(10) == "1.6180339887"
        assert xr.parse_real("7/3").exact == Fraction(7, 3)
        with pytest.raises(ValueError):
            xr.parse_real("banana")

    def test_report_recomputes_its_own_claims(self, grammar_report):
        assert grammar_report["phi_two_ways_agree"] is True
        assert grammar_report["cube_root_residual_below"] is True
        assert grammar_report["decimal_literals_are_exact"] is True
        assert (grammar_report["refusals"]["sqrt(2)/(sqrt(2)-sqrt(2))"]
                == "PrecisionError")
        assert grammar_report["refusals"]["asin(1)"] == "ExpressionError"
        assert grammar_report["exp_inverts_log"] is True
        assert grammar_report["pythagorean_identity"] is True
        assert grammar_report["log_base_8_of_2_is_3"] is True
        assert grammar_report["fractional_power_is_the_root"] is True


# ===========================================================================
# 5.  THE TOWER OF STAND-INS
# ===========================================================================

class TestTowerOfStandIns:

    def test_each_level_holds_a_rational_stand_in(self, report):
        assert report["no_stand_in_is_the_target"] is True
        for text in report["stand_ins"]:
            assert Fraction(text) ** 2 != 2

    def test_a_stand_in_is_exposed_by_a_higher_level(self, report):
        for level, exposed in report["stand_in_exposed_at"]:
            assert exposed is not None
            assert exposed > level

    def test_the_stand_ins_converge_on_the_target(self):
        root2 = xr.sqrt(Fraction(2))
        for level in (4, 8, 16, 32):
            assert abs(xr.surrogate(root2, level) - root2.at(level + 4)) \
                <= Fraction(1, 2 ** level)

    def test_no_carrier_coordinate_holds_an_irrational(self):
        carrier = xr.real_carrier([xr.sqrt(Fraction(2))], 12)
        assert len(carrier) == 24
        assert all(isinstance(value, Fraction) for value in carrier)
        assert carrier[0] ** 2 != 2

    def test_more_than_twenty_four_coordinates_is_refused(self):
        with pytest.raises(ValueError):
            xr.real_carrier([xr.sqrt(Fraction(2))] * 25, 8)


# ===========================================================================
# 6.  THE DYNAMIC CARRIER
# ===========================================================================

class TestDeltaSigma:

    @pytest.mark.parametrize("steps", [1, 2, 10, 100, 1000])
    def test_average_is_within_one_over_n(self, steps):
        target = Fraction(3, 7)
        assert xr.delta_sigma_error(target, steps) <= Fraction(1, steps)

    def test_average_is_a_rational_k_over_n(self):
        steps = 64
        average = xr.delta_sigma_average(Fraction(3, 7), steps)
        assert (average * steps).denominator == 1
        assert 0 <= average <= 1

    def test_the_law_holds_for_an_irrational_target(self):
        target = xr.sqrt(Fraction(2)).at(64) - 1
        for steps in (16, 256, 2048):
            assert xr.delta_sigma_error(target, steps) <= Fraction(1, steps)

    def test_report_reproduces_the_law(self, report):
        assert report["delta_sigma_law_holds"] is True
        assert report["delta_sigma_deterministic"] is True


class TestTwentyFourDimensionalCarrier:

    def test_a_codeword_target_is_reached_exactly(self, report):
        assert report["golay_reachable_deviation"] == 0

    def test_a_constant_irrational_target_is_tracked(self):
        fractional = xr.surrogate(xr.sqrt(Fraction(2)), 40) - 1
        run = xr.golay_delta_sigma(tuple(fractional for _ in range(24)),
                                   200, rule="minnorm")
        assert run["within_one_over_n"] is True

    def test_a_target_outside_the_hull_is_not_reached(self, report):
        assert report["golay_within_one_over_n"] is False
        assert report["golay_average_deviation"] > Fraction(1, 20)

    def test_the_unreachability_has_an_exact_certificate(self, report):
        assert report["golay_unreachable_certified"] is True
        assert report["golay_certificate_gap"] > 0

    def test_the_certificate_is_verified_against_every_codeword(self):
        ramp = tuple(Fraction(i, 24) for i in range(24))
        certificate = xr.hull_certificate(ramp, 400)
        assert certificate["codewords_checked"] == 4096
        assert certificate["separates"] is True
        assert (certificate["value_at_target"]
                - certificate["max_over_codewords"]) == certificate["gap"]

    def test_the_two_quantiser_rules_agree_on_reachability(self):
        half = tuple(Fraction(1, 2) for _ in range(24))
        for rule in ("nearest", "minnorm"):
            run = xr.golay_delta_sigma(half, 60, rule=rule)
            assert run["within_one_over_n"] is True

    def test_an_unknown_rule_is_refused(self):
        half = tuple(Fraction(1, 2) for _ in range(24))
        with pytest.raises(ValueError):
            xr.golay_delta_sigma(half, 4, rule="hopeful")

    def test_a_float_target_is_refused(self):
        with pytest.raises(TypeError):
            xr.golay_delta_sigma(tuple(0.5 for _ in range(24)), 4)


# ===========================================================================
# 7.  CONTINUED FRACTIONS
# ===========================================================================

class TestContinuedFractions:

    def test_sqrt_two_has_the_expected_terms(self):
        terms = xr.continued_fraction(xr.sqrt(Fraction(2)).at(80), 12)
        assert terms[0] == 1
        assert set(terms[1:]) == {2}

    def test_a_convergent_of_sqrt_two_is_a_pell_pair(self, report):
        # The 30-term convergent of sqrt(2) is the Pell pair p/q with
        # p^2 - 2 q^2 = 1, and it approximates the target to better than
        # 1/q^2 -- both checked here rather than quoted.
        convergent = Fraction(report["cf_sqrt2_convergent_30"])
        p, q = convergent.numerator, convergent.denominator
        assert p ** 2 - 2 * q ** 2 in (1, -1)
        assert abs(convergent - xr.sqrt(Fraction(2)).at(120)) < Fraction(1, q ** 2)


# ===========================================================================
# 8.  THE RUNTIME
# ===========================================================================

class TestRealQueries:

    @pytest.mark.parametrize("query,head", [
        ("approximate sqrt(2) to 20 places", "1.41421356237309504880"),
        ("approximate pi to 12 places", "3.141592653589"),
        ("irrational phi to 12 places", "1.618033988749"),
        ("approximate (1+sqrt(5))/2 to 12 places", "1.618033988749"),
        ("approximate sqrt(2)+sqrt(3) to 12 places", "3.146264369941"),
        ("approximate 7/3 to 6 places", "2.333333"),
    ])
    def test_a_value_is_answered_with_its_digits(self, sess, query, head):
        solution = sess.ask(query)
        assert solution.ok, solution.error
        assert solution.kind == "real"
        assert solution.expected["decimal"] == head

    def test_a_rational_is_said_to_be_held_by_a_carrier(self, sess):
        solution = sess.ask("approximate 7/3 to 6 places")
        assert solution.expected["rational"] == "True"
        assert "a carrier holds it exactly" in solution.answer

    def test_an_irrational_is_said_not_to_be(self, sess):
        solution = sess.ask("approximate sqrt(2) to 20 places")
        assert solution.expected["rational"] == "False"
        assert "no carrier holds it" in solution.answer

    def test_the_answer_carries_the_tower_and_the_modulator(self, sess):
        solution = sess.ask("approximate sqrt(2) to 20 places")
        assert solution.expected["delta_sigma_within_bound"] == "True"
        assert len(solution.payload["stand_ins"]) == 6
        assert all("->" in item for item in solution.payload["exposed"])

    def test_a_notation_it_cannot_read_fails_cleanly(self, sess):
        solution = sess.ask("approximate banana")
        assert not solution.ok
        assert "parse_real" in (solution.error or "")


class TestCompareQueries:

    @pytest.mark.parametrize("query,verdict", [
        ("is sqrt(2) greater than 7/5", "True"),
        ("is sqrt(2) greater than 3/2", "False"),
        ("is pi less than 355/113", "True"),
        ("is e less than 5/2", "False"),
    ])
    def test_a_decidable_comparison_is_decided(self, sess, query, verdict):
        solution = sess.ask(query)
        assert solution.ok, solution.error
        assert solution.kind == "compare"
        assert solution.expected["verdict"] == verdict
        assert solution.expected["settled_at"] != "None"

    def test_an_order_question_gives_the_order(self, sess):
        solution = sess.ask("compare pi and 22/7")
        assert solution.ok
        assert solution.expected["order"] == "-1"
        assert "<" in solution.answer

    def test_equality_of_two_processes_is_not_claimed(self, sess):
        solution = sess.ask("is sqrt(2)*sqrt(2) equal to 2")
        assert solution.ok
        assert solution.expected["verdict"] == "undecided"
        assert "not decidable" in solution.answer

    def test_a_comparison_with_one_side_missing_is_refused(self, sess):
        from glm_universal.runtime.parser import QueryError
        with pytest.raises(QueryError):
            sess.ask("is greater than 7/5")


class TestThirdColumn:
    """Every new answer regenerates itself in a fresh interpreter."""

    @pytest.mark.parametrize("query", [
        "approximate sqrt(2) to 20 places",
        "approximate (1+sqrt(5))/2 to 12 places",
        "is sqrt(2) greater than 7/5",
        "is sqrt(2)*sqrt(2) equal to 2",
    ])
    def test_script_reproduces_the_answer(self, sess, query):
        trace = tct.verify_trace(tct.build_trace(sess.ask(query)))
        verdict = trace.verdict
        assert verdict is not None
        assert verdict.returncode == 0, verdict.stderr_tail
        assert verdict.matches_column2, verdict.mismatches

    def test_the_infinite_values_report_answers(self, sess):
        solution = sess.ask("report infinite values")
        assert solution.ok, solution.error
        assert solution.expected["equality_undecided"] == "True"
        assert solution.expected["golay_unreachable_certified"] == "True"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
