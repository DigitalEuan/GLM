"""Tests for ``data_objects/comparison_classes`` -- the comparison-class register.

The register is step 3 of ``studies/RELATIVE_MEASURE_PROPOSAL.md``: a *hot* cup
of tea and a *hot* stellar surface are the same word against two different
brackets, and the bracket is the datum the machine did not hold.  What has to
be pinned is not the prose but the three things that could silently go wrong:

* the register is *derived* -- every class names a quantity the physics
  register already holds, and the dimension, unit and EXT10 exponents in a
  class carrier are read from there rather than typed a second time;
* the carrier round trips, so a class is a first-class register object and not
  a table on the side;
* the scales agree with the semantic lexicon wherever the two overlap, which
  is what makes the measure reading a widening of the static one rather than
  a rival to it.

``test_measure_words.py`` pins what is built on top: the reading, the widening
audit and the refusals.  The machine-checked counterparts are in
``RequestProject/GLM/MeasureView.lean``.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal import data_objects as do
from glm_universal.data_objects import comparison_classes as cc
from glm_universal.data_objects import physics as ph
from glm_universal.data_objects import semantic_lexicon as sl


@pytest.fixture(scope="module")
def classes():
    return cc.comparison_classes()


@pytest.fixture(scope="module")
def summary():
    return cc.register_summary()


class TestTheRegisterIsTheSizeItSaysItIs:
    """The counts the documents quote, recomputed from the register."""

    def test_forty_five_classes_over_eleven_quantities(self, classes,
                                                       summary):
        assert len(classes) == 45
        assert summary["classes"] == 45
        assert summary["quantity_count"] == 11
        assert summary["quantities"] == (
            "density", "force", "frequency", "illuminance", "length",
            "luminous_intensity", "mass", "pressure", "temperature",
            "velocity", "volume")

    def test_classes_per_quantity(self, summary):
        assert summary["classes_per_quantity"] == {
            "temperature": 6, "velocity": 5, "mass": 5, "length": 5,
            "volume": 5, "density": 4, "illuminance": 4, "force": 3,
            "pressure": 3, "luminous_intensity": 3, "frequency": 2}

    def test_eleven_scales_and_sixty_four_degree_words(self, summary):
        assert summary["scales"] == 11
        assert summary["scale_words"] == 64
        assert (sum(len(scale.words) for scale in cc.measure_scales().values())
                == 64)

    def test_every_quantity_with_classes_has_a_scale(self, summary):
        assert summary["scaled_quantities"] == summary["quantities"]

    def test_names_are_unique(self, classes):
        names = [klass.name for klass in classes]
        assert len(set(names)) == len(names)


class TestTheRegisterIsDerived:
    """Nothing dimensional is typed twice: it is read from physics."""

    def test_every_class_names_a_registered_quantity(self, classes, subtests):
        for klass in classes:
            with subtests.test(klass=klass.name):
                assert ph.quantity_by_name(klass.quantity) is klass.registered

    def test_dimension_and_unit_come_from_the_physics_register(
            self, classes, subtests):
        for klass in classes:
            registered = ph.quantity_by_name(klass.quantity)
            with subtests.test(klass=klass.name):
                assert klass.exps_ext10 == registered.exps_ext10
                assert klass.unit == registered.unit

    def test_a_class_of_an_unregistered_quantity_will_not_load(self):
        with pytest.raises(KeyError):
            cc.ComparisonClass(name="mood", quantity="cheerfulness",
                               low=Fraction(1), high=Fraction(2),
                               typical=Fraction(3, 2))

    def test_the_bracket_must_be_ordered_and_contain_the_typical(self):
        with pytest.raises(ValueError):
            cc.ComparisonClass(name="backwards", quantity="temperature",
                               low=Fraction(400), high=Fraction(300),
                               typical=Fraction(350))
        with pytest.raises(ValueError):
            cc.ComparisonClass(name="outside", quantity="temperature",
                               low=Fraction(300), high=Fraction(400),
                               typical=Fraction(500))


class TestTheBracketArithmeticIsExact:
    """Positions and magnitudes are rationals, and no float is constructed."""

    def test_every_datum_is_a_fraction(self, classes, subtests):
        for klass in classes:
            with subtests.test(klass=klass.name):
                for value in (klass.low, klass.high, klass.typical,
                              klass.span, klass.midpoint,
                              klass.typical_position):
                    assert isinstance(value, Fraction)

    def test_magnitude_and_position_are_inverse(self, classes, subtests):
        for klass in classes:
            with subtests.test(klass=klass.name):
                for position in (Fraction(0), Fraction(1, 8), Fraction(1, 2),
                                 Fraction(7, 8), Fraction(1)):
                    magnitude = klass.magnitude_at(position)
                    assert klass.position_of(magnitude) == position
                    assert klass.contains(magnitude)

    def test_the_ends_of_the_bracket_are_the_bracket(self, classes, subtests):
        for klass in classes:
            with subtests.test(klass=klass.name):
                assert klass.magnitude_at(Fraction(0)) == klass.low
                assert klass.magnitude_at(Fraction(1)) == klass.high
                assert klass.typical_position >= 0
                assert klass.typical_position <= 1

    def test_outside_the_bracket_is_reported_not_clamped(self):
        tea = cc.class_by_name("tea")
        assert tea.contains(Fraction(500)) is False
        assert tea.position_of(Fraction(500)) > 1


class TestTheCodecRoundTrips:
    """A class is a register carrier, and the carrier is enough to rebuild it."""

    def test_layout_is_twenty_four_named_coordinates(self):
        assert len(cc.COMPARISON_LAYOUT) == 24
        assert len(set(cc.COMPARISON_LAYOUT)) == 24

    def test_round_trip_for_every_class(self, classes, subtests):
        codec = cc.ComparisonClassCodec()
        for klass in classes:
            with subtests.test(klass=klass.name):
                carrier = codec.encode(klass)
                assert len(carrier) == 24
                assert codec.decode(carrier, name=klass.name) == klass

    def test_the_gloss_is_prose_and_excluded_from_equality(self):
        tea = cc.class_by_name("tea")
        other = cc.ComparisonClass(
            name=tea.name, quantity=tea.quantity, low=tea.low,
            high=tea.high, typical=tea.typical, gloss="something else")
        assert other == tea

    def test_the_register_is_exported_as_objects(self, classes):
        objects = cc.comparison_class_objects()
        assert len(objects) == len(classes)
        assert all(len(obj.carrier) == 24 for obj in objects)
        assert do.all_objects()["comparison"] == objects


class TestTheScales:
    """A scale is an ordered set of degree words at exact positions."""

    def test_positions_are_in_the_unit_interval_and_ordered(self, subtests):
        for quantity, scale in cc.measure_scales().items():
            with subtests.test(quantity=quantity):
                positions = [word.position for word in scale.words]
                assert positions == sorted(positions)
                assert all(0 <= p <= 1 for p in positions)
                assert all(isinstance(p, Fraction) for p in positions)

    def test_above_is_the_strict_upper_set(self):
        temperature = cc.scale_for_quantity("temperature")
        assert temperature is not None
        assert "hot" in temperature.vocabulary
        above = temperature.above("hot")
        assert all(temperature.position_of(w) > temperature.position_of("hot")
                   for w in above)
        assert temperature.position_of("hot") == Fraction(7, 8)
        assert temperature.position_of("cold") == Fraction(1, 8)

    def test_nearest_word_is_nearest(self):
        temperature = cc.scale_for_quantity("temperature")
        assert temperature is not None
        assert temperature.nearest_word(Fraction(7, 8)) == "hot"
        assert temperature.nearest_word(Fraction(1, 8)) == "cold"

    def test_degree_word_finds_a_word_and_declines_the_rest(self):
        assert cc.degree_word("hot") == ("temperature", Fraction(7, 8))
        assert cc.degree_word("expensive") is None

    def test_an_unscaled_quantity_has_no_scale(self):
        assert cc.scale_for_quantity("energy") is None


class TestTheScalesAgreeWithTheLexicon:
    """Where a degree word is also a concept, the two registers must agree."""

    def test_the_agreement_holds(self):
        agreement = cc.lexicon_agreement()
        assert agreement["agrees"] is True
        assert agreement["quantity_errors"] == []
        assert agreement["polarity_errors"] == []
        assert agreement["pole_errors"] == []
        assert agreement["duplicate_words"] == []

    def test_twelve_words_are_shared(self):
        agreement = cc.lexicon_agreement()
        assert agreement["shared_count"] == 12
        words = {row["word"] for row in agreement["shared_words"]}
        assert words == {"cold", "hot", "slow", "fast", "light_adj", "heavy",
                         "weak", "strong", "dense", "large", "small", "dark"}

    def test_shared_words_carry_the_lexicon_quantity(self, subtests):
        concepts = {c.subject: c for c in sl.SEMANTIC_SAMPLE_CONCEPTS}
        for row in cc.lexicon_agreement()["shared_words"]:
            with subtests.test(word=row["word"]):
                concept = concepts[str(row["word"])]
                named = [cc.resolve_quantity(other)
                         for predicate, other in concept.relations
                         if predicate == "property_of"]
                assert str(row["quantity"]) in named

    def test_heavy_is_the_only_neutral_polarity(self):
        agreement = cc.lexicon_agreement()
        assert agreement["polarity_neutral"] == ["heavy"]

    def test_six_opposite_pole_pairs_sum_to_one(self):
        pairs = cc.lexicon_agreement()["pole_pairs"]
        assert len(pairs) == 6
        assert all(pair["sum"] == Fraction(1) for pair in pairs)

    def test_the_check_is_not_vacuous(self, monkeypatch):
        """Move one word off its pole and the agreement reports it."""
        original = cc.MEASURE_SCALES["temperature"]
        broken_words = tuple(
            cc.DegreeWord(w.word, Fraction(1, 3)) if w.word == "hot" else w
            for w in original.words)
        broken = cc.MeasureScale(quantity=original.quantity,
                                 words=tuple(sorted(broken_words,
                                                    key=lambda w: w.position)))
        scales = dict(cc.MEASURE_SCALES)
        scales["temperature"] = broken
        monkeypatch.setattr(cc, "MEASURE_SCALES", scales)
        report = cc.lexicon_agreement()
        assert report["agrees"] is False


class TestTheQuantityAliases:
    """*size* is a volume and *light* an illuminance -- a name, not a datum.

    The alias table is the whole of what lets ``large``, ``small`` and
    ``dark`` be measured, so what it may and may not do is pinned here: it
    must reach a quantity the physics register holds, it must not shadow one,
    and it must supply no coordinate of its own -- every dimensional fact
    about an aliased class still comes out of the physics register.
    """

    def test_the_audit_is_sound(self):
        audit = cc.alias_audit()
        assert audit["sound"] is True
        assert audit["unregistered_targets"] == []
        assert audit["shadowing"] == []
        assert audit["count"] == len(cc.QUANTITY_ALIASES) == 7

    def test_the_seven_aliases(self):
        """Two came from measure words and five from `related_to` endpoints."""
        assert cc.QUANTITY_ALIASES == {
            "size": "volume",
            "light": "illuminance",
            "heat": "energy",
            "weight": "force",
            "illumination": "illuminance",
            "distance": "length",
            "magnetic_field": "magnetic_flux_density",
        }
        assert cc.resolve_quantity("size") == "volume"
        assert cc.resolve_quantity("light") == "illuminance"
        assert cc.resolve_quantity("heat") == "energy"

    def test_resolution_is_the_identity_on_registered_names(self, subtests):
        for name in ("temperature", "volume", "illuminance",
                     "luminous_intensity", "mass"):
            with subtests.test(name=name):
                assert cc.resolve_quantity(name) == name
                assert ph.quantity_by_name(name).name == name

    def test_an_alias_supplies_no_coordinate(self, subtests):
        """Every aliased class reads its dimension out of physics."""
        for klass in cc.classes_for_quantity("volume"):
            with subtests.test(klass=klass.name):
                assert klass.exps_ext10 == ph.quantity_by_name(
                    "volume").exps_ext10
                assert klass.unit == ph.quantity_by_name("volume").unit

    def test_an_alias_to_an_unregistered_quantity_is_caught(self,
                                                            monkeypatch):
        monkeypatch.setattr(cc, "QUANTITY_ALIASES",
                            {"size": "no_such_quantity"})
        audit = cc.alias_audit()
        assert audit["sound"] is False
        assert audit["unregistered_targets"] == ["size -> no_such_quantity"]

    def test_an_alias_that_shadows_a_registered_quantity_is_caught(
            self, monkeypatch):
        monkeypatch.setattr(cc, "QUANTITY_ALIASES", {"mass": "volume"})
        audit = cc.alias_audit()
        assert audit["sound"] is False
        assert audit["shadowing"] == ["mass"]


class TestTheSizeAndLightClasses:
    """The data this round added, and that it is exact."""

    def test_the_size_classes(self):
        names = [k.name for k in cc.classes_for_quantity("volume")]
        assert names == ["droplet", "handheld", "room_volume",
                         "building_volume", "reservoir"]

    def test_the_light_classes(self):
        assert [k.name for k in cc.classes_for_quantity("illuminance")] == [
            "night_sky", "indoor_lighting", "overcast_day",
            "direct_sunlight"]
        assert [k.name for k in
                cc.classes_for_quantity("luminous_intensity")] == [
            "candle", "household_lamp", "lighthouse"]

    def test_every_bracket_is_exact(self, subtests):
        for klass in (cc.classes_for_quantity("volume")
                      + cc.classes_for_quantity("illuminance")
                      + cc.classes_for_quantity("luminous_intensity")):
            with subtests.test(klass=klass.name):
                for value in (klass.low, klass.high, klass.typical):
                    assert isinstance(value, Fraction)

    def test_large_and_small_are_poles_of_the_size_scale(self):
        scale = cc.scale_for_quantity("volume")
        assert scale is not None
        assert scale.position_of("large") == Fraction(7, 8)
        assert scale.position_of("small") == Fraction(1, 8)
        assert scale.position_of("large") + scale.position_of("small") == 1

    def test_dark_and_bright_are_poles_of_the_light_scale(self):
        scale = cc.scale_for_quantity("illuminance")
        assert scale is not None
        assert scale.position_of("dark") == Fraction(1, 8)
        assert scale.position_of("bright") == Fraction(7, 8)

    def test_the_classes_carry_and_round_trip(self, subtests):
        codec = cc.ComparisonClassCodec()
        for klass in (cc.classes_for_quantity("volume")
                      + cc.classes_for_quantity("illuminance")
                      + cc.classes_for_quantity("luminous_intensity")):
            with subtests.test(klass=klass.name):
                assert codec.decode(codec.encode(klass),
                                    name=klass.name) == klass
