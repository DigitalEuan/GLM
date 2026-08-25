"""Tests for `glm_universal.benchmarks` -- the scored task suites.

The benchmarks are themselves a claim, so these tests check the claim's
discipline and not only its arithmetic:

* the evidence tier is declared, well formed, and cannot be forged -- a
  sampled suite without a seed is refused at construction;
* the score is exact rational arithmetic, never a float;
* every suite reports its failures, and the suites with known failure modes
  report those too -- a suite that reported only its wins would pass a naive
  test and is caught here;
* the results written to ``results/`` agree with the run that produced them,
  keep every failing outcome, and are byte-stable across two runs;
* the runtime query and its column-3 script agree with the package API.
"""

from __future__ import annotations

import json
import os
from fractions import Fraction

import pytest

from glm_universal import benchmarks as bm
from glm_universal.benchmarks.harness import EvidenceTier
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return bm.benchmark_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


EXPECTED_SUITES = ("analogy_chemistry", "analogy_physics", "analogy_semantic",
                   "golay_correction", "physics_equations")

_SCORES = {}


def scored(name):
    """Run a suite once per test session; the suites are deterministic."""
    if name not in _SCORES:
        _SCORES[name] = bm.run_suite(name)
    return _SCORES[name]


# ===========================================================================
# 1.  THE REGISTRY
# ===========================================================================

class TestRegistry:

    def test_every_suite_is_registered(self):
        assert bm.suite_names() == EXPECTED_SUITES

    def test_an_unknown_suite_is_refused_by_name(self):
        with pytest.raises(KeyError) as excinfo:
            bm.get_suite("no_such_suite")
        assert "no_such_suite" in str(excinfo.value)

    def test_a_duplicate_registration_is_refused(self):
        existing = bm.get_suite("golay_correction")
        with pytest.raises(ValueError):
            bm.register(existing)

    def test_each_suite_declares_its_question(self):
        for name in bm.suite_names():
            assert bm.get_suite(name).question.endswith("?")


# ===========================================================================
# 2.  THE CONTRACT IS DECLARED BEFORE THE RUN
# ===========================================================================

class TestEvidenceTier:

    def test_a_sampled_tier_must_carry_a_seed(self):
        with pytest.raises(ValueError) as excinfo:
            EvidenceTier(tier="sampled", population="p", ground_truth="g",
                         pass_criterion="c", baseline="b", null_result="n")
        assert "seed" in str(excinfo.value)

    def test_a_non_sampled_tier_may_not_carry_a_seed(self):
        with pytest.raises(ValueError):
            EvidenceTier(tier="exhaustive", population="p", ground_truth="g",
                         pass_criterion="c", baseline="b", null_result="n",
                         seed=1)

    def test_an_unknown_tier_is_refused(self):
        with pytest.raises(ValueError):
            EvidenceTier(tier="vibes", population="p", ground_truth="g",
                         pass_criterion="c", baseline="b", null_result="n")

    @pytest.mark.parametrize("name", EXPECTED_SUITES)
    def test_every_field_of_every_tier_is_filled_in(self, name):
        tier = bm.get_suite(name).tier
        for field in ("tier", "population", "ground_truth", "pass_criterion",
                      "baseline", "null_result"):
            assert getattr(tier, field), f"{name}.{field} is empty"

    @pytest.mark.parametrize("name", EXPECTED_SUITES)
    def test_no_suite_samples_without_recording_a_seed(self, name):
        tier = bm.get_suite(name).tier
        assert tier.tier != "sampled" or tier.seed is not None

    def test_the_score_carries_the_tier_it_was_declared_under(self):
        suite = bm.get_suite("physics_equations")
        assert bm.run_suite("physics_equations").tier == suite.tier


# ===========================================================================
# 3.  THE ARITHMETIC IS EXACT
# ===========================================================================

