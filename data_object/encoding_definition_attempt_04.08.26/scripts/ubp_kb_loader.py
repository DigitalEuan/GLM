"""
UBP System KB loader.

Reads /home/z/my-project/upload/ubp_system_kb.json and exposes:

  - ELEMENTS    : dict[symbol] -> ElementEntry (118 entries)
  - MOLECULES   : dict[ubp_id] -> KBEntry (82 entries)
  - REACTIONS   : dict[ubp_id] -> ReactionEntry (22 entries)
  - PARTICLES   : dict[ubp_id] -> KBEntry (32 entries)
  - LAWS        : dict[ubp_id] -> KBEntry (446 entries)
  - ALL         : dict[ubp_id] -> KBEntry (768 entries)

Each entry has:
  - ubp_id        : str
  - lexicon       : str (human description)
  - math          : str (pipe-separated Key=value|Key=value|...)
  - math_dict     : dict[str, Fraction] (parsed math, values are Fractions)
  - atlas         : dict with 'hierarchy', 'vector' (24-bit list), 'nrci', 'nrci_score', 'tax', etc.
  - vector24      : list[int] (24 bits, convenience accessor)
  - tags          : list[str]

For ELEMENTS specifically:
  - symbol        : 'H', 'He', etc. (parsed from ubp_id 'ELEM_H_001')
  - properties    : dict of all 12 physics properties as Fractions
"""

from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Any

KB_PATH = Path(__file__).resolve().parent.parent.parent / "arc_agi_15" / "vendor" / "ubp_system_kb.json"
if not KB_PATH.exists():
    KB_PATH = Path("/home/z/my-project/upload/ubp_system_kb.json")


class KBEntry:
    """A single hardened UBP object from the system KB."""

    def __init__(self, raw: Dict[str, Any]):
        self.ubp_id: str = raw.get("ubp_id", "")
        self.lexicon: str = raw.get("lexicon", "")
        self.math_str: str = raw.get("math", "")
        self.atlas: Dict[str, Any] = raw.get("atlas", {})
        self.tags: List[str] = raw.get("tags", [])
        self.fingerprint: str = raw.get("fingerprint", "")
        self._math_dict: Optional[Dict[str, Any]] = None

    @property
    def math_dict(self) -> Dict[str, Any]:
        """Parse the math string into a dict of Fraction values.

        Values can be:
          - integer: '12' -> Fraction(12)
          - fraction: '507/25' -> Fraction(507, 25)
          - decimal: '2.2' -> Fraction('2.2')
          - signed: '-2' -> Fraction(-2)
          - non-numeric: 'Yes' / 'No' / 'PRIMITIVE' -> kept as string
        """
        if self._math_dict is None:
            self._math_dict = {}
            if self.math_str:
                for pair in self.math_str.split("|"):
                    pair = pair.strip()
                    if "=" not in pair:
                        continue
                    key, _, val = pair.partition("=")
                    key = key.strip()
                    val = val.strip()
                    # Try Fraction first
                    try:
                        self._math_dict[key] = Fraction(val)
                    except (ValueError, ZeroDivisionError):
                        # Try decimal
                        try:
                            self._math_dict[key] = Fraction(val)
                        except (ValueError, ZeroDivisionError):
                            self._math_dict[key] = val
        return self._math_dict

    @property
    def vector24(self) -> List[int]:
        v = self.atlas.get("vector", [])
        return [int(b) & 1 for b in v]

    @property
    def hamming_weight(self) -> int:
        return sum(self.vector24)

    @property
    def nrci_score(self) -> float:
        return float(self.atlas.get("nrci_score", 0.0))

    def __repr__(self):
        return f"KBEntry({self.ubp_id!r}, hw={self.hamming_weight})"


class ElementEntry(KBEntry):
    """An element entry, with convenience accessors for physics properties."""

    ELEMENT_PROPS = [
        "Z", "M", "EN", "Ion", "Valence_e", "Oxidation",
        "BP", "MP", "Rad", "Rho", "Crystal", "Phase_STP",
    ]

    @property
    def symbol(self) -> str:
        # ubp_id format: 'ELEM_H_001' -> 'H'
        parts = self.ubp_id.split("_")
        if len(parts) >= 3:
            return parts[1]
        return ""

    @property
    def properties(self) -> Dict[str, Any]:
        """All 12 element physics properties as Fractions (or strings)."""
        md = self.math_dict
        return {p: md.get(p) for p in self.ELEMENT_PROPS if p in md}


