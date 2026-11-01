"""Tests for :mod:`glm_universal.reasoning.intake_capability_study` -- the
marks of ``studies/INTAKE_CAPABILITY_STUDY.md`` (Phase 186: what the intake
items absorbed on 1 November 2026 add to the GLM on ARC, Rule 30 and
reasoning across domains, with and without them).

*Created 1 November 2026 (Phase 186).*

What is pinned:

* **The switch** :func:`without_phase186` takes the three Phase 186 tools and
  their English routes out of the toolbox, puts ``tool arc`` on the colour
  solver alone and the ``sequence`` kind without its ``next`` reading -- and
  restores all of it on leaving, even when the body raises.
* **The plain simulation** the study checks ``tool rule30`` against is Rule 30
  (its first 64 cells are the list ``IntakeChecks/RuleThirtyBits.lean``
  states, read out of the Lean file).
* **The grading** of an answer: a verdict is read whether the claim is quoted
  in single or double quotes; a refusal is right only for a question to
  refuse or an open claim; a stated next term, law verdict or ARC grade is
  read off the reply.
* **The twelve conjectures**: each false one has a least counterexample
  (found here) that its plain predicate rejects; each true one survives the
  first 64 values.
* **The thirty questions across domains**: six in each of five domains, ids
  X01-X30, the ARC ones the first six stored tasks in name order.
* **The Lean part**: the four standalone files present, their theorems stated,
  no ``sorry``, each imported by ``AxiomAuditAll.lean``.
* **The stored measurement**, when current: 12 of 14 marks, R2 and S2 missed,
  and the figures the study quotes.

Plain test functions (runnable by ``glm_universal.intake.fallback_tests``).
"""
from __future__ import annotations

from glm_universal.reasoning import colour_induction as ci
from glm_universal.reasoning import intake_capability_study as S


def test_the_switch_takes_out_phase186_and_restores_it():
    from glm_universal.runtime import toolbox as tb
    from glm_universal.wheels import sequence_query as sq
    before = (tb.TOOLS, tb.TOOL_PHRASES, tb._hypothesis_tools, sq.resolve_query)
    names = {t.name for t in tb.TOOLS}
    for tool in S.PHASE186_TOOLS:
        assert tool in names, tool
    with S.without_phase186():
        inside = {t.name for t in tb.TOOLS}
        assert not set(S.PHASE186_TOOLS) & inside
        assert all(t.split()[1] not in S.PHASE186_TOOLS for _p, t in tb.TOOL_PHRASES)
        assert tb._hypothesis_tools() is None
        assert tb.phrase_tool("is force = mass * acceleration a law") is None
    assert (tb.TOOLS, tb.TOOL_PHRASES, tb._hypothesis_tools, sq.resolve_query) == before
    try:
        with S.without_phase186():
            raise RuntimeError("inside")
    except RuntimeError:
        pass
    assert (tb.TOOLS, tb.TOOL_PHRASES, tb._hypothesis_tools, sq.resolve_query) == before


def test_the_plain_simulation_is_rule_30():
    cells = S.plain_centre(64)
    assert cells[:8] == [1, 1, 0, 1, 1, 1, 0, 0]
    assert sum(cells) == 35
    lean = S._lean_centre()
    assert lean == cells


def test_verdicts_read_in_either_quote():
    assert S._verdict_of("rule30: 'x': false -- on the engine's wheel") == "false"
    assert S._verdict_of('rule30: "a left diagonal\'s period": true -- on') == "true"
    assert S._verdict_of("conjecture: 'p for every n': not settled -- on") == "not settled"
    assert S._verdict_of("rule30: refused -- no recogniser reads it") is None


def test_grading_of_answers():
    g = S.grade_answer
    assert g("refuse", None, "refused", "") == "right"
    assert g("open", None, "refused", "") == "right"
    assert g("truth", True, "refused", "") == "refused"
    assert g("truth", False, "answered", "rule30: 'c': false -- x") == "right"
    assert g("truth", True, "answered", "rule30: 'c': false -- x") == "wrong"
    assert g("truth", True, "answered", "rule30: 'c': not settled -- x") == "refused"
    assert g("survives", None, "answered", "conjecture: 'c': not settled -- x") == "right"
    assert g("survives", None, "answered", "conjecture: 'c': false -- x") == "wrong"
    assert g("derive", "derivable", "answered", "derive: derivable in W5 -- ...") == "right"
    assert g("derive", "derivable", "answered", "derive: not derivable -- ...") == "wrong"
    assert g("next", 132, "answered", "132 — the next term of A000108") == "right"
    assert g("next", 132, "answered", "131 — the next term of A000000") == "wrong"
    assert g("refuse", None, "answered", "32 — the next term of A000079") == "wrong"
    assert g("arc", "x", "answered", "arc 1e0a9b12: RIGHT from 3 training pairs") == "right"
    assert g("arc", "x", "answered", "arc 1e0a9b12: WRONG from 3 training pairs") == "wrong"
    assert g("bits", "1101", "answered", "from one black cell: 1101; 3 black") == "right"
    assert g("bits", "1101", "answered", "from one black cell: 1111; 4 black") == "wrong"
    assert g("next", 5, "answered", "no number here") == "unread"


def test_the_twelve_conjectures():
    assert len(S.CONJECTURES) == 12
    assert len({c[0] for c in S.CONJECTURES}) == 12
    for cid, _sentence, truth, check, start in S.CONJECTURES:
        least = S._least_counterexample(check, start)
        if truth:
            assert least is None, cid
        else:
            assert least is not None and not check(least), cid
            assert all(check(n) for n in range(start, least)), cid


def test_the_thirty_questions_across_domains():
    qs = S.cross_domain_questions()
    assert [q[0] for q in qs] == [f"X{i:02d}" for i in range(1, 31)]
    domains = [q[1] for q in qs]
    for d in ("rule30", "number", "physics", "sequence", "arc"):
        assert domains.count(d) == 6, d
    arc = [q[4] for q in qs if q[1] == "arc"]
    assert arc == ci.arc_names()[:6]
    assert qs[0][4] == "".join(map(str, S.plain_centre(20)))
    assert dict((q[0], q[4]) for q in qs)["X19"] == 132


def test_the_lean_part():
    L = S.lean()
    assert len(L["files"]) == 4
    for f in L["files"]:
        assert f["present"], f["file"]
        assert f["stated"] == f["declared"], f["file"]
        assert f["sorry"] == 0, f["file"]
        assert f["audited"], f["file"]


def test_stored_measurement_when_current():
    r = S.current()
    if r is None:
        return
    assert r["taken"] == 14
    missed = sorted(k for k, v in r["marks"].items() if not v)
    assert missed == ["R2", "S2"], missed
    assert r["met"] == 12
    a = r["arc"]
    assert a["combined"]["wrong"] == 0 and len(a["combined"]["tasks_right"]) == 9
    assert len(a["colour"]["tasks_right"]) == 2
    assert a["development_set"] is True
    x = r["cross_domain"]
    assert (x["with"]["right"], x["with"]["wrong"], x["without"]["right"]) == (23, 0, 4)
    r30 = r["rule30"]
    assert (r30["routed_with"]["right"], r30["routed_with"]["wrong"]) == (16, 0)
    assert r30["answered_without"] == 0
    d = r["derive"]
    assert (d["tool_laws_licensed"], d["tool_not_laws_licensed"]) == (63, 0)
    s = r["next_terms"]["with_wheels"]
    assert (s["positive"]["right"], s["positive"]["wrong"], s["controls"]["right"]) == (27, 0, 12)
