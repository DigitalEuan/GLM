"""Tests for the Lorentzian lift of the Golay tie space (Phase 182).

*Created 22 October 2026.*

``studies/LORENTZIAN_LIFT_STUDY.md`` declared the marks. These tests pin:

* the **Lean files** state the quoted theorems with no ``sorry`` and are
  audited;
* the **identities** the Lean file proves, checked on exact samples: the lift
  is null, ``<L x, w> = -1``, the script's ``w`` is ``2 L(0)``, roots have
  norm 2, and ``<L x, r_l> = 1 - |x - l|^2 / 2``;
* a **Golay tie is a deep hole**: 48 vertices, certified ``A_1^24``, every
  vertex root orthogonal to the lift, ``2 L(x)`` in ``II_25,1``;
* the **no-go**: the tie's reflection fixes the tied point and swaps the
  candidates;
* **resolution needs a second reading**: one reading is refused, two
  readings of the same message are resolved, ``tool lorentz`` says so;
* the **stored measurement**, when current, records its marks.
"""

from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path

from glm_universal.reasoning import deep_holes as dh
from glm_universal.reasoning import lorentzian_lift as ll
from glm_universal.reasoning import lorentzian_lift_study as lls
from glm_universal.runtime.toolbox import run_tool

_ROOT = Path(__file__).resolve().parents[2] / "glm_lean"
_TETRAD = 0b1111


def test_lean_files_state_the_theorems_without_sorry():
    text = "".join((_ROOT / f).read_text(encoding="utf-8")
                   for f in ll.LEAN_FILES)
    for name in ll.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    audit = (_ROOT / "RequestProject" / "GLM" / "AxiomAuditAll.lean").read_text(
        encoding="utf-8")
    assert "import RequestProject.GLM.LorentzianLift" in audit
    assert "import RequestProject.GLM.GolayDeepHole" in audit


def test_lift_identities():
    xs = [tuple([0] * 24), ll.doubled(_TETRAD), tuple(range(24)),
          tuple([F(1, 3)] * 12 + [F(-5, 2)] * 12)]
    for x in xs:
        lx = ll.lift(x)
        assert ll.inner(lx, lx) == 0
        assert ll.inner(lx, ll.WEYL) == -1
        for p in xs:
            r = ll.root(p)
            assert ll.inner(r, r) == 2
            assert ll.inner(r, ll.WEYL) == -1
            d2 = sum((F(a) - F(b)) ** 2 for a, b in zip(x, p)) / ll.SCALE
            assert ll.inner(lx, r) == 1 - d2 / 2
    assert ll.SCRIPT_W == tuple(2 * v for v in ll.lift(tuple([0] * 24)))
    assert ll.inner(ll.WEYL, ll.WEYL) == 0


def test_golay_tie_is_an_a1_24_deep_hole():
    cert = ll.tie_certificate(_TETRAD)
    assert cert["ambiguous"] and cert["coset_weight"] == 4
    assert cert["vertices"] == 48 and cert["per_candidate"] == 8
    assert cert["vertex_distance2_raw"] == [16]
    assert cert["roots_orthogonal_to_lift"]
    assert cert["null_vector_in_ii"] and not cert["lift_in_ii"]
    diag = dh.hole_diagram(ll.hole_vertices(_TETRAD), ll.doubled(_TETRAD))
    assert diag["root_system"] == "A_1^24"
    assert diag["completeness_certificate"]["certified"]


def test_the_tie_reflection_fixes_the_point_and_swaps_the_candidates():
    cert = ll.tie_certificate(_TETRAD)
    a, b = cert["candidates"][:2]
    ra, rb = ll.root(ll.doubled(a)), ll.root(ll.doubled(b))
    mirror = ll._sub(ra, rb)
    lx = ll.lift(ll.doubled(_TETRAD))
    assert ll.reflect(mirror, lx) == lx
    assert ll.reflect(mirror, ra) == rb


def test_one_reading_refused_two_resolved():
    one = ll.resolve([_TETRAD])
    assert one["status"] == "tied" and len(one["best"]) == 6
    two = ll.resolve([_TETRAD, 0])
    assert two["status"] == "resolved" and two["value"] == 0
    r = run_tool("tool lorentz 15")
    assert not r.ok and "deep hole" in r.text
    r = run_tool("tool lorentz 15; 0")
    assert r.ok and r.figures["value"] == 0


def test_stored_measurement_when_current():
    report = lls.lorentzian_lift_report()
    if not report.get("available"):
        return
    assert report["taken"] == len(report["marks"])
    for m in ("M1", "M3", "M4", "M5", "M6", "M9", "M10", "L"):
        assert report["marks"][m], m
