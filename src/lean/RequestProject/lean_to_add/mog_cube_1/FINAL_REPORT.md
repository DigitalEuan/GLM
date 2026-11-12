# Final report — a GLM that means what it says

This closes the package. Reports 1–3 (`CUBE_MOG_REPORT.md`,
`CUBE_MOG_REPORT_2.md`, `CUBE_MOG_REPORT_3.md`) are the working notes of the
three stages, written as each stage happened and left unedited. This document
is the summary you can read on its own: what the question was, what the system
now does, what is machine-checked, what failed, and what is left.

Nothing here is asserted from a script run. Every number in the tables below is
the statement of a Lean theorem that compiles in this repository with no
`sorry` and no added axioms; `RequestProject/Package.lean` re-checks the
axioms behind every headline result in one place. Where a claim is *not*
machine-checked it says so, in bold, in §6.

---

## 1. The question

*Can the MOG/Golay data object carry real meaning — enough for a machine to
build sentences that make sense — using words whose content is deterministic
and measurable?*

The working rules were yours: physics-style words first, because their meaning
is measurable; no XOR-as-a-hash, no SHA, no randomness; and no cherry-picking —
a failure is a result and gets written down as one.

## 2. What the system does now

Given a micro-world of three things (water, stone, lamp) with a temperature and
a mass each — 512 possible worlds — the system:

* **holds measurable content on the cube.** A word's physical dimension (the
  exponents of L, M, T, I, Θ, N) is carried on the 24 cells of a cube surface,
  one dimension per face.
* **composes by arithmetic, not by hashing.** Multiplying two quantities is
  adding their cubes, cell by cell, through a ripple-carry adder wired across
  each face (`IntegerCube.addG`). Dividing is subtracting it back out.
* **judges equations exactly.** Over 156 phrases and every ordered pair of
  differently-named ones, it accepts exactly the 356 that are dimensionally
  true, and no others.
* **says true things about a world**, answers questions about it — *is it…?
  why…? which is hotter…? what if we heat it?* — and refuses false premises
  instead of going along with them.
* **joins clauses with `and`, `but`, `so`**, where the choice of word is a
  measured property of the remaining possible worlds, not a decoration.
* **holds a conversation** that remembers its topic and its commitments, and
  can never contradict something it has already said.
* **says what to do**: given a goal it returns a shortest action sequence
  within its horizon, and narrates what changed at each step.

A ten-turn transcript, produced by the Lean definitions themselves:

```
> tell me about the water       the water is frozen
> tell me more                  and it is not heavy
> tell me more                  and it is not hotter than the stone
> is it warm?                   the water is not warm
> why is it warm?               as I said, the water is not warm because the water is frozen
> tell me about the stone       the stone is not frozen
> tell me more                  but it is not hotter than the lamp
> tell me more                  but it is heavier than the lamp
> is it hotter than the water?  the stone is hotter than the water
> tell me more                  and it is not boiling
```

Stage 4 then widened all of this: 24 things instead of three, an abstract
kinship vocabulary on top of the measured one, `because` with a direction of
time, inference carried out *on* the cube surface rather than merely stored
there, paragraphs that stop when they run out of facts, and plans that are
priced and provably cheapest with no horizon at all. §3.5 is the record.

## 3. The headline results

### 3.1 The substrate — the cube surface *is* the MOG

| claim | value | theorem |
|---|---|---|
| 24 surface cells = 6 faces × 4 quadrants = the MOG grid | — | `CubeMOG.IsMog` |
| three-layer factorisation | `2^24 → 2^18 → 2^12` | `fibre_card`, `hexpass_card`, `mog_card`, `parity_layer_factor` |
| weight distribution | `1, 759, 2576, 759, 1` | `CubeMOG.mog_weight_enumerator` |
| minimum distance | `8` | `CubeMOG.mog_min_weight` |
| one erased face | always repaired | `CubeMOG.face_erasure_correctable` |
| any two erased faces | always ambiguous | `CubeMOG.two_face_ambiguous` |
| free cube symmetries (canonical placement) | `12` of 48 — the tetrahedral group | `CubeStab.stabiliser_card`, `preserves_iff_tetrahedral` |
| free cube symmetries (a better placement) | all `24` rotations, no reflection | `CubeStab.oCode_rotations_free`, `oCode_improper_priced` |
| repair of arbitrary damage | `≤ 4·Q`, and `4·Q` is attained | `CubeTax.tax_le_four_Q`, `covering_radius_le_four`, `covering_radius_ge_four` |
| repair below the boundary | unique at `≤ 3` cells, ambiguous at `4` | `repair_unique_of_le_three`, `repair_ambiguous_at_four` |

