"""``glm_universal.runtime.comparatives`` -- the declared comparatives.

*Created 31 October 2026 (repository check).  The table was* ``COMPARATIVES``
*of* :mod:`glm_universal.runtime.declared_frames` *(round three of the stepwise
planner), which still re-exports it, unchanged.  It is held in a module of its
own because* :mod:`glm_universal.reasoning.stepwise_script` *needs only this
table (its word-lie), and importing the frames module for it put the router,
the toolbox and the Lean address book's walk of the whole development into
the import closure of every module that builds a stepwise chain -- among them
the session's field gate* (:mod:`glm_universal.reasoning.typed_ladder`)*,
which* ``tests/test_signoff.py`` *forbids (building a session does not take
the whole development).*
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["COMPARATIVES"]

#: ``word -> (register phrase, direction, gloss)``.  Direction ``>`` names
#: the row with the larger value, ``<`` the row with the smaller.
COMPARATIVES: Dict[str, Tuple[str, str, str]] = {
    "heavier": ("atomic weight", ">", "the larger standard atomic weight"),
    "lighter": ("atomic weight", "<", "the smaller standard atomic weight"),
    "denser": ("density", ">", "the larger density at standard state"),
    "older": ("year discovered", "<",
              "the earlier recorded year of discovery"),
    "newer": ("year discovered", ">",
              "the later recorded year of discovery"),
}
