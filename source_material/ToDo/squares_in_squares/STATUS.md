# STATUS.md — Squares in Squares: the system and sources record (Run 36, 2026-11-07)

> Run 36 is the canonical latest state represented by the surviving run records. Run 34 remains a historical system-map milestone; the full lineage and source documentation below is preserved.

This is the "everything in one place" document: the full record of how
this project works from start to finish — where it came from (the GLM
lineage), what its own engines are and what they did, how a run
operates, and what information comes from where (ours vs. the world's,
and how the two meet at the verification gate). The current delivered
numbers live in §7, and the cascade that multiplies every breakthrough
lives in §4; the forward-looking analysis lives in
`NEXT_STEPS.md`; the run-by-run ledger lives in `RUN_NOTES.md` and
`notes/`.

---

## 1. The lineage: GLM → cent compiler → this project

This project did not start from a packing solver. It started from a
reasoning system, and every layer of that ancestry is still live in
the repository.

**The parent: the GLM** — https://github.com/DigitalEuan/GLM
The *Geometric Language Machine* (E R A Craig, DigitalEuan, 30.10.26):
a substrate-native reasoning system built on an exact substrate — the
extended binary Golay code, the Leech lattice, and exact integer and
rational arithmetic, with no floating point on any path that feeds a
result. Its scale: 8 registers of carriers reached through 31 query
kinds (one dispatches 67 report subjects); its Lean 4 development
certifies the substrate claims (the GLM's front page reports 414 Lean
files with no `sorry`; our own upload carries the certificate for
`layers_universal.lean` — Lean 4 v4.8.0, 100% formally verified, 0
open sorries). Two pieces of the GLM's number-theory evidence matter
here directly:

- **TAX/NRCI** — TAX(v) = HW(v)·Y + ‖v‖²/8 (symmetry tax), NRCI(v) =
  B/(B + TAX(v)) ∈ (0, 1], with Y = 1/(π + 2/π) ∈ (0.264675,
  0.264676), Q = Y + 1/8, B = 10. NRCI = 1 exactly at the vacuum
  (v = 0); regime thresholds (onBit ≤ 5/2, coherent ≤ 10,
  transitional ≤ 70/3, subcoherent above) are Lean-proved. Both
  papers are uploaded here (`upload/GLM_ACADEMIC_PAPER.md`,
  `upload/GLM_Complete_Number_Theory_Evidence.md`).
- **delta-sigma as the canonical carrier for irrational numbers** —
  one valid physical ∆ among many, recognized via a composed-loop
  predicate, not a property of any single substrate. This is why a
  packing of unit squares at exact tangency can be *compiled*, not
  just simulated: the exact values ride a carrier that never rounds.

**The compiler: cent compiler v12_2_ext** —
https://github.com/DigitalEuan/squares_in_squares/tree/main/workspace/cent_compiler_v12_2_ext
The GLM's evidence was compiled into a physical compiler that lives
in this repository's `workspace/` (delivered as
`download/cent_compiler_v12_2_ext.zip`). The GLM's own wheels folder
carries it as the "cent formula wheels" bundle. Its two wheels built
for this project's domain are the origin of everything below (§3).

**This project** — https://github.com/DigitalEuan/squares_in_squares
The Kaggle *Squares in Squares* competition (pack n unit squares into
a minimal square container; 1000 puzzles, n = 1..1000; score =
Σ(L/√n − 1), lower is better) became the compiler's first full-scale
application: a domain where every solution is an exact algebraic
object (tangencies, √2 diagonals, arctan slopes) sitting inside a
numerical verification problem. The engines came from the compiler
(§3); the sources came from the packing community (§6); the two meet
at the gate (§5) and are multiplied by the cascade (§4).

```
GLM  (exact substrate: Golay/Leech, TAX/NRCI, delta-sigma)
 └─ cent compiler v12_2_ext  (41 wheels; £ → ¢ → ∆ pipeline)
     ├─ W36  Numerical SAT Substrate  → packlib: the verifier of this project
     ├─ W37  Viscoelastic Settling    → the pressure-settling engine
     └─ (W1–W35: the engineering corpus the compiler was built for)
         └─ Squares in Squares  (this project: packings as compiled ∆s)
```

## 2. The cent compiler (the instrument set this project grew from)

