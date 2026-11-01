# Audit of `hypothesis_engine_v13.py` (Round 42)

Produced by `v13_audit.py` (v13 run unmodified in quick mode, then the Round 42 guards). EMP unless a Lean name is given.

## What works

* It runs here: standard library only, no imports of earlier engines (about 20 s quick).
* Its TAX test is honest about the main question: the clustering and magnitude tests both come out negative, and it says so.
* It found by itself that every jump has TAX defect 0, which refutes its own earlier (v12) claim.

Status counts: {'law-holds': 3, 'open': 2, 'prediction-confirmed': 1, 'refuted-by-prediction': 1, 'refuted-heldout': 11, 'survives': 27}.

## Static checks of the source

| check | ok | finding |
|---|---|---|
| header promises an exact permutation test over C(N, k) placements | **no** | promised in the module docstring (step 4) but not implemented: the code compares the mean distance with its uniform expectation only, with no p-value |
| self-contained (standard library only) | yes | imports: __future__, collections, dataclasses, fractions, json, pathlib, sys, time, typing |
| 'NEW TO THE LEDGER' is printed only for surviving hypotheses | **no** | printed for every tool-generated key not in the ledger, whatever its status -- including refuted ones (H38 in the run below) |
| the doubling law is stated with both conjuncts | **no** | the TAX narrative says 'a jump occurs exactly when the (D-1) pattern is eventually white'; white(D-1) alone is refuted at D = 53208 (C388), the law needs odd parity of D-2 as well (ldiag_doubles, ldiag_keeps_of_even) |
| Y = 1/(pi + 2/pi) must be irrational for the reduction | **no** | not needed: the linear part Y*w cancels for every real Y because w(a XOR b) = w(a) + w(b) - 2 w(a AND b) always holds (tax_conserved_iff_defect_zero) |

## Guards on the run

| guard | survives | outcome |
|---|---|---|
| identity | **no** | v13 docstring 'conserved iff w(a AND b) in {0, w(a), w(b)}': the stated criterion is wrong -- 276 cases satisfy it but are false, 6 are true but fail it (of 819 checked). |
| identity | yes | closed form 'defect = -2(3c^2 - 2c(a+b) + ab)': the stated criterion agrees with the truth on all 819 cases checked. |
| explained-away | **no** | 'TAX is conserved at every period doubling' (v13 POSITIVE FINDING): EXPLAINED -- every event satisfies 'white(D-1)' (hypothesis of the doubling law ldiag_doubles), and the feature holds at all 4 domain points where 'white(D-1)' holds; proved in general: GLM.HypothesisEngine.Tax.tax_conserved_at_doubling. Not a new mechanism. |
| coincidence | yes | statistics alone: 4 of 4 events carry the feature (expected 0.077); exact P(X >= 4) = 1.33e-07, P(X <= 4) = 1. A statistics-only engine would call this significant; the explained-away guard shows it is forced by white(D-1). |
| exclusivity | **no** | 'TAX is CONSERVED only at the white diagonals' (v13 cross-domain lift): false -- 108 of the 116 feature points lie outside the claimed set (first: 6). |
| consistency | **no** | 2 sentence(s) assert a claim whose hypothesis was refuted (first: utterance 40, H38). |

## Where TAX is conserved (left diagonals, the engine's own profile)

* Pairs `(D-1, D)` with `2 <= D < 6000` that are TAX-conserved: **116**.
* With a white member: 8 (`D = 2, 3, 7, 8, 28, 29, 399, 400`).
* Equal patterns: 3 (`D = 6, 27, 398`).
* Neither: **105** (first: weights 3, 3 with overlap 1 at `D = 33`; weights 5, 8 with overlap 2 at `D = 403`).
* Lean: `tax_conserved_pairs_below_400` lists the 25 conserved pairs below 400 and `tax_conserved_not_only_white` certifies `D = 33` (CERT).

## Verdict

The TAX tool as defined (`TAX(w) = Y w + w^2/8`) does not see the period doublings: conservation is the integer condition `3c^2 - 2c(a+b) + ab = 0` on the weights, it holds trivially whenever one pattern is white (so at every doubling, which needs `white(D-1)`), and it also holds at many pairs with no white member. Three v13 sentences are wrong (criterion, 'NECESSARY', 'only at the white diagonals') and one 'finding' is a consequence of the doubling law's premise. The doubling law `white(D-1) and odd(D-2)` (proved: `ldiag_doubles`, `ldiag_keeps_of_even`) stays the explanation of the doublings.
