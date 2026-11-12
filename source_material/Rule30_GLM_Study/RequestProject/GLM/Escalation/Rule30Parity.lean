module

public import Mathlib
public import RequestProject.GLM.Rule30.Basic

/-!
# Round 43: the escalation boundary of Rule 30 at the substrate (parity) layer

The exploration's substrate layer perceives parity. Here is what that layer can and cannot see
of a Rule 30 row, exactly. For a finite row `x` (white outside `[-N, N]`) write

* `rowParity x N` — the parity of the number of black cells (the substrate view);
* `pairParity x N` — the parity of the number of adjacent black pairs `11`.

* `rowParity_step` : **the parity law of Rule 30.**
  `rowParity (step x) (N+1) = rowParity x N + pairParity x N` (over `ZMod 2`).
  So one Rule 30 step does **not** descend to the parity layer — the next parity needs one more
  bit, the pair parity (`step_not_congruent_parity`: the rows `11` and `101` have the same parity
  and next rows of different parity).
* `step_escalates_again` : the escalated view (parity, pair parity) determines the next parity
  but not the next pair parity: rows `1` and `111` agree on both bits and their next rows have
  different pair parity. Escalation on Rule 30 does not stop after one rung.

For comparison, Rule 90 (`L xor R`) always produces an even row from a finite row, so its step
descends to the parity layer trivially. The non-linearity `C·R` of Rule 30 is exactly the
pair-count term, i.e. exactly what forces the escalation.
-/

@[expose] public section

namespace GLM.Escalation.Rule30Parity

open GLM.Rule30

/-- A Boolean as an element of `ZMod 2`. -/
def bz (b : Bool) : ZMod 2 := (b.toNat : ZMod 2)

/-- `x` is white outside `[-N, N]`. -/
def Supported (x : Config) (N : ℕ) : Prop := ∀ c : ℤ, (c < -N ∨ (N : ℤ) < c) → x c = false

/-- The substrate view of a finite row: parity of its number of black cells. -/
def rowParity (x : Config) (N : ℕ) : ZMod 2 := ∑ c ∈ Finset.Icc (-(N : ℤ)) N, bz (x c)

/-- Parity of the number of adjacent black pairs. -/
def pairParity (x : Config) (N : ℕ) : ZMod 2 :=
  ∑ c ∈ Finset.Icc (-(N : ℤ)) N, bz (x c) * bz (x (c + 1))

theorem sum_Icc_shift (f : ℤ → ZMod 2) (a b d : ℤ) :
    ∑ c ∈ Finset.Icc a b, f (c + d) = ∑ c ∈ Finset.Icc (a + d) (b + d), f c := by
  apply Finset.sum_nbij' (· + d) (· - d)
  · intro c hc; simp only [Finset.mem_Icc] at hc ⊢; constructor <;> omega
  · intro c hc; simp only [Finset.mem_Icc] at hc ⊢; constructor <;> omega
  · intro c _; simp
  · intro c _; simp
  · intro c _; rfl

/-- A sum over any window containing the support equals the sum over the support window. -/
theorem sum_window (f : ℤ → ZMod 2) (N : ℕ) (hf : ∀ c : ℤ, (c < -N ∨ (N : ℤ) < c) → f c = 0)
    (a b : ℤ) (ha : a ≤ -N) (hb : (N : ℤ) ≤ b) :
    ∑ c ∈ Finset.Icc a b, f c = ∑ c ∈ Finset.Icc (-(N : ℤ)) N, f c := by
  symm
  apply Finset.sum_subset
  · intro c hc; simp only [Finset.mem_Icc] at hc ⊢; omega
  · intro c _ hc
    apply hf
    simp only [Finset.mem_Icc, not_and_or, not_le] at hc
    omega

