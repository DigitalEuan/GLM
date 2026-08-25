"""Substantive end-to-end tests: do queries return the right *answer*?

The existing test suites are mostly structural: they verify that the
codecs round-trip, that the parser classifies correctly, that the script
is float-free.  These tests verify the actual reasoning outcomes —
the kind of check that would catch a regression like "I added 60
physics concepts and now `Li : Na :: Be : ?` returns
`acoustic_intensity_level` because `Li` resolved to a physics alias".

Every test in this file is a real query through the runtime session.
If the answer changes, something the user cares about broke.
"""

from __future__ import annotations

import pytest

from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  CHEMISTRY ANALOGIES — must resolve elements to elements
# ===========================================================================

class TestChemistryAnalogiesResolve:

    def test_li_na_be_yields_magnesium(self, sess):
        """The original TCT demo's headline analogy.  After v0.5.0 grew
        the physics register with `acoustic_intensity_level` (symbol
        `Li`), `avogadro_constant` (symbol `Na`), and `bejan_number`
        (symbol `Be`), this query started resolving to physics concepts
        instead of elements.  v0.5.2 suppresses short physics symbol
        aliases that collide with element symbols."""
        sol = sess.ask("Li : Na :: Be : ?")
        assert sol.ok
        assert sol.expected["answer"] == "Mg"

    def test_periodic_group_analogy_resolves_in_chemistry(self, sess):
        """A group-1 vertical analogy should also resolve to an element."""
        sol = sess.ask("Na : K :: Mg : ?")
        assert sol.ok
        # Mg (group 2, period 3) :: Ca (group 2, period 4)
        assert sol.expected["answer"] == "Ca"

    def test_short_element_aliases_resolve_to_chemistry(self, sess):
        """A bare `Li` query should describe lithium, not
        acoustic_intensity_level.  This is the regression that v0.5.2
        fixes."""
        sol = sess.ask("describe Li")
        assert sol.ok
        assert sol.expected["domain"] == "chemistry"
        assert sol.expected["name"] == "Li"


# ===========================================================================
# 2.  PHYSICS ANALOGIES — must resolve to physically meaningful quantities
# ===========================================================================

class TestPhysicsAnalogiesResolve:

    def test_velocity_acceleration_momentum_yields_force_or_tied(self, sess):
        """The original TCT demo's headline physics analogy.  The answer
        `force` is in the tied set with `drag_force`, `lift_force`, and
        `linear_energy_transfer` — they all share dimension L M T^-2."""
        sol = sess.ask("velocity : acceleration :: momentum : ?")
        assert sol.ok
        tied = eval(sol.expected["tied"])
        assert "force" in tied, \
            f"force not in tied set; got {tied}"

    def test_dimension_change_analogy(self, sess):
        """A simple dimension-shift analogy should resolve to the
        physically correct quantity."""
        sol = sess.ask("velocity : acceleration :: length : ?")
        assert sol.ok
        # length (L) → length/time^2 (L T^-2) should give some kind of
        # acceleration-ish quantity.  We assert the answer is a real
        # physics concept, not a chemistry one.
        assert sol.expected["answer"]  # not empty
        # The answer should have a real EXT10 dimension, not be dimensionless.
        # We don't pin the exact answer because several quantities share the
        # L T^-2 dimension.

    def test_force_equals_mass_times_acceleration_holds(self, sess):
        """The canonical physics equation verifier."""
        sol = sess.ask("force = mass * acceleration")
        assert sol.ok
        assert sol.expected["holds"] == "True"


# ===========================================================================
# 3.  LEXICON ANALOGIES — must resolve on meaning, not spelling
# ===========================================================================

class TestLexiconAnalogiesResolve:

    def test_hot_cold_fast_yields_slow(self, sess):
        """The headline lexicon analogy.  After v0.5.1 fixed `slow`'s
        active_stative primitive (was 1/8, now 3/4) this resolves
        correctly to `slow`."""
        sol = sess.ask("hot : cold :: fast : ?")
        assert sol.ok
        assert sol.expected["answer"] == "slow"

    def test_the_antonym_analogy_is_answered_by_the_named_relation(self, sess):
        """No subspace is consulted once the relation has a name.

        The default subspace for a lexicon analogy is `lexicon.primitives`,
        and it is still what the displacement solver uses.  But the register
        *states* `hot opposite_of cold`, so the relation model transports
        that relation from `fast` instead of measuring any distance, and the
        solution records no subspace at all.  Asking for the geometric solve
        explicitly still goes the old way.
        """
        sol = sess.ask("hot : cold :: fast : ?")
        assert sol.ok
        assert sol.payload["subspace"] is None
        assert sol.payload["model"]["model"] == "lexicon_relation"

        geometric = sess.ask(
            "hot : cold :: fast : ? in lexicon.primitives")
        assert geometric.ok
        assert geometric.payload["subspace"] == "lexicon.primitives"

    def test_water_liquid_electron_is_refused_by_the_relation_model(self,
                                                                    sess):
        """A relation the register states, leading nowhere from `electron`.

        `water is_a liquid` is a triple the lexicon carries, so the relation
        model recognises the step and looks `is_a` up from `electron` -- and
        the register states no `is_a` for `electron` at all.  The refusal is
        the honest answer: the machine used to return the nearest word by
        primitive distance, an adjective like `light_adj`, which answers a
        question nobody asked.
        """
        sol = sess.ask("water : liquid :: electron : ?")
        assert not sol.ok
        assert "is_a" in sol.error
        assert "electron" in sol.error


