"""``glm_universal.sandbox.planner`` -- the reverse-call planner, in the sandbox.

What it is
----------
The shipped runtime dispatches on a **query kind** decided by the parser before
the problem is inspected: one kind, one solver.  The reverse-call planner turns
that around.  A string becomes a **Problem** -- a goal, operands, a domain and
constraints -- and a **Planner** inspects the problem, selects every tool whose
declared precondition it satisfies, runs them in cost order, checks each result
against an independent verifier where one exists, and composes what comes back
into one answer with its cost and its evidence.  If every tool refuses, the
plan names every tool it tried and why each refused.

    string -> Problem (goal, operands, domain, constraints)
           -> Planner selects tools by precondition, not by kind
           -> tools run cheapest first, each checked
           -> results composed into one Solution with a cost
           -> if all refuse, every tool tried is named, with its reason

Why it is in the sandbox
------------------------
Because a front end that can call anything is exactly the sort of thing that
quietly starts answering questions the runtime is right to refuse.  The
promotion checklist at the bottom of this module is the price of leaving the
sandbox, and it is **computed**, not asserted: determinism, exactness, no
regression against the runtime, every refusal classified, and every answer
either independently verified or reported as unverified.

What it takes from the escalation round
---------------------------------------
Three things, and they are what makes this more than a tool loop:

1. **Refusals are classified before they are worked around.**  The planner uses
   the same declared classifier as
   :mod:`glm_universal.runtime.escalation_loop`: a refusal that is *principled*
   -- ill formed, underdetermined, or grounded in no register -- stops the
   plan.  A planner that tries eleven tools against a question that is
   underdetermined has not been thorough, it has been noisy.
2. **Cost is charged and reported.**  Every tool run adds its declared integer
   cost, and the plan reports the total.  A cheap verified answer beats an
   expensive one; an unverified answer never displaces a verified one.
3. **The escalation loop is itself a tool.**  When the plain register reading
   refuses, the planner may spend the loop's cost to climb the declared ladder,
   and the answer carries the layer it was found at.

Exactness
---------
Integers and :class:`~fractions.Fraction` only; no float is constructed here,
no random source is consulted, and tool selection is by precondition rather
than by any digest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from ..data_objects import physics as do_physics
from ..reasoning import controller as ctl
from ..reasoning import dimension_layers as dl
from ..reasoning import real_expr as rx
from ..reasoning import term_arithmetic as tar
from ..reasoning import verifier as ve
from ..runtime import escalation_loop as esl
from ..semantics import reference as rf

__all__ = [
    "Problem", "ToolResult", "Tool", "Plan", "PlanStep",
    "REGISTRY", "BUDGET", "parse_problem", "applicable", "plan",
    "TASKS", "task_rows", "promotion_checklist", "planner_report",
    "FALLBACK_RULE", "fallback_row", "fallback_rows", "fallback_jobs",
    "fallback_reading",
    "REPORT_STORE", "cached_planner_report", "report_cache_state",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE THREE CARRIERS
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Problem:
    """What the planner works on: a goal and its operands, not a query kind."""

    raw: str
    goal: str
    operands: Tuple[str, ...] = ()
    domain: Optional[str] = None
    constraints: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    """What one tool returned, and whether anything checked it."""

    tool: str
    answered: bool
    answer: str
    evidence: Dict[str, object] = field(default_factory=dict)
    sub_goals: Tuple[Problem, ...] = ()
    refusal: Optional[str] = None
    verified: bool = False
    verifier: Optional[str] = None


@dataclass(frozen=True)
class Tool:
    """A reasoning module the planner may invoke.

    ``applies_to`` is a cheap precondition on the *problem*, which is what
    makes selection problem-driven; ``cost`` is the declared integer price of
    running it, and ``check`` is an independent verifier where one exists.
    """

    name: str
    goals: Tuple[str, ...]
    applies_to: Callable[[Problem], bool]
    run: Callable[[Problem], ToolResult]
    postcondition: str
    cost: int = 1
    check: Optional[Callable[[Problem, ToolResult], Tuple[bool, str]]] = None


@dataclass(frozen=True)
class PlanStep:
    """One tool invocation, kept whatever it returned."""

    tool: str
    cost: int
    outcome: str          # "answered" | "refused" | "skipped"
    detail: str


@dataclass(frozen=True)
class Plan:
    """What a plan returns: the composed answer, its cost, and its record."""

    problem: Problem
    answered: bool
    answer: str
    tool: Optional[str]
    cost: int
    verified: bool
    steps: Tuple[PlanStep, ...]
    tried: Tuple[str, ...]
    refusals: Tuple[Tuple[str, str], ...] = ()
    refusal_tag: Optional[str] = None
    sub_plans: Tuple["Plan", ...] = ()

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "goal": self.problem.goal,
            "operands": list(self.problem.operands),
            "answered": self.answered,
            "answer": self.answer,
            "tool": self.tool,
            "cost": self.cost,
            "verified": self.verified,
            "tried": list(self.tried),
            "refusals": [list(row) for row in self.refusals],
            "refusal_tag": self.refusal_tag,
            "steps": [{"tool": s.tool, "cost": s.cost, "outcome": s.outcome,
                       "detail": s.detail} for s in self.steps],
            "sub_plans": [p.as_dict() for p in self.sub_plans],
        }


#: The declared cost budget of one plan.  A plan that would exceed it stops and
#: says so, which is the controller's ``exhausted`` refusal in another place.
BUDGET: int = 12

#: How deep a sub-goal may be planned.  Two: a tool may ask for a check, and
#: the check may ask for one more thing, and then it is over.
MAX_DEPTH: int = 2


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE SESSION THE TOOLS SHARE
# ═════════════════════════════════════════════════════════════════════════

_SESSION = None


def session():
    """One session, built on first use: loading the registers is the cost."""
    global _SESSION
    if _SESSION is None:
        from ..runtime.session import GeometricSession
        _SESSION = GeometricSession()
    return _SESSION


def reset_session() -> None:
    """Forget the shared session.  Only ever a memory concern."""
    global _SESSION
    _SESSION = None


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE TOOLS
# ═════════════════════════════════════════════════════════════════════════

def _is_quantity(name: str) -> bool:
    try:
        return do_physics.quantity_by_name(name) is not None
    except (KeyError, AttributeError):
        return False


# --- the register reading -------------------------------------------------

def _runtime_applies(problem: Problem) -> bool:
    return problem.goal in ("describe", "nearest", "verify", "analogy",
                            "report", "coherence", "meaning", "approximate")


def _runtime_run(problem: Problem) -> ToolResult:
    solution = session().ask(problem.raw)
    if solution.ok:
        return ToolResult("runtime", True, solution.answer,
                          evidence={"kind": solution.kind})
    return ToolResult("runtime", False, "", refusal=str(solution.error))


# --- the escalation loop --------------------------------------------------

def _escalated_applies(problem: Problem) -> bool:
    return _runtime_applies(problem)


def _escalated_run(problem: Problem) -> ToolResult:
    climb = session().escalate(problem.raw)
    if climb.answered:
        return ToolResult(
            "escalated_runtime", True, climb.solution.answer,
            evidence={"layer": climb.layer, "ladder": list(climb.ladder),
                      "loop_cost": climb.cost},
            verified=True, verifier="the ladder reports the layer it answered "
                                    "at, and that the rungs below refused")
    return ToolResult("escalated_runtime", False, "",
                      evidence={"layer": climb.layer,
                                "certified_absence": climb.certified_absence},
                      refusal=climb.verdict)


# --- the reference layer --------------------------------------------------

def _reference_applies(problem: Problem) -> bool:
    return problem.goal in ("describe", "meaning") and bool(problem.operands)


def _reference_run(problem: Problem) -> ToolResult:
    term = problem.operands[0]
    resolution = rf.resolve(term)
    if resolution.meaning is None:
        return ToolResult("reference", False, "",
                          refusal=f"{term!r}: {resolution.reason}")
    return ToolResult(
        "reference", True,
        f"{term!r} denotes {resolution.meaning.describe()} "
        f"(sense {resolution.sense})",
        evidence={"sense": resolution.sense, "witness": resolution.witness})


# --- the controller's search ----------------------------------------------

def _controller_applies(problem: Problem) -> bool:
    return (problem.goal == "derive" and bool(problem.operands)
            and _is_quantity(problem.operands[0]))


def _controller_run(problem: Problem) -> ToolResult:
    name = problem.operands[0]
    outcome = ctl.solve(name)
    if not outcome.get("answered"):
        refusal = outcome.get("refusal") or {}
        return ToolResult("controller", False, "",
                          evidence=dict(outcome),
                          refusal=str(refusal.get("reason", "refused")))
    expression = str(outcome.get("expression", ""))
    return ToolResult(
        "controller", True,
        f"{name} = {expression} "
        f"({outcome.get('length')} moves, minimal={outcome.get('minimal')})",
        evidence={"expression": expression, "length": outcome.get("length"),
                  "minimal": outcome.get("minimal")},
        sub_goals=(Problem(raw=f"verify {name} = {expression}", goal="verify",
                           operands=(name, expression), domain="physics"),))


def _controller_check(problem: Problem,
                      result: ToolResult) -> Tuple[bool, str]:
    """Independently: does the derived expression have the target's dimension?"""
    name = problem.operands[0]
    expression = str(result.evidence.get("expression", ""))
    verdict = ve.verify_expression_pair(name, expression, "scalar")
    if verdict.parse_error:
        return False, f"the verifier could not parse it: {verdict.parse_error}"
    return bool(verdict.holds), ("the verifier agrees the two sides have the "
                                 "same dimension" if verdict.holds else
                                 "the verifier says the dimensions differ")


