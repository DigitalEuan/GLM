# 71 — Reconciliation, the ε(gap) guard, and coupled angle relaxation

Run 109 ended with a verified certificate that the truth rejected, and with two loose ends: the
repository's per-row sides did not agree with the delivered submission, and the search had never let a
single angle move. This run closes both. Three new instruments — `true_geom.py`, `reconcile_table.py`,
`relax_angles.py` — plus the ε guard inside `semantic_pack.py`. `submission.csv` and the root
`WHITEBOARD.md` are untouched, and no score is claimed.

## 1. `table.json` reconciled: the 22.646 vs 22.218 question is closed

The audit (`reconcile_table.py`) compares every row's `L` in `workspace/submission/table.json` with the
true side of the same row in `submission.csv`, measured at 40 decimal digits by `true_geom` (Decimal
`cos`/`sin` from Taylor series after exact argument reduction — no float anywhere in the audit).

| | |
|---|---|
| rows | 1000 |
| stale (\|L_table − L_true\| > 1e−9) | **357** |
| stale by more than 1e−3 | 343 |
| largest gap | n = 696: table 26.946513936699, true 26.856289410151 (**9.0e−2**) |
| Σ L_table/√n − 1 | **22.645990612927686** |
| Σ L_true/√n − 1 | **22.218056944873789** = `sqscore`'s delivered score |
| gap | **0.427933668053897** |

**The gap is not a discrepancy in the scoring — it is the model error.** `table.json`'s `L` is the side
of the *snapped-word* pose; `sqscore` measures the *true* stored angles. The two totals differ by
exactly `Σ (L_table − L_true)/√n`, which is the number above to fifteen places. Run 108's
`22.645990612927686` was therefore the score of the model table, not of the submission; the delivered
score is `22.218056945`, and now that is what the table produces too.

`reconcile_table.py --write` rewrote the table cleanly: `L` is the true side at 40 digits, the old value
is kept as `L_model`, the provenance (both totals, the gap, the 357 changed rows) lives in
`table.meta.json` beside the table rather than inside it — every reader iterates the table's keys as row
numbers, and a `_meta` key would have broken `face_slide.score_of`. Re-running the audit reports
**0 stale rows and a gap of 0**, and `sqscore` (22.218056945, 553 beats) and `record_guard.py` both pass.

Consequence worth stating: every earlier run compared candidates with `table L`, which for a
transcendental row was an *overstatement* (n = 330: 18.692672 against a true 18.692388). Those
comparisons are now against the true side.

## 2. The ε(gap) containment guard

`semantic_pack.py` now refuses to promote a snapped-model candidate until it has been bounded against
the true geometry:

    ε(gap) = 2 · max_i | θ_i − word(θ_i) |

Each square's half-extent `(|cos t| + |sin t|)/2` has derivative at most 1 in `t`, so snapping a cell
moves its half-extent by at most its gap; the side is `max(x + ex) − min(x − ex)`, so it moves by at
most twice the largest gap. A candidate is promotable only when all three hold:

1. `|L_true − L_model| ≤ ε` — the snap is not hiding something larger;
2. the pose is overlap-free at 40 digits (`true_geom.check`, the real SAT test);
3. the **true** side is strictly below the row's **true** delivered side.

The bars this leaves, per row:

| n | non-word angles | gap | ε | true side | model side must be below |
|---|---|---|---|---|---|
| 11 | 5 / 11 | 2.88e−3 | 5.76e−3 | 3.877083592 | 3.871321392 |
| 17 | 7 / 17 | 3.44e−3 | 6.88e−3 | 4.675530095 | 4.668646323 |
| 18 | 18 / 18 | 1.68e−3 | 3.36e−3 | 4.822875657 | 4.819512197 |
| 29 | 14 / 29 | 3.52e−3 | 7.03e−3 | 5.933833464 | 5.926803177 |
| 330 | 236 / 330 | 6.91e−3 | 1.38e−2 | 18.692388157 | 18.678566016 |

