"""``glm_universal.reasoning.monster_stack`` -- 10 planes of Monster address.

What this module is
-------------------
The substrate stacks a carrier into ten binary digit planes, and each plane is
a 24-bit mask -- which is to say, an element of ``Lambda / 2 Lambda``, the
space the Monster's ``2A`` involutions are indexed by.  A carrier therefore
has a **ten-plane Monster address**, and this module builds it, types it, and
composes it.

Composition is where the shortcut used to live.  Two addresses can be combined
plane by plane in two quite different ways:

``xor``
    the group law of ``Lambda / 2 Lambda``.  Associative, cheap, and *not the
    algebra*: for a ``2A`` pair the class ``u XOR v`` is exactly the label of
    the third Sakuma axis ``a_ab`` and nothing else.
``sakuma``
    the genuine Griess product

    .. math:: a \\cdot b = \\tfrac{1}{8}\\,(a + b - a_{ab}),

    computed by :mod:`glm_universal.reasoning.product`.  Commutative,
    **non-associative**, and it keeps the two terms the XOR drops.

:func:`shortcut_loss_report` measures the difference exactly: the XOR answer
is the ``a_ab`` term alone, so it discards two of the product's three terms
and every one of its coefficients.  :func:`associativity_report` exhibits a
triple of planes where ``(a.b).c != a.(b.c)`` while the XOR composition of the
same triple is associative -- the precise sense in which the shortcut was
lying about the structure.

Typing a plane, and repairing it
--------------------------------
Only 98,280 of the 16,777,216 classes are of type 2, and only those carry a
``2A`` axis.  A plane whose class is not of type 2 has no product, full stop.
Two policies are offered and neither hides anything:

``strict``
    the plane has no axis; composition at that plane returns ``None`` with a
    reason.
``repair``
    the plane is snapped to the type-2 class or classes at least Hamming
    distance **in the Leech basis coordinates**, and the distance and the
    number of winners are recorded.  A tie is never broken: an ambiguous
    repair yields no axis, exactly as an undecodable Golay word yields no
    codeword.

The repair is basis-dependent -- Hamming distance on class labels is a
statement about the chosen ``Z``-basis of ``Lambda``, not about the lattice --
and every repaired address says so by carrying ``repair_distance`` and
``repair_multiplicity`` next to the raw class.

Everything is exact: ``int`` and :class:`~fractions.Fraction` only.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import digit_stack, leech2
from . import product

__all__ = [
    "DEPTH", "PlaneAddress", "MonsterAddress",
    "nearest_type2_classes", "nearest_two_a_partner", "geometric_tiebreak",
    "plane_address", "monster_address", "address_census",
    "compose_xor", "compose_sakuma", "PlaneProduct", "position_census",
    "associativity_report", "shortcut_loss_report",
    "monster_stack_report",
]

#: The digit-stack depth the substrate uses, and the depth of an address.
DEPTH = digit_stack.STACK_DEPTH


# ===========================================================================
# 1.  TYPING AND REPAIRING A PLANE
# ===========================================================================

@lru_cache(maxsize=4096)
def nearest_type2_classes(mask: int) -> Tuple[int, Tuple[int, ...]]:
    """``(distance, winners)``: the type-2 classes nearest ``mask``.

    Hamming distance on the 24-bit class label, i.e. in the coordinates of
    :data:`glm_universal.substrate.leech2.LEECH_BASIS`.  Exhaustive over the
    98,280 type-2 classes, so the distance is exact and ``winners`` is the
    complete tie -- never a first-found representative.
    """
    if not 0 <= int(mask) < leech2.N_CLASSES:
        raise ValueError("nearest_type2_classes: mask must be a 24-bit class")
    mask = int(mask)
    best = 25
    winners: List[int] = []
    for cls in leech2.type2_classes():
        d = bin(mask ^ cls).count("1")
        if d < best:
            best, winners = d, [cls]
        elif d == best:
            winners.append(cls)
    return best, tuple(sorted(winners))


@lru_cache(maxsize=4096)
def nearest_two_a_partner(mask: int, anchor: int
                          ) -> Tuple[int, Tuple[int, ...]]:
    """``(distance, winners)``: nearest type-2 classes in ``2A`` with ``anchor``.

    Like :func:`nearest_type2_classes`, but the candidates are restricted to
    the classes that actually compose with ``anchor`` under the Sakuma
    relation -- pair invariant 2.  Distances are scanned in increasing order
    and the whole tie at the winning distance is returned.

    This is a *pair-aware* repair.  It is a stronger assumption than the plain
    repair (it lets the partner choose the answer) and callers that use it are
    told so in the plane's note.
    """
    anchor = int(anchor)
    if not leech2.is_type2_class(anchor):
        raise ValueError("nearest_two_a_partner: anchor must be type 2")
    mask = int(mask)
    buckets: Dict[int, List[int]] = {}
    for cls in leech2.type2_classes():
        buckets.setdefault(bin(mask ^ cls).count("1"), []).append(cls)
    for distance in sorted(buckets):
        winners = sorted(cls for cls in buckets[distance]
                         if product.is_two_a_pair(anchor, cls))
        if winners:
            return distance, tuple(winners)
    raise AssertionError("no type-2 class is in the 2A position with the "
                         "anchor, which contradicts the pair census")


def geometric_tiebreak(mask: int,
                       candidates: Sequence[int]) -> Tuple[int, ...]:
    """Narrow a tie of classes by exact distance in the lattice itself.

    Hamming distance between class labels is a statement about the chosen
    ``Z``-basis.  The lattice has a metric of its own, so a tie can be broken
    where the geometry does distinguish: each candidate class ``c`` is scored
    by the least squared distance from ``representative(mask)`` to the two
    minimal vectors ``+-lambda`` of ``c``, and the candidates attaining the
    least score are returned.  A tie that survives this is real.
    """
    point = leech2.representative(int(mask))
    best: Optional[int] = None
    winners: List[int] = []
    for cls in candidates:
        plus, minus = leech2.axis_of_class(int(cls))
        score = min(leech2.norm2([a - b for a, b in zip(point, plus)]),
                    leech2.norm2([a - b for a, b in zip(point, minus)]))
        if best is None or score < best:
            best, winners = score, [int(cls)]
        elif score == best:
            winners.append(int(cls))
    return tuple(sorted(winners))


@dataclass(frozen=True)
class PlaneAddress:
    """One plane of a Monster address.

    Attributes
    ----------
    index
        Which digit plane this is, 0 the least significant.
    mask
        The raw 24-bit plane, read as a class of ``Lambda / 2 Lambda``.
    is_type2
        Whether that class carries a ``2A`` axis of its own.
    axis_class
        The class actually used for the algebra: ``mask`` itself when it is of
        type 2, the unique nearest type-2 class under the repair policy, or
        ``None`` when strict or when the repair is ambiguous.
    repair_distance
        Hamming distance from ``mask`` to the type-2 set (0 when ``is_type2``).
    repair_multiplicity
        How many type-2 classes attain that distance.
    note
        Why there is no axis, when there is none.
    """

    index: int
    mask: int
    is_type2: bool
    axis_class: Optional[int]
    repair_distance: int
    repair_multiplicity: int
    note: str = ""

    @property
    def has_axis(self) -> bool:
        """Whether an algebra element is available at this plane."""
        return self.axis_class is not None

    def axis(self) -> product.AlgebraVector:
        """The ``2A`` axis of this plane."""
        if self.axis_class is None:
            raise product.PositionError(
                f"plane {self.index}: no 2A axis ({self.note})")
        return product.axis(self.axis_class)

    def as_dict(self) -> Dict[str, object]:
        """A JSON-friendly view."""
        return {
            "index": self.index,
            "mask": self.mask,
            "is_type2": self.is_type2,
            "axis_class": self.axis_class,
            "repair_distance": self.repair_distance,
            "repair_multiplicity": self.repair_multiplicity,
            "note": self.note,
        }


def plane_address(index: int, mask: int, repair: bool = True) -> PlaneAddress:
    """Type one plane, repairing it to a ``2A`` axis if asked and possible."""
    mask = int(mask)
    if leech2.is_type2_class(mask):
        return PlaneAddress(index=index, mask=mask, is_type2=True,
                            axis_class=mask, repair_distance=0,
                            repair_multiplicity=1)
    if not repair:
        return PlaneAddress(
            index=index, mask=mask, is_type2=False, axis_class=None,
            repair_distance=-1, repair_multiplicity=0,
            note="strict policy: the class is not of type 2 and carries no "
                 "2A axis")
    distance, winners = nearest_type2_classes(mask)
    if len(winners) == 1:
        return PlaneAddress(index=index, mask=mask, is_type2=False,
                            axis_class=winners[0], repair_distance=distance,
                            repair_multiplicity=1,
                            note=f"repaired at Hamming distance {distance} "
                                 f"in the Leech basis")
    closest = geometric_tiebreak(mask, winners)
    if len(closest) == 1:
        return PlaneAddress(
            index=index, mask=mask, is_type2=False, axis_class=closest[0],
            repair_distance=distance, repair_multiplicity=1,
            note=f"repaired at Hamming distance {distance}; the tie of "
                 f"{len(winners)} classes was resolved by exact lattice "
                 f"distance between representatives")
    return PlaneAddress(
        index=index, mask=mask, is_type2=False, axis_class=None,
        repair_distance=distance, repair_multiplicity=len(closest),
        note=f"ambiguous repair: {len(winners)} type-2 classes at Hamming "
             f"distance {distance}, of which {len(closest)} are also "
             f"equidistant in the lattice; no tie is broken here")


@dataclass(frozen=True)
class MonsterAddress:
    """A carrier as ``depth`` planes of ``Lambda / 2 Lambda``."""

    planes: Tuple[PlaneAddress, ...]
    depth: int
    basis: str
    repair: bool

    def masks(self) -> Tuple[int, ...]:
        """The raw plane masks."""
        return tuple(p.mask for p in self.planes)

    def axis_classes(self) -> Tuple[Optional[int], ...]:
        """The class used for the algebra at each plane."""
        return tuple(p.axis_class for p in self.planes)

    def as_dict(self) -> Dict[str, object]:
        """A JSON-friendly view."""
        return {
            "depth": self.depth,
            "basis": self.basis,
            "repair": self.repair,
            "planes": [p.as_dict() for p in self.planes],
        }


def monster_address(carrier: Sequence, depth: int = DEPTH,
                    basis: str = "standard",
                    repair: bool = True) -> MonsterAddress:
    """The ten-plane Monster address of a carrier.

    ``basis="leech"`` expands the carrier in the Leech ``Z``-basis, where
    plane 0 *is* the class of the point in ``Lambda / 2 Lambda``; it requires
    an integral point of ``Lambda``.  ``basis="standard"`` expands the
    Euclidean coordinates and reads each plane as a class through the same
    coordinate identification, which is what lets an arbitrary rational
    carrier have an address at all.
    """
    stack = digit_stack.class_stack(carrier, depth=depth, basis=basis)
    planes = tuple(plane_address(k, m, repair=repair)
                   for k, m in enumerate(stack.planes))
    return MonsterAddress(planes=planes, depth=stack.depth, basis=basis,
                          repair=repair)


def address_census(address: MonsterAddress) -> Dict[str, object]:
    """How many planes are type 2, repaired, ambiguous or empty."""
    type2 = sum(1 for p in address.planes if p.is_type2)
    repaired = sum(1 for p in address.planes
                   if not p.is_type2 and p.has_axis)
    ambiguous = sum(1 for p in address.planes
                    if p.repair_multiplicity > 1)
    none = sum(1 for p in address.planes if not p.has_axis)
    distances = [p.repair_distance for p in address.planes
                 if p.repair_distance > 0]
    return {
        "depth": address.depth,
        "type2_planes": type2,
        "repaired_planes": repaired,
        "ambiguous_planes": ambiguous,
        "planes_without_axis": none,
        "repair_distances": distances,
        "max_repair_distance": max(distances) if distances else 0,
        "fully_addressable": none == 0,
    }


# ===========================================================================
# 2.  COMPOSITION: THE SHORTCUT AND THE ALGEBRA
# ===========================================================================

def compose_xor(left: MonsterAddress,
                right: MonsterAddress) -> Tuple[int, ...]:
    """The retired shortcut: plane-wise ``XOR`` of the raw classes.

    This is the group law of ``Lambda / 2 Lambda``.  It is associative, it
    never fails, and for a ``2A`` pair it returns precisely the label of the
    third Sakuma axis -- one term of a three-term product.
    """
    _check_same_depth(left, right, "compose_xor")
    return tuple(a ^ b for a, b in zip(left.masks(), right.masks()))


@dataclass(frozen=True)
class PlaneProduct:
    """The Sakuma product at one plane, or the reason there isn't one."""

    index: int
    position: Optional[str]
    value: Optional[product.AlgebraVector]
    xor_class: int
    note: str = ""

    @property
    def defined(self) -> bool:
        """Whether the algebra product exists at this plane."""
        return self.value is not None

    def as_dict(self) -> Dict[str, object]:
        """A JSON-friendly view."""
        return {
            "index": self.index,
            "position": self.position,
            "defined": self.defined,
            "xor_class": self.xor_class,
            "value": (None if self.value is None
                      else {str(k): str(v)
                            for k, v in sorted(self.value.coeffs.items())}),
            "note": self.note,
        }


