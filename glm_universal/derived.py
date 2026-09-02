"""Derived artefacts: computed once, reused only against a recorded digest.

Several things this package reports are *derivations*: a pure function of
frozen inputs -- the source of a module, a data table, the Lean tree -- with
no argument and no state.  The 98,280-class type-2 table, the grounded
semantic graph, the coset and FWHT tables, the escalation class keys, and the
two study ledgers are all of that kind.  They are expensive, and they were
being recomputed once per call: ``test_catalog.py`` spent five and a half
minutes rebuilding the same ledger twelve times.

The model this module copies is
:func:`glm_universal.reasoning.lean_address.address_book`: compute once, store
the answer next to the SHA-256 digest of the tree it was computed from,
recompute when the digest moves, and *report* a stale book rather than answer
from it.  Two layers of that idea live here.

``memo``
    In-process reuse.  A zero-argument derivation is wrapped so the second
    call in a process returns the first call's object.  This is sound for
    exactly the reason the sign-off ledger is sound: the inputs are files, and
    within one process they cannot change without something having written
    them.  Every memo is registered, so :func:`memo_registry` can list them,
    :func:`clear_memos` can drop them, and a test can check that clearing and
    recomputing gives the same answer -- which is what makes the memo an
    optimisation rather than a claim.

``DerivedStore``
    Across processes.  A JSON artefact stored beside the digest of the inputs
    it was computed from, with :meth:`DerivedStore.state` reporting *fresh*,
    *stale* or *absent* the way ``lean_address.cache_state`` does.  Nothing
    here ever answers from a stale artefact; a stale one is a signal to
    recompute, and the recomputation is what gets stored.

Neither layer imports :mod:`hashlib` at module scope, so the core
sub-packages may import this module without breaking the source audit of
:func:`glm_universal.reasoning.blueprint.ubp_source_audit`; the digest is
taken from :mod:`glm_universal.integrity`, lazily, only when a store is used.
"""

from __future__ import annotations

import functools
import json
import os
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple, TypeVar

__all__ = [
    "memo",
    "memo_registry",
    "clear_memos",
    "memo_state",
    "DerivedStore",
    "CACHE_ROOT",
]

T = TypeVar("T")

#: Where derived artefacts are stored: beside the package's frozen data, but
#: in a directory of their own, because these are *recomputable* and the
#: ``_data`` directories are inputs.
CACHE_ROOT = Path(__file__).resolve().parent / "_derived"


# ===========================================================================
#  In-process memoisation
# ===========================================================================

#: Every memoised derivation, by dotted name.
_REGISTRY: Dict[str, "_Memo"] = {}


class _Memo:
    """One memoised zero-argument derivation."""

    def __init__(self, function: Callable[[], T], name: str) -> None:
        self.function = function
        self.name = name
        self.hits = 0
        self.misses = 0
        self._value: Optional[T] = None
        self._filled = False

    def __call__(self) -> T:
        if self._filled:
            self.hits += 1
            return self._value  # type: ignore[return-value]
        self._value = self.function()
        self._filled = True
        self.misses += 1
        return self._value

    @property
    def filled(self) -> bool:
        return self._filled

    def clear(self) -> None:
        self._value = None
        self._filled = False


def memo(function: Callable[[], T]) -> Callable[[], T]:
    """Reuse a zero-argument derivation within one process.

    The wrapped function keeps ``__wrapped__``, so the uncached derivation is
    always reachable -- a test that wants to prove the memo changes nothing
    calls ``f.__wrapped__()`` and compares.
    """
    name = f"{function.__module__}.{function.__qualname__}"
    holder = _Memo(function, name)

    @functools.wraps(function)
    def wrapper() -> T:
        return holder()

    wrapper.__wrapped__ = function  # type: ignore[attr-defined]
    wrapper.memo = holder           # type: ignore[attr-defined]
    _REGISTRY[name] = holder
    return wrapper


def memo_registry() -> Tuple[str, ...]:
    """The dotted names of every memoised derivation, sorted."""
    return tuple(sorted(_REGISTRY))


