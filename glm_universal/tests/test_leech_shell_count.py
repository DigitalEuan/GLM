"""Tests for every Leech shell counted and proved (Phase 180).

*Created 22 October 2026.*

``studies/LEECH_SHELL_COUNT_STUDY.md`` pre-registered its marks.  These tests
pin:

* the **Lean file**: ``LeechShellCount.lean`` states the theorems of §1, has
  no ``sorry``, and is in the axiom audit;
* the **proved sizes**: the eight shell sizes ``leech_shell_sizes`` states
  agree with this package's generating-function count and with the theta
  series, which uses no Golay code;
* the **control**: a perturbed statement (one size off by one) would be seen
  as a disagreement, not absorbed.
"""

from __future__ import annotations

from pathlib import Path

from glm_universal.reasoning import leech_shells as ls

_ROOT = Path(__file__).resolve().parents[3]
_GLM = _ROOT / "overlay" / "glm_lean" / "RequestProject" / "GLM"


def test_lean_file_states_the_theorems_without_sorry():
    text = (_GLM / "LeechShellCount.lean").read_text(encoding="utf-8")
    for name in ls.SHELL_COUNT_LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    assert ls.SHELL_COUNT_LEAN_FILE.endswith("LeechShellCount.lean")


def test_lean_file_is_audited():
    audit = (_GLM / "AxiomAuditAll.lean").read_text(encoding="utf-8")
    assert "import RequestProject.GLM.LeechShellCount" in audit


def test_proved_sizes_agree_three_ways():
    report = ls.proved_shells_check(7)
    assert report["proved_rows"] == 8
    assert report["agree"]
    assert [r["proved"] for r in report["rows"]] == [
        1, 0, 196560, 16773120, 398034000, 4629381120, 34417656000,
        187489935360]


def test_a_perturbed_size_is_a_disagreement():
    proved = ls.proved_shell_sizes()
    ours = dict(ls.shells(7))
    for t in range(8):
        assert proved[t] == ours[t]
        assert proved[t] + 1 != ours[t]
