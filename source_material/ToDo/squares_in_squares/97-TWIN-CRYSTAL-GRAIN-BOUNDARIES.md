# 97 — Twin-crystal grain boundaries: the diagnosis, the constructor, and why the family cannot win (Run 140)

**Run 140, 2026-11-25.** Instruments `scripts/promote_n090.py` (new: the promotion and its
perturbation proof), `scripts/crystal_domains.py` (new: the domain diagnosis),
`scripts/twin_boundary.py` (new: the commensurate twin constructor and its search); ledgers
`workspace/push/import_n090.json`, `crystal_domains.json`, `twin_boundary.json`.
**One row changed: n = 90.** `submission.csv` now scores **`22.217428576`** with **554** beats, up from `22.218056945` / 553; root `WHITEBOARD.md` carries one appended line.

## 1. The promotion: row 90, C1–C4 satisfied

The candidate passed the gate in run 139 (doc 96 §2). This run writes it.

**C1 — proof.** The pose is the published exact rational certificate (jazivxt 2026, improved by
de Winter; `packing/resources/web/de-winter-997-followup-2026-11-21/derived/candidate-reading-copy.json`).
Because `cos(2 arctan t) = (1-t^2)/(1+t^2)` and `sin(2 arctan t) = 2t/(1+t^2)` are rational for
rational `t`, the whole certificate lives in `Q`: 4005 pairs decided by exact four-axis SAT, **0
overlaps, 0 zero-slack touches, minimum slack `1e-73`**. The delivered row is that pose with every
centre inflated by `1 + 1e-9` (`promote_n090.py`, our own frame convention: the certificate itself
touches to `1e-73`, which no decimal CSV can carry).

**C1 on the *rendered* row.** The written file is not the exact pose, so the promotion carries a
perturbation proof: each centre is rounded to the table's 10 decimals (error ≤ `9.89e-11` per pair of
axes), each angle to 12 decimals in radians (error ≤ `4.35e-13`), so no corner moves more than
`d = 9.92e-11`; a pairwise separating slack changes by at most `4d`, leaving
**`min slack 6.03e-10 > 0`**, and the box grows by at most `2d`, leaving
`side ≤ 9.9940387757752980 < 10.0000000019`. No transcendental is evaluated in that step — the
argument is a triangle inequality on the exact pose.

**C2 — margin.** Measured from the written CSV: side **`9.9940387756`** against the delivered
`10.0000000019`, a margin of `5.961e-3` and a score gain of **`6.283680e-4`** — four orders of
magnitude above the `1e-8` noise floor, and it moves the recorded total.

**C3 — integrity.** Every guard green (§5). **C4 — this document.**

| quantity | before | after |
| --- | --- | --- |
| delivered score | `22.218056945` | **`22.217428576`** |
| rows below `ceil(√n)` | 553 | **554** |
| rows tied to the grid | 447 | **446** |
| row 90 side | `10.0000000019` | **`9.9940387756`** |
| verified room (51 rows) | `1.09647` | **`1.09584`** |
| beaten-row headroom | `15.022691` | **`15.076155`** |

Every quoted total moved with it: `sqscore.DELIVERED_SCORE` / `DELIVERED_BEATS`,
`record_guard.CANON` (`22.21742`), the §1 card of `DIRECTORS-NOTE` (score, beats, 446 grid ties,
"552 of 554 certified", the `15.076155` payer), `README`, `STATUS`, `REPRODUCE`, `RECONCILIATION`,
`00-OVERVIEW`, `05-MECHANICS`, `19-COLLECTION-AND-REVIEW`, `NEXT_STEPS`, `GLM_INVESTIGATION`, and
the title-block claims of six older run docs, which are now tagged *historical: at that time* rather
than rewritten.

**Attribution.** The packing is **jazivxt's, improved by Joost de Winter** (T-338, house of
21 November 2026), published with an exact rational certificate by the Squares Project. What this
run contributes is the independent exact verification, the `1e-9` render and the perturbation bound
— not the geometry. The row is a repack of their result, and the ledger says so.

## 2. Crystal-domain diagnosis of the top-room rows

`crystal_domains.py` reads the delivered pose and decides, in `Decimal` at 50 digits: orientation
classes (rotations mod `pi/2`, tolerance `1e-6`), contacts (exact clearance ≤ `1e-9`, split into
edge and corner by counting tight axes), grain boundaries (contacts joining two classes), domains
(connected components), same-class sub-domains, and the rigidity *count* `3m - 3` for the largest
domain. `L^2/n` is the area deficit — how far the pose is from the zero-waste floor.

