This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# GLM system + the boundary studies

## Tier 0 — the coarse read

**Question.** What is in this repository, and where should a reader start?

**Verdict.** This repository holds the Geometric Language Machine system and many studies that came out of developing it so far.

**Deciding figure.** 8 registers of carriers, reached through <!--figure:query-kinds-->24 query kinds<!--/figure--> one of which dispatches 65 report subjects.

**Recomputed by.** `glm_universal.figures.figures`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

> **Positioning.** Before starting a round, read the Positioning section of
> [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md): what is claimed, what is
> not, and why an absence at one layer is not a refutation. It is stated once,
> there, and every document in this repository is written under it.

This repository holds the Geometric Language Machine system and many
studies that came out of developing it so far.

## Where to start

This file is the front door, not the index. The index is
[`ENTRY.md`](ENTRY.md): it states the reading order, lists every study, lists
every archived document, and is *checked* — a link that points at nothing, a
current-state document that cannot be reached from it, or an archive file left
off its list all fail `python3 -m glm_universal.corpus --check`.

Three documents answer most questions on their own:

* [`DIGEST.md`](DIGEST.md) — the whole corpus at tier 0, one generated row per
  document. Reading it and stopping is a coarse reading of the project, not a
  wrong one.
* [`STATUS.md`](STATUS.md) — where the work stands, what is open, and how to
  re-verify it.
