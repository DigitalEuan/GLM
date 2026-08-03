# ══════════════════════════════════════════════════════════════════════════════
# §04  NUMBER VOCABULARY  — derived number-word lattice points (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional

# Import from Master Substrate
from GLM01_substrate import (
    WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category
)

# ── 1. CONSTANTS ───────────────────────────────────────────────────────
_BASE_CHAIN = ["zero", "one", "two", "three", "four"]
_EXTEND = ["five", "six", "seven", "eight", "nine", "ten",
           "eleven", "twelve", "thirteen", "fourteen", "fifteen",
           "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
_TENS = ["thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_BIT_SEQ = [5, 11, 17, 23, 7, 13, 19, 3, 9, 15, 21, 1, 6, 12, 18, 4,
            10, 16, 22, 8, 14, 20, 2, 0]

NUMBER_WORDS: Dict[int, str] = {
    0:"zero",1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",
    8:"eight",9:"nine",10:"ten",11:"eleven",12:"twelve",13:"thirteen",
    14:"fourteen",15:"fifteen",16:"sixteen",17:"seventeen",18:"eighteen",
    19:"nineteen",20:"twenty",30:"thirty",40:"forty",50:"fifty",
    60:"sixty",70:"seventy",80:"eighty",90:"ninety",100:"hundred",1000:"thousand",
}

# ── 2. PERTURBATION LOGIC ──────────────────────────────────────────────
def _perturb(vec: List[int], bits: List[int]) -> List[int]:
    """Flip specific bits in a 24-bit vector to create a related concept."""
    out = list(vec)
    for b in bits: 
        out[b % 24] ^= 1
    return out

# ── 3. INJECTION ENGINE ────────────────────────────────────────────────
def inject_number_vocab(vocab: Any) -> Dict[str, Any]:
    """Inject derived number-word vectors into the live engine vocabulary.
    
    Hardening: Handles both dict-based and class-based vocab containers.
    """
    report = {"injected": 0, "skipped": 0, "derived": []}
    
    # Determine if vocab is a dict or an object with a .words attribute
    target_dict = vocab.words if hasattr(vocab, 'words') else vocab
    
    # Ensure base number words exist in the vocabulary, pre-seeding them if missing
    DEFAULT_BASE = {
        "zero":  [0]*24,
        "one":   [1] + [0]*23,
        "two":   [1,1] + [0]*22,
        "three": [1,1,1] + [0]*21,
        "four":  [1,1,1,1] + [0]*20,
    }
    for w, vec in DEFAULT_BASE.items():
        if w not in target_dict:
            snapped, snap_info = GOLAY_ENGINE.snap_to_codeword(vec)
            fold3 = BLA.fold24_to3(vec)
            try: nrci = float(LEECH_ENGINE.calculate_nrci(vec))
            except Exception: nrci = 0.5
            target_dict[w] = WordEntry(
                word=w, vector=vec, role="NOUN", ubp_id=f"NUM_{w.upper()}",
                hamming_to_system=0, nrci=nrci, golay_codeword=snapped,
                golay_distance=snap_info["anchor_distance"], fold3=fold3,
                mog_category=_get_mog_category(vec)
            )
            if hasattr(vocab, 'by_role'):
                vocab.by_role.setdefault("NOUN", []).append(w)
            report["injected"] += 1
            report["derived"].append(w)

    # Check if we have the base chain to start from
    base_vecs = {w: list(target_dict[w].vector) for w in _BASE_CHAIN if w in target_dict}
    if not base_vecs:
        return report

    derived = {}
    prev_vec = base_vecs.get("four", base_vecs.get("zero"))
    
    # Derive 5-20
    for i, word in enumerate(_EXTEND):
        bit = _BIT_SEQ[i % len(_BIT_SEQ)]
        new_vec = _perturb(prev_vec, [bit])
        derived[word] = new_vec
        prev_vec = new_vec
        
    # Derive Tens (30-90)
    for i, ten in enumerate(_TENS):
        unit_idx = (i + 3) % len(_EXTEND)
        unit_vec = derived.get(_EXTEND[unit_idx], prev_vec)
        derived[ten] = _perturb(unit_vec, [_BIT_SEQ[i], _BIT_SEQ[i + 8]])
        
    # Derive Large Scales
    derived["hundred"] = _perturb(base_vecs.get("zero", [0]*24), [0,4,8,12,16,20])
    derived["thousand"] = _perturb(base_vecs.get("zero", [0]*24), [2,6,10,14,18,22])
    
    # Derive Negatives
    for word, vec in list(derived.items()) + list(base_vecs.items()):
        derived[f"minus_{word}"] = [1 - b for b in vec]
        
    # Commit to Vocab
    for word, vec in derived.items():
        if word in target_dict: 
            report["skipped"] += 1
            continue
            
        snapped, snap_info = GOLAY_ENGINE.snap_to_codeword(vec)
        fold3 = BLA.fold24_to3(vec)
        try: 
            nrci = float(LEECH_ENGINE.calculate_nrci(vec))
        except Exception: 
            nrci = 0.5
            
        entry = WordEntry(
            word=word, vector=vec, role="NOUN", ubp_id=f"NUM_{word}",
            hamming_to_system=0, nrci=nrci, golay_codeword=snapped,
            golay_distance=snap_info["anchor_distance"], fold3=fold3,
            mog_category=_get_mog_category(vec)
        )
        
        target_dict[word] = entry
        
        # Update by_role if it exists
        if hasattr(vocab, 'by_role'):
            vocab.by_role.setdefault("NOUN", []).append(word)
            
        report["injected"] += 1
        report["derived"].append(word)
        
    return report

# ── 4. ISOLATION TEST ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Module 04: Number Vocabulary ===")
    
    # 1. Create a mock vocabulary with the required base chain
    class MockVocab:
        def __init__(self):
            self.words = {}
            # Seed with dummy base vectors (all 0s or 1s for simplicity)
            for w in _BASE_CHAIN:
                self.words[w] = WordEntry(w, [0]*24, "NOUN", f"BASE_{w}")

    mock = MockVocab()
    
    try:
        res = inject_number_vocab(mock)
        print(f"✅ Success: Injected {res['injected']} numbers.")
        print(f"   Sample: 'ten' is grounded? {'ten' in mock.words}")
        print(f"   Sample: 'minus_hundred' is grounded? {'minus_hundred' in mock.words}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()