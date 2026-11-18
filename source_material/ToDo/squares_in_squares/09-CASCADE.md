# 09 — The cascade, modelled and derived backwards

**Run 42, 2026-11-17.** Instrument `scripts/cascade_predict.py`; ledger
`workspace/push/cascade_predict.json`. Read-only: it never writes `table.json`
or `submission.csv`.

**The question.** `workspace/docs/05-original-methods.md` calls the
residue-family cascade planner "original" and states its behaviour as an
engineering fact. Can it be written down mathematically, run backwards from a
target row to the base that would serve it, and used predictively — and where
does the remaining Kaggle score actually live?

---

## 1. Two corrections to the project's own record, found while measuring

Both matter for anything built on top of them.

| claim in the record | what the tree says |
| --- | --- |
| "score 22.218056945, 553/1000 beat grid" (STATUS, notes) | **confirmed** — recomputed from `submission.csv`'s 500,500 placements: **22.218056945, 553 beat grid** |
| `table.json` is the delivered state | **it is stale.** It scores **22.645991** with 543 beats, and **357 of 1000 rows disagree** with the CSV. Every script in this tree that treats `table.json` as current under-reports by 0.43, and one that writes back would *regress* the submission |
| "the table stops at n = 1000; no packings above 1000" (PL-16, §12) | **wrong.** `workspace/submission/extended_table_5000.json` has **4,000 rows, n = 1001…5000**, with `L`, `grid` and a `bound`, of which **805 are non-grid** and **33 carry a stored state** (e.g. n = 1028 at L = 32.556349, gated True) |

The 4,000-row table changes the above-1000 picture from §08: the *easy* rows
there are not only lattice (§08) — they are also **cascade closures** of 33
real bases (1028, 1120, 1188, 1237, 1453, …). But **772 of the 805 non-grid
rows above 1000 have no stored state**: their L values are arithmetic, not
verified packings. That is a verification gap, not a result.

---

## 2. The cascade as mathematics

Write `n = k² + r` with `k = ⌊√n⌋`, `0 < r ≤ 2k`, so the grid value is
`⌈√n⌉ = k + 1`. Define the **slack** of a row:

```
delta(n) = L(n) − k          (delta < 1  <=>  the row beats grid)
```

**Step.** At container `k + delta`, the free band of unit cells around a full
`k × k` block is `2k + 1` cells (k to the right, k above, 1 in the corner), so

```
m_{j+1} = m_j + (2k_j + 1),      k_{j+1} = k_j + 1,      delta unchanged.
```

By induction `m_j = k_j² + r` exactly. Hence:

> **Theorem (ideal cascade).** If some row `k₀² + r` has slack `delta < 1`, then
> for every `k ≥ k₀` the row `k² + r` is packed in container **`k + delta`**,
> i.e. it beats grid by exactly `1 − delta`.

**The invariant is the pair `(r, delta)`.** Not `r` alone, and not `L = k`:
`k² + r` squares cannot fit in a `k × k` box for `r ≥ 1` (area bound), so a
"container k" version of this theorem is false. The first draft of this script
claimed exactly that; the witness chain in docs/05 refuted it and the model was
corrected. The documented chain is the proof by example:

```
5 @ 2.8  ->  10 @ 3.8  ->  17 @ 4.8  ->  26 @ 5.8  ->  37 @ 6.8  ...
 2²+1        3²+1         4²+1          5²+1         6²+1
 r = 1, delta = 0.8 throughout; grid 3, 4, 5, 6, 7; gain 1 − 0.8 = 0.2 each
```

and the delivered table has the same structure at every residue, with its own
slacks: `r = 1 → delta = 0.520815` (L(962) = 31.520815), `r = 2 → 0.535534`,
`r = 5 → 0.606602`, `r = 9 → 0.656854`.

## 3. Derived backwards

For a target `n`: `k = ⌊√n⌋`, `r = n − k²`. Sweeping rows in ascending `k` and
carrying the minimum slack seen so far gives

```
L(n)  <=  k + running_min_{k₀ ≤ k} delta(k₀² + r).
```

So **the row to solve is not n** — it is the smallest base in n's residue
class, and one base serves that whole class for every larger band. That is the
predictive content: 1000 targets collapse to **60 residuals**, each with one
slack parameter.

## 4. What the measurement says

Against the authoritative CSV table:

| | |
| --- | ---: |
| rows covered by the model (residue has a base at k₀ ≤ k) | **931** of 969 |
| table at least as good as the prediction | 491 |
| table *worse* than the prediction | 25 — total gain **2e-9** (rounding) |
| table **better** than the prediction | **415** — worth **0.481427** |
| residues with a usable base | **37** of 60 |

Two firm conclusions:

