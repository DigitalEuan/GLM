"""Tests for the hand-translation experiment against blocker 1.

What is pinned here is the *declaration*: one translation per probe question,
in the same order, with a locus wherever there is a query, a witness wherever
one is claimed, and no translation that smuggles the expected fragment into
the query it asks.  The outcome is not pinned -- a split whose numbers were
asserted in a test would stop being a measurement -- but its structure is:
the three classes partition the twenty questions, each class follows from the
two facts that decide it, and a question counted `surface` really does have a
witness that holds its fragment.

Directive D7 -- no float anywhere -- is checked statically.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import blockers as BL
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import probe_oracle as PO


def _words(text: str) -> set:
    """The whole words of a phrase, lower-cased, keeping `speed_of_light`."""
    return set(re.findall(r"[a-z0-9_.]+", text.lower()))


@pytest.fixture(scope="module")
def report():
    return PO.oracle_report()


class TestDeclaration:

    def test_one_translation_per_question_in_the_same_order(self):
        assert len(PO.TRANSLATIONS) == len(BL.PROBE)
        assert ([t.key for t in PO.TRANSLATIONS]
                == [q.key for q in BL.PROBE])

    def test_a_query_comes_with_a_locus_and_a_witness_with_a_kind(self):
        for translation in PO.TRANSLATIONS:
            if translation.query is None:
                assert translation.locus is None
            else:
                assert translation.locus
            if translation.witness is None:
                assert translation.witness_kind == "none"
            else:
                assert translation.witness in PO.WITNESSES
                assert translation.witness_kind in PO.WITNESS_KINDS
                assert translation.witness_kind != "none"

    def test_no_translation_smuggles_the_answer_into_the_question(self):
        """A query containing the fragment it is scored on proves nothing.

        Unless the asker supplied it: the subject of the question is in the
        English too, and naming it in the translation is what a translation
        is.  So the rule is that a fragment may appear in the query only
        where it already appears in the question being translated, and it is
        read as a whole word so that `M` is not found inside `meaning`.
        """
        questions = {question.key: question for question in BL.PROBE}
        for translation in PO.TRANSLATIONS:
            if translation.query is None:
                continue
            question = questions[translation.key]
            fragment = question.expect.lower()
            if fragment in _words(question.question):
                continue
            assert fragment not in _words(translation.query), translation.key

    def test_every_translation_says_why(self):
        for translation in PO.TRANSLATIONS:
            assert translation.note

    def test_every_declared_witness_is_cited(self):
        cited = {t.witness for t in PO.TRANSLATIONS if t.witness}
        assert cited == set(PO.WITNESSES)


class TestClassification:

    def test_the_class_follows_from_the_two_facts(self):
        assert PO.class_of(True, True) == "parsed"
        assert PO.class_of(True, False) == "parsed"
        assert PO.class_of(False, True) == "surface"
        assert PO.class_of(False, False) == "absent"

    def test_the_three_classes_partition_the_questions(self, report):
        counts = report["counts"]
        assert set(counts) == set(PO.CLASSES)
        assert sum(counts.values()) == report["questions"] == len(BL.PROBE)

    def test_each_row_carries_the_class_its_facts_give_it(self, report):
        for row in report["rows"]:
            assert row["class"] == PO.class_of(bool(row["answered"]),
                                               bool(row["witness_holds"]))

    def test_a_question_with_no_query_is_never_parsed(self, report):
        for row in report["rows"]:
            if row["query"] is None:
                assert row["class"] != "parsed"
                assert row["asked"]["kind"] == "not-expressible"

    def test_the_domains_add_up(self, report):
        for name in PO.CLASSES:
            assert (sum(bucket[name]
                        for bucket in report["by_domain"].values())
                    == report["counts"][name])


class TestWitnesses:

    def test_a_surface_question_really_is_held(self, report):
        expectations = {question.key: question.expect for question in BL.PROBE}
        for row in report["rows"]:
            if row["class"] != "surface":
                continue
            fragment = expectations[str(row["key"])].lower()
            assert fragment in str(row["witness_text"]).lower(), row["key"]

    def test_an_absent_question_is_held_by_nothing(self, report):
        for row in report["rows"]:
            if row["class"] == "absent":
                assert not row["witness_holds"]

    def test_every_witness_returns_something(self):
        for name in PO.WITNESSES:
            assert PO.witness_value(name)

    def test_the_decimal_rendering_is_exact(self):
        assert PO._decimal(Fraction(12011, 1000), 3) == "12.011"
        assert PO._decimal(Fraction(18015, 1000), 3) == "18.015"
        assert PO._decimal(Fraction(1, 2), 0) == "0"
        assert PO._decimal(Fraction(-3, 4), 2) == "-0.75"


class TestAgainstTheEnglishProbe:

    def test_the_translation_never_loses_a_question(self, report):
        """Every question the English gets right, a translation gets right."""
        for row in report["rows"]:
            if report["english"][str(row["key"])] == "correct":
                assert row["class"] == "parsed", row["key"]

    def test_the_parser_is_worth_what_moved(self, report):
        moved = report["moved_by_translation"]
        assert report["parser_worth"] == len(moved)
        assert (report["counts"]["parsed"]
                == report["english_correct"] + len(moved))

    def test_the_surface_figure_is_the_surface_class(self, report):
        assert report["surface_worth"] == report["counts"]["surface"]
        kinds = report["witness_kinds"]
        assert sum(kinds.values()) == report["counts"]["surface"]
        assert kinds["none"] == 0


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(PO.__file__)) == {}
