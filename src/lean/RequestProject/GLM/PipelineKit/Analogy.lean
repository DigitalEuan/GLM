import RequestProject.GLM.PipelineKit.Leech

/-!
# Analogies, displacements and convex hulls (iterations 1, 2, 7, 8)

*Created 21 October 2026* (Phase 175), from `source_material/GLM_Pipeline_Kit/GLMKit/Analogy.lean`
of the owner's 9-iteration pipeline study; imports renamed to `RequestProject.GLM.PipelineKit.*`,
statements and proofs unchanged.

* `xor_analogy_exact_iff` : the `F₂` analogy `D = C ⊕ (A ⊕ B)` is exact iff the displacement
  `x ⊕ f(x)` is the same for `A` and `C` (iteration 1: "a state difference is not generally the
  rule"); for toggle (`f x = ¬x`) it is always exact (`xor_analogy_toggle`).
* `threshold_analogy_toggle_iff` : iteration 8's `Λ₄₈` dual snap (integer analogy
  `3(c + b − a)` decoded by the threshold `≥ 2`) is exact on toggle **only when `A = C`**, which
  explains its 0 % toggle score. `parity_decode_eq_xor` : decoding by parity instead
  (the fix) turns it into the `F₂` analogy, which is 100 % exact on toggle.
* `binary_mem_convexHull_iff` : a 0/1 target lies in the convex hull of a set of 0/1 vectors
  iff it is one of them. So iteration 2's "100 % hull separation" just says the targets were
  not Golay codewords; and constant targets `c·𝟙` lie in the hull because `0` and `𝟙` are
  codewords (`const_mem_convexHull`).
-/

namespace GLMKit

variable {n : ℕ}

/-- The `F₂` analogy `A : B :: C : D` with `D = C ⊕ (A ⊕ B)`. -/
def xorAnalogy (a b c : Fin n → Bool) : Fin n → Bool := fun i => xor (c i) (xor (a i) (b i))

theorem xor_analogy_exact_iff (f : (Fin n → Bool) → (Fin n → Bool)) (a c : Fin n → Bool) :
    xorAnalogy a (f a) c = f c ↔ (fun i => xor (c i) (f c i)) = fun i => xor (a i) (f a i) := by
  constructor
  · intro h
    funext i
    have := congrFun h i
    simp only [xorAnalogy] at this
    rw [← this]
    cases a i <;> cases c i <;> cases f a i <;> rfl
  · intro h
    funext i
    have := congrFun h i
    simp only [xorAnalogy]
    simp only at this
    rw [← this]
    cases c i <;> cases f c i <;> rfl

/-- Any coordinatewise "XOR with a fixed mask" rule (toggle = mask `𝟙`) is solved exactly by the
`F₂` analogy from a single demonstration. -/
theorem xor_analogy_mask (k a c : Fin n → Bool) :
    xorAnalogy a (fun i => xor (a i) (k i)) c = fun i => xor (c i) (k i) := by
  funext i; simp only [xorAnalogy]; cases a i <;> cases c i <;> cases k i <;> rfl

theorem xor_analogy_toggle (a c : Fin n → Bool) :
    xorAnalogy a (fun i => !a i) c = fun i => !c i := by
  funext i; simp only [xorAnalogy]; cases a i <;> cases c i <;> rfl

/-- Iteration 8's decode of the `3×`-embedded integer analogy: bit `= [3(c + b − a) ≥ 2]`. -/
def thresholdAnalogy (a b c : Fin n → Bool) : Fin n → Bool :=
  fun i => decide (2 ≤ 3 * (bitZ (c i) + bitZ (b i) - bitZ (a i)))

/-- **Why the `Λ₄₈` dual snap scores 0 % on toggle.** It is exact iff the demonstration input
equals the query input. -/
theorem threshold_analogy_toggle_iff (a c : Fin n → Bool) :
    thresholdAnalogy a (fun i => !a i) c = (fun i => !c i) ↔ a = c := by
  constructor
  · intro h
    funext i
    have := congrFun h i
    simp only [thresholdAnalogy] at this
    cases ha : a i <;> cases hc : c i <;> simp_all [bitZ]
  · rintro rfl
    funext i
    simp only [thresholdAnalogy]
    have key : ∀ x : Bool, decide (2 ≤ 3 * (bitZ x + bitZ (!x) - bitZ x)) = !x := by
      intro x; cases x <;> decide
    exact key (a i)