### 3.2 Meaning on the substrate — the precision wall, and past it

| | true sentences | accepted | false positives | precision |
|---|---|---|---|---|
| parity (XOR) cube — stage 1 | 356 | 1758 | 1402 | **0.20** |
| integer cube — stage 2 | 356 | 356 | **0** | **1.00** |

* `MeasuredSentences.equations_count`, `substrate_count`,
  `substrate_false_positive_count` — the parity cube's 20% precision, counted
  inside Lean rather than sampled.
* `MeasuredWords.xor_encoding_is_mod_two` — the reason, proved in general:
  **any** encoding whose composition is XOR sees exponents only mod 2, so no
  rearrangement of the code fixes it. `mod_two_blindness_witness` is the
  concrete casualty: the parity cube accepts `E = mc⁴`.
* `IntegerCube.integer_accepts_eq_equations` — the integer cube's accepted set
  is *the same list* as the true set, not merely the same length.
* `IntegerCube.xor_is_add_without_carry` — XOR is this adder with the carry
  wire cut; the carry is exactly the information XOR was throwing away.

### 3.3 Language

| claim | value | theorem |
|---|---|---|
| every generated sentence is true in its world | — | `Semantics.speak_sound`, `Discourse.para_sound` |
| `so` is a deduction; `but` is a real reversal of expectation; `and` is news | — | `so_is_a_deduction`, `but_is_contrastive`, `and_is_informative` |
| generated corpus, all 512 worlds × 3 topics | 1536 paragraphs, 9216 clauses (4824 `and`, 1512 `but`, 2880 `so`), every one valid | `Discourse.corpus_facts` |
| paragraphs that change subject | 512 paragraphs, 3072 clauses, 2524 subject changes, 330 cross-subject deductions | `WideDiscourse.wcorpus_facts` |
| every reply true, in every state, utterance and world | — | `Dialogue.reply_true` |
| a conversation never contradicts itself | — | `Dialogue.run_no_contradiction` |
| the ten-turn script above, run in all 512 worlds | all replies true, ≥ 8 distinct commitments | `Dialogue.script_facts` |
| plans are correct and shortest within the horizon | 22080 of 24576 goal/world pairs solved; 2496 reported unreachable | `Narrative.plan_correct`, `plan_facts` |
| narration reports only real changes | — | `Narrative.story_reports_real_changes` |
| clause storage on three cubes | 60 distinct records, pairwise distance ≥ 8, any 3 damaged cells repaired | `SentenceCode.clause_min_distance`, `clause_repair_bound` |

### 3.4 Zipf and least effort

The corpus is 66288 tokens over 17 types. Every rank sits *above* the Zipf
prediction, and ranks 4–12 sit at more than twice it
(`Zipf.corpus_is_flatter_than_zipf`, `zipf_worst_case`): **the language is far
flatter than English, and the diagnosis is that it has no tail** — 17 words and
a rule that every clause must be news.

The frequencies still buy something. A Huffman code built inside Lean from the
measured counts is prefix-free, exactly invertible on all 1536 paragraphs, and
costs 249528 bits against 331440 — 10397 cubes instead of 13810
(`Zipf.huffman_facts`, `least_effort_is_cheaper`).


### 3.5 Stage 4 — widening the world, and making the cube think

Stage 4 answers, one by one, the five "where to go next" items of §8, and its
files are audited in `Package.lean` alongside the rest.

*The world, widened* (`WideWorld.lean`, `WideInteger.lean`, `Abstract.lean`,
`WideChat.lean`, `WideZipf.lean`)

