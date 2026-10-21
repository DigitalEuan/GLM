# Status


## Tier 0 — the coarse read

**Question.** What is still to do, where does the work stand in one screen, and how is a run closed?

**Verdict.** This is the To-Do list: what is open, sharpest first, with the closed record moved out to the archive and the standing description of the system moved to `SYSTEM.md`.

**Deciding figure.** Every instrument in the table at the head of the document reports its own result on demand.

**Recomputed by.** `glm_universal.signoff.ledger.suite_totals`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 21 October 2026.*

> **Positioning.** Before starting a round, read the Positioning section of
> [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md): what is claimed, what is
> not, and why an absence at one layer is not a refutation. It is stated once,
> there, and every document in this repository is written under it.

## How to work in this repository

**Commit after each completed step, not once at the end** (directive D1). A
step is anything that leaves the tree working — one document reconciled, one
test added, one lemma proved.

This is the To-Do list: what is open, sharpest first, with the closed record moved out to the archive and the standing description of the system moved to `SYSTEM.md`.

**This document is the To-Do list, and only that.** It holds what is open
(§2), the instrument table in one screen (§1) and the close (§3). It does not
hold the record:

* what the system **is** — the standing description, the full instrument
  table and the re-verification commands — is [`SYSTEM.md`](SYSTEM.md);
