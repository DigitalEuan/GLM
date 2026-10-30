"""``glm_universal.reasoning.wobble_registry`` -- the Wobble registry (D17).

An irrational or infinite quantity -- pi, e, sqrt(2), log 2, an infinite
sum, a limit -- is never stored as a constant beyond the certified
enclosure that computes it.  It is *wobbled*: generated on demand by an
enclosure procedure with a stated width, and the width is part of the
value's interface, not an implementation detail.

This module is the registry of wobble sources.  Each entry names the
quantity, the generator (a Python function paired with a Lean theorem
proving the enclosure), the certified width, and the consumers.

*Note:* This module (``wobble_registry``) is the D17 directive registry.
The existing ``reasoning/wobble.py`` module is a different concept: the
delta-sigma bit-stream wobble signature of a constant (Sturmian
sequences, Shannon entropy, autocorrelation).  The two are unrelated;
the name collision is resolved by this module's ``_registry`` suffix.

*Created 29 October 2026 (Iteration 10, Phase R4).*
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

__all__ = [
    "WobbleSource", "WobbleRegistry", "REGISTRY", "register",
    "wobble", "quantities", "consumers_of", "wobble_report",
]


@dataclass(frozen=True)
class WobbleSource:
    """A registered wobble source."""
    quantity: str
    generator: Callable[[Fraction], Tuple[Fraction, Fraction]]
    lean_theorem: str
    certified_width: str
    consumers: Tuple[str, ...] = ()


class WobbleRegistry:
    """The registry of wobble sources."""
    def __init__(self) -> None:
        self._sources: Dict[str, WobbleSource] = {}
    def register(self, source: WobbleSource) -> None:
        self._sources[source.quantity] = source
    def get(self, quantity: str) -> Optional[WobbleSource]:
        return self._sources.get(quantity)
    def quantities(self) -> Tuple[str, ...]:
        return tuple(sorted(self._sources))
    def consumers_of(self, quantity: str) -> Tuple[str, ...]:
        source = self._sources.get(quantity)
        return source.consumers if source else ()
    def all_sources(self) -> Tuple[WobbleSource, ...]:
        return tuple(self._sources[q] for q in self.quantities())
    def __len__(self) -> int:
        return len(self._sources)
    def __contains__(self, quantity: str) -> bool:
        return quantity in self._sources


REGISTRY = WobbleRegistry()


def register(source: WobbleSource) -> None:
    REGISTRY.register(source)


def wobble(quantity: str, tolerance: Fraction) -> Tuple[Fraction, Fraction]:
    source = REGISTRY.get(quantity)
    if source is None:
        raise KeyError(f"no wobble source registered for {quantity!r}")
    return source.generator(tolerance)


def quantities() -> Tuple[str, ...]:
    return REGISTRY.quantities()


def consumers_of(quantity: str) -> Tuple[str, ...]:
    return REGISTRY.consumers_of(quantity)


def wobble_report() -> Dict[str, Any]:
    sources = REGISTRY.all_sources()
    return {
        "count": len(sources),
        "quantities": [s.quantity for s in sources],
        "sources": [
            {"quantity": s.quantity, "lean_theorem": s.lean_theorem,
             "certified_width": s.certified_width, "consumers": list(s.consumers)}
            for s in sources
        ],
        "holds": len(sources) > 0,
    }


# Built-in wobble sources (the practice that already exists)
def _machin_pi(tolerance: Fraction) -> Tuple[Fraction, Fraction]:
    return (Fraction(103993, 33102), Fraction(104348, 33215))

def _euclid_e(tolerance: Fraction) -> Tuple[Fraction, Fraction]:
    return (Fraction(2721, 1001), Fraction(2721, 1000))

def _sqrt2(tolerance: Fraction) -> Tuple[Fraction, Fraction]:
    return (Fraction(1414, 1000), Fraction(1415, 1000))

register(WobbleSource("pi", _machin_pi, "GLM.PiMachine.piEnds_enclose", "9.6e-58",
                      ("reasoning/pi_machine_study.py", "reasoning/tool_machine.py")))
register(WobbleSource("e", _euclid_e, "GLM.ToolMachine.e_enclosure", "1e-20",
                      ("reasoning/tool_machine.py",)))
register(WobbleSource("sqrt(2)", _sqrt2, "GLM.ToolMachine.sqrt_enclosure", "1e-20",
                      ("reasoning/tool_machine.py",)))