| claim | value | theorem |
|---|---|---|
| 24 things, six properties, three comparisons | 1872 words, 3744 literals, 3600 contingent | `WideWorld.wide_vocab_counts` |
| the 144 non-contingent literals are exactly the reflexive comparisons | — | `WideWorld.noncontingent_are_reflexive` |
| the laws hold in every world of every size | — | `WideWorld.schemas_sound` |
| everything said about a wide world is true, and never self-contradictory | 1800 facts in the demonstration world | `describe_sound`, `describe_consistent`, `demoWide_count` |
| integers on a *pair* of records: the window widens `16 → 256` | exact round trip, addition still addition | `WideInteger.decP_encP`, `encP_add`, `sixteen_no_longer_collides`, `pair_window_is_256` |
| but no encoding into any number of records is faithful | — | `WideInteger.no_faithful_pair` |
| an abstract vocabulary the measurements cannot define: kinship | 2328 kin words, 4200 in all, 8400 literals | `Abstract.kin_vocab_counts` |
| ancestry is a strict order; orphans have no ancestors | — | `ancestor_trans`, `ancestor_irrefl`, `ancestor_asymm` |
| "mother" is not any function of the readings, and the readings are not any function of the kinship | — | `mother_not_definable_by_readings`, `readings_not_definable_by_kin` |
| chat over the wide world: every answer true, every reason a ground, no repetition | six-turn transcript pinned | `WideChat.answer_is_true`, `reason_is_a_ground`, `reply_no_repetition`, `demo_transcript` |
| **Zipf, re-measured after widening** | fit moves from **8 of 17** ranks to **37 of 39** (news corpus 35 of 38) | `WideZipf.narrow_band_count`, `zipf_band_counts` |
| …but the head still crosses the law rather than following it | ranks 2–3 above, 4–8 below | `WideZipf.wide_head_crosses_zipf` |

*Causation* (`Causation.lean`)

| claim | value | theorem |
|---|---|---|
| `because` with a direction of time: the reason is never younger than the fact | — | `causalBecause_sound`, `since_le_of_entails` |
| the cycle of report 2 is broken — a fact and its reason cannot swap places | — | `causalBecause_asymm` |
| reasons chain, which is what licenses "…, and that is why …" | — | `causalBecause_trans` |
| a named action cause is a real one; a fact that always held gets none | — | `actionCause_sound`, `static_facts_have_no_action_cause` |
| the entailment `because` really is cyclic — the complaint was justified | — | `grounding_is_cyclic` |
| what the filter costs, over all 4608 histories | 1180416 accepted → 1051584; the strictly-older filter accepts **0** | `causal_filter_counts` |

*Thought on the cube* (`ClauseStore.lean`, `CubeThought.lean`)

| claim | value | theorem |
|---|---|---|
| clauses, links and dimensions stored as records on one surface | 4096 records, 1024 per role | `ClauseStore.role_capacity` |
| any two records differ in at least 8 cells; roles never confuse | — | `rec_min_distance`, `roles_are_separated` |
| three damaged cells read back exactly, and a repaired store is still sound | — | `decodeRec_correct`, `repaired_store_is_still_sound` |
| **inference is addition on the surface**: the conclusion record is the premise record plus a fixed law word | — | `CubeThought.apply_law` |
| denial is one universal translation, the same word for all 48 literals | — | `negation_is_a_translation`, `negWord_is_universal` |
| an inference survives three damaged cells | — | `inference_survives_damage` |
| every law word on the table is a genuine entailment | 78 entailing pairs, 27 distinct law words | `laws_are_sound_on_the_surface`, `law_words_counted` |

*Conversation, paragraphs, priced plans* (`Conversation.lean`, `Paragraph.lean`,
`PlanCost.lean`, `ReachPlan.lean`)

