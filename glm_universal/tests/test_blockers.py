"""Tests for the blockers study and its pre-registered language probe.

What is pinned here is the pre-registration itself -- the questions, the
scoring rule and the pass mark are fixed in the module and must not move
quietly -- together with the properties of the measurements: the probe's
tallies add up, the faculty ledger assigns every result to exactly one of
table lookup, geometric addressing and derivation, and the Python addressing
experiment reports its controls beside its result.

The probe's *outcome* is read from the cache rather than asserted: a probe
whose result was pinned in a test would no longer be a measurement.

Directive D7 -- no float anywhere -- is checked statically.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import blockers as BL
from glm_universal.reasoning import exactness as ex


@pytest.fixture(scope="module")
def stored():
    data = BL.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools blockers --write")
    return data


class TestPreRegistration:

    def test_twenty_questions_over_five_domains(self):
        assert len(BL.PROBE) == 20
        domains = {question.domain for question in BL.PROBE}
        assert domains == {"natural language", "mathematics", "physics",
                           "chemistry", "program text"}
        for domain in domains:
            assert sum(1 for q in BL.PROBE if q.domain == domain) == 4

    def test_every_question_has_a_paraphrase_and_an_expectation(self):
        for question in BL.PROBE:
            assert question.question and question.paraphrase
            assert question.question != question.paraphrase
            assert question.expect and question.why

    def test_the_pass_mark_is_declared(self):
        assert BL.PASS_MARK["of"] == len(BL.PROBE)
        assert BL.PASS_MARK["correct_at_least"] == 10
        assert BL.PASS_MARK["wrong_at_most"] == 1

    def test_the_keys_are_unique(self):
        keys = [question.key for question in BL.PROBE]
        assert len(set(keys)) == len(keys)


class TestProbe:

    def test_the_tallies_add_up(self, stored):
        probe = stored["probe"]
        for which in ("canonical", "paraphrased"):
            tally = probe[which]
            assert sum(tally.values()) == probe["questions"]

    def test_the_verdict_follows_the_declared_pass_mark(self, stored):
        probe = stored["probe"]
        expected = (probe["canonical"]["correct"]
                    >= probe["pass_mark"]["correct_at_least"]
                    and probe["canonical"]["wrong"]
                    <= probe["pass_mark"]["wrong_at_most"])
        assert probe["passed"] == expected

    def test_every_asking_is_one_of_three_outcomes(self, stored):
        for row in stored["probe"]["rows"]:
            for which in ("canonical", "paraphrased"):
                assert row[which]["verdict"] in ("correct", "wrong",
                                                 "refused")

    def test_paraphrase_stability_is_reported(self, stored):
        probe = stored["probe"]
        counted = sum(1 for row in probe["rows"]
                      if row["canonical"]["verdict"]
                      == row["paraphrased"]["verdict"])
        assert probe["stable"] == counted


class TestMeasurements:

    def test_the_cache_describes_the_sources(self):
        assert BL.state()["verdict"] == "fresh"

    def test_the_lexicon_coverage_is_a_rate_out_of_the_words_asked(self, stored):
        lexicon = stored["lexicon"]
        assert lexicon["in_lexicon"] + lexicon["out_of_lexicon"] \
            == lexicon["content_words"]

    def test_the_python_experiment_reports_its_controls(self, stored):
        python = stored["python"]
        assert python["usable"]
        assert python["functions"] == BL.PYTHON_SAMPLE
        assert len(BL.PYTHON_FEATURES) == 24
        assert "nearest_shares_module" in python
        assert "digest_control" in python
        assert "chance" in python

    def test_the_ledger_separates_the_three_things(self, stored):
        classes = {row["class"] for row in stored["ledger"]}
        assert classes <= {"table", "addressed", "derived"}
        assert classes == {"table", "addressed", "derived"}
        for row in stored["ledger"]:
            assert row["why"] and row["measured_in"]

    def test_every_blocker_names_a_measurement_and_an_experiment(self, stored):
        figures = stored["figures"]
        for blocker in stored["blockers"]:
            assert blocker["title"] and blocker["statement"]
            assert blocker["experiment"]
            for name in str(blocker["measurement"]).split(" and "):
                assert name.strip() in figures, name


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(BL.__file__)) == {}
