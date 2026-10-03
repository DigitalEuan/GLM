"""The third sort -- strings, tuples and ranges in the reverse grammar, and
the Python dialect widened to string methods, lists and dicts, pinned.

``glm_universal.reasoning.reverse_tct_seq`` is the sort and
``glm_universal.reasoning.python_containers`` the widening
(``studies/THIRD_SORT_STUDY.md``, Phase 94);
``glm_universal.runtime.third_sort_report`` measures the declared cases of
``glm_universal.evaluation.third_sort_cases``.  The facts the round rests on
are theorems of ``RequestProject/GLM/ThirdSort.lean`` (L).
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import python_speech_cases as pc
from glm_universal.evaluation import third_sort_cases as C
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import python_containers as pcn
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import reverse_tct as rt
from glm_universal.reasoning import reverse_tct_script as rts
from glm_universal.reasoning import reverse_tct_seq as rs
from glm_universal.runtime import third_sort_report as R
from glm_universal.runtime.python_tct import run_column3
from glm_universal.runtime.tct_engine import package_root

LEAN = (Path(__file__).resolve().parents[2] / "glm_lean" / "RequestProject"
        / "GLM" / "ThirdSort.lean")


class TestTheGrammar:
    """T1-T3: the sentences, the refusals, reading back."""

    def test_every_sentence_and_value(self):
        got = R.say_marks(run_scripts=False)
        assert got["T1"]["passed"], got["T1"]["wrong_ids"]
        assert got["read_back"]["right"] == len(C.SAY_CASES)

    def test_every_refusal(self):
        got = R.say_marks(run_scripts=False)
        assert got["T2"]["passed"], got["T2"]

    def test_the_battery(self):
        b = R.battery()
        assert b["terms"] > 1000
        assert b["read_back"] == b["terms"] == b["distinct_sentences"]

    @pytest.mark.parametrize("cp", [0, 31, 32, 48, 57, 65, 90, 97, 122, 127,
                                    923, 0x10FFFF])
    def test_every_character_has_one_spelling(self, cp):
        s = rs.realise(("str", (cp,)))
        assert rs.read(s) == ("str", (cp,))

    def test_a_noncanonical_code_point_is_unreadable(self):
        with pytest.raises(rt.ReverseRefusal) as exc:
            rs.read("the string of one character code point sixty-five")
        assert exc.value.name == "UNREADABLE"

    def test_literals_nest(self):
        t = rs.from_source("((('a', ''), ()), range(2), 'b')")
        assert rs.read(rs.realise(t)) == t


class TestTheSlice:
    """The evaluator's own slice reading against CPython's, exhaustively over
    short sequences (the Lean file proves the indices stay inside)."""

    def test_clamped_indices_equal_cpython(self):
        bounds = [None, -7, -3, -1, 0, 1, 2, 5, 9]
        for n in range(0, 6):
            seq = list(range(n))
            for a in bounds:
                for b in bounds:
                    for c in (-3, -2, -1, 1, 2, 3):
                        assert rs.clamp_indices(n, a, b, c) == seq[a:b:c]


class TestTheEarlierGrammar:
    """T6: the third sort is asked only where the earlier grammar refuses."""

    def test_no_earlier_say_case_moves(self):
        got = R.no_regression()
        assert got["passed"], got["moved"]
        assert got["w2_inside"] == 36

    def test_an_earlier_refusal_stands_when_the_sort_cannot_read(self):
        a = rt.say("f(x)")
        assert a.refusal == "NOT_IN_FRAGMENT"


class TestTheDialectsPrograms:
    """T5."""

    def test_twenty_one_inside(self):
        got = R.dialect_inside()
        assert got["passed"], got["rows"]
        assert got["outside"] == ["tuple-concat"]


class TestColumnThree:
    """T4 and D3, on samples in this unit; the report runs every case."""

    SAY = ("str-reverse", "tuple-nested", "range-total", "str-in",
           "prog-seq", "range-literal")
    DIALECT = ("replace-empty", "split-whitespace", "sorted-tuples",
               "snapshot", "equal-keys", "items")

    def test_say_scripts_verify_and_mutants_fail(self):
        root = str(package_root())
        cases = {c: s for c, s, _ in C.SAY_CASES}
        for cid in self.SAY:
            a = rt.say(cases[cid])
            assert run_column3(rts.render_script(a, root))["verified"], cid
            assert not run_column3(rts.mutated_script(a, root))["verified"], \
                cid

    def test_dialect_scripts_verify_and_mutants_fail(self):
        cases = dict(C.STRING_METHOD_CASES)
        cases.update(C.LIST_CASES)
        cases.update(C.DICT_CASES)
        for cid in self.DIALECT:
            p = sp.speak(cases[cid])
            assert sp.verify_payload(p)["verified"], cid
            assert not sp.verify_payload(p, sp.mutated_script(p))[
                "verified"], cid

    def test_dialect_scripts_are_exact(self):
        from glm_universal.runtime.tct_engine import script_is_exact
        for group in (C.STRING_METHOD_CASES, C.LIST_CASES, C.DICT_CASES):
            for cid, src in group:
                ok, offenders = script_is_exact(sp.speak(src).column3)
                assert ok, (cid, offenders)


class TestTheDialectWidened:
    """D1, D2, D4."""

    def test_every_value_equals_cpython(self):
        for group in (C.STRING_METHOD_CASES, C.LIST_CASES, C.DICT_CASES):
            for cid, src in group:
                p = sp.speak(src)
                assert p.answered, (cid, p.refusal, p.reason)
                ns, ref = sp._cpython_reference(src)
                assert ns["same"](eval(p.value_literal, ns), ref), cid

    def test_every_refusal_by_name(self):
        for cid, src, want in C.DIALECT_REFUSALS:
            p = sp.speak(src)
            assert not p.answered and p.refusal == want, (cid, p.refusal)

    def test_the_superseded_refusals_are_answered(self):
        for cid, src, _old in C.SUPERSEDED_REFUSALS:
            p = sp.speak(src)
            assert p.answered, cid
            assert cid in pc.SUPERSEDED_BY_PHASE94
        assert len(pc.REFUSAL_CASES) == len(pc.PHASE64_REFUSAL_CASES) - 2

    def test_an_alias_never_sees_a_change(self):
        p = sp.speak("a = [1]\nb = a\na += [2]\nb")
        assert p.refusal == "MUTABLE_CONTAINER"
        p = sp.speak("a = [1]\nb = a\na = a + [2]\n(a, b)")
        assert p.answered and p.value == ([1, 2], [1])

    def test_a_list_is_not_a_tuple(self):
        assert sp.speak("[1, 2]").value_literal == "[1, 2]"
        assert sp.speak("[1, 2] == (1, 2)").value is False

    def test_dict_keys_merge_as_cpython(self):
        p = sp.speak("{1: 'a', True: 'b', Fraction(1): 'c'}")
        ns, ref = sp._cpython_reference("{1: 'a', True: 'b', Fraction(1): 'c'}")
        assert ns["same"](eval(p.value_literal, ns), ref)

    def test_ascii_case_mapping(self):
        assert pcn.ascii_upper("Golay code 24") == "GOLAY CODE 24"
        assert pcn.ascii_lower(pcn.ascii_upper("leech")) == "leech"

    def test_phase64_values_and_battery(self):
        for cid, src in pc.VALUE_CASES:
            p = sp.speak(src)
            ns, ref = sp._cpython_reference(src)
            assert p.answered and ns["same"](eval(p.value_literal, ns), ref), \
                cid


class TestStatic:

    def test_no_float(self):
        for mod in (rs, pcn, R):
            assert ex.module_float_sites(Path(mod.__file__)) == {}

    def test_the_lean_file(self):
        text = LEAN.read_text()
        assert "sorry" not in text
        for name in ("decItems_encItems", "decLit_encLit", "encLit_injective",
                     "lt_rangeLen_iff", "mem_rangeList_iff",
                     "two_mul_sum_rangeList", "clampIdx_bounds",
                     "slicePos_mem_bounds", "sliceNeg_mem_bounds",
                     "upper_lower_of_lower", "lower_upper_of_upper",
                     "upper_idem", "length_mapUpper"):
            assert f"theorem {name}" in text, name


def test_the_tool_runs():
    from glm_universal import tools
    assert tools.run(["third-sort", "--no-scripts"]) == 0


def test_values_are_exact():
    a = rt.say("sum(range(1, 11))")
    assert rs.evaluate(rs._dec(a.certificate["value"]), {}) == Fraction(55)
