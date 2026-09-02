"""Tests for ``reasoning/name_coordinate`` -- a coordinate for the name.

``test_escalation.py`` pins the ceiling: 1,040 named entries sit on 757
distinct carriers, so 283 of them are beyond every layer, because a layer's
view is a function of the carrier.  This module pins what happens when the
missing coordinate is supplied, and the point of it is that only *part* of
that is a measurement.

* The code is exact and injective -- integer arithmetic on the entry's own
  name, no float, nothing stored beside the entry.  That is the admission
  rule, and it is checked rather than asserted.
* The exact code lifts the ceiling completely, from any layer at all.  That
  is *forced* (``GLM.Info.namedResolution_of_injective``), so the tests treat
  it as a consistency check on the instrument, not as a finding.
* The finding is the sweep and the control.  Reduced to ``b`` bits the
  ceiling returns, and how fast depends on which reduction is used: modulo a
  prime clears it at 16 bits, keeping the tail of the name never clears it at
  all.  Meanwhile the register label -- a coordinate of the same exactness,
  computed the same way -- recovers nothing, because every collision class
  lies inside one register.
* Every reading is a widening of the carrier reading, structurally -- the
  carrier is part of the key.  What is worth counting, and is counted over
  every row, is the admission rule itself: each coordinate is re-evaluated
  with the entries visited in the opposite order, so a "coordinate" that
  reads anything but its entry is caught.

The machine-checked counterparts are in
``RequestProject/GLM/NameCoordinate.lean``:
``namedLayer_refines_entryLayer`` (the widening),
``namedResolution_of_injective`` (the exact code),
``namedResolution_le_mul`` and ``card_le_of_codeInjOn`` (the bit floor) and
``namedResolution_eq_of_constant_on_classes`` (the control).
"""

from __future__ import annotations

import pytest

from glm_universal.reasoning import escalation as esc
from glm_universal.reasoning import name_coordinate as nc
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def entries():
    return esc.register_carriers()


@pytest.fixture(scope="module")
def report():
    return nc.name_report()


class TestTheCodeIsExactAndInjective:
    """The admission rule: computed from the entry, exactly, with no float."""

    def test_the_code_is_an_integer_of_the_name_alone(self):
        assert nc.name_code("volt") == int.from_bytes(b"\x01volt", "big")
        assert isinstance(nc.name_code("volt"), int)

    def test_the_leading_byte_separates_the_length_bands(self):
        """A name of L bytes lands in [256**L, 2*256**L), so lengths cannot
        collide -- which is why the prefix is there and not decoration."""
        for name in ("a", "ab", "abc", "a_much_longer_name"):
            length = len(name.encode("utf-8"))
            assert 256 ** length <= nc.name_code(name) < 2 * 256 ** length

    def test_it_is_injective_on_the_shipped_corpus(self, entries, report):
        names = [e.name for e in entries]
        codes = [nc.name_code(n) for n in names]
        assert report["code_injective_on_corpus"] is True
        assert len(set(codes)) == len(set(names)) == report["distinct_names"]

    def test_names_repeat_across_registers_but_not_at_a_carrier(self,
                                                                report):
        """1,019 distinct names under 1,040 entries: the code alone is not a
        key, and the reading is the pair (carrier, code)."""
        assert report["distinct_names"] == 1019
        assert report["entries"] == 1040
        assert report["exact"]["distinct"] == 1040

    def test_no_coordinate_is_a_float(self, entries, subtests):
        for kind in ("exact",) + nc.CONTROLS:
            coordinate = nc.coordinate_function(kind)
            with subtests.test(kind=kind):
                values = {coordinate(e) for e in entries[:200]}
                assert all(isinstance(v, (int, str)) for v in values)
                assert not any(isinstance(v, float) for v in values)


