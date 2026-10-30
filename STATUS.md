# Status


## Tier 0 — the coarse read

**Question.** What is still to do, where does the work stand in one screen, and how is a run closed?

**Verdict.** This is the To-Do list: what is open, sharpest first, with the closed record moved out to the archive and the standing description of the system moved to `SYSTEM.md`.

**Deciding figure.** Every instrument in the table at the head of the document reports its own result on demand.

**Recomputed by.** `glm_universal.signoff.ledger.suite_totals`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 30 October 2026.*

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
[`src/lean/RequestProject/`](src/lean/RequestProject/GLM/README.md)
(`lakefile.toml` sets `srcDir = "glm_lean"`); there is no
`RequestProject/` folder at the repository root, so a path written as
`RequestProject/GLM/X.lean` in a record means
`src/lean/RequestProject/GLM/X.lean`. The studies are in
[`studies/`](studies/), the Python package in `glm_universal/`. A file
audit after Phase 158 (the owner asked whether
[`FRICTION_STUDY.md`](studies/FRICTION_STUDY.md),
[`OSCILLATOR_JUNCTION_STUDY.md`](studies/OSCILLATOR_JUNCTION_STUDY.md) and Lean
files had gone missing) found every file present: 232 Lean files (231 under
`GLM/` plus `Main.lean`), all building with `lake build` and 0 `sorry`, and
all 160 study documents. What was wrong was 261 rows of the Properties table
still pointing at the old root path `RequestProject/GLM/…`; they now point at
`src/lean/RequestProject/GLM/…`.

**Repository hygiene: the knowledge cache and the push size.** On 22 October
2026 pushes were failing because the git server rejected them as too large.
The cause was the regenerated counted-knowledge cache,
`glm_universal/knowledge/_knowledge_cache/knowledge.pickle` (about
135 MB), which was tracked by git: it is rewritten whenever any corpus file
moves, so every round committed another full copy. It is now untracked and
listed in `.gitignore`, and so is the rest of that directory (the two
word-address books, about 1 MB each, rewritten on the same trigger). Nothing
is lost: `corpus --refresh` rebuilds the cache, and any reading that finds it
missing counts the corpus once and writes it (about a minute on this corpus;
later readings load it in seconds, and a changed file is the only file read
again). The environment variable `GLM_KNOWLEDGE_CACHE` moves the cache
directory out of the tree if wanted. The fix is held by
[`test_repository_hygiene.py`](glm_universal/tests/test_repository_hygiene.py):
it fails if any cache file is tracked or not ignored, if any tracked file
exceeds 10 MB, or if an absent, deleted or corrupt cache is not rebuilt to the
same knowledge. One consequence to keep in mind: `GLM-main.zip` is also kept
out of version control but *is* read by the corpus, so a clone without it
counts a smaller corpus than this working tree does.

**Starting a new round? Read [`ITERATE.md`](ITERATE.md) §0, then §2 below.**
Every part of the owner's plan of 19 October 2026 has been taken (§2.0); the
next round starts from §2.1.

**Just closed: Phase 184 — the declared majority rule** (23 October 2026;
[`LORENTZIAN_MAJORITY_STUDY.md`](studies/LORENTZIAN_MAJORITY_STUDY.md), record
in `MASTER_PLAN.md` "Phase 184"), §2.1 item 11's first line.
`LorentzianMajority.lean` proves that the target a strict majority of the
weight states is unique (`majority_unique`), that the rule is never wrong while
the honest examples hold at least half the weight and right above half
(`majority_never_wrong`, `majority_sound`), that agreeing decoys below half
carry it (`majority_misled`: the condition is tight), that a wrong answer needs
decoys weighing at least its own group (`majority_wrong_needs_decoys`), and
that it answers wherever the dispersion guard does (`majority_extends_guard`).
In use: `tool majority` (decoy3 155 and decoy5 161 right, 0 wrong, where the
guard answers none; collude5 refused where the plurality vote is wrong 150
times; decoy4 0 right where the plurality has 149). 8 of 8 marks.

