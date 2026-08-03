"""UBP Condensed Module: geometry"""

from ubp_unified_v5 import BinaryLinearAlgebra, GOLAY_ENGINE
from ubp_unified_v5 import LEECH_ENGINE, GOLAY_ENGINE, BinaryLinearAlgebra, SUBSTRATE

# --- Extracted from hex_dictionary_v4_exact.py ---
"""
UBP HexDictionary v4.8 (Spatial-Deterministic Edition)
=====================================================
Identity is derived from TOPOLOGY. 
The 'math' field is treated as a 3D Voxel Structure.
The Vector is a measurement of that structure's Volume and Compactness.

STANDARDS:
1. Domain: Bits 0-2 (Prefix)
2. Volume: Bits 3-7 (Voxel Count, Gray Coded)
3. Compactness: Bits 8-11 (Surface Area Proxy, Gray Coded)
4. Parity: Bits 12-23 (Golay [24,12,8])

Author: Euan R A Craig & UBP Research Cortex v4.2.7
Date: 28 Feb 2026
"""
import json
import os
import re
import math
from typing import Dict, List, Optional, Any, Tuple
from fractions import Fraction
try:
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

class HexDictionaryV4Exact:
    DOMAINS = {'QUANTITY': 0, 'SUBSTANCE': 1, 'MECHANISM': 2, 'ALGORITHM': 3, 'ORGANISM': 4, 'IMPERATIVE': 5, 'ENTROPY': 6, 'MEANING': 7}

    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.id_map: Dict[str, str] = {}
        self.vector_cache: Dict[str, List[int]] = {}

    def _int_to_gray(self, n: int, bits: int) -> List[int]:
        """Gray code ensures that similar volumes have similar bit-patterns."""
        n = int(n) % 2 ** bits
        gray = n ^ n >> 1
        return [gray >> i & 1 for i in range(bits - 1, -1, -1)]

    def _get_domain_for_id(self, ubp_id: str) -> int:
        uid = ubp_id.upper()
        if uid.startswith(('NUM_', 'CONST_', 'MATH_', 'GEO_')):
            return 0
        if uid.startswith(('ELEM_', 'CHEM_', 'MAT_', 'CRYSTAL_')):
            return 1
        if uid.startswith(('PHYS_', 'MECH_', 'PARTICLE_', 'FORCE_')):
            return 2
        if uid.startswith(('PY_', 'CODE_', 'ALGO_', 'DS_', 'BITOP_')):
            return 3
        if uid.startswith(('BIO_', 'CELL_', 'PSYCH_', 'MOLECULE_')):
            return 4
        if uid.startswith(('LAW_', 'ACTION_', 'STATE_', 'IMPERATIVE_')):
            return 5
        if uid.startswith(('PATTERN_', 'TRANSFORM_', 'NOISE_')):
            return 6
        return 7

    def _measure_topology(self, math_dna: str) -> Tuple[int, int]:
        """
        SYMBOLIC HASHING:
        Turns the math string into a Voxel Count (Volume) 
        and a 'Complexity' score (Compactness).
        """
        if not math_dna or math_dna in ['atomic', 'absolute_primitive']:
            return (1, 0)
        numbers = re.findall('[-+]?\\d*\\.\\d+|\\d+', math_dna)
        volume = sum((abs(float(n)) for n in numbers))
        prop_count = math_dna.count('|') + 1
        compactness = int(prop_count * 100 / (volume if volume > 0 else 1))
        return (int(volume), int(compactness))

    def mint_rational_vector(self, ubp_id: str, math_dna: str) -> List[int]:
        """
        PROJECTS a vector from the SPATIAL properties of the math.
        [FIX ISSUE 2] Enforces the Domain Pivot on Bit 12 (Index 11).
        """
        dom_val = self._get_domain_for_id(ubp_id)
        
        # Measure topology for payload
        volume, compactness = self._measure_topology(math_dna)
        
        # We need 11 bits for payload to leave room for the 1-bit pivot
        # Let's use 6 bits for volume and 5 bits for compactness
        p1_bits = self._int_to_gray(volume, 6)
        p2_bits = self._int_to_gray(compactness, 5)
        payload_bits = p1_bits + p2_bits
        
        # Force the Domain Pivot to Bit 12 (Index 11)
        # 1: Phenomenal (Matter/Substance/Organism/Mechanism/Algorithm)
        # 0: Noumenal (Quantity/Imperative/Entropy/Meaning)
        is_phenomenal = 1 if dom_val in [1, 2, 3, 4] else 0
        
        message = payload_bits[:11] + [is_phenomenal]
        
        if CORE_AVAILABLE:
            return GOLAY_ENGINE.encode(message)
        return message + [0] * 12

    def load_memory(self, filepath: str='ubp_system_kb.json'):
        # MIGRATION v4.0: locate the merged v9.9 KB if the legacy filename
        # doesn't exist. Prefer the in-memory adapter when possible.
        import sys as _sys
        if not filepath or not os.path.exists(filepath):
            # Try the adapter's merged v9.9 file
            here = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(here, '..', 'system_kb', 'ubp_system_kb_v4_merged.json'),
                os.path.join('system_kb', 'ubp_system_kb_v4_merged.json'),
                'ubp_system_kb_v4_merged.json',
            ]
            found = next((c for c in candidates if c and os.path.exists(c)), None)
            if found:
                filepath = found
            else:
                # Try to materialise via the adapter
                try:
                    _sys.path.insert(0, os.path.join(here, '..', 'system_kb'))
                    from legacy_adapter import ensure_legacy_kb_on_disk as _ensure
                    filepath = str(_ensure())
                except Exception:
                    if not filepath or not os.path.exists(filepath):
                        return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            entries = data.get('objects', data.get('entries', data))
            # `entries` may be:
            #   (a) dict[fingerprint, positional_list]  — legacy v9.9 columnar
            #   (b) dict[fingerprint, entry_dict]       — legacy dict-of-dicts
            #   (c) list[entry_dict]                    — new-schema list
            if isinstance(entries, list):
                iter_items = [(e.get('fingerprint', str(i)), e) for i, e in enumerate(entries)]
            elif isinstance(entries, dict):
                iter_items = entries.items()
            else:
                iter_items = []
            for fp, entry in iter_items:
                # Hydrate positional v9.9 list into a dict shape.
                if isinstance(entry, list):
                    fields = data.get('_fields', ['ubp_id', 'lexicon', 'tags', 'vector', 'nrci_str', 'nrci_val', 'tax_str', 'mog_tensor'])
                    f_idx = {name: i for i, name in enumerate(fields)}
                    entry = {
                        'ubp_id': entry[f_idx['ubp_id']] if 'ubp_id' in f_idx and len(entry) > f_idx['ubp_id'] else None,
                        'lexicon': entry[f_idx['lexicon']] if 'lexicon' in f_idx and len(entry) > f_idx['lexicon'] else '',
                        'tags': entry[f_idx['tags']] if 'tags' in f_idx and len(entry) > f_idx['tags'] else [],
                        'atlas': {'vector': entry[f_idx['vector']] if 'vector' in f_idx and len(entry) > f_idx['vector'] else []},
                    }
                if not isinstance(entry, dict):
                    continue
                uid = entry.get('ubp_id')
                if uid:
                    self.registry[fp] = entry
                    self.id_map[uid] = fp
                    vec = entry.get('atlas', {}).get('vector') or entry.get('vector')
                    if vec:
                        self.vector_cache[uid] = vec
            print(f'[HEX_DB] Loaded {len(self.id_map)} spatial-deterministic entries.')
        except Exception as e:
            print(f'[HEX_DB] Load failed: {e}')

    def find_by_id(self, ubp_id: str) -> Optional[Dict[str, Any]]:
        fp = self.id_map.get(ubp_id)
        return self.registry.get(fp) if fp else None

    def get_vector(self, ubp_id: str) -> Optional[List[int]]:
        return self.vector_cache.get(ubp_id)
