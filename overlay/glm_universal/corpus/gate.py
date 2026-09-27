"""``glm_universal.corpus.gate`` -- the documents check, asked only when it can
have changed its mind.

The documents gate renders every generated block of every document and
compares it with what is written there.  It costs about three quarters of a
minute, and a session runs it on picking the round up, after each prose edit,
and again at the close.  On the first of those the answer is almost always the
one the last run gave, because nothing has moved at all.

This module is the record that lets it say so.  It takes one digest over
everything the check can read -- the documents, the code that renders them,
the frozen data that code reads, and the Lean sources the blocks quote -- and
stores it beside the verdict the check reached.  The next run recomputes the
digest, and if it is the same digest and the stored verdict was *passing*, the
tree cannot have changed its answer and the check is skipped.

Three properties keep that honest.

* **The digest is over the closure, not over a list.**  It is the sign-off
  ledger's own closure of the corpus command
  (:func:`glm_universal.signoff.rules.unit_closure`), which follows imports and
  adds the data, documents and Lean sources those modules name.  Nothing the
  check reads is outside it, and over-hashing is the safe direction: a file
  that moves without mattering costs one full check, while a file that matters
  can never move unnoticed.
* **Only a pass is ever stored.**  A failing check is never skipped: a session
  that has just been told what is stale must be able to run the gate again,
  see the same failure, and fix it.
* **It can be refused.**  ``--check --all`` ignores the record and runs the
  whole pass, which is also what the release does; the record is an
  optimisation, and nothing depends on it being there.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Iterable, Optional

from .. import integrity
from ..signoff import rules

__all__ = ["GATE_PATH", "SCHEMA", "inputs_digest", "stored", "record",
           "unchanged_since_pass", "forget"]

#: Where the record lives: beside the sign-off ledger, in the overlay root.
GATE_PATH = rules.PROJECT_ROOT / ".glm_corpus_gate.json"

#: Bumped when what the digest covers changes; an older record is ignored
#: rather than trusted, because a digest means nothing without its rule.
SCHEMA = 1

_COMMAND = rules.PROJECT_ROOT / "glm_universal" / "corpus" / "__main__.py"


def _closure() -> Iterable[Path]:
    """Every file the documents check can read."""
    return rules.unit_closure(_COMMAND)


def inputs_digest() -> str:
    """SHA-256 over the closure of the documents check, path by path.

    The same canonical form the ledger uses for a unit: sorted paths relative
    to the repository, each followed by the digest of its bytes.
    """
    root = rules.REPOSITORY_ROOT
    present = [path for path in sorted(_closure()) if path.is_file()]
    return integrity.tree_digest(present, root=root)


def stored() -> Optional[Dict[str, object]]:
    """The recorded verdict, or ``None`` if there is none this schema."""
    if not GATE_PATH.exists():
        return None
    try:
        data = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):                 # pragma: no cover - defensive
        return None
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        return None
    return data


def unchanged_since_pass() -> Optional[Dict[str, object]]:
    """The stored record when it is a pass and nothing it read has moved.

    ``None`` means the check has to be run: there is no record, the record is
    of a failure, or something in the closure has changed.
    """
    data = stored()
    if data is None or data.get("verdict") != "current":
        return None
    if data.get("digest") != inputs_digest():
        return None
    return data


def record(holds: bool, digest: Optional[str] = None) -> Dict[str, object]:
    """Store the verdict of a check that has just been run."""
    data = {
        "schema": SCHEMA,
        "digest": digest if digest is not None else inputs_digest(),
        "verdict": "current" if holds else "stale",
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    GATE_PATH.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n",
                         encoding="utf-8")
    return data


def forget() -> None:
    """Drop the record, so the next check runs in full."""
    if GATE_PATH.exists():
        GATE_PATH.unlink()
