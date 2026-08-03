"""
kb_adapter.py — Adapter for the list-format UBP System KB.

The actual ubp_system_kb.json stores entries as lists:
  [ubp_id, lexicon, tags, vector, nrci_str, nrci_val, tax_str, mog_tensor]

This adapter parses element physics properties from the lexicon text
and provides a clean interface for the encoding training loop.
"""

from __future__ import annotations
import json, re, os
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Any

KB_PATH = Path(__file__).resolve().parent.parent.parent / "arc_agi_15" / "vendor" / "ubp_system_kb.json"
if not KB_PATH.exists():
    # Fallback
    KB_PATH = Path("/home/z/my-project/upload/ubp_system_kb.json")


class Element:
    """An element parsed from the KB."""

    def __init__(self, ubp_id: str, lexicon: str, tags: List[str],
                 vector: List[int], nrci_val: float, mog_tensor: list):
        self.ubp_id = ubp_id
        self.lexicon = lexicon
        self.tags = tags
        self.vector = vector
        self.nrci_val = nrci_val
        self.mog_tensor = mog_tensor

        # Parse symbol from ubp_id: 'ELEM_H_001' -> 'H'
        parts = ubp_id.split("_")
        self.symbol = parts[1] if len(parts) >= 3 else ""

        # Parse physics properties from lexicon
        self.properties = self._parse_properties()

    def _parse_properties(self) -> Dict[str, Any]:
        """Parse physics properties from lexicon text AND mog_tensor."""
        props = {}
        text = self.lexicon

        # Z (atomic number)
        m = re.search(r'Z=(\d+)', text)
        if m:
            props['Z'] = Fraction(int(m.group(1)))

        # Valence
        m = re.search(r'Valence\s+(\d+)', text)
        if m:
            props['Valence_e'] = Fraction(int(m.group(1)))

        # Tension
        m = re.search(r'Tension:\s+(\d+)', text)
        if m:
            props['Tension'] = Fraction(int(m.group(1)))

        # From mog_tensor (structured physics data):
        # [0] = atomic mass M
        # [4] = [BP, MP] (boiling point, melting point in K)
        # [5] = [Z] (atomic number, same as lexicon)
        # [8] = [?, density] (second value is density)
        mog = self.mog_tensor
        if isinstance(mog, list) and len(mog) > 8:
            # Mass from mog_tensor[0]
            if isinstance(mog[0], list) and len(mog[0]) > 0:
                try:
                    val = mog[0][0]
                    if isinstance(val, str):
                        props['M'] = Fraction(val)
                    elif isinstance(val, (int, float)):
                        props['M'] = Fraction(val).limit_denominator(1000)
                except (ValueError, ZeroDivisionError):
                    pass

            # BP and MP from mog_tensor[4]
            if isinstance(mog[4], list) and len(mog[4]) >= 2:
                try:
                    bp_val = mog[4][0]
                    mp_val = mog[4][1]
                    if isinstance(bp_val, str):
                        props['BP'] = Fraction(bp_val)
                    elif isinstance(bp_val, (int, float)):
                        props['BP'] = Fraction(bp_val).limit_denominator(100)
                    if isinstance(mp_val, str):
                        props['MP'] = Fraction(mp_val)
                    elif isinstance(mp_val, (int, float)):
                        props['MP'] = Fraction(mp_val).limit_denominator(100)
                except (ValueError, ZeroDivisionError):
                    pass

            # Z from mog_tensor[5] (redundant with lexicon but useful)
            if isinstance(mog[5], list) and len(mog[5]) > 0:
                try:
                    val = mog[5][0]
                    if isinstance(val, str) and 'Z' not in props:
                        props['Z'] = Fraction(val)
                except (ValueError, ZeroDivisionError):
                    pass

            # Density from mog_tensor[8] (second value)
            if isinstance(mog[8], list) and len(mog[8]) >= 2:
                try:
                    val = mog[8][1]
                    if isinstance(val, str):
                        props['Rho'] = Fraction(val)
                    elif isinstance(val, (int, float)):
                        props['Rho'] = Fraction(val).limit_denominator(1000)
                except (ValueError, ZeroDivisionError):
                    pass

        # Electronegativity — try standard values for common elements
        EN_TABLE = {
            'H': Fraction(220, 100), 'He': 0, 'Li': Fraction(98, 100),
            'Be': Fraction(157, 100), 'B': Fraction(204, 100), 'C': Fraction(255, 100),
            'N': Fraction(304, 100), 'O': Fraction(344, 100), 'F': Fraction(398, 100),
            'Ne': 0, 'Na': Fraction(93, 100), 'Mg': Fraction(131, 100),
            'Al': Fraction(161, 100), 'Si': Fraction(190, 100), 'P': Fraction(219, 100),
            'S': Fraction(258, 100), 'Cl': Fraction(316, 100), 'Ar': 0,
            'K': Fraction(82, 100), 'Ca': Fraction(100, 100), 'Sc': Fraction(136, 100),
            'Ti': Fraction(154, 100), 'V': Fraction(163, 100), 'Cr': Fraction(166, 100),
            'Mn': Fraction(155, 100), 'Fe': Fraction(183, 100), 'Co': Fraction(188, 100),
            'Ni': Fraction(191, 100), 'Cu': Fraction(190, 100), 'Zn': Fraction(165, 100),
            'Ga': Fraction(181, 100), 'Ge': Fraction(201, 100), 'As': Fraction(218, 100),
            'Se': Fraction(255, 100), 'Br': Fraction(296, 100), 'Kr': Fraction(300, 100),
            'Rb': Fraction(82, 100), 'Sr': Fraction(95, 100), 'Ag': Fraction(193, 100),
            'I': Fraction(266, 100), 'Ba': Fraction(89, 100), 'Au': Fraction(254, 100),
            'Pt': Fraction(228, 100), 'Pb': Fraction(233, 100), 'Hg': Fraction(200, 100),
        }
        if self.symbol in EN_TABLE:
            props['EN'] = EN_TABLE[self.symbol]

        # Radius — try standard covalent radii (pm)
        RAD_TABLE = {
            'H': Fraction(31), 'He': Fraction(28), 'Li': Fraction(128),
            'Be': Fraction(96), 'B': Fraction(84), 'C': Fraction(76),
            'N': Fraction(71), 'O': Fraction(66), 'F': Fraction(57),
            'Ne': Fraction(58), 'Na': Fraction(166), 'Mg': Fraction(141),
            'Al': Fraction(121), 'Si': Fraction(111), 'P': Fraction(107),
            'S': Fraction(105), 'Cl': Fraction(102), 'Ar': Fraction(106),
            'K': Fraction(203), 'Ca': Fraction(176), 'Fe': Fraction(132),
            'Cu': Fraction(132), 'Zn': Fraction(122), 'Br': Fraction(120),
            'Ag': Fraction(145), 'Au': Fraction(136), 'I': Fraction(139),
            'Pt': Fraction(136), 'Pb': Fraction(146),
        }
        if self.symbol in RAD_TABLE:
            props['Rad'] = RAD_TABLE[self.symbol]

        return props

    @property
    def hamming_weight(self) -> int:
        return sum(self.vector)


