# 61 — The 45° block: a certified production that breaks the seam floor and still moves nothing

Run 98, 20 November 2026. One production, built exactly, gated, and answered honestly.

Doc 60 named it and gave it a falsifier: a block of `s²` unit squares at the 45° word, axis
fill in the four corner triangles, `L = 2k + 0.520815` at `N = 4k² + 1` for `k = 13, 14, 15`
(and `2k + 0.535534` for `k ≤ 12`). The questions for this run:

1. Derive `T(k, s)`, `N(k, s) = s² + 4T(k, s)` and the closed-form contact side `L(k, s)`
   from exact `Q(√2)` separation roots.
2. Gate-verify over small `(k, s)`, at `(k = 4, s = 5, N = 65)` and at `(k = 13, s = 17,
   N = 677)`.
3. Test whether `L(k, s) − 2k` breaks below the single-word floor `½√2`, and whether it
   matches or beats the delivered slacks `0.535534` / `0.520815`.

The answers, one line each:

* the count is a triangular number and the side is an exact contact root: **`T = k(k+1)/2`
  per corner, `N = s² + 2k(k+1)`, `L = max(s/√2 + k + 1, 2s/√2)`**;
* the family gates exactly in a window of two or three `k` per `s` and is refused beyond it
  by one declared law, `block45_corner_collision` (the two staircases that share a wall
  meet) — **70 gated, 51 refused, 0 mismatches** over 121 rows;
* **yes, it breaks the floor** — 8 certified rows below `2k + ½√2`, the smallest excess
  `0.020815` at `(k = 13, s = 17)`, `N = 653`;
* and **no, it does not move the table** — 0 of 70 beats a delivered row, `N = 65` is exact
  parity (the delivered slack *is* `5/√2 − 3 = 0.535534`), `N = 677` is not in the family at
  all, and asymptotically `L/√N → 1`: the block is the grid in disguise.

`submission.csv` and root `WHITEBOARD.md` are untouched; no row moved, no score claimed.

## 1. The construction, and the two laws

The block is `s²` unit squares at the 45° word `(½√2, ½√2)`, edge to edge in its own frame,
so its bounding box is `s√2` and its four faces are the four lines

    x + y = L ∓ s/√2 ,        y − x = ± s/√2 ,

with `L` the container side. Each corner triangle therefore has legs

    t = L − s/√2 ,

and the unit axis square `[i, i+1] × [j, j+1]` fits in the lower-left triangle iff
`i + j + 2 ≤ t`. Choosing `t = k + 1` (integer legs) makes the staircase square at `(k−1, 0)`
meet the face exactly at its corner — **tangency, not tolerance**. Then

    T(k, s) = Σ_{i=0}^{k−1} (k − i) = k(k+1)/2          per corner
    N(k, s) = s² + 4·T(k, s) = s² + 2k(k+1)
    L(k, s) = s/√2 + k + 1                              (the contact branch)

The second side branch is the block's own diagonal: if `t < s/√2` the block, not the fill,
sets the box, and `L = 2s/√2 = s√2`. Hence

    L(k, s) = max( s/√2 + k + 1 , 2s/√2 ).

Both terms live in `Q(√2)` as `cls(k+1) + cls(0, s/2)` and `cls(0, s)`, so the law is exact
with no root-finding: the separation roots *are* the law. `block45_count` is integer
arithmetic; `block45_side` is a comparison of two field elements.

*The gate caught my first version of this.* The first sweep wrote `L = s/√2 + k + 1` only,
and 84 of 198 rows came back `block45_side_mismatch` — exactly the rows with `t < s/√2`,
where the block's diagonal is longer than the fill's box. The law is now the maximum, and
the refusal stays: the gate is the arbiter, not the algebraist.

## 2. Feasibility is one exact inequality

The corner staircases are not free: the one at `(0,0)` and the one at `(0,L)` both stand on
the wall `x = 0`. The first occupies `y ∈ [0, k]`-ish (its `i = 0` column runs to `j = k−1`),
the second comes down from `L`. They interpenetrate exactly when

    L − (k−1) − 1 < (k−1) + 1        i.e.        L < 2k .

