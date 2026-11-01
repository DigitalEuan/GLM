# Colour induction and the frame plane — `tool induce` on colour grids and objects, `tool arc`, and `tool frame` in 1+2 dimensions

## Tier 0 — the coarse read

**Question.** Can the agreement gate of `tool induce` be carried from 0/1 grids to colour grids whose shape may change — and onto the 50 stored ARC tasks — without a wrong answer (part A), and can `tool frame` be widened to states `(E, px, py)` in 1+2 dimensions, reading the Thomas–Wigner rotation exactly (part B)?

**Verdict.** Partly. On colour grids the gate gives 0 wrong answers in its vocabulary but falls short of the declared coverage, and on the stored ARC tasks it answers only the 2 the vision stack solves, with 0 wrong — the vocabulary binds, not the gate; `tool frame` in 1+2 dimensions gives 0 wrong answers inside and outside its families and reads all 60 Thomas–Wigner queries with their exact Wigner rotation.

**Deciding figure.** Part A 8 of 12 marks (C2, C4, R2, R3 missed): 683 right, 0 wrong, 397 refused of 1,080 in-vocabulary queries; 302 of 360 at three demonstrations; ARC 2 of 50 right, 0 wrong. Part B 8 of 8 marks at the second take: 536 right, 0 wrong of 1,080 inside the families, 0 wrong of 360 outside; Thomas–Wigner 60 of 60.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026. Reconstructed 31 October 2026 from the round records; the original was lost in the October 2026 reorganisation.* The original was written on 22 October 2026 (the date of the Phase 178 record); the marks of each part were committed before that part's first measurement.

> **How this reconstruction was made.** From the Phase 178 record of
> [`MASTER_PLAN.md`](../MASTER_PLAN.md), the "colour induction" and "frame
> plane" rows and the paragraph "Colour grids, objects and the frame plane" of
> [`SYSTEM.md`](../SYSTEM.md), §20.52 of
> [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), To-Do items 9 and 10 of
> [`STATUS.md`](../STATUS.md), the rows of `tests/README.md` for
> `test_colour_induction.py` and `test_frame_plane.py`, and §0 of
> [`IMPROPER_FRAME_STUDY.md`](IMPROPER_FRAME_STUDY.md). The records name the
> missed marks and give the figures; the wording of each mark was not recorded
> anywhere that survived. No figure appears that the records do not give.

## 0. What this document is

A study for Phase 178, taken from the To-Do list (`STATUS.md` §2.1 items 9
and 10), at the owner's request of 22 October 2026, which also asked for §2.0
of `STATUS.md` to be condensed and for a watch on wiring as the round goes.

**Part A** carries the agreement gate of `tool induce`
([`PIPELINE_KIT_STUDY.md`](PIPELINE_KIT_STUDY.md), Phase 175;
[`PIPELINE_ASK_STUDY.md`](PIPELINE_ASK_STUDY.md), Phase 176) from 0/1 grids of
one shape to colour grids whose shape may change, with the two rules the
frame-operator study ([`FRAME_OPERATOR_STUDY.md`](FRAME_OPERATOR_STUDY.md),
Phase 177) left: **read the invariant first**, and **count evidence by span**.
**Part B** widens `tool frame` from `(E, p)` to `(E, px, py)`.

## 1. Part A — what was built

* **`reasoning/colour_induction.py`**: the gate of `tool induce` on colour
  grids whose shape may change. The vocabulary holds whole-grid operators
  (the eight symmetries, gravity, crops, scaling, tiling, mirrors, halves,
  symmetry completion), their two-step compositions, and fitted families (a
  colour map, object recolouring by size, rank or border contact, enclosed
  fill, half logic across a divider). Each pair is read first for what it
  keeps (shape, colour counts, colour set). A colour map fits a pair exactly
  when the output is a function of the input cell by cell
  (`fit_iff_functional`), so a fit is no evidence: a fitted family counts as
  tested only when leave-one-out reproduces the pair left out. The query is
  answered only when every survivor agrees and one is tested, and a fitted
  survivor whose parameter the query needs but the demonstrations never showed
  forces a refusal (`unread_fitted_refuses`).
