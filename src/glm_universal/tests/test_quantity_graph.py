"""Tests for :mod:`glm_universal.wheels.quantity_graph`.

The graph is the absorbed item's ``junctions``/``non_identities``, so the
first test checks the transcription against the supplied files; the rest
check the three behaviours the licensing needs -- transitivity, a declared
non-identity, and the audit of a table that is kept verbatim.
"""
import json
from pathlib import Path

import pytest

from glm_universal.wheels import quantity_graph as qg


def _supplied() -> Path:
    root = Path(__file__).resolve().parents[3] / "source_material" / "ToDo"
    # The absorbed item, not the `_2_ext` copy filed with Squares in Squares.
    hits = list(root.glob("cent_compiler_v12/wheels/W36.json"))
    assert hits, "the absorbed cent_compiler_v12 wheels are not in the tree"
    return hits[0].parent


def _supplied_tables():
    """The operative tables: ``index.json`` for junctions, the per-wheel
    blocks for the one-name non-identities that :data:`REPAIRS` completes."""
    root = _supplied()
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    junctions = [(j["wheel_a"], j["name_a"], j["wheel_b"],
                  j.get("name_b") or j["name_a"], j.get("reason", ""))
                 for j in index["junctions"]]
    non_identities = []
    for path in root.glob("W*.json"):
        d = json.loads(path.read_text(encoding="utf-8"))
        wid = d["id"]
        for n in d.get("non_identities") or []:
            non_identities.append((wid, n["name"], n["other_wheel"],
                                   n.get("reason", "")))
    return sorted(junctions), sorted(non_identities)


def test_the_tables_are_the_supplied_ones():
    junctions, non_identities = _supplied_tables()
    assert sorted(qg._JUNCTIONS) == junctions
    # The supplied non-identities carry one name only; REPAIRS supplies the
    # own-wheel and other-wheel names, read out of the reason.
    repaired = {(wheel, name): (own, other)
                for wheel, name, own, _, other in qg.REPAIRS}
    expected = []
    for wheel, name, other, why in non_identities:
        own, other_name = repaired.get((wheel, name), (name, name))
        expected.append((wheel, own, other, other_name, why))
    assert sorted(qg._NON_IDENTITIES) == sorted(expected)


def test_a_junction_joins_and_is_transitive():
    # W1 current = W14 current = W15 current (the inductor, the capacitor's
    # circuit, the charge carrier) and W24 current (the diode): one class.
    assert qg.may_identify(("W1", "current"), ("W14", "current")) is None
    assert qg.may_identify(("W14", "current"), ("W15", "current")) is None
    assert qg.may_identify(("W1", "current"), ("W24", "current")) is None
    table = qg.classes()
    assert set(table[("W1", "current")]) == {
        ("W1", "current"), ("W14", "current"), ("W15", "current"),
        ("W24", "current")}
    assert qg.wheels_of(("W1", "current"), table) == (
        "W1", "W14", "W15", "W24")


def test_a_declared_non_identity_blocks_the_pair():
    # Stored charge energy against stored current energy, and both against
    # delivered energy: the names coincide, the measurands do not.  The
    # declaration is pairwise, so W14/W15 is refused as undeclared, not as a
    # non-identity.
    for a, b in ((("W3", "energy"), ("W14", "energy")),
                 (("W3", "energy"), ("W15", "energy"))):
        why = qg.may_identify(a, b)
        assert why is not None and why.startswith("declared non-identity")
    assert qg.may_identify(("W14", "energy"), ("W15", "energy")) == \
        "no declared junction"
    # The junction on the same wheel pair, capacitance, still joins.
    assert qg.may_identify(("W3", "capacitance"), ("W14", "capacitance")) is None


def test_an_undeclared_pair_is_not_licenced():
    assert qg.may_identify(("W5", "mass"), ("W15", "power")) == "no declared junction"
    assert qg.may_identify(("W99", "mass"), ("W5", "mass")) is not None
    assert qg.may_identify(("W5", "nonsense"), ("W5", "mass")) is not None
    # A declared non-identity whose names differ in dimension is still a
    # refusal, but the wheel must hold the quantity first.
    assert qg.may_identify(("W39", "magnetomotive_force"), ("W1", "magnetomotive_force")) \
        is not None


def test_the_per_wheel_junction_copy_is_stale():
    """The item's per-wheel blocks hold 29 pairs; its index.json holds 59."""
    root = _supplied()

    def pair(a, b):
        return frozenset((a, b))

    per_wheel = set()
    for path in root.glob("W*.json"):
        d = json.loads(path.read_text(encoding="utf-8"))
        for j in d.get("junctions") or []:
            per_wheel.add(pair((d["id"], j["name_in_this_wheel"]),
                               (j["other_wheel"], j["name_in_other_wheel"])))
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    declared = {
        pair((j["wheel_a"], j["name_a"]),
             (j["wheel_b"], j.get("name_b") or j["name_a"]))
        for j in index["junctions"]
    }
    assert len(per_wheel) == 29
    assert len(declared) == 59
    assert per_wheel < declared


