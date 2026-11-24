# 77 — Stepwise anchors, and the measured polish ceiling (run 117)

Two questions from the Director's Note, answered by instrument rather than by argument:

1. **What is the real hard-projection polish ceiling?** Not "compare a 1 % capture with run 111's
   legal-gap band" — run the repair on the rows and see. Answer: **zero**, on every sampled row.
2. **Can a packing be written as the GLM's stepwise chain — anchors that become commands?** Yes, for
   reconstruction, and it is exact: n = 10 is rebuilt as ten admitted anchor commands in Q(√2), with a
   refusal control that bites 1/4 into its parent.

Read-only throughout: no row changed, no score moved, `submission.csv` and root `WHITEBOARD.md` untouched.
Instruments: `scripts/polish_ceiling.py`, `scripts/anchor_chain.py` (both new); records
`workspace/push/polish_ceiling117.json`, `workspace/push/anchor_chain117.json`.

---

## 1. The 3-versus-6 violation count, reconciled

Doc 75 §11 said "3 violating pairs" and "6 violations at 40 digits" for the same pose. **Both are
correct; they count different things, and neither is a disagreement about the geometry.**

| reader | rule | n = 999 notch |
|---|---|---|
| `notch32.violations(..., eps = 1e-9)` — the screen the repair descends on | a pair is violating when its SAT penetration is **> 1e-9** | **3** pairs (deepest 9.389e-2) |
| `true_geom.check` — the 40-digit judge | a pair is violating when its exact slack is **< 0** | **6** pairs |

So the pose has three pairs overlapping by 1e-2 … 1e-1 and three more that are *near-tangent*: slack
strictly negative but smaller than the screen's 1e-9 admission threshold. The screen deliberately ignores
them (a repair cannot usefully descend on 1e-10 noise); the judge deliberately counts them (a pose is legal
or it is not). The same gap shows at scale wherever both readers are run: in the polish sample, n = 507 at
δ = 1e-4 reads **68** pairs through the screen and **119** at 40 digits.

**Conclusion.** The notch is illegal by 3 deep pairs *and* 3 near-tangent ones. Nothing in §11's verdict
changes; the headline number is the deep one (3), and the 40-digit count (6) is the one a certificate would
have to clear.

## 2. The scope of the k = 32 "no"