**Before it, Phase 183 — the Lorentzian evidence space** (23 October 2026;
[`LORENTZIAN_EVIDENCE_STUDY.md`](studies/LORENTZIAN_EVIDENCE_STUDY.md), record
in `MASTER_PLAN.md` "Phase 183"), at the owner's request: §2.1 item 11 taken
further, and the question asked whether the ambiguous space is of use for
general reasoning. `LorentzianEvidence.lean` proves, in any dimension, that
weighted cues sum to the lifted consensus plus the Weyl vector times their
disagreement (`evidence_decomp`), that `⟨V, V⟩ = −W·D` (`evid_norm`), that
analogy is evidence with weights 1, −1, 1 (`analogy_evidence`), and how long
the question settling a tie must be (`card_ge_of_separates`). In use: the
certificate guard in `tool lorentz` (Golay decoy 61 wrong → 27, 0 right
answers lost, the 27 indistinguishable from honest readings); the settling
question (600 of 600 with five bits); `tool evidence` (relations over the
physics register, 0 wrong with a decoy example). 13 of 15 marks.

**Before it, Phase 182 — the Lorentzian lift of the ambiguous space** (22
October 2026; [`LORENTZIAN_LIFT_STUDY.md`](studies/LORENTZIAN_LIFT_STUDY.md)):
the owner's `iter10_lorentzian.py` audited; every Golay tie an A_1^24 deep
hole named by a null vector of II_25,1; no reflection-invariant rule breaks a
tie; summed scores over further readings resolve ties (`tool lorentz`); 11 of
12 marks. **Phases 180 and 181** (22 October 2026): every Leech shell counted
and proved ([`LEECH_SHELL_COUNT_STUDY.md`](studies/LEECH_SHELL_COUNT_STUDY.md),
6 of 6), and improper maps times a change of units in `tool frame`
([`IMPROPER_UNITS_STUDY.md`](studies/IMPROPER_UNITS_STUDY.md), 8 of 8).

**Before those, Phase 179** (improper maps in `tool frame`;
[`IMPROPER_FRAME_STUDY.md`](studies/IMPROPER_FRAME_STUDY.md)), Phase 178 (colour induction and the frame plane;
[`COLOUR_INDUCTION_STUDY.md`](studies/COLOUR_INDUCTION_STUDY.md)), Phase 177
(frame operators: Lorentz boosts in exact arithmetic and the anchor κ;
[`FRAME_OPERATOR_STUDY.md`](studies/FRAME_OPERATOR_STUDY.md)), Phase 176
(asking for the separating example;
[`PIPELINE_ASK_STUDY.md`](studies/PIPELINE_ASK_STUDY.md)), Phase 175 (the
owner's pipeline kit and `tool induce`;
[`PIPELINE_KIT_STUDY.md`](studies/PIPELINE_KIT_STUDY.md)), Phases 173 and 174
([`STACKED_DIALOGUE_STUDY.md`](studies/STACKED_DIALOGUE_STUDY.md),
[`QUOTED_MEASUREMENTS_STUDY.md`](studies/QUOTED_MEASUREMENTS_STUDY.md)), Phase
172 ([`RESUMED_DIALOGUE_STUDY.md`](studies/RESUMED_DIALOGUE_STUDY.md)), Phase
171 ([`EVIDENCE_IN_USE_STUDY.md`](studies/EVIDENCE_IN_USE_STUDY.md)), and
earlier; each is recorded in `MASTER_PLAN.md`.

---

## 1. Where the work stands, in one screen

| instrument | command | result |
|---|---|---|
| test suite | `python3 -m pytest src/glm_universal/tests -q` | **<!--figure:suite-->(not yet measured: suite)<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **<!--figure:evaluation-case-count-->223<!--/figure-->** cases — 0 confidently wrong, every refusal a `boundary` |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 surprises |
| Lean development | `lake build` (repository root) | <!--figure:lean-files-->425 Lean files<!--/figure-->, **0 `sorry`** |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the coverage claim of `ENTRY.md`, every generated block and every derived cache |

The package holds **<!--figure:registers-->8 registers<!--/figure-->** beside a 45-class comparison register,
**<!--figure:query-kinds-->27 query kinds<!--/figure-->** one of which
dispatches **<!--figure:report-subjects-->67 report subjects<!--/figure-->**, and 3 tasks. The Lean development is
addressed declaration by declaration: `reasoning/lean_address.py` gives each of
the <!--figure:lean-declarations-->9,126<!--/figure--> declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly <!--figure:lean-declarations-->9,126<!--/figure-->/<!--figure:lean-declarations-->9,126<!--/figure--> with 0 coordinate errors
(`report lean`). The other forty-odd instruments, each with its command and its
current figure, are the table in [`SYSTEM.md`](SYSTEM.md) §1.

