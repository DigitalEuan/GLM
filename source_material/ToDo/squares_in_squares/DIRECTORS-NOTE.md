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
| 446 rows tied to `L = k` (the standard grid), 30 bands `k = 3..32` | confirmed (446 includes n = 1; 445 at n >= 2; row 90 left the grid ties when it was promoted in run 140; 30 frontier bands, band 32 clamped at n = 1000). Run 159 splits them: **152 rows are locked by proof** (`r <= 4` or a proved case, `2.5008` of score) and **293 are open** (`4.6029`) | doc 75 §2, run 115, doc 114 §2 |
| 303 tied / 21 ahead / 0 behind the Squares Project catalogue | **[corrected in run 159]** the 0-behind reading was true of the September snapshot. Against the catalogue retrieved 2026-11-27 we are **21 ahead, 273 tied, 30 behind**, worth `+0.008891` of score; the import list is `workspace/push/target_audit.json` | doc 114 §3, `workspace/catalogue/frontier.json` |
| 552 rows hold standalone zero-clearance `galois-certificate/1` proofs | confirmed (552 of 554 beaten rows certified; the promoted row 90 carries the project's exact rational certificate instead, re-verified by `import_n090.py`) | `verify_certificates.py`, run 106 |
| 613 core decision functions, 0 float offenders | confirmed | `glm_wheels.py --audit` |
| **"Grid-frontier rows (`n = k² − 1`) are uniformly compressed"** | **WRONG** — the frontier row of band k is `m* = k² − j*` with `j* = 18…26` at `k >= 21` (e.g. band 23: `m* = 509`, `j* = 20`; band 32: `m* = 998`, `j* = 26`). `n = k² − 1` is not a frontier row anywhere in the table | doc 75 §2 |
| free cell `0.9994–0.9999` at the compressed frontier | **[corrected in run 161]** the reading was the `table.json` *grid* state, not the delivered CSV pose: `reconcile_table.py` rewrote `L` only, leaving the unclosed `k×k` margin grid in `state` for ten bands. The delivered pockets are **0.761940** at k = 26 (2.38108, 8.38097) and **0.732771** at k = 32 (27.59, 0.40); `provenance_repair.py` now copies the CSV state into all 1000 rows and `record_guard` enforces it | doc 115, doc 116 §1, `provenance_repair.py` |
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
  - *The high-band wall is one pocket, not a uniform compression:* **[corrected in run 161]** the
    `0.9994–0.9999` free square was the `table.json` *grid state* for ten bands (`k = 21, 22, 24…31`):
    `reconcile_table.py` rewrote `L` only, so `state` still held the unclosed `k×k` margin grid with its
    `j` unit holes. The delivered CSV poses are mixed and carry a real pocket: **0.761940** at
    `k = 26` (`n = 655`, centre `(2.38108, 8.38097)`; binds cells 26/29/51/64) and **0.732771** at
    `k = 32` (`n = 998`, centre `(27.59, 0.40)`; binds 848/881). The two notch bands were real even in the
    stale states (`k = 23` 0.7534, `k = 32` 0.7171); the delivered k = 32 pocket is 0.7328 and the k = 23
    CSV scan is 0.7320. `provenance_repair.py` now makes the CSV state the table's, and `record_guard`
    calls its guard.
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
2. **Notch-Band Rearrangements (`k = 23`, `k = 32`):** exploit the delivered `0.7320` (k = 23 scan) and
   `0.7328` (k = 32 direct) corner holes (`n = 999`, the k = 32 next row, is the lowest-cost large-band
   breakthrough at `+0.120`). Run 161's bounded 4-cell modules reached residual 0.024 at both, but no
   pack-legal pose; doc 116 §3.
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
   **Run 151 closed the `n ≤ 100` block and audited the high rows' scalable motifs exactly** (doc 107).
   Above 100 the question was whether the table had actually used the literature's scalable families:
   recursive grid products (with cell trims), Friedman's unit-border inflation (`n → n + 2⌊L⌋ + 1` at
   `L + 1`, iterated), and the parametric strip / 45° / rational-rotation motifs. Rebuilt from their own
   laws in Q(√2) from **519 exactly reconstructed bases** (the other 481 rows carry arbitrary angles and
   cannot be replayed without a float), the three families produce **33,074 candidates over all 900 rows
   of 101..1000 and not one strict beat** — best margins −1.5e-9 (products), +1.9e-9 (inflation), −0.177
   (parametric). The near-zero ones are the finding: **425 of the 900 rows are reproduced to 1e-6 by
   these very constructions**, and row 962 is the table's own cascade from row 901 to within the CSV's
   1.9e-9 rendering. The parametric family's ceiling is arithmetic, not parametric: its realised slack is
   5.9–11.6 % above √n where the table sits at 0–4.4 %, and its best members are grid ties. Zero
   promotions; **22.217428576** stands.
   **Run 152 fixed the record and widened the base census** (doc 108). The README/STATUS tables still
   said **553 / 1000** beats against `sqscore`'s 554, and `record_guard` passed them because both of
   its rules are anchored to score literals (`2x.xxxxxx`) — a beat count was never read as a claim.
   Five lines were fixed and **R3** now checks the count on table rows, currency sentences and lines
   naming the current score (a line naming only a superseded score stays history); its line-scoped
   limit is stated, not hidden. On the bases: `exact_words.py` decides every **degree-2** word — the
   rational words and every `Q(√k)` word, with quarter turns recognised as the **axis word** — lifting
   the census from 519 to **552 recovered / 550 trusted**; rows 678–679 turn out *not* to be exact 45°
   sentences (they overlap by 3.34e-10) and are dropped. No row in 1..1000 is a Q(√3), Q(√5) or
   Q(√10) sentence, and the 448 still refused carry a median of 71 distinct angles — general-position
   poses, not hidden motifs. The re-run holds: **36,043 candidates, 900 rows, 0 beats**, with n = 500's
   best candidate improved to 23.414214 and still 0.56 short.
   **Run 153 closed the prose beat count and added the composite family** (doc 109). R3's claim test
   now also covers any line under a **current-state heading** (canonical / current / delivered /
   results / status / frontier / state), decides history per **paragraph** rather than per line, and
   skips fenced code; it flagged exactly `RECONCILIATION.md:10` (553/1000 under "## Canonical state"),
   which is fixed, and correctly leaves `04-RUN-LOG.md`'s run-14 line and the stale-score quotes alone.
   On the audit: the 550 trusted bases seed **family D — a base plus an exact motif in its leftover**
   (base in `[0,L]²`, motif bbox in `[L, L+S]²`, both strips filled to the lattice,
   `n = n_base + m + 2 nx ny`). Because `n ≤ L²`, `m ≤ S²` and the strips hold `≤ 2LS`, every composite
   has `n ≤ (L+S)²`: it can tie the grid and never beat it. Measured over **57,388 candidates and 784
   rows: 0 beats**, the closest at −1.448e-9 being a **grid tie** (row 111) and the second closest
   0.0032 above — the whole audit is now **93,431 candidates, 900 rows, 0 beats**. The negative is
   structural: (A) preserves density, (B) is capped by the grid, (C) is capped by a rotated block's bbox
   (0.66), (D) by `(L+S)²` — no composition of rigid tiles can beat a row denser than the grid.
