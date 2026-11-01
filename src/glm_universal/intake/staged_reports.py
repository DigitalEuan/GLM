"""``glm_universal.intake.staged_reports`` -- a study's recompute function,
run against code still staged in an intake item.

*Created 31 October 2026 (repository check; directive D22).  Last altered
31 October 2026: the two wheel studies' wrappers (``integer_wheel_report``,
``cent_wheels_report``) removed -- the Integer, Monster and cent wheels are
installed in the package (provisionally, by the owner's decision, until the
Lean build confirms them), so their studies are recomputed by the installed
modules directly; the general :func:`staged_call` stays for the next item
whose code waits in ``staged/``.*

A study measured on code that waits in an intake item's ``staged/`` folder
(not yet installed in the package) still needs a function that recomputes its
Tier-0 figures; that function lives in the staged code, which the package does
not import.  :func:`staged_call` runs such a function in the scratch view of
the repository that ``staged:`` tests use
(:func:`glm_universal.intake.actions.staged_overlay`): a fresh interpreter,
the staged files in place, nothing in the repository written.  The result
comes back as plain data (mappings with string keys, lists, strings,
integers, booleans; a ``Fraction`` as its ``"p/q"`` text).  Once the item is
installed the same dotted name runs the installed module.

Nothing here constructs a float.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

from .ledger import Layout, LedgerError, load, record_by_id

__all__ = ["staged_call"]

_RUNNER = r'''
import dataclasses, importlib, json, sys
from fractions import Fraction

def plain(x):
    if isinstance(x, bool) or x is None or isinstance(x, (int, str)):
        return x
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {str(k) if not isinstance(k, str) else k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((plain(v) for v in x), key=repr)
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return plain(dataclasses.asdict(x))
    return repr(x)

module, _, fn = sys.argv[1].rpartition(".")
result = getattr(importlib.import_module(module), fn)()
sys.stdout.write("\n@@GLM-STAGED-RESULT@@" + json.dumps(plain(result), sort_keys=True) + "\n")
'''


def staged_call(item_id: str, dotted: str, layout: Optional[Layout] = None,
                timeout: int = 3600) -> Any:
    """Call ``dotted`` (``module.function``, no argument) in the scratch view
    of the repository with ``item_id``'s staged files in place, and return its
    result as plain data.  Raises :class:`LedgerError` when the item is not in
    the ledger and ``RuntimeError`` when the call fails."""
    from .actions import _env, staged_overlay
    lay = layout or Layout.default()
    rec = record_by_id(load(lay), item_id)
    with tempfile.TemporaryDirectory(prefix="glm-intake-staged-call-") as tmp:
        top = staged_overlay(rec, lay, Path(tmp))
        src = top / lay.package.parent.relative_to(lay.root)
        p = subprocess.run([sys.executable, "-c", _RUNNER, dotted], cwd=str(top),
                           env=_env([src]), capture_output=True, text=True, timeout=timeout)
    marker = "@@GLM-STAGED-RESULT@@"
    if p.returncode != 0 or marker not in p.stdout:
        tail = (p.stderr or p.stdout).strip().splitlines()[-1:] or [""]
        raise RuntimeError(f"{dotted} (staged in {item_id}) failed: exit {p.returncode}; {tail[0][:300]}")
    return json.loads(p.stdout.rsplit(marker, 1)[1].strip())

