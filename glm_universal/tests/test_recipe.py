"""Tests for ``glm_universal.recipe`` -- the recipe made into an object.

Every register in this package was built by hand from one recipe: carriers
whose coordinates derive from something already held, a reading over them, an
audit of what the reading gains, a query that answers where the register
decides and refuses where it does not.  ``glm_universal.recipe`` makes that
recipe's *input* an object -- a :class:`~glm_universal.recipe.spec.DomainSpec`
-- and gives one generic path from any such description to all five parts.

What is pinned here:

* the descriptions are well formed, and a malformed one is refused
  (``TestTheDescriptions``);
* the shared primitives compute what they say, compose, and construct no
  float (``TestThePrimitives``, ``TestExactness``);
* the carrier encoding round-trips through the keys (``TestTheCarrier``);
* the layer chain the description declares is a refinement chain, and what
  each widening gains is the set of pairs it splits (``TestTheWidening``);
* a coordinate no description derives is refused with the reason, and every
  derived one is answered (``TestTheRefusalBoundary``, ``TestTheQuerySurface``);
* and the claim the round exists for: three domains built by hand in earlier
  rounds are deleted and rebuilt from their descriptions alone, carrier by
  carrier and figure by figure (``TestRegeneration``);
* with the whole thing reachable from the CLI (``TestTheRuntime``).

The machine-checked counterparts are in ``RequestProject/GLM/Recipe.lean``:
``Spec.readingOn_mono`` (a wider selection always refines a narrower one),
``Spec.readingOn_append_least`` (it is the least reading keeping both),
``Spec.boundary_readingOn_nonempty_iff`` (what a widening gains is exactly the
pairs it splits), ``Spec.lossless_full_of_keys`` (keys that determine the
objects give a lossless carrier), ``Spec.answer_eq_none_iff`` (the refusal
boundary is exactly the undescribed coordinates) and ``Spec.answer_congr``
(two descriptions agreeing on the coordinates agree on every answer -- which
is regeneration, stated formally).
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal import recipe as rcp
from glm_universal.data_objects.base import N
from glm_universal.recipe import build, spec as S
from glm_universal.recipe import report as RP
from glm_universal.runtime import parser as PA
from glm_universal.runtime.session import GeometricSession, SolverError


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


@pytest.fixture(scope="module")
def summary():
    return RP.recipe_report()


DOMAINS = rcp.DESCRIPTIONS


# ===========================================================================
# 1.  THE DESCRIPTIONS
# ===========================================================================

class TestTheDescriptions:
    """Three domains, described rather than coded."""

    def test_three_domains_are_described(self):
        assert rcp.described_domains() == ("comparison", "harmonics",
                                           "economics")
        assert len(DOMAINS) == 3

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_every_description_lays_out_a_full_carrier(self, spec):
        assert len(spec.coordinates) == N == 24
        assert len(set(spec.layout)) == 24

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_the_keys_are_coordinates_and_the_refusals_are_not(self, spec):
        for key in spec.keys:
            assert spec.derives(key), key
        for refused in spec.refuses:
            assert not spec.derives(refused), refused
        assert spec.refuses, spec.name

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_every_coordinate_says_what_it_derives_from(self, spec):
        """The rule *nothing dimensional is typed twice*, made checkable."""
        for coordinate in spec.coordinates:
            assert coordinate.source, coordinate.name
            assert coordinate.kind in ("derivation", "judgement")
            assert coordinate.rule.render()

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_the_readings_are_a_chain_of_named_selections(self, spec):
        names = [reading.name for reading in spec.readings]
        assert len(names) == 3
        assert names[-1] == "full"
        assert len(set(names)) == 3

    def test_the_judgements_are_exactly_the_musical_conventions(self):
        """They are counted, not eliminated -- and none is dimensional."""
        assert rcp.COMPARISON_DESCRIPTION.judgements == ()
        assert rcp.ECONOMICS_DESCRIPTION.judgements == ()
        assert rcp.HARMONIC_DESCRIPTION.judgements == (
            "euler_gradus", "tet_step", "tet_error", "harmonic_index",
            "subharmonic_index", "is_comma")

    def test_a_description_is_reached_by_name(self):
        assert rcp.description_by_name("harmonics") is \
            rcp.HARMONIC_DESCRIPTION
        with pytest.raises(KeyError):
            rcp.description_by_name("astrology")

    def test_a_coordinate_described_twice_is_refused(self):
        twice = S.Coordinate("x", S.held("a"), "a held fact")
        with pytest.raises(ValueError):
            S.DomainSpec(name="d", facts=lambda: (), coordinates=(twice,
                                                                  twice),
                         keys=("x",), rebuild=lambda k, l: dict(k),
                         readings=())

    def test_a_key_that_is_not_a_coordinate_is_refused(self):
        one = S.Coordinate("x", S.held("a"), "a held fact")
        with pytest.raises(ValueError):
            S.DomainSpec(name="d", facts=lambda: (), coordinates=(one,),
                         keys=("y",), rebuild=lambda k, l: dict(k),
                         readings=())

    def test_a_reading_of_an_underived_coordinate_is_refused(self):
        one = S.Coordinate("x", S.held("a"), "a held fact")
        with pytest.raises(ValueError):
            S.DomainSpec(name="d", facts=lambda: (), coordinates=(one,),
                         keys=("x",), rebuild=lambda k, l: dict(k),
                         readings=(S.Reading("r", ("y",)),))

    def test_a_refusal_the_description_derives_is_refused(self):
        one = S.Coordinate("x", S.held("a"), "a held fact")
        with pytest.raises(ValueError):
            S.DomainSpec(name="d", facts=lambda: (), coordinates=(one,),
                         keys=("x",), rebuild=lambda k, l: dict(k),
                         readings=(), refuses=("x",))


# ===========================================================================
# 2.  THE SHARED PRIMITIVES
# ===========================================================================

class TestThePrimitives:
    """The vocabulary a description is written in."""

    FACTS = {"name": "thing", "ratio": Fraction(3, 2), "low": Fraction(293),
             "high": Fraction(373), "value": Fraction(363), "n": 360,
             "flagged": True, "text": "a b c", "words": ("a", "b")}

    def test_every_primitive_is_declared(self):
        assert len(S.PRIMITIVES) == 25
        assert len(set(S.PRIMITIVES)) == 25
        for name in S.PRIMITIVES:
            assert name != "judgement"

    def test_a_held_fact_is_taken_as_it_stands(self):
        assert S.held("ratio")(self.FACTS) == Fraction(3, 2)

    def test_the_numerator_and_denominator_are_in_lowest_terms(self):
        assert S.numerator("ratio")(self.FACTS) == 3
        assert S.denominator("ratio")(self.FACTS) == 2

    def test_a_quotient_is_exact(self):
        rule = S.quotient("high", "low")
        assert rule(self.FACTS) == Fraction(373, 293)

    def test_an_affine_position_reads_a_bracket(self):
        rule = S.affine_position("value", "low", "high")
        assert rule(self.FACTS) == Fraction(7, 8)

    def test_the_primitives_compose(self):
        """A primitive takes a held fact *or* another derivation."""
        rule = S.numerator(S.quotient("high", "low"))
        assert rule(self.FACTS) == 373
        assert "quotient" in rule.render()

    def test_a_p_adic_exponent_and_the_odd_part(self):
        assert S.p_adic_exponent("n", 2)(self.FACTS) == 3
        assert S.p_adic_exponent("n", 3)(self.FACTS) == 2
        assert S.odd_part("n")(self.FACTS) == 45

    def test_a_flag_is_zero_or_one(self):
        assert S.flag("flagged")(self.FACTS) == 1

    def test_a_judgement_is_marked_as_one(self):
        rule = S.judgement("the domain says so", lambda facts: 1)
        assert rule.is_judgement
        assert rule.primitive == "judgement"
        assert S.Coordinate("j", rule, "a stated convention").kind == \
            "judgement"

    def test_a_derivation_from_a_fact_the_object_lacks_is_refused(self):
        with pytest.raises(KeyError):
            S.held("nowhere")(self.FACTS)

    def test_no_primitive_returns_a_float(self):
        for rule in (S.held("ratio"), S.numerator("ratio"),
                     S.quotient("high", "low"), S.difference("high", "low"),
                     S.midpoint("low", "high"),
                     S.affine_position("value", "low", "high"),
                     S.odd_part("n"), S.flag("flagged")):
            assert not isinstance(rule(self.FACTS), float)


# ===========================================================================
# 3.  THE CARRIER ENCODING AND ITS READ-BACK
# ===========================================================================

class TestTheCarrier:

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_the_register_is_generated_from_the_description(self, spec):
        objects = build.register(spec)
        assert len(objects) == len(spec.facts())
        for obj in objects:
            assert obj.domain == spec.name
            assert len(obj.carrier) == 24
            assert obj.layout == spec.layout

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_every_object_is_recovered_from_its_carrier(self, spec):
        """``GLM.Recipe.Spec.lossless_full_of_keys``, on the register."""
        audit = build.read_back_audit(spec)
        assert audit["failures"] == ()
        assert audit["collisions"] == ()
        assert audit["recovered"] == audit["objects"]
        assert audit["distinct_carriers"] == audit["objects"]
        assert audit["lossless"] is True

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_the_labels_are_carried_rather_than_derived(self, spec):
        """A register's names are not recoverable from its carriers."""
        assert "name" in spec.labels
        for label in spec.labels:
            assert label not in spec.layout

    def test_the_registers_are_the_sizes_the_hand_written_modules_ship(self):
        sizes = {spec.name: len(spec.facts()) for spec in DOMAINS}
        assert sizes == {"comparison": 45, "harmonics": 28, "economics": 21}

    def test_the_description_can_be_read_back_as_a_table(self):
        rows = build.describe(rcp.HARMONIC_DESCRIPTION)
        assert len(rows) == 24
        assert {row["kind"] for row in rows} == {"derivation", "judgement"}
        assert all(row["rule"] and row["source"] for row in rows)