# --- the verifier ---------------------------------------------------------

def _verifier_applies(problem: Problem) -> bool:
    return problem.goal == "verify" and len(problem.operands) >= 2


def _verifier_run(problem: Problem) -> ToolResult:
    left, right = problem.operands[0], problem.operands[1]
    verdict = ve.verify_expression_pair(left, right, "scalar")
    if verdict.parse_error:
        return ToolResult("verifier", False, "",
                          refusal=f"does not parse: {verdict.parse_error}")
    return ToolResult(
        "verifier", True,
        f"{left} = {right} {'holds' if verdict.holds else 'fails'} under "
        f"scalar semantics",
        evidence={"holds": bool(verdict.holds)},
        verified=True,
        verifier="the audit is itself the check: both sides are reduced to "
                 "exact exponents and compared")


# --- dimensional term arithmetic ------------------------------------------

def _terms_applies(problem: Problem) -> bool:
    if problem.goal not in ("describe", "evaluate"):
        return False
    text = " ".join(problem.operands)
    return any(word in text for word in (" divided by ", " times ", " per ",
                                         " over ", "*", "/"))


def _terms_run(problem: Problem) -> ToolResult:
    text = " ".join(problem.operands)
    try:
        reading = tar.evaluate(text)
    except Exception as exc:                    # pragma: no cover - defensive
        return ToolResult("term_arithmetic", False, "", refusal=str(exc))
    names = list(reading.names)
    return ToolResult(
        "term_arithmetic", True,
        f"{text} has dimension {reading.describe()}"
        + (f", named by {', '.join(names[:4])}" if names else
           ", named by nothing in the register"),
        evidence={"names": names, "si7": [str(x) for x in reading.si7]})


