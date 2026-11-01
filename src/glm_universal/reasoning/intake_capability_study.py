"""``glm_universal.reasoning.intake_capability_study`` -- the marks of
``studies/INTAKE_CAPABILITY_STUDY.md`` (Phase 186): what the intake items
absorbed on 1 November 2026 add to the GLM on ARC, on Rule 30 and on general
reasoning across domains, measured with and without them.

*Created 1 November 2026 (Phase 186: the intake items absorbed where they
measurably help, directive D22).*

What is measured
----------------
Each part puts the same questions to the GLM **with** the Phase 186 additions
and **without** them, and counts exact integers.

* **ARC** -- the fifty stored ARC tasks (``arc_agi_17``) through ``tool arc``:
  the colour solver alone (the GLM before Phase 186), and the colour solver
  with the hypothesis engine's plan search on the test inputs it refuses
  (:func:`glm_universal.reasoning.hypothesis_tools.arc_combined_text`); every
  answer graded against the stored output, which neither solver sees.  The
  engine's own synthetic families are run as well, for information.  *These
  fifty tasks are a development set, not a held-out one*: the engine's plan
  search was written by the intake item's author against them, so the ARC
  figures say what the GLM now answers on them, not how it would do on unseen
  tasks.
* **Rule 30** -- the engine's 39-claim Rule 30 domain with its Lean ledger and
  without it; the same 39 sentences put to ``tool rule30 claim`` and, worded
  *"in rule 30, ..."*, to the GLM's answering path (``GLM.routed_result``, the
  reading of ``python3 src/GLM.py -q``) with and without Phase 186; the centre
  column checked against a plain simulation written here and against the list
  ``IntakeChecks/RuleThirtyBits.lean`` states.
* **General reasoning** -- the engine's general domain (ten classic traps)
  with and without its ledger; twelve conjectures about every ``n``
  (:data:`CONJECTURES`) through ``tool conjecture``, each false one checked
  here against its least counterexample, found here by brute force.
* **Formula laws** -- the 115 questions of ``studies/CENT_WHEELS_STUDY.md``
  §4 through ``tool derive``, against the fifteen registry wheels alone.
* **Next terms** -- the pre-registered battery of
  :mod:`glm_universal.wheels.next_term_battery` (45 questions, 13 controls).
* **Across domains** -- thirty English questions (:data:`CROSS_DOMAIN`), six
  in each of five domains, through the answering path with and without
  Phase 186.
* **Lean** -- the four standalone files ``IntakeChecks/*.lean``: present,
  their theorems stated, no ``sorry``, each imported by ``AxiomAuditAll.lean``.
  (They were built with a newer Lean and Mathlib outside the project's build;
  the owner's ``scripts/rebuild_lean.sh`` has still to confirm them.)

*Without Phase 186* is the GLM with the three tools of Phase 186
(``rule30``, ``conjecture``, ``derive``) and their English routes taken out of
the toolbox, ``tool arc`` on the colour solver alone, and the ``sequence``
kind without its ``next`` reading (:func:`without_phase186`): everything else
is the same code.

The marks (fixed on 1 November 2026, after the tools were built and spot-
checked on some of these questions, before this module's first run)
---------------------------------------------------------------------------
* **A1** ARC with the plan search: 0 wrong test grids on the fifty tasks.
* **A2** ARC with the plan search: at least 7 tasks right (the colour solver
  alone: 2; the development figure of the plan search, 9, was known).
* **A3** ARC: the plan search changes no answer the colour solver gives, and
  ``tool arc`` reports for every task the status computed here.
* **R1** Rule 30 battery: with the ledger 39 right, 0 wrong, 0 overclaimed;
  without the ledger 0 wrong and 0 overclaimed (it abstains instead).
* **R2** Rule 30 on the answering path: the 39 sentences worded *"in rule 30,
  ..."*: without Phase 186 none answered; with it 0 wrong and at least 20
  answered right.
* **R3** the centre column: ``tool rule30 centre 1000`` equals the plain
  simulation, and its first 64 cells the list of ``RuleThirtyBits.lean``.
* **G1** general domain: with the ledger 10 right and 0 wrong; without it
  0 wrong and 0 overclaimed.
* **G2** conjectures: 0 wrong of the twelve; every false one refuted with a
  counterexample that is one; no surviving one called proved.
* **D1** ``tool derive``: at least 56 of the 64 laws licensed and 0 of the 51
  not-a-laws (the bars of ``CENT_WHEELS_STUDY.md``), the fifteen registry
  wheels alone licensing at most 4 laws.
* **S1** next terms: 0 wrong on the 45 positives, and more right than without
  the ``next`` reading.
* **S2** next terms: every one of the 13 negative controls refused.
* **X1** across domains: 0 wrong of the thirty with Phase 186.
* **X2** across domains: at least 15 more right with Phase 186 than without.
* **L1** the four standalone Lean files: present, every theorem named here
  stated, no ``sorry``, each imported by ``AxiomAuditAll.lean``.

After the first run (1 November 2026)
-------------------------------------
No mark was changed.  Two things were corrected after the first run, and are
recorded here: the reading of a verdict (:data:`_VERDICT`) expected the claim
in single quotes, so two Rule 30 sentences containing an apostrophe (quoted
in double quotes in the reply) were read as giving no verdict; corrected, the
answering-path count of R2 went from 14 right to 16 right (the mark stays
missed: the bar is 20).  And the Lean mark, written ``L`` at first, was
renamed **L1** so the study ledger reads it as a mark; its test is unchanged.

Exactness
---------
Integers, fractions, tuples and strings only (directive D7).
"""
from __future__ import annotations

