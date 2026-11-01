"""Tests for :mod:`glm_universal.reasoning.hypothesis_tools` -- the Rule 30
study's hypothesis engine on the GLM's answering path (``tool rule30``,
``tool conjecture`` and the plan search behind ``tool arc``).

*Created 1 November 2026 (Phase 186: the intake items absorbed where they
measurably help).*

What is pinned:

* **The centre column is Rule 30's.**  ``tool rule30 centre N`` gives the
  cells a plain simulation written here gives (a list of cells,
  ``new = left XOR (centre OR right)``), for ``N`` up to 64 the list that
  ``IntakeChecks/RuleThirtyBits.lean`` states (read out of the Lean file), and
  refuses an ``N`` it does not read.
* **Rule 30 sentences** are answered with the engine's ring and the Lean
  theorem they rest on (resolved in the development); a sentence the engine's
  recognisers do not read is refused by name; an open question is never
  answered true or false.
* **The battery**: the engine's 39 Rule 30 claims, 0 wrong and 0
  overclaimed.
* **Conjectures**: a false claim is refuted with a counterexample that is
  checked here; a claim that survives every read is reported as surviving,
  never as proved; a registered claim of the general domain is answered with
  its Lean theorem; text that is not a predicate in ``n`` is refused; a claim
  whose values grow beyond reach is read only within the work bound.
* **tool arc**: a test input the colour solver refuses goes to the plan
  search, whose answer is graded against the stored output; a task the colour
  solver answers keeps the colour solver's answer.
* **The toolbox and the English routes** reach these tools.
* **The build-pending note** is on every answer exactly while the register of
  provisional families lists the module (absorbed ahead of the owner's build).
* **Exactness**: no float anywhere in the figures (directive D7).

Plain test functions (runnable by ``glm_universal.intake.fallback_tests``).
"""
from __future__ import annotations

import re
from fractions import Fraction

from glm_universal.constants import lean_file
from glm_universal.reasoning import hypothesis_tools as ht
from glm_universal.reasoning.lean_address import declaration_names
from glm_universal.runtime import toolbox as tb


def _rule30_centre(n: int):
    """The first ``n`` centre cells of Rule 30 from one black cell, by a
    plain simulation on a list of cells (independent of the engine):
    ``new[i] = old[i-1] XOR (old[i] OR old[i+1])``."""
    width = 2 * n + 3
    row = [0] * width
    centre = width // 2
    row[centre] = 1
    out = []
    for _ in range(n):
        out.append(row[centre])
        row = [(row[i - 1] if i > 0 else 0) ^ (row[i] | (row[i + 1] if i + 1 < width else 0))
               for i in range(width)]
    return out


def _floats(x) -> bool:
    if isinstance(x, float):
        return True
    if isinstance(x, dict):
        return any(_floats(v) for v in x.values())
    if isinstance(x, (list, tuple)):
        return any(_floats(v) for v in x)
    return False


def _lean_centre_bits():
    text = lean_file("RequestProject/GLM/IntakeChecks/RuleThirtyBits.lean").read_text(
        encoding="utf-8")
    m = re.search(r"theorem centreBits_64\s*:\s*centreBits\s+64\s*=\s*\[([a-z,\s]+)\]", text)
    assert m, "theorem centreBits_64 : centreBits 64 = [...] not found in RuleThirtyBits.lean"
    return [1 if x == "true" else 0 for x in re.findall(r"true|false", m.group(1))]


# --- tool rule30 centre ----------------------------------------------------

def test_the_simulation_here_is_rule_30():
    # The well-known start of the centre column (OEIS A051023).
    assert _rule30_centre(16) == [1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1]


def test_centre_64_is_the_list_lean_proves():
    ok, text, fig = ht.rule30_text("centre 64")
    assert ok, text
    assert fig["prefix"] == "".join(map(str, _lean_centre_bits()))
    assert fig["prefix"] == "".join(map(str, _rule30_centre(64)))
    assert ht.LEAN_CENTRE in fig["lean"]


def test_centre_long_column_matches_the_simulation():
    ok, text, fig = ht.rule30_text("centre 1000")
    assert ok, text
    bits = _rule30_centre(1000)
    assert fig["black"] == sum(bits)
    assert fig["share"] == str(Fraction(sum(bits), 1000))


def test_centre_refusals():
    for arg in ("centre 0", f"centre {ht.MAX_CENTRE + 1}", "centre many"):
        ok, text, fig = ht.rule30_text(arg)
        assert not ok and fig["status"] == "refused", arg


def test_the_lean_names_cited_exist_in_the_development():
    names = declaration_names()
    assert ht.LEAN_CENTRE in names
    assert ht.LEAN_STEP in names


# --- tool rule30 claim -----------------------------------------------------

def test_a_proved_claim_is_known_with_its_theorem():
    ok, text, fig = ht.rule30_text("claim the least period of right diagonal D divides 2^D")
    assert ok, text
    assert fig["answer"] is True and fig["ring"] == "knows"
    assert fig["lean"] and not fig["lean_not_found"]
    assert all(n in declaration_names() for n in fig["lean"])


def test_a_false_claim_is_refuted():
    ok, text, fig = ht.rule30_text("claim every left diagonal has eventual period dividing 8")
    assert ok, text
    assert fig["answer"] is False and fig["ring"] == "knows"
    assert "400" in fig["reason"]          # the counterexample diagonal


