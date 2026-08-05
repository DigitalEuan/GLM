"""
training_language_v2.py — Words as Proper Data Objects

Each word is a Data Object with MEANING — encoded from measurable properties,
not just hashes. Following the encoding_specification.md:

"A Data Object is to provide 'meaning' by being a representation of a Subject
that has actual alignment with reality through calculation."

Word properties (like element properties Z, EN, Rad, Valence_e):
- Row 0 (Reality): Physical/structural — length, syllables, letters
- Row 1 (Info): Categorical — part of speech, semantic domain
- Row 2 (Activation): Emotional — valence, arousal, concreteness
- Row 3 (Potential): Relational — frequency, ambiguity, associations

Each row is 6-bit Gray-coded, just like elements.
"""

from __future__ import annotations
import sys, json, math, time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
LTM_DIR = SCRIPT_DIR.parent.parent / "long_term_memory"
sys.path.insert(0, str(SCRIPT_DIR))

Y = 0.2646754304045269672

try:
    import ubp_unified_v5 as ubp
    GOLAY = ubp.GOLAY_ENGINE
    HAS_GOLAY = True
except:
    HAS_GOLAY = False


# ═══════════════════════════════════════════════════════════════════════════════
# Word Properties — the "math field" for words
# ═══════════════════════════════════════════════════════════════════════════════

# Part of speech encoding
POS_MAP = {"noun": 0, "verb": 1, "adjective": 2, "adverb": 3, "pronoun": 4, "preposition": 5}

# Semantic domain encoding
DOMAIN_MAP = {
    "animal": 0, "colour": 1, "number": 2, "body": 3, "food": 4,
    "nature": 5, "action": 6, "emotion": 7, "size": 8, "object": 9,
    "time": 10, "place": 11, "person": 12, "abstract": 13, "other": 14,
}

# Emotional valence: -1 (negative) to +1 (positive), scaled to 0-63
VALENCE = {
    # Animals (neutral to positive)
    "cat": 0.5, "dog": 0.7, "fish": 0.3, "bird": 0.5, "horse": 0.5,
    "cow": 0.3, "pig": 0.3, "sheep": 0.4, "lion": 0.4, "tiger": 0.4,
    # Colours (neutral)
    "red": 0.1, "blue": 0.2, "green": 0.2, "yellow": 0.2, "white": 0.2,
    "black": -0.1, "orange": 0.2, "purple": 0.2, "pink": 0.3, "brown": 0.0,
    # Numbers (neutral)
    "one": 0.0, "two": 0.0, "three": 0.0, "four": 0.0, "five": 0.0,
    "six": 0.0, "seven": 0.0, "eight": 0.0, "nine": 0.0, "ten": 0.0,
    # Body (neutral)
    "head": 0.0, "hand": 0.1, "foot": 0.0, "eye": 0.1, "ear": 0.0,
    "nose": 0.0, "mouth": 0.0, "arm": 0.0, "leg": 0.0, "heart": 0.5,
    # Food (positive)
    "bread": 0.4, "milk": 0.3, "meat": 0.3, "rice": 0.3, "apple": 0.5,
    "egg": 0.2, "cheese": 0.4, "cake": 0.7, "soup": 0.4,
    # Nature (mixed)
    "sun": 0.6, "moon": 0.5, "star": 0.6, "sky": 0.4, "sea": 0.5,
    "river": 0.4, "mountain": 0.4, "tree": 0.4, "flower": 0.7, "rain": 0.1,
    # Actions (neutral to positive)
    "run": 0.2, "walk": 0.2, "jump": 0.3, "eat": 0.4, "sleep": 0.3,
    "read": 0.4, "write": 0.3, "sing": 0.5, "dance": 0.6, "swim": 0.3,
    # Emotions (varied)
    "happy": 0.9, "sad": -0.7, "angry": -0.6, "afraid": -0.5, "love": 0.9,
    "hate": -0.8, "hope": 0.7, "fear": -0.6, "joy": 0.9, "pain": -0.7,
    # Sizes (neutral)
    "big": 0.0, "small": 0.0, "tall": 0.0, "short": 0.0, "long": 0.0,
    "wide": 0.0, "thin": 0.0, "thick": 0.0, "deep": 0.0, "high": 0.1,
    # Opposites
    "hot": 0.1, "cold": -0.1, "up": 0.1, "down": -0.1, "in": 0.0,
    "out": 0.0, "yes": 0.3, "no": -0.2, "good": 0.6, "bad": -0.5,
    "old": -0.1, "new": 0.3, "fast": 0.2, "slow": -0.1, "light": 0.3,
    "dark": -0.2, "true": 0.3, "false": -0.3, "start": 0.2, "end": -0.1,
}