import json
import re
from contextlib import contextmanager
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Tuple

from .. import integrity
from . import colour_induction as ci
from . import hypothesis_engine as E
from . import hypothesis_tools as ht

__all__ = [
    "DATA_PATH", "PHASE186_TOOLS", "CONJECTURES", "CROSS_DOMAIN", "LEAN_CHECKS",
    "without_phase186", "arc", "rule30", "general", "derive", "next_terms", "cross_domain",
    "lean", "compute", "measure", "write_measurements", "measurements", "state", "current",
    "intake_capability_report", "plain_centre",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "intake_capability_study.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/intake_capability_study.py",
    "reasoning/hypothesis_engine.py",
    "reasoning/hypothesis_tools.py",
    "reasoning/colour_induction.py",
    "wheels/derive_query.py",
    "wheels/sequence_query.py",
    "wheels/next_term_battery.py",
    "wheels/cent_wheels.py",
    "wheels/cent_wheels_study.py",
    "runtime/toolbox.py",
    "runtime/router.py",
)

#: The toolbox tools Phase 186 added (taken out by :func:`without_phase186`).
PHASE186_TOOLS: Tuple[str, ...] = ("rule30", "conjecture", "derive")


# ── the switch: the GLM without Phase 186 ──────────────────────────────────

@contextmanager
def without_phase186() -> Iterator[None]:
    """The GLM as it answered before Phase 186: the tools ``rule30``,
    ``conjecture`` and ``derive`` and their English routes out of the toolbox,
    ``tool arc`` on the colour solver alone (the hypothesis engine reported
    not installed), and the ``sequence`` kind without its ``next`` reading.
    Everything is restored on leaving, whatever happens inside."""
    from ..runtime import toolbox as tb
    from ..wheels import sequence_query as sq
    saved = (tb.TOOLS, tb.TOOL_PHRASES, tb._hypothesis_tools, sq.resolve_query)
    original = sq.resolve_query

    def resolve_before(text, wheel=None, next_terms=True, offset_junctions=True):
        return original(text, wheel=wheel, next_terms=False, offset_junctions=offset_junctions)

    try:
        tb.TOOLS = tuple(t for t in tb.TOOLS if t.name not in PHASE186_TOOLS)
        tb.TOOL_PHRASES = tuple((p, t) for p, t in tb.TOOL_PHRASES
                                if t.split()[1] not in PHASE186_TOOLS)
        tb._hypothesis_tools = lambda: None
        sq.resolve_query = resolve_before
        yield
    finally:
        tb.TOOLS, tb.TOOL_PHRASES, tb._hypothesis_tools, sq.resolve_query = saved