def _check_same_depth(left: MonsterAddress, right: MonsterAddress,
                      where: str) -> None:
    if left.depth != right.depth:
        raise ValueError(f"{where}: addresses have different depths")


def compose_sakuma(left: MonsterAddress, right: MonsterAddress,
                   pair_repair: bool = False) -> Tuple[PlaneProduct, ...]:
    """Plane-wise Griess product of the two addresses.

    At each plane the two axis classes are multiplied by
    :func:`glm_universal.reasoning.product.axis_product`, which applies the
    idempotent law at ``1A``, the Sakuma relation at ``2A``, zero at ``2B``
    and refuses the unmodelled position rather than inventing a value.

    With ``pair_repair=True`` a plane whose two classes do not compose is
    retried once: the class that is *not* of type 2 is re-snapped to the
    nearest type-2 class that is in the ``2A`` position with the other one
    (:func:`nearest_two_a_partner`).  This buys coverage at the price of a
    stronger assumption, so every plane it touches says so in its note, and a
    tie is still never broken.
    """
    _check_same_depth(left, right, "compose_sakuma")
    out: List[PlaneProduct] = []
    for k, (p, q) in enumerate(zip(left.planes, right.planes)):
        xor_class = p.mask ^ q.mask
        u, v = p.axis_class, q.axis_class
        extra = ""
        if pair_repair and u is not None and v is not None:
            u, v, extra = _pair_repair(p, q, u, v)
        if u is None or v is None:
            missing = "left" if u is None else "right"
            out.append(PlaneProduct(
                index=k, position=None, value=None, xor_class=xor_class,
                note=f"no axis on the {missing} plane: "
                     f"{(p if u is None else q).note}"))
            continue
        position = product.position_name(u, v)
        try:
            value = product.axis_product(u, v)
        except product.PositionError as exc:
            out.append(PlaneProduct(index=k, position=position, value=None,
                                    xor_class=xor_class,
                                    note=str(exc) + extra))
            continue
        out.append(PlaneProduct(index=k, position=position, value=value,
                                xor_class=xor_class, note=extra.strip()))
    return tuple(out)


