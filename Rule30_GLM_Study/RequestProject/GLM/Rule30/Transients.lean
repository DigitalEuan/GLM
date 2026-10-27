module

public import RequestProject.GLM.Rule30.WhiteDiagonals

/-!
# Round 40: how long the left diagonals take to settle, and when the open bit matters

Round 39 left two questions about the eventually white left diagonals (To Do 45, 46): the
*parity* at each white diagonal, and the *open bit* (which of two eventual patterns the next
diagonal takes).  This file proves three things about them, for every family of one-bit machines
of the left-diagonal shape (`LeftMachine`) and then for Rule 30.

## 1. Transients grow at most linearly (`perFrom_linear`, `ldiag_perFrom_linear`)

If diagonals `0, …, N` all have eventual period `Q` and diagonals `0, 1` are `Q`-periodic from
time `T₀`, then diagonal `D ≤ N` is `Q`-periodic from time `T₀ + D * Q`.  The step
(`perFrom_step`): a diagonal settles at most `Q` steps after its two outer neighbours, because
either the nearer neighbour shows a black cell within one period (a reset), or it is white for
ever and the diagonal settles at once.

For the Rule 30 seed: for every `N` there is an `m` such that every left diagonal `D < N` is
`2 ^ m`-periodic from time `1 + D * 2 ^ m` (`ldiag_perFrom_linear`).  So the open bit at a white
diagonal `w` is read off at a single, explicit time: running the band of width `w + 2` for about
`(w + 2) * Q` steps decides it.  (Before this, the only bound was the trivial `2 ^ (w + 2)`.)

## 2. At an odd white diagonal the open bit does not matter (`shift_sync`,
`next_white_independent_of_odd_bit`)

After an eventually white diagonal the next diagonal is fixed only up to complement.  When the
outer neighbour of the white diagonal has **odd** parity over its period `Q`, the complement is a
time shift by `Q` (`odd_white_complement_is_shift`).  The left-diagonal law commutes with time
shifts, so the two choices give the same diagonals up to that time shift, and in particular the
same *next* white diagonal.  So only **even** white diagonals branch.  For two left-edge rows of
Rule 30 this sharpens Round 38's `first_difference_after_white`: their diagonals, up to a time
shift, can only part company after an even white diagonal (`ldiagOf_shift_sync_after_odd_white`).

All results use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

/-- `s` is `Q`-periodic from time `T` on. -/
def PerFrom (s : ℕ → Bool) (Q T : ℕ) : Prop := ∀ t ≥ T, s (t + Q) = s t

theorem PerFrom.mono {s : ℕ → Bool} {Q T T' : ℕ} (h : PerFrom s Q T) (hT : T ≤ T') :
    PerFrom s Q T' := fun t ht => h t (le_trans hT ht)

theorem PerFrom.evPer {s : ℕ → Bool} {Q T : ℕ} (h : PerFrom s Q T) : EvPer s Q := ⟨T, h⟩

section Machine

variable {u v : ℕ → ℕ → Bool}