| n | L | L²/n | room | cls | contacts | grain | dom | same | big | ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 3.877084 | 1.3665 | 0.00000 | 2 | 13+1 | 6 | 1 | 5 | 11 | 0.433 |
| 17 | 4.675530 | 1.2859 | 0.00366 | 3 | 22+2 | 11 | 1 | 8 | 17 | 0.458 |
| 18 | 4.822876 | 1.2922 | 0.02778 | 2 | 24+2 | 6 | 1 | 5 | 18 | 0.471 |
| 19 | 4.885618 | 1.2563 | 0.01333 | 2 | 26+5 | 8 | 1 | 6 | 19 | 0.481 |
| 51 | 7.690356 | 1.1596 | 0.03086 | 2 | 82+37 | 12 | 1 | 5 | 51 | 0.547 |
| 55 | 7.945771 | 1.1479 | 0.02936 | 7 | 93+32 | 25 | 1 | 10 | 55 | 0.574 |
| 68 | 8.798795 | 1.1385 | 0.03260 | 9 | 124+14 | 35 | 1 | 14 | 68 | 0.617 |
| 72 | 9.000000 | 1.1250 | 0.02828 | 1 | 127+112 | 0 | 1 | 1 | 72 | 0.596 |
| 83 | 9.634758 | 1.1184 | 0.02906 | 4 | 132+62 | 23 | 1 | 9 | 83 | 0.537 |
| 84 | 9.697935 | 1.1196 | 0.03005 | 5 | 147+52 | 23 | 1 | 8 | 84 | 0.59 |
| 85 | 9.742641 | 1.1167 | 0.02903 | 2 | 139+99 | 16 | 1 | 5 | 85 | 0.552 |
| 86 | 9.820535 | 1.1214 | 0.03424 | 4 | 137+76 | 17 | 2 | 7 | 85 | 0.544 |
| 88 | 9.882451 | 1.1098 | 0.02798 | 3 | 152+81 | 21 | 2 | 6 | 87 | 0.589 |
| 89 | 9.949747 | 1.1123 | 0.03177 | 2 | 148+108 | 16 | 1 | 5 | 89 | 0.561 |

`cls` classes, `contacts` edge+corner, `grain` cross-class contacts, `dom` domains, `same`
same-class sub-domains, `big` largest domain, `ratio` edge contacts / (3·big − 3).

**What the rows are.** Every high-room row is a *polycrystal*, not a single lattice: **2 to 9
orientation classes**, **6 to 35 grain contacts** each, and one connected contact network per row
(n = 86 and 88 are the only rows with two separate domains; 85 and 87 squares in one piece
elsewhere). n = 72 is the exception and the control: **one class, 239 contacts, zero grain
contacts** — a perfect single crystal, the `8 x 9` grid at `L = 9`, which is why it merely ties the
grid instead of beating it.

**Rigidity.** Edge-contact counts are **0.43–0.62** of the `3m - 3` necessary condition for the
largest domain, so not one of these rows is rigid by counting — consistent with the run-139 finding
that 17 of the n = 90 certificate's squares can slide. The high-room poses are floppy polycrystals,
not locked crystals.

**How much room is geometric.** `L²/n` is `1.11–1.37`: these poses are 11–37 % above zero waste.
Across the 51 room rows the booked room is **1.09584** while the same rows hold **3.72277** of
geometric slack (`L/√n − 1`), so **the room is only 29 % of the distance to a zero-waste pose** —
the room is not an area artefact, but a constructor would have to close a third of the gap to the
area floor to collect all of it.

## 3. The commensurate twin constructor — and its theorem

**Construction.** Domain A is an `a1 x a2` block of unit cells; domain B is a `b1 x b2` block rotated
by the *commensurate rational spinor* angle `tan(θ/2) = p/q`, for which
`cos θ = (q²−p²)/(q²+p²)` and `sin θ = 2pq/(q²+p²)` are **rational**. B's bounding box is placed
`a2 + g` above A's, so the two lattices are separated by a line gap `g ≥ 0`: **zero overlap by
construction**, at any angle, for any block sizes. The exact SAT of `import_n090` re-decides it
anyway, so a construction bug cannot pass silently.

**Coverage.** 12 spinors (`q ≤ 6`, `p ≤ q`, coprime, `p ≠ 0`), 5 gaps (`0, 1/16, 1/8, 1/4, 1/2`),
every integer split `a1·a2 + b1·b2 = n`, on 14 rows: **935520 candidates**, every one scored by the
closed form `max(a1, b1·c + b2·s, a2 + g + b1·s + b2·c)`, and the best per row built and verified
exactly.

