"""``glm_universal.knowledge.ask`` -- the corpus ``--ask`` surface.

The ``corpus`` query kind's request grammar, and the brute-force recheck
column 3 runs.  Parses a request like ``"corpus define golay code"`` or
``"corpus context of nrci"`` and dispatches to the right
:mod:`~glm_universal.knowledge.answer` reading.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``ask.py`` was lost in the upload; this version is a minimal
stub that raises :class:`CorpusRefusal` for every request, so the CLI
subcommand ``corpus-ask`` prints a clean refusal and exits 1.*
"""
from __future__ import annotations

from typing import Any, Dict

__all__ = ["CorpusRefusal", "answer_request"]


class CorpusRefusal(Exception):
    """Raised by :func:`answer_request` when the request cannot be answered.

    The CLI handler in :mod:`glm_universal.tools` catches this and prints
    ``refused: <message>``, exiting 1.
    """


def answer_request(text: str) -> Dict[str, Any]:
    """Parse ``text`` and dispatch to the right corpus reading.

    Returns a dict with at least an ``"answer"`` key (string).  Raises
    :class:`CorpusRefusal` on refusal.

    *Stub:* always raises ``CorpusRefusal``.
    """
    raise CorpusRefusal("the corpus ask surface is not reconstructed")
