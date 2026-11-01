import GLMKit

/-! Run `lake env lean AxiomAudit.lean` to list the axioms behind the headline results.
Expected: only `propext`, `Classical.choice`, `Quot.sound`, plus `Lean.ofReduceBool` /
`Lean.trustCompiler` for the finite checks discharged by `native_decide`. -/

open GLMKit

#print axioms golay_weight_enumerator
#print axioms golay_xor_closed
#print axioms golay_min_distance
#print axioms steiner_5_8_24
#print axioms leech_theta_coefficients
#print axioms parity_wall
#print axioms parity_wall_glue
#print axioms eight_mul_mem
#print axioms junction_iff
#print axioms junction_same_parity
#print axioms bw_four_mul_mem
#print axioms constrA_p_mul_mem
#print axioms constrA_spin_artifact
#print axioms snap_analogy_noop
#print axioms plessS_mul_transpose
#print axioms plessS_transpose_ker_trivial
#print axioms no_field_of_card_six
#print axioms f9_units_cyclic_order_eight
#print axioms f9_alpha_order_four
#print axioms xor_analogy_exact_iff
#print axioms threshold_analogy_toggle_iff
#print axioms parity_decode_eq_xor
#print axioms binary_mem_convexHull_iff
#print axioms leech_layer_perm
#print axioms leech_layer_toggle
