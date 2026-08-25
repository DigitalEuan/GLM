"""``glm_universal.reasoning.periodic_table`` -- the table's own coordinates.

What it does
------------
Gives every atomic number ``Z`` its position in the periodic table: a period,
a group, and a block.  The chemistry register stores ``z``, ``period`` and a
``group_block`` *category* (``"Noble gas"``, ``"Metalloid"``, ...), but not the
group number, and a category is not a coordinate: ``B`` is a metalloid and
``Al`` is a post-transition metal, yet they are one below the other in group
13.  Without the group number an analogy like ``B : Al :: C : ?`` cannot be
transported along the table at all, which is why it used to be answered with
the nearest element in property space (``P``, one place too far) rather than
with ``Si``.

How the position is derived
---------------------------
Not tabulated element by element -- computed from the period boundaries, which
are the only inputs:

    period 1  Z = 1..2      2 elements     s
    period 2  Z = 3..10     8 elements     s p
    period 3  Z = 11..18    8 elements     s p
    period 4  Z = 19..36   18 elements     s d p
    period 5  Z = 37..54   18 elements     s d p
    period 6  Z = 55..86   32 elements     s f d p
    period 7  Z = 87..118  32 elements     s f d p

Within a period the index of an element fixes its group by the width of the
period: a 2-wide period holds groups 1 and 18; an 8-wide period holds 1, 2 and
then 13..18; an 18-wide period holds 1..18 in order; a 32-wide period holds 1,
2, then the fourteen f-block elements -- all of which sit in group 3 -- and
then 4..18.

Two consequences are stated rather than hidden.  Group 3 of periods 6 and 7 is
**not** a single element: it holds fifteen (the f-block plus the d-block entry),
so :func:`atomic_number_at` refuses that position instead of choosing one.  And
hydrogen is placed in group 1 by the same arithmetic that places every other
element; the table's own convention, not a special case.

Every figure the package publishes about the table comes from
:func:`periodic_report`, which re-derives the whole map and checks it against
the register's stored periods.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from ..data_objects import elements as do_elements

__all__ = [
    "PERIOD_BOUNDS", "MAX_Z", "Position", "PositionError",
    "position_of", "atomic_number_at", "symbol_at", "position_of_symbol",
    "periodic_report",
]


class PositionError(ValueError):
    """Raised when a table position is out of range or not a single element."""


#: ``(period, first Z, last Z)`` for each of the seven periods.  These bounds
#: are the module's only tabulated input; everything else is derived.
PERIOD_BOUNDS: Tuple[Tuple[int, int, int], ...] = (
    (1, 1, 2),
    (2, 3, 10),
    (3, 11, 18),
    (4, 19, 36),
    (5, 37, 54),
    (6, 55, 86),
    (7, 87, 118),
)

#: The largest atomic number the register carries.
MAX_Z: int = PERIOD_BOUNDS[-1][2]


@dataclass(frozen=True)
class Position:
    """Where an element sits: period, group, block, and its index in the period.

    ``group`` is 3 for every f-block element, which is where the f-block sits
    in the eighteen-column table.  ``block`` distinguishes them.
    """

    z: int
    period: int
    group: int
    block: str
    index_in_period: int

    def as_dict(self) -> Dict[str, object]:
        return {"z": self.z, "period": self.period, "group": self.group,
                "block": self.block, "index_in_period": self.index_in_period}


def position_of(z: int) -> Position:
    """The table position of atomic number ``z``.

    >>> position_of(5).group, position_of(13).group          # B and Al
    (13, 13)
    >>> position_of(2).group, position_of(36).group          # He and Kr
    (18, 18)
    """
    z = int(z)
    if not 1 <= z <= MAX_Z:
        raise PositionError(f"position_of: Z = {z} is outside 1..{MAX_Z}")
    for period, lo, hi in PERIOD_BOUNDS:
        if lo <= z <= hi:
            index = z - lo + 1
            width = hi - lo + 1
            if width == 2:
                group, block = (1, "s") if index == 1 else (18, "s")
            elif width == 8:
                if index <= 2:
                    group, block = index, "s"
                else:
                    group, block = index + 10, "p"
            elif width == 18:
                group = index
                block = "s" if index <= 2 else "d" if index <= 12 else "p"
            else:                                   # width == 32
                if index <= 2:
                    group, block = index, "s"
                elif index <= 16:
                    group, block = 3, "f"
                else:
                    group = index - 14
                    block = "d" if group <= 12 else "p"
            return Position(z=z, period=period, group=group, block=block,
                            index_in_period=index)
    raise PositionError(f"position_of: Z = {z} matched no period")   # pragma: no cover


def atomic_number_at(period: int, group: int) -> int:
    """The atomic number at a table position.

    Raises
    ------
    PositionError
        If the position is empty, or -- for group 3 of periods 6 and 7 -- if
        it holds fifteen elements rather than one.  Both refusals are the
        honest answer: the position does not name an element.
    """
    period, group = int(period), int(group)
    if not 1 <= group <= 18:
        raise PositionError(f"atomic_number_at: group {group} is outside 1..18")
    matches = [z for z in range(1, MAX_Z + 1)
               if (p := position_of(z)).period == period and p.group == group]
    if not matches:
        raise PositionError(
            f"atomic_number_at: period {period}, group {group} is empty")
    if len(matches) > 1:
        raise PositionError(
            f"atomic_number_at: period {period}, group {group} holds "
            f"{len(matches)} elements (the f-block sits there), so it names "
            f"no single element")
    return matches[0]


@lru_cache(maxsize=1)
def _symbol_by_z() -> Dict[int, str]:
    return {int(o.attributes["z"]): o.name
            for o in do_elements.element_objects()}


@lru_cache(maxsize=1)
def _z_by_symbol() -> Dict[str, int]:
    return {symbol: z for z, symbol in _symbol_by_z().items()}


def symbol_at(period: int, group: int) -> str:
    """The element symbol at a table position; refuses as :func:`atomic_number_at`."""
    return _symbol_by_z()[atomic_number_at(period, group)]


def position_of_symbol(symbol: str) -> Position:
    """The table position of an element symbol, e.g. ``"Al"``."""
    try:
        z = _z_by_symbol()[str(symbol)]
    except KeyError as exc:
        raise PositionError(
            f"position_of_symbol: {symbol!r} is not a register element") from exc
    return position_of(z)


def periodic_report() -> Dict[str, object]:
    """Re-derive the whole map and check it against the register.

    The check that matters is ``periods_agree_with_register``: the derived
    period of every element must equal the period the chemistry register
    stores for it.  The derivation and the stored data come from different
    places, so agreement over all 118 is evidence and not a tautology.
    """
    positions = {z: position_of(z) for z in range(1, MAX_Z + 1)}
    stored = {int(o.attributes["z"]): int(o.attributes["period"])
              for o in do_elements.element_objects()}
    disagreements = sorted(z for z, p in positions.items()
                           if stored.get(z) != p.period)
    by_block: Dict[str, int] = {}
    for position in positions.values():
        by_block[position.block] = by_block.get(position.block, 0) + 1
    by_group: Dict[int, int] = {}
    for position in positions.values():
        by_group[position.group] = by_group.get(position.group, 0) + 1
    ambiguous: List[str] = []
    for period, _lo, _hi in PERIOD_BOUNDS:
        for group in range(1, 19):
            try:
                atomic_number_at(period, group)
            except PositionError as exc:
                if "holds" in str(exc):
                    ambiguous.append(f"period {period}, group {group}")
    return {
        "elements": len(positions),
        "periods": len(PERIOD_BOUNDS),
        "groups": 18,
        "by_block": dict(sorted(by_block.items())),
        "by_group": dict(sorted(by_group.items())),
        "periods_agree_with_register": not disagreements,
        "disagreements": disagreements,
        "ambiguous_positions": ambiguous,
        "noble_gases": [symbol_at(p, 18) for p, _lo, _hi in PERIOD_BOUNDS],
        "group_13": [symbol_at(p, 13) for p, _lo, _hi in PERIOD_BOUNDS
                     if p >= 2],
    }
