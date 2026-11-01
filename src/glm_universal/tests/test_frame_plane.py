"""Tests for ``tool frame`` in 1+2 dimensions (Phase 178, part B).

*Created 22 October 2026 (Phase 178).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from ``tests/README.md``'s row for
this file (seven tests), ``MASTER_PLAN.md`` Phase 178, ``reasoning/
frame_plane.py`` and the reconstructed ``reasoning/frame_plane_study.py``.*

``studies/COLOUR_INDUCTION_STUDY.md`` (part B) declared the marks. These tests
pin:

* the **Lean file** ``LorentzPlane.lean`` states its thirteen theorems with no
  ``sorry``; while it is lost (October 2026 reorganisation) it must be
  recorded in ``studies/_lean_files_needed.md`` and the study's mark L must
  report it not met (the pattern of ``test_lorentzian_majority.py``);
* boosts along both axes, along any direction, and rotations are **Lorentz**
  maps and keep ``E^2 - px^2 - py^2``;
* the **Thomas--Wigner example**: ``B_x(1/2) B_y(1/2)`` is exactly the pure
  boost to ``(25/9, -20/9, -4/3)`` times the rotation ``(15/17, -8/17)``,
  and not itself a boost;
* the **gate**: one pair of that map refused, three answered with the Wigner
  rotation;
* a **reflection seen on a plane** is refused (the span guard);
* ``tool frame`` **routes by component count**: 3-component states to the
  frame plane, 2-component tasks exactly as in Phase 177;
* the **stored measurement**, when current, meets P1, P2, P3, P5, P6 and T
  (the reconstruction's take misses L while the Lean file is missing, and
  P4 by one Thomas query whose demonstrations span two dimensions only).
"""

from __future__ import annotations

from fractions import Fraction as F

from glm_universal.constants import LEAN_FILES_NEEDED, lean_file
from glm_universal.lean_check import audited_or_held
from glm_universal.reasoning import frame_operators as fo
from glm_universal.reasoning import frame_plane as fp
from glm_universal.reasoning import frame_plane_study as fps
from glm_universal.runtime.toolbox import run_tool

_THOMAS = fp.matmul(fp.boost_x(F(1, 2)), fp.boost_y(F(1, 2)))
_XS = [(F(1), F(0), F(0)), (F(2), F(1), F(0)), (F(2), F(0), F(1))]
_Q = (F(3), F(1), F(1))


def _pairs(m, inputs):
    return [(x, fp.matvec(m, x)) for x in inputs]


def test_lean_file_states_the_theorems_without_sorry():
    assert len(fp.LEAN_THEOREMS) == 13
    path = lean_file(fp.LEAN_FILE)   # build tree, or awaiting_recovery/
    if not path.exists():
        # lost in the October 2026 reorganisation: it must then be recorded
        # as missing, and the study's Lean mark must say so.
        assert "`LorentzPlane.lean`" in LEAN_FILES_NEEDED.read_text(
            encoding="utf-8")
        lean = fps._lean()
        assert lean["present"] is False and lean["theorems"] == 0
        return
    text = path.read_text(encoding="utf-8")
    assert audited_or_held("RequestProject.GLM.LorentzPlane")
    for name in fp.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text


def test_boosts_and_rotations_are_lorentz():
    maps = [fp.boost_x(F(3, 5)), fp.boost_y(F(-1, 3)), fp.rot(F(3, 5), F(4, 5)),
            fp.boost_to((F(5, 3), F(4, 3), F(0))),
            fp.boost_to((F(25, 9), F(-20, 9), F(-4, 3))), _THOMAS]
    for m in maps:
        assert fp.is_lorentz(m) and fp.det(m) == 1
        for v in _XS + [_Q]:
            w = fp.matvec(m, v)
            assert fp.mink(w, w) == fp.mink(v, v)
    assert fp.is_lorentz(fp.matmul(maps[0], maps[2]))
    shear = ((F(1), F(0), F(0)), (F(0), F(1), F(1)), (F(0), F(0), F(1)))
    assert not fp.is_lorentz(shear)


def test_thomas_wigner_split_exactly():
    b, (c, s) = fp.wigner(_THOMAS)
    assert (c, s) == (F(15, 17), F(-8, 17))
    assert b == fp.boost_to((F(25, 9), F(-20, 9), F(-4, 3)))
    assert fp.is_symmetric(b) and not fp.is_symmetric(_THOMAS)
    assert fp.matmul(b, fp.rot(c, s)) == _THOMAS
    assert fp.matvec(_THOMAS, (F(1), F(0), F(0))) == \
        (F(25, 9), F(-20, 9), F(-4, 3))


def test_one_pair_refused_three_answered():
    one = fp.solve(_pairs(_THOMAS, _XS[:1]), _Q)
    assert one["status"] != "answered" and one["answer"] is None
    three = fp.solve(_pairs(_THOMAS, _XS), _Q)
    assert three["status"] == "answered"
    assert three["answer"] == fp.matvec(_THOMAS, _Q) == \
        (F(43, 9), F(-29, 9), F(-7, 3))
    assert three["wigner"] == (F(15, 17), F(-8, 17))
    assert three["pure_boost"] is False


def test_a_reflection_seen_on_a_plane_is_refused():
    r = fp.solve(_pairs(fp.PARITY, _XS[:2]), (F(2), F(0), F(1)))
    assert r["status"] == "outside_span" and r["answer"] is None
    assert r["rank"] == 2
    assert "identity" in r["live"]
    ok, text, fig = fp.plane_text(_pairs(fp.PARITY, _XS[:2]),
                                  (F(2), F(0), F(1)))
    assert not ok and fig["status"] == "outside_span"
    assert "span" in text


def test_tool_frame_routes_by_component_count():
    arg3 = " ; ".join(fps.TOOL_PAIRS) + f" ? {fps.TOOL_QUERY}"
    t = run_tool(f"tool frame {arg3}")
    assert t.ok and t.figures.get("dimensions") == "1+2"
    assert t.figures.get("answer") == "43/9,-29/9,-7/3"
    assert t.figures.get("wigner") == fps.TOOL_WIGNER
    assert fp.frame_tool_text(arg3)[2]["dimensions"] == "1+2"
    for arg2 in ("1,0 -> 5/3,-4/3 ; 2,1 -> 2,-1 ? 3,1",
                 "1,0 -> 5/3,-4/3 ? 3,1"):
        want = fo.frame_text(arg2)
        got = run_tool(f"tool frame {arg2}")
        assert (got.ok, got.figures.get("status"), got.figures.get("answer")) \
            == (want[0], want[2].get("status"), want[2].get("answer"))
        assert fp.frame_tool_text(arg2) == want
        assert got.figures.get("dimensions") != "1+2"


def test_stored_measurement_when_current():
    r = fps.current()
    if r is None:
        return
    for mark in ("P1", "P2", "P3", "P5", "P6", "T"):
        assert r["marks"][mark], mark
    t = r["synthetic"]["totals"]["shipped"]
    assert t["inside"]["wrong"] == 0 and t["outside"]["wrong"] == 0
    th = r["synthetic"]["thomas"]
    assert th["wigner_exact"] == th["right"] == th["not_pure"]
