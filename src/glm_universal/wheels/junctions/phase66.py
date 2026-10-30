"""Phase-66 junctions between W01-W10.

Transcribed faithfully from :mod:`glm_universal.engineering.union`
(lines 60-77), which itself transcribes ``studies/CONNECTED_MACHINE_STUDY.md``
§2.1.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["JUNCTIONS", "NON_IDENTITIES"]


#: The five Phase-66 junctions.  Each entry maps a sorted pair of wheel
#: ids to the tuple of shared carrier names.
JUNCTIONS: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("W5", "W6"): ("force", "velocity"),
    ("W5", "W8"): ("mass",),
    ("W1", "W3"): ("voltage",),
    ("W4", "W9"): ("angular_velocity",),
    ("W9", "W10"): ("frequency",),
}


#: The three Phase-66 non-identities.
NON_IDENTITIES: Dict[Tuple[str, str], str] = {
    ("W1", "W2"): ("DC values against sinusoidal amplitudes: identifying "
                   "them makes resistance equal impedance"),
    ("W5", "W8"): "kinetic energy against stored heat",
    ("W5", "W10"): "a massive, non-relativistic body against a photon",
}
