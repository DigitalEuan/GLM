# The 24D Golay/Leech lattice shortcut — the working method

**Implementation:** `lattice_shortcut.py` (self-contained, stdlib only)
**Machine-checked core:** `RequestProject/*.lean` (Lean 4 + Mathlib, no `sorry`)
**Audit of the original directory:** `audit_ubp_directory.py`, `LATTICE_SHORTCUT_REPORT.md`

This document describes the method **as it works**, after the one substantive
bug in the original engine is fixed. Everything asserted here is either proved
in Lean (theorem names given) or checked at run time by
`python3 lattice_shortcut.py --selftest`.

---

## 1. In one paragraph

Integers are mapped into a 24-dimensional binary cube, snapped onto the nearest
codeword of the extended binary Golay code `[24,12,8]`, and the *difference*
between two snapped states, doubled, is an exact vector of the Leech lattice
`Λ₂₄`. The squared length of that vector is `4·d²` where `d²` is the Hamming
distance of the two codewords, and `d²` can only be `0, 8, 12, 16, 24`. A step
with `d² = 8` is a hop to a *nearest neighbour* in `Λ₂₄` (norm 32 — the minimum
norm of the lattice). The distance between two states never requires walking the
integers between them: on the encoding layer it is
`popcount(gray(a XOR b))`, three machine instructions.

---

## 2. The pipeline

```
   integer n
      │
      │  STAGE 1 — ENCODE          three 8-bit channels, Gray coded
      ▼
   w ∈ {0,1}²⁴
      │
      │  STAGE 2 — SNAP            complete Golay decoding (syndrome + full
      ▼                            4096-entry coset-leader table)
   c ∈ Golay[24,12,8]              ← THE FIX
      │
      │  STAGE 3 — STEP            Δv = c₂ − c₁ ,  d² = ‖Δv‖²
      ▼
   2Δv ∈ Λ₂₄ ,  ‖2Δv‖² = 4d² ∈ {0, 32, 48, 64, 96}
```

### Stage 1 — encode

Two encoders, both taken from the original work:

| encoder | channels | used for |
|---|---|---|
| `shift` (default) | `x = n & 0xFF`, `y = (n>>8) & 0xFF`, `z = (n>>16) & 0xFF` | the documented "continuous 24-bit bit-shift map" |
| `factor` | `x = p₁^e₁`, `y = p₂^e₂`, `z = ∏ remaining prime powers` (each mod 256); primes fall back to `shift` | what the published directory generator actually used |

Each channel byte `b` is Gray coded, `g = b ^ (b >> 1)`, and written MSB-first
into coordinates `8k … 8k+7`.

Nothing below depends on which encoder is used — the guarantees are properties
of stages 2 and 3. Two practical differences are worth knowing:

* under `shift`, consecutive integers differ in exactly **one** bit
  (`d²_raw = 1`; Lean: `d2_succ`), which is what makes the O(1) distance
  formula of §4 available;
* under `factor`, consecutive integers are **not** close at all — `1000034`
  and `1000035` have unrelated channel values — so "adjacent integers make
  large jumps" is a property of that encoder, not of the lattice.

### Stage 2 — snap (the fix)

The Golay code has 4096 codewords, minimum distance 8 and **covering radius 4**:
every 24-bit word is within Hamming distance 4 of a codeword. Snapping is a
single table lookup:

```python
def snap(state):
    return state ^ COSET_LEADER[syndrome(state)]        # always a codeword
```

The original `GolayCodeEngine.snap_to_codeword` only inverted error patterns of
weight ≤ 3 and **returned its input unchanged otherwise**, so roughly 43 % of
"snapped" states were not codewords at all — and every downstream lattice
statement silently failed for them. Building the leader table for all 4096
syndromes instead of only the 2325 low-weight ones costs nothing at run time.

At distance 4 the nearest codeword is *not* unique (1771 of the 4096 cosets have
six tied weight-4 leaders), so a convention is required. The one used here is:
minimum weight, then smallest coordinate mask — fixed once, in `COSET_LEADER`,
and used everywhere.

Machine-checked: `golay_covering_radius`, `decode_isGolay`,
`decode_dist_le_four`, `decode_eq_self_of_golay`, `decoding_not_unique`,
`substrate_snap_fails`.