class TestTheReductions:
    """Two ways of spending ``b`` bits of one name, both exact."""

    def test_low_bits_is_the_tail_of_the_name(self):
        assert nc.low_bits_code("metre", 0) == 0
        assert nc.low_bits_code("metre", 8) == ord("e")
        assert nc.low_bits_code("candle", 8) == ord("e")

    def test_prime_mod_uses_the_largest_prime_below_the_bound(self):
        assert nc.largest_prime_below(16) == 13
        assert nc.largest_prime_below(128) == 127
        assert nc.largest_prime_below(1 << 16) == 65521
        assert (nc.prime_mod_code("metre", 16)
                == nc.name_code("metre") % 65521)

    def test_zero_and_one_bit_widths_are_the_constant_coordinate(self):
        assert nc.prime_mod_code("metre", 0) == 0
        assert nc.prime_mod_code("metre", 1) == 0
        assert nc.low_bits_code("metre", 0) == 0

    def test_negative_widths_are_refused(self):
        with pytest.raises(ValueError):
            nc.low_bits_code("metre", -1)
        with pytest.raises(ValueError):
            nc.prime_mod_code("metre", -1)

    def test_an_unknown_coordinate_is_refused(self):
        with pytest.raises(KeyError):
            nc.coordinate_function("vibes")


class TestTheExactCodeLiftsTheCeiling:
    """Forced rather than discovered -- checked as an instrument, not a find."""

    def test_the_ceiling_before(self, report):
        before = report["before"]
        assert before["distinct_carriers"] == 757
        assert before["unreachable"] == 283
        assert before["collision_classes"] == 104
        assert before["within_register"] == 104
        assert before["cross_register"] == 0
        assert before["largest_class_size"] == 78
        assert before["largest_class_register"] == "physics"

    def test_the_ceiling_after(self, report):
        exact = report["exact"]
        assert exact["distinct"] == exact["entries"] == 1040
        assert exact["unreachable"] == 0
        assert exact["recovered"] == 283
        assert exact["violations"] == 0

    def test_it_lifts_the_24_bit_substrate_too(self, report):
        """The coordinate does not need a good layer under it: the coarsest
        layer in the stack resolves everything once the name is beside it."""
        assert report["substrate_resolution"] == 415
        assert report["substrate_resolution_named"] == 1040


class TestTheBitSweep:
    """Where the measurement lives: how much of the name is needed."""

    def test_the_prime_reduction_clears_the_ceiling_at_sixteen_bits(self,
                                                                    report):
        assert report["sufficient_bits"]["prime_mod"] == 16
        by_width = {r["bits"]: r["unreachable"]
                    for r in report["sweeps"]["prime_mod"]}
        assert by_width == {0: 283, 4: 96, 7: 20, 8: 10, 10: 3, 12: 1,
                            14: 2, 16: 0, 20: 0, 24: 0}

    def test_the_sweep_is_not_monotone(self, report):
        """14 bits leaves two unreachable where 12 leaves one: the modulus is
        a different prime at each width, so a wider code is not a finer one."""
        by_width = {r["bits"]: r["unreachable"]
                    for r in report["sweeps"]["prime_mod"]}
        assert by_width[14] > by_width[12]

    def test_the_tail_reduction_never_clears_it(self, report):
        """Suffix families -- ``*_number``, ``*_constant`` -- agree in their
        last bytes however many of them are kept."""
        assert report["sufficient_bits"]["low_bits"] is None
        widths = report["sweeps"]["low_bits"]
        assert min(r["unreachable"] for r in widths) == 138
        assert widths[-1]["unreachable"] == 138

    def test_the_reduction_is_what_differs(self, report):
        """Same name, same width, same exactness: the mixing one is ahead at
        every width above zero, which is what makes the choice a measurement
        rather than a convention."""
        prime = {r["bits"]: r["unreachable"]
                 for r in report["sweeps"]["prime_mod"]}
        low = {r["bits"]: r["unreachable"]
               for r in report["sweeps"]["low_bits"]}
        assert prime[0] == low[0] == 283
        assert all(prime[b] < low[b] for b in nc.BIT_WIDTHS if b)

    def test_the_zero_bit_row_reproduces_the_bare_ceiling(self, report):
        for scheme in nc.SCHEMES:
            row = report["sweeps"][scheme][0]
            assert row["bits"] == 0
            assert row["unreachable"] == report["before"]["unreachable"]
            assert row["recovered"] == 0

    def test_the_pigeonhole_floor_is_below_the_measured_width(self, report):
        """A class of 78 at one carrier needs 78 codes, so seven bits are
        necessary; sixteen were sufficient.  The gap is the corpus's, not the
        theorem's -- ``GLM.Info.card_le_of_codeInjOn``."""
        assert report["forced_bits"] == 7
        assert 2 ** report["forced_bits"] >= 78
        assert 2 ** (report["forced_bits"] - 1) < 78
        assert report["forced_bits"] <= report["sufficient_bits"]["prime_mod"]

    def test_no_width_below_the_floor_clears_the_ceiling(self, report):
        for scheme in nc.SCHEMES:
            for row in report["sweeps"][scheme]:
                if row["bits"] < report["forced_bits"]:
                    assert row["unreachable"] > 0


