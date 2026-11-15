# Squares in Squares: Exact Construction, Verified Propagation, and the Measured Limits of Search

**A machine-verified study in the GLM lineage**

*Working paper — Run 35, 2026-11-07. Project: github.com/DigitalEuan/squares_in_squares.
Parent study: the Geometric Language Machine (GLM), github.com/DigitalEuan/GLM.*

---

## Abstract

We study the *squares-in-squares* problem — pack *n* unit squares into a
smallest square container of side *s(n)* — in the form of the Kaggle
competition of the same name (1000 puzzles, *n* = 1..1000; score
Σ(L/√n − 1), lower is better), as an application of the Geometric
Language Machine (GLM) methodology: exact arithmetic only, every claim
machine-verified, every negative result recorded as a finding. The
delivered system stands at score **22.642387** (grid ceiling 28.937670;
543/1000 puzzles below the grid ceiling; gap to the reported
leaderboard best 22.0544214515 is 0.587965), with every one of the 1000
packings SAT-verified and round-tripped through a 500,500-row CSV at
12 decimals. The study contributes: (1) an exact, contact-identity
derivation of the generalized Göbel family G(a₁,a₂,b,c) and its clipped
variant — 77 gate-verified rows applied in the runs 9–10 sweeps (17 of
them mid-band finds *beyond* the published catalogue), with the
symmetric subfamily contributing 18 more in run 2 (including genuine
beats at n = 861 and 921); 54 delivered rows carry the family labels
today; (2) an exact propagation algebra
(residue-diagonal band chains, removal closure, and two table laws),
whose monotone-envelope law we *upgrade from an empirical check to a
theorem* by formalizing the removal-closure fixpoint in Lean 4; (3) a
measurement layer over all packings (SAT contact language, a TAX/NRCI
measure from the parent study, a D⁴ symmetry census) that produced
falsifiable, and falsified, hypotheses; (4) a complete negative record
of local-search campaigns — the *stall law*: no search campaign in this
project has ever produced one applied improvement, and every score move
has come from analytic construction or source import; (5) a
reproducible source-integration pipeline whose latest instance (run 35)
imported nine registered world-record certificates (jlevy/squares
T-243, T-257, T-267–T-273) for a measured gain of 0.003604, cascaded
through the propagation algebra. The Lean 4 development
(`workspace/lean/tct_squares`) carries the law layer: proved theorems
(feedback into the system), cited axioms (literature premises), and one
deliberate `sorry` marking the combinatorial-geometry wall that the
whole field shares: no non-trivial *s(n)* has a closed-form proof of
optimality.

---

## 1. Problem, metric, and state of the art

**The problem.** For each *n*, place *n* unit squares (arbitrary
positions and rotations) inside a square container of minimal side
*s(n)*. Squares must be pairwise interior-disjoint and contained in the
container. The Kaggle *Squares in Squares* competition fixes *n* =
1..1000 and scores a submission by

  score = Σₙ (L(n)/√n − 1),

where L(n) is the submitted container side; a missing puzzle is charged
the trivial grid value ⌈√n⌉. Lower is better; the *grid ceiling* (all
puzzles at the trivial grid) is 28.937670.

**What is known.** Optimality is proved for very few counts: *s(n) = ⌈√n⌉*
for the square/adjacent families (n = k², k²−1, k²−2, k²−3, k²−4; the
area bound and the T-084/086/064/081 theorem families of the community
register), a handful of individuals (s(2)=2 … s(5)=2+√2/2,
s(11)=3.87708…, s(12)=4, s(13)=4, s(21)=5, …), and the classical small
results (Stromquist 2003: s(10) = 3 + 1/√2). For the large majority of
counts only *upper bounds* (verified packings) and weak lower bounds
exist. The public frontier is maintained by the community register
(jlevy/squares; results page at squaremath.org), by catalogue
curations (Friedman's EJC DS#7 survey and its Ellsworth/kingbird
mirrors), and by certificate repositories (evand/square-packing;
Mishapolk/square-packing-records).

**This study's position.** Our submission is the verified assembly of
the best constructions available to the system at every count — its own
analytic families and propagation, plus every externally sourced record
that passed the verification gate. As of run 35: **22.642387**
(exact 22.642386651), 543/1000 below the grid ceiling, 457 at grid
(156 of them proven floors). The reported leaderboard best
(22.0544214515) leaves a gap of 0.587965, which §10 decomposes.

