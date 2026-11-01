"""Tests for the operations ladder in the stepwise planner (Phase 151).

*Created 31 October 2026 (repository check: the original test file was lost
in the October 2026 reorganisation; written from its row in
tests/README.md and studies/PLANNER_LADDER_STUDY.md).*

``studies/PLANNER_LADDER_STUDY.md`` pre-registered the marks.  These tests
pin:

* the **Lean file**: ``PlannerLadder.lean`` states the theorems of §1 and has
  no ``sorry``;
* **one chain**: said as GLM-BAT, read back from English to the identical
  lines, run to a halt with exit code 0, no drift, the gated pipeline
  promoted;
* **a lie** in a computed step: the drift is exactly that step and nothing
  is promoted (the seed files restored);
* **the gate**: a drifting chain is refused as ``MACHINE_DRIFT``
  (:func:`planner_ladder.gate`, what ``stepwise._ladder_gate`` calls);
* **the stored measurement**: current, and its marks as measured.
"""

from __future__ import annotations

from glm_universal import constants
from glm_universal.reasoning import planner_ladder as pl
from glm_universal.reasoning import planner_ladder_study as pls

TEXT = "what is the atomic number of iron plus the atomic number of oxygen"

_memo: dict = {}


def _chain():
    if "chain" not in _memo:
        from glm_universal.runtime import stepwise as sw
        from glm_universal.runtime.session import GeometricSession
        a = sw.answer(GeometricSession(), TEXT)
        assert a.answered, TEXT
        _memo["chain"] = a.chain
    return _memo["chain"]


def test_lean_file_states_the_theorems_without_sorry():
    path = constants.lean_file(pl.LEAN_FILE)
    text = path.read_text(encoding="utf-8")
    for name in pl.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    assert pls.lean_marks()["met"]


def test_one_chain_said_read_back_run_and_promoted():
    chain = _chain()
    c = pl.check_chain(chain, say=True, ladder=True)
    assert c["said"] is True
    assert c["status"] == "halted" and c["exit"] == 0
    assert c["drift"] == [] and c["first_drift"] is None
    assert c["promoted"] and c["admitted"]
    assert len(chain.steps) in c["computed"]
    words = pl.describe(c)
    assert words["drift"] == "drift: none"
    assert words["pipeline"] == "pipeline: promoted"
    assert len(words["program_lines"].splitlines()) == c["lines"]
    assert sorted(pl.column3_scripts(chain, c["ladder"])) == ["pipeline",
                                                              "run"]


def test_a_lie_in_a_computed_step_is_found_at_that_step():
    chain = _chain()
    c = pl.check_chain(chain, say=False)
    k = c["computed"][-1]
    lie = pl.value_lie(chain.steps[k - 1])
    assert lie is not None
    d = pl.check_chain(pl.lie_chain(chain, k, lie), say=False)
    assert d["drift"] == [pl.file_of(k)]
    assert d["first_drift"] == k
    assert not d["promoted"] and d["failed_at"] == "check"
    assert d["rolled_back"] and not d["admitted"]


def test_a_drifting_chain_is_refused_as_machine_drift():
    chain = _chain()
    honest = pl.gate(chain)
    assert honest["admitted"] and honest["refusal"] == ""
    k = len(chain.steps)
    lie = pl.lie_chain(chain, k, pl.value_lie(chain.steps[k - 1]))
    g = pl.gate(lie)
    assert not g["admitted"]
    assert g["refusal"] == pl.REFUSAL == "MACHINE_DRIFT"
    assert f"the first drift is step {k}" in g["reason"]


def test_the_stored_measurement():
    assert pls.state()["verdict"] == "current"
    r = pls.planner_ladder_report()
    assert r["available"]
    m, marks = r["machine"], r["marks"]
    for name in ("P1", "P2", "P3", "P4", "P5"):
        assert marks[name], name
    n = m["chains"]
    assert n > 0
    assert m["said"] == m["halted"] == m["no_drift"] == m["promoted"] == n
    assert m["lies_found"] == m["lies_rolled_back"] == m["lies"] > 0
    assert m["scripts_run"] == m["scripts_pipeline"] == n
    assert m["mutants_rejected"] == m["mutants"] == 2 * n
    # the frozen-path marks are reported, never assumed: not met while the
    # baseline and the answering-path gate are missing
    assert marks["F1"] is False and marks["F2"] is False
    assert r["met"] == sum(1 for v in marks.values() if v)
