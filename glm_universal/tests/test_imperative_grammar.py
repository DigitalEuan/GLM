"""The imperative grammar -- programs with state in the reverse grammar,
pinned.

``glm_universal.reasoning.reverse_tct_imp`` is the grammar
(``studies/IMPERATIVE_GRAMMAR_STUDY.md``, Phase 95);
``glm_universal.runtime.imperative_report`` measures the declared cases of
``glm_universal.evaluation.imperative_cases``.  The facts the round rests on
are theorems of ``RequestProject/GLM/ImperativeGrammar.lean`` (L).
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import imperative_cases as C
from glm_universal.evaluation import python_speech_cases as pc
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import reverse_tct as rt
from glm_universal.reasoning import reverse_tct_imp as ri
from glm_universal.reasoning import reverse_tct_script as rts
from glm_universal.reasoning import reverse_tct_seq as rs
from glm_universal.runtime import imperative_report as R
from glm_universal.runtime.python_tct import run_column3
from glm_universal.runtime.tct_engine import package_root

LEAN = (Path(__file__).resolve().parents[2] / "glm_lean" / "RequestProject"
        / "GLM" / "ImperativeGrammar.lean")


class TestTheGrammar:
    """I1-I5: the sentences, the values, the refusals, reading back."""

    def test_sentences_values_and_the_phase64_programs(self):
        got = R.say_marks(run_scripts=False)
        for k in ("I1", "I2", "I3"):
            assert got[k]["passed"], (k, got[k]["missed_ids"])
            assert not got[k]["wrong_ids"]
        assert got["read_back"]["right"] == got["read_back"]["of"]

    def test_every_refusal(self):
        got = R.refusal_marks()
        assert got["passed"], got

    def test_the_battery(self):
        b = R.battery()
        assert b["programs"] > 1000
        assert b["read_back"] == b["programs"] == b["distinct_sentences"]

    def test_a_grammar_word_is_spelled_as_a_variable(self):
        a = rt.say("total = 1\nfor k in range(3):\n    total *= 2\ntotal")
        assert a.answered and "the variable total" in a.sentence
        with pytest.raises(rt.ReverseRefusal) as exc:
            ri.read("the program of one step: set the variable x to one. "
                    "the result is the variable x.")
        assert exc.value.name == "UNREADABLE"

    def test_the_trace_is_column_one(self):
        src = dict(pc.VALUE_CASES)["loop-acc"]
        a = rt.say(src)
        assert "the variable total equals the fraction one over two" in \
            a.column1
        assert a.column1[-1] == ("the variable total equals the fraction ten "
                                 "over eleven")

    def test_true_division_is_refused(self):
        a = rt.say("s = 0\nfor k in range(3):\n    s += k / 2\ns")
        assert not a.answered

    def test_sorts_are_decided_before_the_program_runs(self):
        a = rt.say("def f(s):\n    return s + s\nf('ab')")
        assert a.refusal == "SORT_MISMATCH"
        a = rt.say("out = ''\nfor ch in 'ab':\n    out = ch + out\nout")
        assert "the concatenation of ch and out" in a.sentence


class TestColumnThree:
    """I6 on a sample (the report runs every case)."""

    @pytest.mark.parametrize("cid", ["while-gcd", "match-literal",
                                     "def-harmonic"])
    def test_script_verifies_and_mutant_fails(self, cid):
        a = rt.say(dict(pc.VALUE_CASES)[cid])
        root = str(package_root())
        assert run_column3(rts.render_script(a, root))["verified"]
        assert not run_column3(rts.mutated_script(a, root))["verified"]


class TestNoRegression:

    def test_earlier_answers(self):
        got = R.no_regression()
        assert got["moved"] == []
        assert sorted(got["moved_as_declared"]) == sorted(C.PHASE64_STATE)
        # The one refusal of an earlier round the grammar makes more
        # specific (recorded in the study's §4: mark I7 is not met).
        assert got["earlier_moved"] == ["68-refusal:unpack-self"]

    def test_limits_withhold(self):
        got = R.limit_marks()
        assert got["passed"], got


class TestStatic:

    def test_no_float(self):
        for mod in (ri, R):
            assert ex.module_float_sites(Path(mod.__file__)) == {}

    def test_the_lean_file(self):
        text = LEAN.read_text()
        assert "sorry" not in text
        for name in ("iterDec_encList", "depth_lt_of_mem", "decT_encT",
                     "encT_injective", "exec_mono", "exec_agree",
                     "euclidLoop_gcd", "euclidLoop_1071_462",
                     "sum_telescope", "loop_acc_value", "factFuel_eq"):
            assert f"theorem {name}" in text, name


def test_the_tool_runs():
    from glm_universal import tools
    assert tools.run(["imperative", "--no-scripts"]) == 0


def test_values_are_exact():
    a = rt.say(dict(pc.VALUE_CASES)["loop-acc"])
    assert rs.evaluate(rs._dec(a.certificate["value"]), {}) == \
        Fraction(10, 11)


def test_the_post_hoc_differential_battery_has_no_wrong_answer():
    d = R.differential()
    assert d["imperative_answers"] > 300
    assert d["wrong"] == 0, d["wrong_programs"]


def test_a_value_too_large_to_speak_is_a_named_refusal():
    # Found by the post-hoc battery once its generator became integer-only:
    # repeated squaring outgrew the realiser.  It is now SIZE_LIMIT.
    src = "x = 3\nfor k in range(20):\n    x = x ** 2\nx"
    a = rt.say(src)
    assert not a.answered
    assert a.refusal == "SIZE_LIMIT"


def test_the_core_modules_import_no_random_library():
    from glm_universal.reasoning import blueprint as bp
    core = bp.ubp_source_audit()["core_violations"]
    assert not [v for v in core if v["module"].endswith(
        ("imperative_report.py", "reverse_tct_imp.py"))]
