# 32 — The wall margin, and one row's branch-rotation search (Run 69)

Run 68 audited a framing and recorded that its "thinnest wall margin" numbers
were not reproducible from any `sqscore` quantity. This record replaces the
phrase with a definition, computes it on all 1000 delivered rows, and then
spends one row on the search the framing nominated. No row of the table changed;
the delivered total is still `22.218056945` and `sqscore.guard()` still holds. *(Historical: at that time.)*

## 1. The definition

Two different walls bound every row, and Run 68 ran them together:

* the **area wall** `sqrt(n)` — no packing of n unit squares has a smaller side.
  It is a theorem, and it is unreachable except when n is a perfect square;
* the **grid wall** `k = ceil(sqrt(n))` — the side of the plain k × k grid. It is
  a convention: 553 rows are already below it, so it is not a bound at all.

The wall margin is measured against the wall that is a theorem:

| quantity | definition | meaning |
|---|---|---|
| **wall margin** | `mu(n) = L(n) − sqrt(n)` | side length between the delivered side and the area wall — exactly the length any new construction must consume |
| **normalised margin** | `rho(n) = mu(n)/sqrt(n) = score(n)` | its price in score; it is the row's contribution to the total |
| **held** | `k(n) − L(n)` | how far the row already sits below the grid (`held = 0` ⇒ at the grid wall) |
| **value** | `1/sqrt(n)` | score bought per unit of side removed (the marginal) |

`scripts/wall_margin.py` computes all four for n = 1..1000 and writes
`workspace/push/wall_margin.json`.

**Precision.** The delivered table is decimals — coordinates at 12 dp and 45,921
distinct float angles — so there is no exact algebraic `L` to be had from it and
`mu` is exact *for the table as delivered*, not in closed form. `extent_dec()`
re-derives `L` at 50 significant digits with a Decimal cos/sin as a check:

| row | float `L` | 50-digit `L` | difference |
|---|---:|---:|---:|
| 18 | 4.822875657118 | 4.8228756571181033 | 6.2e−16 |
| 184 | 14.000000001858 | 14.000000001858 | 0 |
| 656 | 26.000000001924 | 26.000000001924 | 0 |
| 819 | 29.000000001932 | 29.000000001932 | 0 |

Every margin in this record is decided by gaps ≫ 1e−12, so no ranking below
depends on the last digits.

## 2. The 1000 rows

| statistic | value |
|---|---:|
| rows | 1000 |
| `mu > 0` | 999 |
| `mu = 0` exactly | 1 (n = 1) |
| range of `mu` | 0.000000 … 0.585786 |
| median `mu` | 0.441761 |
| median `rho` | 0.017494 |
| rows with `mu > 0.5` | 251 |
| rows with `mu > 0.55` | 7 |

The perfect squares do not appear at `mu = 0`; they sit `1.0e−9 … 1.9e−9` above
the wall because `packlib.finalize` opens every contact by ~2e−9. So the
thinnest positive margins in the table are, without exception, the 15 smallest
perfect squares (4, 9, 16, … 256, all at ~1e−9): the zero-room band is occupied
entirely by rows whose optimum is `sqrt(n)`.

Fifteen largest margins:

| n | `mu` | `rho` | k | held | proved | beat |
|---:|---:|---:|---:|---:|---|---|
| 2 | 0.585786 | 0.414214 | 2 | ~0 | yes | no |
| 18 | 0.580235 | 0.136763 | 5 | 0.177 | **no** | yes |
| 39 | 0.565724 | 0.090588 | 7 | 0.189 | no | yes |
| 11 | 0.560459 | 0.168985 | 4 | 0.123 | yes (see §5) | yes |
| 68 | 0.552584 | 0.067011 | 9 | 0.201 | no | yes |
| 17 | 0.552424 | 0.133983 | 5 | 0.324 | yes (see §5) | yes |
| 6 | 0.550510 | 0.224745 | 3 | ~0 | yes | no |
| 51 | 0.548928 | 0.076865 | 8 | 0.310 | no | yes |
| 29 | 0.548669 | 0.101885 | 6 | 0.066 | no | yes |
| 86 | 0.546917 | 0.058976 | 10 | 0.179 | no | yes |
| 10 | 0.544829 | 0.172290 | 4 | 0.293 | yes | yes |
| 53 | 0.542766 | 0.074555 | 8 | 0.177 | no | yes |
| 38 | 0.542693 | 0.088036 | 7 | 0.293 | no | yes |
| 105 | 0.542353 | 0.052928 | 11 | 0.211 | no | yes |
| 127 | 0.541451 | 0.048046 | 12 | 0.189 | no | yes |