| claim | value | theorem |
|---|---|---|
| pronouns resolve: what the speaker means is what the hearer reads | — | `Conversation.refOf_resolve`, `clause_roundtrip` |
| a repeated question escalates — reason, then priced plan, then an admission | five-line transcript pinned | `repeat_says_something_new`, `demo_escalates` |
| **paragraph length is content, not fuel**: the generator stops when the stock is exhausted | 512 paragraphs, 11776 clauses; length = the number of facts the world affords | `Paragraph.cgrow_ends_only_when_nothing_is_licensed`, `ccorpus_facts`, `ccorpus_exhausts_the_stock` |
| asserting only positives makes length vary with the world | 3 to 10 clauses, seven distinct lengths | `assertion_lengths_vary`, `assertion_length_is_the_fact_count` |
| plans are priced, and the cheapest is proved cheapest by induction — no finite check | in 2880 of 22080 pairs the cheapest plan beats the shortest, saving 4224 units | `PlanCost.pickMin_le`, `bestPlan_optimal`, `plan_cost_facts` |
| the argument offered for a plan is sound | — | `PlanCost.argument_is_sound` |
| **planning without a horizon**: a reachability table over all 512 worlds | every world reached, max cost 30, max plan 12 actions | `ReachPlan.all_worlds_reached`, `unbounded_optimality`, `bestGoalPlan_correct` |
| what the horizon actually cost | on single-literal goals: nothing — both planners solve the same **54** of 60 at the same price, and the other 6 hold in no world. On *world* goals: three actions reach **63** of 512, the table reaches **512** | `ReachPlan.horizon_gain` |

## 4. What this says about the original idea

The Golay/MOG layer earned a precise verdict rather than a verdict by analogy.

* As a **carrier** it is excellent: composition is free, storage is free,
  a whole lost face is repaired, and the worst-case repair price is exactly
  `4·Q` — a sharp number, not an estimate.
* As a **semantic decision procedure** it fails, and the failure is measurable:
  used alone as an acceptance test it admits four false sentences for every
  true one. That 20% precision *is* the price of characteristic 2.
* The fix is not a better code, it is **keeping the integer content** — and the
  integers fit inside the same 24 cells, four per face. That buys precision
  1.00 and costs the "free to hold" property: an integer record is essentially
  never a codeword (`IntegerCube.phrase_codeword_count = 0`), though it is
  still at most `4·Q` from one.

So the honest architecture that came out of this is two-layer: **integers for
meaning, the code for protection and transport**, with a proved exchange rate
between them.

## 5. What failed — and which of those failures stage 4 closed

*Still standing*

1. **The mod-2 ceiling was not beaten by any linear code** — proved impossible
   (`xor_encoding_is_mod_two`), and worked around rather than solved.
2. **No encoding into 24 cells is faithful on all of ℤ⁶**
   (`IntegerCube.no_faithful_encoding`), and a second record does not help
   (`WideInteger.no_faithful_pair`). Stage 4 moved the window from 16 to 256
   (`pair_window_is_256`); the blind spot moved, it did not disappear.
3. **Two erased faces are always ambiguous**, for every pair — worse than the
   "at the decoding boundary" the brief predicted (`two_face_ambiguous`).
4. **The head of the frequency curve is not Zipfian.** Widening the world fixed
   the body of the distribution — the fit went from 8 of 17 ranks to 37 of 39
   (`WideZipf.zipf_band_counts`) — but ranks 2–3 still sit above the law and
   ranks 4–8 below it (`wide_head_crosses_zipf`). A generated language has no
   accidental head.
5. **Nothing here is learned.** Every definition is written by hand; the system
   measures and derives, it does not induce. That is a property of the design,
   not a bug, but it is the honest limit on the word "language model".
6. **Scaling is demonstrated, not proved.** Stage 4 multiplied the world by
   eight (3 things → 24, 48 contingent literals → 3600, plus 8400 kinship
   literals) and everything survived, which is evidence, not a scaling theorem.

*Closed by stage 4*

