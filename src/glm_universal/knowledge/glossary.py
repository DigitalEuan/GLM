"""``glm_universal.knowledge.glossary`` -- the paper's held-out glossary.

Phase 155's held-out glossary: the 27 entries of the paper's Appendix E
(``GLM_ACADEMIC_PAPER.md``), the grade (shared content words, with ``s``
removed from words >3 letters), the controls (first-mention,
mismatched-gloss), and the **context ranking** that ``corpus define``
now uses.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``glossary.py`` was lost in the upload; this version is a
minimal stub that returns empty values, so the study modules that list
it in their ``_SOURCES`` can compute their digests and the CLI
subcommands degrade gracefully.*
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

__all__ = ["GLOSSARY", "hold_out", "grade", "first_mention",
           "mismatched_gloss", "context_ranking"]


#: The held-out glossary: a tuple of ``(term, gloss)`` pairs.  *Stub:*
#: empty.  The real implementation reads the 27 entries from
#: ``GLM_ACADEMIC_PAPER.md`` Appendix E.
GLOSSARY: Tuple[Tuple[str, str], ...] = ()


def hold_out(knowledge: Any) -> Any:
    """Return a :class:`Knowledge` with the glossary sentences removed.

    *Stub:* returns ``knowledge`` unchanged.
    """
    return knowledge


def grade(answer_tokens: Any, gloss_tokens: Any,
          term_tokens: Any) -> int:
    """The shared-content-words grade.

    *Stub:* returns ``0``.
    """
    return 0


def first_mention(term: str, knowledge: Any) -> Any:
    """The first sentence in the corpus that mentions ``term``.

    *Stub:* returns ``None``.
    """
    return None


def mismatched_gloss(term: str, knowledge: Any) -> Tuple[str, str]:
    """A gloss that mentions ``term`` but does not define it.

    *Stub:* returns ``("", "")``.
    """
    return ("", "")


def context_ranking(term: str, knowledge: Any) -> Dict[str, Any]:
    """The context ranking: of the sentences that define ``term``, the one
    holding most of ``term``'s corpus context first.

    *Stub:* returns ``{}``.
    """
    return {}
