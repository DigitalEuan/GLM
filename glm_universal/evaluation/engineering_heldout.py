"""``glm_universal.evaluation.engineering_heldout`` -- the engineering set.

Why this exists
---------------
The formula-wheel session record
(``source_material/formula_wheel/GLM_formula_wheel_study_session_record.md``)
asks whether the GLM can reason in electrical and mechanical terms: build a
formula wheel from its axioms, reject a formula that does not follow, move a
load onto the Smith chart, carry a problem from a spring to a circuit and
back, and say what a delta-sigma loop does with a rational or an irrational
input.  Its own figures (41/41, 16/16, 6/6) measure a standalone script
against its own expectations; none of them measures a question put to the
machine in words.

This set is that measurement's control.  It was written **before** the
engineering surface (:mod:`glm_universal.engineering`) existed and committed
on its own, so that the commit is the pre-registration: nothing below was
edited after the surface was first run against it.  Every label is written
from textbook physics and circuit theory -- Ohm's law, the reflection
coefficient ``(Z - Z0)/(Z + Z0)``, the force-voltage and force-current
analogies, ``omega0 = sqrt(k/m)`` -- and not read off any register.

The scoring rule
----------------
Stricter than :func:`glm_universal.evaluation.heldout.score_answer`, because
an engineering answer that names one term of three is not right.  ``expect``
is a tuple of *groups*; each group is a tuple of lowercase alternatives; a
right answer contains at least one alternative **of every group**.  ``None``
means the right outcome is a refusal.

* answered, every group present -- **correct**;
* answered, some group absent -- **wrong**;
* answered where ``expect`` is ``None`` -- **wrong**;
* declined where ``expect`` is ``None`` -- **correct refusal**;
* declined where ``expect`` is not ``None`` -- **refused**.

``wrong`` is the count that matters, reported beside safe coverage and never
folded into it.  The ``faculty`` column says in advance what a right answer
would be worth under directive D15 -- ``derive`` (no register holds the
answer), ``address`` (the answer is recovered by structure from a stored key
that is not the query) or ``table`` -- so that a round cannot relabel its
gains after the fact.

Exact and float-free: the module holds strings only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

__all__ = [
    "EngQuestion", "WHEELS", "CHECKS", "SMITH", "ANALOGY", "DELTA_SIGMA",
    "TRICKS", "PARAPHRASES", "STRESS", "STRESS_FIRST_RUN",
    "BASELINE_FIRST_RUN", "ALL_SETS", "score_engineering",
]


@dataclass(frozen=True)
class EngQuestion:
    """One held-out engineering question and what a right answer says."""

    key: str
    question: str
    expect: Optional[Tuple[Tuple[str, ...], ...]]
    faculty: str
    note: str = ""


def _q(key: str, question: str, *groups, faculty: str = "derive",
       note: str = "") -> EngQuestion:
    norm = tuple(tuple(a.lower() for a in (g if isinstance(g, tuple) else (g,)))
                 for g in groups)
    return EngQuestion(key, question, norm or None, faculty, note)


def _refuse(key: str, question: str, note: str,
            faculty: str = "refuse") -> EngQuestion:
    return EngQuestion(key, question, None, faculty, note)


#: Formula-wheel derivations: a target from two named quantities, under the
#: declared axioms of the wheel the quantities belong to.
WHEELS: Tuple[EngQuestion, ...] = (
    _q("w-ohm-p-vr", "derive power from voltage and resistance",
       "voltage^2 / resistance"),
    _q("w-ohm-p-ir", "derive power from current and resistance",
       "current^2 * resistance"),
    _q("w-ohm-i-pv", "derive current from power and voltage",
       "power / voltage"),
    _q("w-ohm-r-pi", "derive resistance from power and current",
       "power / current^2"),
    _q("w-ohm-v-pr", "derive voltage from power and resistance",
       ("(power * resistance)^(1/2)", "(resistance * power)^(1/2)")),
    _q("w-ohm-wheel-p", "complete the formula wheel for power",
       "voltage * current", "current^2 * resistance",
       "voltage^2 / resistance",
       note="the three textbook forms, all required"),
    _q("w-rot-p", "derive power from torque and angular velocity",
       ("torque * angular_velocity", "angular_velocity * torque")),
    _q("w-rot-alpha", "derive angular acceleration from torque and moment "
                      "of inertia", "torque / moment_of_inertia"),
    _q("w-lin-ke", "derive energy from momentum and mass",
       "1/2 * momentum^2 / mass"),
    _q("w-cap-e", "derive energy from charge and capacitance",
       "1/2 * charge^2 / capacitance"),
    _q("w-ac-i", "derive acoustic intensity from acoustic pressure and "
                 "acoustic impedance",
       "acoustic_pressure^2 / acoustic_impedance"),
    _q("w-fluid-v", "derive velocity from volume flow rate and area",
       "volume_flow_rate / area"),
)

#: Dimensional checks, read at the two layers the register keeps.
CHECKS: Tuple[EngQuestion, ...] = (
    _q("c-tau-iw", "is torque = moment_of_inertia * angular_velocity "
                   "dimensionally consistent?", ("inconsistent", "not")),
    _q("c-p-v2r", "is power = voltage^2 / resistance dimensionally "
                  "consistent?", "consistent"),
    _q("c-p-fa", "is pressure = force * area dimensionally consistent?",
       ("inconsistent", "not")),
    _q("c-e-hf", "is energy = planck_constant / frequency dimensionally "
                 "consistent?", ("inconsistent", "not")),
    _q("c-w-f", "is angular_velocity = frequency dimensionally consistent?",
       "si7", "ext10",
       note="consistent in SI, inconsistent with an explicit angle axis: a "
            "right answer names both layers"),
    _q("c-z-vi", "is impedance = voltage * current dimensionally "
                 "consistent?", ("inconsistent", "not")),
)

#: The Smith chart: normalisation, reflection, VSWR, reflected power.
SMITH: Tuple[EngQuestion, ...] = (
    _q("s-g-100", "what is the reflection coefficient of a 100 ohm load on "
                  "a 50 ohm line?", "1/3"),
    _q("s-g-25", "reflection coefficient of a 25 ohm load on a 50 ohm line",
       "-1/3"),
    _q("s-g-cx", "reflection coefficient of a 25+25j ohm load on a 50 ohm "
                 "line", "-1/5", "2/5"),
    _q("s-vswr-100", "what is the vswr of a 100 ohm load on a 50 ohm line?",
       "vswr = 2"),
    _q("s-vswr-25", "vswr of a 25 ohm load on a 50 ohm line", "vswr = 2"),
    _q("s-pr-150", "what fraction of power is reflected by a 150 ohm load "
                   "on a 50 ohm line?", "1/4"),
    _q("s-z-75", "normalized impedance of a 75 ohm load on a 50 ohm line",
       "3/2"),
    _q("s-inv", "what load impedance gives a reflection coefficient of 1/3 "
                "on a 50 ohm line?", "100"),
    _q("s-short", "reflection coefficient of a short circuit on a 50 ohm "
                  "line", "-1"),
    _q("s-matched", "reflection coefficient of a 50 ohm load on a 50 ohm "
                    "line", ("= 0", "is 0", " 0 ")),
    _q("s-active", "is a load with reflection coefficient 1+1j passive?",
       ("not passive", "active")),
)

#: Electro-mechanical analogies and the cross-domain questions they license.
ANALOGY: Tuple[EngQuestion, ...] = (
    _q("a-fv-l", "in the force-voltage analogy, what is the mechanical "
                 "analogue of inductance?", "mass", faculty="address"),
    _q("a-fi-c", "in the force-current analogy, what is the mechanical "
                 "analogue of capacitance?", "mass", faculty="address"),
    _q("a-fv-r", "in the force-voltage analogy, what is the electrical "
                 "analogue of damping coefficient?", "resistance",
       faculty="address"),
    _q("a-fv-k", "in the force-voltage analogy, what is the electrical "
                 "analogue of spring constant?",
       ("1/capacitance", "1 / capacitance", "elastance"), faculty="address"),
    _q("a-tr-p", "translate power = current^2 * resistance into mechanics "
                 "under the force-voltage analogy",
       "velocity^2 * damping_coefficient"),
    _q("a-tr-e", "translate energy = 1/2 * capacitance * voltage^2 into "
                 "mechanics under the force-voltage analogy",
       "1/2 * force^2 / spring_constant"),
    _q("a-w0-mk", "resonant angular frequency of a 4 kg mass on a 100 N/m "
                  "spring", ("= 5 rad/s", "5 rad/s")),
    _q("a-w0-lc", "resonant angular frequency of a 1/4 henry inductor and a "
                  "1 farad capacitor", ("= 2 rad/s", "2 rad/s")),
    _q("a-w0-irr", "resonant angular frequency of a 2 kg mass on a 1 N/m "
                   "spring", ("(1/2)^(1/2)", "sqrt(1/2)", "sqrt(2)/2")),
    _q("a-q-rlc", "quality factor of a series rlc circuit with 2 ohm, "
                  "1 henry and 1/4 farad", ("q = 1", "= 1 ")),
    _q("a-zeta", "damping ratio of a 1 kg mass, 4 N/m spring and 2 N s/m "
                 "damper", ("1/2",)),
)

#: Delta-sigma: the first-order loop on rational and irrational inputs.
DELTA_SIGMA: Tuple[EngQuestion, ...] = (
    _q("d-bits-13", "delta-sigma bits of 1/3 over 6 steps", "001001"),
    _q("d-period-38", "what is the delta-sigma period of dc input 3/8?",
       "period 8"),
    _q("d-avg-27", "delta-sigma average of 2/7 after 7 steps", "2/7"),
    _q("d-irr", "is the delta-sigma bitstream of sqrt(2) - 1 periodic?",
       ("never periodic", "not periodic", "aperiodic")),
    _q("d-period-12", "what is the delta-sigma period of dc input 6/12?",
       "period 2", note="6/12 is 1/2 in lowest terms"),
)

#: Questions whose right outcome is a refusal.
TRICKS: Tuple[EngQuestion, ...] = (
    _refuse("t-no-rel", "derive power from voltage and mass",
            "no declared axiom relates power to voltage and mass alone"),
    _refuse("t-photon", "derive momentum from planck constant and "
                        "wavelength",
            "W10's axioms need wave_speed = c as well; not derivable from "
            "what is declared"),
    _refuse("t-hydraulic", "derive power from pressure and volume flow rate",
            "W6 declares no hydraulic-power axiom"),
    _refuse("t-tau-iw", "derive torque from moment of inertia and angular "
                        "velocity", "not derivable: the time exponents "
                                    "differ"),
    _refuse("t-z0-zero", "reflection coefficient of a 50 ohm load on a 0 ohm "
                         "line", "a zero reference impedance normalises "
                                 "nothing"),
    _refuse("t-farad", "reflection coefficient of a 100 ohm load on a 50 "
                       "farad line", "Z and Z0 must share a dimension"),
    _refuse("t-pole", "reflection coefficient of a -50 ohm load on a 50 ohm "
                      "line", "z = -1 is the pole of the Mobius map"),
    _refuse("t-ambig", "what is the electrical analogue of mass?",
            "the two standard analogies disagree (inductance vs "
            "capacitance): ambiguous without naming one"),
    _refuse("t-entropy", "in the force-voltage analogy, what is the "
                         "mechanical analogue of entropy?",
            "outside the analogy's declared correspondence"),
    _refuse("t-ds-out", "what is the delta-sigma period of dc input 3/2?",
            "the one-bit loop is declared on [0, 1)"),
)

#: New phrasings of questions above, same labels.
PARAPHRASES: Tuple[EngQuestion, ...] = (
    _q("p-ohm-p-vr", "express power in terms of voltage and resistance",
       "voltage^2 / resistance"),
    _q("p-rot-p", "how is power given by torque and angular velocity?",
       ("torque * angular_velocity", "angular_velocity * torque")),
    _q("p-g-100", "gamma for a 100 ohm load with a 50 ohm reference",
       "1/3"),
    _q("p-vswr", "standing wave ratio of a 25 ohm load on a 50 ohm line",
       "vswr = 2"),
    _q("p-fv-l", "which mechanical quantity corresponds to inductance in "
                 "the force-voltage analogy?", "mass", faculty="address"),
    _q("p-w0", "natural angular frequency of a 4 kg mass on a 100 N/m "
               "spring", ("= 5 rad/s", "5 rad/s")),
    _q("p-tau", "does torque = moment_of_inertia * angular_velocity have "
                "consistent dimensions?", ("inconsistent", "not")),
    _q("p-ds", "bitstream of a first-order delta-sigma modulator for 1/3, "
               "6 steps", "001001"),
)

ALL_SETS: Dict[str, Tuple[EngQuestion, ...]] = {
    "wheels": WHEELS, "checks": CHECKS, "smith": SMITH, "analogy": ANALOGY,
    "delta-sigma": DELTA_SIGMA, "tricks": TRICKS, "paraphrases": PARAPHRASES,
}


def score_engineering(item: EngQuestion, ok: bool, haystack: str) -> str:
    """The verdict of one asking, by the rule in the module docstring."""
    text = " " + haystack.lower() + " "
    if item.expect is None:
        return "wrong" if ok else "correct-refusal"
    if not ok:
        return "refused"
    return ("correct" if all(any(a in text for a in group)
                             for group in item.expect) else "wrong")


#: The hostile set, written **after** the surface's first run scored the
#: sets above and committed before it was run.  Its first-run figures are
#: frozen in :data:`STRESS_FIRST_RUN` once taken, because every change after
#: that run is made knowing its result.
STRESS: Tuple[EngQuestion, ...] = (
    _q("x-derive-caps", "Derive POWER from VOLTAGE and CURRENT",
       "voltage * current"),
    _q("x-derive-order", "derive power from resistance and current",
       ("resistance * current^2", "current^2 * resistance")),
    _q("x-derive-r", "derive resistance from voltage and power",
       "voltage^2 / power"),
    _q("x-derive-i-root", "derive current from power and resistance",
       ("(power / resistance)^(1/2)",)),
    _q("x-derive-v-lin", "derive velocity from energy and mass",
       ("(2 * energy / mass)^(1/2)",),
       note="v = sqrt(2E/m) from E = 1/2 m v^2"),
    _q("x-derive-freq", "derive frequency from energy and planck constant",
       "energy / planck_constant"),
    _q("x-derive-lambda", "derive wavelength from wave speed and frequency",
       "wave_speed / frequency"),
    _refuse("x-derive-self", "derive power from power and voltage",
            "a target cannot be one of its own inputs"),
    _refuse("x-derive-unknown", "derive flux capacitance from voltage and "
                                "current", "no such quantity in any wheel"),
    _q("x-check-ke", "is energy = mass * velocity^2 dimensionally "
                     "consistent?", "consistent",
       note="consistent (the 1/2 is dimensionless)"),
    _q("x-check-hbar", "is energy = planck_constant * frequency dimensionally "
                       "consistent?", "consistent"),
    _refuse("x-check-unknown", "is power = wibble * current dimensionally "
                               "consistent?", "wibble is not a quantity"),
    _q("x-smith-cap", "reflection coefficient of a 50-50j ohm load on a 50 "
                      "ohm line", "1/5", "-2/5",
       note="z = 1 - j; Gamma = -j/(2 - j) = (1 - 2j)/5"),
    _q("x-smith-pure-l", "reflection coefficient of a 50j ohm load on a 50 "
                         "ohm line", "j", note="z = j: Gamma = (j-1)/(j+1) "
                                               "= j"),
    _q("x-smith-75", "reflection coefficient of a 75 ohm load on a 50 ohm "
                     "line", "1/5"),
    _q("x-smith-vswr-75", "vswr of a 75 ohm load on a 50 ohm line",
       "vswr = 3/2"),
    _q("x-smith-power-25", "what fraction of power is reflected by a 25 ohm "
                           "load on a 50 ohm line?", "1/9"),
    _q("x-smith-300", "reflection coefficient of a 300 ohm load on a 75 ohm "
                      "line", "3/5"),
    _refuse("x-smith-lossless-vswr", "vswr of a 50j ohm load on a 50 ohm "
                                     "line", "|Gamma| = 1: infinite VSWR"),
    _refuse("x-smith-neg-z0", "reflection coefficient of a 50 ohm load on a "
                              "-50 ohm line", "negative reference"),
    _refuse("x-smith-henry", "reflection coefficient of a 2 henry load on a "
                             "50 ohm line", "a henry is not an impedance"),
    _q("x-smith-passive", "is a load with reflection coefficient 3/5+4/5j "
                          "passive?", "passive",
       note="|Gamma| = 1: passive and lossless"),
    _q("x-ana-fc-r", "in the force-current analogy, what is the electrical "
                     "analogue of damping coefficient?",
       ("1/resistance", "conductance"), faculty="address"),
    _q("x-ana-fc-v", "in the force-current analogy, what is the mechanical "
                     "analogue of voltage?", "velocity", faculty="address"),
    _q("x-ana-fv-q", "in the force-voltage analogy, what is the mechanical "
                     "analogue of charge?", "displacement", faculty="address"),
    _q("x-ana-power", "what is the electrical analogue of power?", "power",
       faculty="address", note="both analogies agree: not ambiguous"),
    _q("x-ana-tr-back", "translate force = damping_coefficient * velocity "
                        "into electrical terms under the force-voltage "
                        "analogy", "voltage = resistance * current"),
    _refuse("x-ana-tr-unnamed", "translate power = voltage * current into "
                                "mechanics", "no analogy named"),
    _q("x-res-lc-irr", "resonant angular frequency of a 2 henry inductor and "
                       "a 1 farad capacitor", ("(1/2)^(1/2)",)),
    _q("x-res-9", "resonant angular frequency of a 1 kg mass on a 9 N/m "
                  "spring", ("= 3 rad/s", "3 rad/s")),
    _q("x-q-mech", "quality factor of a 1 kg mass, 16 N/m spring and "
                   "2 N s/m damper", ("q = 2", "= 2 ")),
    _refuse("x-res-mixed", "resonant angular frequency of a 1 kg mass and a "
                           "1 farad capacitor", "mixed domains"),
    _refuse("x-res-neg", "resonant angular frequency of a -1 kg mass on a "
                         "4 N/m spring", "negative mass"),
    _q("x-ds-bits-half", "delta-sigma bits of 1/2 over 4 steps", "0101"),
    _q("x-ds-avg-13", "delta-sigma average of 1/3 after 10 steps", "3/10"),
    _q("x-ds-irr3", "is the delta-sigma bitstream of sqrt(3) - 1 periodic?",
       ("never periodic", "not periodic", "aperiodic")),
    _q("x-ds-rat", "is the delta-sigma bitstream of 2/5 periodic?",
       "period 5"),
    _refuse("x-ds-neg", "delta-sigma bits of -1/3 over 6 steps",
            "outside [0, 1)"),
)

#: The stress set's first run, frozen.  The one ``wrong`` is ``x-smith-cap``:
#: the answer ``Gamma = 1/5 - 2/5j`` is right, and the label's fragment
#: ``-2/5`` does not match the rendering ``- 2/5j``.  The label is left as it
#: was registered and the renderer was not changed to meet it; the verdict is
#: recorded as a scoring artifact in ``studies/ENGINEERING_LANGUAGE_STUDY.md``.
STRESS_FIRST_RUN: Dict[str, int] = {
    "correct": 27, "wrong": 1, "refused": 0, "correct-refusal": 10}

#: Both existing paths on the 63 questions above, measured before any
#: engineering code existed (``GeometricSession.ask`` and ``ask_planned``
#: gave the same tally).
BASELINE_FIRST_RUN: Dict[str, int] = {
    "correct": 0, "wrong": 0, "refused": 53, "correct-refusal": 10}
