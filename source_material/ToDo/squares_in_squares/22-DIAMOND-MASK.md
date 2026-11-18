# 22 — G-2b: the diamond as a mask (run 54)

Instrument `scripts/diamond_mask.py` (selftest 10/10), ledger
`workspace/push/diamond_mask.json`. Read-only: no row changed, no score claimed.

Answers the run-54 review of `21`. The short version: the block's extent was
never the right parameter. Once the tilted part is a **mask**, three of the four
rows the full-block declaration refused in `21` reconstruct exactly, the fourth
turns out to be two lattices and not one block at all, and the geometry that
falls out — the r = 1 tilted part is a **five-deep diagonal strip** — is the
fact the square `p × p` declaration was hiding.

## 1. The representation: frame, mask, fill, separately

| part | what it is | how it is recovered |
| --- | --- | --- |
| frame | `kappa = L/2 + kappa0`, `kappa0` in ℚ(√2) | from **one site**, never from the centroid |
| mask | a set of integer sites `(u, v)` | from **differences** of tilted centres |
| fill | upright squares, near/far/centre anchored | the wall-anchor codes of `21` §2 |

Recovery uses the inverse 45° transform

    x + y = kx + ky + √2·u          x − y = kx − ky − √2·v

so after subtracting the smallest `(x+y)` and the largest `(x−y)` both
coordinates are integers with no fitting at all. **The centroid is never used**:
removing sites moves the centroid while the lattice stays exactly where it is,
and the selftest checks that a block with a corner removed keeps the same
`kappa0` bit for bit.

Verification is a **one-to-one match of centres *and* orientations**, not a
comparison of position sets: both sides are sorted on the exact coordinate and
compared componentwise, and the orientation sequence must agree. That caught a
real bug in my first version, which rounded to 6 dp and turned the finalizer's
1e-9 pad into a spurious 1e-6 mismatch on n = 530.

## 2. The side is solved, not guessed

`min_side(atom, t)` bisects on `L` with the block pinned at a declared
translation `t`. Positions are linear in `L`, every comparison in `exact_gate` is
in ℚ(√2), so the bisection is over an ordered field: the return is a bracket
`(lo, hi)` where `lo` is **exactly infeasible** and `hi` is **exactly feasible**.
That is a two-sided certificate for the declaration, and it is strictly stronger
than the LP of `21` because the exact gate checks **all** separating axes of every
pair, so no declared-axis branch can hide an alternative.

Floats only nominate the bracket. Nothing is rounded except `hi`, which is then
nudged upward until it passes exactly; a failure is `candidate_rejected_exact`,
never `layout_infeasible` — that word now means a checked certificate and is used
only when no side packs the declaration at all.

Translations are a declared finite set, `{(0,0), (±1/2, 0)}`: the
half-integer frame the delivered atoms use. This deliberately does **not** search
continuous translations, and §7 says so.

## 3. Reconstruction: a partial row and a full control

Every row below certifies at the delivered side, exactly, with worst penetration
0. The reported `L` is the delivered `L` minus the finalizer's pad (1.9e-9).

| n | k | frame `p` | tilted sites | upright | occupancy | mask shape | certified `L` |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 226 | 15 | 5 | 25 | 201 | 1.000 | 5 × 5 full | 15.535533906 |
| 325 | 18 | 19 | 95 | 230 | 0.263 | 19 × 5 band | 18.535533906 |
| 530 | 23 | 26 | 130 | 400 | 0.192 | 26 × 5 band | 23.535533906 |
| 577 | 24 | 29 | 145 | 432 | 0.172 | 29 × 5 band | 24.535533906 |

So the acceptance test the review asked for passes on both sides: the full
control reproduces, and so do the partial rows — with the shapes named.

**n = 290 is not a partial diamond: it is two diamonds.** 25 of its 50 tilted
squares sit on a second 45° lattice whose frame is offset by **0.384808 =
0.2721·√2** in `x − y` from the first. A single frame plus a mask cannot hold
two lattices, and the refusal now says exactly that instead of "no layout
enumerated". Extending to two frames is a real piece of work, and this run does
not do it.

## 4. The geometry the mask reveals

