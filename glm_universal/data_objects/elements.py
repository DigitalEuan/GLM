"""Chemistry carriers: all 118 elements, and the diatomics with measured D0.

The register
------------
118 elements ingested from PubChem's periodic table and frozen into
``_data/elements_118.json``.  Every decimal column was converted with
``Fraction(str)``, which is exact: hydrogen's atomic weight is the rational
``126/125``, not ``1.008`` rounded to a binary float.

Missingness is data, not an inconvenience
-----------------------------------------
The source is a real measured table and it has holes -- the superheavy
elements have no measured electronegativity, most of the periodic table has no
tabulated homonuclear bond dissociation energy.  In-repo coverage over the 118
elements is:

===============================  =======
atomic weight                    118/118
group block, standard state      118/118
valence electrons (derived)      108/118
ionization energy                102/118
melting point                    103/118
density                           96/118
electronegativity (Pauling)       95/118
atomic radius (PubChem)           99/118
boiling point                     93/118
electron affinity                 57/118
covalent radius (Cordero)          24/118
homonuclear BDE                    21/118
===============================  =======

Nothing is imputed.  A missing field is stored as coordinate ``0`` **and** its
bit is set in the missingness mask at coordinate 17, so ``0`` as a measured
value and ``0`` as "no measurement" stay distinguishable and the round trip
restores ``None`` rather than a fabricated zero.  Any analysis that treats the
zero as a measurement is reading the carrier without reading the mask.

Valence electrons are *derived*, not quoted: the ``s`` and ``p`` electrons of
the highest principal quantum number in the PubChem electron configuration.
For the ten elements whose configuration is flagged ``(predicted)`` the
derivation is declined and the field is missing.

The 24-coordinate layout
------------------------
::

    0   z                        atomic number (1..118)
    1   atomic_weight_u          exact rational, u
    2   electronegativity        Pauling
    3   atomic_radius_pm         PubChem empirical radius, pm
    4   covalent_radius_pm       Cordero consensus, pm
    5   valence_electrons        derived from the configuration
    6   homonuclear_bde          kJ/mol
    7   ionization_energy_eV
    8   electron_affinity_eV
    9   melting_point_K
    10  boiling_point_K
    11  density_g_per_cm3
    12  period                   derived from z
    13  group_block_code
    14  standard_state_code
    15  year_discovered
    16  electron_count_check     equals z; a redundant consistency coordinate
    17  missing_mask             bitmask over coordinates 1..16
    18  golay_codeword           the [24,12,8] codeword of z
    19  brick0_weight            Golay weight in MOG trio brick 0
    20  brick1_weight
    21  brick2_weight
    22  hexacode_shadow          the GF(4) shadow packed base-4
    23  golay_weight             total Hamming weight of the codeword

Coordinates 18..23 are functions of ``z`` alone.  They are the element's
address in MOG geometry: ``z`` is mapped to a 12-bit message, the Golay
encoder produces the codeword, and its weight profile across the trio is
recorded.  Because the Golay code has minimum distance 8, two elements' address
words differ in at least eight of the 24 cells -- the periodic table inherits
an error-correcting separation it did not have.  Decoding reads 0..17 and
re-derives 18..23, so a corrupted address is detected rather than believed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..substrate import mog
from .base import Codec, DataObject, Scalar, as_exact

__all__ = [
    "ELEMENT_LAYOUT", "MEASURED_FIELDS", "Element", "Diatomic",
    "ElementCodec", "load_element_register", "load_diatomic_register",
    "element_objects", "element_by_symbol", "element_by_z",
    "period_of", "golay_address", "periodic_separation_report",
]

_ELEMENTS = Path(__file__).resolve().parent / "_data" / "elements_118.json"
_DIATOMICS = Path(__file__).resolve().parent / "_data" / "diatomics.json"

#: Carrier coordinates 1..16, in order.  Coordinate i holds field i-1 of this
#: tuple, and bit i-1 of the missingness mask records whether it was measured.
MEASURED_FIELDS: Tuple[str, ...] = (
    "atomic_weight_u", "electronegativity_pauling", "atomic_radius_pm",
    "covalent_radius_pm", "valence_electrons", "homonuclear_bde_kJ_per_mol",
    "ionization_energy_eV", "electron_affinity_eV", "melting_point_K",
    "boiling_point_K", "density_g_per_cm3", "period", "group_block_code",
    "standard_state_code", "year_discovered", "electron_count_check",
)
assert len(MEASURED_FIELDS) == 16

ELEMENT_LAYOUT: Tuple[str, ...] = (
    ("z",) + MEASURED_FIELDS + ("missing_mask", "golay_codeword",
                                "brick0_weight", "brick1_weight",
                                "brick2_weight", "hexacode_shadow",
                                "golay_weight")
)
assert len(ELEMENT_LAYOUT) == 24

#: Last atomic number of each period; used to derive the period from ``z``.
_PERIOD_ENDS = (2, 10, 18, 36, 54, 86, 118)


def period_of(z: int) -> int:
    """The periodic-table period of atomic number ``z`` (1..7)."""
    if not 1 <= z <= 118:
        raise ValueError(f"period_of: z must be 1..118, got {z}")
    for i, end in enumerate(_PERIOD_ENDS, start=1):
        if z <= end:
            return i
    raise AssertionError("unreachable")


@dataclass(frozen=True)
class Element:
    """One chemical element with exact rational attributes.

    Every measured field is ``Optional``: ``None`` means the in-repo sources
    carry no value, and is preserved through the round trip.
    """

    z: int
    symbol: str
    name: str
    electron_configuration: str
    atomic_weight_u: Optional[Fraction] = None
    electronegativity_pauling: Optional[Fraction] = None
    atomic_radius_pm: Optional[Fraction] = None
    covalent_radius_pm: Optional[Fraction] = None
    valence_electrons: Optional[int] = None
    homonuclear_bde_kJ_per_mol: Optional[Fraction] = None
    ionization_energy_eV: Optional[Fraction] = None
    electron_affinity_eV: Optional[Fraction] = None
    melting_point_K: Optional[Fraction] = None
    boiling_point_K: Optional[Fraction] = None
    density_g_per_cm3: Optional[Fraction] = None
    group_block: Optional[str] = None
    group_block_code: Optional[int] = None
    standard_state: Optional[str] = None
    standard_state_code: Optional[int] = None
    year_discovered: Optional[int] = None

    @property
    def period(self) -> int:
        """Derived from ``z``; always present."""
        return period_of(self.z)

    def field(self, name: str) -> Optional[Fraction]:
        """Value of a :data:`MEASURED_FIELDS` entry, including derived ones."""
        if name == "period":
            return Fraction(self.period)
        if name == "electron_count_check":
            return Fraction(self.z)
        value = getattr(self, name)
        return None if value is None else as_exact(value)


@dataclass(frozen=True)
class Diatomic:
    """A diatomic species with an experimental dissociation energy at 0 K."""

    species: str
    element_a: str
    element_b: str
    charge: int
    d0_kJ_per_mol: Optional[Fraction]
    uncertainty_kJ_per_mol: Optional[Fraction]
    uncertainty_status: str

    @property
    def homonuclear(self) -> bool:
        """Whether both atoms are the same element."""
        return self.element_a == self.element_b


# ===========================================================================
# GOLAY ADDRESSING
# ===========================================================================

def golay_address(z: int) -> Dict[str, int]:
    """The MOG address of an element, derived from ``z`` alone.

    ``z`` indexes the ``[24, 12, 8]`` Golay code's 4096 codewords directly
    (``1 <= z <= 118 < 4096``), so distinct elements receive distinct
    codewords at Hamming distance at least 8 -- the code's minimum distance.
    """
    if not 1 <= z <= 118:
        raise ValueError(f"golay_address: z must be 1..118, got {z}")
    word = mog.GOLAY_MASKS[z]
    shadow = mog.hexacode_shadow(word)
    packed = 0
    for digit in shadow:
        packed = packed * 4 + int(digit)
    return {
        "codeword": word,
        "brick0_weight": bin(word & mog.BRICKS[0]).count("1"),
        "brick1_weight": bin(word & mog.BRICKS[1]).count("1"),
        "brick2_weight": bin(word & mog.BRICKS[2]).count("1"),
        "hexacode_shadow": packed,
        "weight": bin(word).count("1"),
    }


# ===========================================================================
# REGISTERS
# ===========================================================================

def _ofrac(text: Optional[str]) -> Optional[Fraction]:
    return None if text is None else Fraction(text)


@lru_cache(maxsize=1)
def load_element_register() -> Tuple[Element, ...]:
    """The 118 elements, parsed once from the frozen snapshot."""
    raw = json.loads(_ELEMENTS.read_text(encoding="utf-8"))
    out: List[Element] = []
    for rec in raw["elements"]:
        out.append(Element(
            z=rec["z"], symbol=rec["symbol"], name=rec["name"],
            electron_configuration=rec["electron_configuration"],
            atomic_weight_u=_ofrac(rec["atomic_weight_u"]),
            electronegativity_pauling=_ofrac(rec["electronegativity_pauling"]),
            atomic_radius_pm=_ofrac(rec["atomic_radius_pm"]),
            covalent_radius_pm=_ofrac(rec["covalent_radius_pm"]),
            valence_electrons=rec["valence_electrons"],
            homonuclear_bde_kJ_per_mol=_ofrac(
                rec["homonuclear_bde_kJ_per_mol"]),
            ionization_energy_eV=_ofrac(rec["ionization_energy_eV"]),
            electron_affinity_eV=_ofrac(rec["electron_affinity_eV"]),
            melting_point_K=_ofrac(rec["melting_point_K"]),
            boiling_point_K=_ofrac(rec["boiling_point_K"]),
            density_g_per_cm3=_ofrac(rec["density_g_per_cm3"]),
            group_block=rec["group_block"],
            group_block_code=rec["group_block_code"],
            standard_state=rec["standard_state"],
            standard_state_code=rec["standard_state_code"],
            year_discovered=rec["year_discovered"],
        ))
    if len(out) != 118:
        raise AssertionError(f"element register holds {len(out)}, not 118")
    if sorted(e.z for e in out) != list(range(1, 119)):
        raise AssertionError("atomic numbers are not contiguous 1..118")
    return tuple(out)


@lru_cache(maxsize=1)
def load_diatomic_register() -> Tuple[Diatomic, ...]:
    """Diatomic species with NIST CCCBDB dissociation energies at 0 K."""
    raw = json.loads(_DIATOMICS.read_text(encoding="utf-8"))
    return tuple(
        Diatomic(species=r["species"], element_a=r["element_a"],
                 element_b=r["element_b"], charge=r["charge"],
                 d0_kJ_per_mol=_ofrac(r["d0_kJ_per_mol"]),
                 uncertainty_kJ_per_mol=_ofrac(r["uncertainty_kJ_per_mol"]),
                 uncertainty_status=r["uncertainty_status"])
        for r in raw["species"])


@lru_cache(maxsize=1)
def _by_symbol() -> Dict[str, Element]:
    return {e.symbol: e for e in load_element_register()}


def element_by_symbol(symbol: str) -> Element:
    """Look an element up by chemical symbol."""
    try:
        return _by_symbol()[symbol]
    except KeyError:
        raise KeyError(f"elements: no element with symbol {symbol!r}") from None


def element_by_z(z: int) -> Element:
    """Look an element up by atomic number."""
    return load_element_register()[z - 1]


# ===========================================================================
# CODEC
# ===========================================================================

class ElementCodec(Codec):
    """Embed an :class:`Element` in ``Q^24`` and read it back exactly."""

    domain = "chemistry"
    layout = ELEMENT_LAYOUT

    def encode(self, source: Element) -> DataObject:
        """The 24-coordinate carrier of a chemical element."""
        carrier: List[Scalar] = [source.z]
        mask = 0
        for i, name in enumerate(MEASURED_FIELDS):
            value = source.field(name)
            if value is None:
                mask |= 1 << i
                carrier.append(0)
            else:
                carrier.append(value)
        carrier.append(mask)                       # 17
        addr = golay_address(source.z)
        carrier.append(addr["codeword"])           # 18
        carrier.append(addr["brick0_weight"])      # 19
        carrier.append(addr["brick1_weight"])      # 20
        carrier.append(addr["brick2_weight"])      # 21
        carrier.append(addr["hexacode_shadow"])    # 22
        carrier.append(addr["weight"])             # 23
        return DataObject(
            name=source.symbol, domain=self.domain, carrier=carrier,
            attributes={
                "name": source.name, "z": source.z,
                "electron_configuration": source.electron_configuration,
                "group_block": source.group_block,
                "standard_state": source.standard_state,
                "period": source.period,
                "missing_fields": [n for i, n in enumerate(MEASURED_FIELDS)
                                   if mask >> i & 1],
            },
            layout=ELEMENT_LAYOUT,
            provenance={
                "source": ("PubChem periodic table via _data/elements_118.json"
                           "; covalent radius and BDE from the in-repo Cordero"
                           " and CRC tables (partial coverage)"),
                "missing_policy": ("absent values are coordinate 0 with the "
                                   "bit set in missing_mask; nothing imputed"),
            },
        )

    def decode(self, obj: DataObject) -> Element:
        """Recover the element.  Raises if the derived Golay address disagrees."""
        c = obj.carrier
        z = int(c[0])
        mask = int(c[17])
        values: Dict[str, Optional[Fraction]] = {}
        for i, name in enumerate(MEASURED_FIELDS):
            values[name] = None if (mask >> i) & 1 else as_exact(c[1 + i])

        addr = golay_address(z)
        expected = (addr["codeword"], addr["brick0_weight"],
                    addr["brick1_weight"], addr["brick2_weight"],
                    addr["hexacode_shadow"], addr["weight"])
        found = tuple(int(x) for x in c[18:24])
        if found != expected:
            raise ValueError(
                f"elements.decode: Golay address of {obj.name!r} is "
                f"inconsistent with z={z}; carrier is corrupt")
        if values["period"] is not None and int(values["period"]) != period_of(z):
            raise ValueError(
                f"elements.decode: period of {obj.name!r} disagrees with z={z}")
        if (values["electron_count_check"] is not None
                and int(values["electron_count_check"]) != z):
            raise ValueError(
                f"elements.decode: electron count check of {obj.name!r} "
                f"disagrees with z={z}")

        attrs = obj.attributes
        ve = values["valence_electrons"]
        return Element(
            z=z, symbol=obj.name, name=attrs["name"],
            electron_configuration=attrs["electron_configuration"],
            atomic_weight_u=values["atomic_weight_u"],
            electronegativity_pauling=values["electronegativity_pauling"],
            atomic_radius_pm=values["atomic_radius_pm"],
            covalent_radius_pm=values["covalent_radius_pm"],
            valence_electrons=None if ve is None else int(ve),
            homonuclear_bde_kJ_per_mol=values["homonuclear_bde_kJ_per_mol"],
            ionization_energy_eV=values["ionization_energy_eV"],
            electron_affinity_eV=values["electron_affinity_eV"],
            melting_point_K=values["melting_point_K"],
            boiling_point_K=values["boiling_point_K"],
            density_g_per_cm3=values["density_g_per_cm3"],
            group_block=attrs["group_block"],
            group_block_code=(None if values["group_block_code"] is None
                              else int(values["group_block_code"])),
            standard_state=attrs["standard_state"],
            standard_state_code=(None if values["standard_state_code"] is None
                                 else int(values["standard_state_code"])),
            year_discovered=(None if values["year_discovered"] is None
                             else int(values["year_discovered"])),
        )


def element_objects() -> Tuple[DataObject, ...]:
    """All 118 elements as encoded :class:`DataObject` instances."""
    codec = ElementCodec()
    return tuple(codec.encode(e) for e in load_element_register())


# ===========================================================================
# DIAGNOSTICS
# ===========================================================================

def periodic_separation_report() -> Dict[str, object]:
    """Minimum pairwise Hamming separation of the 118 Golay element addresses.

    Computed over all ``C(118, 2) = 6903`` pairs.  The Golay code's minimum
    distance is 8, so the observed minimum must be at least 8; reporting it
    turns that guarantee into a measurement.
    """
    words = [golay_address(z)["codeword"] for z in range(1, 119)]
    best = 24
    pairs = 0
    histogram: Dict[int, int] = {}
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            d = bin(words[i] ^ words[j]).count("1")
            histogram[d] = histogram.get(d, 0) + 1
            best = min(best, d)
            pairs += 1
    return {
        "elements": len(words),
        "pairs_compared": pairs,
        "minimum_separation": best,
        "golay_minimum_distance": 8,
        "meets_golay_bound": best >= 8,
        "distinct_codewords": len(set(words)),
        "distance_histogram": dict(sorted(histogram.items())),
    }
