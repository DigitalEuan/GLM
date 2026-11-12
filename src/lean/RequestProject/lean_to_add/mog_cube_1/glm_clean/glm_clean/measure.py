"""
Measure — ONE TAX, ONE NRCI, 5 shells. Nothing else.

Per the refinement: TGIC and ValueGeometry are NOT separate systems.
They're reads of the same vector. If needed, they're helper functions here.

The ONE formula:
  TAX(v) = HW(v)·Y + ‖v‖²/8
  NRCI(v) = B / (B + TAX(v))

The 5 shells are READ OPERATORS on the same data_object:
  Shell 0: HW + ‖v‖²           (sign-blind, the original)
  Shell 1: sign-parity           (sign-sensitive — needs physical expansion)
  Shell 2: sextet-balance        (MOG column distribution)
  Shell 3: coset-type            (syndrome weight / 12)
  Shell 4: sextet-signed         (finest sign pattern)
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import math

from .body import Body, Y, Z_STAR, B
from .data_object import DataObject, ROWS


SEXTET_RANGES = [(0, 6), (6, 12), (12, 18), (18, 24)]


@dataclass
class ShellBreakdown:
    """The 5-shell breakdown of a data_object's coherence."""
    shell0_golay: float
    shell1_sign_parity: float
    shell2_sextet_balance: float
    shell3_coset_type: float
    shell4_sextet_signed: float
    tax_total: float
    nrci: float
    sign_class: int
    sextet_pattern: Tuple[int, ...]


@dataclass
class CoherenceRegime:
    name: str
    nrci: float
    tax: float


