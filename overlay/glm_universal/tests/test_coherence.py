"""Unit tests for ``glm_universal.reasoning.coherence``.

The coherence module used to be the one place in the package where a float
was constructed: NRCI shells 2 and 4 involve a square root.  They now take
that root rationally, at a declared resolution, so the module is exact like
the rest of the package.  These tests pin that down:

* :func:`rational_sqrt` really is a floor root at resolution
  ``1/SQRT_DENOM``, and it is exact on perfect squares;
* :func:`decimal_str` renders a rational by integer arithmetic alone, cutting
  toward zero at the requested number of places;
* every shell, the combined tax and the NRCI are :class:`Fraction` values;
* NRCI lies in ``(0, 1]``, is ``1`` exactly on the vacuum, and falls as tax
  is added;
* the regime thresholds are exact rationals, so a value sitting exactly on a
  threshold lands on the documented side of it;
* the same carrier gives the same Fraction on every call.

Run with::

    uv run pytest glm_universal/tests/test_coherence.py -q
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import coherence as CO

VACUUM = [0] * 24
OCTAD = [1] * 8 + [0] * 16
SIGNED_OCTAD = [1, -1] * 4 + [0] * 16
SPREAD = [1, 0, 0, 0, 0, 0] * 4
SKEWED = [1] * 6 + [0] * 18
CARRIERS = [VACUUM, OCTAD, SIGNED_OCTAD, SPREAD, SKEWED]


# ===========================================================================
# 1.  RATIONAL SQUARE ROOTS
# ===========================================================================

class TestRationalSqrt:

    @pytest.mark.parametrize("x", [Fraction(0), Fraction(1), Fraction(4),
                                   Fraction(9), Fraction(1, 4),
                                   Fraction(25, 16)])
    def test_exact_on_perfect_squares(self, x):
        root = CO.rational_sqrt(x)
        assert root * root == x

    @pytest.mark.parametrize("x", [Fraction(2), Fraction(3), Fraction(5),
                                   Fraction(7, 3), Fraction(123, 7)])
    def test_is_the_floor_root_at_the_declared_resolution(self, x):
        root = CO.rational_sqrt(x)
        step = Fraction(1, CO.SQRT_DENOM)
        assert root * root <= x
        assert (root + step) * (root + step) > x

    def test_denominator_divides_the_declared_resolution(self):
        root = CO.rational_sqrt(Fraction(2))
        assert CO.SQRT_DENOM % root.denominator == 0

    def test_negative_argument_is_zero(self):
        assert CO.rational_sqrt(Fraction(-1)) == 0

    def test_a_coarser_resolution_is_still_a_lower_bound(self):
        coarse = CO.rational_sqrt(Fraction(2), 10 ** 3)
        fine = CO.rational_sqrt(Fraction(2))
        assert coarse <= fine
        assert coarse * coarse <= 2

    def test_returns_a_fraction_never_a_float(self):
        assert isinstance(CO.rational_sqrt(Fraction(2)), Fraction)


# ===========================================================================
# 2.  EXACT DECIMAL DISPLAY
# ===========================================================================

class TestDecimalStr:

    @pytest.mark.parametrize("value,places,expected", [
        (Fraction(1), 6, "1.000000"),
        (Fraction(1, 2), 4, "0.5000"),
        (Fraction(1, 3), 4, "0.3333"),
        (Fraction(2, 3), 4, "0.6666"),          # truncated, not rounded
        (Fraction(-1, 3), 4, "-0.3333"),
        (Fraction(7), 0, "7"),
        (Fraction(0), 3, "0.000"),
    ])
    def test_renders_as_documented(self, value, places, expected):
        assert CO.decimal_str(value, places) == expected

    def test_truncates_toward_zero(self):
        assert CO.decimal_str(Fraction(9999, 10000), 3) == "0.999"
        assert CO.decimal_str(Fraction(-9999, 10000), 3) == "-0.999"

    def test_more_places_extends_rather_than_changes(self):
        short = CO.decimal_str(Fraction(1, 7), 4)
        long = CO.decimal_str(Fraction(1, 7), 8)
        assert long.startswith(short)

    def test_y_decimal_matches_the_rational_constant(self):
        assert CO.decimal_str(CO.Y, 15) == CO.Y_DECIMAL


# ===========================================================================
# 3.  THE FIVE SHELLS ARE EXACT
# ===========================================================================

class TestShellsAreExact:

    @pytest.mark.parametrize("shell", [CO.tax_shell0, CO.tax_shell1,
                                       CO.tax_shell2, CO.tax_shell3,
                                       CO.tax_shell4])
    def test_every_shell_returns_a_fraction(self, shell):
        for carrier in CARRIERS:
            assert isinstance(shell(carrier), Fraction)

    def test_every_shell_is_nonnegative(self):
        for carrier in CARRIERS:
            for shell in (CO.tax_shell0, CO.tax_shell1, CO.tax_shell2,
                          CO.tax_shell3, CO.tax_shell4):
                assert shell(carrier) >= 0

    def test_the_vacuum_pays_no_tax(self):
        for shell in (CO.tax_shell0, CO.tax_shell1, CO.tax_shell2,
                      CO.tax_shell3, CO.tax_shell4):
            assert shell(VACUUM) == 0
        assert CO.combined_tax(VACUUM) == 0

    def test_shell0_is_the_documented_formula(self):
        hw = sum(1 for x in OCTAD if x != 0)
        norm2 = sum(Fraction(x) ** 2 for x in OCTAD)
        assert CO.tax_shell0(OCTAD) == Fraction(hw) * CO.Y + norm2 / 8

    def test_shell1_is_zero_on_balanced_signs_and_one_on_uniform_signs(self):
        assert CO.tax_shell1(SIGNED_OCTAD) == 0
        assert CO.tax_shell1(OCTAD) == 1

    def test_shell2_is_zero_on_an_evenly_spread_carrier(self):
        assert CO.tax_shell2(SPREAD) == 0
        assert CO.tax_shell2(SKEWED) > 0

    def test_shell3_is_a_twelfth_multiple(self):
        for carrier in CARRIERS:
            assert (CO.tax_shell3(carrier) * 12).denominator == 1

    def test_combined_tax_is_the_weighted_sum(self):
        for carrier in CARRIERS:
            expected = (CO.tax_shell0(carrier)
                        + CO.ALPHA[0] * CO.tax_shell1(carrier)
                        + CO.ALPHA[1] * CO.tax_shell2(carrier)
                        + CO.ALPHA[2] * CO.tax_shell3(carrier)
                        + CO.ALPHA[3] * CO.tax_shell4(carrier))
            assert CO.combined_tax(carrier) == expected


# ===========================================================================
# 4.  NRCI
# ===========================================================================

class TestNRCI:

    def test_returns_a_fraction_in_the_unit_interval(self):
        for carrier in CARRIERS:
            value = CO.nrci(carrier)
            assert isinstance(value, Fraction)
            assert 0 < value <= 1

    def test_the_vacuum_is_perfectly_coherent(self):
        assert CO.nrci(VACUUM) == 1
        assert CO.coherence_regime(CO.nrci(VACUUM)) == "OnBit"

    def test_more_tax_means_less_coherence(self):
        light = [1] + [0] * 23
        heavy = [1] * 24
        assert CO.combined_tax(light) < CO.combined_tax(heavy)
        assert CO.nrci(light) > CO.nrci(heavy)

    def test_nrci_is_the_budget_form(self):
        for carrier in CARRIERS:
            tax = CO.combined_tax(carrier)
            assert CO.nrci(carrier) == CO.B / (CO.B + tax)

    def test_breakdown_agrees_with_the_standalone_functions(self):
        for carrier in CARRIERS:
            bd = CO.nrci_breakdown(carrier)
            assert bd["nrci"] == CO.nrci(carrier)
            assert bd["tax_total"] == CO.combined_tax(carrier)
            assert bd["shell2_sextet_balance"] == CO.tax_shell2(carrier)
            assert bd["shell4_sextet_signed"] == CO.tax_shell4(carrier)
            assert isinstance(bd["nrci"], Fraction)
            assert isinstance(bd["tax_total"], Fraction)

    def test_the_class_reproduces_the_functions_with_all_shells_on(self):
        engine = CO.RefinedNRCI()
        for carrier in CARRIERS:
            assert engine.compute(carrier) == CO.nrci(carrier)
            assert isinstance(engine.compute(carrier), Fraction)

    def test_disabling_a_shell_can_only_raise_the_coherence(self):
        full = CO.RefinedNRCI()
        without4 = CO.RefinedNRCI(use_shell4=False)
        for carrier in CARRIERS:
            assert without4.compute(carrier) >= full.compute(carrier)

    def test_repeated_calls_give_the_identical_rational(self):
        for carrier in CARRIERS:
            assert CO.nrci(carrier) == CO.nrci(carrier)
            assert CO.nrci_breakdown(carrier) == CO.nrci_breakdown(carrier)


# ===========================================================================
# 5.  REGIMES ARE DECIDED ON EXACT THRESHOLDS
# ===========================================================================

class TestCoherenceRegime:

    @pytest.mark.parametrize("value,regime", [
        (Fraction(1), "OnBit"),
        (Fraction(4, 5), "OnBit"),
        (Fraction(799, 1000), "Coherent"),
        (Fraction(1, 2), "Coherent"),
        (Fraction(499, 1000), "Transitional"),
        (Fraction(3, 10), "Transitional"),
        (Fraction(299, 1000), "Subcoherent"),
        (Fraction(0), "Subcoherent"),
    ])
    def test_thresholds_are_exact_and_inclusive_from_above(self, value,
                                                           regime):
        assert CO.coherence_regime(value) == regime

    def test_a_value_on_a_threshold_is_not_at_the_mercy_of_rounding(self):
        # 4/5 is not representable in binary floating point; the exact
        # comparison still puts it in OnBit, every time.
        assert CO.coherence_regime(Fraction(4, 5)) == "OnBit"
        assert CO.coherence_regime(Fraction(4, 5) - Fraction(1, 10 ** 30)) \
            == "Coherent"

    def test_breakdown_regime_matches_the_standalone_call(self):
        for carrier in CARRIERS:
            bd = CO.nrci_breakdown(carrier)
            assert bd["regime"] == CO.coherence_regime(bd["nrci"])


# ===========================================================================
# 6.  NO FLOAT IS CONSTRUCTED IN THE MODULE
# ===========================================================================

class TestModuleExactness:

    def test_the_source_builds_no_float(self):
        path = Path(CO.__file__)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value,
                                                             float):
                offenders.append(f"line {node.lineno}: float literal")
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "float"):
                offenders.append(f"line {node.lineno}: float() call")
        assert not offenders, offenders

    def test_the_module_no_longer_exports_a_float_constant(self):
        assert not hasattr(CO, "Y_FLOAT")
        assert isinstance(CO.Y, Fraction)
        assert isinstance(CO.Q, Fraction)
        assert isinstance(CO.B, Fraction)
        assert CO.Q == CO.Y + CO.Z_STAR

    def test_everything_advertised_is_present(self):
        for name in CO.__all__:
            assert hasattr(CO, name), name