1. **The cascade is saturated.** Wherever a base exists, the table already
   achieves the chain value to machine precision — the 25 exceptions are
   float noise. There is no score left in *applying* the cascade. It has been
   applied.
2. **Construction beats the chain by 0.481 scoring units** across 415 rows.
   The constant-δ chain is a weak bound; the Göbel/strip families are what
   actually deliver the beating rows. So the cascade is a *floor generator*,
   not the engine.

## 5. Where the remaining score actually lives

Decomposition of 22.218056945:

| bucket | rows | score |
| --- | ---: | ---: |
| beats grid | 553 | 15.022691 |
| at grid | 447 | **7.195366** |

All of the upside is in the 447 grid rows, and they are not uniform: they are
concentrated in the **23 residues with no base at all** (r = 38 … 60). For a
residue `r`, let `W(r) = Σ_{n = k²+r, n ≤ 1000} 1/√n` be its column weight.
Then:

* **opening a base with slack δ** banks `(1 − δ) · W(r)` across the column;
* **reducing an existing base's slack by Δ** banks `Δ · W(r)`.

| r | rows | W(r) | base today | banks at δ=0.5 | banks at δ=0.8 |
| ---: | ---: | ---: | --- | ---: | ---: |
| 38 | 13 | 0.515 | **none** | 0.257462 | 0.102985 |
| 39 | 12 | 0.464 | **none** | 0.232247 | 0.092899 |
| 40 | 11 | 0.433 | **none** | 0.216261 | 0.086505 |
| 41 | 10 | 0.385 | **none** | 0.192277 | 0.076911 |
| 42 | 10 | 0.384 | **none** | 0.192131 | 0.076852 |
| 43 | 9 | 0.339 | **none** | 0.169257 | 0.067703 |
| 44 | 9 | 0.338 | **none** | 0.169134 | 0.067654 |
| 45 | 8 | 0.295 | **none** | 0.147272 | 0.058909 |
| 46 | 8 | 0.294 | **none** | 0.147171 | 0.058868 |
| 47 | 7 | 0.252 | **none** | 0.126236 | 0.050494 |
| 48 | 7 | 0.252 | **none** | 0.126152 | — |
| 49 | 6 | 0.212 | **none** | 0.106069 | — |

For scale: the whole run-35 source import gained **0.003604**. *One* mediocre
base at δ = 0.8 in residue 38 is worth **0.103** — twenty-eight times that
import. That is the correct place to spend effort, and it is a different place
from where the last six runs have been spent (local search on the objective).

And the same residues are the ones §08 called the open region above 1000:
`r > k` is precisely the **upper half of each band**, where `L = k+1` stops
being plausible. The score inside 1000 and the unconstructible rows outside it
are the *same* population.

## 6. The other cascade in the repository, and what does not transfer

`src/lean/RequestProject/GLM/Cascade.lean` is a different animal: a MASH 1-1
delta-sigma cascade, with exact theorems — the cascade's instantaneous error is
a second difference of a bounded sequence (`casOut_error`), so the doubly
accumulated error is bounded (`casDouble_sum`) and the triangular-window
average is within `2/(M(M−1))`, `O(1/M²)`, against `1/(2M)` for one loop
(`firstOrder_triangular_error_ge`). It is a genuine "two wobbles buy an order"
statement, proved with no probabilistic model.

Read against this project it suggests one thing and *only* one: our per-n score
is a first difference along `n`, so a windowed reading of the score over n is
the natural analogue — but nothing in that file says anything about packings,
and no measurement here supports importing it. It is a template for how to
*state* a gain exactly, which is what §2 above tries to do, and that is all I
will claim for it.

## 7. The plan this analysis supports

Ranked by measured score per unit of work. PL-21 first.

| id | move | expected |
| --- | --- | --- |
| **PL-21** | For each of the 23 base-less residues (r = 38…60), target the **first row of the column** — n = k₀² + r with the smallest k₀ ≥ ⌈r/2⌉ — and search for *any* packing with slack < 1. One base opens the whole column | 0.10–0.26 per residue at δ = 0.8; ~2.0 across the top 12 |
| **PL-22** | For the 37 covered residues, reduce the base slack by Δ; each 0.01 buys `0.01 · W(r)` | 0.005 per 0.01 on r = 1 |
| **PL-23** | Make the CSV the single source of truth (or regenerate `table.json` from it). 357 rows currently disagree | prevents a 0.43 regression |
| **PL-24** | Verify or discard the **772** non-grid rows above 1000 that have L but no state | integrity, not score |

## 8. Reproduction

```bash
python3 scripts/cascade_predict.py --table <L-table.json> --json
# L-table: {"n": {"L": value}}; the authoritative L comes from submission.csv
```