class ReactionEntry(KBEntry):
    """A reaction entry, with parsed reactants/products and ΔH."""

    @property
    def delta_h_kJ(self) -> Optional[float]:
        """Parse 'Value=-483.6kJ' or 'Value=+411kJ' from math field."""
        md = self.math_dict
        if "Value" in md:
            v = md["Value"]
            if isinstance(v, Fraction):
                return float(v)
        # Fallback: regex search the raw math string
        m = re.search(r"Value\s*=\s*(-?\d+\.?\d*)\s*kJ", self.math_str)
        if m:
            return float(m.group(1))
        return None

    @property
    def reaction_type(self) -> Optional[str]:
        m = re.search(r"Type\s*=\s*(\w+)", self.math_str)
        return m.group(1) if m else None

    @property
    def reactants_str(self) -> Optional[str]:
        m = re.search(r"In\s*=\s*([^|]+)", self.math_str)
        return m.group(1).strip() if m else None

    @property
    def products_str(self) -> Optional[str]:
        m = re.search(r"Out\s*=\s*([^|]+)", self.math_str)
        return m.group(1).strip() if m else None

    @property
    def reactant_elements(self) -> List[str]:
        """Parse element symbols from reactant string like '2H2+O2' -> ['H', 'O']."""
        if not self.reactants_str:
            return []
        return self._extract_elements(self.reactants_str)

    @property
    def product_elements(self) -> List[str]:
        if not self.products_str:
            return []
        return self._extract_elements(self.products_str)

    @staticmethod
    def _extract_elements(s: str) -> List[str]:
        """Extract element symbols from a chemical formula string."""
        # Match capital letter optionally followed by lowercase letter
        symbols = re.findall(r"[A-Z][a-z]?", s)
        # Deduplicate while preserving order
        seen = set()
        result = []
        for sym in symbols:
            if sym not in seen:
                seen.add(sym)
                result.append(sym)
        return result


# ──────────────────────────────────────────────────────────────────────────────
# Loader
# ──────────────────────────────────────────────────────────────────────────────

def load_kb() -> Dict[str, KBEntry]:
    """Load the full KB and return a dict of {fingerprint: KBEntry}."""
    with open(KB_PATH) as f:
        raw = json.load(f)
    entries = {}
    for fp, data in raw.items():
        uid = data.get("ubp_id", "")
        if uid.startswith("ELEM_"):
            entries[fp] = ElementEntry(data)
        elif uid.startswith("REACTION_"):
            entries[fp] = ReactionEntry(data)
        else:
            entries[fp] = KBEntry(data)
    return entries


def categorize(entries: Dict[str, KBEntry]) -> Dict[str, Dict[str, KBEntry]]:
    """Split entries into categories by ubp_id prefix."""
    cats: Dict[str, Dict[str, KBEntry]] = {
        "ELEMENTS": {},
        "MOLECULES": {},
        "REACTIONS": {},
        "PARTICLES": {},
        "LAWS": {},
        "OTHER": {},
    }
    for fp, e in entries.items():
        uid = e.ubp_id
        if uid.startswith("ELEM_"):
            cats["ELEMENTS"][uid] = e
        elif uid.startswith("MOLECULE_"):
            cats["MOLECULES"][uid] = e
        elif uid.startswith("REACTION_"):
            cats["REACTIONS"][uid] = e
        elif uid.startswith("PARTICLE_"):
            cats["PARTICLES"][uid] = e
        elif uid.startswith("LAW_"):
            cats["LAWS"][uid] = e
        else:
            cats["OTHER"][uid] = e
    return cats


# ──────────────────────────────────────────────────────────────────────────────
# Module-level singletons (loaded once on import)
# ──────────────────────────────────────────────────────────────────────────────

ALL_ENTRIES = load_kb()
_CATEGORIES = categorize(ALL_ENTRIES)

ELEMENTS: Dict[str, ElementEntry] = {}  # keyed by symbol
for uid, e in _CATEGORIES["ELEMENTS"].items():
    if isinstance(e, ElementEntry):
        ELEMENTS[e.symbol] = e

MOLECULES: Dict[str, KBEntry] = _CATEGORIES["MOLECULES"]
REACTIONS: Dict[str, ReactionEntry] = {
    uid: e for uid, e in _CATEGORIES["REACTIONS"].items() if isinstance(e, ReactionEntry)
}
PARTICLES: Dict[str, KBEntry] = _CATEGORIES["PARTICLES"]
LAWS: Dict[str, KBEntry] = _CATEGORIES["LAWS"]


def get_element(symbol: str) -> Optional[ElementEntry]:
    return ELEMENTS.get(symbol)


def get_entry(uid: str) -> Optional[KBEntry]:
    """Look up any entry by ubp_id."""
    for e in ALL_ENTRIES.values():
        if e.ubp_id == uid:
            return e
    return None


if __name__ == "__main__":
    print(f"Total KB entries: {len(ALL_ENTRIES)}")
    print(f"  Elements:   {len(ELEMENTS)}")
    print(f"  Molecules:  {len(MOLECULES)}")
    print(f"  Reactions:  {len(REACTIONS)}")
    print(f"  Particles:  {len(PARTICLES)}")
    print(f"  Laws:       {len(LAWS)}")
    print()
    print("Sample element (C):")
    c = get_element("C")
    if c:
        print(f"  ubp_id: {c.ubp_id}")
        print(f"  vector: {c.vector24}")
        print(f"  HW:     {c.hamming_weight}")
        print(f"  props:  {c.properties}")
    print()
    print("Sample reaction (H2O form):")
    for uid, r in REACTIONS.items():
        if "H2O" in uid:
            print(f"  ubp_id: {r.ubp_id}")
            print(f"  ΔH:     {r.delta_h_kJ} kJ")
            print(f"  type:   {r.reaction_type}")
            print(f"  react:  {r.reactants_str} -> {r.products_str}")
            print(f"  elems:  reactant={r.reactant_elements} product={r.product_elements}")
            print(f"  vector: {r.vector24}")
            break
