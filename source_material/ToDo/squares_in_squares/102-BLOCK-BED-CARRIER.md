# 102 — The block-bedded carrier: a seamed grid whose runs are disjoint by law reproduces 19 of the 110 two-class rows, one short of the entry gate (Run 145; corrected in Run 146)

**Run 145, 2026-11-26.** Instrument `scripts/block_bed.py` (new), ledger
`workspace/push/block_bed.json`. Doc 101 §6 closed run 144 with one instruction: the next carrier
must be sparse **by construction** — "translates that are disjoint by a law, not by a drop rule" —
because run 144's notched *product* could share area with the bar but not with itself, and 28 of its
30 count-matched rows were refused by the exact gate for exactly that reason. This run builds that
carrier, gives it its own spec, gate, controls and entry test, and runs the entry test **first**.

**Answer: the carrier is built and the law holds, but the entry test FAILS at 19 of 110**
(threshold 20) — by one row. Run 145 first reported 48/110 PASS; that number came from a counting
defect (§8) and is retracted here. The true result: **82** of the 110 sides are of the form
`a + (s/2)√2`; of those, **19** rows have their count reached by a declaration the exact gate
certifies at 0 violations, and **63** have no declaration at their count. Every one of the 19 is a
**symmetric** declaration (`kx = ky = K/2`): the family reproduces the table exactly where the
delivered pose is x–y symmetric, and nowhere else. The shortfall is arithmetic, not geometry: **28**
rows are not of the form `a + (s/2)√2` at all, and **63** are in the side group but no declaration of
the family reaches their count. **No sweep is authorised by this gate.**

**The split is not what decides it — the count is, and the count lives on the symmetric
declaration.** Freeing `kx` and `ky` was supposed to be the decisive degree of freedom; with the
corrected counter every one of the 19 hits has `kx = ky = K/2`, and an asymmetric split never even
reaches the delivered count at the delivered side. The spec keeps the free split (nothing forbids
it, and it costs one pass), but it is not doing any work yet, and the run-145 claim that 45 of the 48
needed it was an artefact of §8's defect.

**Nothing promoted.** `submission.csv` and root `WHITEBOARD.md` are untouched; the delivered total
stands at **22.217428576** / 554 beats / 446 ties. No sweep was run: the entry gate now permits one,
and §6 prices it.

## 1. What was asked

1. build the next carrier from doc 101 §6: sparse **by construction** — disjoint translates by a
   law, not a drop rule — with **its own spec, exact gate, controls**;
2. run the **20-of-110 entry test first**, and only sweep if it passes;
3. record the outcome exactly, the refusal included.

## 2. The carrier (spec)

**Declaration.** Seven integers `(a, s, K, kx, ky, p, q)`:

| symbol | meaning | bound |
|---|---|---|
| `a`, `s` | the side `L = a + (s/2)√2` | `a ≥ 1`, `1 ≤ s ≤ 30` |
| `K` | grid positions per axis | `2 ≤ K ≤ 34`, and `K < L` |
| `kx`, `ky` | the two run lengths **on each axis** | `1 ≤ kx, ky ≤ K−1`, run 2 has `K − k` |
| `p`, `q` | the tilted block, `p` cells along one tilted axis and `q` along the other | `p·q ≤ 330` |

**The law.** Each axis carries two runs separated by a **positive gap**:

- run 1 on an axis: centres `1/2, 3/2, …, k − 1/2`, i.e. the span `[0, k]`;
- run 2 on the same axis: centres `L − (K−k) + 1/2, …, L − 1/2`, i.e. the span `[L−(K−k), L]`;
- the gap `g = L − K > 0` is the seam, and it is the *only* thing between the runs.

The carrier is `X × Y`, where `X` uses `kx` and `Y` uses `ky` — **the two axes' splits are
independent**, because nothing in the problem makes a pose symmetric in x and y and the delivered
poses are not. Every two carrier cells are then separated by at least `g` on one axis (different
runs) or by exactly `0` (adjacent in one run, an exact contact), for **any** `g > 0` and **any**
split. Carrier–carrier overlap is therefore impossible by arithmetic: there is no interlock
parameter, no pair to test, and nothing for a notch to repair. That is the whole difference from run
144, where run 2 was *slid into* run 1 by an interlock `o` and the gate had to refuse.

