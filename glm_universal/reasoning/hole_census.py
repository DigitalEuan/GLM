"""``glm_universal.reasoning.hole_census`` -- a reference centre for every one
of the 23 Niemeier types, and the configuration reading over all of them
(Phase 123, part A; lattice item 7).

The question
------------
The deep-hole rounds read ten reference holes: the two constructions and the
first twelve declared walks reach ten of the 23 Niemeier types and no more.
``studies/LATTICE_COMPLETION_STUDY.md`` §2.A declares how the other thirteen
are reached -- in three stages, each used only for what the stages before it
left unreached -- and what is then measured on them.

1. **The walk, continued.**  The declared walk seeds are
   ``20260825 + 977 i``; the first round used ``i < 12``.  Stage 1 runs
   ``i = 12, 13, ...`` in chunks of 256 until every type is reached or the
   budget of 2,048 walks is spent.  Per type the smallest ``i`` is the
   reference.
2. **The cycle construction**, for a type with an ``A_n`` component.  Every
   component of a deep hole has the hole's Coxeter number, and only one
   Niemeier type has an ``A_n`` component, so a deep hole with an ``A~_n``
   component is that type.  ``n + 1`` lattice points with the ``A~_n`` Gram
   matrix are chosen by the declared sweep, their centroid is taken, and it is
   kept only if the frozen path certifies it.
3. **The pilot's seeds**, the walk at seeds 1000, 1001, ..., 2995 in order.

Each new reference is then run through the escalation round's ensemble at
both seeds to 7680 starts and stored as sufficient statistics, exactly as
:mod:`share_ensemble` stores the ten.  This module only takes and stores the
measurement; the configuration reading over all 23 references is read from
the store by :mod:`glm_universal.reasoning.lattice_completion`, so that the
reading can change without re-taking an hour of walks and decodes.

Exactness
---------
Integers and :class:`~fractions.Fraction`; the sweep is the package's
deterministic linear congruential sequence, never ``random``.
"""

from __future__ import annotations

import json
import os
import sys
from fractions import Fraction
from functools import lru_cache
from operator import mul
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import leech2
from . import configuration_reading as cr
from . import deep_hole_classifier as dhc
from . import deep_hole_escalation as de
from . import deep_holes as dh
from . import share_ensemble as se
from .fwht_decode import _Sweep, nearest_lattice_point_fwht

__all__ = [
    "WALK_BASE", "WALK_STRIDE", "FIRST_NEW_INDEX", "WALK_BUDGET", "CHUNK",
    "CYCLE_SEED", "CYCLE_ATTEMPTS", "PILOT_SEEDS", "SIZES", "TOP",
    "walk_seed", "a_component", "cycle_attempt", "cycle_hole",
    "census", "new_ensembles", "module_digest", "measure", "write_measurements",
    "measurements", "state", "current", "DATA_PATH",
]

#: The declared walk seeds are ``WALK_BASE + WALK_STRIDE * i``.
WALK_BASE: int = 20260825
WALK_STRIDE: int = 977
#: The first round used ``i < 12``; stage 1 continues from here.
FIRST_NEW_INDEX: int = len(dhc.WALK_SEEDS)
#: The budget of stage 1, and the chunk it is run and checked in.
WALK_BUDGET: int = 2048
CHUNK: int = 256

#: The sweep seed and attempt budget of the cycle construction (stage 2).
CYCLE_SEED: int = 20260901
CYCLE_ATTEMPTS: int = 64

#: The pilot's walk seeds (stage 3), in the order they are tried.
PILOT_SEEDS: Tuple[int, ...] = tuple(range(1000, 2996))

#: The ensemble sizes of the new holes: nested prefixes of one 7680-start run.
SIZES: Tuple[int, ...] = (240, 480, 960, 1920, 3840, 7680)
TOP: int = SIZES[-1]

Point = Tuple[int, ...]


def walk_seed(index: int) -> int:
    """The declared walk seed at index ``index``."""
    return WALK_BASE + WALK_STRIDE * index


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE THREE STAGES
# ═════════════════════════════════════════════════════════════════════════

def _walk(seed: int) -> Dict[str, object]:
    """One frozen walk; top level so that it is picklable."""
    run = dh.walked_hole(seed=seed, probes=dhc.WALK_PROBES,
                         patience=dhc.WALK_PATIENCE)
    if not run.get("reached_deep_hole") or not run.get("certified"):
        return {"seed": seed, "type": None}
    return {"seed": seed, "type": str(run["niemeier_type"]),
            "center": tuple(Fraction(x) for x in run["center"])}


def _map(function, items: Sequence, jobs: int) -> List:
    if jobs > 1 and len(items) > 1:
        try:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=jobs) as pool:
                return list(pool.map(function, items))
        except Exception:                      # pragma: no cover - fall back
            pass
    return [function(item) for item in items]


