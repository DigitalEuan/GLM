# 106 — The block's position, decided instead of sampled (Run 149)

**Headline.** Run 148's third measurement was a *probe*: on seven open tie rows it visited 40 sides ×
7×7 offsets × every `(K, split, shape)` — **421,713 declarations, 0 nominations**. A probe's zero is a
sample: it says the 49 positions tried per declaration missed, not that no position hits. This run
replaces it with a decision, in exact arithmetic, over the **whole** legal domain:

* **plain block** (`p × q`): **every** open non-proved row up to `n = 100` — the sixteen the sweep calls
  `tie reached`, plus `n = 12` — **7,381 declarations, 94,339 boxes, every box list emptied, 0
  survivors** — no side that would beat the delivered one and no block position of any shape that fits
  attains the row's count;
* **notched block** (`p × q` minus an `a × b` corner, `a, b ≤ 2`), through the same engine and on the
  same rows: **6,038 declarations, 69,614 boxes, every box list emptied, 0 survivors** (parameter box
  in §4).

Nothing was promoted: no candidate exists to promote, so C1–C4 was never entered, `submission.csv` and
root `WHITEBOARD.md` are untouched, and the delivered total stands at **22.217428576** (554 beats, 446
grid ties).

Two defects in run 149's own framing were found while widening this run, and both are fixed below: its
interval ended at the **grid** side, which on `n = 40, 65, 89` (delivered side 1.7e-9 *below* the grid
side) contains the family's own tie pose, so those rows could never be emptied as stated — `n = 65`'s
least bed under the grid-side interval is `0`, i.e. the count is attained at 8.5355 by a declaration with
`K < k`; and its fixed `SMAX = 13` cut `p + q = 14` at `k = 10`. The `n = 12` sentence "the least bed is
2" was also a reading of a sample; it is now a certified minimum with an exact witness. The run also **re-ran the run-148 sweep** to build on it and corrected three of its claims —
`counts_max` was filtering the wide map at 130, "unattained everywhere" is false, and §2's two missing
counts are `3` and `99`, not `1` and `2`. That correction lives in doc 105 §0 and is summarised in §8.

---

## 1. The question, and why a sample cannot answer it

The family's count is `n = K² − D + m` with `D` the carrier cells the block beds out and `m` the block's
own cells. For a row `n` and a declaration the count law therefore **fixes the bed**:

```
D* = K² + m − n
```

and the design question is

```
exists (L, cx, cy) with  sqrt(n) < L < k,  h ≤ cx, cy ≤ L − h,  D(L, cx, cy) = D*   ?
```

where `k = ceil(sqrt n)`, `h` is the block's bbox half-extent, and `L ≥ K` is the family's own seam law
(the two runs on an axis must not overlap). `D` is an integer step function of `(L, cx, cy)`, so the
question is whether the level set `{D = D*}` is empty. `D` is **not** monotone in the offset (the corner
of the play square is *not* the minimum: on `n = 12`, `K = 3`, a 2×2 block the corner gives `D = 4` and
an interior point gives `D = 2`), it is **not** an interval (run 148 measured `{8, 10, 12}` on a
symmetric declaration), and it **steps by up to 4**. Every shortcut that would turn a sample into a
theorem — monotonicity, convexity in the offset, bisection on `D` — is false, which is why run 148 could
only sample.

## 2. The decision

