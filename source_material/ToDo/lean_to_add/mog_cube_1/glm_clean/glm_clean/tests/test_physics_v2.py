#!/usr/bin/env python3
"""
Physics encoding — Round 2: cleaner encodings + snap triple test.

The first round showed:
  - Directions: opposites and orthogonals both ~3-4 bits apart (not differentiating)
  - Temperatures: ordering IS visible (freezing-boiling = 11, adjacent = 5-8)
  - Numbers: parity bit works, magnitude loosely correlates

Round 2: Make the encoding SHARPER. Use the bits more deliberately.
"""

import sys
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/download/arc_agi_17')

from glm_clean import Mind, Body, DataObject, Snap
from ubp_unified_v5 import GOLAY_ENGINE


def int_to_6bits(n: int) -> List[int]:
    n = n & 0x3F
    return [(n >> (5 - i)) & 1 for i in range(6)]


# ══════════════════════════════════════════════════════════════════════════════
# CLEANER DIRECTION ENCODING
# ══════════════════════════════════════════════════════════════════════════════

def encode_direction_v2(direction: str) -> DataObject:
    """Encode direction with SHARPER bit assignments.

    Use the 24 bits as a 3D direction vector directly:
      Bits 0-7   (X axis):   sign in bit 0, magnitude in bits 1-7
      Bits 8-15  (Y axis):   sign in bit 8, magnitude in bits 9-15
      Bits 16-23 (Z axis):   sign in bit 16, magnitude in bits 17-23

    left   = (-1, 0, 0) → bit 0 = 1 (negative), bits 1-7 = 0000001 (mag 1)
    right  = (+1, 0, 0) → bit 0 = 0 (positive), bits 1-7 = 0000001 (mag 1)
    up     = (0, +1, 0) → bit 8 = 0, bits 9-15 = 0000001
    down   = (0, -1, 0) → bit 8 = 1, bits 9-15 = 0000001
    forward= (0, 0, +1) → bit 16 = 0, bits 17-23 = 0000001
    back   = (0, 0, -1) → bit 16 = 1, bits 17-23 = 0000001
    center = (0, 0, 0)  → all zeros
    """
    vectors = {
        "left":    (-1, 0, 0),
        "right":   (+1, 0, 0),
        "up":      (0, +1, 0),
        "down":    (0, -1, 0),
        "forward": (0, 0, +1),
        "back":    (0, 0, -1),
        "center":  (0, 0, 0),
    }

    v = vectors.get(direction.lower())
    if v is None:
        raise ValueError(f"Unknown direction: {direction}")

    bits = [0] * 24
    # X axis: bits 0-7
    if v[0] != 0:
        bits[0] = 1 if v[0] < 0 else 0  # sign
        mag_bits = int_to_6bits(abs(v[0]))  # 6 bits
        for i, b in enumerate(mag_bits):
            bits[1 + i] = b
    # Y axis: bits 8-15
    if v[1] != 0:
        bits[8] = 1 if v[1] < 0 else 0
        mag_bits = int_to_6bits(abs(v[1]))
        for i, b in enumerate(mag_bits):
            bits[9 + i] = b
    # Z axis: bits 16-23
    if v[2] != 0:
        bits[16] = 1 if v[2] < 0 else 0
        mag_bits = int_to_6bits(abs(v[2]))
        for i, b in enumerate(mag_bits):
            bits[17 + i] = b

    return DataObject(bits=bits)


