"""``glm_universal.knowledge.thermo_friction_study`` -- Phase 159's measurement -- the bimetallic governor (A1-A7), the thermoelectric prompt anchor (B1-B6, B6'), and the sintered register-vocabulary respelling (C1-C6).  19 marks + 1 amended.  Ships sintering if C1-C4 met.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``thermo_friction_study.py`` was lost in the upload; this version is a working
stub that exposes the standard 8-function study apparatus.  The stored
measurement JSON (``_data/thermo_friction.json``) does not exist, so the report
function returns ``available=False``; the CLI subcommand ``thermo-friction``
prints the re-take instruction and exits 1.  When the full corpus
infrastructure is restored, run ``tools thermo-friction --write`` to take
the measurement.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest", "thermo_friction_report",
    "BLIND_SPOT_PATH",

]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "thermo_friction.json"

BLIND_SPOT_PATH = _HERE / "_data" / "thermo_friction_blind_spot.json"

_SOURCES: Tuple[str, ...] = (
    "knowledge/thermo_friction_study.py",
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
    marks: Dict[str, bool] = {m: False for m in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "B1", "B2", "B3", "B4", "B5", "B6", "C1", "C2", "C3", "C4", "C5", "C6",)}
    return {
        "corpus": {"governor": {"position": {}, "most_frequent": {}, "overlap": {}, "distinct": {}}, "anchor": {"read": 0, "hot_sentences": 0, "readers": {}}, "sinter": {"recovery_set": 0, "recovery": {}, "lexicon_changed": {}}},
        "shipped": (),

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

def write_blind_spot() -> Path:
    """Write the blind-spot JSON to :data:`BLIND_SPOT_PATH`.

    *Stub:* writes an empty blind-spot record.
    """
    BLIND_SPOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    import json as _json
    BLIND_SPOT_PATH.write_text(
        _json.dumps({"question": "", "exit": 0}) + "\n", encoding="utf-8")
    return BLIND_SPOT_PATH


def write_frozen(path: Path) -> Path:
    """Copy the supplied frozen JSON into :data:`_HERE/_data/thermo_friction_frozen.json`.

    *Stub:* echoes the supplied JSON.
    """
    target = _HERE / "_data" / "thermo_friction_frozen.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copyfile(str(path), str(target))
    return target


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


def thermo_friction_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reasons": [(f"the stored measurement is absent; re-take it with "
                       f"python3 -m glm_universal.tools thermo-friction --write")],
    }
