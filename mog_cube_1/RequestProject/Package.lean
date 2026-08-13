/-
# Package root and audit file

This module imports every file of the development and re-checks, in one place,
the axioms behind the headline results of the reports
(`CUBE_MOG_REPORT.md`, `CUBE_MOG_REPORT_2.md`, `CUBE_MOG_REPORT_3.md`,
`FINAL_REPORT.md`).

Building this file therefore builds the whole package.  Each `#print axioms`
below must report only `propext`, `Classical.choice`, `Quot.sound` and — for
the results whose finite searches are discharged by `native_decide` —
`Lean.ofReduceBool` and `Lean.trustCompiler`.  Any `sorryAx` in the list would
mean an unproved claim had slipped into a report; there are none.

The audit is grouped exactly as the reports are.
-/

import Mathlib
import RequestProject.GolaySemantics
import RequestProject.GolayHexTiles
import RequestProject.CubeSurfaceMOG
import RequestProject.CubeStabiliser
import RequestProject.CubeTax
import RequestProject.MeasuredWords
import RequestProject.MeasuredSentences
import RequestProject.IntegerCube
import RequestProject.ThreeCube
import RequestProject.Semantics
import RequestProject.Grounding
import RequestProject.SentenceCode
import RequestProject.Chat
import RequestProject.Discourse
import RequestProject.WideDiscourse
import RequestProject.Dialogue
import RequestProject.Zipf
import RequestProject.Narrative
import RequestProject.WideWorld
import RequestProject.WideInteger
import RequestProject.WideChat
import RequestProject.WideZipf
import RequestProject.Abstract
import RequestProject.Causation
import RequestProject.ClauseStore
import RequestProject.CubeThought
import RequestProject.Conversation
import RequestProject.Paragraph
import RequestProject.PlanCost
import RequestProject.ReachPlan
import RequestProject.GolayCode
import RequestProject.GolaySteiner
import RequestProject.GolayInvolution
import RequestProject.GolayTh
import RequestProject.Quantified
import RequestProject.Learning
import RequestProject.Relative
import RequestProject.Scaling
import RequestProject.Continuous
import RequestProject.GolayEnumerator
import RequestProject.Capstone

namespace Package

/-! ## Report 1 — the cube surface as the MOG -/

-- the three-layer factorisation 2^24 → 2^18 → 2^12, and the Golay parameters
#print axioms CubeMOG.fibre_card
#print axioms CubeMOG.hexpass_card
#print axioms CubeMOG.mog_card
#print axioms CubeMOG.parity_layer_factor
#print axioms CubeMOG.mog_weight_enumerator
#print axioms CubeMOG.mog_min_weight

-- erasure: one face heals, every pair of faces is ambiguous
#print axioms CubeMOG.face_erasure_correctable
#print axioms CubeMOG.two_face_ambiguous

-- experiment 1: which cube symmetries are free
#print axioms CubeStab.stabiliser_card
#print axioms CubeStab.preserves_iff_tetrahedral
#print axioms CubeStab.oCode_rotations_free
#print axioms CubeStab.oCode_improper_priced

-- the price list, and the sharp 4·Q repair bound
#print axioms CubeTax.covering_radius_le_four
#print axioms CubeTax.covering_radius_ge_four
#print axioms CubeTax.tax_le_four_Q
#print axioms CubeTax.repair_unique_of_le_three
#print axioms CubeTax.repair_ambiguous_at_four
#print axioms CubeTax.xor_codeword_free
#print axioms CubeTax.and_is_priced

-- measurable words, and the characteristic-2 ceiling
#print axioms MeasuredWords.dimWord_mul
#print axioms MeasuredWords.accepts_true_equations
#print axioms MeasuredWords.mod_two_blindness_witness
#print axioms MeasuredWords.xor_encoding_is_mod_two
#print axioms MeasuredWords.dimension_channel_repairable

-- the measured precision of the parity cube: 356 true, 1758 accepted
#print axioms MeasuredSentences.phrases_count
#print axioms MeasuredSentences.equations_count
#print axioms MeasuredSentences.substrate_count
#print axioms MeasuredSentences.substrate_false_positive_count
#print axioms MeasuredSentences.equations_are_accepted

/-! ## Report 2 — past the precision wall, and into sentences -/

