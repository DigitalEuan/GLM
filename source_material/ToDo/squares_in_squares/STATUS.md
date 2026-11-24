# STATUS.md — Squares in Squares: the system and sources record (Run 70, 2026-11-18)

> **Start here every run: [`DIRECTORS-NOTE.md`](DIRECTORS-NOTE.md)** — the standing perspective: what we are doing, what “no floats” means here, what is already proved (as leverage), the open leads, and the C1–C4 promotion gate. Read it before proposing a route; update it in the same commit if a number changes.

> Run 70 is the canonical latest state represented by the surviving run records. Run 34 remains the historical system-map milestone (§1–§6 are its record and are still accurate); §7 carries the delivered numbers, §8 the frontier, §9/§9.1 the run history through 69, and `19` §12 the theory closure of runs 62–67 followed by the run-68 framing audit (`31`) and the run-69 margin definition and single-row search (`32`) and the run-70 cent-contract audit and T1 branch flip (`33`). No row of the table has changed since the run-47 re-score.

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

## 7. Delivered state (verified Run 52; re-checked at run 67 by `sqscore.guard` — no row changed since; Run 36 and Run 34 remain historical context)

| Quantity | Value |
|---|---|
| Submission score | **22.218056945** (rounded **22.218057**) |
| Grid ceiling | 28.937670 |
| Total improvement | −6.719613 |
| Puzzles beating the grid | **553 / 1000** |
| Grid-tied | 447 (of which **152 are proven floors**) |
| Open rows (attackable set) | **305** (root_audit run 34) |
| Leaderboard best (user-reported 2026-11-05) | 22.0544214515 |
| Gap to leader | **0.163635** |

Score history: 22.823536 (run 13) → 22.819978 (runs 26–27, T-263) →
22.642386651 (runs 35–36) → **22.218056945** (run 47 audit re-score; guarded
at run 52).

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