# --- exact reals ----------------------------------------------------------

def _real_applies(problem: Problem) -> bool:
    return problem.goal == "approximate" and bool(problem.operands)


def _real_run(problem: Problem) -> ToolResult:
    text = problem.operands[0]
    places = int(problem.constraints.get("places", "20"))
    try:
        value = rx.parse_expression(text)
        decimal = value.decimal(places)
    except Exception as exc:
        return ToolResult("exact_real", False, "",
                          refusal=f"{text!r} does not parse as a real "
                                  f"expression: {exc}")
    return ToolResult("exact_real", True,
                      f"{text} = {decimal} to {places} places",
                      evidence={"places": places, "decimal": decimal})


def _real_check(problem: Problem, result: ToolResult) -> Tuple[bool, str]:
    """Independently: does a deeper reading agree to the places reported?"""
    text = problem.operands[0]
    places = int(result.evidence.get("places", 20))
    try:
        deeper = rx.parse_expression(text).decimal(places + 8)
    except Exception:                           # pragma: no cover - defensive
        return False, "the deeper reading did not parse"
    shown = str(result.evidence.get("decimal", ""))
    return deeper.startswith(shown), (
        "a reading eight places deeper agrees to every place reported"
        if deeper.startswith(shown) else
        "a deeper reading disagrees with the places reported")


# --- which layer separates two carriers -----------------------------------

def _layers_applies(problem: Problem) -> bool:
    return (problem.goal == "layers" and len(problem.operands) >= 2
            and _is_quantity(problem.operands[0])
            and _is_quantity(problem.operands[1]))


def _carrier(name: str) -> Tuple[Fraction, ...]:
    quantity = do_physics.quantity_by_name(name)
    exps = [Fraction(x) for x in quantity.exps_ext10]
    return tuple(exps + [Fraction(0)] * (24 - len(exps)))


def _layers_run(problem: Problem) -> ToolResult:
    left, right = problem.operands[0], problem.operands[1]
    a, b = _carrier(left), _carrier(right)
    separating = None
    for layer in dl.LAYERS:
        if layer.measure(layer.perceive(a), layer.perceive(b)) != 0:
            separating = layer.name
            break
    if separating is None:
        return ToolResult(
            "layers", True,
            f"no layer of the stack separates {left} from {right}: they are "
            f"the same carrier as far as every reading goes",
            evidence={"separating_layer": None})
    return ToolResult(
        "layers", True,
        f"{left} and {right} are first separated at the {separating} layer",
        evidence={"separating_layer": separating})