class TestTheControls:
    """A coordinate is not informative merely by being exact."""

    def test_the_register_label_recovers_nothing(self, report):
        assert report["control_recovered"]["register"] == 0
        assert report["control_recovered"]["constant"] == 0

    def test_and_that_is_forced_by_where_the_classes_lie(self, report):
        """Every collision class is inside one register, so the register
        coordinate is constant on the classes; the Lean statement is
        ``namedResolution_eq_of_constant_on_classes``."""
        assert report["before"]["cross_register"] == 0
        assert (report["before"]["within_register"]
                == report["before"]["collision_classes"])

    def test_the_weak_controls_recover_part_and_not_all(self, report):
        recovered = report["control_recovered"]
        assert recovered["initial"] == 174
        assert recovered["length"] == 177
        for kind in ("initial", "length"):
            assert 0 < recovered[kind] < report["before"]["unreachable"]

    def test_the_name_beats_every_control(self, report):
        best_control = max(report["control_recovered"].values())
        assert report["exact"]["recovered"] > best_control


class TestEveryCoordinateIsAFunctionOfTheEntry:
    """The admission rule, enforced on every row rather than asserted."""

    def test_no_row_of_the_study_breaks_the_rule(self, report, subtests):
        rows = [report["exact"]]
        rows += report["controls"]
        for scheme in nc.SCHEMES:
            rows += report["sweeps"][scheme]
        assert len(rows) == 25
        for row in rows:
            with subtests.test(coordinate=row["coordinate"],
                               bits=row["bits"]):
                assert row["violations"] == 0
                assert row["recovered"] >= 0
                assert row["distinct"] >= report["before"]["distinct_carriers"]

    def test_resolution_never_falls_below_the_layers_own(self, entries):
        plain = esc.resolution_ceiling(entries)["distinct_carriers"]
        for kind in nc.CONTROLS:
            row = nc.control_row(entries, kind)
            assert row["distinct"] >= plain

    def test_a_coordinate_that_is_not_a_function_of_the_entry_is_caught(
            self, entries):
        """The zero above is not vacuous.  A 'coordinate' that reads the
        traversal rather than the entry disagrees with itself on the second
        pass, and the violation counter says so."""
        seen = {"i": 0}

        def by_position(entry):
            seen["i"] += 1
            return seen["i"] % 2

        row = nc.named_ceiling(entries[:100], by_position,
                               label="positional")
        assert row.violations > 0


class TestTheReportSubject:
    """``report names`` recomputes the study and its numbers survive."""

    def test_the_subject_is_listed_and_answers(self):
        from glm_universal.runtime import session as sess
        assert "names" in sess.REPORT_SUBJECTS
        solution = GeometricSession().ask("report names")
        assert solution.kind == "report"
        assert "283" in solution.answer
        assert "16 bits" in solution.answer

    def test_the_expected_column_matches_the_instrument(self, report):
        solution = GeometricSession().ask("report names")
        expected = solution.expected
        assert expected["entries"] == str(report["entries"])
        assert expected["exact_recovered"] == "283"
        assert expected["forced_bits"] == "7"
        assert expected["sufficient_bits_prime_mod"] == "16"
        assert expected["sufficient_bits_low_bits"] == "None"
        assert expected["control_recovered"] == (
            "constant:0,register:0,initial:174,length:177")
        assert expected["violations"] == "0"

    def test_the_aliases_reach_the_same_subject(self, subtests):
        session = GeometricSession()
        answer = session.ask("report names").answer
        for alias in ("report name coordinate", "report naming"):
            with subtests.test(alias=alias):
                assert session.ask(alias).answer == answer