# Concreteness: 0 (abstract) to 1 (concrete)
CONCRETENESS = {
    "cat": 1.0, "dog": 1.0, "fish": 1.0, "bird": 1.0, "horse": 1.0,
    "cow": 1.0, "pig": 1.0, "sheep": 1.0, "lion": 1.0, "tiger": 1.0,
    "red": 0.8, "blue": 0.8, "green": 0.8, "yellow": 0.8, "white": 0.8,
    "black": 0.8, "orange": 0.8, "purple": 0.8, "pink": 0.8, "brown": 0.8,
    "one": 0.2, "two": 0.2, "three": 0.2, "four": 0.2, "five": 0.2,
    "six": 0.2, "seven": 0.2, "eight": 0.2, "nine": 0.2, "ten": 0.2,
    "head": 1.0, "hand": 1.0, "foot": 1.0, "eye": 1.0, "ear": 1.0,
    "nose": 1.0, "mouth": 1.0, "arm": 1.0, "leg": 1.0, "heart": 1.0,
    "bread": 1.0, "milk": 1.0, "meat": 1.0, "rice": 1.0, "apple": 1.0,
    "egg": 1.0, "cheese": 1.0, "cake": 1.0, "soup": 1.0,
    "sun": 1.0, "moon": 1.0, "star": 1.0, "sky": 0.9, "sea": 1.0,
    "river": 1.0, "mountain": 1.0, "tree": 1.0, "flower": 1.0, "rain": 0.9,
    "run": 0.6, "walk": 0.6, "jump": 0.6, "eat": 0.7, "sleep": 0.6,
    "read": 0.5, "write": 0.5, "sing": 0.5, "dance": 0.6, "swim": 0.7,
    "happy": 0.2, "sad": 0.2, "angry": 0.3, "afraid": 0.3, "love": 0.2,
    "hate": 0.2, "hope": 0.2, "fear": 0.3, "joy": 0.2, "pain": 0.5,
    "big": 0.5, "small": 0.5, "tall": 0.6, "short": 0.6, "long": 0.6,
    "wide": 0.5, "thin": 0.5, "thick": 0.5, "deep": 0.5, "high": 0.6,
    "hot": 0.7, "cold": 0.7, "up": 0.3, "down": 0.3, "in": 0.2,
    "out": 0.2, "yes": 0.0, "no": 0.0, "good": 0.2, "bad": 0.2,
    "old": 0.4, "new": 0.4, "fast": 0.5, "slow": 0.5, "light": 0.6,
    "dark": 0.6, "true": 0.1, "false": 0.1, "start": 0.3, "end": 0.3,
}

# Word domain assignments
WORD_DOMAINS = {
    "cat": "animal", "dog": "animal", "fish": "animal", "bird": "animal",
    "horse": "animal", "cow": "animal", "pig": "animal", "sheep": "animal",
    "lion": "animal", "tiger": "animal",
    "red": "colour", "blue": "colour", "green": "colour", "yellow": "colour",
    "white": "colour", "black": "colour", "orange": "colour", "purple": "colour",
    "pink": "colour", "brown": "colour",
    "one": "number", "two": "number", "three": "number", "four": "number",
    "five": "number", "six": "number", "seven": "number", "eight": "number",
    "nine": "number", "ten": "number",
    "head": "body", "hand": "body", "foot": "body", "eye": "body", "ear": "body",
    "nose": "body", "mouth": "body", "arm": "body", "leg": "body", "heart": "body",
    "bread": "food", "milk": "food", "meat": "food", "rice": "food", "apple": "food",
    "egg": "food", "cheese": "food", "cake": "food", "soup": "food", "fish": "food",
    "sun": "nature", "moon": "nature", "star": "nature", "sky": "nature", "sea": "nature",
    "river": "nature", "mountain": "nature", "tree": "nature", "flower": "nature", "rain": "nature",
    "run": "action", "walk": "action", "jump": "action", "eat": "action", "sleep": "action",
    "read": "action", "write": "action", "sing": "action", "dance": "action", "swim": "action",
    "happy": "emotion", "sad": "emotion", "angry": "emotion", "afraid": "emotion",
    "love": "emotion", "hate": "emotion", "hope": "emotion", "fear": "emotion",
    "joy": "emotion", "pain": "emotion",
    "big": "size", "small": "size", "tall": "size", "short": "size", "long": "size",
    "wide": "size", "thin": "size", "thick": "size", "deep": "size", "high": "size",
    "hot": "size", "cold": "size", "up": "abstract", "down": "abstract", "in": "abstract",
    "out": "abstract", "yes": "abstract", "no": "abstract", "good": "abstract", "bad": "abstract",
    "old": "abstract", "new": "abstract", "fast": "action", "slow": "action",
    "light": "nature", "dark": "nature", "true": "abstract", "false": "abstract",
    "start": "abstract", "end": "abstract",
}

