import RequestProject.GLM.PipelineKit.Leech

/-!
# Higher lattice layers: `Λ₃₂` (Construction D), `Λ₄₈`/`Λ₉₆` (Construction A over `F₃`)

*Created 21 October 2026* (Phase 175), from `source_material/GLM_Pipeline_Kit/GLMKit/Lattices.lean`
of the owner's 9-iteration pipeline study; imports renamed to `RequestProject.GLM.PipelineKit.*`,
statements and proofs unchanged.

What iterations 4, 6, 7, 8 and 9 measured, and why the numbers came out as they did.

* `bw_four_mul_mem` : `4ℤⁿ ⊆ 4ℤⁿ + 2·C₂ + C₁` — iteration 4's `Λ₃₂` "room" success is the
  inclusion of `4ℤⁿ`; the padding bits play no role.
* `constrA_p_mul_mem` : `pℤⁿ ⊆` any Construction-A lattice — iteration 4/6's `Λ₄₈`, `Λ₉₆`
  "spin" success is the inclusion of `3ℤⁿ` (3 ≡ 0 in `F₃`, i.e. *deletion*, not a unit).
* `constrA_spin_artifact` : every coordinate permutation and every integer rescaling of a
  `3×`-embedded target stays in the lattice, so the "3-spin" (iter 6) and "8-spin" (iter 7)
  superposition counts are just the number of operations tried, independent of the target.
* `constrA_analogy_mem`, `snap_analogy_noop` : for a linear code, `D* = C + (B − A)` of three
  lattice points is already a lattice point, so **every** snap that fixes lattice points
  (trivial or the iteration-9 syndrome-coset decoder) returns `D*` unchanged (DI7, explained
  in full generality — it is not specific to the trivial embedding).

Compare `GLMKit.eight_mul_mem`: the same trivial-scaling phenomenon already happens inside
`Λ₂₄` with the factor 8.
-/

namespace GLMKit

variable {n : ℕ}

/-- Construction-D style lattice `4ℤⁿ + 2·C₂ + C₁` for binary codes `C₁ ⊆ C₂`
(the `Λ₃₂` Barnes–Wall form used in iteration 4, with `C₁ = RM(1,5)`, `C₂ = RM(3,5)`). -/
def ConstrD (C₁ C₂ : Set (Fin n → Bool)) (x : Fin n → ℤ) : Prop :=
  ∃ (a : Fin n → ℤ) (c₂ c₁ : Fin n → Bool), c₂ ∈ C₂ ∧ c₁ ∈ C₁ ∧
    ∀ i, x i = 4 * a i + 2 * bitZ (c₂ i) + bitZ (c₁ i)

/-- `4ℤⁿ` lies in the Construction-D lattice, for any codes containing `0`. -/
theorem bw_four_mul_mem (C₁ C₂ : Set (Fin n → Bool)) (h₁ : (fun _ => false) ∈ C₁)
    (h₂ : (fun _ => false) ∈ C₂) (v : Fin n → ℤ) : ConstrD C₁ C₂ (fun i => 4 * v i) :=
  ⟨v, _, _, h₂, h₁, fun i => by simp [bitZ]⟩

/-- Construction A over `ZMod p`: `x ∈ ℤⁿ` with `x mod p ∈ C` (iteration 4's `Λ₄₈` over the
Pless code, iteration 6's `Λ₉₆` over `C ⊕ C`). -/
def ConstrA (p : ℕ) (C : Set (Fin n → ZMod p)) (x : Fin n → ℤ) : Prop :=
  (fun i => (x i : ZMod p)) ∈ C

/-- `pℤⁿ` lies in every Construction-A lattice whose code contains `0`. -/
theorem constrA_p_mul_mem (p : ℕ) (C : Set (Fin n → ZMod p)) (h0 : 0 ∈ C) (v : Fin n → ℤ) :
    ConstrA p C (fun i => p * v i) := by
  unfold ConstrA
  convert h0 using 1
  funext i
  simp

/-- The `3×`-embedding of a binary word (as in `snap_ternary_48`) is always in `Λ₄₈`. -/
theorem constrA_three_mul_binary (C : Set (Fin n → ZMod 3)) (h0 : 0 ∈ C) (b : Fin n → Bool) :
    ConstrA 3 C (fun i => 3 * bitZ (b i)) := by
  exact_mod_cast constrA_p_mul_mem 3 C h0 (fun i => bitZ (b i))

/-- **Spin-count artifact.** Every permutation of coordinates composed with every integer
rescaling maps a `p×`-embedded target back into the lattice. -/
theorem constrA_spin_artifact (p : ℕ) (C : Set (Fin n → ZMod p)) (h0 : 0 ∈ C)
    (v : Fin n → ℤ) (σ : Equiv.Perm (Fin n)) (k : ℤ) :
    ConstrA p C (fun i => k * (p * v (σ i))) := by
  unfold ConstrA
  convert h0 using 1
  funext i
  simp

/-- For a linear code, Construction A is closed under `D* = C + (B − A)`. -/
theorem constrA_analogy_mem (p : ℕ) (C : AddSubgroup (Fin n → ZMod p)) {a b c : Fin n → ℤ}
    (ha : ConstrA p C a) (hb : ConstrA p C b) (hc : ConstrA p C c) :
    ConstrA p C (fun i => c i + (b i - a i)) := by
  unfold ConstrA at *
  have := C.add_mem hc (C.sub_mem hb ha)
  convert this using 1
  funext i
  simp

/-- **DI7 in general.** Any snap that fixes lattice points returns `D* = C + (B − A)`
unchanged when `A, B, C` are lattice points: the snap step of the lattice analogy is a no-op. -/
theorem snap_analogy_noop (p : ℕ) (C : AddSubgroup (Fin n → ZMod p))
    (snap : (Fin n → ℤ) → (Fin n → ℤ)) (hsnap : ∀ x, ConstrA p C x → snap x = x)
    {a b c : Fin n → ℤ} (ha : ConstrA p C a) (hb : ConstrA p C b) (hc : ConstrA p C c) :
    snap (fun i => c i + (b i - a i)) = fun i => c i + (b i - a i) :=
  hsnap _ (constrA_analogy_mem p C ha hb hc)

end GLMKit
