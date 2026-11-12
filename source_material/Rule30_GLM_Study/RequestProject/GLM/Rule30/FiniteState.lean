module

public import RequestProject.GLM.Rule30.Unpredictability

/-!
# Finite-state observers: the exact form of the Seed Typicality target

A *finite-state observer* reads a column bit by bit, keeps only a state from a finite set, and
before each bit guesses it from its current state. This is the class of "observers with bounded
memory" (the GLM observer `Y` with a finite read window or finite internal register).

Main results (all proved):

* `eventuallyPeriodic_iff_exists_fsObserver` : a sequence is eventually periodic **iff** some
  finite-state observer is eventually always right on it.
* `problem1_iff_fsObservers_fail` : **Problem 1 is equivalent to**: every finite-state observer
  makes infinitely many mistakes on the centre column.
* `FSTypical a` : every finite-state observer is right on `a` with asymptotic frequency exactly `1/2`.
* `ae_fsTypical` : for almost every row, every column is `FSTypical`, simultaneously for all
  finite-state observers (there are only countably many).
* `exists_fsTypical_column` : so `FSTypical` is a consistent, non-vacuous notion (in contrast to
  typicality for *all* causal predictors, which no row has: `no_row_typical_for_all_predictors`).
* `problems_one_and_two_of_seed_fsTypical` : **Seed Typicality Theorem (target) ⇒ Problems 1
  and 2.** If the seed's centre column is `FSTypical`, both prize problems follow.

`SeedFSTypical` is therefore the precise statement of the "Seed Typicality Theorem" proposed as
the bridge for P1 and P2. It remains **open**: this file proves that it suffices, and that it holds
for almost every row, but not that it holds for the seed.

Remark: the wobble-arrow observer of `Perspective.lean` is *not* finite-state (it needs the
unbounded counter `D(t)`), so it is covered by `ae_predictor_hits_half` but not by `FSTypical`.
-/

@[expose] public section

namespace GLM.Rule30

open MeasureTheory Filter

/-- A finite-state observer (Moore machine): an initial state, a state update on reading a bit,
and a guess for the next bit made from the current state. Finiteness of `σ` is assumed where
needed. -/
structure FSObserver (σ : Type) where
  init : σ
  update : σ → Bool → σ
  guess : σ → Bool

namespace FSObserver

variable {σ : Type} (O : FSObserver σ)

/-- The state after reading `a 0, …, a (t-1)`. -/
def state (O : FSObserver σ) (a : ℕ → Bool) : ℕ → σ
  | 0 => O.init
  | t + 1 => O.update (state O a t) (a t)

/-- The observer's guess for bit `t`. -/
def predict (t : ℕ) (a : ℕ → Bool) : Bool := O.guess (O.state a t)

theorem state_causal (a b : ℕ → Bool) (t : ℕ) (h : ∀ i < t, a i = b i) :
    O.state a t = O.state b t := by
  induction t with
  | zero => rfl
  | succ t ih =>
    simp only [state]
    rw [ih (fun i hi => h i (by omega)), h t (by omega)]

/-- A finite-state observer is a causal predictor. -/
theorem isCausal : IsCausal O.predict := fun t a b h => by
  simp only [predict, O.state_causal a b t h]

end FSObserver

/-- The predictor is right on `a` at every time from some point on. -/
def EventuallyAlwaysRight (pred : ℕ → (ℕ → Bool) → Bool) (a : ℕ → Bool) : Prop :=
  ∃ N, ∀ t ≥ N, pred t a = a t

/-- **A finite-state observer that is eventually always right forces eventual periodicity.**
Once it is always right, the observer runs autonomously (`s ↦ update s (guess s)`), and a map of a
finite set into itself is eventually periodic. -/
theorem eventuallyPeriodic_of_fsObserver {σ : Type} [Finite σ] (O : FSObserver σ) (a : ℕ → Bool)
    (h : EventuallyAlwaysRight O.predict a) : EventuallyPeriodic a := by
  obtain ⟨N, hN⟩ := h
  set s := O.state a
  -- after time `N` the state evolves autonomously
  have hstep : ∀ t ≥ N, s (t + 1) = O.update (s t) (O.guess (s t)) := by
    intro t ht
    show O.update (O.state a t) (a t) = _
    rw [← hN t ht]; rfl
  obtain ⟨i, j, hij, heq⟩ := Finite.exists_ne_map_eq_of_infinite (fun k : ℕ => s (N + k))
  wlog hlt : i < j generalizing i j
  · exact this j i (Ne.symm hij) heq.symm (by omega)
  have hrep : ∀ m, s (N + i + m) = s (N + j + m) := by
    intro m
    induction m with
    | zero => simpa using heq
    | succ m ih =>
      rw [← add_assoc, ← add_assoc, hstep _ (by omega), hstep _ (by omega), ih]
  refine ⟨j - i, by omega, N + i, fun n hn => ?_⟩
  rw [← hN n (by omega), ← hN (n + (j - i)) (by omega)]
  show O.guess (s (n + (j - i))) = O.guess (s n)
  have := hrep (n - (N + i))
  rw [show N + i + (n - (N + i)) = n by omega, show N + j + (n - (N + i)) = n + (j - i) by omega]
    at this
  rw [this]

