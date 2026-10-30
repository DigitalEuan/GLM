import RequestProject.GLM.AxiomGuard
import RequestProject.GLM.PipelineKit.Golay
import RequestProject.GLM.PipelineKit.Leech
import RequestProject.GLM.PipelineKit.Lattices
import RequestProject.GLM.PipelineKit.Fields
import RequestProject.GLM.PipelineKit.Pless
import RequestProject.GLM.PipelineKit.Analogy
import RequestProject.GLM.PipelineKit.Permutation
import RequestProject.GLM.PipelineInduction

/-!
# Axiom audit of the pipeline kit, enforced by the build

*Created 21 October 2026* (Phase 176), from `source_material/GLM_Pipeline_Kit/GLMKit/AxiomAudit.lean`.
The kit's file lists `#print axioms` for its 25 headline results and asks the reader to check the
output by eye. Here the same 25 names (unchanged) are passed to `#guard_axioms`, which fails the
build if any of them depends on an axiom outside the standard set (see `AxiomGuard.lean`). The
17 theorems of `PipelineInduction.lean` (Phase 175) are guarded too, and the last line guards
every theorem in the `GLMKit` namespace, not only the headline ones.
-/

open GLMKit

#guard_axioms golay_weight_enumerator golay_xor_closed golay_min_distance steiner_5_8_24
  leech_theta_coefficients parity_wall parity_wall_glue eight_mul_mem junction_iff
  junction_same_parity bw_four_mul_mem constrA_p_mul_mem constrA_spin_artifact snap_analogy_noop
  plessS_mul_transpose plessS_transpose_ker_trivial no_field_of_card_six
  f9_units_cyclic_order_eight f9_alpha_order_four xor_analogy_exact_iff
  threshold_analogy_toggle_iff parity_decode_eq_xor binary_mem_convexHull_iff leech_layer_perm
  leech_layer_toggle

open GLM.PipelineInduction in
#guard_axioms truth_consistent consistent_of_subset agree_sound ambiguous_forces_refusal
  mem_consistentIn consistentIn_more_demos collapse_some collapse_some_of_agree
  collapse_none_of_disagree mem_selectTier selectTier_append solve_sound
  solve_refuses_disagreement solve_answers_agreement solve_never_invents solve_none_of_unfit
  perm_toggle_layer

#guard_axioms_prefix GLMKit
