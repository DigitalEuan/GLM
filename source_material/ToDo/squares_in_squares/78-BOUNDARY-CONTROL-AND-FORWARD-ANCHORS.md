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

## 3. The forward settler: from transcript to constructor

`settle(n, L, field)` runs the grammar **forwards** at a target side. At each node it generates
the anchors the three commands can *determine* — a corner closed by two walls, or a cell
tangent to the frontier cell and closed by a wall or a second contact, sliding on the exact
lattice — admits a candidate only when `step_check` and the exact placement gate pass at
clearance `>= 0`, and backtracks when a move is refused. Every comparison is in Q(sqrt d); there
is no float anywhere in the search.

| target | result | verdict |
|---|---|---|
| **n = 4 at L = 2** (proved optimum) | **4/4 settled**, exact span `2`, 0 refusals | the grammar constructs |
| **n = 5 at L = 2 + 1/2 sqrt2** (proved optimum) | **4/5**, then "no determined anchor at clearance >= 0" | **structural: the DFS is exhausted at 221 nodes**, not a budget cap |
| **n = 212 at L = 15** (Block45 regime, +0.0711) | 14/212 in a node-capped probe, span `11/2` of 15 | no answer within budget; the tree is too large |

**Why n = 5 fails, exactly.** The settler exhausts its whole tree (221 nodes, well under the
600-node cap) without reaching 5 cells. The generator closes a new cell only against the
**frontier** cell; the optimal fifth cell is the tilted one that closes against two *non-frontier*
axis cells. So the missing command is precise: **STACK_BLOCK on two independent placed cells**,
not on one. The grammar as built is a constructor for corner-and-stack settlements, and it is
provably unable to reach the proved 5-cell optimum — which is a fact about the move set, not
about `s(5)`.

**n = 212.** At L = 15 with axis + diagonal directions the settler fills a 5.5-wide corner with 14
cells and the determined-anchor frontier dies there; the unrestricted search did not terminate
within 900 s, so this is reported as **no answer within budget**, not as an impossibility. What it
does show is the shape of the obstruction the run-115 families priced: forward anchor settling
does not tile.

**Verdict.** The anchor chain is a verified transcript (exact, per-step, refusable) and now a
*partial* constructor: it settles small corner-and-stack targets exactly, and its failure at n = 5
localises the missing command to two-parent closure. To settle at the scale of the 447 grid rows,
that command has to be added and the search has to be ordered (best-first on closed contacts
rather than DFS), or the settler stays a small-target device.

## 4. Checks

| check | result |
|---|---|
| `anchor_chain.py --selftest` | n=10 side `3 + 1/2 sqrt2`, n=18 side `7/2 + 1/2 sqrt7`, 28/28 anchors, refusal at exact slack `-1/4` |
| `anchor_chain.py` | both JSONs written, `chain_check` green, 0 overlaps |
| `anchor_chain.py --forward --small` | n=4 target reached; n=5 stalls at 4/5 (DFS exhausted) |
| `polish_ceiling.py --control boundary` | 12 rows, ceilings all `0.00000`, extrapolated `+0.00000` |
| `glm_wheels.py --audit` | **643 decision functions, 0 offenders**; `anchor_chain` 30, none naming float |
| `sqscore.py`, `record_guard.py`, `void_insert.py --selftest` | re-run green |
| `submission.csv`, `WHITEBOARD.md` | untouched |