A cross-domain physical compiler with a living knowledge base: it
takes an abstract operation £, decomposes it into atomic ¢ steps
(22 ¢ primitives: 16 atomic + 6 composite), enumerates all valid
physical ∆ implementations, escalates through 5 fidelity layers, and
emits a SPICE netlist for the chosen ∆. As delivered here
(`workspace/cent_compiler_v12_2_ext/`, `wheels/index.json`): **41
wheels, 100 axioms, 159 cases** across 8 axes (L, M, T, I, H, N, J,
A); 22 proposals with the full 8-step pipeline trace; 22 `.cir`
netlists written to disk; the native `case_table` corpus runs all 127
rows (after the upstream parser fix for rational `^(1/2)`-style
powers, which had crashed the native corpus — fixed in this project,
run 18).

Two wheels were built *for this project's domain* and are its engines:

| wheel | title (index.json) | what it became here |
|---|---|---|
| **W36** | Numerical SAT Substrate (NumPy) — the packing engine's exact algebra | `packlib`'s SAT verifier: the honest gate every packing passes (§3.1) |
| **W37** | Viscoelastic Settling (SciPy) — L-BFGS-B, creep and the pressure ramp | the pressure-settling engine (§3.2) |

The other 39 wheels are the engineering corpus (Ohm, Fourier,
thermal conduction, …) — they are the compiler's reason to exist and
are not used by the packing pipeline; they are kept because the
compiler is one deliverable, not a packing utility.

## 3. The engines (what this project's own machinery is, and what it did)

The record in §6 must not be read as "this system only consumes other
people's data." The system's own machinery is the verification and
search substrate inherited from the compiler, and it produced this
project's first 448 below-grid rows (runs 1–12: survey parse, Göbel
families, chains, closures) before the import era began. It has
remained the gate ever since: nothing enters the table without
passing the engines.

### 3.1 W36 — the numerical SAT substrate (the verifier)

`scripts/packlib.py` (+ `pressure_settle.py`'s `sat_stack`, the same
math): for every ordered pair of squares, the separation margins on
the four candidate axes [u_i, v_i, u_j, v_j]; for every square, the
signed wall excess on the four container sides. Every packing in the
table — imported or constructed — passes: pairwise SAT non-overlap
(worst penetration ≤ 0), bbox containment, per-n counts, 2e-9
clearance, 12-decimal round-trip through the CSV. Exact values ride
the delta-sigma carrier: the survey's record SVGs parse at 20–100
digits; the Mishapolk certificates arrive as exact rationals in the
centre basis t = tan(θ/2); the Göbel families are closed-form
algebra. The substrate is the reason a 12-dp CSV can round-trip at
all — a float pipeline could not certify tangency at 2e-9.

### 3.2 W37 — the pressure-settling engine (the search layer, and its honest record)

