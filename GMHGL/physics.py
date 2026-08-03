from __future__ import annotations
"""UBP Condensed Module: physics"""


# --- Extracted from metrics_exact.py ---
"""
UBP Metrics (Exact) v4.x
=======================

Version: 4
Author: Euan R A Craig, New Zealand
Date: 02 January 2026

Goal: strict float-free metrics suitable for core UBP logic.

Design rules:
- No floats, no UBPUltimateSubstrate.get_pi(50), no numpy.
- All computations return Fractions (or ints / enums).
- π is represented as a rational approximation derived from *integer* continued fraction coefficients.
  This keeps the entire system float-free while remaining deterministic and reproducible.

IMPORTANT:
- If you want an absolutely symbolic π (unevaluated), replace `pi_approx()` usage with an expression
  object of your choice. This module keeps things runnable without external dependencies.
"""
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Dict, Optional
from ubp_unified_v5 import BinaryLinearAlgebra, GOLAY_ENGINE, LEECH_ENGINE, SUBSTRATE, UBPUltimateSubstrate

class CoherenceRegime(Enum):
    ONBIT = 'OnBit'
    COHERENT = 'Coherent'
    TRANSITIONAL = 'Transitional'
    SUBCOHERENT = 'Subcoherent'
_PI_CF = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2, 1, 84, 2, 1, 1, 15]

def _cf_to_fraction(a) -> Fraction:
    """Convert continued fraction coefficients to a Fraction, exact."""
    if not a:
        raise ValueError('continued fraction coefficients empty')
    x = Fraction(a[-1], 1)
    for c in reversed(a[:-1]):
        x = Fraction(c, 1) + Fraction(1, x)
    return x

def pi_approx(terms: int=10) -> Fraction:
    """
    Deterministic rational approximation of π using `terms` CF coefficients.
    terms=5 gives 355/113.
    """
    if terms < 1:
        raise ValueError('terms must be >= 1')
    terms = min(terms, len(_PI_CF))
    return _cf_to_fraction(_PI_CF[:terms])

@dataclass(frozen=True)
class UBPConstantsExact:
    PI_TERMS: int = 6
    PGCI_TARGET: Fraction = Fraction(9999999, 10000000)

    def pi(self) -> Fraction:
        return pi_approx(self.PI_TERMS)

    def observer_fixed_point(self) -> Fraction:
        p = self.pi()
        return p + Fraction(2, 1) / p

    def y_constant(self) -> Fraction:
        return Fraction(1, 1) / self.observer_fixed_point()

class UBPObserverExact:

    def __init__(self, c: UBPConstantsExact):
        self.c = c

    def get_base_cost(self) -> Fraction:
        return self.c.observer_fixed_point()

    def calculate_realm_cost(self, realm_complexity: Fraction=Fraction(1, 1), dimensions: int=6) -> Fraction:
        return self.get_base_cost() * realm_complexity * Fraction(dimensions, 6)

class UBPCoherenceExact:

    @staticmethod
    def calculate_holographic_nrci(tax: Fraction, constants: Dict[str, Fraction]) -> Fraction:
        """
        [LAW_HOLO_BOUND_001] v6.4.0 Refined Holographic NRCI.
        Scales the Leech Kissing Number entropy by the Observer Constant (Y).
        """
        # S_holo = log2(196560) approx 17.58496
        s_holo = Fraction(1758496, 100000)
        y = constants['Y']
        ten = Fraction(10, 1)
        
        # Formula: 10 / (10 + Tax + (S_holo * Y))
        return ten / (ten + tax + (s_holo * y))

    @staticmethod
    def clamp01(x: Fraction) -> Fraction:
        if x < 0:
            return Fraction(0, 1)
        if x > 1:
            return Fraction(1, 1)
        return x

    @staticmethod
    def calculate_nrci(observed_variance: Fraction, theoretical_variance: Fraction=Fraction(1, 1)) -> Fraction:
        if theoretical_variance == 0:
            raise ZeroDivisionError('theoretical_variance must be nonzero')
        return UBPCoherenceExact.clamp01(Fraction(1, 1) - observed_variance / theoretical_variance)

    @staticmethod
    def get_regime(nrci_value: Fraction, target: Fraction) -> CoherenceRegime:
        if nrci_value >= target:
            return CoherenceRegime.ONBIT
        if nrci_value >= Fraction(1, 2):
            return CoherenceRegime.COHERENT
        if nrci_value >= Fraction(1, 10):
            return CoherenceRegime.TRANSITIONAL
        return CoherenceRegime.SUBCOHERENT

class UBPMetricsExact:

    def analyze_state(self, variance: Fraction, realm: str='standard', is_quantum: bool=False) -> Dict[str, object]:
        nrci = self.coherence.calculate_nrci(variance)
        
        # v6.4.0 Ultra-Fine Audit
        if is_quantum:
            # Local import to bypass environment cache issues
            from ubp_unified_v5 import UBPUltimateSubstrate
            c = UBPUltimateSubstrate.get_v6_constants()
            # Treat variance as Tax for this calculation
            nrci = self.coherence.calculate_holographic_nrci(variance, c)
            
        regime = self.coherence.get_regime(nrci, self.constants.PGCI_TARGET)
        return {
            'nrci': nrci, 
            'regime': regime.value, 
            'observer_cost': self.observer.get_base_cost(), 
            'is_stable': nrci >= Fraction(42, 100) # Noise Floor check
        }
