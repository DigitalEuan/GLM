"""The typed carrier layer: arbitrary data as exact points of the substrate.

A :class:`DataObject` is a named, domain-tagged 24-vector over ``Q`` together
with the provenance of how it got there.  It owns no algebra of its own: every
geometric question is delegated to :mod:`glm_universal.substrate`.  What this
module adds is *typing*, *dynamic stack derivation*, and a **losslessness
contract** that is asserted rather than asserted-to.

Two round trips, and why both are needed
----------------------------------------
``substrate`` round trip
    ``class_stack_rebuild(class_stack(v)) == v``.  A property of the digit
    stack, proved by Proposition D1 in
    :mod:`glm_universal.substrate.digit_stack` and re-checked here for every
    object.  It says the *encoding* loses nothing.
semantic round trip
    ``decode(encode(x)) == x``.  A property of each :class:`Codec`.  It says
    the *embedding* loses nothing.  The first can hold while the second fails
    -- a codec that drops a field still produces a perfectly faithful stack of
    the truncated carrier -- so a claim of losslessness that only checks the
    substrate leg is worth nothing.

Dynamic stack parameters
------------------------
:func:`derive_dynamic_parameters` answers, for an arbitrary ``v in Q^24``: what
is the least pair ``(offset, depth)`` at which ``v`` stacks faithfully?  Three
quantities are involved and they are easy to conflate, so they are named apart:

``denominator``
    The least common denominator of the 24 rational coordinates.  Clearing it
    is what makes a rational carrier integral.  It is a *general* integer -- the
    physics register uses denominators of 12, which are not powers of two.
``dyadic_exponent``
    The least ``S >= 0`` with ``2^S v in Z^24``, when one exists.  This is what
    the plan text calls the offset ``O`` in ``2^O v in Z^24``.  It exists **only
    when every denominator is a power of two**, and is therefore ``None`` for
    most of the physics register.  It is reported, not relied on; the
    denominator route above is strictly more general and is the one the codecs
    use.
``offset`` (translation) and ``depth``
    The substrate's own parameters: a translation making the cleared integers
    non-negative, and the number of binary digit planes.  With
    ``max_abs = max |cleared coordinate|``, the least admissible pair is the
    least power of two ``offset >= max_abs`` and the least ``depth`` with
    ``2^depth > offset + max_abs``.  Every shifted coordinate then lies in
    ``[0, 2^depth - 1]`` inclusive, which is the containment the plan requires.

No depth ceiling is hardcoded anywhere.  A carrier whose coordinates reach
``10^40`` simply yields a depth near 135, and stacks exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Any, Dict, Iterable, List, Mapping, Optional, Sequence,
                    Tuple, Union)

from .. import substrate
from ..substrate import digit_stack, golay_decode, leech2, mog

__all__ = [
    "N", "Scalar", "Carrier",
    "StackParameters", "derive_dynamic_parameters", "dyadic_exponent",
    "DataObject", "Codec", "RoundTripFailure",
    "as_exact", "exact_vector", "carrier_to_json", "carrier_from_json",
]

#: Carrier dimension.  Fixed by the Leech lattice, not by convention.
N = 24

Scalar = Union[int, Fraction]
Carrier = Tuple[Scalar, ...]


class RoundTripFailure(AssertionError):
    """Raised when a codec fails its own losslessness contract."""


# ===========================================================================
# 1.  EXACT SCALARS
# ===========================================================================

def as_exact(value: Any) -> Fraction:
    """Coerce to :class:`~fractions.Fraction`, refusing floats.

    A float admitted here would silently make every downstream exactness claim
    unfalsifiable, so ``float`` raises rather than being rounded.  Decimal
    *strings* are accepted and converted exactly: ``as_exact("1.0080")`` is
    ``Fraction(126, 125)``, not an approximation.
    """
    if isinstance(value, bool):
        raise TypeError("data_objects: booleans are not carrier scalars")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    if isinstance(value, float):
        raise TypeError(
            "data_objects: floats are refused -- pass an int, a Fraction, or "
            "a decimal string (Fraction('1.0080') is exact)")
    raise TypeError(f"data_objects: inexact scalar type "
                    f"{type(value).__name__}")


def exact_vector(values: Iterable[Any]) -> Carrier:
    """Coerce 24 values to exact scalars, collapsing integral ones to ``int``."""
    out: List[Scalar] = []
    for v in values:
        f = as_exact(v)
        out.append(int(f) if f.denominator == 1 else f)
    if len(out) != N:
        raise ValueError(f"exact_vector: {N} coordinates required, "
                         f"got {len(out)}")
    return tuple(out)


# ===========================================================================
# 2.  DYNAMIC STACK PARAMETERS
# ===========================================================================

def dyadic_exponent(vector: Sequence[Scalar]) -> Optional[int]:
    """Least ``S >= 0`` with ``2^S v in Z^24``, or ``None`` if none exists.

    Exists exactly when every coordinate's denominator is a power of two.
    Returned for diagnostic completeness; the codecs clear the general least
    common denominator instead, which always exists.
    """
    worst = 0
    for value in vector:
        den = as_exact(value).denominator
        if den & (den - 1):          # not a power of two
            return None
        worst = max(worst, den.bit_length() - 1)
    return worst


@dataclass(frozen=True)
class StackParameters:
    """The derived, data-dependent parameters of a carrier's digit stack."""

    denominator: int
    """Least common denominator cleared before binary expansion."""

    max_abs: int
    """Largest absolute value among the cleared integer coordinates."""

    offset: int
    """Translation applied to every cleared coordinate; a power of two."""

    depth: int
    """Number of binary digit planes; least admissible for this carrier."""

    dyadic_exponent: Optional[int]
    """Least ``S`` with ``2^S v`` integral, or ``None`` if not dyadic."""

    def shifted_upper_bound(self) -> int:
        """The largest value any shifted coordinate can take: ``2^depth - 1``."""
        return (1 << self.depth) - 1

    def contains(self) -> bool:
        """Whether every shifted coordinate lies in ``[0, 2^depth - 1]``."""
        return 0 <= self.offset - self.max_abs and \
            self.offset + self.max_abs <= self.shifted_upper_bound()

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "denominator": self.denominator,
            "max_abs": self.max_abs,
            "offset": self.offset,
            "depth": self.depth,
            "dyadic_exponent": self.dyadic_exponent,
            "shifted_upper_bound": self.shifted_upper_bound(),
            "contained": self.contains(),
        }


