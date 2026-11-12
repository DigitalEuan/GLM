# Stage 5 — closing the list at the end of the final report

`FINAL_REPORT.md` §8 ended with five things the package could not do. This
stage attacks all five and closes four of them; the fifth (classification of the
Golay code) is advanced but **not** finished, and is labelled as such throughout.
It then adds a capstone that joins the two ends of the chain — data at one end,
English sentences at the other — so that no law in the pipeline is written by
hand any more.

Everything below is the statement of a Lean theorem that compiles in this
repository. The build has **no `sorry`** and adds **no axioms**;
`RequestProject/Package.lean` re-prints the axioms of 179 headline results,
including all of stage 5. As in earlier stages, many of the finite counts are
discharged by `native_decide`, so those additionally trust Lean's compiler
(`Lean.ofReduceBool`, `Lean.trustCompiler`) rather than the kernel alone. The
axiom audit makes that boundary visible result by result.

| §8 item | file | status |
|---|---|---|
| 1. learning | `Learning.lean` | closed |
| 2. a real scaling theorem | `Scaling.lean` | closed for the counts and for contingency; the finite checks stay finite |
| 3. continuous quantities | `Continuous.lean` | closed |
| 4. classification of the Golay code | `GolayEnumerator.lean` | **not closed**; the weight enumerator is proved, uniqueness is not |
| 5. a grammar | `Relative.lean` | closed for relative clauses |
| — | `Capstone.lean` | new: learn → utter → check, end to end |

---

## 1. Learning (`Learning.lean`)

The law table is no longer an assumption. The learner is version-space
elimination over the 2256 ordered pairs of distinct contingent literals, with no
scoring, no threshold and no randomness: a hypothesis dies the first time a world
refutes it.

*Proved for every corpus, with no finite check:*

* `learn_holds_on_corpus` — what is learned fits the data it came from.
* `laws_are_never_missed` — **recall is 1 at every corpus size**. A genuine
  entailment is learned from *any* corpus at all, so the learner's error is
  one-sided: it over-generates, it never misses.
* `learn_antitone` — more data is never worse.

*Measured inside Lean:*

* `learn_all_worlds` — from the complete corpus the learner returns **exactly**
  `CubeThought.lawPairs`: the same 78 pairs, as a list, that the package used to
  write down by hand.
* `learning_curve` — `2256` hypotheses before any data, then
  `1680, 1545, 1394, 1227, 1099, 904, 762, 521, 365, 177, 84, 78` after
  `1, 2, 4, 8, 16, 32, 64, 128, 256, 384, 480, 481` worlds. Precision climbs
  from `78/2256 ≈ 3%` to 1.
* `prefix_corpus_needs_481` — read in their natural order, **481 of the 512**
  worlds are needed; at 480 six false laws are still standing.
* `generalisation_error_at_256` — trained on the first half, the learner keeps
  365 laws and the held-out half refutes **287** of them: a 78.6% test error.
  Half the data is not nearly the answer.
* `learned_law_is_false_witness` — a named casualty: after sixteen worlds the
  learner still believes that whatever is *not hotter than the lamp* is *not
  boiling*.

*Which data, not how much:*

* `teaching_set_learns_the_table` — **twelve** worlds, chosen by greedy
  elimination and verified here, learn exactly the table: forty times less data
  than the natural order needs.
* `teaching_set_irredundant` — and no one of the twelve can be dropped.
* `teaching_lower_bound` — **no corpus of three worlds or fewer can ever do it**,
  for any choice of worlds. This is proved, not searched: 2178 hypotheses must
  die and one world kills at most 576 (`one_world_kills_at_most_576`).

  **The gap is honest and unclosed**: the smallest teaching set has size
  somewhere in `[4, 12]`, and this stage does not say where.
* `learned_table_on_the_surface` — the learned pairs, translated by
  `CubeThought.lawWord`, are the same 27 distinct cube words the hand-written
  table used, and each still acts as `dxor`-addition on the surface. The
  learner reconstructs the cube's law table, not merely a list.
* `law_word_curve` — how the surface sees the learning: `172, 155, 93, 27`
  distinct translations at 16, 64, 256, 481 worlds.

**The honest limit.** This is induction over a *fixed, finite, correctly
labelled* hypothesis space. The learner is told which literals exist and sees
perfect data; it invents no atoms and tolerates no mislabelled world, and its
bias — "a law is a material implication between two literals" — is written by
hand. What it does show is that the table is recoverable from twelve
observations.

## 2. A real scaling theorem (`Scaling.lean`)

Stage 4 widened the world from 3 things to 24 and re-measured. Stage 5 proves
the same statements for **every** `n` at once, with no enumeration.

* `wcontingent_iff_not_reflexive` — a literal says something exactly when its
  atom is not one of the reflexive comparisons (*hotter than itself*, *heavier
  than itself*, *same temperature as itself*). Both directions are proved by
  exhibiting worlds (`atom_takes_both`, `refl_atom_constant`), for all `n`.
