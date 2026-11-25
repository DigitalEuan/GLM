# Snapshot reconciliation

## Canonical state

The latest state represented by the surviving run records is **Run 52**,
dated 2026-11-18, which re-scores and guards the run-47 table. The canonical
reported values are:

- score: **22.217428576** (rounded: **22.217429**);
- rows beating the grid: **553/1000**;
- reported leaderboard gap: **0.163635**.

## Historical milestones

| Snapshot | Score | Meaning |
|---|---:|---|
| Run 15 | 22.823536 | Earlier frontier after the atlas import and chain conversions; 454 rows beat grid. |
| Run 32 | 22.645991 | Recovery/documentation state after the Mishapolk import; 543 rows beat grid. |
| Run 34 | 22.645991 | Accuracy-dive/system-map milestone preserved in the GitHub lineage. |
| Run 35 | 22.642386651 | Run 35 score move: nine register records plus the n=338 chain conversion. |
| Run 36 | 22.642386651 | Re-establishment of Run 35 from surviving records. |
| Run 47 | 22.218056945 | Audit re-score of the same table; supersedes Run 36. Historical: superseded by the run-140 n = 90 promotion. |

Run 15, Run 32, Run 34, Run 35 and Run 36 values remain in the detailed history
because they document real intermediate states. They are not the current score
and must not be presented as such; `scripts/record_guard.py` enforces this.

## Reconciliation policy

1. README and STATUS current-result blocks use Run 36.
2. NEXT_STEPS identifies Run 36 as the current planning baseline.
3. REPRODUCE labels the retained Run 15 command block as historical.
4. The full GitHub repository lineage is preserved; this update does not
   replace the richer live checkout with the flattened attachment.
