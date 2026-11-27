# 117 — Rational-spinor C1 and the widened pocket-insertion module

**Run 162 · 2026-11-27 · status: C1 unblocked for mixed rational spinors (positive control green);
widened D1 runs recorded, still zero pack-legal candidates; nothing promoted.**
**Instruments:** `scripts/snap_certify.py`, `scripts/interval_verifier.py`,
`scripts/pocket_insert.py`, `scripts/true_geom.py`, `scripts/packlib.py`.
**Ledgers:** `workspace/push/pocket_insert.json`, `workspace/push/snap_certify.json`.
**Untouched:** `workspace/submission/submission.csv`, root `WHITEBOARD.md`. Score unchanged:
**22.217428576459…, 554 beats, 446 ties**.

---

## 0. Result in one paragraph

C1 is no longer blocked by the absence of a global 0°/45° word. `snap_certify` already wrote a
`field: "Q"` certificate whose cell frames are the rational spinors
`(cos, sin) = ((1−t²)/(1+t²), 2t/(1+t²))`, and the new control 9 proves a genuinely mixed pose —
axis + 3-4-5 + 5-12-13, no 45° cell — passes the exact certificate and C2 at L = 4 against a
delivered 4.1. `interval_verifier` now also accepts the exact `spin(c,s)` direction; control 8
certifies `(3/5,4/5)` with half-extent 7/10. The widened D1 module was upgraded to 16 cells with a
vectorized analytic gradient (validated against central differences), a clamped axis-aligned seed,
and a local damped projection that is reverted when it makes the pose worse. Twenty-four records
cover the top actionable targets. The 16-cell module improves the residual at 55, 211, 509, 604,
655 and 998, and the 4-cell baseline remains better at 29 and 998; **no record is pack-legal**, so
C1/C2 were not entered for any candidate and `submission.csv` is unchanged. The remaining problem
is the last 0.001–0.09 of overlap, not the certificate.

---

## 1. C1 — the rational-spinor certificate

### 1.1 What was already there

`snap_certify.py` snaps each angle to the continued-fraction convergent of
`t = sin θ / (1 + cos θ)` with denominator ≤ 100,000, writes the centre as a rational with
denominator ≤ 1e9, and emits:

```
field: "Q"
cell r: [c, -s, s, c]       # c² + s² = 1, rational
L: exact rational side
```

`verify_certificates.verify_certificate` checks orthonormality, determinant +1, all four wall
inequalities, the exact declared side, and every pairwise 4-axis SAT inequality on integers. It never
needs a `Quad(d)` tag; the old `Q`/`Quad(d)` restriction was a property of the *input alphabet*, not
of the verifier.

### 1.2 New mixed-angle positive control

`snap_certify --selftest` control 9:

| cell | centre | spinor `t` | frame `(c, s)` |
| --- | --- | --- | --- |
| 0 | (1/2, 1/2) | axis | (1, 0) |
| 1 | (19/10, 19/10) | 1/2 | (3/5, 4/5) |
| 2 | (33/10, 33/10) | 1/3 | (4/5, 3/5) |

The pose has exact side `L = 4`, zero violations, and `adjudicate(3, …, Q(4), Decimal("4.1"))`
returns **C1 = True, C2 = True, margin = 0.1**. The certificate's second frame is exactly
`["3/5", "-4/5", "4/5", "3/5"]`. This is the positive control the Q/Quad-only path could not supply:
two different non-axis rotations, no 45° direction, and no `Quad(d)` field.

### 1.3 The interval route

`interval_verifier.dir_iv` now accepts `("spin", c, s)` with rational `c² + s² = 1` and returns the
exact point intervals `(c,c)`, `(s,s)`. Control 8 certifies a `(3/5,4/5)` cell with half-extent
7/10 and strictly positive slack against an axis cell. This is the rigorous rational-interval
alternative named in C1; it does not need a square root or a float.

### 1.4 What this does and does not settle

* **Settled:** a pack-legal pose whose directions are rational spinors can be certified under C1 with
  no global word and no `Quad(d)` tag. The frame is exact, the side is exact, and the SAT pass is
  integer-exact.
* **Not settled:** the exact *repair* of a 1000-cell mixed pose is expensive. A 30-cell snap plus
  `relax_simultaneous` did not finish in 180 s, so the exact route is a final adjudicator, not an
  inner loop. No pack-legal candidate existed in this run, so no 1000-cell exact repair was attempted.
* **C2/C3/C4:** unchanged. C2 is the 40-digit `true_geom` side against the delivered side at 1e-8;
  C3 is `sqscore` + `record_guard` + `glm_wheels --audit`; C4 is the refusal/promotion ledger.

---

## 2. D1 — widened module and analytic gradient

### 2.1 Changes

* **Module size:** 16 cells by default (15–20 requested); the 4-cell module is kept as a baseline.
* **Seed:** the pocket centre from the frontier pose; the centre is clamped into `[L_lo+h, L_hi−h]`
  and the new cell starts axis-aligned. The scan's largest free square may be smaller than a unit
  cell, and the old unclamped seed paid a six-figure box penalty at n = 29.
* **Gradient:** `_pair_terms` differentiates the active SAT axis, including the support derivative
  and the axis derivative for the owning cell; `_container_terms` differentiates the box penalty.
  L-BFGS-B now uses `jac=True` (15–20 cells = 48–63 variables, no finite differences).
* **Projection:** `repair_local` is a damped Jacobi sweep over pairs incident to the moved module,
  with fixed cells held; the result is compared with the pre-repair pose and the better one is kept.
  The exact `snap_certify` relaxation is reserved for a pack-legal finalist.