The r = 1 tilted part is a **strip five diagonal rows deep**, not a block: the
mask is 19×5 at n = 325, 26×5 at 530, 29×5 at 577, and only at n = 226 (and the
full-block rows of `21`) is it 5×5. That is why the square declaration had to
refuse them — a `p × p` mask cannot be a five-deep strip — and it is the first
statement in this study about *which* lattice sites the construction occupies
rather than how many.

The strip grows in one direction only (`u`), so the tilted part adds one
diagonal row per step while the fill supplies the rest. Any grammar that treats
the block as an extent cannot express this; the mask does, for free.

## 5. Count-preserving boundary edits

At fixed `n`, each move exchanges tilted sites for upright squares (or moves one
site), then the exact bisection prices it. Costs are exact side minus delivered:

| n | boundary run +1 | boundary run +2 | move row end | trim outer u-row |
| ---: | ---: | ---: | ---: | --- |
| 226 | +0.914214 | +0.914214 | +0.914214 | rejected exactly |
| 325 | +0.813708 | +0.813708 | +0.849242 | rejected exactly |
| 530 | +0.763456 | +0.763456 | +0.798990 | rejected exactly |
| 577 | +0.884776 | +0.884776 | +0.914214 | rejected exactly |

Two readings. First, **no count-preserving boundary edit gains** anywhere: every
feasible one costs between 0.76 and 0.92 of side, an order of magnitude more than
the 0.0147 step being chased. Second, the run length does not matter (k = 1 and
k = 2 give the same side) because the binding constraint is the *band width*, not
the number of squares in it — the strip is already as deep as the fill allows.

`trim outer u-row` is the interesting negative: removing five outer sites and
adding five upright squares needs about 4.5 more side. It is rejected by the
exact gate at every nominated side, which is what `candidate_rejected_exact` is
for — it says the declaration does not pack at the sides the float search
proposed, not that the layout is impossible.

## 6. Re-ranked: the corrected cascade, and three of my own numbers withdrawn

The review was right on all three counts, and each correction **lowers** the
published numbers.

**(a) `lp_seam` pinned-L bug.** The LP zeroed the coefficient of `L` when `L` was
pinned *and* fixed its bound, so every row was evaluated at `L = 0`. Fixed: the
coefficient stays 1 and pinning happens only in the bounds. The pinned column of
`21` §4 was vacuous rather than wrong (the point was feasible anyway); the free
variants of `21` §5 were unaffected.

**(b) `candidate_rejected_exact`.** A snapped candidate that fails the gate — and
now also its eight half-step neighbours — is a rejected *candidate*, not a proved
infeasibility. The word `exactly_infeasible` is gone; `layout_infeasible` is
reserved for a checked certificate.

**(c) The ranks, priced per legal start, forward only.** This is the correction
that matters. `cascade_rank` used to take the column-wide minimum slack and apply
it at the bottom row, i.e. replay a base **backwards** to rows its source cannot
reach. `cascade_rank` also never checked that `n = k² + r` has residue `r`, so
r = 6 was getting n = 10 (a residue-1 row) as its base. Both fixed; every start
is priced with its own slack and only rows `k ≥ k0` count.

With the columns' own delivered slacks:

    now = 0.000000 for EVERY column

That is not a bug, it is the finding: the delivered slack **decreases** with `k`
in every column (r = 1 runs 0.5355 at k = 8 down to 0.5208 at k = 31), so
re-placing an existing base higher up always costs side. No column can be
improved by moving its own base; the whole 0.1637 gap needs a *better* base.

The per-start optimistic column (Karakus floor at the start, forward only) is the
upper bound on what a new base at that start would pay:

| column | best start | n | floor | upper bound |
| --- | ---: | ---: | ---: | ---: |
| r = 1 | k = 3 | 10 | 0.1926 | **0.971058** |
| r = 2 | k = 4 | 18 | 0.2749 | 0.763005 |
| r = 3 | k = 6 | 39 | 0.2663 | 0.640436 |
| r = 4 | k = 7 | 53 | 0.3007 | 0.567224 |
| r = 5 | k = 8 | 69 | 0.3262 | 0.514936 |
| r = 6 | k = 8 | 70 | 0.3899 | 0.473293 |
| r = 7 | k = 9 | 88 | 0.4022 | 0.435213 |
| r = 8 | k = 10 | 108 | 0.4121 | 0.400866 |

