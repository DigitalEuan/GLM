#!/usr/bin/env python3
"""
Independent audit + corrected implementation of the "24D Leech Lattice Geodesic
Shortcut" method.

NOTE (revision 2).  This script was written before `value_geometry.py`,
`ubp_tgic_engine.py` and `tgic_v3.py` were available, so it models the pipeline
with the bit-shift encoder only.  That is correct for primes but not for
composites, which the real generator encodes through their prime powers; the
"Deep Interfacial Sequence" is therefore reported here as unreproducible when
in fact it reproduces exactly.  Use `audit_ubp_directory.py` (runs against the
author's own modules) for the directory audit and `lattice_shortcut.py` for the
operational method.  This file is kept for the raw-layer measurements it makes.

This script:
  1. re-derives the encoding pipeline that was actually used to produce
     `lattice_shortcut_directory_standalone.json`,
  2. checks every numerical claim in `lattice_shortcode_directory.md`
     and in the JSON directory against a from-scratch reimplementation,
  3. implements the *corrected* pipeline (complete Golay decoding) and
     re-audits the same two sequences,
  4. writes `lattice_shortcut_directory_corrected_rev1.json`.

Everything here is ordinary Python; the mathematical statements that this
script suggests are proved formally in `RequestProject/*.lean`.
"""

from __future__ import annotations
import json
from collections import Counter
from itertools import combinations

