"""Tests for the owner's pipeline kit in the GLM (Phase 175).

*Created 21 October 2026.*

``studies/PIPELINE_KIT_STUDY.md`` declared the marks.  These tests pin:

* the **Lean files**: ``PipelineInduction.lean`` states its theorems, and the
  kit's seven files are present, all without ``sorry``;
* the **bridge**: the kit's four substrate checks hold on the GLM's own
  ``leech2`` (a short run of the 2,000-word mark);
* the **operators**: the region fill and the two path writers on hand-made
  grids, and a permutation keeping weight;
* the **gate**: an answer when every fitting hypothesis agrees, a refusal
  when two disagree, a refusal when nothing fits, and the two-step search
  finding a composition no single operator fits;
* the **evidence guard**: one demonstration never fits an XOR mask;
* ``tool induce`` through the toolbox, answered and refused;
* the **stored measurement**, when current, meets every mark.
"""

from __future__ import annotations

from pathlib import Path

from glm_universal.reasoning import pipeline_kit as pk
from glm_universal.reasoning import pipeline_kit_study as pks

_ROOT = Path(__file__).resolve().parents[2] / "glm_lean"


def _g(text):
    return pk.parse_grid(text)


def test_lean_files_state_the_theorems_without_sorry():
    text = (_ROOT / pk.LEAN_FILE).read_text(encoding="utf-8")
    for name in pk.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    for f in pk.KIT_LEAN_FILES:
        body = (_ROOT / f).read_text(encoding="utf-8")
        assert "sorry" not in body, f


def test_bridge_holds_on_the_substrate():
    fails = pk.check_substrate(200)
    assert fails["trials"] == 200
    assert all(fails[k] == 0 for k in ("parity_wall", "parity_wall_glue",
                                       "eight_mul", "junction_parity"))


def test_operators_on_hand_made_grids():
    assert pk.fill_enclosed(_g("1111/1001/1111")) == _g("1111/1111/1111")
    assert pk.fill_enclosed(_g("1110/1000/1110")) == _g("1110/1000/1110")
    assert pk.path_vh(_g("100/000/001")) == _g("100/100/111")
    assert pk.path_hv(_g("100/000/001")) == _g("111/001/001")
    assert pk.path_vh(_g("100/000/000")) is None
    lib = pk.permutation_library(4, 6)
    cells = pk.flatten(pk.sample("reflect_v", 3)[0])
    for p in lib.values():
        assert sum(pk.permute(cells, p)) == sum(cells)


def test_gate_answers_refuses_and_composes():
    demos = [pk.sample("reflect_v", i) for i in range(4)]
    x, y = pk.sample("reflect_v", 999)
    r = pk.solve(demos, x)
    assert r["status"] == "answered" and r["answer"] == y
    one = [(_g("10110"), _g("01101"))]
    assert pk.solve(one, _g("11100"))["status"] == "ambiguous"
    unfit = [(_g("1000"), _g("1100")), (_g("0100"), _g("0111"))]
    assert pk.solve(unfit, _g("0010"))["status"] == "unsolved"
    demos = [pk.sample("reflect_v_then_toggle", i) for i in range(4)]
    x, y = pk.sample("reflect_v_then_toggle", 999)
    assert pk.solve(demos, x, depth=1)["status"] != "answered"
    r = pk.solve(demos, x)
    assert r["status"] == "answered" and r["answer"] == y


def test_one_demonstration_fits_no_mask():
    x, y = pk.sample("toggle", 5)
    assert pk._xor_mask([(x, y)]) is None
    assert pk._xor_mask([(x, y), (x, y)]) is None
    x2, y2 = pk.sample("toggle", 6)
    assert pk._xor_mask([(x, y), (x2, y2)]) == (1,) * 24


def test_tool_induce_answers_and_refuses():
    from glm_universal.runtime.toolbox import run_tool
    ok = run_tool(pks.TOOL_ANSWER)
    assert ok.ok and ok.figures["answer"] == pks.TOOL_ANSWER_TRUE
    no = run_tool(pks.TOOL_REFUSE)
    assert not no.ok and no.figures["status"] == "ambiguous"
    bad = run_tool("tool induce 102 -> 010 ? 000")
    assert not bad.ok and "refused" in bad.text


def test_stored_measurement_meets_every_mark():
    stored = pks.current()
    if stored is None:
        return
    assert stored["met"] == stored["taken"] == len(stored["marks"])
    assert stored["totals"]["shipped"]["wrong"] == 0
