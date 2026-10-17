"""``glm_universal.reasoning.address_read`` -- a ladder carrier read by its
address, under the placement guard (Phase 143).

``studies/ADDRESS_READ_STUDY.md``.  The `locate` query kind's operation: a
point of 24 exact coordinates goes in, and either a named carrier comes out,
certified to be the strictly nearest of the 142, or a refusal that says rung
by rung why no carrier could be certified.

The read
--------
The point is quantised at each rung of the ladder in the middle-out order.
At the first rung whose cell holds exactly one carrier ``i`` and whose
placement guard holds,

    ``|q - c_i| + |q - p| < rho_p``,

decided exactly (``GLM.CellGuard.sqrt_add_lt_sqrt_iff``), the read answers
``i``.  ``rho_p`` is read from the stored table
(:mod:`glm_universal.reasoning.address_table`), which is used only while the
digests it is kept beside hold.  ``RequestProject/GLM/AddressRead.lean``
proves:

* ``read_strict_nearest`` / ``read_agrees_with_scan`` -- an answer is the
  strictly nearest carrier, the one a full scan finds;
* ``read_order_independent`` -- any visiting order gives the same answer;
* ``read_unique_in_ball`` -- the answer is the only carrier within the margin
  ``D = rho_p - |q - p|`` of the point, and :func:`margin_bound` reports a
  rational lower bound on ``D`` that never overstates it (``margin_lower``);
* ``read_origin`` -- if the request says the point is a carrier moved by at
  most ``delta`` and ``delta + |q - p| < rho_p``, the answer is that carrier.

The read uses two distances per rung it tries; it never scans the carriers.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout.  No float, no
randomness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import isqrt
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import construction_ladder as CL
from . import address_table as AT
from . import cell_guard as CG
from . import ladder_escalation as LE
from . import norm256_hex as NH
from . import placement_guard as PG

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "LADDER", "ORDER", "REGISTERS",
    "AddressError", "Read", "resolve", "parse_request", "margin_bound",
    "read_point", "load_table", "carrier_label", "margin_text",
]

LEAN_FILE = "RequestProject/GLM/AddressRead.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "guarded_eq_some", "entry_unique_in_ball", "read_eq_some",
    "read_strict_nearest", "read_agrees_with_scan", "read_order_independent",
    "read_unique_in_ball", "read_origin", "read_none_iff", "margin_lower")

LADDER: Tuple[str, ...] = AT.LADDER
ORDER: Tuple[str, ...] = CL.middle_out_order(LADDER)

#: The registers the 142 carriers are drawn from.
REGISTERS: Tuple[str, ...] = ("physics", "chemistry", "molecules",
                              "mathematics", "harmonics", "lexicon")

#: The decimal places of the reported margin.
MARGIN_SCALE = 1000

Point = Tuple[int, ...]
Vector = Tuple[Fraction, ...]


class AddressError(ValueError):
    """A request the read refuses, with a short machine-readable reason:
    ``stale-table``, ``unknown-name``, ``ambiguous-name``, ``dimension`` or
    ``malformed``."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def carrier_label(rows, i: int) -> str:
    """``register:name`` of carrier ``i``."""
    return f"{rows[i][0]}:{rows[i][1]}"


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE TABLE, CHECKED AGAINST ITS DIGESTS
# ═════════════════════════════════════════════════════════════════════════

def load_table(stored: Optional[Dict[str, object]] = None, rows=None
               ) -> Dict[str, Dict[Point, Tuple[str, object]]]:
    """The parsed table, or :class:`AddressError` ``stale-table`` naming the
    digests that do not hold and the command that re-takes it."""
    rows = rows if rows is not None else AT.carriers()
    stored = stored if stored is not None else AT.measurements()
    st = AT.state(stored, rows)
    if not st["fresh"]:
        raise AddressError(
            "stale-table",
            f"the stored address table is {st['verdict']} "
            f"({', '.join(st['failed'])} digest does not hold), so no radius "
            f"in it can be trusted; re-take it with `PYTHONPATH=. python3 -m "
            f"glm_universal.tools address-table --write`")
    try:
        return AT.parse(stored)                        # type: ignore[arg-type]
    except (KeyError, TypeError, ValueError) as error:  # pragma: no cover
        raise AddressError("stale-table",
                           f"the stored address table does not parse: "
                           f"{error}") from None


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE REQUEST
# ═════════════════════════════════════════════════════════════════════════

