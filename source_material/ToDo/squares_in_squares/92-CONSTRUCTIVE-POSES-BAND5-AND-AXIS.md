# 92 — Constructive poses: the angle question is closed, band 5 recomputed from scratch, and the 44 "one-axis" rows are not axis-free

**Run 135, 2026-11-25.** Instrument `scripts/construct92.py`; record `workspace/push/construct92.json`.
`submission.csv` and root `WHITEBOARD.md` are untouched: **nothing was promoted**, because no candidate
legalised below its row's delivered side.

**The brief.** Runs 132–134 closed every *tightening* route on the delivered table: `g* = 1` to 40 digits on
551/551 rows, squeeze-and-legalise negative on 20/20, and pure band slides worth at most `5.5e-13` anywhere. The
next budget was to go the other way — **build poses from scratch** at a row's own count, at band 5
(`n = 20..23`, seeking `L < 5`) and/or at the 44 rows whose poses run 134 called "one-binding-axis", with the
explicit hope that a *multi-angle* or *asymmetric* lattice seam could escape the deadlocked
`span_x = span_y = L` shape. This run does all three, and the answer is negative in each case, with the reason
written down exactly.

---

## 1. Family I — the four-corner seam at any exact angle

Four axis-aligned `k x k` blocks in the corners of the box and a strip of `m` unit squares at angle `theta`,
centres one unit apart along the strip's own edge direction, so consecutive strip cells are edge-to-edge
contacts. Doc 47 (run 84) proved this family's 45-degree side to be `2k + m*sqrt2/2`. The question is whether
**another** exact angle is cheaper: the `Q(sqrt 7)` ring direction (`0.424031` rad — the angle the delivered
rows 18 and 55 are actually built at), the `3-4-5` Pythagorean spinor (`36.87 deg`), or `5-12-13`
(`22.62 deg`).

**The side, for every field, is one formula.** With `c = cos theta`, `s = sin theta`:

```
L(k, m) = 2k + 1/(c + s) + (m - 1) * max(c, s)
```

The first term is the two corner blocks on the strip's long axis; `1/(c+s)` is the half-diagonal the first
strip cell needs; every further cell moves the strip one unit along its own edge direction and costs
`max(c, s)` of that axis's room. At `c = s = sqrt2/2` this is `2k + sqrt2/2 + (m-1)sqrt2/2 = 2k + m*sqrt2/2`,
doc 47's number exactly — control 2 pins that equality and, further, that the 45-degree pose is **cell-for-cell
identical** to `mixed_field.strip_sentence`.

**The lemma.** Both terms are minimised at 45 degrees, and 45 degrees is the *unique* minimiser:

```
1/(c + s) >= sqrt2/2   because   (c + s)^2 = 1 + 2cs <= 2,
max(c, s)  >= sqrt2/2   because   max(c, s)^2 >= (c^2 + s^2)/2 = 1/2,
```

with equality in either **iff** `c = s`. Checked exactly (`Fraction` in `Q(sqrt d)`, no float) on all four
words (control 1):

| word | `1/(c+s)` | `max(c,s)` | 45? |
| :--- | ---: | ---: | :--- |
| `45 deg` | **0.7071067812** | **0.7071067812** | yes |
| `ring 24.30 deg (sqrt7)` | 0.7559289460 | 0.9114378277 | no |
| `3-4-5 36.87 deg` | 0.7142857143 | 0.8000000000 | no |
| `5-12-13 22.62 deg` | 0.7647058824 | 0.9230769231 | no |

So no exact-field angle — and no rational spinor — undercuts the 45-degree seam at **any** `(k, m)`. That closes
the "multi-angle / asymmetric seam" hypothesis for this family: the asymmetry that would decouple the two axes
is exactly what makes the word more expensive on its long axis, and the corner blocks cannot buy it back because
their own count is maximised when they are square.

**The certified table** (each pose built at the closed-form side, gated exactly — 0 violations, 0 penetration —
then rebuilt `1/1000` narrower and required to be refused; every row below is `status = certified`, i.e. legal
at `L` and refused at `L - 1e-3`, so the side is minimal to `1e-3` **inside this family**):

