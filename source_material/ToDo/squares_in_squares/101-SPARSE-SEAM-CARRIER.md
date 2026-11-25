# 101 — The sparse seam carrier: two notched axis runs reproduce 2 of the 110 two-class rows (Run 144)

**Run 144, 2026-11-25.** Instrument `scripts/seam_carrier.py` (new), ledger
`workspace/push/seam_carrier.json`. Doc 100 closed run 143 with one correction and one instruction:
two *whole* lattices cannot share area (a full block fills its own bbox), the delivered classes are
unions of **4-54** lattice translates, so "the carrier must therefore be **sparse or notched** (fill <
1, several translation domains)", and the new prototype needs "its own carrier spec, count law and
controls" plus doc 99 §9's gate — **reproduce at least 20 of the 110 delivered two-class `(n, side)`
pairs before any sweep**. This run builds that carrier, gates it exactly, and runs the entry test
first.

**Answer: the carrier is built, certified and refused by its own entry test. 2 of 110** rows are
reproduced (threshold 20). **No sweep was run.** The refusal is specific, and it is a *different*
refusal from run 143's: the sparse carrier reaches the delivered side **and** the delivered count on
**25** of the 110 rows — the geometry, not the arithmetic, is what fails. On **23** of those 25 rows
the exact gate refuses the pose (carrier runs overlap each other by a fraction of a cell); the 2 rows
that pass are the two atoms the family was calibrated on, `n = 5` and `n = 10`. Of the remaining 85
rows, **57** are in the family's side group but no member reaches their count, and **28** are not in
the side group at all.

**Nothing promoted.** `submission.csv` and root `WHITEBOARD.md` are untouched; the delivered total
stands at **22.217428576** / 554 beats / 446 ties.

## 1. What was asked

1. build the corrected prototype from doc 100: a **sparse/notched carrier** — fill < 1, a few
   translation domains — with its own spec, its own exact gate and its own controls;
2. run the **20-of-110 entry test first**, and only sweep if it passes;
3. record the outcome exactly, refusal included.

Doc 99 §9's rule is what the gate is for: a family that cannot reproduce a fifth of the delivered
two-class table has no business being searched, whatever its parameters look like.

## 2. The carrier (spec)

**Declaration.** Five integers `(k1, k2, o, m, s)`:

| symbol | meaning | bound |
|---|---|---|
| `k1`, `k2` | cell counts of the two runs on each axis | `1 ≤ k ≤ 34` |
| `o` | interlock: how far run 2 is drawn back along its axis | `0 ≤ o ≤ 2` |
| `m` | 45° cells of the centred diagonal bar | `1 ≤ m ≤ 90` |
| `s` | seam width in units of `w = √2/2` | `1 ≤ s ≤ 30` |

**Cells.** The carrier is *two* axis runs per axis rather than one, offset by a seam:

- run 1 on an axis: centres `1/2, 3/2, …, (k1 − 1/2)` — a full run of `k1` cells;
- run 2: the same run of `k2` cells, shifted by the seam `s·w` along that axis and drawn back by `o`;
- the carrier is the **product** of the two axes' run lists, so its cell count before notching is
  `P = (k1 + k2)²` — a grid, exactly the object run 143 proved cannot share area.

**Slots.** A centred 45° bar of `m` cells, `c_i = (L/2, L/2) + ((i − (m−1)/2)·1/2)·(1,1)`,
`i = 0 … m−1`, with `w = √2/2` the 45° cell's own half-extent — the seam width is the diamond's
half-extent, exactly (`w²·2 = 1`, control 1).

**Insertion rule (the notch).** A carrier cell is **dropped** when it touches or overlaps any slot.
Nothing else is removed, and the rule never moves a cell. This is what makes the carrier sparse:
`fill = n / (L/w)²` lands at `0.65-0.73` on the four certified members (control 5), and the axis
class splits into 2-4 translation domains while the tilted class stays one (control 5) — exactly doc
100's "fill < 1, a few translation domains".