class TestExactArithmetic:

    @pytest.mark.parametrize("name", EXPECTED_SUITES)
    def test_scores_are_fractions_not_floats(self, name):
        score = scored(name)
        assert isinstance(score.score, Fraction)
        assert isinstance(score.baseline_score, Fraction)

    def test_no_float_appears_anywhere_in_the_report(self, report):
        blob = json.dumps(report, sort_keys=True)
        parsed = json.loads(blob)

        def walk(node):
            if isinstance(node, float):
                raise AssertionError(f"a float reached the report: {node}")
            if isinstance(node, dict):
                for value in node.values():
                    walk(value)
            if isinstance(node, list):
                for value in node:
                    walk(value)

        walk(parsed)

    def test_a_score_is_passes_over_total(self, report):
        for suite in report["suites"]:
            assert (Fraction(suite["score"])
                    == Fraction(suite["passed"], suite["total"]))


# ===========================================================================
# 4.  THE SCORES THEMSELVES
# ===========================================================================

class TestScores:

    def test_the_golay_suite_is_exhaustive_below_the_packing_radius(self):
        score = scored("golay_correction")
        assert score.total == 1 + 24 + 276 + 2024      # = 2325
        assert score.passed == score.total
        assert score.score == 1

    def test_the_golay_baseline_is_the_uncorrected_word(self):
        score = scored("golay_correction")
        assert score.baseline_score == Fraction(1, 2325)
        assert score.beats_baseline

    def test_the_verifier_refuses_every_false_equation(self):
        score = scored("physics_equations")
        assert (score.measurements["false_refused"]
                == score.measurements["false_cases"])

    def test_the_verifier_beats_accepting_everything(self):
        score = scored("physics_equations")
        assert score.baseline_score == Fraction(20, 30)
        assert score.score > score.baseline_score

    @pytest.mark.parametrize("name", EXPECTED_SUITES)
    def test_every_suite_beats_its_declared_baseline(self, name):
        score = scored(name)
        assert score.verdict == "pass", (
            f"{name} scored {score.score} against {score.baseline_score}")

    def test_the_analogy_baseline_is_below_the_analogy_score(self):
        for name in ("analogy_chemistry", "analogy_semantic",
                     "analogy_physics"):
            score = scored(name)
            assert score.baseline_score < score.score

    def test_a_suite_with_no_tasks_would_be_refused(self):
        """An empty suite is a broken suite, not a perfect one."""
        tier = EvidenceTier(tier="curated", population="none",
                            ground_truth="none", pass_criterion="none",
                            baseline="none", null_result="none")
        empty = bm.Suite(
            name="empty_suite", question="Does an empty suite score?",
            tier=tier,
            runner=lambda: bm.SuiteScore(
                name="empty_suite", question="Does an empty suite score?",
                tier=tier, outcomes=(), baseline_score=Fraction(0)))
        bm.register(empty)
        try:
            with pytest.raises(ValueError) as excinfo:
                bm.run_suite("empty_suite")
            assert "empty suite" in str(excinfo.value)
        finally:
            bm.harness._REGISTRY.pop("empty_suite")


# ===========================================================================
# 5.  NEGATIVE AND NULL RESULTS ARE REPORTED, NOT HIDDEN
# ===========================================================================

