# 81 — Time-budgeted rows, and whether this line can reach 990 cells (run 122)

`sq_cli.py row` now reports best effort inside a wall-clock budget instead of burning the budget and saying
nothing (§1). Then the honest strategic question: **no — this line cannot realistically reach the ~990-cell
unbeaten rows, and it should not be scaled** (§2–§4). Read-only: no row changed, no score moved.

## 1. A time budget that still reports

`settle(..., progress=PATH)` checkpoints the **deepest placement reached so far** to `PATH` whenever it
improves (and on success), writing each cell exactly as `[x_a, x_b, y_a, y_b, c_a, c_b, s_a, s_b, dir, i]`
meaning `a + b sqrt d`. `sq_cli.py row` runs the settler in a child process with `--seconds`, kills it at the
deadline and **reloads the checkpoint**, so a timed-out probe still yields a gated partial pose, its exact span,
its overlap count, and a verdict.

Measured round trip: n = 5 at `2 + 1/2 sqrt2` reloads from its checkpoint as 5 cells, span exactly
`2 + 1/2 sqrt2`, **0 overlaps**, nodes 69 / states 87 — identical to the live run.

| row | budget | best effort | partial span | overlaps | anchors still available | verdict |
|---|---|---|---|---|---|---|
| n = 12, k = 4 | 45 s | **8/12** | exactly 4 | 0 | **73** | time budget, not exhaustion |
| **n = 23, k = 5** | **150 s** | **11/23** | exactly 5 | 0 | **129** | time budget, not exhaustion |
| n = 23, tabula rasa (run 121) | 900 s | *nothing reported* | — | — | — | now fixed |

Both stalls are **budget/order limits**, not exhaustion and not a missing command: the generator still offers
73 and 129 determined anchors at the deepest state. That distinction is only observable *because* the partial
progress is reported — the run-121 probe destroyed exactly this evidence.

## 2. The cost model, from measured runs

Candidates per node scale with the placed count squared (every parent pair is tested, every candidate sweeps
its contacts), so time per node scales the same way. Measured, generator `closure`, width 8:

| placed d | nodes | seconds | pairs tested | pairs/node | s/node |
|---|---|---|---|---|---|
| 4 | 5 | 0.31 | 47 | 9 | 0.06 |
| 5 | 69 | 31.2 | 12 096 | 175 | 0.45 |
| 6 | 17 | 8.75 | 4 584 | 270 | 0.52 |
| 7 | 128 | 102.6 | 48 768 | 381 | 0.80 |

`pairs/node ~ 7 d^2` (fit at d = 5, predicts 343 at d = 7 against 381 measured) and throughput ~388 pairs/s.
Extrapolating, for a **single** chain that never backtracks (1 node per cell):

| d | seconds per node | minimum wall clock for the chain |
|---|---|---|
| 12 | 2.6 | 31 s |
| 23 | 9.6 | 3.7 min |
| 100 | 181 | 5.0 h |
| **990** | **17 696** | **4 866 h ≈ 203 days** |

That is the *floor*: no refusals, no backtracking, no width. The measured runs are 3–18 nodes per cell, not 1,
so the true figure for a 990-cell row is worse by another factor of 3–18 — and this is for **one** row of the
447. Even the 100-cell rows, which are not the target, cost half a day each.

## 3. And even if it finished, it would not score

The second, more damning problem is not speed:

* Every settlement so far lands **exactly on its target span** (n = 4 -> 2, n = 6 -> 3, n = 7 -> 3,
  n = 5 -> `2 + 1/2 sqrt2`). The grammar builds closed configurations: every anchor sits at an exact wall or
  tangency, so the pose is lattice-locked at the side it was aimed at.
* The unbeaten rows we would aim it at are **1.5e-9 to 1.6e-9 above the grid side** already
  (n = 12: 4.0000000015 against 4; n = 23: 5.0000000016 against 5). Reproducing the grid there is worth
  **1e-9 per row**.
* The score needs **4e-3 to 1e-2** of improvement per row (the legal-gap band is 6.2e-5 to 3.3e-4, the 1 % capture
  is 0.15023). A closure at the grid side is **six orders of magnitude** short of mattering.

So the anchor line is not a scoring instrument for these rows at any speed. It is a **certifier**: it proves a
pose is exact and overlap-free, which is what C1–C4 demand of a *candidate that something else has to find*.

## 4. What to do instead

* **Keep** `anchor_chain` and `sq_cli.py verify` as the certification path — that is real, cheap value: any
  future candidate gets an exact span, an exact overlap certificate and a refusal control in one command.
* **Do not scale** the settler past roughly 12–16 cells. Above that the budget buys partial poses that carry no
  evidence, and the width limit (8) would decide the outcome anyway.
* **Spend the search effort where the cost per row is seconds, not hours**: the existing
  `polish_pricing` / `resqueeze` family already runs 12 rows in the time one 23-cell probe burns. Its ceiling
  was measured at **0.00000** on 12/12 sampled rows (run 117), which means the *current move set* is exhausted —
  so the next test is not more of the same, it is a **new non-closure perturbation** (free positions with slack
  ~1e-6 rather than exact contacts), scored per row by measured dL.
* **Cheapest honest next step**: run that per-row route on 20 of the 447 unbeaten rows with a 10 s budget each
  (~4 min total), and report the measured dL distribution. If the median is below the legal-gap band, the route
  is dead and worth saying so; if a tail appears, that tail is what to scale.

## 5. Checks

| check | result |
|---|---|
| `settle(..., progress=)` round trip | n = 5 reloads to 5 cells, span `2 + 1/2 sqrt2`, 0 overlaps, 69 nodes / 87 states |
| `sq_cli.py row 12 --seconds 45` | 8/12, span 4, 0 overlaps, 73 anchors available |
| `sq_cli.py row 23 --seconds 150` | 11/23, span 5, 0 overlaps, 129 anchors available |
| `sq_cli.py verify 10`, `sq_cli.py audit` | 10 anchors / 0 overlaps; 0 float offenders |
| `anchor_chain --selftest`, `sqscore`, `record_guard`, `void_insert --selftest` | green |
| `glm_wheels --audit` | **657 functions, 0 offenders**; `anchor_chain` 44, none naming float |
| `submission.csv`, `WHITEBOARD.md` | untouched |