def _layers_check(problem: Problem, result: ToolResult) -> Tuple[bool, str]:
    """Independently: every layer below the named one must conflate them."""
    left, right = problem.operands[0], problem.operands[1]
    a, b = _carrier(left), _carrier(right)
    named = result.evidence.get("separating_layer")
    for layer in dl.LAYERS:
        same = layer.measure(layer.perceive(a), layer.perceive(b)) == 0
        if layer.name == named:
            return (not same), ("the named layer does separate them"
                                if not same else
                                "the named layer does not separate them")
        if not same:
            return False, f"the {layer.name} layer separates them first"
    return named is None, ("no layer separates them, as reported"
                           if named is None else
                           "the named layer is not in the stack")


REGISTRY: Tuple[Tool, ...] = (
    Tool("reference", ("describe", "meaning"), _reference_applies,
         _reference_run, "the meaning a term denotes", cost=1),
    Tool("runtime", ("describe", "nearest", "verify", "analogy", "report",
                     "coherence", "meaning", "approximate"),
         _runtime_applies, _runtime_run,
         "the register reading of the question", cost=1),
    Tool("verifier", ("verify",), _verifier_applies, _verifier_run,
         "whether an equation is dimensionally consistent", cost=2),
    Tool("term_arithmetic", ("describe", "evaluate"), _terms_applies,
         _terms_run, "the dimension of a written expression", cost=2),
    Tool("escalated_runtime", ("describe", "nearest", "verify", "analogy",
                               "report", "coherence", "meaning",
                               "approximate"),
         _escalated_applies, _escalated_run,
         "the register reading, escalated along the declared ladder", cost=3),
    Tool("controller", ("derive",), _controller_applies, _controller_run,
         "a derivation plan for a register quantity", cost=3,
         check=_controller_check),
    Tool("layers", ("layers",), _layers_applies, _layers_run,
         "the first layer of the stack that separates two carriers", cost=4,
         check=_layers_check),
    Tool("exact_real", ("approximate",), _real_applies, _real_run,
         "an exact real read to a stated number of places", cost=4,
         check=_real_check),
)


def applicable(problem: Problem) -> Tuple[Tool, ...]:
    """Every tool whose precondition the problem satisfies, cheapest first."""
    chosen = [tool for tool in REGISTRY if tool.applies_to(problem)]
    return tuple(sorted(chosen, key=lambda tool: (tool.cost, tool.name)))


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE PROBLEM PARSER
# ═════════════════════════════════════════════════════════════════════════

def parse_problem(text: str) -> Problem:
    """Read a string as a goal with operands.  Deterministic, and dull.

    The parser is deliberately thin: the point of the architecture is that the
    *planner* decides what to run, so the goal is a hint and not a dispatch.
    """
    raw = text.strip()
    lowered = raw.lower()
    if lowered.startswith("derive "):
        return Problem(raw, "derive", (raw[7:].strip(),), "physics")
    if lowered.startswith("layers ") or " separated from " in lowered:
        body = raw[7:] if lowered.startswith("layers ") else raw
        parts = [p.strip() for p in body.replace(" separated from ", " and ")
                 .split(" and ") if p.strip()]
        return Problem(raw, "layers", tuple(parts[:2]), "physics")
    if lowered.startswith(("approximate ", "evaluate ")):
        body = raw.split(" ", 1)[1]
        places = "20"
        if " to " in body and body.rstrip().endswith("places"):
            body, tail = body.rsplit(" to ", 1)
            digits = "".join(ch for ch in tail if ch.isdigit())
            places = digits or places
        return Problem(raw, "approximate", (body.strip(),), None,
                       {"places": places})
    if "=" in raw and lowered.startswith(("verify ", "check ", "is it true")):
        body = raw.split(" ", 1)[1] if " " in raw else raw
        left, right = body.split("=", 1)
        return Problem(raw, "verify", (left.strip(), right.strip()), "physics")
    if "::" in raw:
        return Problem(raw, "analogy", tuple(
            part.strip() for part in raw.replace("::", ":").split(":")), None)
    if lowered.startswith(("nearest", "closest")):
        return Problem(raw, "nearest", (raw.split(" to ")[-1].strip(),), None)
    if lowered.startswith("meaning of "):
        return Problem(raw, "meaning", (raw[11:].strip(),), None)
    if lowered.startswith(("describe ", "what is ")):
        body = raw.split(" ", 1)[1] if lowered.startswith("describe ") \
            else raw[8:]
        return Problem(raw, "describe", (body.strip(),), None)
    return Problem(raw, "describe", (raw,), None)


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE PLANNER
# ═════════════════════════════════════════════════════════════════════════

