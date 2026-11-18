# 34 — The queued action: a flip plus free-set expansion, on a seed that is not there (Run 71)

Run 70 ran the T1 branch flip with every translation free and the free set fixed
at the delivered tight pairs, at three rows. `33` §7 queued the one cell of the
card it never entered: **a flip combined with free-set expansion, on a seed whose
LP is not already rigid at `L0`**. This is that run, and its answer is that the
seed does not exist in the delivered table: the action cannot be run as written,
and the refusal is exhaustive over the declared ladder rather than a sample.

No row of the table changed. The delivered total is still `22.218056945`, 553
beats, and `sqscore.guard()` holds.

## 1. The action, restated

* seed — a row and a declared flip whose constraint system has room at `L0`;
* flip — one contact edge changed from its `argmin` branch to one of the three
  alternatives (`u_i`, `v_i`, `u_j`, `v_j`), every other branch delivered;
* free-set expansion — the repair grows from the flipped pair outward along the
  contact graph (pair → 1-ring → 2-ring → all), so that the *smallest* sufficient
  repair is found rather than assumed;
* judge — `declp.gate`: 12-dp state, `packlib.verify(tol=0)`, `sqscore.row_gain`.
  LP feasibility is recorded as `lp` and never as a result.

## 2. What "slack" is, and what it is not

The wall margin `mu = L − sqrt(n)` is **not** slack: it is the distance to the area
wall, and a row can have a large `mu` and still be pinned. Run 69's own figures say
so (n = 18 has `mu` rank 2 of 1000 and rigidity 3.1e−8). Three things were
therefore measured separately:

| measure | what it is | how it was taken |
|---|---|---|
| **base depth** | largest `eps` with `solve(L0 − eps)` feasible on the delivered branches | the declared ladder, smallest step first |
| **flip depth** | the same after one declared flip | the seed test; `1e−6` in the run, `1e−7` and `1e−8` in the probes below |
| **pad slack** | largest `pad` with `solve(L0, pad)` feasible — interior room in the contact system | bisection; a pad demands *more* separation in the same box, a shrink demands the same separations in a smaller box, so these are related but not equivalent |

## 3. The search

Order: the wall-margin ranking, largest `mu` first — the rows with the most nominal
room. Population: **every open row at n = 4–60**, 42 rows (15 of the 57 are among
the 156 proved rows and are excluded, since a refusal there would only re-derive a
proof). Cell space per row: every contact edge incident to an extreme achiever,
each of its three alternative branches.

## 4. Result

**42 rows, 2,228 contact edges at extreme achievers, 6,684 declared flips.**

| | value |
|---|---|
| rows | 42 (n = 4–60, all open) |
| base depth | **0 at every row** — nothing admits a 1e−6 contraction |
| flips tested | 6,684 |
| seeds at `L0 − 1e−6` | **0** |
| ladder cells entered | 0 |
| gate-accepted | 0 |
| gains | **0** |

The ledger is `workspace/push/flipgrow.json` (schema `flipgrow/1`), one record per
row with `mu`, its wall-margin rank, contacts, edges, base depth, base pad, flip
count, seeds and gains.

The fine probes, on the top rows, locate the boundary precisely:

| seed test | rows | flips | seeds | cells | gated |
|---|---:|---:|---:|---:|---:|
| `L0 − 1e−6` | 42 | 6,684 | 0 | 0 | 0 |
| `L0 − 1e−7` | 5 | 423 | 0 | 0 | 0 |
| `L0 − 1e−8` | 2 (n = 18, 11) | 78 | **20** | 400 | **0** |

At 1e−8 the LP starts admitting flips — that is the solver's own scale (run 69's
base rigidity is 3.1e−8), not geometry — and the ladder does enter 400 cells and
the gate refuses **every one**. That is the clearest statement in the run of why
the gate, and not the LP, is the judge.

## 5. Why: the frame is over-determined

Counting binding constraints against degrees of freedom, for every row 4–120
(`flipgrow.py --census`, ledger `flipgrow_census.json`):

| n | variables | contacts | walls | binding | binding − 2n |
|---:|---:|---:|---:|---:|---:|
| 5 | 10 | 4 | 8 | 12 | **+2** |
| 11 | 22 | 14 | 11 | 25 | +3 |
| 18 | 36 | 26 | 14 | 40 | +4 |
| 20 | 40 | 55 | 18 | 73 | +33 |
| 39 | 78 | 68 | 24 | 92 | +14 |
| 60 | 120 | 195 | 27 | 222 | +102 |
| 100 | 200 | 342 | 40 | 382 | +182 |

