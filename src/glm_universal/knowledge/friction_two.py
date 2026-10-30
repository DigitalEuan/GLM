"""``glm_universal.knowledge.friction_two`` -- worn contact and the noise-set reader.

Phase 157's worn contact (each touch-set word has a budget of 2) and the
noise-set sticking reader (margin of ``r/8``, ``r`` the leader's changes
so far), over Phase 156's sample and readers.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``friction_two.py`` was lost in the upload; this version is a
minimal stub that returns empty values.*
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = [
    "worn_contact_predict", "worn_continuation", "noise_set_reader",
]


def worn_contact_predict(model: Any, prefix: Any,
                         budget: int = 2) -> Optional[str]:
    """The worn-contact predictor: each touch-set word has a budget of
    ``budget``.

    *Stub:* returns ``None``.
    """
    return None


def worn_continuation(model: Any, prompt: Any,
                      max_tokens: int = 12) -> Dict[str, Any]:
    """The continuation under the worn-contact predictor.

    *Stub:* returns ``{"text": "", "stop": "refusal"}``.
    """
    return {"text": "", "stop": "refusal"}


def noise_set_reader(evidence: Any, sentence: Any,
                     base: int = 8) -> List[Any]:
    """The noise-set sticking reader: leaders within ``r/base`` of the top.

    *Stub:* returns ``[]``.
    """
    return []
