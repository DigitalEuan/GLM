/-
# The tower does not stop

`Stack.lean` builds a finite stack and proves that above its top layer there is
nothing left to lose.  That is the *terminating* case, and it is the exception.
This file proves the other half of the thesis — the part that says

> this continues, I think

— by exhibiting an infinite tower of strictly increasing resolutions on the
same carrier type.

The `n`-th **dyadic layer** sees a rational to resolution `2⁻ⁿ`: it perceives
`q` as `⌊q · 2ⁿ⌋`.  Three theorems then say everything.

* `dyadic_refines_succ` — each layer refines the one below: nothing expressible
  at a coarse resolution is lost when the resolution is doubled.  The tower is
  cumulative.
* `dyadic_boundary_nonempty` — **every** step has a non-empty boundary, so by
  `boundary_nonempty_iff_new_visible` every step adds genuinely new expressive
  power.  No layer is the last one; the ascent never runs out of work.
* `dyadic_separates` — and yet the tower is not idle repetition: any two
  distinct carriers are eventually told apart, at a computable level.

Together: an unbounded, strictly increasing, cumulative ladder of layers, each
true at its own resolution, each superseded, and none of them final.  This is
the "dimension capacity continues" half of the study, in the same vocabulary as
the rest of it.
-/
import RequestProject.GLM.Stack

namespace GLM.Info

open Layer

/-! ## The dyadic tower -/

/-- Layer `n` of the dyadic tower: a rational is seen to resolution `2⁻ⁿ`.
Layer `0` is exactly the integer layer of the GLM stack. -/
def dyadicLayer (n : ℕ) : Layer ℚ where
  View := ℤ
  perceive q := ⌊q * 2 ^ n⌋

@[simp] lemma dyadicLayer_perceive (n : ℕ) (q : ℚ) :
    (dyadicLayer n).perceive q = ⌊q * 2 ^ n⌋ := rfl

/-- The bottom of the tower is the GLM's integer layer. -/
theorem dyadicLayer_zero : dyadicLayer 0 = integerLayer := by
  have : (fun q : ℚ => ⌊q * 2 ^ (0:ℕ)⌋) = fun q : ℚ => ⌊q⌋ := by
    funext q; norm_num
  simp only [dyadicLayer, integerLayer, this]

/-- Halving the resolution is dividing the view by two. -/
lemma floor_mul_two_pow_succ (q : ℚ) (n : ℕ) :
    ⌊q * 2 ^ n⌋ = ⌊q * 2 ^ (n + 1)⌋ / ((2 : ℕ) : ℤ) := by
  rw [← Int.floor_div_natCast (q * 2 ^ (n + 1)) 2]
  congr 1
  push_cast
  ring

/-- **The tower is cumulative.**  Each layer refines the one below it, so by
`Visible.mono` every proposition expressible at resolution `2⁻ⁿ` stays
expressible at every finer resolution. -/
theorem dyadic_refines_succ (n : ℕ) :
    Refines (dyadicLayer (n + 1)) (dyadicLayer n) := by
  intro a b hab
  show ⌊a * 2 ^ n⌋ = ⌊b * 2 ^ n⌋
  rw [floor_mul_two_pow_succ a n, floor_mul_two_pow_succ b n]
  exact congrArg (· / ((2 : ℕ) : ℤ)) hab

/-- Refinement all the way up the tower, not just one step at a time. -/
theorem dyadic_refines_of_le {m n : ℕ} (h : m ≤ n) :
    Refines (dyadicLayer n) (dyadicLayer m) := by
  induction n with
  | zero =>
      have : m = 0 := Nat.le_zero.1 h
      subst this
      exact refines_refl _
  | succ k ih =>
      rcases Nat.lt_or_ge m (k + 1) with hm | hm
      · exact Refines.trans (dyadic_refines_succ k) (ih (Nat.lt_succ_iff.1 hm))
      · have : m = k + 1 := le_antisymm h hm
        subst this
        exact refines_refl _

