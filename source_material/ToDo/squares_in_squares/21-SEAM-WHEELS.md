# 21 — G-2: the seam, declared, solved, certified

**Run 53, 2026-11-18.** Instrument `scripts/seam_wheels.py` (selftest 20/20),
ledger `workspace/push/seam_wheels.json`; the reconstruction wheel is registered
in `motif_wheels.py` (`M-diamond`, selftest 13/13). Read-only: no row changed,
no score claimed, `submission.csv` untouched.

## 1. What was asked, and what this answers

The review of `20` made three demands and named one first run:

1. **`M-diamond` must reconstruct the two known atoms before it is asked to beat
   either** — integer parameters, exact count, exact side, wall-contact
   signature, and a reproduction of `5/√2 − 3` and `17/√2 − 23/2`.
2. **`M-seam` as a bounded solve over a declared layout**, where a float answer
   nominates and exact arithmetic certifies, and where *layout not enumerated*,
   *numerically inconclusive*, *exactly infeasible* and *feasible but no gain*
   are four different ledger outcomes.
3. **Rank by the score the cascade actually delivers**, and separate "can this
   construction work" from "would it matter if it did".

The first run asked for: reconstruct the two atoms, then compare the current
band, a mirrored band, and a staircase seam at the same count and side budget;
the deliverable is either a verified new base **or** a ledger that names the
bottleneck (count, wall fit, seam overlap, or no gain).

This run delivers all three on the r = 1 column, and the answer is the fourth
bottleneck: **no gain.** The seam is already optimal for the arrangement, and
the remaining score is not in the boundary at all (§5, §6).

## 2. The declaration: integers in, side out

A delivered atom is read as integers only (`describe`):

| parameter | meaning |
| --- | --- |
| `p` | diamond extent: a `p × p` block of unit squares at exactly 45° |
| `dx, dy` | the block's offset from the container centre, in **half-integers** |
| `(m, i, m', j)` per upright square | wall anchors: `m = 0 → 1/2 + i`, `m = 1 → L − 1/2 − i`, `m = 2 → L/2 + i` |

Two facts make this exact rather than fitted. The 45° block is **not** a free
lattice: a `p × p` tiling of the rotated frame has centres exactly

    c + ((u − v), (u + v − p + 1)) · √2/2,      u, v = 0 … p − 1

and every upright coordinate is `a + b·L` with `a, b ∈ ½ℤ`. So the whole atom
lies in ℚ(√2) and the **only free scalar is the side L**. `describe` recovers
the integers from a row, rebuilds the row from them, and refuses if the two do
not agree to 1e-8 — the declaration is either a fact about the row or it is not
accepted.

## 3. Reconstruction — the acceptance test passes

`exact_gate` recomputes containment and all pair penetrations in ℚ(√2) with no
floats. The two atoms:

| n | k | p | columns | δ measured | exact δ | exact side L | walls (upright/tilted) |
| ---: | ---: | ---: | --- | ---: | --- | --- | --- |
| 65 | 8 | 5 | 8 + 8 | 0.535533908 | `5/√2 − 3` = `−3 + 5√2/2` | `5 + 5√2/2` | 8, 8, 8, 8 / 0 |
| 626 | 25 | 17 | 25 + 24 | 0.520815282 | `17/√2 − 23/2` = `−23/2 + 17√2/2` | `27/2 + 17√2/2` | 24, 25, 25, 25 / 0 |

Both gate exactly with worst penetration **0** — the side is the algebraic
number, not a fit. The stored row is that side **+1.8e-9** (n = 65) and
**+1.9e-9** (n = 626): the finalizer's contact pad, which matters in §4.

The wall signature is the fact worth carrying forward: **in both atoms no tilted
square touches a wall.** The 45° block is held in place entirely by the upright
fill, which meets all four walls with 8 squares per wall at n = 65 and 24–25 at
n = 626. A seam is therefore never a block-to-wall problem in this family; it is
a block-to-fill problem.

Coverage, honestly: the declaration is tested as a wheel on all 30 rows
`n = k² + 1`, k = 2…31, and reproduces **19** of them (n = 5, 26, 65, 82, 101,
122, 145, 170, 197, 226, 257, 362, 401, 442, 485, 626, 730, 842, 962). The 11
refusals are the **partial diamonds** — n = 290, 325, 530, 577 and siblings carry
50, 95, 130, 145 tilted squares instead of a full `p²`, which is exactly the
occupancy-0.502–0.660 set tabulated in `20` §4. Those rows need a mask, not a
`p`, and they are where the other half of the 0.0147 step lives.

## 4. The solve: the LP nominates, ℚ(√2) certifies

