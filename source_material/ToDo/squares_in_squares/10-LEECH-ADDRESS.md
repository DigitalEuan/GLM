# 10 — 24 pockets as an address space for packings

**Run 43, 2026-11-17.** Instrument `scripts/leech_address.py`; ledger
`workspace/push/leech_address.json`. Read-only.

The proposal: the Leech lattice's 24 coordinates are 24 pockets; put data in
them, arrange the pockets systematically, and use the arrangement as a higher
language for this puzzle. This document builds that, measures it, and separates
what the measurement refutes (my feature map) from what the mathematics
supports (the lattice as a quantiser).

---

## 1. What the repository already has

Three assets, all relevant:

* **`src/lean/RequestProject/GLM/Escalation/LeechResidue.lean`** — the exact
  integer form of the lattice: `x ∈ √8·Λ₂₄` iff the 24 coordinates share a
  parity `m`, `Σx ≡ 4m (mod 8)`, and each residue class mod 4 is a codeword of
  the GLM's own Golay code. It also proves a **warning**: the syndromes mod
  8, 144 and 256 do not see deep holes, because `Λ₂₄ + mℤ²⁴ = Λ₂₄` for `8 ∣ m`.
  Coarse modular addresses on the lattice carry no information. That is the
  trap this document then walks into and measures.
* **`leechlean/3_leech_bridge/out/codebook.json`** — **39,992 tokens**, each a
  24-pocket integer vector (e.g. `"ws: " → [0,0,2,0,2,4,0,0,0,0,-2,0,-2,-2,-2,-2,0,-2,2,0,2,0,2,-2]`).
  The "24 pockets holding data" idea is already built in this repo — for text.
* **The Golay code** (24 bits, 4096 words, minimum distance 8), which is what
  makes 24 bits a *legal* address space rather than an arbitrary one.

## 2. The mapping used

Square symmetry puts `θ mod π/2`, and the CRAM study already used 6 angle bins,
so 24 = **6 angle sectors × 4 radial shells**:

```
pocket(i) = (floor(6θ/(π/2)), clamp(floor(4·r/(L/2)), 0, 3))    r = |centre_i − centre| / (L/2)
```

A packing → 24 counts → normalise → threshold at the mean → 24-bit word → snap
to the **nearest extended Golay codeword**. The codeword is the address.
Minimum distance 8 is the claimed error correction: words within 4 bits share an
address.

Verified first: **4096 codewords, minimum nonzero weight 8, maximum 24** — the
code is the extended Golay code, not something that merely looks like it.

## 3. What the measurement says

Over the 1000 delivered rows:

| quantity | value |
| --- | ---: |
| distinct addresses | **50** of 1000 rows |
| address entropy | **2.811 bits** (max 12) |
| snap distance to nearest codeword | median **4**, max 4, exact 0 |
| **MI(address; beats grid)** | **0.1930 bits** (H = 0.881) |
| permutation null for that MI | mean 0.0431, max 0.0644 |
| MI(address; residue r) | 0.9198 bits (H = 5.670) |
| MI(address; band k) | 0.5626 bits (H = 4.725) |

Pocket occupation (fraction of all squares), and it is extremely skewed:

| sector | shell 0 | 1 | 2 | 3 |
| --- | ---: | ---: | ---: | ---: |
| 0–15° | 0.042 | 0.122 | 0.199 | **0.460** |
| 15–30° | 0.001 | 0.004 | 0.015 | 0.026 |
| 30–45° | 0.006 | 0.013 | 0.013 | 0.009 |
| 45–60° | 0.001 | 0.003 | 0.003 | 0.003 |
| 60–75° | 0.001 | 0.005 | 0.017 | 0.029 |
| 75–90° | 0.001 | 0.004 | 0.006 | 0.018 |

**82% of all squares sit in sector 0**, one pocket holds **46%** of the corpus,
and the emptiest (pocket 16) holds **0.07%**. The 24 pockets are not 24 useful
pockets; they are about 6 useful pockets and 18 near-empty ones.

Stability under the project's own perturbation:

| n | word distance | address | ΔE at amp 0.005 / 0.02 / 0.08 |
| ---: | ---: | --- | --- |
| 60 | 3 | **always 8 bits away** (different codeword) | 2.1e-3 / 3.3e-2 / 4.6e-1 |
| 240 | 6 | always 8 bits away | 6.0e-3 / 9.4e-2 / 1.4e+0 |
| 961 | 4 | always 8 bits away | 2.8e-2 / 4.4e-1 / 6.4e+0 |

## 4. Diagnosis: two failures, both structural

