# Squares in Squares — Verified Constructions, Leech-Lattice Analysis, and the Rotated-Block Program

This repository is the complete, reproducible working state of a
Kaggle *Squares in Squares* project (pack n unit squares into a minimal
square container; 1000 puzzles, n = 1..1000; score = Σ(L/√n − 1), lower
is better), extended with a machine-verified Leech-lattice layer and a
fully enumerated rotated-block family program.

## Headline results (run-12 era; see the top-level docs for the
current state — this file's ledger sections carry the per-run numbers)

| Quantity | Value |
|---|---|
| Submission score | **22.887471** (grid ceiling 28.937670, improvement −6.050199) |
| Puzzles beating the plain grid | 448 / 1000 |
| Certification | 1000/1000 packings SAT-verified + full CSV round-trip |
| Golay/Leech verification | 28/28 + 14/14 assertions, integer-exact (leech_core.py, octad_moves.py) |
| Grid → Leech-level mapping | 87% exact number-field coverage (leech_map.py) |
| Algebraic certificates | 280 (7 angle families × full (a,p) sweeps + survey records) |

## Repository layout

```
scripts/            All pipeline code (Python; one module = one stage).
  packlib.py          THE verifier: SAT non-overlap, bbox, CSV I/O, finalize.
  theta_family.py     Rotated-block family: exact s(θ) formula, feasibility,
                      sweep machinery (7 special angles).
  theta225_push.py    Run 5: full 7-angle re-sweep, certificate collection
                      build (54 → 280), Level-0 gap analysis, extended-range
                      sweep 1001..5000.
  gobel_squares.py    Göbel 45° family (historical entry point).
  galois_certs.py     Galois certificates for construction levels.
  build_table.py, final_assembly.py, score_submission.py
                      Table assembly, submission.csv + round-trip, scoring.
  leech_core.py       Golay code + Leech lattice, tower, projection law
                      (28 verified assertions, exact integer computation).
  octad_moves.py      Octad calculus: Steiner ladder, intersections,
                      distance-8 graph, covering radius (14 assertions).
  leech_map.py        1000 grids → number fields → laminated-tower levels.
  level_audit.py      The audited field-identification standard (2e-8).
  figures.py          The 5 report figures (English labels).
  gen_report.js, patch_footers.py  Report docx generation + post-processing.
workspace/          Data: submission/ (table.json, submission.csv,
  galois_certificates.json, extended_table_5000.json, ...),
  svgs/ (survey SVGs), ledgers, docs, tools. (glm-repo/ is a reference
  clone excluded from the archive.)
download/           Deliverables: submission.csv, table.json, reports,
  figures, verification JSONs. See download/README.md.
```

## The five runs (history)

1. **Engine + survey integration** — cascade search, 235 survey SVGs
   parsed with the survey's own parser, removal windows, partial-fill
   chains: score 28.35 → 23.19.
2. **Göbel families** — full (a,b) sweep applied 18 verified improvements;
   family proven exhausted for n ≤ 1000.
3. **Closure + chains** — removal-closure to fixpoint, chain3 family:
   score 23.173640 (final), 407/1000 beat grid; live-catalogue check
   confirmed we are at the published frontier for n ≤ 1000.
4. **Leech layer** (leech_core.py, octad_moves.py, leech_map.py) — the
   logic of the Golay/Leech system verified exactly; the 1000 grids
   mapped to laminated-tower levels by number field (87% exact);
   Q(√2) alone carries 70% of the total improvement.
5. **Rotated-block program completion** (theta225_push.py) — all 7
   special angles swept over the full (a,p) range: 271 verified members,
   certificates 54 → 280 (including 38 in the nested quartic field
   Q(√(2+√2)) with cyclic C4 Galois group). The hoped-for conversion of
   Level-0 puzzles did NOT materialize: of the 130 unresolved grids, the
   family reaches only 10, and loses to the numeric optimum on every one
   (closest gap 0.004 at n=28). The 45° kink-minimum (proven by sweep)
   and the exhaustion result of Run 2 explain why. No table or score
   change; the deliverable of Run 5 is the certificate collection plus
   the honest negative result.

## Reproducing

See **REPRODUCE.md** for the exact command chain, expected outputs, and
the list of steps that need network access (live catalogue mirrors) or
transient /tmp files.

