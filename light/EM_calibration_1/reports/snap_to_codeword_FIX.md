# Fixing the `snap_to_codeword` Bug in `GMHGL/ubp_unified_v5.py`

**Date:** 2026-08-06
**Bug:** `GolayCodeEngine.snap_to_codeword` returns non-codewords for ~43% of inputs
**Lean proof of bug:** `leech_lattice/RequestProject/Substrate.lean` theorem `legacySnap_not_codeword`
**Lean proof of fix:** `leech_lattice/RequestProject/Decoder.lean` theorems `decode_isGolay`, `decode_dist_le_four`

---

## The bug in one sentence

`GolayCodeEngine._build_syndrome_table` (line 582 of `ubp_unified_v5.py`) only builds coset leaders for Hamming weights 0, 1, 2, 3 — it omits weight 4. Since the Golay code's covering radius is 4 (a theorem, see Lean `golay_covering_radius`), this leaves 1,771 of the 4,096 cosets without a leader. When `snap_to_codeword` looks up one of these missing syndromes, it returns its input UNCHANGED — and ~43% of the time, that input is NOT a codeword.

The Lean theorem `legacySnap_not_codeword` proves this explicitly for input `15`:
```
legacySnap 15 = 15  ∧  ¬ IsGolay 15
```

The further theorem `legacy_d2_not_div_four` shows that the legacy engine produces `d² = 2` for the transition `15 → 23`, which is **impossible** between two genuine Golay codewords (the true law is `4 | d²`, so `d² ∈ {0, 8, 12, 16, 24}`).

The published "100% even d²" observation is therefore a tautology — Lean `legacy_even_quantisation` proves it follows from the parity structure of Golay cosets, NOT from any deep property of the integers being encoded.

---

## The fix (one block to add, no other changes needed)

You only need to extend `_build_syndrome_table` to include weight-4 patterns. The `snap_to_codeword` method itself does NOT need to change — once the table is complete, the `if st in self._syn_table` check at line 622 will always succeed.

### Step 1: Open `GMHGL/ubp_unified_v5.py` and locate lines 581–605

You're looking for this method (the comment at line 581 says "lazy: 2325 entries for weight ≤ 3"):

```python
    # ── syndrome table (lazy: 2325 entries for weight ≤ 3) ────────────────────
    def _build_syndrome_table(self) -> Dict[Tuple[int, ...], List[int]]:
        cols = self._H_cols
        table: Dict[Tuple[int, ...], List[int]] = {}
        # weight 0
        table[tuple([0]*12)] = [0]*24
        # weight 1
        for i in range(24):
            e = [0]*24; e[i] = 1
            table[cols[i]] = e
        # weight 2
        for i in range(24):
            for j in range(i+1, 24):
                s = tuple(a ^ b for a, b in zip(cols[i], cols[j]))
                e = [0]*24; e[i] = 1; e[j] = 1
                table[s] = e
        # weight 3
        for i in range(24):
            for j in range(i+1, 24):
                sij = tuple(a ^ b for a, b in zip(cols[i], cols[j]))
                for k in range(j+1, 24):
                    s = tuple(a ^ b for a, b in zip(sij, cols[k]))
                    e = [0]*24; e[i] = 1; e[j] = 1; e[k] = 1
                    table[s] = e
        return table
```

### Step 2: Replace the entire method with this (just adds the weight-4 block)

