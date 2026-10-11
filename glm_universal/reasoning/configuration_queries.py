"""``glm_universal.reasoning.configuration_queries`` -- the escalation round's
44 queries, read by the configuration reading ``L5`` at 1920 starts
(Phase 123, part B; the measurement half).

``studies/LATTICE_COMPLETION_STUDY.md`` §2.B puts ``L5`` into the deep-hole
answering path.  The answer rule, the absences and the report are
:mod:`glm_universal.reasoning.configuration_classifier`; this module only
takes and stores what they read, so that the rule can be read again without
re-running an ensemble:

* the 44-query set exactly as :func:`deep_hole_failures.plan` rebuilds it
  (the escalation round's construction), with each query's centre and seed;
* for each query, the joint reading's verdict at ``(joint, 1920)`` -- the
  stopping rule B1 asks for the recorded 40 of 44 -- and the query's ``L5``
  profile at 1920 starts;
* the ten reference profiles at the reference seed, under both readings.

The ensembles are :func:`deep_hole_escalation.emissions`, run in parallel by
:func:`deep_hole_failures.fill`; the cache stores profiles, never records.

Exactness
---------
Integers and :class:`~fractions.Fraction` only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from .. import integrity
from . import configuration_reading as cr
from . import deep_hole_escalation as de
from . import deep_hole_failures as dhf
from . import share_ensemble as se

__all__ = ["STARTS", "measure", "write_measurements", "measurements",
           "module_digest", "state", "current", "DATA_PATH"]

#: The escalation round's passing cell, where the classifier reads.
STARTS: int = dhf.CELL_STARTS


def measure(parallel: bool = True) -> Dict[str, object]:
    """Every ensemble the 44 queries need, read by both readings."""
    dhf.fill(parallel)
    layout = dhf.plan()
    references = tuple(
        {"label": label,
         "profile": cr.configuration_profile(
             dhf.record_for(centre, de.REFERENCE_SEED))}
        for label, centre in layout["references"])          # type: ignore[misc]
    joint = {row["query"]: row for row in dhf.query_rows()}
    queries = []
    for query in layout["queries"]:                         # type: ignore[union-attr]
        if not query.get("used"):
            queries.append({"name": str(query["name"]), "used": False,
                            "truth": str(query["truth"]),
                            "kind": str(query["kind"]),
                            "reason": str(query["reason"])})
            continue
        record = dhf.record_for(query["centre"], int(query["seed"]))
        row = joint[str(query["name"])]
        queries.append({
            "name": str(query["name"]), "used": True,
            "truth": str(query["truth"]), "kind": str(query["kind"]),
            "seed": int(query["seed"]),
            "joint_label": row["label"], "joint_correct": bool(row["correct"]),
            "profile": cr.configuration_profile(record),
        })
    return {"starts": STARTS, "references": references,
            "queries": tuple(queries), "source_digest": module_digest()}


DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "configuration_queries.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/configuration_queries.py", "reasoning/configuration_reading.py",
    "reasoning/deep_hole_failures.py",
) + tuple(de._SOURCES)


def module_digest() -> str:
    """One digest over the sources the stored profiles came from."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    return integrity.tree_digest([root / name for name in names], root)


def write_measurements(path: Optional[Path] = None,
                       parallel: bool = True) -> Path:
    """Take the measurement and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(se._freeze(measure(parallel)), sort_keys=True,
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
    """The stored profiles if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