## Guarantee

Every packing shipped in submission.csv was re-verified from the file as
written on disk (pairwise SAT non-overlap with worst penetration ≤ 0,
bounding-box containment, per-n counts, id continuity 0..500499, 12-dp
round-trip stability with ~2e-9 clearance). Every mathematical claim in
the Leech layer is machine-verified with exact integer computation; no
floats anywhere in the lattice math. Λ16's kissing number 7320 is cited
(SPLAG), not verified — marked as such everywhere it appears.


# Run 18 (2026-11-05): snapshot as system of record + cent v12_2

**The project now has a GitHub snapshot of record:**
https://github.com/DigitalEuan/squares_in_squares — it carries everything
done so far and the most up-to-date `submission.csv` (scores 22.823536,
454/1000 — the current frontier). After this sandbox's recycles the
snapshot is the replay source: restore `workspace/` + `scripts/` from it,
re-fetch the register certs (`python3 scripts/fetch_atlas.py`), then
`import_atlas` + `cascade3` + `closure_apply` + `final_assembly` to
rebuild the frontier (verified twice this run).

Files the snapshot is missing (user can add from local iterations):
- `workspace/sources/atlas/lists/certs/` — 324 register certificate files
  (only best.json survived; `fetch_atlas.py` re-fetches them live);
- run-16/17 `*_outcomes.json` ledgers (this download/ carries them);
- `cent_compiler_v12_2` WITH the extension (see
  `cent_compiler_v12_2_ext.zip` — W36/W37 wheels + the wheels.py
  rational-power parser fix).

## cent_compiler v12_2 extension (user ask 3)

Fetched from the GLM repo. Extended (workspace/cent_compiler_v12_2,
delivered as `cent_compiler_v12_2_ext.zip`):
- **W36** Numerical SAT Substrate (NumPy) and **W37** Viscoelastic
  Settling (SciPy) as proper wheels (monomial laws, 4 cases each with
  negative controls, dimensions, junctions) — 33 wheels total;
- junctions/non-identities moved into `wheels/index.json` (the loader
  only reads those — per-wheel arrays are silently ignored);
- **upstream parser fix**: `wheels.py` rejected rational `^(1/2)`-style
  powers, so `case_table()` crashed on the native corpus (W21/W24/W25/
  W29/W34); now all 127 rows run.

## Pressure-Settling Engine v2 (pressure_settle.py)

Compiled from W36+W37 (the run-6 pattern). Exact analytic gradient
through the SAT stack (FD-verified < 1e-8, gated in the self-test),
pressure ramp, crystalline seeds, symmetry-breaking kicks. Outcome:
**honest negative** — it clears gradient-exactness but not the two
feasible containers; per the run-6 rule the campaign aborted. Reading:
local dynamics cannot cross the rearrangement gap into tilted banded
architectures; the engine's natural role is local refinement (polish),
not discovery. Full details: `run18_outcomes.json`.


# Run 21 (2026-11-05): boundary demo, wheels census, clue ledger

## Q1 — the engine's 'E 0.01-0.05 stall' is not a machinery floor

boundary_demo.py crossed the grid boundary with the SAME engine, seeds
and gate: verified finds with objective exactly 0.00 at every feasible
target down to g+0.0005 (n=12: 3/4 at 4.0005, verified L 4.000491;
n=20: 2/4 at 5.001), and 0 finds with f ~ 1e-6 below the grid. The
engine resolves the boundary to ~1e-3. The 0.01-0.05 band appears only
inside the infeasible region (the stall law: penetration 0.45-0.88 x
deficit) — there, it is the correct report of infeasibility, and it
cannot be designed around: below grid for the 23 roots the packings do
not exist. What CAN be designed around is prior mismatch (n=20 @ 5.005:
0/4, f=0.145 with RSA seeds vs converged at 5.002) — the engine family
addresses this (lattice prior: grid control 8/15).

## Q2 — wheels: 41 vs 45 reconciled

