"""``glm_universal.reasoning.patience_census`` -- the three census centres the
frozen path left uncertified, re-read with a patience that lets the probe
finish (Phase 123, part A; a post-hoc follow-up, declared after the census).

What happened
-------------
:mod:`hole_census` reached all thirteen new Niemeier types by the declared
walk (1,280 walks), but it certifies each reference centre a second time
with the construction convention of the first round -- 400 probes at the
reference seed with a patience of 60 starts -- and three of the thirteen
failed that second reading: ``A_17 E_7`` (26 vertices), ``A_5^4 D_4`` (29)
and ``D_4^6`` (30).  The probe stopped after 60 starts without a new vertex
and returned 25, 28 and 29 vertices, a set the diagram reader cannot
identify.  The pre-registered mark A1 is scored on that census and is
missed; this module does not change it.

The follow-up
-------------
Declared after the census, and labelled post hoc wherever it is reported:
the same three centres, the same reference seed, the frozen path unchanged,
with **1,600 probes and a patience of 240 starts**.  A centre is kept only if
that reading certifies it as the type the walk named.  Each kept centre is
then run through the escalation round's ensemble at both seeds to 7680
starts, exactly as :func:`hole_census.new_ensembles` runs the other ten, so
that the ``L5`` cell over all 23 types can be read beside the pre-registered
one over the 20 the census certified.

Exactness
---------
Integers and :class:`~fractions.Fraction` only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from . import deep_hole_classifier as dhc
from . import deep_holes as dh
from . import hole_census as hc
from . import share_ensemble as se

__all__ = [
    "PROBES", "PATIENCE", "recertify", "module_digest", "measure",
    "write_measurements", "measurements", "state", "current", "DATA_PATH",
]

#: The follow-up's probe budget and patience (the census used 400 and 60).
PROBES: int = 1600
PATIENCE: int = 240


def _recertify_one(entry: Dict[str, object]) -> Dict[str, object]:
    reading = dh.classify_carrier(entry["center"], probes=PROBES,
                                  seed=dhc.REFERENCE_SEED, patience=PATIENCE)
    out = {key: entry[key] for key in ("stage", "how", "seed", "center")
           if key in entry}
    out.update({
        "census_type": entry.get("type"),
        "census_vertex_count": int(entry.get("vertex_count") or 0),
        "type": reading["niemeier_type"],
        "certified": bool(reading["certified"]),
        "starts_run": int(reading["probe"].get("starts_run") or 0),
        "vertices": tuple(tuple(int(x) for x in v)
                          for v in reading["probe"]["vertices"]),
        "vertex_count": int(reading["probe"]["vertex_count"]),
    })
    return out


def recertify(census: Optional[Dict[str, object]] = None
              ) -> Tuple[Dict[str, object], ...]:
    """Every census entry the census left uncertified, read again."""
    census = census if census is not None else hc.current()
    if census is None:
        return ()
    return tuple(_recertify_one(e) for e in census["census"]["entries"]
                 if not e["certified"])


# ═════════════════════════════════════════════════════════════════════════
# THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "patience_census.json")

_SOURCES: Tuple[str, ...] = ("reasoning/patience_census.py",) + tuple(
    hc._SOURCES)


def module_digest() -> str:
    """One digest over the sources, and over the census it re-reads."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    paths = [root / name for name in names] + [hc.DATA_PATH]
    return integrity.tree_digest(paths, root)


def measure(jobs: Optional[int] = None) -> Dict[str, object]:
    """The re-reading, and the ensembles of every centre it certifies."""
    workers = jobs if jobs is not None else (os.cpu_count() or 1)
    entries = recertify()
    kept = [e for e in entries
            if e["certified"] and e["type"] is not None]
    holes = hc.new_ensembles(kept, hc.TOP, workers) if kept else ()
    return {"probes": PROBES, "patience": PATIENCE, "entries": entries,
            "holes": holes, "sizes": hc.SIZES, "top": hc.TOP,
            "source_digest": module_digest()}


def write_measurements(path: Optional[Path] = None,
                       jobs: Optional[int] = None) -> Path:
    """Take the follow-up and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(se._freeze(measure(jobs)), sort_keys=True,
                   ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = se._thaw(json.loads(DATA_PATH.read_text(encoding="utf-8")))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The follow-up if it still describes the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
