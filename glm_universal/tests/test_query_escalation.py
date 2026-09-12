"""Tests for the escalation loop and ``reasoning/query_escalation``.

``studies/QUERY_ESCALATION_STUDY.md`` wires the deep-hole ladder's discipline
into the ordinary query loop, under directive D13: the ladder is declared per
query kind before it is climbed, every rung run is charged, a refusal carries
the layer it was refused at, and a refusal classified as principled is never
escalated.  These tests pin the parts that have to be *right* rather than
merely reported:

* the **tower is declared and finite** -- three rungs with integer costs, one
  ladder per query kind, and an undeclared kind gets one rung rather than an
  undeclared ladder;
* the **classification precedes the climb** -- every declared marker maps a
  refusal to a non-escalatable tag, and an unmarked refusal is an absence,
  which is the only kind a finer reading can repair;
* the **cost is the sum of the rungs run**, never below the first rung's and
  never above the whole ladder's, which is
  `GLM.EscalationLoop.climbFrom_cost_ge`, `climbFrom_cost_le` and
  `climb_direct_cost`;
* an **answer above the first rung is a statement about the rungs below it**
  (`climb_answers_least`), and a refusal from the loop is a statement about
  every rung of the ladder (`climbFrom_refused_all`);
* the **safety gate over the whole evaluation set** -- no answer moves, none
  becomes more expensive, and no principled refusal is converted;
* the **exactness** of both modules, by the static instrument of directive D7.

The two gates are measured over 147 evaluation cases and are read from the
cache; one test fails if that cache no longer describes the sources it was
taken from (D4).  The cheap structural properties are recomputed here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import pipeline as ppl
from glm_universal.reasoning import query_escalation as qesc
from glm_universal.runtime import escalation_loop as esl
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def stored():
    data = qesc.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools queryesc --write")
    return data


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


# ---------------------------------------------------------------------------
#  1.  The tower, declared
# ---------------------------------------------------------------------------

def test_the_tower_is_three_rungs_with_integer_costs():
    assert [layer.key for layer in esl.LAYERS] == ["L1", "L2", "L3"]
    for layer in esl.LAYERS:
        assert isinstance(layer.cost, int)
        assert layer.cost > 0
        assert layer.title and layer.description
    assert [layer.cost for layer in esl.LAYERS] == [1, 2, 4]


def test_every_declared_ladder_starts_at_the_register_reading():
    for kind, rungs in esl.LADDERS.items():
        assert rungs[0] == "L1", kind
        assert list(rungs) == sorted(rungs), kind
        for key in rungs:
            assert key in esl.LAYER_BY_KEY


def test_an_undeclared_kind_gets_one_rung_and_not_an_undeclared_ladder():
    assert esl.ladder_for("no such kind") == esl.DEFAULT_LADDER == ("L1",)
    assert esl.ladder_for("describe") == ("L1", "L2", "L3")


def test_the_ladder_table_prices_the_top_of_every_ladder():
    for row in esl.ladder_table():
        rungs = row["rungs"]
        assert row["height"] == len(rungs)
        assert row["top_cost"] == sum(esl.LAYER_BY_KEY[k].cost for k in rungs)
    heights = {row["kind"]: row["height"] for row in esl.ladder_table()}
    assert heights["meaning"] == 1        # escalating it would be circular
    assert heights["report"] == 1


def test_the_neighbourhood_radius_is_declared_and_exact():
    assert isinstance(esl.NEIGHBOURHOOD_RADIUS, int)
    assert esl.NEIGHBOURHOOD_RADIUS == 2


# ---------------------------------------------------------------------------
#  2.  Which refusals may be escalated at all
# ---------------------------------------------------------------------------

def test_every_declared_marker_classifies_a_refusal_as_non_escalatable():
    for marker, tag, reason in esl.PRINCIPLED_MARKERS:
        verdict = esl.classify(f"unsolved: something {marker} here")
        assert verdict["escalatable"] is False, marker
        assert verdict["tag"] == tag
        assert verdict["marker"] == marker
        assert reason


def test_the_markers_name_only_the_three_declared_kinds_of_refusal():
    tags = {tag for _marker, tag, _reason in esl.PRINCIPLED_MARKERS}
    assert tags == {"ill-formed", "underdetermined", "ungrounded"}


def test_an_unmarked_refusal_is_read_as_an_absence():
    verdict = esl.classify("unsolved: nothing here matches a marker")
    assert verdict["escalatable"] is True
    assert verdict["tag"] == esl.ESCALATABLE == "absent"
    assert verdict["marker"] is None


def test_classification_is_case_insensitive():
    marker = esl.PRINCIPLED_MARKERS[0][0]
    assert esl.classify(marker.upper())["escalatable"] is False


# ---------------------------------------------------------------------------
#  3.  One climb: cost, layer, and what the verdict says
# ---------------------------------------------------------------------------

def test_a_question_the_register_answers_costs_one_rung(session):
    climb = session.escalate("describe energy")
    assert climb.answered is True
    assert climb.layer == "L1"
    assert climb.escalated is False
    assert climb.cost == esl.LAYERS[0].cost


def test_the_cost_is_the_sum_of_the_rungs_that_ran(session):
    for question in ("describe energy", "describe energie",
                     "describe unobtainium", "nearest to k_B"):
        climb = session.escalate(question)
        assert climb.cost == sum(a.cost for a in climb.attempts)
        assert climb.cost >= esl.LAYER_BY_KEY[climb.ladder[0]].cost


def test_an_answer_above_the_first_rung_means_the_rungs_below_refused(session):
    climb = session.escalate("describe energie")
    assert climb.answered is True
    assert climb.escalated is True
    reached = climb.ladder.index(climb.layer)
    ran = {a.layer: a.outcome for a in climb.attempts}
    for key in climb.ladder[:reached]:
        assert ran.get(key) in ("refused", "skipped"), key
    assert ran[climb.layer] == "answered"
    assert "escalating" in climb.verdict


def test_a_refusal_carries_the_layer_it_was_refused_at(session):
    climb = session.escalate("describe unobtainium")
    assert climb.answered is False
    assert climb.layer is not None
    assert climb.layer in climb.ladder
    assert climb.refusal_tag is not None


def test_a_refusal_at_the_top_says_so_about_every_rung(session):
    climb = session.escalate("describe unobtainium")
    assert climb.layer == climb.ladder[-1]
    assert "every rung" in climb.verdict or "the whole of the declared" \
        in climb.verdict
    for key in climb.ladder:
        outcome = next((a.outcome for a in climb.attempts if a.layer == key),
                       "not run")
        assert outcome in ("refused", "skipped"), key


def test_a_certified_absence_names_the_radius_it_is_certified_within(session):
    climb = session.escalate("describe unobtainium")
    assert climb.certified_absence is True
    assert climb.shortlist == ()
    assert str(esl.NEIGHBOURHOOD_RADIUS) in climb.verdict


def test_a_principled_refusal_stops_the_climb_where_it_was_classified(session):
    climb = session.escalate("Ca : Sc :: Ba : ?")
    assert climb.answered is False
    assert climb.refusal_tag != esl.ESCALATABLE
    assert climb.layer == climb.ladder[0]
    assert climb.cost == esl.LAYER_BY_KEY[climb.ladder[0]].cost
    assert "not escalated" in climb.verdict


def test_the_climb_is_recorded_beside_the_answer_and_not_written_into_it(
        session):
    direct = session.ask("describe energy")
    escalated = esl.ask(session, "describe energy")
    assert escalated.answer == direct.answer
    assert escalated.payload["escalation"]["layer"] == "L1"
    assert escalated.payload["escalation"]["cost"] == 1


# ---------------------------------------------------------------------------
#  4.  The measured gates
# ---------------------------------------------------------------------------

def test_the_probe_set_contains_probes_of_every_outcome(stored):
    outcomes = {(row["answered"], row["escalated"]) for row in stored["probes"]}
    assert (True, False) in outcomes        # answered directly
    assert (True, True) in outcomes         # answered by escalating
    assert (False, False) in outcomes or (False, True) in outcomes
    assert len(stored["probes"]) == len(qesc.PROBES)


def test_nothing_the_runtime_already_answers_moves(stored):
    # The cache is JSON, so a tuple the report built is read back as a list;
    # what is being checked is that these three are empty.
    safety = stored["safety"]
    assert safety["cases"] == 147
    assert list(safety["answers_moved"]) == []
    assert list(safety["answers_costing_more_than_the_first_rung"]) == []
    assert list(safety["principled_refusals_converted"]) == []
    assert safety["holds"] is True


def test_escalation_buys_something_and_the_cost_is_reported(stored):
    utility = stored["utility"]
    assert utility["has_an_instance"] is True
    assert len(utility["resolved_above_the_first_rung"]) == 4
    for cost in utility["escalated_cost"]:
        assert cost > utility["direct_cost"]


def test_two_refusals_are_returned_as_certified_absences(stored):
    assert len(stored["utility"]["certified_absences"]) == 2


def test_every_declared_refusal_of_the_evaluation_set_is_classified(stored):
    for row in stored["classified"]:
        assert row["layer"] is not None
        if row["answered"]:
            # Two of the evaluation's declared refusals are refusals *in
            # prose*: the runtime returns them as an answer whose content is
            # the refusal, so the loop never reaches a refusal to classify.
            # They are non-escalatable for that reason, not by marker.
            assert row["answered_as_prose"] is True, row["id"]
            assert row["tag"] is None, row["id"]
            assert row["escalatable"] is False, row["id"]
            continue
        assert row["tag"] is not None, row["id"]
        assert row["escalatable"] == (row["tag"] == esl.ESCALATABLE)


def test_no_refusal_classified_as_principled_becomes_an_answer(stored):
    for row in stored["classified"]:
        if row["tag"] is not None and not row["escalatable"]:
            assert row["answered"] is False, row["id"]


# ---------------------------------------------------------------------------
#  5.  The runtime, and the record
# ---------------------------------------------------------------------------

def test_the_subject_answers_from_the_cache(stored):
    session = GeometricSession()
    solution = session.ask("report query escalation")
    assert solution.kind == "report"
    assert solution.expected["cache"] == "fresh"
    assert solution.expected["cases"] == "147"
    assert solution.expected["safety_holds"] == "True"
    assert solution.expected["answers_moved"] == "0"
    assert solution.expected["principled_refusals_converted"] == "0"
    assert solution.expected["rungs"] == "3"


def test_column_three_renders_for_the_subject():
    session = GeometricSession()
    script = tct.render_script(session.ask("report query escalation"))
    assert "query_escalation" in script


def test_the_pipeline_row_names_the_study_the_subject_and_the_lean_file():
    row = next(r for r in ppl.REGISTRY if r.key == "query-escalation")
    assert row.document == "QUERY_ESCALATION_STUDY.md"
    assert row.subject == "query escalation"
    assert "EscalationLoop.lean" in row.lean
    assert "runtime/escalation_loop.py" in row.modules


def test_neither_module_holds_a_float():
    assert ex.module_float_sites(Path(qesc.__file__)) == {}
    assert ex.module_float_sites(Path(esl.__file__)) == {}


def test_the_two_copies_of_the_lean_file_agree():
    here = Path(qesc.__file__).resolve().parents[2]
    mirror = here / "glm_lean" / "RequestProject" / "GLM" / \
        "EscalationLoop.lean"
    original = here.parent / "RequestProject" / "GLM" / "EscalationLoop.lean"
    assert mirror.is_file()
    text = mirror.read_text(encoding="utf-8")
    for name in ("climb_answers_least", "climbFrom_cost_le",
                 "climbFrom_cost_ge", "climb_direct_cost",
                 "climbFrom_refused_all", "climb_principled",
                 "climb_total"):
        assert name in text
    assert "sorry" not in text
    if original.is_file():
        assert original.read_text(encoding="utf-8") == text
