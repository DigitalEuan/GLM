"""The corrected, working pipeline assembled from the verified pieces.

    encode   : grid -> 24-bit word                         (tasks.grid_to_word)
    measure  : Golay syndrome, coset leader, parity       (golay.*)
    layer    : exact parity rule instead of a learned head (leech.hits_parity_wall)
    embed    : 8x embedding, always a Leech point          (leech.embed8)
    junction : exact Lambda/2Lambda label (syndrome, wt%4) (leech.junction_label)
    operate  : F_2 XOR analogy for coordinatewise rules, learned cell permutation for
               permutation rules (analogy.xor_analogy / analogy.learn_permutation)
"""
from __future__ import annotations
from typing import Dict, List, Sequence, Tuple

from . import analogy, golay, leech, tasks


def measure(word: int) -> Dict:
    cw, err = golay.decode(word)
    return {
        "popcount": golay.popcount(word),
        "parity": golay.popcount(word) % 2,
        "syndrome": golay.syndrome(word),
        "nearest_codeword": cw,
        "distance_to_code": golay.popcount(err),
        "is_codeword": err == 0,
        "hits_parity_wall_4x": leech.hits_parity_wall(word),
        "leech_point_8x": leech.embed8(word),
        "junction": leech.junction_label(word),
    }


def solve(demos: Sequence[Tuple[tasks.Grid, tasks.Grid]], query: tasks.Grid):
    """Infer a rule from demonstration pairs and apply it to the query.

    Returns (prediction grid or None, rule name).
    All rules consistent with every demo are kept as a superposition of hypotheses:
      1. constant XOR displacement (toggle, any XOR-mask rule)
      2. a geometric cell permutation from `analogy.permutation_library` consistent with all
         demos (reflect_v, translate-as-shift, ...)
      3. (fallback) any cell permutation uniquely determined by the demos
    An answer is returned only if all surviving hypotheses agree on the query; otherwise the
    result is "ambiguous:<hypotheses>" and more demonstrations are needed.
    Use at least 2 demonstrations: with one demo every rule has a constant XOR displacement.
    """
    H, W = len(query), len(query[0])
    flat = [(tasks.flatten(x), tasks.flatten(y)) for x, y in demos]
    q = tasks.flatten(query)
    hypotheses = {}                       # rule name -> predicted flat output
    deltas = {tuple(a ^ b for a, b in zip(x, y)) for x, y in flat}
    if len(deltas) == 1:
        d = next(iter(deltas))
        hypotheses["xor_displacement"] = tuple(a ^ b for a, b in zip(q, d))
    for name, p in analogy.consistent_permutations(flat, H, W).items():
        hypotheses["permutation:" + name] = tuple(analogy.permute_op(q, p))
    if not hypotheses:
        perm = analogy.learn_permutation(flat)
        if perm is not None:
            hypotheses["cell_permutation"] = tuple(analogy.permute_op(q, perm))
    if not hypotheses:
        return None, "unsolved"
    outs = set(hypotheses.values())
    rule = "|".join(sorted(hypotheses))
    if len(outs) == 1:          # every surviving hypothesis agrees: the superposition collapses
        out = list(next(iter(outs)))
        return [out[r * W:(r + 1) * W] for r in range(H)], rule
    return None, "ambiguous:" + rule