### Stage 3 — step

For a transition `c₁ → c₂`:

* `Δv = c₂ − c₁ ∈ {−1,0,+1}²⁴`, and `d² = ‖Δv‖²` equals the Hamming distance
  `|c₁ ⊕ c₂|`;
* `2Δv` is an element of the Leech lattice in the integral `×√8` scaling
  (`corrected_step_isLeech`), of norm `‖2Δv‖² = 4d²` (`normSq_stepVec`);
* since `c₁ ⊕ c₂` is again a codeword and the code is doubly even with minimum
  weight 8, **`d² ∈ {0, 8, 12, 16, 24}`** (`corrected_quantized`);
* `d² = 8` ⟺ `‖2Δv‖² = 32` ⟺ the step is a **minimal vector** of `Λ₂₄`, i.e. a
  kissing-sphere hop (`corrected_octad_iff_minimal`, `leech_min_norm`).

---

## 3. A worked example

```
$ python3 lattice_shortcut.py --explain 1000003 1000033

STAGE 1 — ENCODE  (integer -> 24-bit word)
  1000003:  x= 67 y= 66 z= 15  -> Gray per byte -> 000100001100011001000110
  1000033:  x= 97 y= 66 z= 15  -> Gray per byte -> 000100001100011010001010

STAGE 2 — SNAP  (nearest Golay codeword, complete decoder)
  1000003:  000100001100011001000110  -> 000100001100000001001111   (4 bits corrected, weight 8)
  1000033:  000100001100011010001010  -> 000101101100011010101011   (4 bits corrected, weight 12)
       (a weight-4 correction: exactly the case the original engine
        could not handle and left unsnapped)

STAGE 3 — STEP  (jump vector and lattice class)
  Dv           = [0,0,-1,0,0,1,-1,1,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0]
  d^2 = ||Dv||^2 = 8   (octad (minimal vector))
  2Dv in Lambda_24, ||2Dv||^2 = 32   <- minimum norm: a kissing-sphere hop
  quantisation:  4 | d^2  -> True

SHORTCUT — the same raw metric without touching the interval
  a XOR b                  = 34
  popcount(gray(a XOR b))  = 4
  direct Hamming(w_a, w_b) = 4   (agrees)
```

Both states needed a **weight-4** correction — precisely the case the old engine
dropped. With the fix, the step is an exact minimal Leech vector.

---

## 4. The actual shortcut

Gray coding is `GF(2)`-linear on each channel, so

> **`d²_raw(a, b) = popcount( gray(a XOR b) )`**

(`d2_eq_pop_gray_xor`; `raw_d2_shortcut` in the script). The 24-dimensional
distance between the encodings of two integers is obtained from `a XOR b`
alone: an XOR, a shift-XOR and a popcount, independent of `|b − a|`. No
interval traversal, no enumeration of the 759 octads, no lattice search. Adding
the snap costs two more table lookups and gives the exact lattice distance.

This is the honest, provable content of the "geodesic shortcut" idea: it is a
shortcut for the **metric**, not for arithmetic.

---

## 5. What is guaranteed

| # | guarantee | Lean theorem | run-time check |
|---|---|---|---|
| G1 | every snapped state is a Golay codeword | `decode_isGolay` | ✔ |
| G2 | snapping moves a state by ≤ 4 bits | `decode_dist_le_four` | ✔ |
| G3 | `d² ∈ {0,8,12,16,24}` — quantisation by 4 | `corrected_quantized` | ✔ |
| G4 | `2Δv` is always a Leech vector | `corrected_step_isLeech` | ✔ |
| G5 | `‖2Δv‖² = 4d²`, `= 32` exactly for octad steps | `normSq_stepVec`, `corrected_octad_iff_minimal` | ✔ |
| G6 | 32 is the minimum norm of `Λ₂₄` | `leech_min_norm` | — |
| G7 | `d²_raw(a,b) = popcount(gray(a⊕b))` | `d2_eq_pop_gray_xor` | ✔ |
| G8 | the *old* engine's "100 % even quantisation" is a Golay-coset parity fact, true for any encoder and any integers | `legacy_even_quantisation` | ✔ |
| — | the generator matrix really gives Golay `[24,12,8]` | `golay_weight_distribution`, `golay_min_dist`, `golay_weight_div_four` | ✔ |