# Part of speech
WORD_POS = {}
for w in list(VALENCE.keys()):
    if w in WORD_DOMAINS and WORD_DOMAINS[w] in ("animal", "colour", "number", "body", "food", "nature", "object"):
        WORD_POS[w] = "noun"
    elif w in WORD_DOMAINS and WORD_DOMAINS[w] == "action":
        WORD_POS[w] = "verb"
    elif w in WORD_DOMAINS and WORD_DOMAINS[w] == "size":
        WORD_POS[w] = "adjective"
    elif w in WORD_DOMAINS and WORD_DOMAINS[w] == "emotion":
        WORD_POS[w] = "adjective"
    elif w in ("yes", "no", "true", "false"):
        WORD_POS[w] = "adverb"
    elif w in ("up", "down", "in", "out"):
        WORD_POS[w] = "adverb"
    elif w in ("old", "new", "good", "bad", "fast", "slow", "light", "dark"):
        WORD_POS[w] = "adjective"
    elif w in ("start", "end"):
        WORD_POS[w] = "noun"
    else:
        WORD_POS[w] = "noun"


# ═══════════════════════════════════════════════════════════════════════════════
# Data Object Encoding — word as 24-bit MOG grid
# ═══════════════════════════════════════════════════════════════════════════════

def gray6(n: int) -> List[int]:
    """6-bit Gray code."""
    n &= 0x3F
    g = n ^ (n >> 1)
    return [(g >> (5 - i)) & 1 for i in range(6)]


def encode_word(word: str) -> List[int]:
    """Encode a word as a 24-bit Data Object with meaning.

    Row 0 (Reality): Physical properties — length, syllable count
    Row 1 (Info): Categorical — part of speech, semantic domain
    Row 2 (Activation): Emotional — valence, concreteness
    Row 3 (Potential): Structural — letter hash, vowel ratio
    """
    w = word.lower()

    # Row 0 (Reality): length (0-63)
    length_val = min(len(w), 63)
    row0 = gray6(length_val)

    # Row 1 (Info): POS (0-5) in high 3 bits, domain (0-14) in low 3 bits
    pos_val = POS_MAP.get(WORD_POS.get(w, "noun"), 0)
    domain_val = DOMAIN_MAP.get(WORD_DOMAINS.get(w, "other"), 14)
    row1_val = (pos_val << 3) | (domain_val & 0x07)
    row1 = gray6(row1_val)

    # Row 2 (Activation): valence (-1 to +1) → 0-63, concreteness (0-1) → interleaved
    valence = VALENCE.get(w, 0.0)
    valence_bits = int((valence + 1) * 31.5) & 0x3F  # -1→0, 0→31, +1→63
    concrete = CONCRETENESS.get(w, 0.5)
    concrete_bit = 1 if concrete > 0.5 else 0
    # Interleave: valence in bits 0-4, concreteness in bit 5
    row2_val = (concrete_bit << 5) | (valence_bits & 0x1F)
    row2 = gray6(row2_val)

    # Row 3 (Potential): structural — vowel count in high 3, consonant count in low 3
    vowels = sum(1 for c in w if c in 'aeiou')
    consonants = sum(1 for c in w if c.isalpha() and c not in 'aeiou')
    row3_val = ((min(vowels, 7) & 0x07) << 3) | (min(consonants, 7) & 0x07)
    row3 = gray6(row3_val)

    return row0 + row1 + row2 + row3


# ═══════════════════════════════════════════════════════════════════════════════
# Substrate Operations
# ═══════════════════════════════════════════════════════════════════════════════

def do_metrics(vec):
    hw = sum(vec)
    tax = hw * Y + sum(v*v for v in vec) / 8.0
    nrci = 10.0 / (10.0 + tax)
    return {"hw": hw, "nrci": nrci, "tax": tax}