1. **The address encodes the puzzle, not the packing.** MI with residue `r` is
   0.92 bits and with band `k` is 0.56 — the address is largely a proxy for `n`.
   MI with the *outcome* that matters (does the row beat grid) is real but small:
   0.193 against a null of 0.043, so ~0.15 bits of genuine signal. The pocket
   histogram is mostly counting *how many squares are axis-aligned at this size*,
   which is a size statement.
2. **Snapping to the code destroys gradation.** Every distinct address is at
   least **8 bits** away — that is what minimum distance 8 *means* — so Hamming
   distance in address space cannot rank anything. Measured: a perturbation that
   raises the energy by 2e-3 and one that raises it by 4.6e-1 land on addresses
   the same 8 bits apart. The address is a step function with no metric left to
   be a *language* with.

This is the same failure shape as `LeechResidue.lean`'s warning, and the same
one as the CRAM contact word (Jaccard 0.018–0.054): a coarse global quantisation
of a packing says almost nothing about the packing. The negative is specific:
**24 global histogram pockets + Golay snapping cannot address this data.**

## 5. What the mathematics does support

The instinct that 24 dimensions are the right number is not wrong — it is
*provable*, but for a different job than "pockets as bins". Λ₂₄ is the **best
known lattice quantiser in dimension 24**, and that is exactly the "address
space" property one wants:

| | Λ₂₄ | ℤ²⁴ (cubic) |
| --- | ---: | ---: |
| normalised second moment `G` (quantisation error per unit density) | **0.0658** | 0.0833 (= 1/12) |
| covering radius² `μ` | 4 | 1 |
| kissing number | 196,560 | 48 |

So at equal density Leech encodes 21% less error than a cubic grid, and its
covering is 4× better in squared radius. **If** the packing feature vector lives
in 24 dimensions with comparable scales, then Λ₂₄ is the right quantiser — and
the correct use is *nearest lattice point plus the residual vector*, not
snapping to a codeword and throwing the residual away.

That is the design this measurement points at:

* **Per-square, not global.** One address per square (or per contact), laid out
  in the 24 pockets as (angle sector, shell) *with real-valued counts kept*, not
  thresholded. This preserves gradation, which the measurement shows is what the
  global version loses.
* **Lattice as quantiser, not as alphabet.** Compute the nearest Λ₂₄ point and
  keep `x − λ` as the language. The residual is graded, stable under small
  motion (bounded by the covering radius), and lives in 24 dims where the
  lattice is optimal.
* **Both claims are testable**: residual norm should correlate with ΔE
  (Spearman), and residual direction should repeat across the bistable seeds
  found in PL-15.

## 6. What is refuted, and what is not

* **Refuted:** 24-dim *global histograms*, thresholded and Golay-snapped, as an
  addressing language for packings. 50 addresses, 2.8 bits, no metric, mostly
  encoding `n`. Do not build on it.
* **Not refuted, and supported by the literature rather than by me:** Λ₂₄ as the
  quantiser for a *per-square* 24-dim feature. I have not measured that — the
  next instrument would, and the falsifier is stated above.

## 7. Reproduction

```bash
python3 scripts/leech_address.py --json     # ~20 s
```

---

## 8. Snapping as a measurement (run 44)

Treating the snap as an *action* is what failed in §4: the word is replaced and
the code's minimum distance 8 flattens everything to "different". Treat it as a
*measurement* and the object is the **statistic of the snap**, which the code
does not flatten. Instrument `scripts/leech_measure.py`, controls
`scripts/leech_snap_controls.py`, ledgers `leech_measure.json` /
`leech_snap_controls.json`.

### Three corrections to §4

1. **The hard distance is graded, not saturated.** §4 reported "median 4, max 4"
   and implied a constant. The histogram is `{1: 5, 2: 27, 3: 296, 4: 672}`,
   variance 0.316 — 32 rows sit within one or two bits of a legal word, and the
   distance carries `MI = 0.0831` bits about beating grid. Reporting only the
   median was a presentation error that hid the measurement.
2. **My first soft statistic was degenerate, and I caught it by looking.** The
   uncentred correlation of the shares with a codeword's ±1 pattern scored
   **exactly 1.0000 for all 1000 rows**: since the pocket support nearly always
   fits inside some weight-16 or weight-24 codeword, "max correlation" was a
   support-coverage test, not a similarity. Centred, it behaves: ρ₁ ∈
   [0.278, 0.671], median 0.471, sd 0.061, **995 distinct values**.
