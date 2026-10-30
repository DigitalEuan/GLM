module

public import Mathlib
public import RequestProject.GLM.Friction

/-!
# Friction, the rest: the re-read, the noise-set margin and wear (Phase 157)

The formal half of `studies/FRICTION_TWO_STUDY.md` (§5).

* `reread_keeps_answer`, `reread_refuses_iff` — the "did you mean" re-read keeps
  the first verdict when it answers and takes the respelt question's verdict
  only when the first refuses.  It never takes an answer away, and it refuses
  exactly when both readings refuse.
* `noise_switches_le` — the reader whose margin is set from how noisy the leader
  has been (move only when `q·S(leader) > (q + r)·S(held)`, for any rule `r`)
  is a keep-or-move reader, so by `GLM.Friction.held_switches_le` it changes its
  reading no more often than the leader.  `noise_steady_moves_iff`: while the
  leader has not changed (`r = 0`) it moves exactly when the leader strictly
  beats the held reading.
* `worn_touches_le` — under a wear budget of `b` per word of the touch set `P`,
  where a word counts at a step only if it has counted fewer than `b` times
  before, the total number of touches over any number of steps is at most
  `b · |P|`.
-/

@[expose] public section

namespace GLM.FrictionTwo

open GLM.Friction

/-! ## The re-read -/

section Reread

variable {α : Type*}

/-- The re-read: a verdict is `some answer` or `none` (refused).  Keep the first
verdict when it answers; otherwise take the second (the respelt question's). -/
def reread : Option α → Option α → Option α
  | some a, _ => some a
  | none, v => v

/-- **The re-read never takes an answer away.** -/
theorem reread_keeps_answer (a : α) (second : Option α) :
    reread (some a) second = some a := rfl

/-- The re-read refuses exactly when both readings refuse. -/
theorem reread_refuses_iff (first second : Option α) :
    reread first second = none ↔ first = none ∧ second = none := by
  cases first <;> simp [reread]

/-- When the first reading refuses, the re-read's verdict is the second's. -/
theorem reread_of_refused (second : Option α) : reread none second = second := rfl

end Reread

/-! ## The margin set from the leader's noise -/

section Noise

variable {α : Type*}

/-- The noise-set reader with scale `q` and noise rule `r` (in the system, `r t`
is the number of changes of the leader so far): it starts at the leader and moves
to the leader `a (t+1)` only when `q·S(leader) > (q + r (t+1))·S(held)`. -/
def noisy (S : ℕ → α → ℕ) (a : ℕ → α) (q : ℕ) (r : ℕ → ℕ) : ℕ → α
  | 0 => a 0
  | t + 1 => if (q + r (t + 1)) * S (t + 1) (noisy S a q r t) < q * S (t + 1) (a (t + 1))
      then a (t + 1) else noisy S a q r t

lemma noisy_step (S : ℕ → α → ℕ) (a : ℕ → α) (q : ℕ) (r : ℕ → ℕ) (t : ℕ) :
    noisy S a q r (t + 1) = noisy S a q r t ∨ noisy S a q r (t + 1) = a (t + 1) := by
  simp only [noisy]
  split_ifs <;> simp

/-- **N1, proved for every noise rule:** the noise-set reader never switches more
often than the frictionless reader (the leader). -/
theorem noise_switches_le [DecidableEq α] (S : ℕ → α → ℕ) (a : ℕ → α) (q : ℕ)
    (r : ℕ → ℕ) (n : ℕ) : switches (noisy S a q r) n ≤ switches a n :=
  held_switches_le (noisy S a q r) a rfl (noisy_step S a q r) n

/-- The reader moves to a leader different from its held reading exactly when the
noise-set margin is passed. -/
theorem noisy_moves_iff (S : ℕ → α → ℕ) (a : ℕ → α) (q : ℕ) (r : ℕ → ℕ) (t : ℕ)
    (hne : noisy S a q r t ≠ a (t + 1)) :
    noisy S a q r (t + 1) = a (t + 1) ↔
      (q + r (t + 1)) * S (t + 1) (noisy S a q r t) < q * S (t + 1) (a (t + 1)) := by
  simp only [noisy]
  split_ifs with h
  · simp [h]
  · simp [h, hne]

/-- With a steady leader (no noise, `r = 0`) and a positive scale, the reader
moves exactly when the leader strictly beats the held reading. -/
theorem noise_steady_moves_iff (S : ℕ → α → ℕ) (a : ℕ → α) (q : ℕ) (r : ℕ → ℕ)
    (t : ℕ) (hq : 0 < q) (hr : r (t + 1) = 0) (hne : noisy S a q r t ≠ a (t + 1)) :
    noisy S a q r (t + 1) = a (t + 1) ↔
      S (t + 1) (noisy S a q r t) < S (t + 1) (a (t + 1)) := by
  rw [noisy_moves_iff S a q r t hne, hr, Nat.add_zero]
  exact Nat.mul_lt_mul_left hq

end Noise

/-! ## Wear -/

section Wear

variable {β : Type*} [DecidableEq β]

/-- How many of the steps before `t` the word `p` counted at. -/
def used (T : ℕ → Finset β) (p : β) (t : ℕ) : ℕ :=
  ((Finset.range t).filter (fun s => p ∈ T s)).card

lemma used_succ (T : ℕ → Finset β) (p : β) (t : ℕ) :
    used T p (t + 1) = used T p t + if p ∈ T t then 1 else 0 := by
  unfold used
  rw [Finset.range_add_one, Finset.filter_insert]
  split_ifs with h
  · rw [Finset.card_insert_of_notMem (by simp)]
  · rfl

/-- A word with a budget of `b` counts at most `b` times. -/
lemma used_le (T : ℕ → Finset β) (b : ℕ) (p : β)
    (hlive : ∀ t, p ∈ T t → used T p t < b) (n : ℕ) : used T p n ≤ b := by
  induction n with
  | zero => simp [used]
  | succ n ih =>
    rw [used_succ]
    split_ifs with h
    · have := hlive n h; omega
    · omega

/-- **Wear bounds the pull.**  If at every step only words of the touch set `P`
count, and only while they have counted fewer than `b` times before, then the
total number of touches over the first `n` steps is at most `b · |P|`. -/
theorem worn_touches_le (P : Finset β) (T : ℕ → Finset β) (b n : ℕ)
    (hsub : ∀ t, T t ⊆ P) (hlive : ∀ t, ∀ p ∈ T t, used T p t < b) :
    ∑ t ∈ Finset.range n, (T t).card ≤ b * P.card := by
  have hcount : ∑ t ∈ Finset.range n, (T t).card = ∑ p ∈ P, used T p n := by
    have h1 : ∀ t, (T t).card = ∑ p ∈ P, if p ∈ T t then 1 else 0 := by
      intro t
      rw [Finset.sum_boole, Nat.cast_id]
      congr 1
      ext p
      simp only [Finset.mem_filter]
      exact ⟨fun h => ⟨hsub t h, h⟩, fun h => h.2⟩
    simp_rw [h1]
    rw [Finset.sum_comm]
    refine Finset.sum_congr rfl (fun p _ => ?_)
    rw [Finset.sum_boole, Nat.cast_id]
    rfl
  rw [hcount, mul_comm]
  calc ∑ p ∈ P, used T p n ≤ ∑ _p ∈ P, b :=
        Finset.sum_le_sum (fun p _ => used_le T b p (fun t h => hlive t p h) n)
    _ = P.card * b := by rw [Finset.sum_const, smul_eq_mul]

end Wear

end GLM.FrictionTwo