* **`tool arc NAME`** runs it on a stored ARC task and grades every test
  answer.
* **`reasoning/colour_induction_study.py`**, `tools colour-induction`: the
  marks of part A.

## 2. Part A — the marks

C1–C6 (the synthetic colour families), R1–R3 (the stored ARC tasks), B, L
(`ColourInduction.lean`) and T. The records name the four that were missed and
what each missed by; their wording is lost.

| mark | what the records attach to it |
|---|---|
| **C1** | not attached by the records |
| **C2** | coverage at three demonstrations against the declared 90 % |
| **C3** | not attached by the records |
| **C4** | the span rule preventing a wrong answer the shipped gate would otherwise give |
| **C5** | not attached by the records |
| **C6** | not attached by the records |
| **R1** | not attached by the records |
| **R2** | the stored ARC tasks (missed on 2 of 50 right, the vision stack's 2) |
| **R3** | the stored ARC tasks (missed on 2 of 50 right, 48 unsolved) |
| **B** | not attached by the records (the round recorded binary tasks unchanged, 200 of 200) |
| **L** | not attached by the records (`ColourInduction.lean`, 12 theorems) |
| **T** | not attached by the records |

## 3. Part A — what came out

### 3.1 The marks (second take, the measurement of record)

| mark | recorded result | outcome |
|---|---|---|
| **C1** | — | met |
| **C2** | 302 of 360 at three demonstrations, below the declared 90 % | missed |
| **C3** | — | met |
| **C4** | the span rule prevented no wrong answer and cost 83 right answers | missed |
| **C5** | — | met |
| **C6** | — | met |
| **R1** | — | met |
| **R2** | ARC 2 of 50 right — the vision stack's 2 | missed |
| **R3** | ARC 2 of 50 right, 48 unsolved | missed |
| **B** | — | met |
| **L** | — | met |
| **T** | — | met |

**8 of 12 marks**, at each of the two takes. The outcomes of the marks the
records do not attach a result to follow from the count: four are named as
missed, and twelve less four is eight. Which recorded figure each of them was
read from (the ARC tasks' 0 wrong, the binary tasks' 200 of 200, the Lean
build) is not recorded.

### 3.2 The two takes

**Take 1:** 10 wrong in-vocabulary answers — a set-aside fitted survivor was
the rule, and a generator background artefact. **Take 2**, after the unread
rule (a fitted survivor whose parameter the query needs but the demonstrations
never showed forces a refusal) and one background per task: 683 right, 0
wrong, 397 refused of 1,080 in-vocabulary queries. Coverage at three
demonstrations 302 of 360 (C2 missed); of the refusals, 192 are disagreements
and 122 unread parameters, refusals an ask could resolve. Once unread
survivors refuse, the span rule prevented no wrong answer and cost 83 (C4
missed). On the 50 stored ARC tasks the solver answered the same 2 tasks the
vision stack solves, with 0 wrong; 48 tasks lie outside the vocabulary (R2, R3
missed). Partly, then: on colour grids the gate gives 0 wrong answers in its vocabulary but
falls short of the declared coverage, and on the stored ARC tasks it answers
only the 2 the vision stack solves, with 0 wrong — the vocabulary binds, not
the gate.

## 4. Part B — what was built

* **`reasoning/frame_plane.py`**: `tool frame` on `(E, px, py)`, with the Gram
  matrix invariant layer, completion from pairs, leave-one-out testing, the
  Wigner decomposition and the span guard. Six families: identity, units,
  rotation, pure boost, proper orthochronous Lorentz, Lorentz times units. A
  Lorentz answer is split into a pure boost times its Wigner rotation
  (`GLM.LorentzPlane.thomas_wigner`).
* **The span guard**: a query outside the span of the demonstrations is
  answered only when they span all three dimensions.
* **`reasoning/frame_plane_study.py`**, `tools frame-plane`: the marks of
  part B.

## 5. Part B — the marks

P1–P6, L (`LorentzPlane.lean`) and T. The wording of each is lost; the records
give the figures of §6 and the outcome of every mark at each take.

| mark | what the records attach to it |
|---|---|
| **P1** | not attached by the records |
| **P2** | not attached by the records |
| **P3** | not attached by the records |
| **P4** | not attached by the records |
| **P5** | not attached by the records |
| **P6** | not attached by the records |
| **L** | not attached by the records (`LorentzPlane.lean`, 13 theorems) |
| **T** | not attached by the records |

## 6. Part B — what came out

| mark | outcome (second take) |
|---|---|
| **P1** | met |
| **P2** | met |
| **P3** | met |
| **P4** | met |
| **P5** | met |
| **P6** | met |
| **L** | met |
| **T** | met |

**Take 1: 7 of 8** — 6 wrong answers outside the families, from
rank-deficient demonstrations. **Take 2**, with the span guard: **8 of 8** —
536 right, 0 wrong of 1,080 queries inside the families, 0 wrong of 360
outside; Thomas–Wigner 60 of 60, every one with the exact Wigner rotation;
2-component tasks unchanged, 200 of 200. The reflection `py -> -py` and time
reversal `E -> -E` were measured as outside families: refused, every one of 240
queries (as [`IMPROPER_FRAME_STUDY.md`](IMPROPER_FRAME_STUDY.md) §0 records).
`tool frame` in 1+2 dimensions gives 0 wrong answers inside and outside its
families and reads all 60 Thomas–Wigner queries with their exact Wigner
rotation.

## 7. The Lean files and the wiring

* **`ColourInduction.lean`** (12 theorems): every cell permutation keeps the
  colour counts (`count_perm`), a colour map fits a pair exactly when the
  output is a function of the input cell by cell (`fit_iff_functional`), the
  gate is sound (`gate_sound`), never answers untested
  (`untested_never_answers`) and refuses when a fitted survivor's parameter is
  unread (`unread_fitted_refuses`).
* **`LorentzPlane.lean`** (13 theorems): boosts along both axes and rotations
  are Lorentz, the Minkowski form is kept, and `B_x(1/2) B_y(1/2)` is the pure
  boost to `(25/9, −20/9, −4/3)` times the rotation `(15/17, −8/17)`
  (`thomas_wigner`), not itself a boost.
* Both were in `AxiomAuditAll.lean` (9,757 theorems, standard axioms only);
  `lake build` succeeded, 0 `sorry`.
* **Wiring.** `tool induce` sends colour or shape-changing tasks to the colour
  solver (binary tasks unchanged, 200 of 200); `tool arc NAME` is new; `tool
  frame` sends 3-component states to the frame plane (2-component unchanged,
  200 of 200); English routes were added for `tool arc` (*solve the ARC task
  …*), `tool frame` (*which operator maps …*) and `tool kappa` (*what is the
  anchor kappa*), which had none. `tests/test_connected_machine.py`'s module
  set names `colour_induction`. Both studies are `tools` subcommands
  (`colour-induction`, `frame-plane`), declared measurement-only in the wiring
  census. `.gitignore` was restored (it was missing) and the tracked Python
  bytecode untracked.
* Tests: `tests/test_colour_induction.py` (10) and `tests/test_frame_plane.py`
  (7), run by hand: all passed (pytest was not installed).

## 8. Disclosed, and the state of the files

**Disclosed by the round.** `tool arc 1e0a9b12` was run once before the marks
were committed; a post-hoc probe of local-rule families gave 0 new ARC solves
and was reverted.

**At this reconstruction (31 October 2026).** `reasoning/colour_induction.py`,
`reasoning/colour_induction_study.py`, `reasoning/frame_plane.py` and
`reasoning/frame_plane_study.py` are in the tree, but the two study modules
(and `colour_induction.py`) were themselves reconstructed on 31 October 2026:
their docstrings say that the marks' wording, the task families and the
generators are the reconstruction's, not the lost originals, and that the
figures they give are their own. A measurement they store is therefore not
this round's: §8.1 gives it apart from the record, and nothing above is
changed by it. The two test files of §7 are in the tree
(`src/glm_universal/tests/`), also reconstructed on 31 October 2026 against the
reconstructed modules. `ColourInduction.lean` and `LorentzPlane.lean` are not in
the tree (recorded missing in [`_lean_files_needed.md`](_lean_files_needed.md);
`LorentzImproper.lean` is held until `LorentzPlane.lean` returns); until they
return, the tests' Lean checks only confirm that each file is recorded missing
and that the study reads it as absent, and mark L of each part is not met.

### 8.1 The reconstructed modules re-measured (31 October 2026)

*Added 31 October 2026 (repository check).* The two reconstructed study
modules were re-measured on 31 October 2026, in the same repository check; the
measurements are stored in `reasoning/_data/colour_induction_study.json` and
`reasoning/_data/frame_plane_study.json`, and the figures below are read from
those files. They are **the reconstruction's figures, not the round's**: the
generators, the task families and the wording of every mark are the
reconstruction's (each module's docstring gives them), so they neither replace
the record of §§3 and 6 nor enter the tier-0 block. They are given here because
they differ from the record, and where they differ is said.

