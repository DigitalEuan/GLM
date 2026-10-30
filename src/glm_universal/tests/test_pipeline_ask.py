"""Tests for asking the separating example when ``tool induce`` refuses
(Phase 176).

*Created 21 October 2026.*

``studies/PIPELINE_ASK_STUDY.md`` declared the marks.  These tests pin:

* the **Lean file** states its theorems with no ``sorry``;
* the **true rules** the study uses as the oracle reproduce every family's
  generator;
* the **pool** never offers the query or a demonstration input;
* the **choice** separates the survivors, and on a hand-made tie one reply
  decides the query;
* the **loop** turns that refusal into the true rule's answer, and the
  survivors shrink at the ask (``separating_strict_shrink``);
* ``tool induce``'s refusal names the input to ask about;
* the **stored measurement**, when current, meets every mark.
"""

from __future__ import annotations

from pathlib import Path

from glm_universal.reasoning import pipeline_ask as pa
from glm_universal.reasoning import pipeline_ask_study as pas
from glm_universal.reasoning import pipeline_kit as pk

_ROOT = Path(__file__).resolve().parents[2] / "lean"


def _g(text):
    return pk.parse_grid(text)


def test_lean_file_states_the_theorems_without_sorry():
    text = (_ROOT / pa.LEAN_FILE).read_text(encoding="utf-8")
    for name in pa.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text


def test_true_rules_reproduce_the_generators():
    for name in pk.FAMILIES:
        rule = pa.true_rule(name)
        for s in range(40):
            x, y = pk.sample(name, s)
            assert rule(x) == y, (name, s)


def test_pool_excludes_query_and_demonstrations():
    demos = [pk.sample("toggle", i) for i in range(3)]
    q, _ = pk.sample("toggle", 99)
    pool = pa.candidate_pool(demos, q)
    assert q not in pool
    assert all(x not in pool for x, _ in demos)
    assert len(pool) == len(set(pool)) > 24


def test_choice_separates_and_decides_a_hand_made_tie():
    # complement and "complement then fill_enclosed" agree on demonstrations
    # with no enclosed region and disagree on a query that has one
    demos = [(_g("1010/0101/1010"), _g("0101/1010/0101")),
             (_g("1100/0011/1100"), _g("0011/1100/0011"))]
    q = _g("0000/0110/0000")
    r = pk.solve(demos, q)
    assert r["status"] == "ambiguous"
    live = pa.survivors(demos, q)
    c = pa.separating_input(demos, q, live)
    assert c is not None and c["blocks"] >= 2
    outs = {hy(c["input"]) for hy in live}
    assert len(outs) >= 2
    a = pa.ask_loop(demos, q, pk._complement)
    assert a["status"] == "answered"
    assert a["answer"] == pk._complement(q)
    step = a["asks"][0]
    assert set(step["after"]) < set(step["before"])


def test_tool_refusal_names_the_input():
    from glm_universal.runtime.toolbox import run_tool
    r = run_tool(pas.TOOL_REFUSE)
    assert not r.ok
    assert r.figures["status"] == "ambiguous"
    assert "to settle it, give the output for" in r.text
    assert pk.parse_grid(r.figures["ask"]) is not None


def test_stored_measurement_meets_every_mark():
    stored = pas.current()
    if stored is None:
        return                      # stale or absent: the ledger re-takes it
    assert stored["met"] == stored["taken"] == 8
    t = stored["totals"]
    assert t["wrong"] == 0
    assert t["shrink_exceptions"] == 0
