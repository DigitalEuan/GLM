# 91 — Beaten-row tightening: the ranking, the slack census, and the payback on delivered rows

**Run 132, 2026-11-25.** Instruments `scripts/beaten_leverage.py` and `scripts/tighten.py`; records
`workspace/push/beaten_leverage132.json` and `workspace/push/tighten132.json`.
`submission.csv` and root `WHITEBOARD.md` are untouched: **nothing was promoted**, because nothing passed.

The brief had three parts: rank the beaten rows by unclaimed room with the proved optima filtered out; spend a
bounded budget tightening the top of that ranking with coordinates *and* angles free, gating every candidate
exactly; log the ranking, the distribution and any wins. Two independent instruments came out of it, and both
give the same answer from opposite directions.

---

## 1. The ranking

`room(n, L) = L/sqrt(n) - 1` is the row's own score — the whole of what that row still holds — and the 553
delivered beats are worth `22.218056945` in total. `beaten_leverage.rank` filters the rows whose delivered side
is already the proved optimum (a Q(√2) value from `optima.proved`, compared at 40 digits) and sorts the rest by
room.

**Two rows are filtered**, and they are worth naming because it is easy to assume there are more: `n = 5`
(`2 + √2/2 = 2.7071067812`, delivered to the pad) and `n = 10` (`3 + √2/2 = 3.7071067812`). The other proved
values — `n = 2, 3, 4, 6..9, 14, 15, 24, 35` and every perfect square — are *not* beaten rows at all (they are
grids, or `n = 3` is `2`), so they never enter the ranking. That leaves **551 rows holding `14.639746101` of
unclaimed room**; the 449 grid/unbeaten rows hold the other `7.578310844`.

The top of the ranking:

| n | k | L (delivered) | room | 1/√n | src |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 11 | 4 | 3.877083591506 | **0.168985** | 0.301511 | `aux:square-11.svg-0` |
| 18 | 5 | 4.822875657118 | 0.136763 | 0.235702 | `exact:square-18.svg` |
| 17 | 5 | 4.675530095176 | 0.133983 | 0.242536 | `exact:square-17.svg` |
| 19 | 5 | 4.885618084754 | 0.120838 | 0.229416 | `exact:square-19.svg` |
| 26 | 6 | 5.621320345204 | 0.102432 | 0.196116 | `exact:square-26.svg` |
| 29 | 6 | 5.933833464340 | 0.101885 | 0.185695 | `exact:square-29.svg` |
| 28 | 6 | 5.824444618330 | 0.100717 | 0.188982 | `exact:square-28.svg` |
| 27 | 6 | 5.707106782836 | 0.098333 | 0.192450 | `exact:square-27.svg` |
| 39 | 7 | 6.810722084774 | 0.090588 | 0.160128 | `exact:square-39.svg` |
| 38 | 7 | 6.707106782888 | 0.088036 | 0.162221 | `exact:square-38.svg` |
| 37 | 7 | 6.598619610942 | 0.084806 | 0.164399 | `exact:square-37.svg` |
| 41 | 7 | 6.926693096180 | 0.081768 | 0.156174 | `exact:square-41.svg` |

Three properties of this ranking are worth recording, because they change where a budget should go:

* **Room is spread, not concentrated.** The top ten rows hold `1.142559` of `14.639746` — 7.8 %. Band by band,
  the room is `0.169` at `k = 4`, `0.392` at `5`, `0.403` at `6`, then flat at `0.42–0.57` from `k = 7` all the
  way to `k = 32`. There is no single fat row to attack; the score is a long tail.
* **Room and leverage pull in opposite directions.** Room falls with `n` and `1/√n` falls with `n` too, so the
  top rows are high-room *and* high-margin only because they are small: a gain of `dL` on `n = 11` is worth
  `0.30·dL` and on `n = 999` only `0.032·dL`. The ranking by room is therefore also the ranking by
  "score per unit of improvement", which is the useful order for a bounded budget.
* **The top three are band 5 and band 4 — and run 131 already showed why they are hard.** `n = 17` is delivered
  at `4.675530`, *below* the pocket construction's `4.707107`: the frontier pose in that band is not the pocket,
  and run 131's bound (a pocket arrangement cannot hold more than 17 cells below 5) is consistent with a smarter
  17-cell pose existing. Band 5's open rows are `20..23`, and they sit *below* these three in room because their
  sides are only `0.13` off the grid, not because they are easier.

