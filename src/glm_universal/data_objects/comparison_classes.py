"""Comparison classes: the missing half of a relative measure.

Why this register exists
------------------------
``semantic_lexicon`` holds ``hot`` as a standalone concept: ten primitives, a
part of speech and four relations, one of which is ``property_of
temperature``.  That is enough to say *what quantity the word is about* and
which pole of it the word names, and it is not enough to say *how hot* -- and
it never can be, because "hot" is not a temperature.  A cup of tea is hot at
350 K, a summer day is hot at 308 K, and a star is cold at 3000 K.  The
missing datum is not resolution in the carrier; it is the **comparison class**
the word is measured against.

This module supplies it: a small register of classes, each naming

* a **quantity** that the physics register already holds -- so the dimension
  is *derived*, never typed twice;
* an exact **low** and **high** bracket, in SI base units, that the class's
  members are agreed to lie between;
* an exact **typical** magnitude inside that bracket.

and, beside the classes, the **measure scales**: for each quantity, an ordered
family of degree words, each with an exact position in ``[0, 1]``.  A word and
a class together name an exact magnitude,

.. math::  \\mathrm{magnitude} = \\mathrm{low} + p\\,(\\mathrm{high}-\\mathrm{low}),

which is a measurement rather than a word, and is what
:mod:`glm_universal.reasoning.measure_view` reads.

What is new data and what is derived
------------------------------------
Only two things here are new: the brackets of a class, and the position of a
degree word on its scale.  Everything else is re-derived at load time and
checked:

* a class's ten EXT10 exponents come from ``physics.quantity_by_name`` and a
  class naming a quantity the register does not hold fails to load;
* where ordinary language and the SI register use different names for the
  same quantity -- the lexicon's *size* is a volume, its *light* an
  illuminance -- :data:`QUANTITY_ALIASES` resolves the one to the other and
  :func:`alias_audit` requires the target to be registered and the alias not
  to be, so an alias reaches an existing quantity and can never invent one;
* a degree word that is also a lexicon concept must have that concept's
  ``property_of`` quantity, and must sit on the side of the midpoint its
  ``positive_negative`` primitive says (when that primitive is not the neutral
  ``1/2``, which for ``heavy`` it is -- see
  :func:`lexicon_agreement`);
* the poles of a lexicon ``opposite_of`` pair that both sit on a scale must
  have positions summing to 1.

Exactness
---------
Every magnitude is an ``int`` or a :class:`fractions.Fraction`.  No float is
constructed anywhere in this module, and decimal strings are read exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import physics as ph
from . import semantic_lexicon as sl
from .base import Codec, DataObject, as_exact

__all__ = [
    "COMPARISON_LAYOUT",
    "ComparisonClass", "ComparisonClassCodec",
    "DegreeWord", "MeasureScale",
    "COMPARISON_CLASSES", "MEASURE_SCALES",
    "QUANTITY_ALIASES", "resolve_quantity", "alias_audit",
    "comparison_classes", "class_by_name", "classes_for_quantity",
    "measure_scales", "scale_for_quantity", "degree_word",
    "scaled_quantities", "comparison_class_objects",
    "lexicon_agreement", "register_summary",
]


# ===========================================================================
# 0.  TWO NAMES FOR ONE QUANTITY
# ===========================================================================

#: Ordinary language names some quantities differently from the SI register.
#: The lexicon says ``large`` is ``property_of size`` and ``dark`` is
#: ``property_of light``; the physics register holds neither word, and holds
#: both quantities -- *size* is a **volume** in cubic metres and *light*, as a
#: word about how lit a scene is, is an **illuminance** in lux.
#:
#: This table is a *resolution between two names*, and deliberately nothing
#: else.  It supplies no coordinate: everything dimensional about ``size``
#: continues to be read out of the physics register's ``volume`` entry, so
#: adding an alias cannot smuggle in a quantity the register does not hold.
#: :func:`alias_audit` enforces both halves of that -- the target must be a
#: registered quantity, and the alias must **not** be, or it would shadow a
#: real entry rather than reach one.
#:
#: The table has grown once, and the second group is worth distinguishing from
#: the first.  The first two entries were added because a *measure word* named
#: a quantity the register spells differently, and each brought comparison
#: classes with it.  The rest were added because the **lexicon's own
#: ``related_to`` triples** name quantities the same way -- ``entropy
#: related_to heat``, ``heavy related_to weight``, ``dark related_to
#: illumination`` -- and every one of those relations was being declined for
#: the sole reason that the endpoint's ordinary-language name was not the SI
#: one.  They supply no classes and no coordinates; each is exactly the same
#: kind of statement as the first two, and each is subject to the same audit.
QUANTITY_ALIASES: Dict[str, str] = {
    # named by a measure word
    "size": "volume",
    "light": "illuminance",
    # named by a lexicon relation
    "heat": "energy",
    "weight": "force",
    "illumination": "illuminance",
    "distance": "length",
    "magnetic_field": "magnetic_flux_density",
}


def resolve_quantity(name: str) -> str:
    """The physics register's name for a quantity the lexicon may rename.

    Identity on every name the register already holds; the entries of
    :data:`QUANTITY_ALIASES` otherwise.
    """
    return QUANTITY_ALIASES.get(name, name)


def alias_audit() -> Dict[str, object]:
    """Check that every alias reaches the register and shadows nothing."""
    unregistered_targets: List[str] = []
    shadowing: List[str] = []
    for alias, target in QUANTITY_ALIASES.items():
        try:
            ph.quantity_by_name(target)
        except KeyError:
            unregistered_targets.append(f"{alias} -> {target}")
        try:
            ph.quantity_by_name(alias)
        except KeyError:
            pass
        else:
            shadowing.append(alias)
    return {
        "aliases": dict(QUANTITY_ALIASES),
        "count": len(QUANTITY_ALIASES),
        "unregistered_targets": unregistered_targets,
        "shadowing": shadowing,
        "sound": not (unregistered_targets or shadowing),
    }


#: What each of the 24 coordinates of a comparison-class carrier holds.
COMPARISON_LAYOUT: Tuple[str, ...] = (
    "ext10.L", "ext10.M", "ext10.T", "ext10.I", "ext10.H",   # 0..4
    "ext10.N", "ext10.J", "ext10.A", "ext10.S", "ext10.B",   # 5..9
    "low",                 # 10 the bottom of the bracket, SI base units
    "high",                # 11 the top of the bracket
    "typical",             # 12 the typical magnitude of a member
    "span",                # 13 high - low
    "midpoint",            # 14 (low + high) / 2
    "typical_position",    # 15 (typical - low) / span, in [0, 1]
    "span_ratio",          # 16 high / low, dimensionless
    "decimal_scale",       # 17 the integer k with 10^k <= typical < 10^(k+1)
    "quantity_index",      # 18 the quantity's index in the physics register
    "domain_index",        # 19 the quantity's physics domain
    "nonzero_exponents",   # 20 how many EXT10 axes the quantity uses
    "si7_lossy",           # 21 1 when EXT10 -> SI7 discards an exponent
    "scale_words",         # 22 how many degree words the quantity's scale has
    "spans_decades",       # 23 the decimal scale of the span ratio
)
assert len(COMPARISON_LAYOUT) == 24


def _decimal_scale(value: Fraction) -> int:
    """The integer ``k`` with ``10^k <= value < 10^(k+1)``, exactly.

    Decided by integer comparison against powers of ten; no logarithm is
    evaluated and no float is constructed.  ``value`` must be positive.
    """
    if value <= 0:
        raise ValueError("decimal scale: the magnitude must be positive")
    k = 0
    ten = Fraction(10)
    while value >= ten ** (k + 1):
        k += 1
    while value < ten ** k:
        k -= 1
    return k


# ===========================================================================
# 1.  THE CLASS
# ===========================================================================

@dataclass(frozen=True)
class ComparisonClass:
    """One comparison class: a quantity, a bracket, and a typical magnitude.

    ``low``, ``high`` and ``typical`` are in the SI base unit of the quantity
    -- kelvin for a temperature class, metres per second for a velocity class
    -- and are exact.  The dimension is not stored: it is read from the
    physics register by :attr:`quantity`.
    """

    name: str
    quantity: str
    low: Fraction
    high: Fraction
    typical: Fraction
    #: Prose, and prose only.  It is excluded from equality so that the
    #: codec's round trip -- which restores the bracket and the quantity,
    #: the only things a carrier holds -- is an equality of classes.
    gloss: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "low", Fraction(as_exact(self.low)))
        object.__setattr__(self, "high", Fraction(as_exact(self.high)))
        object.__setattr__(self, "typical", Fraction(as_exact(self.typical)))
        if self.low <= 0:
            raise ValueError(f"{self.name}: the bracket must be positive")
        if self.high <= self.low:
            raise ValueError(f"{self.name}: high must exceed low")
        if not (self.low <= self.typical <= self.high):
            raise ValueError(
                f"{self.name}: the typical magnitude must lie in the bracket")
        # Derivation, not decoration: a class naming a quantity the physics
        # register does not hold cannot be constructed at all.
        ph.quantity_by_name(self.quantity)

    # -- derived ------------------------------------------------------------

    @property
    def registered(self) -> ph.Quantity:
        """The physics register's entry for this class's quantity."""
        return ph.quantity_by_name(self.quantity)

    @property
    def exps_ext10(self) -> Tuple[Fraction, ...]:
        """The ten EXT10 exponents, taken from the physics register."""
        return self.registered.exps_ext10

    @property
    def unit(self) -> str:
        """The unit string the physics register records for the quantity."""
        return self.registered.unit

    @property
    def span(self) -> Fraction:
        return self.high - self.low

    @property
    def midpoint(self) -> Fraction:
        return (self.low + self.high) / 2

    @property
    def typical_position(self) -> Fraction:
        """Where the typical magnitude sits on the class's own scale."""
        return (self.typical - self.low) / self.span

    def magnitude_at(self, position: Fraction) -> Fraction:
        """The exact magnitude a position on ``[0, 1]`` names in this class."""
        position = Fraction(as_exact(position))
        if not (0 <= position <= 1):
            raise ValueError("magnitude_at: the position must lie in [0, 1]")
        return self.low + position * self.span

    def position_of(self, magnitude: Fraction) -> Fraction:
        """Where a magnitude sits on this class's scale.

        Returned unclamped: a value below the bracket has a negative position
        and one above it a position past 1, and the caller decides what to do
        about that rather than being handed a silently clipped number.
        """
        magnitude = Fraction(as_exact(magnitude))
        return (magnitude - self.low) / self.span

    def contains(self, magnitude: Fraction) -> bool:
        """Whether a magnitude lies inside the bracket, endpoints included."""
        magnitude = Fraction(as_exact(magnitude))
        return self.low <= magnitude <= self.high

    def carrier(self) -> Tuple[object, ...]:
        """The 24 coordinates of :data:`COMPARISON_LAYOUT`."""
        quantity = self.registered
        index = _quantity_index(self.quantity)
        scale = MEASURE_SCALES.get(self.quantity)
        return (
            *quantity.exps_ext10,
            self.low,
            self.high,
            self.typical,
            self.span,
            self.midpoint,
            self.typical_position,
            self.high / self.low,
            _decimal_scale(self.typical),
            index,
            quantity.domain_index,
            sum(1 for e in quantity.exps_ext10 if e != 0),
            1 if ph.si7_projection_lossy(quantity) else 0,
            len(scale.words) if scale is not None else 0,
            _decimal_scale(self.high / self.low),
        )

    def as_object(self) -> DataObject:
        """This class as a register carrier."""
        return DataObject(
            name=self.name,
            domain="comparison",
            carrier=self.carrier(),
            attributes={
                "quantity": self.quantity,
                "unit": self.unit,
                "low": self.low,
                "high": self.high,
                "typical": self.typical,
                "typical_position": self.typical_position,
                "gloss": self.gloss,
            },
            layout=COMPARISON_LAYOUT,
            provenance={
                "source": "comparison-class register",
                "derivation": "the ten exponents are read from the physics "
                              "register; only the bracket is new data",
            },
        )


