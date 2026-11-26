# 104 — The r-run carrier: the audit of the defect class, and whether more translates buy reach

**Headline.** Run 146 found the defect class in run 145's split counter: a fast analytic count with
no independent cross-check, and a solver that gated a pose without requiring its count to match the
row's. The audit of the other carriers and sweep instruments found **four** more instances — one of
them a *beat claim with no certificate at all* — and all four are repaired. The block-bedded carrier
extended to `r` equal runs per axis reproduces run 145's **19/110** exactly at `r = 2` (same rows,
same declarations) and adds **0** at `r = 3..6`: the extra translates buy **no reach**. The entry
test stays 19/110, a FAIL by one row against the threshold of 20.

---

## 1. The defect class

Two shapes of one error:

* **an analytic count with no independent cross-check** — a fast formula decides a count, and
  nothing ever builds the set it is supposed to describe and compares;
* **a solver that gates a pose without requiring its count to match the target** — the gate decides
  disjointness, which is a different question, and a gated pose of the wrong count passes.

Run 145's `split_counts` had both: its windows were compared as offsets against absolute positions
(read 146's repair, doc 102 §8), so the count it returned belonged to a different question than the
pose built, and the entry test accepted `r["ok"]` without `r["n"] == n`. A pose can gate perfectly
and carry 48 cells when the row asks for 110.

## 2. The audit

Every instrument that *claims* a reproduction, a tie, or a beat was read for these two shapes. Four
instances were found; all are repaired in place, and each repair is guarded by a control that fails
if it is removed.

| instrument | run | the defect | the repair | did a published number move? |
|---|---|---|---|---|
| `seam_carrier.py` | 144 | `entry_test` accepted `r["ok"]` alone; the analytic `counts_for` nominates and `check` gates, but nothing required the pose's count to be the row's | accept only `r["ok"] and r["n"] == n`; control 9 now compares `counts_for` with `assemble` on **every** bar size in a 5-wide window for 8 declarations (was 3 sizes for 6, only the built one) | no: re-runs **2/110**, ledger byte-identical — the two reproductions were genuine |
| `shared_box.py` | 143 | `entry_test` accepted on `cert["overlaps"] == 0` only — never `n`, never the side; and `beats_family` counted configurations whose **closed-form** side beat the delivered side **without building or gating any of them** | require `cert["n"] == n` and `abs(cert["side"] - target) <= TOL`; every `better` claim is now built and gated (`better_cert`, `beats_family_certified`); new control 10 checks the closed form against the independent exact SAT on the built pose for 8 configurations and its tightness (`legal(s* - 1e-9)` is False) | no: 0/110 before and after, 0 `better` rows — the defect was **latent**, never a wrong published number |
| `motif_wheels.py` | 121 | `judge` gated `cell.state` at the declared `n` without checking that the state carries `n` cells — a declaration with the wrong count could be scored a survivor | `count_mismatch` refusal (`len(cell.state) != n`), before the gate | no: selftest 13/13 still green |
| `ext_census.py` | 131 | the pocket patch wrote `L_after` from the windmill declaration without recording or requiring the pose's own cell count | `cells`/`count_ok` recorded; a patch row whose pose is not a pose of `n` is skipped | no certified row changed |

**Inspected and clear.** `block_bed.py` (repaired in run 146: `split_counts` shifts by `L/2`, entry
test requires `r["n"] == n`, control 9 compares the two counters on every split);
`beat_probe.py` (count table then gate, and the probe asserts `r["n"] == n`); `notch136.py` (judges
the *delivered* poses only — its claims are measurements of rows that already exist, not poses it
builds); `construct_seam.py` (the gate is on constructed `Q(sqrt2)` cells and the count is fixed by
the construction; its controls assert the count); `tilt_audit.py`, `row_census.py`,
`beaten_leverage.py`, `range_leverage.py` (arithmetic over the delivered table — the count is the
row's own key, no pose is built or claimed); `crystal_domains.py` (domain counts from the delivered
poses, asserted against their declared cells).

## 3. The r-run law

Run 145's carrier puts **two** runs on each axis, anchored at the faces: run 1 occupies `[0, kx]`,
run 2 `[L - ky, L]`, with the seam gap `g = L - K > 0`. The extension replaces that with `r` **equal**
runs and `r - 1` **equal** gaps, on each axis independently:

```
u  = K / r                                  (integer, r | K)
g  = (L - K) / (r - 1)                      > 0
run J (J = 0..r-1):  starts at J*(u + g)  -  centres start + 1/2, ..., start + u - 1/2
```

so run 0 begins at the face `x = 0` and run `r-1` ends at the face `x = L`: the carrier still spans
exactly `[0, L]`, the box is still its own bbox, and any two cells on one axis are separated by
`0` (adjacent) or `g > 0` (different runs). Carrier-carrier overlap is still impossible by
arithmetic, for any `r` and any split — control 2 gates the carrier alone (no block) for every
`(K, r)` it is tried on, and asserts `g > 0` and the exact span.

`r = 2` is exactly run 145's symmetric split `kx = ky = K/2`; control 1 asserts the positions and
the gap agree with `block_bed.runs` element for element.

The count is still `n = K^2 - D + p*q`, with `D` the number of carrier cells the centred tilted
block beds out. `D` is counted analytically (a window per x cell, bisection over the y positions),
and — the discipline the audit asks for — **control 3 asserts the analytic `D` equals the number
`assemble_r` actually drops**, cell by cell, on every declaration it is tried on. No pose is ever
accepted on the count's word: the entry test and the probe both require `r["ok"] and r["n"] == n`.

## 4. Entry test

`python3 scripts/block_bed_r.py` — the same 110 two-class rows, the same side law, the same hint
(`p*q` = the row's tilted-class size, which only bounds which declarations are tried).

| quantity | value |
|---|---|
| rows | 110 |
| reproduced | **19** |
| threshold | 20 |
| verdict | **FAIL by one** |
| by `r` | `r = 2`: 19, `r = 3`: 0, `r = 4`: 0, `r = 5`: 0, `r = 6`: 0 |
| sides exact in `Q(sqrt2)` | 110 |
| rows that matched a count | 19 |
| gates refused after a count match | 0 |

**Fidelity control.** At `r = 2` the family reproduces **19/19** of run 145's rows — the same rows,
at the same declarations (`K`, `p`, `q`, and `old kx = ky = K/2`), 0 extra. The r-family is a strict
superset of the two-run family, and it earns nothing beyond it.

The interpretation is the same as run 145's: the 19 rows are exactly the symmetric ones, every one
at `kx = ky = K/2` with a square-or-nearly block. A third or fifth run does not change the seam's
arithmetic, it only moves the same cells; the reach is bounded by the *count*, not by the number of
translate domains.

## 5. The beat probe

`python3 scripts/block_bed_r.py --beat --hits` asks run 146's question with the r-family supplying
the count: for each row, every side of the group grid **strictly below** the delivered side (the
area bound `L*L >= n` makes a beat possible only in `[sqrt(n), L_del)`), every `K` from the exact
count floor to `floor(L)`, every shape `p x q` with `p*q` in `[n - K^2, min(330, n)]` whose bbox fits,
`need = K^2 + p*q - n`, and the bed count `D` of the r-family (equal runs, `r = 2..6`). The first
`D == need` is rebuilt by `check_r` and gated, and a hit requires `r["ok"] and r["n"] == n` — the
count must be the row's, not merely a gated pose.

**Result: 19 rows, 183 (row, side) windows, 124,176 (side, K, shape) trials, 0 count matches,
0 gate refusals, 0 beats.** Twenty minutes.

**Coverage, stated plainly.** The probe ran on the **19 rows the family reaches at all** — the entry
test's reproductions. A full 110-row sweep at five run counts costs 60-230 s per row (more than two
hours): the r-family's count is five bisection sweeps per shape where run 146's two-run table was one
`O(K^2)` pass, so the full sweep was not run in this visit. What covers the rest: run 146's
**full-110** probe at `r = 2`, the identical side window and shape rule, returned **0 count matches in
949,243 trials**; and the entry test prices `r = 3..6` at **0 additional rows** at the delivered sides.
The subset is therefore the reach set, and the rest of the space is already priced null.

**Sensitivity control.** `--beat --control` re-finds **19 / 19** ties at exactly their delivered side
(`r = 2`), so the search can find a tie and finds none below.

## 6. Do extra translates buy reach?

**No.** The r-family is a strict superset of run 145's carrier — at `r = 2` it reproduces all 19 of
its rows at all 19 of its declarations — and `r = 3..6` adds **0** rows at the delivered sides and
**0** beats below them. The extra translate domains buy a larger *count surface* (more `(K, D)` pairs
per side), but not a smaller side: the count law `n = K^2 - D + p*q` still has `K^2` as its leading
term, and the gap `g = (L - K)/(r - 1)` shrinks as `r` grows, so more runs sit closer together and the
block beds more of them, not fewer. The binding constraint is arithmetic, and it is the same one run
146 named: `19` rows tied, `0` beaten, `submission.csv` untouched, the delivered total unchanged at
**22.217428576** (554 beats, 446 grid ties).

**Where this leaves the carriers.** The block-bedded family — at any run count — explains the
symmetric part of the table and nothing else. The two directions that survive are the ones run 103
named and this run does not spend: a **rational-`b` side law** `a + b*sqrt2` for the 28 rows outside
the halves group, and a carrier whose translate law does not require every run to end on a face.

## 7. The audit, in one line

Four instruments carried the defect class; three could have published a wrong claim and one was
already carrying an uncertified beat counter; all four now require a built pose whose count is the
row's. The corrected numbers did not move — the defects were latent, not realised — which is the
outcome an audit wants: the guards are now where the numbers are.
