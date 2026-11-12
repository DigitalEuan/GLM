module

public import RequestProject.GLM.Rule30.AdjacentColumns
public import RequestProject.GLM.Rule30.Wobble

/-!
# Measure-theoretic layer: Problems 1 and 2 hold for almost every initial row

Put the fair-coin (Bernoulli `1/2`) product measure `bernoulliRow` on the space of all rows
`ℤ → Bool`. We prove that, **for a random row, every column of Rule 30 is exactly a sequence of
independent fair coin flips**, and deduce the strong law and aperiodicity almost surely:

* `column_bit_fair`        : each bit `a(t)(c)` is a fair coin.
* `column_iIndep`          : the bits `a(0)(c), a(1)(c), a(2)(c), …` are mutually independent.
* `column_law`             : the law of the column `t ↦ a(t)(c)` is the fair-coin product measure
  on `ℕ → Bool`.
* `column_prefix_law`      : every column word of length `n` has probability exactly `2^{-n}`.
* `ae_column_frequency_half` : **Problem 2 holds for almost every row** (strong law of large
  numbers, Etemadi's form, from Mathlib).
* `ae_column_not_eventuallyPeriodic` : **Problem 1 holds for almost every row.**

The engine is cone separation (left-permutivity): `a(t)(c) = x_{c−t} xor (function of
x_{c−t+1}, …, x_{c+t})`, and the new coordinate `x_{c−t}` is a fair coin independent of
everything the earlier bits of the column depend on.

**Why this does not settle the prize problems.** The seed is a single point of the row space,
and it has probability `0`. "Almost every" says nothing about it. `ColumnInverse.lean` shows the
gap cannot be closed by measure theory alone: every sequence whatsoever (periodic, biased, …)
is the centre column of some row.
-/

@[expose] public section

namespace GLM.Rule30

open MeasureTheory ProbabilityTheory Filter Topology

/-- The fair coin on `Bool`. -/
noncomputable def coin : Measure Bool := (PMF.uniformOfFintype Bool).toMeasure

instance : IsProbabilityMeasure coin := by unfold coin; infer_instance

theorem coin_singleton (b : Bool) : coin {b} = 1 / 2 := by
  unfold coin
  rw [PMF.toMeasure_apply_singleton _ _ (measurableSet_singleton b),
    PMF.uniformOfFintype_apply]
  simp

/-- The fair-coin product measure on rows: every cell independently black with probability
`1/2`. -/
noncomputable def bernoulliRow : Measure Config := Measure.infinitePi (fun _ : ℤ => coin)

instance : IsProbabilityMeasure bernoulliRow := by unfold bernoulliRow; infer_instance

/-- The column at position `c`, as a random variable on rows. -/
def colAt (c : ℤ) (t : ℕ) (x : Config) : Bool := evolve x t c

/-! ## Measurability -/

theorem measurable_evolve (t : ℕ) (c : ℤ) : Measurable (fun x : Config => evolve x t c) := by
  induction t generalizing c with
  | zero => exact measurable_pi_apply c
  | succ t ih =>
    have h : Measurable (fun x : Config =>
        ((evolve x t (c - 1), evolve x t c, evolve x t (c + 1)) : Bool × Bool × Bool)) :=
      (ih _).prodMk ((ih _).prodMk (ih _))
    exact (measurable_of_finite (fun p : Bool × Bool × Bool => rule30 p.1 p.2.1 p.2.2)).comp h

theorem measurable_colAt (c : ℤ) (t : ℕ) : Measurable (colAt c t) := measurable_evolve t c

/-! ## Independence of one coordinate from a finite block -/

/-- The cells strictly inside the light cone on the left: `(c − t, c + t]`. -/
def innerCone (c : ℤ) (t : ℕ) : Finset ℤ := Finset.Ioc (c - t) (c + t)

/-- Restriction of a row to a finite set of cells. -/
def restr (F : Finset ℤ) (x : Config) : F → Bool := fun i => x i

/-- Extension by white cells. -/
def extW (F : Finset ℤ) (v : F → Bool) : Config := fun i => if h : i ∈ F then v ⟨i, h⟩ else false

theorem measurable_restr (F : Finset ℤ) : Measurable (restr F) :=
  measurable_pi_lambda _ (fun i => measurable_pi_apply (i : ℤ))

theorem coords_iIndep : iIndepFun (fun (i : ℤ) (x : Config) => x i) bernoulliRow := by
  have := iIndepFun_infinitePi (P := fun _ : ℤ => coin) (X := fun _ => (id : Bool → Bool))
    (fun _ => measurable_id)
  simpa using this

/-- The leftmost cell of the cone is independent of the inner cone. -/
theorem leftCell_indep_innerCone (c : ℤ) (t : ℕ) :
    IndepFun (fun x : Config => x (c - t)) (restr (innerCone c t)) bernoulliRow := by
  have h := coords_iIndep.indepFun_finset {c - (t : ℤ)} (innerCone c t)
    (by simp [innerCone]) (fun i => measurable_pi_apply i)
  let a : ({c - (t : ℤ)} : Finset ℤ) := ⟨c - t, by simp⟩
  exact h.comp (φ := fun v : ({c - (t : ℤ)} : Finset ℤ) → Bool => v a) (ψ := id)
    (measurable_pi_apply a) measurable_id

theorem leftCell_fair (c : ℤ) (t : ℕ) (b : Bool) :
    bernoulliRow ((fun x : Config => x (c - t)) ⁻¹' {b}) = 1 / 2 := by
  have h := Measure.infinitePi_map_eval (fun _ : ℤ => coin) (c - t)
  unfold bernoulliRow
  rw [← Measure.map_apply (by fun_prop) (measurableSet_singleton b), h]
  exact coin_singleton b

/-- **The basic half-lemma.** If a fair bit `ξ` is independent of `W`, then for every
measurable `g` the event `ξ = g(W)` has conditional probability `1/2` given any event about `W`. -/
theorem half_of_indep {Ω β : Type*} [MeasurableSpace Ω] [MeasurableSpace β] {μ : Measure Ω}
    (ξ : Ω → Bool) (W : Ω → β) (hξ : Measurable ξ) (hW : Measurable W)
    (hind : IndepFun ξ W μ) (hfair : ∀ b, μ (ξ ⁻¹' {b}) = 1 / 2)
    (g : β → Bool) (hg : Measurable g) (A : Set β) (hA : MeasurableSet A) :
    μ ({ω | ξ ω = g (W ω)} ∩ W ⁻¹' A) = 1 / 2 * μ (W ⁻¹' A) := by
  have hT : MeasurableSet (A ∩ g ⁻¹' {true}) := hA.inter (hg (measurableSet_singleton _))
  have hF : MeasurableSet (A ∩ g ⁻¹' {false}) := hA.inter (hg (measurableSet_singleton _))
  have hset : {ω | ξ ω = g (W ω)} ∩ W ⁻¹' A =
      (ξ ⁻¹' {true} ∩ W ⁻¹' (A ∩ g ⁻¹' {true})) ∪ (ξ ⁻¹' {false} ∩ W ⁻¹' (A ∩ g ⁻¹' {false})) := by
    ext ω
    simp only [Set.mem_inter_iff, Set.mem_setOf_eq, Set.mem_preimage, Set.mem_union,
      Set.mem_singleton_iff]
    cases h1 : ξ ω <;> cases h2 : g (W ω) <;> simp
  have hA' : W ⁻¹' A = W ⁻¹' (A ∩ g ⁻¹' {true}) ∪ W ⁻¹' (A ∩ g ⁻¹' {false}) := by
    ext ω
    simp only [Set.mem_preimage, Set.mem_union, Set.mem_inter_iff, Set.mem_singleton_iff]
    cases g (W ω) <;> simp
  rw [hset, measure_union, hind.measure_inter_preimage_eq_mul _ _ (measurableSet_singleton _) hT,
    hind.measure_inter_preimage_eq_mul _ _ (measurableSet_singleton _) hF, hfair, hfair, hA',
    measure_union, mul_add]
  · rw [Set.disjoint_left]
    intro ω h1 h2
    simp only [Set.mem_preimage, Set.mem_inter_iff, Set.mem_singleton_iff] at h1 h2
    rw [h1.2] at h2; exact Bool.noConfusion h2.2
  · exact hW hF
  · rw [Set.disjoint_left]
    intro ω h1 h2
    simp only [Set.mem_preimage, Set.mem_inter_iff, Set.mem_singleton_iff] at h1 h2
    rw [h1.1] at h2; exact Bool.noConfusion h2.1
  · exact (hξ (measurableSet_singleton _)).inter (hW hF)

/-! ## The column bit as "new coin xor old information" -/

theorem evolve_extW_eq (c : ℤ) (s t : ℕ) (hs : s < t) (x : Config) :
    evolve (extW (innerCone c t) (restr (innerCone c t) x)) s c = evolve x s c := by
  apply evolve_congr
  intro j h1 h2
  have : j ∈ innerCone c t := by simp [innerCone]; omega
  simp [extW, restr, this]

/-- **Cone separation as a coin flip.** `a(t)(c) = x_{c−t} xor a(t)(c)[x_{c−t} := 0]`, where the
second term only depends on the inner cone. -/
theorem evolve_eq_xor_inner (c : ℤ) (t : ℕ) (x : Config) :
    evolve x t c = xor (x (c - t)) (evolve (extW (innerCone c t) (restr (innerCone c t) x)) t c) := by
  set y := extW (innerCone c t) (restr (innerCone c t) x)
  have hy : y (c - t) = false := by simp [y, extW, innerCone]
  have hin : ∀ j, c - t < j → j ≤ c + t → y j = x j := by
    intro j h1 h2
    have : j ∈ innerCone c t := by simp [innerCone]; omega
    simp [y, extW, restr, this]
  cases hx : x (c - t)
  · simp only [Bool.false_xor]
    apply evolve_congr
    intro j h1 h2
    rcases eq_or_lt_of_le h1 with h | h
    · rw [← h, hx, hy]
    · exact (hin j h h2).symm
  · have := evolve_flip_left_edge y t c
    rw [Bool.true_xor, ← this]
    apply evolve_congr
    intro j h1 h2
    rcases eq_or_lt_of_le h1 with h | h
    · subst h; simp [flipAt, hx, hy]
    · simp only [flipAt]
      rw [Function.update_of_ne (by omega), hin j h h2]

/-- **One column step.** For any `h` and any event `A` about the inner cone,
`P(a(t)(c) = h(inner cone) and inner cone ∈ A) = ½ · P(inner cone ∈ A)`. -/
theorem col_step (c : ℤ) (t : ℕ) (h : (innerCone c t → Bool) → Bool) (A : Set (innerCone c t → Bool)) :
    bernoulliRow ({x | evolve x t c = h (restr (innerCone c t) x)} ∩ restr (innerCone c t) ⁻¹' A) =
      1 / 2 * bernoulliRow (restr (innerCone c t) ⁻¹' A) := by
  have key := half_of_indep (μ := bernoulliRow) (fun x : Config => x (c - t))
    (restr (innerCone c t)) (measurable_pi_apply _) (measurable_restr _)
    (leftCell_indep_innerCone c t) (leftCell_fair c t)
    (fun v => xor (h v) (evolve (extW (innerCone c t) v) t c)) (measurable_of_finite _) A
    (Set.toFinite A).measurableSet
  rw [← key]
  congr 1
  ext x
  simp only [Set.mem_inter_iff, Set.mem_setOf_eq]
  rw [evolve_eq_xor_inner c t x]
  cases x (c - t) <;> cases h (restr (innerCone c t) x) <;>
    cases evolve (extW (innerCone c t) (restr (innerCone c t) x)) t c <;> simp

/-- **Each column bit is a fair coin.** -/
theorem column_bit_fair (c : ℤ) (t : ℕ) (b : Bool) :
    bernoulliRow (colAt c t ⁻¹' {b}) = 1 / 2 := by
  have := col_step c t (fun _ => b) Set.univ
  simp only [Set.preimage_univ, Set.inter_univ, measure_univ, mul_one] at this
  exact this

theorem set_bool_cases (B : Set Bool) : B = ∅ ∨ B = {true} ∨ B = {false} ∨ B = Set.univ := by
  by_cases ht : true ∈ B <;> by_cases hf : false ∈ B
  · right; right; right; ext b; cases b <;> simp [ht, hf]
  · right; left; ext b; cases b <;> simp [ht, hf]
  · right; right; left; ext b; cases b <;> simp [ht, hf]
  · left; ext b; cases b <;> simp [ht, hf]

/-- A column bit is independent of every event about the inner cone. -/
theorem col_indep_step (c : ℤ) (t : ℕ) (B : Set Bool) (A : Set (innerCone c t → Bool)) :
    bernoulliRow (colAt c t ⁻¹' B ∩ restr (innerCone c t) ⁻¹' A) =
      bernoulliRow (colAt c t ⁻¹' B) * bernoulliRow (restr (innerCone c t) ⁻¹' A) := by
  rcases set_bool_cases B with rfl | rfl | rfl | rfl
  · simp
  · rw [column_bit_fair]; exact col_step c t (fun _ => true) A
  · rw [column_bit_fair]; exact col_step c t (fun _ => false) A
  · rw [Set.preimage_univ, Set.univ_inter, measure_univ, one_mul]

/-! ## The law of a column -/

/-- **The bits of every column are mutually independent** under the fair-coin row measure. -/
theorem column_iIndep (c : ℤ) : iIndepFun (fun t x => colAt c t x) bernoulliRow := by
  rw [iIndepFun_iff_measure_inter_preimage_eq_mul]
  intro S
  induction S using Finset.induction_on_max with
  | h0 => intro sets _; simp
  | step t S hlt ih =>
    intro sets _
    have htS : t ∉ S := fun h => lt_irrefl t (hlt t h)
    rw [Finset.prod_insert htS, Finset.set_biInter_insert]
    have hrep : (⋂ i ∈ S, colAt c i ⁻¹' sets i) = restr (innerCone c t) ⁻¹'
        {v | ∀ i ∈ S, evolve (extW (innerCone c t) v) i c ∈ sets i} := by
      ext x
      simp only [Set.mem_iInter, Set.mem_preimage, Set.mem_setOf_eq, colAt]
      constructor
      · intro hx i hi; rw [evolve_extW_eq c i t (hlt i hi)]; exact hx i hi
      · intro hx i hi; rw [← evolve_extW_eq c i t (hlt i hi)]; exact hx i hi
    rw [hrep, col_indep_step, ← hrep, ih (sets := sets) (fun _ _ => (Set.toFinite _).measurableSet)]

theorem coin_eq_map_colAt (c : ℤ) (t : ℕ) : bernoulliRow.map (colAt c t) = coin := by
  rw [Measure.ext_iff_singleton]
  intro b
  rw [Measure.map_apply (measurable_colAt c t) (measurableSet_singleton b), column_bit_fair,
    coin_singleton]

/-- **The law of a column is the fair-coin product measure.** For a random row, the column
`t ↦ a(t)(c)` is distributed exactly as an infinite sequence of independent fair coin flips. -/
theorem column_law (c : ℤ) :
    bernoulliRow.map (fun x t => evolve x t c) = Measure.infinitePi (fun _ : ℕ => coin) := by
  have h := (iIndepFun_iff_map_fun_eq_infinitePi_map (fun t => measurable_colAt c t)).1
    (column_iIndep c)
  simp only [coin_eq_map_colAt] at h
  exact h

/-- **Prefix law.** Every column word of length `n` has probability `2^{-n}`. -/
theorem column_prefix_law (c : ℤ) (n : ℕ) (w : ℕ → Bool) :
    bernoulliRow {x | ∀ t < n, evolve x t c = w t} = (1 / 2) ^ n := by
  have h := (column_iIndep c).measure_inter_preimage_eq_mul (Finset.range n)
    (sets := fun t => {w t}) (fun _ _ => measurableSet_singleton _)
  have hset : {x : Config | ∀ t < n, evolve x t c = w t} = ⋂ i ∈ Finset.range n, colAt c i ⁻¹' {w i} := by
    ext x; simp [colAt]
  rw [hset, h]
  simp [column_bit_fair]

/-! ## Problem 2 for almost every row -/

/-- **Problem 2 holds almost surely.** For almost every row (fair-coin product measure), the
frequency of black cells in column `c` tends to `1/2`. -/
theorem ae_column_frequency_half (c : ℤ) :
    ∀ᵐ x ∂bernoulliRow, HasFrequencyHalf (fun t => evolve x t c) := by
  let g : Bool → ℝ := fun b => if b then 1 else 0
  let X : ℕ → Config → ℝ := fun t x => g (colAt c t x)
  have hmeas : ∀ t, Measurable (X t) := fun t => (measurable_of_finite g).comp (measurable_colAt c t)
  have hint : Integrable (X 0) bernoulliRow := by
    refine (integrable_const (1 : ℝ)).mono' (hmeas 0).aestronglyMeasurable (ae_of_all _ ?_)
    intro x; simp only [X, g]; split_ifs <;> simp
  have hindep : Pairwise (fun i j => IndepFun (X i) (X j) bernoulliRow) := by
    intro i j hij
    exact ((column_iIndep c).indepFun hij).comp (measurable_of_finite g) (measurable_of_finite g)
  have hident : ∀ i, IdentDistrib (X i) (X 0) bernoulliRow bernoulliRow := by
    intro i
    have : IdentDistrib (colAt c i) (colAt c 0) bernoulliRow bernoulliRow :=
      ⟨(measurable_colAt c i).aemeasurable, (measurable_colAt c 0).aemeasurable,
        by rw [coin_eq_map_colAt, coin_eq_map_colAt]⟩
    exact this.comp (measurable_of_finite g)
  have hmean : bernoulliRow[X 0] = 1 / 2 := by
    have : ∫ x, X 0 x ∂bernoulliRow = ∫ b, g b ∂coin := by
      rw [← coin_eq_map_colAt c 0, integral_map (measurable_colAt c 0).aemeasurable
        (measurable_of_finite g).aestronglyMeasurable]
    rw [this, integral_fintype]
    · simp [g, Measure.real, coin_singleton]
    · exact Integrable.of_finite
  have hslln := strong_law_ae X hint hindep hident
  rw [hmean] at hslln
  filter_upwards [hslln] with x hx
  unfold HasFrequencyHalf freq
  refine hx.congr (fun n => ?_)
  have : ∑ i ∈ Finset.range n, X i x = (ones (fun t => evolve x t c) n : ℝ) := by
    simp only [X, g, colAt, ones]
    rw [Finset.sum_boole]
  rw [this, smul_eq_mul, div_eq_inv_mul]

/-! ## Problem 1 for almost every row -/

/-- `P(a(N+p+k)(c) = a(N+k)(c) for all k < m) = 2^{-m}` for `p ≥ 1`. -/
theorem periodic_window_prob (c : ℤ) (N p : ℕ) (hp : 0 < p) (m : ℕ) :
    bernoulliRow {x | ∀ k < m, evolve x (N + p + k) c = evolve x (N + k) c} = (1 / 2) ^ m := by
  induction m with
  | zero => simp
  | succ m ih =>
    set t := N + p + m
    have hrep : {x : Config | ∀ k < m, evolve x (N + p + k) c = evolve x (N + k) c} =
        restr (innerCone c t) ⁻¹' {v | ∀ k < m, evolve (extW (innerCone c t) v) (N + p + k) c =
          evolve (extW (innerCone c t) v) (N + k) c} := by
      ext x
      simp only [Set.mem_setOf_eq, Set.mem_preimage]
      constructor
      · intro hx k hk
        rw [evolve_extW_eq c _ t (by omega), evolve_extW_eq c _ t (by omega)]; exact hx k hk
      · intro hx k hk
        rw [← evolve_extW_eq c _ t (by omega), ← evolve_extW_eq c (N + k) t (by omega)]
        exact hx k hk
    have hset : {x : Config | ∀ k < m + 1, evolve x (N + p + k) c = evolve x (N + k) c} =
        {x | evolve x t c = (fun v => evolve (extW (innerCone c t) v) (N + m) c)
          (restr (innerCone c t) x)} ∩
        restr (innerCone c t) ⁻¹' {v | ∀ k < m, evolve (extW (innerCone c t) v) (N + p + k) c =
          evolve (extW (innerCone c t) v) (N + k) c} := by
      rw [← hrep]
      ext x
      simp only [Set.mem_setOf_eq, Set.mem_inter_iff]
      rw [evolve_extW_eq c (N + m) t (by omega)]
      constructor
      · intro hx; exact ⟨hx m (by omega), fun k hk => hx k (by omega)⟩
      · rintro ⟨h1, h2⟩ k hk
        rcases Nat.lt_succ_iff_lt_or_eq.mp hk with hk | rfl
        · exact h2 k hk
        · exact h1
    rw [hset, col_step c t (fun v => evolve (extW (innerCone c t) v) (N + m) c), ← hrep, ih,
      pow_succ, mul_comm]

/-- **Problem 1 holds almost surely.** For almost every row, column `c` is not eventually
periodic. -/
theorem ae_column_not_eventuallyPeriodic (c : ℤ) :
    ∀ᵐ x ∂bernoulliRow, ¬ EventuallyPeriodic (fun t => evolve x t c) := by
  rw [ae_iff]
  simp only [not_not]
  have hset : {x : Config | EventuallyPeriodic (fun t => evolve x t c)} ⊆
      ⋃ p : ℕ, ⋃ N : ℕ, {x | 0 < p ∧ ∀ n ≥ N, evolve x (n + p) c = evolve x n c} := by
    rintro x ⟨p, hp, N, hN⟩
    simp only [Set.mem_iUnion, Set.mem_setOf_eq]
    exact ⟨p, N, hp, hN⟩
  refine measure_mono_null hset (measure_iUnion_null fun p => measure_iUnion_null fun N => ?_)
  rcases Nat.eq_zero_or_pos p with rfl | hp
  · simp
  · have hle : ∀ m, bernoulliRow {x | 0 < p ∧ ∀ n ≥ N, evolve x (n + p) c = evolve x n c} ≤
        (1 / 2) ^ m := by
      intro m
      rw [← periodic_window_prob c N p hp m]
      apply measure_mono
      rintro x ⟨_, hx⟩ k _
      have := hx (N + k) (by omega)
      rwa [show N + k + p = N + p + k by ring] at this
    have hlim : Tendsto (fun m : ℕ => ((1 : ENNReal) / 2) ^ m) atTop (𝓝 0) :=
      ENNReal.tendsto_pow_atTop_nhds_zero_of_lt_one (by norm_num)
    exact le_antisymm (ge_of_tendsto' hlim hle) (zero_le _)

/-- Packaged: for almost every row, every column satisfies both Problem 1 and Problem 2. -/
theorem ae_problems_one_and_two :
    ∀ᵐ x ∂bernoulliRow, ∀ c : ℤ,
      ¬ EventuallyPeriodic (fun t => evolve x t c) ∧ HasFrequencyHalf (fun t => evolve x t c) := by
  rw [ae_all_iff]
  intro c
  filter_upwards [ae_column_not_eventuallyPeriodic c, ae_column_frequency_half c] with x h1 h2
  exact ⟨h1, h2⟩

end GLM.Rule30
