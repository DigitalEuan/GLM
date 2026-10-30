"""``glm_universal.knowledge.confidence_curve`` -- Phase 168's measurement -- the sure/balanced/candidate modes chosen on a calibration fold (C1-C6) and the definitions' quality description (D1, D2).  8 marks.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``confidence_curve.py`` was lost in the upload; this version is a working
stub that exposes the standard 8-function study apparatus.  The stored
measurement JSON (``_data/confidence_curve.json``) does not exist, so the report
function returns ``available=False``; the CLI subcommand ``confidence-curve``
prints the re-take instruction and exits 1.  When the full corpus
infrastructure is restored, run ``tools confidence-curve --write`` to take
the measurement.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest", "confidence_curve_report",
    "TOP",

]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "confidence_curve.json"

TOP: int = 3  # the candidate top-K

_SOURCES: Tuple[str, ...] = (
    "knowledge/confidence_curve.py",
    "knowledge/answer.py",
    "knowledge/glossary.py",
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
    marks: Dict[str, bool] = {m: False for m in ("C1", "C2", "C3", "C4", "C5", "C6", "D1", "D2",)}
    return {
        "calibration": {"positions": 0, "unguarded": 0},
        "held": {"positions": 0, "unguarded": 0},
        "modes": {"sure": {"chosen": 0, "guard": 0, "calibration": {}, "held": {}, "control": {}}, "balanced": {"chosen": 0, "guard": 0, "calibration": {}, "held": {}, "control": {}}},
        "candidate": {"held": {"hit_rate": 0, "coverage": 0}},
        "definitions": {"described": 0, "answered": 0, "strong": 0, "strong_agree": 0, "weak": 0, "weak_agree": 0},

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


def confidence_curve_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reason": (f"the stored measurement is absent; re-take it with "
                   f"python3 -m glm_universal.tools confidence-curve --write"),
    }
