# Run 28 notes (2026-11-06)

Run documentation under the distinct name.  The same content is in README.md (Run 28 section), RUN_NOTES.md, and download/run28/README.md.
# Run 28 (2026-11-06): the SAT data reviewed

User input: review the SAT data for any insight there.

## The instrument: scripts/sat_review.py

Per-pair separating-axis data over all 1000 delivered packings:
margins (gap = -penetration), contact normals (argmin axis), contact
types (count of simultaneously tight SAT axes), binding-wall touches,
free squares (no pair contact, no wall touch), Maxwell counting
ratios.  Ledger: workspace/push/sat_review28.json.  Validated against
the run-26 n=50 decode: 105 contacts, exact match.

## Five findings (measured)

1. **The contact language is 99% parallel.**  1,806,403 pair contacts:
   51.5% 2-tight (parallel edge / non-parallel corner), 47.5% 4-tight
   (parallel corner), 1.0% generic, 3-tight empty.  run18-frontier —
   the record class — is the outlier at 8% generic contacts, Maxwell
   ratio median 1.057 (1.2+ everywhere else).  P1' guidance: seek
   generic contact structures; the parallel languages are measured
   dead ends.
2. **The T-263 family floats 41 squares.**  n=299/334/371 each carry
   41 free squares at ratio 0.68 — the most slack in the table.  The
   41 are identical across the family; quasi-contacting at median gap
   0.0035, wall distance up to 6.46.  Imported after the P2 polish
   campaign, never polish-seeded.  P2 renewed for exactly this family.
3. **The grid is rigid at the pair level.**  The 546 grid rows have
   nearest non-contact gap exactly 1.0 — a full empty cell.  P2's
   0-finds there are now measured, not anecdotal.
4. **Karakuş's rectangle bound (T-083) gives us nothing new.**
   s(N) >= 1/2 + sqrt(N - floor(sqrt(N)) + 1/4) for nonsquare 8..324:
   0 violations against our L, and it implies grid-optimality only on
   the c=1 diagonal (k^2-1, already T-084).  No new floors — but it
   is the right certificate shape for the mid-band if it extends.
5. **The register is still at grid at every top aim** (250/251/284/
   191/190: finder '-').  Nobody upstream has beaten the mid-band
   either.

Plus one retraction: the tier-1 report's "theorem s(6)=3" is not
backed by the register (n=6 appears only in restricted-optimality
rows, C1/C0).  s(6)=3 stays a conjecture by our classification; n=6
remains a legal aim.  Recorded as failure 13 in NEXT_STEPS: a
"theorem" cited without a register row is a claim, not a floor.

## NEXT_STEPS.md updated to the Run-28 state

New §2a (the SAT data reviewed); failure 13; P2 renewed for the
T-263 family; P1' updated with the generic-contact guidance; §0
status table and run-28 entry.  Copies: NEXT_STEPS.md and
download/NEXT_STEPS.md.

Score 22.819977568 (unchanged — review run); download table/
csv copies in sync (no table change).
