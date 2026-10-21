# The pipeline kit in the GLM — rules induced from demonstrations, answered only when every fitting rule agrees

## Tier 0 — the coarse read

**Question.** Can the owner's 9-iteration pipeline kit be brought into the GLM so that it solves tasks given as demonstrations, closes the two task families the kit left open, chains two operators when one does not fit, works on bit strings as well as grids, and never gives a wrong answer it could have refused?

**Verdict.** Yes, within its operator vocabulary. The kit's bridge, never run before, holds on the GLM's own substrate; its seven Lean files build in the GLM's development; `tool induce` keeps every operator hypothesis that fits all the demonstrations, single operators and two-step compositions together, and answers only when they all agree. Over 2,250 queries in fifteen families it gave 0 wrong answers at a cost of 129 refusals, closed both open families (49 of 50 each at four demonstrations), and answered at least 47 of 50 queries of every two-step and bit-string family; the two controls that answer more eagerly gave 12 and 19 wrong answers. Lean proves the gate sound: an answer is the true rule's whenever the true rule is in the tier read, and refusing is forced when two fitting rules disagree.

**Deciding figure.** 12 of 12 marks; wrong answers 0 of 2,250 (controls: 12 and 19); flood fill and shortest path 0 → 49 of 50 each at four demonstrations; the three two-step families 0 → 47, 50 and 50 of 50; bridge failures 0 in 2,000 words.

