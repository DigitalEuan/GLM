# 96 — The 17 deltas were drift, and the n = 90 import is real (Run 139)

**Run 139, 2026-11-25.** Instruments `scripts/pub_bounds_check.py` (extended: three-way
`PDF | PUB | live` classification) and `scripts/import_n090.py` (new: the published n = 90
certificate in exact arithmetic); ledgers `workspace/push/pub_bounds_check.json`,
`workspace/push/import_n090.json`; saved sources `workspace/push/pub_frontier100_20261020.pdf`
(sha256 `78677612…3a703`) with its extracted text, `workspace/push/pub_frontier_20261020.html`
(live table), `workspace/push/n090_candidate-reading-copy.json` (the certificate).
**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

> **Run 140 promotion.** Row 90 was written to `submission.csv` in run 140 (doc 97 §1): the
> delivered total is now `22.217428576` with 554 beats, and the room is `1.09584`. The figures
> below are this run's, at that time.

Run 138 attributed 17 bound deltas to my transcription. That was a claim about my own reading, and it
was worth checking before it hardened into the record: if the deltas were the survey moving, the
lesson is different (my `PUB` was a faithful month-old snapshot) from if they were typos (my reading
is unreliable). The same principle governs run 138's one open import: the `n = 90` gain was priced at
`6.28e-4` from a table, and a price is not a packing.

## 1. The correction: 17 deltas, 0 transcription errors, all drift

**Method.** `PUB` was transcribed from the PDF edition. That edition is saved with its extracted
text, so the instrument parses it and compares three numbers per row:

| | source | what a difference would mean |
| --- | --- | --- |
| `PUB` | my transcription | — |
| `PDF` | the edition `PUB` was read from (v0.7.0, **23 October 2026**) | `PDF != PUB` ⇒ transcription error |
| `live` | `frontier.html`, fetched 2026-11-25 | `live != PDF` ⇒ the survey moved |

All three are `Decimal`; the room is computed from `live`, so it does not depend on the
classification. Selftest control 4 checks the PDF's sha256, parses its table (≥190 entries, spot
values `s(12) ≥ 3.971500`, `s(37) ≥ 6.440000`, `s(90) ≤ 10`) and requires `n_transcription == 0`
**and** `n_drift == n_diffs`.

