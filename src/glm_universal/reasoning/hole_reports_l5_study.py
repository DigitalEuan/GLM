"""``glm_universal.reasoning.hole_reports_l5_study`` -- Phase 149.

The configuration reading (``L5``) in the other deep-hole reports: the marks
of ``studies/HOLE_REPORTS_L5_STUDY.md``.  ``tools hole-reports-l5 --write``
re-takes them.

What is measured
----------------
* **C1, D1, E1, R1** -- the three readings of :mod:`hole_reports_l5` (the
  classifier's sanity query and the 44 queries; the escalation gate at every
  stored size; the joint reading's four failures and ``L5``'s per-type
  criterion at 1920 starts), from the stores that already exist.
* **Q1** -- the battery through the session: ``report hole classifier``,
  ``report hole ladder``, ``report hole failures`` and ``report hole
  configuration`` (the control).  Each must answer; the first three must end
  with the ``L5`` clause :mod:`hole_reports_l5` writes; every column-3 script
  must verify; and two mutants of each must be rejected (one of the round's
  own expected keys, and an ``l5_*`` key -- for the control a second own
  key).  A mutant whose key the answer does not state cannot be formed and
  counts as not rejected.
* **F1** -- the frozen path: every evaluation case of the baseline frozen
  before the answering-path edit (``_data/hole_l5_baseline.json``) asked
  again; present with the same status, every moved text with a declared cause
  (:data:`DECLARED_CAUSES`, which inherits
  :data:`budget_guard_frozen.DECLARED_CAUSES`), and the three reports' old
  texts kept verbatim as prefixes.  When the baseline file is absent, F1
  cannot be measured and is reported not met, with the reason; nothing is
  asked.

L1 (the Lean file builds) is the build's; :func:`lean_state` reports whether
the file is present and states its four theorems without ``sorry``.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from
``studies/HOLE_REPORTS_L5_STUDY.md`` (§4 marks, §7 results),
``MASTER_PLAN.md`` Phase 149, the CLI handler ``tools hole-reports-l5``
(the report keys it prints), ``budget_guard_frozen.py`` and
``answering_question.py`` (the frozen-path and mutant patterns).  The earlier
stand-in of 29 October 2026 returned all marks False without measuring.*

Last altered 31 October 2026 (repository check: the measurement made
genuine).
"""
from __future__ import annotations

import dataclasses
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity
from . import hole_reports_l5 as hl5