_SESSION = None


def _routed(question: str) -> Tuple[str, str]:
    """One question read as ``-q`` reads it: ``(status, answer text)``."""
    global _SESSION
    import GLM
    from ..runtime.session import GeometricSession
    if _SESSION is None:
        _SESSION = GeometricSession()
    r = GLM.routed_result(_SESSION, question)
    return str(r.status), str(r.answer or "")


# ── ARC ────────────────────────────────────────────────────────────────────

def _grade(answer, want) -> str:
    if answer is None:
        return "refused"
    if want is None:
        return "unchecked"
    return "right" if answer == E.G(want) else "wrong"


def _task_status(grades: List[str]) -> str:
    if "wrong" in grades:
        return "wrong"
    return "right" if grades and all(g == "right" for g in grades) else "refused"


def arc() -> Dict[str, object]:
    """The fifty stored tasks: the colour solver alone, the plan search on
    every test input (for information), and the two together as ``tool arc``
    now answers; per test grid and per task."""
    from ..runtime.toolbox import run_tool
    from .colour_induction_study import _vision_solved
    names = ci.arc_names()
    tasks = {n: ci.arc_task(n) for n in names}
    rows = []
    for name in names:
        task = tasks[name]
        colour = [t["grade"] for t in ci.arc_solve(task)["tests"]]
        plan, combined = [], []
        for i, test in enumerate(task["test"]):
            ans, _progs, _note = ht.arc_plan(task["train"], test["input"])
            plan.append(_grade(ans, test.get("output")))
            combined.append(colour[i] if colour[i] != "refused" else plan[i])
        tool = run_tool(f"tool arc {name}")
        rows.append({"task": name, "colour": colour, "plan": plan, "combined": combined,
                     "tool_status": tool.figures.get("status")})

    def tally(key: str) -> Dict[str, object]:
        grids = [g for r in rows for g in r[key]]
        status = {r["task"]: _task_status(r[key]) for r in rows}
        return {"grids": len(grids),
                **{g: sum(1 for x in grids if x == g) for g in ("right", "wrong", "refused")},
                "tasks_right": sorted(t for t, s in status.items() if s == "right"),
                "tasks_wrong": sorted(t for t, s in status.items() if s == "wrong")}

    unchanged = all(r["combined"][i] == r["colour"][i] for r in rows
                    for i in range(len(r["colour"])) if r["colour"][i] != "refused")
    tool_agrees = [r["task"] for r in rows if r["tool_status"] == _task_status(r["combined"])]
    return {"tasks": len(names), "colour": tally("colour"), "plan": tally("plan"),
            "combined": tally("combined"), "colour_answers_unchanged": unchanged,
            "tool_agrees": len(tool_agrees),
            "tool_disagrees": sorted(set(names) - set(tool_agrees)),
            "vision_stack_solved": _vision_solved(tasks) if names else [],
            "development_set": True, "synthetic": _synthetic()}


def _synthetic() -> Dict[str, object]:
    """The engine's own synthetic ARC families (seed 18; for information)."""
    puzzles = E.make_synthetic(18, 5)
    res = E.run_arc(puzzles, random_draws=2)
    keep = ("n", "base", "on_demand", "all_provisions", "random_same_size")
    return {k: res[k] for k in keep if k in res}


# ── Rule 30 ────────────────────────────────────────────────────────────────

def plain_centre(n: int) -> List[int]:
    """The first ``n`` centre cells of Rule 30 from one black cell, by a plain
    simulation on a list of cells (``new[i] = old[i-1] XOR (old[i] OR
    old[i+1])``), independent of the engine."""
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


def _lean_centre() -> List[int]:
    from ..constants import lean_file
    path = lean_file("RequestProject/GLM/IntakeChecks/RuleThirtyBits.lean")
    if not path.is_file():
        return []
    m = re.search(r"theorem centreBits_64\s*:\s*centreBits\s+64\s*=\s*\[([a-z,\s]+)\]",
                  path.read_text(encoding="utf-8"))
    return [1 if x == "true" else 0 for x in re.findall(r"true|false", m.group(1))] if m else []