def plan(problem: Problem, depth: int = 0, budget: int = BUDGET) -> Plan:
    """Select tools by precondition, run them cheapest first, compose.

    The rules, in the order they bite:

    * a refusal classified **principled** stops the plan, whatever tools are
      left, because no tool repairs a question that is ill formed,
      underdetermined or grounded in no register;
    * a **verified** answer beats an unverified one, and among verified
      answers the cheapest wins;
    * the plan stops when the declared budget is spent, and says so;
    * if everything refuses, every tool tried is named with its reason.
    """
    tools = applicable(problem)
    steps: List[PlanStep] = []
    tried: List[str] = []
    refusals: List[Tuple[str, str]] = []
    sub_plans: List[Plan] = []
    spent = 0
    best: Optional[Tuple[int, bool, ToolResult]] = None
    principled: Optional[str] = None

    if not tools:
        return Plan(problem=problem, answered=False,
                    answer=(f"no tool declares a precondition this problem "
                            f"satisfies (goal {problem.goal!r})"),
                    tool=None, cost=0, verified=False, steps=(), tried=(),
                    refusal_tag="no-tool")

    for tool in tools:
        if spent + tool.cost > budget:
            steps.append(PlanStep(tool.name, 0, "skipped",
                                  f"the budget of {budget} would be exceeded "
                                  f"({spent} spent)"))
            continue
        result = tool.run(problem)
        spent += tool.cost
        tried.append(tool.name)
        if not result.answered:
            reason = result.refusal or "refused without a reason"
            refusals.append((tool.name, reason))
            verdict = esl.classify(reason)
            steps.append(PlanStep(tool.name, tool.cost, "refused",
                                  f"{verdict['tag']}: {reason[:160]}"))
            if not verdict["escalatable"]:
                principled = str(verdict["tag"])
                break
            continue
        verified, note = result.verified, result.verifier or ""
        if tool.check is not None:
            verified, note = tool.check(problem, result)
        steps.append(PlanStep(
            tool.name, tool.cost, "answered",
            f"{result.answer[:160]}"
            + (f"  [checked: {note}]" if note else "  [unchecked]")))
        candidate = (tool.cost, verified, result)
        if best is None or (verified, -tool.cost) > (best[1], -best[0]):
            best = candidate
        for sub in result.sub_goals:
            if depth + 1 <= MAX_DEPTH and spent < budget:
                child = plan(sub, depth + 1, budget - spent)
                sub_plans.append(child)
                spent += child.cost
                steps.append(PlanStep(
                    f"{tool.name} -> {child.tool or 'nothing'}", child.cost,
                    "answered" if child.answered else "refused",
                    f"sub-goal {sub.goal}: {child.answer[:120]}"))

    if best is not None:
        cost, verified, result = best
        return Plan(problem=problem, answered=True, answer=result.answer,
                    tool=result.tool, cost=spent, verified=verified,
                    steps=tuple(steps), tried=tuple(tried),
                    refusals=tuple(refusals), sub_plans=tuple(sub_plans))

    named = "; ".join(f"{name}: {reason[:80]}" for name, reason in refusals)
    return Plan(
        problem=problem, answered=False,
        answer=(f"every tool tried refused"
                + (f", and the refusal is {principled}, so the plan stopped "
                   f"rather than trying the rest" if principled else "")
                + f": {named}"),
        tool=None, cost=spent, verified=False, steps=tuple(steps),
        tried=tuple(tried), refusals=tuple(refusals),
        refusal_tag=principled or esl.ESCALATABLE, sub_plans=tuple(sub_plans))


def ask(text: str) -> Plan:
    """Parse a string as a problem and plan it."""
    return plan(parse_problem(text))


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE DECLARED TASK SET
# ═════════════════════════════════════════════════════════════════════════

#: ``(question, what it is here to show)``.  Declared, and reported in full
#: whatever each one does -- including the ones the planner is expected to
#: refuse, because a task set of things that work measures nothing.
TASKS: Tuple[Tuple[str, str], ...] = (
    ("derive energy",
     "the controller searches, and the verifier checks what it found"),
    ("derive pressure", "a second derivation, to show the first is not a one-off"),
    ("derive unobtainium", "no such quantity: no tool declares a precondition"),
    ("verify energy = force * length", "the audit, answered by the verifier"),
    ("verify energy = force * time", "a false equation: answered, and false"),
    ("describe energy", "the register reading, cheapest first"),
    ("describe energie", "a misspelling: only the escalated reading finds it"),
    ("describe unobtainium", "absent everywhere: every tool refuses, and says so"),
    ("describe justice", "open vocabulary: refused, and classified"),
    ("meaning of H2O", "the reference layer answers where the register does not"),
    ("nearest to k_B", "a constant the register does not spell"),
    ("layers energy and torque",
     "the layer stack: which reading first tells two carriers apart"),
    ("approximate sqrt(2)+1 to 20 places",
     "an exact real, checked against a deeper reading"),
    ("approximate banana to 20 places", "not a real expression: refused"),
    ("Ca : Sc :: Ba : ?", "underdetermined: the plan must stop, not shop"),
)