def _quantity_index(name: str) -> int:
    """Position of a quantity in the physics register, for the carrier."""
    for i, quantity in enumerate(ph.load_physics_register()):
        if quantity.name == name:
            return i
    raise KeyError(f"no such physical quantity: {name}")


class ComparisonClassCodec(Codec):
    """Encode a comparison class to its carrier and read it back.

    The read-back uses coordinates 10, 11, 12 and 18 alone -- the bracket and
    the quantity -- because everything else is derived from them, so the round
    trip cannot disagree with the derivation.  The name is not a coordinate,
    exactly as in the other registers.
    """

    layout = COMPARISON_LAYOUT

    def encode(self, value: ComparisonClass) -> Tuple[object, ...]:
        return value.carrier()

    def decode(self, carrier: Sequence[object],
               name: str = "class") -> ComparisonClass:
        index = int(Fraction(carrier[18]))
        quantity = ph.load_physics_register()[index]
        return ComparisonClass(
            name=name,
            quantity=quantity.name,
            low=Fraction(carrier[10]),
            high=Fraction(carrier[11]),
            typical=Fraction(carrier[12]))


# ===========================================================================
# 2.  THE MEASURE SCALE
# ===========================================================================

@dataclass(frozen=True)
class DegreeWord:
    """One word on a measure scale, with its exact position in ``[0, 1]``."""

    word: str
    position: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "position", Fraction(as_exact(self.position)))
        if not (0 <= self.position <= 1):
            raise ValueError(f"{self.word}: position must lie in [0, 1]")


