"""``glm_universal.quoted_measurements`` -- which stored measurements a
computation read, so a cache that records answers can be guarded by them.

*Created 20 October 2026 (Phase 174: ``studies/QUOTED_MEASUREMENTS_STUDY.md``).*

Why this module exists
----------------------
A measurement cache is guarded by the digest of its *sources*: the modules it
lists in ``_SOURCES``.  A census that records the system's *answers* -- the
evidence census of Phase 169 records every evaluation answer -- also depends on
every stored measurement those answers quote: ``report anonymous`` reads
``reasoning/_data/anonymous_register_study.json``, and so on.  Re-take one of
those, and the census still holds the old answer while its digest still says
*current* (``ITERATE.md`` §0.1, hazard 4; ``STATUS.md`` To-Do item 7).

This module records, while a computation runs, every file it opens under a
``_data`` directory of the package -- the stored measurements -- so that the
cache can store that list beside its result and add those files to its digest.
Re-take a quoted measurement and the census turns *stale*, as it should.

Nothing here interprets a file; it only notes which were opened.  The
recording wraps :func:`open` (and :func:`io.open`, through which
:meth:`pathlib.Path.read_text` and :meth:`pathlib.Path.read_bytes` read) for
the duration of a ``with`` block and restores them afterwards.  A file read
before the block began -- at the import of a module imported earlier -- is not
seen; the caches that use this start the recording before their imports.
"""

from __future__ import annotations

import builtins
import contextlib
import io
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set

__all__ = ["PACKAGE_ROOT", "DATA_DIR", "recording", "quoted_paths", "existing"]

#: The package whose stored measurements are recorded.
PACKAGE_ROOT: Path = Path(__file__).resolve().parent

#: The directory name a stored measurement lives under.
DATA_DIR = "_data"


def _note(seen: Set[str], target) -> None:
    if isinstance(target, int):
        return
    try:
        path = Path(target).resolve()
    except (TypeError, ValueError, OSError):
        return
    try:
        rel = path.relative_to(PACKAGE_ROOT)
    except ValueError:
        return
    if DATA_DIR in rel.parts[:-1] and path.is_file():
        seen.add(rel.as_posix())


@contextlib.contextmanager
def recording() -> Iterator[Set[str]]:
    """Record every stored measurement opened for reading inside the block.

    Yields the set the names are added to (package-relative, POSIX), which
    holds its contents after the block ends.  Nested blocks each see the
    reads made inside them.
    """
    seen: Set[str] = set()
    old_builtin, old_io = builtins.open, io.open

    def recorded_open(file, mode="r", *args, **kwargs):
        if "r" in mode and not any(c in mode for c in "wax+"):
            _note(seen, file)
        return old_io(file, mode, *args, **kwargs)

    builtins.open = recorded_open
    io.open = recorded_open
    try:
        yield seen
    finally:
        builtins.open = old_builtin
        io.open = old_io


def quoted_paths(names: Iterable[str],
                 exclude: Iterable[Path] = ()) -> List[str]:
    """The recorded names, sorted, without those in ``exclude`` (a cache's
    own file and the caches downstream of it, which would make a cycle)."""
    skip = set()
    for p in exclude:
        try:
            skip.add(Path(p).resolve().relative_to(PACKAGE_ROOT).as_posix())
        except ValueError:
            continue
    return sorted(set(names) - skip)


def existing(names: Optional[Iterable[str]]) -> List[Path]:
    """The recorded names as paths under the package, those that exist."""
    out = []
    for n in names or ():
        p = PACKAGE_ROOT / n
        if p.is_file():
            out.append(p)
    return out
