"""``glm_universal.reasoning.budget_guard_frozen`` -- the frozen path of
Phases 147 and 148, and the ladder audit taken in the same pass.

Both rounds move answers the evaluation pins (``studies/BUDGET_READING_STUDY.md``
item F1, ``studies/NEAREST_ADDRESS_STUDY.md`` item F1), so they share one
baseline: every evaluation case asked through the session **before either
round touched the answering path** (``_data/budget_guard_baseline.json``; the
two Lean files of the rounds were written first, so the Lean declaration count
the baseline saw already includes them).

What is measured
----------------
* **F1** -- every baseline case asked again: present, the same status
  (answered or refused), and the cause of every text that moved, from
  :data:`DECLARED_CAUSES`.  A moved text with no declared cause is
  ``undeclared``.
* **A0** -- the ladder audit: while the whole evaluation is asked, every
  function of the construction ladder's measurement modules that reads the
  ladder *unguarded* is wrapped and counted.  Phase 130 found no answering
  path that reads it; A0 is that finding measured on every question the
  evaluation asks, after both rounds.

The measurement asks about two hundred questions (about fifteen minutes), so
it is stored beside the digest of its sources
(``tools budget-guard-frozen --write``).

Exactness
---------
Strings, booleans and ints only.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "BASELINE_PATH", "DATA_PATH", "DECLARED_CAUSES", "UNGUARDED",
    "f1_frozen_path", "measure", "write_measurements", "measurements",
    "state", "current",
]

_HERE = Path(__file__).resolve().parent
BASELINE_PATH: Path = _HERE / "_data" / "budget_guard_baseline.json"
DATA_PATH: Path = _HERE / "_data" / "budget_guard_frozen.json"

#: Why a baseline case's text may move, declared before the measurement.
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
    # the new kind
    "unknown-nonsense": "Phase 147: the list of query kinds the refusal names "
                        "gains 'hole'",
    "report-language": "Phases 147-148: the language report counts the query "
                       "kinds and the evaluation questions, which gain the "
                       "new kind and the new cases",
    "report-query-escalation": "Phases 147-148: the query-escalation report "
                               "counts the evaluation cases, which gain the "
                               "new ones",
    "report-routes": "Phase 147: the route table lists the query kinds, which "
                     "gain 'hole'",
}

#: The functions that read the construction ladder without the guard: the
#: measurement modules' own readings (Phases 125-129).
UNGUARDED: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("ladder_escalation", ("reading", "answer_at_rung", "answer_with_order",
                           "run_orders", "run_fixed_rungs",
                           "ladder_escalation_report", "length_sweep")),
    ("norm256_hex", ("_named", "audit", "run_ladder", "fill",
                     "norm256_hex_report")),
    ("cell_guard", ("guarded_named", "read_set", "union_ladder",
                    "cell_guard_report")),
    ("placement_guard", ("read_set", "placement_guard_report")),
)

_SOURCES: Tuple[str, ...] = (
    "reasoning/budget_guard_frozen.py",
    "reasoning/_data/budget_guard_baseline.json",
    "reasoning/hole_reading.py",
    "reasoning/nearest_address.py",
    "runtime/session.py",
    "runtime/parser.py",
    "runtime/reports/lattice_geometry.py",
    "evaluation/cases.py",
)


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


def _instrument() -> Tuple[Dict[str, int], List[Tuple[object, str, object]]]:
    """Wrap every unguarded reading; return the counter and what to undo."""
    import importlib
    counts: Dict[str, int] = {}
    undo: List[Tuple[object, str, object]] = []
    for module_name, names in UNGUARDED:
        module = importlib.import_module(f"{__package__}.{module_name}")
        for name in names:
            original = getattr(module, name, None)
            if original is None:
                continue
            key = f"{module_name}.{name}"
            counts[key] = 0

            def wrapper(*args, __o=original, __k=key, **kwargs):
                counts[__k] += 1
                return __o(*args, **kwargs)

            functools.update_wrapper(wrapper, original)
            setattr(module, name, wrapper)
            undo.append((module, name, original))
    return counts, undo


def f1_frozen_path(session=None) -> Dict[str, object]:
    """F1 and A0 in one pass over the evaluation."""
    from ..evaluation import cases as ev
    session = session or _session()
    questions = {c.id: c.question for c in ev.CASES}
    before = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["before"]
    counts, undo = _instrument()
    rows = []
    answers: Dict[str, Tuple[bool, str]] = {}
    try:
        for cid, text in questions.items():
            sol = session.ask(text)
            answers[cid] = (bool(sol.ok), sol.answer)
    finally:
        for module, name, original in undo:
            setattr(module, name, original)
    for b in before:
        cid = str(b["id"])
        if cid not in answers:
            rows.append({"id": cid, "present": False, "same_status": False,
                         "same_text": False, "cause": "absent"})
            continue
        ok, answer = answers[cid]
        same_text = answer == b["answer"]
        cause = None if same_text else DECLARED_CAUSES.get(cid, "undeclared")
        rows.append({"id": cid, "present": True,
                     "same_status": ok == bool(b["ok"]),
                     "same_text": same_text, "cause": cause})
    new = sorted(set(questions) - {str(b["id"]) for b in before})
    moved = [r for r in rows if r["present"] and not r["same_text"]]
    return {
        "cases": len(rows),
        "present": sum(r["present"] for r in rows),
        "same_status": sum(r["same_status"] for r in rows),
        "same_text": sum(r["present"] and r["same_text"] for r in rows),
        "moved": [{"id": r["id"], "cause": r["cause"]} for r in moved],
        "undeclared": [r["id"] for r in moved if r["cause"] == "undeclared"],
        "new_cases": new,
        "new_answers": {cid: {"ok": answers[cid][0],
                              "answer": answers[cid][1]} for cid in new},
        "asked": len(answers),
        "audit": {"unguarded_calls": {k: v for k, v in counts.items() if v},
                  "functions_watched": len(counts),
                  "total": sum(counts.values())},
    }


def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))],
                                 root)


def measure() -> Dict[str, object]:
    out = f1_frozen_path()
    out["source_digest"] = module_digest()
    return out


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(measure(), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


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
    return {"present": True, "fresh": fresh,
            "verdict": "current" if fresh else "stale",
            "live_digest": live, "stored_digest": stored.get("source_digest")}


def current() -> Optional[Dict[str, object]]:
    return measurements() if state()["fresh"] else None