_VERDICT = re.compile(r"['\"]: (true|false|not settled) -- ")


def _verdict_of(text: str) -> Optional[str]:
    m = _VERDICT.search(text)
    return m.group(1) if m else None


def _truth_grade(truth, verdict: Optional[str]) -> str:
    """``right`` / ``wrong`` / ``overclaim`` / ``abstain`` / ``refused``, as
    the engine scores (truth ``None``: the claim is open)."""
    if verdict is None:
        return "refused"
    said = {"true": True, "false": False, "not settled": None}[verdict]
    if said == truth:
        return "right"
    if said is None:
        return "abstain"
    if truth is None:
        return "overclaim"
    return "wrong"


def _count(grades: List[str], kinds=("right", "wrong", "overclaim", "abstain", "refused")
           ) -> Dict[str, int]:
    return {k: sum(1 for g in grades if g == k) for k in kinds}


def rule30() -> Dict[str, object]:
    data = ht._data()
    _, with_l = E.run_rule30(data, True)
    _, without_l = E.run_rule30(data, False)
    dom = E.Rule30Domain(data)
    sentences = [h["text"] for h in with_l["hypotheses"]]
    tool_rows, truths = [], []
    for s in sentences:
        h = E.import_statement(dom, s)
        truth = dom.truth(h) if E.recognise(s) is not None else "unset"
        truths.append(truth)
        _ok, text, _fig = ht.rule30_text("claim " + s)
        tool_rows.append(_truth_grade(truth, _verdict_of(text)) if truth != "unset"
                         else "unscored")
    questions = [f"in rule 30, {s}" for s in sentences]
    with without_phase186():
        before = [_routed(q) for q in questions]
    after = [_routed(q) for q in questions]

    def routed_grades(rows):
        out = []
        for (status, text), truth in zip(rows, truths):
            if status != "answered":
                out.append("refused")
            elif truth == "unset":
                out.append("unscored")
            else:
                out.append(_truth_grade(truth, _verdict_of(text)))
        return out

    centre = ht.rule30_text("centre 1000")[2]
    plain = plain_centre(1000)
    lean = _lean_centre()
    return {
        "claims": len(sentences),
        "battery_with_ledger": dict(with_l["score"]),
        "battery_without_ledger": dict(without_l["score"]),
        "recognised": sum(1 for t in truths if t != "unset"),
        "tool": _count(tool_rows, ("right", "wrong", "overclaim", "abstain", "refused",
                                   "unscored")),
        "routed_without": _count(routed_grades(before), ("right", "wrong", "overclaim",
                                                         "abstain", "refused", "unscored")),
        "routed_with": _count(routed_grades(after), ("right", "wrong", "overclaim", "abstain",
                                                     "refused", "unscored")),
        "answered_without": sum(1 for s, _ in before if s == "answered"),
        "answered_with": sum(1 for s, _ in after if s == "answered"),
        "centre_1000_black": centre.get("black"),
        "centre_1000_matches_plain": centre.get("black") == sum(plain)
        and centre.get("prefix") == "".join(map(str, plain[:64])),
        "centre_64_matches_lean": bool(lean) and centre.get("prefix") == "".join(map(str, lean)),
    }


# ── general reasoning ──────────────────────────────────────────────────────

def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _is_prime_big(n: int) -> bool:
    """Trial division where it is cheap; the Fermat number 2^32 + 1 is
    settled by its known factor 641 (Euler), found by the same division."""
    return _is_prime(n) if n < 10 ** 12 else not any(n % p == 0 for p in range(2, 10 ** 4))


