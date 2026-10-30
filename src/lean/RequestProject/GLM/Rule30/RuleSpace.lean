module

public import RequestProject.GLM.Rule30.FiniteState
public import RequestProject.GLM.Rule30.ColumnInverse

/-!
# Rule spaces: "randomness" as escape from a declared class of rules

Round 6 formalises the working stance of this study: *randomness is not a thing in itself, only
rules not yet discovered*.  A sequence is never "random" absolutely; it can only **escape** a
declared space of rules (predictors).  All results are proved.

* `RuleSpace` : a set of causal predictors (rules that guess bit `t` from bits `< t`).
* `Escapes R a` : no rule of `R` is eventually always right on `a`.
* `TypicalFor R a` : every rule of `R` is right on `a` exactly half the time (asymptotically).
* `not_escapes_allRules` : **every sequence is captured by some rule.** For each `a` there is a
  causal rule that is right at every step.  So "random relative to all rules" is empty, which is
  the formal content of "randomness is undiscovered rule space": randomness only makes sense
  *relative to a declared rule space*.
* `centerCol_captured` : in particular the centre column is captured by the Rule 30 rule itself.
* `escapes_mono`, `escapes_of_typicalFor` : smaller spaces are easier to escape; typicality implies
  escape.
* **The prize problems as escape statements:**
  - `problem1_iff_escapes_lag` : Problem 1 ⟺ the centre column escapes the *lag rules*
    ("bit `t` repeats bit `t−p`").
  - `problem1_iff_escapes_fs` : Problem 1 ⟺ it escapes all *finite-state rules*.
  - `escapes_lag_iff_escapes_fs` : for every sequence, escaping the lag rules is equivalent to
    escaping all finite-state rules (for *exact* eventual prediction, finite memory gives nothing
    beyond "repeat with lag `p`").
  - `problem2_iff_typical_const` : Problem 2 ⟺ the centre column is typical for the one-rule space
    {"always black"}.
  - `seedFSTypical_iff` : the Seed Typicality target is typicality for the finite-state space.
* `exists_rightWhite_row_captured_by_lag` : escape is **seed-specific**: there are right-white rows
  (same diagonal structure as the seed) whose centre column is captured by a lag-2 rule.

The ladder for the GLM is therefore: lag rules ⊂ finite-state rules ⊂ counter rules (the wobble
arrow) ⊂ all computable rules.  P1 is escape from the first rung (equivalently the second), P2 is
typicality for the single constant rule, `SeedFSTypical` is typicality for the second rung, and
escape from the top rung is impossible for any sequence.
-/

@[expose] public section

namespace GLM.Rule30

open Filter

/-- A rule space: a set of predictors. -/
abbrev RuleSpace := Set (ℕ → (ℕ → Bool) → Bool)

/-- `a` escapes `R`: no rule in `R` is eventually always right on `a`. -/
def Escapes (R : RuleSpace) (a : ℕ → Bool) : Prop := ∀ pred ∈ R, ¬ EventuallyAlwaysRight pred a

/-- The hit sequence of a rule on `a`. -/
def hitsOf (pred : ℕ → (ℕ → Bool) → Bool) (a : ℕ → Bool) (t : ℕ) : Bool := decide (a t = pred t a)

/-- `a` is typical for `R`: every rule of `R` hits `a` with asymptotic frequency `1/2`. -/
def TypicalFor (R : RuleSpace) (a : ℕ → Bool) : Prop := ∀ pred ∈ R, HasFrequencyHalf (hitsOf pred a)

/-- All causal rules. -/
def allRules : RuleSpace := {pred | IsCausal pred}

/-- The lag rules `t ↦ a(t − p)`, `p ≥ 1`. -/
def lagRules : RuleSpace := {pred | ∃ p, 0 < p ∧ pred = lagPredictor p}

/-- The finite-state rules. -/
def fsRules : RuleSpace := {pred | ∃ n, ∃ O : FSObserver (Fin n), pred = O.predict}