def derive_dynamic_parameters(vector: Sequence[Scalar]) -> StackParameters:
    """Least admissible stack parameters for an arbitrary ``v in Q^24``.

    No depth ceiling is imposed: the depth is a measurement of the carrier's
    coordinate range after denominator clearing, exactly as Proposition D1
    describes.

    Examples
    --------
    >>> p = derive_dynamic_parameters([0] * 23 + [Fraction(3, 4)])
    >>> p.denominator, p.max_abs, p.offset, p.depth, p.dyadic_exponent
    (4, 3, 4, 4, 2)
    >>> p.contains()
    True
    """
    if len(vector) != N:
        raise ValueError(f"derive_dynamic_parameters: {N} coordinates "
                         f"required, got {len(vector)}")
    ints, den = digit_stack._clear_denominators(tuple(vector))
    max_abs = max((abs(c) for c in ints), default=0)
    offset, depth = digit_stack.derive_stack_parameters(max_abs)
    params = StackParameters(denominator=den, max_abs=max_abs, offset=offset,
                             depth=depth,
                             dyadic_exponent=dyadic_exponent(vector))
    if not params.contains():
        raise AssertionError(
            "derive_dynamic_parameters: containment violated -- this is a bug "
            "in the derivation, not in the data")
    return params


# ===========================================================================
# 3.  THE DATA OBJECT
# ===========================================================================