## 2. The slack census: every one of the 551 poses is at exact contact

The first thing a tightening pass should establish is whether there is any slack to take for free. A uniform
contraction about the box centre is the cheapest coordinated shift there is: every coordinate moves, the angles
stay, and the pair test under contraction is `g·|d·q| >= h_a + h_b` on some axis, so the pose stays legal for
every `g` down to

```
g* = max over pairs of ( min over the four axes of (h_a + h_b)/|d.q| ) ,
```

and the side then drops from `L` to `L(g*)`. `beaten_leverage.exact_bound` computes that threshold in `Decimal`
at 40 digits (the float scan only proposes the binding pair — and the control C2 case where a legal grid gave
`g = 1.9` when the rule was wrong shows why the proposal is never trusted), contracts, and re-gates the result
with `legal_slide.check_pose`.

**All 551 beaten rows measured, no sampling:**

| | rows |
| :--- | ---: |
| loose (`g* <= 1 - 1e-8`, a real free gain) | **0** |
| contact to the `finalize` pad (`g* = 1 - ~1.8e-9`) | 246 |
| exactly tight (`g* = 1` to 40 digits) | 305 |

`g*` ranges over `[0.99999999959, 1]`. The largest free gain in the whole table is `4.745e-09` of side, and the
sum over all 551 rows is `4.798e-07` — which is the `finalize` pad (`2e-9` relative), not a pose property, and
below any noise floor worth acting on.

**So the answer to "what slack is there" is: none.** Every delivered beat is a fully jammed contact structure;
there is no slide, and no shift, that can reduce a side. Any improvement must come from a rearrangement.

## 3. The bounded rearrangement pass

That leaves rearrangement, which is what `tighten.py` spends its budget on. Per row and per seed it runs the
repo's own `structure.attempt` **from the delivered pose** — the squeeze-and-project loop that relaxes `(x, y, t)`
patch by patch, so angles move; nothing is frozen — to a target of `L0 - 0.004`, then measures the projected pose
at 40 digits (`p_screen.measure`: exact depth, violation count and side) and hands it to the exact legal-move
stage (`p_screen.convert`: minimum legal uniform scale, band slides, exact tightening). The reported `dL` is
`L0 - L_final`, so positive is a gain. Ten rows (the top of the ranking), two seeds, 8 s of squeeze each:

| n | seed | p (exact depth after projection) | dL | c = (δ - dL)/(p·L) |
| ---: | ---: | ---: | ---: | ---: |
| 11 | 0 | 9.595e-3 | −1.751e-2 | 0.578 |
| 11 | 1 | 7.192e-3 | −1.333e-2 | 0.611 |
| 18 | 0 | 8.733e-3 | −2.841e-2 | 0.798 |
| 18 | 1 | 6.849e-3 | −1.820e-2 | 0.660 |
| 17 | 0 | 8.644e-3 | −2.760e-2 | 0.784 |
| 17 | 1 | 7.039e-3 | −2.054e-2 | 0.741 |
| 19 | 0 | 5.873e-3 | −1.881e-2 | 0.788 |
| 19 | 1 | 5.491e-3 | −1.396e-2 | 0.708 |
| 26 | 0 | 3.498e-3 | −1.213e-2 | 0.820 |
| 26 | 1 | 1.121e-2 | −3.938e-2 | 0.835 |
| 29 | 0 | 1.724e-2 | −8.098e-2 | 0.830 |
| 29 | 1 | 2.359e-2 | −1.127e-1 | 0.834 |
| 28 | 0 | 1.674e-2 | −6.530e-2 | 0.831 |
| 28 | 1 | 1.597e-2 | −6.202e-2 | 0.829 |
| 27 | 0 | 4.259e-3 | −1.614e-2 | 0.809 |
| 27 | 1 | 1.553e-3 | −2.083e-3 | 0.686 |
| 39 | 0 | 8.659e-3 | −3.809e-2 | 0.796 |
| 39 | 1 | 2.483e-2 | −1.305e-1 | 0.811 |
| 38 | 0 | 2.226e-3 | −6.565e-3 | 0.786 |
| 38 | 1 | 2.570e-3 | −8.842e-3 | 0.776 |

**20 attempts, 20 conversions, 0 positive dL.** The distribution is `dL ∈ [-0.1305, -0.0021]` with median
`-1.881e-2`: every row moved *backwards*, by 2 mm to 13 cm depending on how much overlap the squeeze left.
Summed at the rows' own margins the attempts would cost `-0.1426` of score if promoted.

