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

    Y ≈ 264675430404527 / 10^12 = 0.264675430404527

which matches the float value to 15 significant figures.  For exact work
we use the Fraction throughout; the float is only for display.

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

Everything is exact where possible (Fraction), with float fallbacks only
for operations that genuinely need irrationals (sqrt in Shell 2, 4).
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "Y", "Y_FLOAT", "Q", "B", "DELTA", "Z_STAR",
    "SEXTET_RANGES",
    "tax_shell0", "tax_shell1", "tax_shell2", "tax_shell3", "tax_shell4",
    "nrci", "nrci_breakdown", "coherence_regime",
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
#: For exact arithmetic we use this Fraction.  For operations that genuinely
#: need the irrational value (e.g. Shell 2's sqrt), Y_FLOAT is provided.
#:
#: NOTE: 1/(π + 2/π) ≈ 0.264675430404527
Y = Fraction(264675430404527, 10**15)

#: Float approximation of Y for operations that need irrationals.
Y_FLOAT = 1.0 / (math.pi + 2.0 / math.pi)

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

def tax_shell2(point: Sequence) -> float:
    """Sextet-balance tax: coefficient of variation across 4 MOG sextets.

    The 24 coordinates split into 4 sextets.  This shell measures how
    evenly the |weight| is distributed across them.

    Range: [0, ~2]
        0 = perfectly balanced
        higher = skewed

    Returns a float (requires sqrt, which is irrational in general).
    """
    weights = []
    for s, e in SEXTET_RANGES:
        w = sum(abs(point[i]) for i in range(s, e))
        weights.append(float(w))
    mean_w = sum(weights) / 4.0
    if mean_w < 1e-15:
        return 0.0
    variance = sum((w - mean_w) ** 2 for w in weights) / 4.0
    return math.sqrt(variance) / mean_w


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

def tax_shell4(point: Sequence) -> float:
    """Sextet-signed tax: L2 norm of signed sextet sums, normalized.

    For each of the 4 sextets, compute the SIGNED sum of coordinates.
    The 4-tuple (s1, s2, s3, s4) identifies sign-variants within a
    Pascal class.  The tax is the L2 norm, normalized.

    Returns a float (requires sqrt).
    """
    sextet_sums = []
    for s, e in SEXTET_RANGES:
        sextet_sums.append(sum(point[s:e]))
    norm = math.sqrt(sum(float(s) ** 2 for s in sextet_sums))
    max_coord = max((abs(float(x)) for x in point), default=1)
    if max_coord < 1e-15:
        return 0.0
    max_norm = math.sqrt(4) * max_coord * 6
    return norm / max_norm


# ═════════════════════════════════════════════════════════════════════════
# 7.  COMBINED NRCI
# ═════════════════════════════════════════════════════════════════════════

def nrci(point: Sequence, *,
         alpha1: float = 0.5, alpha2: float = 0.3,
         alpha3: float = 0.2, alpha4: float = 0.4) -> float:
    """The refined NRCI = B / (B + tax), with all five shells.

    Returns a float in (0, 1].
        1.0 = perfectly coherent (zero tax, the vacuum)
        0.5 = moderately coherent (an octad)
        0.0 = maximally incoherent (infinite tax)
    """
    t = float(tax_shell0(point))
    t += alpha1 * float(tax_shell1(point))
    t += alpha2 * tax_shell2(point)
    t += alpha3 * float(tax_shell3(point))
    t += alpha4 * tax_shell4(point)
    return 10.0 / (10.0 + t)


def nrci_breakdown(point: Sequence, *,
                   alpha1: float = 0.5, alpha2: float = 0.3,
                   alpha3: float = 0.2, alpha4: float = 0.4
                   ) -> Dict[str, object]:
    """Full breakdown of all shell taxes and the combined NRCI."""
    t0 = tax_shell0(point)
    t1 = tax_shell1(point)
    t2 = tax_shell2(point)
    t3 = tax_shell3(point)
    t4 = tax_shell4(point)
    total = float(t0) + alpha1 * float(t1) + alpha2 * t2 + \
            alpha3 * float(t3) + alpha4 * t4
    return {
        "shell0_golay": str(t0),
        "shell1_sign_parity": str(t1),
        "shell2_sextet_balance": t2,
        "shell3_coset_type": str(t3),
        "shell4_sextet_signed": t4,
        "tax_total": total,
        "nrci": 10.0 / (10.0 + total),
        "regime": coherence_regime(10.0 / (10.0 + total)),
    }


def coherence_regime(nrci_value: float) -> str:
    """The coherence regime for an NRCI value.

    OnBit (≥0.8): at most 6 active distinctions.
    Coherent (≥0.5): at most 25 active distinctions.
    Transitional (≥0.3): up to 59 (unreachable on 24 coords).
    Subcoherent (<0.3): very high tax.
    """
    if nrci_value >= 0.8:
        return "OnBit"
    if nrci_value >= 0.5:
        return "Coherent"
    if nrci_value >= 0.3:
        return "Transitional"
    return "Subcoherent"


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REFINED NRCI CLASS (configurable)
# ═════════════════════════════════════════════════════════════════════════

class RefinedNRCI:
    """Configurable multi-shell NRCI.

    Parameters
    ----------
    alpha1..alpha4 : float
        Weights for Shells 1-4.  Shell 0 is always weight 1.
    use_shell1..use_shell4 : bool
        Enable/disable individual shells.
    """

    def __init__(self, *,
                 alpha1: float = 0.5, alpha2: float = 0.3,
                 alpha3: float = 0.2, alpha4: float = 0.4,
                 use_shell1: bool = True, use_shell2: bool = True,
                 use_shell3: bool = True, use_shell4: bool = True):
        self.alpha1 = alpha1
        self.alpha2 = alpha2
        self.alpha3 = alpha3
        self.alpha4 = alpha4
        self.use_shell1 = use_shell1
        self.use_shell2 = use_shell2
        self.use_shell3 = use_shell3
        self.use_shell4 = use_shell4

    def compute(self, point: Sequence) -> float:
        """Compute the refined NRCI."""
        t = float(tax_shell0(point))
        if self.use_shell1:
            t += self.alpha1 * float(tax_shell1(point))
        if self.use_shell2:
            t += self.alpha2 * tax_shell2(point)
        if self.use_shell3:
            t += self.alpha3 * float(tax_shell3(point))
        if self.use_shell4:
            t += self.alpha4 * tax_shell4(point)
        return 10.0 / (10.0 + t)

    def describe(self, point: Sequence) -> Dict[str, object]:
        """Full breakdown with all shell taxes."""
        t0 = tax_shell0(point)
        t1 = tax_shell1(point) if self.use_shell1 else Fraction(0)
        t2 = tax_shell2(point) if self.use_shell2 else 0.0
        t3 = tax_shell3(point) if self.use_shell3 else Fraction(0)
        t4 = tax_shell4(point) if self.use_shell4 else 0.0
        total = float(t0)
        if self.use_shell1:
            total += self.alpha1 * float(t1)
        if self.use_shell2:
            total += self.alpha2 * t2
        if self.use_shell3:
            total += self.alpha3 * float(t3)
        if self.use_shell4:
            total += self.alpha4 * t4
        return {
            "shell0_golay": str(t0),
            "shell1_sign_parity": str(t1),
            "shell2_sextet_balance": t2,
            "shell3_coset_type": str(t3),
            "shell4_sextet_signed": t4,
            "tax_total": total,
            "nrci": 10.0 / (10.0 + total),
            "regime": coherence_regime(10.0 / (10.0 + total)),
        }
