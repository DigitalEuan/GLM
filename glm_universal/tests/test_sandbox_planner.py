"""Tests for ``sandbox/planner`` -- the occupant of the sandbox, and its walls.

``studies/REVERSE_CALL_PLANNER_STUDY.md`` builds a problem-driven front end:
instead of dispatching on a query kind decided before the problem is read, it
inspects the problem and selects tools by declared precondition.  Directive D14
keeps it isolated until it earns its way out.  These tests hold the two things
that matter while it is in there:

* **the walls** -- no shipped module imports the sandbox, so deleting the
  directory cannot change a single answer the system gives.  The one declared
  exception is the documentation layer (``corpus.render``, ``corpus.cost`` and
  the command-line reporter), which import it *lazily*, inside the function
  that reports on it.  This is checked with :mod:`ast` over the sources rather
  than trusted;
* **the checklist** -- every promotion line is computed, ``ready`` is their
  conjunction, and the module is not promoted while any line is false.  The
  test that matters is the negative one: the utility gate is false today, and
  a test asserting so fails the moment somebody quietly relaxes it.

The tool registry, the parser and the budget are checked cheaply.  The two
readings that run the whole evaluation set are marked ``exhaustive``:
they certify rather than sample, and the sign-off runner turns them on.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from glm_universal.evaluation import cases as ev_cases
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import pipeline as ppl
from glm_universal.runtime import escalation_loop as esl
from glm_universal.sandbox import planner as pl

PACKAGE_ROOT = Path(pl.__file__).resolve().parents[1]

#: The declared exception to the isolation rule: the documentation layer may
#: import the sandbox, lazily, inside the code that reports on it.
DECLARED_IMPORTERS = {"corpus/cost.py", "corpus/render.py", "tools.py"}


@pytest.fixture(scope="module")
def report():
    return pl.planner_report()


# ---------------------------------------------------------------------------
#  1.  The walls
# ---------------------------------------------------------------------------

def _sandbox_imports(path: Path):
    """Every import of the sandbox in one file, and whether it is lazy.

    Laziness is decided in the *same* parse the import was found in: a node
    from one ``ast.parse`` is never identical to the corresponding node of
    another, so the two questions have to be asked of one tree.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    inside_a_function = set()
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(parent):
                inside_a_function.add(id(child))
    found = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            dots = "." * node.level
            names = [dots + module] + [f"{dots}{module}.{a.name}"
                                       for a in node.names]
        if any("sandbox" in name for name in names):
            found.append((node, id(node) in inside_a_function))
    return found


def test_no_shipped_module_imports_the_sandbox():
    offenders = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        if relative.startswith(("sandbox/", "tests/")):
            continue
        if not _sandbox_imports(path):
            continue
        if relative in DECLARED_IMPORTERS:
            continue
        offenders.append(relative)
    assert offenders == [], (
        "D14: nothing the system computes with may import the sandbox")


def test_the_declared_importers_are_the_documentation_layer_and_are_lazy():
    for relative in sorted(DECLARED_IMPORTERS):
        path = PACKAGE_ROOT / relative
        assert path.is_file(), relative
        nodes = _sandbox_imports(path)
        assert nodes, f"{relative} no longer imports the sandbox"
        for node, lazy in nodes:
            assert lazy, (
                f"{relative}: the declared exception is a *lazy* import, "
                f"inside the function that reports on the sandbox "
                f"(line {node.lineno})")


def test_the_sandbox_is_not_a_report_subject():
    """Wiring it into the runtime would be the wall coming down."""
    from glm_universal.runtime.session import REPORT_SUBJECTS
    for subject in REPORT_SUBJECTS:
        assert "planner" not in subject
        assert "sandbox" not in subject


def test_the_pipeline_row_declares_that_it_is_not_wired():
    row = next(r for r in ppl.REGISTRY if r.key == "reverse-call-planner")
    assert row.document == "REVERSE_CALL_PLANNER_STUDY.md"
    assert row.modules == ("sandbox/planner.py",)
    assert row.subject is None
    assert row.wire_expected is False
    assert row.lean_expected is False
    assert row.lean == ()
    stage = ppl.stage_report(row)
    assert stage["complete"] is True        # unwired by declaration, not blocked


# ---------------------------------------------------------------------------
#  2.  The tools, and how one is selected
# ---------------------------------------------------------------------------

def test_every_tool_declares_a_precondition_a_cost_and_a_postcondition():
    assert len(pl.REGISTRY) >= 8
    names = [tool.name for tool in pl.REGISTRY]
    assert len(names) == len(set(names))
    for tool in pl.REGISTRY:
        assert tool.goals
        assert callable(tool.applies_to)
        assert callable(tool.run)
        assert tool.postcondition
        assert isinstance(tool.cost, int) and tool.cost > 0


