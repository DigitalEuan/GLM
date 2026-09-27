"""Tests for the named-relation analogy layer.

Two modules are under test and one runtime path:

* :mod:`glm_universal.reasoning.periodic_table` -- period, group and block
  derived from the seven period boundaries and nothing else.  The tests check
  the derivation against facts about the table that hold independently of it
  (the noble gases are the last element of each period; boron and aluminium
  share a group; the f-block makes group 3 of periods 6 and 7 ambiguous), and
  against the period the chemistry register stores for all 118 elements.
* :mod:`glm_universal.reasoning.analogy_models` -- four models that say what
  the relation between ``A`` and ``B`` *is* and transport it to ``C``.  The
  tests check both halves of each model: what it answers, and what it
  declines to answer.
* :meth:`GeometricSession._solve_analogy` -- that a named relation is used in
  preference to the displacement solver, that a model's refusal is reported
  rather than papered over, and that naming a subspace still buys the
  geometric solve.

Run with::

    uv run pytest glm_universal/tests/test_analogy_models.py -q
"""

from __future__ import annotations

import pytest

from glm_universal.data_objects import elements as DE
from glm_universal.data_objects import physics as DP
from glm_universal.data_objects import semantic_lexicon as DL
from glm_universal.reasoning import analogy_models as AM
from glm_universal.reasoning import periodic_table as PT
from glm_universal.runtime.session import GeometricSession


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture(scope="module")
def elements():
    return DE.element_objects()


@pytest.fixture(scope="module")
def physics():
    return DP.physics_objects()


@pytest.fixture(scope="module")
def lexicon():
    objects = DL.semantic_lexicon_objects()
    if isinstance(objects, tuple) and objects and isinstance(objects[0],
                                                             tuple):
        objects = objects[0]
    return tuple(objects)


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE DERIVED TABLE
# ===========================================================================

class TestDerivedPositions:
    """Period, group and block are computed, never looked up."""

    def test_the_only_tabulated_input_is_the_period_boundaries(self):
        assert len(PT.PERIOD_BOUNDS) == 7
        assert PT.PERIOD_BOUNDS[0] == (1, 1, 2)
        assert PT.MAX_Z == 118
        # The boundaries tile 1..118 without gap or overlap.
        covered = []
        for _period, lo, hi in PT.PERIOD_BOUNDS:
            covered.extend(range(lo, hi + 1))
        assert covered == list(range(1, PT.MAX_Z + 1))

    def test_every_period_ends_in_group_eighteen(self):
        for _period, _lo, hi in PT.PERIOD_BOUNDS:
            assert PT.position_of(hi).group == 18

    def test_the_noble_gases_come_out_of_the_derivation(self):
        assert [PT.symbol_at(p, 18) for p, _lo, _hi in PT.PERIOD_BOUNDS] == [
            "He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"]

    def test_group_thirteen_comes_out_of_the_derivation(self):
        assert [PT.symbol_at(p, 13) for p in range(2, 8)] == [
            "B", "Al", "Ga", "In", "Tl", "Nh"]

    def test_the_block_of_each_element_is_derived(self):
        assert PT.position_of_symbol("H").block == "s"
        assert PT.position_of_symbol("C").block == "p"
        assert PT.position_of_symbol("Fe").block == "d"
        assert PT.position_of_symbol("Ce").block == "f"

    def test_the_derived_period_agrees_with_the_register_for_all_118(self):
        report = PT.periodic_report()
        assert report["elements"] == 118
        assert report["periods_agree_with_register"] is True
        assert report["disagreements"] == []

    def test_the_f_block_makes_exactly_two_positions_ambiguous(self):
        report = PT.periodic_report()
        assert report["ambiguous_positions"] == [
            "period 6, group 3", "period 7, group 3"]

    def test_an_ambiguous_position_is_refused_and_says_why(self):
        with pytest.raises(PT.PositionError) as excinfo:
            PT.atomic_number_at(6, 3)
        assert "15 elements" in str(excinfo.value)
        assert "f-block" in str(excinfo.value)

    def test_an_empty_position_is_refused(self):
        # Period 1 has only groups 1 and 18.
        with pytest.raises(PT.PositionError) as excinfo:
            PT.atomic_number_at(1, 5)
        assert "empty" in str(excinfo.value)

    def test_a_position_outside_the_table_is_refused(self):
        with pytest.raises(PT.PositionError):
            PT.atomic_number_at(4, 19)
        with pytest.raises(PT.PositionError):
            PT.position_of(0)
        with pytest.raises(PT.PositionError):
            PT.position_of(119)

    def test_a_non_element_symbol_is_refused(self):
        with pytest.raises(PT.PositionError):
            PT.position_of_symbol("Xx")


