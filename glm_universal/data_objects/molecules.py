"""``glm_universal.data_objects.molecules`` -- molecules as multi-carriers.

What was missing
----------------
The chemistry register holds 118 elements and 52 diatomics.  A molecule of
any size had no representation at all: there was no way to say ``C6H12O6``
to the machine, and no carrier for it to sit on.

The representation
------------------
A molecule is **not** collapsed into one carrier and left there.  It is a
*multi-carrier*: the bundle of its constituent element carriers, each with
its count, together with one composite carrier derived from them.  Both are
kept, because they say different things and the composite alone cannot say
what the bundle says:

* the **bundle** ``((symbol, count, carrier), ...)`` is faithful --
  :func:`formula_from_bundle` reads the formula straight back off it;
* the **composite** carrier is the 24 coordinates the geometry works with,
  and it is a *summary*.  :func:`composite_collisions` looks for two
  different molecules with the same composite and reports what it finds,
  rather than assuming the summary is injective.

Every number on a molecule's carrier is computed from the element register
at load time.  There is no molecular data file: the only thing stored per
molecule is its **name and formula**, and everything else -- molar mass,
electron count, electronegativity spread, degree of unsaturation -- is
derived.  Where the element register has a gap the derived value is absent
and the missingness bit is set, exactly as it is for an element; nothing is
imputed.

The formula grammar
-------------------
:func:`parse_formula` reads element symbols with optional counts, nested
brackets, hydrates written with ``.``, and a trailing charge in the usual
``+``/``-``/``2+`` notation: ``H2O``, ``Ca(OH)2``, ``Fe2(SO4)3``,
``CuSO4.5H2O``, ``SO4 2-``.  An unknown symbol is refused by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import mog
from .base import Codec, DataObject, Scalar, as_exact
from .elements import Element, element_by_symbol, load_element_register

__all__ = [
    "MOLECULE_LAYOUT",
    "MOLECULE_FIELDS",
    "MOLECULES",
    "FormulaError",
    "Molecule",
    "MoleculeCodec",
    "parse_formula",
    "format_formula",
    "molecule_by_name",
    "load_molecule_register",
    "molecule_objects",
    "molecule_bundle",
    "formula_from_bundle",
    "composite_collisions",
    "molecules_report",
]


class FormulaError(ValueError):
    """Raised when a formula names an element the register does not have."""


# ===========================================================================
# 1.  THE FORMULA GRAMMAR
# ===========================================================================

def _symbols() -> Dict[str, Element]:
    return {e.symbol: e for e in load_element_register()}


def parse_formula(text: str) -> Tuple[Dict[str, int], int]:
    """Read a formula into element counts and a charge.

    Returns ``(counts, charge)``.  Raises :class:`FormulaError` on an
    unknown element symbol, an unbalanced bracket or a count of zero.
    """
    known = _symbols()
    body = text.strip()
    charge = 0

    # A trailing charge: "2-", "+", "3+".  Only at the very end.
    #
    # The magnitude digits are read only when they are separated from the
    # formula by whitespace, as the register writes them ("SO4 2-").  Without
    # that rule "NO3-" would be ambiguous -- nitrate with charge -1, or NO
    # with charge -3 -- and the parser would silently pick the second.  With
    # it, a bare sign is a unit charge and nothing is guessed:  "NO3-" is
    # nitrate, "O4S 2-" is sulfate.
    while body and body[-1] in "+-":
        sign = 1 if body[-1] == "+" else -1
        rest = body[:-1]
        digits = ""
        while rest and rest[-1].isdigit():
            digits = rest[-1] + digits
            rest = rest[:-1]
        if digits and not (rest == "" or rest[-1].isspace()):
            # The digits belong to the last element symbol, not the charge.
            digits = ""
            rest = body[:-1]
        charge += sign * (int(digits) if digits else 1)
        body = rest.rstrip()
        break

    # Hydrates and adducts: "CuSO4.5H2O" is the sum of its parts.
    if "." in body:
        total: Dict[str, int] = {}
        for part in body.split("."):
            part = part.strip()
            if not part:
                raise FormulaError(f"parse_formula: empty part in {text!r}")
            multiplier = 0
            index = 0
            while index < len(part) and part[index].isdigit():
                multiplier = multiplier * 10 + int(part[index])
                index += 1
            multiplier = multiplier or 1
            counts, part_charge = parse_formula(part[index:])
            if part_charge:
                raise FormulaError(f"parse_formula: a charge inside an adduct "
                                   f"is not supported: {text!r}")
            for symbol, count in counts.items():
                total[symbol] = total.get(symbol, 0) + multiplier * count
        return total, charge

    stack: List[Dict[str, int]] = [{}]
    index = 0
    while index < len(body):
        char = body[index]
        if char.isspace():
            index += 1
        elif char in "([":
            stack.append({})
            index += 1
        elif char in ")]":
            if len(stack) == 1:
                raise FormulaError(f"parse_formula: unbalanced bracket in "
                                   f"{text!r}")
            group = stack.pop()
            index += 1
            count = 0
            while index < len(body) and body[index].isdigit():
                count = count * 10 + int(body[index])
                index += 1
            count = count or 1
            for symbol, value in group.items():
                stack[-1][symbol] = stack[-1].get(symbol, 0) + value * count
        elif char.isupper():
            start = index
            index += 1
            while index < len(body) and body[index].islower():
                index += 1
            symbol = body[start:index]
            if symbol not in known:
                raise FormulaError(f"parse_formula: {symbol!r} is not an "
                                   f"element in the register ({text!r})")
            count = 0
            while index < len(body) and body[index].isdigit():
                count = count * 10 + int(body[index])
                index += 1
            count = count or 1
            if count == 0:
                raise FormulaError(f"parse_formula: a count of zero in "
                                   f"{text!r}")
            stack[-1][symbol] = stack[-1].get(symbol, 0) + count
        else:
            raise FormulaError(f"parse_formula: unreadable character "
                               f"{char!r} in {text!r}")
    if len(stack) != 1:
        raise FormulaError(f"parse_formula: unclosed bracket in {text!r}")
    if not stack[0]:
        raise FormulaError(f"parse_formula: {text!r} names no element")
    return stack[0], charge


def format_formula(counts: Dict[str, int], charge: int = 0) -> str:
    """A formula string in Hill order: carbon, hydrogen, then alphabetical."""
    remaining = dict(counts)
    parts: List[str] = []

    def emit(symbol: str) -> None:
        count = remaining.pop(symbol)
        parts.append(symbol if count == 1 else f"{symbol}{count}")

    if "C" in remaining:
        emit("C")
        if "H" in remaining:
            emit("H")
    for symbol in sorted(remaining):
        parts.append(symbol if remaining[symbol] == 1
                     else f"{symbol}{remaining[symbol]}")
    text = "".join(parts)
    if charge:
        # A space before the charge, as the register writes it.  It is what
        # keeps the result re-readable: without it "O4S2-" would parse as
        # S2 with charge -1 rather than sulfate.
        magnitude = abs(charge)
        text += " " + ("" if magnitude == 1 else str(magnitude))
        text += "+" if charge > 0 else "-"
    return text


# ===========================================================================
# 2.  THE MOLECULE
# ===========================================================================

#: Coordinates 0..18 of the carrier, in order.  Coordinate ``i`` holds field
#: ``i`` of this tuple and bit ``i`` of the missingness mask says whether the
#: element register had what it needed to compute it.
MOLECULE_FIELDS: Tuple[str, ...] = (
    "atom_count", "distinct_elements", "molar_mass_u", "electron_count",
    "valence_electron_total", "heaviest_z", "lightest_z",
    "electronegativity_min", "electronegativity_max",
    "electronegativity_mean", "electronegativity_spread",
    "degree_of_unsaturation", "charge", "carbon_count", "hydrogen_count",
    "oxygen_count", "nitrogen_count", "heteroatom_count",
    "carbon_mass_fraction",
)
assert len(MOLECULE_FIELDS) == 19

MOLECULE_LAYOUT: Tuple[str, ...] = MOLECULE_FIELDS + (
    "missing_mask", "composition_codeword", "composition_brick0",
    "composition_brick1", "composition_brick2")
assert len(MOLECULE_LAYOUT) == 24


@dataclass(frozen=True)
class Molecule:
    """A molecule: a name, a formula, and everything derived from them."""

    name: str
    formula: str
    counts: Dict[str, int]
    charge: int

    # -- composition ------------------------------------------------------
    @property
    def atom_count(self) -> int:
        return sum(self.counts.values())

    @property
    def distinct_elements(self) -> int:
        return len(self.counts)

    def count_of(self, symbol: str) -> int:
        return self.counts.get(symbol, 0)

    @property
    def heteroatom_count(self) -> int:
        return sum(count for symbol, count in self.counts.items()
                   if symbol not in ("C", "H"))

    # -- derived from the element register --------------------------------
    def _elements(self) -> List[Tuple[Element, int]]:
        return [(element_by_symbol(symbol), count)
                for symbol, count in sorted(self.counts.items())]

    @property
    def molar_mass_u(self) -> Optional[Fraction]:
        total = Fraction(0)
        for element, count in self._elements():
            if element.atomic_weight_u is None:
                return None
            total += Fraction(element.atomic_weight_u) * count
        return total

    @property
    def electron_count(self) -> int:
        return (sum(element.z * count for element, count in self._elements())
                - self.charge)

    @property
    def valence_electron_total(self) -> Optional[int]:
        total = 0
        for element, count in self._elements():
            if element.valence_electrons is None:
                return None
            total += element.valence_electrons * count
        return total - self.charge

    @property
    def heaviest_z(self) -> int:
        return max(element.z for element, _c in self._elements())

    @property
    def lightest_z(self) -> int:
        return min(element.z for element, _c in self._elements())

    def _electronegativities(self) -> Optional[List[Tuple[Fraction, int]]]:
        out: List[Tuple[Fraction, int]] = []
        for element, count in self._elements():
            if element.electronegativity_pauling is None:
                return None
            out.append((Fraction(element.electronegativity_pauling), count))
        return out

    @property
    def electronegativity_min(self) -> Optional[Fraction]:
        values = self._electronegativities()
        return None if values is None else min(v for v, _c in values)

    @property
    def electronegativity_max(self) -> Optional[Fraction]:
        values = self._electronegativities()
        return None if values is None else max(v for v, _c in values)

    @property
    def electronegativity_spread(self) -> Optional[Fraction]:
        values = self._electronegativities()
        if values is None:
            return None
        return max(v for v, _c in values) - min(v for v, _c in values)

    @property
    def electronegativity_mean(self) -> Optional[Fraction]:
        """The count-weighted mean: an atom-by-atom average, not a per-element one."""
        values = self._electronegativities()
        if values is None:
            return None
        return (sum(v * c for v, c in values)
                / Fraction(sum(c for _v, c in values)))

    @property
    def carbon_mass_fraction(self) -> Optional[Fraction]:
        mass = self.molar_mass_u
        if mass is None or mass == 0:
            return None
        carbon = element_by_symbol("C")
        if carbon.atomic_weight_u is None:
            return None
        return (Fraction(carbon.atomic_weight_u) * self.count_of("C")) / mass

    @property
    def degree_of_unsaturation(self) -> Optional[Fraction]:
        """Rings plus pi bonds, for a formula built from C, H, N, O and halogens.

        ``(2C + 2 + N - H - X) / 2``.  It is defined only when every element
        present has a settled valence in that formula, so a molecule with a
        transition metal in it gets ``None`` rather than a number that does
        not mean anything.
        """
        allowed = {"C", "H", "N", "O", "F", "Cl", "Br", "I", "S", "P"}
        if any(symbol not in allowed for symbol in self.counts):
            return None
        if any(self.count_of(symbol) for symbol in ("S", "P")):
            return None
        halogens = sum(self.count_of(s) for s in ("F", "Cl", "Br", "I"))
        value = (2 * self.count_of("C") + 2 + self.count_of("N")
                 - self.count_of("H") - halogens)
        return Fraction(value, 2)

    def field(self, name: str) -> Optional[Fraction]:
        """One carrier field, as an exact value or ``None`` if unavailable."""
        if name == "atom_count":
            return Fraction(self.atom_count)
        if name == "distinct_elements":
            return Fraction(self.distinct_elements)
        if name == "electron_count":
            return Fraction(self.electron_count)
        if name == "heaviest_z":
            return Fraction(self.heaviest_z)
        if name == "lightest_z":
            return Fraction(self.lightest_z)
        if name == "charge":
            return Fraction(self.charge)
        if name == "heteroatom_count":
            return Fraction(self.heteroatom_count)
        if name in ("carbon_count", "hydrogen_count", "oxygen_count",
                    "nitrogen_count"):
            symbol = {"carbon_count": "C", "hydrogen_count": "H",
                      "oxygen_count": "O", "nitrogen_count": "N"}[name]
            return Fraction(self.count_of(symbol))
        value = getattr(self, name)
        return None if value is None else as_exact(value)


# ===========================================================================
# 3.  THE REGISTER
# ===========================================================================

#: The molecules the register carries: a name and a formula each, and
#: nothing else.  Every number attached to them is derived from the element
#: register, so this table cannot be wrong about a measurement -- it does
#: not contain one.
MOLECULES: Tuple[Tuple[str, str], ...] = (
    # inorganic
    ("water", "H2O"),
    ("hydrogen peroxide", "H2O2"),
    ("ammonia", "NH3"),
    ("carbon dioxide", "CO2"),
    ("carbon monoxide", "CO"),
    ("methane", "CH4"),
    ("sulfuric acid", "H2SO4"),
    ("nitric acid", "HNO3"),
    ("hydrochloric acid", "HCl"),
    ("sodium chloride", "NaCl"),
    ("calcium carbonate", "CaCO3"),
    ("calcium hydroxide", "Ca(OH)2"),
    ("iron(III) sulfate", "Fe2(SO4)3"),
    ("copper(II) sulfate pentahydrate", "CuSO4.5H2O"),
    ("silicon dioxide", "SiO2"),
    ("aluminium oxide", "Al2O3"),
    ("titanium dioxide", "TiO2"),
    ("sodium hydroxide", "NaOH"),
    ("potassium permanganate", "KMnO4"),
    ("ozone", "O3"),
    ("dinitrogen monoxide", "N2O"),
    ("sulfur hexafluoride", "SF6"),
    ("phosphoric acid", "H3PO4"),
    # organic
    ("methanol", "CH4O"),
    ("ethanol", "C2H6O"),
    ("acetic acid", "C2H4O2"),
    ("acetone", "C3H6O"),
    ("benzene", "C6H6"),
    ("toluene", "C7H8"),
    ("phenol", "C6H6O"),
    ("glucose", "C6H12O6"),
    ("sucrose", "C12H22O11"),
    ("urea", "CH4N2O"),
    ("glycine", "C2H5NO2"),
    ("alanine", "C3H7NO2"),
    ("caffeine", "C8H10N4O2"),
    ("aspirin", "C9H8O4"),
    ("paracetamol", "C8H9NO2"),
    ("ethylene", "C2H4"),
    ("acetylene", "C2H2"),
    ("naphthalene", "C10H8"),
    ("octane", "C8H18"),
    ("cyclohexane", "C6H12"),
    ("formaldehyde", "CH2O"),
    ("chloroform", "CHCl3"),
    ("dichlorodifluoromethane", "CCl2F2"),
    # ions
    ("sulfate ion", "SO4 2-"),
    ("nitrate ion", "NO3 -"),
    ("ammonium ion", "NH4 +"),
    ("carbonate ion", "CO3 2-"),
    ("hydroxide ion", "OH -"),
)


@lru_cache(maxsize=1)
def load_molecule_register() -> Tuple[Molecule, ...]:
    """Every molecule, with its composition parsed from its formula."""
    out: List[Molecule] = []
    for name, formula in MOLECULES:
        counts, charge = parse_formula(formula)
        out.append(Molecule(name=name, formula=formula, counts=counts,
                            charge=charge))
    return tuple(out)


def molecule_from_formula(text: str, name: Optional[str] = None) -> Molecule:
    """Build a molecule from a formula alone, registered or not.

    The register holds 51 species, and a formula names infinitely many.  This
    is the route for the rest of them: the formula is parsed into an exact
    composition and charge, and every coordinate of the resulting carrier is
    then derived from the element register exactly as a registered molecule's
    is -- so an unregistered species is a first-class carrier, not a special
    case.  Raises :class:`FormulaError` if the formula does not parse or names
    an element the register does not hold.
    """
    counts, charge = parse_formula(text)
    return Molecule(name=name or format_formula(counts, charge),
                    formula=text, counts=counts, charge=charge)


def object_from_formula(text: str, name: Optional[str] = None) -> DataObject:
    """The encoded carrier of a molecule named only by its formula."""
    return MoleculeCodec().encode(molecule_from_formula(text, name))


def molecule_by_name(name: str) -> Molecule:
    """One molecule by name, or by formula."""
    key = name.strip().lower()
    for molecule in load_molecule_register():
        if molecule.name.lower() == key or molecule.formula.lower() == key:
            return molecule
    raise KeyError(f"molecule_by_name: no molecule named {name!r}")


# ===========================================================================
# 4.  THE CARRIERS
# ===========================================================================

def _composition_address(counts: Dict[str, int], charge: int) -> Dict[str, int]:
    """A Golay codeword addressing the composition, derived from it.

    The composition is folded into an index below 4,096 and that index picks
    a codeword, so two molecules with different compositions land on
    codewords at Hamming distance at least 8 unless the fold collided.  The
    fold is a plain positional hash of ``(z, count)`` pairs; it is a
    *summary* and the module says so rather than pretending it is unique.
    """
    index = (charge + 7) % 4096
    for symbol, count in sorted(counts.items()):
        z = element_by_symbol(symbol).z
        index = (index * 131 + z * 37 + count) % 4096
    word = mog.GOLAY_MASKS[index]
    return {
        "index": index,
        "codeword": word,
        "brick0_weight": bin(word & mog.BRICKS[0]).count("1"),
        "brick1_weight": bin(word & mog.BRICKS[1]).count("1"),
        "brick2_weight": bin(word & mog.BRICKS[2]).count("1"),
    }


class MoleculeCodec(Codec):
    """Embed a :class:`Molecule` in ``Q^24`` and read it back exactly."""

    domain = "molecules"
    layout = MOLECULE_LAYOUT

    def encode(self, source: Molecule) -> DataObject:
        carrier: List[Scalar] = []
        mask = 0
        for i, name in enumerate(MOLECULE_FIELDS):
            value = source.field(name)
            if value is None:
                mask |= 1 << i
                carrier.append(0)
            else:
                carrier.append(value)
        carrier.append(mask)
        address = _composition_address(source.counts, source.charge)
        carrier.append(address["codeword"])
        carrier.append(address["brick0_weight"])
        carrier.append(address["brick1_weight"])
        carrier.append(address["brick2_weight"])
        return DataObject(
            name=source.name, domain=self.domain, carrier=carrier,
            attributes={
                "formula": source.formula,
                "composition": dict(sorted(source.counts.items())),
                "charge": source.charge,
                "hill_formula": format_formula(source.counts, source.charge),
                "elements": tuple(sorted(source.counts)),
                "missing_fields": [n for i, n in enumerate(MOLECULE_FIELDS)
                                   if mask >> i & 1],
            },
            layout=MOLECULE_LAYOUT,
            provenance={
                "source": ("name and formula only; every coordinate is "
                           "derived from the element register at load time"),
                "missing_policy": ("a coordinate the element register cannot "
                                   "support is 0 with its bit set in "
                                   "missing_mask; nothing imputed"),
                "representation": ("this is the composite carrier; the "
                                   "faithful representation is the bundle, "
                                   "see molecules.molecule_bundle"),
            },
        )

    def decode(self, obj: DataObject) -> Molecule:
        """Recover the molecule, checking the carrier against its composition."""
        counts = {str(k): int(v)
                  for k, v in obj.attributes["composition"].items()}
        charge = int(obj.attributes["charge"])
        molecule = Molecule(name=obj.name,
                            formula=str(obj.attributes["formula"]),
                            counts=counts, charge=charge)
        mask = int(obj.carrier[19])
        for i, name in enumerate(MOLECULE_FIELDS):
            value = molecule.field(name)
            absent = bool(mask >> i & 1)
            if (value is None) != absent:
                raise ValueError(
                    f"molecules.decode: missingness of {name} on "
                    f"{obj.name!r} disagrees with the element register")
            if value is not None and as_exact(obj.carrier[i]) != value:
                raise ValueError(
                    f"molecules.decode: coordinate {name} of {obj.name!r} "
                    f"disagrees with its composition")
        address = _composition_address(counts, charge)
        if int(obj.carrier[20]) != address["codeword"]:
            raise ValueError(f"molecules.decode: composition address of "
                             f"{obj.name!r} is corrupt")
        return molecule


def molecule_objects() -> Tuple[DataObject, ...]:
    """Every molecule as an encoded :class:`DataObject`."""
    codec = MoleculeCodec()
    return tuple(codec.encode(m) for m in load_molecule_register())


# ===========================================================================
# 5.  THE MULTI-CARRIER
# ===========================================================================

def molecule_bundle(molecule: Molecule) -> Tuple[Tuple[str, int,
                                                       Tuple[Scalar, ...]], ...]:
    """The faithful representation: one element carrier per constituent.

    A molecule is a bundle of its elements with multiplicities.  Nothing is
    summed, so nothing is lost: :func:`formula_from_bundle` reads the
    composition straight back off it.
    """
    from .elements import ElementCodec
    codec = ElementCodec()
    out = []
    for symbol, count in sorted(molecule.counts.items()):
        carrier = codec.encode(element_by_symbol(symbol)).carrier
        out.append((symbol, count, tuple(carrier)))
    return tuple(out)


def formula_from_bundle(bundle: Sequence[Tuple[str, int, Sequence[Scalar]]],
                        charge: int = 0) -> str:
    """Read the formula back off a bundle -- the bundle loses nothing."""
    counts = {symbol: count for symbol, count, _carrier in bundle}
    return format_formula(counts, charge)


def composite_collisions() -> Dict[str, object]:
    """Do two different molecules share one composite carrier?

    The composite is a summary of the bundle, and a summary may collide.
    This checks rather than assumes, on the register as it stands, and
    reports what it finds.
    """
    objects = molecule_objects()
    seen: Dict[Tuple[Scalar, ...], List[str]] = {}
    for obj in objects:
        seen.setdefault(tuple(obj.carrier), []).append(obj.name)
    collisions = tuple(sorted(tuple(sorted(names))
                              for names in seen.values() if len(names) > 1))
    # And the bundle, on the same register.
    bundles: Dict[Tuple, List[str]] = {}
    for molecule in load_molecule_register():
        key = (tuple((s, c) for s, c, _v in molecule_bundle(molecule)),
               molecule.charge)
        bundles.setdefault(key, []).append(molecule.name)
    bundle_collisions = tuple(sorted(tuple(sorted(names))
                                     for names in bundles.values()
                                     if len(names) > 1))
    return {
        "molecules": len(objects),
        "distinct_composites": len(seen),
        "composite_collisions": collisions,
        "composite_collision_count": len(collisions),
        "distinct_bundles": len(bundles),
        "bundle_collisions": bundle_collisions,
        "bundle_collision_count": len(bundle_collisions),
        "bundle_is_faithful": all(
            formula_from_bundle(molecule_bundle(m), m.charge)
            == format_formula(m.counts, m.charge)
            for m in load_molecule_register()),
    }


def molecules_report() -> Dict[str, object]:
    """Everything this module knows, recomputed on call."""
    register = load_molecule_register()
    objects = molecule_objects()
    missing: Dict[str, int] = {}
    for obj in objects:
        for name in obj.attributes["missing_fields"]:
            missing[name] = missing.get(name, 0) + 1
    elements_used = sorted({symbol for molecule in register
                            for symbol in molecule.counts})
    heaviest = max(register, key=lambda m: m.molar_mass_u or Fraction(0))
    most_atoms = max(register, key=lambda m: m.atom_count)
    return {
        "molecules": len(register),
        "distinct_elements_used": len(elements_used),
        "elements_used": tuple(elements_used),
        "largest_by_mass": (heaviest.name, heaviest.molar_mass_u),
        "largest_by_atom_count": (most_atoms.name, most_atoms.atom_count),
        "charged": tuple(m.name for m in register if m.charge),
        "coordinates": len(MOLECULE_LAYOUT),
        "derived_fields": len(MOLECULE_FIELDS),
        "missing_by_field": dict(sorted(missing.items())),
        "collisions": composite_collisions(),
        "method": (
            "The register stores a name and a formula per molecule and "
            "nothing else.  Every coordinate is derived from the element "
            "register when the carrier is built, and a coordinate the "
            "element register cannot support is left absent with its "
            "missingness bit set rather than imputed.  The molecule is "
            "represented twice: as the faithful bundle of its element "
            "carriers with multiplicities, and as one composite carrier "
            "summarising them for the geometry."),
    }
