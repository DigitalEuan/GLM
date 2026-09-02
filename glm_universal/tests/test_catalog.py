"""Tests for ``reasoning/catalog`` and its runtime wiring.

``source_material/glm_study_findings_catalog.md`` records the findings of a series of external
studies.  This module turns that record into a live claim ledger: every
testable sentence is recomputed against the package and given one of four
verdicts.  What the tests below pin is not the verdicts' *values* -- those are
allowed to move when the package does, which is the point of a live ledger --
but that every claim is settled by a computation, that the ledger covers all
six sections, that no verdict is invented, and that the arithmetic the ledger
leans on (the code-to-lattice ladder, the generator step costs) is right.

The figures reached through this ledger are backed by theorems of
``RequestProject/GLM/Sturmian.lean`` (the spectral columns),
``RequestProject/GLM/Mantissa.lean`` (the 53-bit question) and
``RequestProject/GLM/Cascade.lean`` (the modulator's error bound).
"""

from __future__ import annotations

import pytest

from glm_universal.reasoning import catalog as cat
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return cat.catalog_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE CODE-TO-LATTICE LADDER
# ===========================================================================

class TestLatticeLadder:

    def test_reed_muller_is_generated_at_the_right_size(self):
        assert len(cat.first_order_reed_muller(3)) == 16
        assert len(cat.first_order_reed_muller(4)) == 32
        assert cat.minimum_weight(cat.first_order_reed_muller(3)) == (4, 14)
        assert cat.minimum_weight(cat.first_order_reed_muller(4)) == (8, 30)

    def test_a_degenerate_dimension_is_refused(self):
        with pytest.raises(ValueError):
            cat.first_order_reed_muller(0)

    def test_construction_a_gives_d4_and_e8(self):
        rows = {row["code"]: row for row in cat.lattice_ladder()}
        assert rows["parity [4,3,2]"]["construction_a_kissing"] == 24
        assert rows["ext. Hamming [8,4,4]"]["construction_a_kissing"] == 240

    def test_construction_a_does_not_give_barnes_wall(self):
        """The catalogue's third rung is the claim that fails."""
        rows = {row["code"]: row for row in cat.lattice_ladder()}
        rung = rows["Reed-Muller RM(1,4) [16,5,8]"]
        assert rung["claimed_kissing"] == 4320
        assert rung["construction_a_kissing"] != 4320
        assert not rung["matches"]

    def test_the_leech_row_is_reached_by_the_substrates_own_ladder(self):
        rows = {row["code"]: row for row in cat.lattice_ladder()}
        leech = rows["ext. binary Golay [24,12,8]"]
        assert leech["abc_ladder_kissing"] == 196560
        assert leech["construction_a_kissing"] == cat.construction_a_leech_only()
        assert leech["construction_a_kissing"] < 196560


# ===========================================================================
# 2.  GENERATOR STEP COSTS
# ===========================================================================

class TestGeneratorCosts:

    def test_heron_doubles_its_correct_bits(self):
        cost = cat.heron_step_cost(2)
        assert cost[10] <= cost[30] <= cost[50] <= cost[100]
        assert cost[100] - cost[50] == 1

    def test_the_fifty_bit_column_is_reproduced_except_at_thirteen(self):
        band = {n: cat.heron_step_cost(n)[50]
                for n in (2, 3, 5, 7, 11, 13, 15, 17, 19, 23)}
        assert band[2] == band[3] == 5
        assert band[5] == band[7] == band[11] == 6
        assert all(band[n] == 7 for n in (13, 15, 17, 19, 23))

    def test_a_radicand_below_two_is_refused(self):
        with pytest.raises(ValueError):
            cat.heron_step_cost(1)

    def test_the_sparse_series_is_the_cheapest_of_the_three(self):
        costs = cat.generator_step_costs()
        assert costs["liouville"][50] < costs["machin"][50]
        assert costs["machin"][50] < costs["exponential"][50]

    def test_the_exponential_tail_bound_gives_seventeen_terms(self):
        assert cat.exponential_term_cost()[50] == 17


# ===========================================================================
# 3.  THE LEDGER
# ===========================================================================

