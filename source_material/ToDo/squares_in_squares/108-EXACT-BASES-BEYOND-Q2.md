# 108 — Exact bases beyond Q(√2), and the beat count the guard could not see (Run 152)

**Two defects, both closed by measurement.** The README's summary table said **553 / 1000** rows beat
the plain grid while `sqscore` reports **554**, and `record_guard` — which exists exactly to stop a stale
total from being read as current — passed it. Nothing in the guard was wrong: its scan is anchored to
*score literals* (`2x.xxxxxx`), so a beat count was never even looked at. Run 152 fixes the record
(README, `STATUS.md` ×2, `REPRODUCE.md`, `00-OVERVIEW.md`) and teaches the guard the second number (R3).

The same run extends the exact base census of doc 107 from the 0°/45° words to the whole degree-2
catalogue — the rational words and every `Q(√k)` word — and re-runs the audit. **33 rows join; 2 of them
turn out not to be exact sentences at all; the audit still finds zero strict beats** in 36,043 candidates
over all 900 rows of 101..1000.

---

## 1. Why the guard missed 553

`record_guard.py`'s two fatal rules both key off `SCORE_RE = 2[0-9]\.\d{5,9}`:

* **R1 currency** — a line asserting current state must quote the delivered score.
* **R2 headline** — a document's first ten lines must quote the delivered score.

Row 90's promotion moved the *score* from 22.218056945 to 22.217428576 and the *beat count* from 553 to
554 in the same commit. Every document that was updated for the score passed both rules; the beat count
in those same tables was invisible, because `553 / 1000` does not match the score pattern and the guard
had no rule mentioning beats at all. So the drift survived a green guard:

| document | line | said | is |
| --- | --- | --- | --- |
| `README.md` | 48 | `Puzzles beating the plain grid \| **553 / 1000**` | **554 / 1000** |
| `STATUS.md` | 386 | same row, plus `Grid-tied \| 447` and `Total improvement \| −6.719613` | **554 / 1000**, 446, −6.720241 |
| `STATUS.md` | 569 | same row | **554 / 1000** |
| `REPRODUCE.md` | 6 | `553/1000 rows beating grid` | `554/1000 ...` |
| `00-OVERVIEW.md` | 14 | `553/1000 rows beat grid` | `554/1000 ...` |

**R3 (new).** A line that counts the beats must quote `sqscore.summarise()`'s own count when it is a
*claim*: a markdown table row, a currency sentence, or a line that names the current score. A line that
names only a **superseded** score is history (the `09-CASCADE.md` quote of the run-38 state stays), and
the `TAGS` opt-out is the same one R1 and R2 use. On the current record R3 flags exactly the three stale
table rows (`README.md:48`, `STATUS.md:386`, `STATUS.md:569`) and passes everything else:

```
[record_guard] delivered 22.217428576, beats 554, rows 1000; scanned 115 docs,
               401 totals, 21 beat counts
```

Its limit is stated rather than hidden: R3 is **line-scoped**, so a sentence that puts the current score
on one line and the beat count on the next (`REPRODUCE.md`, `00-OVERVIEW.md`) is not caught — those two
were fixed by hand and are listed above.

## 2. The word catalogue: what an exact base can be

A row is exact when every cell's angle is a point of the unit circle of degree ≤ 2 over Q
(`scripts/exact_words.py`):

* **Q** — the rational words. Every Pythagorean triple (3-4-5, 5-12-13, 8-15-17, 7-24-25, …) and every
  half-angle parametrisation `t = p/q` → `(cos, sin) = ((q²−p²)/D, 2pq/D)`, `D = p²+q²`. **Quarter turns
  are the axis word**: the unit square is invariant under π/2, so a row turned by π/2, π or 3π/2 is the
  same sentence, not a new one. (Run 151 refused those rows — it tested only 0, π and π/4.)
* **Q(√k)**, k square-free > 1 — the words with `cos²` and `sin²` rational: 45° is k = 2, a lattice
  rotated by `atan(1/2)` has `cos² = 4/5` (k = 5), by `atan(1/3)` has `9/10` (k = 10), 30°/60° has
  `3/4` (k = 3). The word is built exactly by `sqrt(a/b) = sqrt(a·b)/b` with the squarefree part taken
  from an integer, and `c² + s² = 1` is then *checked* in the field before the word is returned.
* **not a word** — any other angle. Its cosine is not this kind of number.

The decision rule is sized to the data, not to taste: `cos²` must be within **1e-10** of a rational with
denominator **≤ 2000**. The CSV's 12-decimal radian angle perturbs `cos²` by ~1e-12, and a random real
misses every such rational by ~1e-7 — so the band is 100× above the noise and 1000× below a coincidence.
`sin²` is not fitted but taken as `1 − cos²` (exact by the circle identity) and must match the measured
value to the same band.

Two guards keep a recovered base honest: the word identity above, and a **reproduction check** — the
rebuilt side must match the delivered side to 5e-9, i.e. the row *is* that sentence and not merely
close to one. And a misidentified word still cannot invent a win: whatever word is used, the pose is a
genuine exact packing and its side is that pose's side, so a strict beat is always a real packing's side.

## 3. The census

| | run 151 | run 152 |
| --- | --- | --- |
| exact bases recovered | 519 | **552** |
| — in Q (rational words) | — | 450 |
| — in Q(√2) | 519 (as "0/45°") | 102 |
| — in Q(√3), Q(√5), Q(√10), … | — | **0** |
| refused: not a declared word | 481 | **448** |
| refused: two different radicals | — | **0** |