**Why, in one line.** The squeeze asks for `δ = 4e-3` of side from a pose that section 2 just showed has *zero*
slack, so it can only pay in overlap: `p` is within a factor of two of `δ` in every attempt. The conversion then
pays the legalisation, and `dL = δ - c·p·L` with `c` measured here at **0.578–0.835, median 0.745** — slightly
below doc 87's analytic `0.83` (the difference is the band slides and exact tightening recovering part of the
penalty on the rows where they found something). For any `L > 1.2`, `c·L > 1`, so `dL < 0` no matter how the
budget is spent. The booking is exact: `n = 27` seed 1 drew the smallest overlap (`1.553e-3`), and it has the
smallest loss (`-2.083e-3`) — the ordering of `p` is the ordering of `dL` almost row for row.

**The one regime where a bounded tightening can win** is a pose that already has slack, because then the squeeze's
`δ` comes out of the gap instead of out of overlap and `p ≈ 0`, so `dL ≈ δ > 0`. Section 2 measured that regime
across all 551 rows and found it empty. That is why the pass had no candidate: not because the budget was small,
but because the precondition fails everywhere in the table.

## 4. Verdict

**Nothing promoted. 551 of 551 beaten rows remain jammed** (0 loose, 0 moved), and **0 of 20** rearrangement
attempts produced a positive `dL`. `submission.csv` and root `WHITEBOARD.md` are untouched; the score is
`22.218056945` with 553 beats and 447 unbeaten rows, exactly as delivered. No C1–C4 case was assembled because no
candidate existed to assemble one around.

What this run does establish, and what a future run should not re-litigate:

* The proved-optimal filter costs only **two** rows (`n = 5, 10`); the ranking's other 551 are all genuinely open.
* The room is a **long tail** — 7.8 % in the top ten, `0.42–0.57` per band across 26 bands.
* **There is no free slack anywhere in the delivered table**, exactly: `g* = 1` for every beat, to 40 digits.
* On a jammed pose the squeeze-and-legalise route **cannot** be profitable: it is governed by `dL = δ - c·p·L`
  with `p ≈ δ` and `c ≈ 0.75`, which is negative for every row in the table.
* Therefore a run that wants to move a scored row needs a **constructive** pose at the row's own count (`p_screen`'s
  lesson, restated), not a tightening of the delivered one. Run 131's pocket bound is an example of the right
  question asked at the wrong row; this run is the demonstration that the delivered poses themselves are not the
  seam to open.

## 5. Files, records, checks

* `scripts/beaten_leverage.py` (new; `Decimal` throughout, float only in the binding-pair *proposal*):
  `rank`, `room`, `float_binding`, `pair_ratio_min`, `contract`, `exact_bound`, `certify`, `selftest`, `main`.
* `scripts/tighten.py` (new): `one` (squeeze → measure → convert), `main` with `--rows/--seconds/--seed`.
* `workspace/push/beaten_leverage132.json` — the 551-row ranking, the 2 filtered rows, and the full contraction
  census (551 rows: `g*`, `L0`, `L1`, gain, band, per-chunk counts).
* `workspace/push/tighten132.json` — the 20 attempts with `p`, `dL`, the conversion record and the certificate.
* **Controls.** `beaten_leverage --selftest` **4**: a tight 3×3 grid gives `g = 1` and gain exactly `0`; the same
  grid loosened to spacing `1.05` and `1.25` contracts to exactly the predicted gains `0.1` and `0.5` with
  `g = 1/s` (this control caught the per-axis/per-pair rule error that produced `g = 1.9` on a *legal* grid); the
  real delivered `n = 18` pose (angle `0.424031`, angles present) is legal at 40 digits and gains at most the pad;
  a duplicated cell is refused with one violation at 40 digits.
* Guards green: `range_leverage --selftest` **5**, `construct_seam --selftest` **4**, `band5 --selftest` **4**,
  `ext_census --selftest` **4**, `p_screen` **4**, `legal_slide` **8**, `structure --control`, `--check-solver`,
  `perturb`, `anchor_chain`, `void_insert`, `true_geom`, `sqscore` **22.218056945** (553 / 447), `record_guard` OK,
  `glm_wheels --audit` **684 functions, 0 offenders** (both new scripts are discovery instruments; `tighten.py`
  delegates every comparison to the audited modules), `py_compile` OK.
