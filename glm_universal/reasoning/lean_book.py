"""The stored address book, read without opening the Lean development.

Why this module exists, and why it is separate
==============================================

:mod:`glm_universal.reasoning.lean_address` does two different jobs.  It
*builds* the address book, which means walking the whole Lean development and
parsing every file in it; and it *answers* from the book once it is built.
The first job is the refresh chain's; the second is the runtime's.

Keeping both in one module made every reader of either a reader of the
development.  The sign-off ledger computes a unit's closure by following
imports, and a module that walks the tree can only be recorded as depending on
all of it -- so once the runtime session reached the tree-walking module, an
edit to any one Lean file made 79 of the 98 test units stale, and a round paid
for a full release after touching a single proof.  The measurement is in
``studies/ITERATION_COST_STUDY.md`` §5e.

This module is the answering half, and it is deliberately small: it reads the
JSON the refresh chain writes and nothing else.  It opens no source of the
development, it names none, and it imports nothing that does.  A reader that
only needs what the book records therefore depends on the book, which is one
generated file, rather than on the development it was generated from.

What it does *not* do is decide whether the book is still a description of the
development: that question needs the tree, so it belongs to
:func:`glm_universal.reasoning.lean_address.cache_state` and to
``corpus --check``, which report a stale book and name the command that
rebuilds it.  The rule is the one the package already keeps for every derived
table: a reader answers from what was written, and the refresh chain is what
keeps that honest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

__all__ = ["BOOK_PATH", "book", "declaration_rows", "stored_digest",
           "schema"]

_HERE = Path(__file__).resolve()

#: The stored book.  The same file
#: :data:`glm_universal.reasoning.lean_address.DATA_PATH` names; it is spelled
#: out here so that this module imports nothing that reads the development.
BOOK_PATH = _HERE.parent / "_data" / "lean_addresses.json"

_cache: Optional[Dict[str, object]] = None


def book(refresh: bool = False) -> Optional[Dict[str, object]]:
    """The stored book as it was written, or ``None`` if it is absent."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not BOOK_PATH.exists():
        return None
    _cache = json.loads(BOOK_PATH.read_text(encoding="utf-8"))
    return _cache


def schema() -> Optional[int]:
    """The schema the stored book was written under."""
    stored = book()
    if stored is None:
        return None
    value = stored.get("schema")
    return int(value) if isinstance(value, int) else None


def stored_digest() -> Optional[str]:
    """The digest of the development the book was written from.

    Recorded, not recomputed: comparing it with the development as it stands
    means reading the development, which is what this module avoids.
    """
    stored = book()
    if stored is None:
        return None
    value = stored.get("tree_digest")
    return str(value) if value is not None else None


def declaration_rows() -> Mapping[str, Mapping[str, object]]:
    """One row per declaration: file, line, kind, namespace, statement.

    The order is the book's own -- the order the declarations occur in, file
    by file -- so a reader that lists them lists them as they are written.
    A book written under an older schema has no namespace and no statement
    stored; those rows carry the empty string rather than a guess, which is
    the same refusal the rest of the package makes when a table has not been
    rebuilt.
    """
    stored = book()
    if stored is None:
        return {}
    meta = stored.get("declarations")
    if not isinstance(meta, dict):
        return {}
    order = stored.get("order")
    names: Tuple[str, ...]
    if isinstance(order, list):
        names = tuple(str(name) for name in order if str(name) in meta)
    else:                                          # pragma: no cover
        names = tuple(sorted(str(name) for name in meta))
    out: Dict[str, Mapping[str, object]] = {}
    for name in names:
        row = meta[name]
        if not isinstance(row, dict):              # pragma: no cover
            continue
        out[name] = {
            "file": row.get("file", ""),
            "line": row.get("line", 0),
            "kind": row.get("kind", ""),
            "namespace": row.get("namespace", ""),
            "statement": row.get("statement", ""),
        }
    return out
