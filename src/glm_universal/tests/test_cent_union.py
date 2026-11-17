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
    stress = set(cu.dmn.copies_of("stress", system))
    penetration = set(cu.dmn.copies_of("pair_penetration", system))
    assert stress & penetration, "pair_penetration and stress are one class"
    flux = set(cu.dmn.copies_of("flux", system))
    magnetic = set(cu.dmn.copies_of("magnetic_flux", system))
    assert flux & magnetic, "W39 magnetic_flux joins W16 flux"


def test_a_single_wheel_question_is_answered():
    got = cu.derive_across("energy", ("inductance", "current"))
    assert got.answered
    assert got.formula == "1/2 * inductance * current^2"
    assert "W14" in got.wheels


def test_a_cross_name_answer_uses_the_asked_name():
    # `stress` is the class that joins W21/W36/W37; the canonical name is
    # `pair_penetration`, but the question asked `stress`.
    got = cu.derive_across("pair_energy", ("stress",))
    assert got.answered
    assert got.formula == "stress^2"
    assert "pair_penetration" not in got.formula


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
    assert report["naive_six_answered"] == 7
    assert report["licensed_answered"] == 3
    assert report["licensed_refused"] == 5
    assert len(report["conflations"]) == 4
    for row in report["conflations"]:
        assert row["naive_six"] is not None
        assert not row["answered"] or row["licensed"] != row["naive_six"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
