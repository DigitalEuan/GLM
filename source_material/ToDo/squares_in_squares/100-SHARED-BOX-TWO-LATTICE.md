# 100 — The shared box, built and refused: two whole lattices reproduce 0 of the 110 two-class rows (Run 143)

**Run 143, 2026-11-25.** Instruments `scripts/shared_box.py` (new) and `scripts/tilt_audit.py`
(extended), ledgers `workspace/push/shared_box.json` and `workspace/push/tilt_audit.json`. Doc 99
left one instruction and one gate: build the area-sharing two-lattice constructor, and reproduce at
least 20 of the 110 delivered two-class `(n, side)` pairs **before** any search sweep. This run
widens the coverage measurement, builds the constructor exactly as briefed, and runs the gate first.

**Answer: the constructor is built, certified and refused by its own gate.** It reproduces **0 of
110** delivered two-class sides (threshold 20), its closest configuration is the degenerate spinor
`1/1` — a plain grid split — in **110 / 110** rows, and its best side is **never below the grid**
(equal in 106 rows, above in 4) while the delivered sides sit 0.0503-0.4792 under it. **No sweep was
run.** The refusal is exact, not a tuning failure: a full rectangular block fills its own bounding
box, so two full blocks cannot share area at all — they can only share the *container*. Area sharing
needs a carrier with a void in it, and the delivered rows have one: **0 of 110** are two single
lattices, with the larger class a union of **4-54** lattice translates.

**Nothing promoted.** `submission.csv` and root `WHITEBOARD.md` are untouched; the delivered total
stands at **22.217428576** / 554 beats / 446 ties.

## 1. What was asked

Three parts, in this order:

1. extend the tilt audit so the bbox-fill / area-sharing measurement covers **every** priced-out
   class in all 508 beating rows (doc 99 §6 measured only the 110 two-class probes);
2. build `scripts/shared_box.py` — two whole lattices in one shared box, no deletions, float-free —
   and run doc 99 §9's entry test **first**, with no sweep before it passes;
3. record the outcome with exact numbers, including a refusal and its diagnosis if the gate fails.

Part 2 failed its gate, so part 3 is a refusal record. Nothing below is a search result.

## 2. Part 1: the sharing is population-wide, not a two-class artefact

`tilt_audit.py` already decided, per class, whether doc 98's inequality prices it out. It now also
measures, for **every such class**, how much of the class's own bounding box is occupied by *any*
cell — its own or another class's — through a unit-bucket index over all cells of the row. The new
per-class fields are `inside`, `coverage` and `cover_ratio` (= coverage ÷ the row's own box density
`n/L²`); per row `po_classes`, `po_cells`, `po_inside_zero`, `po_ratio_ge90`, `po_ratio_median`,
`po_ratio_min`; and aggregate `po_*` fields.

| all priced-out classes | value |
| --- | --- |
| classes / rows / cells | **873 / 508 / 43,144** |
| bbox-sharing ratio, pooled q1 / median / q3 / min | **0.918 / 0.951 / 0.973 / 0.688** |
| classes at ratio ≥ 0.90 | **719 of 873** |
| classes at ratio < 0.50 | **0** |
| classes with **no** other cell inside their bbox | **1** (in the 1 row where every priced-out class is like that) |

The two-class probe doc 99 reported is unchanged by the wider measurement (coverage median 0.879,
ratio median 0.937), which is the expected cross-check: the 110 rows were a faithful sample, not a
favourable one. The mechanism is therefore population-wide — in 872 of 873 priced-out classes the
box the inequality charges for is being used, usually to the container's own density. Doc 99 §6 is
confirmed at the level of every class rather than one probe per row.

This is a measurement, not a construction; no verdict moved and no side changed.

## 3. Part 2: the constructor, exactly as briefed

`scripts/shared_box.py` builds two **full rectangles of lattice** and keeps both whole:

- **A**: an `a1 x a2` block of axis cells, exactly the rectangle `[0, a1] x [0, a2]`;
- **B**: a `b1 x b2` block of the same lattice rotated by a rational spinor
  `tan(theta/2) = p/q`, so `c = (q²-p²)/(p²+q²)`, `s = 2pq/(p²+q²)`, occupying a rotated
  rectangle of bbox `W = b1 c + b2 s` by `H = b1 s + b2 c`;
- A in the bottom-left corner, B's bbox in the top-right corner of one square box `[0, L]²`, so the
  **container** is shared and nothing is deleted.

**The contact side is closed-form.** With `Delta = c_B - c_A` the four axis slacks are affine in
`L`, so

    s* = max( max(a1, a2, W, H),  min(r_x, r_y, r_u, r_v) )

