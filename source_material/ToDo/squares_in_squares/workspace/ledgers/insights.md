# Insights

## The residue-family insight reframes the search problem

The competition invites record-breaking (find s(11)-beating packings!).
The cascade planner found a cheaper game: **one base at n = k₀²+r opens the
whole family k²+r across all k**. A marginal 11@3.98 — far from Trump's
famous 3.877 — would score on 30 puzzles. This turns "beat the mathematicians"
into "find any good-enough base per residue", and the L-extension closure
(free, exact, two-path-counted) does the rest. The strategy, not the
gradient, produced the −0.588.

## Instruments that refuse are instruments you can trust

The engine refused 6@2.9 — matching the proven s(6)=3 — and refused 7, 8
below 3 likewise. A search tool whose failures agree with impossibility
theorems is *calibrated*: its successes can be believed (and are then
certified independently anyway). This is the same reflex as the quartet's
refusal taxonomy: what the tool declines to claim is part of its evidence.

## Measured/exact is a contract, not a compromise

Rotated-square geometry has no exact arithmetic (cos of free angles); the
honest move is the TCT §2 clause: declare the error bound, mark the tier
measured. The split here — exact isqrt accounting, exact closure counts,
measured search, double-scanned 1e-9 certificates — keeps every claim in
the right tier. The soundness gap is even named in Lean. The leaderboard
will not care; the ledger does, and the ledger is the study.

## Where physics-style relaxation stops

PBD settling with SAT separation is genuinely good at dense liquid-like
packings and genuinely bad at crystalline motifs: the famous packings
(45° strips, 40° pairs, six-angle 29s) are *low-measure* configurations
that jamming relaxation almost never finds. The frontier table (docs/05)
shows jams at E ~ 1e-2 — the signature of missing motif structure. The
proposed motif-seeded search is the honest next step: analytic families
(Göbel parameters) as seeds, relaxation as polisher.

## The six-study arc, applied

Six studies in, the method's habit is the deliverable: decompose, classify,
double-derive, certify, and put the refusals in the ledger. This one ends
with something you can upload: 300-ish words of theory and a CSV that beats
the grid ceiling on 30 puzzles — with every number behind it re-derivable
by running six scripts.

## Final insight: sources beat search

The campaign's biggest single gain (28.350 → 23.285) came not from a better
optimizer but from integrating the authoritative source: 235 record SVGs
from the live survey, parsed at 20–100 digit precision, completed by
removal windows and partial-fill chains. The engine's honest jams at
E ~ 1e-2 were the *tell* — those configurations are crystalline motifs
(Göbel strips, Trump/Hämäläinen angles), and the community has spent
decades refining them by hand. Lesson recorded: when relaxation jams
systematically, look for the structure it cannot invent, and check whether
that structure already exists as data.

Second lesson: the *removal window* argument (⌊s⌋² < n ≤ N ⇒ drop
squares) is a two-line proof that turned 174 pictured records into
coverage of every n ≤ 324, and the partial-fill chain generalized it to
every n ≤ 1000. Symmetry: dropping squares shrinks n at fixed s; adding
band cells grows n at s+1. Both directions are free once a single record
is in hand.


## Final push (GLM run): analytic families beat annealing — again

A full simulated-annealing campaign (exact SAT penalties, collective moves,
9-schedule probe) could not clear a 2.6e-4 residual on constructed packings
nor a 0.02 sub-grid attack: the motif barrier, quantified. Re-deriving the
Göbel-square family from one survey SVG (square-233.svg) and sweeping its
constraint produced 18 verified improvements in seconds — including two
beats on puzzles grid-tied in the survey itself (n=861: 30→29.849242,
n=921: 31→30.849242). The pattern is now three-for-three across this
project: when search jams, the structure already exists somewhere as data
or as an analytic family; find it, verify it, apply it.

## Second push (wheels run): the catalogue is closed, the frontier is honest

Re-fetched squaring.net: the equal-squares family pages are gone; what
remains on the live site is the integer-dissection (squared-squares) class.
The motif zoo over our own 1000 verified packings shows 191 signatures —
45° dominant (Göbel outputs and chains), with a golden-ratio *near-miss*
(31.5663° records vs atan(1/φ)=31.717°: 0.15° apart — φ is not the
generator) and a mirrored sporadic pair 45°±2.3522° (no rational tangent,
no radical form). Göbel-square family: exhausted for n ≤ 1000 (all 18
applicable members applied last run; asymmetric-depth variants are
dominated by the symmetric member — same s, fewer squares). Residue map:
chain3 covers r ≤ 18 per block; the remaining 594 grid-tied concentrate at
mid-band r = 19..2k, where no source, family, or relaxation route exists.
The wheels doctrine delivered every score jump this project has had; both
wheels are now fully integrated. Score stands 23.193864, 406/1000 beat grid.

## Third push: closure discipline + the live catalogue

The 19-entry closure harvest (score 23.193864 -> 23.173640, incl. n=860
30.0->29.85 from the 861 Göbel base) came from re-running the removal
closure after the family sweep — the two pushes compose, but only if the
loop order is enforced: ANY table change triggers closure re-run to
fixpoint. Second find: kingbird.myphotos.cc — the actively-maintained
mirror of Friedman's catalogue (Davidebyzero; record n=2043 improved Sep
2026). 164 records parsed: ZERO real imports for n<=1000 — independent
confirmation the table is at the published frontier. The one crossover
window (1000,1024) tested exactly: open by exhaustion (Göbel max member
under s=32 is 964@31.556; next is 1028@32.56; chains >=32.5). Sturmian
classifier implemented: all roomy mid-band targets RIGID_WALL at seed
level (rho=1.0, all-touching) — and the cost measurement (one 20k-move
anneal at n=803 >150s) justified classifying before committing cycles.
Extended table 1001..5000 delivered (4 catalogue records with states,
29 Göbel members, 77 closure spot-checks, 805/4000 beat grid by bound).