**Side law.** Assembled as declared, not derived:
`L = (k1 + k2) + s·w − o`, i.e. `a + (s/2)√2` with `a = k1 + k2 − o`.

**Count law.** `n = P − dropped + m`, with `dropped` the number of distinct carrier cells the notch
removes. The family writes the *side in closed form* and the *count by construction*; the count is
read off the assembled pose, never assumed.

## 3. The exact gate and the controls

Every verdict is `qsqrt2.gate` on `Q(√2)` cells with no tolerance: `ok` iff every pair is separated
on some axis by an exact SAT slack `≥ 0`, plus exact containment in the `L × L` box. No float names
any decision: the module's 15 decision functions are bytecode-audited to **0 naming float** (control
8; `selftest` is the only exempt function).

`python3 scripts/seam_carrier.py --selftest` — **8 controls, exit 0**:

1. the seam width is the 45° cell's own half-extent: `w²·2 = 1` and `frame_extent(W45) = w`, exactly;
2. `n = 5` is reproduced as the delivered atom: `(1,1,0,1,1)` → `2 + 1/2√2`, gate ok;
3. the box shrink is refused: the same pose at `L − 1e-9` fails the gate;
4. the notch is load-bearing: keeping the 8 dropped cells of `(2,2,1,2,1)` gives **10 overlapping
   pairs**;
5. sparseness: `n = 5 / 10 / 9 / 32` at fill **0.6823 / 0.7277 / 0.6549 / 0.7113** (all < 1), axis
   domains **4 / 4 / 2 / 4**, tilt domains **1 / 1 / 1 / 1**;
6. containment and the two atoms: `n = 5` at `2 + ½√2`, `n = 10` at `3 + ½√2` (8 cells dropped),
   `n = 9` at `3 + ½√2`, every cell inside the box exactly; and the illegal `(2,3,1,3)` is **refused**
   with 2 overlapping pairs;
7. the exact side against a 60-digit `Decimal` shadow on all three sizes;
8. the bytecode audit: 15 decision functions, **0** naming float.

A fast counter (`count_for`, band-restricted, exact) reproduces `assemble` on every declaration it is
used for — it is a speedup of the same computation, not a second decision procedure.

## 4. The entry test

`python3 scripts/seam_carrier.py` — all 110 delivered two-class rows, every declaration with
`1 ≤ k1 ≤ a`, `0 ≤ o ≤ 2`, `k2 = a + o − k1`, `m` = the row's own tilted-class size, and the side group
`a + (s/2)√2` read off the delivered side (verified exactly to `1e-8`). A row counts only when a
declaration builds **exactly that count**, **exactly that side**, and clears the exact gate.

**Result: 2 / 110 reproduced.** The two are `n = 5` at `2 + ½√2` from `(1,1,0,1,1)` and `n = 10` at
`3 + ½√2` from `(2,2,1,2,1)` (8 cells dropped, 11 exact contacts) — the family's own calibration
atoms, and both exactly the delivered rows. **Threshold 20: FAIL. No sweep.**

The failure sorts into three disjoint classes, and the middle one is the informative one:

| class | rows | what happens |
|---|---|---|
| side + count both hit, gate **refuses** | **23** | `n = 27, 38, 52, 67, 104, 125, 149, 174, 201, 231, 262, 296, 331, 369, 408, 449, 493, 538, 586, 635, 686, 853, 974` |
| side + count both hit, gate **passes** | **2** | `n = 5`, `n = 10` |
| in the side group, **no member reaches the count** | 57 | e.g. `n = 65` (`5 + 5/2√2`, `m = 25`), `n = 124` (`6 + 4√2`, `m = 64`) |
| **not** of the form `a + (s/2)√2` | 28 | `n = 11, 18, 19, 26, 28, 50, 51, 54, 70, 85, 123, 126, 178, 230, 234, 295, 367, 368, 407, 448, 491, 626, 677, 730, 785, 842, 901, 962` |

(The 28 are the rows whose delivered side is *not* `a + (s/2)√2` for integer `a` and `1 ≤ s ≤ 30` —
the wider count of doc 100 allowed any rational `b`, 101 of 110. The family's side group is narrower
than the field: that is a property of the parameterisation, and it is reported rather than hidden.)