def test_selection_is_by_precondition_and_ordered_by_cost():
    problem = pl.parse_problem("describe energy")
    tools = pl.applicable(problem)
    assert tools
    assert [tool.cost for tool in tools] == sorted(tool.cost
                                                   for tool in tools)
    for tool in tools:
        assert tool.applies_to(problem) is True


def test_a_problem_is_a_goal_and_operands_and_not_a_query_kind():
    problem = pl.parse_problem("verify energy = force * length")
    assert problem.goal == "verify"
    assert problem.operands
    assert problem.raw == "verify energy = force * length"


def test_the_budget_is_declared_and_finite():
    assert isinstance(pl.BUDGET, int) and pl.BUDGET > 0
    assert isinstance(pl.MAX_DEPTH, int) and pl.MAX_DEPTH >= 1


def test_a_plan_keeps_every_tool_it_tried_including_the_refusals():
    result = pl.ask("describe unobtainium")
    assert result.answered is False
    assert result.tried
    assert result.refusals
    assert result.refusal_tag is not None
    assert result.cost == sum(step.cost for step in result.steps)


def test_an_answer_carries_the_tool_that_produced_it_and_its_check():
    result = pl.ask("verify energy = force * length")
    assert result.answered is True
    assert result.tool is not None
    assert result.verified is True


def test_a_principled_refusal_stops_the_plan_rather_than_shopping():
    result = pl.ask("Ca : Sc :: Ba : ?")
    assert result.answered is False
    assert result.refusal_tag != esl.ESCALATABLE
    assert "stopped" in result.answer


def test_planning_the_same_problem_twice_gives_the_same_plan():
    first = pl.ask("describe energy")
    second = pl.ask("describe energy")
    assert (first.answer, first.cost, first.tool) == \
        (second.answer, second.cost, second.tool)


def test_the_module_holds_no_float():
    assert ex.module_float_sites(Path(pl.__file__)) == {}


# ---------------------------------------------------------------------------
#  3.  The declared task set
# ---------------------------------------------------------------------------

def test_the_task_set_contains_tasks_it_is_expected_to_refuse():
    assert len(pl.TASKS) == 15
    for question, purpose in pl.TASKS:
        assert question and purpose
    assert any("refused" in purpose for _question, purpose in pl.TASKS)


@pytest.mark.exhaustive
def test_the_declared_tasks_are_answered_and_checked(report):
    assert len(report["tasks"]) == len(pl.TASKS)
    assert report["answered"] == 10
    assert report["verified"] == report["answered"]
    assert len(report["answered_beyond_the_runtime"]) == 5
    for row in report["tasks"]:
        if row["answered"]:
            assert row["verified"] is True, row["task"]
        else:
            assert row["refusal_tag"], row["task"]


# ---------------------------------------------------------------------------
#  4.  The promotion checklist, and the line that is false
# ---------------------------------------------------------------------------

@pytest.mark.exhaustive
def test_the_checklist_is_computed_and_ready_is_its_conjunction(report):
    promotion = report["promotion"]
    checks = promotion["checks"]
    assert set(checks) == {
        "deterministic", "exact", "no_regression_against_the_runtime",
        "every_refusal_classified", "every_answer_independently_checked",
        "no_principled_refusal_reaches_the_planner",
        "answers_something_the_runtime_does_not"}
    for value in checks.values():
        assert isinstance(value, bool)
    assert promotion["ready"] is all(checks.values())


@pytest.mark.exhaustive
def test_the_safety_gate_holds_and_the_utility_gate_does_not(report):
    """The state the round left, and the reason the module is not promoted."""
    checks = report["promotion"]["checks"]
    assert checks["no_principled_refusal_reaches_the_planner"] is True
    assert checks["answers_something_the_runtime_does_not"] is False
    assert report["promotion"]["ready"] is False


@pytest.mark.exhaustive
def test_the_fallback_is_measured_over_the_whole_evaluation_set(report):
    fallback = report["fallback"]
    assert fallback["cases"] == len(ev_cases.CASES)
    #  Four when the reading was first taken, seven since the field surface
    #  added three refusals of its own (an unknown field, an unknown row and
    #  a value the register records as missing).  The measurement moved with
    #  the evaluation set; what it says did not.
    assert fallback["planner_consulted"] == 7
    assert fallback["gained"] == ()
    assert fallback["principled_refusals_offered_to_the_planner"] == ()
    assert fallback["safety_holds"] is True
    assert fallback["utility_holds"] is False
    assert "consulted only on a refusal" in str(fallback["rule"])