`lp_seam` minimises L over three variables — the side and the block's
translation — subject to one **declared separating axis per seam pair**, signed
by the side the delivered row puts the block on. Every inequality is linear
because each coordinate is `a + b·L`; the declaration is the discrete part the
review asked for, and the solver only answers "how tightly can *this* fit".

Three liabilities are kept apart in the ledger: the declaration (a rebuild
mismatch is `layout_not_enumerated`), the float solve (HiGHS, nominal), and the
certificate (the nominated side is snapped to ℚ(√2) and replayed through
`exact_gate`).

**Result: on all 14 full-diamond r = 1 rows the LP returns exactly the delivered
algebraic side**, with the block pinned and with it free to translate:

| n | delivered (stored) | LP optimum = exact side | difference |
| ---: | ---: | ---: | ---: |
| 65 | 8.535533908 | 8.535533906 | 1.8e-9 |
| 101 | 10.535533908 | 10.535533906 | 1.8e-9 |
| 257 | 16.535533908 | 16.535533906 | 1.9e-9 |
| 485 | 22.535533910 | 22.535533906 | 3.7e-9 |
| 626 | 25.520815282 | 25.520815280 | 1.9e-9 |

**The 2e-9 trap, recorded because it bit.** The first sweep reported
`feasible_gain` of `0.000000002` on *every* row: the exact side of an atom is
2e-9 below its stored side, because `packlib.finalize` opens every contact by
that much. Comparing an unpadded algebraic side with a padded stored side is not
a gain — it is the pad. `GAIN_MIN = 20 × PAD = 4e-8` now separates them, and the
`feasible_no_gain` detail prints the difference so the pad is visible rather
than inferred. This is the seventh instrument defect of the kind catalogued in
`19` §2.6: a private scale, silently compared.

## 5. One structural choice at a time

With the orientations frozen, each variant changes exactly one thing the review
listed, and is solved by the same LP:

Every number below is the certified exact side **minus the delivered one**, so a
positive number is a loss to the delivered table:

| n | seam (pinned) | seam (free) | mirrored | seam turned (x) | partial row (fullest) | partial row (seam) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 65 | 0 | 0 | 0 | 0 | +0.500000 | +0.500000 |
| 82 | 0 | 0 | 0 | **+1.121320** | +0.500000 | +0.500000 |
| 101 | 0 | 0 | 0 | 0 | +0.500000 | +0.500000 |
| 122 | 0 | 0 | 0 | **+1.121320** | +0.500000 | +0.500000 |
| 145, 197, 257 | 0 | 0 | 0 | 0 | +0.500000 | +0.500000 |
| 170, 226 | 0 | 0 | 0 | **+1.121320** | +0.500000 | +0.500000 |
| 362, 401, 442, 485 | 0 | 0 | 0 | LP infeasible | LP infeasible | LP infeasible |
| 626 | 0 | 0 | 0 | **+1.307612** | **+0.742641** | **+0.742641** |

* **mirrored** — every wall anchor swapped, block reflected: **exactly zero on
  all 14 rows.** The atoms are mirror-symmetric, so this knob does not exist.
* **seam turned (x only)** — x-anchors flipped, y left alone: zero on the 5 rows
  whose layout is already x-symmetric, `3√2/2 − 1 = 1.121320` on four,
  `+1.307612` at n = 626, and infeasible on four. Turning one seam is never free
  and sometimes impossible.
* **partial row moved** — one upright square re-placed in the emptiest row:
  exactly `+0.5` on nine rows, `+0.742641` at n = 626, infeasible on four. The
  two choices of source square coincide everywhere they are feasible, which says
  the partial-row end is unique.

Outcome tally over the whole sweep (14 rows × 6 cells, plus 4 rows the
declaration refuses): **71 `feasible_no_gain`, 12 `lp_infeasible`, 4
`layout_not_enumerated`, 1 candidate rejected at the exact gate, 0
`feasible_gain`.** That last label is `candidate_rejected_exact` since run 54
(§11): a rounded point that fails the gate, with its eight half-step neighbours
also tried, is a rejected candidate, not a proved infeasibility.

Read together: the arrangement sits at a local optimum in every declared degree
of freedom — block position, block mirror, seam turn, partial-row end. Every
non-trivial move costs a half unit or more, and none is free. **The boundary
cannot be improved while the block is kept**, which is the question the review
asked. The r = 1 atom is a different-*block* target, not a better-boundary one.

## 6. Ranked by what the cascade pays — the target moves

`cascade_rank` replays **one** base to the end of its column (`(r, δ)` is the
cascade invariant from `09` §2). The first version summed every (base, row) pair
and reported 0.731635 for r = 1; that number counted each row once per base, i.e.
multiplied by the column length. Corrected, and with the Karakuş floor as the
optimistic base side:

