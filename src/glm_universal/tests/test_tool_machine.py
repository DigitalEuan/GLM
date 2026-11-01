"""Tests for the machine working the tools out (Phase 163).

*Created 31 October 2026 (repository check: the original test file was lost
in the October 2026 reorganisation; written from its row in
tests/README.md and studies/TOOL_MACHINE_STUDY.md).*

These tests pin:

* the **Lean files**: ``ToolMachine.lean`` and ``LeechMachine.lean`` state
  their theorems with no ``sorry`` -- or, while missing
  (``studies/_lean_files_needed.md``), that L1 is reported not met (the test
  is then skipped, never passed);
* **lockstep terms**: the continued-fraction terms the machine certifies are
  the terms of the number (computed here independently);
* the **Golay census** over the code's own generator: 4,096 codewords, 759
  octads and the Leech kissing number 196,560;
* a **held-out sample** of the control: admitted, a lie refused, silent
  where the tool refuses;
* a **wrong square-root witness** stops the run;
* the **switch off** carries the tool step;
* the **stored measurement** (the original module's record).

*Last altered 31 October 2026: the stored measurement may be the
reconstruction's re-take (F1' not measured) as well as the original record.*
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from glm_universal import constants
from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import planner_ladder as pl
from glm_universal.reasoning import planner_ladder_study as pls
from glm_universal.reasoning import tool_machine as tm
from glm_universal.reasoning import tool_machine_study as tms

_FILES = {"q.txt": ()}


def _sqrt_cf(m: int, count: int):
    """The continued fraction of ``sqrt(m)`` by the classical integer
    recurrence -- independent of the machine and of the tool."""
    a0 = math.isqrt(m)
    out, p, q, a = [a0], 0, 1, a0
    while len(out) < count:
        p = a * q - p
        q = (m - p * p) // q
        a = (a0 + p) // q
        out.append(a)
    return out


def _e_cf(count: int):
    out = [2]
    k = 1
    while len(out) < count:
        out += [1, 2 * k, 1]
        k += 1
    return out[:count]


def test_lean_files_state_their_theorems_without_sorry():
    pairs = ((tm.LEAN_FILE, tm.LEAN_THEOREMS),
             (tms.LEECH_LEAN_FILE, tms.LEECH_LEAN_THEOREMS))
    missing = []
    for name, theorems in pairs:
        path = constants.lean_file(name)
        m = pls.lean_marks(path.name, theorems)
        if not path.exists():
            assert m["present"] is False and m["met"] is False
            missing.append(path.name)
            continue
        text = path.read_text(encoding="utf-8")
        for t in theorems:
            assert f"theorem {t}" in text, t
        assert "sorry" not in text and m["met"]
    if missing:
        pytest.skip(f"{', '.join(missing)} missing (studies/"
                    f"_lean_files_needed.md); L1 is reported not met")


def test_lockstep_terms_are_terms_of_the_number():
    cases = [(f"sqrt({m})", _sqrt_cf(m, 10)) for m in (2, 7, 13, 19)]
    cases.append(("e", _e_cf(10)))
    with tms.switches(True):
        for x, terms in cases:
            for k in (1, 4, 10):
                rec = ("tool", f"tool continued fraction {x} terms {k}",
                       "index", "terms", str(k - 1))
                right = tms.held_out_chain(f"term {k} of {x}", rec,
                                           Fraction(terms[k - 1]))
                c = pl.check_chain(right, say=False, read=True, files=_FILES)
                assert c["admitted"] and c["computed"] == [1], (x, k)
                wrong = pl.lie_chain(right, 1, Fraction(terms[k - 1] + 1))
                d = pl.check_chain(wrong, say=False, read=True, files=_FILES)
                assert not d["admitted"], (x, k)


def test_the_golay_census_from_the_generator():
    lines = ["CALL :GOLAY", "SET /A K=128*YN8+4*276+24*YNALL",
             "EXIT /B 0"] + list(tm.golay_census_lines())
    run = bm.run_program(bm.parse_program(lines), None, {}, (),
                         budget=pl.BUDGET, inert=False, jump=False)
    assert run.status == "halted" and run.exit_code == 0
    assert run.env["YNALL"] == "4096"
    assert run.env["YN8"] == "759"
    assert run.env["K"] == "196560"


def test_a_held_out_sample_of_the_control():
    k = tms.held_out_part(140)
    assert k["answered"] > 0 and k["refused_by_tool"] > 0
    assert k["admitted"] == k["answered"]
    assert k["lies_refused"] == k["lies"] == k["answered"]
    assert k["machine_silent"] == k["refused_by_tool"]
    assert k["carried"] == 0


def test_a_wrong_square_root_witness_stops_the_run():
    rec = ("tool", "tool convergent 5 of sqrt(7)", "value", "value")
    chain = tms.held_out_chain("convergent 5 of sqrt(7)", rec,
                               Fraction(37, 14))
    with tms.switches(True):
        honest = pl.check_chain(chain, say=False, read=True, files=_FILES)
    with tms.switches(True, root=tms._moved_root):
        moved = pl.check_chain(chain, say=False, read=True, files=_FILES)
    assert honest["admitted"] and honest["computed"] == [1]
    assert moved["exit"] == 2 and not moved["admitted"]


def test_the_switch_off_carries_the_tool_step():
    from glm_universal.runtime import stepwise as sw
    from glm_universal.runtime.session import GeometricSession
    text = "the first convergent of pi whose denominator is above 1000"
    a = sw.answer(GeometricSession(), text)
    assert a.answered
    planned = [s.index for s in a.chain.steps if s.op == "planned"]
    assert planned
    with tms.switches(False):
        off = pl.check_chain(a.chain, say=False, read=True)
    with tms.switches(True):
        on = pl.check_chain(a.chain, say=False, read=True)
    assert off["admitted"] and set(planned) <= set(off["carried"])
    assert on["admitted"] and set(planned) <= set(on["computed"])
    assert on["carried"] == []


def test_the_stored_measurement():
    st = tms.stored()
    assert st is not None
    # 8 of 9 either way: the original module's record (F1 missed, F1' met)
    # or, since 31 October 2026, the reconstruction's re-take, which leaves
    # F1' unmeasured because the frozen path's baseline was lost with the
    # module (TOOL_MACHINE_STUDY.md §7.5) -- never an amended mark met
    # without its comparison.
    assert (st["met"], st["taken"]) == (8, 9)
    assert st["marks"]["F1"] is False
    if st["amended"] != {"F1'": True}:
        assert st["amended"] == {"F1'": False}
        assert st["frozen"]["measured"] is False and st["frozen"]["note"]
    assert st["chains"]["carried_on"] == 0
    assert st["chains"]["lies_found"] == st["chains"]["lies"]
    k = st["held_out"]
    assert k["admitted"] == k["answered"] and k["lies_refused"] == k["lies"]
    assert k["machine_silent"] == k["refused_by_tool"]
    report = tms.tool_machine_report()
    assert report["available"] == tms.state()["fresh"]
