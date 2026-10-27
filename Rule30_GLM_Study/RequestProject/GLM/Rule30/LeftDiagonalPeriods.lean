module

public import RequestProject.GLM.Rule30.ReadAngle

/-!
# Round 38: the period law of the left diagonals (found by the hypothesis engine)

`ReadAngle.lean` proved that every left diagonal `ldiag D t = a(t)(D − t)` is eventually periodic
with a power-of-two period, and recorded (`EMP`, ledger C133) that the periods are at most `8`
for `D ≤ 200`.  The Round 38 hypothesis engine (`rule30_round38/` in the study folder) proposed
the natural generalisation *"every left diagonal has eventual period dividing 8"*.  It survived
the development range, and was refuted on the held-out range at `D = 400`.  The engine read the
counterexample, found that diagonal `399` is eventually white, and proposed the mechanism that
this file proves for every diagonal.

## The one-bit machine with a reset

A left diagonal is driven by the two diagonals outside it:
`ldiag D (t+1) = ldiag (D−2) t xor (ldiag (D−1) t ∨ ldiag D t)` (`ldiag_succ`).  When the input
`ldiag (D−1)` is black the machine is **reset**: its next bit no longer depends on its own state.

* `one_bit_reset` : if both inputs are periodic with period `Q` and the second input is black at
  least once after they became periodic, the output is periodic with the **same** period `Q`.
* `one_bit_white_input`, `parityOn_shift` : if the second input is eventually white, the output
  advances by the parity of the first input: `u (t + Q) = u t xor parity`.  So the period stays
  `Q` when the parity is even and doubles when it is odd (`one_bit_doubles`).

## The law for the left diagonals (every `D`)

* `ldiag_evPer_of_not_white` : if the diagonals `D − 1` and `D − 2` have eventual period `Q` and
  diagonal `D − 1` is **not** eventually white, then diagonal `D` has eventual period `Q`.
* `ldiag_doubles` : if diagonal `D − 1` is eventually white and diagonal `D − 2` has period `Q`
  with odd parity, then diagonal `D` does not have period `Q`, and it has period `2Q`.
* `leftDiag_periods_bounded_of_finitely_many_white` : if only finitely many left diagonals are
  eventually white, one period serves every left diagonal.  Contrapositive
  (`infinitely_many_white_of_unbounded`): **unbounded left-diagonal periods force infinitely many
  eventually white left diagonals.**

## Seed-forgetting (every left-white row)

* `one_bit_sync` : two one-bit machines with the same inputs agree from the first black cell of
  the reset input on, whatever their initial bits.
* `ldiagOf_sync`, `first_difference_after_white` : for two rows white on `(−∞, 0)` and black at
  `0`, the first left diagonal on which they differ eventually comes right after an eventually
  white diagonal.  A reset erases the seed; only white diagonals let it leave a trace.

The certified data (`LeftDiagonalPeriodsData.lean`) shows the law at work: the eventually white
diagonals below `87868` are exactly `2, 7, 28, 399, 53207, 58286, 87866`, and the least period
doubles exactly after the odd ones, at `D = 3, 8, 29, 400, 87867`.

All results use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Two predicates on Boolean sequences -/

/-- `s` has eventual period `p` (`p = 0` allowed: then it says nothing). -/
def EvPer (s : ℕ → Bool) (p : ℕ) : Prop := ∃ T, ∀ t ≥ T, s (t + p) = s t

/-- `s` is eventually white (eventually `false`). -/
def EventuallyWhite (s : ℕ → Bool) : Prop := ∃ T, ∀ t ≥ T, s t = false

theorem EvPer.mul {s : ℕ → Bool} {p : ℕ} (h : EvPer s p) (k : ℕ) : EvPer s (k * p) := by
  obtain ⟨T, hT⟩ := h
  exact ⟨T, periodic_mul hT k⟩

theorem EvPer.of_dvd {s : ℕ → Bool} {p q : ℕ} (h : EvPer s p) (hpq : p ∣ q) : EvPer s q := by
  obtain ⟨k, rfl⟩ := hpq
  rw [mul_comm]; exact h.mul k

