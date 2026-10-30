"""Tests for the Lorentzian evidence space (Phase 183).

*Created 23 October 2026.*

``studies/LORENTZIAN_EVIDENCE_STUDY.md`` declared the marks. These tests pin:

* the **Lean file** states the quoted theorems with no ``sorry`` and is
  audited;
* the **identities** it proves, on exact samples: the decomposition
  ``V = W L(xbar) + (D/2) w``, ``<V, V> = -W D``, null exactly when the cues
  agree, and analogy as evidence with weights ``1, -1, 1``;
* the **settling question** of a Golay tie: five positions, one per tetrad,
  settle every candidate, and the revealed bits pick the sent codeword;
* the **certificate guard** refuses an answer outside the first reading's
  tie;
* ``tool evidence``: agreeing examples give the dimension class and its
  names, disagreeing examples are refused;
* the **stored measurement**, when current, records its marks.

No test imports pytest, so the file runs by hand as well.
"""

from __future__ import annotations

from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

from glm_universal.reasoning import lorentzian_evidence as le
from glm_universal.reasoning import lorentzian_evidence_study as les
from glm_universal.reasoning import lorentzian_lift as ll
from glm_universal.runtime.toolbox import run_tool

_ROOT = Path(__file__).resolve().parents[2] / "lean"
_TETRAD = 0b1111


def test_lean_file_states_the_theorems_without_sorry():
    text = (_ROOT / le.LEAN_FILE).read_text(encoding="utf-8")
    for name in le.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    audit = (_ROOT / "RequestProject" / "GLM" / "AxiomAuditAll.lean").read_text(
        encoding="utf-8")
    assert "import RequestProject.GLM.LorentzianEvidence" in audit


def test_decomposition_and_norm():
    pts = [(F(1), F(-2), F(3, 2)), (F(0), F(5), F(-1, 3)), (F(2), F(2), F(2))]
    for ws in ((1, 1, 1), (1, 2, 3), (3, 1, 1)):
        cues = [(p, F(w)) for p, w in zip(pts, ws)]
        assert le.decomposition_holds(cues)
        V = le.evidence(cues)
        assert le.inner(V, V) == -le.weight(cues) * le.dispersion(cues)
        assert le.dispersion(cues) > 0
    same = [(pts[0], F(1)), (pts[0], F(2))]
    V = le.evidence(same)
    assert le.dispersion(same) == 0 and le.inner(V, V) == 0
    golay = [(tuple(F(v) for v in ll.doubled(m)), F(1)) for m in (0, 15, 255)]
    assert le.decomposition_holds(golay, ll.SCALE)


def test_analogy_is_evidence():
    a, b, c = (F(1), F(0), F(2)), (F(3), F(1), F(0)), (F(0), F(4), F(1))
    cues = le.analogy_cues(a, b, c)
    assert le.weight(cues) == 1
    assert le.consensus(cues) == tuple(z + y - x for x, y, z in zip(a, b, c))
    assert le.decomposition_holds(cues)


def test_evidence_ranks_by_the_consensus():
    cues = [((F(0), F(0)), F(1)), ((F(2), F(0)), F(1))]
    cand = {"left": (F(0), F(0)), "mid": (F(1), F(2)), "right": (F(2), F(0))}
    res = le.decide(cues, cand)
    assert res["status"] == "tied" and res["best"] == ["left", "right"]
    cues.append(((F(2), F(1)), F(1)))
    assert le.decide(cues, cand)["value"] == "right"
    assert le.decide(cues, cand, budget=F(1))["status"] == "conflicting"


def test_the_settling_question_of_a_golay_tie():
    blocks = le.sextet_blocks(_TETRAD)
    assert len(blocks) == 6
    union = 0
    for _, blk in blocks:
        assert bin(blk).count("1") == 4 and union & blk == 0
        union |= blk
    q = le.settling_question(_TETRAD)
    assert len(q) == 5
    for c, _ in blocks:
        st = le.settle(_TETRAD, {i: (c >> i) & 1 for i in q})
        assert st["status"] == "resolved" and st["value"] == c
    for sub in combinations(q, 4):
        assert any(le.settle(_TETRAD, {i: (c >> i) & 1 for i in sub})["status"]
                   != "resolved" for c, _ in blocks)
    assert le.settling_question(0) == []


def test_tool_lorentz_asks_and_reads_the_bits():
    r = run_tool("tool lorentz 15")
    assert not r.ok and r.figures["ask"] == le.settling_question(15)
    bits = " ".join(f"{i}=0" for i in r.figures["ask"])
    r = run_tool(f"tool lorentz 15; @{bits}")
    assert r.ok and r.figures["value"] == 0


def test_certificate_guard_refuses_outside_the_tie():
    first = _TETRAD
    tied = set(c for c, _ in le.sextet_blocks(first))
    found = None
    for second in range(1, 1 << 12):
        res = ll.resolve([first, second << 12], guard=ll.GUARD)
        if res["value"] is not None and res["value"] not in tied:
            found = second << 12
            break
    if found is not None:
        res = le.certificate_resolve([first, found])
        assert res["status"] == "outside_certificate" and res["value"] is None


def test_tool_evidence():
    r = run_tool("tool evidence velocity : acceleration, energy : power "
                 ":: momentum")
    assert r.ok and r.figures["status"] == "class"
    assert "force" in r.text
    r = run_tool("tool evidence velocity : acceleration, mass : density "
                 ":: momentum")
    assert not r.ok and r.figures["status"] == "conflicting"
    r = run_tool("tool evidence length : wavenumber, time : frequency :: mass")
    assert not r.ok and r.figures["status"] == "conflicting"


def test_stored_measurement_when_current():
    report = les.lorentzian_evidence_report()
    if not report.get("available"):
        return
    assert report["taken"] == len(report["marks"])
    for m in ("E1", "G1", "G2", "G3", "G4", "G5b", "G6", "P1", "P2", "L"):
        assert report["marks"][m], m


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