* what each round **did** is [`MASTER_PLAN.md`](MASTER_PLAN.md) (and
  [`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md));
* the running account this document used to carry, round by round up to
  Phase 110, and the candidate list as it was named, are in
  [`archive/STATUS_ROUNDS_ARCHIVE.md`](archive/STATUS_ROUNDS_ARCHIVE.md);
* how to run a round is [`ITERATE.md`](ITERATE.md).

**Keeping it short.** When a round closes, *delete* the To-Do line it took
(its record goes to `MASTER_PLAN.md` and its study), add the lines the round
left as new To-Do lines, and replace the "Just closed" paragraph below. Never
stack a second "round before" paragraph here: that stack is what made this
document three thousand lines long.

**Every run updates the paper.**
[`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md) is the record of the
GLM as a whole and is kept up to date in every development run (the owner's
standing instruction; it is a row of the close checklist, `ITERATE.md` §4.1).

**Where the files are.** The Lean development lives in one place only,
[`overlay/glm_lean/RequestProject/`](overlay/glm_lean/RequestProject/GLM/README.md)
(`lakefile.toml` sets `srcDir = "overlay/glm_lean"`); there is no
`RequestProject/` folder at the repository root, so a path written as
`RequestProject/GLM/X.lean` in a record means
`overlay/glm_lean/RequestProject/GLM/X.lean`. The studies are in
[`studies/`](studies/), the Python package in `overlay/glm_universal/`. A file
audit after Phase 158 (the owner asked whether
[`FRICTION_STUDY.md`](studies/FRICTION_STUDY.md),
[`OSCILLATOR_JUNCTION_STUDY.md`](studies/OSCILLATOR_JUNCTION_STUDY.md) and Lean
files had gone missing) found every file present: 232 Lean files (231 under
`GLM/` plus `Main.lean`), all building with `lake build` and 0 `sorry`, and
all 160 study documents. What was wrong was 261 rows of the Properties table
still pointing at the old root path `RequestProject/GLM/…`; they now point at
`overlay/glm_lean/RequestProject/GLM/…`.

**Starting a new round? Read [`ITERATE.md`](ITERATE.md) §0, then §2 below —
§2.0 points to the owner's plan for the next runs,
[`source_material/GLM_19OCT26_1.md`](source_material/GLM_19OCT26_1.md).**

**Just closed: Phase 175** (21 October 2026) — **the owner's pipeline kit in
the GLM** ([`PIPELINE_KIT_STUDY.md`](studies/PIPELINE_KIT_STUDY.md), record in
[`MASTER_PLAN.md`](MASTER_PLAN.md) "Phase 175"). The files of the
9-iteration pipeline study are in
[`source_material/GLM_Pipeline_Kit/`](source_material/GLM_Pipeline_Kit/README.md),
split back into their nine kit modules, seven Lean files, 40 scripts and 22 data
files. The kit's bridge, never run before, holds on the GLM's own substrate
(0 failures in 2,000 words); its seven Lean files build under
`GLM/PipelineKit/`; and `tool induce` induces a rule from demonstration pairs
of 0/1 grids or bit strings, keeping every operator hypothesis that fits —
the kit's permutations and mask, a region fill and a two-point path writer
(the kit's open items), and every two-step composition — and answers only when
they all agree. 0 wrong answers in 2,250 queries at a cost of 129 refusals;
the eager controls gave 12 and 19. `PipelineInduction.lean` (17 theorems)
proves the gate sound. 12 of 12 marks.

**Before it, Phases 173 and 174** (several open ties at once,
[`STACKED_DIALOGUE_STUDY.md`](studies/STACKED_DIALOGUE_STUDY.md); the answer
censuses guarded by what their answers quote, and the replay gate as a step of
the close, [`QUOTED_MEASUREMENTS_STUDY.md`](studies/QUOTED_MEASUREMENTS_STUDY.md)).

**Before them, Phase 172** (the open tie kept across turns;
[`RESUMED_DIALOGUE_STUDY.md`](studies/RESUMED_DIALOGUE_STUDY.md)): a question
stays open across unrelated turns; the adversarial battery at the `locate`
junctions; `report anonymous` pinned on its claim.

**Before it, Phase 171** (the evidence model in use;
[`EVIDENCE_IN_USE_STUDY.md`](studies/EVIDENCE_IN_USE_STUDY.md)): `GLM.py -q …
--result` and the evaluation's replay gate (`evaluation --replay`).

**Before it, Phases 167–170** (four parts of the owner's plan of 19 October
2026, §2.0): adversarial replies at the `nearest` ties
([`ADVERSARIAL_DIALOGUE_STUDY.md`](studies/ADVERSARIAL_DIALOGUE_STUDY.md));
the corpus confidence curve
([`CONFIDENCE_CURVE_STUDY.md`](studies/CONFIDENCE_CURVE_STUDY.md)); one
evidence and result model
([`EVIDENCE_MODEL_STUDY.md`](studies/EVIDENCE_MODEL_STUDY.md)); contextual
domain frames ([`CONTEXT_FRAMES_STUDY.md`](studies/CONTEXT_FRAMES_STUDY.md)).

**Before them, Phase 166** (the machine sums π;
[`PI_MACHINE_STUDY.md`](studies/PI_MACHINE_STUDY.md)): Machin's formula and the
arctangent series proved in Lean and run in GLM-BAT.

**Before it, Phase 165** (the Leech kissing number from the lattice's
definition; [`LEECH_KISSING_STUDY.md`](studies/LEECH_KISSING_STUDY.md)): the
minimal shell proved both ways and its 196,560 a theorem.

**Before it, Phase 164** (the Leech shells from the lattice's definition;
[`LEECH_SHELLS_STUDY.md`](studies/LEECH_SHELLS_STUDY.md)): the minimal shapes
proved, every shell counted from the Golay census, and the `llvq` tool's wrong
norm-12 entry replaced.

**Before it, Phase 163** (the machine works the tools out;
[`TOOL_MACHINE_STUDY.md`](studies/TOOL_MACHINE_STUDY.md)): no step of an
answered chain is carried, and the Leech kissing number is counted from the
Golay code's generator rows.

**Before it, Phase 162** (corpus source tiers; [`SOURCE_TIERS_STUDY.md`](studies/SOURCE_TIERS_STUDY.md)),
Phase 161 (the study ledger: every study as one
machine-readable row; [`STUDY_LEDGER_STUDY.md`](studies/STUDY_LEDGER_STUDY.md)), and
Phase 160 (the machine sorts: the 48 carried folds computed by
counting; [`FOLD_MACHINE_STUDY.md`](studies/FOLD_MACHINE_STUDY.md)), and
Phase 159 (thermomechanical friction: sintering ships;
[`THERMO_FRICTION_STUDY.md`](studies/THERMO_FRICTION_STUDY.md)), and
Phase 158 (the oscillator junction tried four ways;
[`OSCILLATOR_JUNCTION_STUDY.md`](studies/OSCILLATOR_JUNCTION_STUDY.md)), and
Phase 157 (five domain wheels with their junctions, and friction, the rest;
[`DOMAIN_WHEELS_STUDY.md`](studies/DOMAIN_WHEELS_STUDY.md),
[`FRICTION_TWO_STUDY.md`](studies/FRICTION_TWO_STUDY.md)), and Phase 156
(friction: what holds when the question moves).

Before those, Phase 155 (the corpus's definitions graded), Phase 154 (the corpus as what the GLM knows), Phase 153 (the
machine reads what it carries), and Phases 150, 151 and 152.

---

## 1. Where the work stands, in one screen

| instrument | command | result |
|---|---|---|
| test suite | `python3 -m pytest glm_universal/tests -q` | **<!--figure:suite-->5,397 tests across 181 of the 183 test files, 18,972 subtests, outside the document checks<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **<!--figure:evaluation-case-count-->223<!--/figure-->** cases — 0 confidently wrong, every refusal a `boundary` |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 surprises |
| Lean development | `lake build` (repository root) | <!--figure:lean-files-->253 Lean files<!--/figure-->, **0 `sorry`** |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the coverage claim of `ENTRY.md`, every generated block and every derived cache |

The package holds **<!--figure:registers-->8 registers<!--/figure-->** beside a 45-class comparison register,
**<!--figure:query-kinds-->28 query kinds<!--/figure-->** one of which
dispatches **<!--figure:report-subjects-->67 report subjects<!--/figure-->**, and 3 tasks. The Lean development is
addressed declaration by declaration: `reasoning/lean_address.py` gives each of
the <!--figure:lean-declarations-->5,893<!--/figure--> declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly <!--figure:lean-declarations-->5,893<!--/figure-->/<!--figure:lean-declarations-->5,893<!--/figure--> with 0 coordinate errors
(`report lean`). The other forty-odd instruments, each with its command and its
current figure, are the table in [`SYSTEM.md`](SYSTEM.md) §1.

---

## 2. To Do

Sharpest first within each group. Each line names the study section that
states the item in full; the bracketed names (`lattice item 6`, `track M`, …)
are the names earlier records use, kept so that a reference in a study or a
module docstring still finds its line. When a line is taken, delete it here and
record the round in `MASTER_PLAN.md`.

### 2.0 The owner's plan for the next runs — read this first

The owner's development plan of 19 October 2026 is
[`source_material/GLM_19OCT26_1.md`](source_material/GLM_19OCT26_1.md). It
sets the direction for the next several runs: take the next round from it
before anything else in §2. It is a supplied document, not a study, so it
states aims, not measured results. Check any claim it makes about the system's
current state against the studies before building on it. Its parts and the
lines of §2.1 they take over:

* **Part I, thermomechanical friction — taken (Phase 159,
  [`THERMO_FRICTION_STUDY.md`](studies/THERMO_FRICTION_STUDY.md)).** A, the
  governor, almost never acts; B, the prompt anchor, is steadier but not more
  accurate; C, sintering, ships. What it left is the new item 4.
* **Part II.1, one evidence and result model — taken (Phase 169,
  [`EVIDENCE_MODEL_STUDY.md`](studies/EVIDENCE_MODEL_STUDY.md)).** Every
  evaluation answer reads into one `Result` (`runtime/evidence.py`); the
  census found and repaired two column-3 replays. What it left is the new
  item 7 of §2.1.
* **Part II.2, the carried-value gaps — taken (Phase 160,
  [`FOLD_MACHINE_STUDY.md`](studies/FOLD_MACHINE_STUDY.md), and Phase 163,
  [`TOOL_MACHINE_STUDY.md`](studies/TOOL_MACHINE_STUDY.md)).** The folds,
  then the tool answers and verdict-dependent steps, are computed by the
  machine: no step of an answered chain is carried. What is left is item 2.
* **Part II.3, contextual domain frames — taken (Phase 170,
  [`CONTEXT_FRAMES_STUDY.md`](studies/CONTEXT_FRAMES_STUDY.md)).** *Which
  energy* and *which body drives the wave* are declared contexts a question
  may name; what is left is item 5.
* **Part II.4, a declared corpus confidence curve — taken (Phase 168,
  [`CONFIDENCE_CURVE_STUDY.md`](studies/CONFIDENCE_CURVE_STUDY.md)).** Sure,
  balanced and candidate modes declared on a calibration fold; definitions
  carry a quality description. What is left is item 3.
* **Part II.5, adversarial interactive testing — taken (Phase 167,
  [`ADVERSARIAL_DIALOGUE_STUDY.md`](studies/ADVERSARIAL_DIALOGUE_STUDY.md)).**
  Dialogue never promotes a carrier outside the head, proved for any replies;
  what is left is the new item 8 of §2.1. Item 1 stays postponed.

Every part of the plan has now been taken once. The next round starts from
§2.1 (Phase 171 took two lines of item 7; Phase 172 took two lines of item 8
and one of item 7; Phase 173 two more lines of item 8; Phase 174 two more
lines of item 7).
* **Part II.6, a machine-readable study ledger — taken (Phase 161,
  [`STUDY_LEDGER_STUDY.md`](studies/STUDY_LEDGER_STUDY.md)).** Every study is
  one row read from the files (`tools study-ledger --json`); what it left is
  the new bullet *the study ledger, the rest* in §2.2.
* **Part II.7, corpus source tiers reported separately — taken (Phase 162,
  [`SOURCE_TIERS_STUDY.md`](studies/SOURCE_TIERS_STUDY.md)).** Every corpus
  experiment is read on five tiers and on the written tier, the supplied tier
  and both; the confirmed reading is the measured policy; what it left is
  the new item 6 of §2.1.

When a part is taken, record it in `MASTER_PLAN.md` and its study as usual,
and mark it taken here. Leave the plan file as supplied.

**Standing rule: `source_material/` is the less reliable tier** (owner's note,
19 October 2026). As a corpus, what is under `source_material/` (older
scripts, supplied studies, the members of `GLM-main.zip`) is less reliable
than the documents, code and Lean written and checked in this repository.
Adapt every corpus-facing mechanism to that. Where things stand now:

* **Already tiered:** the document inventory and its checks
  (`corpus/inventory.py`) never walk `source_material/`. The knowledge
  corpus's `define`/`ask` readers rank a supplied or archived sentence below
  every written one except a stored data file (`knowledge/answer.py`,
  `source_rank`). The K8′ glossary terms are read from written Markdown
  only (`knowledge/study.py`, `bold_terms`).
* **Measured by tier, not yet tiered in use (Phase 162):** the counted model
  in `knowledge/model.py`, and everything built on it — continuation, the
  guarded predictor, `similar`, the word address, context sets, the friction
  respeller's vocabulary — still counts a `source_material/` sentence the same
  as a written one. `tools source-tiers` now reports the census (1,036 of
  2,268 documents, 46% of sentences, 39% of tokens in the supplied tier) and
  every corpus experiment written only, supplied only and both.
* **The declared way the supplied tier should count** (measured, not yet
  shipped): *admitted only as a candidate that written evidence must
  confirm* — the only one of the three declared policies that raises
  precision on written text; excluding it and down-weighting it both lose
  precision ([`SOURCE_TIERS_STUDY.md`](studies/SOURCE_TIERS_STUDY.md) §7.4).
  Until it ships, a corpus reading resting only on `source_material/` is
  reported as such, not as what the GLM knows. The same goes for retrieval
  from the older scripts: a result recovered from `GLM-main.zip` is a
  candidate until it is re-derived, tested or proved here.

**Standing rule: the supplied files stay as supplied** (owner's instruction,
18 October 2026). `source_material/GLM-main.zip` and the two supplied PDFs
are kept in the project folder exactly as they are, managed by the owner, and
out of version control (`.gitignore` keeps every `.zip` and `.pdf` out, with
a comment saying so). A clone of the repository therefore lacks them; the
documents that cite them cite files beside the repository, not in it. Nothing
under `source_material/` is edited, renamed or dated by a round.

**Standing rule: date every file a round creates or alters** (owner's
instruction, 18 October 2026; directive D17 in
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md)). A new file says
`Created <day Month year>`, an altered one `Last altered <day Month year>`,
in the file itself; a study also says when it was pre-registered and
measured. `python3 -m glm_universal.tools dates` lists every stamp and fails
on a bad one. Forward only; `source_material/`, generated documents and
stored data are exempt.

### 2.1 The next round — take one of these

1. **The question at the other three ties** (left by Phases 145, 146, 148
   and 150; *postponed by the owner* until more such ties accumulate as new
   domains are added, or a higher mechanism that carries them is found). Since Phase 150 the `locate` junction and the `nearest` tie put
   a question and read a reply. Three refusals at a tie still have no
   declared vocabulary:
   * the crowded zero cell of the address read;
   * the `report hole` ties;
   * the decoder's `classify` refusal.

   Giving one a vocabulary, and the reply its turn, changes answers the
   evaluation pins, so it needs a frozen-path comparison that declares the
   evaluation-set counts new cases move (`report language`, `report query
   escalation`, the discourse census).
   [`NEAREST_QUESTION_STUDY.md`](studies/NEAREST_QUESTION_STUDY.md) §7.4,
   [`ANSWERING_QUESTION_STUDY.md`](studies/ANSWERING_QUESTION_STUDY.md) §7.5.

2. **The machine's reading, the rest** (left by Phases 153, 160, 163, 164, 165 and 166).
   Since Phase 163 no step of an answered stepwise chain is carried, and
   since Phase 166 π is summed by the machine like `e`
   (`PI_MACHINE_STUDY.md`). Since Phase 164
   the Leech shapes are proved and every shell is counted from the Golay
   census (`LEECH_SHELLS_STUDY.md`), but only by the tool: GLM-BAT still
   counts only the minimal shell. Since Phase 165 the minimal shell is proved
   both ways and its 196,560 is a theorem (`LEECH_KISSING_STUDY.md`); the
   procedure's correctness for the shells `t ≥ 3` is still argued, not
   proved (the REM line cites `leech_kissing_number` since Phase 166); a
   kissing-number question costs about 164,000 machine steps (the census
   could be cached by digest); reals other than
   `π`, `e`, `√m` and tools other than the five computed stay carried. Which
   rows belong to a declared set is still the planner's (a membership file,
   `@<set>.<row>=member;`, would let the machine read it). A question read is
   membership, not position. The number-word junctions (`NUMBER_JUNCTIONS`)
   are a short declared list. The typed planner's other plan kinds (ordering
   and extremum, linear, Bezout, factorise, substrate facts) are not yet said
   as GLM-BAT.
   [`TOOL_MACHINE_STUDY.md`](studies/TOOL_MACHINE_STUDY.md) §7.4,
   [`FOLD_MACHINE_STUDY.md`](studies/FOLD_MACHINE_STUDY.md) §7.4,
   [`LEECH_SHELLS_STUDY.md`](studies/LEECH_SHELLS_STUDY.md) §7.3,
   [`LEECH_KISSING_STUDY.md`](studies/LEECH_KISSING_STUDY.md) §7.3,
   [`PI_MACHINE_STUDY.md`](studies/PI_MACHINE_STUDY.md) §7.3.

