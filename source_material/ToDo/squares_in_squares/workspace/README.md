# Deliverables

- **`repository.zip`** — the full working repository (scripts, workspace
  docs/ledgers, survey SVGs, submissions; excludes the 153MB `glm-repo`
  clone and transient logs). Unzip and read `my-project/README.md` first.
- **`submission.csv`** — the Kaggle submission: 500,500 rows (all 1000
  puzzles), ids 0..500499, format identical to `sample_submission.csv`.
  Every packing re-verified by round-trip (0 issues).
  **Score 23.173640** vs grid ceiling 28.937670 (improvement −5.764030,
  407/1000 puzzles beat grid).
- **`table.json`** — per-n best-packing table (L, state, source per n).
- **`extended_table_5000.json`** — upper bounds for n=1001..5000 (4
  live-catalogue records with states incl. the Sep-2026 n=2043 record,
  29 verified Göbel members, closure with 77 numerical spot-checks, +1
  forward bound; 805/4000 entries beat grid by bound).
- **`galois_certificates.json`** — 54 exact-field certificates (minimal
  polynomials + Galois groups): Q(√2)/C2, Q(√3)/C2, Q(√6)/C2,
  Q(√(2+√2))/C4 (x⁴−4x²+2), Q(√2,√3)/V4, plus the √7 survey records.
- **`theta30_new_members.json`** — the first Q(√3)-level packings ever
  constructed (n=5: 1+√3; n=37: 4√3, min-poly x²−48), full states,
  independently re-verified. Both beat grid; both lose to the world
  records — delivered as mathematical objects, not table entries.
- **`REPORT.md`** — method + verification summary.
- **`GLM_INVESTIGATION.md`** — the deep-dive report on SKILL_v3, the GLM
  system, and the capability mapping (what assisted, what refused, what
  produced the push).

Run 2 ("wheels"): survey re-fetched (family pages gone; remaining
catalogue is the wrong class), motif zoo over all 1000 verified packings
(191 signatures), golden-ratio tested as near-miss (0.15° off — φ is not
a generator), 45°±2.3522° mirrored pair shown sporadic, Göbel family
proven exhausted for n ≤ 1000. No new constructions verified; honest
refusal on the remainder.

Run 3 (directive: GLM-assisted geometric optimization): removal-closure
re-run to fixpoint → **19 more improvements** (18 chain values lowered +
**n=860: 30.0→29.85** from the 861 Göbel base).
**Score 23.173640, 407/1000 beat grid.** Found the live maintained
catalogue (kingbird mirror, updated Sep 2026) — **zero real imports for
n≤1000**: independent confirmation we are at the published frontier.
Crossover window (1000,1024) tested exactly: open by exhaustion (Göbel
max member under s=32 is 964@31.556; next is 1028@32.56; chains ≥32.5).
Delta-Sigma controller + Sturmian classifier implemented and measured:
n=12,13 RIGID_WALL at 3.995 (ρ=1.0); all 10 roomiest mid-band targets
RIGID_WALL at seed level (one full anneal at n=803 measured >150s for
20k moves — classification first is the whole point). Full account in
`GLM_INVESTIGATION.md` (addendum).

Run 4 (level-escalation hypothesis: √3): tested at three layers. (1)
Empirical: levels are PARALLEL — Q(599) ∥ Q(√2)(293) ∥ Q(√7)(24, genuine:
n=18=(7+√7)/2) ∥ numerical(209); zero 30°/60° records anywhere; the 16
biquadratic fits were all chance (residual test). (2) Constructive: exact
θ-generalized Göbel family, verified at 7 special angles + 0.05° fine
sweep — s(θ) strictly decreases toward 45°, minimum at exactly 45.00°;
mixed 45°+30° two-block structures all far worse than grid. (3) Galois
certificates for every level (54). Verdict: NO — 45°/√2 is the family's
ceiling and floor; the jam walls are real structures, not a missing
higher field. New Q(√3) packings built and certified as by-products
(n=5: 1+√3; n=37: 4√3) — both beat grid, both lose to the records.
Score unchanged 23.173640; honest negative with full mechanism. Details
in `GLM_INVESTIGATION.md` (addendum).

