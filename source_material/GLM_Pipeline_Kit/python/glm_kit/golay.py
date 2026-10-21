"""Binary Golay code G24 (Lean: GLMKit/Golay.lean)."""
from __future__ import annotations
from functools import lru_cache
from itertools import combinations
from typing import Dict, List, Tuple

N = 24
GEN_POLY = 0xC75          # x^11+x^10+x^6+x^5+x^4+x^2+1, generator of cyclic G23
ALL_ONES = (1 << N) - 1


def popcount(w: int) -> int:
    return bin(w & ALL_ONES).count("1")


def extend_parity(w: int) -> int:
    """Append the overall parity bit (coordinate 23)."""
    return w | ((popcount(w) & 1) << 23)


ROWS: List[int] = [extend_parity(GEN_POLY << i) for i in range(12)]


@lru_cache(maxsize=1)
def codewords() -> Tuple[int, ...]:
    code = [0]
    for r in ROWS:
        code = code + [c ^ r for c in code]
    return tuple(code)


@lru_cache(maxsize=1)
def codeword_set() -> frozenset:
    return frozenset(codewords())


def syndrome(w: int) -> int:
    """12-bit syndrome.  G24 is self-dual, so the generator rows are also parity checks."""
    s = 0
    for k, r in enumerate(ROWS):
        s |= (popcount(w & r) & 1) << k
    return s


def is_codeword(w: int) -> bool:
    return 0 <= w <= ALL_ONES and syndrome(w) == 0


@lru_cache(maxsize=1)
def leader_table() -> Dict[int, int]:
    """Syndrome -> minimum-weight coset leader (weights 0..4; 4096 cosets)."""
    table: Dict[int, int] = {}
    for wt in range(5):
        for pos in combinations(range(N), wt):
            e = 0
            for p in pos:
                e |= 1 << p
            s = syndrome(e)
            if s not in table:
                table[s] = e
        if len(table) == 4096:
            break
    return table


def decode(w: int) -> Tuple[int, int]:
    """Nearest-codeword decoding: returns (codeword, error pattern)."""
    e = leader_table()[syndrome(w)]
    return w ^ e, e


def octads() -> List[int]:
    return [c for c in codewords() if popcount(c) == 8]


def weight_enumerator() -> Dict[int, int]:
    out: Dict[int, int] = {}
    for c in codewords():
        out[popcount(c)] = out.get(popcount(c), 0) + 1
    return dict(sorted(out.items()))
