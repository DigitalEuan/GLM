"""``glm_universal.reasoning.nearest_address`` -- the guarded read in the
``nearest`` kind (Phase 148).

``studies/NEAREST_ADDRESS_STUDY.md`` took the rest of item 1 of
``STATUS.md`` §2.1 (*the placement guard in the answering path*, left by
Phases 129 and 143).  Phase 143 gave the ``locate`` kind the guarded read of
the construction ladder.  The ``nearest`` kind ranked only carriers of one
register by name and refused a point or a moved carrier
(``'C moved 8 by 1/2' names no carrier``).  This module answers those
requests:

* the **ranking** -- every one of the 142 carriers of the address table,
  sorted by exact squared distance to the point (ties broken by
  ``register:name``), the scan the ``nearest`` kind has always made;
* the **guarded read** of the same point (Phase 143/144's read, junctions
  included), which certifies the head of the ranking and the gap after it.

What an answer is worth is ``GLM.NearestAddress``: when the read answers, the
head of the ranking is the read's carrier (``ranking_head_eq_read``), every
later carrier lies outside the read's margin while the head lies inside it
(``ranking_tail_outside``), and a stated move inside the margin makes the head
the carrier the point came from (``ranking_head_origin``).  When the read
refuses, the head is still the strict nearest carrier whenever there is one
(``ranking_head_of_strict``), but no margin is certified, and the answer says
so.

A request reaches this path only when it names what no register can: a move
(``<ref> moved <s> by <m> [word <k>]``) or 24 exact coordinates.  A carrier
name keeps the register ranking it always had.

Exactness
---------
Integers and :class:`fractions.Fraction` only.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import address_read as AR
from . import address_table as AT
from . import cell_guard as CG
from . import coordinate_junction as CJ

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "DEFAULT_LIMIT", "is_address_request",
    "split_request", "ranking", "nearest_read",
]

LEAN_FILE: str = "RequestProject/GLM/NearestAddress.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "ranking_head_of_strict", "ranking_head_eq_read", "ranking_tail_outside",
    "ranking_head_origin")

#: How many carriers the answer lists when the request names no count.
DEFAULT_LIMIT: int = 5

_MOVE = re.compile(r"\smoved\s+\S+\s+by\s+\S+", re.I)
_COUNTED = re.compile(r"^(?:the\s+)?(?:nearest|closest)\s+(?P<k>\d+)\s+"
                      r"(?:carriers\s+)?(?:to|of)\s+(?P<rest>.+)$", re.I)
_PLAIN = re.compile(r"^(?:what\s+is\s+)?(?:the\s+)?(?:nearest|closest)"
                    r"(?:\s+carriers?)?\s+(?:to|of)\s+(?P<rest>.+)$", re.I)
_TOP = re.compile(r"\s+top\s+(?P<k>\d+)\s*$", re.I)


def _numbers(text: str) -> int:
    body = re.sub(r"\s+within\s+\S+\s*$", "", text.strip(), flags=re.I)
    tokens = [t for t in re.split(r"[,\s]+", body) if t]
    if not tokens:
        return 0
    if all(re.fullmatch(r"[-+]?\d+(?:/\d+)?", t) for t in tokens):
        return len(tokens)
    return 0


def is_address_request(text: str) -> bool:
    """Does the operand name a point no register holds -- a move or a list of
    exact coordinates (at least two, comma separated)?"""
    text = text.strip()
    if _MOVE.search(f" {text}"):
        return True
    return "," in text and _numbers(text) >= 2


def split_request(raw: str) -> Optional[Tuple[str, Optional[int]]]:
    """``(request, limit)`` when a whole ``nearest`` query is on the address
    path, else ``None``.  ``nearest 3 to <request>``, ``nearest to <request>
    top 3`` and ``nearest to <request>`` are read."""
    text = raw.strip().rstrip("?").strip()
    limit: Optional[int] = None
    counted = _COUNTED.match(text)
    if counted:
        limit, rest = int(counted.group("k")), counted.group("rest")
    else:
        plain = _PLAIN.match(text)
        if not plain:
            return None
        rest = plain.group("rest")
    top = _TOP.search(rest)
    if top and limit is None:
        limit, rest = int(top.group("k")), rest[: top.start()]
    rest = rest.strip()
    if not is_address_request(rest):
        return None
    return rest, limit


def ranking(point: Sequence, rows=None) -> List[Tuple[int, Fraction]]:
    """Every carrier with its exact squared distance to ``point``, nearest
    first, ties broken by ``register:name`` -- a ranking in the sense of
    ``GLM.NearestAddress.Ranking``."""
    rows = rows if rows is not None else AT.carriers()
    q = tuple(Fraction(x) for x in point)
    scored = [(i, CG._nsq(q, rows[i][2])) for i in range(len(rows))]
    scored.sort(key=lambda item: (item[1], AR.carrier_label(rows, item[0])))
    return scored


def nearest_read(request: str, limit: Optional[int] = None,
                 rows=None) -> Dict[str, object]:
    """The ranking of ``request``'s point and its guarded read.

    Raises :class:`address_read.AddressError` for a request the address
    grammar refuses (``unknown-name``, ``ambiguous-name``, ``dimension``,
    ``malformed``, ``stale-table``).
    """
    rows = rows if rows is not None else AT.carriers()
    limit = DEFAULT_LIMIT if limit is None else int(limit)
    if limit < 1:
        raise AR.AddressError("malformed", f"a ranking lists at least one "
                                           f"carrier, not {limit}")
    table = AR.load_table(rows=rows)
    parts = AR.parse_request(request, rows)
    jtable, jstate = CJ.load(rows=rows)
    read = CJ.read_point(parts["point"], table, jtable, rows,
                         delta2=parts["delta2"])
    ranked = ranking(parts["point"], rows)
    best = ranked[0][1]
    tied = [i for i, d in ranked if d == best]
    out: Dict[str, object] = {
        "label": parts["label"], "point": parts["point"],
        "delta2": parts["delta2"], "origin": parts["origin"],
        "pool": len(rows), "limit": min(limit, len(rows)),
        "ranked": ranked[: min(limit, len(rows))],
        "head": ranked[0][0], "head_tied": tied,
        "second": ranked[1] if len(ranked) > 1 else None,
        "read_status": read.status, "rung": read.rung,
        "margin": read.margin, "members": tuple(read.members or ()),
        "read_carrier": read.carrier,
        "origin_certified": read.origin_certified,
        "junction_table": jstate.get("verdict"),
        "unguarded": read.unguarded,
    }
    if read.status == "answered":
        members = tuple(read.members) if read.members else (read.carrier,)
        # GLM.NearestAddress.ranking_head_eq_read: the head is the read's
        # carrier -- for a junction, the least-distance set is the junction.
        if len(members) == 1:
            agrees = tied == [read.carrier]
        else:
            agrees = sorted(tied) == sorted(members)
        if not agrees:
            raise AssertionError(
                f"nearest: the ranking's head {tied} disagrees with the "
                f"guarded read {members}; GLM.NearestAddress."
                f"ranking_head_eq_read says it cannot")
        m = read.margin
        others = [d for i, d in ranked if i not in members]
        out["gap_certified"] = m > 0 and all(d >= m * m for d in others)
        out["certified"] = True
    else:
        out["gap_certified"] = False
        out["certified"] = False
    return out
