# 20 — G-1: the r = 1 column in the exact t-basis

**Run 52, 2026-11-18.** Answers G-1 of `19-COLLECTION-AND-REVIEW.md` §6.
Instrument: `scripts/r1_atoms.py`; ledger `workspace/push/r1_atoms.json`.
Every number below is printed by that script from `submission.csv`; δ is
`Decimal(repr(L)) − k`, so it is exact to the stored 12 decimals.

## 1. The question

The column `n = k² + 1` (k = 1..31) carries one number, `δ = L − k`, and it
*steps*: 0.535534 for k = 8..24 and 0.520815 for k = 25..31. If that step is a
different angle **word**, it is a vocabulary target (a new construction). If it
is the same words arranged differently, it is an arrangement target. G-1's
falsifier: *same t-multiset ⇒ stop and go to G-2.*

## 2. Method — what counts as a word

Angles are reduced mod π/2 (a square is symmetric) and classified:

| class | test | t |
| --- | --- | --- |
| `axis` | \|sin 2θ\| < 1e-12 | 0 |
| `pi/4` | \|θ − π/4\| < 1e-11 | √2 − 1 (quadratic) |
| `t=a/b` | tan(θ/2) = a/b, **b ≤ 10⁴**, residual ≤ 1e-12 | rational |
| `other` | none of the above | printed as an angle |

The denominator bound is the whole point of the instrument. With b ≤ 10⁷ *every*
float angle is "rational" to 1e-12 — the first version of the script duly
reported `t = 4258896/9585127` for the k = 6 row. A 10⁴ bound makes `t = 1/3` a
word and leaves a numerically-optimised angle as what it is: a number with no
declared basis. `pi/4` is separated from the nearest rational near-45
certificate (225058681/543339720, 1e-10 away) by the 1e-11 window.

## 3. The column, measured

| k | n | δ = L − k | exact δ | tilt | alphabet |
| ---: | ---: | ---: | --- | ---: | --- |
| 1 | 2 | 1.000000001 | `1` | 0 | axis only |
| 2, 3 | 5, 10 | 0.70710678 | `√2/2` (h 3) | 1, 2 | axis + π/4 |
| 4 | 17 | 0.675530095 | **no small form** | 7 | axis + 39.805°(6) + 53.376°(1) |
| 5 | 26 | 0.621320345 | `3(√2−1)/2` (h 8) | 9 | axis + π/4 |
| 6 | 37 | 0.598619611 | **no small form** | 15 | axis + 42.087°(6) + 47.913°(6) + π/4(3) |
| 7 | 50 | 0.571428573 | `4/7` (h 11) | 16 | axis(34) + **t = 1/3** |
| 8–24 | 65–577 | 0.535533908 | `5/√2 − 3` (h 13) | 25…145 | axis + π/4 |
| 25–31 | 626–962 | 0.520815282 | `17/√2 − 23/2` (h 42) | 289 | axis + π/4 |

"h" is the height `|a|+|b|+c` of the fit `(a + b√D)/c`; all residuals are
−1.4e-9…−4e-9, which is the finalizer's ~2e-9 clearance pad, not algebra error.
The fits are searched over D ∈ {2,3,5,6,7,10,11,13,17} at height ≤ 240; a δ with
no fit inside that box is reported as having none, not as irrational.

## 4. The one structural difference at k = 25

Every row carries a **45° diamond**: squares on a lattice of spacing 1/√2 whose
centres span `p` positions per axis. A *full* p×p diamond is p² unit squares in a
p√2 × p√2 block — the zero-waste 45° packing.

| rows | p | occupancy (count/p²) | diamond side | L |
| --- | ---: | ---: | ---: | ---: |
| k = 8–16, 19–22 | 5 | **1.000** | 7.0711 | k + 0.535534 |
| k = 17, 18 | 9, 12 | 0.617, 0.660 | 12.73, 16.97 | k + 0.535534 |
| k = 23 | 15 | 0.578 | 21.21 | 23.535534 |
| k = 24 | **17** | **0.502** (145/289) | 24.0416 | 24.535534 |
| k = 25–31 | **17** | **1.000** (289/289) | 24.0416 | k + 0.520815 |

