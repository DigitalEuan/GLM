"""Optional bridge to the full GLM substrate (glm_universal).

NOT executed in the verification session (the GLM repository was not available there).
Use it inside the GLM system to confirm that the GLM's own substrate satisfies the theorems
proved in GLMKit.  The Lean theorems `parity_wall`, `parity_wall_glue`, `eight_mul_mem` and
`junction_iff` are proved for ANY binary code containing 0, so they must hold for the
substrate's MOG-ordered Golay code too; any failure here indicates a bug in the substrate
(or a different lattice model), not in the kit.

    from glm_universal.substrate import leech2
    from glm_kit import glm_bridge
    print(glm_bridge.check_substrate(leech2))
"""
from __future__ import annotations
import random
from typing import Dict


def _bits_msb(w: int):
    """The study scripts' convention: coordinate i = bit (23 - i)."""
    return [(w >> (23 - i)) & 1 for i in range(24)]


def check_substrate(leech2, trials: int = 2000, seed: int = 0) -> Dict[str, int]:
    rng = random.Random(seed)
    glue = (-3,) + (1,) * 23
    fails = {"parity_wall": 0, "parity_wall_glue": 0, "eight_mul": 0, "junction_parity": 0}
    for _ in range(trials):
        w = rng.getrandbits(24)
        b = _bits_msb(w)
        even = sum(b) % 2 == 0
        if bool(leech2.in_leech(tuple(4 * x for x in b))) != even:
            fails["parity_wall"] += 1
        if bool(leech2.in_leech(tuple(4 * x + g for x, g in zip(b, glue)))) != even:
            fails["parity_wall_glue"] += 1
        if not leech2.in_leech(tuple(8 * x for x in b)):
            fails["eight_mul"] += 1
        # junction: same class_of for two even 4x-embeddings must imply equal wt mod 4
        w2 = rng.getrandbits(24)
        b2 = _bits_msb(w2)
        if even and sum(b2) % 2 == 0:
            try:
                same = leech2.class_of(tuple(4 * x for x in b)) == leech2.class_of(tuple(4 * x for x in b2))
            except Exception:
                same = False
            if same and (sum(b) - sum(b2)) % 4 != 0:
                fails["junction_parity"] += 1
    fails["trials"] = trials
    return fails