@dataclass(frozen=True)
class MeasureScale:
    """The ordered degree words of one quantity.

    The scale is *relative*: a position is not a magnitude, and becomes one
    only against a comparison class.  ``above_on`` -- the ordering the
    proposal named as the load-bearing relation -- is exactly the order of
    :attr:`words`, and is derived from the positions rather than listed.
    """

    quantity: str
    words: Tuple[DegreeWord, ...]

    def __post_init__(self) -> None:
        if len(self.words) < 2:
            raise ValueError(f"{self.quantity}: a scale needs two words")
        positions = [w.position for w in self.words]
        if positions != sorted(positions) or len(set(positions)) != len(
                positions):
            raise ValueError(
                f"{self.quantity}: scale positions must strictly increase")
        if positions[0] != 0 or positions[-1] != 1:
            raise ValueError(
                f"{self.quantity}: a scale must run from 0 to 1")
        ph.quantity_by_name(self.quantity)

    @property
    def vocabulary(self) -> Tuple[str, ...]:
        return tuple(w.word for w in self.words)

    def position_of(self, word: str) -> Fraction:
        for entry in self.words:
            if entry.word == word:
                return entry.position
        raise KeyError(f"{word} is not on the {self.quantity} scale")

    def above(self, word: str) -> Tuple[str, ...]:
        """The words strictly above ``word`` on this scale, in order."""
        p = self.position_of(word)
        return tuple(w.word for w in self.words if w.position > p)

    def nearest_word(self, position: Fraction) -> str:
        """The scale word nearest a position; ties go to the lower word.

        The comparison is exact: two candidate distances are rationals, and
        the tie case is decided by ``<=`` rather than by rounding.
        """
        position = Fraction(as_exact(position))
        best = self.words[0]
        for entry in self.words[1:]:
            if abs(entry.position - position) < abs(best.position - position):
                best = entry
        return best.word

    def above_on_pairs(self) -> Tuple[Tuple[str, str], ...]:
        """Every ``(lower, higher)`` pair the scale orders."""
        return tuple((a.word, b.word)
                     for i, a in enumerate(self.words)
                     for b in self.words[i + 1:])