def test_an_open_claim_is_neither_true_nor_false():
    ok, text, fig = ht.rule30_text("claim the periods of the left diagonals are unbounded")
    assert fig["answer"] is None
    assert fig["ring"] == "doesn't know"
    assert not ok


def test_an_unrecognised_sentence_is_refused():
    ok, text, fig = ht.rule30_text("claim rule 30 is beautiful")
    assert not ok and fig["status"] == "refused"
    assert "recognises no Rule 30 family" in text


def test_the_battery():
    ok, text, fig = ht.rule30_text("battery")
    assert ok, text
    sc = fig["score"]
    assert sc["n"] == 39 and sc["wrong"] == 0 and sc["overclaim"] == 0
    assert sc["right"] == 39
    assert sum(fig["rings"].values()) == 39


# --- tool conjecture -------------------------------------------------------

def test_parse_conjecture():
    assert ht.parse_conjecture("2n + 1 is odd for every n")[0] == "(2*n + 1) % 2 == 1"
    assert ht.parse_conjecture("n^2 + n + 41 is prime for every n >= 3")[:2] == \
        ("isprime(n**2 + n + 41)", 3)
    assert ht.parse_conjecture("6 divides n^3 - n")[0] == "(n**3 - n) % (6) == 0"
    assert ht.parse_conjecture("the sky is blue")[0] is None
    assert ht.parse_conjecture("__import__('os') == n")[0] is None


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def test_a_false_conjecture_is_refuted_with_a_checked_counterexample():
    ok, text, fig = ht.conjecture_text("n^2 + n + 41 is prime for every n")
    assert ok, text
    assert fig["answer"] is False
    n = int(re.search(r"n = (\d+)", fig["reason"]).group(1))
    assert not _is_prime(n * n + n + 41)


def test_a_surviving_conjecture_is_never_called_proved():
    ok, text, fig = ht.conjecture_text("6 divides n^3 - n for every n")
    assert ok, text
    assert fig["answer"] is None and fig["ring"] == "thinks true"
    assert "proved" not in fig["reason"]


def test_a_registered_claim_is_answered_with_its_theorem():
    ok, text, fig = ht.conjecture_text("euler")
    assert ok, text
    assert fig["answer"] is False
    assert fig["lean"] and all(n in declaration_names() for n in fig["lean"])


def test_a_conjecture_beyond_reach_is_read_only_within_the_work_bound():
    # n ** n at n = 20000 has about 286,000 bits: the reading stops at a scale
    # instead of running on, and the answer says where.
    ok, text, fig = ht.conjecture_text("n**n > 0 for every n")
    assert ok, text
    assert fig["answer"] is None and fig["stopped_at"] is not None
    assert fig["scales"] == [s for s in ht.CONJECTURE_SCALES if s < fig["stopped_at"]]
    assert "work bound" in text
    ok2, text2, fig2 = ht.conjecture_text("sum(range(10**12)) > n")
    assert not ok2 and fig2["status"] == "refused"


def test_a_conjecture_refusal():
    ok, text, fig = ht.conjecture_text("the sky is blue")
    assert not ok and fig["status"] == "refused"


# --- tool arc --------------------------------------------------------------

def test_arc_plan_search_answers_a_task_the_colour_solver_refuses():
    ok, text, fig = ht.arc_combined_text("d631b094")
    assert ok, text
    assert fig["status"] == "right"
    assert "plan search" in fig["solvers"]


def test_arc_colour_answer_is_kept():
    from glm_universal.reasoning import colour_induction as ci
    assert ht.arc_combined_text("1e0a9b12") == ci.arc_text("1e0a9b12")


# --- the toolbox and the English routes ------------------------------------

def test_the_toolbox_reaches_the_tools():
    for q, tool in (("tool rule30 centre 10", "rule30"), ("tool conjecture euler", "conjecture"),
                    ("tool arc d631b094", "arc")):
        got = tb.run_tool(q)
        assert got.ok, (q, got.text)
        assert tb.tool_named(tool) is not None


def test_the_english_routes():
    cases = {
        "what are the first 20 cells of rule 30's centre column": "tool rule30 centre 20",
        "in rule 30, the least period of right diagonal D divides 2^D":
            "tool rule30 claim the least period of right diagonal D divides 2^D",
        "score the rule 30 battery": "tool rule30 battery",
        "is n^2 + n + 41 prime for every n": "tool conjecture n^2 + n + 41 is prime for every n",
        "check the conjecture that 6 divides n^3 - n for every n":
            "tool conjecture 6 divides n^3 - n for every n",
    }
    for text, asked in cases.items():
        assert tb.phrase_tool(text) == asked, text


# --- the build-pending note ------------------------------------------------

def test_the_build_note_follows_the_register():
    # While the register of provisional families lists this module (the item
    # absorbed ahead of the owner's Lean build), every answer says so.
    from glm_universal.wheels import provisional_items
    listed = any(ht.MODULE in tuple(e.get("modules") or ())
                 for e in provisional_items().values())
    note = ht.build_note()
    assert (note is not None) == listed
    ok, text, fig = ht.rule30_text("centre 5")
    if listed:
        assert f"[{note}]" in text and fig["provisional"] == note
        assert "rebuild_lean.sh" in note
    else:
        assert "provisional" not in fig


# --- exactness -------------------------------------------------------------

def test_no_float_in_the_figures():
    for got in (ht.rule30_text("centre 100"), ht.conjecture_text("2^n > n for every n"),
                ht.arc_combined_text("d631b094")):
        assert not _floats(got[2])
