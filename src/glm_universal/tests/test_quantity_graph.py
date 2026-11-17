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
    junctions, non_identities = [], []
    for path in _supplied().glob("W*.json"):
        d = json.loads(path.read_text(encoding="utf-8"))
        wid = d["id"]
        for j in d.get("junctions") or []:
            junctions.append((wid, j["name_in_this_wheel"], j["other_wheel"],
                              j["name_in_other_wheel"], j.get("reason", "")))
        for n in d.get("non_identities") or []:
            non_identities.append((wid, n["name"], n["other_wheel"],
                                   n.get("reason", "")))
    return sorted(junctions), sorted(non_identities)


def test_the_tables_are_the_supplied_ones():
    junctions, non_identities = _supplied_tables()
    assert sorted(qg._JUNCTIONS) == junctions
    assert sorted(qg._NON_IDENTITIES) == non_identities


def test_a_junction_joins_and_is_transitive():
    # W1 current = W14 current = W15 current (the inductor, the capacitor's
    # circuit, the charge carrier): one class of three.
    assert qg.may_identify(("W1", "current"), ("W14", "current")) is None
    assert qg.may_identify(("W14", "current"), ("W15", "current")) is None
    assert qg.may_identify(("W1", "current"), ("W15", "current")) is None
    table = qg.classes()
    assert set(table[("W1", "current")]) == {
        ("W1", "current"), ("W14", "current"), ("W15", "current")}
    assert qg.wheels_of(("W1", "current"), table) == ("W1", "W14", "W15")


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


def test_the_audit_keeps_the_verbatim_defects_visible():
    a = qg.audit()
    unknown = {endpoint for _, endpoint in a["unknown_endpoints"]}
    # W4 holds no `energy` and no `relaxation_time`; W36 holds no `energy`
    # (only pair_energy and wall_energy).
    assert ("W4", "energy") in unknown
    assert ("W4", "relaxation_time") in unknown
    assert ("W36", "energy") in unknown
    # Fifteen junctions are declared in one direction only.
    one_way = {frozenset((j.a, j.b)) for j in a["one_way"]}
    assert len(one_way) == 15
    for pair in ((("W36", "pair_penetration"), ("W21", "stress")),
                 (("W38", "input_torque"), ("W4", "torque")),
                 (("W39", "magnetic_flux"), ("W16", "flux")),
                 (("W41", "heat_rate"), ("W15", "power")),
                 (("W42", "applied_load"), ("W5", "force"))):
        assert frozenset(pair) in one_way
    assert a["contradictions"] == []
    assert a["duplicates"] == []


def test_an_unknown_endpoint_is_dropped_from_the_graph_not_silently_used():
    graph = {frozenset(e) for e in qg.edges()}
    assert frozenset({("W36", "pair_energy"), ("W4", "energy")}) not in graph
    # The sound cent edges remain, and a one-way declaration still joins.
    assert frozenset({("W36", "pair_penetration"), ("W21", "stress")}) in graph
    assert qg.may_identify(("W21", "stress"), ("W36", "pair_penetration")) is None
    assert qg.may_identify(("W39", "magnetic_flux"), ("W16", "flux")) is None


def test_the_report_is_self_consistent():
    report = qg.graph_report()
    assert report["junctions"] == 43
    assert report["non_identities"] == 15
    # 43 declarations, 15 of them one-way: 14 mirror pairs plus 15 one-way
    # edges make 29 undirected edges; one names a quantity W4 lacks, leaving 28.
    assert report["sound_edges"] == 28
    joined = report["joined_quantities"]
    assert "W5:mass" in joined and "W13:mass" in joined
    assert "W3:energy" not in joined
    assert "W41:heat_rate" in joined


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