/-- **The parity law of Rule 30.** -/
theorem rowParity_step (x : Config) (N : ℕ) (hx : Supported x N) :
    rowParity (step x) (N + 1) = rowParity x N + pairParity x N := by
  have hz : ∀ c : ℤ, (c < -N ∨ (N : ℤ) < c) → bz (x c) = 0 := by
    intro c hc; simp [bz, hx c hc]
  have hz2 : ∀ c : ℤ, (c < -N ∨ (N : ℤ) < c) → bz (x c) * bz (x (c + 1)) = 0 := by
    intro c hc; rw [hz c hc, zero_mul]
  unfold rowParity pairParity
  simp only [step]
  have hloc : ∀ c, bz (rule30 (x (c - 1)) (x c) (x (c + 1))) =
      bz (x (c + -1)) + bz (x c) + bz (x (c + 1)) + bz (x c) * bz (x (c + 1)) := by
    intro c; unfold bz; rw [rule30_zmod, sub_eq_add_neg]
  simp only [hloc, Finset.sum_add_distrib]
  have e1 := sum_Icc_shift (fun c => bz (x c)) (-((N + 1 : ℕ) : ℤ)) ((N + 1 : ℕ) : ℤ) (-1)
  have e2 := sum_Icc_shift (fun c => bz (x c)) (-((N + 1 : ℕ) : ℤ)) ((N + 1 : ℕ) : ℤ) 1
  simp only at e1 e2
  rw [e1, e2]
  have w1 := sum_window (fun c => bz (x c)) N hz (-((N + 1 : ℕ) : ℤ) + -1) (((N + 1 : ℕ) : ℤ) + -1)
    (by push_cast; omega) (by push_cast; omega)
  have w2 := sum_window (fun c => bz (x c)) N hz (-((N + 1 : ℕ) : ℤ)) ((N + 1 : ℕ) : ℤ)
    (by push_cast; omega) (by push_cast; omega)
  have w3 := sum_window (fun c => bz (x c)) N hz (-((N + 1 : ℕ) : ℤ) + 1) (((N + 1 : ℕ) : ℤ) + 1)
    (by push_cast; omega) (by push_cast; omega)
  have w4 := sum_window (fun c => bz (x c) * bz (x (c + 1))) N hz2 (-((N + 1 : ℕ) : ℤ))
    ((N + 1 : ℕ) : ℤ) (by push_cast; omega) (by push_cast; omega)
  simp only at w1 w2 w3 w4
  rw [w1, w2, w3, w4]
  have h3 : ∀ s t : ZMod 2, s + s + s + t = s + t := by decide
  exact h3 _ _

/-- The row `11` (cells `0, 1`). -/
def rowA : Config := fun c => decide (c = 0 ∨ c = 1)
/-- The row `101` (cells `-1, 1`). -/
def rowB : Config := fun c => decide (c = -1 ∨ c = 1)
/-- The single black cell `1`. -/
def rowC : Config := fun c => decide (c = 0)
/-- The row `111`. -/
def rowD : Config := fun c => decide (c = -1 ∨ c = 0 ∨ c = 1)

theorem supp_rowA : Supported rowA 1 := by intro c hc; simp [rowA]; omega
theorem supp_rowB : Supported rowB 1 := by intro c hc; simp [rowB]; omega
theorem supp_rowC : Supported rowC 1 := by intro c hc; simp [rowC]; omega
theorem supp_rowD : Supported rowD 1 := by intro c hc; simp [rowD]; omega

theorem step_supported (x : Config) (N : ℕ) (hx : Supported x N) : Supported (step x) (N + 1) := by
  intro c hc
  simp only [step, rule30]
  rw [hx (c - 1) (by push_cast at hc; omega), hx c (by push_cast at hc; omega),
    hx (c + 1) (by push_cast at hc; omega)]
  rfl

/-- **One Rule 30 step does not descend to the parity layer.** `11` and `101` have the same
(even) parity; their successors `1101` and `11011` have different parity. -/
theorem step_not_congruent_parity :
    Supported rowA 1 ∧ Supported rowB 1 ∧ rowParity rowA 1 = rowParity rowB 1 ∧
      rowParity (step rowA) 2 ≠ rowParity (step rowB) 2 := by
  refine ⟨supp_rowA, supp_rowB, ?_, ?_⟩
  · decide
  · rw [rowParity_step _ _ supp_rowA, rowParity_step _ _ supp_rowB]
    decide

/-- **Escalation does not stop after one rung.** `1` and `111` agree on parity and pair parity;
their successors `111` and `11001` have different pair parity. -/
theorem step_escalates_again :
    rowParity rowC 1 = rowParity rowD 1 ∧ pairParity rowC 1 = pairParity rowD 1 ∧
      pairParity (step rowC) 2 ≠ pairParity (step rowD) 2 := by
  refine ⟨by decide, by decide, by decide⟩

end GLM.Escalation.Rule30Parity