def _pair_repair(p: PlaneAddress, q: PlaneAddress, u: int, v: int
                 ) -> Tuple[Optional[int], Optional[int], str]:
    """Re-snap the non-type-2 side of a plane against the type-2 side."""
    if product.pair_invariant_classes(u, v) in (0, 2, 4):
        return u, v, ""
    # Invariant 1: the position the algebra does not model.  A side that was
    # only ever a repair may be re-snapped; a side that is genuinely of type 2
    # is data and is left alone.
    if not q.is_type2:
        distance, winners = nearest_two_a_partner(q.mask, u)
        if len(winners) > 1:
            winners = geometric_tiebreak(q.mask, winners)
        if len(winners) == 1:
            return u, winners[0], (
                f"  [pair repair: the right plane was re-snapped to a 2A "
                f"partner of the left at Hamming distance {distance}]")
    if not p.is_type2:
        distance, winners = nearest_two_a_partner(p.mask, v)
        if len(winners) > 1:
            winners = geometric_tiebreak(p.mask, winners)
        if len(winners) == 1:
            return winners[0], v, (
                f"  [pair repair: the left plane was re-snapped to a 2A "
                f"partner of the right at Hamming distance {distance}]")
    return u, v, ""


def position_census(planes: Sequence[PlaneProduct]) -> Dict[str, object]:
    """How the planes of a composition are distributed over the positions."""
    counts: Dict[str, int] = {}
    for pp in planes:
        key = pp.position or "no axis"
        counts[key] = counts.get(key, 0) + 1
    defined = sum(1 for pp in planes if pp.defined)
    return {
        "planes": len(planes),
        "by_position": dict(sorted(counts.items())),
        "defined": defined,
        "undefined": len(planes) - defined,
    }