| column | rows | k | δ* (its own best) | pays now | optimistic | floor at base |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| r = 1 | 30 | 2–31 | 0.520815 | **0.153449** | 0.971058 | 0.192582 |
| r = 2 | 29 | 3–31 | 0.535534 | 0.303951 | 0.705237 | 0.372281 |
| r = 6 | 26 | 2–31 | 0.591378 | **0.589705** | 1.332026 | 0.192582 |
| r = 7 | 25 | 2–31 | 0.612885 | **0.584422** | 0.995378 | 0.372281 |
| r = 8 | 24 | 3–31 | 0.633983 | 0.425392 | 1.179826 | 0.140055 |

"pays now" = what a base **as good as the column already is** pays when it
exists at the bottom of the column. For r = 1 that is 0.153, and the delivered
table already contains the good base — at k = 25, where it cannot lift the rows
below it. That is the measured content of `19` §4.3's "the r = 1 column is worth
0.0365 per 0.01": the base exists, just too high in the column.

**The base-less window is priced out.** The correct residue census (`n − ⌊√n⌋²`)
confirms residues **38–60 plus r = 0** are base-less — 24 columns, as `19` said.
But a residue r only exists for `k ≥ (r−1)/2`, so r = 38 cannot start below
n = 438 and has 13 rows. The upside of *one base* at the Karakuş floor:

| base-less column | rows | first n | reachable | slack* | upside |
| --- | ---: | ---: | ---: | ---: | ---: |
| **r = 38** | 13 | 438 | 12 | 0.951161 | **0.022703** |
| r = 40 | 11 | 481 | 10 | 0.953438 | 0.017919 |
| r = 42 | 10 | 526 | 9 | 0.955512 | 0.015071 |
| r = 44 | 9 | 573 | 8 | 0.957408 | 0.012554 |
| r = 39 | 12 | 439 | 12 | 0.975595 | 0.011336 |
| … r = 60 | 1 | — | — | — | 0 (the bound equals the grid) |

So the highest-upside base-less residue in the 38–47 window the review named is
**r = 38 at 0.0227**, and that is an *upper* bound. It is one seventh of the
0.1637 needed, and it is an order of magnitude below one base in r = 6 (0.590).
`19` §4.3's "0.10–0.26 per residue at δ ≈ 0.8" was a hypothetical *shallow* row;
no such row exists — that estimate is now superseded in `19` §6.

**The target the pricing actually implies:** a base in r = 6 or r = 7, at the
column's own slack, available at the bottom, pays 0.58–0.59 — three times the
gap to the leader. That is where a new block is worth building, and it is a
different block from the 45° seam block, because r = 6 and r = 7 rows are
already beating with their own atoms.

One caveat, stated because the number looks large: the *optimistic* column is
the Karakuş floor, a proved lower bound on the side, not a forecast. It is there
to separate "would it matter" from "can it work", and the answer to the first is
yes, emphatically, for the open columns.

## 7. The two controls from the review's table

**The stronger prune (Karakış 2026, `arXiv:2609.37410`, Cor. 1.2).**
`s(N) ≥ 1/2 + √(N − ⌊√N⌋ + 1/4)` for every nonsquare `N ≥ 8`. It is strictly
stronger than the area bound at every nonsquare and it is *exact* at
`N = k² − 1`, where it gives `k`. It is now a prune in `motif_wheels.judge` that
fires **before** the gate (a declaration below it is a builder error, not a
loss), and again after the gate as an invariant on the verifier. The selftest
exercises it in the only window where it binds: `s(10) ≥ 3.192582` above the
area floor 3.162278, so a declared 3.18 is refused as `below_karakus_bound`.

**The negative control.** `s(k²−1) = k` is a theorem. All **29** rows
`n = k² − 1` in the delivered table sit at exactly `L = k` (0 beats). The control
is clean, so a claimed beat there would indict the builder, the verifier or the
scorer — and none occurs.

**The positive control.** Arslanov–Mustafin–Shangitbayev's `s(k²−k) < k`
(k ≥ 12) is residue `r = k − 1`. Our table beats the grid on **20 of 20**
members, k = 12…31 (n = 132 … 930), with slack 0.015–0.083. The table already
expresses that published family — which is a stronger acceptance test for a
*builder* than for the wheel, since these rows come from the delivered table.

## 8. Bui's staircase: what it is here, and why it is not the cheap next move

From `arXiv:2508.04603v2` §3.1.1–3.1.2, verbatim: rows are horizontal stacks of
`m` unit squares rotated by `θ`, consecutive rows offset by
`(Δ₂, −Δ₃) = (sec(θ+σ₁) sin σ₁, sec(θ+σ₁) cos σ₁)`, and the ceiling — the first
row in column `j` that can be replaced by an upright stack — is

    i_j = ⌈(j−1)(1 − Δ₁)/Δ₂⌉ + 1,      Δ₁ = cos θ.