def do_and(a, b): return [a[i] & b[i] for i in range(24)]
def do_xor(a, b): return [a[i] ^ b[i] for i in range(24)]

def golay_snap(vec):
    if HAS_GOLAY:
        s, _ = GOLAY.snap_to_codeword(vec)
        return s
    return vec[:]


# ═══════════════════════════════════════════════════════════════════════════════
# Word Groups and Pairs
# ═══════════════════════════════════════════════════════════════════════════════

WORD_GROUPS = {
    "animals": ["cat", "dog", "fish", "bird", "horse", "cow", "pig", "sheep", "lion", "tiger"],
    "colours": ["red", "blue", "green", "yellow", "white", "black", "orange", "purple", "pink", "brown"],
    "numbers": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
    "body": ["head", "hand", "foot", "eye", "ear", "nose", "mouth", "arm", "leg", "heart"],
    "food": ["bread", "milk", "meat", "rice", "apple", "egg", "cheese", "cake", "soup"],
    "nature": ["sun", "moon", "star", "sky", "sea", "river", "mountain", "tree", "flower", "rain"],
    "actions": ["run", "walk", "jump", "eat", "sleep", "read", "write", "sing", "dance", "swim"],
    "emotions": ["happy", "sad", "angry", "afraid", "love", "hate", "hope", "fear", "joy", "pain"],
    "sizes": ["big", "small", "tall", "short", "long", "wide", "thin", "thick", "deep", "high"],
}

