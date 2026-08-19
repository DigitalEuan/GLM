#!/usr/bin/env python3
"""
GLM Elements — 119 elements from the UBP knowledge base.

Elements are substances, not quantities. They don't have dimensional
exponents like energy (L²MT⁻²). Instead, they have PROPERTIES that
are physics quantities:
  - mass (M)
  - boiling_point (H)
  - melting_point (H)
  - electronegativity (dimensionless)
  - density (ML⁻³)
  - ionization_energy (L²MT⁻²)
  - valence (dimensionless)
  - phase at STP (dimensionless)

The element's carrier is its 24-bit Golay codeword from the UBP KB.
This is NOT derived from dimensional exponents — it's the element's
address in the Leech lattice, computed from its physical properties.

Usage:
    from elements import ElementStore
    store = ElementStore()
    h = store.get('hydrogen')
    print(h['symbol'], h['z'], h['mass'])
    print(h['vector'])  # 24-bit Golay codeword
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from fractions import Fraction as F

_KB_PATH = Path(__file__).resolve().parent.parent / "long_term_memory" / "ubp_system_kb.json"


def _sf(v) -> Optional[float]:
    """Safely convert a value to float."""
    if v is None or v == 0 or v == '0':
        return None
    try:
        return float(F(v))
    except Exception:
        return None


class ElementStore:
    """
    Loads and provides access to 119 elements from the UBP KB.

    Each element has:
      - symbol, z, mass, bp, mp, en, valence, rho, phase, tension
      - vector: 24-bit Golay codeword (the element's Leech lattice address)
      - nrci: Non-Random Coherence Index
      - tags: classification tags from the KB
    """

    def __init__(self, kb_path: Optional[Path] = None):
        self._elements: Dict[str, Dict] = {}
        self._by_symbol: Dict[str, str] = {}  # symbol → name
        self._by_z: Dict[int, str] = {}        # z → name
        self._load(kb_path or _KB_PATH)

    def _load(self, kb_path: Path):
        """Load elements from the UBP knowledge base."""
        if not kb_path.exists():
            print(f"[elements] KB not found: {kb_path}")
            return

        with open(kb_path) as f:
            kb = json.load(f)

        entries = kb.get('entries', {})
        count = 0

        for key, val in entries.items():
            if not isinstance(val, list) or len(val) < 2:
                continue
            lex = str(val[1])
            if 'Element:' not in lex:
                continue

            # Parse name and symbol from lexicon
            m = re.match(r'\[Element:\s*(\w+)\s*\((\w+)\)\]', lex)
            if not m:
                continue
            name = m.group(1).lower()
            symbol = m.group(2)

            # Parse Z from lexicon
            z_match = re.search(r'Z=(\d+)', lex)
            z = int(z_match.group(1)) if z_match else None

            # Parse valence from lexicon
            val_match = re.search(r'Valence\s+(\d+)', lex)
            valence = int(val_match.group(1)) if val_match else None

            # Parse phase from lexicon
            phase_match = re.search(r'Phase\s+(\d+)', lex)
            phase = int(phase_match.group(1)) if phase_match else None

            # Parse tension from lexicon
            tension_match = re.search(r'Tension:\s*([\d/]+)', lex)
            tension = tension_match.group(1) if tension_match else None

            # Parse potential from lexicon
            pot_match = re.search(r'with\s+(\w+)\s+potential', lex)
            potential = pot_match.group(1) if pot_match else None

            # Extract properties from mog_tensor
            tensor = val[7] if len(val) > 7 else None
            mass = _sf(tensor[0][0]) if isinstance(tensor, list) and isinstance(tensor[0], list) and tensor[0][0] else None
            bp = _sf(tensor[4][0]) if isinstance(tensor, list) and len(tensor) > 4 and isinstance(tensor[4], list) and tensor[4][0] else None
            mp = _sf(tensor[4][1]) if isinstance(tensor, list) and len(tensor) > 4 and isinstance(tensor[4], list) and len(tensor[4]) > 1 and tensor[4][1] else None
            rho = _sf(tensor[8][1]) if isinstance(tensor, list) and len(tensor) > 8 and isinstance(tensor[8], list) and len(tensor[8]) > 1 and tensor[8][1] else None
            en = _sf(tensor[11][232]) if isinstance(tensor, list) and len(tensor) > 11 and isinstance(tensor[11], list) and len(tensor[11]) > 232 and tensor[11][232] else None
            ie = _sf(tensor[11][490]) if isinstance(tensor, list) and len(tensor) > 11 and isinstance(tensor[11], list) and len(tensor[11]) > 490 and tensor[11][490] else None

            # Get the 24-bit vector
            vector = val[3] if len(val) > 3 and isinstance(val[3], list) else None

            # Get NRCI
            nrci = _sf(val[5]) if len(val) > 5 else None

            # Get tags
            tags = val[6] if len(val) > 6 and isinstance(val[6], list) else []

            element = {
                'name': name,
                'symbol': symbol,
                'z': z,
                'mass': mass,
                'bp': bp,
                'mp': mp,
                'en': en,
                'valence': valence,
                'rho': rho,
                'ie': ie,
                'phase': phase,
                'tension': tension,
                'potential': potential,
                'vector': vector,
                'nrci': nrci,
                'tags': tags,
            }

            self._elements[name] = element
            if symbol:
                self._by_symbol[symbol] = name
            if z:
                self._by_z[z] = name
            count += 1

    # ── Access ──────────────────────────────────────────────────────

    def get(self, name_or_symbol: str) -> Optional[Dict]:
        """Get an element by name or symbol."""
        name = name_or_symbol.lower()
        if name in self._elements:
            return self._elements[name]
        # Try symbol
        if name_or_symbol in self._by_symbol:
            return self._elements[self._by_symbol[name_or_symbol]]
        return None

    def get_by_z(self, z: int) -> Optional[Dict]:
        """Get an element by atomic number."""
        if z in self._by_z:
            return self._elements[self._by_z[z]]
        return None

    def list_elements(self) -> List[str]:
        """List all element names."""
        return sorted(self._elements.keys())

    def count(self) -> int:
        return len(self._elements)

    # ── Queries ─────────────────────────────────────────────────────

    def by_property(self, prop: str, min_val: float = None,
                    max_val: float = None) -> List[Dict]:
        """Find elements by property range."""
        results = []
        for e in self._elements.values():
            val = e.get(prop)
            if val is None:
                continue
            if min_val is not None and val < min_val:
                continue
            if max_val is not None and val > max_val:
                continue
            results.append(e)
        return sorted(results, key=lambda x: x.get(prop, 0))

    def noble_gases(self) -> List[Dict]:
        """List noble gases (valence = 8 or 2 for He)."""
        return [e for e in self._elements.values()
                if 'NOBLE_GAS' in e.get('tags', [])]

    def metals(self) -> List[Dict]:
        """List metals."""
        return [e for e in self._elements.values()
                if any('METAL' in t and 'NONMETAL' not in t
                       for t in e.get('tags', []))]

    def nonmetals(self) -> List[Dict]:
        """List nonmetals."""
        return [e for e in self._elements.values()
                if 'NONMETAL' in e.get('tags', [])]

    def transition_metals(self) -> List[Dict]:
        """List transition metals."""
        return [e for e in self._elements.values()
                if 'TRANSITION_METAL' in e.get('tags', [])]

    # ── Periodic table relationships ────────────────────────────────

    def period(self, z: int) -> int:
        """Get the period of an element."""
        if z <= 2: return 1
        if z <= 10: return 2
        if z <= 18: return 3
        if z <= 36: return 4
        if z <= 54: return 5
        if z <= 86: return 6
        return 7

    def group(self, z: int) -> Optional[int]:
        """Get the group of an element (approximate)."""
        # Simplified group assignment
        groups = {
            1: 1, 2: 18,
            3: 1, 4: 2, 5: 13, 6: 14, 7: 15, 8: 16, 9: 17, 10: 18,
            11: 1, 12: 2, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18,
            19: 1, 20: 2, 21: 3, 22: 4, 23: 5, 24: 6, 25: 7, 26: 8,
            27: 9, 28: 10, 29: 11, 30: 12, 31: 13, 32: 14, 33: 15,
            34: 16, 35: 17, 36: 18,
        }
        return groups.get(z)

    def is_halogen(self, z: int) -> bool:
        return z in (9, 17, 35, 53, 85)

    def is_alkali(self, z: int) -> bool:
        return z in (3, 11, 19, 37, 55, 87)

    def is_alkaline_earth(self, z: int) -> bool:
        return z in (4, 12, 20, 38, 56, 88)

    # ── Relationships to physics quantities ─────────────────────────

    def relates_to(self, name: str) -> List[Tuple[str, str, str]]:
        """
        Get relationships between an element and physics quantities.

        Returns list of (element, relationship, quantity) tuples.
        """
        e = self.get(name)
        if not e:
            return []

        rels = []
        if e['mass'] is not None:
            rels.append((e['name'], 'has_mass', f"{e['mass']} u"))
        if e['en'] is not None:
            rels.append((e['name'], 'has_electronegativity', str(e['en'])))
        if e['bp'] is not None:
            rels.append((e['name'], 'has_boiling_point', f"{e['bp']} K"))
        if e['mp'] is not None:
            rels.append((e['name'], 'has_melting_point', f"{e['mp']} K"))
        if e['rho'] is not None:
            rels.append((e['name'], 'has_density', f"{e['rho']} kg/m³"))
        if e['valence'] is not None:
            rels.append((e['name'], 'has_valence', str(e['valence'])))
        if e['phase'] is not None:
            phase_names = {1: 'gas', 2: 'liquid', 3: 'solid'}
            rels.append((e['name'], 'is_phase', phase_names.get(e['phase'], str(e['phase']))))
        return rels

    # ── Comparison ──────────────────────────────────────────────────

    def compare(self, a: str, b: str) -> Dict[str, Any]:
        """Compare two elements by their properties."""
        ea = self.get(a)
        eb = self.get(b)
        if not ea or not eb:
            return {"error": f"Unknown element: {a if not ea else b}"}

        result = {"elements": [ea['name'], eb['name']], "differences": {}}
        for prop in ['mass', 'bp', 'mp', 'en', 'rho', 'valence', 'z']:
            va = ea.get(prop)
            vb = eb.get(prop)
            if va is not None and vb is not None:
                result["differences"][prop] = {
                    ea['name']: va,
                    eb['name']: vb,
                    "diff": round(va - vb, 4),
                }
        return result

    # ── String representation ───────────────────────────────────────

    def describe(self, name: str) -> str:
        """Get a human-readable description of an element."""
        e = self.get(name)
        if not e:
            return f"Unknown element: {name}"

        lines = [f"{e['name'].title()} ({e['symbol']})"]
        lines.append(f"  Atomic number: {e['z']}")
        if e['mass']: lines.append(f"  Atomic mass: {e['mass']:.3f} u")
        if e['en']: lines.append(f"  Electronegativity: {e['en']:.2f}")
        if e['bp']: lines.append(f"  Boiling point: {e['bp']:.2f} K")
        if e['mp']: lines.append(f"  Melting point: {e['mp']:.2f} K")
        if e['rho']: lines.append(f"  Density: {e['rho']:.4f} kg/m³")
        if e['valence']: lines.append(f"  Valence: {e['valence']}")
        phase_names = {1: 'Gas', 2: 'Liquid', 3: 'Solid'}
        if e['phase']: lines.append(f"  Phase (STP): {phase_names.get(e['phase'], '?')}")
        if e['potential']: lines.append(f"  Crystal potential: {e['potential']}")
        if e['vector']:
            hw = sum(e['vector'])
            lines.append(f"  Carrier: HW={hw} (24-bit Golay codeword)")
        if e['nrci']: lines.append(f"  NRCI: {e['nrci']:.6f}")
        return "\n".join(lines)