3. **The corpus, read more finely** (left by Phases 154, 155 and 168).
   Since Phase 168 the counted model has declared operating modes (balanced
   33.7% at 42.4% held out; sure 62.0% at 7.3%), but they are measured, not
   wired: putting them into `continue` and the guarded predictor, with a label
   saying which mode answered, changes pinned answers and needs a frozen-path
   comparison. The sure bar should be an absolute precision declared before
   it is measured (C3 missed on a ratio to an accuracy that moved between
   folds), and a calibration fold trained on as many documents as the
   held-out model would let coverage transfer (C1). Definitions carry a
   quality description (`confidence_curve.quality`), but strong answers agree
   with the held-out gloss only slightly more often than weak ones (4 of 15
   against 2 of 8): a grade that predicts agreement — context support alone,
   the source tier, or the squared cosine of context sets — is open, and
   `corpus --ask` does not print the description yet. The positional word
   address never puts a plural beside its singular (W3′: 6 of 1,100), and
   `similar` or the word address as the parser's *did you mean* needs a
   frozen-path comparison.
   [`CONFIDENCE_CURVE_STUDY.md`](studies/CONFIDENCE_CURVE_STUDY.md) §7.4,
   [`CORPUS_DEFINITIONS_STUDY.md`](studies/CORPUS_DEFINITIONS_STUDY.md) §7.4,
   [`CORPUS_KNOWLEDGE_STUDY.md`](studies/CORPUS_KNOWLEDGE_STUDY.md) §7.5.