def load_elements() -> Dict[str, Element]:
    """Load all elements from the KB."""
    with open(KB_PATH) as f:
        raw = json.load(f)

    entries = raw.get("entries", raw)
    elements = {}

    for fp, data in entries.items():
        if not isinstance(data, list) or len(data) < 8:
            continue
        uid = data[0]
        if not uid.startswith("ELEM_"):
            continue

        elem = Element(
            ubp_id=uid,
            lexicon=data[1],
            tags=data[2],
            vector=[int(b) & 1 for b in data[3]],
            nrci_val=float(data[5]) if data[5] else 0.0,
            mog_tensor=data[7],
        )
        # Don't overwrite if we already have this symbol (prefer first entry)
        if elem.symbol not in elements:
            elements[elem.symbol] = elem

    return elements


# Known chemistry pairs: (symbol_a, symbol_b, bond_energy_kJ, delta_H_kJ, label)
# From the E1-E2-E3 study
KNOWN_PAIRS = [
    ("H", "H", 436, None, "H-H covalent"),
    ("H", "O", 463, -241.8, "H-O water"),
    ("H", "F", 568, None, "H-F HF"),
    ("H", "Cl", 431, -92.3, "H-C1 HCl"),
    ("H", "N", 391, None, "H-N ammonia"),
    ("H", "C", 413, -74.8, "H-C methane"),
    ("O", "O", 498, None, "O=O oxygen"),
    ("O", "O", 146, None, "O-O peroxide"),
    ("N", "N", 946, None, "N≡N nitrogen"),
    ("N", "N", 163, None, "N-N hydrazine"),
    ("C", "O", 358, None, "C-O methanol"),
    ("C", "O", 799, None, "C=O CO2"),
    ("C", "C", 347, None, "C-C ethane"),
    ("C", "C", 614, None, "C=C ethylene"),
    ("C", "C", 839, None, "C≡C acetylene"),
    ("C", "N", 305, None, "C-N methylamine"),
    ("C", "N", 615, None, "C=N formaldehyde-oxime"),
    ("C", "N", 891, None, "C≡N HCN"),
    ("C", "F", 485, None, "C-F fluoromethane"),
    ("C", "Cl", 339, None, "C-Cl chloromethane"),
    ("C", "Br", 276, None, "C-Br bromomethane"),
    ("C", "I", 238, None, "C-I iodomethane"),
    ("C", "S", 259, None, "C-S methanethiol"),
    ("Si", "O", 452, None, "Si-O silica"),
    ("Si", "Si", 226, None, "Si-Si disilane"),
    ("P", "O", 335, None, "P-O phosphate"),
    ("S", "O", 265, None, "S-O SO2"),
    ("S", "H", 363, None, "S-H H2S"),
    ("Na", "Cl", 411, -411.2, "NaCl salt"),
    ("K", "Cl", 427, -436.5, "KCl"),
    ("Li", "F", 577, -616.0, "LiF"),
    ("Mg", "O", 394, -601.6, "MgO"),
    ("Ca", "O", 402, -635.1, "CaO"),
    ("Al", "O", 512, -1675.7, "Al2O3"),
    ("Fe", "O", 407, -824.2, "Fe2O3"),
    ("Fe", "S", 310, None, "FeS"),
    ("Cu", "S", 274, None, "CuS"),
    ("Zn", "O", 284, None, "ZnO"),
]


