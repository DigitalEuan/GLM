"""Tests for ``reasoning/review_sweep`` -- the register of stalled results.

``studies/REVIEW_SWEEP_STUDY.md`` implements directive D13's second practice
clause: rank candidates for a re-reading by whether there is an identifiable
discarded quantity at the coarse reading, not by how disappointing the original
result was.  These tests hold the parts that have to be *right* rather than
merely reported:

* the **order is computed from the rule**, not written by hand -- an entry
  claiming a discarded quantity it cannot point at ranks below one that
  honestly names nothing, which is the failure mode the clause exists to stop;
* **every entry cites a study that exists** and is not a stub, and every
  claimed discarded quantity resolves to an attribute that reports it;
* **a re-reading is licensed only for the `recoverable` class**, and the four
  `no-discard` entries each name what is needed instead;
* the **register is not a copy of the open list** -- it says which of the open
  list a finer reading could possibly help, and the sharpest open question is
  deliberately *not* at the top;
* the **exactness** of the module, by the static instrument of directive D7.

Everything is recomputed: the module reads the tree and counts, so no cache is
involved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import pipeline as ppl
from glm_universal.reasoning import review_sweep as rvs
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return rvs.review_sweep_report()


# ---------------------------------------------------------------------------
#  1.  The shape of an entry
# ---------------------------------------------------------------------------

def test_every_entry_is_complete_and_has_a_declared_class():
    keys = [entry.key for entry in rvs.REGISTER]
    assert len(keys) == len(set(keys))
    for entry in rvs.REGISTER:
        assert entry.verdict in rvs.CLASSES, entry.key
        assert entry.stall and entry.reading and entry.discarded
        assert entry.next_step
        assert entry.document.endswith(".md")


def test_an_unknown_entry_is_refused_rather_than_guessed():
    with pytest.raises(KeyError):
        rvs.entry_by_key("no such entry")


def test_every_entry_cites_a_study_that_exists_and_is_not_a_stub(report):
    for row in report["entries"]:
        assert row["document_found"] is True, row["key"]
        assert row["document_is_a_study"] is True, row["key"]
        assert row["document_bytes"] >= rvs.STUB_BYTES


def test_every_claimed_discarded_quantity_points_at_where_it_is_reported(
        report):
    for row in report["entries"]:
        if row["claims_a_discarded_quantity"]:
            assert row["module"], row["key"]
            assert row["attribute"], row["key"]
            assert row["attribute_resolves"] is True, row["key"]
        assert row["supported"] is True, row["key"]


def test_the_register_reports_no_defect(report):
    assert report["defects"] == ()
    assert report["holds"] is True


# ---------------------------------------------------------------------------
#  2.  The ranking is the rule, not a hand-written order
# ---------------------------------------------------------------------------

def test_the_classes_rank_in_the_declared_order():
    assert rvs.CLASSES == ("recoverable", "recovered", "needs-a-theorem",
                           "no-discard")


def test_the_order_is_non_decreasing_in_the_class_rank(report):
    seen = [rvs.CLASSES.index(str(row["verdict"]))
            for row in report["entries"]]
    assert seen == sorted(seen)


def test_an_unsupported_claim_ranks_below_an_honest_no_discard():
    """The rule with teeth: a claim that cannot be pointed at is demoted."""
    bogus = rvs.Entry(
        key="test-unsupported",
        stall="a stall invented by this test",
        document="REVIEW_SWEEP_STUDY.md",
        reading="a coarse reading",
        verdict="recoverable",
        discarded="a quantity this entry cannot point at",
        module="glm_universal.reasoning.review_sweep",
        attribute="no_such_attribute")
    row = rvs.entry_report(bogus)
    assert row["attribute_resolves"] is False
    assert row["supported"] is False
    honest = rvs.entry_report(rvs.entry_by_key("planner-utility"))
    assert rvs._rank_key(row) > rvs._rank_key(honest)


def test_the_ranking_is_stable_across_calls(report):
    again = rvs.review_sweep_report()
    assert [row["key"] for row in again["entries"]] == \
        [row["key"] for row in report["entries"]]


# ---------------------------------------------------------------------------
#  3.  What the register licenses
# ---------------------------------------------------------------------------

def test_a_re_reading_is_licensed_only_for_the_recoverable_class(report):
    licensed = set(report["recoverable"])
    assert licensed == {row["key"] for row in report["entries"]
                        if row["verdict"] == "recoverable"}
    assert report["licensed_for_re_reading"] == len(licensed)
    assert licensed


def test_the_sharpest_open_question_is_not_the_one_that_is_licensed(report):
    """Sorted by disappointment this would be first; by the rule it is not."""
    separation = rvs.entry_by_key("deep-hole-separation")
    assert separation.verdict == "no-discard"
    assert separation.key not in report["recoverable"]
    assert report["entries"][0]["key"] != separation.key


def test_every_no_discard_entry_names_what_is_needed_instead(report):
    for row in report["entries"]:
        if row["verdict"] == "no-discard":
            assert row["next_step"]
            assert "re-reading" in row["next_step"] \
                or "new" in row["next_step"] or "proof" in row["next_step"] \
                or "pre-registration" in row["next_step"]


def test_the_recovered_entries_are_kept_with_the_reading_that_resolved_them(
        report):
    recovered = report["by_class"]["recovered"]
    assert set(recovered) == {"rational-conflation", "deep-hole-per-type"}
    for key in recovered:
        entry = rvs.entry_by_key(key)
        assert "Recovered by" in entry.discarded or "recovered" in \
            entry.discarded.lower()


def test_the_classes_partition_the_register(report):
    total = sum(len(report["by_class"][name]) for name in report["classes"])
    assert total == report["count"] == len(rvs.REGISTER)


def test_the_register_states_the_rule_and_its_limits(report):
    assert "identifiable at the coarse reading" in str(report["rule"])
    assert "judgement" in str(report["limits"])


# ---------------------------------------------------------------------------
#  4.  The runtime, and the record
# ---------------------------------------------------------------------------

def test_the_subject_answers_with_the_recomputed_register(report):
    session = GeometricSession()
    solution = session.ask("report review sweep")
    assert solution.kind == "report"
    assert solution.expected["entries"] == str(report["count"])
    assert solution.expected["holds"] == "True"
    assert solution.expected["defects"] == "0"
    assert solution.expected["order"] == ",".join(
        str(row["key"]) for row in report["entries"])


def test_column_three_renders_for_the_subject():
    session = GeometricSession()
    script = tct.render_script(session.ask("report review sweep"))
    assert "review_sweep" in script


def test_the_pipeline_row_names_the_study_and_the_subject():
    row = next(r for r in ppl.REGISTRY if r.key == "review-sweep")
    assert row.document == "REVIEW_SWEEP_STUDY.md"
    assert row.subject == "review sweep"
    assert row.lean_expected is False
    assert row.lean == ()


def test_the_module_holds_no_float():
    assert ex.module_float_sites(Path(rvs.__file__)) == {}
