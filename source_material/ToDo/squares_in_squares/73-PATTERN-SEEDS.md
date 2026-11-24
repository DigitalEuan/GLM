# 73 — Constructive pattern seeds: macro-block topologies, and why the tilt must stay on the boundary

Run 111 closed the repair route: every mechanism that starts from the delivered pose and perturbs it —
free angles, face slides, chains, lifts, penetration ladders — is refused, and the best legal state on
n = 29 is still `9.6e−5` worse than delivered. Doc 72 §5 then asks the other question: can a packing be
**built** instead of repaired? This run builds. `scripts/pattern_seeds.py` never reads the delivered
coordinates of a row; it reads `n` and `L_delivered` and synthesises packings from macro-blocks, judged
by `true_geom.py` at 40 digits.

**Verdict: no family comes within `C2`, so nothing is promoted and `submission.csv` is untouched.** But
the deficits are not mysterious — they decompose exactly, and the decomposition names the reason tilt
fails in the body and works on the boundary.

## 1. Target set (doc 72 §5 R1 and R3)

Nine rows, chosen to cover both halves of the request:

| class | rows | why |
|---|---|---|
| open residue above 324 | 680, 733, 845, 904, 971 | not word-exact, so no exact sentence exists for them (doc 65); 680/733/845 are the `2k + 4/7` family, 904 is `side-not-recovered`, 971 is the largest-void row in the table |
| high-slack mid-range | 29, 41, 53, 55 | the rows where a construction has the most relative room (`L/√n` = 1.10, 1.08, 1.07, 1.07) |

R3 is satisfied by mechanism: macro-block topology is not among the refused mechanisms (face slide,
chain, lift, re-orientation, void trade, free angle). R1 is *not* satisfied for the open rows — they are
non-word, so they are certifiable by no algebraic field at all (doc 70 §4). A win there would be
discovery-only until an interval verifier is added, and this document says so rather than quietly
treating a float result as a candidate.

## 2. The generator

A **block** is a `w`-by-`h` array of unit squares at a fixed angle, with its exact bounding box. A seed
is a list of blocks whose areas sum to `n`, placed by a **shelf packer** over bounding boxes: boxes never
overlap, so the squares never overlap — and that is verified, not assumed. Two hairline constants
(`ε_g = 1e−9`) separate neighbouring cells and neighbouring blocks, because a construction contact sits
at SAT slack exactly 0 and would otherwise read as a `1e−16` float overlap at 40 digits; the cost is
`≤ 3e−8` of side, six orders below any deficit measured here.

Four topologies:

* **A — dual-tilted blocks.** Two 45° blocks `k×k`, a bent transition strip (one strip of each parity, so
  the seam turns a corner), an upright residue.
* **B — L-cut nested frames.** An upright core, four 45° perimeter bands, an upright residue staircase.
* **C — rational-t lattices.** Blocks at a Pythagorean angle — `arctan(3/4)`, `arctan(5/12)`,
  `arctan(8/15)`, `arctan(2/1)` — in square and band form, upright residue.
* **D — upright reference.** A near-square upright block plus a residual strip, no tilt anywhere. Every
  tilted family has to beat this before its tilt can claim to have earned anything.

Ranking is in float, the reported side is `true_geom.side` at 40 digits, and zero overlap is
`true_geom.check` at 40 digits — the same separation as the rest of the repository. 26 to 120 block
configurations per family per row, 13 shelf widths each.

## 3. Results: every family loses, and D loses least

Best seed per row and family (`L_seed`, and the deficit against the true delivered side):

| n | delivered | A (dual 45°) | B (L-cut frame) | C (Pythagorean) | **D (upright)** |
|---|---|---|---|---|---|
| 29 | 5.933833 | 7.828427 (−31.9%) | 6.656854 (−12.2%) | 8.538462 (−43.9%) | **6.000000 (−1.12%)** |
| 41 | 6.926693 | 8.828427 (−27.5%) | 7.414214 (−7.04%) | 9.846154 (−42.2%) | **7.000000 (−1.06%)** |
| 53 | 7.822876 | 9.828427 (−25.6%) | 8.656854 (−10.7%) | 11.153846 (−42.6%) | **8.000000 (−2.26%)** |
| 55 | 7.945771 | 9.828427 (−23.7%) | 8.414214 (−5.90%) | 11.769231 (−48.1%) | **8.000000 (−0.68%)** |
| 680 | 26.571429 | 28.828427 (−8.49%) | 27.656854 (−4.08%) | 39.230769 (−47.6%) | **27.000000 (−1.61%)** |
| 733 | 27.571429 | 29.828427 (−8.19%) | 28.656854 (−3.94%) | 39.230769 (−42.3%) | **28.000000 (−1.55%)** |
| 845 | 29.571429 | 31.828427 (−7.63%) | 30.656854 (−3.67%) | 43.230769 (−46.2%) | **30.000000 (−1.45%)** |
| 904 | 30.563626 | 32.828427 (−7.41%) | 31.656854 (−3.58%) | 44.461538 (−45.5%) | **31.000000 (−1.43%)** |
| 971 | 31.678780 | 33.828427 (−6.79%) | 33.000000 (−4.17%) | 45.769231 (−44.5%) | **32.000000 (−1.01%)** |