@dataclass(frozen=True)
class DataObject:
    """A named 24-dimensional exact carrier with its provenance.

    Parameters
    ----------
    name
        Identifier, unique within its domain.
    domain
        One of ``"physics"``, ``"chemistry"``, ``"mathematics"``,
        ``"lexicon"`` -- or any string a future codec introduces.
    carrier
        24 exact scalars.  Coerced through :func:`exact_vector`, so a float
        anywhere raises at construction rather than at analysis time.
    attributes
        The typed source data the carrier was built from.  Round-trip tests
        compare a decoded object's attributes against these.
    layout
        Per-coordinate names, in carrier order, so a coordinate can be read
        back by meaning rather than by index.
    provenance
        Free-form record of where the values came from.
    """

    name: str
    domain: str
    carrier: Carrier
    attributes: Mapping[str, Any] = field(default_factory=dict)
    layout: Tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "carrier", exact_vector(self.carrier))
        if self.layout and len(self.layout) != N:
            raise ValueError(f"DataObject: layout must name {N} coordinates, "
                             f"got {len(self.layout)}")

    # -- stack -------------------------------------------------------------

    def parameters(self) -> StackParameters:
        """Least admissible stack parameters for this carrier."""
        return derive_dynamic_parameters(self.carrier)

    def stack(self, depth: Optional[int] = None,
              offset: Optional[int] = None) -> digit_stack.DigitStack:
        """The 2-adic digit stack, fitted to this carrier by default."""
        if depth is None and offset is None:
            p = self.parameters()
            depth, offset = p.depth, p.offset
        return digit_stack.class_stack(self.carrier, depth=depth,
                                       offset=offset, basis="standard")

    def rebuild(self, depth: Optional[int] = None,
                offset: Optional[int] = None) -> Carrier:
        """Reconstruct the carrier from its stack."""
        return digit_stack.class_stack_rebuild(self.stack(depth, offset))

    def round_trip_ok(self, depth: Optional[int] = None,
                      offset: Optional[int] = None) -> bool:
        """Whether ``rebuild(stack(v)) == v`` exactly."""
        rebuilt = self.rebuild(depth, offset)
        if len(rebuilt) != len(self.carrier):
            return False
        return all(as_exact(a) == as_exact(b)
                   for a, b in zip(rebuilt, self.carrier))

    # -- geometry ----------------------------------------------------------

    def mog_grid(self) -> List[List[Scalar]]:
        """The carrier as the MOG's ``4 x 6`` frame."""
        return mog.to_grid_4x6(self.carrier)

    def mog_trio(self) -> List[List[Scalar]]:
        """The carrier as the trio's three ``2x2x2`` bricks of eight."""
        return mog.to_trio_3x8(self.carrier)

    def plane_grids(self) -> List[List[List[int]]]:
        """Each digit plane as a ``4 x 6`` grid of bits, plane 0 first."""
        out = []
        for plane in self.stack().planes:
            bits = [(plane >> i) & 1 for i in range(N)]
            out.append(mog.to_grid_4x6(bits))
        return out

    def facet_signature(self) -> Dict[str, int]:
        """Total weight in each of the 31 named MOG facets, summed over planes.

        A coarse but exactly-computed geometric fingerprint: how much of the
        carrier's binary content lands in each brick, column, row and cube
        face.  Facets overlap by design, so the weights do not sum to the
        total.
        """
        totals = {facet: 0 for facet in digit_stack.FACETS}
        for report in digit_stack.facet_projection(self.stack()):
            for facet, weight in report.facet_weights.items():
                totals[facet] += weight
        return totals

    def monster_address(self) -> Dict[str, object]:
        """The plane-0 mask and what the substrate can say about it.

        Plane 0 is a 24-bit mask, hence a MOG frame.  Whether it is also a
        ``Lambda / 2 Lambda`` class of geometric significance depends on the
        carrier being a Leech point, which a general data carrier is not; the
        report says which case applies rather than asserting the flattering
        one.
        """
        stack = self.stack()
        plane0 = stack.planes[0]
        integral = all(as_exact(c).denominator == 1 for c in self.carrier)
        ints = [int(as_exact(c)) for c in self.carrier] if integral else None
        in_lattice = bool(ints is not None and leech2.in_leech(ints))
        out: Dict[str, object] = {
            "plane0_mask": f"0x{plane0:06x}",
            "plane0_weight": bin(plane0).count("1"),
            "depth": stack.depth,
            "offset": stack.offset,
            "denominator": stack.denominator,
            "is_golay_codeword": plane0 in mog.GOLAY_SET,
            "carrier_is_integral": integral,
            "carrier_in_leech_lattice": in_lattice,
        }
        if in_lattice and ints is not None:
            cls = leech2.class_of(ints)
            out["leech_class"] = cls
            out["leech_norm2"] = leech2.norm2(ints)
            out["is_2a_axis"] = leech2.is_2a_axis(ints)
        else:
            out["leech_class"] = None
            out["note"] = ("carrier is not a point of Lambda; plane 0 is a MOG "
                           "frame but not a Lambda/2Lambda class")
        return out

    def golay_alignment(self) -> Dict[str, object]:
        """Nearest-structure report of plane 0 against the Golay code.

        Reports the exact Hamming distance from plane 0 to the ``[24,12,8]``
        code and how many codewords attain it.  Distance ``0`` means plane 0
        *is* a codeword; the Golay code corrects up to three errors, so a
        distance above three has no unique nearest codeword and the count says
        so explicitly.

        Computed by
        :func:`glm_universal.substrate.golay_decode.decode_complete`, which
        returns every minimum-weight coset leader rather than the first one a
        scan reaches, so a tie is reported and never broken silently.
        """
        plane0 = self.stack().planes[0]
        decoding = golay_decode.decode_complete(plane0)
        winners = decoding.candidates
        return {
            "plane0_mask": f"0x{plane0:06x}",
            "distance_to_code": decoding.weight,
            "nearest_codeword_count": len(winners),
            "uniquely_decodable": (decoding.status != "ambiguous"
                                   and decoding.guaranteed),
            "nearest_codeword": (f"0x{winners[0]:06x}" if len(winners) == 1
                                 else None),
            "decode_status": decoding.status,
            "decode_guaranteed": decoding.guaranteed,
        }

    # -- views -------------------------------------------------------------

    def coordinate(self, label: str) -> Scalar:
        """Read a coordinate by its layout name."""
        if not self.layout:
            raise KeyError("DataObject: no layout is defined")
        try:
            return self.carrier[self.layout.index(label)]
        except ValueError:
            raise KeyError(f"DataObject: no coordinate named {label!r}") from None

    def labelled(self) -> Dict[str, Scalar]:
        """The carrier as a ``{layout name: value}`` mapping."""
        if not self.layout:
            raise KeyError("DataObject: no layout is defined")
        return dict(zip(self.layout, self.carrier))

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view, exact rationals rendered as strings."""
        return {
            "name": self.name,
            "domain": self.domain,
            "carrier": carrier_to_json(self.carrier),
            "layout": list(self.layout),
            "parameters": self.parameters().as_dict(),
            "provenance": dict(self.provenance),
        }


# ===========================================================================
# 4.  CODEC PROTOCOL
# ===========================================================================

class Codec:
    """Base class for the four domain codecs.

    A subclass supplies :meth:`encode` and :meth:`decode` and inherits the
    contract check.  Subclasses are stateless value-factories; nothing here
    mutates.
    """

    domain: str = "abstract"
    layout: Tuple[str, ...] = ()

    def encode(self, source: Any) -> DataObject:      # pragma: no cover
        raise NotImplementedError

    def decode(self, obj: DataObject) -> Any:         # pragma: no cover
        raise NotImplementedError

    def round_trip(self, source: Any) -> Tuple[bool, Any]:
        """``(semantic round trip held, decoded value)``."""
        decoded = self.decode(self.encode(source))
        return decoded == source, decoded

    def check(self, source: Any) -> DataObject:
        """Encode, assert both round trips, return the object.

        Raises
        ------
        RoundTripFailure
            If the substrate leg or the semantic leg fails.  A codec that
            cannot pass this is not shipped.
        """
        obj = self.encode(source)
        if not obj.round_trip_ok():
            raise RoundTripFailure(
                f"{self.domain}: substrate round trip failed for {obj.name!r}")
        decoded = self.decode(obj)
        if decoded != source:
            raise RoundTripFailure(
                f"{self.domain}: semantic round trip failed for {obj.name!r}")
        return obj


# ===========================================================================
# 5.  SERIALISATION
# ===========================================================================

def carrier_to_json(carrier: Sequence[Scalar]) -> List[str]:
    """Exact rationals as ``"n/d"`` strings -- no float ever appears."""
    return [f"{as_exact(c).numerator}/{as_exact(c).denominator}"
            for c in carrier]


def carrier_from_json(values: Sequence[str]) -> Carrier:
    """Inverse of :func:`carrier_to_json`."""
    return exact_vector(Fraction(v) for v in values)
