#!/usr/bin/env python3
"""Round 39 — scan Rule 30's period-32 regime at the level of eventual patterns.

The proved laws (Lean: `one_bit_reset`, `ldiag_evPer_of_not_white`, `white_iff_coincide`) say
that, between two eventually white left diagonals, the eventual pattern of diagonal D + 2 is a
function of the patterns of D and D + 1 (the map F below).  So once the patterns of two adjacent
diagonals are known exactly, the following diagonals can be computed at O(Q) cost each, with no
run of the automaton, until the next white diagonal appears.

This script:
  1. runs the automaton exactly (left half-line, packed bits) far enough to read the eventual
     patterns of diagonals 87867 and 87868 (the first period-32 diagonal and its neighbour);
  2. checks F against the automaton on diagonal 87869;
  3. iterates F, stopping at a white diagonal (the next one) or at a return to the start state
     (which would make the left side periodic in D for ever, `regime_periodic`).

`ldiag_infinitely_many_white` (Lean) guarantees that a white diagonal comes eventually (within
4^32 + 1 diagonals); the exhaustive regime statistics (`rule30_engine_r39.py`) put the typical gap
near 2^32.  Run: python3 regime_scan.py [steps]   (default 3·10^8, about 40 minutes)
Writes regime_scan.json.
"""

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent / "rule30_round38"))

import hypothesis_engine as he  # noqa: E402  (the Round 38 exact observatory)


def F(A: int, B: int, Q: int) -> int:
    """Eventual pattern of diagonal D+2 from those of D (A) and D+1 (B), period Q, B ≠ 0.
    Patterns are Q-bit integers indexed by absolute phase t mod Q.  Starting at a phase where B
    is black the machine is reset (`one_bit_reset`), so the periodic output is unique."""
    phi = (B & -B).bit_length() - 1
    x = 1 - ((A >> phi) & 1)
    ph = (phi + 1) % Q
    C = 0
    for _ in range(Q):
        C |= x << ph
        x = ((A >> ph) & 1) ^ (((B >> ph) & 1) | x)
        ph = (ph + 1) % Q
    return C


def reduce_pattern(pat: int, Q: int, M: int = 64) -> int:
    out = 0
    for ph in range(Q):
        out |= ((pat >> ph) & 1) << ph
    for ph in range(M):
        assert ((pat >> ph) & 1) == ((pat >> (ph % Q)) & 1), "pattern does not have period Q"
    return out


def scan(start: int = 87867, Q: int = 32, steps: int = 300_000_000, log=print) -> dict:
    t0 = time.time()
    p = he.left_profile(start + 3, pmax=64, tmax=2 * (start + 3) + 512)
    A, B = reduce_pattern(p.pattern[start], Q), reduce_pattern(p.pattern[start + 1], Q)
    assert F(A, B, Q) == reduce_pattern(p.pattern[start + 2], Q), "F disagrees with the automaton"
    log(f"exact patterns read in {time.time() - t0:.1f}s; F agrees with the automaton at "
        f"D = {start + 2}")
    s0 = (A, B)
    a, b, D = A, B, start + 1
    result = {"start": start, "Q": Q, "steps": steps, "white": None, "return": None}
    t1 = time.time()
    for k in range(1, steps + 1):
        a, b = b, F(a, b, Q)
        D += 1
        if b == 0:
            result["white"] = {"D": D, "outer_parity": bin(a).count("1") % 2}
            break
        if (a, b) == s0:
            result["return"] = k
            break
        if k % 50_000_000 == 0:
            log(f"  … {k} diagonals, no white yet ({time.time() - t1:.0f}s)")
    result["last_D"] = D
    result["seconds"] = round(time.time() - t1, 1)
    return result


def emit(start: int, Q: int) -> tuple:
    """Exact eventual patterns of diagonals start, start+1 (hex), checked against F once."""
    p = he.left_profile(start + 3, pmax=64, tmax=2 * (start + 3) + 512)
    A, B = reduce_pattern(p.pattern[start], Q), reduce_pattern(p.pattern[start + 1], Q)
    assert F(A, B, Q) == reduce_pattern(p.pattern[start + 2], Q)
    return format(A, "x"), format(B, "x")


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--emit":
    # python3 regime_scan.py --emit START Q   → arguments for ./regime_scan
    st, q = int(sys.argv[2]), int(sys.argv[3])
    print(q, *emit(st, q), st)
    sys.exit(0)

if __name__ == "__main__":
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 300_000_000
    res = scan(steps=steps, log=lambda *a: print(*a, flush=True))
    print(res, flush=True)
    (HERE / "regime_scan.json").write_text(json.dumps(res, indent=1))
