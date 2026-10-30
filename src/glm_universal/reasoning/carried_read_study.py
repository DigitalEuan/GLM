"""``glm_universal.reasoning.carried_read_study`` -- the carried-read measurement.

The measurement of the machine reading what it carries: registers as
files, typed plans and field answers through GLM-BAT.  ``--write``
re-takes it; ``take_baseline`` takes the baseline.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original module was lost in the upload; this version is a working stub.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest", "take_baseline",
    "carried_read_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "carried_read_study.json"
BASELINE_PATH = _HERE / "_data" / "carried_read_baseline.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/carried_read_study.py",
    "reasoning/carrier_read.py",
    "reasoning/batch_machine.py",
    "runtime/session.py",
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
    """Working stub."""
    marks: Dict[str, bool] = {m: False for m in (
        "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8",
        "R9", "R10", "R11", "R12",
    )}
    return {
        "chains": {"admitted": 0, "register_reads": 0, "question_reads": 0,
                   "computed": 0, "carried": 0},
        "lies": {"register": 0, "question": 0, "computed": 0},
        "typed_plans": {"admitted": 0, "refused": 0},
        "field_answers": {"admitted": 0, "refused": 0},
        "texts": 0,
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def take_baseline() -> Path:
    """Take the baseline measurement and write it to :data:`BASELINE_PATH`.

    *Stub:* writes an empty baseline.
    """
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps(_plain(compute()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n",
        encoding="utf-8")
    return BASELINE_PATH


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


def carried_read_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reason": ("the stored measurement is absent; re-take it with "
                   "python3 -m glm_universal.tools carried-read --write"),
    }
