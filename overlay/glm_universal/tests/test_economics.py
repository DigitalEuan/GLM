"""Tests for the economic register -- the third of the universality claim.

The sentence under test is catalogue claim 6.2's economic half, ``market
price discovery maps to proximity in the Leech lattice``.  Five groups:

1. **Exactness** -- the magnitude bucket is computed by integer comparison
   alone, so it must satisfy its defining inequality on prices of any
   magnitude, including ones no float represents.  The machine-checked
   counterpart is ``RequestProject/GLM/LogBucket.lean``
   (``bucket_spec``, ``bucket_unique``, ``bucket_mono``, ``bucket_zpow``).
2. **The register** -- what the shipped CSV holds, counted here rather than
   quoted, together with the codec round trip.
3. **The geometry** -- price vectors, the scale sweep, and the separation the
   sweep reaches.
4. **The verdict** -- and, in particular, that it is *not reproduced* rather
   than confirmed, because the undecoded control does exactly as well.  A test
   that let this pass as a confirmation would be the failure mode the control
   exists to catch.
5. **The runtime surface** -- ``report economics`` solves, its column-3 script
   is float-free, and it reproduces column 2 in a fresh interpreter.
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.data_objects import economics_register as ER
from glm_universal.reasoning import catalog as CA
from glm_universal.reasoning import economics as EC
from glm_universal.runtime import session as SE
from glm_universal.runtime import tct_engine as TE


@pytest.fixture(scope="module")
def report():
    return EC.economics_report()


@pytest.fixture(scope="module")
def records():
    return ER.load_price_register()


class TestExactBucket:
    """``floor(log_base(p))`` by integer comparison, on any magnitude."""

    def test_the_defining_inequality_holds_on_the_register(self, records):
        for record in records:
            for base in (2, 10):
                k = ER.compute_exact_log_bucket(record.price, base)
                assert Fraction(base) ** k <= record.price
                assert record.price < Fraction(base) ** (k + 1)

    def test_powers_of_the_base_land_on_their_own_exponent(self):
        for base in (2, 3, 10):
            for k in range(-12, 13):
                assert ER.compute_exact_log_bucket(
                    Fraction(base) ** k, base) == k

    def test_magnitudes_no_float_reaches(self):
        huge = Fraction(10) ** 400 + Fraction(1, 3)
        tiny = Fraction(1, 10 ** 400) / 3
        assert ER.compute_exact_log_bucket(huge, 10) == 400
        assert ER.bucket_bounds_hold(huge, 10)
        assert ER.compute_exact_log_bucket(tiny, 10) == -401
        assert ER.bucket_bounds_hold(tiny, 10)

    def test_the_bucket_is_monotone(self, records):
        prices = sorted(r.price for r in records)
        buckets = [ER.compute_exact_log_bucket(p, 2) for p in prices]
        assert buckets == sorted(buckets)

    def test_scaling_by_a_power_of_the_base_shifts_the_bucket(self, records):
        for record in records:
            for shift in (-5, -1, 0, 1, 7):
                scaled = record.price * Fraction(2) ** shift
                assert (ER.compute_exact_log_bucket(scaled, 2)
                        == record.log_bucket(2) + shift)

    def test_a_non_positive_price_is_refused(self):
        for bad in (Fraction(0), Fraction(-1, 7)):
            with pytest.raises(ValueError):
                ER.compute_exact_log_bucket(bad, 2)

    def test_a_base_below_two_is_refused(self):
        for bad in (1, 0, -2, True):
            with pytest.raises(ValueError):
                ER.compute_exact_log_bucket(Fraction(3), bad)


class TestRegister:
    """What the shipped register holds, counted here."""

    def test_the_summary_is_what_the_rows_say(self, records, report):
        summary = report["register"]
        assert summary["records"] == len(records)
        assert summary["instruments"] == len(
            {r.identifier for r in records})
        assert summary["windows"] == len(ER.WINDOWS)
        assert summary["all_bounds_hold"] is True

    def test_every_instrument_has_every_window(self, records):
        for identifier in ER.instrument_identifiers():
            series = ER.instrument_series(identifier)
            assert tuple(r.observation_window for r in series) == ER.WINDOWS

    def test_keys_are_unique(self, records):
        keys = [r.key for r in records]
        assert len(set(keys)) == len(keys)

    def test_a_currency_pair_names_no_physical_denominator(self, records):
        for record in records:
            if record.is_dimensionless_currency:
                assert (record.denominator_physical_quantity
                        == ER.DIMENSIONLESS)
                assert all(e == 0 for e in record.exponents)

    def test_the_codec_round_trips_every_record(self, records):
        codec = ER.PriceCodec()
        for record in records:
            assert codec.decode(codec.encode(record)) == record

    def test_the_carrier_layout_is_twenty_four_named_coordinates(self):
        assert len(ER.ECONOMICS_LAYOUT) == 24
        assert len(set(ER.ECONOMICS_LAYOUT)) == 24

    def test_the_module_constructs_no_float(self):
        for module in (ER, EC):
            tree = ast.parse(
                Path(module.__file__).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                assert not (isinstance(node, ast.Constant)
                            and isinstance(node.value, float)), module.__name__
                assert not (isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Name)
                            and node.func.id == "float"), module.__name__


class TestGeometry:
    """Price vectors, the sweep, and what it separates."""

    def test_a_price_vector_is_exact_and_of_length_twenty_four(self, records):
        for record in records:
            vector = EC.price_vector(record, 8)
            assert len(vector) == 24
            assert all(isinstance(x, Fraction) for x in vector)

    def test_the_mantissa_lies_in_its_half_open_interval(self, records):
        for record in records:
            for base in (2, 10):
                mantissa = EC._mantissa(record.price, base)
                assert 1 <= mantissa < base

    def test_scaling_scales_the_vector(self, records):
        record = records[0]
        one = EC.price_vector(record, 1)
        eight = EC.price_vector(record, 8)
        assert tuple(8 * x for x in one) == eight

    def test_the_sweep_separates_at_the_reported_scale(self, report):
        separation = report["lattice"]
        assert separation["best_distinct"] == separation["record_count"]
        assert separation["best_scale"] in separation["fully_separated"]

    def test_a_scale_below_the_separating_one_conflates(self, report):
        separation = report["lattice"]
        low = [row for row in separation["rows"] if row["scale"] == 1]
        assert low and low[0]["distinct_points"] < separation["record_count"]

    def test_decoded_points_are_deterministic(self):
        assert EC.decoded_points(8) == EC.decoded_points(8)


class TestVerdict:
    """The control is what decides it, and it is not reproduced."""

    def test_proximity_does_track_the_market(self, report):
        verdict = report["verdict"]
        assert verdict["tracks_the_market"] is True
        assert verdict["best_comovement_rate"] > verdict["chance_rate"]

    def test_but_the_undecoded_control_does_just_as_well(self, report):
        verdict = report["verdict"]
        assert verdict["beats_control"] is False
        assert (verdict["control_comovement_rate"]
                >= verdict["best_comovement_rate"])

    def test_so_the_claim_is_recorded_as_not_reproduced(self, report):
        assert report["verdict"]["verdict"] == "not reproduced"
        assert "control" in report["verdict"]["because"]

    def test_the_catalogue_takes_its_verdict_from_the_module(self, report):
        entries = [c for c in CA.catalog_report()["claims"]
                   if c["section"] == "6.2" and "economic" in c["claim"]]
        assert len(entries) == 1
        assert entries[0]["verdict"] == report["verdict"]["verdict"]
        assert str(report["lattice"]["best_scale"]) in entries[0]["figure"]


class TestRuntime:
    """The report subject, and its column-3 script."""

    def test_report_economics_solves(self):
        solution = SE.GeometricSession().ask("report economics")
        assert solution.ok
        assert solution.expected["verdict"] == "not reproduced"
        assert solution.expected["beats_control"] == "False"

    def test_the_expected_block_agrees_with_the_module(self, report):
        solution = SE.GeometricSession().ask("report economics")
        assert solution.expected["records"] == str(
            report["register"]["records"])
        assert solution.expected["best_scale"] == str(
            report["lattice"]["best_scale"])

    def test_the_generated_script_is_float_free(self):
        session = SE.GeometricSession()
        script = TE.render_script(session.ask("report economics"))
        ok, offenders = TE.script_is_exact(script)
        assert ok, offenders

    def test_the_script_reproduces_column_two(self):
        session = SE.GeometricSession()
        trace = TE.verify_trace(TE.build_trace(session.ask("report economics")),
                                timeout=900)
        assert trace.verdict.executed, trace.verdict.stderr_tail
        assert trace.verdict.verified, trace.verdict.mismatches
