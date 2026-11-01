"""Tests for ``runtime/respell.py`` (Phase 157) and ``runtime/sinter.py``
(Phase 159): the did-you-mean read by spelling and by use, and the register
lexicon opened once when it refuses.

``studies/FRICTION_TWO_STUDY.md`` §§2.1, 2.5, 2.6 and
``studies/THERMO_FRICTION_STUDY.md`` §2.3 fix the rules these tests pin: the
candidates are the known words one optimal-string-alignment edit away; the
shipped reading is *count first, use under load*; a token holding a digit is
never respelt; the edit is replayed on the original's case; the sintered
reading consults the lexicon only when the solid reading leaves a token of a
word's shape alone, and leaves protected tokens to the solid reading; and the
re-read in ``GLM.py`` never takes an answer away.

*Created 31 October 2026 (repository check): the module tests were lost with
the modules in the October 2026 reorganisation; written for the
reconstructed ``respell.py`` and ``sinter.py``.*
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from glm_universal.runtime import respell as rs
from glm_universal.runtime import sinter as sn

SRC = Path(__file__).resolve().parents[2]


def _table(documents, coordinates=None):
    return rs.Table(documents=dict(documents),
                    coordinates={w: tuple(v) for w, v in
                                 (coordinates or {}).items()})


# --------------------------------------------------------------- the edit

def test_the_four_edits_are_found():
    assert rs.edit("dsecribe", "describe") == ("transpose", 1)
    # the first position at which the deletion applies (either 'g' would do)
    assert rs.edit("energgy", "energy") == ("delete", 4)
    assert rs.edit("enrgy", "energy") == ("insert", 2)
    assert rs.edit("enerqy", "energy") == ("substitute", 4)
    assert rs.edit("energy", "energy") is None
    assert rs.edit("abcd", "badc") is None


def test_replay_keeps_the_original_case():
    # the two cases Phase 157's first measurement lost (§2.5)
    assert rs.replay("NromFamily", "normfamily") == "NormFamily"
    assert rs.replay("mleting_point_K", "melting_point_k") == "melting_point_K"
    # an inserted or substituted letter takes its left neighbour's case
    assert rs.replay("ENRGY", "energy") == "ENERGY"
    assert rs.replay("Enrgy", "energy") == "Energy"
    assert rs.replay("ENERQY", "energy") == "ENERGY"
    # the first measurement's writing: the case of the first letter only
    assert rs.first_letter_case("NromFamily", "normfamily") == "Normfamily"


def test_candidates_are_known_words_one_edit_away():
    t = _table({"describe": 40, "energy": 90, "enemy": 3, "rare": 2})
    assert rs.candidates("dsecribe", t) == ["describe"]
    assert rs.candidates("enrgy", t) == ["energy"]
    assert "rare" not in rs.candidates("rar", t)       # in fewer than 3 documents


# ------------------------------------------------------------ the readings

def test_an_unknown_token_is_respelt_and_the_note_names_it():
    t = _table({"describe": 40, "energy": 90})
    r = rs.respell("dsecribe energy", tbl=t)
    assert r.changed and r.text == "describe energy"
    assert r.note() == "'dsecribe' read as 'describe'"


def test_tokens_with_digits_short_tokens_and_known_words_are_left_alone():
    t = _table({"x8ad5a3": 5, "describe": 40, "cat": 9, "the": 99})
    assert not rs.respell("0x8ad5a3", tbl=t).changed          # T1': a code
    assert rs.respell("0x8ad5a3", tbl=t, amended=False).changed   # first take
    assert not rs.respell("cta", tbl=t).changed               # under 4
    assert not rs.respell("describe the", tbl=t).changed


def test_loaded_reads_count_first_and_use_only_on_a_tie():
    # 'waht' is one edit from 'what' (frequent) and 'watt' (rare, but in
    # the company of 'power'): loaded keeps 'what'; use alone takes 'watt'.
    coords = {"what": (1, 0, 0), "watt": (0, 9, 0), "power": (0, 9, 0)}
    t = _table({"what": 500, "watt": 10, "power": 80}, coords)
    assert rs.respell("waht power", "loaded", tbl=t).text == "what power"
    assert rs.respell("waht power", "use", tbl=t).text == "watt power"
    assert rs.respell("waht power", "spelling", tbl=t).text == "what power"
    # mismatched use: the same reweighting read from other company
    assert rs.respell("waht power", "mismatched", company=["what"],
                      tbl=t).text == "what power"
    # a count tie is decided by use; a tie that remains leaves it alone
    t2 = _table({"what": 10, "watt": 10, "power": 80}, coords)
    assert rs.respell("waht power", "loaded", tbl=t2).text == "watt power"
    assert not rs.respell("waht", "loaded", tbl=t2).changed


def test_an_absent_table_respells_nothing(tmp_path):
    t = rs.table(tmp_path / "none.json")
    assert not t.present and not rs.respell("dsecribe", tbl=t).changed


def test_the_switch():
    assert rs.enabled({}) and rs.enabled({"GLM_RESPELL": "1"})
    assert not rs.enabled({"GLM_RESPELL": "0"})


# ------------------------------------------------------------ sintering

def test_the_protected_class_and_the_word_shape():
    assert sn.protected("x8ad5a3") and sn.protected("melting_point_K")
    assert sn.protected("NromFamily") and not sn.protected("Mlilisecond")
    assert sn.word_shape("mlilisecond") and not sn.word_shape("x8ad5a3")


def test_sintering_reads_a_register_word_the_corpus_does_not_know():
    t = _table({"describe": 40})
    lex = frozenset({"millisecond", "microsecond"})
    r = sn.respell_sintered("gram : mass :: mlilisecond : ?", t, lex)
    assert r.text == "gram : mass :: millisecond : ?"
    # solid alone (loaded) leaves it, having no corpus candidate
    assert not rs.respell("gram : mass :: mlilisecond : ?", tbl=t).changed


def test_sintering_never_takes_the_solid_reading_away():
    t = _table({"burst": 50})
    lex = frozenset({"brunt"})
    # 'burnt' is one edit from the corpus word 'burst': the solid reading
    # answers and the lexicon is never consulted (sinter_keeps_solid)
    assert sn.respell_sintered("burnt", t, lex).text == "burst"
    assert rs.respell("burnt", tbl=t).text == "burst"


def test_a_lexicon_entry_is_known_and_several_candidates_refuse():
    t = _table({"able": 90})
    lex = frozenset({"abbe", "abba", "abby"})
    assert rs.respell("abbe", tbl=t).text == "able"      # the 45-word hazard
    assert not sn.respell_sintered("abbe", t, lex).changed   # C3
    assert not sn.respell_sintered("abbz", t, lex).changed   # three candidates


def test_protected_tokens_are_read_as_loaded_reads_them():
    t = _table({"dose": 40, "does": 400})
    lex = frozenset({"dose"})
    for tok in ("DoSe", "dose9"):
        assert (sn.respell_sintered(tok, t, lex).text
                == rs.respell(tok, tbl=t).text)


def test_the_stored_lexicon_reads_the_four_registers():
    state = sn.lexicon_state()
    if not state["present"]:
        return
    assert state["read"] == {"physics": 726, "elements": 118,
                             "intervals": 28, "comparison_classes": 45}
    assert state["entries"] == 1393 == len(sn.lexicon())


# ------------------------------------------------------- the CLI re-read

def _q(question: str, env_extra=None):
    env = dict(os.environ, PYTHONPATH=str(SRC))
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(SRC / "GLM.py"), "-q", question,
                           "--no-banner", "-c", "1"], cwd=str(SRC), env=env,
                          capture_output=True, text=True, timeout=600)


def test_a_refused_question_is_respelt_and_answered():
    if not rs.table().present:
        return
    p = _q("dsecribe energy")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "RESPELT  'dsecribe' read as 'describe'" in p.stdout
    off = _q("dsecribe energy", {"GLM_RESPELL": "0"})
    assert off.returncode == 1 and "RESPELT" not in off.stdout


def test_a_question_that_answers_is_never_reread():
    p = _q("describe energy")
    assert p.returncode == 0 and "RESPELT" not in p.stdout