**Every row 4–120 has more binding constraints than the 2n variables that could
move.** The least over-determined row in the table is n = 5, over by 2. So a flip
— which relaxes exactly one pair's separation and adds none — leaves the framework
over-determined, and the measurement agrees with the count to 1e−6. This is the
structural content of "jammed": the rows are not slack that a flip could spend,
they are pinned with spare constraints.

The census is a pointer, not a proof (rows can be redundant and rank matters);
the LP is what decides, and it decided the same way on 6,684 cells.

## 6. Why the refusal is exhaustive, and exactly where the window is

Two monotonicities do the work:

1. **In the free set.** Any solution on a subset of variables is a solution on all
   of them, so feasibility is monotone increasing in the free set. Testing at
   "all free" is therefore the *strongest* form of the test, and the ladder
   (pair → rings → all) can only find a smaller sufficient repair, never more
   room. That is why free-set expansion cannot rescue a flip that "all free"
   refuses — the expansion is a search for the minimal repair, and there is no
   repair to minimise.
2. **In `eps`.** `L0 − eps` is feasible only for `eps` below the row's own
   remaining rigidity, so a refusal at a given `eps` refuses every *larger*
   `eps`. The seed test is therefore taken at the smallest declared step and the
   ladder above it is covered by the same call.

What is **not** covered: contractions below 1e−6. The declared ladder stops there,
and a gain from a 1e−7 contraction would still be above the gate's 1e−9
resolution, so that window was probed separately (§4): at 1e−7 nothing is
feasible; at 1e−8 the LP is permissive and the gate refuses. Nothing in the window
between 1e−8 and 1e−6 is both LP-feasible and gate-accepted.

## 7. Controls

A test that only refuses is not evidence. `flipgrow.py --control`:

| control | expectation | outcome |
|---|---|---|
| loose 2×2 grid at side 2.2 | base depth 1e−2 | **1e−2** |
| the same grid, one contact edge flipped onto each alternative branch at `L0 − 1e−6` | the seed test fires and the gate accepts | **1 of 3 branches seeds and gates** |
| two unit squares at their exact optimum, side 2.0 | base and every flip refused | **base refused, every flip refused** |

So the seed test, the ladder and the gate all fire when the geometry allows, and
refuse at a tight optimum; the 6,684 refusals are refusals of the rows.

## 8. What is still open

Closed by this run:

* single-flip cells with free-set expansion at any open row n ≤ 60, over the
  declared ladder — refuted, exhaustively by the monotonicity in §6;
* the queued action itself, as specified in `33` §7 — it has no seed.

Still open, and honestly distinct:

* **two or more flips.** Run 70's `flip2` was capped and only run at three rows;
  a two-flip cell is outside this run's declaration.
* **a new contact.** A flip may only reassign an *existing* contact edge; "a
  non-contact pair becomes the separating one" is outside the cell space (the
  run-70 limit, unchanged).
* **rows above 60.** The LP is built over all pairs, so n = 1000 is out of reach
  here; the census says those rows are *more* over-determined, not less.
* **the 675 rows above n = 324** with no catalogue source: a different problem.
* **a slack-positive row**, if one is ever constructed by a different method
  (a seed from outside the table, not a repair of it). The instrument is now
  built and controlled for that case: `flipgrow.py <n>` will seed, expand and
  gate it.

## 9. Re-running

    python3 scripts/flipgrow.py --census          # binding constraints vs 2n, n <= 120
    python3 scripts/flipgrow.py --control         # both directions of the seed test
    python3 scripts/flipgrow.py                   # 42 rows, 6,684 flips (~110 s)
    python3 scripts/flipgrow.py 18 39             # named rows
    python3 scripts/flipgrow.py --seed-eps 1e-8 18 11   # the fine probe (~3 s)
    python3 scripts/declp.py --selftest           # 6/6, the shared LP
    python3 scripts/sqscore.py                    # 22.218056945
    python3 scripts/record_guard.py               # no stale total as current

Ledgers: `workspace/push/flipgrow.json` (the run) and
`workspace/push/flipgrow_census.json` (the count). Neither writes the submission.
