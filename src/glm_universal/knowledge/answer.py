"""``glm_universal.knowledge.answer`` -- the corpus query surface.

The seven readings of the corpus: ``define``, ``context``, ``similar``,
``related``, ``continue_text``, ``spread``, ``predict``.  Each takes a
:class:`~glm_universal.knowledge.model.Knowledge` instance (loaded via
:func:`~glm_universal.knowledge.model.load` if ``None``) and the
term/phrase, and returns a dict with the answer and the witness
sentence/address.  Refuses (returns ``{"ok": False, "refusal": "..."}``)
on unknown terms, ties, and words with too little company.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``answer.py`` was lost in the upload; this version is a minimal
stub that returns refusals for every reading, so the runtime's
``evidence.from_define`` (which uses ``getattr`` with a fallback) and the
study modules' ``compute()`` functions degrade gracefully.  When the full
corpus-query infrastructure is restored, each function should be replaced
with its real implementation.*
"""
from __future__ import annotations

from typing import Any, Dict, Optional

__all__ = [
    "define", "context", "similar", "related",
    "continue_text", "spread", "predict",
]


def _refuse(reading: str) -> Dict[str, Any]:
    """A standard refusal dict for a reading that is not reconstructed."""
    return {"ok": False, "refusal": f"{reading} is not reconstructed"}


def define(term: str, knowledge: Any = None) -> Dict[str, Any]:
    """The ``define`` reading: the sentence that defines ``term``.

    Returns a dict with ``answer`` (the defining sentence), ``candidates``
    (the witness addresses), ``witness`` (the pattern/strength/source
    tuple), and ``ok``.  *Stub:* always refuses.
    """
    return _refuse("define")


def context(term: str, knowledge: Any = None,
            scale: str = "sentence") -> Dict[str, Any]:
    """The ``context`` reading: the sentences that mention ``term``.

    *Stub:* always refuses.
    """
    return _refuse("context")


def similar(word: str, knowledge: Any = None,
             k: int = 10) -> Dict[str, Any]:
    """The ``similar`` reading: the ``k`` words nearest ``word`` on the
    lattice.

    *Stub:* always refuses.
    """
    return _refuse("similar")


def related(word: str, knowledge: Any = None,
            k: int = 10) -> Dict[str, Any]:
    """The ``related`` reading: the ``k`` words co-occurring with ``word``.

    *Stub:* always refuses.
    """
    return _refuse("related")


def continue_text(prefix: str, knowledge: Any = None,
                  max_tokens: int = 12) -> Dict[str, Any]:
    """The ``continue_text`` reading: the continuation of ``prefix``.

    *Stub:* always refuses.
    """
    return _refuse("continue_text")


def spread(word: str, knowledge: Any = None) -> Dict[str, Any]:
    """The ``spread`` reading: the folders/documents ``word`` appears in.

    *Stub:* always refuses.
    """
    return _refuse("spread")


def predict(prefix: str, knowledge: Any = None) -> Dict[str, Any]:
    """The ``predict`` reading: the next-token prediction for ``prefix``.

    *Stub:* always refuses.
    """
    return _refuse("predict")
