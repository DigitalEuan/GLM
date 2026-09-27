"""``glm_universal.signoff.mirror`` -- the Lean tree's second copy, generated.

The formal development lives twice: ``RequestProject/GLM/`` at the repository
root, which is what ``lake build`` compiles, and
``overlay/glm_lean/RequestProject/GLM/``, which ships with the package so that
the overlay is self-contained.  That the two agree is a real invariant and it
is checked -- the ``lean-copies-identical`` instrument runs ``diff -r`` over
them -- but checking is not the same as maintaining, and keeping two copies in
step by hand is a class of mistake rather than a task.

So the mirror is **generated**, on the same terms as ``DIGEST.md``: one side is
the source, the other is an output, and the command that writes it says what it
wrote.  ``RequestProject/GLM`` is the source, because that is the copy the
build compiles; the mirror's own ``README.md`` is the one file that belongs to
the mirror and is never overwritten.

::

    cd overlay
    PYTHONPATH=. python3 -m glm_universal.tools lean-mirror
    PYTHONPATH=. python3 -m glm_universal.tools lean-mirror --write
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import ledger as sl

__all__ = [
    "SOURCE",
    "MIRROR",
    "MIRROR_ONLY",
    "mirror_report",
    "write_mirror",
]

#: The copy the build compiles: the source of truth.
SOURCE = sl.REPOSITORY_ROOT / "RequestProject" / "GLM"

#: The copy that ships inside the overlay: an output.
MIRROR = sl.PROJECT_ROOT / "glm_lean" / "RequestProject" / "GLM"

#: Files that belong to the mirror and are not written from the source.
MIRROR_ONLY: Tuple[str, ...] = ("README.md",)


def _relative_files(root: Path) -> Tuple[str, ...]:
    if not root.is_dir():
        return ()
    return tuple(sorted(str(p.relative_to(root))
                        for p in root.rglob("*") if p.is_file()))


def mirror_report() -> Dict[str, object]:
    """What the mirror is missing, holds extra, or holds differently."""
    source = [name for name in _relative_files(SOURCE)
              if name not in MIRROR_ONLY]
    mirrored = [name for name in _relative_files(MIRROR)
                if name not in MIRROR_ONLY]
    missing = [name for name in source if name not in set(mirrored)]
    extra = [name for name in mirrored if name not in set(source)]
    differing = [name for name in source
                 if name not in missing
                 and (SOURCE / name).read_bytes() != (MIRROR / name).read_bytes()]
    return {
        "source": str(SOURCE),
        "mirror": str(MIRROR),
        "files": len(source),
        "missing": tuple(missing),
        "extra": tuple(extra),
        "differing": tuple(differing),
        "identical": not (missing or extra or differing),
    }


def write_mirror(report: Optional[Dict[str, object]] = None
                 ) -> Dict[str, object]:
    """Bring the mirror to the source, and say what that took.

    Copies what is missing or different and removes what the source no longer
    has.  A file listed in :data:`MIRROR_ONLY` is left alone -- the mirror's
    README describes the mirror.
    """
    found = report if report is not None else mirror_report()
    written: List[str] = []
    removed: List[str] = []
    for name in tuple(found["missing"]) + tuple(found["differing"]):
        target = MIRROR / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / name, target)
        written.append(name)
    for name in found["extra"]:
        (MIRROR / name).unlink()
        removed.append(name)
    after = mirror_report()
    return {
        "written": tuple(sorted(written)),
        "removed": tuple(sorted(removed)),
        "identical": after["identical"],
        "files": after["files"],
    }
