# Methods Tried and Their Measured Effects

A honest ledger of every approach we have attempted on the 50 real
ARC-AGI-2 training tasks, what it actually achieved, and what we
learned.  Compiled so we stop re-trying things that don't work and
stop discarding things that do.

**Baseline:** 50 real ARC-AGI-2 training tasks.  Hard gate = exact
train-pair reproduction.  Solve = exact match on the held-out test
output.

---

## A. Encoder layer — turning an ARC grid into UBP substrate

| # | Method | What it does | Effect | Verdict |
|---|--------|-------------|--------|---------|
| A1 | Flat 24-bit vector per grid | Concatenate all cells, hash to 24 bits, snap to Golay | NRCI computable but no signal for correctness | kept as diagnostic only |
| A2 | Per-cell 24-bit Leech address | Each (row, col, colour, h, w) → unique 24-bit address via `ontological_position_to_vector` | Foundation for hex-colour learning; gives 70-94% cell accuracy on 12 tasks | **KEEP — core substrate** |
| A3 | LDP codec (10-bit structural fingerprint) | Per-object mass/tension/zone via `C(N) = ⌊N/2⌋ - φ(N)/2` | Diagnostic only; never predicted correctness | drop from pipeline, keep module |
| A4 | MOG quadrant split (4×6 = 24 bits) | Bits 0-5 Mirrors, 6-11 Information, 12-17 Activation, 18-23 Potential | Conceptually clean, used by A2 | keep |
| A5 | Gray code → Z₄ → R¹² lift (HDRB Pillar 2) | 24-bit → 12 Z₄ entries → 12 real coords | Enables Whitney forms + Hodge decomposition | **KEEP — HDRB pillar** |

**Lesson:** the per-cell 24-bit address (A2) is the only encoder that
produces useful signal.  Everything else is diagnostic depth.

---

## B. Candidate generation — producing transformations to test

| # | Method | What it does | Solve rate contribution | Verdict |
|---|--------|-------------|------------------------|---------|
| B1 | All 162 DSL ops, brute force | Try every op, hard-gate filter | 1/50 (the gravity_down task) | **KEEP** but only ~20 ops ever win — drop the other 142 |
| B2 | Train-derived colour mapping | Read off `{old: new}` from train pairs | 0/50 alone, but ties break correctly with B1 | keep |
| B3 | CRG-learned colour mapping | ObjectCRG extracts dominant transform per colour | 0/50 alone | keep as candidate source |
| B4 | Two-op compositions (geo + recolour) | 12 geo ops × 2 train maps = 24 composed programs | 0/50 | drop, never wins |
| B5 | Prediction paths: analogy | Find structurally similar train object, apply its transform | 1/50 (a chain task) | keep, occasionally wins |
| B6 | Prediction paths: chain | Discover multi-step CRG edge chains | 1/50 | keep |
| B7 | Prediction paths: group | Detect spatially-grouped objects, transform together | 1/50 | keep |
| B8 | **Hex-colour uniform delta** | If every cell has the same `addr_in XOR addr_out`, apply it | 0/50 — only catches identity | keep, cheap |
| B9 | **Hex-colour colour mapping** | Per-colour mode mapping derived from deltas | Catches pure recolour tasks | keep |
| B10 | **Hex-colour nearest-address (single NN)** | For each test cell, find nearest train cell, apply its delta | **12/50 candidates pass train gate; 70-94% cell accuracy on the 12 it gets wrong on test** | **KEEP — the wobble** |
| B11 | **Hex-colour k-NN voting (k=5, threshold 0.6)** | Vote among K nearest; fall back if uncertain | Same train-gate pass rate as B10 but more conservative on test | **KEEP — refine** |
| B12 | Generative transformer | ObjectCRG + Φ-grammar + Three Column | 0/50 beyond what B1-B7 already produce | drop from pipeline, keep module |
| B13 | Φ-grammar conditional candidates | Position-dependent pattern detectors | 0/50 | drop, never produced a winner |
| B14 | SRCC monad (T, η, μ) | Self-referential computational cycle | 0/50 — converges on NRCI, not on correctness | drop from pipeline |
| B15 | TGIC v3 (HomologyJump, InformationFunctional, CanonicalEvolution) | Escape local minima via octad XOR | 0/50 | drop from pipeline |
| B16 | Bell number partition analysis | Count learning methods for n objects | Diagnostic only | drop from pipeline |

**Lesson:** the ONLY methods that produce train-passing candidates
beyond the 162 DSL ops are B5-B7 (prediction paths) and B8-B11
(hex-colour learning).  Everything else is observability.

---

## C. Filtering and ranking — choosing among candidates

| # | Method | What it does | Effect | Verdict |
|---|--------|-------------|--------|---------|
| C1 | NRCI as ranker | Higher NRCI = more coherent = preferred | Fails: stability ≠ correctness, often picks wrong | drop as ranker |
| C2 | NRCI as tiebreaker (after hard gate) | Among train-pass survivors, highest NRCI wins | No improvement vs random | drop |
| C3 | LDP mass/tension as ranker | Lower tension = more stable = preferred | Same failure as C1 | drop |
| C4 | HDRB signature match | Train signature vs candidate signature, cosine similarity | Doesn't discriminate when signatures match (common case) | keep as sanity check, not ranker |
| C5 | **Source priority (MDL proxy)** | Identity < gravity/rotate/flip < shift/crop < recolour < train_map < compose < hex_uniform < hex_colour_map < hex_nearest < analogy/chain/group | Recovers the 1/50 baseline; doesn't improve it | **KEEP** — Occam's razor is the right default |
| C6 | eml (Y observer) | `exp(NRCI) - ln(tension)` | Diagnostic only | drop |
| C7 | Triadic verifier (Oracle + Swarm + NoiseCore) | Three-layer agreement | Never produced a different verdict than the hard gate | drop |