# ===========================================================================
# 2.  periodic_step
# ===========================================================================

class TestPeriodicStep:

    def test_the_headline_case_transports_down_a_group(self, elements):
        result = AM.periodic_step("He", "Ne", "Ar", elements)
        assert result is not None
        assert result.answer == "Kr"
        assert result.unique
        assert result.witness["d_period"] == "1"
        assert result.witness["d_group"] == "0"

    def test_a_group_step_transports_across(self, elements):
        result = AM.periodic_step("B", "Al", "C", elements)
        assert result.answer == "Si"
        assert result.witness["d_period"] == "1"
        assert result.witness["d_group"] == "0"

    def test_a_diagonal_step_transports_both_coordinates(self, elements):
        # Li (2, 1) -> Na (3, 1) is down a period; Be (2, 2) -> Mg (3, 2).
        assert AM.periodic_step("Li", "Na", "Be", elements).answer == "Mg"
        # Li (2, 1) -> Be (2, 2) is one group across; Na (3, 1) -> Mg (3, 2).
        assert AM.periodic_step("Li", "Be", "Na", elements).answer == "Mg"

    def test_the_step_is_reversible(self, elements):
        assert AM.periodic_step("Kr", "Ar", "Ne", elements).answer == "He"

    def test_the_model_declines_when_a_term_is_not_an_element(self, elements):
        assert AM.periodic_step("He", "Ne", "energy", elements) is None
        assert AM.periodic_step("water", "Ne", "Ar", elements) is None

    def test_the_model_declines_a_step_of_zero(self, elements):
        assert AM.periodic_step("He", "He", "Ar", elements) is None

    def test_the_f_block_position_is_refused_not_guessed(self, elements):
        # Ca (4, 2) -> Sc (4, 3) transported to Ba (6, 2) asks for (6, 3).
        result = AM.periodic_step("Ca", "Sc", "Ba", elements)
        assert result is not None
        assert result.answer is None
        assert result.refusal is not None
        assert "f-block" in result.refusal
        assert result.witness["target_period"] == "6"
        assert result.witness["target_group"] == "3"

    def test_a_step_off_the_table_is_refused(self, elements):
        # He (1, 18) -> Ne (2, 18) transported to Og (7, 18) asks for period 8.
        result = AM.periodic_step("He", "Ne", "Og", elements)
        assert result is not None
        assert result.answer is None
        assert result.refusal is not None

    def test_the_refusal_still_reports_the_relation(self, elements):
        result = AM.periodic_step("Ca", "Sc", "Ba", elements)
        assert "step of (+0 period, +1 group)" in result.relation


# ===========================================================================
# 3.  reciprocal_dimension
# ===========================================================================

class TestReciprocalDimension:

    def test_length_wavenumber_time_gives_frequency(self, physics):
        result = AM.reciprocal_dimension("length", "wavenumber", "time",
                                         physics)
        assert result is not None
        assert "frequency" in result.answer.split(" or ")
        assert result.model == "reciprocal_dimension"

    def test_the_relation_runs_the_other_way_too(self, physics):
        result = AM.reciprocal_dimension("time", "frequency", "length",
                                         physics)
        assert result is not None
        assert "wavenumber" in result.answer.split(" or ")

    def test_the_model_declines_a_step_that_is_not_a_reciprocal(self,
                                                                physics):
        assert AM.reciprocal_dimension("length", "area", "time",
                                       physics) is None
        assert AM.reciprocal_dimension("force", "energy", "pressure",
                                       physics) is None

    def test_the_model_declines_when_a_is_dimensionless(self, physics):
        # A dimensionless quantity is its own reciprocal's dimension, so the
        # pattern would match every dimensionless pair and mean nothing.
        names = {o.name for o in physics}
        assert "strain" in names
        assert AM.reciprocal_dimension("strain", "strain", "time",
                                       physics) is None

    def test_the_answer_excludes_the_operands(self, physics):
        result = AM.reciprocal_dimension("length", "wavenumber", "time",
                                         physics)
        assert "time" not in result.candidates
        assert "length" not in result.candidates

    def test_a_surviving_tie_is_reported_and_not_broken(self, physics):
        result = AM.reciprocal_dimension("length", "wavenumber", "time",
                                         physics)
        if not result.unique:
            assert " or " in result.answer
            assert len(result.candidates) == len(result.answer.split(" or "))


