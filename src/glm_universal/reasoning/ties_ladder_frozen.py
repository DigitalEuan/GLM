"""``glm_universal.reasoning.ties_ladder_frozen`` -- the evaluation's frozen
path of Phases 150 and 151.

Both rounds move answers the evaluation pins
(``studies/NEAREST_QUESTION_STUDY.md`` item F1,
``studies/PLANNER_LADDER_STUDY.md`` item F2), so they share one baseline: every
evaluation case asked through the session **before either round touched the
answering path** (``_data/ties_ladder_baseline.json``; the two Lean files of
the rounds were written while it was being taken, so its Lean declaration
count may already include them).

What is measured
----------------
**F1** -- every baseline case asked again: present, the same status (answered
or refused), and the cause of every text that moved, from
:data:`DECLARED_CAUSES`; a moved text with no declared cause is
``undeclared``.  The cases of :data:`PREFIX_CASES` must keep their old text as
a verbatim prefix (the ``nearest`` junction answer now ends with the question
that splits it); one that does not is listed in ``prefix_broken``.  F1 holds
when every baseline case is present with the same status, nothing is
undeclared and no prefix is broken.

The measurement asks every evaluation case (about fifteen minutes), so it is
stored beside the digest of its sources (``tools ties-ladder-frozen
--write``).  ``nearest_question_study`` reads the stored record for its own
F1.  When the baseline file is absent F1 cannot be measured: the record says
so, F1 is not met, and nothing is asked (a baseline taken now would not be
the one taken before the rounds' edits, so none is made up).

Exactness
---------
Strings, booleans and ints only.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from
``studies/NEAREST_QUESTION_STUDY.md`` (§4 F1, §7.1), ``MASTER_PLAN.md``
Phases 150, 151 and 162 (the D17 cause), the stored frozen-path record
carried in ``_data/nearest_question_study.json`` (its moved texts and their
causes), the CLI handler ``tools ties-ladder-frozen``, and the working
``budget_guard_frozen.py`` and ``frozen_path.py``.  The earlier stand-in of
29 October 2026 returned zero counts without measuring.*

Last altered 31 October 2026 (repository check: the measurement made
genuine).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "BASELINE_PATH", "DATA_PATH", "DECLARED_CAUSES", "PREFIX_CASES",
    "_SOURCES", "f1_frozen_path", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest",
    "ties_ladder_frozen_report",
]

_HERE = Path(__file__).resolve().parent
BASELINE_PATH: Path = _HERE / "_data" / "ties_ladder_baseline.json"

#: Why F1 is not met while the baseline is absent (the owner's wording for
#: the record, 31 October 2026; the same sentence in hole_reports_l5_study).
BASELINE_LOST: str = ("baseline lost in the October 2026 reorganisation; a "
                      "new baseline needs a frozen-path comparison before "
                      "the answering path moves again")
DATA_PATH: Path = _HERE / "_data" / "ties_ladder_frozen.json"

#: Why a baseline case's text may move, declared from its cause, never from
#: its size (the causes the stored record of the last re-take carried).
DECLARED_CAUSES: Dict[str, str] = {
    # the tree measures itself
    "report-lean": "the tree: the Lean declaration count, measured live",
    "report-retrieval": "the tree: the address-book index over the Lean "
                        "declarations",
    "report-relay": "the tree: the stack relay's strides are drawn from the "
                    "Lean declarations",
    "report-anonymous": "the tree: the anonymous register's queries are the "
                        "relay's strides",
    "report-generated": "the tree: the overlay's stored bytes, measured live",
    # the rounds' own
    "report-language": "Phase 150: the language report counts the evaluation "
                       "questions, which gain the round's cases",
    "report-query-escalation": "Phase 150: the query-escalation report counts "
                               "the evaluation cases, which gain the round's "
                               "cases",
    "nearest-address-junction": "Phase 150: the head is a certified junction, "
                                "so the answer ends with the question that "
                                "splits it (prefix kept)",
    # later rounds
    "unknown-nonsense": "Phase 154: the list of query kinds the refusal names "
                        "gains 'corpus'",
    "report-directives": "Phase 162: the directives report counts the "
                         "standing rules, which gain D17 (the owner's dating "
                         "rule)",
}

#: Cases whose old text must survive as a verbatim prefix.
PREFIX_CASES: Tuple[str, ...] = ("nearest-address-junction",)

_SOURCES: Tuple[str, ...] = (
    "reasoning/ties_ladder_frozen.py",
    "reasoning/nearest_address.py",
    "reasoning/timed_question.py",
    "reasoning/coordinate_junction.py",
    "reasoning/planner_ladder.py",
    "runtime/session.py",
    "runtime/parser.py",
    "runtime/stepwise.py",
    "evaluation/cases.py",
)

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


def f1_frozen_path(session=None) -> Dict[str, object]:
    """Every baseline case asked again, or -- without the baseline -- the
    reason F1 cannot be measured."""
    if not BASELINE_PATH.is_file():
        return {"F1": False, "baseline": "absent", "asked": 0, "cases": 0,
                "present": 0, "same_status": 0, "same_text": 0, "moved": [],
                "new_cases": [], "prefix_broken": [], "undeclared": [],
                "reason": (f"{BASELINE_PATH.name}: {BASELINE_LOST}")}
    from ..evaluation import cases as ev
    session = session or _session()
    questions = {c.id: c.question for c in ev.CASES}
    before = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["before"]
    answers: Dict[str, Tuple[bool, str]] = {}
    for cid, text in questions.items():
        sol = session.ask(text)
        answers[cid] = (bool(sol.ok), sol.answer)
    rows: List[Dict[str, object]] = []
    for b in before:
        cid = str(b["id"])
        if cid not in answers:
            rows.append({"id": cid, "present": False, "same_status": False,
                         "same_text": False, "cause": "absent"})
            continue
        ok, answer = answers[cid]
        same_text = answer == b["answer"]
        cause = None
        prefix_ok = None
        if not same_text:
            cause = DECLARED_CAUSES.get(cid, "undeclared")
            if cid in PREFIX_CASES:
                prefix_ok = answer.startswith(b["answer"])
        rows.append({"id": cid, "present": True,
                     "same_status": ok == bool(b["ok"]),
                     "same_text": same_text, "cause": cause,
                     "prefix_ok": prefix_ok})
    moved = [r for r in rows if r["present"] and not r["same_text"]]
    undeclared = [r["id"] for r in moved if r["cause"] == "undeclared"]
    prefix_broken = [r["id"] for r in moved if r.get("prefix_ok") is False]
    present = sum(1 for r in rows if r["present"])
    same_status = sum(1 for r in rows if r["same_status"])
    new = sorted(set(questions) - {str(b["id"]) for b in before})
    return {
        "F1": (present == len(rows) == same_status and len(rows) > 0
               and not undeclared and not prefix_broken),
        "baseline": "present",
        "asked": len(answers), "cases": len(rows), "present": present,
        "same_status": same_status,
        "same_text": sum(1 for r in rows if r["present"] and r["same_text"]),
        "moved": [{"id": r["id"], "cause": r["cause"]} for r in moved],
        "new_cases": new, "prefix_broken": prefix_broken,
        "undeclared": undeclared,
        "new_answers": {cid: {"ok": answers[cid][0],
                              "answer": answers[cid][1]} for cid in new},
    }


def compute(session=None) -> Dict[str, object]:
    frozen = f1_frozen_path(session)
    return {"frozen": frozen, "marks": {"F1": bool(frozen["F1"])}}


def module_digest() -> str:
    root = _HERE.parent
    paths = [root / n for n in sorted(set(_SOURCES))]
    if BASELINE_PATH.is_file():
        paths.append(BASELINE_PATH)
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                      ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = stored.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    if state()["fresh"]:
        return measurements()
    return None


def ties_ladder_frozen_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    s = state()
    return {
        "available": False,
        "reason": (f"the stored measurement is {s['verdict']}; re-take it "
                   f"with python3 -m glm_universal.tools ties-ladder-frozen "
                   f"--write"),
    }