| word | `n` | `L` (certified) | grid | gain | `< 5` |
| :--- | ---: | ---: | ---: | ---: | :--- |
| 45 deg | 5 | **2.707106781** | 3 | +0.292893 | yes |
| 45 deg | 17 | **4.707106781** | 5 | +0.292893 | yes |
| 45 deg | 18 | 5.414213562 | 5 | −0.414214 | no |
| 45 deg | 20 | 6.828427125 | 5 | −1.828427 | no |
| ring | 5 | 2.755928946 | 3 | +0.244071 | yes |
| ring | 17 | 4.755928946 | 5 | +0.244071 | yes |
| ring | 20 | 7.490242429 | 5 | −2.490242 | no |
| 3-4-5 | 17 | 4.714285714 | 5 | +0.285714 | yes |
| 3-4-5 | 20 | 7.114285714 | 5 | −2.114286 | no |
| 5-12-13 | 17 | 4.764705882 | 5 | +0.235294 | yes |
| 5-12-13 | 20 | 7.533936652 | 5 | −2.533937 | no |

(the record has all 48 `(word, k, m)` with `k <= 3`, `m <= 4`.)

Three facts fall out, and the first is a **positive control on the whole instrument**: at `(k,m) = (1,1)` the
45-degree family reproduces `s(5) = 2 + sqrt2/2 = 2.707106781`, a *proved* optimum (`optima.py`, Stromquist),
so the assembler is not blind. Second, at the same count the other words are strictly worse: `17` cells cost
`4.7559` (ring), `4.7143` (3-4-5), `4.7647` (5-12-13) against `4.7071` — the ordering the lemma predicts, now
measured. Third, **every word caps at `n = 17` below `L = 5`**, because `n = 18` already needs
`5.414` (45 deg) and more elsewhere. That is run 131's pocket cap restated on a four-word family: the
constructive route cannot reach rows 20–23 at all. `n = 20` in this family costs `6.83` at best — a deficit of
`1.83`, not a rounding.

**Scope, stated plainly.** The minimality here is *inside the family* and certified to `1e-3` by exact refusal,
not by exhaustive search. The count claims are family statements: "the four-corner seam at any of these four
exact words holds at most 17 cells below 5", not "no arrangement holds 20".

## 2. Family II — band 5 rebuilt from scratch

For `n = 20..23` the delivered row is the plain `5 x 5` grid, so a beat means 20..23 cells below `L = 5`, i.e. a
density above `0.8` — **better than the plain grid's own density at that count**, which is why this is hard and
why it is worth measuring rather than assuming. Each count is built from scratch: the `5 x 5` grid with
`j = 25 - n` cells removed in four notch shapes (top rows, corner staircase, centre block, corner block). The
pose is then squeezed and projected with the repo's own loop from an explicit pose
(`p_screen.squeeze_from`, the run-132 instrument for rearranged poses), measured at 40 digits
(`p_screen.measure`) and legalised exactly (`p_screen.convert`: minimum legal scale, void swaps, band ladder,
exact step), which asserts its own output is legal.

