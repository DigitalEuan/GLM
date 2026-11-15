# Run 30 notes (2026-11-06)

Run documentation under the distinct name. The same content is in README.md (Run 30 section), RUN_NOTES.md, and download/run30/README.md.
# Run 30 (2026-11-06): P2 closed for good; the Mishapolk import (largest since run 22)

## (a) P2 — the T-263 renewal returned an honest null

The one bounded re-run the SAT review asked for (NEXT_STEPS run 28
renewed P2 for the 41-floater family). 12/12 cells (n = 299/334/371,
ladder 0.002/0.005/0.01 below row L; settle -> anneal -> re-harden
hops; finalize gate): **0 finds, 0 hard hops**; soft extents pinned
0.4-2.5e-3 above L_t in every cell. The floaters at Maxwell ratio 0.68
do not settle deeper by contact-graph re-breaking - the record's depth
is not floaters waiting to close. P2 is closed for good; the run-29
falsifiable prediction (phi down on any improvement) stands untested:
there was no improvement to measure.

## (b) P3 — Mishapolk: the band 325..1000 was never empty upstream

The weekly atlas check was unchanged, but the Karimi lead (issue #799,
read via browser) pointed past our sources.
**Mishapolk/square-packing-records** `upper_bounds.json` carries
verified bounds at ALL 1000 n - the 676 rows in 325..1000 were
invisible to our atlas (squaremath.org covers 1..324 only).

Imported 221 rows in two invocations (exact certificates, center-basis
t = tan(theta/2)): 25 after a verify-tolerance fix (exact tangency in
an open container rounds to +2e-15 float noise), 196 after a dry-run
ledger bug fix (applied rows from a dry run must never feed the resume
ledger). Score **22.819977568 -> 22.645990613** (-0.173983); beats-grid
454 -> 543. The standing channel absorbed it (cascade 9, closure 3,
assembly round-trip 0 issues); root_audit refreshed: fixpoint true,
305 open rows, aggregate 0.375304; the best aim moved to c=32 n=356
(0.011102, 14 conversions).

## (c) Karimi read

Two-strip packings (L-shape with tilted wall strips, Ryu Thm 1.3
lineage) live at n >= 1184 - outside our range. The **window
theorem** matters to us: for every integer K >= 16, s(n) < K whenever
n <= K^2 - 8*sqrt(K) - 19 (exponent 3/5 -> 1/2 over Bui/McClenagan) -
the certificate shape for our mid-band rows.

## NEXT_STEPS.md updated to the Run-30 state

P2 closed for good; P3 adds Mishapolk to the weekly loop; aiming map
refreshed (top aims 356/395/355, every one at grid today); value
ladder recomputed (gap 0.591569; d* 0.0365; ceiling 5.005). Copies:
NEXT_STEPS.md and download/NEXT_STEPS.md.
