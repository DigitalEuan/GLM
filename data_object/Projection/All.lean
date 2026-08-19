import Projection.Layers
import Projection.OneParameter
import Projection.Fibre
import Projection.Cheapest
import Projection.Cost
import Projection.Surprisal
import Projection.Independence

/-!
# The projection sub-study, assembled

This module imports the six modules of the sub-study and audits the axioms of
every headline theorem.  Nothing new is proved here.

Module order (and the graded cost model used to choose it — see
`Projection/README.md` for the full table):

1. `Projection.Layers` — the layer theorem.  *No finite symmetry produces `π` or
   `e`; `φ` is a character value of one.*  The headline.
2. `Projection.OneParameter` — the three one-parameter motions; `π` as period
   generator, `φ` as stretch eigenvalue, `e` as flow time-1 value.
3. `Projection.Fibre` — projection and fibre: the trace on `SL(2,ℤ)` and the
   hull `⌊·⌋` over 13 are both lossy, provably.
4. `Projection.Cheapest` — `φ` is the smallest *quadratic* Pisot number; the
   plastic number is smaller in degree 3; `φ` is badly approximable.
5. `Projection.Cost` — the coherence ladder is `Q`-gauge-independent; the graded
   cost model; a shortcut/distortion theorem.
6. `Projection.Surprisal` — the bit-score ledger.
7. `Projection.Independence` — appendix: the two branches of the
   `trdeg ℚ(π,e)` question, both stated conditionally.

Every theorem below depends only on Lean's three standard axioms
(`propext`, `Classical.choice`, `Quot.sound`).
-/

section AxiomAudit

open UBPProjection

-- Module 1 — the layer theorem
#print axioms eigenvalue_of_finite_order_pow_eq_one
#print axioms trace_isAlgebraic_of_finite_order
#print axioms transcendental_not_trace_of_finite_order
#print axioms lattice_character_ne_pi
#print axioms lattice_character_ne_e
#print axioms phi_is_trace_of_order_ten
#print axioms phi_mem_cyclotomic
#print axioms phi_not_eigenvalue_of_finite_order
#print axioms seed_layer_placement

-- Module 2 — the three motions
#print axioms rot_eq_one_iff
#print axioms two_pi_least_period
#print axioms period_fibre_infinite
#print axioms shear_eigenvalue_eq_one
#print axioms fibMat_eigenvector
#print axioms quadratic_eigenvalue_fibre
#print axioms phi_pow_beats_linear
#print axioms sl2_real_eigenvalue_iff
#print axioms flow_time_one
#print axioms e_flow_fibre

-- Module 3 — projection and fibre
#print axioms trace_fibre_infinite
#print axioms same_trace_not_conjugate
#print axioms floor_fibre_thirteen
#print axioms three_monomials_give_thirteen
#print axioms thirteen_not_invertible

-- Module 4 — cheapest
#print axioms phi_isQuadPisot
#print axioms quadratic_pisot_ge_phi
#print axioms plastic_lt_phi
#print axioms plastic_conjugates_inside_disc
#print axioms phi_badly_approximable
#print axioms phi_not_liouville

-- Module 5 — cost
#print axioms nrci_calibrated
#print axioms nrci_gauge_independent
#print axioms GradedCost.total_const
#print axioms shortcut_thirteen
#print axioms natAbs_le_thirteen_mul_wordLen
#print axioms shortcut_distortion

-- Module 6 — surprisal
#print axioms alpha_bits_lt_one
#print axioms muon_bits_between_three_and_four
#print axioms proton_bits_between_two_and_three
#print axioms capacityBits_pos

-- Appendix — the two branches
#print axioms pi_mul_e_dichotomy
#print axioms pi_mul_e_isAlgebraic_of_monad_rat
#print axioms monad_irrational_of_pi_mul_e_transcendental
#print axioms wobble_irrational_of_pi_mul_e_transcendental

end AxiomAudit