# Singleton
_ELEMENTS: Optional[Dict[str, Element]] = None
_MOLECULES: Optional[Dict[str, 'Molecule']] = None


class Molecule:
    """A molecule parsed from the KB."""

    def __init__(self, ubp_id: str, lexicon: str, tags: List[str],
                 vector: List[int], nrci_val: float, mog_tensor: list):
        self.ubp_id = ubp_id
        self.lexicon = lexicon
        self.tags = tags
        self.vector = vector
        self.nrci_val = nrci_val
        self.mog_tensor = mog_tensor

        # Parse name from ubp_id: 'MOLECULE_H2O_001' -> 'H2O'
        parts = ubp_id.split("_")
        self.name = "_".join(parts[1:-1]) if len(parts) >= 3 else ubp_id

        # Parse physics properties from mog_tensor and lexicon
        self.properties = self._parse_properties()

    def _parse_properties(self) -> Dict[str, Any]:
        props = {}
        mog = self.mog_tensor
        if isinstance(mog, list) and len(mog) > 8:
            # Mass from mog_tensor[0]
            if isinstance(mog[0], list) and len(mog[0]) > 0:
                try:
                    val = mog[0][0]
                    if isinstance(val, str):
                        props['M'] = Fraction(val)
                    elif isinstance(val, (int, float)):
                        props['M'] = Fraction(val).limit_denominator(1000)
                except (ValueError, ZeroDivisionError):
                    pass
            # BP and MP from mog_tensor[4]
            if isinstance(mog[4], list) and len(mog[4]) >= 2:
                try:
                    bp_val = mog[4][0]
                    mp_val = mog[4][1]
                    if isinstance(bp_val, str):
                        props['BP'] = Fraction(bp_val)
                    elif isinstance(bp_val, (int, float)):
                        props['BP'] = Fraction(bp_val).limit_denominator(100)
                    if isinstance(mp_val, str):
                        props['MP'] = Fraction(mp_val)
                    elif isinstance(mp_val, (int, float)):
                        props['MP'] = Fraction(mp_val).limit_denominator(100)
                except (ValueError, ZeroDivisionError):
                    pass
            # Density from mog_tensor[8]
            if isinstance(mog[8], list) and len(mog[8]) >= 2:
                try:
                    val = mog[8][1]
                    if isinstance(val, str) and val != '0':
                        props['Rho'] = Fraction(val)
                    elif isinstance(val, (int, float)) and val != 0:
                        props['Rho'] = Fraction(val).limit_denominator(1000)
                except (ValueError, ZeroDivisionError):
                    pass
            # Electron count from mog_tensor[5] (if present)
            if isinstance(mog[5], list) and len(mog[5]) > 0:
                try:
                    val = mog[5][0]
                    if isinstance(val, str):
                        props['Electrons'] = Fraction(val)
                except (ValueError, ZeroDivisionError):
                    pass

        # Parse formula weight from lexicon if mog_tensor doesn't have it
        import re
        m = re.search(r'(?:MW|Molecular\s+weight)[:\s]+(\d+\.?\d*)', self.lexicon, re.IGNORECASE)
        if m and 'M' not in props:
            props['M'] = Fraction(m.group(1))

        return props

    @property
    def hamming_weight(self) -> int:
        return sum(self.vector)


