"""``glm_universal.reasoning.shortest_tag`` -- how many tag bits a tie needs
(Phase 135).

The question
------------
Phase 133 gave the carrier a seven-bit sender tag; Phase 134 protected it with
an eleven-bit and a fifteen-bit tag that absorb one and two flipped tag bits
(``reasoning/carrier_read.py``).  Phase 134 ended on the line "tags shorter
than eleven or fifteen bits were not searched for" (``STATUS.md`` §2.2).
``studies/SHORTEST_TAG_STUDY.md`` declared the marks this module measures.

What is proved (``RequestProject/GLM/ShortestTag.lean``)
---------------------------------------------------------
A tag stage of radius ``s`` resolves every tie when every octad's tag has
weight ``D > 2s`` (``mtag_separation``).  How short can such a tag be?

* ``tag_length_floor`` -- every parity tag with octad weight ``>= D >= 1`` has
  ``r >= D + 6`` bits.  So the seven-bit tag is the shortest that resolves
  every tie (``tag7_shortest``), and a tag correcting one (two) flipped tag
  bits needs at least nine (eleven) bits.
* ``protected_tags_shortest_of_shape`` -- a tag built as parities of a seven-bit
  tag (both protected tags are) needs eleven bits for ``D = 3`` and fifteen
  for ``D = 5``; the protected tags meet both.

What is not proved, and is measured here
----------------------------------------
Whether a tag *not* built on seven bits fills the gap (nine or ten bits for
``D = 3``, eleven to fourteen for ``D = 5``).  :func:`gap_search` runs a
deterministic local search over all 4,096 tag functionals (every functional
on the code is realised by a mask on the twelve low coordinates) and reports
the least *deficit* it reached, ``sum over octads of max(0, D - weight)``.
A deficit of zero would be a shorter tag; a positive deficit is a search
that failed, never a proof that none exists.  The same search is run on the
three lengths the constructions show possible, as its control.

Exactness
---------
``int`` masks and bit-sets only.  No float, no RNG: the search's choices come
from a fixed integer recurrence, so every run reproduces the last.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.mog import GOLAY_MASKS
from . import carrier_read as crd
from . import designed_substrate as dsub

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "FLOOR_GENERAL", "FLOOR_BUILT",
    "octads", "tag_weights", "min_octad_weight", "built_on_seven",
    "seven_bit_values", "kernel_census", "deficit", "local_search",
    "functional_rank",
    "gap_search", "s2_constructions", "s3_kernel", "s4_onto",
    "shortest_tag_report",
]

N = 24
LEAN_FILE = "RequestProject/GLM/ShortestTag.lean"

#: The theorems of ``RequestProject/GLM/ShortestTag.lean`` (mark S1).
LEAN_THEOREMS: Tuple[str, ...] = (
    "two_mul_card_mem_le", "octadFree_avoiding_card_le", "kernel_card_ge",
    "short_tag_kills_octad", "short_mtag_kills_octad", "tag_length_floor",
    "tag7_shortest", "protected_tag_floors", "octadFree_closed_card_le",
    "tag7_value_is_octad_value", "tag7_octads_onto", "built_tag_packing",
    "first_moment", "no_even_15_7_6", "no_14_7_5", "built_tag_floor",
    "tag11_built", "tag15_built", "protected_tags_shortest_of_shape",
)

#: The proved floor for every parity tag: octad weight ``D`` needs ``D + 6``.
FLOOR_GENERAL: Dict[int, int] = {1: 7, 3: 9, 5: 11}

#: The proved floor for tags built as parities of a seven-bit tag; met by the
#: seven-bit tag and the two protected tags.
FLOOR_BUILT: Dict[int, int] = {1: 7, 3: 11, 5: 15}

#: The lengths the search is asked about: the gap between the two floors.
GAP: Dict[int, Tuple[int, ...]] = {3: (9, 10), 5: (11, 12, 13, 14)}

_LCG_A, _LCG_C, _LCG_M = 1103515245, 12345, 1 << 31


def _popcount(x: int) -> int:
    return bin(x).count("1")


@lru_cache(maxsize=1)
def octads() -> Tuple[int, ...]:
    """The 759 octads of the GLM's code, as 24-bit masks."""
    return tuple(c for c in GOLAY_MASKS if _popcount(c) == 8)


def tag_weights(masks: Sequence[int]) -> Tuple[int, ...]:
    """The weight of every octad's tag through ``masks``."""
    return tuple(_popcount(crd.mtag(o, masks)) for o in octads())


def min_octad_weight(masks: Sequence[int]) -> int:
    return min(tag_weights(masks))


