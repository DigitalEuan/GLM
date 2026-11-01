"""``glm_universal.wheels.cfsg_import`` -- absorb ``card_<X> = <int>``
declarations from a local clone of the AxiomMath/CFSG Lean formalisation into
a Monster Wheel.

*Created 31 October 2026 (repository check).  This was the method*
``MonsterWheel.extend_from_cfsg_directory`` *of the supplied
glm_wheels_bundle, absorbed with* :mod:`glm_universal.wheels.monster_wheel`
*(directive D22).  It is a module of its own because it walks a directory
for Lean files, and the sign-off closure rule reads such a walk as a
dependency on the whole Lean development: kept in* ``monster_wheel.py`` *it
put the development into the import closure of every session, since the
parser's* ``sequence`` *lookup kind builds the wheel.  Behaviour unchanged.*

The walk reads only the directory it is given (never the repository's own
Lean tree unless that is what the caller passes) and never touches the
network.  An id already present is never overwritten (``conflict_unsound``).
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

__all__ = ["extend_from_cfsg_directory"]


def extend_from_cfsg_directory(wheel, cfsg_root: Path) -> Tuple[int, int]:
    """Walk ``cfsg_root`` and absorb into ``wheel`` (a
    :class:`~glm_universal.wheels.monster_wheel.MonsterWheel`) every
    ``card_<X> = <int>`` declaration whose id is new.  Returns
    ``(added, failed)``: entries registered, files that could not be read."""
    added = 0
    failed = 0
    for lean_file in sorted(Path(cfsg_root).rglob("*.lean")):
        try:
            entries = wheel.parse_cfsg_lean_file(lean_file)
        except Exception:
            failed += 1
            continue
        for e in entries:
            if e.oeis_id in wheel:
                continue
            wheel.register(e)
            added += 1
        wheel._absorbed_from_cfsg.append(lean_file)
    return added, failed
