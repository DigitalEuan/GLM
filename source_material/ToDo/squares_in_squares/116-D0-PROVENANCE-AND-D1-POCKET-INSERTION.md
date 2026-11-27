# 116 — D0 provenance repair and D1 open-tie pocket insertion

**Run 161 · 2026-11-27 · status: D0 complete and enforced; D1 bounded trials refused at the gate.**
**Instruments:** `scripts/provenance_repair.py` (new), `scripts/open_tie_pockets.py` (new),
`scripts/pocket_insert.py` (new), `scripts/reconcile_table.py`, `scripts/sqscore.py`,
`scripts/packlib.py`, `scripts/true_geom.py`, `scripts/record_guard.py`.
**Ledgers:** `workspace/push/provenance_repair.json`, `workspace/push/open_tie_pockets.json`,
`workspace/push/pocket_insert.json`, `workspace/push/table_before_provenance.json` (backup).
**Untouched:** `workspace/submission/submission.csv`, root `WHITEBOARD.md`. Score unchanged:
**22.217428576459…, 554 beats, 446 ties**.

---

## 0. Result in one paragraph

D0 is done: all **358** stale `table.json` states now hold the CSV pose, `state_src` is set on every
row, and one stale side (n = 90, the post-reconcile promotion) is corrected from `10.0000000018` to
`9.9940387756`. The guard enforces state↔CSV identity, `|extent − L| ≤ 1e-9`, zero overlap at
`packlib.verify`, and an unchanged `sqscore` on all 1000 rows; it is now called by `record_guard.py`, so
it cannot silently drift again. `reconcile_table.py` reads **0 stale sides** and the table's own score
equals the CSV's to 40 digits. D1 then ranked the **293 open ties**: exactly **26** are actionable in the
score-positive sense (their `n−1` is a beaten frontier), led by 656 (pocket 0.762, 4 binders), 56
(0.745, 3), 999 (0.733, 2), and 30 (0.727, 3). Bounded local insertion was run on five of them. Every
trial ended with a small residual overlap or a side at the frontier; **no candidate reached
`packlib.verify` ok**, so C1/C2 were never entered and nothing was promoted. The closest was 29→30:
side 5.966913431 against grid 6, residual 0.006773. The blocking issue for the next run is now explicit:
the exact certificate formats accept `Q`/`Quad(d)` directions, while a delivered mixed pose has
arbitrary angles; a legal float candidate would still need a new interval-trig certification route.

---

## 1. D0 — the CSV is the single source of truth

`provenance_repair.py --write` copied every CSV state into `table.json`, kept `L_model` and `src`, added
`state_src: "submission.csv"` and a per-row `state_digest`, and wrote a backup before touching the file.
It also set `L` from the CSV where it disagreed — one row, n = 90, whose promotion happened after the
last reconcile:

| row | old `L` | CSV `L` | change |
| --- | --- | --- | --- |
| 90 | 10.0000000018 | 9.9940387756 | −0.0059612262 |

`table.meta.json` now records the true score `22.217428576459…`, the preserved historical model
score `22.6459906129…`, gap `0.4285620365`, and **0** stale rows (the pre-repair `357/343` counts are
gone). The guard report (`workspace/push/provenance_repair.json`):

```
rows                 1000
problems             []
changed states       358
changed L            1 (n = 90)
worst |extent-L|     0
worst packlib pen    -6.141354091937501e-11
score                22.217428576459144153…
beats / grid         554 / 446
csv sha256           29d7f43637216599a9982611ff644f987e26a856f75b441f55b10c4087df1990
```

What the guard checks, for every row:

* **G1** exactly n cells and `state_src == "submission.csv"`;
* **G2** float equality with the CSV coordinate triple;
* **G3** `true_geom.side(state)` equals the table `L` at 40 digits, within `1e-9`;
* **G4** `packlib.verify(state)` reports `ok` (zero overlap);
* **G5** `sqscore.guard()` still reads 22.217428576459…, 554 beats, 446 ties.

