"""``glm_universal.evaluation.certificates_heldout`` -- the certificate set.

Why this exists
---------------
Experiment X7 of ``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`` adds a
planner frame that *derives* rather than retrieves. It solves linear
Diophantine equations in two unknowns, gives Bezout coefficients, and
factorises within a stated trial-division bound. Every answer carries a
certificate that can be checked on its own. Every "no" carries an
impossibility certificate, and a question past the bound is refused, with
the bound named.

This set was written **before** that frame existed and committed on its own,
so the commit is the pre-registration. Every label was worked out by hand
from elementary number theory, not read off any register or any code.

The rendering it assumes, fixed here before the frame was written: the
general solution of ``a x + b y = c`` is written ``x = x0 + s k`` with
``s = |b / g| > 0`` and ``x0`` the least non-negative residue modulo ``s``,
where ``g = gcd(a, b)``. A factorisation is written as ascending prime powers
joined by ``" * "``, for example ``2^3 * 3^2 * 5``.

The scoring rule is :func:`glm_universal.evaluation.heldout.score_answer`
unchanged: ``expect`` is a tuple of lowercase fragments, at least one of which
a right answer contains, or ``None`` when the right outcome is a refusal.

Exact and float-free: the module holds strings only.
"""

from __future__ import annotations

from typing import Tuple

from .heldout import HeldOut, _q

__all__ = ["CERTIFICATES"]


CERTIFICATES: Tuple[HeldOut, ...] = (
    _q("x7-solve-12-18-30", "solve 12x + 18y = 30 in integers",
       "x = 1 + 3k", note="gcd 6 divides 30; 2x + 3y = 5 at (1, 1)"),
    _q("x7-can-6-9-5", "can 6x + 9y = 5 be solved in integers",
       "does not divide 5", note="gcd 3 does not divide 5"),
    _q("x7-bezout-240-46", "bezout coefficients of 240 and 46",
       "gcd(240, 46) = 2", note="2 = 240*(-9) + 46*47"),
    _q("x7-solve-7-5-1", "solve 7x + 5y = 1 in integers",
       "x = 3 + 5k", note="7*3 + 5*(-4) = 1"),
    _q("x7-solve-4-6-7", "solve 4x + 6y = 7 in integers",
       "does not divide 7", note="gcd 2 does not divide 7"),
    _q("x7-solve-0-0-5", "solve 0x + 0y = 5 in integers",
       "does not divide 5", note="gcd(0, 0) = 0 divides only 0"),
    _q("x7-solve-0-0-0", "solve 0x + 0y = 0 in integers",
       "every", note="every integer pair is a solution"),
    _q("x7-solve-3-m9-6", "solve 3x - 9y = 6 in integers",
       "x = 2 + 3k", note="x - 3y = 2 at (2, 0)"),
    _q("x7-factor-360", "factorise 360", "2^3 * 3^2 * 5"),
    _q("x7-factor-97", "factorise 97", "97 is prime"),
    _q("x7-factor-1", "factorise 1", "no prime factors"),
    _q("x7-factor-euler", "factorise 600851475143",
       "71 * 839 * 1471 * 6857"),
    _q("x7-factor-past-bound", "factorise 998244359987710471", note=(
        "1000000007 * 998244353: both factors lie past the trial-division "
        "bound, so the right outcome is a refusal naming the bound")),
    _q("x7-quadratic", "solve x^2 + y^2 = 3 in integers",
       note="not linear; outside the frame, so refused"),
    _q("x7-bezout-17-0", "bezout coefficients of 17 and 0",
       "gcd(17, 0) = 17"),
    _q("x7-non-integer", "solve 12x + 18y = 30.5 in integers",
       note="a non-integer coefficient is outside the frame; refused"),
)