3. **"No metric left" holds only for codeword Hamming.** Distance-to-code, the
   Euclidean distance to `{0,1}²⁴ ∩ C`, and the soft profile are all graded.

### The observables

| statistic | spread | MI with beats grid |
| --- | --- | ---: |
| hard distance `d(w,C)` | `{1:5, 2:27, 3:296, 4:672}` | 0.0831 |
| Euclidean distance to the code | median 12.54, sd 2.56 | 0.1722 |
| centred ρ₁ | 0.278 – 0.671, 995 values | 0.1239 |
| **decisiveness gap** `ρ₁ − ρ₂` | median 0.0044, max 0.1726 | **0.2955** |
| permutation null | — | 0.0019 mean, 0.0046 max |

### The controls — and the one that decides

| quantity | value |
| --- | ---: |
| I(band k; beats) | 0.0163 |
| I(residue r; beats) | 0.4438 |
| I(gap; beats) | 0.2955 |
| **I(gap; beats \| band)** | **0.3619** — *rises*, so it is not band-mediated |
| **I(gap; beats \| residue)** | **0.1356** |
| within-residue permutation (300 reps) | null 0.0549 ± 0.0082, max 0.0785 |
| **z** | **+9.87**, p < 0.0001 → excess **≈ 0.081 bits genuine** |

So the decisiveness of the nearest-codeword measurement tells you something
about whether a row beats grid that is **not** just its residue class — 0.081
bits after the null is subtracted, roughly 9% of `H(beats) = 0.881`. It is the
first 24-pocket statistic in this project to survive controls.

### What it is not

**It does not track energy.** Spearman(Δgap, ΔE) over 20 seeds × 3 amplitudes ×
3 rows: −0.061 (n=60), −0.132 (n=240), +0.108 (n=961), pooled −0.124. So the
statistic is a **static property of a configuration**, not a local energy gauge —
it says which puzzles look decisively legal, not how good a perturbation was.
The PL-26 falsifier in that direction fails, and I record it as failed.

The direction of the effect (are beating rows *more* or *less* decisive?) is not
measured; that is PL-28. Nor is 0.081 bits a certificate — it is a ranking
prior, and its use would be to order the rows inside a residue column when
searching for the base that PL-21 needs.

---

## 9. The prior is a rotation detector (run 45)

PL-28 asked for the sign and the use. The sign is positive and strong, and then
the control destroys the claim, which is the correct outcome to record.

**Sign.** Beating rows are *more* decisive: mean gap 0.03155 vs
0.01772 for grid rows, `AUC(gap -> beats) = 0.7540`
(permutation null 0.4999 ± 0.0189, z = +13.48). Per-column median AUC 0.716
(IQR 0.667–0.782, 95% of columns above 0.5). That looked like the first usable
prior in this project.

**The mechanism, visible in the medians.** Grid rows have gap median **0.0000**
and 63.4% are exactly zero
(700 grid rows); beating rows have gap median 0.02287 and only
10 of 300 are zero. A gap of exactly zero means ρ₂ = ρ₁:
the pocket vector sits *on* a codeword. An axis-aligned grid does exactly that —
every square at θ = 0 puts all occupancy in one sector. So the statistic was
measuring **whether the packing is rotated**.

**The control.**

| quantity | value |
| --- | ---: |
| rotated among beating rows | 100.0% |
| rotated among grid rows | 36.1% |
| **AUC(rotation -> beats)** | **0.8193** |
| AUC(gap -> beats), all rows | 0.7540 |
| **AUC(gap -> beats), rotated rows only** | **0.3495** |
| MI(rotation; beats) | 0.3312 (null 0.0007) |
| MI(gap quartile; beats) | 0.2276 (null 0.0015) |
| **MI(gap; beats \| rotation)** | **0.0304** |
| MI(rotation; beats \| gap) | 0.1340 |

87% of the gap's information disappears once rotation is known, while rotation
keeps 40% of its own after controlling the gap: the information flows
*rotation → gap*, not the other way. And among rotated rows the gap is mildly
*anti*-predictive (AUC 0.3495 < 0.5). A one-bit rotation flag —
which we can read off the angles directly — explains the address statistic
better than the address statistic explains anything.

**So it is not a prior.** 0.0304 bits survive, which is
neither zero nor useful: it does not rank rows by value either. Among rotated
beating rows `Spearman(gap, δ) = +0.166` — and
positive means *more decisive ↔ larger slack ↔ worse packing*, the wrong
direction for a quality prior. The attack list built in `leech_prior.py` (rows
nearest the beating-row profile) therefore does **not** rank quality, and I am
retracting its use; it is at most an ordering with no evidence behind it.