4. **The guaranteed payer:** the `554` beaten rows leave `15.076155` score unclaimed below them (the row-90
   promotion added its own `0.053464`); a uniform `1 %` capture is `+0.15076` and `5 %` is `+0.75381` — the whole `0.163635` gap to the reported leader is `1.1 %`
   of that room, and it needs no new construction, only a tighter polish than the one that produced the
   record. Grid-row beats (all 30 band tops by inheritance) are worth `+0.23251` in total.

4. **Proposal engines with the exact pipeline as judge (`run 154`):** `proposal_anneal.py` (float, isolated)
   + `snap_certify.py` (zero float, audited) is the first end-to-end *propose -> snap -> gate* loop, and it
   refuses on exactly one axis: free-angle annealing lands on the `k x k` lattice it starts from, so at
   `k - 1e-4` its best pose is `1.5e-2 .. 3.6e-2` illegal — 1,490x to 3,600x over the `1e-5` line — and an
   exact repair cannot help, because a pair separated in an over-full box hands its overlap to the
   neighbour (it *raised* the residual on 18 of 20 rows). The route is not dead, its variable is wrong: a
   spinor with denominator `<= 32` quantises to ~`1e-3` rad (`1.5e-2` of slop at `k = 15`), so a proposal
   good enough to survive the snap must already be a word construction. **Next: anneal on the word alphabet**
   (`t = p/q`, `q <= 32` as the rotation move set), which makes Stage 2's snap the identity and turns the
   `1e-5` rule into a statement about the pose. Doc 110.