The refusal is a statement about a **search space**, and it is worth naming it precisely (the Director's
Note's own discipline):

* **insertion point** — the centre of the largest free axis-aligned square found by `hmax_scan(grid=140,
  angles=33)` plus six refine rounds, side **0.8394**; not any other of the pose's free regions, and not a
  rotated free square;
* **move set** — exact single-cell separating-axis slides (both signs, all four axes of each pair), and a
  patch descent over 4.5-wide patches of `(x, y, θ)` with L-BFGS-B and monotone acceptance;
* **container** — exactly `k = 32`, enforced by clamping, never by penalty;
* **order** — one cell inserted into a fixed frontier pose of 998 cells; no cell removed, no cell added
  twice, no block replaced.

What the run *does* establish inside that space: the finite free square is 0.1606 short of a cell, the
descent buys 3.1e-3 of side and 1.9e-4 of the deepest bite, and the three deep pairs are mutually blocking
(closing one by an exact slide opens another). What it does **not** establish: that no 999-cell packing
below 32 exists, and in particular nothing about replacing the notch's three-cell neighbourhood as a block
— which is the one move this space excludes and run 115 priced.

## 3. The measured polish ceiling

`polish_ceiling.py` does to a beaten row what wants to be done to it: shrink its own container by `delta`,
clamp every cell into the smaller box (a **hard projection** — the side constraint is never a penalty), run
the contact-graph repair, and ask `true_geom` at 40 digits whether it closes.

Sample: 12 beaten rows stratified by capture `e`, bands k = 17 … 32.

| n | k | capture e | δ = 3e-5 | δ = 1e-4 | δ = 3.3e-4 | ceiling |
|---|---|---|---|---|---|---|
| 655 | 26 | 0.001 | 88 viol | 88 viol | 88 viol | **0.00000** |
| 507 | 23 | 0.062 | 119 viol | 119 viol | 119 viol | **0.00000** |
| 270 | 17 | 0.126 | 68 viol | 68 viol | 68 viol | **0.00000** |
| 417 | 21 | 0.178 | 75 viol | 75 viol | 73 viol | **0.00000** |
| 337 | 19 | 0.220 | 69 viol | 69 viol | 69 viol | **0.00000** |
| 985 | 32 | 0.252 | 123 viol | 123 viol | 123 viol | **0.00000** |
| 590 | 25 | 0.287 | 141 viol | 141 viol | 141 viol | **0.00000** |
| 917 | 31 | 0.326 | 180 viol | 182 viol | 182 viol | **0.00000** |
| 449 | 22 | 0.361 | 84 viol | 84 viol | 84 viol | **0.00000** |
| 584 | 25 | 0.387 | 99 viol | 99 viol | 99 viol | **0.00000** |
| 968 | 32 | 0.436 | 126 viol | 126 viol | 126 viol | **0.00000** |
| 904 | 31 | 0.468 | 123 viol | 123 viol | 123 viol | **0.00000** |

**Every sampled row has ceiling `0.00000`.** Not one closes even at δ = 3e-5 — one thirtieth of the band's
floor (6.2e-5). The repair stalls after one or two passes ("no single slide helps") in every case.

**The mechanism, which is the real finding.** These poses sit at zero clearance. Clamping the whole box
inward overlaps *every* tight pair at once (the deepest bite equals δ/2), and a pose with no slack has
nothing for a single-cell slide to trade: closing one pair opens another. So the polish problem is not
"the move is 12–30× bigger than the band" (run 117's pricing) but "**the move set cannot move at all**".

**Caveat, stated so the claim is not overread.** The initialisation clamps the *whole* container, which is
the worst case for a tight pose; a polish that moved only boundary cells, or that re-solved a face at a
time, is not tested here. The claim is therefore: *this* hard-projection repair obtains nothing, so the
honest ceiling of a polish campaign is **0.00000**, not the +0.00999 the band comparison allowed and not
the 0.15023 – 0.21742 a 1 % capture is worth. Both earlier numbers are now upper bounds that are not
attained by the only polish instrument we have.

## 4. Anchors that become commands

`anchor_chain.py` bridges `glm_universal.reasoning.stepwise_script`. The split is explicit because the two
layers hold different things:

* **the Step** carries the command in column 1 ("Step 5: PROPAGATE_SLIDE places cell 1 (axis) is given as
  5."), the same command in column 2 ("s5 = PROPAGATE_SLIDE#1 = 5 (given)"), the number of cells placed as
  its exact value, and the anchor's geometry in `detail`. `step_check` verifies the columns, the backward
  links and the count;
* **the anchor gate** verifies the geometry exactly in Q(√2): no overlap with any earlier cell, every
  declared contact tangent with slack **exactly 0**, every declared wall edge **exactly** on the container,
  and every requirement an earlier step.

An anchor is admitted only when **both** pass. Steps are `given` rather than recomputed because a placement
is a reading, not an arithmetic result — the GLM's own category for it — and the geometry gate is what
does the work.

**The exact row (n = 10).** The delivered decimal strings snap to `(1/4)Z + (1/4)√2 Z` at directions 0° and
45°, worst read **1.2e-9** (the finalizer pad), so the reconstruction is exact:

| step | command | cell | verdict |
|---|---|---|---|
| 1 | ANCHOR_CORNER | 0 | admitted |
| 2 | ANCHOR_CORNER | 3 | admitted |
| 3 | ANCHOR_CORNER | 4 | admitted |
| 4 | ANCHOR_CORNER | 7 | admitted |
| 5 | PROPAGATE_SLIDE | 1 | admitted |
| 6 | PROPAGATE_SLIDE | 2 | admitted |
| 7 | PROPAGATE_SLIDE | 5 | admitted |
| 8 | PROPAGATE_SLIDE | 6 | admitted |
| 9 | STACK_BLOCK | 8 | admitted |
| 10 | STACK_BLOCK | 9 | admitted |

* side, exactly: **`3 + 1/2√2`** (= 3.707106781186…, the proved optimum `s(10)`, doc 24);
* overlaps: **0**; `step_check` passes on all ten, and `chain_check` over the whole chain passes;
* the contact graph the commands read off is exact: `0-1, 0-2, 1-2, 1-8, 2-9, 4-5, 4-6, 5-6, 5-9, 6-8,
  8-9`, with cells 3 and 7 wall-only at opposite corners — the pinwheel.

**The refusal control.** Cell 1, moved 1/4 towards cell 0 along the axis they actually touch, offered to
the same two-step gate: **refused — "overlap with cell 0: exact slack −1/4"**. The refusal is geometric, not
a plumbing error (a first draft was rejected by `step_check` for an index mismatch, which proved nothing;
the control now uses a properly indexed chain so only the geometry can fail it).

## 5. So can the project be "a working computation settling into an efficient grid"?

**As a certificate language, yes — exactly, and that is a real gain.** A legal packing *is* a chain of
anchor commands, each admitted by a two-column exact check plus a field-exact placement check. That gives
the project a normal form in which a pose can be stated, replayed, audited and refused at the first illegal
anchor, with the refusal carrying an exact slack. It is the same content as `true_geom` + the certificate
gate, but expressed in the planner's own step format, so an anchor chain and a GLM chain are the same kind
of object.

**As a generator, no — not by itself.** Every command above was *read off* a finished pose: `command_for`
classifies a cell by which walls and contacts already close it. Nothing in the chain proposes a packing, and
`order_cells` refuses when a cell touches no wall and no placed cell, which is precisely the situation a
search is in. To make anchors *settle* rather than *describe*, the chain has to run goal-directed (given
`L`, admit anchors until the frame closes and reject dead ends) — which is the constructive search this
project already runs numerically, now with an exact admission test per step. That is the honest status:
**a verified transcript, not yet a solver.**

## 6. Checks

| check | result |
|---|---|
| `anchor_chain.py --selftest` | exact side `3 + 1/2√2`, 10/10 anchors, refusal at exact slack −1/4 |
| `anchor_chain.py` | JSON written, `chain_check` green, 0 overlaps |
| `glm_wheels.py --audit` | **632 decision functions, 0 offenders**; `anchor_chain` 19, 0 naming float |
| `polish_ceiling.py` | sample of 12 rows, ceilings all 0.00000 |
| `sqscore.py`, `record_guard.py`, `void_insert.py --selftest` | re-run green, score unchanged |
| `submission.csv`, `WHITEBOARD.md` | untouched |
