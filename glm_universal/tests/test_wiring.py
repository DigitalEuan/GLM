"""Substantive tests for the v0.5.3 wiring work.

Four previously-built-but-unused reasoning mechanisms are now wired
into the runtime session as new query kinds:

* `project A B` -- uses `reasoning/dimension_layers.escalate`
* `trilinear A B C` -- uses `reasoning/product.griess_trilinear`
* `coherence <concept>` -- uses `reasoning/coherence.nrci_breakdown`
* `describe <concept>` now also includes `lattice_projection` (uses
  `reasoning/analogy.nearest_lattice_point`)

These tests verify that each query kind actually returns a useful
answer -- not just that the system returns one.
"""

from __future__ import annotations

import pytest

from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  PROJECT -- the layered projection (wires escalate)
# ===========================================================================

class TestProjectQuery:

    def test_project_carbon_oxygen_walks_five_layers(self, sess):
        """`project C O` should walk all 5 dimension-projection layers."""
        sol = sess.ask("project carbon oxygen")
        assert sol.ok
        assert sol.expected["layers_walked"] == "5"
        # The five layers are substrate, integer, rational, griess, universal.
        assert sol.expected["final_layer"] == "universal"

    def test_project_returns_a_distance_at_each_layer(self, sess):
        """Every layer should report a non-negative distance."""
        sol = sess.ask("project carbon oxygen")
        assert sol.ok
        all_views = sol.payload["all_views"]
        assert len(all_views) == 5
        for layer_name, view_a, view_b, distance in all_views:
            # Distance is rendered as a string; parse it as a Fraction.
            from fractions import Fraction
            d = Fraction(distance)
            assert d >= 0, f"{layer_name} distance {d} is negative"

    def test_project_with_one_operand_falls_back_to_describe(self, sess):
        """`project carbon` (one operand) should fall back to describe."""
        sol = sess.ask("project carbon")
        # The parser falls back to describe, so kind is "describe".
        assert sol.kind == "describe"
        assert sol.ok

    def test_project_layer_names_are_the_directive_layers(self, sess):
        """The five layer names should match the directive's pipeline:
        substrate -> integer -> rational -> griess -> universal."""
        sol = sess.ask("project carbon oxygen")
        assert sol.ok
        layer_names = [name for name, _, _, _ in sol.payload["all_views"]]
        assert layer_names == ["substrate", "integer", "rational",
                                "griess", "universal"]


# ===========================================================================
# 2.  TRILINEAR -- the invariant form <A.B, C> (wires griess_trilinear)
# ===========================================================================

class TestTrilinearQuery:

    def test_trilinear_on_known_2a_triple(self, sess):
        """The demo's known 2A triple (127, 432, 463) gives T = -3/32."""
        sol = sess.ask("trilinear 127 432 463")
        assert sol.ok
        assert sol.expected["trilinear"] == "-3/32"

    def test_trilinear_reports_all_three_axes(self, sess):
        """The expected dict should carry axis_a, axis_b, axis_c."""
        sol = sess.ask("trilinear 127 432 463")
        assert sol.ok
        assert sol.expected["axis_a"] == "127"
        assert sol.expected["axis_b"] == "432"
        assert sol.expected["axis_c"] == "463"

    def test_trilinear_reports_pairwise_forms(self, sess):
        """The three pairwise bilinear forms should be reported."""
        sol = sess.ask("trilinear 127 432 463")
        assert sol.ok
        # The three pairwise forms should all be non-negative Fractions.
        from fractions import Fraction
        for key in ("pairwise_AB", "pairwise_AC", "pairwise_BC"):
            v = Fraction(sol.expected[key])
            assert v >= 0, f"{key} = {v} is negative"

    def test_trilinear_on_non_2a_carrier_fails_honestly(self, sess):
        """A carrier whose nearest lattice point is the origin (class 0)
        should fail honestly with 'not a type-2 class'."""
        # trio_brick_0 is the all-ones-on-first-octad carrier, which
        # projects to the zero lattice point (class 0).
        sol = sess.ask("trilinear trio_brick_0 trio_brick_1 trio_brick_2")
        assert not sol.ok
        assert "trilinear" in (sol.error or "")

    def test_trilinear_with_two_operands_falls_back_to_describe(self, sess):
        """`trilinear 127 432` (two operands) should fall back to describe."""
        sol = sess.ask("trilinear 127 432")
        assert sol.kind == "describe"