The 33 new rows are `19, 26, 50, 66, 85, 104, 125, 149, 171, 174, 198, 201, 202, 230, 231, 262, 296,
331, 369, 408, 449, 492, 493, 538, 585, 586, 634, 635, 678, 679, 686, 853, 974` — quarter-turned rows
(π/2 multiples) and rational-word rows (3-4-5 at row 50, 171, 198, 230).

**Two of them are not exact sentences.** Rebuilt at 45°, rows **678** and **679** overlap by one pair at
clearance **−3.34e-10**: the delivered poses there rest on a 45° block that is off 45° by ~1e-10 rad.
Run 152 gates the extension's 33 inferred sentences before trusting them, so both are **dropped**:

```
new sentences: 33 recovered beyond run 151's rule, 31 pass the exact gate, 2 dropped
               [(678, 1), (679, 1)] (clearance ['-3.34E-10', '-3.34E-10'])
exact bases: 550 of 1000  words {'axis': 446, 'mixed': 104}  fields {'Q': 450, 'Q(√2)': 100}
refused: 450  {'an angle that is not a declared word': 448,
               'the inferred sentence overlaps at the exact gate': 2}
```

**And the other fields are empty — measured, not assumed.** No delivered row anywhere in 1..1000 is a
`Q(√3)`, `Q(√5)` or `Q(√10)` sentence, even though the classifier would have found one instantly (its
controls recover `atan(1/2)`, `atan(1/3)` and 30° from the angle alone). The 448 refusals are not
near-misses: they carry a **median of 71 distinct angle values** (min 2, max 998), which is the
signature of a numerically optimised general-position pose, not of a lattice motif.

## 4. The re-run

```
scale_motifs: 36043 candidates over n = 101..1000, 900 rows reached, 0 strict beat(s)
  A-product      31577 candidates, 900 rows, 0 beats, best margin -1.498e-9  (row 133)
  B-inflate       4348 candidates, 554 rows, 0 beats, best margin +1.936e-9  (row 962)
  C-rot-block      118 candidates,  91 rows, 0 beats, best margin -0.177    (row 106)
```

Against run 151 (33,074 candidates from 519 bases) the extension adds 2,969 candidates and 28 more rows
reached by the cascade, and it changes exactly one frontier side:

| n | delivered | run 151 best | run 152 best |
| --- | --- | --- | --- |
| 500 | 22.850605 | 23.485281 (m = 126, drop 4) | **23.414214** (m = 125, 2×2, no trim) |
| 272 | 16.965586 | 18.000000 | 18.000000 |
| 962 | 31.520815 | 31.520815 (+1.9e-9) | 31.520815 (+1.9e-9) |

Row 125 is one of the newly recovered bases, and its 2×2 product is a *better* candidate at n = 500 than
anything run 151 could build — a direct, visible effect of the wider census. It is still **0.56 above**
the delivered row, so the answer to the brief does not move: on all 900 rows, every candidate in every
family is at or above the delivered side, and nothing is promoted. `submission.csv` and root
`WHITEBOARD.md` are untouched; **22.217428576** (554 beats, 446 ties) stands.

## 5. Controls

* `python3 scripts/exact_words.py --selftest` — **8/8**, 10 decision functions, 0 naming `float`:
  squarefree parts; the Pythagorean words' exactness (`c²+s²=1` in Q); the classifier on the CSV's own
  angles (0 → axis, 0.643501108793 → 4/5, 3/5, 0.785398163397 → 45°); quarter turns as the same word;
  `atan(1/2)`, `atan(1/3)`, 30° recovered into Q(√5), Q(√10), Q(√3); the refusals (a mixed-radical word
  and three non-words); embedding a rational word into Q(√5) and refusing Q(√5) → Q(√3).
* `python3 scripts/scale_motifs.py --selftest` — **13/13**, 25 decision functions, 0 naming `float`:
  run 151's controls 1–8 (the CSV read exactly, the gate, row 20's rebuild, the product and border laws,
  the planted duplicate, both words with their spare area, the margin rule), then row 50 joining as a
  rational-word base, a **3×3 grid at `atan(1/2)` in Q(√5) gating end-to-end at exactly `9/√5`**, the
  mixed-radical refusal by name, and the census (552 recovered, Q 450 / Q(√2) 102).
* `python3 scripts/record_guard.py` — R3 in place; **0 stale totals** after the five fixes above.

## 6. Reproduce

```
python3 scripts/exact_words.py --selftest     # 8 controls, the field catalogue
python3 scripts/scale_motifs.py --selftest    # 13 controls, ~40 s
python3 scripts/scale_motifs.py --promote     # ~3.5 min; 36,043 candidates, 0 beats
python3 scripts/record_guard.py               # R1, R2, R3
```

Ledger `workspace/push/scale_motifs.json` gains `base_fields` (the field census), `refused` (by name),
and `base_gate` (the 33 new sentences and the 2 that overlap).

## 7. What this closes, and what it leaves

**Closed.** (i) The record: the beat count is now checked by the same instrument that checks the score,
and the five stale lines are fixed. (ii) The exact-base question for degree ≤ 2: **550 of 1000 rows are
exact sentences**, and the number is not larger because the table's high rows are general-position poses
(median 71 distinct angles), not because of a missing word — the other quadratic fields are empty in this
table and that is now a measurement. (iii) The audit's negative survives a 6.3 % larger census, with the
one frontier side it moves (n = 500) still 0.56 short.

**Left, declared.** (i) 448 rows are outside the degree-2 catalogue; reaching them exactly needs a
degree-4 tower (mixed radicals — **zero** such rows exist) or a different instrument altogether. (ii) The
new-sentence gate is run over the 33 inferred bases only; the 519 declared ones are not re-gated on every
run (C1 gates whatever would be promoted, from any base). (iii) `record_guard`'s R3 is line-scoped, as
stated in §1 — a score and a beat count split across two lines is a shape it does not catch.
