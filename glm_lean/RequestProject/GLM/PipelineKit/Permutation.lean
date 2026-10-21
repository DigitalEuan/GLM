import RequestProject.GLM.PipelineKit.Leech

/-!
# Permutation operators (fix for DI1/DI3 "the combiner cannot express permutations")

*Created 21 October 2026* (Phase 175), from `source_material/GLM_Pipeline_Kit/GLMKit/Permutation.lean`
of the owner's 9-iteration pipeline study; imports renamed to `RequestProject.GLM.PipelineKit.*`,
statements and proofs unchanged.

The substrate's `combiner.apply_op` acts coordinatewise, so it cannot express `reflect_v`
(a permutation of cells). The kit adds `permute_op` (Python) whose Lean counterpart is
precomposition with a permutation `σ` of the coordinates.

* `wt_comp_perm`         : permutations preserve weight;
* `leech_layer_perm`     : hence a permuted target sits on the same lattice layer
                           (`4·b ∈ Λ₂₄` iff `4·(b ∘ σ) ∈ Λ₂₄`);
* `wt_not`               : toggling all `n` bits sends weight `w` to `n − w`, so on 24-cell
                           grids toggle also preserves parity (and the lattice layer).
* `reflectV`             : the vertical-axis mirror of an `h × w` grid, as a permutation of
                           cells; `reflectV_involutive` — applying it twice is the identity.
-/

namespace GLMKit

variable {n : ℕ}

theorem wt_comp_perm (b : Fin n → Bool) (σ : Equiv.Perm (Fin n)) : wt (b ∘ σ) = wt b := by
  unfold wt
  apply Finset.card_bij (fun i _ => σ i)
  · intro i hi; simpa using hi
  · intro i _ j _ h; exact σ.injective h
  · intro j hj; exact ⟨σ.symm j, by simpa using hj, by simp⟩

theorem leech_layer_perm (b : Fin 24 → Bool) (σ : Equiv.Perm (Fin 24)) :
    Leech24 (fun i => 4 * bitZ ((b ∘ σ) i)) ↔ Leech24 (fun i => 4 * bitZ (b i)) := by
  rw [leech24_parity_wall, leech24_parity_wall, wt_comp_perm]

theorem wt_not (b : Fin n → Bool) : wt (fun i => !b i) = n - wt b := by
  unfold wt
  have h := Finset.card_filter_add_card_filter_not (s := Finset.univ) (fun i => b i = true)
  simp only [Finset.card_univ, Fintype.card_fin] at h
  have : (Finset.univ.filter fun i => (!b i) = true) = Finset.univ.filter fun i => ¬ b i = true := by
    ext i; simp
  rw [this]
  omega

/-- On 24-cell grids, toggle preserves the lattice layer. -/
theorem leech_layer_toggle (b : Fin 24 → Bool) :
    Leech24 (fun i => 4 * bitZ (!b i)) ↔ Leech24 (fun i => 4 * bitZ (b i)) := by
  have h1 := leech24_parity_wall (fun i => !b i)
  have h2 := leech24_parity_wall b
  simp only at h1
  rw [h1, h2, wt_not, Nat.even_sub (by
    unfold wt; exact (Finset.card_filter_le _ _).trans (by simp))]
  simp [show Even 24 by decide]

/-- Mirror of an `h × w` grid across its vertical axis, as a permutation of cells. -/
def reflectV (h w : ℕ) : Equiv.Perm (Fin h × Fin w) :=
  Equiv.prodCongr (Equiv.refl _) Fin.revPerm

theorem reflectV_involutive (h w : ℕ) (x : Fin h × Fin w) : reflectV h w (reflectV h w x) = x := by
  obtain ⟨r, c⟩ := x
  simp [reflectV, Fin.revPerm_apply]

end GLMKit
