"""Tests for the build-enforced axiom audit (Phase 176).

*Created 21 October 2026.*

``RequestProject/GLM/AxiomGuard.lean`` defines ``#guard_axioms``,
``#guard_axioms_prefix`` and ``#guard_axioms_development``;
``AxiomAuditAll.lean`` imports every Lean file of the development and runs
the last, so ``lake build`` fails if any theorem anywhere rests on a
non-standard axiom (or on ``sorry``).  That only covers every file if the
import list does, which is what these tests pin.  The kit's audit
(``PipelineKit/AxiomAudit.lean``) guards the same 25 names as the owner's
``GLMKit/AxiomAudit.lean``.
"""

from __future__ import annotations

import re
from pathlib import Path

_LEAN = Path(__file__).resolve().parents[2] / "glm_lean"
_GLM = _LEAN / "RequestProject" / "GLM"
_KIT = Path(__file__).resolve().parents[3] / "source_material" / \
    "GLM_Pipeline_Kit" / "GLMKit" / "AxiomAudit.lean"


def _module(p: Path) -> str:
    return ".".join(p.relative_to(_LEAN).with_suffix("").parts)


def test_whole_development_audit_imports_every_file():
    text = (_GLM / "AxiomAuditAll.lean").read_text(encoding="utf-8")
    imported = set(re.findall(r"^import (\S+)", text, re.M))
    every = {_module(p) for p in (_LEAN / "RequestProject").rglob("*.lean")}
    every.discard("RequestProject.GLM.AxiomAuditAll")
    assert every - imported == set(), sorted(every - imported)[:10]
    assert "#guard_axioms_development" in text


def test_guard_rejects_sorry_and_hand_axioms():
    text = (_GLM / "AxiomGuard.lean").read_text(encoding="utf-8")
    for name in ("propext", "Classical.choice", "Quot.sound",
                 "Lean.ofReduceBool", "Lean.trustCompiler"):
        assert f"``{name}" in text, name
    assert "sorryAx" in text          # documented as rejected
    # the project's sorry scan greps whole words; the guard's files must pass it
    for f in ("AxiomGuard.lean", "AxiomAuditAll.lean", "PipelineKit/AxiomAudit.lean"):
        body = (_GLM / f).read_text(encoding="utf-8")
        assert not re.search(r"\bsorry\b", body), f


def test_kit_audit_guards_the_owner_list():
    owner = set(re.findall(r"#print axioms (\w+)", _KIT.read_text(encoding="utf-8")))
    assert len(owner) == 25
    ours = (_GLM / "PipelineKit" / "AxiomAudit.lean").read_text(encoding="utf-8")
    block = ours.split("#guard_axioms", 1)[1].split("open GLM.PipelineInduction")[0]
    assert set(re.findall(r"\w+", block)) >= owner