# ===========================================================================
# 3.  THE DATA
# ===========================================================================

F = Fraction

#: The comparison classes, grouped by quantity and in a fixed order.  The
#: brackets are the new data this module contributes; they are stated in SI
#: base units and are deliberately generous, since a class is a *range of
#: ordinary cases*, not a measurement.
COMPARISON_CLASSES: Tuple[ComparisonClass, ...] = (
    # ── temperature (K) ────────────────────────────────────────────────
    ComparisonClass("cryostat", "temperature", F(1, 100), F(100), F(4),
                    "laboratory cryogenics, from dilution fridge to liquid "
                    "nitrogen"),
    ComparisonClass("weather", "temperature", F(233), F(323), F(288),
                    "outdoor air at the surface of the Earth"),
    ComparisonClass("human_body", "temperature", F(300), F(315), F(310),
                    "core temperature of a living human"),
    ComparisonClass("tea", "temperature", F(293), F(373), F(350),
                    "a cup of tea between room temperature and boiling"),
    ComparisonClass("oven", "temperature", F(300), F(550), F(450),
                    "a domestic oven"),
    ComparisonClass("stellar_surface", "temperature", F(2000), F(50000),
                    F(5772), "the photosphere of a main-sequence star"),
    # ── velocity (m/s) ─────────────────────────────────────────────────
    ComparisonClass("continental_drift", "velocity", F(1, 10 ** 10),
                    F(1, 10 ** 8), F(1, 10 ** 9),
                    "the motion of a tectonic plate"),
    ComparisonClass("walking", "velocity", F(1, 2), F(3), F(3, 2),
                    "a person on foot"),
    ComparisonClass("road_vehicle", "velocity", F(5), F(40), F(25),
                    "a car on a road"),
    ComparisonClass("airliner", "velocity", F(50), F(300), F(250),
                    "a commercial aircraft in cruise"),
    ComparisonClass("bullet", "velocity", F(100), F(1200), F(800),
                    "a rifle projectile"),
    # ── mass (kg) ──────────────────────────────────────────────────────
    ComparisonClass("fruit", "mass", F(1, 50), F(1, 2), F(3, 20),
                    "a piece of fruit in the hand"),
    ComparisonClass("person", "mass", F(3), F(150), F(70),
                    "a human being"),
    ComparisonClass("road_vehicle_mass", "mass", F(500), F(40000), F(1500),
                    "a car to a loaded lorry"),
    ComparisonClass("ship", "mass", F(10 ** 5), F(10 ** 8), F(10 ** 7),
                    "a vessel at sea"),
    ComparisonClass("star", "mass", F(10 ** 29), F(10 ** 32), F(2 * 10 ** 30),
                    "a main-sequence star"),
    # ── length (m) ─────────────────────────────────────────────────────
    ComparisonClass("grain", "length", F(1, 10 ** 4), F(1, 100),
                    F(1, 1000), "a grain of sand to a grain of rice"),
    ComparisonClass("room", "length", F(1), F(20), F(4),
                    "the span of a room"),
    ComparisonClass("building", "length", F(3), F(300), F(30),
                    "the height of a building"),
    ComparisonClass("mountain", "length", F(100), F(9000), F(2000),
                    "the height of a mountain"),
    ComparisonClass("planet_radius", "length", F(10 ** 6), F(10 ** 8),
                    F(6371000), "the radius of a planet"),
    # ── force (N) ──────────────────────────────────────────────────────
    ComparisonClass("grip", "force", F(10), F(600), F(300),
                    "what a human hand can exert"),
    ComparisonClass("vehicle_traction", "force", F(1000), F(10 ** 4), F(5000),
                    "the tractive force of a road vehicle"),
    ComparisonClass("rocket_thrust", "force", F(10 ** 5), F(10 ** 7),
                    F(10 ** 6), "the thrust of a launch vehicle"),
    # ── density (kg/m^3) ───────────────────────────────────────────────
    ComparisonClass("gas", "density", F(1, 10), F(10), F(6, 5),
                    "a gas at ordinary pressure"),
    ComparisonClass("liquid", "density", F(500), F(2000), F(1000),
                    "a liquid at ordinary pressure"),
    ComparisonClass("metal", "density", F(2000), F(22000), F(7870),
                    "a structural or heavy metal"),
    ComparisonClass("stellar_core", "density", F(10 ** 4), F(10 ** 6),
                    F(150000), "the core of a main-sequence star"),
    # ── pressure (Pa) ──────────────────────────────────────────────────
    ComparisonClass("atmospheric", "pressure", F(87000), F(108000),
                    F(101325), "sea-level air pressure"),
    ComparisonClass("tyre", "pressure", F(10 ** 5), F(10 ** 6), F(250000),
                    "a pneumatic tyre"),
    ComparisonClass("ocean_depth", "pressure", F(10 ** 5), F(10 ** 8),
                    F(10 ** 7), "hydrostatic pressure in the sea"),
    # ── frequency (Hz) ─────────────────────────────────────────────────
    ComparisonClass("audible", "frequency", F(20), F(20000), F(440),
                    "the range a human ear hears"),
    ComparisonClass("radio", "frequency", F(10 ** 5), F(10 ** 10),
                    F(10 ** 8), "a radio carrier"),
    # ── volume (m^3), which is what the lexicon calls *size* ───────────
    ComparisonClass("droplet", "volume", F(1, 10 ** 9), F(1, 10 ** 6),
                    F(1, 10 ** 7), "a drop of liquid to a teaspoon"),
    ComparisonClass("handheld", "volume", F(1, 10 ** 5), F(1, 100),
                    F(1, 1000), "an object carried in one hand"),
    ComparisonClass("room_volume", "volume", F(10), F(500), F(50),
                    "the air in a room"),
    ComparisonClass("building_volume", "volume", F(1000), F(10 ** 6),
                    F(10 ** 4), "the enclosed volume of a building"),
    ComparisonClass("reservoir", "volume", F(10 ** 6), F(10 ** 9),
                    F(10 ** 7), "a body of impounded water"),
    # ── illuminance (lx), which is what the lexicon calls *light* ──────
    ComparisonClass("night_sky", "illuminance", F(1, 1000), F(1, 2),
                    F(1, 4), "a scene lit by the night sky alone"),
    ComparisonClass("indoor_lighting", "illuminance", F(50), F(1000),
                    F(300), "a room under artificial light"),
    ComparisonClass("overcast_day", "illuminance", F(1000), F(20000),
                    F(10000), "daylight under cloud"),
    ComparisonClass("direct_sunlight", "illuminance", F(20000), F(120000),
                    F(100000), "an unshaded surface in full sun"),
    # ── luminous intensity (cd), the SI base quantity of light ─────────
    ComparisonClass("candle", "luminous_intensity", F(1, 2), F(2), F(1),
                    "an open flame, the unit's own namesake"),
    ComparisonClass("household_lamp", "luminous_intensity", F(10), F(500),
                    F(100), "a domestic lamp"),
    ComparisonClass("lighthouse", "luminous_intensity", F(10 ** 5),
                    F(10 ** 7), F(10 ** 6), "a coastal navigation light"),
)


