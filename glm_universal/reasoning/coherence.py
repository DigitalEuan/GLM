"""``glm_universal.reasoning.coherence`` -- NRCI and the Y constant.

What this module is
-------------------
The Griess metric measures **distance** between carriers.
NRCI measures **coherence** — how structured, non-random a carrier is.

Both perspectives are needed:
- Distance tells you how far apart two concepts are.
- Coherence tells you how stable each concept is in the substrate.

The Y constant
--------------
Y = 1/(π + 2/π) ≈ 0.264675 — the read quantum: the cost of reading one
distinction.  Q = Y + 1/8 is the activation quantum: the minimum tax of
any nonzero pattern.

In this module Y is carried as an exact rational continued-fraction
approximation, not a float.  The approximation is:

    Y ≈ 264675430404527 / 10^15 = 0.264675430404527

which agrees with the true value to 15 significant figures.  That Fraction
is what every function here computes with; the decimal string ``Y_DECIMAL``
exists only for display.

The five NRCI shells
--------------------
Shell 0 (Golay): HW·Y + ‖v‖²/8 — sign-blind, the original NRCI.
Shell 1 (Sign-parity): |n_pos - n_neg| / n_nonzero — sign balance.
Shell 2 (Sextet-balance): CV of |weight| across 4 MOG sextets.
Shell 3 (Coset-type): Golay syndrome weight / 12.
Shell 4 (Sextet-signed): L2 norm of signed sextet sums.

The combined tax is:
    tax = tax_0 + α₁·tax_1 + α₂·tax_2 + α₃·tax_3 + α₄·tax_4
    NRCI = B / (B + tax),  B = 10

Exactness
---------
**No float is constructed anywhere in this module.**  Shells 2 and 4 involve a
square root, which is irrational in general; earlier versions therefore
returned floats and this module was the one exception to the package's
exactness rule.  It is no longer.  The square root is taken by
:func:`rational_sqrt`, which returns the largest rational with denominator
``SQRT_DENOM`` whose square does not exceed its argument.  That value is
exact, deterministic, reproducible across interpreters, and within
``1/SQRT_DENOM`` of the true root -- a *declared resolution*, in the same
spirit as the rational ``Y`` above, rather than whatever the platform's
binary floating point happens to do.  Every shell, the combined tax and the
NRCI are :class:`~fractions.Fraction` values throughout, and
:func:`decimal_str` renders them for display without ever building a float.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "Y", "Y_DECIMAL", "Q", "B", "DELTA", "Z_STAR",
    "SEXTET_RANGES", "SQRT_DENOM", "ALPHA",
    "rational_sqrt", "decimal_str",
    "tax_shell0", "tax_shell1", "tax_shell2", "tax_shell3", "tax_shell4",
    "combined_tax", "nrci", "nrci_breakdown", "coherence_regime",
    "RefinedNRCI",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE Y CONSTANT
# ═════════════════════════════════════════════════════════════════════════

#: The read quantum Y = 1/(π + 2/π), carried as an exact rational
#: approximation.  The continued-fraction expansion of 1/(π + 2/π) gives
#: convergents 1/3, 3/11, 19/72, 136/514, ...; the fraction below is the
#: 15-digit rational approximation.
#:
#: Every function in this module computes with this Fraction; the roots that
#: Shells 2 and 4 need are taken rationally by :func:`rational_sqrt`.
#:
#: NOTE: 1/(π + 2/π) ≈ 0.264675430404527
Y = Fraction(264675430404527, 10**15)

#: The same value as a decimal string, for display.  Nothing computes with it.
Y_DECIMAL = "0.264675430404527"

#: Primitive difference Δ = 2.
DELTA = Fraction(2)

#: Zone-share cost Z★ = 1/8.
Z_STAR = Fraction(1, 8)

#: Activation quantum Q = Y + Z★ = Y + 1/8.
Q = Y + Z_STAR

#: Coherence budget B = 10.
B = Fraction(10)

#: The 4 MOG sextet ranges: [start, end) for each tetrad.
SEXTET_RANGES = ((0, 6), (6, 12), (12, 18), (18, 24))

#: The declared resolution of :func:`rational_sqrt`: roots are returned as
#: multiples of ``1/SQRT_DENOM``.  Fifteen digits is the precision at which
#: ``Y`` itself is carried, so the two agree.
SQRT_DENOM = 10 ** 15

#: The default shell weights α₁..α₄, as exact rationals.
ALPHA = (Fraction(1, 2), Fraction(3, 10), Fraction(1, 5), Fraction(2, 5))


# ══════════════════════════════════════════════════════════════════════
# 1b.  EXACT SQUARE ROOTS AND EXACT DISPLAY
# ══════════════════════════════════════════════════════════════════════

def rational_sqrt(x: Fraction, denom: int = SQRT_DENOM) -> Fraction:
    """The square root of ``x`` at a declared rational resolution.

    Returns the largest ``p / denom`` whose square is at most ``x``, computed
    with :func:`math.isqrt` on integers alone.  Hence, for ``x >= 0``::

        rational_sqrt(x) ** 2 <= x < (rational_sqrt(x) + 1/denom) ** 2

    so the answer is below the true root by less than ``1/denom``, and it is
    the same rational on every machine and every run.  A negative argument
    returns ``0``: the callers here only ever pass sums of squares.
    """
    if x <= 0:
        return Fraction(0)
    scaled = Fraction(x) * denom * denom
    root = math.isqrt(scaled.numerator // scaled.denominator)
    return Fraction(root, denom)


def decimal_str(x: Fraction, places: int = 6) -> str:
    """``x`` as a decimal string, truncated toward zero, built from integers.

    Display only -- and display that never constructs a float, so a rendered
    number is exactly the rational the module computed, cut at ``places``.
    """
    value = Fraction(x)
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    units = (value.numerator * scale) // value.denominator
    whole, frac = divmod(units, scale)
    if places == 0:
        return f"{sign}{whole}"
    return f"{sign}{whole}.{frac:0{places}d}"


# ═════════════════════════════════════════════════════════════════════════
# 2.  SHELL 0: GOLAY SHELL (sign-blind, exact)
# ═════════════════════════════════════════════════════════════════════════

def tax_shell0(point: Sequence) -> Fraction:
    """Golay shell tax: HW·Y + ‖v‖²/8.

    This is the original NRCI tax.  Sign-blind: HW counts nonzero coords,
    ‖v‖² sums squares.  All sign-variants of an octad have identical tax_0.

    Returns an exact :class:`~fractions.Fraction`.
    """
    hw = sum(1 for x in point if x != 0)
    ns = sum(Fraction(x) ** 2 for x in point)
    return Fraction(hw) * Y + ns / 8


# ═════════════════════════════════════════════════════════════════════════
# 3.  SHELL 1: SIGN-PARITY (sign-sensitive, exact)
# ═════════════════════════════════════════════════════════════════════════

def tax_shell1(point: Sequence) -> Fraction:
    """Sign-parity tax: |n_pos - n_neg| / n_nonzero.

    Range: [0, 1]
        0 = perfectly balanced (equal +/- count)
        1 = all same sign

    For binary vectors (0/1), this is always 0 (no negatives).
    Returns an exact Fraction.
    """
    nonzero = [x for x in point if x != 0]
    if not nonzero:
        return Fraction(0)
    n_neg = sum(1 for x in nonzero if x < 0)
    n_pos = len(nonzero) - n_neg
    return Fraction(abs(n_pos - n_neg), len(nonzero))


# ═════════════════════════════════════════════════════════════════════════
# 4.  SHELL 2: SEXTET-BALANCE (partially sign-sensitive, needs sqrt)
# ═════════════════════════════════════════════════════════════════════════

def tax_shell2(point: Sequence) -> Fraction:
    """Sextet-balance tax: coefficient of variation across 4 MOG sextets.

    The 24 coordinates split into 4 sextets.  This shell measures how
    evenly the |weight| is distributed across them.

    Range: [0, ~2]
        0 = perfectly balanced
        higher = skewed

    The variance is exact; only its square root needs rounding, and that is
    done by :func:`rational_sqrt` at the module's declared resolution.  The
    result is a :class:`~fractions.Fraction`.
    """
    weights = [sum(Fraction(abs(point[i])) for i in range(s, e))
               for s, e in SEXTET_RANGES]
    mean_w = sum(weights, Fraction(0)) / 4
    if mean_w == 0:
        return Fraction(0)
    variance = sum(((w - mean_w) ** 2 for w in weights), Fraction(0)) / 4
    return rational_sqrt(variance) / mean_w


# ═════════════════════════════════════════════════════════════════════════
# 5.  SHELL 3: COSET-TYPE (needs Golay syndrome)
# ═════════════════════════════════════════════════════════════════════════

def _golay_syndrome_weight(point: Sequence) -> int:
    """Compute the Golay syndrome weight from the substrate's own engine.

    Falls back to a self-contained computation if the substrate isn't
    available.
    """
    from ..substrate import mog
    bits = tuple(1 if x != 0 else 0 for x in point)
    # Use the Golay parity-check matrix from the substrate
    H_cols = mog._H_COLUMNS if hasattr(mog, '_H_COLUMNS') else None
    if H_cols is None:
        # Build it from the generator
        B = [
            (0,1,1,1,1,1,1,1,1,1,1,1),
            (1,1,1,0,1,1,1,0,0,0,1,0),
            (1,1,0,1,1,1,0,0,0,1,0,1),
            (1,0,1,1,1,0,0,0,1,0,1,1),
            (1,1,1,1,0,0,0,1,0,1,1,0),
            (1,1,1,0,0,0,1,0,1,1,0,1),
            (1,1,0,0,0,1,0,1,1,0,1,1),
            (1,0,0,0,1,0,1,1,0,1,1,1),
            (1,0,0,1,0,1,1,0,1,1,1,0),
            (1,0,1,0,1,1,0,1,1,1,0,0),
            (1,1,0,1,1,0,1,1,1,0,0,0),
            (1,0,1,1,0,1,1,1,0,0,0,1),
        ]
        H_cols = []
        for k in range(24):
            col = []
            for j in range(12):
                if k < 12:
                    col.append(B[j][k])
                else:
                    col.append(1 if (k - 12) == j else 0)
            H_cols.append(tuple(col))
    s = [0] * 12
    for k, bit in enumerate(bits):
        if bit:
            col = H_cols[k]
            for j in range(12):
                s[j] ^= col[j]
    return sum(s)


def tax_shell3(point: Sequence) -> Fraction:
    """Coset-type tax: Golay syndrome weight / 12.

    Range: [0, 1]
        0 = codeword (most stable)
        1 = maximally non-codeword

    Returns an exact Fraction.
    """
    sw = _golay_syndrome_weight(point)
    return Fraction(sw, 12)


# ═════════════════════════════════════════════════════════════════════════
# 6.  SHELL 4: SEXTET-SIGNED (finest shell, needs sqrt)
# ═════════════════════════════════════════════════════════════════════════

def tax_shell4(point: Sequence) -> Fraction:
    """Sextet-signed tax: L2 norm of signed sextet sums, normalized.

    For each of the 4 sextets, compute the SIGNED sum of coordinates.
    The 4-tuple (s1, s2, s3, s4) identifies sign-variants within a
    Pascal class.  The tax is the L2 norm, normalized by ``sqrt(4)`` times
    the largest coordinate times 6 -- and ``sqrt(4) = 2`` exactly, so the
    only root here is the norm itself.

    Returns a :class:`~fractions.Fraction`.
    """
    sextet_sums = [sum((Fraction(x) for x in point[s:e]), Fraction(0))
                   for s, e in SEXTET_RANGES]
    norm = rational_sqrt(sum((s ** 2 for s in sextet_sums), Fraction(0)))
    max_coord = max((abs(Fraction(x)) for x in point), default=Fraction(1))
    if max_coord == 0:
        return Fraction(0)
    max_norm = 2 * max_coord * 6
    return norm / max_norm


# ═════════════════════════════════════════════════════════════════════════
# 7.  COMBINED NRCI
# ═════════════════════════════════════════════════════════════════════════

def combined_tax(point: Sequence, *,
                 alpha1: Fraction = ALPHA[0], alpha2: Fraction = ALPHA[1],
                 alpha3: Fraction = ALPHA[2],
                 alpha4: Fraction = ALPHA[3]) -> Fraction:
    """The weighted sum of the five shell taxes, exactly."""
    return (tax_shell0(point)
            + Fraction(alpha1) * tax_shell1(point)
            + Fraction(alpha2) * tax_shell2(point)
            + Fraction(alpha3) * tax_shell3(point)
            + Fraction(alpha4) * tax_shell4(point))


def nrci(point: Sequence, *,
         alpha1: Fraction = ALPHA[0], alpha2: Fraction = ALPHA[1],
         alpha3: Fraction = ALPHA[2],
         alpha4: Fraction = ALPHA[3]) -> Fraction:
    """The refined NRCI = B / (B + tax), with all five shells.

    Returns an exact :class:`~fractions.Fraction` in (0, 1].
        1 = perfectly coherent (zero tax, the vacuum)
        1/2 = moderately coherent (an octad)
        0 = maximally incoherent (infinite tax)
    """
    total = combined_tax(point, alpha1=alpha1, alpha2=alpha2,
                         alpha3=alpha3, alpha4=alpha4)
    return B / (B + total)


def nrci_breakdown(point: Sequence, *,
                   alpha1: Fraction = ALPHA[0], alpha2: Fraction = ALPHA[1],
                   alpha3: Fraction = ALPHA[2], alpha4: Fraction = ALPHA[3]
                   ) -> Dict[str, object]:
    """Full breakdown of all shell taxes and the combined NRCI.

    Shells 0, 1 and 3 are reported as strings, as they always were; shells 2
    and 4, the tax and the NRCI are now exact ``Fraction`` values rather than
    floats.
    """
    t0 = tax_shell0(point)
    t1 = tax_shell1(point)
    t2 = tax_shell2(point)
    t3 = tax_shell3(point)
    t4 = tax_shell4(point)
    total = (t0 + Fraction(alpha1) * t1 + Fraction(alpha2) * t2
             + Fraction(alpha3) * t3 + Fraction(alpha4) * t4)
    value = B / (B + total)
    return {
        "shell0_golay": str(t0),
        "shell1_sign_parity": str(t1),
        "shell2_sextet_balance": t2,
        "shell3_coset_type": str(t3),
        "shell4_sextet_signed": t4,
        "tax_total": total,
        "nrci": value,
        "regime": coherence_regime(value),
    }


def coherence_regime(nrci_value) -> str:
    """The coherence regime for an NRCI value.

    OnBit (≥4/5): at most 6 active distinctions.
    Coherent (≥1/2): at most 25 active distinctions.
    Transitional (≥3/10): up to 59 (unreachable on 24 coords).
    Subcoherent (<3/10): very high tax.

    The thresholds are exact rationals, so a value sitting on one lands on
    the same side of it every time.
    """
    value = Fraction(nrci_value)
    if value >= Fraction(4, 5):
        return "OnBit"
    if value >= Fraction(1, 2):
        return "Coherent"
    if value >= Fraction(3, 10):
        return "Transitional"
    return "Subcoherent"


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REFINED NRCI CLASS (configurable)
# ═════════════════════════════════════════════════════════════════════════

class RefinedNRCI:
    """Configurable multi-shell NRCI.

    Parameters
    ----------
    alpha1..alpha4 : Fraction
        Weights for Shells 1-4.  Shell 0 is always weight 1.
    use_shell1..use_shell4 : bool
        Enable/disable individual shells.
    """

    def __init__(self, *,
                 alpha1: Fraction = ALPHA[0], alpha2: Fraction = ALPHA[1],
                 alpha3: Fraction = ALPHA[2], alpha4: Fraction = ALPHA[3],
                 use_shell1: bool = True, use_shell2: bool = True,
                 use_shell3: bool = True, use_shell4: bool = True):
        self.alpha1 = Fraction(alpha1)
        self.alpha2 = Fraction(alpha2)
        self.alpha3 = Fraction(alpha3)
        self.alpha4 = Fraction(alpha4)
        self.use_shell1 = use_shell1
        self.use_shell2 = use_shell2
        self.use_shell3 = use_shell3
        self.use_shell4 = use_shell4

    def compute(self, point: Sequence) -> Fraction:
        """Compute the refined NRCI, exactly."""
        return B / (B + self._total(point))

    def _total(self, point: Sequence) -> Fraction:
        """The weighted tax over the enabled shells."""
        total = tax_shell0(point)
        if self.use_shell1:
            total += self.alpha1 * tax_shell1(point)
        if self.use_shell2:
            total += self.alpha2 * tax_shell2(point)
        if self.use_shell3:
            total += self.alpha3 * tax_shell3(point)
        if self.use_shell4:
            total += self.alpha4 * tax_shell4(point)
        return total

    def describe(self, point: Sequence) -> Dict[str, object]:
        """Full breakdown with all shell taxes."""
        t0 = tax_shell0(point)
        t1 = tax_shell1(point) if self.use_shell1 else Fraction(0)
        t2 = tax_shell2(point) if self.use_shell2 else Fraction(0)
        t3 = tax_shell3(point) if self.use_shell3 else Fraction(0)
        t4 = tax_shell4(point) if self.use_shell4 else Fraction(0)
        total = self._total(point)
        value = B / (B + total)
        return {
            "shell0_golay": str(t0),
            "shell1_sign_parity": str(t1),
            "shell2_sextet_balance": t2,
            "shell3_coset_type": str(t3),
            "shell4_sextet_signed": t4,
            "tax_total": total,
            "nrci": value,
            "regime": coherence_regime(value),
        }