class TestFindingsAreReported:

    @pytest.mark.parametrize("name", EXPECTED_SUITES)
    def test_every_suite_reports_at_least_one_finding(self, name):
        assert scored(name).findings

    def test_every_failing_task_appears_in_a_finding_or_an_outcome(self):
        for name in EXPECTED_SUITES:
            score = scored(name)
            for failure in score.failures:
                assert failure in score.outcomes

    def test_the_golay_suite_reports_the_weight_four_ambiguity(self):
        score = scored("golay_correction")
        keys = {f.key for f in score.findings}
        assert "weight_4_is_ambiguous" in keys
        assert score.measurements["ambiguous_at_weight_4"] == "10626/10626"

    def test_the_golay_suite_reports_weight_five_miscorrection(self):
        score = scored("golay_correction")
        keys = {f.key for f in score.findings}
        assert "weight_5_is_confidently_wrong" in keys
        assert score.measurements["miscorrected_at_weight_5"] == "42504/42504"

    def test_the_equation_suite_reports_the_ext10_angular_boundary(self):
        score = scored("physics_equations")
        keys = {f.key for f in score.findings}
        assert "ext10_refuses_angular_momentum" in keys

    def test_the_equation_suite_reports_the_semantics_divergence(self):
        score = scored("physics_equations")
        finding = next(f for f in score.findings
                       if f.key == "scalar_vs_full_semantics")
        assert int(score.measurements["scalar_full_divergences"]) > 0
        assert finding.detail != "none"

    def test_the_physics_analogy_suite_reports_the_reciprocal_case(self):
        """The reciprocal case is reported either way round.

        Before the named-relation layer, `length : wavenumber :: time : ?`
        was the suite's structural failure and the finding said so.  The
        layer answers it, so the finding flips rather than vanishing: a
        case that used to be a documented limit must not be able to leave
        the report silently.
        """
        score = scored("analogy_physics")
        keys = {f.key for f in score.findings}
        reciprocal = next(o for o in score.outcomes
                          if o.task == "length : wavenumber :: time : ?")
        wanted = ("reciprocal_relations_are_in_model" if reciprocal.passed
                  else "reciprocal_relations_are_out_of_model")
        assert wanted in keys

    def test_the_named_analogy_suites_list_their_misses(self):
        for name in ("analogy_chemistry", "analogy_semantic"):
            score = scored(name)
            finding = next(f for f in score.findings if f.key == "misses")
            assert len(score.failures) == int(finding.statement.split()[0])

    def test_a_suite_scoring_its_baseline_is_named_a_null_result(self):
        tier = bm.get_suite("physics_equations").tier
        score = bm.SuiteScore(
            name="x", question="Is it?", tier=tier,
            outcomes=(bm.TaskOutcome("t", True, "a", "a"),),
            baseline_score=Fraction(1))
        assert score.verdict == "null"
        assert not score.beats_baseline


# ===========================================================================
# 6.  THE LINKS THE SUITES DEPEND ON ARE REAL
# ===========================================================================

class TestGroundTruthIsExternal:

    def test_every_physics_analogy_target_is_in_the_register(self):
        from glm_universal.benchmarks import suites as sui
        assert sui.cases_with_targets() == sui.PHYSICS_ANALOGIES

    def test_the_true_and_false_equations_are_disjoint(self):
        assert not (set(bm.PHYSICS_EQUATIONS_TRUE)
                    & set(bm.PHYSICS_EQUATIONS_FALSE))

    def test_the_false_equations_really_are_dimensionally_false(self):
        """Checked against the register's exponents, not the verifier."""
        from glm_universal.reasoning import verifier as ve
        for lhs, rhs in bm.PHYSICS_EQUATIONS_FALSE:
            left = ve.parse(lhs)
            right = ve.parse(rhs)
            assert left.exps != right.exps or left.rank != right.rank

    def test_the_chemistry_answers_are_all_element_symbols(self):
        from glm_universal.data_objects import elements as el
        known = {e.symbol for e in el.load_element_register()}
        for _, _, _, expected in bm.CHEMISTRY_ANALOGIES:
            assert expected in known

    def test_the_semantic_answers_are_all_in_the_vocabulary(self):
        from glm_universal.data_objects import semantic_lexicon as sl
        words = {c.subject for c in sl.SEMANTIC_SAMPLE_CONCEPTS}
        for a, b, c, expected in bm.SEMANTIC_ANALOGIES:
            assert {a, b, c, expected} <= words


# ===========================================================================
# 7.  THE RESULTS ON DISK
# ===========================================================================

@pytest.fixture(scope="module")
def written(tmp_path_factory):
    """One write of the whole results tree, shared by the tests below."""
    target = tmp_path_factory.mktemp("results")
    report = bm.write_results(str(target))
    return target, report