---

## 1b. Reorganisation status (29 October 2026)

The repository has been reorganised across 15 iterations:

- **Phase R1** (iter 5): executable code moved to `src/` (`glm_universal/`, `lean/`, `GLM.py`)
- **Phase R2** (iter 6): all 15 wheels centralized under `src/glm_universal/wheels/`
- **Phase R3** (iter 8): every study converted to a `.yaml` + `.md` pair (189 manifests)
- **Phase R4** (iter 10): Wobble subsystem (D17) — `reasoning/wobble_registry.py`
- **Phase R5** (iter 10): Reversibility ledger (D18) — `reasoning/reversibility.py`
- **Phase R6** (iter 10): Generate-don't-store (D19) — `reasoning/generate_not_store.py`
- **Stage 3** (iter 10): signoff schema bumped 5->6; YAML_PROTOCOL_ENABLED=True
- **Rule30 absorption** (iter 7): 156 Lean files absorbed into `src/lean/` (412 total)
- **Stub implementation** (iters 12-15): 13 of 24 stub modules now have real implementations

Remaining (both need Lean installed):
- **Phase 5**: 5 reasoning study stubs (`hole_reports_l5`, `ties_ladder_frozen`, `planner_ladder`, `carried_read`, `l5_first_budget`)
- **Phase 6**: 6 deep-runtime stubs (`evidence`, `frame_plane_study`, `adversarial_dialogue_study`, `nearest_question_study`, `reader`, `model`)

The 19 directives (D1-D19) are in `PROJECT_DIRECTIVES.md`, enforced by `reasoning/directives.py`.
The fundamental constants are centralized in `src/glm_universal/constants.py`.
The 12 missing Lean files (placeholders) are documented in `studies/_lean_files_needed.md` — each needs to be recovered from the owner's development environment.
The study ledger (`corpus/study_ledger.py`) reads the YAML manifests and verifies the predecessor graph is acyclic (153 edges, 189 studies).

## 2. To Do

Sharpest first within each group. Each line names the study section that
states the item in full; the bracketed names (`lattice item 6`, `track M`, …)
are the names earlier records use, kept so that a reference in a study or a
module docstring still finds its line. When a line is taken, delete it here and
record the round in `MASTER_PLAN.md`.

### 2.0 The owner's plan of 19 October 2026 — every part taken

The owner's development plan,
[`source_material/GLM_19OCT26_1.md`](source_material/GLM_19OCT26_1.md), set
the direction for Phases 159–174. Every part has been taken once, and what
each left is a line of §2.1 or §2.2: Part I, thermomechanical friction (Phase
159, [`THERMO_FRICTION_STUDY.md`](studies/THERMO_FRICTION_STUDY.md); item 4);
II.1, one evidence and result model (Phase 169,
[`EVIDENCE_MODEL_STUDY.md`](studies/EVIDENCE_MODEL_STUDY.md); item 7); II.2,
the carried-value gaps (Phases 160 and 163,
[`FOLD_MACHINE_STUDY.md`](studies/FOLD_MACHINE_STUDY.md),
[`TOOL_MACHINE_STUDY.md`](studies/TOOL_MACHINE_STUDY.md); item 2); II.3,
contextual domain frames (Phase 170,
[`CONTEXT_FRAMES_STUDY.md`](studies/CONTEXT_FRAMES_STUDY.md); item 5); II.4,
a corpus confidence curve (Phase 168,
[`CONFIDENCE_CURVE_STUDY.md`](studies/CONFIDENCE_CURVE_STUDY.md); item 3);
II.5, adversarial interactive testing (Phase 167,
[`ADVERSARIAL_DIALOGUE_STUDY.md`](studies/ADVERSARIAL_DIALOGUE_STUDY.md); item
8); II.6, a machine-readable study ledger (Phase 161,
[`STUDY_LEDGER_STUDY.md`](studies/STUDY_LEDGER_STUDY.md); §2.2); II.7, corpus
source tiers (Phase 162,
[`SOURCE_TIERS_STUDY.md`](studies/SOURCE_TIERS_STUDY.md); item 6). The plan
file stays as supplied. Three standing rules came with it and still hold:

**Standing rule: `source_material/` is the less reliable tier** (owner's note,
19 October 2026). The document inventory never walks it; `define`/`ask` rank
a supplied sentence below every written one; the glossary reads written
Markdown only. The counted model and what is built on it (continuation, the
guarded predictor, `similar`, the word address, context sets, the respeller's
vocabulary) still count a supplied sentence like a written one; the declared
policy — *a supplied reading is a candidate that written evidence must
confirm* — is measured, not shipped (item 6). Until it ships, a reading
resting only on `source_material/` is reported as such, and a result recovered
from `GLM-main.zip` is a candidate until it is re-derived, tested or proved
here.

**Standing rule: the supplied files stay as supplied** (owner's instruction,
18 October 2026). `source_material/GLM-main.zip` and the supplied PDFs are
kept in the project folder exactly as they are and out of version control
(`.gitignore`). Nothing under `source_material/` is edited, renamed or dated
by a round.

**Standing rule: date every file a round creates or alters** (owner's
instruction, 18 October 2026; directive D17 in
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md)): `Created <day Month year>`
or `Last altered <day Month year>` in the file itself; a study also says when
it was pre-registered and measured. `python3 -m glm_universal.tools dates`
lists every stamp and fails on a bad one.

### 2.1 The next rounds

0. **repository check and fix** this repository has been reorganised and needs
a proper check through everything, some parts may be broken and require fixing.
   * 'glm_universal.constants' - in 'src/glm_universal' is to be the single source 
of recording and updating constants for this repository and the GLM - the 
ITERATION.md document and other top-level documents need to pass this function on to
'glm_universal.constants' and record that is to be upheld ongoing.
   * the 'source_material' folder has become the input method for this repository and the
GLM, it currently has several folders and studies that have yet to be processed and 
absorbed into the GLM for use, these items must be Lean verified before absorbtion
so they can be trusted 'studies/_lean_files_needed.md' records some that have been partly
tested but need Lean verification. Other studies ready for 
investigation/fixing/testing/lean/absorption (if they work for the GLM): 
cent_compiler_v12 (of particular interest to test/fix/lean/absorb), attention, 
conversation_experiment, devops_ladder (may be covered by other studies already), 
formula_wheel, glm_wheels_bundle, hidden_memory, R_Calculus (becomes 'hypothesis_engine.py' in Rule30_GLM_Study), 
Rule30_GLM_Study (loads of lean already made).
- prioritise the ones that have lean already - test for the GLM's reasoning abilities/scope 
for measurable improvement then absorb into the GLM system for use, then move into the studies 
that need deeper investigation and fixing/testing.

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