4. **Friction, the fourth pass** (left by Phase 159). The self-made valley
   is a basin, not a loop: *the same way* is the continuation of 37 prompts,
   each entering it once, so a continuation scored by how many distinct
   prompts the corpus sends into it (an attractor census) is the next
   reading. The prompt anchor keeps 95.5% of the informative switches where
   the margins keep about 70%, at 6 final readings; whether it is the better
   steadiness trade needs a sample that does not shift with the corpus — a
   friction sample frozen by address would make every friction measurement
   reproducible across rounds. The sintered lexicon holds the four registers'
   names; units and structural words the parser reads but no register names
   are outside it, and the hazard it removed (a correct rare word respelt into
   a commoner one, 45 register words) applies to any rare word. Use beats the
   wrong company but loses to count; a declared share is not measured.
   `tests/test_figures.py` still fails on the suite sentence, which only
   `signoff --close` with pytest re-takes.
   [`THERMO_FRICTION_STUDY.md`](studies/THERMO_FRICTION_STUDY.md) §7.5,
   [`FRICTION_TWO_STUDY.md`](studies/FRICTION_TWO_STUDY.md) §7.7.

5. **The domain wheels, the rest** (left by Phases 157, 158 and 170).
   Since Phase 170 a question may name a declared context (*the energy is
   delivered over a time*, *stored in a capacitor*, *a rotating body drives
   the wave*, …), and *which energy* and *which body drives the wave* are
   answered. The contexts are six declared phrases read by the engineering
   surface only: reading them through the language descriptions, offering
   them at a `nearest` tie (*which energy is meant?*), saying the stored
   energy's reading in words, and declaring other couplings (a wave driving
   an oscillator, a generator driving an LC circuit) are open. The union
   census's code still reads its declaration more narrowly than its words,
   and the naive control should be taken wheel pair by wheel pair.
   [`CONTEXT_FRAMES_STUDY.md`](studies/CONTEXT_FRAMES_STUDY.md) §7.5,
   [`DOMAIN_WHEELS_STUDY.md`](studies/DOMAIN_WHEELS_STUDY.md) §7.5.

6. **The source tiers, in use** (left by Phase 162). The confirmed reading
   — the whole corpus's answer, given only when the written tier has counted
   it — is measured, not shipped: putting it into the continuation and the
   guarded predictor, with a label on every answer that rests on the supplied
   tier, changes answers the evaluation pins and needs a frozen-path
   comparison. `define` ranks a stored data file below the supplied tier, and
   four bold terms are answered from supplied sentences only because the
   written rival is a stored measurement quoting an earlier answer; whether a
   stored measurement should be a definition source at all is the same kind
   of change. The held-out rule (every fifth document of the sorted corpus)
   re-deals every later fold when one document is added early in the sort, so
   held-out figures are not comparable across rounds; folds by the digest of
   the path would fix that and re-take `corpus-knowledge` and the studies
   that read the split. `similar`, the word address, context sets and the
   respeller's vocabulary are not yet read by tier, and a down-weighting that
   keeps precision needs a guard read in the units of its decision.
   [`SOURCE_TIERS_STUDY.md`](studies/SOURCE_TIERS_STUDY.md) §7.5.

