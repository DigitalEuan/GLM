# 68 — depth-two chains, a coupled multi-cell repair, and two Lean contracts (run 107)

Run 106 certified 552 of the 553 exact rows and left two questions: whether a certified sentence
is jammed at *depth one* (doc 66 §7's two-cell trade), and whether n = 330's three coupled
overlaps can be cleared by moving several cells at once (doc 67 §§2–3). This run answers both
with one instrument, `scripts/observer_chain.py` (6 controls, float-free, in the audit list), and
the first thing it does is **correct the instrument that answered the first question last time**.

The two contracts are used as structure, never as authority, and each is re-computed exactly in
Python from the Lean file's own data:

| contract | Lean source | what this run computes |
|---|---|---|
| `readCost d t = 1/(t + d/t)` | `ObserverY.lean`, `readCost`, `readCost_le_amgm` | exact over `Q`; ceiling `1/(2√2) = √2/4` as a field element |
| `taxMOG = bitTax + syndromePenalty` | `ObserverY.lean` §14 A, `syndromePenalty_le` | `taxMOG/Q` = cells moved + `W`·violated pairs left, exact integers |
| syndrome diagnosis at weight ≤ 3 | `GolaySemantics.lean`, `violation_unique_of_wt_le_three` | the 24-cell syndrome rebuilt over GF(2) from its `Bmat`; injective at weights 1–3, 1771 colliding classes at weight 4 |

## 1. Erratum: run 106's "jammed at depth one" was an instrument artifact

`cand106.wall_room` caps a pair by the maximum over *narrowing* axes of `slack/|d.q|`, and breaks
to a cap of `0` as soon as a narrowing axis has negative slack. But a pair is legal while **some**
axis is separated, so a pair fails only when *every* axis is negative: an axis that is constant or
widening under the motion never fails, and an axis already negative constrains nothing. Control 1
pins the difference on an exact knight pair — cells at `(1/2, 1/2)` and `(3/2, 5/2)`, so `dx = 1`
and `dy = 2`, moving `+x`:

| rule | the pair's moving-axis rows | cap |
|---|---|---|
| run 106's `wall_room` | `(slack 0, rate −1)` twice | **0** (a block) |
| `room_set` (corrected) | same rows, but the axis with `d⋅q = 0` and slack `+1` is never entered | **unbounded** — the pair is separated along `y` and stays so |

The consequence is blunt: **run 106's part-3 verdict ("every one of 1216 and 2880 combinations has
`tau = 0`") is false**, because that rule zeroes the room of any partner whose neighbour merely
shares a projection. With the corrected rule, **all 90 of n = 66's inward probes and all 216 of
n = 325's have positive room** (§2). The *conclusion* of run 106 — no two-cell trade lowers L —
survives this run (§2), but for a different reason, and doc 67 §3 and the run-106 entry carry a
pointer to this section instead of the old claim.

## 2. Part 1 — the directed depth-two tracer

Both rows are reproduced from `cand106` and checked against run 106's certified sides before
anything is computed: n = 66 at `L = 4328427125631/500000000000`, n = 325 at
`L = 741421356313/40000000000`, both `verified`. The contact graph is the *tight* graph (SAT slack
exactly 0): **3** tight pairs at n = 66 and **1** at n = 325 — a certified sentence is a packing
with a contact, not a rigid body.

From each bounding-box wall cell and each inward direction, the tracer spends the cell's **corridor**
(the sum of its successive rooms, each one closing the next contact), then walks the chain
wall → tight blocker 1 → tight blocker 2 from the stalled state, pruning whenever a required
receding direction is itself a tight contact of an outside cell (`blocked_by`), and keeping a chain
only if two interior cells can hold it and every tight contact inside it survives the shear.

| | n = 66 | n = 325 |
|---|---|---|
| wall cells (per face `lo_x, hi_x, lo_y, hi_y`) | 30 (7, 8, 8, 7) | 72 (18, 18, 18, 18) |
| inward probes | 90 | 216 |
| probes with positive corridor | **90** | **216** |
| corridor range | `231/10^12` … `742640687523/10^12 − √2/2` = **0.035533** | `27/250000000000` … `80761184477/10^11 − √2/2` = **0.100500** |
| stalled states traced | 90 | 216 |
| two-cell chains with room > 0 | 68 | 144 |
| three-cell chains (wall + two interior) | 12 | **0** |
| pruned at blocker 2 (no receding room) | 4 | 0 |
| pruned by the shear condition | 558 | 1224 |
| **probes that shrink L** | **0** | **0** |
| gated at clearance 0 (`dL = 0` / `dL > 0`) | 5 (3 / 2) | 5 (3 / 2) |
| runtime | 23.87 s | 200 s |

So the sentences are *not* jammed — the corridors are real, up to `0.0355` and `0.1005` of free
travel inward — and yet **no single-cell and no two- or three-cell chain lowers the side**. The
reason is exact and visible in the second column: the bounding-box face is **multiply defined**
(7–8 cells per face at n = 66, 18 per face at n = 325). Moving one face cell inward leaves the face
where it is, because six or seventeen other cells still touch it, so the side cannot move until
*every* face cell moves. That is not a chain of two cells; it is a face slide of 7–18.

Both directions of the honest reading are recorded: depth one is **open** (contra run 106),
depth two is **closed** for the side (all 68 + 144 + 12 chains give `dL ≥ 0`, and the ten probes that were run through the gate certify
at clearance 0 — six with `dL = 0`, four with `dL > 0` between `231/10^12` and
`231/10^12 + 231/2·10^12·√2` — legal moves that leave the side or grow it, never shrink it).

## 3. Part 2 — the coupled multi-cell repair on n = 330's three-overlap cycle

Starting from run 106's four exact moves, n = 330 carries `L = 118003255389229/6312500000000` and
**three violated pairs, all disjoint**: `(184, 195)` with slack `−2 + 2828238908803/2·10^12·√2`,
`(216, 233)` with `−1/2 + 353548007689/10^12·√2`, and `(224, 247)` with
`−1/2 + 352353905641/10^12·√2`. (Doc 67 §2 named the last two and the common clearance; the first
is the pair cell 195's own diagonal step created, which is why the cluster is
`{184, 195, 216, 224, 233, 247}` and not the five cells doc 67 listed.)

**The MOG contract names the fault set.** Three simultaneous violations are inside the exact
diagnosis range (control 4: weights 1–3 map injectively to syndromes, weight 4 does not), so the
repair does not speculate: it targets the six named cells.

**Two cells cannot do it, and that is a counting fact.** The three violated pairs are disjoint, so a
hitting set needs one cell from each: **0** subsets of size 2 hit all three, **8** of size 3 do.
|S| = 2 is empty by construction, not by search.

**The 3-cell search is exhaustive.** 8 hitting sets × 8³ = 4096 joint motions, each step exact
(the clearing time of a violated pair is the last of its axes to leave the overlap, so the binding
pair lands exactly on contact):

| quantity | result |
|---|---|
| candidates | 4096 |
| clear all three named pairs at their exact clearing time | **4096** |
| leave **zero** violated pairs (the gate's own count) | **0** |
| minimum debt | **2** (3 candidates) |
| debt histogram | 2:3, 3:13, 4:90, 5:222, 6:404, 7:537, 8:531, 9:436, 10:491, 11:525, 12:481, 13:273, 14:59, 15:30, 16:1 |

The nearest candidate — cells `{184, 216, 224}` along `(−1,1)/√2`, `(−1,1)/√2` and `(1,1)/√2` by
`t = 1 − 40644125503/10^11·√2 = 0.425299…` — clears the three and breaks exactly two:

```
pair (170, 184): −2 + 278387009073/25·10^10·√2     (a 45 degree pair, 1.2e−10 of overlap)
pair (201, 216): −2 + 1115740420767/10^12·√2       (a 45 degree pair, 7.4e−11 of overlap)
```

and its side is unchanged (`dL = 0`). **n = 330 stays blocked**, and the obstruction is now exact
rather than generic: the three overlaps are not a defect of five neighbouring cells but of a
cluster embedded at the 45 degree word, and any joint motion large enough to clear them
(`t` in `0.42…1.46`) carries a cell into a *new* 45 degree neighbour two cells away.

The `taxMOG` ordering behaves as the contract says it should and is not by itself decisive: a
2-cell repair leaving one pair costs `2 + 1 = 3` units, exactly a 3-cell repair that clears all
three (`3 + 0 = 3`), so the tie must be — and is — broken by the gate, never by the tax. With the
2-cell branch empty, every surviving candidate scores `3 + debt ≥ 5`, and the minimum is **5**.

## 4. What is and is not claimed

**Established.** Run 106's `wall_room` pair rule is conservative and its "jammed at depth one"
verdict is an artifact; with the corrected rule 90/90 and 216/216 inward probes have positive room
(`231/10^12`–`0.0355` at n = 66, `27/2·10^11`–`0.1005` at n = 325). Neither certified sentence
loses any side to a single-cell move, a two-cell chain or a three-cell chain: 0 of 90, 0 of 68 and
0 of 12 at n = 66; 0 of 216, 0 of 144 and 0 of 0 at n = 325, with the multiply-defined faces as the
exact reason. n = 330's three disjoint overlaps cannot be hit by two cells (0 hitting sets) and
every one of the 4096 three-cell joint motions that clears them leaves at least two violations
elsewhere; the nearest leaves exactly two, with the exact slacks above. The three contracts are
re-computed exactly: `readCost(2,1) = readCost(2,2) = 1/3` against the ceiling `√2/4`, the
efficiency of every integer loop-check `2√2/3`, and the MOG syndrome injective at weights 1–3 and
colliding at 4.

**Not claimed.** Any improvement: no side moved on either row, no certificate with a smaller L
exists in either search space, and the four `dL > 0` probes are legal moves that *grow* the box by at
most `231/10^12 + 231/2·10^12·√2`.
That depth two is closed in general — it is closed for these two rows, in this chain model (wall →
two tight blockers), with the corridors spent first. That n = 330 is unrepairable — it is
unrepairable by 2 and 3 simultaneous cells of the named cluster; a face-scale or multi-step
strategy is a different search. `submission.csv` and the root `WHITEBOARD.md` are untouched: no
verified certificate achieved a strictly smaller side, so nothing there changes, and no score is
claimed.

**Next.** The measurement points at one concrete move the tracer cannot express: a **face slide** —
all 7–8 (n = 66) or 18 (n = 325) cells of a bounding-box face translated by a common `t`, which is
the only motion that can move a multiply-defined face. Its feasibility is the same exact interval
problem with 18 variables instead of one, and the corridor numbers above are its natural bound.
