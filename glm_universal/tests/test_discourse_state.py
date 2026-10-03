"""Discourse state -- a set carried as a column, the fourth shape of
follow-up, and follow-ups bound on every surface, pinned.

``glm_universal.runtime.discourse`` is the layer
(``studies/DISCOURSE_STATE_STUDY.md``, Phase 92);
``glm_universal.runtime.discourse_report`` measures the declared cases of
``glm_universal.evaluation.discourse_cases``.  The facts the round rests on
are theorems of ``RequestProject/GLM/DiscourseState.lean`` (D7).
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from glm_universal.evaluation import discourse_cases as C
from glm_universal.reasoning import exactness as ex
from glm_universal.runtime import discourse as D
from glm_universal.runtime import discourse_report as R
from glm_universal.runtime.conversation import Conversation, FollowUpError
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[2] / "glm_lean" / "RequestProject"
        / "GLM" / "DiscourseState.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


def _outcome(session, script, surfaces=False):
    return R.outcome_of(D.Discourse(session, surfaces=surfaces),
                        script)["outcome"]


class TestTheColumn:

    def test_the_tie_is_a_column_of_fourteen(self, session):
        layer = D.Discourse(session)
        layer.ask("largest abstract_concrete in carrier:lexicon")
        sol = layer.ask("describe it")
        assert sol.kind == "column" and sol.ok
        assert tuple(sol.payload["members"]) == C.LEXICON_TIE
        assert len(sol.payload["cells"]) == 14

    def test_every_cell_is_the_answer_asked_alone(self, session):
        layer = D.Discourse(session)
        layer.ask("smallest charge in molecule")
        sol = layer.ask("field molar_mass_u of it")
        fresh = GeometricSession()
        for cell in sol.payload["cells"]:
            assert fresh.ask(cell["asked"]).answer == cell["answer"]
        assert "7501/125" in sol.payload["cells"][0]["answer"]

    def test_a_hole_refuses_the_column(self, session):
        layer = D.Discourse(session)
        layer.ask("largest abstract_concrete in carrier:lexicon")
        with pytest.raises(FollowUpError) as err:
            layer.ask("field electronegativity_pauling of it")
        assert err.value.reason == "column-incomplete"

    def test_the_switch_returns_the_refusal(self, session):
        layer = D.Discourse(session, carry=False)
        layer.ask("largest abstract_concrete in carrier:lexicon")
        with pytest.raises(FollowUpError) as err:
            layer.ask("describe it")
        assert err.value.reason == "ambiguous-antecedent"

    def test_a_comparison_is_not_a_set(self, session):
        assert _outcome(session, ("order atomic_weight_u of carbon and "
                                  "oxygen", "describe it")) \
            == "ambiguous-antecedent"


class TestTheFourthShape:

    def test_shapes_are_detected_in_order(self, session):
        layer = D.Discourse(session)
        assert layer.shape_of("why?") == "why"
        assert layer.shape_of("describe the one before that") == "prior"
        assert layer.shape_of("describe both of them") == "plural"
        assert layer.shape_of("describe it") == "pronoun"
        assert layer.shape_of("is it true that energy is mass") is None

    def test_the_one_before_that(self, session):
        assert _outcome(session, ("describe carbon", "describe water",
                                  "describe the one before that")) == "C"

    def test_both_and_them(self, session):
        assert _outcome(session, ("describe carbon", "describe oxygen",
                                  "describe both of them")) \
            == ("column", ("C", "O"))
        assert _outcome(session, ("describe carbon", "describe them")) \
            == "number-mismatch"

    def test_why_reads_the_record(self, session):
        layer = D.Discourse(session)
        layer.ask("describe carbon")
        layer.ask("describe it")
        sol = layer.ask("why?")
        assert sol.kind == "why" and sol.payload["subject"] == "C"
        with pytest.raises(FollowUpError) as err:
            D.Discourse(session).ask("why?")
        assert err.value.reason == "no-antecedent"

    def test_whole_first(self, session):
        layer = D.Discourse(session)
        text = "field atomic_weight_u of carbon"
        assert layer.ask(text).answer == session.ask(text).answer


class TestTheMarks:

    def test_every_group_as_declared(self):
        groups = R.group_report()
        for name, g in groups.items():
            assert g["met"] == g["cases"], (name, g["wrong"])
        assert sum(g["cases"] for g in groups.values()) == len(C.ALL_CASES)

    def test_the_controls(self):
        c = R.control_report()
        assert c["met"], c
        assert c["base"]["new_as_declared"] == []
        assert c["session_alone"]["answers_as_declared"] == []

    def test_nothing_earlier_moves_but_the_declared_move(self):
        e = R.earlier_report()
        assert e["met"], e
        assert e["moved"] == ["pronoun-tie-refused"]

    def test_the_column_computes_nothing(self):
        cells = R.cells_report()
        assert cells["met"], cells
        assert cells["cells"] >= 30

    def test_the_census_releases_nothing(self):
        census = R.census_report()
        assert census["met"], census
        assert census["taken_answered_alone"] == 0


class TestTheCommandLine:

    def test_converse(self):
        from GLM import main as glm_main
        out = io.StringIO()
        code = glm_main(["--converse", "smallest charge in molecule",
                         "--converse", "field molar_mass_u of them",
                         "--converse", "why?"], out=out)
        text = out.getvalue()
        assert code == 0
        assert "COLUMN" in text and "carbonate ion" in text
        assert "turn 1" in text


class TestStatic:

    def test_no_float(self):
        for mod in (D, R):
            assert ex.module_float_sites(Path(mod.__file__)) == {}

    def test_the_lean_file(self):
        text = LEAN.read_text()
        assert "sorry" not in text
        for name in ("resolveD_eq_lift_resolve", "resolveD_column_licensed",
                     "resolveD_column_produced", "resolveD_incomplete_hole",
                     "column_cell_eq_alone", "resolvePlural_both_two",
                     "resolvePlural_never_single",
                     "resolvePrior_cons_deciding",
                     "resolvePrior_stable_under_dead_turn",
                     "tie_is_a_column", "prior_walks_past_unlicensed"):
            assert f"theorem {name}" in text, name
