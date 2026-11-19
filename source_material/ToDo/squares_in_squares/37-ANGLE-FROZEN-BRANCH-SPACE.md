# 37 — The branch space at frozen angles: an exact leaf, an empty bound (Run 74)

Run 73 nominated an instrument and closed a dimension. This run builds the instrument and finds
that half of it does not work — for a reason that is measurable in one line — and that the other
half does. It also answers the two questions attached to the nomination: the dimension theorem is
qualified everywhere it is stated, and `--milp` is retired.

No row of the table changed. The delivered total is still `22.218056945`, 553 beats, and
`sqscore.guard()` holds.

## 1. What the model is, and why this is the one that must be exact

`declp` (run 70) answers a *declared* question: given one separating axis per pair, can the
translations shrink the box? Its verdict is exact but its scope is the declaration, so a refusal
says nothing about the row — which is why runs 65–71 kept finding cells and never a row.

The branch-space model asks the disjunctive question instead. With orientations **frozen**, two
convex unit squares do not overlap **iff** some axis in `{u_i, v_i, u_j, v_j}` separates them:

    |(c_j - c_i) . q| >= h_i(q) + h_j(q),      h_k(q) = (|q.u_k| + |q.v_k|)/2

(the separating-axis theorem; `packlib.verify` evaluates the same min-over-four-axes penetration).
So

    "n squares at these angles fit in side L"
        <=>  "there is a choice of one (axis, sign) per pair and a translation with all
              separations and all containments at that choice"

is an **equivalence**, not a relaxation: a state that satisfies a declared separating axis for
every pair is a packing, and a valid packing has such a choice. That is what makes this instrument
different in kind from `declp`, and it is what made the nomination worth building.

The model at a node (`scripts/bb2d.py`):

    variables   d_i in R^2 translations, t = L, w_{p,a} in [0,1] for the branch a of pair p
    containment c_i + d_i + h_i <= t/2 ,  -(c_i + d_i) + h_i <= t/2
    pair p, a  s_a q_a.(d_j - d_i) + M (1 - w_{p,a}) >= h_i(q_a) + h_j(q_a) - s_a q_a.(c_j - c_i)
               sum_a w_{p,a} = 1
    objective   min t

`w` integral selects one branch per pair. `M` is *tight*: the exact maximum violation the disabled
constraint can reach over the containment box (`dbox`, `_BigM`), which matters — the symmetric
±(L+1.5) box used in the first draft made every M about three times larger and every bound worse.

The B&B is ours: the LP relaxation (fractional `w`) is the node bound, the branch is the pair whose
`w` is least integral, one child fixes its favourite branch and the other forbids it, the incumbent
is the delivered side, and a leaf's state goes through `declp.gate` — 12 dp, `packlib.verify`,
`tol = 0`. No solver sees the disjunction; the branch space is walked by us.

## 2. The bound is empty, and that is the finding

| n | delivered `L0` | root relaxation | largest square's own extent `max 2h_i` | `sqrt(n)` |
|---:|---:|---:|---:|---:|
| 5 | 2.707107 | 1.414214 | 1.414214 | 2.2361 |
| 6 | 3.000000 | 1.000000 | 1.000000 | 2.4495 |
| 9 | 3.000000 | 1.000000 | 1.000000 | 3.0000 |
| 10 | 3.707107 | 1.414214 | 1.414214 | 3.1623 |
| 11 | 3.877084 | 1.409216 | 1.409216 | 3.3166 |
| 13 | 4.000000 | 1.000000 | 1.000000 | 3.6056 |
| 18 | 4.822876 | 1.322876 | 1.322876 | 4.2426 |

The root relaxation equals `max_i 2h_i` on every row — **the extent of the single largest square**.
It says the box must hold one square, and nothing else.

Why: with `w` continuous and `sum_a w_a = 1`, a pair can put a fraction on each of its four axes
*and both signs*, and the two signs of one axis cancel. So `Delta c = 0` — the pair fully
overlapping — is feasible with `1/8` on each branch, every branch paid for out of its own big-M.
The relaxation therefore permits every pair to overlap and collapses to the containment system,
whose optimum is `max_i 2h_i` exactly. The cheap alternative — drop the undecided pairs — leaves
the same containment-only system and gives the same value at *every* node. So the disjunctive
relaxation is not better than dropping the pairs: at the root they coincide, and there is no bound
here to branch and bound on.

Consequences, measured rather than argued:

* **n = 2 and n = 3 close** (7 and 111 nodes) and agree with exhaustive enumeration of every
  structure (4 and 64 structures, control 3).
