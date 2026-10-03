# Discourse state: a tie carried as a column, the fourth shape of follow-up, and follow-ups on every surface

## Tier 0 — the coarse read

**Question.** Can the conversation carry what an earlier turn left behind further than one substituted name — a set a fold produced, *the one before that*, *both of them*, *why?* — and bind a follow-up whose rewritten question only another surface of the machine answers?

**Verdict.** Yes: a tie is now carried as a column of the rows' own answers, the fourth shape binds or refuses with a named reason, and a follow-up is licensed by every surface through the router, with every declared case as declared and 0 wrong.

**Deciding figure.** 29 of 29 declared follow-ups as declared (7 column, 16 fourth-shape, 6 surface), 0 wrong; Phase 55's layer gives 0 of the 20 new-behaviour cases as declared; the session alone as the licence answers 0 of the 5 surface answers; 15 of 15 of Phase 55's follow-ups keep their outcome but the 1 declared move; 32 of 32 column cells equal the answer asked alone; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.discourse_report.discourse_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 5 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md) and
[`STATUS.md`](../STATUS.md) §3.4: *discourse state* — candidate 0b (a tie
carried as a column, now that set folds exist), then D = 0a (the fourth shape
of follow-up), then K3 (bind conversation follow-ups on every surface, not
only the planner's). All three are the next round named by
[`CONVERSATION_STUDY.md`](CONVERSATION_STUDY.md) §8 and
[`CONNECTED_MACHINE_STUDY.md`](CONNECTED_MACHINE_STUDY.md) §6.

Before this round the conversation layer
([`runtime/conversation.py`](../overlay/glm_universal/runtime/conversation.py),
Phase 55) binds three surface shapes and refuses everything else: *describe
it* after the fourteen-row tie at the top of the lexicon's `abstract_concrete`
column is refused `ambiguous-antecedent`; *describe the one before that* binds
`that` as a pronoun to the newest name; *describe both of them* and *why?* are
not follow-ups at all; and a follow-up is licensed only when the **session**
answers its rewritten text, so *is the atomic number of it prime* after
*describe iron* — which the stepwise planner answers — is refused
`unlicensed`.

## 1. What *the answer for several rows at once* is

Candidate 0 asked for this statement before any code, and it was written at
the head of the declared cases before any code of the round:

* A fold whose end is attained by several rows **produced a set**. A later
  *it* or *them* names that set: the question is asked of every row, each by
  the same asker that would answer it written out in full, and the answer is
  the **column** of those answers in the fold's order.
* The column is answered only when every row answers. A row that does not is
  a hole, and a hole refuses the column (`column-incomplete`), exactly as a
  hole refuses a fold over a register column (Phase 85,
  [`HOLE_FOLDS_STUDY.md`](HOLE_FOLDS_STUDY.md)). When **no** row answers, the
  set does not decide and older turns are read, as for any unlicensed side.
* A column turn produces the same set again, so the set is **carried**: *field
  molar_mass_u of it* after *describe it* after the tie is a second column.
* A comparison's two rows are **not** a set the turn produced. *It* after
  *order atomic_weight_u of carbon and oxygen* is still
  `ambiguous-antecedent`; *both of them* names the pair.

## 2. The fourth shape, and the surfaces

* ***The one before that.*** *That* is the newest turn that decides; the
  referent is what the next older deciding turn decides (a row, a set, or the
  ambiguity refusal). Nothing before *that* is `no-antecedent`.
* **The plural** — *them*, *both of them*, *each of them*, *all of them*. A
  side of two or more names is read as a set (a fold's tie, a column, or the
  rows a turn was about). A single row reads on only for *both*, whose number
  is stated: to the single row of the next older deciding turn, the two in
  the order they were named. A plural with one referent, or *both* with other
  than two, is `number-mismatch`.
* ***Why?*** explains the turn before it from the record alone: the binding
  it made and the candidates it weighed, the refusal and its reason, or — for
  a whole query — its own derivation. It computes nothing.
* **Every surface (K3).** The licensing test is a parameter. With the router
  as the licence, a candidate is licensed when any surface answers the
  rewritten text, and a turn the typed or the stepwise planner answered names
  the register rows written in its question (the element and molecule
  tables' names, longest phrase first).
* **Whole first.** A text the machine already answers as written is a whole
  query, whatever words it holds — so the layer can add answers and can never
  change one the machine gives alone.

## 3. Declarations — written before any code of the round

The corpus is
[`evaluation/discourse_cases.py`](../overlay/glm_universal/evaluation/discourse_cases.py),
committed with §1 and before any code: 7 column cases (0b), 16 fourth-shape
cases (D = 0a: 4 for *the one before that*, 8 plural, 4 *why?*) and 6
surface cases (K3), each a whole conversation with its expected outcome — a
bound name, a column of named rows, the subject *why?* names, or a refusal
reason. One earlier declared outcome is declared to move (`DECLARED_MOVES`):
Phase 55's `pronoun-tie-refused` goes from `ambiguous-antecedent` to the
column of fourteen.

| mark | claim | measured by |
|---|---|---|
| **D1** | every column case gets its declared outcome; 0 wrong | `group_report` |
| **D2** | every fourth-shape case gets its declared outcome; 0 wrong | `group_report` |
| **D3** | every surface case, with the router as the licence, gets its declared outcome; 0 wrong | `group_report` |
| **D4** | the controls: Phase 55's layer gives none of the new-behaviour cases their declared outcome; the first-winner rule (bind the set's first row alone) answers every column case with one row in place of the column; the recency rule for *the one before that* (the second most recent mention) differs on at least one case; the session alone as the licence answers none of the surface cases' declared answers; with `carry=False` every tie case returns to `ambiguous-antecedent` | `control_report` |
| **D5** | nothing earlier moves: Phase 55's 15 declared follow-ups keep their outcomes under the new layer, but for the one declared move, which gets its declared column | `earlier_report` |
| **D6** | the column computes nothing: every cell of every column, and every single answer, equals what its rewritten text gets asked alone of a fresh asker | `cells_report` |
| **D7** | `RequestProject/GLM/DiscourseState.lean` builds with no `sorry` and standard axioms, and proves the operation a conservative extension of Phase 55's, a column a produced set every row of which answers, `column-incomplete` earned, a column's cells the rows asked alone, *both* two rows or a refusal and never a single binding, and *the one before that* bound from strictly older turns | Lean |
| **D8** | the shape census: no text of an earlier declared corpus that Phase 55's layer took for a follow-up is released, and every earlier text the new phrasings take is one the machine refuses alone (so whole first leaves every answer where it was) | `census_report` |

The measurement is `glm_universal.runtime.discourse_report.discourse_report`.

## 4. What was built

* [`runtime/discourse.py`](../overlay/glm_universal/runtime/discourse.py) —
  `Discourse`, a subclass of Phase 55's `Conversation`: the set a turn
  produced (`COLUMN_KINDS`: an `extremum` tie and a `column` turn), the
  column (`ColumnBinding`, a `column` solution whose cells are the rows'
  answers), the shapes `why`, `prior` and `plural` ahead of the three old
  ones, the refusals `column-incomplete` and `number-mismatch`, a refusal
  recorded as a turn, the `surfaces=True` licence through
  `router.ask_routed`, the rows read from a routed question
  (`ROW_DOMAINS`), and whole first. `carry=False` is the round's switch.
* [`runtime/discourse_report.py`](../overlay/glm_universal/runtime/discourse_report.py)
  — the measurement; `tools discourse-state`;
  `tests/test_discourse_state.py`.
* **Wiring.** `GLM.py --converse TEXT` (repeatable): successive texts are one
  conversation over every surface, a column printed row by row, a refusal
  with its reason. `-q`, `--ask` and `--steps` are unchanged.
* [`RequestProject/GLM/DiscourseState.lean`](../overlay/glm_lean/RequestProject/GLM/DiscourseState.lean)
  — §6.

## 5. Results

Measured by `tools discourse-state` at the close of the round.

**Can it?** Yes: a tie is now carried as a column of the rows' own answers, the fourth shape binds or refuses with a named reason, and a follow-up is licensed by every surface through the router, with every declared case as declared and 0 wrong.

| mark | result | figure |
|---|---|---|
| **D1** | met | 7 of 7 column cases: the fourteen-row tie as a column of 14 descriptions; the two-row tie `carbonate ion, sulfate ion` as a column of molar masses `7501/125` and `48033/500`; the same set carried through a column turn; a set none of whose rows holds an electronegativity walked past to `C`; one row at the end bound as before (`Og`); refused `column-incomplete` (12 of the 14 rows hold no electronegativity) and `ambiguous-antecedent` (a comparison's two rows); 0 wrong |
| **D2** | met | 16 of 16 fourth-shape cases: *the one before that* `C` twice (once walking past `water`, which holds no electronegativity) and once a set; *both of them* the pair of a comparison, its electronegativities `51/20` and `86/25`, and two single-row turns in the order named; *them* the set of a tie; *why?* naming the bound `C`, the refusal `column-incomplete` and a whole query's own derivation; refused `no-antecedent` 3 times, `number-mismatch` twice and `column-incomplete` once; 0 wrong |
| **D3** | met | 6 of 6 surface cases: *is the atomic number of it prime* bound to `Fe` and answered by the stepwise planner; *and oxygen?* after a typed-planner question bound to `oxygen` (`86/25`); *describe both of them* after a comparison the planner answered; a set carried into *what is the molar mass of it*; the ionization energy of `H` fed to a wheel derivation through the pronoun; refused `unlicensed` once; 0 wrong |
| **D4** | met | Phase 55's layer gives 0 of the 20 new-behaviour cases their declared outcome (it agrees on the 3 cases declared unchanged); the first-winner rule answers 10 of 10 column cases with a single row, dropping 22 rows; the recency rule differs on 2 of the 4 *one before that* cases (`prior-licensing`, `prior-set`); the session alone answers 0 of the 5 surface answers; `carry=False` returns 4 of 4 tie cases to `ambiguous-antecedent` |
| **D5** | met | 15 of 15 of Phase 55's follow-ups as declared now; the one that moved is the declared `pronoun-tie-refused` |
| **D6** | met | 32 of 32 column cells and 7 of 7 single answers equal the answer their rewritten text gets asked alone of a fresh asker |
| **D7** | met | §6 |
| **D8** | met | of 3056 earlier declared strings, 0 that Phase 55's layer took for a follow-up are released; 15 (8 distinct, all prose holding *them*) carry a new phrasing, and the machine answers 0 of them alone |

**In all.** 29 of 29 declared follow-ups as declared, with 0 wrong. Every
mark was met on the first full run; no declared case was changed. As in
earlier rounds, the corpus and the module share an author, so this is the
reach of the declared set, not an independent test (§7).

**What the whole machine gained.** Before the round no surface held a
conversation over the whole machine: Phase 55's layer reached the session
alone and was not on any command-line path. `GLM.py --converse` now holds one
over every surface, so a set, a pair, *the one before that* and *why?* are
answered there, each row by the surface that would answer it written out.

## 6. What is proved rather than measured

[`RequestProject/GLM/DiscourseState.lean`](../overlay/glm_lean/RequestProject/GLM/DiscourseState.lean)
states the new operation over the same turns as
[`RequestProject/GLM/Conversation.lean`](../overlay/glm_lean/RequestProject/GLM/Conversation.lean),
with one more bit per turn — whether its answer side is a set the turn
produced — and builds with no `sorry`:

* `resolveD_eq_lift_resolve` — on a conversation in which no turn produced a
  set, the new operation **is** Phase 55's. Nothing moves that the round did
  not declare.
* `resolveD_column_licensed`, `resolveD_column_produced`,
  `resolveD_column_two_le` — a column is a set some turn produced, whole,
  of at least two rows, every one of which answers.
* `resolveD_incomplete_hole` — `column-incomplete` is earned: the set holds a
  row that answers and a row that does not.
* `column_cell_eq_alone` — a column's `i`-th cell is the `i`-th row asked
  alone, one cell per row.
* `resolvePlural_both_two`, `resolvePlural_never_single`,
  `resolvePlural_column_licensed` — *both of them* is two rows or a refusal;
  no plural binds a single row; every row of a plural's column answers.
* `resolvePrior_cons_deciding`, `resolvePrior_stable_under_dead_turn` —
  *the one before that* is decided by the turns older than *that* alone, and
  a newer turn naming nothing usable does not move it.
* `tie_is_a_column`, `comparison_still_ambiguous`,
  `tie_with_a_hole_is_incomplete`, `dead_set_walked_past`,
  `prior_walks_past_unlicensed`, `both_across_turns`, `them_one_row`,
  `both_of_three` — the shipped cases, decided by computation. The first is
  Phase 55's `tie_is_refused` with the turn marked as producing its set.

## 7. Limits, and what the round leaves

* **The declared phrasings are surface patterns.** *the one before that*,
  four plurals and four spellings of *why*; *the first of them*, *the other
  one*, *the second* are not read. Nothing here parses English.
* **A column is all or nothing.** A set with holes is refused, never
  answered over its present rows; *those of them that have one* would be the
  present-rows reading Phase 85 gives folds, and is not declared.
* **The column is not folded.** *The heavier of them* or *the sum of their
  molar masses* would hand the column to the stepwise planner's folds; that is
  the natural next step and it is not taken.
* **Rows read from a routed question are the two register tables' names.**
  A routed turn about a physical concept or a lexicon word names nothing a
  later pronoun can bind, and the lookup is longest phrase first over at most
  three words.
* **The licence is the asker's answer, not its truth.** Whole first and
  licensing both trust the machine's own verdict; a surface that answers
  wrongly would license wrongly. No such answer is known on the declared set.
* **Licensing costs a trial per row** — fourteen for the lexicon tie, and
  through the router each trial may reach the stepwise planner. The plan
  store of Phase 56 is not wired to the new shapes.
* **One author.** The corpus and the module were written together; the
  outside question sets of Phase 89 hold no multi-turn conversations, so no
  outside set measures this layer yet.

## 8. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools discourse-state
PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_discourse_state.py
python3 GLM.py --converse "smallest charge in molecule" \
               --converse "what is the molar mass of it" --converse "why?"
cd .. && lake build RequestProject.GLM.DiscourseState
```