---

## 2. Lineage: GLM → cent compiler → this project

This project did not begin as a packing solver. It is a descendant of
the **Geometric Language Machine** (GLM), a substrate-native reasoning
system built on exact carriers (the extended binary Golay code, the
Leech lattice, exact integer/rational arithmetic; no floating point on
any path that feeds a result). Two GLM elements are load-bearing here.

**TAX/NRCI.** The GLM's number-theory evidence defines a symmetry tax
TAX(v) = HW(v)·Y + ‖v‖²/8 and a normalized coherence
NRCI(v) = B/(B + TAX(v)) ∈ (0, 1] with Y = 1/(π + 2/π) ∈
(0.264675, 0.264676), B = 10; NRCI = 1 exactly at the vacuum v = 0
(Lean-proved in the parent study). §6.2 shows this measure, applied to
the SAT data of the packings, separates the landscape into exactly two
phases — and the separation is a *theorem* in our Lean layer
(`nrci_eq_one_iff_zero`).

**Delta-sigma as the irrational carrier.** Irrationals are carried as
processes (feedback loops), never rounded statics. This is why a
packing at exact tangency (√2 diagonals, arctan slopes) can be
*compiled* rather than approximated: the survey record SVGs parse at
20–100 digits; the community certificates arrive as exact rationals in
the center basis t = tan(θ/2); the analytic families are closed-form.

**The cent compiler.** The GLM's evidence was compiled into a physical
compiler (cent compiler v12_2_ext, shipped in this repository's
`workspace/`): an abstract operation is decomposed into atomic steps
and realized on physical substrates ("wheels"). Two wheels are this
project's engines: **W36** (Numerical SAT Substrate) became `packlib`,
the exact verification gate every packing passes; **W37**
(Viscoelastic Settling) became the pressure-settling search engine —
whose campaign record (§7) is a measured null on this landscape.

**Method discipline (SKILL_v3).** Every answer is decomposed into
atomic claims; each claim carries plain English, exact mathematics, and
an executable stdlib re-derivation; refusals are named, never silent.
Concretely in this project: *no result without a script-computed
ledger*; *no row enters the table without passing the gate*; *a null is
a finding*.

---

## 3. Method: the operating loop and the honest gate

**The gate (W36).** `scripts/packlib.py` verifies any candidate state
of (x, y, θ) square placements by the separating-axis test over all
four candidate axes per pair (penetration ≤ 0 required), bounding-box
containment, and a global finalize step (scale (1 + 2·10⁻⁹), 12-decimal
rounding) that guarantees the 12-dp CSV round-trip can never flip a
contact into an overlap. Every packing in the table — imported or
constructed — passes this gate. The one time the gate disagreed with a
source (exact tangencies vs float tolerance, run 30) the *instrument*
was corrected by 2·10⁻¹⁵, not the check skipped.

**The loop.** Sources and constructions → gate → `table.json` (the
system of record) → propagation channel (cascade3 → closure_apply →
final_assembly, mandatory order) → `submission.csv` (500,500 rows) →
independent rescore (`score_submission.py`) → instrumented audit
(`root_audit.py`: chain-envelope fixpoint, aiming map, table laws) →
documents updated together → git commit (the GitHub repository is the
durability line; the sandbox has rolled back four times). All scripts
resolve their own paths from the repository location; the offline
verification chain is deterministic (~15 min).

**Ledgers.** Every run writes measured outcomes to `workspace/push/*.json`
and a narrative to `notes/`. Documentation claims must come from
scripts — a rule written after run 27 caught hand-eyeballed diagonal
memberships in this very document family (failure 11 of
`NEXT_STEPS.md`).

---

## 4. Exact construction: the generalized Göbel family

### 4.1 The architecture and the contact identity

The family **G(a₁, a₂, b, c)** (run 9) places

* a **diamond**: b columns × c rows of unit squares at 45°, centered in
  the container (a solid b×c block in the rotated frame);
* four **corner staircases**: axis-aligned triangles T(a) = a(a+1)/2 of
  unit squares, depth a₁ at corners (0,0), (s,s) and depth a₂ at
  (s,0), (0,s);

with exact counts and constraints

  n = a₁(a₁+1) + a₂(a₂+1) + b·c,
  s = max( √2(b+c)/2,  a₁+1+√2·b/2,  a₂+1+√2·c/2 ),
  a₁ + a₂ ≤ s.