* **n = 5, 6, 9, 10 do not close** at a 6,000-node budget: 6, 1,235, 0 and 0 leaves reached, and
  the residual lower bound is still 2.000000. With no pruning the tree *is* the enumeration, and
  the families are `8^4 * 4^6 = 16,777,216` structures at n = 5 and `8^9 * 4^36 ~ 6.3e29` at
  n = 10 (4 branches on an axis-aligned pair, 8 on a tilted one).

So the answer to run 73 §6(c) is a negative with a cause: **a branch-space MILP at frozen angles
cannot certify a row of this table above n ≈ 4, and no row is certified by it.** It is not a budget
problem. It is that the disjunction, relaxed, says nothing.

## 3. What does close: the leaf oracle over a finite family

The leaf is exact, and small: `structure_lp` solves **one** complete structure with `2n + 1`
columns and no `w` at all (~1.5 ms). Two controls tie it to what the project already trusts:

* it reproduces `declp`'s own minimum side on the delivered structure — n = 5 `2.707106780`
  against `2.707106711`, n = 10 `3.707106779` against `3.707106731`, n = 18 `4.822875652` against
  `4.822875625` (differences +6.9e−8, +4.7e−8, +2.7e−8; the control asserts 1e−6);
* it agrees with the full leaf LP (with `w` pinned) on the delivered structure **and on a flip**.

That oracle answers a finite family exactly, and the family run 71 sampled is the natural one: the
delivered branch assignment, changed in `k` places. Every member is solved to *its own* minimum
side — so the answer is a number and a margin, not a yes/no at one eps — and any improvement would
still have to pass the gate.

`python3 scripts/bb2d.py --flips 2 5 10 11 13` (110 s):

| n | `L0` | structures in `k = 1` | moved | infeasible | nearest moved | `k = 2` | moved | infeasible | improvements |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 2.707107 | 46 | 28 | 16 | **+2.36e−1** | 979 | 280 | 696 | **0** |
| 10 | 3.707107 | 199 | 71 | 96 | **+4.04e−2** | 19,477 | 3,792 | 15,161 | **0** |
| 11 | 3.877084 | 285 | 75 | 168 | **+4.48e−3** | 40,050 | 5,107 | 34,052 | **0** |
| 13 | 4.000000 | 234 | 0 | 153 | — | 27,261 | 0 | 24,119 | **0** |
| 18 | 4.822876 | 779 | 148 | 464 | **+1.04e−2** | — | — | — | — |

Totals at `k = 2`: **87,767 structures, 9,179 of which have a different minimum side, 74,028 not
feasible inside `L0 + 0.5`, 4,560 tied, and 0 improvements.** Every improvement would have been
gated; none occurred. "Moved" is the honest denominator: a flip of a pair that is slack in both
branches changes nothing, and of the 1,543 single flips at these five rows only **322** change the
optimum (897 are not feasible inside `L0 + 0.5` and 324 are tied). Counting all 1,543 as "tested"
would have overstated run 71's kind of search by a factor of five.

Two numbers in that table are the useful ones:

* **n = 13 is completely rigid** — 0 of 234 single flips and 0 of 27,261 double flips change the
  optimum. That is what run 73's corollary predicts for an axis-aligned row: no declaration
  matters, because the grid is optimal in the axis-parallel class by theorem.
* **n = 11 has a competitor 4.48e−3 away.** Something in the depth-2 family needs 3.881566 against
  the delivered 3.877084. That is the tightest measured neighbourhood in the table: the row is a
  record by four milli-units of side under this family, and any further search there is aimed at a
  gap of that size, not at a structural one.

What this does **not** say: that `L` is optimal for the angle multiset. It says the delivered
*structure* is optimal among the structures within two declared-branch changes of itself, at those
angles. The rest of the branch space is closed by nothing (see §2).

## 4. The dimension theorem, qualified

Run 73's counting argument is correct and its scope was stated too broadly. The theorem is:

> For **axis-parallel** unit cubes in `d` dimensions, `L_d(n) = ⌈n^{1/d}⌉` for every n.

It says nothing about rotated solids, and the restriction is not vacuous. In two dimensions the
same argument gives `L = ⌈√n⌉` **for axis-parallel squares**, and the delivered table's own n = 5
row is `2.707107 < 3 = ⌈√5⌉` because one square is at π/4. Rotating is exactly the freedom the
theorem excludes, and it is the freedom the score is made of (447 aligned rows, all at `⌈√n⌉`;
553 beats, none aligned). So `L_d(n) = ⌈n^{1/d}⌉` is *the optimum in the axis-parallel class* — which
is what the proof covers, what all of run 72's comparisons live in, and what makes the 447 rows
optimal within that class and not one word more.