5. **The calibration gate is the cheap experiment (`run 155`):** `proposal_anneal.py --selftest` now has to
   find cold packings that beat the integer grid at `n = 5` (2.71), `n = 10` (3.72) and `n = 39` (6.85) before
   any row above 100 is touched, and it **fails at 39** (`+3.3e-2`): the rebuilt solver (joint L-BFGS-B,
   Lubachevsky-Stillinger inflation, basin-hopping, simultaneous quench) is calibrated where it is cheap and
   unaffordable where it matters — one `solve` at 39 squares is ~8 minutes, and 118 squares is 19x the pairs.
   The gate cost 14 minutes and stopped a target run that would have spent hours to produce another 1e-2
   negative; it also caught the SAT measure **inverted** and gave the project its floor — the clamped `k x k`
   grid at `k - 1e-4` penetrates exactly **1e-4**, ten times worse than the `1e-5` pass line, so any solver
   result above 1e-4 is worse than doing nothing. **Next for this route: the analytic gradient** (one pass
   instead of `3n` finite differences) and bounded per-solve restarts; do not spend target budget before the
   gate passes at 39. Doc 111.

6. **The gate moved from cost to search (`run 156`):** `proposal_anneal.py` now has the exact analytic
   gradient (`2.46e-9` against central differences, **86.1x** on 60 L-BFGS-B iterations at `n = 39`, one
   gradient pass costing 1.24x a value at `n = 118`), a hard wall-clock `Cap` raised from *inside* both the
   L-BFGS-B and basin-hopping callbacks (the gate's cases run 8.2 / 12.3 / 38.5 s where run 155 spent 526 s
   in one restart), and boundary-deficit plus block-plus-margin seeds. It still fails at **n = 5** (`1.45e-1`)
   and `n = 10` (`9.33e-2`) as well as `n = 39` (`3.63e-2`): twelve configurations, thousands of basin steps
   each, all jam at `8e-2`-`2e-1` because the `2 + 1/sqrt 2` optimum needs its fifth square *between* the
   block's corners, through a gap that is closed at the current pose. Speed was never going to buy that:
   the next move is a **structural one** — teleport-into-hole on run 127's `legal_slide` void seats, block
   swaps, or a constructive enumeration of the block-plus-`r` topology — and until it lands the gate keeps
   refusing the `n = 101..1000` run, which is the correct outcome.

7. **The structural move works at five and ten (`run 157`):** `squeeze_ladder` drops a jittered
   45-degree cell near the centroid, lets L-BFGS-B re-form, and keeps only improvements — the one move
   that can put a square *inside* a jammed block, which is what `n = 5`'s `2 + 1/sqrt 2` pose needs
   (four corners plus a 45-degree centre). Teleport-into-seat (run 127's `void_seats`, pinned to
   `legal_slide.slack` exactly) and block swap join it. The gate now reads **n = 5 PASS `-7.5e-05` in
   3.3 s** and **n = 10 PASS `-4.6e-05` in 4.7 s**, where run 156 failed at `1.45e-1` and `9.33e-2`;
   **n = 39 still fails at `+2.7e-2`** in 41 s, and that is the whole remaining blocker: at 83% density
   a five-cell squeeze does not open a 39-cell pose, so the next move has to be scale-aware (local
   compression of a block, a row shuffle, or a squeeze repeated along a line). Until it lands the gate
   keeps refusing `n = 101..1000`.