| n | best | delivered | bound | spinor | gap | A | B | overlaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 4.000000 | 3.877084 | 4 | 1/1 | 0 | [2, 1] | [3, 3] | 0 |
| 17 | 5.000000 | 4.675530 | 5 | 1/1 | 0 | [1, 1] | [4, 4] | 0 |
| 18 | 5.000000 | 4.822876 | 5 | 1/1 | 0 | [2, 1] | [4, 4] | 0 |
| 19 | 5.000000 | 4.885618 | 5 | 1/1 | 0 | [2, 2] | [3, 5] | 0 |
| 51 | 8.000000 | 7.690356 | 8 | 1/1 | 0 | [2, 1] | [7, 7] | 0 |
| 55 | 8.000000 | 7.945771 | 8 | 1/1 | 0 | [5, 3] | [5, 8] | 0 |
| 68 | 9.000000 | 8.798795 | 9 | 1/1 | 0 | [4, 1] | [8, 8] | 0 |
| 72 | 9.000000 | 9.000000 | 9 | 1/1 | 0 | [6, 3] | [6, 9] | 0 |
| 83 | 10.000000 | 9.634758 | 10 | 1/1 | 0 | [2, 1] | [9, 9] | 0 |
| 84 | 10.000000 | 9.697935 | 10 | 1/1 | 0 | [2, 2] | [8, 10] | 0 |
| 85 | 10.000000 | 9.742641 | 10 | 1/1 | 0 | [4, 1] | [9, 9] | 0 |
| 86 | 10.000000 | 9.820535 | 10 | 1/1 | 0 | [3, 2] | [8, 10] | 0 |
| 88 | 10.000000 | 9.882451 | 10 | 1/1 | 0 | [4, 2] | [8, 10] | 0 |
| 89 | 10.000000 | 9.949747 | 10 | 1/1 | 0 | [8, 1] | [9, 9] | 0 |

**The theorem.** For two blocks glued along a straight line, `n = a1a2 + b1b2`, and the side is
`max(a1, b1, a2 + b2)` — an **integer**. Since `a1a2 + b1b2 ≤ max(a1, b1)·(a2 + b2)`, every such
configuration has `L ≥ √n`, and being an integer, `L ≥ ceil(√n)`. **The family can at best tie the
grid; it can never beat it.** The search attains exactly `ceil(√n)` on 14 of 14 rows, and the
optimiser picks **`p/q = 1/1`** — a 90° rotation, which for a square lattice is the same lattice, so
the best "twin" is the degenerate one: two plain grids. Every genuine twin angle (the other ten
spinors) is strictly worse, because a rotated block's bounding box is `b1·c + b2·s` by
`b1·s + b2·c`, and `c + s ≥ 1` with equality only at the degenerate angles.

Since **554 of our rows already beat the grid**, the family is provably dominated on every row we
care about: no two-block-butted twin can improve any of them, at any gap and any spinor.

**The one strict improvement, and why it was refused.** At n = 72 the constructor ties `L = 9`
exactly while our delivered row carries our own frame padding (`9.0000000018`). That is strictly
smaller by `1.78e-9` — a score gain of `2.47e-11`, **below the C2 noise floor** (it would not move
the 9-decimal total). Refused, and recorded as refused: **0 promotions from this family.**

## 4. What the diagnosis says to build next

The delivered poses already *are* polycrystals with 6–35 grain contacts each. A constructor that
butts two blocks along a line cannot compete because it wastes the interface; the poses that win
share area *across* the boundary, with cells of one lattice interleaving into the other's gaps. That
is a one-parameter family per spinor (slide the interface), and it is the natural next instrument:
build a commensurate interface where both lattices own cells on both sides of the line, and gate it
exactly. The diagnosis bounds what such a construction can ever win on the 51 room rows: **3.72277**
of score at absolute best (zero waste everywhere), of which the booked room is `1.09584`.

## 5. Checks

`promote_n090.py` (promotion, perturbation bound `6.03e-10` slack, `2d` box), `crystal_domains
--selftest` **4** controls, `twin_boundary --selftest` **5** controls (rational spinors;
`c = 3/5, s = 4/5` block bbox `14/5`; a built twin with zero overlaps and min slack 0; a displaced
cell caught at `-0.5`; the closed-form family bound), and the full guard set: `sqscore`
**22.217428576** (554/447 → 554/446), `record_guard` OK, `glm_wheels --audit` **684 functions,
0 offenders**, `row_census`, `motif_wheels`, `leech_audit_fix`, `verify_certificates`, `notch136`,
`glm_plan` (5), `pub_bounds_check` (4), `witt_octad` (5), `import_n090` (5), `pure_slide`,
`beaten_leverage`, `band5`, `ext_census`, `range_leverage`, `construct_seam`, `p_screen`,
`legal_slide`, `structure --control`/`--check-solver`, `perturb`, `anchor_chain`, `void_insert`,
`true_geom`, `py_compile`.
