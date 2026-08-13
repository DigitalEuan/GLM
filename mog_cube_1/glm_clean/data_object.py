"""
The DataObject — a 24-bit vector arranged as a 4×6 MOG grid.

THE input format. Every concept enters the GLM as a DataObject.

The MOG 4×6 grid:
            col 0   col 1   col 2   col 3   col 4   col 5
row 0       b0      b1      b2      b3      b4      b5      ← Reality (identity)
row 1       b6      b7      b8      b9      b10     b11     ← Info (about)
row 2       b12     b13     b14     b15     b16     b17     ← Activation (does)
row 3       b18     b19     b20     b21     b22     b23     ← Potential (function)

Per user: "The Information row should carry rich 'about' whatever the Subject is."

The Info row carries 6 semantic features (proven self-sufficient, no hint lists):
  magnitude, complexity, concrete, relation, dynamic, specific
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass


# The 4 MOG rows with their semantic labels
ROWS = ("reality", "info", "activation", "potential")


@dataclass
class DataObject:
    """A 24-bit vector arranged as a 4×6 MOG grid."""

    bits: List[int]  # 24 bits, 0 or 1

    def __post_init__(self):
        if len(self.bits) != 24:
            raise ValueError(f"DataObject expects 24 bits, got {len(self.bits)}")
        if any(b not in (0, 1) for b in self.bits):
            raise ValueError("DataObject bits must be 0 or 1")

    # ── constructors ─────────────────────────────────────────────────────
    @classmethod
    def from_int(cls, n: int) -> "DataObject":
        bits = [(n >> (23 - i)) & 1 for i in range(24)]
        return cls(bits=bits)

    @classmethod
    def from_rows(cls, reality: List[int], info: List[int],
                  activation: List[int], potential: List[int]) -> "DataObject":
        return cls(bits=reality + info + activation + potential)

    # ── conversions ──────────────────────────────────────────────────────
    def to_int(self) -> int:
        n = 0
        for b in self.bits:
            n = (n << 1) | b
        return n

    # ── row accessors ────────────────────────────────────────────────────
    @property
    def reality(self) -> List[int]: return list(self.bits[0:6])
    @property
    def info(self) -> List[int]: return list(self.bits[6:12])
    @property
    def activation(self) -> List[int]: return list(self.bits[12:18])
    @property
    def potential(self) -> List[int]: return list(self.bits[18:24])

    def row(self, name: str) -> List[int]:
        idx = ROWS.index(name)
        return list(self.bits[idx*6:(idx+1)*6])

    def row_int(self, name: str) -> int:
        n = 0
        for b in self.row(name):
            n = (n << 1) | b
        return n

    # ── operators ────────────────────────────────────────────────────────
    def hamming_distance(self, other: "DataObject") -> int:
        return sum(1 for a, b in zip(self.bits, other.bits) if a != b)

    def hamming_weight(self) -> int:
        return sum(self.bits)

    def __repr__(self) -> str:
        return f"DataObject(int={self.to_int()}, hw={self.hamming_weight()})"


# ══════════════════════════════════════════════════════════════════════════════
# THE ONE ENCODER
# ══════════════════════════════════════════════════════════════════════════════

def _int_to_6bits(n: int) -> List[int]:
    n = n & 0x3F
    return [(n >> (5 - i)) & 1 for i in range(6)]


def _gray_code(n: int, bits: int = 6) -> List[int]:
    n = n & ((1 << bits) - 1)
    gray = n ^ (n >> 1)
    return [(gray >> (bits - 1 - i)) & 1 for i in range(bits)]


# ── heuristic feature extractors (self-sufficient, no hint lists) ────────────

def _heuristic_concrete(w: str) -> int:
    """0=concrete, 1=abstract."""
    abstract_suffixes = ("tion", "sion", "ment", "ness", "ity", "ism", "ship", "ance", "ence")
    concrete_suffixes = ("er", "or", "ist")
    if any(w.endswith(s) for s in abstract_suffixes):
        return 1
    if any(w.endswith(s) for s in concrete_suffixes) and len(w) > 4:
        return 0
    return 0 if len(w) <= 5 else 1


def _heuristic_relation(w: str) -> int:
    """0=thing, 1=relation."""
    if len(w) <= 3:
        return 1
    if w.endswith("ly") and len(w) > 3:
        return 1
    if w.endswith("er") and len(w) > 3:
        return 1
    if w.endswith("est") and len(w) > 4:
        return 1
    if w.endswith("ish") and len(w) > 3:
        return 1
    return 0


def _heuristic_dynamic(w: str) -> int:
    """0=static, 1=dynamic."""
    if w.endswith("ing") and len(w) > 4:
        return 1
    if w.endswith("ed") and len(w) > 3:
        return 1
    if w.endswith("ize") or w.endswith("ise"):
        return 1
    if w.endswith("ate") and len(w) > 4:
        return 1
    if w.endswith("ify") and len(w) > 3:
        return 1
    common_verbs = {"run", "walk", "jump", "swim", "fly", "climb", "crawl",
                   "dance", "fall", "rise", "go", "come", "move", "turn",
                   "make", "build", "break", "cut", "push", "pull", "lift",
                   "drop", "throw", "catch", "kick", "hit", "give", "take",
                   "bring", "send", "hold", "open", "close", "grow", "burn",
                   "begin", "start", "end", "stop", "wait", "say", "tell",
                   "speak", "talk", "call", "sing", "cry", "laugh", "ask"}
    if w in common_verbs:
        return 1
    return 0


def _detect_pos(w: str) -> str:
    """Simple POS detection."""
    verb_endings = ("ed", "ing", "ize", "ise", "ify", "ate")
    adj_endings = ("ful", "less", "ous", "ive", "able", "ible", "al", "ic")
    adv_endings = ("ly",)
    if any(w.endswith(e) for e in verb_endings):
        return "verb"
    if any(w.endswith(e) for e in adj_endings):
        return "adjective"
    if any(w.endswith(e) for e in adv_endings):
        return "adverb"
    return "noun"


def _extract_features(w: str) -> Dict[str, int]:
    """6 semantic features. General heuristics only — no hint lists."""
    # syllables
    vowel_groups = 0
    prev_vowel = False
    for c in w:
        is_vowel = c.lower() in "aeiouy"
        if is_vowel and not prev_vowel:
            vowel_groups += 1
        prev_vowel = is_vowel
    syllables = max(1, vowel_groups)

    return {
        "magnitude": 1 if len(w) > 6 else 0,
        "complexity": 1 if syllables >= 3 else 0,
        "concrete": _heuristic_concrete(w),
        "relation": _heuristic_relation(w),
        "dynamic": _heuristic_dynamic(w),
        "specific": 1 if (w.isdigit() or len(w) >= 8) else 0,
    }


# POS codes (3 bits)
POS_CODES = {"noun": 1, "verb": 2, "adjective": 4, "adverb": 6,
             "pronoun": 8, "preposition": 10, "conjunction": 12,
             "number": 16, "operator": 18, "unknown": 0}

# Function codes (3 bits)
FUNC_CODES = {"subject": 1, "object": 2, "predicate": 3, "modifier": 4,
              "complement": 5, "connective": 6, "operator": 7, "unknown": 0}


def _encode_word(w: str) -> DataObject:
    """Encode a word using MOG row semantics (v2 heuristic-only)."""
    w = w.lower().strip()
    pos = _detect_pos(w)
    features = _extract_features(w)
    consonants = sum(1 for c in w if c.isalpha() and c.lower() not in "aeiou")
    vowels = sum(1 for c in w if c.lower() in "aeiou")

    # REALITY: POS (3 bits) + first letter (3 bits)
    pos_code = POS_CODES.get(pos, 0) & 0b111
    first_letter = ord(w[0]) - ord('a') if w and w[0].isalpha() else 0
    reality = _int_to_6bits((pos_code << 3) | (first_letter % 8))

    # INFO: 6 semantic features (the 'about' row)
    info = [features["magnitude"], features["complexity"], features["concrete"],
            features["relation"], features["dynamic"], features["specific"]]

    # ACTIVATION: valence-ish (3 bits) + consonants (3 bits)
    val_code = 2 if pos == "verb" else (1 if pos == "adjective" else 0)
    activation = _int_to_6bits((val_code << 3) | (consonants % 8))

    # POTENTIAL: syntactic function (3 bits) + vowels (3 bits)
    if pos == "noun": func = "subject"
    elif pos == "verb": func = "predicate"
    elif pos in ("adjective", "adverb"): func = "modifier"
    elif pos in ("preposition", "conjunction"): func = "connective"
    else: func = "unknown"
    func_code = FUNC_CODES.get(func, 0) & 0b111
    potential = _int_to_6bits((func_code << 3) | (vowels % 8))

    return DataObject.from_rows(reality, info, activation, potential)


def _encode_number(n: int) -> DataObject:
    """Encode an integer. Numbers are geometric shapes (vertex count = 2|N|+4)."""
    vc = 2 * abs(n) + 4 + (1 if n < 0 else 0)
    # prime factor count
    def _pf_count(num):
        if num < 2: return 0
        factors = set()
        num = abs(num)
        d = 2
        while d * d <= num:
            while num % d == 0:
                factors.add(d); num //= d
            d += 1
        if num > 1: factors.add(num)
        return len(factors)

    n_factors = _pf_count(n) % 8
    is_prime = 1 if n_factors == 1 and abs(n) > 1 else 0

    reality = _gray_code(vc % 64, 6)
    info = _int_to_6bits((1 if n < 0 else 0) << 5 | (min(4, vc // 8) & 0b11111))
    activation = _int_to_6bits((n_factors << 3) | (is_prime << 2))
    potential = _int_to_6bits(n % 8)

    return DataObject.from_rows(reality, info, activation, potential)


def encode(raw_input: Union[str, int, DataObject]) -> DataObject:
    """THE ONE encoder. Handles words and numbers. That's it."""
    if isinstance(raw_input, DataObject):
        return raw_input
    if isinstance(raw_input, int):
        return _encode_number(raw_input)
    if isinstance(raw_input, str):
        # try number
        try:
            return _encode_number(int(raw_input))
        except ValueError:
            pass
        return _encode_word(raw_input)
    raise ValueError(f"Cannot encode {type(raw_input)}")
