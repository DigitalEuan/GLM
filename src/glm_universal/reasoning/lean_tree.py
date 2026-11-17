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
