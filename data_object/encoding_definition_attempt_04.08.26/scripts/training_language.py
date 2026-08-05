"""
training_language.py — Language Training: Words as Data Objects

From the encoding spec: "words may have meaning when compared relative to
other words and known Subjects, not many things work well in isolation —
generally speaking the strongest results occur through interaction,
comparison, reflection and other relationship calculations."

So we encode words, compute relationships, and see what the substrate reveals.
"""

from __future__ import annotations
import sys, json, math, time, hashlib
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
# Word Encoding Methods
# ═══════════════════════════════════════════════════════════════════════════════

def word_to_24bit_hash(word: str) -> List[int]:
    """Encode word as 24-bit hash (deterministic)."""
    h = hashlib.sha256(word.lower().encode()).digest()
    bits = []
    for byte in h[:3]:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits[:24]


def word_to_24bit_letters(word: str) -> List[int]:
    """Encode word using letter positions in alphabet.
    Each letter maps to a bit position (a=0, b=1, ..., z=25).
    """
    bits = [0] * 24
    for ch in word.lower():
        if 'a' <= ch <= 'z':
            pos = ord(ch) - ord('a')
            bits[pos % 24] = 1
    return bits


def word_to_24bit_structural(word: str) -> List[int]:
    """Encode word structure: length, vowels, consonants, patterns."""
    bits = [0] * 24
    vowels = sum(1 for c in word.lower() if c in 'aeiou')
    consonants = sum(1 for c in word.lower() if c.isalpha() and c not in 'aeiou')

    # Row 0 (Reality): length encoding
    length_val = min(len(word), 63)
    for i in range(6):
        bits[i] = (length_val >> (5 - i)) & 1

    # Row 1 (Info): vowel/consonant ratio
    if len(word) > 0:
        ratio_val = int(vowels / len(word) * 63) & 0x3F
    else:
        ratio_val = 0
    for i in range(6):
        bits[6 + i] = (ratio_val >> (5 - i)) & 1

    # Row 2 (Activation): first/last letter
    if word:
        first_val = (ord(word[0].lower()) - ord('a')) & 0x3F
        last_val = (ord(word[-1].lower()) - ord('a')) & 0x3F
        combined = (first_val ^ last_val) & 0x3F
        for i in range(6):
            bits[12 + i] = (combined >> (5 - i)) & 1

    # Row 3 (Potential): hash of middle
    mid = word[len(word)//2:] if len(word) > 2 else word
    mid_hash = sum(ord(c) for c in mid) & 0x3F
    for i in range(6):
        bits[18 + i] = (mid_hash >> (5 - i)) & 1

    return bits


# ═══════════════════════════════════════════════════════════════════════════════
# Substrate Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def do_metrics(vec):
    hw = sum(vec)
    tax = hw * Y + sum(v*v for v in vec) / 8.0
    nrci = 10.0 / (10.0 + tax)
    return {"hw": hw, "nrci": nrci, "tax": tax}

def do_and(a, b): return [a[i] & b[i] for i in range(24)]
def do_xor(a, b): return [a[i] ^ b[i] for i in range(24)]
def do_or(a, b): return [a[i] | b[i] for i in range(24)]

def golay_snap(vec):
    if HAS_GOLAY:
        s, _ = GOLAY.snap_to_codeword(vec)
        return s
    return vec[:]


# ═══════════════════════════════════════════════════════════════════════════════
# Word Relationship Data
# ═══════════════════════════════════════════════════════════════════════════════

WORD_GROUPS = {
    "animals": ["cat", "dog", "fish", "bird", "horse", "cow", "pig", "sheep", "lion", "tiger"],
    "colours": ["red", "blue", "green", "yellow", "white", "black", "orange", "purple", "pink", "brown"],
    "numbers": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
    "body": ["head", "hand", "foot", "eye", "ear", "nose", "mouth", "arm", "leg", "heart"],
    "food": ["bread", "milk", "meat", "fish", "rice", "apple", "egg", "cheese", "cake", "soup"],
    "nature": ["sun", "moon", "star", "sky", "sea", "river", "mountain", "tree", "flower", "rain"],
    "actions": ["run", "walk", "jump", "eat", "sleep", "read", "write", "sing", "dance", "swim"],
    "emotions": ["happy", "sad", "angry", "afraid", "love", "hate", "hope", "fear", "joy", "pain"],
    "sizes": ["big", "small", "tall", "short", "long", "wide", "thin", "thick", "deep", "high"],
    "opposites": [
        ("hot", "cold"), ("up", "down"), ("in", "out"), ("yes", "no"),
        ("good", "bad"), ("old", "new"), ("fast", "slow"), ("light", "dark"),
        ("true", "false"), ("start", "end"),
    ],
}

WORD_PAIRS = [
    # (word_a, word_b, relationship, expected_similarity)
    ("cat", "dog", "same_group", 0.8),
    ("cat", "fish", "same_group", 0.8),
    ("cat", "red", "different_group", 0.2),
    ("red", "blue", "same_group", 0.8),
    ("red", "cat", "different_group", 0.2),
    ("hot", "cold", "opposite", 0.3),
    ("up", "down", "opposite", 0.3),
    ("happy", "sad", "opposite", 0.3),
    ("happy", "joy", "synonym", 0.9),
    ("sad", "pain", "related", 0.7),
    ("big", "small", "opposite", 0.3),
    ("big", "tall", "related", 0.7),
    ("sun", "moon", "opposite", 0.3),
    ("sun", "star", "related", 0.7),
    ("run", "walk", "related", 0.7),
    ("run", "swim", "related", 0.6),
    ("head", "hand", "same_group", 0.8),
    ("bread", "milk", "same_group", 0.8),
    ("one", "two", "same_group", 0.8),
    ("cat", "happy", "different_group", 0.2),
    ("run", "red", "different_group", 0.2),
    ("sun", "happy", "related", 0.5),
    ("heart", "love", "related", 0.6),
    ("dark", "fear", "related", 0.6),
    ("fast", "run", "related", 0.7),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Training Session
# ═══════════════════════════════════════════════════════════════════════════════

def run_language_training():
    print("=" * 70)
    print("LANGUAGE TRAINING — Words as Data Objects")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test 3 encoding methods
    encoders = {
        "hash": word_to_24bit_hash,
        "letters": word_to_24bit_letters,
        "structural": word_to_24bit_structural,
    }

    # ═══ Part 1: Encode all words ═══
    print("PART 1: Word Encoding")
    print("-" * 40)

    all_words = set()
    for group_name, group_words in WORD_GROUPS.items():
        if group_name == "opposites":
            for a, b in group_words:
                all_words.add(a)
                all_words.add(b)
        else:
            all_words.update(group_words)
    for a, b, _, _ in WORD_PAIRS:
        if isinstance(a, str): all_words.add(a)
        if isinstance(b, str): all_words.add(b)

    word_data = {}
    for enc_name, enc_fn in encoders.items():
        word_data[enc_name] = {}
        for word in all_words:
            vec = enc_fn(word)
            snapped = golay_snap(vec)
            m = do_metrics(vec)
            word_data[enc_name][word] = {
                "vec": vec, "snapped": snapped,
                "hw": m["hw"], "nrci": m["nrci"],
                "bits_changed": sum(1 for i in range(24) if vec[i] != snapped[i]),
            }

        unique = len(set(tuple(d["snapped"]) for d in word_data[enc_name].values()))
        print(f"  {enc_name:12s}: {len(all_words)} words, {unique} unique vectors")

    # ═══ Part 2: Within-group similarity ═══
    print(f"\nPART 2: Within-Group Similarity")
    print("-" * 40)

    for enc_name in encoders:
        print(f"\n  [{enc_name}]")
        for group_name, group_words in WORD_GROUPS.items():
            if group_name == "opposites":
                pairs_to_check = [(a, b) for a, b in group_words]
            elif len(group_words) < 2:
                continue
            else:
                pairs_to_check = [(group_words[i], group_words[j]) for i in range(len(group_words)) for j in range(i+1, min(len(group_words), i+5))]
            and_nrcis = []
            for w1, w2 in pairs_to_check:
                    if w1 in word_data[enc_name] and w2 in word_data[enc_name]:
                        v1 = word_data[enc_name][w1]["vec"]
                        v2 = word_data[enc_name][w2]["vec"]
                        and_vec = do_and(v1, v2)
                        and_m = do_metrics(and_vec)
                        and_nrcis.append(and_m["nrci"])
            avg = sum(and_nrcis) / len(and_nrcis) if and_nrcis else 0
            print(f"    {group_name:12s}: avg AND_NRCI = {avg:.4f} ({len(and_nrcis)} pairs)")

    # ═══ Part 3: Cross-group distance ═══
    print(f"\nPART 3: Cross-Group Distance")
    print("-" * 40)

    for enc_name in encoders:
        print(f"\n  [{enc_name}]")
        groups = list(WORD_GROUPS.keys())
        for i in range(min(5, len(groups))):
            for j in range(i+1, min(5, len(groups))):
                g1_words = WORD_GROUPS[groups[i]][:3]
                g2_words = WORD_GROUPS[groups[j]][:3]
                cross_nrcis = []
                for w1 in g1_words:
                    for w2 in g2_words:
                        if w1 in word_data[enc_name] and w2 in word_data[enc_name]:
                            v1 = word_data[enc_name][w1]["vec"]
                            v2 = word_data[enc_name][w2]["vec"]
                            and_vec = do_and(v1, v2)
                            and_m = do_metrics(and_vec)
                            cross_nrcis.append(and_m["nrci"])
                avg = sum(cross_nrcis) / len(cross_nrcis) if cross_nrcis else 0
                print(f"    {groups[i]:10s} ↔ {groups[j]:10s}: avg AND_NRCI = {avg:.4f}")

    # ═══ Part 4: Word pair relationships ═══
    print(f"\nPART 4: Word Pair Relationships")
    print("-" * 40)

    for enc_name in encoders:
        print(f"\n  [{enc_name}]")
        print(f"  {'Pair':25s} {'Relation':15s} {'AND_NRCI':9s} {'XOR_HW':7s} {'Expected':9s}")
        for w1, w2, relation, expected in WORD_PAIRS:
            if w1 not in word_data[enc_name] or w2 not in word_data[enc_name]:
                continue
            v1 = word_data[enc_name][w1]["vec"]
            v2 = word_data[enc_name][w2]["vec"]
            and_vec = do_and(v1, v2)
            xor_vec = do_xor(v1, v2)
            and_m = do_metrics(and_vec)
            xor_m = do_metrics(xor_vec)
            print(f"  {w1:10s}-{w2:10s}  {relation:15s} {and_m['nrci']:9.4f} {sum(xor_vec):7d} {expected:9.2f}")

    # ═══ Part 5: Can we predict relationship from AND_NRCI? ═══
    print(f"\nPART 5: Predicting Relationships")
    print("-" * 40)

    try:
        import statistics

        for enc_name in encoders:
            same_group_nrcis = []
            diff_group_nrcis = []
            opposite_nrcis = []
            related_nrcis = []

            for w1, w2, relation, expected in WORD_PAIRS:
                if w1 not in word_data[enc_name] or w2 not in word_data[enc_name]:
                    continue
                v1 = word_data[enc_name][w1]["vec"]
                v2 = word_data[enc_name][w2]["vec"]
                and_m = do_metrics(do_and(v1, v2))

                if relation == "same_group":
                    same_group_nrcis.append(and_m["nrci"])
                elif relation == "different_group":
                    diff_group_nrcis.append(and_m["nrci"])
                elif relation == "opposite":
                    opposite_nrcis.append(and_m["nrci"])
                elif relation in ("related", "synonym"):
                    related_nrcis.append(and_m["nrci"])

            print(f"\n  [{enc_name}]")
            if same_group_nrcis:
                print(f"    Same group:     mean={statistics.mean(same_group_nrcis):.4f} (n={len(same_group_nrcis)})")
            if diff_group_nrcis:
                print(f"    Diff group:     mean={statistics.mean(diff_group_nrcis):.4f} (n={len(diff_group_nrcis)})")
            if opposite_nrcis:
                print(f"    Opposite:       mean={statistics.mean(opposite_nrcis):.4f} (n={len(opposite_nrcis)})")
            if related_nrcis:
                print(f"    Related/Syn:    mean={statistics.mean(related_nrcis):.4f} (n={len(related_nrcis)})")

            # Can we distinguish same_group from different_group?
            if same_group_nrcis and diff_group_nrcis:
                sep = statistics.mean(same_group_nrcis) - statistics.mean(diff_group_nrcis)
                print(f"    Separation (same - diff): {sep:+.4f}")

    except ImportError:
        print("  (statistics module not available)")

    # ═══ Part 6: Golay structure of words ═══
    print(f"\nPART 6: Golay Structure of Words")
    print("-" * 40)

    for enc_name in encoders:
        hw_dist = Counter()
        changed_count = 0
        for word, d in word_data[enc_name].items():
            hw_dist[d["hw"]] += 1
            if d["bits_changed"] > 0:
                changed_count += 1
        print(f"\n  [{enc_name}]")
        print(f"    Words needing Golay snap: {changed_count}/{len(all_words)}")
        print(f"    HW distribution: {dict(sorted(hw_dist.items()))}")

    # ═══ Save ═══
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_words": len(all_words),
        "n_pairs": len(WORD_PAIRS),
        "encoders": list(encoders.keys()),
        "word_groups": {k: v for k, v in WORD_GROUPS.items()},
        "word_pairs": WORD_PAIRS,
        "results": {},
    }
    for enc_name in encoders:
        output["results"][enc_name] = {
            "n_unique": len(set(tuple(d["snapped"]) for d in word_data[enc_name].values())),
            "sample_encodings": {
                word: {"hw": d["hw"], "nrci": round(d["nrci"], 4)}
                for word, d in list(word_data[enc_name].items())[:5]
            },
        }

    out_path = LTM_DIR / "language_training.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved to {out_path}")

    return output


if __name__ == "__main__":
    run_language_training()