# ===========================================================================
# 4.  THE WIDENING AUDIT
# ===========================================================================

class TestTheWidening:

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_the_chain_is_a_refinement_chain(self, spec):
        """Appending coordinates can only widen: ``Spec.readingOn_mono``."""
        audit = build.widening_audit(spec)
        assert audit["chain_intact"] is True
        assert audit["lossless"] is True
        for step in audit["steps"]:
            assert step["refines"] is True
            assert step["classes_above"] >= step["classes_below"]

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_what_a_widening_gains_is_the_pairs_it_splits(self, spec):
        """``Spec.boundary_readingOn_nonempty_iff``, measured."""
        for step in build.widening_audit(spec)["steps"]:
            gained = step["gained_pairs"]
            grew = step["classes_above"] > step["classes_below"]
            assert grew == (gained > 0)
            if gained:
                assert step["example"] is not None

    def test_the_comparison_chain_gains_exactly_three_pairs(self):
        steps = build.widening_audit(rcp.COMPARISON_DESCRIPTION)["steps"]
        assert [step["gained_pairs"] for step in steps] == [1, 2]
        assert [step["classes_below"] for step in steps] == [42, 43]
        assert steps[-1]["classes_above"] == 45

    def test_the_top_of_every_chain_tells_every_object_apart(self):
        for spec in DOMAINS:
            audit = build.widening_audit(spec)
            assert audit["top_resolution"] == audit["objects"]

    def test_a_reading_the_description_does_not_declare_is_refused(self):
        with pytest.raises(KeyError):
            build.resolution(rcp.HARMONIC_DESCRIPTION, "nowhere")


