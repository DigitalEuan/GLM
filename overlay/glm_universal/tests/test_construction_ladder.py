"""Tests for the construction ladder and the escalation that walks it.

Three modules are under test, and they answer three different questions:

* ``substrate/golay_paley`` -- does the attached note's 12 x 12 block really
  generate the code this system runs on, and which of the note's claims about
  it survive recomputation?  The four corrections are pinned here, so a later
  round cannot quietly re-adopt the printed versions;
* ``substrate/construction_ladder`` -- are the five rungs the objects they are
  declared to be?  Every rung's minimum norm and kissing number is checked
  against its *generated* theta series rather than against a table, the
  containments are checked shell by shell, and the two witnesses that make the
  ladder a diamond rather than a chain are checked in both directions;
* ``reasoning/ladder_escalation`` -- does the escalation do what
  ``studies/CONSTRUCTION_LADDER_STUDY.md`` says?  The quantisers must land on
  their own rung and order themselves by containment; the measurement is read
  from the cache, which must still describe the sources it was taken from.

Directive D7 -- no float anywhere -- is checked statically on all three.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import ladder_escalation as LE
from glm_universal.substrate import construction_ladder as CL
from glm_universal.substrate import golay_paley as GP
from glm_universal.substrate import leech2, leech_construct as LC


# ═════════════════════════════════════════════════════════════════════════
#  1.  The note's block, and its claims
# ═════════════════════════════════════════════════════════════════════════

class TestGolayPaley:

    def test_block_generates_the_substrate_code(self):
        assert GP.generates_substrate_code()

    def test_weight_enumerator(self):
        assert GP.weight_distribution(sorted(GP.binary_codewords())) == {
            0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}

    def test_self_dual(self):
        assert GP.is_self_orthogonal()
        assert len(GP.binary_codewords()) == 1 << 12

    def test_shortened_code_is_perfect(self):
        report = GP.shortened_code_report()
        assert report["minimum_weight"] == 7
        assert report["perfect"]
        assert report["words_times_ball"] == 1 << 23

    def test_q_is_hadamard_and_q_minus_i_is_not(self):
        check = GP.hadamard_check()
        assert check["q_is_hadamard"]
        assert not check["q_minus_i_is_pm1"]
        assert not check["q_minus_i_is_hadamard"]

    def test_the_design_is_2_11_6_3_and_its_complement_2_11_5_2(self):
        design = GP.bibd_from_core()
        assert design["on_the_ones"]["block_size"] == 6
        assert design["on_the_ones"]["lambda"] == 3
        assert design["on_the_zeros"]["block_size"] == 5
        assert design["on_the_zeros"]["lambda"] == 2
        assert design["on_the_ones"]["symmetric_2_design"]
        assert design["on_the_zeros"]["symmetric_2_design"]

    def test_ternary_codes(self):
        report = GP.ternary_report()
        assert report["extended"]["weight_distribution"] == {
            0: 1, 6: 264, 9: 440, 12: 24}
        assert report["extended"]["words_of_weight_11"] == 0
        assert report["stripped"]["is_11_6_5"]
        assert report["stripped"]["perfect"]
        # The block as printed in the note is not the perfect code.
        assert report["as_printed"]["minimum_weight"] == 2
        assert report["as_printed"]["repeated_row"]

    def test_every_claim_has_a_verdict_and_a_recomputation(self):
        for row in GP.document_claims():
            assert row["verdict"] in (GP.CONFIRMED, GP.CORRECTED, GP.REFUTED)
            for name in str(row["recomputed_by"]).split(", "):
                assert hasattr(GP, name.split(".")[0]) or name.startswith(
                    "reasoning."), name

    def test_the_corrections_are_the_four_found(self):
        report = GP.golay_paley_report()
        assert report["confirmed"] == 7
        assert report["corrected"] == 4
        assert report["refuted"] == 0


# ═════════════════════════════════════════════════════════════════════════
#  2.  The five rungs
# ═════════════════════════════════════════════════════════════════════════

class TestLadder:

    def test_rungs_are_coarse_to_fine(self):
        assert CL.BASE_ORDER == ("B", "C", "A", "D", "Z")
        assert CL.RUNG_ORDER == ("2A", "4D", "4Z", "B", "C", "A",
                                 "2D", "2Z", "A/2", "D", "Z")
        # The thickened ladder keeps its middle where the system reads.
        assert CL.MIDDLE == "A"
        assert CL.BASE_MIDDLE == "A"

    def test_covolumes_fall_and_the_order_is_generated(self):
        covolumes = [CL.rung_spec(key).covolume_log2 for key in CL.RUNG_ORDER]
        assert covolumes == sorted(covolumes, reverse=True)
        assert covolumes == [60, 49, 48, 37, 36, 36, 25, 24, 12, 1, 0]

    def test_generated_series_confirms_every_declared_invariant(self):
        for row in CL.shell_table(64):
            assert row["agrees"], row

    def test_leech_series_agrees_with_the_substrate(self):
        series = CL.theta_series("C", 64)
        stored = leech2.theta_series(order=4)
        assert dict(series["shells"]) == {
            16 * n: count for n, count in enumerate(stored) if count}

    def test_grid_and_checkerboard_shells_are_the_combinatorial_counts(self):
        grid = dict(CL.theta_series("Z", 4)["shells"])
        assert grid[1] == 2 * 24
        assert grid[2] == 4 * (24 * 23 // 2)
        checker = dict(CL.theta_series("D", 4)["shells"])
        assert 1 not in checker
        assert checker[2] == 4 * (24 * 23 // 2)
        # norm 4 with an even coordinate sum: (+-2, 0^23) and (+-1^4).
        assert checker[4] == 2 * 24 + 16 * (24 * 23 * 22 * 21 // 24)

    def test_construction_a_shell_counts_come_from_the_weight_enumerator(self):
        shells = dict(CL.theta_series("A", 32)["shells"])
        assert shells[16] == 48
        # (+-4, +-4) pairs, plus 2^8 sign patterns on each of the 759 octads.
        assert shells[32] == 4 * (24 * 23 // 2) + 759 * 2 ** 8

    def test_containment_implies_shell_by_shell_domination(self):
        order = 48
        series = {rung: CL.theta_series(rung, order)["coefficients"]
                  for rung in CL.RUNG_ORDER}
        for row in CL.inclusion_report()["rows"]:
            if not row["contained"]:
                continue
            lower, upper = str(row["lower"]), str(row["upper"])
            if CL.theta_series(lower, order)["known_to"] is not None:
                limit = int(CL.theta_series(lower, order)["known_to"]) + 1
            else:
                limit = order + 1
            for norm in range(limit):
                assert series[lower][norm] <= series[upper][norm], (
                    lower, upper, norm)

    def test_the_ladder_is_a_diamond_not_a_chain(self):
        report = CL.inclusion_report()
        assert not report["is_a_chain"]
        assert ("A", "C") in report["incomparable_pairs"]
        assert report["witnesses_missing"] == ()

    def test_the_gap_between_the_checkerboard_and_a_is_filled(self):
        report = CL.inclusion_report()
        assert report["filled_gap"] == ("A", "2D", "2Z", "A/2", "D")
        assert report["gap_chain_holds"]

    def test_every_derived_containment_holds_on_generated_points(self):
        check = CL.containment_spot_check()
        assert check["all_hold"], check["failures"]
        assert check["points_checked"] > 0

    def test_the_thickening_narrows_the_widest_step(self):
        report = CL.thickening_report()
        assert report["base_rungs"] == 5 and report["rungs"] == 11
        assert report["middle_unchanged"]
        before = report["widest_step_before"]
        after = report["widest_step_after"]
        assert before["minimum_norms"] == (2, 16)
        assert (int(after["ratio_numerator"])
                <= 2 * int(after["ratio_denominator"]))

    def test_the_two_witnesses(self):
        four_e = (4,) + (0,) * 23
        glue = (-3,) + (1,) * 23
        assert CL.in_rung(four_e, "A") and not CL.in_rung(four_e, "C")
        assert CL.in_rung(glue, "C") and not CL.in_rung(glue, "A")
        assert CL.in_rung(four_e, "D") and CL.in_rung(glue, "D")

    def test_membership_agrees_with_the_existing_construction_module(self):
        octad = tuple(2 if i < 8 else 0 for i in range(24))
        for rung in ("A", "B", "C"):
            assert CL.in_rung(octad, rung) == LC.in_level(octad, rung)

    def test_middle_out_walk(self):
        walk = CL.middle_out_order()
        assert walk[0] == CL.MIDDLE == "A"
        assert sorted(walk) == sorted(CL.RUNG_ORDER)
        assert CL.middle_out_order(CL.BASE_ORDER) == ("A", "D", "C", "Z", "B")

    def test_scaled_rungs_are_the_base_rungs_scaled(self):
        for key in CL.RUNG_ORDER:
            spec = CL.rung_spec(key)
            base = CL.rung_spec(spec.base)
            assert spec.kissing == base.kissing
            assert (spec.covolume_log2
                    == base.covolume_log2 + 24 * spec.exponent)
            if spec.exponent >= 0:
                assert (spec.minimum_norm
                        == base.minimum_norm * 4 ** spec.exponent)
            else:
                assert (spec.minimum_norm * 4 ** -spec.exponent
                        == base.minimum_norm)

    def test_membership_on_a_scaled_rung_is_membership_after_scaling(self):
        octad = tuple(2 if i < 8 else 0 for i in range(24))
        doubled = tuple(2 * value for value in octad)
        assert CL.in_rung(doubled, "2A") == CL.in_rung(octad, "A")
        assert not CL.in_rung(octad, "2A")          # not divisible by 4
        assert CL.in_rung((2,) + (0,) * 23, "2Z")
        assert not CL.in_rung((1,) + (0,) * 23, "2Z")

    def test_a_generated_ladder_of_each_length(self):
        assert CL.ladder_of_length(5) == CL.BASE_ORDER
        assert CL.ladder_of_length(11) == CL.RUNG_ORDER
        for length in (5, 7, 9, 11, 13, 15):
            ladder = CL.ladder_of_length(length)
            assert len(ladder) == length
            assert len(set(ladder)) == length
            assert set(CL.BASE_ORDER) <= set(ladder)
        with pytest.raises(ValueError):
            CL.ladder_of_length(4)

    def test_middle_out_of_any_length_is_a_permutation(self):
        for size in range(1, 9):
            keys = tuple(str(i) for i in range(size))
            walk = CL.middle_out_order(keys)
            assert sorted(walk) == sorted(keys)
            assert walk[0] == keys[size // 2]


# ═════════════════════════════════════════════════════════════════════════
#  3.  The quantisers
# ═════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def sample():
    return LE.sample_carriers()[:4]


class TestQuantisers:

    def test_every_quantiser_lands_on_its_own_rung(self, sample):
        for _, _, carrier in sample:
            for rung in CL.RUNG_ORDER:
                point = LE.quantise(carrier, rung).point
                assert CL.in_rung(point, rung), rung

    def test_distance_respects_containment(self, sample):
        for _, _, carrier in sample:
            distance = {rung: LE.quantise(carrier, rung).distance2
                        for rung in CL.RUNG_ORDER}
            for lower, upper in (("D", "Z"), ("A", "D"), ("C", "D"),
                                 ("B", "A"), ("B", "C"), ("A", "2D"),
                                 ("2D", "2Z"), ("2Z", "A/2"), ("A/2", "D"),
                                 ("2A", "4D"), ("4D", "4Z")):
                assert distance[upper] <= distance[lower], (lower, upper)

    def test_a_scaled_quantiser_is_its_base_quantiser_scaled(self, sample):
        for _, _, carrier in sample:
            halved = tuple(Fraction(value) / 2 for value in carrier)
            scaled = LE.quantise(carrier, "2Z")
            base = LE.quantise(halved, "Z")
            assert scaled.point == tuple(2 * x for x in base.point)
            assert scaled.distance2 == 4 * base.distance2

    def test_work_is_counted_and_costs_rise_with_the_rung(self, sample):
        carrier = sample[0][2]
        costs = {rung: LE.quantise(carrier, rung).cost
                 for rung in CL.RUNG_ORDER}
        assert costs["Z"] <= costs["D"] < costs["A"] <= costs["B"]
        assert costs["A"] < costs["C"]

    def test_perturbation_is_deterministic_and_of_the_declared_support(self,
                                                                       sample):
        carrier = sample[0][2]
        first = LE.perturb(carrier, 3, 8, Fraction(1, 2))
        again = LE.perturb(carrier, 3, 8, Fraction(1, 2))
        assert first == again
        moved = sum(1 for a, b in zip(carrier, first) if a != b)
        assert moved == 8

    def test_a_lattice_point_survives_a_perturbation_inside_its_radius(self):
        # Rung C has minimum norm 32, so a point *of the lattice* moved by an
        # offset of squared length below 8 still quantises to itself.  Eight
        # coordinates by 1/2 is 2.  (The same is not true of an arbitrary
        # query: a carrier near a cell boundary can cross it.)
        point = tuple(Fraction(4) if i < 2 else Fraction(0) for i in range(24))
        assert CL.in_rung(tuple(int(x) for x in point), "C")
        for index in (0, 1, 7):
            query = LE.perturb(point, index, 8, Fraction(1, 2))
            assert LE.quantise(query, "C").point == tuple(
                int(x) for x in point)


# ═════════════════════════════════════════════════════════════════════════
#  4.  The measurement
# ═════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def stored():
    data = LE.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools ladder --write")
    return data


class TestMeasurement:

    def test_the_cache_describes_the_sources(self):
        assert LE.state()["verdict"] == "fresh"

    def test_the_escalation_never_answers_wrongly(self, stored):
        for name, scores in stored["orders"]["totals"].items():
            assert scores["wrong"] == 0, name

    def test_the_escalation_beats_every_fixed_rung(self, stored):
        ladder = stored["orders"]["totals"]["middle_out"]["correct"]
        for rung, scores in stored["fixed_rungs"]["totals"].items():
            if rung == "oracle":
                continue
            assert ladder > scores["correct"], rung

    def test_the_thickened_ladder_beats_the_five_rung_one(self, stored):
        assert stored["ladder_length"] == 11
        after = stored["orders"]["totals"]["middle_out"]["correct"]
        before = stored["before"]["orders"]["totals"]["middle_out"]["correct"]
        assert stored["before"]["ladder_length"] == 5
        assert after > before
        for name, scores in stored["before"]["orders"]["totals"].items():
            assert scores["wrong"] == 0, name

    def test_the_sweep_finds_where_the_ladder_stops_being_safe(self, stored):
        sweep = stored["length_sweep"]
        rows = {row["length"]: row for row in sweep["rows"]}
        assert set(rows) == {5, 7, 9, 11, 13, 15}
        # Correctness is non-decreasing while the ladder is safe.
        safe = [length for length in (5, 7, 9, 11, 13)]
        scores = [rows[length]["correct"]["middle_out"] for length in safe]
        assert scores == sorted(scores)
        for length in safe:
            row = rows[length]
            assert max(row["wrong"].values()) == 0, length
            assert row["rungs_disagree"] == 0, length
            assert row["order_independent"], length
            assert row["matches_oracle"], length
        assert sweep["longest_safe"] == 13
        assert sweep["first_broken"] == 15
        broken = rows[15]
        # The boundary is the hypothesis of the order-independence theorem
        # failing: the rungs disagree, and the orders stop agreeing.
        assert broken["rungs_disagree"] > 0
        assert not broken["order_independent"]
        assert max(broken["wrong"].values()) > 0

    def test_the_stopping_rule_loses_nothing_against_the_oracle(self, stored):
        assert stored["orders"]["totals"]["middle_out"]["correct"] == \
            stored["oracle"]

    def test_every_order_returns_the_same_answers(self, stored):
        counts = {name: scores["correct"]
                  for name, scores in stored["orders"]["totals"].items()}
        assert len(set(counts.values())) == 1, counts
        assert stored["agreement"]["rungs_disagree"] == 0

    def test_the_orders_differ_only_in_cost(self, stored):
        costs = stored["order_cost"]
        assert len(set(costs.values())) > 1
        assert stored["cheapest_order"] in costs
        assert costs[stored["cheapest_order"]] == min(costs.values())

    def test_thickening_moved_the_cheapest_order(self, stored):
        # On the note's five rungs, starting in the middle was the cheapest
        # walk.  On the thickened ladder it is the dearest: the middle rung is
        # a Golay decode, and the coarse end is now reached in fewer visits.
        before = stored["before"]["order_cost"]
        after = stored["order_cost"]
        assert before["middle_out"] < before["coarse_to_fine"]
        assert after["middle_out"] > after["coarse_to_fine"]
        assert stored["cheapest_order"] == "coarse_to_fine"
        assert stored["before"]["cheapest_order"] == "fine_to_coarse"

    def test_the_best_fixed_rung_moves_with_the_perturbation(self, stored):
        best = {row["best_rung"] for row in stored["best_rung_per_setting"]}
        assert len(best) > 1, best

    def test_order_facts(self):
        facts = LE.order_facts()
        assert facts["visits_every_rung_once"]
        assert facts["starts_in_the_middle"]


# ═════════════════════════════════════════════════════════════════════════
#  5.  Exactness (D7)
# ═════════════════════════════════════════════════════════════════════════

class TestExactness:

    @pytest.mark.parametrize("module", [GP, CL, LE])
    def test_no_float_is_constructed(self, module):
        path = Path(module.__file__)
        assert ex.module_float_sites(path) == {}