| n | notch | squeezed `L` | exact depth `p` | violated pairs | **converted `L`** | `dL` |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 20 | top rows | 4.996213 | 1.195e-2 | 18 | 5.044053 | −4.405e-2 |
| 20 | staircase | 4.996165 | 8.611e-3 | 33 | 5.030757 | −3.076e-2 |
| 20 | **centre** | 4.996038 | **1.465e-3** | 40 | **5.001898** | **−1.898e-3** |
| 20 | corner | 4.996298 | 1.564e-2 | 31 | 5.058075 | −5.807e-2 |
| 21 | top rows | 4.996095 | 4.990e-3 | 30 | 5.015079 | −1.508e-2 |
| 21 | staircase | 4.996201 | 1.286e-2 | 34 | 5.047211 | −4.721e-2 |
| 21 | centre | 4.996292 | 1.512e-2 | 27 | 5.057103 | −5.710e-2 |
| 21 | corner | 4.996118 | 6.653e-3 | 41 | 5.022516 | −2.252e-2 |
| 22 | top rows | 4.996085 | 4.970e-3 | 43 | 5.015976 | −1.598e-2 |
| 22 | staircase | 4.996077 | 4.706e-3 | 40 | 5.014625 | −1.462e-2 |
| 22 | centre | 4.996044 | 1.980e-3 | 47 | **5.003965** | −3.965e-3 |
| 22 | corner | 4.996075 | 3.804e-3 | 41 | 5.011320 | −1.132e-2 |
| 23 | top rows | 4.996061 | 3.266e-3 | 52 | 5.009137 | −9.137e-3 |
| 23 | staircase | 4.996048 | 2.346e-3 | 49 | 5.005439 | −5.439e-3 |
| 23 | centre | 4.996106 | 5.375e-3 | 46 | 5.017689 | −1.769e-2 |
| 23 | corner | 4.996041 | 2.039e-3 | 51 | **5.004200** | −4.200e-3 |

**16 fresh patterns, 0 hits.** Every one legalises strictly **above** `5`, by between `1.898e-3` and `5.808e-2`.
The closest is `n = 20` with the centre notch at `5.001898` — an honest near-miss with exact numbers, and worth
recording as such: the mechanism reaches within `0.0019` of the row and stops on the wrong side. The pattern in
the table is the run-132 law seen from the other end: the squeeze always shaves the full `0.004` request and
leaves `p` of overlap, and the exact conversion pays back a little more than that (`dL = -0.004 + ...`), so the
converted side sits just above the start. `n = 20` and `n = 22` are closest where the removed cells are
*interior* (the centre notch) rather than on an edge — the notch gives the squeeze somewhere to put the overlap
without tilting the outer rows.

**Controls for this pipeline, because a null from a weak instrument is worthless:**

| control | construction | result |
| :--- | :--- | :--- |
| A recovery | a `4 x 4` grid inflated to side `4.2` (gap `0.2`) | converted to **`4.15`**, `dL = +0.05`, certified 0 violations |
| B optimum | the same grid already at `4.0` (`s(16) = 4`, proved) | `dL = -0.002643`, `certified` side `4.002643`, **no gain reported** |

A closes a real gap and returns a legal pose; B refuses to invent a gain at a proved optimum. So the band-5
null is a statement about the patterns, not about a pipeline that cannot legalise.

## 3. Family III — the 44 "one-binding-axis" rows are not axis-free

Run 134 flagged 44 rows as having a single binding axis (`span_x != span_y`), and the brief's premise was that
those rows "permit" a single-axis reduction. Measuring the spans exactly (40-digit `Decimal` from the delivered
pose, `legal_slide.spans`) **corrects that reading**:

| quantity over the 44 rows | value |
| :--- | ---: |
| `L - min(span_x, span_y)` — the *free-axis slack* | |
| smallest (n = 928) | `1.55e-23` |
| largest (n = 934) | **`1.575e-10`** |
| rows below `1e-12` | **41 / 44** |
| rows below `1e-9` | **44 / 44** |

So the second axis falls short of the side by at most `1.6e-10` — the same order as `finalize`'s own pad
(`2e-9` relative, `~6e-8` absolute on a side of 31, and the poses are padded at roughly `1e-10` absolute here).
There is **no geometric room** on the free axis: these rows are square-tied like the other 507, tied to within
the finaliser's noise. That is why run 134's slide search found only `2e-13 … 5.5e-13` on them — it was
measuring the pad, not a free axis. The correct statement about the table is therefore:

> **551 / 551 delivered beats are square-tied to at least `1.6e-10`.** The 507/44 split is a statement about the
> last digit, not about two different geometries.