## 5. Diagnosis

**The side and the count are not the problem; the interlock is.** On the 23 refused rows the family's
declaration `(1, a, 1, m_hint, 1)` reproduces the delivered side *identically* — `L = 1 + a + ½√2 − 1`
— and reproduces the delivered count *identically*, and then the gate refuses the pose because the
two axis runs overlap each other. Measured pattern, row by row: `a` runs 5, 6, 7, 8, 10, 11, 12, 13,
14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 31 with `m_hint` always `a + 1..a + 12`, and in
each case the only declarations at that side are ones whose seam `o = 1` puts run 2 exactly one unit
inside run 1's span — the seam is *not a gap at all* when `s·w ≈ 0.707` and the interlock is one cell.

That is the same obstruction run 143 found from the other side, restated in carrier terms:

- a **full** product carrier (run 143) cannot share area because it fills its bbox;
- a **notched** product carrier (this run) removes cells only where the *bar* is, so it can share
  with the bar but **not with itself**: the notch rule has no authority over carrier-carrier
  overlap, and the gate correctly refuses rather than repairing. The "give-way" variant that lets
  run 1 win was measured and rejected in this run's design stage (`n = 10 → 8`, `n = 27 → 19`: it
  over-drops and destroys the count) — so this is not an implementation gap but the family's limits.
- the delivered rows need **both**: a carrier whose own translates are disjoint *and* which leaves the
  bar a void to sit in. The family supplies the second and not the first.

Two further numbers bound what a repair can buy: on the 57 exact-side rows with no count match, the
shortfall is structural — the family's `n = (k1+k2)² − dropped + m` cannot reach the delivered count
with `m` at the delivered tilted-class size, because `dropped` is at most the band (`≈ 3(k1+k2)`) and
the required `P` is too small; e.g. `n = 65` at `5 + 5/2√2` needs `k1 + k2 = 5 + o ≤ 7`, so
`P ≤ 49` and `n ≤ 49 + 25` with **no** drops, against a delivered 65.

## 6. What this changes

- Doc 100's instruction is honoured and its prediction **confirmed** in the direction that matters:
  the delivered rows need a *sparse* carrier (fill < 1 with several translation domains is reachable
  and is what the certified atoms look like), but a notched **product** is not enough. The next
  carrier must be sparse **by construction** — translates that are disjoint by a law, not by a drop
  rule — or the notch must be given authority over carrier-carrier overlap with a count-preserving
  repair.
- The entry test is cheap enough to keep as the first gate of every carrier run: the whole 110-row
  sweep runs in about two minutes in `Q(√2)` after the exact-prune fixes (the band counter, the
  offset-keyed collision memo, and the gate's own exact `|Δ| ≥ 2` skip reused as a pre-filter, which
  reproduces `gate.ok` on every declaration it admits and is still followed by the full gate on every
  pose the test accepts).
- **Refused: the sweep. Promoted: nothing.** `submission.csv` and root `WHITEBOARD.md` untouched.

## 7. Checks

`seam_carrier --selftest` **8 controls** (exit 0); `seam_carrier` entry test **2/110** (fail,
threshold 20) and ledger written; `shared_box --selftest` 9; `tilt_audit --selftest` 8;
`interleaved_boundary` 9; `twin_boundary` 5; `notch136`; `glm_plan` 5; `pure_slide`;
`beaten_leverage`; `band5`; `ext_census`; `range_leverage`; `construct_seam`; `p_screen`;
`legal_slide`; `structure --control`/`--check-solver`; `perturb`; `anchor_chain`; `void_insert`;
`true_geom`; `row_census`; `motif_wheels` 13; `crystal_domains` 4; `import_n090` 5;
`pub_bounds_check` 4; `witt_octad` 5; `leech_audit_fix`; `verify_certificates`; `sqscore`
**22.217428576** (554/446); `record_guard` OK; `glm_wheels --audit` 0 offenders; `py_compile` OK.

no row changed |
