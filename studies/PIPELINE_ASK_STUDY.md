# Asking for the separating example — and the pipeline kit's late files

## Tier 0 — the coarse read

**Question.** When `tool induce` refuses because two rules that fit every demonstration disagree on the query, can the GLM name the one further example that would settle it, and does asking for it turn refusals into right answers without ever producing a wrong one? And do the pipeline kit's five late files (its test suite, its demo, its axiom audit and its Lean root) hold up inside the GLM?

**Verdict.** Yes to both. Of the 2,250 queries of Phase 175, the 129 refused as ambiguous were handed to the new ask loop with the family's true rule replying: 127 were answered right after exactly one ask, 0 wrong, 2 still refused. Every ask removed survivors, as `separating_strict_shrink` proves it must. The kit's own suite passes unchanged (14 of 14), its demo table is reproduced exactly, and on the demo's 250 queries, drawn from the kit's own task generator, `tool induce` gives 235 right and 0 wrong against the kit's 149. The kit's audit became a check the build enforces: every one of the 9,582 theorems of the development rests on the standard axioms only.

**Deciding figure.** 8 of 8 ask marks and 4 of 4 cross-check marks; ambiguous refusals answered right after asking 127 of 129, wrong 0; asks 128; kit demo protocol 235 right, 0 wrong (kit 149, 0); axiom guard 9,582 theorems.

**Recomputed by.** `glm_universal.reasoning.pipeline_ask_study.pipeline_ask_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 21 October 2026. The ask marks (§5) were written into
`reasoning/pipeline_ask_study.py` before the first measurement and taken once,
the same day. The cross-check's third mark was narrowed after its first take
(§7.3).*

## 0. What this document is

A study for Phase 176, taken at the owner's request of 21 October 2026, in two
parts.

**Part 1, the late files.** Phase 175 brought the owner's pipeline kit into
the GLM without five files its `README.md` names. They arrived this round and
were placed in the kit's folder,
[`source_material/GLM_Pipeline_Kit/`](../source_material/GLM_Pipeline_Kit/README.md),
as the owner asked: `python/tests/test_kit.py`, `python/run_pipeline_demo.py`,
`GLMKit/AxiomAudit.lean`, and the Lean root `GLMKit.lean`, `lakefile.toml` and
`lean-toolchain` (uploaded as `lean-toolchain.txt`, renamed back). The upload
had overwritten the repository's own `lakefile.toml` with the kit's; the
repository's file (`srcDir = "overlay/glm_lean"`, library `RequestProject`)
was restored, and the kit's copy kept in the kit folder.

**Part 2, a To-Do line.** `STATUS.md` §2.1 item 9 asked, among other things:
*when it refuses, choose the query grid that would separate the disagreeing
hypotheses and ask for its output.* This round does that.

## 1. What is proved

**`overlay/glm_lean/RequestProject/GLM/PipelineAsk.lean`** (namespace
`GLM.PipelineAsk`; 7 theorems, 0 `sorry`), for any input type, output type and
hypothesis class `H`, the reply given by the true rule `f`:

* `separating_demo_removes` — after the reply to an input on which two
  hypotheses differ, they cannot both still fit;
* `consistentIn_cons` — a new demonstration filters the survivors by agreement
  on it;
* `separating_strict_shrink` — so the number of survivors drops by at least
  one;
* `truth_survives_asks` — the true rule keeps fitting however many replies are
  added;
* `asks_shrink` — after `k` separating asks at least `k` members have gone;
* `asks_bounded` — with the true rule in `H`, at most `|H| − 1` separating asks
  can be made: the loop stops;
* `ask_then_sound` — whatever the gate answers after the asks is the true
  rule's answer.

Not proved: that one ask suffices, or that the declared pool holds a
separating input. Both are measured.

**`overlay/glm_lean/RequestProject/GLM/AxiomGuard.lean`** turns the kit's
`AxiomAudit.lean` (a list of `#print axioms` lines to be read by eye) into
commands that fail the build: `#guard_axioms n₁ n₂ …`,
`#guard_axioms_prefix P` and `#guard_axioms_development`. The accepted set is
`propext`, `Classical.choice`, `Quot.sound`, `Lean.ofReduceBool`,
`Lean.trustCompiler` and the axioms `native_decide`/`bv_decide` generate; a
hand-written axiom or the `sorryAx` an unfinished proof leaves fails it. It
was checked against a scratch file: a `decide` proof, a `native_decide` proof
and `Classical.em` pass; a `sorry` proof and a proof from a declared axiom are
each rejected with the offending axiom named.

