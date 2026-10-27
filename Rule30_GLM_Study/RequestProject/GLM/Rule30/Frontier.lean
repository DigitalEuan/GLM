import RequestProject.GLM.Rule30.Prizes
import RequestProject.GLM.Rule30.FiniteState
import RequestProject.GLM.Rule30.Spectral
import RequestProject.GLM.Rule30.WobbleCertificate
import RequestProject.GLM.Rule30.NoConstantColumn
import RequestProject.GLM.Rule30.OnePeriodicColumn
import RequestProject.GLM.Rule30.ElementaryCA
import RequestProject.GLM.Rule30.Observer
import RequestProject.GLM.Rule30.ChiralLeak
import RequestProject.GLM.Rule30.WobbleLenses
import RequestProject.GLM.Rule30.ShortcutNetwork
import RequestProject.GLM.Rule30.LeftWhiteCompactness
import RequestProject.GLM.Rule30.RunBoundSearch
import RequestProject.GLM.Rule30.Injector
import RequestProject.GLM.Rule30.TopMonomial
import RequestProject.GLM.Rule30.WholeCone
import RequestProject.GLM.Rule30.Ergodic
import RequestProject.GLM.Rule30.Problem3Quantifiers
import RequestProject.GLM.Rule30.Perspective

/-!
# Audit: the frontier of the study, machine-checked in one place

This file adds no new mathematics about Rule 30. It collects the **frontier** of the study as
a handful of checked statements, so that the GLM (or a reader) can see in one file

1. `frontier_proved_partial`: what is proved about the seed's centre column;
2. `frontier_sufficient_targets`: which open hypotheses would settle Problems 1 and 2
   (each arrow is a proved implication);
3. `frontier_restatements`: which reformulations are *equivalent* to Problem 1 or 2
   (proving one is the same task as proving the problem);
4. `frontier_blocked_routes`: which proposed routes are proved **not** to work;
5. `frontier_weakest_target_strictly_weaker`: the weakest sufficient target found so far
   (`SeedAPBalanced`) is strictly weaker, for general sequences, than seed typicality.

Everything here is a direct consequence of theorems proved elsewhere in the package. See
`AUDIT.md` for the plain-language version.
-/



namespace GLM.Rule30

/-- **What is proved about the seed** (the partial results on Problems 1 and 2).
* the centre column is not eventually constant (period 1 of Problem 1);
* at most one column of the seed pattern is eventually periodic;
* the lifted period-1 statement holds for every left-white row;
* Problems 1 and 2 hold for almost every initial row (fair-coin measure). -/
theorem frontier_proved_partial :
    (¬ ∃ b N, ∀ t ≥ N, centerCol t = b) ∧
    (∀ c d : ℤ, EventuallyPeriodic (fun t => evolve seed t c) →
        EventuallyPeriodic (fun t => evolve seed t d) → c = d) ∧
    LeftWhiteAperiodic 1 ∧
    (∀ᵐ x ∂bernoulliRow, ∀ c : ℤ,
        ¬ EventuallyPeriodic (fun t => evolve x t c) ∧ HasFrequencyHalf (fun t => evolve x t c)) :=
  ⟨centerCol_not_eventually_constant, fun _ _ hc hd => seed_at_most_one_periodic_column hc hd,
    leftWhiteAperiodic_one, ae_problems_one_and_two⟩

/-- **Sufficient open targets.** Each of these open statements would settle the problem(s)
named; each implication is proved.
* `SeedFSTypical → SeedAPBalanced → Problem1 ∧ Problem2`;
* `LeftWhiteAperiodicAll → Problem1` (the stack lift), equivalently `RunBoundsAll → Problem1`;
* `PeriodTwoLinearBound → LeftWhiteAperiodic 2` (the narrowest open rung);
* a `C√N` wobble bound → `Problem2`;
* `Problem3Eventual → Problem3`. -/
theorem frontier_sufficient_targets :
    (SeedFSTypical → SeedAPBalanced) ∧
    (SeedAPBalanced → Problem1 ∧ Problem2) ∧
    (LeftWhiteAperiodicAll → Problem1) ∧
    (LeftWhiteAperiodicAll ↔ RunBoundsAll) ∧
    (PeriodTwoLinearBound → LeftWhiteAperiodic 2) ∧
    (∀ C : ℝ, (∀ᶠ n in Filter.atTop, |(wobble centerCol n : ℝ)| ≤ C * Real.sqrt n) →
        Problem2) ∧
    (Problem3Eventual → Problem3) :=
  ⟨apBalanced_of_fsTypical, problems_one_and_two_of_seed_apBalanced,
    problem1_of_leftWhiteAperiodicAll, leftWhiteAperiodicAll_iff_runBoundsAll,
    leftWhiteAperiodic_two_of_linearBound, problem2_of_sqrt_bound, problem3_of_eventual⟩

