# Snapshot reconciliation

## Canonical state

The latest state represented by the surviving run records is **Run 36**,
dated 2026-11-07. Run 36 re-established the successful Run 35 score move
after a sandbox rollback and reproduced it from the surviving records.
The canonical reported values are:

- score: **22.642386651** (rounded: **22.642387**);
- rows beating the grid: **543/1000**;
- reported leaderboard gap: **0.587965**;
- direct gain from nine register records: **0.003359**;
- additional n=338 chain gain: **0.000245**;
- total Run 35/36 improvement: **0.003604**.

## Historical milestones

| Snapshot | Score | Meaning |
|---|---:|---|
| Run 15 | 22.823536 | Earlier frontier after the atlas import and chain conversions; 454 rows beat grid. |
| Run 32 | 22.645991 | Recovery/documentation state after the Mishapolk import; 543 rows beat grid. |
| Run 34 | 22.645991 | Accuracy-dive/system-map milestone preserved in the GitHub lineage. |
| Run 35 | 22.642386651 | Latest score move: nine register records plus the n=338 chain conversion. |
| Run 36 | 22.642386651 | Re-establishment of Run 35 from surviving records; canonical latest state. |

Run 15, Run 32, and Run 34 values remain in the detailed history because
they document real intermediate states. They should not be presented as the
current score in README or STATUS front matter.

## Reconciliation policy

1. README and STATUS current-result blocks use Run 36.
2. NEXT_STEPS identifies Run 36 as the current planning baseline.
3. REPRODUCE labels the retained Run 15 command block as historical.
4. The full GitHub repository lineage is preserved; this update does not
   replace the richer live checkout with the flattened attachment.