/-- A `Q`-periodic sequence that is white on one window of length `Q` is white for ever after. -/
theorem white_of_window {s : ℕ → Bool} {Q T : ℕ} (hQ : 0 < Q) (hs : PerFrom s Q T)
    (hw : ∀ t, T ≤ t → t < T + Q → s t = false) : ∀ t ≥ T, s t = false := by
  intro t
  induction t using Nat.strong_induction_on with
  | _ t ih =>
    intro ht
    by_cases hlt : t < T + Q
    · exact hw t ht hlt
    · obtain ⟨t', rfl⟩ : ∃ t', t = t' + Q := ⟨t - Q, by omega⟩
      rw [hs t' (by omega)]
      exact ih t' (by omega) (by omega)

/-- **One step of settling.**  If diagonals `D` and `D + 1` are `Q`-periodic from `T`, and
diagonal `D + 2` has eventual period `Q`, then diagonal `D + 2` is `Q`-periodic from `T + Q`. -/
theorem perFrom_step (hm : LeftMachine u) {D Q T : ℕ} (hQ : 0 < Q)
    (ha : PerFrom (u D) Q T) (hb : PerFrom (u (D + 1)) Q T) (hc : EvPer (u (D + 2)) Q) :
    PerFrom (u (D + 2)) Q (T + Q) := by
  have hu : ∀ t, u (D + 2) (t + 1) = xor (u D t) (u (D + 1) t || u (D + 2) t) := hm D
  by_cases hex : ∃ t₀, T ≤ t₀ ∧ t₀ < T + Q ∧ u (D + 1) t₀ = true
  · obtain ⟨t₀, h1, h2, h3⟩ := hex
    exact PerFrom.mono (one_bit_reset hu ha hb h1 h3) (by omega)
  · push_neg at hex
    have hw : ∀ t ≥ T, u (D + 1) t = false :=
      white_of_window hQ hb fun t h1 h2 => by simpa using hex t h1 h2
    cases hp : parityOn (u D) T Q
    · have := one_bit_white_period hu ha hw
      refine PerFrom.mono (fun t ht => ?_) (Nat.le_add_right T Q)
      rw [this t ht, hp]; simp
    · exact absurd hc (one_bit_doubles hu ha hw hp).2.1

/-- **Transients grow at most linearly.**  If diagonals `0, …, N` have eventual period `Q > 0`
and diagonals `0` and `1` are `Q`-periodic from `T₀`, then each diagonal `D ≤ N` is
`Q`-periodic from `T₀ + D * Q`. -/
theorem perFrom_linear (hm : LeftMachine u) {N Q T₀ : ℕ} (hQ : 0 < Q)
    (hper : ∀ D, D ≤ N → EvPer (u D) Q) (h0 : PerFrom (u 0) Q T₀) (h1 : PerFrom (u 1) Q T₀) :
    ∀ D, D ≤ N → PerFrom (u D) Q (T₀ + D * Q) := by
  intro D
  induction D using Nat.strong_induction_on with
  | _ D ih =>
    intro hD
    match D, ih, hD with
    | 0, _, _ => simpa using h0
    | 1, _, _ => exact h1.mono (by omega)
    | D + 2, ih, hD =>
      have ha := (ih D (by omega) (by omega)).mono
        (show T₀ + D * Q ≤ T₀ + (D + 1) * Q by nlinarith)
      have hb := ih (D + 1) (by omega) (by omega)
      have := perFrom_step hm hQ ha hb (hper (D + 2) hD)
      convert this using 1; ring

/-- Time shifts of a left machine are left machines. -/
theorem LeftMachine.shift (hm : LeftMachine u) (k : ℕ) : LeftMachine (fun D t => u D (t + k)) := by
  intro D t
  simp only
  rw [show t + 1 + k = (t + k) + 1 by ring, hm]

/-- **Two-machine synchronisation.**  If two left machines eventually agree on diagonals `j` and
`j + 1`, and diagonal `j + 1` of the first is not eventually white, they eventually agree on
diagonal `j + 2`. -/
theorem sync_two (hu : LeftMachine u) (hv : LeftMachine v) {j : ℕ}
    (h0 : EventuallyEq (u j) (v j)) (h1 : EventuallyEq (u (j + 1)) (v (j + 1)))
    (hnw : ¬ EventuallyWhite (u (j + 1))) : EventuallyEq (u (j + 2)) (v (j + 2)) := by
  obtain ⟨T0, hT0⟩ := h0
  obtain ⟨T1, hT1⟩ := h1
  obtain ⟨t₀, ht₀, hbl⟩ := exists_black_after hnw (max T0 T1)
  refine ⟨t₀ + 1, fun t ht => ?_⟩
  induction t, ht using Nat.le_induction with
  | base =>
    rw [hu, hv, ← hT0 t₀ (le_trans (le_max_left _ _) ht₀),
      ← hT1 t₀ (le_trans (le_max_right _ _) ht₀), hbl]
    simp
  | succ t ht ih =>
    rw [hu, hv, ← hT0 t (by omega), ← hT1 t (by omega), ih]

/-- Eventual whiteness is invariant under time shift and eventual equality. -/
theorem eventuallyWhite_shift_iff {s s' : ℕ → Bool} {k : ℕ}
    (h : EventuallyEq (fun t => s (t + k)) s') : EventuallyWhite s ↔ EventuallyWhite s' := by
  obtain ⟨T', hT'⟩ := h
  constructor
  · rintro ⟨T, hT⟩
    exact ⟨max T T', fun t ht => by
      rw [← hT' t (le_of_max_le_right ht)]; exact hT _ (by omega)⟩
  · rintro ⟨T, hT⟩
    refine ⟨T + T' + k, fun t ht => ?_⟩
    have := hT' (t - k) (by omega)
    simp only at this
    rw [show t - k + k = t by omega] at this
    rw [this]; exact hT _ (by omega)

/-- **Shift synchronisation.**  If `v` agrees eventually with `u` shifted by `k` on diagonals `j`
and `j + 1`, the agreement persists along every white-free stretch of `u` beyond `j`, up to and
including the first eventually white diagonal. -/
theorem shift_sync (hu : LeftMachine u) (hv : LeftMachine v) {j k : ℕ}
    (h0 : EventuallyEq (fun t => u j (t + k)) (v j))
    (h1 : EventuallyEq (fun t => u (j + 1) (t + k)) (v (j + 1))) :
    ∀ n, (∀ i, j + 1 ≤ i → i ≤ j + n → ¬ EventuallyWhite (u i)) →
      EventuallyEq (fun t => u (j + n + 1) (t + k)) (v (j + n + 1)) := by
  have hu' := hu.shift k
  have key : ∀ n, (∀ i, j + 1 ≤ i → i ≤ j + n → ¬ EventuallyWhite (u i)) →
      EventuallyEq (fun t => u (j + n) (t + k)) (v (j + n)) ∧
      EventuallyEq (fun t => u (j + n + 1) (t + k)) (v (j + n + 1)) := by
    intro n
    induction n with
    | zero => intro _; exact ⟨h0, h1⟩
    | succ n ih =>
      intro hnw
      obtain ⟨ha, hb⟩ := ih fun i h1 h2 => hnw i h1 (by omega)
      refine ⟨hb, ?_⟩
      have hnw' : ¬ EventuallyWhite (fun t => u (j + n + 1) (t + k)) := by
        rw [← eventuallyWhite_shift_iff (k := k) ⟨0, fun t _ => rfl⟩]
        exact hnw (j + n + 1) (by omega) (by omega)
      exact sync_two (u := fun D t => u D (t + k)) hu' hv ha hb hnw'
  exact fun n h => (key n h).2

/-- **At an odd white diagonal the complement is a time shift.**  Two solutions `d`, `d'` of
`d (t + 1) = a t xor d t` driven by an `a` of period `Q` and odd parity are eventually equal or
eventually related by the shift `Q`. -/
theorem odd_white_complement_is_shift {a d d' : ℕ → Bool} {Q T : ℕ}
    (ha : PerFrom a Q T) (hodd : parityOn a T Q = true)
    (hd : ∀ t ≥ T, d (t + 1) = xor (a t) (d t)) (hd' : ∀ t ≥ T, d' (t + 1) = xor (a t) (d' t)) :
    EventuallyEq d d' ∨ EventuallyEq (fun t => d (t + Q)) d' := by
  -- the difference of two solutions is constant
  have hconst : ∀ t ≥ T, xor (d t) (d' t) = xor (d T) (d' T) := by
    intro t ht
    induction t, ht using Nat.le_induction with
    | base => rfl
    | succ t ht ih =>
      rw [hd t ht, hd' t ht, ← ih]
      cases a t <;> cases d t <;> cases d' t <;> rfl
  -- one period of `d` advances by the (odd) parity, i.e. complements
  have hrun : ∀ t ≥ T, ∀ n, d (t + n) = xor (d t) (parityOn a t n) := by
    intro t ht n
    induction n with
    | zero => simp [parityOn]
    | succ n ih =>
      rw [← add_assoc, hd _ (by omega), ih]
      simp only [parityOn]
      cases d t <;> cases parityOn a t n <;> cases a (t + n) <;> rfl
  have hanti : ∀ t ≥ T, d (t + Q) = !d t := by
    intro t ht
    rw [hrun t ht Q, parityOn_shift ha t ht, hodd]
    cases d t <;> rfl
  cases hT : xor (d T) (d' T)
  · left
    refine ⟨T, fun t ht => ?_⟩
    have := hconst t ht
    rw [hT] at this
    cases h1 : d t <;> cases h2 : d' t <;> simp_all
  · right
    refine ⟨T, fun t ht => ?_⟩
    have := hconst t ht
    rw [hT] at this
    simp only
    rw [hanti t ht]
    cases h1 : d t <;> cases h2 : d' t <;> simp_all

/-- **The next white diagonal does not depend on an odd bit.**  Let `u`, `v` be left machines
which eventually agree on diagonal `w`, both have diagonal `w + 1` white from `T`, and suppose
diagonal `w` of `u` is `Q`-periodic from `T` with **odd** parity.  Then for some shift `k`, `v`
agrees eventually with `u` shifted by `k` on every diagonal up to and including the first
eventually white diagonal of `u` beyond `w + 1`; in particular the two machines have the same
eventually white diagonals on that stretch. -/
theorem next_white_independent_of_odd_bit (hu : LeftMachine u) (hv : LeftMachine v)
    {w Q T : ℕ} (hwq : PerFrom (u w) Q T) (hodd : parityOn (u w) T Q = true)
    (hwe : ∀ t ≥ T, v w t = u w t)
    (hu1 : ∀ t ≥ T, u (w + 1) t = false) (hv1 : ∀ t ≥ T, v (w + 1) t = false) :
    ∃ k, ∀ n, (∀ i, w + 2 ≤ i → i ≤ w + 1 + n → ¬ EventuallyWhite (u i)) →
      EventuallyEq (fun t => u (w + 2 + n) (t + k)) (v (w + 2 + n)) ∧
      (EventuallyWhite (u (w + 2 + n)) ↔ EventuallyWhite (v (w + 2 + n))) := by
  have hd : ∀ t ≥ T, u (w + 2) (t + 1) = xor (u w t) (u (w + 2) t) := by
    intro t ht; rw [hu, hu1 t ht]; simp
  have hd' : ∀ t ≥ T, v (w + 2) (t + 1) = xor (u w t) (v (w + 2) t) := by
    intro t ht; rw [hv, hv1 t ht, hwe t ht]; simp
  have hk : ∃ k, EventuallyEq (fun t => u (w + 2) (t + k)) (v (w + 2)) := by
    rcases odd_white_complement_is_shift hwq hodd hd hd' with h | h
    · exact ⟨0, by simpa using h⟩
    · exact ⟨Q, h⟩
  obtain ⟨k, h1⟩ := hk
  have h0 : EventuallyEq (fun t => u (w + 1) (t + k)) (v (w + 1)) :=
    ⟨T, fun t ht => by simp only; rw [hu1 _ (by omega), hv1 t ht]⟩
  refine ⟨k, fun n hnw => ?_⟩
  have := shift_sync hu hv (j := w + 1) (k := k) h0 h1 n
    (fun i hi1 hi2 => hnw i (by omega) (by omega))
  rw [show w + 1 + n + 1 = w + 2 + n by ring] at this
  exact ⟨this, eventuallyWhite_shift_iff this⟩

/-! ### 3. The doubling is read two diagonals further out -/

/-- Parity of the number of black cells of `s` at the **even** offsets `T, T + 2, …` of the
window `[T, T + n)`. -/
def evenParityOn (s : ℕ → Bool) (T : ℕ) : ℕ → Bool
  | 0 => false
  | n + 1 => xor (evenParityOn s T n) (if n % 2 = 0 then s (T + n) else false)

/-- If `a (t + 1) = e t xor a t` from time `T` on, the parity of `a` over a window of **even**
length `n` equals the parity of `e` at the even offsets of that window. -/
theorem parityOn_eq_evenParityOn {a e : ℕ → Bool} {T : ℕ}
    (ha : ∀ t ≥ T, a (t + 1) = xor (e t) (a t)) {n : ℕ} (hn : n % 2 = 0) :
    parityOn a T n = evenParityOn e T n := by
  have hrun : ∀ n, a (T + n) = xor (a T) (parityOn e T n) := by
    intro n
    induction n with
    | zero => simp [parityOn]
    | succ n ih =>
      rw [← add_assoc, ha _ (by omega), ih]
      simp only [parityOn]
      cases a T <;> cases parityOn e T n <;> cases e (T + n) <;> rfl
  have key : ∀ n, parityOn a T n = if n % 2 = 0 then evenParityOn e T n
      else xor (xor (a T) (parityOn e T n)) (evenParityOn e T n) := by
    intro n
    induction n with
    | zero => simp [parityOn, evenParityOn]
    | succ n ih =>
      simp only [parityOn, evenParityOn, hrun n]
      rcases Nat.mod_two_eq_zero_or_one n with h | h
      · have h' : (n + 1) % 2 = 1 := by omega
        simp only [ih, h, h', if_true, one_ne_zero, if_false]
        cases a T <;> cases parityOn e T n <;> cases e (T + n) <;>
          cases evenParityOn e T n <;> rfl
      · have h' : (n + 1) % 2 = 0 := by omega
        simp only [ih, h, h', if_true, one_ne_zero, if_false]
        cases a T <;> cases parityOn e T n <;> cases e (T + n) <;>
          cases evenParityOn e T n <;> rfl
  rw [key n, if_pos hn]

/-- **The doubling is read two diagonals out.**  If diagonals `D + 1` and `D + 2` agree from time
`T` on (by `white_iff_coincide` this happens eventually exactly when diagonal `D + 3` is
eventually white), then for every even `Q` the parity of diagonal `D + 2` over `[T, T + Q)` is
the parity of diagonal `D` at the even offsets of that window.  So whether the period doubles
after the white diagonal `D + 3` (`ldiag_doubles`) is decided by diagonal `D`. -/
theorem doubling_read_two_out {u : ℕ → ℕ → Bool} (hm : LeftMachine u) {D Q T : ℕ}
    (hQ : Q % 2 = 0) (hc : ∀ t ≥ T, u (D + 1) t = u (D + 2) t) :
    parityOn (u (D + 2)) T Q = evenParityOn (u D) T Q := by
  refine parityOn_eq_evenParityOn (fun t ht => ?_) hQ
  rw [hm, hc t ht]
  cases u (D + 2) t <;> rfl

/-! ### 4. Shift-equivalence of two machines, extended one diagonal at a time -/

theorem parityOn_shift_arg (s : ℕ → Bool) (k T n : ℕ) :
    parityOn (fun t => s (t + k)) T n = parityOn s (T + k) n := by
  induction n with
  | zero => rfl
  | succ n ih => simp only [parityOn, ih, show T + n + k = T + k + n by ring]

/-- **Extension past a non-white diagonal.**  If `v` agrees eventually with `u` shifted by `k` on
all diagonals `≤ D + 1`, and diagonal `D + 1` of `u` is not eventually white, the agreement
extends to diagonal `D + 2`. -/
theorem shift_equiv_extend (hu : LeftMachine u) (hv : LeftMachine v) {k D : ℕ}
    (hall : ∀ D', D' ≤ D + 1 → EventuallyEq (fun t => u D' (t + k)) (v D'))
    (hnw : ¬ EventuallyWhite (u (D + 1))) :
    ∀ D', D' ≤ D + 2 → EventuallyEq (fun t => u D' (t + k)) (v D') := by
  intro D' hD'
  rcases Nat.lt_or_ge D' (D + 2) with h | h
  · exact hall D' (by omega)
  · obtain rfl : D' = D + 2 := by omega
    have hnw' : ¬ EventuallyWhite (fun t => u (D + 1) (t + k)) := by
      rw [← eventuallyWhite_shift_iff (k := k) ⟨0, fun t _ => rfl⟩]; exact hnw
    exact sync_two (u := fun D t => u D (t + k)) (hu.shift k) hv (hall D (by omega))
      (hall (D + 1) le_rfl) hnw'

/-- **Extension past an odd white diagonal.**  If `v` agrees eventually with `u` shifted by `k`
on all diagonals `≤ D + 1`, diagonal `D + 1` of `u` is white from `T`, diagonal `D` is
`Q`-periodic from `T` with odd parity, and all diagonals `≤ D + 1` have eventual period `Q`,
then for a new shift (`k` or `k + Q`) the agreement extends to diagonal `D + 2`. -/
theorem shift_equiv_extend_odd (hu : LeftMachine u) (hv : LeftMachine v) {k D Q T : ℕ}
    (hall : ∀ D', D' ≤ D + 1 → EventuallyEq (fun t => u D' (t + k)) (v D'))
    (hper : ∀ D', D' ≤ D + 1 → EvPer (u D') Q)
    (hDq : PerFrom (u D) Q T) (hodd : parityOn (u D) T Q = true)
    (hw : ∀ t ≥ T, u (D + 1) t = false) :
    ∃ k', ∀ D', D' ≤ D + 2 → EventuallyEq (fun t => u D' (t + k')) (v D') := by
  obtain ⟨Ta, hTa⟩ := hall D (by omega)
  obtain ⟨Tb, hTb⟩ := hall (D + 1) le_rfl
  set T' := max (max Ta Tb) T with hT'
  have hd : ∀ t ≥ T', u (D + 2) (t + k + 1) = xor (u D (t + k)) (u (D + 2) (t + k)) := by
    intro t ht
    rw [hu, hw (t + k) (by omega)]; simp
  have hd' : ∀ t ≥ T', v (D + 2) (t + 1) = xor (u D (t + k)) (v (D + 2) t) := by
    intro t ht
    have h1 := hTa t (by omega)
    have h2 := hTb t (by omega)
    simp only at h1 h2
    rw [hv, ← h1, ← h2, hw (t + k) (by omega)]; simp
  have ha : PerFrom (fun t => u D (t + k)) Q T' := fun t ht => by
    simp only; rw [show t + Q + k = (t + k) + Q by ring, hDq (t + k) (by omega)]
  have hodd' : parityOn (fun t => u D (t + k)) T' Q = true := by
    rw [parityOn_shift_arg, parityOn_shift hDq (T' + k) (by omega), hodd]
  rcases odd_white_complement_is_shift (d := fun t => u (D + 2) (t + k)) (d' := v (D + 2)) ha hodd'
    (fun t ht => by simp only; rw [show t + 1 + k = t + k + 1 by ring]; exact hd t ht) hd' with
    h | h
  · refine ⟨k, fun D' hD' => ?_⟩
    rcases Nat.lt_or_ge D' (D + 2) with h' | h'
    · exact hall D' (by omega)
    · obtain rfl : D' = D + 2 := by omega
      exact h
  · refine ⟨k + Q, fun D' hD' => ?_⟩
    rcases Nat.lt_or_ge D' (D + 2) with h' | h'
    · obtain ⟨Tp, hTp⟩ := hper D' (by omega)
      obtain ⟨Tq, hTq⟩ := hall D' (by omega)
      refine ⟨max Tp Tq, fun t ht => ?_⟩
      simp only at hTq ⊢
      rw [show t + (k + Q) = (t + k) + Q by ring, hTp (t + k) (by omega)]
      exact hTq t (by omega)
    · obtain rfl : D' = D + 2 := by omega
      obtain ⟨T2, hT2⟩ := h
      exact ⟨T2, fun t ht => by
        have := hT2 t ht; simp only at this ⊢; rw [← this]; congr 1; ring⟩

end Machine

/-! ## Rule 30 -/

/-- **Rule 30, any left-edge row: transients grow at most linearly.**  If left diagonals
`0, …, N` have eventual period `Q > 0`, then left diagonal `D ≤ N` is `Q`-periodic from time
`1 + D * Q`. -/
theorem ldiagOf_perFrom_linear {x : Config} (hx : LeftEdgeAtZero x) {N Q : ℕ} (hQ : 0 < Q)
    (hper : ∀ D : ℕ, D ≤ N → EvPer (ldiagOf x D) Q) :
    ∀ D : ℕ, D ≤ N → PerFrom (ldiagOf x D) Q (1 + D * Q) := by
  refine perFrom_linear (u := fun D t => ldiagOf x (D : ℤ) t) (ldiagOf_leftMachine x) hQ hper
    (fun t _ => ?_) (fun t ht => ?_)
  · simp [ldiagOf_zero hx]
  · obtain ⟨n, rfl⟩ := Nat.exists_eq_add_of_le' ht
    simp only [Nat.cast_one]
    rw [show n + 1 + Q = (n + Q) + 1 by ring, ldiagOf_one hx, ldiagOf_one hx]

/-- **Rule 30 seed: explicit settling times.**  For every `N` there is an `m` such that every left
diagonal `D < N` is `2 ^ m`-periodic from time `1 + D * 2 ^ m`.  So all eventual data of the left
diagonals below `N` (whiteness, parity, the open bit) is read from the finite band of width `N`
run for `N * 2 ^ m + 1` steps. -/
theorem ldiag_perFrom_linear (N : ℕ) :
    ∃ m, ∀ D : ℕ, D < N → PerFrom (ldiag D) (2 ^ m) (1 + D * 2 ^ m) := by
  obtain ⟨m, hm⟩ := ldiag_common_period N
  refine ⟨m, fun D hD => ?_⟩
  exact ldiagOf_perFrom_linear seed_leftEdgeAtZero (N := N - 1) (by positivity)
    (fun D' hD' => hm D' (by omega)) D (by omega)

/-- **Rule 30: only even white diagonals branch.**  Let `x`, `y` be rows whose left
diagonals `w` eventually agree, with left diagonal `w + 1` eventually white in both, and suppose
diagonal `w` of `x` has eventual period `Q` with **odd** parity.  Then up to one time shift `k`,
the left diagonals of `y` agree eventually with those of `x` from `w + 2` up to and including
the next eventually white diagonal of `x`. -/
theorem ldiagOf_shift_sync_after_odd_white {x y : Config} {w Q T : ℕ}
    (hwq : PerFrom (ldiagOf x w) Q T) (hodd : parityOn (ldiagOf x w) T Q = true)
    (hwe : ∀ t ≥ T, ldiagOf y w t = ldiagOf x w t)
    (hx1 : ∀ t ≥ T, ldiagOf x ((w + 1 : ℕ) : ℤ) t = false)
    (hy1 : ∀ t ≥ T, ldiagOf y ((w + 1 : ℕ) : ℤ) t = false) :
    ∃ k, ∀ n, (∀ i : ℕ, w + 2 ≤ i → i ≤ w + 1 + n → ¬ EventuallyWhite (ldiagOf x i)) →
      EventuallyEq (fun t => ldiagOf x ((w + 2 + n : ℕ) : ℤ) (t + k))
        (ldiagOf y ((w + 2 + n : ℕ) : ℤ)) ∧
      (EventuallyWhite (ldiagOf x ((w + 2 + n : ℕ) : ℤ)) ↔
        EventuallyWhite (ldiagOf y ((w + 2 + n : ℕ) : ℤ))) :=
  next_white_independent_of_odd_bit (u := fun D t => ldiagOf x (D : ℤ) t)
    (v := fun D t => ldiagOf y (D : ℤ) t) (ldiagOf_leftMachine x) (ldiagOf_leftMachine y)
    hwq hodd hwe hx1 hy1

/-- **Rule 30: the doubling is read two diagonals out.**  If left diagonals `D + 1` and `D + 2`
agree from time `T` on, then for even `Q` the parity of left diagonal `D + 2` over
`[T, T + Q)` equals the parity of left diagonal `D` at the even offsets of that window. -/
theorem ldiag_doubling_read_two_out {D Q T : ℕ} (hQ : Q % 2 = 0)
    (hc : ∀ t ≥ T, ldiag ((D + 1 : ℕ) : ℤ) t = ldiag ((D + 2 : ℕ) : ℤ) t) :
    parityOn (ldiag ((D + 2 : ℕ) : ℤ)) T Q = evenParityOn (ldiag (D : ℤ)) T Q :=
  doubling_read_two_out (u := fun D t => ldiag (D : ℤ) t) ldiag_leftMachine hQ hc

end GLM.Rule30
