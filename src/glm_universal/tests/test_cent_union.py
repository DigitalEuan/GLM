"""Tests for :mod:`glm_universal.wheels.cent_union`.

The union merges three junction tables (Phase 66, the domain wheels and the
absorbed cent item), feeds the typed quantity graph's pairings to the split
system over all 39 wheels, and measures the energy family.  The tests pin the
merge, the cross-name join, one answered question, the refused factor-1/2
conflict, and the report's counts.
"""
import pytest

from glm_universal.wheels import cent_union as cu


def test_the_third_table_is_merged_not_duplicated():
    # Phase 66 and the domain table are the first two; the absorbed item's
    # table repeats most of them, and the merge keeps each pair once.
    assert cu.JUNCTIONS[("W1", "W14")] == ("current",)
    assert cu.JUNCTIONS[("W5", "W11")] == ("velocity",)
    assert cu.JUNCTIONS[("W1", "W15")] == ("current", "power")
    assert len(cu.JUNCTIONS) == 15
    for names in cu.JUNCTIONS.values():
        assert len(names) == len(set(names))


def test_a_cross_name_pairing_joins_different_names():
    system = cu.split_system()
    flux = set(cu.dmn.copies_of("flux", system))
    magnetic = set(cu.dmn.copies_of("magnetic_flux", system))
    assert flux & magnetic, "W39 magnetic_flux joins W16 flux"
    # The W36 pair_penetration/stress join is a dimension gap, so it is not
    # in the licensed system.
    stress = set(cu.dmn.copies_of("stress", system))
    penetration = set(cu.dmn.copies_of("pair_penetration", system))
    assert not (stress & penetration)


def test_a_single_wheel_question_is_answered():
    got = cu.derive_across("energy", ("inductance", "current"))
    assert got.answered
    assert got.formula == "1/2 * inductance * current^2"
    assert "W14" in got.wheels


def test_a_cross_name_answer_uses_the_asked_name():
    # A class label's canonical name need not be the name asked; the display
    # map restores the asked name (the real cross-name case, W36/stress, is a
    # dimension gap and is refused, so the rule is unit-tested directly).
    from fractions import Fraction
    from glm_universal.engineering import domains as dmn
    from glm_universal.engineering.union import SplitSystem
    system = SplitSystem(
        ({"pair_energy@0": Fraction(1), "pair_penetration@1": Fraction(-2)},),
        ("W36",), ("pair_energy = pair_penetration^2",),
        ("pair_energy@0", "pair_penetration@1"))
    found = dmn.derive_relations("pair_energy@0", ("pair_penetration@1",),
                                 system, {"pair_penetration@1": "stress"})
    assert found is not None and found.formula == "stress^2"


def test_the_capacitor_against_delivered_conflict_is_refused():
    # W3's 1/2 C V^2 against the delivered C V^2 that W1+W15 license; the
    # union refuses rather than choosing one.
    got = cu.derive_across("energy", ("charge", "voltage"))
    assert not got.answered
    assert "ambiguous" in got.reason and "1/2" in got.reason


def test_the_repaired_guards_are_non_identities():
    from glm_universal.wheels import quantity_graph as qg
    for a, b in ((("W39", "magnetomotive_force"), ("W1", "current")),
                 (("W41", "temperature_difference"), ("W8", "temperature")),
                 (("W42", "moment_of_inertia_of_section"), ("W4", "moment_of_inertia")),
                 (("W36", "pair_energy"), ("W5", "energy"))):
        why = qg.may_identify(a, b)
        assert why is not None and why.startswith("declared non-identity")


def test_the_energy_family_report():
    report = cu.energy_family_report()
    assert report["questions"] == 8
    # The 39-wheel naive union merges every `energy` and is ill-posed on all
    # eight; the six energy wheels alone derive seven of them.
    assert report["naive_answered"] == 0
    assert report["naive_ill_posed"] == 8
    assert report["family_naive_answered"] == 7
    assert report["licensed_answered"] == 3
    assert report["licensed_refused"] == 5
    assert len(report["conflations"]) == 4
    for row in report["conflations"]:
        assert row["family_naive"] is not None
        assert not row["answered"] or row["licensed"] != row["family_naive"]


def test_the_mass_family_refuses_the_e_mc2_conflation():
    report = cu.family_report("mass")
    assert report["family_naive_answered"] == 2
    assert report["licensed_answered"] == 0
    assert {row["family_naive"] for row in report["conflations"]} == {
        "2 * mass * speed_of_light^2", "1/2 * energy / speed_of_light^2"}


def test_the_time_family_refuses_the_travel_charging_conflation():
    report = cu.family_report("time")
    assert report["family_naive_answered"] == 3
    assert report["licensed_answered"] == 1
    assert {row["family_naive"] for row in report["conflations"]} == {
        "length * power / energy", "energy / power"}


def test_the_angle_family_refuses_the_phase_conflation():
    report = cu.family_report("angle")
    assert report["family_naive_answered"] == 2
    assert report["licensed_answered"] == 0
    assert {row["family_naive"] for row in report["conflations"]} == {
        "angular_frequency", "angular_velocity"}


def test_the_stress_family_is_repaired_and_the_gap_is_refused():
    report = cu.family_report("stress")
    assert report["licensed_answered"] == 1
    assert report["licensed_refused"] == 1
    rows = {(row["target"], row["inputs"]): row for row in report["rows"]}
    assert rows[("dissipated_power", ("force", "area", "strain_rate"))]["licensed"] \
        == "force * strain_rate / area"
    assert not rows[("pair_energy", ("stress",))]["answered"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