/-- The witness pair at level `n`: the two carriers that level `n` conflates and
level `n + 1` splits. -/
lemma dyadic_witness (n : ℕ) :
    ⌊(0 : ℚ) * 2 ^ n⌋ = ⌊((2 : ℚ) ^ (n + 1))⁻¹ * 2 ^ n⌋ ∧
      ⌊(0 : ℚ) * 2 ^ (n + 1)⌋ ≠ ⌊((2 : ℚ) ^ (n + 1))⁻¹ * 2 ^ (n + 1)⌋ := by
  have hne : ((2 : ℚ) ^ (n + 1)) ≠ 0 := by positivity
  have hhalf : ((2 : ℚ) ^ (n + 1))⁻¹ * 2 ^ n = 1 / 2 := by
    field_simp
    ring
  have hone : ((2 : ℚ) ^ (n + 1))⁻¹ * 2 ^ (n + 1) = 1 := by
    field_simp
  refine ⟨?_, ?_⟩
  · rw [hhalf, zero_mul, Int.floor_zero, floor_half]
  · rw [hone, zero_mul, Int.floor_zero, Int.floor_one]
    exact zero_ne_one

/-- **No layer is the last one.**  Every step of the tower has a non-empty
boundary, so by `boundary_nonempty_iff_new_visible` every step adds a
proposition the layer below cannot state.  The ascent continues without end. -/
theorem dyadic_boundary_nonempty (n : ℕ) :
    (Boundary (dyadicLayer (n + 1)) (dyadicLayer n)).Nonempty := by
  obtain ⟨hsame, hdiff⟩ := dyadic_witness n
  exact ⟨(0, ((2 : ℚ) ^ (n + 1))⁻¹), hsame, hdiff⟩

/-- Restated in the form the study uses: each step is a strict gain in
expressive power. -/
theorem dyadic_new_visible (n : ℕ) :
    ∃ P : ℚ → Prop, Visible (dyadicLayer (n + 1)) P ∧ ¬ Visible (dyadicLayer n) P :=
  (boundary_nonempty_iff_new_visible (dyadic_refines_succ n)).1
    (dyadic_boundary_nonempty n)

/-- No layer of the tower is lossless: each one still conflates something. -/
theorem dyadic_not_lossless (n : ℕ) : ¬ (dyadicLayer n).Lossless := by
  intro h
  obtain ⟨hsame, hdiff⟩ := dyadic_witness n
  exact hdiff (congrArg (fun q : ℚ => ⌊q * 2 ^ (n + 1)⌋) (h hsame))

/-! ## The tower is exhaustive as well as unbounded -/

/-- **Every distinction is eventually made.**  Distinct carriers are told apart
at some finite level, so the tower loses nothing permanently: the ascent is
unbounded but not futile. -/
theorem dyadic_separates {q r : ℚ} (h : q ≠ r) :
    ∃ n : ℕ, ¬ (dyadicLayer n).Indist q r := by
  -- Work with the smaller carrier first; the statement is symmetric.
  rcases lt_or_gt_of_ne h with hlt | hlt
  · exact dyadic_separates_of_lt hlt
  · obtain ⟨n, hn⟩ := dyadic_separates_of_lt hlt
    exact ⟨n, fun hc => hn (indist_symm hc)⟩
where
  /-- The strict-inequality case: pick a resolution finer than the gap. -/
  dyadic_separates_of_lt {q r : ℚ} (h : q < r) :
      ∃ n : ℕ, ¬ (dyadicLayer n).Indist q r := by
    obtain ⟨n, hn⟩ : ∃ n : ℕ, (r - q)⁻¹ < 2 ^ n := pow_unbounded_of_one_lt _ (by norm_num)
    refine ⟨n, ?_⟩
    have hpos : (0 : ℚ) < r - q := sub_pos.mpr h
    have h2 : (0 : ℚ) < 2 ^ n := by positivity
    have key : q * 2 ^ n + 1 ≤ r * 2 ^ n := by
      have hgap : 1 < (r - q) * 2 ^ n := by
        rw [inv_lt_iff_one_lt_mul₀ hpos] at hn
        linarith
      nlinarith
    have hfloor : ⌊q * 2 ^ n + 1⌋ ≤ ⌊r * 2 ^ n⌋ := Int.floor_le_floor key
    rw [Int.floor_add_one] at hfloor
    show ¬ (⌊q * 2 ^ n⌋ = ⌊r * 2 ^ n⌋)
    omega

end GLM.Info