k = 24 and k = 25 carry the *same* diamond — same p = 17, same spacing 0.7071068,
same 24.0416 side — one half-filled, one full. The δ step is 0.014719 and the
diamond fill changes 145 → 289 while the axis fill goes 432 → 337.

## 5. The answer

**SAME alphabet.** Both bands use `{axis, π/4}` and nothing else; the δ step is
not a new word. It is a different **coefficient of the same √2 word** —
`5/√2 − 3` → `17/√2 − 23/2`, both in ℚ(√2), carried by a fuller diamond.

So, per G-1's falsifier: **stop, go to G-2** — but with the target sharpened. The
k ≥ 25 atom is not mysterious and not a new vocabulary item; it is *a full p×p
diamond of side p√2 inside the axis fill*, at p = 17. That is a parameter for a
declared wheel (`M-diamond(p, t)`), not a search.

## 6. The by-product, which is the larger result

Across all 31 rows, **the field of δ is the field of the alphabet**:

* axis only → δ = 1 exactly (ℚ);
* π/4 rows → δ ∈ ℚ(√2) always: √2/2, 3(√2−1)/2, 5/√2 − 3, 17/√2 − 23/2;
* the one row with a **rational** t (k = 7, t = 1/3) → δ = **4/7**, rational;
* the two rows whose angles are **not** declared words (k = 4, 6) are exactly the
  two rows whose δ has **no small algebraic form** at height ≤ 240.

31/31. This is the "score is a property of the word" claim of `19` §5 turned into
a measurement: the score's field tracks the alphabet's field, and where there is
no alphabet there is no small algebraic δ. It is the strongest evidence yet that
the generative side (§5 of `19`) is the right side to work.

## 7. What this does not show

* The `(p, −c)` reading of the band constants — `(5, −3)` and `(17, −23/2)` — is
  an observation, not a derivation. It cannot be a per-row formula: k = 17..24
  carry p = 9…17 and still hold `5/√2 − 3`, so p in the constant belongs to the
  band's base, not to the row. Any formula must be derived, not fitted — the
  fits in §3 are already at the edge of what a 9-digit δ can distinguish.
* Nothing here produces a packing. It prices one: the k ≥ 25 atom is a full
  17×17 diamond, worth 0.014719 in δ on 7 rows.
* The t-basis of a *tilted* square is only as exact as the stored angle. These
  are declared classes, not certificates; certification remains
  `workspace/push/exact_replay37.json` and the Fraction replay track.

## 7a. Follow-up (run 53, `21-SEAM-WHEELS.md`)

The §4 diamond table is now a *declaration* rather than an observation:
`seam_wheels.describe` reads a row as (p, half-integer block offset, wall
anchors) and rebuilds it in ℚ(√2), and the two atoms reproduce exactly — n = 65
as p = 5 with 8+8 upright columns and δ = `5/√2 − 3`, n = 626 as p = 17 with
25+24 columns and δ = `17/√2 − 23/2`, both gated with worst penetration 0. Two
facts from that run belong next to §4's table: **no tilted square touches a wall
in either atom** (the upright fill holds the block), and the partial rows in the
table's 0.502–0.660 occupancy band are exactly the rows this declaration refuses.
The §5 verdict stands and is now measured on the seam itself: solving the
declared seam returns the delivered side on all 14 full-diamond rows, so the
0.0147 step is not recoverable by improving the boundary.

## 8. Files

* `scripts/r1_atoms.py` — the instrument (word classifier, δ fits, diamond).
* `workspace/push/r1_atoms.json` — ledger: 31 rows, families, fits, verdict.
* answers `19-COLLECTION-AND-REVIEW.md` §6 G-1; feeds G-2 (`M-diamond(p, t)`),
  which is run 53 — `21-SEAM-WHEELS.md`.
