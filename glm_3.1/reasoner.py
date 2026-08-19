#!/usr/bin/env python3
"""
GLM Reasoner — wraps glm_lean/glm3's MonsterReasoner for the new unified GLM.

This module provides:
  - Exact equation verification (audit)
  - Formula discovery (solve)
  - Buckingham Pi dimensionless groups
  - Concept meaning (exact rational exponents)
  - Carrier derivation (Leech lattice point from meaning)
  - Monster addresses, Griess similarity, relation words
  - Concept listing and identification

All math is exact — Fraction arithmetic, no floats in reasoning.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Sequence
from fractions import Fraction as F

# ── Path setup ──────────────────────────────────────────────────────────
_REPO = Path(__file__).resolve().parent.parent
_GLM3 = _REPO / "glm_lean" / "glm3"
_GLM2 = _REPO / "glm_lean" / "glm2"
_GLM1 = _REPO / "glm_lean" / "glm"

for p in [str(_GLM3), str(_GLM2), str(_GLM1)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Import the GLM-3 stack ─────────────────────────────────────────────
try:
    from glm3_reasoner import MonsterReasoner
    from glm2_meaning import Meaning
    from glm2_library import CONCEPTS, ALIASES
    _GLM3_AVAILABLE = True
except ImportError as e:
    print(f"[reasoner] GLM-3 not available: {e}")
    _GLM3_AVAILABLE = False

# ── Meaning types (re-export) ───────────────────────────────────────────
# Meaning = (10 rational exponents, decimal scale, tensor rank, P/T/C parities)
# Axes: L, M, T, I, H, N, J, A, S, B
#   L = length, M = mass, T = time, I = current, H = temperature
#   N = amount, J = luminous intensity, A = plane angle, S = solid angle
#   B = information


class GLMReasoner:
    """
    The unified reasoner: exact dimensional reasoning via the Monster.

    Usage:
        r = GLMReasoner()
        r.audit("energy", "mass*speed^2")        # True equation
        r.solve("speed", ["energy", "mass"])      # discovers speed = sqrt(E/m)
        r.meaning("energy")                        # exact rational exponents
        r.nearest("energy")                        # Griess-space neighbours
        r.list_concepts()                          # all 660 concepts
    """

    def __init__(self):
        if not _GLM3_AVAILABLE:
            raise RuntimeError("GLM-3 stack not available. Run from GLM repo root.")
        self._mr = MonsterReasoner()
        self._cache: Dict[str, Any] = {}

    # ── Core reasoning (exact) ──────────────────────────────────────────

    def audit(self, lhs: str, rhs: str) -> Dict[str, Any]:
        """Check if lhs and rhs have the same dimensions. Returns verdict."""
        result = self._mr.audit(lhs, rhs)
        return {
            "lhs": lhs,
            "rhs": rhs,
            "pass": bool(result.admissible) if hasattr(result, 'admissible') else bool(result),
            "reasons": result.reasons() if hasattr(result, 'reasons') else [],
        }

    def solve(self, target: str, sources: Sequence[str]) -> Dict[str, Any]:
        """Derive formula for `target` in terms of `sources` via Smith normal form."""
        result = self._mr.solve(target, sources)
        return {
            "target": target,
            "sources": list(sources),
            "solvable": result.solvable if hasattr(result, "solvable") else False,
            "formula": str(result) if result else None,
        }

    def pi_groups(self, names: Sequence[str]) -> List[Dict[str, Any]]:
        """Extract Buckingham Pi dimensionless groups."""
        raw = self._mr.base.pi_groups(names)
        # Convert Fraction values to strings for JSON serialization
        return [{k: str(v) for k, v in group.items()} for group in raw]

    # ── Meaning & carrier ───────────────────────────────────────────────

    def meaning(self, text: str) -> Dict[str, Any]:
        """Get the exact meaning of a concept (10 rational exponents + metadata)."""
        m = self._mr.meaning(text)
        v = m.vector()  # tuple of 11 Fractions (10 exponents + scale)
        axes = ["L", "M", "T", "I", "H", "N", "J", "A", "S", "B"]
        return {
            "text": text,
            "exponents": {axes[i]: str(v[i]) for i in range(10)},
            "scale": str(m.scale),
            "rank": m.rank,
            "parities": {"P": m.p, "T": m.t, "C": m.c},
            "kind": m.kind,
            "domain": m.domain,
            "signature": str(m.signature) if hasattr(m, 'signature') else "",
        }

    def carrier(self, text: str) -> Tuple[int, ...]:
        """Get the Leech lattice point derived from the concept's meaning."""
        return self._mr.carrier(text)

    def identify(self, text: str) -> Dict[str, Any]:
        """Identify a concept — find its meaning, carrier, and properties."""
        return self._mr.identify(text)

    # ── Monster layer ───────────────────────────────────────────────────

    def address(self, text: str) -> Dict[str, Any]:
        """Get the Monster address of a concept."""
        return self._mr.address(text)

    def similarity(self, a: str, b: str) -> float:
        """Griess algebra inner product between two concepts."""
        s = self._mr.similarity(a, b)
        return float(s) if not isinstance(s, str) else float(s)

    def distance(self, a: str, b: str) -> str:
        """Exact distance between two concepts in Griess space."""
        return self._mr.distance(a, b)

    def nearest(self, name: str, count: int = 8) -> List[Tuple[str, float]]:
        """Nearest neighbours in Griess algebra space."""
        raw = self._mr.nearest(name, count)
        # glm3 returns (name, similarity_as_string) — convert to float
        return [(n, float(s)) for n, s in raw]

    def relation(self, a: str, b: str) -> Dict[str, Any]:
        """Get the 10-letter type-code relation between two concepts."""
        return self._mr.relation(a, b)

    def cluster(self, threshold: float = 0.05) -> List[List[str]]:
        """Single-linkage clustering of concepts by Griess distance."""
        return self._mr.cluster(F(threshold))

    # ── Library ─────────────────────────────────────────────────────────

    def list_concepts(self, domain: Optional[str] = None) -> List[str]:
        """List all concepts, optionally filtered by domain."""
        return self._mr.list_concepts(domain)

    def domains(self) -> List[str]:
        """List all concept domains."""
        return sorted(set(
            self._mr.meaning(c).domain
            for c in self._mr.list_concepts()
        ))

    def ledger(self) -> Dict[str, Any]:
        """The 196,884 eigenvalue ledger of the Griess algebra."""
        return self._mr.ledger()

    # ── Verification ────────────────────────────────────────────────────

    def verify_equations(self, equations: List[Tuple[str, str, str]]) -> List[Dict]:
        """
        Verify a list of (lhs, rhs, label) equations.
        Returns list of {label, lhs, rhs, pass, reasons}.
        """
        results = []
        for lhs, rhs, label in equations:
            r = self.audit(lhs, rhs)
            r["label"] = label
            results.append(r)
        return results

    def quick_test(self) -> Dict[str, Any]:
        """Run a quick self-test: audit, solve, meaning, nearest."""
        results = {}

        # True equations
        true_eqs = [
            ("energy", "mass*speed^2", "E=mc^2"),
            ("force", "mass*acceleration", "F=ma"),
            ("power", "force*speed", "P=Fv"),
            ("torque", "moment(position, force)", "τ=r×F"),
            ("pressure", "force/area", "p=F/A"),
        ]
        results["true_equations"] = self.verify_equations(true_eqs)

        # False equations
        false_eqs = [
            ("energy", "mass*speed^4", "E=mc^4 (wrong)"),
            ("force", "mass*speed", "F=mc (wrong)"),
        ]
        results["false_equations"] = self.verify_equations(false_eqs)

        # Solve
        results["solve_speed"] = self.solve("speed", ["energy", "mass"])
        results["solve_force"] = self.solve("force", ["mass", "acceleration"])

        # Meaning
        results["meaning_energy"] = self.meaning("energy")
        results["meaning_torque"] = self.meaning("torque")

        # Nearest
        results["nearest_energy"] = [
            (name, float(sim)) for name, sim in self.nearest("energy", 5)
        ]

        return results
