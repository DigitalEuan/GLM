"""``glm_universal.reasoning.stray_blind`` -- which pairs of deep holes a
reading of distances alone must conflate (Phase 110, lattice item 10).

The question
------------
``studies/DEEP_HOLE_ESCALATION_STUDY.md`` measured that the exact rational
distance measure ``L3`` gives ``A_1^24`` and ``A_2^12`` *identical* reference
profiles: both holes emit no stray over the declared ensemble, so each measure
is a single atom at the covering radius.  ``STATUS.md`` §3.4 item 10 recorded
that as an observation and asked for the theorem that says *which* pairs such
a reading must conflate.

The answer, proved in ``RequestProject/GLM/StrayBlind.lean``
------------------------------------------------------------
Every emission is a lattice point, so none is nearer to a deep hole than the
covering radius, and the arrivals are exactly the emissions *at* it.  The
multiset of emission distances is therefore ``A`` copies of the covering
radius plus the stray spectrum (``distances_decomp``), and

* two records of the same size have the same distance profile **exactly when
  their stray spectra agree** (``distances_eq_iff``) -- the pairs ``L3`` must
  conflate are the pairs with equal stray spectra, whatever their types;
* in particular every pair of stray-free records is conflated
  (``strayFree_conflate``);
* a reading blind to strays *and* to the vertex reached sees one point mass at
  the covering radius for every hole (``arrivalMeasure_const``), so it
  conflates all of them;
* a conflated pair of references with different labels makes the separation
  criterion fail at every spread (``not_resolves_of_indist``), so the ``L3``
  rung can never reach ``rho < 1`` while the conflation persists -- the
  bearing on lattice item 6.

What this module measures
-------------------------
The theorem is a prediction about the measured ladder, and this module checks
it against the same ensembles the ladder read: at every ensemble size of
``deep_hole_escalation.STARTS_LADDER`` it computes, for the ten reference
holes,

* the minimum distance each record reaches (the theorem's hypothesis is that
  all holes share one covering radius);
* the **predicted** conflated pairs (equal stray spectra) and the **measured**
  ones (``L3`` distance exactly ``0``), which the theorem says are equal;
* the stray-free holes.

No float, no tolerance: every distance is a :class:`~fractions.Fraction`.  The
ensembles are a quarter of an hour of exact decoding, so the census is stored
beside the digest of its sources (``python3 -m glm_universal.tools stray-blind
--write`` re-takes it).
"""

from __future__ import annotations

import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import deep_hole_escalation as de

__all__ = [
    "Record", "covering_minimum", "stray_spectrum", "distance_profile",
    "predicted_pairs", "measured_pairs", "census", "reference_records",
    "stray_blind_report", "module_digest", "measure", "write_measurements",
    "measurements", "state", "current", "DATA_PATH", "LEAN_MODULE",
]

#: One emission record: ``(point, exact squared distance)`` per start.
Record = Sequence[Tuple[Tuple[int, ...], Fraction]]

#: The Lean file that proves what this module checks.
LEAN_MODULE: str = "RequestProject/GLM/StrayBlind.lean"

DATA_PATH: Path = Path(__file__).resolve().parent / "_data" / "stray_blind.json"


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE READINGS THE THEOREM IS ABOUT
# ═════════════════════════════════════════════════════════════════════════

def covering_minimum(record: Record) -> Optional[Fraction]:
    """The least squared distance the record reaches -- the covering radius
    as soon as one start arrives (``minimum_eq_radius``)."""
    if not record:
        return None
    return min(Fraction(distance) for _point, distance in record)


def stray_spectrum(record: Record, radius: Fraction
                   ) -> Tuple[Tuple[Fraction, int], ...]:
    """The stray spectrum: each distance other than ``radius`` with its
    count, sorted.  This is ``GLM.StrayBlind.strays`` as a multiset."""
    counts: Dict[Fraction, int] = {}
    for _point, distance in record:
        value = Fraction(distance)
        if value != radius:
            counts[value] = counts.get(value, 0) + 1
    return tuple(sorted(counts.items()))


