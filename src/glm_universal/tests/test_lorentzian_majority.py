"""Tests for the declared majority rule for conflicting evidence (Phase 184).

*Created 23 October 2026.*

``studies/LORENTZIAN_MAJORITY_STUDY.md`` declared the marks. These tests pin:

* the **Lean file** states the quoted theorems with no ``sorry`` and is
  audited;
* the **rule** against its definition: a target answers exactly when its
  agreeing group holds a strict majority of the weight, at most one can, and
  a negative weight is refused;
* the **soundness condition** and its tightness on small hand-made sets;
* ``tool majority``: a strict majority answers and names the outvoted
  examples, one against one is refused, agreeing examples answer as
  ``tool evidence`` does;
* the **stored measurement**, when current, records its marks.

No test imports pytest, so the file runs by hand as well.
"""

from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path

from glm_universal.reasoning import lorentzian_majority as lm
from glm_universal.reasoning import lorentzian_majority_study as lms
from glm_universal.runtime.toolbox import run_tool

_ROOT = Path(__file__).resolve().parents[2] / "lean"


def test_lean_file_states_the_theorems_without_sorry():
    text = (_ROOT / lm.LEAN_FILE).read_text(encoding="utf-8")
    for name in lm.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    audit = (_ROOT / "RequestProject" / "GLM" / "AxiomAuditAll.lean").read_text(
        encoding="utf-8")
    assert "import RequestProject.GLM.LorentzianMajority" in audit


def test_rule_matches_its_definition():
    m = lm.majority(["a", "b", "a"])
    assert m["status"] == "majority" and m["value"] == "a"
    assert m["share"] == F(2, 3) and m["decoys_needed"] == 2
    assert lm.majority(["a", "b"])["status"] == "no_majority"
    assert lm.majority(["a", "b", "c"])["status"] == "no_majority"
    assert lm.majority(["a", "a", "b", "b"])["status"] == "no_majority"
    # weights: one heavy cue outweighs two light ones
    assert lm.majority(["a", "b", "b"], [3, 1, 1])["value"] == "a"
    assert lm.majority(["a", "b", "b"], [2, 1, 1])["status"] == "no_majority"
    assert lm.majority(["a", "b"], [F(1, 2), 0])["value"] == "a"
    try:
        lm.majority(["a", "b"], [1, -1])
    except ValueError:
        pass
    else:
        raise AssertionError("a negative weight must be refused")


def test_soundness_condition_and_tightness():
    # honest at least half: never wrong
    for targets in (["d", "e"], ["d", "d", "e", "f"], ["d", "d", "e", "e"]):
        assert lm.majority(targets)["value"] in (None, "d")
    # honest strictly more than half: right
    for targets in (["d"], ["d", "d", "e"], ["d", "e", "d", "f", "d"]):
        assert lm.majority(targets)["value"] == "d"
    # below half, decoys agreeing: the rule is carried (majority_misled)
    assert lm.majority(["d", "e", "e"])["value"] == "e"
    # below half, decoys disagreeing: refused
    assert lm.majority(["d", "e", "e", "f", "g"])["status"] == "no_majority"


def test_tool_majority():
    r = run_tool("tool majority velocity : acceleration, length : velocity, "
                 "mass : density :: momentum")
    assert r.ok and r.figures["status"] == "class"
    assert r.figures["support"] == 2 and r.figures["outvoted"] == 1
    assert "force" in r.text and "Outvoted: mass : density" in r.text
    r = run_tool("tool majority velocity : acceleration, mass : density "
                 ":: momentum")
    assert not r.ok and r.figures["status"] == "no_majority"
    r = run_tool("tool majority velocity : acceleration, energy : power "
                 ":: momentum")
    e = run_tool("tool evidence velocity : acceleration, energy : power "
                 ":: momentum")
    assert r.ok and e.ok and r.figures["class_size"] == e.figures["class_size"]
    assert not run_tool("tool majority nonsense").ok


def test_stored_measurement_when_current():
    report = lms.lorentzian_majority_report()
    if not report.get("available"):
        return
    assert report["taken"] == len(report["marks"])
    for m in ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "L"):
        assert report["marks"][m], m


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
