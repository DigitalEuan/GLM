"""``glm_universal.runtime.explanation_frames`` -- the outside questions that
ask *why*, answered where a register or an exact derivation decides them
(Phase 120, track E of ``studies/QUESTION_SET_B_STUDY.md`` §8; the study is
``studies/EXPLANATION_ANCHOR_STUDY.md``).

The topics, their anchors and their column-3 checks are
:mod:`glm_universal.reasoning.explanation_anchors`; this module puts one
frame per topic on the router's ``frames`` surface.  A frame reads a
question whose cue words meet its topic; the frames are tried after every
other frame (the meta frames included), so they read only text no other
frame reads, and ``question_frames.EXPLANATIONS = False`` takes them off.
"""

from __future__ import annotations

from typing import Optional, Tuple

from ..reasoning import explanation_anchors as EA
from .question_frames import Frame, Reading

__all__ = ["EXPLANATION_FRAMES", "reading_of", "read_topic", "mutated"]


def reading_of(ans: EA.Answer) -> Reading:
    """The frame layer's :class:`Reading` of an explanation answer."""
    return Reading(f"explain_{ans.topic}", ans.answered, ans.value,
                   ans.column1, ans.column2, ans.script, code=ans.code,
                   backing=ans.backing, disputes=ans.disputes)


def read_topic(tp: EA.Topic, text: str = "") -> Reading:
    return reading_of(EA.read_topic(tp, text))


def mutated(tp: EA.Topic, kind: str) -> Optional[Reading]:
    ans = EA.mutated(tp, kind)
    return None if ans is None else reading_of(ans)


def _frame(tp: EA.Topic) -> Frame:
    def match(t: str, tp=tp) -> Optional[dict]:
        return {"topic": tp.key, "text": t} if EA.topic_of(t) is tp else None

    def answer(g: dict, tp=tp) -> Reading:
        return read_topic(tp, g["text"])
    return Frame(f"explain_{tp.key}", f"explanation anchored: {tp.key}",
                 match, answer, source="E")


#: One frame per topic, tried after every other frame.
EXPLANATION_FRAMES: Tuple[Frame, ...] = tuple(_frame(tp) for tp in EA.TOPICS)