```python
    # ── syndrome table (complete: 4096 entries, weights 0..4) ─────────────────
    # FIX per leech_lattice/RequestProject/Decoder.lean (Lean theorems
    # `golay_covering_radius`, `decode_isGolay`, `decode_dist_le_four`).
    # The previous version only built weights 0..3 (2,325 entries) and silently
    # returned non-codewords for the 1,771 weight-4 cosets (43% of inputs).
    # See Substrate.lean `legacySnap_not_codeword` for the proof of the bug.
    def _build_syndrome_table(self) -> Dict[Tuple[int, ...], List[int]]:
        cols = self._H_cols
        table: Dict[Tuple[int, ...], List[int]] = {}
        # weight 0
        table[tuple([0]*12)] = [0]*24
        # weight 1
        for i in range(24):
            e = [0]*24; e[i] = 1
            table[cols[i]] = e
        # weight 2
        for i in range(24):
            for j in range(i+1, 24):
                s = tuple(a ^ b for a, b in zip(cols[i], cols[j]))
                e = [0]*24; e[i] = 1; e[j] = 1
                table[s] = e
        # weight 3
        for i in range(24):
            for j in range(i+1, 24):
                sij = tuple(a ^ b for a, b in zip(cols[i], cols[j]))
                for k in range(j+1, 24):
                    s = tuple(a ^ b for a, b in zip(sij, cols[k]))
                    e = [0]*24; e[i] = 1; e[j] = 1; e[k] = 1
                    table[s] = e
        # weight 4 — THE FIX (covers the remaining 1,771 cosets)
        # Per Lean `golay_covering_radius`: every 24-bit word is within Hamming
        # distance 4 of a codeword, so this completes the decoder.
        # Per Lean `decoding_not_unique`: at distance 4 the nearest codeword is
        # not unique (1,771 cosets have 6 tied weight-4 leaders). The tiebreak
        # convention below is: first-found = lex-smallest by index order. This
        # matches Decoder.lean's `leaderNat` ("minimum weight, then smallest
        # coordinate mask").
        for i in range(24):
            for j in range(i+1, 24):
                sij = tuple(a ^ b for a, b in zip(cols[i], cols[j]))
                for k in range(j+1, 24):
                    sijk = tuple(a ^ b for a, b in zip(sij, cols[k]))
                    for l in range(k+1, 24):
                        s = tuple(a ^ b for a, b in zip(sijk, cols[l]))
                        if s not in table:  # only add if not already covered
                            e = [0]*24
                            e[i] = 1; e[j] = 1; e[k] = 1; e[l] = 1
                            table[s] = e
        return table
```

### Step 3 (optional but recommended): Update the comment on `snap_to_codeword`

The method itself works correctly without changes, but the comment is now misleading. Locate lines 611–629 and update the comment:

```python
    # ── snap (complete decoder: corrects any pattern of weight ≤ 4) ──────────
    # Per Lean `decode_isGolay`: the result is always a Golay codeword.
    # Per Lean `decode_dist_le_four`: snap distance is ≤ 4 (the covering radius).
    # The `else` branch below is now unreachable (the table is complete), but is
    # kept as a defensive fallback.
    def snap_to_codeword(self, v24: List[int]) -> Tuple[List[int], Dict[str, Any]]:
        if len(v24) != 24:
            raise ValueError("snap: 24 bits required")
        s = self.syndrome(v24)
        sw = sum(s)
        if sw == 0:
            return list(v24), {"syndrome_weight": 0, "corrected": False,
                               "anchor_distance": 0, "correctable": True}
        self._ensure_syn_table()
        st = tuple(s)
        if st in self._syn_table:
            e = self._syn_table[st]
            corrected = [v24[i] ^ e[i] for i in range(24)]
            d = sum(e)
            return corrected, {"syndrome_weight": sw, "corrected": True,
                               "anchor_distance": d, "correctable": True}
        # Unreachable after the weight-4 fix (table is complete, 4096 entries).
        # Kept as a defensive fallback per Lean `decode_isGolay`.
        return list(v24), {"syndrome_weight": sw, "corrected": False,
                           "anchor_distance": -1, "correctable": False}
```

### Step 4: Verify the fix

After saving, run this one-liner to confirm:

```python
python3 -c "
import sys; sys.path.insert(0, 'GMHGL')
from ubp_unified_v5 import GolayCodeEngine
ge = GolayCodeEngine()
ge._ensure_syn_table()
print(f'Table size: {len(ge._syn_table)} entries (should be 4096)')

# Test the Lean counterexample: input 15
v24 = [(15 >> i) & 1 for i in range(24)]
cw, meta = ge.snap_to_codeword(v24)
all_cws = set(tuple(c) for c in ge.get_all_codewords())
is_cw = tuple(cw) in all_cws
print(f'snap(15) is codeword: {is_cw} (should be True after fix)')
print(f'snap(15) anchor_distance: {meta[\"anchor_distance\"]} (should be 4)')

# Count failures across all 2^24 inputs is too slow; sample 10000
import random
random.seed(0)
fails = 0
for _ in range(10000):
    n = random.randint(0, (1<<24) - 1)
    v = [(n >> i) & 1 for i in range(24)]
    cw, meta = ge.snap_to_codeword(v)
    if tuple(cw) not in all_cws:
        fails += 1
print(f'Random sample failures: {fails}/10000 (should be 0 after fix)')
"
```

