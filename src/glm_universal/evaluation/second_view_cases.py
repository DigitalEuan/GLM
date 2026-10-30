"""``glm_universal.evaluation.second_view_cases`` -- the declared cases of Phase 96.

The probes and marks of ``studies/SECOND_VIEW_STUDY.md`` §2, written and
committed before :mod:`glm_universal.reasoning.second_view` existed.  Round 8
of the order of work in ``STATUS.md`` §3.4, *second readings*: J2 with H's
X1 (a second view of one carrier produced by the runtime rather than supplied
by the caller), then J1 (the composition of the context stage and a second
reading, declared and measured on a fresh probe), then J3 (the Leech
escalation on a soft channel whose reliabilities come from the machine's own
readings).

Nothing here is random (D7): every probe is a fixed stride or a full census.

* :data:`FRAMES` -- the declared frames of the framed register: view ``k``
  stores the codeword rotated down by ``k`` coordinates (package order,
  cyclic), and is read back by rotating up by ``k``.  A burst ``e`` that
  falls on the same stored positions of every view (a *common-mode* burst)
  is therefore read through view ``k`` as the error ``rot(e, k)``.
* :data:`PAIR_FRAMES` -- the two-view register of marks V1 and V6.
* :data:`CODEWORD_STRIDE` -- the codeword probe (X1's: 64 codewords at stride
  64 through the sorted 4,096).
* :data:`FRESH_CASE_OFFSET` / :data:`CASE_SIZES` -- mark V6's case sets
  ``S'_k``: the codewords at indices ``2 + j * floor(4096 / k)``, ``j < k``
  (Phase 65's K1 used offset 1, so no set is shared).
* :data:`SHARE_MARK` -- V6's answered share, required at every ``k``.
* :data:`DIALECT_CASES` -- ``(id, source)``: programs the dialect must answer
  equal to CPython with the prelude, column 3 verified.
* :data:`DIALECT_REFUSALS` -- ``(id, source, refusal name)``.
* :data:`SCOPED` -- figures seen while the frames were chosen, before this
  declaration; reported as such and never scored as a result.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["FRAMES", "PAIR_FRAMES", "CODEWORD_STRIDE", "FRESH_CASE_OFFSET",
           "CASE_SIZES", "SHARE_MARK", "DIALECT_CASES", "DIALECT_REFUSALS",
           "SCOPED", "MARKS"]

#: The framed register's three views (rotation offsets).
FRAMES: Tuple[int, ...] = (0, 1, 3)

#: The two-view register: the first two frames.
PAIR_FRAMES: Tuple[int, ...] = (0, 1)

#: X1's codeword probe: every 64th codeword of the sorted 4,096.
CODEWORD_STRIDE = 64

#: Mark V6: the fresh case sets start at index 2 (K1's started at 1).
FRESH_CASE_OFFSET = 2
CASE_SIZES: Tuple[int, ...] = (2, 4, 8, 16, 32)

#: Mark V6: the answered share required at every ``k`` (as a fraction).
SHARE_MARK = (99, 100)

#: Figures computed while the frames were scoped, before this file was
#: written.  The search that chose the frames counted, over all 10,626
#: weight-4 bursts, how many leave an octad through the union of the errors
#: the views read: one second frame at offset 1 leaves 174; the frames
#: (0, 1, 3) leave none; the mirror frames (0, -1, -3) leave 2.  They are
#: reported in the study as the scoping search, not as results.
SCOPED: Dict[str, int] = {
    "pair_open_bursts": 174,
    "triple_open_bursts": 0,
    "mirror_triple_open_bursts": 2,
}

#: The declared marks, by name; the study's §2 states each in full.
MARKS: Tuple[str, ...] = (
    "V1 two views: the live count of every common-mode burst is predicted",
    "V2 three views: every common-mode weight-4 burst resolved, 0 wrong",
    "V3 one second frame never suffices: every single frame leaves a burst",
    "V4 X1 through the register: 4,224 of 4,224 independent double reads",
    "V5 inside the packing radius: every burst of weight <= 3 answered right",
    "V6 composition on a fresh probe: 0 wrong, open count as predicted, "
    ">= 99 % at every k",
    "V7 the soft channel of the views: the escalation equals the "
    "intersection on every read",
    "V8 the dialect: declared programs equal CPython, scripts verified, "
    "mutants rejected",
    "V9 no regression: the carried-fork figures and the Python cases",
)

#: Mark V8.  ``c`` below is ``golay_encode(1234)``; every program is closed.
DIALECT_CASES: Tuple[Tuple[str, str], ...] = (
    ("views-clean",
     "read_views(*store_views(golay_encode(1234)))"),
    ("views-burst",
     "e = 0b1111\n"
     "w = store_views(golay_encode(1234))\n"
     "read_views(w[0] ^ e, w[1] ^ e, w[2] ^ e)"),
    ("views-burst-spread",
     "e = (1 << 0) | (1 << 5) | (1 << 11) | (1 << 17)\n"
     "w = store_views(golay_encode(77))\n"
     "read_views(w[0] ^ e, w[1] ^ e, w[2] ^ e) == golay_encode(77)"),
    ("views-small",
     "w = store_views(golay_encode(4095))\n"
     "read_views(w[0] ^ 0b111, w[1] ^ 0b111, w[2] ^ 0b111)"),
    ("views-count",
     "len(store_views(golay_encode(9)))"),
    ("views-two",
     "w = store_views(golay_encode(300))\n"
     "read_views(w[0] ^ 0b100010001, w[1] ^ 0b100010001)"),
)

#: Mark V8's refusals: no view, more views than frames, a stored value
#: that is not a codeword.
DIALECT_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("views-none", "read_views()", "PYTHON_ERROR"),
    ("views-too-many",
     "w = store_views(golay_encode(1))\n"
     "read_views(w[0], w[1], w[2], w[0])", "PYTHON_ERROR"),
    ("views-not-codeword", "store_views(1)", "OUTSIDE_SUBSTRATE"),
)
