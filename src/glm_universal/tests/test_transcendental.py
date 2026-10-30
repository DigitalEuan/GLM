"""Tests for exp, log, sin, cos, tan and the real power ``x^y``.

:mod:`~glm_universal.reasoning.transcendental` extends the process view of a
real number past ``+ - * /``, integer powers and roots.  Every function here
is a rule that returns, for a precision ``k``, an exact ``Fraction`` within
``2**-k`` of the value, and every error budget is paid for in rational
arithmetic -- no float is constructed anywhere in the module.

These tests pin three things.  First, the digits: each value is checked
against its classical expansion to twenty places, so a wrong series or a
mis-stated tail bound shows up immediately.  Second, the identities: ``exp``
inverts ``log``, ``sin**2 + cos**2 = 1``, ``2^(1/3)`` is ``root(3, 2)`` and
``log(2, 8)`` is ``3`` -- an implementation can produce plausible digits and
still fail these.  Third, the boundary: a logarithm needs a positivity
witness for the same reason a division needs a nonzero one, and the inverse
and hyperbolic family is refused *by name* rather than silently mis-answered.

The machine-checked counterparts are in
``RequestProject/GLM/Transcendental.lean``: the Lipschitz bounds the module
budgets against, the positivity witness as an equivalence, and
``x ** y = exp (y * log x)`` for a positive base.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import exact_real as xr
from glm_universal.reasoning import real_expr as rx
from glm_universal.reasoning import transcendental as tr


@pytest.fixture(scope="module")
def report():
    return tr.transcendental_report()


#: The first twenty decimal places, from the classical expansions.  The
#: module must reproduce them digit for digit.
KNOWN_DIGITS = {
    "exp(1)": "2.71828182845904523536",
    "log(2)": "0.69314718055994530941",
    "log(10)": "2.30258509299404568401",
    "sin(1)": "0.84147098480789650665",
    "cos(1)": "0.54030230586813971740",
    "tan(1)": "1.55740772465490223050",
    "2^pi": "8.82497782707628762385",
    "2^(1/3)": "1.25992104989487316476",
}


def _one() -> xr.ExactReal:
    return xr.from_fraction(Fraction(1))


# ===========================================================================
# 1.  THE DIGITS
# ===========================================================================

class TestDigits:

    @pytest.mark.parametrize("text,expected", sorted(KNOWN_DIGITS.items()))
    def test_written_expression_reproduces_the_classical_expansion(
            self, text, expected):
        assert rx.parse_expression(text).decimal(20) == expected

    def test_the_module_and_the_grammar_agree(self):
        direct = tr.exp(_one())
        written = rx.parse_expression("exp(1)")
        assert abs(direct.at(70) - written.at(70)) <= Fraction(1, 2 ** 66)

    def test_a_negative_argument(self):
        assert (rx.parse_expression("exp(0-3)").decimal(20)
                == "0.04978706836786394297")

    def test_a_large_argument_is_slow_and_not_wrong(self):
        # No reduction modulo pi is attempted; the series is simply summed.
        assert (rx.parse_expression("sin(10)").decimal(20)
                == "-0.54402111088936981341")

    def test_more_precision_does_not_change_the_digits_already_shown(self):
        value = rx.parse_expression("log(2)")
        assert value.decimal(40).startswith(KNOWN_DIGITS["log(2)"])


# ===========================================================================
# 2.  THE RATIONAL KERNELS
# ===========================================================================

class TestRationalKernels:
    """Each kernel must be within ``2**-k`` of the value, at every ``k``."""

    @pytest.mark.parametrize("k", [4, 12, 24, 48])
    def test_exp_kernel_is_within_its_stated_bound(self, k):
        # Checked against the process, which is itself refined further.
        near = tr.rational_exp_approx(Fraction(3, 2), k)
        far = tr.exp(xr.from_fraction(Fraction(3, 2))).at(k + 20)
        assert abs(near - far) <= Fraction(1, 2 ** k)

    @pytest.mark.parametrize("k", [4, 12, 24, 48])
    def test_log_kernel_is_within_its_stated_bound(self, k):
        near = tr.rational_log_approx(Fraction(7, 3), k)
        far = tr.log(xr.from_fraction(Fraction(7, 3))).at(k + 20)
        assert abs(near - far) <= Fraction(1, 2 ** k)

    @pytest.mark.parametrize("k", [4, 12, 24, 48])
    def test_sin_and_cos_kernels_are_within_their_stated_bounds(self, k):
        for kernel, process in ((tr.rational_sin_approx, tr.sin),
                                (tr.rational_cos_approx, tr.cos)):
            near = kernel(Fraction(5, 4), k)
            far = process(xr.from_fraction(Fraction(5, 4))).at(k + 20)
            assert abs(near - far) <= Fraction(1, 2 ** k)

    def test_every_kernel_returns_an_exact_rational(self):
        for value in (tr.rational_exp_approx(Fraction(1), 30),
                      tr.rational_log_approx(Fraction(2), 30),
                      tr.rational_sin_approx(Fraction(1), 30),
                      tr.rational_cos_approx(Fraction(1), 30),
                      tr.log_two_approx(30)):
            assert isinstance(value, Fraction)

    def test_log_two_kernel_agrees_with_the_process(self):
        assert abs(tr.log_two_approx(60)
                   - tr.log(xr.from_fraction(Fraction(2))).at(80)) \
            <= Fraction(1, 2 ** 60)

    def test_a_kernel_refuses_a_float(self):
        with pytest.raises(TypeError):
            tr.rational_sin_approx(1.0, 10)


# ===========================================================================
# 3.  THE IDENTITIES
# ===========================================================================

class TestIdentities:

    def test_exp_inverts_log(self):
        value = rx.parse_expression("exp(log(7/2))")
        assert abs(value.at(60) - Fraction(7, 2)) <= Fraction(1, 2 ** 55)

    def test_log_inverts_exp(self):
        value = rx.parse_expression("log(exp(3))")
        assert abs(value.at(60) - 3) <= Fraction(1, 2 ** 55)

    def test_pythagorean_identity(self):
        value = rx.parse_expression("sin(1)^2+cos(1)^2")
        assert abs(value.at(60) - 1) <= Fraction(1, 2 ** 55)

    def test_tan_is_sin_over_cos(self):
        left = rx.parse_expression("tan(1)")
        right = rx.parse_expression("sin(1)/cos(1)")
        assert abs(left.at(60) - right.at(60)) <= Fraction(1, 2 ** 55)

    def test_exp_of_one_is_the_constant_e(self):
        assert abs(rx.parse_expression("exp(1)").at(80) - xr.e().at(80)) \
            <= Fraction(1, 2 ** 78)

    def test_a_logarithm_to_a_base(self):
        assert abs(rx.parse_expression("log(2, 8)").at(60) - 3) \
            <= Fraction(1, 2 ** 55)

    def test_a_fractional_power_is_the_root(self):
        left = rx.parse_expression("2^(1/3)")
        right = rx.parse_expression("root(3, 2)")
        assert abs(left.at(60) - right.at(60)) <= Fraction(1, 2 ** 55)

    def test_a_half_power_is_the_square_root(self):
        left = rx.parse_expression("2^0.5")
        right = rx.parse_expression("sqrt(2)")
        assert abs(left.at(60) - right.at(60)) <= Fraction(1, 2 ** 55)

    def test_the_power_route_is_exp_of_the_log(self):
        two = xr.from_fraction(Fraction(2))
        direct = tr.rpow(two, xr.pi())
        written = rx.parse_expression("exp(pi*log(2))")
        assert abs(direct.at(60) - written.at(60)) <= Fraction(1, 2 ** 55)

    def test_one_to_any_power_is_one(self):
        value = tr.rpow(xr.from_fraction(Fraction(1)), xr.pi())
        assert value.at(40) == 1


# ===========================================================================
# 4.  THE POSITIVITY WITNESS
# ===========================================================================

class TestPositivityWitness:
    """``log`` needs one for the reason division needs a nonzero witness."""

    def test_a_positive_value_has_a_witness(self):
        exponent = tr.positive_witness(xr.from_fraction(Fraction(2)))
        assert exponent is not None
        assert xr.from_fraction(Fraction(2)).at(exponent + 4) \
            >= Fraction(1, 2 ** exponent)

    def test_a_small_positive_value_still_has_one(self):
        tiny = xr.from_fraction(Fraction(1, 2 ** 40))
        assert tr.positive_witness(tiny) is not None

    def test_a_value_that_is_zero_has_no_witness_at_any_depth(self):
        two = xr.from_fraction(Fraction(2))
        assert tr.positive_witness(two - two, 24) is None
        assert tr.positive_witness(two - two, 64) is None

    def test_a_value_below_zero_has_no_witness(self):
        assert tr.positive_witness(xr.from_fraction(Fraction(-1)), 24) is None

    def test_the_search_depth_is_the_one_the_module_names(self):
        assert tr.POSITIVE_WITNESS_DEPTH == 96

    def test_log_of_something_not_known_positive_is_refused(self):
        undecided = xr.sqrt(Fraction(2)) - xr.sqrt(Fraction(2))
        with pytest.raises(xr.PrecisionError):
            tr.log(undecided, None, 24)

    def test_the_refusal_names_the_depth_it_searched_to(self):
        with pytest.raises(xr.PrecisionError) as caught:
            rx.parse_expression("log(sqrt(2)-sqrt(2))", depth=24).at(16)
        assert "24" in str(caught.value)

    def test_an_argument_known_to_be_zero_is_refused_by_its_value(self):
        # Nothing is searched for here: the value is exactly zero, so the
        # refusal names the value rather than a depth.
        with pytest.raises(rx.ExpressionError) as caught:
            rx.parse_expression("log(1-1)", depth=24).at(16)
        assert "not positive" in str(caught.value)

    def test_a_power_inherits_the_witness(self):
        with pytest.raises(xr.PrecisionError):
            rx.parse_expression("(sqrt(2)-sqrt(2))^pi", depth=24).at(16)

    def test_a_power_of_an_exactly_zero_base_is_refused_by_its_value(self):
        with pytest.raises(rx.ExpressionError):
            rx.parse_expression("0^pi", depth=24).at(16)


# ===========================================================================
# 5.  WHERE IT STOPS
# ===========================================================================

class TestWhereItStops:

    @pytest.mark.parametrize("text", [
        "asin(1)", "acos(1)", "atan(1)", "arcsin(1)", "arctan(1)",
        "sinh(1)", "cosh(1)", "tanh(1)", "asinh(1)", "erf(1)", "gamma(2)",
        "zeta(2)",
    ])
    def test_the_unbuilt_family_is_refused_by_name(self, text):
        with pytest.raises(rx.ExpressionError):
            rx.parse_expression(text)

    def test_the_unbuilt_family_is_listed_rather_than_discovered(self):
        for name in ("asin", "atan", "sinh", "erf", "gamma", "zeta"):
            assert name in rx.UNBUILT_FUNCTIONS

    def test_the_refusal_says_what_would_be_needed(self):
        with pytest.raises(rx.ExpressionError) as caught:
            rx.parse_expression("asin(1)")
        assert "asin" in str(caught.value)

    def test_a_negative_base_with_a_real_exponent_has_no_real_value(self):
        with pytest.raises((rx.ExpressionError, xr.PrecisionError)):
            rx.parse_expression("(0-2)^pi", depth=24).at(16)

    def test_a_negative_base_with_an_integer_exponent_is_fine(self):
        assert rx.parse_expression("(0-2)^3").at(20) == Fraction(-8)


# ===========================================================================
# 6.  THE REPORT RECOMPUTES ITS OWN CLAIMS
# ===========================================================================

class TestReport:

    @pytest.mark.parametrize("key", [
        "exp_1_is_e", "log_inverts_exp", "pythagorean_identity",
        "power_agrees_with_grammar", "fractional_power_is_the_root",
        "sin_half_below_half",
    ])
    def test_every_claim_holds(self, report, key):
        assert report[key] is True

    @pytest.mark.parametrize("key,text", [
        ("exp_1_decimal_20", "exp(1)"),
        ("log_2_decimal_20", "log(2)"),
        ("sin_1_decimal_20", "sin(1)"),
        ("cos_1_decimal_20", "cos(1)"),
        ("tan_1_decimal_20", "tan(1)"),
        ("two_to_the_pi_decimal_20", "2^pi"),
    ])
    def test_the_reported_digits_are_the_known_ones(self, report, key, text):
        assert report[key] == KNOWN_DIGITS[text]

    def test_the_report_records_the_witness_and_its_absence(self, report):
        assert report["positive_witness_depth"] == 96
        assert report["witness_for_2"] is not None
        assert report["witness_for_a_difference_that_is_zero"] is None

    @pytest.mark.parametrize("text", [
        "log(0)", "log(1-1)", "asin(1)", "atan(1)", "0^pi", "(0-1)^pi",
    ])
    def test_every_recorded_refusal_really_refuses(self, report, text):
        assert report["refusals"][text] != "accepted"

    def test_the_module_exports_what_it_documents(self):
        from glm_universal import reasoning
        for name in ("exp", "log", "sin", "cos", "tan", "rpow",
                     "positive_witness", "transcendental_report"):
            assert hasattr(reasoning, name)
            assert name in tr.__all__ or name in reasoning.__all__