def _fold(text: str) -> str:
    return re.sub(r"[\s_]+", " ", text.strip().lower())


def resolve(ref: str, rows) -> int:
    """The index of the carrier ``ref`` names: ``name`` or
    ``register:name``; exact spelling first, then case and ``_``/space
    folded."""
    ref = ref.strip()
    register = None
    name = ref
    if ":" in ref:
        register, name = (part.strip() for part in ref.split(":", 1))
        if register not in REGISTERS:
            raise AddressError("unknown-name",
                               f"{register!r} is not one of the registers "
                               f"the 142 carriers are drawn from "
                               f"({', '.join(REGISTERS)})")
    pool = [i for i, row in enumerate(rows)
            if register is None or row[0] == register]
    hits = [i for i in pool if rows[i][1] == name]
    if not hits:
        hits = [i for i in pool if _fold(rows[i][1]) == _fold(name)]
    if not hits:
        raise AddressError("unknown-name",
                           f"{ref!r} names none of the 142 carriers the "
                           f"address table holds")
    if len(hits) > 1:
        raise AddressError("ambiguous-name",
                           f"{ref!r} names {len(hits)} carriers: "
                           f"{', '.join(carrier_label(rows, i) for i in hits)}"
                           f"; say which register")
    return hits[0]


def _fraction(token: str, what: str) -> Fraction:
    try:
        return Fraction(token.strip())
    except (ValueError, ZeroDivisionError):
        raise AddressError("malformed",
                           f"{token.strip()!r} is not an exact number "
                           f"({what})") from None


def _integer(token: str, what: str) -> int:
    value = _fraction(token, what)
    if value.denominator != 1:
        raise AddressError("malformed", f"{token!r} is not an integer "
                                        f"({what})")
    return int(value)


_MOVED = re.compile(r"^(?P<ref>.+?)\s+moved\s+(?P<s>\S+)\s+by\s+(?P<m>\S+)"
                    r"(?:\s+word\s+(?P<k>\S+))?\s*$")
_WITHIN = re.compile(r"^(?P<coords>.*?)\s+within\s+(?P<d>\S+)\s*$")


def parse_request(text: str, rows=None) -> Dict[str, object]:
    """Read a `locate` request.

    Returns ``point`` (24 exact coordinates), ``delta2`` (the squared bound
    on the move, or ``None``), ``origin`` (the carrier the point was made
    from, or ``None``) and ``label`` (what the request named).
    """
    rows = rows if rows is not None else AT.carriers()
    text = text.strip()
    if not text:
        raise AddressError("malformed", "no carrier and no point to locate")
    looks_numeric = "," in text or re.match(r"^[-+]?\d", text) is not None
    if looks_numeric:
        delta2 = None
        coords_text = text
        within = _WITHIN.match(text)
        if within:
            coords_text = within.group("coords")
            d = _fraction(within.group("d"), "the bound after `within`")
            if d < 0:
                raise AddressError("malformed", "a bound on a move is not "
                                                "negative")
            delta2 = d * d
        tokens = [t for t in re.split(r"[,\s]+", coords_text.strip()) if t]
        point = tuple(_fraction(t, "a coordinate") for t in tokens)
        if len(point) != LE.DIM:
            raise AddressError("dimension",
                               f"a carrier has {LE.DIM} coordinates; the "
                               f"request gives {len(point)}")
        return {"point": point, "delta2": delta2, "origin": None,
                "label": "the given point"}
    moved = _MOVED.match(text)
    if moved:
        ref = moved.group("ref")
        support = _integer(moved.group("s"), "the number of coordinates moved")
        if not 1 <= support <= LE.DIM:
            raise AddressError("malformed",
                               f"a move touches between 1 and {LE.DIM} "
                               f"coordinates, not {support}")
        magnitude = _fraction(moved.group("m"), "the size of the move")
        if magnitude <= 0:
            raise AddressError("malformed", "the size of a move is positive")
    else:
        ref = text
        support = 0
        magnitude = Fraction(0)
    if re.search(r"\s(moved|by|word|within)\s", f" {text} ") and not moved:
        raise AddressError("malformed",
                           f"{text!r}: a move is `moved <s> by <m> "
                           f"[word <k>]`")
    try:
        origin = resolve(ref, rows)
    except AddressError as error:
        if error.reason != "unknown-name" or " " not in ref.strip():
            raise
        words = ref.split()
        for cut in range(len(words) - 1, 0, -1):
            try:
                resolve(" ".join(words[:cut]), rows)
            except AddressError:
                continue
            raise AddressError("malformed",
                               f"unread words after the carrier "
                               f"{' '.join(words[:cut])!r}: "
                               f"{' '.join(words[cut:])!r}") from None
        raise
    carrier = rows[origin][2]
    if support:
        word = (_integer(moved.group("k"), "the codeword index")
                if moved.group("k") is not None else origin)
        if word < 0:
            raise AddressError("malformed", "a codeword index is not "
                                            "negative")
        point = tuple(LE.perturb(carrier, word, support, magnitude))
        label = (f"{carrier_label(rows, origin)} moved on {support} "
                 f"coordinates by {magnitude} (codeword {word})")
    else:
        point = tuple(Fraction(x) for x in carrier)
        label = carrier_label(rows, origin)
    return {"point": point, "delta2": support * magnitude * magnitude,
            "origin": origin, "label": label}


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE READ
# ═════════════════════════════════════════════════════════════════════════

