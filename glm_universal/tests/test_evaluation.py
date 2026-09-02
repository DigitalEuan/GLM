"""Tests for ``glm_universal.evaluation`` -- the end-to-end CLI assessment.

The evaluation drives ``GLM.py`` in a fresh interpreter over a fixed question
set and scores what comes back.  These tests pin three things: that the
question set really does cover every query kind and every report subject the
runtime advertises (so the assessment cannot quietly fall behind the runtime),
that the scoring is asymmetric in the way it claims -- a confident wrong
answer is worse than a refusal -- and that the harness genuinely runs the CLI,
by running a few cases end to end.
"""

from __future__ import annotations

import pytest

from glm_universal.evaluation import cases as EC
from glm_universal.evaluation import harness as EH
from glm_universal.runtime.parser import KINDS
from glm_universal.runtime.session import REPORT_SUBJECTS


# ===========================================================================
# 1.  THE QUESTION SET
# ===========================================================================

class TestQuestionSet:

    def test_the_ids_are_unique(self):
        ids = [case.id for case in EC.CASES]
        assert len(ids) == len(set(ids))

    def test_every_query_kind_is_exercised(self):
        covered = set(EC.KINDS_COVERED)
        assert covered == set(KINDS), set(KINDS) ^ covered

    def test_every_report_subject_is_exercised(self):
        asked = set(EC.SUBJECTS_COVERED)
        assert set(REPORT_SUBJECTS) <= asked, set(REPORT_SUBJECTS) - asked

    def test_expected_answers_carry_a_ground_truth(self):
        for case in EC.CASES:
            if case.expect == "answer":
                assert case.contains, case.id

    def test_expected_refusals_are_classified(self):
        for case in EC.CASES:
            if case.expect == "refusal":
                assert case.classification in ("boundary", "gap"), case.id

    def test_the_boundary_refusals_are_represented(self):
        """A refusal at a stated boundary is a result, and must be tested.

        The second kind -- ``gap``, a question the machine could answer but
        does not -- is *not* required to be present: the set held exactly one
        such case (``coherence PbCl2``) and closing it in v1.4.0 emptied that
        class.  What is required is that every refusal is classified, which
        :meth:`test_expected_refusals_are_classified` checks, and that the
        boundary class is never empty.
        """
        kinds = {case.classification for case in EC.CASES
                 if case.expect == "refusal"}
        assert "boundary" in kinds
        assert kinds <= {"boundary", "gap"}

    def test_the_carrier_solvers_take_an_unregistered_formula(self):
        """The closed gap, pinned: the species that used to be refused."""
        by_id = {case.id: case for case in EC.CASES}
        for name in ("coherence", "spatial", "angle", "cluster"):
            case = by_id[f"{name}-unregistered-molecule"]
            assert case.expect == "answer", case.id
            assert "PbCl2" in case.question

    def test_a_malformed_case_is_rejected(self):
        with pytest.raises(ValueError):
            EC.EvalCase("x", "verify", "verify a = b", "answer")
        with pytest.raises(ValueError):
            EC.EvalCase("x", "verify", "verify a = b", "refusal")
        with pytest.raises(ValueError):
            EC.EvalCase("x", "verify", "verify a = b", "maybe")


# ===========================================================================
# 2.  THE SCORING
# ===========================================================================

class TestScoring:

    def test_a_refusal_is_recognised_by_its_exit_line(self):
        answer, refused = EH._answer_line(
            "QUERY   x\nUNSOLVED        resolve: 'x' names no carrier")
        assert refused
        assert "names no carrier" in answer

    def test_a_refusal_is_recognised_inside_an_answer(self):
        answer, refused = EH._answer_line(
            "QUERY   x\nANSWER  'justice' denotes nothing determinate: ...")
        assert refused
        assert answer.startswith("'justice'")

    def test_an_answer_is_not_a_refusal(self):
        _, refused = EH._answer_line("ANSWER  force = mass * acceleration "
                                     "holds under scalar semantics")
        assert not refused

    def test_a_missing_ground_truth_is_reported(self):
        case = EC.EvalCase("x", "analogy", "a : b :: c : ?", "answer",
                           contains=("Mg",))
        assert EH._missing(case, "a : b :: c : Fe") == ["Mg"]
        assert EH._missing(case, "a : b :: c : Mg") == []

    def test_a_forbidden_phrase_is_reported(self):
        case = EC.EvalCase("x", "verify", "verify a = b", "answer",
                           contains=("holds",), forbids=("does not hold",))
        assert EH._missing(case, "a = b does not hold") != []

    def test_being_confidently_wrong_costs_more_than_refusing(self):
        assert EH.WEIGHTS["wrong_answer"] < EH.WEIGHTS["unexpected_refusal"]
        assert EH.WEIGHTS["error"] < EH.WEIGHTS["unexpected_refusal"]
        assert EH.WEIGHTS["unexpected_refusal"] < EH.WEIGHTS["correct"]
        assert EH.WEIGHTS["refused_as_expected"] == EH.WEIGHTS["correct"]


# ===========================================================================
# 3.  THE HARNESS, RUNNING THE REAL CLI
# ===========================================================================

class TestHarnessEndToEnd:
    """A few cases run for real, one fresh interpreter each."""

    def test_the_cli_is_where_the_harness_looks_for_it(self):
        assert EH.CLI_PATH.is_file()

    def test_an_answered_case_scores_correct(self):
        case = next(c for c in EC.CASES if c.id == "verify-newton")
        result = EH.run_case(case)
        assert result.outcome == "correct", result.stopped_at
        assert result.returncode == 0
        assert result.passed

    def test_a_refused_case_scores_as_expected(self):
        case = next(c for c in EC.CASES if c.id == "describe-unknown-word")
        result = EH.run_case(case)
        assert result.outcome == "refused_as_expected", result.stopped_at
        assert result.refused
        assert result.passed

    def test_division_by_an_exact_zero_refuses_rather_than_crashing(self):
        """The gap closed in this round: it used to raise a traceback."""
        case = next(c for c in EC.CASES if c.id == "real-divide-by-zero")
        result = EH.run_case(case)
        assert result.outcome == "refused_as_expected", result.stopped_at
        assert "exact zero" in result.answer

    def test_a_wrong_answer_is_reported_with_where_it_stops(self):
        """A ground truth the machine does not meet must be caught."""
        case = EC.EvalCase("check-detects-wrong", "verify",
                           "verify force = mass * acceleration", "answer",
                           contains=("does not hold",))
        result = EH.run_case(case)
        assert result.outcome == "wrong_answer"
        assert "does not hold" in result.stopped_at

    def test_a_small_report_runs_and_summarises(self):
        subset = tuple(c for c in EC.CASES
                       if c.id in ("verify-newton", "analogy-alkali",
                                   "meaning-open-vocabulary"))
        report = EH.evaluation_report(subset, jobs=3)
        assert report["cases"] == 3
        assert report["passed"] == 3
        assert set(report["per_kind"]) == {"verify", "analogy", "meaning"}
        text = EH.format_report(report)
        assert "PER QUERY KIND" in text
        assert "no failures" in text
