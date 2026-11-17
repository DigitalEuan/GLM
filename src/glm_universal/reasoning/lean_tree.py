"""``glm_universal.reasoning.lean_tree`` -- locating and digesting the Lean tree.

This module is the only place that walks the Lean development with a
``*.lean`` glob.  Splitting it out of :mod:`glm_universal.reasoning.lean_address`
means that modules on the answering path, which read only the stored address
book, no longer name that glob in their import closure: the sign-off ledger
resolves a ``*.lean`` (or bare ``.lean``) token to the whole development, so
a module that merely *imports* a module containing such a token takes every
Lean file as a dependency.  Builders and digesters import this module; the
answering path does not.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

_HERE = Path(__file__).resolve()

_LEAN_CANDIDATES = (
    _HERE.parent.parent.parent / "lean" / "RequestProject" / "GLM",
)

def lean_root() -> Optional[Path]:
    """The directory holding the Lean development, or ``None``."""
    for candidate in _LEAN_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return None

def lean_files() -> Tuple[Path, ...]:
    """Every ``.lean`` file of the development, in a stable order."""
    root = lean_root()
    if root is None:
        return ()
    return tuple(sorted(root.rglob("*.lean")))

def tree_digest() -> str:
    """SHA-256 over the Lean sources: name and content of every file."""
    from .. import integrity

    root = lean_root()
    if root is None:
        return "absent"
    return integrity.tree_digest(lean_files(), root)


def lean_available() -> bool:
    """Whether the Lean development is present on disk.

    The Lean half of the system is an *optional check*: when it is absent
    the Python half still answers, and a caller that needs a Lean file
    should treat ``False`` as "no Lean file to land on" rather than as an
    error.  Nothing here shells out to ``lake``.
    """
    return lean_root() is not None


def lean_file_for(name: str, create: bool = False) -> tuple:
    """The Lean file a declaration named ``name`` lives in (or would live
    in), and whether it is present.

    Returns ``(path, present)``.  ``path`` is the existing file when the
    declaration is found in the stored book or the development; when neither
    is available it is the candidate path the development would use
    (``<root>/<Name>.lean`` with dots as separators) so a caller can create
    it.  ``present`` is ``True`` only when the file exists on disk.

    With ``create=True`` a missing file (and its parent directories) is
    created as an empty Lean file and ``present`` becomes ``True``.  This is
    the "land on a Lean file if it exists or can be created" path: it never
    runs ``lake`` and never overwrites an existing file.
    """
    root = lean_root()
    candidate = None
    # Prefer the stored book's file field when it is there.
    try:
        from . import lean_book as _lb
        rows = _lb.declaration_rows()
        row = rows.get(name)
        if isinstance(row, dict):
            f = row.get("file")
            if f:
                if root is not None:
                    p = root / f if not Path(f).is_absolute() else Path(f)
                    if p.exists():
                        return (p, True)
                    candidate = p
    except Exception:
        pass
    if root is None:
        return (None, False)
    # Fall back to a name-derived candidate path.
    if candidate is None:
        rel = name.replace(".", "/") + ".lean"
        candidate = root / rel
    present = candidate.exists()
    if create and not present:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text("", encoding="utf-8")
            present = True
        except OSError:
            present = candidate.exists()
    return (candidate, present)


def source_label() -> str:
    """Which half of the system is available for answering: ``lean`` when the
    development is present, ``python`` otherwise."""
    return "lean" if lean_available() else "python"