/-- The counter observer for an eventually periodic sequence: it counts time up to `N + p` and then
cycles through the period, guessing the stored bit. -/
def counterObserver (a : ℕ → Bool) (N p : ℕ) (hp : 0 < p) : FSObserver (Fin (N + p)) where
  init := ⟨0, by omega⟩
  update i _ := if h : i.val + 1 < N + p then ⟨i.val + 1, h⟩ else ⟨N, by omega⟩
  guess i := a i.val

/-- The counter value after `t` steps. -/
theorem counter_arith (N p t : ℕ) (hp : 0 < p) :
    (if t + 1 < N + p then t + 1 else N + (t + 1 - N) % p) =
      if (if t < N + p then t else N + (t - N) % p) + 1 < N + p
        then (if t < N + p then t else N + (t - N) % p) + 1 else N := by
  have hm := Nat.mod_lt (t - N) hp
  by_cases h1 : t + 1 < N + p
  · rw [if_pos h1, if_pos (show t < N + p by omega), if_pos h1]
  · rw [if_neg h1]
    by_cases h2 : t < N + p
    · rw [if_pos h2, if_neg (by omega), show t + 1 - N = p by omega, Nat.mod_self]; simp
    · rw [if_neg h2]
      have key : (t + 1 - N) % p = if (t - N) % p + 1 < p then (t - N) % p + 1 else 0 := by
        rw [show t + 1 - N = (t - N) + 1 by omega, Nat.add_mod]
        rcases Nat.lt_or_ge 1 p with hp1 | hp1
        · rw [Nat.mod_eq_of_lt hp1]
          split_ifs with h3
          · exact Nat.mod_eq_of_lt h3
          · rw [show (t - N) % p + 1 = p by omega, Nat.mod_self]
        · have : p = 1 := by omega
          subst this; simp [Nat.mod_one]
      rw [key]
      split_ifs <;> omega

theorem counterObserver_state (a b : ℕ → Bool) (N p : ℕ) (hp : 0 < p) (t : ℕ) :
    ((counterObserver a N p hp).state b t).val =
      if t < N + p then t else N + (t - N) % p := by
  induction t with
  | zero => simp [FSObserver.state, counterObserver]; omega
  | succ t ih =>
    rw [counter_arith N p t hp, ← ih]
    simp only [FSObserver.state, counterObserver]
    split_ifs <;> rfl

/-- **An eventually periodic sequence is predicted perfectly by a finite-state observer** (the
counter observer is right at every time). -/
theorem exists_fsObserver_of_eventuallyPeriodic (a : ℕ → Bool) (h : EventuallyPeriodic a) :
    ∃ n, ∃ O : FSObserver (Fin n), ∀ t, O.predict t a = a t := by
  obtain ⟨p, hp, N, hN⟩ := h
  refine ⟨N + p, counterObserver a N p hp, fun t => ?_⟩
  show a ((counterObserver a N p hp).state a t).val = a t
  rw [counterObserver_state]
  split_ifs with ht
  · rfl
  · have := periodic_mul hN ((t - N) / p) (N + (t - N) % p) (by omega)
    rw [← this]
    congr 1
    have := Nat.mod_add_div (t - N) p
    rw [mul_comm] at this
    omega