# ===========================================================================
# 3.  WHAT THE SHORTCUT COST
# ===========================================================================

def _two_a_triple() -> Tuple[int, int, int]:
    """A deterministic triple of type-2 classes, pairwise in ``2A`` position.

    Searched for in sorted class order, so the answer is a function of the
    substrate's own table and not of iteration luck.
    """
    classes = sorted(leech2.type2_classes())[:400]
    for i, u in enumerate(classes):
        for v in classes[i + 1:]:
            if not product.is_two_a_pair(u, v):
                continue
            w = u ^ v
            if (product.is_two_a_pair(u, w)
                    and product.is_two_a_pair(v, w)):
                return u, v, w
    raise AssertionError("no 2A triple found among the first 400 classes")


def shortcut_loss_report() -> Dict[str, object]:
    """The XOR shortcut against the Sakuma product, term by term.

    For a ``2A`` pair ``(u, v)`` the product is ``(1/8)(a_u + a_v - a_{u^v})``.
    The shortcut keeps the label ``u ^ v`` and drops everything else, so what
    it returns is one basis axis where the algebra has three, with the wrong
    sign and no coefficient.  Both are compared under the Griess form.
    """
    u, v, _ = _two_a_triple()
    prod = product.axis_product(u, v)
    xor_class = u ^ v
    shortcut = product.axis(xor_class)
    difference = prod - shortcut
    return {
        "u": u,
        "v": v,
        "position": product.position_name(u, v),
        "xor_class": xor_class,
        "sakuma_terms": {str(k): str(c)
                         for k, c in sorted(prod.coeffs.items())},
        "sakuma_term_count": len(prod.coeffs),
        "shortcut_term_count": 1,
        "terms_discarded_by_xor": len(prod.coeffs) - 1,
        "coefficient_on_xor_term": str(prod.coeffs.get(xor_class,
                                                       Fraction(0))),
        "sakuma_norm2": str(product.griess_form(prod, prod)),
        "shortcut_norm2": str(product.griess_form(shortcut, shortcut)),
        "difference_norm2": str(product.griess_form(difference, difference)),
        "xor_is_the_third_axis_label": (
            product.sakuma_third_axis(u, v) == xor_class),
    }