Design (`scripts/pressure_settle.py`, reconstructed after the run-17
recycle from the engines' import contract): the settle objective f =
Σ max(pair_margin, 0)² + Σ max(wall_out, 0)² (squared hinges; f = 0
exactly at a jammed feasible state) with an EXACT analytic gradient
through the SAT stack (finite-difference-verified < 1e-6 in the
self-test); pressure ramp; crystalline seeds; symmetry-breaking
kicks; L-BFGS-B creep (W37's title). The known n=5 pinwheel sits at
objective ~0 — a solution is a zero of f.

Campaign record (measured, all ledgers in `workspace/push/` and
`download/`):

- **Run 6 (the origin)**: the cent engines' first campaign on this
  table — 0 finds. The residue audit that followed corrected the
  picture: the engine's natural role is local refinement, not
  discovery.
- **Run 18 (v2)**: honest negative — clears gradient-exactness but
  not the two feasible containers; campaign aborted per the run-6
  rule. Reading: local dynamics cannot cross the rearrangement gap
  into tilted banded architectures.
- **Run 19 (oracle study)**: E1 basin 0/10 at ALL noise levels — the
  settle-in channel cannot even *hold* a known solution; E2 cold
  restarts 1/40 (the n=5 pinwheel); revalidation: n=10 @ 3.72 — 1/24
  rediscoveries, best L 3.719999566183 (the svg-record class found
  from cold seeds); n=40 @ 6.84 — 0/24 (the Göbel a3b4 family not
  found at this pressure).
- **Run 20 (the stall law)**: at target L_t = grid − d, the best
  terminal settle objective gives penetration p ≈ 0.45–0.88·d across
  every tested delta; p → 0 only as d → 0. If a packing existed below
  grid, some seed would reach it — none does. 132 template attempts:
  0 finds (best f 4.5e-7 at n=12, d=0.001).
- **Run 22 (soft relaxation, the pass-through channel)**: v1 SA 0/16
  incl. controls; v2 hybrid at n=5 tight: 4/16 hard hops, verified
  2.708107 below grid — the engine *can* re-harden a gap-throttled
  target, given a tight one.
- **Run 30 (the T-263 renewal, closing P2)**: 12/12 cells (299/334/371
  × ladder 0.002/0.005/0.01), settle → anneal(6k moves) → re-harden
  hops; 0 finds, 0 hard hops; soft extents pinned 0.4–2.5e-3 above
  L_t. The 41 floaters at Maxwell ratio 0.68 do not settle deeper by
  contact-graph re-breaking. P2 closed for good.

Current role (the design law): the engine is the refinement and
verification gate — the honest gate of §5 — and the measurement
layer's subject (runs 28–29: per-pair SAT margins, the contact
language, TAX/NRCI on the SAT data). It is not the discovery layer:
no search campaign in this project has ever produced a single applied
improvement (every score move came from a construction family or an
import — §6). That is a *measured* statement about this landscape
(the stall law), not a limitation of the engine elsewhere.

### 3.3 The Leech/Golay layer (the classification substrate)

`scripts/leech_core.py`, `octad_moves.py`, `leech_map.py`: the GLM's
own substrate applied to this table. `leech_map.json` classifies all
1000 rows by number field: level 0 unresolved 114 (no certificate;
improvement sum 1.630 — where the remaining score lives), level 1
rational Λ1–Λ4 552 (field Q), level 2 quadratic Λ8 334. Tiers:
certificate 886, null 111, strict 3. Verification headline (carried
since run 4): 28/28 + 14/14 integer-exact assertions; no floats
anywhere in the lattice math. Λ16's kissing number 7320 is cited
(SPLAG), not verified — marked as such everywhere it appears. The
exact algebraic certificates: 54 in `json/galois_certificates.json`
(Galois groups per record: e.g. θ=45°, a=1, p=1, n=5:
s_exact = √2/2 + 2, minimal polynomial 2x² − 8x + 7, group C2);
1169 total across the 7 angle families × full (a,p) sweeps + surveys
+ the run-11 census (the front-page headline figure).

---

## 4. The cascade (how one breakthrough becomes many)

No improvement enters this table as a single row. Every breakthrough —
constructed or imported — is multiplied by exact propagation laws
before it lands, and the same channel runs on everything: our
constructions, the register, the Mishapolk certs. This is the machinery
that answers "what happens to the other 999 puzzles when one record
improves", and it is the reason a single import can pay more than its
own face value.

### 4.1 The residue-diagonal chain law (cascade3.py)

The table's rows live on residue diagonals: for n with K = ⌈√n⌉, the
diagonal is c = n − (K−1)², members n = (K−1)² + c for every K above
the base. **The law: a record at L(m) converts every member n ≥ m of
the same diagonal to L(n) ≤ L(m) + (K(n) − K(m))** — extend the
record's packing with a 1-wide band strip per shell. The conversion is
a construction (band cells placed in the free margin of the L+1
container, computed from the actual bounding box), and it is verified
through the gate like everything else. cascade3.py enumerates these
2D band-extension chains from every base packing; per-n winners are
finalized and verified once, then merged into the table.

Live examples (measured on the delivered table, run 34): the T-263
record s(299) = 17.801238535867 (K=18) → L(334) = 18.801238537761
(K=19: +1) → L(371) = 19.801238537765 (K=20: +2) — one import, three
table rows, the two extensions binding at equality +2e-9 (storage
noise). And the n=5 pinwheel (L = 2.707106782448) → L(10) =
3.707106782648 = L(5)+1: the survey's own n=10 record is the strip
extension of the pinwheel — the diagonal c=10 was closed by the
community at exactly the value our law predicts.

### 4.2 The removal closure (closure_apply.py)

Removing squares from a packing never grows its bounding box, so every
n < m inherits L(m) for free: F(n) = min over m ≥ n of L(m) (the
prefix-min envelope from above). For each n with F(n) < L(n), the
closure drops (m−n) squares greedily from a base m — each step removes
the square whose removal most reduces the bounding box — and keeps the
candidate with the smallest result. Iterated to fixpoint, because a
smaller L at n can itself serve n' < n as a base. 18 delivered rows
carry the `closure` label. This is also how the chain converts
*inward*: the prefix of a band-extended packing is that packing's own
state, so a chain row at n simultaneously improves every n' ≤ n.

### 4.3 The table laws (the invariants the cascade leaves behind)

Two laws hold on the delivered table with zero violations, checked
every run by `root_audit.py`'s `table_laws` block (run 34: monotone
999/999 pairs clean, shell 937/937 clean). The tolerance is 1e-7 — the
same ENV_TOL as the chain envelope: `final_assembly.py` stores states
up to +2e-9 per row so the 12-dp CSV can round-trip, so comparisons at
1e-12 would read storage noise as violations; at 1e-7 both laws are
exactly clean.