theorem escapes_mono {R R' : RuleSpace} (h : R ⊆ R') {a : ℕ → Bool} (ha : Escapes R' a) :
    Escapes R a := fun pred hp => ha pred (h hp)

/-- Typicality implies escape. -/
theorem escapes_of_typicalFor {R : RuleSpace} {a : ℕ → Bool} (h : TypicalFor R a) : Escapes R a := by
  rintro pred hp ⟨N, hN⟩
  refine not_hasFrequencyHalf_of_eventually_true _ N (fun t ht => ?_) (h pred hp)
  simp [hitsOf, hN t ht]

/-- **Every sequence is captured by some rule.** -/
theorem not_escapes_allRules (a : ℕ → Bool) : ¬ Escapes allRules a :=
  fun h => h (fun t _ => a t) (fun _ _ _ _ => rfl) ⟨0, fun _ _ => rfl⟩

/-- The centre column is captured by the Rule 30 rule itself. -/
theorem centerCol_captured :
    (fun t (_ : ℕ → Bool) => centerCol t) ∈ allRules ∧
      EventuallyAlwaysRight (fun t _ => centerCol t) centerCol :=
  ⟨fun _ _ _ _ => rfl, 0, fun _ _ => rfl⟩

/-- A sequence is eventually periodic iff some lag rule is eventually always right on it. -/
theorem eventuallyPeriodic_iff_lag (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ ∃ p, 0 < p ∧ EventuallyAlwaysRight (lagPredictor p) a := by
  constructor
  · rintro ⟨p, hp, N, hN⟩
    refine ⟨p, hp, N + p, fun t ht => ?_⟩
    simp only [lagPredictor, if_pos (show p ≤ t by omega)]
    have := hN (t - p) (by omega)
    rw [show t - p + p = t by omega] at this
    exact this.symm
  · rintro ⟨p, hp, N, hN⟩
    refine ⟨p, hp, N, fun n hn => ?_⟩
    have := hN (n + p) (by omega)
    simp only [lagPredictor, if_pos (show p ≤ n + p by omega), Nat.add_sub_cancel] at this
    exact this.symm

theorem escapes_lag_iff (a : ℕ → Bool) : Escapes lagRules a ↔ ¬ EventuallyPeriodic a := by
  rw [eventuallyPeriodic_iff_lag]
  constructor
  · rintro h ⟨p, hp, hr⟩
    exact h _ ⟨p, hp, rfl⟩ hr
  · rintro h pred ⟨p, hp, rfl⟩ hr
    exact h ⟨p, hp, hr⟩

theorem escapes_fs_iff (a : ℕ → Bool) : Escapes fsRules a ↔ ¬ EventuallyPeriodic a := by
  rw [eventuallyPeriodic_iff_exists_fsObserver]
  constructor
  · rintro h ⟨n, O, hr⟩
    exact h _ ⟨n, O, rfl⟩ hr
  · rintro h pred ⟨n, O, rfl⟩ hr
    exact h ⟨n, O, hr⟩

/-- **For exact eventual prediction, finite memory gives nothing beyond lag rules.** -/
theorem escapes_lag_iff_escapes_fs (a : ℕ → Bool) : Escapes lagRules a ↔ Escapes fsRules a := by
  rw [escapes_lag_iff, escapes_fs_iff]

/-- **Problem 1 ⟺ the centre column escapes the lag rules.** -/
theorem problem1_iff_escapes_lag : Problem1 ↔ Escapes lagRules centerCol :=
  (escapes_lag_iff centerCol).symm

/-- **Problem 1 ⟺ the centre column escapes all finite-state rules.** -/
theorem problem1_iff_escapes_fs : Problem1 ↔ Escapes fsRules centerCol :=
  (escapes_fs_iff centerCol).symm

/-- **Problem 2 ⟺ typicality for the one-rule space {"always black"}.** -/
theorem problem2_iff_typical_const : Problem2 ↔ TypicalFor {constPredictor} centerCol := by
  unfold TypicalFor
  simp only [Set.mem_singleton_iff, forall_eq]
  have : hitsOf constPredictor centerCol = centerCol := by
    funext t; simp [hitsOf, constPredictor]
  rw [this]; rfl

/-- **The Seed Typicality target is typicality for the finite-state rule space.** -/
theorem seedFSTypical_iff : SeedFSTypical ↔ TypicalFor fsRules centerCol := by
  unfold SeedFSTypical FSTypical TypicalFor
  constructor
  · rintro h pred ⟨n, O, rfl⟩
    exact h n O
  · intro h n O
    exact h _ ⟨n, O, rfl⟩

/-- **Escape is seed-specific.** Some right-white row has a centre column captured by a lag rule. -/
theorem exists_rightWhite_row_captured_by_lag :
    ∃ x : Config, (∀ i, 0 < i → x i = false) ∧
      ¬ Escapes lagRules (fun t => evolve x t 0) := by
  obtain ⟨x, hx, -, hper⟩ := exists_row_with_periodic_column
  refine ⟨x, hx, ?_⟩
  rw [escapes_lag_iff, not_not]
  exact hper

end GLM.Rule30