class TestWrittenResults:

    def test_writing_produces_one_file_per_suite_plus_claims(self, written):
        tmp_path, report = written
        written_names = sorted(os.listdir(tmp_path))
        assert written_names == sorted([f"{n}.json" for n in EXPECTED_SUITES]
                                       + ["claims.json"])
        assert report["run_id"]

    def test_the_claims_file_records_the_run_id_and_every_claim(self,
                                                                written):
        tmp_path, report = written
        with open(tmp_path / "claims.json", encoding="utf-8") as handle:
            claims = json.load(handle)
        assert claims["run_id"] == report["run_id"]
        assert {c["suite"] for c in claims["claims"]} == set(EXPECTED_SUITES)

    def test_no_headline_number_travels_without_its_verdict(self, written):
        tmp_path, _ = written
        with open(tmp_path / "claims.json", encoding="utf-8") as handle:
            claims = json.load(handle)
        for claim in claims["claims"]:
            assert claim["verdict"] in ("pass", "null", "below baseline")
            assert "baseline" in claim["claim"]

    def test_a_written_suite_keeps_every_failing_outcome(self, written):
        tmp_path, _ = written
        with open(tmp_path / "analogy_chemistry.json",
                  encoding="utf-8") as handle:
            record = json.load(handle)
        failed = [o for o in record["outcomes"] if not o["passed"]]
        assert len(failed) == len(scored("analogy_chemistry").failures)

    def test_a_large_suite_is_sampled_but_says_so(self, written):
        tmp_path, _ = written
        with open(tmp_path / "golay_correction.json",
                  encoding="utf-8") as handle:
            record = json.load(handle)
        assert record["outcomes_total"] == 2325
        assert record["outcomes_written"] < record["outcomes_total"]
        assert "sampled" in record["outcomes_note"]

    def test_two_runs_write_the_same_bytes(self, tmp_path):
        first = tmp_path / "a"
        second = tmp_path / "b"
        bm.write_results(str(first))
        bm.write_results(str(second))
        for name in os.listdir(first):
            with open(first / name, encoding="utf-8") as handle:
                left = handle.read()
            with open(second / name, encoding="utf-8") as handle:
                right = handle.read()
            assert left == right, f"{name} is not reproducible"

    def test_the_committed_results_match_the_current_run(self, report):
        """The checked-in ``results/`` must not drift from the code."""
        path = os.path.join(bm.results_dir(), "claims.json")
        with open(path, encoding="utf-8") as handle:
            committed = json.load(handle)
        assert committed["run_id"] == report["run_id"], (
            "benchmarks/results/ is stale; re-run "
            "`python3 -m glm_universal.benchmarks --write`")


# ===========================================================================
# 8.  THE RUNTIME SURFACE
# ===========================================================================

class TestRuntimeQuery:

    def test_benchmarks_is_a_report_subject(self, sess):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "benchmarks" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        sol = sess.ask("report benchmarks")
        assert sol.ok, sol.error
        assert "suites" in sol.answer

    def test_the_query_agrees_with_the_package(self, sess, report):
        sol = sess.ask("report benchmarks")
        assert sol.expected["run_id"] == report["run_id"]
        assert sol.expected["task_count"] == str(report["task_count"])

    def test_every_suite_is_named_in_the_expected_block(self, sess):
        sol = sess.ask("report benchmarks")
        for name in EXPECTED_SUITES:
            assert f"score_{name}" in sol.expected
            assert f"verdict_{name}" in sol.expected

    def test_the_generated_script_reproduces_column_two(self, sess):
        sol = sess.ask("report benchmarks")
        trace = tct.verify_trace(tct.build_trace(sol))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()

    def test_the_findings_reach_the_answer(self, sess):
        sol = sess.ask("report benchmarks")
        joined = " ".join(step.mathematics for step in sol.steps)
        assert "weight_5_is_confidently_wrong" in joined
