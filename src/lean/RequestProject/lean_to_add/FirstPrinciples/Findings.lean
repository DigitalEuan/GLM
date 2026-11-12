import FirstPrinciples.Distinction
import FirstPrinciples.Distance
import FirstPrinciples.Packing
import FirstPrinciples.Seeds
import FirstPrinciples.FitCapacity
import FirstPrinciples.Triad
import UBP.League2

set_option autoImplicit false

/-!
# The first-principles sub-study, assembled

This module imports the five stages, records the two places where the
first-principles chain touches the parent audit, and prints the axiom
dependencies of every headline finding.  The prose version of the list is
`FirstPrinciples/FINDINGS.md`.

The chain, in one paragraph:

> A distinction is the least a substrate can carry (FP-1, FP-2); `n` of them
> give `2ⁿ` states (FP-3); the only reversible unary operation is the toggle
> (FP-4); the two-element carrier is the field `ZMod 2` (FP-5), so the state
> space is `(ZMod 2)ⁿ`, in which every element is self-inverse (FP-6) and
> commutativity is a theorem (FP-7).  Toggle-count is then the substrate's
> metric (FP-8, FP-9), unique decoding within radius `t` needs minimum distance
> `2t+1` (FP-10, FP-11), and even minimum distance always leaves an ambiguous
> state (FP-12).  Counting balls (FP-13) gives the sphere-packing bound (FP-14),
> whose equality case for three-error correction picks out the lengths `7` and
> `23` and no others below 2000 (FP-15, FP-16); at length `24` the same code
> leaves 43 % of the space uncovered (FP-17), so `24` is a self-duality
> preference, not an information-theoretic necessity (FP-18).  Up to here every
> quantity is an integer, and no seed is a ratio of integers (FP-19): `π, φ, e`
> enter as an independent input.  Each is forced by the rôle it is given
> (FP-20, FP-21, FP-22) and the three are distinct (FP-23), but the rule that
> multiplies them into `ℳ` and reads off `13` is not forced (FP-24).  Finally,
> the numerical agreements: a lattice of candidate values approximates every
> target to half its spacing (FP-25), which already accounts for the `α⁻¹` fit
> (FP-26, FP-27), leaves the muon fit worth one order of magnitude (FP-28) and
> the proton fit worth a factor four (FP-29); the general bound is FP-30, and
> the intermediate "hierarchy" layer is definitional (FP-31).  The decorative
> arithmetic `3, 6, 9` and `24` is generic (FP-32 … FP-35).
-/

namespace UBPFirstPrinciples

/-! ## Where the chain meets the parent audit -/

/-- **Bridge 1.**  The extended Golay code has minimum distance `8 = 2·3 + 2`,
so FP-12 applies to it: its fourth toggle is never correctable.  The parent
study exhibits this concretely — the weight-4 pattern `30` sends the all-ones
codeword to a *different* codeword of weight 16, while the weight-4 pattern `15`
is still corrected. -/
theorem bridge_even_distance_is_realised :
    LatticeShortcut.pop 30 = 4 ∧
      LatticeShortcut.decode (UBP.League2.allOnes ^^^ 30) ≠ UBP.League2.allOnes ∧
      LatticeShortcut.pop (LatticeShortcut.decode (UBP.League2.allOnes ^^^ 30)) = 16 :=
  UBP.League2.weight_four_can_escape

/-- **Bridge 2.**  The parent study's central numerical object, `ℳ = πφe` with
`⌊ℳ⌋ = 13`, is the one place where Stage 3's free choice (FP-24) enters the
physics formulas; every downstream number is a rational expression in it. -/
theorem bridge_hull_is_a_choice :
    ⌊UBP.monad⌋ = 13 ∧ ⌊Real.pi * UBP.eSeed / UBP.phi⌋ = 5 :=
  ⟨hull_alternatives.1, hull_alternatives.2.1⟩

end UBPFirstPrinciples

/-! ## Axiom audit -/

section Audit

open UBPFirstPrinciples

-- Stage 0
#print axioms no_information_without_distinction
#print axioms surjects_onto_bool
#print axioms bitfield_card
#print axioms perm_bool_card
#print axioms two_element_ring_is_zmod_two
#print axioms perm_bool_eq
#print axioms self_inverse
#print axioms reachable
#print axioms self_inverse_forces_comm

-- Stage 1
#print axioms dist_translation_invariant
#print axioms dist_eq_weight
#print axioms unique_decoding
#print axioms even_distance_ambiguity

-- Stage 2
#print axioms ball_card_eq
#print axioms hamming_bound
#print axioms perfect_triple_length
#print axioms golay23_perfect_arithmetic
#print axioms golay24_not_perfect
#print axioms parityExt_dist_of_odd
#print axioms parityExt_min_distance

-- Stage 3
#print axioms seeds_not_ratio_of_counts
#print axioms phi_reachable_by_root_extraction
#print axioms pi_e_not_algebraically_reachable
#print axioms phi_unique_positive_root
#print axioms pi_least_positive_zero
#print axioms e_unique_unit_growth_base
#print axioms hull_alternatives

-- Stage 4
#print axioms lattice_approx
#print axioms alpha_generic_guarantee
#print axioms muon_generic_guarantee
#print axioms alpha_fit_barely_beats_generic
#print axioms muon_fit_beats_generic_by_ten
#print axioms proton_generic_guarantee
#print axioms proton_fit_beats_generic_by_four
#print axioms protonPred_eq
#print axioms fit_capacity
#print axioms unmatched_target_exists
#print axioms derived_layer_is_definitional

-- Stage 5
#print axioms tgic_counts_generic
#print axioms interaction_counts_differ
#print axioms twentyfour_decompositions

-- Bridges
#print axioms bridge_even_distance_is_realised
#print axioms bridge_hull_is_a_choice

end Audit
