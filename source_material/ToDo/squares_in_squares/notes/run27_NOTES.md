# Run 27 notes (2026-11-06)

Run documentation under the distinct name.  The same content is in README.md (Run 27 section), RUN_NOTES.md, and download/run27/README.md.
# Run 27 (2026-11-06): P4 — the root-conversion instrument

User: continue this project - see NEXT_STEPS P4.

## The standing channel: fixpoint confirmed

cascade3 (0 chain improvements, 0 fails) -> closure_apply (fixpoint
after 0 rounds) -> final_assembly (round-trip 0 issues).  Score
unchanged 22.819977568; beats-grid 454.  The propagation loop has
nothing left to convert - as required, this is now verified by an
instrument rather than asserted.

## The instrument: scripts/root_audit.py

For every residue diagonal: the chain envelope (running rho = min
L-K over lower members), a fixpoint audit (rows above envelope =
unexploited conversions), and an aiming map - the measured value of
a T-263-class record (depth 0.0216) placed at each open row, with
its conversion list.  Ledger: workspace/push/root_audit27.json.
Cross-validated against an independent reimplementation; the totals
agree to 1e-6.

## Two documentation errors found and fixed

The run-26 NEXT_STEPS §2 eyeballed diagonal memberships and chain
extents, and got them wrong:
- 453, 498, 810, 869, 930, 993 were listed as c=10 members.
  Computed: 453 = 21²+12 (c=12), 498 = 22²+14 (c=14); 810, 869,
  930, 993 belong to the open-head diagonals c=26/28/30/32.
- "T-263 binds the c=10 tail" was wrong twice: T-263 binds only
  299..539 (the chain stops at 410/451 where gobel2 designs are
  deeper), and 586..971 is bound by the community record at 586
  (rho = 1/sqrt(2)-1).  The true c=10 staircase has 11 roots
  (35, 110, 131, 154, 179, 206, 235, 266, 299, 410, 586).
- The run-26 claim "the register now moves above n=324" was also
  wrong: the register's entire result set spans n = 5..308 with zero
  bounds above 324.
All three corrections are in NEXT_STEPS.md §2/§1; the instrument
recomputes the map from the table so these claims can no longer
drift (failure mode 11 in §3).

## The register's optimality theorems absorbed

The frontier results table (273 rows parsed) contains four theorems
that prove entire diagonal heads: s(k²−1)=k [T-084 Karakuş],
s(k²−2)=k [T-086 chelokot], s(k²−3)=k [T-064 Daniel], s(k²−4)=k
[T-081 Daniel], plus 21 individual results (s(11), s(13)=4, s(21)=5,
s(32)=6, s(44)=7 [T-252], s(45/46)=7, s(59/60/61)=8, s(76)=9,
s(77/78)=9, s(95/96)=10, s(2..5)) and machine-checked s(12)=4.
These 156 proven floors now gate the instrument: without them it
aimed at perfect squares and overcounted the aggregate by 70% (0.736
vs the true 0.4334).

## The corrected leverage map (measured)

- Open rows: 394 (of 546 tied; 152 are proven floors that can never
  move).  All live at r = 2K−1−c >= 5; area room 6.662; the
  leader's standing is 11.5% of that ceiling.
- Top aims (one T-263-class record): 251 (16 rows, 0.015569), 250
  (15, 0.014877), 284 (16, 0.014863), 191 (13, 0.014854).
- Aggregate: one record at every diagonal's best open aim =
  0.4334 (56.6% of the gap); uniform depth d* = 0.0382 over the 394
  open rows matches the leader.
- The instrument's top-diagonals table reproduces the original
  Run-13 §2 numbers exactly (c=26: 0.274/16; c=25: 0.272/15; ...) -
  that table was right all along; only the run-26 edit was wrong.

## NEXT_STEPS.md rewritten to the Run-27 state

Section 0 status table (runs 14-27); §1 tie structure with the
proven-floor split; §2 corrected with instrument numbers; §3 extended
with failures 11-12; P4 rewritten as instrumented; value ladder
updated.  Copies: NEXT_STEPS.md and download/NEXT_STEPS.md.

Score 22.819977568 (unchanged - instrument run); submission.csv
round-trip 0 issues; download copies in sync.