`record_guard.py` now runs `provenance_repair.py --guard` as its final check, so a future state drift
fails the standing guard rather than only a new instrument. `reconcile_table.py` re-reads the table as
**0 stale sides**, `score over table L == score over true L == 22.217428576459140`, gap `0.000000000000000`.
`frontier_census.py` now reports **0 states differing from the CSV** and no stale frontier rows.

The 358-row classification is unchanged from doc 115: for `k = 21, 22, 24…31` the old state was the
unclosed `k × k` margin grid, for k = 23 and 32 an older mixed pose. `void_insert.load_pose` and every
instrument that imports it now read the delivered pose.

---

## 2. D1 ranking — 293 open ties, 26 actionable

`open_tie_pockets.py` reads the open-tie rows from `target_audit.json`, scans each row's own CSV pose,
and — when `n−1` is a beaten frontier — measures the predecessor pose, because that is the only pose
whose extra cell can **beat** row n. An open tie's own pose sits at `L = k` with `r` unit holes; seating a
cell there only reproduces the tie.

```
open ties: 293
actionable (n-1 beaten): 26
```

Top of the ranking (coarse scan; `pre` is the predecessor pocket, `binds` counts cells whose allowed
half-size at that pocket is < 0.5):

| target n | k | r | predecessor | pre_free | binds |
| --- | --- | --- | --- | --- | --- |
| 656 | 26 | 20 | 655 | **0.761940** | 4 |
| 56 | 8 | 8 | 55 | 0.745472 | 3 |
| 999 | 32 | 25 | 998 | **0.732771** | 2 |
| 30 | 6 | 6 | 29 | 0.726674 | 3 |
| 605 | 25 | 20 | 604 | 0.662199 | 4 |
| 345 | 19 | 16 | 344 | 0.647323 | 5 |
| 557 | 24 | 19 | 556 | 0.613935 | 5 |
| 708 | 27 | 21 | 707 | 0.613805 | 4 |
| 212 | 15 | 13 | 211 | 0.613400 | 2 |
| 424 | 21 | 17 | 423 | 0.592557 | 4 |
| 184 | 14 | 12 | 183 | 0.575620 | 3 |
| 877 | 30 | 23 | 876 | 0.575576 | 3 |

The remaining 14 actionable rows continue down to 0.47; the other 267 open ties have no beaten
predecessor at their `k`, so their own pose is the grid and insertion cannot be score-positive without a
side reduction. The full list is `workspace/push/open_tie_pockets.json`.

The direct measurements at the stated centres (doc 115) are the exact values:
`n = 655` 0.761940 at `(2.38108, 8.38097)`, binds cells 26/29/51/64; `n = 998` 0.732771 at
`(27.59, 0.40)`, binds 848/881. The coarse scan on 998 finds a slightly larger 0.760380 elsewhere; the
direct value is the reproducible one because it carries its centre.

---

## 3. D1 trials — bounded, recorded, refused

`pocket_insert.py` holds the rest of the pose fixed, selects the 4–20 cells nearest the measured pocket,
adds one cell at the pocket centre, and runs multi-start L-BFGS-B on the moved cells plus the new one.
The container is `k − 1e-5`, so any legal pose inside it is a strict beat by 1e-5. Every result is
checked by `packlib.verify`; only a pack-legal result would be passed to `true_geom.check` at 40 digits.

| frontier → target | module | starts × cap | best residual | best side | pack ok |
| --- | --- | --- | --- | --- | --- |
| 29 → 30 (k=6) | 8 | 6 × 12 s | **0.006773** | 5.966913431 | no |
| 55 → 56 (k=8) | 8 | 6 × 12 s | 0.039407 | 7.972801486 | no |
| 509 → 510 (k=23) | 4 | 4 × 12 s | 0.024056 | 22.989777095 | no |
| 655 → 656 (k=26) | 4 | 4 × 12 s | 0.021515 | 25.999711088 | no |
| 998 → 999 (k=32) | 4 | 2 × 20 s | 0.309227 | 31.993087809 | no |

The `56 → 57` run was also made as a control on the **own** pose of an open tie: free side 0.999828,
residual 0.286123, side 8.00000000175, pack no. It confirms the ranking's premise — seating into the
tie's own near-unit hole cannot beat `k`.

