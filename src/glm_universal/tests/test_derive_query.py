"""Tests for :func:`glm_universal.wheels.derive_query.derive_text` -- the
derivability engine of the formula wheels on the answering path (*is emf =
magnetic_field * area / time a law?*).

*Created 1 November 2026 (Phase 186: intake absorption).*

What is pinned:

* **The study's split is reproduced.**  Every question of
  :data:`glm_universal.wheels.cent_wheels_study.MEASURE_BATTERY` put through
  :func:`derive_text` is licensed exactly when the study's measurement
  licenses it, by the same wheel: 63 of the 64 laws, none of the 51
  not-a-laws (``studies/CENT_WHEELS_STUDY.md`` §8).
* **Certificates re-check.**  A derivable answer's rational combination of
  axioms recombines, exactly, to the equation's relation; a not-derivable
  answer's separating functional is zero on every axiom of its wheel and
  nonzero on the equation.
* **The provisional note** is carried by an answer that rests on a cent wheel
  while that family is provisional, and never by one from a registry wheel.
* **Refusals give a reason**: text that is no equation, a float literal,
  a literal out of all proportion, an unknown wheel, and quantities no wheel
  knows (named).
* **Figures are exact** -- no float anywhere (directive D7).

Plain test functions (runnable by ``glm_universal.intake.fallback_tests``).
"""
from __future__ import annotations

from fractions import Fraction

from glm_universal.wheels import provisional_status
from glm_universal.wheels.cent_wheels import relation_vector_q
from glm_universal.wheels.cent_wheels_study import LAW, MEASURE_BATTERY, NOT_A_LAW, battery_rows
from glm_universal.wheels.derive_query import derive_text, known_quantities, split_wheel


def _licensed(ok, figures) -> bool:
    return bool(ok) and figures.get("verdict") == "derivable"


def _exact(value) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, tuple):
        return all(_exact(v) for v in value)
    return isinstance(value, (int, str, Fraction))


def test_the_study_battery_split_is_reproduced():
    study = {r["qid"]: r["with_cent"] for r in battery_rows()}
    laws = nots = laws_licensed = nots_licensed = 0
    for qid, _wheel, eq, gold, _source, _reason in MEASURE_BATTERY:
        ok, text, figures = derive_text(eq)
        lic = _licensed(ok, figures)
        assert lic == (study[qid] is not None), (qid, text)
        if lic:
            assert figures["wheel"] == study[qid], qid
        if gold == LAW:
            laws += 1
            laws_licensed += lic
        else:
            assert gold == NOT_A_LAW
            nots += 1
            nots_licensed += lic
    assert (laws, laws_licensed) == (64, 63)
    assert (nots, nots_licensed) == (51, 0)


def test_every_battery_answer_has_exact_figures_and_a_reason():
    for qid, _wheel, eq, *_ in MEASURE_BATTERY:
        ok, text, figures = derive_text(eq)
        assert text.startswith("derive: "), qid
        for key, value in figures.items():
            assert _exact(value), (qid, key, value)
        if not ok:
            assert "no wheel knows" in text, (qid, text)


def test_a_certificate_recombines_exactly():
    for eq in ("emf = magnetic_field * area / time", "power = current^2 * resistance",
               "electric_field = magnetic_field / (permittivity * permeability)^(1/2)"):
        ok, text, figures = derive_text(eq)
        assert ok and figures["verdict"] == "derivable", text
        total = {}
        for axiom, weight in figures["certificate"]:
            assert isinstance(weight, Fraction) and weight != 0
            assert axiom in text
            for k, v in relation_vector_q(axiom).items():
                total[k] = total.get(k, Fraction(0)) + weight * v
        assert {k: v for k, v in total.items() if v} == relation_vector_q(eq), eq


def test_a_law_from_a_registry_wheel_carries_no_note():
    ok, text, figures = derive_text("voltage = current * resistance")
    assert ok and figures["verdict"] == "derivable" and figures["wheel"] == "W1"
    assert figures["engine"] == "integer"
    assert provisional_status("W1") is None
    assert "provisional" not in figures and "[provisional" not in text


def test_a_law_from_a_cent_wheel_carries_the_note():
    ok, text, figures = derive_text("emf = magnetic_field * area / time")
    assert ok and figures["verdict"] == "derivable" and figures["wheel"] == "W16"
    assert figures["engine"] == "rational"
    note = provisional_status("W16")
    if note:
        assert figures["provisional"] == note
        assert text.endswith(f" [{note}]")
    else:
        assert "provisional" not in figures


def test_not_derivable_gives_the_separating_reason():
    ok, text, figures = derive_text("flux = 2 * magnetic_field * area")
    assert ok and figures["verdict"] == "not derivable", text
    assert figures["wheel"] == "W16" and figures["functional"] == (("#2", 1),)
    assert "coefficient" in text and figures["functional_value"] != 0
    # The functional is zero on every axiom of W16 and not on the equation.
    from glm_universal.wheels.cent_wheels import cent_wheel
    functional = dict(figures["functional"])
    for axiom in cent_wheel("W16").axioms:
        rel = relation_vector_q(axiom)
        assert sum(Fraction(v) * rel.get(k, Fraction(0)) for k, v in functional.items()) == 0
    # Quantities no single wheel names together: each is placed.
    ok, text, figures = derive_text("capillary_height = surface_tension / pressure")
    assert ok and figures["verdict"] == "not derivable" and figures["covering"] == ()
    assert "dimension table of W32" in text


def test_one_wheel_can_be_named():
    eq = "emf = magnetic_field * area / time"
    assert split_wheel(eq + " in W16") == (eq, "W16")
    assert split_wheel(eq + " wheel w16?") == (eq, "W16")
    assert split_wheel(eq + " in wheel W01") == (eq, "W1")
    ok, text, figures = derive_text(eq + " in W16")
    assert ok and figures["verdict"] == "derivable" and figures["wheel"] == "W16"
    ok, text, figures = derive_text(eq + " in W1")
    assert ok and figures["verdict"] == "not derivable" and figures["wheel"] == "W1"
    assert "provisional" not in figures and "functional" in figures
    for wid in ("W35", "W26", "W99"):
        ok, text, figures = derive_text(eq + " in " + wid)
        assert not ok and f"no wheel {wid}" in text, wid


def test_garbage_and_unknown_quantities_are_refused_with_a_reason():
    cases = {
        "": "derive takes an equation",
        "x = = y": "exactly one '='",
        "hello world": "cannot read",
        "voltage = 9.81 * current": "cannot read",
        "voltage = -1 * current": "negative coefficient",
        "voltage = 123456789012 * current": "is above",
        "voltage = current^1000 * resistance": "is above",
    }
    for arg, reason in cases.items():
        ok, text, figures = derive_text(arg)
        assert not ok and reason in text, (arg, text)
    ok, text, figures = derive_text("foo = bar * area")
    assert not ok and figures["unknown"] == ("bar", "foo")
    assert "no wheel knows bar, foo" in text
    ok, text, figures = derive_text("valence = temperature / membrane_voltage")
    assert not ok and figures["unknown"] == ("membrane_voltage", "valence")
    assert "area" in known_quantities() and "capillary_height" in known_quantities()


def test_an_identity_and_determinism():
    ok, text, figures = derive_text("flux = flux")
    assert ok and figures["verdict"] == "derivable" and figures["certificate"] == ()
    assert "identity" in text
    for arg in ("emf = magnetic_field * area / time", "flux = 2 * magnetic_field * area",
                "foo = bar"):
        assert derive_text(arg) == derive_text(arg)