def margin_bound(rho2: Fraction, b2: Fraction,
                 scale: int = MARGIN_SCALE) -> Fraction:
    """A rational lower bound on ``sqrt(rho2) - sqrt(b2)``: ``a - b`` with
    ``a^2 <= rho2`` and ``b^2 >= b2`` at ``scale`` (``margin_lower``)."""
    a = Fraction(isqrt(int(rho2 * scale * scale)), scale)
    n = -((-b2 * scale * scale) // 1)              # ceiling
    s = isqrt(int(n))
    if s * s < n:
        s += 1
    return a - Fraction(s, scale)


def margin_text(margin: Fraction) -> str:
    """The margin as a decimal with three places (exact: its denominator
    divides :data:`MARGIN_SCALE`)."""
    scaled = margin * MARGIN_SCALE
    sign = "-" if scaled < 0 else ""
    whole, part = divmod(abs(int(scaled)), MARGIN_SCALE)
    return f"{sign}{whole}.{part:03d}"


@dataclass
class Read:
    """One read of one point."""

    point: Vector
    status: str                         # "answered" | "refused"
    carrier: Optional[int] = None
    rung: Optional[str] = None
    cell: Optional[Point] = None
    a2: Optional[Fraction] = None       # |q - c_i|^2
    b2: Optional[Fraction] = None       # |q - p|^2
    rho2: Optional[Fraction] = None
    margin: Optional[Fraction] = None
    origin_certified: Optional[bool] = None
    unguarded: Optional[Tuple[int, str]] = None
    rows: List[Dict[str, object]] = field(default_factory=list)


def read_point(point: Sequence, table, rows=None,
               order: Sequence[str] = ORDER,
               delta2: Optional[Fraction] = None) -> Read:
    """Walk ``order``; answer at the first rung whose guard holds."""
    rows = rows if rows is not None else AT.carriers()
    q = tuple(Fraction(x) for x in point)
    out = Read(point=q, status="refused")
    for rung in order:
        cell = NH.quantise(q, rung)
        entry = table[rung].get(cell)
        if entry is None:
            out.rows.append({"rung": rung, "cell": "empty"})
            continue
        kind, data = entry
        if kind == "shared":
            out.rows.append({"rung": rung, "cell": "shared",
                             "members": tuple(data)})
            continue
        i, rho2 = data
        a2 = CG._nsq(q, rows[i][2])
        b2 = CG._nsq(q, cell)
        holds = PG.exact_lt(a2, b2, rho2)
        out.rows.append({"rung": rung, "cell": "single", "carrier": i,
                         "guard": holds, "a2": a2, "b2": b2, "rho2": rho2})
        if out.unguarded is None:
            out.unguarded = (i, rung)
        if holds:
            out.status = "answered"
            out.carrier, out.rung, out.cell = i, rung, cell
            out.a2, out.b2, out.rho2 = a2, b2, rho2
            out.margin = margin_bound(rho2, b2)
            if delta2 is not None:
                out.origin_certified = PG.exact_lt(Fraction(delta2), b2, rho2)
            return out
    return out
