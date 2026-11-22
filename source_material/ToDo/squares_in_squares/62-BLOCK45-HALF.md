# 62 — The half-integer corner fill: the side is exact, the fill is not, and the half unit is slack

Run 99, 22 November 2026. One production, built exactly, gated, and answered honestly.

Doc 61 §8 named it and gave it a falsifier: build the `t ∈ ℤ + ½` corner fill with the extra
staircase squares the half unit admits, and ask whether any `(s, k)` reaches `L = 2k + 0.520815`
at `N = 677, 785, 901` with clearance 0.

The answers, one line each:

* the half unit admits **no extra triangle square**: a unit axis square fits iff `i + j + 2 ≤ t`,
  so `t` enters only through `⌊t⌋`, and the laws are `T = k(k−1)/2` per corner,
  `N = s² + 2k(k−1)`, `L = max(s/√2 + k + ½, s√2)`;
* the exact **dominance law**: the half member at `k` is run 98's integer contact member at
  `k − 1`, same `N`, side never smaller and at most `½` larger — and at the seven delivered
  counts run 98 reproduces exactly, the half fill is **exactly `½` behind**;
* feasibility is one inequality, `L ≥ 2k − 2`, and the sweep agrees with it on **all 124 rows**
  (76 gated, 48 refused), the window at `s = 17` being `k ≤ 14` with `4, 12, 24, 40` colliding
  pairs at `k = 15, 16, 17, 18`;
* the falsifier **fails, and it fails precisely**: the delivered sides at 677/785/901 are
  *exactly* `s/√2 + k + ½` at `k = 14, 16, 18`, so the half-integer **side** law is the delivered
  side with no tolerance — while the corner fill at that side holds `653, 769, 901` against the
  rows' `677, 785, 901`, short by `24, 16, 0`, and only the first is a sentence;
* so **no certified half-integer sentence reaches `L = 2k + 0.520815` at the three counts**;
  `0` of `76` gated rows beats a delivered row and `0` is at parity.

`submission.csv` and root `WHITEBOARD.md` are untouched; no row moved, no score claimed.

## 1. The construction, and why the half unit adds nothing

The block is run 98's: `s²` unit squares at the 45° word, edge to edge in its own frame,
centred in the container. Its faces are `x + y = L ∓ s/√2` and `y − x = ±s/√2`, so each corner
region is the triangle `x, y ≥ 0`, `x + y ≤ t` with

    t = L − s/√2 .

A unit axis square `[i, i+1] × [j, j+1]` sits inside that triangle iff its far corner does:
`i + j + 2 ≤ t`. **That is the whole of it.** The half unit therefore cannot add a square: for
every integer `i + j`, `i + j + 2 ≤ k + ½` and `i + j + 2 ≤ k` are the same condition, so

    T_half(k) = #{(i, j) ≥ 0 : i + j ≤ k − 2} = k(k−1)/2          per corner
    N(s, k)   = s² + 4·T_half(k) = s² + 2k(k−1)
    L(s, k)   = max( s/√2 + k + ½ , 2s/√2 ) .

In `Q(√2)` this is `cls(0, s/2) + cls(k) + cls(1/2)`, compared with `cls(0, s)` for the block's
own diagonal — exact, no root-finding, the separation roots *are* the law. `block45half_count`
is integer arithmetic; `block45half_side` compares two field elements.

The half unit changes the **side**, not the count: a sentence can stand half a unit further out
and hold exactly the same squares. That is visible in the gate too — every staircase square is
`1/(2√2) = 0.353553` clear of the block's face, so the sentence has **no axis-to-block contact**
at all, while run 98's integer sentence has its last staircase square tangent to the face.

*Correction to doc 61 §8.* That section read the delivered rows' `t = 14.5` and "six extra
squares per corner" as the half unit admitting staircase squares. The arithmetic says otherwise:
at `t = 14.5` the staircase holds `T(13) = 91` per corner — the *same* as at `t = 14` — and the
delivered 677 row's `388 = 4 × 97` axis squares are therefore not four corner staircases. §5
measures what they are instead.

