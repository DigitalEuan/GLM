# 72 — Synthesis: what is verified, what is refused, and what would justify another run

Runs 60–111 built one thing: an exact, audited pipeline that certifies packings of n unit squares in a
square container, with a strict separation between *discovery* (heuristic, float, untrusted) and
*certification* (exact algebraic, bytecode-audited, independently verified). This document collates what
that pipeline has established, states the architectural invariants that keep it honest, and sets the
falsifiable criteria under which another run is worth running at all.

## 1. Run 111: the definitive push on n = 29, and the loose-gap screen

n = 29 was the one row where run 110's legal gap was `2e−3` rather than `1e−7`, so it got the definitive
push: a constrained shrink ladder (a hinge that *punishes* the side for exceeding a target rather than
rewarding smallness), six targets from `1e−4` to `4e−3`, up to four restarts each, every attempt
projected back to feasibility by minimising overlap alone, every survivor measured by `true_geom` at 40
digits — 24 optimisations in all.

| δ | 1e−4 | 2e−4 | 5e−4 | 1e−3 | 2e−3 | 4e−3 |
|---|---|---|---|---|---|---|
| best **legal** side found | **5.933929467** | 5.934008995 | 5.934325467 | 5.934637925 | 5.935377646 | 5.937557661 |
| vs delivered 5.933833464 | **+9.6e−5** | +1.8e−4 | +4.9e−4 | +8.0e−4 | +1.5e−3 | +3.7e−3 |

**No legal state beats 5.933833464.** The ladder is monotone in δ — the harder it is asked to shrink,
the closer it gets to the delivered side *from above* — and the best legal state is `9.6e−5` worse,
against `2e−3` before the push. That is the signature of a locally minimal packing: as the target
approaches the delivered side the best achievable legal state approaches it too, without crossing.

**The screen: n = 29 is not unique, and it is not loose either.** The same ladder (δ = `1e−4`, `5e−4`,
three tries) was run on doc 69's ten highest-slack rows, so the numbers are comparable across rows:

| n | 11 | 17 | 18 | 28 | **29** | 37 | 39 | 41 | 53 | 55 |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder gap | +3.34e−4 | +2.04e−4 | +1.42e−4 | +9.44e−5 | **+9.60e−5** | +9.90e−5 | +6.17e−5 | +3.34e−4 | +8.01e−5 | +1.01e−4 |
| best known gap (any schedule) | +9.3e−8 | +3.7e−7 | +2.8e−7 | +9.44e−5 | +9.60e−5 | +9.90e−5 | +6.17e−5 | +3.34e−4 | +8.01e−5 | +1.01e−4 |

Two things follow, and the second is the important one.

* Every one of the ten rows has a positive legal gap under this ladder, in one narrow band
  (`6.2e−5 … 3.3e−4`). n = 29 sits in the middle of that band: it is neither uniquely loose nor
  uniquely tight, so there is no "loose subset" to chase beyond the one row already pushed.
* The band is **schedule loss, not structure.** Where a row was given a stronger schedule the gap
  collapsed: n = 11, 17 and 18 reach `+9.3e−8`, `+3.7e−7`, `+2.8e−7` under run 110's penalty plus
  projection, and the ladder additionally beats the general schedule on n = 28, 37, 39, 41, 53, 55
  (whose full-schedule results were `+1.95e−3 … +3.19e−3`). A ladder gap is therefore an upper bound on
  the local room, never a measurement of it — the only defensible reading is the best known gap in the
  second row, and none of the ten is below the delivered side.

## 2. What is verified

1. **552 rows certified** (run 106): for each, an exact certificate — every pair's separating axis with
   rational slack, `clearance = 0`, `void ≥ 0` at the stated side — checked by an independent verifier
   that knows nothing about how the certificate was produced (`verify_certificates.py`, 11 mutation
   controls, 7 shipped certificates re-checked on every audit).
2. **The delivered table scores 22.218056945**, 553 of 1000 rows beating the grid, recomputed on every
   audit from `submission.csv` by `sqscore` (which `record_guard.py` refuses to run without).
3. **The face squeeze is exact and its gain is the polish** (run 108): every face of n = 66 and n = 325
   has positive exact room (`231/10¹²`, `27/25·10¹⁰`), a single face cannot move a *square* container's
   side, the two-face squeeze can and does — `−4.62e−10` and `−2.16e−10`, both certified at clearance 0
   — and 31 of the 33 word-exact rows with n ≤ 40 shrink the same way (Σ dL = −2.6881e−8). The total
   metric gain is `−7.885757e−9`: real, verified, and five orders below the delivered sides' precision.
4. **The table is reconciled with the submission** (run 110): 357 of 1000 rows carried a snapped-model
   side instead of the true one; `Σ L_table/√n − 1 = 22.645990612927686` and
   `Σ L_true/√n − 1 = 22.218056944873789` differ by exactly `0.427933668053897`, the accumulated model
   error. The two numbers that had looked contradictory were the same score measured on two poses.
5. **The exact carriers are known**: `Q(√2)` for the eight words that 553 rows use, `Q(√7)` for the
   family of runs 93–94, `Q(√5)` for one instance; the gate is parametrised by its field (run 91) and
   the certificate by its degree.

## 3. What is proved to be refused

1. **A single face slide never lowers a square side** (run 108): `L` is the larger of two extents, so
   moving one face only renames which axis binds. This is a two-line proof, and it explains a decade of
   failed corridor searches.
2. **Depth-2 chains do not move the side** (run 107): opening a two-cell trade always leaves a
   three-overlap cycle at n = 330; the obstruction is relational, not numerical.
