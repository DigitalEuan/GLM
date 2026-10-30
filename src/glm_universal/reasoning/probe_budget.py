"""``glm_universal.reasoning.probe_budget`` -- a stopping rule for the
certifying reading of a deep hole (Phase 124).

``studies/PROBE_BUDGET_STUDY.md`` pre-registered the rule and six marks.  The
census of Phase 123 certified a reference centre with the first round's
convention -- at most 400 modulator starts, stopping after 60 barren starts --
and three of its thirteen new centres were left uncertified because the probe
stopped before it had seen the last vertex.

The rule
--------
No barren stop, and a budget of :data:`BUDGET` starts: the reading stops on
the completeness certificate (which :func:`deep_holes.hole_vertices` already
checks after every new vertex) or after the budget, whichever is first.  The
budget is the one `GLM.ProbeBudget.budget_serves_every_type` proves enough
under the model of independent starts in which every vertex of a hole with
``k`` vertices has share at least ``1/(2k)``: the union bound on an unseen
vertex is then at most ``1/1000`` for every Niemeier type.

What is measured
----------------
* :func:`share_check` -- the model's hypothesis (P2): every arrival share of
  every reference hole, at both ensemble seeds and 7680 starts, is at least
  ``1/(2k)``, read from the stored ensembles;
* :func:`reference_rows` -- the 23 reference centres read under the rule
  (P3, P6);
* :func:`heldout_rows` -- the declared held-out walks, each centre that is a
  deep hole read under the rule and under the census convention (P4, P5, P6).

Exactness
---------
Integers and :class:`~fractions.Fraction` only.
"""

from __future__ import annotations

import json
import os
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import configuration_reading as cr
from . import deep_hole_classifier as dhc
from . import deep_hole_escalation as de
from . import deep_holes as dh
from . import hole_census as hc
from . import patience_census as pc
from . import share_ensemble as se

__all__ = [
    "BUDGET", "SHARE_CONSTANT", "CENSUS_PROBES", "CENSUS_PATIENCE",
    "HELDOUT_INDICES", "LEAN_MODULE", "read_by_rule", "read_by_census",
    "share_check", "reference_rows", "heldout_rows", "module_digest",
    "measure", "write_measurements", "measurements", "state", "current",
    "probe_budget_report", "DATA_PATH",
]

#: The budget, proved enough for every type by `GLM.ProbeBudget`.
BUDGET: int = 1056
#: The declared floor on ``k * p_min`` the budget is proved under.
SHARE_CONSTANT: Fraction = Fraction(1, 2)
#: The census convention the rule replaces.
CENSUS_PROBES: int = 400
CENSUS_PATIENCE: int = 60
#: The held-out walks: declared walk indices 3000 ... 3255.
HELDOUT_INDICES: Tuple[int, ...] = tuple(range(3000, 3256))
#: The Lean file of the round.
LEAN_MODULE: str = "RequestProject/GLM/ProbeBudget.lean"


def _reading(centre: Sequence, probes: int, patience: int) -> Dict[str, object]:
    reading = dh.classify_carrier(tuple(Fraction(x) for x in centre),
                                  probes=probes, seed=dhc.REFERENCE_SEED,
                                  patience=patience)
    probe = reading["probe"]
    return {
        "type": reading["niemeier_type"],
        "certified": bool(reading["certified"]),
        "starts_run": int(probe.get("starts_run") or 0),
        "vertex_count": int(probe["vertex_count"]),
        "vertices": tuple(tuple(int(x) for x in v) for v in probe["vertices"]),
        "budget_reached": int(probe.get("starts_run") or 0) >= probes,
    }


def read_by_rule(centre: Sequence) -> Dict[str, object]:
    """The rule: no barren stop, :data:`BUDGET` starts at most."""
    return _reading(centre, BUDGET, BUDGET)


def read_by_census(centre: Sequence) -> Dict[str, object]:
    """The census convention: 400 starts, stopping after 60 barren ones."""
    return _reading(centre, CENSUS_PROBES, CENSUS_PATIENCE)


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE MODEL'S HYPOTHESIS (P2)
# ═════════════════════════════════════════════════════════════════════════