@memo
def task_rows() -> Tuple[Dict[str, object], ...]:
    """Every declared task, planned, and compared with the plain runtime.

    Memoised within a process: five generated blocks quote this table, and
    within one run the files it is derived from cannot move.  The uncached
    derivation stays reachable as ``task_rows.__wrapped__``, and
    :func:`promotion_checklist` calls *that* for its determinism line -- a
    determinism check answered out of a cache would check nothing.
    """
    rows: List[Dict[str, object]] = []
    for question, purpose in TASKS:
        result = ask(question)
        try:
            direct = session().ask(question)
            direct_ok, direct_answer = direct.ok, direct.answer
        except Exception as exc:
            direct_ok, direct_answer = False, f"raised: {exc}"
        rows.append({
            "task": question,
            "purpose": purpose,
            "goal": result.problem.goal,
            "answered": result.answered,
            "tool": result.tool,
            "cost": result.cost,
            "verified": result.verified,
            "tried": list(result.tried),
            "refusal_tag": result.refusal_tag,
            "answer": result.answer,
            "runtime_answered": direct_ok,
            "runtime_answer": direct_answer,
        })
    return tuple(rows)


# ═════════════════════════════════════════════════════════════════════════
# 6b.  THE FALLBACK READING -- the whole evaluation set, both ways
# ═════════════════════════════════════════════════════════════════════════

#: How the planner would be wired in if it were promoted.  Not as a
#: replacement for the runtime -- the parser here is thinner than the
#: runtime's and would lose cases -- but as a **fallback**: the runtime answers
#: whatever it answers, unchanged, and the planner is consulted only where the
#: runtime refuses.  That is the arrangement this reading measures, because it
#: is the only one whose safety gate can be stated before it is run.
FALLBACK_RULE = (
    "the runtime answers first and its answers are untouched; the planner is "
    "consulted only on a refusal, and only on a refusal the escalation "
    "classifier calls escalatable")


def fallback_row(index: int) -> Dict[str, object]:
    """One evaluation case under the fallback rule, by its position.

    Taken by index rather than by case so that it can be handed to a worker
    process: an index pickles, a case need not.  Nothing here reads anything
    but the declared case and the code, which is what makes the whole reading
    safe to compute out of order.
    """
    from ..evaluation import cases as ev

    case = ev.CASES[index]
    try:
        direct = session().ask(case.question)
        direct_ok, direct_answer = direct.ok, direct.answer
    except Exception as exc:                    # pragma: no cover - defensive
        direct_ok, direct_answer = False, f"raised: {exc}"
    tag = (None if direct_ok
           else str(esl.classify(direct_answer)["tag"]))
    consulted = (not direct_ok) and tag == esl.ESCALATABLE
    result = ask(case.question) if consulted else None
    return {
        "id": case.id,
        "kind": case.kind,
        "question": case.question,
        "runtime_answered": direct_ok,
        "runtime_answer": direct_answer,
        "refusal_tag": tag,
        "planner_consulted": consulted,
        "planner_answered": bool(result and result.answered),
        "planner_answer": result.answer if result else None,
        "planner_tool": result.tool if result else None,
        "planner_verified": bool(result and result.verified),
        "planner_cost": result.cost if result else 0,
    }


def fallback_jobs() -> int:
    """How many processes the fallback reading may use.

    Every core by default, one when ``GLM_PLANNER_JOBS=1``.  The reading is
    the expensive half of this module -- it asks the live runtime every
    declared evaluation case -- and the cases are independent, so running them
    one at a time is a choice rather than a requirement.  The answers do not
    depend on it: ``tests/test_sandbox_planner.py`` runs the reading both ways
    and requires the same rows in the same order.
    """
    import os

    raw = os.environ.get("GLM_PLANNER_JOBS")
    if raw is not None:
        try:
            return max(1, int(raw))
        except ValueError:
            return 1
    return max(1, min(8, os.cpu_count() or 1))