The container formula is a *derivation*, not a fit: the diamond's hull
is the rotated rectangle |u| ≤ b/2, |v| ≤ c/2 (u = (x+y−s)/√2,
v = (y−x)/√2); the staircase's far corner sits at x+y = a₁+1; the
hull's near edge sits at x+y = s − √2·b/2; contact is the equality of
the two. The feasibility inequality a₁+a₂ ≤ s is the adjacent-pair
non-collision along a container edge. The whole family is closed-form
algebra over √2 — the `staircase_cells` and `gobel_count` Lean lemmas
carry its counting half.

**What it produced.** Sweeping all (a₁,a₂,b,c) with n ≤ 1000 under
packlib verification: 68 applied rows (17 mid-band finds *beyond* the
published catalogue, 51 below-grid improvements; run 9), plus the
clipped variant G(a₁,a₂,b,c,t) (run 10: remove t×t blocks at the four
diamond corners — trade 4t² cells for √2·t on all four sides; 9
applied, 5 of them real finds at high n). The earlier symmetric
subfamily sweep (run 2: square diamond, equal depths — the survey's
square-233.svg generalized) applied 18 rows including two *beats on
open problems* — counts grid-tied in both our table and the survey:
**n = 861: 30 → 29.849242** and **n = 921: 31 → 30.849242**. The
strip/central-square family was swept and dominated (0 finds).

### 4.2 Competing hypotheses, tested and recorded

* **Golden-ratio hypothesis.** Record tilts cluster near atan(1/φ) =
  31.717°, but the measured value is 31.5663° — 0.15° apart. φ is not
  the generator; the near-miss is a negative result.
* **Level escalation ("perhaps √3, not just √2?"; run 4).** The exact
  θ-generalized family s(θ) = (2a·M + 2m + p)/(cosθ + sinθ) was
  derived and swept at 7 special angles plus a 0.05° fine sweep: s(θ)
  decreases strictly toward 45°; the minimum sits at exactly 45.00° for
  every (a,p). The 45°/√2 level is simultaneously the family's floor
  and ceiling — rotating away shrinks the diagonal gain (c+s) faster
  than the staircase cost. √3 never wins at any n. First Q(√3)-level
  packings were constructed as by-products (n=5: 1+√3, n=37: 4√3) —
  both beat grid, both lose to the world records.
* **Field census.** 54 exact certificates (`json/galois_certificates.json`,
  1169 across the full angle-family sweeps): Q(√2)/C₂, Q(√3)/C₂,
  Q(√7)/C₂ (genuine — e.g. s(18) = (7+√7)/2), Q(√(2+√2))/C₄
  (x⁴−4x²+2, the real subfield of Q(ζ₁₆)), Q(√2,√3)/V₄ at 15°. The 16
  biquadratic "fits" in the record data failed the residual test
  (2.4e-9..1.6e-8 vs 1.8e-9 genuine). Levels are parallel branches, not
  an escalation hierarchy.
* **Family completeness (run 35 probe).** We tested whether any lattice
  square fits around a family state that the family itself leaves out
  (edge-wedge extensions beyond the staircases): for **all 217 frontier
  cores** — every (a₁,a₂,b,c) whose family side beats or nearly beats
  (within 0.01) the delivered table — the greedy maximal fill adds
  **exactly zero squares**. The corner staircases are already maximal
  lattice packings of their contact triangles; the step gaps admit no
  unit square (max inscribed square in a legs-1 gap triangle has side
  2−√2 < 1); wedge rows exist only for thin diamonds (b ≫ c), where the
  contact geometry already assigns the room to the opposite staircase
  and the swept a₂ parameter covers it. *The family is lattice-maximal
  at the frontier* — a measured statement closing the "wedges" avenue.

### 4.3 The analytic-vs-search verdict

Every applied improvement in this project's construction layer came
from contact-identity derivations of families — not from numerical
search (§7). The motif barrier that defeated every settle engine (a
collective crystalline reorganization) is *trivially crossed by
construction*: the mid-band's craved collective motif is the 45°
diamond with staircases. This is the project's central methodological
lesson, and it aligns with the 45-year literature experience on these
puzzles.

---

## 5. The propagation algebra: one record becomes many

No improvement enters the table as a single row. Every breakthrough is
multiplied by exact propagation laws before it lands
(`scripts/cascade3.py`, `scripts/closure_apply.py`).

### 5.1 Residue-diagonal band chains (the chain law)

