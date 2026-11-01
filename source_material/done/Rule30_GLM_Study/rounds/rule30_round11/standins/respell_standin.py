"""STAND-IN for ``glm_universal/runtime/respell.py`` (Round 11, not the owner's module).

``GLM.py -q`` imports ``respell`` and ``sinter`` on every question.  This stand-in reports
the respelling as switched off (``enabled() -> False``), so ``-q`` answers exactly as the
routed reading does and a refused question stays refused: no respelt second reading.
Replace with the real module (Phase 157, FRICTION_TWO_STUDY.md) from the GLM tree.
"""


def enabled() -> bool:
    return False