# ===========================================================================
# 4.  scale_shift
# ===========================================================================

class TestScaleShift:

    def test_a_thousandfold_step_transports_to_another_dimension(self,
                                                                 physics):
        result = AM.scale_shift("gram", "mass", "millisecond", physics)
        assert result is not None
        assert "time" in result.answer.split(" or ")
        assert result.witness["d_scale"] == "3"

    def test_the_model_declines_when_the_dimensions_differ(self, physics):
        assert AM.scale_shift("gram", "time", "millisecond", physics) is None

    def test_the_model_declines_when_the_scale_is_unchanged(self, physics):
        assert AM.scale_shift("length", "length", "time", physics) is None

    def test_the_model_declines_on_a_name_it_does_not_hold(self, physics):
        assert AM.scale_shift("gram", "mass", "He", physics) is None


# ===========================================================================
# 5.  lexicon_relation
# ===========================================================================

class TestLexiconRelation:

    def test_an_antonym_is_transported(self, lexicon):
        result = AM.lexicon_relation("hot", "cold", "fast", lexicon)
        assert result is not None
        assert "slow" in result.answer.split(" or ")
        assert "opposite_of" in result.witness["relations"]

    def test_the_states_of_matter_ladder_beats_the_hypernym(self, lexicon):
        # `fluid` is nearer to `liquid` in the primitive metric because it is
        # its hypernym; the stated relation gives `gas`.
        result = AM.lexicon_relation("solid", "liquid", "liquid", lexicon)
        assert result is not None
        assert "gas" in result.answer.split(" or ")
        assert "fluid" not in result.answer.split(" or ")

    def test_the_answer_may_be_b_itself(self, lexicon):
        # Only A and C are excluded: two things can stand in the same
        # relation to one third thing, so B must stay reachable.  The states
        # ladder is exactly that case read the other way.
        result = AM.lexicon_relation("gas", "liquid", "solid", lexicon)
        assert result is not None
        assert result.answer is not None

    def test_a_vague_relation_is_not_transportable(self, lexicon, subtests):
        """``related_to`` transports nothing -- and the repair is what does.

        The stored lexicon is checked with ``repaired=False``, which is the
        control: on a pair the register links by ``related_to`` alone, the
        model declines.  With the repair switched on, such a pair may become
        answerable -- but only through a relation the physics register
        *decided* (``same_dimension_as``, ``differs_by``), never through the
        vague one, and that is asserted too.
        """
        assert AM.VAGUE_RELATIONS == ("related_to",)
        triples = [(s, r, o) for obj in lexicon
                   for (s, r, o) in obj.attributes.get("triples", ())
                   if r == "related_to"]
        assert triples, "the register should carry some related_to triples"
        vague_only = [(s, o) for s, _r, o in triples
                      if {r for obj in lexicon
                          for (ss, r, oo) in obj.attributes.get("triples", ())
                          if {ss, oo} == {s, o}} == {"related_to"}]
        if not vague_only:                           # pragma: no cover
            pytest.skip("every related_to pair carries another relation too")
        for subject, other in vague_only:
            with subtests.test(pair=(subject, other)):
                assert AM.lexicon_relation(subject, other, "fast", lexicon,
                                           repaired=False) is None
                answered = AM.lexicon_relation(subject, other, "fast",
                                               lexicon)
                if answered is not None:
                    assert "related_to" not in answered.relation

    def test_the_model_declines_when_no_triple_links_a_and_b(self, lexicon):
        assert AM.lexicon_relation("fast", "liquid", "hot", lexicon) is None

    def test_a_relation_that_reaches_nothing_from_c_is_refused(self, lexicon):
        result = AM.lexicon_relation("water", "liquid", "electron", lexicon)
        assert result is not None
        assert result.answer is None
        assert "is_a" in result.refusal

    def test_the_synonym_groups_are_reflexive_and_disjoint(self):
        seen = set()
        for group in AM.RELATION_SYNONYMS:
            assert len(group) == len(set(group))
            assert not (set(group) & seen)
            seen |= set(group)
            for name in group:
                assert AM._synonyms(name) == group
        assert AM._synonyms("opposite_of") == ("opposite_of",)