Run 5 (tie-resolution framework: carried forks): framework arithmetic
verified exact (1771, 6-fold, 680064=1771×384). Wheels certified dead by
inequality (tilted-grid capacity {0:593}; mirror-split needs θ≥126.87°).
Fork: 30/30 branches RIGID_WALL ρ=1.000 (clean-grid seed overlap exactly
0 — one perfect crystal, nothing to discriminate); 16/16 settles 3 jams
in 3 calls. Positive control n=5/n=12 (below-grid optima famously
known): pressure alone FAILED both — cannot even reach grid−0.004.
Verdict: the crystalline tie is a LOCK, not a d=4 ambiguity; the GLM
mapping inverts at this wall. Zero finds; score stands 23.173640.
Artifacts: fork_results.json, positive_control.json.

# Run 6: residue audit + cent isomorphism engines (residue_audit.py, cent_engines.py)

**Part 1 (audit, verified):** the 593 grid-tied puzzles are exactly
31 perfect squares (r=0, optimal by area) + 60 Nagamochi class
(r=2k-1,2k, s=m proven) + **69 LOW-band counterexamples (r in k+1..18)**
+ **433 MID-band (19<=r<=2k-2)**. Two corrections to the received
picture: (1) "r<=18 solved by cascade" is refuted by data — the
cascade's true reach is r<=k (the jammed LOW band is exactly
r in [k+1..18]); (2) the survey catalogue has ZERO holes vs our table
(checked all n<=1000) — we match the published state of the art
everywhere. The L-extension leverage m -> m+2*floor(L)+1 in L+1 was
verified CONSTRUCTIVELY (packlib: pen <= 8.9e-16) — the audit is in
`residue_audit.json`, the distribution in `fig/f6_residue.png`.

**Part 2 (cent engines, compiled and run):** the four recommended
isomorphisms — P04 flywheel (W4<->W5), P05 optical PLL (W9<->W19),
P11 piezo (W20), P12 Griffith (W21) — were compiled from the
cent_compiler_v12 specs into `scripts/cent_engines.py`: all four run
on one shared exact-SAT substrate (packlib math), with the physics
relations mapped to move dynamics. Selftest: all four engines FIND
n=13 @ L=4.2 from gentle seeds (functional). Campaign on the jammed
band (small bases {6,12,13,20,21,22,30..33} + roomy MID {695,696,748,
749,803,804,862,922,983,984}, containers grid-0.002 and grid-0.02,
236/240 runs, 4 skipped on time budget — same class as completed):
**zero finds**. Every engine jams at the motif barrier (pen 0.02-0.25,
identical at 8k and 20k iterations) — the same signature as every
prior campaign. Honest verdict in `run6_outcomes.json`: the compiled
isomorphisms are functional search engines but none invents the
collective crystalline motif the mid-band needs. Score unchanged:
**23.173640**, 407/1000 beat grid.

# Run 7: strategic plan (Lorentzian lift, gain tables, plan document)

- `scripts/lorentz_lift.py` + `scripts/debug_lorentz.py`: the LorentzianLift.lean
  program compiled for packing (lift linear scoring, certified ties + context,
  bisector-reflection jumps, escalation rounds). Sanity (13@4.2): exact FIND.
  Open targets at grid-0.002: residual pen 1.5e-4..7.7e-4 (prior wall 0.06).
  `workspace/push/lorentz_results.json` holds the honest frontier.
- **Substrate correction (important):** `cent_engines.sat_margins` had its
  orientation matrices transposed since Run 6 — blind to mixed-angle overlaps.
  Fixed and cross-checked against packlib pair-by-pair (debug_lorentz.py).
  Run 6 engines descended a corrupted objective; their packlib-measured
  outcomes stand, the stronger claim is retracted.
- `scripts/gain_tables.py` + `download/run7_gain_tables.json`: the value
  ladder. grid-0.002 over all 593 open = 0.053314 only; MID alone at 0.1
  = 1.848594 (score 21.325046 — past the leader); LOW alone would need
  grid-0.1394 (out of reach). Conclusion: re-aim at the mid-band.
- `download/Run7_Strategic_Plan.docx/.pdf`: the full plan (done / lack /
  next; phases 0-3 with milestones; risks; reproducibility). Cover R4/GO-1,
  TOC + Roman/Arabic numbering, 3 tables + Figure 1 (f6_residue.png);
  postcheck 0 errors; visual page check passed (9 pages, no blanks).

# Run 8: execution of the plan (push, measured)