def built_on_seven(masks: Sequence[int]) -> Optional[Tuple[int, ...]]:
    """If every mask after the first seven is the exclusive-or of some of the
    first seven, the selector of each (bit ``j`` set when tag mask ``j`` is
    used); otherwise ``None``.  The Lean file's ``selRows11``/``selRows15``."""
    base = tuple(masks[:7])
    table = {}
    for s in range(1, 128):
        x = 0
        for j in range(7):
            if s >> j & 1:
                x ^= base[j]
        table.setdefault(x, s)
    rows = tuple(1 << j for j in range(7))
    for m in masks[7:]:
        if m not in table:
            return None
        rows += (table[m],)
    return rows


def seven_bit_values() -> Dict[int, int]:
    """How many octads take each value of the seven-bit tag."""
    out: Dict[int, int] = {}
    for o in octads():
        t = dsub.tag(o)
        out[t] = out.get(t, 0) + 1
    return out


def kernel_census() -> Dict[str, int]:
    """The kernel of the seven-bit tag on the code: its size, its octads, and
    the size of its part avoiding coordinate 0 (the Plotkin step's set)."""
    kernel = [c for c in GOLAY_MASKS if dsub.tag(c) == 0]
    return {
        "kernel": len(kernel),
        "kernel_octads": sum(1 for c in kernel if _popcount(c) == 8),
        "avoiding_coordinate_0": sum(1 for c in kernel if not c & 1),
        "plotkin_cap": 24,
        "kernel_weights": sorted({_popcount(c) for c in kernel}),
    }


# ---------------------------------------------------------------------------
# The search
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _functionals() -> Tuple[int, ...]:
    """The hit-set over the 759 octads of every nonzero functional on the
    code, realised by the masks ``1 .. 4095`` on the twelve low coordinates
    (bit ``i`` set when octad ``i`` has odd overlap with the mask)."""
    octs = octads()
    out = []
    for m in range(1, 1 << 12):
        h = 0
        for i, o in enumerate(octs):
            if _popcount(o & m) & 1:
                h |= 1 << i
        out.append(h)
    return tuple(out)


_ALL = (1 << 759) - 1


def _planes(hits: Sequence[int], d: int) -> List[int]:
    """``planes[k]`` is the set of octads hit at least ``k + 1`` times."""
    planes = [0] * d
    for h in hits:
        for k in range(d - 1, 0, -1):
            planes[k] |= planes[k - 1] & h
        planes[0] |= h
    return planes


def deficit(hits: Sequence[int], d: int) -> int:
    """``sum over octads of max(0, d - number of hits)``."""
    return sum(759 - _popcount(p) for p in _planes(hits, d))


def _best_replacement(others: Sequence[int], d: int,
                      funcs: Sequence[int]) -> Tuple[int, int]:
    base = _planes(others, d)
    best, best_j = None, 0
    for j, h in enumerate(funcs):
        total = 759 - _popcount(base[0] | h)
        for k in range(1, d):
            total += 759 - _popcount(base[k] | (base[k - 1] & h))
        if best is None or total < best:
            best, best_j = total, j
    return best, best_j


