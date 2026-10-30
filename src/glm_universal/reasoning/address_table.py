"""``glm_universal.reasoning.address_table`` -- the stored table the address
read answers from (Phase 143).

``studies/ADDRESS_READ_STUDY.md`` section 2.1.  For every rung of the ladder
Phase 129 measured and every cell one of the 142 declared carriers falls in,
the table holds either the one carrier of the cell and the cell's placement
radius

    ``rho_p^2 = min over k != i of |c_k - p|^2``

(:func:`glm_universal.reasoning.placement_guard.radii`), or the several
carriers that share the cell.  Computing it takes about three quarters of a
minute, so a query cannot; it is computed once and stored.

Kept beside the digest of what it came from (directive D4)
----------------------------------------------------------
The table is stored with three digests:

* ``source_digest`` -- the quantisers and the guard the cells depend on, and
  this module;
* ``carriers_digest`` -- the names and the exact coordinates of the carriers;
* ``content_digest`` -- the table itself.

:func:`current` returns the table only when all three hold against what is
live.  ``RequestProject/GLM/AddressRead.lean`` proves the read sound on a
*sound* table -- every stored radius at most the distance from the centre to
every other carrier -- and the digests are what make the stored table the one
that was computed sound: a moved carrier, a changed quantiser or an edited
entry each make it unusable rather than wrong.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout; radii are stored as
``"n/d"`` strings.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import cell_guard as CG
from . import ladder_escalation as LE
from . import placement_guard as PG

__all__ = [
    "LADDER", "DATA_PATH", "carriers", "carriers_digest", "content_digest",
    "build", "module_digest", "measure", "write_measurements",
    "measurements", "state", "current", "parse",
]

#: The ladder the table covers: the one Phase 129 measured.
LADDER: Tuple[str, ...] = PG.LADDER

Carrier = Tuple[str, str, Tuple[Fraction, ...]]
Point = Tuple[int, ...]

_carriers: Optional[Tuple[Carrier, ...]] = None


def carriers(refresh: bool = False) -> Tuple[Carrier, ...]:
    """The 142 declared carriers, ``(register, name, coordinates)``."""
    global _carriers
    if _carriers is None or refresh:
        _carriers = tuple(LE.sample_carriers())
    return _carriers


def _q(value: Fraction) -> str:
    value = Fraction(value)
    return f"{value.numerator}/{value.denominator}"


def carriers_digest(rows: Sequence[Carrier]) -> str:
    """SHA-256 over the carriers' registers, names and exact coordinates."""
    canon = [[register, name, [_q(x) for x in coords]]
             for register, name, coords in rows]
    return integrity.sha256_hex(json.dumps(canon, separators=(",", ":"))
                                .encode("utf-8"))


def content_digest(stored: Dict[str, object]) -> str:
    """SHA-256 over the table proper: the ladder, the carriers' names and the
    rungs' entries."""
    body = {key: stored.get(key) for key in ("ladder", "carriers", "rungs")}
    return integrity.sha256_hex(json.dumps(body, sort_keys=True,
                                           separators=(",", ":"))
                                .encode("utf-8"))


def build(rows: Optional[Sequence[Carrier]] = None) -> Dict[str, object]:
    """The table, computed from the carriers (about 45 seconds)."""
    rows = tuple(rows) if rows is not None else carriers()
    rungs: Dict[str, Dict[str, list]] = {}
    for rung in LADDER:
        index = CG._index(rung, rows)
        rads = PG.radii(rung, rows, index)
        single = sorted([list(point), members[0], _q(rads[point])]
                        for point, members in index.items()
                        if len(members) == 1)
        shared = sorted([list(point), list(members)]
                        for point, members in index.items()
                        if len(members) > 1)
        rungs[rung] = {"single": single, "shared": shared}
    table: Dict[str, object] = {
        "ladder": list(LADDER),
        "carriers": [[register, name] for register, name, _c in rows],
        "rungs": rungs,
    }
    table["carriers_digest"] = carriers_digest(rows)
    table["content_digest"] = content_digest(table)
    return table


def parse(stored: Dict[str, object]
          ) -> Dict[str, Dict[Point, Tuple[str, object]]]:
    """``rung -> point -> ("single", (i, rho2))`` or ``("shared", members)``."""
    out: Dict[str, Dict[Point, Tuple[str, object]]] = {}
    for rung, entries in dict(stored["rungs"]).items():   # type: ignore[arg-type]
        cells: Dict[Point, Tuple[str, object]] = {}
        for point, i, rho2 in entries["single"]:
            cells[tuple(point)] = ("single", (int(i), Fraction(rho2)))
        for point, members in entries["shared"]:
            cells[tuple(point)] = ("shared", tuple(int(m) for m in members))
        out[rung] = cells
    return out


# ═════════════════════════════════════════════════════════════════════════
# THE CACHE, GUARDED BY THREE DIGESTS
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "address_table.json")

_SOURCES: Tuple[str, ...] = ("reasoning/address_table.py",) + tuple(
    PG._SOURCES)


def module_digest() -> str:
    """One digest over the sources the table's cells and radii depend on."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    return integrity.tree_digest([root / name for name in names], root)


def measure() -> Dict[str, object]:
    """The table, recomputed, with its source digest."""
    table = build()
    table["source_digest"] = module_digest()
    return table


def write_measurements(path: Optional[Path] = None) -> Path:
    """Compute the table and store it beside its digests."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(measure(), indent=0, sort_keys=True)
                      + "\n", encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False, path: Optional[Path] = None
                 ) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current; ``None`` if the
    file is absent or does not parse."""
    global _cache
    if path is None and _cache is not None and not refresh:
        return _cache
    target = Path(path) if path is not None else DATA_PATH
    if not target.exists():
        return None
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except ValueError:
        return None
    loaded = loaded if isinstance(loaded, dict) else None
    if path is None:
        _cache = loaded
    return loaded


def state(stored: Optional[Dict[str, object]] = None,
          rows: Optional[Sequence[Carrier]] = None) -> Dict[str, object]:
    """Which of the three digests hold.  ``verdict`` is ``absent``,
    ``fresh`` or ``stale``; ``failed`` names the digests that do not hold."""
    stored = stored if stored is not None else measurements()
    if stored is None:
        return {"present": False, "fresh": False, "failed": ("absent",),
                "verdict": "absent"}
    rows = rows if rows is not None else carriers()
    failed: List[str] = []
    if stored.get("source_digest") != module_digest():
        failed.append("source")
    if stored.get("carriers_digest") != carriers_digest(rows):
        failed.append("carriers")
    try:
        same = stored.get("content_digest") == content_digest(stored)
    except (TypeError, ValueError):
        same = False
    if not same:
        failed.append("content")
    if list(stored.get("ladder") or ()) != list(LADDER):
        failed.append("ladder")
    return {"present": True, "fresh": not failed, "failed": tuple(failed),
            "verdict": "fresh" if not failed else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The stored table if all three digests hold, else ``None``."""
    stored = measurements()
    if stored is None or not state(stored)["fresh"]:
        return None
    return stored