def _stage_walks(seeds: Sequence[int], missing: set, jobs: int,
                 stage: str, label_of_seed) -> Tuple[Dict[str, Dict], int]:
    """Run ``seeds`` in chunks until ``missing`` is empty; first per type."""
    found: Dict[str, Dict[str, object]] = {}
    run = 0
    for start in range(0, len(seeds), CHUNK):
        if not (missing - set(found)):
            break
        chunk = list(seeds[start:start + CHUNK])
        results = _map(_walk, chunk, jobs)
        run += len(chunk)
        for result in results:                 # results are in seed order
            label = result["type"]
            if label in missing and label not in found:
                found[label] = {"stage": stage,
                                "how": label_of_seed(result["seed"]),
                                "seed": result["seed"],
                                "center": result["center"]}
        print(f"  hole-census: {stage}, {run} walks, {len(found)} of "
              f"{len(missing)} reached", file=sys.stderr, flush=True)
    return found, run


def a_component(label: str) -> Optional[int]:
    """The rank ``n`` of the label's ``A_n`` component, if it has one."""
    for family, rank, _power in _parse(label):
        if family == "A":
            return int(rank)
    return None


def _parse(label: str) -> List[Tuple[str, int, int]]:
    import re
    return [(f, int(r), int(p or 1))
            for f, r, p in re.findall(r"([ADE])_(\d+)(?:\^(\d+))?", label)]


@lru_cache(maxsize=1)
def _minimal() -> Tuple[Point, ...]:
    return tuple(tuple(int(x) for x in v) for v in leech2.minimal_vectors())


def _ip(a: Sequence[int], b: Sequence[int]) -> int:
    return sum(map(mul, a, b))


def _select(conditions: Sequence[Tuple[Point, int]]) -> List[Point]:
    return [m for m in _minimal()
            if all(_ip(m, v) == t for v, t in conditions)]


def cycle_attempt(n: int, sweep: _Sweep) -> Optional[Tuple[Point, ...]]:
    """``n + 1`` Leech points with the ``A~_n`` Gram matrix, or ``None``.

    Raw squared distances (the package's ``x sqrt(8)`` scale): 48 between
    neighbours on the cycle, 32 otherwise.  ``v_0 = 0``; the ``n - 2`` points
    not adjacent to it are minimal vectors chosen in turn (inner product 8
    with the previous one, 16 with the earlier ones); each neighbour of
    ``v_0`` is a chosen point plus a minimal vector with the inner products
    its distances force, and the two neighbours must be at squared distance 32.
    """
    if n < 4:
        return None
    chain: List[Point] = []
    pool = _minimal()
    chain.append(pool[sweep.below(len(pool))])
    while len(chain) < n - 2:
        candidates = _select([(chain[-1], 8)] + [(u, 16) for u in chain[:-1]])
        if not candidates:
            return None
        chain.append(candidates[sweep.below(len(candidates))])
    length = len(chain)
    ends: List[List[Point]] = []
    for first in (True, False):
        base = chain[1] if first else chain[length - 2]
        adjacent = 0 if first else length - 1
        want = [16 if j == adjacent else 24 for j in range(length)]
        steps = _select([(chain[j], want[j] - _ip(base, chain[j]))
                         for j in range(length)])
        ends.append([tuple(b + s for b, s in zip(base, step))
                     for step in steps])
    pairs = [(a, b) for a in ends[0] for b in ends[1] if _ip(a, b) == 32]
    if not pairs:
        return None
    left, right = pairs[sweep.below(len(pairs))]
    return ((0,) * 24, left) + tuple(chain) + (right,)


def cycle_hole(label: str, attempts: int = CYCLE_ATTEMPTS
               ) -> Optional[Dict[str, object]]:
    """Stage 2 for one label: the first certified centroid, or ``None``."""
    n = a_component(label)
    if n is None:
        return None
    sweep = _Sweep(CYCLE_SEED + n)
    for attempt in range(attempts):
        points = cycle_attempt(n, sweep)
        if points is None:
            continue
        total = [sum(column) for column in zip(*points)]
        centre = tuple(Fraction(x, n + 1) for x in total)
        nearest = nearest_lattice_point_fwht(list(centre)).point
        distance = sum((Fraction(p) - c) ** 2 for p, c in zip(nearest, centre))
        if distance != 16:                     # raw covering radius squared
            continue
        reading = dh.classify_carrier(centre, probes=400,
                                      seed=dhc.REFERENCE_SEED, patience=60)
        if reading["certified"] and reading["niemeier_type"] == label:
            return {"stage": "cycle", "how": f"cycle construction, attempt "
                    f"{attempt} at sweep seed {CYCLE_SEED + n}",
                    "attempt": attempt, "center": centre}
    return None