with `r_x = a1 + W`, `r_y = a2 + H` and `r_u`, `r_v` the two rotated-axis roots. No bisection and no
scan: one `Fraction` expression per split, and `legal` re-decides it from the slacks.

**The certification path is independent.** Every accepted pose is rebuilt as exact `Fraction`
cells `(x, y, c, s)` and every pair is passed to `import_n090.pair_slack` — the exact SAT used by
the delivered table — so a control or entry-test pass is a cell-level statement, not a restatement
of the rectangle algebra. (One bug was found and fixed this way: the block must be translated by
its **cell-corner** bbox `min(centre) - (|c|+|s|)/2`, not its centre bbox, or it sits half a cell
into its neighbour. The first build showed min slack `-1/2` and one overlap; the SAT caught it.)

The exact-arithmetic audit is clean: `exact_field.audit_module` reports **16 decision functions, 0
naming `float`**.

## 4. Controls (9, all exact)

1. four spinors satisfy `c² + s² = 1` identically;
2. `4x4 + 2x2` at the 53.13° spinor `1/2`: `s* = 214/35 = 6.1142857` exactly (diagonal contact),
   legal there and illegal `1e-9` below — the closed form is tight;
3. the built pose at that side: **20 cells, 0 overlaps**, min slack exactly 0, side reproduced to
   `1e-12` by the independent SAT;
4. squeezing the box by `1/4` breaks 2 cell pairs, and the SAT agrees;
5. the side is a genuine saving against doc 97's butted bound: **6.114286 < 6.800000**
   (saving 0.685714);
6. the degenerate spinor `p = q` (90°, `c = 0, s = 1`): `4x4 + 1x1` = **17 cells at side 5**, 0
   overlaps — the grid, as doc 97 says;
7. `shapes(0)` is empty and `shapes(1) = [(1, 1)]` (no zero-cell block can be built);
8. containment: every cell of three further configurations lies inside `[0, L]²`;
9. the decision path names no `float` (16 functions, 0 offenders).

The family is non-empty and it genuinely shares the container: control 5 proves a tilted pair can
beat a butted one by 0.686 of side. The gate below is therefore a statement about the delivered
rows, not about a broken constructor.

## 5. The entry test: 0 / 110, and the family never leaves the grid

Test: for each of the 110 two-class beating rows, the family's closest side to the delivered side
over every split `A + B = n` (both blocks, `n = 5 … 974`), every divisor-pair shape with aspect ≤ 3,
and the six spinors `1/1, 1/2, 2/3, 1/3, 1/4, 3/4`, at tolerance `1e-8`. A pass requires 20 rows and
an exact-SAT certificate with 0 overlaps.

| entry test | value |
| --- | --- |
| rows reproduced (threshold 20) | **0 / 110 — FAIL** |
| rows with no split fitting the delivered box | 0 |
| configs strictly beating the delivered side | **0** |
| closest configuration genuinely tilted | **0 / 110** |
| family best side equals the grid side `k` | **106 / 110** |
| family best side **below** `k` | **0 / 110** |
| `\|s* - L_delivered\|` min / median / max | **0.1144 / 0.3171 / 1.3934** |
| quartiles of that deficit | 0.1144 / 0.2929 / 0.3171 / 0.4645 / 1.3934 |
| delivered saving `k - L` min / median / max | 0.0503 / 0.3076 / 0.4792 |

The closest row is `n = 19`: delivered **4.885618084…**, family best **5** (`4x4 + 1x3` at `1/1`),
deficit 0.1144. The worst is `n = 489`: delivered **22.6066017…**, family best **24**
(`21x22 + 3x9` at `1/1`), deficit 1.3934. In both, and in all 110 rows, the closest pose is the
degenerate spinor — which is the plain grid split — so **the family's entire reach is the grid or
worse**. This is stronger than the entry test needed: not only does it fail to reproduce a delivered
side, it never produces a single configuration below `k`.

## 6. The structural census: the delivered classes are not single lattices

The entry test says the family cannot reach the delivered poses. The census says why, and it is not
about tilt at all. For each of the 110 rows, each class is projected onto its own lattice frame
(`u = x c + y s`, `v = -x s + y c`) and the cell centres are reduced modulo 1 at `1e-6`; the number
of distinct remainders is the number of **translation domains** the class is built from. One domain
is a single lattice translate; more means a sparse carrier, a union of disjoint pieces.

| translation domains (110 rows) | value |
| --- | --- |
| rows where both classes are a single lattice | **0** |
| smaller class | 1-7 domains |
| larger class | **4-54 domains** |
| rows where at least one class has ≥ 4 domains | **110 / 110** |

So every delivered two-class row is two *sparse, multi-translate* lattices — not two full
rectangles. They interlock because each class has voids the other occupies; a class with 4-54
translates has plenty of them, while a full block has none.

