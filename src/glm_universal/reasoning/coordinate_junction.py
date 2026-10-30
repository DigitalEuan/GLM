"""``glm_universal.reasoning.coordinate_junction`` -- register junctions: the
address read over carriers that share coordinates (Phase 144).

``studies/COORDINATE_JUNCTION_STUDY.md``.  Phase 143's `locate` read refuses
every carrier whose exact coordinates another carrier also has: its cell is
shared at every rung and its placement radius is 0.  Phase 66's junction rule
for formula wheels (:mod:`glm_universal.engineering.union`) says what to do
with a name two wheels share: it is one quantity only where a declared
junction identifies it, and is split otherwise.  This module applies the same
discipline to coordinates.

* A **junction** is the set of carriers at one exact coordinate vector.  No
  function of the coordinates names each member
  (``GLM.CoordinateJunction.no_read_separates``), so the junction is the
  finest answer any read can certify.
* The **junction table** adds, for every shared cell of the stored address
  table whose members form one junction, the junction radius
  ``rho_p^2 = min over carriers k off the junction's coordinates of
  |c_k - p|^2``.  It is stored beside five digests and used only while all
  hold.
* The **junction read** is Phase 143's read with one change: at such a cell
  the placement guard is decided against the junction radius, and the answer
  is the junction.  ``RequestProject/GLM/CoordinateJunction.lean`` proves the
  answer is strictly nearer than every carrier off its coordinates
  (``jread_junction_nearest``), is exactly the scan's least-distance set
  (``jread_scan``), is order-independent (``jread_order_independent``),
  carries a margin within which nothing else lies (``jread_unique_in_ball``)
  and contains the origin when a bounded move is inside the margin
  (``jread_origin``).  Where coordinates are distinct nothing changes
  (``jsound_of_sound``, ``jread_strict_nearest_of_injective``).
* The **declarations** (:data:`DECLARATIONS`) say, per junction, whether its
  members are one object filed twice (``identity``) or distinct objects the
  encoding does not separate (``distinct``), with the reason and the relation
  between them.  A junction with no declaration is read as distinct -- the
  default Phase 66 gives a shared name no junction identifies.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout.  No float, no
randomness.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import address_read as AR
from . import address_table as AT
from . import cell_guard as CG
from . import norm256_hex as NH
from . import placement_guard as PG

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "Declaration", "DECLARATIONS",
    "junctions", "declaration_for", "declarations_digest", "check_declarations",
    "build", "DATA_PATH", "module_digest", "measure", "write_measurements",
    "measurements", "state", "load", "describe", "JRead", "read_point",
    "census",
]

LEAN_FILE = "RequestProject/GLM/CoordinateJunction.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "no_read_separates", "jsound_of_sound", "JTableSound.of_tableSound",
    "entry_junction_in_ball", "jread_junction_nearest", "jread_members_tie",
    "jread_scan", "jread_order_independent", "jread_unique_in_ball",
    "jread_origin", "jread_strict_nearest_of_injective")

Point = Tuple[int, ...]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE DECLARATIONS (the study's section 2.3, argued before any read)
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Declaration:
    """One declared junction: its members (``register:name``), whether they
    are one object (``identity``) or not (``distinct``), what the coordinates
    do not carry, and how the members are related."""

    members: Tuple[str, ...]
    kind: str
    why: str
    relation: str


_FILLED = tuple(f"mathematics:filled_{shape}" for shape in (
    "1x24", "2x12", "3x8", "4x6", "6x4", "8x3", "12x2", "24x1"))

DECLARATIONS: Tuple[Declaration, ...] = (
    Declaration(
        ("physics:absorptance", "physics:albedo"), "distinct",
        "both are dimensionless ratios of the same domain code; absorptance "
        "is the absorbed fraction of incident radiation, albedo the "
        "reflected fraction",
        "for an opaque surface, absorptance = 1 - albedo (a conversion, not "
        "an identity)"),
    Declaration(
        ("physics:acoustic_absorption", "physics:acoustic_intensity_level",
         "physics:acoustic_power_level"), "distinct",
        "the encoding holds the dimension (all three are dimensionless) and "
        "the domain; they are a coefficient and two levels in decibels "
        "against different references (1 pW/m^2, 1 pW)",
        "power level = intensity level + 10 log10(S / 1 m^2) over a "
        "surface S"),
    Declaration(
        _FILLED, "distinct",
        "the carrier holds the 24 entries in row order; the shape (rows, "
        "cols) is not a coordinate",
        "a reshape: the same entries, different matrices"),
    Declaration(
        ("mathematics:golay_codeword_0", "mathematics:hexacode_word_0"),
        "distinct",
        "the all-zero vector in both; the field (2 against 4) and the "
        "length (24 against 6 symbols) are not coordinates",
        "the zero word of each code"),
)


def _coords(rows, i: int) -> Tuple[Fraction, ...]:
    return tuple(Fraction(x) for x in rows[i][2])


def junctions(rows) -> List[Tuple[int, ...]]:
    """The junctions of two or more members, each in carrier order, ordered
    by their first member."""
    groups: Dict[Tuple[Fraction, ...], List[int]] = {}
    for i in range(len(rows)):
        groups.setdefault(_coords(rows, i), []).append(i)
    return sorted(tuple(g) for g in groups.values() if len(g) > 1)


def _labels(rows, members: Sequence[int]) -> Tuple[str, ...]:
    return tuple(AR.carrier_label(rows, i) for i in members)


def declaration_for(labels: Sequence[str],
                    declarations: Sequence[Declaration] = DECLARATIONS
                    ) -> Optional[Declaration]:
    """The declaration whose members are exactly ``labels``, if any."""
    wanted = frozenset(labels)
    for dec in declarations:
        if frozenset(dec.members) == wanted:
            return dec
    return None


def declarations_digest(declarations: Sequence[Declaration] = DECLARATIONS
                        ) -> str:
    """SHA-256 over the declarations."""
    canon = [[list(d.members), d.kind, d.why, d.relation]
             for d in declarations]
    return integrity.sha256_hex(json.dumps(canon, separators=(",", ":"))
                                .encode("utf-8"))


def check_declarations(rows, declarations: Sequence[Declaration]
                       = DECLARATIONS) -> List[str]:
    """What is wrong with the declarations against the live carriers: a kind
    other than ``identity``/``distinct``, or members that are not exactly one
    junction.  Empty when they hold."""
    live = {frozenset(_labels(rows, g)) for g in junctions(rows)}
    problems = []
    for dec in declarations:
        if dec.kind not in ("identity", "distinct"):
            problems.append(f"{dec.members[0]}: kind {dec.kind!r}")
        if frozenset(dec.members) not in live:
            problems.append(f"{', '.join(dec.members)}: not a junction of "
                            f"the live carriers")
    return problems


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE JUNCTION TABLE AND ITS DIGESTS
# ═════════════════════════════════════════════════════════════════════════

def _q(value: Fraction) -> str:
    value = Fraction(value)
    return f"{value.numerator}/{value.denominator}"


def _content_digest(stored: Dict[str, object]) -> str:
    body = {key: stored.get(key) for key in ("ladder", "rungs")}
    return integrity.sha256_hex(json.dumps(body, sort_keys=True,
                                           separators=(",", ":"))
                                .encode("utf-8"))


def build(rows=None, address: Optional[Dict[str, object]] = None,
          declarations: Sequence[Declaration] = DECLARATIONS
          ) -> Dict[str, object]:
    """The junction table, computed from the carriers and the stored address
    table's shared cells."""
    rows = tuple(rows) if rows is not None else AT.carriers()
    address = address if address is not None else AT.measurements()
    rungs: Dict[str, List[list]] = {}
    coords = [_coords(rows, i) for i in range(len(rows))]
    for rung in AT.LADDER:
        out = []
        for point, members in address["rungs"][rung]["shared"]:
            first = coords[members[0]]
            if any(coords[m] != first for m in members):
                continue
            rho2 = min(CG._nsq(coords[k], point) for k in range(len(rows))
                       if coords[k] != first)
            out.append([list(point), list(members), _q(rho2)])
        rungs[rung] = sorted(out)
    table: Dict[str, object] = {"ladder": list(AT.LADDER), "rungs": rungs}
    table["carriers_digest"] = AT.carriers_digest(rows)
    table["declarations_digest"] = declarations_digest(declarations)
    table["address_digest"] = address.get("content_digest")
    table["content_digest"] = _content_digest(table)
    return table


DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "junction_table.json")

_SOURCES: Tuple[str, ...] = ("reasoning/coordinate_junction.py",) + tuple(
    AT._SOURCES)


def module_digest() -> str:
    """One digest over the sources the junction table depends on."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    return integrity.tree_digest([root / name for name in names], root)


def measure() -> Dict[str, object]:
    """The junction table, recomputed, with its source digest."""
    table = build()
    table["source_digest"] = module_digest()
    return table


def write_measurements(path: Optional[Path] = None) -> Path:
    """Compute the junction table and store it beside its digests."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(measure(), indent=0, sort_keys=True)
                      + "\n", encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False, path: Optional[Path] = None
                 ) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if path is None and _cache is not None and not refresh:
        return _cache
    target = Path(path) if path is not None else DATA_PATH
    if not target.exists():
        return None
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except ValueError:
        return None
    loaded = loaded if isinstance(loaded, dict) else None
    if path is None:
        _cache = loaded
    return loaded


def state(stored: Optional[Dict[str, object]] = None, rows=None,
          address: Optional[Dict[str, object]] = None,
          declarations: Sequence[Declaration] = DECLARATIONS
          ) -> Dict[str, object]:
    """Which digests hold.  ``failed`` names the ones that do not:
    ``source``, ``carriers``, ``declarations``, ``address``, ``content``,
    ``ladder``, or ``absent``."""
    stored = stored if stored is not None else measurements()
    if stored is None:
        return {"present": False, "fresh": False, "failed": ("absent",),
                "verdict": "absent"}
    rows = rows if rows is not None else AT.carriers()
    address = address if address is not None else AT.measurements()
    failed: List[str] = []
    if stored.get("source_digest") != module_digest():
        failed.append("source")
    if stored.get("carriers_digest") != AT.carriers_digest(rows):
        failed.append("carriers")
    if (stored.get("declarations_digest") != declarations_digest(declarations)
            or check_declarations(rows, declarations)):
        failed.append("declarations")
    if (address is None
            or stored.get("address_digest") != address.get("content_digest")
            or not AT.state(address, rows)["fresh"]):
        failed.append("address")
    try:
        same = stored.get("content_digest") == _content_digest(stored)
    except (TypeError, ValueError):
        same = False
    if not same:
        failed.append("content")
    if list(stored.get("ladder") or ()) != list(AT.LADDER):
        failed.append("ladder")
    return {"present": True, "fresh": not failed, "failed": tuple(failed),
            "verdict": "fresh" if not failed else "stale"}


