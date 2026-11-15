# Run 31 notes (2026-11-06)

Run documentation under the distinct name. The same content is in README.md (Run 31 section), RUN_NOTES.md, and download/run31/README.md.
# Run 31 (2026-11-06): the symmetry review — user input as a measured
hypothesis

## (a) The D4 census (`scripts/symmetry_audit.py`)

User input: "many optimal grids are symmetrical and efficient." Treated
as a hypothesis and measured on the run-30 table - a D4 point-group
census over all 1000 packings (8 elements about the bbox center;
rotations leave theta invariant mod pi/2, every reflection maps
theta -> -theta), joined per row with recomputed SAT measures (C, g,
phi, NRCI), depth, class, status. Ledger
`workspace/push/symmetry_audit31.json`.

Findings (section 2c of NEXT_STEPS.md):
- **The input is true of the construction classes, not of the
  records.** gobel2/gobelS 100% symmetric (D2/D4), chain3 76%, exact
  71%, closure 72% - but mishapolk 0% (209/209 C1,
  distance-to-symmetry >= 0.1), run18-frontier 5%, register C1.
- **The tied/sub split (15.3% vs 37.6%) is a storage artifact** -
  stored tied states are tail-drop grids; canonical symmetric
  arrangements exist for every tied row.
- **Efficiency (C/n) tracks the contact language**: grid 3.600
  (corner contacts included; validated at n=356: C=1313 = 674 edge +
  639 corner), constructions 3.1-3.6, records ~1.9-2.8. G~depth +0.31
  and G~C/n +0.32 are present but weak - class structure carries them.
- depth~phi flipped to +0.14 on the run-30 table (was -0.61
  frontier-only in run 29): the Mishapolk import added asymmetric
  deep rows. Correlations now carry their row set (failure 15).

## (b) The P1' campaign built on the census - closed by null

At the refreshed top aims 356/395/355 (open upstream too: Mishapolk's
verified best there is the integer grid):
- **Arm A** (symmetric canonical seeds: D4/D2/Cs hole orbits in the
  KxK lattice; ramp_settle pressure + 3 anneal cycles; finalize gate):
  14/14 cells null - 0 hard hops, soft extents pinned ~2e-3 above
  L_t, the run-30 signature.
- **Arm B** (record-seeded greedy max-clearance axis-aligned insertion
  at L(seed)): 3/3 null. Three bugs were found and fixed, each caught
  by a synthetic sanity test (a grid with known holes; the greedy must
  recover exactly those holes): the seed rule, the tangency
  acceptance (pen=0 is legal), and the container bounds (centers in
  [0.5, L-0.5]). The final null is structural: the Mishapolk records'
  free area is a thin seam (best first-candidate overlap +0.257 at
  n=344; 16.7 units^2 fragmented across 51 orientations), not
  +1-voided grids like the gobel rows. Mid-band +1 insertion at fixed
  L has no purchase - matching Karimi's +8-per-K jumps.

P1' is closed by null. The aims stay open; only an imported record can
claim them now. Score unchanged 22.645990613 (the run is analysis + an
honest campaign null).