#: Twelve claims about every ``n``: ``(id, sentence, truth, check)`` -- the
#: truth fixed by a theorem or by the least counterexample (found here), and
#: the check a plain Python predicate written here, independent of the
#: evaluator ``tool conjecture`` uses.
CONJECTURES: Tuple[Tuple[str, str, bool, Callable[[int], bool], int], ...] = (
    ("C01", "n^2 + n + 41 is prime for every n", False,
     lambda n: _is_prime(n * n + n + 41), 0),
    ("C02", "n^2 - n + 41 is prime for every n", False,
     lambda n: _is_prime(n * n - n + 41), 0),
    ("C03", "2^n - 1 is prime for every n >= 2", False, lambda n: _is_prime(2 ** n - 1), 2),
    ("C04", "n^2 + 1 is prime for every n >= 1", False, lambda n: _is_prime(n * n + 1), 1),
    ("C05", "2^(2^n) + 1 is prime for every n", False,
     lambda n: _is_prime_big(2 ** (2 ** n) + 1), 0),
    ("C06", "6 divides n^3 - n for every n", True, lambda n: (n ** 3 - n) % 6 == 0, 0),
    ("C07", "2^n > n for every n", True, lambda n: 2 ** n > n, 0),
    ("C08", "n^2 % 4 in (0, 1) for every n", True, lambda n: n * n % 4 in (0, 1), 0),
    ("C09", "isprime(n) or n % 2 == 0 or n % 3 == 0 or n < 25 for every n", False,
     lambda n: _is_prime(n) or n % 2 == 0 or n % 3 == 0 or n < 25, 0),
    ("C10", "30 divides n^5 - n for every n", True, lambda n: (n ** 5 - n) % 30 == 0, 0),
    ("C11", "n*(n+1)*(n+2) % 6 == 0 for every n", True,
     lambda n: n * (n + 1) * (n + 2) % 6 == 0, 0),
    ("C12", "isprime(6*n + 1) or isprime(6*n + 5) for every n >= 1", False,
     lambda n: _is_prime(6 * n + 1) or _is_prime(6 * n + 5), 1),
)


def _least_counterexample(check: Callable[[int], bool], start: int, upto: int = 64
                          ) -> Optional[int]:
    for n in range(start, start + upto):
        if not check(n):
            return n
    return None


def general() -> Dict[str, object]:
    _, w = E.run_general(True)
    _, wo = E.run_general(False)
    rows = []
    for cid, sentence, truth, check, start in CONJECTURES:
        least = _least_counterexample(check, start)
        _ok, text, fig = ht.conjecture_text(sentence)
        answer = fig.get("answer")
        ring = fig.get("ring")
        m = re.search(r"n = (\d+)", str(fig.get("reason") or ""))
        stated = int(m.group(1)) if m else None
        if fig.get("status") == "refused" or ring is None:
            grade = "refused"
        elif truth is False:
            grade = ("right" if answer is False and stated is not None and not check(stated)
                     else "wrong" if answer is True else "abstain" if answer is None
                     else "wrong")
        else:
            grade = ("right" if answer is None and ring == "thinks true"
                     else "wrong" if answer is False else "overclaim")
        rows.append({"id": cid, "truth": truth, "least_counterexample": least,
                     "answer": answer, "ring": ring, "stated_counterexample": stated,
                     "grade": grade})
    return {"with_ledger": dict(w["score"]), "without_ledger": dict(wo["score"]),
            "conjectures": rows,
            "conjecture_tally": _count([r["grade"] for r in rows]),
            "false_claims": sum(1 for r in rows if r["truth"] is False),
            "false_with_counterexample": [r["id"] for r in rows if r["truth"] is False
                                          and r["least_counterexample"] is not None]}


# ── formula laws ───────────────────────────────────────────────────────────

def derive() -> Dict[str, object]:
    from ..wheels.cent_wheels_study import LAW, battery_rows
    from ..wheels.derive_query import derive_text
    rows = battery_rows()
    laws = [r for r in rows if r["gold"] == LAW]
    nots = [r for r in rows if r["gold"] != LAW]

    def licensed(r) -> bool:
        ok, _text, fig = derive_text(r["equation"])
        return bool(ok) and fig.get("verdict") == "derivable"

    tool = {r["qid"]: licensed(r) for r in rows}
    return {"questions": len(rows), "laws": len(laws), "not_laws": len(nots),
            "tool_laws_licensed": sum(tool[r["qid"]] for r in laws),
            "tool_not_laws_licensed": sum(tool[r["qid"]] for r in nots),
            "fifteen_wheels_laws_licensed": sum(r["baseline"] is not None for r in laws),
            "fifteen_wheels_not_laws_licensed": sum(r["baseline"] is not None for r in nots),
            "tool_agrees_with_study": all(tool[r["qid"]] == (r["with_cent"] is not None)
                                          for r in rows)}