**Correction to part 8's headline.** The claim "first 24-pocket statistic to
survive controls" was tested against the residue control only. It does not
survive the rotation control, which is the more parsimonious explanation, and a
statistic that is a rewrite of a one-bit flag we already had is not a language.

## 10. A correction to the base count (39 columns, not 23)

Measuring directly from the delivered table rather than from the cascade model:
**21 residues contain at least one beating row; 39 do not** (r = 0, 22, 24–60).
§09-CASCADE.md reported "37 of 60 residues with a base", and that figure came
from the planner's *model* (a chain the code believed it could build), not from
the delivered packings. The measured number is the smaller one, so **PL-21's
population is 39 columns, not 23**, and its ceiling is correspondingly larger:
the residues including 22 and 24–37 add weight that the earlier table omitted.

## 11. Where the Leech thread ends

Three instruments, three closures, all honest:

| claim | verdict |
| --- | --- |
| 24 pockets + Golay snapping as an address alphabet | **closed**: 50 addresses, 2.8 bits, encodes `n` |
| snapping as a measurement (distance, ρ₁, gap) | **closed**: the measurement is a rotation detector (87% mediated) |
| Λ₂₄ as a quantiser for a per-square feature (PL-26) | **not tested**, and no longer motivating: the feature map, not the lattice, is the bottleneck |
| the lattice itself | untouched — nothing measured here fails it, and nothing measured here needed it beyond the Golay code that generates it |

The one thing this thread produced that has score value is not the address: it is
the measurement that **39 residue columns have never been opened**, against an
earlier record that said 23. That is where the remaining 7.195366 of grid score
sits, and it is search work, not language work.

---

## 12. Two instrument errors — every number in parts 7-9 re-measured (run 47)

Building the area ceiling exposed two bugs in my own instruments, and both
contaminate parts 7-9. `scripts/leech_audit_fix.py` re-measures everything; it
reproduces the delivered table to 1.3e-10 and 553 beats and cross-checks 20 rows
against `packlib.verify`.

**Error 1 — wrong score scale.** Parts 7-10 scored `10/L`. The repository scores
`sum(L/sqrt(n) - 1)`, which gives 22.218056945, and `10/L` gave 593.279 for the
same table. Absolute totals in `11-AREA-CEILING.md` are rebuilt.

**Error 2 — inflated bounding box.** Every Leech instrument computed
`L = max(x) + max(ex) - (min(x) - min(ex))` instead of the per-square
`max(x_i + ex_i) - min(x_i - ex_i)`. That inflates L and reclassified **253 of
the 553** beating rows as grid: the instruments saw 300 beats where the delivered
table has 553. Every `beats` label in parts 7-9 came from it.

### What changes, re-measured against the correct target

| | part 8/9 (broken target) | corrected |
| --- | ---: | ---: |
| beats / grid | 300 / 700 | **553 / 447** |
| AUC(gap -> beats) | 0.7540 | **0.9861** |
| AUC(rotation -> beats) | 0.8193 | **1.0000** |
| MI(rotation; beats) | 0.3312 | **0.9919** |
| MI(gap quartile; beats) | 0.2276 | **0.8687** |
| **MI(gap; beats \| rotation)** | 0.0304 | **0.0000** |

With the target correct the conclusion is not weaker, it is total:
**rotation predicts beating grid perfectly** (AUC 1.0000, MI 0.9919, every
beating row rotated *and* every grid row unrotated), and the snap statistic adds
**exactly nothing** once rotation is known — `MI(gap; beats | rotation) = 0.0000`.
The address is a rewrite of a one-bit flag, with zero residual information.

**Withdrawal.** Part 8's "≈0.081 bits genuine, the first 24-pocket statistic to
survive controls" is withdrawn in full. It was a property of the mislabelled
target, not of the address space: with 253 beating rows wrongly called grid, a
rotation proxy looked like partial information.

**Also withdrawn: PL-30.** The corrected target gives **37 residues with a
beating row and 24 without**, which is the record's original figure. My "39
base-less columns" was the phantom of the inflated box — the extra 15 were
columns whose beating rows the bug had hidden.

### What survives from the Leech thread

* The Golay machinery is correct: 4096 codewords, min nonzero weight 8, verified.
* The hard distance is graded (histogram `{1:5, 2:27, 3:296, 4:672}` stands — it
  does not depend on the target).
* The address alphabet claim (part 7) stands: 50 addresses, 2.811 bits, MI with
  residue 0.9198 — all computed without a `beats` label.
* Everything that used a `beats` label is superseded by the table above.