## Fourth push: level escalation tested (√3 hypothesis) — elegant refutation

The user hypothesized the jam/wall indicates level escalation to √3 (and
higher systems). Tested exhaustively, three layers:
1. EMPIRICAL: angle histogram over all 1000 packings + the catalogue —
   levels exist but are PARALLEL: Q(599) ∥ Q(√2)(293) ∥ Q(√7)(24, genuine:
   n=18=(7+√7)/2) ∥ numerical(209). ZERO 30°/60° records anywhere; the 16
   biquadratic "fits" all had residuals 2.4e-9..1.6e-8 = chance matches
   (expected count at that density ≈ 12), while genuine fits sit at
   ~1.8e-9 (our inflation signature). Parallel levels, no escalation.
2. CONSTRUCTIVE: exact θ-generalized Göbel family, s(θ) =
   (2aM+2m+p)/(c+s), verified states at 7 special angles; s(θ) strictly
   decreases toward 45°, minimum exactly at 45.00° (fine sweep 0.05°
   steps). √3/30° never beats √2/45° at any n. Mixed 45°+30° two-block
   structures: 36 verified, all far worse than grid. The refutation is
   exact and structural: rotating away from 45° lowers c+s (the
   container-diagonal gain) faster than it lowers the staircase cost —
   45° is the kink point of M(θ); √2 is the family's ceiling and floor.
3. CERTIFICATES (the honest "Galois" content): sympy minimal polynomials
   + galois_group for every level: Q(√2)/C2, Q(√3)/C2, Q(√6)/C2,
   Q(√(2+√2))/C4 (x⁴−4x²+2, real subfield of Q(ζ16)), Q(√2,√3)/V4 —
   54 certificates in galois_certificates.json. New Q(√3) constructions
   delivered (n=5: 1+√3; n=37: 4√3, min-poly x²−48) — beat grid, lose to
   the world records (n=37: 6.928 vs 6.5986, a 0.33 gap).
Also: zero of the 593 grid-tied n are proven optimal anywhere in the
literature — the wall is empirical, so level tests had to be (and were)
exhaustive rather than proof-based. Zero real movement in score: the
answer to "is it √3?" is a clean, certified no — with the first √3-level
packings ever built as the by-product.

## Fifth push: carried-fork / tie-resolution (Golay d=4 mapping) — honest verdict

The user supplied a full tie-resolution framework (Golay d=4 six-fold ties,
carried forks, tags/wheels/multi-view) and asked to apply it to the wall.
Operationalized as: replace run-3's jittered seeds (grid_seed tilts every
square ±0.35 rad = the framework's own "blind jitter" failure mode) with
STRUCTURAL seeds, carry all branches (4 bases × hot/cold = 8), classify
each, settle under the Delta-Sigma controller at full pressure.
1. FRAMEWORK ARITHMETIC: all verified exact — C(24,4)=10626=6×1771;
   4096−2325=1771 (the coset-leader and STELEN-weight derivations agree);
   λ₄=C(20,1)/C(4,1)=5, so nearest codewords = {0}∪5 octads = 6-fold;
   680064=1771×384 exactly. The framework's own numbers are correct.
2. WHEELS: A (rigid tilted k-grid at s=k+1, wheel = strip width+tilt):
   extra-square capacity = {0: 593} — zero for every open n, certified by
   the bbox/width inequality (θ≤~2.2° vs needing ≥~15°). B (mirror-split
   ±θ): gap≥1 needs θ≥126.87°, impossible; max gap 0.9980<1. Both wheels
   certified dead — and they are exactly the "tag" class the framework
   prescribes (structural keys resolving ties deterministically).
3. FORK: 30/30 branches across 8 targets classified RIGID_WALL, ρ=1.000,
   n/n contacts; S1's clean-grid seed overlap is EXACTLY 0.0e+00 — a
   perfect crystal, zero ambiguity in the state. All 16 full-pressure
   settles: 3 jams in 3 calls each, zero successes; the wall never yields
   even 0.004.
4. POSITIVE CONTROL (the decisive test): n=5 and n=12 — the smallest open
   grid-tied n whose below-grid optima are FAMOUS and simple (2.7071 =
   45° square + corners; 3.8771) — pressure-alone FAILED both (0/10
   calls × 3 seeds, 61s/83s): cannot even reach grid−0.004. So the settle
   engine is structurally incapable of crossing the wall from a grid seed
   ANYWHERE, including where the answer is known to exist and is simple.
VERDICT: in this problem the crystalline tie is a LOCK, not a d=4
ambiguity. The GLM tie-resolution mapping inverts: at d=4 the six
candidates are all valid codewords and a tag picks the true one; at the
packing wall the branch states are all the SAME state (one crystal, seed
overlap 0, ρ=1) — there is nothing to discriminate and no key to supply.
Every structural key that exists in the 2D geometry (wheels A/B, levels,
mixing) has now been tried and certified dead. Zero finds; score stands
23.173640. The wall re-confirmed by the fork's own protocol — the honest
closing result of the five-push campaign.
