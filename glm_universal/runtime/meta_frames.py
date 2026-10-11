"""``glm_universal.runtime.meta_frames`` -- questions about the GLM's own
engineering, answered from the project's own documents (Phase 117, track M
of ``studies/QUESTION_SET_B_STUDY.md`` §8; the study is
``studies/META_QUESTIONS_STUDY.md``).

The topics, their evidence and their column-3 checks are
:mod:`glm_universal.reasoning.meta_evidence`; this module puts one frame
per topic on the router's ``frames`` surface.  A frame reads a question
that names the machine (the GLM, *your benchmark*, *the system*, a refusal
code, the TCT columns) and meets its topic's cue; the frames are tried
after every other frame, so they read only text no other frame reads, and
``question_frames.META = False`` takes them off.
"""

from __future__ import annotations

from typing import Optional, Tuple

from ..reasoning import meta_evidence as ME
from .question_frames import Frame, Reading

__all__ = ["META_FRAMES", "reading_of", "read_topic", "mutated"]


def reading_of(ans: ME.Answer) -> Reading:
    """The frame layer's :class:`Reading` of an evidence answer."""
    return Reading(f"meta_{ans.topic}", ans.answered, ans.value, ans.column1,
                   ans.column2, ans.script, code=ans.code,
                   backing=ans.backing, disputes=ans.disputes)


def read_topic(tp: ME.Topic, text: str) -> Reading:
    return reading_of(ME.read_topic(tp, text))


def mutated(tp: ME.Topic, text: str, kind: str) -> Reading:
    return reading_of(ME.mutated(tp, text, kind))


def _frame(tp: ME.Topic) -> Frame:
    def match(t: str, tp=tp) -> Optional[dict]:
        return {"topic": tp.key, "text": t} if ME.topic_of(t) is tp else None

    def answer(g: dict, tp=tp) -> Reading:
        return read_topic(tp, g["text"])
    return Frame(f"meta_{tp.key}", f"meta question: {tp.key}", match, answer,
                 source="M")


#: One frame per topic, tried after every other frame.
META_FRAMES: Tuple[Frame, ...] = tuple(_frame(tp) for tp in ME.TOPICS)
