"""Tests for escalating operations that are not retrieval.

``reasoning/operation_escalation`` asks whether the construction ladder helps
anything other than naming a carrier.  What is pinned here is the *protocol*
rather than the outcome: the refusal contract, the controls, the fact that a
wrong answer is counted separately from a refusal, and the fact that a
negative result would be reported rather than hidden.  The measured figures
are read from the cache, which must still describe the sources it was taken
from.

Directive D7 -- no float anywhere -- is checked statically.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import operation_escalation as OE


@pytest.fixture(scope="module")
def stored():
    data = OE.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools operations --write")
    return data


class TestProtocol:

    def test_every_operation_is_declared_with_what_a_rung_adds(self):
        keys = {operation.key for operation in OE.OPERATIONS}
        assert keys == {"register", "dimension", "chemistry", "physics",
                        "harmony", "program"}
        for operation in OE.OPERATIONS:
            assert operation.question
            assert operation.what_a_rung_adds

    def test_the_contract_is_unanimity(self):
        assert OE._answer(("a", "a", "a")) == "a"
        assert OE._answer(("a", "b")) is None
        assert OE._answer(()) is None

    def test_the_operations_are_not_retrieval(self):
        # Retrieval needs a singleton cell; these operations answer from a
        # cell with several members as long as they agree, which is a weaker
        # contract and a different question.
        assert OE._answer(("physics", "physics")) == "physics"

    def test_queries_are_the_declared_perturbations(self):
        operation = [o for o in OE.OPERATIONS if o.key == "harmony"][0]
        entries = operation.carriers()
        queries = OE.operation_queries(operation)
        assert len(queries) == len(entries) * len(OE.LE.PERTURBATIONS)
        index, query, truth = queries[0]
        assert truth == entries[index][1]
        assert all(isinstance(value, Fraction) for value in query)


class TestMeasurement:

    def test_the_cache_describes_the_sources(self):
        assert OE.state()["verdict"] == "fresh"

    def test_every_operation_reports_all_three_outcomes(self, stored):
        for row in list(stored["operations"]) + [stored["equation"]]:
            score = row["escalation"]
            assert (score["correct"] + score["wrong"] + score["refused"]
                    == score["queries"])

    def test_every_operation_beats_its_substrate_removed_control(self, stored):
        for row in list(stored["operations"]) + [stored["equation"]]:
            control = row["control_substrate_removed"]
            assert row["escalation"]["correct"] > control["correct"], \
                row["operation"]

    def test_every_operation_beats_the_label_prior(self, stored):
        for row in list(stored["operations"]) + [stored["equation"]]:
            assert row["gain_over_prior"] > 0, row["operation"]

    def test_the_verdict_matches_the_gain(self, stored):
        for row in list(stored["operations"]) + [stored["equation"]]:
            gain = row["gain_over_best_rung"]
            if gain > 0:
                assert row["verdict"] == "escalation helps"
            elif gain == 0:
                assert "buys nothing" in row["verdict"]
            else:
                assert "worse" in row["verdict"]

    def test_the_unsafe_operations_are_named(self, stored):
        unsafe = set(stored["unsafe"])
        for row in list(stored["operations"]) + [stored["equation"]]:
            assert (row["operation"] in unsafe) == (not row["safe"])
            if not row["safe"]:
                assert row["escalation"]["wrong"] > 0

    def test_the_equation_check_is_a_derivation(self, stored):
        equation = stored["equation"]
        assert equation["true_cases"] > 0 and equation["false_cases"] > 0
        assert equation["cases"] == (equation["true_cases"]
                                     + equation["false_cases"])
        assert "recovered" in equation["derivation"]
        # The prior answers half the cases by construction, so a gain over it
        # is the check doing arithmetic rather than guessing a class.
        assert equation["gain_over_prior"] > 0


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(OE.__file__)) == {}