class TestLedger:

    def test_every_section_contributes_claims(self):
        for section in (cat.section_1_claims, cat.section_2_claims,
                        cat.section_3_claims, cat.section_4_claims,
                        cat.section_5_claims, cat.section_6_claims):
            assert len(section()) > 0

    def test_every_claim_carries_a_known_verdict_and_a_figure(self, report):
        for entry in report["claims"]:
            assert entry["verdict"] in cat.VERDICTS
            assert entry["section"]
            assert entry["claim"]
            assert entry["figure"]

    def test_a_refuted_claim_says_what_holds_instead(self, report):
        refuted = [c for c in report["claims"]
                   if c["verdict"] in (cat.REFUTED, cat.NOT_REPRODUCED)]
        assert refuted
        for entry in refuted:
            assert entry.get("instead")

    def test_the_tally_adds_up(self, report):
        assert sum(report["tally"].values()) == report["claim_count"]
        assert report["claim_count"] == len(report["claims"])

    def test_the_ledger_covers_all_six_sections(self, report):
        leading = {label.split(".")[0] for label in report["section_labels"]}
        assert leading == {"1", "2", "3", "4", "5", "6"}
        assert report["sections"] == 6

    def test_the_ledger_finds_both_agreement_and_disagreement(self, report):
        """A ledger that only ever confirms is not testing anything."""
        assert report["confirmed"] > 0
        assert report["refuted"] > 0

    def test_the_open_gaps_are_recorded_rather_than_passed(self, report):
        gaps = [c for c in report["claims"]
                if c["verdict"] == cat.NOT_IMPLEMENTED]
        assert gaps
        for entry in gaps:
            assert entry["figure"]

    def test_the_reading_states_the_tally(self, report):
        reading = report["reading"]
        assert str(report["claim_count"]) in reading
        assert "confirmed" in reading and "refuted" in reading

    def test_the_report_is_recomputed_rather_than_stored(self, report):
        """The report is derived on demand, not read back from a file.

        ``cat.catalog_report`` is memoised -- the first call in a process computes it and
        later calls return that object -- so asking twice would prove nothing.
        The uncached derivation underneath is reached through ``__wrapped__``:
        it builds a fresh object, and that object must equal the memoised one.
        The memo is therefore an optimisation and never a claim.
        """
        again = cat.catalog_report.__wrapped__()
        assert again == report
        assert again is not report


# ===========================================================================
# 4.  THE UNIVERSALITY CLAIM OF SECTION 6.2
# ===========================================================================

class TestUniversalityClaimIsSplit:
    """Section 6.2 names three domains, and each is now measurable.

    Chemistry, music and — since the economic register was added — markets are
    all registers, so the sentence can be measured for each of them
    separately.  Carrying one verdict for all three would hide which domain
    earned what, so the sentence is still carried as two claims, the musical
    half reading its verdict off the harmony study and the economic half off
    the economics study.
    """

    def _section_62(self, report):
        return [c for c in report["claims"] if c["section"] == "6.2"]

    def test_the_sentence_is_carried_as_two_claims(self, report):
        entries = self._section_62(report)
        assert len(entries) == 2
        assert "musical harmony" in str(entries[0]["claim"])
        assert "market price discovery" in str(entries[1]["claim"])

    def test_the_musical_half_is_decided_by_the_harmony_study(self, report):
        from glm_universal.reasoning import harmony as hy
        music = self._section_62(report)[0]
        verdict = hy.harmony_report()["verdict"]
        assert str(music["verdict"]) == str(verdict["verdict"])
        assert music["verdict"] in cat.VERDICTS
        assert music["verdict"] != cat.NOT_IMPLEMENTED

    def test_the_musical_half_states_the_statistic_that_decided_it(self,
                                                                  report):
        from glm_universal.reasoning import harmony as hy
        music = self._section_62(report)[0]
        separation = hy.harmony_report()["lattice"]
        figure = str(music["figure"])
        assert str(separation["best_scale"]) in figure
        assert str(separation["best_distinct"]) in figure
        assert "harmony" in figure

    def test_the_economic_half_is_decided_by_the_economics_study(self, report):
        """The economic half is no longer an open gap.

        It was carried as ``not implemented`` while there was no register of
        prices to run the claim against.  There is one now, so the claim reads
        its verdict off :mod:`glm_universal.reasoning.economics` at call time,
        exactly as the musical half reads its own off the harmony study.
        """
        from glm_universal.reasoning import economics as ec
        markets = self._section_62(report)[1]
        verdict = ec.economics_report()["verdict"]
        assert str(markets["verdict"]) == str(verdict["verdict"])
        assert markets["verdict"] in cat.VERDICTS
        assert markets["verdict"] != cat.NOT_IMPLEMENTED
        assert "economic register" in str(markets["figure"])

    def test_the_economic_half_states_the_statistic_that_decided_it(self,
                                                                    report):
        from glm_universal.reasoning import economics as ec
        markets = self._section_62(report)[1]
        report_ = ec.economics_report()
        figure = str(markets["figure"])
        assert str(report_["lattice"]["best_scale"]) in figure
        assert str(report_["lattice"]["record_count"]) in figure
        assert "economics" in figure


# ===========================================================================
# 5.  THE RUNTIME WIRING
# ===========================================================================

class TestRuntimeWiring:

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "catalog" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        solution = sess.ask("report catalog")
        assert solution.kind == "report"
        assert "confirmed" in solution.answer
        assert "refuted" in solution.answer
        assert len(solution.steps) == 4

    @pytest.mark.parametrize("surface", ["report catalogue",
                                         "report study findings",
                                         "report external studies"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    @pytest.mark.exhaustive
    def test_the_generated_script_reproduces_column_two(self, sess):
        """Column 3 recomputes the whole ledger in a fresh interpreter."""
        solution = sess.ask("report catalog")
        trace = tct.verify_trace(tct.build_trace(solution))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self, sess):
        import json
        json.dumps(sess.ask("report catalog").payload)