__all__ = [
    "DATA_PATH", "BASELINE_PATH", "_SOURCES", "BATTERY", "PREFIX_CASES",
    "DECLARED_CAUSES", "lean_state", "q1_battery", "f1_frozen_path",
    "compute", "measure", "write_measurements", "measurements", "state",
    "current", "module_digest", "hole_reports_l5_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "hole_reports_l5_study.json"
BASELINE_PATH = _HERE / "_data" / "hole_l5_baseline.json"

#: The battery of §3: ``(question, clause reading or None, own keys, l5 key)``.
#: The control (``report hole configuration``) carries no clause; its second
#: mutant alters a second key of its own.
BATTERY: Tuple[Tuple[str, Optional[str], Tuple[str, ...]], ...] = (
    ("report hole classifier", "classifier", ("correct", "l5_correct")),
    ("report hole ladder", "ladder", ("best_q0", "l5_passing")),
    ("report hole failures", "failures", ("correct", "l5_failures_correct")),
    ("report hole configuration", None, ("correct", "queries")),
)

#: The evaluation cases whose old text must survive as a verbatim prefix.
PREFIX_CASES: Dict[str, str] = {
    "report-hole-classifier": "Phase 149: the report keeps the first round's "
                              "answer and gains the L5 clause (prefix kept)",
    "report-hole-ladder": "Phase 149: the report keeps the escalation round's "
                          "answer and gains the L5 clause (prefix kept)",
    "report-hole-failures": "Phase 149: the report keeps the failure round's "
                            "answer and gains the L5 clause (prefix kept)",
}


def _declared_causes() -> Dict[str, str]:
    from . import budget_guard_frozen as bgf
    out = dict(bgf.DECLARED_CAUSES)
    out.setdefault("report-directives",
                   "Phase 162: the directives report counts the standing "
                   "rules, which gain D17 (the owner's dating rule)")
    return out


#: Why a baseline case's text may move (inherited from the frozen path of
#: Phases 147-148, MASTER_PLAN.md Phase 162/D17).
DECLARED_CAUSES: Dict[str, str] = _declared_causes()

_SOURCES: Tuple[str, ...] = (
    "reasoning/hole_reports_l5_study.py",
    "reasoning/hole_reports_l5.py",
    "reasoning/configuration_classifier.py",
    "reasoning/configuration_queries.py",
    "reasoning/configuration_reading.py",
    "reasoning/share_ensemble.py",
    "reasoning/deep_hole_classifier.py",
    "reasoning/deep_hole_failures.py",
    "reasoning/deep_hole_escalation.py",
    "reasoning/budget_guard_frozen.py",
    "runtime/reports/lattice_geometry.py",
    "runtime/tct_engine.py",
    "runtime/session.py",
    "evaluation/cases.py",
)

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


def lean_state() -> Dict[str, object]:
    """L1's file: present, its theorems stated, and no ``sorry``."""
    from ..constants import lean_file
    path = lean_file(hl5.LEAN_FILE)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    found = [t for t in hl5.LEAN_THEOREMS if f"theorem {t}" in text]
    return {"file": hl5.LEAN_FILE, "present": bool(text),
            "declared": len(hl5.LEAN_THEOREMS), "theorems": len(found),
            "sorry": text.count("sorry"),
            "met": bool(text) and len(found) == len(hl5.LEAN_THEOREMS)
                   and "sorry" not in text}


# ═════════════════════════════════════════════════════════════════════════
# Q1 -- the battery
# ═════════════════════════════════════════════════════════════════════════

def _verifies(sol) -> bool:
    from ..runtime.tct_engine import build_trace, verify_trace
    return bool(verify_trace(build_trace(sol)).verified)


def _mutant(sol, key: str, base_ok: bool = True) -> Optional[bool]:
    """Alter ``key`` of the answer's expected values; ``True`` when column 3
    rejects the altered claim, ``None`` when the answer states no such key.
    A rejection counts only where the unaltered script verifies: a script
    that never verifies rejects everything and so tells nothing."""
    expected = dict(sol.expected or {})
    if key not in expected:
        return None
    if not base_ok:
        return False
    altered = dict(expected)
    altered[key] = str(expected[key]) + "-altered"
    bad = dataclasses.replace(sol, expected=altered)
    return not _verifies(bad)


def q1_battery(session=None, readings=None) -> Dict[str, object]:
    session = session or _session()
    readings = readings if readings is not None else hl5.readings()
    clause_of = {"classifier": hl5.classifier_clause,
                 "ladder": hl5.ladder_clause,
                 "failures": hl5.failures_clause}
    rows: List[Dict[str, object]] = []
    for question, reading, keys in BATTERY:
        sol = session.ask(question)
        row: Dict[str, object] = {"question": question, "answered":
                                  bool(sol.ok)}
        if reading is not None:
            clause = clause_of[reading](readings[reading])
            row["clause"] = bool(sol.ok and clause and clause in sol.answer)
        else:
            row["clause"] = None
        row["script"] = bool(sol.ok) and _verifies(sol)
        row["mutants"] = [{"key": k, "rejected": (
                              _mutant(sol, k, bool(row["script"]))
                              if sol.ok else None)}
                          for k in keys]
        rows.append(row)
    mutants = [m for r in rows for m in r["mutants"]]
    return {
        "rows": rows, "questions": len(rows),
        "answered": sum(1 for r in rows if r["answered"]),
        "clauses": sum(1 for r in rows if r["clause"]),
        "clause_reports": sum(1 for r in rows if r["clause"] is not None),
        "scripts": sum(1 for r in rows if r["script"]),
        "mutants": len(mutants),
        "mutants_rejected": sum(1 for m in mutants if m["rejected"] is True),
        "mutants_unformed": sum(1 for m in mutants if m["rejected"] is None),
    }


# ═════════════════════════════════════════════════════════════════════════
# F1 -- the frozen path
# ═════════════════════════════════════════════════════════════════════════

def f1_frozen_path(session=None) -> Dict[str, object]:
    """Every baseline case asked again (about fifteen minutes), or -- with
    the baseline file absent -- the reason F1 cannot be measured."""
    empty = {"baseline": "absent", "cases": 0, "present": 0,
             "same_status": 0, "same_text": 0,
             "prefix_cases": len(PREFIX_CASES),
             "prefix_kept": 0, "moved": [], "undeclared": [],
             "prefix_broken": [], "new_cases": [], "asked": 0,
             "reason": (f"{BASELINE_PATH.name}: baseline lost in the "
                        f"October 2026 reorganisation; a new baseline needs "
                        f"a frozen-path comparison before the answering "
                        f"path moves again")}
    if not BASELINE_PATH.is_file():
        return empty
    from ..evaluation import cases as ev
    session = session or _session()
    before = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["before"]
    questions = {c.id: c.question for c in ev.CASES}
    rows = []
    for b in before:
        cid = str(b["id"])
        if cid not in questions:
            rows.append({"id": cid, "present": False, "same_status": False,
                         "same_text": False, "cause": "absent",
                         "prefix": None})
            continue
        sol = session.ask(questions[cid])
        same_text = sol.answer == b["answer"]
        prefix = None
        if cid in PREFIX_CASES:
            prefix = sol.answer.startswith(b["answer"])
        if same_text:
            cause = None
        elif cid in PREFIX_CASES:
            cause = PREFIX_CASES[cid] if prefix else "prefix broken"
        else:
            cause = DECLARED_CAUSES.get(cid, "undeclared")
        rows.append({"id": cid, "present": True,
                     "same_status": bool(sol.ok) == bool(b["ok"]),
                     "same_text": same_text, "cause": cause,
                     "prefix": prefix})
    moved = [r for r in rows if r["present"] and not r["same_text"]]
    prefixed = [r for r in rows if r["id"] in PREFIX_CASES and r["present"]]
    return {
        "baseline": "present", "cases": len(rows),
        "present": sum(1 for r in rows if r["present"]),
        "same_status": sum(1 for r in rows if r["same_status"]),
        "same_text": sum(1 for r in rows if r["present"] and r["same_text"]),
        "prefix_cases": len(PREFIX_CASES),
        "prefix_kept": sum(1 for r in prefixed if r["prefix"]),
        "moved": [{"id": r["id"], "cause": r["cause"]} for r in moved],
        "undeclared": [r["id"] for r in moved if r["cause"] == "undeclared"],
        "prefix_broken": [r["id"] for r in prefixed if not r["prefix"]],
        "new_cases": sorted(set(questions) - {str(b["id"]) for b in before}),
        "asked": len(rows),
    }


# ═════════════════════════════════════════════════════════════════════════
# The marks
# ═════════════════════════════════════════════════════════════════════════

_DEFAULTS = {
    "classifier": {"seed_correct": 0, "seed_queries": 0, "correct": 0,
                   "wrong": 0, "refused": 0, "queries": 0, "answered": 0,
                   "within_radius": 0, "within_answered": 0},
    "ladder": {"passing": 0, "sizes": 0, "smallest_passing": None,
               "passes_without_criterion": []},
    "failures": {"l5_correct": 0, "joint_failures": 0,
                 "locally_certified": 0, "types": 0,
                 "starts": hl5.FAILURE_STARTS},
}


def compute(session=None) -> Dict[str, object]:
    """Every measured mark of §4 (L1 is the build's)."""
    session = session or _session()
    raw = hl5.readings()
    readings = {k: dict(_DEFAULTS[k], **v) for k, v in raw.items()}
    c, d, e = readings["classifier"], readings["ladder"], readings["failures"]
    q = q1_battery(session, raw)
    f = f1_frozen_path(session)
    marks = {
        "C1": bool(c.get("available")) and c["seed_correct"]
              == c["seed_queries"] == 10 and c["correct"] == c["queries"]
              == 44 and c["wrong"] == 0,
        "D1": bool(d.get("available")) and d["passing"] == d["sizes"] > 0
              and d["smallest_passing"] == 240,
        "E1": bool(e.get("available")) and e["l5_correct"]
              == e["joint_failures"] == 4 and e["locally_certified"]
              == e["types"] > 0 and bool(e.get("rho_below_one")),
        "R1": bool(c.get("available")) and c["within_answered"]
              == c["within_radius"] > 0,
        "Q1": q["answered"] == q["questions"] == 4 and q["clauses"]
              == q["clause_reports"] == 3 and q["scripts"] == 4
              and q["mutants_rejected"] == q["mutants"] == 8,
        "F1": f["baseline"] == "present" and f["present"] == f["cases"]
              == f["same_status"] > 0 and not f["undeclared"]
              and f["prefix_kept"] == f["prefix_cases"],
    }
    return {
        "readings": readings, "questions": q, "frozen": f,
        "lean": lean_state(), "marks": marks,
        "met": sum(1 for v in marks.values() if v), "taken": len(marks),
    }


def module_digest() -> str:
    root = _HERE.parent
    names = sorted(set(_SOURCES))
    paths = [root / n for n in names]
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


def hole_reports_l5_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    s = state()
    return {
        "available": False,
        "reason": (f"the stored measurement is {s['verdict']}; re-take it "
                   f"with python3 -m glm_universal.tools hole-reports-l5 "
                   f"--write"),
    }