* `PipelineKit/AxiomAudit.lean` guards the owner's 25 names unchanged, the 17
  theorems of `PipelineInduction.lean`, and all 130 theorems in the `GLMKit`
  namespace;
* `AxiomAuditAll.lean` imports every Lean file of the development and guards
  every theorem in it, so the build enforces the audit: 9,582 theorems, standard axioms only. A test fails if a
  Lean file is missing from its import list.

The kit as delivered was also built on its own, with its own `lakefile.toml`
and `lean-toolchain` (Lean 4.28.0, Mathlib v4.28.0): it builds, and its
`AxiomAudit.lean` prints only standard axioms for all 25 names. The GLM's
copies of the seven files differ from the delivered ones only in their import
lines and a dated header.

## 2. The mechanism

`reasoning/pipeline_ask.py`. When the shipped solver's result is `ambiguous`,
`separating_input` looks over a declared pool of inputs of the query's shape:
every one-cell change of the query and of each demonstration input, then 24
seeded random grids with the query's weight, 24 for each demonstration
input's weight, and 24 of any weight — never the query itself (asking for the
query's output would be asking for the answer) and never a demonstration
input. An input is usable when every surviving hypothesis gives it an output
and at least two outputs differ. Among usable inputs it takes the one whose
worst reply leaves the fewest distinct answers to the query, then the fewest
survivors. `ask_loop` asks, adds the reply as a demonstration, and solves
again, at most three times.

`tool induce` now ends an ambiguous refusal with the sentence *to settle it,
give the output for X — the fitting hypotheses split n ways there, and …*,
and returns the input as the figure `ask`. On Phase 175's under-determined
example (one demonstration of a 3×3 grid, 332 fitting hypotheses giving 12
answers) it names `010/000/001`, on which the 332 split 12 ways and after
which the query is decided whatever the reply.