## 2. The dominance law

The half member at `k` and the integer member at `k − 1` have the **same count**:

    N_half(s, k) = s² + 2k(k−1) = s² + 2(k−1)k = N_int(s, k−1) .

Their sides are the same two quantities offset by `½`:

    L_int = max(h + k, 2h) ,       L_half = max(h + k + ½, 2h) ,       h = s/√2 ,

so `L_int ≤ L_half ≤ L_int + ½`, always. Three cases, all three asserted in control 30:

| case | example | `L_half − L_int` |
|---|---|---|
| both fill-bounded | `(17, 14)` vs `(17, 13)` | exactly `1/2` |
| both block-bounded | `(5, 2)`: both `= 5√2 = 7.071068` | `0` |
| mixed (half fill, integer block) | `(3, 2)`: `4.621320 − 4.242641` | `5/2 − 3/2√2 = 0.378680` |

So `t ∈ ℤ + ½` can never be the better sentence: it is its integer sibling, same count, and its
side is never smaller — and the gap is `½` in the ordinary case.

The dominance is measurable against the table, not just in algebra. Run 98 established seven
counts at which its integer sentence *is* the delivered row (`N = 5, 40, 65, 89, 124, 148, 233`).
At each of them the half member's side is exactly `½` behind the delivered side:

| `N` | half member `(s, k)` | delivered side | half side − delivered |
|---|---|---|---|
| 5 | (1, 2) | `2 + ½√2` | **−0.500000** |
| 40 | (4, 4) | `4 + 2√2` | **−0.500000** |
| 65 | (5, 5) | `5 + 5/2√2` | **−0.500000** |
| 89 | (7, 5) | `5 + 7/2√2` | **−0.4999999999999** |
| 124 | (8, 6) | `6 + 4√2` | **−0.500000** |
| 148 | (8, 7) | `7 + 4√2` | **−0.500000** |
| 233 | (11, 8) | `8 + 11/2√2` | **−0.500000** |

