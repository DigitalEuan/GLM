"""Physics carriers: the 720-concept dimensional register in 24 dimensions.

The register
------------
720 named physical quantities across 26 domains, ingested from
``workflow/GLM/glm_lean/glm2/glm2_library.py`` and frozen into
``_data/physics_660.json`` as exact rationals.  Each concept carries a
*meaning*: ten rational exponents on the EXT10 axes

    ``(L, M, T, I, H, N, J, A, S, B)``

-- length, mass, time, current, thermodynamic temperature, amount, luminous
intensity, plane angle, solid angle, information -- plus a decimal ``scale``
(the quantity is ``10^scale`` times the SI coherent unit), a tensor ``rank``,
the ``P``/``T``/``C`` gradings, a nominal ``kind`` and a ``domain``.

SI7 and EXT10
-------------
SI7 is the first seven axes: the seven SI base dimensions.  EXT10 adds ``A``
(plane angle), ``S`` (solid angle) and ``B`` (information), which SI treats as
dimensionless.  The projection ``EXT10 -> SI7`` is therefore **lossy exactly
when a concept has a nonzero A, S or B exponent** -- and that is not a defect
of the encoding but a real statement about SI: it is why torque and energy
share a dimension in SI7 and separate in EXT10.  :func:`si7_projection_lossy`
decides this per concept, and :func:`basis_collision_report` counts the
dimensional collisions each basis induces over the whole register.

The 24-coordinate layout
------------------------
Ten EXT10 exponents, seven SI7 exponents, seven meaning scalars.  ``10 + 7 + 7``
is exactly 24, with no padding and no spare coordinate::

    0..9    EXT10 exponents  L M T I H N J A S B     (exact, may be fractional)
    10..16  SI7 projection   L M T I H N J           (redundant by construction)
    17      scale            decimal exponent
    18      rank             tensor rank
    19      p                space-inversion parity anomaly
    20      t                time-reversal anomaly
    21      c                charge-conjugation anomaly
    22      kind             nominal-kind index
    23      domain           domain index

Coordinates 10..16 duplicate 0..6.  That redundancy is deliberate: it puts both
bases in one carrier so a reasoner can act on either without re-deriving one
from the other, and it gives the round-trip test a built-in consistency check
(a decoder that read the wrong slice would disagree with itself).  Decoding
reads 0..9 and 17..23; 10..16 are then re-derived and compared.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .base import Codec, DataObject, Scalar, as_exact

__all__ = [
    "AXES_EXT10", "AXES_SI7", "AXIS_LONG", "PHYSICS_LAYOUT",
    "Quantity", "PhysicsCodec",
    "load_physics_register", "physics_objects", "quantity_by_name",
    "si7_projection_lossy", "basis_collision_report", "dimension_string",
]

_DATA = Path(__file__).resolve().parent / "_data" / "physics_660.json"

#: The ten EXT10 axes, in register order.
AXES_EXT10: Tuple[str, ...] = ("L", "M", "T", "I", "H", "N", "J",
                               "A", "S", "B")

#: The seven SI base dimensions: the first seven EXT10 axes.
AXES_SI7: Tuple[str, ...] = AXES_EXT10[:7]

AXIS_LONG: Dict[str, str] = {
    "L": "length", "M": "mass", "T": "time", "I": "electric current",
    "H": "thermodynamic temperature", "N": "amount of substance",
    "J": "luminous intensity", "A": "plane angle", "S": "solid angle",
    "B": "information",
}

#: Names of the 24 carrier coordinates, in order.
PHYSICS_LAYOUT: Tuple[str, ...] = (
    tuple(f"ext10.{a}" for a in AXES_EXT10)
    + tuple(f"si7.{a}" for a in AXES_SI7)
    + ("scale", "rank", "p", "t", "c", "kind", "domain")
)
assert len(PHYSICS_LAYOUT) == 24


@dataclass(frozen=True)
class Quantity:
    """One physical quantity of the register, with exact rational exponents."""

    name: str
    symbol: str
    unit: str
    gloss: str
    exps_ext10: Tuple[Fraction, ...]
    scale: Fraction
    rank: int
    p: int
    t: int
    c: int
    kind: int
    domain_index: int
    domain_name: str

    def __post_init__(self) -> None:
        if len(self.exps_ext10) != 10:
            raise ValueError(f"{self.name}: EXT10 needs ten exponents")

    @property
    def exps_si7(self) -> Tuple[Fraction, ...]:
        """The SI7 projection: the first seven exponents."""
        return self.exps_ext10[:7]

    @property
    def angular_part(self) -> Tuple[Fraction, ...]:
        """The three exponents SI7 discards: ``(A, S, B)``."""
        return self.exps_ext10[7:]

    def dimension_string(self, basis: str = "EXT10") -> str:
        """Human-readable dimension, e.g. ``L^2 M T^-2``."""
        return dimension_string(self.exps_ext10, basis)

    def is_dimensionless(self, basis: str = "EXT10") -> bool:
        """Whether every exponent in the given basis vanishes."""
        exps = self.exps_ext10 if basis == "EXT10" else self.exps_si7
        return all(e == 0 for e in exps)


def dimension_string(exps: Sequence[Fraction], basis: str = "EXT10") -> str:
    """Render an exponent vector as ``L^2 M T^-2``; ``"1"`` when trivial."""
    axes = AXES_EXT10 if basis == "EXT10" else AXES_SI7
    exps = tuple(exps)[:len(axes)]
    parts: List[str] = []
    for axis, e in zip(axes, exps):
        if e == 0:
            continue
        if e == 1:
            parts.append(axis)
        elif e.denominator == 1:
            parts.append(f"{axis}^{e.numerator}")
        else:
            parts.append(f"{axis}^({e.numerator}/{e.denominator})")
    return " ".join(parts) if parts else "1"


def si7_projection_lossy(quantity: Quantity) -> bool:
    """Whether ``EXT10 -> SI7`` discards information for this quantity.

    True exactly when the plane-angle, solid-angle or information exponent is
    nonzero.  Torque (``A^-1``) is lossy; energy is not; the two therefore
    collide in SI7 and separate in EXT10.
    """
    return any(e != 0 for e in quantity.angular_part)


# ===========================================================================
# REGISTER
# ===========================================================================

@lru_cache(maxsize=1)
def load_physics_register() -> Tuple[Quantity, ...]:
    """The 720 quantities, parsed once from the frozen snapshot."""
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    if raw["axes_ext10"] != list(AXES_EXT10):
        raise AssertionError("physics snapshot axis order has drifted")
    out: List[Quantity] = []
    for rec in raw["concepts"]:
        out.append(Quantity(
            name=rec["name"], symbol=rec["symbol"], unit=rec["unit"],
            gloss=rec["gloss"],
            exps_ext10=tuple(Fraction(e) for e in rec["exps_ext10"]),
            scale=Fraction(rec["scale"]), rank=rec["rank"], p=rec["p"],
            t=rec["t"], c=rec["c"], kind=rec["kind_index"],
            domain_index=rec["domain_index"],
            domain_name=rec["domain_name"],
        ))
    return tuple(out)


@lru_cache(maxsize=1)
def _by_name() -> Dict[str, Quantity]:
    return {q.name: q for q in load_physics_register()}


def quantity_by_name(name: str) -> Quantity:
    """Look a quantity up by its register name."""
    try:
        return _by_name()[name]
    except KeyError:
        raise KeyError(f"physics: no quantity named {name!r}") from None


# ===========================================================================
# CODEC
# ===========================================================================

class PhysicsCodec(Codec):
    """Embed a :class:`Quantity` in ``Q^24`` and read it back exactly."""

    domain = "physics"
    layout = PHYSICS_LAYOUT

    def encode(self, source: Quantity) -> DataObject:
        """The 24-coordinate carrier of a physical quantity."""
        carrier: List[Scalar] = []
        carrier.extend(source.exps_ext10)          # 0..9
        carrier.extend(source.exps_si7)            # 10..16
        carrier.append(source.scale)               # 17
        carrier.append(source.rank)                # 18
        carrier.append(source.p)                   # 19
        carrier.append(source.t)                   # 20
        carrier.append(source.c)                   # 21
        carrier.append(source.kind)                # 22
        carrier.append(source.domain_index)        # 23
        return DataObject(
            name=source.name, domain=self.domain, carrier=carrier,
            attributes={
                "symbol": source.symbol, "unit": source.unit,
                "gloss": source.gloss, "domain_name": source.domain_name,
                "dimension_ext10": source.dimension_string("EXT10"),
                "dimension_si7": source.dimension_string("SI7"),
                "si7_projection_lossy": si7_projection_lossy(source),
            },
            layout=PHYSICS_LAYOUT,
            provenance={
                "source": "glm2_library.CONCEPTS via _data/physics_660.json",
                "basis": "EXT10 with redundant SI7 projection",
            },
        )

    def decode(self, obj: DataObject) -> Quantity:
        """Recover the quantity.  Raises if the redundant SI7 slice disagrees."""
        c = obj.carrier
        exps = tuple(as_exact(x) for x in c[0:10])
        si7 = tuple(as_exact(x) for x in c[10:17])
        if si7 != exps[:7]:
            raise ValueError(
                f"physics.decode: carrier is internally inconsistent for "
                f"{obj.name!r} -- the SI7 slice does not match the first "
                f"seven EXT10 exponents")
        attrs = obj.attributes
        return Quantity(
            name=obj.name, symbol=attrs["symbol"], unit=attrs["unit"],
            gloss=attrs["gloss"], exps_ext10=exps, scale=as_exact(c[17]),
            rank=int(c[18]), p=int(c[19]), t=int(c[20]), c=int(c[21]),
            kind=int(c[22]), domain_index=int(c[23]),
            domain_name=attrs["domain_name"],
        )


def physics_objects() -> Tuple[DataObject, ...]:
    """Every one of the 660 quantities as an encoded :class:`DataObject`."""
    codec = PhysicsCodec()
    return tuple(codec.encode(q) for q in load_physics_register())


# ===========================================================================
# BASIS DIAGNOSTICS
# ===========================================================================

def basis_collision_report() -> Dict[str, object]:
    """How many quantities each basis fails to tell apart.

    A *collision* is a pair of distinct register names sharing an exponent
    vector in the given basis.  EXT10 resolves strictly more pairs than SI7,
    and the difference is exactly the angular/informational content SI7
    discards.  Both counts are computed from the register, not quoted.
    """
    register = load_physics_register()
    out: Dict[str, object] = {"concepts": len(register)}
    for basis, key in (("SI7", lambda q: q.exps_si7),
                       ("EXT10", lambda q: q.exps_ext10)):
        buckets: Dict[Tuple[Fraction, ...], List[str]] = {}
        for q in register:
            buckets.setdefault(key(q), []).append(q.name)
        colliding = {dimension_string(k, basis): sorted(v)
                     for k, v in buckets.items() if len(v) > 1}
        pairs = sum(len(v) * (len(v) - 1) // 2 for v in buckets.values())
        out[basis] = {
            "distinct_dimension_vectors": len(buckets),
            "colliding_dimension_classes": len(colliding),
            "concepts_in_a_collision": sum(len(v) for v in colliding.values()),
            "colliding_pairs": pairs,
            "largest_collision_class": max(
                (len(v) for v in buckets.values()), default=0),
        }
    lossy = [q.name for q in register if si7_projection_lossy(q)]
    out["si7_projection_lossy_count"] = len(lossy)
    out["ext10_resolves_extra_pairs"] = (
        out["SI7"]["colliding_pairs"] - out["EXT10"]["colliding_pairs"])
    return out
