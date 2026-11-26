# DIRECTORS-NOTE — the standing perspective for every run

> **Read this first, every iteration.** It states what we are doing, what "no floats" means here, what is
> already proved (so it is leverage, not blinders), where the open leads are, and the gate any result must
> pass before it is promoted. The run ledger (`04-RUN-LOG.md`) is the history; this card is the *standing
> intent*.
>
> **Provenance.** Added 2026-11-24 (run 116) from the CEO executive memory card, reviewed line by line against
> the repository. The review found **one factual error**, corrected below and marked **[corrected]**; every
> other number was confirmed and is cited to its source. A run that changes one of these numbers must update
> this card in the same commit.

## Review of the card (run 116)

| claim | verdict | source |
| --- | --- | --- |
| score `22.217428576`, 554 rows below `ceil(√n)` | confirmed (re-checked after the run-140 n = 90 promotion; was `22.218056945`, 553) | `sqscore.py` `guard()` |
| 446 rows tied to `L = k` (the standard grid), 30 bands `k = 3..32` | confirmed (446 includes n = 1; 445 at n >= 2; row 90 left the grid ties when it was promoted in run 140; 30 frontier bands, band 32 clamped at n = 1000) | doc 75 §2, run 115 |
| 303 tied / 21 ahead / 0 behind the Squares Project catalogue | confirmed (303 equal, 21 ahead by `0.006414`, 0 behind) | doc 75 §1 |
| 552 rows hold standalone zero-clearance `galois-certificate/1` proofs | confirmed (552 of 554 beaten rows certified; the promoted row 90 carries the project's exact rational certificate instead, re-verified by `import_n090.py`) | `verify_certificates.py`, run 106 |
| 613 core decision functions, 0 float offenders | confirmed | `glm_wheels.py --audit` |
| **"Grid-frontier rows (`n = k² − 1`) are uniformly compressed"** | **WRONG** — the frontier row of band k is `m* = k² − j*` with `j* = 18…26` at `k >= 21` (e.g. band 23: `m* = 509`, `j* = 20`; band 32: `m* = 998`, `j* = 26`). `n = k² − 1` is not a frontier row anywhere in the table | doc 75 §2 |
| free cell `0.9994–0.9999` at the compressed frontier | confirmed (and equal to `1 − (k−L)/k` within `6e-4` in ten of eleven bands) | doc 75 §3, `void_insert.py` |
| real corner notches `k = 23` (`0.7534`) and `k = 32` (`0.7171`); `n = 999` costs `+0.120` | confirmed (`+0.1195` for the k = 32 next row) | doc 75 §2–§3 |
| Block45 / Block45Half / ridge beat the grid on 369 already-beaten counts, and come within `+0.0711` on n = 212, 242, 243, 244 | confirmed (0 of 444 unbeaten rows beaten; median deficit `+0.6066`) | doc 75 §6, `grid_families.py` |
| `1e-9` face-squeeze saved `−7.89e-9`, `submission_candidate.csv` only | confirmed | run 108 |
| fixed-box `3×3` (`6 → 7`) block swaps blocked by `s(7) = 3` | confirmed (short by `2.2e-5…8.9e-5`, proved impossible) | doc 75 §5, `block_swap.py` |

**[corrected] in §2 below.** The compression statement is about the *frontier pose* of each band, not about
`n = k² − 1`, and its operative content is: the largest square that fits that pose's free space is
`0.9994–0.9999` of a cell, i.e. every void in it is a squashed unit cell.

---

# CEO EXECUTIVE MEMORY CARD — SQUARES IN SQUARES (GLM)

**First-Time Orientation — What We Are Doing:**
We are developing the **Geometric Language Machine (GLM)** and testing it on the 1,000-row *Squares in
Squares* packing problem (`n = 1..1000` unit squares in a minimal square of side `L`). The Kaggle leaderboard
score is a **public, falsifiable proof of progress — not a ceiling**: better packings exist, and our goal is to
discover genuine geometric/algebraic structures that beat our current `22.217428576` baseline (`554` rows below `ceil(√n)`, `446` rows currently tied to the `L = k` standard grid; `30` bands `k = 3..32`; `303` tied
and `21` ahead of the Squares Project catalogue, `0` behind).

## 1. CORE OPERATING DEFINITION: "NO FLOATS" (GLM NATIVE WORK)
- **What "No Floats" Means Here:** Any operation that introduces rounding drift **or** hides its reasoning
  behind an external black-box dependency. Every core calculation must **"show its work"** explicitly and
  immediately using native exact structures (`fractions.Fraction`, integer arithmetic, `math.isqrt`, exact
  algebraic fields `Q`, `Q(√2)`, `Q(√5)`, `Q(√7)`).
- **Discovery vs. Proof:** Untrusted float heuristics may explore freely to propose leads, **never** to claim a
  result — every candidate must translate into exact/interval proof before promotion. Discovery instruments
  live outside the audit by design (`relax_angles.py`, `pattern_seeds.py`, `void_insert.py`, `block_swap.py`,
  `grid_families.py`, `resqueeze.py`); the certification side (`true_geom`, `verify_certificates`,
  `interval_verifier`, `semantic_pack`, `sqscore`) stays float-free and byte-audited.

## 2. WHAT IS PROVED SO FAR (USE AS LEVERAGE, NOT BLINDERS)
- **Certified Ground Truth:** `552` rows hold standalone zero-clearance `galois-certificate/1` proofs
  (`verify_certificates.py`); `613` core decision functions pass `glm_wheels --audit` (`0` float offenders).
- **Structural Measurements (`docs 72–75`):**
  - *All-lattice ceiling (`T1`):* any pure integer-lattice pose needs `L ≥ ceil(√n)`; beating a grid row
    requires tilted cells or non-lattice seams.
  - *Solid-wall fringe cap (`T2`):* a one-cell tilted fringe glued onto a solid upright wall holds at most
    `floor(L)²`.
  - *Compression wall (`k >= 21`):* **[corrected]** the *frontier pose* of a band (`m* = k² − j*`,
    `j* = 18…26`) is a uniformly compressed lattice — the largest square fitting its free space is
    `0.9994–0.9999` of a cell, equal to `1 − (k−L)/k` within `6e-4` in ten of eleven bands — so every void in
    it is a squashed unit cell, not a hole. **Two bands are real corner notches:** `k = 23` (`0.7534` hole)
    and `k = 32` (`0.7171` hole; its next row `n = 999` costs only `+0.120` to crack, the cheapest large-band
    price in the table).
  - *Existing family baseline:* `Block45`, `Block45Half` and `ridge` beat the grid on `369` already-beaten
    counts and come within **`+0.0711`** of beating it on four near-miss rows (`n = 212, 242, 243, 244`);
    on the `444` unbeaten rows they cover, they beat the base **zero** times (median deficit `+0.6066`, max
    `+0.7071 = ½√2`).
  - *Prior low-yield paths (deprioritize unless a new structural angle opens them):* `1e-9` face-squeeze
    micro-polishing (`−7.89e-9` saved in `submission_candidate.csv`), local L-BFGS-B nudging on
    `submission.csv` poses, fixed-box `3×3` (`6 → 7`) block swaps (`s(7) = 3`, short by `2.2e-5…8.9e-5`),
    and unguarded angle snapping (`ε(gap)` catches model artifacts).

## 3. WHERE TO AIM NEXT (OPEN LEADS FOR REAL MOVEMENT)
1. **Dynamic Re-Squeeze Block Substitution (`run 116`):** replace `pq` cells with `pq + 1` at larger pitch
   *while allowing the surrounding pose to expand and re-squeeze*, so compression redistributes globally
   rather than locally. Instrument: `resqueeze.py` (patch-coordinate relaxation with a container hinge).
2. **Notch-Band Rearrangements (`k = 23`, `k = 32`):** exploit the real `0.7534` and `0.7171` corner holes
   (`n = 999`, the k = 32 next row, is the lowest-cost large-band breakthrough at `+0.120`).
3. **Near-Misses & Interior Seams:** push the four `+0.0711` `Block45` near-misses (`n = 212, 242, 243, 244`)
   and **interior tilted seams** (`(Z + 4/7)²` / rational-sheared interfaces where tilted cells interlock
   inside a seam rather than on a solid wall), and unify `verify_certificates.py` (exact contact) with
   `interval_verifier.py` (rational enclosure). **Run 140 closes the butted variant of this lead:** two
   rigid blocks joined along a straight interface have an integer side `max(a1, b1, a2 + b2)` and
   `n = a1a2 + b1b2 <= max(a1, b1)(a2 + b2)`, so the family is floored at `ceil(sqrt n)` and can only tie
   the grid; 935,520 spinor/gap/split candidates confirm it (`twin_boundary.py`, doc 97 §3). What remains
   open is the *interleaved* interface — cells of both lattices owning area on both sides of the seam —
   which no butted family can express. **Run 141 has now measured it** (`interleaved_boundary.py`,
   doc 98): the interleaved constructor beats the butted bound (7.2000 against 8.2000 on its positive
   control) but loses to the grid on all three small high-room targets — 270,000 placements, 250,221
   exact-count assemblies, best sides `5.000000 / 5.000000 / 8.000000` against delivered
   `4.822876 / 4.885618 / 7.690356`, every winner at the degenerate spinor `1/1`. The reason is exact:
   a `b1 x b2` grain at spinor angle `theta` has `W H >= b1b2(1 + sin 2theta)`, so it can only pay for
   itself under `sqrt(m(1+sin 2theta)) - sqrt(m) < 1` — at most 6-17 cells for `q <= 4`, where a 49-cell
   grain is priced out. **Run 142 has now audited that inequality across all 1,000 rows**
   (`tilt_audit.py`, doc 99): every one of the 446 ties is a single-class axis pose with **zero**
   tilted cells, while **508 of the 554 beats carry a class the inequality prices out** (43,144 of
   their 125,490 tilted cells) — so the price does not separate ties from beats. It does not,
   because the rejected classes do not own their bounding boxes: in the 110 two-class beats the
   tilted class's bbox is filled to a median **0.937 of the container's own density**, i.e. the
   other lattice is inside it. **The lever is area sharing between two whole lattices** (a
   shared-box interlock), not many short grain contacts and not a better line; the two-grain
   statement holds only for poses that must give the grain its own box (doc 99 §8-§9).
   **Run 143 has now built that constructor and refused it** (`shared_box.py`, doc 100): two whole
   rectangle blocks in one shared box, closed-form contact side, 9 controls, entry test first —
   **0 of 110** delivered two-class `(n, side)` pairs reproduced, the closest pose a plain grid split
   in 110/110, the family never below the grid, because a full block fills its own bbox and two full
   blocks can only share the *container*. Area sharing needs a **sparse carrier**: 0/110 delivered
   two-class rows are two single lattices, and their larger class is a union of 4–54 translates.
   The lever stands; the carrier is not a rectangle.
   **Run 144 has now built the sparse carrier and refused it too** (`seam_carrier.py`, doc 101): two
   axis runs per axis across a seam of `s·w` plus a centred 45° bar, cells dropped where they touch the
   bar — **9 controls**, fill **0.68–0.73 < 1**, axis **2–4** / tilt **1** translation domains, one
   legality path (`check` → `gate`, no pre-filter), and an
   entry test of **2 of 110** (threshold 20) with the bar searched over `m_hint ± 2` (cap `90 → 330`), the
   two calibration atoms `n = 5` and `n = 10`. **30** rows
   hit the delivered side *and* count, but **28** of them are refused by the exact gate: the notch only
   removes what the bar covers, so a notched **product** shares with the bar and not with itself. The
   ±2 window adds five of those refusals (`n = 40, 492, 585, 634, 909`, five at a non-hinted bar size)
   and refuses all five, so the refusal is the family's and not a one-bar-size artefact. The
   next carrier must be sparse **by construction** (disjoint translates by a law) or the notch must gain
   authority over carrier-carrier overlap with a count-preserving repair.
   **Run 145 built that carrier; its entry test FAILS at 19 of 110** (`block_bed.py`, doc 102) — one
   short of the 20-row gate. (Run 145 first claimed 48/110 PASS; that was a counting defect —
   a split table that did not shift its windows and took the wrong end of run 2, plus an entry test
   that never compared the gated pose's count with `n` — retracted in run 146, doc 102 §8.) The
   two runs of each axis are separated by a **positive gap** `g = L − K > 0` instead of an interlock,
   so carrier–carrier overlap is impossible by arithmetic — for any gap and any split — and the two
   axes' splits are **independent** (`kx ≠ ky` is the general case); the tilted class is a **centred
   p×q block** and a carrier cell is dropped iff its interior meets the block, one four-inequality SAT
   against the whole block rather than a pair scan. **10 controls**, **22** float-free decision
   functions, fill **0.68–0.91 < 1** (carrier **0.40–0.55**), domains axis **4** / tilt **1**. The
   entry test reaches **19 of 110** delivered two-class `(n, side)` pairs (threshold 20) with **0 gate
   refusals**, and every hit is a **symmetric** declaration (`kx = ky = K/2`) with a square block: the
   family reproduces the table exactly where the table is symmetric, and the free split is not the
   decisive parameter — the **count** is. What remains is arithmetic, not geometry: **28** rows are
   outside the side group `a + (s/2)√2` and **63** are inside it with no declaration at their count.
   **No sweep is authorised** (19 < 20); the question a sweep would ask — "can it reach a row's count
   at a side below the delivered one" — is instead put directly to the family by the beat probe of
   run 146 (doc 103), because the area bound `L*L >= n` collapses the side axis to the window
   `[√n, L_del)` and turns the sweep into a visit. **Run 146 ran that probe: 0 beats in 949,243
   (side, K, shape) trials over all 110 rows, with the sensitivity control re-finding 19/19 ties at
   their own sides.** So the family only explains the table — 19 tied, 0 beaten — and no parameter of
   it moves a side down: **do not sweep it.** The two directions the probe prices are `r` runs per axis
   (same disjointness law, `r − 1` gaps, a bigger count surface) and a rational-`b` side law `a + b√2`
   for the 28 rows outside the halves group.
   **Run 147 answered both, and audited the instruments.** `r` runs per axis (`block_bed_r.py`, doc
   104): `r = 2` is run 145's symmetric split exactly and reproduces **19/19** of its rows at **19/19**
   declarations; `r = 3..6` adds **0** rows at the delivered sides and **0** beats below them on the 19
   reach rows (183 windows, 124,176 trials, control re-finding 19/19 ties) — **more translates buy no
   reach**, because the gap `(L − K)/(r − 1)` shrinks as `r` grows and the block beds more of the
   carrier, not fewer. The same visit audited every claiming instrument for run 146's defect class:
   `seam_carrier` (a gated pose counted without its count), `shared_box` (accepted on overlaps alone,
   and a `beats_family` count with **no pose built**), `motif_wheels` (a state gated without carrying
   `n` cells), `ext_census` (a side written without the pose's count) — all repaired, **no published
   number moved**.    The rational-`b` side law is the direction left.
   **Run 148 has now swept the family instead of probing it** (`carrier_ceil.py`, doc 105). The count
   is a step function of the side (each carrier cell is bedded on one open interval of sides), so the
   whole `(side, count)` surface is a finite union of open intervals, computable exactly: **0 beats in
   25,935 declarations at `n ≤ 100`** (16 rows tied exactly: 20, 30, 40, 42, 56–58, 65, 72–74, 89,
   91–94) **and 0 in 213,150 at `n ≤ 225`** (24 tied), with the **falsifier silent on all 48 proved
   rows in scope** — the strongest available check, since a proved optimum cannot be beaten. The
   family's last unspent parameter, the **block's position**, is then spent on the seven open tie rows
   (`12, 20, 30, 42, 56, 72, 91`): **421,713 declarations over 40 sides × 7×7 offsets, 0 nominations**.
   The reason is structural, not budgetary: a beat needs `K ≤ k−1` and `L < k`, so the seam gap is under
   one unit and the block always beds cells — the least bed reachable grows as 2, 3, 4, 5, 7, 7, 10 with
   `k`, while the count law's cheapest declaration asks for `0`. And the bed is **not** an interval (a
   symmetric declaration takes only even values) and **steps by up to 4**, so no interpolation or
   bisection on it is sound. **The carrier line is closed**: it explains the table (58 ties at `n ≤ 225`
   once run 148's own `counts_max = 130` filter is removed — doc 105 §0; run 148 read 24 because that
   filter dropped every count from 131 to 225 before comparing it with a row) and cannot move it, at any
   split, any shape, any `r` (run 147) and any position.
   **Run 149 has now decided the position instead of sampling it** (`carrier_offset.py`, doc 106). A
   carrier cell's bed-set is four strict half-spaces in `(L, cx, cy)` — hence **convex** — so a box in
   those three parameters carries an exact **floor** (cells bedded at every point of the box) and
   **ceiling** (cells bedded at some point), and a branch and bound that prunes a box when the floor
   exceeds the count law's demand `D* = K² + m − n` or the ceiling falls short **empties the box list**:
   on **every** open, non-proved row up to 100 — the 16 `tie reached` rows plus `n = 12` — that is
   **7,381 declarations, 94,339 boxes, 0 survivors** (run 150): no side that would beat the delivered
   one, no block position, no shape that fits (`p + q ≤ isqrt(2k²−1)`), no declaration. The
   same engine takes run 148's **notched block** (`p×q` minus an `a×b` corner, `a, b ≤ 2`; the L is
   exactly the union of two full rectangles, so its floor is the union of their forced sets and its
   ceiling the full block's possible set) through **6,038 declarations and 69,614 boxes** with the same
   result — the notch lowers the demand by `a·b` and must un-bed that many cells, and the band a corner
   can free is never that wide. A planted-configuration control (plant a pose, walk the boxes that
   contain it, no false zero) is what caught the missing seam law `L ≥ K` in the first draft. Nothing
   promoted; **22.217428576** stands.
   **Run 150 widened that decision to every open row and found two defects in run 149's framing**, both
   now fixed. (a) The interval's end was the **grid** side; a beat needs the **delivered** side minus the
   project's `1e-8` floor. The two coincide for fourteen of the sixteen rows and `n = 12`, and run 149's
   domain was a *superset* there, so its verdicts stand — but `n = 40, 65, 89` deliver 1.7e-9 *below*
   their grid side and the family attains the count at the delivered side with `K < k`, i.e. inside
   `[√n, k]`, so those rows can never be emptied as stated. The minima pass found it: `n = 65`'s least
   bed under the grid-side interval is `0`, a hit that is not a beat. (b) `SMAX = 13` was a cap only at
   `k = 10` (the complete bound is 5, 7, 8, 9, 11, 12, 14 for `k = 4..10`), so 89..94 gained the `7×7`
   block. With both fixed, seventeen rows, **7,381 declarations and 94,339 boxes, 0 survivors** (n = 65's
   46,134 boxes are the expensive row). The `n = 12` sentence "the least bed is 2" is no longer a reading
   of a 49-position sample: `D = 0` is emptied, `D = 1` is emptied, and `D = 2` is hit at
   `(L, cx, cy) = (3.999999735963447809, 2.025124976626836406, 1.560660450042059492)` — one cell short,
   certified. Nothing promoted.
4. **The guaranteed payer:** the `554` beaten rows leave `15.076155` score unclaimed below them (the row-90
   promotion added its own `0.053464`); a uniform `1 %` capture is `+0.15076` and `5 %` is `+0.75381` — the whole `0.163635` gap to the reported leader is `1.1 %`
   of that room, and it needs no new construction, only a tighter polish than the one that produced the
   record. Grid-row beats (all 30 band tops by inheritance) are worth `+0.23251` in total.

## 4. PROMOTION GATE (C1–C4)
Keep `submission.csv` and root `WHITEBOARD.md` untouched until a candidate passes:
- **C1 (Proof):** exact certificate (`verify_certificates.py` at clearance `≥ 0`) or certified rational
  interval proof (`interval_verifier.py`).
- **C2 (Margin):** strictly smaller `40-digit` true side (`true_geom.py`: `L_true < L_delivered`, `0`
  overlap), and above the ε/rendering noise floor so the metric actually moves.
- **C3 (Integrity):** `sqscore` + `record_guard.py` + `glm_wheels --audit` (`0` floats) all green.
- **C4 (Honest Ledger):** log exact numbers, wins **and refusals**, cleanly — a refused candidate is a
  result and is recorded as one.

## 5. HOW TO USE THIS CARD IN A RUN
1. Open with the orientation above; re-read §2 before proposing a route (most routes are already priced).
2. Pick from §3, or bring a new structural angle and say which priced route it changes.
3. Every run ends with: exact numbers, what improved, what was refused and why, and a fresh §3 if the
   landscape moved. If a number in §1–§3 changed, update this card in the same commit.
