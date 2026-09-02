"""Tests for ``reasoning/companion`` and its runtime wiring.

Two companion preprints sit beside the main GLM paper -- *The Generators and
Containers of Real Processes* and *GLM Iteration Study and Lattice Survey* --
and this module reads both as a live claim ledger, finer than the catalogue's
because the preprints state the projection, the indexing and the alphabet
their summary omits.

What the tests below pin is not the verdicts' *values*, which are allowed to
move when the package does; it is that every claim is settled by a
computation, that both studies are covered, that no verdict is invented, that
a disagreement says what holds instead, and that the transcribed tables are
only ever compared against and never answered from.  The transcribed tables
themselves are pinned, because a ledger that quietly edits the claim it is
testing tests nothing.
"""

from __future__ import annotations

import json

import pytest

from glm_universal.reasoning import companion as cpn
from glm_universal.reasoning import containers as con
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return cpn.companion_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE TRANSCRIBED TABLES
# ===========================================================================

class TestTranscribedTables:

    def test_all_three_tables_cover_the_same_eight_constants(self):
        names = {c.name for c in con.CONSTANTS}
        assert set(cpn.CONVERGENCE_TABLE_1) == names
        assert set(cpn.WOBBLE_TABLE_2) == names
        assert set(cpn.HULL_TABLE_3) == names

    def test_the_convergence_table_is_three_thresholds_wide(self):
        for name, row in cpn.CONVERGENCE_TABLE_1.items():
            assert len(row) == len(con.PRECISION_THRESHOLDS), name
            assert all(entry is None or entry >= 0 for entry in row), name

    def test_the_wobble_table_is_five_columns_wide(self):
        for name, row in cpn.WOBBLE_TABLE_2.items():
            assert len(row) == 5, name

    def test_the_hull_table_states_a_status_and_a_norm(self):
        for name, (status, norm) in cpn.HULL_TABLE_3.items():
            assert status in ("inside", "outside"), name
            assert float(norm) >= 0, name

    def test_the_two_studies_are_named_by_their_section_prefix(self):
        assert set(cpn.STUDIES) == {"G", "I"}


# ===========================================================================
# 2.  THE LEDGER
# ===========================================================================

class TestLedger:

    def test_every_group_contributes_claims(self):
        for group in (cpn.convergence_claims, cpn.wobble_claims,
                      cpn.hull_claims, cpn.recurrence_claims,
                      cpn.lattice_claims, cpn.boundary_claims):
            assert len(group()) > 0, group.__name__

    def test_every_claim_carries_a_known_verdict_and_a_figure(self, report):
        for entry in report["claims"]:
            assert entry["verdict"] in cpn.VERDICTS
            assert entry["section"]
            assert entry["claim"]
            assert entry["figure"]

    def test_every_section_label_names_one_of_the_two_studies(self, report):
        for entry in report["claims"]:
            assert str(entry["section"])[0] in cpn.STUDIES

    def test_both_studies_are_tested(self, report):
        assert report["claims_by_study"]["G"] > 0
        assert report["claims_by_study"]["I"] > 0
        assert (sum(report["claims_by_study"].values())
                == report["claim_count"])

    def test_a_disagreement_says_what_holds_instead(self, report):
        disputed = [c for c in report["claims"]
                    if c["verdict"] in (cpn.REFUTED, cpn.NOT_REPRODUCED)]
        assert disputed
        for entry in disputed:
            assert entry.get("instead")

    def test_the_tally_adds_up(self, report):
        assert sum(report["tally"].values()) == report["claim_count"]
        assert report["claim_count"] == len(report["claims"])
        assert report["tally"] == cpn.verdict_tally()

    def test_the_ledger_finds_both_agreement_and_disagreement(self, report):
        """A ledger that only ever confirms is not testing anything."""
        assert report["confirmed"] > 0
        assert report["refuted"] > 0

    def test_the_open_gap_is_recorded_rather_than_passed(self, report):
        gaps = [c for c in report["claims"]
                if c["verdict"] == cpn.NOT_IMPLEMENTED]
        assert gaps
        for entry in gaps:
            assert entry["figure"]

    def test_the_sections_are_sorted_and_unique(self, report):
        sections = report["sections"]
        assert list(sections) == sorted(set(sections))

    def test_the_reading_states_the_tally(self, report):
        reading = report["reading"]
        assert str(report["claim_count"]) in reading
        for word in ("confirmed", "refuted", "not reproduced"):
            assert word in reading

    def test_the_report_is_recomputed_rather_than_stored(self, report):
        """The report is derived on demand, not read back from a file.

        ``cpn.companion_report`` is memoised -- the first call in a process computes it and
        later calls return that object -- so asking twice would prove nothing.
        The uncached derivation underneath is reached through ``__wrapped__``:
        it builds a fresh object, and that object must equal the memoised one.
        The memo is therefore an optimisation and never a claim.
        """
        again = cpn.companion_report.__wrapped__()
        assert again == report
        assert again is not report


# ===========================================================================
# 3.  THE VERDICTS THAT TURN ON A DEFINITION
# ===========================================================================

class TestVerdictsRestOnComputation:

    def test_the_hull_verdicts_are_the_censuss_own(self, report):
        """The ledger does not decide the hull; ``containers`` does.

        Table 3's headline sentence is that Liouville's constant is the only
        one inside.  The verdict on it is read off the certified census, and
        the figure quotes that census constant by constant.
        """
        census = {row["name"]: row["status"] for row in con.hull_table()}
        entries = [c for c in report["claims"]
                   if c["section"] == "G5.1"
                   and "only Liouville" in str(c["claim"])]
        assert len(entries) == 1
        figure = str(entries[0]["figure"])
        for name, status in census.items():
            assert f"{name} {status}" in figure, name
        inside = [name for name, status in census.items()
                  if status == "inside"]
        assert len(inside) > 1
        assert entries[0]["verdict"] == cpn.REFUTED

    def test_the_rigid_baselines_period_is_the_certified_one(self, report):
        period = con.stream_period(con.constant_by_name("1/3"))
        assert period == 3
        entries = [c for c in report["claims"] if c["section"] == "G4.3"]
        assert entries
        assert all(c["verdict"] == cpn.REFUTED for c in entries)
        assert any(str(period) in str(c["figure"]) for c in entries)

    def test_the_lattice_ladder_claim_is_the_substrates_own_enumeration(
            self, report):
        entries = [c for c in report["claims"] if c["section"] == "I6.5"]
        assert entries
        assert any("196560" in str(c["figure"]).replace(",", "")
                   for c in entries)


# ===========================================================================
# 4.  THE RUNTIME WIRING
# ===========================================================================

class TestRuntimeWiring:

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "companion" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        solution = sess.ask("report companion")
        assert solution.kind == "report"
        assert "confirmed" in solution.answer
        assert "refuted" in solution.answer
        assert len(solution.steps) == 4

    @pytest.mark.parametrize("surface", ["report companion studies",
                                         "report preprints",
                                         "report iteration study",
                                         "report lattice survey"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    @pytest.mark.exhaustive
    def test_the_generated_script_reproduces_column_two(self, sess):
        """Column 3 recomputes the whole ledger in a fresh interpreter."""
        solution = sess.ask("report companion")
        trace = tct.verify_trace(tct.build_trace(solution))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self, sess):
        json.dumps(sess.ask("report companion").payload)