No trial reached `pack_ok`, so the exact `true_geom` check, C1 and C2 were not entered. The C4 ledger
records the refusals and the parameters; `workspace/push/pocket_insert.json` holds both. No candidate was
promoted; `submission.csv` and root `WHITEBOARD.md` are untouched.

**What the refusals mean.** The local module is close at 29 (0.0068 residual) and 655/509 (0.021–0.024),
but closeness is not a candidate: `packlib.verify` is the gate, and it says overlap. The near-misses show
the four/eight-cell move is in the right place — the residual is small, not 0.3 — and that the next
attempt should either widen the module (15–20 cells, analytic gradient so the extra variables are
affordable) or seed the freed cells in the surrounding slivers rather than at their current positions.

**The C1 blocker is separate and structural.** The delivered mixed poses carry arbitrary angles
(655: 235 cells above 1e-4, max 23.86°; 998: 317 above 1e-4, 945 angle classes at 1e-9). The exact
certificate formats accept `Q` and `Quad(d)` directions; `true_geom` is a 40-digit measurement, not a
certificate. Even a pack-legal float candidate would therefore stop at C1. The next D1 run needs one of:
an exact-word module (D2), or a rigorous interval verifier for rational angles. This is recorded as a
blocker, not hidden as a failure of the pocket thesis.

No global sweep, no 0°/45° template, and no stale-table experiment was run.

---

## 4. Guards and checks

```
python3 scripts/provenance_repair.py --selftest
python3 scripts/provenance_repair.py --guard
python3 scripts/reconcile_table.py                 # 0 stale; table score == CSV score
python3 scripts/frontier_census.py                 # 0 states differ
python3 scripts/record_guard.py                    # includes the provenance guard
python3 scripts/glm_wheels.py --audit              # 708 functions, 0 offenders
python3 scripts/sqscore.py                         # 22.217428576, 554 beats, 446 ties
```

`provenance_repair --selftest` has four controls: stale-state detection, the extent identity, a planted
overlap refused by `packlib`, and the delivered `sqscore` guard. `pocket_insert --selftest` recovers the
planted 3×3-minus-centre ninth cell. `record_guard` is green on 123 docs, and now refuses if the table
state is not the CSV state.

**Limitations.** The D1 search is float discovery and the module is bounded to 4–8 cells in these
trials; the 20-cell budget has not been run because finite-difference L-BFGS-B is too slow at 27
variables in a 12 s cap. The scan's `own_free` values for grid ties are coarse (0.000 when the grid nodes
miss a unit hole), which is why the ranking uses the predecessor measurements. `n = 998`'s direct pocket
is 0.7328, but the coarse scan found 0.7604 elsewhere; neither is a candidate. No C1/C2 decision was made
because no pack-legal pose exists in the ledger.

---

## 5. What changed, and what is next

**Changed.** `table.json` (358 states, 1 L, `state_src`, `state_digest`), `table.meta.json`,
`record_guard.py` (provenance enforcement), `void_insert.py` (container `k−1e-4`, bbox centring, k=32 CLI
fix), plus the three new instruments and three ledgers. The old table is preserved at
`workspace/push/table_before_provenance.json`.

**Next, in order.**

1. **Certification route first.** Either restrict D1 to exact-word poses (D2) or add a rational-angle
   interval certificate. Without one, a legal D1 pose cannot be promoted, so the search is unadjudicable.
2. **Widen the module with an analytic gradient.** The 29→30 residual is 0.0068; a 15–20-cell module with
   a gradient (or a projection repair after L-BFGS) is the cheapest next test. Keep the 4-cell trial as
   the control.
3. **Do not re-rank the 267 non-actionable open ties as if they were candidates.** Their own pose is the
   grid at `L = k`; insertion reproduces the tie. Only the 26 predecessor rows can move the score.
4. **Keep the provenance guard in every future run.** The 0.9997 sliver cannot recur while
   `record_guard` calls `provenance_repair --guard`.

No promotion; the score and the submission are unchanged. The next run starts from a table whose every
pose is the one the scorer actually reads.