-- the integer cube: addition with carry, reversible, and exactly precise
#print axioms IntegerCube.encG_add
#print axioms IntegerCube.subG_addG
#print axioms IntegerCube.xor_is_add_without_carry
#print axioms IntegerCube.integer_accepts_eq_equations
#print axioms IntegerCube.integer_false_positive_count
#print axioms IntegerCube.encG_tax_le_four
#print axioms IntegerCube.wrap_blindness_witness
#print axioms IntegerCube.no_faithful_encoding

-- the three-cube (Turyn) construction and clause storage
#print axioms ThreeCube.turyn_min_weight
#print axioms ThreeCube.turyn_weight_enumerator
#print axioms SentenceCode.clause_min_distance
#print axioms SentenceCode.clause_repair_bound

-- the micro-world, its sentences, and the question answerer
#print axioms Semantics.speak_sound
#print axioms Semantics.because_is_explanatory
#print axioms Chat.answer_true
#print axioms Chat.why_reason_counts
#print axioms Grounding.well_typed_accepted
#print axioms Grounding.dimension_cannot_decide_truth

/-! ## Report 3 — connectives, conversation, Zipf, plans -/

-- and / but / so
#print axioms Discourse.para_sound
#print axioms Discourse.so_is_a_deduction
#print axioms Discourse.but_is_contrastive
#print axioms Discourse.and_is_informative
#print axioms Discourse.para_no_repetition
#print axioms Discourse.para_information_increases
#print axioms Discourse.corpus_facts
#print axioms WideDiscourse.wcorpus_facts

-- conversation
#print axioms Dialogue.reply_true
#print axioms Dialogue.run_no_contradiction
#print axioms Dialogue.script_facts

-- Zipf, and the least-effort code
#print axioms Zipf.corpus_is_flatter_than_zipf
#print axioms Zipf.zipf_worst_case
#print axioms Zipf.huffman_facts
#print axioms Zipf.least_effort_is_cheaper

-- planning and narration
#print axioms Narrative.plan_correct
#print axioms Narrative.story_reports_real_changes
#print axioms Narrative.plan_facts

/-! ## Stage 4 — the widened world, causation, storage, plans -/

-- the widened world: 24 entities, a vocabulary of 3600 literals, sound laws
#print axioms WideWorld.schemas_sound
#print axioms WideWorld.wide_vocab_counts
#print axioms WideWorld.describe_sound
#print axioms WideWorld.describe_consistent
#print axioms WideWorld.demoWide_count

-- integers on a pair of cubes: a 256-wide window, still with no faithful encoding
#print axioms WideInteger.decP_encP
#print axioms WideInteger.encP_add
#print axioms WideInteger.sixteen_no_longer_collides
#print axioms WideInteger.pair_window_is_256
#print axioms WideInteger.no_faithful_pair

-- kinship: an abstract vocabulary the measurements cannot define
#print axioms Abstract.ancestor_trans
#print axioms Abstract.ancestor_irrefl
#print axioms Abstract.mother_not_definable_by_readings
#print axioms Abstract.readings_not_definable_by_kin
#print axioms Abstract.describeK_sound
#print axioms Abstract.describeK_consistent
#print axioms Abstract.kin_vocab_counts

-- chat over the wide world
#print axioms WideChat.answer_is_true
#print axioms WideChat.reason_is_a_ground
#print axioms WideChat.reply_no_repetition
#print axioms WideChat.demo_transcript

-- Zipf over the wide vocabulary
#print axioms WideZipf.corpus_sizes
#print axioms WideZipf.wide_head_crosses_zipf
#print axioms WideZipf.zipf_band_counts

-- causation: "because" with a direction of time
#print axioms Causation.causalBecause_sound
#print axioms Causation.causalBecause_asymm
#print axioms Causation.causalBecause_trans
#print axioms Causation.actionCause_sound
#print axioms Causation.static_facts_have_no_action_cause
#print axioms Causation.grounding_is_cyclic
#print axioms Causation.causal_filter_counts

-- clause storage on the cube surface, and inference as translation
#print axioms ClauseStore.rec_min_distance
#print axioms ClauseStore.decodeRec_correct
#print axioms ClauseStore.roles_are_separated
#print axioms ClauseStore.repaired_store_is_still_sound
#print axioms CubeThought.apply_law
#print axioms CubeThought.negation_is_a_translation
#print axioms CubeThought.inference_survives_damage
#print axioms CubeThought.laws_are_sound_on_the_surface