The base-less window, with **every** start priced:

| residue | best start | n | floor | upside |
| --- | ---: | ---: | ---: | ---: |
| r = 38 | k = 24 | 614 | 0.7951 | **0.058535** |
| r = 39 | k = 25 | 664 | 0.7834 | 0.053093 |
| r = 40 | k = 25 | 665 | 0.8032 | 0.041996 |
| r = 41 | k = 25 | 666 | 0.8229 | 0.037758 |
| … all 38–60 | | | | 0.414036 total |

**Withdrawn from `21`:** 0.153449 (r = 1), 0.589705 (r = 6), 0.584422 (r = 7),
0.425392 (r = 8) and 0.022703 (r = 38) were artefacts of replaying slack
backwards and/or pricing a single start. The honest numbers are `now = 0` for
every column and 0.058535 for the best base-less start. The qualitative
conclusion survives and sharpens: **the deep base-less columns are not where the
score is** (0.059 against a 0.1637 gap), and the largest single upper bound is at
the *shallow* end of the r = 1 column, at n = 10.

The caveat stands: the optimistic column is a proved lower bound on the side, so
it bounds a construction, not a forecast. And the ranking's top start (n = 10) is
a 10-square row with 2 tilted squares — there is no strip there for this grammar
to edit, which is why §5's edits were run on the r = 1 rows that *do* have one.

**(d) A scored gain uses the finalized score.** `certify` now reports
`SQ.row_gain(n, SQ.extent(fp_st)) − SQ.row_gain(n, L_del)` from the packlib
replay, not the unpadded exact side. No gain occurred, so this changed no number
here; it would have changed any claimed one.

## 7. The correction about smaller angles

`21` §8 said a Bui seam at θ ≈ 0.20 rad "is not in ℚ(√2), so it cannot be
certified exactly". **That was wrong**, and the review is right. With rational
`t = tan(θ/2)`,

    cos θ = (1 − t²)/(1 + t²)        sin θ = 2t/(1 + t²)

both are **rational**, hence in ℚ ⊂ ℚ(√2). Every such orientation is exactly
representable and the exact gate can certify such a packing directly — no field
extension, no tolerance. So the question about a staircase seam near θ ≈ 0.2 is
purely whether it saves space at our sizes, not whether it can be represented.
What remains true from §8 is the arithmetic: Bui's accounted waste at x ≈ 25 is
`(m+i_m)θ ≈ 10` plus `O(x^{3/4}+x^{1/2}) ≈ 16`, the same order as the atom's 25.3,
so a win at these sizes is not indicated — but that is now a claim about area,
not about the field, and it is testable rather than blocked.

## 8. What this does not show

* **One frame only.** n = 290 needs two, with a known 0.384808 offset. Not done.
* **The block is pinned.** The side is exact for the declaration with the block
  in a declared translation; continuous translation is not searched.
* **Four moves.** trim / boundary run / move row end, at four rows of the r = 1
  column. `base_and_edits` dedupes by D4 symmetry of the index grid, so mirrored
  and rotated copies do not consume runs — but the grammar is not a search.
* **No score moved.** 0 survivors everywhere; `submission.csv` untouched.
* The `now = 0` result is a statement about *delivered* bases. It does not bound
  what a different construction at the same residue could pay — that is the
  optimistic column, which is a bound.

## 9. Files

* `scripts/diamond_mask.py` — `MaskAtom`, `lattice_coords` (differences only),
  `describe_mask`, `verify` (oriented 1-to-1), `min_side`/`certify_side` (exact
  bracket), `edit_trim_row`/`edit_boundary_run`/`edit_move_end`, `canonical`
  (D4), `evaluate`; `--selftest` 10/10.
* `scripts/seam_wheels.py` — `lp_seam` L-coefficient fix,
  `candidate_rejected_exact` with the eight-neighbour retry, finalized-score
  gains, `cascade_rank`/`baseless_rank` re-priced per start and residue-checked;
  selftest 20/20.
* `workspace/push/diamond_mask.json` — 20 cells: 4 reconstructions, 4 × 4 edits,
  the refused row and the two-frame diagnostic.
* supersedes the pricing in `21` §6 and corrects `21` §8.