* **Ledger:** the 4-cell and 16-cell records are separate, not overwriting each other.

### 2.2 Gradient check

The selftest compares all six variables of `_pair_terms` (x, y, angle for both cells) against central
differences on three overlapping pairs; the maximum error is below `2e-4` relative. The box gradient
is checked at two cells outside `[0,1]²`. The planted 3×3-minus-centre still accepts its ninth cell.

### 2.3 Trials

`packlib.verify` is the gate; `exact_side` is only computed after it passes. No row below is legal.

| frontier → target | pocket | 4-cell obj / L | 16-cell obj / L | pack |
| --- | ---: | --- | --- | --- |
| 29 → 30 | 0.800296 | **0.007303** / 5.966910709 | 0.008161 / 5.998734190 | no |
| 55 → 56 | 0.755579 | 0.027390 / 7.972859537 | **0.016633** / 7.972848665 | no |
| 211 → 212 | 0.668138 | 0.090959 / 14.996770228 | **0.081257** / 14.996751841 | no |
| 345 → 346 | 0.999845 | 0.001451 / 19.000000002 | **0.001376** / 19.000000002 | no |
| 509 → 510 | 0.732053 | 0.021520 / 22.989777095 | **0.014819** / 22.989777095 | no |
| 604 → 605 | 0.760979 | 0.021744 / 24.993298935 | **0.020807** / 24.996632858 | no |
| 655 → 656 | 0.761940 | 0.021513 / 25.999711088 | **0.018633** / 25.999850559 | no |
| 998 → 999 | 0.732771 | **0.043369** / 31.993113005 | 0.050671 / 31.993106895 | no |
| 184 → 185 | 0.999895 | — | 0.000950 / 14.000000002 | no |
| 424 → 425 | 0.999801 | — | 0.001576 / 21.000000002 | no |
| 557 → 558 | 0.999841 | **0.001876** / 24.000000002 | 0.002227 / 24.000000002 | no |
| 708 → 709 | 0.999558 | **0.002126** / 27.000000002 | timeout | no |
| 877 → 878 | 0.999570 | **0.002376** / 30.000000002 | timeout | no |

The 20-cell 655 attempt (6 restarts × 20 s) is worse than 16 cells: `0.029871`, L `25.999845827`,
pack no. The widened module therefore helps where the pocket has interior room (55, 211, 509, 604,
655) and does not rescue the boundary-constrained small rows or 998; the 4-cell module remains the
control and is better at 29 and 998.

### 2.4 Why no promotion

No record has `pack_ok = True`. The closest residual is `0.000950` at 184, but its side is
`14.000000001858` — a hair **above** the grid, not below it; 345/424/557/708/877 sit at their grid
sides for the same reason. The only genuine side reductions are 29 (5.9669 vs 6), 55 (7.9728 vs 8),
211 (14.9968 vs 15), 509 (22.9898 vs 23), 604 (24.9933 vs 25), 655 (25.9997 vs 26), 998 (31.9931 vs
32) — and every one still overlaps. C1/C2 were not entered, no row was promoted, and the C4 ledger
records the refusals with their parameters.

---

## 3. Guards

```
python3 scripts/snap_certify.py --selftest          # 9 controls, 24 decision functions, 0 float
python3 scripts/interval_verifier.py --selftest     # 8 controls, exact spin direction
python3 scripts/pocket_insert.py --selftest         # planted seat + analytic-gradient check
python3 scripts/true_geom.py --selftest             # 3 controls
python3 scripts/sqscore.py                          # 22.217428576, 554 beats, 446 ties
python3 scripts/record_guard.py                     # clean, 124 docs
python3 scripts/glm_wheels.py --audit               # 708 functions, 0 offenders
python3 scripts/provenance_repair.py --guard        # 1000 rows, 0 stale
```

The core/verifier/snap modules remain float-free: `snap_certify` 24 decision functions,
`interval_verifier` 17, `verify_certificates` 30, `true_geom` 7 — all 0 naming float. The new
`pocket_insert` arithmetic is discovery (float) by design; its verdict is still `packlib`/`true_geom`.

**Limitations.** The 16-cell search is a local L-BFGS-B result, not a global one; 708/877 timed out at
16 cells. The projection is reverted when it is worse, so it does not claim to close a residual it
cannot. The exact rational repair was not run on a 1000-cell pack-legal pose because none exists.
No candidate was promoted, so no new score number is claimed.

---

## 4. What changed, and next

**Changed:** `snap_certify.py` (mixed positive control), `interval_verifier.py` (`spin` spec +
control), `pocket_insert.py` (clamped seed, analytic gradient, local projection, separate ledger
records). `submission.csv` and `WHITEBOARD.md` untouched.

**Next, in order.**

1. **Exact repair at production size.** The C1 certificate is ready; the blocker is the cost of
   snapping and relaxing 1000 cells. A local exact relaxation (module + neighbours, fixed remainder)
   is the right target, not a global 1000² Fraction sweep.
2. **Use 16 cells only on interior pockets.** 655/509/604/55/211 improved; 29 and 998 prefer 4. Select
   the module by pocket clearance, not by a fixed count.
3. **Do not treat a sub-grid residual as a candidate.** 345/424/557/708/877 have tiny residuals but
   sit at the grid side; only a side strictly below `k` can beat the row.
4. **Keep C1 control 9 in every run.** It is the standing proof that mixed rational spinors do not
   need a `Quad(d)` word.

No promotion; the score and both protected files are unchanged. The next run starts with a working
mixed-angle C1 judge and a measured, bounded D1 search.