# ── next terms ─────────────────────────────────────────────────────────────

def next_terms() -> Dict[str, object]:
    from ..wheels.next_term_battery import measure_next_terms
    m = measure_next_terms()
    return {k: m[k] for k in ("questions", "controls", "with_wheels", "with_wheels_first_rule",
                              "without_next")}


# ── across domains ─────────────────────────────────────────────────────────

def _catalan(k: int) -> int:
    from math import comb
    return comb(2 * k, k) // (k + 1)


def _nth_prime(k: int) -> int:
    n, found = 1, 0
    while found < k:
        n += 1
        if _is_prime(n):
            found += 1
    return n


def _bits(n: int) -> str:
    return "".join(map(str, plain_centre(n)))


#: Thirty questions in five domains: ``(id, domain, question, kind,
#: expected)``.  The expected outcome is computed here (the centre column by
#: the plain simulation, the next terms by closed forms, the conjectures'
#: truth by :data:`CONJECTURES`' reasoning); an ARC question is graded against
#: the stored output by ``tool arc`` itself, and its six tasks are the first six
#: stored tasks in name order (chosen by that rule, not by outcome).
def cross_domain_questions() -> Tuple[Tuple[str, str, str, str, object], ...]:
    arc_names = ci.arc_names()[:6]
    q = [
        ("X01", "rule30", "what are the first 20 cells of rule 30's centre column",
         "bits", _bits(20)),
        ("X02", "rule30", "show the rule 30 centre column up to 64 cells", "bits", _bits(64)),
        ("X03", "rule30", "in rule 30, the least period of right diagonal D divides 2^D",
         "truth", True),
        ("X04", "rule30", "in rule 30, every left diagonal has eventual period dividing 8",
         "truth", False),
        ("X05", "rule30", "in rule 30, the centre column is not eventually periodic with "
                          "period p ≤ 100 and preperiod ≤ 1000", "truth", True),
        ("X06", "rule30", "in rule 30, the periods of the left diagonals are unbounded",
         "open", None),
        ("X07", "number", "is n^2 + n + 41 prime for every n", "truth", False),
        ("X08", "number", "is it true that 2^n > n for every n", "survives", None),
        ("X09", "number", "is 2^n - 1 prime for every n >= 2", "truth", False),
        ("X10", "number", "check the conjecture that 6 divides n^3 - n for every n",
         "survives", None),
        ("X11", "number", "is n^2 + 1 prime for every n >= 1", "truth", False),
        ("X12", "number", "is it true that n^2 - n + 41 is prime for every n", "truth", False),
        ("X13", "physics", "is force = mass * acceleration a law", "derive", "derivable"),
        ("X14", "physics", "is energy = mass * speed_of_light a law", "derive",
         "not derivable"),
        ("X15", "physics", "does power = force * velocity follow from the wheels", "derive",
         "derivable"),
        ("X16", "physics", "is emf = magnetic_field * area / time a law", "derive",
         "derivable"),
        ("X17", "physics", "is power = force * time a law", "derive", "not derivable"),
        ("X18", "physics", "is voltage = current * resistance a law", "derive", "derivable"),
        ("X19", "sequence", "what comes next in 1, 1, 2, 5, 14, 42", "next", _catalan(6)),
        ("X20", "sequence", "what comes next in 1, 2, 6, 24, 120", "next", 720),
        ("X21", "sequence", "what comes next in 2, 3, 5, 7, 11, 13", "next", _nth_prime(7)),
        ("X22", "sequence", "what comes next in 1, 3, 6, 10, 15", "next", 6 * 7 // 2),
        ("X23", "sequence", "what comes next in 9, 9, 9, 1", "refuse", None),
        ("X24", "sequence", "what comes next in 1, 2", "refuse", None),
    ]
    for i, name in enumerate(arc_names):
        q.append((f"X{25 + i}", "arc", f"solve the arc task {name}", "arc", name))
    return tuple(q)


CROSS_DOMAIN = cross_domain_questions


_NEXT = re.compile(r"^(-?\d+) — the next term")
_DERIVE = re.compile(r"\bderive: (derivable|not derivable)\b")
_ARC = re.compile(r"\barc [0-9a-f]{8}: (RIGHT|WRONG|refused)\b")


def grade_answer(kind: str, expected, status: str, text: str) -> str:
    """``right`` / ``wrong`` / ``refused`` for one answer of the cross-domain
    set (an answer that does not state the thing asked is ``unread``)."""
    if status != "answered":
        return "right" if kind in ("refuse", "open") else "refused"
    if kind == "bits":
        m = re.search(r"from one black cell: ([01]+)", text)
        if not m:
            return "unread"
        return "right" if m.group(1) == str(expected)[:len(m.group(1))] and \
            len(m.group(1)) == min(len(str(expected)), 64) else "wrong"
    if kind in ("truth", "open", "survives"):
        v = _verdict_of(text)
        if v is None:
            return "unread"
        if kind == "truth":
            return "right" if (v == "true") == expected and v != "not settled" else \
                "refused" if v == "not settled" else "wrong"
        return "right" if v == "not settled" else "wrong"
    if kind == "derive":
        m = _DERIVE.search(text)
        if not m:
            return "unread"
        return "right" if m.group(1) == expected else "wrong"
    if kind == "next":
        m = _NEXT.match(text.strip())
        if not m:
            return "unread"
        return "right" if int(m.group(1)) == expected else "wrong"
    if kind == "refuse":
        return "wrong" if _NEXT.match(text.strip()) else "right"
    if kind == "arc":
        m = _ARC.search(text)
        if not m:
            return "unread"
        return {"RIGHT": "right", "WRONG": "wrong", "refused": "refused"}[m.group(1)]
    return "unread"


def cross_domain() -> Dict[str, object]:
    questions = cross_domain_questions()
    with without_phase186():
        before = [_routed(q[2]) for q in questions]
    after = [_routed(q[2]) for q in questions]
    rows = []
    for (qid, domain, question, kind, expected), b, a in zip(questions, before, after):
        rows.append({"id": qid, "domain": domain, "question": question,
                     "without": grade_answer(kind, expected, *b),
                     "with": grade_answer(kind, expected, *a)})
    kinds = ("right", "wrong", "refused", "unread")
    by_domain = {}
    for d in ("rule30", "number", "physics", "sequence", "arc"):
        mine = [r for r in rows if r["domain"] == d]
        by_domain[d] = {"without": _count([r["without"] for r in mine], kinds),
                        "with": _count([r["with"] for r in mine], kinds)}
    return {"questions": len(rows), "rows": rows, "by_domain": by_domain,
            "without": _count([r["without"] for r in rows], kinds),
            "with": _count([r["with"] for r in rows], kinds)}


# ── Lean ───────────────────────────────────────────────────────────────────

#: The four standalone files and the theorems each must state.
LEAN_CHECKS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("IntakeChecks/RuleThirtyBits", ("rule30_wolfram", "testBit_step_zero",
                                     "testBit_step_succ", "centreBits_64",
                                     "centreBits_64_ones")),
    ("IntakeChecks/SporadicOrderCheck", ("orders_length", "orders_nodup", "names_nodup",
                                         "order_M")),
    ("IntakeChecks/NextTerm", ("nextTerm_sound", "nextTerm_witness",
                               "nextTerm_none_of_split", "catalan_terms", "fib_terms")),
    ("IntakeChecks/Derivability", ("derivable_of_combination",
                                   "not_derivable_of_functional", "force_example",
                                   "energy_not_from_speed")),
)