Rows live on residue diagonals: for n with K = ⌈√n⌉, the diagonal is
c = n − (K−1)². **Law:** a record at L(m) converts every member n ≥ m
of the same diagonal to L(n) ≤ L(m) + (K(n) − K(m)) — extend the
record's packing with one band strip per shell, placed in the free
margin of the L+1 container computed from the actual bounding box.
Verified example: the T-263 register record s(299) = 17.801238535867
(K=18) → L(334) = 18.801238537761 (+1) → L(371) = 19.801238537765
(+2), the extensions binding at equality up to 2·10⁻⁹ storage noise.
Run 35's imports produced one such conversion (n=338 from the n=303
record: L(303)+1 = 18.9018327 < previous 18.9063328). The Lean
development carries the arithmetic half: `ceil_sqrt_mono` (K is
non-decreasing) and `chain_value_mono` (chain values never decrease
along a diagonal — so `cascade3.py` may take per-n minima in any
order).

### 5.2 Removal closure (the prefix-min envelope)

Removing squares never grows a bounding box, so every n < m inherits
L(m) for free: F(n) = minₘ≥ₙ L(m). `closure_apply.py` realizes the
greedy removal (drop the square whose removal shrinks the bbox most),
iterated to fixpoint because a smaller L at n can itself serve n' < n.
18 delivered rows carry the `closure` label; the run-30 Mishapolk
import's channel post-processing re-earned 12 of its 221 rows at
deeper values (8 band chains, 4 removals) — the channel pays
dividends *after* imports.

### 5.3 The table laws — and their upgrade to theorems

Two invariants hold on the delivered table, checked every run by
`root_audit.py` (run 35: monotone 999/999 clean, shell 937/937 clean
at tolerance 1e-7):

* **Monotone envelope**: L(n) ≤ L(n+1) for all adjacent pairs.
* **Shell law**: L(n + 2⌊L(n)⌋ + 1) ≤ L(n) + 1 — adding 2⌊L⌋+1 squares
  to a packing at container L costs at most one more unit (the two new
  bands fit around the existing bbox).

The monotone envelope is no longer merely empirical. In
`workspace/lean/tct_squares/TCT/Laws.lean` we formalize the envelope
(prefix-min over the upper tail), the removal-closure fixpoint, and
prove:

> **Theorem (`closure_fixpoint_monotone`).** A side table at
> removal-closure fixpoint satisfies L(n) ≤ L(n+1) on its window.

The root_audit "999/999 clean" is the measured instance of this
theorem on the delivered table; the theorem is the *reason* the check
passes, and any future table violating the law would be evidence of a
broken closure, not of a packing phenomenon. The shell law's count
core (m + 2L + 1) is the earlier `cascade_count_symbolic` lemma.

### 5.4 What the channel has paid (measured)

| event | gain |
|---|---|
| run-13 register import (76 records), direct | 0.050264 |
| — chain conversions on those records (33 rows) | 0.013671 |
| T-263 s(299) import + cascade (run 26) | 0.003559 |
| **Mishapolk 221-row import + channel (run 30)** | **0.173983** |
| **run-35 register records (T-243/257/267–273) + channel** | **0.003604** |
| total closed since run 13 | **0.245081** |

---

## 6. The measurement layer

### 6.1 The SAT contact language (`sat_review.py`, run 28)

Per-pair separating-axis data over all 1000 packings (1,806,403 pair
contacts): 51.5% have exactly 2 tight SAT axes (parallel edge or
non-parallel corner), 47.5% have 4 (parallel corner), 1.0% are generic
single-tight contacts; 3-tight is structurally empty. The construction
classes (grid/chain/closure/göbel) are ≥ 99% parallel; the record
classes carry the generic contacts (run18-frontier 8%). The grid rows
have nearest non-contact gap exactly 1.0 — the grid is *provably rigid
at the pair level*, which converts the search nulls on grid rows from
anecdote to measurement.

### 6.2 The TAX/NRCI measure (`sat_measure.py`, run 29)

The binary layer of the SAT data is the **symmetry tie** (both axis
families see the same two directions). The tie residual is sharply
bimodal: tied ≤ 5e-12, generic ≥ 1.1e-8 — a 3.3-decade empty gap;
"parallel" is a measured property, not a tolerance choice. Carrying the
contact word as the carrier: SAT-TAX = g·Q (g generic contacts,
Q = Y + 1/8 from the parent study), SAT-NRCI = 10/(10 + SAT-TAX).
Findings:

1. **The vacuum (NRCI = 1) is exactly the grid rows** — now the Lean
   theorem `nrci_eq_one_iff_zero` (Q > 0 suffices).
2. The only off-vacuum *provable* rows are the four hand-proved
   packings (n = 5, 11, 17, 19); the provable frontier off the vacuum
   is the generic language at small n.
3. Depth is not bought with genericity (frontier-only correlation
   φ vs depth = −0.61): the landscape is two-phase — a vacuum phase
   (lattice-tied; depth via chain arithmetic at large n) and a generic
   phase (small n, where every known proof lives). [Re-measured after
   the run-30 import: +0.14 on the full table — every published
   correlation carries its row set, `NEXT_STEPS.md` failure 15.]

### 6.3 Symmetry census (`symmetry_audit.py`, run 31)

D⁴ census over all 1000 packings: constructions are majority-symmetric
(gobel2/gobelS 100%, chain3 76%, exact 71%, closure 72%) but every
record class is asymmetric (mishapolk 0% — 209/209 C1; run18-frontier
5%). Symmetry is the signature of the parametric classes that already
sit below the frontier — not a route to depth. A record-seeded
insertion campaign built on this census closed by null (the records'
free area is a thin seam fragmented across 51 orientations; best first
candidate overlaps by +0.257), matching Karimi's observation that his
next-shell strip jumps +8 squares: there is no +1 route.

### 6.4 The aiming map (`root_audit.py`)

The instrument computes, after every table change: the chain-envelope
fixpoint (0 rows above the envelope required), the proven-floor set
(156 rows), and the leverage of a hypothetical record at every open
row (conversions through the channel). Current best aim: **c=32,
n=356** (a T-263-depth record there converts 14 rows, value 0.011102);
one such record at every diagonal's first open row is worth 0.375304
(63.4% of the gap). The map is why campaigns are aimed by instruments,
never by eyeball.

---

## 7. Search is measured, and measured to be null here

The W37-derived pressure-settling engine (exact analytic gradient
through the SAT stack, pressure ramp, L-BFGS-B creep) and the
simulated-annealing push were run hard and recorded honestly:

* **Run 6 / 18**: campaigns abort per the run-6 rule on feasibility
  miss; local dynamics cannot cross the rearrangement gap.
* **Run 19 (oracle study)**: the settle-in channel cannot *hold* a
  known solution (E1 basin 0/10 at all noise levels); cold restarts
  1/40 (the n=5 pinwheel).
* **Run 20 (the stall law)**: at target depth d below grid, terminal
  settle penetration is p ≈ 0.45–0.88·d across every tested delta;
  p → 0 only as d → 0. 132 template attempts: 0 finds.
* **Run 22**: soft relaxation can *re-harden* a gap-throttled tight
  target (4/16 hops at n=5) — the pass-through channel — but needs a
  target that exists.
* **Runs 23–25, 30 (P2, closed for good)**: 64/64 cells of
  motif-seeded numerical polish: 0 finds. The T-263 family's 41
  floating squares do not settle deeper by contact-graph re-breaking.
* **Run 5 (the fork program)**: the GLM tie-resolution framework
  (Golay d=4 six-fold ties; carried forks; four resolution mechanisms)
  was mapped onto packing jams and tested with full pressure: 30/30
  structural-seed classifications RIGID_WALL (ρ = 1.000, n/n
  contacts; the clean grid seed has overlap exactly 0 — a perfect
  crystal); the positive control (n = 5 and 12, where below-grid
  optima are famous) failed from grid seeds 0/30 calls. In square
  packing the crystalline tie is a **lock**, not a d=4 ambiguity:
  all branches carry the same state, so there is nothing to
  discriminate and no key to supply. Every structural wheel tried
  (tilted grids, mirror splits) certified dead by exact inequalities.
* **Run 35 (wedge extensions)**: family-completeness probe (§4.2):
  0/217 frontier cores admit any extra lattice square.

**The honest ledger: no search campaign in this project has ever
produced a single applied improvement.** Every score move came from a
construction family or an import. This is a measured property of this
landscape (the stall law + the motif barrier), not a limitation of the
engines in general — and the engines' real role is the verification
gate and refinement, which is where they have delivered throughout.

---

## 8. Source integration: the record frontier