Both counts are right with different denominators. IMPLEMENTED = 41
(the wheels/*.json files; index.json is generated from them and
agrees; 19 of them are also Python Wheel() defs W1-W19). PLANNED = 45
(the expansion roadmap's full slot range W1..W45). The 4 reserved
slots are W26, W27 (Astrophysics & Cosmology) and W30, W31 (the
unnamed roadmap gap between W29 Spintronics and W32 Capillarity).
The earlier '41 wheels' claims in this README mean implemented; the
user's snapshot counts 45 because the reserved slots exist as defined
ids in the roadmap.

## Q3 — the clues are not zero; they are unanimous

clue_ledger.json assembles seven quantitative channels (Leech
levels/fields, stall law, boundary crossing, atlas, waste-by-level,
score arithmetic, positive controls) — all agreeing that the 23 roots'
optima are their grids. Cross-checking also caught a phantom: an
earlier session's 'n=12 optimum 3.8771' was actually n=11's literature
value mislabelled (the claimed 45-deg 3x3 construction is impossible:
bounding box 3*sqrt(2) = 4.2426 > 3.8771). positive_control.py is
corrected accordingly; the table import was sound all along (n=10
3.7071, n=11 3.8771 correctly present from the atlas).

Deliverables from this run live in download/run21/ (new/edited files
only, each under its repository destination path, with MANIFEST.md).


# Run 22 (2026-11-05): soft relaxation — the pass-through channel

The user asked to try soft relaxation.  Two builds, both honest:

v1 (SA-only hops): uniformly underpowered — 0/16 hard hops on all 8
cells INCLUDING the controls where packings exist.  Kept as
workspace/push/soft_relax_v1_sa.json.

v2 (hybrid; scripts/soft_relax.py): SA hot shuffle with overlaps
allowed (pass-through homotopy, t0 0.30/0.45) + settle_to (L-BFGS-B,
ftol 1e-14) re-hardening.  A hop is HARD when P.verify reports
worst_pen <= -1e-10; its value is the state's OWN extent (may exceed
L_t — the honest requirement of the arrangement).

Results:
- control n=5 tight: 4/16 hard hops, VERIFIED 2.708107407 — a genuine
  below-grid verified find (the pinwheel, 0.293 under grid).  The soft
  channel WORKS where packings exist and the target is tight.
- the channel is gap-throttled: n=5 loose (+0.05): 0/16 — loose walls
  let overlaps persist through polish; soft relaxation needs a TIGHT
  target to generate the re-hardening pressure.
- n=11 (below-grid optimum exists, gap 0.122): 0/16 at this budget —
  a budget verdict, not an existence verdict.
- roots n=12, n=20: 0/16 in all four cells — the soft channel joins
  the unanimous set (runs 20/21): below grid the packings do not exist.

Deliverables: download/run22/ (new/edited files only; MANIFEST.md has
the repository placements).


# Run 23 (2026-11-05): submission audit + tightest ladder sweep

User questions: (2) no README received; (3) did the soft relaxation
move submission.csv or the score?

## Q3 answer: no — with evidence

- Write footprint: table.json content 08:03, submission.csv copies
  19:15; run 22 wrote 22:18+ and touched only
  workspace/push/soft_relax*.json.  Nothing moved.
- sha256: download copies byte-identical to workspace copies.
- Independent recomputation from submission.csv (packlib.verify on all
  1000 rows, every state non-overlapping): 22.823536149 == table
  score.  In sync.
- The score delta the user saw (22.8875 -> 22.8235) is RUN 19's
  application of 6 run18-frontier rows (n=183, 211, 308, 343, 380,
  419), hours before run 22 started.
- Run 22's verified 2.7081 (n=5) was ABOVE the table's existing
  2.7071 (gobelS:a1b1) — a control, correctly not applied.

## Q2 answer: delivery-pattern bug, fixed

Run 22 delivered README.md only nested under download/run22/.
This run refreshes the TOP-LEVEL download/README.md too; standard
from now on.

## Correction of a run-22 claim

"We beat the atlas on all 114 level-0 rows" is RETRACTED as
circular: leech_map.py reads download/table.json — the 'atlas' was
our own table one minute earlier.  The -0.77 was run 19's application
delta.

## The sweep

12 top-waste at-grid rows {2,6,7,8,13,14,21,22,23,30,42,56} x ladder
(grid-0.0005, -0.002, -0.01) x 2 seeds x 8 hops = 288 hop-polishes
(soft pass-through + L-BFGS re-hardening).  Ladder calibrated by the
6 run18-frontier cracks (0.0004..0.0065 below grid).

Result: 0/288 hard hops, 0 finds, table unchanged, score unchanged
22.823536149.  The gap-throttle law is confirmed in the negative
direction — even 0.0005 below grid, no small-n level-1 row
re-hardens.  Honest nuance: the level-1 wall is porous at large n
(run 18's six cracks); the next sweep targets the large-n bands.


# Run 24 (2026-11-05): NEXT_STEPS.md execution

User: "NEXT_STEPS.md has been updated since run 13 — push on as logical."

## Correction of the Run 23 record

The Nov-5 08:03 table write (22.887471 -> 22.823536, -0.0639) was NOT
"run 19 applying 6 rows": it applied 109 rows, all tagged run18-frontier
— the community import (76 records, +0.050264) plus the cascade
propagation (33 conversions, +0.013671), exactly NEXT_STEPS S6.  The 6
rows run 23 cited were the 6 of the 109 that landed below their grid.

## P3 source watch (executed)

Local lists re-imported: idempotent (applied 0, skipped 4, rejected
320) — the table is exactly at the community's certified frontier for
n <= 324.  Live register (2026-11-05): no record changes visible after
2026-10-17.  Verified bounds gained: s(13)=4, s(21)=5, s(32)=6,
s(45)=7, s(60)=s(61)=8 PROVEN — six at-grid rows now proven optimal at
the trivial grid and excluded from all future sweeps; s(12) >= 15680/3951
= 3.9686 (the grid-4 row for n=12 has a certified gap of only 0.0314);
families s(k^2-3)=k, s(k^2-4)=k proven.

## P2 family-seeded polish (executed — the open experiment)

NEXT_STEPS P2 was still open: every previous sweep (runs 20-23) seeded
from random states.  This run rebuilt the 26 best per-n corner-band
family designs from the gobel5 near-miss pool (8489 entries, gap <=
0.002), verified each seed (count, extent, non-overlap), and ran the
identical hop loop as run 23 — same seeds, same anneal streams, ONLY
the initial state differs.

Result: 45 cells, 0 hard checks, 0
finds.  (Details in workspace/push/p2_seed_polish.json.)

## P4 propagation + P1 decision

cascade3 + closure_apply re-run to fixpoint after the sweep (mandatory
order).  P1 (generalized Gobel strip) not executed this run — budget;
it remains the named next architecture, seed map = the near-miss pool.

Score: 22.823536149 (before 22.823536149).


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

---

# Run 28 (2026-11-06): the SAT data reviewed

## The instrument: scripts/sat_review.py

User input: review the SAT data for insight. Per-pair SAT margins over
all 1000 packings joined with depth, class, status; ledger
`workspace/push/sat_review28.json`.

## Five findings (measured)

Contact language 99% parallel (run18-frontier 8% generic outlier);
T-263 family 41 floaters at Maxwell ratio 0.68 (most slack); grid
nearest-gap exactly 1.0; n=50 decode cross-validated (105 contacts);
the tie test is the SAT data's binary layer.

## NEXT_STEPS.md updated to the Run-28 state

§2a added; failure 13 (a "theorem" cited without the register row).
Score 22.819977568 unchanged (measurement run).
---

# Run 29 (2026-11-06): the SAT measure — TAX/NRCI on the SAT data

## Where TAX and NRCI are defined

upload/GLM_Complete_Number_Theory_Evidence.md §1.1-1.3; §4.8 of the
GLM academic paper (the parent system github.com/DigitalEuan/GLM):
TAX(v) = HW(v)*Y + |v|^2/8 = HW*Q on binary carriers; NRCI = 10/(10+TAX)
in (0,1]; NRCI=1 iff v=0. Regimes at integer cutoffs (Lean-proved
thresholds): onBit TAX<=5/2; coherent <=10; transitional <=70/3.

## The instrument: scripts/sat_measure.py

The carrier is the packing's contact word with 1-bits = generic
contacts; SAT-TAX = g*Q, SAT-NRCI with the GLM's constants. Ledger
`workspace/push/sat_measure29.json`. Vacuum = exactly the 546 grid
rows; only off-vacuum provable rows = the 4 hand-proved packings
(5/11/17/19); depth anti-correlates with genericity (frontier -0.61;
chain3 deepest yet nearly vacuum). §2b added.

## NEXT_STEPS.md updated to the Run-29 state

Score 22.819977568 unchanged (measurement run).
---

# Run 30 (2026-11-06): P2 closed for good; the Mishapolk import (largest since run 22)

## (a) P2 — the T-263 renewal returned an honest null

scripts/t263_polish.py: 12/12 cells (299/334/371 x ladder
0.002/0.005/0.01 below row L); settle -> anneal(6k moves) -> re-harden
hops; finalize gate. 0 finds, 0 hard hops; soft extents pinned 0.4-2.5e-3
above L_t in every cell. The 41 floaters at Maxwell ratio 0.68 do not
settle deeper by contact-graph re-breaking. Baselines NRCI 0.3104
(g=57). P2 closed for good.

## (b) P3 — Mishapolk: the band 325..1000 was never empty upstream

fetch_mishapolk.py + import_mishapolk.py: upper_bounds.json carries
verified bounds at ALL 1000 n (the band 325..1000 was invisible to our
atlas). 221 rows imported in 2 invocations (25 + 196; verify-tolerance
fix exact-tangency +2e-15; dry-run ledger bug fixed - applied rows from
a dry run must never feed the resume ledger). Cert format: header n S;
per square x y t (centre, t=tan(theta/2)). Channel: cascade3 9 applied,
closure_apply 3, final_assembly round-trip 0 issues. Score
22.819977568 -> 22.645990613 (-0.173983); beats-grid 454 -> 543.
root_audit refreshed: fixpoint true, 305 open rows, aggregate
0.375304; best aim moved to c=32 n=356 (0.011102, 14 conversions).

## (c) Karimi read (via browser; preprints.org blocks plain fetchers)

Two-strip L-shape with tilted wall strips (Ryu Thm 1.3 lineage); 2824
bounds at n=1184..9944 (outside our range); window theorem: for every
integer K >= 16, s(n) < K whenever n <= K^2 - 8*sqrt(K) - 19 (exponent
3/5 -> 1/2 over Bui/McClenagan) - the certificate shape for our
mid-band rows.

## NEXT_STEPS.md updated to the Run-30 state

§2a.2, §2c added; P2 closed-for-good; P1' aimed. Score 22.645990613.
---

# Run 31 (2026-11-06): the symmetry review — user input as a measured hypothesis

## (a) The D4 census (scripts/symmetry_audit.py)

User input: "many optimal grids are symmetrical and efficient." Treated
as a hypothesis and measured on the run-30 table - a D4 point-group
census over all 1000 packings (8 elements about the bbox center;
rotations leave theta invariant mod pi/2, every reflection maps
theta -> -theta), joined per row with recomputed SAT measures (C, g,
phi, NRCI), depth, class, status. Ledger
`workspace/push/symmetry_audit31.json`.

Findings (section 2c of NEXT_STEPS.md):
- The input is true of the construction classes, not of the records.
  gobel2/gobelS 100% symmetric (D2/D4), chain3 76%, exact 71%, closure
  72% - but mishapolk 0% (209/209 C1, distance-to-symmetry >= 0.1),
  run18-frontier 5%, register (T-263) C1.
- tied-vs-sub 15.3% vs 37.6% - storage artifact (stored tied states
  are tail-drop grids; canonical symmetric arrangements exist for
  every tied row).
- G~depth +0.31 / G~C/n +0.32 present but weak.

## (b) The P1' campaign (built on the census) — closed by null

Arm A (symmetric canonical seeds) 14/14 null at the aims 356/395/355;
arm B (record-seeded greedy insertion) 3/3 null after three bug fixes
each caught by a synthetic sanity test (failure 14: seed rule;
tangency sign; container bounds). The Mishapolk records' free area is
a thin seam (best first-candidate overlap +0.257 at n=344), not
+1-voided grids - mid-band +1 insertion at fixed L has no purchase,
matching Karimi's +8-per-K jumps. P1' closed by null; the aims stay
open upstream.

## NEXT_STEPS.md updated to the Run-31 state

§2c written; §3 failures 14-15; P1' CLOSED BY NULL. Score 22.645990613
unchanged (analysis + campaign null).
---

# Run 32 (2026-11-06): rollback recovery + the documentation layer

## (a) The recovery (third rollback of the project)

The tree opened the turn at the run-27 era: HEAD at 9b5ad58, clean
status, but runs 28-31 (SAT review, SAT measure, the Mishapolk import,
the symmetry census) gone from local history. The GitHub remote
(github.com/DigitalEuan/squares_in_squares) held them: adopted via
reset --hard origin/main, then the union restored from the preserved
local lineage (branch sandbox-lineage-27): 789 paths incl. all 73
download/ delivery files, RUN_NOTES.md, the exploration scripts, the
atlas content - plus 10 top-level download/ files the remote itself
had dropped between runs 27 and 31 (run19/20_outcomes, run25_NOTES,
extended_table_5000, fork_results, galois_certificates,
positive_control, theta30_new_members, submission.csv, table.json).

## (b) Re-verification on the recovered tree (P4 doctrine)

Channel loop: cascade3 0 applied; closure_apply fixpoint after 0
rounds; final_assembly round-trip 0 issues; table.json bit-identical
to the pre-loop state. Score 22.645990613, 543 beats - the run-31
fixpoint is intact on the recovered tree. root_audit32.json: 0 above
envelope, 305 open rows, aggregate 0.375304, best aim c=32 n=356.

## (c) The instrument fix

root_audit.py had its score/gap hardcoded to the run-27 values - so
the run-30 refresh (stored in root_audit27.json) printed the stale
gap 0.7656 instead of 0.5916, and the ledger carried the wrong run
label. Fixed: the ledger path and run label are now argv, the score
and gap are computed from the live table. root_audit32 reproduces the
run-30 refresh exactly (0/305/0.375304/356) with the corrected gap
0.591569. Failure 16 in NEXT_STEPS §3 records the standing rules.

## (d) The documentation layer (the user's standing order)

README.md was frozen at the run-13 era - six score moves (runs 18-30)
unreflected; STATUS.md likewise. Now: README refreshed to the run-32
state (headline + score engine incl. the run-27-31 instruments);
STATUS.md REWRITTEN per the new standing rule - it duplicates the
README headline and score-engine information and adds the system map
(how the system operates, what information comes from where: every
artifact class named by its producing instrument) plus the
script-computed source census; RUN_NOTES ported for runs 28-31 (the
ledger was itself at the run-27 state); NEXT_STEPS updated to run-32
(header, §0 row, failure 16, §6 entry 8).

## NEXT_STEPS.md updated to the Run-32 state

P4 re-verified on the recovered tree; the aiming map unchanged (no
table change). Score 22.645990613 (unchanged - recovery + docs run);
submission.csv round-trip 0 issues. Copies: NEXT_STEPS.md and
download/NEXT_STEPS.md.

---

# Run 33 (2026-11-07): rollback #4; the lineage record (GLM, cent
compiler, engines) + the README transport rule

## (a) Rollback #4 and the user's upload (the transport lesson)

The turn opened with the tree back at the run-27 era AGAIN - but this
time the remote had moved: the user's upload (45e0a63) carried the
run-32 NEXT_STEPS.md and STATUS (4).md (the run-32 STATUS, renamed by
the browser), renamed to STATUS.md, then revised (b6408ad). Lesson
recorded as failure 17: the README never comes through the upload
path; STATUS and NEXT_STEPS do. So from this run: STATUS.md carries a
straight, unedited copy of the README at its bottom (the user cuts it
from STATUS and pastes it over the current README - "it WILL NOT work
any other way"); the STATUS body never mentions the copy.

## (b) Run-32 redo (lost to rollback #4)

Everything from run 32 was redone from the conversation records and
re-verified bit-identically: root_audit.py instrument fix; channel
loop (cascade 0, closure fixpoint, assembly 0 issues, table
bit-identical); root_audit32 (0 above envelope / 305 open / aggregate
0.375304 / gap 0.591569 / best aim c=32 n=356); README and RUN_NOTES
rebuilt; NEXT_STEPS was carried by the user's upload (no redo needed).

## (c) The lineage record (the user's three-part order)

1. STATUS.md restructured: the body is now the system + sources record
   from start to finish - the GLM parent lineage (GLM -> cent compiler
   W36/W37 -> this project's engines), the cent compiler section, the
   engines deep dive (pressure-settling: design, honest campaign
   record, the stall law, current role; W36 SAT substrate; the
   Leech/Golay layer), the operating loop, the information map (what
   is ours vs what enters through the gate, with the source census) -
   and ZERO mention of the other file. The README copy rides at the
   bottom after a --- separator, unedited.
2. The "imports only" reading is corrected: the front page and the
   record now state where the engines came from (the cent compiler's
   W36/W37) and what they did - the engines are the origin and the
   gate of everything; imports are what the sources feed through the
   gate the engines define.
3. The three URLs recorded: this project at
   github.com/DigitalEuan/squares_in_squares; the parent GLM at
   github.com/DigitalEuan/GLM; the cent compiler at
   github.com/DigitalEuan/squares_in_squares/tree/main/workspace/cent_compiler_v12_2_ext.

Score 22.645990613 unchanged (recovery + documentation run); 543/1000
beat grid; channel fixpoint re-verified on the recovered tree.

---

# Run 34 (2026-11-07): the cascade recorded; the accuracy dive; GitHub
as the transport

## (a) The user's three-part order

1. repository.zip retired (the GitHub repository carries the whole
   tree; a zip of it is a duplicate) — noted in STATUS §5 and
   NEXT_STEPS 17c.
2. The cascade recorded as STATUS §4 (the standing ask): the chain law
   with live examples (T-263 17.801238535867 -> 334: +1 -> 371: +2,
   binding at equality +2e-9; the n=5 pinwheel -> n=10 = L(5)+1), the
   removal closure, the table laws (monotone 999/999, shell 937/937 at
   1e-7 with the tolerance note), and the measured ledger: import face
   value vs cascade post-processing (register 0.050264 direct +
   0.013671 via 33 conversions; T-263 0.003559; Mishapolk 0.173983;
   total 0.241477 since run 13).
3. Accuracy dive (measured, all ledger-sourced):
   - table laws re-homed from the phantom `gap_analysis.py` (run-33
     STATUS credited a checker that never existed) into root_audit.py
     as a table_laws block; root_audit34 = laws 0/0 + fixpoint 0/305 +
     aim c=32 n=356; channel bit-identical.
   - Register import re-attributed: RUN 13 (import_atlas.py docstring
     'Run 13 push A'; evand/square-packing best.json + certs). The
     'run18-frontier' label was born at the run-18 snapshot-restore
     (restore_from_repo.py). 76 applied (atlas_import.json) -> 75 in
     the census: 3 rows (154/270/303) later beaten by Mishapolk; +2
     (327/332) via the restore.
   - Mishapolk 221 applied -> 209 census: the channel re-earned 12
     deeper (8 chain3 band extensions, 4 closure removals from the
     neighbouring Mishapolk packing) — import_mishapolk30.json.
   - 'Ellsworth catalogue, 164 historical records' replaced by the
     code paths: 235 Friedman survey SVGs (the Ellsworth-hosted set);
     kingbird is the mirror of the survey catalogue (4 SVGs).
   - '448 rows by runs 1-12' verified: the frozen run-12 header of
     this file (448/1000 at 22.887471) — the header now says so.

Score 22.645990613 unchanged (documentation + accuracy run). Copies:
NEXT_STEPS.md and download/NEXT_STEPS.md.

---

# Run 37 (2026-11-08): the mechanics run — the clear picture

**User order.** Continue the project; start from the GitHub repo
(updated); focus on the mechanics of the 2D packing system — the 24D
lattice / Golay clue, the tower of layers, the exact float-free
environment — with the score as sanity check.

**Found at turn start:** the sandbox had rolled back again (run-27
era, remote config missing — the 4th time). The user's updated remote
carried the reconciled Run-36 documents + the imported run-36
artifacts, but its *table* was run-34-era: the run-35 score move was
missing (the reconciliation imported artifacts, not tree state).
Re-executed a 3rd time: import 9 records (0.003359) + cascade n=338
(0.000245) → **22.642386651**; the rebuilt csv is bit-identical (md5
4bbc80de…) to the imported submission.run36.csv. Failure 18 amendment
(d) recorded.

**The study (no score change, by design):** 05-MECHANICS.md — the
provenance picture (layer_settle37): cert-rational 674 (18.1% of
improvement; grid 457 + imports 217), design-quadratic 134 (44.9%),
derived 124 (23.0%), float-only 68 (14.1%). exact_replay37: 133/133
import geometries verified in pure Fraction (both-squares SAT, exact
container fit); drift 1.83e-9…1.35e-8 = the finalize clearance; 84
side-only mishapolk rows = the honest exactness boundary. t-basis
census: all 133 contain axis-aligned squares; the top 45° signature
(20 rows) is the rational 225058681/543339720 = √2−1+O(1e-10); 22 in
the arctan(1/2) bucket; the rest hand-polished rational angles (run
31's asymmetry census agrees). chain3 inheritance exact integer:
L(334)−L(299) = 1+2e-9, L(371)−L(334) = 1.000000000.

**Instruments patched:** leech_map.py (constant-series Spearman now
"UNDEFINED", not a crash — the run-5-era +0.79 was a property of the
construction-era table; on the import frontier 991/1000 are level 0
under the certified standard); level_audit.py (kingbird mirror down:
table-only with a printed note). Mishapolk certs re-mirrored (337
fetched, 8 upstream 404s). Exact chain regenerated: leech_core 28/28,
octad_moves 14/14, galois_certs 280 (9 value-matched on the live
table), level_audit Q 460 / Q(√2) 239 / biquad 19 / no-fit 274.

**The answer to the 24D/Golay clue** (05-MECHANICS §5): the substrate
logic is real, closed and verified; on the current frontier the
empirical Λ-window mapping degenerates — the import frontier is
exact-rational in the t-basis. The tower enforces the language
(exactness), not the score. No isomorphism claimed, none needed.

Score unchanged: **22.642386651** (543/1000; gap 0.587965).
Deliverables: 05-MECHANICS.md; layer_settle37.py; exact_replay37.py;
patched leech_map.py / level_audit.py; 6 ledgers under
workspace/push/; download/run37/ + MANIFEST.

---

# Run 38 (2026-11-09): the score push — 22.642387 -> 22.218057

**User order.** Continue the project; push the score.

**The watch (all force-refreshed).** Mishapolk byte-identical to the
run-30 copy (the ledger's 871 "beats" are our own finalize echo —
failure 19: 'kept' never re-downloads; recorded). Register + atlas
0 new. Imports DRY 0 rows.

**The broader scan (failure 20 born).** Web search over the problem's
name-space: Ostashev's 12 records (we win 8, 4 echo; his README points
at Couzo), Couzo #561's 9 SHA-verified certs (we win 8, 1 echo — our
Mishapolk rows are stronger than this entire 2026 GitHub network),
jlevy/squares = squaremath (our atlas, flat). The tell was in the
register itself: issue #914's Kaggle per-puzzle leaderboard sides sit
below every public packing at 204/268/303/304. The live channel is
Kaggle's public notebook network: busya PRIME's aggregator notebook
(LB 22.2180568; 136 notebooks + 33 datasets, 68,269 packings merged
shortest-first per puzzle, certified by the hosts' metric code as
doubles). Its output is public — mirrored via browser + signed GCS
URL (submission.csv 500,500 rows; provenance.csv per-puzzle 45-digit
L + sources), saved under workspace/sources/busyaprime38/.

**The import** (import_busyaprime38.py; the import_candidates gate
verbatim: verify 1e-9, finalize +2e-9, MIN_GAIN 1e-7): 345 rows
applied, direct gain 0.424330 — the largest single import in project
history (2.4x Mishapolk's 0.173983). Zero verify failures. Channel
flat: 0 chain conversions (the new roots' windows are saturated), 0
closure. Round-trip 0 issues.

**State after**: score **22.218056945** (rounded 22.218057), 553/1000
beat grid, gap to leader **0.163635** (was 0.587965). Laws clean
(monotone 999/999, shell 937/937); fixpoint 0 above envelope / 295
open. Census: busyaprime 345 (the new dominant import class), grid
447, exact 71, run18-frontier 64, chain3 23, mishapolk 13, gobelS 11,
register 7, gobel2 6, closure 6, removal 4, aux 2, gobel3 1.

**The honest reading**: the aggregator's own note says the remaining
0.164 to the leader "is new packings, not a better merge" — the
leader (Cats and boxes, 22.0544214515) holds private packings. The
next moves are: (a) watch the aggregator weekly (it re-runs as public
notebooks improve); (b) the 295 open rows are now mostly
grid-floor/proven-floor territory — the aiming map says T-263-class
records at first open rows would be 0.360798; (c) the proven-floor
set grew with the merge (see root_audit38).