/-- **Exact equivalence.** A sequence is eventually periodic iff some finite-state observer is
eventually always right on it. -/
theorem eventuallyPeriodic_iff_exists_fsObserver (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ ∃ n, ∃ O : FSObserver (Fin n), EventuallyAlwaysRight O.predict a := by
  constructor
  · intro h
    obtain ⟨n, O, hO⟩ := exists_fsObserver_of_eventuallyPeriodic a h
    exact ⟨n, O, 0, fun t _ => hO t⟩
  · rintro ⟨n, O, hO⟩
    exact eventuallyPeriodic_of_fsObserver O a hO

/-- **Problem 1, restated through observers.** The centre column is not eventually periodic iff
every finite-state observer makes infinitely many mistakes on it. -/
theorem problem1_iff_fsObservers_fail :
    Problem1 ↔ ∀ n (O : FSObserver (Fin n)) (N : ℕ), ∃ t ≥ N, O.predict t centerCol ≠ centerCol t := by
  unfold Problem1
  rw [eventuallyPeriodic_iff_exists_fsObserver]
  simp only [EventuallyAlwaysRight, not_exists, not_forall, exists_prop]

/-- The same equivalence for observers on an arbitrary finite state type. -/
theorem problem1_iff_fsObservers_fail' :
    Problem1 ↔ ∀ (σ : Type) [Finite σ] (O : FSObserver σ), ¬ EventuallyAlwaysRight O.predict centerCol := by
  constructor
  · intro h σ _ O hO
    exact h (eventuallyPeriodic_of_fsObserver O centerCol hO)
  · intro h hp
    obtain ⟨n, O, hO⟩ := (eventuallyPeriodic_iff_exists_fsObserver centerCol).mp hp
    exact h (Fin n) O hO

/-- **Finite-state typicality.** Every finite-state observer is right on `a` with asymptotic
frequency exactly `1/2`. -/
def FSTypical (a : ℕ → Bool) : Prop :=
  ∀ n (O : FSObserver (Fin n)), HasFrequencyHalf (fun t => decide (a t = O.predict t a))

/-- **The Seed Typicality target** (open): the seed's centre column is finite-state typical. -/
def SeedFSTypical : Prop := FSTypical centerCol

/-- The constant observer "always guess black". -/
def constObserver : FSObserver (Fin 1) := ⟨0, fun _ _ => 0, fun _ => true⟩

/-- **Seed Typicality ⇒ Problems 1 and 2.** -/
theorem problems_one_and_two_of_seed_fsTypical (h : SeedFSTypical) : Problem1 ∧ Problem2 := by
  constructor
  · intro hp
    obtain ⟨n, O, hO⟩ := exists_fsObserver_of_eventuallyPeriodic centerCol hp
    refine not_hasFrequencyHalf_of_eventually_true _ 0 (fun t _ => ?_) (h n O)
    simp [hO t]
  · have := h 1 constObserver
    simp only [FSObserver.predict, constObserver] at this
    simpa [Problem2] using this

theorem fsObserver_predict_hit {n : ℕ} (O : FSObserver (Fin n)) (c : ℤ) (x : Config) (t : ℕ) :
    decide ((fun t => evolve x t c) t = O.predict t (fun t => evolve x t c)) = hit O.predict c t x :=
  rfl

/-- **Almost every row is finite-state typical**, in every column, simultaneously for all
finite-state observers. -/
theorem ae_fsTypical (c : ℤ) : ∀ᵐ x ∂bernoulliRow, FSTypical (fun t => evolve x t c) := by
  have key : ∀ᵐ x ∂bernoulliRow, ∀ (n : ℕ) (i : Fin n) (u : Fin n → Bool → Fin n) (g : Fin n → Bool),
      HasFrequencyHalf (fun t => hit (FSObserver.predict ⟨i, u, g⟩) c t x) := by
    rw [ae_all_iff]; intro n
    rw [ae_all_iff]; intro i
    rw [ae_all_iff]; intro u
    rw [ae_all_iff]; intro g
    exact ae_predictor_hits_half _ (FSObserver.isCausal _) c
  filter_upwards [key] with x hx
  intro n O
  exact hx n O.init O.update O.guess

/-- `FSTypical` is consistent: some row has a finite-state typical centre column. -/
theorem exists_fsTypical_column (c : ℤ) : ∃ x : Config, FSTypical (fun t => evolve x t c) :=
  (ae_fsTypical c).exists

/-- And it is a real restriction: the constant sequence is not finite-state typical. -/
theorem not_fsTypical_const : ¬ FSTypical (fun _ => true) := by
  intro h
  have := h 1 constObserver
  exact not_hasFrequencyHalf_of_eventually_true _ 0 (fun t _ => by
    simp [FSObserver.predict, constObserver]) this

end GLM.Rule30
