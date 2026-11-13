# LEECHLEAN_STUDY — the supplied `leechlean` item, taken through the intake

## Tier 0 — the coarse read

**Question.** Does the supplied item `leechlean` — the recurring parts of the
repository's Lean development mapped to exact Leech-lattice addresses, with a
byte-exact address-stream codec, the Lambda/2Lambda coset layer, error
correction of corrupted address streams, the library lattice-graph and the
move algebra d = B − A — hold up when it is tested inside the full GLM
environment, and does taking it in let the GLM answer questions about its own
Lean development that it currently refuses?

**Verdict.** Yes. Tested inside the full GLM environment the item holds: its engine agrees with the substrate everywhere its 37-check battery cross-checks it, its codec is byte-exact over the repository's actual Lean tree (442 of 442 files through the 442-file codebook), its correction re-measures at 100% detection with 0 false alarms and 97.3-100% correction, and taking it in lets the GLM answer questions about its own Lean development that it refused before -- with the move model's advantage reproduced live.

**Deciding figure.** 15 of 15 questions answered right and 0 wrong through the tool leechlean surface, against 0 of 15 through the GLM without it; 6 of 6 negative controls refused or left alone; and on the 30-file leave-one-file-out sample the move model 51.6% against the part model 42.5% greedy top-1 (+9.1 points)