- **Phase 1 (LP closure)**: scipy/HiGHS feasibility LP over the lift engine's
  near-states. Computed negative with two measured laws: (1) `s* = (k-L)/(k-1)`
  EXACTLY on every target — the engine always lands a rigid grid; the LP is a
  finisher, not a finder; (2) mixed 0/45 contact costs 1+sqrt(2)/2 = 1.2071 on
  every SAT axis vs 1.0 same-angle — compression must come from same-angle
  45 strips (Gobel mechanism). Zero binding flips ever helped; angle flips
  didn't either. `lp_phase1.json`.
- **Phase 2a (sweep)**: LOW complete 69/69, both depths, 2 seeds, 0 finds.
  MID largest-first: 3/433 within session budget (n=1000,999,998), law held
  on all. `lp_sweep.json` (crash-safe incremental).
- **Phase 2b (0.1-class)**: 8 k-blocks (k=17..30) at depths 0.1/0.2 — rigid
  grids everywhere (s* = law exactly), one jammed-worse case, 0 finds.
  `phase2b.json`.
- **Area recalibration**: the plan's Table 2 ignored the area bound. 34/433
  MID can NEVER reach grid-0.1 ((k-0.1)^2 < n). Honest 0.1-class ceiling
  20.541 (vs naive 20.508), still beats the leader. **Leader = uniform
  grid-0.041986 exactly** (d* solved); catch threshold ~0.045, sound win ~0.06.
  Absolute area floor 14.241. `run8_area_recal.json`, `area_recal.py`.
- **Verdict**: search cannot produce 0.1-class; next run must construct
  analytically (Gobel-family sweep for the mid-band, LP as finisher).
  `Run7_Strategic_Plan.docx` now carries the Section 8 Execution Addendum
  (26 headings, Table 4; postcheck 0 errors; visual check passed, 11 pages).
- No finds applied: submission unchanged, local score 23.173640. The free
  Phase 0 re-upload (worth 0.020224) remains: file is
  `workspace/submission/submission.csv` (24.8 MB, 500500 rows).

# Run 9 (2026-11-04): the construction program (gobel2.py)

The FULL four-parameter Göbel family G(a1,a2,b,c) — independent
staircase depths a1 (x+y) and a2 (x−y), b×c 45° diamond — swept for
the first time (the shipped gobel_squares.py covered only a1=a2, b=c).
326 pre-filtered candidates, 68 applied, 0 verify-fails; 17 direct MID
finds beyond the published catalogue (4 of the 10 strategic roomy
targets: 695, 803, 862, 922) + 51 LOW improvements. Propagation:
cascade3 +81, closure +44, fixpoint pass 2. Score 23.173640 →
22.897558; beats-grid 407 → 445; MID below grid 8 → 46.
Wave 2 honest negatives: mixed-wedge serration rows a wash;
asymmetric pair splits split-invariant; side-band squares degenerate.
Full record: `download/README.md` (Run 9 section), `gobel2_results.json`,
`run9_outcomes.json` (headline corrected 2026-11-04: the file was
accidentally regenerated during run 10; true run-9 fixpoint =
22.897558 / 445).

# Run 10 (2026-11-04): the clipped family + the closed front

Wave A: G(a1,a2,b,c,t) — clip the t×t block at each (u,v) sign corner
of the diamond; trades 4t² cells for √2·t bbox on all four sides,
contacts untouched (deep slice degenerates to a smaller Run-9
diamond). 4.37M pre-filtered, 510 generated, 9 applied (5 real finds,
all high-n: 802, 918, 925, 980, 988; depths (√2−1)² and 0.0502525),
0 verify-fails (`gobel3_results.json`).
Wave B: the pocket-fill n-migration front — NEGATIVE, and structurally
so: the closure fixpoint makes L non-decreasing in n, so no state can
help a larger n; 509 clean fills measured, 0 applicable; the exact
all-angle SAT engine (touching-legal) confirms the permissive model's
verdict (`gobel3_fill.json`). The 234 first-pass verify-fails were a
geometric-model bug (mixed-30° states read as 45° balls), fixed by
exact SAT — verdict taken from the corrected engine.
Propagation: cascade3 +2, closure +5 (1 round). Round-trip clean:
500500 rows, 0 issues. Score 22.897558 → 22.887471; beats-grid
445 → 448; MID below grid 46 → 49. Open band: LOW 69, MID 392.
Full record: `download/README.md` (Run 10 section), `run10_outcomes.json`.
