"""Tests for the capability probes: the map of what the machine can do.

The rest of this suite asks whether the mechanisms still behave as they did.
The probes in :mod:`glm_universal.capabilities` ask the other question -- *what
can the machine do at all, and where exactly does it stop?* -- and this module
pins their answers.

Three things are checked here, and they are different in kind.

1.  **The harness is honest.**  A probe that raises is reported as an error
    and never propagated; a verdict that differs from the declared expectation
    is surfaced as a *surprise* rather than buried.
2.  **The verdict table is stable.**  Every probe's verdict is pinned by name.
    A probe that starts holding where it broke is a capability won, and this
    test is where it must be acknowledged: the table is edited deliberately,
    not drifted into.
3.  **The boundaries are the ones claimed.**  For each break that is a
    *theorem* -- the Golay repair radius, undecidable equality, the convex
    hull of the code -- the underlying quantity is recomputed here, so the
    report cannot go stale against the code it describes.
"""

from __future__ import annotations

import pytest

from glm_universal import capabilities as cap
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return cap.capability_report()


@pytest.fixture(scope="module")
def by_name(report):
    return {str(result["name"]): result for result in report["results"]}


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


#: The verdict every probe is expected to return.  ``breaks`` is not a
#: failure: it is a boundary that has been located.  Entries marked
#: ``theorem`` cannot move; the others are the work list.
EXPECTED_VERDICTS = {
    # -- reals ----------------------------------------------------------
    "real_sqrt_to_arbitrary_precision": "holds",
    "real_transcendental_constants": "holds",
    "real_arithmetic_is_closed": "holds",
    "real_written_arithmetic": "holds",
    "real_tower_exposes_every_stand_in": "holds",
    "real_equality_is_decidable": "breaks",              # theorem
    "real_division_by_an_undecided_value": "breaks",     # theorem
    "real_value_as_carrier": "breaks",                   # theorem
    "real_surrogate_on_a_grid_point": "breaks",          # theorem
    "real_transcendental_functions": "holds",            # built in v1.2.0
    # -- the dynamic carrier --------------------------------------------
    "dynamic_one_dimensional_bound": "holds",
    "dynamic_resolution_grows_with_time": "holds",
    "dynamic_24d_reachable_target": "holds",
    "dynamic_24d_irrational_target": "holds",
    "dynamic_24d_arbitrary_target": "breaks",            # theorem
    "dynamic_repair_is_single_valued": "breaks",         # theorem
    # -- substrate, carriers, layers, algebra ---------------------------
    "substrate_repair_radius": "breaks",                 # theorem
    "carrier_unbounded_magnitude": "holds",
    "carrier_rejects_floats": "holds",
    "carrier_non_dyadic_denominator": "breaks",          # theorem
    "layers_form_a_refinement_chain": "holds",
    "layers_can_compute_addition": "breaks",             # theorem
    "tax_conservation_above_bits": "breaks",             # theorem
    "algebra_product_is_associative": "breaks",          # theorem
    # -- meaning and scale ----------------------------------------------
    "semantics_refuses_an_ambiguous_term": "holds",
    "semantics_open_vocabulary": "breaks",               # work item
    "scale_precision_has_no_ceiling": "holds",
    "scale_more_than_24_coordinates": "breaks",          # theorem
    # -- the running machine --------------------------------------------
    "runtime_answers_about_irrationals": "holds",
    "runtime_admits_what_it_cannot_parse": "holds",
    "runtime_orders_two_reals": "holds",
    "runtime_answer_reruns_itself": "holds",
    "runtime_arithmetic_inside_a_describe": "holds",
}


# ===========================================================================
# 1.  THE HARNESS
# ===========================================================================