**And run 72's headline needs one correction, which the same reading forces.** The "extrusion of
the delivered 2D row" is only a cube state when the row is axis-aligned: a square at π/4 is not a
unit cube, and at n = 5 and n = 10 the ledger already says `extrude_ok = False`. At those two rows
the column marked `extr` (`2.7071`, `3.7071`) is the extent of a set of **overlapping** cubes, and
`desc(extr) = L2` is not rigidity — the trace shows the description LP proposing `3.0` and `4.0`
and the descent refusing, because the state it started from is not legal. So:

* the `3D strictly better` verdict is **true** at n = 5 and n = 10 but **vacuous**: there is no
  extruded packing to beat, only a row that cannot be extruded;
* the "extrusion is rigid under its own declared axes on every row" reading in `35` §3 is wrong at
  those two rows and stands at the other ten;
* the 3D comparison itself is untouched: `L(9) = 3`, `L(5..8) = 2`, `L(n) = ⌈n^{1/3}⌉` by §2's
  theorem, all inside the axis-parallel class.

## 5. `--milp` is retired

Decision: **remove it from `declp3.py`.** 126 lines — `_disjunction`, `milp_min_side`,
`feasible_below`, `milp_report` and the `--milp` dispatch — deleted. Reasons, in order:

1. **It is subsumed.** The sub-box count settles every n in every dimension in nine lines. A solver
   path that can only ever re-derive a proved value is not an instrument, it is a liability.
2. **It never did the job it was built for.** n = 9 (216 binaries) timed out at 60 s and was killed
   at 300 s; n = 4 and n = 5 closed only because they are tiny.
3. **Run 74 measures why a bigger budget would not help.** The 2D branch-space relaxation — the
   same big-M disjunction one dimension down — has a root bound equal to the largest square's own
   extent. The 3D one is the same construction; it closed n ≤ 5 by enumeration inside the solver,
   not by bounding.

The record of what it did stays in `36` §4 (and in `git show fd22941`). `--exhaustive` and
`--selftest` stay; they are cheap, and `--exhaustive` is a genuine lower bound for n ≤ 4.

## 6. Controls

```
python3 scripts/bb2d.py --selftest        # 4 controls, exact gate, 1.8 s
```

1. **Degradation to `declp`** — the delivered structure's LP against `declp`'s own bisected optimum
   at n = 5, 10, 18 (agreement to 7e−8), and the root relaxation printed beside it (1.414214
   against 1.414214 for "drop every undecided pair": the measurement in §2, in the control).
2. **Lean structure LP = full leaf LP** on the delivered structure and on one flip, at n = 5, 10.
3. **Exhaustive structure enumeration at n = 2, 3** — 4 and 64 structures — against the B&B's
   answer, both closed.
4. **The gate is the judge** — the delivered n = 5 row gates at `2.707106782`; a copy with one
   square moved 75% of the way to another is refused with penetration `0.905330`.

Two defects were caught by these controls and by none of the printed results: the `w` columns were
first laid out at `offs[p] + a` instead of `2n + 1 + offs[p] + a`, so the branch weights overlapped
the translation columns (every leaf came back infeasible); and the translation box was first
derived for a container `[0, L]` while the model's container is `[-L/2, L/2]` (every leaf came back
infeasible again). Both were found by control 1 refusing to reproduce `declp`, which is the third
run in a row that this control has earned its place.

## 7. What this means for the project

* **The nomination is closed, negatively.** Run 73 §6(c) hoped a 2D branch-space MILP would
  "certify a row optimal for its angle multiset instead of failing to improve it". It cannot: the
  relaxation is empty, so the method is enumeration, and the families are `10^16` and `10^29`. The
  remaining certified statements are the finite ones in §3.
* **The row-level question is still open, and now it is priced.** For n = 11 the depth-2 family
  comes within 4.48e−3; for n = 10 within 4.04e−2. Anyone attacking a row at frozen angles should
  aim at that margin, and should know that 84% of the depth-2 structures are not even feasible
  inside `L0 + 0.5`.
* **The score's lever has not moved.** Axis-aligned rows cannot gain by theorem (run 73), and
  rotated rows cannot gain by branch change within two (this run). What is left is the angle
  multiset itself — the angle word of `31`/`28` — and the 675-row source block. That is the same
  conclusion as run 73, reached from the other side, and it is now supported by 87,767 solved
  structures rather than by 6,684 feasibility tests.

## 8. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/bb2d.py --selftest                       # 4 controls (~2 s)
python3 scripts/bb2d.py 2 3 5 6 9 10                     # B&B: 2,3 close; 5-10 open
python3 scripts/bb2d.py --flips 1 5 10 11 13 18          # depth 1, exact (~4 s)
python3 scripts/bb2d.py --flips 2 5 10 11 13             # depth 2, exact (~135 s)
python3 scripts/declp3.py --selftest                     # the 3D instrument, unchanged
```

Ledgers: `workspace/push/bb2d.json` (B&B), `bb2d_flips1.json`, `bb2d_flips2.json` (the families).