def _scale(quantity: str, *pairs: Tuple[str, Fraction]) -> MeasureScale:
    return MeasureScale(quantity=quantity,
                        words=tuple(DegreeWord(w, p) for w, p in pairs))


#: The degree words of each quantity, with exact positions.  A position is
#: relative: it becomes a magnitude only against a comparison class.  Where a
#: word is also a lexicon concept the two must agree, which
#: :func:`lexicon_agreement` checks.
MEASURE_SCALES: Dict[str, MeasureScale] = {
    scale.quantity: scale for scale in (
        _scale("temperature",
               ("freezing", F(0)), ("cold", F(1, 8)), ("cool", F(3, 8)),
               ("tepid", F(1, 2)), ("warm", F(5, 8)), ("hot", F(7, 8)),
               ("scalding", F(1))),
        _scale("velocity",
               ("crawling", F(0)), ("slow", F(1, 8)), ("steady", F(3, 8)),
               ("moderate_speed", F(1, 2)), ("brisk", F(5, 8)),
               ("fast", F(7, 8)), ("blistering", F(1))),
        _scale("mass",
               ("featherlight", F(0)), ("light_adj", F(1, 8)),
               ("middling", F(1, 2)), ("hefty", F(5, 8)), ("heavy", F(7, 8)),
               ("crushing", F(1))),
        _scale("force",
               ("feeble", F(0)), ("weak", F(1, 8)), ("moderate_force",
                                                     F(1, 2)),
               ("firm", F(5, 8)), ("strong", F(7, 8)),
               ("overwhelming", F(1))),
        _scale("density",
               ("rarefied", F(0)), ("sparse", F(1, 8)), ("ordinary", F(1, 2)),
               ("dense", F(7, 8)), ("packed", F(1))),
        _scale("length",
               ("minute", F(0)), ("compact", F(1, 8)), ("medium", F(1, 2)),
               ("roomy", F(5, 8)), ("vast", F(7, 8)), ("immense", F(1))),
        _scale("pressure",
               ("slack", F(0)), ("low_pressure", F(1, 8)),
               ("nominal", F(1, 2)), ("high_pressure", F(7, 8)),
               ("crushing_pressure", F(1))),
        _scale("frequency",
               ("deep", F(0)), ("low_pitched", F(1, 8)),
               ("mid_pitched", F(1, 2)), ("high_pitched", F(7, 8)),
               ("piercing", F(1))),
        _scale("volume",
               ("minuscule", F(0)), ("small", F(1, 8)),
               ("moderate_size", F(1, 2)), ("sizeable", F(5, 8)),
               ("large", F(7, 8)), ("colossal", F(1))),
        _scale("illuminance",
               ("lightless", F(0)), ("dark", F(1, 8)), ("dim", F(3, 8)),
               ("lit", F(1, 2)), ("bright", F(7, 8)),
               ("dazzling", F(1))),
        _scale("luminous_intensity",
               ("invisible", F(0)), ("faint", F(1, 8)),
               ("glowing", F(1, 2)), ("brilliant", F(7, 8)),
               ("searing", F(1))),
    )
}


