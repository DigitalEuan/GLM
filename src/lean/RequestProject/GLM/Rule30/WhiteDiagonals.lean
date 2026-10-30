module

public import RequestProject.GLM.Rule30.LeftDiagonalPeriods

/-!
# Round 39: where white diagonals come from, and the regime dichotomy

Round 38 proved that the periods of the left diagonals can only change one step past an
eventually white diagonal (`ldiag_doubles`).  The Round 39 hypothesis engine asked the next
question: *which* diagonals are eventually white?  Its miner found, on all data, an exact local
law ("diagonal `D + 2` is eventually white exactly when diagonals `D` and `D + 1` eventually
coincide"), and its regime analysis found that between two white diagonals the eventual
patterns evolve by an **injective** map on a finite set.  This file proves both, for every
family of one-bit machines of the Rule 30 left-diagonal shape, and then specialises to Rule 30.

## The machine family

`u : ℕ → ℕ → Bool` with `u (D + 2) (t + 1) = u D t xor (u (D + 1) t ∨ u (D + 2) t)`
(`LeftMachine u`).  The left diagonals of Rule 30 from any row with a left edge are such a family
(`ldiagOf_leftMachine`).

## Results (all proved, every index)

* `white_iff_coincide` : if `u 0` is not eventually white, then `u (D + 2)` is eventually white
  **iff** `u D` and `u (D + 1)` are eventually equal.
* `no_two_consecutive_white` : two adjacent diagonals are never both eventually white.
* `regime_finite_check` : **a finite check decides each regime.**  If `u D₀`, `u (D₀ + 1)` have
  eventual period `Q > 0` and none of the diagonals `D₀ + 1, …, D₀ + 4 ^ Q + 1` is eventually
  white, then **no** diagonal beyond `D₀` is eventually white.
* `regime_periodic` : if no diagonal beyond `D₀` is eventually white, the eventual diagonals are
  periodic in `D` from `D₀` on, with a period `P` with `0 < P ≤ 4 ^ Q`.

* `white_after_white` : **there is no last white diagonal**: after an eventually white diagonal
  another one comes within `4 ^ Q + 1` diagonals (a white-free future would make the diagonals
  periodic in `D` back to the white diagonal itself).

For Rule 30:

* `ldiag_infinitely_many_white` : **Rule 30 has infinitely many eventually white left
  diagonals** (Round 38 knew seven, and had only "unbounded periods ⇒ infinitely many").
* `ldiag_white_after_white` : the gap after a white diagonal is at most `4 ^ Q + 1`.
* `ldiag_periods_unbounded_iff` : the periods are unbounded **iff** for every `m` some white
  diagonal has an outer neighbour of odd parity over `2 ^ m` (`OddWhiteAt`).  So the open
  question (To Do 45) is now only about the *parities* of the white diagonals.

Also for Rule 30 (`ldiag_white_iff_coincide`, `ldiag_no_two_consecutive_white`,
`ldiag_regime_finite_check`, `ldiag_periodic_in_D_of_finitely_many_white`) this gives a sharp
form of the open question "are the left-diagonal periods unbounded?": if only finitely many
left diagonals are eventually white, the whole left side is eventually periodic in `D` as well
as in `t`; and each regime can be closed by a finite (if huge) computation.

All results use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

/-- A family of one-bit machines with the shape of the Rule 30 left diagonals. -/
def LeftMachine (u : ℕ → ℕ → Bool) : Prop :=
  ∀ D t, u (D + 2) (t + 1) = xor (u D t) (u (D + 1) t || u (D + 2) t)

section Machine

variable {u : ℕ → ℕ → Bool}

theorem EventuallyEq.symm' {s s' : ℕ → Bool} (h : EventuallyEq s s') : EventuallyEq s' s := by
  obtain ⟨T, hT⟩ := h
  exact ⟨T, fun t ht => (hT t ht).symm⟩

theorem EventuallyEq.trans' {s s' s'' : ℕ → Bool} (h : EventuallyEq s s')
    (h' : EventuallyEq s' s'') : EventuallyEq s s'' := by
  obtain ⟨T, hT⟩ := h
  obtain ⟨T', hT'⟩ := h'
  exact ⟨max T T', fun t ht => (hT t (le_of_max_le_left ht)).trans
    (hT' t (le_of_max_le_right ht))⟩

theorem EventuallyWhite.of_eventuallyEq {s s' : ℕ → Bool} (hw : EventuallyWhite s)
    (h : EventuallyEq s s') : EventuallyWhite s' := by
  obtain ⟨T, hT⟩ := hw
  obtain ⟨T', hT'⟩ := h
  exact ⟨max T T', fun t ht => by
    rw [← hT' t (le_of_max_le_right ht)]; exact hT t (le_of_max_le_left ht)⟩

/-- A sequence that is not eventually white is black at arbitrarily late times. -/
theorem exists_black_after {s : ℕ → Bool} (hw : ¬ EventuallyWhite s) (T : ℕ) :
    ∃ t ≥ T, s t = true := by
  by_contra hne
  push_neg at hne
  exact hw ⟨T, fun t ht => by simpa using hne t ht⟩

/-- An eventually white diagonal forces its two outer neighbours to coincide eventually. -/
theorem coincide_of_white (hm : LeftMachine u) {D : ℕ} (hw : EventuallyWhite (u (D + 2))) :
    EventuallyEq (u D) (u (D + 1)) := by
  obtain ⟨T, hT⟩ := hw
  refine ⟨T, fun t ht => ?_⟩
  have h1 := hm D t
  rw [hT t ht, hT (t + 1) (by omega)] at h1
  generalize u D t = a at h1 ⊢
  generalize u (D + 1) t = b at h1 ⊢
  cases a <;> cases b <;> simp at h1 ⊢

/-- If the two outer neighbours coincide eventually and the outermost is not eventually white,
the diagonal is eventually white. -/
theorem white_of_coincide (hm : LeftMachine u) {D : ℕ} (he : EventuallyEq (u D) (u (D + 1)))
    (hnw : ¬ EventuallyWhite (u D)) : EventuallyWhite (u (D + 2)) := by
  obtain ⟨T, hT⟩ := he
  obtain ⟨t₀, ht₀, hb⟩ := exists_black_after hnw T
  refine ⟨t₀ + 1, fun t ht => ?_⟩
  induction t, ht using Nat.le_induction with
  | base => rw [hm, ← hT t₀ ht₀, hb]; simp
  | succ t ht ih => rw [hm, ← hT t (by omega), ih]; simp

/-- **Two adjacent diagonals are never both eventually white** (when the edge is not). -/
theorem no_two_consecutive_white (hm : LeftMachine u) (h0 : ¬ EventuallyWhite (u 0)) :
    ∀ D, ¬ (EventuallyWhite (u D) ∧ EventuallyWhite (u (D + 1))) := by
  intro D
  induction D with
  | zero => exact fun h => h0 h.1
  | succ D ih =>
    rintro ⟨h1, h2⟩
    exact ih ⟨(h1.of_eventuallyEq (coincide_of_white hm h2).symm'), h1⟩

/-- **The white-diagonal criterion.**  Diagonal `D + 2` is eventually white exactly when the two
diagonals outside it eventually coincide. -/
theorem white_iff_coincide (hm : LeftMachine u) (h0 : ¬ EventuallyWhite (u 0)) (D : ℕ) :
    EventuallyWhite (u (D + 2)) ↔ EventuallyEq (u D) (u (D + 1)) := by
  refine ⟨coincide_of_white hm, fun he => white_of_coincide hm he fun hD => ?_⟩
  exact no_two_consecutive_white hm h0 D ⟨hD, hD.of_eventuallyEq he⟩

/-- Forward synchronisation inside one family: if the inputs of the machines at `D + 2` and
`D' + 2` coincide eventually and the reset input is not eventually white, so do the outputs. -/
theorem sync_forward (hm : LeftMachine u) {D D' : ℕ} (h0 : EventuallyEq (u D) (u D'))
    (h1 : EventuallyEq (u (D + 1)) (u (D' + 1))) (hnw : ¬ EventuallyWhite (u (D + 1))) :
    EventuallyEq (u (D + 2)) (u (D' + 2)) := by
  obtain ⟨T0, hT0⟩ := h0
  obtain ⟨T1, hT1⟩ := h1
  obtain ⟨t₀, ht₀, hb⟩ := exists_black_after hnw (max T0 T1)
  refine ⟨t₀ + 1, fun t ht => ?_⟩
  induction t, ht using Nat.le_induction with
  | base =>
    rw [hm, hm, ← hT0 t₀ (le_of_max_le_left ht₀), ← hT1 t₀ (le_of_max_le_right ht₀), hb]
    simp
  | succ t ht ih =>
    rw [hm, hm, ← hT0 t (by omega), ← hT1 t (by omega), ih]

/-- Backward determinism: the machine can be run backwards (left permutivity of Rule 30). -/
theorem sync_backward (hm : LeftMachine u) {D D' : ℕ}
    (h1 : EventuallyEq (u (D + 1)) (u (D' + 1))) (h2 : EventuallyEq (u (D + 2)) (u (D' + 2))) :
    EventuallyEq (u D) (u D') := by
  obtain ⟨T1, hT1⟩ := h1
  obtain ⟨T2, hT2⟩ := h2
  refine ⟨max T1 T2, fun t ht => ?_⟩
  have e := hm D t
  have e' := hm D' t
  rw [hT2 (t + 1) (by omega), hT2 t (le_of_max_le_right ht), hT1 t (le_of_max_le_left ht)] at e
  have h := e.symm.trans e'
  generalize u D t = a at h ⊢
  generalize u D' t = b at h ⊢
  generalize (u (D' + 1) t || u (D' + 2) t) = c at h
  cases a <;> cases b <;> cases c <;> simp_all

/-- Eventual period propagates along a stretch of diagonals that are not eventually white. -/
theorem evPer_propagate (hm : LeftMachine u) {Q D₀ : ℕ} (h0 : EvPer (u D₀) Q)
    (h1 : EvPer (u (D₀ + 1)) Q) (M : ℕ)
    (hnw : ∀ D, D₀ + 1 ≤ D → D ≤ D₀ + M → ¬ EventuallyWhite (u D)) :
    ∀ n, n ≤ M → EvPer (u (D₀ + n)) Q ∧ EvPer (u (D₀ + n + 1)) Q := by
  intro n
  induction n with
  | zero => intro _; exact ⟨h0, h1⟩
  | succ n ih =>
    intro hn
    obtain ⟨ha, hb⟩ := ih (by omega)
    refine ⟨hb, ?_⟩
    obtain ⟨Ta, hTa⟩ := ha
    obtain ⟨Tb, hTb⟩ := hb
    obtain ⟨t₀, ht₀, hbl⟩ := exists_black_after (hnw (D₀ + n + 1) (by omega) (by omega))
      (max Ta Tb)
    have hm' : ∀ t, u (D₀ + n + 2) (t + 1) =
        xor (u (D₀ + n) t) (u (D₀ + n + 1) t || u (D₀ + n + 2) t) := hm (D₀ + n)
    exact ⟨t₀ + 1, one_bit_reset hm' (EvPer.mono_start hTa (le_max_left _ _))
      (EvPer.mono_start hTb (le_max_right _ _)) ht₀ hbl⟩

/-! ### Keys: eventually `Q`-periodic sequences form a finite set up to eventual equality -/

open Classical in
/-- The eventual pattern of `s` over one period `Q`, read after `s` has become periodic. -/
noncomputable def evKey (Q : ℕ) (s : ℕ → Bool) : Fin Q → Bool :=
  if h : EvPer s Q then fun i => s (Q * Classical.choose h + i) else fun _ => false

theorem evPer_shift {s : ℕ → Bool} {Q T : ℕ} (h : ∀ t ≥ T, s (t + Q) = s t) :
    ∀ t ≥ T, s t = s (Q * T + t % Q) := by
  intro t ht
  rcases Nat.eq_zero_or_pos Q with hQ | hQ
  · subst hQ; simp
  have hT : T ≤ Q * T := Nat.le_mul_of_pos_left T hQ
  -- both `t` and `Q * T + t % Q` are ≥ T and congruent mod Q
  have key : ∀ a ≥ T, ∀ k, s (a + k * Q) = s a := fun a ha k => periodic_mul h k a ha
  have hmod : t % Q + Q * (t / Q) = t := Nat.mod_add_div t Q
  by_cases hle : Q * T ≤ Q * (t / Q)
  · have := key (Q * T + t % Q) (by omega) (t / Q - T)
    rw [← this]; congr 1
    have : (t / Q - T) * Q = Q * (t / Q) - Q * T := by
      rw [Nat.sub_mul, mul_comm (t / Q), mul_comm T]
    omega
  · push_neg at hle
    have hlt : t / Q < T := lt_of_mul_lt_mul_left hle (Nat.zero_le _)
    have := key t ht (T - t / Q)
    rw [← this]; congr 1
    have : (T - t / Q) * Q = Q * T - Q * (t / Q) := by
      rw [Nat.sub_mul, mul_comm T, mul_comm (t / Q)]
    omega

theorem eventuallyEq_of_evKey {Q : ℕ} (hQ : 0 < Q) {s s' : ℕ → Bool} (hs : EvPer s Q)
    (hs' : EvPer s' Q) (hk : evKey Q s = evKey Q s') : EventuallyEq s s' := by
  set T := Classical.choose hs
  set T' := Classical.choose hs'
  have hT := Classical.choose_spec hs
  have hT' := Classical.choose_spec hs'
  have hk' : ∀ i : Fin Q, s (Q * T + i) = s' (Q * T' + i) := by
    intro i
    have := congrFun hk i
    simpa [evKey, hs, hs', T, T'] using this
  refine ⟨max T T', fun t ht => ?_⟩
  rw [evPer_shift hT t (le_of_max_le_left ht), evPer_shift hT' t (le_of_max_le_right ht)]
  exact hk' ⟨t % Q, Nat.mod_lt t hQ⟩

/-! ### The regime dichotomy -/

/-- Propagation of a repeat: if the pair of diagonals at `i` repeats at `i + P` (up to eventual
equality) and no diagonal in `(i, M)` is eventually white, the repeat persists up to `M`. -/
theorem repeat_propagate (hm : LeftMachine u) {i P M : ℕ}
    (h0 : EventuallyEq (u i) (u (i + P))) (h1 : EventuallyEq (u (i + 1)) (u (i + 1 + P)))
    (hnw : ∀ D, i + 1 ≤ D → D < M → ¬ EventuallyWhite (u D)) :
    ∀ n, i + n + 1 ≤ M → EventuallyEq (u (i + n)) (u (i + n + P)) ∧
      EventuallyEq (u (i + n + 1)) (u (i + n + 1 + P)) := by
  intro n
  induction n with
  | zero => intro _; simpa using ⟨h0, h1⟩
  | succ n ih =>
    intro hn
    obtain ⟨ha, hb⟩ := ih (by omega)
    refine ⟨by simpa [add_assoc] using hb, ?_⟩
    have := sync_forward hm ha (by simpa [add_right_comm] using hb)
      (hnw (i + n + 1) (by omega) (by omega))
    simpa [add_assoc, add_comm, add_left_comm] using this

/-- Pigeonhole: among `4 ^ Q + 1` consecutive pairs of `Q`-periodic diagonals two coincide. -/
theorem exists_repeat (hm : LeftMachine u) {Q D₀ : ℕ} (hQ : 0 < Q) (h0 : EvPer (u D₀) Q)
    (h1 : EvPer (u (D₀ + 1)) Q)
    (hnw : ∀ D, D₀ + 1 ≤ D → D ≤ D₀ + 4 ^ Q → ¬ EventuallyWhite (u D)) :
    ∃ i P, D₀ ≤ i ∧ 0 < P ∧ i + P ≤ D₀ + 4 ^ Q ∧ EventuallyEq (u i) (u (i + P)) ∧
      EventuallyEq (u (i + 1)) (u (i + 1 + P)) := by
  have hper := evPer_propagate hm h0 h1 (4 ^ Q) hnw
  let f : Fin (4 ^ Q + 1) → (Fin Q → Bool) × (Fin Q → Bool) :=
    fun n => (evKey Q (u (D₀ + n)), evKey Q (u (D₀ + n + 1)))
  have hcard : Fintype.card ((Fin Q → Bool) × (Fin Q → Bool)) < Fintype.card (Fin (4 ^ Q + 1)) := by
    simp only [Fintype.card_prod, Fintype.card_fun, Fintype.card_bool, Fintype.card_fin]
    rw [← mul_pow]; norm_num
  obtain ⟨a, b, hab, hfab⟩ := Fintype.exists_ne_map_eq_of_card_lt f hcard
  have key : ∀ a b : Fin (4 ^ Q + 1), a < b → f a = f b → ∃ i P, D₀ ≤ i ∧ 0 < P ∧
      i + P ≤ D₀ + 4 ^ Q ∧ EventuallyEq (u i) (u (i + P)) ∧
      EventuallyEq (u (i + 1)) (u (i + 1 + P)) := by
    intro a b hlt hf
    have ha := hper a (by omega)
    have hb := hper b (by omega)
    simp only [f, Prod.mk.injEq] at hf
    refine ⟨D₀ + a, b - a, by omega, by omega, by omega, ?_, ?_⟩
    · have e : D₀ + ↑a + (↑b - ↑a) = D₀ + ↑b := by omega
      rw [e]; exact eventuallyEq_of_evKey hQ ha.1 hb.1 hf.1
    · have e : D₀ + ↑a + 1 + (↑b - ↑a) = D₀ + ↑b + 1 := by omega
      rw [e]; exact eventuallyEq_of_evKey hQ ha.2 hb.2 hf.2
  rcases lt_or_gt_of_ne hab with h | h
  · exact key a b h hfab
  · exact key b a h hfab.symm

/-- **A finite check closes a regime.**  If diagonals `D₀` and `D₀ + 1` have eventual period
`Q > 0`, and none of the diagonals `D₀ + 1, …, D₀ + 4 ^ Q + 1` is eventually white, then no
diagonal beyond `D₀` is eventually white. -/
theorem regime_finite_check (hm : LeftMachine u) {Q D₀ : ℕ} (hQ : 0 < Q) (h0 : EvPer (u D₀) Q)
    (h1 : EvPer (u (D₀ + 1)) Q)
    (hnw : ∀ D, D₀ + 1 ≤ D → D ≤ D₀ + 4 ^ Q + 1 → ¬ EventuallyWhite (u D)) :
    ∀ D, D₀ + 1 ≤ D → ¬ EventuallyWhite (u D) := by
  obtain ⟨i, P, hi, hP, hiP, he0, he1⟩ :=
    exists_repeat hm hQ h0 h1 (fun D h h' => hnw D h (by omega))
  by_contra hcon
  push_neg at hcon
  have hex : ∃ m, D₀ + 1 ≤ m ∧ EventuallyWhite (u m) := by
    obtain ⟨m, hm1, hm2⟩ := hcon
    exact ⟨m, hm1, by simpa using hm2⟩
  classical
  let m := Nat.find hex
  have hmspec := Nat.find_spec hex
  have hmin : ∀ k, k < m → ¬ (D₀ + 1 ≤ k ∧ EventuallyWhite (u k)) := fun k hk => Nat.find_min hex hk
  have hbig : D₀ + 4 ^ Q + 1 < m := by
    by_contra hle; push_neg at hle
    exact hnw m hmspec.1 hle hmspec.2
  -- the repeat reaches index `m`
  have hrep := repeat_propagate hm he0 he1 (M := m) (fun D hD hDm h => hmin D hDm ⟨by omega, h⟩)
    (m - P - i) (by omega)
  have e : i + (m - P - i) + P = m := by omega
  rw [e] at hrep
  have hw : EventuallyWhite (u (i + (m - P - i))) := hmspec.2.of_eventuallyEq hrep.1.symm'
  exact hmin _ (by omega) ⟨by omega, hw⟩

/-- **Regime periodicity.**  If diagonals `D₀`, `D₀ + 1` have eventual period `Q > 0` and no
diagonal beyond `D₀` is eventually white, the eventual diagonals are periodic in `D` from `D₀`
on, with a period `0 < P ≤ 4 ^ Q`. -/
theorem regime_periodic (hm : LeftMachine u) {Q D₀ : ℕ} (hQ : 0 < Q) (h0 : EvPer (u D₀) Q)
    (h1 : EvPer (u (D₀ + 1)) Q) (hnw : ∀ D, D₀ + 1 ≤ D → ¬ EventuallyWhite (u D)) :
    ∃ P, 0 < P ∧ P ≤ 4 ^ Q ∧ ∀ D, D₀ ≤ D → EventuallyEq (u D) (u (D + P)) := by
  obtain ⟨i, P, hi, hP, hiP, he0, he1⟩ :=
    exists_repeat hm hQ h0 h1 (fun D h _ => hnw D h)
  refine ⟨P, hP, by omega, ?_⟩
  -- forward from `i`
  have fwd : ∀ n, EventuallyEq (u (i + n)) (u (i + n + P)) ∧
      EventuallyEq (u (i + n + 1)) (u (i + n + 1 + P)) := fun n =>
    repeat_propagate hm he0 he1 (M := i + n + 1) (fun D hD _ => hnw D (by omega)) n (by omega)
  -- backward from `i` down to `D₀`
  have bwd : ∀ k, k ≤ i - D₀ → EventuallyEq (u (i - k)) (u (i - k + P)) ∧
      EventuallyEq (u (i - k + 1)) (u (i - k + 1 + P)) := by
    intro k
    induction k with
    | zero => intro _; simpa using fwd 0
    | succ k ih =>
      intro hk
      obtain ⟨ha, hb⟩ := ih (by omega)
      have e1 : i - (k + 1) + 1 = i - k := by omega
      refine ⟨?_, by rw [e1]; exact ha⟩
      have h1' : EventuallyEq (u (i - (k + 1) + 1)) (u (i - (k + 1) + P + 1)) := by
        rw [e1, show i - (k + 1) + P + 1 = i - k + P by omega]; exact ha
      have h2' : EventuallyEq (u (i - (k + 1) + 2)) (u (i - (k + 1) + P + 2)) := by
        rw [show i - (k + 1) + 2 = i - k + 1 by omega,
          show i - (k + 1) + P + 2 = i - k + 1 + P by omega]; exact hb
      exact sync_backward hm h1' h2'
  intro D hD
  rcases le_or_gt i D with h | h
  · have := (fwd (D - i)).1
    rwa [show i + (D - i) = D by omega] at this
  · have := (bwd (i - D) (by omega)).1
    rwa [show i - (i - D) = D by omega] at this

/-- **There is no last white diagonal.**  After an eventually white diagonal `w` (with `u w`,
`u (w + 1)` of eventual period `Q > 0`) another eventually white diagonal comes within
`4 ^ Q + 1` steps.  Reason: by `regime_periodic`, a white-free future would make the diagonals
periodic in `D` back to `w` itself, so `w` would recur. -/
theorem white_after_white (hm : LeftMachine u) {Q w : ℕ} (hQ : 0 < Q) (h0 : EvPer (u w) Q)
    (h1 : EvPer (u (w + 1)) Q) (hw : EventuallyWhite (u w)) :
    ∃ D, w + 1 ≤ D ∧ D ≤ w + 4 ^ Q + 1 ∧ EventuallyWhite (u D) := by
  by_contra hne
  push_neg at hne
  have hall := regime_finite_check hm hQ h0 h1 hne
  obtain ⟨P, hP, -, hper⟩ := regime_periodic hm hQ h0 h1 hall
  exact hall (w + P) (by omega) (hw.of_eventuallyEq (hper w le_rfl))

end Machine

/-! ## Rule 30 -/

/-- The left diagonals of any row with a left edge at `0` form a left machine. -/
theorem ldiagOf_leftMachine (x : Config) : LeftMachine (fun D t => ldiagOf x (D : ℤ) t) := by
  intro D t
  have := ldiagOf_succ x ((D + 2 : ℕ) : ℤ) t
  have e0 : ((D + 2 : ℕ) : ℤ) - 2 = (D : ℤ) := by push_cast; ring
  have e1 : ((D + 2 : ℕ) : ℤ) - 1 = ((D + 1 : ℕ) : ℤ) := by push_cast; ring
  rw [e0, e1] at this
  exact this

theorem seed_leftEdgeAtZero : LeftEdgeAtZero seed :=
  ⟨fun j hj => by simp [seed]; omega, by simp [seed]⟩

theorem ldiag_leftMachine : LeftMachine (fun D t => ldiag (D : ℤ) t) :=
  ldiagOf_leftMachine seed

theorem ldiagOf_zero_not_white {x : Config} (hx : LeftEdgeAtZero x) :
    ¬ EventuallyWhite (ldiagOf x 0) := by
  rintro ⟨T, hT⟩
  have := hT T le_rfl
  rw [ldiagOf_zero hx] at this
  exact absurd this (by simp)

theorem ldiag_zero_not_white : ¬ EventuallyWhite (ldiag 0) :=
  ldiagOf_zero_not_white seed_leftEdgeAtZero

/-- **White-diagonal criterion for Rule 30** (any row with a left edge): left diagonal `D + 2` is
eventually white exactly when left diagonals `D` and `D + 1` eventually coincide. -/
theorem ldiagOf_white_iff_coincide {x : Config} (hx : LeftEdgeAtZero x) (D : ℕ) :
    EventuallyWhite (ldiagOf x ((D : ℤ) + 2)) ↔
      EventuallyEq (ldiagOf x (D : ℤ)) (ldiagOf x ((D : ℤ) + 1)) := by
  have := white_iff_coincide (ldiagOf_leftMachine x) (by simpa using ldiagOf_zero_not_white hx) D
  simpa using this

theorem ldiag_white_iff_coincide (D : ℕ) :
    EventuallyWhite (ldiag ((D : ℤ) + 2)) ↔ EventuallyEq (ldiag (D : ℤ)) (ldiag ((D : ℤ) + 1)) :=
  ldiagOf_white_iff_coincide seed_leftEdgeAtZero D

/-- No two adjacent left diagonals of Rule 30 are both eventually white. -/
theorem ldiag_no_two_consecutive_white (D : ℕ) :
    ¬ (EventuallyWhite (ldiag (D : ℤ)) ∧ EventuallyWhite (ldiag ((D : ℤ) + 1))) := by
  have := no_two_consecutive_white ldiag_leftMachine (by simpa using ldiag_zero_not_white) D
  simpa using this

/-- **Rule 30: a finite check closes a regime.**  If left diagonals `D₀`, `D₀ + 1` have eventual
period `Q > 0` and none of `D₀ + 1, …, D₀ + 4 ^ Q + 1` is eventually white, no left diagonal
beyond `D₀` is eventually white (so all later periods are `Q`). -/
theorem ldiag_regime_finite_check {Q D₀ : ℕ} (hQ : 0 < Q) (h0 : EvPer (ldiag D₀) Q)
    (h1 : EvPer (ldiag ((D₀ + 1 : ℕ) : ℤ)) Q)
    (hnw : ∀ D : ℕ, D₀ + 1 ≤ D → D ≤ D₀ + 4 ^ Q + 1 → ¬ EventuallyWhite (ldiag D)) :
    ∀ D : ℕ, D₀ + 1 ≤ D → ¬ EventuallyWhite (ldiag D) :=
  regime_finite_check (u := fun D t => ldiag (D : ℤ) t) ldiag_leftMachine hQ h0 h1 hnw

/-- **Rule 30: finitely many white left diagonals force periodicity in `D`.**  If no left
diagonal beyond `D₀` is eventually white, then for some `P > 0` every left diagonal `D ≥ D₀`
eventually equals left diagonal `D + P`. -/
theorem ldiag_periodic_in_D_of_finitely_many_white {D₀ : ℕ}
    (hw : ∀ D : ℕ, D₀ ≤ D → ¬ EventuallyWhite (ldiag D)) :
    ∃ P, 0 < P ∧ ∀ D : ℕ, D₀ ≤ D → EventuallyEq (ldiag D) (ldiag ((D + P : ℕ) : ℤ)) := by
  obtain ⟨m, hm⟩ := ldiag_common_period (D₀ + 2)
  obtain ⟨P, hP, -, hper⟩ := regime_periodic (u := fun D t => ldiag (D : ℤ) t)
    ldiag_leftMachine (Q := 2 ^ m) (D₀ := D₀) (by positivity) (hm D₀ (by omega))
    (hm (D₀ + 1) (by omega)) (fun D hD => hw D (by omega))
  exact ⟨P, hP, hper⟩

/-- Contrapositive: if the left side of Rule 30 is **not** eventually periodic in `D`, infinitely
many left diagonals are eventually white. -/
theorem ldiag_infinitely_many_white_of_aperiodic_in_D
    (h : ∀ D₀ P : ℕ, 0 < P → ∃ D : ℕ, D₀ ≤ D ∧
      ¬ EventuallyEq (ldiag D) (ldiag ((D + P : ℕ) : ℤ))) :
    ∀ D₀ : ℕ, ∃ D ≥ D₀, EventuallyWhite (ldiag D) := by
  intro D₀
  by_contra hne
  push_neg at hne
  obtain ⟨P, hP, hper⟩ := ldiag_periodic_in_D_of_finitely_many_white (D₀ := D₀) hne
  obtain ⟨D, hD, hnot⟩ := h D₀ P hP
  exact hnot (hper D hD)

/-- Left diagonal `2` is eventually white (diagonals `0` and `1` are both black from time `1`). -/
theorem ldiag_two_white : EventuallyWhite (ldiag 2) := by
  have := (ldiag_white_iff_coincide 0).mpr ⟨1, fun t ht => by
    obtain ⟨n, rfl⟩ := Nat.exists_eq_add_of_le' ht
    have h1 := ldiagOf_one seed_leftEdgeAtZero n
    simp only [ldiagOf_seed] at h1
    simp [ldiag_zero, h1]⟩
  simpa using this

/-- **Rule 30: there is no last white left diagonal.**  After every eventually white left
diagonal `w` another one comes within `4 ^ Q + 1` diagonals, where `Q` is an eventual period of
diagonals `w` and `w + 1`. -/
theorem ldiag_white_after_white {w Q : ℕ} (hQ : 0 < Q) (h0 : EvPer (ldiag w) Q)
    (h1 : EvPer (ldiag ((w + 1 : ℕ) : ℤ)) Q) (hw : EventuallyWhite (ldiag w)) :
    ∃ D : ℕ, w + 1 ≤ D ∧ D ≤ w + 4 ^ Q + 1 ∧ EventuallyWhite (ldiag D) :=
  white_after_white (u := fun D t => ldiag (D : ℤ) t) ldiag_leftMachine hQ h0 h1 hw

/-- **Rule 30 has infinitely many eventually white left diagonals.** -/
theorem ldiag_infinitely_many_white : ∀ D₀ : ℕ, ∃ D ≥ D₀, EventuallyWhite (ldiag D) := by
  intro D₀
  by_contra hne
  push_neg at hne
  classical
  -- the last white diagonal below `max D₀ 2`
  set N := max D₀ 2
  let P : ℕ → Prop := fun D => EventuallyWhite (ldiag D)
  have h2 : P 2 := by simpa [P] using ldiag_two_white
  set w := Nat.findGreatest P N
  have hw : P w := Nat.findGreatest_spec (P := P) (m := 2) (by omega) h2
  have hwN : w ≤ N := Nat.findGreatest_le N
  have hgreat : ∀ D : ℕ, w < D → ¬ P D := by
    intro D hD hPD
    rcases le_or_gt D N with h | h
    · exact Nat.findGreatest_is_greatest hD h hPD
    · exact hne D (by omega) hPD
  obtain ⟨m, hm⟩ := ldiag_common_period (w + 2)
  obtain ⟨D, hD1, -, hD⟩ := ldiag_white_after_white (Q := 2 ^ m) (by positivity)
    (hm w (by omega)) (hm (w + 1) (by omega)) hw
  exact hgreat D (by omega) hD

/-! ## The open question, restated exactly: unbounded periods ⟺ odd white diagonals -/

/-- Left diagonal `w + 1` is eventually white and left diagonal `w` (outside it) has eventual
period `Q` with **odd** parity over one period.  By `ldiag_doubles`, diagonal `w + 2` then loses
the period `Q`. -/
def OddWhiteAt (Q w : ℕ) : Prop :=
  ∃ T, (∀ t ≥ T, ldiag w (t + Q) = ldiag w t) ∧ (∀ t ≥ T, ldiag ((w : ℤ) + 1) t = false) ∧
    parityOn (ldiag w) T Q = true

/-- **Unbounded periods ⟺ odd white diagonals.**  The left-diagonal periods of Rule 30 are
unbounded exactly when, for every `m`, some eventually white left diagonal has an outer
neighbour of odd parity over the period `2 ^ m`.  Together with `ldiag_infinitely_many_white`
(white diagonals never stop) this isolates what is still open: the parities of the white
diagonals. -/
theorem ldiag_periods_unbounded_iff :
    (∀ m, ∃ D : ℕ, ¬ EvPer (ldiag D) (2 ^ m)) ↔ ∀ m, ∃ w : ℕ, OddWhiteAt (2 ^ m) w := by
  constructor
  · intro hu m
    by_contra hne
    push_neg at hne
    obtain ⟨D, hD⟩ := hu m
    apply hD
    clear hD
    induction D using Nat.strong_induction_on with
    | _ D ih =>
      match D, ih with
      | 0, _ => exact ⟨0, fun t _ => by simp [ldiag_zero]⟩
      | 1, _ =>
        refine ⟨1, fun t ht => ?_⟩
        obtain ⟨n, rfl⟩ := Nat.exists_eq_add_of_le' ht
        have h1 := ldiagOf_one seed_leftEdgeAtZero n
        have h2 := ldiagOf_one seed_leftEdgeAtZero (n + 2 ^ m)
        simp only [ldiagOf_seed] at h1 h2
        push_cast
        rw [show n + 1 + 2 ^ m = n + 2 ^ m + 1 by ring, h1, h2]
      | D + 2, ih =>
        have e1 : ((D + 2 : ℕ) : ℤ) - 1 = ((D + 1 : ℕ) : ℤ) := by push_cast; ring
        have e2 : ((D + 2 : ℕ) : ℤ) - 2 = (D : ℤ) := by push_cast; ring
        have hD0 := ih D (by omega)
        have hD1 := ih (D + 1) (by omega)
        by_cases hw : EventuallyWhite (ldiag ((D + 1 : ℕ) : ℤ))
        · obtain ⟨T1, hT1⟩ := hw
          obtain ⟨T0, hT0⟩ := hD0
          set T := max T0 T1
          have hper : ∀ t ≥ T, ldiag (D : ℤ) (t + 2 ^ m) = ldiag (D : ℤ) t :=
            fun t ht => hT0 t (le_of_max_le_left ht)
          have hwh : ∀ t ≥ T, ldiag ((D : ℤ) + 1) t = false := fun t ht => by
            have := hT1 t (le_of_max_le_right ht); push_cast at this; exact this
          cases hp : parityOn (ldiag (D : ℤ)) T (2 ^ m)
          · have := ldiag_keeps_of_even (D := ((D + 2 : ℕ) : ℤ)) (T := T) (Q := 2 ^ m)
              (by rw [e2]; exact hper) (by rw [e1]; push_cast; exact hwh) (by rw [e2]; exact hp)
            exact this
          · exact absurd ⟨T, hper, hwh, hp⟩ (hne D)
        · have := ldiag_evPer_of_not_white (D := ((D + 2 : ℕ) : ℤ)) (Q := 2 ^ m)
            (by rw [e1]; exact hD1) (by rw [e2]; exact hD0) (by rw [e1]; exact hw)
          exact this
  · intro h m
    obtain ⟨w, T, hper, hwh, hodd⟩ := h m
    have e1 : ((w + 2 : ℕ) : ℤ) - 1 = (w : ℤ) + 1 := by push_cast; ring
    have e2 : ((w + 2 : ℕ) : ℤ) - 2 = (w : ℤ) := by push_cast; ring
    refine ⟨w + 2, (ldiag_doubles (D := ((w + 2 : ℕ) : ℤ)) (T := T) (Q := 2 ^ m)
      (by rw [e2]; exact hper) (by rw [e1]; exact hwh) (by rw [e2]; exact hodd)).1⟩

end GLM.Rule30