The gap may be any positive number, which is exactly what lets the box take the delivered irrational
sides `a + (s/2)√2` while every cell stays on the integers.

**The block.** The tilted class is a **p×q block** — the closed rectangle R of side `p` and `q` whose
edge normals are `±(√2/2, ±√2/2)`, centred at `(L/2, L/2)`. Its cells are the product of `p` and `q`
translates by `(√2/2, √2/2)` and `(√2/2, −√2/2)`, so R is *exactly* their union and its
half-extents are `p/2` and `q/2` in the block's own frame. Run 144's `m`-cell bar is the `p = 1`
case; the delivered classes are blocks far more often than bars (`5×5`, `8×8`, `15×15`, `18×18`, and
1-wide bars at `(2,25)`, `(3,13)`, `(5,19)` … — but the 19 reproductions of §4 use only
square blocks `p = q` of size 1, 4, 5, 7, 8, 11, 15 and 18, which is what an x–y symmetric
centred pose forces).

**The bed (the only insertion rule).** A carrier cell is **dropped iff its interior meets R's
interior** — the block cuts its own bed out of the grid, and nothing else is removed and nothing is
moved. Because R *is* the union of the block's cells, this is the same predicate the gate applies
pair by pair, decided in one shot by four exact SAT inequalities against R; control 7 checks the two
agree cell by cell on every cell of four declarations.

**Side law.** Written in closed form and *generated*: `L = a + (s/2)√2`. The carrier spans exactly
`[0, L]²` (run 1 from 0, run 2 to L), so the box is the carrier's own bbox and the pose must fill it
(`L_pose == L` is part of the verdict).

**Count law.** `n = K² − dropped + p·q`, read off the assembled pose, never assumed. The counter
that finds `dropped` is the column-by-column one (§3), not a second rule.

**Sparseness.** Two translation domains per axis, four in the plane (control 5, axis 4 / tilt 1),
and fill `n/L²` **0.68 / 0.74 / 0.86 / 0.89 / 0.91** on the five declarations measured, with the
*carrier's* own fill `0.40–0.55` — the bed is a large hole, not a thin strip.

## 3. The exact gate and the controls

Every verdict is `qsqrt2.gate` on `Q(√2)` cells with no tolerance: `ok` iff every pair is separated
on some axis by an exact SAT slack `≥ 0`, plus exact containment and the span. No float names any
decision: the module's **22 decision functions** are bytecode-audited to **0 naming float** (control
8; `selftest` is the only exempt function).

`python3 scripts/block_bed.py --selftest` — **10 controls, exit 0**:

1. the law, for five declarations including two with `kx ≠ ky`: `g > 0` on both axes, the
   run-to-run centre gap is exactly `1 + g`, adjacent cells within a run are exactly `1` apart, and
   the carrier alone gates **ok with 0 violations** (64 cells / 168 contacts, 100 / 288, …);
2. the bed is load-bearing: keeping the dropped cells makes the gate refuse on every declaration
   tried (24 cells dropped at `(5,5,8,4,4,5×5)`, 40 at `(6,8,10,5,5,8×8)`, 35 at `(5,5,8,1,7,5×5)`);
3. the atom: `(2,1,2,1,1,1,1)` gives `n = 5` at `2 + ½√2`, 0 overlaps, 4 exact contacts;
4. the side is the contact side: the same pose at `L − 1e-9` is refused;
5. sparseness: fill **0.6823 / 0.8579 / 0.8922 / 0.9126 / 0.7412** (all < 1), carrier fill
   **0.5458 / 0.5147 / 0.5490 / 0.4416 / 0.3980**, domains **axis 4 / tilt 1**;
6. containment, the span, and the family's own refusal of a block too large for its box
   (`(2,1,2,1,1,4×4)`: `contained = False`, `span = False`);
7. the bed rule *is* the gate's pairwise predicate — on all `K²` cells of four declarations the cell
   is dropped iff some block cell refuses it, and the count agrees with `assemble`;
8. the bytecode audit: **22** decision functions, **0** naming float;
9. one counter, one gate: the analytic column counter equals `assemble`'s drops on six
   declarations, and `check`'s verdict equals the raw gate's;
10. the family rebuilds the delivered **pose**, not merely its numbers: at `n = 5`, `65`, `124` the
    built pose equals the CSV's pose up to translation and the square's eight symmetries.

## 4. The entry test

