"""``glm_universal.reasoning.confidence_floor`` -- answer above a floor, or say how sure.

The question
------------
Phase 77 attached the exact posterior to the decoder's own readings
(:mod:`glm_universal.reasoning.decoder_confidence`): the carried fork's context
stage (``resolve``) and the second reading (``agree``) can each say how likely
their answer is to be the codeword sent, at a declared bit-flip rate.  It left
two things open: a *floor* (answer only above a declared confidence) and the
confidence printed beside every answer.  The owner declined to pick the
floor's threshold and asked instead for a hunt over thresholds -- and, where no
threshold works, for a confidence score rather than a refusal.  The
confidence-floor study (Phase 80) declared its marks F1-F7 before this module
existed; :mod:`glm_universal.reasoning.confidence_floor_marks` measures them,
including the exact channel census the hunt is run on.

The two readings of this module
-------------------------------
* **The graded answer** (:func:`graded_resolve`, :func:`graded_agree`) -- the
  reading's value *and* its confidence, with a band word.  It never refuses on
  confidence; it refuses only where the reading itself refuses, by the same
  name (``AMBIGUOUS``, ``UNCORRECTABLE``, ``OUTSIDE_SUBSTRATE``,
  ``RATE_OUT_OF_RANGE``).
* **The floor** (:func:`floor_resolve`, :func:`floor_agree`) -- the same
  reading, which answers only when its confidence is at least the declared
  floor ``t`` and otherwise refuses ``BELOW_FLOOR``, naming the confidence it
  had.  A floor that is not an exact rational in ``(0, 1]`` is refused
  ``FLOOR_OUT_OF_RANGE``.

The bands are wording declared by the study, never a changed answer:
*near-certain* at or above 999/1000, *confident* at or above 99/100,
*probable* at or above 9/10, *uncertain* below.

The Lean half of the study proves what a floor promises
(``GLM.ConfidenceFloor.floor_error_le``: every answered read at least ``t``
sure means the answered reads are wrong with probability at most ``1 - t``) and
why overstating the rate is safe
(``GLM.ConfidenceFloor.floor_safe_overdeclared``).

Exactness
---------
``int`` masks and :class:`fractions.Fraction` only.  No float, no RNG.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, Sequence, Tuple

from .decoder_confidence import (ConfidenceRefusal, agree_confidence,
                                 decode_confidence)

__all__ = [
    "BANDS", "band", "floor_check", "graded_resolve", "graded_agree",
    "floor_resolve", "floor_agree",
]

#: The declared bands: ``(least confidence, word)``, highest first.
BANDS: Tuple[Tuple[Fraction, str], ...] = (
    (Fraction(999, 1000), "near-certain"),
    (Fraction(99, 100), "confident"),
    (Fraction(9, 10), "probable"),
    (Fraction(0), "uncertain"),
)


def band(confidence: Fraction) -> str:
    """The declared band word of a confidence."""
    for least, word in BANDS:
        if confidence >= least:
            return word
    return BANDS[-1][1]


def floor_check(t: object) -> Fraction:
    """The declared floor as a ``Fraction`` in ``(0, 1]``, or a refusal."""
    if isinstance(t, bool) or not isinstance(t, (int, Fraction)):
        raise ConfidenceRefusal("FLOOR_OUT_OF_RANGE",
                                "the confidence floor must be an exact "
                                "rational")
    t = Fraction(t)
    if not 0 < t <= 1:
        raise ConfidenceRefusal(
            "FLOOR_OUT_OF_RANGE",
            f"a confidence floor of {t} is outside (0, 1]: a floor at or "
            f"below 0 refuses nothing and one above 1 refuses everything")
    return t


def _graded(reading: Dict[str, object]) -> Dict[str, object]:
    out = dict(reading)
    out["band"] = band(reading["confidence"])
    return out


def graded_resolve(subject: int, p: object,
                   cases: Sequence[int]) -> Dict[str, object]:
    """``resolve`` with its confidence beside the answer: never refused on
    confidence, refused where ``resolve`` refuses."""
    if not cases:
        raise ConfidenceRefusal("UNCORRECTABLE", "resolve needs at least one "
                                "declared case")
    return _graded(decode_confidence(subject, p, list(cases)))


def graded_agree(reads: Sequence[int], p: object) -> Dict[str, object]:
    """``agree`` with its confidence beside the answer."""
    return _graded(agree_confidence(list(reads), p))


def _floored(reading: Dict[str, object], t: Fraction) -> Dict[str, object]:
    conf = reading["confidence"]
    if conf < t:
        raise ConfidenceRefusal(
            "BELOW_FLOOR", f"the answer is the codeword sent with probability "
            f"{conf} ({band(conf)}), below the declared floor {t}")
    out = _graded(reading)
    out["floor"] = t
    return out


def floor_resolve(subject: int, p: object, t: object,
                  cases: Sequence[int]) -> Dict[str, object]:
    """``resolve`` answered only at confidence ``>= t``."""
    t = floor_check(t)
    return _floored(graded_resolve(subject, p, cases), t)


def floor_agree(reads: Sequence[int], p: object,
                t: object) -> Dict[str, object]:
    """``agree`` answered only at confidence ``>= t``."""
    t = floor_check(t)
    return _floored(graded_agree(reads, p), t)
