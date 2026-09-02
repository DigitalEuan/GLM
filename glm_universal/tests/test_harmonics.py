"""Tests for the harmonic register and the harmony study.

``data_objects/harmonics.py`` holds 28 musical intervals as exact rational
frequency ratios; ``reasoning/harmony.py`` asks whether the catalogue's claim
-- that chemical equilibria, musical harmony and market price discovery all
map to proximity in the Leech lattice -- survives being run.

What the tests below pin is that nothing here is approximate and nothing is
flattering.  Every coordinate is decided by integer comparison rather than by a
logarithm; the codec's round trip reads the ratio back from two coordinates so
that it cannot disagree with the derivation; and the study's verdict is held to
its own control, so that a "confirmed" would have to beat the same distance
measured *before* the lattice decoder was applied.  At present it does not, and
the recorded verdict is ``not reproduced`` -- that is asserted here, so that a
later change which quietly upgrades it has to change this file too.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.data_objects import harmonics as hm
from glm_universal.reasoning import harmony as hy


@pytest.fixture(scope="module")
def report():
    return hy.harmony_report()


@pytest.fixture(scope="module")
def sess():
    from glm_universal.runtime.session import GeometricSession
    return GeometricSession()


# ===========================================================================
# 1.  THE REGISTER
# ===========================================================================

class TestRegister:

    def test_the_register_holds_twenty_eight_intervals(self):
        assert len(hm.interval_register()) == 28
        assert (len(hm.JUST_INTERVALS) + len(hm.SEPTIMAL_INTERVALS)
                + len(hm.COMMAS)) == 28

    def test_names_are_unique(self):
        names = [i.name for i in hm.interval_register()]
        assert len(set(names)) == len(names)

    def test_every_ratio_is_an_exact_fraction(self):
        for interval in hm.interval_register():
            assert isinstance(interval.ratio, Fraction)
            assert not isinstance(interval.ratio.numerator, float)
            assert interval.ratio > 0

    def test_no_coordinate_is_a_float(self):
        for interval in hm.interval_register():
            for coordinate in interval.carrier():
                assert type(coordinate) in (int, Fraction)

    def test_every_carrier_has_twenty_four_coordinates(self):
        assert len(hm.HARMONIC_LAYOUT) == 24
        for interval in hm.interval_register():
            assert len(interval.carrier()) == 24

    def test_a_float_ratio_is_refused(self):
        with pytest.raises(TypeError):
            hm.Interval("bad", 1.5)          # type: ignore[arg-type]

    def test_a_non_positive_ratio_is_refused(self):
        with pytest.raises(ValueError):
            hm.Interval("bad", Fraction(-3, 2))

    def test_interval_by_name_finds_and_misses(self):
        assert hm.interval_by_name("perfect_fifth").ratio == Fraction(3, 2)
        with pytest.raises(KeyError):
            hm.interval_by_name("no_such_interval")

    def test_the_summary_counts_what_the_register_holds(self):
        summary = hm.register_summary()
        assert summary["count"] == 28
        assert summary["just"] == len(hm.JUST_INTERVALS)
        assert summary["septimal"] == len(hm.SEPTIMAL_INTERVALS)
        assert summary["commas"] == len(hm.COMMAS)
        # 1 is the unison's; 2 belongs to the octave, whose only prime is 2.
        assert summary["prime_limits"] == (1, 2, 3, 5, 7)

    def test_the_septimal_intervals_are_the_seven_limit_ones(self):
        for interval in hm.SEPTIMAL_INTERVALS:
            assert interval.prime_limit == 7

    def test_superparticular_intervals_are_n_over_n_minus_one(self):
        for name in hm.register_summary()["superparticular"]:
            ratio = hm.interval_by_name(name).ratio
            assert ratio.numerator == ratio.denominator + 1

    def test_harmonic_objects_are_carriers_in_their_own_domain(self):
        objects = hm.harmonic_objects()
        assert len(objects) == 28
        for obj in objects:
            assert obj.domain == "harmonics"
            assert len(obj.carrier) == 24
            assert obj.layout == hm.HARMONIC_LAYOUT

    def test_the_register_is_reachable_from_the_package(self):
        from glm_universal import data_objects as do
        assert len(do.all_objects()["harmonics"]) == 28
        assert do.interval_by_name("octave").ratio == Fraction(2)


# ===========================================================================
# 2.  ARITHMETIC ON A RATIO, DECIDED EXACTLY
# ===========================================================================

class TestExactArithmetic:

    @pytest.mark.parametrize("ratio,expected", [
        (Fraction(1), {}),
        (Fraction(2), {2: 1}),
        (Fraction(3, 2), {2: -1, 3: 1}),
        (Fraction(5, 4), {2: -2, 5: 1}),
        (Fraction(81, 80), {2: -4, 3: 4, 5: -1}),
        (Fraction(7, 4), {2: -2, 7: 1}),
    ])
    def test_prime_exponents(self, ratio, expected):
        assert hm.prime_exponents(ratio) == expected

    def test_prime_exponents_reports_primes_beyond_the_layout(self):
        assert hm.prime_exponents(Fraction(11, 8)) == {2: -3, 11: 1}

    def test_prime_exponents_refuses_a_non_positive_ratio(self):
        with pytest.raises(ValueError):
            hm.prime_exponents(Fraction(0))

    @pytest.mark.parametrize("ratio,gradus", [
        (Fraction(1), 1),
        (Fraction(2), 2),
        (Fraction(3, 2), 4),
        (Fraction(5, 4), 7),
        (Fraction(4, 3), 5),
    ])
    def test_euler_gradus(self, ratio, gradus):
        assert hm.euler_gradus(ratio) == gradus

    def test_product_complexity_is_n_times_d(self):
        assert hm.product_complexity(Fraction(45, 32)) == 45 * 32

    @pytest.mark.parametrize("ratio,step", [
        (Fraction(1), 0),
        (Fraction(2), 12),
        (Fraction(3, 2), 7),
        (Fraction(4, 3), 5),
        (Fraction(5, 4), 4),
        (Fraction(6, 5), 3),
        (Fraction(7, 4), 10),
        (Fraction(81, 80), 0),
        (Fraction(531441, 524288), 0),
    ])
    def test_tet_step_is_the_nearest_equal_step(self, ratio, step):
        assert hm.tet_step(ratio) == step

    def test_tet_step_brackets_its_answer_in_integers(self):
        """The defining inequality, checked as integers for every interval."""
        for interval in hm.interval_register():
            ratio = interval.ratio
            k = hm.tet_step(ratio)
            power = ratio ** 24
            assert Fraction(2) ** (2 * k - 1) <= power
            assert power < Fraction(2) ** (2 * k + 1)

    def test_tet_step_refuses_a_non_positive_ratio(self):
        with pytest.raises(ValueError):
            hm.tet_step(Fraction(0))

    def test_only_powers_of_two_are_tempered_exactly(self):
        for interval in hm.interval_register():
            tempered = hm.tet_error(interval.ratio) == 1
            assert tempered == (interval.ratio in (Fraction(1), Fraction(2)))

    def test_the_fifth_misses_by_the_pythagorean_comma(self):
        # (3/2)^12 / 2^7 is the Pythagorean comma, exactly.
        assert hm.tet_error(Fraction(3, 2)) == Fraction(531441, 524288)

    def test_the_major_third_misses_by_this_exact_amount(self):
        assert hm.tet_error(Fraction(5, 4)) == Fraction(244140625, 268435456)

    def test_a_comma_is_an_interval_the_unison_swallows(self):
        for interval in hm.COMMAS:
            assert interval.is_comma
            assert hm.tet_step(interval.ratio) == 0
        assert not hm.interval_by_name("perfect_fifth").is_comma
        assert not hm.interval_by_name("unison").is_comma


# ===========================================================================
# 3.  THE CODEC
# ===========================================================================

class TestCodec:

    def test_every_interval_round_trips(self):
        codec = hm.IntervalCodec()
        for interval in hm.interval_register():
            carrier = codec.encode(interval)
            back = codec.decode(carrier, name=interval.name)
            assert back == interval

    def test_the_round_trip_uses_only_the_two_stored_coordinates(self):
        """Corrupting a derived coordinate cannot change what is read back."""
        codec = hm.IntervalCodec()
        interval = hm.interval_by_name("major_third")
        carrier = list(codec.encode(interval))
        carrier[9] = 999            # euler_gradus, derived
        carrier[10] = -5            # tet_step, derived
        back = codec.decode(carrier, name="major_third")
        assert back.ratio == Fraction(5, 4)

    def test_the_object_round_trips_through_the_substrate(self):
        for obj in hm.harmonic_objects():
            assert obj.round_trip_ok()


# ===========================================================================
# 4.  TEMPERAMENT
# ===========================================================================

class TestTemperament:

    def test_the_table_has_a_row_per_interval(self, report):
        rows = report["temperament"]["rows"]
        assert len(rows) == 28
        assert {r["name"] for r in rows} == {i.name for i in
                                             hm.interval_register()}

    def test_only_the_unison_and_the_octave_are_tempered_exactly(self, report):
        assert set(report["temperament"]["tempered_exactly"]) == {"unison",
                                                                  "octave"}

    def test_the_reported_fifth_and_third_errors_are_exact(self, report):
        assert report["temperament"]["fifth_error"] == Fraction(531441,
                                                                524288)
        assert report["temperament"]["third_error"] == Fraction(244140625,
                                                                268435456)

    def test_the_worst_and_best_missed_are_scale_tones(self, report):
        worst = hm.interval_by_name(report["temperament"]["worst_missed"])
        best = hm.interval_by_name(report["temperament"]["best_missed"])
        for interval in (worst, best):
            assert not interval.is_comma
            assert Fraction(1) <= interval.ratio <= Fraction(2)

    def test_the_error_magnitude_is_symmetric(self):
        sharp = hy._error_magnitude(Fraction(3, 2))
        flat = hy._error_magnitude(Fraction(2, 3))
        assert sharp == flat == Fraction(3, 2)


# ===========================================================================
# 5.  THE FIFTH NEVER CLOSES
# ===========================================================================

class TestClosure:

    def test_no_stack_of_fifths_is_a_stack_of_octaves(self, report):
        closure = report["closure"]
        assert closure["closes"] is False
        assert closure["closures"] == ()
        assert closure["bound"] == 200

    def test_the_twelve_fifth_residue_is_the_pythagorean_comma(self, report):
        closure = report["closure"]
        assert (closure["twelve_fifths_over_seven_octaves"]
                == Fraction(531441, 524288))

    def test_four_fifths_miss_the_major_third_by_the_syntonic_comma(self,
                                                                   report):
        closure = report["closure"]
        assert closure["four_fifths_over_major_third"] == Fraction(81, 80)
        assert closure["syntonic_comma"] == Fraction(81, 80)

    def test_the_search_can_be_widened_and_still_finds_nothing(self):
        assert hy.fifth_never_closes(bound=40)["closures"] == ()

    def test_the_reason_it_cannot_close(self):
        """``(3/2)^n = 3^n / 2^n`` in lowest terms, and 3^n is never even."""
        for n in range(1, 60):
            ratio = Fraction(3, 2) ** n
            assert ratio.numerator == 3 ** n
            assert ratio.numerator % 2 == 1


# ===========================================================================
# 6.  TWO ORDERINGS OF CONSONANCE
# ===========================================================================

class TestConsonance:

    def test_kendall_tau_of_a_ranking_with_itself_is_one(self):
        assert hy.kendall_tau((1, 2, 3, 4), (1, 2, 3, 4)) == 1

    def test_kendall_tau_of_a_reversal_is_minus_one(self):
        assert hy.kendall_tau((1, 2, 3, 4), (4, 3, 2, 1)) == -1

    def test_kendall_tau_is_exact_and_rational(self):
        tau = hy.kendall_tau((1, 2, 3), (1, 3, 2))
        assert tau == Fraction(1, 3)
        assert isinstance(tau, Fraction)

    def test_ties_count_as_neither(self):
        assert hy.kendall_tau((1, 1, 1), (1, 2, 3)) == 0

    def test_kendall_tau_of_an_empty_or_single_ranking_is_zero(self):
        assert hy.kendall_tau((), ()) == 0
        assert hy.kendall_tau((5,), (7,)) == 0

    def test_kendall_tau_refuses_rankings_of_different_length(self):
        with pytest.raises(ValueError):
            hy.kendall_tau((1, 2), (1, 2, 3))

    def test_the_two_measures_agree_more_than_they_disagree(self, report):
        tau = report["consonance"]["tau"]
        assert isinstance(tau, Fraction)
        assert tau == Fraction(313, 378)
        assert tau > Fraction(1, 2)

    def test_they_do_not_agree_completely(self, report):
        """If they did, one of them would be redundant."""
        assert report["consonance"]["tau"] < 1

    def test_the_unison_is_simplest_on_both_measures(self, report):
        assert report["consonance"]["simplest_by_tenney"][0] == "unison"
        assert report["consonance"]["simplest_by_gradus"][0] == "unison"


# ===========================================================================
# 7.  THE LATTICE CLAIM, AND ITS CONTROL
# ===========================================================================

class TestLattice:

    def test_a_tuning_vector_is_the_exponents_and_nothing_else(self):
        vector = hy.tuning_vector(hm.interval_by_name("perfect_fifth"))
        assert vector[:4] == (-1, 1, 0, 0)
        assert set(vector[4:]) == {0}
        assert len(vector) == 24

    def test_the_unison_sits_at_the_origin(self):
        assert set(hy.tuning_vector(hm.interval_by_name("unison"))) == {0}

    def test_scaling_scales_the_vector(self):
        interval = hm.interval_by_name("major_third")
        assert (hy.tuning_vector(interval, 4)
                == tuple(4 * c for c in hy.tuning_vector(interval, 1)))

    def test_the_tuning_vector_is_not_the_register_carrier(self):
        """Deliberately so: the carrier holds consonance outright."""
        interval = hm.interval_by_name("major_third")
        assert tuple(hy.tuning_vector(interval)) != tuple(interval.carrier())

    def test_the_lattice_separates_every_interval_at_a_large_scale(self,
                                                                  report):
        separation = report["lattice"]
        assert separation["interval_count"] == 28
        assert separation["best_distinct"] == 28
        assert 8 in separation["fully_separated"]

    def test_a_small_scale_collapses_intervals_onto_the_unison(self, report):
        first = report["lattice"]["rows"][0]
        assert first["scale"] == 1
        assert first["distinct_points"] < 28

    def test_distance_from_the_unison_orders_the_intervals(self, report):
        separation = report["lattice"]
        assert separation["best_tau_tenney"] == Fraction(53, 63)
        assert separation["best_tau_gradus"] == Fraction(29, 42)
        assert separation["best_tau_tenney"] > Fraction(1, 2)

    def test_the_control_is_the_same_distance_without_the_lattice(self,
                                                                 report):
        control = report["lattice"]["control"]
        assert control["tau_tenney"] == Fraction(53, 63)
        assert control["distinct"] == 20

    def test_the_lattice_does_not_beat_its_control(self, report):
        """The finding.  Recorded rather than hidden."""
        separation = report["lattice"]
        assert separation["beats_control"] is False
        assert separation["best_tau_tenney"] == \
            separation["control"]["tau_tenney"]

    def test_the_decoder_reorders_no_pair_at_the_best_scale(self, report):
        assert report["lattice"]["best_reordered_pairs"] == 0

    def test_the_decoder_does_reorder_pairs_at_small_scales(self, report):
        """So the count is measuring something, not stuck at zero."""
        rows = report["lattice"]["rows"]
        assert any(r["reordered_pairs"] > 0 for r in rows)

    def test_every_reported_distance_is_an_integer(self, report):
        for row in report["lattice"]["rows"]:
            assert isinstance(row["max_distance2"], int)


# ===========================================================================
# 8.  THE VERDICT
# ===========================================================================

class TestVerdict:

    def test_the_claim_is_recorded_as_not_reproduced(self, report):
        verdict = report["verdict"]
        assert verdict["verdict"] == "not reproduced"
        assert verdict["separated"] is True
        assert verdict["ordered"] is True
        assert verdict["beats_control"] is False

    def test_the_reason_names_the_control(self, report):
        because = report["verdict"]["because"]
        assert "control" in because
        assert "prime-exponent" in because

    def test_the_claim_is_quoted_verbatim(self, report):
        assert report["verdict"]["claim"] == hy.CLAIM
        assert "Leech lattice" in hy.CLAIM

    def test_the_threshold_is_stated_rather_than_chosen_afterwards(self,
                                                                  report):
        assert report["verdict"]["threshold"] == Fraction(1, 2)

    def test_a_verdict_that_beat_its_control_would_be_confirmed(self):
        """The confirming branch is reachable -- it is simply not reached."""
        verdict = hy._verdict({
            "fully_separated": (8,),
            "best_tau_tenney": Fraction(9, 10),
            "best_tau_gradus": Fraction(1, 2),
            "best_reordered_pairs": 17,
            "control": {"tau_tenney": Fraction(1, 5),
                        "tau_gradus": Fraction(1, 5),
                        "distinct": 20},
            "beats_control": True,
        })
        assert verdict["verdict"] == "confirmed"

    def test_a_lattice_that_did_not_order_would_be_refuted(self):
        verdict = hy._verdict({
            "fully_separated": (8,),
            "best_tau_tenney": Fraction(1, 10),
            "best_tau_gradus": Fraction(1, 10),
            "best_reordered_pairs": 3,
            "control": {"tau_tenney": Fraction(0),
                        "tau_gradus": Fraction(0),
                        "distinct": 20},
            "beats_control": True,
        })
        assert verdict["verdict"] == "refuted"


# ===========================================================================
# 9.  THE REPORT AS A WHOLE
# ===========================================================================

class TestReport:

    def test_the_report_has_the_six_sections(self, report):
        assert set(report) == {"register", "temperament", "closure",
                               "consonance", "lattice", "verdict"}

    def test_no_float_appears_anywhere_in_the_report(self, report):
        def walk(value):
            if isinstance(value, float):
                raise AssertionError("a float reached the report")
            if isinstance(value, dict):
                for key, item in value.items():
                    walk(key)
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(report)

    @pytest.mark.exhaustive
    def test_the_report_is_deterministic(self):
        """Two independent computations agree.

        ``harmony_report`` is cached, so calling it twice would compare an
        object with itself.  ``__wrapped__`` is the uncached function, so this
        really does run the study twice.
        """
        first = hy.harmony_report.__wrapped__(bound=24)
        second = hy.harmony_report.__wrapped__(bound=24)
        assert first["verdict"] == second["verdict"]
        assert first["consonance"]["tau"] == second["consonance"]["tau"]

    def test_the_module_is_reachable_from_the_package(self):
        from glm_universal import reasoning as R
        assert R.harmony_report is hy.harmony_report
        assert R.harmony is hy


# ===========================================================================
# 10.  THE RUNTIME WIRING
# ===========================================================================

class TestRuntime:

    def test_the_register_is_a_domain_a_session_can_load(self, sess):
        from glm_universal.runtime.session import DOMAINS
        assert "harmonics" in DOMAINS
        assert len(sess.register("harmonics")) == 28

    def test_the_register_loads_lazily(self):
        from glm_universal.runtime.session import GeometricSession
        fresh = GeometricSession()
        assert "harmonics" not in fresh.loaded_domains()
        fresh.register("harmonics")
        assert "harmonics" in fresh.loaded_domains()

    def test_an_interval_can_be_described(self, sess):
        solution = sess.ask("describe perfect_fifth")
        assert "perfect_fifth" in solution.answer
        text = " ".join(step.language + " " + step.mathematics
                        for step in solution.steps)
        assert "531441/524288" in text
        assert "Harmony.lean" in text

    def test_the_octave_is_described_as_tempered_exactly(self, sess):
        text = " ".join(step.language + " " + step.mathematics
                        for step in sess.ask("describe octave").steps)
        assert "that step is the interval itself" in text

    def test_harmony_is_a_report_subject(self, sess):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "harmony" in REPORT_SUBJECTS
        assert sess.ask("report harmony").kind == "report"

    @pytest.mark.parametrize("surface", ["report music", "report tuning",
                                         "report temperament",
                                         "report consonance"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    def test_the_report_states_the_verdict(self, sess):
        answer = sess.ask("report harmony").answer
        assert "not reproduced" in answer
        assert "control" in answer

    @pytest.mark.exhaustive
    def test_the_generated_script_reproduces_column_two(self, sess):
        from glm_universal.runtime import tct_engine as tct
        trace = tct.verify_trace(tct.build_trace(sess.ask("report harmony")))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self, sess):
        import json
        json.dumps(sess.ask("report harmony").payload)

    def test_the_payload_holds_no_float(self, sess):
        """Every rational reaches the payload as an exact "n/d" string."""
        payload = sess.ask("report harmony").payload

        def walk(value):
            assert not isinstance(value, float)
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(payload)