`python3 lattice_shortcut.py --selftest` re-checks all of these (except G6,
which is a statement about the infinite lattice) on samples of the state space.

### About G8

The old engine's headline observation, "`d² ∈ 2ℤ`, 100 % of transitions", is
**true** — but it is a theorem about the code, not a measurement of deep
integers:

* the Golay code is doubly even, so Hamming-weight parity is constant on each
  coset;
* the cosets the old engine failed to correct are exactly those with a
  weight-4 leader — even;
* hence *every* output of the old engine has even weight, and every distance
  between two of them is even, for any inputs whatsoever.

With the complete decoder the true law is the strictly stronger `4 ∣ d²`.

---

## 6. Node metrics (TGIC 3-6-9)

Reproduced exactly (in exact rational arithmetic) from the supplied engines, but
with the fixed snap inside the face transforms:

* `symmetry_tax(c) = hw·Y + ‖c‖²/8` with `Y = 1/(π + 2/π)`;
* `nrci(c) = 10/(10 + tax)`;
* **3** `tgic_3_axis_orthogonality` — rewards Hamming distance 4 between each
  pair of 8-bit blocks;
* **6** `tgic_6_face_coherence` — mean tax over the AND/XOR/OR face transforms;
* **9** `tgic_9_neighbour_pressure` — penalty beyond nine *other* nodes within
  distance 8 (the `ubp_tgic_engine.py` version counted the node itself; the
  `tgic_v3.py` version fixes this, as does the implementation here);
* `tgic_stability` — mean of orthogonality, coherence and NRCI, minus pressure.

For byte-for-byte reproduction of the published numbers the script also provides
`legacy_snap` and `reencode_snap`, the two snap variants the original engines
used; `audit_ubp_directory.py` confirms that both agree exactly with the
substrate.

These are scoring rules, not physical laws, and they are **not** primality
detectors: see the report for measurements.

---

## 7. Limits — read before using

1. **Many-to-one.** Snapping maps 2²⁴ words onto 4096 codewords. Ten thousand
   consecutive integers occupy only 526 distinct states, so 25 % of consecutive
   steps are collisions (`d² = 0`). A snapped state does not identify its
   integer (`snapEnc_collision`, `snapEnc_range`).
2. **No arithmetic acceleration.** Nothing here helps to factor, to test
   primality, or to "skip" to a target integer. The `factor` encoder *requires*
   the factorisation as input; it does not produce it.
3. **Not a primality signal.** The "propeller imbalance" of `value_geometry.py`
   is the coefficient of variation of `log p` over the *distinct* prime factors
   of `n`. It is exactly 0 for every prime power (e.g. `1018081 = 1009²`), and
   below the claimed composite threshold 0.15 for 2.7 % of the composites in
   `[10⁶, 10⁶+10⁴)` (e.g. `1005973 = 997 × 1009`, imbalance 0.00087).
4. **A tie-break is a choice.** At distance 4 six codewords may be equally near;
   results at that distance depend on the convention, which is why it is fixed
   and documented rather than left implicit.

---

## 8. Command reference

```bash
python3 lattice_shortcut.py --selftest                 # verify every guarantee
python3 lattice_shortcut.py --explain 1000003 1000033  # narrate one transition
python3 lattice_shortcut.py --walk 1000003 1000033 1000037
python3 lattice_shortcut.py --range 1000033 1000051 --map factor
python3 lattice_shortcut.py --primes 1000000 20        # walk 20 deep primes
python3 lattice_shortcut.py --stats 1000000 10000      # aggregate statistics
python3 lattice_shortcut.py --tgic 1000003             # node report
python3 lattice_shortcut.py --range 1000033 1000051 --json out.json
```

Typical output of `--stats 1000000 10000` (encoder `shift`):

```json
{"steps": 9999, "d2_histogram": {"0": 2517, "8": 7482},
 "octad_rate_pct": 74.83, "collision_rate_pct": 25.17,
 "all_quantised_by_4": true, "all_leech_vectors": true,
 "distinct_states": 526, "legacy_non_codeword_rate_pct": 43.16}
```

Every step is an exact Leech-lattice vector; three quarters of them are minimal
(kissing-sphere) hops; and the last figure is what the old engine was getting
wrong.