Expected output after fix:
```
Table size: 4096 entries (should be 4096)
snap(15) is codeword: True (should be True after fix)
snap(15) anchor_distance: 4 (should be 4)
Random sample failures: 0/10000 (should be 0 after fix)
```

---

## What changes, what doesn't

**Changes:**
- `_build_syndrome_table` now returns 4,096 entries instead of 2,325
- `snap_to_codeword` now ALWAYS returns a codeword (was returning non-codewords ~43% of the time)
- `decode` (which calls `snap_to_codeword`) is now correct
- Any downstream code that depends on `snap_to_codeword` (Data Object encoding, lattice shortcut, etc.) now gets genuine codewords

**Does NOT change:**
- The generator matrix `G`, parity-check matrix `H`, or any other structure
- The encoding function (it was always correct — it's a linear code)
- The syndrome computation
- The set of 4,096 codewords
- The 759 octads (weight-8 codewords)
- Any other engine function

**Performance cost:**
- The table now has 4,096 entries instead of 2,325 (memory: ~400 KB vs ~230 KB)
- Building the table takes ~1 second longer (one-time cost, lazy-loaded)
- Lookup speed is unchanged (O(1) dict lookup either way)

---

## Why this matters for the calibration study

Before the fix, any substrate experiment that called `snap_to_codeword` on a weight-4 coset input was getting a **non-codeword** back — meaning all downstream Leech-lattice claims (norm² = 32 for minimal vectors, `4 | d²` for transitions, etc.) were silently broken for those inputs. The Lean theorem `legacy_d2_not_div_four` proves this: the legacy engine produces `d² = 2` for the transition `15 → 23`, which is mathematically impossible between two genuine codewords.

After the fix, every snap returns a genuine codeword, every transition has `d² ∈ {0, 8, 12, 16, 24}` (per Lean `corrected_quantized`), and every octad transition is a genuine minimal Leech vector (per Lean `corrected_octad_iff_minimal`). The calibration experiments can then trust the substrate dynamics.

---

## Reference: the Lean theorems (from `leech_lattice/RequestProject/`)

| File | Theorem | Statement |
|---|---|---|
| `Decoder.lean` | `golay_covering_radius` | Every 24-bit word is within Hamming distance 4 of a codeword |
| `Decoder.lean` | `decode_isGolay` | The complete decoder always returns a codeword |
| `Decoder.lean` | `decode_dist_le_four` | Snap distance is ≤ 4 |
| `Decoder.lean` | `decode_eq_self_of_golay` | Codewords are fixed points of the decoder |
| `Decoder.lean` | `decoding_not_unique` | At distance 4, the nearest codeword is not unique (6 ties per coset) |
| `Decoder.lean` | `substrate_snap_fails` | Explicit counterexample: input 15 returns non-codeword under legacy |
| `Substrate.lean` | `legacySnap_not_codeword` | `legacySnap 15 = 15 ∧ ¬ IsGolay 15` |
| `Substrate.lean` | `legacySnap_even_weight` | Every legacy output has even Hamming weight (even when non-codeword) |
| `Substrate.lean` | `legacy_even_quantisation` | The "100% even d²" is a tautology (parity of Golay cosets) |
| `Substrate.lean` | `legacy_d2_not_div_four` | Legacy produces d²=2 (impossible for true codewords) |
| `Shortcut.lean` | `corrected_quantized` | True law: d² ∈ {0, 8, 12, 16, 24} (i.e., 4 \| d²) |
| `Shortcut.lean` | `corrected_octad_iff_minimal` | d²=8 transitions are exactly the minimal Leech vectors |
| `Shortcut.lean` | `snapEnc_collision` | `snapEnc 1000037 = snapEnc 1000038` (consecutive integers collapse) |

The last theorem is the user's point #2: lattice hops are a metric shortcut, not substrate dynamics. The substrate doesn't propagate by hopping between codewords — it propagates by relaxation events (TAX-minimizing transitions). The fix above ensures those relaxation events are computed on genuine codewords.