def _hole_records() -> List[Tuple[str, object, object]]:
    rows: List[Tuple[str, object, object]] = []
    for data in (se.current(), hc.current(), pc.current()):
        if data is None:
            continue
        for hole in data["holes"]:
            rows.append((str(hole["label"]), hole["reference"],
                         hole["sanity"]))
    return rows


def share_check(starts: int = hc.TOP) -> Dict[str, object]:
    """Every arrival share against ``1/(2k)``, both seeds, every hole."""
    rows = []
    for label, reference, sanity in _hole_records():
        for role, record in (("reference", reference), ("sanity", sanity)):
            shares, _r2 = cr.arrivals(se.multiset(record, starts))
            k = len(shares)
            total = sum(shares.values())
            smallest = Fraction(min(shares.values()), total)
            rows.append({"label": label, "seed": role, "vertices": k,
                         "k_times_min_share": k * smallest,
                         "holds": k * smallest >= SHARE_CONSTANT})
    least = min((r["k_times_min_share"] for r in rows), default=None)
    return {"rows": tuple(rows), "holes": len({r["label"] for r in rows}),
            "least": least,
            "holds": bool(rows) and all(r["holds"] for r in rows)}


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE READINGS (P3 -- P6)
# ═════════════════════════════════════════════════════════════════════════

def _reference_centres() -> List[Dict[str, object]]:
    """The 23 reference centres with their recorded type and vertex set."""
    out: List[Dict[str, object]] = []
    for entry in de.reference_entries()[0]:
        out.append({"label": str(entry["type"]), "centre": entry["center"],
                    "vertices": tuple(tuple(int(x) for x in v)
                                      for v in entry["vertices"])})
    census = hc.current()
    if census is not None:
        for entry in census["census"]["entries"]:
            if entry["certified"]:
                out.append({"label": str(entry["type"]),
                            "centre": entry["center"],
                            "vertices": tuple(tuple(int(x) for x in v)
                                              for v in entry["vertices"])})
    extra = pc.current()
    if extra is not None:
        for entry in extra["entries"]:
            if entry["certified"]:
                out.append({"label": str(entry["type"]),
                            "centre": entry["center"],
                            "vertices": tuple(tuple(int(x) for x in v)
                                              for v in entry["vertices"])})
    return out


def _reference_one(item: Dict[str, object]) -> Dict[str, object]:
    reading = read_by_rule(item["centre"])
    return {"label": item["label"], "type": reading["type"],
            "certified": reading["certified"],
            "same_type": reading["type"] == item["label"],
            "same_vertices": (sorted(reading["vertices"])
                              == sorted(item["vertices"])),
            "starts_run": reading["starts_run"],
            "budget_reached": reading["budget_reached"]}


def reference_rows(jobs: int = 1) -> Tuple[Dict[str, object], ...]:
    """P3: every reference centre under the rule."""
    return tuple(hc._map(_reference_one, _reference_centres(), jobs))


def _heldout_one(index: int) -> Dict[str, object]:
    seed = hc.walk_seed(index)
    run = dh.walked_hole(seed=seed, probes=dhc.WALK_PROBES,
                         patience=dhc.WALK_PATIENCE)
    row: Dict[str, object] = {
        "index": index, "seed": seed,
        "reached_deep_hole": bool(run.get("reached_deep_hole")),
        "walk_type": run.get("niemeier_type"),
        "walk_certified": bool(run.get("certified")),
    }
    if not row["reached_deep_hole"]:
        return row
    centre = tuple(Fraction(x) for x in run["center"])
    rule = read_by_rule(centre)
    census = read_by_census(centre)
    row.update({
        "rule_certified": rule["certified"], "rule_type": rule["type"],
        "rule_starts": rule["starts_run"],
        "rule_vertex_count": rule["vertex_count"],
        "rule_budget_reached": rule["budget_reached"],
        "census_certified": census["certified"],
        "census_type": census["type"],
        "census_starts": census["starts_run"],
        "census_vertex_count": census["vertex_count"],
        "agree": (not census["certified"]) or (
            rule["certified"] and rule["type"] == census["type"]
            and sorted(rule["vertices"]) == sorted(census["vertices"])),
    })
    return row