* `contentful_atom_count` — `3n + 3n²` contentful atoms.
* `usefulLits_length_formula` — `6n + 6n²` contingent literals. At `n = 24`
  this is the 3600 that stage 4 counted.
* `describe_length_formula` — **every one of the `18ⁿ` worlds is described by
  exactly `3n + 3n²` facts**: the length of a description is a property of the
  lexicon, not of the world. At `n = 24` it is the 1800 of stage 4, now proved
  for all worlds at once rather than for one.
* `describeQ_length_formula` — 12 quantified sentences, whatever the world.
* `describeR_length_formula` — 144 sentences with a relative clause, whatever
  the world.

What is *not* scaled: the finite checks stay finite. Anything proved by
`native_decide` at `n = 3` or `n = 24` — the 512-world tables, the demonstration
counts — remains a statement about that size.

## 3. Continuous quantities (`Continuous.lean`)

Temperatures were four bands and masses two. Here a world is `Fin n → ℤ × ℤ`:
degrees Celsius and kilograms, unbounded.

* `thresholds_depend_only_on_band` — the four old words see only which band a
  reading is in, and `twenty_and_twentyone_agree` is the concrete casualty:
  20 °C and 21 °C satisfy exactly the same words of the old lexicon.
* The repair is **graded comparatives**: *hotter by at least k*. Then
  `graded_separates` (any two distinct differences are told apart),
  `strongest_grade_is_exact` (the strongest true grade *is* the difference) and
  `strongest_grade_determines_difference` (the hearer recovers the number).
* `claws_sound` and `graded_laws` — the law schemas survive the continuum, now
  proved by arithmetic (`omega`) rather than by enumerating states.
* **The substrate still has a window, and it is sharp.** One MOG column holds a
  difference exactly iff it lies in `[−8, 7]` (`difference_roundtrip_iff_window`),
  and it fails silently: `twenty_reads_as_four`. Two faces widen the window to
  `[−128, 127]` and no further (`difference_roundtrip2_iff_window`,
  `window_is_sharp`).
* The discipline that follows: `sayGrade` states a difference only when the
  substrate can hold it. `sayGrade_sound` — whatever it says is exact and
  survives the cube; `sayGrade_none_iff` — when it says nothing, the gap is
  outside the window. In `demoC_facts` a furnace at 500 °C and a room at 21 °C
  are 479 degrees apart, and the system **declines to say so** rather than
  storing a number that would read back wrong.
* The dimensional layer now does work rather than standing ready:
  `difference_is_well_typed` and `continuous_comparisons_are_free` (a difference
  of temperatures is a temperature, so the cube accepts it for nothing), against
  `grading_across_dimensions_is_rejected` (grading a temperature against a mass
  is the category error the cube refuses).

## 4. Classification — advanced, not closed (`GolayEnumerator.lean`)

`IsGolay` is the four standard defining properties: dimension 12,
self-orthogonal, doubly even, minimum weight 8. §6 of the final report flagged
that identifying such a code with *the* extended Golay code is a classification
theorem the package quotes rather than proves.

This file proves, for **every** code satisfying the definition and with no
enumeration:

* `octad_count` — there are exactly **759** octads, by double counting the
  5-subsets against the Steiner property (`C(24,5) = 42504 = 56 · 759`).
* `card_wt_eq_eight`, `card_wt_eq_sixteen` — 759 words of weight 8 and 759 of
  weight 16 (the complements), `card_wt_eq_zero`, `card_wt_eq_twentyfour` — one
  each of weight 0 and 24.
* `golay_weight_enumerator` — the weight enumerator is `1, 759, 2576, 759, 1`.

**What is still missing.** The weight enumerator is a consequence of the
definition; *uniqueness up to permutation equivalence* is not proved here. So
the negative rows of §6 remain statements about **every** code with the four
properties, which is the stronger reading anyway, and the identification with
"the" Golay code remains quoted. This item is **not** closed.

## 5. A grammar (`Relative.lean`)

Clauses were joined, not nested. This file adds recursive conditions
(`lit`, `and`, `or`, `not`) and restricted quantification — *every/some thing
that is A is B* — over worlds of any size.

* `evalR_flip` — duality: the denial of *every A is B* is *some A is not B*.
* `restricted_is_conservative` and `ex_conservative` — **conservativity**, the
  defining property of natural-language determiners: *every A is B* and *every A
  is A-and-B* say the same thing. Proved for every world and every size, not
  assumed.
* Monotonicity profiles: `univ_downward_in_restrictor`, `univ_upward_in_scope`,
  `ex_upward_in_both`.
* `vacuous_universal` / `existential_import_fails` — with a witness: nothing
  boils in a cold world, so *every boiling thing is heavy* is true there and has
  no instance. Recorded as the behaviour it is, not patched away.
