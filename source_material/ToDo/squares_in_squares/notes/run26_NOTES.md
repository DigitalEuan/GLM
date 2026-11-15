# Run 26 notes (2026-11-06)

Run documentation under the distinct name (README.md reportedly never arrives at the user's end).  The same content is in README.md (Run 26 section), RUN_NOTES.md, and download/run26/README.md.
# Run 26 (2026-11-06): P1 closed; the source watch pays

User: continue - see NEXT_STEPS.md (which likely needs updating).

## P1(b) two-block — closed by domination

The exact version of the named design: a 45-degree m x m corner block
(lower-left face on the line x+y=D, D integer) plus the maximal
integer-lattice axis-aligned fill.  L = (D + (3/2)sqrt(2) m)/2 and
n = m^2 + |cells|, all exact integer/radical arithmetic.
763 designs enumerated (m<=24, D<=139, L<=34),
284 finalize-verified: 0 penetration,
count, L=formula everywhere.  Result: the family never exceeds the
plain grid capacity floor(L)^2 at the same L (0 designs beat it; min
gap 0 at the single tie m=1, D=3, L=2.5607, n=4=gridcap).  The
acceptance test n=44/58/31 fails by capacity: ceilings 36/49/25 below
their grids - short by 8/9/6 squares.  P1(b) is closed.
(Ledger: workspace/push/twoblock_run26.json.)

## P1(c) tilted seams — closed as a family; the blob regime named

Census over all 454 sub-grid rows:
314 are strip-45 (P1(a), closed run 25),
31 are Pythagorean-exact,
109 are drifted.  The cleanest record,
n=50, decodes exactly: L=53/7 (dev 1.7e-9), angle arctan(3/4) (dev
1.6e-11 deg), tilted centers on the 1/50 lattice (maxdev 8.1e-8),
axis grid at 2/7 mod 1 (offsets 1.3e-8), 105 contacts at zero - it
packs grid-capacity+1 (49+1 squares) into L=53/7.  These are
isostatic hand-polished arrangements on rational lattices, not
members of a parametric family: the decode->closed-form->sweep method
does not transfer.  P1(c) is closed as a family; the follow-up (P1'
in NEXT_STEPS.md) is a blob-regime insertion campaign seeded from the
records themselves.  (Ledger: workspace/push/seam_census26.json.)

## P3 source watch — T-263 s(299) imported; the only score gain of runs 14-26

The weekly register check found jlevy/squares #824/#893: s(299) <=
17.8012385339790622 (T-263; finder Evan Daniel via fault-line DP
seeded from Deotte's s(334), improved by Doega Oezden by 1.54e-8),
superseding the catalogue's 33/2 + sqrt(7)/2.  The retained packet
(kenaznia-doga/s299-upper-bound) carries the certificate as exact
rationals; fetched, parsed, and verified: packlib.verify ok=True with
L = side EXACTLY and worst_pen = 0.0.  Applied: 17.822875657 ->
17.801238536 (row gain 0.001251307), provenance recorded in
the row src.  (Ledger: workspace/push/import_s299.json.)

## P4 fixpoint — the chain propagates T-263

cascade3 converted n=334 (18.822875659 -> 18.801238538) and n=371
(19.822875659 -> 19.801238538) by the chain law; it correctly stops
where the gobel2 designs are already deeper (410: 20.778 < 20.801;
453; 498).  closure_apply: fixpoint after 0 more rounds;
final_assembly: round-trip 0 issues.  Score 22.823536149 ->
22.819977568 (-0.003558581); beats-grid 454 (334 and
371 are the new sub-grid members); submission.csv rebuilt and all
1000 rows re-verified independently from the CSV.

## NEXT_STEPS.md rewritten

Now current with runs 14-26: new section 0 (execution status, every
closure with its numbers), the gap recomputed (0.765556), P1 replaced
by P1' (blob-regime insertion, first targets the at-grid c=10 tail
810/869/930/993), P2 marked done, P3 upgraded to weekly register
watch, value ladder updated with the measured T-263 return.  Copies:
NEXT_STEPS.md (top level) and download/NEXT_STEPS.md.