# ===========================================================================
# 5.  THE REFUSAL BOUNDARY
# ===========================================================================

class TestTheRefusalBoundary:

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_the_described_are_answered_and_the_absent_refused(self, spec):
        """``GLM.Recipe.Spec.answer_eq_none_iff``, exercised."""
        audit = build.refusal_audit(spec)
        assert audit["derived"] == 24
        assert audit["answered"] == 24
        assert audit["all_derived_answered"] is True
        assert audit["all_absent_refused"] is True
        assert len(audit["refused"]) == len(spec.refuses)
        for row in audit["refused"]:
            assert row["answered"] is False
            assert row["coordinate"] in row["reason"]

    def test_an_object_the_register_does_not_hold_is_refused_too(self):
        result = build.answer(rcp.COMPARISON_DESCRIPTION, "span_ratio",
                              "cup_of_coffee")
        assert result["answered"] is False
        assert "no object named" in result["reason"]

    def test_a_cent_is_refused_because_it_is_a_logarithm(self):
        assert "cents" in rcp.HARMONIC_DESCRIPTION.refuses
        result = build.answer(rcp.HARMONIC_DESCRIPTION, "cents",
                              "perfect_fifth")
        assert result["answered"] is False


# ===========================================================================
# 6.  THE QUERY SURFACE
# ===========================================================================