Sources beat search — every score move since run 9 has been an import
or a construction. The gate discipline (§3) makes import safe: every
external packing is re-verified exactly as our own constructions.

**The register (jlevy/squares; squaremath.org results page).**
Attributed records with T-ids, exact certificates, and independent
re-verification. Runs 13/18 (76 records, 0.050264 + 0.013671 cascade)
and run 26 (T-263, the s(299) fault-line record, 0.003559) were the
pre-run-30 imports.

**Mishapolk/square-packing-records (run 30).** `upper_bounds.json`
carries verified bounds at *all* 1000 counts — the band 325..1000 had
been invisible to the n ≤ 324 atlas. 221 exact certificates imported
(center basis t = tan(θ/2)): 22.819978 → 22.645991 (−0.173983) — the
largest single import of the project.

**Run 35 (this study's latest).** The source watch found the register
moving: Evan Daniel's certificate pipeline (evand/square-packing)
registered **nine new upper bounds** — T-243 (n=182), T-257 (n=172),
and T-267–T-273 (n = 175, 204, 260, 268, 293, 303, 304) — each below
our table and below every previously public bound at its count. All
nine certificates were mirrored (`workspace/sources/candidates/`),
parsed exactly, and passed the gate; applied with the attribution map
(ledger `workspace/push/import_candidates35.json`):

| n | side before | side after | record |
|---:|---:|---:|---|
| 172 | 13.618988959 | 13.617935700 | T-257 |
| 175 | 13.764174319 | 13.764050053 | T-267 |
| 182 | 13.974090715 | 13.970916438 | T-243 |
| 204 | 14.808642842 | 14.804361386 | T-268 |
| 260 | 16.645753252 | 16.633520953 | T-269 |
| 268 | 16.878814823 | 16.872499520 | T-270 |
| 293 | 17.634146343 | 17.623065214 | T-271 |
| 303 | 17.909772219 | 17.901832753 | T-272 |
| 304 | 17.929427760 | 17.920944095 | T-273 |

The channel then converted n = 338 (chain3 from the 303 record):
22.645991 → **22.642387** (direct 0.003359 + cascade 0.000245).
Lineage follows the register's own attributions (172 continues the
s(199) record of Nate Chaoweeraprasit, improved by Siddharth Gupta;
204 continues Daniil Ostashev's s(176); 260 continues Kirill
Tymchishin's s(260); 293 is the 260 packing mirrored plus an L-strip).
The standing weekly watch (`fetch_atlas.py`, `fetch_mishapolk.py`,
`fetch_candidates.py` — all idempotent) now covers all three sources.

**Claims we cannot use.** Side-only claims (Kaggle per-puzzle
leaderboard rows without coordinates) are recorded in the register
issues and deliberately not imported — a side without a verifiable
packing is not a result under our gate. Karimi's two-strip
constructions live at n ≥ 1184 (outside our range), but his **window
theorem** (s(n) < K for all n ≤ K² − 8√K − 19, K ≥ 16; exponent
improved 3/5 → 1/2 over Bui/McClenagan) is the certificate shape for
our mid-band rows: it proves sub-grid *existence* exactly where our
aiming map points.

---

## 9. Formal verification layer (Lean 4)

`workspace/lean/tct_squares` (Lean 4 v4.8.0 + Mathlib) is the
project's proof tier, in three modules:

* **`TCT/Basic.lean`** — premises and arithmetic witnesses: literature
  axioms (Friedman survey data; Nagamochi s(k²−2)=s(k²−1)=k; Stromquist
  s(10)=3+1/√2; competition metric; engine instrument; optimality
  open) and closed lemmas (`cascade_count_symbolic` — the shell count
  m+2L+1, closed with `omega`; `verification_margin_soundness` — a
  square is never negative). One **deliberate `sorry`** remains:
  `s11_optimal_value` — no closed characterization of s(11) (or any
  non-trivial s(n)) is known; it marks the combinatorial-geometry wall
  the whole field shares.
* **`TCT/Layers.lean`** — the perception-layer lattice (Substrate /
  Integer / Rational) with the run-11 boundary: the sharp scan-blindness
  lemma (`scan_blind_to_clearance`) — a 12-dp value scan cannot certify
  at the table's clearance scale — the formal counterpart of the
  measured audit that moved all certification to exact certificates.
* **`TCT/Laws.lean`** *(new, run 35)* — the law layer of §5–6, and the
  paper's formal core:

| formal statement | status | system role |
|---|---|---|
| `prefixMin_le` / `prefixMin_mono` | proved | removal closure: envelope ≤ covered row; monotone in window start |
| `closure_fixpoint_monotone` | proved | **feedback**: the monotone-envelope table law is a corollary of the closure fixpoint |
| `staircase_cells`, `gobel_count`, `gobel_square_count`, `diamond_bbox_square_case` | proved | the Göbel family arithmetic the sweeps use |
| `ceil_sqrt_mono`, `chain_value_mono` | proved | the chain law never converts downward along a diagonal |
| `nrci_eq_one_iff_zero`, `nrci_lt_one_off_vacuum` | proved | the run-29 vacuum theorem (NRCI=1 ⟺ grid rows) |
| `sq_floor_of_area_bound` | proved | perfect-square proven floors from the area bound |
| `Packable`, `area_bound` | axioms | the packing predicate and the measure bound, cited (certified per-row by packlib, not by this development) |

The feedback loop the user asked for is now concrete: the Lean layer
does not merely describe the system — two of its theorems
(`closure_fixpoint_monotone`, `nrci_eq_one_iff_zero`) *explain why
measured checks pass*, and their hypotheses (closure fixpoint, Q > 0)
become machine-checkable requirements on the Python channel and the
measure constants. A future refinement cycle can treat the root_audit
laws as theorem instances: if one fails on a candidate table, the
closure or the finalize step is broken — not the mathematics.

---

## 10. Results

**Score ledger** (grid ceiling 28.937670 throughout):

| stage | score | beats grid | note |
|---|---:|---:|---|
| runs 1–2 | 23.19 | 399 | survey SVGs + first Göbel sweeps |
| runs 3–8 | 23.173640 | 407 | catalogue front confirmed; √3/fork programs null |
| run 9 | 22.897558 | 445 | full G(a₁,a₂,b,c): 17 mid-band finds |
| run 10 | 22.887471 | 448 | clipped family; pocket-fill structurally negative |
| runs 13–25 | 22.823536 | 454 | register import + chains; P2/P1 closed |
| runs 26–29 | 22.819978 | 454 | T-263 + cascade; measurement layer built |
| runs 30–34 | 22.645991 | 543 | Mishapolk import (−0.173983); analysis, nulls, recovery |
| **run 35** | **22.642387** | **543** | **9 register records + cascade (−0.003604)** |

**Delivered census** (script-computed, run 35): grid 457 · mishapolk
207 · chain3 88 · exact 77 · run18-frontier 68 · gobel2 34 · gobelS 18
· removal 18 · closure 18 · register 10 · aux 3 · gobel3 2. Every
below-grid row (543) is either a verified construction, a verified
import, or a verified propagation of one.

**Certification** (all re-verified from disk): 1000/1000 packings
SAT-verified (worst penetration ≤ 0, bbox containment, 2e-9 clearance);
submission.csv 500,500 rows, id continuity 0..500499, 12-dp round-trip
0 issues; Golay/Leech layer 28/28 + 14/14 integer-exact assertions
(Λ₁₆'s kissing number 7320 cited from SPLAG, not verified — marked);
1169 algebraic certificates; 156 proven floors; table laws clean
(monotone 999/999, shell 937/937); chain-envelope fixpoint true.

**The gap, decomposed** (0.587965 to the reported leader): 305 open
rows remain (all at diagonal distance r = 2K−1−c ≥ 5). A uniform depth
d\* = 0.0365 across them reproduces the leader exactly; the area bound
on the open rows allows 5.005 (theoretical ceiling). The aiming map's
aggregate (one T-263-depth record at every diagonal's first open row)
is 0.375304 — 63.4% of the gap — with the best single aim at n = 356.

---

## 11. Open problems and forward map

1. **The 305 open rows** are open in the strong sense: zero are proven
   optimal anywhere; the published frontier (register + Mishapolk +
   kingbird catalogue) has nothing below our values except the
   side-only claims we cannot verify. The next gain anywhere is a new
   world record by definition.
2. **The source watch (P3) is the only standing item that has paid**
   (runs 13, 22, 26, 30, 35). Three idempotent fetchers now cover the
   atlas, Mishapolk, and the evand candidate pipeline; the register's
   issues are the alert channel.
3. **Karimi's window theorem** is the right certificate shape for the
   mid-band: if the two-strip constructions are ever optimized below
   n = 1184, import directly (P3).
4. **Certification completeness (P5)**: extend the Lean build with the
   chain-envelope fixpoint checker as a theorem instance; exact
   Fraction replays of imported states; formalize the shell law's
   band-existence half (currently count-only in Lean, existence by
   construction in `cascade3.py`).
5. **Family research beyond the lattice frontier**: §4.2 closes lattice
   wedges; the remaining construction avenues are new *architectures*
   (non-lattice corner fills, partial clips of the clipped family,
   two-strip classes at small angles) — each is a derivation task, not
   a search task, by this project's central lesson (§4.3).

---

## 12. Reproducibility and guarantee

The repository is the complete working state. The offline chain
(`REPRODUCE.md`) re-derives everything from the files on disk:
`packlib.py` self-tests → submission round-trip + independent rescore →
Golay/Leech assertions → field map → figures. The importers
(`import_atlas.py`, `import_mishapolk.py`, `import_candidates.py`) are
idempotent and resume-safe; the channel order (cascade3 →
closure_apply → final_assembly) is mandatory; `root_audit.py` gates
every run (fixpoint, laws, aiming map).

**Guarantee.** Every packing shipped in `submission.csv` was
re-verified from the file as written on disk (pairwise SAT non-overlap
with worst penetration ≤ 0, bounding-box containment, per-n counts, id
continuity 0..500499, 12-dp round-trip stability with ~2e-9 clearance).
Every mathematical claim in the lattice layer is integer-exact; no
floats anywhere in the lattice math. Optimality is never claimed for
any packing except where a cited theorem or register proof row exists
(156 proven floors). Every number in this paper comes from a
script-computed ledger (`workspace/push/`, `json/`).

---

## References

1. W. W. R. Ball / H. S. M. Coxeter / M. Gardner lineage; the modern
   catalogue: S. P. Friedman, "Squares in Squares", *Electronic Journal
   of Combinatorics*, Dynamic Survey DS#7 (2009), and its maintained
   mirrors (Ellsworth-hosted SVG set; kingbird.myphotos.cc).
2. H. Nagamochi, "Packing a square with similar rectangles"
   (s(k²−2) = s(k²−1) = k theorem family), 2005.
3. W. Stromquist, "Packing 10 or 11 unit squares in a square"
   (s(10) = 3 + 1/√2), 2003.
4. M. Kearney, N. Shiu, "Packing unit squares in squares" (small-n
   results), 2002. [Cited as premise in TCT/Basic; the community
   register carries no optimality row at n = 6 — the "s(6) = 3 theorem"
   line was retracted in run 28 and s(6) = 3 stands as a conjecture in
   our classification.]
5. Karakuş, rectangle bound s(N) ≥ 1/2 + √(N − ⌊√N⌋ + 1/4)
   (register row T-083; checked against every row, run 28).
6. A. Karimi, two-strip packings and the window theorem
   s(n) < K for n ≤ K² − 8√K − 19 (K ≥ 16); preprint read at run 30.
7. Community register: jlevy/squares (github.com/jlevy/squares),
   results at squaremath.org; T-ids per the closing replies of issues
   #806/#845/#914 (records T-243, T-257, T-267–T-273).
8. E. Daniel (evand), square-packing certificate pipeline
   (github.com/evand/square-packing; `search/packer/candidates/`).
9. M. Polkovskyi (Mishapolk), square-packing-records
   `upper_bounds.json` (exact rational bounds, N ≤ 10000).
10. E. R. A. Craig (DigitalEuan), *The Geometric Language Machine* and
    *GLM Complete Number Theory Evidence* (TAX/NRCI, delta-sigma
    carriers), github.com/DigitalEuan/GLM; SKILL_v3 methodology.
11. J. H. Conway, N. J. A. Sloane, *Sphere Packings, Lattices and
    Groups* (Λ₁₆ kissing number 7320 — cited, not verified here).
12. This project's ledgers: `workspace/push/*.json`, `json/
    galois_certificates.json`, `json/leech_map.json`, and the Lean
    development `workspace/lean/tct_squares` (TCT/Basic, TCT/Layers,
    TCT/Laws).

---

*Operational note.* This document is the study overview
(`GLM_INVESTIGATION.md`); the system record is `STATUS.md`, the
forward map `NEXT_STEPS.md`, the reproduction chain `REPRODUCE.md`,
and the run ledger `notes/`. Updated together each run (the run-32
documentation-freeze failure made this a standing rule).