WORD_PAIRS = [
    ("cat", "dog", "same_group"), ("cat", "fish", "same_group"),
    ("cat", "red", "diff_group"), ("red", "blue", "same_group"),
    ("hot", "cold", "opposite"), ("up", "down", "opposite"),
    ("happy", "sad", "opposite"), ("happy", "joy", "synonym"),
    ("big", "small", "opposite"), ("sun", "moon", "opposite"),
    ("run", "walk", "related"), ("heart", "love", "related"),
    ("dark", "fear", "related"), ("fast", "run", "related"),
    ("cat", "happy", "diff_group"), ("run", "red", "diff_group"),
    ("sun", "star", "related"), ("bread", "milk", "same_group"),
    ("head", "hand", "same_group"), ("one", "two", "same_group"),
    ("sad", "pain", "related"), ("big", "tall", "related"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Training
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    print("=" * 70)
    print("LANGUAGE TRAINING v2 — Words as Data Objects with Meaning")
    print("=" * 70)
    print()

    # Encode all words
    all_words = set()
    for group_words in WORD_GROUPS.values():
        all_words.update(group_words)
    for a, b, _ in WORD_PAIRS:
        all_words.add(a)
        all_words.add(b)

    encodings = {}
    for word in all_words:
        vec = encode_word(word)
        snapped = golay_snap(vec)
        m = do_metrics(vec)
        encodings[word] = {
            "vec": vec, "snapped": snapped,
            "hw": m["hw"], "nrci": m["nrci"],
            "bits_changed": sum(1 for i in range(24) if vec[i] != snapped[i]),
            "properties": {
                "length": len(word),
                "pos": WORD_POS.get(word, "?"),
                "domain": WORD_DOMAINS.get(word, "?"),
                "valence": VALENCE.get(word, 0),
                "concreteness": CONCRETENESS.get(word, 0.5),
            },
        }

    unique = len(set(tuple(d["snapped"]) for d in encodings.values()))
    print(f"Words: {len(all_words)}, Unique vectors: {unique}")

    # Show some encodings
    print(f"\nSample Data Objects:")
    for word in ["cat", "happy", "run", "red", "big", "sun", "love", "fear"]:
        if word in encodings:
            e = encodings[word]
            p = e["properties"]
            print(f"  {word:8s} HW={e['hw']:2d} NRCI={e['nrci']:.4f} "
                  f"pos={p['pos']:10s} domain={p['domain']:10s} "
                  f"val={p['valence']:+.1f} conc={p['concreteness']:.1f}")

    # Within-group similarity
    print(f"\nWithin-Group AND_NRCI:")
    for group_name, group_words in WORD_GROUPS.items():
        and_nrcis = []
        for i in range(len(group_words)):
            for j in range(i+1, min(len(group_words), i+6)):
                w1, w2 = group_words[i], group_words[j]
                if w1 in encodings and w2 in encodings:
                    v1, v2 = encodings[w1]["vec"], encodings[w2]["vec"]
                    and_m = do_metrics(do_and(v1, v2))
                    and_nrcis.append(and_m["nrci"])
        avg = sum(and_nrcis) / len(and_nrcis) if and_nrcis else 0
        print(f"  {group_name:12s}: {avg:.4f} (n={len(and_nrcis)})")

    # Cross-group
    print(f"\nCross-Group AND_NRCI:")
    groups = list(WORD_GROUPS.keys())
    for i in range(min(5, len(groups))):
        for j in range(i+1, min(5, len(groups))):
            g1, g2 = WORD_GROUPS[groups[i]][:3], WORD_GROUPS[groups[j]][:3]
            cross = []
            for w1 in g1:
                for w2 in g2:
                    if w1 in encodings and w2 in encodings:
                        and_m = do_metrics(do_and(encodings[w1]["vec"], encodings[w2]["vec"]))
                        cross.append(and_m["nrci"])
            avg = sum(cross) / len(cross) if cross else 0
            print(f"  {groups[i]:10s} ↔ {groups[j]:10s}: {avg:.4f}")

    # Word pairs
    print(f"\nWord Pair Relationships (with meaning):")
    print(f"  {'Pair':25s} {'Relation':12s} {'AND_NRCI':9s} {'XOR_HW':7s} {'ΔVal':6s} {'ΔConc':6s}")
    for w1, w2, relation in WORD_PAIRS:
        if w1 not in encodings or w2 not in encodings:
            continue
        v1, v2 = encodings[w1]["vec"], encodings[w2]["vec"]
        and_m = do_metrics(do_and(v1, v2))
        xor_hw = sum(do_xor(v1, v2))
        dv = abs(VALENCE.get(w1, 0) - VALENCE.get(w2, 0))
        dc = abs(CONCRETENESS.get(w1, 0.5) - CONCRETENESS.get(w2, 0.5))
        print(f"  {w1:10s}-{w2:10s}  {relation:12s} {and_m['nrci']:9.4f} {xor_hw:7d} {dv:+.1f} {dc:.1f}")

    # Prediction: can AND_NRCI distinguish same_group from diff_group?
    import statistics
    same_nrcis = []
    diff_nrcis = []
    opp_nrcis = []
    rel_nrcis = []
    for w1, w2, rel in WORD_PAIRS:
        if w1 not in encodings or w2 not in encodings:
            continue
        and_m = do_metrics(do_and(encodings[w1]["vec"], encodings[w2]["vec"]))
        if rel == "same_group": same_nrcis.append(and_m["nrci"])
        elif rel == "diff_group": diff_nrcis.append(and_m["nrci"])
        elif rel == "opposite": opp_nrcis.append(and_m["nrci"])
        elif rel in ("related", "synonym"): rel_nrcis.append(and_m["nrci"])

    print(f"\nRelationship Prediction:")
    if same_nrcis: print(f"  Same group:  mean={statistics.mean(same_nrcis):.4f} (n={len(same_nrcis)})")
    if diff_nrcis: print(f"  Diff group:  mean={statistics.mean(diff_nrcis):.4f} (n={len(diff_nrcis)})")
    if opp_nrcis:  print(f"  Opposite:    mean={statistics.mean(opp_nrcis):.4f} (n={len(opp_nrcis)})")
    if rel_nrcis:  print(f"  Related:     mean={statistics.mean(rel_nrcis):.4f} (n={len(rel_nrcis)})")
    if same_nrcis and diff_nrcis:
        sep = statistics.mean(same_nrcis) - statistics.mean(diff_nrcis)
        print(f"  Separation (same - diff): {sep:+.4f}")

    # Golay structure
    changed = sum(1 for d in encodings.values() if d["bits_changed"] > 0)
    print(f"\nGolay: {changed}/{len(encodings)} words change bits on snap")

    # Save
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_words": len(all_words),
        "n_unique": unique,
        "encoding": "Data Object (4-row MOG with meaning)",
        "rows": {
            "row0_reality": "word length",
            "row1_info": "POS (3 bits) + domain (3 bits)",
            "row2_activation": "valence (5 bits) + concreteness (1 bit)",
            "row3_potential": "vowel count (3 bits) + consonant count (3 bits)",
        },
        "word_data": {
            w: {"hw": d["hw"], "nrci": round(d["nrci"], 4), "props": d["properties"]}
            for w, d in encodings.items()
        },
    }
    out_path = LTM_DIR / "language_training_v2.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved to {out_path}")

    return output


if __name__ == "__main__":
    run()