/-- The fix: decode the integer analogy by parity. -/
def parityAnalogy (a b c : Fin n → Bool) : Fin n → Bool :=
  fun i => decide ((bitZ (c i) + bitZ (b i) - bitZ (a i)) % 2 = 1)

theorem parity_decode_eq_xor (a b c : Fin n → Bool) : parityAnalogy a b c = xorAnalogy a b c := by
  funext i
  simp only [parityAnalogy, xorAnalogy]
  cases a i <;> cases b i <;> cases c i <;> simp [bitZ]

theorem parity_analogy_toggle (a c : Fin n → Bool) :
    parityAnalogy a (fun i => !a i) c = fun i => !c i := by
  rw [parity_decode_eq_xor, xor_analogy_toggle]

/-! ### Convex hulls of 0/1 vectors (iteration 2, phase 2) -/

/-- A 0/1 vector is an extreme point of the unit cube. -/
lemma binary_mem_extremePoints_cube (t : Fin n → ℝ) (ht : ∀ i, t i = 0 ∨ t i = 1) :
    t ∈ Set.extremePoints ℝ {x : Fin n → ℝ | ∀ i, 0 ≤ x i ∧ x i ≤ 1} := by
  rw [mem_extremePoints]
  refine ⟨fun i => by rcases ht i with h | h <;> rw [h] <;> norm_num, ?_⟩
  rintro x hx y hy ⟨a, b, ha, hb, hab, hxy⟩
  have key : ∀ i, x i = t i ∧ y i = t i := by
    intro i
    have hi := congrFun hxy i
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul] at hi
    obtain ⟨hx0, hx1⟩ := hx i
    obtain ⟨hy0, hy1⟩ := hy i
    rcases ht i with h | h <;> rw [h] at hi ⊢
    · constructor <;> nlinarith
    · constructor <;> nlinarith
  exact ⟨funext fun i => (key i).1, funext fun i => (key i).2⟩

/-- **Hull separation is membership.** A 0/1 target lies in the convex hull of a set of 0/1
vectors iff it belongs to the set. -/
theorem binary_mem_convexHull_iff (S : Set (Fin n → ℝ)) (hS : ∀ s ∈ S, ∀ i, s i = 0 ∨ s i = 1)
    (t : Fin n → ℝ) (ht : ∀ i, t i = 0 ∨ t i = 1) : t ∈ convexHull ℝ S ↔ t ∈ S := by
  refine ⟨fun h => ?_, fun h => subset_convexHull ℝ S h⟩
  set cube := {x : Fin n → ℝ | ∀ i, 0 ≤ x i ∧ x i ≤ 1}
  have hcube : Convex ℝ cube := by
    intro x hx y hy a b ha hb hab i
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    obtain ⟨hx0, hx1⟩ := hx i
    obtain ⟨hy0, hy1⟩ := hy i
    constructor <;> nlinarith
  have hsub : convexHull ℝ S ⊆ cube := convexHull_min (fun s hs i => by
    rcases hS s hs i with h | h <;> rw [h] <;> norm_num) hcube
  have hext : t ∈ Set.extremePoints ℝ (convexHull ℝ S) :=
    inter_extremePoints_subset_extremePoints_of_subset hsub
      ⟨h, binary_mem_extremePoints_cube t ht⟩
  exact extremePoints_convexHull_subset hext

/-- Constant targets `c·𝟙` (`0 ≤ c ≤ 1`) lie in the hull of any set containing `0` and `𝟙`
(both are Golay codewords, `GLMKit.zero_mem_golay`, `GLMKit.allOnes_mem_golay`). -/
theorem const_mem_convexHull (S : Set (Fin n → ℝ)) (h0 : (0 : Fin n → ℝ) ∈ S)
    (h1 : (fun _ => (1 : ℝ)) ∈ S) (c : ℝ) (hc0 : 0 ≤ c) (hc1 : c ≤ 1) :
    (fun _ => c) ∈ convexHull ℝ S := by
  have hseg : segment ℝ (0 : Fin n → ℝ) (fun _ => (1 : ℝ)) ⊆ convexHull ℝ S :=
    segment_subset_convexHull h0 h1
  apply hseg
  refine ⟨1 - c, c, by linarith, hc0, by ring, ?_⟩
  funext i
  simp

end GLMKit
