"""Tests for the answer censuses guarded by what their answers quote, and
the replay gate as a sign-off instrument (Phase 174).

*Created 20 October 2026.*

``studies/QUOTED_MEASUREMENTS_STUDY.md`` pre-registered its marks.  These
tests pin:

* the **recorder**: a stored measurement opened inside the block is named,
  a file outside a ``_data`` directory or opened for writing is not;
* the **digest**: a census's digest moves with the quoted list;
* the **order**: stage 0 of the close re-takes the censuses last;
* the **instrument**: ``replay`` is declared with the replay gate in its
  closure.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from glm_universal import quoted_measurements as qm
from glm_universal.reasoning import evidence_model_study as ems
from glm_universal.signoff import __main__ as so
from glm_universal.signoff import checks as C

_DATA = qm.PACKAGE_ROOT / "reasoning" / "_data"


def test_the_recorder_names_stored_measurements_read():
    target = _DATA / "stacked_dialogue_study.json"
    with qm.recording() as seen:
        target.read_text(encoding="utf-8")
        json.load(open(_DATA / "resumed_dialogue_study.json",
                       encoding="utf-8"))
        (qm.PACKAGE_ROOT / "integrity.py").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.json").write_text("{}", encoding="utf-8")
    assert seen == {"reasoning/_data/stacked_dialogue_study.json",
                    "reasoning/_data/resumed_dialogue_study.json"}


def test_the_recorder_restores_open():
    import builtins
    import io
    before = (builtins.open, io.open)
    with qm.recording():
        pass
    assert (builtins.open, io.open) == before


def test_quoted_paths_drop_the_excluded():
    names = {"reasoning/_data/a.json", "reasoning/_data/evidence_model_study.json"}
    assert qm.quoted_paths(names, (ems.DATA_PATH,)) == ["reasoning/_data/a.json"]


def test_the_census_digest_moves_with_what_it_quotes():
    some = ["reasoning/_data/stacked_dialogue_study.json"]
    assert ems.module_digest(some) != ems.module_digest([])


def test_the_censuses_are_retaken_last():
    assert so.CENSUS_LAST == ("evidence_model_study", "evidence_in_use_study")


def test_the_replay_instrument_is_declared():
    replay = C.checks_by_name()["replay"]
    assert "--replay-only" in replay.command
    closure = {p.relative_to(C.L.REPOSITORY_ROOT).as_posix()
               for p in C.check_closure(replay)}
    assert "glm_universal/evaluation/replay.py" in closure
    assert "GLM.py" in closure