`python3 scripts/block_bed.py` — all 110 delivered two-class rows, every declaration with
`K` from `⌈√(n − p·q)⌉` to `⌊L⌋` (the count law forces `K² ≥ n − p·q`, an exact integer prune), both
splits `1 ≤ kx, ky ≤ K−1`, and every block shape `p·q = m`, where `m` is the row's delivered
tilted-class size — the *hint* bounds which declarations are tried and never decides legality. A row
counts only when a declaration builds **exactly that count**, **exactly that side** `a + (s/2)√2`
(recovered from the delivered decimal and verified exactly), and clears the exact gate, containment
and the span.

**Result: 19 / 110 reproduced, threshold 20 — FAIL, by one row. No sweep is authorised.** The
whole sweep takes about **5 m 40 s** (the corrected counter admits far more declarations to the gate,
so it is slower than run 145's 2 m 40 s).

The 110 sort into three disjoint classes, and the middle class of run 144 is **empty**:

| class | rows | what happens |
|---|---|---|
| side + count both hit, **gate passes** | **19** | `n = 5, 40, 65, 89, 101, 124, 145, 148, 197, 200, 233, 257, 265, 401, 485, 489, 581, 636, 688` — every one at `kx = ky = K/2` |
| side + count both hit, gate **refuses** | **0** | — the run-144 obstruction does not occur |
| in the side group, **no declaration reaches the count** | 63 | the family's arithmetic cannot place that many cells at that side |
| **not** of the form `a + (s/2)√2` | 28 | `n = 11, 18, 19, 26, 28, 50, 51, 54, 70, 85, 123, 126, 178, 230, 234, 295, 367, 368, 407, 448, 491, 626, 677, 730, 785, 842, 901, 962` |

(The 28 are the same rows run 144 found — its 82/110 side group is this family's side group too.)

**The split is free and unused.** With `kx` and `ky` independent the search visits every split,
and all **19** count matches sit at `kx = ky = K/2`; no asymmetric split reaches a delivered count at
the delivered side. So the free split is part of the spec without being load-bearing, and the
family's reproductions are the centred symmetric grid-plus-block poses — which is what the delivered
poses are (control 10 shows the built pose *is* the delivered pose at `n = 5, 65, 124`).

**What "reproduced" means here.** The entry test asks for the delivered `(n, side)` pair, and each
hit is a legal pose with exactly that count and that side — which is the same score as the delivered
row. It is a **tie, not a beat**, and nothing is promoted. The *arrangement* is a separate question:
control 10 shows the symmetric declaration is the delivered pose at `n = 5, 65, 124`, and the search
returns whichever declaration it meets first, which need not be the recorded one.

## 5. Diagnosis

**Why 19 and not 110.** Two independent limits, both measured:

- **28 rows are outside the side group.** The family writes its side as `a + (s/2)√2`; 28 delivered
  sides are not of that form for any `1 ≤ s ≤ 30`, and no declaration can reach them. This is a
  property of the parameterisation, unchanged from run 144.
- **63 rows are inside the side group and unreachable in count.** The carrier has four translates
  (two runs on each axis) and a centred block, so its count is `K*K - dropped + p*q`, with the grid
  size `K` pinned to `sqrt n` and the block's waste `p*q - dropped` a small number. The delivered
  axis classes are unions of 4–54 translates (doc 100 §7), and the delivered counts are almost all
  **not** of the form "a centred grid plus a small block correction": 63 of the 82 in-group rows have
  no declaration at their count at all, and the 19 that do are exactly the symmetric ones.

**What is not a limit any more.** Geometry. Across the 19 reproductions and the whole entry search
the gate refused **0** declarations: the positive-gap carrier is legal for every declaration that
fits its box, which is the statement run 144 could not make. The limit is the *count*, and counts are
decided by the block's waste, not by the gate.

## 6. What this changes

- **The entry gate is NOT passed, so this family is not authorised for a sweep** (doc 99 §9): 19 is
  one short of 20. The question a sweep would have asked is still the right one — "can it reach a
  row's count at a side below the delivered one" — and run 146 answers it directly with
  `beat_probe.py` (doc 103) instead of by sweeping: fix `n`, search `(a, s, K, kx, ky, p, q)` with
  `L = a + (s/2)√2` strictly below the delivered side, and gate. The area bound `L*L >= n` collapses
  the side axis to the window `[√n, L_del)`, which is what makes the probe a visit rather than a
  sweep.
- **The value surface is now local.** For every reproduced row the family holds a legal pose at the
  delivered side; moving the same shape to `a' + (s'/2)√2` one step lower is the natural beat
  candidate, and it is a single-parameter probe of the family's own member, not a search over poses.
- **Refused: nothing this run** (the gate systematically refuses every declaration that does not fit
  its box — control 6). **Promoted: nothing.** `submission.csv` and root `WHITEBOARD.md` untouched.

## 7. Checks

Run this visit, each exit 0 unless marked: `block_bed --selftest` **10 controls**; `block_bed` entry
test **19/110** (FAIL, threshold 20) and ledger written, ~5 m 40 s; `beat_probe --selftest`
**3 controls**; `beat_probe` (doc 103); `shared_box --selftest` 9;
`seam_carrier --selftest` 9; `tilt_audit --selftest` 8; `true_geom` 3 controls; `structure
--control`; `structure --check-solver`; `interleaved_boundary`; `twin_boundary`; `notch136`;
`glm_plan`; `pure_slide`; `beaten_leverage`; `band5`; `range_leverage`; `construct_seam`;
`anchor_chain`; `row_census`; `motif_wheels`; `crystal_domains`; `import_n090`; `pub_bounds_check`;
`witt_octad`; `leech_audit_fix`; `verify_certificates` **7 verified, 0 failed**; `sqscore`
**22.217428576** (554/446); `record_guard` OK; `glm_wheels --audit` **684 functions, 0 offenders**;
`py_compile` on `block_bed` and `qsqrt2` OK.

**Not re-run this visit** (long sweeps whose code and inputs this run did not touch): `ext_census`,
`p_screen`, `legal_slide`, `perturb`, `void_insert` — each exceeded a 30-90 s cap and none reads
`block_bed`. The rewritten `workspace/push/*.json` ledgers of the guards that do write one were
reverted; the only ledger this run adds is `workspace/push/block_bed.json`.

no row changed |

## 8. Correction (run 146): the 48 was a counting defect

Run 146 asked the beat question and found this instead. `split_counts` — the table that gives the
bed's `D` for every y split from one x pass — had two defects, and either one alone makes it answer a
different question:

1. **It did not shift its windows.** `dy_window` returns its interval in *offsets* from the box
   centre and `count_windows` shifts by `L/2` before comparing; `split_counts` compared the offset
   window directly against the *absolute* y positions `0.5 + i` and `L − K + 0.5 + j`.
2. **It took the wrong end of the second run.** For a split `ky` the runs are anchored at `0` and at
   `L`, so run 1 is the *first* `ky` positions and run 2 is the **last** `K − ky`; the code used
   `cb[:K-ky]`, the first `K − ky`.

The entry test used that table only as a filter (`if K*K - Ds[ky] + p*q != n: continue`) and then
called `check`, which rebuilds the pose and gates it — but **it never compared `check`'s count with
`n`**. So a declaration the wrong filter admitted was gated, passed (the gate decides disjointness,
not the count) and was counted as a reproduction: all **48** of run 145's "reproductions" have
`family_n != n`, and the ledger records that field. The corrected run writes **19**, and every one of
the 19 has `family_n == n`.

**The fixes, all three of them.**

- `split_counts` shifts by `L/2` and takes `cb[ky:]`, and its docstring states both;
- the entry test accepts a hit only when `r["ok"] and r["n"] == n`;
- **control 9** no longer checks one split: it compares the split table with `bed_count` (and so with
  `assemble`) on *every* split of four declarations. That control fails on the old code and passes
  now, which is the difference between a guard and a habit.

**What survives.** The carrier, the gap law, the bed rule, the exact gate, containment and the span:
the 19 reproductions are poses the exact gate certifies, and control 10 still shows the built pose
*is* the delivered pose at `n = 5, 65, 124`. **What does not survive** is the headline (19, not 48),
the "45 asymmetric hits" (there are none: every hit is symmetric), and the claim that the entry gate
is passed. What run 145 got right about the *shape* of the result: the family's reproductions are the
symmetric centred poses on a `K = 2k` grid with a `k × k`-scale square block, i.e. the family
reproduces the table exactly where the table is symmetric, and its free split was never the point.

no row changed |
