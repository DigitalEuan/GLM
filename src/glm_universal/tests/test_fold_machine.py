"""Tests for the machine sorting (Phase 160).

*Created 31 October 2026 (repository check: the original test file was lost
in the October 2026 reorganisation; written from its row in
tests/README.md and studies/FOLD_MACHINE_STUDY.md).*

These tests pin:

* the **Lean file**: ``FoldMachine.lean`` states the theorems and has no
  ``sorry`` -- or, while it is missing (``studies/_lean_files_needed.md``),
  that the mark is reported not met (the test is then skipped, never
  passed);
* the **window** ``L <= q < E`` holds exactly the ``q``-th smallest,
  exhaustively on small columns, and the **stable position** of the top
  rows is the stable sort;
* a **synthetic sample** of the control: admitted, a lie refused, silent
  where the planner refuses;
* a **wrong witness** stops the run; a **declared hole with a reading**
  stops the run;
* the **switch off** carries the fold as Phase 153 did;
* top rows, a rank and a bound computed and checked;
* the **stored measurements**.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product

import pytest

from glm_universal import constants
from glm_universal.reasoning import fold_machine as fm
from glm_universal.reasoning import fold_machine_study as fms
from glm_universal.reasoning import planner_ladder as pl
from glm_universal.reasoning import planner_ladder_study as pls

_memo: dict = {}


def _session():
    if "session" not in _memo:
        from glm_universal.runtime.session import GeometricSession
        _memo["session"] = GeometricSession()
    return _memo["session"]


def _chain(text):
    if text not in _memo:
        from glm_universal.runtime import stepwise as sw
        a = sw.answer(_session(), text)
        assert a.answered, text
        _memo[text] = a.chain
    return _memo[text]


def _fold(chain) -> int:
    return [s.index for s in chain.steps if s.op == "fold"][-1]


def _check(chain, files=None):
    return pl.check_chain(chain, say=False, read=True, files=files,
                          ladder=True)


def test_lean_file_states_the_theorems_without_sorry():
    path = constants.lean_file(fm.LEAN_FILE)
    m = pls.lean_marks(fm.LEAN_FILE, fm.LEAN_THEOREMS)
    if not path.exists():
        assert m["present"] is False and m["met"] is False
        pytest.skip(f"{fm.LEAN_FILE} is missing (studies/"
                    f"_lean_files_needed.md); L1 is reported not met")
    text = path.read_text(encoding="utf-8")
    for name in fm.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text and m["met"]


def test_the_window_holds_exactly_the_qth_smallest():
    for n in range(1, 5):
        for col in product(range(3), repeat=n):
            vals = [Fraction(v) for v in col]
            ordered = sorted(vals)
            for q in range(n):
                for x in vals:
                    lo, hi = fm.window(vals, x)
                    assert (lo <= q < hi) == (x == ordered[q]), (col, q, x)


def test_the_stable_position_is_the_stable_sort():
    for n in range(1, 5):
        for col in product(range(3), repeat=n):
            vals = [Fraction(v) for v in col]
            for symbol in (">", "<"):
                pos = fm.stable_positions(vals, symbol)
                order = sorted(range(n), key=lambda i: vals[i],
                               reverse=(symbol == ">"))
                assert sorted(pos) == list(range(n))
                assert [order.index(i) for i in range(n)] == pos


def test_a_synthetic_sample_of_the_control():
    k = fms.synthetic_part(count=60)
    assert k["answered"] > 0 and k["refused_by_planner"] > 0
    assert k["admitted"] == k["answered"]
    assert k["lies_refused"] == k["lies"] > 0
    assert k["machine_silent"] == k["refused_by_planner"]
    assert k["carried"] == 0


def test_a_wrong_witness_stops_the_run():
    chain = _chain("what is the median atomic number of the halogens")
    k = _fold(chain)
    with fms.switches(True):
        honest = _check(chain)
    assert honest["admitted"] and k in honest["computed"]
    with fms.switches(True, shift=1):
        moved = _check(chain)
    assert moved["exit"] == 2 and not moved["admitted"]
    assert pl.file_of(k) not in moved["ladder"].run.files


def test_a_declared_hole_with_a_reading_stops_the_run():
    from glm_universal.reasoning import carried_read as cr
    chain = _chain("what is the median density of the halogens")
    k = _fold(chain)
    assert chain.steps[k - 1].detail.get("missing")
    seed = cr.seed_files(chain, _session())
    with fms.switches(True):
        honest = _check(chain, seed)
        holed = fms._hole_files(chain, k, seed)
        assert holed is not None
        d = _check(chain, holed)
    assert honest["admitted"] and k in honest["computed"]
    assert d["first_drift"] == k and d["exit"] == 2 and not d["promoted"]


def test_the_switch_off_carries_the_fold():
    chain = _chain("what is the median density of the halogens")
    k = _fold(chain)
    with fms.switches(False):
        off = _check(chain)
    with fms.switches(True):
        on = _check(chain)
    assert off["admitted"] and k in off["carried"]
    assert on["admitted"] and k in on["computed"]


def test_top_rows_by_stable_position_and_a_lie():
    chain = _chain("which is the lightest of the halogens")
    k = _fold(chain)
    with fms.switches(True):
        c = _check(chain)
        lie = fms.fold_lie(chain.steps[k - 1])
        assert lie is not None
        d = _check(pl.lie_chain(chain, k, lie))
    assert c["admitted"] and k in c["computed"]
    assert d["first_drift"] == k and not d["admitted"]


def test_a_rank_and_a_bound_are_computed():
    for text in ("what is the rank of xenon by atomic number among the "
                 "noble gases",
                 "what are the bounds on the total electronegativity of the "
                 "noble gases"):
        chain = _chain(text)
        k = _fold(chain)
        with fms.switches(True):
            c = _check(chain)
        assert c["admitted"] and k in c["computed"], text


def test_the_stored_measurements():
    assert fms.state()["verdict"] == "current"
    r = fms.fold_machine_report()
    assert r["available"]
    marks, c, k = r["marks"], r["chains"], r["synthetic"]
    for name in ("M1", "M2", "M3", "M4", "M5", "M6", "K1", "P1"):
        assert marks[name], name
    assert r["amended"] == {"M4'": True}
    assert c["folds_carried_on"] == 0 < c["folds_carried_off"]
    assert c["admitted"] == c["chains"] and c["read_back"] == c["said"]
    assert c["lies_found"] == c["lies"] and c["witness_wrong"] == 0
    assert k["columns"] == fms.SYNTHETIC
    assert k["admitted"] == k["answered"] and k["lies_refused"] == k["lies"]
    assert k["machine_silent"] == k["refused_by_planner"]
    # F1 is reported, never assumed
    assert marks["F1"] == bool(r["frozen"]["measured"] and
                               r["frozen"]["same_text"] ==
                               r["frozen"]["texts"] > 0)
