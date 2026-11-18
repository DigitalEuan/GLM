# 29 — The §11.5 probe, and the resolution/dithering question (runs 65–66)

Two follow-ups from `19` §11. Both are measured; neither moves the score.

---

# Part A — the bounded experiment of §11.5 (run 65)

## A.1 What was run

`19` §11.5 proposed: fix the side just below the delivered `L`, free only k
squares, seed with the delivered tight-pair axis assignment, and demand a
certificate. With the orientations frozen and each pair's axis taken from the
delivered state, the model is **exactly a linear program** in the free
translations — the same declared-axis LP as `seam_wheels.lp_seam`, widened from
one seam translation to k free squares:

    for each pair with the delivered axis q and sign s:
        s·((c_j + D_j − c_i − D_i)·q) ≥ h_i(q) + h_j(q)
    containment: |x_i + D_i| + h_i ≤ L/2,  |y_i + D_i| + h_i ≤ L/2

because q and both h are constants once θ is frozen. `scripts/sat_probe.py`,
ledger `sat_probe/1`.

Targets: the six rows in n = 20..300 with the most **area slack** `L² − n` —
295, 298, 299, 294, 297, 300 — because a shrink is most plausible where the
cell is emptiest. Free sets: the k squares whose walls are binding (largest
`|x| + h`), for k ∈ {8, 12, 20}. ε ∈ {1e−6, 1e−4, 1e−2}.

**One bug, recorded.** The first run put the global translation into the pair
constraints, where it cancels between the two squares of a pair; every cell came
back infeasible for that reason alone. Fixed, and a diagnostic added so the
refusal is explained rather than merely reported.

> **Erratum (run 67).** The LP used here had three defects — pair-row sign order,
> inequality direction, and the separation constant (`h_i + h_j` instead of
> `0.5 + Eu[owner, other]`). The delivered state was infeasible *at its own side*,
> which is how it was caught. The 18 `rigid core spans` refusals below are computed
> outside the LP and still hold, but the free set was chosen so they had to: see
> `30`, which earns the refusal by growing k from the extreme achievers. The LP
> reasoning in A.1–A.3 is withdrawn and superseded by `30`.

## A.2 Result: 18 cells, 0 feasible — and the reason is structural

| | |
|---|---|
| cells solved | **18** (6 rows × 3 free-sets) |
| feasible at any ε ≥ 1e−6 | **0** |
| gains | **0** |

Every cell refuses for the same measured reason, reported by the diagnostic as
`rigid core spans`: after removing the k boundary squares, the remaining frozen
set **still spans the full side** in at least one axis — it reaches
`≥ L − 1e−6` on its own. So no amount of motion by the k free squares can lower
the side, because the side is not set by them.

That is the same fact as `L7`: **the walls, not the contact graph, pin these
packings.** A row's side is typically achieved by many wall-touching squares
(and tilted squares, whose bounding box is `½(|cos θ| + |sin θ|)` per side), not
by a handful of boundary pieces a small neighbourhood could release.

## A.3 What this refusal does and does not say

* **Says:** with k ≤ 20 free squares and the delivered axis assignment, no row in
  the slack-heaviest band can be shrunk by even 1e−6. This is a *feasibility*
  result for a declared LP, so it is a certificate, not a heuristic failure.
* **Does not say:** that a *different* axis assignment, or a rearrangement of the
  rigid core, cannot shrink a row. The declaration is the conservative edge —
  exactly the same caveat `21` §9 records for `lp_seam`.
* **Follow-up implied by A.2:** the right neighbourhood is not "k boundary
  squares" but "the set that achieves the extreme in x and y, *and* the squares
  sharing its axes" — i.e. a whole wall. Doing that is `diamond_mask`'s grammar
  over the wall, which already returned 0 gains.

---

# Part B — resolution reduction / dithering (run 66)

## B.1 The proposal, restated

Solve at a coarse "resolution" — a lattice of admissible placements, pixel-style
— then refine back to full precision, in the way one renders a low-res image and
upsamples. The hope is that the coarse problem is small enough to solve globally
and its solution is a guide.

