# 106 — The block's position, decided instead of sampled (Run 149)

**Headline.** Run 148's third measurement was a *probe*: on seven open tie rows it visited 40 sides ×
7×7 offsets × every `(K, split, shape)` — **421,713 declarations, 0 nominations**. A probe's zero is a
sample: it says the 49 positions tried per declaration missed, not that no position hits. This run
replaces it with a decision, in exact arithmetic, over the **whole** legal domain:

* **plain block** (`p × q`): seven rows, **1,579 declarations, 15,349 boxes, every box list emptied,
  0 survivors** — no side below the row's grid side and no block position attains the row's count;
* **notched block** (`p × q` minus an `a × b` corner, `a, b ≤ 2`), through the same engine and on the
  same rows: **6,038 declarations, 69,614 boxes, every box list emptied, 0 survivors** (parameter box
  in §4).

Nothing was promoted: no candidate exists to promote, so C1–C4 was never entered, `submission.csv` and
root `WHITEBOARD.md` are untouched, and the delivered total stands at **22.217428576** (554 beats, 446
grid ties). The run also **re-ran the run-148 sweep** to build on it and corrected three of its claims —
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

## 3. The seven rows, plain block

The open, non-proved tie rows — the plain grid's side, where the literature has not proved the grid
optimal. `PMAX = 10` (`p, q ≤ 10`), `SMAX = 13` (`p + q ≤ 13`), every `K ≤ k−1`, every split up to the
box's reflection, `p ≤ q` up to the block's frame symmetry (control 7), and the count law's own
`m ≥ n − K²`.

| n | k | declarations | boxes | the count law's demands `D*` | verdict |
| --- | --- | --- | --- | --- | --- |
| 12 | 4 | 4 | 26 | 0..3 | **emptied** |
| 20 | 5 | 37 | 127 | 0..8 | **emptied** |
| 30 | 6 | 52 | 244 | 0..11 | **emptied** |
| 42 | 7 | 134 | 1,062 | 0..14 | **emptied** |
| 56 | 8 | 261 | 1,767 | 0..23 | **emptied** |
| 72 | 9 | 506 | 5,972 | 0..28 | **emptied** |
| 91 | 10 | 585 | 6,151 | 0..32 | **emptied** |
| | | **1,579** | **15,349** | | **0 survivors** |

**What the table says.** Every declaration the family can write for these seven rows, at every legal
side below the grid side and every legal position of the block, beds a number of carrier cells the
count law did not ask for. Run 148's *sample* is now a theorem on the same rows, and the structural
reading it measured is the reason: a beat needs `K ≤ k−1` and `L < k`, so the seam gap `L − K` is under
one unit, the block's own bbox `(p+q)/√2` is most of the box, and its play `L − 2h` is small — the bed
cannot be pushed down to `D*`. The two cheapest demands in the whole table are `D* = 0`; the family
never beds zero cells, because a block that fits inside the box is surrounded by the carrier on all
four sides.

The `n = 12` case is the sharpest and worth naming: its only near declaration is `K = 3`, a 2×2 block,
`D* = 1`, and the *least* bed over the whole legal domain is 2 — one cell more than the row needs, at
every side and every position. That single cell is the difference between a beat at `L ≈ 3.92` (margin
`0.08` over the delivered 4) and a tie at 4. It is now a proved difference, not a sampled one.

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
The declared box is `a, b ≤ 2` with `a < p, b < q`, `PMAX = 10`, `SMAX = 13`, every `K ≤ k−1` and every
split, on the same seven rows:

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

**Closed.** (i) The block's position is no longer a hole in the family's account: on the seven open,
non-proved tie rows the family beats nothing at any side, at any position, for every declaration in the
declared box — plain block and notched. (ii) The method is a decision, not a search, and it is cheap:
15,349 boxes for 1,579 declarations (about ten boxes per declaration), because the count law's demand is
a single integer and most declarations are pruned at the root. (iii) Band 5's tie is reproduced from
this side too (control 6): `(5,1,1,1,2)` builds count 20 at `L = 5` exactly, and the cheapest demand for
20 is emptied strictly below 5.

**Left, honestly declared.** The declared parameter box is `p, q ≤ 10`, `p + q ≤ 13`, `a, b ≤ 2`, `K ≤
k−1`, and the seven rows. Outside it: larger blocks (`p + q > 13`) cannot fit below these rows' grid
sides at all for `k ≤ 8`, but for `k = 9, 10` the box is a real restriction and a wider `SMAX` is the
first thing to try; the notch is capped at `2 × 2` and a purposeful shape (a notch that follows the
carrier's seam, rather than a corner of the block's own frame) is not in this family; the interleaved
interface (doc 98) remains outside every count-law family. The engine also does not *prove* a coverage
statement about *all* families — only about the declarations it enumerates, which is why the enumeration
is spelled out above rather than summarised.

## 6. Controls

`carrier_offset.py --selftest` (8):

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
   is emptied strictly below 5 in 5 boxes;
7. the reflection identity `in_bed(dx, dy, q, p) = in_bed(dy, dx, p, q)` — why `p ≤ q` with every split
   is the whole family;
8. the bytecode audit: 23 decision functions, 0 naming `float`.

The falsifier is structural rather than a row list here: the family cannot beat a proved-optimal row, and
this run adds no beat anywhere. The one proved row among the two counts the sweep misses (`n = 223`) is
consistent with that.

## 7. Reproduce

```
python3 scripts/carrier_offset.py --selftest   # 8 controls
python3 scripts/carrier_offset.py              # the seven open tie rows, plain block (~2 min)
python3 scripts/carrier_offset.py --notched     # the same rows, notched block (~10 min)
```

Ledger: `workspace/push/carrier_offset.json`, under `plain` and `notched`: per row the declarations
decided, the boxes visited, the tally of verdicts, the count law's demands, and — for anything that
survives — the surviving boxes as exact decimal shadows and, for a hit, the gated pose.

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

The wide and narrow ledgers were regenerated with the defect fixed (`carrier_ceil.json` for `n ≤ 100`,
`carrier_ceil_wide.json` for `n ≤ 225`), and `carrier_ceil.py --selftest` still passes 7/7.
