"""Tests for the power-of-two norm family and the escalation over it.

Three things are under test:

* ``substrate/construction_ladder`` -- the key parser and the containment
  relation that now reach the whole generated family, not just the declared
  rungs;
* ``substrate/norm_family`` -- is the family really complete, is every rung's
  declared minimum norm and kissing number what its *generated* theta series
  says, and is the chain a chain?
* ``reasoning/norm_escalation`` -- the re-taken measurement, read from its
  cache, including the property the round cares about most: that a reading
  refuses rather than answering wrongly, and that the ladder which loses it is
  reported as a failure rather than kept.

Directive D7 -- no float anywhere -- is checked statically on both new
modules.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import ladder_escalation as LE
from glm_universal.reasoning import norm_escalation as NE
from glm_universal.substrate import construction_ladder as CL
from glm_universal.substrate import norm_family as NF


# ═════════════════════════════════════════════════════════════════════════
#  1.  Keys, generated on demand
# ═════════════════════════════════════════════════════════════════════════

class TestKeys:

    @pytest.mark.parametrize("key,expected", [
        ("Z", ("Z", 0)), ("2D", ("D", 1)), ("8C", ("C", 3)),
        ("A/2", ("A", -1)), ("4096Z", ("Z", 12)),
    ])
    def test_parse(self, key, expected):
        assert CL.parse_key(key) == expected

    @pytest.mark.parametrize("key", ["3Z", "B/2", "D/2", "X", "2X", "",
                                     "8192Z"])
    def test_not_a_rung(self, key):
        assert CL.parse_key(key) is None
        with pytest.raises(KeyError):
            CL.rung_spec(key)

    def test_a_generated_rung_knows_its_invariants(self):
        spec = CL.rung_spec("8C")
        base = CL.rung_spec("C")
        assert spec.base == "C" and spec.exponent == 3
        # Doubling three times multiplies the norm by 4^3 and the covolume by
        # 2^(24*3), and leaves the kissing number alone.
        assert spec.minimum_norm == base.minimum_norm * 64
        assert spec.covolume_log2 == base.covolume_log2 + 72
        assert spec.kissing == base.kissing

    def test_membership_of_a_generated_rung(self):
        point = tuple(8 * value for value in CL.sample_points("C")[0])
        assert CL.in_rung(point, "8C")
        assert not CL.in_rung(tuple(4 * v for v in CL.sample_points("C")[0]),
                              "8C")


# ═════════════════════════════════════════════════════════════════════════
#  2.  The family
# ═════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def family():
    return NF.norm_family_report()


class TestFamily:

    def test_the_scaling_rule_is_what_the_family_rests_on(self, family):
        rule = family["scaling_rule"]
        assert rule["norm_times_four"]
        assert rule["covolume_plus_24"]
        assert rule["kissing_unchanged"]

    def test_every_power_of_two_carries_a_rung(self, family):
        completeness = family["completeness"]
        assert completeness["complete"]
        assert completeness["gaps"] == ()
        assert completeness["norms"] == tuple(1 << p for p in range(12))

    def test_the_family_needs_more_than_one_construction(self, family):
        # A single construction scaled by powers of two visits every *other*
        # power of two, so no one base fills the family.
        for base in NF.FAMILY_BASES:
            norms = {CL.rung_spec(key).minimum_norm
                     for key in NF.family_rungs()
                     if CL.scale_of(key)[0] == base}
            assert not {1 << power for power in range(12)} <= norms, base
        assert len(family["completeness"]["bases_used_by_the_chain"]) > 1

    def test_declared_invariants_agree_with_the_generated_series(self, family):
        assert family["series_all_agree"]
        for row in family["rows"]:
            for entry in row["rungs"]:
                assert entry["series_reaches_minimum"], entry["rung"]
                assert entry["minimum_norm"] == row["norm"], entry["rung"]

    def test_the_densest_rung_at_norm_32_is_the_leech_lattice(self):
        assert NF.densest_at_norm(32) == "C"
        assert CL.rung_spec("C").kissing == 196_560

    def test_the_chain_is_a_chain(self, family):
        chain = family["chain"]
        assert chain["holds"]
        for step in chain["steps"]:
            assert step["derived"], step
            assert step["misses"] == 0, step
            assert step["norms"][0] == 2 * step["norms"][1]

    def test_the_densest_order_is_not_a_chain(self, family):
        # C and A are incomparable -- the diamond -- so the densest rung at
        # each norm does not give a tower, and the module says so with a
        # witness rather than glossing it.
        rows = {row["rung"]: row for row in family["containment_order"]}
        assert rows["C"]["incomparable"]
        assert rows["C"]["witness"] is not None

    def test_every_derived_containment_holds_on_real_points(self, family):
        spot = family["spot_check"]
        assert spot["all_hold"]
        assert spot["failures"] == ()
        assert spot["unwitnessed_non_containments"] == ()
        assert spot["claims"] > 0 and spot["points_checked"] > 0


# ═════════════════════════════════════════════════════════════════════════
#  3.  Quantisers for the new rungs
# ═════════════════════════════════════════════════════════════════════════

class TestQuantisers:

    @pytest.mark.parametrize("rung", ["8C", "4A", "2C", "16Z", "8D"])
    def test_the_nearest_point_is_on_the_rung(self, rung):
        vector = [Fraction(i * 3 % 7) - Fraction(1, 3) for i in range(24)]
        result = LE.quantise(vector, rung)
        assert CL.in_rung(result.point, rung)
        assert result.distance2 >= 0

    def test_scaling_is_an_exact_similarity(self):
        vector = [Fraction(i % 5) + Fraction(1, 4) for i in range(24)]
        base = LE.quantise([value / 4 for value in vector], "C")
        scaled = LE.quantise(vector, "4C")
        assert scaled.point == tuple(4 * value for value in base.point)
        assert scaled.distance2 == 16 * base.distance2


# ═════════════════════════════════════════════════════════════════════════
#  4.  The measurement
# ═════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def stored():
    data = NE.current()
    assert data is not None, (
        "the measurement cache is absent or stale; re-take it with "
        "python3 -m glm_universal.tools normladder --write")
    return data


class TestMeasurement:

    def test_the_cache_describes_the_sources(self):
        assert NE.state()["verdict"] == "fresh"

    def test_the_declared_ladder_is_one_rung_per_power_of_two(self, stored):
        declared = stored["declared"]
        assert declared["norms_are_powers_of_two"]
        assert declared["one_rung_per_norm"]
        assert tuple(declared["norms"]) == tuple(
            sorted(declared["norms"], reverse=True))

    def test_the_full_family_loses_the_refusal_property(self, stored):
        # This is the round's negative finding, pinned so it cannot quietly
        # become a footnote: the densest rung at every norm up to 2,048
        # answers a query wrongly.
        declared = stored["declared"]
        assert not declared["safety"]["safe"]
        assert declared["safety"]["wrong"] >= 1

    def test_the_repair_restores_it(self, stored):
        repair = stored["repair"]
        repaired = stored["repaired"]
        assert repair["safe"]
        assert repaired["safety"]["safe"]
        assert repaired["orders"]["totals"]["middle_out"]["wrong"] == 0
        assert repair["rounds"] >= 1
        assert repair["ladder"] == repaired["ladder"]

    def test_the_repair_says_what_it_retired_and_why(self, stored):
        moves = [move for round_ in stored["repair"]["history"]
                 for move in round_["moves"]]
        assert moves
        for move in moves:
            assert move["why"]
            assert move["norm"] in {1 << power for power in range(12)}

    def test_the_repaired_ladder_beats_the_named_rungs(self, stored):
        repaired = stored["repaired"]["orders"]["totals"]["middle_out"]
        named = stored["named_rungs"]["orders"]["totals"]["middle_out"]
        assert named["wrong"] == 0
        assert repaired["wrong"] == 0
        assert repaired["correct"] > named["correct"]

    def test_the_repaired_ladder_beats_every_single_rung(self, stored):
        best = stored["repaired"]["best_fixed_rung"]
        assert stored["repaired"]["orders"]["totals"]["middle_out"]["correct"] \
            > best["correct"]

    def test_the_stopping_rule_loses_nothing_against_the_oracle(self, stored):
        for key in ("declared", "repaired", "chain"):
            report = stored[key]
            assert report["orders"]["totals"]["middle_out"]["correct"] == \
                report["oracle"], key

    def test_the_sweep_locates_the_breaking_point(self, stored):
        sweep = stored["sweep"]
        rows = {row["length"]: row for row in sweep["rows"]}
        assert set(rows) == set(NE.FAMILY_LENGTHS)
        assert sweep["first_broken"] is not None
        assert sweep["longest_safe"] is not None
        assert sweep["longest_safe"] < sweep["first_broken"]
        for length, row in sorted(rows.items()):
            if length <= sweep["longest_safe"]:
                assert row["safe"], length
                assert row["matches_oracle"], length
            if length >= sweep["first_broken"]:
                assert not row["safe"], length

    def test_correctness_rises_along_the_safe_part_of_the_sweep(self, stored):
        sweep = stored["sweep"]
        safe = [row["correct"]["middle_out"] for row in sweep["rows"]
                if row["length"] <= sweep["longest_safe"]]
        assert safe == sorted(safe)


# ═════════════════════════════════════════════════════════════════════════
#  5.  Exactness (D7)
# ═════════════════════════════════════════════════════════════════════════

class TestExactness:

    @pytest.mark.parametrize("module", [NF, NE])
    def test_no_float_is_constructed(self, module):
        path = Path(module.__file__)
        assert ex.module_float_sites(path) == {}