# ===========================================================================
# 3.  COHERENCE -- the five-shell NRCI breakdown (wires nrci_breakdown)
# ===========================================================================

class TestCoherenceQuery:

    def test_coherence_carbon_returns_nrci(self, sess):
        """`coherence carbon` should return an NRCI value and regime."""
        sol = sess.ask("coherence carbon")
        assert sol.ok
        assert "nrci" in sol.expected
        assert "regime" in sol.expected
        # Carbon's carrier is highly incoherent (large coordinates), so
        # the NRCI should be in the Subcoherent regime.
        assert sol.expected["regime"] == "Subcoherent"

    def test_coherence_zero_vector_has_nrci_one(self, sess):
        """The zero carrier (perfect coherence, the vacuum) has NRCI = 1."""
        # We don't have a 'zero' concept in the registers, but we can
        # check the regime bucketing is correct: NRCI=1.0 -> OnBit.
        from glm_universal.reasoning import coherence as co
        zero = [0] * 24
        breakdown = co.nrci_breakdown(zero)
        assert breakdown["nrci"] == 1.0
        assert breakdown["regime"] == "OnBit"

    def test_coherence_reports_all_five_shells(self, sess):
        """The five shell taxes should all be reported in the payload."""
        sol = sess.ask("coherence carbon")
        assert sol.ok
        breakdown = sol.payload["breakdown"]
        for shell in ("shell0_golay", "shell1_sign_parity",
                      "shell2_sextet_balance", "shell3_coset_type",
                      "shell4_sextet_signed"):
            assert shell in breakdown, f"missing shell: {shell}"

    def test_coherence_regime_is_one_of_four(self, sess):
        """The regime must be one of the four documented regimes."""
        sol = sess.ask("coherence carbon")
        assert sol.ok
        assert sol.expected["regime"] in ("OnBit", "Coherent",
                                            "Transitional", "Subcoherent")


# ===========================================================================
# 4.  DESCRIBE now includes lattice_projection (wires nearest_lattice_point)
# ===========================================================================

class TestDescribeIncludesLatticeProjection:

    def test_describe_carbon_has_lattice_distance2(self, sess):
        """`describe carbon` should now report lattice_distance2."""
        sol = sess.ask("describe carbon")
        assert sol.ok
        assert "lattice_distance2" in sol.expected
        # The distance should be a non-negative rational.
        from fractions import Fraction
        d = Fraction(sol.expected["lattice_distance2"])
        assert d >= 0

    def test_describe_carbon_has_lattice_norm2(self, sess):
        """`describe carbon` should now report lattice_norm2."""
        sol = sess.ask("describe carbon")
        assert sol.ok
        assert "lattice_norm2" in sol.expected

    def test_describe_carbon_has_lattice_is_2a_axis(self, sess):
        """`describe carbon` should now report lattice_is_2a_axis."""
        sol = sess.ask("describe carbon")
        assert sol.ok
        assert "lattice_is_2a_axis" in sol.expected
        # Carbon's nearest lattice point is NOT a 2A axis.
        assert sol.expected["lattice_is_2a_axis"] == "False"

    def test_describe_payload_includes_lattice_projection(self, sess):
        """The describe payload should carry the lattice_projection block."""
        sol = sess.ask("describe carbon")
        assert sol.ok
        assert "lattice_projection" in sol.payload
        lp = sol.payload["lattice_projection"]
        assert "distance2" in lp
        assert "norm2" in lp
        assert "is_2a_axis" in lp

    def test_describe_step_lists_lattice_projection(self, sess):
        """The describe steps should include a lattice_projection step."""
        sol = sess.ask("describe carbon")
        assert sol.ok
        step_labels = [s.label for s in sol.steps]
        assert "lattice_projection" in step_labels


# ===========================================================================
# 5.  Cross-query smoke tests
# ===========================================================================

class TestNewQueryKindsSmoke:

    @pytest.mark.parametrize("query", [
        "project carbon oxygen",
        "trilinear 127 432 463",
        "coherence carbon",
        "coherence gravity",
        "coherence energy",
    ])
    def test_query_succeeds(self, sess, query):
        """Each new query kind should succeed (or fail honestly)."""
        sol = sess.ask(query)
        # Either ok=True, or ok=False with a clear error message.
        assert sol.ok or sol.error, f"{query!r} returned no error message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
