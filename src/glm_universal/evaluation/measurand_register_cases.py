"""``glm_universal.evaluation.measurand_register_cases`` -- the measurand
register: the declared corpus.

The declared corpus of ``studies/MEASURAND_REGISTER_STUDY.md`` (Phase 87),
written and committed before any code of the round.  Every expected answer
was worked by hand, in exact fractions, from:

* the element register's own values (the first ionization energy of hydrogen
  ``13.598 eV``, the electron affinity of chlorine ``3.617 eV``, the atomic
  radius of iron ``194 pm``, the melting point of iron ``1811 K``);
* the exact defining constants of the SI (9th edition, 2019):
  ``h = 6.62607015e-34 J s``, ``c = 299792458 m/s`` and
  ``e = 1.602176634e-19 C``, so that ``1 eV = e J`` exactly;
* the axioms of the ten formula wheels
  (:data:`glm_universal.engineering.wheels.WHEELS`) under the junction table
  of :mod:`glm_universal.engineering.union`;
* the declared conversion laws of the round: a stated efficiency ``eta`` with
  ``0 < eta <= 1`` relating the power out of a conversion to the power in
  (``P_out = eta * P_in``), for a motor (DC electrical power in, shaft power
  out), a generator (shaft in, DC electrical out), a pump (shaft in, the
  hydraulic power ``force * velocity`` of the fluid column out) and a turbine
  (hydraulic in, shaft out).

Three groups:

* :data:`REGISTER_CASES` -- a register value read through its **measurand**:
  a first ionization energy is the least energy one photon must carry to
  ionize the free atom, an electron affinity the least energy one photon must
  carry to detach the extra electron from the anion, so read by name each is
  a photon's energy (``energy`` of wheel W10), per atom, in joules.  A radius
  is a length and is *not* a wavelength by name; written ``wavelength = ...``
  the question identifies the two, which is the asker's to do.
* :data:`CONVERSION_CASES` -- a conversion through a stated efficiency as a
  law of its own, across the non-identities the junction table declares.
* :data:`CHARGE_CASES` -- the elementary charge as an exact unit of charge.

An expected verdict is ``("ANSWER", value)``, ``("AMBIGUOUS",)`` or
``("REFUSED", NAME)``; a value is in the coherent SI unit unless a unit is
asked for.  Nothing in an earlier corpus is amended by this round.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["REGISTER_CASES", "CONVERSION_CASES", "CHARGE_CASES",
           "NEW_REFUSAL_NAMES", "NAIVE_WRONG_AT_LEAST",
           "UNRESTRICTED_WRONG"]

Verdict = Tuple[str, ...]

#: The named refusals this round adds.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "EFFICIENCY_OUT_OF_RANGE",  # a stated or derived efficiency not in (0, 1]
    "EFFICIENCY_UNDECLARED",    # an efficiency that names no declared law
)

#: Mark R4: the naive control -- the conversion read as an identity (the
#: shared name ``power`` identified across the wheels, the efficiency
#: dropped) -- must answer at least this many of the answered conversion
#: cases, each wrongly.
NAIVE_WRONG_AT_LEAST = 6

#: Mark R4: the case the measurand's wheel restriction refuses and the
#: unrestricted reading (a register energy fed to every wheel's ``energy``)
#: answers, wrongly.
UNRESTRICTED_WRONG: Tuple[str, ...] = ("r09",)

# (id, question, expected verdict)
REGISTER_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("r01", "given the ionization energy of hydrogen, what is the frequency",
     ("ANSWER", "145242652460880000000000/44173801")),
    ("r02", "given the electron affinity of chlorine, what is the frequency",
     ("ANSWER", "38633819234520000000000/44173801")),
    ("r03", "given the ionization energy of hydrogen and wave speed = "
            "299792458, what is the wavelength in nanometres",
     ("ANSWER", "6621486190496429/72621326230440")),
    ("r04", "given energy = the ionization energy of hydrogen, what is the "
            "frequency", ("ANSWER", "145242652460880000000000/44173801")),
    ("r05", "given the electron affinity of helium, what is the frequency",
     ("REFUSED", "VALUE_MISSING")),
    ("r06", "given the covalent radius of carbon and frequency = 5, what is "
            "the wave speed", ("REFUSED", "UNKNOWN_QUANTITY")),
    ("r07", "given wavelength = the atomic radius of iron and frequency = 5, "
            "what is the wave speed", ("ANSWER", "97/100000000000")),
    ("r08", "given the melting point of iron and entropy = 2, what is the "
            "energy", ("ANSWER", "3622")),
    ("r09", "given the ionization energy of hydrogen, mass = 2 and specific "
            "heat capacity = 450, what is the temperature",
     ("REFUSED", "NO_DERIVATION")),
    ("r10", "given temperature = the ionization energy of hydrogen and "
            "entropy = 2, what is the energy", ("REFUSED", "UNIT_MISMATCH")),
    ("r11", "given the electronegativity of fluorine, what is the frequency",
     ("REFUSED", "SCALE_UNDECLARED")),
    ("r12", "given energy = the ionization energy of hydrogen, mass = 2 and "
            "specific heat capacity = 450, what is the temperature",
     ("ANSWER", "605177718587/250000000000000000000000000000000")),
)

CONVERSION_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("e01", "given voltage = 230 volts, current = 2 amperes, motor "
            "efficiency = 9/10 and angular velocity = 100, what is the "
            "torque", ("ANSWER", "207/50")),
    ("e02", "given torque = 3, angular velocity = 50 and generator "
            "efficiency = 4/5, what is the power", ("AMBIGUOUS",)),
    ("e03", "given torque = 3, angular velocity = 50, generator efficiency = "
            "4/5 and voltage = 12, what is the current", ("ANSWER", "10")),
    ("e04", "given pressure = 200000 pascals, area = 1/100 square metres, "
            "velocity = 3/10 metres per second, pump efficiency = 3/4 and "
            "angular velocity = 150, what is the torque", ("ANSWER", "16/3")),
    ("e05", "given force = 5000 newtons, velocity = 2, turbine efficiency = "
            "9/10 and angular velocity = 300, what is the torque",
     ("ANSWER", "30")),
    ("e06", "given voltage = 230 volts, current = 2 amperes, torque = 4 and "
            "angular velocity = 100, what is the motor efficiency",
     ("ANSWER", "20/23")),
    ("e07", "given voltage = 12 volts, current = 2 amperes, torque = 1 and "
            "angular velocity = 30, what is the motor efficiency",
     ("REFUSED", "EFFICIENCY_OUT_OF_RANGE")),
    ("e08", "given voltage = 230 volts, current = 2 amperes, motor "
            "efficiency = 6/5 and angular velocity = 100, what is the torque",
     ("REFUSED", "EFFICIENCY_OUT_OF_RANGE")),
    ("e09", "given voltage = 230 volts, current = 2 amperes, efficiency = "
            "9/10 and angular velocity = 100, what is the torque",
     ("REFUSED", "EFFICIENCY_UNDECLARED")),
    ("e10", "given voltage = 230 volts, current = 2 amperes and angular "
            "velocity = 100, what is the torque", ("REFUSED", "NO_DERIVATION")),
    ("e11", "given voltage = 230 volts, current = 2 amperes, motor "
            "efficiency = 0 and angular velocity = 100, what is the torque",
     ("REFUSED", "EFFICIENCY_OUT_OF_RANGE")),
    ("e12", "given voltage = 230 volts, current = 2 amperes, motor "
            "efficiency = 90 percent and angular velocity = 100, what is the "
            "torque", ("ANSWER", "207/50")),
    ("e13", "given voltage = 230 volts, current = 2 amperes, motor "
            "efficiency = 9/10 and angular velocity = 100, what is the torque "
            "in millinewton metres", ("ANSWER", "4140")),
    ("e14", "given torque = 3, angular velocity = 50, generator efficiency = "
            "4/5 and current = 4 amperes, what is the voltage",
     ("ANSWER", "30")),
)

CHARGE_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("c01", "given charge = 3 elementary charges and capacitance = 2 "
            "picofarads, what is the voltage",
     ("ANSWER", "2403264951/10000000000000000")),
    ("c02", "given charge = 1 elementary charge and voltage = 1 volt, what is "
            "the energy in electronvolts", ("ANSWER", "1/2")),
    ("c03", "given voltage = 5 volts and capacitance = 8 picofarads, what is "
            "the charge in elementary charges",
     ("ANSWER", "200000000000000000/801088317")),
    ("c04", "given voltage = 2 elementary charges and capacitance = 1, what "
            "is the charge", ("REFUSED", "UNIT_MISMATCH")),
)