def heldout_rows(jobs: int = 1) -> Tuple[Dict[str, object], ...]:
    """P4 -- P6: the held-out walks under both readings."""
    return tuple(hc._map(_heldout_one, list(HELDOUT_INDICES), jobs))


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "probe_budget.json")

_SOURCES: Tuple[str, ...] = ("reasoning/probe_budget.py",) + tuple(
    pc._SOURCES)


def module_digest() -> str:
    """One digest over the sources and the stores the readings depend on."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    paths = [root / name for name in names] + [hc.DATA_PATH, pc.DATA_PATH]
    return integrity.tree_digest(paths, root)


def measure(jobs: Optional[int] = None) -> Dict[str, object]:
    """The references and the held-out walks under the rule."""
    workers = jobs if jobs is not None else (os.cpu_count() or 1)
    return {"budget": BUDGET, "census_probes": CENSUS_PROBES,
            "census_patience": CENSUS_PATIENCE,
            "references": reference_rows(workers),
            "heldout": heldout_rows(workers),
            "source_digest": module_digest()}


def write_measurements(path: Optional[Path] = None,
                       jobs: Optional[int] = None) -> Path:
    """Take the readings and store them beside their digest."""
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
    """The readings if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE MARKS
# ═════════════════════════════════════════════════════════════════════════

def _median(values: Sequence[int]) -> Optional[Fraction]:
    ordered = sorted(values)
    if not ordered:
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return Fraction(ordered[middle])
    return Fraction(ordered[middle - 1] + ordered[middle], 2)


def probe_budget_report() -> Dict[str, object]:
    """Every mark of the round, from the store and the stored ensembles."""
    shares = share_check()
    data = current()
    if data is None:
        return {"available": False, "shares": shares, "reason": (
            "the probe-budget readings are absent or stale; re-take them "
            "with python3 -m glm_universal.tools probe-budget --write")}
    refs = data["references"]
    held = data["heldout"]
    reached = [r for r in held if r["reached_deep_hole"]]
    rule_ok = sum(1 for r in reached if r["rule_certified"])
    census_ok = sum(1 for r in reached if r["census_certified"])
    census_missed: Dict[str, int] = {}
    for r in reached:
        if not r["census_certified"] and r["rule_certified"]:
            label = str(r["rule_type"])
            census_missed[label] = census_missed.get(label, 0) + 1
    starts = ([int(r["starts_run"]) for r in refs]
              + [int(r["rule_starts"]) for r in reached])
    types = sorted({str(r["rule_type"]) for r in reached
                    if r["rule_certified"]})
    marks = {
        "P1": True,           # the build; pinned by the tests
        "P2": shares["holds"],
        "P3": (len(refs) == len(cr.NIEMEIER_TYPES)
               and all(r["certified"] and r["same_type"]
                       and r["same_vertices"] for r in refs)),
        "P4": bool(reached) and rule_ok == len(reached),
        "P5": all(r["agree"] for r in reached),
        "P6": (not any(r["budget_reached"] for r in refs)
               and not any(r["rule_budget_reached"] for r in reached)),
    }
    return {
        "available": True, "lean": LEAN_MODULE, "budget": BUDGET,
        "shares": shares, "references": refs,
        "references_certified": sum(1 for r in refs if r["certified"]
                                    and r["same_type"]
                                    and r["same_vertices"]),
        "walks": len(held), "reached": len(reached),
        "rule_certified": rule_ok, "census_certified": census_ok,
        "census_missed_by_type": census_missed,
        "types_reached": types,
        "median_starts": _median(starts), "max_starts": max(starts)
        if starts else None,
        "marks": marks, "marks_met": sum(1 for v in marks.values() if v),
    }