def load(stored: Optional[Dict[str, object]] = None, rows=None,
         address: Optional[Dict[str, object]] = None,
         declarations: Sequence[Declaration] = DECLARATIONS
         ) -> Tuple[Optional[Dict[str, Dict[Point, Tuple[Tuple[int, ...],
                                                         Fraction]]]],
                    Dict[str, object]]:
    """``(table, state)``: the parsed junction table, or ``None`` when any
    digest fails (the read then refuses junction cells as Phase 143 does)."""
    stored = stored if stored is not None else measurements()
    st = state(stored, rows, address, declarations)
    if not st["fresh"]:
        return None, st
    try:
        parsed = {rung: {tuple(point): (tuple(int(m) for m in members),
                                        Fraction(rho2))
                         for point, members, rho2 in entries}
                  for rung, entries in dict(stored["rungs"]).items()}
    except (KeyError, TypeError, ValueError):
        return None, dict(st, fresh=False, failed=("content",),
                          verdict="stale")
    return parsed, st


def describe(labels: Sequence[str],
             declarations: Sequence[Declaration] = DECLARATIONS) -> str:
    """What the answer says about a junction's members: its declaration, or
    *undeclared, read as distinct* (Phase 66's default for a shared name no
    junction identifies)."""
    dec = declaration_for(labels, declarations)
    if dec is None:
        return ("this junction is undeclared, so its members are read as "
                "distinct carriers, not as one object")
    if dec.kind == "identity":
        return (f"declared an identity: one object filed under "
                f"{len(labels)} names ({dec.why})")
    return (f"declared distinct: {dec.why}; how they are related: "
            f"{dec.relation}")


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE JUNCTION READ
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class JRead(AR.Read):
    """One junction read: Phase 143's read, with the answered junction."""

    members: Tuple[int, ...] = ()
    junction_cells: List[str] = field(default_factory=list)