One carrier cell at `(x(L), y(L))` against one block **rectangle** R — a rotated rectangle of
half-extents `pu, qv` in the block's own frame `u = (x+y)/√2`, `v = (y−x)/√2`, centred at `(U0, V0)` in
that frame — is the SAT test of two squares. The pair is separated on one of four axes (`x`, `y`, and
R's two own edge normals), so "the cell's interior meets R's" is the intersection of **four strict
half-spaces**:

```
|(x+y) − (cx+cy) − √2·U0| < 1 + √2·pu
|(y−x) − (cy−cx) − √2·V0| < 1 + √2·qv
|x − cx − (U0−V0)/√2|     < 1/2 + (pu+qv)/√2
|y − cy − (U0+V0)/√2|     < 1/2 + (pu+qv)/√2
```

Each form is **affine in `(L, cx, cy)`**, so each cell's bed-set is an **open convex polyhedron** in the
three parameters. That gives a box `B` two exact numbers:

* **floor(B)** — the cells whose four interval hulls over `B` clear the constants: those cells are
  bedded at *every* point of `B`, because a convex function is bounded on a box by its corners;
* **ceiling(B)** — the cells whose hulls all meet their strip: those are the only ones that can be
  bedded *somewhere* in `B`.

The decision is then a branch and bound:

```
floor > D*   →  no point of B has the row's count   (pruned)
ceiling < D* →  no point of B has the row's count   (pruned)
floor = ceiling → D is exactly that constant on B   (pruned, or a hit if it equals D*)
otherwise    →  split the widest side at its exact midpoint
```

**An empty box list is the theorem.** A non-empty list is never rounded away: a box that survives the
declared budget, or survives to `TOL` without the count at its centre, is reported as `OPEN`, and a box
that survives to `TOL` *with* the count at its centre hands back a pose which the exact gate then judges.

Everything is `a + b√2` with `a, b` rational (`qsqrt2.Q2`), bisection halves exactly, and every
comparison is `Quad.sign()`. No tolerance, no float in a decision path (control 8).

**A defect the control found.** The first draft's domain was the area floor and the block's fit
(`L ≥ max(√n, 2h)`). Planted-configuration control 4 then produced a "hit" at `L = 3.9999…` on a `K = 4`
declaration — a carrier whose two runs *overlap*, i.e. not a pose of this family at all. The domain must
carry the family's seam law `L ≥ K`, and it now does; `assemble` refuses a pose with a negative seam gap
on its own, so a candidate cannot be reported without it.

## 3. The open rows, plain block

**Which rows.** The `n ≤ 100` sweep (doc 105) reports sixteen rows where the family reaches the count
exactly at its delivered side (`tie reached`), and the literature proves none of them optimal; those are
the open rows. `n = 12` is carried in addition — the sweep is 0.414 *above* its delivered 4 there, so it
is not a tie, but its delivered side is exactly the grid side and it was run 148's sharpest case.
`open_rows()` derives the sixteen from the sweep's ledger and asserts the result against the module's
constant, so the scope is audited rather than chosen.

**The interval ends where a beat could live.** A pose beats a row only if its side is below the
delivered side by more than the noise floor, so the search interval is

```
sqrt(n) ≤ L ≤ delivered(n) − 1e-8
```

with `delivered(n)` the submission's own side for the row, read exactly from the CSV. For the fourteen
rows whose delivered side *is* the grid side (and for `n = 12`) this differs from run 149's `L ≤ k` by
1.6e-9. For `n = 40, 65, 89` it differs decisively: their delivered side is 1.7e-9 **below** the grid
side and the family attains the count there with `K < k`, i.e. *inside* `[sqrt n, k]`, so a grid-side
interval holds an attainment by construction and could never be emptied. The minima pass found it at
`n = 65`: under the grid-side interval its least bed is 0 — the count is attained at 8.5355 by a
declaration with `K < k`. That is a hit and not a beat; under the delivered-side end the same
declarations are empty.

**The box is every shape that fits.** The block must sit inside a side below `k`, so `(p+q)/√2 < k`, i.e.
`p + q ≤ isqrt(2k²−1)` — 5, 7, 8, 9, 11, 12, 14 for `k = 4..10`. Run 149's fixed `SMAX = 13` was already
complete for `k ≤ 9` and cut `p + q = 14` at `k = 10`; the per-row bound replaces it. `PMAX = 10` was
never binding (`pq ≤ n` together with `p + q ≤ 14` gives `p ≤ 7`). Then every `K ≤ k−1`, every split up
to the box's reflection, `p ≤ q` up to the block's frame symmetry (control 7), and the count law's own
`m ≥ n − K²`.

| n | k | declarations | boxes | the count law's demands `D*` | verdict |
| --- | --- | --- | --- | --- | --- |
| 12 | 4 | 4 | 26 | 0..3 | **emptied** |
| 20 | 5 | 37 | 127 | 0..8 | **emptied** |
| 30 | 6 | 52 | 232 | 0..11 | **emptied** |
| 40 | 7 | 169 | 2,083 | 0..16 | **emptied** |
| 42 | 7 | 134 | 1,062 | 0..14 | **emptied** |
| 56 | 8 | 261 | 1,765 | 0..23 | **emptied** |
| 57 | 8 | 243 | 1,199 | 0..22 | **emptied** |
| 58 | 8 | 216 | 746 | 0..21 | **emptied** |
| 65 | 9 | 756 | 46,134 | 0..35 | **emptied** |
| 72 | 9 | 522 | 5,988 | 0..28 | **emptied** |
| 73 | 9 | 481 | 3,855 | 0..27 | **emptied** |
| 74 | 9 | 431 | 2,559 | 0..26 | **emptied** |
| 89 | 10 | 950 | 11,152 | 0..41 | **emptied** |
| 91 | 10 | 852 | 6,442 | 0..39 | **emptied** |
| 92 | 10 | 795 | 4,633 | 0..38 | **emptied** |
| 93 | 10 | 763 | 3,651 | 0..37 | **emptied** |
| 94 | 10 | 715 | 2,685 | 0..36 | **emptied** |
| | | **7,381** | **94,339** | | **0 survivors** |

**What the table says.** Every declaration the family can write for every open row up to 100, at every
side that would beat the delivered one and every legal position of the block, beds a number of carrier
cells the count law did not ask for. Run 148's *sample* is now a theorem on more than twice as many rows, and
the structural reading it measured is the reason: a beat needs `K ≤ k−1` and a side below the delivered
one, so the seam gap `L − K` is under one unit, the block's own bbox `(p+q)/√2` is most of the box, and
its play `L − 2h` is small — the bed cannot be pushed down to `D*`. The cheapest demand everywhere is
`D* = 0`; the family never beds zero cells, because a block that fits inside the box is surrounded by
the carrier on all four sides.

**How many cells short.** The minima ask the same search a different question — the smallest `v` with a
hit, after every smaller `v` has been emptied — which turns "short" into a number. At `n = 12` on the
`K = 3`, 2×2 declaration (`D* = 1`): `D = 0` is emptied, `D = 1` is emptied, and `D = 2` is a **hit** at
the exact rational point

```
L  = 3.999999735963447809219360
cx = 2.025124976626836406448048
cy = 1.560660450042059491988836
```

where the counter reads 2. So the least bed over the legal domain is **exactly 2, certified** — "0
nowhere", "1 nowhere", "2 here" — and the row is **one cell short** on that declaration. (Run 149's
"the least bed is 2" was a reading of a 40-side × 7×7 sample; it is now a theorem with a witness.) The
row's cheapest demand is `D* = 0` (a `K = 3`, 1×3 block) and even there the least bed is 2, so the row is
two cells short at that one; the 2×2 is the sharpest single declaration the family has. `n = 20` is the
same shape of statement: at `(4,1,3,1,4)` the demand is `D* = 0` and the least bed is **5**, five cells
short; at `(4,2,2,2,2)` it is 2. Rows whose cheapest demand is large are not minimised — the loop would
ask dozens of attainability questions to pin a number no claim uses — and `--minima` says so rather than
reporting a lower bound as an answer.