theorem EvPer.mono_start {s : ℕ → Bool} {p T T' : ℕ} (h : ∀ t ≥ T, s (t + p) = s t)
    (hT : T ≤ T') : ∀ t ≥ T', s (t + p) = s t := fun t ht => h t (le_trans hT ht)

/-- Parity of the number of black cells of `a` in the window `[t, t + n)`. -/
def parityOn (a : ℕ → Bool) (t : ℕ) : ℕ → Bool
  | 0 => false
  | n + 1 => xor (parityOn a t n) (a (t + n))

/-! ## The one-bit machine `u (t+1) = a t xor (b t ∨ u t)` -/

/-- **Reset law.**  Periodic inputs with a black cell in the second input after the start: the
output has the same period. -/
theorem one_bit_reset {a b u : ℕ → Bool} {Q T t₀ : ℕ}
    (hu : ∀ t, u (t + 1) = xor (a t) (b t || u t))
    (ha : ∀ t ≥ T, a (t + Q) = a t) (hb : ∀ t ≥ T, b (t + Q) = b t)
    (ht₀ : T ≤ t₀) (hb₀ : b t₀ = true) : ∀ t ≥ t₀ + 1, u (t + Q) = u t := by
  intro t ht
  induction t, ht using Nat.le_induction with
  | base =>
    rw [show t₀ + 1 + Q = (t₀ + Q) + 1 by ring, hu, hu, ha _ ht₀, hb _ ht₀, hb₀]
    simp
  | succ t ht ih =>
    rw [show t + 1 + Q = (t + Q) + 1 by ring, hu, hu, ih, ha _ (by omega), hb _ (by omega)]

/-- **White second input.**  The output runs the parity of the first input. -/
theorem one_bit_white_input {a b u : ℕ → Bool} {T : ℕ}
    (hu : ∀ t, u (t + 1) = xor (a t) (b t || u t)) (hb : ∀ t ≥ T, b t = false) :
    ∀ t ≥ T, ∀ n, u (t + n) = xor (u t) (parityOn a t n) := by
  intro t ht n
  induction n with
  | zero => simp [parityOn]
  | succ n ih =>
    rw [← add_assoc, hu, hb _ (by omega), ih]
    simp only [parityOn]
    cases u t <;> cases parityOn a t n <;> cases a (t + n) <;> rfl

theorem parityOn_succ_start (a : ℕ → Bool) (t n : ℕ) :
    parityOn a (t + 1) n = xor (xor (parityOn a t n) (a t)) (a (t + n)) := by
  induction n with
  | zero => simp [parityOn]
  | succ n ih =>
    simp only [parityOn, ih]
    rw [show t + 1 + n = t + (n + 1) by ring]
    cases parityOn a t n <;> cases a t <;> cases a (t + n) <;> cases a (t + (n + 1)) <;> rfl

/-- The parity over one period does not depend on where the window starts. -/
theorem parityOn_shift {a : ℕ → Bool} {Q T : ℕ} (ha : ∀ t ≥ T, a (t + Q) = a t) :
    ∀ t ≥ T, parityOn a t Q = parityOn a T Q := by
  intro t ht
  induction t, ht using Nat.le_induction with
  | base => rfl
  | succ t ht ih =>
    rw [parityOn_succ_start, ha _ ht, ih]
    cases parityOn a T Q <;> cases a t <;> rfl

/-- With a white second input the output advances by one fixed parity per period. -/
theorem one_bit_white_period {a b u : ℕ → Bool} {Q T : ℕ}
    (hu : ∀ t, u (t + 1) = xor (a t) (b t || u t)) (ha : ∀ t ≥ T, a (t + Q) = a t)
    (hb : ∀ t ≥ T, b t = false) : ∀ t ≥ T, u (t + Q) = xor (u t) (parityOn a T Q) := by
  intro t ht
  rw [one_bit_white_input hu hb t ht Q, parityOn_shift ha t ht]

/-- **Doubling law.**  White second input and odd parity: the period `Q` is lost (the output is
anti-periodic) and `2Q` is a period. -/
theorem one_bit_doubles {a b u : ℕ → Bool} {Q T : ℕ}
    (hu : ∀ t, u (t + 1) = xor (a t) (b t || u t)) (ha : ∀ t ≥ T, a (t + Q) = a t)
    (hb : ∀ t ≥ T, b t = false) (hodd : parityOn a T Q = true) :
    (∀ t ≥ T, u (t + Q) = !u t) ∧ ¬ EvPer u Q ∧ EvPer u (2 * Q) := by
  have h := one_bit_white_period hu ha hb
  have anti : ∀ t ≥ T, u (t + Q) = !u t := by
    intro t ht; rw [h t ht, hodd]; cases u t <;> rfl
  refine ⟨anti, ?_, ⟨T, fun t ht => ?_⟩⟩
  · rintro ⟨T', hT'⟩
    have e1 := anti (max T T') (le_max_left _ _)
    have e2 := hT' (max T T') (le_max_right _ _)
    rw [e2] at e1; cases hu' : u (max T T') <;> simp [hu'] at e1
  · rw [two_mul, ← add_assoc, anti _ (by omega), anti _ ht, Bool.not_not]

/-! ## The law for the left diagonals -/

theorem ldiag_machine (D : ℤ) :
    ∀ t, ldiag D (t + 1) = xor (ldiag (D - 2) t) (ldiag (D - 1) t || ldiag D t) :=
  ldiag_succ D

/-- **Period law, reset case.**  If the two outer diagonals have period `Q` and the nearer one is
not eventually white, the diagonal has period `Q` as well. -/
theorem ldiag_evPer_of_not_white {D : ℤ} {Q : ℕ} (h1 : EvPer (ldiag (D - 1)) Q)
    (h2 : EvPer (ldiag (D - 2)) Q) (hw : ¬ EventuallyWhite (ldiag (D - 1))) :
    EvPer (ldiag D) Q := by
  obtain ⟨T1, hT1⟩ := h1
  obtain ⟨T2, hT2⟩ := h2
  have : ∃ t₀ ≥ max T1 T2, ldiag (D - 1) t₀ = true := by
    by_contra hne
    push_neg at hne
    exact hw ⟨max T1 T2, fun t ht => by simpa using hne t ht⟩
  obtain ⟨t₀, ht₀, hb₀⟩ := this
  exact ⟨t₀ + 1, one_bit_reset (ldiag_machine D) (EvPer.mono_start hT2 (le_max_right _ _))
    (EvPer.mono_start hT1 (le_max_left _ _)) ht₀ hb₀⟩

/-- **Period law, doubling case.**  If the nearer outer diagonal is eventually white and the
farther one has period `Q` with odd parity, the diagonal loses the period `Q` and has `2Q`. -/
theorem ldiag_doubles {D : ℤ} {Q T : ℕ} (h2 : ∀ t ≥ T, ldiag (D - 2) (t + Q) = ldiag (D - 2) t)
    (hw : ∀ t ≥ T, ldiag (D - 1) t = false) (hodd : parityOn (ldiag (D - 2)) T Q = true) :
    ¬ EvPer (ldiag D) Q ∧ EvPer (ldiag D) (2 * Q) :=
  (one_bit_doubles (ldiag_machine D) h2 hw hodd).2

/-- With an eventually white nearer diagonal and even parity, the period is kept. -/
theorem ldiag_keeps_of_even {D : ℤ} {Q T : ℕ}
    (h2 : ∀ t ≥ T, ldiag (D - 2) (t + Q) = ldiag (D - 2) t)
    (hw : ∀ t ≥ T, ldiag (D - 1) t = false) (heven : parityOn (ldiag (D - 2)) T Q = false) :
    EvPer (ldiag D) Q :=
  ⟨T, fun t ht => by rw [one_bit_white_period (ldiag_machine D) h2 hw t ht, heven]; simp⟩

/-- Every left diagonal has some power-of-two eventual period (`ReadAngle.lean`), in `EvPer`
form. -/
theorem ldiag_evPer_pow (D : ℤ) : ∃ k, EvPer (ldiag D) (2 ^ k) := by
  obtain ⟨k, T, h⟩ := ldiag_eventually_periodic D
  exact ⟨k, T, h⟩

/-- Finitely many left diagonals share a power-of-two period. -/
theorem ldiag_common_period (n : ℕ) : ∃ m, ∀ D : ℕ, D < n → EvPer (ldiag D) (2 ^ m) := by
  induction n with
  | zero => exact ⟨0, fun D hD => absurd hD (Nat.not_lt_zero _)⟩
  | succ n ih =>
    obtain ⟨m, hm⟩ := ih
    obtain ⟨k, hk⟩ := ldiag_evPer_pow (n : ℤ)
    refine ⟨max m k, fun D hD => ?_⟩
    rcases Nat.lt_succ_iff_lt_or_eq.mp hD with h | h
    · exact (hm D h).of_dvd (pow_dvd_pow 2 (le_max_left _ _))
    · subst h; exact hk.of_dvd (pow_dvd_pow 2 (le_max_right _ _))

/-- **Bounded periods from finitely many white diagonals.**  If no left diagonal beyond `D₀` is
eventually white, one power of two is an eventual period of every left diagonal. -/
theorem leftDiag_periods_bounded_of_finitely_many_white {D₀ : ℕ}
    (hw : ∀ D : ℕ, D₀ ≤ D → ¬ EventuallyWhite (ldiag D)) :
    ∃ m, ∀ D : ℕ, EvPer (ldiag D) (2 ^ m) := by
  obtain ⟨m, hm⟩ := ldiag_common_period (D₀ + 2)
  refine ⟨m, fun D => ?_⟩
  induction D using Nat.strong_induction_on with
  | _ D ih =>
    rcases lt_or_ge D (D₀ + 2) with h | h
    · exact hm D h
    · have e1 : ((D : ℤ) - 1) = ((D - 1 : ℕ) : ℤ) := by omega
      have e2 : ((D : ℤ) - 2) = ((D - 2 : ℕ) : ℤ) := by omega
      apply ldiag_evPer_of_not_white
      · rw [e1]; exact ih _ (by omega)
      · rw [e2]; exact ih _ (by omega)
      · rw [e1]; exact hw _ (by omega)

/-- **Unbounded periods force infinitely many eventually white left diagonals.** -/
theorem infinitely_many_white_of_unbounded (hu : ∀ m, ∃ D : ℕ, ¬ EvPer (ldiag D) (2 ^ m)) :
    ∀ D₀ : ℕ, ∃ D ≥ D₀, EventuallyWhite (ldiag D) := by
  intro D₀
  by_contra hne
  push_neg at hne
  obtain ⟨m, hm⟩ := leftDiag_periods_bounded_of_finitely_many_white
    (D₀ := D₀) (fun D hD hW => hne D hD hW)
  obtain ⟨D, hD⟩ := hu m
  exact hD (hm D)

/-- The open uniform statement proposed by the engine, as a `Prop` (never an axiom): every left
diagonal has eventual period dividing `p`. -/
def LeftDiagPeriodDivides (p : ℕ) : Prop := ∀ D : ℕ, EvPer (ldiag D) p

theorem LeftDiagPeriodDivides.of_dvd {p q : ℕ} (h : LeftDiagPeriodDivides p) (hpq : p ∣ q) :
    LeftDiagPeriodDivides q := fun D => (h D).of_dvd hpq

/-! ## Seed-forgetting: what every left-white row shares with the seed

The Round 38 engine's controls found that the seeds `11` and `101` have exactly the same eventual
left diagonals as the single black cell, and that among all 512 seeds of width `≤ 10` the first
eventual difference from the single cell always sits right after an eventually white diagonal.
The reset law explains this: a reset erases the machine's memory, so only a white input lets the
initial row leave a trace. -/

/-- Left diagonal `D` of an arbitrary row (left edge at `0` when the row is white on `(-∞, 0)` and
black at `0`). -/
def ldiagOf (x : Config) (D : ℤ) (t : ℕ) : Bool := evolve x t (D - t)

theorem ldiagOf_seed : ldiagOf seed = ldiag := rfl

theorem ldiagOf_succ (x : Config) (D : ℤ) (t : ℕ) :
    ldiagOf x D (t + 1) = xor (ldiagOf x (D - 2) t) (ldiagOf x (D - 1) t || ldiagOf x D t) := by
  unfold ldiagOf
  rw [evolve_succ]
  have e1 : D - ((t + 1 : ℕ) : ℤ) - 1 = D - 2 - t := by push_cast; ring
  have e2 : D - ((t + 1 : ℕ) : ℤ) = D - 1 - t := by push_cast; ring
  have e3 : D - ((t + 1 : ℕ) : ℤ) + 1 = D - t := by push_cast; ring
  rw [e1, e3, e2]; rfl

/-- Rows white on `(-∞, 0)` and black at `0`. -/
def LeftEdgeAtZero (x : Config) : Prop := (∀ j, j < 0 → x j = false) ∧ x 0 = true

theorem ldiagOf_neg {x : Config} (hx : LeftEdgeAtZero x) {D : ℤ} (hD : D < 0) (t : ℕ) :
    ldiagOf x D t = false :=
  evolve_white_left x 0 hx.1 t _ (by omega)

theorem ldiagOf_zero {x : Config} (hx : LeftEdgeAtZero x) (t : ℕ) : ldiagOf x 0 t = true := by
  have := evolve_left_edge x 0 hx.1 hx.2 t
  simpa [ldiagOf] using this

theorem ldiagOf_one {x : Config} (hx : LeftEdgeAtZero x) (t : ℕ) :
    ldiagOf x 1 (t + 1) = true := by
  rw [ldiagOf_succ, ldiagOf_neg hx (by norm_num)]
  norm_num [ldiagOf_zero hx]

/-- Two sequences agree from some time on. -/
def EventuallyEq (s s' : ℕ → Bool) : Prop := ∃ T, ∀ t ≥ T, s t = s' t

/-- **Synchronisation.**  Two one-bit machines fed the same inputs agree from the first black
cell of the reset input on, whatever their initial bits. -/
theorem one_bit_sync {a b u u' : ℕ → Bool} {t₀ : ℕ}
    (hu : ∀ t, u (t + 1) = xor (a t) (b t || u t))
    (hu' : ∀ t, u' (t + 1) = xor (a t) (b t || u' t)) (hb : b t₀ = true) :
    ∀ t ≥ t₀ + 1, u t = u' t := by
  intro t ht
  induction t, ht using Nat.le_induction with
  | base => rw [hu, hu', hb]; simp
  | succ t ht ih => rw [hu, hu', ih]

/-- **Seed-forgetting law.**  If two left-edge rows have eventually equal diagonals `D − 1` and
`D − 2`, and diagonal `D − 1` is not eventually white, their diagonals `D` are eventually
equal. -/
theorem ldiagOf_sync {x y : Config} {D : ℤ}
    (h1 : EventuallyEq (ldiagOf x (D - 1)) (ldiagOf y (D - 1)))
    (h2 : EventuallyEq (ldiagOf x (D - 2)) (ldiagOf y (D - 2)))
    (hw : ¬ EventuallyWhite (ldiagOf x (D - 1))) :
    EventuallyEq (ldiagOf x D) (ldiagOf y D) := by
  obtain ⟨T1, hT1⟩ := h1
  obtain ⟨T2, hT2⟩ := h2
  have : ∃ t₀ ≥ max T1 T2, ldiagOf x (D - 1) t₀ = true := by
    by_contra hne
    push_neg at hne
    exact hw ⟨max T1 T2, fun t ht => by simpa using hne t ht⟩
  obtain ⟨t₀, ht₀, hb⟩ := this
  refine ⟨t₀ + 1, fun t ht => ?_⟩
  induction t, ht using Nat.le_induction with
  | base =>
    rw [ldiagOf_succ, ldiagOf_succ, ← hT1 t₀ (le_trans (le_max_left _ _) ht₀),
      ← hT2 t₀ (le_trans (le_max_right _ _) ht₀), hb]
    simp
  | succ t ht ih =>
    rw [ldiagOf_succ, ldiagOf_succ, ← hT1 t (by omega), ← hT2 t (by omega), ih]

/-- **Where two left-edge rows can first differ.**  If `D` is the first left diagonal on which two
left-edge rows are not eventually equal, then `D ≥ 2` and diagonal `D − 1` (of either row) is
eventually white. -/
theorem first_difference_after_white {x y : Config} (hx : LeftEdgeAtZero x)
    (hy : LeftEdgeAtZero y) {D : ℕ}
    (hbelow : ∀ D' : ℕ, D' < D → EventuallyEq (ldiagOf x D') (ldiagOf y D'))
    (hD : ¬ EventuallyEq (ldiagOf x D) (ldiagOf y D)) :
    2 ≤ D ∧ EventuallyWhite (ldiagOf x ((D : ℤ) - 1)) := by
  have h0 : EventuallyEq (ldiagOf x 0) (ldiagOf y 0) :=
    ⟨0, fun t _ => by rw [ldiagOf_zero hx, ldiagOf_zero hy]⟩
  have h1 : EventuallyEq (ldiagOf x 1) (ldiagOf y 1) := ⟨1, fun t ht => by
    obtain ⟨n, rfl⟩ := Nat.exists_eq_add_of_le' ht
    rw [ldiagOf_one hx, ldiagOf_one hy]⟩
  have hD2 : 2 ≤ D := by
    by_contra hlt
    interval_cases D
    · exact hD (by simpa using h0)
    · exact hD (by simpa using h1)
  refine ⟨hD2, ?_⟩
  by_contra hw
  have e1 : ((D : ℤ) - 1) = ((D - 1 : ℕ) : ℤ) := by omega
  have e2 : ((D : ℤ) - 2) = ((D - 2 : ℕ) : ℤ) := by omega
  apply hD
  have := ldiagOf_sync (x := x) (y := y) (D := (D : ℤ)) (by rw [e1]; exact hbelow _ (by omega))
    (by rw [e2]; exact hbelow _ (by omega)) hw
  exact this

end GLM.Rule30
