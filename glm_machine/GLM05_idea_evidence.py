# ══════════════════════════════════════════════════════════════════════════════
# §05  IDEA EVIDENCE  — source-tagged (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class IdeaEvidence:
    """
    The fundamental unit of evidence within an Idea Zone.
    Tracks the origin, resonance, and geometric fit of a concept.
    """
    word: str
    vector: List[int]
    role: str
    nrci: float
    turn: int
    resonance: float
    fit: str            # "reinforce" | "drift" | "seed" | "inferred"
    source: str = "user"  # "user" | "inferred" | "computed" | "kb"

# ── 2. ISOLATION TEST ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Module 05: Idea Evidence ===")
    try:
        # Create a dummy evidence point
        test_vec = [0, 1] * 12
        ev = IdeaEvidence(
            word="hamiltonian",
            vector=test_vec,
            role="NOUN",
            nrci=0.85,
            turn=1,
            resonance=1.0,
            fit="seed",
            source="user"
        )
        print(f"✅ Success: Created evidence for '{ev.word}' (Source: {ev.source})")
        print(f"   Vector Length: {len(ev.vector)} bits")
    except Exception as e:
        print(f"❌ Failed: {e}")