**Part A.** The reconstruction's generator: twelve in-vocabulary families
(`flip_h`, `gravity_down`, `crop`, `scale2`, `tile2x2`, `mirror_h`,
`complete_h`, `flip_v_then_scale2`, `colour_map`, `recolour_by_size`,
`enclosed_fill`, `half_logic`), thirty queries each at two, three and four
demonstrations (1,080 queries), and four families outside the vocabulary
(`translate_right`, `extend_right`, `hollow`, `count_bar`; 360 queries). The
solvers are the shipped gate, the gate without the span rule, the first take
(an unread survivor set aside rather than refused) and an eager control (the
first survivor answers).

| mark | the reconstruction's figure | outcome | the round's record (§3.1) |
|---|---|---|---|
| **C1** | 942 right, 0 wrong, 138 refused of 1,080 in-vocabulary queries | met | met |
| **C2** | 333 of 360 at three demonstrations, against the declared 90 % | met | missed (302 of 360) |
| **C3** | outside the vocabulary 7 right, 2 wrong, 351 refused of 360 (the re-measurement names the rules that answered: `translate_right` by `gravity_right`, `count_bar` by gravity then crop) | missed | met |
| **C4** | the span rule prevented no wrong answer and cost 15 right answers | missed | missed (cost 83) |
| **C5** | the invariant reading skipped 403,660 hypotheses over 1,440 queries and changed no verdict and no answer | met | met |
| **C6** | the eager control gives 5 wrong in-vocabulary answers (the first take 2) | met | met |
| **R1** | ARC: 0 wrong of the 50 stored tasks | met | met |
| **R2** | ARC: 2 right (`1e0a9b12`, `ae58858e`), the same 2 the vision stack solves | missed | missed |
| **R3** | ARC: 2 of 50 right, 48 refused | missed | missed |
| **B** | binary tasks unchanged, 200 of 200 | met | met |
| **L** | `ColourInduction.lean` is not in the tree | missed | met |
| **T** | a colour task answered through the colour solver; `tool arc 1e0a9b12` graded right | met | met |