def load_molecules() -> Dict[str, Molecule]:
    """Load all molecules from the KB."""
    with open(KB_PATH) as f:
        raw = json.load(f)
    entries = raw.get("entries", raw)
    molecules = {}
    for fp, data in entries.items():
        if not isinstance(data, list) or len(data) < 8:
            continue
        uid = data[0]
        if not uid.startswith("MOLECULE_"):
            continue
        mol = Molecule(
            ubp_id=uid,
            lexicon=data[1],
            tags=data[2],
            vector=[int(b) & 1 for b in data[3]],
            nrci_val=float(data[5]) if data[5] else 0.0,
            mog_tensor=data[7],
        )
        molecules[mol.name] = mol
    return molecules


def get_molecule(name: str) -> Optional[Molecule]:
    global _MOLECULES
    if _MOLECULES is None:
        _MOLECULES = load_molecules()
    return _MOLECULES.get(name)


def get_all_molecules() -> Dict[str, Molecule]:
    global _MOLECULES
    if _MOLECULES is None:
        _MOLECULES = load_molecules()
    return _MOLECULES


# Known molecule pairs for chemistry prediction
# (mol_a, mol_b, interaction_type, known_value, label)
MOLECULE_PAIRS = [
    # Combustion reactions (kJ/mol)
    ("H2O", "H2O", "formation", -285.8, "Water formation"),
    ("CO2", "H2O", "formation", -393.5, "CO2 formation"),
    ("METHANE", "OXYGEN", "combustion", -890.4, "CH4 combustion"),
    ("ETHANOL", "OXYGEN", "combustion", -1367.0, "Ethanol combustion"),
    ("GLUCOSE", "OXYGEN", "combustion", -2803.0, "Glucose combustion"),
    # Acid-base
    ("HYDROCHLORIC", "WATER", "dissolution", -75.1, "HCl dissolution"),
    ("AMMONIA", "WATER", "dissolution", -30.5, "NH3 dissolution"),
    # Bond energies (kJ/mol) for molecule-internal bonds
    # We can also treat molecule pairs as interaction tests
]

# Molecule bond energies (kJ/mol) - bonds within molecules
MOLECULE_BOND_ENERGIES = [
    ("H2O", "O-H", 463, "Water O-H bond"),
    ("METHANE", "C-H", 413, "Methane C-H bond"),
    ("AMMONIA", "N-H", 391, "Ammonia N-H bond"),
    ("HYDROCHLORIC", "H-Cl", 431, "HCl bond"),
    ("ETHANOL", "C-C", 347, "Ethanol C-C bond"),
    ("ETHANOL", "C-O", 358, "Ethanol C-O bond"),
    ("ETHANOL", "O-H", 463, "Ethanol O-H bond"),
    ("BENZENE", "C-C", 518, "Benzene C-C (aromatic)"),
    ("BENZENE", "C-H", 413, "Benzene C-H bond"),
    ("ACETYLENE", "C≡C", 839, "Acetylene C≡C bond"),
    ("ACETYLENE", "C-H", 556, "Acetylene C-H bond"),
]

# Molecule-molecule interaction pairs
MOLECULE_PAIRS = [
    # Formation enthalpies (kJ/mol)
    ("H2O", "H2O", "formation", -285.8, "Water formation"),
    ("CO2", "H2O", "formation", -393.5, "CO2 formation"),
    ("METHANE", "OXYGEN", "combustion", -890.4, "CH4 combustion"),
    ("ETHANOL", "OXYGEN", "combustion", -1367.0, "Ethanol combustion"),
    ("GLUCOSE", "OXYGEN", "combustion", -2803.0, "Glucose combustion"),
    ("HYDROCHLORIC", "WATER", "dissolution", -75.1, "HCl dissolution"),
    ("AMMONIA", "WATER", "dissolution", -30.5, "NH3 dissolution"),
    # DNA base pair hydrogen bonds
    ("ADENINE", "THYMINE", "h_bond", -12.0, "A-T H-bond"),
    ("GUANINE", "CYTOSINE", "h_bond", -17.0, "G-C H-bond"),
]

def get_element(symbol: str) -> Optional[Element]:
    global _ELEMENTS
    if _ELEMENTS is None:
        _ELEMENTS = load_elements()
    return _ELEMENTS.get(symbol)

def get_all_elements() -> Dict[str, Element]:
    global _ELEMENTS
    if _ELEMENTS is None:
        _ELEMENTS = load_elements()
    return _ELEMENTS


if __name__ == "__main__":
    elems = load_elements()
    print(f"Loaded {len(elems)} elements")
    for sym in ["H", "He", "Li", "C", "N", "O", "Fe", "Au", "U"]:
        e = elems.get(sym)
        if e:
            print(f"  {sym}: Z={e.properties.get('Z', '?')} "
                  f"EN={e.properties.get('EN', '?')} "
                  f"Rad={e.properties.get('Rad', '?')} "
                  f"Val={e.properties.get('Valence_e', '?')} "
                  f"vector_hw={e.hamming_weight}")