# ===========================================================================
# 6.  THE LAYER AND ITS REPORT
# ===========================================================================

class TestTheLayer:

    def test_every_model_name_is_a_callable_in_a_domain(self):
        registered = {fn.__name__ for fns in AM.MODELS_BY_DOMAIN.values()
                      for fn in fns}
        assert registered == set(AM.MODEL_NAMES)

    def test_a_domain_with_no_models_declines(self, elements):
        assert AM.explain_analogy("nowhere", "He", "Ne", "Ar",
                                  elements) is None

    def test_explain_returns_the_first_model_that_recognises_the_pair(
            self, physics):
        result = AM.explain_analogy("physics", "length", "wavenumber", "time",
                                    physics)
        assert result.model == "reciprocal_dimension"
        result = AM.explain_analogy("physics", "gram", "mass", "millisecond",
                                    physics)
        assert result.model == "scale_shift"

    def test_the_report_solves_every_case_as_expected(self):
        report = AM.analogy_models_report()
        assert report["cases_total"] == len(AM.REPORT_CASES)
        assert report["cases_as_expected"] == report["cases_total"], [
            row for row in report["cases"] if not row["as_expected"]]

    def test_the_report_carries_the_table_derivation(self):
        report = AM.analogy_models_report()
        assert report["periodic_table"]["periods_agree_with_register"] is True

    def test_a_refusal_case_in_the_report_carries_its_reason(self):
        report = AM.analogy_models_report()
        refusals = [row for row in report["cases"] if row["answer"] == ""]
        assert refusals
        for row in refusals:
            assert row["refusal"]

    def test_the_report_is_deterministic(self):
        first = AM.analogy_models_report()
        second = AM.analogy_models_report()
        assert first == second


# ===========================================================================
# 7.  THE RUNTIME PATH
# ===========================================================================

class TestTheSessionUsesTheModels:

    def test_a_named_relation_is_preferred_to_a_displacement(self, sess):
        sol = sess.ask("He : Ne :: Ar : ?")
        assert sol.ok
        assert sol.expected["model"] == "periodic_step"
        assert sol.expected["answer"] == "Kr"
        assert "result" not in sol.payload

    def test_the_reciprocal_case_is_answered_by_its_model(self, sess):
        sol = sess.ask("length : wavenumber :: time : ?")
        assert sol.ok
        assert sol.expected["model"] == "reciprocal_dimension"
        assert "frequency" in sol.answer

    def test_the_scale_case_is_answered_by_its_model(self, sess):
        sol = sess.ask("gram : mass :: millisecond : ?")
        assert sol.ok
        assert sol.expected["model"] == "scale_shift"
        assert "time" in sol.answer

    def test_a_model_refusal_is_reported_not_overwritten(self, sess):
        sol = sess.ask("Ca : Sc :: Ba : ?")
        assert not sol.ok
        assert "f-block" in sol.error

    def test_an_unrecognised_relation_falls_back_on_the_displacement(self,
                                                                     sess):
        sol = sess.ask("force : energy :: pressure : ?")
        assert sol.ok
        assert "result" in sol.payload
        model_step = next(s for s in sol.steps if s.label == "model")
        assert "No relation model recognises" in model_step.language

    def test_naming_a_subspace_asks_for_the_geometric_solve(self, sess):
        sol = sess.ask("He : Ne :: Ar : ? in chemistry.position")
        assert sol.ok
        assert sol.payload["subspace"] == "chemistry.position"
        assert "result" in sol.payload

    def test_the_lexicon_subspace_can_now_be_named(self, sess):
        sol = sess.ask("hot : cold :: fast : ? in lexicon.primitives")
        assert sol.ok
        assert sol.payload["subspace"] == "lexicon.primitives"

    def test_the_steps_of_a_model_answer_name_the_relation(self, sess):
        sol = sess.ask("He : Ne :: Ar : ?")
        labels = [step.label for step in sol.steps]
        assert labels[:3] == ["resolve", "model", "position"]
        assert "periodic_step" in sol.steps[1].mathematics

    def test_the_report_subject_is_reachable(self, sess):
        sol = sess.ask("report analogies")
        assert sol.ok
        assert "relation models" in sol.answer.lower()
