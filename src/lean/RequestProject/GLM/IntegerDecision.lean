module

public import Mathlib

/-!
# The integer decision, completed (Phase 79)

`studies/INTEGER_DECISION_STUDY.md`, mark Z6. The facts the Omega test relies
on when it decides a linear system over `ℤ` in
`glm_universal.reasoning.integer_decision`:

* `exact_shadow` — with an upper coefficient of one, the integer shadow is the
  real shadow;
* `dark_shadow_gap` — the dark-shadow row guarantees an integer between a lower
  bound `β ≤ b·z` and an upper bound `a·z ≤ α`;
* `splinter_count` and `splinter_tail` — an integer point outside every
  splinter satisfies the dark-shadow row, so the dark shadow together with the
  splinters covers every integer point;
* `split_cover` — the split of a row `s ≤ 0` into `s = 0, …, s = −K` and
  `s ≤ −K − 1` misses no integer;
* `substitution_bijective` — replacing a variable by itself plus an integer
  affine form in the others is a bijection of the integer points, so a
  refutation after the substitution is a refutation before it.
-/

@[expose] public section

namespace GLM.IntegerDecision

/-- With upper coefficient one, an integer `z` with `β ≤ b·z` and `z ≤ α`
exists exactly when the real shadow `β ≤ b·α` holds. -/
theorem exact_shadow (b α β : ℤ) (hb : 0 < b) :
    (∃ z : ℤ, β ≤ b * z ∧ z ≤ α) ↔ β ≤ b * α := by
  constructor
  · rintro ⟨z, h1, h2⟩
    nlinarith
  · intro h
    exact ⟨α, h, le_rfl⟩

/-- The dark shadow is sound: the row `a·β + (a−1)(b−1) ≤ b·α` guarantees an
integer `z` with `β ≤ b·z` and `a·z ≤ α`. -/
theorem dark_shadow_gap (a b α β : ℤ) (ha : 0 < a) (hb : 0 < b)
    (h : a * β + (a - 1) * (b - 1) ≤ b * α) :
    ∃ z : ℤ, β ≤ b * z ∧ a * z ≤ α := by
  refine ⟨-((-β) / b), ?_, ?_⟩
  · have h1 := Int.emod_add_mul_ediv (-β) b
    have h2 := Int.emod_nonneg (-β) hb.ne'
    nlinarith
  · have h1 := Int.emod_add_mul_ediv (-β) b
    have h3 := Int.emod_lt_of_pos (-β) hb
    have key : b * (a * (-((-β) / b))) < b * (α + 1) := by nlinarith
    have := lt_of_mul_lt_mul_left key hb.le
    omega

/-- The splinter count `K = ⌊(m·b − m − b)/m⌋` satisfies
`m·b − m − b < m·(K + 1)`. -/
theorem splinter_count (m b : ℤ) (hm : 0 < m) :
    m * b - m - b < m * ((m * b - m - b) / m + 1) := by
  have h1 := Int.emod_add_mul_ediv (m * b - m - b) m
  have h3 := Int.emod_lt_of_pos (m * b - m - b) hm
  nlinarith

/-- Outside the splinters the dark shadow holds: if `b·z ≥ β + k` with
`m·b − m − b < m·k`, and `a·z ≤ α` with `a ≤ m`, then the dark-shadow row
`a·β + (a−1)(b−1) ≤ b·α` holds. -/
theorem splinter_tail (a b m α β z k : ℤ) (ha : 0 < a) (hb : 0 < b)
    (ham : a ≤ m) (hk : m * b - m - b < m * k) (hlow : β + k ≤ b * z)
    (hup : a * z ≤ α) :
    a * β + (a - 1) * (b - 1) ≤ b * α := by
  have hak : a * b - a - b < a * k := by
    rcases le_or_gt 0 (k - b + 1) with h | h
    · nlinarith
    · nlinarith
  nlinarith

/-- The split of a row `s ≤ 0` at count `K` covers every integer the row
allows: `s` is one of `0, −1, …, −K`, or `s ≤ −K − 1`. -/
theorem split_cover (s : ℤ) (K : ℕ) (hs : s ≤ 0) :
    (∃ i : ℕ, i ≤ K ∧ s = -(i : ℤ)) ∨ s ≤ -(K : ℤ) - 1 := by
  by_cases h : s ≤ -(K : ℤ) - 1
  · exact Or.inr h
  · left
    refine ⟨(-s).toNat, ?_, ?_⟩ <;> omega

/-- Replacing coordinate `k` by itself plus an integer affine form in the
other coordinates is a bijection of `ℤ`-points. -/
theorem substitution_bijective {ι : Type*} [Fintype ι] [DecidableEq ι] (k : ι)
    (q : ι → ℤ) (hq : q k = 0) (q0 : ℤ) :
    Function.Bijective
      (fun x : ι → ℤ => Function.update x k (x k + ∑ i, q i * x i + q0)) := by
  have hsum : ∀ (x : ι → ℤ) (c : ℤ),
      ∑ i, q i * Function.update x k c i = ∑ i, q i * x i := by
    intro x c
    refine Finset.sum_congr rfl fun i _ => ?_
    by_cases h : i = k
    · subst h
      simp [hq]
    · simp [Function.update_of_ne h]
  refine Function.bijective_iff_has_inverse.mpr
    ⟨fun y => Function.update y k (y k - ∑ i, q i * y i - q0), ?_, ?_⟩
  · intro x
    simp only
    rw [hsum]
    ext i
    by_cases h : i = k
    · subst h
      simp only [Function.update_self]
      ring
    · simp [Function.update_of_ne h]
  · intro y
    simp only
    rw [hsum]
    ext i
    by_cases h : i = k
    · subst h
      simp only [Function.update_self]
      ring
    · simp [Function.update_of_ne h]

/-- Pugh's parallelogram has no integer point (a check of the example the
study opens with, by exhaustion of the enclosing box). -/
theorem pugh_no_integer_point :
    ∀ x ∈ Finset.Icc (-5 : ℤ) 5, ∀ y ∈ Finset.Icc (-5 : ℤ) 5,
      ¬ (27 ≤ 11 * x + 13 * y ∧ 11 * x + 13 * y ≤ 45 ∧
         -10 ≤ 7 * x - 9 * y ∧ 7 * x - 9 * y ≤ 4) := by
  decide

/-- Pugh's parallelogram lies inside the box `[−5, 5]²`, so the check above is
the whole of it. -/
theorem pugh_in_box (x y : ℤ) (h1 : 27 ≤ 11 * x + 13 * y) (h2 : 11 * x + 13 * y ≤ 45)
    (h3 : -10 ≤ 7 * x - 9 * y) (h4 : 7 * x - 9 * y ≤ 4) :
    x ∈ Finset.Icc (-5 : ℤ) 5 ∧ y ∈ Finset.Icc (-5 : ℤ) 5 := by
  simp only [Finset.mem_Icc]
  omega

end GLM.IntegerDecision
