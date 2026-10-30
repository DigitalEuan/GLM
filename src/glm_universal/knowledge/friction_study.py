"""``glm_universal.knowledge.friction_study`` -- Phase 156's measurement -- the survey of the evaluation's 222 cases under seven declared perturbations (F1-F4, F1', F4', X1-X4), contact over the whole prompt (C1-C4, C1'-C3'), and the stick-slip reading (S1-S4, S1'-S4').  12 marks + 9 amended + 4 fix marks.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``friction_study.py`` was lost in the upload; this version is a working
stub that exposes the standard 8-function study apparatus.  The stored
measurement JSON (``_data/friction.json``) does not exist, so the report
function returns ``available=False``; the CLI subcommand ``friction``
prints the re-take instruction and exits 1.  When the full corpus
infrastructure is restored, run ``tools friction --write`` to take
the measurement.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest", "friction_report",
    "SURVEY_PATH",

]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "friction.json"

SURVEY_PATH = _HERE / "_data" / "friction_survey.json"

_SOURCES: Tuple[str, ...] = (
    "knowledge/friction_study.py",
    "knowledge/friction.py",
    "knowledge/friction_survey.py",
    "knowledge/model.py",
    "knowledge/reader.py",
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


from fractions import Fraction


def compute(knowledge: Any = None) -> Dict[str, object]:
    """Run the measurement and return the report dict.

    *Working stub.*  Returns the report dict shape with all marks
    ``False``, so the stored JSON (when it exists) carries the true
    marks and the CLI handler can pretty-print them.
    """
    marks: Dict[str, bool] = {m: False for m in ("F1", "F2", "F3", "F4", "C1", "C2", "C3", "C4", "S1", "S2", "S3", "S4",)}
    return {
        "survey": {"cases": 0, "base_passing": 0, "by_perturbation": {}},
        "corpus": {"contact": {"sentences": 0, "positions": 0, "correct": {"patch": 0, "contact": 0, "control": 0}}, "stickslip": {"read": 0, "readers": {}}},

        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def module_digest() -> str:
    root = _HERE.parent  # glm_universal/
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

def write_survey(jobs: int = 8) -> Path:
    """Write the survey JSON to :data:`SURVEY_PATH`.

    *Stub:* writes a minimal empty survey.
    """
    SURVEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    import json as _json
    SURVEY_PATH.write_text(
        _json.dumps({"cases": 0, "base_passing": 0, "by_perturbation": {}}) + "\n", encoding="utf-8")
    return SURVEY_PATH


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


def friction_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reasons": [(f"the stored measurement is absent; re-take it with "
                       f"python3 -m glm_universal.tools friction --write")],
    }