This is a tolerance statement at `1e-6` on the delivered decimal coordinates, the same tolerance at
which doc 99's class partition is stable 110/110. It is written into the ledger with the per-row
domain pair, so it can be re-read rather than trusted.

## 7. The diagnosis: a shared container is not a shared box

Two facts, one algebraic and one geometric, make the refusal structural.

**Algebraic.** A full `b1 x b2` block's bbox is exactly

    W H = (b1 c + b2 s)(b1 s + b2 c) = b1 b2 + (b1² + b2²) (sin 2theta)/2
        >= b1 b2 (1 + sin 2theta),

with equality at `b1 = b2` (AM-GM). That is doc 98's price, now an identity for this family rather
than an inequality about a grain.

**Geometric.** Because a block *is* a full rectangle of unit cells, its cells tile its bbox exactly.
Two such blocks are cell-disjoint **iff** their rectangles are disjoint (control 3 checks the two
directions against the cell-level SAT on the built poses). Two disjoint rectangles inside a box of
side `L` have areas that add, so

    L² >= a1 a2 + W H >= n + m_B sin 2theta,

and a beat, `L < k`, requires `m_B sin 2theta < k² - n <= 2k - 1`. Tilting is therefore only
affordable with a *small* tilted class at the very top of a band — exactly doc 99 §9's area window —
and the family's measured minimum never finds it: `0 / 110` splits go below `k`, `106 / 110` land on
`k` and 4 land above it.

The consequence is the correction doc 99 needs, and it is sharper than "the family is mis-parametrised".
Doc 99 read the delivered rows as "two lattices sharing one bounding box". The constructor shows that
**two full lattices cannot share a bounding box** — filling your own bbox is exactly what makes the
sharing impossible. Real area sharing requires at least one partner to be a **sparse carrier** with
a void the other fills, i.e. several translation domains, fill < 1. The delivered census says the
table has exactly that: 4-54 domains in the larger class of every row.

So the mechanism doc 99 measured is real; the object doc 99 proposed to build it with is not the
mechanism's carrier. Doc 99 §9's own words — "two whole lattices in one shared box, no deletions" —
name the one construction that provably cannot do it.

## 8. What this does to doc 99 §9

The decision in doc 99 §9 stands on the evidence; its **carrier** is corrected here:

- **Keep**: area sharing between two lattices, not many short grain contacts and not a better
  separating line. The census and the coverage measurement both still point there, and the 110 rows
  are still 110 rows of proof that the mechanism is delivered.
- **Correct**: the partner cannot be a full rectangle. The next prototype must be
  **sparse/notched carriers — fill < 1, 2-4 translation domains per class** — so that one lattice's
  void is the other's room. That is the shape the table actually uses.
- **Keep the gate**: the entry test is cheap (about 19 s over 110 rows, plus a 2 s census), it is
  falsifiable, and it refused a family that looked plausible on paper before any sweep was spent.
  Its threshold of 20 rows is what turned "build the thing doc 99 described" into a one-run negative.

## 9. What was not built, and why

No sparse-carrier constructor was written this run: it needs its own carrier spec (which translates,
which cells are dropped and by what rule), its own count law and its own controls, which is a run of
its own — the same judgement doc 99 made about this constructor, now paid back. **Refused: the
sweep; nothing promoted; `submission.csv` untouched.**

## 10. Guards, and what is not claimed

Checked this run, each exit 0: `shared_box --selftest` **9** · `shared_box` entry test + census
(0/110, 0/110 single lattices) · `tilt_audit --selftest` 8 · `interleaved_boundary` 9 ·
`twin_boundary` 5 · `notch136` · `glm_plan` 5 · `pure_slide` · `beaten_leverage` · `band5` ·
`ext_census` · `range_leverage` · `construct_seam` · `p_screen` · `legal_slide` · `structure
--control` and `--check-solver` · `perturb` · `anchor_chain` · `void_insert` · `true_geom` ·
`row_census` · `motif_wheels` 13 · `crystal_domains` 4 · `import_n090` 5 · `pub_bounds_check` 4 ·
`witt_octad` 5 · `leech_audit_fix` · `verify_certificates` · `sqscore` **22.217428576** (554/446) ·
`record_guard` OK · `glm_wheels --audit` 0 offenders · `py_compile`.

**Not claimed.** The entry test searches six spinors and aspect ≤ 3, so it is a statement about
*this* family, not about every full-block pair; the closed-form side, the cell SAT and the census are
exact/tolerance-stated as described, but a passing configuration somewhere outside the six spinors
was not searched for. The domain census is a `1e-6` tolerance statement on decimal CSV coordinates,
like doc 99's class partition. And no sparse carrier has been built, so nothing here says the
corrected prototype will pass its own gate — only that the table's shape says what it must be.
