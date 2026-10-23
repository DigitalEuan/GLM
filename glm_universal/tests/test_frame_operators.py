"""Tests for the Lorentz-boosts study: exact rational boosts, operators
inferred from example pairs, and the anchor kappa (Phase 177).

*Created 21 October 2026.*

``studies/FRAME_OPERATOR_STUDY.md`` declared the marks.  These tests pin:

* both **Lean files** state their theorems with no ``sorry``;
* the **arithmetic** mirrors ``RationalBoost.lean``: the worked example of
  the source document, invariance, inverse, composition, the light-cone
  diagonal form, and the light-like confound on one ray and its breaking on
  the other;
* the **gate**: one demonstration of a boost is refused with a massive state
  to ask about, two are answered with the boost named; light-like
  demonstrations on one ray are refused; an operator outside the families
  is refused, including on data confined to one line (the evidence guard);
* the **anchor**: ``kappa`` lies in the register's ``D0(Br2)`` interval and
  every cell ratio is free of it;
* the **stored measurement**, when current, meets every mark but F4.
"""

from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path

from glm_universal.reasoning import frame_operators as fo
from glm_universal.reasoning import frame_operator_study as fos
from glm_universal.reasoning import kappa_anchor as ka

_ROOT = Path(__file__).resolve().parents[2] / "glm_lean"


def test_lean_files_state_the_theorems_without_sorry():
    for f, names in ((fo.LEAN_FILE, fo.LEAN_THEOREMS),
                     (ka.LEAN_FILE, ka.LEAN_THEOREMS)):
        text = (_ROOT / f).read_text(encoding="utf-8")
        for name in names:
            assert f"theorem {name}" in text, (f, name)
        assert "sorry" not in text


def test_worked_example_of_the_source_document():
    # u = 1/2 gives the matrix (5/3, -4/3; -4/3, 5/3); the unit rest state
    # goes to (5/3, -4/3) and keeps E^2 - p^2 = 1
    out = fo.boost(F(1, 2), (F(1), F(0)))
    assert out == (F(5, 3), F(-4, 3))
    assert fo.inv(out) == 1
    assert fo.ca(F(1, 2)) ** 2 - fo.sb(F(1, 2)) ** 2 == 1


def test_inverse_composition_and_lightcone():
    q = (F(7), F(3))
    for u in (F(1, 3), F(-2, 5), F(5, 7)):
        assert fo.boost(-u, fo.boost(u, q)) == q
        k = fo.doppler(u)
        assert fo.plus(fo.boost(u, q)) == fo.plus(q) / k
        assert fo.minus(fo.boost(u, q)) == k * fo.minus(q)
        for v in (F(1, 2), F(-1, 4)):
            w = fo.compose(u, v)
            assert fo.boost(u, fo.boost(v, q)) == fo.boost(w, q)
            assert fo.doppler(w) == fo.doppler(u) * fo.doppler(v)


def test_null_confound_one_ray_and_its_breaking():
    u = F(1, 2)
    e = F(4)
    assert fo.boost(u, (e, e)) == fo.scale(1 / fo.doppler(u), (e, e))
    assert fo.boost(u, (e, -e)) == fo.scale(fo.doppler(u), (e, -e))


def test_one_boost_demonstration_asks_for_a_massive_state():
    ok, text, figures = fo.frame_text("1,0 -> 5/3,-4/3 ? 3,1")
    assert not ok and figures["status"] == "ambiguous"
    x = fo.parse_state(figures["ask"])
    assert fo.inv(x) != 0
    assert "to settle it, give the output for" in text


def test_two_boost_demonstrations_answer_and_name_the_boost():
    ok, text, figures = fo.frame_text("1,0 -> 5/3,-4/3 ; 2,1 -> 2,-1 ? 3,1")
    assert ok and figures["answer"] == "11/3,-7/3"
    assert "u = 1/2" in text


def test_light_like_one_ray_is_refused():
    ok, text, figures = fo.frame_text("1,1 -> 1/3,1/3 ; 2,2 -> 2/3,2/3 ? 3,1")
    assert not ok
    assert "null_confound" in text


def test_outside_the_families_is_refused():
    shear = lambda q: (q[0] + q[1], q[1])
    demos = [((F(3), F(1)), shear((F(3), F(1)))),
             ((F(2), F(-1)), shear((F(2), F(-1))))]
    assert fo.solve(demos, (F(5), F(2)))["status"] == "unfit"
    # data confined to one line: the two-parameter family fits but is not
    # tested, so the guard refuses rather than answer wrongly
    line = [((F(1), F(1)), shear((F(1), F(1)))),
            ((F(2), F(2)), shear((F(2), F(2))))]
    r = fo.solve(line, (F(5), F(2)))
    assert r["status"] in ("untested", "ambiguous")
    assert fo.solve(line, (F(5), F(2)), evidence_guard=False)["status"] == "answered"


def test_kappa_anchor():
    r = ka.kappa_report()
    assert r["within_br2_interval"] and r["kappa_free"]
    assert [n for n, _ in r["ordering"]] == [
        "third significant figure", "register uncertainty",
        "tick-budget rounding", "which tabulated quantity"]
    ok, text, _ = ka.kappa_text("")
    assert ok and "Br2" in text


def test_stored_measurement_meets_its_marks():
    report = fos.frame_operator_report()
    if not report.get("available"):
        return
    missed = [m for m, ok in report["marks"].items() if not ok]
    assert missed == ["F4"], missed
    assert report["extra"]["confound_same_ray_separates"] == 0
