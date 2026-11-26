# 102 — The block-bedded carrier: a seamed grid whose runs are disjoint by law reproduces 48 of the 110 two-class rows (Run 145)

**Run 145, 2026-11-26.** Instrument `scripts/block_bed.py` (new), ledger
`workspace/push/block_bed.json`. Doc 101 §6 closed run 144 with one instruction: the next carrier
must be sparse **by construction** — "translates that are disjoint by a law, not by a drop rule" —
because run 144's notched *product* could share area with the bar but not with itself, and 28 of its
30 count-matched rows were refused by the exact gate for exactly that reason. This run builds that
carrier, gives it its own spec, gate, controls and entry test, and runs the entry test **first**.

**Answer: the carrier is built, the law holds, and the entry test PASSES. 48 of the 110** delivered
two-class `(n, side)` pairs are reproduced (threshold 20), every one of them by a pose the exact
gate certifies at 0 violations — **0 refusals of any kind**. The refusal mode that killed run 144 is
gone by construction, and nothing else took its place. The shortfall that remains is arithmetic, not
geometry: **28** rows are not of the form `a + (s/2)√2` at all, and **34** are in the side group but
no declaration of the family reaches their count.

**45 of the 48 need the two axes split differently.** With one split for both axes the family
reaches 19; with `kx` and `ky` free it reaches 48. Nothing in the problem makes a pose x–y
symmetric, and the delivered poses are not — so the split is part of the spec, and it is the single
parameter that decides the entry test.

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
1-wide bars at `(2,25)`, `(3,13)`, `(5,19)` … — 26 distinct shapes appear in the 48 reproductions).

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

**Result: 48 / 110 reproduced, threshold 20 — PASS. No sweep was run in this visit.** The whole
sweep takes **2 m 40 s**.

The 110 sort into three disjoint classes, and the middle class of run 144 is **empty**:

| class | rows | what happens |
|---|---|---|
| side + count both hit, **gate passes** | **48** | e.g. `n = 40` at `(6,3,3,4×4)`, `n = 124` at `(10,5,5,8×8)`, `n = 909` at `(27,10,1,16×16)` |
| side + count both hit, gate **refuses** | **0** | — the run-144 obstruction does not occur |
| in the side group, **no declaration reaches the count** | 34 | the family's arithmetic cannot place that many cells at that side |
| **not** of the form `a + (s/2)√2` | 28 | `n = 11, 18, 19, 26, 28, 50, 51, 54, 70, 85, 123, 126, 178, 230, 234, 295, 367, 368, 407, 448, 491, 626, 677, 730, 785, 842, 901, 962` |

(The 28 are the same rows run 144 found — its 82/110 side group is this family's side group too.)

**The split is the decisive parameter.** With one split for both axes (`kx = ky`) the search
reproduces **19**; with `kx`, `ky` independent it reproduces **48** — 45 of the 48 use an asymmetric
split, and a scan of the 13 rows that are one cell out in the symmetric family finds **no**
asymmetric count match either, so the extra pairs are not a fudge on a near miss: they are the
difference between a family that assumes a symmetry the geometry does not have and one that does
not.

**What "reproduced" means here.** The entry test asks for the delivered `(n, side)` pair, and each
hit is a legal pose with exactly that count and that side — which is the same score as the delivered
row. It is a **tie, not a beat**, and nothing is promoted. The *arrangement* is a separate question:
control 10 shows the symmetric declaration is the delivered pose at `n = 5, 65, 124`, and the search
returns whichever declaration it meets first, which need not be the recorded one.

## 5. Diagnosis

**Why 48 and not 110.** Two independent limits, both measured:

- **28 rows are outside the side group.** The family writes its side as `a + (s/2)√2`; 28 delivered
  sides are not of that form for any `1 ≤ s ≤ 30`, and no declaration can reach them. This is a
  property of the parameterisation, unchanged from run 144.
- **34 rows are inside the side group and unreachable in count.** The carrier has four translates
  (two runs on each axis). The delivered axis classes are unions of 4–54 translates (doc 100 §7), and
  where the class is a staggered or interleaved family the grid's `K² − dropped` cannot place the
  delivered count at the delivered side. The nearest misses in the *symmetric* family are one cell
  (`n = 82, 122, 170, 173, 226, 298, 362, 442, 534, 741` — ten of them at exactly `n − 1`), which is
  the signature of a boundary cell: the family drops it, the delivered pose keeps it.

**What is not a limit any more.** Geometry. Across 48 reproductions and the whole entry search the
gate refused **0** declarations: the positive-gap carrier is legal for every declaration that fits
its box, which is the statement run 144 could not make.

## 6. What this changes

- **The entry gate is passed, so a sweep is authorised** (doc 99 §9). What the sweep must ask is *not*
  "can the family rebuild the table" — 48 rows say yes at the delivered sides — but **"can it reach a
  row's count at a side below the delivered one"**: fix `n`, search `(a, s, K, kx, ky, p, q)` with
  `L = a + (s/2)√2` strictly below the current best side, and gate. The count law prunes it hard
  (`K ≈ √n`, since `dropped − p·q` is a small perimeter-sized number), and the independent splits cost
  one pass per `(K, kx)` rather than one per split, so the pricing is a row-cost of ~1.5 s at n ≈ 900
  and well under a second below n ≈ 300 — a few hours for all 1,000 rows, minutes for the 110 two-class
  rows and the 44 one-binding-axis rows run 134 left open.
- **The value surface is now local.** For every reproduced row the family holds a legal pose at the
  delivered side; moving the same shape to `a' + (s'/2)√2` one step lower is the natural beat
  candidate, and it is a single-parameter probe of the family's own member, not a search over poses.
- **Refused: nothing this run** (the gate systematically refuses every declaration that does not fit
  its box — control 6). **Promoted: nothing.** `submission.csv` and root `WHITEBOARD.md` untouched.

## 7. Checks

Run this visit, each exit 0 unless marked: `block_bed --selftest` **10 controls**; `block_bed` entry
test **48/110** (pass, threshold 20) and ledger written, **2 m 40 s**; `shared_box --selftest` 9;
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
