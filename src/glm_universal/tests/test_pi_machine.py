"""Tests for the machine summing ``pi`` by Machin's formula (Phase 166).

*Created 19 October 2026.*

``studies/PI_MACHINE_STUDY.md`` pre-registered its marks.  These tests pin:

* the **Lean file**: ``PiMachine.lean`` states the theorems of §1 and has no
  ``sorry``;
* the **machine**: GLM-BAT, run on the program's ``pi`` lines, leaves the
  four integers of ``piEnds`` -- and the Python mirror of ``piEnds`` agrees
  with what Lean itself evaluates;
* the **enclosure**: nested strictly inside Mathlib's twenty-digit decimals,
  and certifying every continued-fraction term the tool answers;
* the **control**: a wrong Machin formula (``237`` for ``239``) is caught by
  Mathlib's decimals;
* the **switch**: with it off, ``pi`` is the declared constant again.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import pi_machine_study as pms
from glm_universal.reasoning import tool_machine as tm

_ROOT = Path(__file__).resolve().parents[3]
_GLM = _ROOT / "src" / "lean" / "RequestProject" / "GLM"


def test_lean_file_states_the_theorems_without_sorry():
    text = (_GLM / "PiMachine.lean").read_text(encoding="utf-8")
    for name in tm.PI_LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    assert pms.lean_marks()["met"]


def test_machine_leaves_the_lean_ends():
    m = pms.machine_marks()
    assert m["status"] == "halted" and m["exit"] == 0
    assert m["ends_equal"] and m["lean_eval_equal"]


def test_enclosure_nested_and_certifies_the_tools_terms():
    assert pms.enclosure_marks()["met"]
    t = pms.term_marks()
    assert t["summed_terms"] >= pms.MAX_TERM > t["declared_terms"]
    assert t["tool_agrees"] is True


def test_wrong_formula_is_caught():
    assert pms.control_marks()["disjoint"]


def test_switch_off_restores_the_declared_constant():
    class _B:
        lines: list = []
    b = _B()
    b.lines = []
    with pms.switch(False):
        tm._enclose(b, "pi", 0)
    assert f"SET /A XLA={tm.PI_LOW[0]}" in b.lines
    b.lines = []
    tm._enclose(b, "pi", 0)
    assert any("PISUMF0" in x for x in b.lines)
    lo, hi = tm.pi_ends(*tm.PI_TERMS)
    assert Fraction(*lo) < Fraction(*hi)
