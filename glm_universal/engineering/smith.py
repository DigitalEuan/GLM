"""``glm_universal.engineering.smith`` -- the Smith chart, in exact arithmetic.

Where it sits
-------------
The Smith chart comes *after* dimensional grounding, never inside it: a load
impedance ``Z`` and a reference ``Z0`` must share a dimension (the formula
wheel's check), and only then is ``z = Z / Z0`` a dimensionless complex
number the chart can hold.  The chart itself is the Mobius map

    Gamma = (z - 1) / (z + 1),        z = (1 + Gamma) / (1 - Gamma),

which carries the closed right half-plane (passive loads) onto the closed
unit disc.  Every figure here is a Gaussian rational -- a pair of
``Fraction`` -- so the map, its inverse, admittance duality, reflected power
``|Gamma|^2`` and the resistance and reactance circles are computed without
rounding.  The one irrational step, ``|Gamma| = sqrt(|Gamma|^2)`` inside the
VSWR, is returned exactly when ``|Gamma|^2`` is a rational square and in
closed radical form otherwise.

What is proved rather than tested
---------------------------------
``RequestProject/GLM/EngineeringWheels.lean`` proves, over the complex
numbers: the round trip ``z -> Gamma -> z``; admittance duality
``Gamma(1/z) = -Gamma(z)``; and passivity: ``Re z >= 0`` gives
``|Gamma| <= 1``, with ``|Gamma| = 1`` exactly on the imaginary axis.  The 16
checks of :func:`smith_checks` are the executable side of those statements
plus the exact circle geometry, and they reproduce the 16/16 of the session
record's ``glm_smith_chart_study.py`` protocol from its description.

Matching
--------
:func:`l_network_search` is the exact counterpart of the record's RF
extension: a series-reactance / shunt-susceptance L-section over a rational
component grid, scored by the worst ``|Gamma|^2`` across a band of rational
angular frequencies, with a bypass candidate so a poor grid can never force a
network worse than none, and ``+/-5 %`` component corners.  Angular frequency
is declared directly in rad/s, so no ``2*pi`` ever enters the arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "GaussQ", "gamma_of", "z_of", "normalise", "vswr", "reflected_power",
    "is_passive", "resistance_circle", "reactance_circle", "smith_checks",
    "SeriesRLC", "l_network_search", "smith_report", "rational_sqrt",
]


@dataclass(frozen=True)
class GaussQ:
    """A Gaussian rational ``re + im*j``."""

    re: Fraction
    im: Fraction = Fraction(0)

    @staticmethod
    def of(re, im=0) -> "GaussQ":
        return GaussQ(Fraction(re), Fraction(im))

    def __add__(self, o: "GaussQ") -> "GaussQ":
        return GaussQ(self.re + o.re, self.im + o.im)

    def __sub__(self, o: "GaussQ") -> "GaussQ":
        return GaussQ(self.re - o.re, self.im - o.im)

    def __mul__(self, o: "GaussQ") -> "GaussQ":
        return GaussQ(self.re * o.re - self.im * o.im,
                      self.re * o.im + self.im * o.re)

    def __neg__(self) -> "GaussQ":
        return GaussQ(-self.re, -self.im)

    def conj(self) -> "GaussQ":
        return GaussQ(self.re, -self.im)

    def norm2(self) -> Fraction:
        return self.re * self.re + self.im * self.im

    def inv(self) -> "GaussQ":
        n = self.norm2()
        if n == 0:
            raise ZeroDivisionError("0 has no reciprocal")
        return GaussQ(self.re / n, -self.im / n)

    def __truediv__(self, o: "GaussQ") -> "GaussQ":
        return self * o.inv()

    def render(self) -> str:
        if self.im == 0:
            return f"{self.re}"
        sign = "-" if self.im < 0 else "+"
        mag = abs(self.im)
        imag = "j" if mag == 1 else f"{mag}j"
        if self.re == 0:
            return f"-{imag}" if self.im < 0 else imag
        return f"{self.re} {sign} {imag}"


ONE = GaussQ.of(1)


def normalise(z_load: GaussQ, z0: Fraction) -> GaussQ:
    """``z = Z / Z0``; a reference that is not positive normalises nothing."""
    if z0 <= 0:
        raise ValueError("the reference impedance must be positive")
    return GaussQ(z_load.re / z0, z_load.im / z0)


def gamma_of(z: GaussQ) -> GaussQ:
    """``(z - 1) / (z + 1)``; ``z = -1`` is the pole and raises."""
    if z == -ONE:
        raise ZeroDivisionError("z = -1 is the pole of the Mobius map")
    return (z - ONE) / (z + ONE)


def z_of(gamma: GaussQ) -> GaussQ:
    """``(1 + Gamma) / (1 - Gamma)``; ``Gamma = 1`` is the open circuit."""
    if gamma == ONE:
        raise ZeroDivisionError("Gamma = 1 is the open circuit (z infinite)")
    return (ONE + gamma) / (ONE - gamma)


def reflected_power(gamma: GaussQ) -> Fraction:
    """The reflected fraction of incident power, ``|Gamma|^2``."""
    return gamma.norm2()


def is_passive(gamma: GaussQ) -> bool:
    return gamma.norm2() <= 1


def rational_sqrt(q: Fraction) -> Optional[Fraction]:
    """The exact square root of ``q`` when it is rational, else ``None``."""
    if q < 0:
        return None
    a, b = isqrt(q.numerator), isqrt(q.denominator)
    if a * a == q.numerator and b * b == q.denominator:
        return Fraction(a, b)
    return None


def vswr(gamma: GaussQ) -> Tuple[Optional[Fraction], str]:
    """``(1 + |Gamma|) / (1 - |Gamma|)``: exact where ``|Gamma|`` is
    rational, else a closed radical form.  ``|Gamma| >= 1`` has no finite
    VSWR and raises."""
    g2 = gamma.norm2()
    if g2 >= 1:
        raise ValueError("|Gamma| >= 1: the standing-wave ratio is infinite "
                         "or undefined")
    g = rational_sqrt(g2)
    if g is not None:
        value = (1 + g) / (1 - g)
        return value, f"{value}"
    return None, f"(1 + ({g2})^(1/2)) / (1 - ({g2})^(1/2))"


def resistance_circle(r: Fraction) -> Tuple[GaussQ, Fraction]:
    """The constant-resistance circle ``Re z = r``: centre, radius."""
    return GaussQ.of(r / (1 + r)), Fraction(1) / (1 + r)


def reactance_circle(x: Fraction) -> Tuple[GaussQ, Fraction]:
    """The constant-reactance circle ``Im z = x`` (x != 0): centre, radius."""
    if x == 0:
        raise ValueError("x = 0 is the real axis, a line, not a circle")
    return GaussQ.of(1, 1 / x), abs(1 / x)


def _on_circle(p: GaussQ, centre: GaussQ, radius: Fraction) -> bool:
    return (p - centre).norm2() == radius * radius


def smith_checks() -> List[Tuple[str, bool]]:
    """The 16 preregistered transformation and geometry checks."""
    z1 = GaussQ.of(Fraction(1, 2), Fraction(1, 2))
    z2 = GaussQ.of(2, -3)
    lossless = GaussQ.of(0, 2)
    active = GaussQ.of(-Fraction(1, 2), 1)
    checks = [
        ("matched load: z = 1 gives Gamma = 0", gamma_of(ONE) == GaussQ.of(0)),
        ("short circuit: z = 0 gives Gamma = -1",
         gamma_of(GaussQ.of(0)) == GaussQ.of(-1)),
        ("real load: z = 2 gives Gamma = 1/3",
         gamma_of(GaussQ.of(2)) == GaussQ.of(Fraction(1, 3))),
        ("real load: z = 1/2 gives Gamma = -1/3",
         gamma_of(GaussQ.of(Fraction(1, 2))) == GaussQ.of(Fraction(-1, 3))),
        ("complex load: z = 1/2 + j/2 gives Gamma = -1/5 + 2j/5",
         gamma_of(z1) == GaussQ.of(Fraction(-1, 5), Fraction(2, 5))),
        ("inverse: Gamma = 1/3 gives z = 2",
         z_of(GaussQ.of(Fraction(1, 3))) == GaussQ.of(2)),
        ("round trip z -> Gamma -> z (1/2 + j/2)", z_of(gamma_of(z1)) == z1),
        ("round trip z -> Gamma -> z (2 - 3j)", z_of(gamma_of(z2)) == z2),
        ("admittance duality: Gamma(1/z) = -Gamma(z)",
         gamma_of(z2.inv()) == -gamma_of(z2)),
        ("passive load lies inside the unit disc",
         gamma_of(z2).norm2() < 1),
        ("lossless load lies on the unit circle",
         gamma_of(lossless).norm2() == 1),
        ("active load lies outside the unit disc",
         gamma_of(active).norm2() > 1),
        ("reflected power: z = 2 reflects 1/9",
         reflected_power(gamma_of(GaussQ.of(2))) == Fraction(1, 9)),
        ("constant-resistance circle r = 1/2 passes through Gamma(1/2 + j/2)",
         _on_circle(gamma_of(z1), *resistance_circle(Fraction(1, 2)))),
        ("constant-reactance circle x = -3 passes through Gamma(2 - 3j)",
         _on_circle(gamma_of(z2), *reactance_circle(Fraction(-3)))),
        ("VSWR of z = 2 is exactly 2",
         vswr(gamma_of(GaussQ.of(2)))[0] == 2),
    ]
    return checks


# ---------------------------------------------------------------------------
# Matching: an exact L-section over a rational band
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SeriesRLC:
    """A series R-L-C load, component values in ohm, henry, farad."""

    r: Fraction
    l: Fraction
    c: Fraction

    def impedance(self, w: Fraction) -> GaussQ:
        return GaussQ(self.r, w * self.l - 1 / (w * self.c))


def _series(z: GaussQ, kind: str, value: Fraction, w: Fraction) -> GaussQ:
    x = w * value if kind == "L" else -1 / (w * value)
    return z + GaussQ.of(0, x)


def _shunt(z: GaussQ, kind: str, value: Fraction, w: Fraction) -> GaussQ:
    b = w * value if kind == "C" else -1 / (w * value)
    y = z.inv() + GaussQ.of(0, b)
    return y.inv()


def _worst(load: SeriesRLC, net, band: Sequence[Fraction],
           z0: Fraction) -> Fraction:
    worst = Fraction(0)
    for w in band:
        z = load.impedance(w)
        for stage in net:
            z = stage(z, w)
        g2 = gamma_of(normalise(z, z0)).norm2()
        worst = max(worst, g2)
    return worst


def l_network_search(load: SeriesRLC, band: Sequence[Fraction],
                     z0: Fraction,
                     grids: Dict[str, Sequence[Fraction]]
                     ) -> Dict[str, object]:
    """Exhaustive exact search of series-then-shunt L-sections.

    ``grids`` maps ``"L"`` to inductor values (henry) and ``"C"`` to
    capacitor values (farad); each is used in both positions.  Every
    candidate is scored by its worst ``|Gamma|^2`` over ``band``; the
    bypass (no network) is always a candidate.  Returns the best, the
    bypass score, the candidate count and the best candidate's worst score
    over the ``+/-5 %`` corners of both components.
    """
    bypass = _worst(load, (), band, z0)
    best = ("bypass", None, None, bypass)
    count = 1
    for skind in ("L", "C"):
        for sv in grids[skind]:
            for pkind in ("L", "C"):
                for pv in grids[pkind]:
                    net = (lambda z, w, k=skind, v=sv: _series(z, k, v, w),
                           lambda z, w, k=pkind, v=pv: _shunt(z, k, v, w))
                    score = _worst(load, net, band, z0)
                    count += 1
                    if score < best[3]:
                        best = (f"series {skind} / shunt {pkind}",
                                (skind, sv), (pkind, pv), score)
    corner = best[3]
    if best[1] is not None:
        corner = Fraction(0)
        for a in (Fraction(95, 100), Fraction(105, 100)):
            for b in (Fraction(95, 100), Fraction(105, 100)):
                (sk, sv), (pk, pv) = best[1], best[2]
                net = (lambda z, w, k=sk, v=sv * a: _series(z, k, v, w),
                       lambda z, w, k=pk, v=pv * b: _shunt(z, k, v, w))
                corner = max(corner, _worst(load, net, band, z0))
    return {"topology": best[0], "series": best[1], "shunt": best[2],
            "worst_gamma2": best[3], "bypass_gamma2": bypass,
            "corner_gamma2": corner, "candidates": count}


def smith_report() -> Dict[str, object]:
    """The Smith-chart figures: the 16 checks and one exact matching run."""
    checks = smith_checks()
    # A deterministic load: 25 ohm, 20 nH, 2 pF, around 5*10^9 rad/s.
    load = SeriesRLC(Fraction(25), Fraction(20, 10 ** 9),
                     Fraction(2, 10 ** 12))
    band = [Fraction(45 + k, 10) * 10 ** 9 for k in range(0, 11)]
    grid = [Fraction(k, 2) for k in range(1, 21)]
    match = l_network_search(load, band, Fraction(50), {
        "L": [g * Fraction(1, 10 ** 9) for g in grid],
        "C": [g * Fraction(1, 10 ** 12) for g in grid]})
    return {"checks": len(checks), "passed": sum(ok for _, ok in checks),
            "failed": [name for name, ok in checks if not ok],
            "match": match}