The four largest **`rho`** in the whole table are n = 2 (0.414214), 6 (0.224745),
10 (0.172290) and 11 (0.168985) — every one of them a row the record names as
proved optimal. The rows with the most score per row are all closed.

## 3. n = 184, 656, 819 — the verdict

| n | L | k | `mu` | rank of `mu` | `rho` | rank of `rho` | held | proved | beat |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 184 | 14.0000000019 | 14 | 0.435340 | 517 / 1000 | 0.032094 | 159 / 1000 | −1.9e−9 | no | no |
| 656 | 26.0000000019 | 26 | 0.387503 | 604 / 1000 | 0.015129 | 637 / 1000 | −1.9e−9 | no | no |
| 819 | 29.0000000019 | 29 | 0.381824 | 610 / 1000 | 0.013342 | 702 / 1000 | −1.9e−9 | no | no |

They are **not special, in either direction**.

* All three sit *at* the grid (`held ≈ −2e−9`: the finalize pad, i.e. `held = 0`
  to the table's precision). Measured room is 0.435 / 0.388 / 0.382 of side.
* On side length they rank **517, 604, 610** of 1000 — mid-table, not near the
  top and nowhere near the bottom. 251 rows have `mu > 0.5`, all three are below
  that; the maximum is 0.585786 and the median 0.441761, so 184 is slightly
  above the median and 656/819 slightly below.
* On score value they rank **159, 637, 702**. n = 18 alone has `mu = 0.580235`
  and `rho = 0.136763` — 3.2× the normalised margin of n = 184.
* They are certainly not the **thinnest**: the thinnest positive margins belong
  to the perfect squares at ~1e−9, and every one of those is proved optimal.
  Run 68's "thinnest wall margin" reading is exactly inverted: thin margins are
  where no room exists, not where room is scarce among live rows.

What the ranking cannot say, and this is the honest limit: `mu` is geometry, not
opportunity. §9.2 of `26-FRONTIER-CROSSWALK.md` records **0 rows above best
known** for n ≤ 324, and 675 rows have no source at all, so no row in this table
has "unclaimed side" in the source sense. A large `mu` at n = 18 does not mean
`0.58` of side is available; it means the row is far from the area wall, which
is true of every row whose n is far below a square.

## 4. The target rule

Fixed before the search, so the row is not chosen to fit the outcome:

> among rows that are (a) not proved optimal by this project's record, and
> (b) small enough to enumerate the whole declared cell space (n ≤ 20), take the
> largest `rho`, tie-break on `mu`.

The proved set is `optima.proved()` **plus** the rows the record quotes as proved
optimal below the grid — `s(5), s(11), s(12), s(13), s(17), s(19)` (`README`,
`04-RUN-LOG.md` run 27). With that exclusion the rule selects

**n = 18**, `L0 = 4.822875657118104`, `rho = 0.136763` (rank 8 / 1000),
`mu = 0.580235` (rank 2 / 1000), 18 of 18 squares tilted, `held = 0.177`.

Excluding n = 11 is a correction, not a choice: the naive rule ("not in
`optima.proved()`") picks n = 11, and a search there would have been spent on a
row this record elsewhere calls closed (§5).

## 5. A record inconsistency, found while applying the rule

The tree says two incompatible things about the small rows, and the difference
decides whether a search at n = 11 or 12 is live:

* proved: `README`/`STATUS` "156 proven-optimal rows (… s(5), s(11), s(17),
  s(19))", `04-RUN-LOG.md` run 27 "Stromquist Thm 2 for s(11)", and
  `GLM_INVESTIGATION.md` "s(11) = 3.87708…, s(12) = 4, s(13) = 4, s(21) = 5".
* open: `01-LAYERS.md` ("one deliberate `sorry` marking the s(11) wall"),
  `workspace/docs/02-decomposition.md` ("optimality known only for
  n ∈ {1..8, 10, 14, 15, 24, 35} + families"), and
  `workspace/verification/VERIFICATION_REPORT.md` ("optimality of s(11) open").

Both cannot be right. This run resolves nothing about it — it only refuses to
search a row whose status is contested, and flags the contradiction for a
separate pass. Nothing else in this record depends on the answer.

## 6. The search — 5,560 cells, one row

Words are exact: a rational `t = tan(theta/2)` gives `cos = (1−t²)/(1+t²)` and
`sin = 2t/(1+t²)`, so no angle enters the model as a rounded float.

| word | t | theta |
|---|---:|---:|
| axis | 0 | 0° |
| `p8` | √2 − 1 | 45° |
| `atan2` | 1/2 | 53.1301° |
| `atan3` | 1/3 | 36.8699° |
| `atan4` | 1/4 | 28.0725° |

Three cell families, all on row 18:

1. **B — branch assignment.** Squares grouped into delivered angle classes; every
   square in a class takes the same word; all `|W|^b` combinations.
2. **S1 / S2 — word reassignment.** One square re-worded (18 × 5 = 90 cells) and
   two squares re-worded (153 × 25 = 3,825 cells), every other square delivered.
3. **R — re-slot.** A tilted square is moved to another square's slot *and*
   re-worded (5 × 5 × 18 = 1,620 cells, the five tilted squares only).

Each cell is priced by the run-67 corrected declared-axis LP — separation on the
owner's axis is `0.5 + the other square's extent`, the defect that invalidated
run 67's first pass — with every translation free, all pair axes declared from
the trial geometry, and side `L0 − eps` for `eps ∈ {1e-2, 3e-3, 1e-3, 1e-4, 1e-6}`
at a 5e−10 separation pad. Then, for cells the LP admits, a **second, undeclared
pass**: `cram_relax.relax` pressure-settles the cell at `L0 − 1e-3` for 1,200
moves and `cram_relax.settle_and_gate` reports `packlib.finalize` +
`packlib.verify`.

The gate is the only judge: a 12-dp state, `packlib.verify(..., tol=0.0)`, and
`sqscore.row_gain`. LP feasibility alone counts for nothing.

| pass | cells | LP-feasible | gate-accepted | gains |
|---|---:|---:|---:|---:|
| B + S1 + S2 | 3,940 | 0 | 0 | 0 |
| R (re-slot) | 1,620 | 0 | 0 | 0 |
| relax (identity + S1 + R) | 1,171 | — | 0 | 0 |

**Result: refusal.** No cell in the declared space is feasible even at
`eps = 1e-6`, and no settled state is accepted by the exact gate below the
delivered side.

## 7. Instrument controls (without these the refusal means nothing)

| control | expectation | outcome |
|---|---|---|
| identity at `L0` | feasible | **feasible** |
| identity at `L0 − eps`, bisected | row 18 is jammed to some tight value | **max declared shrink 3.0898e−8** |
| loose 2×2 grid of 4 squares at side 2.2, asked to shrink to 2.05 | feasible and gated | **feasible, gate ok, pen −0.05** |
| proved row n = 12 at side 3.99 | refused | **refused** (`s(12) = 4`) |

So the machinery does certify a shrink when one exists, does refuse a proved
optimum, and the row itself is rigid to 3e−8 under its own contact axes: nothing
that keeps row 18's contact structure can shrink it at all, which is why every
reassignment — not merely most — comes back infeasible.

## 8. What this does and does not establish

Established: the wall margin is defined, computed for all 1000 rows, and n = 184,
656, 819 are ordinary mid-table rows at the grid, while the largest margins and
the largest `rho` are dominated by rows the record calls proved; and row 18
admits no improvement over 5,560 declared cells with the exact gate as judge.

Not established: impossibility. The LP needs a declared separating axis per pair
and refusals are conservative there; a global rearrangement with a *different*
contact graph is outside this cell space. The relax pass reduces that risk (it
declares nothing) but a 1,200-move settle from a re-worded delivered state is not
an exhaustive global search. Nothing about rows above n = 324 changes: they
remain open for want of a source.

## 9. Re-running

    python3 scripts/wall_margin.py                  # 1000 rows, mu/rho/held/value
    python3 scripts/branch_rot.py                   # controls + 5,560 declared cells
    python3 scripts/branch_rot.py --relax-only      # controls + 1,171 settled cells
    python3 scripts/sqscore.py                      # score guard: 22.218056945
    python3 scripts/record_guard.py                 # no stale total as current

Ledgers: `workspace/push/wall_margin.json` (schema `wallmargin/1`) and
`workspace/push/branch_rot.json` (schema `branchrot/1`, including every cell's
verdict). Neither writes to the submission.