# ===========================================================================
# 4.  ACCESS
# ===========================================================================

def comparison_classes() -> Tuple[ComparisonClass, ...]:
    """Every comparison class, in register order."""
    return COMPARISON_CLASSES


def class_by_name(name: str) -> ComparisonClass:
    """One comparison class, by name."""
    for entry in COMPARISON_CLASSES:
        if entry.name == name:
            return entry
    raise KeyError(f"no such comparison class: {name}")


def classes_for_quantity(quantity: str) -> Tuple[ComparisonClass, ...]:
    """The classes that measure one quantity, in register order."""
    return tuple(c for c in COMPARISON_CLASSES if c.quantity == quantity)


def measure_scales() -> Mapping[str, MeasureScale]:
    """The scales, keyed by quantity."""
    return MEASURE_SCALES


def scale_for_quantity(quantity: str) -> Optional[MeasureScale]:
    """The scale of a quantity, or ``None`` when the quantity has no words."""
    return MEASURE_SCALES.get(quantity)


def degree_word(word: str) -> Optional[Tuple[str, Fraction]]:
    """``(quantity, position)`` for a degree word, or ``None``.

    A word is on at most one scale: :func:`register_summary` reports the
    vocabulary size, and :func:`lexicon_agreement` fails if a word were ever
    listed twice.
    """
    for quantity, scale in MEASURE_SCALES.items():
        for entry in scale.words:
            if entry.word == word:
                return (quantity, entry.position)
    return None