**Lesson:** when multiple candidates pass the hard gate, Occam's razor
(C5) is the best tiebreaker we have.  All "coherence-based" rankers
conflate stability with correctness.

---

## D. Verification — accepting a candidate

| # | Method | What it does | Effect | Verdict |
|---|--------|-------------|--------|---------|
| D1 | Hard gate (exact train-pair reproduction) | Program must reproduce every train pair exactly | **The ONLY reliable filter** | **KEEP — non-negotiable** |
| D2 | Soft gate (NRCI ≥ threshold) | Accept if coherence is high enough | Catastrophic — accepts wrong candidates | drop, never use |
| D3 | Triadic verification | Language + math + code agreement | Adds nothing beyond D1 | drop |

**Lesson:** the hard gate is sacred.  Every softening of it has
backfired.

---

## E. Substrate-level / GLM modules

| # | Method | What it does | Effect | Verdict |
|---|--------|-------------|--------|---------|
| E1 | UBP backbone (ubp_unified_v5.py) | Golay engine, Leech engine, MOG categories | Foundation — used by A2, A5, B10 | **KEEP — load-bearing** |
| E2 | Spatial arithmetic (R(n), eml) | `R(n) = 1/(2·sin(π/n))`, `eml(x,y) = exp(x) - ln(y)` | Diagnostic; never predicted correctness | **KEEP — needed for geometric language** |
| E3 | LDP (Literal Data Physics) | `mass = C(N) = ⌊N/2⌋ - φ(N)/2`, tension, zone | Diagnostic only | keep module, drop from pipeline |
| E4 | TGIC v3 | HomologyJump, InformationFunctional, CanonicalEvolution | No solve-rate contribution | keep module, drop from pipeline |
| E5 | HDRB (Hodge–De Rham Bridge) | 4 pillars: axiomatic iso, substrate lift, Whitney, Hodge decomp | Diagnostic; doesn't discriminate | **KEEP — needs to become a generative primitive, not just a signature** |
| E6 | GLM lingo translator | Human ↔ UBP-Lingo, geometric translator via Totient Reaction Kinetics | Reasoning trace; no solve-rate contribution | **KEEP — needs to actually drive candidate generation** |
| E7 | GLM lingo chat | 4-layer reasoning (Reality/Information/Activation/Potential) | Reasoning trace; no solve-rate contribution | **KEEP — needs to drive generation** |
| E8 | CRG persistence (save/load across tasks) | Accumulate edges across tasks | No cross-task transfer observed | drop from pipeline |
| E9 | Per-object 24D addresses | Each object gets a Leech address | Subsumed by A2 | drop, A2 is finer-grained |
| E10 | ObjectCRG (full) | 30 SpatialRelations, 38 TransformTypes, AnalogicalMapping, TransformChain, ObjectGroup | Powers B5-B7 | **KEEP — load-bearing for prediction paths** |

**Lesson:** the GLM modules are not useless — they are *unusued*.
Lingo chat, geometric translator, and continuous learner should DRIVE
candidate generation, not just produce traces.  This is the user's
"language machine, not script pipeline" point.

---

## F. What has actually worked (the keepers)

1. **Hard gate (D1)** — non-negotiable
2. **Per-cell 24-bit Leech address (A2)** — the substrate
3. **Hex-colour k-NN with voting (B11)** — the "wobble", 70-94% cell accuracy
4. **~20 DSL ops (B1 trimmed)** — gravity, rotate, flip, recolour, shift, crop, tile
5. **Prediction paths analogy/chain/group (B5-B7)** — occasionally wins
6. **Source priority MDL tiebreak (C5)** — Occam's razor
7. **UBP backbone (E1) + Spatial arithmetic (E2)** — the maths layer

Everything else is either diagnostic depth (kept as modules, dropped
from pipeline) or failed experiments.

---

## G. What we have NOT yet tried (the leads)

1. **Free k-arm**: instead of anchoring the k-NN at Y (the observer
   constant), anchor it only at the test cell.  Let the arm rotate
   (try the test cell under D4 rotations) and time-propagate (apply
   the delta through T steps).

2. **Geometric language primitives**: direction, Time, rotation as
   first-class language tokens.  Currently the system has no
   vocabulary for "this cell moved leftward over 2 time-steps".  The
   lingo translator exists but doesn't drive generation.

3. **256-colour space mapping**: the standard 3-3-2 RGB palette is
   well-studied.  Bridge our 24-bit Leech addresses to this palette
   via the 2×4×8×32 = 2048 cell bridge (2 hemispheres × 4 MOG
   quadrants × 8 octad bits × 32 subpalette indices).

4. **Per-object k-arm**: instead of one global k-NN, segment the grid
   into objects and run a k-arm per object.  Different objects can
   receive different transformations.

5. **GLM as language machine**: use the lingo chat to DESCRIBE the
   task in geometric language, then TRANSLATE the description into a
   transformation.  Currently the chat is a trace; it should drive
   generation.

6. **HDRB as generative primitive**: currently HDRB is a signature.
   It should also generate — e.g., "the train signature is
   harmonic-dominant, so prefer recolour-like candidates".

7. **144 = 12×12 pairwise angular sectors**: when moving data through
   Time, the 12 angular sectors of Golay (one per message bit) have
   144 pairwise interactions.  Use this as the relational space for
   temporal transformation.

These are the leads to follow.
