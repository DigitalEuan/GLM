#!/usr/bin/env python3
"""Test: find a glue vector for odd-parity binary grids using octad structure."""
import sys
sys.path.insert(0, 'glm_repo'); sys.path.insert(0, 'scripts')
import warnings; warnings.filterwarnings('ignore', category=SyntaxWarning)
import numpy as np
from glm_universal.substrate import leech2, mog
from bin_tasks import sample_task

# Octads not containing position 0
octads = list(mog.OCTAD_MASKS)
octad_no_0 = [o for o in octads if not (o & 1)]
print(f'Octads total: {len(octads)}; octads not containing position 0: {len(octad_no_0)}')

# Glue: position 0 = -3, octad positions = -1, others = +1
def build_glue(octad_mask):
    glue = []
    for i in range(24):
        if i == 0:
            glue.append(-3)
        elif (octad_mask >> (23 - i)) & 1:
            glue.append(-1)
        else:
            glue.append(1)
    return tuple(glue)

# Generate 20 odd-parity grids
odd_grids = []
for trial in range(1, 200):
    x, _, _ = sample_task('toggle', seed=trial, H=4, W=6)
    bits = list(x.flatten())
    if sum(bits) % 2 == 1:
        odd_grids.append(bits)
    if len(odd_grids) >= 20:
        break

print(f'Odd-parity grids collected: {len(odd_grids)}')

# Try several octads
for octad_idx in [0, 1, 5, 50, 100, 300, 600]:
    if octad_idx >= len(octad_no_0):
        continue
    glue = build_glue(octad_no_0[octad_idx])
    ok = sum(1 for bits in odd_grids
             if leech2.in_leech(tuple(4*int(b) + g for b, g in zip(bits, glue))))
    print(f'  octad_no_0[{octad_idx}]: {ok}/{len(odd_grids)} odd-parity grids in Leech')

# Also test: for an odd-parity grid, search ALL octads to find one that makes it Leech
print('\nPer-grid search across all octads not containing pos 0:')
total_found = 0
for i, bits in enumerate(odd_grids[:5]):
    found_octad = None
    for o in octad_no_0:
        glue = build_glue(o)
        t = tuple(4*int(b) + g for b, g in zip(bits, glue))
        if leech2.in_leech(t):
            found_octad = o
            break
    if found_octad:
        total_found += 1
        print(f'  grid {i} (n_ones={sum(bits)}): found working octad')
    else:
        print(f'  grid {i} (n_ones={sum(bits)}): NO working octad among {len(octad_no_0)} tried')
print(f'Total: {total_found}/5 odd-parity grids have a working octad glue')
