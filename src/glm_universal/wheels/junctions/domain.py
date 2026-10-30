"""Phase-157 domain junctions between W01-W15.

The ten declared junctions and four non-identities from
``studies/DOMAIN_WHEELS_STUDY.md`` §2.3, plus the two aliases from §2.3.

The W09/W13 junction uses rule B (``rate_only``: ``frequency`` joined,
``angle`` split) per Phase 158's ``OSCILLATOR_JUNCTION_STUDY.md``.  See
:mod:`glm_universal.wheels.junctions.oscillator` for the four variants.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["JUNCTIONS", "NON_IDENTITIES", "ALIASES"]


#: The ten Phase-157 junctions.  Each entry maps a sorted pair of wheel
#: ids to the tuple of shared carrier names.
#:
#: Note: the W09/W13 junction joins ``frequency`` only (rule B, Phase 158).
#: The original Phase-157 declaration also joined ``angle``; Phase 158
#: split it and recorded the split as a non-identity (see below).
JUNCTIONS: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("W5", "W11"): ("velocity",),       # the moving body's velocity
    ("W5", "W12"): ("mass",),           # the body whose density is read
    ("W6", "W12"): ("area",),           # the flow's cross-section
    ("W11", "W12"): ("length",),        # the length the fluid moves
    ("W9", "W13"): ("frequency",),      # rule B: frequency joined, angle split
    ("W5", "W13"): ("mass",),           # the oscillating body is the dynamic body
    ("W3", "W14"): ("capacitance",),    # the LC circuit's capacitor
    ("W1", "W14"): ("current",),        # the inductor's current
    ("W1", "W15"): ("current", "power"),  # charge and energy carried by the circuit
    ("W3", "W15"): ("charge",),         # the charge moved is the charge stored
}


#: The four declared non-identities (pairs of wheels that share a name
#: but where the identification is refused, with the reason).
#:
#: The W13/W14 ``angular_frequency`` non-identity is the
#: mechanical-oscillator-against-electrical-oscillator refusal.  The
#: W09/W13 ``angle`` non-identity is the Phase-158 split (rule B).
NON_IDENTITIES: Dict[Tuple[str, str], str] = {
    ("W13", "W14"): "a mechanical oscillator against an electrical one "
                    "(angular_frequency)",
    ("W3", "W14"): "the capacitor's stored energy against the inductor's "
                   "(energy)",
    ("W3", "W15"): "the energy stored in a capacitor against the energy "
                   "delivered over a time (energy)",
    ("W11", "W15"): "a travel time against a charging time (time)",
    # Phase-158 split: W09/W13 angle is split under rule B.
    ("W9", "W13"): "the wave's angle against the oscillator's angle: "
                   "rule B splits angle, joining frequency only (Phase 158)",
}


#: The two aliases: names that map to another name before the junction
#: table is consulted.
ALIASES: Dict[str, str] = {
    "speed": "velocity",
    "distance": "length",
}