At `θ = π/4` (the only tilt in our alphabet that is exactly representable) this
is `1 − Δ₁ = 1 − √2/2` and the delivered staircase is exactly the case
`Δ₂ = 1 − Δ₁`, i.e. `i_j = j`: **one square removed per column, per side.** The
delivered atoms are the 45° member of Bui's family, at its steepest admissible
staircase. §5 measured what every other member costs: the turn that makes
`Δ₂ ≠ 1 − Δ₁` costs `3√2/2 − 1` or fails outright.

The paper's own regime is `θ ∈ Θ(x^{-1/2})`: at `x ≈ 25` that is θ ≈ 0.20 rad,
not in ℚ(√2), so an instance cannot be certified by the exact gate at all. Its
accounted waste is `O((m+i_m)θ) ≈ 10` area units for a 25-column tile, plus
§5's top/bottom `O(x^{3/4} + x^{1/2}) ≈ 16`, against the delivered atom's
`L² − n = 25.3`. **Same order** — the asymptotic exponent only bites at `x ≫ 10³`.
So the finite primitive is not a cheap win at our sizes and cannot be certified
exactly; testing it properly needs §4's trapezoid nesting and §5's square
reduction, which is a different piece of work, not another spin of this wheel.
This is an arithmetic judgement from the paper's own bounds, not a measurement.

## 9. What this does not show

* The LP is float and the certificate is *feasibility*, not optimality. "The
  delivered side is optimal" means optimal **for the declared per-pair separation
  modes** — the block may not overlap its fill another way.
* The declaration covers full `p × p` blocks only. Eleven of the 30 r = 1 rows
  are partial diamonds and refuse; they are not priced here.
* The variants are transforms of one declaration. The instrument does not search
  over declarations, so "no gain" is a statement about these four knobs.
* The optimistic column in §6 is a proved lower bound on the side, never a
  construction. Nothing here produces a packing; it prices four of them.
* Bui's construction is analysed, not implemented (§8).

## 10. Files

* `scripts/seam_wheels.py` — the instrument: `Q2` exact field, `exact_gate`,
  `describe`/`build`, `lp_seam`, `certify`, the four variants, `bound_karakus`,
  `cascade_rank`, `baseless_rank`; `--selftest` 20/20.
* `scripts/motif_wheels.py` — `M-diamond` registered as a **reconstruction**
  wheel (`Cell.expect_L`, status `reconstructs`), the Karakuş prune, the
  `layout_not_enumerated` path; `--selftest` 13/13.
* `workspace/push/seam_wheels.json` — 88 cells, 14 certified rows, the cascade
  and base-less rankings, the control counts, the per-cell outcome labels.
* answers the run-53 review of `20-R1-ATOMS.md`; supersedes the pricing in
  `19-COLLECTION-AND-REVIEW.md` §4.3 / §6 G-2 — and its own §6 pricing is in turn
  superseded in run 54, see §11.

## 11. Run-54 addendum (details in `22-DIAMOND-MASK.md`)

The `p × p` extent of §2 is not the right parameter. With the tilted part as an
integer **mask**, three of the rows §3 refused reconstruct exactly — n = 325, 530,
577 are 19×5, 26×5 and 29×5 diagonal strips — and the fourth, n = 290, is not a
partial diamond at all: 25 of its 50 tilted squares lie on a second 45° lattice
offset by 0.384808 = 0.2721·√2. So the r = 1 tilted part is a **five-deep strip**,
which a square extent can never express.

Three of this document's statements need correcting:

* §5's tally word `exactly_infeasible` is now `candidate_rejected_exact`. A
  snapped candidate that fails the gate is not a proof that the layout is
  impossible, and the eight half-step neighbours are now tried before rejecting.
* §6's pricing — 0.153449 (r = 1), 0.589705 (r = 6), 0.584422 (r = 7), 0.425392
  (r = 8) and 0.022703 (r = 38) — is **withdrawn**. It replayed a column-wide
  slack backwards to rows its source base cannot reach, and the base-less number
  priced a single start. Re-priced per legal start and forward only, `now` is
  0.000000 for every column (delivered slack decreases with k, so re-placing a
  base higher up always costs) and the best base-less start is 0.058535. The
  qualitative conclusion is unchanged and sharper; the numbers are in `22` §6.
* §8's claim that a Bui seam near θ ≈ 0.2 rad "is not in ℚ(√2), so it cannot be
  certified exactly" is **wrong**. For rational t = tan(θ/2), cos θ and sin θ are
  rational, hence in ℚ ⊂ ℚ(√2): those orientations are exactly representable and
  the exact gate can certify them. §8's area argument stands; its field argument
  does not. See `22` §7.