**Result: 0 transcription errors. All 17 are drift.** `PUB` agrees with the 23 October edition on
every number the edition prints; the live table is a month newer. Corroboration the instrument reads
rather than assumes: the live table marks **all 17** rows `recent result` (the survey's own "since
August 2026" badge), and **4 of the 16 lower-bound rises are rows 44, 76, 95, 96 — exactly the four
whose badge changed to *proved optimal* since the edition**, where a proved row's lower bound rises
to its upper bound. The proved set went 45 → 49 in the same month, which is also why four rows left
the room.

| n | field | `PUB` (23 Oct edition) | `live` (25 Nov) | kind |
| --- | --- | --- | --- | --- |
| 12 | lb | `3.971500` | `3.9715` | `3.9716` | drift |
| 19 | lb | `4.825000` | `4.825` | `4.8275` | drift |
| 20 | lb | `4.905000` | `4.905` | `4.9125` | drift |
| 26 | lb | `5.545000` | `5.545` | `5.555` | drift |
| 27 | lb | `5.643500` | `5.6435` | `5.655` | drift |
| 28 | lb | `5.735000` | `5.735` | `5.7425` | drift |
| 29 | lb | `5.810000` | `5.81` | `5.82` | drift |
| 30 | lb | `5.883500` | `5.8835` | `5.8925` | drift |
| 31 | lb | `5.952500` | `5.9525` | `5.9775` | drift |
| 37 | lb | `6.440000` | `6.44` | `6.4975` | drift |
| 39 | lb | `6.650000` | `6.65` | `6.6625` | drift |
| 44 | lb | `6.972500` | `6.9725` | `7` | drift |
| 76 | lb | `8.965000` | `8.965` | `9` | drift |
| 90 | ub | `10` | `10` | `9.9940387665828706` | drift |
| 94 | lb | `9.950000` | `9.95` | `9.972` | drift |
| 95 | lb | `9.965000` | `9.965` | `10` | drift |
| 96 | lb | `9.970000` | `9.97` | `10` | drift |

* **Four are proofs**: `44` `6.9725 → 7`, `76` `8.965 → 9`, `95` `9.965 → 10`, `96` `9.97 → 10` —
  new optimality certificates, so the bound closes on the upper bound.
* **Twelve are tighter lower bounds**: `3.9715 → 3.9716` at `n = 12` up to `6.44 → 6.4975` at
  `n = 37`. Each one makes the true room *smaller* than the figure transcribed in run 137.
* **One is an upper bound where the world moved**: `s(90) ≤ 9.9940387665828706` (jazivxt 2026,
  improved by de Winter, house from 15–21 November) where the edition still said `10`.

The verified room is unchanged at **`1.09647` over 51 rows** — the number never
depended on the attribution, only on reading `live` instead of the edition. What changes is the
lesson: `PUB` is a *snapshot*, not a constant, and any figure quoted from it must be re-derived from
`live` at the moment it is quoted. The instrument now does that and carries the classification, so a
future edition cannot silently re-price the room either.

## 2. The n = 90 import — C1 to C4, by exact arithmetic

**The certificate.** The case record's house carries an *exact rational* reading copy (Squares
Project, `packing/resources/web/de-winter-997-followup-2026-11-21/derived/candidate-reading-copy.json`,
from the author's `n90-rational.zip`, sha256 `c04a0a60…574afa`): 90 rows of

    [cx, cy, tan(theta/2)]

with a rational `center_scale`, so the centre is `(cx/scale, cy/scale)` and the orientation is
`2*arctan(t)`. The decisive fact is arithmetic: for rational `t`,

    cos(2 arctan t) = (1 - t^2)/(1 + t^2),    sin(2 arctan t) = 2t/(1 + t^2)

so the rotation is **rational**, not merely algebraic. Corners, separating axes and the bounding box
are all exact `Fraction`s. There is no float, no `Decimal` and no interval in the decision.

**C1 (proof).** For each of the 4005 pairs, the exact separating slack is the maximum over the four
orientation axes of `|d·a| - r_i - r_j`, all rational:

| quantity | value |
| --- | --- |
| pairs | 4005 |
| overlapping pairs | **0** |
| pairs touching at exactly 0 | **0** |
| **minimum slack** | **`1e-73`** (pair 15,19) |
| bounding-box side | **`9.9940387665828698`** |
| published exact side | `9.9940387665828698` |

The certificate is *strictly* feasible — every pair separated, the tightest by `1e-73`, which is the
record's own `8.994039e-73` contraction showing up as geometry. **C1: PASS, exact.**

**C2 (margin).** Delivered row 90 is `10.0000000019`; the certificate's side is `9.9940387665828698`:

* margin `+5.961235e-3` of side — 8 orders of magnitude above the `1e-12` counting tolerance and
  above the `1e-9` frame padding;
* gain `(10.0000000019 - 9.9940387665828698)/sqrt(90)` = **`6.283693757e-4`**, i.e.
  `22.218056945 → 22.2174286` if the row is promoted;
* rendered the way a delivered row must be (centres `× (1 + 1e-9)`, our own convention, because a
  CSV in decimals cannot keep a `1e-73` contact): 0 overlaps, min slack `1.000e-09`, side
  `9.9940387755769091`, gain **`6.283684276e-4`** — the render costs `9.5e-10` of the `5.96e-3`
  margin.

**C2: PASS, strict.**

**C3 (integrity).** `sqscore` `22.218056945` (553/447), `record_guard` OK, `glm_wheels --audit` 684
functions 0 offenders — all green, and nothing in the delivered table was touched, so the delivered
record still holds while the candidate is priced.

**C4 (honest ledger).** This document, plus `workspace/push/import_n090.json` and the 5-control
selftest: the 5×5 grid (side exactly 5, 72 touching pairs), a displaced square (checked overlap,
`-0.5` slack — the checker is not vacuous), the Pythagorean rotation `t = 1/2 → (3/5, 4/5)` with a
`7/5 × 7/5` bbox, the candidate, and the `1e-9`-rendered candidate.

**Verdict: the `6.28e-4` is real, and now it is a certificate rather than a table entry.**
`6.283693757e-4` exactly, `6.283684276e-4` as a deliverable row.

## 3. Why row 90 is not in `submission.csv` yet

C1–C3 pass, so the gate would allow the write; the write is a different job from the check:

1. **90 rows of geometry** at enough digits: `x`, `y` and `angle` from exact rationals. With the
   `1e-9` render the pose is legal with `1e-9` slack, so ~18 significant digits suffice for the
   CSV, and `angle = 2*arctan(t)` in degrees must be rendered consistently for all 90 cells.
2. **The delivered record moves**: `DELIVERED_SCORE` `22.218056945 → 22.2174286` in `sqscore`, the
   quoted totals in `record_guard`, and the §1 figures in `README`, `STATUS` and this register —
   one commit that is mostly a constant cascade, and every one of those numbers must move together.
3. **The room moves with it**: `1.09647 → 1.09584` over the same 51 rows (row 90
   stays above its `9.73` lower bound, it just contributes less).
4. **Attribution is part of C4**: the row would be our own repack of jazivxt's and de Winter's
   geometry, and the ledger must say so plainly — the packing is theirs, the certificate is theirs,
   and what this run adds is the independent exact verification and the `1e-9` render.

That is a mechanical, single-row promotion with a sizable constant cascade. It is queued, not
sneaked in behind a verification run.

## 4. What this changes in the register

| said | verified |
| --- | --- |
| 17 deltas were transcription errors, 16 of them from rounded PDF text | **0 transcription errors; all 17 are survey drift in the month since the 23 Oct edition** |
| PDF edition dated 2026-10-20 | **v0.7.0, 23 October 2026** (file name `…20261008.pdf`) |
| `n = 90` worth `6.28e-4` from the table | **`6.283693757e-4` exact, `6.283684276e-4` rendered — C1 and C2 PASS** |
| room `1.09647` over 51 rows | unchanged (it is computed from `live` either way) |

## 5. Next

1. **Promote row 90** (§3): the only certified gain on the table, ~`6.28e-4`.
2. Re-derive the room and the §1 record after the promotion; the world-record bands (`k = 4, 5, 7`)
   are untouched by it.
3. Nothing else from a bounds table without a certificate behind it.

**Checks.** `import_n090 --selftest` **5**; `pub_bounds_check --selftest` **4** (now including the
three-way classification); `glm_plan --selftest` **5**; `witt_octad --selftest` **5**; the full guard
set green (`notch136`, `pure_slide`, `beaten_leverage`, `band5`, `ext_census`, `range_leverage`,
`construct_seam`, `p_screen`, `legal_slide`, `structure --control` and `--check-solver`, `perturb`,
`anchor_chain`, `void_insert`, `true_geom`); `sqscore` **22.218056945** (553/447); `record_guard` OK;
`glm_wheels --audit` **684 functions, 0 offenders**; `py_compile` OK.