`reasoning/pipeline_kit_crosscheck.py` runs the kit's late Python files
against the GLM: the kit's suite unchanged, and the demo's protocol (five
families, 50 queries, four demonstrations, seeds `1000(s+1)+k` and
`1000(s+1)+999`, drawn from the **kit's** generator `glm_kit.tasks`) scored
for the kit's solver and for the GLM's.

## 3. What is measured

`tools pipeline-ask --write` (about half a minute): Phase 175's 2,250 queries
(fifteen families, 50 queries, two, three and four demonstrations) with the
shipped solver; every `ambiguous` refusal goes to `ask_loop` with the family's
true rule as the oracle (`TRUE_RULES`; a test checks each reproduces its
family's generator). The control asks for the first separating input of the
pool, unscored.

`tools pipeline-kit-crosscheck` (a few seconds, nothing stored).

## 4. Faculties

Asking (a refusal now carries the question that would remove it), and audit
(the axiom check is part of the build instead of a reading).

## 5. The marks

Declared before measuring (`pipeline_ask_study.py`):

| mark | statement |
|---|---|
| A1 | after asking, 0 ambiguous refusals answered wrongly |
| A2 | at least 80% of them answered right within three asks |
| A3 | of those right, at least half needed exactly one ask |
| A4 | for at least 95% of them the pool holds a separating input |
| A5 | every ask leaves a strict subset of the survivors, new fitted hypotheses apart — 0 exceptions |
| A6 | the scored choice needs no more asks in total than the first-separating control |
| L | `PipelineAsk.lean` states its theorems with no `sorry` |
| T | `tool induce`'s refusal of the under-determined example names an input |

The cross-check (`pipeline_kit_crosscheck.py`): K1 the kit's suite, 14 tests,
0 failures; K2 the README's demo table reproduced exactly; K3 `tool induce`
on the demo's 250 queries, 0 wrong and more right than the kit in total; K4
every refusal there is forced (status `ambiguous`).

## 6. What is not claimed

The oracle is the true rule, so the measurement says what asking buys when
the owner answers correctly; it says nothing about a wrong reply. The tasks
are synthetic two-colour grids and bit strings. The ask is put by the tool's
text; the conversation does not yet hold it open and read the reply back as
a demonstration. That `asks_bounded` bounds the loop needs the true rule in
the class, as `solve_sound` does.

## 7. What came out

### 7.1 The ask

Queries 2,250; refused as ambiguous 129, each handed to the ask loop with the
family's true rule replying. After at most three asks: right 127,
wrong 0, still refused 2; asks 128, every right answer after exactly one ask.
Every ask removed survivors, as `separating_strict_shrink` proves it must:
shrink exceptions 0 of 128 asks (8 asks saw a fitted hypothesis appear with
the new demonstration, counted, not excepted). No separating input in the
pool: 1.

| family | ambiguous | right after asking | wrong | still refused |
|---|---|---|---|---|
| toggle | 38 | 38 | 0 | 0 |
| fill_then_reflect_h | 33 | 33 | 0 | 0 |
| flood_fill | 19 | 19 | 0 | 0 |
| translate | 13 | 13 | 0 | 0 |
| reflect_h | 9 | 9 | 0 | 0 |
| path_then_rotate180 | 6 | 6 | 0 | 0 |
| bfs_shortest | 4 | 3 | 0 | 1 |
| path_hv | 3 | 2 | 0 | 1 |
| rotate180 | 2 | 2 | 0 | 0 |
| reflect_v | 1 | 1 | 0 | 0 |
| reflect_v_then_toggle | 1 | 1 | 0 | 0 |

8 of 8 marks. A6 holds only as a tie: the control also needed 128 asks and
got 127 right, 0 wrong. On this set one ask always sufficed, so the score
never had a second ask to save; it is the part of the mechanism this study
did not test.

### 7.2 The two left

Both are path tasks at two demonstrations where each demonstration's two
cells are adjacent, so the path is the input itself and the identity, both
path writers and over a hundred two-step compositions all fit. The usability
rule — every survivor must give the candidate an output — then fails: a
composition such as `path_vh then path_hv` has no output on most inputs. In
one case no input of the pool qualifies; in the other the first ask is made
and a second finds none. Counting *no output* as a reply of its own, which
removes every hypothesis that gives one when the true rule does not, would
reach both; it is the first item of §7.4.

### 7.3 The cross-check, and its third mark narrowed

| family | kit right/wrong/refused | GLM right/wrong/refused |
|---|---|---|
| toggle | 50/0/0 | 41/0/9 |
| translate | 49/0/1 | 46/0/4 |
| reflect_v | 50/0/0 | 50/0/0 |
| flood_fill | 0/0/50 | 48/0/2 |
| bfs_shortest | 0/0/50 | 50/0/0 |
| total | 149/0/101 | 235/0/15 |

K1 (the kit's suite passes unchanged: 14 tests, 0 failures, 0 errors) and K2 (every row of the README's table)
hold. K3 as first written asked for at least as many right as the kit on
*every* family, and failed on its first run: toggle 41 against 50, translate
46 against 49. The reason is the GLM's larger vocabulary. On toggle,
`complement then fill_enclosed` fits demonstrations with no enclosed region
and disagrees with `complement` on a query that has one; the kit, without
the fill, cannot see that tie and answers. K3 was narrowed to the total and
K4 added: all 15 of the GLM's refusals are forced (15 of 15 `ambiguous`), and
the per-family counts stay in the table. With this round's ask, each of
those 15 is a refusal that names its separating example.

### 7.4 What this answers, and what is left

The To-Do line's third clause is done: a refusal names the example that
would settle it, and asking for that example settled 127 of 129. Left:

* count *no output* as a reply when choosing the input (§7.2);
* hold the ask open in the conversation and read the reply back as a
  demonstration (the stacked dialogue of Phase 173 can carry it);
* a set where one ask does not suffice, to test the score against the
  control;
* the rest of item 9 as before: colours and objects, longer chains under a
  declared cost bound, and the kit's neural learners (needs `numpy`/`torch`).

## In one paragraph

Yes to both questions. `tool induce` now says, when it refuses, which further example would settle
the question, and asking for it works: of Phase 175's 129 ambiguous refusals,
127 became right answers after one ask and none became wrong, with Lean
proving that each separating ask removes a fitting rule, that the asking
stops, and that the answer it then gives is the true rule's. The pipeline
kit's late files hold up: its 14 tests pass unchanged, its demo table is
reproduced exactly, and on the kit's own tasks the GLM answers 235 of 250
right with none wrong where the kit answers 149. The kit's axiom audit became
a build-enforced guard: every one of the 9,582 theorems of the development
rests on the standard axioms only.