def scaled_quantities() -> Tuple[str, ...]:
    """The quantities that have both a scale and at least one class."""
    return tuple(sorted(q for q in MEASURE_SCALES
                        if classes_for_quantity(q)))


def comparison_class_objects() -> Tuple[DataObject, ...]:
    """The comparison-class register as carriers."""
    return tuple(entry.as_object() for entry in COMPARISON_CLASSES)


# ===========================================================================
# 5.  THE CHECKS THAT MAKE THIS A DERIVATION
# ===========================================================================

def lexicon_agreement() -> Dict[str, object]:
    """Where the scales and the semantic lexicon must, and do, agree.

    Three checks, all re-derived from the two registers rather than recorded:

    ``quantity``
        a scale word that is also a lexicon concept must have that concept's
        ``property_of`` quantity;
    ``polarity``
        the concept's ``positive_negative`` primitive must put the word on the
        side of the midpoint the scale does -- **unless** the primitive is the
        neutral ``1/2``, which carries no polarity to check.  ``heavy`` is
        exactly that case, and it is the point: the static reading cannot say
        that ``heavy`` is the high pole of mass, and the scale can;
    ``poles``
        the positions of a lexicon ``opposite_of`` pair that both sit on a
        scale must sum to 1.
    """
    concepts = {c.subject: c for c in sl.SEMANTIC_SAMPLE_CONCEPTS}
    shared: List[Dict[str, object]] = []
    quantity_errors: List[str] = []
    polarity_errors: List[str] = []
    neutral: List[str] = []
    pole_pairs: List[Dict[str, object]] = []
    pole_errors: List[str] = []
    seen: Dict[str, str] = {}
    duplicate_words: List[str] = []

    for quantity, scale in MEASURE_SCALES.items():
        for entry in scale.words:
            if entry.word in seen:
                duplicate_words.append(entry.word)
            seen[entry.word] = quantity
            concept = concepts.get(entry.word)
            if concept is None:
                continue
            named = [o for p, o in concept.relations if p == "property_of"]
            if [resolve_quantity(n) for n in named] != [quantity]:
                quantity_errors.append(
                    f"{entry.word}: lexicon says {named}, scale says "
                    f"{quantity}")
            polarity = concept.primitives.get("positive_negative")
            if polarity is None or polarity == Fraction(1, 2):
                neutral.append(entry.word)
            elif (polarity > Fraction(1, 2)) != (entry.position
                                                 > Fraction(1, 2)):
                polarity_errors.append(
                    f"{entry.word}: polarity {polarity} against position "
                    f"{entry.position}")
            shared.append({"word": entry.word, "quantity": quantity,
                           "position": entry.position,
                           "polarity": polarity})

    for concept in sl.SEMANTIC_SAMPLE_CONCEPTS:
        for predicate, other in concept.relations:
            if predicate != "opposite_of":
                continue
            here = degree_word(concept.subject)
            there = degree_word(other)
            if here is None or there is None or here[0] != there[0]:
                continue
            if concept.subject > other:      # each pair once
                continue
            total = here[1] + there[1]
            pole_pairs.append({"low": other if there[1] < here[1]
                               else concept.subject,
                               "high": concept.subject if here[1] > there[1]
                               else other,
                               "sum": total})
            if total != 1:
                pole_errors.append(
                    f"{concept.subject}/{other}: positions sum to {total}")

    return {
        "shared_words": shared,
        "shared_count": len(shared),
        "duplicate_words": duplicate_words,
        "quantity_errors": quantity_errors,
        "polarity_errors": polarity_errors,
        "polarity_neutral": neutral,
        "pole_pairs": pole_pairs,
        "pole_errors": pole_errors,
        "agrees": not (quantity_errors or polarity_errors or pole_errors
                       or duplicate_words),
    }


def register_summary() -> Mapping[str, object]:
    """What the register holds, for a report to quote."""
    quantities = sorted({c.quantity for c in COMPARISON_CLASSES})
    return {
        "classes": len(COMPARISON_CLASSES),
        "aliases": dict(QUANTITY_ALIASES),
        "alias_count": len(QUANTITY_ALIASES),
        "aliases_sound": alias_audit()["sound"],
        "quantities": tuple(quantities),
        "quantity_count": len(quantities),
        "classes_per_quantity": {q: len(classes_for_quantity(q))
                                 for q in quantities},
        "scales": len(MEASURE_SCALES),
        "scale_words": sum(len(s.words) for s in MEASURE_SCALES.values()),
        "scaled_quantities": scaled_quantities(),
        "widest_class": max(
            COMPARISON_CLASSES,
            key=lambda c: _decimal_scale(c.high / c.low)).name,
        "lexicon_agreement": lexicon_agreement()["agrees"],
    }
