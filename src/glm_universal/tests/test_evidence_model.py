"""Tests for one evidence and result model (Phase 169).

*Rebuilt 31 October 2026 (repository check).*  The original file was lost in
the October 2026 reorganisation, together with the original
``runtime/evidence.py`` (reconstructed 29 October 2026).
``glm_universal/tests/README.md`` recorded what its six tests pinned, and
this file pins the same six things against ``runtime/evidence.py`` and
``studies/EVIDENCE_MODEL_STUDY.md``, and since the Lean declaration lookup was
restored (31 October 2026) two more:

* a ``Result`` carries the ten fields the plan names;
* ``GLM.`` names are read in first-seen order, and a Python ``repr``'s
  closing quote is not taken for a prime (amendment R5');
* through the adapter, a cited name is checked against the declarations of
  the Lean development: an invented name is cited but not declared, a
  declared name read out of a ``repr`` loses the closing quote, and a
  declared primed name keeps its prime (added 31 October 2026, when the
  declaration lookup was reconstructed), and the census counts an undeclared
  citation against R5;
* a refusal in words is read by the evaluation's markers;
* a corpus term read through ``from_define`` is answered with its quality as
  witness and boundary, and a nonsense word is refused with a reason;
* the trilinear column-3 template replays a triple of bare axis labels (the
  first of the two replay defects of the study's §7.3; this rebuild found the
  repair lost with the upload and restored it);
* the stored measurement, when current, meets all nine marks.
"""

from __future__ import annotations

from glm_universal.runtime import evidence as evm


def test_a_result_carries_the_ten_fields():
    # the ten the plan names, and `replayed` beside them
    assert evm.FIELDS[-1] == "replayed" and len(evm.FIELDS) == 11
    r = evm.Result(question="q", status="answered", surface="planner",
                   kind="trilinear", answer="a")
    d = r.as_dict()
    for name in evm.FIELDS:
        assert name in d, name
    for name in ("answer", "candidates", "evidence", "witness", "theorems",
                 "boundary", "budget", "ambiguity", "refusal", "history"):
        assert name in evm.FIELDS, name
    assert r.answered and not evm.Result(
        question="q", status="refused", surface="planner", kind="x",
        answer="").answered


def test_theorem_names_in_first_seen_order_and_no_quote_for_a_prime():
    # The names are assembled at run time so that this file cites no Lean
    # declaration itself (test_lean_address checks every name the package
    # cites); the shapes are what matter here.
    g = "GLM."
    a, b, c = g + "Alpha.one", g + "Beta.two", g + "Alpha.three"
    text = (f"by {a} and {b}, again {a}; payload ['{c}', '{b}']")
    # the pattern allows Lean's prime, so the repr's closing quote is read
    assert evm._scan_theorems(text) == (a, b, c + "'", b + "'")
    # R5' against the declarations removes it, and the names stay in
    # first-seen order without repeats
    names, declared = evm.cited_theorems(text, declared=[a, b, c])
    assert names == (a, b, c) and declared == (a, b, c)
    assert not any(n.endswith("'") for n in names)
    # a trailing prime is dropped only when the unprimed name is the
    # declared one; a declared primed name is kept as it is
    assert evm._strip_trailing_prime([a + "'"], [a]) == (a,)
    assert evm._strip_trailing_prime([a + "'"], [a, a + "'"]) == (a + "'",)
    assert evm.cited_theorems(f"by {a}'", declared=[a, a + "'"]) == ((a + "'",), (a + "'",))


def _solution(answer):
    from types import SimpleNamespace
    return SimpleNamespace(kind="trilinear", answer=answer, ok=True, error=None,
                           steps=[], expected={}, payload={}, script_spec=None)


def test_the_adapter_checks_citations_against_the_lean_declarations():
    declared = evm.declared_names()
    assert len(declared) > 1000          # the development is read, not assumed
    real = sorted(n for n in declared if not n.endswith("'"))[0]
    primed = sorted(n for n in declared if n.endswith("'"))
    invented = "GLM." + "Invented.not_a_declaration"
    assert invented not in declared
    r = evm.from_solution("q", _solution(
        f"by {real} and {invented}; payload ['{real}']"))
    assert r.theorems == (real, invented)
    assert r.theorems_declared == (real,)          # the invented name is not
    if primed:                                     # a declared primed name
        r = evm.from_solution("q", _solution(f"uses {primed[0]} here"))
        assert r.theorems == r.theorems_declared == (primed[0],)
    # the router's other surfaces read their text the same way
    from types import SimpleNamespace
    routed = SimpleNamespace(surface="toolbox", answered=True,
                             text=f"see {invented}", solution=None, payload=None)
    r = evm.from_routed("q", routed)
    assert r.theorems == (invented,) and r.theorems_declared == ()


def test_the_census_counts_an_undeclared_citation_against_r5():
    from glm_universal.reasoning import evidence_model_study as ems
    report = {"errors": [], "cases": 1, "R2": {"disagree": []},
              "R3": {"with_reason": 0, "refused": 0}, "R4": {"unclassified": []},
              "R5": {"cited": ["x"], "undeclared": ["x"]},
              "R6": {"failed": [], "replayable": 1},
              "R7": {"open": 0, "open_with_candidates": 0, "history_ok": 0,
                     "with_given": 0},
              "R8": {"define": [{"status": "refused", "refusal": "r"}],
                     "turns": [{"status": "x", "candidates": []}, {"history": []}]},
              "R9": {"fields_ok": 1, "results": 1}}
    assert ems._marks(report)["R5"] is False
    report["R5"]["undeclared"] = []
    assert ems._marks(report)["R5"] is True


def test_a_refusal_in_words_is_read_by_the_evaluations_markers():
    from glm_universal.evaluation.harness import REFUSAL_MARKERS
    assert REFUSAL_MARKERS
    for marker in REFUSAL_MARKERS:
        assert evm.refused_in_words(f"the GLM {marker} here")
    assert not evm.refused_in_words("trilinear 127 432 463: <A.B, C> = -3/32")


def test_from_define_answers_a_corpus_term_and_refuses_nonsense():
    from glm_universal.knowledge import model as mdl
    knowledge = mdl.load()
    golay = evm.from_define("golay code", knowledge)
    assert golay.status == "answered"
    assert golay.witness
    assert golay.boundary.startswith("corpus:")
    assert golay.surface == "corpus"
    nonsense = evm.from_define("yalog", knowledge)
    assert nonsense.status == "refused"
    assert nonsense.refusal


def test_trilinear_column3_replays_bare_axis_labels():
    from glm_universal.runtime.session import GeometricSession
    solution = GeometricSession().ask("trilinear 127 432 463")
    assert solution.answer.endswith("= -3/32")
    r = evm.from_solution("trilinear 127 432 463", solution, replay=True)
    assert r.replayed is True
    assert r.boundary == "certified"


def test_stored_measurement_when_current_meets_all_nine_marks():
    from glm_universal.reasoning import evidence_model_study as ems
    stored = ems.current()
    if stored is None:
        return            # stale or absent: the study's own command re-takes it
    assert sorted(stored["marks"]) == [f"R{i}" for i in range(1, 10)]
    assert stored["met"] == 9, stored["marks"]