Zero violations at 40 digits for all 36 seeds that have one. Nothing beats `L_delivered`, so C2 fails
everywhere and nothing is lifted to `verify_certificates.py`.

## 4. The deficit, decomposed: tilt waste against packing waste

Each seed's void splits exactly into two parts:

    void = L_seed² − n  =  (Σ block bounding-box areas − n)  +  (L_seed² − Σ block bbox areas)
                          \______ tilt waste ______/          \_____ packing waste _____/

*Tilt waste* is what the bounding boxes of tilted blocks cost over the squares inside them. *Packing
waste* is everything the shelf leaves between the boxes. Both are in the run's ledger, per family, per row.

| n | A tilt / pack | B tilt / pack | C tilt / pack | D tilt / pack |
|---|---|---|---|---|
| 29 | 8.0 / 24.3 | 4.0 / 11.3 | 17.8 / 26.2 | 0.0 / 7.0 |
| 680 | 8.0 / 143.1 | 4.0 / 80.9 | 480.0 / 379.1 | 0.0 / 49.0 |
| 971 | 8.0 / 165.4 | 4.0 / 114.0 | 661.1 / 462.8 | 0.0 / 53.0 |

Two facts fall out, and they are the real result of the run.

**A solid tilted block doubles its area.** A `k×k` block at 45° has bounding box `k√2` on a side, so its
boxes cover `2k²` for `k²` squares — 100% tilt waste. At a Pythagorean angle `(p, q)` with `c = p/s`,
`s = q/s`, a `b×b` block's box is `b²(c + s)²`: `1.96 b²` at 3-4-5, `1.83` at 8-15-17, and the cheapest
of the four, `1.710` at 5-12-13. That is why family C is not merely worst but *capped*: no configuration
can waste less than `0.71` of its area in boxes alone, and at n = 971 it indeed lands at `661` (`0.68 n`),
its tilted squares contributing only `970 − 661 + …` — the deficit is the tilt itself, not the packing.
**The optimiser responds by using almost no tilt.** Family A's best seed on every row above n = 300 is
`k = 2` — the smallest legal dual block, tilt waste exactly `8` — and family B's is `band = 1`, waste `4`.
Both families then behave like D with a little decoration, and the deficit they carry over D is pure
packing waste from the extra boxes.

**Which is exactly the boundary lesson.** The delivered packings do tilt — 45° staircases and
`2k + 4/7` edges are all over the table — but the tilt lives in a *one-cell boundary staircase*, where a
tilted cell's surplus triangle is `O(perimeter)`, not `O(area)`. Body tilt costs its area a second time;
edge tilt costs a strip. Every family here puts tilt in the body, so every family loses by roughly the
factor the geometry demands, and the ranking A < B < C follows the amount of solid tilted area each
topology forces.

The remaining `1.0–2.3%` of family D is not tilt at all: it is the shelf's inability to nest the residual
strip into the near-square block (49–57 units at n ≥ 680, 53 at n = 971), against a delivered void of only
`26–33` units on those same rows. A nesting packer — guillotine or a proper bottom-left — could close
part of that; a compaction pass could close more; neither would make an *upright* construction beat a
delivered packing that already places its leftovers in the corners.

## 5. Against doc 72 §5

| criterion | result |
|---|---|
| **C1** certifiable pose | fails by construction: the targeted open rows are non-word, and every seed here is a float placement |
| **C2** strictly smaller 40-digit true side, zero overlap | **fails on all nine rows** — the closest is D on n = 904 at `+0.4364` |
| **C3** gain above `ε` and rendering noise | not reached |
| **C4** the metric moves | not reached |

What would change the verdict, in the order worth trying:

1. **A boundary family** (call it E): upright core, plus a *one-cell 45° staircase* along one and then two
   sides, built as a stair rather than as a block. This is the only topology whose tilt cost is
   perimeter-order, and it is the shape the delivered table actually uses — so building it from scratch is
   the honest test of whether the generator can reproduce the frontier, not just approach it.
2. **A nesting packer** (guillotine, or bottom-left with corner insertion) to cut family D's `1–2%` to the
   delivered void, which would tell us whether the residual is constructional or fundamental.
3. **An interval-arithmetic verifier** before any of this can produce a candidate: the open rows are
   non-word, so C1 blocks promotion of any float placement regardless of how good the side is.

## 6. Controls and audit

`pattern_seeds --selftest`: **5 controls** (axis block side 2, 45° block side `2√2`, block areas sum to `n`
in every family, no duplicate cells and zero `true_geom` violations for a mixed shelf, near-square residue
chosen over exact factorisation). `pattern_seeds.py` is **discovery-side and deliberately outside the
float audit**, exactly like `relax_angles.py`: it proposes, `true_geom` judges, and it may not print or
promote a result. The audit still checks **596** decision functions with **0** naming `float`, every
selftest is green, `sqscore` still reports 22.218056945 with 553 beats, and `record_guard.py` still
refuses a stale total presented as current. Ledger: `workspace/push/pattern_seeds.json`.
