"""``glm_universal.knowledge.friction_survey`` -- the seven perturbations.

Phase 156's seven declared perturbations of the evaluation's 222 cases
(``qmark``, ``capital``, ``spaces``, ``please``, ``tellme``, ``typo``,
``drop_the``), scored hold/stick/slip, and the re-scoring of stepwise-
planner ``REFUSED`` lines as refusals.

*Reconstructed 29 October 2026 (Iteration 4 of the reorganisation).  The
original ``friction_survey.py`` was lost in the upload; this version is a
minimal stub.  The :data:`PERTURBATIONS` constant is faithful (the seven
names); the ``survey`` and ``rescore_refused`` functions return empty
results.*
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

__all__ = ["PERTURBATIONS", "perturb", "_typo", "survey", "rescore_refused"]


#: The seven declared perturbations.  This constant is faithful.
PERTURBATIONS: Tuple[str, ...] = (
    "qmark",      # add a trailing question mark
    "capital",    # capitalise the first letter
    "spaces",     # collapse multiple spaces
    "please",     # prefix with "please "
    "tellme",     # prefix with "tell me "
    "typo",       # introduce a single transposition
    "drop_the",   # drop the first "the"
)


def perturb(text: str, pid: str) -> str:
    """Apply perturbation ``pid`` to ``text``.

    *Stub:* returns ``text`` unchanged.
    """
    return text


def _typo(text: str) -> str:
    """The ``typo`` perturbation: a single transposition.

    *Stub:* returns ``text`` unchanged.
    """
    return text


def survey(cases: Any = None, jobs: int = 8) -> Dict[str, Any]:
    """Run the seven perturbations over ``cases`` (default: the evaluation
    cases), scored hold/stick/slip.

    *Stub:* returns ``{"cases": 0, "base_passing": 0, "by_perturbation": {}}``.
    """
    return {"cases": 0, "base_passing": 0, "by_perturbation": {}}


def rescore_refused(runs: Any) -> Dict[str, Any]:
    """Re-score stepwise-planner ``REFUSED`` lines as refusals.

    *Stub:* returns ``{}``.
    """
    return {}