2. **The machine's reading, the rest** (left by Phases 153, 160, 163, 164, 165, 166 and 180).
   Since Phase 163 no step of an answered stepwise chain is carried, and
   since Phase 166 π is summed by the machine like `e`
   (`PI_MACHINE_STUDY.md`). Since Phase 164
   the Leech shapes are proved and every shell is counted from the Golay
   census (`LEECH_SHELLS_STUDY.md`), but only by the tool: GLM-BAT still
   counts only the minimal shell. Since Phase 165 the minimal shell is proved
   both ways and its 196,560 is a theorem (`LEECH_KISSING_STUDY.md`); since
   Phase 180 the procedure is proved correct for every shell and the first
   eight shells are theorems (`LEECH_SHELL_COUNT_STUDY.md`), though the
   `llvq` answer does not cite the proof yet (citing it moves recorded
   answers, so the frozen paths need re-taking); a kissing-number question costs about 164,000 machine steps (the census
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
   [`LEECH_SHELL_COUNT_STUDY.md`](studies/LEECH_SHELL_COUNT_STUDY.md) §7.3,
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

9. **Rule induction, the rest** (left by Phases 175, 176 and 178). Since
   Phase 178 `tool induce` reads colour grids and objects and `tool arc`
   reads the 50 stored ARC tasks: 0 wrong, but only 2 of 50 right (the vision
   stack's 2), 48 refused because nothing in the vocabulary fits. Next: a
   wider vocabulary that pays its way on real grids (per-object operators,
   line drawing, local rules — a first try at local rules gave 0 new solves
   and was not shipped), measured on a **fresh held-out ARC set** (the 50
   stored tasks are no longer held out for this solver); asking for the
   separating example on colour tasks (C2 missed: 302 of 360 at three
   demonstrations; 192 disagreements and 122 unread parameters are refusals
   an ask could resolve); a family set on which the span rule prevents an
   error the unread rule does not (C4 missed at the second take: the span
   rule cost 83 right answers and prevented none); chains of three or more
   steps under a declared cost bound per step (D13) rather than enumeration;
   when choosing the example, count *no output* as a reply of its own; hold
   the ask open in the conversation and read the reply back as a
   demonstration (Phase 173's stacked dialogue can carry it); and re-running
   the kit's neural learners on the exact labels (needs `numpy`/`torch`).
   [`COLOUR_INDUCTION_STUDY.md`](studies/COLOUR_INDUCTION_STUDY.md) §9,
   [`PIPELINE_KIT_STUDY.md`](studies/PIPELINE_KIT_STUDY.md) §7.4,
   [`PIPELINE_ASK_STUDY.md`](studies/PIPELINE_ASK_STUDY.md) §7.4.

10. **Frame operators, the rest** (left by Phases 177, 178, 179 and 181). Since
    Phase 178 `tool frame` works in 1+2 dimensions (boosts along any axis,
    rotations, their compositions, Thomas–Wigner read exactly) and the span
    rule and invariant reading are in `tool induce`; since Phase 179 the
    improper maps (reflections, time reversal, and their compositions with
    Lorentz maps) are declared families, named by component
    ([`IMPROPER_FRAME_STUDY.md`](studies/IMPROPER_FRAME_STUDY.md) §7.4).
    Since Phase 181 an improper map times a change of units is a family too
    ([`IMPROPER_UNITS_STUDY.md`](studies/IMPROPER_UNITS_STUDY.md) §7.3), with
    a rational scale (an irrational one is refused, as for `lorentz_units`).
    Left: hold `tool
    frame`'s ask open in the conversation as Phase 173 does; 3+1 dimensions. Test the TAX refractive-index law only with material data
    fixed independently of the indices (the review's four conditions;
    [`FRAME_OPERATOR_STUDY.md`](studies/FRAME_OPERATOR_STUDY.md) §9). Decide
    which tabulated quantity κ names (`D0` or the 298 K bond energy) and
    whether the tick budget is `27` or `24 + 8Q`; both shift every output
    more than κ's digits do (§6).

11. **The Lorentzian evidence space, the rest** (left by Phases 182,
    183 and 184). The lift is an evidence space in any dimension, the certificate
    guard and the settling question are in `tool lorentz`, and `tool
    evidence` combines examples of a relation over the physics register
    ([`LORENTZIAN_EVIDENCE_STUDY.md`](studies/LORENTZIAN_EVIDENCE_STUDY.md)
    §8). Since Phase 184 the majority rule is declared and proved sound while
    the honest examples hold at least half the weight (`tool majority`;
    [`LORENTZIAN_MAJORITY_STUDY.md`](studies/LORENTZIAN_MAJORITY_STUDY.md)
    §7): the condition is the caller's and cannot be read from the targets; a
    plurality rule for sources whose wrong examples are independent (decoy4's
    149 right answers) and weights from a source's standing are open. Left
    too: the evidence space on Leech-level
    address ties (`reasoning/tie_break.py`) and the other 22 deep-hole types;
    holding `tool lorentz`'s five-bit question open across conversation turns
    (as Phase 173 does); and the 27 decoy errors no reading-only rule can
    remove, which need a record of which message a reading is of (Phase 133's
    sender tag is the instrument of that kind).

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
* **`report relay` near the evaluation's ceiling** (left by Phase 184). With
  6,224 Lean declarations `report relay` takes about 230 seconds on its own,
  most of it the 1,660 ranking queries of the relay study (each a full scan
  of the address table, the text ranking and the name ranking); on eight
  evaluation processes it can pass the 300-second ceiling. Phase 184 fixed the
  same drift in `report lean` (199 → 56 seconds, `nearest_points` pruned on
  the principal axis); the relay's rankings want the same treatment — an exact
  pruned `k`-nearest search, or the ranked lists cached by digest — not a
  higher ceiling.
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
(study, `MASTER_PLAN.md` phase, this list), then from `` run
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