class Measure:
    """ONE measurement framework. ONE TAX. ONE NRCI. 5 shells as reads."""

    def __init__(self, body: Body):
        self.body = body
        self.golay = body.golay

    # ═════════════════════════════════════════════════════════════════════
    # THE ONE TAX + NRCI
    # ═════════════════════════════════════════════════════════════════════

    def tax(self, v: DataObject) -> float:
        """TAX(v) = HW(v)·Y + ‖v‖²/8 — the ONE tax."""
        return float(self.body.tax(v.bits))

    def nrci(self, v: DataObject) -> float:
        """NRCI(v) = B / (B + TAX(v)) — the ONE coherence index."""
        return float(self.body.nrci(v.bits))

    def regime(self, v: DataObject) -> CoherenceRegime:
        nrci = self.nrci(v)
        tax = self.tax(v)
        if nrci > 0.75: name = "OnBit"
        elif nrci > 0.50: name = "Balanced"
        elif nrci > 0.25: name = "Stressed"
        else: name = "Decoherent"
        return CoherenceRegime(name=name, nrci=nrci, tax=tax)

    # ═════════════════════════════════════════════════════════════════════
    # THE 5 SHELLS (multi-resolution read of the SAME data_object)
    # ═════════════════════════════════════════════════════════════════════

    def shell0_golay(self, v: DataObject) -> float:
        hw = v.hamming_weight()
        ns = sum(b * b for b in v.bits)
        return hw * float(Y) + ns * float(Z_STAR)

    def shell1_sign_parity(self, v: DataObject) -> float:
        """Sign-parity. For binary vectors, always 0. Activate via physical expansion."""
        nonzero = [b for b in v.bits if b != 0]
        if not nonzero: return 0.0
        n_neg = sum(1 for x in nonzero if x < 0)
        n_pos = len(nonzero) - n_neg
        return abs(n_pos - n_neg) / len(nonzero)

    def shell2_sextet_balance(self, v: DataObject) -> float:
        """Coefficient of variation across 4 MOG sextets."""
        sextets = [v.bits[s:e] for s, e in SEXTET_RANGES]
        weights = [sum(abs(x) for x in s) for s in sextets]
        if max(weights) == 0: return 0.0
        mean_w = sum(weights) / 4.0
        variance = sum((w - mean_w) ** 2 for w in weights) / 4.0
        return math.sqrt(variance) / (mean_w + 1e-10)

    def shell3_coset_type(self, v: DataObject) -> float:
        """Syndrome weight / 12."""
        return self.body.syndrome_weight(v.bits) / 12.0

    def shell4_sextet_signed(self, v: DataObject) -> float:
        """L2 norm of signed sextet sums."""
        sextet_sums = [sum(v.bits[s:e]) for s, e in SEXTET_RANGES]
        norm = math.sqrt(sum(s * s for s in sextet_sums))
        max_coord = max(abs(x) for x in v.bits) if any(v.bits) else 1
        max_norm = math.sqrt(4) * max_coord * 6
        return norm / (max_norm + 1e-10)

    def describe(self, v: DataObject) -> ShellBreakdown:
        """Full 5-shell breakdown."""
        t0 = self.shell0_golay(v)
        t1 = self.shell1_sign_parity(v)
        t2 = self.shell2_sextet_balance(v)
        t3 = self.shell3_coset_type(v)
        t4 = self.shell4_sextet_signed(v)
        alpha1, alpha2, alpha3, alpha4 = 0.5, 0.3, 0.2, 0.4
        total = t0 + alpha1 * t1 + alpha2 * t2 + alpha3 * t3 + alpha4 * t4
        nrci = 10.0 / (10.0 + total)
        sign_class = sum(1 for x in v.bits if x < 0)
        sextet_pattern = tuple(sum(v.bits[s:e]) for s, e in SEXTET_RANGES)
        return ShellBreakdown(
            shell0_golay=t0, shell1_sign_parity=t1,
            shell2_sextet_balance=t2, shell3_coset_type=t3,
            shell4_sextet_signed=t4, tax_total=total, nrci=nrci,
            sign_class=sign_class, sextet_pattern=sextet_pattern,
        )

    # ═════════════════════════════════════════════════════════════════════
    # PHYSICAL EXPANSION (activates sign-sensitive shells)
    # ═════════════════════════════════════════════════════════════════════

    def expand_to_physical(self, v: DataObject, max_points: int = 64) -> List[List[int]]:
        """Expand binary vector to physical Leech points (+/-2 coords)."""
        import random
        nonzero_pos = [i for i, b in enumerate(v.bits) if b != 0]
        n = len(nonzero_pos)
        if n == 0: return [list(v.bits)]
        if n > 12:
            rng = random.Random(42)
            return [[2 if (j in nonzero_pos and rng.random() > 0.5) else (-2 if j in nonzero_pos else 0) for j in range(24)] for _ in range(max_points)]
        n_total = 2 ** n
        if n_total > max_points:
            rng = random.Random(42)
            indices = rng.sample(range(n_total), max_points)
        else:
            indices = range(n_total)
        points = []
        for idx in indices:
            point = [0] * 24
            for j, pos in enumerate(nonzero_pos):
                point[pos] = 2 if (idx >> j) & 1 == 0 else -2
            points.append(point)
        return points

    def physical_nrci_stats(self, v: DataObject, max_points: int = 32) -> Dict[str, Any]:
        """NRCI stats across physical Leech points."""
        points = self.expand_to_physical(v, max_points)
        nrcis = []
        for p in points:
            hw = sum(1 for x in p if x != 0)
            ns = sum(x * x for x in p)
            tax = hw * float(Y) + ns * float(Z_STAR)
            nonzero = [x for x in p if x != 0]
            if nonzero:
                n_neg = sum(1 for x in nonzero if x < 0)
                n_pos = len(nonzero) - n_neg
                t1 = abs(n_pos - n_neg) / len(nonzero)
            else:
                t1 = 0.0
            sw = self.body.syndrome_weight([1 if x != 0 else 0 for x in p])
            t3 = sw / 12.0
            total = tax + 0.5 * t1 + 0.2 * t3
            nrcis.append(10.0 / (10.0 + total))
        mean_n = sum(nrcis) / len(nrcis)
        return {
            "n_points": len(points),
            "mean_nrci": mean_n,
            "max_nrci": max(nrcis),
            "min_nrci": min(nrcis),
            "unique_nrci_count": len(set(round(n, 6) for n in nrcis)),
        }

    # ═════════════════════════════════════════════════════════════════════
    # COMPARISON (multi-modal distance)
    # ═════════════════════════════════════════════════════════════════════

    def compare(self, v1: DataObject, v2: DataObject) -> Dict[str, float]:
        """Multi-modal distance between two data_objects."""
        return {
            "hamming": float(v1.hamming_distance(v2)),
            "nrci_binary": float(abs(self.nrci(v1) - self.nrci(v2))),
            "nrci_physical": float(abs(
                self.physical_nrci_stats(v1, max_points=32)["max_nrci"] -
                self.physical_nrci_stats(v2, max_points=32)["max_nrci"]
            )),
            "regime_match": 0.0 if self.regime(v1).name == self.regime(v2).name else 1.0,
        }