def test_the_audit_keeps_the_verbatim_defects_visible():
    a = qg.audit()
    unknown = {endpoint for _, endpoint in a["unknown_endpoints"]}
    # W4 holds no `energy` (the one bad junction) and no `relaxation_time`
    # (the one guard left vacuous -- no other-wheel name to read).
    assert ("W4", "energy") in unknown
    assert ("W4", "relaxation_time") in unknown
    # W36 `energy` was repaired to `pair_energy`, so it is no longer unknown.
    assert ("W36", "energy") not in unknown
    # ``index.json`` declares each pair once; the graph symmetrises all 59.
    one_way = {frozenset((j.a, j.b)) for j in a["one_way"]}
    assert len(one_way) == 59
    for pair in ((("W36", "pair_penetration"), ("W21", "stress")),
                 (("W38", "input_torque"), ("W4", "torque")),
                 (("W39", "magnetic_flux"), ("W16", "flux")),
                 (("W41", "heat_rate"), ("W15", "power")),
                 (("W42", "applied_load"), ("W5", "force"))):
        assert frozenset(pair) in one_way
    assert a["contradictions"] == []
    assert a["duplicates"] == []


def test_the_audit_classifies_what_it_cannot_use():
    a = qg.audit()
    assert {frozenset((j.a, j.b)) for j in a["dropped_junctions"]} == {
        frozenset({("W20", "strain"), ("W1", "charge")}),
        frozenset({("W22", "temperature"), ("W8", "temperature")}),
        frozenset({("W23", "charge"), ("W1", "charge")}),
        frozenset({("W32", "viscosity"), ("W6", "velocity")}),
        frozenset({("W35", "temperature"), ("W8", "temperature")}),
        frozenset({("W35", "ion_concentration"), ("W12", "amount")}),
        frozenset({("W36", "pair_energy"), ("W4", "energy")}),
    }
    assert [[list(n.a), list(n.b)] for n in a["vacuous_non_identities"]] == [
        [["W37", "relaxation_time"], ["W4", "relaxation_time"]]]
    why = qg.may_identify(("W37", "relaxation_time"), ("W4", "relaxation_time"))
    assert why.startswith("declared non-identity, vacuous")


def test_an_unknown_endpoint_is_dropped_from_the_graph_not_silently_used():
    graph = {frozenset(e) for e in qg.edges()}
    assert frozenset({("W36", "pair_energy"), ("W4", "energy")}) not in graph
    # The W36 stress edge is a dimension gap and is excluded from the graph.
    assert frozenset({("W36", "pair_penetration"), ("W21", "stress")}) not in graph
    assert qg.may_identify(("W36", "pair_penetration"), ("W21", "stress")) \
        .startswith("declared junction, dimension gap")
    # The sound cent edges remain, and a one-way declaration still joins.
    assert frozenset({("W39", "magnetic_flux"), ("W16", "flux")}) in graph
    assert qg.may_identify(("W39", "magnetic_flux"), ("W16", "flux")) is None


def test_dimension_gaps_are_the_declared_analogies():
    gaps = {frozenset((a, b)) for a, b, _, _ in qg.dimension_gaps()}
    assert gaps == {
        frozenset({("W21", "stress"), ("W36", "pair_penetration")}),
        frozenset({("W37", "stress"), ("W36", "pair_penetration")}),
        frozenset({("W1", "voltage"), ("W20", "stress")}),
        frozenset({("W12", "area"), ("W34", "pipe_radius")}),
    }


def test_the_stress_class_is_repaired_across_the_dimensioned_wheels():
    for a, b in ((("W20", "stress"), ("W21", "stress")),
                 (("W20", "stress"), ("W37", "stress")),
                 (("W21", "stress"), ("W40", "stress")),
                 (("W37", "stress"), ("W40", "stress"))):
        assert qg.may_identify(a, b) is None
    group = qg.classes()[("W21", "stress")]
    assert {w for w, _ in group} == {"W20", "W21", "W37", "W40"}


def test_the_report_is_self_consistent():
    report = qg.graph_report()
    assert report["junctions"] == 59
    assert report["non_identities"] == 15
    assert report["bridges"] == 2
    # 59 declared pairs: 7 name a quantity the wheel lacks and 4 are dimension
    # gaps, leaving 48; the two stress bridges make 50 sound edges.
    assert report["sound_edges"] == 50
    joined = report["joined_quantities"]
    assert "W5:mass" in joined and "W13:mass" in joined
    assert "W3:energy" not in joined
    assert "W41:heat_rate" in joined


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