def local_search(r: int, d: int, moves: int, seed: int = 1) -> Dict[str, object]:
    """Annealed single-bit replacement: from a recurrence-chosen start, replace
    one tag bit by a recurrence-chosen functional, keep the change if the
    deficit does not rise, and otherwise keep it with probability about
    ``2 ** (-1.44 * rise / T)`` (integer arithmetic), the temperature ``T``
    falling linearly from 2 to 0.05 over ``moves`` proposals.  Returns the
    least deficit reached and the low-coordinate masks reaching it."""
    funcs = _functionals()
    x = seed

    def nxt() -> int:
        nonlocal x
        x = (_LCG_A * x + _LCG_C) % _LCG_M
        return x >> 8

    state = [nxt() % len(funcs) for _ in range(r)]
    cur = deficit([funcs[j] for j in state], d)
    best, best_state = cur, list(state)
    for step in range(moves):
        if best == 0:
            break
        i, j = nxt() % r, nxt() % len(funcs)
        old = state[i]
        state[i] = j
        val = deficit([funcs[k] for k in state], d)
        rise = val - cur
        if rise <= 0:
            cur = val
        else:
            t100 = 5 + (195 * (moves - step)) // moves      # T in hundredths
            bits = -(-rise * 144 // t100)                    # ceil(1.44 rise / T)
            if bits < 16 and nxt() % 65536 < (65536 >> bits):
                cur = val
            else:
                state[i] = old
        if cur < best:
            best, best_state = cur, list(state)
    return {"r": r, "d": d, "moves": moves, "seed": seed,
            "least_deficit": best,
            "masks": tuple(j + 1 for j in best_state)}


def functional_rank(masks: Sequence[int]) -> int:
    """The rank over GF(2) of a tag's functionals, given as low-coordinate
    masks (``1 .. 4095``): 7 for a tag built on a seven-bit tag."""
    rows: List[int] = []
    for m in masks:
        x = m
        for b in rows:
            x = min(x, x ^ b)
        if x:
            rows.append(x)
    return len(rows)


def gap_search(moves: int = 2_000_000,
               seeds: Sequence[int] = (1, 2, 3)) -> Dict[str, object]:
    """S5 and S6: the search on the gap lengths and, as its control, on the
    three lengths the constructions reach."""
    out: Dict[str, object] = {"moves": moves, "seeds": tuple(seeds),
                              "gap": {}, "control": {}}
    for d, rs in GAP.items():
        for r in rs:
            runs = [local_search(r, d, moves, s) for s in seeds]
            out["gap"][f"D{d}_r{r}"] = min(t["least_deficit"] for t in runs)
    for d, r in FLOOR_BUILT.items():
        runs = [local_search(r, d, moves, s) for s in seeds]
        found = [t for t in runs if t["least_deficit"] == 0]
        out["control"][f"D{d}_r{r}"] = {
            "found": len(found), "of": len(runs),
            "ranks": tuple(functional_rank(t["masks"]) for t in found),
            "verified": all(min_octad_weight(t["masks"]) >= d for t in found)}
    return out


# ---------------------------------------------------------------------------
# The marks
# ---------------------------------------------------------------------------

def s2_constructions() -> Dict[str, object]:
    """S2: the three constructions meet the built floor exactly, and both
    protected tags are built on the seven-bit tag."""
    w7 = min_octad_weight(dsub.TAG_MASKS)
    w11 = min_octad_weight(crd.TAG11_MASKS)
    w15 = min_octad_weight(crd.TAG15_MASKS)
    sel11 = built_on_seven(crd.TAG11_MASKS)
    sel15 = built_on_seven(crd.TAG15_MASKS)
    lean = _lean_text()
    out = {
        "min_weight": (w7, w11, w15),
        "lengths": (len(dsub.TAG_MASKS), len(crd.TAG11_MASKS),
                    len(crd.TAG15_MASKS)),
        "sel11": sel11, "sel15": sel15,
        "sel_in_lean": (lean is not None and sel11 is not None
                        and sel15 is not None
                        and _lean_rows(lean, "selRows11") == sel11
                        and _lean_rows(lean, "selRows15") == sel15),
    }
    out["passed"] = (out["min_weight"] == (1, 3, 5)
                     and out["lengths"] == (FLOOR_BUILT[1], FLOOR_BUILT[3],
                                            FLOOR_BUILT[5])
                     and out["sel_in_lean"])
    return out


def s3_kernel() -> Dict[str, object]:
    """S3: the Plotkin step on the seven-bit tag's own kernel: 32 codewords,
    no octad, and at most 24 of them avoid any one coordinate."""
    out = kernel_census()
    worst = 0
    kernel = [c for c in GOLAY_MASKS if dsub.tag(c) == 0]
    for j in range(N):
        worst = max(worst, sum(1 for c in kernel if not c >> j & 1))
    out["most_avoiding_one_coordinate"] = worst
    out["passed"] = (out["kernel"] == 32 and out["kernel_octads"] == 0
                     and worst <= 24)
    return out


def s4_onto() -> Dict[str, object]:
    """S4: the seven-bit tag takes every one of its 127 nonzero values on the
    octads (``tag7_octads_onto``), with the multiplicities measured."""
    values = seven_bit_values()
    mult = sorted(set(values.values()))
    out = {"values": len(values), "zero_taken": 0 in values,
           "multiplicities": mult,
           "passed": len(values) == 127 and 0 not in values}
    return out


def _lean_text() -> Optional[str]:
    path = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _lean_rows(text: str, name: str) -> Optional[Tuple[int, ...]]:
    import re
    m = re.search(rf"def {name} : List ℕ :=\s*\[([^\]]*)\]", text)
    if not m:
        return None
    return tuple(int(v) for v in m.group(1).replace("\n", " ").split(","))


def s1_lean() -> Dict[str, object]:
    text = _lean_text()
    present = (text is not None
               and all(f"theorem {n}" in text for n in LEAN_THEOREMS))
    return {"present": present,
            "sorry_free": text is not None and "sorry" not in text,
            "passed": present and text is not None and "sorry" not in text}


def shortest_tag_report(moves: int = 2_000_000,
                        seeds: Sequence[int] = (1, 2, 3)) -> Dict[str, object]:
    """Every mark of ``studies/SHORTEST_TAG_STUDY.md``."""
    s1, s2, s3, s4 = s1_lean(), s2_constructions(), s3_kernel(), s4_onto()
    s5 = gap_search(moves, seeds)
    s5_control = all(v["found"] >= 1 and v["verified"]
                     for v in s5["control"].values())
    s6_gap_none = all(v > 0 for v in s5["gap"].values())
    marks = {"S1": s1["passed"], "S2": s2["passed"], "S3": s3["passed"],
             "S4": s4["passed"], "S5": s5_control, "S6": s6_gap_none}
    return {"S1": s1, "S2": s2, "S3": s3, "S4": s4, "S5": s5,
            "floor_general": dict(FLOOR_GENERAL),
            "floor_built": dict(FLOOR_BUILT), "marks": marks}