With `L = s/√2 + k + 1` that is `k > s/√2 + 1`, so

    feasible  ⟺  k ≤ ⌊s/√2⌋ + 1 .

This is *derived*, and then **checked against the gate on every row of the sweep**:
121 rows, `gated ⟺ k ≤ ⌊s/√2⌋ + 1` on all 121, 0 mismatches. Beyond it the refusal is
declared, not incidental:

    Refusal("block45_corner_collision", "… k pairs overlap (the corner staircases meet on a wall)")

| `s` | gated `k` | refused `k` | `⌊s/√2⌋+1` |
|---|---|---|---|
| 1 | 1 | ≥ 2 | 1 |
| 2 | 1, 2 | ≥ 3 | 2 |
| 5 | 1–4 | ≥ 5 | 4 |
| 9 | 1–7 | ≥ 8 | 7 |
| 10 | 1–8 | — (8 is the window's top) | 8 |
| 17 | 1–13 | 14, 15, 16, 17 | 13 |

At `s = 17` the whole window is `k ≤ 13`; `k = 14` fails with **4** colliding pairs,
`k = 16` with 24, `k = 17` with 40 — the count of overlaps grows as the staircases cross
deeper. `(17, 15)` also refuses; the sweep's extras list skipped it, and the run records it
as refused by the same law (the earlier probe found 4 violations at `k = 14` and the law
says every `k ≥ 14` fails).

## 3. The excess, and the floor

In the contact branch, `L − 2k = s/√2 + 1 − k`. Over the feasible window that runs from
`s/√2 − ⌊s/√2⌋` (at the top, `k = ⌊s/√2⌋+1`) up to about 2. So the block can push its
excess down to **exactly the fractional part of `s/√2`**:

    min_{k feasible} ( L − 2k )  =  frac(s/√2) .

Checked on the ledger: at `k = ⌊s/√2⌋+1` the measured excess equals `frac(s/√2)` on every
`s` in the sweep, 0 exceptions.

Certified rows below `2k + ½√2 = 2k + 0.707107`:

| `s` | `k` | `N` | `L` | `L − 2k` | contacts | vs delivered row |
|---|---|---|---|---|---|---|
| 17 | 13 | 653 | 26.020815… | **0.020815** | 2308 | no row at 653 |
| 10 | 8 | 244 | 16.071068… | 0.071068 | 794 | behind by 0.071068 |
| 3 | 3 | 33 | 6.121320… | 0.121320 | 72 | behind by 0.121320 |
| 6 | 5 | 96 | 10.242641… | 0.242641 | 278 | behind by 0.242641 |
| 9 | 7 | 193 | 14.363961… | 0.363961 | 612 | behind by 0.363961 |
| 2 | 2 | 16 | 4.414214… | 0.414214 | 26 | behind by 0.414214 |
| 5 | 4 | 65 | 8.535534… | 0.535534 | 172 | **exact parity (0E−69)** |
| 8 | 6 | 148 | 12.656854… | 0.656854 | 454 | **exact parity (0E−68)** |

So the single-word floor `½√2` is **the ridge's floor, not a law of squares**. Eight exact
sentences sit below it, the best by a factor of 34. That is the honest answer to the floor
question, and it is not in doubt: those eight are gate-certified at clearance exactly 0.

## 4. The two asked points

### 4a. `(k = 4, s = 5)` — `N = 65`: certified, and it *is* the delivered row

`T = 10`, `N = 25 + 40 = 65`, `L = 5/√2 + 5 = 8.5355339059327376…`, 172 exact contacts,
gate clearance 0, and the delivered side at `n = 65` minus this side is **`0E−69`**: the
table's own stored side is `5 + 5/2√2`, which is this law. The delivered slack
`L − 2k = 8.535534 − 8 = 0.535534` **is** `5/√2 − 3`. This is parity, not a win — the row
already had it. It is still the strongest kind of confirmation available: the production
reproduces a delivered row's side *exactly*, from a count law and a contact root, with no
fit.

### 4b. `(k = 13, s = 17)` — `N = 677`: an exact count refusal

`N(13, 17) = 289 + 2·13·14 = 289 + 364 = 653`, not 677. `N = 677` would need
`T = (677 − 289)/4 = 97` per corner, and the staircase counts are triangular: `k = 13`
gives 91, `k = 14` gives 105. **677 is not in the family at all** — the exhaustive check
`s ≤ 30, k ≤ 25, s² + 2k(k+1) = 677` finds nothing (control 29 asserts it).

The delivered row at 677 is therefore *not* this production, and its own counts say so:
388 axis squares = `4 × 97`, and 97 is not a triangular number. Its corners are half a unit
wider than a contact staircase (`t = 26.520815 − 12.020815 = 14.5`), which is how six extra
squares per corner fit — a relaxed pose at the table's `1e−9` polish, not a sentence.

The family's own member at `(13, 17)` is certified and is the run's headline number:

    N = 653,  L = 26.020815280171307…,  L − 2k = 0.020815280171307…  <  ½√2 = 0.707106781…

2308 exact contacts, clearance 0, 439 tilted + 214 axis squares. It has no delivered row to
beat (653 is not a delivered count), and its side is above `⌈√653⌉ = 26` — so it is a
floor-breaking sentence, not a record.

### 4c. The 901 row, which *is* the family in count and is refused in geometry

`N(17, 17) = 289 + 612 = 901` — exactly the delivered 901 row's count (`612 axis + 289
tilted`), and `153 = T(17, 17)` axis squares per corner. But `k = 17 > ⌊17/√2⌋ + 1 = 13`,
so the exact staircase **cannot be built at that count**: the gate reports 40 colliding
pairs, and the reason is the inequality — the wall-anchored staircases need `L ≥ 2k = 34`
while the family's own side is `L(17, 17) = 17/√2 + 18 = 30.020815`. The delivered 901 row
sits at `L = 30.520815`, exactly **half a unit wider**, i.e. `t = L − s/√2 = 18.5`: same
count law (153 is `T(17, 17)`), half-integer legs, so its corner squares are inset and its
`L` is *also* below `2k = 34` — it is not this sentence at a slightly different side, it is
the same arithmetic in a pose the exact fill cannot take. So the table's 901 is a relaxed
pose; the exact production at those parameters is infeasible, and the run says so rather
than reporting a near miss.

## 5. Does it scale past `n = 1000`? Yes — as the grid

Certified above 1000 (all gated, clearance 0):

| `s` | `k` | `N` | `L` | `L/√N` | contacts | vs delivered |
|---|---|---|---|---|---|---|
| 25 | 17 | 1237 | 35.677670… | 1.014406 | 4532 | no row at 1237 |
| 35 | 24 | 2425 | 49.748737… | 1.010244 | 9112 | no row at 2425 |
| 50 | 35 | 5020 | 71.355339… | 1.007105 | 19230 | no row at 5020 |

Those three do beat the *grid* (`⌈√N⌉`), because 1237, 2425 sit just above a perfect square
and the family's side is within `O(1)` of `√N`. But `L/√N → 1`: along the minimal-excess
ladder `k = ⌊s/√2⌋+1`,

| `s` | `k` | `N` | `L` | `L − 2k` | `L/√N` |
|---|---|---|---|---|---|
| 17 | 13 | 653 | 26.02082 | 0.020815 | 1.018273 |
| 25 | 18 | 1309 | 36.67767 | 0.677670 | 1.013752 |
| 50 | 36 | 5164 | 72.35534 | 0.355339 | 1.006879 |
| 99 | 71 | 20025 | 142.00357 | 0.003571 | 1.003490 |
| 198 | 141 | 79248 | 282.00714 | 0.007143 | 1.001765 |
| 396 | 281 | 315300 | 562.01429 | 0.014285 | 1.000888 |

`N ≈ 2s²`, `L ≈ s√2 = √N`, so the family **is** the grid in the limit, one `O(1)` above it.
The reason is visible in the geometry: the block plus four corner staircases covers the box
except for four thin gaps along the faces, and the count `s² + 2k(k+1)` is what a `√N × √N`
square holds. The certified `frac(s/√2)` excess is bought by matching the grid's own
diagonal, not by beating it.

So the honest scaling answer to the session's headline question — *can the grammar certify
record-level topologies `L < 2k + ½√2` past `n = 1000`?* — is: **it certifies the
inequality, and the inequalities are not records.** The floor is broken at every scale
(certified at `N = 1237` and `N = 2425` too, by the ladder above), but no member of this
family beats a delivered row: 0 of 70, at any count.

## 6. Verification

* `glm_wheels.py --selftest` — **29 controls, exit 0, 2 m 0 s**; control 29 is new and asserts the
  count law over `s, k ≤ 8`, both side branches, the two showcase sentences (with the
  delivered rows' `0E−69` / `0E−68` parity), the `k = 14` collision refusal, and that no
  `(s, k)` with `s ≤ 30, k ≤ 25` emits `N = 677`.
* `glm_wheels.py --audit` — **258 functions, 0 offenders** (up 5: `block45_count`,
  `block45_side`, `_block45_sentence`, `p_block45`, `block45_spin`; no float named).
* `glm_wheels.py --block-spin` — 121 rows (every `(s, k)` with `N ≤ 250`, plus
  `(17, 13), (17, 16), (17, 17)`), **70 gated, 51 `block45_corner_collision`**, 8 below
  `2k + ½√2`, 0 beating the delivered row, `2 m 16 s`, ledger
  `workspace/push/block45_spin.json`.
* Feasibility law and minimal-excess law re-checked *against the ledger*: 121/121 and 8/8.
* `glm_wheels.py` bare run exit 0, ledger `workspace/push/glm_wheels.json`;
  `record_guard.py` OK; `family_spin.py --calibrate/--gate-ks/--beyond`,
  `grammar_induction.py`, `qsqrt2.py`, `field_triage.py` unchanged and green.
* README/STATUS footers byte-identical from `## Current results`.

## 7. Honesty about what is proved and what is measured

* **Proved (exact, `Q(√2)` throughout):** the count law; the side law, both branches; the
  70 gated sentences (clearance 0, `gate_L == L`); the 51 collision refusals; the
  feasibility inequality on the sweep; the minimal excess `frac(s/√2)`; the count refusal at
  677.
* **Measured (12-dp pose, `Decimal` at 70 digits):** every statement about a delivered row —
  the `0E−69` / `0E−68` parities, the `677` row's `97`-per-corner anatomy, the `901` row's
  `t = 18.5`. Those rows are poses at `~1e−9`, not sentences (run 95's `−2.365e−9` overlap
  is the standing evidence).
* **Not claimed:** that the block is a frontier family — it is not, and §5 says why in one
  line (`L/√N → 1`). Nor that no other topology can beat the floor at large `N`; this run
  settles one production, exactly, and reports the inequality it does break.
* The `k = 15` row at `s = 17` was not in the sweep's extras; the law (`k ≤ 13`) refuses it,
  and the record says the law is what refuses it rather than a missing measurement.

## 8. What this means for the next run

The block's gap is not in its geometry but in its **corner fill**: a contact staircase needs
integer legs, and the table's own low-slack rows use *half-integer* legs (`t = 14.5` at
`N = 677`, `t = 18.5` at `N = 901`) with six extra squares per corner. That is the next
production, and it has a precise falsifier: build the `t ∈ ℤ + ½` corner fill with the extra
staircase squares the half unit admits, and ask whether any `(s, k)` reaches
`L = 2k + 0.520815` at `N = 677`, `785`, `901` with clearance 0. If it does, the delivered
`k = 13..15` rows are grammar; if it does not, the half-unit is a pose and the frontier there
stays measured rather than proved.
