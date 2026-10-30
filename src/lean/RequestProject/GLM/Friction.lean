module

public import Mathlib

/-!
# Friction: stick-slip readings and contact over the whole prompt (Phase 156)

The formal half of `studies/FRICTION_STUDY.md`.

* `held_switches_le` — a reader that at every step either keeps its reading or
  moves to the current leader changes its reading no more often than the
  leader itself changes.  Static friction can only remove changes of mind,
  never add them, whatever the margin.
* `stick_switches_le`, `held_within_margin` — the sticking reader (move to the
  leader only when `q·S(leader) > (q+1)·S(held)`) is such a reader, and its
  held reading is always within the margin of the leader.
* `contact_keeps_large_lead`, `contact_empty_prompt` — the contact score
  `R(c)·(1 + A(c))`, with `A(c)` at most the number `m` of prompt words, never
  overturns a lead in the row larger than the factor `1 + m`, and with no
  prompt words it ranks exactly as the row does.
-/

@[expose] public section

namespace GLM.Friction

/-! ## Switches -/

section Switches

variable {α : Type*} [DecidableEq α]

/-- The number of steps `t < n` at which the reading `f` changes: `f (t+1) ≠ f t`. -/
def switches (f : ℕ → α) : ℕ → ℕ
  | 0 => 0
  | n + 1 => switches f n + if f (n + 1) ≠ f n then 1 else 0

@[simp] lemma switches_zero (f : ℕ → α) : switches f 0 = 0 := rfl

lemma switches_succ (f : ℕ → α) (n : ℕ) :
    switches f (n + 1) = switches f n + if f (n + 1) ≠ f n then 1 else 0 := rfl

lemma switches_mono (f : ℕ → α) {m n : ℕ} (h : m ≤ n) : switches f m ≤ switches f n := by
  induction h with
  | refl => exact le_rfl
  | step _ ih => exact ih.trans (by rw [switches_succ]; omega)

/-- The invariant behind `held_switches_le`: the held reading's switches, plus one
if it is not at the leader now, never exceed the leader's switches. -/
lemma held_switches_add_le (h a : ℕ → α) (h0 : h 0 = a 0)
    (hstep : ∀ t, h (t + 1) = h t ∨ h (t + 1) = a (t + 1)) (n : ℕ) :
    switches h n + (if h n ≠ a n then 1 else 0) ≤ switches a n := by
  induction n with
  | zero => simp [h0]
  | succ n ih =>
    rw [switches_succ, switches_succ]
    rcases hstep n with hk | hm
    · rw [hk]
      split_ifs at ih ⊢ <;> simp_all <;> omega
    · rw [hm]
      split_ifs at ih ⊢ with e1 e2 e3 <;> simp_all <;> omega

/-- **Static friction only removes changes of mind.**  A reading that starts at the
leader and at every step either stays or moves to the leader switches no more often
than the leader does. -/
theorem held_switches_le (h a : ℕ → α) (h0 : h 0 = a 0)
    (hstep : ∀ t, h (t + 1) = h t ∨ h (t + 1) = a (t + 1)) (n : ℕ) :
    switches h n ≤ switches a n :=
  le_trans (Nat.le_add_right _ _) (held_switches_add_le h a h0 hstep n)

end Switches

/-! ## The sticking reader -/

section Stick

variable {α : Type*}

/-- The sticking reader with margin `q`: it starts at the leader `a 0` and moves to
the leader `a (t+1)` only when `q·S(leader) > (q+1)·S(held)`. -/
def stick (S : ℕ → α → ℕ) (a : ℕ → α) (q : ℕ) : ℕ → α
  | 0 => a 0
  | t + 1 => if (q + 1) * S (t + 1) (stick S a q t) < q * S (t + 1) (a (t + 1))
      then a (t + 1) else stick S a q t

lemma stick_step (S : ℕ → α → ℕ) (a : ℕ → α) (q t : ℕ) :
    stick S a q (t + 1) = stick S a q t ∨ stick S a q (t + 1) = a (t + 1) := by
  simp only [stick]
  split_ifs <;> simp

/-- S1: the sticking reader never switches more often than the frictionless one. -/
theorem stick_switches_le [DecidableEq α] (S : ℕ → α → ℕ) (a : ℕ → α) (q n : ℕ) :
    switches (stick S a q) n ≤ switches a n :=
  held_switches_le (stick S a q) a rfl (stick_step S a q) n

/-- The held reading is always within the margin of the leader. -/
theorem held_within_margin (S : ℕ → α → ℕ) (a : ℕ → α) (q t : ℕ) :
    q * S t (a t) ≤ (q + 1) * S t (stick S a q t) := by
  cases t with
  | zero => simp only [stick]; nlinarith
  | succ t =>
    simp only [stick]
    split_ifs with hs
    · nlinarith
    · omega

end Stick

/-! ## Contact over the whole prompt -/

section Contact

variable {β : Type*}

/-- The contact score of a candidate: its row count times one plus the number of
prompt words it touches. -/
def contact (R A : β → ℕ) (c : β) : ℕ := R c * (1 + A c)

/-- **The corpus still decides a clear lead.**  When every candidate touches at
most `m` prompt words, a candidate whose row count exceeds another's by more than
the factor `1 + m` keeps its lead under contact. -/
theorem contact_keeps_large_lead (R A : β → ℕ) (m : ℕ) (hA : ∀ x, A x ≤ m) (c d : β)
    (hlead : R d * (1 + m) < R c) : contact R A d < contact R A c := by
  unfold contact
  have h1 : R d * (1 + A d) ≤ R d * (1 + m) := Nat.mul_le_mul_left _ (by have := hA d; omega)
  have h2 : R c ≤ R c * (1 + A c) := Nat.le_mul_of_pos_right _ (by omega)
  omega

/-- With no prompt words touching, contact ranks exactly as the row does. -/
theorem contact_empty_prompt (R A : β → ℕ) (hA : ∀ x, A x = 0) (c : β) :
    contact R A c = R c := by
  simp [contact, hA]

end Contact

end GLM.Friction
