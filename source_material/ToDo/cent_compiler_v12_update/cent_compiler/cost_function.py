"""
The ¢_cost function: ranks ∆ implementations by 6 axes.

Axes (lower = better):
  1. component_count     — 0 for 1 component, +2 per additional
  2. domain_consistency   — 0 if all same domain, 3 if mixed
  3. carrier_consistency  — 0 if all same carrier, 2 if mixed
  4. implementation_cost  — sum of component costs (op-amp=1, multiplier=3, ...)
  5. precision            — carrier-type precision (static=0, temporal=1, spatial=2)
  6. speed                — domain bandwidth (electrical=0, mechanical=2, thermal=4)

Total = sum of all axes. Lower total = better ∆.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
from .substrate_library import DeltaImplementationSpec


@dataclass
class CostBreakdown:
    """Cost components for a ∆ implementation."""
    component_count_score: float
    domain_consistency_score: float
    carrier_consistency_score: float
    implementation_cost_score: float
    precision_score: float
    speed_score: float
    total: float

    def render(self) -> str:
        return (f"components={self.component_count_score:.0f}, "
                f"domain={self.domain_consistency_score:.0f}, "
                f"carrier={self.carrier_consistency_score:.0f}, "
                f"cost={self.implementation_cost_score:.0f}, "
                f"precision={self.precision_score:.0f}, "
                f"speed={self.speed_score:.0f} → total={self.total:.0f}")


# Cost heuristics for each component (lower = cheaper)
COMPONENT_COST: Dict[str, int] = {
    "resistor divider": 0, "op-amp gain": 1, "gear train": 2, "lever": 1,
    "pipe area change": 1, "Gilbert cell multiplier": 3,
    "Hall effect multiplier": 3, "DC motor": 4, "rack and pinion": 3,
    "op-amp + analog multiplier in feedback loop": 2,
    "op-amp + multiplier in feedback (a/b)": 2,
    "op-amp + multiplier in feedback (1/a)": 2,
    "square-root cam (shaped profile)": 5,
    "delta-sigma modulator + sqrt lookup in feedback": 5,
    "delta-sigma modulator with equilibrium feedback": 5,
    "delta-sigma modulator (bitstream sum → integral)": 5,
    "delta-sigma phase tracker (bitstream → phase mod 2π)": 5,
    "nonlinear orifice with pressure feedback": 4,
    "op-amp with feedback network": 1, "servo motor with position feedback": 4,
    "hydraulic valve with pressure feedback": 5,
    "radiative equilibrium (Stefan-Boltzmann)": 2,
    "capacitor (Q = ∫I dt)": 1, "inductor flux linkage (λ = ∫V dt)": 1,
    "mass (p = ∫F dt)": 2, "thermal mass (Q = ∫P dt)": 2,
    "flywheel (L = ∫τ dt)": 3, "rotary encoder (θ mod 2π)": 3,
    "PLL phase detector (Δφ mod 2π)": 3,
    "interferometer fringe (Δφ mod π)": 5,
    "search coil": 2, "bifilar pendulum": 4,
    "KCL node": 0, "KVL loop": 0, "rigid body": 0, "pipe junction": 0,
    "inductor": 1, "capacitor": 1, "damper": 2, "thermal resistor": 1,
}

DOMAIN_SPEED: Dict[str, int] = {
    "electrical": 0, "digital": 1, "rotational": 1, "mechanical": 2,
    "fluidic": 3, "thermal": 4, "optical": 0, "mixed": 3,
}

CARRIER_PRECISION: Dict[str, int] = {
    "temporal": 1, "static": 0, "spatial": 2, "phase-wrap": 1, "mixed": 3,
}


def _infer_domains(components: List[str]) -> set:
    domains = set()
    for comp in components:
        for domain, keywords in [
            ("electrical", ["op-amp", "capacitor", "inductor", "resistor",
                            "gilbert", "pll", "diode", "kcl", "kvl", "multiplier"]),
            ("mechanical", ["mass", "lever", "gear", "cam", "servo", "rack",
                            "damper", "flywheel", "rigid"]),
            ("fluidic", ["orifice", "valve", "hydraulic", "pipe", "junction"]),
            ("thermal", ["thermal", "radiative", "stefan"]),
            ("digital", ["delta-sigma", "adc", "lookup"]),
            ("optical", ["interferometer"]),
            ("rotational", ["encoder", "rotor"]),
            ("electromagnetic", ["search coil", "hall"]),
        ]:
            if any(k in comp.lower() for k in keywords):
                domains.add(domain)
    return domains


def compute_cost(impl: DeltaImplementationSpec) -> CostBreakdown:
    """Compute the ¢_cost of a ∆ implementation. Lower = better."""
    n_comps = len(impl.components)
    comp_score = max(0, (n_comps - 1) * 2)

    domains = _infer_domains(impl.components)
    domain_score = 0 if len(domains) <= 1 else 3

    carrier_score = 0 if impl.carrier_type != "mixed" else 2

    impl_cost = sum(COMPONENT_COST.get(c, 3) for c in impl.components)

    precision_score = CARRIER_PRECISION.get(impl.carrier_type, 3)

    speed_score = min(DOMAIN_SPEED.get(d, 3) for d in domains) if domains else 3

    total = (comp_score + domain_score + carrier_score +
             impl_cost + precision_score + speed_score)
    return CostBreakdown(
        component_count_score=comp_score,
        domain_consistency_score=domain_score,
        carrier_consistency_score=carrier_score,
        implementation_cost_score=impl_cost,
        precision_score=precision_score,
        speed_score=speed_score,
        total=total,
    )


def rank_and_prune(
    impls: List[DeltaImplementationSpec],
    top_n: int = 10,
) -> List[Tuple[DeltaImplementationSpec, CostBreakdown]]:
    """Rank ∆ implementations by cost (ascending) and return top N.

    Deduplicates by (domain, carrier_type, is_delta_sigma) signature first
    so the top N represents DIVERSE implementations, not N copies of the
    same domain/carrier combo with minor component swaps.

    This resolves Gap 1: the £_osc combinatorial explosion (57,600 ∆)
    is pruned to the top N diverse picks.
    """
    scored = [(impl, compute_cost(impl)) for impl in impls]
    scored.sort(key=lambda x: x[1].total)

    seen_signatures = set()
    diverse = []
    for impl, cost in scored:
        sig = (impl.substrate_domain, impl.carrier_type, impl.is_delta_sigma)
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            diverse.append((impl, cost))
        if len(diverse) >= top_n:
            break
    return diverse
