"""``glm_universal.evaluation.cognition_heldout`` -- the round-two question set.

Why this exists
---------------
Round two of ``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`` (Phase 63, §6)
adds three readings to the typed planner:

* **Y1** -- the interval layer: is a register value consistent with a quoted
  decimal, or with the declared standard value?
* **Y2** -- rational recognition: which simple fraction rounds to a quoted
  decimal, with a certificate of how far it is unique?
* **Y3** -- dimensional derivation: how does one quantity depend on others,
  up to a dimensionless constant -- unique, impossible, or undetermined?

This set was written **before** any of those frames existed and committed
with the declarations, so the commit is the pre-registration.  The labels
were worked out by hand: the dimensional ones by solving the exponent
equations on paper, the fraction ones from continued fractions (and
confirmed by a brute-force scan over denominators that shares no code with
the frame), the interval ones from the register's held values and the X6
standard table.

The renderings it assumes, fixed here before the frames were written:

* Y1 answers begin ``yes`` or ``no``;
* Y2 answers name the fraction as ``p/q``;
* Y3 answers write every factor as ``name^e`` with ``e`` a reduced fraction,
  exponent one written ``^1``, joined by ``" * "``, in the order the
  quantities were asked; an impossibility says ``no product of powers``.

The scoring rule is :func:`glm_universal.evaluation.heldout.score_answer`
unchanged: ``expect`` is a tuple of lowercase fragments, at least one of which
a right answer contains, or ``None`` when the right outcome is a refusal.

Exact and float-free: the module holds strings only.
"""

from __future__ import annotations

from typing import Tuple

from .heldout import HeldOut, _q

__all__ = ["INTERVAL_QUESTIONS", "FRACTION_QUESTIONS", "DIMENSION_QUESTIONS",
           "COGNITION_ROUND2"]


INTERVAL_QUESTIONS: Tuple[HeldOut, ...] = (
    _q("y1-iron-55845", "is the atomic weight of iron consistent with 55.845",
       "yes", note="held 55.84 -> [55.835, 55.845] meets [55.8445, 55.8455]"),
    _q("y1-iron-559", "is the atomic weight of iron consistent with 55.9",
       "no", note="[55.835, 55.845] and [55.85, 55.95] are disjoint"),
    _q("y1-carbon-12011",
       "is the atomic weight of carbon consistent with 12.011", "yes",
       note="held 12.011 at three places"),
    _q("y1-carbon-121", "is the atomic weight of carbon consistent with 12.1",
       "no", note="[12.0105, 12.0115] and [12.05, 12.15] are disjoint"),
    _q("y1-lithium-694",
       "is the atomic weight of lithium consistent with 6.94", "yes",
       note="the register holds 7, read at zero places as [6.5, 7.5]"),
    _q("y1-iron-standard",
       "is the atomic weight of iron consistent with the standard value",
       "yes", note="[55.835, 55.845] meets 55.845(2) = [55.843, 55.847]"),
    _q("y1-oxygen-standard",
       "is the atomic weight of oxygen consistent with the standard value",
       "yes", note="[15.9985, 15.9995] meets [15.99903, 15.99977]"),
    _q("y1-gold-standard",
       "is the atomic weight of gold consistent with the standard value",
       note="gold is not in the declared 30-row standard table; refused"),
)

FRACTION_QUESTIONS: Tuple[HeldOut, ...] = (
    _q("y2-0142857", "what fraction rounds to 0.142857", "1/7"),
    _q("y2-03333", "what fraction rounds to 0.3333", "1/3"),
    _q("y2-314159", "what fraction rounds to 3.14159", "355/113",
       note="355/113 = 3.1415929...; 2 * 113^2 * 10^-5 <= 1"),
    _q("y2-02857", "what fraction rounds to 0.2857", "2/7"),
    _q("y2-06667", "what fraction rounds to 0.6667", "2/3"),
    _q("y2-0125", "what fraction rounds to 0.125", "1/8"),
    _q("y2-05", "what fraction rounds to 0.5", "1/2"),
    _q("y2-271828", "what fraction rounds to 2.71828", note=(
        "the simplest is 1264/465, and 1457/536 also rounds to it: "
        "2 * 465^2 * 10^-5 > 1, so the frame refuses")),
    _q("y2-141421", "what fraction rounds to 1.41421", note=(
        "the simplest is 816/577 and 2 * 577^2 * 10^-5 > 1; refused")),
    _q("y2-01", "what fraction rounds to 0.1", note=(
        "the simplest is 1/7, and 1/8, 1/9, 1/10 ... round to it too; "
        "refused")),
)

DIMENSION_QUESTIONS: Tuple[HeldOut, ...] = (
    _q("y3-pendulum", "how does period depend on length and acceleration",
       "length^1/2 * acceleration^-1/2", note="T = k sqrt(L / g)"),
    _q("y3-kinetic", "how does kinetic energy depend on mass and velocity",
       "mass^1 * velocity^2"),
    _q("y3-spring", "how does period depend on mass and spring constant",
       "mass^1/2 * spring_constant^-1/2", note="T = k sqrt(m / k_s)"),
    _q("y3-pressure", "how does pressure depend on force and area",
       "force^1 * area^-1"),
    _q("y3-momentum", "how does momentum depend on mass and velocity",
       "mass^1 * velocity^1"),
    _q("y3-power", "how does power depend on voltage and current",
       "voltage^1 * current^1"),
    _q("y3-sound", "how does sound speed depend on pressure and density",
       "pressure^1/2 * density^-1/2", note="c = k sqrt(p / rho)"),
    _q("y3-rest-energy",
       "how does energy depend on mass and speed of light",
       "mass^1 * speed_of_light^2"),
    _q("y3-ohm", "how does resistance depend on voltage and current",
       "voltage^1 * current^-1"),
    _q("y3-pendulum-mass",
       "how does period depend on length, acceleration and mass",
       "length^1/2 * acceleration^-1/2 * mass^0",
       note="mass enters with exponent 0: the period does not depend on it"),
    _q("y3-mass-impossible", "how does mass depend on length and time",
       "no product of powers", note="neither carries M"),
    _q("y3-force-impossible", "how does force depend on length and velocity",
       "no product of powers", note="neither carries M"),
    _q("y3-drag-undetermined", "how does drag force depend on density, "
       "velocity, area and dynamic viscosity", note=(
           "four quantities over three dimensions leave one free "
           "dimensionless group (a Reynolds number); refused")),
    _q("y3-velocity-undetermined",
       "how does velocity depend on length, time and wavelength", note=(
           "length / wavelength is dimensionless and free; refused")),
    _q("y3-angle-ambiguous", "how does period depend on angular frequency",
       note=("the extended reading keeps the angle and finds no product; "
             "the SI reading drops it and finds period = omega^-1; the "
             "readings disagree, so the planner refuses")),
)

COGNITION_ROUND2: Tuple[HeldOut, ...] = (INTERVAL_QUESTIONS
                                         + FRACTION_QUESTIONS
                                         + DIMENSION_QUESTIONS)