class TestTheQuerySurface:

    def test_a_coordinate_is_answered_off_whichever_domain_derives_it(self):
        answered = RP.ask("span_ratio", "tea")
        assert answered["answered"] is True
        assert answered["domain"] == "comparison"
        assert answered["value"] == Fraction(373, 293)
        assert answered["kind"] == "derivation"

    def test_the_same_surface_reaches_a_second_domain(self):
        answered = RP.ask("numerator", "perfect_fifth")
        assert answered["answered"] is True
        assert answered["domain"] == "harmonics"
        assert answered["value"] == 3

    def test_a_judgement_is_answered_and_reported_as_one(self):
        answered = RP.ask("euler_gradus", "perfect_fifth")
        assert answered["answered"] is True
        assert answered["kind"] == "judgement"
        assert answered["value"] == 4

    def test_a_domain_may_be_named(self):
        answered = RP.ask("numerator", "perfect_fifth", "harmonics")
        assert answered["answered"] is True
        with pytest.raises(KeyError):
            RP.ask("numerator", "perfect_fifth", "astrology")

    def test_a_coordinate_no_description_derives_is_refused(self):
        refused = RP.ask("cents", "perfect_fifth")
        assert refused["answered"] is False
        assert "no description derives" in refused["reason"]
        assert "comparison, harmonics, economics" in refused["reason"]

    def test_an_object_no_register_holds_is_refused_with_the_other_reason(
            self):
        refused = RP.ask("span_ratio", "cup_of_coffee")
        assert refused["answered"] is False
        assert "no register holds an object named" in refused["reason"]

    def test_the_shared_surface_is_measured_rather_than_claimed(self):
        shared = RP.shared_surface()
        assert shared["coordinates"] == 72
        assert shared["derivations"] == 66
        assert shared["judgements"] == 6
        assert shared["judgements_by_domain"] == {
            "comparison": 0, "harmonics": 6, "economics": 0}
        assert shared["primitives_available"] == 25
        assert len(shared["primitives_used"]) == 23
        assert set(shared["primitives_used"]) <= set(S.PRIMITIVES)


# ===========================================================================
# 7.  REGENERATION -- THE TEST THE ROUND EXISTS FOR
# ===========================================================================

class TestRegeneration:

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_the_domain_comes_back_from_its_description_alone(self, spec):
        result = build.regeneration(spec)
        assert result["mismatches"] == ()
        assert result["carriers_compared"] == len(spec.facts())
        assert result["carriers_identical"] == result["carriers_compared"]
        assert result["objects_agree"] is True
        assert result["objects_disagreeing"] == ()
        assert result["figures_unchanged"] is True
        assert result["regenerated"] is True

    def test_all_ninety_four_carriers_are_identical(self, summary):
        verdict = summary["verdict"]
        assert verdict["carriers_compared"] == 94
        assert verdict["carriers_identical"] == 94
        assert verdict["domains_described"] == 3
        assert verdict["domains_regenerated"] == 3
        assert verdict["chains_intact"] is True
        assert verdict["all_lossless"] is True
        assert verdict["figures_unchanged"] is True
        assert verdict["verdict"] == "regenerated"

    def test_the_figures_the_reasoning_modules_measure_are_named(self,
                                                                 summary):
        named = {row["domain"]: row["figures"] for row in summary["domains"]}
        assert named["comparison"]
        assert named["harmonics"]
        assert named["economics"]
        assert all(figures for figures in named.values())

    def test_a_description_with_no_native_constructor_cannot_regenerate(self):
        one = S.Coordinate("x", S.held("x"), "a held fact")
        spec = S.DomainSpec(
            name="d", facts=lambda: ({"name": "o", "x": 1},),
            coordinates=(one,), keys=("x",),
            rebuild=lambda keyed, labels: {**keyed, **labels},
            readings=(S.Reading("full", ("x",)),))
        with pytest.raises(ValueError):
            build.regenerate(spec)

    @pytest.mark.exhaustive
    def test_the_slow_figures_are_unchanged_too(self):
        """The audits that cost minutes rather than milliseconds."""
        for spec in DOMAINS:
            if not spec.figures_exhaustive:
                continue
            result = build.regeneration(spec, exhaustive=True)
            assert result["figures_unchanged"] is True
            assert result["regenerated"] is True