HEX_DB_EXACT = HexDictionaryV4Exact()

# --- Extracted from math_atlas.py ---
"""
MathAtlas v4.0 - The Definitive Mathematical Substrate
======================================================
Consolidated from v1.3, v2.0, and v3.0.

"Every object is a recursive construction of its own history."

Author: E R A Craig / UBP Research Cortex v4.2.7
Date: 13 February 2026
"""
import json
import hashlib
import decimal
import math
import numpy as np
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Union, Set
try:
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
UNIVERSAL_NORTH = [-0.30656966974248284, -0.9197090092274486, 0.2452557357939863]
decimal.getcontext().prec = 300

class MathAtlasConstants:
    """Ultra-high precision mathematical constants for v4.0."""

    @classmethod
    def _cf_to_fraction(cls, cf, depth=100):
        x = Fraction(cf[-1], 1)
        for c in reversed(cf[:-1]):
            x = Fraction(c, 1) + Fraction(1, x)
        return x

    @classmethod
    def get_pi(cls) -> Fraction:
        cf = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2, 1, 84, 2, 1, 1, 15, 3, 13, 1, 4, 2, 6, 6, 99, 1, 2, 2, 6, 3, 5, 1, 1, 6, 8, 1, 7, 1, 6, 1, 99, 7, 4, 1, 3, 3, 1, 4, 1]
        return cls._cf_to_fraction(cf)

    @classmethod
    def get_e(cls) -> Fraction:
        cf = [2] + [x for n in range(1, 30) for x in [1, 2 * n, 1]]
        return cls._cf_to_fraction(cf)

    @classmethod
    def get_phi(cls) -> Fraction:
        return cls._cf_to_fraction([1] * 100)

    @classmethod
    def get_sqrt(cls, n) -> Fraction:
        x = Fraction(n, 1)
        for _ in range(10):
            x = (x + n / x) / 2
        return x