def clear_memos(names: Optional[Iterable[str]] = None) -> int:
    """Drop cached values.  Returns how many held one."""
    wanted = list(_REGISTRY) if names is None else list(names)
    dropped = 0
    for name in wanted:
        holder = _REGISTRY.get(name)
        if holder is not None and holder.filled:
            holder.clear()
            dropped += 1
    return dropped


def memo_state() -> Dict[str, Dict[str, object]]:
    """Hits, misses and whether a value is held, per derivation."""
    return {
        name: {"filled": holder.filled, "hits": holder.hits,
               "misses": holder.misses}
        for name, holder in sorted(_REGISTRY.items())
    }


# ===========================================================================
#  Digest-keyed artefacts on disk
# ===========================================================================

class DerivedStore:
    """A JSON artefact stored beside the digest of what it was derived from.

    ``inputs`` is the callable that lists the files the artefact depends on;
    ``schema`` is bumped whenever the artefact's shape changes, so an old file
    is *absent* rather than wrong.
    """

    def __init__(self, name: str, inputs: Callable[[], Iterable[Path]],
                 schema: int = 1, root: Optional[Path] = None) -> None:
        self.name = name
        self.inputs = inputs
        self.schema = schema
        self.root = Path(root) if root is not None else CACHE_ROOT

    # -- the digest ------------------------------------------------------
    @property
    def path(self) -> Path:
        return self.root / f"{self.name}.json"

    def input_paths(self) -> Tuple[Path, ...]:
        return tuple(sorted({Path(p).resolve() for p in self.inputs()}))

    def input_digest(self) -> str:
        """SHA-256 over the inputs: name and content of every one."""
        from . import integrity  # local: the core must not import hashlib

        paths: List[Path] = [p for p in self.input_paths() if p.is_file()]
        if not paths:
            return "absent"
        # names are taken relative to the deepest directory holding all of
        # them, so the digest is about the inputs and not about where the
        # checkout happens to live
        root = Path(os.path.commonpath([str(p) for p in paths]))
        if root.is_file():
            root = root.parent
        return integrity.tree_digest(paths, root)

    # -- reading and writing ---------------------------------------------
    def load(self) -> Optional[Dict[str, object]]:
        """The stored artefact, or ``None`` when there is none."""
        if not self.path.is_file():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (ValueError, OSError):  # pragma: no cover - defensive
            return None

    def state(self) -> Dict[str, object]:
        """Is the stored artefact still a description of its inputs?

        The same three-way answer ``lean_address.cache_state`` gives: present
        or not, fresh or not, with both digests shown so the verdict can be
        checked rather than believed.
        """
        stored = self.load()
        live = self.input_digest()
        if stored is None:
            return {"name": self.name, "present": False, "fresh": False,
                    "stored_digest": None, "live_digest": live,
                    "verdict": "absent"}
        recorded = stored.get("input_digest")
        fresh = (recorded == live and stored.get("schema") == self.schema)
        return {"name": self.name, "present": True, "fresh": fresh,
                "stored_digest": recorded, "live_digest": live,
                "verdict": "fresh" if fresh else "stale"}

    def read_fresh(self) -> Optional[object]:
        """The payload, but only if the digest still holds."""
        if not self.state()["fresh"]:
            return None
        stored = self.load()
        return None if stored is None else stored.get("payload")

    def write(self, payload: object) -> Path:
        """Store a payload against the digest of the inputs *now*.

        Written through a temporary file in the same directory and moved into
        place, so a reader never sees half an artefact.  The suite runs its
        files in parallel and several processes may derive the same thing at
        once; without this, one of them could read what another was midway
        through writing.
        """
        self.root.mkdir(parents=True, exist_ok=True)
        document = {
            "name": self.name,
            "schema": self.schema,
            "input_digest": self.input_digest(),
            "payload": payload,
        }
        body = json.dumps(document, indent=1, sort_keys=True) + "\n"
        scratch = self.path.with_name(f"{self.path.name}.{os.getpid()}.part")
        scratch.write_text(body, encoding="utf-8")
        os.replace(scratch, self.path)
        return self.path

    def cached(self, compute: Callable[[], object]) -> object:
        """The payload: read when fresh, recomputed and stored otherwise."""
        found = self.read_fresh()
        if found is not None:
            return found
        payload = compute()
        self.write(payload)
        return payload
