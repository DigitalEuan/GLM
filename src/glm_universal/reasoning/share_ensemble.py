"""``glm_universal.reasoning.share_ensemble`` -- the deep-hole ensembles of the
escalation ladder, extended to 30720 starts and stored as sufficient
statistics (Phase 121, lattice item 6).

Why a separate module
---------------------
``studies/SHARE_SEPARATION_STUDY.md`` asks whether a share-carrying rung of
the deep-hole ladder (``L2`` or ``L4`` of
:mod:`glm_universal.reasoning.deep_hole_escalation`) reaches the separation
criterion ``rho = 2W/B < 1`` once the ensemble is larger than the ladder's top
rung of 1920 starts.  Answering it needs ``2 x 10 x 30720 = 614,400`` exact
nearest-Leech-point decodes -- about four hours on one core.  That cost
belongs to the *ensemble*, not to the readings applied to it, so it lives here
alone and is guarded by the digest of exactly the code that emits it: this
file and the escalation ladder's own sources.  The readings, the report and
the bound are in :mod:`glm_universal.reasoning.share_separation`, which reads
the stored statistics and can change without re-taking them.

What is stored
--------------
For each of the ten reference holes and each of the two seeds (the reference
seed and the sanity seed, exactly the ladder's), the ensemble is run by
:func:`deep_hole_escalation.emissions` unchanged.  The declared sweep emits
its starts in a fixed order, so the ensemble of every smaller size is a
prefix of the 30720-start one.  What is kept is, for every prefix size in
:data:`SIZES`, the multiset of ``(emitted point, exact squared distance)``
pairs: a table of the distinct pairs in first-seen order and, per size, the
count of each.  Every reading of the ladder is a function of that multiset,
and so is the vertex-matched shift the bound is about, so nothing a reading
needs is discarded.

Exactness
---------
Integers and :class:`~fractions.Fraction` only.  The pool of worker processes
changes how long the run takes and nothing else: the ensemble is a declared
deterministic sweep.
"""

from __future__ import annotations

import json
import os
import sys
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import deep_hole_escalation as de

__all__ = [
    "SIZES", "EXTENSION_SIZES", "TOP", "SEEDS", "summarise", "ensembles",
    "multiset", "module_digest", "measure", "write_measurements",
    "measurements", "state", "current", "DATA_PATH",
]

#: The extension rungs declared in the pre-registration, beyond the ladder.
EXTENSION_SIZES: Tuple[int, ...] = (3840, 7680, 15360, 30720)

#: Every prefix size the statistics are kept at: the ladder's four, then the
#: extension.  Nested, so one run at the top supplies every size.
SIZES: Tuple[int, ...] = tuple(de.STARTS_LADDER) + EXTENSION_SIZES

#: The size actually run.
TOP: int = SIZES[-1]

#: The two seeds, in the ladder's roles.
SEEDS: Tuple[Tuple[str, int], ...] = (("reference", de.REFERENCE_SEED),
                                      ("sanity", de.SANITY_SEED))

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "share_ensemble.json")


# ═════════════════════════════════════════════════════════════════════════
# 1.  ONE ENSEMBLE, SUMMARISED
# ═════════════════════════════════════════════════════════════════════════

def summarise(record: Sequence[Tuple[Tuple[int, ...], Fraction]],
              sizes: Sequence[int] = SIZES) -> Dict[str, object]:
    """The sufficient statistics of one emission record at every prefix size.

    ``table`` lists the distinct ``(point, distance)`` pairs in the order the
    record first reaches them; ``counts[str(n)]`` gives, for the first ``n``
    starts, the count of each table entry (zero-padded to the table).
    """
    index: Dict[Tuple[Tuple[int, ...], Fraction], int] = {}
    table: List[Tuple[Tuple[int, ...], Fraction]] = []
    running: List[int] = []
    counts: Dict[str, Tuple[int, ...]] = {}
    wanted = sorted(set(int(n) for n in sizes))
    position = 0
    for n in wanted:
        while position < min(n, len(record)):
            point, distance = record[position]
            key = (tuple(int(x) for x in point), Fraction(distance))
            slot = index.get(key)
            if slot is None:
                slot = len(table)
                index[key] = slot
                table.append(key)
                running.append(0)
            running[slot] += 1
            position += 1
        counts[str(n)] = tuple(running)
    return {"table": tuple(table), "counts": counts,
            "length": len(record)}


def multiset(summary: Dict[str, object], starts: int
             ) -> Tuple[Tuple[Tuple[int, ...], Fraction, int], ...]:
    """``(point, distance, count)`` for the first ``starts`` starts, from a
    stored summary; entries with count zero are left out."""
    table = summary["table"]
    counts = summary["counts"][str(starts)]
    out = []
    for slot, count in enumerate(counts):
        if count:
            point, distance = table[slot]
            out.append((tuple(int(x) for x in point), Fraction(distance),
                        int(count)))
    return tuple(out)


def _run(item: Tuple[str, str, Tuple[Fraction, ...], int, int]
         ) -> Tuple[str, str, Dict[str, object]]:
    label, role, centre, seed, top = item
    record = de.emissions(tuple(centre), int(seed), int(top))
    print(f"  share-ensemble: {label} at the {role} seed, {top} starts done",
          file=sys.stderr, flush=True)
    return label, role, summarise(record)


def ensembles(top: int = TOP, jobs: Optional[int] = None
              ) -> Tuple[Dict[str, object], ...]:
    """Run every reference hole at both seeds to ``top`` starts.

    One row per hole, in the ladder's reference order, with the summary of
    each seed's record.
    """
    entries, _siblings = de.reference_entries()
    items = []
    for entry in entries:
        centre = tuple(Fraction(x) for x in entry["center"])
        for role, seed in SEEDS:
            items.append((str(entry["type"]), role, centre, seed, top))
    workers = jobs if jobs is not None else (os.cpu_count() or 1)
    results: List[Tuple[str, str, Dict[str, object]]] = []
    if workers > 1:
        try:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=workers) as pool:
                results = list(pool.map(_run, items))
        except Exception:                  # pragma: no cover - fall back
            results = [_run(item) for item in items]
    else:
        results = [_run(item) for item in items]
    by_key = {(label, role): summary for label, role, summary in results}
    rows = []
    for entry in entries:
        label = str(entry["type"])
        rows.append({"label": label,
                     "reference": by_key[(label, "reference")],
                     "sanity": by_key[(label, "sanity")]})
    return tuple(rows)


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

#: This file and the sources the ladder's ensemble is emitted by (D4).
_SOURCES: Tuple[str, ...] = ("reasoning/share_ensemble.py",) + tuple(
    de._SOURCES)


def module_digest() -> str:
    """One digest over the sources the ensembles are emitted by."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def _thaw(value: object) -> object:
    if isinstance(value, dict):
        if set(value) == {"__fraction__"}:
            return Fraction(str(value["__fraction__"]))
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(_thaw(item) for item in value)
    return value


def measure(jobs: Optional[int] = None) -> Dict[str, object]:
    """The ensembles, with the digest of what emitted them beside them."""
    return {"sizes": SIZES, "extension": EXTENSION_SIZES, "top": TOP,
            "seeds": {role: seed for role, seed in SEEDS},
            "holes": ensembles(TOP, jobs),
            "source_digest": module_digest()}


def write_measurements(path: Optional[Path] = None,
                       jobs: Optional[int] = None) -> Path:
    """Take the ensembles and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure(jobs)), sort_keys=True,
                   ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = _thaw(json.loads(DATA_PATH.read_text(encoding="utf-8")))
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
    """The ensembles if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
