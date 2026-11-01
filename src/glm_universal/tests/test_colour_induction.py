"""Tests for colour induction: ``tool induce`` on colour grids whose shape may
change, and ``tool arc`` on the stored ARC tasks (Phase 178, part A).

*Created 22 October 2026 (Phase 178).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from ``tests/README.md``'s row for
this file (ten tests), ``MASTER_PLAN.md`` Phase 178 and the reconstructed
``reasoning/colour_induction.py`` and ``reasoning/colour_induction_study.py``.
The tasks below are this reconstruction's.*

``studies/COLOUR_INDUCTION_STUDY.md`` declared the marks. These tests pin:

* the **Lean file** ``ColourInduction.lean`` states its recorded theorems
  with no ``sorry``; while it is lost (October 2026 reorganisation) it must
  be recorded in ``studies/_lean_files_needed.md`` and the study's mark L
  must report it not met (the pattern of ``test_lorentzian_majority.py``);
* **grids** are parsed and one **background** read per task;
* the **invariant reading** skips the count-keeping operators when a
  demonstration changes the colour counts, and skipping changes no verdict;
* the **span rule**: one demonstration of a recolour is not answered (no fit
  was tested on a demonstration it was not fitted to), two are;
* a **symmetry** is answered, and a query showing a colour no demonstration
  showed is refused (the unread rule);
* a **shape-changing** tile is answered;
* ``tool induce`` sends colour tasks to the colour solver and binary tasks to
  the pipeline kit exactly as before;
* ``tool arc`` reads a stored task and grades its answer;
* the **English openings** reach ``tool arc`` and ``tool induce``;
* the **stored measurement**, when current, meets C1, C5, C6, R1, B and T
  (the reconstruction's take misses C3, C4, R2, R3 and L; Phase 178's take
  missed C2, C4, R2 and R3).
"""

from __future__ import annotations

from glm_universal.constants import LEAN_FILES_NEEDED, lean_file
from glm_universal.lean_check import audited_or_held
from glm_universal.reasoning import colour_induction as ci
from glm_universal.reasoning import colour_induction_study as cis
from glm_universal.reasoning import pipeline_kit as pk
from glm_universal.runtime.toolbox import phrase_tool, run_tool

_RECOLOUR = "120/300 -> 340/500 ; 210/003 -> 430/005 ? 210/030"
_BINARY = "10/00 -> 01/00 ; 00/10 -> 00/01 ? 10/10"


def _solve(arg, **kw):
    pairs, query, why = ci.parse_task(arg)
    assert pairs is not None, why
    return ci.solve(pairs, query, **kw)


def test_lean_file_states_the_theorems_without_sorry():
    path = lean_file(ci.LEAN_FILE)   # build tree, or awaiting_recovery/
    if not path.exists():
        # lost in the October 2026 reorganisation: it must then be recorded
        # as missing, and the study's Lean mark must say so.
        assert "`ColourInduction.lean`" in LEAN_FILES_NEEDED.read_text(
            encoding="utf-8")
        lean = cis._lean()
        assert lean["present"] is False and lean["theorems"] == 0
        return
    text = path.read_text(encoding="utf-8")
    assert audited_or_held("RequestProject.GLM.ColourInduction")
    for name in ci.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text


def test_grids_parsed_and_the_background_read():
    assert ci.parse_grid("120/300") == ((1, 2, 0), (3, 0, 0))
    assert ci.parse_grid("1 2/3 4") == ((1, 2), (3, 4))
    assert ci.parse_grid("1,2/3,4") == ((1, 2), (3, 4))
    assert ci.parse_grid("12/3") is None          # not rectangular
    assert ci.parse_grid("1a/34") is None         # not colours 0-9
    pairs, query, why = ci.parse_task(_RECOLOUR)
    assert why == "" and len(pairs) == 2 and query == ((2, 1, 0), (0, 3, 0))
    assert ci.background(pairs, query) == 0
    # a tie goes to the smaller colour
    g = ((1, 2), (2, 1))
    assert ci.background([(g, g)]) == 1
    assert ci.parse_task("120/300 -> 340/500")[0] is None     # no query
    assert ci.is_colour_task(pairs, query)
    bp, bq, _ = ci.parse_task(_BINARY)
    assert not ci.is_colour_task(bp, bq)


