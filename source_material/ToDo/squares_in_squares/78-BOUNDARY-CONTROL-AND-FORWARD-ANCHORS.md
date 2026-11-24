# 78 — The boundary-only control, the Q(sqrt 7) row, and a forward settler (run 118)

Closing two open items from doc 77: the methodological caveat in §3 (the polish ceiling was
measured with the *worst-case* clamp), and §5 (the anchor grammar could only describe a
finished pose). Read-only: no row changed, no score moved, `submission.csv` and root
`WHITEBOARD.md` untouched. Instruments: `scripts/polish_ceiling.py --control boundary`,
`scripts/anchor_chain.py --forward`; records `polish_ceiling117_boundary.json`,
`anchor_chain118.json`, `anchor_forward118.json`.

## 1. The loophole, and the control that closes it

Doc 77 §3 measured the polish ceiling by shrinking a row's container and clamping **every**
cell into the smaller box — the worst case for a zero-clearance pose, since every tight pair
breaks at once. The honest objection is that the ceiling of `0.00000` might be an artefact of
that initialisation.

`--control boundary` changes exactly one thing: it shrinks the box by the same `delta` and
translates **only** the cells whose bounding box now crosses a wall, each by its exact minimal
amount, leaving every interior cell untouched. Then the identical contact-graph repair runs and
`true_geom` judges at 40 digits. Same 12 stratified rows, same three `delta`s:

| n | k | capture e | boundary δ=3e-5 | δ=1e-4 | δ=3.3e-4 | boundary ceiling | whole-box ceiling |
|---|---|---|---|---|---|---|---|
| 655 | 26 | 0.001 | 88 | 88 | 88 | **0.00000** | 0.00000 |
| 507 | 23 | 0.062 | 119 | 119 | 119 | **0.00000** | 0.00000 |
| 270 | 17 | 0.126 | 68 | 68 | 68 | **0.00000** | 0.00000 |
| 417 | 21 | 0.178 | 75 | 75 | 73 | **0.00000** | 0.00000 |
| 337 | 19 | 0.220 | 69 | 69 | 69 | **0.00000** | 0.00000 |
| 985 | 32 | 0.252 | 123 | 123 | 123 | **0.00000** | 0.00000 |
| 590 | 25 | 0.287 | 141 | 141 | 141 | **0.00000** | 0.00000 |
| 917 | 31 | 0.326 | 180 | 182 | 182 | **0.00000** | 0.00000 |
| 449 | 22 | 0.361 | 84 | 84 | 84 | **0.00000** | 0.00000 |
| 584 | 25 | 0.387 | 99 | 99 | 99 | **0.00000** | 0.00000 |
| 968 | 32 | 0.436 | 126 | 126 | 126 | **0.00000** | 0.00000 |
| 904 | 31 | 0.468 | 123 | 123 | 123 | **0.00000** | 0.00000 |

**Result: 12 of 12 rows, ceiling `0.00000`, at every `delta`.** The gentlest initialisation
available to this move set fails at `delta = 3e-5` on every sampled row, with tens of violations
at 40 digits and the repair stalling after one or two passes. **Local polish is closed.** The
ceiling is not a property of the clamp; it is a property of the poses (zero clearance, no slack
to trade) and of a move set made of single-cell slides.

## 2. The Q(sqrt 7) row: n = 18 as an admitted chain

The command grammar is field-independent: the same three commands and the same two gates,
pointed at a different real quadratic field.

* **Field.** Q(sqrt 7). Directions: `axis`, and the Ring word `((1+sqrt7)/4, (sqrt7-1)/4)` —
  cos 24.295189° = 0.9114378278, sin = 0.4114378278, unit exactly on the circle.
* **Coordinates.** `(a + b sqrt7)/q` with `q` up to 32, read from the delivered decimals: e.g.
  `(-5 - sqrt7)/4 = -1.9114378278`, `(-9 - 3 sqrt7)/16 = -1.0585783703`,
  `(50 - 22 sqrt7)/32 = -0.2564540255`. Worst read **1.79e-9** (the finalizer pad).
* **Chain.** 18/18 anchors admitted: **4 ANCHOR_CORNER, 6 PROPAGATE_SLIDE, 8 STACK_BLOCK**;
  `step_check` and `chain_check` green on the whole chain.