def encode_temperature_v2(temp_str: str) -> DataObject:
    """Encode temperature with the actual Celsius value in the bits.

    Use a linear scale: 0°C = 0, 100°C = 63 (6 bits).
    Put the value in MULTIPLE rows so the encoding is robust.
    """
    temps = {"freezing": 0, "cold": 10, "cool": 20, "tepid": 30,
             "warm": 40, "hot": 60, "boiling": 100}

    t = temps.get(temp_str.lower())
    if t is None:
        raise ValueError(f"Unknown temperature: {temp_str}")

    # Scale to 6 bits (0-63)
    scaled = min(63, t * 63 // 100)

    # REALITY: the temperature value
    reality = int_to_6bits(scaled)

    # INFO: same value (redundant for robustness)
    info = int_to_6bits(scaled)

    # ACTIVATION: energy (proportional to T)
    energy = min(63, scaled)
    activation = int_to_6bits(energy)

    # POTENTIAL: phase (0=solid, 1=liquid, 2=gas)
    if t <= 0: phase = 0
    elif t >= 100: phase = 2
    else: phase = 1
    potential = int_to_6bits(phase << 4 | (scaled & 0b1111))

    return DataObject.from_rows(reality, info, activation, potential)


def encode_speed_v2(speed_str: str) -> DataObject:
    """Encode speed with the actual value in the bits."""
    speeds = {"stopped": 0, "slow": 5, "walk": 5, "jog": 10,
              "run": 15, "sprint": 30, "fast": 50, "very_fast": 63}

    s = speeds.get(speed_str.lower())
    if s is None:
        raise ValueError(f"Unknown speed: {speed_str}")

    # REALITY: speed value
    reality = int_to_6bits(s)

    # INFO: same value
    info = int_to_6bits(s)

    # ACTIVATION: kinetic energy (v²)
    ke = min(63, s * s // 25) if s > 0 else 0
    activation = int_to_6bits(ke)

    # POTENTIAL: motion state
    motion = 0 if s == 0 else 1
    potential = int_to_6bits(motion << 4 | (s & 0b1111))

    return DataObject.from_rows(reality, info, activation, potential)


def hamming(v1, v2):
    return sum(1 for a, b in zip(v1.bits, v2.bits) if a != b)


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_directions_v2():
    """Test the cleaner direction encoding."""
    print(f"\n{'='*70}")
    print("DIRECTIONS v2 (3D vector encoding)")
    print(f"{'='*70}")

    dirs = ["left", "right", "up", "down", "forward", "back", "center"]
    encoded = {d: encode_direction_v2(d) for d in dirs}

    print(f"\n{'Dir':<10} {'vector':<15} {'int':<12}")
    print("-" * 40)
    vectors = {"left": "(-1,0,0)", "right": "(+1,0,0)", "up": "(0,+1,0)",
               "down": "(0,-1,0)", "forward": "(0,0,+1)", "back": "(0,0,-1)",
               "center": "(0,0,0)"}
    for d in dirs:
        print(f"{d:<10} {vectors[d]:<15} {encoded[d].to_int():<12}")

    print(f"\n--- Opposites (should be CLOSE: differ only in sign bit) ---")
    opposites = [("left", "right"), ("up", "down"), ("forward", "back")]
    for w1, w2 in opposites:
        d = hamming(encoded[w1], encoded[w2])
        print(f"  {w1} - {w2}: {d} bits")

    print(f"\n--- Orthogonal (should be FARTHER than opposites) ---")
    ortho = [("left", "up"), ("left", "down"), ("left", "forward"),
             ("right", "up"), ("up", "forward"), ("down", "back")]
    for w1, w2 in ortho:
        d = hamming(encoded[w1], encoded[w2])
        print(f"  {w1} - {w2}: {d} bits")

    print(f"\n--- Center (should be far from all directions) ---")
    for d_name in ["left", "right", "up", "forward"]:
        d = hamming(encoded["center"], encoded[d_name])
        print(f"  center - {d_name}: {d} bits")

    # The KEY physics test: opposites should be CLOSER than orthogonals
    opp_dists = [hamming(encoded[w1], encoded[w2]) for w1, w2 in opposites]
    orth_dists = [hamming(encoded[w1], encoded[w2]) for w1, w2 in ortho]
    print(f"\n--- Physics check ---")
    print(f"  Mean opposite distance: {sum(opp_dists)/len(opp_dists):.1f}")
    print(f"  Mean orthogonal distance: {sum(orth_dists)/len(orth_dists):.1f}")
    print(f"  Opposites closer than orthogonals? {sum(opp_dists)/len(opp_dists) < sum(orth_dists)/len(orth_dists)}")

    return encoded


def test_temperatures_v2():
    """Test the cleaner temperature encoding."""
    print(f"\n{'='*70}")
    print("TEMPERATURES v2 (direct value encoding)")
    print(f"{'='*70}")

    temps = ["freezing", "cold", "cool", "tepid", "warm", "hot", "boiling"]
    temp_values = {"freezing": 0, "cold": 10, "cool": 20, "tepid": 30,
                   "warm": 40, "hot": 60, "boiling": 100}
    encoded = {t: encode_temperature_v2(t) for t in temps}

    print(f"\n{'Temp':<12} {'°C':<6} {'int':<12}")
    print("-" * 35)
    for t in temps:
        print(f"{t:<12} {temp_values[t]:<6} {encoded[t].to_int():<12}")

    # Ordering check: distance should correlate with temperature difference
    print(f"\n--- Ordering (distance vs temp diff) ---")
    print(f"{'Pair':<30} {'ΔT':<6} {'Hamming':<8}")
    print("-" * 50)
    pairs_by_diff = []
    for i, t1 in enumerate(temps):
        for t2 in temps[i+1:]:
            td = abs(temp_values[t1] - temp_values[t2])
            hd = hamming(encoded[t1], encoded[t2])
            pairs_by_diff.append((td, hd, f"{t1}-{t2}"))
    pairs_by_diff.sort()
    for td, hd, name in pairs_by_diff:
        print(f"{name:<30} {td:<6} {hd:<8}")

    # Correlation
    temp_diffs = [p[0] for p in pairs_by_diff]
    ham_dists = [p[1] for p in pairs_by_diff]
    mean_td = sum(temp_diffs) / len(temp_diffs)
    mean_hd = sum(ham_dists) / len(ham_dists)
    cov = sum((t - mean_td) * (h - mean_hd) for t, h in zip(temp_diffs, ham_dists)) / len(temp_diffs)
    std_td = math.sqrt(sum((t - mean_td)**2 for t in temp_diffs) / len(temp_diffs))
    std_hd = math.sqrt(sum((h - mean_hd)**2 for h in ham_dists) / len(ham_dists))
    corr = cov / (std_td * std_hd) if std_td * std_hd > 0 else 0
    print(f"\n  Correlation (temp_diff, hamming): {corr:.3f}")
    print(f"  (1.0 = perfect ordering, 0 = no ordering, -1 = reverse)")

    return encoded, corr


def test_snap_triple_physics():
    """Test the snap triple on physics concepts."""
    print(f"\n{'='*70}")
    print("SNAP TRIPLE on physics concepts")
    print(f"{'='*70}")

    mind = Mind(state_path=Path('/tmp/physics_triple.json'))

    # Directions
    dirs = ["left", "right", "up", "down", "forward", "back", "center"]
    dir_snaps = {d: mind.snap_op.snap(encode_direction_v2(d)) for d in dirs}

    print(f"\n--- Direction snap triples ---")
    print(f"{'Dir':<10} {'tax':<5} {'before_int':<12} {'after_int':<12}")
    print("-" * 42)
    for d in dirs:
        s = dir_snaps[d]
        print(f"{d:<10} {s.syndrome_tax:<5} {s.before_int:<12} {s.after_int:<12}")

    # Triple distance for physics pairs
    print(f"\n--- Triple distances (tax×before×after) ---")
    print(f"{'Pair':<25} {'triple':<10} {'tax_d':<6} {'before_d':<8} {'after_d':<8}")
    print("-" * 60)

    test_pairs = [
        ("left", "right"), ("up", "down"), ("forward", "back"),  # opposites
        ("left", "up"), ("left", "forward"), ("up", "forward"),   # orthogonals
        ("left", "center"), ("right", "center"),                   # center
    ]
    for w1, w2 in test_pairs:
        s1, s2 = dir_snaps[w1], dir_snaps[w2]
        td = mind.triple_distance(s1, s2)
        cmp = mind.triple_compare(s1, s2)
        print(f"{w1+'-'+w2:<25} {td:<10.1f} {cmp['tax_diff']:<6.0f} {cmp['before_dist']:<8.0f} {cmp['after_dist']:<8.0f}")

    # Physics check: opposites should have SMALLER triple than orthogonals
    opp_triples = [mind.triple_distance(dir_snaps[w1], dir_snaps[w2])
                   for w1, w2 in [("left","right"), ("up","down"), ("forward","back")]]
    orth_triples = [mind.triple_distance(dir_snaps[w1], dir_snaps[w2])
                    for w1, w2 in [("left","up"), ("left","forward"), ("up","forward")]]
    print(f"\n  Opposite mean triple: {sum(opp_triples)/len(opp_triples):.1f}")
    print(f"  Orthogonal mean triple: {sum(orth_triples)/len(orth_triples):.1f}")
    print(f"  Opposites closer? {sum(opp_triples)/len(opp_triples) < sum(orth_triples)/len(orth_triples)}")


def test_composition_v2():
    """Test: does left XOR right = something like center?"""
    print(f"\n{'='*70}")
    print("COMPOSITION v2 (left + right = ?)")
    print(f"{'='*70}")

    left = encode_direction_v2("left")
    right = encode_direction_v2("right")
    center = encode_direction_v2("center")

    print(f"\n  left:   {left.bits}")
    print(f"  right:  {right.bits}")
    print(f"  center: {center.bits}")

    # left XOR right — the "vector sum" in binary
    xor_lr = [a ^ b for a, b in zip(left.bits, right.bits)]
    print(f"\n  left XOR right: {xor_lr}")
    print(f"  (Only the sign bit should differ → XOR = sign bit pattern)")

    # The sign bit for X axis is bit 0. left has bit 0 = 1, right has bit 0 = 0.
    # XOR should be: bit 0 = 1, all else = 0.
    print(f"\n  Bit 0 (X sign): left={left.bits[0]}, right={right.bits[0]}, XOR={xor_lr[0]}")
    print(f"  Other bits should all be 0: {all(b == 0 for i, b in enumerate(xor_lr) if i != 0)}")

    # Snap the XOR
    snapped_bits, meta = GOLAY_ENGINE.snap_to_codeword(xor_lr)
    print(f"\n  left XOR right snapped: correctable={meta['correctable']}, distance={meta['anchor_distance']}")
    print(f"  (If it snaps to all-zeros (center), then left⊕right ≈ center)")


def main():
    print("=" * 70, flush=True)
    print("Physics Encoding — Round 2", flush=True)
    print("=" * 70, flush=True)

    dir_encoded = test_directions_v2()
    temp_encoded, temp_corr = test_temperatures_v2()
    test_snap_triple_physics()
    test_composition_v2()

    print(f"\n{'='*70}")
    print("VERDICT")
    print(f"{'='*70}")

    # Summary
    opp_dists = [hamming(dir_encoded[w1], dir_encoded[w2])
                 for w1, w2 in [("left","right"), ("up","down"), ("forward","back")]]
    orth_dists = [hamming(dir_encoded[w1], dir_encoded[w2])
                  for w1, w2 in [("left","up"), ("left","forward"), ("up","forward")]]
    opp_mean = sum(opp_dists) / len(opp_dists)
    orth_mean = sum(orth_dists) / len(orth_dists)

    print(f"\n1. DIRECTIONS:")
    print(f"   Opposites (left-right, up-down, forward-back): mean {opp_mean:.1f} bits")
    print(f"   Orthogonals (left-up, left-forward, up-forward): mean {orth_mean:.1f} bits")
    print(f"   Opposites closer than orthogonals? {opp_mean < orth_mean}")
    print(f"   → {'YES — physics emerges!' if opp_mean < orth_mean else 'NO — encoding needs work'}")

    print(f"\n2. TEMPERATURES:")
    print(f"   Correlation (temp_diff, hamming): {temp_corr:.3f}")
    print(f"   → {'YES — temperature ordering emerges!' if temp_corr > 0.5 else 'PARTIAL — weak ordering'}")


if __name__ == "__main__":
    main()