## 4. The notched block, through the same engine

Run 148's list named this as its item 2: the block does not have to be a full rectangle. Remove a
corner of `a × b` block cells and the block is an **L**. The kept cells are then exactly the union of
**two full rectangles** in the block's own frame,

```
R1 = {u ∈ [−p/2+a, p/2], v ∈ [−q/2, q/2]}      (p−a) × q
R2 = {u ∈ [−p/2, −p/2+a], v ∈ [−q/2, q/2−b]}  a × (q−b)
```

so `m = p·q − a·b`, and the engine needs no new geometry: the **floor** is the union of the two
rectangles' forced sets (a cell forced by either kept rectangle is bedded by the block), and the
**ceiling** is the full `p × q` rectangle's possible set. The bracket is exactly the notch's own effect —
the cells that overlap the full block only inside the removed corner — and it closes as the boxes shrink.
The declared box is `a, b ≤ 2` with `a < p, b < q`, `p + q ≤ 13`, every `K ≤ k−1` and every split, on
the same seven rows. All seven have `delivered(n) = k` to within 1.6e-9, so the interval this run used
(the grid side) is a **superset** of the beat interval §3 now uses: the empty box lists below cover the
smaller interval too. The notched family was not extended to the ten rows §3 added, and §5 says so.

| n | k | declarations | boxes | `D*` | verdict |
| --- | --- | --- | --- | --- | --- |
| 12 | 4 | 7 | 43 | 0..3 | **emptied** |
| 20 | 5 | 94 | 262 | 0..8 | **emptied** |
| 30 | 6 | 160 | 708 | 0..11 | **emptied** |
| 42 | 7 | 429 | 3,709 | 0..14 | **emptied** |
| 56 | 8 | 972 | 7,722 | 0..23 | **emptied** |
| 72 | 9 | 1,935 | 25,635 | 0..28 | **emptied** |
| 91 | 10 | 2,441 | 31,535 | 0..32 | **emptied** |
| | | **6,038** | **69,614** | | **0 survivors** |

