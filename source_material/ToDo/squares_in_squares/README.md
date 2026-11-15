# Squares in Squares — Verified Constructions, Leech-Lattice Analysis, and the Rotated-Block Program

This repository is a reproducible working state of a
Kaggle *Squares in Squares* project (pack n unit squares into a minimal
square container; 1000 puzzles, n = 1..1000; score = Σ(L/√n − 1), lower
is better), extended with a machine-verified Leech-lattice layer and a
fully enumerated rotated-block family program.

**Where this project began.** It is a branch of the GLM study
(github.com/DigitalEuan/GLM): the *Geometric Language Machine*, foundations include: use exact Arithmetic; no floats/rounding, no SHA-256, no random or disruptive operations anywhere possible - specifically within computation,
number-theory evidence-based (TAX/NRCI, Y/Q/B constants, delta-sigma as the
canonical carrier for irrationals). Part of the GLM project is a concept generator — the cent compiler v12_2_ext, it has "wheels" of data that spin to find operational paths regardless of domain 
(github.com/DigitalEuan/squares_in_squares/tree/main/workspace/cent_compiler_v12_2_ext).
Two of those wheels are this project's engines: **W36** (Numerical SAT
Substrate — the exact algebra that became packlib's SAT verifier) and
**W37** (Viscoelastic Settling — the creep/pressure ramp that became
the "pressure-settling engine" - the engine concept the cent_compiler generated). Every construction this project
produces is a wheel certificate (W36); every search it runs is a wheel
settle (W37). The record from start to finish — lineage, engines, sources,
operating loop — is the system record in `STATUS.md`. More operatiors and more/denser wheels should produce more concepts, I suspect the Python libraries would make excellent wheels - reduce to cent_compiler '¢' primitives and exact Arithmetic then confirm with Lean4.

## Current results (Run 36, 2026-11-07; last score move run 35)

| Quantity | Value |
|---|---|
| Submission score | **22.642386651** (rounded **22.642387**; grid ceiling 28.937670, improvement −6.295283) |
| Puzzles beating the plain grid | **543 / 1000** |
| Leaderboard best (reported) | 22.0544214515 → gap **0.587965** |
| Certification | 1000/1000 packings SAT-verified + 500,500-row CSV round-trip (0 issues; Run 36 record) |
| Golay/Leech verification | 28/28 + 14/14 assertions, integer-exact |
| Algebraic certificates | 1169 (7 angle families + surveys + run-11 census) |
| Proven-optimal rows | 156 (152 tied at grid + 4 below-grid: s(5), s(11), s(17), s(19)) |
| Latest score move | **Nine Evan Daniel register records (Run 35) + n=338 chain conversion**: 22.645991 → **22.642386651** (−0.003604) |

## The score engine (what actually produces improvements)

1. **The project's own engines (GLM lineage)** — the W36 SAT substrate
   verifies every construction exactly (20–100-digit algebra, pairwise
   separation, 12-dp round-trip), and the W37-derived pressure-settling
   engine (analytic gradient through the SAT stack, pressure ramp,
   L-BFGS-B creep) is the honest search layer: its campaign record is
   measured and null on this landscape (the stall law: terminal
   penetration p ≈ 0.45–0.88·d at target depth d), so it now serves as
   the verification/refinement gate, not the discovery layer. The
   Leech/Golay layer (leech_core, octad_moves: 28/28 + 14/14
   integer-exact assertions) classifies all 1000 rows by number field.
2. **Source integration** — the survey's 235 record SVGs (20–100 digit
   parse), the Ellsworth catalogue, the community register (76 records
   our table lacked, run 18; the T-263 record, run 26), and — the
   largest import of the project — **Mishapolk/square-packing-records**
   (run 30: verified bounds at ALL 1000 n; the band 325..1000 was
   invisible to our atlas; 221 rows imported, −0.173983). Sources beat
   search: every score move since run 9 has been an import. I am trying to keep track of all external sources and clearly identify and reference them.
3. **Analytic families** — Göbel strip/central-square, the 4-parameter
   diamond+staircase G(a1,a2,b,c) (17 mid-band finds beyond the catalogue),
   the clipped variant G(a1,a2,b,c,t) (5 more).
4. **Exact propagation** — removal closure (prefix-min envelope) +
   L-extension band chains; the residue-diagonal law multiplies every find
   (one base at n₀ opens its whole diagonal n = (K−1)² + c).
5. **The honest gate** — every state, imported or constructed, is
   packlib-verified (SAT non-overlap, bbox containment, 2e-9 clearance,
   12-dp round-trip). Nothing ships unverified.
6. **The measurement layer (runs 27–31)** — `root_audit.py` (chain-envelope
   fixpoint audit + the aiming map: where a new record pays most; best aim
   c=32 n=356), `sat_review.py` (per-pair SAT margins, contact language,
   Maxwell ratios), `sat_measure.py` (TAX/NRCI regime map — the GLM's own
   measure applied to the SAT data: the vacuum is exactly the grid rows),
   `symmetry_audit.py` (D4 census: constructions symmetric, records
   asymmetric), and `root_audit.py`'s `table_laws` block checks the
   monotone envelope and the shell law every run (999/999 and 937/937
   clean at run 34). Every campaign is aimed by these instruments,
   never by eyeball.

## Reproducing

See **REPRODUCE.md** for the exact command chain, expected outputs, and
the list of steps that need network access (live catalogue mirrors) or
transient /tmp files.

## Operations 
Each run, update top-level STATUS.md (include the README.md copied at the bottom of STATUS.md), NEXT_STEPS.md and REPRODUCE.md all need updating. If possible GLM_INVESTIGATION.md should be upkeep as an overview of the whole study.

## Guarantee

Every packing shipped in submission.csv was re-verified from the file as
written on disk (pairwise SAT non-overlap with worst penetration ≤ 0,
bounding-box containment, per-n counts, id continuity 0..500499, 12-dp
round-trip stability with ~2e-9 clearance). Every mathematical claim in
the Leech layer is machine-verified with exact integer computation; no
floats anywhere in the lattice math. Λ16's kissing number 7320 is cited
(SPLAG), not verified — marked as such everywhere it appears.