@memo
def fallback_rows() -> Tuple[Dict[str, object], ...]:
    """Every evaluation case, under the fallback rule.

    For each declared evaluation case: what the runtime does, and -- where the
    runtime refuses -- what the planner does with the same string.  The
    classification of the refusal is taken from the shipped escalation
    classifier, so a refusal the system holds to be correct at every layer is
    identified *before* the planner is offered the question.

    Computed across processes when there is more than one core
    (:func:`fallback_jobs`), and in this one otherwise.  The order of the rows
    is the declared order of the cases either way.
    """
    from ..evaluation import cases as ev

    indices = range(len(ev.CASES))
    jobs = fallback_jobs()
    if jobs <= 1:
        return tuple(fallback_row(index) for index in indices)
    from concurrent.futures import ProcessPoolExecutor

    #  One case per hand-out: the cases are wildly uneven -- the longest is
    #  three minutes and the median under a second -- so any chunking pairs a
    #  long case with another and lengthens the run.
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        return tuple(pool.map(fallback_row, indices, chunksize=1))


def fallback_reading(rows: Optional[Sequence[Dict[str, object]]] = None
                     ) -> Dict[str, object]:
    """The two gates the fallback has to pass, measured over the whole set.

    *Safety*: no answer the runtime gives moves, and no refusal classified as
    principled is offered to the planner at all -- let alone answered by it.
    *Utility*: the arrangement answers something the runtime does not, and
    every such answer is one an independent check agreed with.
    """
    rows = list(rows if rows is not None else fallback_rows())
    principled_consulted = [row["id"] for row in rows
                            if row["planner_consulted"]
                            and row["refusal_tag"] not in (None,
                                                           esl.ESCALATABLE)]
    gained = [row for row in rows if row["planner_answered"]]
    unchecked = [row["id"] for row in gained if not row["planner_verified"]]
    return {
        "rule": FALLBACK_RULE,
        "cases": len(rows),
        "runtime_answered": sum(1 for row in rows if row["runtime_answered"]),
        "runtime_refused": sum(1 for row in rows
                               if not row["runtime_answered"]),
        "principled_refusals": sum(1 for row in rows
                                   if not row["runtime_answered"]
                                   and row["refusal_tag"] not in
                                   (None, esl.ESCALATABLE)),
        "planner_consulted": sum(1 for row in rows
                                 if row["planner_consulted"]),
        "principled_refusals_offered_to_the_planner":
            tuple(principled_consulted),
        "gained": tuple(str(row["id"]) for row in gained),
        "gained_unchecked": tuple(unchecked),
        #  The runtime's answers are not recomputed by the planner under this
        #  rule, so nothing it says can move them: the gate is structural, and
        #  it is stated here rather than measured because measuring a thing
        #  the arrangement makes impossible would be theatre.
        "answers_moved": (),
        "safety_holds": not principled_consulted,
        "utility_holds": bool(gained) and not unchecked,
    }


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE PROMOTION CHECKLIST -- computed, not asserted
# ═════════════════════════════════════════════════════════════════════════

def promotion_checklist(rows: Optional[Sequence[Dict[str, object]]] = None,
                        fallback: Optional[Dict[str, object]] = None
                        ) -> Dict[str, object]:
    """What would have to hold for this to leave the sandbox.

    Each line is measured here rather than promised.  ``ready`` is the
    conjunction, and while it is false the module stays where it is.
    """
    rows = list(rows if rows is not None else task_rows())
    fallback = fallback if fallback is not None else fallback_reading()
    #  The repeat is deliberately the *uncached* derivation: ``task_rows`` is
    #  memoised, and comparing a memo with itself would make this line true by
    #  construction rather than by measurement.
    repeat = task_rows.__wrapped__()  # type: ignore[attr-defined]
    deterministic = all(
        first["answer"] == second["answer"] and first["cost"] == second["cost"]
        and first["tool"] == second["tool"]
        for first, second in zip(rows, repeat))
    exact = all(not isinstance(value, float)
                for row in rows for value in row.values())
    regressions = [row["task"] for row in rows
                   if row["runtime_answered"] and not row["answered"]]
    unclassified = [row["task"] for row in rows
                    if not row["answered"] and not row["refusal_tag"]]
    unverified = [row["task"] for row in rows
                  if row["answered"] and not row["verified"]]
    checks = {
        "deterministic": deterministic,
        "exact": exact,
        "no_regression_against_the_runtime": not regressions,
        "every_refusal_classified": not unclassified,
        "every_answer_independently_checked": not unverified,
        "no_principled_refusal_reaches_the_planner":
            bool(fallback["safety_holds"]),
        "answers_something_the_runtime_does_not":
            bool(fallback["utility_holds"]),
    }
    return {
        "checks": checks,
        #  The order the lines are read in, carried beside them: a mapping
        #  survives a trip through JSON but the order of its keys does not,
        #  and the checklist is read top to bottom.
        "order": tuple(checks),
        "regressions": tuple(regressions),
        "unclassified": tuple(unclassified),
        "unverified": tuple(unverified),
        "fallback": fallback,
        "ready": all(checks.values()),
        "rule": ("The planner ships when every line above is true.  While any "
                 "is false it stays in the sandbox, and the false line is the "
                 "work that remains -- not a caveat to be written around."),
    }


