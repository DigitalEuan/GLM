module

public import RequestProject.GLM.Rule30.Ergodic

/-!
# Rule 30 is a measure-preserving dynamical system

The ergodic-theory frame: `(Config, bernoulliRow, step)` is a measure-preserving system.

* `step_iIndep`          : for a fair-coin row, the cells of the next row are again independent
  fair coins.
* `step_map`             : `bernoulliRow.map step = bernoulliRow`.
* `step_measurePreserving`, `evolve_measurePreserving` : Rule 30 (and every iterate) preserves
  the fair-coin measure.

So the fair-coin measure is an **invariant measure** of Rule 30. It is the natural "observer-free"
reference measure of the GLM picture. Together with `Ergodic.lean`: in this invariant measure, a
typical row has normal, aperiodic columns. The prize problems ask whether the specific row `seed`,
which is not typical for this measure (it is a null point, `bernoulliRow_seed_null`), still
behaves typically along its centre column.
-/

@[expose] public section

namespace GLM.Rule30

open MeasureTheory ProbabilityTheory

theorem measurable_step : Measurable step :=
  measurable_pi_lambda _ (fun c => measurable_evolve 1 c)

/-- A single coordinate is independent of the restriction to any finite set not containing it. -/
theorem cell_indep_restr (i : ℤ) (F : Finset ℤ) (hi : i ∉ F) :
    IndepFun (fun x : Config => x i) (restr F) bernoulliRow := by
  have h := coords_iIndep.indepFun_finset {i} F (by simpa using hi) (fun j => measurable_pi_apply j)
  let a : ({i} : Finset ℤ) := ⟨i, by simp⟩
  exact h.comp (φ := fun v : ({i} : Finset ℤ) → Bool => v a) (ψ := id)
    (measurable_pi_apply a) measurable_id

