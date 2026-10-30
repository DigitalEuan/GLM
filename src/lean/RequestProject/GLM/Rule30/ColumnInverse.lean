module

public import RequestProject.GLM.Rule30.Ergodic
public import RequestProject.GLM.Rule30.Prizes

/-!
# The column inverse: where measure theory stops and the seed begins

Cone separation makes the map "row ↦ centre column" a triangular bijection once the right half
of the row is fixed:

* `column_inverse_exists` : for **any** right half `z` (cells `> 0`) and **any** target sequence
  `s : ℕ → Bool`, there is a row agreeing with `z` on the right half whose centre column is
  exactly `s`.
* `column_inverse_unique` : that row is unique.

Consequences:

* `seed_unique_preimage` : the seed is the *only* row that is white on the right and has
  Rule 30's centre column. The prize problems are therefore statements about one specific
  point `Φ⁻¹(a)` of a bijection `Φ`, where `a` is the centre column.
* `exists_row_with_periodic_column`, `exists_row_with_biased_column` : every behaviour occurs,
  including periodic columns and columns with frequency `0`, for rows with any prescribed right
  half (white, like the seed's).
* `bernoulliRow_singleton_null`, `bernoulliRow_seed_null` : every single row, the seed
  included, has probability `0`.
* `measure_theory_boundary` : packaged statement of the boundary. Problems 1 and 2 hold for
  almost every row (`Ergodic.lean`), the seed is a null point, and the exceptional set meets
  every right half. So no argument that only uses "almost every row" can reach the seed.
  What is missing is a reason why the seed is *generic*.
-/

@[expose] public section

namespace GLM.Rule30

open MeasureTheory Filter Topology

/-- Rows agree on the right half `(0, ∞)`. -/
def SameRight (x z : Config) : Prop := ∀ i, 0 < i → x i = z i

/-- Approximations to the column inverse: fix cell `-t` at stage `t`. -/
def invApprox (z : Config) (s : ℕ → Bool) : ℕ → Config
  | 0 => fun i => if 0 < i then z i else if i = 0 then s 0 else false
  | t + 1 =>
    if evolve (invApprox z s t) (t + 1) 0 = s (t + 1) then invApprox z s t
    else flipAt (invApprox z s t) (0 - ((t + 1 : ℕ) : ℤ))

theorem invApprox_succ_eq (z : Config) (s : ℕ → Bool) (t : ℕ) (i : ℤ) (hi : i ≠ -((t + 1 : ℕ) : ℤ)) :
    invApprox z s (t + 1) i = invApprox z s t i := by
  simp only [invApprox]
  split_ifs
  · rfl
  · simp only [flipAt]; rw [Function.update_of_ne (by omega)]

theorem invApprox_stable (z : Config) (s : ℕ → Bool) (t : ℕ) :
    ∀ m, ∀ i, -(t : ℤ) ≤ i → invApprox z s (t + m) i = invApprox z s t i := by
  intro m
  induction m with
  | zero => intro i _; rfl
  | succ m ih =>
    intro i hi
    rw [← Nat.add_assoc, invApprox_succ_eq z s (t + m) i (by push_cast; omega), ih i hi]

theorem invApprox_column (z : Config) (s : ℕ → Bool) (t : ℕ) :
    evolve (invApprox z s t) t 0 = s t := by
  cases t with
  | zero => simp [invApprox]
  | succ t =>
    simp only [invApprox]
    split_ifs with h
    · exact h
    · rw [evolve_flip_left_edge]
      revert h; cases evolve (invApprox z s t) (t + 1) 0 <;> cases s (t + 1) <;> simp

theorem invApprox_right (z : Config) (s : ℕ → Bool) (t : ℕ) (i : ℤ) (hi : 0 < i) :
    invApprox z s t i = z i := by
  have := invApprox_stable z s 0 t i (by omega)
  simp only [Nat.zero_add] at this
  rw [this]; simp [invApprox, hi]

/-- **Column inverse, existence.** For every right half `z` and every sequence `s` there is a row
with right half `z` whose centre column is `s`. -/
theorem column_inverse_exists (z : Config) (s : ℕ → Bool) :
    ∃ x : Config, SameRight x z ∧ ∀ t, evolve x t 0 = s t := by
  refine ⟨fun i => invApprox z s i.natAbs i, fun i hi => invApprox_right z s _ i hi, fun t => ?_⟩
  rw [← invApprox_column z s t]
  apply evolve_congr
  intro j h1 h2
  simp only [zero_sub, zero_add] at h1 h2
  have hj : j.natAbs ≤ t := by omega
  obtain ⟨m, hm⟩ := Nat.exists_eq_add_of_le hj
  rw [hm, invApprox_stable z s j.natAbs m j (by omega)]

/-- **Column inverse, uniqueness.** Two rows with the same right half and the same centre column
are equal. -/
theorem column_inverse_unique (x y : Config) (hx : ∀ i, 0 < i → x i = y i)
    (hcol : ∀ t, evolve x t 0 = evolve y t 0) : x = y := by
  have key : ∀ t : ℕ, x (-(t : ℤ)) = y (-(t : ℤ)) := by
    intro t
    induction t using Nat.strong_induction_on with
    | _ t ih =>
      have hin : extW (innerCone 0 t) (restr (innerCone 0 t) x) =
          extW (innerCone 0 t) (restr (innerCone 0 t) y) := by
        funext i
        simp only [extW, restr]
        split_ifs with h
        · simp only [innerCone, Finset.mem_Ioc] at h
          rcases lt_or_ge 0 i with hi | hi
          · exact hx i hi
          · have := ih i.natAbs (by omega)
            rwa [show -(i.natAbs : ℤ) = i by omega] at this
        · rfl
      have h1 := evolve_eq_xor_inner 0 t x
      have h2 := evolve_eq_xor_inner 0 t y
      rw [hin, hcol t, h2] at h1
      simp only [zero_sub] at h1
      revert h1
      cases x (-(t : ℤ)) <;> cases y (-(t : ℤ)) <;>
        cases evolve (extW (innerCone 0 t) (restr (innerCone 0 t) y)) t 0 <;> simp
  funext i
  rcases lt_or_ge 0 i with hi | hi
  · exact hx i hi
  · have := key i.natAbs
    rwa [show -(i.natAbs : ℤ) = i by omega] at this

/-- **The seed is the unique preimage.** Among rows that are white on `(0, ∞)`, the seed is the only
one whose centre column is Rule 30's centre column. -/
theorem seed_unique_preimage (x : Config) (hx : ∀ i, 0 < i → x i = false)
    (hcol : ∀ t, evolve x t 0 = centerCol t) : x = seed :=
  column_inverse_unique x seed (fun i hi => by rw [hx i hi]; simp [seed]; omega) hcol

/-- Every behaviour occurs: some row that is white on the right, like the seed, has an eventually
periodic centre column different from the all-white one (here: `1, 0, 1, 0, …`). -/
theorem exists_row_with_periodic_column :
    ∃ x : Config, (∀ i, 0 < i → x i = false) ∧ (∀ t, evolve x t 0 = decide (t % 2 = 0)) ∧
      EventuallyPeriodic (fun t => evolve x t 0) := by
  obtain ⟨x, hx, hcol⟩ := column_inverse_exists (fun _ => false) (fun t => decide (t % 2 = 0))
  refine ⟨x, hx, hcol, 2, by norm_num, 0, fun n _ => ?_⟩
  show evolve x (n + 2) 0 = evolve x n 0
  rw [hcol, hcol]; simp [Nat.add_mod_right]

/-- Some row that is white on the right has a column with frequency `1/3`, so Problem 2 fails for it. -/
theorem exists_row_with_biased_column :
    ∃ x : Config, (∀ i, 0 < i → x i = false) ∧ (∀ t, evolve x t 0 = decide (t % 3 = 0)) ∧
      ¬ HasFrequencyHalf (fun t => evolve x t 0) := by
  obtain ⟨x, hx, hcol⟩ := column_inverse_exists (fun _ => false) (fun t => decide (t % 3 = 0))
  refine ⟨x, hx, hcol, fun hfreq => ?_⟩
  have hfun : (fun t => evolve x t 0) = (fun t => decide (t % 3 = 0)) := funext hcol
  rw [hfun] at hfreq
  -- along `n = 3k` the frequency is exactly `1/3`
  have hones : ∀ k, ones (fun t => decide (t % 3 = 0)) (3 * k) = k := by
    intro k
    induction k with
    | zero => rfl
    | succ k ih =>
      rw [show 3 * (k + 1) = 3 * k + 1 + 1 + 1 by ring, ones_succ, ones_succ, ones_succ, ih]
      simp only [decide_eq_true_eq]
      rw [if_pos (by omega), if_neg (by omega), if_neg (by omega)]
  have hsub : Tendsto (fun k : ℕ => freq (fun t => decide (t % 3 = 0)) (3 * (k + 1))) atTop
      (𝓝 (1 / 2)) :=
    hfreq.comp (tendsto_id.const_mul_atTop' (by norm_num) |>.comp (tendsto_add_atTop_nat 1))
  have hconst : ∀ k : ℕ, freq (fun t => decide (t % 3 = 0)) (3 * (k + 1)) = 1 / 3 := by
    intro k
    unfold freq
    rw [hones]
    push_cast
    field_simp
  simp only [hconst, tendsto_const_nhds_iff] at hsub
  norm_num at hsub

/-- Every single row has probability `0` under the fair-coin row measure. -/
theorem bernoulliRow_singleton_null (y : Config) : bernoulliRow {y} = 0 := by
  have hle : ∀ n, bernoulliRow {y} ≤ (1 / 2) ^ n := by
    intro n
    rw [← column_prefix_law 0 n (fun t => evolve y t 0)]
    apply measure_mono
    intro x hx
    rw [Set.mem_singleton_iff] at hx
    subst hx
    intro t _; rfl
  have hlim : Tendsto (fun m : ℕ => ((1 : ENNReal) / 2) ^ m) atTop (𝓝 0) :=
    ENNReal.tendsto_pow_atTop_nhds_zero_of_lt_one (by norm_num)
  exact le_antisymm (ge_of_tendsto' hlim hle) (zero_le _)

/-- The seed is a null point. -/
theorem bernoulliRow_seed_null : bernoulliRow {seed} = 0 := bernoulliRow_singleton_null seed

/-- **The boundary of the measure-theoretic method.**
1. For almost every row, every column satisfies Problems 1 and 2.
2. The seed has probability zero.
3. For every right half, in particular the seed's white one, some row with that right half has
   an eventually periodic centre column, and some has a centre column with frequency `1/3`.
4. The seed is the unique row that is white on the right and has Rule 30's centre column.
So "almost every row" cannot be specialised to the seed. A proof of Problems 1 and 2 has to show
that the seed is generic, using properties of the seed itself. -/
theorem measure_theory_boundary :
    (∀ᵐ x ∂bernoulliRow, ∀ c : ℤ,
      ¬ EventuallyPeriodic (fun t => evolve x t c) ∧ HasFrequencyHalf (fun t => evolve x t c)) ∧
    bernoulliRow {seed} = 0 ∧
    (∀ z : Config, ∃ x, SameRight x z ∧ EventuallyPeriodic (fun t => evolve x t 0)) ∧
    (∀ z : Config, ∃ x, SameRight x z ∧ ¬ HasFrequencyHalf (fun t => evolve x t 0)) ∧
    (∀ x : Config, (∀ i, 0 < i → x i = false) → (∀ t, evolve x t 0 = centerCol t) → x = seed) := by
  refine ⟨ae_problems_one_and_two, bernoulliRow_seed_null, fun z => ?_, fun z => ?_,
    seed_unique_preimage⟩
  · obtain ⟨x, hx, hcol⟩ := column_inverse_exists z (fun _ => false)
    exact ⟨x, hx, 1, one_pos, 0, fun n _ => by
      show evolve x (n + 1) 0 = evolve x n 0
      rw [hcol, hcol]⟩
  · obtain ⟨x, hx, hcol⟩ := column_inverse_exists z (fun _ => false)
    refine ⟨x, hx, fun hfreq => ?_⟩
    have hfun : (fun t => evolve x t 0) = (fun _ => false) := funext hcol
    rw [hfun] at hfreq
    have hzero : ∀ n, freq (fun _ : ℕ => false) n = 0 := by
      intro n; simp [freq, ones]
    have hf : freq (fun _ : ℕ => false) = fun _ => 0 := funext hzero
    unfold HasFrequencyHalf at hfreq
    rw [hf] at hfreq
    have := tendsto_nhds_unique tendsto_const_nhds hfreq
    norm_num at this

end GLM.Rule30