@memo
def planner_report() -> Dict[str, object]:
    """Everything the sandbox knows about itself, recomputed on call."""
    rows = task_rows()
    fallback = fallback_reading()
    answered = [row for row in rows if row["answered"]]
    verified = [row for row in answered if row["verified"]]
    beyond = [row for row in answered if not row["runtime_answered"]]
    return {
        "tools": tuple({"name": tool.name, "cost": tool.cost,
                        "goals": tool.goals,
                        "postcondition": tool.postcondition,
                        "has_check": tool.check is not None}
                       for tool in REGISTRY),
        "budget": BUDGET,
        "max_depth": MAX_DEPTH,
        "tasks": rows,
        "answered": len(answered),
        "verified": len(verified),
        "answered_beyond_the_runtime": tuple(str(row["task"])
                                             for row in beyond),
        "refused": len(rows) - len(answered),
        "fallback": fallback,
        "promotion": promotion_checklist(rows, fallback),
        "method": (
            "A string becomes a problem; the planner selects every tool whose "
            "declared precondition the problem satisfies, runs them cheapest "
            "first, checks each answer where an independent check exists, and "
            "stops on a refusal classified as principled.  What it returns is "
            "the cheapest verified answer, or a refusal naming every tool "
            "tried."),
        "limits": (
            "Eight tools, not sixty-seven: a tool is registered here when it "
            "has a precondition that can be checked cheaply and a "
            "postcondition that can be stated, and registering the rest is "
            "the work the promotion checklist is waiting on.  The parser is "
            "deliberately thin, so a problem it reads wrongly is planned "
            "wrongly -- which is a reason the planner is in the sandbox."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REPORT, KEPT ACROSS PROCESSES
# ═════════════════════════════════════════════════════════════════════════
#
#  Taking the report costs about a minute and a half: the declared tasks are
#  cheap, but the fallback reading asks the live runtime every one of the
#  evaluation cases.  Five generated blocks quote it, and every ``--check`` of
#  the corpus renders all five, which is why a documentation check used to
#  cost a quarter of an hour.  The memo above fixes that within one process;
#  this store fixes it across processes, on the same terms the rest of the
#  package uses -- the payload is kept beside the digest of the code it was
#  derived from, a stale payload is never answered from, and recomputing is
#  what happens instead.

#: The store itself, built on first use by :func:`_report_store`.
REPORT_STORE = None


def _report_store():
    """The store, built on first use so importing this module costs nothing."""
    global REPORT_STORE
    if REPORT_STORE is None:
        from ..signoff.ledger import code_store

        REPORT_STORE = code_store("sandbox_planner_report", __file__,
                                  schema=1)
    return REPORT_STORE


def cached_planner_report() -> Dict[str, object]:
    """:func:`planner_report`, reused while the code it reads is unchanged.

    The payload travels through JSON, so what comes back out of the store has
    lists where the fresh report has tuples.  Nothing that reads it depends on
    the difference -- ``tests/test_sandbox_planner.py`` renders every planner
    block both ways and requires the text to be identical -- and no float can
    appear either way, because the report holds only integers, strings and
    booleans.
    """
    payload = _report_store().cached(planner_report)
    return payload if isinstance(payload, dict) else planner_report()


def report_cache_state() -> Dict[str, object]:
    """Present, and derived from the code as it stands?"""
    return _report_store().state()


if __name__ == "__main__":                      # pragma: no cover
    report = planner_report()
    print(f"tools        {len(report['tools'])}, budget {report['budget']}")
    for row in report["tasks"]:                 # type: ignore[union-attr]
        state = (f"answered by {row['tool']}" if row["answered"]
                 else f"refused ({row['refusal_tag']})")
        print(f"  {row['task']:<38} {state:<34} cost {row['cost']:>2} "
              f"verified {row['verified']}")
    print(f"answered     {report['answered']} of {len(report['tasks'])}, "
          f"{report['verified']} independently checked")
    for name, value in report["promotion"]["checks"].items():  # type: ignore[index]
        print(f"  {name:<38} {value}")
    print(f"ready        {report['promotion']['ready']}")      # type: ignore[index]