def associativity_report() -> Dict[str, object]:
    """``(a.b).c`` against ``a.(b.c)``, and the same triple under XOR.

    The XOR composition is a group law and therefore associative; the Griess
    product is not.  Both statements are computed on one triple of type-2
    classes drawn deterministically from the substrate's table.
    """
    u, v, w = _two_a_triple()
    a, b, c = product.axis(u), product.axis(v), product.axis(w)
    left = product.algebra_product(product.algebra_product(a, b), c)
    right = product.algebra_product(a, product.algebra_product(b, c))
    difference = left - right
    xor_left = (u ^ v) ^ w
    xor_right = u ^ (v ^ w)
    return {
        "classes": [u, v, w],
        "positions": {
            "uv": product.position_name(u, v),
            "vw": product.position_name(v, w),
            "uw": product.position_name(u, w),
        },
        "left_terms": {str(k): str(x)
                       for k, x in sorted(left.coeffs.items())},
        "right_terms": {str(k): str(x)
                        for k, x in sorted(right.coeffs.items())},
        "associative": left == right,
        "difference_norm2": str(product.griess_form(difference, difference)),
        "xor_associative": xor_left == xor_right,
        "commutative": (product.algebra_product(a, b)
                        == product.algebra_product(b, a)),
        "reading": ("the shortcut is associative and the algebra is not, so "
                    "any pipeline that composed addresses by XOR was working "
                    "in a quotient where the Monster's product does not "
                    "live"),
    }


# ===========================================================================
# 4.  ONE REPORT
# ===========================================================================

def _default_carriers() -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Two deterministic Leech points, used when no carrier is supplied."""
    minimal = []
    for v in leech2.minimal_vectors():
        minimal.append(v)
        if len(minimal) >= 2:
            break
    return minimal[0], minimal[1]


def monster_stack_report(left: Optional[Sequence] = None,
                         right: Optional[Sequence] = None,
                         basis: str = "leech") -> Dict[str, object]:
    """The whole wiring, recomputed on two carriers."""
    if left is None or right is None:
        a, b = _default_carriers()
        left = list(left if left is not None else a)
        right = list(right if right is not None else b)
    addr_l = monster_address(left, basis=basis)
    addr_r = monster_address(right, basis=basis)
    sakuma = compose_sakuma(addr_l, addr_r)
    paired = compose_sakuma(addr_l, addr_r, pair_repair=True)
    xor = compose_xor(addr_l, addr_r)
    defined = [p for p in sakuma if p.defined]
    return {
        "depth": addr_l.depth,
        "basis": basis,
        "left_address": addr_l.as_dict(),
        "right_address": addr_r.as_dict(),
        "left_census": address_census(addr_l),
        "right_census": address_census(addr_r),
        "sakuma_planes": [p.as_dict() for p in sakuma],
        "xor_planes": list(xor),
        "planes_with_product": len(defined),
        "positions": [p.position for p in sakuma],
        "position_census": position_census(sakuma),
        "position_census_pair_repaired": position_census(paired),
        "shortcut_loss": shortcut_loss_report(),
        "associativity": associativity_report(),
    }