**7 of 12 marks**, where the record gives 8 of 12: C2 is met here and missed
in the record, and C3 and L are missed here and met in the record (L because
the Lean file was lost). The in-vocabulary counts differ from the record's
683 right, 0 wrong and 397 refused because the generator differs; both give 0
wrong in the vocabulary.

**Part B.** The reconstruction's generator: nine families inside those of
Phase 178 (`identity`, `units`, `rotation`, `boost_x`, `boost_y`, `boost`,
`lorentz`, `thomas`, `lorentz_units`) and three outside (`reflect`,
`time_reverse`, `shear`; the first two are declared families since Phase 179),
thirty queries each at one to four demonstrations (1,080 queries inside, 360
outside). The solvers are the shipped gate, the same gate over the six families
of Phase 178 and a first-fit control.

| mark | the reconstruction's figure | outcome | the round's record (§6) |
|---|---|---|---|
| **P1** | inside: 533 right, 0 wrong, 547 refused of 1,080 | met | met |
| **P2** | 263 of 270 at three demonstrations, against the declared 95 % | met | met |
| **P3** | outside: 118 right, 0 wrong, 242 refused of 360 | met | met |
| **P4** | Thomas–Wigner 59 of 60, each of the 59 with the exact Wigner rotation; the one miss is a refusal (by the re-measurement's account, two proportional demonstration inputs span only two dimensions) | missed | met (60 of 60) |
| **P5** | the first-fit control gives 69 wrong answers (5 inside, 64 outside) | met | met |
| **P6** | 2-component tasks unchanged, 200 of 200 | met | met |
| **L** | `LorentzPlane.lean` is not in the tree | missed | met |
| **T** | the three-pair task of `B_x(1/2) B_y(1/2)` answered with the Wigner rotation `15/17, −8/17`, its one-pair version refused | met | met |

**6 of 8 marks**, where the record gives 8 of 8: P4 and L are missed here. The
record's figures inside the families (536 right, 0 wrong of 1,080) and for
Thomas–Wigner (60 of 60) are not reproduced by the reconstruction's generator;
both give 0 wrong inside and outside the families.

## 9. What is left

**Rule induction** (`STATUS.md` §2.1 item 9):

* a wider vocabulary that pays its way on real grids (per-object operators,
  line drawing, local rules — a first try at local rules gave 0 new solves and
  was not shipped), measured on a **fresh held-out ARC set**: the 50 stored
  tasks are no longer held out for this solver;
* asking for the separating example on colour tasks (C2 missed: 302 of 360 at
  three demonstrations; 192 disagreements and 122 unread parameters are
  refusals an ask could resolve);
* a family set on which the span rule prevents an error the unread rule does
  not (C4 missed at the second take: the span rule cost 83 right answers and
  prevented none);
* chains of three or more steps under a declared cost bound per step (D13)
  rather than enumeration;
* when choosing the example, count *no output* as a reply of its own; hold the
  ask open in the conversation and read the reply back as a demonstration;
* re-running the kit's neural learners on the exact labels (needs
  `numpy`/`torch`).