7. **The evidence model, in use, the rest** (left by Phases 169, 171 and
   174). Since Phase 171 `GLM.py -q … --result` prints any answer as the one
   result model; since Phase 174 the replay gate is the sign-off instrument
   `replay`, and the two answer censuses are guarded by the stored
   measurements their answers quote (`QUOTED_MEASUREMENTS_STUDY.md`). Other
   measurements that record answers (the frozen paths, `queryesc`) are still
   guarded by their sources only, and the recorder sees only files read after
   it starts. `--converse`, `--steps`, `--ask`, `--python` and `--reverse`
   still print their own objects; the frames, reverse, Python and engineering
   surfaces have no column 3; the evidence kind is declared by query kind
   rather than read from the computation.
   [`QUOTED_MEASUREMENTS_STUDY.md`](studies/QUOTED_MEASUREMENTS_STUDY.md) §3,
   [`EVIDENCE_IN_USE_STUDY.md`](studies/EVIDENCE_IN_USE_STUDY.md) §7.5,
   [`EVIDENCE_MODEL_STUDY.md`](studies/EVIDENCE_MODEL_STUDY.md) §7.5.

8. **Dialogue, the rest** (left by Phases 167, 172 and 173). Since Phase 173
   several questions stay open at once, a reply is read against the newest it
   fits or the turn it names, and a question closes after five unrelated turns
   (`STACKED_DIALOGUE_STUDY.md`). The window is a declared constant, not a
   measured length; a reply that fits several open questions goes to the
   newest by rule, and only a turn number can point at an older one (no
   *the first question*, no topic). A word echo (`yes`, then `yes`) is still
   read as a confirmation, inside the proved limit. A true reply that is no
   option (the carrier meant outside the head) is refused `not-an-option`
   without saying it is evidence the carrier is not in the head.
   [`STACKED_DIALOGUE_STUDY.md`](studies/STACKED_DIALOGUE_STUDY.md) §7.3,
   [`RESUMED_DIALOGUE_STUDY.md`](studies/RESUMED_DIALOGUE_STUDY.md) §7.4,
   [`ADVERSARIAL_DIALOGUE_STUDY.md`](studies/ADVERSARIAL_DIALOGUE_STUDY.md) §7.4.

9. **Rule induction, the rest** (left by Phase 175). `tool induce` answers
   within a binary operator vocabulary and chains at most two steps. Next:
   colours and objects (per-colour masks, object extraction, per-object
   operators) so that real ARC grids can be read; chains of three or more
   steps under a declared cost bound per step (D13) rather than enumeration;
   when it refuses, choose the query grid that would separate the disagreeing
   hypotheses and ask for its output through the conversation (the stacked
   dialogue of Phase 173 can hold that question open); and the kit's other
   open line, re-running the neural learners of iterations 1, 5–7 and 9 on the
   exact labels (needs `numpy`/`torch`, not available here).
   [`PIPELINE_KIT_STUDY.md`](studies/PIPELINE_KIT_STUDY.md) §7.4.

### 2.2 Smaller follow-ups left by closed studies

Each is a section a closed study ends on; any of them can be folded into a
round from §2.1 or taken as a short round of its own.

