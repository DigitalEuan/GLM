# 69 — the face slide, the high-slack rows, and the exact score (run 108)

Doc 68 §4 ended with one untested move: a **face slide**, every cell that realises one side of a
certified row's bounding box translated inward by a common exact `t`. Run 107 could see the room
(each face cell had a positive corridor) and still measured `dL = 0` for every single-cell and
two-cell chain; this run explains why, and settles the slide exactly.

The instrument is `scripts/face_slide.py` (4 controls, 27 decision functions, float-free, in the
`--audit` list). Its three parts are one exact interval question, one ranked constructive attack,
and one exact summation.

## 1. The face slide is legal, and a single face changes nothing

For a face `F` (the cells realising `lo_x`, say) and the inward direction `d`, the feasible set of a
common translation `t d` is an interval `[0, T]`. For a moving cell and a fixed one, each of the
pair's eight axes is separated at `t = 0` with slack `s` and fails at `s/|d·q|` if the motion
narrows it, or never if it widens it; the pair survives while *some* axis survives, so its cap is
the largest such failure time, and `T` is the smallest pair cap over the face. Axes that are not
separated at `t = 0` are skipped — they cannot hold the pair at zero, and they cannot extend the
component of `t = 0` either. (Run 106's `wall_room` treated a negative axis as an immediate block;
control 1 of doc 68's instrument pinned that error on an exact knight pair.)

| row | `L` (delivered = exact) | `lo_x` | `hi_x` | `lo_y` | `hi_y` |
|---|---|---|---|---|---|
| n = 66 | `4328427125631/500000000000` = 8.656854251262 | 7 cells, `T = 231/10^12`, binds (0, 1) | 8 cells, `T = 231/10^12`, (15, 16) | 8 cells, `T = 231/10^12`, (15, 21) | 7 cells, `T = 231/10^12`, (0, 5) |
| n = 325 | `741421356313/40000000000` = 18.535533907825 | 18 cells, `T = 27/250000000000`, (97, 3) | 18 cells, `T = 27/250000000000`, (107, 90) | 18 cells, `T = 27/250000000000`, (102, 0) | 18 cells, `T = 27/250000000000`, (112, 93) |

So the faces are **not** jammed: every one of the eight has strictly positive room, `231/10^12` at
n = 66 and `27/250000000000` at n = 325, and sliding a face by its own `T` gates clean with the
binding pair at exact contact. And yet **one face slide changes `L` by exactly zero**. The reason is
the shape of the container: `L` is the larger of the two extents, and both rows are (to the
delivered precision) square — `lo_x = lo_y` and `hi_x = hi_y` — so pulling one face inward leaves
the *other axis* defining the side. This is the missing half of doc 68 §2's observation: the face is
multiply defined, and the container is too.

Sliding **both faces of one axis** shortens that axis by their two rooms at once; alternating axes
then lets the other one bind. That is the whole squeeze, and it works:

| row | four slides | `dL` | new `L` | gate | certificate |
|---|---|---|---|---|---|
| n = 66 | `lo_x, hi_x, lo_y, hi_y`, each `231/10^12` | `-231/500000000000` = **−4.62e−10** | `21642135627/2500000000` = 8.6568542508 | clearance 0 | **verified** |
| n = 325 | same four, each `27/250000000000` | `-27/125000000000` = **−2.16e−10** | `18535533907609/1000000000000` = 18.535533907609 | clearance 0 | **verified** |

The same squeeze on the **33 exact-worded rows with n ≤ 40** (the fast part of the census) gives
**31 shrinking rows**, every one of them with a verified certificate at clearance 0 and with the
total `Σ dL = -26881/10^12 = -2.6881e-8`; the pattern is unmistakable — n = 2 goes from
`2000000001/1000000000` to exactly `2`, n = 6, 7, 8 from `3000000001334/10^12` to exactly `3` — the
slides remove the `1e-9` polish face by face. Two of the 33 have no room at all (`T = 0` on every
side: their faces are already in exact contact).

**Both certified sides shrink, and both moved states carry verified certificates at clearance 0.**
The gain is exactly the sum of the four face rooms, and those rooms are exactly the `1e-9` polish
that the delivered decimals carry: 4.62e−10 at n = 66 and 2.16e−10 at n = 325. It is a genuine
strictly-smaller *side* — the certificate closes at clearance 0 and `verify_certificates.py` accepts
it — but it is a **rounding-scale** gain, not a packing gain. Nothing about the arrangement
improved; a strip of the safety margin between "exact contact" and "delivered decimal" was spent.

## 2. The high-slack rows: ranked, and attacked

Run 106 certified 552 of the 1,000 rows. The other **448** are the corpus's uncertified classes
(doc 65): **424 relaxed** rows — at least one transcendental angle, so no exact class is searched —
and **24** with an algebraic side but no lifted pose. They are ranked by their own Kaggle
contribution `L/√n − 1` (exact, in rigorous intervals), with the void `L² − n` recorded beside it:

| rank | n | `L/√n − 1` | `L` | void `L²−n` | source |
|---|---|---|---|---|---|
| 1 | 11 | 1.168985 | 3.877083592 | 4.0318 | `aux:square-11.svg-0` |
| 2 | 18 | 1.136763 | 4.822875657 | 5.2601 | `exact:square-18.svg` |
| 3 | 17 | 1.133983 | 4.675530095 | 4.8606 | `exact:square-17.svg` |
| 4 | 29 | 1.101885 | 5.933833464 | 6.2104 | `exact:square-29.svg` |
| 5 | 28 | 1.100717 | 5.824444618 | 5.9242 | `exact:square-28.svg` |
| 6 | 39 | 1.090588 | 6.810722085 | 7.3859 | `exact:square-39.svg` |
| 7 | 37 | 1.084806 | 6.598619611 | 6.5418 | `exact:square-37.svg` |
| 8 | 41 | 1.081768 | 6.926693096 | 6.9791 | `exact:square-41.svg` |
| 9 | 53 | 1.074555 | 7.822875657 | 8.1974 | `exact:square-53.svg` |
| 10 | 55 | 1.071408 | 7.945771009 | 8.1353 | `exact:square-55.svg` |
| 11 | 54 | 1.067796 | 7.846667195 | 7.5702 | `exact:square-54.svg` |
| 12 | 68 | 1.067011 | 8.798795239 | 9.4188 | `run18-frontier` |
| 13 | 69 | 1.062669 | 8.827194658 | 8.9194 | `exact:square-69.svg` |
| 14 | 70 | 1.061478 | 8.880960373 | 8.8715 | `run18-frontier` |
| 15 | 71 | 1.061466 | 8.944071559 | 8.9964 | `exact:square-71.svg` |

All fifteen are small or medium rows whose side sits far above the area bound — exactly where a
rearrangement has the most to gain, and exactly where the corpus's angles are transcendental.

**The attack.** For each of the fifteen: snap every stored angle to the nearest exact word (the
worst gap is 3.4e−3 rad, so these are *new* packings, not the delivered one), survey in the exact
field, repair each overlap by the smallest exact slide (`repair_step`), slide to the tightest
contact, then run the face-slide squeeze of §1, and certify whatever is clean at clearance 0.

| outcome | rows |
|---|---|
| certified at clearance 0 | 3 (n = 11, 17, 41) — **all worse** |
| repair stalled with violations left | 12 |
| strictly smaller `L` than the delivered row | **0** |

The three that certify are worse than the delivered row, by exact amounts:

| n | certified `L` | delivered `L` | `ΔL` |
|---|---|---|---|
| 11 | `12821760635589947/3305125000000000` | `1938541795753/500000000000` | `+6011784170943/2644100000000000` = **+2.27e−3** |
| 17 | `3158778935434117/675500000000000` | `584441261897/125000000000` | `+458356142729/675500000000000` = **+6.79e−4** |
| 41 | `758339900877/109375000000` | `346334654809/50000000000` | `+11725495717/1750000000000` = **+6.70e−3** |

None of the three admits a face slide afterwards (`compress` finds `T = 0` on all four sides), so
each is a genuinely tighter but *worse* packing of its row: the word lattice moves 3.4e−3 radians
away from the delivered angles and loses more than the slide can recover. The other twelve do not
even reach a legal pose — the lattice is too coarse for their transcendental carriers, and the exact
repair runs out of single-cell slides:

| n | violations at start → end | | n | start → end |
|---|---|---|---|---|
| 18 | 16 → 14 | | 54 | 26 → 16 |
| 28 | 16 → 15 | | 55 | 17 → 16 |
| 29 | 20 → **1** | | 68 | 52 → 50 |
| 37 | 20 → 13 | | 69 | 24 → 15 |
| 39 | 21 → 7 | | 70 | 32 → 29 |
| 53 | 24 → 13 | | 71 | 31 → 30 |

## 3. The exact metric

The metric is `score = Σ_n L_n/√n − 1` over the 1,000 rows (`scripts/deliver24.py`'s own formula),
lower is better. Each term is bounded rigorously with integer square roots — `isqrt` at scale
`10^40`, both roots bracketed, so the whole sum is an interval that provably contains the true
value; no float, no Decimal and no tolerance appears anywhere in the decision path. Over the
delivered table the formula gives

```
score_before = 22.645990612927686   (bounds agree to 15 places; the float recomputation
                                     scripts/deliver24.py does gives 22.64599061292769)
```

(Note the honest discrepancy: the repo records the *leaderboard* number **22.218056945** as
"delivered", and the local formula over `table.json` does not reproduce it — it differs by 0.428.
The **delta** does not depend on that constant: any linear score in `L` changes by
`Σ (L*−L)/√n` over the changed rows.)

With the 33 verified improvements of §1 — the two named rows included — the exact bounds are

```
score_after = score_before − 0.000000007885757   (both bounds identical to 15 places)
Δ           = −7.885757e−9
```

so the total metric strictly improves, by **7.9 × 10⁻⁹**. That is the whole gain: thirty-three rows
each shedding `1e-9`-to-`1e-10` of polish, and eight other rows (n ≤ 40 with no face room) plus the
448 uncertified rows unchanged. The candidate is in `workspace/push/submission_candidate.csv` — the
**1,026 changed square rows only**, as a patch of the delivered file, with coordinates rounded to
twelve places; every one of the 33 rounded states was **re-gated exactly** and still clears at
`clearance ≥ 0` (`rounded_regate` in `workspace/push/face_slide.json`), so the patch is
submission-safe.

**The decision.** `submission.csv` is **not** updated. The improvement is verified and strictly
positive, but it is entirely the `1e-9` safety polish that the delivered coordinates carry, not a
smaller packing: no row's arrangement improved, the wave of `−7.9e−9` is five decimal places below
the delivered sides' own precision, and the candidate patch is left on disk for the user to apply in
one command if they want it. A genuine packing gain — one that moves a side by more than the polish
— was not found by any of the three searches this run.


**What is and is not claimed.** The face slide is settled: on both named rows every face has
positive exact room, a single face cannot lower a square side (the container is square and the other
axis binds), the two-face squeeze can, and both rows shrink by exactly the sum of their four rooms
with **verified** certificates at clearance 0 — `−4.62e−10` at n = 66 and `−2.16e−10` at n = 325.
Thirty-one of the 33 exact-worded rows with n ≤ 40 shrink the same way, for a total exact metric
gain of `−7.885757e−9`. The high-slack rows are ranked and attacked: three certify (all worse, by
`+2.27e−3`, `+6.79e−4`, `+6.70e−3`), twelve stall, **none** improves, so the 448 uncertified rows
remain uncertified and their delivered sides stand.

**Not claimed:** that any row gained a *packing* improvement — every verified shrink is the
`1e-9`-scale polish, and removing it moves the metric by 7.9e−9, not by anything the leaderboard
would call a gain. The 553-row census sweep is **not** complete: the sweep over all exact-worded
rows is ~2 s a row (the large 45°-heavy rows dominate), so this run measured the 33 rows with
n ≤ 40 plus the two named rows and stopped there rather than run for an hour; the remaining 518
worded rows are untested and are the next run's first task. `submission.csv` and the root
`WHITEBOARD.md` are untouched.