**Recomputed by.** `glm_universal.reasoning.leech_lean_study.leech_lean_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 11 November 2026 by `python3 -m glm_universal.intake scaffold leechlean` (directive D22). Every passage still marked as to be written is filled in, and the marks of §3 fixed, before any code of the round exists; the intake's measured gate refuses the study while any is left.*

## 0. What this document is

A **pre-registration**, now taken: the marks of §3 were fixed before any port code existed, and this document records both the declaration and the outcome of §8.

The item is [`source_material/ToDo/leechlean`](../source_material/ToDo/leechlean) (kind: code); its record is `leechlean` in [`source_material/INTAKE.yaml`](../source_material/INTAKE.yaml), where it stands at *triaged*.

This round takes the item through the intake in this sandbox as far as the
evidence honestly reaches: the item's tests are run against the GLM package and
the repository's own Lean tree (Q1), its finite claims are proved in Lean files
that are **compiled standalone under the pinned toolchain
`leanprover/lean4:v4.28.0`** (Q2 — a full `lake build` with Mathlib is not
possible in this sandbox, so the repository's own *absorbed ahead of the build*
route is used, exactly as for `glm_wheels_bundle` and `Rule30_GLM_Study`), and
its help is measured through a new `tool leechlean` query surface against the
GLM without it (Q3). The port is pure Python over the substrate's exact
machinery — the package has no numpy, and the port does not add one.

## 1. What the item offers, and what this round takes

The item offers: the recurring parts of a Lean development mapped to
Leech-lattice addresses — an exact Leech engine built from the substrate's own
Golay parity block B (4096 codewords, 759 octads, 196,560 minimal vectors,
the norm-48 shell census), a part→address codebook (39,992 parts: 29,422
token, 10,421 bigram, 63 frame, 86 tactic parts; 0 collisions; one bit of
surprisal = 4 units of Leech energy, Pearson r = 0.897 over undisplaced
parts), a byte-exact address-stream codec (442/442 corpus files round-trip),
the Lambda/2Lambda coset layer (own Z-basis of det 2^36, the 2^24-class
census with the singular count 2^23 + 2^11), error correction of corrupted
address streams (100% detection, 0 false alarms, 96–100% correction under
jitter, single flips, minimal-vector slips and bursts), the library
lattice-graph (29,422 parts joined by 80,375 edges with 55,269 frame contexts)
with continuation queries and on-the-fly addressing of new parts, and the move
algebra d = B − A with the class homomorphism onto Lambda/2Lambda (80,361
distinct moves carry all 1,487,183 ticks; the recorded head-to-head:
predicting the next move 45.8% vs the next part 40.6% greedy top-1,
leave-one-file-out).

What this round takes: **the part→address codebook as an addressing of the
GLM's own Lean development, the move algebra as a measured reasoning primitive,
the correction layers as a verification instrument, and the library graph as a
continuation surface** — all as one `tool leechlean` query surface and one
staged module set, `reasoning/leech_lean*.py`, written in pure Python over the
substrate's exact machinery (`substrate/leech2.py`, `substrate/mog.py`,
`reasoning/analogy.py`) and the item's bundled data. The engine is *not*
re-implemented: the substrate already carries the Golay code, the Leech
membership predicate, the Lambda/2Lambda class map with its type-2 table and
the exact nearest-point decoder, and the item's own battery
(`tests/test_leechlean_in_glm.py`, this round's Q1 instrument) cross-checks
every one of the item's numpy implementations against those substrate modules
before anything is taken.

What this round leaves: the item's bulk-build pipeline (rebuilding the
codebook from a Lean tree, the PPMI/SVD direction embedding, the fingerprint
module, the eight-teen report figures and the four docx reports). They stay
in the item folder, byte-identical as supplied; nothing of the round edits
them.

## 2. The questions

* **Q1.** Do the item's own tests pass where it stands — in the full GLM
  environment, not in isolation? The instrument is the item test
  `item:tests/test_leechlean_in_glm.py` (37 checks: the Golay engine against
  `substrate/mog.py`, membership and the decoder against
  `substrate/leech2.py` and `reasoning/analogy.py`, the coset layer, the
  codebook, the codec over the repository's actual `src/lean` tree,
  correction, the move algebra, the library graph), plus the item's four
  demos (`item:demo/...`).
* **Q2.** Are its finite and arithmetical claims proved in Lean (§5)?
* **Q3.** Does taking it into the GLM help, on a figure measured against the
  GLM without it (§8)?
* **Q4** (the item's own). Is the item's engine the substrate's engine — the
  parity block, the 4096 codewords, the 759 octads, the membership predicate,
  the nearest-point decoder, the class map — agreeing everywhere it is
  cross-checked?
* **Q5** (the item's own). Is the codec byte-exact on the GLM's actual Lean
  development as it stands today, not only on the 442-file corpus the
  codebook was built from?
* **Q6** (the item's own). Does the correction layer hold up on re-measurement
  (100% detection, 0 false alarms, at least 96% correction)?
* **Q7** (the item's own). Does the move algebra recompute from the bundled
  library graph exactly as recorded (80,361 moves, 63,257 classes, the class
  law, the well-defined pairing)?
* **Q8** (the item's own). Does the library graph answer queries —
  continuation, the universal core, the frame attestation of a part?
* **Q9** (the item's own, the mechanism). Does the move model beat the part
  model on the recorded protocol (greedy top-1, leave-one-file-out) —
  re-measured live on a pre-registered sample inside the GLM environment,
  not only read from the item's recorded `exp_moves.json`?

## 3. The marks, declared before the code

| Mark | What is measured | Met when |
|---|---|---|
| I1 | the item's named tests, in the full GLM environment | every named test passes: the 37-check battery `item:tests/test_leechlean_in_glm.py` and the four item demos, recorded by `advance leechlean tested`, and after the port the staged tests of §7 as well |
| I2 | the Lean obligations of §5 | every named Lean file is in the build tree, imported by `AxiomAuditAll.lean`, and compiles standalone under the pinned toolchain `leanprover/lean4:v4.28.0` with no `sorry` and no new axiom (this sandbox has no Mathlib, so the full `lake build` is the owner's to run: the absorption is ahead of the build, exactly as for `glm_wheels_bundle`, and every answer that rests on the item says so) |
| I3 | the help it gives | the criterion of §8: at least 12 of the 15 pre-registered questions answered right and 0 wrong through the `tool leechlean` surface, against 0 of 15 through the GLM without it; every negative control refused or left alone; and the move model reproduces its advantage over the part model on the pre-registered sample of §8 (at least +3 points greedy top-1) |
| I4 | no regression | after absorption the package tests that cover the touched surfaces pass — `tests/test_figures.py`, `tests/test_connected_two.py`, and the three new test files of §7 — and `corpus --check` holds |

## 4. Controls

* **The GLM without the item, on the same frozen inputs**: the 15 questions of
  §8 asked through the same routing with the tool module absent — the tool's
  lazy import is the same refusal pattern as `tool rule30`'s
  (`reasoning/hypothesis_tools.py`), so the baseline is a real refusal, not a
  degraded answer.
* **Negative controls** (each must be refused or left alone, never answered
  anyway): a part that is not in the codebook; a file path that does not
  exist; a continuation asked of a part the library has never seen; a
  "verify this proof" overclaim (the library's attestation is syntactic and
  must say so, never claim a proof); a corrupted stream offered as clean
  (must be flagged, not passed); a request to prove something (the tool
  proposes and checks, it never proves).
* **The item's own recorded experiments** (`data/exp_*.json`) stand as the
  cross-check for every recomputed figure: the battery re-derives the
  repertoire, the class occupancy, the library counts and the correction
  rates from the bundled data and must land on the recorded numbers.
* **Honest labelling**: every graph continuation is a proposal labelled
  unverified; every answer that rests on an item absorbed ahead of the build
  carries the ahead-of-build note; no float reaches a figure.

## 5. Lean obligations

The finite claims a Lean file must prove, in `IntakeChecks/` (compiled
standalone under `leanprover/lean4:v4.28.0`, core only — no Mathlib in this
sandbox; `AxiomAuditAll.lean` imports them, and the owner's
`scripts/rebuild_lean.sh` has to confirm them):

* `IntakeChecks/LeechLeanGolay.lean` — the substrate's parity block B itself:
  the generator `[I_12 | B]` has exactly 4096 distinct codewords, every weight
  lies in {0, 8, 12, 16, 24}, exactly 759 words have weight 8 (the octads),
  and the weight enumerator is exactly {0: 1, 8: 759, 12: 2576, 16: 759,
  24: 1} — the code the whole addressing rests on.
* `IntakeChecks/LeechLeanCodec.lean` — the addressing itself on real data: the
  Leech membership predicate (one parity, Golay supports mod 4, sum = 4m
  mod 8) defined over the same B, decided for every address of a fixed
  48-part slice of the actual codebook (the literal addresses of the 442-file
  corpus's 48 most common parts), the slice injective (distinct addresses),
  and the codec's round trip on a literal tick slice of the sample file: the
  address stream decodes through the codebook slice to exactly the original
  part sequence.

Everything else (the class map, the decoder's optimality, the correction
rates) is measured by the Python instruments of §7 against the substrate,
which already carries the proofs it claims (`Address.lean` for the
declaration-level quantiser the item extends).

## 6. What this round does not do

* It does not rebuild the codebook or the direction embedding: the bundled
  codebook (39,992 parts, built from the 442-file corpus) is taken as the
  item's data, cross-checked, not regenerated.
* It does not run `lake build`: Mathlib is not available in this sandbox. The
  Lean files of §5 are compiled standalone with the pinned toolchain, the
  absorption is ahead of the build, and the owner's `rebuild_lean.sh` +
  `confirm-build leechlean` close it.
* It does not add numpy or scipy to the package: the port is pure Python
  over the substrate's exact machinery, at the cost that stream-scale
  operations are bounded (the tool verifies and corrects the streams it is
  asked about, not the whole corpus at once).
* It does not claim the graph's continuations are proofs: they are
  attestation-weighted proposals, labelled unverified, and the overclaim
  control of §4 holds.
* It does not touch the Griess algebra beyond the class layer: the 196,884
  dimensions stay what the item's README says — the computable fragment is
  the class map, the pairing and the convolution.

## 7. Files

* The item, `source_material/ToDo/leechlean` (as supplied; the round adds only
  `tests/` and `staged/`): `leechlean/` (14 modules), `data/` (the codebook,
  the library core, the recorded experiments), `demo/` (the four demos and
  their outputs), `docs/` (the four reports), `figures/`, `README.md`, and
  this round's `tests/test_leechlean_in_glm.py` — 37 checks, the Q1
  instrument.
* The study: this file and `LEECHLEAN_STUDY.yaml`.
* The port (staged in the item, installed at absorption):
  `staged/src/glm_universal/reasoning/leech_lean.py` (the engine adapter:
  codebook, lattice checks over the substrate, moves, correction sieve,
  library), `staged/src/glm_universal/reasoning/leech_lean_tools.py` (the
  `tool leechlean` answer functions), `staged/src/glm_universal/reasoning/
  leech_lean_study.py` (the §8 measurement and this Tier 0's recompute),
  with `staged/src/glm_universal/reasoning/_data/leech_lean_core.json.gz`
  (the library graph, derived from the item's `data/library_core.npz`, pure
  JSON so the package needs no numpy) and staged tests
  `tests/test_leech_lean.py`, `tests/test_leech_lean_tools.py`,
  `tests/test_leech_lean_study.py`.
* The package wiring (this round's edits): the `Tool("leechlean", ...)`
  entry, its wrapper and English routes in `runtime/toolbox.py`; the
  `MEASUREMENT_ONLY` declaration for the study module; the tool-kind
  evaluation cases in `evaluation/cases.py`.
* The Lean: `src/lean/RequestProject/GLM/IntakeChecks/LeechLeanGolay.lean`,
  `src/lean/RequestProject/GLM/IntakeChecks/LeechLeanCodec.lean`, imported by
  `AxiomAuditAll.lean`.
* The intake record: `source_material/INTAKE.yaml`, id `leechlean`.

## 8. The measurement

**Pre-registered protocol** (fixed before any port code exists). The instrument
is `glm_universal.reasoning.leech_lean_study.leech_lean_report`, run in the
scratch view against the staged code, and re-run from the installed package at
absorption:

1. **The 15 questions**, asked through the `tool leechlean` surface (the real
   dispatch, in process), each graded right/wrong/refused against fragments
   fixed from the item's own data before the first run: (1) the address and
   energy of the part `theorem` (energy 40, 6,725 uses); (2) the address and
   energy of `:=` (energy 20); (3) the address of the import word `Mathlib`
   (energy 76); (4) the Lambda/2Lambda class and class type of `theorem`'s
   address (type 2, the minimal-vector classes); (5) the file report for
   `RequestProject/GLM/Golay/Code.lean` — tick count, byte-exact round trip,
   on-lattice addresses, journey energy; (6) the move report for the same
   file — move count, the class types met, whether the composed move of the
   two most common moves is back in the repertoire; (7) the continuation
   query for `theorem` (the library's single attested continuation,
   `ws: `, 6,725 joinings); (8) the universal core — which parts occur in at
   least 400 of the 442 library files (18 parts, the micro-syntax);
   (9) how many parts the library holds at each granularity (29,422 token,
   10,421 bigram, 63 frame, 86 tactic); (10) the verification of the sample
   stream's corruption: a single ±1 flip detected through the parity
   congruence and corrected; (11) the clean stream passes with 0 false
   alarms; (12) the attestation of a part under a frame — `theorem` under
   its declaration frame, attested in hundreds of files; (13) the stitch
   query: a snippet with one genuinely new identifier gets a fresh Leech
   address on the fly and the projection is byte-exact; (14) the slip
   control: a minimal-vector slip is on the lattice, so the sieve alone
   misses it and the class syndrome catches it; (15) the energy law: the
   most common part (`ws: `, 526,563 uses, 8 units) sits on the one-bit
   sphere and the rare `Mathlib` (201 uses, 76 units) far out — one bit of
   surprisal = four units of Leech energy.
2. **The baseline**: the same 15 questions through the same routing with the
   tool module absent — the expected answer is 0 of 15, all refused.
3. **The negative controls** of §4 (six), each graded refused / left alone /
   answered-anyway.
4. **The mechanism, live** (Q9): the recorded head-to-head re-measured on a
   pre-registered sample — the 442 corpus files decoded through the codebook,
   30 of them drawn with the fixed seed 20261111, and for each a
   leave-one-file-out greedy top-1 model built over the other files twice:
   once predicting the next part from the previous part, once predicting the
   next move from the previous move. The bar is direction with a margin: the
   move model at least 3 points above the part model on the sample (the
   recorded full-corpus figures are 45.8% vs 40.6%).
5. **The regression check** (I4): the package tests named in §3, after the
   staged code is installed.

**Criterion.** at least 12 of the 15 pre-registered questions answered right
and 0 wrong through the `tool leechlean` surface, against 0 of 15 through the
GLM without it; every negative control refused or left alone; and the move
model at least 3 points above the part model on the sample.

**Taken 11 November 2026** (recomputed by
`glm_universal.reasoning.leech_lean_study.leech_lean_report`; the staged test
`tests/test_leech_lean_study.py` holds it to these figures).

**Result.** 15 of 15 questions answered right and 0 wrong through the tool leechlean surface, against 0 of 15 through the GLM without it; 6 of 6 negative controls refused or left alone; and on the 30-file leave-one-file-out sample the move model 51.6% against the part model 42.5% greedy top-1 (+9.1 points)

The per-question grades: all fifteen right (q1-q15), zero wrong; the baseline
without the tool: all fifteen refused, 0 answered. The negative controls: the
unknown part, the unknown file, the unseen continuation, the "prove"
overclaim and the Riemann request all refused; the corrupted stream offered
as clean flagged (40 of 40 ticks, not passed). The mechanism: on the
30-file leave-one-file-out sample the move model scored
51.6% greedy top-1 against the part model's
42.5% (42575 of
82419 against 36442 of
85603 ticks) -- the direction and the margin of the
item's recorded full-corpus head-to-head (45.8% against 40.6%), reproduced
live inside the GLM environment.

The marks: **I1 met.** -- every named test passes: the item's 37-check
battery and its four demos, and the three staged test files against the
staged code. **I2 pending one step.** -- both Lean files are in the build tree and imported by `AxiomAuditAll.lean`, and `LeechLeanGolay.lean` compiles standalone under the pinned toolchain `leanprover/lean4:v4.28.0` (verified, twice); `LeechLeanCodec.lean`'s standalone compile is the remaining step (the command is recorded in the intake record's next_step); the owner's `scripts/rebuild_lean.sh` still has to confirm both in the full build. **I3 met.** -- the criterion above, with margin:
15 of 15 against a bar of 12, and +9.1 points against a bar of +3.
**I4** is the closing step: after absorption the touched package tests
re-run (absorption itself re-runs every named test against the installed
package), and the corpus refresh with `tests/test_figures.py` follows;
until then it is pending, not missed.