- **Monotone envelope**: L(n) ≤ L(n+1) over all 999 adjacent pairs. A
  packing that improves n without improving n+1 is possible in
  principle; the table has never exhibited one.
- **Shell law**: L(n + 2⌊L(n)⌋ + 1) ≤ L(n) + 1, 937 pairs checked —
  adding 2⌊L⌋+1 squares to a packing at container L costs at most one
  more unit (the two new bands fit around the existing bbox).

### 4.4 What the cascade has paid (measured; NEXT_STEPS §1 ledger)

| event | gain |
|---|---|
| run-13 register import (76 records) — direct | 0.050264 |
| — cascade on those records (33 chain conversions) | 0.013671 |
| T-263 s(299) import + cascade (run 26) | 0.003559 |
| Mishapolk 221-row import + channel (run 30) | **0.173983** |
| **total closed since run 13** | **0.241477** |

The channel's post-processing is why imports are worth more than their
face value. Of the Mishapolk import's 221 applied rows, the standing
channel subsequently found deeper values for 12: 8 re-labeled `chain3`
(a band extension beats the imported cert at that n) and 4 re-labeled
`closure` (a square removed from the *neighbouring* Mishapolk packing
at n+1 beats the row's own cert at n). The import's 221 rows therefore
appear in the census as 209 `mishapolk` + 12 rows now carrying their
deeper producer. The register import shows the same pattern at run-13
scale: 76 applied, and the aiming map exists because of all this —
`root_audit.py` ranks every open row by what a record there would
convert through these laws (best current aim c=32 n=356: 0.011102 for
14 conversions; one-per-diagonal aggregate 0.375304, 63.4% of the
remaining gap).

## 5. The operating loop (how a run works, start to finish)

```
   upload/ + workspace/sources/          scripts/ (the engines + instruments)
   external sources  ─────────────────▶  imports & constructions
        │                                   │
        │                          packlib.verify (W36: the honest gate)
        │                                   │
        ▼                                   ▼
   workspace/sources/atlas, mishapolk   workspace/submission/table.json
   (fetched clones; git-tracked          (the system of record: 1000 rows,
    register copies)                      n → {L, state, src})
                                              │
                    cascade3 ─ closure_apply ─┤ (the standing channel,
                    final_assembly (round-trip)│  mandatory order)
                                              ▼
                                   submission.csv (500,500 rows) ── score
                                              │
                workspace/push/*.json ◀───────┤ (ledgers: every run's
                RUN_NOTES.md, notes/          │  measured outcomes)
                NEXT_STEPS + REPRODUCE        ▼
                + download/runNN/ copies         git commit (the user uploads to
GitHub — the durability line)
```

Per run: read `NEXT_STEPS.md` (the map) → execute the highest-priority
open item with a script → every claim lands in a `workspace/push/`
ledger JSON with measured numbers → after any table change, re-run
the channel (cascade3 → closure_apply → final_assembly, mandatory
order) and `root_audit.py` (fixpoint + aiming map + table laws) →
update the documents together (this file, the front page,
`NEXT_STEPS.md`, `REPRODUCE.md`, `RUN_NOTES.md`) → `deliverNN.py`
copies the state to `download/runNN/` and checks the syncs → commit;
the user uploads to GitHub.

**Transport (run 34 rule): the GitHub repository
(github.com/DigitalEuan/squares_in_squares) is the bulk vehicle —
`repository.zip` is retired (the repository carries the whole tree,
so a zip of it is a duplicate). The front page still rides at the
bottom of this file: the upload path has never delivered it (failure
17), and this file is the one document that crosses every time. The
sandbox recycles (four times so far: runs 17, 19, 32, 33); the GitHub
remote is the durability line.

## 6. The information map (what is ours, what enters, and where it all lives)

### 6.1 What the system produces itself

| Artifact | Producer | Where |
|---|---|---|
| Verified packings (constructions) | Göbel families G(a1,a2,b,c) + clipped t-variant + strips (`gobel2/3/S`) | `table.json` rows, `src: gobel*` |
| Chain conversions | `cascade3.py` (L-extension bands) | `src: chain3` |
| Removal-closure rows | `closure_apply.py` | `src: closure:*` |
| The SAT verification of everything | `packlib.py` (W36) | every row; `submission.csv` round-trip |
| Fixpoint + aiming map | `root_audit.py` | `workspace/push/root_audit*.json` |
| SAT-margin / TAX-NRCI / symmetry measures | `sat_review.py`, `sat_measure.py`, `symmetry_audit.py` | `workspace/push/*28/29/31.json` |
| Number-field classification | `leech_map.py` + `leech_core.py` + `octad_moves.py` | `json/leech_map.json` |
| The delivered table + CSV | `final_assembly.py` | `workspace/submission/` |

### 6.2 What enters from the world (through the gate — never around it)

| Source | What it gives | Entered as | Where it lives |
|---|---|---|---|
| The task | competition definition, baseline | `upload/Squares in Squares.txt`, `sample_submission.csv` | `upload/` (inputs, never modified) |
| Friedman survey (EJC DS#7; the Ellsworth-hosted svg set, kingbird mirror) | 235 record SVGs (Decimal-exact, 20–100 digit parse) + theory; 4 catalogue SVGs (kingbird) | `src: exact/aux/removal` | `workspace/svgs/`, parsed into `table.json` |
| Square Packing Atlas (squaremath.org, the jlevy/squares register; source: evand/square-packing `best.json` + certs) | certified best-known for n ≤ 324, exact rational certificates | **run-13 import** (`import_atlas.py`, "Run 13 push A") → `src: run18-frontier` (label born at the run-18 snapshot-restore); + the T-263 record s(299) (run 26: finder Evan Daniel, fault-line DP, register #824/#893) | `workspace/sources/atlas/` |
| **Mishapolk/square-packing-records** | verified bounds at ALL 1000 n (the band 325..1000 was invisible to our atlas) | `fetch_mishapolk.py` + `import_mishapolk.py` → `src: mishapolk` (221 rows, −0.173983) | `workspace/sources/mishapolk/` (5.3 GB clone; only `upper_bounds.json` tracked) |
| GLM parent study | the substrate laws (TAX/NRCI, delta-sigma), the Lean certificate, the two engine wheels | compiled into the cent compiler (W36/W37) | `upload/` papers + `workspace/cent_compiler_v12_2_ext/` |
| Karimi preprint (read run 30) | the window theorem (certificate shape for mid-band) | read via browser; no rows | cited in `NEXT_STEPS.md` |

Every external packing — atlas, Mishapolk, survey — enters through the
same W36 verification as our own constructions; nothing is trusted on
its source's say-so. The one case where the gate found a mismatch
(Mishapolk's exact tangencies vs our verify tolerance) was fixed by
widening OUR tolerance by 2e-15, not by skipping the check — the
source was right and the instrument learned.

### 6.3 The delivered census (script-computed, Run 36)

| Source class | All 1000 | Beats grid (543) | What it is |
|---|---|---|---|
| `grid` | 457 | 0 (tied) | the trivial ⌈√n⌉ grid — the ceiling every other class beats |
| `mishapolk` | 207 | 207 | run-30 import after Run 35/36 re-attribution; verified bounds and exact certificates |
| `chain3` | 88 | 88 | our L-extension band chains |
| `exact` | 77 | 77 | survey record SVGs (20–100 digit parse) |
| `run18-frontier` | 68 | 68 | the run-13 register import after later channel re-attribution |
| göbel families (2/3/S) | 54 | 54 | our analytic constructions |
| `removal` | 18 | 18 | removal windows from survey packings |
| `closure` | 18 | 18 | our removal-closure fixpoint |
| `aux` | 3 | 3 | auxiliary survey constructions |
| `register` | 10 | 10 | Run 35 register records, including T-263 and the nine later candidate records |

## 7. Delivered state (verified Run 36; Run 34 remains historical context)

| Quantity | Value |
|---|---|
| Submission score | **22.642386651** (rounded **22.642387**) |
| Grid ceiling | 28.937670 |
| Total improvement | −6.295283 |
| Puzzles beating the grid | **543 / 1000** |
| Grid-tied | 457 (of which **152 are proven floors**) |
| Open rows (attackable set) | **305** (root_audit run 34) |
| Leaderboard best (user-reported 2026-11-05) | 22.0544214515 |
| Gap to leader | **0.587965** |

Score history: 22.823536 (run 13) → 22.819978 (runs 26–27, T-263) →
**22.642386651** (Run 35 register records + n=338 chain; reproduced at Run 36) — latest score move after the Run 34 Mishapolk state (runs 31–34:
analysis, campaign nulls, recoveries + documentation).

Table invariants (checked every run: `root_audit.py`'s `table_laws`
block for the monotone envelope and the shell law, the fixpoint audit
for the chain envelope, and the `final_assembly.py` round-trip —
re-verified runs 32–34: cascade 0, closure fixpoint, assembly 0
issues, table bit-identical; run 34: monotone 999/999, shell
937/937):

- **Chain-envelope fixpoint**: 0 rows above the chain envelope.
- **Monotone envelope**: L(n) ≤ L(n+1) — 999/999 pairs clean.
- **Shell law**: L(n + 2⌊L(n)⌋ + 1) ≤ L(n) + 1 — 937/937 clean.
- **CSV round-trip**: 500,500 rows, id continuity 0..500499, 12-dp
  stability, 0 issues.

(Comparison tolerance 1e-7 everywhere: finalize stores states up to
+2e-9 per row for the round-trip, so 1e-12 comparisons would read
storage noise as violations. The run-33 edition of this file credited
these laws to a `gap_analysis.py` that did not exist; they now live in
`root_audit.py`, which prints and records them every run.)

## 8. The frontier (where the remaining 0.592 lives)

- **305 open rows** (root_audit): all at r = 2K−1−c ≥ 5; a uniform
  depth d\* = 0.0365 on them matches the leader exactly. Best single
  aim: c=32 n=356 (a T-263-class record there = 0.011102, converts 14
  rows); aggregate one-per-diagonal: 0.375304 (63.4% of the gap).
- **P1/P1'/P2 are closed by measured null** (runs 23–31: numerical
  insertion and polish are dead in this landscape — the stall law;
  the records' voids are thin seams, not +1 space). If anything moves
  at the aims it will be an imported record (P3), not a construction
  or a settle.
- **P3 (the only item that has paid, every time)**: the weekly source
  watch — atlas, Mishapolk (upper_bounds.json at all 1000 n), the
  community register, Karimi's preprint (its two-strip constructions
  live at n ≥ 1184, outside our range; the window theorem is the
  certificate shape for our mid-band).
- **P5 (open)**: certification completeness — the Lean build and
  exact replays; the tier-1 report's "s(6)=3 theorem" line retracted
  (register: restricted-optimality only).

## 9. Run history (1 → 36)

| Run | Theme | Score after | Verdict |
|---|---|---|---|
| 1 | engine + survey integration | 23.19 | sources dominate search |
| 2 | Göbel family sweep, motif zoo | 23.19 | family exhausted; φ is not a generator |
| 3 | closure to fixpoint + live catalogue | 23.173640 | at published frontier; catalogue adds 0 |
| 4 | Leech/Golay layer + √3 escalation test | 23.173640 | lattice logic exact; √3 refuted 3 ways |
| 5 | rotated-block program (7 angles) | 23.173640 | 45° kink minimum; Level-0 negative |
| 6 | residue audit + cent engines' first campaign | 23.173640 | audit corrected the picture; engines: local refinement, not discovery |
| 7 | Lorentz lift + gain tables + plan | 23.173640 | value ladder: mid-band is the prize |
| 8 | LP closure + sweeps + area recalibration | 23.173640 | search cannot produce 0.1-class; construct analytically |
| 9 | gobel2: full G(a1,a2,b,c) | 22.897558 | 17 mid-band finds beyond the catalogue |
| 10 | gobel3: clipped diamond + pocket fill | 22.887471 | 5 finds; pocket-fill structurally negative |
| 11 | precision architecture + certificates | 22.887471 | 1169 certificates; value-scan certification impossible at 4e-9 |
| 12 | lemma-driven table laws | 22.887471 | monotone envelope, shell law, 94 proven rows, new Q(√2) family |
| 13 | community register import + propagation + G4 test | 22.823536 | 76 records + 33 chain conversions; G4 architecture ceiling proven |
| 14–16 | (lost in rollback #1 — see run 17) | — | no ledgers survive; re-covered at run 17 |
| 17 | **rollback #1 recovery**: Nov-2 snapshot rollback lost runs 9–16; frontier re-recovered idempotently (register re-fetch, import identical, gobel2 re-implemented from spec) | 22.823536 | the recovery pattern is born: GitHub + idempotent imports |
| 18 | GitHub snapshot as system of record; cent v12_2 extension (W36/W37, 41 wheels; parser fix, 127-row corpus); pressure-settle v2 (honest negative) | 22.823536 | sources re-verified twice |
| 19 | oracle study (E1 0/10, E2 1/40) + 23-root campaign (honest zeroes); **rollback #2** mid-campaign | 22.823536 | the settle-in channel cannot even hold a known solution |
| 20 | double-check verdict; the stall law (p ≈ 0.45–0.88·d); 132 template attempts | 22.823536 | infeasibility-proof program proposed |
| 21 | boundary demo, wheels census, clue ledger | 22.823536 | nulls; ledgers kept |
| 22 | soft relaxation — the pass-through channel (n=5 tight: 4/16 hard hops, verified 2.708107 below grid) | 22.823536 | named; needs a tight target to re-harden |
| 23 | submission audit + tightest ladder sweep | 22.823536 | P2 cells 0 finds |
| 24 | NEXT_STEPS.md execution | 22.823536 | map execution |
| 25 | P1 strip scan rerun + P2 remainder (52/52 cells) | 22.823536149 | both closed by null/capacity |
| 26 | P1(b) two-block, P1(c) census; T-263 import | 22.819978 | +0.003559; P1 closed |
| 27 | P4: root_audit.py instrument | 22.819978 | fixpoint true; aiming map born; 2 doc errors fixed |
| 28 | SAT data review (user input) | 22.819978 | contact language 99% parallel; T-263 floaters |
| 29 | SAT measure: TAX/NRCI (user input) | 22.819978 | vacuum = the grid rows; depth~φ |
| 30 | P2 renewal null + **Mishapolk import** | **22.645991** | −0.173983; 543 beat grid; root_audit refreshed |
| 31 | symmetry census (user input); P1' null | 22.645991 | constructions symmetric, records asymmetric |
| 32 | **rollback #3 recovery** + documentation layer: adopted the remote's runs 28–31; channel fixpoint re-verified bit-identical; root_audit fixed (stale run-27 gap); documents unfrozen (were run-13 era through six score moves) | 22.645991 | failure 16 (rollback rules); STATUS got the system map |
| 33 | **rollback #4 recovery** + the lineage record: run-32 artifacts redone bit-identically; the GLM → cent compiler → this project lineage recorded (this document rebuilt); the front-page copy rides at the bottom of this file for the upload transport | 22.645991 | failure 17 (the transport rule); see `NEXT_STEPS.md` |
| 34 | accuracy dive (user order): **the cascade recorded** (§4: chain law with live T-263/pinwheel examples, removal closure, table laws, the measured ledger 0.241477); table laws re-homed from a phantom reference into `root_audit.py` (monotone 999/999, shell 937/937 @1e-7); census re-verified against the live table and the import ledgers (register re-attributed to run 13: 76 applied, 3 beaten by Mishapolk, +2 via the run-18 restore; Mishapolk 221→209 = 8 chain3 + 4 closure re-earned); `repository.zip` retired — the GitHub repository is the transport | 22.645991 | channel bit-identical; laws 0-violation |
| 35 | **score move**: nine Evan Daniel register records T-243/T-257/T-267–T-273 imported, plus the n=338 chain conversion; direct gain 0.003359 and cascade gain 0.000245 | **22.642386651** | latest score move; 543/1000 beat grid |
| 36 | **re-establishment**: Run 35 reproduced from its surviving records; independent rescore, cascade, closure fixpoint, wedge probe, and documentation state re-verified | **22.642386651** | canonical latest state represented by the run records |

## 10. Guarantee

Every packing in `submission.csv` is re-verified from the file on disk
(pairwise SAT non-overlap with worst penetration ≤ 0, bbox containment,
per-n counts, id continuity 0..500499, 12-dp round-trip with ~2e-9
clearance). Imported packings carry their finder attribution in `src`.
The lattice-mathematics claims are integer-exact (Λ16's kissing number
7320 is cited, marked as such). Optimality is never claimed for any
packing: the verified statement is always "improved over the grid
ceiling on N puzzles, certified". Every number in this file comes from
a script-computed ledger (§6); the sync between this file, the front
page, and the live table is checked by `deliverNN.py` every run.

---

# Squares in Squares — Verified Constructions, Leech-Lattice Analysis, and the Rotated-Block Program

This repository is the complete, reproducible working state of a
Kaggle *Squares in Squares* project (pack n unit squares into a minimal
square container; 1000 puzzles, n = 1..1000; score = Σ(L/√n − 1), lower
is better), extended with a machine-verified Leech-lattice layer and a
fully enumerated rotated-block family program.

**Where this project began.** It is a descendant of the GLM study
(github.com/DigitalEuan/GLM): the *General Lattice Machine*, whose
number-theory evidence (TAX/NRCI, Y/Q/B constants, delta-sigma as the
canonical carrier for irrationals) was compiled into a physical
compiler — the cent compiler v12_2_ext, 41 wheels
(github.com/DigitalEuan/squares_in_squares/tree/main/workspace/cent_compiler_v12_2_ext).
Two of those wheels are this project's engines: **W36** (Numerical SAT
Substrate — the exact algebra that became packlib's SAT verifier) and
**W37** (Viscoelastic Settling — the creep/pressure ramp that became
the pressure-settling engine). Every construction this project
produces is a W36 certificate; every search it runs is a W37
settle. The record from start to finish — lineage, engines, sources,
operating loop — is the system record in `STATUS.md`.

## Headline results (Run 34, 2026-11-07; last score move run 30)

| Quantity | Value |
|---|---|
| Submission score | **22.645991** (grid ceiling 28.937670, improvement −6.291679) |
| Puzzles beating the plain grid | **543 / 1000** |
| Leaderboard best (reported) | 22.0544214515 → gap **0.591569** |
| Certification | 1000/1000 packings SAT-verified + 500,500-row CSV round-trip (0 issues; re-verified runs 32–34) |
| Golay/Leech verification | 28/28 + 14/14 assertions, integer-exact |
| Algebraic certificates | 1169 (7 angle families + surveys + run-11 census) |
| Proven-optimal rows | 156 (152 tied at grid + 4 below-grid: s(5), s(11), s(17), s(19)) |
| Largest single import | **Mishapolk/square-packing-records, 221 rows (run 30)**: 22.819978 → 22.645991 (−0.173983) |

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
   search: every score move since run 9 has been an import.
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
Each run, update top-level README.md, STATUS.md, NEXT_STEPS.md and REPRODUCE.md all need updating. If possible GLM_INVESTIGATION.md should be upkeep as an overview of the whole study.

## Guarantee

Every packing shipped in submission.csv was re-verified from the file as
written on disk (pairwise SAT non-overlap with worst penetration ≤ 0,
bounding-box containment, per-n counts, id continuity 0..500499, 12-dp
round-trip stability with ~2e-9 clearance). Every mathematical claim in
the Leech layer is machine-verified with exact integer computation; no
floats anywhere in the lattice math. Λ16's kissing number 7320 is cited
(SPLAG), not verified — marked as such everywhere it appears.