def test_invariant_reading_skips_count_keeping_operators():
    arg = ("123/400 -> 112233/112233/440000/440000 ; "
           "05/67 -> 0055/0055/6677/6677 ? 89/10")
    pairs, query, _ = ci.parse_task(arg)
    inv = ci.read_invariants(pairs)
    assert inv == {"counts_kept": False, "no_new_colour": True,
                   "shape_kept": False}
    reading = ci.read_task(pairs, query)
    assert reading["skipped_by_invariant"] > 0
    keepers = {o.name for o in ci.operators() if o.count_keep}
    assert "flip_h" in keepers and "rotate90" in keepers
    assert not keepers & {s.name for s in reading["survivors"]}
    with_it = ci.verdict(reading)
    without = ci.verdict(ci.read_task(pairs, query, invariant=False))
    assert without["skipped_by_invariant"] == 0
    assert without["tried"] > with_it["tried"]
    assert with_it["status"] == without["status"] == "answered"
    assert ci.grid_text(with_it["answer"]) == "8899/8899/1100/1100"
    assert with_it["answer"] == without["answer"]


def test_one_demonstration_of_a_recolour_is_not_answered():
    one = _RECOLOUR.split(";")[0] + " ? 210/030"
    r = _solve(one)
    assert r["status"] == "untested" and r["answer"] is None
    assert "colour_map" in r["survivors"]
    # counted as tested by its own fit, the same family would answer
    assert _solve(one, span_rule=False)["status"] == "answered"
    # a second demonstration tests it, and it answers
    r2 = _solve(_RECOLOUR)
    assert r2["status"] == "answered"
    assert ci.grid_text(r2["answer"]) == "430/050"
    assert "colour_map" in r2["tested"]


def test_a_symmetry_answered_and_unread_colours_refused():
    r = _solve("120/034/500 -> 021/430/005 ; 006/780/090 -> 600/087/090 "
               "? 300/045/600")
    assert r["status"] == "answered"
    assert ci.grid_text(r["answer"]) == "003/540/006"
    assert "flip_h" in r["survivors"]
    # colour 7 is in no demonstration: the colour map never read it
    u = _solve("120/300 -> 340/500 ; 210/003 -> 430/005 ? 710/030")
    assert u["status"] == "unread" and u["answer"] is None
    assert u["unread"]["colour_map"] == ["colour 7"]
    ok, text, fig = ci.induce_colour_text(*ci.parse_task(
        "120/300 -> 340/500 ; 210/003 -> 430/005 ? 710/030")[:2])
    assert not ok and fig["status"] == "unread"
    assert "unread_fitted_refuses" in text


def test_a_shape_changing_tile():
    r = _solve("123/400 -> 123123/400400/123123/400400 ; "
               "05/67 -> 0505/6767/0505/6767 ? 89/10")
    assert r["status"] == "answered"
    assert ci.grid_text(r["answer"]) == "8989/1010/8989/1010"
    assert "tile2x2" in r["survivors"]


def test_tool_induce_routes_colour_and_binary_tasks():
    t = run_tool(f"tool induce {_RECOLOUR}")
    assert t.ok and t.figures.get("solver") == "colour"
    assert t.figures.get("answer") == "430/050"
    assert ci.induce_tool_text(_RECOLOUR)[2]["solver"] == "colour"
    # a binary task whose grids keep their shape: the pipeline kit, unchanged
    want = pk.induce_text(_BINARY)
    b = run_tool(f"tool induce {_BINARY}")
    assert (b.ok, b.text, b.figures) == want
    assert ci.induce_tool_text(_BINARY) == want
    assert b.figures.get("solver") != "colour"


def test_tool_arc_reads_a_stored_task():
    assert "1e0a9b12" in ci.arc_names()
    t = run_tool("tool arc 1e0a9b12")
    assert t.ok and t.figures.get("status") == "right", t.text
    assert "RIGHT" in t.text
    ok, _text, fig = ci.arc_text("1e0a9b12")
    assert ok and fig["right"] == fig["tests"] and fig["wrong"] == 0
    u = run_tool("tool arc 00000000")
    assert not u.ok
    assert not ci.arc_text("00000000")[0]


def test_the_english_openings_reach_the_tools():
    assert phrase_tool("Solve the ARC task 1e0a9b12") == "tool arc 1e0a9b12"
    assert phrase_tool(f"induce the rule from {_RECOLOUR}") == \
        f"tool induce {_RECOLOUR}"
    assert phrase_tool(f"please infer the rule in {_RECOLOUR}") == \
        f"tool induce {_RECOLOUR}"
    assert phrase_tool("what is the anchor kappa") == "tool kappa"


def test_stored_measurement_when_current():
    r = cis.current()
    if r is None:
        return
    for mark in ("C1", "C5", "C6", "R1", "B", "T"):
        assert r["marks"][mark], mark
    assert r["synthetic"]["totals"]["shipped"]["in"]["wrong"] == 0
    assert r["arc"]["wrong"] == []
    assert r["binary"]["same_router"] == r["binary"]["queries"]
