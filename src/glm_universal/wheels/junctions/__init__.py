"""``glm_universal.wheels.junctions`` -- the declared wheel junctions.

Three junction tables, one per phase of the wheel studies:

  * :mod:`phase66` -- the five Phase-66 junctions between W01-W10.
  * :mod:`domain` -- the ten Phase-157 junctions between W01-W15, plus
    four non-identities and two aliases.
  * :mod:`oscillator` -- the four variants of the W09/W13 junction
    (A/B/C/D), with B (``rate_only``) as the shipped choice.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

__all__ = ["phase66", "domain", "oscillator"]
