"""Tests for the two lattice rungs above the Leech lattice.

``substrate/lattice32`` builds the 32-dimensional Barnes-Wall lattice by
Construction D over a nested dual pair of Reed-Muller codes;
``substrate/lattice48`` builds a certified extremal 48-dimensional even
unimodular lattice over the ternary Pless symmetry code ``C(23)``;
``reasoning/higher_lattices`` assembles both into the ladder and reports the
multi-resolution addressing the 32-dimensional rung buys.

The machine-checked counterparts live in
``RequestProject/GLM/HigherLattices.lean`` --
``BarnesWall.norm_ge_of_ne_zero``, ``BarnesWall.norm_dvd_eight``,
``BarnesWall.mk_injective`` and ``Ternary.even_norm_ge_eighteen`` -- so what is
checked here is that the code builds the objects those theorems are about, in
exact arithmetic, and that the numerical inputs the theorems assume really
hold.

The exhaustive searches (``2^24`` binary codewords, ``2^23`` ternary
information vectors, information support up to 6 over both information sets)
are opt-in and are exercised by the ``test_exhaustive_*`` cases, which take a
few seconds each.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import higher_lattices as hlt
from glm_universal.runtime.session import GeometricSession
from glm_universal.substrate import lattice32 as L32
from glm_universal.substrate import lattice48 as L48


@pytest.fixture(scope="module")
def r32():
    return L32.lattice32_report()


@pytest.fixture(scope="module")
def r48():
    return L48.lattice48_report()


@pytest.fixture(scope="module")
def ladder():
    return hlt.higher_lattices_report()


class TestThirtyTwoCodes:
    """The two Reed-Muller codes, with the parameters the theorem assumes."""

    def test_outer_code_is_32_6_16(self, r32):
        outer = r32["codes"]["outer"]
        assert (outer["length"], outer["dimension"],
                outer["minimum_weight"]) == (32, 6, 16)
        assert outer["words"] == 64
        assert outer["weights"] == [0, 16, 32]

    def test_inner_code_is_32_26_4(self, r32):
        inner = r32["codes"]["inner"]
        assert (inner["length"], inner["dimension"],
                inner["minimum_weight"]) == (32, 26, 4)
        assert inner["sub_minimum_witnesses"] == 0
        assert inner["weight_4_words"] == 1240

    def test_the_codes_are_nested_and_dual(self, r32):
        assert r32["codes"]["nested"] is True
        assert r32["codes"]["dual"]["is_dual_pair"] is True
        assert r32["codes"]["dual"]["dimensions_sum"] == 32


class TestThirtyTwoLattice:
    """Minimum, evenness, determinant and the kissing census."""

    def test_minimum_is_extremal(self, r32):
        assert r32["minimum"]["minimum_norm2"] == 16
        assert r32["minimum"]["lattice_minimum"] == 4
        assert r32["minimum"]["is_extremal"] is True

    def test_every_case_of_the_argument_reaches_16(self, r32):
        assert [case["bound"] for case in r32["minimum"]["cases"]] \
            == [16, 16, 16]

    def test_unimodular_and_even(self, r32):
        det = r32["determinant"]
        assert det["gram_determinant_is_2_to_64"] is True
        assert det["scaled_determinant"] == 1
        assert det["unimodular"] is True
        assert det["even"] is True

    def test_kissing_number(self, r32):
        census = r32["kissing"]["census"]
        assert census["total"] == 146880
        assert census["distinct"] == 146880
        assert sum(census["counts"].values()) == 146880
        assert r32["kissing"]["agrees"] is True

    def test_address_is_a_bijection_on_probes(self):
        trip = hlt.address_round_trip()
        assert trip["all_in_lattice"] is True
        assert trip["all_round_trip"] is True
        assert trip["all_levels_usable"] is True

    def test_index_ladder_multiplies_out(self):
        gain = hlt.resolution_gain()
        assert gain["coarse_addresses"] == 64
        assert gain["middle_addresses"] == 2 ** 26
        assert gain["total_index"] == 2 ** 32
        assert gain["product_is_total"] is True


class TestFortyEightCodes:
    """The binary code that is not enough, and the ternary one that is."""

    def test_binary_qr47_is_self_dual_doubly_even(self, r48):
        code = r48["binary_route"]["code"]
        assert code["dimension"] == 24
        assert code["self_dual"] is True
        assert code["doubly_even_generators"] is True
        assert code["doubly_even_pairs"] is True

    def test_ternary_symmetry_matrix(self):
        report = L48.ternary_code_report()
        assert report["skew_symmetric"] is True
        assert report["S_times_S_transpose_is_minus_I_mod_3"] is True
        assert report["self_orthogonal"] is True
        assert report["self_dual"] is True
        assert report["second_information_set"] is True

    def test_ternary_weights_divisible_by_three(self):
        report = L48.ternary_code_report()
        assert report["all_weights_divisible_by_3"] is True
        assert report["pair_weights"] == [15]

    def test_extremal_weight_enumerator(self):
        we = L48.weight_enumerator()
        assert we["all_nonnegative_integers"] is True
        assert we["total_is_3_to_24"] is True
        assert we["minimum_weight"] == 15
        assert we["A_48"] == 96


class TestFortyEightLattice:
    """Construction A, the even sublattice, and the neighbour that is extremal."""

    def test_construction_a_is_odd_unimodular_minimum_three(self, r48):
        ca = r48["construction_a"]
        assert ca["unimodular"] is True
        assert ca["even"] is False
        assert ca["minimum"] == 3

    def test_even_sublattice_reaches_six(self, r48):
        ev = r48["even_sublattice"]
        assert ev["index_in_A"] == 2
        assert ev["determinant"] == 4
        assert ev["minimum_norm2"] == 18
        assert ev["minimum"] == 6

    def test_both_glue_vectors_have_even_norm(self, r48):
        glue = r48["neighbours"]["glue_vectors"]
        assert glue["h_norm"] == 36
        assert glue["h_prime_norm"] == 42
        assert glue["both_even"] is True

    def test_the_two_neighbours_are_separated_by_parity(self, r48):
        n = r48["neighbours"]
        assert n["N1"]["coset"]["parity_required_on_twos"] == "even"
        assert n["N2"]["coset"]["parity_required_on_twos"] == "odd"
        assert n["N1"]["minimum"] == 4
        assert n["N2"]["minimum"] == 6
        assert n["N2"]["extremal"] is True

    def test_census_cross_checks_against_the_enumerator(self, r48):
        census = r48["neighbours"]["census"]
        assert census["total"] == 96
        assert census["even_number_of_twos"] == 96
        assert census["odd_number_of_twos"] == 0
        assert census["cross_check_A_48"] == 96

    def test_binary_route_lattice_minimum_is_two(self, r48):
        assert r48["binary_route"]["lattice_minimum"] == 2


class TestLadder:
    """The ladder as a whole, with exact centre densities."""

    def test_every_rung_is_extremal(self, ladder):
        assert ladder["ladder"]["all_extremal"] is True

    def test_centre_densities(self):
        assert hlt.centre_density(8, 2) == Fraction(1, 16)
        assert hlt.centre_density(24, 4) == 1
        assert hlt.centre_density(32, 4) == 1
        assert hlt.centre_density(48, 6) == Fraction(3, 2) ** 24

    def test_the_48_is_denser_than_the_leech(self, ladder):
        gain = ladder["ladder"]["density_gain_over_leech"]
        assert gain[24] == 1
        assert gain[32] == 1
        assert gain[48] == Fraction(3, 2) ** 24
        assert gain[48] > 16000

    def test_kissing_numbers_are_the_computed_ones(self, ladder):
        rows = {r["dimension"]: r for r in ladder["ladder"]["rows"]}
        assert rows[24]["kissing"] == 196560
        assert rows[32]["kissing"] == 146880
        assert rows[48]["kissing"] is None


@pytest.mark.exhaustive
class TestExhaustive:
    """The searches that certify rather than record.

    Marked ``exhaustive``: deselected on a routine run, run in full at round
    close and under ``--exhaustive``.  See ``overlay/conftest.py``.
    """

    def test_exhaustive_binary_minimum_distance(self):
        result = L48.binary_minimum_distance(True)
        assert result["dimension"] == 24
        assert result["minimum_weight"] == 12
        assert result["agrees"] is True

    def test_exhaustive_ternary_minimum_distance(self):
        result = L48.ternary_minimum_distance(6)
        assert result["excludes_weights_up_to"] == 12
        assert result["best_weight_found"] == 15
        assert result["certifies_minimum_15"] is True

    def test_exhaustive_full_weight_census(self):
        census = L48.full_weight_census(True)
        assert census["exhaustive"] is True
        assert census["with_leading_one"] == 48
        assert census["total"] == 96
        assert census["even_number_of_twos"] == 96
        assert census["odd_number_of_twos"] == 0
        assert census["agrees_with_enumerator"] is True


class TestRuntimeWiring:
    """``report lattices`` reaches the study and reproduces it."""

    def test_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "lattices" in REPORT_SUBJECTS

    def test_report_answers(self):
        session = GeometricSession()
        solution = session.ask("report lattices")
        assert solution.kind == "report"
        assert "three-resolution address" in solution.answer
        assert "even number of 2s" in solution.answer
        assert len(solution.steps) == 6

    def test_expected_values_carry_the_headline_numbers(self):
        session = GeometricSession()
        expected = session.ask("report lattices").expected
        assert expected["kissing_32"] == "146880"
        assert expected["N2_minimum"] == "6/1"
        assert expected["N2_extremal"] == "True"
        assert expected["full_weight_even"] == "96"
        assert expected["all_extremal"] == "True"

    def test_aliases_reach_the_same_solver(self):
        session = GeometricSession()
        head = session.ask("report lattices").answer
        for alias in ("report higher lattices", "report barnes-wall",
                      "report ladder"):
            assert session.ask(alias).answer == head