def distance_profile(record: Record) -> Tuple[Tuple[Fraction, int], ...]:
    """The distance profile: every distance with its count, sorted.  This is
    ``GLM.StrayBlind.distances`` as a multiset, and what ``L3`` normalises."""
    counts: Dict[Fraction, int] = {}
    for _point, distance in record:
        value = Fraction(distance)
        counts[value] = counts.get(value, 0) + 1
    return tuple(sorted(counts.items()))


def _pairs(names: Sequence[str]) -> List[Tuple[str, str]]:
    return [(names[i], names[j]) for i in range(len(names))
            for j in range(i + 1, len(names))]


def predicted_pairs(records: Dict[str, Record], radius: Fraction
                    ) -> Tuple[Tuple[str, str], ...]:
    """The pairs the theorem says a distance-only reading must conflate:
    equal size and equal stray spectrum (``distances_eq_iff``)."""
    names = sorted(records)
    spectra = {name: stray_spectrum(records[name], radius) for name in names}
    return tuple(pair for pair in _pairs(names)
                 if len(records[pair[0]]) == len(records[pair[1]])
                 and spectra[pair[0]] == spectra[pair[1]])


def measured_pairs(records: Dict[str, Record]) -> Tuple[Tuple[str, str], ...]:
    """The pairs the ``L3`` rung actually conflates: exact Wasserstein
    distance ``0`` between the two rational profiles."""
    names = sorted(records)
    profiles = {name: de.rational_profile(records[name]) for name in names}
    return tuple(pair for pair in _pairs(names)
                 if de.wasserstein1(profiles[pair[0]], profiles[pair[1]]) == 0)


def census(records: Dict[str, Record]) -> Dict[str, object]:
    """The theorem's prediction against the measurement, for one table of
    records of one size."""
    minima = {name: covering_minimum(records[name]) for name in sorted(records)}
    values = {value for value in minima.values() if value is not None}
    common = len(values) == 1
    radius = min(values) if values else None
    predicted = predicted_pairs(records, radius) if radius is not None else ()
    measured = measured_pairs(records)
    stray_free = tuple(name for name in sorted(records)
                       if radius is not None
                       and not stray_spectrum(records[name], radius))
    return {
        "radius": radius,
        "common_radius": common,
        "minima": minima,
        "predicted": predicted,
        "measured": measured,
        "agree": predicted == measured,
        "stray_free": stray_free,
        "rho_defined": not measured,
    }


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE MEASUREMENT OVER THE LADDER'S OWN ENSEMBLES
# ═════════════════════════════════════════════════════════════════════════

def _emit(item: Tuple[Tuple[Fraction, ...], int, int]) -> Record:
    centre, seed, starts = item
    return de.emissions(tuple(centre), int(seed), int(starts))


@lru_cache(maxsize=None)
def reference_records() -> Tuple[Tuple[str, Record], ...]:
    """Each reference hole's record at the reference seed, to the top rung,
    in parallel where possible (the ensemble is deterministic, so the pool
    changes only how long this takes)."""
    entries, _siblings = de.reference_entries()
    labels = [str(entry["type"]) for entry in entries]
    items = [(tuple(Fraction(x) for x in entry["center"]), de.REFERENCE_SEED,
              de.MAX_STARTS) for entry in entries]
    records: List[Record] = []
    try:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor() as pool:
            records = list(pool.map(_emit, items))
    except Exception:                      # pragma: no cover - fall back
        records = [_emit(item) for item in items]
    return tuple(zip(labels, records))


def stray_blind_report() -> Dict[str, object]:
    """The census at every ensemble size of the ladder."""
    table = reference_records()
    rows = []
    for starts in de.STARTS_LADDER:
        records = {label: de.prefix(record, starts) for label, record in table}
        row = census(records)
        row["starts"] = starts
        row["declared"] = starts in de.DECLARED_STARTS
        rows.append(row)
    return {
        "holes": len(table),
        "rows": tuple(rows),
        "agree_everywhere": all(row["agree"] for row in rows),
        "common_radius_everywhere": all(row["common_radius"] for row in rows),
        "lean": LEAN_MODULE,
    }


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE CACHE
# ═════════════════════════════════════════════════════════════════════════

_SOURCES: Tuple[str, ...] = ("reasoning/stray_blind.py",) + tuple(
    name for name in de._SOURCES)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
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


def measure() -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it."""
    payload = dict(stray_blind_report())
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the census and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n",
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
    """The census if it still describes the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