* **Side, exactly:** **`7/2 + 1/2 sqrt7`** (= 4.822875655532…), zero overlaps, and the columns
  are native to the planner: `Step 5: PROPAGATE_SLIDE places cell 1 (axis) is given as 5.` /
  `s5 = PROPAGATE_SLIDE#1 = 5 (given)`.

So the grammar generalises: a second field, a second direction word, the same commands, the same
gate. The only thing that changed between n = 10 and n = 18 was the field object.

## 3. The forward settler: re-tested without caps, then completed

**The claim re-tested, and corrected.** The first version of this section said the n = 5 search was
"exhausted at 221 nodes". That run had a per-node candidate truncation (`[:12]`) and a node cap, so the
claim was not yet genuine. Re-run with **no per-node candidate cap and no node limit** — only a
state-deduping `seen` set, so permutations of the same placement collapse:

| generator | result | nodes | states | exhausted |
|---|---|---|---|---|
| frontier (one-parent), no caps | **4/5** | **69** | **68** | **yes — stack emptied** |

The claim **holds** — the one-parent state space closes at four cells — and the **count is corrected**
from 221 to **69 nodes / 68 states**. (The 221 came from the capped bookkeeping; it was not a measured
closure.)

**The two changes that were missing.** A direct diagnostic showed the generator *does* produce the
optimal fifth cell from the optimal four corner cells; the search simply never reached that state.

1. **Two-parent STACK_BLOCK.** Two tangency equations are two *linear* equations in the centre, so the
   candidate is **solved exactly** — a 2x2 solve in Q(sqrt 2) — over the axis pairs of both parents
   **and of the candidate itself** (the 45 degree cell touches two axis cells along *its* axis, not
   theirs). This is the command doc 78 §3 predicted.
2. **ANCHOR_CORNER at every depth.** A regression of the rewrite: corners were offered only at depth 0,
   so the four-corner state was unreachable and every branch died at depth 1.

A third candidate algorithm was tried and **abandoned as wrong**: enumerating the field lattice
(a/4 + (b/4)sqrt2 in both coordinates) as free offsets. It is not a sparse lattice — there are ~10 000
field points within radius 3/2 — so it is both slow (65 s for 19 nodes) and not the right shape of
search. Solving the constraints is.

**Result:**

| target | result | exact span | nodes / states |
|---|---|---|---|
| n = 4 at L = 2 | **4/4** | `2` | 9 / 14 |
| n = 5 at `2 + 1/2 sqrt2` — frontier, no caps | 4/5 (exhausted) | — | 69 / 68 |
| n = 5 at `2 + 1/2 sqrt2` — two-parent closure | **5/5** | **`2 + 1/2 sqrt2`** | 248 / 260 |

The settled pose is the known optimum: four axis cells in the corners and one diagonal cell at
`(1 + 1/4 sqrt2, 1 + 1/4 sqrt2)`, all admitted at clearance >= 0 with exact refusals on the way.

**Verdict.** The grammar now **settles the proved 5-cell optimum exactly**, so the constructor is
complete at least through n = 5 and the "missing command" diagnosis was right. complete at least through n = 5 and the "missing command" diagnosis was right. n = 212 at L = 15 is
still only a **budget-limited probe**: at a node cap of 25 the frontier settler places **25 cells
spanning the full 15** and the search has *not* terminated — so it is neither a success nor an
impossibility. (The earlier "14 cells in a 5.5-wide corner" came from pre-fix parameters and is
**withdrawn**.)

## 4. Checks

| check | result |
|---|---|
| `anchor_chain.py --selftest` | n=10 side `3 + 1/2 sqrt2`, n=18 side `7/2 + 1/2 sqrt7`, 28/28 anchors, refusal at exact slack `-1/4` |
| `anchor_chain.py` | both JSONs written, `chain_check` green, 0 overlaps |
| `anchor_chain.py --forward --small` | n=4 target reached; n=5 stalls at 4/5 (DFS exhausted) |
| `polish_ceiling.py --control boundary` | 12 rows, ceilings all `0.00000`, extrapolated `+0.00000` |
| `glm_wheels.py --audit` | **646 decision functions, 0 offenders**; `anchor_chain` 33, none naming float |
| `sqscore.py`, `record_guard.py`, `void_insert.py --selftest` | re-run green |
| `submission.csv`, `WHITEBOARD.md` | untouched |