## 9. Run history (1 → 70)

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
| 35 | **score move** (historical, superseded at run 47): nine Evan Daniel register records T-243/T-257/T-267–T-273 imported, plus the n=338 chain conversion; direct gain 0.003359 and cascade gain 0.000245 | 22.642386651 | 543/1000 beat grid |
| 36 | **re-establishment** (historical): Run 35 reproduced from its surviving records; independent rescore, cascade, closure fixpoint, wedge probe, and documentation state re-verified | 22.642386651 | superseded at run 47 |
| 47 | **audit re-score** (current): the run-36 table re-scored against the corrected extent and the one scorer | **22.218056945** | 553/1000 beat grid; guarded since run 52 |
| 48–51 | audit reconciliation window: the drift inventory that produced `19` §1 (ten documents quoting old totals, `table.json` diverging) | 22.218056945 | no score move; the record itself was the defect |
| 52 | `record_guard.py` implemented; G-1: the r = 1 column in the exact t-basis | 22.218056945 | **falsifier fired** — same t-multiset across the δ step, so the step is arrangement, not vocabulary (`20`) |
| 53 | G-2: both r = 1 atoms rebuilt from integers in ℚ(√2); the seam solved by LP | 22.218056945 | all 12 full-diamond rows return the delivered algebraic side, pinned, penetration 0 (`21`) |
| 54 | G-2b: the "block" re-declared as a five-deep diagonal **strip**; prices corrected per legal start, forward only | 22.218056945 | `now` = 0 for every delivered column; best base-less start 0.058535; 0 gains (`22`) |
| 55 | seed wheels: two-tilt grammar spun at n = 10 | 22.218056945 | 436 cells, 80 certified, 0 gains; best centred = the delivered optimum 3.707106791 (`23`) |
| 56 | optimality battery of published proofs | 22.218056945 | **42 proved rows**, at = 42, above = 0; Karakuş's n = 10 value is 0.51 *below* the optimum (`24`) |
| 57 | open-row literature crosswalk | 22.218056945 | 10 at published, **2 beat published** (n = 28, 29), 0 above (`25`) |
| 58–59 | frontier crosswalk, rule corrected to the catalogue's own words | 22.218056945 | 316 rows resolved, 0 targets; the "56 beats" were not a label offset (`26`) |
| 60 | `parse_tt.py` — the page fetched with `curl`, not the truncating reader | 22.218056945 | 215 cells, 0 unparseable; **the catalogue's scope ends at n = 324** |
| 61 | frontier corrected again: the trivial grid is *not* best-known above 324 | 22.218056945 | 325 determined (246 at, 79 beats), **675 open**, `best_known = null` (`26` §9) |
| 62 | Bui's staircase (arXiv:2508.04603v2) implemented exactly in ℚ, §3.1.1 only | 22.218056945 | 132 cells, **132/132 `packlib.verify`, 0 gains**; density 0.23–0.82 vs ≈0.95 (`27`) |
| 63 | G-3: the expressiveness ladder | 22.218056945 | six rungs, **4 recomputed, 2 quoted**; Λ₂₄ kills coarsening at all eight scales (`28`) |
| 64 | the SAT/disjunctive model assessed as a decision procedure | 22.218056945 | 0.76 % of pairs tight at n = 1000 → 1e300729 leaves; decisive only with the disjunction fixed (`19` §11) |
| 65 | §11.5 bounded probe (18 cells) | 22.218056945 | 0 feasible — but circular free set + a broken LP; **withdrawn** (`29` Part A + erratum) |
| 66 | resolution/dithering probe | 22.218056945 | the answers are invalid at **every** m including 128; dithering has no admissible residual (`29` Part B) |
| 67 | §11.5 probe with an **earned** free set | 22.218056945 | core unspans only at k = 161/184/267/298 (55–100 %); the LP refuses at every k to **k = n**, which is a certificate: the delivered side is the exact optimum of the declared-axis, fixed-orientation LP (`30`) |
| 68 | algebraic-word framing, audited (`31`) | 22.218056945 | three closures confirmed (run 5: 280 certificates / 0 conversions; run 52: same `{axis, π/4}` alphabet across 0.520815; run 55: 436 cells / 80 certified / 0 gains); four figures corrected — 45° carries 43.2 % of gain and 23.2 % of beats (not 70 %), no `0.67k + 4` law, the three "thinnest margin" rows are at the grid (gain 0, `r = 12/20/22`), `s(k²−5) = k` external and reported (T-298) with 25/25 contact rows at grid |
| 69 | wall margin, and one row's branch-rotation search (`32`) | 22.218056945 | `mu = L − sqrt(n)` defined, priced `rho = mu/sqrt(n)`, computed on all 1000 rows: 184/656/819 are mid-table (mu ranks 517/604/610, rho ranks 159/637/702; median 0.441761/0.017494) and the thinnest margins are the proved perfect squares; fixed rule selects n = 18 (rho 0.136763, rank 8), where 3,940 declared + 1,620 re-slot + 1,171 settled cells give **0 feasible, 0 gate-accepted, 0 gains**; controls: rigidity 3.1e−8, loose 4-square shrinks and gates, n = 12 refused; s(11) proved/open contradiction recorded, not resolved |
| 70 | cent-compiler contract audited; T1 SAT-branch flip implemented (`33`) | 22.218056945 | branch flip (`u_i`/`v_i`/`u_j`/`v_j` per tight pair, then LP contraction) run exhaustively: n = 18/20/30 give 1,071 + 4,572 + 2,160 = **7,803 cells, 0 feasible, 0 gated, 0 gains**; base cell refused at 1e−2 (rigidity 3.1e−8); controls pass (loose 4 → 2.19 gated; forced branch feasible at 2.001, refused at 1.5); card figures corrected — 0.76 % only at n = 1000 (16.99/28.95/20.46 % at 18/20/30), `s(5) = 2+√2/2` proved so the n = 5 test is ill-posed, "0/8" is run 41, "run 50" absent |
| 71 | the queued card action: one branch flip plus free-set expansion, seeded by the wall-margin ranking (`34`) | 22.218056945 | all 42 open rows at n = 4–60 searched in wall-margin order: 2,228 contact edges, **6,684 single flips**, base depth 0 at every row, **0 seeds** so the free-set ladder was never entered — 0 cells, 0 gated, 0 gains; exhaustive over the declared ladder by two monotonicities (feasibility rises with the free set, falls with `eps`), so expansion cannot rescue a flip that all-free refuses; probes: 1e−7 gives 0 seeds, 1e−8 gives 20 seeds / 400 cells / **0 gated** (the LP's own scale, and the gate refuses); census: every row 4–120 has more binding constraints than `2n` variables (least over-determined is n = 5, +2; n = 18, +4); controls fire both ways (loose 2×2 at 2.2: depth 1e−2, one flipped branch seeds and gates; two squares at their optimum 2.0: base and every flip refused) |

### 9.1 The theory closure (runs 62–67) — what it decided

Run 36's map ended with the frontier open. Runs 62–67 did not search; they **priced
the nominated routes and closed them on measurement**, and the single most useful
thing they produced is a set of exact "no" statements:

* **Coarsening is dead.** Twice, independently: the Λ₂₄ predicate at eight scales
  (tilted rows illegal 87/87 at every scale, untilted legal 168/168 somewhere), and
  snapping ten *delivered answers* to a `1/m` lattice (invalid at every m including
  128, because at an optimum contacts have penetration exactly 0 — equalities have
  no neighbourhood).
* **A neighbourhood cannot lower a side.** With the delivered axis assignment and
  θ frozen, freeing the extremes and their tight-pair partners raises k to 55–100 %
  before the frozen core even stops spanning, and the LP then refuses at every k up
  to and including k = n.
* **k = n is a certificate.** Feasible at L₀, infeasible at L₀ − 1e−6, all
  translations free: the delivered side is the exact optimum of the declared-axis,
  fixed-orientation LP — `lp_seam`'s statement extended from one seam to a whole row.
* **The residue is the branch assignment.** 0.76 % of pairs are tight; each has ≥ 2
  admissible resolving axes; nothing in the score ranks the branches (`L1`). That,
  plus rotation (`L5`), is the only object the material still points at.

Recorded defect of the session, kept rather than tidied: the probe behind run 65 was
wrong three times over (circular free set, then `i`/`j`/inequality errors, then
`h_i + h_j` instead of `0.5 + Eu[owner, other]`). One invariant would have caught all
of it — *the delivered state must be feasible at its own side* — and it is now
permanent: `python3 scripts/sat_probe.py --selftest` → 6/6.

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

## Current results (Run 101, 2026-11-22; last score move run 47)

| Quantity | Value |
|---|---|
| Submission score | **22.218056945** (rounded **22.218057**; grid ceiling 28.937670, improvement −6.719613) |
| Puzzles beating the plain grid | **553 / 1000** |
| Leaderboard best (reported) | 22.0544214515 → gap **0.163635** |
| Certification | 1000/1000 packings SAT-verified + 500,500-row CSV round-trip (0 issues; Run 36 record) |
| Golay/Leech verification | 28/28 + 14/14 assertions, integer-exact |
| Algebraic certificates | 1169 (7 angle families + surveys + run-11 census) |
| Proven-optimal rows | 156 (152 tied at grid + 4 below-grid: s(5), s(11), s(17), s(19)) |
| Latest score move | **Run 47 audit re-score**: 22.642386651 → **22.218056945** (−0.424330); guarded by `sqscore.guard` |
| Latest session | **Runs 69–76, margin + three discrete searches + the dimension by proof + the branch space at frozen angles + the near-miss spent, the seam offset measured, and the row census** — wall margin on 1000 rows; 5,560 word cells at n = 18; 7,803 branch-flip cells; 6,684 flips over the 42 open rows (0 seeds); cubes-in-a-cube LP with an exact rational gate, then `L_d(n) = ⌈n^{1/d}⌉` **in the axis-parallel class** by a sub-box count (2D n = 5 already beats it by rotation: 2.707107 < 3); a 2D branch-space MILP with our own LP-guided B&B — its relaxation is empty at the root (the bound is the largest square's own extent), so it closes only n ≤ 3, while the same exact leaf closed **87,767 structures within two branch changes for 0 improvements** (nearest competitor +4.48e−3 at n = 11 — run 75 identifies it as the single flip of pair 7–8, certified at +4.475e−3, a dead end as a construction, and fixes the gate call that could never have reported a gain); `--milp` retired; W1 started: the n = 290 two-lattice seam's offset measures `18 − (25/2)√2` in x−y and a shift costs exactly the shift, so the seam is tight; run 76's row census splits the 447 grid rows into 60 settled by a published bound (26 of them above n = 324) and 387 open, 247 of those above 324 in one residue band (m ≥ 21), and certifies the delivered side as the frozen-angle optimum on all 87 beating rows with n ≤ 200; **no row changed**; the 553 beats are exactly the rows containing a rotated square (447 axis-aligned rows, all at `⌈√n⌉`); run 77 finishes the frozen-angle certificate — **150 of 150** beating rows at n ≤ 324 (the whole catalogue block, not a slice) and **41 of 41** in 325 ≤ n ≤ 400, union **191 of 191** — folds it into the one row ledger (60 closed by a published bound, 191 certified, 362 beat-open, 387 grid-open) and shows the gap accounting cannot attribute the 0.163635 gap (conceivable total 22.028443, 135×); run 78 aims a construction at the band — the 247 open rows above 324, contiguous in the residue one block per k, each block starting one past that k's last record — by extending each record by one square at six orientations: **0 of 14**, the best placement overlapping by 0.094–0.142 (largest empty square 0.86–0.91, and 70 local LPs infeasible), so no band row is one square from the records we hold; and gives every row its exact algebraic side (447 in ℚ, all exactly `⌈√n⌉`; 100 in ℚ(√2); 4 Pythagorean; 449 recorded as not expressible), with 0 disagreements against the scorer; run 79 builds the tilted boundary layer from scratch for the first open row of each of the 14 k-blocks — a trimmed axis grid plus two `j×j` 45° lattice blocks, certified through `finalize` then the exact gate — and gets **0 of 14** with capacity **m ≤ 0** at every k (the best gated build is the plain `k×k` grid at side k; one diamond nets `k²−2`; at the n=326 record's own side the clean build carries 290 against the grid's 324 and the polished record's 326, so the diamond trade is negative by area and only polishing recovers it — the 54 clean records top out at m = 13, the band starts at 21); run 80 asks whether any solve we hold refines further and gets **0 of 553** — every beating row refuses a wall-ring shrink even at 1e-7 with up to 200 squares free, the 191 rows certified at 1e-6 included — and finds the table is a **60-parameter object**: 969 of 969 non-square rows sit exactly at their residue class's causal chain value (0 open above `finalize`'s 2e-9), so `d(total)/dδ*(r) = W(r)` (3.6453 for r=1 over 31 rows), the cascade channel is already applied everywhere, and the 23 classes still at δ = 1 are the band's residues; run 81 asks the reverse question of the band — the **space around** each of the 14 anchor records, the largest empty square over all orientations in closed form (SAT), three boxes, 17 orientations: **0.695–0.807 of a unit**, always at 0°, falling to 0.569–0.632 at 45°, so the deficit to one more unit square is 0.19–0.31 and tilt *loses* 0.12–0.18 of side — the free space is rectangular and the bottleneck is interior (box placement moves it by ≤ 0.003); 0 of 42 states gate, and the run also corrects run 78's `1 − margin` reading (a tilted candidate needs `0.5k + 0.5` on the packed square's axes, so 0.86–0.91 was an over-estimate, while its optimistic scan still found no placement); run 82 turns those numbers into certified intervals — `s <= 2 max clearance` (disk) and `s <= sqrt 2 M(0)` (inscription), each proved by branch and bound, with the axis-aligned maximum `M(0)` certified to **1e-4** at every anchor — giving achieved 0.695–0.807 against certified upper 0.788–0.886, a **gap of 0.071–0.098 per anchor**, and the largest upper side 0.8869 < 1 is a **proof that no unit square fits at any orientation** (margin ≥ 0.113); and sub-block seeding (`b x b`, same budget) measures the initial placing's effect — a single coarse grid loses 0.13 on the sharpest pockets, decomposition recovers all of them and **corrects k = 29 from 0.71218 to 0.736113** (verified, certificate recomputed, deficit 0.288 → 0.264), at the cost of a 2e-4 block-boundary loss at k = 23; run 83 lifts the verification alphabet one step to ℚ(√2) — exact `a+b√2` arithmetic and a gate with no tolerance, in which the 0° and 45° words are both first-class — and certifies seven mixed sentences at the tight side of their families, including the **four-corner glue at `2 + 1/2√2 = 2.707107` (five squares against the grid's 3)** and the rational `t=1/2` word at `19/7`; the seam law `L = 2 + 1/(cos+sin) >= 2 + 1/√2` (equality only at 45°, exactly) makes every rational tilt's cost explicit — `5/7 - 1/2√2` at `t=1/2`, `13/17 - 1/2√2` at `t=1/5` — and the minimal bridge is one tilted square coupling four 0° squares at once, while a diamond can bridge a seam but not replace a square (the 3×3 ring needs `2+√2`); a ΔΣ carrier across the seam converges like `1/N` and never reproduces the sentence (1 of 5 rungs legal, and only at a side larger by 1.9e-8); the fields swap order between N=2 and N=5 by an exact inequality; and 447 delivered rows are exactly the 0° word while **451 use no word at all**; run 84 lifts the 100 decimal-shadow rows into exact ℚ(√2) sentences with a float-free reconstructor — **97 of 100** at gate clearance exactly 0, 127,837 certified contacts over 37,260 squares, all 97 sides irrational, the other 3 (n = 51, 126, 295) not small-height sentences at all — replaces the float-fed ΔΣ with a carrier whose accumulator is a field element (legality is the sign of its error; for the whole-sentence Pell map the side excess is exactly `(r − √2)/2`, so legality is proved for every rational rung), and closes the seam family in closed form `L(k,m) = 2k + m√2/2`, `N = 4k² + m`, `V = 2km√2 + m²/2 − m`, `gain = 1 − m√2/2` (54/54 certified for k = 2..10, m = 1..6, refused 1e-9 below; gain > 0 only at m = 1, where the strip is a strict win over the odd grid at every k, though the delivered rows at those n already dominate it); run 85 extracts the ring logic into a domain-neutral exact tower (`exact_field`: Z, Q, Q(√d) for arbitrary square-free d, rational t-points, exact order/floor/ceil, **145 decision functions audited in bytecode with 0 naming float**, and the audit itself tested against a planted offender) and lifts the declared-law wheel out of packing into `glm_wheels` — any domain registers an alphabet, five syntax slots (`Tile`/`Frame`/`Strip`/`Glue`/`SymmetryFold`) with closed-form laws, and a **four-witness** suite (exact gate + topology + conservation + independent 70-digit Decimal); two domains run on it unchanged, 35 cells / 31 certified, with real refusals by law — `strip_needs_diamond` for `S(k,0)` and `not_sturmian` (`p(2) = 2 ≠ 3`) for a rational slope — the coboundary law corrected to its seam-aware form, and the packing wheel covering grids, pockets, strips, rational-t glues, the diagonal fold and the atoms n = 5, 10, 40; **all 447 pure-Q rows certified at clearance exactly 0 with side ⌈√n⌉** (419,281 exact contacts over 205,282 squares; 136 rows by the exact gate, 311 by an exact lattice lemma the gate agrees with), the exact 2D feasible cage replacing the per-coordinate height fallback, and a correction to run 84 that the "3 float artefacts" were 2 search gaps + 1 square: the mixed lift is **99/100** (n = 51 = `16/3 + 5/3√2`, n = 295 = `22/3 + 22/3√2`, both at clearance 0), with only n = 126's square 120 off-lattice; run 86 registers a **third, structurally distinct domain** on the same engine — integer and quadratic lattice shells (`Z^d`, `D4`, `E8`) held in doubled coordinates so every norm, inner product and theta coefficient is an exact integer sum — with exact-norm, kissing-topology, theta-conservation and 70-digit Decimal witnesses plus two declared refusal laws (`empty_shell`, `rank_budget`): **24 of 28 cells certified**, from theta series *computed by enumeration* (D4 1,0,24,0,24,0,96; E8 1,0,240,0,2160; kissing 4/24/240; root degrees 8/56) and `theta(A (+) B) = theta(A)·theta(B)` verified cell by cell, with the engine's four friction points named (a real double-import bug, a packing-shaped row schema, a witness that had to be re-implemented, and four-witness scoping that is per family); an exhaustive translation-and-reflection induction over **45 lifted states and 13 templates** finds **1 exact decomposition in 45** (n = 5, the pocket we already had) and proves every atom is irreducible over the declared families while `Tile1` covers exactly its axis squares (n = 10 → 8/10, n = 40 → 24/40, mean 0.7324), pinpointing the missing diamond-placement primitive; n = 126's last square turns out to have a **rank-1** contact algebra (`y − x = 11/2 + 5/2√2`, satisfied to 1.5e-9) whose exact feasible segment is `x ∈ [1.3357864, 1.3713203]` — empty of field points at tolerance 1e-4, yet containing **173** Q(√2) placements at clearance 0 (nearest `x = 43/32`, 8.2e-3 away) — so the pose is off-lattice while its topology is not: **99/100 pose lifts, 100/100 topology realisations**, with square 98 newly recovered as `(5 − 2√2, 19/2)`; and all **1,000 rows now carry an exact field class** — 447 grid, 99 Q(√2) pose, 18 Q(√2) side, 5 Q(√7) side, 3 Q(√5) side, 4 rational-t (denominators ≤ 7), 424 continuous — from 70-digit Decimal trig, continued-fraction Pythagorean tests and exact `recover_scalar`; ; run 87 keeps the promise doc 49 deferred — the engine contract becomes domain-neutral: `Wheel.spin` writes **size / measure / invariant** and a witness count instead of the packing-shaped `n / extent / gain` (`Claim.n` survives as a read-only alias, so no builder changed), witness suites are declared per family (`Witness.families`) and filtered through one `Domain.suite(claim)`, and a single `DecimalWitness` takes a per-domain `scalar` (a `Quad` of any `d`, a `Fraction`, an `int`, a `Decimal`) in place of the packing-only one — so spatial packings, Sturmian sequences and lattice shells print in **one uniform table** (28/31, 6/7, 24/28 certified; 17 controls, `w` = 4 or 3 per row); n = 126's rank-1 probe is promoted to `qsqrt2.cage_segment(...)`, a permanent mode that derives the rank, the law, the exact segment `x ∈ [1.3357864, 1.3713203]` (width 0.0355339) and the Q(√2) enumeration from the state alone — no typed bounds, no monkeypatching — and control 11 reproduces run 86's **173** while proving that number **too generous**: it counted candidates whose *rational part* lay in the band with the x-containment test skipped, so the corrected cage holds **4** placements at clearance 0, nearest still `x = 43/32` (8.2e-3), and n = 126's verdict stands as off-lattice pose with on-lattice topology; and the diamond primitive arrives as `DiamondField` — a declarative `cells` + `slots` spec over Q(√2) whose insertion rule drops colliding axis cells and *derives* L, the void and the contact graph — passing the induction acceptance test **3/3 exact**: n = 10 (8 axis + 2 diamonds, 8 of 16 dropped, `L = 3 + 1/2√2`), n = 19 (11 + 8, `L = 3 + 4/3√2`) and n = 40 (24 + 16, `L = 4 + 2√2`), each identical to its Atom cell with L reproduced and 10/10, 19/19, 40/40 covered, registered as three certified spatial cells, with n = 19 and n = 40 honestly declaring explicit axis cells because those sets are not product grids; ; run 88 closes doc 50's two limits and finds they were one — the strip is a field of (k, m): `strip_field(k, m)` declares two k-runs per axis across a seam of width `m√2/2` plus m anti-diagonal slots, so `S(k,0)` stops being refused as `strip_needs_diamond` and certifies as the plain 2k grid with **gain 0** (identical to `Tile 2k`, pinned by control 19), and the **spatial wheel is 31/31 certified, 0 refused**; and run 87's claim that n = 19 and n = 40 "are not product grids" turns out to be false — tested against their slot lists both are exactly a product minus collisions (`n19`: `{1/2,3/2} ∪ {1/2+a,3/2+a,5/2+a}` × `{1/2,3/2,5/2} ∪ {3/2+a,5/2+a}`, `a = 4/3√2`, carrier 25 → 11 cells; `n40`: `{1/2,3/2,5/2} ∪ {3/2+2√2,5/2+2√2,7/2+2√2}` squared, 36 → 24), so a field is now two short run lists plus its slots — `(start, step, count)` in Q(√2), product of the two skeletons, with run 87's "bent grid" as the two-run case and no cell lists left anywhere; the drop counts move in the honest direction (n19 0 → 14, n40 0 → 12) because the carriers are full products and the insertion rule does the trimming, while N, L, void and contacts are identical to run 87 and control 18 compares the generated cells against the run-87 census one by one (8/11/24, all equal) and fails if a field ever needs more than two runs per axis; control 5 changed with the finding — "the wheel must have at least one refused cell" is no longer true, so it now asserts the opposite and exercises every refusal law (`degenerate_cell`, `negative_seam`, `unknown_field`, `no_diamond`, `declaration_overlaps`) on constructed cells while the other wheels still refuse by `not_sturmian`, `empty_shell` and `rank_budget` — **19 controls**, **177 audited functions, 0 offenders**; ; run 89 pays two small debts of the same kind — a code path and a number that said something no longer true: `p_pocket(k)` is rewired through `strip_field(k, 1)`, so strips and pockets share one assembly (the pocket is S(k,1); run 84's sentence is now only the cross-check) with identical state, words, L and N = 4k² + 1 and its own family, the wheel's Pocket rows unchanged and spatial still **31/31**; and the dead `checks` counter in `glm_wheels`' selftest is gone — each control announces itself through one helper and the summary is `len(announced)`, so the count is the number of controls that ran rather than a literal (run 88 had already broken it), and `--selftest` now exits 0 instead of returning the count as its status; **19 controls**, **177 audited functions, 0 offenders**; ; run 90 finishes what run 89 started and opens the algebraic rungs — the Strip's seam law is shared by the Pocket so their claims differ only in family and parameters, and a genuinely malformed declaration is now refused three ways by `declaration_overlaps` (two coincident slots and two slots 1/10 apart, both caught by the gate since the insertion rule cannot see slot-slot overlap, plus a slot over an axis cell with the rule off); the strip's seam width turns out to be a *derived* quantity — the binding contact conditions give `w* = min(1/(c+s), c+s)` and **`L = 2k + w*`** at clearance exactly 0, whose 45° member is `S(k,1)` cell for cell — so the ridge extends the wheel to three new algebraic rungs, each certified by all four witnesses: `Slope` 2:1 in Q(√5) at `2k + ⅓√5`, `Seventh` with the word `(√7/4, 3/4)` in Q(√7) at `2k + 6 − 2√7`, and `Tilt` t = 1/2 at `2k + 5/7`, nine cells in all, taking the spatial wheel to **40/40 certified, 0 refused**; verification is one procedure over any field — `qgate(cls, …)` is a port of `qsqrt2.gate` over any `Quad(d)`, the gate/contact/conservation/Decimal witnesses read the claim's field and `_tag` rebuilds the grid side there, with control 21 proving the port agrees with the original exactly on the three atoms; calibration against the table is exact and negative — at n = 5 the side `2 + ½√2` beats every rung by 1.39e−3 (Seventh), 7.18e−3 (Tilt) and 3.83e−2 (Slope), and n = 17/37 are recorded as **uncalibrated** because those delivered rows carry an orientation outside the axis/45° alphabet and do not lift, so nothing here is claimed as a win; **21 controls**, **197 audited functions, 0 offenders**; ; run 91 removes the second decision procedure run 90 had introduced — `qsqrt2`'s gate is parametrised by its field class (`cls`, defaulted by `field_of` from the first coordinate, with every constant built from it) so `Q.gate(state, words)` is unchanged for every existing caller while a Q(√5)/Q(√7) sentence is decided by the same code, and `glm_wheels` loses `qgate`, `qpairs`, `qside`, `qframe_extent` and `qaxis_extent` plus the unused run-90 helpers `field_class` and `sqrt_in`; control 21 is widened from three sentences to **all 40 spatial cells**, checking that the inferred and declared field classes give identical ok/L/clearance/contacts/violations, that the witness path `gate_of` equals both, and that for **every pair** the axis vectors and slack signs from `Q.pair_axes` and `pairs_of` agree — with the ridge assertions kept (45° = `S(k,1)` cell for cell, every rung at clearance 0 with its exact side); the float audit drops from 197 to **191** functions, still **0 offenders**; **21 controls**, spatial still **40/40**, no number moved; records `31`–`54`; run 92 lets the ridge hold **m** tilted squares — the bar is edge to edge along
`−v = (s, −c)` and each block-slot slack is linear in the seam width (`d·q = P + Q w`,
`need = 1/2 + (|c|+|s|)/2` on every axis), so `w*(m)` is the smallest closed-form root at
which the exact gate passes, with `N = 4k² + m`, the 45° member equal to `strip_field(k, m)`
cell for cell, slot for slot and side for side on all nine `(k, m)` for `k, m = 1..3`
(`L = 2k + m√2/2`), the single-seed member still `min(1/(c+s), c+s)`, and the exact law
`w*(2) = 2w*(1)` on all four rungs while past `m = 2` the binding pair re-binds (45° stays
linear through `m = 4`; the Q(√7) rung's `m = 3` is smaller, `−1/2 + √7`, as the bar's end
slips into the corner void) — and it also corrects run 90's Q(√7) word: the census's n = 18
tilt recovers at 70 digits to `cos = 1/4 + 1/4√7`, `sin = −1/4 + 1/4√7` on the unit circle,
so `_sqrt7_word` is the table's own word and that rung's side is `2k + 2/7√7`, while the
honest answer on whether any `(k, m)` reaches `7/2 + √7/2` is **no** — `N = 18` forces
`(2, 2)`, where the rungs give `4 + √2`, `4 + 2/3√5`, `4 + 4/7√7` and `38/7`, none at the
needed `(√7 − 1)/2` seam, and the row itself is 10 axis squares on `±(5/4 + √7/4)²` plus 8
tilted, i.e. `L = 3 + 2cos`: an odd rational part with a cosine term where the ridge is an
even `2k` plus a seam, so it is a ring sentence rather than a near miss; **22 controls**,
spatial **46/46** certified, float audit **195 functions, 0 offenders**, no row changed;
records `31`–`55`; run 93 reads the whole Q(√7) slice of the census — five rows (n = 18, 53, 151,
234, 747), each re-derived from its own pose at 70 digits — and finds one shared word,
`((1+√7)/4, (√7−1)/4)`, unit-checked exactly in every one, with the single side law
`L = 2k + 3/2 + (c + s)` (`ring_side`), which at `k = 1` is exactly `7/2 + √7/2` and so
contains run 92's `3 + 2cos` as a special case; solving it per row splits the family by the
**parity of k** — integer for two rows (18: k = 1, 151: k = 5), half-integer for three
(53: 5/2, 234: 13/2, 747: 25/2) — while the alphabets differ widely (1, 3, 2, 1 and 663
distinct tilt angles, with 8, 6, 24, 36 and 2 squares at the word); and it builds the Ring
family in `glm_wheels` — `ring_side`, `ring_frame`, `ring_candidates`, `ring_field`,
`p_ring`, field-general, with the exact gate as arbiter — which **refuses** at every tried
`(k, word)` (Q(√7) and 45°, k = 1, 2) under the declared law `ring_unresolved`, because the
census's own ring is 10 boundary axis squares plus 4 tilted in the edge gaps plus a central
pinwheel rather than four corner modules, and its recorded pose carries 0.03–0.07 of slack
between module and frame — a polished decimal packing, not an exact contact sentence — so
no Ring cell is registered and **n = 18 is not yet constructed from grammar**, the coupled
gap/pinwheel tangency being named as the next job; **23 controls**, spatial **46/46**,
float audit **200 functions, 0 offenders**, no row changed; run 94 rebuilds the Ring from the census's own sentence and certifies it — the n = 18 pose is not a corner-module ansatz and is not slack: it is a C2 perimeter of 10 axis squares (4 corners at `±(k + c)`, a 3-square run up the left wall, a run down the right wall, one square inward on each horizontal wall), **4 gap squares** each wedged across a wall gap, and **4 pinwheel squares** — every one of the eight tilted a 2×2 exact solve in Q(√7) from two declared tangencies (`|(q − p)·u| = 1/2 + (|c| + |s|)/2` against an axis square, `= 1` against a tilted one on `v`), so with **22 declared tangencies, all exact contacts, and 14 flush wall faces** the exact gate certifies **N = 18 at `L = 7/2 + ½√7` with clearance 0, 26 contacts and 0 violations**, the `Ring k=1` cell is registered and the spatial wheel is **47/47 certified**, and the constructed sentence reproduces the delivered n = 18 row to **1.8e-9** (the CSV's own shim scale) — so n = 18 *is* now constructed from grammar, and run 93's "0.03–0.07 of slack" was read off the wrong sentence; and the grammar is shown not to generalise: the pinwheel's closure contact has `u`-separation exactly 1 at every `k` while its `v`-offset is `2·p5·v + 2 = 5/4 − (4k − 1)/4·√7` = −0.734313 at `k = 1` (the contact exists) and −3.380065, −6.025816, −11.317319 at `k = 2, 3, 5` (exact closure slack `−13/4 + (4k − 1)/4·√7`, growing by √7 per `k`), so `k ≥ 2` refuses under the declared law `ring_chain_adrift` — a tangency that is measured and is not one — and the census's own `k = 5` row is not this family's member even in count: the ring would have `N = 4k + 14 = 34` at the census's own side `23/2 + ½√7`, while n = 151 is a 151-square staircase (125 axis squares in 21 staggered columns at `±(j + c)` and `±(j + 1/2 − s)` plus 26 tilted, 24 at the word) — the side law generalises across all five Q(√7) rows, the sentence splits at `k = 1`; **24 controls**, spatial **47/47**, float audit **207 functions, 0 offenders**, no row changed; run 95 closes both questions run 94 left — (i) the ring's `k ≥ 2` refusal is *structural*, not a collision: at `k = 3, 4, 5` the drifted sentence still passes the exact gate at clearance 0 with 0 violations and fails only its declared tangencies (8 of 22, 4 the pinwheel closure, slack `−13/4 + (4k − 1)/4√7`), while only at `k = 2` does the drift also collide (clearance `−21/4 + 7/4√7` ≈ −0.620), so refusal and collision are now separated by measurement; (ii) the n = 151 row is a **multi-layer staircase** and its axis layer is grammar — an odd integer grid realised on two lattices offset by `2c` (block `A`: `(a − c, b + c)` for `a < b` = 55 squares; block `B`: `(a + c, b − c)` for `a ≥ b` = 66; four corner caps) plus a two-layer brick wall of word-aligned squares in the diagonal seam, each brick tangent along its own `v` to `B(a, a)` or `A(a, a + 1)`, walking `a = −k … k − 2` with the column repeated when `a % 3 == 0` — so the exact gate certifies **N = 149 at `L = 23/2 + ½√7` with clearance 0** (449 contacts, all 24 declarations exact; `Staircase k=5` registered, spatial **48/48**), the 149 centres matching the delivered row to 9.0e−8; the wall closes only at `c − s = 1/2` (control 5 refuses the 45° word by `staircase_layer_gap`), and the last two squares of the row cannot be word-aligned: the wall's thirteenth column pinches the top-right cap by exactly `−163/128 + 61/128√7` (−0.012572), sliding only trades one pinch for another, and the table instead rotates those two squares to 0.6147618 rad, whose cos/sin is not a unit word of Q(√7) at height ≤ 4096 and not Pythagorean — so **n = 151 is refused by an exact law**, the family constructs 149 of the 151 with `N(k) = 4k² + 4k + 5 + 2|columns(k)|` , the corner pocket is decided by an **exact cage**, with no scan and no tolerance (24 exact boxes at side 1/8 spanning `5/8` in `u` and `3/4` in `v` — both below 1, so the word-aligned capacity is exactly 1), the one square it admits is the **cap brick** (`u + 12`, `v = (17 + √7)/8`, exactly tangent along `u`), so the ceiling is a certified **150 at the same side, clearance 0**, and the cage is then empty even for the census word; the closure law is one line — `v_A − v_B − 1 = 2c(c+s) − (1+s) − 1 = s(2(c−s) − 1)` — so a **62-word spin** (Q(√2), Q(√5), Q(√7), rational-t) closes at the census word alone and refuses every other rung by `staircase_layer_gap` with its own exact residual, the 151st square is refused by an **exact empty cage for 78 of 78 field-compatible second words** (every unit word of Q(√7) at height ≤ 8, every Pythagorean word with denominator ≤ 13), a `k = 1..9` calibration spin never beats a delivered row (`k = 1` behind by 0.8229, `k = 3` and `k = 5` by 0.1158, `k = 6` by 0.0447, exact in `Decimal`), and it does not beat the table at n = 149 (table side `12 + ½√2`); the corner pocket is decided by an exact cage, not a scan — capacity exactly 1 (cover `5/8` × `3/4`), the cap brick certifies **N = 150** at the same side, and the cage is empty against it — and the 78-word sweep runs as **66 rotation-class cages** (a quarter turn cannot change a cage's answer) with a rational pre-filter that only skips cells which cannot cover the box: the sweep 40.0 s → 19.5 s, no verdict moved; the table's own `19211307153/31250000000` rad rotation, rounded up at `1e−25` into Q(√7), closes a certified **150** as well, and the 151st is **excluded exactly** (along `u` the single cage's cover is `3/4` wide — free span `0.447289`; along `v` `staircase_chords`: the **union** of the 16 blocks' free sets spans `0.624681 < 1`, the largest single block's chord being `0.558490`, which alone would not cover a pair split across blocks — a finite exact proof in Q(√7), no scan; the `(2, 1)` rectangle cage is *not* used, since it rules out only the tangent pair; the census word's rectangle cage is empty too); replaying the delivered pair against the exact 149 overlaps by **−2.365e−9** — so the table's n = 151 is a 12-dp pose at `1e−9` tolerance, not a sentence; **27 controls**, float audit of the new functions clean (241 functions, 0 offenders), no row changed; records `31`–`58`; run 96 makes the chord check sound and uniform — the pair proof now reads the **union** of the 16 blocks' free `v`-sets (`0.624681 < 1`, not the per-block `0.558490`), and the same two instruments run over the census word plus **all 66 rotation classes** of the 78 field-compatible words (`--chord-spin`, 2 m 02 s, outside the suite): **66 of 66 place one square, 66 of 66 place no pair**, free spans `0.428760–0.780198` (`u`) and `0.440099–0.822876` (`v`); and it answers the score question honestly — `family_spin.py` spins **364 exact members** (Ridge, Strip, Diamond, Ring, Staircase over Q(√2), Q(√5), Q(√7) and three rational-t words) against the delivered row at the same `N`, the table's side recomputed from its 12-dp pose at 70 digits: **0 beat the table, 6 are at parity** (the atoms `n = 5, 10, 18, 19, 40`, agreeing to 1.3–1.7e−9), **358 are behind** and the shortfall grows (closest the Seventh at `n = 5` by `0.001391`; the 45° rung at `N = 901` is `30.70711` against `30.52082`, so splicing it in would **raise** the total by `0.0062`), and `--gate-ks 1,2,3,15` gates **88 of the 364** sides — the whole `k = 15` column included, **3252 contacts** at `m = 1`, every one clearance 0 with `gate_L == L` — so the calibration is feasible as well as exact; because every family is single-word with `L = 2k + w`, `w = m min(1/(c+s), c+s) >= ½√2` (minimum at `x = c + s = 1`), while the delivered rows sit at `2k + O(1/k)` — the table explains 576 of 1000 sides and constructs 6 of them, and the other **424 rows carry no field class at all**; above 1000 the ridge is exact and zero-drift — `N = 1025` at `L = 32 + ½√2` (void `−½ + 32√2`, 3724 contacts, 0.293 inside the grid's 33), `N = 1937` at `44 + ½√2` (7228 contacts), the seven words at `N = 1025` ordered exactly as `min(x, 1/x)` predicts — and the **staircase does not scale** (from `k = 6` the wall is longer than the seam it fills: 38 violations at `k = 6` with no gauge in 25 slides, 297 at `k = 21` where the bbox is `62.71` against the law's `44.82`), so its side law is `k = 5` only; doc 59 maps all of it onto the 7-rung ladder (rung 6 empty, rungs 4 and 7 the table's and ours) and names the next production — a **two-word closure**; **27 controls** at 1 m 51.9 s (the `u`-axis repair costs ~3 s; no inflation), float audit green, no row changed; ; run 97 asks the two-word question the ladder named and answers it structurally — `family_spin.py --motifs` (read-only over `submission.csv`) shows the below-floor rows at the ridge's own counts carry **one** word in a *block*: at `N = 901`, 612 axis + 289 tilted, and the 289 form an exact **17×17 lattice** of the 45° word (17 distinct `u` and `v` levels, every gap `1.000000`), the *same* block appearing at `N = 677`; the genuinely two-word rows are **mirror pairs** `(θ, 90°−θ)` — `n = 198` is the 3-4-5 pair, tight to `1.5e−10` (443 rows carry ≥2 tilted classes, 26 exactly two, 9 mirror, 52 below the floor) — and `glm_wheels.py --two-word-spin` builds a field-exact coupled bar (word 1 at the seam centre, word 2 at the exact mixed need `(1 + |cos Δ| + |sin Δ|)/2 > 1`, width from a **monotone closed-form gauge**, the gate as arbiter) over **36 word pairs × `k = 1..8` = 288 sentences, all gated at clearance 0**, seam **constant in `k`** per pair at `2.019084…2.533523`: **0 below `2k + ½√2`, 0 beating the table**, and `0.605…1.119` *wider* than the single-word `m = 2` ridge (`2k + √2`) at the same `N` — coupling cannot cancel the seam, because the floor is **per square** (`φ(θ) = min(x, 1/x) ≥ ½√2`, equality only at 45°) and the mixed tangency is `> 1`; the escape the table actually uses is the block, named as the next production with its falsifier; **28 controls** at 1 m 50.7 s, float audit **253 functions, 0 offenders**, no row changed; records `31`–`60`; run 98 builds the production doc 60 named and answers it exactly: the 45° block of `s²` squares with axis fill in the four corner triangles has `T = k(k+1)/2` per corner, `N = s² + 2k(k+1)` and the contact side `L = max(s/√2 + k + 1, 2s/√2)` (the second branch is the block's own diagonal — the gate caught the first sweep's missing branch as `block45_side_mismatch` on 84 rows); feasibility is one exact inequality, `k ≤ ⌊s/√2⌋ + 1`, because the staircases at the two ends of a wall interpenetrate exactly when `L < 2k`, and the sweep agrees on all **121 rows** (70 gated, 51 refused by `block45_corner_collision`, 0 mismatches); `L − 2k = s/√2 + 1 − k` is minimised at exactly `frac(s/√2)`, so **8 certified rows sit below the single-word floor `½√2`** — the smallest excess **0.020815** at `(k = 13, s = 17)`, `N = 653`, `L = 26.0208152801…`, 2308 exact contacts — which settles that the floor is the ridge's floor and not a law of squares; the two asked points resolve honestly and oppositely: `(k = 4, s = 5)` is `N = 65` at `L = 5/√2 + 5 = 8.5355339059…` with the delivered side differing by **`0E−69`** (the slack `0.535534` *is* `5/√2 − 3` — parity, and the production reproduces a delivered row from a count law and a contact root), while `(k = 13, s = 17, N = 677)` is a **count refusal**: `N(13, 17) = 653`, `677` needs `T = 97` per corner and `T` is triangular (91/105), no `(s, k)` with `s ≤ 30, k ≤ 25` emits it, and the delivered 677 row's own `388 = 4 × 97` axis squares with `t = 14.5` show it is a half-unit-relaxed pose, not this sentence (the `901` row is the family's `(17, 17)` count but infeasible, 40 collisions, the delivered one half a unit wider at `30.520815`); above 1000 the family gates exactly (`N = 1237` at 4532 contacts, `N = 2425` at 9112, `N = 5020` at 19230) yet `L/√N → 1` — 1.018273 at 653 down to 1.000888 at 315300, `N ≈ 2s²`, `L ≈ s√2 = √N`, the block *is* the grid in the limit — so **0 of 70 gated rows beats a delivered row** (seven counts are exact parity: `N = 5, 40, 65, 89, 124, 148, 233`) and the grammar's certified `L < 2k + ½√2` inequalities are not records; **29 controls**, float audit **258 functions, 0 offenders**, no row changed; records `31`–`61`; run 99 builds the production doc 61 §8 named — the half-integer corner fill `t ∈ ℤ + ½` — and answers it exactly: a unit axis square fits the corner triangle `x + y ≤ t` iff `i + j + 2 ≤ t`, so the count sees only `⌊t⌋` and the half unit buys **no square**, giving `T = k(k−1)/2` per corner, `N = s² + 2k(k−1)`, `L = max(s/√2 + k + ½, s√2)` (doc 61's "six extra squares per corner" is corrected: at `t = 14.5` the staircase holds 91, the same as at `t = 14`); the exact dominance law follows — the half member at `k` is run 98's integer contact member at `k − 1`, same `N`, side never smaller and at most `½` larger (exactly `½` in the fill branch, `0` when the block's diagonal sets both, `5/2 − 3/2√2` at `(3, 2)` in between) — and it is measurable against the table: at the seven counts run 98 reproduces exactly (`N = 5, 40, 65, 89, 124, 148, 233`) the half fill is **exactly `½` behind** the delivered side; the sweep of **124 rows** (76 gated, 48 refused by `block45half_corner_collision`) agrees with the feasibility law `L ≥ 2k − 2` on **all 124** (0 mismatches), the window at `s = 17` being `k ≤ 14` with `4, 12, 24, 40` colliding pairs at `k = 15, 16, 17, 18`; the family's excess `L − 2k = s/√2 + ½ − k` crosses zero — closest above `+0.035534` at `(5, 4)`, closest below `−0.085786` at `(2, 2)` — so **29 of 76 gated rows sit below `2k + ½√2`**, and that is exactly why the inequality is not a record here: `k` is the corner parameter, not the ridge's, and `L − 2k` is not the record functional for a block family; the falsifier then resolves more sharply than doc 61 could: the delivered rows' exact lifted sides `29/2 + 17/2√2`, `33/2 + 17/2√2`, `37/2 + 17/2√2` are **exactly** `s/√2 + k + ½` at `k = 14, 16, 18`, so the half-integer *side* law is the delivered side with no tolerance, while the corner fill at that side holds `N = 653, 769, 901` against the rows' `677, 785, 901` — short by **24, 16, 0** — and only `k = 14` is a sentence (clearance 0, **2256 contacts**); at `k = 16` and `k = 18` the two staircases on each wall meet, so the delivered 901 is the fill's count and the fill's side in an arrangement the centred corner fill cannot take, `677` is no count of the family at all, and `785` is one only at `(5, 20)` and infeasible; **0 of 76 gated rows beats a delivered row and 0 is at parity** (closest behind `−0.207107` at `N = 13`, `−0.292893` at `N = 85`, exactly `−0.5` at the seven parity counts), the requested `k = 16, 17, 18` rows are all refused (`N = 769, 833, 901`), and above 1000 the fill gates exactly (`N = 1385` at `L = 41/2 + 25/2√2`, void `−2609/4 + 1025/2√2`, **5016 contacts**, `0.177670` outside the grid's 38) while `L/√N → 1`; the ladder reading is that rung 2 is blind to the half (`integer_indist_zero_half`: `T(k) = T(k + ½)` exactly), rung 3 sees it **as slack** (`rational_distinguishes_zero_half`: `L` moves by `½`, `N` does not), and rung 7 decides (`certificate`: clearance 0 at `k = 14`, the declared wall collision at `k = 16, 18`); run 100 builds the two composable exact plugins the request asked for — a rational Bernstein enclosure in `exact_field.py` (`bernstein_coeffs` / `bernstein_enclosure` / `bernstein_quadratic` / `bernstein_nodes`) that turns a sign question about a continuum into one exact basis change, sound but incomplete (`x² + 1` on `[−1, 1]` encloses as `[0, 2]`; one subdivision certifies `lo = 1`), whose slide certificate on `Block45(5,4)` is positive on `[½, 1]` with `lo = 5/4` and refused on `[−1, 1]` in agreement with the gate's endpoint slacks `½`, `1`, and whose cage replay reads `5/8`, `3/4` and `1/12 + 11/48√7` — all short, capacity 1, `agree True` — and a quadratic-norm residue mask (`norm_residue` / `residue_norm_filter`) whose legality is the `2D²` scaling and whose usefulness is the content division a first benchmark exposed as missing (without it every residue was 0 mod 8: a vacuous mask, fixed before it was reported), so that at mod 8 a primitive `A + B√d` is never `0 mod 8` for `d = 2, 5, 7` and the mask is exact on the Block45Half cells; the benchmark over the four certified cells plus one synthetic sparse lattice reads pairs/contacts/rejected/survivors/extra 266/172/70/196/24, 1102/794/252/850/56, 182/112/70/112/0, 2978/2256/722/2256/0 and 342/90/90/252/162 with **0 false rejections** at mod 8, 12 and 24 and every contact kept — 1.1–1.4× because contact density (65–76 %) and Amdahl set the ceiling, not the mask's cost (an eighth of the exact pass), and the synthetic lattice's 162 diagonal survivors are the blind spot that is stated rather than hidden; the chain and its 7-rung reading are doc 63, `Q`'s comparisons no longer lose `sign` (`_diff`), and no row moved: run 101 draws the certificate boundary and adds the stage doc 63 §6 named — `galois_certificate/1` writes a sentence as exact field tags (`Q`, `Quad(2)`, `Quad(5)`, `Quad(7)`), an exact container side with its exact origin, exact rotation matrices row-major per cell and exact centres, with the canonical-fraction strings the parser accepts and the decimal spellings it refuses (`1.5` is a projection, not a value); the standalone zero-float `verify_certificates.py` rebuilds each sentence from the file alone and checks `R^T R = I`, `det R = 1`, every wall, the declared side and all four axes of every pair with its witness axis and exact gap, accepting `≥ 0` at clearance 0, returning either the verified summary (N, L, contacts, void) or the first exact failed inequality with kind `infeasible` (an overlap with its gap, a wall, a reflection, a non-orthonormal frame) or `outside_representation` (a decimal, a wrong shape, an unknown tag, a duplicate id, a loose `L`, a declared summary the object lacks) — 7 certificates verify (tile2 Q N=4; ring18 Quad(7) 18, `7/2 + 1/2√7`, 26 contacts; staircase149 449; staircase150 451; block45_5_4 Quad(2) 65, `5 + 5/2√2`, 172; block45half_17_14 653, `29/2 + 17/2√2`, 2256; slope21 Quad(5) 5, `2 + 1/3√5`), and **11** mutations of the shipped document are each refused at their own check — two of them genuine SAT overlaps, a three-square sentence inside its box with the span exactly its declared `L` whose cells at `(1/2, 1/2)` and `(7/5, 1/2)` overlap by `1/10`, refused at `sat` with pair `[0, 1]` and gap `-1/10`, in `Q` and again in `Quad(2)`; the verifier's SAT pass is then made independent of the gate's formulation — one common denominator `D`, slacks carried as the integer residual `2D²·slack` in `Z[√d]`, abs and max as integer tests, the field element rebuilt only to *print* the gap — so its bytecode names no producer function, the `Quad` formulation survives only as a witness the selftest cross-checks on all **4,532** candidate pairs (same sign *and* same exact largest slack), and the document pass drops 5 s → 0.55 s; the two formulations are also fuzzed against each other on random exact sentences — unit words found by one integer search, mixed denominators up to 120, coincident centres for strict overlaps — **9,729 pairs over four seeds, 0 mismatches**, a fuzz that on its first run caught the printed gap dividing the integer residual by `D` instead of `2D²` (invisible on the shipped zero clearances); the next stage is `pair_max_slack_bound`, an exact bound `|A + B√d| ≥ 1/(|A| + |B|S)` on the **max** slack (the request's "tightest axis" is the minimum, which is exactly what keeps a diagonal survivor — corrected and recorded), so on `Block45(5,4)` it rejects all 94 non-contacts and leaves the 172 contacts and on the synthetic lattice it takes the mask's 252 survivors to the 90 contacts; the chained prune→mask→bound→gate benchmark reads 2.08×, 2.92×, 2.19×, 4.96× and 4.65× end to end with the filters alone at 1.26×, 1.14×, 1.33×, 1.08× and 2.55× — after a first version that over-reported because it did not time the gate's own `Quad` prune (212,878 pairs at N = 653), now decided on integer components instead — and the mask is shown contact-safe but not verdict-safe, since an overlap has no tight axis either and only the bound keeps it (control 32's 1/10 counter-example); doc 64 carries the schema, the eight-area exact-vs-display ledger and the honest 63 §6 update, and no row moved: ; run 102 turns the certificate instrument on the 424 relaxed rows: **546** of the 1,000 carry a certified exact sentence (447 grid + 99 Q(√2) pose lifts), **30** have an algebraic side but no lifted pose, **424** are relaxed, and a new carrier census shows **every relaxed row carries at least one transcendental angle** (453 rows do; `1–10`: 14, `11–100`: 123, `>100`: 316) with a carrier on the bounding box in 361 of them; the lifting test on 14 targets — the notches 677/785/901, the continuous rows bracketing them (680, 689, 733, 788, 845, 904) and the relaxed rows with the most slack (11, 17, 39, 68, 86) — **lifts 3 and refuses 11**: the three notches certify at clearance 0 (`29/2 + 17/2√2`, `33/2 + 17/2√2`, `37/2 + 17/2√2`, 2375/2785/3227 contacts, certificates verified) with exact sides **3.84–3.85e−9 below** the published ones — the polish shim, not a gain, so **no row beats its delivered side materially**; the four `2k + 4/7` rows (680, 733, 788, 845, sides 186/7, 193/7, 200/7, 207/7) are `not-on-lattice` because dropping their 90–110 carriers leaves squares the surviving contact equations do not pin, and seven (689, 904, 11, 17, 39, 68, 86) are `side-not-recovered` because the core's span is not within 1e−7 of the declared Q(√2) lattice; the completion probe passes its positive control (one cell removed from n = 677 is put back by the axis word at the same side, clearance 0) but no relaxed row reaches it — 0 of 0 attempted — and the control caught two bugs of run 101's family (a pair's clearance read as the minimum slack, contacts emitted per axis without the pair's maximum being zero); the next production is a rational-t construction at side `2k + 4/7`; run 103 cleans the run-102 stage and bounds its cost — `qsqrt2.recover_leftovers` takes a deterministic work `budget` (120 units; `None` = the old unbounded search, so the verifier path is unchanged) and the carrier-drop policy is one documented function — which takes the 14-row run from ~45 min to **306 s** with **every verdict unchanged** (3 lifted / 4 not-on-lattice / 7 side-not-recovered, same sides, contacts, certificates and 546/30/424 tally), and it starts the `2k + 4/7` rung for n = 680, 733, 788, 845: an exact strip lemma says no unit square fits a 4/7 margin (min bbox width over the rational-t alphabet is 1, at the two axis words), the four rows are `N = m² + 4` at side exactly `2k + 4/7` and their angles snap to a constant structure — `m² − 52` axis squares plus exactly **28** at the 3-4-5 word and **28** at `t = 1/3` — whose snapped gate misses by only **1–2 pairs** (788 by **2e−11**), while an exact word-level repair swaps nothing (the defect is positional) and the lift from scratch refuses (`not-on-lattice`, budget exhausted): **0 of 4 certified**, with the next experiment named (788's 2e−11 positional repair; the 28 + 28 band's contact law); **32 controls** plus **6** in `landscape65.py` and **4** in `rat47.py`, run 104 closes the rung's last pair positionally — one cell of each offending pair translated by an exact rational amount along a SAT axis of the pair (788 by **2e−11**), the feasible set an exact interval union in `Q`, the witness the first feasible move so clearance is exactly 0 — and **all four rows gate at clearance exactly 0 with verified certificates**, but at the delivered side, **1.93e−9 above `2k + 4/7`**: the wide wall's tightest cell has 6.8–7.5e−11 of inward room (26–28× short of the excess) and `7` does not divide the pose's `10^12` grid, so the rung itself is still not captured; and it measures the 28 + 28 band — axis cells exactly `m² − 52`, a **7.48-thick strip whose thickness agrees to 5.8e−11** across four independently polished rows while its free length wanders 3.6e−3 (28 cells, 28–29 intra-band contacts: a chain, not a body), **five intra-band contact types with four identical in every row and one count flipping 8↔9**, a band-to-axis interface that is *not* fixed (28–32 contacts, 11–13 types), and the rung's `4/7` as the **shift between `Z²` and `(Z + 4/7)²`** with **18 gaps of exactly 3/7** in every row; above 1000 the arithmetic is exact (`N = m² + 4 = (m² − 52) + 56`, sides `228/7`, `284/7`, `319/7` at m = 32, 40, 45) and growing a row by copying its outer 3-wide band outward **adds no drift** (the new excess is the source row's, digit for digit) yet yields 965 cells where the law asks 1028 — the outer band is not periodic (58 cells in the last 3 units against 87) — so the side law is constructive and the count law is not; **32 controls** plus **6** in `landscape65.py`, **4** in `rat47.py`, **5** in `rat47pos.py` and **5** in `rat47law.py`, run 105 turns to candidates and kills the obvious lever exactly — a homothety of a delivered row cannot lower its side (the container *is* the bbox) — leaving the square's extent `(|c|+|s|)/2`, whose floor is the all-axis bbox, a bound over *every* word relabelling; on ten rows chosen by largest relative void (six above 324, four below 70) **0 of 10 candidates beat**, nine because the axis bound equals the delivered bbox *exactly* (a proof, not a search) and one, n = 333, because its `9.2835e−4` shrink carries 116 overlaps against 115; but **five rows gain their first tight certified sentence** (325, 329, 331, 66, 67) by one exact slide to the nearest contact — sides equal to the delivered ones digit for digit, slides `1e−10`–`2e−10` — and the off-axis motifs are settled as algebra rather than sampling: the strip penalty `|c|+|s|−1` is 0 / 0.414214 / 0.366025 / 0.260074 at axis / 45° / 60° / 72°, hexagonal needs a **new field** Q(√3) whose first certified sentence this is (`N = 2`, `L = 3/2 + ½√3 = 2.366025`, verified — better than the 45° corner by 0.0482, worse than the axis pair by exactly the penalty), and golden is *inexpressible* in Q(√5) because `sin72`'s square has discriminant `20480 = 64²·5`; **5 controls**, **33** in `cand105.py`, float audit **460 functions, 0 offenders**, no row changed; records `31`–`65`; run 106 certifies the census — the screen puts **553** rows in it (words within `1e−9`; the worst row, n = 743, is 1.27 away), one exact `survey` pass per row returns the overlapping pairs and the tightest slack, one `slide_best` closes that pair on *every* positive axis at once (n = 634's diagonal pair has both separations at `1 + 77/10^12`, so a single-axis slide leaves it separated; `t = 77/10^12·√2` on both certifies it with 2 contacts), and the exact gate plus a `galois-certificate/1` decide: **552 of 553 certified at clearance 0, 547 of them for the first time** — 550 by a slide, 2 (n = 678, 679, one overlap each) by the repair — the one exception being n = 1, a single square with no pair to contact, and three spread representatives (n = 2 `L = 2`, n = 427 `1312500000119/62500000000`, n = 1000 `16000000000969/500000000000`) re-verified by the standalone verifier alone (**3 verified, 0 failed**), 551 certified sides identical to the delivered ones and one (`n = 2`, at exactly `L = 2`) `1e−9` lower — the table's own shim and the row's own floor, not a gain — so 547 rows stop being a pose with a tolerance and become a sentence with a witness; the 45 degree repair is generalised to field axes (`t = (sign(proj)·need − proj)/k`, eight signed directions, no `Decimal`) and the two asked rows stay blocked honestly — **n = 330 goes 6 → 3 overlaps in four exact moves** (one of them diagonal, `−1 + 1414025346279/2·10^12·√2`) and stops on three mutually coupled pairs at `−1/2 + 352353905641/10^12·√2`, and **n = 332 does not start** (159 → 159 on its first move) — while the census's two near-misses close (n = 678, 679 certify at `1326776695393/50000000000`); and doc 66 §7's two-cell trade is **enumerated, not sampled**: **1216** combinations on n = 66 and **2880** on n = 325 (every bbox wall cell × every adjacent partner × all eight signed directions) have `tau = 0` **exactly**, none turned down by a gate, so both sentences are jammed at depth one — no interior slack to spend — with the mechanism proven live by a control that shrinks a 4 × 3 sentence's box 4 → 3; **5 controls**, **25** in `cand106.py`, float audit **520 functions, 0 offenders**, no row changed; records `31`–`67`; run 107 answers depth two and the coupled repair with one float-free instrument (`observer_chain.py`, 6 controls) and **corrects run 106** first: `wall_room` capped a pair on its narrowing axes and blocked on a negative one, but a pair is legal while *some* axis is separated — the exact knight pair (`dx = 1`, `dy = 2`) reads 0 under the old rule and unbounded under the corrected one — so "jammed at depth one" was an artifact and **all 90 of n = 66's and all 216 of n = 325's inward probes have positive room** (corridors `231/10^12`–`0.035533` and `27/2·10^11`–`0.100500`); yet **no side moves**: 0 of 90 single-cell, 0 of 68 two-cell and 0 of 12 three-cell chains lower L at n = 66, and 0 of 216, 0 of 144, 0 of 0 at n = 325, because every bounding-box face is **multiply defined** (7–8 cells at n = 66, 18 at n = 325) so the side can move only when the whole face does; the two Lean contracts are re-computed exactly (`readCost(2,1) = readCost(2,2) = 1/3` against the ceiling `√2/4`, so every integer loop-check pays `2√2/3` of it; `taxMOG/Q = cells moved + violated pairs left`, whose `2 + 1 = 3 + 0` tie only the gate can break; the 24-cell syndrome rebuilt over GF(2) from the Lean `Bmat` is injective at weights 1–3 and has 1771 colliding classes at weight 4), and n = 330's three **disjoint** overlaps (184,195), (216,233), (224,247) sit inside the diagnosable weight: 0 hitting sets of size 2, and all **4096** three-cell joint motions clear them while leaving **at least two** other violations (minimum debt 2; the nearest, cells {184, 216, 224} at `t = 1 − 40644125503/10^11·√2`, breaks (170,184) by `−2 + 278387009073/25·10^10·√2` and (201,216) by `−2 + 1115740420767/10^12·√2`), so n = 330 stays blocked exactly; **6 controls**, **35** in `observer_chain.py`, float audit **547 functions, 0 offenders**, no row changed; records `31`–`68`; run 108 settles the face slide doc 68 §4 left open: every face of the two certified rows has positive exact room (`231/10^12` at n = 66, `27/250000000000` at n = 325), a single face slide changes **nothing** because the container is a square and the other axis binds, while the two-face squeeze changes everything — both rows shrink by the sum of their four rooms (`−4.62e−10`, `−2.16e−10`) with **verified** certificates at clearance 0 — and 31 of the 33 exact-worded rows with n ≤ 40 shrink the same way (`Σ dL = −2.6881e−8`): the `1e-9` polish is spendable, but no packing improves, the exact metric moves `−7.885757e−9` (from `22.645990612927686`), the candidate patch of 1,026 changed square rows in `workspace/push/submission_candidate.csv` re-gates clean at clearance ≥ 0, and `submission.csv` is left untouched; the 448 uncertified rows are ranked by their own metric term and the top 15 attacked — three certify (**worse**, by `+2.27e−3`, `+6.79e−4`, `+6.70e−3`), twelve stall with 1–50 overlaps left, **none improves**; **4 controls**, **27** in `face_slide.py`, float audit **575 functions, 0 offenders**, no row changed; records `31`–`69`; run 109 builds the relational layer: `scripts/semantic_pack.py` maps contacts, wall pins, depth-2 pin chains and void pockets exactly, and finds every analysable row **relationally closed** (n = 11: 5 contacts, 2 pins, 2 chains, one `3.53e−4` pocket on a non-binding side; n = 17: 4 chains; n = 29: 1; n = 330: 30 contacts, 2 pins, 28 free wall cells all on `hi_x`/`hi_y` while both binding cells are pinned), then attacks 234 coupled moves (2–5-cell rigid cluster translations, 45°/90° re-orientations, pin-into-void trades): 92 legal, **one model win and zero true wins** — at n = 330 a rigid move gates at clearance 0 with a **verified** certificate at `L = 18.692488` against the table's `18.692672`, but under the row's true angles the same coordinates are `18.692916` against the delivered `18.692388`, i.e. `2.43e−4` **worse** (score `+2.9e−5`); the patch was reverted at once and `sqscore`/`record_guard` are green on the delivered table. The lesson is structural: 236 of n = 330's 330 angles are not words (gaps to `6.9e−3` rad), the table's L is itself a model value (overstating that row by `2.84e−4`), and `cos` of a rational non-zero angle is transcendental, so **no algebraic field can certify a transcendental row** — the sound routes are a snap error budget, certified interval arithmetic, or a genuine extension only for algebraic angles; **3 controls**, **28** in `semantic_pack.py`; run 110 reconciles the delivered table: `reconcile_table.py` measures every row at 40 decimal digits (`true_geom.py`, no float) and finds **357 of 1000 rows stale** (largest `9.0e−2` at n = 696), with `Σ L_table/√n − 1 = 22.645990612927686` against `Σ L_true/√n − 1 = 22.218056944873789` — the two numbers that had looked contradictory differ by exactly `0.427933668053897`, the accumulated snapping error — so `L` is now the true side, `L_model` kept, provenance in `table.meta.json`, and `sqscore`/`record_guard` are green; adds the **ε(gap) containment guard** (`ε = 2·max|θ − word|`, which bounds the model error since the half-extent is 1-Lipschitz in the angle), so a candidate is promotable only within ε, overlap-free at 40 digits, and strictly below the true delivered side — run 109's n = 330 artifact is refused automatically (model `18.692487647`, true `18.692915843`, overlaps at true angles) and the bars are 3.871321392 / 4.668646323 / 4.819512197 / 5.926803177 / 18.678566016; and frees **all angles** (`relax_angles.py`, L-BFGS-B on position + angle, discovery only, outside the audit): every shrunk state has 11–41 overlaps and the best legal state is worse than delivered on all four rows (`+9.3e−8`, `+3.7e−7`, `+2.8e−7`, `+2.0e−3`), so the delivered packings sit on the feasibility boundary; **3+2+2+4 controls**, **36** in `semantic_pack.py`, **7** in `true_geom.py`, **6** in `reconcile_table.py`; run 111 gives n = 29 its definitive push — a constrained shrink ladder (six targets `1e−4` … `4e−3`, four restarts, projection after every attempt, judged only by `true_geom` at 40 digits): **no legal state beats `5.933833464`**, the best is `5.933929467` (`+9.6e−5`, down from `+2e−3`) and the ladder is monotone in its target; the screen of doc 69's ten highest-slack rows puts every one in a single legal-gap band (`6.2e−5 … 3.3e−4`, n = 29 in the middle), so there is no uniquely loose row, and the band is schedule loss rather than structure (11/17/18 collapse to `1e−7` under run 110's stronger schedule, while the ladder beats the general schedule on the six bigger rows); `72-SYNTHESIS-AND-NEXT.md` collates runs 60–111 — 552 certified rows, exact carriers, the integer-scaled SAT verifier, face-squeeze bounds, the ε guard, the reconciled table, six architectural invariants and four falsifiable promotion criteria; run 112 abandons repair for construction — `pattern_seeds.py` builds macro-block seeds (dual 45° blocks, L-cut frames, Pythagorean lattices, and an upright reference) from `n` and `L_delivered` alone and judges them with `true_geom` at 40 digits: **no family beats the delivered side on any of nine rows** (upright loses least at `0.68–2.26%`, then L-cut frames `3.6–12.2%`, dual 45° blocks `6.8–31.9%`, Pythagorean lattices `42–48%`, all with zero violations), and the exact split `void = tilt waste + packing waste` explains it — a `k×k` 45° block doubles its area in its bounding box, so a tilted body pays twice while a tilted boundary staircase pays only a strip, which is why the best seeds use almost no tilt and why the delivered table tilts only at the edge; run 113 makes the non-word rows certifiable and closes the boundary route — `interval_verifier.py` brackets every direction in rational intervals (`isqrt` on scaled integers, `Fraction` only, 7 controls, now inside the float audit at **613 functions, 0 offenders**) and proves all 4N wall bounds and a strictly positive separating-axis gap for any rational-centre pose, refusing exact contacts as inconclusive; the corner-nesting packer (`nest_pack`, corner insertion over boxes) gains A `1.0` of side on eight of nine rows and B `0.24–0.88`, with B tying the upright reference on six, and corrects doc 73's reading of D's residual (for upright blocks the boxes tile, so `L² − n` is the ceiling, not the shelf); family E's seats follow a derived law — pitch `1/max(|c|,|s|)` and protrusion `|c|+|s|`, both `≥ 1`, equality only at the axis — so **not one fringe cell fits inside the delivered side on any of the nine rows**, E's fill is exactly `floor(L)²`, and the shortfall is `n − floor(L)²` = 4, 5, 4, 6, 4, 4, 4, 4, 10 cells, every fill certified strictly below `L_delivered` (3,844 wall bounds and 461,280 pairs on n = 971, tightest slack `1e-9`); the `t = 1/q` sweep at n = 971 runs 952 → 961 cells (void 51.5 → 42.5) monotonically, saturating exactly where the tilt vanishes, so all 9 cells the 45° staircase could contribute are recovered by removing it; the lattice ceiling (`side ≥ ceil(sqrt n)`, and all nine rows beat the grid) then closes every integer-lattice construction on those rows by arithmetic; run 114 prices the grid wall instead of arguing with it — `published_census.py` benchmarks every covered row against the Squares Project's best-known list of 2026-10-20 (**0 behind, 21 ahead by 0.006414**, so the catalogue holds no score) and re-prices each unbeaten row in void currency: since `n = k^2 - j` is beaten iff `V = L^2 - n < j`, the frontier rows spend **87–99.9 % of their void budget** and the median next row must give up **0.72 unit^2** of empty area; `void_insert.py` then measures the operative question exactly (separating axis over the four edge normals, 2 controls with known answers — an emptied `3 x 3` corner reads 1.0000, a full one 0.0000): the largest square that fits in each frontier pose is **0.45–0.83 of a cell at `k <= 20`** (a real void, so a rearrangement) but **0.9994–0.9999 at `k >= 21`**, where it equals `1 - (k - L)/k` to within `6e-4` in ten of eleven bands — those poses are **uniformly compressed lattices** whose every hole is a squashed unit cell (`k = 23` the exception at 0.7534); eleven seating attempts (`--seat`, container hinged at `k - 1e-3` so any legal seating is automatically a beat, 1–6 freed cells, `1e-9` clearance, 40-digit verdict) **all fail**, landing at `k + 2e-9` with 2–11 violations and the container short by ~`4e-3`, while unhinged the cell seats perfectly at `k + 1.1e-4…2.4e-4` — local freedom cannot redistribute a uniform compression, which is why no world record crosses these rows either; the campaigns are then priced honestly: inheriting each band's frontier side on all 30 next rows is worth **+0.23251** (more than the 0.163635 gap, so the grid campaign *can* pay for it at 100 % success), while the **553 beaten rows leave 15.02 score unclaimed** and a 1 % capture is **+0.15023** — 1.1 % of that room is the whole gap; doc 75 records it with the recommendation that the compressed-lattice rows need a global compression-redistributing move (block substitution), not a local push; run 115 runs the block-substitution campaign on the compressed-lattice band tops and answers the family question — `block_swap.py` enumerates every near-full p x q block (1–3 holes, ≥4 cells, p ≤ q ≤ 7) of all twelve k ≥ 21 frontier poses and asks whether c+1 cells fit the block's own compressed box at the record side: **0 blocks fit in any band**, and the best block everywhere is the same **3 x 3 holding 6 cells (3 holes) needing 7 cells in 2.9991–3.0000**, short by **2.2e-5…8.9e-5** — the compression itself (`3·delta/k` predicts 3.3e-5 at k = 26 against 2.2e-5 measured) and **impossible rather than hard**, since **s(7) = 3 is proved**: the optimiser stalls at penetration 1.8e-8, 2.3e-8, 7.2e-8 (k = 26, 29, 31) after 2500 iterations and four restarts; `grid_families.py` then spells Block45, Block45Half and the ridge (m ≥ 2) exactly — 660 members, 369 of them at counts the table already beats — and asks whether any member (a packing of N cells covers every n ≤ N) puts a grid row below base: **0 of 444 beaten, 0 at parity**, closest **+0.0711** at n = 212, 242, 243, 244, 17 rows within 0.15 and 43 within 0.25, median **+0.6066**, max **+0.7071 = ½√2** — so the 45° families beat the base grid only where the table already does, and on the unsolved set they are 0.07–0.71 *behind*; the band count is corrected to **30** (k = 3…32, band 32 clamped at n = 1000, frontier 998 → next row 999), which run 114's loop dropped — moving the inheritance bound to **0.23251** — and band k = 32 measures a real 0.7171 notch (not a sliver) with the cheapest large-band price in the table (+0.120); run 116 places the standing card — `DIRECTORS-NOTE.md` at the project top level (orientation, the no-float definition, proved leverage, open leads, the C1–C4 gate), reviewed line by line with **one factual error corrected** (the compressed frontier rows are `m* = k² − j*`, `j* = 18…26`, **not** `n = k² − 1`) and pointed to from README, STATUS and `00-OVERVIEW.md` — and opens the re-squeeze lead: `resqueeze.py` inserts a cell at the free-space point then runs patch-coordinate relaxation (overlapping 4.5-wide patches, sweeps in random order, a **monotone acceptance test** that keeps a patch move only if the whole-pose penalty falls) with the container at `k`; the control (no insertion, k = 26) caught a margin bug that **destroyed a legal pose** (box at `k − 1e-3`: pen 0.59, 234 violations) and then set the instrument's floor — residual contacts `2.4e-14` (max `7e-8`), side `26.0000000013`, i.e. **penalty descent inflates the pose to `k` and spends the frontier's own `delta`** instead of gaining room; with the insertion k = 26 lands at side `26.0000000013` with 79 violations and max penetration `4.6e-6` (the sliver to `1e-9`), while the k = 32 notch lands at side **`31.996876`** — `3.1e-3` *inside* `k`, worth `9.9e-5` — but jammed with 17 overlaps at max `9.4e-2` after `1/168` then `0/168` patch moves were accepted, so the notch is **real room** and the jam is combinatorial 17 pairs deep; no beat, and the next fix is named (hard side projection + contact repair, not more descent); run 117 takes the k = 32 notch to its end under the card's first fix — the side constraint as a **hard projection** (every cell clamped exactly into the `k`-box after every move, penetration the only objective) plus a **contact-graph repair** (exact separating slide `sign(proj)(h_a + h_b + eps − |proj|)` on the deepest pair, monotone on `(pairs, sumsq, depth)`, 12 pairs per pass) — and answers the question: **no**, n = 999 does **not** get below 32 with zero overlap; it reaches side `31.99687592223010338076867830301645689164` (`3.1e-3` inside `k`, worth `9.9e-5`) with **6 violations at 40 digits**, the 23-pass repair moving the deepest bite only `9.392e-2 → 9.389e-2` before **no single slide helped**, and a constrained sweep accepting **0/168** patches (the monotone test refuses all of them, so it is a true local minimum of that move set); the finer scan also corrects the k = 32 free square from `0.7171` to **`0.8394`**, so the cell is `0.1606` short while the pose has `1.4e-2` of slack against a `9.4e-2` bite and the three pairs are mutually blocking; and it **prices the polish campaign** — a 1 % capture (one pp of `e`, worth `0.21742`; 1 % of the 15.02 room is `0.15023`) needs `dL = 0.01(k − sqrt n)` = **`0.00399…0.00984`, median `0.00708`** per row against run 111's measured legal-gap band **`6.2e-5…3.3e-4`**: **0 of 553 rows** need less than `3e-3`, every one needs more than the whole band, and the best-case polish ceiling (every row moves by `3.3e-4`) is **`+0.00999`** — so 1 % costs **21.8× the entire campaign**, the polish is 553 new constructions rather than a nudge, and its honest ceiling is one sixteenth of the gap; run 117 reconciles and measures — doc 75 §11's **3 pairs vs 6 violations** is two readers, not two answers (the repair's screen admits penetration **> 1e-9**: 3 pairs, deepest `9.389e-2`; the 40-digit judge counts every **slack < 0**: 6, the extra three being near-tangent), and the k = 32 **no** is scoped to the finest free-square centre (`0.8394`), exact single-cell slides plus patch descent, container exactly 32 — `polish_ceiling.py` then measures the ceiling instead of arguing from run 111's band by shrinking each row's own container and repairing under a hard clamp: on a 12-row stratified sample (k = 17…32) **every ceiling is `0.00000`**, not one row closing even at `delta = 3e-5` (one thirtieth of the band's floor), each stalling after one or two passes because a zero-clearance pose has no slack to trade, so the honest polish ceiling is **0** rather than the `+0.00999` the band allowed or the `0.15023…0.21742` a 1 % capture is worth; and `anchor_chain.py` bridges `glm_universal.reasoning.stepwise_script` — **ANCHOR_CORNER / STACK_BLOCK / PROPAGATE_SLIDE** admitted only when `step_check` and an exact Q(√2) placement gate both pass — rebuilding the certified n = 10 row as **10/10 admitted anchors** (4 corner, 4 slide, 2 stack) with side exactly **`3 + 1/2√2`**, zero overlap, contact graph `0-1 0-2 1-2 1-8 2-9 4-5 4-6 5-6 5-9 6-8 8-9`, plus a refusal control that bites `1/4` into its parent and is refused for the geometry (**exact slack `−1/4`**); float audit **632 functions, 0 offenders** (`anchor_chain` 19 of them), and the verdict on the project's question: a verified transcript of a packing, not yet a solver; run 118 closes both open items — the polish ceiling's worst-case-clamp loophole is closed by the **boundary-only control** (shrink by `delta`, translate only the cells protruding past a wall, same repair, same 40-digit judge: **12/12 sampled rows `0.00000` at all three `delta`s** again, so local polish is closed and the ceiling is a property of zero-clearance poses plus single-cell slides, not of the clamp) and the anchor grammar goes forward — `anchor_chain.py` is now field-generic and rebuilds the **Q(√7) n = 18 Ring row** as **18/18 admitted anchors** (4 corner, 6 slide, 8 stack) at side exactly **`7/2 + 1/2√7`** from coords `(a+b√7)/q`, `q ≤ 32`, worst read `1.8e-9`, the same three commands and two gates as n = 10; its **forward settler** admits determined anchors only at clearance `≥ 0` and backtracks on exact refusals: **n = 4 at L = 2 settles 4/4** exactly, **n = 5 at `2+1/2√2` stalls at 4/5 with the DFS exhausted (221 nodes, not a cap)** — locating the missing command precisely as **two-parent closure** — and **n = 212 at L = 15** fills 14 cells in a 5.5-wide corner before the frontier dies, no answer within budget; audit green; run 119 re-tests and completes the forward settler — doc 78 §3's "exhausted at 221 nodes" is re-run with **no per-node candidate cap and no node limit** (state-deduped): the claim **holds**, the one-parent state space closes at **4/5 in 69 nodes / 68 states**, and the **count is corrected** from 221; the diagnostic showed the generator *does* produce the optimal fifth cell from the optimal four corners, so the search was never reaching that state — adding the **two-parent STACK_BLOCK** (two tangency equations solved exactly as a 2×2 system in Q(√2) over the axis pairs of both parents *and the candidate*, since the 45° cell touches two axis cells along *its* axis) and **ANCHOR_CORNER at every depth** (a regression of the rewrite) gives **5/5 at `2 + 1/2√2`**, span exactly the target, 248 nodes / 260 states, settling the known optimum — four corner cells plus `(1 + 1/4√2, 1 + 1/4√2)`; a free 2-D field-lattice enumeration was tried and **abandoned as the wrong algorithm** (~10 000 field points within radius 3/2), and **n = 212 at L = 15** stays an honest no-answer-within-budget (14 cells in a 5.5-wide corner); run 120 replaces the sweeps with **constraint intersection** (wall+contact solved by one division, two-parent STACK_BLOCK as an exact 2×2 solve over both parents' axes *and the candidate's*) and adds two audited speedups — an **integer-only √d bounds prefilter** (skip rates **98.3 %** at n = 5, **99.4 %** at n = 6 and n = 7) and a **failure-pair memo** (**86.1 %** hits at n = 5, **88.0 %** at n = 7) — and — corrected in run 121 by re-running the old generator at the same settings — the real speedup is the **width 8 + contact-first ordering** (248 → 60 nodes, 140.8 → 25.8 s at the *same* generator), the intersection generator being marginally **slower** (69 vs 60 nodes) but derivation-complete; the settler then runs **n = 6 at L = 3 → 6/6** (17 nodes / 43 states, 8.75 s) and **n = 7 at L = 3 → 7/7** (128 nodes / 159 states, 102.6 s), both spans exactly 3 = the proved optimum — **no stall for either**, so nothing to diagnose as exhaustion, missing command or budget, while the frontier-mode n = 5 stall remains **genuine exhaustion** (69 nodes, 68 states, stack emptied); stated plainly that settling 6 and 7 at L = 3 confirms the grammar on the grid regime (every 3×3 cell is corner- or contact-closed) and does not test it where the grid fails; run 121 makes the run-120 speedup **attributable** — the old generator is kept as `mode="sweep"` and re-run at the same width and ordering: sweep **60 nodes / 25.8 s**, intersection **69 nodes / 31.2 s**, so the real speedup is the **width 8 + contact-first ordering** (248 → 60 nodes, 140.8 → 25.8 s at the same generator) and the intersection is marginally slower while being derivation-complete; dead code (`_offset_cache`, the unused `lattice=` argument) removed; and the settler is pointed at real rows through a new CLI (`sq_cli.py settle|row|verify|audit`) — **n = 12 (k = 4, unbeaten) settles 8/12 at a 20-node cap with **73 determined anchors still available**, so its stall is a **budget/order limit, not exhaustion and not a missing command**, and **n = 23 (k = 5)** is **throughput-limited** (no result in 900 s, state space nowhere near closed); run 122 gives `row` a **wall-clock budget with checkpointed partial progress** (the deepest pose, reloadable exactly) — **n = 23 in 150 s reports 11/23 at span exactly 5 with 0 overlaps and 129 anchors still available**, and n = 12 in 45 s reports 8/12, both **budget-limited rather than exhausted or missing a command**; and the strategic answer is recorded plainly: the settler **cannot reach the ~990-cell rows** — `pairs/node ~ 7d²` at ~388 pairs/s gives **~17 700 s per node at d = 990**, a **4 866 h (203-day) floor** for a single non-backtracking chain, and even a completed chain would land on the grid side, worth **1e-9** against the **4e-3–1e-2** per row the score needs, so the line is kept as a **certifier** (`sq_cli verify`) and not scaled; run 123 runs the **non-closure perturbation test** doc 81 named — 20 of the 447 unbeaten rows at 10 s each, cells free within ~1e-6 — and gets **dL exactly 0 on 20/20** (0 violations), with the search *validated* by controls that recover injected slack of **5.0e-3 of 6.0e-3** and still 8e-6 of 3e-5, and with the poses measured at **1.2e-10 internal clearance and no touching contacts**, so the rows are already at their grid side and a gain needs a **topology change, not a polish** — verdict: **no tail, do not scale**, and the three local routes (closure settler, polish clamps, perturbation) now agree that the 447 rows need a different packing structure; run 124 tests the **structure-changing route** (penalty squeeze + projection + legalisation, with a block teleport and a 2×2 rotation as the structural moves) on 20 evenly spaced unbeaten rows at ~10.5 s each, after two controls prove the mechanism fires (**100 % recovery of an injected 3.75e-3**; a 0.3-displaced cell absorbed) — **0 rows with positive dL**: the only legal outcomes are the delivered side or an **expansion of 5e-2–1.6e-1**, so the route **cannot hold a compression** on these rows; the run also found **three mechanical bugs in the resqueeze instrument** (intra-patch pairs unpenalised, empty patch list for flat poses, illegal poses counted as gains), which puts run 116's null result **on notice for a re-run**, and leaves the relaxer trustworthy as the second half of a combinatorial tiling search; run 125 completes that table — all **20** rows at 3 s per attempt give dL **0** on 20/20 — and measures why: one relaxation sweep costs **5.3 s at n = 33, 72.6 s at n = 439, 163.3 s at n = 942** (374–410 ms per patch solve, 13–426 patches), so no sweep finishes inside the budget and every pose returns at the delivered side; where a sweep does finish (n = 33, 10 s) the squeeze gains 2.0e-3 and legalisation returns **4.98e-1**, so run 124's "cannot hold a shrink" is narrowed to **no gain where it ran, untested at scale, with throughput — not geometry — as the named bottleneck** (doc 83 §3–§4 rewritten); and run 116's band test is **re-run on the corrected driver** (doc 84): all three bands still **no beat** — k = 26 settles at `26.0000000016` (control) and `26.0000000037` (insert), while k = 32 drives the 999-cell pose to **`31.906664808`** with `4.13e-3` penetration and the first near-legal rung (`f = 0.1`) lands at **`35.097331289`**, 3.1 above the grid side — so the old null is **confirmed** and its violation counts (76, 79, 17) are **retracted** as artifacts of the unpenalised intra-patch pairs and the empty patch list, both runs being sweep-limited; run 126 removes that limit — the patch solve is compacted to the patch+neighbourhood and given an analytic gradient (374–410 ms → 2.1–2.4 ms per patch, verified against scipy finite differences at 6.6e-6–1.25e-5 and 57–67x faster, with a control that caught a gradient right at the start pose and 1e7 wrong off it) — and re-runs the same 20-row table with the attempt budget split 60/40 between squeeze and projection: **20/20 rows now complete at least one sweep, 19/20 squeezes reach L0 − 4e-3, and dL is still 0** because legalising costs 4.6e-2 to 3.0, so run 124's null is reinstated on evidence instead of inference (docs 83, 85); float audit **657 functions, 0 offenders**, no row changed; run 127 builds the **legal rearrangement move** doc 86 named — `legal_slide.py`: band slides, single-cell slides and a block swap into a void, each accepted only if the 40-digit separating-axis slack **at the destination** is `>= 0` (legal at every accepted step, never squeeze-then-repair; only moved-vs-unmoved pairs need testing, since a common translation preserves the group's internal offsets exactly) — with five controls: P a gapped 4x4 tightens **4.25 -> 4.00** with one legal move and the resulting pose re-checked pair by pair, N three single-cell overlaps refused at exact **-1, -1/2, -1**, N3 a 4-unit slide onto a *distant* occupied cell refused at **-1** (regression, below), N2 a free cell slides into empty space and is accepted (so refusals are about overlap, not paralysis), V a 3x3 with its centre removed gives **7 seats**, the outside cell swaps in at slack **0** and the side falls **5.00 -> 3.00**; the first sample run then exposed a soundness bug — `check_move` tested the mover's *old* neighbour list, so a long slide passed over its old neighbours and was accepted (clearances of 3.3-9.5 **units** on poses jammed at 1e-10, the same on all four walls), fixed by a destination lookup with N3 as its regression; on 6 unbeaten rows (33, 159, 439, 662, 883, 942) at 20 s each the move set **fires but does not shrink**: **0 slides** accepted, because every wall cell has **3.3e-10 ... 6.5e-11** of legal room (measured by bisection, not derived), **1 legal void swap on every row** but side-neutral (the vacated cell is one of a full wall column), **dL 0 on 6/6**, and on n = 33 and n = 159 the independent 40-digit pass returns the delivered side with **0 violations**; doc 85 is now audited — every per-patch rate is measured (2.1-2.4 ms warm, 374-410 ms pre-change), every sweep time is arithmetic on those rates (**5.3 / 72.6 / 163.3 s -> 0.4 / 1.0 / 3.2 s are estimates**: no sweep ever completed in run 125), completion is counted (appendix: **20/20 rows with >= 1 completed sweep**, 18/20 also aborted one), and the n = 33 pre-change figure is corrected from 264 ms to **517 ms** (first call, imports included; 264 ms is the warm batched figure); a third independent instrument therefore puts the blocker in the packing structure, and the named next step is to run this move set on the **relaxed** poses, where clearance is not zero; float audit **678 functions, 0 offenders** (657 + `legal_slide`'s 21), no row changed |

## Where the score stands, said plainly

Runs 62–67 changed **no row of the table**. They priced the routes that were
nominated and closed them on measurement: the catalogue the frontier is read
against stops at n = 324 (675 rows open for want of a *source*, not a method —
runs 76–77 settle 60 grid rows outright by a published bound and certify the 191
beating rows at n ≤ 400 as frozen-angle optima, and 247 of the open grid rows sit
above 324 in one residue band);
Bui's construction was implemented exactly and refused (density 0.23–0.82 against
≈0.95); and the remaining search shapes — k-square neighbourhoods, reduced
resolution, global disjunctive SAT — were each refused with a certificate or a
counted reason rather than an opinion. Every instrument points at the same object:
the **branch assignment** (which pair is tight on which axis) and rotation.

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
7. **The theory layer (runs 62–67)** — the part that decides rather than searches,
   and the only part that can say *why* a route is dead: `bui_wheel.py` (a
   published nomination implemented to the letter over ℚ and refused on density,
   132/132 verified, 0 gains), `ladder.py` (six expressiveness rungs, 4 recomputed,
   2 honestly quoted — the Λ₂₄ sweep kills coarsening at all eight scales),
   `disj_census.py` (0.76 % of pairs tight at n = 1000, 1e300729 leaves: the model
   is decisive *with the disjunction fixed*), `sat_probe.py` + `extreme_probe.py`
   (the declared-axis LP as a certificate: with every translation free, the
   delivered side is the exact optimum at ε = 1e−6), and `resolution_probe.py`
   (snapping the *answers* to a lattice invalidates them at every resolution,
   m = 128 included — contacts are equalities with no neighbourhood). Records
   `27`–`30`; `sat_probe.py --selftest` (6/6) is the invariant that guards the LP.

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