A from-scratch construction at these counts is also outside this run's budget, and the run records that rather
than claiming it: the exact anchor-closure grammar (run 117's builder) at the rows' own counts and
`L = delivered - 1/1000` places **12 cells of 303 / 330 / 335** at a 12-node cap (37.7 / 38.1 / 37.9 s per row,
`exhausted = false` for all three). That is a *budget measurement*, not a result about the rows: at `n >= 303`
the grammar's node count grows with the pose and 12 nodes is 4 % of one row.

## 4. Verdict

**Nothing promoted.** `submission.csv` and root `WHITEBOARD.md` are untouched; the score is `22.218056945` with
553 beats and 447 unbeaten rows, exactly as delivered. No C1–C4 case was assembled because no candidate existed
to assemble one around: Family I caps at 17 cells below 5 for **every** exact word, Family II produced 16 legal
poses all strictly above 5, and Family III shows the "axis-free" rows have `1.6e-10` of freedom.

What this run settles, and what a later run should not re-litigate:

* **The multi-angle seam is priced and closed.** `L(k,m) = 2k + 1/(c+s) + (m-1)max(c,s)`, both terms are
  `>= sqrt2/2` with equality iff `45 deg`, so 45 degrees is the unique cheapest word at every count. The ring
  (`Q(sqrt 7)`), the `3-4-5` and the `5-12-13` spinors are all strictly worse; measured, not argued.
* **The exact seam family holds at most 17 cells below `L = 5`**, in every one of the four words, matching run
  131's pocket bound on a wider family. 18 cells already need `5.414`.
* **Fresh patterns at the row's own count legalise above 5**, closest `5.001898` (`n = 20`, centre notch), and
  the pipeline is shown to recover a real `0.05` gap (control A) and to refuse a fake gain at `s(16)` (control B).
* **The 44-row split in run 134 is a `1e-10` effect.** All 551 beats are square-tied to `1.6e-10`; there is no
  row in the table where a single-axis move has macroscopic room.

**Where that leaves the next budget.** The constructive family that pays is the one that is *full at the row's
own count* and changes the combinatorics of a boundary row (the notch/insertion route), and the only rows where
a hit would still be worth its arithmetic are the ones whose frontier pose is *not* the delivered beat — which
runs 131–135 have now shown is none of them below `L = 5`. A future run that wants score should attack a
`k = 23` or `k = 32` corner notch (the two real holes: `0.7534` and `0.7171`), where the void is a shape rather
than a squashed cell, and it should expect to spend its budget on construction, not on measurement.

## 5. Files, records, checks

* `scripts/construct92.py` (new; `Fraction`/`Q(sqrt 2)`/`Q(sqrt 7)` throughout, exact comparisons; floats only
  in the repo's squeeze stage and in display): `gate`, `seam_cost`, `seam_side`, `strip_pose`, `family_certify`,
  `lemma_rows`, `family_table`, `band5_best`, `pattern`, `squeeze_fresh`, `band5_run`, `band5_controls`,
  `pocket_control`, `axis_rows`, `axis_census`, `axis_probe`, `selftest`, `main`.
* `workspace/push/construct92.json` — the four words' lemma rows, the 48-row certified family table, the 16
  fresh-pattern attempts (projected side, exact `p`, violated pairs, converted side, `dL`), the two pipeline
  controls, the 44-row exact span census and the three anchored probes.
* **Controls.** `construct92 --selftest` **5**: the lemma on all four words (`1/(c+s) >= sqrt2/2`,
  `max(c,s) >= sqrt2/2`, equality iff 45 degrees); the 45-degree family equal to `2k + m*sqrt2/2` exactly and
  cell-for-cell equal to `mixed_field.strip_sentence`; run 131's pocket cap `17` (604 admissible tuples); a
  duplicate cell refused with penetration exactly `1`; both the 45-degree and ring seams legal at their closed
  form and refused `1/1000` below (`4.707106781` vs `4.755928946`).
* Guards green after the change: `pure_slide --selftest` **5**, `beaten_leverage` **4**, `band5` **4**,
  `ext_census` **4**, `range_leverage` **5**, `construct_seam` **4**, `p_screen` **4**, `legal_slide` **8**,
  `structure --control` / `--check-solver`, `perturb`, `anchor_chain`, `void_insert`, `true_geom`,
  `sqscore` **22.218056945** (553 / 447), `record_guard` OK, `glm_wheels --audit` **0 offenders**, `py_compile`.
