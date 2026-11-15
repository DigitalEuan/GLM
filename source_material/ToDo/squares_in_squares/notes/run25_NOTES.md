# Run 25 notes (2026-11-06)

Run documentation shipped under this distinct name because README.md reportedly never arrives at the user's end.  The same content is in README.md (Run 25 section), RUN_NOTES.md, and download/run25/README.md.
# Run 25 (2026-11-06): P1 strip scan rerun + P2 remainder

User: "(a) restart the P1 strip scan (as designed, it can be rerun)";
(b) finish the P2 remainder.

## P1 executed — and closed in the negative

The generalized Gobel strip was built EXACTLY, not searched.  A decode
pass (scripts/strip_decode.py) mapped the imported member states
(n=5,10,27,38,52,67 at L=a+1+1/sqrt2) into the (p,q) frame and read
off the closed form: w chains of 45-degree squares (q in [-w/2,w/2]),
2 tip diamonds at +-(L/sqrt2 - 1/sqrt2), and per q-side an independent
staircase with levels k=1..a_s at |q|=w/2+k/sqrt2, diamonds at
p=((a_s-k)-2j)/sqrt2 — every outer vertex touches the container edge
simultaneously.  The decode reproduces the stored states to the last
digit: the imported 'exact:square-N.svg' rows ARE this family.

Result of the sweep as designed (n=K^2-r, r in [5,K+4]) plus a
full-range closure check on all n<=1000:

- 88/88 designs finalize-verified (0 penetration, count, L=formula).
- The 30 w=1 member points: 27 are the SAME design as the table
  (deltas 1e-9..2e-9 = finalize scale noise); n=17 (4.6755 vs 4.7071)
  and n=84 (9.6979 vs 9.7071) are strictly deeper in the table.
- Family beats grid at 196 rows over the full range, but the table is
  strictly deeper at 950 and equal at the rest: **0 finds anywhere**.
- The acceptance test n=44/58/31 FAILS by capacity: the family's
  ceilings below grid are 38/52/27 squares — short by 6/6/4.  No
  (w,a) exists that passes it; this is a capacity fact, not search
  luck.

P1(a) is closed: the generalized strip adds nothing to the current
table on any row.  The remaining P1 candidates are (b) two-block /
block+slab and (c) axis-aligned dominant + tilted seams.
(Ledger: workspace/push/strip_run25.json.)

## P2 remainder — the designed sweep is complete

Run 24 stopped at 45/52 cells; this run re-ran the remainder
(P2_ROWS=134,135,157,158): 8 cells, 4/4 family seeds rebuilt ok
(verified_L == want to 9 dp), 0 hard checks, 0 finds.  Combined:
52/52 cells, 0 hard checks anywhere.  The A/B vs run 23's random
seeds is decided — both seed classes fail identically at targets
grid-0.0005/grid-0.002: these rows are jammed at their family
geometry.  (Ledger: workspace/push/p2_seed_polish_run25.json.)

## Fixpoint + delivery fix

cascade3 + closure_apply re-run after both parts (mandatory order):
0 changes; final score 22.823536149, beats-grid 454; download/table.json
+ submission.csv in sync.

Delivery fix: README.md reportedly never arrives at the user's end —
from this run the run documentation also ships as RUN_NOTES.md (repo
top level) and download/run25_NOTES.md; the README.md copies are kept.

Score: 22.823536149 (before 22.823536149).