## B.2 The decisive test: can a coarse lattice even *hold* the answer?

`scripts/resolution_probe.py` takes ten delivered rows (n = 10, 25, 50, 83, 100,
150, 200, 290, 500, 1000) — i.e. the *answers* — and snaps their centres to the
`1/m` lattice (and, separately, their angles to multiples of `π/(4m)`). If the
exact solution cannot be represented at resolution m, no search at resolution m
could have found it.

| m | θ snapped | rows invalid (of 10) | total loss | vs gap 0.1636 |
| ---: | --- | ---: | ---: | --- |
| 2 | no | 6 | −0.1606 | within |
| 2 | yes | 6 | −0.1643 | **exceeds** |
| 4 | no | 7 | −0.2088 | **exceeds** |
| 4 | yes | 7 | −0.2229 | **exceeds** |
| 8 | no | 6 | −0.0570 | within |
| 16 | no | 6 | −0.0184 | within |
| 32 | no | 7 | −0.0238 | within |
| 64 | no | 6 | −0.0058 | within |
| 128 | no | 7 | −0.0050 | within |

Two results, and the first is the important one:

1. **The snapped packing is invalid at every resolution, including m = 128.**
   Six or seven of ten rows fail `packlib.verify` with `pen > 0` at *every* m.
   The cause is structural: at a delivered optimum every load-bearing contact has
   penetration **exactly 0**, so any displacement at all — of size `≤ 1/(2m)`,
   however fine — opens a violation on some other pair. Contacts are equalities,
   and equalities have no neighbourhood.
2. The *side* cost of snapping is genuinely small once m ≥ 32 (0.005 over ten
   rows at m = 128), which is why the naive metrics look encouraging. It is
   irrelevant: a single `pen > 0` invalidates the packing, and the gate is binary.

## B.3 Why dithering specifically does not transfer

Dithering works because a display has an *admissible residual*: the eye averages
quantisation error, and error diffusion keeps the local mean. The packing problem
has no admissible residual — `pen ≤ 0` is a hard constraint, not a tolerance. Any
error-diffused overlap is an invalid packing, and there is no averaging that makes
`pen = +1e-4` acceptable. Error diffusion needs a continuous tolerance; here there
is none. (The float/scan layer of the ladder, rung 1, is the only place a tolerance
exists at all, and it is below 2.5e-13.)

## B.4 What the existing material already says about resolution

The escalation material does bear on this, and it says the same thing three ways:

* **Rung 3 of the ladder** (`28` §1) is a *resolution sweep*: the Λ₂₄ predicate was
  tested at eight scales, and tilted rows were illegal at **every** scale — 87/87
  — while untilted rows were legal somewhere, 168/168. Coarsening never created the
  structure.
* **`L3`** ("quantisation destroys exactly the structure that pays") is the general
  form: the score is carried by the √2 word, and √2 is not a lattice point at any
  scale.
* **`L1`** removes the search incentive even if representation worked: the feasible
  set at a fixed side has `E = 0` exactly, so a coarse objective is flat across
  solutions and cannot rank them.

## B.5 Where a coarse-to-fine idea *could* still be sound

One version is not refuted by the above, and it is worth stating precisely: coarsen
the **combinatorial** variable rather than the geometry — i.e. solve a coarse problem
whose variables are *which pairs are tight and on which axis* (the branch
assignment), then lift to a full-precision LP with that assignment fixed. That is
exactly `seam_wheels.lp_seam` generalised, and Part A shows what it returns when the
neighbourhood is small. The geometric coarsening — positions and angles on a
lattice — is the part that B.2 kills.

---

# Files

* `scripts/sat_probe.py` — declared-axis feasibility LP at fixed side, `satprobe/1`.
* `workspace/push/sat_probe.json` — 18 cells, 0 feasible, with the rigid-core span.
* `scripts/resolution_probe.py` — lattice snapping at 7 resolutions, `resolution/1`.
* `workspace/push/resolution_probe.json` — the table above, per row.
* follows `19` §11.5 (Part A) and answers the resolution question (Part B).