**What the notch does and does not buy.** The design arithmetic is clean and worth stating, because it is
the reason the notch cannot pay here: notching `a·b` cells lowers the block's own count by `a·b` while
keeping the same bbox (`h` is unchanged, so the same `L` is needed), so the count law's demand falls to
`D*_plain − a·b`. The notch must therefore **un-bed at least `a·b` carrier cells** that the full block
bedded. What it can un-bed is bounded by the cells whose only overlap with the block was inside the
removed corner, which is a band a cell wide around a corner of the block — at most a handful — while
`a·b` grows by four as soon as the notch grows. On these seven rows the band is never enough: every
notched declaration is emptied, so the family gains nothing by cutting a corner off the block.

## 5. What this closes, and what it leaves

**Closed.** (i) The block's position is no longer a hole in the family's account: on **every** open,
non-proved row up to 100 the family beats nothing — at any side that would beat the delivered one, at
any position, for every shape that fits: 7,381 declarations, 94,339 boxes, 0 survivors (plain block),
and the notched block on the seven rows it was run on under a superset interval. (ii) The method is a
decision, not a search, and it is cheap: twelve boxes per declaration on average (94,339 for 7,381),
because the count law's demand is a single integer and most declarations are pruned at the root; `n = 65`
is the one expensive row at 46,134 boxes, its domain holding the family's own tie at 8.5355. (iii) Band
5's tie is reproduced from this side too (control 6): `(5,1,1,1,2)` builds count 20 at `L = 5` exactly,
and the cheapest demand for 20 is emptied strictly below the delivered side. (iv) `n = 12`'s one-cell gap
is a certified minimum with an exact witness, not a sampled reading (§3).

**Left, honestly declared.** The block's shape is complete for these rows (`p + q ≤ isqrt(2k²−1)` is
every block whose bbox fits below the grid side) and `K ≤ k−1` is the family's own definition (`K = k`
*is* the grid). Outside the box: **the notch is capped at `2 × 2` and was run on seven rows, not
seventeen** — the plain block is the complete map, the notched one is a sample of rows; a purposeful
shape (a notch that follows the carrier's seam, rather than a corner of the block's own frame) is not in
this family; **rows above 100** are untouched by this decision (the wide sweep's ties there are doc 105
§2); a block whose bbox needs `p + q ≥ isqrt(2k²)` cannot fit below the grid side at all, so there is
nothing to decide there; and the engine proves nothing about *families it does not enumerate* — the
interleaved interface (doc 98) remains outside every count-law family. The `1e-8` floor is the project's
own (`carrier_ceil.MARGIN`): a pose that beats a row by less than that is not counted as a beat
anywhere, including here, and the interval's end is exactly that line.

## 6. Controls

`carrier_offset.py --selftest` (9):

1. the pair test, the four-strip form and `block_bed.in_bed` agree on 12 declaration × side pairs;
2. the rectangle's thresholds are `block_bed.beds` exactly (no re-derivation drift) on 4 shapes;
3. on 250 sampled points of 2 boxes, `floor ≤ D(point) ≤ ceiling` holds exactly;
4. **no false zero**: on 70 declaration × position triples a *planted* configuration (its count read off
   the pose, the pose gated) is walked down the chain of boxes that contain it — the engine's floor and
   ceiling bracket its bed at every depth, so its box can never be pruned. (The plain family has no
   *in-domain* planted pose — a legal pose at `K = k−1` has `n ≤ K²`, which is the theorem itself — so
   the control plants a point and shrinks the side window onto it; that is a test of the search, not of
   the row semantics, and it is the control that caught the missing seam law.)