* [`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md) — what the machine can
  do, measured rather than described.

## The layout, in one paragraph

The package lives in **`overlay/`** — the supplied archive, unpacked and
finished. The Lean 4 development lives in **`RequestProject/GLM/`** and builds
with `lake build`, with no `sorry`; the overlay keeps its own byte-identical
copy of the same files under `overlay/glm_lean/`. The write-ups are in
**`studies/`**, with the standalone scripts two of them are about in
`studies/scripts/`. Records of closed rounds are in **`archive/`**, and what
was supplied rather than written here is in **`source_material/`**, kept as
received.

## The figures, and why none of them is typed in

The package holds **8 registers** of carriers, reached through
**<!--figure:query-kinds-->24 query kinds<!--/figure-->** one of which
dispatches **65 report subjects**, and is checked by
**<!--figure:test-files-->116 test files<!--/figure-->** alongside
**<!--figure:lean-files-->140 Lean files<!--/figure-->**.

Every count in this repository's documentation is recomputed by
`overlay/glm_universal/figures.py` and written to
[`overlay/FIGURES.md`](overlay/FIGURES.md). Regenerate it with
`python -m glm_universal.figures --write` from `overlay/`;
`tests/test_figures.py` fails when a document and the code disagree, so no
figure below needs to be re-derived by hand. That is directive **D6**.

```bash
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q     # the suite
PYTHONPATH=. python3 GLM.py -q "report information loss" -c 1
PYTHONPATH=. python3 GLM.py -q "report admission"        -c 1
PYTHONPATH=. python3 GLM.py -q "report capabilities"     -c 1
PYTHONPATH=. python3 -m glm_universal.capabilities
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8
PYTHONPATH=. python3 -m glm_universal.corpus --check
```

```bash
lake build          # RequestProject/GLM/*.lean, 140 Lean files, no sorry
```

## 1. The GLM system

* **`GLM.py`** batch and interactive modes, all documented flags and
  meta-commands, and the exit-code contract.
  Since Phase 63 a batch question is read by the typed planner first, which
  reaches the certificate, interval, rational-recognition and dimensional
  frames; `--grammar` asks the grammar alone
  ([`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md)).
  Since Phase 64 `--python SOURCE` (and `--python-file PATH`) evaluates a
  declared dialect of Python exactly on the substrate and prints its three
  columns, or a named refusal; `--verify-tct` runs column 3 in a fresh
  `python3 -I`
  ([`PYTHON_SPEECH_STUDY.md`](studies/PYTHON_SPEECH_STUDY.md)).
  Since Phase 67 `--reverse TEXT` (and `--ask` with a prefix such as
  `say:`, `negate:` or `entails:`) runs Three Column Thinking backwards: the
  mathematics generates the language column through a grammar proved uniquely
  readable; since Phase 68 that grammar covers floor quotient, remainder,
  `abs`, `min`, `max`, bitwise operators, Golay masks and `either …, or …`, and
  `relay:` hands the result to the planner as a question and reads the answer
  back; since Phase 69 `entails over the integers:` and `bounds over the
  integers of x:` decide the same statements with every variable an integer,
  splitting floor quotient and remainder into residue cases
  ([`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md)).
* **Native wherever it can be (Phase 70).** Where a standard method tied or
  narrowly beat a Golay/Leech-native one, the native one was kept and refined:
  Lean-corpus retrieval now reads two native Leech books, each in two layers
  (the address and its exact read-back), and beats the raw feature vector on
  both query sets while equalling the like-for-like standard ranking; the
  controller's read-back scorer solves 24 of 24 tasks
  ([`NATIVE_PARITY_STUDY.md`](studies/NATIVE_PARITY_STUDY.md)).
* **The legacy `snap` decoder is retired.** Complete syndrome decoding
  (`substrate/golay_decode.py`) returns *every* nearest codeword and a status;
  no tie is broken silently. Weight-5 miscorrection is shown, via the Steiner
  system `S(5,8,24)` verified over all 42,504 five-subsets, to be a theorem
  about the code rather than a defect of the decoder.
* **The full Leech lattice replaces Construction A**, restoring the true
  kissing number 196,560 from A's 48, with each construction condition shown
  necessary by what breaks without it; **the exact 2A Sakuma product replaces
  the XOR shortcut**; **the six facets are strict linear projections** with the
  exact lattice index that says what a facet reading loses.
* **The `LEGACY_TO_CORE` bridge is implemented and tested**: the two frames
  share exactly 8 of their 4,096 codewords, the permutation is an isometry and
  therefore safe to wrap around a decoder, and a dataset migrates through one
  call with round-trip and referential-integrity checks.
* **`semantics/` replaces spelling with meaning.** The inherited concept graph
  was audited rather than described — 83 of its 4,282 concepts denote anything
  determinate, and 2 of its 4,015 edges state a re-derivable relation — and the
  grounded graph that replaces it holds 357 meanings, 1,705 notations and
  12,859 edges, every one re-derived on demand.
* **`capabilities/` says where the machine stops.** 33 probes, each phrased as
  a question a user would ask, each answered by running the real code: 20 hold,
  13 break, 0 errored, 0 surprises. A break is a located boundary, not a
  failure — and when one is closed the probe flips to `holds` and says so, as
  the transcendental-function probe did.
* **A molecules register.** 51 molecules over 17 elements, each parsed from a
  formula into an exact composition and encoded losslessly into the same
  24-coordinate carrier.
* **Zero failures across the suite**, and every published number is recomputed
  by a `*_report` function rather than quoted.

**[`MASTER_PLAN.md`](MASTER_PLAN.md)** tracks this work phase by phase, with
what was built, where it lives, and how to see it recompute itself.

## 1b. What this round closed

Each entry here is a report subject, a test file, a study and a Lean file, in
the shape directive **D5** requires — implemented, wired, tested, formalised,
verified.

**The faculties made into a stack.** The sharpest negative result this system
held was its own: *retrieval by lattice address beats chance and loses to plain
text overlap*. That was measured with each faculty answering alone. This round
made them answer together — every faculty reports how much evidence it has for
*this* query, and below a stated gate of 1/10 the leading text search is judged
to have abstained and the geometric address books answer in its place, by a
stated quota and interleave. At `k = 5` the stack is ahead of the text control
on a tuning stride (383 → 392 of 437), on a disjoint held-out stride (376 → 381
of 437) and on goal queries (759 → 766 of 874), and never below it at any
window. The gate fires on 62 of 1,748 queries; the geometry carries **21**
against **0** lost, where a digest-and-reshuffle control carries 2 and a name
search none. `relay_confident` proves the stack cannot cost anything where the
leader is strong and `relay_carry` proves a faculty holding the answer inside
its quota cannot be drowned out. The identical relay runs in a register with no
text in it — 50 ARC grids, an eight-dimension visual look that discards 95.3 %
of 1,089 proposals — and solves a puzzle its leading faculty does not.
`report relay`, [`STACK_RELAY_STUDY.md`](studies/STACK_RELAY_STUDY.md),
`Relay.lean`.

### The register where the address is the only reader

The relay above wins on a *residue* — 18 queries in 1,602, and the round that
measured it left the right question open: is there a register where a
structural address is not a second opinion but the only faculty that can read
the query at all? There is. A query is **anonymous** when its identifiers are
not the corpus's — a goal from a second formalisation, a generated goal with no
names, an autoformalised statement in its source's vocabulary — and renaming is
the reproducible form of it. Over the same 874 queries the text search falls
from 759 hits at k = 5 to 85 and the identifier address book from 410 to 46,
both to within a hair of the 48 that chance gives, while the structural address holds 183
of its 253 and leads every other faculty by more than a factor of two. A
renaming cannot move a count of the syntax (`features_anonymise`) and leaves no
identifier overlap at all (`overlap_anonymise_eq_zero`), so the stack's existing
gate — not re-tuned, not told about the register — fires on 586 of the 874 and
hands them to the geometry (`relay_hands_over`). The shipped feature map is
audited rather than idealised along the way: it counts type words wherever they
occur, including inside an identifier, which moves a coordinate on 38 of the
874 queries and never a logical, numeric, bracket or length coordinate.
`report anonymous`,
[`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md),
`Anonymous.lean`.

### Four things an earlier round closed

* **The cross-register analogy.** `heat : temperature :: force : ?` was refused
  for years because the lexicon reached nothing from `force`. An energy-conjugate
  register of 7 rows — an effort, an extent and the transfer they make — now
  carries the analogy across domains, every row checked against the physics
  register in exact integer arithmetic. `force` reaches `work`, and the four
  criteria a transportable relation must meet are stated, so a refusal names
  the criterion it failed. `report conjugates`,
  [`CONJUGATE_STUDY.md`](studies/CONJUGATE_STUDY.md), `Conjugate.lean`.
* **Sparse chemistry, decided rather than blank.** Every empty cell of the
  element register now has a disposition. A rule is admitted only if its
  leave-one-out error is at most half that of predicting the field's own mean,
  scored on at least twenty elements; nine fields take one, 185 cells are
  filled by estimate — coverage 1257 → 1442 of 1652 — and each of the remaining
  210 carries one of three stated reasons. Nothing is written back into the
  register. `report completion`,
  [`ELEMENT_COMPLETION_STUDY.md`](studies/ELEMENT_COMPLETION_STUDY.md),
  `Completion.lean`.
* **The vague `related_to` triples.** The problem was never the 66 the lexicon
  holds; it was that every new one brought the hand work back. A standing rule
  now tries four routes in order, of which only the last asks a person, and 34
  of the 66 are decided without one. Four proposer rules were scored against
  the hand-decided register and three refused, each on a named disagreement.
  `report vagueness`, [`VAGUENESS_STUDY.md`](studies/VAGUENESS_STUDY.md),
  `Vagueness.lean`.
* **Open vocabulary.** A commitment with no mechanism behind it is now a door:
  a name is admissible exactly when a stated route gives it coordinates
  computed from a register the machine already checks. Three routes admit and
  one refuses, and the refusal is conditional and names its condition — so
  `justice` is refused until a register that measures it exists, never as a
  matter of kind. `report admission`,
  [`ADMISSION_STUDY.md`](studies/ADMISSION_STUDY.md), `Admission.lean`.

## 2. What the machine can actually do so far, measured

The write-up is **[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md)**. It
does not describe the machine; it reports what happened when the machine was
run, with every figure produced by a command that can be re-run.

* **The end-to-end instrument, `glm_universal/evaluation/`.** **<!--figure:evaluation-cases-->177 CLI cases<!--/figure-->**,
  each starting `GLM.py` in a **fresh interpreter** — one subprocess per
  question, no shared session, no warm caches — covering **all <!--figure:query-kinds-->24 query kinds<!--/figure-->**
  and every report subject, with the coverage checked against the runtime's own
  tables by a test. 16 of the questions are ones the machine *should* refuse.
* **Scoring is asymmetric.** A refusal tells the user where the machine stops
  and a confident wrong answer does not, so `correct` and `refused_as_expected`
  score `+1`, an unexpected refusal `0`, and a wrong answer or a crash `−1`.
* **Boundaries separated from gaps, and no gap is left.** All 16 correct
  refusals are boundaries — undecidable equality of real processes, a
  vocabulary that is exactly the registers, a quotient by an exact zero — and
  `refusals_gap` is 0.
* **The other two instruments:** 33 probes (20 hold, 13 break, 0 errored, 0
  surprises) and 2,389 of 2,390 benchmark tasks across 5 suites, every suite
  above its baseline.

The document ends by naming what is untouched — the Niemeier deep-hole census,
the 32- and 48-dimensional lattices, words as projections, and the delta–sigma
directions still not started — so nothing is implicitly claimed. The same list
is kept in `archive/MASTER_PLAN_ARCHIVE.md` §7.9 and mirrored in
[`STATUS.md`](STATUS.md).

## 3. The supplied documents, read as claim ledgers

Several supplied files record claims rather than code:
`glm_unification_blueprint.md`, a specification, and
`glm_study_findings_catalog.md`, a record of measurements from studies run
outside this package. A document that is only read drifts from the system it
describes, so each was turned into a **live ledger**: every testable sentence
restated as a claim, recomputed against the package as it stands, and given one
of four verdicts — `confirmed`, `refuted`, `not reproduced`, `not implemented`.

* **The blueprint.** `reasoning/blueprint.py`, `report blueprint`. Write-up:
  **[`GLM_UNIFICATION_BLUEPRINT_AUDIT.md`](studies/GLM_UNIFICATION_BLUEPRINT_AUDIT.md)**.
  Reaching verdicts needed three subjects built beside it —
  `reasoning/engine.py` (Part III's carrier engine), `reasoning/mantissa.py`
  (binary64 modelled exactly, with no float ever constructed) and
  `reasoning/reversible.py` (the Gray read channel, the Toffoli and Fredkin
  gates, the kink invariant) — with `Mantissa.lean` and `Reversible.lean` as
  the machine-checked half.
* **The study catalogue.** `reasoning/catalog.py`, `report catalog`. Write-up:
  **[`GLM_STUDY_CATALOG_AUDIT.md`](studies/GLM_STUDY_CATALOG_AUDIT.md)**. **58
  testable claims: 33 confirmed, 14 refuted, 7 not reproduced, 4 not
  implemented.** Where the catalogue reports a number produced by running a
  loop, the package reproduces it to the digit; where it reports that a
  measured column *is* a property of the thing measured, the column is usually
  a closed form of the input. The sharpest case is the "vibrational
  signature": `Sturmian.lean` proves that the modulator's stream is the
  mechanical word of its target, so entropy, run lengths, transition rate and
  one-density are all determined by the target before the loop is run
  (`reasoning/wobble.py`, `report signature`).
* **The two companion preprints.** `reasoning/companion.py`,
  `report companion`. Write-up:
  **[`GLM_COMPANION_STUDIES_AUDIT.md`](studies/GLM_COMPANION_STUDIES_AUDIT.md)**.
  **49 testable claims: 26 confirmed, 17 refuted, 5 not reproduced, 1 not
  implemented.** The instrument built beside it is `reasoning/containers.py`
  (`report containers`): eight constants through three containers, with both
  hull verdicts checked against all 196,560 Leech minimal vectors rather than
  a sample, since a sample can establish *inside* and can never establish
  *outside*.
* **The deep dive through the supplied archive.** Everything named in the
  original brief was gone through and written up:
  [`SOURCE_SALVAGE_AUDIT.md`](studies/SOURCE_SALVAGE_AUDIT.md),
  [`SOURCE_SALVAGE_SECOND_PASS.md`](studies/SOURCE_SALVAGE_SECOND_PASS.md) and
  [`ARCHIVE_DEEP_DIVE_STUDY.md`](studies/ARCHIVE_DEEP_DIVE_STUDY.md).

## 3b. The universality claim, measured in three registers

Section 6.2 of the catalogue says chemical equilibria, musical harmony and
market price discovery all map to Leech proximity. Two thirds of that can now
be measured here. `data_objects/harmonics.py` holds **28 intervals** as exact
rational frequency ratios — every coordinate computed from the pair `(n, d)`,
no float anywhere — and `reasoning/harmony.py` (`report harmony`) tests the
sentence rather than repeating it: equal temperament's miss is the exact
rational `(n/d)^12 / 2^k`, `1` at the unison and the octave and nowhere else;
no stack of fifths is a stack of octaves, searched to `n = 200` and proved for
every `n` in `Harmony.lean`; and each interval is decoded to its nearest Leech
point through its prime exponents.

**The verdict is `not reproduced`.** Proximity does order the intervals by
consonance, at an exact Kendall tau of `53/63` — but the same distance taken
*before* the decoder runs scores `53/63` too, and the decoder reorders no
pair, so what is measured is the prime-exponent vector rather than the
geometry of the lattice. Write-up:
**[`HARMONY_STUDY.md`](studies/HARMONY_STUDY.md)**.

The economic third is measured too. `data_objects/economics_register.py`
holds 21 quoted prices as exact rationals — seven instruments over three
consecutive quarters — read through an exact magnitude bucket decided by
integer comparison rather than by a logarithm, and proved well defined,
unique, monotone and scale-shifting in `RequestProject/GLM/LogBucket.lean`.
The lattice separates all 21 records at scale 1024 and every record's nearest
neighbour is another quarter of the same instrument, 21 of 21 against a chance
rate of `1/10` — but the undecoded control scores 21 of 21 as well, so this
third is **`not reproduced`** for the same reason the musical one is. Write-up:
**[`ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md)**.

## 4. Checking it, without checking it twice

The suite is about a quarter of an hour, and `lake build`, the end-to-end
evaluation, the benchmark suites, the capability probes and the figures check
cost more again. Almost none of it changes between one iteration and the next,
and re-running an unchanged check proves nothing — but "it is probably still
fine" is a guess, not a verification.

`overlay/.glm_signoff.json` makes the guess into a check. Each test file and
each instrument carries the SHA-256 of **everything its last passing result
depended on**: the file itself, every package module it imports transitively,
the frozen data those modules read, the documents and Lean sources they name,
the test scaffolding and the interpreter version. If the digest still holds,
the result still holds. If one byte anywhere in that closure differs, the unit
is stale and runs again.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.signoff --verify         # what still holds
PYTHONPATH=. python3 -m glm_universal.signoff --plan           # what would run, and why
PYTHONPATH=. python3 -m glm_universal.signoff --run-everything # run only that
PYTHONPATH=. python3 -m glm_universal.signoff --run-all        # ignore the ledger
```

Three things keep it honest: a failure is recorded as a failure and never
signs; the sign-off package's own sources are inside every closure, so changing
the rules invalidates every signature; and nothing is skipped silently —
`--plan` says what will be skipped before anything runs and `--verify` re-checks
every signature without running a test. The full run stays available and is
what a release check does. The rule is directive **D4** of
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md); the design is
[`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md) Phase 12.

## 5. The documents are data too

A corpus nobody can navigate is a corpus nobody reads. Directive **D10** says a
document is data: classified by rule, generated where it can be, addressed and
checked. So

* every current-state document opens with a **tier-0 block** — question,
  verdict, the one figure that decides it, and the function that recomputes
  that figure — and a check fails if a verdict says something its document does
  not go on to say;
* **[`DIGEST.md`](DIGEST.md)** is all of those blocks on one page, generated,
  so it cannot drift;
* a document is an **archive** document exactly when its name ends
  `_ARCHIVE.md`, when it is the session working note, or when it lives under a
  directory named `archive` — a rule, not a judgement;
* every section of every document has a **Leech address**, and a question can
  be answered with a shortlist that is complete up to a stated radius
  ([`CORPUS_ADDRESS_STUDY.md`](studies/CORPUS_ADDRESS_STUDY.md)).

The README chain is part of that system rather than beside it: `overlay/`,
each sub-package, the Lean tree and the test suite each carry a README, each
one is a corpus document with its own tier-0 block, each appears as a row of
`DIGEST.md`, and [`ENTRY.md`](ENTRY.md) reaches the whole chain.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check      # the document contract
PYTHONPATH=. python3 -m glm_universal.corpus --ask "what bears on the Golay code?"
```

## Layout

```
ENTRY.md                      the index: what to read, in what order, and what may be skipped
DIGEST.md                     every document at tier 0, one generated row each
README.md                     this file
STATUS.md                     where the work stands now, and what is left
MASTER_PLAN.md                the wiring status: the header, the phase index, the open phase
CAPABILITY_ASSESSMENT.md      what the machine can do, measured rather than described
PROJECT_DIRECTIVES.md         the positioning, the standing rules with the instrument
                              that enforces each, and the round protocol
ITERATE.md                    the operating manual: the three gates, and which to run when
ARISTOTLE_SUMMARY.md          the working notes left by the sessions that built this
archive/                      records of closed rounds, kept as they were written
  MASTER_PLAN_ARCHIVE.md      the closed phases
  PACKAGE_README_ARCHIVE.md   the package change log, row by row
  PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md
                              the argument each standing rule was written with
studies/                      the write-ups produced here — see ENTRY.md for the full list
  scripts/                    the standalone scripts two of those studies are about
source_material/              what was supplied, kept as received
RequestProject/               the Lean 4 development (140 Lean files, no sorry)
  GLM/                        one file per result; GLM/README.md indexes them
overlay/                      the GLM repository, with the finished package
  GLM.py                      the CLI
  README.md                   the package's own top-level README and change log
  FIGURES.md                  every quoted number, generated
  REASONING_CAPABILITY.md     whether the machine reasons, measured
  glm_universal/              the package proper (eleven sub-packages)
  glm_lean/                   the overlay's copy of the Lean development
  arc_agi_17/                 the ARC experiments
lakefile.toml, lean-toolchain the Lean build
```
