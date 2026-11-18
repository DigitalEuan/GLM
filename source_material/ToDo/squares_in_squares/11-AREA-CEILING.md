# 11 — Where the remaining score can be (area ceiling, rebuilt)

Instrument **`scripts/leech_audit_fix.py`** (the only scorer of this quantity since
`scripts/area_ceiling.py` was folded into it and deleted); ledger
`workspace/push/leech_audit_fix.json`. Its section 3 prints exactly the numbers
below: base-less 0.806788 over 177 rows, open columns 6.388578 over 270 rows,
total grid ceiling 7.195366, beating-row headroom 15.022691.

## 0. This document was wrong and has been rebuilt

The first version scored a row as `10/L`. The repository's score
(`build_table.py`, `cascade2.py`, `packlib`) is

```
score(n) = L_n / sqrt(n) - 1        lower is better, floor 0
grid(n)  = ceil(sqrt(n)) / sqrt(n) - 1
gain     = (ceil(sqrt(n)) - L_n) / sqrt(n)
```

so the first version reported a "score" of 593.279 for a table that scores
**22.218056945**. It also computed `L` as
`max(x) + max(ex) - (min(x) - min(ex))`, which inflates the box by up to two
half-extents; the correct extent is per square. Rebuilt on both corrections the
instrument reproduces the delivered table to **1.3e-10** and **553 beats**, and
cross-checks 20 rows against `packlib.verify` exactly. Every figure below is from
that run.

## 1. The bound

A row is beaten only with `sqrt(n) <= L_n < ceil(sqrt(n))`, so the largest
possible gain at a row is

```
gain <= (ceil(sqrt(n)) - sqrt(n)) / sqrt(n)
```

attained only by a zero-waste packing, which is impossible for non-square `n`.
Since the score's floor is 0, the total remaining room is the score itself —
**22.218057** — of which the unattainable part is most of it. The useful
decomposition is grid rows versus beating rows:

| population | rows | ceiling if beaten with zero waste |
| --- | ---: | ---: |
| grid rows, total | 447 | 7.195366 |
| beating rows, headroom to zero waste | 553 | 15.022691 |

## 2. The unopened columns are not where the score is

| population | rows | ceiling | per row |
| --- | ---: | ---: | ---: |
| base-less residue columns | 177 | 0.806788 | 0.004558 |
| columns that already beat | 270 | 6.388578 | 0.023661 |

Opening every unopened column perfectly would win **0.8068** — 11% of the
grid-row ceiling — at **0.2× worse per row** than
tightening what is already open. **PL-21 stays deprioritised**, now on the right
number.

**Retraction of PL-30.** The corrected target gives **37 residue columns
with a beating row and 24 without** — matching the record's original "37 of 60",
not the "39 base-less" I reported last round. That figure came from the broken
`L`: inflating the box turned 253 beating rows into grid rows and emptied six
columns that are in fact open. PL-30 is withdrawn; `09-CASCADE.md` §5's
population was right.

## 3. The exchange rate — this is the actionable number

A column's slack is set by its base and inherited by every row (09-CASCADE §2), so
`dscore/dslack = sum 1/sqrt(n)` over the column's rows.

| | |
| --- | ---: |
| marginal rate over the open columns | **52.3830 score per unit slack** |
| per 0.01 of slack | **0.5238** |

Best columns:

| r | rows | beating | per unit slack | per 0.01 |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 31 | 0 | 4.0272 | 0.0403 |
| 1 | 31 | 30 | 3.6453 | 0.0365 |
| 2 | 31 | 29 | 3.4437 | 0.0344 |
| 3 | 30 | 28 | 2.8060 | 0.0281 |
| 4 | 30 | 27 | 2.7538 | 0.0275 |
| 5 | 29 | 26 | 2.3745 | 0.0237 |
| 6 | 29 | 25 | 2.3505 | 0.0235 |
| 7 | 28 | 24 | 2.0779 | 0.0208 |

## 4. What to do

Tightening slack by 0.01 across the open columns is worth **0.5238** —
0.65× everything the unopened columns could ever give, for a construction change
of 0.01 rather than a new column. Slack of 0.05 is worth **2.6192**, more than
four times the entire unopened ceiling.

So the score lives in **slack**, in columns already open, and the target is the
column with the most rows at small `k`: `r = 1` (31 rows, 30 beating,
3.6453 per unit). That is PL-32.

## 5. What the two errors cost

* The `10/L` scale made every total in the first version wrong by a factor of ~27
  and made "headroom 24.7" look like a budget when the score's own floor makes
  that meaningless.
* The inflated box mislabelled 253 of 553 beating rows as grid, which is what
  produced PL-30's phantom 39 columns and the 0.081-bit "genuine" information in
  part 8.