(`N = 89` reads `−0.4999999999999` because the delivered side is the exact lift of a 12-dp pose;
the gap is `½` to the pose's own `1e-9`.) This is the dominance law measured in the units the
table is written in: where the grammar owns the row, the half-integer fill loses by exactly half
a unit.

## 3. Feasibility is one inequality, derived and checked

The staircases at the two ends of a wall,

* corner 0's reaching `x = k − 1` (its `i = k−2` square spans `[k−2, k−1]`),
* corner 1's starting at `L − (k−1)`, in the same row band `y ∈ [0, k−1]`,

interpenetrate exactly when `L − (k−1) < k − 1`, i.e.

    L ≥ 2k − 2 .

With `L = s/√2 + k + ½` that is `k ≤ s/√2 + 5/2`, so the window is `k ≤ ⌊s/√2⌋ + 2` or `+ 3`
according to `frac(s/√2)`. The code states the inequality itself (`block45half_feasible`) and the
sweep checks it against the gate on every row: **124 rows, gated ⟺ feasible, 0 mismatches.**

| `s` | gated `k` | refused `k` |
|---|---|---|
| 1 | 2, 3 | ≥ 4 |
| 5 | 2–6 | ≥ 7 |
| 9 | 2–8 | ≥ 9 |
| 13 | 2–11 | ≥ 12 |
| 17 | 2–14 | 15, 16, 17, 18, … |

At `s = 17` the colliding pairs grow with the overshoot: **4** at `k = 15`, **12** at `k = 16`,
**24** at `k = 17`, **40** at `k = 18` — the same counts run 98 measured for its integer
neighbours, because the two families' staircases are the same objects.

## 4. The floor, honestly

In the contact branch the family's own excess is

    L − 2k = s/√2 + ½ − k .

At the top of the window the excess lands in `(−2.5, −1.5]` (it decreases by exactly `1` per
`k`), and because different `s` put the window's top at different offsets from `0`, the family
crosses zero inside the window too. The sweep's certified values approach zero from both sides:
the closest above is **`+0.035534`** at `(5, 4)`, `N = 49`, and the closest below **`−0.085786`**
at `(2, 2)`, `N = 8`. 29 of the 76 gated rows have `L − 2k < ½√2`, so the inequality of the session's
headline question is met — at essentially every scale — and none of it is a record:

* the family's `k` **is not the ridge's `k`**: it counts corner staircase rows, while `2k + ½√2`
  is a statement about the ridge's half-block. A negative `L − 2k` here means the block's
  half-diagonal is shorter than the corner parameter, not that a packing is tight;
* the only like-for-like comparison is at the same `N`, and there the family is behind every
  delivered row it shares a count with: **0 beats, 0 parity, 53 gated rows with a delivered
  count**, the closest being `−0.207107` at `N = 13`, `−0.292893` at `N = 85`,
  `−0.328427` at `N = 56`, `−0.449747` at `N = 133`, and exactly `−0.5` at the seven counts of
  §2;
* and §2's dominance law says the same thing structurally: every half member is an integer
  contact member plus half a unit of side.

Contrast run 98, where the inequality was met by a family whose excess was *positive but small*
(`+0.020815` at `N = 653`). Here the inequality is met by moving `k`, which is free; the count
does not follow. That is the difference between a floor result and a parameterisation artefact,
and it is worth stating in one line: **`L − 2k` is not the record functional for a block family.**

## 5. The falsifier at 677, 785, 901 — the side matches exactly, the fill does not

The delivered rows' sides, lifted exactly from their 12-dp poses (the convention of runs 96–98),
are

| `n` | exact lifted side | `= s/√2 + k + ½` | half member `k` |
|---|---|---|---|
| 677 | `29/2 + 17/2√2` | `12.020815… + 14.5` | 14 |
| 785 | `33/2 + 17/2√2` | `12.020815… + 16.5` | 16 |
| 901 | `37/2 + 17/2√2` | `12.020815… + 18.5` | 18 |

All three equalities are **exact in `Q(√2)`**, not `1e-9` approximations: the half-integer side
law is the delivered side. (Control 30 asserts the 677 identity; `--block-half-spin`'s
calibration asserts all three and the ledger records them.)

The other half of the question is the count, and there the identification stops:

| `n` | half member `(s, k)` | corner fill `N` | short by `n − N` | gate verdict | contacts |
|---|---|---|---|---|---|
| 677 | (17, 14) | 653 | **24** | **gated**, clearance 0 | 2256 |
| 785 | (17, 16) | 769 | **16** | `block45half_corner_collision` (12 pairs) | — |
| 901 | (17, 18) | 901 | **0** | `block45half_corner_collision` (40 pairs) | — |

At the delivered 677 side the corner fill certifies **653** squares — 24 fewer than the row —
and it is the only one of the three that is a sentence. At the 785 side the fill is 16 short
*and* infeasible. At the 901 side the count and the side both coincide with the delivered row,
and the arrangement refuses: `L = 30.520815… < 2k − 2 = 34`, so the two staircases on each wall
overlap by 3.48 units and the gate reports 40 colliding pairs.

So the delivered 901 row is **the half-integer corner fill's count and the half-integer corner
fill's side, in an arrangement the centred corner fill cannot take.** That is a sharper answer
than doc 61's "901 is the family's count but infeasible": it is the *half* family's arithmetic
exactly, and the failure is placement, not arithmetic. The 24, 16 and 0 are the axis squares that
live outside the four corner triangles — notch/band squares, which §10 names as the next
production.

The requested `k = 13, 14, 15` and `k = 16, 17, 18` columns at `s = 17`, exactly:

| `k` | `N` | `L` | `L − 2k` | delivered side at `N` | verdict |
|---|---|---|---|---|---|
| 13 | 601 | 25.520815… | −0.479185 | — | gated |
| 14 | 653 | 26.520815… | −1.479185 | — | gated (2256 contacts) |
| 15 | 709 | 27.520815… | −2.479185 | 27 | refused, 4 pairs |
| 16 | 769 | 28.520815… | −3.479185 | 28 | refused, 12 pairs |
| 17 | 833 | 29.520815… | −4.479185 | 29 | refused, 24 pairs |
| 18 | 901 | 30.520815… | −5.479185 | `37/2 + 17/2√2` (**equal**) | refused, 40 pairs |

Two exact readings of the last three rows: at `N = 709, 769, 833` the delivered rows are grids at
`L = 27, 28, 29`, and the half side law sits exactly `0.520815 = 17/√2 − 23/2` above them; at
`N = 901` the delivered row is not a grid row, and the half law coincides with it. The constant
`0.520815` the session asked about is exactly this offset — it is a *side* relation, and it does
not carry a fill.

Count refusals: `677` is no count of the family at all (no `(s, k)` with `s ≤ 30, k ≤ 25`;
`677` would need `T = 97` per corner, and `k(k−1)/2 = 97` has no integer solution). `785` *is* a
count — at `(s = 5, k = 20)`, a 5×5 block with a twenty-row staircase — and it is refused:
`L = 24.036… < 2k − 2 = 38`. Both are asserted in control 30.

## 6. Above `n = 1000`: exact, and still the grid in disguise

One certified row (the gate is minutes per thousand cells, so the rest are law, labelled):

| `s` | `k` | `N` | `L` | void `L² − N` | `L/√N` | grid | verdict |
|---|---|---|---|---|---|---|---|
| 25 | 20 | 1385 | `41/2 + 25/2√2` = 38.177670 | `−2609/4 + 1025/2√2` = 72.534451 | 1.025852 | 38 | **gated**, 5016 contacts |
| 35 | 27 | 2629 | `55/2 + 35/2√2` = 52.248737 | `−5041/4 + 1925/2√2` = 100.930554 | 1.019015 | 52 | law only |
| 50 | 37 | 5164 | `75/2 + 25√2` = 72.855339 | `−10031/4 + 1875√2` = 143.900429 | 1.013837 | 72 | law only |

The certified row is `0.177670` outside `⌈√1385⌉ = 38`; the ratio `L/√N → 1` exactly as in run
98, because `N ≈ 2s²` and `L ≈ s√2`. The half family adds nothing above 1000 that the integer
family does not already have — it is the same sentence, half a unit wider (§2) — so this table is
reported as a consistency check, not as a frontier.

## 7. Rung 3 over rung 2, and rung 7

The half unit is exactly where the 7-rung ladder's first two levels differ, and this run is a
concrete instance of that difference:

* **Rung 2 (integer) is blind to the half** — `integer_indist_zero_half`. The corner count is a
  function of `⌊t⌋`: `T(k + ½) = T(k) = k(k−1)/2`, exactly. An integer-only reader given `t`
  cannot tell `14` from `14.5`, and would price the delivered 677 corner at 97 squares or 91
  without knowing which.
* **Rung 3 (rational/algebraic) sees it** — `rational_distinguishes_zero_half`, in its packing
  form. In `Q(√2)` the two legs are different numbers, and the difference is exactly what the
  table's rows carry: `L` moves by `½` while `N` does not, and the delivered sides
  `29/2 + 17/2√2`, `33/2 + 17/2√2`, `37/2 + 17/2√2` are *exactly* the half-integer legs. The
  rational rung buys the side law, and nothing else.
* **Rung 7 (certificate) decides.** Seeing the half does not make it a sentence. The exact gate
  at clearance 0 accepts `k = 14` and refuses `k = 16, 18` — the same arithmetic that produced
  the delivered 901 side. This is the ladder's own discipline: a representation that *sees* a
  coordinate still has to certify what it sees, and here the certificate says the centred corner
  fill cannot exist at the delivered 901.

The Lean anchors named in this section are `integer_indist_zero_half` and
`rational_distinguishes_zero_half` (`workspace/lean/tct_squares/TCT/Layers.lean`, `01-LAYERS.md`);
they are conceptual references only, not a build dependency, and no Lean compilation is attempted
here.

## 8. Verification

* `glm_wheels.py --selftest` — **30 controls, exit 0, 2 m 30 s**; control 30 is new and asserts
  the count law over `s, k ≤ 8` (including `T_half(s, k) = T_int(s, k−1)`), both side branches,
  the three dominance cases, the gated `(17, 14)` sentence with its `½` of dominance, the
  `k = 15` and `k = 18` collisions, the exact 677 side identity, the 24/16/0 deltas, the
  feasibility flags `[True, False, False]`, and the two count facts (677 absent; 785 present only
  at `(5, 20)` and infeasible).
* `glm_wheels.py --audit` — **265 functions, 0 offenders** (up 7: `block45half_count`,
  `block45half_side`, `block45half_feasible`, `_block45half_sentence`, `p_block45half`,
  `block45half_spin`, `block45half_calibrate`; no float named).
* `glm_wheels.py --block-half-spin` — 124 rows (every `(s, k)` with `N ≤ 250`, plus
  `(17, 13) … (17, 18)`), **76 gated, 48 `block45half_corner_collision`**, 29 below `2k + ½√2`,
  **0 beating the delivered row, 0 at parity**, `3 m 18 s`, ledger
  `workspace/push/block45half_spin.json` (with the three-row calibration).
* `glm_wheels.py --block-half-beyond` — the gated `N = 1385` row and the two law rows,
  `22 s`, ledger `workspace/push/block45half_beyond.json`.
* Feasibility law and dominance law re-checked *against the ledger*: 124/124 and 53/53.
* `glm_wheels.py` bare run exit 0, ledger `workspace/push/glm_wheels.json`;
  `record_guard.py` OK; `family_spin.py --calibrate/--gate-ks/--beyond`,
  `grammar_induction.py`, `qsqrt2.py`, `field_triage.py` unchanged and green.
* README/STATUS footers byte-identical from `## Current results`.

## 9. Honesty about what is proved and what is measured

* **Proved (exact, `Q(√2)` throughout):** the count law and the floor argument that the half unit
  adds no triangle square; the side law, both branches; the dominance law in all three cases; the
  feasibility inequality on all 124 swept rows; the 76 gated sentences (clearance 0,
  `gate_L == L`); the 48 collision refusals with their pair counts; the exact delivered-side
  identities at 677/785/901; the deltas 24/16/0; the count facts at 677 and 785.
* **Measured (the exact lift of the 12-dp pose, `Decimal` at 70 digits):** every statement about
  a delivered *row*'s side or count — including the `−0.4999999999999` at `N = 89`, which is the
  pose's own `1e-9`, and the `0.520815` offsets against the grid rows at 709/769/833. Those rows
  are poses, not sentences (run 95's `−2.365e-9` overlap is the standing evidence).
* **Not claimed:** that the half-integer fill is a frontier family (it is dominated, §2); that
  `L < 2k + ½√2` is a record at any scale (§4); that no other topology can beat the floor. This
  run settles one production exactly and reports the one thing it does establish: the delivered
  low-slack sides *are* the half-integer side law, and the fills are not the corner fill.

## 10. What this means for the next run

The difference between the delivered rows and this fill is a **count**, not a side: `24`, `16`
and `0` squares at the same three sides. Those squares cannot be in the four corner triangles —
a triangle of legs `14.5` holds at most 91 unit squares, and the 677 row carries 97 per corner
role. They sit in the notch and band regions where the free space around the block is wider than
a triangle: the measured pose at 677 is an off-centre block with two wide bands, and its 388 axis
squares are a row/band fill, not four staircases.

So the next production is the **band fill**: derive the count of unit squares in the free region
of the box (rows anchored at the walls, the block's `L1` distance law
`d(a) + d(b) ≥ s/√2` deciding each cell), and ask whether that closed form reproduces `677`,
`785`, `901` at their delivered sides with clearance 0. The falsifier is exact and narrow: a
count law `B(s, k)` with `B(17, 14) = 97` per corner (or 388 total), `B(17, 16) = 124`,
`B(17, 18) = 153`, and a gated sentence at `k = 16` and `k = 18` — the two cases this fill
refuses. If the bands close, the delivered 677/785/901 rows are grammar; if they do not, the
half-integer leg is a pose and the frontier there stays measured rather than proved.
