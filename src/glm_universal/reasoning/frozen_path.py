"""``glm_universal.reasoning.frozen_path`` -- the frozen-path comparison of the
lattice round (Phase 123, mark B5).

``studies/LATTICE_COMPLETION_STUDY.md`` §2.B declared that putting the
configuration reading into the answering path must not move an existing
answer: *every evaluation case present before the round returns the same
answer and the same refusal after it.*

What "before" is
----------------
The answers of every evaluation case as the query-escalation store
(``_data/query_escalation.json``) recorded them before the round touched the
answering path, copied unchanged into ``_data/lattice_frozen_baseline.json``
with the digest of the store they came from.  That store was taken before
Phase 121, so a figure the tree measures of itself (the Lean declaration
count, the address-book retrieval figures, the stored bytes) also moved in
Phases 121 and 122; those differences are listed, not hidden.

What is compared
----------------
For every case of the baseline: whether it is still present, whether it is
still answered or still refused (``ok``), and whether the answer text is
identical.  Every case whose text moved is listed with the declared reason
from :data:`DECLARED_CAUSES`; a moved text with no declared cause is reported
as ``undeclared``.

B5 holds when every baseline case is present, no case moves between answered
and refused, and no moved text is undeclared.

Exactness
---------
Strings and booleans only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "BASELINE_PATH", "DATA_PATH", "DECLARED_CAUSES", "baseline", "measure",
    "write_measurements", "measurements", "module_digest", "state", "current",
    "frozen_path_report",
]

_HERE = Path(__file__).resolve().parent
BASELINE_PATH: Path = _HERE / "_data" / "lattice_frozen_baseline.json"
DATA_PATH: Path = _HERE / "_data" / "lattice_frozen_path.json"

#: Why a case's answer text may differ from the baseline.  Declared from the
#: cause of each difference, never from its size; a case whose text moved
#: for any other reason is ``undeclared`` and fails B5.
DECLARED_CAUSES: Dict[str, str] = {
    "report-unknown-subject": "this round: the list of report subjects in "
                              "the refusal gains 'hole configuration'",
    "report-pipeline": "this round: the pipeline gains the lattice-completion "
                       "row",
    "report-language": "this round: the count of evaluation questions of the "
                       "undescribed kinds gains the new case",
    "report-lean": "the tree: the Lean declaration count, measured live",
    "report-retrieval": "the tree: the address-book index over the Lean "
                        "declarations, measured live",
    "report-relay": "the tree: the stack relay's query strides are drawn "
                    "from the Lean declarations",
    "report-anonymous": "the tree: the anonymous register's queries are the "
                        "relay's strides",
    "report-generated": "the tree: the overlay's stored bytes, measured live",
    "report-query-escalation": "this round: the query-escalation report "
                               "counts the evaluation cases, which gain the "
                               "new one, and it is re-taken over them",
    "unknown-nonsense": "Phase 134: the list of query kinds the refusal "
                        "names gains 'carrier'",
}

_SOURCES: Tuple[str, ...] = (
    "reasoning/frozen_path.py",
    "reasoning/_data/lattice_frozen_baseline.json",
    "evaluation/cases.py",
)


def baseline() -> Dict[str, object]:
    """The answers before the round, as stored."""
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def module_digest() -> str:
    """One digest over the baseline, the case list and this module."""
    root = _HERE.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def measure(session=None) -> Dict[str, object]:
    """Ask every baseline case again and compare."""
    from ..evaluation import cases as ev
    from ..runtime.session import GeometricSession
    session = session or GeometricSession()
    questions = {case.id: case.question for case in ev.CASES}
    rows: List[Dict[str, object]] = []
    for before in baseline()["before"]:
        case_id = str(before["id"])
        if case_id not in questions:
            rows.append({"id": case_id, "present": False, "same_status": False,
                         "same_text": False, "cause": None})
            continue
        after = session.ask(questions[case_id])
        same_text = after.answer == before["answer"]
        rows.append({
            "id": case_id, "present": True,
            "before_ok": bool(before["ok"]), "after_ok": bool(after.ok),
            "same_status": bool(after.ok) == bool(before["ok"]),
            "same_text": same_text,
            "cause": None if same_text else DECLARED_CAUSES.get(
                case_id, "undeclared"),
        })
    new = sorted(set(questions) - {str(b["id"]) for b in baseline()["before"]})
    return {"rows": tuple(rows), "new_cases": tuple(new),
            "source_digest": module_digest()}


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the comparison and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(measure(), indent=1, sort_keys=True,
                                 default=list) + "\n", encoding="utf-8")
    return target


def measurements() -> Optional[Dict[str, object]]:
    """The stored comparison, or ``None`` if absent."""
    if not DATA_PATH.exists():
        return None
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def state() -> Dict[str, object]:
    """Whether the store is present and fresh against its sources."""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same,
            "verdict": "fresh" if same else "stale",
            "live_digest": live, "stored_digest": stored.get("source_digest")}


def current() -> Optional[Dict[str, object]]:
    """The stored comparison if it is fresh, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored


def frozen_path_report() -> Dict[str, object]:
    """B5 and its counts, from the store."""
    data = current()
    if data is None:
        return {"available": False, "reason": (
            "the frozen-path comparison is absent or stale; re-take it with "
            "python3 -m glm_universal.tools frozen-path --write")}
    rows = data["rows"]
    moved = [r for r in rows if r["present"] and not r["same_text"]]
    undeclared = [r["id"] for r in moved if r["cause"] == "undeclared"]
    present = sum(1 for r in rows if r["present"])
    same_status = sum(1 for r in rows if r["same_status"])
    return {
        "available": True, "cases": len(rows), "present": present,
        "same_status": same_status,
        "same_text": sum(1 for r in rows if r["present"] and r["same_text"]),
        "moved": tuple({"id": r["id"], "cause": r["cause"]} for r in moved),
        "undeclared": tuple(undeclared),
        "new_cases": tuple(data["new_cases"]),
        "holds": (present == len(rows) and same_status == len(rows)
                  and not undeclared),
    }