def test_the_number_of_workers_is_declared_and_overridable(monkeypatch):
    monkeypatch.setenv("GLM_PLANNER_JOBS", "1")
    assert pl.fallback_jobs() == 1
    monkeypatch.setenv("GLM_PLANNER_JOBS", "3")
    assert pl.fallback_jobs() == 3
    monkeypatch.setenv("GLM_PLANNER_JOBS", "not a number")
    assert pl.fallback_jobs() == 1
    monkeypatch.delenv("GLM_PLANNER_JOBS")
    assert pl.fallback_jobs() >= 1


def test_the_reading_is_the_same_read_in_parallel_as_read_in_order():
    """Splitting the cases across processes is a speed-up, not a change.

    Checked on a sample rather than on all 149: the whole reading is what the
    exhaustive cases above run, and what matters here is that a row does not
    depend on which process computed it or on the order they finished in.
    """
    from concurrent.futures import ProcessPoolExecutor

    sample = [0, 1, 2, 3]
    in_order = [pl.fallback_row(index) for index in sample]
    with ProcessPoolExecutor(max_workers=2) as pool:
        in_parallel = list(pool.map(pl.fallback_row, sample, chunksize=1))
    assert in_parallel == in_order


def test_the_gate_is_measured_against_a_set_the_module_did_not_choose():
    """D14 asks for at least one gate on the whole evaluation set."""
    from glm_universal.evaluation import cases as ev
    assert "evaluation" in pl.fallback_rows.__doc__
    assert len(ev.CASES) > 100


@pytest.mark.exhaustive
def test_the_by_product_is_two_questions_the_shipped_classifier_does_not_mark():
    """The planner marks two refusals ill formed that the shipped list misses.

    Seven refusals reach the planner since the field surface added three of
    its own; all seven stop, and the two the planner marks are the two it
    marked when four reached it, so the by-product is the same finding over a
    larger set.
    """
    rows = [row for row in pl.fallback_rows() if row["planner_consulted"]]
    assert len(rows) == 7
    stopped = [row for row in rows
               if not row["planner_answered"]
               and row["refusal_tag"] == esl.ESCALATABLE]
    assert len(stopped) == 7
    marked_by_the_planner = [row["question"] for row in stopped
                             if pl.ask(str(row["question"])).refusal_tag
                             != esl.ESCALATABLE]
    assert len(marked_by_the_planner) == 2


# ---------------------------------------------------------------------------
#  7.  The report, kept rather than re-taken
# ---------------------------------------------------------------------------
#
#  Taking the report asks the live runtime every evaluation case and costs
#  about a minute and a half.  Five generated blocks quote it, so a document
#  check used to pay for it five times.  It is now memoised within a process
#  and stored across processes beside the digest of the code it is derived
#  from -- and a cache of a measurement is only admissible if it is the same
#  measurement, which is what these check.

def test_the_report_is_memoised_but_the_derivation_stays_reachable():
    assert pl.planner_report() is pl.planner_report()
    assert callable(getattr(pl.planner_report, "__wrapped__", None))
    assert callable(getattr(pl.task_rows, "__wrapped__", None))
    assert callable(getattr(pl.fallback_rows, "__wrapped__", None))


def test_the_determinism_line_is_measured_against_an_uncached_run():
    """A memo compared with itself would make the checklist true for free."""
    source = inspect.getsource(pl.promotion_checklist)
    assert "task_rows.__wrapped__()" in source
    assert pl.task_rows.__wrapped__() == pl.task_rows()


def test_the_stored_report_renders_the_blocks_the_fresh_one_renders(report):
    from glm_universal.corpus import render as rd

    names = [name for name in rd.BLOCKS if name.startswith("plannersandbox")]
    assert names
    cached = pl.cached_planner_report()
    fresh = {name: rd._render_block(name) for name in names}
    original = pl.cached_planner_report
    try:
        pl.cached_planner_report = lambda: report
        from_fresh = {name: rd._render_block(name) for name in names}
    finally:
        pl.cached_planner_report = original
    assert fresh == from_fresh
    assert cached["answered"] == report["answered"]
    assert cached["promotion"]["ready"] == report["promotion"]["ready"]


def test_the_stored_report_is_keyed_on_the_code_and_not_on_the_documents():
    pl.cached_planner_report()
    state = pl.report_cache_state()
    assert state["present"] is True
    assert state["verdict"] == "fresh"
    paths = [str(p) for p in pl._report_store().input_paths()]
    assert any(p.endswith("sandbox/planner.py") for p in paths)
    assert not any(p.endswith(".md") for p in paths)


def test_the_checklist_carries_the_order_its_lines_are_read_in():
    """JSON keeps a list in order and a mapping in whatever order it likes."""
    promotion = pl.planner_report()["promotion"]
    assert tuple(promotion["order"]) == tuple(promotion["checks"])