-- conversation with pronouns
#print axioms Conversation.clause_roundtrip
#print axioms Conversation.answer_true
#print axioms Conversation.repeat_says_something_new
#print axioms Conversation.plan_is_optimal
#print axioms Conversation.demo_escalates

-- paragraphs that stop when there is nothing left to say
#print axioms Paragraph.cgrow_sound
#print axioms Paragraph.cgrow_ends_only_when_nothing_is_licensed
#print axioms Paragraph.ccorpus_facts
#print axioms Paragraph.pcorpus_facts
#print axioms Paragraph.assertion_length_is_the_fact_count

-- priced plans, and optimality without a horizon
#print axioms PlanCost.pickMin_le
#print axioms PlanCost.bestPlan_optimal
#print axioms PlanCost.bestPlan_none_iff
#print axioms PlanCost.plan_cost_facts
#print axioms PlanCost.argument_is_sound
#print axioms ReachPlan.all_worlds_reached
#print axioms ReachPlan.unbounded_optimality
#print axioms ReachPlan.bestGoalPlan_correct
#print axioms ReachPlan.horizon_gain

/-! ## The Golay files — the last claim of `FINAL_REPORT.md` §6 -/

#print axioms GolayInv.fiber_card
#print axioms GolayInv.unique_octad
#print axioms GolayInv.sigmaD_fixed_card
#print axioms GolayInv.no_diagonal_mirror_invariant_golay
#print axioms GolayInv.no_Td_invariant_golay
#print axioms GolayInv.no_Oh_invariant_golay
#print axioms GolayInv.oPack_isGolay
#print axioms GolayInv.exists_O_invariant_golay
#print axioms GolayInv.o_stabiliser_exact
#print axioms GolayInv.thPack_isGolay
#print axioms GolayInv.exists_Th_invariant_golay
#print axioms GolayInv.th_stabiliser_exact
#print axioms GolayInv.octad_count
#print axioms GolayInv.golay_weight_enumerator

/-! ## Stage 5 — learning, relative clauses, and the counts as functions of `n`

`STAGE5_REPORT.md` is the write-up.  These are its headline results. -/

#print axioms Learning.learn_holds_on_corpus
#print axioms Learning.laws_are_never_missed
#print axioms Learning.learn_antitone
#print axioms Learning.learn_all_worlds
#print axioms Learning.learning_curve
#print axioms Learning.prefix_corpus_needs_481
#print axioms Learning.generalisation_error_at_256
#print axioms Learning.teaching_set_learns_the_table
#print axioms Learning.teaching_set_irredundant
#print axioms Learning.teaching_lower_bound
#print axioms Learning.learned_table_on_the_surface

#print axioms Relative.evalR_flip
#print axioms Relative.restricted_is_conservative
#print axioms Relative.valid_iff_local
#print axioms Relative.law_schemas
#print axioms Relative.law_schemas_sound
#print axioms Relative.describeR_decides
#print axioms Relative.relative_clause_is_new
#print axioms Relative.accidental_generalisations

#print axioms Scaling.wcontingent_iff_not_reflexive
#print axioms Scaling.usefulLits_length_formula
#print axioms Scaling.describe_length_formula
#print axioms Scaling.describeQ_length_formula
#print axioms Scaling.describeR_length_formula

#print axioms Continuous.thresholds_depend_only_on_band
#print axioms Continuous.graded_separates
#print axioms Continuous.strongest_grade_is_exact
#print axioms Continuous.strongest_grade_determines_difference
#print axioms Continuous.claws_sound
#print axioms Continuous.difference_roundtrip_iff_window
#print axioms Continuous.difference_roundtrip2_iff_window
#print axioms Continuous.sayGrade_sound
#print axioms Continuous.sayGrade_none_iff
#print axioms Continuous.difference_is_well_typed
#print axioms Continuous.demoC_facts

#print axioms Capstone.learned_sentences_count
#print axioms Capstone.learned_sentences_are_assertible
#print axioms Capstone.learned_sentences_are_complete
#print axioms Capstone.why_answer_is_a_learned_law
#print axioms Capstone.why_answer_witness
#print axioms Capstone.premature_sentence_is_false

end Package