# ---------------------------------------------------------------------------
# Golay [24,12,8]: generator G = [I12 | B] with B taken from ubp_unified_v5.py
# ---------------------------------------------------------------------------
B = [
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

# row i of G as a 24-bit mask: bit j == coordinate j (coordinates 0..11 are the
# information positions, 12..23 the parity positions).
ROWS = [ (1 << i) | sum((1 << (12 + j)) for j in range(12) if B[i][j])
         for i in range(12) ]

MASK24 = (1 << 24) - 1


def pop(x: int) -> int:
    return bin(x).count("1")


def codeword(m: int) -> int:
    x = 0
    for i in range(12):
        if (m >> i) & 1:
            x ^= ROWS[i]
    return x


CODEWORDS = [codeword(m) for m in range(4096)]
CODESET = set(CODEWORDS)
OCTADS = [c for c in CODEWORDS if pop(c) == 8]

# syndrome: 12 bits, s(v) = H v.  With G = [I|B], B symmetric, H = [B | I].
H_COLS = [ sum((1 << j) for j in range(12) if (ROWS[j] >> k) & 1) for k in range(24) ]


def syndrome(v: int) -> int:
    s = 0
    for k in range(24):
        if (v >> k) & 1:
            s ^= H_COLS[k]
    return s


def _build_leader_table():
    """Complete (nearest-codeword) decoding table: syndrome -> min-weight leader."""
    table = {}
    ties = {}
    for w in range(5):
        for pos in combinations(range(24), w):
            e = sum(1 << p for p in pos)
            s = syndrome(e)
            if s not in table:
                table[s] = e
                ties[s] = 1
            elif pop(table[s]) == w:
                ties[s] += 1
    return table, ties


LEADER, TIES = _build_leader_table()


def snap_complete(v: int) -> int:
    """Corrected snap: always returns a codeword (covering radius 4)."""
    return v ^ LEADER[syndrome(v)]


def snap_substrate(v: int) -> int:
    """The snap actually implemented in ubp_unified_v5.py: only corrects
    error patterns of weight <= 3, otherwise returns the input unchanged."""
    s = syndrome(v)
    e = LEADER[s]
    return v ^ e if pop(e) <= 3 else v


# ---------------------------------------------------------------------------
# Encodings
# ---------------------------------------------------------------------------
def gray24(n: int) -> int:
    """'Continuous 24-bit shift' Gray encoding, as documented in section 2."""
    n &= MASK24
    return n ^ (n >> 1)


def gray_bytes(n: int) -> int:
    """The encoding actually used by the directory generator: the three 8-bit
    channels x = n & 0xFF, y = (n >> 8) & 0xFF, z = (n >> 16) & 0xFF are Gray
    encoded *separately* and concatenated (x in the high coordinates)."""
    out = 0
    for k, sh in enumerate((0, 8, 16)):
        b = (n >> sh) & 0xFF
        g = b ^ (b >> 1)
        # channel k occupies coordinates 8k..8k+7, MSB first (list order),
        # bit position of list index p is p (see json vectors)
        for i in range(8):
            if (g >> (7 - i)) & 1:
                out |= 1 << (8 * k + i)
    return out


def vec(mask: int):
    return [(mask >> i) & 1 for i in range(24)]


def jump(f, a: int, b: int):
    va, vb = vec(f(a)), vec(f(b))
    return [y - x for x, y in zip(va, vb)]


def d2(f, a: int, b: int) -> int:
    return pop(f(a) ^ f(b))


# ---------------------------------------------------------------------------
# 1. Reproducibility of the published directory
# ---------------------------------------------------------------------------
def reproducibility_report(path="lattice_shortcut_directory_standalone.json"):
    data = json.load(open(path))
    out = {}
    pipelines = {
        "gray24": gray24,
        "gray24+substrate snap": lambda n: snap_substrate(gray24(n)),
        "byte-gray": gray_bytes,
        "byte-gray+substrate snap": lambda n: snap_substrate(gray_bytes(n)),
        "byte-gray+complete snap": lambda n: snap_complete(gray_bytes(n)),
    }
    for cat, steps in data["catalogs"].items():
        res = {}
        for name, f in pipelines.items():
            exact = sum(1 for s in steps
                        if jump(f, s["origin_node"]["n"], s["target_node"]["n"])
                        == s["jump_vector_24d"])
            res[name] = f"{exact}/{len(steps)} jump vectors reproduced exactly"
        out[cat] = res
    return out


# ---------------------------------------------------------------------------
# 2. Claim checks
# ---------------------------------------------------------------------------
def claim_checks():
    r = {}

    # Golay engine really is the [24,12,8] Golay code
    r["golay_weight_distribution"] = dict(sorted(Counter(pop(c) for c in CODEWORDS).items()))

    # (a) "consecutive deep integers jump by d^2 in {8,10,12}"
    seq = list(range(1000033, 1000051))
    r["consecutive_d2_gray24"] = sorted(Counter(d2(gray24, n, n + 1) for n in seq[:-1]).items())
    r["consecutive_d2_bytegray"] = sorted(Counter(d2(gray_bytes, n, n + 1) for n in seq[:-1]).items())

    # (b) "even quantization rate 100%"  (raw encoding, all pairs in a window)
    odd = 0
    tot = 0
    for a in range(100000, 100200):
        for b in range(a + 1, 100200):
            tot += 1
            if d2(gray24, a, b) % 2 == 1:
                odd += 1
    r["gray24_pairs_tested"] = tot
    r["gray24_pairs_with_odd_d2"] = odd
    r["gray24_odd_d2_iff_opposite_parity"] = all(
        (d2(gray24, a, b) % 2) == ((a ^ b) & 1)
        for a in range(100000, 100300) for b in range(a, a + 40))

    # (c) the O(1) XOR shortcut
    r["xor_shortcut_valid"] = all(
        d2(gray24, a, b) == pop(gray24(a ^ b))
        for a in range(1000000, 1000500) for b in range(a, a + 60))

    # (d) does the substrate snap actually return codewords?
    bad = [n for n in range(1000000, 1001000)
           if snap_substrate(gray_bytes(n)) not in CODESET]
    r["substrate_snap_failures_per_1000"] = len(bad)
    r["complete_snap_failures_per_1000"] = sum(
        1 for n in range(1000000, 1001000) if snap_complete(gray_bytes(n)) not in CODESET)
    r["ambiguous_weight4_cosets"] = sum(1 for s, e in LEADER.items() if pop(e) == 4)
    _w4 = Counter()
    for _pos in combinations(range(24), 4):
        _w4[syndrome(sum(1 << p for p in _pos))] += 1
    r["weight4_coset_leader_multiplicities"] = dict(Counter(
        _w4[s] for s, e in LEADER.items() if pop(e) == 4))
    r["max_coset_leader_weight"] = max(pop(e) for e in LEADER.values())

    # (e) with complete decoding the jump norms are Golay weights
    norms = Counter(d2(lambda n: snap_complete(gray_bytes(n)), n, n + 1)
                    for n in range(1000000, 1002000))
    r["corrected_consecutive_d2_distribution"] = sorted(norms.items())

    # (f) Leech membership of the doubled corrected jumps
    ok = True
    for n in range(1000000, 1001000):
        dv = jump(lambda k: snap_complete(gray_bytes(k)), n, n + 1)
        sup = sum(1 << i for i, x in enumerate(dv) if x != 0)
        neg = sum(1 for x in dv if x < 0)
        if sup not in CODESET or neg % 2 != 0:
            ok = False
    r["corrected_jumps_are_leech_vectors"] = ok
    return r


# ---------------------------------------------------------------------------
# 3. Corrected directory
# ---------------------------------------------------------------------------
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def corrected_catalog(nodes):
    enc = lambda n: snap_complete(gray_bytes(n))
    steps = []
    for k in range(len(nodes) - 1):
        a, b = nodes[k], nodes[k + 1]
        dv = jump(enc, a, b)
        raw = d2(gray_bytes, a, b)
        sup = sum(1 << i for i, x in enumerate(dv) if x != 0)
        nsq = sum(x * x for x in dv)
        steps.append({
            "step": k + 1,
            "origin": {"n": a, "is_prime": is_prime(a)},
            "target": {"n": b, "is_prime": is_prime(b)},
            "raw_gray_d2": raw,
            "raw_gray_d2_via_xor_shortcut": pop(gray_bytes(a ^ b)) if False else
                sum(pop((lambda t: t ^ (t >> 1))(((a ^ b) >> sh) & 0xFF)) for sh in (0, 8, 16)),
            "snapped_jump_vector_24d": dv,
            "snapped_d2": nsq,
            "support_is_golay_codeword": sup in CODESET,
            "is_minimal_octad_step": nsq == 8 and sup in CODESET,
            "doubled_jump_is_leech_vector": sup in CODESET and sum(1 for x in dv if x < 0) % 2 == 0,
            "doubled_norm_sq_x8_representation": 4 * nsq,
        })
    return steps


def main():
    interfacial = list(range(1000033, 1000051))
    primes = [1000003, 1000033, 1000037, 1000039, 1000081, 1000099, 1000117,
              1000121, 1000133, 1000151, 1000159, 1000171, 1000183, 1000187,
              1000193, 1000199, 1000211, 1000213, 1000231, 1000249]

    cats = {
        "Deep Interfacial Sequence (N = 1,000,033 .. 1,000,050)": corrected_catalog(interfacial),
        "Deep Prime-to-Prime Trajectory (P > 1,000,000)": corrected_catalog(primes),
    }
    allsteps = [s for v in cats.values() for s in v]
    summary = {
        "total_transitions": len(allsteps),
        "raw_gray_d2_distribution": sorted(Counter(s["raw_gray_d2"] for s in allsteps).items()),
        "snapped_d2_distribution": sorted(Counter(s["snapped_d2"] for s in allsteps).items()),
        "all_snapped_supports_are_golay_codewords":
            all(s["support_is_golay_codeword"] for s in allsteps),
        "all_doubled_jumps_are_leech_vectors":
            all(s["doubled_jump_is_leech_vector"] for s in allsteps),
        "minimal_octad_step_rate_pct":
            round(100 * sum(s["is_minimal_octad_step"] for s in allsteps) / len(allsteps), 2),
        "even_quantization_rate_pct_raw":
            round(100 * sum(s["raw_gray_d2"] % 2 == 0 for s in allsteps) / len(allsteps), 2),
    }
    out = {"reproducibility_of_published_directory": reproducibility_report(),
           "claim_checks": claim_checks(),
           "summary": summary,
           "catalogs": cats}
    json.dump(out, open("lattice_shortcut_directory_corrected_rev1.json", "w"), indent=2)
    print(json.dumps({k: out[k] for k in
                      ("reproducibility_of_published_directory", "claim_checks", "summary")},
                     indent=2))


if __name__ == "__main__":
    main()
