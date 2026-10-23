"""Tests for improper maps in ``tool frame`` (Phase 179).

*Created 22 October 2026.*

``studies/IMPROPER_FRAME_STUDY.md`` declared the marks. These tests pin:

* the **Lean file** states its theorems with no ``sorry``;
* the **arithmetic** mirrors ``LorentzImproper.lean``: parity and time
  reversal are Lorentz maps of determinant ``-1``; every Lorentz map lies in
  one of four components and splits as ``B . P^a . T^b``;
* the **gate**: a reflection, time reversal and both are answered from three
  pairs and named by component; seen on a plane only, a reflection is still
  refused, the refusal citing ``plane_partner``;
* **no answer changes**: on a reproducible sample the Phase 178 family set's
  answers are the shipped set's;
* the **stored measurement**, when current, meets every mark.
"""

from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path

from glm_universal.reasoning import frame_plane as fp
from glm_universal.reasoning import improper_frame_study as ifs
from glm_universal.runtime.toolbox import run_tool

_ROOT = Path(__file__).resolve().parents[2] / "glm_lean"
_XS = [(F(1), F(0), F(0)), (F(2), F(1), F(0)), (F(2), F(0), F(1))]
_Q = (F(3), F(1), F(1))


def _pairs(m, inputs):
    return [(x, fp.matvec(m, x)) for x in inputs]


def test_lean_file_states_the_theorems_without_sorry():
    text = (_ROOT / fp.LEAN_FILE_IMPROPER).read_text(encoding="utf-8")
    for name in fp.LEAN_THEOREMS_IMPROPER:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text


def test_parity_and_time_reversal_are_improper_lorentz():
    for m in (fp.PARITY, fp.TIME_REV, fp.reflect(F(3, 5), F(4, 5))):
        assert fp.is_lorentz_any(m) and fp.det(m) == -1
    assert fp.component(fp.PARITY) == "lorentz_parity"
    assert fp.component(fp.TIME_REV) == "lorentz_time"
    assert fp.component(fp.matmul(fp.PARITY, fp.TIME_REV)) == "lorentz_pt"
    assert fp.component(fp.IDENT) == "lorentz"
    shear = ((F(1), F(0), F(0)), (F(0), F(1), F(1)), (F(0), F(0), F(1)))
    assert fp.component(shear) is None


def test_split_recomposes():
    lor = fp.matmul(fp.boost_x(F(1, 3)), fp.rot(F(3, 5), F(4, 5)))
    for a in (0, 1):
        for t in (0, 1):
            m = lor
            if a:
                m = fp.matmul(m, fp.PARITY)
            if t:
                m = fp.matmul(m, fp.TIME_REV)
            b, aa, tt = fp.improper_split(m)
            assert (aa, tt) == (a, t) and b == lor and fp.is_lorentz(b)


def test_gate_answers_each_component_from_three_pairs():
    lor = fp.matmul(fp.boost_x(F(1, 2)), fp.boost_y(F(1, 2)))
    cases = {"lorentz_parity": fp.matmul(lor, fp.PARITY),
             "lorentz_time": fp.matmul(lor, fp.TIME_REV),
             "lorentz_pt": fp.matmul(fp.matmul(lor, fp.PARITY), fp.TIME_REV)}
    for name, m in cases.items():
        r = fp.solve(_pairs(m, _XS), _Q)
        assert r["status"] == "answered", name
        assert r["answer"] == fp.matvec(m, _Q)
        assert r["component"] == name
        assert r["split"]["wigner"] == (F(15, 17), F(-8, 17))


def test_reflection_on_a_plane_still_refused():
    r = fp.solve(_pairs(fp.PARITY, _XS[:2]), (F(2), F(0), F(1)))
    assert r["status"] == "outside_span"
    assert "identity" in r["live"] and "lorentz_parity" in r["live"]
    t = run_tool("tool frame 1,0,0 -> 1,0,0 ; 2,1,0 -> 2,1,0 ? 2,0,1")
    assert not t.ok and "plane_partner" in t.text


def test_tool_frame_names_the_component():
    t = run_tool("tool frame 1,0,0 -> -1,0,0 ; 2,1,0 -> -2,1,0 ; "
                 "2,0,1 -> -2,0,1 ? 3,1,1")
    assert t.ok and t.figures.get("answer") == "-3,1,1"
    assert t.figures.get("component") == "lorentz_time"


def test_phase_178_answers_unchanged_on_a_sample():
    for fam in ifs.IMPROPER + ifs.PROPER + ifs.OUT_VOCAB:
        for q in range(3):
            pairs, (qx, _qy), _m = ifs._task(fam, q + 3000, 3)
            old = fp.solve(pairs, qx, families=fp.PHASE_178_FAMILIES)
            new = fp.solve(pairs, qx)
            if old["status"] == "answered":
                assert new["status"] == "answered"
                assert new["answer"] == old["answer"]


def test_stored_measurement_when_current():
    r = ifs.current()
    if r is None:
        return
    assert r["met"] == r["taken"]
    assert r["synthetic"]["changed"] == []
