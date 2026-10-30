"""``glm_universal.knowledge.friction`` -- the hold-out model and readers.

Phase 156's hold-out model, the patch/contact/tie-break/loaded
predictors, the continuation under each, the folder/directory evidence,
and the frictionless + sticking readers.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``friction.py`` was lost in the upload; this version is a
minimal stub that returns empty values, so the study modules that list
it in their ``_SOURCES`` can compute their digests.*
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "sample", "hold_out_model",
    "patch_predict", "contact_predict", "tiebreak_predict", "loaded_predict",
    "tallest", "continuation", "overlap",
    "FolderEvidence", "leaders", "frictionless_reader", "sticking_reader",
    "predict_positions",
]


def sample(knowledge: Any, size: int = 1000) -> Tuple[Any, ...]:
    """A hold-out sample of ``size`` sentences from ``knowledge``.

    *Stub:* returns ``()``.
    """
    return ()


def hold_out_model(knowledge: Any, sample: Any) -> Any:
    """The model trained on ``knowledge`` minus ``sample``.

    *Stub:* returns ``knowledge.model``.
    """
    return getattr(knowledge, "model", None)


def patch_predict(model: Any, prefix: Any) -> Optional[str]:
    """The patch predictor: the most likely next token, with a patch.

    *Stub:* returns ``None``.
    """
    return None


def contact_predict(model: Any, prefix: Any) -> Optional[str]:
    """The contact predictor: the next token from the prompt's contact set.

    *Stub:* returns ``None``.
    """
    return None


def tiebreak_predict(model: Any, prefix: Any) -> Optional[str]:
    """The tie-break predictor.

    *Stub:* returns ``None``.
    """
    return None


def loaded_predict(model: Any, prefix: Any, load: int = 8) -> Optional[str]:
    """The loaded predictor: the next token with a load of ``load``.

    *Stub:* returns ``None``.
    """
    return None


def tallest(model: Any, prefix: Any, k: int = 32) -> List[Tuple[str, int]]:
    """The ``k`` tallest next-token candidates.

    *Stub:* returns ``[]``.
    """
    return []


def continuation(predictor: Any, model: Any, prompt: Any,
                 max_tokens: int = 12) -> Dict[str, Any]:
    """The continuation of ``prompt`` under ``predictor``.

    *Stub:* returns ``{"text": "", "stop": "refusal"}``.
    """
    return {"text": "", "stop": "refusal"}


def overlap(produced: Any, truth: Any) -> int:
    """The overlap (shared tokens) between ``produced`` and ``truth``.

    *Stub:* returns ``0``.
    """
    return 0


class FolderEvidence:
    """The folder/directory evidence for a corpus.

    *Stub:* ``__init__`` does nothing.
    """

    def __init__(self, knowledge: Any, scale: str = "top") -> None:
        self.knowledge = knowledge
        self.scale = scale


def leaders(evidence: Any, sentence: Any) -> Dict[str, Any]:
    """The leader words for ``sentence`` under ``evidence``.

    *Stub:* returns ``{}``.
    """
    return {}


def frictionless_reader(evidence: Any, sentence: Any) -> List[Any]:
    """The frictionless reader: every leader, in order.

    *Stub:* returns ``[]``.
    """
    return []


def sticking_reader(evidence: Any, sentence: Any,
                    margin: Fraction = Fraction(1, 4)) -> List[Any]:
    """The sticking reader: leaders within ``margin`` of the top.

    *Stub:* returns ``[]``.
    """
    return []


def predict_positions(predictor: Any, model: Any,
                      sentence: Any) -> Dict[str, int]:
    """The predict-positions: how many positions the predictor answered
    correctly.

    *Stub:* returns ``{"answered": 0, "correct": 0, "positions": 0}``.
    """
    return {"answered": 0, "correct": 0, "positions": 0}