def _certify(entry: Dict[str, object]) -> Dict[str, object]:
    """The frozen path's certificate and vertex set at a reference centre."""
    reading = dh.classify_carrier(entry["center"], probes=400,
                                  seed=dhc.REFERENCE_SEED, patience=60)
    out = dict(entry)
    out.update({"type": reading["niemeier_type"],
                "certified": bool(reading["certified"]),
                "vertices": tuple(tuple(int(x) for x in v)
                                  for v in reading["probe"]["vertices"]),
                "vertex_count": int(reading["probe"]["vertex_count"])})
    return out


def census(jobs: Optional[int] = None) -> Dict[str, object]:
    """The three stages, run in order for the types the ten do not cover."""
    workers = jobs if jobs is not None else (os.cpu_count() or 1)
    old = [str(e["type"]) for e in de.reference_entries()[0]]
    missing = set(cr.NIEMEIER_TYPES) - set(old)
    found: Dict[str, Dict[str, object]] = {}
    walk_seeds = [walk_seed(i) for i in range(FIRST_NEW_INDEX,
                                              FIRST_NEW_INDEX + WALK_BUDGET)]
    stage1, walks_run = _stage_walks(
        walk_seeds, set(missing), workers, "walk",
        lambda s: f"declared walk i = {(s - WALK_BASE) // WALK_STRIDE}")
    found.update(stage1)
    cycles_tried: List[str] = []
    for label in sorted(missing - set(found), key=cr.NIEMEIER_TYPES.index):
        if a_component(label) is None:
            continue
        cycles_tried.append(label)
        hit = cycle_hole(label)
        if hit is not None:
            found[label] = hit
    pilot_run = 0
    left = missing - set(found)
    if left:
        stage3, pilot_run = _stage_walks(
            PILOT_SEEDS, set(left), workers, "pilot",
            lambda s: f"pilot walk seed {s}")
        found.update(stage3)
    entries = [_certify(found[label]) for label in cr.NIEMEIER_TYPES
               if label in found]
    return {"old": tuple(old), "missing": tuple(sorted(missing,
                                                       key=cr.NIEMEIER_TYPES.index)),
            "entries": tuple(entries), "walks_run": walks_run,
            "cycles_tried": tuple(cycles_tried), "pilot_walks_run": pilot_run,
            "unreached": tuple(label for label in cr.NIEMEIER_TYPES
                               if label in missing and label not in found)}


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE ENSEMBLES OF THE NEW HOLES
# ═════════════════════════════════════════════════════════════════════════

def _run(item: Tuple[str, str, Tuple[Fraction, ...], int, int]
         ) -> Tuple[str, str, Dict[str, object]]:
    label, role, centre, seed, top = item
    record = de.emissions(tuple(centre), int(seed), int(top))
    print(f"  hole-census: {label} at the {role} seed, {top} starts done",
          file=sys.stderr, flush=True)
    return label, role, se.summarise(record, SIZES)


def new_ensembles(entries: Sequence[Dict[str, object]], top: int = TOP,
                  jobs: Optional[int] = None) -> Tuple[Dict[str, object], ...]:
    """Every new reference at both seeds to ``top`` starts, summarised."""
    workers = jobs if jobs is not None else (os.cpu_count() or 1)
    items = [(str(e["type"]), role, tuple(e["center"]), seed, top)
             for e in entries for role, seed in se.SEEDS]
    results = _map(_run, items, workers)
    by_key = {(label, role): summary for label, role, summary in results}
    return tuple({"label": str(e["type"]),
                  "reference": by_key[(str(e["type"]), "reference")],
                  "sanity": by_key[(str(e["type"]), "sanity")]}
                 for e in entries)


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "hole_census.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/hole_census.py", "reasoning/deep_holes.py",
    "reasoning/voronoi_walk.py", "reasoning/deep_hole_classifier.py",
) + tuple(se._SOURCES)


def module_digest() -> str:
    """One digest over the sources the census and its ensembles came from."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    return integrity.tree_digest([root / name for name in names], root)


def measure(jobs: Optional[int] = None) -> Dict[str, object]:
    """The census and the ensembles of what it reached."""
    found = census(jobs)
    certified = [e for e in found["entries"] if e["certified"]]
    holes = new_ensembles(certified, TOP, jobs)
    return {"census": found, "holes": holes, "sizes": SIZES, "top": TOP,
            "seeds": {role: seed for role, seed in se.SEEDS},
            "source_digest": module_digest()}


def write_measurements(path: Optional[Path] = None,
                       jobs: Optional[int] = None) -> Path:
    """Take the census and the ensembles and store them beside the digest."""
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
    """The census if it still describes the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