class TestHarness:

    def test_every_registered_probe_is_declared_here(self):
        assert set(cap.probe_names()) == set(EXPECTED_VERDICTS)

    def test_the_two_probe_files_account_for_every_probe(self):
        declared = set(cap.ALL_PROBE_NAMES) | set(cap.LANGUAGE_PROBE_NAMES)
        assert declared == set(cap.probe_names())
        assert (len(cap.ALL_PROBE_NAMES) + len(cap.LANGUAGE_PROBE_NAMES)
                == len(cap.probe_names()))

    def test_each_probe_declares_a_known_area_and_expectation(self):
        for name in cap.probe_names():
            item = cap.get_probe(name)
            assert item.area in cap.AREAS
            assert item.expectation in ("holds", "breaks")
            assert item.question.endswith("?"), name

    def test_an_unknown_probe_is_named_in_the_error(self):
        with pytest.raises(KeyError):
            cap.get_probe("no_such_probe")

    def test_a_probe_that_raises_is_reported_not_propagated(self):
        broken = cap.Probe("temporary_broken_probe", "reals",
                           "Does a probe that raises get reported?", "holds",
                           lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        cap.register(broken)
        try:
            result = cap.run_probe("temporary_broken_probe")
        finally:
            cap.harness._REGISTRY.pop("temporary_broken_probe", None)
        assert result["verdict"] == "error"
        assert "boom" in str(result["boundary"])
        assert result["surprise"] is True

    def test_a_probe_must_name_a_known_area(self):
        with pytest.raises(ValueError):
            cap.Probe("x", "no such area", "Is it?", "holds", lambda: None)

    def test_a_probe_must_declare_holds_or_breaks(self):
        with pytest.raises(ValueError):
            cap.Probe("x", "reals", "Is it?", "maybe", lambda: None)


# ===========================================================================
# 2.  THE VERDICT TABLE
# ===========================================================================

class TestVerdicts:

    @pytest.mark.parametrize("name,verdict", sorted(EXPECTED_VERDICTS.items()))
    def test_probe_verdict_is_as_declared(self, by_name, name, verdict):
        assert by_name[name]["verdict"] == verdict, by_name[name]["boundary"]

    def test_no_probe_errored(self, report):
        assert report["errors"] == 0, report["error_names"]

    def test_no_probe_surprised_its_own_expectation(self, report):
        assert report["surprises"] == ()

    def test_every_break_states_where_it_stops(self, report):
        for boundary in report["boundaries"]:
            assert len(boundary["boundary"]) > 40, boundary["name"]

    def test_the_counts_add_up(self, report):
        assert (report["holds"] + report["breaks"] + report["errors"]
                == report["probes"] == len(EXPECTED_VERDICTS))

    def test_every_area_is_probed(self, report):
        assert set(report["by_area"]) == set(cap.AREAS)


# ===========================================================================
# 3.  THE BOUNDARIES THAT ARE THEOREMS
# ===========================================================================

class TestTheoremBoundaries:
    """Each of these is recomputed, so the report cannot go stale."""

    def test_the_repair_radius_is_three(self, by_name):
        from glm_universal.substrate import golay_decode as gd
        result = by_name["substrate_repair_radius"]
        assert "3" in result["boundary"]
        # weight 3 is corrected; weight 4 is a declared tie.
        assert gd.decode_complete(0b111).corrected == 0
        assert gd.decode_complete(0b1111).corrected is None

    def test_equality_of_processes_is_never_claimed(self, by_name):
        from fractions import Fraction

        from glm_universal.reasoning import exact_real as xr
        assert by_name["real_equality_is_decidable"]["verdict"] == "breaks"
        root2 = xr.sqrt(Fraction(2))
        assert xr.decide_equal(root2 * root2,
                               xr.from_fraction(Fraction(2)), 128) is None

    def test_the_unreachable_target_has_a_certificate(self, by_name):
        from fractions import Fraction

        from glm_universal.reasoning import exact_real as xr
        result = by_name["dynamic_24d_arbitrary_target"]
        assert result["verdict"] == "breaks"
        ramp = tuple(Fraction(i, 24) for i in range(24))
        certificate = xr.hull_certificate(ramp, 400)
        assert certificate["separates"] is True
        assert certificate["codewords_checked"] == 4096

    def test_the_algebra_is_not_associative(self, by_name):
        from glm_universal.reasoning import product as pr
        result = by_name["algebra_product_is_associative"]
        assert result["verdict"] == "breaks"
        first, second = pr.sample_two_a_pairs(1)[0]
        a, b, c = pr.two_a_subalgebra(first, second).labels
        x, y, z = pr.axis(a), pr.axis(b), pr.axis(c)
        assert (pr.algebra_product(pr.algebra_product(x, y), z)
                != pr.algebra_product(x, pr.algebra_product(y, z)))

    def test_the_twenty_fifth_coordinate_is_refused(self, by_name):
        from fractions import Fraction

        from glm_universal.reasoning import exact_real as xr
        assert by_name["scale_more_than_24_coordinates"]["verdict"] == "breaks"
        with pytest.raises(ValueError):
            xr.real_carrier([xr.sqrt(Fraction(2))] * 25, 8)


# ===========================================================================
# 4.  THE BOUNDARIES THAT ARE WORK ITEMS
# ===========================================================================

class TestWorkItems:
    """These *can* move, and the probe says exactly what would move each."""

    def test_transcendental_functions_are_built_and_the_inverses_are_not(
            self, by_name):
        from glm_universal.reasoning import real_expr as rx
        result = by_name["real_transcendental_functions"]
        assert result["verdict"] == "holds"
        # What was a work item in v1.1.0 now answers.
        for text in ("sin(1)", "log(2)", "2^pi"):
            assert len(rx.parse_expression(text).decimal(20)) > 0
        # What replaced it as the boundary: the inverse and hyperbolic family.
        for text in ("asin(1)", "atan(1)", "sinh(1)"):
            with pytest.raises(rx.ExpressionError):
                rx.parse_expression(text)

    def test_the_vocabulary_is_the_registers(self, by_name):
        from glm_universal.semantics import reference as rf
        result = by_name["semantics_open_vocabulary"]
        assert result["verdict"] == "breaks"
        assert rf.resolve("justice").meaning is None
        assert rf.resolve("energy").meaning is not None

    def test_a_dimensional_expression_can_now_be_described(self, by_name, sess):
        result = by_name["runtime_arithmetic_inside_a_describe"]
        assert result["verdict"] == "holds"
        assert sess.ask("what is energy").ok
        composed = sess.ask("what is energy divided by time")
        assert composed.ok, composed.error
        assert "L^2 M T^-3" in composed.answer
        assert "power" in composed.answer


# ===========================================================================
# 5.  THE RUNTIME WIRING
# ===========================================================================

class TestCapabilityQuery:

    def test_report_capabilities_answers(self, sess):
        solution = sess.ask("report capabilities")
        assert solution.ok, solution.error
        assert int(solution.expected["probes"]) == len(EXPECTED_VERDICTS)
        assert solution.expected["errors"] == "0"
        assert solution.expected["surprises"] == "()"

    def test_the_answer_names_where_the_machine_breaks(self, sess):
        solution = sess.ask("report capabilities")
        assert int(solution.expected["breaks"]) == sum(
            1 for verdict in EXPECTED_VERDICTS.values() if verdict == "breaks")

    @pytest.mark.exhaustive
    def test_the_third_column_reruns_the_probes(self, sess):
        trace = tct.verify_trace(tct.build_trace(sess.ask("report capabilities")))
        verdict = trace.verdict
        assert verdict is not None
        assert verdict.returncode == 0, verdict.stderr_tail
        assert verdict.matches_column2, verdict.mismatches


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
