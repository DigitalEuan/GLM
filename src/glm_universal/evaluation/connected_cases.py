"""``glm_universal.evaluation.connected_cases`` -- the declared questions of the
connected-machine round.

Written and committed before :mod:`glm_universal.runtime.router`,
:mod:`glm_universal.runtime.toolbox` and :mod:`glm_universal.engineering.union`
existed (``studies/CONNECTED_MACHINE_STUDY.md`` §2).

* :data:`UNION_QUESTIONS` -- questions for the *across wheels* mode of the
  engineering surface, each with the formula it must give or the word
  ``refuse``.
* :data:`UNION_LABELS` -- the physics label of each formula family of §2.3:
  ``True`` for a law of the wheels' domain, ``False`` for a formula naive
  composition reaches by conflating two measurands.
* :data:`TOOL_QUESTIONS` -- ``tool <name>`` questions, one per module the
  wiring audit found unreached, with a fragment the answer must contain.
* :data:`ROUTED_MIXED` -- text of each kind, with the surface that must read
  it.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["UNION_QUESTIONS", "UNION_LABELS", "TOOL_QUESTIONS",
           "ROUTED_MIXED", "JUNCTIONS_DECLARED"]


#: ``(key, question, expected)``: ``expected`` is the formula text, or
#: ``"refuse"``.
UNION_QUESTIONS: Tuple[Tuple[str, str, str], ...] = (
    ("u-hydraulic", "derive power from pressure and volume flow rate "
                    "across wheels", "pressure * volume_flow_rate"),
    ("u-hydraulic-p", "derive pressure from power and volume flow rate "
                      "across wheels", "power / volume_flow_rate"),
    ("u-hydraulic-q", "derive volume flow rate from power and pressure "
                      "across wheels", "power / pressure"),
    ("u-in-wheel", "derive power from voltage and resistance across wheels",
     "voltage^2 / resistance"),
    ("u-in-wheel-2", "derive momentum from mass and velocity across wheels",
     "mass * velocity"),
    ("u-emc2", "derive energy from mass and speed of light across wheels",
     "refuse"),
    ("u-v2c", "derive velocity from mass and speed of light across wheels",
     "refuse"),
    ("u-thermal", "derive velocity from specific heat capacity and "
                  "temperature across wheels", "refuse"),
    ("u-z-r", "derive impedance from current and resistance across wheels",
     "refuse"),
    ("u-photon-q", "derive volume flow rate from area and speed of light "
                   "across wheels", "refuse"),
    ("u-unknown", "derive happiness from mass and velocity across wheels",
     "refuse"),
    ("u-debroglie", "derive momentum from planck constant and wavelength "
                    "across wheels", "refuse"),
)

#: The formula families of §2.3, keyed by the target and the formula text the
#: exact solver renders, with the physics label.
UNION_LABELS: Dict[Tuple[str, str], bool] = {
    ("power", "pressure * volume_flow_rate"): True,
    ("pressure", "power / volume_flow_rate"): True,
    ("volume_flow_rate", "power / pressure"): True,
}

#: The junctions of §2.1: ``(wheel, wheel) -> names identified``.
JUNCTIONS_DECLARED: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("W5", "W6"): ("force", "velocity"),
    ("W5", "W8"): ("mass",),
    ("W1", "W3"): ("voltage",),
    ("W4", "W9"): ("angular_velocity",),
    ("W9", "W10"): ("frequency",),
}

#: ``(question, fragment the answer must contain)``.
TOOL_QUESTIONS: Tuple[Tuple[str, str], ...] = (
    ("tool moonshine", "196884"),
    ("tool llvq", "196560"),
    ("tool pcgs", "admitted"),
    ("tool salvage", "Lightspeed.lean"),
    ("tool salvage second", "Cube/Surface.lean"),
    ("tool deep dive", "37800"),
    ("tool tie break GLM.Address.Quantiser", "tie class"),
    ("tool stability GLM.Address.Quantiser", "radius"),
)

#: ``(text, surface that must read it)``.
ROUTED_MIXED: Tuple[Tuple[str, str], ...] = (
    ("tools", "toolbox"),
    ("tool moonshine", "toolbox"),
    ("Fraction(1, 3) + Fraction(1, 6)", "python"),
    ("x = 5\nx << 3", "python"),
    ("golay_encode(5) ^ golay_encode(3)", "python"),
    ("derive power from voltage and resistance", "engineering"),
    ("derive power from pressure and volume flow rate across wheels",
     "engineering"),
    ("what is energy", "planner"),
    ("what is 2 + 2", "planner"),
    ("address of golay", "planner"),
    ("golay", "planner"),
)