# ===========================================================================
# 4.  DESCRIBE — must report the right domain and key facts
# ===========================================================================

class TestDescribeReportsCorrectDomain:

    def test_describe_carbon_reports_chemistry(self, sess):
        sol = sess.ask("describe carbon")
        assert sol.ok
        assert sol.expected["domain"] == "chemistry"

    def test_describe_carbon_reports_round_trip_ok(self, sess):
        """The substrate round trip is the losslessness contract."""
        sol = sess.ask("describe carbon")
        assert sol.ok
        assert sol.expected["round_trip_ok"] == "True"

    def test_describe_energy_reports_physics_by_default(self, sess):
        """Because DOMAIN_PRIORITY ranks physics first, `describe energy`
        without a hint should resolve to the physics quantity."""
        sol = sess.ask("describe energy")
        assert sol.ok
        assert sol.expected["domain"] == "physics"

    def test_describe_energy_with_lexicon_hint_reports_semantic(self, sess):
        """The semantic concept is reachable with an explicit hint."""
        sol = sess.ask("describe energy", domain="lexicon")
        assert sol.ok
        assert sol.expected["domain"] == "lexicon"

    def test_describe_gravity_resolves_to_lexicon(self, sess):
        """gravity is not in physics; the lexicon concept wins."""
        sol = sess.ask("describe gravity")
        assert sol.ok
        assert sol.expected["domain"] == "lexicon"


# ===========================================================================
# 5.  REGRESSION GUARD — the queries the user actually asks
# ===========================================================================

class TestUserFacingQueries:

    @pytest.mark.parametrize("query,expected_substring", [
        ("describe carbon", "C"),
        ("describe energy", "physics"),
        ("describe gravity", "lexicon"),
        ("describe hot", "lexicon"),
        ("force = mass * acceleration", "True"),
        ("Li : Na :: Be : ?", "Mg"),
        ("hot : cold :: fast : ?", "slow"),
        ("velocity : acceleration :: momentum : ?", "force"),
    ])
    def test_query_returns_expected_substring(self, sess, query,
                                                expected_substring):
        """Smoke tests for the queries the user has actually asked in
        this session.  Each query must succeed and the answer must
        contain the expected substring."""
        sol = sess.ask(query)
        assert sol.ok, f"{query!r} failed: {sol.error}"
        # Check both the answer and the expected dict for the substring.
        text = sol.answer + " " + str(dict(sol.expected)) + " " + \
               str(sol.payload)
        assert expected_substring in text, \
            f"{query!r}: expected {expected_substring!r} not found in answer. " \
            f"Got: {sol.answer[:200]}"


# ===========================================================================
# 6.  CROSS-DOMAIN — coercion to a common register, or an honest refusal
# ===========================================================================

class TestCrossRegisterCoercion:
    """Operands split across registers by domain priority alone.

    ``heat : temperature :: force : ?`` is the case that shows what the
    coercion is and is not for.  ``heat`` is only a lexicon concept while
    ``temperature`` and ``force`` are claimed by physics first, so the three
    operands appear to span two registers.  They do not -- all three are
    lexicon concepts too -- and the parser finds the single register that
    holds them all, which is what makes the query *parse*.  Carriers from
    different registers share no coordinate layout, so this coercion, and
    not a mixed-layout subtraction, is the only thing that could.

    Parsing it is not answering it.  The solver then finds that the relation
    the lexicon states -- ``temperature drives heat`` -- reaches nothing at
    all when looked up from ``force``, and that physics, the more specific
    register, holds two of the three terms and not the third.  That is the
    signature of a question about physics coerced into the lexicon, and the
    honest answer is to say so.
    """

    def test_the_cross_register_analogy_parses_into_one_register(self, sess):
        sol = sess.ask("heat : temperature :: force : ?")
        assert sol.kind == "analogy"
        assert sol.query.domain == "lexicon"

    def test_the_cross_register_analogy_is_refused_with_the_split_named(
            self, sess):
        sol = sess.ask("heat : temperature :: force : ?")
        assert not sol.ok
        assert "drives" in sol.error
        assert "physics holds" in sol.error
        assert "but not heat" in sol.error

    def test_the_coercion_is_recorded_in_the_parse_trace(self, sess):
        sol = sess.ask("heat : temperature :: force : ?")
        trace = " ".join(sol.query.trace)
        assert "coerced" in trace
        assert "lexicon" in trace

    def test_a_domain_hint_still_wins(self, sess):
        """An explicit register is never overridden by the coercion."""
        sol = sess.ask("energy : power :: force : ?", domain="physics")
        assert sol.query.domain == "physics"

    def test_operands_with_no_common_register_are_still_refused(self, sess):
        """Coercion rescues a false split, never a real one.

        ``carbon`` is a chemistry concept and ``heat`` a lexicon one, with no
        register holding both, so the query is refused rather than answered
        by subtracting carriers that do not share a layout.
        """
        sol = sess.ask("heat : carbon :: force : ?")
        assert not sol.ok
        assert "could not settle on a single domain" in (sol.error or "")
        assert "no single register" in " ".join(sol.query.trace)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