| the old failure | what closed it |
|---|---|
| paragraph length is fuel, not content | `Paragraph.cgrow` stops when the stock is exhausted; length is now the fact count (`ccorpus_exhausts_the_stock`, `assertion_length_is_the_fact_count`) |
| `because` is entailment, not causation | `Causation.causalBecause` adds a direction of time; the old connective is proved cyclic (`grounding_is_cyclic`), the new one asymmetric and transitive |
| questions can make the system repeat itself | `Conversation` escalates: reason, then a priced plan, then an admission (`repeat_says_something_new`, `demo_escalates`) |
| the cube is storage, not thought | inference is now addition on the surface, and survives damage (`CubeThought.apply_law`, `inference_survives_damage`) |
| anaphora stops at the subject | clause-level reference with "the former"/"the latter", proved unambiguous (`Conversation.clause_roundtrip`, `former_latter_demo`) |
| plans are exhibited, not argued for | plans are priced, provably cheapest, and horizon-free (`PlanCost.bestPlan_optimal`, `ReachPlan.unbounded_optimality`) |
| vocabulary is tiny — three things, six properties | 24 things, 3600 contingent literals, plus an abstract kinship vocabulary the measurements cannot define (`WideWorld.wide_vocab_counts`, `Abstract.mother_not_definable_by_readings`) |

## 6. What is *not* machine-checked

* The invariance table below is now **proved**, not searched. `GolayCode.lean`,
  `GolaySteiner.lean` and `GolayInvolution.lean` show in Lean that the octads of
  any Golay code form a Steiner system `S(5,8,24)` (`unique_octad`, by moment
  counting — no weight enumerator, no uniqueness theorem), and then that a
  single diagonal mirror of the cube destroys invariance: it fixes exactly four
  of the 24 cells, there are 220 mirror-invariant 5-sets, every invariant 8-set
  contains a multiple of six of them, and `6 ∤ 220`
  (`no_diagonal_mirror_invariant_golay`). Since that mirror lies in `T_d ⊆ O_h`,
  both negative rows follow for **every** placement of **every** Golay code, not
  merely the ones a search reached (`no_Td_invariant_golay`,
  `no_Oh_invariant_golay`).

  | group | order | verdict | where |
  |---|---|---|---|
  | `O_h` | 48 | no invariant Golay code | `GolayInv.no_Oh_invariant_golay` (proved) |
  | `T_d` | 24 | no invariant Golay code | `GolayInv.no_Td_invariant_golay` (proved) |
  | `O` | 24 | an invariant Golay code exists | `GolayInv.exists_O_invariant_golay` (proved) |
  | `T_h` | 24 | invariant Golay codes exist | `GolayInv.exists_Th_invariant_golay` (proved) |

  The `T_h` row was the final search-only claim in the package, and
  `GolayTh.lean` now closes it — and restates the `O` row in the same abstract
  language — by exhibiting the witnesses: twelve explicit generators whose span
  has dimension 12, is self-orthogonal, and carries only the weights
  `0, 8, 12, 16, 24`, each of the 24 group elements carrying each generator back
  into the code. `o_stabiliser_exact` and `th_stabiliser_exact` add that each
  group is the *whole* stabiliser of its code among the 48 cube symmetries — as
  each has to be, since anything larger would contain a diagonal mirror.

  **The one caveat.** `IsGolay` asks for the four standard defining properties
  of the extended Golay code — dimension 12, self-orthogonal, doubly even,
  minimum weight 8. The Python search asked only for dimension 12 and minimum
  weight 8 and appealed to uniqueness for the rest. The two agree on every code
  either could mean, but that identification is a classification theorem which
  is *not* proved here. (It cuts the right way for the positive rows: the
  exhibited codes are checked to have all four properties.)

  The search remains re-runnable for comparison:
  `python3 glm_clean/exp7_invariance_check.py` writes
  `glm_clean/results/exp7_invariance.json` (`O_h` exhaustive in 29 s, `T_d` in
  93 s), and it agrees with the theorems.
* 103 of the finite searches in the development are discharged by
  `native_decide`, so those results additionally trust Lean's compiler
  (`Lean.ofReduceBool`, `Lean.trustCompiler`) rather than the kernel alone.
  `RequestProject/Package.lean` prints the axiom list of every headline result
  so the boundary is visible; no result depends on `sorryAx`.