theorem cell_fair (i : ℤ) (b : Bool) : bernoulliRow ((fun x : Config => x i) ⁻¹' {b}) = 1 / 2 := by
  have := leftCell_fair i 0 b
  simpa using this

/-- The cells used by `step` on `S ∪ {m}`, apart from `m − 1`. -/
def stepSupport (m : ℤ) (S : Finset ℤ) : Finset ℤ :=
  insert m (insert (m + 1) (S.image (· - 1) ∪ S ∪ S.image (· + 1)))

theorem step_extW (m : ℤ) (S : Finset ℤ) (c : ℤ) (hc : c ∈ S) (x : Config) :
    step (extW (stepSupport m S) (restr (stepSupport m S) x)) c = step x c := by
  have h : ∀ j ∈ ({c - 1, c, c + 1} : Finset ℤ), j ∈ stepSupport m S := by
    intro j hj
    simp only [Finset.mem_insert, Finset.mem_singleton] at hj
    simp only [stepSupport, Finset.mem_insert, Finset.mem_union, Finset.mem_image]
    rcases hj with rfl | rfl | rfl
    · exact Or.inr (Or.inr (Or.inl (Or.inl ⟨c, hc, rfl⟩)))
    · exact Or.inr (Or.inr (Or.inl (Or.inr hc)))
    · exact Or.inr (Or.inr (Or.inr ⟨c, hc, rfl⟩))
  simp only [step, extW, restr]
  rw [dif_pos (h _ (by simp)), dif_pos (h _ (by simp)), dif_pos (h _ (by simp))]

theorem step_eq_xor (m : ℤ) (S : Finset ℤ) (x : Config) :
    step x m = xor (x (m - 1))
      ((extW (stepSupport m S) (restr (stepSupport m S) x)) m ||
        (extW (stepSupport m S) (restr (stepSupport m S) x)) (m + 1)) := by
  have h1 : m ∈ stepSupport m S := by simp [stepSupport]
  have h2 : m + 1 ∈ stepSupport m S := by simp [stepSupport]
  simp only [step, rule30, extW, restr, dif_pos h1, dif_pos h2]

theorem step_cell_step (m : ℤ) (S : Finset ℤ) (hS : ∀ c ∈ S, m < c) (h : (stepSupport m S → Bool) → Bool)
    (A : Set (stepSupport m S → Bool)) :
    bernoulliRow ({x | step x m = h (restr (stepSupport m S) x)} ∩ restr (stepSupport m S) ⁻¹' A) =
      1 / 2 * bernoulliRow (restr (stepSupport m S) ⁻¹' A) := by
  have hnot : m - 1 ∉ stepSupport m S := by
    intro hmem
    simp only [stepSupport, Finset.mem_insert, Finset.mem_union, Finset.mem_image] at hmem
    rcases hmem with h | h | ((⟨c, hc, h⟩ | hc) | ⟨c, hc, h⟩)
    · omega
    · omega
    · have := hS c hc; omega
    · have := hS _ hc; omega
    · have := hS c hc; omega
  have key := half_of_indep (μ := bernoulliRow) (fun x : Config => x (m - 1))
    (restr (stepSupport m S)) (measurable_pi_apply _) (measurable_restr _)
    (cell_indep_restr _ _ hnot) (cell_fair _)
    (fun v => xor (h v) (extW (stepSupport m S) v m || extW (stepSupport m S) v (m + 1)))
    (measurable_of_finite _) A (Set.toFinite A).measurableSet
  rw [← key]
  congr 1
  ext x
  simp only [Set.mem_inter_iff, Set.mem_setOf_eq]
  rw [step_eq_xor m S x]
  cases x (m - 1) <;> cases h (restr (stepSupport m S) x) <;>
    cases (extW (stepSupport m S) (restr (stepSupport m S) x) m ||
      extW (stepSupport m S) (restr (stepSupport m S) x) (m + 1)) <;> simp

theorem step_fair (m : ℤ) (b : Bool) : bernoulliRow ((fun x => step x m) ⁻¹' {b}) = 1 / 2 := by
  have := step_cell_step m ∅ (by simp) (fun _ => b) Set.univ
  simp only [Set.preimage_univ, Set.inter_univ, measure_univ, mul_one] at this
  exact this

/-- **The next row of a fair-coin row is again a fair-coin row**: its cells are independent. -/
theorem step_iIndep : iIndepFun (fun c x => step x c) bernoulliRow := by
  rw [iIndepFun_iff_measure_inter_preimage_eq_mul]
  intro S
  induction S using Finset.induction_on_min with
  | h0 => intro sets _; simp
  | step m S hgt ih =>
    intro sets _
    have hmS : m ∉ S := fun h => lt_irrefl m (hgt m h)
    rw [Finset.prod_insert hmS, Finset.set_biInter_insert]
    have hrep : (⋂ i ∈ S, (fun x => step x i) ⁻¹' sets i) = restr (stepSupport m S) ⁻¹'
        {v | ∀ i ∈ S, step (extW (stepSupport m S) v) i ∈ sets i} := by
      ext x
      simp only [Set.mem_iInter, Set.mem_preimage, Set.mem_setOf_eq]
      constructor
      · intro hx i hi; rw [step_extW m S i hi]; exact hx i hi
      · intro hx i hi; rw [← step_extW m S i hi]; exact hx i hi
    have hstep : bernoulliRow ((fun x => step x m) ⁻¹' sets m ∩ restr (stepSupport m S) ⁻¹'
        {v | ∀ i ∈ S, step (extW (stepSupport m S) v) i ∈ sets i}) =
        bernoulliRow ((fun x => step x m) ⁻¹' sets m) * bernoulliRow (restr (stepSupport m S) ⁻¹'
        {v | ∀ i ∈ S, step (extW (stepSupport m S) v) i ∈ sets i}) := by
      rcases set_bool_cases (sets m) with h | h | h | h <;> rw [h]
      · simp
      · rw [step_fair]; exact step_cell_step m S hgt (fun _ => true) _
      · rw [step_fair]; exact step_cell_step m S hgt (fun _ => false) _
      · rw [Set.preimage_univ, Set.univ_inter, measure_univ, one_mul]
    rw [hrep, hstep, ← hrep, ih (sets := sets) (fun _ _ => (Set.toFinite _).measurableSet)]

/-- **Rule 30 preserves the fair-coin measure.** -/
theorem step_map : bernoulliRow.map step = bernoulliRow := by
  have h := (iIndepFun_iff_map_fun_eq_infinitePi_map (fun c => measurable_evolve 1 c)).1 step_iIndep
  have hc : ∀ c, bernoulliRow.map (fun x => step x c) = coin := by
    intro c
    rw [Measure.ext_iff_singleton]
    intro b
    rw [Measure.map_apply (f := fun x => step x c) (measurable_evolve 1 c) (measurableSet_singleton b),
      step_fair, coin_singleton]
  have h' : bernoulliRow.map (fun x c => step x c) = Measure.infinitePi (fun _ : ℤ => coin) := by
    rw [show (fun x c => step x c) = (fun x c => evolve x 1 c) from rfl, h]
    congr 1
    funext c
    exact hc c
  exact h'

theorem step_measurePreserving : MeasurePreserving step bernoulliRow bernoulliRow :=
  ⟨measurable_step, step_map⟩

theorem evolve_eq_iterate (x : Config) (n : ℕ) : evolve x n = step^[n] x := by
  induction n generalizing x with
  | zero => rfl
  | succ n ih => rw [evolve_succ', ih, Function.iterate_succ_apply]

/-- **Every iterate of Rule 30 preserves the fair-coin measure.** -/
theorem evolve_measurePreserving (n : ℕ) :
    MeasurePreserving (fun x => evolve x n) bernoulliRow bernoulliRow := by
  have : (fun x => evolve x n) = step^[n] := funext fun x => evolve_eq_iterate x n
  rw [this]
  exact step_measurePreserving.iterate n

end GLM.Rule30
