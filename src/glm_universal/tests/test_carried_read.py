"""Tests for the machine reading what it carries (Phase 153).

*Created 31 October 2026 (repository check: the original test file was lost
in the October 2026 reorganisation; written from its row in
tests/README.md and studies/CARRIED_READ_STUDY.md).*

These tests pin:

* the **Lean file**: ``CarriedRead.lean`` states the theorems of §1 and has
  no ``sorry``;
* the **register files**: unique keys; ``FIND`` finds an entry and not its
  altered value; the element snapshot agrees with the loaded register;
* **one chain with reads**: admitted, with register reads, question reads
  and computed steps; a lie at a register read found at its own step and
  rolled back;
* the **typed planner** and **field** gates: an honest answer admitted, an
  altered one refused as ``MACHINE_DRIFT``;
* the **stored measurement** and its marks.
"""

from __future__ import annotations

from glm_universal import constants
from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import carried_read_study as crs
from glm_universal.reasoning import planner_ladder as pl
from glm_universal.reasoning import register_files as rf
from glm_universal.reasoning import typed_ladder as tl

TEXT = "what is the atomic number of iron times 2"

_memo: dict = {}


def _session():
    if "session" not in _memo:
        from glm_universal.runtime.session import GeometricSession
        _memo["session"] = GeometricSession()
    return _memo["session"]


def _files():
    return rf.register_files(_session())


def _chain():
    if "chain" not in _memo:
        from glm_universal.runtime import stepwise as sw
        a = sw.answer(_session(), TEXT)
        assert a.answered, TEXT
        _memo["chain"] = a.chain
    return _memo["chain"]


def _run(lines, files):
    return bm.run_program(bm.parse_program(lines), None, files, (),
                          budget=10000, inert=False, jump=False)


def test_lean_file_states_the_theorems_without_sorry():
    text = constants.lean_file(crs.LEAN_FILE).read_text(encoding="utf-8")
    for name in crs.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text


def test_register_files_have_unique_keys():
    reg = _files()
    assert reg["tables"] and sum(t["entries"] for t in reg["tables"]) > 0
    for t in reg["tables"]:
        lines = reg["files"][t["path"]]
        keys = [x.split("=", 1)[0] for x in lines]
        assert len(keys) == len(set(keys)) and t["duplicated"] == 0
        assert all(x.startswith("@") and x.endswith(";") for x in lines)
    names = {t["table"] for t in reg["tables"]}
    assert not names & set(rf.NOT_REGISTERS)


def test_find_finds_an_entry_and_not_its_altered_value():
    reg = _files()
    path = rf.table_path("element")
    line = rf.entry_line("Fe", "z", 26)
    assert line == "@Fe.z=26;" and line in reg["files"][path]
    found, altered = crs.find_programs(path, (line,))
    files = {path: reg["files"][path]}
    assert _run(found, files).exit_code == 0
    assert _run(altered, files).exit_code == 0       # the altered one unseen
    miss = [f'FIND "@Fe.z=27;" < {path} || EXIT /B 2', "EXIT /B 0"]
    assert _run(miss, files).exit_code == 2


def test_the_element_snapshot_agrees_with_the_register():
    snap = _files()["snapshot"]
    assert snap["pairs"] > 0 and snap["agree"] == snap["pairs"]
    assert snap["differ"] == []


def test_one_chain_with_reads_is_admitted():
    chain = _chain()
    c = pl.check_chain(chain, say=False, read=True)
    assert c["admitted"]
    assert c["read_register"] and c["read_question"]
    assert len(chain.steps) in c["computed"]
    assert c["carried"] == []


def test_a_register_lie_is_found_at_its_step_and_rolled_back():
    chain = _chain()
    c = pl.check_chain(chain, say=False, read=True)
    k = c["read_register"][-1]
    d = pl.check_chain(pl.lie_chain(chain, k, chain.steps[k - 1].value + 1),
                       say=False, read=True)
    assert d["first_drift"] == k
    assert d["exit"] == 2
    assert not d["promoted"] and d["rolled_back"]


def test_the_typed_planner_gate():
    from glm_universal.runtime import semantic_plan as sp
    planned = sp.plan_question(_session(), "what is the gcd of 12 and 18")
    c = tl.plan_check(planned)
    assert c is not None and c["admitted"] and c["refusal"] == ""
    assert c["last_computed"]
    lie = tl.typed_lie(c["chain"])
    d = pl.check_chain(lie, say=False, read=True)
    assert not d["admitted"]
    assert d["first_drift"] == len(lie.steps)


def test_the_field_gate():
    held = _session().field_surface.field("z", "Fe")
    assert held.table == "element"
    c = tl.field_check(held, files=_files()["files"])
    assert c["admitted"] and c["refusal"] == "" and c["read_register"] == [1]
    d = tl.field_check(held, files=_files()["files"],
                       value=tl.field_lie(held.value))
    assert not d["admitted"] and d["refusal"] == tl.REFUSAL == "MACHINE_DRIFT"


def test_the_stored_measurement_and_its_marks():
    assert crs.state()["verdict"] == "current"
    r = crs.carried_read_report()
    assert r["available"]
    marks = r["marks"]
    for name in ("R1", "R2", "C1", "C2", "C3", "C4", "C5", "T1", "T2", "S1",
                 "S2"):
        assert marks[name], name
    c, t, f = r["chains"], r["typed"], r["fields"]
    assert c["admitted"] == c["chains"] > 0
    assert c["reg_found"] == c["reg_lies"] > 0
    assert c["q_found"] == c["q_lies"] - c["q_in_question"]
    assert t["admitted"] == t["said"] > 0 and t["refused"] == t["lies"]
    assert f["admitted"] == f["read"] > 0 and f["refused"] == f["lies"]
    assert r["registers"]["duplicated"] == 0
    # F1 is reported, never assumed: met only when measured
    assert marks["F1"] == bool(r["frozen"]["measured"] and
                               r["frozen"]["same_text"] ==
                               r["frozen"]["texts"] > 0)
