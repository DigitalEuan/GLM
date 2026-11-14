"""The cent transfer compiler, as the GLM's source of proposals.

*Created 14 November 2026 (platform round, cent compiler round 1).*

The compiler is a supplied system filed at ``source_material/ToDo/cent_compiler_v12``
(intake item ``cent_compiler_v12``).  It answers two questions the GLM does not
answer itself: given a problem statement, which declared physical or
information methods could compute it (``discover``); and given an operation,
what are the reviewable proposals for realising it, with a test handoff
(``propose``).

This module is the one way the GLM asks.  It is a subprocess bridge, not an
import: the compiler is a separate system with its own gate, grammar and
review ledger, and the GLM must be able to run without the supply folder at
all.  Nothing here writes, nothing here measures, and no value is invented --
what comes back is the compiler's own JSON, parsed, with its schema carried
through so a caller can see which of the compiler's schemas it is holding.

Usage::

    PYTHONPATH=src python3 -m glm_universal.cent_bridge "compute an irrational value"
    PYTHONPATH=src python3 -m glm_universal.cent_bridge --propose sqrt --target glm-reference
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .constants import source_material_item

#: The intake item that holds the compiler.  One folder, one system.
CENT_ITEM = "cent_compiler_v12"
#: The launcher inside that folder (``python3 cent <command>``).
CENT_LAUNCHER = "cent"


class CentUnavailable(RuntimeError):
    """The compiler is not in this checkout, so it cannot be asked."""


class CentError(RuntimeError):
    """The compiler ran but did not answer: a non-zero exit or no JSON."""


def cent_directory() -> Path:
    """The folder the compiler is filed in (whether or not it exists)."""
    return source_material_item(CENT_ITEM)


def available() -> bool:
    """Is the compiler present and launchable in this checkout?"""
    folder = cent_directory()
    return (folder / CENT_LAUNCHER).is_file() and (folder / "cent_compiler").is_dir()


def _require() -> Path:
    folder = cent_directory()
    if not available():  # pragma: no cover - message path, tested via monkeypatch
        raise CentUnavailable(
            f"the cent compiler is not in this checkout: looked for "
            f"{folder / CENT_LAUNCHER}; the intake item is {CENT_ITEM}"
        )
    return folder


def _run(command: Sequence[str], *, timeout: int) -> Dict[str, Any]:
    """Run one ``cent`` command and return its parsed JSON payload."""
    folder = _require()
    argv: List[str] = [sys.executable, str(folder / CENT_LAUNCHER), *command, "--json"]
    try:
        completed = subprocess.run(
            argv,
            cwd=str(folder),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CentError(f"cent {' '.join(command)} could not be run: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        raise CentError(
            f"cent {' '.join(command)} failed with exit {completed.returncode}: "
            f"{detail[-1] if detail else 'no stderr'}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CentError(f"cent {' '.join(command)} did not return JSON") from exc
    if not isinstance(payload, dict):
        raise CentError(f"cent {' '.join(command)} returned {type(payload).__name__}, not an object")
    return payload


def discover(problem: str, *, domain: Optional[str] = None,
             limit: int = 20, timeout: int = 120) -> Dict[str, Any]:
    """Find the declared methods that could compute ``problem``.

    Returns the compiler's ``cent-discovery/1`` payload: the parsed problem
    (behaviour, object, goals), whether anything matched, and the candidate
    methods with their declared evidence.  An unmatched problem is an answer,
    not an error: ``payload["matched"]`` is ``False`` and the payload still
    says what it read.
    """
    command = ["discover", problem, "--limit", str(int(limit))]
    if domain:
        command += ["--domain", domain]
    return _run(command, timeout=timeout)


def propose(operation: str, *, target: str = "glm-reference", top: int = 3,
            trial: bool = False, timeout: int = 180) -> Dict[str, Any]:
    """Build reviewable proposals for ``operation`` on ``target``.

    Returns the compiler's proposal bundle: each proposal carries its
    mechanism, its adapter, the handoff command and the fixed test vectors it
    would be executed over.  ``trial=True`` also runs the ready proposals over
    those vectors (the compiler's own ``--trial``).
    """
    command = ["propose", operation, "--target", target, "--top", str(int(top))]
    if trial:
        command.append("--trial")
    return _run(command, timeout=timeout)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """``python3 -m glm_universal.cent_bridge [--propose OP] [--target T] QUESTION``."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not available():
        print(f"cent compiler unavailable: {cent_directory()}")
        return 2
    if any(a in {"-h", "--help"} for a in args):
        print(__doc__)
        return 0
    propose_operation: Optional[str] = None
    target = "glm-reference"
    words: List[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--propose" and index + 1 < len(args):
            propose_operation = args[index + 1]
            index += 2
            continue
        if token == "--target" and index + 1 < len(args):
            target = args[index + 1]
            index += 2
            continue
        words.append(token)
        index += 1
    try:
        if propose_operation is not None:
            payload = propose(propose_operation, target=target)
            print(f"PROPOSALS  {propose_operation} on {target}")
        else:
            question = " ".join(words).strip()
            if not question:
                print("give a problem statement, or --propose OPERATION")
                return 2
            payload = discover(question)
            print(f"DISCOVER   {question}")
            matched = payload.get("matched")
            print(f"matched    {'yes' if matched else 'no'}")
            problem = payload.get("problem") or {}
            if problem.get("goals"):
                print("goals      " + ", ".join(problem["goals"]))
    except (CentUnavailable, CentError) as exc:
        print(f"cent: {exc}")
        return 1
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
