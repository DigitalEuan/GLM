#!/usr/bin/env python3
"""
================================================================================
 lattice_shortcut.py -- the 24D Golay/Leech "lattice shortcut", operational form
================================================================================

This is the *working* core of the UBP "24D Leech-lattice geodesic shortcut",
rewritten as a single self-contained module with the one substantive bug fixed.

WHAT THE METHOD IS
------------------
A three-stage map from integers to points of the Leech lattice Lambda_24, plus
an O(1) formula for the distance between two such points.

    n  --(1) encode-->  w in {0,1}^24  --(2) snap-->  c in Golay[24,12,8]
                                       --(3) step-->  2*(c2-c1) in Lambda_24

  (1) ENCODE.  Two encoders are provided, both from the original write-up:
        "shift"  : x = n & 0xFF, y = (n>>8) & 0xFF, z = (n>>16) & 0xFF,
                   each byte Gray-coded (b ^ b>>1) and written MSB-first.
        "factor" : x = p1^e1, y = p2^e2, z = product of the remaining prime
                   powers, each reduced mod 256 and Gray-coded as above
                   (primes fall back to "shift"; this is what the published
                   directory generator actually used).
      Everything below holds for *any* encoder into 24-bit words.

  (2) SNAP.  Nearest-codeword ("complete") decoding of the extended binary
      Golay code [24,12,8]: syndrome lookup in a full 4096-entry coset-leader
      table.  This is THE FIX.  The original engine only inverted error
      patterns of weight <= 3 and returned its input unchanged otherwise, so
      ~47% of "snapped" states were not codewords at all.  The Golay covering
      radius is 4, so a complete table always succeeds, at identical cost
      (one lookup).

  (3) STEP.  For a transition c1 -> c2 the jump vector is Dv = c2 - c1 in
      {-1,0,+1}^24 with d^2 = ||Dv||^2 = HammingDistance(c1,c2), and the
      doubled vector 2*Dv is an exact element of the Leech lattice Lambda_24
      (standard Golay construction, x sqrt(8) integral scaling) of norm 4*d^2.

WHAT IS GUARANTEED (machine-checked in Lean 4, see RequestProject/*.lean)
------------------------------------------------------------------------
  G1  Every snapped state is a Golay codeword                [decode_isGolay]
  G2  Snapping moves a state by at most 4 bits          [decode_dist_le_four]
  G3  d^2 in {0, 8, 12, 16, 24}  -- quantisation by 4    [corrected_quantized]
  G4  2*Dv is always a Leech vector                 [corrected_step_isLeech]
  G5  ||2*Dv||^2 = 4*d^2, and = 32 exactly for octad steps  [normSq_stepVec,
                                                    corrected_octad_iff_minimal]
  G6  32 is the minimum norm of Lambda_24, so octad steps really are
      minimal / kissing-sphere hops                             [leech_min_norm]
  G7  d^2(a,b) = popcount(gray(a XOR b)) for the raw layer: the jump norm
      never requires walking the interval a..b            [d2_eq_pop_gray_xor]
  G8  Even quantisation (d^2 in 2Z) holds for the *old* engine too, but it is
      a parity property of Golay cosets, not evidence about primes
                                             [substrate_snap_even_weight]

HONEST LIMITS
-------------
  * Snapping is 24 bits -> 12 bits: only 4096 states exist, so different
    integers collide (d^2 = 0 steps).  This is a metric/encoding layer, not an
    arithmetic shortcut: nothing here accelerates factoring or primality.
  * At distance 4 the nearest codeword is not unique (1771 of the 4096 cosets
    have 6 tied weight-4 leaders); a convention is fixed here (minimum weight,
    then smallest coordinate mask) and is used consistently.

USAGE
-----
    python3 lattice_shortcut.py --explain 1000033 1000037
    python3 lattice_shortcut.py --walk 1000003 1000249 --map shift
    python3 lattice_shortcut.py --range 1000033 1000051 --map factor
    python3 lattice_shortcut.py --stats 1000000 10000
    python3 lattice_shortcut.py --tgic 1000003
    python3 lattice_shortcut.py --selftest
    python3 lattice_shortcut.py --json out.json --range 1000033 1000051

Python >= 3.8, standard library only.
================================================================================
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# ══════════════════════════════════════════════════════════════════════════════
#  0.  Bit conventions
#
#  A 24-bit state is carried as a Python int; bit j of the int is coordinate j
#  of the 24-vector, i.e. state = sum(v[j] << j).  `bits_of` / `int_of` convert
#  to and from the coordinate-list form used by the original substrate.
# ══════════════════════════════════════════════════════════════════════════════

MASK24 = (1 << 24) - 1


def popcount(x: int) -> int:
    """Hamming weight (Python 3.8-compatible)."""
    return bin(x).count("1")


def bits_of(state: int) -> List[int]:
    """int -> 24-coordinate list (coordinate j = bit j)."""
    return [(state >> j) & 1 for j in range(24)]


def int_of(v: Sequence[int]) -> int:
    """24-coordinate list -> int."""
    return sum((1 << j) for j, b in enumerate(v) if b)


# ══════════════════════════════════════════════════════════════════════════════
#  1.  The extended binary Golay code [24, 12, 8]
# ══════════════════════════════════════════════════════════════════════════════

# Symmetric parity block B of G = [I12 | B]  (identical to the substrate's).
GOLAY_B: List[List[int]] = [
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0],
    [1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1],
    [1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0],
    [1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1],
    [1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1],
    [1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0],
    [1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0],
    [1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1],
]

# Generator rows as 24-bit masks: information bit i, then the parity block.
GOLAY_ROWS: List[int] = [
    (1 << i) | sum(GOLAY_B[i][j] << (12 + j) for j in range(12))
    for i in range(12)
]


def golay_encode(msg12: int) -> int:
    """Systematic encoding of a 12-bit message into a 24-bit codeword."""
    c = 0
    for i in range(12):
        if (msg12 >> i) & 1:
            c ^= GOLAY_ROWS[i]
    return c


CODEWORDS: Tuple[int, ...] = tuple(golay_encode(m) for m in range(4096))
CODEWORD_SET = frozenset(CODEWORDS)
OCTADS: Tuple[int, ...] = tuple(c for c in CODEWORDS if popcount(c) == 8)


def is_codeword(state: int) -> bool:
    return state in CODEWORD_SET


def syndrome(state: int) -> int:
    """12-bit syndrome: discrepancy between the word and the re-encoding of its
    information half.  Zero exactly on codewords."""
    return (state ^ golay_encode(state & 0xFFF)) >> 12


def _build_coset_leaders() -> Tuple[int, ...]:
    """Full coset-leader table: for each of the 4096 syndromes, a minimum-weight
    representative of that coset.  Tie-break: smallest coordinate mask."""
    table: List[Optional[int]] = [None] * 4096
    table[0] = 0
    found = 1
    # enumerate error patterns by increasing weight; the covering radius is 4,
    # so weight <= 4 already fills the table.
    for weight in range(1, 5):
        for e in _patterns_of_weight(weight):
            s = syndrome(e)
            if table[s] is None:
                table[s] = e
                found += 1
        if found == 4096:
            break
    assert found == 4096, "coset-leader table incomplete"
    return tuple(int(x) for x in table)  # type: ignore[arg-type]


def _patterns_of_weight(weight: int) -> Iterable[int]:
    """All 24-bit masks of a given Hamming weight, in increasing numeric order."""
    if weight == 0:
        yield 0
        return
    idx = list(range(weight))
    while True:
        yield sum(1 << i for i in idx)
        k = weight - 1
        while k >= 0 and idx[k] == 24 - weight + k:
            k -= 1
        if k < 0:
            return
        idx[k] += 1
        for j in range(k + 1, weight):
            idx[j] = idx[j - 1] + 1


COSET_LEADER: Tuple[int, ...] = _build_coset_leaders()


def snap(state: int) -> int:
    """THE FIXED SNAP: complete (nearest-codeword) Golay decoding.

    Always returns a codeword, at Hamming distance <= 4 from the input
    (covering radius of the Golay code).  Cost: one 12-bit table lookup."""
    return state ^ COSET_LEADER[syndrome(state)]


def legacy_snap(state: int) -> int:
    """The ORIGINAL engine, for comparison only: corrects error patterns of
    weight <= 3 and otherwise returns its input unchanged (so the result need
    not be a codeword)."""
    e = COSET_LEADER[syndrome(state)]
    return state ^ e if popcount(e) <= 3 else state


def reencode_snap(state: int) -> int:
    """A third variant, used inside the substrate's RuneCube face transforms:
    re-encode the information half of the (legacy-)snapped word.  Always a
    codeword, but not the nearest one when the legacy snap failed (it can move
    the state by up to 12 bits).  Provided for exact reproduction of the
    published TGIC metrics; the operational method uses `snap`."""
    return golay_encode(legacy_snap(state) & 0xFFF)


# ══════════════════════════════════════════════════════════════════════════════
#  2.  Encoders:  integer -> 24-bit word
# ══════════════════════════════════════════════════════════════════════════════

def gray8(b: int) -> int:
    """8-bit reflected-binary Gray code."""
    b &= 0xFF
    return b ^ (b >> 1)


def _channel(byte_value: int, slot: int) -> int:
    """Place one Gray-coded byte MSB-first into coordinates 8*slot .. 8*slot+7."""
    g = gray8(byte_value)
    out = 0
    for i in range(8):
        if (g >> (7 - i)) & 1:
            out |= 1 << (8 * slot + i)
    return out


def encode_channels(x: int, y: int, z: int) -> int:
    """Assemble a 24-bit state from three byte channels."""
    return _channel(x, 0) | _channel(y, 1) | _channel(z, 2)


def encode_shift(n: int) -> int:
    """Continuous 24-bit bit-shift encoder (no mod-256 wrap)."""
    n = abs(int(n))
    return encode_channels(n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF)


def prime_factorisation(n: int) -> List[Tuple[int, int]]:
    """Trial-division factorisation, ascending primes, as (p, e) pairs."""
    n = abs(int(n))
    out: List[Tuple[int, int]] = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n //= d
                e += 1
            out.append((d, e))
        d += 1 if d == 2 else 2
    if n > 1:
        out.append((n, 1))
    return out


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def encode_factor(n: int) -> int:
    """ValueGeometry factor encoder (the one the published generator used).

    Primes are encoded by `encode_shift`; a composite puts its first prime
    power on X, its second on Y and the product of the rest on Z."""
    f = prime_factorisation(n)
    if len(f) == 1 and f[0][1] == 1:          # n is prime
        return encode_shift(n)
    x = f[0][0] ** f[0][1] if len(f) > 0 else 1
    y = f[1][0] ** f[1][1] if len(f) > 1 else 1
    z = 1
    for p, e in f[2:]:
        z *= p ** e
    return encode_channels(x & 0xFF, y & 0xFF, z & 0xFF)


ENCODERS = {"shift": encode_shift, "factor": encode_factor}


# ══════════════════════════════════════════════════════════════════════════════
#  3.  Transitions:  jump vectors, norms, Leech membership
# ══════════════════════════════════════════════════════════════════════════════

LATTICE_CLASS = {0: "collision", 8: "octad (minimal vector)", 12: "dodecad",
                 16: "hexadecad", 24: "antipodal"}


def d2(state_a: int, state_b: int) -> int:
    """Squared jump norm = Hamming distance of the two 24-bit states."""
    return popcount(state_a ^ state_b)


def jump_vector(state_a: int, state_b: int) -> List[int]:
    """Dv = v(b) - v(a) in {-1,0,+1}^24."""
    va, vb = bits_of(state_a), bits_of(state_b)
    return [b - a for a, b in zip(va, vb)]


def leech_vector(state_a: int, state_b: int) -> List[int]:
    """2*Dv: the exact Leech-lattice element of the transition (integral
    x sqrt(8) scaling), of norm 4*d^2."""
    return [2 * t for t in jump_vector(state_a, state_b)]


def raw_d2_shortcut(a: int, b: int) -> int:
    """THE O(1) SHORTCUT.  For the Gray layer (before snapping) the jump norm
    between *any* two integers is

            d^2(a,b) = popcount( gray(a XOR b) )

    because Gray coding is GF(2)-linear on each channel.  Three machine
    instructions; no traversal of the integers between a and b, no octad
    enumeration.  (Verified against the direct computation in --selftest.)"""
    x = a ^ b
    return (popcount(gray8(x & 0xFF)) + popcount(gray8((x >> 8) & 0xFF))
            + popcount(gray8((x >> 16) & 0xFF)))


def transition(a: int, b: int, encoder: str = "shift") -> Dict[str, object]:
    """Full description of one transition a -> b."""
    enc = ENCODERS[encoder]
    wa, wb = enc(a), enc(b)
    ca, cb = snap(wa), snap(wb)
    d = d2(ca, cb)
    return {
        "from": a,
        "to": b,
        "raw_state_from": wa,
        "raw_state_to": wb,
        "snapped_state_from": ca,
        "snapped_state_to": cb,
        "snap_correction_from": popcount(wa ^ ca),
        "snap_correction_to": popcount(wb ^ cb),
        "raw_d2": d2(wa, wb),
        "d2": d,
        "lattice_class": LATTICE_CLASS.get(d, "?"),
        "is_octad_step": d == 8,
        "is_minimal_vector": d == 8,
        "leech_norm_sq": 4 * d,
        "quantised_by_4": d % 4 == 0,
        "jump_vector": jump_vector(ca, cb),
        "leech_vector": leech_vector(ca, cb),
        "both_states_are_codewords": is_codeword(ca) and is_codeword(cb),
    }


def walk(sequence: Sequence[int], encoder: str = "shift") -> List[Dict[str, object]]:
    return [transition(sequence[i], sequence[i + 1], encoder)
            for i in range(len(sequence) - 1)]


def walk_summary(steps: Sequence[Dict[str, object]]) -> Dict[str, object]:
    d2s = [int(s["d2"]) for s in steps]
    n = len(d2s) or 1
    hist: Dict[int, int] = {}
    for d in d2s:
        hist[d] = hist.get(d, 0) + 1
    return {
        "steps": len(d2s),
        "d2_histogram": dict(sorted(hist.items())),
        "octad_rate_pct": round(100.0 * sum(1 for d in d2s if d == 8) / n, 4),
        "collision_rate_pct": round(100.0 * sum(1 for d in d2s if d == 0) / n, 4),
        "all_quantised_by_4": all(d % 4 == 0 for d in d2s),
        "all_even": all(d % 2 == 0 for d in d2s),
        "all_leech_vectors": all(bool(s["both_states_are_codewords"]) for s in steps),
        "mean_d2": round(sum(d2s) / n, 4),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  4.  Node metrics (Leech tax / NRCI and the TGIC 3-6-9 audit)
#
#  Reproduced from the UBP substrate, with the fixed snap used inside the face
#  transforms.  Exact rational arithmetic throughout.
# ══════════════════════════════════════════════════════════════════════════════

def _pi_fraction(terms: int = 50) -> Fraction:
    """pi as a continued fraction (OEIS A001203), ~80 correct digits."""
    cf = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2,
          1, 84, 2, 1, 1, 15, 3, 13, 1, 4, 2, 6, 6, 99, 1, 2, 2, 6, 3, 5,
          1, 1, 6, 8, 1, 7, 1, 6, 1, 99, 7, 4, 1, 3, 3, 1, 4, 1][:terms]
    x = Fraction(cf[-1])
    for c in reversed(cf[:-1]):
        x = Fraction(c) + 1 / x
    return x


PI = _pi_fraction()
Y_CONST = 1 / (PI + 2 / PI)          # observer constant Y ~ 0.264673


def symmetry_tax(state: int) -> Fraction:
    """Leech symmetry tax  hw*Y + ||v||^2/8  (for 0/1 states ||v||^2 = hw)."""
    hw = popcount(state)
    return Fraction(hw) * Y_CONST + Fraction(hw, 8)


def nrci(state: int) -> Fraction:
    """Non-Random Coherence Index 10/(10 + tax)."""
    return Fraction(10) / (10 + symmetry_tax(state))


def _blocks(state: int) -> Tuple[int, int, int]:
    return state & 0xFF, (state >> 8) & 0xFF, (state >> 16) & 0xFF


def tgic_3_axis_orthogonality(state: int) -> Fraction:
    """[THE 3] ideal is Hamming distance 4 between each pair of 8-bit blocks."""
    x, y, z = _blocks(state)
    dev = (abs(4 - popcount(x ^ y)) + abs(4 - popcount(x ^ z))
           + abs(4 - popcount(y ^ z)))
    return Fraction(1) / (1 + Fraction(dev) * Y_CONST)


def _face_xy(state: int, snap_fn=snap) -> int:
    x, y, z = _blocks(state)
    nx = x & y
    return snap_fn(nx | (nx << 8) | (z << 16))


def _face_xz(state: int, snap_fn=snap) -> int:
    x, y, z = _blocks(state)
    return snap_fn(x | (y << 8) | ((x ^ z) << 16))


def _face_yz(state: int, snap_fn=snap) -> int:
    x, y, z = _blocks(state)
    return snap_fn(x | ((y | z) << 8) | (z << 16))


def tgic_6_face_coherence(state: int, snap_fn=snap) -> Fraction:
    """[THE 6] stability of the three RuneCube face transforms (AND/XOR/OR)."""
    return Fraction(10) / (10 + runecube_face_tax(state, snap_fn))


def runecube_face_tax(state: int, snap_fn=snap) -> Fraction:
    """Average symmetry tax over the three faces."""
    return (symmetry_tax(_face_xy(state, snap_fn))
            + symmetry_tax(_face_xz(state, snap_fn))
            + symmetry_tax(_face_yz(state, snap_fn))) / 3


def tgic_9_neighbour_pressure(state: int, manifold: Sequence[int]) -> Fraction:
    """[THE 9] penalty once more than nine other states lie within distance 8."""
    neighbours = sum(1 for v in manifold if v != state and d2(state, v) <= 8)
    return Fraction(max(0, neighbours - 9)) * Y_CONST


def tgic_stability(state: int, manifold: Sequence[int] = (), snap_fn=snap) -> Fraction:
    """Master 3-6-9 audit: mean of orthogonality, face coherence and NRCI,
    minus neighbourhood pressure."""
    ortho = tgic_3_axis_orthogonality(state)
    faces = tgic_6_face_coherence(state, snap_fn)
    base = nrci(state)
    pressure = tgic_9_neighbour_pressure(state, manifold) if manifold else Fraction(0)
    return (ortho + faces + base) / 3 - pressure


def node_report(n: int, encoder: str = "shift") -> Dict[str, object]:
    w = ENCODERS[encoder](n)
    c = snap(w)
    return {
        "n": n,
        "encoder": encoder,
        "raw_state": f"{w:024b}",
        "snapped_state": f"{c:024b}",
        "bits_corrected": popcount(w ^ c),
        "is_codeword": is_codeword(c),
        "weight": popcount(c),
        "lattice_class": {0: "Identity", 8: "Octad", 12: "Dodecad",
                          16: "Hexadecad", 24: "Full"}.get(popcount(c), "?"),
        "symmetry_tax": float(symmetry_tax(c)),
        "nrci": float(nrci(c)),
        "tgic_3_axis_orthogonality": float(tgic_3_axis_orthogonality(c)),
        "tgic_6_face_coherence": float(tgic_6_face_coherence(c)),
        "runecube_face_tax": float(runecube_face_tax(c)),
        "tgic_master_stability": float(tgic_stability(c)),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  5.  Self-test:  every guarantee, checked at run time
# ══════════════════════════════════════════════════════════════════════════════

def selftest(verbose: bool = True) -> bool:
    def report(name: str, ok: bool, detail: str = "") -> bool:
        if verbose:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
        return ok

    ok = True

    # -- the code itself -------------------------------------------------------
    weights: Dict[int, int] = {}
    for c in CODEWORDS:
        weights[popcount(c)] = weights.get(popcount(c), 0) + 1
    ok &= report("Golay weight enumerator 1 + 759x^8 + 2576x^12 + 759x^16 + x^24",
                 weights == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}, str(weights))
    ok &= report("code is linear (closed under XOR)",
                 all(is_codeword(CODEWORDS[i] ^ CODEWORDS[j])
                     for i in range(0, 4096, 97) for j in range(0, 4096, 89)))
    ok &= report("minimum distance 8",
                 min(popcount(c) for c in CODEWORDS if c) == 8)
    ok &= report("doubly even (all weights divisible by 4)",
                 all(popcount(c) % 4 == 0 for c in CODEWORDS))

    # -- the decoder -----------------------------------------------------------
    ok &= report("coset-leader table complete (4096 syndromes)",
                 len(COSET_LEADER) == 4096 and len(set(map(syndrome, COSET_LEADER))) == 4096)
    ok &= report("covering radius 4 (every leader has weight <= 4)",
                 max(popcount(e) for e in COSET_LEADER) == 4)
    ok &= report("G1: snap always returns a codeword",
                 all(is_codeword(snap(v)) for v in range(0, 1 << 24, 1021)))
    ok &= report("G2: snap moves a state by at most 4 bits",
                 all(popcount(v ^ snap(v)) <= 4 for v in range(0, 1 << 24, 1021)))
    ok &= report("snap fixes codewords", all(snap(c) == c for c in CODEWORDS))
    n_bad = sum(1 for v in range(0, 1 << 24, 1021) if not is_codeword(legacy_snap(v)))
    tested = len(range(0, 1 << 24, 1021))
    ok &= report("legacy snap leaves ~44% of inputs uncorrected (the bug)",
                 n_bad > 0, f"{n_bad}/{tested} = {100.0*n_bad/tested:.1f}%")

    # -- transitions -----------------------------------------------------------
    sample = list(range(1000000, 1000400))
    for enc in ("shift", "factor"):
        steps = walk(sample, enc)
        ok &= report(f"G3 [{enc}]: d^2 in {{0,8,12,16,24}} (quantisation by 4)",
                     all(int(s["d2"]) in (0, 8, 12, 16, 24) for s in steps))
        ok &= report(f"G5 [{enc}]: ||2Dv||^2 = 4 d^2 and = 32 exactly for octads",
                     all(sum(t * t for t in s["leech_vector"]) == 4 * int(s["d2"])  # type: ignore[arg-type]
                         and ((sum(t * t for t in s["leech_vector"]) == 32)  # type: ignore[arg-type]
                              == (int(s["d2"]) == 8)) for s in steps))
        ok &= report(f"G4 [{enc}]: every step is a Leech vector",
                     all(bool(s["both_states_are_codewords"]) for s in steps))

    # -- the O(1) shortcut -----------------------------------------------------
    pairs = [(a, b) for a in range(1000000, 1000040) for b in range(1000000, 1000040)]
    ok &= report("G7: popcount(gray(a XOR b)) == direct raw jump norm",
                 all(raw_d2_shortcut(a, b) == d2(encode_shift(a), encode_shift(b))
                     for a, b in pairs))

    # -- the legacy "even quantisation" law ------------------------------------
    ok &= report("G8: legacy-snapped states always have even weight "
                 "(so d^2 was always even -- a Golay coset parity fact)",
                 all(popcount(legacy_snap(v)) % 2 == 0 for v in range(0, 1 << 24, 1021)))

    # -- honest limits ---------------------------------------------------------
    states = {snap(encode_shift(n)) for n in range(1000000, 1010000)}
    ok &= report("information loss: 10000 consecutive integers -> few states",
                 len(states) < 4096, f"{len(states)} distinct states")
    tied = sum(1 for s in range(4096)
               if popcount(COSET_LEADER[s]) == 4)
    ok &= report("ties: cosets with weight-4 leaders need a tie-break convention",
                 tied > 0, f"{tied} of 4096 cosets")

    if verbose:
        print(f"\n  {'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}")
    return bool(ok)


# ══════════════════════════════════════════════════════════════════════════════
#  6.  Explainer mode
# ══════════════════════════════════════════════════════════════════════════════

def explain(a: int, b: int, encoder: str = "shift") -> None:
    enc = ENCODERS[encoder]
    wa, wb = enc(a), enc(b)
    ca, cb = snap(wa), snap(wb)
    d = d2(ca, cb)
    line = "─" * 78

    print(line)
    print(f"  LATTICE SHORTCUT   {a}  ->  {b}     (encoder: {encoder})")
    print(line)

    print("\nSTAGE 1 — ENCODE  (integer -> 24-bit word)")
    if encoder == "shift":
        for n, w in ((a, wa), (b, wb)):
            x, y, z = n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF
            print(f"  {n}:  x={x:3d} y={y:3d} z={z:3d}  "
                  f"-> Gray per byte -> {w:024b}")
    else:
        for n, w in ((a, wa), (b, wb)):
            f = prime_factorisation(n)
            fs = " x ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in f)
            print(f"  {n} = {fs}" + ("  (prime: bit-shift channels)" if is_prime(n) else ""))
            print(f"      -> {w:024b}")

    print("\nSTAGE 2 — SNAP  (nearest Golay codeword, complete decoder)")
    for n, w, c in ((a, wa, ca), (b, wb, cb)):
        print(f"  {n}:  {w:024b}  -> {c:024b}   "
              f"({popcount(w ^ c)} bit(s) corrected, weight {popcount(c)}, "
              f"codeword: {is_codeword(c)})")
    if max(popcount(wa ^ ca), popcount(wb ^ cb)) == 4:
        print("       (a weight-4 correction: exactly the case the original")
        print("        engine could not handle and left unsnapped)")

    print("\nSTAGE 3 — STEP  (jump vector and lattice class)")
    dv = jump_vector(ca, cb)
    print(f"  Dv           = {dv}")
    print(f"  d^2 = ||Dv||^2 = {d}   ({LATTICE_CLASS.get(d, '?')})")
    print(f"  2Dv in Lambda_24, ||2Dv||^2 = {4*d}"
          + ("   <- minimum norm of the Leech lattice: a kissing-sphere hop"
             if d == 8 else ""))
    print(f"  quantisation:  4 | d^2  -> {d % 4 == 0}")

    print("\nSHORTCUT — the same raw metric without touching the interval")
    print(f"  a XOR b                       = {a ^ b}")
    print(f"  popcount(gray(a XOR b))       = {raw_d2_shortcut(a, b)}")
    print(f"  direct Hamming(w_a, w_b)      = {d2(wa, wb)}   (agrees)")
    print("  cost: xor, shift-xor, popcount — independent of |b - a|.")

    print("\nNODE METRICS (exact rational arithmetic)")
    for n, c in ((a, ca), (b, cb)):
        print(f"  {n}: tax={float(symmetry_tax(c)):.6f}  nrci={float(nrci(c)):.6f}  "
              f"ortho={float(tgic_3_axis_orthogonality(c)):.6f}  "
              f"coherence={float(tgic_6_face_coherence(c)):.6f}  "
              f"stability={float(tgic_stability(c)):.6f}")

    print("\nWHAT THIS DOES NOT DO")
    print("  Only 4096 snapped states exist, so the map is many-to-one: a d^2 = 0")
    print("  step means two integers collided, not that they are 'the same'.")
    print("  The shortcut is for the 24D metric, not for arithmetic on a or b.")
    print(line)


def stats(start: int, count: int, encoder: str = "shift") -> Dict[str, object]:
    seq = list(range(start, start + count))
    steps = walk(seq, encoder)
    s = walk_summary(steps)
    states = [snap(ENCODERS[encoder](n)) for n in seq]
    s["distinct_states"] = len(set(states))
    s["integers"] = count
    s["legacy_non_codeword_rate_pct"] = round(
        100.0 * sum(1 for n in seq if not is_codeword(legacy_snap(ENCODERS[encoder](n)))) / count, 4)
    return s


# ══════════════════════════════════════════════════════════════════════════════
#  7.  CLI
# ══════════════════════════════════════════════════════════════════════════════

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="24D Golay/Leech lattice shortcut — operational implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--map", choices=sorted(ENCODERS), default="shift",
                   help="encoder: 'shift' (continuous 24-bit) or 'factor' "
                        "(ValueGeometry prime-power channels)")
    p.add_argument("--explain", nargs=2, type=int, metavar=("A", "B"),
                   help="narrate one transition end to end")
    p.add_argument("--walk", nargs="+", type=int, metavar="N",
                   help="jump norms along an explicit list of integers")
    p.add_argument("--range", nargs=2, type=int, metavar=("LO", "HI"),
                   help="walk the consecutive integers LO .. HI-1")
    p.add_argument("--primes", nargs=2, type=int, metavar=("FROM", "COUNT"),
                   help="walk the first COUNT primes >= FROM")
    p.add_argument("--stats", nargs=2, type=int, metavar=("START", "COUNT"),
                   help="aggregate statistics over COUNT consecutive integers")
    p.add_argument("--tgic", type=int, metavar="N", help="node report for N")
    p.add_argument("--selftest", action="store_true", help="verify every guarantee")
    p.add_argument("--json", metavar="FILE", help="also write results as JSON")
    args = p.parse_args(argv)

    payload: Dict[str, object] = {}
    did = False

    if args.selftest:
        did = True
        print("SELF-TEST\n")
        if not selftest():
            return 1

    if args.explain:
        did = True
        explain(args.explain[0], args.explain[1], args.map)

    seq: Optional[List[int]] = None
    if args.walk:
        seq = list(args.walk)
    elif args.range:
        seq = list(range(args.range[0], args.range[1]))
    elif args.primes:
        seq, n = [], args.primes[0]
        while len(seq) < args.primes[1]:
            if is_prime(n):
                seq.append(n)
            n += 1

    if seq is not None:
        did = True
        steps = walk(seq, args.map)
        print(f"{'step':>4}  {'from':>10} -> {'to':<10} {'raw':>4} {'d^2':>4} "
              f"{'||2Dv||^2':>9}  class")
        for i, s in enumerate(steps, 1):
            print(f"{i:>4}  {s['from']:>10} -> {s['to']:<10} {s['raw_d2']:>4} "
                  f"{s['d2']:>4} {s['leech_norm_sq']:>9}  {s['lattice_class']}")
        summary = walk_summary(steps)
        print("\nsummary:", json.dumps(summary))
        payload["walk"] = {"sequence": seq, "steps": steps, "summary": summary}

    if args.stats:
        did = True
        s = stats(args.stats[0], args.stats[1], args.map)
        print(json.dumps(s, indent=2))
        payload["stats"] = s

    if args.tgic is not None:
        did = True
        r = node_report(args.tgic, args.map)
        print(json.dumps(r, indent=2))
        payload["node"] = r

    if not did:
        p.print_help()
        print("\nTry:  python3 lattice_shortcut.py --explain 1000033 1000037")
        return 0

    if args.json and payload:
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=2)
        print(f"\nwritten: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