def read_point(point: Sequence, table, jtable, rows=None,
               order: Sequence[str] = AR.ORDER,
               delta2: Optional[Fraction] = None) -> JRead:
    """Walk ``order``; answer at the first rung whose guard holds -- at a
    single-carrier cell exactly as :func:`address_read.read_point`, at a
    junction cell with the junction radius.  ``jtable`` ``None`` reads as
    Phase 143."""
    rows = rows if rows is not None else AT.carriers()
    q = tuple(Fraction(x) for x in point)
    out = JRead(point=q, status="refused")
    for rung in order:
        cell = NH.quantise(q, rung)
        entry = table[rung].get(cell)
        if entry is None:
            out.rows.append({"rung": rung, "cell": "empty"})
            continue
        kind, data = entry
        if kind == "shared":
            junction = (jtable or {}).get(rung, {}).get(cell)
            if junction is None:
                out.rows.append({"rung": rung, "cell": "shared",
                                 "members": tuple(data)})
                continue
            members, rho2 = junction
            i = members[0]
        else:
            i, rho2 = data
            members = (i,)
        a2 = CG._nsq(q, rows[i][2])
        b2 = CG._nsq(q, cell)
        holds = PG.exact_lt(a2, b2, rho2)
        out.rows.append({"rung": rung,
                         "cell": "single" if len(members) == 1 else "junction",
                         "carrier": i, "members": tuple(members),
                         "guard": holds, "a2": a2, "b2": b2, "rho2": rho2})
        if out.unguarded is None and len(members) == 1:
            out.unguarded = (i, rung)
        if holds:
            out.status = "answered"
            out.carrier, out.rung, out.cell = i, rung, cell
            out.members = tuple(members)
            out.a2, out.b2, out.rho2 = a2, b2, rho2
            out.margin = AR.margin_bound(rho2, b2)
            if delta2 is not None:
                out.origin_certified = PG.exact_lt(Fraction(delta2), b2, rho2)
            return out
    return out


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE CENSUS OVER THE SIX REGISTERS IN FULL
# ═════════════════════════════════════════════════════════════════════════

#: Attributes that name or describe a row rather than say what it is.
_DESCRIPTIVE = ("symbol", "gloss")


def census() -> Dict[str, object]:
    """The junctions of the six registers in full: how many, whether any
    crosses a register, and which attributes would separate their members
    (the attributes the coordinates do not carry)."""
    from . import escalation as ESC
    groups: Dict[Tuple[Fraction, ...], List[Tuple[str, object]]] = {}
    total = 0
    for register in ESC.REGISTERS:
        for obj in ESC._register_loader(register)():
            total += 1
            key = tuple(Fraction(x) for x in obj.carrier)
            groups.setdefault(key, []).append((register, obj))
    found = [g for g in groups.values() if len(g) > 1]
    separating: Counter = Counter()
    descriptive_only = []
    per_register: Counter = Counter()
    for g in found:
        per_register[g[0][0]] += 1
        attrs = [dict(getattr(obj, "attributes", {}) or {}) for _r, obj in g]
        keys = sorted(set().union(*attrs))
        for key in keys:
            values = [repr(a.get(key)) for a in attrs]
            if len(set(values)) == len(values):
                separating[key] += 1
        substantive = [k for k in keys if k not in _DESCRIPTIVE]
        if all(len({repr(a.get(k)) for a in attrs}) == 1
               for k in substantive):
            descriptive_only.append(tuple(f"{r}:{o.name}" for r, o in g))
    cross = [g for g in found if len({r for r, _o in g}) > 1]
    return {
        "carriers": total,
        "distinct": len(groups),
        "junctions": len(found),
        "in_junctions": sum(len(g) for g in found),
        "cross_register": len(cross),
        "per_register": dict(sorted(per_register.items())),
        "largest": max((len(g) for g in found), default=0),
        "separated_by": dict(sorted(separating.items(),
                                    key=lambda kv: (-kv[1], kv[0]))),
        "descriptive_only": len(descriptive_only),
        "descriptive_only_examples": [list(g) for g in descriptive_only[:8]],
    }
