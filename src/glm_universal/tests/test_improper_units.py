"""Tests for improper Lorentz maps times a change of units in ``tool frame``
(Phase 181).

*Created 22 October 2026.*

``studies/IMPROPER_UNITS_STUDY.md`` declared the marks. These tests pin:

* the **Lean file** states its theorems with no ``sorry`` and is audited;
* the **gate**: twice a reflection, three halves of time reversal, and a
  scaled ``P . T`` are answered from three pairs, each named by component and
  scale; seen on a plane only, they are refused;
* **no answer changes**: on a reproducible sample the Phase 179 family set's
  answers are the shipped set's;
* the **stored measurement**, when current, meets every mark.
"""

from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path

from glm_universal.reasoning import frame_plane as fp
from glm_universal.reasoning import improper_units_study as ius
from glm_universal.runtime.toolbox import run_tool

_ROOT = Path(__file__).resolve().parents[2] / "lean"
_XS = [(F(1), F(0), F(0)), (F(2), F(1), F(0)), (F(2), F(0), F(1))]
_Q = (F(3), F(1), F(1))


def _scaled(s, m):
    return tuple(tuple(s * v for v in row) for row in m)


def _pairs(m, inputs):
    return [(x, fp.matvec(m, x)) for x in inputs]


def test_lean_file_states_the_theorems_without_sorry():
    text = (_ROOT / fp.LEAN_FILE_UNITS).read_text(encoding="utf-8")
    for name in fp.LEAN_THEOREMS_UNITS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    audit = (_ROOT / "RequestProject" / "GLM" / "AxiomAuditAll.lean").read_text(
        encoding="utf-8")
    assert "import RequestProject.GLM.LorentzUnits" in audit


def test_scaled_improper_maps_are_answered_and_named():
    cases = ((F(2), fp.PARITY, "lorentz_parity"),
             (F(3, 2), fp.TIME_REV, "lorentz_time"),
             (F(5, 3), fp.matmul(fp.PARITY, fp.TIME_REV), "lorentz_pt"))
    for s, m, name in cases:
        sm = _scaled(s, m)
        r = fp.solve(_pairs(sm, _XS), _Q)
        assert r["status"] == "answered"
        assert r["answer"] == fp.matvec(sm, _Q)
        assert r["component"] == name and r["scale"] == s


def test_on_a_plane_they_are_refused():
    sm = _scaled(F(2), fp.PARITY)
    r = fp.solve(_pairs(sm, _XS[:2]), _XS[2])
    assert r["status"] == "outside_span"
    assert r["ask"] == _XS[2]


def test_the_tool_says_the_scale():
    ok = run_tool("tool frame 1,0,0 -> 2,0,0 ; 2,1,0 -> 4,2,0 ; "
                  "2,0,1 -> 4,0,-2 ? 3,1,1")
    assert ok.ok and ok.figures["answer"] == "6,2,-2"
    assert ok.figures["component"] == "lorentz_parity"
    assert ok.figures["scale"] == "2"
    assert "conformal_split" in ok.text


def test_phase_179_answers_unchanged_on_a_sample():
    for fam in ius.REGRESSION + ius.OUT_VOCAB:
        for q in range(4):
            pairs, (qx, _qy), _m, _sc = ius._task(fam, q + 3000, 3)
            old = fp.solve(pairs, qx, families=fp.PHASE_179_FAMILIES)
            new = fp.solve(pairs, qx)
            if old["status"] == "answered":
                assert new["status"] == "answered"
                assert new["answer"] == old["answer"]


def test_stored_measurement_meets_every_mark():
    report = ius.improper_units_report()
    if not report.get("available"):
        return
    assert report["met"] == report["taken"] == 8
    assert report["synthetic"]["changed"] == []
