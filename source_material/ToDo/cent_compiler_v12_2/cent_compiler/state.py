"""Machine state, per-instruction state slots, and exact pseudo-random streams.

State ownership
---------------
Every stateful *instruction instance* owns its own slot.  ``rate`` and
``delay`` nodes no longer share a single history register, so multiple nodes in
one program behave independently.

Synchronous update discipline
-----------------------------
:class:`EvalContext` reads pre-tick state and accumulates writes.  Nothing is
committed until the caller calls :meth:`EvalContext.commit`, which is what
makes retries transactional: a failed attempt leaves the machine untouched.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from .exact import CentError, ErrorCode, Q, q
from .geometry import Carrier24, origin

_MASK64 = (1 << 64) - 1


class SplitMix64:
    """Deterministic 64-bit stream (Steele–Lea–Flood SplitMix64).

    Used by ``¢_noise``.  This is a *deterministic* stream, not a physical
    entropy source; the noise primitive's documented distribution is the
    discrete two-point law ``±a`` with probability 1/2, whose mean and variance
    are exact rationals.
    """

    def __init__(self, seed: int = 0):
        self.state = int(seed) & _MASK64

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK64
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
        return (z ^ (z >> 31)) & _MASK64

    def next_bit(self) -> int:
        return self.next_u64() >> 63

    def sign(self) -> int:
        return 1 if self.next_bit() else -1

    def fork(self, salt: int) -> "SplitMix64":
        return SplitMix64(self.next_u64() ^ (int(salt) & _MASK64))

    def as_dict(self) -> dict[str, int]:
        return {"state": self.state}


@dataclass
class MachineState:
    """Global registers plus per-instruction state slots."""

    accumulator: Q = field(default_factory=lambda: q(0))
    grid_position: Carrier24 = field(default_factory=origin)
    slots: dict[str, dict[str, Any]] = field(default_factory=dict)
    clock: int = 0
    seed: int = 0
    hysteresis_bit: bool = False  # legacy scalar register, retained for the old API

    def __post_init__(self) -> None:
        object.__setattr__(self, "accumulator", q(self.accumulator))
        if not isinstance(self.slots, dict):
            raise CentError(ErrorCode.TYPE_ERROR, "slots must be a dict")
        if self.clock < 0:
            raise CentError(ErrorCode.INVALID_INPUT, "clock must be nonnegative")

    # -- slots ------------------------------------------------------------
    def slot(self, key: str) -> dict[str, Any]:
        return self.slots.get(key, {})

    def with_slot(self, key: str, value: dict[str, Any]) -> "MachineState":
        new_slots = dict(self.slots)
        new_slots[key] = value
        return MachineState(
            accumulator=self.accumulator,
            grid_position=self.grid_position,
            slots=new_slots,
            clock=self.clock,
            seed=self.seed,
            hysteresis_bit=self.hysteresis_bit,
        )

    def copy(self) -> "MachineState":
        return copy.deepcopy(self)

    def snapshot(self) -> "MachineState":
        return self.copy()

    def restore(self, snapshot: "MachineState") -> "MachineState":
        return snapshot.copy()

    def as_dict(self) -> dict[str, Any]:
        return {
            "accumulator": str(self.accumulator),
            "grid_position": [str(x) for x in self.grid_position],
            "clock": self.clock,
            "seed": self.seed,
            "hysteresis_bit": self.hysteresis_bit,
            "slots": copy.deepcopy(self.slots),
        }


@dataclass
class EvalContext:
    """Reads pre-tick state; writes are applied only on ``commit``."""

    state: MachineState
    clock: int = 0
    writes: dict[str, dict[str, Any]] = field(default_factory=dict)
    random: Optional[SplitMix64] = None

    def __post_init__(self) -> None:
        if self.random is None:
            self.random = SplitMix64(self.state.seed)

    def read_slot(self, key: str) -> dict[str, Any]:
        return self.state.slot(key)

    def write_slot(self, key: str, value: dict[str, Any]) -> None:
        self.writes[key] = value

    def commit(self) -> MachineState:
        slots = dict(self.state.slots)
        slots.update(self.writes)
        new_state = MachineState(
            accumulator=self.state.accumulator,
            grid_position=self.state.grid_position,
            slots=slots,
            clock=self.state.clock,
            seed=self.state.seed,
            hysteresis_bit=self.state.hysteresis_bit,
        )
        return new_state

    def next_clock(self, state: MachineState) -> MachineState:
        """Return a committed state with the clock advanced by one tick."""
        committed = self.commit()
        return MachineState(
            accumulator=committed.accumulator,
            grid_position=committed.grid_position,
            slots=committed.slots,
            clock=state.clock + 1,
            seed=state.seed,
            hysteresis_bit=committed.hysteresis_bit,
        )