5. the notched L is exactly `R1 ∪ R2`, and its kept cells never leave the full rectangle;
6. band 5: `(5,1,1,1,2)` builds count 20 at `L = 5` (gate ok), and the cheapest demand for 20 (`D* = 0`)
   is emptied strictly below 5 in 5 boxes; and the interval's end: 4.9999999916 at row 20 (delivered
   5.0000000016) and 8.5355338977 at row 65 (delivered 8.5355339077, grid side 9) — a pose at the
   delivered side is never inside the box;
7. the reflection identity `in_bed(dx, dy, q, p) = in_bed(dy, dx, p, q)` — why `p ≤ q` with every split
   is the whole family;
8. the bytecode audit: 30 decision functions, 0 naming `float`;
9. the minimiser: on 3 declarations the box list empties unresolved, the constant box that set the value
   reads it at its centre, and 125 sampled points of each domain are never below it.

The falsifier is structural rather than a row list here: the family cannot beat a proved-optimal row, and
this run adds no beat anywhere. The one proved row among the two counts the sweep misses (`n = 223`) is
consistent with that.

## 7. Reproduce

```
python3 scripts/carrier_offset.py --selftest   # 9 controls
python3 scripts/carrier_offset.py              # every open row to 100, plain block (~13 min)
python3 scripts/carrier_offset.py --notched     # the seven rows of §4, notched block (~25 min)
python3 scripts/carrier_offset.py --minima      # the exact least bed where it is cheap (~5 min)
```

Ledgers: `workspace/push/carrier_offset.json`, under `plain` and `notched` — per row the declarations
decided, the boxes visited, the box (with the interval's end), the tally of verdicts, the count law's
demands, and — for anything that survives — the surviving boxes as exact decimal shadows and, for a hit,
the gated pose; and `workspace/push/carrier_minima.json` for the exact least bed, its witness point and
the root floor where the minimum was not asked (`rows` in that file lists exactly which rows it covers,
so a partial run cannot be mistaken for the whole map — the minimum is a diagnostic, and the decision
above does not depend on it).

**Checks.** `sqscore.guard` green (22.217428576, 554 beats, 446 grid ties) at the start of every run; no
row changed; `submission.csv` and root `WHITEBOARD.md` untouched.

## 8. The correction this run made to doc 105

Three claims in doc 105 were wrong and are corrected there (§0) and in the code:

1. **`counts_max` filtered the wide map at 130.** `family_map`'s default is `counts_max = 130` and the
   wide run used it, so counts 131–225 were dropped before comparison. The same 213,150 declarations
   reach **223 of 225** counts and tie **58** rows, not 129 and 24.
2. **"Unattatined below the cap" is not "unattained everywhere".** The cap and `K ≤ 15`, `p + q ≤ 21`
   bound the statement; `n = 131`, one of the "never attained" rows, is attained on
   `L ∈ (12, 12.292893218814]` by `(K, kx, ky, p, q) = (12, 1, 1, 1, 9)` — inside that very box.
3. **The `n ≤ 100` map's two missing counts are `3` and `99`**, not `1` and `2`; `n = 1` is reached at
   side 2.

And two corrections this run made to **its own earlier framing** (run 149's, in this doc):

4. **The interval's end is the delivered side, not the grid side.** Run 149 used `L < k` everywhere. That
   is right, and stronger than needed, for the fourteen rows and `n = 12` whose delivered side is the
   grid side to 1.6e-9 — a beat needs `L < delivered − 1e-8 < k`. But `n = 40, 65, 89` deliver 1.7e-9
   *below* their grid side and the family attains the count at the delivered side with `K < k`, so
   `[sqrt n, k]` holds an attainment by construction: `n = 65`'s least bed under that interval is 0, a hit
   that is not a beat. The interval now ends at `delivered(n) − 1e-8` (control 6), which is exactly where
   the beat condition lives.
5. **`SMAX = 13` was a cap only at `k = 10`.** The complete bound is `p + q ≤ isqrt(2k²−1)` (§3): for
   `k ≤ 9` run 149's constant exceeded it, so nothing was lost there, but at `k = 10` it cut `p + q = 14`
   and with it 89..94's 7×7 blocks.

The wide and narrow ledgers were regenerated with the defect fixed (`carrier_ceil.json` for `n ≤ 100`,
`carrier_ceil_wide.json` for `n ≤ 225`), and `carrier_ceil.py --selftest` still passes 7/7.
