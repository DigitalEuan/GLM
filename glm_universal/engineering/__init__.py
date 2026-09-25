"""``glm_universal.engineering`` -- electrical and mechanical as languages.

The formula-wheel session record
(``source_material/formula_wheel/GLM_formula_wheel_study_session_record.md``)
built three standalone studies -- a corrected formula wheel, an exact Smith
chart and a delta-sigma audio loop -- and named, as its first priority,
running them against the GLM's own substrate.  This package is that
integration, plus the piece the record did not have: a way to *ask*.

``wheels``      formula wheels as rational spans, with certificates; the ten
                wheels and 41 cases of the corrected study, grounded in the
                726-quantity register at EXT10 and SI7.
``smith``       the Smith chart over Gaussian rationals, and exact
                L-section matching.
``analogy``     the force-voltage and force-current analogies as maps on
                laws, checked for structure preservation.
``delta_sigma`` periodicity by theorem, noise shaping measured exactly.
``speak``       the question surface: seven frames, refusal by reason,
                fall-through to the typed planner.
``study``       the whole measurement and its evidence envelopes.

The rules that license answers are proved in
``RequestProject/GLM/EngineeringWheels.lean``.  Nothing here writes to a
register; everything is ``int`` and ``Fraction``.
"""

from . import analogy, delta_sigma, smith, speak, study, wheels

__all__ = ["analogy", "delta_sigma", "smith", "speak", "study", "wheels"]
