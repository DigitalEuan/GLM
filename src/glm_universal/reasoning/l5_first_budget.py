"""``glm_universal.reasoning.l5_first_budget`` -- ``L5`` at the first round's
budget (Phase 152).

``studies/L5_FIRST_BUDGET_STUDY.md`` asks whether the configuration reading
``L5``'s answer rule names the escalation round's 44 queries at 240 starts,
the classifier round's budget, where Phase 149 had measured them only at 1920.
It is a measurement, not an answering-path change.

How
---
The ensembles are the declared ones (:func:`deep_hole_escalation.emissions`)
at the centres and seeds of :func:`deep_hole_failures.plan` (54 of them: the
ten references at two seeds and the 34 query ensembles that are not a
reference's), cut at 240 starts.  A 240-start ensemble is the first 240
starts of the 1920-start one, because the offsets of a seed are drawn in
order from one sweep (:func:`deep_hole_classifier.offsets`); **P0** checks
this seed by seed.  The ten references and the 44 queries are profiled under
``L5`` (:func:`configuration_reading.configuration_profile`) and read by the
same answer rule (:func:`configuration_classifier.classify_queries`) with the
certified radii of the 240-start reference table.

The marks (§4): **P0** the prefix property for every seed the ensembles use;
**W1** 0 of the 44 answered wrongly at 240 starts; **R1** every query inside
its own type's certified radius at 240 starts answered.  Reported without a
threshold: the seed queries named as themselves, and the counts correct,
refused, inside their radius and the absences, beside the 1920-start figures
(read from the stored :mod:`configuration_queries` profiles).

Cost: :func:`deep_hole_failures.plan` (a few minutes, it re-certifies the
transformed holes) and 54 ensembles of 240 starts (about nine seconds each),
run over ``workers`` processes.  So the measurement is stored beside the
digest of its sources (``tools l5-first-budget --write [--jobs N]``).

Exactness
---------
Integers and :class:`fractions.Fraction` only.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from
``studies/L5_FIRST_BUDGET_STUDY.md`` (§0 How, §4 marks, §7 results),
``MASTER_PLAN.md`` Phase 152 and the CLI handler ``tools l5-first-budget``
(the report keys it prints).  The earlier stand-in of 29 October 2026
returned all marks False without measuring.*

Last altered 31 October 2026 (repository check: the measurement made
genuine).
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import deep_hole_escalation as de

__all__ = [
    "DATA_PATH", "_SOURCES", "STARTS", "FULL_STARTS", "p0_prefix",
    "profiles_at", "summarise", "reading_at", "at_full", "compute",
    "measure", "write_measurements", "measurements", "state", "current",
    "module_digest", "l5_first_budget_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "l5_first_budget.json"

#: The first (classifier) round's budget.
STARTS: int = 240

#: The budget the 44 queries were profiled at (configuration_queries.STARTS).
FULL_STARTS: int = 1920

_SOURCES: Tuple[str, ...] = (
    "reasoning/l5_first_budget.py",
    "reasoning/configuration_classifier.py",
    "reasoning/configuration_reading.py",
    "reasoning/configuration_queries.py",
    "reasoning/deep_hole_failures.py",
) + tuple(de._SOURCES)

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


# ═════════════════════════════════════════════════════════════════════════
# P0 -- the prefix property
# ═════════════════════════════════════════════════════════════════════════

def p0_prefix(seeds: Sequence[int]) -> Dict[str, object]:
    """For every seed, are the 240 offsets the first 240 of the 1920?"""
    from . import deep_hole_classifier as dhc
    rows = []
    for seed in sorted(set(int(s) for s in seeds)):
        short = dhc.offsets(seed, STARTS)
        full = dhc.offsets(seed, FULL_STARTS)
        rows.append({"seed": seed, "prefix": tuple(full[:STARTS]) == short})
    return {"seeds": len(rows), "prefix": sum(1 for r in rows if r["prefix"]),
            "rows": rows}


# ═════════════════════════════════════════════════════════════════════════
# The 240-start profiles
# ═════════════════════════════════════════════════════════════════════════

def _profile(item: Tuple[Tuple[Fraction, ...], int, int]) -> object:
    """One ensemble's ``L5`` profile, as a worker computes it (top level, so
    it is picklable)."""
    from . import configuration_reading as cr
    centre, seed, starts = item
    return cr.configuration_profile(
        de.emissions(tuple(centre), int(seed), int(starts)))


def profiles_at(keys: Sequence[Tuple[Tuple[Fraction, ...], int]],
                starts: int = STARTS, workers: int = 4
                ) -> Dict[Tuple[Tuple[Fraction, ...], int], object]:
    """The ``L5`` profile of every ``(centre, seed)`` at ``starts``."""
    items = [(tuple(c), int(s), int(starts)) for c, s in keys]
    out: Dict[Tuple[Tuple[Fraction, ...], int], object] = {}
    if workers and workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=int(workers)) as pool:
            for (c, s, _n), prof in zip(items, pool.map(_profile, items)):
                out[(c, s)] = prof
        return out
    for item in items:
        out[(item[0], item[1])] = _profile(item)
    return out


# ═════════════════════════════════════════════════════════════════════════
# The reading
# ═════════════════════════════════════════════════════════════════════════

def summarise(run: Dict[str, object]) -> Dict[str, object]:
    """The counts the study reports, from a
    :func:`configuration_classifier.classify_queries` run."""
    rows = list(run["rows"])
    seed = [r for r in rows if r["kind"] == "seed"]
    within = [r for r in rows if r["within_own_radius"]]
    return {
        "queries": len(rows),
        "seed_queries": len(seed),
        "seed_correct": sum(1 for r in seed if r["verdict"] == "correct"),
        "correct": sum(1 for r in rows if r["verdict"] == "correct"),
        "wrong": sum(1 for r in rows if r["verdict"] == "wrong"),
        "refused": sum(1 for r in rows if r["verdict"] == "refused"),
        "nearest_correct": sum(1 for r in rows if r["nearest_correct"]),
        "within_radius": len(within),
        "within_answered": sum(1 for r in within if r["answer"] is not None),
        "absences": sum(int(r["absences"]) for r in rows),
        "false_absences": sum(1 for r in rows if r["false_absence"]),
        "refused_queries": [{"query": r["query"], "truth": r["truth"],
                             "nearest": r["nearest"],
                             "own_distance": r["own_distance"],
                             "own_radius": r["own_radius"]}
                            for r in rows if r["verdict"] == "refused"],
        "wrong_queries": [r["query"] for r in rows
                          if r["verdict"] == "wrong"],
        "false_absence_queries": [r["query"] for r in rows
                                  if r["false_absence"]],
    }


def reading_at(layout: Dict[str, object],
               profiles: Dict[Tuple[Tuple[Fraction, ...], int], object],
               joint: Optional[Dict[str, bool]] = None
               ) -> Tuple[Dict[str, object], Dict[str, object]]:
    """The 44 queries read against the reference table built from
    ``profiles``: ``(summary, classify_queries run)``."""
    from . import configuration_classifier as cc
    joint = joint or {}
    table = tuple((str(label), profiles[(tuple(centre), de.REFERENCE_SEED)])
                  for label, centre in layout["references"])
    queries = []
    for q in layout["queries"]:
        if not q.get("used"):
            continue
        queries.append({
            "name": str(q["name"]), "used": True, "truth": str(q["truth"]),
            "kind": str(q["kind"]),
            "joint_correct": bool(joint.get(str(q["name"]), False)),
            "profile": profiles[(tuple(q["centre"]), int(q["seed"]))],
        })
    run = cc.classify_queries(table, {"queries": queries})
    return summarise(run), run


def at_full() -> Optional[Dict[str, object]]:
    """The 1920-start figures, from the stored query profiles."""
    from . import configuration_classifier as cc
    from . import configuration_queries as cq
    data = cq.current()
    if data is None:
        return None
    out = summarise(cc.classify_queries(cc.reference_table(data), data))
    out["starts"] = cq.STARTS
    return out


def _ensemble_check(layout: Dict[str, object],
                    profiles: Dict[Tuple[Tuple[Fraction, ...], int], object]
                    ) -> Dict[str, object]:
    """The 240-start reference profiles against the ones the stored share
    ensembles give at 240 (both seeds): the same ensembles, cut the same
    way, so they must agree."""
    from . import configuration_reading as cr
    from . import share_ensemble as se
    data = se.current()
    if data is None:
        return {"available": False}
    stored = {str(h["label"]): h for h in data["holes"]}
    checked = agree = 0
    for label, centre in layout["references"]:
        hole = stored.get(str(label))
        if hole is None:
            continue
        for role, seed in (("reference", de.REFERENCE_SEED),
                           ("sanity", de.SANITY_SEED)):
            key = (tuple(centre), seed)
            if key not in profiles:
                continue
            checked += 1
            agree += int(cr.configuration_profile(
                se.multiset(hole[role], STARTS)) == profiles[key])
    return {"available": True, "checked": checked, "agree": agree}


# ═════════════════════════════════════════════════════════════════════════
# The measurement
# ═════════════════════════════════════════════════════════════════════════

def compute(workers: int = 4) -> Dict[str, object]:
    """P0, W1, R1 and the reported counts at 240 and 1920 starts."""
    from . import configuration_queries as cq
    from . import deep_hole_failures as dhf
    layout = dhf.plan()
    keys = dhf.ensemble_keys()
    prefix = p0_prefix([s for _c, s in keys])
    profiles = profiles_at(keys, STARTS, workers)
    stored = cq.current()
    joint = ({str(q["name"]): bool(q.get("joint_correct"))
              for q in stored["queries"] if q.get("used")}
             if stored is not None else {})
    reading, _run = reading_at(layout, profiles, joint)
    reading["starts"] = STARTS
    full = at_full()
    marks = {
        "P0": prefix["seeds"] > 0 and prefix["prefix"] == prefix["seeds"],
        "W1": reading["queries"] == 44 and reading["wrong"] == 0,
        "R1": reading["within_radius"] > 0
              and reading["within_answered"] == reading["within_radius"],
    }
    return {
        "reading": reading, "prefix": prefix, "at_1920": full,
        "ensembles": len(keys),
        "ensemble_check": _ensemble_check(layout, profiles),
        "marks": marks, "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def module_digest() -> str:
    root = _HERE.parent
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure(workers: int = 4) -> Dict[str, object]:
    r = compute(workers)
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None,
                       workers: int = 4) -> Path:
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure(workers)), indent=1, sort_keys=True,
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


def l5_first_budget_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    s = state()
    return {
        "available": False,
        "reason": (f"the stored measurement is {s['verdict']}; re-take it "
                   f"with python3 -m glm_universal.tools l5-first-budget "
                   f"--write"),
    }