**Recomputed by.** `glm_universal.reasoning.pipeline_kit_study.pipeline_kit_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 21 October 2026 (measured the same day, in one session). The marks
were written after one exploratory pass, not before any measurement; what that
pass changed is §7.2, and one mark was narrowed after its first take, §7.3.*

## 0. What this document is

A study for Phase 175, taken at the owner's request of 21 October 2026: the
files of the 9-iteration GLM pipeline study were delivered into
[`source_material/GLM_Pipeline_Kit/`](../source_material/GLM_Pipeline_Kit/README.md)
(its `README.md`, `FINDINGS.md`, `worklog.md`, the original study document
`ARC_20Oct2026.txt`, and the condensed files split back into `python/glm_kit/`
(9 modules), `GLMKit/` (7 Lean files), `scripts/` (40) and `data/` (22)), with
the instruction to use the methods to raise the GLM's reasoning and its task
steps — designed for ARC-style puzzles, but not to be confined to them.

The kit's own audit (`FINDINGS.md`) names three things to do inside the GLM:
run `glm_bridge.check_substrate(leech2)`; give `flood_fill` and
`bfs_shortest` a verified operator; and put the exact rules (parity wall,
8× embedding, junction label, parity analogy, permutation operator) where the
study had learned heads. This round does the first two, uses the third as the
solver's measuring step and layer filter, and adds composition.

## 1. What is proved

**The kit's seven files**, unchanged but for their imports, under
`overlay/glm_lean/RequestProject/GLM/PipelineKit/` (`Golay`, `Leech`,
`Lattices`, `Pless`, `Fields`, `Analogy`, `Permutation`; namespace `GLMKit`;
0 `sorry`). Their finite facts are discharged by `native_decide`, so those
results carry `Lean.ofReduceBool` and `Lean.trustCompiler` as well as the
standard axioms; the kit's `README.md` §2 lists what each file proves.

**The solver**, `overlay/glm_lean/RequestProject/GLM/PipelineInduction.lean`
(namespace `GLM.PipelineInduction`; 17 theorems, 0 `sorry`). A hypothesis is a
function `α → β`; it is *consistent* with demonstrations `(x, y)` when it maps
every `x` to its `y`. Hypotheses come in tiers; `solve` reads the first tier
with a consistent member and answers only when all its consistent members
agree on the query.

* `truth_consistent` — the rule that made the demonstrations fits them.
* `agree_sound` — if the true rule is in a class and every consistent member
  agrees on the query, that answer is the true rule's.
* `ambiguous_forces_refusal` — if two consistent members disagree, every
  answer is wrong for some member that fits everything seen.
* `consistentIn_more_demos` — a further demonstration only removes
  hypotheses.
* `solve_sound` — **the tiered solver's answer is the true rule's whenever the
  true rule is in the tier it read**, i.e. every earlier tier had no
  consistent member.
* `solve_refuses_disagreement`, `solve_answers_agreement` — it refuses exactly
  when that tier disagrees.
* `solve_never_invents` — every answer is the output of a hypothesis that fits
  every demonstration; `solve_none_of_unfit` — with none, it refuses.
* `perm_toggle_layer` — a cell permutation followed by a toggle keeps a
  24-cell word on the same `4×` Leech layer (from the kit's
  `leech_layer_perm` and `leech_layer_toggle`; this one inherits the kit's
  `native_decide`).

`solve_sound`, `solve_never_invents` and `solve_none_of_unfit` use `propext`
and `Quot.sound` only. What Lean does *not* say is whether a task's true rule
lies in the tier the solver reads; that is a property of the task family, and
the wrong-answer counts below measure it.

## 2. The mechanism

`overlay/glm_universal/reasoning/pipeline_kit.py`, reached as `tool induce`
(`GLM.py -q "tool induce IN -> OUT ; IN -> OUT ? QUERY"`, grids as rows of 0s
and 1s split by `/`; a one-row grid is a bit string). The English opening
"induce the rule from … ? …" reaches it too, after the planner refuses.

1. **Encode and measure** (the kit's first steps, on the GLM's substrate): the
   query's 24-bit word, its weight, whether `4b` and `8b` are Leech points
   (`leech2.in_leech`), and its class modulo `2Λ` (`leech2.class_of`).
2. **Hypothesise.** Tier 1: the single operators — the kit's cell
   permutations (three mirrors, cyclic shifts by up to two cells, the same
   keeping the last row; on a square grid also the transpose and quarter
   turns), complement, the constant XOR mask fitted from the pairs, and two
   new operators: the **region fill** (every empty cell not connected to the
   border through empty cells) and the **two-point path writer** (vertical leg
   first, or horizontal first, from the first set cell). Two-step
   compositions of any two of these, and "a permutation, then a fitted mask",
   are read **in the same tier** (the shipped `union` reading; §7.2). Tier 2:
   a cell permutation learned cell by cell from the pairs (the kit's
   fallback).
3. **Filter by layer.** A cell permutation keeps weight (`wt_comp_perm`), so if
   any demonstration changes the weight, no permutation is tried — 2,653
   hypotheses skipped per query on the 4×6 families whose rule changes the
   weight.
4. **Evidence guard.** A fitted mask is offered only when at least two
   distinct demonstrations exist: one pair fits a mask to any rule at all.
5. **Collapse or refuse.** The answer is given only if every surviving
   hypothesis gives the query the same grid; otherwise the refusal names the
   disagreeing hypotheses and how many answers they give, and — when the
   single operators alone would have answered — says what they would have
   said and why it is not asserted.

## 3. What is measured

`overlay/glm_universal/reasoning/pipeline_kit_study.py`
(`python3 -m glm_universal.tools pipeline-kit`, about a minute). Fifteen
families, fifty queries each, at two, three and four demonstrations — 2,250
queries per configuration. Samples come from a fixed integer recurrence, not a
random source.

* **kit** (5): the study's `toggle`, `translate`, `reflect_v`, `flood_fill`,
  `bfs_shortest`;
* **single** (3): `reflect_h`, `rotate180`, `path_hv`;
* **steps** (3): `reflect_v_then_toggle`, `fill_then_reflect_h`,
  `path_then_rotate180` — two operators in turn;
* **string** (4): one-row grids of 24 bits: reverse, rotate, complement,
  reverse-then-complement.

Four configurations: **shipped**; **occam** (single operators read as a tier
before compositions); **no gate** (occam, and the first fitting hypothesis
answers whether or not the others agree); **kit** (the kit as delivered: its
permutations and fitted mask and learned permutation, no new operator, no
composition).

## 4. Faculties

Under [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) §1: **derive** and **refuse**.
Every answer is computed from the demonstrations by an operator; no register
holds it. Every wrong answer the controls give and the shipped solver does not
is a refusal at a counted cost. Nothing here is addressing.

## 5. The marks

| mark | what | result |
|---|---|---|
| **B** | the kit's bridge on the GLM's `leech2`: parity wall, parity wall with glue, 8× embedding, junction parity | 0, 0, 0, 0 failures in 2,000 words |
| **L1** | `PipelineInduction.lean` states its 17 theorems, no `sorry` | 17 of 17, 0 |
| **L2** | the kit's seven Lean files present, no `sorry` | 7 of 7, 0 |
| **K** | the kit as delivered, four demonstrations: toggle, translate, reflect_v 50 right; flood_fill, bfs_shortest 0 right | 50, 50, 50; 0, 0 — reproduced |
| **D** | flood_fill and bfs_shortest at least 45 of 50 right, 0 wrong | 49 and 49, 0 wrong |
| **S** | each two-step family at least 45 of 50, 0 wrong; the kit 0 | 47, 50, 50; kit 0, 0, 0 |
| **G** | each bit-string family at least 45 of 50, 0 wrong | 50, 50, 50, 50 |
| **R** | shipped: 0 wrong over 2,250; occam and no gate: more than 0 | 0 (129 refused); 12; 19 |
| **M** | no fixed-vocabulary hypothesis surviving more demonstrations that did not survive fewer | 0 in 1,500 nested reads |
| **W** | the layer filter changes no answer, and filters on every weight-changing family | 0 changed; 9 of 9 |
| **A** | iteration 8's threshold decode on toggle analogies with `A ≠ C`; the parity decode | 0 of 30; 30 of 30 |
| **T** | `tool induce` answers a fixed reflect task with the true grid and refuses an under-determined one | answered `010/110/001`; refused, ambiguous |

## 6. What is not claimed

* Not that the GLM solves ARC. The families are synthetic, binary, on small
  grids, and every one of them has its rule inside the operator vocabulary;
  real ARC tasks have colours, objects and rules outside it. What is shown is
  the *discipline*: within a stated vocabulary, the solver answers only what
  the demonstrations determine, and says so when they do not.
* Not that refusals are free: 129 of 2,250 queries were refused, most of them
  at two demonstrations.
* Not that the neural learners of iterations 1, 5, 6, 7 and 9 were re-run;
  the kit's audit marks them unverified, and this round did not run them.
* Not that the kit's cyclic Golay code and the GLM's MOG-ordered code are the
  same bitmask table; the bridge tests the *theorems*, which are stated for
  any binary code containing 0.

## 7. What came out

### 7.1 The table

Shipped solver, right / wrong / refused out of 50, at two, three and four
demonstrations; the kit as delivered at four; hypotheses skipped by the layer
filter at four (summed over the 50 queries).

| family | group | 2 | 3 | 4 | kit at 4 | layer-skipped |
|---|---|---|---|---|---|---|
| `toggle` | kit | 32 / 0 / 18 | 38 / 0 / 12 | 42 / 0 / 8 | 50 / 0 / 0 | 132650 |
| `translate` | kit | 42 / 0 / 8 | 46 / 0 / 4 | 49 / 0 / 1 | 50 / 0 / 0 | 0 |
| `reflect_v` | kit | 49 / 0 / 1 | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 0 |
| `flood_fill` | kit | 37 / 0 / 13 | 45 / 0 / 5 | 49 / 0 / 1 | 0 / 0 / 50 | 132650 |
| `bfs_shortest` | kit | 48 / 0 / 2 | 49 / 0 / 1 | 49 / 0 / 1 | 0 / 0 / 50 | 132650 |
| `reflect_h` | single | 42 / 0 / 8 | 49 / 0 / 1 | 50 / 0 / 0 | 50 / 0 / 0 | 0 |
| `rotate180` | single | 48 / 0 / 2 | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 0 |
| `path_hv` | single | 48 / 0 / 2 | 49 / 0 / 1 | 50 / 0 / 0 | 0 / 0 / 50 | 132650 |
| `reflect_v_then_toggle` | steps | 49 / 0 / 1 | 50 / 0 / 0 | 50 / 0 / 0 | 0 / 0 / 50 | 132650 |
| `fill_then_reflect_h` | steps | 29 / 0 / 21 | 41 / 0 / 9 | 47 / 0 / 3 | 0 / 0 / 50 | 132650 |
| `path_then_rotate180` | steps | 44 / 0 / 6 | 50 / 0 / 0 | 50 / 0 / 0 | 0 / 0 / 50 | 132650 |
| `string_reverse` | string | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 0 |
| `string_rotate` | string | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 0 |
| `string_complement` | string | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 2850 |
| `string_reverse_complement` | string | 50 / 0 / 0 | 50 / 0 / 0 | 50 / 0 / 0 | 0 / 0 / 50 | 2850 |

Totals over the 2,250 queries: shipped 2,121 right, 0 wrong, 129 refused;
occam 2,205 right, 12 wrong, 33 refused; no gate 2,231 right, 19 wrong; the
kit 1,199 right, 3 wrong, 1,048 refused. The kit's three wrong answers are
all on the path families at two demonstrations: twice both demonstrations
joined adjacent cells, so the output equalled the input and the identity
fitted; once a half-turn fitted a path drawn symmetrically. Every wrong answer of every
control came at two or three demonstrations; at four none gave one.

### 7.2 What the exploratory pass changed

The first pass read single operators before compositions (what is now the
`occam` control) and offered a fitted mask from a single distinct pair. It gave
12 wrong answers, all on `fill_then_reflect_h` and `path_then_rotate180`:
when every demonstration's rectangle happened to be symmetric top to bottom,
the fill alone fitted demonstrations made by "fill, then mirror", and the
solver never looked further. That is exactly the case `solve_sound` excludes —
the true rule was not in the tier read — so the fix was to read compositions in
the same tier as single operators, and the fill alone now meets "fill, then
mirror" and disagrees on the query. Two repeated demonstrations also let a mask
fit any rule; the evidence guard (§2, step 4) removed that. The cost of both is
the difference between 33 and 129 refusals.

The largest single cost is `toggle` at 8 to 18 refusals: on random grids a
region fill or a path writer often changes nothing on the demonstrations, so
"fill, then complement" fits as well as "complement" and disagrees on a query
with an enclosed hole. Given only the vocabulary and the demonstrations, the
refusal is correct (`ambiguous_forces_refusal`); a vocabulary weighted by
simplicity would answer, at the price of the wrong answers in §7.1's controls.

### 7.3 One mark narrowed after its first take

M was first declared over every hypothesis, and failed: 16 exceptions in 1,500
nested reads. All 16 were fitted masks on `translate`, whose first two
demonstrations are often the same pair — a mask appears only when the second
distinct pair arrives (the evidence guard). The Lean theorem is about a fixed
class, and the masks are fitted, so M now counts the fixed vocabulary and
reports the fitted appearances (16) beside it. Nothing else was restated.

### 7.4 What this answers, and what is left

The owner asked whether the kit's methods raise the GLM's reasoning and task
steps. Measured: the GLM now has a tool that derives an answer from examples
by search over a stated vocabulary, chains two operators when one does not
fit, refuses with a reason when the examples under-determine the rule, and does
so on bit strings as on grids. Three lines are left:

* **colours and objects** — the operators are binary; an ARC grid has ten
  colours, and the next vocabulary is per-colour masks, object extraction and
  per-object operators;
* **deeper chains** — two steps are searched exhaustively (3,424 hypotheses on
  a 4×6 grid); three would need the layer filter and a cost bound per step
  (D13) rather than enumeration;
* **asking for the deciding demonstration** — when the solver refuses, it
  knows which hypotheses disagree; choosing the query that would separate
  them, and asking the user for that one, is the conversational step the
  stacked dialogue of Phase 173 already supports.

## In one paragraph

Yes, within its operator vocabulary. The kit's bridge, never run before, holds on the GLM's own substrate; its seven Lean files build in the GLM's development; `tool induce` keeps every operator hypothesis that fits all the demonstrations, single operators and two-step compositions together, and answers only when they all agree. Over 2,250 queries in fifteen families it gave 0 wrong answers at a cost of 129 refusals, closed both open families (49 of 50 each at four demonstrations), and answered at least 47 of 50 queries of every two-step and bit-string family; the two controls that answer more eagerly gave 12 and 19 wrong answers. Lean proves the gate sound: an answer is the true rule's whenever the true rule is in the tier read, and refusing is forced when two fitting rules disagree.