* The Python mirrors (`glm_chat2.py`, `glm_discourse.py`) are convenience
  reimplementations. They agree with every Lean number, but the Lean side is
  the authority.

## 7. Reproducing it

```bash
lake build                       # whole development, ~8000 jobs, no sorry
lake build RequestProject.Package  # + the axiom audit of every headline result
python3 glm_chat2.py             # stage 1–2 mirror: prints its number and Lean's
python3 glm_discourse.py         # stage 3 mirror: connectives, dialogue, Zipf, plans
python3 make_theorem_index.py    # regenerate THEOREM_INDEX.md
python3 glm_clean/exp7_invariance_check.py   # the old search, now superseded by proof (§6)
```

`THEOREM_INDEX.md` lists all 1122 top-level declarations (513 definitions,
609 theorems) with a one-line summary each.

## 8. Where to go next, in order of expected value

The five items listed here at the end of stage 3 were all carried out in stage
4; §3.5 records what each of them bought, and §5 records what each of them did
not fix. What is left is of a different kind:

1. **Learning.** Nothing in the package is induced from data. The smallest
   honest step would be fitting the law table of `CubeThought` from a corpus of
   worlds rather than writing it, and measuring how many of the 78 entailing
   pairs are recovered.
2. **A real scaling theorem.** Stage 4 is evidence that the constructions
   survive an eight-fold widening. A statement that soundness holds for every
   `n`, with the counts as functions of `n`, is within reach for the parts that
   are already schematic (`WideWorld.schemas_sound`, `allLits_length`,
   `kinAtoms_length`) and out of reach for the parts that are finite checks.
3. **Continuous quantities.** Temperatures are four steps and masses two. Real
   ranges would change the Zipf head, and would make the dimensional layer do
   work it currently only stands ready to do.
4. **Classification.** `IsGolay` is the four defining properties; that they
   pin the extended Golay code up to equivalence is the one standard fact the
   package quotes rather than proves, and it is what would let the negative
   rows of §6 be stated for "the" Golay code rather than for every code with
   those properties.
5. **A grammar.** Clauses are joined, not nested. Relative clauses and
   quantifiers are the next structural step, and neither is a decoding problem.

## 9. Stage 5 — the five items above, taken up

The five items of §8 were attacked in a fifth stage; `STAGE5_REPORT.md` is its
write-up and the authority on the numbers. In brief:

| §8 item | file | outcome |
|---|---|---|
| 1. learning | `Learning.lean` | closed. The 78-entry law table is *fitted*, not written: recall is 1 at every corpus size, complete data returns exactly `CubeThought.lawPairs`, twelve chosen worlds suffice, and no corpus of three or fewer can ever do it. |
| 2. scaling | `Scaling.lean` | closed for the counts: `3n + 3n²` contentful atoms, `6n + 6n²` contingent literals, and every one of the `18ⁿ` worlds described by exactly `3n + 3n²` facts, for all `n`. |
| 3. continuous quantities | `Continuous.lean` | closed. Integer degrees and kilograms, graded comparatives that recover the exact difference, and the substrate window proved sharp at `[−8, 7]` on one face and `[−128, 127]` on two. |
| 4. classification | `GolayEnumerator.lean` | **not closed.** 759 octads and the weight enumerator `1, 759, 2576, 759, 1` are now proved for every code with the four defining properties; uniqueness up to equivalence is still quoted, not proved. |
| 5. a grammar | `Relative.lean` | closed for relative clauses: conservativity, monotonicity, duality, exactly 12 law schemas valid at every world size, and a proof that nesting says what no unrestricted sentence can. |

`Capstone.lean` joins the ends: 78 English conditionals learned from twelve
observed worlds, each passing the system's own test for a law, no law of the
lexicon left unsaid, and the *why*-answers licensed by the same learning. The
half-trained failure is recorded beside it — after sixteen worlds 1099 sentences
stand, of which 1021 are false.

What remains open after stage 5 is listed in `STAGE5_REPORT.md` §7: Golay
uniqueness, the teaching-set gap `[4, 12]`, the mod-2 ceiling, no invention of
new atoms, no tolerance of noise, and the finite checks that stay finite.