**Frame operators** (`STATUS.md` §2.1 item 10): improper maps (reflections,
time reversal) as declared families rather than refusals — taken by Phase 179
([`IMPROPER_FRAME_STUDY.md`](IMPROPER_FRAME_STUDY.md)), whose theorem
`plane_partner` is the reason for this round's span guard, which had been
argued from a measurement; 3+1 dimensions; holding `tool frame`'s ask open in
the conversation.

## In one paragraph

Phase 178 carries the agreement gate of `tool induce` from 0/1 grids to colour
grids whose shape may change, reading the invariant first and counting
evidence by span; a fitted family counts as tested only when leave-one-out
reproduces the pair left out, and an unread fitted parameter forces a refusal.
On 1,080 in-vocabulary queries the second take gave 683 right, 0 wrong and 397
refusals, but coverage at three demonstrations was 302 of 360, below the
declared 90 %, and the span rule prevented no error once unread survivors
refuse; on the 50 stored ARC tasks the solver answered the vision stack's 2,
with 0 wrong. The same round widened `tool frame` to 1+2 dimensions: after the
span guard, 536 right and 0 wrong inside its families, 0 wrong outside, and all
60 Thomas–Wigner queries read with their exact Wigner rotation. Part A 8 of 12
marks, part B 8 of 8.