PI = MathAtlasConstants.get_pi()
E = MathAtlasConstants.get_e()
PHI = MathAtlasConstants.get_phi()
Y_CONST = Fraction(1, 1) / (PI + Fraction(2, 1) / PI)

@dataclass
class ConstructionPath:
    """A specific geometric construction for a MathObject."""
    primitives: List[Tuple]
    method: str
    tax: Fraction = field(init=False)
    voxels: List[Tuple] = field(init=False, default_factory=list)

    def __post_init__(self):
        self._build(offset=(0, 0, 0))

    def _build(self, offset):
        total_tax = Fraction(0, 1)
        x, y, z = offset
        for op_tuple in self.primitives:
            op = op_tuple[0]
            if op == 'D':
                mag = op_tuple[1] if len(op_tuple) > 1 else 1
                for _ in range(mag):
                    x += 1
                    self.voxels.append((x, y, z, '#00ffff'))
                    total_tax += Y_CONST
            elif op == 'X':
                mag = op_tuple[1] if len(op_tuple) > 1 else 1
                for _ in range(mag):
                    x -= 1
                    self.voxels.append((x, y, z, '#ff0000'))
                    total_tax += Y_CONST
            elif op in ['N', 'J']:
                child = op_tuple[1]
                child_offset = (x, y + 1, z) if op == 'N' else (x, y, z + 1)
                if hasattr(child, 'get_canonical_path'):
                    cp = child.get_canonical_path()
                    for vx, vy, vz, c in cp.voxels:
                        self.voxels.append((child_offset[0] + vx, child_offset[1] + vy, child_offset[2] + vz, c))
                    total_tax += cp.tax + Y_CONST / (2 if op == 'N' else 4)
        self.tax = total_tax + Fraction(len(self.voxels) ** 2, 800)