# ===========================================================================
# 8.  EXACTNESS
# ===========================================================================

class TestExactness:

    @pytest.mark.parametrize("spec", DOMAINS, ids=lambda s: s.name)
    def test_no_carrier_coordinate_is_a_float(self, spec):
        for values in build.carriers(spec):
            for value in values:
                assert isinstance(value, (int, Fraction))
                assert not isinstance(value, float)

    def test_the_payload_holds_no_float(self, sess):
        payload = sess.ask("derive span_ratio of tea").payload

        def walk(value):
            assert not isinstance(value, float)
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)

        walk(payload)


# ===========================================================================
# 9.  THE RUNTIME
# ===========================================================================

class TestTheRuntime:

    def test_derive_is_a_declared_query_kind(self):
        assert "derive" in PA.KINDS

    def test_the_parser_classifies_the_kind(self, sess):
        query = PA.parse_query("derive span_ratio of tea", sess.index)
        assert query.kind == "derive"
        assert query.options["coordinate"] == "span_ratio"
        assert query.options["object"] == "tea"

    def test_the_parser_reads_a_named_domain(self, sess):
        query = PA.parse_query("derive numerator of perfect_fifth in "
                               "harmonics", sess.index)
        assert query.kind == "derive"
        assert query.options["domain"] == "harmonics"

    def test_the_query_answers(self, sess):
        solution = sess.ask("derive span_ratio of tea")
        assert solution.ok is True
        assert solution.kind == "derive"
        assert "373/293" in solution.answer
        assert solution.payload["answer"]["domain"] == "comparison"

    def test_the_query_refuses_at_the_boundary(self, sess):
        solution = sess.ask("derive cents of perfect_fifth")
        assert solution.ok is False
        assert solution.error is not None
        assert solution.error.startswith("derive: ")
        assert "no description derives" in solution.error

    def test_the_solver_itself_raises_the_refusal(self, sess):
        query = PA.parse_query("derive cents of perfect_fifth", sess.index)
        with pytest.raises(SolverError):
            sess._solve_derive(query)

    def test_the_report_subject_is_reachable(self, sess):
        solution = sess.ask("report recipe")
        assert solution.ok is True
        assert solution.payload["report"]["verdict"] == "regenerated"
        assert solution.payload["report"]["coordinates"] == 72

    @pytest.mark.parametrize("surface", ["report recipes",
                                         "report descriptions",
                                         "report regeneration",
                                         "report generic path"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    def test_the_report_states_the_verdict(self, sess):
        answer = sess.ask("report recipe").answer
        assert "3 domains described" in answer
        assert "94 of 94 carriers" in answer
        assert "regenerated" in answer

    def test_the_payload_is_json_serialisable(self, sess):
        import json
        json.dumps(sess.ask("report recipe").payload)
        json.dumps(sess.ask("derive span_ratio of tea").payload)

    @pytest.mark.exhaustive
    def test_the_generated_script_reproduces_column_two(self, sess):
        from glm_universal.runtime import tct_engine as tct
        for question in ("report recipe", "derive span_ratio of tea"):
            trace = tct.verify_trace(tct.build_trace(sess.ask(question)))
            assert trace.verdict is not None
            assert trace.verdict.executed
            assert trace.verdict.returncode == 0
            assert trace.verdict.matches_column2
            assert trace.verdict.mismatches == ()
            assert trace.verdict.missing_keys == ()