/-- **Restatements** (equivalent forms; proving any of them *is* proving the problem).
* Problem 1 ⟺ every lag `p` has arbitrarily late mismatches;
* Problem 1 ⟺ every finite-state observer errs infinitely often;
* Problem 1 ⟺ no "shortcut" (jump) rule ever takes over the centre column;
* Problem 1 ⟺ the degree-one ANF slice is not eventually periodic;
* Problem 1 ⟺ the same question for the mirror wheel 86;
* Problem 2 ⟺ the wobble `D(n)` is `o(n)`. -/
theorem frontier_restatements :
    (Problem1 ↔ ∀ p, 0 < p → ∀ N, ∃ t ≥ N, centerCol (t + p) ≠ centerCol t) ∧
    (Problem1 ↔ ∀ n (O : FSObserver (Fin n)) (N : ℕ), ∃ t ≥ N, O.predict t centerCol ≠ centerCol t) ∧
    (Problem1 ↔ ∀ J (f : (Fin J → Bool) → Bool) N, ¬ JumpRuleFrom centerCol J f N) ∧
    (Problem1 ↔ ¬ ∃ p > 0, ∃ N, ∀ n ≥ N,
        anfCoeff (fun x => evolve x (n + p) 0) {0} = anfCoeff (fun x => evolve x n 0) {0}) ∧
    (Problem1 ↔ WheelProblem1 86 seed 0) ∧
    (Problem2 ↔ Filter.Tendsto (fun n => (wobble centerCol n : ℝ) / n) Filter.atTop (nhds 0)) :=
  ⟨problem1_iff_lag_mismatch, problem1_iff_fsObservers_fail, problem1_iff_no_jumpRule,
    problem1_iff_linearCoeff, problem1_iff_eightySix, problem2_iff_wobble⟩

/-- **Blocked routes** (negative controls).
* no property of the `n`-step maps (degree, cone separation, weight, …) can by itself force a
  non-periodic centre column for every row;
* every fact about ANF coefficients of degree `≥ 2` (the injector parity lock included) is
  compatible with a periodic seed column;
* no finite prefix decides Problem 1 or Problem 2. -/
theorem frontier_blocked_routes :
    (∀ P : (ℕ → Config → Bool) → Prop, P (fun n x => evolve x n 0) →
        ¬ (P (fun n x => evolve x n 0) →
          ∀ x : Config, ¬ EventuallyPeriodic (fun n => evolve x n 0))) ∧
    (∃ G : ℕ → Config → Bool,
        (∀ n S, 2 ≤ S.card → anfCoeff (G n) S = anfCoeff (fun x => evolve x n 0) S) ∧
        EventuallyPeriodic (fun n => G n seed)) ∧
    (∀ (c : ℕ → Bool) (N : ℕ),
        (∃ a : ℕ → Bool, (∀ i < N, a i = c i) ∧ EventuallyPeriodic a) ∧
        (∃ b : ℕ → Bool, (∀ i < N, b i = c i) ∧ ¬ EventuallyPeriodic b)) ∧
    (∀ (c : ℕ → Bool) (N : ℕ),
        (∃ a : ℕ → Bool, (∀ i < N, a i = c i) ∧ HasFrequencyHalf a) ∧
        (∃ b : ℕ → Bool, (∀ i < N, b i = c i) ∧ ¬ HasFrequencyHalf b)) :=
  ⟨map_properties_cannot_decide_periodicity, injector_lock_compatible_with_periodicity,
    no_finite_certificate_problem1, no_finite_certificate_problem2⟩

/-- **The weakest sufficient target is strictly weaker than seed typicality** (for general
sequences): finite-state typicality implies AP-balance, and the converse fails. -/
theorem frontier_weakest_target_strictly_weaker :
    (∀ a : ℕ → Bool, FSTypical a → APBalanced a) ∧
    ∃ a : ℕ → Bool, APBalanced a ∧ ¬ FSTypical a :=
  ⟨fun _ h => apBalanced_of_fsTypical h, exists_apBalanced_not_fsTypical⟩

/-- **The observer's frame** (the user's "wobble as perspective" idea, as proved).
* the arrow `−sign D(n)` is exactly the direction that moves the running frequency towards `1/2`;
* the centre column cannot tell Rule 30 from its mirror image Rule 86 (it fixes the class
  `{30, 86}` among all 256 wheels). -/
theorem frontier_observer_frame :
    (∀ (a : ℕ → Bool) (n : ℕ), 1 ≤ n →
        (|freq a (n + 1) - 1 / 2| < |freq a n - 1 / 2| ↔
          (observerArrow a n ≠ 0 ∧ stepDir a n = observerArrow a n))) ∧
    (∀ r : ℕ, r < 256 → (ecaColumn r seed 0 = centerCol ↔ r = 30 ∨ r = 86)) :=
  ⟨fun a _ hn => deviation_decreases_iff a hn, centre_column_class⟩

end GLM.Rule30
