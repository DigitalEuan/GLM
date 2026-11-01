"""``glm_universal.knowledge.friction_survey`` -- the seven perturbations.

Phase 156's survey (``studies/FRICTION_STUDY.md`` §2.1): every case of the
end-to-end evaluation is run through ``GLM.py`` in a fresh interpreter and
scored by the evaluation's own harness (:func:`glm_universal.evaluation.
harness.run_case`), unperturbed (the **base**) and under each of seven
declared perturbations that applies:

=========  ========  ===========================================  ======================================
id         class     perturbation                                 applies when
=========  ========  ===========================================  ======================================
qmark      surface   append ``?``                                 the question does not end in ``?``
capital    surface   capitalise the first letter                  the first character is a lower-case letter
spaces     surface   every single space doubled                   the question has a space
please     lexical   prefix ``please``                            always
tellme     lexical   prefix ``can you tell me``                   always
typo       lexical   swap the second and third letters of the     such a word exists and the swap changes it
                     longest alphabetic word of at least five
                     letters (the first such word on a tie)
drop_the   lexical   delete the first standalone word ``the``     the question contains it
=========  ========  ===========================================  ======================================

A perturbed run of a case that passes at base is scored by the same criteria
as the case: **hold** if it passes; **stick** if the case expects an answer
and the run refuses; **slip** if the run is a wrong answer or an error (for a
case that expects a refusal, an answer).  Cases that do not pass at base are
reported and excluded from the rates.

The amended reading of §2.4 (*refusals read as refusals*, F1′ and F4′): every
run scored ``error`` is run again through ``GLM.py`` and its output kept; a
run whose output has a line beginning ``REFUSED`` and no ``ANSWER`` line is
re-scored as a refusal (a stick, or a hold for a case that expects a
refusal).  Nothing else is re-scored (:func:`rescore_refused`).

Exact throughout: every figure is an ``int`` count.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/FRICTION_STUDY.md
§§2.1, 2.4 and 7.1, studies/FRICTION_TWO_STUDY.md §§2.2 and 7.2,
studies/THERMO_FRICTION_STUDY.md §2.3 (``_typo``), the call sites in
glm_universal/tools.py and the evaluation harness (evaluation/harness.py).*
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "PERTURBATIONS", "CLASSES", "SURFACE", "LEXICAL", "perturb", "applies",
    "_typo", "drop_the", "classify", "tally", "survey", "rescore_refused",
    "refusal_reread",
]


#: The seven declared perturbations, in the study's order.
PERTURBATIONS: Tuple[str, ...] = (
    "qmark", "capital", "spaces", "please", "tellme", "typo", "drop_the",
)

#: The class of each perturbation (§2.1): F2 reads the surface ones, F3 the
#: lexical ones.
CLASSES: Dict[str, str] = {
    "qmark": "surface", "capital": "surface", "spaces": "surface",
    "please": "lexical", "tellme": "lexical", "typo": "lexical",
    "drop_the": "lexical",
}
SURFACE: Tuple[str, ...] = tuple(p for p in PERTURBATIONS
                                 if CLASSES[p] == "surface")
LEXICAL: Tuple[str, ...] = tuple(p for p in PERTURBATIONS
                                 if CLASSES[p] == "lexical")

#: An alphabetic word: a maximal run of letters.
_ALPHA_WORD = re.compile(r"[A-Za-z]+")

#: The standalone word ``the`` (not part of a longer word).
_THE = re.compile(r"(?<![A-Za-z0-9_])the(?![A-Za-z0-9_])")

#: The minimum length of the word the typo moves.
TYPO_MIN_LETTERS = 5


def _typo(text: str) -> Optional[str]:
    """The ``typo`` perturbation, or ``None`` when it does not apply.

    The longest alphabetic word (a maximal run of letters) of at least five
    letters -- the first such word on a tie -- has its second and third
    letters swapped; the perturbation applies when such a word exists and the
    swap changes it (``"describe"`` -> ``"dsecribe"``).
    """
    best = None
    for m in _ALPHA_WORD.finditer(text):
        word = m.group(0)
        if len(word) < TYPO_MIN_LETTERS:
            continue
        if best is None or len(word) > len(best.group(0)):
            best = m
    if best is None:
        return None
    word = best.group(0)
    swapped = word[0] + word[2] + word[1] + word[3:]
    if swapped == word:
        return None
    return text[:best.start()] + swapped + text[best.end():]


def drop_the(text: str) -> Optional[str]:
    """The ``drop_the`` perturbation: the first standalone ``the`` deleted
    (with one space beside it), or ``None`` when the question has none."""
    m = _THE.search(text)
    if m is None:
        return None
    start, end = m.start(), m.end()
    if end < len(text) and text[end] == " ":
        end += 1
    elif start > 0 and text[start - 1] == " ":
        start -= 1
    return text[:start] + text[end:]


def perturb(text: str, pid: str) -> Optional[str]:
    """Perturbation ``pid`` applied to ``text``; ``None`` when it does not
    apply (§2.1's last column).  Raises ``KeyError`` for an unknown id."""
    if pid == "qmark":
        return None if text.endswith("?") else text + "?"
    if pid == "capital":
        if text and text[0].isalpha() and text[0].islower():
            return text[0].upper() + text[1:]
        return None
    if pid == "spaces":
        return text.replace(" ", "  ") if " " in text else None
    if pid == "please":
        return "please " + text
    if pid == "tellme":
        return "can you tell me " + text
    if pid == "typo":
        return _typo(text)
    if pid == "drop_the":
        return drop_the(text)
    raise KeyError(f"unknown perturbation {pid!r}")


def applies(text: str, pid: str) -> bool:
    """Whether perturbation ``pid`` applies to ``text``."""
    return perturb(text, pid) is not None


# ---------------------------------------------------------------------------
#  Scoring
# ---------------------------------------------------------------------------

def classify(expect: str, outcome: str) -> str:
    """``hold`` / ``stick`` / ``slip`` for a harness outcome of a case that
    passes at base (§2.1)."""
    if outcome in ("correct", "refused_as_expected"):
        return "hold"
    if expect == "answer" and outcome == "unexpected_refusal":
        return "stick"
    return "slip"


def _empty_tally() -> Dict[str, int]:
    return {"runs": 0, "hold": 0, "stick": 0, "slip": 0}


def tally(runs: Iterable[Mapping[str, Any]], key: str = "class"
          ) -> Dict[str, Dict[str, int]]:
    """Per perturbation, the runs and their hold/stick/slip counts (every
    perturbation present, in the declared order, even when it never applied)."""
    out = {pid: _empty_tally() for pid in PERTURBATIONS}
    for run in runs:
        t = out[run["perturbation"]]
        t["runs"] += 1
        t[run[key]] += 1
    return out


# ---------------------------------------------------------------------------
#  Running the CLI
# ---------------------------------------------------------------------------

def _cli_output(question: str, timeout: int = 300) -> Tuple[int, str]:
    """``GLM.py -q question`` in a fresh interpreter, as the harness runs it;
    the exit code and the standard output."""
    from ..evaluation import harness as hr
    env = dict(os.environ)
    env["PYTHONPATH"] = str(hr.PACKAGE_ROOT)
    try:
        proc = subprocess.run(
            [sys.executable, str(hr.CLI_PATH), "-q", question,
             "--no-banner", "-c", "1"],
            cwd=str(hr.PACKAGE_ROOT), env=env, capture_output=True,
            text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return -1, ""
    return proc.returncode, proc.stdout


def refusal_reread(stdout: str) -> bool:
    """§2.4: the output has a line beginning ``REFUSED`` and no ``ANSWER``
    line."""
    lines = stdout.splitlines()
    return (any(line.startswith("REFUSED") for line in lines)
            and not any(line.startswith("ANSWER") for line in lines))


def rescore_refused(runs: Sequence[Mapping[str, Any]], timeout: int = 300,
                    jobs: int = 1, output=_cli_output) -> List[Dict[str, Any]]:
    """The runs with every ``error`` run re-run and, when its output is a
    planner ``REFUSED`` line with no ``ANSWER`` line, re-scored as a refusal
    (a stick; a hold for a case that expects a refusal).  Each run gains the
    key ``rescored`` (its class under this reading) and, for a re-run,
    ``rerun_refused``.  ``output`` is the runner (a test passes its own)."""
    out = [dict(r) for r in runs]
    errors = [i for i, r in enumerate(out) if r.get("outcome") == "error"]

    def one(i: int) -> Tuple[int, bool]:
        _code, stdout = output(out[i]["question"], timeout)
        return i, refusal_reread(stdout)

    if jobs <= 1:
        reread = [one(i) for i in errors]
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            reread = list(pool.map(one, errors))
    flags = dict(reread)
    for i, r in enumerate(out):
        r["rescored"] = r["class"]
        if i in flags:
            r["rerun_refused"] = flags[i]
            if flags[i]:
                r["rescored"] = "hold" if r["expect"] == "refusal" else "stick"
    return out


# ---------------------------------------------------------------------------
#  The survey
# ---------------------------------------------------------------------------

def survey(cases: Optional[Sequence[Any]] = None, jobs: int = 8,
           timeout: int = 300, run_case=None, rescore: bool = True,
           output=_cli_output) -> Dict[str, Any]:
    """Run the base and the seven perturbations over ``cases`` (default: the
    evaluation's :data:`~glm_universal.evaluation.cases.CASES`).

    About 1,300 runs of ``GLM.py`` for the whole set (§7: ~25 minutes on eight
    jobs); ``run_case`` and ``output`` replace the harness's runner and the
    re-run's (a test passes stand-ins).  Returns the cases, how many pass at
    base (and which fail), the per-perturbation tally as declared
    (``by_perturbation``), the tally with refusals read as refusals
    (``rescored``), the F-mark denominators and every run.
    """
    from ..evaluation import cases as ev
    from ..evaluation import harness as hr
    cases = tuple(ev.CASES if cases is None else cases)
    runner = run_case or hr.run_case

    def run(item):
        case, question = item
        return runner(_moved(case, question), timeout)

    base = _map(run, [(c, c.question) for c in cases], jobs)
    passing = [c for c, r in zip(cases, base) if r.passed]
    failing = [c.id for c, r in zip(cases, base) if not r.passed]
    plan: List[Tuple[Any, str, str]] = []
    for case in passing:
        for pid in PERTURBATIONS:
            moved = perturb(case.question, pid)
            if moved is not None:
                plan.append((case, pid, moved))
    results = _map(run, [(c, q) for c, _p, q in plan], jobs)
    runs: List[Dict[str, Any]] = []
    for (case, pid, moved), res in zip(plan, results):
        runs.append({
            "id": case.id, "kind": case.kind, "expect": case.expect,
            "perturbation": pid, "question": moved,
            "outcome": res.outcome, "answer": res.answer,
            "class": classify(case.expect, res.outcome),
        })
    if rescore:
        runs = rescore_refused(runs, timeout=timeout, jobs=jobs, output=output)
    else:
        for r in runs:
            r["rescored"] = r["class"]
    refusal_runs = sum(1 for r in runs if r["expect"] == "refusal")
    return {
        "cases": len(cases),
        "base_passing": len(passing),
        "base_failing": failing,
        "by_perturbation": tally(runs, "class"),
        "rescored": tally(runs, "rescored"),
        "refusal_runs": refusal_runs,
        "refusal_slips": sum(1 for r in runs if r["expect"] == "refusal"
                             and r["class"] == "slip"),
        "refusal_slips_rescored": sum(1 for r in runs
                                      if r["expect"] == "refusal"
                                      and r["rescored"] == "slip"),
        "errors": sum(1 for r in runs if r["outcome"] == "error"),
        "runs": runs,
    }


def _moved(case: Any, question: str) -> Any:
    """The case with its question replaced (the harness reads ``question``)."""
    if question == case.question:
        return case
    from dataclasses import is_dataclass, replace
    if is_dataclass(case):
        return replace(case, question=question)
    if hasattr(case, "_replace"):                 # a named tuple
        return case._replace(question=question)
    import copy
    moved = copy.copy(case)
    moved.question = question
    return moved


def _map(fn, items: Sequence[Any], jobs: int) -> List[Any]:
    if jobs <= 1:
        return [fn(x) for x in items]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(fn, items))