* **Tidiness, the rest** (noted in Phase 172). `MASTER_PLAN.md` holds every
  phase from 38 to 172 in full (about ten thousand lines) although its own
  rule is that only the open phase is state and the rest belongs in
  [`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md); moving
  the closed phases needs a check of every reader that looks a phase up in
  the plan (the study ledger, `tools dates`, the tests naming the plan)
  first. Phase 172 stopped tracking Python bytecode (`__pycache__/`, 902
  files) in version control; the tree as uploaded for Phase 173 tracked it
  again, and `.gitignore` now names `__pycache__/` and `*.pyc` so it stays
  out.
* **The study ledger, the rest** (left by Phase 161). The deciding figures
  count their marks in more than one way (the Lean mark with the measured
  marks, beside them, or not at all), so a figure's count cannot be checked
  against its stored measurement; one declared convention, or the stored file
  recording the marks taken outside it, would let S4′ be met. Older studies
  declare marks in lists the reader does not see; 11 studies have no phase in
  either source and one disagrees (96 against 97); and `corpus --check` does
  not yet run the file check. Two of its items were settled by the owner on
  18 October 2026: the supplied `GLM-main.zip` and two PDFs stay outside
  version control, as supplied (§2.0); and the studies carry no dates only
  until they are next altered, because D17 now dates every file a round
  creates or alters — the ledger could read the stamps as its
  pre-registration and measurement dates.
  [`STUDY_LEDGER_STUDY.md`](studies/STUDY_LEDGER_STUDY.md) §7.4.

* **`L5` in the other deep-hole reports, the rest** (left by Phases 149 and
  152). Phase 152 measured the 44 queries at 240 starts: 43 named correctly,
  1 refused, 0 wrong. One absence of the 397 issued at that budget is false
  (on the refused query, which lies outside its own radius), so a reading at
  240 starts would have to refuse its absences outside the radius as well as
  its answer; nothing in the answering path reads `L5` at 240 starts. At 480
  starts `L5` passes the gate with its per-type criterion holding for 9 of
  10 types, so one type's pass there is observed, not certified.
  [`L5_FIRST_BUDGET_STUDY.md`](studies/L5_FIRST_BUDGET_STUDY.md) §7.4,
  [`HOLE_REPORTS_L5_STUDY.md`](studies/HOLE_REPORTS_L5_STUDY.md) §7.4.

* **The budget rule, the rest** (left by Phase 147). `deep_holes.py` keeps
  its frozen defaults (the walk's 200 starts with patience 40, and
  `classify_carrier`'s patience 60), because six stored measurements digest
  that file; no answering-path caller uses them any more, so changing them is
  a re-take of those measurements rather than an answer change. The `hole`
  kind does not read a hole named by its Niemeier type.
  [`BUDGET_READING_STUDY.md`](studies/BUDGET_READING_STUDY.md) §7.4.

* **The guarded read in `nearest`, the rest** (left by Phase 148). The pool
  is the 142 carriers of the address table, not the registers in full;
  ranking a point against a whole register needs a table over it. Where the
  read refuses, the scan's head is another carrier than the origin on 51 of
  620 points; the answer says no margin is certified, and nothing more.
  [`NEAREST_ADDRESS_STUDY.md`](studies/NEAREST_ADDRESS_STUDY.md) §7.5.

* **The connected machine, the rest** (left by Phases 136 to 141).
  Since Phase 138 a tool's verdict is a planner step, but only from the two
  tools with a boolean figure (`gates`, `wiring`) and from any tool value by
  equality; the ladder's relations and a law's fate are not yet verdicts. The
  search reads one shape (the first convergent past a denominator bound,
  whose measure is proved); a search without a proved measure — *the first
  term of the continued fraction of X above 100* — waits for a proof, since
  no cap is to be added. Four of the sixteen fresh rewordings are unread
  (*the fraction closest to e with …*, *the kissing number of the
  24-dimensional leech lattice*, *the number of norm 6 vectors in the leech
  lattice*, *the minimum number of gate moves to go from …*); reading them
  now would be a post-hoc fit, so a fresh held-out set comes first. Since
  Phase 141 a prime that neither `p - 1` nor `p + 1` reaches is certified by
  an elliptic curve; a refusal now spends four budgets, and the order of the
  searches could change (N+1 ahead of Pocklington when `p + 1` is smooth,
  the elliptic search earlier on large numbers; either re-pins a
  kernel-checked instance); the measurement's `cert-k` tamper should be
  restated so that it is invalid by construction; the typed planner's own
  primality frame keeps its 10^12 limit (giving it certificates changes which
  surface answers, so it needs a frozen-path comparison)
  ([`ELLIPTIC_CERTIFICATE_STUDY.md`](studies/ELLIPTIC_CERTIFICATE_STUDY.md)
  §7.1). `tool wiring` names the 29
  modules no question reaches (171 of 200 are reached), each declared
  measurement-only with its reason; since Phase 143 the two ladder guards and
  `norm256_hex` are reached from the `locate` kind.
  [`TOOL_VERDICTS_STUDY.md`](studies/TOOL_VERDICTS_STUDY.md) §7,
  [`CONNECTED_MACHINE_TWO_STUDY.md`](studies/CONNECTED_MACHINE_TWO_STUDY.md)
  §7.3.

* **The question in the answering path, the rest** (left by Phase 146).
  Since Phases 172 and 173 a reply is read across unrelated turns and against
  any open question (item 8). Since Phase 150 `nearest` also puts the question at a tied head and reads
  `given` replies. Replies are
  written `key is reply`, because an `=` is read as an identity by the
  description layer's infix `verify` shape; a reply value containing `;` is
  not expressible.
  [`ANSWERING_QUESTION_STUDY.md`](studies/ANSWERING_QUESTION_STUDY.md) §7.5.

* **Time and the question, the rest** (left by Phase 145). The vocabularies
  for the other ties are item 1 of §2.1. The 78-member junction of dimensionless physics quantities takes up to 22
  questions, because no declared question halves it (`exists_halving` says
  one exists); a measurand coordinate would be one (the decision of §2.3).
  Questions are chosen by what splits, not by what a user can answer or what
  an answer costs; and the developer's answers are taken as true — one
  confirming question catches a single false answer, more than one is not
  measured.
  [`TIMED_QUESTION_STUDY.md`](studies/TIMED_QUESTION_STUDY.md) §7.6.

* **Register junctions, the rest** (left by Phase 144). The zero word's
  junction (`golay_codeword_0`, `hexacode_word_0`) shares every cell with
  `high_denominator_2x3` and `rational_root_thirds`, the two carriers refused
  for crowding: reading the three needs a finer cell near the origin than the
  ladder has, not a junction. The full registers hold 104 junctions over 387
  of 1,094 carriers (0 crossing a register), measured but not declared; a
  register larger than the 142-carrier sample must re-take both tables
  (`tools address-table --write`, `tools junction-table --write`), and each
  junction a read can answer should get a declaration. In 87 of the 104 the
  members differ only in name, symbol and gloss — whether the encoding should
  carry a coordinate for the measurand (the unit alone would split 8) is a
  decision for the registers (§2.3). Since Phase 148 `nearest` reads
  junctions on its address path; the escalation reports do not read the
  construction ladder at all.
  [`COORDINATE_JUNCTION_STUDY.md`](studies/COORDINATE_JUNCTION_STUDY.md) §7.7.

* **The designed substrate, the rest** (left by Phases 133, 134 and 135). The
  `carrier` kind reads the stages and the protected tag, but the soft
  certificate is reached only through a supplied soft reading: its acceptance
  rate on a soft reading the GLM produces itself is not measured, because the
  GLM produces none yet. The carrier read carries no guard of its own beyond
  the stages' assumptions: a fifteen-bit tag with three or more flipped bits
  can mislead radius 2 (`tag15_three_flips_mislead`; 26,681 of 680,064 tied
  reads with three consecutive flips, post hoc), and reading it at radius 1 instead never misleads on three
  flips but corrects only one. Since Phase 135 the tag lengths are bounded:
  the seven-bit tag is the shortest possible and the protected tags are the
  shortest built on seven bits; a tag of another shape with 9–10 bits (one
  flip) or 11–14 bits (two) is neither found nor excluded, and the search's
  control never reached 15 bits, so a stronger search comes first
  ([`SHORTEST_TAG_STUDY.md`](studies/SHORTEST_TAG_STUDY.md) §7.5). The substrate study's other results (the four-label
  mirror, the 86–128-value Golay tag, the Delsarte bound) are cited, not
  re-proved.
  [`PROTECTED_TAG_STUDY.md`](studies/PROTECTED_TAG_STUDY.md) §7.5,
  [`DESIGNED_SUBSTRATE_STUDY.md`](studies/DESIGNED_SUBSTRATE_STUDY.md) §7.5,
  [`SHORTEST_TAG_STUDY.md`](studies/SHORTEST_TAG_STUDY.md) §7.5.

* **Norm 256 and the hex colour, the rest** (left by Phase 127). `H16` is
  measured beside the ladder only; putting it into the answering path needs a
  frozen-path comparison. The 4096-colour subspace that decides membership of
  the rotated Leech rung has no use yet, because that rung was retired; other
  rotations of the Leech lattice were deliberately not compared on the 568
  queries. [`NORM_256_HEX_STUDY.md`](studies/NORM_256_HEX_STUDY.md) §7.5.
* **GLM-BAT, the rest** (left by Phases 125, 126, 130, 131, 132 and 142). Stream
  merging (`2>&1`), `SORT` options, `FOR /F`, `SETLOCAL`/`ENDLOCAL` and
  delayed expansion are refused. Since Phase 142 a pass whose step grows
  linearly (an accumulator adding a counter: L12 is now *never*) is jumped or
  certified; geometric growth (N5, `N=N*2`, whose closed form
  `const_ratio_closed_form` is proved) and cubic growth (an accumulator fed by
  an accumulator) are still refused, as are accumulators fed by a constant
  variable or an expression
  ([`QUADRATIC_LASSO_STUDY.md`](studies/QUADRATIC_LASSO_STUDY.md) §7.5);
  a jump whose output would pass 1,000,000 lines (P6); an `ECHO`
  with redirection or inside a chain or test body on a pass (P10); a constant
  read through `ERRORLEVEL`; and comparisons of text. The run encoder takes
  the block covering the most lines even when it has only two copies, so
  P8's printed text opens with two 16-line blocks; asking for three copies
  would state it as the hand computation expected.
  [`QUADRATIC_LASSO_STUDY.md`](studies/QUADRATIC_LASSO_STUDY.md) §7.5,
  [`AFFINE_OUTPUT_STUDY.md`](studies/AFFINE_OUTPUT_STUDY.md) §7.5,
  [`CONSTANT_BOUND_STUDY.md`](studies/CONSTANT_BOUND_STUDY.md) §7.4,
  [`COUNTER_LASSO_STUDY.md`](studies/COUNTER_LASSO_STUDY.md) §7.4,
  [`OPERATIONS_LADDER_STUDY.md`](studies/OPERATIONS_LADDER_STUDY.md) §7.4.
* **Radicals, the rest** (left by Phases 114, 115 and 116). Compositions whose
  outer polynomial has degree below 5, with the obstruction in the inner
  polynomial, and imprimitive groups that are not compositions over the
  rationals, are still silent
  ([`COMPOSED_RADICAL_STUDY.md`](studies/COMPOSED_RADICAL_STUDY.md) §4); so
  are primitive groups of prime-power degree with no element whose power is
  a transposition or a 3-cycle (`PSL(2, 7)` on eight points), and primitive
  groups with no `(n - 1, 1)` element (`S5` on the ten pairs of five points)
  ([`PRIMITIVE_DEGREE_STUDY.md`](studies/PRIMITIVE_DEGREE_STUDY.md) §4). A positive statement of solvability
  (the resolvent sextic for quintics). Dedekind's theorem in Lean, which
  would close the gap between the factorisation and the group element. The
  16-modular-factor cap (lattice reduction past it).
  [`PRIMITIVE_RADICAL_STUDY.md`](studies/PRIMITIVE_RADICAL_STUDY.md) §4.
* **The router's reach into the Lean tree** (left by Phase 115). Every unit
  that reaches the router takes the whole Lean development through
  `reasoning/lean_address.py`'s tree walker, and the median cost of one Lean
  edit now stands one unit above half the units that name any Lean file;
  split the walker out of the module the answering path reads.
  [`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5k.
* **Derivations, the rest** (left by Phase 119). Six or more variables
  (`TOO_MANY_VARIABLES`); claims that neither Zhang–Yeung nor chains of two
  copies decide (8 of the 40 five-variable battery claims and Phase 118's 3
  undecided claims stay `NOT_SHANNON`); rate distortion with a symbolic
  source, and continuous sources; Robin at both ends with coefficients of
  opposite sign (the number of negative eigenvalues then depends on `a`, `b`
  and `L` together), a symbolic coefficient at the near end, and variable
  coefficients.
  [`DERIVATION_FOUR_STUDY.md`](studies/DERIVATION_FOUR_STUDY.md) §6.
* **Meta questions, the rest** (track M; left by Phase 117). Recognition of
  rewordings: p92a goes to the earlier `deep_hole_tie` frame and h92 ("coset
  weight is 4") is read by no frame. A meta question on a topic outside the
  declared eighteen is not read.
  [`META_QUESTIONS_STUDY.md`](studies/META_QUESTIONS_STUDY.md) §5.
* **Explanations, the rest** (track E; left by Phase 120). Recognition of
  rewordings: 30 of the 35 held-out rewordings are read by no frame (none is
  misread). A *why* question outside the declared 35 is not read, and the
  explanations themselves are still refused. The nuclide register holds ground
  states only — no excited states (the Hoyle state is quoted), isomers or
  abundances.
  [`EXPLANATION_ANCHOR_STUDY.md`](studies/EXPLANATION_ANCHOR_STUDY.md) §5.
* **The studies the router holds** (left by Phase 117). The meta frames read
  six studies, so editing the paper, the integer-decision study or the
  symbolic-parameters study now makes 48 units stale where it made two or
  three; a stored, digest-checked copy of the quoted sentences would take
  that back out.
  [`META_QUESTIONS_STUDY.md`](studies/META_QUESTIONS_STUDY.md) §6.
* **Lattice, measured but not settled.** Whether larger ensembles make
  `A_1^24` or `A_2^12` emit a stray (not measured;
  [`STRAY_BLIND_STUDY.md`](studies/STRAY_BLIND_STUDY.md)). A margin other
  than twice the nearest distance for the adopted guard, which refuses 137
  queries it used to answer (lattice item 8;
  [`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md) §9).
* **The planner's utility gate** (item 9). Reading one of the loop's
  questions from English — the next measurable step before the supplied
  planner could earn promotion out of the sandbox under D14.
  [`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md).
* **Frames and folds.** Cross-table comparison, differences between
  molecules, a frame over the nuclide register (which now exists, Phase 120,
  but is read only by the explanation anchors), one-sided ranges, the top `k`
  under a hole. [`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md) §6.
* **Discourse.** The column handed to the planner's folds, a present-rows
  column, further phrasings, the plan store for the new shapes, an outside
  multi-turn set. [`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md) §7.
* **The register against the world.** Sources for electron affinity and the
  melting and boiling points; isotope masses for the 34 world-silent weights;
  a held-out check of the narrowing.
  [`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md) §6.
* **Temperature scales.** A register in degrees Fahrenheit (the declaration
  `GLM.MeasurandKinds.fahrenheit_kelvin` already states), an answer stated in
  degrees Celsius, the ITS-90 vapour-pressure ranges as interval values.
  [`CELSIUS_REGISTER_STUDY.md`](studies/CELSIUS_REGISTER_STUDY.md) §7;
  the measurand register's own remainder,
  [`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md) §6.
* **Typed operators.** Polar phasors, three-phase power and power-factor
  correction, the verifier's rank algebra joined to the typed values.
  [`TYPED_OPERATORS_STUDY.md`](studies/TYPED_OPERATORS_STUDY.md) §6.
* **The Python dialect and the reverse grammar.** Unicode case and
  whitespace tables as a register, booleans as a term, sets and
  comprehensions ([`THIRD_SORT_STUDY.md`](studies/THIRD_SORT_STUDY.md) §6);
  `break`, closures, the truth of sequences, a trace inside calls, a program
  with state handed to the planner as a sentence
  ([`IMPERATIVE_GRAMMAR_STUDY.md`](studies/IMPERATIVE_GRAMMAR_STUDY.md) §6);
  keywords and defaults, starred displays, unpacking in the imperative grammar
  ([`UNPACKING_RESCORE_STUDY.md`](studies/UNPACKING_RESCORE_STUDY.md) §6);
  the relay reading the integer certificate kinds and an `INDEPENDENT`
  verdict's witness handed on as a follow-up
  ([`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md) §12).
* **Second readings.** Framing an existing register by default; a soft
  channel whose reliabilities come from outside the views.
  [`SECOND_VIEW_STUDY.md`](studies/SECOND_VIEW_STUDY.md) §6.
* **Substrate-native cognition.** Semantic judgements as annotated
  provenance (E4); deeper PCGS proofs (E7).
  [`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md) §8.
* **Supplied material not yet read in** (candidate G and Phase 49). The
  language half of `mog_cube_1` (about thirty files) and the unported part of
  `ObserverY.lean` (Appendix C.3 of
  [`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md)); the vision
  experiments script `glm_vision_experiments_v14.py`; the v4 query-loop
  reading (no control yet) and the v4 higher-lattice escalation (argued, never
  run) of [`NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md).
* **The soft floor's breaks at rate 1/5**, which remain under every contract
  variant. [`CONTRACT_MATRIX_STUDY.md`](studies/CONTRACT_MATRIX_STUDY.md),
  [`RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md) §4.

### 2.3 Waiting on the owner

* **Outside material:** a register that arrives anonymous on its own (item 4)
  — goals from a second Lean development, or from a generator, scored against
  the anonymous-register controls.
  [`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md).
* **Decisions:** whether the registers should carry a coordinate that
  separates the members of a junction, or keep the junction as the answer
  ([`COORDINATE_JUNCTION_STUDY.md`](studies/COORDINATE_JUNCTION_STUDY.md)
  §7.4); whether any discrepancy found against the outside sources is
  ever written back into a register
  ([`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md) §6); the
  element register's aluminium melting point, 933.437 K against ITS-90's
  933.473 K ([`CELSIUS_REGISTER_STUDY.md`](studies/CELSIUS_REGISTER_STUDY.md)
  §7); the planner's DC `power` asked an alternating question
  ([`TYPED_OPERATORS_STUDY.md`](studies/TYPED_OPERATORS_STUDY.md) §6).
* **Proposed for retirement:** candidate P's 42 PIPELINE laws, which could be
  re-read only through UBP pipelines the GLM does not implement
  ([`LAW_TRIAGE_STUDY.md`](studies/LAW_TRIAGE_STUDY.md) §3); candidate H's
  concept 6, which waits on a trilinear object in the runtime.

### 2.4 Parked, and ongoing

* **Parked at the owner's direction (Phase 106):** the rest of the retrieval
  line — N5 (a native word ranking with the part letter words first), the AST
  index study's §8, the citation-scope study's §6 and the document-tree
  study's §6. Kept as the record; every operation it built stays in the
  system.
* **Ongoing rather than finishable:** the lexicon's vague `related_to`
  triples and the sparse chemistry cells — see [`SYSTEM.md`](SYSTEM.md) §3.2.

**The discipline any item is taken under**, unchanged: describe or measure,
never assert; count what does not generalise; freeze the path being replaced
so the new one has something to agree with; and the end-to-end evaluation must
return the same answers and the same refusals.

---

## 3. Closing a run

The close is one exact sequence, written out with its measured cost in
[`ITERATE.md`](ITERATE.md) §4. In short: finish the work and write it down
(study, `MASTER_PLAN.md` phase, this list), then from `overlay/` run
`corpus --refresh`, `corpus --check` and `signoff --close --jobs 8` once,
touch no document afterwards, and commit. The test-suite row above is the
sign-off ledger's own count, recorded by the close.

---

## 4. The document map

There is no hand-kept index any more, because a hand-kept index is a stored
table and this project's rule is that a table may be kept only beside the
digest of what it came from.

* [`ENTRY.md`](ENTRY.md) states the reading order and the coverage claim:
  these documents describe the system as it is, everything else is a record of
  a round.  The claim is tested — `glm_universal.corpus.checks` fails if a
  current-state document is unreachable from it or an archived one is missing
  from its list.
* [`DIGEST.md`](DIGEST.md) is that list at tier 0, one row per document —
  question, verdict, deciding figure, and the function that recomputes it.  It
  is **generated** from the documents' own tier-0 blocks by
  `python3 -m glm_universal.corpus --write`, so it cannot drift from them.