@dataclass
class MathObjectV4:
    ubp_id: str
    name: str
    description: str
    category: str = 'math.general'
    paths: List[ConstructionPath] = field(default_factory=list)
    components: Dict[str, 'MathObjectV4'] = field(default_factory=dict)
    morphisms: Dict[str, str] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)

    def add_path(self, primitives, method):
        path = ConstructionPath(primitives, method)
        self.paths.append(path)
        return path

    def get_canonical_path(self) -> ConstructionPath:
        return min(self.paths, key=lambda p: p.tax) if self.paths else ConstructionPath([], 'empty')

    def get_vector(self) -> List[int]:
        if not CORE_AVAILABLE:
            return [0] * 24
        geo_str = str(sorted(list(set(self.get_canonical_path().voxels))))
        h = hashlib.sha256(geo_str.encode()).digest()
        msg_int = (h[0] << 8 | h[1]) & 4095
        return GOLAY_ENGINE.encode([msg_int >> i & 1 for i in range(11, -1, -1)])

    def get_charge(self) -> float:
        v = [
            float(sum(vector[0:8]) - 4),
            float(sum(vector[8:16]) - 4),
            float(sum(vector[16:24]) - 4)
        ]
        mag = math.sqrt(sum(x*x for x in v))
        if mag == 0: return 0.0
    
        mag_n = math.sqrt(sum(x*x for x in UNIVERSAL_NORTH))
        unit_v = [x / mag for x in v]
        unit_north = [x / mag_n for x in UNIVERSAL_NORTH]
    
        dot = sum(a * b for a, b in zip(unit_v, unit_north))
        return round(float(math.degrees(math.acos(max(-1, min(1, dot))))), 4)

    def get_recursive_math(self) -> str:
        """Builds the full embedded math string."""
        if not self.components:
            return self.properties.get('math_raw', f'Val={self.name}')
        parts = [f'{k}=[{v.get_recursive_math()}]' for k, v in self.components.items()]
        return '|'.join(parts)

    def to_dict(self) -> Dict:
        cp = self.get_canonical_path()
        nrci = Fraction(1, 1) / (Fraction(1, 1) + cp.tax * Fraction(1, 10))
        return {'ubp_id': self.ubp_id, 'name': self.name, 'math': self.get_recursive_math(), 'category': self.category, 'nrci': f'{nrci.numerator}/{nrci.denominator}', 'nrci_score': float(nrci), 'vector': self.get_vector(), 'geometric_charge': self.get_charge(), 'atlas_metadata': {'voxels': len(cp.voxels), 'tax': {'n': cp.tax.numerator, 'd': cp.tax.denominator}, 'path_count': len(self.paths)}}

    def calculate_compactness(self) -> Fraction:
        """
        Calculates the 3D efficiency of the voxel cloud.
        """
        voxels = self.get_canonical_path().voxels
        if not voxels:
            return Fraction(0)
        volume = len(voxels)
        coords = set(((v[0], v[1], v[2]) for v in voxels))
        surface = 0
        for x, y, z in coords:
            neighbors = [(x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)]
            for n in neighbors:
                if n not in coords:
                    surface += 1
        if surface == 0:
            return Fraction(1)
        vol_2_3 = Fraction(int(math.pow(volume, 2 / 3) * 1000), 1000)
        return vol_2_3 / surface

    def get_nrci(self) -> Fraction:
        """
        v6.0 Unified Stability Formula.
        """
        cp = self.get_canonical_path()
        c_factor = self.calculate_compactness()
        vec = self.get_vector()
        final_tax = LEECH_ENGINE.calculate_symmetry_tax(vec)
        return Fraction(10, 1) / (Fraction(10, 1) + final_tax)

def PositiveInteger(n: int) -> MathObjectV4:
    obj = MathObjectV4(f'MATH_NAT_{n:010d}', f'Natural {n}', f'The number {n}', 'number.natural')
    obj.add_path([('D', n)], 'direct')
    obj.properties['math_raw'] = f'Val={n}'
    return obj

def Rational(p: int, q: int) -> MathObjectV4:
    num = PositiveInteger(p)
    den = PositiveInteger(q)
    obj = MathObjectV4(f'MATH_RAT_{p}_{q}', f'Rational {p}/{q}', f'The fraction {p}/{q}', 'number.rational')
    obj.components = {'num': num, 'den': den}
    obj.add_path([('N', num), ('J', den)], 'nested')
    return obj

class ExactRationalEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Fraction):
            return {'n': obj.numerator, 'd': obj.denominator, 'v': float(obj)}
        if isinstance(obj, MathObjectV4):
            return obj.to_dict()
        return super().default(obj)