8. **The collective moves land, and the third calibration case is mispriced (`run 158`):** `band_shear`
   (a contiguous band on one of four axes, shifted transversely with the boundary strips leaning into the
   seam), `bundle_rotate` (a nearest-neighbour chain rotated *rigidly* about its centroid) and
   `seed_bridge` (two axis sub-grids in opposite corners, leftovers seated at a fixed tilt in the diagonal
   seam) are in the solver, with `struct_ladder` giving them the keep-best ladder. The gate reads
   **n = 5 PASS `-7.2e-05` in 3.3 s**, **n = 10 PASS `-4.6e-05` in 4.0 s**, **n = 39 FAIL `+2.500e-02` in
   30.4 s** (37.9 s total) — the moves bought `2.3e-3` at 39, which is nothing. The reason is now measured,
   not guessed: the case's side is **0.57 % above the best known packing in the world** (6.81072208306864,
   Schadt 2026, degree 5, Galois `S5`), forty bridge variants land at best `+2.5775e-02`, deflation from a
   *valid* 7.00 pose floors at `+1.1778e-02` at 6.95 and `+3.541e-02` at 6.85 with the floor unmoved when
   the path and the relaxation are doubled (a jam, not a budget), and the same solver passes the job it is
   for — **`n = 39` at `6.9999` gives `+4.663e-15` in 5.3 s**. The target regime itself is close but not
   open (`n = 118` at `10.9999`: `+2.069e-05` with `defect`, twice the `1e-5` line; `bridge` and `strip`
   are harmful there). Doc 113 recommends replacing the third case with the target regime — `n = 39` at
   `7 - 1e-4`, or `n = 118` at `11 - 1e-4` —    because as written it asks for a record packing. Not actioned:
   the brief's rule is that the gate decides, so no `n > 100` row was run and nothing was promoted.

9. **The landscape, and the target list was aimed at proved optima (`run 159`):** `s(k^2 - 3) = k` is
   **proved** for every `k >= 6` (Daniel 2026, Lean, rebuilt by the Squares Project; the catalogue records
   `n = 118` proved with upper = lower = 11) and `s(k^2 - 4) = k` covers `117, 140, 165, 192, 221`
   (`ValidTilt9`, reported independently by Hosono). So the ten-row list of runs 154-158 could not be beaten
   at any budget, and `n = 118` at `11 - 1e-4` was *impossible*, not hard. Even an **open** tie at the target
   side is out of reach: `n = 111` at `10.9999` lands at `+2.151e-05`, twice the `1e-5` line, because
   `k - 1e-4` there means beating the best packing known to anyone. The score decomposes exactly as
   `22.217428576459 = 15.076155` (554 beaten) `+ 7.141273` (446 tied), and the ties split into **152 locked
   by proof** (`2.5008`) and **293 open** (`4.6029`). The measured frontier is `r = 5..26`: `0/120` beaten at
   `r <= 3`, one `1e-9`-pad artefact at `r = 4`, then a monotone climb to **every row beaten at `r >= 27`**;
   no known family reaches the band (the L-shaped bands cover `r >= 8 sqrt(K) + 21`, i.e. the region already
   beaten). Three stale facts were fixed: the **proved list** (`PROVED_R = (0,1,2,3,4)`, `r <= 12` cap gone,
   so `--rank` now returns 111, 133, 112, 157, 134, ...), the **catalogue snapshot** (30 rows now have a
   verified bound below ours, `+0.008891`), and **`--budget`** (80.1 s for a 6 s request, now 6.2 s). The
   leader's `0.163635` is a **1 % side reduction across the 554 beaten rows** — 1.1 % of their 15.076
   headroom, i.e. **polish, not records**. Ranked next: import the 30 rows (**+0.0089**, certain); re-audit
   the catalogue every run (`scripts/target_audit.py`); build the side-reduction (polish) loop and test it on
   one beaten row; treat open ties only as record attempts at small `k` (`n = 20` alone is `0.118` if it
   could reach `sqrt 20`). Doc 114.
10. **D0 makes the CSV pose the table's, and D1 prices the open ties (`run 161`):** `provenance_repair.py`
    copied all **358** stale `table.json` states from `submission.csv` and fixed the one post-reconcile side
    (n = 90, `10.0000000018 → 9.9940387756`); `record_guard` now calls its guard, which enforces
    `|extent−L| ≤ 1e-9`, `0` overlap and the unchanged `sqscore` on all 1000 rows. Of the 293 open ties,
    **26** have a beaten predecessor; measured predecessor pockets lead with 656 (`0.762`), 56 (`0.745`),
    999 (`0.733`), 30 (`0.727`). Bounded 4–8-cell insertion was run on 29→30, 55→56, 509→510, 655→656 and
    998→999: **0 pack-legal candidates**, closest 29→30 at residual `0.006773` (side `5.966913431` vs grid 6).
    Nothing promoted. The next blocker is C1 for arbitrary angles: `Q`/`Quad(d)` certificates do not cover
    the delivered mixed poses, so a legal D1 pose still needs a rational-angle interval certificate or an
    exact-word module. Doc 116.

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
