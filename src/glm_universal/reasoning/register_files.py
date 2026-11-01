"""``glm_universal.reasoning.register_files`` -- the session's registers as
GLM-BAT files (Phase 153).

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/CARRIED_READ_STUDY.md
(§0, §1, §5, marks R1 and R2), MASTER_PLAN.md (Phase 153) and
RequestProject/GLM/CarriedRead.lean.*

Every declared **register** table of the field surface -- the ``element``
and ``molecule`` source tables, the ITS-90 fixed points, and the carrier
attributes of the session's default domains -- is written as
``reg/<table>.txt`` (a ``:`` in a table name written ``_``), one line
``@<row>.<field>=<value>;`` per scalar entry whose key and value avoid the
delimiters ``@ = ;`` and GLM-BAT's special characters ``< > | & % " ^``.
The ``lean``, ``python`` and ``function`` tables are not registers and are
not written.

The element table is written from the frozen snapshot
(``data_objects/_data/elements_118.json``) by this module's own reader
(:func:`snapshot_element_rows`), not from the loaded register, and compared
with the loaded register entry for entry (mark R1).

``FIND "@k=v;"`` finds a line exactly when the register holds ``(k, v)``
(``GLM.CarriedRead.find_iff_mem``), and with unique keys exactly when ``v``
is the register's value at ``k`` (``find_iff_eq``) -- which is why R1 checks
that the keys are unique.

Exactness
---------
Integers, :class:`fractions.Fraction` and strings only.
"""

from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "REGISTER_KINDS", "NOT_REGISTERS", "table_path", "value_text",
    "key_ok", "entry_line", "snapshot_element_rows", "snapshot_agreement",
    "register_tables", "register_files", "table_entries",
]

#: The field-surface kinds that are registers.
REGISTER_KINDS: Tuple[str, ...] = ("source", "carrier")

#: The declared tables that are not registers (never given to the machine).
NOT_REGISTERS: Tuple[str, ...] = ("lean", "python", "function")

_SPECIAL = set('<>|&%"^@=;')

_SNAPSHOT = Path(__file__).resolve().parent.parent / "data_objects" / \
    "_data" / "elements_118.json"

_cache: Dict[Tuple[str, ...], Dict[str, object]] = {}
_default: Dict[None, Dict[str, object]] = {}


def table_path(table: str) -> str:
    """The machine file of a register table."""
    return "reg/" + table.replace(":", "_") + ".txt"


def key_ok(text: str) -> bool:
    """A row or field name a register line can carry."""
    return bool(text) and text == text.strip() and not (set(text) & _SPECIAL)


def value_text(value: object) -> Optional[str]:
    """The text of a scalar value as a register line writes it (a number
    ``n`` or ``n/d``, a string as it is), or ``None`` for a value that is
    not sayable (a tuple, a mapping, a missing value, a special
    character)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else \
            f"{value.numerator}/{value.denominator}"
    if isinstance(value, str):
        return value if key_ok(value) else None
    return None


def entry_line(row: str, field: str, value: object) -> Optional[str]:
    """``@row.field=value;`` or ``None`` when not sayable."""
    v = value_text(value)
    if v is None or not key_ok(str(row)) or not key_ok(str(field)):
        return None
    return f"@{row}.{field}={v};"


# ---------------------------------------------------------------------------
# the element snapshot, read by this module itself
# ---------------------------------------------------------------------------

_FRACTION = re.compile(r"^-?\d+/\d+$")


def snapshot_element_rows() -> Dict[str, Dict[str, object]]:
    """The element table read straight from the frozen snapshot: one row per
    symbol, every field of the register's ``Element`` record, a ``p/q``
    string read as an exact fraction and an integer kept as an integer."""
    from dataclasses import fields as dc_fields
    from ..data_objects.elements import Element
    names = [f.name for f in dc_fields(Element)]
    raw = json.loads(_SNAPSHOT.read_text(encoding="utf-8"))
    out: Dict[str, Dict[str, object]] = {}
    for rec in raw["elements"]:
        row: Dict[str, object] = {}
        for name in names:
            v = rec.get(name)
            if isinstance(v, str) and _FRACTION.match(v):
                v = Fraction(v)
            row[name] = v
        out[str(rec["symbol"])] = row
    return out


def snapshot_agreement(surface) -> Dict[str, object]:
    """The snapshot reading against the loaded element register, entry for
    entry over the scalar entries either side holds."""
    snap = snapshot_element_rows()
    loaded = surface.table_by_name("element").rows()
    pairs = agree = 0
    differ: List[str] = []
    for row in sorted(set(snap) | set(loaded)):
        a, b = snap.get(row, {}), loaded.get(row, {})
        for f in sorted(set(a) | set(b)):
            va, vb = value_text(a.get(f)), value_text(b.get(f))
            if va is None and vb is None:
                continue
            pairs += 1
            if va == vb:
                agree += 1
            else:
                differ.append(f"{row}.{f}")
    return {"pairs": pairs, "agree": agree, "differ": differ[:20]}


# ---------------------------------------------------------------------------
# the files
# ---------------------------------------------------------------------------

def register_tables(surface) -> List[object]:
    """The surface's register tables, in its priority order."""
    return [t for t in surface.tables()
            if t.kind in REGISTER_KINDS and t.name not in NOT_REGISTERS]


def table_entries(rows: Mapping[str, Mapping[str, object]]
                  ) -> Tuple[List[str], int, int]:
    """``(lines, left out, duplicated keys)`` of one table.  A field the row
    leaves empty (``None``) is no entry at all and is not counted as left
    out; *left out* counts the entries held but not sayable (a tuple, a
    mapping, a special character)."""
    lines: List[str] = []
    keys: Dict[str, int] = {}
    left = 0
    for row in rows:
        for f, v in rows[row].items():
            if v is None:
                continue
            line = entry_line(str(row), str(f), v)
            if line is None:
                left += 1
                continue
            key = line.split("=", 1)[0]
            keys[key] = keys.get(key, 0) + 1
            lines.append(line)
    dup = sum(1 for n in keys.values() if n > 1)
    return lines, left, dup


def register_files(session=None) -> Dict[str, object]:
    """Every register table as a machine file: ``{"files": {path: lines},
    "tables": [{"table", "path", "entries", "left_out", "duplicated"}],
    "snapshot": ...}``.  Cached by the session's domains."""
    if session is None:
        if None in _default:
            return _default[None]
        from ..runtime.session import GeometricSession
        session = GeometricSession()
        _default[None] = register_files(session)
        return _default[None]
    surface = session.field_surface
    key = tuple(sorted(getattr(session, "_domains", ()) or ()))
    if key in _cache:
        return _cache[key]
    files: Dict[str, Tuple[str, ...]] = {}
    tables: List[Dict[str, object]] = []
    for t in register_tables(surface):
        rows = snapshot_element_rows() if t.name == "element" else t.rows()
        lines, left, dup = table_entries(rows)
        path = table_path(t.name)
        files[path] = tuple(lines)
        tables.append({"table": t.name, "path": path, "entries": len(lines),
                       "left_out": left, "duplicated": dup})
    out = {"files": files, "tables": tables,
           "snapshot": snapshot_agreement(surface)}
    _cache[key] = out
    return out
