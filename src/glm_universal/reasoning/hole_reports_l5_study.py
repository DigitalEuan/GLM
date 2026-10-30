"""``glm_universal.reasoning.hole_reports_l5_study`` -- Phase 149.

The configuration reading (``L5``) in the other deep-hole reports: the
marks of ``studies/HOLE_REPORTS_L5_STUDY.md``.  ``--write`` re-takes
them (about fifteen minutes for the frozen path).

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original module was lost in the upload; this version is a working stub
that exposes the standard 8-function study apparatus.  The stored
measurement JSON does not exist, so the report returns ``available=False``.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest",
    "hole_reports_l5_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "hole_reports_l5_study.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/hole_reports_l5_study.py",
    "reasoning/deep_hole_classifier.py",
    "reasoning/deep_hole_failures.py",
    "reasoning/deep_hole_escalation.py",
)

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    from fractions import Fraction
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def compute() -> Dict[str, object]:
    """Working stub: returns the report dict shape with all marks False."""
    marks: Dict[str, bool] = {m: False for m in
                              ("C1", "D1", "E1", "R1", "Q1", "F1")}
    return {
        "readings": {
            "classifier": {"seed_correct": 0, "seed_queries": 0,
                           "correct": 0, "wrong": 0, "refused": 0,
                           "queries": 0, "answered": 0, "within_radius": 0},
            "ladder": {"passing": 0, "sizes": 0, "smallest_passing": 0,
                       "passes_without_criterion": 0},
            "failures": {"l5_correct": 0, "joint_failures": 0,
                         "locally_certified": 0, "types": 0, "starts": 0},
        },
        "questions": {"answered": 0, "questions": 0, "scripts": 0,
                      "mutants": 0, "mutants_rejected": 0},
        "frozen": None,
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def module_digest() -> str:
    root = _HERE.parent
    paths = [root / n for n in sorted(set(_SOURCES))]
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
    return {
        "available": False,
        "reason": ("the stored measurement is absent; re-take it with "
                   "python3 -m glm_universal.tools hole-reports-l5 --write"),
    }