Run 109's artifact is now refused automatically: the n = 330 candidate has model `18.692487647`, true
`18.692915843`, ε `1.38e−2`; it passes the ε budget (the model is 4.3e−4 off) but it is **not
overlap-free at its true angles** and it does not beat the true delivered side, so
`promotable = False`. Re-running the rigid and re-orientation searches on n = 11, 17, 29 under the new
rule gives 0 model wins and 0 promotions. `--guard` prints the table above and the verdict for every
recorded candidate; `semantic_pack --selftest` control 4 fails a gain outside ε and also fails a gain
inside ε that does not beat the true side.

## 3. Coupled position **and** angle relaxation (discovery only)

`relax_angles.py` drops the word restriction for *discovery*: every cell gets `(Δx, Δy, Δθ)` and the
whole configuration is relaxed together by L-BFGS-B on `side + 1e6 · Σ penetration²`, three restarts
from the delivered pose, followed by a second phase that minimises overlap alone (a projection back to
feasibility — a penalty can always buy a shrink with a few overlaps, a projection cannot). Every
survivor is then measured by `true_geom` at 40 digits.

| n | delivered true side | smallest state found | best **legal** state | gain | verdict |
|---|---|---|---|---|---|
| 11 | 3.877083592 | 3.877083545 (11 overlaps) | 3.877083684 | **+9.3e−8** | no improvement |
| 17 | 4.675530095 | 4.675529993 (19 overlaps) | 4.675530462 | **+3.7e−7** | no improvement |
| 18 | 4.822875657 | 4.822875581 (17 overlaps) | 4.822875941 | **+2.8e−7** | no improvement |
| 29 | 5.933833464 | 5.933833380 (41 overlaps) | 5.935805327 | **+2.0e−3** | no improvement |

The pattern is the same on every row and it is the point: **the delivered packings sit exactly on the
feasibility boundary.** Freeing all angles and all positions together buys `5e−8 … 5e−5` of side — and
immediately produces 11 to 41 overlapping pairs. Projecting those back to legality costs more than the
shrink: every legal state the relaxation reaches is *worse* than the delivered one. For n = 11, 17 and
18 the cheapest legal state is within `1e−7` of delivered, i.e. the row is locally optimal to that
precision under coupled position-and-angle moves; n = 29 is locally optimal only to `2e−3`, which is
the one place a deeper search could still have room.

**Discovery and certification stayed separate, as they must.** None of the four rows is close to
word-exact — the largest angle offsets are 0.084, 0.146, 0.361 and 0.364 rad — so nothing found here
could ever carry an exact `Q(√2)` certificate, and by doc 70 §4 no algebraic field can certify these
rows at all (`cos θ` is transcendental for a non-zero rational angle). `relax_angles.py` therefore uses
float arithmetic, is **not** in the float audit, and proposes nothing as certified; the audit covers
`true_geom` (7 functions), `reconcile_table` (6) and `semantic_pack` (36) instead.

## 4. What is and is not claimed

**Claimed.** The table is reconciled with the submission (357 rows corrected, both totals explained,
gap closed to exactly the accumulated model error, all guards green). The ε(gap) guard is in place and
rejects the one artifact the previous run produced. Coupled position-and-angle relaxation — with the
angles genuinely free — finds no legal side smaller than the delivered one on any of n = 11, 17, 18, 29;
the best legal states are `+9.3e−8`, `+3.7e−7`, `+2.8e−7`, `+2.0e−3` above delivered.

**Not claimed.** That these rows are globally optimal — `relax_angles` is a local method (3 restarts,
L-BFGS-B), and the `1e−7` gaps on the three small rows mean "no gain at this precision", not a proof.
Nothing here is a certificate, and `submission.csv` is untouched: no candidate reached a strictly
smaller *true* side with zero overlap, which is the condition for touching it. The other 444
transcendental rows were not relaxed.

**Next.** Apply the same relaxation to the remaining high-slack rows (n = 29 first, where the legal gap
is `2e−3` rather than `1e−7`), and carry the ε budget into any future word-based search so that no model
win can be promoted without surviving the true geometry.