3. **Every analysable high-slack row is relationally closed** (run 109): pins are held by pins; the only
   free wall in the sample (n = 11, `3.53e−4`) is on the *non-binding* axis. n = 330's 28 free wall cells
   are all on `hi_x`/`hi_y` while both binding cells are pinned.
4. **No algebraic field can certify a transcendental row** (doc 70 §4): the gate's separations involve
   `cos`/`sin` of the stored angles, and `cos θ` is transcendental for any non-zero rational θ
   (Lindemann–Weierstrass). 447 of the 1000 rows are in that class; no amount of field extension helps.
5. **Model wins are not wins** (run 109/110): a snapped-pose candidate at n = 330 had a verified
   certificate at `18.692488` against a table side of `18.692672`, yet at the row's true angles it was
   `2.43e−4` worse. The ε(gap) guard now refuses exactly that class of artifact before promotion.
6. **Free angles buy nothing legal** (run 110/111): with every `(Δx, Δy, Δθ)` free, the best *legal*
   state is worse than delivered on n = 11, 17, 18 (`+9.3e−8 … +2.8e−7`) and on n = 29 (`+9.6e−5` after
   the definitive push).

## 4. Architectural invariants

These are the properties that make the results trustworthy, and they are enforced, not merely intended.

1. **Discovery is untrusted.** Every heuristic lives in a module that proposes states; none of them may
   print or promote a result. `relax_angles.py` (float, scipy) is deliberately *outside* the float audit
   for exactly that reason.
2. **Certification is exact and float-free.** `qsqrt2.py` (gate), `verify_certificates.py` (verifier),
   `cand105/106`, `face_slide`, `semantic_pack`, `true_geom`, `reconcile_table` contain no `float` at
   all: `glm_wheels --audit` checks the bytecode of **596 decision functions** for the name `float` and
   reports **0 offenders** on every run.
3. **One scorer.** `sqscore.py` is the only place a score is computed; it asserts its own output against
   the delivered 22.218056945 / 553 beats before anything else may use it.
4. **Two independent witnesses.** A certificate is built by one module and verified by another that has
   no access to the search; run 110's guard adds a third, at 40 digits under the true angles.
5. **Every claim is bounded.** `ε(gap) = 2·max|θ − word(θ)|` bounds the model error; the 12-decimal
   rendering is bounded by `5e−13`; nothing is compared at a precision it has not earned.
6. **Guardrails on prose.** `record_guard.py` refuses a stale total presented as current; the README and
   STATUS run-history is one line, byte-identical in both files.

## 5. Falsifiable criteria for another run

Another Squares-in-Squares run is justified only if it can state, in advance, a **test that could fail**.
The criteria below are the ones this repository now holds itself to; each is checkable from the artefacts.

**A run that could promote a row must satisfy all of:**

* **C1 — the pose is certifiable.** Either every angle is one of the exact words (so `Q(√2)` suffices),
  or the angle is algebraic with a known extension, or an interval-arithmetic verifier is accepted as a
  second judge. A transcendental row cannot be promoted by any exact-certificate route, so a run whose
  target is transcendental is *discovery only* and must be reported as such.
* **C2 — the true side is strictly smaller.** Promotion requires `L_true(candidate) < L_true(delivered)`
  at 40 digits, with zero overlap at those same digits — the condition that has never yet been met.
* **C3 — the gain is above the budget.** The gain must exceed both `ε(gap)` (for a snapped model) and
  `100 × 10⁻¹²` (the rendering noise of the submission format). A gain that only appears inside the
  model error is not a gain.
* **C4 — the metric moves.** `Σ ΔL/√n` must be strictly negative with the two bounds agreeing, so a
  leaderboard improvement is implied rather than assumed.

**A row is worth attacking only if it has a structural reason, not merely a large slack:**

* **R1 — a word-exact row** whose true side exceeds its best-known floor, i.e. a row in the 552 with a
  *certifiable* pose that a new construction might beat. The 448 uncertified rows are excluded by C1
  unless an interval verifier is added first.
* **R2 — a loose legal gap on a certifiable row.** The relaxation gap is the diagnostic: `+9.3e−8`,
  `+3.7e−7`, `+2.8e−7` (n = 11, 17, 18) say "no room at this precision"; n = 29's `+9.6e−5` says "room,
  but still not enough". A word-exact row with a gap above `1e−4` would be the first target.
* **R3 — a named mechanism.** Face slides, chains, clusters, re-orientations, void trades and free angles
  have all been tested and refused; a new run must name a mechanism not among them, and say which
  invariant of §4 it stresses.

**Cost.** Every run must leave the audit green (0 offenders), every selftest green, `sqscore` and
`record_guard` green, and `submission.csv` untouched unless C1–C4 hold. A run that cannot meet that is
not worth its tokens.

## 6. What is not claimed

Not that the 552 certified rows are optimal — only that they are *verified at their stated sides*. Not
that the delivered table is optimal — only that no tested mechanism improves it, and that its score is
`22.218056945` when measured on the poses actually submitted. Not that the 447 transcendental rows are
unimprovable — only that no mechanism used here improves them, and that no exact certificate for them
can exist in an algebraic field. Not that the relaxations are converged — `L-BFGS-B` with a handful of
restarts is a local method, and the gaps it reports are upper bounds on the local room, not proofs.

The honest summary after fifty runs of this phase: **the pipeline is sound, the frontier is
well-characterised, and every mechanism tried so far for moving it has failed for a reason that can be
stated in one sentence.**