def lean() -> Dict[str, object]:
    from ..constants import lean_file
    audit = lean_file("RequestProject/GLM/AxiomAuditAll.lean")
    audit_text = audit.read_text(encoding="utf-8") if audit.is_file() else ""
    rows = []
    for name, theorems in LEAN_CHECKS:
        path = lean_file(f"RequestProject/GLM/{name}.lean")
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        rows.append({"file": name, "present": path.is_file(),
                     "stated": sum(1 for t in theorems
                                   if re.search(rf"theorem {re.escape(t)}\b", text)),
                     "declared": len(theorems), "sorry": len(re.findall(r"\bsorry\b", text)),
                     "audited": f"import RequestProject.GLM.{name.replace('/', '.')}"
                                in audit_text})
    return {"files": rows, "standalone": "built with Lean 4.34 and Mathlib outside the "
                                         "project's build; the owner's scripts/rebuild_lean.sh "
                                         "has still to confirm them"}


# ── the report ─────────────────────────────────────────────────────────────

def compute() -> Dict[str, object]:
    report = {"arc": arc(), "rule30": rule30(), "general": general(), "derive": derive(),
              "next_terms": next_terms(), "cross_domain": cross_domain(), "lean": lean()}
    marks = _marks(report)
    report["marks"] = marks
    report["met"] = sum(marks.values())
    report["taken"] = len(marks)
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    a, r30, g, d, s, x, L = (r["arc"], r["rule30"], r["general"], r["derive"],
                             r["next_terms"], r["cross_domain"], r["lean"])
    wl, wol = r30["battery_with_ledger"], r30["battery_without_ledger"]
    gw, gwo = g["with_ledger"], g["without_ledger"]
    with_next, without_next = s["with_wheels"], s["without_next"]
    conj = g["conjectures"]
    return {
        "A1": a["tasks"] > 0 and a["combined"]["wrong"] == 0,
        "A2": len(a["combined"]["tasks_right"]) >= 7,
        "A3": a["colour_answers_unchanged"] and a["tool_agrees"] == a["tasks"],
        "R1": (wl["n"] == 39 and wl["right"] == 39 and wl["wrong"] == 0
               and wl["overclaim"] == 0 and wol["wrong"] == 0 and wol["overclaim"] == 0),
        "R2": (r30["answered_without"] == 0 and r30["routed_with"]["wrong"] == 0
               and r30["routed_with"]["overclaim"] == 0 and r30["routed_with"]["right"] >= 20),
        "R3": r30["centre_1000_matches_plain"] and r30["centre_64_matches_lean"],
        "G1": (gw["right"] == 10 and gw["wrong"] == 0 and gwo["wrong"] == 0
               and gwo["overclaim"] == 0),
        "G2": (len(conj) == 12 and all(c["grade"] != "wrong" and c["grade"] != "overclaim"
                                       for c in conj)
               and all(c["grade"] == "right" for c in conj if c["truth"] is False)
               and not any(c["answer"] is True for c in conj)),
        "D1": (d["tool_laws_licensed"] >= 56 and d["tool_not_laws_licensed"] == 0
               and d["fifteen_wheels_laws_licensed"] <= 4),
        "S1": (with_next["positive"]["wrong"] == 0
               and with_next["positive"]["right"] > without_next["positive"]["right"]),
        "S2": with_next["controls"]["wrong"] == 0,
        "X1": x["with"]["wrong"] == 0,
        "X2": x["with"]["right"] - x["without"]["right"] >= 15,
        "L1": all(f["present"] and f["stated"] == f["declared"] and f["sorry"] == 0
                 and f["audited"] for f in L["files"]),
    }


def _plain(x):
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))], root)


def measure() -> Dict[str, object]:
    report = compute()
    report["source_digest"] = module_digest()
    return report


_cache: Optional[Dict[str, object]] = None


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_plain(measure()), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    global _cache
    _cache = None
    return target


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    fresh = stored.get("source_digest") == live
    return {"present": True, "fresh": fresh, "verdict": "current" if fresh else "stale",
            "live_digest": live, "stored_digest": stored.get("source_digest")}


def current() -> Optional[Dict[str, object]]:
    return measurements() if state()["fresh"] else None


def intake_capability_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it with "
            f"python3 -m glm_universal.tools intake-capability --write")}
    return dict(stored, available=True)