* `valid_iff_local` — the reduction that replaces enumeration: a restricted
  universal holds in **every world of every size** iff it holds at each of the
  18 local states.
* `law_schemas_count` / `law_schemas` / `law_schemas_sound` — of the 144
  literal-restricted universals exactly **12** are laws, they are exactly the
  temperature ladder, the mass ladder and *every boiling thing is hot*, and each
  is proved to hold in every world of every size. `lawSentences_pinned` prints
  them in English.
* `describeR_sound`, `describeR_complete`, `describeR_decides` — no gaps and no
  contradictions: of each sentence and its denial, exactly one is uttered.
* `demoR_counts` — in the 24-thing demonstration world, of the 288 sentences
  144 are true (exactly half, as duality forces): 28 universal, 116 existential.
* `relative_clause_is_new` — **nesting is new expressive power.** Two worlds
  `wA`, `wB` agree on every one of the 24 unrestricted quantified sentences —
  same temperatures, same masses, differently paired — and disagree on *every
  hot thing is heavy*. So no Boolean combination of unrestricted sentences has
  the truth value of a relative clause.
* `accidental_generalisations` — **the trap, measured.** Of the 28 true
  universals in the demonstration world, 24 hold in every world and **4 do
  not**: *every boiling thing is heavy* is true where it was read and false one
  world along (`boiling_heavy_is_an_accident`). A system that generalises from
  one world is wrong 4 times in 28 here, and the package says which 4.
* `compound_relative_clause` — the recursion is real: *every thing that is hot
  and not heavy is warm*.

## 6. The capstone (`Capstone.lean`)

The two ends are joined, with no hand-written law anywhere in the chain:

```
12 observed worlds ──learn──▶ 78 pairs ──render──▶ 78 English conditionals
```

* `learned_sentences_count` — 78 sentences, all distinct;
  `learned_sentences_sample` pins the first five, e.g. *if the water is frozen
  then the water is not warm*.
* `learned_sentences_are_assertible` — every uttered sentence passes the
  system's **own** test for a law (`evalS` of a `law` is `lawOK`): the antecedent
  entails the consequent in all 512 worlds, both halves are contingent, and they
  are distinct. Nothing uttered is a coincidence of the observed data, a
  tautology, or vacuous.
* `learned_sentences_are_complete` — and the converse: every law of the world
  that the lexicon can state is one of the 78. Nothing true is left unsaid.
* `why_answer_is_a_learned_law` — the explanations are licensed by the
  learning. Whenever the system answers *why …?* with a reason, the implication
  it leaned on is a pair the learner recovers, from any corpus whatever.
  `why_answer_witness` shows the case occurs: *the water is not warm because the
  water is frozen*, backed by the learned sentence *if the water is frozen then
  the water is not warm*.
* `premature_sentence_is_false` and `premature_sentence_count` — the failure in
  the same terms. After sixteen worlds the system would utter *if the water is
  not hotter than the lamp then the water is not boiling*, which is false; at
  that point 1099 sentences stand, of which **1021** are false. The twelve-world
  teaching corpus produces none of them.

## 7. What is still open after stage 5

1. **Golay uniqueness.** The weight enumerator is proved; classification up to
   equivalence is not. Everything about the code is therefore stated for every
   code with the four defining properties.
2. **The teaching-set gap `[4, 12]`.** The lower bound is a union bound and the
   upper bound is a greedy witness; neither is known to be tight.
3. **The mod-2 ceiling.** Unchanged from stage 1: XOR on 24 cells cannot carry
   dimension exponents outside a window, and the fix in every stage has been to
   widen the record, not to remove the ceiling. `Continuous.lean` re-proves the
   window is sharp at one and two faces.
4. **No new atoms.** The learner fits laws over a lexicon it is given. Nothing
   in the package invents a predicate, and `Abstract.lean` shows that some
   vocabulary (kinship) provably cannot be defined from the measurements at all.
5. **Noise.** Every corpus in `Learning.lean` is perfectly labelled. One
   mislabelled world deletes a true law and, because recall-1 is proved only for
   correct data, the guarantee goes with it.
6. **The finite checks stay finite.** `Scaling.lean` lifts the counting and the
   contingency argument to all `n`; the demonstration tables and the 512-world
   enumerations are still statements about one size, checked by `native_decide`.

## 8. Reproducing stage 5

```bash
lake build                             # whole development, ~8070 jobs, no sorry
lake build RequestProject.Package      # + the axiom audit of 179 headline results
lake build RequestProject.Learning     # the learner and the learning curve
lake build RequestProject.Relative     # relative clauses and the 12 law schemas
lake build RequestProject.Scaling      # the counts as polynomials in n
lake build RequestProject.Continuous   # integer temperatures, graded comparatives
lake build RequestProject.GolayEnumerator  # 759 octads, weight enumerator
lake build RequestProject.Capstone     # learn → utter → check
python3 make_theorem_index.py          # regenerate THEOREM_INDEX.md
```
